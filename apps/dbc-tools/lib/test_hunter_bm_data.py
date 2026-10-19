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
  (e) 201805 / 201807: family 0, SUPPRESS_CASTER_PROCS, one custom attr row of 0x208000 (S1a-3); no family bits on the
      helper carriers;
  (f) spell_proc rows of 201806 (attributes_mask 0x2) and 201848 (CAST phase 0x1), positive keys;
  (g) 201811 (stored -2001 / live -2000 since S1b PT-2, mask (0,0,0x20000000), spell_group 1231 + rule 1) and 201812 (shape, linked from 201857), the four
      capstone links;
  (h) Longevity 53262-53264 mask (0, 0x2000000, 0x200000); Cobra Strikes 53256 / 53259 / 53260 aura DUMMY with no
      trigger spell (S1b: spell_hun_cobra_strikes_bm does the reset);
  (i) 34471 has no eff2 and a 15 s duration; A9's four ids (34027, 58914, 60110, 60113) are inert by data;
  (j) tab 361 = 33 talents / 80 points, one talent per cell, no PrereqTalent, skill line 50, row 2139 = Stampede 201802
      since S1b. (34692 in no talent row lives in test_hunter_inert_keys.py.)

S1b (hunter-rework S1b-HANDOFF WP-A row A3, B1-B6, S1a carry-overs, PT-1..PT-6; S1b-WP-BRIEF decisions 1-6):

  (k) 201802 Stampede: no family bit (SpellClassSet 0 as built, A1 deviation 1), no IS_ABILITY, AttributesEx 0, eff0
      SUMMON misc inside STAMPEDE_ENTRY_MIN/MAX with MiscValueB 1021; SLA 30543 (skill line 50, class mask 4);
  (l) 201803 Steady Shot (Nature): Nature, family 0, CANT_CRIT, IGNORE_CASTER_MODIFIERS | SUPPRESS_CASTER_PROCS |
      ALWAYS_HIT, range >= 50000, TargetA 6, and NO custom attr 0x200000 (dropped by review M2);
  (m) 201809 + its spell_proc row (attributes 464, attributes_mask 0x2, hit mask CRIT, family mask d2 b22 | b23 only);
  (n) the six B1 spell_proc rows (positive keys, 34468 alone CAST | HIT) and the edited -53256 row (CAST, flags 0x100);
  (o) 201808 is MOD_DAMAGE_PERCENT_DONE misc 127; no Culling / Improved Viper rank holds a SpellMod on d2 b23;
  (p) guardians 300200-300207 inside STAMPEDE_ENTRY_MIN/MAX, npc_hun_stampede_beast, the BM 4.6 family, three models;
  (q) 53270 in no talent row (stock Talent.dbc overlaid by the package);
  (r) scripted_by positive keys of the five S1b spell classes; custom attrs 0x208000 on 201805 / 201807 (S1a-3);
  (s) PT-2 201811 live -2000; PT-3 56641 1000 ms with a matching CastingTimeIndex; S1a-1 201602 live >= 50; PT-6 Arcane
      Shot eff1 base points 199; PT-1 AttributesEx7 0 on 75593 / 75446 / 75447; S1a-2 DoT SpellMod on Phoenix's Plume /
      Master's Command;
  (t) PT-5: the 16 Command display passives (commanded + COMMAND_DISPLAY_OFFSET), names matching HunterMechanics.cpp's
      kits.
  (u) tooltip rows T1 (Pathfinding 19559 / 19560 / 201820), T16 (Shark Attack 201839 / 201840), PT2 (Mobility 53483 /
      53485): new text present, old text gone.

Every check is a pure function; the negative-fixture class feeds each one a minimal bad input.

Run directly:

    apps/dbc-tools/.venv/bin/python3 -m pytest apps/dbc-tools/lib/test_hunter_bm_data.py -q
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import build, dbcfmt, state  # noqa: E402
from lib.test_hunter_pet_data import check_equipped_item_class, package_data  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
HUNTER_MECHANICS_CPP = REPO_ROOT / "src" / "server" / "game" / "Entities" / "Unit" / "HunterMechanics.cpp"
HUNTER_DATA_H = REPO_ROOT / "src" / "server" / "game" / "Entities" / "Unit" / "Generated" / "HunterData.h"

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
CU_NO_POSITIVE_TAKEN_BONUS = 0x200000
HELPER_COPY_CUSTOM_ATTR = CU_IGNORE_ARMOR | CU_NO_POSITIVE_TAKEN_BONUS     # 0x208000 (S1a-3)

# ---- the id sets -----------------------------------------------------------------------------------------------------
COMMANDED = tuple(range(201720, 201737))                                  # 17 spells, 201736 is the splash
RANGED_COMMANDED = frozenset({201729, 201734, 201735, 201736})
COMMANDS = (201800, 201801)
BEAST_PET_BUFF = 201603
BEAST_MARKER = 201875
ATTR_PASSIVE = 0x40
ATTR_EX7_CONSOLIDATE = 0x10000000
AURA_DUMMY = 4
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
# player and never triggered, so the requirement is wanted. S1b (A6, PT-6) edits Arcane Shot 3044, which keeps its 2 for
# the same reason (a ranged-weapon shot the player casts). S2a (S2-HANDOFF M4 / stale line 6) adds the other player-cast
# ranged shots: Aimed Shot 19434, Chimera Shot 53209, Multi-Shot 2643 and the three marks 201920-201922. These are the
# ONLY exemptions from the -1 guard (test_hunter_mm_data.PLAYER_CAST_SHOTS mirrors this set). S3a (S3-HANDOFF N5) adds
# the Survival ranged shots it touches, stock class 2 kept: Explosive Shot 53301, Wyvern Sting 19386, Scatter Shot 19503
# and the retired Black Arrow 3674 (masks only).
EQUIPPED_ITEM_CLASS_EXEMPT = frozenset({56641, 3044, 19434, 53209, 2643, 201920, 201921, 201922,
                                        53301, 19386, 19503, 3674})
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
    2227: (9, 1),
    2139: (10, 1),
}
TAB_TALENT_COUNT = 33
TAB_POINTS = 80
STAMPEDE_ROW = 2139
STAMPEDE_SPELL = 201802
STOCK_BEAST_MASTERY_RANK = 53270     # granted only by linked_spell(56316, 53270, 2) since S1b; in no talent row
SKILL_LINE_BM = 50
CLASSMASK_HUNTER = 4
COMMAND_SLA_IDS = (30541, 30542, 30543)
STAMPEDE_SLA = 30543

# ---- S1b ids ---------------------------------------------------------------------------------------------------------
STEADY_SHOT_NATURE = 201803
BM_PET_PROCS = 201809
CULLING_BUFF = 201808
COBRA_SHOT_TRANSFORM = 201811
STEADY_SHOT = 56641
ARCANE_SHOT = 3044
VIPER_POISON = 201602
CULLING_RANKS = (201841, 201842, 201843)
IMPROVED_VIPER_RANKS = (201830, 201831)
FEROCIOUS_INSPIRATION_BUFFS = (75593, 75446, 75447)
PLUME_AND_MASTERS_COMMAND = (24443, 19575, 201826, 201852, 201853, 201854)    # Phoenix's Plume r1-r3, Master's Command
GUARDIANS = tuple(range(300200, 300208))
# BM 4.6: the Stampede beast's CreatureFamily (Wolf, Cat, Raptor, Bear, Spider, then the Ferocity / Tenacity / Cunning
# fallbacks Hyena, Boar, Bat).
GUARDIAN_FAMILY = {300200: 1, 300201: 2, 300202: 11, 300203: 4, 300204: 3, 300205: 25, 300206: 5, 300207: 24}
GUARDIAN_MODELS = 3
STAMPEDE_SCRIPT = "npc_hun_stampede_beast"
SUMMON_PROPERTIES = 1021
COMMANDED_SLOTTED = tuple(range(201720, 201736))       # 201736 (Venomous Cloud's splash) is in no kit slot
DISPLAY_IDS = tuple(range(201858, 201874))
NEW_S1B_IDS = (STAMPEDE_SPELL, STEADY_SHOT_NATURE, BM_PET_PROCS, *DISPLAY_IDS, 75446, 75447)
# Ids S1b edits (data or tooltip) in the hunter source files, from the S1b A1/A2/A4/A5/A6 reports and the diff; S1a's id
# sets above already hold the rest (201720-201736, 201800/201801, 201805-201811, 201820-201857, the BM stock ranks).
EDITED_S1B_IDS = (
    VIPER_POISON, 34074, 13161, 13163, 16827, 17253, 24604, 49966, 61846, 19574, 34026,      # hunter_spells / shared
    201710, 201715, 201717, 201718, 53175, 53176, 53186, 53187,                                  # hunter_pet
    19598, 19599, 19600, 34455, 34459, 34460, 56314, 56315, 56316, 75593,                        # hunter_trigger_spells
)
# B1: Steady Shot's Nature hit rows, one per rank, positive keys. Serpent's Swiftness r3 alone also sees CAST (KC cut).
STEADY_SHOT_NATURE_PROCS = {34466: 0x2, 34467: 0x2, 34468: 0x3}
STEADY_SHOT_FAMILY_MASK = (0, 0, 0x20000000)            # d2 b29
COBRA_STRIKES_PROC_KEY = -53256
BM_PET_PROC_FAMILY_MASK = (0, 0, 0x00C00000)            # d2 b22 (commanded) | b23 (basic), no d1 b28
# The five S1b spell classes (S1b-WP-BRIEF class table) and the positive keys each is bound to.
S1B_SCRIPT_BINDINGS = {
    "spell_hun_steady_shot_nature": frozenset(STEADY_SHOT_NATURE_PROCS),
    "spell_hun_cobra_strikes_bm": frozenset({53256, 53259, 53260}),
    "spell_hun_arcane_shot_bm": frozenset({ARCANE_SHOT}),
    "spell_hun_bm_pet_procs": frozenset({BM_PET_PROCS}),
    "spell_hun_stampede": frozenset({STAMPEDE_SPELL}),
}

EFFECT_SUMMON = 28
AURA_MOD_DAMAGE_PERCENT_DONE = 79
SCHOOL_MASK_NATURE = 8
SCHOOL_MASK_ALL = 127
SPELLMOD_DAMAGE = 0
SPELLMOD_DOT = 22
COMMANDED_READER_MASK = (0, 0, 0x400000)                # d2 b22
PET_BASIC_D2 = 0x800000                                 # d2 b23
TARGET_UNIT_CASTER = 1
TARGET_UNIT_TARGET_ENEMY = 6
ATTR_DO_NOT_DISPLAY = 0x80
DISPLAY_ATTRIBUTES = 0x150
ATTR_EX2_CANT_CRIT = 0x20000000
ATTR_EX3_IGNORE_CASTER_MODIFIERS = 0x20000000
ATTR_EX3_ALWAYS_HIT = 0x40000
STEADY_SHOT_NATURE_EX3 = ATTR_EX3_IGNORE_CASTER_MODIFIERS | ATTR_EX3_SUPPRESS_CASTER_PROCS | ATTR_EX3_ALWAYS_HIT
STEADY_SHOT_NATURE_MIN_RANGE = 50000.0
STEADY_SHOT_CAST_MS = 1000           # PT-3: + CalcCastTime's 500 ms = the real 1.5 s
VIPER_MIN_LIVE = 50                  # S1a-1: hundredths of a percent of max mana per tick
ARCANE_SHOT_MANA_BP = 199            # PT-6: eff1 DUMMY, 20.0% of base mana in tenths (live 200)
PROC_HIT_CRITICAL = 0x2
PROC_ATTR_TRIGGERED_CAN_PROC = 0x2


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


def live_value(row: dict, effect: int) -> int:
    """The smallest value `SpellEffectInfo::CalcValue` can return for effect `effect` (1-based): BasePoints plus 1 when
    DieSides >= 1 (it rolls irand(1, DieSides)), BasePoints alone when DieSides is 0."""
    return _i(row, f"EffectBasePoints_{effect}") + (1 if _i(row, f"EffectDieSides_{effect}") >= 1 else 0)


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


def check_command_gcd(spell_id: int, row: dict | None) -> list[str]:
    """(d2) a Command press starts the shared hunter GCD (S1b-FIX F-1): category 133, 1500 ms, and a cooldown of its own."""
    if row is None:
        return [f"{spell_id}: not declared"]
    bad = []
    if _i(row, "StartRecoveryCategory") != 133 or _i(row, "StartRecoveryTime") != 1500:
        bad.append(f"GCD {_i(row, 'StartRecoveryCategory')}/{_i(row, 'StartRecoveryTime')}, expected 133/1500")
    if _i(row, "RecoveryTime") not in (30000, 60000):
        bad.append(f"RecoveryTime {_i(row, 'RecoveryTime')}, expected 30000 / 60000")
    return [f"{spell_id}: {b}" for b in bad]


def check_beast_marker(marker: dict | None, buff: dict | None) -> list[str]:
    """The hunter-side Aspect of the Beast marker (S1b-FIX F-2): visible dummy, not passive, no consolidate flag, the
    pet buff's duration, no family bits, tooltip read from 201603."""
    if marker is None or buff is None:
        return [f"{BEAST_MARKER}/{BEAST_PET_BUFF}: not declared"]
    bad = []
    if _i(marker, "Attributes") & ATTR_PASSIVE:
        bad.append("passive (0x40): hidden from the buff bar")
    if _i(marker, "AttributesEx7") & ATTR_EX7_CONSOLIDATE:
        bad.append("AttributesEx7 consolidate flag (0x10000000) set")
    if _i(marker, "EquippedItemClass") != -1:
        bad.append(f"EquippedItemClass {marker.get('EquippedItemClass')}, expected -1")
    if any(spell_mask(marker)) or any(effect_mask(marker, e) != (0, 0, 0) for e in range(3)):
        bad.append("family bits set")
    if (_i(marker, "Effect_1"), _i(marker, "EffectAura_1")) != (6, AURA_DUMMY) or _i(marker, "Effect_2") or _i(marker, "Effect_3"):
        bad.append("must be exactly one APPLY_AURA / SPELL_AURA_DUMMY effect")
    # both rows are built from duration_ms through the same SpellDuration lookup, so equal ms means an equal index
    if not _i(marker, "DurationIndex") or _i(marker, "DurationIndex") != _i(buff, "DurationIndex"):
        bad.append("duration differs from 201603")
    if "$201603s1" not in str(marker.get("AuraDescription_Lang_enUS", "")):
        bad.append("AuraDescription must read $201603s1, not a hard-coded percent")
    return [f"{BEAST_MARKER}: {b}" for b in bad]


def check_helper_copy(spell_id: int, row: dict | None, custom_attrs: list[dict]) -> list[str]:
    """(e) Beast Cleave / Spiked Collar copy: family 0, SUPPRESS_CASTER_PROCS, exactly one custom attr row of 0x208000
    (IGNORE_ARMOR | NO_POSITIVE_TAKEN_BONUS, S1a-3: the copy's BP already carries the victim's damage-taken mods)."""
    if row is None:
        return [f"{spell_id}: not declared"]
    bad = []
    if _i(row, "SpellClassSet") != 0:
        bad.append(f"SpellClassSet {row.get('SpellClassSet')}, expected 0")
    if not _i(row, "AttributesEx3") & ATTR_EX3_SUPPRESS_CASTER_PROCS:
        bad.append(f"AttributesEx3 0x{_i(row, 'AttributesEx3'):X} lacks SUPPRESS_CASTER_PROCS (0x10000)")
    bad += check_custom_attr(spell_id, custom_attrs, HELPER_COPY_CUSTOM_ATTR, prefix=False)
    return [f"{spell_id}: {b}" for b in bad]


def check_custom_attr(spell_id: int, custom_attrs: list[dict], want: int, prefix: bool = True) -> list[str]:
    """Exactly one spell_custom_attr row for `spell_id` (the table is keyed on the spell id: a second row would replace
    the first) and its value is exactly `want`."""
    attrs = [int(c["attributes"]) for c in custom_attrs if int(c["spell_id"]) == spell_id]
    if attrs == [want]:
        return []
    problem = f"custom attr rows {[hex(a) for a in attrs]}, expected exactly one of 0x{want:X}"
    return [f"{spell_id}: {problem}" if prefix else problem]


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
    """(g) 201811: eff0 ADD_FLAT_MODIFIER CASTING_TIME (misc 10) stored -2001 (live -2000, S1b PT-2: CalcCastTime adds
    500 ms to the ranged-slot Steady Shot before mods) on (0,0,0x20000000), attributes 464, in spell_group 1231 whose
    rule is 1 (EXCLUSIVE)."""
    if row is None:
        return ["201811: not declared"]
    bad = []
    if _i(row, "Effect_1") != EFFECT_APPLY_AURA or _i(row, "EffectAura_1") != AURA_ADD_FLAT_MODIFIER:
        bad.append(f"eff0 is {row.get('Effect_1')}/{row.get('EffectAura_1')}, expected APPLY_AURA / ADD_FLAT_MODIFIER")
    if _i(row, "EffectMiscValue_1") != 10:
        bad.append(f"eff0 misc {row.get('EffectMiscValue_1')}, expected 10 (CASTING_TIME)")
    if _i(row, "EffectBasePoints_1") != -2001 or live_value(row, 1) != -2000:
        bad.append(f"eff0 stored base points {row.get('EffectBasePoints_1')} / die sides "
                   f"{row.get('EffectDieSides_1')}, expected -2001 / 1 (live -2000, PT-2)")
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
    (entry, raw override and built row), skill line 50 on the Command SkillLineAbility rows, (10,1) = 2139 -> Stampede
    201802 (S1b B6; the built row's SpellRank_1 too)."""
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
        if _i(row, "ID") == STAMPEDE_ROW:
            ranks = [_i(row, f"SpellRank_{n}") for n in range(1, 10)]
            if ranks != [STAMPEDE_SPELL] + [0] * 8:
                bad.append(f"talent {STAMPEDE_ROW}: built SpellRank_1..9 {ranks}, expected [{STAMPEDE_SPELL}, 0, ...]")
    stampede = next((t for t in mine if int(t["id"]) == STAMPEDE_ROW), None)
    if stampede is None:
        bad.append(f"row {STAMPEDE_ROW} not declared in tab {TAB}")
    elif list(stampede.get("rank_spell_ids") or []) != [STAMPEDE_SPELL]:     # its cell (10,1) is TAB_CELLS'
        bad.append(f"row {STAMPEDE_ROW} ranks {stampede.get('rank_spell_ids')}, expected [{STAMPEDE_SPELL}] (S1b B6)")
    for entry in sla_entries:
        if int(entry["id"]) in COMMAND_SLA_IDS and int(entry["skill_line"]) != SKILL_LINE_BM:
            bad.append(f"SkillLineAbility {entry['id']}: skill line {entry['skill_line']}, expected {SKILL_LINE_BM}")
    return bad


# ---- S1b checks ------------------------------------------------------------------------------------------------------

def _proc_mask(proc: dict) -> tuple[int, int, int]:
    return tuple(_u32(proc.get(f"SpellFamilyMask{n}")) for n in (0, 1, 2))


def _procs_by_key(procs: list[dict]) -> dict[int, list[dict]]:
    out: dict[int, list[dict]] = {}
    for p in procs:
        out.setdefault(int(p["SpellId"]), []).append(p)
    return out


def _aura_dummy_on_self(row: dict) -> str:
    """'' when eff0 is APPLY_AURA / DUMMY at target 1 (the caster), else the problem."""
    got = (_i(row, "Effect_1"), _i(row, "EffectAura_1"), _i(row, "ImplicitTargetA_1"))
    if got == (EFFECT_APPLY_AURA, AURA_DUMMY, TARGET_UNIT_CASTER):
        return ""
    return f"eff0 {got[0]}/{got[1]} at target {got[2]}, expected APPLY_AURA / DUMMY at 1"


def check_stampede_spell(row: dict | None, entry_min: int, entry_max: int) -> list[str]:
    """(k) 201802 as built: SpellClassSet 0 and no family bit (A1 deviation 1: family 0 keeps the stock Readiness off
    it until S2, Q16), no IS_ABILITY (a bit-less IS_ABILITY button is a gcd_haste error), AttributesEx 0, eff0 SUMMON
    whose misc is a Stampede guardian entry and whose MiscValueB is SummonProperties 1021."""
    if row is None:
        return [f"{STAMPEDE_SPELL}: not declared"]
    bad = []
    if _i(row, "SpellClassSet") != 0 or any(spell_mask(row)):
        bad.append(f"SpellClassSet {row.get('SpellClassSet')} mask {_hex(spell_mask(row))}, expected 0, no family bit")
    if _i(row, "Attributes") & ATTR_IS_ABILITY:
        bad.append(f"Attributes 0x{_i(row, 'Attributes'):X} holds IS_ABILITY (0x10)")
    if _i(row, "AttributesEx") != 0:
        bad.append(f"AttributesEx 0x{_i(row, 'AttributesEx'):X}, expected 0")
    if _i(row, "Effect_1") != EFFECT_SUMMON:
        bad.append(f"eff0 type {row.get('Effect_1')}, expected SUMMON (28): spell_hun_stampede hooks EFFECT_0 SUMMON")
    if not entry_min <= _i(row, "EffectMiscValue_1") <= entry_max:
        bad.append(f"eff0 misc {row.get('EffectMiscValue_1')}, expected a guardian entry in {entry_min}-{entry_max}")
    if _i(row, "EffectMiscValueB_1") != SUMMON_PROPERTIES:
        bad.append(f"eff0 MiscValueB {row.get('EffectMiscValueB_1')}, expected {SUMMON_PROPERTIES}")
    return [f"{STAMPEDE_SPELL}: {b}" for b in bad]


def check_stampede_sla(sla_entries: list[dict]) -> list[str]:
    """(k) SkillLineAbility 30543 teaches 201802 on skill line 50 to class mask 4 (hunter), one row."""
    rows = [e for e in sla_entries if int(e["id"]) == STAMPEDE_SLA]
    if len(rows) != 1:
        return [f"SkillLineAbility {STAMPEDE_SLA}: {len(rows)} rows declared, expected 1"]
    e = rows[0]
    got = (int(e["spell_id"]), int(e["skill_line"]), int(e.get("class_mask") or 0))
    want = (STAMPEDE_SPELL, SKILL_LINE_BM, CLASSMASK_HUNTER)
    if got == want:
        return []
    return [f"SkillLineAbility {STAMPEDE_SLA}: (spell, skill line, class mask) {got}, expected {want}"]


def check_steady_shot_nature(row: dict | None, range_max: dict[int, float], custom_attrs: list[dict]) -> list[str]:
    """(l) 201803: Nature, family 0 without bits, CANT_CRIT, Ex3 IGNORE_CASTER_MODIFIERS | SUPPRESS_CASTER_PROCS |
    ALWAYS_HIT, a range of at least 50000 yd (triggered casts are range-checked, L6), eff0 SCHOOL_DAMAGE at TargetA 6,
    and no spell_custom_attr row carrying 0x200000 (NO_POSITIVE_TAKEN_BONUS): brief decision 3 added it, the S1b review
    (M2) dropped it again. `range_max`: SpellRange index -> RangeMax_1."""
    if row is None:
        return [f"{STEADY_SHOT_NATURE}: not declared"]
    bad = []
    if _i(row, "SchoolMask") != SCHOOL_MASK_NATURE:
        bad.append(f"SchoolMask {row.get('SchoolMask')}, expected {SCHOOL_MASK_NATURE} (Nature)")
    if _i(row, "SpellClassSet") != 0 or any(spell_mask(row)):
        bad.append(f"SpellClassSet {row.get('SpellClassSet')} mask {_hex(spell_mask(row))}, expected family 0, no bits")
    if not _i(row, "AttributesEx2") & ATTR_EX2_CANT_CRIT:
        bad.append(f"AttributesEx2 0x{_i(row, 'AttributesEx2'):X} lacks CANT_CRIT (0x20000000)")
    ex3 = _u32(row.get("AttributesEx3"))
    if ex3 & STEADY_SHOT_NATURE_EX3 != STEADY_SHOT_NATURE_EX3:
        bad.append(f"AttributesEx3 0x{ex3:X} lacks 0x{STEADY_SHOT_NATURE_EX3 & ~ex3:X} of IGNORE_CASTER_MODIFIERS | "
                   f"SUPPRESS_CASTER_PROCS | ALWAYS_HIT")
    yards = range_max.get(_i(row, "RangeIndex"))
    if yards is None or float(yards) < STEADY_SHOT_NATURE_MIN_RANGE:
        bad.append(f"RangeIndex {row.get('RangeIndex')} ({yards} yd), expected >= {STEADY_SHOT_NATURE_MIN_RANGE:.0f}")
    if _i(row, "Effect_1") != EFFECT_SCHOOL_DAMAGE or _i(row, "ImplicitTargetA_1") != TARGET_UNIT_TARGET_ENEMY:
        bad.append(f"eff0 {row.get('Effect_1')} at TargetA {row.get('ImplicitTargetA_1')}, expected SCHOOL_DAMAGE (2) "
                   f"at 6")
    attrs = [int(c["attributes"]) for c in custom_attrs if int(c["spell_id"]) == STEADY_SHOT_NATURE]
    if any(a & CU_NO_POSITIVE_TAKEN_BONUS for a in attrs):
        bad.append(f"custom attr rows {[hex(a) for a in attrs]} carry 0x200000 (NO_POSITIVE_TAKEN_BONUS), dropped by "
                   f"review M2")
    return [f"{STEADY_SHOT_NATURE}: {b}" for b in bad]


def check_bm_pet_procs(row: dict | None, procs: list[dict]) -> list[str]:
    """(m) 201809: attributes 464, eff0 aura DUMMY at target 1, DBC ProcTypeMask 0x10110 / ProcChance 100; its one
    spell_proc row (positive key): flags 0x10110, family 9 mask d2 b22 | b23 only, HIT phase, hit mask CRIT 0x2,
    attributes_mask 0x2 (TRIGGERED_CAN_PROC, L8). The row's chance is 0 (A1 deviation 2: the DBC ProcChance applies)."""
    bad = []
    if row is None:
        bad.append("not declared")
    else:
        if _i(row, "Attributes") != 464:
            bad.append(f"Attributes {row.get('Attributes')}, expected 464")
        if _aura_dummy_on_self(row):
            bad.append(_aura_dummy_on_self(row) + " (OnEffectProc EFFECT_0 SPELL_AURA_DUMMY)")
        if _i(row, "ProcTypeMask") != 0x10110 or _i(row, "ProcChance") != 100:
            bad.append(f"ProcTypeMask 0x{_i(row, 'ProcTypeMask'):X} ProcChance {row.get('ProcChance')}, "
                       f"expected 0x10110 / 100")
    by_key = _procs_by_key(procs)
    if -BM_PET_PROCS in by_key:
        bad.append(f"spell_proc -{BM_PET_PROCS}: negative key (no ranks, L7)")
    rows = by_key.get(BM_PET_PROCS, [])
    if len(rows) != 1:
        bad.append(f"spell_proc {BM_PET_PROCS}: {len(rows)} rows, expected 1")
    for p in rows[:1]:
        if _i(p, "ProcFlags") != 0x10110:
            bad.append(f"spell_proc ProcFlags 0x{_i(p, 'ProcFlags'):X}, expected 0x10110")
        if _i(p, "SpellFamilyName") != SPELLFAMILY_HUNTER or _proc_mask(p) != BM_PET_PROC_FAMILY_MASK:
            bad.append(f"spell_proc family {p.get('SpellFamilyName')} mask {_hex(_proc_mask(p))}, expected 9 "
                       f"{_hex(BM_PET_PROC_FAMILY_MASK)} (d2 b22 | b23 only)")
        if _i(p, "SpellPhaseMask") != 0x2:
            bad.append(f"spell_proc SpellPhaseMask {p.get('SpellPhaseMask')}, expected HIT 0x2")
        if _i(p, "HitMask") != PROC_HIT_CRITICAL:
            bad.append(f"spell_proc HitMask 0x{_i(p, 'HitMask'):X}, expected CRITICAL 0x2 only")
        if not _i(p, "AttributesMask") & PROC_ATTR_TRIGGERED_CAN_PROC:
            bad.append(f"spell_proc AttributesMask 0x{_i(p, 'AttributesMask'):X} lacks TRIGGERED_CAN_PROC 0x2 (L8)")
    return [f"{BM_PET_PROCS}: {b}" for b in bad]


def check_steady_shot_nature_procs(procs: list[dict], expected=STEADY_SHOT_NATURE_PROCS) -> list[str]:
    """(n) B1: one positive-key spell_proc row per Serpent's Swiftness / Cobra Shot rank (no -34466 / -201849 chain
    row), flags 0x100, family 9 mask Steady Shot d2 b29 only, hit mask 0; phase HIT 0x2, except 34468 CAST | HIT 0x3."""
    by_key = _procs_by_key(procs)
    bad = []
    for key in (-34466, -201849):
        if key in by_key:
            bad.append(f"spell_proc {key}: a chain row (B1 replaces it with one positive row per rank)")
    for spell_id, phase in expected.items():
        rows = by_key.get(spell_id, [])
        if -spell_id in by_key:
            bad.append(f"spell_proc -{spell_id}: negative key, use +{spell_id} (L7)")
        if len(rows) != 1:
            bad.append(f"spell_proc {spell_id}: {len(rows)} rows, expected 1")
            continue
        p = rows[0]
        if _i(p, "ProcFlags") != 0x100:
            bad.append(f"spell_proc {spell_id}: ProcFlags 0x{_i(p, 'ProcFlags'):X}, expected 0x100")
        if _i(p, "SpellFamilyName") != SPELLFAMILY_HUNTER or _proc_mask(p) != STEADY_SHOT_FAMILY_MASK:
            bad.append(f"spell_proc {spell_id}: family {p.get('SpellFamilyName')} mask {_hex(_proc_mask(p))}, "
                       f"expected 9 {_hex(STEADY_SHOT_FAMILY_MASK)} (Steady Shot only)")
        if _i(p, "SpellPhaseMask") != phase:
            bad.append(f"spell_proc {spell_id}: SpellPhaseMask 0x{_i(p, 'SpellPhaseMask'):X}, expected 0x{phase:X}")
        if _i(p, "HitMask") != 0:
            bad.append(f"spell_proc {spell_id}: HitMask 0x{_i(p, 'HitMask'):X}, expected 0")
    return bad


def check_cobra_strikes_proc(procs: list[dict]) -> list[str]:
    """(n) B2: H0's -53256 row edited in place (one row, still the chain key): flags 0x100, family 9 mask Steady Shot d2
    b29 only, CAST phase 0x1 (once per Steady Shot cast), hit mask 0; no positive-key twin on any rank."""
    by_key = _procs_by_key(procs)
    bad = []
    for spell_id in (53256, 53259, 53260):
        if spell_id in by_key:
            bad.append(f"spell_proc {spell_id}: a positive-key twin of the {COBRA_STRIKES_PROC_KEY} chain row")
    rows = by_key.get(COBRA_STRIKES_PROC_KEY, [])
    if len(rows) != 1:
        return bad + [f"spell_proc {COBRA_STRIKES_PROC_KEY}: {len(rows)} rows, expected 1 (edited in place)"]
    p = rows[0]
    if _i(p, "ProcFlags") != 0x100:
        bad.append(f"spell_proc {COBRA_STRIKES_PROC_KEY}: ProcFlags 0x{_i(p, 'ProcFlags'):X}, expected 0x100")
    if _i(p, "SpellFamilyName") != SPELLFAMILY_HUNTER or _proc_mask(p) != STEADY_SHOT_FAMILY_MASK:
        bad.append(f"spell_proc {COBRA_STRIKES_PROC_KEY}: family {p.get('SpellFamilyName')} mask "
                   f"{_hex(_proc_mask(p))}, expected 9 {_hex(STEADY_SHOT_FAMILY_MASK)}")
    if _i(p, "SpellPhaseMask") != 0x1:
        bad.append(f"spell_proc {COBRA_STRIKES_PROC_KEY}: SpellPhaseMask 0x{_i(p, 'SpellPhaseMask'):X}, "
                   f"expected CAST 0x1")
    if _i(p, "HitMask") != 0:
        bad.append(f"spell_proc {COBRA_STRIKES_PROC_KEY}: HitMask 0x{_i(p, 'HitMask'):X}, expected 0")
    return bad


def check_culling_buff_and_readers(rows_by_id: dict[int, dict]) -> list[str]:
    """(o) B4 carry-over: 201808 eff0 APPLY_AURA MOD_DAMAGE_PERCENT_DONE misc 127 (all schools), so it scales all pet
    damage evenly and never stacks with the Tenacity kit's DAMAGE op on the basics; no Culling the Herd / Improved
    Aspect of the Viper rank holds a SpellMod effect whose mask reads d2 b23 (the basic attacks)."""
    bad = []
    row = rows_by_id.get(CULLING_BUFF)
    if row is None:
        bad.append(f"{CULLING_BUFF}: not declared")
    elif (_i(row, "Effect_1"), _i(row, "EffectAura_1"), _i(row, "EffectMiscValue_1")) != (
            EFFECT_APPLY_AURA, AURA_MOD_DAMAGE_PERCENT_DONE, SCHOOL_MASK_ALL):
        bad.append(f"{CULLING_BUFF}: eff0 {row.get('Effect_1')}/{row.get('EffectAura_1')} misc "
                   f"{row.get('EffectMiscValue_1')}, expected APPLY_AURA / MOD_DAMAGE_PERCENT_DONE (79) misc 127")
    for spell_id in (*CULLING_RANKS, *IMPROVED_VIPER_RANKS):
        rank = rows_by_id.get(spell_id)
        if rank is None:
            bad.append(f"{spell_id}: not declared")
            continue
        for index, _effect, aura in _effects(rank):
            if aura in SPELLMOD_AURAS and effect_mask(rank, index)[2] & PET_BASIC_D2:
                bad.append(f"{spell_id}: SpellMod effect {index} mask {_hex(effect_mask(rank, index))} reads d2 b23 "
                           f"(the basic attacks; Culling is the 201808 aura)")
    return bad


def check_stampede_guardians(creatures: list[dict], models: list[dict], entry_min: int, entry_max: int) -> list[str]:
    """(p) B6: each of 300200-300207 declared once, inside PET's STAMPEDE_ENTRY_MIN/MAX (GetPassthroughKind), ScriptName
    npc_hun_stampede_beast, type 1 (beast), the BM 4.6 family, and three creature_template_model rows (idx 0-2,
    probability 1.0)."""
    bad = []
    by_entry: dict[int, list[dict]] = {}
    for c in creatures:
        by_entry.setdefault(int(c["entry"]), []).append(c)
    model_rows: dict[int, list[dict]] = {}
    for m in models:
        model_rows.setdefault(int(m["CreatureID"]), []).append(m)
    for entry, family in GUARDIAN_FAMILY.items():
        rows = by_entry.get(entry, [])
        if len(rows) != 1:
            bad.append(f"creature {entry}: {len(rows)} creature_template rows, expected 1")
            continue
        c = rows[0]
        if not entry_min <= entry <= entry_max:
            bad.append(f"creature {entry}: outside STAMPEDE_ENTRY_MIN/MAX {entry_min}-{entry_max}")
        if c.get("ScriptName") != STAMPEDE_SCRIPT:
            bad.append(f"creature {entry}: ScriptName {c.get('ScriptName')!r}, expected {STAMPEDE_SCRIPT!r}")
        if int(c.get("family") or 0) != family:
            bad.append(f"creature {entry}: family {c.get('family')}, expected {family} (BM 4.6)")
        if int(c.get("type") or 0) != 1:
            bad.append(f"creature {entry}: type {c.get('type')}, expected 1 (beast)")
        mine = model_rows.get(entry, [])
        idx = sorted(int(m["Idx"]) for m in mine)
        if idx != list(range(GUARDIAN_MODELS)) or any(float(m["Probability"]) != 1.0 for m in mine):
            bad.append(f"creature {entry}: model idx {idx} probabilities {[m['Probability'] for m in mine]}, expected "
                       f"{GUARDIAN_MODELS} models idx 0-{GUARDIAN_MODELS - 1} at 1.0")
    for entry in sorted(by_entry):
        if entry_min <= entry <= entry_max and entry not in GUARDIAN_FAMILY:
            bad.append(f"creature {entry}: inside the Stampede block but not one of the BM 4.6 guardians")
    return bad


def check_no_talent_teaches(talent_rows: list[dict], spell_id: int = STOCK_BEAST_MASTERY_RANK) -> list[str]:
    """(q) `spell_id` is in no SpellRank_1..9 of the built Talent rows (stock Talent.dbc overlaid by the package), so
    learning / resetting talents never grants or strips it (S1b L15; Kindred Spirits' link grants 53270)."""
    return [f"talent {r['ID']}: SpellRank_{n} is {spell_id}" for r in talent_rows for n in range(1, 10)
            if _i(r, f"SpellRank_{n}") == spell_id]


def check_script_bindings(bound: list[dict], expected=S1B_SCRIPT_BINDINGS) -> list[str]:
    """(r) every S1b spell class is bound exactly to its positive keys (L7): no negative key, nothing missing or
    extra."""
    got: dict[str, set[int]] = {}
    for r in bound:
        got.setdefault(r["ScriptName"], set()).add(int(r["spell_id"]))
    bad = []
    for name, ids in expected.items():
        have = got.get(name, set())
        negative = sorted(i for i in have if i < 0)
        if negative:
            bad.append(f"{name}: negative keys {negative} (L7: positive keys only)")
        if have != set(ids):
            bad.append(f"{name}: bound to {sorted(have)}, expected {sorted(ids)}")
    return bad


def check_s1b_values(rows_by_id: dict[int, dict], entries_by_id: dict[int, dict],
                     cast_times: dict[int, int]) -> list[str]:
    """(s) PT-3: 56641 declares cast_time_ms 1000 and its CastingTimeIndex resolves to 1000 ms (`cast_times`: index ->
    Base); S1a-1: 201602 eff0 live >= 50; PT-6: Arcane Shot eff1 (Effect_2) DUMMY stored 199; PT-1: AttributesEx7 0
    (no Consolidated Buffs) on 75593 / 75446 / 75447."""
    bad = []
    steady, entry = rows_by_id.get(STEADY_SHOT), entries_by_id.get(STEADY_SHOT)
    if steady is None or entry is None:
        bad.append(f"{STEADY_SHOT}: not declared")
    else:
        if entry.get("cast_time_ms") != STEADY_SHOT_CAST_MS:
            bad.append(f"{STEADY_SHOT}: cast_time_ms {entry.get('cast_time_ms')}, "
                       f"expected {STEADY_SHOT_CAST_MS} (PT-3)")
        base = cast_times.get(_i(steady, "CastingTimeIndex"))
        if base != STEADY_SHOT_CAST_MS:
            bad.append(f"{STEADY_SHOT}: CastingTimeIndex {steady.get('CastingTimeIndex')} is {base} ms, expected "
                       f"{STEADY_SHOT_CAST_MS} (it must match cast_time_ms)")
    viper = rows_by_id.get(VIPER_POISON)
    if viper is None:
        bad.append(f"{VIPER_POISON}: not declared")
    elif live_value(viper, 1) < VIPER_MIN_LIVE:
        bad.append(f"{VIPER_POISON}: eff0 live {live_value(viper, 1)}, expected >= {VIPER_MIN_LIVE} "
                   f"(S1a-1, x10 storage)")
    arcane = rows_by_id.get(ARCANE_SHOT)
    if arcane is None:
        bad.append(f"{ARCANE_SHOT}: not declared")
    elif _i(arcane, "Effect_2") != EFFECT_DUMMY or _i(arcane, "EffectBasePoints_2") != ARCANE_SHOT_MANA_BP:
        bad.append(f"{ARCANE_SHOT}: eff1 type {arcane.get('Effect_2')} bp {arcane.get('EffectBasePoints_2')}, expected "
                   f"DUMMY (3) / {ARCANE_SHOT_MANA_BP} (PT-6: 20.0% of base mana in tenths)")
    for spell_id in FEROCIOUS_INSPIRATION_BUFFS:
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
        elif _i(row, "AttributesEx7") != 0:
            bad.append(f"{spell_id}: AttributesEx7 0x{_i(row, 'AttributesEx7'):X}, expected 0 (PT-1)")
    return bad


def check_dot_spellmods(rows_by_id: dict[int, dict], ids=PLUME_AND_MASTERS_COMMAND) -> list[str]:
    """(s) S1a-2: each Phoenix's Plume / Master's Command rank holds an ADD_PCT_MODIFIER DOT (misc 22) effect on the
    commanded mask d2 b22 next to its DAMAGE (misc 0) effect on the same mask, with the same base points."""
    bad = []
    for spell_id in ids:
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
            continue
        by_op: dict[int, list[int]] = {}
        for index, effect, aura in _effects(row):
            if effect == EFFECT_APPLY_AURA and aura == AURA_ADD_PCT_MODIFIER \
                    and effect_mask(row, index) == COMMANDED_READER_MASK:
                by_op.setdefault(_i(row, f"EffectMiscValue_{index}"), []).append(_i(row, f"EffectBasePoints_{index}"))
        dot, damage = by_op.get(SPELLMOD_DOT), by_op.get(SPELLMOD_DAMAGE)
        if not dot:
            bad.append(f"{spell_id}: no ADD_PCT_MODIFIER DOT (misc 22) effect on {_hex(COMMANDED_READER_MASK)}")
        elif not damage or dot != damage:
            bad.append(f"{spell_id}: DOT base points {dot} differ from the DAMAGE effect's {damage}")
    return bad


def parse_kit_slots(mechanics_cpp: str, hunter_data_h: str) -> dict[int, str]:
    """PT-5: commanded spell id -> 'I' / 'II', read from the PetKit tables of HunterMechanics.cpp (the type defaults
    and GetFamilyKits; `struct PetKit { basic; utility; commandI; commandII; }` in HunterMechanics.h), with the
    SPELL_*_COMMAND names resolved through HunterData.h. A spell found in both slots maps to 'both'."""
    names = {m.group(1): int(m.group(2))
             for m in re.finditer(r"constexpr\s+u?int32\s+(\w+)\s*=\s*(\d+)\s*;", hunter_data_h)}
    slots: dict[int, str] = {}
    for m in re.finditer(r"\{\s*SPELL_\w+\s*,\s*SPELL_\w+\s*,\s*(SPELL_\w+_COMMAND)\s*,\s*(SPELL_\w+_COMMAND)\s*\}",
                         mechanics_cpp):
        for name, slot in ((m.group(1), "I"), (m.group(2), "II")):
            spell_id = names.get(name)
            if spell_id is None:
                slots.setdefault(-1, name)      # an unresolved name is reported by the check below
                continue
            if slots.get(spell_id, slot) != slot:
                slot = "both"
            slots[spell_id] = slot
    return slots


def check_command_displays(rows_by_id: dict[int, dict], offset: int, slots: dict[int, str], bound: list[dict],
                           talents: list[dict], trainer_spells: list[dict]) -> list[str]:
    """(t) PT-5 (brief decision 1): for each commanded spell 201720-201735 a display spell at id + offset (offset = the
    COMMAND_DISPLAY_OFFSET const, 138): Attributes 0x150 (PASSIVE, no DO_NOT_DISPLAY 0x80), eff0 APPLY_AURA DUMMY at
    target 1, family 0 without bits, Name "Command <slot>: <commanded name>" with the slot the kit tables give it;
    no script binding, in no talent row, no trainer row. 201736 (no slot) has no display."""
    bad = []
    if -1 in slots:
        bad.append(f"HunterMechanics.cpp kit names {slots[-1]} not found in HunterData.h")
    displays = set()
    for commanded in COMMANDED_SLOTTED:
        display = commanded + offset
        displays.add(display)
        row, source = rows_by_id.get(display), rows_by_id.get(commanded)
        slot = slots.get(commanded)
        if slot not in ("I", "II"):
            bad.append(f"{commanded}: kit slot {slot!r} in HunterMechanics.cpp, expected exactly one of I / II")
        if row is None:
            bad.append(f"{display}: display of {commanded} not declared")
            continue
        if _i(row, "Attributes") != DISPLAY_ATTRIBUTES or _i(row, "Attributes") & ATTR_DO_NOT_DISPLAY:
            bad.append(f"{display}: Attributes 0x{_i(row, 'Attributes'):X}, expected 0x150 (no DO_NOT_DISPLAY 0x80)")
        if _aura_dummy_on_self(row):
            bad.append(f"{display}: {_aura_dummy_on_self(row)}")
        if any(_i(row, f"Effect_{n}") for n in (2, 3)):
            bad.append(f"{display}: has effects beyond eff0")
        if _i(row, "SpellClassSet") != 0 or any(spell_mask(row)):
            bad.append(f"{display}: SpellClassSet {row.get('SpellClassSet')} mask {_hex(spell_mask(row))}, "
                       f"expected none")
        if source is not None and slot in ("I", "II"):
            want = f"Command {slot}: {source.get('Name_Lang_enUS')}"
            if row.get("Name_Lang_enUS") != want:
                bad.append(f"{display}: Name {row.get('Name_Lang_enUS')!r}, expected {want!r}")
    if COMMANDED[-1] + offset in rows_by_id:
        bad.append(f"{COMMANDED[-1] + offset}: a display for the splash {COMMANDED[-1]}, which no kit slot names")
    for r in bound:
        if int(r["spell_id"]) in displays:
            bad.append(f"{r['spell_id']}: display spell bound to {r['ScriptName']} (no script, PT-5)")
    for t in talents:
        for sid in t.get("rank_spell_ids") or []:
            if sid in displays:
                bad.append(f"talent {t['id']}: rank {sid} is a display spell")
    for t in trainer_spells:
        if int(t["SpellId"]) in displays:
            bad.append(f"trainer {t['TrainerId']}: teaches display spell {t['SpellId']}")
    return bad


# (u) S1b-HANDOFF tooltip table rows T1 / T16 / PT2 (coordinator: "only if cheap"): the new text is in the built
# Description, the old text is gone. id -> (required substrings, forbidden substrings).
_T1_MAIN = ("Increases the chance for your Aspect of the Monkey to grant Versatility by $s1%, and increases your "
            "Versatility by $s2%.")
_T1_CAP = ("Increases the speed bonus of your Aspect of the Cheetah, Aspect of the Pack and mounts by $201813s1%. Does "
           "not stack with other effects that increase mounted speed.")
_T1_OLD = ("Aspect of the Monkey to trigger by", "and your mounted speed by")
_T16 = "Increases the damage done by your pet by $s1%."
_PT2 = "Reduces the cooldown of your pet's Dash by ${$m1/-1000} sec."
TOOLTIP_TEXTS = {
    **{i: ((_T1_MAIN, _T1_CAP), _T1_OLD) for i in (19559, 19560, 201820)},       # T1 Pathfinding (stock ranks + capstone)
    **{i: ((_T16,), ("Increases your pet's damage by",)) for i in (201839, 201840)},  # T16 Shark Attack
    **{i: ((_PT2,), ("ability by",)) for i in (53483, 53485)},                       # PT2 Mobility
}


def check_tooltip_texts(rows_by_id: dict[int, dict], expected=TOOLTIP_TEXTS) -> list[str]:
    """(u) each id's built Description_Lang_enUS holds every required substring and none of the forbidden ones."""
    bad = []
    for spell_id, (required, forbidden) in expected.items():
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
            continue
        text = str(row.get("Description_Lang_enUS") or "")
        bad += [f"{spell_id}: tooltip lacks {want!r}" for want in required if want not in text]
        bad += [f"{spell_id}: tooltip still has the old {old!r}" for old in forbidden if old in text]
    return bad


# ---- real data -------------------------------------------------------------------------------------------------------

def _consts(package) -> dict:
    return {c["name"]: c["value"] for c in package.consts}


def _range_max(reuse) -> dict[int, float]:
    """SpellRange index -> RangeMax_1: the stock table plus every range the package's build minted."""
    rows = {**state.load_stock_rows(dbcfmt.SPELLRANGE), **{r["ID"]: r for r in reuse.minted.get("spellrange", [])}}
    return {int(i): float(r.get("RangeMax_1") or 0) for i, r in rows.items()}


def _cast_times(reuse) -> dict[int, int]:
    """SpellCastTimes index -> Base ms: the stock table plus every cast time the package's build minted."""
    rows = {**state.load_stock_rows(dbcfmt.SPELLCASTTIMES),
            **{r["ID"]: r for r in reuse.minted.get("spellcasttimes", [])}}
    return {int(i): int(r.get("Base") or 0) for i, r in rows.items()}


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

    def test_steady_shot_potency_keeps_the_live_cast_time(self):
        # PT-3 cut the DBC cast to 1000 ms (the engine adds 500 ms to ranged-slot shots); the potency time basis must
        # stay at the live 1.5 s or the base and the RAP coefficient drop by a third (S1b review B-1).
        package = package_data()["package"]
        bonus = [r for r in package.spell_bonus_data if int(r["entry"]) == 56641]
        self.assertEqual(len(bonus), 1)
        # TUNE3: ap_potency 49 (TUNE1 70, was 100), so the coefficient is 0.49 * (1.5 / 3.5)
        self.assertAlmostEqual(bonus[0]["ap_bonus"], 0.49 * 1.5 / 3.5, places=4)

    def test_s1b_ids_have_equipped_item_class_minus_one(self):
        rows = package_data()["rows_by_id"]
        self.assertClean(check_required_rows_declared(rows, (*NEW_S1B_IDS, *EDITED_S1B_IDS,
                                                             *EQUIPPED_ITEM_CLASS_EXEMPT)))
        self.assertClean(check_equipped_item_class(rows, sorted({*NEW_S1B_IDS, *EDITED_S1B_IDS}
                                                                - EQUIPPED_ITEM_CLASS_EXEMPT)))
        for spell_id in sorted(EQUIPPED_ITEM_CLASS_EXEMPT):
            self.assertEqual(rows[spell_id].get("EquippedItemClass"), 2, f"{spell_id} keeps the stock ranged weapon")

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

    def test_command_presses_start_the_gcd(self):
        rows = package_data()["rows_by_id"]
        self.assertClean([b for i in COMMANDS for b in check_command_gcd(i, rows.get(i))])

    def test_aspect_of_the_beast_marker(self):
        data = package_data()
        rows = data["rows_by_id"]
        self.assertClean(check_beast_marker(rows.get(BEAST_MARKER), rows.get(BEAST_PET_BUFF)))
        names = {r["ScriptName"] for r in data["package"].spell_script_names if int(r["spell_id"]) == BEAST_PET_BUFF}
        self.assertEqual(names, {"spell_hun_aspect_beast_pet_buff"})

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

    def test_cobra_strikes_ranks_are_dummy_auras(self):
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

    # ---- S1b ----
    def test_stampede_spell_and_sla(self):
        data = package_data()
        consts = _consts(data["package"])
        self.assertClean(check_stampede_spell(data["rows_by_id"].get(STAMPEDE_SPELL), consts["STAMPEDE_ENTRY_MIN"],
                                              consts["STAMPEDE_ENTRY_MAX"]))
        self.assertClean(check_stampede_sla(data["package"].skill_line_abilities))

    def test_steady_shot_nature_hit(self):
        data = package_data()
        self.assertClean(check_steady_shot_nature(data["rows_by_id"].get(STEADY_SHOT_NATURE), _range_max(data["reuse"]),
                                                  data["package"].custom_attrs))

    def test_bm_pet_proc_carrier(self):
        data = package_data()
        self.assertClean(check_bm_pet_procs(data["rows_by_id"].get(BM_PET_PROCS), data["package"].spell_procs))

    def test_steady_shot_nature_and_cobra_strikes_proc_rows(self):
        procs = package_data()["package"].spell_procs
        self.assertClean(check_steady_shot_nature_procs(procs))
        self.assertClean(check_cobra_strikes_proc(procs))

    def test_culling_the_herd_is_a_damage_done_aura(self):
        self.assertClean(check_culling_buff_and_readers(package_data()["rows_by_id"]))

    def test_stampede_guardians(self):
        package = package_data()["package"]
        consts = _consts(package)
        self.assertClean(check_stampede_guardians(package.creature_templates, package.creature_template_models,
                                                  consts["STAMPEDE_ENTRY_MIN"], consts["STAMPEDE_ENTRY_MAX"]))

    def test_53270_in_no_talent_row(self):
        package = package_data()["package"]
        talents = {**state.load_stock_rows(dbcfmt.TALENT),
                   **{int(r["ID"]): r for r in map(build.build_talent_row, package.talents)}}
        self.assertClean(check_no_talent_teaches(list(talents.values())))
        self.assertClean(check_linked_spells(package.linked_spells, (KINDRED_LINK,)))

    def test_s1b_script_bindings_and_custom_attrs(self):
        package = package_data()["package"]
        self.assertClean(check_script_bindings(package.spell_script_names))
        self.assertClean([b for i in HELPER_COPIES
                          for b in check_custom_attr(i, package.custom_attrs, HELPER_COPY_CUSTOM_ATTR)])
        # review M2: 201803 carries no 0x200000 (check_steady_shot_nature asserts the same on the built data)
        self.assertEqual([c for c in package.custom_attrs if int(c["spell_id"]) == STEADY_SHOT_NATURE
                          and int(c["attributes"]) & CU_NO_POSITIVE_TAKEN_BONUS], [])

    def test_s1b_values(self):
        data = package_data()
        entries = {int(e["id"]): e for e in data["package"].spells}
        self.assertClean(check_s1b_values(data["rows_by_id"], entries, _cast_times(data["reuse"])))

    def test_command_dot_spellmods(self):
        self.assertClean(check_dot_spellmods(package_data()["rows_by_id"]))

    def test_command_display_passives(self):
        data = package_data()
        package = data["package"]
        offset = _consts(package)["COMMAND_DISPLAY_OFFSET"]
        self.assertEqual(offset, DISPLAY_IDS[0] - COMMANDED_SLOTTED[0], "brief decision 1: 201720 + 138 = 201858")
        slots = parse_kit_slots(HUNTER_MECHANICS_CPP.read_text(encoding="utf-8"),
                                HUNTER_DATA_H.read_text(encoding="utf-8"))
        self.assertClean(check_command_displays(data["rows_by_id"], offset, slots, package.spell_script_names,
                                                package.talents, package.trainer_spells))

    def test_tooltip_texts_t1_t16_pt2(self):
        self.assertClean(check_tooltip_texts(package_data()["rows_by_id"]))


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


GOOD_ATTRS = [{"spell_id": 201805, "attributes": 0x208000}, {"spell_id": 201807, "attributes": 0x208000}]


def good_procs() -> list[dict]:
    return [
        {"SpellId": 201806, "ProcFlags": 0x10114, "SpellPhaseMask": 0x2, "AttributesMask": 0x2},
        {"SpellId": 201848, "ProcFlags": 0x100, "SpellPhaseMask": 0x1, "SpellFamilyName": 9, "SpellFamilyMask0": 0x1000},
    ]


def good_transform() -> dict:
    return {"ID": 201811, "Attributes": 464, "Effect_1": 6, "EffectAura_1": 107, "EffectMiscValue_1": 10,
            "EffectBasePoints_1": -2001, "EffectDieSides_1": 1, "EffectSpellClassMaskA_3": 0x20000000}


GOOD_GROUPS = [{"id": 1231, "spell_id": 201811}]
GOOD_RULES = [{"group_id": 1231, "stack_rule": 1}]


def good_tbw() -> dict:
    return {"ID": 201812, "Attributes": 464, "SpellClassSet": 9, "Effect_1": 6, "EffectAura_1": 108,
            "EffectMiscValue_1": 0, "EffectSpellClassMaskA_2": 0x800, "Effect_2": 6, "EffectAura_2": 226,
            "EffectAuraPeriod_2": 1000}


def good_tab() -> list[dict]:
    talents = []
    for talent_id, (tier, column) in TAB_CELLS.items():
        ranks = [STAMPEDE_SPELL] if talent_id == STAMPEDE_ROW else [talent_id * 10]
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

    def test_only_the_player_cast_ranged_shots_are_exempt_from_the_equipped_item_class_guard(self):
        self.assertEqual(EQUIPPED_ITEM_CLASS_EXEMPT, {56641, 3044, 19434, 53209, 2643, 201920, 201921, 201922,
                                                      53301, 19386, 19503, 3674})
        rows = {i: {"ID": i, "EquippedItemClass": 2} for i in (56641, 34026, 3044, 19434, 201920, 201930, 201933)}
        ids = set(rows) - EQUIPPED_ITEM_CLASS_EXEMPT
        # 34026 (Kill Command), 201930 (Viper's Bite, a triggered DoT) and 201933 (the free, triggered Arcane Shot) are
        # not exempt: class 2 on them fails
        self.assertEqual(len(check_equipped_item_class(rows, sorted(ids))), 3)
        # an S1b display spell left at the stock-style 0 fails
        self.assertEqual(len(check_equipped_item_class({201858: {"ID": 201858, "EquippedItemClass": 0}}, (201858,))), 1)
        self.assertFalse(set(NEW_S1B_IDS) & EQUIPPED_ITEM_CLASS_EXEMPT)
        self.assertFalse(set(EDITED_S1B_IDS) & EQUIPPED_ITEM_CLASS_EXEMPT)

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

    def test_command_gcd_and_beast_marker_guards(self):
        press = {**good_press(), "StartRecoveryCategory": 133, "StartRecoveryTime": 1500, "RecoveryTime": 30000}
        self.assertEqual(check_command_gcd(201800, press), [])
        self.assertEqual(len(check_command_gcd(201800, {**press, "StartRecoveryTime": 0})), 1)
        self.assertEqual(len(check_command_gcd(201800, {**press, "RecoveryTime": 0})), 1)
        buff = {"DurationIndex": 9}
        marker = {"Attributes": 0, "AttributesEx7": 0, "EquippedItemClass": -1, "Effect_1": 6, "EffectAura_1": 4,
                  "Effect_2": 0, "Effect_3": 0, "DurationIndex": 9, "AuraDescription_Lang_enUS": "x $201603s1% y"}
        self.assertEqual(check_beast_marker(marker, buff), [])
        for bad in ({"Attributes": 0x40}, {"AttributesEx7": 0x10000000}, {"EquippedItemClass": 0}, {"DurationIndex": 8},
                    {"EffectAura_1": 79}, {"SpellClassMask_1": 1}, {"AuraDescription_Lang_enUS": "15% more"}):
            self.assertEqual(len(check_beast_marker({**marker, **bad}, buff)), 1, bad)

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
        # S1a-3: the S1a value 0x8000 alone (damage-taken mods counted twice) and a split second row both fail
        self.assertEqual(len(check_helper_copy(201807, good_copy(), [{"spell_id": 201807, "attributes": 0x8000}])), 1)
        split = [{"spell_id": 201807, "attributes": 0x8000}, {"spell_id": 201807, "attributes": 0x200000}]
        self.assertEqual(len(check_helper_copy(201807, good_copy(), split)), 1)
        self.assertEqual(len(check_custom_attr(201810, GOOD_ATTRS, 0x1000)), 1)
        self.assertEqual(check_custom_attr(201810, [{"spell_id": 201810, "attributes": 0x1000}], 0x1000), [])

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
        self.assertEqual(len(check_cobra_shot_transform({**good_transform(), "EffectBasePoints_1": -1501},
                                                        GOOD_GROUPS, GOOD_RULES)), 1)       # S1a's value, pre PT-2
        self.assertEqual(len(check_cobra_shot_transform({**good_transform(), "EffectDieSides_1": 0},
                                                        GOOD_GROUPS, GOOD_RULES)), 1)       # live -2001
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
        next(t for t in stampede if t["id"] == STAMPEDE_ROW)["rank_spell_ids"] = [STOCK_BEAST_MASTERY_RANK]
        self.assertEqual(len(check_tab_361(stampede, [], [])), 1)                                    # S1a's 53270 back
        built = {"ID": STAMPEDE_ROW, "TabID": TAB, "SpellRank_1": STAMPEDE_SPELL}
        self.assertEqual(check_tab_361(talents, [built], []), [])
        self.assertEqual(len(check_tab_361(talents, [{**built, "SpellRank_1": STOCK_BEAST_MASTERY_RANK}], [])), 1)
        self.assertEqual(len(check_tab_361(talents, [{**built, "SpellRank_2": 201802}], [])), 1)      # a second rank
        self.assertEqual(len(check_tab_361(talents, [], [{"id": 30541, "skill_line": 202}])), 1)
        self.assertEqual(check_tab_361(talents, [], [{"id": 30541, "skill_line": 50}]), [])
        other_tab = talents + [{"id": 9999, "tab_id": 362, "tier": 0, "column": 0, "rank_spell_ids": [1]}]
        self.assertEqual(check_tab_361(other_tab, [], []), [])                                       # other tabs are ignored

    def test_stock_rank_helper_ignores_custom_and_other_tabs(self):
        talents = [{"tab_id": TAB, "rank_spell_ids": [19559, 201820]}, {"tab_id": 362, "rank_spell_ids": [1]}]
        self.assertEqual(_stock_ranks(talents), [19559])

    def test_live_value_helper(self):
        self.assertEqual(live_value({"EffectBasePoints_1": -2001, "EffectDieSides_1": 1}, 1), -2000)
        self.assertEqual(live_value({"EffectBasePoints_2": 49}, 2), 49)
        self.assertEqual(live_value({"EffectBasePoints_3": 4, "EffectDieSides_3": 3}, 3), 5)


# ---- S1b negative fixtures -------------------------------------------------------------------------------------------

ENTRY_MIN, ENTRY_MAX = 300200, 300219


def good_stampede() -> dict:
    return {"ID": 201802, "Attributes": 0x50000, "AttributesEx": 0, "SpellClassSet": 0, "Effect_1": EFFECT_SUMMON,
            "EffectMiscValue_1": 300205, "EffectMiscValueB_1": SUMMON_PROPERTIES}


def good_sla() -> list[dict]:
    return [{"id": STAMPEDE_SLA, "spell_id": STAMPEDE_SPELL, "skill_line": SKILL_LINE_BM,
             "class_mask": CLASSMASK_HUNTER}]


def good_nature() -> dict:
    return {"ID": 201803, "SchoolMask": 8, "SpellClassSet": 0, "AttributesEx2": 0x20000000, "AttributesEx3": 0x20050000,
            "RangeIndex": 30202, "Effect_1": EFFECT_SCHOOL_DAMAGE, "ImplicitTargetA_1": 6}


GOOD_RANGES = {30202: 50000.0, 13: 40.0}
NATURE_ATTRS: list[dict] = []          # review M2: 201803 has no custom attr row


def good_carrier() -> dict:
    return {"ID": 201809, "Attributes": 464, "Effect_1": 6, "EffectAura_1": 4, "ImplicitTargetA_1": 1,
            "ProcTypeMask": 0x10110, "ProcChance": 100}


def good_carrier_proc(**cols) -> dict:
    return {"SpellId": 201809, "ProcFlags": 0x10110, "SpellFamilyName": 9, "SpellFamilyMask2": 0xC00000,
            "SpellPhaseMask": 0x2, "HitMask": 0x2, "AttributesMask": 0x2, **cols}


def good_b1_procs() -> list[dict]:
    return [{"SpellId": i, "ProcFlags": 0x100, "SpellFamilyName": 9, "SpellFamilyMask2": 0x20000000,
             "SpellPhaseMask": phase, "HitMask": 0} for i, phase in STEADY_SHOT_NATURE_PROCS.items()]


def good_cobra_proc(**cols) -> dict:
    return {"SpellId": -53256, "ProcFlags": 0x100, "SpellFamilyName": 9, "SpellFamilyMask2": 0x20000000,
            "SpellPhaseMask": 0x1, "HitMask": 0, **cols}


def good_culling_rows() -> dict[int, dict]:
    rows = {201808: {"ID": 201808, "Effect_1": 6, "EffectAura_1": 79, "EffectMiscValue_1": 127}}
    for i in CULLING_RANKS:
        rows[i] = {"ID": i, "Effect_1": 6, "EffectAura_1": 4}
    for i in IMPROVED_VIPER_RANKS:
        rows[i] = {"ID": i, "Effect_1": 6, "EffectAura_1": 107, "EffectMiscValue_1": 18, "EffectSpellClassMaskA_2": 0,
                   "Effect_2": 6, "EffectAura_2": 108, "EffectMiscValue_2": 3, "EffectSpellClassMaskB_1": 0x40000}
    return rows


def good_guardians() -> tuple[list[dict], list[dict]]:
    creatures = [{"entry": e, "family": f, "type": 1, "ScriptName": STAMPEDE_SCRIPT}
                 for e, f in GUARDIAN_FAMILY.items()]
    models = [{"CreatureID": e, "Idx": idx, "Probability": 1.0} for e in GUARDIAN_FAMILY for idx in range(3)]
    return creatures, models


def good_bindings() -> list[dict]:
    return [{"spell_id": i, "ScriptName": name} for name, ids in S1B_SCRIPT_BINDINGS.items() for i in sorted(ids)]


def good_value_rows() -> dict[int, dict]:
    rows = {56641: {"ID": 56641, "CastingTimeIndex": 4},
            201602: {"ID": 201602, "EffectBasePoints_1": 49, "EffectDieSides_1": 1},
            3044: {"ID": 3044, "Effect_2": EFFECT_DUMMY, "EffectBasePoints_2": 199}}
    rows.update({i: {"ID": i, "AttributesEx7": 0} for i in FEROCIOUS_INSPIRATION_BUFFS})
    return rows


GOOD_CAST_TIMES = {4: 1000, 30001: 1500, 1: 0}
GOOD_ENTRIES = {56641: {"id": 56641, "cast_time_ms": 1000}}


def good_dot_rows() -> dict[int, dict]:
    return {i: {"ID": i, "Effect_1": 6, "EffectAura_1": 108, "EffectMiscValue_1": 0, "EffectBasePoints_1": 29,
                "EffectSpellClassMaskA_3": 0x400000, "Effect_2": 6, "EffectAura_2": 108, "EffectMiscValue_2": 22,
                "EffectBasePoints_2": 29, "EffectSpellClassMaskB_3": 0x400000} for i in PLUME_AND_MASTERS_COMMAND}


def good_displays() -> tuple[dict[int, dict], dict[int, str]]:
    rows, slots = {}, {}
    for n, commanded in enumerate(COMMANDED_SLOTTED):
        slot = "I" if n % 2 == 0 else "II"
        slots[commanded] = slot
        rows[commanded] = {"ID": commanded, "Name_Lang_enUS": f"Ability {n}"}
        rows[commanded + 138] = {"ID": commanded + 138, "Name_Lang_enUS": f"Command {slot}: Ability {n}",
                                 "Attributes": 0x150, "Effect_1": 6, "EffectAura_1": 4, "ImplicitTargetA_1": 1}
    return rows, slots


class HunterBmS1bNegativeTest(unittest.TestCase):
    def test_stampede_spell_guard(self):
        self.assertEqual(check_stampede_spell(good_stampede(), ENTRY_MIN, ENTRY_MAX), [])
        self.assertEqual(len(check_stampede_spell(None, ENTRY_MIN, ENTRY_MAX)), 1)
        for bad in ({"SpellClassSet": 9}, {"SpellClassMask_3": 0x1}, {"Attributes": 0x50010}, {"AttributesEx": 0x4},
                    {"Effect_1": EFFECT_DUMMY}, {"EffectMiscValue_1": 300220}, {"EffectMiscValue_1": 57386},
                    {"EffectMiscValueB_1": 0}):
            self.assertEqual(len(check_stampede_spell({**good_stampede(), **bad}, ENTRY_MIN, ENTRY_MAX)), 1, bad)

    def test_stampede_sla_guard(self):
        self.assertEqual(check_stampede_sla(good_sla()), [])
        self.assertEqual(len(check_stampede_sla([])), 1)
        self.assertEqual(len(check_stampede_sla(good_sla() * 2)), 1)
        for bad in ({"skill_line": 202}, {"class_mask": 0}, {"spell_id": STOCK_BEAST_MASTERY_RANK}):
            self.assertEqual(len(check_stampede_sla([{**good_sla()[0], **bad}])), 1, bad)

    def test_steady_shot_nature_guard(self):
        self.assertEqual(check_steady_shot_nature(good_nature(), GOOD_RANGES, NATURE_ATTRS), [])
        self.assertEqual(len(check_steady_shot_nature(None, GOOD_RANGES, NATURE_ATTRS)), 1)
        for bad in ({"SchoolMask": 1}, {"SpellClassSet": 9}, {"SpellClassMask_3": 0x20000000}, {"AttributesEx2": 0},
                    {"RangeIndex": 13}, {"RangeIndex": 99}, {"ImplicitTargetA_1": 1}, {"Effect_1": EFFECT_DUMMY}):
            self.assertEqual(len(check_steady_shot_nature({**good_nature(), **bad}, GOOD_RANGES, NATURE_ATTRS)), 1, bad)
        for bit in (0x20000000, 0x10000, 0x40000):          # each of the three Ex3 bits is required
            row = {**good_nature(), "AttributesEx3": 0x20050000 & ~bit}
            self.assertEqual(len(check_steady_shot_nature(row, GOOD_RANGES, NATURE_ATTRS)), 1, hex(bit))
        for attrs in ([{"spell_id": 201803, "attributes": 0x200000}], [{"spell_id": 201803, "attributes": 0x208000}]):
            self.assertEqual(len(check_steady_shot_nature(good_nature(), GOOD_RANGES, attrs)), 1, attrs)   # M2
        other = [{"spell_id": 201807, "attributes": 0x208000}]
        self.assertEqual(check_steady_shot_nature(good_nature(), GOOD_RANGES, other), [])     # another spell's row

    def test_bm_pet_procs_guard(self):
        self.assertEqual(check_bm_pet_procs(good_carrier(), [good_carrier_proc()]), [])
        self.assertEqual(len(check_bm_pet_procs(None, [good_carrier_proc()])), 1)
        for bad in ({"Attributes": 0}, {"ProcChance": 0}, {"EffectAura_1": 42}, {"ImplicitTargetA_1": 5}):
            self.assertEqual(len(check_bm_pet_procs({**good_carrier(), **bad}, [good_carrier_proc()])), 1, bad)
        for bad in ({"AttributesMask": 0}, {"HitMask": 0x3}, {"HitMask": 0}, {"SpellFamilyMask1": 0x10000000},
                    {"SpellFamilyMask2": 0x400000}, {"SpellFamilyName": 0}, {"SpellPhaseMask": 0x1},
                    {"ProcFlags": 0x100}):
            self.assertEqual(len(check_bm_pet_procs(good_carrier(), [good_carrier_proc(**bad)])), 1, bad)
        self.assertEqual(len(check_bm_pet_procs(good_carrier(), [good_carrier_proc(SpellId=-201809)])), 2)
        self.assertEqual(len(check_bm_pet_procs(good_carrier(), [good_carrier_proc()] * 2)), 1)
        self.assertEqual(len(check_bm_pet_procs(good_carrier(), [])), 1)

    def test_steady_shot_nature_proc_rows_guard(self):
        self.assertEqual(check_steady_shot_nature_procs(good_b1_procs()), [])

        def with_change(spell_id, **cols):
            return [{**p, **cols} if p["SpellId"] == spell_id else p for p in good_b1_procs()]

        self.assertEqual(len(check_steady_shot_nature_procs(with_change(34468, SpellPhaseMask=0x2))), 1)  # loses CAST
        self.assertEqual(len(check_steady_shot_nature_procs(with_change(34466, SpellPhaseMask=0x3))), 1)  # gains CAST
        self.assertEqual(len(check_steady_shot_nature_procs(with_change(34467, SpellFamilyMask1=0x1))), 1)
        self.assertEqual(len(check_steady_shot_nature_procs(with_change(34466, HitMask=0x2))), 1)
        self.assertEqual(len(check_steady_shot_nature_procs(with_change(34467, ProcFlags=0))), 1)
        self.assertEqual(len(check_steady_shot_nature_procs(with_change(34467, SpellId=-34467))), 2)
        self.assertEqual(len(check_steady_shot_nature_procs(good_b1_procs()[:-1])), 1)
        chain = good_b1_procs() + [{**good_b1_procs()[0], "SpellId": -34466}]
        self.assertEqual(len(check_steady_shot_nature_procs(chain)), 2)     # the chain row + rank 1's negative twin

    def test_cobra_strikes_proc_guard(self):
        self.assertEqual(check_cobra_strikes_proc([good_cobra_proc()]), [])
        h0 = good_cobra_proc(ProcFlags=0, SpellFamilyMask0=0x800, SpellFamilyMask1=0x800000, SpellPhaseMask=0x2,
                             HitMask=0x2)
        self.assertEqual(len(check_cobra_strikes_proc([h0])), 4)            # H0's row unedited: flags, mask, phase, hit
        self.assertEqual(len(check_cobra_strikes_proc([good_cobra_proc()] * 2)), 1)
        self.assertEqual(len(check_cobra_strikes_proc([good_cobra_proc(), good_cobra_proc(SpellId=53256)])), 1)
        self.assertEqual(len(check_cobra_strikes_proc([])), 1)

    def test_culling_guard(self):
        self.assertEqual(check_culling_buff_and_readers(good_culling_rows()), [])
        for spell_id, bad in ((201808, {"EffectAura_1": 108}), (201808, {"EffectMiscValue_1": 1}),
                              (201842, {"Effect_2": 6, "EffectAura_2": 108, "EffectSpellClassMaskB_3": 0x800000}),
                              (201831, {"Effect_3": 6, "EffectAura_3": 107, "EffectSpellClassMaskC_3": 0xC00000})):
            rows = good_culling_rows()
            rows[spell_id] = {**rows[spell_id], **bad}
            self.assertEqual(len(check_culling_buff_and_readers(rows)), 1, (spell_id, bad))
        rows = good_culling_rows()
        rows[201841] = {**rows[201841], "EffectSpellClassMaskA_3": 0x800000}     # a DUMMY's mask is not a SpellMod
        self.assertEqual(check_culling_buff_and_readers(rows), [])
        rows.pop(201830)
        self.assertEqual(len(check_culling_buff_and_readers(rows)), 1)

    def test_stampede_guardians_guard(self):
        creatures, models = good_guardians()
        self.assertEqual(check_stampede_guardians(creatures, models, ENTRY_MIN, ENTRY_MAX), [])
        for entry, bad in ((300201, {"ScriptName": ""}), (300205, {"family": 1}), (300203, {"type": 0})):
            changed = [{**c, **bad} if c["entry"] == entry else c for c in creatures]
            self.assertEqual(len(check_stampede_guardians(changed, models, ENTRY_MIN, ENTRY_MAX)), 1, (entry, bad))
        two = [m for m in models if not (m["CreatureID"] == 300207 and m["Idx"] == 2)]
        self.assertEqual(len(check_stampede_guardians(creatures, two, ENTRY_MIN, ENTRY_MAX)), 1)
        zero = [{**m, "Probability": 0.0} if m["CreatureID"] == 300200 else m for m in models]
        self.assertEqual(len(check_stampede_guardians(creatures, zero, ENTRY_MIN, ENTRY_MAX)), 1)
        self.assertEqual(len(check_stampede_guardians(creatures + creatures[:1], models, ENTRY_MIN, ENTRY_MAX)), 1)
        self.assertEqual(len(check_stampede_guardians(creatures[1:], models, ENTRY_MIN, ENTRY_MAX)), 1)
        self.assertEqual(len(check_stampede_guardians(creatures, models, ENTRY_MIN, 300205)), 2)     # 300206 / 300207
        stray = creatures + [{"entry": 300210, "family": 1, "type": 1, "ScriptName": STAMPEDE_SCRIPT}]
        self.assertEqual(len(check_stampede_guardians(stray, models, ENTRY_MIN, ENTRY_MAX)), 1)

    def test_no_talent_teaches_guard(self):
        clean = [{"ID": 2139, "SpellRank_1": 201802}, {"ID": 1, "SpellRank_1": 19559}]
        self.assertEqual(check_no_talent_teaches(clean), [])
        self.assertEqual(len(check_no_talent_teaches(clean + [{"ID": 2139, "SpellRank_3": 53270}])), 1)

    def test_script_bindings_guard(self):
        self.assertEqual(check_script_bindings(good_bindings()), [])
        negative = [{**b, "spell_id": -53256} if b["spell_id"] == 53256 else b for b in good_bindings()]
        self.assertEqual(len(check_script_bindings(negative)), 2)           # negative key + the set differs
        self.assertEqual(len(check_script_bindings([b for b in good_bindings() if b["spell_id"] != 34468])), 1)
        extra = good_bindings() + [{"spell_id": 56641, "ScriptName": "spell_hun_steady_shot_nature"}]
        self.assertEqual(len(check_script_bindings(extra)), 1)
        self.assertEqual(check_script_bindings(good_bindings() + [{"spell_id": -1, "ScriptName": "other"}]), [])

    def test_s1b_values_guard(self):
        self.assertEqual(check_s1b_values(good_value_rows(), GOOD_ENTRIES, GOOD_CAST_TIMES), [])

        def changed(spell_id, **cols):
            rows = good_value_rows()
            rows[spell_id] = {**rows[spell_id], **cols}
            return rows

        stale_entry = {56641: {"id": 56641, "cast_time_ms": 1500}}
        self.assertEqual(len(check_s1b_values(good_value_rows(), stale_entry, GOOD_CAST_TIMES)), 1)
        stale_index = changed(56641, CastingTimeIndex=30001)
        self.assertEqual(len(check_s1b_values(stale_index, GOOD_ENTRIES, GOOD_CAST_TIMES)), 1)
        self.assertEqual(len(check_s1b_values(stale_index, stale_entry, GOOD_CAST_TIMES)), 2)
        for cols in ({"EffectBasePoints_1": 4}, {"EffectBasePoints_1": 48}, {"EffectDieSides_1": 0}):
            self.assertEqual(len(check_s1b_values(changed(201602, **cols), GOOD_ENTRIES, GOOD_CAST_TIMES)), 1, cols)
        ok = changed(201602, EffectBasePoints_1=50, EffectDieSides_1=0)
        self.assertEqual(check_s1b_values(ok, GOOD_ENTRIES, GOOD_CAST_TIMES), [])
        for cols in ({"EffectBasePoints_2": 49}, {"Effect_2": 0}):
            self.assertEqual(len(check_s1b_values(changed(3044, **cols), GOOD_ENTRIES, GOOD_CAST_TIMES)), 1, cols)
        consolidated = changed(75446, AttributesEx7=0x10000000)
        self.assertEqual(len(check_s1b_values(consolidated, GOOD_ENTRIES, GOOD_CAST_TIMES)), 1)
        rows = good_value_rows()
        rows.pop(75447)
        self.assertEqual(len(check_s1b_values(rows, GOOD_ENTRIES, GOOD_CAST_TIMES)), 1)

    def test_dot_spellmods_guard(self):
        self.assertEqual(check_dot_spellmods(good_dot_rows()), [])
        for spell_id, cols in ((201826, {"Effect_2": 0, "EffectAura_2": 0}),
                               (24443, {"EffectSpellClassMaskB_3": 0, "EffectSpellClassMaskA_3": 0x400000}),
                               (201853, {"EffectSpellClassMaskB_2": 0x10000000}),
                               (19575, {"EffectBasePoints_2": 19}),
                               (201852, {"EffectMiscValue_2": 0})):
            rows = good_dot_rows()
            rows[spell_id] = {**rows[spell_id], **cols}
            self.assertEqual(len(check_dot_spellmods(rows)), 1, (spell_id, cols))
        rows = good_dot_rows()
        rows.pop(201854)
        self.assertEqual(len(check_dot_spellmods(rows)), 1)

    def test_kit_slot_parser(self):
        header = ("constexpr uint32 SPELL_BITE = 17253; // x\n"
                  "constexpr uint32 SPELL_A_COMMAND = 201720; // a\nconstexpr uint32 SPELL_B_COMMAND = 201721; // b\n")
        cpp = "{ 1, { SPELL_BITE, SPELL_BITE, SPELL_A_COMMAND, SPELL_B_COMMAND } },"
        self.assertEqual(parse_kit_slots(cpp, header), {201720: "I", 201721: "II"})
        swapped = cpp + "\n{ 2, { SPELL_BITE, SPELL_BITE, SPELL_B_COMMAND, SPELL_A_COMMAND } },"
        self.assertEqual(parse_kit_slots(swapped, header), {201720: "both", 201721: "both"})
        unknown = cpp + "\nconstexpr PetKit K = { SPELL_BITE, SPELL_BITE, SPELL_C_COMMAND, SPELL_A_COMMAND };"
        slots = parse_kit_slots(unknown, header)
        self.assertEqual(slots[-1], "SPELL_C_COMMAND")
        self.assertEqual(slots[201720], "both")

    def test_command_display_guard(self):
        rows, slots = good_displays()
        self.assertEqual(check_command_displays(rows, 138, slots, [], [], []), [])

        def changed(display, **cols):
            out = dict(rows)
            out[display] = {**out[display], **cols}
            return out

        for display, cols in ((201858, {"Attributes": 0x1D0}), (201858, {"Attributes": 0x40}),
                              (201859, {"Name_Lang_enUS": "Command I: Ability 1"}),
                              (201860, {"Name_Lang_enUS": "Command I: Rake"}), (201861, {"ImplicitTargetA_1": 6}),
                              (201862, {"EffectAura_1": 108}), (201863, {"Effect_2": 6}),
                              (201864, {"SpellClassSet": 9}),
                              (201865, {"SpellClassMask_3": 0x400000})):
            self.assertEqual(len(check_command_displays(changed(display, **cols), 138, slots, [], [], [])), 1,
                             (display, cols))
        missing = {k: v for k, v in rows.items() if k != 201873}
        self.assertEqual(len(check_command_displays(missing, 138, slots, [], [], [])), 1)
        self.assertEqual(len(check_command_displays({**rows, 201874: {"ID": 201874}}, 138, slots, [], [], [])), 1)
        self.assertEqual(len(check_command_displays(rows, 138, {**slots, 201725: "both"}, [], [], [])), 1)
        self.assertEqual(len(check_command_displays(rows, 138, {k: v for k, v in slots.items() if k != 201730}, [], [],
                                                    [])), 1)
        self.assertEqual(len(check_command_displays(rows, 138, {**slots, -1: "SPELL_X_COMMAND"}, [], [], [])), 1)
        bound = [{"spell_id": 201866, "ScriptName": "spell_hun_command"}]
        self.assertEqual(len(check_command_displays(rows, 138, slots, bound, [], [])), 1)
        talents = [{"id": 1, "rank_spell_ids": [201867]}]
        self.assertEqual(len(check_command_displays(rows, 138, slots, [], talents, [])), 1)
        trainers = [{"TrainerId": 204, "SpellId": 201868}]
        self.assertEqual(len(check_command_displays(rows, 138, slots, [], [], trainers)), 1)
        self.assertGreaterEqual(len(check_command_displays(rows, 137, slots, [], [], [])), 1)   # wrong offset

    def test_tooltip_text_guard(self):
        good = {i: {"ID": i, "Description_Lang_enUS": " ".join(req)} for i, (req, _old) in TOOLTIP_TEXTS.items()}
        self.assertEqual(check_tooltip_texts(good), [])
        old_t16 = {**good, 201839: {"ID": 201839, "Description_Lang_enUS": "Increases your pet's damage by $s1%."}}
        self.assertEqual(len(check_tooltip_texts(old_t16)), 2)                    # new text missing + old text present
        old_t1 = {**good, 201820: {"ID": 201820, "Description_Lang_enUS": " ".join(TOOLTIP_TEXTS[201820][0]) +
                                   " Aspect of the Monkey to trigger by"}}
        self.assertEqual(len(check_tooltip_texts(old_t1)), 1)
        no_cap = {**good, 19560: {"ID": 19560, "Description_Lang_enUS": _T1_MAIN}}
        self.assertEqual(len(check_tooltip_texts(no_cap)), 1)
        self.assertEqual(len(check_tooltip_texts({k: v for k, v in good.items() if k != 53485})), 1)


if __name__ == "__main__":
    unittest.main()
