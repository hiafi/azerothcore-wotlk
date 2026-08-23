"""
Inverse of build.py: given a full merged Spell.dbc / Talent.dbc /
TalentTab.dbc row (base ⊕ overlay), produce the friendly source fields plus
a `raw_overrides` dict — used by pull.py / pull_talents.py to seed source
rows from existing data.

Losslessness works by construction rather than by hand-listing every
column: reverse a row into friendly fields, rebuild it with `build.py`
(for spells, reusing the *same* secondary-table rows, so CastingTimeIndex/
DurationIndex/RangeIndex/EffectRadiusIndex land on the same IDs instead of
minting new ones), then diff column-by-column against the original.
Anything that doesn't come back identical — whether this module simply
doesn't model it, or a friendly field's simplifying assumptions don't fit
this particular row — goes into `raw_overrides`, so the round trip is exact
either way.
"""

from __future__ import annotations

from . import build
from .dbcfmt import SPELL, TALENT, TALENTTAB
from .reuse import ReuseContext


def reverse_spell_row(row: dict, secondary_rows: dict[str, dict[int, dict]]) -> dict:
    """`secondary_rows`: {"spellcasttimes": {ID: row}, "spellduration": {...},
    "spellrange": {...}, "spellradius": {...}} — the merged base⊕overlay view
    for each, exactly as `state.load_existing_rows` produces per table."""
    cast = secondary_rows["spellcasttimes"].get(row["CastingTimeIndex"])
    duration = secondary_rows["spellduration"].get(row["DurationIndex"])
    rng = secondary_rows["spellrange"].get(row["RangeIndex"])

    entry = {
        "id": row["ID"],
        "name": row.get("Name_Lang_enUS") or "",
        "school": row["SchoolMask"],
        "dispel": row["DispelType"],
        "mechanic": row["Mechanic"],
        "attributes": row["Attributes"],
        "category": row["Category"],
        "cast_time_ms": cast["Base"] if cast else None,
        "cooldown_ms": row["RecoveryTime"],
        "category_cooldown_ms": row["CategoryRecoveryTime"],
        "power_type": row["PowerType"],
        "mana_cost": row["ManaCost"],
        "range_yards": rng["RangeMax_1"] if rng else None,
        "duration_ms": duration["Duration"] if duration else None,
        "spell_icon_id": row["SpellIconID"],
    }

    for i in (1, 2, 3):
        if not row.get(f"Effect_{i}"):
            continue
        radius = secondary_rows["spellradius"].get(row[f"EffectRadiusIndex_{i}"])
        entry[f"effect{i}"] = {
            "type": row[f"Effect_{i}"],
            "base_points": row[f"EffectBasePoints_{i}"],
            "points_per_level": row[f"EffectRealPointsPerLevel_{i}"],
            "die_sides": row[f"EffectDieSides_{i}"],
            "mechanic": row[f"EffectMechanic_{i}"],
            "implicit_target_a": row[f"ImplicitTargetA_{i}"],
            "implicit_target_b": row[f"ImplicitTargetB_{i}"],
            "apply_aura": row[f"EffectAura_{i}"],
            "amplitude": row[f"EffectAuraPeriod_{i}"],
            "misc_value": row[f"EffectMiscValue_{i}"],
            "trigger_spell": row[f"EffectTriggerSpell_{i}"],
            "chain_targets": row[f"EffectChainTargets_{i}"],
            "radius_yards": radius["Radius"] if radius else None,
        }

    # The exact bounds here don't matter: every lookup below is expected to
    # find an existing match (that's the whole premise of reversing an
    # existing row), so find_or_mint never needs to actually mint.
    reuse = ReuseContext(
        {name: list(rows.values()) for name, rows in secondary_rows.items()},
        _dummy_id_ranges(),
    )
    rebuilt = build.build_spell_row(entry, reuse)

    overrides = {c: row[c] for c in SPELL.columns if rebuilt.get(c) != row.get(c)}
    entry["raw_overrides"] = overrides or None
    return entry


def reverse_talenttab_row(row: dict) -> dict:
    """No secondary-table lookups involved, so this one's a direct
    build-and-diff — no ReuseContext needed."""
    entry = {
        "id": row["ID"],
        "name": row.get("Name_Lang_enUS") or "",
        "class_mask": row["ClassMask"],
        "pet_talent_mask": row["PetTalentMask"],
        "order_index": row["OrderIndex"],
        "spell_icon_id": row["SpellIconID"],
    }
    rebuilt = build.build_talenttab_row(entry)
    overrides = {c: row[c] for c in TALENTTAB.columns if rebuilt.get(c) != row.get(c)}
    entry["raw_overrides"] = overrides or None
    return entry


def reverse_talent_row(row: dict) -> dict:
    rank_ids = [row[f"SpellRank_{i}"] for i in range(1, 10)]
    while rank_ids and rank_ids[-1] == 0:
        rank_ids.pop()
    entry = {
        "id": row["ID"],
        "tab_id": row["TabID"],
        "tier": row["TierID"],
        "column": row["ColumnIndex"],
        "rank_spell_ids": rank_ids,
        "depends_on": {"talent_id": row["PrereqTalent_1"], "rank": row["PrereqRank_1"]},
        "flags": row["Flags"],
    }
    rebuilt = build.build_talent_row(entry)
    overrides = {c: row[c] for c in TALENT.columns if rebuilt.get(c) != row.get(c)}
    entry["raw_overrides"] = overrides or None
    return entry


def _dummy_id_ranges() -> dict:
    # find_or_mint only mints when nothing matches; every lookup here is
    # expected to hit an existing row, so the exact bounds don't matter as
    # long as they're present for all four secondary tables.
    wide = {"start": 900000, "end": 999999}
    return {
        "spellcasttimes": wide, "spellduration": wide,
        "spellrange": wide, "spellradius": wide,
    }
