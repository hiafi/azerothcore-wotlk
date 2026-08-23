"""
Reuse-or-mint matching for the small "lookup" DBCs referenced by spell
effects (SpellCastTimes, SpellDuration, SpellRange, SpellRadius).

Index 0 is treated as the stock "none/instant/no radius" sentinel in all
four tables (standard WotLK DBC convention), so a spell that doesn't need
one of these just gets index 0 rather than a matched or minted row.

Otherwise: given a wanted set of field values, look for an existing row
(base client DBC ⊕ current SQL overlay, passed in by the caller) whose
fields already match, and only mint a new row — from the reserved block in
`source/ids.yaml` — when nothing does. This is what keeps `git diff` small:
regenerating with no new distinct values reuses every ID it used last time.
"""

from __future__ import annotations

from . import dbcfile, dbcfmt


class IdBlockExhausted(Exception):
    pass


class ReuseTable:
    """Reuse-or-mint bookkeeping for one lookup table."""

    def __init__(self, name: str, existing_rows: list[dict], id_range: dict):
        self.name = name
        self.existing_rows = list(existing_rows)
        self._start = id_range["start"]
        self._end = id_range["end"]
        self._used_ids = {row["ID"] for row in self.existing_rows}
        self._next_candidate = self._start
        self.minted_rows: list[dict] = []

    def find_or_mint(self, match_fields: dict, full_row_fn) -> int:
        """`match_fields` is a subset of column->value this row must match
        (besides ID). `full_row_fn` builds the full row dict when minting."""
        for row in self.existing_rows:
            if all(row.get(k) == v for k, v in match_fields.items()):
                return row["ID"]
        for row in self.minted_rows:
            if all(row.get(k) == v for k, v in match_fields.items()):
                return row["ID"]

        new_id = self._next_candidate
        while new_id in self._used_ids:
            new_id += 1
        if new_id > self._end:
            raise IdBlockExhausted(
                f"{self.name}: reserved block {self._start}-{self._end} is full"
            )
        self._next_candidate = new_id + 1
        self._used_ids.add(new_id)
        row = full_row_fn(new_id)
        self.minted_rows.append(row)
        return new_id


class ReuseContext:
    """Bundles a ReuseTable per lookup table and exposes friendly-unit
    (ms / yards) helpers used by `build.py`."""

    def __init__(self, existing_rows_by_table: dict, ids_cfg: dict):
        self._tables = {
            name: ReuseTable(name, existing_rows_by_table.get(name, []), ids_cfg[name])
            for name in ("spellcasttimes", "spellduration", "spellrange", "spellradius")
        }

    @property
    def minted(self) -> dict:
        """{table_name: [new full rows]} — feed straight to sql_out/patch_out."""
        return {name: t.minted_rows for name, t in self._tables.items() if t.minted_rows}

    def cast_time_index(self, cast_time_ms: int | None) -> int:
        if not cast_time_ms:
            return 0
        return self._tables["spellcasttimes"].find_or_mint(
            {"Base": cast_time_ms, "PerLevel": 0, "Minimum": 0},
            lambda new_id: {
                "ID": new_id, "Base": cast_time_ms, "PerLevel": 0, "Minimum": 0,
            },
        )

    def duration_index(self, duration_ms: int | None) -> int:
        if not duration_ms:
            return 0
        return self._tables["spellduration"].find_or_mint(
            {"Duration": duration_ms, "DurationPerLevel": 0, "MaxDuration": duration_ms},
            lambda new_id: {
                "ID": new_id, "Duration": duration_ms, "DurationPerLevel": 0,
                "MaxDuration": duration_ms,
            },
        )

    def radius_index(self, radius_yards: float | None) -> int:
        if not radius_yards:
            return 0
        return self._tables["spellradius"].find_or_mint(
            {"Radius": float(radius_yards), "RadiusPerLevel": 0.0, "RadiusMax": float(radius_yards)},
            lambda new_id: {
                "ID": new_id, "Radius": float(radius_yards), "RadiusPerLevel": 0.0,
                "RadiusMax": float(radius_yards),
            },
        )

    def range_index(self, range_yards: float | None) -> int:
        if not range_yards:
            return 0
        match = {
            "RangeMin_1": 0.0, "RangeMin_2": 0.0,
            "RangeMax_1": float(range_yards), "RangeMax_2": float(range_yards),
            "Flags": 0,
        }

        def build_row(new_id):
            row = dbcfile.empty_row(dbcfmt.SPELLRANGE)
            row.update(match)
            row["ID"] = new_id
            return row

        return self._tables["spellrange"].find_or_mint(match, build_row)
