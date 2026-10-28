"""
Rogue S1a data gate (rogue-rework S1a-HANDOFF WP-A row A5, S1a-WP-BRIEF).

Loads the real rogue DSL package (source/classes/rogue/) and asserts on the BUILT rows (stock base + DSL +
raw_overrides via `build.build_spell_row`), like test_rogue_rg0a.py / test_rogue_rg0b.py. Every check is a pure
function over built rows / package tables; the negative tests prove each can fail (every single expectation is
mutated on its own against a fixture that satisfies all of them).

  1. Talent grid: tab 182 = the 34 talents in the doc's cells, ranks, 76 points, row totals 8/8/8/7/6/10/10/11/5/2/1,
     no arrows, the retired five (276, 278, 279, 2066, 2070) on tab 60800, tab skill line 253, SLA 30800 / 30801.
  2. Row expectations (EXPECT / MUST_SET / MUST_CLEAR): the 47 new rows 203800-203847 (less 203835) and the stock rows
     S1 edits (1329, 14177, 51662, 32645, Master Poisoner, rank markers, proc keys), brief R3 / R4 / R8-R13 / R17.
  3. Family bits on exactly their carriers, new-row masks, the never-bits, every reader mask equal to its `_masks`
     composite (and to the brief's literal value) with its aura / SpellMod op.
  4. Rank amounts the C++ reads (brief section 5), talent rank frames (attributes 464, SpellLevel 9 + 5 x row + rank).
  5. Script bindings / unbinds, proc rows (-14186 re-masked, five removed, every S1 procs_on phase 2), links, custom
     attrs, SDV 1320-1323 (names <= 12 chars) and their attachment, consts.

Run: apps/dbc-tools/.venv/bin/python3 -m pytest apps/dbc-tools/lib/test_rogue_s1.py -q
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import build, dbcfmt, source, spell_tables, state, trainer_state  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.dsl.tooltip import DEFINED_NAME, MAX_NAME_LENGTH  # noqa: E402
from lib.reuse import ReuseContext  # noqa: E402
from lib.test_rogue_rg0a import (  # noqa: E402,F401
    ATTR0_HIDDEN, ATTR0_PASSIVE, ROGUE_DIR, TOOL_ROOT, _i, _u32, effect_mask, m, spell_mask)
from lib.test_rogue_rg0b import check_rows  # noqa: E402

# ---- ids ---------------------------------------------------------------------------------------------------------------

S1_IDS = tuple(i for i in range(203800, 203848) if i != 203835)
S1_RESERVED_ABSENT = (203835, 203848)
(MUT, COLD_BLOOD, HFB, ENVENOM, GARROTE, RUPTURE, SS, SHIV) = (1329, 14177, 51662, 32645, 703, 1943, 1752, 203725)
MH, OH = 203827, 203828
KB, KB_MH, KB_OH, KB_DOT = 203822, 203840, 203841, 203842
PB = 203807
DB_BLEED, DB_TICK = 203829, 203830
BS_BUFF, BS_STRIKE = 203831, 203832
CB_AFTER, SF_HASTE = 203833, 203834
SV_SPLASH, TB_DEBUFF = 203836, 203837
REM_CRIT, REM_POISON = 203838, 203839
OVERKILL_BUFF, DS_ENERGIZE = 203843, 203847
VP_HELPERS = (203844, 203845, 203846)

ONE_HAND_MASK = 41105            # 0xA091: axe 0, mace 4, sword 7, fist 13, dagger 15 (brief R3)
EX3_MH, EX3_OH, EX3_PARENT = 0x600, 0x1000200, 0x1010400
EX3_SUPPRESS_CASTER = 0x10000
EX3_SUPPRESS_TARGET = 0x20000
EX3_ALWAYS_HIT = 0x40000
EX3_IGNORE_CASTER_MODS = 0x20000000
EX3_STACK_PER_CASTER = 0x80
EX2_CANT_CRIT = 0x20000000
HIDDEN_PASSIVE_ATTR = 464
D0_B16, D0_B17, D0_B20 = 0x10000, 0x20000, 0x100000
NEVER_D0 = m.FORBIDDEN_D0 | m.FORBIDDEN_DAGGER_D0 | D0_B16 | D0_B17 | D0_B20
NEVER_D1 = m.FORBIDDEN_D1 | m.FORBIDDEN_DAGGER_D1

APPLY_AURA, TRIGGER_SPELL, ADD_COMBO, WEAPON_PCT, NORM_WEAPON, SCHOOL_DAMAGE, ENERGIZE = 6, 64, 80, 31, 121, 2, 30
AURA_DUMMY, AURA_PERIODIC_DAMAGE, AURA_PERIODIC_DUMMY = 4, 3, 226
AURA_FLAT, AURA_PCT = 107, 108
OP = {"DAMAGE": 0, "DURATION": 1, "EFFECT1": 3, "RANGE": 5, "CRIT": 7, "EFFECT2": 12, "COST": 14, "CRIT_DAMAGE": 15,
      "CHANCE": 18, "ACTIVATION": 19, "DOT": 22}

# ---- grid (S1-HANDOFF section 4; tab 182) ------------------------------------------------------------------------------

TAB = 182
RETIRED_TAB = 60800
RETIRED = (276, 278, 279, 2066, 2070)
# talent id -> (tier, column, rank spell ids or rank count)
GRID = {
    60390: (0, 0, [203800, 203801, 203802]), 270: (0, 1, [14138, 14139, 14140]), 272: (0, 2, [14144, 14148]),
    277: (1, 0, [13733, 13865, 13866]), 273: (1, 1, [14156, 14160, 14161]), 2068: (1, 2, 2),
    269: (2, 0, [14128, 14132, 14135]), 1719: (2, 1, 1), 60391: (2, 2, [203803, 203804]), 382: (2, 3, [14983, 203823]),
    60392: (3, 0, [203805, 203806]), 1762: (3, 1, [31244, 31245]), 268: (3, 3, [14113, 14114, 14115]),
    280: (4, 0, [14177]), 60393: (4, 1, [203807]), 60394: (4, 2, [203808]), 1721: (4, 3, [31208, 31209, 203824]),
    283: (5, 0, [14186, 14190, 14193]), 682: (5, 1, [16513, 16514, 16515]), 60395: (5, 2, [203809, 203810]),
    274: (5, 3, [14158, 14159]),
    281: (6, 0, [203825, 203826]), 1715: (6, 1, [31226, 31227, 58410]), 2065: (6, 2, [51625, 51626]),
    1723: (6, 3, [31380, 31382, 31383]),
    2069: (7, 0, [51634, 51635, 51636]), 60396: (7, 1, [203811, 203812, 203813]), 60397: (7, 2, [203814, 203815]),
    1718: (7, 3, [31234, 31235, 31236]),
    60398: (8, 0, [203816, 203817]), 2071: (8, 1, [51662]), 60399: (8, 2, [203818, 203819]),
    60400: (9, 1, [203820, 203821]), 60401: (10, 1, [203822]),
}
ROW_TOTALS = [8, 8, 8, 7, 6, 10, 10, 11, 5, 2, 1]
SLA_ROWS = {30800: (253, PB), 30801: (253, KB)}

# ---- family bits (brief section 4) ---------------------------------------------------------------------------------------

POISON_GROUP = 0x80000
D2_CARRIERS = {   # (bit const, value): exact carrier set
    "KINGSBANE_DOT": (0x200, {KB_DOT}),
    "POISON_STRIKE": (0x400, {KB_MH, KB_OH}),
    "DOOMBLADE": (0x800, {DB_BLEED, DB_TICK}),
    "SHATTERING_VIAL": (0x2000, {SV_SPLASH}),
    "POISON_BOMB": (0x4000, {PB}),
    "FINISHER_GROUP": (0x40000, {2098, 5171, 8647, 1943, 408, 26679, 32645, 204148, 204169, 204170, 203959, 203969, 51690}),   # + S2 Death from Above, S3 Between the Eyes / En Garde / Killing Spree
    "DIRECT_BUILDER_GROUP": (0x80000, {1752, 53, 8676, 1776, 14278, SHIV, 14251, 203958}),   # + S3 Riposte, Pistol Shot
    "MUTILATE_HANDS": (0x100000, {MH, OH}),
    "GHOSTLY_STRIKE_ID": (0x200000, {14278}),
    "KINGSBANE_PARENT": (0x400000, {KB}),     # review M1: Cold Blood's RANGE reader names the Kingsbane parent
}
POISON_GROUP_NEW = {KB_MH, KB_OH, KB_DOT, SV_SPLASH, BS_STRIKE}       # + existing d1 b19 carriers
FULL_MASKS = {   # full spell masks of the new carrier rows (brief section 4)
    MH: (0, 0, 0x100000), OH: (0, 0, 0x100000), KB_MH: (0, 0x80000, 0x400), KB_OH: (0, 0x80000, 0x400),
    KB_DOT: (0, 0x80000, 0x200), DB_BLEED: (0, 0, 0x800), DB_TICK: (0, 0, 0x800), SV_SPLASH: (0, 0x80000, 0x2000),
    PB: (0, 0, 0x4000), BS_STRIKE: (0, 0x80000, 0), KB: (0, 0, 0x400000),
}
# the _masks composites, literal values from the brief (the test pins both the module and the rows)
COMPOSITES = {
    "LETHALITY_READ": (0x10002000, 0x40000, 0x180400),
    "COLD_BLOOD_READ": (0x20000, 0x40109, 0x180400),
    "COLD_BLOOD_RANGE_READ": (0x20000, 0x240109, 0x580400),   # + Mutilate parent d1 b21 + Kingsbane parent d2 b22 (M1)
    "REMORSELESS_READ": (0x206, 0, 0x300000),
    "REMORSELESS_POISON_READ": (0, 0x80000, 0),
    "MUTILATE_HAND_BITS": (0, 0, 0x100000),
    "SEAL_FATE_PROC_READ": (0, 0, 0x80000),
    "SEAL_FATE_DAMAGE_READ": (0x20000, 0x1, 0),
    "SEAL_FATE_DOT_READ": (0x100000, 0, 0),
    "RUTHLESSNESS_READ": (0, 0, 0x40000),
    "RUTHLESSNESS_READ_S3": (0, 0x800000, 0x40000),   # S3 ruling: + Killing Spree's strikes (d1 b23)
    "FIND_WEAKNESS_READ": (0x100, 0xC0100, 0x1C0600),
    "POISON_DAMAGE_READ": (0, 0x80000, 0),
    "VILE_POISONS_MIND_NUMBING_READ": (0x8000, 0, 0),
    "VILE_POISONS_WOUND_DURATION_READ": (0x10000000, 0, 0),
    "VENOMOUS_FAN_READ": (0, 0x40000, 0),
    "MURDER_DOT_READ": (0x100, 0, 0),
    "TOXIC_BLADE_SHIV_READ": (0x20000000, 0, 0),
    "WOUND_BLEED_READ_S1": (0x100100, 0, 0x800),
    "HUNGER_FOR_BLOOD_READ": (0x110100, 0, 0xA00),
    # S2 (WP-BRIEF section 4) extends three S1 readers with d2 b7 | b8 | b17 / d2 b12; the S1 module constants stay
    "FIND_WEAKNESS_READ_S2": (0x100, 0xC0100, 0x1E0780),
    # S3 extends the three "every ability" readers by name (U65): + Between the Eyes d2 b5 and Blade Rush d2 b15
    "COLD_BLOOD_READ_S3": (0x20000, 0x40109, 0x188420),
    "COLD_BLOOD_RANGE_READ_S3": (0x20000, 0x240109, 0x588420),
    "FIND_WEAKNESS_READ_S3": (0x100, 0xC0100, 0x1E87A0),
    "WOUND_BLEED_READ_S2": (0x100100, 0, 0x1800),
    "HUNGER_FOR_BLOOD_READ_S2": (0x110100, 0, 0x1A00),
    "IMPROVED_POISONS_READ": (0, 0, 0x2),
    "BLINDSIDE_COST_READ": (0x2, 0, 0),
}
# (spell id, effect 1-based, composite, aura, SpellMod op or None)   -- brief section 4 "Reader masks"
READERS = (
    [(i, 1, "LETHALITY_READ", AURA_PCT, OP["CRIT_DAMAGE"]) for i in (14128, 14132, 14135)]
    + [(COLD_BLOOD, 1, "COLD_BLOOD_READ_S3", AURA_FLAT, OP["CRIT"]), (COLD_BLOOD, 2, "COLD_BLOOD_READ_S3", AURA_PCT, OP["DAMAGE"]),
       (COLD_BLOOD, 3, "COLD_BLOOD_RANGE_READ_S3", AURA_FLAT, OP["RANGE"])]
    + [(REM_CRIT, 1, "REMORSELESS_READ", AURA_FLAT, OP["CRIT"]),
       (REM_POISON, 1, "REMORSELESS_POISON_READ", AURA_PCT, OP["DAMAGE"]),
       (REM_POISON, 2, "REMORSELESS_POISON_READ", AURA_PCT, OP["DOT"])]
    + [(i, 2, "MUTILATE_HAND_BITS", None, None) for i in (13733, 13865, 13866)]
    + [(i, 2, "SEAL_FATE_DAMAGE_READ", AURA_PCT, OP["DAMAGE"]) for i in (14186, 14190, 14193)]
    + [(i, 3, "SEAL_FATE_DOT_READ", AURA_PCT, OP["DOT"]) for i in (14186, 14190, 14193)]
    + [(i, 1, "RUTHLESSNESS_READ_S3", AURA_PCT, OP["DAMAGE"]) for i in (14156, 14160, 14161)]
    + [(i, 2, "RUTHLESSNESS_READ_S3", AURA_PCT, OP["DOT"]) for i in (14156, 14160, 14161)]
    + [(i, 1, "FIND_WEAKNESS_READ_S3", AURA_FLAT, OP["CRIT"]) for i in (31234, 31235, 31236)]
    + [(i, 1, "POISON_DAMAGE_READ", AURA_PCT, OP["DAMAGE"]) for i in (16513, 16514, 16515)]
    + [(i, 2, "POISON_DAMAGE_READ", AURA_PCT, OP["DOT"]) for i in (16513, 16514, 16515)]
    + [(i, 3, "VILE_POISONS_MIND_NUMBING_READ", AURA_PCT, OP["EFFECT1"]) for i in (16513, 16514, 16515)]
    + [(i, 1, "VILE_POISONS_WOUND_DURATION_READ", AURA_FLAT, OP["DURATION"]) for i in VP_HELPERS]
    + [(i, 1, "VENOMOUS_FAN_READ", AURA_PCT, OP["DAMAGE"]) for i in (203809, 203810)]
    + [(i, 2, "MURDER_DOT_READ", AURA_PCT, OP["DOT"]) for i in (14158, 14159)]
    + [(i, 1, "TOXIC_BLADE_SHIV_READ", AURA_FLAT, OP["EFFECT2"]) for i in (203816, 203817)]
    + [(TB_DEBUFF, 1, "POISON_DAMAGE_READ", 271, None), (13218, 1, "WOUND_BLEED_READ_S2", 271, None)]
    + [(HFB, 1, "HUNGER_FOR_BLOOD_READ_S2", AURA_PCT, OP["ACTIVATION"])]
    + [(i, 1, "IMPROVED_POISONS_READ", AURA_FLAT, OP["CHANCE"]) for i in (14113, 14114, 14115)]
    + [(BS_BUFF, 1, "BLINDSIDE_COST_READ", AURA_PCT, OP["COST"]), (ENVENOM, 2, "POISON_DAMAGE_READ", AURA_FLAT, OP["CRIT"])]
)

# ---- rank amounts the C++ reads (brief section 5 / 13): (id, effect 1-based, aura, value) ------------------------------------
AMOUNTS = (
    [(i, 1, AURA_DUMMY, v) for i, v in zip((203803, 203804), (15, 30))]            # Doomblade
    + [(i, 1, AURA_DUMMY, v) for i, v in zip((203805, 203806), (10, 20))]          # Blindside
    + [(i, 1, AURA_DUMMY, v) for i, v in zip((31244, 31245), (15, 30))]            # Quick Recovery
    + [(203808, 1, AURA_DUMMY, 5)]                                                  # Shattering Vial
    + [(i, 2, AURA_DUMMY, 10) for i in (31208, 31209, 203824)]                     # Fleet Footed per cp
    + [(i, 1, AURA_DUMMY, v) for i, v in zip((203825, 203826), (20, 40))]          # Overkill
    + [(i, 1, AURA_DUMMY, v) for i, v in zip((51625, 51626), (50, 100))]           # Deadly Brew
    + [(i, 1, AURA_DUMMY, v) for i, v in zip((203811, 203812, 203813), (10, 20, 30))]    # Zoldyck
    + [(i, 1, AURA_DUMMY, v) for i, v in zip((203814, 203815), (4, 8))]            # Cut Throat
    + [(i, 1, AURA_DUMMY, v) for i, v in zip((203818, 203819), (1, 2))]            # Indiscriminate Carnage
    + [(i, 1, AURA_DUMMY, v) for i, v in zip((203820, 203821), (5, 10))]           # Dashing Scoundrel
    + [(i, 1, AURA_DUMMY, v) for i, v in zip((14144, 14148), (25, 50))]            # Remorseless markers (R12)
    + [(i, 3, AURA_DUMMY, v) for i, v in zip((14156, 14160, 14161), (33, 66, 100))]  # Ruthlessness (R13)
    + [(i, 1, 193, v) for i, v in zip((203800, 203801, 203802), (1, 2, 3))]        # Quick Pace (R11)
    + [(i, 1, 306, v) for i, v in zip((14138, 14139, 14140), (2, 4, 6))]           # Malice
    + [(i, 1, AURA_PCT, v) for i, v in zip((203809, 203810), (15, 30))]            # Venomous Fan
    + [(i, 1, AURA_FLAT, v) for i, v in zip((203816, 203817), (1, 2))]             # Toxic Blade
    + [(203823, 1, 35, 30)]                                                         # Vigor r2 (R11)
    + [(i, 1, 172, v) for i, v in zip((31208, 31209, 203824), (3, 6, 10))]         # Fleet Footed (R11)
    + [(i, 1, AURA_PCT, v) for i, v in zip((14156, 14160, 14161), (1, 2, 3))]      # Ruthlessness pct DAMAGE
    + [(i, 2, AURA_PCT, v) for i, v in zip((14156, 14160, 14161), (1, 2, 3))]      # Ruthlessness pct DOT
    + [(COLD_BLOOD, 1, AURA_FLAT, 100), (COLD_BLOOD, 2, AURA_PCT, 20), (COLD_BLOOD, 3, AURA_FLAT, 5)]
    + [(HFB, 1, AURA_PCT, -50), (BS_BUFF, 1, AURA_PCT, -100)]
    + [(CB_AFTER, 1, 52, 4), (SF_HASTE, 1, 31, 70), (TB_DEBUFF, 1, 271, 10)]       # R10: 52, not 57
    + [(REM_CRIT, 1, AURA_FLAT, 25), (REM_POISON, 1, AURA_PCT, 10), (REM_POISON, 2, AURA_PCT, 10)]
    + [(OVERKILL_BUFF, 1, 110, 20), (DS_ENERGIZE, 1, None, 1)]
    + [(i, 1, AURA_FLAT, v) for i, v in zip(VP_HELPERS, (1000, 2000, 3000))]       # Vile Poisons helpers
    + [(ENVENOM, 2, AURA_FLAT, 0)]                                                  # Dashing Scoundrel hook, base 0
)
# the rank-frame rows (talent ranks): id -> (talent row, rank); hidden passives, attributes 464 (brief section 10.15)
RANK_FRAMES = {}
for _row, _ids in ((0, (203800, 203801, 203802)), (2, (203803, 203804)), (3, (203805, 203806)), (4, (203808,)),
                   (5, (203809, 203810)), (6, (203825, 203826)), (7, (203811, 203812, 203813, 203814, 203815)),
                   (8, (203816, 203817, 203818, 203819)), (9, (203820, 203821))):
    for _rank, _id in enumerate(_ids, 1):
        RANK_FRAMES[_id] = (_row, _rank)
# talents with two rank groups sharing a row: Zoldyck r1-3 then Cut Throat r1-2 (ranks restart), IC after Toxic
RANK_FRAMES.update({203814: (7, 1), 203815: (7, 2), 203816: (8, 1), 203817: (8, 2), 203818: (8, 1), 203819: (8, 2)})

SCRIPTS = {
    (MUT, "spell_rog_mutilate_rework"), (MH, "spell_rog_dual_strike_hand"), (OH, "spell_rog_dual_strike_hand"),
    (KB, "spell_rog_kingsbane"), (KB_DOT, "spell_rog_kingsbane_dot"), (DB_BLEED, "spell_rog_doomblade"),
    (SS, "spell_rog_sinister_strike_blindside"), (ENVENOM, "spell_rog_envenom_assassination"),
    (RUPTURE, "spell_rog_rupture_carnage"), (GARROTE, "spell_rog_garrote_cut_throat"),
    (HFB, "spell_rog_hunger_for_blood"), (PB, "spell_rog_poison_bomb"), (SV_SPLASH, "spell_rog_shattering_vial"),
    (REM_CRIT, "spell_rog_remorseless_attacks_rework"), (COLD_BLOOD, "spell_rog_cold_blood_rework"),
    (-51634, "spell_rog_focused_attacks_rework"), (13218, "spell_rog_wound_poison_mastery"),
    (203846, "spell_rog_vile_poisons_mastery"),
}
UNBOUND = {
    (-1329, "spell_rog_mutilate"), (14177, "spell_rog_cold_blood"), (-51634, "spell_rog_focused_attacks"),
    (-14143, "spell_rog_remorseless_attacks"), (-31244, "spell_rog_quick_recovery"),
    (-51625, "spell_rog_deadly_brew"), (-51664, "spell_rog_cut_to_the_chase"), (-51627, "spell_rog_turn_the_tables"),
    (52910, "spell_rog_turn_the_tables_proc"), (52914, "spell_rog_turn_the_tables_proc"),
    (52915, "spell_rog_turn_the_tables_proc"),
}
PROC_REMOVED = (-14156, -31244, -51625, -51664, -51627)
PROC_MARKER_RANKS = (14156, 14160, 14161, 31244, 31245, 51625, 51626, 14144, 14148)   # R8 / R12: ProcTypeMask 0
LINKS = {(16513, 203844, 2), (16514, 203845, 2), (16515, 203846, 2)}
SDV_ATTACH = {1320: (203701, 203702, 203703, ENVENOM), 1321: (51723,), 1322: (GARROTE, RUPTURE), 1323: (2098, 26679)}
CONSTS = {
    "MUTILATE_PER_POISON_PCT": 15, "MUTILATE_NORMALIZED_SPEED_MS": 1700, "RUTHLESSNESS_ICD_MS": 9000,
    "DEADLY_BREW_ICD_MS": 4000, "DASHING_SCOUNDREL_ICD_MS": 1000, "DOOMBLADE_TICKS": 4,
    "DOOMBLADE_CAPSTONE_PCT_PER_BLEED": 5, "KINGSBANE_STACK_PCT": 5, "KINGSBANE_MAX_STACKS": 50,
    "KINGSBANE_ENVENOM_STACKS": 2, "POISON_BOMB_IMPACT_STACKS": 2, "POISON_BOMB_PULSES": 3,
    "POISON_BOMB_PULSE_MS": 2000, "POISON_BOMB_RADIUS_YD": 8, "INDISCRIMINATE_CARNAGE_RADIUS_YD": 8,
    "ZOLDYCK_HEALTH_PCT": 30, "SEAL_FATE_CAPSTONE_PCT_PER_CP": 20, "OVERKILL_TAIL_MS": 20000,
    "QUICK_RECOVERY_ENERGY": 10, "VENOMOUS_FAN_POISON_MULT": 2, "WOUND_MASTERY_DIVISOR": 2,
}

TEXTS = {
    DB_BLEED: "Bleeding.", TB_DEBUFF: "Taking more damage from the rogue's poisons.",
    REM_CRIT: "Your next strike has a higher chance to be a critical strike.", REM_POISON: "Poison damage increased.",
    OVERKILL_BUFF: "Energy regeneration increased.", CB_AFTER: "Critical strike chance increased.",
    SF_HASTE: "Movement speed increased.",
}


def value_of(row: dict, effect: int) -> int:
    """The engine's CalcValue at level-independent terms: stored base points + 1 when DieSides is 1."""
    base = _i(row, f"EffectBasePoints_{effect}")
    return base + (1 if _i(row, f"EffectDieSides_{effect}") == 1 else 0)


# ---- expectations ------------------------------------------------------------------------------------------------------

def expectations(idx: dict) -> tuple[dict, dict, dict]:
    """(EXPECT, MUST_SET, MUST_CLEAR). `idx` carries reuse-minted indices: infinite, d<ms> durations, r30."""
    inf = idx["infinite"]
    one_hand = {"EquippedItemClass": 2, "EquippedItemSubclass": ONE_HAND_MASK}
    exact = {
        # ---- Mutilate parent (R3, S1-HANDOFF 2,1)
        MUT: {**one_hand, "ManaCost": 45, "SpellLevel": 20, "BaseLevel": 20, "StartRecoveryCategory": 133,
              "StartRecoveryTime": 1000},
        MH: {**one_hand, "Effect_1": WEAPON_PCT, "Effect_2": NORM_WEAPON, "Effect_3": 0, "SpellLevel": 20,
             "BaseLevel": 20, "DefenseType": 2, "RangeIndex": idx["melee"], "Speed": 0,
             "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0x100000},
        OH: {**one_hand, "Effect_1": WEAPON_PCT, "Effect_2": NORM_WEAPON, "Effect_3": 0, "SpellLevel": 20,
             "BaseLevel": 20, "DefenseType": 2, "RangeIndex": idx["melee"], "Speed": 0,
             "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0x100000},
        # ---- Kingsbane
        KB: {**one_hand, "ManaCost": 35, "RecoveryTime": 60000, "StartRecoveryCategory": 133, "StartRecoveryTime": 1000,
             "SpellLevel": 60, "BaseLevel": 60, "RangeIndex": idx["melee"], "SpellVisualID_1": 90250,
             "Effect_1": ADD_COMBO, "EffectBasePoints_1": 0, "Effect_2": TRIGGER_SPELL, "EffectTriggerSpell_2": KB_MH,
             "Effect_3": TRIGGER_SPELL, "EffectTriggerSpell_3": KB_OH,
             "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0x400000},
        KB_MH: {**one_hand, "Effect_1": WEAPON_PCT, "SpellLevel": 60, "BaseLevel": 60, "DefenseType": 2,
                "SpellClassMask_1": 0, "SpellClassMask_2": 0x80000, "SpellClassMask_3": 0x400},
        KB_OH: {**one_hand, "Effect_1": WEAPON_PCT, "SpellLevel": 60, "BaseLevel": 60, "DefenseType": 2,
                "SpellClassMask_1": 0, "SpellClassMask_2": 0x80000, "SpellClassMask_3": 0x400},
        KB_DOT: {"Effect_1": APPLY_AURA, "EffectAura_1": AURA_PERIODIC_DAMAGE, "EffectAuraPeriod_1": 2000,
                 "DispelType": 4, "CumulativeAura": 0, "ProcTypeMask": 0, "ProcCharges": 0, "SpellLevel": 60,
                 "BaseLevel": 60, "DurationIndex": idx["d14000"], "EquippedItemClass": -1, "SpellIconID": 1637,
                 "SpellClassMask_1": 0, "SpellClassMask_2": 0x80000, "SpellClassMask_3": 0x200},
        # ---- Poison Bomb (R4)
        PB: {"ManaCost": 30, "RecoveryTime": 30000, "StartRecoveryCategory": 133, "StartRecoveryTime": 1000, "Speed": 18,
             "RangeIndex": idx["r30"], "SpellVisualID_1": 90251, "DurationIndex": idx["d6000"],
             "Effect_1": 27, "EffectAura_1": AURA_DUMMY, "ImplicitTargetA_1": 53, "ImplicitTargetB_1": 16,
             "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0x4000},
        # ---- Doomblade (R17)
        DB_BLEED: {"Effect_1": APPLY_AURA, "EffectAura_1": AURA_PERIODIC_DUMMY, "EffectAuraPeriod_1": 2000,
                   "DurationIndex": idx["d8000"], "Mechanic": 15, "EquippedItemClass": -1, "SpellIconID": 1501,
                   "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0x800},
        DB_TICK: {"Effect_1": SCHOOL_DAMAGE, "Mechanic": 15, "DefenseType": 0, "EquippedItemClass": -1,
                  "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0x800},
        # ---- Blindside (R9, R17)
        BS_BUFF: {"DurationIndex": idx["d12000"], "Effect_1": APPLY_AURA, "EffectAura_1": AURA_PCT,
                  "EffectMiscValue_1": OP["COST"], "EquippedItemClass": -1, "SpellIconID": 2126,
                  "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0},
        BS_STRIKE: {"Effect_1": SCHOOL_DAMAGE, "Effect_2": 0, "DefenseType": 1, "EquippedItemClass": -1,
                    "SpellClassMask_1": 0, "SpellClassMask_2": 0x80000, "SpellClassMask_3": 0},
        CB_AFTER: {"Effect_1": APPLY_AURA, "EffectAura_1": 52, "Effect_2": 0, "EffectMiscValue_1": 0,
                   "DurationIndex": idx["d15000"], "EquippedItemClass": -1, "SpellIconID": 32},
        SF_HASTE: {"Effect_1": APPLY_AURA, "EffectAura_1": 31, "DurationIndex": idx["d4000"],
                   "EquippedItemClass": -1, "SpellIconID": 55},
        SV_SPLASH: {"Effect_2": 0, "Effect_1": APPLY_AURA, "EffectAura_1": AURA_PERIODIC_DAMAGE,
                    "EffectAuraPeriod_1": 1000, "DurationIndex": idx["d2000"], "DispelType": 0, "SpellLevel": 30,
                    "EquippedItemClass": -1,
                    "SpellClassMask_1": 0, "SpellClassMask_2": 0x80000, "SpellClassMask_3": 0x2000},
        TB_DEBUFF: {"Effect_1": APPLY_AURA, "EffectAura_1": 271, "DurationIndex": idx["d8000"],
                    "ImplicitTargetA_1": 6, "EquippedItemClass": -1, "SpellIconID": 2269},
        REM_CRIT: {"Effect_1": APPLY_AURA, "EffectAura_1": AURA_FLAT, "EffectMiscValue_1": OP["CRIT"],
                   "DurationIndex": idx["d20000"], "ProcTypeMask": 87376, "ProcCharges": 1, "ProcChance": 100,
                   "EquippedItemClass": -1, "SpellIconID": 695},
        REM_POISON: {"Effect_1": APPLY_AURA, "EffectAura_1": AURA_PCT, "EffectMiscValue_1": OP["DAMAGE"],
                     "Effect_2": APPLY_AURA, "EffectAura_2": AURA_PCT, "EffectMiscValue_2": OP["DOT"],
                     "DurationIndex": idx["d10000"], "EquippedItemClass": -1, "SpellIconID": 695},
        OVERKILL_BUFF: {"Effect_1": APPLY_AURA, "EffectAura_1": 110, "EffectMiscValue_1": 3, "DurationIndex": inf,
                        "EquippedItemClass": -1, "SpellIconID": 2285},
        DS_ENERGIZE: {"Effect_1": ENERGIZE, "EffectMiscValue_1": 3, "ImplicitTargetA_1": 1, "EquippedItemClass": -1},
        203844: {"Effect_1": APPLY_AURA, "EffectAura_1": AURA_FLAT, "EffectMiscValue_1": OP["DURATION"]},
        203845: {"Effect_1": APPLY_AURA, "EffectAura_1": AURA_FLAT, "EffectMiscValue_1": OP["DURATION"]},
        203846: {"Effect_1": APPLY_AURA, "EffectAura_1": AURA_FLAT, "EffectMiscValue_1": OP["DURATION"],
                 "Effect_2": APPLY_AURA, "EffectAura_2": AURA_PERIODIC_DUMMY, "EffectAuraPeriod_2": 1000},
        # ---- stock rows edited in place
        COLD_BLOOD: {"Attributes": 327696, "StartRecoveryCategory": 0, "StartRecoveryTime": 0, "ProcTypeMask": 87376,
                     "ProcCharges": 1, "ProcChance": 100},
        HFB: {"Effect_1": APPLY_AURA, "EffectAura_1": AURA_PCT, "EffectMiscValue_1": OP["ACTIVATION"],
              "Effect_2": 0, "Effect_3": 0, "TargetAuraState": 0, "StartRecoveryCategory": 0, "StartRecoveryTime": 0,
              "ManaCost": 0, "RecoveryTime": 120000, "DurationIndex": idx["d10000"], "DispelType": 9},
        ENVENOM: {"Effect_2": APPLY_AURA, "EffectAura_2": AURA_FLAT, "EffectMiscValue_2": OP["CRIT"],
                  "ImplicitTargetA_2": 1},
        31226: {"SpellIconID": 1960, "Effect_1": APPLY_AURA, "EffectAura_1": 231, "Effect_2": APPLY_AURA,
                "EffectAura_2": 246, "EffectMiscValue_2": 4, "EffectBasePoints_3": 32, "EffectDieSides_3": 1},
        31227: {"SpellIconID": 1960, "Effect_1": APPLY_AURA, "EffectAura_1": 231, "Effect_2": APPLY_AURA,
                "EffectAura_2": 246, "EffectMiscValue_2": 4, "EffectBasePoints_3": 65, "EffectDieSides_3": 1},
        58410: {"SpellIconID": 1960, "Effect_1": APPLY_AURA, "EffectAura_1": 231, "Effect_2": APPLY_AURA,
                "EffectAura_2": 246, "EffectMiscValue_2": 4, "EffectBasePoints_3": 99, "EffectDieSides_3": 1},
        14186: {"ProcChance": 33}, 14190: {"ProcChance": 66}, 14193: {"ProcChance": 100},
        51634: {"ProcChance": 33}, 51635: {"ProcChance": 66}, 51636: {"ProcChance": 100},
        51637: {"Effect_1": ENERGIZE},
    }
    for rid in PROC_MARKER_RANKS:                           # R8 / R12: stale DBC proc keys cleared
        exact.setdefault(rid, {}).update({"ProcTypeMask": 0, "ProcChance": 101})
    for sid in (203844, 203845, 203846):
        exact[sid].update({"EquippedItemClass": -1})
    for sid, (row, rank) in RANK_FRAMES.items():            # hidden passive frames (brief section 10.15)
        exact.setdefault(sid, {}).update({"Attributes": HIDDEN_PASSIVE_ATTR, "EquippedItemClass": -1,
                                          "SpellLevel": 9 + 5 * row + rank,
                                          "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0})
    must_set = {
        MUT: {"AttributesEx3": EX3_PARENT, "SpellClassMask_2": 0x200000},   # 1329 keeps d1 b21, never d1 b1/b2
        MH: {"AttributesEx3": EX3_MH, "Attributes": ATTR0_HIDDEN},
        OH: {"AttributesEx3": EX3_OH, "Attributes": ATTR0_HIDDEN},
        KB_MH: {"AttributesEx3": EX3_MH, "Attributes": ATTR0_HIDDEN},
        KB_OH: {"AttributesEx3": EX3_OH, "Attributes": ATTR0_HIDDEN},
        KB_DOT: {"AttributesEx3": EX3_STACK_PER_CASTER},
        PB: {"AttributesEx3": EX3_SUPPRESS_TARGET | EX3_SUPPRESS_CASTER},
        DB_BLEED: {"AttributesEx3": EX3_STACK_PER_CASTER},
        DB_TICK: {"AttributesEx3": EX3_IGNORE_CASTER_MODS | EX3_ALWAYS_HIT | EX3_SUPPRESS_CASTER,
                  "AttributesEx2": EX2_CANT_CRIT, "Attributes": ATTR0_HIDDEN},
        BS_STRIKE: {"AttributesEx2": EX2_CANT_CRIT, "AttributesEx3": EX3_SUPPRESS_CASTER | EX3_ALWAYS_HIT,
                    "Attributes": ATTR0_HIDDEN},
        SV_SPLASH: {"AttributesEx3": EX3_SUPPRESS_CASTER},
        TB_DEBUFF: {"AttributesEx3": EX3_STACK_PER_CASTER},
        DS_ENERGIZE: {"Attributes": ATTR0_HIDDEN},
    }
    for sid in VP_HELPERS:
        must_set[sid] = {"Attributes": ATTR0_PASSIVE | ATTR0_HIDDEN}
    for sid in (2098, 5171, 8647, 1943, 408, 26679, ENVENOM):
        must_set[sid] = {"SpellClassMask_3": 0x40000}
    for sid in (1752, 53, 8676, 1776, 14278, SHIV):
        must_set[sid] = {"SpellClassMask_3": 0x80000}
    must_set[14278]["SpellClassMask_3"] |= 0x200000
    must_set[14278]["SpellClassMask_1"] = 0x40000000          # Ghostly Strike's own d0 b30 stays
    for sid in (KB_MH, KB_OH, KB_DOT, SV_SPLASH, BS_STRIKE):
        must_set.setdefault(sid, {})["SpellClassMask_2"] = POISON_GROUP
    must_clear = {
        MUT: {"SpellClassMask_2": 0x6},
        COLD_BLOOD: {"Attributes": 0x02000000 | ATTR0_PASSIVE | ATTR0_HIDDEN},
        HFB: {"Attributes": ATTR0_PASSIVE | ATTR0_HIDDEN},
        KB: {"Attributes": ATTR0_HIDDEN},
        PB: {"Attributes": ATTR0_HIDDEN},
        KB_DOT: {"Attributes": ATTR0_PASSIVE | ATTR0_HIDDEN},
        DB_BLEED: {"Attributes": ATTR0_PASSIVE | ATTR0_HIDDEN},
        TB_DEBUFF: {"Attributes": ATTR0_PASSIVE | ATTR0_HIDDEN},
        BS_BUFF: {"Attributes": ATTR0_PASSIVE | ATTR0_HIDDEN},
        CB_AFTER: {"Attributes": ATTR0_PASSIVE | ATTR0_HIDDEN},
        SF_HASTE: {"Attributes": ATTR0_PASSIVE | ATTR0_HIDDEN},
        REM_CRIT: {"Attributes": ATTR0_PASSIVE | ATTR0_HIDDEN},
        REM_POISON: {"Attributes": ATTR0_PASSIVE | ATTR0_HIDDEN},
        OVERKILL_BUFF: {"Attributes": ATTR0_PASSIVE | ATTR0_HIDDEN},
    }
    for sid in (MH, OH, KB_MH, KB_OH):                      # never d1 b1/b2/b3 or the dagger bits on a hand (R3)
        must_clear[sid] = {"SpellClassMask_1": NEVER_D0, "SpellClassMask_2": NEVER_D1}
    must_clear[DB_BLEED] = {**must_clear[DB_BLEED], "SpellClassMask_1": D0_B20}   # d0 b20 is Rupture's alone
    must_clear[DB_TICK] = {"SpellClassMask_1": D0_B20}
    must_clear[BS_STRIKE] = {"SpellClassMask_3": 0x400}     # R9: not d2 b10
    return exact, must_set, must_clear


def check_value_cases(rows: dict, cases) -> list[str]:
    """(id, effect, aura or None, value): the effect applies that aura (when given) with that engine value."""
    bad = []
    for sid, eff, aura, value in cases:
        row = rows.get(sid)
        if row is None:
            bad.append(f"{sid}: not built")
            continue
        if aura is not None and _i(row, f"EffectAura_{eff}") != aura:
            bad.append(f"{sid}: effect {eff} aura {row.get(f'EffectAura_{eff}')!r}, expected {aura}")
        if value_of(row, eff) != value:
            bad.append(f"{sid}: effect {eff} value {value_of(row, eff)}, expected {value}")
    return bad


def check_effect_order(rows: dict) -> list[str]:
    """Mutilate parent: an ADD_COMBO_POINTS bp 1 (= 2), triggers 203827 / 203828 (R3); hand frames copy the stock
    5374 / 27576 Ex3 (RG0b C1 0x200 kept)."""
    row = rows.get(MUT)
    if row is None:
        return [f"{MUT}: not built"]
    bad = []
    triggers = {_i(row, f"EffectTriggerSpell_{n}") for n in (1, 2, 3) if _i(row, f"Effect_{n}") == TRIGGER_SPELL}
    if triggers != {MH, OH}:
        bad.append(f"{MUT}: trigger spells {sorted(triggers)}, expected {[MH, OH]}")
    combo = [n for n in (1, 2, 3) if _i(row, f"Effect_{n}") == ADD_COMBO]
    if len(combo) != 1 or value_of(row, combo[0]) != 2:
        bad.append(f"{MUT}: ADD_COMBO_POINTS effects {combo} (want one worth 2 points)")
    return bad


def check_texts(rows: dict) -> list[str]:
    bad = []
    for sid, text in TEXTS.items():
        got = rows.get(sid, {}).get("AuraDescription_Lang_enUS")
        if got != text:
            bad.append(f"{sid}: aura text {got!r}, expected {text!r}")
    for sid in (BS_BUFF, HFB, KB_DOT):
        if not str(rows.get(sid, {}).get("AuraDescription_Lang_enUS") or "").strip():
            bad.append(f"{sid}: no aura text")
    return bad


# ---- carriers, masks, readers --------------------------------------------------------------------------------------------

def check_carriers(rows: dict) -> list[str]:
    bad = []
    for name, (bit, want) in D2_CARRIERS.items():
        have = {sid for sid, r in rows.items() if spell_mask(r)[2] & bit}
        if have != want:
            bad.append(f"d2 {name} {bit:#x}: carriers {sorted(have)}, expected exactly {sorted(want)}")
    have = {sid for sid, r in rows.items() if spell_mask(r)[1] & POISON_GROUP}
    for sid in sorted(POISON_GROUP_NEW - have):
        bad.append(f"d1 b19 POISON_GROUP: {sid} lacks the bit")
    return bad


def check_new_masks(rows: dict, s1_ids) -> list[str]:
    """Every new row: SpellClassSet 8; spell masks exactly the section-4 carrier masks, zero otherwise; no never-bit."""
    bad = []
    for sid in s1_ids:
        r = rows.get(sid)
        if r is None:
            continue
        if _i(r, "SpellClassSet") != 8:
            bad.append(f"{sid}: SpellClassSet {r.get('SpellClassSet')!r}, expected 8")
        mask = spell_mask(r)
        want = FULL_MASKS.get(sid, (0, 0, 0))
        if mask != want:
            bad.append(f"{sid}: spell mask ({', '.join(hex(w) for w in mask)}), expected "
                       f"({', '.join(hex(w) for w in want)})")
        if mask[0] & NEVER_D0 or mask[1] & NEVER_D1:
            bad.append(f"{sid}: spell mask holds never-bits")
    return bad


def check_readers(rows: dict) -> list[str]:
    bad = []
    for sid, eff, comp, aura, op in READERS:
        r = rows.get(sid)
        if r is None:
            bad.append(f"{sid}: not built")
            continue
        want = COMPOSITES[comp]
        got = effect_mask(r, eff)
        if got != want:
            bad.append(f"{sid}: effect {eff} mask {tuple(hex(w) for w in got)}, expected {comp} "
                       f"{tuple(hex(w) for w in want)}")
        if aura is not None and _i(r, f"EffectAura_{eff}") != aura:
            bad.append(f"{sid}: effect {eff} aura {r.get(f'EffectAura_{eff}')!r}, expected {aura}")
        if op is not None and _i(r, f"EffectMiscValue_{eff}") != op:
            bad.append(f"{sid}: effect {eff} SpellMod op {r.get(f'EffectMiscValue_{eff}')!r}, expected {op}")
    return bad


def check_composites(module) -> list[str]:
    bad = []
    for name, want in COMPOSITES.items():
        got = tuple(getattr(module, name, ()))
        if got != want:
            bad.append(f"_masks.{name} = {tuple(hex(w) for w in got)}, expected {tuple(hex(w) for w in want)}")
    return bad


def check_s1_id_set(rows: dict) -> list[str]:
    have = {sid for sid in rows if 203800 <= sid <= 203869}
    bad = []
    for sid in sorted(set(S1_IDS) - have):
        bad.append(f"{sid}: S1 row not built")
    for sid in sorted(have - set(S1_IDS)):
        bad.append(f"{sid}: unexpected S1 row (203835 / 203848 are not built, 203849-203869 are spare)")
    return bad


def check_visibility(rows: dict) -> list[str]:
    """Hands, tick, strike, helpers and energize hidden; talent-rank frames hidden passives are in the row table."""
    bad = []
    for sid in (MH, OH, KB_MH, KB_OH, DB_TICK, BS_STRIKE, DS_ENERGIZE):
        if not _u32(rows.get(sid, {}).get("Attributes")) & ATTR0_HIDDEN:
            bad.append(f"{sid}: not hidden (Attributes 0x80)")
    return bad


# ---- grid / tables -----------------------------------------------------------------------------------------------------

def check_grid(talents: list[dict], retired: list[dict], tabs: list[dict], tab_text: str) -> list[str]:
    bad = []
    mine = [t for t in talents if int(t["tab_id"]) == TAB]
    seen = {}
    for t in mine:
        if int(t["id"]) in seen:
            bad.append(f"talent {t['id']} emitted twice")
        seen[int(t["id"])] = t
    for tid in sorted(set(GRID) - set(seen)):
        bad.append(f"talent {tid}: not on tab {TAB}")
    for tid in sorted(set(seen) - set(GRID)):
        bad.append(f"talent {tid}: unexpected on tab {TAB}")
    cells = {}
    row_points = [0] * 11
    for tid, (tier, col, ranks) in GRID.items():
        t = seen.get(tid)
        if t is None:
            continue
        if (int(t["tier"]), int(t["column"])) != (tier, col):
            bad.append(f"talent {tid}: cell ({t['tier']},{t['column']}), expected ({tier},{col})")
        got = list(t.get("rank_spell_ids") or [])
        if isinstance(ranks, int):
            if len(got) != ranks:
                bad.append(f"talent {tid}: {len(got)} ranks, expected {ranks}")
        elif got != ranks:
            bad.append(f"talent {tid}: ranks {got}, expected {ranks}")
        if t.get("depends_on"):
            bad.append(f"talent {tid}: has an arrow (depends_on {t['depends_on']})")
        cells.setdefault((int(t["tier"]), int(t["column"])), []).append(tid)
        row_points[tier] += len(got)
    for cell, ids in cells.items():
        if len(ids) > 1:
            bad.append(f"cell {cell}: shared by {ids}")
    if len(seen) != 34 or sum(row_points) != 76:
        bad.append(f"{len(seen)} talents / {sum(row_points)} points, expected 34 / 76")
    if row_points != ROW_TOTALS:
        bad.append(f"row point totals {row_points}, expected {ROW_TOTALS}")
    ret_ids = {int(r["id"]) for r in retired}
    for tid in RETIRED:
        rows = [t for t in talents if int(t["id"]) == tid]
        if tid not in ret_ids:
            bad.append(f"talent {tid}: not retired")
        if len(rows) != 1:
            bad.append(f"talent {tid}: emitted {len(rows)} times, expected once")
        for t in rows:
            if int(t["tab_id"]) != RETIRED_TAB:
                bad.append(f"talent {tid}: on tab {t['tab_id']}, expected {RETIRED_TAB}")
            if t.get("rank_spell_ids"):
                bad.append(f"talent {tid}: still ranks {t['rank_spell_ids']}")
    if not re.search(r"assassination_182_tab\s*=\s*tab\((?:[^()]|\([^()]*\))*?skill_line\s*=\s*253\b", tab_text, re.S):
        bad.append("tab 182 does not declare skill_line=253")
    return bad


def check_slas(slas: list[dict]) -> list[str]:
    by_id = {int(s["id"]): s for s in slas if 30800 <= int(s["id"]) <= 30809}
    bad = []
    if sorted(by_id) != sorted(SLA_ROWS):
        bad.append(f"SkillLineAbility ids {sorted(by_id)}, expected {sorted(SLA_ROWS)}")
    for sid, (line, spell) in SLA_ROWS.items():
        s = by_id.get(sid)
        if s is None:
            continue
        got = (int(s["skill_line"]), int(s["spell_id"]), int(s.get("class_mask") or 0), int(s.get("acquire_method") or 0))
        if got != (line, spell, 8, 0):
            bad.append(f"SLA {sid}: {got}, expected {(line, spell, 8, 0)}")
    return bad


def check_scripts(names: list[dict], removals: list[dict]) -> list[str]:
    bound = {(int(n["spell_id"]), n["ScriptName"]) for n in names}
    unbound = {(int(n["spell_id"]), n["ScriptName"]) for n in removals}
    bad = [f"script {n} not bound to {s}" for s, n in sorted(SCRIPTS - bound)]
    bad += [f"script {n} not unbound from {s}" for s, n in sorted(UNBOUND - unbound)]
    for sid in (KB_MH, KB_OH):                       # R15: the Kingsbane hands need no script
        if any(s == sid for s, _n in bound):
            bad.append(f"{sid}: bound to a script (R15: only 203827 / 203828 take the dual-strike hand script)")
    for pair in sorted(bound & UNBOUND):
        bad.append(f"{pair}: both bound and unbound")
    return bad


def check_procs(procs: list[dict], removals: list[dict]) -> list[str]:
    bad = []
    gone = {int(r["SpellId"]) for r in removals}
    for sid in PROC_REMOVED:
        if sid not in gone:
            bad.append(f"spell_proc {sid}: removal not declared")
    sf = [p for p in procs if int(p["SpellId"]) == -14186]
    if len(sf) != 1:
        bad.append(f"-14186: {len(sf)} spell_proc rows, expected 1")
    for p in sf:
        want = {"SpellFamilyName": 8, "SpellFamilyMask0": 0, "SpellFamilyMask1": 0, "SpellFamilyMask2": 0x80000,
                "SpellPhaseMask": 2, "HitMask": 2, "Cooldown": 500}
        for k, v in want.items():
            if int(p.get(k) or 0) != v:
                bad.append(f"-14186: {k} = {p.get(k)!r}, expected {v}")
    for p in procs:                                   # nothing may proc on the once-per-cast bits
        sid = int(p["SpellId"])
        if (203800 <= sid <= 203869 or sid == -14186) and int(p.get("SpellPhaseMask") or 0) != 2:
            bad.append(f"{sid}: procs_on SpellPhaseMask {p.get('SpellPhaseMask')!r}, expected 2 (HIT)")
        if int(p.get("SpellFamilyName") or 0) == 8:
            if int(p.get("SpellFamilyMask2") or 0) & (0x100000 | 0x400) or int(p.get("SpellFamilyMask1") or 0) & 0x40000:
                bad.append(f"{sid}: proc row matches d2 b20 / d2 b10 / d1 b18 (once-per-cast bits, brief 10.3)")
    return bad


def check_links_attrs(links: list[dict], attrs: list[dict]) -> list[str]:
    bad = []
    got = {(int(x["spell_trigger"]), int(x["spell_effect"]), int(x["type"])) for x in links
           if int(x["spell_trigger"]) in (16513, 16514, 16515)}
    if got != LINKS:
        bad.append(f"Vile Poisons helper links {sorted(got)}, expected {sorted(LINKS)}")
    a = {int(x["spell_id"]): int(x["attributes"]) for x in attrs}
    if a.get(GARROTE) != 0:
        bad.append(f"{GARROTE}: custom attr {a.get(GARROTE)!r}, expected 0 (R1: behind flag cleared)")
    if a.get(203720) != 0x08000000 or a.get(8676) != 0:
        bad.append("RG0b custom attrs (Enforcer 0x08000000, Ambush 0) changed")
    return bad


def check_sdv(entries: list[dict], rows: dict) -> list[str]:
    bad = []
    by_id = {int(e["id"]): e for e in entries if 1320 <= int(e["id"]) <= 1334}
    if sorted(by_id) != sorted(SDV_ATTACH):
        bad.append(f"SDV ids {sorted(by_id)}, expected {sorted(SDV_ATTACH)}")
    for sid, e in by_id.items():
        for name in DEFINED_NAME.findall(str(e.get("Variables") or "")):
            if len(name) > MAX_NAME_LENGTH:
                bad.append(f"SDV {sid}: variable name {name!r} is {len(name)} chars (max {MAX_NAME_LENGTH})")
    for sdv, spells in SDV_ATTACH.items():
        for sid in spells:
            if _i(rows.get(sid, {}), "SpellDescriptionVariableID") != sdv:
                bad.append(f"{sid}: SpellDescriptionVariableID {rows.get(sid, {}).get('SpellDescriptionVariableID')!r}, "
                           f"expected {sdv}")
    return bad


def check_consts(consts: dict) -> list[str]:
    bad = []
    for k, v in CONSTS.items():
        if k not in consts:
            bad.append(f"const {k} missing")
        elif consts[k] != v:
            bad.append(f"const {k} = {consts[k]!r}, expected {v}")
    return bad


# ---- real data -----------------------------------------------------------------------------------------------------------

_CACHE: dict = {}


def _data():
    if not _CACHE:
        ids_cfg = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
        spell_table_index = spell_tables.load_spell_table_index()
        creature_table_index = spell_tables.load_creature_table_index()
        package = registry.load_class_package(
            ROGUE_DIR, ids_cfg=ids_cfg, trainer_index=trainer_state.load_trainer_index(),
            existing_group_ids={key[0] for key in spell_table_index.live_keys("spell_group")},
            shapeshift_index=state.load_stock_rows(dbcfmt.SPELLSHAPESHIFTFORM),
            existing_creature_rows={int(r["entry"]): r for r in creature_table_index.live_rows("creature_template")},
            creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
            creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS,
            live_data=spell_tables.load_dsl_live_data(),
        )
        reuse = ReuseContext({}, ids_cfg)
        rows = [build.build_spell_row(e, reuse) for e in package.spells]
        by_id = {int(r["ID"]): r for r in rows}
        idx = {"infinite": reuse.duration_index(0), "r30": reuse.range_index(30.0), "melee": _i(by_id[1752], "RangeIndex")}
        for ms in (2000, 4000, 6000, 8000, 10000, 12000, 14000, 15000, 20000):
            idx[f"d{ms}"] = reuse.duration_index(ms)
        _CACHE.update(package=package, rows=by_id, idx=idx)
    return _CACHE


class RogueS1DataTest(unittest.TestCase):
    def assertClean(self, problems: list[str]):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_s1_row_set(self):
        self.assertClean(check_s1_id_set(_data()["rows"]))

    def test_rows(self):
        d = _data()
        self.assertClean(check_rows(d["rows"], *expectations(d["idx"])))

    def test_value_cases(self):
        self.assertClean(check_value_cases(_data()["rows"], AMOUNTS))

    def test_mutilate_effects(self):
        self.assertClean(check_effect_order(_data()["rows"]))

    def test_texts(self):
        self.assertClean(check_texts(_data()["rows"]))

    def test_visibility(self):
        self.assertClean(check_visibility(_data()["rows"]))

    def test_carriers(self):
        self.assertClean(check_carriers(_data()["rows"]))

    def test_new_row_masks(self):
        self.assertClean(check_new_masks(_data()["rows"], S1_IDS))

    def test_readers(self):
        self.assertClean(check_readers(_data()["rows"]))

    def test_masks_module_composites(self):
        self.assertClean(check_composites(m))

    def test_grid(self):
        p = _data()["package"]
        text = (ROGUE_DIR / "rogue_talents.py").read_text(encoding="utf-8")
        self.assertClean(check_grid(p.talents, p.retired_talents, p.tabs, text))

    def test_skill_line_abilities(self):
        self.assertClean(check_slas(_data()["package"].skill_line_abilities))

    def test_scripts(self):
        p = _data()["package"]
        self.assertClean(check_scripts(p.spell_script_names, p.script_removals))

    def test_procs(self):
        p = _data()["package"]
        self.assertClean(check_procs(p.spell_procs, p.proc_removals))

    def test_links_and_custom_attrs(self):
        p = _data()["package"]
        self.assertClean(check_links_attrs(p.linked_spells, p.custom_attrs))

    def test_sdv(self):
        d = _data()
        self.assertClean(check_sdv(d["package"].tooltip_vars, d["rows"]))

    def test_consts(self):
        self.assertClean(check_consts({c["name"]: c["value"] for c in _data()["package"].consts}))


# ---- negative fixtures: every check must fire on a minimal bad input -----------------------------------------------------

IDX = {"infinite": 21, "melee": 2, "r30": 30, "d2000": 40, "d4000": 41, "d6000": 42, "d8000": 43, "d10000": 44,
       "d12000": 45, "d14000": 46, "d15000": 47, "d20000": 48}


def _good_rows() -> dict:
    exact, must_set, _clear = expectations(IDX)
    rows: dict[int, dict] = {}
    for sid, cols in exact.items():
        rows.setdefault(sid, {"ID": sid}).update({c: (v & 0xFFFFFFFF if v < 0 else v) for c, v in cols.items()})
    for sid, cols in must_set.items():
        row = rows.setdefault(sid, {"ID": sid})
        for col, bits in cols.items():
            row[col] = _u32(row.get(col)) | bits
    return rows


def _good_full_rows() -> dict:
    """Rows satisfying the carrier / mask / reader / value / text / id-set checks too."""
    rows = _good_rows()
    for sid in S1_IDS:
        r = rows.setdefault(sid, {"ID": sid})
        r["SpellClassSet"] = 8
        mask = FULL_MASKS.get(sid, (0, 0, 0))
        if sid not in rows or not any(r.get(f"SpellClassMask_{n}") for n in (1, 2, 3)):
            for n, w in enumerate(mask, 1):
                r[f"SpellClassMask_{n}"] = w
        r["Attributes"] = _u32(r.get("Attributes")) | (ATTR0_HIDDEN if sid in (MH, OH, KB_MH, KB_OH, DB_TICK, BS_STRIKE,
                                                                              DS_ENERGIZE) else 0)
    for sid in D2_CARRIERS["FINISHER_GROUP"][1] | D2_CARRIERS["DIRECT_BUILDER_GROUP"][1] | {14278}:
        r = rows.setdefault(sid, {"ID": sid})
    for name, (bit, who) in D2_CARRIERS.items():
        for sid in who:
            r = rows.setdefault(sid, {"ID": sid})
            r["SpellClassMask_3"] = _u32(r.get("SpellClassMask_3")) | bit
    for sid in POISON_GROUP_NEW:
        r = rows.setdefault(sid, {"ID": sid})
        r["SpellClassMask_2"] = _u32(r.get("SpellClassMask_2")) | POISON_GROUP
    for sid, eff, comp, aura, op in READERS:
        r = rows.setdefault(sid, {"ID": sid})
        for n, w in enumerate(COMPOSITES[comp], 1):
            r[f"EffectSpellClassMask{'ABC'[eff - 1]}_{n}"] = w
        if aura is not None:
            r[f"EffectAura_{eff}"] = aura
        if op is not None:
            r[f"EffectMiscValue_{eff}"] = op
    for sid, eff, aura, value in AMOUNTS:
        r = rows.setdefault(sid, {"ID": sid})
        r[f"EffectBasePoints_{eff}"] = value - 1
        r[f"EffectDieSides_{eff}"] = 1
        if aura is not None:
            r[f"EffectAura_{eff}"] = aura
    for sid, text in TEXTS.items():
        rows.setdefault(sid, {"ID": sid})["AuraDescription_Lang_enUS"] = text
    for sid in (BS_BUFF, HFB, KB_DOT):
        rows.setdefault(sid, {"ID": sid})["AuraDescription_Lang_enUS"] = "text"
    mut = rows[MUT]
    mut.update({"Effect_1": TRIGGER_SPELL, "EffectTriggerSpell_1": MH, "Effect_2": TRIGGER_SPELL,
                "EffectTriggerSpell_2": OH, "Effect_3": ADD_COMBO, "EffectBasePoints_3": 1, "EffectDieSides_3": 1})
    return rows


class RogueS1NegativeTest(unittest.TestCase):
    def test_rows_clean_fixture(self):
        self.assertEqual(check_rows(_good_rows(), *expectations(IDX)), [])

    def test_every_exact_expectation_can_fail(self):
        exact, ms, mc = expectations(IDX)
        for sid, cols in exact.items():
            for col, want in cols.items():
                rows = _good_rows()
                rows[sid][col] = (_u32(want) ^ 0x4) if want else 0x4
                self.assertGreaterEqual(len(check_rows(rows, exact, ms, mc)), 1, (sid, col))

    def test_every_set_bit_expectation_can_fail(self):
        exact, ms, mc = expectations(IDX)
        for sid, cols in ms.items():
            for col, bits in cols.items():
                rows = _good_rows()
                rows[sid][col] = _u32(rows[sid].get(col)) & ~bits
                self.assertGreaterEqual(len(check_rows(rows, exact, ms, mc)), 1, (sid, col))

    def test_every_clear_bit_expectation_can_fail(self):
        exact, ms, mc = expectations(IDX)
        for sid, cols in mc.items():
            for col, bits in cols.items():
                rows = _good_rows()
                rows[sid][col] = _u32(rows[sid].get(col)) | bits
                self.assertGreaterEqual(len(check_rows(rows, exact, ms, mc)), 1, (sid, col))

    def test_named_hazards(self):
        """The brief's hazards, each on its own."""
        exact, ms, mc = expectations(IDX)
        for sid, col, val in ((MUT, "ManaCost", 60), (MUT, "EquippedItemSubclass", 32768), (MH, "Effect_1", NORM_WEAPON),
                              (MH, "Effect_2", WEAPON_PCT), (KB, "RecoveryTime", 30000), (COLD_BLOOD, "Attributes", 33882128),
                              (HFB, "StartRecoveryTime", 1000), (HFB, "TargetAuraState", 16), (KB_DOT, "CumulativeAura", 50),
                              (KB_DOT, "DispelType", 0), (PB, "Speed", 0), (DB_TICK, "DefenseType", 2),
                              (BS_STRIKE, "DefenseType", 0), (31226, "SpellIconID", 1), (REM_CRIT, "ProcCharges", 0),
                              (14144, "ProcTypeMask", 87376), (14161, "ProcChance", 100), (14193, "ProcChance", 99)):
            rows = _good_rows()
            rows[sid][col] = val
            self.assertGreaterEqual(len(check_rows(rows, exact, ms, mc)), 1, (sid, col, val))

    def test_missing_row(self):
        rows = _good_rows()
        del rows[KB]
        self.assertGreaterEqual(len(check_rows(rows, *expectations(IDX))), 1)

    def test_s1_row_set(self):
        rows = {sid: {} for sid in S1_IDS}
        self.assertEqual(check_s1_id_set(rows), [])
        self.assertEqual(len(check_s1_id_set({k: v for k, v in rows.items() if k != KB})), 1)
        for extra in (203835, 203848, 203850):
            self.assertEqual(len(check_s1_id_set({**rows, extra: {}})), 1, extra)

    def test_value_cases(self):
        rows = _good_full_rows()
        self.assertEqual(check_value_cases(rows, AMOUNTS), [])
        for sid, eff, aura, value in AMOUNTS:
            bad = {k: dict(v) for k, v in rows.items()}
            bad[sid][f"EffectBasePoints_{eff}"] = value + 1
            self.assertGreaterEqual(len(check_value_cases(bad, AMOUNTS)), 1, (sid, eff, "value"))
            if aura is not None:
                bad = {k: dict(v) for k, v in rows.items()}
                bad[sid][f"EffectAura_{eff}"] = aura + 1
                self.assertGreaterEqual(len(check_value_cases(bad, AMOUNTS)), 1, (sid, eff, "aura"))
        self.assertEqual(len(check_value_cases({k: v for k, v in rows.items() if k != 203808}, AMOUNTS)), 1)
        # die sides 0 reads the stored value as is
        self.assertEqual(value_of({"EffectBasePoints_1": 5, "EffectDieSides_1": 0}, 1), 5)
        self.assertEqual(value_of({"EffectBasePoints_1": 5, "EffectDieSides_1": 1}, 1), 6)
        # R10: 57 is spell crit, not weapon crit
        bad = {k: dict(v) for k, v in rows.items()}
        bad[CB_AFTER]["EffectAura_1"] = 57
        self.assertGreaterEqual(len(check_value_cases(bad, AMOUNTS)), 1)

    def test_mutilate_effects(self):
        rows = _good_full_rows()
        self.assertEqual(check_effect_order(rows), [])
        self.assertEqual(len(check_effect_order({})), 1)
        for col, val in (("EffectTriggerSpell_2", 5374), ("EffectBasePoints_3", 0), ("Effect_3", 0), ("Effect_1", 6)):
            bad = {k: dict(v) for k, v in rows.items()}
            bad[MUT][col] = val
            self.assertGreaterEqual(len(check_effect_order(bad)), 1, col)

    def test_texts_and_visibility(self):
        rows = _good_full_rows()
        self.assertEqual(check_texts(rows), [])
        self.assertEqual(check_visibility(rows), [])
        for sid in TEXTS:
            bad = {k: dict(v) for k, v in rows.items()}
            bad[sid]["AuraDescription_Lang_enUS"] = TEXTS[sid] + " "
            self.assertEqual(len(check_texts(bad)), 1, sid)
        for sid in (BS_BUFF, HFB, KB_DOT):
            bad = {k: dict(v) for k, v in rows.items()}
            bad[sid]["AuraDescription_Lang_enUS"] = ""
            self.assertEqual(len(check_texts(bad)), 1, sid)
        for sid in (MH, OH, KB_MH, KB_OH, DB_TICK, BS_STRIKE, DS_ENERGIZE):
            bad = {k: dict(v) for k, v in rows.items()}
            bad[sid]["Attributes"] = 0
            self.assertEqual(len(check_visibility(bad)), 1, sid)

    def test_carriers(self):
        rows = _good_full_rows()
        self.assertEqual(check_carriers(rows), [])
        for name, (bit, who) in D2_CARRIERS.items():
            gone = {k: dict(v) for k, v in rows.items()}      # a carrier loses the bit
            victim = sorted(who)[0]
            gone[victim]["SpellClassMask_3"] = _u32(gone[victim].get("SpellClassMask_3")) & ~bit
            self.assertGreaterEqual(len(check_carriers(gone)), 1, (name, "missing"))
            extra = {k: dict(v) for k, v in rows.items()}      # a stranger gains it
            extra[999999] = {"ID": 999999, "SpellClassMask_3": bit}
            self.assertGreaterEqual(len(check_carriers(extra)), 1, (name, "extra"))
        for sid in POISON_GROUP_NEW:
            gone = {k: dict(v) for k, v in rows.items()}
            gone[sid]["SpellClassMask_2"] = 0
            self.assertEqual(len(check_carriers(gone)), 1, sid)
        # R9: Blindside's strike must not carry d2 b10
        bad = {k: dict(v) for k, v in rows.items()}
        bad[BS_STRIKE]["SpellClassMask_3"] = 0x400
        self.assertGreaterEqual(len(check_carriers(bad)), 1)

    def test_new_masks(self):
        rows = _good_full_rows()
        self.assertEqual(check_new_masks(rows, S1_IDS), [])
        bad = {k: dict(v) for k, v in rows.items()}
        bad[KB]["SpellClassMask_3"] = 0x1
        self.assertEqual(len(check_new_masks(bad, S1_IDS)), 1)                   # a stray family bit on a parent
        bad = {k: dict(v) for k, v in rows.items()}
        bad[KB]["SpellClassSet"] = 0
        self.assertEqual(len(check_new_masks(bad, S1_IDS)), 1)
        for sid, col, bit in ((MH, "SpellClassMask_2", 0x2), (MH, "SpellClassMask_2", 0x4), (MH, "SpellClassMask_2", 0x8),
                              (DB_BLEED, "SpellClassMask_1", D0_B20), (DB_TICK, "SpellClassMask_1", D0_B16),
                              (KB_MH, "SpellClassMask_1", D0_B17), (KB_OH, "SpellClassMask_1", 0x2000000),
                              (KB_OH, "SpellClassMask_2", 0x40000), (203800, "SpellClassMask_1", 0x4000000)):
            bad = {k: dict(v) for k, v in rows.items()}
            bad[sid][col] = _u32(bad[sid].get(col)) | bit
            self.assertGreaterEqual(len(check_new_masks(bad, S1_IDS)), 1, (sid, col, bit))

    def test_readers(self):
        rows = _good_full_rows()
        self.assertEqual(check_readers(rows), [])
        for sid, eff, comp, aura, op in READERS:
            bad = {k: dict(v) for k, v in rows.items()}
            col = f"EffectSpellClassMask{'ABC'[eff - 1]}_1"
            bad[sid][col] = _u32(bad[sid].get(col)) ^ 0x1
            self.assertGreaterEqual(len(check_readers(bad)), 1, (sid, eff, "mask"))
            wrong_dword = {k: dict(v) for k, v in rows.items()}        # the wrong-effect-letter trap (bug-doc :2178)
            for n in (1, 2, 3):
                wrong_dword[sid][f"EffectSpellClassMask{'ABC'[eff % 3]}_{n}"] = COMPOSITES[comp][n - 1]
                wrong_dword[sid][f"EffectSpellClassMask{'ABC'[eff - 1]}_{n}"] = 0
            self.assertGreaterEqual(len(check_readers(wrong_dword)), 1, (sid, eff, "letter"))
            if aura is not None:
                bad = {k: dict(v) for k, v in rows.items()}
                bad[sid][f"EffectAura_{eff}"] = aura + 1
                self.assertGreaterEqual(len(check_readers(bad)), 1, (sid, eff, "aura"))
            if op is not None:
                bad = {k: dict(v) for k, v in rows.items()}
                bad[sid][f"EffectMiscValue_{eff}"] = op + 1
                self.assertGreaterEqual(len(check_readers(bad)), 1, (sid, eff, "op"))
        self.assertGreaterEqual(len(check_readers({})), 1)

    def test_composites(self):
        class Mod:
            pass
        good = Mod()
        for name, value in COMPOSITES.items():
            setattr(good, name, value)
        self.assertEqual(check_composites(good), [])
        for name in COMPOSITES:
            bad = Mod()
            for n, v in COMPOSITES.items():
                setattr(bad, n, v)
            setattr(bad, name, (COMPOSITES[name][0] ^ 1,) + COMPOSITES[name][1:])
            self.assertEqual(len(check_composites(bad)), 1, name)
        gone = Mod()
        self.assertEqual(len(check_composites(gone)), len(COMPOSITES))

    def test_grid(self):
        def good():
            out = [{"id": tid, "tab_id": TAB, "tier": t, "column": c,
                    "rank_spell_ids": list(r) if isinstance(r, list) else list(range(1, r + 1)), "depends_on": None}
                   for tid, (t, c, r) in GRID.items()]
            out += [{"id": tid, "tab_id": RETIRED_TAB, "tier": 0, "column": 0, "rank_spell_ids": [], "depends_on": None}
                    for tid in RETIRED]
            return out
        tab_text = "assassination_182_tab = tab(\n    id=182,\n    skill_line=253,\n    raw_overrides={},\n)\n"
        ret = [{"id": t} for t in RETIRED]
        self.assertEqual(check_grid(good(), ret, [], tab_text), [])
        idx = lambda ts, tid: next(t for t in ts if t["id"] == tid)  # noqa: E731
        cases = []
        g = good(); idx(g, 60390)["tier"] = 1; cases.append(("moved", g))
        g = good(); idx(g, 270)["column"] = 3; cases.append(("moved col", g))
        g = good(); idx(g, 273)["depends_on"] = {"talent_id": 272, "rank": 2}; cases.append(("arrow", g))
        g = good(); idx(g, 269)["rank_spell_ids"] = [14128, 14132, 14135, 14136, 14137]; cases.append(("5 ranks", g))
        g = good(); idx(g, 60391)["rank_spell_ids"] = [203803]; cases.append(("short", g))
        g = good(); idx(g, 60391)["rank_spell_ids"] = [203804, 203803]; cases.append(("rank order", g))
        g = good(); g = [t for t in g if t["id"] != 60401]; cases.append(("missing", g))
        g = good(); idx(g, 276)["tab_id"] = TAB; cases.append(("276 not retired", g))
        g = good(); idx(g, 2070)["rank_spell_ids"] = [51664]; cases.append(("2070 ranked", g))
        g = good(); g.append({"id": 9999, "tab_id": TAB, "tier": 3, "column": 2, "rank_spell_ids": [1], "depends_on": None})
        cases.append(("extra", g))
        g = good(); idx(g, 60392)["tier"], idx(g, 60392)["column"] = 3, 1; cases.append(("shared cell", g))
        g = good(); g.append(dict(idx(g, 280))); cases.append(("duplicate", g))
        for label, talents in cases:
            self.assertGreaterEqual(len(check_grid(talents, ret, [], tab_text)), 1, label)
        self.assertGreaterEqual(len(check_grid(good(), ret[1:], [], tab_text)), 1)
        self.assertGreaterEqual(len(check_grid(good(), ret, [], tab_text.replace("253", "202"))), 1)
        self.assertGreaterEqual(len(check_grid(good(), ret, [], tab_text.replace("    skill_line=253,\n", ""))), 1)

    def test_slas(self):
        good = [{"id": i, "skill_line": line, "spell_id": s, "class_mask": 8, "acquire_method": 0}
                for i, (line, s) in SLA_ROWS.items()]
        self.assertEqual(check_slas(good), [])
        self.assertGreaterEqual(len(check_slas(good[1:])), 1)
        self.assertGreaterEqual(len(check_slas(good + [{**good[0], "id": 30802}])), 1)
        for col, val in (("skill_line", 202), ("spell_id", 5), ("class_mask", 0), ("acquire_method", 1)):
            self.assertEqual(len(check_slas([{**good[0], col: val}] + good[1:])), 1, col)

    def test_scripts(self):
        names = [{"spell_id": s, "ScriptName": n} for s, n in sorted(SCRIPTS)]
        rem = [{"spell_id": s, "ScriptName": n} for s, n in sorted(UNBOUND)]
        self.assertEqual(check_scripts(names, rem), [])
        for i in range(len(names)):
            self.assertEqual(len(check_scripts(names[:i] + names[i + 1:], rem)), 1, names[i])
        for i in range(len(rem)):
            self.assertEqual(len(check_scripts(names, rem[:i] + rem[i + 1:])), 1, rem[i])
        self.assertEqual(len(check_scripts(names + [{"spell_id": KB_MH, "ScriptName": "spell_rog_dual_strike_hand"}], rem)), 1)
        self.assertEqual(len(check_scripts(names + [{"spell_id": -1329, "ScriptName": "spell_rog_mutilate"}], rem)), 1)

    def test_procs(self):
        rem = [{"SpellId": s} for s in PROC_REMOVED]
        sf = {"SpellId": -14186, "SpellFamilyName": 8, "SpellFamilyMask0": 0, "SpellFamilyMask1": 0,
              "SpellFamilyMask2": 0x80000, "SpellPhaseMask": 2, "HitMask": 2, "Cooldown": 500}
        self.assertEqual(check_procs([sf], rem), [])
        self.assertEqual(len(check_procs([], rem)), 1)
        self.assertEqual(len(check_procs([sf, sf], rem)), 1)
        for i in range(len(rem)):
            self.assertEqual(len(check_procs([sf], rem[:i] + rem[i + 1:])), 1, rem[i])
        for col, val in (("SpellFamilyName", 0), ("SpellFamilyMask2", 0x180000), ("SpellFamilyMask0", 2),
                         ("SpellPhaseMask", 1), ("HitMask", 1), ("Cooldown", 0)):
            self.assertGreaterEqual(len(check_procs([{**sf, col: val}], rem)), 1, col)
        s1 = {**sf, "SpellId": 203838, "SpellFamilyMask2": 0}
        self.assertGreaterEqual(len(check_procs([sf, {**s1, "SpellPhaseMask": 0}], rem)), 1)
        for mask in (("SpellFamilyMask2", 0x100000), ("SpellFamilyMask2", 0x400), ("SpellFamilyMask1", 0x40000)):
            self.assertGreaterEqual(len(check_procs([sf, {**s1, mask[0]: mask[1]}], rem)), 1, mask)

    def test_links_attrs(self):
        links = [{"spell_trigger": a, "spell_effect": b, "type": t} for a, b, t in sorted(LINKS)]
        attrs = [{"spell_id": GARROTE, "attributes": 0}, {"spell_id": 203720, "attributes": 0x08000000},
                 {"spell_id": 8676, "attributes": 0}]
        self.assertEqual(check_links_attrs(links, attrs), [])
        self.assertEqual(len(check_links_attrs(links[1:], attrs)), 1)
        self.assertEqual(len(check_links_attrs(links[:-1] + [{**links[-1], "type": 0}], attrs)), 1)
        self.assertEqual(len(check_links_attrs(links, attrs[1:])), 1)
        self.assertEqual(len(check_links_attrs(links, [{**attrs[0], "attributes": 0x20000}] + attrs[1:])), 1)
        self.assertEqual(len(check_links_attrs(links, attrs[:1] + [{**attrs[1], "attributes": 0}] + attrs[2:])), 1)

    def test_sdv(self):
        entries = [{"id": i, "Variables": "$vile1=1\r\n$vile2=${$<vile1>*2}"} for i in SDV_ATTACH]
        rows = {sid: {"SpellDescriptionVariableID": sdv} for sdv, ss in SDV_ATTACH.items() for sid in ss}
        self.assertEqual(check_sdv(entries, rows), [])
        self.assertGreaterEqual(len(check_sdv(entries[1:], rows)), 1)
        self.assertEqual(len(check_sdv(entries + [{"id": 1324, "Variables": ""}], rows)), 1)
        long_name = [{**entries[0], "Variables": "$averyverylongname=1"}] + entries[1:]
        self.assertEqual(len(check_sdv(long_name, rows)), 1)
        bad = {k: dict(v) for k, v in rows.items()}
        bad[ENVENOM]["SpellDescriptionVariableID"] = 0
        self.assertEqual(len(check_sdv(entries, bad)), 1)
        bad = {k: v for k, v in rows.items() if k != 51723}
        self.assertEqual(len(check_sdv(entries, bad)), 1)

    def test_consts(self):
        self.assertEqual(check_consts(dict(CONSTS)), [])
        for name in CONSTS:
            self.assertEqual(len(check_consts({k: v for k, v in CONSTS.items() if k != name})), 1, name)
            self.assertEqual(len(check_consts({**CONSTS, name: CONSTS[name] + 1})), 1, name)


if __name__ == "__main__":
    unittest.main()
