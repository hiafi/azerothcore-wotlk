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

hunter-pet-families F0 (hunter-pet-families.F0.HANDOFF.md s2, s5, s7, s9):

  (v) the kit table: HunterMechanics.cpp FAMILY_KITS has one row per hunter family (32), every id it names is declared
      by the package, every command has a display in COMMAND_DISPLAYS (the command -> display table that replaced the
      +138 offset), and every slot 2 / slot 3 spell carries d1 b28 + b29; the type defaults name commands only;
  (w) the F0 utilities 201753, 201983-201986 and the kit v2 marker 202014; their SkillLineAbility rows live in
      test_hunter_pet_data.py;
  (x) Mobility 53483 / 53485: ADD_PCT_MODIFIER cooldown -10 / -20 on d1 b29 alone, and the d1 b29 carrier and reader
      sets of the package;
  (y) Bear retrofit (ruling 19): Swipe 420 on both effects, Maul 715 (x0.80 since ruling 23b); Swipe bound to spell_hun_command_aoe_falloff.

hunter-pet-families F1 (hunter-pet-families.F1.HANDOFF.md s1, s2, s5):

  (z) the 8 Ferocity kits: the kit rows (v, with FINISHED_KITS / MANUAL_GROUP_FAMILIES / NO_MOBILITY_UTILITIES), command
      potency = the ruling 1 scale of the PLAN s3.1 number, the commands and helpers (carriers, schools, multi-hit
      follow-ups incl. Twin Bite's one, the cones' target anchor), the utilities (level, cooldown, NO_AUTOCAST_AI on
      the two manual raid cooldowns, TargetA 56, spell groups, Scavenge, Fresh Kill, the hidden Rebirth) and the script
      bindings of each PLAN s5.2 tag.

The kit and display tables are parsed from the C++ (one source: the C++ drives the game, the parser checks it against
the DSL), with names resolved through the generated HunterData.h.

Every check is a pure function; the negative-fixture class feeds each one a minimal bad input.

Run directly:

    apps/dbc-tools/.venv/bin/python3 -m pytest apps/dbc-tools/lib/test_hunter_bm_data.py -q
hunter-pet-families ruling 23 (PLAN §11, user 2026-11-13):
  (ac) the type scales (ruling 23b adds Tenacity command damage x0.80: the F2 commands and helpers, Bear's Swipe /
  Maul, the Tenacity defaults Thrash / Crushing Blow): Bite / Claw / Smack x1.5 (the Ferocity and Tenacity basics), every Cunning damage potency (the
  F3 commands and helpers, Spider's Venom Bite / Venomous Cloud + splash, the type defaults Feint Strike / Ambush, Spit /
  Venom Spit) x0.39; no Cunning kit keeps a Ferocity / Tenacity basic.
hunter-pet-families ruling 24 (PLAN §11, user 2026-11-13):
  (ad) pet type identity: the single-target Ferocity commands and helpers x1.07 and the single-target Cunning ones a
  further x0.94 (single-target = what Hunter::IsBeastCleaveExcluded lets Beast Cleave copy, plus the non-area damage
  helpers), the AoE commands and their splashes untouched; the Beast Cleave pet copy multipliers (Ferocity 0.93,
  Tenacity 1.0, Cunning 1.74) as const()s in HunterData.h, read by spell_hun_beast_cleave for the pet only; the
  talent tooltip's line.
hunter-pet-families F2 (hunter-pet-families.F2.HANDOFF.md):
  (aa) the 9 Tenacity kits: potency = the ruling 1 scale of PLAN §3.2, the commands and their helpers (Gore's debuff,
  Pincer Crush's root, Burrow Attack's pulse, Death Roll's channel, Warp Strike's blink, Deadly Sting's refresh), the
  utilities (levels, cooldowns, raid TargetA 56, Earthen Bulwark manual with no Mobility, groups incl. the new 1232
  rule 4, Bubble Shield's absorb on the hunter), the script bindings.
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
BM_SCRIPT_CPP = REPO_ROOT / "src" / "server" / "scripts" / "Spells" / "spell_hunter_beast_mastery.cpp"

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


def check_commanded_spell(spell_id: int, row: dict | None, extra_effects: frozenset[int] = frozenset(),
                          extra_auras: frozenset[int] = frozenset(), ranged: bool | None = None) -> list[str]:
    """(b) one commanded spell: family 9 + d1 b28 + d2 b22, only SCHOOL_DAMAGE / PERIODIC_DAMAGE (+ the Lunge JUMP and
    Venomous Cloud's TRIGGER_SPELL) among the effects, at least one damage effect, DefenseType RANGED exactly for the
    four ranged ones. hunter-pet-families F1: `extra_effects` / `extra_auras` admit a command's other effects (a DUMMY
    target anchor or follow-up, a snare); F3: `ranged` overrides the RANGED_COMMANDED lookup (the Cunning commands)."""
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
            elif aura not in extra_auras:
                bad.append(f"effect {index} is APPLY_AURA with aura {aura}, expected PERIODIC_DAMAGE (3)")
        elif effect not in (EFFECT_JUMP, EFFECT_TRIGGER_SPELL) and effect not in extra_effects:
            bad.append(f"effect {index} has unexpected type {effect}")
    if not damage:
        bad.append("no SCHOOL_DAMAGE / PERIODIC_DAMAGE effect")
    is_ranged = spell_id in RANGED_COMMANDED if ranged is None else ranged
    want = DEFENSE_RANGED if is_ranged else DEFENSE_MELEE
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


_KIT_FIELDS = ("basic", "group", "utility", "commandI", "commandII", "flags")
_FIELD = r"\s*([\w:]+)\s*"
_KIT_ROW = re.compile(r"\{\s*(\d+)\s*,\s*\{" + ",".join([_FIELD] * 6) + r"\}\s*\}")
_DEFAULT_ROW = re.compile(r"constexpr\s+PetKit\s+(KIT_\w+)\s*=\s*\{" + ",".join([_FIELD] * 6) + r"\}\s*;")
_DISPLAY_ROW = re.compile(r"\{\s*([\w:]+)\s*,\s*([\w:]+)\s*\}")
KIT_FLAGS = {"PET_KIT_GROUP_AUTOCAST": 0x1}


def _header_names(hunter_data_h: str) -> dict[str, int]:
    return {m.group(1): int(m.group(2))
            for m in re.finditer(r"constexpr\s+u?int32\s+(\w+)\s*=\s*(\d+)\s*;", hunter_data_h)}


def _block(mechanics_cpp: str, name: str) -> str:
    """The `{{ ... }};` initializer of the std::array `name` in HunterMechanics.cpp ('' when missing)."""
    m = re.search(rf"\b{name}\s*=\s*\{{\{{(.*?)\}}\}};", mechanics_cpp, re.S)
    return m.group(1) if m else ""


def _resolve(token: str, names: dict[str, int], unresolved: list[str]) -> int:
    token = token.removeprefix("HunterData::").removeprefix("Hunter::")
    if token.isdigit():
        return int(token)
    if token in KIT_FLAGS:
        return KIT_FLAGS[token]
    if token in names:
        return names[token]
    unresolved.append(token)
    return -1


def _strip_comments(cpp: str) -> str:
    return re.sub(r"//[^\n]*", "", cpp)


def parse_kits(mechanics_cpp: str, hunter_data_h: str) -> tuple[dict[int, dict], dict[str, dict], list[str]]:
    """hunter-pet-families F0: (FAMILY_KITS rows by family id, the KIT_*_DEFAULT rows by name, unresolved names).
    Each row is a dict of `_KIT_FIELDS`; a name is resolved through HunterData.h (0 and flag names literally)."""
    names, unresolved = _header_names(hunter_data_h), []
    cpp = _strip_comments(mechanics_cpp)
    kits: dict[int, dict] = {}
    for m in _KIT_ROW.finditer(_block(cpp, "FAMILY_KITS")):
        family = int(m.group(1))
        row = {field: _resolve(m.group(n + 2), names, unresolved) for n, field in enumerate(_KIT_FIELDS)}
        kits.setdefault(family, row) if family not in kits else unresolved.append(f"duplicate family {family}")
    defaults = {m.group(1): {field: _resolve(m.group(n + 2), names, unresolved) for n, field in enumerate(_KIT_FIELDS)}
                for m in _DEFAULT_ROW.finditer(cpp)}
    return kits, defaults, unresolved


def parse_command_displays(mechanics_cpp: str, hunter_data_h: str) -> tuple[dict[int, int], list[str]]:
    """hunter-pet-families F0: COMMAND_DISPLAYS as {command id: display id}, plus unresolved names."""
    names, unresolved = _header_names(hunter_data_h), []
    displays: dict[int, int] = {}
    for m in _DISPLAY_ROW.finditer(_block(_strip_comments(mechanics_cpp), "COMMAND_DISPLAYS")):
        command = _resolve(m.group(1), names, unresolved)
        if command in displays:
            unresolved.append(f"duplicate command {m.group(1)}")
        displays[command] = _resolve(m.group(2), names, unresolved)
    return displays, unresolved


def parse_kit_slots(mechanics_cpp: str, hunter_data_h: str) -> dict[int, str]:
    """PT-5: commanded spell id -> 'I' / 'II', read from the kit tables of HunterMechanics.cpp (FAMILY_KITS and the
    KIT_*_DEFAULT rows, parse_kits). A spell found in both slots maps to 'both'; an unresolved name is kept under -1."""
    kits, defaults, unresolved = parse_kits(mechanics_cpp, hunter_data_h)
    slots: dict[int, str] = {}
    if unresolved:
        slots[-1] = unresolved[0]
    for row in (*kits.values(), *defaults.values()):
        for field, slot in (("commandI", "I"), ("commandII", "II")):
            spell_id = row[field]
            if spell_id <= 0:
                continue
            if slots.get(spell_id, slot) != slot:
                slot = "both"
            slots[spell_id] = slot
    return slots


def check_command_displays(rows_by_id: dict[int, dict], displays: dict[int, int], slots: dict[int, str],
                           bound: list[dict], talents: list[dict], trainer_spells: list[dict]) -> list[str]:
    """(t) PT-5 (brief decision 1) + hunter-pet-families F0: COMMAND_DISPLAYS names a display for every slotted command
    and for nothing else: Attributes 0x150 (PASSIVE, no DO_NOT_DISPLAY 0x80), eff0 APPLY_AURA DUMMY at target 1,
    family 0 without bits, Name "Command <slot>: <commanded name>" with the slot the kit tables give it; no script
    binding, in no talent row, no trainer row. 201736 (no slot) has none."""
    bad = []
    if -1 in slots:
        bad.append(f"HunterMechanics.cpp kit names {slots[-1]} not found in HunterData.h")
    slotted = {i for i in slots if i > 0}
    if set(displays) != slotted:
        bad.append(f"COMMAND_DISPLAYS commands {sorted(set(displays))} != the kits' commands {sorted(slotted)}")
    for commanded in sorted(slotted):
        display = displays.get(commanded)
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
    if COMMANDED[-1] in displays:
        bad.append(f"{COMMANDED[-1]}: the splash has a display, but no kit slot names it")
    shown = set(displays.values())
    for r in bound:
        if int(r["spell_id"]) in shown:
            bad.append(f"{r['spell_id']}: display spell bound to {r['ScriptName']} (no script, PT-5)")
    for t in talents:
        for sid in t.get("rank_spell_ids") or []:
            if sid in shown:
                bad.append(f"talent {t['id']}: rank {sid} is a display spell")
    for t in trainer_spells:
        if int(t["SpellId"]) in shown:
            bad.append(f"trainer {t['TrainerId']}: teaches display spell {t['SpellId']}")
    return bad


# (v) hunter-pet-families F0: the 32 hunter families (CreatureFamily.dbc ids with a pet talent type).
HUNTER_FAMILIES = frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 20, 21, 24, 25, 26, 27, 30, 31, 32, 33, 34, 35, 37, 38,
                             39, 41, 42, 43, 44, 45, 46})
PET_ABILITY_D1 = 0x10000000
PET_UTILITY_D1 = 0x20000000
# Slot 2 spells that skip the Mobility bit (ruling 10): Ancient Hysteria 201760, Eternal Guardian 201761 (F1), Earthen
# Bulwark 201769 (F2).
NO_MOBILITY_UTILITIES: frozenset[int] = frozenset({201760, 201761, 201769})
# The placeholders of the families without a kit (Dash, Last Stand, Bullheaded): F3 removed them from every kit, so no
# kit row may name one.
PLACEHOLDER_SLOT_SPELLS = frozenset({61684, 53478, 53490})
FINISHED_KITS = {     # family: (group, utility)
    1: (24604, 201983), 2: (201715, 201984), 11: (201716, 201985), 4: (201717, 201986), 3: (201753, 201718),
    # hunter-pet-families F1: the 8 Ferocity kits (PLAN §3.1)
    7: (201754, 201987), 25: (201755, 201988), 12: (201756, 201989), 37: (201757, 201990), 44: (201758, 201991),
    39: (201759, 201992), 45: (201760, 201993), 46: (201761, 201994),
    # hunter-pet-families F2: the 9 Tenacity kits (PLAN §3.2)
    5: (201762, 201995), 6: (201763, 201996), 21: (201764, 201997), 8: (201765, 201998), 20: (201766, 201999),
    9: (201767, 202000), 32: (201768, 202001), 42: (201769, 202002), 43: (201770, 202003),
    # hunter-pet-families F3: the 10 Cunning kits (PLAN §3.3)
    24: (201771, 202004), 26: (201772, 202005), 27: (201773, 202006), 30: (201774, 202007), 31: (201775, 202008),
    35: (201776, 202009), 33: (201777, 202010), 34: (201778, 202011), 38: (201779, 202012), 41: (201780, 202013),
}
# Finished kits whose slot 2 is manual (no PET_KIT_GROUP_AUTOCAST): the long raid cooldowns.
MANUAL_GROUP_FAMILIES = frozenset({45, 46, 42})


def check_family_kits(kits: dict[int, dict], defaults: dict[str, dict], unresolved: list[str],
                      displays: dict[int, int], rows_by_id: dict[int, dict]) -> list[str]:
    """(v) one row per hunter family; every id declared; commands with a display; slot spells with d1 b28 + b29
    (d1 b28 alone for NO_MOBILITY_UTILITIES); every family's kit slot spells (FINISHED_KITS, all 32 since F3); slot 2
    autocast except the manual raid cooldowns; no kit names a retired placeholder; the type defaults carry no slot
    spell."""
    bad = [f"HunterMechanics.cpp: {name} not resolved through HunterData.h" for name in unresolved]
    if set(kits) != HUNTER_FAMILIES:
        bad.append(f"FAMILY_KITS families: missing {sorted(HUNTER_FAMILIES - set(kits))}, "
                   f"extra {sorted(set(kits) - HUNTER_FAMILIES)}")
    for family, row in sorted(kits.items()):
        for field in _KIT_FIELDS[:5]:
            spell_id = row[field]
            if field in ("basic", "commandI", "commandII") and spell_id <= 0:
                bad.append(f"family {family}: {field} is empty")
            elif spell_id > 0 and spell_id not in rows_by_id:
                bad.append(f"family {family}: {field} {spell_id} is not declared by the hunter package")
        for field in ("commandI", "commandII"):
            if row[field] > 0 and row[field] not in displays:
                bad.append(f"family {family}: {field} {row[field]} has no COMMAND_DISPLAYS pair")
        for field in ("group", "utility"):
            spell = rows_by_id.get(row[field])
            if spell is None:
                continue
            if row[field] in PLACEHOLDER_SLOT_SPELLS:
                bad.append(f"family {family}: {field} {row[field]} is a retired placeholder (F3)")
            want = PET_ABILITY_D1 | (0 if row[field] in NO_MOBILITY_UTILITIES else PET_UTILITY_D1)
            got = spell_mask(spell)[1] & (PET_ABILITY_D1 | PET_UTILITY_D1)
            if _i(spell, "SpellClassSet") != SPELLFAMILY_HUNTER or got != want:
                bad.append(f"family {family}: {field} {row[field]} SpellClassSet {spell.get('SpellClassSet')} d1 "
                           f"0x{spell_mask(spell)[1]:X}, expected family 9 with 0x{want:X} of d1 b28/b29")
        finished = FINISHED_KITS.get(family)
        if finished and (row["group"], row["utility"]) != finished:
            bad.append(f"family {family}: slots {(row['group'], row['utility'])}, F0 says {finished}")
        want_autocast = bool(finished) and family not in MANUAL_GROUP_FAMILIES
        if bool(row["flags"] & KIT_FLAGS["PET_KIT_GROUP_AUTOCAST"]) != want_autocast:
            bad.append(f"family {family}: GROUP_AUTOCAST {bool(row['flags'] & 1)}, expected {want_autocast}")
    if set(defaults) != {"KIT_FEROCITY_DEFAULT", "KIT_TENACITY_DEFAULT", "KIT_CUNNING_DEFAULT", "KIT_NONE"}:
        bad.append(f"type default kits: {sorted(defaults)}")
    for name, row in defaults.items():
        if row["group"] or row["utility"] or row["flags"]:
            bad.append(f"{name}: a type default seats the basic and Growl only, got {row}")
        if name != "KIT_NONE" and not (row["commandI"] in displays and row["commandII"] in displays):
            bad.append(f"{name}: commands without a COMMAND_DISPLAYS pair")
    return bad


# (w) the F0 utilities: id -> (SpellLevel, Effect_1, EffectAura_1, EffectBasePoints_1, amplitude, RecoveryTime ms)
F0_UTILITIES = {
    201983: (36, EFFECT_APPLY_AURA, 20, 5, 1000, 60000),        # Lick Your Wounds: 6% x 5 = 30% over 5 s
    201984: (20, EFFECT_APPLY_AURA, 16, 149, 0, 0),             # Prowl (24450's numbers; category 38 cooldown)
    201985: (30, 98, 0, 149, 0, 30000),                         # Tail Sweep: knockback
    201986: (36, EFFECT_APPLY_AURA, 20, 2, 1000, 60000),        # Frenzied Regeneration: 3% x 10 = 30% over 10 s
    201753: (26, EFFECT_APPLY_AURA, 216, -26, 0, 10000),        # Sticky Webbing: casting time +25%
}
KIT_V2_MARKER = 202014
AURA_INTERRUPT_MELEE_ATTACK = 0x1000
SPELL_GROUP_CAST_TIME_DEBUFFS = 1096


def check_f0_utilities(rows_by_id: dict[int, dict], groups: list[dict]) -> list[str]:
    """(w) shape of each F0 utility (level, first effect, cooldown), d1 b28 + b29 family 9, EquippedItemClass -1, not
    passive; Prowl breaks on the pet's melee swing; Tail Sweep targets the enemy; Sticky Webbing in group 1096; the
    kit v2 marker is a hidden passive DUMMY with no family."""
    bad = []
    for spell_id, (level, effect, aura, bp, amplitude, recovery) in F0_UTILITIES.items():
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
            continue
        got = (_i(row, "SpellLevel"), _i(row, "Effect_1"), _i(row, "EffectAura_1"), _i(row, "EffectBasePoints_1"),
               _i(row, "EffectAuraPeriod_1"), _i(row, "RecoveryTime"))
        if got != (level, effect, aura, bp, amplitude, recovery):
            bad.append(f"{spell_id}: (level, effect, aura, bp, amplitude, cooldown) {got}, expected "
                       f"{(level, effect, aura, bp, amplitude, recovery)}")
        if _i(row, "SpellClassSet") != SPELLFAMILY_HUNTER or spell_mask(row) != (0, 0x30000000, 0):
            bad.append(f"{spell_id}: family {row.get('SpellClassSet')} mask {_hex(spell_mask(row))}, expected 9 "
                       f"(0, 0x30000000, 0)")
        if _i(row, "EquippedItemClass") != -1 or _i(row, "Attributes") & ATTR_PASSIVE:
            bad.append(f"{spell_id}: EquippedItemClass {row.get('EquippedItemClass')} / passive")
    prowl = rows_by_id.get(201984)
    if prowl is not None and not _i(prowl, "AuraInterruptFlags") & AURA_INTERRUPT_MELEE_ATTACK:
        bad.append("201984: Prowl lacks AuraInterruptFlags 0x1000 (MELEE_ATTACK): the next swing must break it")
    sweep = rows_by_id.get(201985)
    if sweep is not None and _i(sweep, "ImplicitTargetA_1") != TARGET_UNIT_TARGET_ENEMY:
        bad.append(f"201985: Tail Sweep TargetA {sweep.get('ImplicitTargetA_1')}, expected 6 (the target)")
    if not any(int(g["id"]) == SPELL_GROUP_CAST_TIME_DEBUFFS and int(g["spell_id"]) == 201753 for g in groups):
        bad.append("201753: Sticky Webbing not in spell_group 1096 (Cast Time Debuffs)")
    marker = rows_by_id.get(KIT_V2_MARKER)
    if marker is None:
        bad.append(f"{KIT_V2_MARKER}: kit v2 marker not declared")
    else:
        if _i(marker, "Attributes") != 464 or _aura_dummy_on_self(marker):
            bad.append(f"{KIT_V2_MARKER}: Attributes {marker.get('Attributes')}, expected the hidden passive DUMMY 464")
        if _i(marker, "SpellClassSet") or any(spell_mask(marker)):
            bad.append(f"{KIT_V2_MARKER}: has a family or mask")
    return bad


# (x) Mobility and the d1 b29 group
MOBILITY = {53483: -11, 53485: -21}       # stored base points: -10% / -20%
SPELLMOD_COOLDOWN = 11
EFFECT_APPLY_AREA_AURA_PET = 119
# Every d1 b29 carrier the package declares: the slot 2 / 3 utilities, plus the retired Dive 23145 (F3 took the bit
# off the retired Dash 61684).
D1_B29_CARRIERS = frozenset({23145, 24604, 201715, 201716, 201717, 201718, 201753, 201983, 201984, 201985,
                             201986,
                             # hunter-pet-families F1: the Ferocity slot 2 (not 201760 / 201761, ruling 10) and slot 3
                             *range(201754, 201760), *range(201987, 201995),
                             # F2: the Tenacity slot 2 (not Earthen Bulwark 201769, ruling 10) and slot 3
                             *range(201762, 201769), 201770, *range(201995, 202004),
                             # F3: the Cunning slot 2 and slot 3 (no ruling 10 spell among them)
                             *range(201771, 201781), *range(202004, 202014)})
# Readers: Mobility, the retired Dive ranks (talent 2208 retired, never applied), and Point of No Escape 202058, whose
# aura 271 reads every bit but two (damage from caster: a pet utility deals no damage).
D1_B29_READERS = frozenset({53483, 53485, 53554, 53555, 202058})


def check_mobility(rows_by_id: dict[int, dict], rows: list[dict]) -> list[str]:
    bad = []
    for spell_id, bp in MOBILITY.items():
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
            continue
        got = (_i(row, "Effect_1"), _i(row, "EffectAura_1"), _i(row, "EffectMiscValue_1"),
               _i(row, "EffectBasePoints_1"), effect_mask(row, 1))
        want = (EFFECT_APPLY_AREA_AURA_PET, AURA_ADD_PCT_MODIFIER, SPELLMOD_COOLDOWN, bp, (0, PET_UTILITY_D1, 0))
        if got != want:
            bad.append(f"{spell_id}: (effect, aura, misc, bp, mask) {got}, expected {want}")
    family9 = [r for r in rows if _i(r, "SpellClassSet") == SPELLFAMILY_HUNTER]
    carriers = {int(r["ID"]) for r in family9 if spell_mask(r)[1] & PET_UTILITY_D1}
    readers = {int(r["ID"]) for r in family9 if any(effect_mask(r, e)[1] & PET_UTILITY_D1 for e in (1, 2, 3))}
    if carriers != D1_B29_CARRIERS:
        bad.append(f"d1 b29 carriers: extra {sorted(carriers - D1_B29_CARRIERS)}, "
                   f"missing {sorted(D1_B29_CARRIERS - carriers)}")
    if readers != D1_B29_READERS:
        bad.append(f"d1 b29 readers: extra {sorted(readers - D1_B29_READERS)}, missing {sorted(D1_B29_READERS - readers)}")
    return bad


# (u) S1b-HANDOFF tooltip table rows T1 / T16 / PT2 (coordinator: "only if cheap"): the new text is in the built
# Description, the old text is gone. id -> (required substrings, forbidden substrings).
_T1_MAIN = ("Increases the chance for your Aspect of the Monkey to grant Versatility by $s1%, and increases your "
            "Versatility by $s2%.")
_T1_CAP = ("Increases the speed bonus of your Aspect of the Cheetah, Aspect of the Pack and mounts by $201813s1%. Does "
           "not stack with other effects that increase mounted speed.")
_T1_OLD = ("Aspect of the Monkey to trigger by", "and your mounted speed by")
_T16 = "Increases the damage done by your pet by $s1%."
_PT2 = "Reduces the cooldown of your pet's utility abilities by ${$m1*-1}%."   # hunter-pet-families F0
TOOLTIP_TEXTS = {
    **{i: ((_T1_MAIN, _T1_CAP), _T1_OLD) for i in (19559, 19560, 201820)},       # T1 Pathfinding (stock ranks + capstone)
    **{i: ((_T16,), ("Increases your pet's damage by",)) for i in (201839, 201840)},  # T16 Shark Attack
    **{i: ((_PT2,), ("Dash",)) for i in (53483, 53485)},                             # PT2 Mobility (F0)
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


# (z) hunter-pet-families F1 (F1.HANDOFF §1, §2, §5; PLAN §3.1, §4.1, §5.2): the 8 Ferocity kits.
F1_SCALE = {"I": 0.84, "II": 0.65}        # ruling 1: _pet_kits.COMMAND_I_SCALE / COMMAND_II_SCALE
# Commanded spell or helper -> [(effect, the §3.1 number, slot, kind)]. 'direct' = the effect's potency; 'total' = a
# DoT's total over the spell's duration (rate x amplitude / 1.5 s per tick, times the ticks).
F1_POTENCY = {
    201606: [(1, 150, "I", "direct"), (2, 250, "I", "total")],     # Rend Flesh
    201607: [(1, 800, "II", "direct")],                             # Carrion Feast
    201608: [(1, 400, "I", "direct")],                              # Tendon Rip
    201609: [(1, 333, "II", "direct")], 201660: [(1, 333, "II", "direct")],    # Cackling Frenzy + strike
    201610: [(2, 400, "I", "direct")],                              # Leaping Kick (eff1 is the jump)
    201611: [(1, 1000, "II", "direct")],                            # Stampeding Kick
    201612: [(1, 600, "I", "direct")],                              # Serenity Dust
    201613: [(1, 800, "II", "direct")],                             # Dazzling Wings
    201614: [(1, 150, "I", "direct"), (2, 250, "I", "total")],     # Sting
    201615: [(1, 200, "II", "direct")], 201661: [(1, 200, "II", "direct")],    # Swarm + strike
    201616: [(1, 400, "I", "direct")],                              # Monstrous Bite
    201617: [(1, 1000, "II", "direct")],                            # Primal Rampage
    201618: [(1, 300, "I", "direct")],                              # Lava Breath
    201619: [(1, 550, "II", "direct")], 201662: [(1, 550, "II", "direct")],    # Twin Bite + second bite
    201620: [(1, 400, "I", "direct")],                              # Spirit Strike
    201621: [(1, 1000, "II", "direct")],                            # Spirit Pounce
}
F1_COMMANDS = tuple(range(201606, 201622))
F1_HELPERS = (201660, 201661, 201662)
F1_NATURE_COMMANDS = frozenset({201614, 201620})
F1_FIRE_COMMANDS = frozenset({201618})
# command -> (strike helper, follow-ups); Twin Bite is the twohit shape: one follow-up (F1 review MINOR 1)
F1_MULTIHIT = {201609: (201660, 2), 201615: (201661, 4), 201619: (201662, 1)}
ATTR1_NO_AUTOCAST_AI = 0x20000
F1_NO_AUTOCAST = frozenset({201760, 201761})                       # F1 review MINOR 2
F1_CONES = (201613, 201618)
AURA_MOD_DECREASE_SPEED = 33
EFFECT_HEAL_PCT = 136
EFFECT_RESURRECT = 18
TARGET_UNIT_CASTER_AREA_RAID = 56
TARGET_UNIT_CONE_ENEMY = 104
SUPPRESS_CASTER_PROCS = 0x10000
# slot 2 / slot 3 / utility helpers: unlock level (SpellLevel = the pet level the SkillLineAbility row teaches it)
F1_LEVELS = {201754: 14, 201755: 32, 201756: 20, 201757: 26, 201758: 15, 201759: 30, 201760: 60, 201761: 20,
             201987: 36, 201988: 20, 201989: 16, 201990: 12, 201991: 30, 201992: 30, 201993: 30, 201994: 30}
F1_RAID_EFFECTS = frozenset({201755, 201757, 201759, 201760, 201994})    # every effect TargetA 56 (ruling 7)
F1_SPELL_GROUPS = {201754: 1062, 201755: 1022, 201756: 1060, 201757: 1105, 201758: 1058, 201759: 1056,
                   201988: 1061}
F1_RECOVERY = {201754: 10000, 201755: 40000, 201756: 10000, 201757: 40000, 201758: 10000, 201759: 40000,
               201760: 300000, 201761: 600000, 201987: 60000, 201988: 30000, 201989: 30000, 201990: 60000,
               201991: 60000, 201992: 60000, 201993: 60000, 201994: 60000}
FRESH_KILL = 202018
ETERNAL_GUARDIAN_REBIRTH = 202017
TARGET_FLAG_CORPSE_ALLY = 0x8000
# script -> the F1 ids bound to it (positive keys); Swipe keeps its F0 bindings
F1_SCRIPT_BINDINGS = {
    201607: {"spell_hun_command_execute"},
    201609: {"spell_hun_command_multihit"}, 201615: {"spell_hun_command_multihit"},
    201619: {"spell_hun_command_multihit"},
    201613: {"spell_hun_command_aoe_falloff"}, 201618: {"spell_hun_command_aoe_falloff"},
    201991: {"spell_hun_pet_control_boss_filter"}, 201992: {"spell_hun_pet_control_boss_filter"},
    201987: {"spell_hun_pet_scavenge"}, 201761: {"spell_hun_pet_eternal_guardian"},
    201760: {"spell_sha_bloodlust"},
}
F1_IDS = frozenset({*F1_COMMANDS, *F1_HELPERS, *range(201754, 201762), *range(201987, 201995), 202017, 202018,
                    *range(202109, 202125)})


def _potency_of(entry: dict, effect: int, kind: str) -> float | None:
    pot = (entry.get(f"effect{effect}") or {}).get("_potency")
    if not pot:
        return None
    if kind == "direct":
        return float(pot["total_potency"])
    return float(pot["total_potency"]) * float(pot["t_seconds"]) / 1.5 * float(pot.get("ticks", 1.0))


def check_f1_potency(entries_by_id: dict[int, dict], table=F1_POTENCY, extra_scale: float = 1.0,
                     id_scales: dict[int, float] | None = None) -> list[str]:
    """(z) every new command (and helper hit) is the ruling 1 scale of its §3.1 number; `extra_scale` is a further
    type scale on top (F3: the Cunning damage scale of ruling 23), `id_scales` a per-spell one on top of that (ruling
    24: the single-target commands)."""
    bad = []
    for spell_id, rows in table.items():
        entry = entries_by_id.get(spell_id)
        if entry is None:
            bad.append(f"{spell_id}: not declared")
            continue
        scale = extra_scale * (id_scales or {}).get(spell_id, 1.0)
        for effect, authored, slot, kind in rows:
            got = _potency_of(entry, effect, kind)
            want = authored * F1_SCALE[slot] * scale
            if got is None or abs(got - want) > 0.01:
                bad.append(f"{spell_id} eff{effect}: potency ({kind}) {got}, expected {authored} x {F1_SCALE[slot]}"
                           f"{f' x {round(scale, 4)}' if scale != 1.0 else ''} = {round(want, 4)}")
    return bad


# (ac) hunter-pet-families PLAN §11 ruling 23 (user 2026-11-13): the type scales after the 32-family sweep (Cunning
# ~3,000 DPS vs Ferocity ~1,690 / Tenacity ~1,830). Pinned here independently of _pet_kits.py's constants.
R23_CUNNING_SCALE = 0.39
R23_BASIC_SCALE = 1.5
R23B_TENACITY_SCALE = 0.80      # ruling 23b: Tenacity command damage (the F2 commands, Bear, the Tenacity defaults)
CUNNING_FAMILIES = frozenset({3, 24, 26, 27, 30, 31, 33, 34, 35, 38, 41})   # Spider + the ten F3 kits
R24_CUNNING_ST_SCALE = 0.94     # ruling 24 (section (ad)): the single-target Cunning commands, on top of x0.39
R24_CUNNING_ST = R23_CUNNING_SCALE * R24_CUNNING_ST_SCALE
# spell -> [(effect, the pre-ruling-23 potency, kind, scale)]; 'total' = a DoT's total over its duration (a rate of 63 per
# 1.5 s for 6 s is 252). The F3 commands are in F3_POTENCY (extra_scale), these are the rows with no PLAN §3 number.
R23_POTENCY = {
    17253: [(1, 40.8, "direct", R23_BASIC_SCALE)],         # Bite (TUNE1 40.8)
    16827: [(1, 25.5, "direct", R23_BASIC_SCALE)],         # Claw
    49966: [(1, 25.5, "direct", R23_BASIC_SCALE)],         # Smack
    201710: [(1, 33.0, "direct", R23_CUNNING_SCALE)],      # Venom Spit (Spider)
    201711: [(1, 33.0, "direct", R23_CUNNING_SCALE)],      # Spit (every other Cunning family)
    201728: [(1, 504.0, "direct", R24_CUNNING_ST), (2, 252.0, "total", R24_CUNNING_ST)],   # Venom Bite (ST, r24)
    201729: [(1, 1170.0, "total", R23_CUNNING_SCALE)],     # Venomous Cloud (219.375 x 2 s / 1.5 s x 4 ticks)
    201736: [(1, 585.0, "total", R23_CUNNING_SCALE)],      # its 50% splash
    201734: [(1, 756.0, "direct", R24_CUNNING_ST)],        # Feint Strike (Cunning type default I; ST, ruling 24)
    201735: [(1, 1170.0, "direct", R24_CUNNING_ST)],       # Ambush (Cunning type default II; ST, ruling 24)
    # ruling 23b (the F2 commands are in F2_POTENCY with extra_scale): Bear's retrofit numbers and the type defaults
    201726: [(1, 420.0, "direct", R23B_TENACITY_SCALE), (2, 420.0, "direct", R23B_TENACITY_SCALE)],   # Swipe + splash eff
    201727: [(1, 715.0, "direct", R23B_TENACITY_SCALE)],   # Maul
    201732: [(1, 504.0, "direct", R23B_TENACITY_SCALE)],   # Thrash (Tenacity type default I)
    201733: [(1, 650.0, "direct", R23B_TENACITY_SCALE)],   # Crushing Blow (Tenacity type default II)
}


def check_ruling_23_potency(entries_by_id: dict[int, dict], table=R23_POTENCY) -> list[str]:
    """(ac) each scaled spell's potency = its pre-ruling number x its ruling 23 scale."""
    bad = []
    for spell_id, rows in table.items():
        entry = entries_by_id.get(spell_id)
        if entry is None:
            bad.append(f"{spell_id}: not declared")
            continue
        for effect, current, kind, scale in rows:
            got = _potency_of(entry, effect, kind)
            want = current * scale
            if got is None or abs(got - want) > 0.01:
                bad.append(f"{spell_id} eff{effect}: potency ({kind}) {got}, expected {current} x {scale} = "
                           f"{round(want, 4)}")
    return bad


def check_f1_commands(rows_by_id: dict[int, dict], displays: dict[int, int]) -> list[str]:
    """(z) the commands and helpers are commanded-spell carriers; schools; helpers suppress caster procs and have no
    display; the multi-hit follow-ups (Twin Bite's second bite included) and the cones' target anchor."""
    bad = []
    for spell_id in (*F1_COMMANDS, *F1_HELPERS):
        bad += check_commanded_spell(spell_id, rows_by_id.get(spell_id), frozenset({EFFECT_DUMMY}),
                                     frozenset({AURA_MOD_DECREASE_SPEED}))
        row = rows_by_id.get(spell_id)
        if row is None:
            continue
        school = 8 if spell_id in F1_NATURE_COMMANDS else 4 if spell_id in F1_FIRE_COMMANDS else 1
        if _i(row, "SchoolMask") != school:
            bad.append(f"{spell_id}: SchoolMask {row.get('SchoolMask')}, expected {school}")
    for helper in F1_HELPERS:
        row = rows_by_id.get(helper)
        if row is not None and not _i(row, "AttributesEx3") & SUPPRESS_CASTER_PROCS:
            bad.append(f"{helper}: a command helper without SUPPRESS_CASTER_PROCS (it would proc the pet talents "
                       f"again)")
        if helper in displays:
            bad.append(f"{helper}: a command helper has a COMMAND_DISPLAYS pair (it is in no kit slot)")
    for command, (strike, follow_ups) in F1_MULTIHIT.items():
        row = rows_by_id.get(command) or {}
        dummies = [n for n, effect, _ in _effects(row) if effect == EFFECT_DUMMY]
        if len(dummies) != 1 or _i(row, f"EffectTriggerSpell_{dummies[0]}") != strike or \
                live_value(row, dummies[0]) != follow_ups:
            bad.append(f"{command}: expected one DUMMY naming strike {strike} with value {follow_ups} (the follow-ups)")
    for command in F1_CONES:
        row = rows_by_id.get(command) or {}
        cone = [n for n, effect, _ in _effects(row) if effect == EFFECT_SCHOOL_DAMAGE and
                _i(row, f"ImplicitTargetA_{n}") == TARGET_UNIT_CONE_ENEMY]
        anchor = [n for n, effect, _ in _effects(row) if effect == EFFECT_DUMMY and
                  _i(row, f"ImplicitTargetA_{n}") == TARGET_UNIT_TARGET_ENEMY]
        if len(cone) != 1 or len(anchor) != 1:
            bad.append(f"{command}: expected one cone damage effect (TargetA 104) and one DUMMY at the target (the "
                       f"falloff's primary), got {cone} / {anchor}")
    return bad


def check_f1_utilities(rows_by_id: dict[int, dict], groups: list[dict]) -> list[str]:
    """(z) unlock level, cooldown, family 9, not passive, EquippedItemClass -1; TargetA 56 on the raid effects; the
    stock spell groups; Scavenge, Fresh Kill and the hidden Rebirth."""
    bad = []
    for spell_id, level in F1_LEVELS.items():
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
            continue
        if (_i(row, "SpellLevel"), _i(row, "RecoveryTime")) != (level, F1_RECOVERY[spell_id]):
            bad.append(f"{spell_id}: (SpellLevel, RecoveryTime) {(_i(row, 'SpellLevel'), _i(row, 'RecoveryTime'))}, "
                       f"expected {(level, F1_RECOVERY[spell_id])}")
        if _i(row, "SpellClassSet") != SPELLFAMILY_HUNTER or _i(row, "EquippedItemClass") != -1 or \
                _i(row, "Attributes") & ATTR_PASSIVE:
            bad.append(f"{spell_id}: family {row.get('SpellClassSet')}, EquippedItemClass "
                       f"{row.get('EquippedItemClass')}, passive {bool(_i(row, 'Attributes') & ATTR_PASSIVE)}")
        if bool(_i(row, "AttributesEx") & ATTR1_NO_AUTOCAST_AI) != (spell_id in F1_NO_AUTOCAST):
            bad.append(f"{spell_id}: AttributesEx 0x{_i(row, 'AttributesEx'):X}, NO_AUTOCAST_AI (0x20000) expected "
                       f"only on the manual raid cooldowns {sorted(F1_NO_AUTOCAST)}")
        if spell_id in F1_RAID_EFFECTS:
            targets = [_i(row, f"ImplicitTargetA_{n}") for n, effect, _ in _effects(row) if effect]
            if not targets or any(t != TARGET_UNIT_CASTER_AREA_RAID for t in targets):
                bad.append(f"{spell_id}: TargetA {targets}, expected 56 (CASTER_AREA_RAID) on every effect")
    declared_groups = {(int(g["id"]), int(g["spell_id"])) for g in groups}
    for spell_id, group in F1_SPELL_GROUPS.items():
        if (group, spell_id) not in declared_groups:
            bad.append(f"{spell_id}: not in spell_group {group}")
    grouped = {sid for _, sid in declared_groups} & set(F1_LEVELS)
    if grouped - set(F1_SPELL_GROUPS):
        bad.append(f"F1 utilities in an unexpected spell_group: {sorted(grouped - set(F1_SPELL_GROUPS))}")
    scavenge = rows_by_id.get(201987) or {}
    if (_i(scavenge, "Effect_1"), _i(scavenge, "EffectBasePoints_1"), _i(scavenge, "ImplicitTargetA_1")) != \
            (EFFECT_HEAL_PCT, 59, TARGET_UNIT_CASTER):
        bad.append("201987: Scavenge is not HEAL_PCT 60% on the pet (ruling 4)")
    fresh = rows_by_id.get(FRESH_KILL) or {}
    if _i(fresh, "Attributes") & ATTR_PASSIVE or not _i(fresh, "DurationIndex") or _i(fresh, "SpellClassSet") or \
            _aura_dummy_on_self(fresh):
        bad.append(f"{FRESH_KILL}: Fresh Kill must be a visible (not passive) timed DUMMY on the pet, family 0")
    rebirth = rows_by_id.get(ETERNAL_GUARDIAN_REBIRTH) or {}
    got = tuple(_i(rebirth, key) for key in ("Effect_1", "ImplicitTargetA_1", "Targets", "SpellClassSet"))
    if got != (EFFECT_RESURRECT, 0, TARGET_FLAG_CORPSE_ALLY, 0):
        bad.append(f"{ETERNAL_GUARDIAN_REBIRTH}: the hidden Rebirth must be RESURRECT (18), no TargetA, Targets "
                   f"0x8000 (CORPSE_ALLY), family 0")
    return bad


def check_f1_bindings(bound: list[dict], expected=F1_SCRIPT_BINDINGS, ids=F1_IDS) -> list[str]:
    """(z) each script tag is bound to exactly its F1 spells (positive keys), and no other F1 id has a binding."""
    got: dict[int, set[str]] = {}
    for r in bound:
        sid = int(r["spell_id"])
        if sid in ids or -sid in ids:
            got.setdefault(sid, set()).add(r["ScriptName"])
    bad = []
    for sid in sorted(set(got) | set(expected)):
        if got.get(sid, set()) != expected.get(sid, set()):
            bad.append(f"{sid}: bound to {sorted(got.get(sid, set()))}, expected {sorted(expected.get(sid, set()))}")
    return bad



# (aa) hunter-pet-families F2 (F2.HANDOFF; PLAN §3.2, §4.1, §5.2): the 9 Tenacity kits.
# Commanded spell or helper -> [(effect, the §3.2 number, slot, kind)] (the F1 table's shape; a pulse is a third of the
# command's number per pulse).
F2_POTENCY = {
    201622: [(1, 650, "I", "direct")],                              # Gore
    201623: [(1, 800, "II", "direct")],                             # Tusk Sweep
    201624: [(1, 600, "I", "direct")],                              # Snap
    201625: [(1, 1300, "II", "total")],                             # Death Roll (channel)
    201626: [(1, 800, "I", "direct")],                              # Snapping Bite
    201627: [(1, 800, "II", "direct")],                             # Shell Spin
    201628: [(1, 800, "I", "direct")],                              # Pincer Crush
    201629: [(1, 800, "II", "direct")],                             # Bubble Burst
    201630: [(1, 300, "I", "direct"), (2, 300, "I", "total")],     # Stinger
    201631: [(1, 1000, "II", "direct")],                            # Deadly Sting
    201632: [(1, 500, "I", "direct")],                              # Thunderstomp
    201633: [(1, 1100, "II", "direct")],                            # Pound
    201634: [(2, 600, "I", "direct")],                              # Warp Strike (eff1 is the blink)
    201635: [(1, 1000, "II", "direct")],                            # Phase Rend
    201667: [(1, 500 / 3, "I", "direct")],                          # Burrow Attack's pulse (3 per press)
    201637: [(1, 1100, "II", "direct")],                            # Devour
    201638: [(2, 800, "I", "direct")],                              # Horn Charge (eff1 is the jump)
    201639: [(1, 800, "II", "direct")],                             # Stampede
}
F2_COMMANDS = tuple(range(201622, 201640))
F2_DAMAGE_HELPERS = (201667,)                       # Burrow Attack's pulse: a commanded-spell carrier
GORE_DEBUFF, PINCER_CRUSH_ROOT, BURROW_ATTACK_PULSE = 201665, 201666, 201667
F2_NATURE_COMMANDS = frozenset({201630, 201631})
F2_FROST_COMMANDS = frozenset({201629})
F2_ARCANE_COMMANDS = frozenset({201635})
F2_CONES = (201623, 201639)
F2_AROUND_PET = (201627, 201632, 201667)            # area around the pet (TargetA 22 / B 15) + DUMMY anchor
F2_TRIGGERS = {201622: GORE_DEBUFF, 201628: PINCER_CRUSH_ROOT}      # command -> its rider (TRIGGER_SPELL)
F2_ROOT_AURA = 26
F2_PERIODIC_TRIGGER = {201636: BURROW_ATTACK_PULSE}
F2_CHANNELS = frozenset({201625})
ATTR1_IS_CHANNELED = 0x4
ATTR3_DOT_STACKING_RULE = 0x80
EFFECT_TELEPORT_UNITS = 5
TARGET_DEST_TARGET_BACK = 65
F2_REFRESH = {201631: 201630}                       # Deadly Sting refreshes Stinger
F2_LEVELS = {201762: 40, 201763: 10, 201764: 10, 201765: 10, 201766: 15, 201767: 10, 201768: 26, 201769: 30,
             201770: 20, 201995: 30, 201996: 10, 201997: 28, 201998: 10, 201999: 18, 202000: 16, 202001: 10,
             202002: 30, 202003: 40}
F2_RECOVERY = {201762: 40000, 201763: 10000, 201764: 40000, 201765: 10000, 201766: 10000, 201767: 40000,
               201768: 10000, 201769: 120000, 201770: 40000, 201995: 60000, 201996: 60000, 201997: 60000,
               201998: 60000, 201999: 60000, 202000: 30000, 202001: 30000, 202002: 60000, 202003: 60000}
F2_RAID_EFFECTS = frozenset({201762, 201764, 201767, 201769, 201770, 202003})    # every effect TargetA 56
F2_NO_AUTOCAST = frozenset({201769})                # Earthen Bulwark (F1 review MINOR 2)
SPELL_GROUP_RAID_DAMAGE_TAKEN = 1232
RAID_DAMAGE_TAKEN_MEMBERS = frozenset({201769, 202006})     # Earthen Bulwark (F2), Gale Barrier (F3)
F2_SPELL_GROUPS = {201762: 1029, 201763: 1059, 201764: 1086, 201765: 1059, 201766: 1058, 201767: 1088, 201768: 1096,
                   201769: SPELL_GROUP_RAID_DAMAGE_TAKEN, 201770: 1006}
BUBBLE_SHIELD = 201998
AURA_SCHOOL_ABSORB = 69
TARGET_UNIT_MASTER = 27
F2_SCRIPT_BINDINGS = {
    201623: {"spell_hun_command_aoe_falloff"}, 201627: {"spell_hun_command_aoe_falloff"},
    201629: {"spell_hun_command_aoe_falloff"}, 201632: {"spell_hun_command_aoe_falloff"},
    201667: {"spell_hun_command_aoe_falloff"}, 201639: {"spell_hun_command_aoe_falloff"},
    201636: {"spell_hun_command_pulse"}, 201631: {"spell_hun_command_refresh"},
    201666: {"spell_hun_pet_control_boss_filter"}, 201995: {"spell_hun_pet_control_boss_filter"},
    201999: {"spell_hun_pet_control_boss_filter"}, 201998: {"spell_hun_pet_absorb"},
}
F2_IDS = frozenset({*F2_COMMANDS, GORE_DEBUFF, PINCER_CRUSH_ROOT, BURROW_ATTACK_PULSE, *range(201762, 201771),
                    *range(201995, 202004), *range(202125, 202143)})


def check_f2_commands(rows_by_id: dict[int, dict], displays: dict[int, int]) -> list[str]:
    """(aa) the commands and the pulse are commanded-spell carriers with their schools; the riders (Gore's debuff,
    Pincer Crush's root) are family-0 helpers cast by TRIGGER_SPELL; the cones and the pet-centered areas keep their
    DUMMY anchor; Death Roll channels; Warp Strike blinks behind the target; Deadly Sting names Stinger; Burrow
    Attack's aura casts the pulse; no helper has a display."""
    bad = []
    for spell_id in (*F2_COMMANDS, *F2_DAMAGE_HELPERS):
        row = rows_by_id.get(spell_id)
        extra = frozenset({EFFECT_DUMMY, EFFECT_TELEPORT_UNITS})
        if spell_id in F2_PERIODIC_TRIGGER:
            # Burrow Attack's damage is its pulse's: the command itself only carries the periodic trigger aura
            bad += [b for b in check_commanded_spell(spell_id, row, extra, frozenset({AURA_PERIODIC_TRIGGER_SPELL}))
                    if "no SCHOOL_DAMAGE" not in b]
        else:
            bad += check_commanded_spell(spell_id, row, extra)
        if row is None:
            continue
        school = 8 if spell_id in F2_NATURE_COMMANDS else 16 if spell_id in F2_FROST_COMMANDS else \
            64 if spell_id in F2_ARCANE_COMMANDS else 1
        if _i(row, "SchoolMask") != school:
            bad.append(f"{spell_id}: SchoolMask {row.get('SchoolMask')}, expected {school}")
    for command, rider in F2_TRIGGERS.items():
        row = rows_by_id.get(command) or {}
        if not any(e == EFFECT_TRIGGER_SPELL and _i(row, f"EffectTriggerSpell_{n}") == rider
                   for n, e, _ in _effects(row)):
            bad.append(f"{command}: no TRIGGER_SPELL effect casting its rider {rider}")
        helper = rows_by_id.get(rider) or {}
        if _i(helper, "SpellClassSet") or any(spell_mask(helper)) or \
                not _i(helper, "AttributesEx3") & SUPPRESS_CASTER_PROCS or _i(helper, "Attributes") & ATTR_PASSIVE:
            bad.append(f"{rider}: a rider must be a visible family-0 helper with SUPPRESS_CASTER_PROCS")
    gore = rows_by_id.get(GORE_DEBUFF) or {}
    if (_i(gore, "Effect_1"), _i(gore, "EffectAura_1"), live_value(gore, 1)) != (EFFECT_APPLY_AURA, AURA_DUMMY, 4):
        bad.append(f"{GORE_DEBUFF}: Gore's debuff must be a DUMMY aura of 4 (ruling 9, read by the C++)")
    if not _i(gore, "AttributesEx3") & ATTR3_DOT_STACKING_RULE:
        bad.append(f"{GORE_DEBUFF}: Gore's debuff needs AttributesEx3 0x80 (one copy per caster: a second hunter's "
                   f"Boar must not remove the first one's, F2 review MINOR 1)")
    root = rows_by_id.get(PINCER_CRUSH_ROOT) or {}
    if (_i(root, "Effect_1"), _i(root, "EffectAura_1")) != (EFFECT_APPLY_AURA, F2_ROOT_AURA):
        bad.append(f"{PINCER_CRUSH_ROOT}: Pincer Crush's rider must be a MOD_ROOT aura")
    for command in (*F2_CONES, *F2_AROUND_PET):
        row = rows_by_id.get(command) or {}
        want_a, want_b = (TARGET_UNIT_CONE_ENEMY, 0) if command in F2_CONES else (22, 15)
        area = [n for n, effect, _ in _effects(row) if effect == EFFECT_SCHOOL_DAMAGE and
                (_i(row, f"ImplicitTargetA_{n}"), _i(row, f"ImplicitTargetB_{n}")) == (want_a, want_b)]
        anchor = [n for n, effect, _ in _effects(row) if effect == EFFECT_DUMMY and
                  _i(row, f"ImplicitTargetA_{n}") == TARGET_UNIT_TARGET_ENEMY]
        if len(area) != 1 or len(anchor) != 1:
            bad.append(f"{command}: expected one area damage effect (TargetA/B {want_a}/{want_b}) and one DUMMY at the "
                       f"target (the falloff's primary), got {area} / {anchor}")
    for command in F2_CHANNELS:
        row = rows_by_id.get(command) or {}
        if not _i(row, "AttributesEx") & ATTR1_IS_CHANNELED or not _i(row, "DurationIndex"):
            bad.append(f"{command}: a channel needs AttributesEx 0x4 and a duration")
    warp = rows_by_id.get(201634) or {}
    if (_i(warp, "Effect_1"), _i(warp, "ImplicitTargetA_1"), _i(warp, "ImplicitTargetB_1")) != \
            (EFFECT_TELEPORT_UNITS, TARGET_UNIT_CASTER, TARGET_DEST_TARGET_BACK):
        bad.append("201634: Warp Strike's eff0 must teleport the pet behind the target (5, A 1, B 65)")
    for command, refreshed in F2_REFRESH.items():
        row = rows_by_id.get(command) or {}
        if not any(e == EFFECT_DUMMY and _i(row, f"EffectTriggerSpell_{n}") == refreshed for n, e, _ in _effects(row)):
            bad.append(f"{command}: no DUMMY naming {refreshed} (spell_hun_command_refresh)")
    for command, pulse in F2_PERIODIC_TRIGGER.items():
        row = rows_by_id.get(command) or {}
        if (_i(row, "Effect_1"), _i(row, "EffectAura_1"), _i(row, "ImplicitTargetA_1"),
                _i(row, "EffectTriggerSpell_1")) != (EFFECT_APPLY_AURA, AURA_PERIODIC_TRIGGER_SPELL, TARGET_UNIT_CASTER,
                                                     pulse):
            bad.append(f"{command}: eff0 must be a periodic trigger aura on the pet casting {pulse}")
    for helper in (GORE_DEBUFF, PINCER_CRUSH_ROOT, BURROW_ATTACK_PULSE):
        if helper in displays:
            bad.append(f"{helper}: a command helper has a COMMAND_DISPLAYS pair (it is in no kit slot)")
    return bad


def check_f2_utilities(rows_by_id: dict[int, dict], groups: list[dict], rules: list[dict]) -> list[str]:
    """(aa) unlock level, cooldown, family 9, not passive, EquippedItemClass -1, NO_AUTOCAST_AI only on Earthen
    Bulwark; TargetA 56 on the raid effects; the spell groups and the new group 1232's rule 4; Bubble Shield is an
    absorb on the hunter."""
    bad = []
    for spell_id, level in F2_LEVELS.items():
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
            continue
        if (_i(row, "SpellLevel"), _i(row, "RecoveryTime")) != (level, F2_RECOVERY[spell_id]):
            bad.append(f"{spell_id}: (SpellLevel, RecoveryTime) {(_i(row, 'SpellLevel'), _i(row, 'RecoveryTime'))}, "
                       f"expected {(level, F2_RECOVERY[spell_id])}")
        if _i(row, "SpellClassSet") != SPELLFAMILY_HUNTER or _i(row, "EquippedItemClass") != -1 or \
                _i(row, "Attributes") & ATTR_PASSIVE:
            bad.append(f"{spell_id}: family {row.get('SpellClassSet')}, EquippedItemClass "
                       f"{row.get('EquippedItemClass')}, passive {bool(_i(row, 'Attributes') & ATTR_PASSIVE)}")
        if bool(_i(row, "AttributesEx") & ATTR1_NO_AUTOCAST_AI) != (spell_id in F2_NO_AUTOCAST):
            bad.append(f"{spell_id}: AttributesEx 0x{_i(row, 'AttributesEx'):X}, NO_AUTOCAST_AI (0x20000) expected "
                       f"only on {sorted(F2_NO_AUTOCAST)}")
        if spell_id in F2_RAID_EFFECTS:
            targets = [_i(row, f"ImplicitTargetA_{n}") for n, effect, _ in _effects(row) if effect]
            if not targets or any(t != TARGET_UNIT_CASTER_AREA_RAID for t in targets):
                bad.append(f"{spell_id}: TargetA {targets}, expected 56 (CASTER_AREA_RAID) on every effect")
    declared_groups = {(int(g["id"]), int(g["spell_id"])) for g in groups}
    for spell_id, group in F2_SPELL_GROUPS.items():
        if (group, spell_id) not in declared_groups:
            bad.append(f"{spell_id}: not in spell_group {group}")
    grouped = {sid for _, sid in declared_groups} & set(F2_LEVELS)
    if grouped - set(F2_SPELL_GROUPS):
        bad.append(f"F2 utilities in an unexpected spell_group: {sorted(grouped - set(F2_SPELL_GROUPS))}")
    members = {sid for gid, sid in declared_groups if gid == SPELL_GROUP_RAID_DAMAGE_TAKEN}
    if members != RAID_DAMAGE_TAKEN_MEMBERS:
        bad.append(f"spell_group {SPELL_GROUP_RAID_DAMAGE_TAKEN} members {sorted(members)}, expected Earthen Bulwark "
                   f"201769 and (F3) Gale Barrier 202006")
    rule = {int(r["group_id"]): int(r["stack_rule"]) for r in rules}.get(SPELL_GROUP_RAID_DAMAGE_TAKEN)
    if rule != 4:
        bad.append(f"spell_group {SPELL_GROUP_RAID_DAMAGE_TAKEN}: stack rule {rule}, expected 4 (highest wins, "
                   f"ruling 7)")
    shield = rows_by_id.get(BUBBLE_SHIELD) or {}
    if (_i(shield, "Effect_1"), _i(shield, "EffectAura_1"), _i(shield, "ImplicitTargetA_1")) != \
            (EFFECT_APPLY_AURA, AURA_SCHOOL_ABSORB, TARGET_UNIT_MASTER):
        bad.append(f"{BUBBLE_SHIELD}: Bubble Shield must be a SCHOOL_ABSORB aura on the hunter (TargetA 27)")
    return bad


def check_f2_bindings(bound: list[dict]) -> list[str]:
    """(aa) each script tag is bound to exactly its F2 spells (positive keys), and no other F2 id has a binding."""
    return check_f1_bindings(bound, F2_SCRIPT_BINDINGS, F2_IDS)


def check_f2_absorb_coefficient(bonus_rows: list[dict], spell_id: int = BUBBLE_SHIELD) -> list[str]:
    """(aa) Bubble Shield's absorb scales from the pet's AP: spell_hun_pet_absorb reads spell_bonus_data.ap_bonus.
    F3 passes Swarm Shield."""
    ap = {int(r["entry"]): float(r.get("ap_bonus") or 0) for r in bonus_rows}.get(spell_id, 0.0)
    return [] if ap > 0 else [f"{spell_id}: no spell_bonus_data ap_bonus for spell_hun_pet_absorb to read"]


# (ab) hunter-pet-families F3 (F3.HANDOFF; PLAN §3.3, §4.1, §5.2): the 10 Cunning kits.
# Commanded spell or helper -> [(effect, the §3.3 number, slot, kind)] (the F1 table's shape; a splash is 50% of its
# command's number, a channel tick a third of Froststorm Breath's).
F3_POTENCY = {
    201640: [(1, 900, "I", "direct")],                              # Sonic Bite (rule 17: full potency)
    201641: [(1, 1800, "II", "direct")],                            # Shriek (rule 17)
    201642: [(1, 600, "I", "direct"), (2, 300, "I", "total")],     # Talon Rake
    201643: [(1, 1800, "II", "direct")],                            # Swoop
    201644: [(1, 1250, "I", "direct")],                             # Lightning Breath
    201645: [(1, 1450, "II", "direct")],                            # Chain Lightning
    201646: [(1, 600, "I", "direct"), (2, 650, "I", "total")],     # Fire Breath
    201647: [(1, 1450, "II", "direct")],                            # Flame Nova
    201648: [(1, 600, "I", "direct"), (2, 300, "I", "total")],     # Ravage
    201649: [(1, 1800, "II", "direct")],                            # Gut Rip
    201650: [(1, 900, "I", "total")],                               # Poison Spit
    201651: [(1, 1800, "II", "total")],                             # Constrict
    201652: [(1, 900, "I", "direct")], 201675: [(1, 450, "I", "direct")],     # Spore Burst + its 50% splash
    201653: [(1, 1800, "II", "total")], 201674: [(1, 900, "II", "total")],    # Fungal Bloom + its 50% splash
    201654: [(1, 900, "I", "direct")],                              # Nether Shock
    201655: [(1, 1800, "II", "direct")],                            # Nether Lash
    201656: [(1, 600, "I", "direct")], 201670: [(1, 650, "I", "direct")],     # Twin Bite: Frost + Nature bite
    201671: [(1, 1850 / 3, "II", "direct")],                        # Froststorm Breath's tick (3 per channel)
    201658: [(1, 1250, "I", "total")],                              # Venom Web Spray
    201659: [(1, 1450, "II", "direct")],                            # Swarm Spit
}
F3_COMMANDS = tuple(range(201640, 201660))
TWIN_BITE_NATURE, FROSTSTORM_TICK, CONSTRICT_ROOT, VENOM_WEB_SPRAY_ROOT, FUNGAL_BLOOM_SPLASH, SPORE_BURST_SPLASH = \
    201670, 201671, 201672, 201673, 201674, 201675
F3_DAMAGE_HELPERS = (TWIN_BITE_NATURE, FROSTSTORM_TICK, FUNGAL_BLOOM_SPLASH, SPORE_BURST_SPLASH)
F3_SCHOOLS = {   # SchoolMask; every other command or helper is Physical (F1 decision 2)
    **{i: 8 for i in (201644, 201645, 201650, 201652, 201653, 201658, 201659, 201670, 201674, 201675)},     # Nature
    **{i: 4 for i in (201646, 201647)},                                                                    # Fire
    **{i: 64 for i in (201654, 201655)},                                                                   # Arcane
    **{i: 16 for i in (201656, 201657, 201671)},                                                           # Frost
}
F3_MELEE = frozenset({201641, 201657})          # the two cones start at the pet: melee reach (RangeIndex 2)
F3_CONES = (201641, FROSTSTORM_TICK)            # cone damage (TargetA 104) + DUMMY anchor at the target
F3_AT_TARGET = (201647, 201659)                 # area at the target (TargetA 53 / B 16)
F3_SPLASHES = {201652: SPORE_BURST_SPLASH, 201653: FUNGAL_BLOOM_SPLASH}       # command -> its 50% splash
F3_ROOTS = {201651: CONSTRICT_ROOT, 201658: VENOM_WEB_SPRAY_ROOT}             # command -> its root rider
F3_CHAINS = {201640: (2, 0.5), 201645: (3, 1.0)}   # Sonic Bite's bounce (rule 17), Chain Lightning (ruling 6, falloff)
F3_MULTIHIT = {201656: (TWIN_BITE_NATURE, 1)}
F3_CHANNEL = {201657: FROSTSTORM_TICK}
EFFECT_DISPEL = 38
EFFECT_DISPEL_MECHANIC = 108
AURA_MOD_DAMAGE_PERCENT_TAKEN = 87
F3_LEVELS = {201771: 14, 201772: 40, 201773: 32, 201774: 32, 201775: 10, 201776: 26, 201777: 26, 201778: 26,
             201779: 26, 201780: 10, 202004: 16, 202005: 18, 202006: 30, 202007: 30, 202008: 30, 202009: 30,
             202010: 30, 202011: 16, 202012: 10, 202013: 10}
F3_RECOVERY = {201771: 10000, 201772: 40000, 201773: 10000, 201774: 10000, 201775: 10000, 201776: 10000,
               201777: 40000, 201778: 40000, 201779: 40000, 201780: 40000, 202004: 30000, 202005: 60000,
               202006: 60000, 202007: 60000, 202008: 60000, 202009: 60000, 202010: 60000, 202011: 30000,
               202012: 60000, 202013: 60000}
F3_RAID_EFFECTS = frozenset({201772, 201777, 201778, 201779, 201780, 202006, 202010})    # every effect TargetA 56
F3_NO_AUTOCAST = frozenset({202006})            # Gale Barrier: a raid cooldown (F1 review MINOR 2)
F3_SPELL_GROUPS = {201771: 1062, 201772: 1036, 201773: 1101, 201774: 1101, 201775: 1015, 201776: 1096,
                   201779: 1048, 201780: 1084, 202006: SPELL_GROUP_RAID_DAMAGE_TAKEN,
                   201777: 1233, 201778: 1233}
# F3 review MAJOR 1: aura 65 limits itself only through a rule 3 group, so the pet spell haste buffs, Fire Attunement
# 202209 and Wrath of Air 2895 share the new group 1233
SPELL_GROUP_SPELL_HASTE = 1233
SPELL_HASTE_MEMBERS = frozenset({201777, 201778, 202209, 2895})
GALE_BARRIER, EARTHEN_BULWARK, SWARM_SHIELD, SHED_SKIN, SHED_SKIN_HEAL = 202006, 201769, 202013, 202009, 202032
F3_SCRIPT_BINDINGS = {
    201641: {"spell_hun_command_aoe_falloff"}, 201645: {"spell_hun_command_aoe_falloff"},
    201647: {"spell_hun_command_aoe_falloff"}, FROSTSTORM_TICK: {"spell_hun_command_aoe_falloff"},
    201659: {"spell_hun_command_aoe_falloff"},
    201656: {"spell_hun_command_multihit"}, 201657: {"spell_hun_command_pulse"},
    SPORE_BURST_SPLASH: {"spell_hun_command_splash"}, FUNGAL_BLOOM_SPLASH: {"spell_hun_command_splash"},
    202005: {"spell_hun_pet_control_boss_filter"}, 202007: {"spell_hun_pet_control_boss_filter"},
    202012: {"spell_hun_pet_control_boss_filter"}, CONSTRICT_ROOT: {"spell_hun_pet_control_boss_filter"},
    VENOM_WEB_SPRAY_ROOT: {"spell_hun_pet_control_boss_filter"},
    SWARM_SHIELD: {"spell_hun_pet_absorb"},
}
F3_IDS = frozenset({*F3_COMMANDS, *range(201670, 201676), *range(201771, 201781), *range(202004, 202014),
                    SHED_SKIN_HEAL, *range(202143, 202163)})


def _float(row: dict, key: str) -> float:
    return float(row.get(key) or 0)


def check_f3_commands(rows_by_id: dict[int, dict], displays: dict[int, int]) -> list[str]:
    """(ab) the commands and the damage helpers are commanded-spell carriers with their schools and DmgClass (RANGED
    at 30 yd, the two cones melee); the cones and the areas at the target keep their shape; the root riders are
    family-0 helpers cast by TRIGGER_SPELL; the splashes are area helpers the command triggers; Sonic Bite and Chain
    Lightning chain; Twin Bite names its Nature bite; Froststorm Breath channels its cone tick; no helper has a
    display."""
    bad = []
    for spell_id in (*F3_COMMANDS, *F3_DAMAGE_HELPERS):
        row = rows_by_id.get(spell_id)
        problems = check_commanded_spell(spell_id, row, frozenset({EFFECT_DUMMY}),
                                         frozenset({AURA_PERIODIC_TRIGGER_SPELL}),
                                         ranged=spell_id not in F3_MELEE)
        if spell_id in F3_CHANNEL:
            # Froststorm Breath's damage is its tick's: the channel itself only carries the periodic trigger aura
            problems = [b for b in problems if "no SCHOOL_DAMAGE" not in b]
        bad += problems
        if row is None:
            continue
        school = F3_SCHOOLS.get(spell_id, 1)
        if _i(row, "SchoolMask") != school:
            bad.append(f"{spell_id}: SchoolMask {row.get('SchoolMask')}, expected {school}")
        if spell_id in F3_COMMANDS and (_i(row, "RangeIndex") == 2) != (spell_id in F3_MELEE):
            bad.append(f"{spell_id}: RangeIndex {row.get('RangeIndex')}, expected "
                       f"{'2 (melee: a cone starts at the pet)' if spell_id in F3_MELEE else 'a 30 yd range'}")
    for command in F3_CONES:
        row = rows_by_id.get(command) or {}
        cone = [n for n, effect, _ in _effects(row) if effect == EFFECT_SCHOOL_DAMAGE and
                _i(row, f"ImplicitTargetA_{n}") == TARGET_UNIT_CONE_ENEMY]
        anchor = [n for n, effect, _ in _effects(row) if effect == EFFECT_DUMMY and
                  _i(row, f"ImplicitTargetA_{n}") == TARGET_UNIT_TARGET_ENEMY]
        if len(cone) != 1 or len(anchor) != 1:
            bad.append(f"{command}: expected one cone damage effect (TargetA 104) and one DUMMY at the target (the "
                       f"falloff's primary), got {cone} / {anchor}")
    for spell_id in (*F3_AT_TARGET, *F3_SPLASHES.values()):
        row = rows_by_id.get(spell_id) or {}
        if (_i(row, "ImplicitTargetA_1"), _i(row, "ImplicitTargetB_1")) != (53, 16):
            bad.append(f"{spell_id}: eff0 must hit the area at the target (TargetA 53 / B 16)")
    for command, helper in {**F3_SPLASHES, **F3_ROOTS}.items():
        row = rows_by_id.get(command) or {}
        if not any(e == EFFECT_TRIGGER_SPELL and _i(row, f"EffectTriggerSpell_{n}") == helper
                   for n, e, _ in _effects(row)):
            bad.append(f"{command}: no TRIGGER_SPELL effect casting {helper}")
    for root in F3_ROOTS.values():
        helper = rows_by_id.get(root) or {}
        if (_i(helper, "Effect_1"), _i(helper, "EffectAura_1")) != (EFFECT_APPLY_AURA, F2_ROOT_AURA) or \
                _i(helper, "SpellClassSet") or any(spell_mask(helper)) or \
                not _i(helper, "AttributesEx3") & SUPPRESS_CASTER_PROCS or _i(helper, "Attributes") & ATTR_PASSIVE:
            bad.append(f"{root}: a root rider must be a visible family-0 MOD_ROOT helper with SUPPRESS_CASTER_PROCS")
    for command, (targets, amplitude) in F3_CHAINS.items():
        row = rows_by_id.get(command) or {}
        got = (_i(row, "EffectChainTargets_1"), round(_float(row, "EffectChainAmplitude_1"), 3))
        if got != (targets, amplitude):
            bad.append(f"{command}: chain (targets, amplitude) {got}, expected {(targets, amplitude)}")
    for command, (strike, follow_ups) in F3_MULTIHIT.items():
        row = rows_by_id.get(command) or {}
        dummies = [n for n, effect, _ in _effects(row) if effect == EFFECT_DUMMY]
        if len(dummies) != 1 or _i(row, f"EffectTriggerSpell_{dummies[0]}") != strike or \
                live_value(row, dummies[0]) != follow_ups:
            bad.append(f"{command}: expected one DUMMY naming strike {strike} with value {follow_ups} (the follow-ups)")
        helper = rows_by_id.get(strike) or {}
        if not _i(helper, "AttributesEx3") & SUPPRESS_CASTER_PROCS:
            bad.append(f"{strike}: a follow-up strike without SUPPRESS_CASTER_PROCS")
    for command, tick in F3_CHANNEL.items():
        row = rows_by_id.get(command) or {}
        if not _i(row, "AttributesEx") & ATTR1_IS_CHANNELED or not _i(row, "DurationIndex"):
            bad.append(f"{command}: a channel needs AttributesEx 0x4 and a duration")
        if (_i(row, "Effect_1"), _i(row, "EffectAura_1"), _i(row, "ImplicitTargetA_1"),
                _i(row, "EffectTriggerSpell_1")) != (EFFECT_APPLY_AURA, AURA_PERIODIC_TRIGGER_SPELL, TARGET_UNIT_CASTER,
                                                     tick):
            bad.append(f"{command}: eff0 must be a periodic trigger aura on the pet casting {tick}")
        if (_i(row, "Effect_2"), _i(row, "ImplicitTargetA_2")) != (EFFECT_DUMMY, TARGET_UNIT_TARGET_ENEMY):
            bad.append(f"{command}: eff1 must be the DUMMY anchor at the target (the pulse's stashed primary)")
    for helper in (*F3_DAMAGE_HELPERS, *F3_ROOTS.values()):
        if helper in displays:
            bad.append(f"{helper}: a command helper has a COMMAND_DISPLAYS pair (it is in no kit slot)")
    return bad


def check_f3_utilities(rows_by_id: dict[int, dict], groups: list[dict], rules: list[dict]) -> list[str]:
    """(ab) unlock level, cooldown, family 9, not passive, EquippedItemClass -1, NO_AUTOCAST_AI only on Gale Barrier;
    TargetA 56 on the raid effects; the spell groups; Gale Barrier is one aura 87 effect like Earthen Bulwark (group
    1232 compares within one aura type); Swarm Shield is an absorb on the hunter; Shed Skin cleanses roots and snares
    and triggers its poison cleanse + heal; group 1233 holds the four aura 65 spells under rule 3 (only the highest
    applies; review MAJOR 1)."""
    bad = []
    for spell_id, level in F3_LEVELS.items():
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
            continue
        if (_i(row, "SpellLevel"), _i(row, "RecoveryTime")) != (level, F3_RECOVERY[spell_id]):
            bad.append(f"{spell_id}: (SpellLevel, RecoveryTime) {(_i(row, 'SpellLevel'), _i(row, 'RecoveryTime'))}, "
                       f"expected {(level, F3_RECOVERY[spell_id])}")
        if _i(row, "SpellClassSet") != SPELLFAMILY_HUNTER or _i(row, "EquippedItemClass") != -1 or \
                _i(row, "Attributes") & ATTR_PASSIVE:
            bad.append(f"{spell_id}: family {row.get('SpellClassSet')}, EquippedItemClass "
                       f"{row.get('EquippedItemClass')}, passive {bool(_i(row, 'Attributes') & ATTR_PASSIVE)}")
        if bool(_i(row, "AttributesEx") & ATTR1_NO_AUTOCAST_AI) != (spell_id in F3_NO_AUTOCAST):
            bad.append(f"{spell_id}: AttributesEx 0x{_i(row, 'AttributesEx'):X}, NO_AUTOCAST_AI (0x20000) expected "
                       f"only on {sorted(F3_NO_AUTOCAST)}")
        if spell_id in F3_RAID_EFFECTS:
            targets = [_i(row, f"ImplicitTargetA_{n}") for n, effect, _ in _effects(row) if effect]
            if not targets or any(t != TARGET_UNIT_CASTER_AREA_RAID for t in targets):
                bad.append(f"{spell_id}: TargetA {targets}, expected 56 (CASTER_AREA_RAID) on every effect")
    declared_groups = {(int(g["id"]), int(g["spell_id"])) for g in groups}
    for spell_id, group in F3_SPELL_GROUPS.items():
        if (group, spell_id) not in declared_groups:
            bad.append(f"{spell_id}: not in spell_group {group}")
    grouped = {sid for _, sid in declared_groups} & set(F3_LEVELS)
    if grouped - set(F3_SPELL_GROUPS):
        bad.append(f"F3 utilities in an unexpected spell_group: {sorted(grouped - set(F3_SPELL_GROUPS))}")
    haste = {sid for gid, sid in declared_groups if gid == SPELL_GROUP_SPELL_HASTE}
    if haste != SPELL_HASTE_MEMBERS:
        bad.append(f"spell_group {SPELL_GROUP_SPELL_HASTE} members {sorted(haste)}, expected "
                   f"{sorted(SPELL_HASTE_MEMBERS)} (the aura 65 spell haste buffs)")
    rule = {int(x["group_id"]): int(x["stack_rule"]) for x in rules}.get(SPELL_GROUP_SPELL_HASTE)
    if rule != 3:
        bad.append(f"spell_group {SPELL_GROUP_SPELL_HASTE}: stack rule {rule}, expected 3 (aura 65 keeps only the "
                   f"highest through a same-effect group)")
    gale, bulwark = rows_by_id.get(GALE_BARRIER) or {}, rows_by_id.get(EARTHEN_BULWARK) or {}
    gale_effects = [(e, a) for _, e, a in _effects(gale) if e]
    if gale_effects != [(EFFECT_APPLY_AURA, AURA_MOD_DAMAGE_PERCENT_TAKEN)] or \
            _i(bulwark, "EffectAura_1") != AURA_MOD_DAMAGE_PERCENT_TAKEN:
        bad.append(f"{GALE_BARRIER}: Gale Barrier must be one aura 87 effect, Earthen Bulwark's aura type (group 1232 "
                   f"compares within one aura type, then the effect count), got {gale_effects}")
    shield = rows_by_id.get(SWARM_SHIELD) or {}
    if (_i(shield, "Effect_1"), _i(shield, "EffectAura_1"), _i(shield, "ImplicitTargetA_1")) != \
            (EFFECT_APPLY_AURA, AURA_SCHOOL_ABSORB, TARGET_UNIT_MASTER):
        bad.append(f"{SWARM_SHIELD}: Swarm Shield must be a SCHOOL_ABSORB aura on the hunter (TargetA 27)")
    shed, heal = rows_by_id.get(SHED_SKIN) or {}, rows_by_id.get(SHED_SKIN_HEAL) or {}
    got = [(_i(shed, f"Effect_{n}"), _i(shed, f"EffectMiscValue_{n}"), _i(shed, f"EffectTriggerSpell_{n}"))
           for n in (1, 2, 3)]
    if got != [(EFFECT_DISPEL_MECHANIC, 7, 0), (EFFECT_DISPEL_MECHANIC, 11, 0), (EFFECT_TRIGGER_SPELL, 0,
                                                                                 SHED_SKIN_HEAL)]:
        bad.append(f"{SHED_SKIN}: expected DISPEL_MECHANIC root, DISPEL_MECHANIC snare, TRIGGER_SPELL "
                   f"{SHED_SKIN_HEAL}, got {got}")
    if [(_i(heal, "Effect_1"), _i(heal, "EffectMiscValue_1")), (_i(heal, "Effect_2"), _i(heal, "EffectBasePoints_2"))] \
            != [(EFFECT_DISPEL, 4), (EFFECT_HEAL_PCT, 19)] or _i(heal, "SpellClassSet"):
        bad.append(f"{SHED_SKIN_HEAL}: expected a family-0 DISPEL Poison + HEAL_PCT 20%")
    return bad


def check_f3_bindings(bound: list[dict]) -> list[str]:
    """(ab) each script tag is bound to exactly its F3 spells (positive keys), and no other F3 id has a binding."""
    return check_f1_bindings(bound, F3_SCRIPT_BINDINGS, F3_IDS)


# (ad) hunter-pet-families PLAN §11 ruling 24 (user 2026-11-13): pet type identity. Single-target Ferocity command
# damage x1.07, single-target Cunning command damage x0.94 (on top of ruling 23), and the pet's own Beast Cleave copy
# share by type (Ferocity x0.93, Tenacity x1.0, Cunning x1.74). Pinned independently of _pet_kits.py and
# hunter_bm_spells.py.
R24_FEROCITY_ST_SCALE = 1.07
R24_BEAST_CLEAVE_PET_SCALES = {
    "BEAST_CLEAVE_PET_FEROCITY_SCALE": 0.93,
    "BEAST_CLEAVE_PET_TENACITY_SCALE": 1.0,
    "BEAST_CLEAVE_PET_CUNNING_SCALE": 1.74,
}
FEROCITY_FAMILIES = frozenset({1, 2, 7, 11, 12, 25, 37, 39, 44, 45, 46})   # Wolf, Cat, Raptor + the eight F1 kits
TENACITY_FAMILIES_R24 = frozenset({4, 5, 6, 8, 9, 20, 21, 32, 42, 43})       # Bear + the nine F2 kits (unchanged)
# "Single-target" = a damage spell of a command Beast Cleave copies (Hunter::IsBeastCleaveExcluded: no area / chain
# > 1 effect, no TRIGGER_SPELL into an area), plus that command's non-area damage helpers (multi-hit strikes, a second
# bite).
R24_FEROCITY_ST_IDS = frozenset({
    201720, 201721, 201722, 201723, 201724,         # Wolf Lunge / Rip Throat, Cat Rake / Pounce, Raptor Savage Rend
    201730, 201731,                                 # the Ferocity type defaults
    201606, 201607, 201608, 201609, 201660, 201610, 201611, 201612, 201614, 201615, 201661, 201616, 201617,
    201619, 201662, 201620, 201621,                 # F1 (Dazzling Wings 201613 and Lava Breath 201618 are AoE)
})
R24_CUNNING_ST_IDS = frozenset({
    201728, 201734, 201735,                         # Spider's Venom Bite, the Cunning type defaults
    201642, 201643, 201644, 201646, 201648, 201649, 201650, 201651, 201654, 201655, 201656, 201670, 201658,
})
R24_AOE_IDS = frozenset({                           # never scaled by ruling 24
    201725, 201613, 201618,                         # Ferocity: Leaping Tear, Dazzling Wings, Lava Breath
    201729, 201736, 201640, 201641, 201645, 201647, 201652, 201675, 201653, 201674, 201657, 201671, 201659,
})
# Wolf / Cat / Raptor and the type defaults: literal balance-pass numbers (the check_ruling_23_potency shape)
R24_POTENCY = {
    201720: [(2, 302.4, "direct", R24_FEROCITY_ST_SCALE)],                                     # Lunge (eff1 jump)
    201721: [(1, 552.5, "direct", R24_FEROCITY_ST_SCALE)],                                     # Rip Throat
    201722: [(1, 168.0, "direct", R24_FEROCITY_ST_SCALE), (2, 252.0, "total", R24_FEROCITY_ST_SCALE)],   # Rake
    201723: [(1, 520.0, "direct", R24_FEROCITY_ST_SCALE)],                                     # Pounce
    201724: [(1, 378.0, "direct", R24_FEROCITY_ST_SCALE)],                                     # Savage Rend
    201730: [(1, 336.0, "direct", R24_FEROCITY_ST_SCALE)],                                     # Savage Strikes
    201731: [(1, 650.0, "direct", R24_FEROCITY_ST_SCALE)],                                     # Savage Pounce
    201725: [(1, 585.0, "direct", 1.0)],                                                       # Leaping Tear (AoE)
}
# the Beast Cleave talent's ruling 24 line: 50% x 0.93 / 1.0 / 1.74
R24_TOOLTIP = {201848: (["Your pet's share depends on its type: Ferocity 46.5%, Tenacity 50%, Cunning 87%."], [])}


def _has_area_effect(row: dict) -> bool:
    """HunterMechanics.cpp HasAreaEffect: an effect with a radius or a chain of more than one target."""
    return any(effect and (_i(row, f"EffectRadiusIndex_{n}") or _i(row, f"EffectChainTargets_{n}") > 1)
               for n, effect, _ in _effects(row))


def _deals_damage(row: dict) -> bool:
    return any(effect == EFFECT_SCHOOL_DAMAGE or (effect == EFFECT_APPLY_AURA and aura == AURA_PERIODIC_DAMAGE)
               for _, effect, aura in _effects(row))


def _triggered(row: dict) -> list[tuple[int, int]]:
    """(effect or aura kind, triggered id) of every TRIGGER_SPELL, follow-up DUMMY and periodic-trigger effect."""
    out = []
    for n, effect, aura in _effects(row):
        trigger = _i(row, f"EffectTriggerSpell_{n}")
        if trigger and (effect in (EFFECT_TRIGGER_SPELL, EFFECT_DUMMY) or aura == AURA_PERIODIC_TRIGGER_SPELL):
            out.append((effect, trigger))
    return out


def classify_single_target(commands: list[int], rows_by_id: dict[int, dict]) -> tuple[set[int], set[int]]:
    """(ad) (single-target damage spells, AoE damage spells) of `commands` and their damage helpers. A command is AoE
    when it has an area effect or triggers an area spell (a TRIGGER_SPELL, as IsBeastCleaveExcluded checks, or the
    tick of a channel / pulse, whose command deals no damage itself); its helpers follow it, and an area helper is
    always AoE."""
    single, area = set(), set()
    for command in commands:
        row = rows_by_id.get(command) or {}
        helpers = [(kind, rows_by_id.get(t) or {}, t) for kind, t in _triggered(row)]
        aoe = _has_area_effect(row) or any(_has_area_effect(h) for _, h, _ in helpers)
        for spell_id, spell_row in [(command, row), *((t, h) for _, h, t in helpers)]:
            if _deals_damage(spell_row):
                (area if aoe or _has_area_effect(spell_row) else single).add(spell_id)
    return single, area


def check_ruling_24_classification(kits: dict[int, dict], defaults: dict[str, dict], rows_by_id: dict[int, dict],
                                   families: frozenset, default: str, expected_st: frozenset,
                                   expected_aoe: frozenset = R24_AOE_IDS) -> list[str]:
    """(ad) the single-target set the C++ rule gives for one type's kits (and its type default) is the pinned one, and
    no pinned AoE spell reads as single-target."""
    commands = [kits[f][slot] for f in sorted(families) if f in kits for slot in ("commandI", "commandII")]
    commands += [defaults.get(default, {}).get(slot, 0) for slot in ("commandI", "commandII")]
    single, _ = classify_single_target([c for c in commands if c], rows_by_id)
    bad = [f"{sid}: single-target by the Beast Cleave rule but not pinned" for sid in sorted(single - expected_st)]
    bad += [f"{sid}: pinned single-target but the Beast Cleave rule disagrees" for sid in sorted(expected_st - single)]
    bad += [f"{sid}: pinned AoE but single-target by the rule" for sid in sorted(single & expected_aoe)]
    return bad


def check_beast_cleave_type_scales(consts: dict, hunter_data_h: str, cpp: str,
                                   expected: dict = R24_BEAST_CLEAVE_PET_SCALES) -> list[str]:
    """(ad) the three Beast Cleave type multipliers: declared const() values, emitted into HunterData.h, read by
    spell_hun_beast_cleave for the pet only (PassthroughKind::Pet)."""
    bad = []
    header = {m.group(1): float(m.group(2))
              for m in re.finditer(r"constexpr\s+float\s+(\w+)\s*=\s*([\d.]+)f\s*;", hunter_data_h)}
    for name, value in expected.items():
        if consts.get(name) is None or abs(float(consts[name]) - value) > 1e-9:
            bad.append(f"{name}: const {consts.get(name)}, expected {value}")
        if header.get(name) is None or abs(header[name] - value) > 1e-6:
            bad.append(f"{name}: HunterData.h has {header.get(name)}, expected {value}")
        if f"HunterData::{name}" not in cpp:
            bad.append(f"{name}: spell_hunter_beast_mastery.cpp never reads it")
    if "PassthroughKind::Pet" not in cpp:
        bad.append("spell_hunter_beast_mastery.cpp: the type scale is not limited to the pet")
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
        # TUNE3: ap_potency 44.1 (pass 1031: was 49; TUNE1 70, was 100), so the coefficient is 0.441 * (1.5 / 3.5)
        self.assertAlmostEqual(bonus[0]["ap_bonus"], 0.441 * 1.5 / 3.5, places=4)

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
        cpp, header = HUNTER_MECHANICS_CPP.read_text(encoding="utf-8"), HUNTER_DATA_H.read_text(encoding="utf-8")
        slots = parse_kit_slots(cpp, header)
        displays, unresolved = parse_command_displays(cpp, header)
        self.assertEqual(unresolved, [])
        # the 16 pairs F0 moved into the table are still the offset's
        self.assertEqual({c: d for c, d in displays.items() if c in COMMANDED_SLOTTED},
                         {c: c + offset for c in COMMANDED_SLOTTED})
        self.assertClean(check_command_displays(data["rows_by_id"], displays, slots, package.spell_script_names,
                                                package.talents, package.trainer_spells))

    # (v) hunter-pet-families F0
    def test_family_kit_table(self):
        cpp, header = HUNTER_MECHANICS_CPP.read_text(encoding="utf-8"), HUNTER_DATA_H.read_text(encoding="utf-8")
        kits, defaults, unresolved = parse_kits(cpp, header)
        displays, _ = parse_command_displays(cpp, header)
        self.assertEqual(len(kits), 32)
        self.assertClean(check_family_kits(kits, defaults, unresolved, displays, package_data()["rows_by_id"]))

    # (w)
    def test_f0_utilities(self):
        data = package_data()
        self.assertClean(check_f0_utilities(data["rows_by_id"], data["package"].spell_groups))

    # (x)
    def test_mobility_and_the_pet_utility_group(self):
        data = package_data()
        self.assertClean(check_mobility(data["rows_by_id"], data["rows"]))

    # (y) ruling 19: Swipe x500/600 (504 -> 420 on both effects), Maul x1100/1000 (650 -> 715). Instant pet commands
    # share one time basis, so ap_bonus is proportional to the authored potency (Rip Throat 552.5 as the yardstick).
    def test_bear_retrofit(self):
        package = package_data()["package"]
        bonus = {int(r["entry"]): r["ap_bonus"] for r in package.spell_bonus_data}
        # ruling 23b: x0.80 on top of the ruling 19 numbers; the reference Rip Throat took ruling 24's Ferocity x1.07
        rip_throat = 552.5 * R24_FEROCITY_ST_SCALE
        self.assertAlmostEqual(bonus[201726] / bonus[201721], 420.0 * R23B_TENACITY_SCALE / rip_throat, places=6)
        self.assertAlmostEqual(bonus[201727] / bonus[201721], 715.0 * R23B_TENACITY_SCALE / rip_throat, places=6)
        swipe = {r["ScriptName"] for r in package.spell_script_names if int(r["spell_id"]) == 201726}
        self.assertEqual(swipe, {"spell_hun_command_splash", "spell_hun_command_aoe_falloff"})
        self.assertEqual(_consts(package)["COMMAND_AOE_FALLOFF_PCT"], 50)

    def test_tooltip_texts_t1_t16_pt2(self):
        self.assertClean(check_tooltip_texts(package_data()["rows_by_id"]))

    # (z) hunter-pet-families F1
    def test_f1_command_potency_is_the_ruling_1_scale(self):
        entries = {int(e["id"]): e for e in package_data()["package"].spells}
        # ruling 24: the single-target F1 commands and helpers x1.07, the two AoE commands untouched
        self.assertClean(check_f1_potency(entries, id_scales=dict.fromkeys(R24_FEROCITY_ST_IDS,
                                                                           R24_FEROCITY_ST_SCALE)))

    def test_f1_commands_and_helpers(self):
        cpp, header = HUNTER_MECHANICS_CPP.read_text(encoding="utf-8"), HUNTER_DATA_H.read_text(encoding="utf-8")
        displays, unresolved = parse_command_displays(cpp, header)
        self.assertEqual(unresolved, [])
        self.assertTrue(set(F1_COMMANDS) <= set(displays), "every F1 command has a COMMAND_DISPLAYS pair")
        self.assertEqual(sorted(displays[c] for c in F1_COMMANDS), list(range(202109, 202125)))
        self.assertClean(check_f1_commands(package_data()["rows_by_id"], displays))

    def test_f1_utilities(self):
        data = package_data()
        self.assertClean(check_f1_utilities(data["rows_by_id"], data["package"].spell_groups))

    def test_f1_script_bindings(self):
        self.assertClean(check_f1_bindings(package_data()["package"].spell_script_names))


    # (aa) hunter-pet-families F2
    def test_f2_command_potency_is_the_ruling_1_scale(self):
        entries = {int(e["id"]): e for e in package_data()["package"].spells}
        self.assertClean(check_f1_potency(entries, F2_POTENCY, R23B_TENACITY_SCALE))

    def test_f2_commands_and_helpers(self):
        cpp, header = HUNTER_MECHANICS_CPP.read_text(encoding="utf-8"), HUNTER_DATA_H.read_text(encoding="utf-8")
        displays, unresolved = parse_command_displays(cpp, header)
        self.assertEqual(unresolved, [])
        self.assertTrue(set(F2_COMMANDS) <= set(displays), "every F2 command has a COMMAND_DISPLAYS pair")
        self.assertEqual(sorted(displays[c] for c in F2_COMMANDS), list(range(202125, 202143)))
        self.assertClean(check_f2_commands(package_data()["rows_by_id"], displays))

    def test_f2_utilities(self):
        package = package_data()["package"]
        self.assertClean(check_f2_utilities(package_data()["rows_by_id"], package.spell_groups,
                                            package.spell_group_rules))
        self.assertClean(check_f2_absorb_coefficient(package.spell_bonus_data))

    def test_f2_script_bindings(self):
        self.assertClean(check_f2_bindings(package_data()["package"].spell_script_names))

    # (ab) hunter-pet-families F3
    def test_f3_command_potency_is_the_ruling_1_scale(self):
        entries = {int(e["id"]): e for e in package_data()["package"].spells}
        # ruling 24: the single-target F3 commands and helpers a further x0.94
        self.assertClean(check_f1_potency(entries, F3_POTENCY, R23_CUNNING_SCALE,
                                          dict.fromkeys(R24_CUNNING_ST_IDS, R24_CUNNING_ST_SCALE)))

    # (ac) ruling 23
    def test_ruling_23_type_scales(self):
        entries = {int(e["id"]): e for e in package_data()["package"].spells}
        self.assertClean(check_ruling_23_potency(entries))
        # no Cunning family kept a Ferocity / Tenacity basic (they would be scaled x1.5, not x0.39)
        cpp, header = HUNTER_MECHANICS_CPP.read_text(encoding="utf-8"), HUNTER_DATA_H.read_text(encoding="utf-8")
        kits, _, unresolved = parse_kits(cpp, header)
        self.assertEqual(unresolved, [])
        cunning_basics = {kits[f]["basic"] for f in kits if f in CUNNING_FAMILIES}
        self.assertEqual(cunning_basics, {201710, 201711})
        self.assertFalse(cunning_basics & {17253, 16827, 49966})
        other_basics = {kits[f]["basic"] for f in kits if f not in CUNNING_FAMILIES}
        self.assertEqual(other_basics, {17253, 16827, 49966})


    # (ad) ruling 24
    def test_ruling_24_classification(self):
        cpp, header = HUNTER_MECHANICS_CPP.read_text(encoding="utf-8"), HUNTER_DATA_H.read_text(encoding="utf-8")
        kits, defaults, unresolved = parse_kits(cpp, header)
        self.assertEqual(unresolved, [])
        rows = package_data()["rows_by_id"]
        self.assertClean(check_ruling_24_classification(kits, defaults, rows, FEROCITY_FAMILIES,
                                                        "KIT_FEROCITY_DEFAULT", R24_FEROCITY_ST_IDS))
        self.assertClean(check_ruling_24_classification(kits, defaults, rows, CUNNING_FAMILIES,
                                                        "KIT_CUNNING_DEFAULT", R24_CUNNING_ST_IDS))
        self.assertEqual(set(kits), FEROCITY_FAMILIES | CUNNING_FAMILIES | TENACITY_FAMILIES_R24)

    def test_ruling_24_potency(self):
        entries = {int(e["id"]): e for e in package_data()["package"].spells}
        self.assertClean(check_ruling_23_potency(entries, R24_POTENCY))
        # every pinned single-target spell is covered by a potency table that applies its scale
        covered = set(F1_POTENCY) | set(F3_POTENCY) | set(R23_POTENCY) | set(R24_POTENCY)
        self.assertEqual((R24_FEROCITY_ST_IDS | R24_CUNNING_ST_IDS) - covered, set())

    def test_ruling_24_beast_cleave(self):
        package = package_data()["package"]
        cpp = BM_SCRIPT_CPP.read_text(encoding="utf-8")
        self.assertClean(check_beast_cleave_type_scales(_consts(package), HUNTER_DATA_H.read_text(encoding="utf-8"),
                                                        cpp))
        self.assertClean(check_tooltip_texts(package_data()["rows_by_id"], R24_TOOLTIP))
    def test_f3_commands_and_helpers(self):
        cpp, header = HUNTER_MECHANICS_CPP.read_text(encoding="utf-8"), HUNTER_DATA_H.read_text(encoding="utf-8")
        displays, unresolved = parse_command_displays(cpp, header)
        self.assertEqual(unresolved, [])
        self.assertTrue(set(F3_COMMANDS) <= set(displays), "every F3 command has a COMMAND_DISPLAYS pair")
        self.assertEqual(sorted(displays[c] for c in F3_COMMANDS), list(range(202143, 202163)))
        self.assertClean(check_f3_commands(package_data()["rows_by_id"], displays))

    def test_f3_utilities(self):
        package = package_data()["package"]
        self.assertClean(check_f3_utilities(package_data()["rows_by_id"], package.spell_groups,
                                            package.spell_group_rules))
        self.assertClean(check_f2_absorb_coefficient(package.spell_bonus_data, SWARM_SHIELD))

    def test_f3_script_bindings(self):
        self.assertClean(check_f3_bindings(package_data()["package"].spell_script_names))

    def test_f3_no_family_uses_a_type_default_command(self):
        # Since F3 every family has its own commands; 201730-201735 stay only as the unknown-family fallback.
        cpp, header = HUNTER_MECHANICS_CPP.read_text(encoding="utf-8"), HUNTER_DATA_H.read_text(encoding="utf-8")
        kits, _, unresolved = parse_kits(cpp, header)
        self.assertEqual(unresolved, [])
        defaults = set(range(201730, 201736))
        self.assertEqual({f: (k["commandI"], k["commandII"]) for f, k in kits.items()
                          if {k["commandI"], k["commandII"]} & defaults}, {})

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

        def table(*rows):
            return "constexpr std::array<FamilyKit, 2> FAMILY_KITS =\n{{\n" + "\n".join(rows) + "\n}};\n"

        row1 = "    // Wolf\n    { 1, { SPELL_BITE, 0, 0, SPELL_A_COMMAND,\n        SPELL_B_COMMAND, PET_KIT_GROUP_AUTOCAST } },"
        self.assertEqual(parse_kit_slots(table(row1), header), {201720: "I", 201721: "II"})
        kits, defaults, unresolved = parse_kits(table(row1), header)
        self.assertEqual(kits, {1: {"basic": 17253, "group": 0, "utility": 0, "commandI": 201720,
                                    "commandII": 201721, "flags": 1}})
        self.assertEqual((defaults, unresolved), ({}, []))
        swapped = table(row1, "    { 2, { SPELL_BITE, 0, 0, SPELL_B_COMMAND, SPELL_A_COMMAND, 0 } },")
        self.assertEqual(parse_kit_slots(swapped, header), {201720: "both", 201721: "both"})
        unknown = table(row1) + "constexpr PetKit KIT_X_DEFAULT =\n    { SPELL_BITE, 0, 0, SPELL_C_COMMAND, SPELL_A_COMMAND, 0 };"
        slots = parse_kit_slots(unknown, header)
        self.assertEqual(slots[-1], "SPELL_C_COMMAND")
        self.assertEqual(slots[201720], "both")
        # a row outside the FAMILY_KITS initializer is not a family row
        self.assertEqual(parse_kits("{ 3, { SPELL_BITE, 0, 0, SPELL_A_COMMAND, SPELL_B_COMMAND, 0 } },", header)[0], {})

    def test_display_table_parser(self):
        header = "constexpr uint32 SPELL_A_COMMAND = 201720; // a\nconstexpr uint32 SPELL_A_DISPLAY = 201858; // b\n"
        cpp = ("constexpr std::array<CommandDisplay, 1> COMMAND_DISPLAYS =\n{{\n"
               "    { SPELL_A_COMMAND, HunterData::SPELL_A_DISPLAY },\n}};\n")
        self.assertEqual(parse_command_displays(cpp, header), ({201720: 201858}, []))
        self.assertEqual(parse_command_displays(cpp.replace("SPELL_A_DISPLAY }", "SPELL_Z }"), header)[1], ["SPELL_Z"])

    def test_command_display_guard(self):
        rows, slots = good_displays()
        table = {c: c + 138 for c in COMMANDED_SLOTTED}
        self.assertEqual(check_command_displays(rows, table, slots, [], [], []), [])

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
            self.assertEqual(len(check_command_displays(changed(display, **cols), table, slots, [], [], [])), 1,
                             (display, cols))
        missing = {k: v for k, v in rows.items() if k != 201873}
        self.assertEqual(len(check_command_displays(missing, table, slots, [], [], [])), 1)
        with_splash = {**table, 201736: 201874}
        self.assertGreaterEqual(len(check_command_displays(rows, with_splash, slots, [], [], [])), 1)
        without_pair = {k: v for k, v in table.items() if k != 201731}
        self.assertGreaterEqual(len(check_command_displays(rows, without_pair, slots, [], [], [])), 1)
        self.assertEqual(len(check_command_displays(rows, table, {**slots, 201725: "both"}, [], [], [])), 1)
        self.assertEqual(len(check_command_displays(rows, table, {k: v for k, v in slots.items() if k != 201730}, [],
                                                    [], [])), 1)
        self.assertEqual(len(check_command_displays(rows, table, {**slots, -1: "SPELL_X_COMMAND"}, [], [], [])), 1)
        bound = [{"spell_id": 201866, "ScriptName": "spell_hun_command"}]
        self.assertEqual(len(check_command_displays(rows, table, slots, bound, [], [])), 1)
        talents = [{"id": 1, "rank_spell_ids": [201867]}]
        self.assertEqual(len(check_command_displays(rows, table, slots, [], talents, [])), 1)
        trainers = [{"TrainerId": 204, "SpellId": 201868}]
        self.assertEqual(len(check_command_displays(rows, table, slots, [], [], trainers)), 1)
        shifted = {c: c + 137 for c in COMMANDED_SLOTTED}
        self.assertGreaterEqual(len(check_command_displays(rows, shifted, slots, [], [], [])), 1)   # wrong pairs

    def test_family_kit_guard(self):
        displays = {c: c + 138 for c in COMMANDED_SLOTTED}
        util = {"SpellClassSet": 9, "SpellClassMask_2": 0x30000000}
        rows = {i: {"ID": i} for i in (17253, 16827, 49966, 201710, 201711, 61684, 53478, 53490, *COMMANDED_SLOTTED)}
        rows.update({i: {"ID": i, **util} for g_u in FINISHED_KITS.values() for i in g_u})
        rows.update({i: {"ID": i, "SpellClassSet": 9, "SpellClassMask_2": 0x10000000} for i in NO_MOBILITY_UTILITIES})

        def row(basic, group, utility, c1, c2, flags):
            return dict(zip(_KIT_FIELDS, (basic, group, utility, c1, c2, flags)))

        kits = {f: row(17253, 61684, 0, 201730, 201731, 0) for f in HUNTER_FAMILIES}
        for family, (group, utility) in FINISHED_KITS.items():
            kits[family] = row(16827, group, utility, 201720, 201721, 0 if family in MANUAL_GROUP_FAMILIES else 1)
        defaults = {"KIT_FEROCITY_DEFAULT": row(17253, 0, 0, 201730, 201731, 0),
                    "KIT_TENACITY_DEFAULT": row(17253, 0, 0, 201732, 201733, 0),
                    "KIT_CUNNING_DEFAULT": row(201711, 0, 0, 201734, 201735, 0),
                    "KIT_NONE": row(0, 0, 0, 0, 0, 0)}
        rows[61684].update(util)
        self.assertEqual(check_family_kits(kits, defaults, [], displays, rows), [])
        self.assertEqual(len(check_family_kits({k: v for k, v in kits.items() if k != 46}, defaults, [], displays,
                                               rows)), 1)                                    # a family missing
        self.assertEqual(len(check_family_kits(kits, defaults, ["SPELL_X"], displays, rows)), 1)
        self.assertEqual(len(check_family_kits({**kits, 24: row(201711, 201771, 202004, 201730, 999, 1)}, defaults,
                                               [], displays, rows)), 2)                     # undeclared, no display
        # F3: a kit naming a retired placeholder (and so not its own slot spells)
        self.assertEqual(len(check_family_kits({**kits, 24: row(201711, 53490, 202004, 201720, 201721, 1)}, defaults,
                                               [], displays, rows)), 3)                     # placeholder, mask, slots
        self.assertEqual(len(check_family_kits({**kits, 1: row(16827, 24604, 201983, 201720, 201721, 0)}, defaults,
                                               [], displays, rows)), 1)                     # autocast flag lost
        self.assertEqual(len(check_family_kits({**kits, 3: row(201710, 201718, 201753, 201728, 201729, 1)},
                                               defaults, [], displays, rows)), 1)           # Spider slots swapped
        no_b29 = {**rows, 201983: {"ID": 201983, "SpellClassSet": 9, "SpellClassMask_2": 0x10000000}}
        self.assertEqual(len(check_family_kits(kits, defaults, [], displays, no_b29)), 1)
        # F1: Ancient Hysteria must not carry the Mobility bit (ruling 10), and its kit is manual
        with_b29 = {**rows, 201760: {"ID": 201760, "SpellClassSet": 9, "SpellClassMask_2": 0x30000000}}
        self.assertEqual(len(check_family_kits(kits, defaults, [], displays, with_b29)), 1)
        self.assertEqual(len(check_family_kits({**kits, 45: row(17253, 201760, 201993, 201720, 201721, 1)}, defaults,
                                               [], displays, rows)), 1)                     # manual slot 2 autocast
        bad_default = {**defaults, "KIT_FEROCITY_DEFAULT": row(17253, 61684, 0, 201730, 201731, 0)}
        self.assertEqual(len(check_family_kits(kits, bad_default, [], displays, rows)), 1)

    def test_mobility_guard(self):
        def mob(bp, **cols):
            return {"Effect_1": 119, "EffectAura_1": 108, "EffectMiscValue_1": 11, "EffectBasePoints_1": bp,
                    "EffectSpellClassMaskA_2": 0x20000000, "SpellClassSet": 9, **cols}
        rows = {53483: {"ID": 53483, **mob(-11)}, 53485: {"ID": 53485, **mob(-21)}}
        rows.update({i: {"ID": i, "SpellClassSet": 9, "SpellClassMask_2": 0x30000000} for i in D1_B29_CARRIERS})
        rows.update({i: {"ID": i, "SpellClassSet": 9, "EffectSpellClassMaskA_2": 0x20000000}
                     for i in D1_B29_READERS - set(MOBILITY)})
        self.assertEqual(check_mobility(rows, list(rows.values())), [])
        flat = {**rows, 53483: {"ID": 53483, **mob(-8001, EffectAura_1=107)}}
        self.assertEqual(len(check_mobility(flat, list(flat.values()))), 1)
        reader = {**rows, 999: {"ID": 999, "SpellClassSet": 9, "EffectSpellClassMaskB_2": 0x20000000}}
        self.assertEqual(len(check_mobility(reader, list(reader.values()))), 1)
        carrier = {**rows, 998: {"ID": 998, "SpellClassSet": 9, "SpellClassMask_2": 0x20000000}}
        self.assertEqual(len(check_mobility(carrier, list(carrier.values()))), 1)

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


def good_f1_command_rows() -> dict[int, dict]:
    rows = {}
    for spell_id in (*F1_COMMANDS, *F1_HELPERS):
        school = 8 if spell_id in F1_NATURE_COMMANDS else 4 if spell_id in F1_FIRE_COMMANDS else 1
        rows[spell_id] = {"ID": spell_id, "SpellClassSet": 9, "SpellClassMask_2": 0x10000000,
                          "SpellClassMask_3": 0x400000, "Effect_1": EFFECT_SCHOOL_DAMAGE, "ImplicitTargetA_1": 6,
                          "DefenseType": DEFENSE_MELEE, "SchoolMask": school}
    for helper in F1_HELPERS:
        rows[helper]["AttributesEx3"] = SUPPRESS_CASTER_PROCS
    for command, (strike, follow_ups) in F1_MULTIHIT.items():
        rows[command].update({"Effect_2": EFFECT_DUMMY, "EffectTriggerSpell_2": strike,
                              "EffectBasePoints_2": follow_ups - 1, "EffectDieSides_2": 1, "ImplicitTargetA_2": 6})
    for command in F1_CONES:
        rows[command].update({"ImplicitTargetA_1": 104, "Effect_3": EFFECT_DUMMY, "ImplicitTargetA_3": 6})
    return rows


def good_f1_utility_rows() -> tuple[dict[int, dict], list[dict]]:
    rows = {}
    for spell_id, level in F1_LEVELS.items():
        target = 56 if spell_id in F1_RAID_EFFECTS else 6
        rows[spell_id] = {"ID": spell_id, "SpellClassSet": 9, "EquippedItemClass": -1, "Attributes": 0x50010,
                          "SpellLevel": level, "RecoveryTime": F1_RECOVERY[spell_id], "Effect_1": EFFECT_APPLY_AURA,
                          "ImplicitTargetA_1": target,
                          "AttributesEx": ATTR1_NO_AUTOCAST_AI if spell_id in F1_NO_AUTOCAST else 0}
    rows[201987].update({"Effect_1": EFFECT_HEAL_PCT, "EffectBasePoints_1": 59, "ImplicitTargetA_1": 1})
    rows[FRESH_KILL] = {"ID": FRESH_KILL, "Attributes": 0, "DurationIndex": 1, "Effect_1": EFFECT_APPLY_AURA,
                        "EffectAura_1": AURA_DUMMY, "ImplicitTargetA_1": 1}
    rows[ETERNAL_GUARDIAN_REBIRTH] = {"ID": ETERNAL_GUARDIAN_REBIRTH, "Effect_1": EFFECT_RESURRECT,
                                      "Targets": TARGET_FLAG_CORPSE_ALLY}
    groups = [{"id": g, "spell_id": sid} for sid, g in F1_SPELL_GROUPS.items()]
    return rows, groups


class HunterPetFamiliesF1GuardTest(unittest.TestCase):
    """(z) every F1 check fires on a minimal bad input."""

    def test_ruling_23_guard(self):
        def entry(value):
            return {"effect1": {"_potency": {"total_potency": value}}}
        good = {1: entry(61.2), 2: entry(12.87)}
        table = {1: [(1, 40.8, "direct", 1.5)], 2: [(1, 33.0, "direct", 0.39)]}
        self.assertEqual(check_ruling_23_potency(good, table), [])
        self.assertEqual(len(check_ruling_23_potency({**good, 1: entry(40.8)}, table)), 1)    # basic unscaled
        self.assertEqual(len(check_ruling_23_potency({**good, 2: entry(33.0)}, table)), 1)    # Cunning unscaled
        self.assertEqual(len(check_ruling_23_potency({2: good[2]}, table)), 1)                # missing
        # ruling 23b: a Tenacity command that kept (or double-took) the scale is caught by the F2 table check
        tenacity = {1: {"effect1": {"_potency": {"total_potency": 650 * 0.84 * 0.8}}}}
        self.assertEqual(check_f1_potency(tenacity, {1: [(1, 650, "I", "direct")]}, 0.8), [])
        self.assertEqual(len(check_f1_potency({1: {"effect1": {"_potency": {"total_potency": 650 * 0.84}}}},
                                              {1: [(1, 650, "I", "direct")]}, 0.8)), 1)

    def test_potency_guard(self):
        def entry(value, kind="direct"):
            pot = {"total_potency": value, "t_seconds": 3.0, "ticks": 3.0} if kind == "total" else \
                {"total_potency": value}
            return {"effect1": {"_potency": pot}}
        table = {1: [(1, 400, "I", "direct")], 2: [(1, 1000, "II", "direct")], 3: [(1, 250, "I", "total")]}
        good = {1: entry(336.0), 2: entry(650.0), 3: entry(35.0, "total")}    # 35 x 3 s / 1.5 s x 3 ticks = 210
        self.assertEqual(check_f1_potency(good, table), [])
        self.assertEqual(len(check_f1_potency({**good, 1: entry(400.0)}, table)), 1)      # unscaled
        self.assertEqual(len(check_f1_potency({**good, 2: entry(546.0)}, table)), 1)      # Command I scale on II
        self.assertEqual(len(check_f1_potency({**good, 3: entry(52.5, "total")}, table)), 1)
        self.assertEqual(len(check_f1_potency({1: good[1], 2: good[2]}, table)), 1)       # missing
        self.assertEqual(len(check_f1_potency({**good, 1: {"effect1": {}}}, table)), 1)   # no potency

    def test_command_guard(self):
        rows = good_f1_command_rows()
        self.assertEqual(check_f1_commands(rows, {}), [])

        def changed(spell_id, **cols):
            return {**rows, spell_id: {**rows[spell_id], **cols}}

        self.assertEqual(len(check_f1_commands(changed(201660, AttributesEx3=0), {})), 1)
        self.assertEqual(len(check_f1_commands(rows, {201661: 202200})), 1)
        self.assertEqual(len(check_f1_commands(changed(201609, EffectBasePoints_2=2), {})), 1)    # 3 follow-ups
        self.assertEqual(len(check_f1_commands(changed(201615, EffectTriggerSpell_2=201660), {})), 1)
        self.assertEqual(len(check_f1_commands(changed(201619, EffectBasePoints_2=1), {})), 1)    # two follow-ups
        self.assertEqual(len(check_f1_commands(changed(201613, Effect_3=0), {})), 1)              # no anchor
        self.assertEqual(len(check_f1_commands(changed(201620, SchoolMask=1), {})), 1)           # Nature lost
        self.assertEqual(len(check_f1_commands(changed(201608, Effect_2=EFFECT_APPLY_AURA, EffectAura_2=12), {})), 1)
        self.assertEqual(len(check_f1_commands(changed(201608, Effect_2=EFFECT_APPLY_AURA,
                                                       EffectAura_2=AURA_MOD_DECREASE_SPEED), {})), 0)   # a snare

    def test_utility_guard(self):
        rows, groups = good_f1_utility_rows()
        self.assertEqual(check_f1_utilities(rows, groups), [])

        def changed(spell_id, **cols):
            return {**rows, spell_id: {**rows[spell_id], **cols}}

        self.assertEqual(len(check_f1_utilities(changed(201760, SpellLevel=70), groups)), 1)
        self.assertEqual(len(check_f1_utilities(changed(201761, AttributesEx=0), groups)), 1)        # autocastable
        self.assertEqual(len(check_f1_utilities(changed(201755, AttributesEx=0x20000), groups)), 1)  # buff no autocast
        self.assertEqual(len(check_f1_utilities(changed(201760, RecoveryTime=600000), groups)), 1)
        self.assertEqual(len(check_f1_utilities(changed(201755, ImplicitTargetA_1=20), groups)), 1)   # subgroup only
        self.assertEqual(len(check_f1_utilities(changed(201991, Attributes=0x50050), groups)), 1)    # passive
        self.assertEqual(len(check_f1_utilities(rows, groups[1:])), 1)                              # group missing
        self.assertEqual(len(check_f1_utilities(rows, groups + [{"id": 1060, "spell_id": 201989}])), 1)
        self.assertEqual(len(check_f1_utilities(changed(201987, EffectBasePoints_1=29), groups)), 1)  # Scavenge 30%
        self.assertEqual(len(check_f1_utilities(changed(FRESH_KILL, Attributes=0x40), groups)), 1)
        self.assertEqual(len(check_f1_utilities(changed(ETERNAL_GUARDIAN_REBIRTH, SpellClassSet=9), groups)), 1)
        self.assertEqual(len(check_f1_utilities({k: v for k, v in rows.items() if k != 201994}, groups)), 1)

    def test_binding_guard(self):
        bound = [{"spell_id": sid, "ScriptName": name} for sid, names in F1_SCRIPT_BINDINGS.items() for name in names]
        self.assertEqual(check_f1_bindings(bound), [])
        self.assertEqual(len(check_f1_bindings(bound[1:])), 1)
        self.assertEqual(len(check_f1_bindings(bound + [{"spell_id": 201620, "ScriptName": "spell_hun_twohit"}])), 1)
        self.assertEqual(len(check_f1_bindings(bound + [{"spell_id": -201609, "ScriptName": "x"}])), 1)



def good_f2_command_rows() -> dict[int, dict]:
    rows = {}
    for spell_id in (*F2_COMMANDS, *F2_DAMAGE_HELPERS):
        school = 8 if spell_id in F2_NATURE_COMMANDS else 16 if spell_id in F2_FROST_COMMANDS else \
            64 if spell_id in F2_ARCANE_COMMANDS else 1
        rows[spell_id] = {"ID": spell_id, "SpellClassSet": 9, "SpellClassMask_2": 0x10000000,
                          "SpellClassMask_3": 0x400000, "Effect_1": EFFECT_SCHOOL_DAMAGE, "ImplicitTargetA_1": 6,
                          "DefenseType": DEFENSE_MELEE, "SchoolMask": school}
    for command, rider in F2_TRIGGERS.items():
        rows[command].update({"Effect_2": EFFECT_TRIGGER_SPELL, "EffectTriggerSpell_2": rider})
    rows[GORE_DEBUFF] = {"ID": GORE_DEBUFF, "AttributesEx3": SUPPRESS_CASTER_PROCS | ATTR3_DOT_STACKING_RULE,
                         "Effect_1": EFFECT_APPLY_AURA,
                         "EffectAura_1": AURA_DUMMY, "EffectBasePoints_1": 3, "EffectDieSides_1": 1}
    rows[PINCER_CRUSH_ROOT] = {"ID": PINCER_CRUSH_ROOT, "AttributesEx3": SUPPRESS_CASTER_PROCS,
                               "Effect_1": EFFECT_APPLY_AURA, "EffectAura_1": F2_ROOT_AURA}
    for command in F2_CONES:
        rows[command].update({"ImplicitTargetA_1": 104, "Effect_2": EFFECT_DUMMY, "ImplicitTargetA_2": 6})
    for command in F2_AROUND_PET:
        rows[command].update({"ImplicitTargetA_1": 22, "ImplicitTargetB_1": 15, "Effect_2": EFFECT_DUMMY,
                              "ImplicitTargetA_2": 6})
    rows[201625].update({"Effect_1": EFFECT_APPLY_AURA, "EffectAura_1": AURA_PERIODIC_DAMAGE, "AttributesEx": 0x204,
                         "DurationIndex": 30112})
    rows[201634].update({"Effect_1": EFFECT_TELEPORT_UNITS, "ImplicitTargetA_1": 1, "ImplicitTargetB_1": 65,
                         "Effect_2": EFFECT_SCHOOL_DAMAGE, "ImplicitTargetA_2": 6})
    rows[201631].update({"Effect_2": EFFECT_DUMMY, "ImplicitTargetA_2": 6, "EffectTriggerSpell_2": 201630})
    rows[201636].update({"Effect_1": EFFECT_APPLY_AURA, "EffectAura_1": AURA_PERIODIC_TRIGGER_SPELL,
                         "ImplicitTargetA_1": 1, "EffectTriggerSpell_1": BURROW_ATTACK_PULSE, "Effect_2": EFFECT_DUMMY,
                         "ImplicitTargetA_2": 6})
    return rows


def good_f2_utility_rows() -> tuple[dict[int, dict], list[dict], list[dict]]:
    rows = {}
    for spell_id, level in F2_LEVELS.items():
        target = 56 if spell_id in F2_RAID_EFFECTS else 6
        rows[spell_id] = {"ID": spell_id, "SpellClassSet": 9, "EquippedItemClass": -1, "Attributes": 0x50010,
                          "SpellLevel": level, "RecoveryTime": F2_RECOVERY[spell_id], "Effect_1": EFFECT_APPLY_AURA,
                          "ImplicitTargetA_1": target,
                          "AttributesEx": ATTR1_NO_AUTOCAST_AI if spell_id in F2_NO_AUTOCAST else 0}
    rows[BUBBLE_SHIELD].update({"EffectAura_1": AURA_SCHOOL_ABSORB, "ImplicitTargetA_1": TARGET_UNIT_MASTER})
    groups = [{"id": g, "spell_id": sid} for sid, g in F2_SPELL_GROUPS.items()]
    groups.append({"id": SPELL_GROUP_RAID_DAMAGE_TAKEN, "spell_id": 202006})     # F3's Gale Barrier
    rules = [{"group_id": SPELL_GROUP_RAID_DAMAGE_TAKEN, "stack_rule": 4}]
    return rows, groups, rules


class HunterPetFamiliesF2GuardTest(unittest.TestCase):
    """(aa) every F2 check fires on a minimal bad input."""

    def test_command_guard(self):
        rows = good_f2_command_rows()
        self.assertEqual(check_f2_commands(rows, {}), [])

        def changed(spell_id, **cols):
            return {**rows, spell_id: {**rows[spell_id], **cols}}

        self.assertEqual(len(check_f2_commands(changed(201622, Effect_2=0), {})), 1)                 # Gore's rider
        self.assertEqual(len(check_f2_commands(changed(GORE_DEBUFF, SpellClassSet=9), {})), 1)
        self.assertEqual(len(check_f2_commands(changed(GORE_DEBUFF, EffectBasePoints_1=9), {})), 1)  # 10%, not 4
        self.assertEqual(len(check_f2_commands(changed(GORE_DEBUFF, AttributesEx3=SUPPRESS_CASTER_PROCS), {})), 1)
        self.assertEqual(len(check_f2_commands(changed(PINCER_CRUSH_ROOT, AttributesEx3=0), {})), 1)
        self.assertEqual(len(check_f2_commands(changed(201623, Effect_2=0), {})), 1)                 # no anchor
        self.assertEqual(len(check_f2_commands(changed(201627, ImplicitTargetB_1=16), {})), 1)       # wrong area
        self.assertEqual(len(check_f2_commands(changed(201625, AttributesEx=0x200), {})), 1)        # not channeled
        self.assertEqual(len(check_f2_commands(changed(201634, ImplicitTargetB_1=0), {})), 1)       # no blink
        self.assertEqual(len(check_f2_commands(changed(201631, EffectTriggerSpell_2=201622), {})), 1)
        self.assertEqual(len(check_f2_commands(changed(201636, EffectTriggerSpell_1=0), {})), 1)
        self.assertEqual(len(check_f2_commands(changed(201629, SchoolMask=1), {})), 1)              # Frost lost
        self.assertEqual(len(check_f2_commands(rows, {BURROW_ATTACK_PULSE: 202200})), 1)
        self.assertEqual(len(check_f2_commands(changed(201667, SpellClassMask_3=0), {})), 1)        # carrier lost

    def test_utility_guard(self):
        rows, groups, rules = good_f2_utility_rows()
        self.assertEqual(check_f2_utilities(rows, groups, rules), [])

        def changed(spell_id, **cols):
            return {**rows, spell_id: {**rows[spell_id], **cols}}

        self.assertEqual(len(check_f2_utilities(changed(201769, AttributesEx=0), groups, rules)), 1)    # autocastable
        self.assertEqual(len(check_f2_utilities(changed(201762, AttributesEx=0x20000), groups, rules)), 1)
        self.assertEqual(len(check_f2_utilities(changed(201769, RecoveryTime=60000), groups, rules)), 1)
        self.assertEqual(len(check_f2_utilities(changed(202003, ImplicitTargetA_1=20), groups, rules)), 1)
        self.assertEqual(len(check_f2_utilities(changed(201999, Attributes=0x50050), groups, rules)), 1)
        self.assertEqual(len(check_f2_utilities(rows, groups[1:], rules)), 1)                     # group missing
        self.assertEqual(len(check_f2_utilities(rows, groups + [{"id": 1232, "spell_id": 201997}], rules)), 2)
        self.assertEqual(len(check_f2_utilities(rows, groups, [])), 1)                            # no rule 4
        self.assertEqual(len(check_f2_utilities(changed(BUBBLE_SHIELD, ImplicitTargetA_1=1), groups, rules)), 1)
        self.assertEqual(len(check_f2_utilities({k: v for k, v in rows.items() if k != 202001}, groups, rules)), 1)

    def test_binding_and_absorb_guard(self):
        bound = [{"spell_id": sid, "ScriptName": name} for sid, names in F2_SCRIPT_BINDINGS.items() for name in names]
        self.assertEqual(check_f2_bindings(bound), [])
        self.assertEqual(len(check_f2_bindings(bound[1:])), 1)
        self.assertEqual(len(check_f2_bindings(bound + [{"spell_id": 201622, "ScriptName": "spell_hun_gore"}])), 1)
        self.assertEqual(check_f2_absorb_coefficient([{"entry": BUBBLE_SHIELD, "ap_bonus": 0.3}]), [])
        self.assertEqual(len(check_f2_absorb_coefficient([{"entry": BUBBLE_SHIELD, "ap_bonus": 0}])), 1)


def good_f3_command_rows() -> dict[int, dict]:
    rows = {}
    for spell_id in (*F3_COMMANDS, *F3_DAMAGE_HELPERS):
        rows[spell_id] = {"ID": spell_id, "SpellClassSet": 9, "SpellClassMask_2": 0x10000000,
                          "SpellClassMask_3": 0x400000, "Effect_1": EFFECT_SCHOOL_DAMAGE, "ImplicitTargetA_1": 6,
                          "DefenseType": DEFENSE_MELEE if spell_id in F3_MELEE else DEFENSE_RANGED,
                          "SchoolMask": F3_SCHOOLS.get(spell_id, 1),
                          "RangeIndex": 2 if spell_id in F3_MELEE else 6}
    for command in F3_CONES:
        rows[command].update({"ImplicitTargetA_1": 104, "Effect_2": EFFECT_DUMMY, "ImplicitTargetA_2": 6})
    for spell_id in (*F3_AT_TARGET, *F3_SPLASHES.values()):
        rows[spell_id].update({"ImplicitTargetA_1": 53, "ImplicitTargetB_1": 16})
    for command, helper in {**F3_SPLASHES, **F3_ROOTS}.items():
        rows[command].update({"Effect_2": EFFECT_TRIGGER_SPELL, "EffectTriggerSpell_2": helper})
    for root in F3_ROOTS.values():
        rows[root] = {"ID": root, "AttributesEx3": SUPPRESS_CASTER_PROCS, "Effect_1": EFFECT_APPLY_AURA,
                      "EffectAura_1": F2_ROOT_AURA}
    for command, (targets, amplitude) in F3_CHAINS.items():
        rows[command].update({"EffectChainTargets_1": targets, "EffectChainAmplitude_1": amplitude})
    for command, (strike, follow_ups) in F3_MULTIHIT.items():
        rows[command].update({"Effect_2": EFFECT_DUMMY, "EffectTriggerSpell_2": strike,
                              "EffectBasePoints_2": follow_ups - 1, "EffectDieSides_2": 1, "ImplicitTargetA_2": 6})
        rows[strike]["AttributesEx3"] = SUPPRESS_CASTER_PROCS
    for command, tick in F3_CHANNEL.items():
        rows[command].update({"Effect_1": EFFECT_APPLY_AURA, "EffectAura_1": AURA_PERIODIC_TRIGGER_SPELL,
                              "ImplicitTargetA_1": 1, "EffectTriggerSpell_1": tick, "Effect_2": EFFECT_DUMMY,
                              "ImplicitTargetA_2": 6, "AttributesEx": 0x204, "DurationIndex": 30112})
    return rows


def good_f3_utility_rows() -> tuple[dict[int, dict], list[dict]]:
    rows = {}
    for spell_id, level in F3_LEVELS.items():
        target = 56 if spell_id in F3_RAID_EFFECTS else 6
        rows[spell_id] = {"ID": spell_id, "SpellClassSet": 9, "EquippedItemClass": -1, "Attributes": 0x50010,
                          "SpellLevel": level, "RecoveryTime": F3_RECOVERY[spell_id], "Effect_1": EFFECT_APPLY_AURA,
                          "ImplicitTargetA_1": target,
                          "AttributesEx": ATTR1_NO_AUTOCAST_AI if spell_id in F3_NO_AUTOCAST else 0}
    rows[GALE_BARRIER]["EffectAura_1"] = AURA_MOD_DAMAGE_PERCENT_TAKEN
    rows[EARTHEN_BULWARK] = {"ID": EARTHEN_BULWARK, "Effect_1": EFFECT_APPLY_AURA,
                             "EffectAura_1": AURA_MOD_DAMAGE_PERCENT_TAKEN}
    rows[SWARM_SHIELD].update({"EffectAura_1": AURA_SCHOOL_ABSORB, "ImplicitTargetA_1": TARGET_UNIT_MASTER})
    rows[SHED_SKIN].update({"Effect_1": EFFECT_DISPEL_MECHANIC, "EffectMiscValue_1": 7,
                            "Effect_2": EFFECT_DISPEL_MECHANIC, "EffectMiscValue_2": 11,
                            "Effect_3": EFFECT_TRIGGER_SPELL, "EffectTriggerSpell_3": SHED_SKIN_HEAL})
    rows[SHED_SKIN_HEAL] = {"ID": SHED_SKIN_HEAL, "Effect_1": EFFECT_DISPEL, "EffectMiscValue_1": 4,
                            "Effect_2": EFFECT_HEAL_PCT, "EffectBasePoints_2": 19}
    groups = [{"id": g, "spell_id": sid} for sid, g in F3_SPELL_GROUPS.items()]
    groups += [{"id": SPELL_GROUP_SPELL_HASTE, "spell_id": sid} for sid in (202209, 2895)]
    return rows, groups


class HunterPetFamiliesF3GuardTest(unittest.TestCase):
    """(ab) every F3 check fires on a minimal bad input."""

    def test_command_guard(self):
        rows = good_f3_command_rows()
        self.assertEqual(check_f3_commands(rows, {}), [])

        def changed(spell_id, **cols):
            return {**rows, spell_id: {**rows[spell_id], **cols}}

        self.assertEqual(len(check_f3_commands(changed(201644, DefenseType=DEFENSE_MELEE), {})), 1)   # not ranged
        self.assertEqual(len(check_f3_commands(changed(201641, RangeIndex=6), {})), 1)              # cone at 30 yd
        self.assertEqual(len(check_f3_commands(changed(201649, RangeIndex=2), {})), 1)              # Cunning in melee
        self.assertEqual(len(check_f3_commands(changed(201670, SchoolMask=16), {})), 1)             # Nature lost
        self.assertEqual(len(check_f3_commands(changed(201641, Effect_2=0), {})), 1)                # no anchor
        self.assertEqual(len(check_f3_commands(changed(201647, ImplicitTargetB_1=15), {})), 1)      # wrong area
        self.assertEqual(len(check_f3_commands(changed(201652, Effect_2=0), {})), 1)                # no splash
        self.assertEqual(len(check_f3_commands(changed(201651, EffectTriggerSpell_2=201673), {})), 1)
        self.assertEqual(len(check_f3_commands(changed(CONSTRICT_ROOT, SpellClassSet=9), {})), 1)
        self.assertEqual(len(check_f3_commands(changed(201645, EffectChainAmplitude_1=0.5), {})), 1)  # compounding
        self.assertEqual(len(check_f3_commands(changed(201640, EffectChainTargets_1=0), {})), 1)    # no bounce
        self.assertEqual(len(check_f3_commands(changed(201656, EffectBasePoints_2=1), {})), 1)      # two follow-ups
        self.assertEqual(len(check_f3_commands(changed(201670, AttributesEx3=0), {})), 1)
        self.assertEqual(len(check_f3_commands(changed(201657, AttributesEx=0x200), {})), 1)       # not channeled
        self.assertEqual(len(check_f3_commands(changed(201657, EffectTriggerSpell_1=201670), {})), 1)
        self.assertEqual(len(check_f3_commands(rows, {FROSTSTORM_TICK: 202200})), 1)
        self.assertEqual(len(check_f3_commands(changed(201675, SpellClassMask_3=0), {})), 1)        # carrier lost

    def test_utility_guard(self):
        rows, groups = good_f3_utility_rows()
        rules = [{"group_id": SPELL_GROUP_SPELL_HASTE, "stack_rule": 3}]
        self.assertEqual(check_f3_utilities(rows, groups, rules), [])

        def changed(spell_id, **cols):
            return {**rows, spell_id: {**rows[spell_id], **cols}}

        self.assertEqual(len(check_f3_utilities(changed(GALE_BARRIER, AttributesEx=0), groups, rules)), 1)   # autocastable
        self.assertEqual(len(check_f3_utilities(changed(201772, AttributesEx=0x20000), groups, rules)), 1)
        self.assertEqual(len(check_f3_utilities(changed(201772, ImplicitTargetA_1=20), groups, rules)), 1)   # subgroup only
        self.assertEqual(len(check_f3_utilities(changed(202012, Attributes=0x50050), groups, rules)), 1)     # passive
        self.assertEqual(len(check_f3_utilities(changed(202005, SpellLevel=10), groups, rules)), 1)
        self.assertEqual(len(check_f3_utilities(rows, groups[1:], rules)), 1)                              # group missing
        self.assertEqual(len(check_f3_utilities(rows, groups + [{"id": 1096, "spell_id": 202008}], rules)), 1)
        self.assertEqual(len(check_f3_utilities(changed(GALE_BARRIER, Effect_2=EFFECT_DUMMY, ImplicitTargetA_2=56),
                                                groups, rules)), 1)                                # a second effect
        self.assertEqual(len(check_f3_utilities(changed(GALE_BARRIER, EffectAura_1=AURA_SCHOOL_ABSORB), groups, rules)), 1)
        self.assertEqual(len(check_f3_utilities(changed(SWARM_SHIELD, ImplicitTargetA_1=1), groups, rules)), 1)
        self.assertEqual(len(check_f3_utilities(changed(SHED_SKIN, EffectMiscValue_2=7), groups, rules)), 1)
        self.assertEqual(len(check_f3_utilities(changed(SHED_SKIN_HEAL, EffectBasePoints_2=29), groups, rules)), 1)
        self.assertEqual(len(check_f3_utilities({k: v for k, v in rows.items() if k != 202010}, groups, rules)), 1)
        self.assertEqual(len(check_f3_utilities(rows, groups, [])), 1)                              # no rule 3
        self.assertEqual(len(check_f3_utilities(rows, groups, [{"group_id": 1233, "stack_rule": 4}])), 1)
        self.assertEqual(len(check_f3_utilities(rows, [g for g in groups if g["spell_id"] != 202209], rules)), 1)

    def test_binding_guard(self):
        bound = [{"spell_id": sid, "ScriptName": name} for sid, names in F3_SCRIPT_BINDINGS.items() for name in names]
        self.assertEqual(check_f3_bindings(bound), [])
        self.assertEqual(len(check_f3_bindings(bound[1:])), 1)
        self.assertEqual(len(check_f3_bindings(bound + [{"spell_id": 201652, "ScriptName": "spell_hun_command_aoe_"
                                                         "falloff"}])), 1)     # Sporebat: rule 17, no falloff
        self.assertEqual(check_f2_absorb_coefficient([{"entry": SWARM_SHIELD, "ap_bonus": 0.3}], SWARM_SHIELD), [])
        self.assertEqual(len(check_f2_absorb_coefficient([], SWARM_SHIELD)), 1)

    def test_kit_table_guard(self):
        # a kit naming a retired placeholder fails (F3)
        rows = {i: {"ID": i, "SpellClassSet": 9, "SpellClassMask_2": 0x10000000} for i in PLACEHOLDER_SLOT_SPELLS}
        kits = {24: {"basic": 201711, "group": 53490, "utility": 61684, "commandI": 201640, "commandII": 201641,
                     "flags": 1}}
        problems = check_family_kits(kits, {}, [], {201640: 202143, 201641: 202144}, rows)
        self.assertTrue(any("retired placeholder" in p for p in problems))


class HunterPetFamiliesRuling24GuardTest(unittest.TestCase):
    """(ad) every ruling 24 check fires on a minimal bad input."""

    @staticmethod
    def _rows():
        def damage(sid, **cols):
            return {"ID": sid, "Effect_1": EFFECT_SCHOOL_DAMAGE, **cols}
        return {
            1: damage(1),                                                       # single-target command
            2: damage(2, EffectRadiusIndex_1=13),                               # area command
            3: damage(3, EffectChainTargets_1=2),                               # chain command
            4: damage(4, Effect_2=EFFECT_TRIGGER_SPELL, EffectTriggerSpell_2=5),    # trigger into a splash
            5: damage(5, EffectRadiusIndex_1=13),                               # the splash
            6: damage(6, Effect_2=EFFECT_DUMMY, EffectTriggerSpell_2=7),        # multi-hit command
            7: damage(7),                                                       # its strike helper
            8: {"ID": 8, "Effect_1": EFFECT_APPLY_AURA, "EffectAura_1": AURA_PERIODIC_TRIGGER_SPELL,
                "EffectTriggerSpell_1": 9},                                     # a channel
            9: damage(9, EffectRadiusIndex_1=13),                               # its area tick
        }

    def test_classification_guard(self):
        rows = self._rows()
        self.assertEqual(classify_single_target([1, 2, 3, 4, 6, 8], rows), ({1, 6, 7}, {2, 3, 4, 5, 9}))
        kits = {1: {"commandI": 1, "commandII": 2}, 2: {"commandI": 6, "commandII": 4}}
        defaults = {"KIT_X": {"commandI": 3, "commandII": 8}}
        args = (kits, defaults, rows, frozenset({1, 2}), "KIT_X")
        self.assertEqual(check_ruling_24_classification(*args, frozenset({1, 6, 7}), frozenset({2, 3, 4, 5, 9})), [])
        self.assertEqual(len(check_ruling_24_classification(*args, frozenset({1, 6}), frozenset())), 1)  # no helper
        self.assertEqual(len(check_ruling_24_classification(*args, frozenset({1, 2, 6, 7}), frozenset())), 1)  # AoE
        self.assertEqual(len(check_ruling_24_classification(*args, frozenset({1, 6, 7}), frozenset({1}))), 1)

    def test_potency_guard(self):
        def entry(value):
            return {"effect1": {"_potency": {"total_potency": value}}}
        table = {1: [(1, 400, "I", "direct")], 2: [(1, 400, "I", "direct")]}
        good = {1: entry(400 * 0.84 * 1.07), 2: entry(400 * 0.84)}             # 1 single-target, 2 AoE
        self.assertEqual(check_f1_potency(good, table, id_scales={1: 1.07}), [])
        self.assertEqual(len(check_f1_potency({**good, 1: entry(336.0)}, table, id_scales={1: 1.07})), 1)  # unscaled
        self.assertEqual(len(check_f1_potency({**good, 2: entry(336.0 * 1.07)}, table, id_scales={1: 1.07})), 1)
        cunning = {1: entry(400 * 0.84 * 0.39 * 0.94)}
        self.assertEqual(check_f1_potency(cunning, {1: table[1]}, 0.39, {1: 0.94}), [])
        self.assertEqual(len(check_f1_potency({1: entry(400 * 0.84 * 0.39)}, {1: table[1]}, 0.39, {1: 0.94})), 1)
        self.assertEqual(len(check_ruling_23_potency({1: entry(302.4)}, {1: [(1, 302.4, "direct", 1.07)]})), 1)

    def test_beast_cleave_scales_guard(self):
        consts = dict(R24_BEAST_CLEAVE_PET_SCALES)
        header = "".join(f"    constexpr float {k} = {v}f; // x\n" for k, v in consts.items())
        cpp = "".join(f"HunterData::{k} " for k in consts) + "PassthroughKind::Pet"
        self.assertEqual(check_beast_cleave_type_scales(consts, header, cpp), [])
        self.assertEqual(len(check_beast_cleave_type_scales(
            {**consts, "BEAST_CLEAVE_PET_CUNNING_SCALE": 1.0}, header, cpp)), 1)              # const drifted
        self.assertEqual(len(check_beast_cleave_type_scales(
            consts, header.replace("0.93f", "1.0f"), cpp)), 1)                                 # stale header
        self.assertEqual(len(check_beast_cleave_type_scales(
            consts, header, cpp.replace("PassthroughKind::Pet", ""))), 1)                      # not pet-only
        self.assertEqual(len(check_beast_cleave_type_scales(
            consts, header, cpp.replace("HunterData::BEAST_CLEAVE_PET_FEROCITY_SCALE", ""))), 1)
        rows = {201848: {"Description_Lang_enUS": "Lasts 12 sec."}}
        self.assertEqual(len(check_tooltip_texts(rows, R24_TOOLTIP)), 1)


if __name__ == "__main__":
    unittest.main()
