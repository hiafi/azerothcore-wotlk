"""
Builds full-width Spell / Talent / TalentTab rows from the friendly
source/spells.csv and source/talents.yaml entries.

Every row starts from `dbcfile.empty_row(table)` (every column 0/blank),
then friendly fields are mapped onto their real columns, then that row's
`raw_overrides` dict (if any) is applied last — see the "raw_overrides
escape hatch" section of the plan / README for why: it's what makes the
friendly schema not need to model all 234 Spell.dbc columns, and what makes
`reverse.py` lossless the other way around.

Note: `spell_weight` / `coeff_weight` are captured here as passthrough
metadata only — turning them into `BasePoints`/`RealPointsPerLevel` is the
single-rank-spell-system ticket's job (docs/single-rank-spell-system.md),
not this one. This ticket's effects use whatever `base_points` /
`points_per_level` the source row gives directly.
"""

from __future__ import annotations

from . import dbcfile, dbcfmt
from .reuse import ReuseContext

_ALL_LOCALES = dbcfmt.LOCALE_SUFFIXES


def _set_all_locales(row: dict, base_column: str, text: str) -> None:
    """Mirrors upstream convention (see spell_dbc.sql): only enUS is set,
    every other locale column stays blank."""
    row[f"{base_column}_Lang_enUS"] = text or ""


def build_spell_row(entry: dict, reuse: ReuseContext) -> dict:
    row = dbcfile.empty_row(dbcfmt.SPELL)
    row["ID"] = entry["id"]
    _set_all_locales(row, "Name", entry.get("name", ""))

    row["SchoolMask"] = entry.get("school", 0) or 0
    row["DispelType"] = entry.get("dispel", 0) or 0
    row["Mechanic"] = entry.get("mechanic", 0) or 0
    row["Attributes"] = entry.get("attributes", 0) or 0
    row["Category"] = entry.get("category", 0) or 0

    row["CastingTimeIndex"] = reuse.cast_time_index(entry.get("cast_time_ms"))
    row["RecoveryTime"] = entry.get("cooldown_ms", 0) or 0
    row["CategoryRecoveryTime"] = entry.get("category_cooldown_ms", 0) or 0
    row["PowerType"] = entry.get("power_type", 0) or 0
    row["ManaCost"] = entry.get("mana_cost", 0) or 0
    row["ManaCostPct"] = entry.get("mana_cost_pct", 0) or 0
    row["RangeIndex"] = reuse.range_index(entry.get("range_yards"))
    row["DurationIndex"] = reuse.duration_index(entry.get("duration_ms"))
    row["SpellIconID"] = entry.get("spell_icon_id", 0) or 0

    default_radius = entry.get("radius_yards")
    for i in range(1, 4):
        effect = entry.get(f"effect{i}")
        if not effect:
            continue
        n = i - 1
        row[f"Effect_{i}"] = effect.get("type", 0)
        row[f"EffectBasePoints_{i}"] = effect.get("base_points", 0)
        row[f"EffectRealPointsPerLevel_{i}"] = effect.get("points_per_level", 0.0)
        row[f"EffectDieSides_{i}"] = effect.get("die_sides", 1)
        row[f"EffectMechanic_{i}"] = effect.get("mechanic", 0)
        row[f"ImplicitTargetA_{i}"] = effect.get("implicit_target_a", 0)
        row[f"ImplicitTargetB_{i}"] = effect.get("implicit_target_b", 0)
        row[f"EffectAura_{i}"] = effect.get("apply_aura", 0)
        row[f"EffectAuraPeriod_{i}"] = effect.get("amplitude", 0)
        row[f"EffectMiscValue_{i}"] = effect.get("misc_value", 0)
        row[f"EffectTriggerSpell_{i}"] = effect.get("trigger_spell", 0)
        row[f"EffectChainTargets_{i}"] = effect.get("chain_targets", 0)
        row[f"EffectRadiusIndex_{i}"] = reuse.radius_index(
            effect.get("radius_yards", default_radius)
        )

    row.update(entry.get("raw_overrides") or {})
    return row


def build_talent_row(entry: dict) -> dict:
    row = dbcfile.empty_row(dbcfmt.TALENT)
    row["ID"] = entry["id"]
    row["TabID"] = entry["tab_id"]
    row["TierID"] = entry["tier"]
    row["ColumnIndex"] = entry["column"]
    ranks = entry.get("rank_spell_ids") or []
    for i, spell_id in enumerate(ranks[:9]):
        row[f"SpellRank_{i + 1}"] = spell_id
    depends = entry.get("depends_on") or {}
    row["PrereqTalent_1"] = depends.get("talent_id", 0)
    row["PrereqRank_1"] = depends.get("rank", 0)
    row["Flags"] = entry.get("flags", 0) or 0
    row.update(entry.get("raw_overrides") or {})
    return row


def build_talenttab_row(entry: dict) -> dict:
    row = dbcfile.empty_row(dbcfmt.TALENTTAB)
    row["ID"] = entry["id"]
    _set_all_locales(row, "Name", entry.get("name", ""))
    row["SpellIconID"] = entry.get("spell_icon_id", 0) or 0
    row["ClassMask"] = entry.get("class_mask", 0) or 0
    row["PetTalentMask"] = entry.get("pet_talent_mask", 0) or 0
    row["OrderIndex"] = entry.get("order_index", 0) or 0
    row.update(entry.get("raw_overrides") or {})
    return row


def build_item_row(entry: dict) -> dict:
    row = dbcfile.empty_row(dbcfmt.ITEM)
    row["ID"] = entry["id"]
    row["ClassID"] = entry.get("class_id", 0) or 0
    row["SubclassID"] = entry.get("subclass_id", 0) or 0
    row["Sound_Override_Subclassid"] = entry.get("sound_override_subclass_id", 0) or 0
    row["Material"] = entry.get("material", 0) or 0
    row["DisplayInfoID"] = entry.get("display_info_id", 0) or 0
    row["InventoryType"] = entry.get("inventory_type", 0) or 0
    row["SheatheType"] = entry.get("sheathe_type", 0) or 0
    return row


def build_skilllineability_row(entry: dict) -> dict:
    row = dbcfile.empty_row(dbcfmt.SKILLLINEABILITY)
    row["ID"] = entry["id"]
    row["SkillLine"] = entry["skill_line"]
    row["Spell"] = entry["spell_id"]
    row["ClassMask"] = entry.get("class_mask", 0) or 0
    row["RaceMask"] = entry.get("race_mask", 0) or 0
    row["MinSkillLineRank"] = entry.get("min_skill_line_rank", 1) or 0
    row.update(entry.get("raw_overrides") or {})
    return row
