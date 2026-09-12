"""
Reuse-or-mint matching for the small "lookup" DBCs referenced by spell
effects (SpellCastTimes, SpellDuration, SpellRange, SpellRadius).

Index 0 is treated as the stock "none/instant/no radius" sentinel in
SpellCastTimes/SpellRange/SpellRadius (standard WotLK DBC convention), so a
spell that doesn't need one of these just gets index 0 rather than a matched
or minted row. SpellDuration is the one exception - see duration_index below,
this is NOT "index 0 means permanent" the way the other three tables work.

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

    def reserved_rows(self) -> list[dict]:
        """Every row this table currently needs inside its OWN reserved id block — reused
        (`existing_rows`) plus freshly minted (`minted_rows`) — restricted to `[_start, _end]`
        since that's exactly what `sql_out`'s `DELETE ... WHERE ID BETWEEN` for this table
        removes. See `ReuseContext.reserved_rows` for why this must be the SQL-emission input
        instead of `minted_rows` alone."""
        return [
            row for row in self.existing_rows + self.minted_rows
            if self._start <= row["ID"] <= self._end
        ]


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

    @property
    def reserved_rows(self) -> dict:
        """{table_name: [every row this run needs inside the reserved block]} — reused rows
        included, not just freshly minted ones.

        Bugfix (2026-09-12, "Frostbolt/Fireball/Glacial Spike casting instantly" recurring - see
        docs/dbc-build-pipeline.md and docs/.master-todo-list.md): `generate.py` used to feed
        `sql_out.emit_pending_sql` only `.minted` for these 4 secondary tables, while the emitted
        SQL's own `DELETE FROM x WHERE ID BETWEEN <reserved block>` unconditionally wipes the
        *whole* reserved range. Any run that doesn't happen to re-mint a value some other,
        untouched spell still depends on (e.g. a run that only adds one new spell's cast time)
        deleted every previously-reused row in that table and never reinserted it - dropping that
        spell's cast time/duration/range/radius out from under it with no warning. This exact
        failure mode already happened at least twice live (`2026_09_06_02.sql`'s own header
        documents the first recurrence; the live DB was found to have regressed to it again,
        emptied, on 2026-09-12 - almost certainly one of the Arcane Mage rework's own Phase 2-4
        migrations repeating it a second time). Use this instead of `.minted` for both the SQL
        emission and the client-patch merge (`generate.py`'s `new_rows_by_table`) so a full
        reserved-range delete is always paired with a full reinsert of everything that block
        still needs, not just this run's own deltas. This does NOT by itself fix a case where
        `state.py`'s own "existing" view is already stale (e.g. content applied live but never
        promoted into `data/sql/updates/db_world/`) - it only stops a *correctly-informed* run
        from discarding rows other spells still depend on."""
        return {
            name: t.reserved_rows() for name, t in self._tables.items() if t.reserved_rows()
        }

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
        # Bugfix (2026-08-26, "Icicles never stacks" playtest report): a falsy duration_ms means
        # "this aura shouldn't naturally expire", but index 0 does NOT mean that here - unlike
        # SpellCastTimes/SpellRange/SpellRadius, the real client's SpellDuration.dbc has no row at
        # all for ID 0 (confirmed by direct extraction of the shipped file), so
        # SpellInfo::GetDuration() (SpellInfo.cpp) falls through its `if (!DurationEntry) return 0`
        # branch - a literal, immediately-expiring 0ms duration, not permanent. Aura::CalcMaxDuration
        # (SpellAuras.cpp) papers over this with a `IsPassive() && !DurationEntry -> -1` special case,
        # which is why this was invisible for passive-marked rows (e.g. Biting Cold, 200010-200012)
        # but broke Icicles (200001, not passive - it's a script-managed stacking buff, not a known
        # ability) outright: every recast synced to a fresh 0-duration aura instead of adding a stack
        # to the existing one. Reuse the real permanent row (Duration/MaxDuration both -1) instead.
        if not duration_ms:
            return self._tables["spellduration"].find_or_mint(
                {"Duration": -1, "DurationPerLevel": 0, "MaxDuration": -1},
                lambda new_id: {
                    "ID": new_id, "Duration": -1, "DurationPerLevel": 0, "MaxDuration": -1,
                },
            )
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
