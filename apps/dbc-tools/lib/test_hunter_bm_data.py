"""
Hunter S1a (Beast Mastery) built-row guards (hunter-rework S1a-HANDOFF WP-A table row A5; S1a-WP-BRIEF; BEAST-MASTERY.md
2.2, 2.4, 4.3-4.13, 5).

Loads the real hunter DSL package (shared with `test_hunter_pet_data.py`, one load per process) and asserts on the BUILT rows
(stock base + DSL + raw_overrides, via `build.build_spell_row`), so a stale raw twin that wins fails here too:

  (a) `EquippedItemClass == -1` on every id S1a declares or edits (L1): the new ids, the pulled/edited stock ids and every
      stock rank spell of tab 361 that the package declares;
  (b) the 17 commanded spells 201720-201736: SCHOOL_DAMAGE / PERIODIC_DAMAGE only (no weapon-damage effect), d1 b28 + d2 b22,
      family 9, melee DefenseType except 201729 / 201734 / 201735 / 201736 (RANGED by design);
  (c) no talent / reader SpellMod mask or spell_proc family mask on a BM spell holds d1 b28;
  (d) Commands 201800 / 201801: d2 b21, IS_ABILITY, AttributesEx 0;
  (e) 201805 / 201807: family 0, SUPPRESS_CASTER_PROCS, custom attr 0x8000; no family bits on the helper carriers;
  (f) spell_proc rows of 201806 (attributes_mask 0x2) and 201848 (CAST phase 0x1), positive keys;
  (g) 201811 (stored -1501, mask (0,0,0x20000000), spell_group 1231 + rule 1) and 201812 (shape, linked from 201857), the four
      capstone links;
  (h) Longevity 53262-53264 mask (0, 0x2000000, 0x200000); Cobra Strikes 53256 / 53259 / 53260 inert until S1b;
  (i) 34471 has no eff2 and a 15 s duration; A9's four ids (34027, 58914, 60110, 60113) are inert by data;
  (j) tab 361 = 33 talents / 80 points, one talent per cell, no PrereqTalent, skill line 50, row 2139 still stock 53270.
      (34692 in no talent row lives in test_hunter_inert_keys.py.)

Every check is a pure function; the negative-fixture class feeds each one a minimal bad input.

Run directly:

    apps/dbc-tools/.venv/bin/python3 -m pytest apps/dbc-tools/lib/test_hunter_bm_data.py -q
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import build  # noqa: E402
from lib.test_hunter_pet_data import check_equipped_item_class, package_data  # noqa: E402

LETTERS = ("A", "B", "C")
PET_BIT_D1 = 0x10000000
SPELLMOD_AURAS = {107, 108}
SPELLFAMILY_HUNTER = 9

# effect / aura ids (SpellEffects.h, SpellAuraDefines.h)
EFFECT_SCHOOL_DAMAGE = 2
EFFECT_DUMMY = 3
EFFECT_APPLY_AURA = 6
EFFECT_JUMP = 41
EFFECT_TRIGGER_SPELL = 64
WEAPON_DAMAGE_EFFECTS = {17, 31, 58, 121}   # WEAPON_DAMAGE_NOSCHOOL, WEAPON_PERCENT_DAMAGE, WEAPON_DAMAGE, NORMALIZED_WEAPON_DMG
AURA_DUMMY = 4
AURA_PERIODIC_DAMAGE = 3
AURA_PROC_TRIGGER_SPELL = 42
AURA_PERIODIC_TRIGGER_SPELL = 23
AURA_PERIODIC_DUMMY = 226
AURA_ADD_FLAT_MODIFIER = 107
AURA_ADD_PCT_MODIFIER = 108

DEFENSE_MELEE = 2
DEFENSE_RANGED = 3

ATTR_IS_ABILITY = 0x10
ATTR_EX3_SUPPRESS_CASTER_PROCS = 0x10000
CU_IGNORE_ARMOR = 0x8000

# ---- the id sets -----------------------------------------------------------------------------------------------------
COMMANDED = tuple(range(201720, 201737))                                  # 17 spells, 201736 is the splash
RANGED_COMMANDED = frozenset({201729, 201734, 201735, 201736})
COMMANDS = (201800, 201801)
HELPER_COPIES = (201805, 201807)
HELPER_CARRIERS = tuple(range(201805, 201814))                            # 201805-201813: no family bits (BM 2.4)
NEW_S1A_IDS = (
    *range(201720, 201737), 201800, 201801, 201804, 201805, 201806, 201807, 201808,
    201810, 201811, 201812, 201813, *range(201820, 201858),
)
EDITED_STOCK_IDS = (
    34026, 56641, 61846, 201601, 19574, 34471, 57447, 57452, 57453, 57483, 57484, 57485, 35060, 35061, 56851, 58914,
    34027, 60110, 60113, 75593,
)
# Stock rank spells BM 5 re-keys with new values: they must be declared AND carry -1. Ranks whose values are unchanged
# (Ferocity, Ferocious Inspiration, Kindred Spirits, Beast Mastery) are covered dynamically below when declared.
REQUIRED_STOCK_RANKS = (
    19559, 19560, 19583, 19584, 19585, 35029, 35030, 24443, 19575, 19552, 19553, 19554, 19616, 19617, 19618,
    34453, 34454, 34462, 34464, 34465, 34466, 34467, 34468, 53256, 53259, 53260, 53262, 53263, 53264,
)
# Orchestrator ruling (S1a): Steady Shot keeps its stock EquippedItemClass 2 (ranged weapon). It is cast directly by the
# player and never triggered, so the requirement is wanted. The ONLY exemption from the -1 guard.
EQUIPPED_ITEM_CLASS_EXEMPT = frozenset({56641})
TAB = 361
TAB_RANK_CAP = 200000

LONGEVITY = (53262, 53263, 53264)
LONGEVITY_MASK = (0, 0x02000000, 0x00200000)
COBRA_STRIKES = {53256: 5, 53259: 10, 53260: 15}
INERT_FOUR = (34027, 58914, 60110, 60113)
KINDRED_LINK = (56316, 53270, 2)
LINKS = ((201820, 201813, 2), (201851, 201811, 2), (201857, 201812, 2), KINDRED_LINK)
COBRA_SHOT_GROUP = 1231

# BEAST-MASTERY 2.2: talent id -> (tier, column)
TAB_CELLS = {
    1384: (0, 0), 60200: (0, 1), 1389: (0, 2), 1381: (0, 3),
    1624: (1, 0), 1625: (1, 1), 1395: (1, 2), 1382: (1, 3),
    60201: (2, 1), 1396: (2, 2), 2138: (2, 3),
    1385: (3, 0), 1393: (3, 2), 1397: (3, 3),
    1390: (4, 0), 1387: (4, 1), 1388: (4, 2), 60202: (4, 3),
    60203: (5, 0), 60204: (5, 1), 1799: (5, 2),
    1801: (6, 0), 1386: (6, 1), 60205: (6, 2), 1800: (6, 3),
    1802: (7, 0), 60206: (7, 1), 2136: (7, 2),
    2137: (8, 0), 1803: (8, 1), 2140: (8, 2),
    2227: (9, 2),
    2139: (10, 1),
}
TAB_TALENT_COUNT = 33
TAB_POINTS = 80
STAMPEDE_ROW = 2139
STOCK_BEAST_MASTERY_RANK = 53270
SKILL_LINE_BM = 50
COMMAND_SLA_IDS = (30541, 30542, 30543)


def _u32(value) -> int:
    return int(value or 0) & 0xFFFFFFFF


def effect_mask(row: dict, effect: int) -> tuple[int, int, int]:
    """Effect `effect` (1-based): letter = effect index, number = dword (README Gotcha)."""
    letter = LETTERS[effect - 1]
    return tuple(_u32(row.get(f"EffectSpellClassMask{letter}_{n}")) for n in (1, 2, 3))


def spell_mask(row: dict) -> tuple[int, int, int]:
    return tuple(_u32(row.get(f"SpellClassMask_{n}")) for n in (1, 2, 3))


def _hex(mask) -> str:
    return "(" + ", ".join(f"0x{w:X}" for w in mask) + ")"


def _i(row: dict, key: str) -> int:
    return int(row.get(key) or 0)


def _effects(row: dict):
    for index in (1, 2, 3):
        yield index, _i(row, f"Effect_{index}"), _i(row, f"EffectAura_{index}")


def _stock_ranks(talents: list[dict]) -> list[int]:
    return sorted({sid for t in talents if t.get("tab_id") == TAB for sid in t.get("rank_spell_ids") or []
                   if sid < TAB_RANK_CAP})


# ---- checks (pure: take built rows / entries, return problem strings) --------------------------------------------------

def check_required_rows_declared(rows_by_id: dict[int, dict], ids) -> list[str]:
    return [f"{i}: not declared in the hunter package" for i in ids if i not in rows_by_id]


def check_commanded_spell(spell_id: int, row: dict | None) -> list[str]:
    """(b) one commanded spell: family 9 + d1 b28 + d2 b22, only SCHOOL_DAMAGE / PERIODIC_DAMAGE (+ the Lunge JUMP and
    Venomous Cloud's TRIGGER_SPELL) among the effects, at least one damage effect, DefenseType RANGED exactly for the
    four ranged ones."""
    if row is None:
        return [f"{spell_id}: not declared"]
    bad = []
    if _i(row, "SpellClassSet") != SPELLFAMILY_HUNTER:
        bad.append(f"SpellClassSet {row.get('SpellClassSet')}, expected 9")
    mask = spell_mask(row)
    if not mask[1] & PET_BIT_D1:
        bad.append(f"SpellClassMask {_hex(mask)} lacks d1 b28 (0x10000000)")
    if not mask[2] & 0x400000:
        bad.append(f"SpellClassMask {_hex(mask)} lacks d2 b22 (0x400000)")
    damage = 0
    for index, effect, aura in _effects(row):
        if not effect:
            continue
        if effect in WEAPON_DAMAGE_EFFECTS:
            bad.append(f"effect {index} is weapon-damage type {effect} (the 0.25 pet white scale would cut it)")
        elif effect == EFFECT_SCHOOL_DAMAGE:
            damage += 1
        elif effect == EFFECT_APPLY_AURA:
            if aura == AURA_PERIODIC_DAMAGE:
                damage += 1
            else:
                bad.append(f"effect {index} is APPLY_AURA with aura {aura}, expected PERIODIC_DAMAGE (3)")
        elif effect not in (EFFECT_JUMP, EFFECT_TRIGGER_SPELL):
            bad.append(f"effect {index} has unexpected type {effect}")
    if not damage:
        bad.append("no SCHOOL_DAMAGE / PERIODIC_DAMAGE effect")
    want = DEFENSE_RANGED if spell_id in RANGED_COMMANDED else DEFENSE_MELEE
    if _i(row, "DefenseType") != want:
        bad.append(f"DefenseType {row.get('DefenseType')}, expected {want} ({'RANGED' if want == DEFENSE_RANGED else 'MELEE'})")
    return [f"{spell_id}: {b}" for b in bad]


def check_no_pet_bit_readers(rows_by_id: dict[int, dict], ids, procs: list[dict]) -> list[str]:
    """(c) on the given spells: no SpellMod effect mask and no declared spell_proc family mask holds d1 b28."""
    bad = []
    wanted = set(ids)
    for spell_id in sorted(wanted):
        row = rows_by_id.get(spell_id)
        if row is None:
            continue
        for index, _effect, aura in _effects(row):
            if aura in SPELLMOD_AURAS and effect_mask(row, index)[1] & PET_BIT_D1:
                bad.append(f"{spell_id}: SpellMod effect {index} mask {_hex(effect_mask(row, index))} holds d1 b28")
    for proc in procs:
        if abs(int(proc["SpellId"])) in wanted and _u32(proc.get("SpellFamilyMask1")) & PET_BIT_D1:
            bad.append(f"spell_proc {proc['SpellId']}: family mask holds d1 b28")
    return bad


def check_command_press(spell_id: int, row: dict | None) -> list[str]:
    """(d) a Command press: d2 b21, IS_ABILITY, AttributesEx 0."""
    if row is None:
        return [f"{spell_id}: not declared"]
    bad = []
    if not spell_mask(row)[2] & 0x200000:
        bad.append(f"SpellClassMask {_hex(spell_mask(row))} lacks d2 b21 (0x200000)")
    if not _i(row, "Attributes") & ATTR_IS_ABILITY:
        bad.append(f"Attributes 0x{_i(row, 'Attributes'):X} lacks IS_ABILITY (0x10)")
    if _i(row, "AttributesEx") != 0:
        bad.append(f"AttributesEx 0x{_i(row, 'AttributesEx'):X}, expected 0")
    return [f"{spell_id}: {b}" for b in bad]


def check_helper_copy(spell_id: int, row: dict | None, custom_attrs: list[dict]) -> list[str]:
    """(e) Beast Cleave / Spiked Collar copy: family 0, SUPPRESS_CASTER_PROCS, custom attr 0x8000."""
    if row is None:
        return [f"{spell_id}: not declared"]
    bad = []
    if _i(row, "SpellClassSet") != 0:
        bad.append(f"SpellClassSet {row.get('SpellClassSet')}, expected 0")
    if not _i(row, "AttributesEx3") & ATTR_EX3_SUPPRESS_CASTER_PROCS:
        bad.append(f"AttributesEx3 0x{_i(row, 'AttributesEx3'):X} lacks SUPPRESS_CASTER_PROCS (0x10000)")
    attrs = [int(c["attributes"]) for c in custom_attrs if int(c["spell_id"]) == spell_id]
    if not attrs or not attrs[-1] & CU_IGNORE_ARMOR:
        bad.append(f"custom attr {attrs}, expected 0x8000 (IGNORE_ARMOR)")
    return [f"{spell_id}: {b}" for b in bad]


def check_no_family_bits(rows_by_id: dict[int, dict], ids=HELPER_CARRIERS) -> list[str]:
    """(e) BM 2.4: no family bit on the helper carriers 201805-201813."""
    bad = []
    for spell_id in ids:
        row = rows_by_id.get(spell_id)
        if row is not None and any(spell_mask(row)):
            bad.append(f"{spell_id}: SpellClassMask {_hex(spell_mask(row))}, expected no family bits (BM 2.4)")
    return bad


def check_spell_proc_rows(procs: list[dict]) -> list[str]:
    """(f) 201806: positive key, attributes_mask 0x2 (TRIGGERED_CAN_PROC), spell phase HIT 0x2, proc flags 0x10114.
    201848: positive key, spell phase CAST 0x1, flags 0x100, family 9 mask (0x1000, 0, 0)."""
    bad = []
    by_id = {int(p["SpellId"]): p for p in procs}
    for spell_id in (201806, 201848):
        if -spell_id in by_id:
            bad.append(f"spell_proc -{spell_id}: negative key (this spell has no ranks); use +{spell_id}")
        if spell_id not in by_id:
            bad.append(f"spell_proc {spell_id}: not declared")
    p = by_id.get(201806)
    if p:
        if not _i(p, "AttributesMask") & 0x2:
            bad.append(f"spell_proc 201806: AttributesMask 0x{_i(p, 'AttributesMask'):X} lacks 0x2 (TRIGGERED_CAN_PROC)")
        if _i(p, "SpellPhaseMask") != 0x2:
            bad.append(f"spell_proc 201806: SpellPhaseMask {p.get('SpellPhaseMask')}, expected 0x2")
        if _i(p, "ProcFlags") != 0x10114:
            bad.append(f"spell_proc 201806: ProcFlags 0x{_i(p, 'ProcFlags'):X}, expected 0x10114")
    p = by_id.get(201848)
    if p:
        if _i(p, "SpellPhaseMask") != 0x1:
            bad.append(f"spell_proc 201848: SpellPhaseMask {p.get('SpellPhaseMask')}, expected CAST 0x1")
        if _i(p, "ProcFlags") != 0x100:
            bad.append(f"spell_proc 201848: ProcFlags 0x{_i(p, 'ProcFlags'):X}, expected 0x100")
        mask = tuple(_u32(p.get(f"SpellFamilyMask{n}")) for n in (0, 1, 2))
        if _i(p, "SpellFamilyName") != SPELLFAMILY_HUNTER or mask != (0x1000, 0, 0):
            bad.append(f"spell_proc 201848: family {p.get('SpellFamilyName')} mask {_hex(mask)}, expected 9 (0x1000, 0x0, 0x0)")
    return bad


def check_cobra_shot_transform(row: dict | None, groups: list[dict], rules: list[dict]) -> list[str]:
    """(g) 201811: eff0 ADD_FLAT_MODIFIER CASTING_TIME (misc 10) stored -1501 on (0,0,0x20000000), attributes 464,
    in spell_group 1231 whose rule is 1 (EXCLUSIVE)."""
    if row is None:
        return ["201811: not declared"]
    bad = []
    if _i(row, "Effect_1") != EFFECT_APPLY_AURA or _i(row, "EffectAura_1") != AURA_ADD_FLAT_MODIFIER:
        bad.append(f"eff0 is {row.get('Effect_1')}/{row.get('EffectAura_1')}, expected APPLY_AURA / ADD_FLAT_MODIFIER")
    if _i(row, "EffectMiscValue_1") != 10:
        bad.append(f"eff0 misc {row.get('EffectMiscValue_1')}, expected 10 (CASTING_TIME)")
    if _i(row, "EffectBasePoints_1") != -1501:
        bad.append(f"eff0 stored base points {row.get('EffectBasePoints_1')}, expected -1501 (live -1500, B3)")
    if effect_mask(row, 1) != (0, 0, 0x20000000):
        bad.append(f"eff0 mask {_hex(effect_mask(row, 1))}, expected (0x0, 0x0, 0x20000000)")
    if _i(row, "Attributes") != 464:
        bad.append(f"Attributes {row.get('Attributes')}, expected 464")
    if not any(int(g["id"]) == COBRA_SHOT_GROUP and int(g["spell_id"]) == 201811 for g in groups):
        bad.append(f"not a member of spell_group {COBRA_SHOT_GROUP}")
    group_rules = [r for r in rules if int(r["group_id"]) == COBRA_SHOT_GROUP]
    if not group_rules or int(group_rules[-1]["stack_rule"]) != 1:
        bad.append(f"spell_group {COBRA_SHOT_GROUP} has no stack rule 1: {[r.get('stack_rule') for r in group_rules]}")
    return [f"201811: {b}" for b in bad]


def check_tbw_mastery(row: dict | None) -> list[str]:
    """(g) 201812: attributes 464, eff0 ADD_PCT_MODIFIER DAMAGE (misc 0) on (0, 0x800, 0), eff1 PERIODIC_DUMMY amplitude
    1000, family 9."""
    if row is None:
        return ["201812: not declared"]
    bad = []
    if _i(row, "Attributes") != 464:
        bad.append(f"Attributes {row.get('Attributes')}, expected 464")
    if _i(row, "SpellClassSet") != SPELLFAMILY_HUNTER:
        bad.append(f"SpellClassSet {row.get('SpellClassSet')}, expected 9")
    if _i(row, "Effect_1") != EFFECT_APPLY_AURA or _i(row, "EffectAura_1") != AURA_ADD_PCT_MODIFIER:
        bad.append(f"eff0 is {row.get('Effect_1')}/{row.get('EffectAura_1')}, expected APPLY_AURA / ADD_PCT_MODIFIER")
    if _i(row, "EffectMiscValue_1") != 0:
        bad.append(f"eff0 misc {row.get('EffectMiscValue_1')}, expected 0 (DAMAGE)")
    if effect_mask(row, 1) != (0, 0x800, 0):
        bad.append(f"eff0 mask {_hex(effect_mask(row, 1))}, expected (0x0, 0x800, 0x0)")
    if _i(row, "Effect_2") != EFFECT_APPLY_AURA or _i(row, "EffectAura_2") != AURA_PERIODIC_DUMMY:
        bad.append(f"eff1 is {row.get('Effect_2')}/{row.get('EffectAura_2')}, expected APPLY_AURA / PERIODIC_DUMMY (226)")
    if _i(row, "EffectAuraPeriod_2") != 1000:
        bad.append(f"eff1 amplitude {row.get('EffectAuraPeriod_2')}, expected 1000")
    return [f"201812: {b}" for b in bad]


def check_linked_spells(linked: list[dict], expected=LINKS) -> list[str]:
    have = {(int(r["spell_trigger"]), int(r["spell_effect"]), int(r["type"])) for r in linked}
    return [f"linked_spell{key} not declared" for key in expected if key not in have]


def check_longevity(rows_by_id: dict[int, dict]) -> list[str]:
    """(h) Longevity ranks: eff0 mask (0, 0x2000000, 0x200000) = Bestial Wrath + the Command presses."""
    bad = []
    for spell_id in LONGEVITY:
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
        elif effect_mask(row, 1) != LONGEVITY_MASK:
            bad.append(f"{spell_id}: eff0 mask {_hex(effect_mask(row, 1))}, expected {_hex(LONGEVITY_MASK)}")
    return bad


def check_cobra_strikes(rows_by_id: dict[int, dict]) -> list[str]:
    """(h) Cobra Strikes ranks: eff0 aura DUMMY, trigger_spell 0, ProcChance 5/10/15, ProcTypeMask 0x100."""
    bad = []
    for spell_id, chance in COBRA_STRIKES.items():
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
            continue
        if _i(row, "Effect_1") != EFFECT_APPLY_AURA or _i(row, "EffectAura_1") != AURA_DUMMY:
            bad.append(f"{spell_id}: eff0 is {row.get('Effect_1')}/{row.get('EffectAura_1')}, expected APPLY_AURA / DUMMY (4)")
        if _i(row, "EffectTriggerSpell_1") != 0:
            bad.append(f"{spell_id}: EffectTriggerSpell_1 {row.get('EffectTriggerSpell_1')}, expected 0")
        if _i(row, "ProcChance") != chance:
            bad.append(f"{spell_id}: ProcChance {row.get('ProcChance')}, expected {chance}")
        if _i(row, "ProcTypeMask") != 0x100:
            bad.append(f"{spell_id}: ProcTypeMask 0x{_i(row, 'ProcTypeMask'):X}, expected 0x100")
    return bad


def check_beast_within_buff(row: dict | None, fifteen_s_index: int) -> list[str]:
    """(i) 34471: no eff2 (the stun-immunity aura) and DurationIndex for 15 s."""
    if row is None:
        return ["34471: not declared"]
    bad = []
    if _i(row, "Effect_3") or _i(row, "EffectAura_3"):
        bad.append(f"eff2 still present ({row.get('Effect_3')}/{row.get('EffectAura_3')}), expected none")
    if _i(row, "DurationIndex") != fifteen_s_index:
        bad.append(f"DurationIndex {row.get('DurationIndex')}, expected {fifteen_s_index} (15 s)")
    return [f"34471: {b}" for b in bad]


def check_inert_four(rows_by_id: dict[int, dict], ids=INERT_FOUR) -> list[str]:
    """(i) A9: no SpellMod, TRIGGER_SPELL (effect 64 or aura 42 / 23) or non-zero ProcTypeMask; 58914 eff0 is aura DUMMY;
    34027 / 58914 also carry ProcChance 0 and ProcCharges 0; the three no-op rows keep only aura DUMMY effects."""
    bad = []
    for spell_id in ids:
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
            continue
        for index, effect, aura in _effects(row):
            if aura in SPELLMOD_AURAS:
                bad.append(f"{spell_id}: effect {index} is a SpellMod (aura {aura})")
            if effect == EFFECT_TRIGGER_SPELL or aura in (AURA_PROC_TRIGGER_SPELL, AURA_PERIODIC_TRIGGER_SPELL):
                bad.append(f"{spell_id}: effect {index} triggers a spell (effect {effect} / aura {aura})")
            if _i(row, f"EffectTriggerSpell_{index}"):
                bad.append(f"{spell_id}: EffectTriggerSpell_{index} {row.get(f'EffectTriggerSpell_{index}')}, expected 0")
            if spell_id != 58914 and effect and (effect != EFFECT_APPLY_AURA or aura != AURA_DUMMY):
                bad.append(f"{spell_id}: effect {index} is {effect}/{aura}, expected a no-op APPLY_AURA / DUMMY")
        if _i(row, "ProcTypeMask") != 0:
            bad.append(f"{spell_id}: ProcTypeMask 0x{_i(row, 'ProcTypeMask'):X}, expected 0")
        if spell_id in (34027, 58914):
            for key in ("ProcChance", "ProcCharges"):
                if _i(row, key) != 0:
                    bad.append(f"{spell_id}: {key} {row.get(key)}, expected 0")
    row = rows_by_id.get(58914)
    if row is not None and (_i(row, "Effect_1") != EFFECT_APPLY_AURA or _i(row, "EffectAura_1") != AURA_DUMMY):
        bad.append(f"58914: eff0 is {row.get('Effect_1')}/{row.get('EffectAura_1')}, must stay APPLY_AURA / DUMMY "
                   f"(the stock spell_hun_kill_command_pet registers on it)")
    return bad


def check_tab_361(talents: list[dict], built_talents: list[dict], sla_entries: list[dict]) -> list[str]:
    """(j) tab 361: the 33 talents of BM 2.2 in their cells, 80 points, one talent per cell, no PrereqTalent anywhere
    (entry, raw override and built row), skill line 50 on the Command SkillLineAbility rows, 2139 still stock 53270."""
    mine = [t for t in talents if t.get("tab_id") == TAB]
    bad = []
    ids = [int(t["id"]) for t in mine]
    if len(mine) != TAB_TALENT_COUNT:
        bad.append(f"tab {TAB} has {len(mine)} talents, expected {TAB_TALENT_COUNT}")
    if set(ids) != set(TAB_CELLS):
        bad.append(f"tab {TAB} talent ids differ: unexpected {sorted(set(ids) - set(TAB_CELLS))}, "
                   f"missing {sorted(set(TAB_CELLS) - set(ids))}")
    points = sum(len(t.get("rank_spell_ids") or []) for t in mine)
    if points != TAB_POINTS:
        bad.append(f"tab {TAB} totals {points} points, expected {TAB_POINTS}")
    cells: dict[tuple[int, int], list[int]] = {}
    for t in mine:
        cells.setdefault((int(t["tier"]), int(t["column"])), []).append(int(t["id"]))
        want = TAB_CELLS.get(int(t["id"]))
        if want is not None and (int(t["tier"]), int(t["column"])) != want:
            bad.append(f"talent {t['id']} at {(t['tier'], t['column'])}, expected {want}")
        if t.get("depends_on"):
            bad.append(f"talent {t['id']}: depends_on {t['depends_on']} (no prerequisites anywhere, D7)")
        for key in (t.get("raw_overrides") or {}):
            if str(key).startswith(("PrereqTalent", "PrereqRank")):
                bad.append(f"talent {t['id']}: raw override {key}")
    for cell, talent_ids in sorted(cells.items()):
        if len(talent_ids) > 1:
            bad.append(f"cell {cell} holds talents {talent_ids}")
    for row in built_talents:
        if int(row.get("TabID") or 0) != TAB:
            continue
        for n in (1, 2, 3):
            if _i(row, f"PrereqTalent_{n}"):
                bad.append(f"talent {row['ID']}: built PrereqTalent_{n} {row.get(f'PrereqTalent_{n}')}")
    stampede = next((t for t in mine if int(t["id"]) == STAMPEDE_ROW), None)
    if stampede is None:
        bad.append(f"row {STAMPEDE_ROW} not declared in tab {TAB}")
    elif list(stampede.get("rank_spell_ids") or []) != [STOCK_BEAST_MASTERY_RANK]:
        bad.append(f"row {STAMPEDE_ROW} ranks {stampede.get('rank_spell_ids')}, expected the stock [{STOCK_BEAST_MASTERY_RANK}] "
                   f"until S1b")
    for entry in sla_entries:
        if int(entry["id"]) in COMMAND_SLA_IDS and int(entry["skill_line"]) != SKILL_LINE_BM:
            bad.append(f"SkillLineAbility {entry['id']}: skill line {entry['skill_line']}, expected {SKILL_LINE_BM}")
    return bad


# ---- real data -------------------------------------------------------------------------------------------------------

class HunterBmDataTest(unittest.TestCase):
    def assertClean(self, problems: list[str]):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_s1a_ids_have_equipped_item_class_minus_one(self):
        data = package_data()
        rows = data["rows_by_id"]
        declared_ranks = [i for i in _stock_ranks(data["package"].talents) if i in rows]
        self.assertClean(check_required_rows_declared(rows, (*NEW_S1A_IDS, *EDITED_STOCK_IDS, *REQUIRED_STOCK_RANKS)))
        ids = {*NEW_S1A_IDS, *EDITED_STOCK_IDS, *REQUIRED_STOCK_RANKS, *declared_ranks} - EQUIPPED_ITEM_CLASS_EXEMPT
        self.assertClean(check_equipped_item_class(rows, sorted(ids)))
        self.assertEqual(rows[56641].get("EquippedItemClass"), 2, "56641 keeps the stock ranged-weapon requirement")

    def test_commanded_spells(self):
        rows = package_data()["rows_by_id"]
        self.assertClean([b for i in COMMANDED for b in check_commanded_spell(i, rows.get(i))])

    def test_no_bm_reader_holds_the_pet_bit(self):
        data = package_data()
        ids = {*NEW_S1A_IDS, *EDITED_STOCK_IDS, *REQUIRED_STOCK_RANKS, 201802, 201803, 201809}
        self.assertClean(check_no_pet_bit_readers(data["rows_by_id"], ids, data["package"].spell_procs))

    def test_command_presses(self):
        rows = package_data()["rows_by_id"]
        self.assertClean([b for i in COMMANDS for b in check_command_press(i, rows.get(i))])

    def test_beast_cleave_and_spiked_collar_copies(self):
        data = package_data()
        self.assertClean([b for i in HELPER_COPIES
                          for b in check_helper_copy(i, data["rows_by_id"].get(i), data["package"].custom_attrs)])
        self.assertClean(check_no_family_bits(data["rows_by_id"]))

    def test_spell_proc_rows(self):
        self.assertClean(check_spell_proc_rows(package_data()["package"].spell_procs))

    def test_cobra_shot_transform_and_group(self):
        data = package_data()
        package = data["package"]
        self.assertClean(check_cobra_shot_transform(data["rows_by_id"].get(201811), package.spell_groups,
                                                    package.spell_group_rules))

    def test_the_beast_within_mastery_passive(self):
        self.assertClean(check_tbw_mastery(package_data()["rows_by_id"].get(201812)))

    def test_capstone_links(self):
        self.assertClean(check_linked_spells(package_data()["package"].linked_spells))

    def test_longevity_mask(self):
        self.assertClean(check_longevity(package_data()["rows_by_id"]))

    def test_cobra_strikes_inert_until_s1b(self):
        self.assertClean(check_cobra_strikes(package_data()["rows_by_id"]))

    def test_the_beast_within_buff(self):
        data = package_data()
        self.assertClean(check_beast_within_buff(data["rows_by_id"].get(34471), data["reuse"].duration_index(15000)))

    def test_a9_rows_are_inert_by_data(self):
        self.assertClean(check_inert_four(package_data()["rows_by_id"]))

    def test_tab_361_layout(self):
        data = package_data()
        package = data["package"]
        built = [build.build_talent_row(t) for t in package.talents if t.get("tab_id") == TAB]
        self.assertClean(check_tab_361(package.talents, built, package.skill_line_abilities))


# ---- negative fixtures: every check must fire on a minimal bad input -------------------------------------------------------

def good_commanded(spell_id: int = 201721) -> dict:
    ranged = spell_id in RANGED_COMMANDED
    return {"ID": spell_id, "SpellClassSet": 9, "SpellClassMask_2": 0x10000000, "SpellClassMask_3": 0x400000,
            "Effect_1": EFFECT_SCHOOL_DAMAGE, "DefenseType": DEFENSE_RANGED if ranged else DEFENSE_MELEE,
            "EquippedItemClass": -1}


def good_press(spell_id: int = 201800) -> dict:
    return {"ID": spell_id, "Attributes": 0x50010, "AttributesEx": 0, "SpellClassMask_3": 0x200000}


def good_copy(spell_id: int = 201807) -> dict:
    return {"ID": spell_id, "SpellClassSet": 0, "AttributesEx3": 0x20000000 | 0x10000 | 0x40000}


GOOD_ATTRS = [{"spell_id": 201805, "attributes": 0x8000}, {"spell_id": 201807, "attributes": 0x8000}]


def good_procs() -> list[dict]:
    return [
        {"SpellId": 201806, "ProcFlags": 0x10114, "SpellPhaseMask": 0x2, "AttributesMask": 0x2},
        {"SpellId": 201848, "ProcFlags": 0x100, "SpellPhaseMask": 0x1, "SpellFamilyName": 9, "SpellFamilyMask0": 0x1000},
    ]


def good_transform() -> dict:
    return {"ID": 201811, "Attributes": 464, "Effect_1": 6, "EffectAura_1": 107, "EffectMiscValue_1": 10,
            "EffectBasePoints_1": -1501, "EffectSpellClassMaskA_3": 0x20000000}


GOOD_GROUPS = [{"id": 1231, "spell_id": 201811}]
GOOD_RULES = [{"group_id": 1231, "stack_rule": 1}]


def good_tbw() -> dict:
    return {"ID": 201812, "Attributes": 464, "SpellClassSet": 9, "Effect_1": 6, "EffectAura_1": 108,
            "EffectMiscValue_1": 0, "EffectSpellClassMaskA_2": 0x800, "Effect_2": 6, "EffectAura_2": 226,
            "EffectAuraPeriod_2": 1000}


def good_tab() -> list[dict]:
    talents = []
    for talent_id, (tier, column) in TAB_CELLS.items():
        ranks = [STOCK_BEAST_MASTERY_RANK] if talent_id == STAMPEDE_ROW else [talent_id * 10]
        talents.append({"id": talent_id, "tab_id": TAB, "tier": tier, "column": column, "rank_spell_ids": ranks,
                        "depends_on": None, "raw_overrides": None})
    # 80 points: pad ranks on the multi-rank talents until the total is reached
    extra = TAB_POINTS - len(talents)
    for t in talents:
        if extra and t["id"] != STAMPEDE_ROW:
            take = min(extra, 2)
            t["rank_spell_ids"] += [t["id"] * 10 + n for n in range(1, take + 1)]
            extra -= take
    return talents


class HunterBmDataNegativeTest(unittest.TestCase):
    def test_equipped_item_class_guard_fires_on_stock_zero(self):
        rows = {201720: {"ID": 201720, "EquippedItemClass": -1}, 34026: {"ID": 34026, "EquippedItemClass": 0}}
        self.assertEqual(len(check_equipped_item_class(rows, (201720, 34026))), 1)
        self.assertEqual(len(check_equipped_item_class(rows, (201721,))), 1)            # undeclared
        self.assertEqual(len(check_required_rows_declared(rows, (201720, 201721))), 1)

    def test_only_steady_shot_is_exempt_from_the_equipped_item_class_guard(self):
        self.assertEqual(EQUIPPED_ITEM_CLASS_EXEMPT, {56641})
        rows = {56641: {"ID": 56641, "EquippedItemClass": 2}, 34026: {"ID": 34026, "EquippedItemClass": 2}}
        ids = {56641, 34026} - EQUIPPED_ITEM_CLASS_EXEMPT
        self.assertEqual(len(check_equipped_item_class(rows, sorted(ids))), 1)      # 34026 is not exempt

    def test_commanded_spell_good_row_passes_and_each_defect_fires(self):
        for spell_id in COMMANDED:
            self.assertEqual(check_commanded_spell(spell_id, good_commanded(spell_id)), [], spell_id)
        self.assertEqual(len(check_commanded_spell(201721, None)), 1)
        for effect in sorted(WEAPON_DAMAGE_EFFECTS):
            row = {**good_commanded(), "Effect_2": effect}
            self.assertEqual(len(check_commanded_spell(201721, row)), 1, effect)
        self.assertEqual(len(check_commanded_spell(201721, {**good_commanded(), "Effect_1": EFFECT_DUMMY})), 2)  # + no damage
        self.assertEqual(len(check_commanded_spell(201721, {**good_commanded(), "SpellClassMask_2": 0})), 1)
        self.assertEqual(len(check_commanded_spell(201721, {**good_commanded(), "SpellClassMask_3": 0x800000})), 1)
        self.assertEqual(len(check_commanded_spell(201721, {**good_commanded(), "SpellClassSet": 0})), 1)
        # a SpellMod-style aura where PERIODIC_DAMAGE belongs
        row = {**good_commanded(), "Effect_2": EFFECT_APPLY_AURA, "EffectAura_2": AURA_ADD_FLAT_MODIFIER}
        self.assertEqual(len(check_commanded_spell(201721, row)), 1)
        ok = {**good_commanded(), "Effect_2": EFFECT_APPLY_AURA, "EffectAura_2": AURA_PERIODIC_DAMAGE}
        self.assertEqual(check_commanded_spell(201721, ok), [])

    def test_ranged_by_design_is_enforced_both_ways(self):
        self.assertEqual(len(check_commanded_spell(201729, {**good_commanded(201729), "DefenseType": DEFENSE_MELEE})), 1)
        self.assertEqual(len(check_commanded_spell(201721, {**good_commanded(), "DefenseType": DEFENSE_RANGED})), 1)
        self.assertEqual(RANGED_COMMANDED, {201729, 201734, 201735, 201736})

    def test_pet_bit_in_a_bm_reader_is_caught(self):
        reader = {"ID": 201852, "EffectAura_1": 108, "EffectSpellClassMaskA_2": 0x10000000 | 0x400000}
        clean = {"ID": 201853, "EffectAura_1": 108, "EffectSpellClassMaskA_3": 0x400000}
        rows = {201852: reader, 201853: clean}
        self.assertEqual(len(check_no_pet_bit_readers(rows, (201852, 201853), [])), 1)
        self.assertEqual(check_no_pet_bit_readers(rows, (201853,), []), [])
        self.assertEqual(len(check_no_pet_bit_readers(rows, (201852,), [])), 1)
        # a carrier's own mask is not a reader: only SpellMod effects count
        self.assertEqual(check_no_pet_bit_readers({201720: good_commanded(201720)}, (201720,), []), [])
        proc = {"SpellId": 201809, "SpellFamilyMask1": 0x10000000}
        self.assertEqual(len(check_no_pet_bit_readers({}, (201809,), [proc])), 1)
        self.assertEqual(check_no_pet_bit_readers({}, (201809,), [{"SpellId": 5, "SpellFamilyMask1": 0x10000000}]), [])

    def test_command_press_guard(self):
        self.assertEqual(check_command_press(201800, good_press()), [])
        self.assertEqual(len(check_command_press(201800, {**good_press(), "SpellClassMask_3": 0x400000})), 1)
        self.assertEqual(len(check_command_press(201800, {**good_press(), "Attributes": 0x50000})), 1)
        self.assertEqual(len(check_command_press(201800, {**good_press(), "AttributesEx": 0x4})), 1)
        self.assertEqual(len(check_command_press(201801, None)), 1)

    def test_helper_copy_guard(self):
        self.assertEqual(check_helper_copy(201807, good_copy(), GOOD_ATTRS), [])
        self.assertEqual(len(check_helper_copy(201807, {**good_copy(), "SpellClassSet": 9}, GOOD_ATTRS)), 1)
        self.assertEqual(len(check_helper_copy(201807, {**good_copy(), "AttributesEx3": 0x40000}, GOOD_ATTRS)), 1)
        self.assertEqual(len(check_helper_copy(201807, good_copy(), [])), 1)
        self.assertEqual(len(check_helper_copy(201807, good_copy(), [{"spell_id": 201807, "attributes": 0x1000}])), 1)
        self.assertEqual(len(check_helper_copy(201807, None, GOOD_ATTRS)), 1)

    def test_family_bits_on_a_helper_carrier_are_caught(self):
        self.assertEqual(check_no_family_bits({201811: {"ID": 201811}}), [])
        self.assertEqual(len(check_no_family_bits({201811: {"ID": 201811, "SpellClassMask_3": 0x20000000}})), 1)
        self.assertEqual(check_no_family_bits({201814: {"ID": 201814, "SpellClassMask_3": 1}}), [])   # spare id, out of range

    def test_spell_proc_guard(self):
        self.assertEqual(check_spell_proc_rows(good_procs()), [])
        bad_attr = good_procs()
        bad_attr[0]["AttributesMask"] = 0
        self.assertEqual(len(check_spell_proc_rows(bad_attr)), 1)
        bad_phase = good_procs()
        bad_phase[1]["SpellPhaseMask"] = 0x2
        self.assertEqual(len(check_spell_proc_rows(bad_phase)), 1)
        negative = good_procs()
        negative[1]["SpellId"] = -201848
        self.assertEqual(len(check_spell_proc_rows(negative)), 2)      # negative key present, positive missing
        self.assertEqual(len(check_spell_proc_rows(good_procs()[:1])), 1)
        bad_family = good_procs()
        bad_family[1]["SpellFamilyMask0"] = 0x800
        self.assertEqual(len(check_spell_proc_rows(bad_family)), 1)

    def test_cobra_shot_transform_guard(self):
        self.assertEqual(check_cobra_shot_transform(good_transform(), GOOD_GROUPS, GOOD_RULES), [])
        self.assertEqual(len(check_cobra_shot_transform({**good_transform(), "EffectBasePoints_1": -1500},
                                                        GOOD_GROUPS, GOOD_RULES)), 1)
        self.assertEqual(len(check_cobra_shot_transform({**good_transform(), "EffectSpellClassMaskA_3": 0}, GOOD_GROUPS,
                                                        GOOD_RULES)), 1)
        self.assertEqual(len(check_cobra_shot_transform({**good_transform(), "EffectMiscValue_1": 0}, GOOD_GROUPS,
                                                        GOOD_RULES)), 1)
        self.assertEqual(len(check_cobra_shot_transform(good_transform(), [], GOOD_RULES)), 1)
        self.assertEqual(len(check_cobra_shot_transform(good_transform(), GOOD_GROUPS, [{"group_id": 1231, "stack_rule": 0}])), 1)
        self.assertEqual(len(check_cobra_shot_transform(None, GOOD_GROUPS, GOOD_RULES)), 1)

    def test_tbw_mastery_guard(self):
        self.assertEqual(check_tbw_mastery(good_tbw()), [])
        self.assertEqual(len(check_tbw_mastery({**good_tbw(), "EffectAuraPeriod_2": 0})), 1)
        self.assertEqual(len(check_tbw_mastery({**good_tbw(), "EffectAura_2": 4})), 1)
        self.assertEqual(len(check_tbw_mastery({**good_tbw(), "EffectSpellClassMaskA_2": 0x1000})), 1)
        self.assertEqual(len(check_tbw_mastery({**good_tbw(), "Attributes": 0})), 1)
        self.assertEqual(len(check_tbw_mastery({**good_tbw(), "EffectAura_1": 107})), 1)
        self.assertEqual(len(check_tbw_mastery({**good_tbw(), "SpellClassSet": 0})), 1)

    def test_linked_spell_guard(self):
        good = [{"spell_trigger": a, "spell_effect": b, "type": c} for a, b, c in LINKS]
        self.assertEqual(check_linked_spells(good), [])
        self.assertEqual(len(check_linked_spells(good[:-1])), 1)
        self.assertEqual(len(check_linked_spells([{**good[2], "type": 0}, *good[:2], good[3]])), 1)

    def test_longevity_guard(self):
        rows = {i: {"ID": i, "EffectSpellClassMaskA_2": 0x2000000, "EffectSpellClassMaskA_3": 0x200000} for i in LONGEVITY}
        self.assertEqual(check_longevity(rows), [])
        stale = {**rows, 53263: {"ID": 53263, "EffectSpellClassMaskA_2": 0x12000000, "EffectSpellClassMaskA_3": 0x8}}
        self.assertEqual(len(check_longevity(stale)), 1)
        self.assertEqual(len(check_longevity({53262: rows[53262]})), 2)

    def test_cobra_strikes_guard(self):
        def row(chance):
            return {"Effect_1": 6, "EffectAura_1": 4, "ProcChance": chance, "ProcTypeMask": 0x100}
        rows = {i: {"ID": i, **row(c)} for i, c in COBRA_STRIKES.items()}
        self.assertEqual(check_cobra_strikes(rows), [])
        self.assertEqual(len(check_cobra_strikes({**rows, 53256: {"ID": 53256, **row(20)}})), 1)
        self.assertEqual(len(check_cobra_strikes({**rows, 53259: {"ID": 53259, **row(10), "EffectAura_1": 42}})), 1)
        self.assertEqual(len(check_cobra_strikes({**rows, 53259: {"ID": 53259, **row(10), "EffectTriggerSpell_1": 53257}})), 1)
        self.assertEqual(len(check_cobra_strikes({**rows, 53260: {"ID": 53260, **row(15), "ProcTypeMask": 0x11140}})), 1)

    def test_beast_within_buff_guard(self):
        good = {"ID": 34471, "Effect_1": 6, "Effect_2": 6, "DurationIndex": 77}
        self.assertEqual(check_beast_within_buff(good, 77), [])
        self.assertEqual(len(check_beast_within_buff({**good, "Effect_3": 6, "EffectAura_3": 77}, 77)), 1)
        self.assertEqual(len(check_beast_within_buff({**good, "DurationIndex": 8}, 77)), 1)

    def test_inert_four_guard(self):
        noop = {"Effect_1": 6, "EffectAura_1": 4}
        rows = {34027: {"ID": 34027, **noop}, 58914: {"ID": 58914, **noop}, 60110: {"ID": 60110, **noop},
                60113: {"ID": 60113, **noop}}
        self.assertEqual(check_inert_four(rows), [])
        spellmod = {**rows, 60110: {"ID": 60110, "Effect_1": 6, "EffectAura_1": 107}}
        self.assertGreaterEqual(len(check_inert_four(spellmod)), 1)
        trigger = {**rows, 34027: {"ID": 34027, "Effect_1": 6, "EffectAura_1": 42, "EffectTriggerSpell_1": 58914}}
        self.assertGreaterEqual(len(check_inert_four(trigger)), 1)
        self.assertEqual(len(check_inert_four({**rows, 60113: {"ID": 60113, **noop, "ProcTypeMask": 0x100}})), 1)
        self.assertEqual(len(check_inert_four({**rows, 34027: {"ID": 34027, **noop, "ProcChance": 100}})), 1)
        self.assertEqual(len(check_inert_four({**rows, 58914: {"ID": 58914, "Effect_1": 3}})), 1)          # eff0 no longer DUMMY
        self.assertEqual(len(check_inert_four({**rows, 58914: {"ID": 58914, "Effect_1": 6, "EffectAura_1": 4,
                                                               "ProcCharges": 3}})), 1)
        self.assertEqual(len(check_inert_four({k: v for k, v in rows.items() if k != 60113})), 1)

    def test_tab_361_guard(self):
        talents = good_tab()
        self.assertEqual(sum(len(t["rank_spell_ids"]) for t in talents), TAB_POINTS)
        self.assertEqual(check_tab_361(talents, [], []), [])
        self.assertEqual(len(check_tab_361(talents[:-1], [], [])) >= 1, True)                        # 32 talents
        collide = [dict(t) for t in talents]
        collide[1]["tier"], collide[1]["column"] = collide[0]["tier"], collide[0]["column"]
        self.assertGreaterEqual(len(check_tab_361(collide, [], [])), 2)                              # cell clash + wrong cell
        prereq = [dict(t) for t in talents]
        prereq[3]["depends_on"] = {"talent_id": 1384, "rank": 3}
        self.assertEqual(len(check_tab_361(prereq, [], [])), 1)
        raw = [dict(t) for t in talents]
        raw[3]["raw_overrides"] = {"PrereqTalent_1": 1384}
        self.assertEqual(len(check_tab_361(raw, [], [])), 1)
        self.assertEqual(len(check_tab_361(talents, [{"ID": 1381, "TabID": TAB, "PrereqTalent_1": 1384}], [])), 1)
        points = [dict(t) for t in talents]
        points[0]["rank_spell_ids"] = points[0]["rank_spell_ids"] + [999999]
        self.assertEqual(len(check_tab_361(points, [], [])), 1)
        stampede = [dict(t) for t in talents]
        next(t for t in stampede if t["id"] == STAMPEDE_ROW)["rank_spell_ids"] = [201802]
        self.assertEqual(len(check_tab_361(stampede, [], [])), 1)                                    # row ranks
        self.assertEqual(len(check_tab_361(talents, [], [{"id": 30541, "skill_line": 202}])), 1)
        self.assertEqual(check_tab_361(talents, [], [{"id": 30541, "skill_line": 50}]), [])
        other_tab = talents + [{"id": 9999, "tab_id": 362, "tier": 0, "column": 0, "rank_spell_ids": [1]}]
        self.assertEqual(check_tab_361(other_tab, [], []), [])                                       # other tabs are ignored

    def test_stock_rank_helper_ignores_custom_and_other_tabs(self):
        talents = [{"tab_id": TAB, "rank_spell_ids": [19559, 201820]}, {"tab_id": 362, "rank_spell_ids": [1]}]
        self.assertEqual(_stock_ranks(talents), [19559])


if __name__ == "__main__":
    unittest.main()
