"""
Rogue S3a data gate (rogue-rework S3a-HANDOFF WP-A row A5, S3a-WP-BRIEF sections 2-6, 8, 10 and 12).

Loads the real rogue DSL package (source/classes/rogue/) and asserts on the BUILT rows (stock base + DSL + raw_overrides via
`build.build_spell_row`), like test_rogue_s2.py. Every check is a pure function over built rows / package tables; the
negative tests prove each can fail (every single expectation is mutated on its own against a fixture that satisfies all of
them). Expected values are written out here from the brief, never imported from `_masks.py` (the module's composites are
pinned against the brief's literals instead).

  1. Talent grid: tab 181 = the 36 talents in the doc's cells, ranks, 75 points, row totals 11/10/7/9/8/7/8/3/8/3/1, no
     arrows, flags, tab skill line 38, the six retired on 60800, Weapon Specialization renamed, SLA 30810-30814.
  2. Row expectations (EXACT / MUST_SET / MUST_CLEAR): the 54 new rows 203950-204003 and the stock rows S3 edits (13877,
     13750, 51690, 14251, the strikes 57841 / 57842, ranks), brief section 10 and R1-R25; spare ids absent.
  3. Family bits on exactly their carriers, new-row masks, the never-bits, every reader mask equal to its brief literal
     READ THROUGH THE RAW KEYS (letter = effect, number = dword) with its aura / SpellMod op; `_masks` composites.
  4. Rank amounts the C++ reads (brief section 5), talent rank frames (attributes 464, SpellLevel 9 + 5 x row + rank).
  5. Script bindings / unbinds / rebinds, proc rows, links, groups, custom attrs, SDV 1350-1352 + the extended 1323 /
     1335 / 1336 (names <= 12 chars), consts, the generated RogueData.h names.

Run: apps/dbc-tools/.venv/bin/python3 -m pytest apps/dbc-tools/lib/test_rogue_s3.py -q
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

# ---- ids (brief section 2) ---------------------------------------------------------------------------------------------

S3_IDS = tuple(range(203950, 204004))                 # 54 new rows
S3_SPARE = tuple(range(204004, 204130))               # fix-pass spare + unassigned: nothing may be built here
QR = (203950, 203951, 203952)
ACC = (203953, 203954, 203955)
LEARN, MARKER, PS, BTE = 203956, 203957, 203958, 203959
RL = (203960, 203961, 203962)
GH, QD, RB = 203963, 203964, 203965
IR = (203966, 203967, 203968)
EG = 203969
CDG = (203970, 203971, 203972)
DM = (203973, 203974)
HT = (203975, 203976)
CEL = (203977, 203978)
IFEINT, BR = 203979, 203980
SA_R = (32601, 203981, 203982)
(OPP, OPP_COMP, PRIMED, SECOND, HT_BUFF, PS_EXTRA, SA_BUFF, BR_BUFF, BF_COPY) = range(203983, 203992)
(DM_STRIKE, IR_CLEAVE, HS_MAIN, HS_OFF, AR_CEL, ANTIC, BT_DEBUFF, IK_BUFF) = range(203992, 204000)
(SPRINT_HELPER, ENDURANCE_HELPER, FEINT_HELPER, PREY_DEBUFF) = range(204000, 204004)
SINISTER_STRIKE, EVISCERATE, BACKSTAB, AMBUSH, KICK = 1752, 2098, 53, 8676, 1766
RIPOSTE, BLADE_FLURRY, ADRENALINE_RUSH, KILLING_SPREE = 14251, 13877, 13750, 51690
KS_MAIN, KS_OFF = 57841, 57842
UA_RANKS, UA_STRIKES = (51672, 51674), (51675, 51677)
SND, SPRINT, EVASION, FEINT = 5171, 2983, 5277, 1966
COLD_BLOOD, MOMA_BUFF = 14177, 204164
FW = (31234, 31235, 31236)
HIDDEN_PASSIVE_ATTR = 464

D0_B1, D0_B11, D0_B17, D0_B22, D0_B25, D0_B26 = 0x2, 0x800, 0x20000, 0x400000, 0x2000000, 0x4000000
FORBIDDEN_S3_D0 = D0_B11 | D0_B22 | D0_B25 | D0_B26          # brief section 4: on no S3 row
D2_B4, D2_B19 = 0x10, 0x80000
FORBIDDEN_COPY = (D0_B1, 0, D2_B4 | D2_B19)                   # brief section 4: on none of the copies
COMBO_ATTRS = 0x100000 | 0x400000                              # AttributesEx: NeedsComboPoints()
EX1_STEALTH_OK = 0x20
EX3_SUPPRESS_CASTER, EX3_ALWAYS_HIT, EX3_IGNORE_CASTER_MODS, EX3_STACK_PER_CASTER = 0x10000, 0x40000, 0x20000000, 0x80
EX3_REQ_MAIN, EX3_REQ_OFF, EX3_SUPPRESS_TARGET = 0x400, 0x1000000, 0x20000
EX3_NOT_A_PROC = 0x200
EX2_CANT_CRIT = 0x20000000

APPLY_AURA, LEARN_SPELL, ADD_COMBO, SCHOOL_DAMAGE, DUMMY_EFFECT, WEAPON_PCT = 6, 36, 80, 2, 3, 31
NORMALIZED_WEAPON, CHARGE = 121, 96
AURA_DUMMY, AURA_FLAT, AURA_PCT, AURA_PERIODIC_DUMMY = 4, 107, 108, 226
OP = {"DAMAGE": 0, "DURATION": 1, "THREAT": 2, "CRIT": 7, "COOLDOWN": 11, "EFFECT2": 12, "COST": 14}
RANGE_SELF, RANGE_MELEE, RANGE_20, RANGE_40, RANGE_100 = 1, 2, 3, 5, 6
RADIUS_5YD = 8

# ---- grid (S3a brief 10.1; tab 181) ------------------------------------------------------------------------------------

TAB = 181
RETIRED_TAB = 60800
RETIRED = (203, 182, 1703, 1705, 1707, 1825)
GRID = {
    201: (0, 1, [13732, 13863]), 221: (0, 2, [13715, 13848, 13849]), 1827: (1, 0, [14165, 14166]),
    187: (1, 1, [13713, 13853, 13854]), 206: (1, 2, [13754, 13867]), 181: (1, 3, [13705, 13832, 13843]),
    204: (2, 0, [13742, 13872]), 301: (2, 3, [14251]), 222: (3, 1, [13743, 13875]),
    186: (3, 2, [13712, 13788, 13789]), 1122: (3, 3, [18427, 18428, 18429]), 184: (4, 0, [13709, 13800, 13801]),
    223: (4, 1, [13877]), 242: (4, 2, [13960, 13961, 13962]), 1706: (5, 2, [31124, 31126]), 205: (6, 1, [13750]),
    2073: (8, 0, [51672, 51674]), 1709: (8, 3, [32601, 203981, 203982]), 2074: (8, 2, [51682, 58413]),
    2075: (9, 1, [51685, 51686, 51687]), 2076: (10, 1, [51690]),
    60405: (0, 0, list(QR)), 60406: (0, 3, list(ACC)), 60407: (2, 1, [LEARN]), 60408: (2, 2, list(RL)),
    60409: (3, 0, [GH]), 60410: (4, 3, [QD]), 60411: (5, 0, [RB]), 60412: (5, 1, list(IR)), 60413: (5, 3, [EG]),
    60414: (6, 0, list(CDG)), 60415: (6, 2, list(DM)), 60416: (6, 3, list(HT)), 60417: (7, 2, list(CEL)),
    60418: (7, 3, [IFEINT]), 60419: (8, 1, [BR]),
}
ROW_TOTALS = [11, 10, 7, 9, 8, 7, 8, 3, 8, 3, 1]
TALENT_COUNT, POINT_COUNT = 36, 75
FLAGS = {301: 1, 223: 1, 205: 1, 2076: 1, 1709: 0, 60407: 0, 60409: 1, 60413: 1, 60419: 1}
SLA_ROWS = {30810: (38, PS), 30811: (38, BTE), 30812: (38, GH), 30813: (38, EG), 30814: (38, BR)}
SLA_RANGE = range(30810, 30825)
WEAPON_SPEC_RANKS = (13709, 13800, 13801)

# ---- family bits (brief section 4) ----------------------------------------------------------------------------------------

CARRIER_CLASS = {   # own SpellClassMask_1/_2/_3 of the carrier rows, written out from the brief's table
    PS: (0, 0, 0x80010), BTE: (0, 0, 0x40020), EG: (0, 0, 0x40040), BR: (0, 0, 0x8000), GH: (0, 0, 0x10000),
    SECOND: (0, 0, 0x800000), PS_EXTRA: (0, 0, 0x1000000), KS_MAIN: (0, 0x800000, 0), KS_OFF: (0, 0x800000, 0),
    IR_CLEAVE: (0, 0x100, 0), RIPOSTE: (0, 0x100, 0x80000), KILLING_SPREE: (0, 0x800000, 0x40000),
}
NEW_BIT_CARRIERS = {   # (dword index, bit value) -> exact carrier set across every built row
    (2, 0x10): {PS}, (2, 0x20): {BTE}, (2, 0x40): {EG}, (2, 0x8000): {BR}, (2, 0x10000): {GH},
    (2, 0x800000): {SECOND}, (2, 0x1000000): {PS_EXTRA},
    (1, 0x800000): {KILLING_SPREE, KS_MAIN, KS_OFF}, (1, 0x100): {RIPOSTE, IR_CLEAVE},
}
GROUP_MEMBERS = {   # existing group bits: these rows must carry them (membership, not exact set)
    (2, 0x40000): {BTE, EG, KILLING_SPREE}, (2, 0x80000): {PS, RIPOSTE},
}
COPY_ROWS = (SECOND, PS_EXTRA, BF_COPY, DM_STRIKE, IR_CLEAVE, HS_MAIN, HS_OFF, KS_MAIN, KS_OFF)
NO_BIT_ROWS = (BF_COPY, HS_MAIN, HS_OFF, SPRINT_HELPER, ENDURANCE_HELPER, FEINT_HELPER, PREY_DEBUFF, BT_DEBUFF)
NO_MASK_STRIKES = UA_STRIKES        # SpellClassSet 8, no bits (C14)

# reader literals from brief section 4
COMPOSITES = {
    "IMPROVED_SS_READ": (0x2, 0, 0x800000),
    "AGGRESSION_READ": (0x20002, 0, 0x1800030),
    "SURPRISE_ATTACKS_READ": (0x20020206, 0, 0x1800030),
    "COUP_DE_GRACE_READ": (0x20000, 0x800000, 0x20),
    "BLADE_RUSH_EMPOWER_READ": (0x20000, 0x800000, 0x20),
    "OPPORTUNITY_READ": (0, 0, 0x10),
    "HAIR_TRIGGER_READ": (0, 0, 0x10),
    "PRIMED_POWDER_READ": (0, 0, 0x20),
    "BLADE_TWISTING_READ": (0, 0x40000, 0x1980400),
    "IMPROVED_RIPOSTE_THREAT_READ": (0, 0x100, 0x200000),
    "IMPROVED_SND_READ": (0x40000, 0, 0),
    "ENDURANCE_EVASION_READ": (0x20, 0, 0),
    "IMPROVED_SPRINT_DURATION_READ": (0x40, 0, 0),
    "IMPROVED_SPRINT_TRIGGER_READ": (0x40, 0, 0),
    "COLD_BLOOD_READ_S3": (0x20000, 0x40109, 0x188420),
    "COLD_BLOOD_RANGE_READ_S3": (0x20000, 0x240109, 0x588420),
    "MOMA_READ_S3": (0x20000, 0x40109, 0x1A85A0),
    "FIND_WEAKNESS_READ_S3": (0x100, 0xC0100, 0x1E87A0),
    "PISTOL_SHOT_CLASS": (0, 0, 0x80010),
    "BETWEEN_THE_EYES_CLASS": (0, 0, 0x40020),
    "EN_GARDE_CLASS": (0, 0, 0x40040),
    "BLADE_RUSH_CLASS": (0, 0, 0x8000),
    "GRAPPLING_HOOK_CLASS": (0, 0, 0x10000),
    "SS_SECOND_STRIKE_CLASS": (0, 0, 0x800000),
    "PISTOL_SHOT_EXTRA_CLASS": (0, 0, 0x1000000),
    "KILLING_SPREE_STRIKE_CLASS": (0, 0x800000, 0),
    "RIPOSTE_CLEAVE_CLASS": (0, 0x100, 0),
    "RIPOSTE_CLASS_S3": (0, 0x100, 0x80000),
    "KILLING_SPREE_CLASS_S3": (0, 0x800000, 0x40000),
    "PISTOL_SHOT": 0x10, "BETWEEN_THE_EYES": 0x20, "EN_GARDE": 0x40, "BLADE_RUSH": 0x8000, "GRAPPLING_HOOK": 0x10000,
    "SS_SECOND_STRIKE": 0x800000, "PISTOL_SHOT_EXTRA": 0x1000000,
    "SLICE_AND_DICE": 0x40000, "EVASION": 0x20, "SPRINT": 0x40, "ADRENALINE_RUSH_D1": 0x80, "BLADE_FLURRY_D1": 0x800,
    "KILLING_SPREE_D1": 0x800000,
}
# (spell id, effect 1-based (= letter A/B/C), composite, aura, SpellMod op or None)
READERS = (
    [(i, 1, "IMPROVED_SS_READ", AURA_PCT, OP["DAMAGE"]) for i in (13732, 13863)]
    + [(i, 1, "AGGRESSION_READ", AURA_FLAT, OP["CRIT"]) for i in (18427, 18428, 18429)]
    + [(i, 1, "SURPRISE_ATTACKS_READ", AURA_PCT, OP["DAMAGE"]) for i in SA_R]
    + [(i, 1, "COUP_DE_GRACE_READ", AURA_PCT, OP["DAMAGE"]) for i in CDG]
    + [(BR_BUFF, 1, "BLADE_RUSH_EMPOWER_READ", AURA_PCT, OP["DAMAGE"]),
       (OPP_COMP, 1, "OPPORTUNITY_READ", AURA_PCT, OP["COST"]),
       (OPP_COMP, 2, "OPPORTUNITY_READ", AURA_PCT, OP["DAMAGE"]),
       (HT_BUFF, 1, "HAIR_TRIGGER_READ", AURA_PCT, OP["DAMAGE"]),
       (PRIMED, 1, "PRIMED_POWDER_READ", AURA_PCT, OP["DAMAGE"]),
       (BT_DEBUFF, 1, "BLADE_TWISTING_READ", 271, None)]
    + [(i, 2, "IMPROVED_RIPOSTE_THREAT_READ", AURA_PCT, OP["THREAT"]) for i in IR]
    + [(i, 1, "IMPROVED_SND_READ", AURA_PCT, OP["DURATION"]) for i in (14165, 14166)]
    + [(i, 2, "IMPROVED_SND_READ", AURA_FLAT, OP["EFFECT2"]) for i in (14165, 14166)]
    + [(i, 1, "ENDURANCE_EVASION_READ", AURA_FLAT, OP["COOLDOWN"]) for i in (13742, 13872)]
    + [(i, 1, "IMPROVED_SPRINT_DURATION_READ", AURA_FLAT, OP["DURATION"]) for i in (13743, 13875)]
    + [(13875, 2, "IMPROVED_SPRINT_TRIGGER_READ", 109, None)]
    + [(COLD_BLOOD, 1, "COLD_BLOOD_READ_S3", AURA_FLAT, OP["CRIT"]),
       (COLD_BLOOD, 2, "COLD_BLOOD_READ_S3", AURA_PCT, OP["DAMAGE"]),
       (COLD_BLOOD, 3, "COLD_BLOOD_RANGE_READ_S3", AURA_FLAT, 5),
       (MOMA_BUFF, 1, "MOMA_READ_S3", AURA_FLAT, OP["CRIT"])]
    + [(i, 1, "FIND_WEAKNESS_READ_S3", AURA_FLAT, OP["CRIT"]) for i in FW]
)
# effects that must read NO mask at all (stale twins cleared, brief R8): (spell id, effect 1-based)
EMPTY_MASKS = (
    [(i, e) for i in (51685, 51686, 51687) for e in (1, 2)]               # Prey: A_1 / B_1 0x400000
    + [(i, 2) for i in (31124, 31126)]                                     # Blade Twisting: B_1 0x6
    + [(i, 2) for i in (51682, 58413)]                                     # Savage Combat: B_1 0x400000
    + [(32601, 2)]                                                         # Surprise Attacks: B_1 0x2200000e
    + [(i, 1) for i in UA_RANKS + UA_STRIKES]                              # Unfair Advantage: A_1 0x20006
    + [(i, e) for i in (13742, 13872) for e in (2, 3)]                     # Endurance: stat aura B_1 0x20
    + [(i, e) for i in (13705, 13832, 13843) for e in (2, 3)]              # Precision eff1 / eff2
    + [(i, 2) for i in (13715, 13848, 13849)]                              # Dual Wield Spec eff1
)
# effects that must be emptied (type 0): (spell id, effect 1-based)
EMPTY_EFFECTS = (
    [(i, e) for i in (31124, 31126) for e in (2, 3)]
    + [(i, 2) for i in (51682, 58413)] + [(32601, 2)]
    + [(i, 2) for i in (13705, 13832, 13843)]
)

# ---- rank amounts the C++ reads (brief section 5, 10): (id, effect 1-based, aura or None, engine value) ------------------
AMOUNTS = (
    [(MARKER, 1, AURA_DUMMY, 25), (QD, 1, AURA_DUMMY, 1), (RB, 1, AURA_DUMMY, 1000)]
    + [(i, 1, AURA_DUMMY, v) for i, v in zip(DM, (50, 100))]
    + [(i, 1, AURA_DUMMY, v) for i, v in zip(HT, (4, 8))]
    + [(i, 1, AURA_DUMMY, v) for i, v in zip(CEL, (2, 4))]
    + [(IFEINT, 1, AURA_DUMMY, 10), (203982, 2, AURA_DUMMY, 40)]
    + [(i, 1, AURA_DUMMY, v) for i, v in zip((31124, 31126), (2, 4))]
    + [(i, 1, AURA_DUMMY, v) for i, v in zip((51685, 51686, 51687), (3, 6, 10))]
    + [(i, 2, AURA_DUMMY, v) for i, v in zip((51685, 51686, 51687), (5, 10, 15))]
    + [(i, 1, AURA_DUMMY, v) for i, v in zip((13960, 13961, 13962), (33, 66, 100))]
    + [(i, 3, AURA_DUMMY, v) for i, v in zip((13742, 13872), (10, 20))]
    + [(i, 1, AURA_FLAT, v) for i, v in zip((13742, 13872), (-30000, -60000))]
    + [(i, 1, AURA_PCT, v) for i, v in zip(CDG, (10, 20, 30))]
    + [(203972, 2, AURA_PERIODIC_DUMMY, 1)]
    + [(i, 1, 193, v) for i, v in zip(QR, (1, 2, 3))]
    + [(i, 1, 306, v) for i, v in zip(ACC, (2, 4, 6))]
    + [(i, 1, 142, v) for i, v in zip(RL, (15, 30, 45))]
    + [(i, 1, 47, v) for i, v in zip(IR, (1, 2, 3))]
    + [(i, 2, AURA_PCT, v) for i, v in zip(IR, (20, 40, 60))]
    + [(i, 1, AURA_PCT, v) for i, v in zip(SA_R, (2, 4, 6))]
    + [(i, 1, AURA_PCT, v) for i, v in zip((13732, 13863), (5, 10))]
    + [(i, 1, 290, v) for i, v in zip((13705, 13832, 13843), (1, 2, 3))]
    + [(i, 2, 290, v) for i, v in zip((13715, 13848, 13849), (1, 2, 3))]
    + [(i, 1, AURA_FLAT, v) for i, v in zip((18427, 18428, 18429), (5, 10, 15))]
    + [(i, 1, 280, v) for i, v in zip(WEAPON_SPEC_RANKS, (5, 10, 15))]
    + [(i, 1, AURA_PCT, v) for i, v in zip((14165, 14166), (25, 50))]
    + [(i, 2, AURA_FLAT, v) for i, v in zip((14165, 14166), (3, 6))]
    + [(i, 1, AURA_FLAT, v) for i, v in zip((13743, 13875), (1000, 2000))]
    + [(i, 2, 138, v) for i, v in zip((13712, 13788, 13789), (3, 6, 10))]
    + [(i, 1, 49, v) for i, v in zip((13712, 13788, 13789), (2, 4, 6))]
    + [(RIPOSTE, 3, None, 2)]
    + [(OPP_COMP, 1, AURA_PCT, -100), (OPP_COMP, 2, AURA_PCT, 50), (BR_BUFF, 1, AURA_PCT, 30),
       (AR_CEL, 1, 110, 100)]
)
# rank frames: id -> (tier row, rank); hidden passives, attributes 464 (brief section 10.15)
RANK_FRAMES = {LEARN: (2, 1), 203981: (8, 2), 203982: (8, 3)}      # Surprise Attacks r2 / r3 (32601 is rank 1)
for _row, _ids in ((0, QR), (0, ACC), (2, RL), (4, (QD,)), (5, (RB,)), (5, IR), (6, CDG), (6, DM), (6, HT), (7, CEL),
                   (7, (IFEINT,))):
    for _rank, _id in enumerate(_ids, 1):
        RANK_FRAMES[_id] = (_row, _rank)

# ---- scripts, procs, links, groups, attrs, SDV, consts --------------------------------------------------------------------

NEW_ID_SCRIPTS = {
    (PS, "spell_rog_pistol_shot"), (PS_EXTRA, "spell_rog_pistol_shot_extra"), (BTE, "spell_rog_between_the_eyes"),
    (DM_STRIKE, "spell_rog_deft_maneuvers_strike"), (BR, "spell_rog_blade_rush"), (GH, "spell_rog_grappling_hook"),
    (EG, "spell_rog_en_garde"), (203972, "spell_rog_coup_de_grace_mastery"),
    (SPRINT_HELPER, "spell_rog_improved_sprint_helper"), (ENDURANCE_HELPER, "spell_rog_endurance_helper"),
    (FEINT_HELPER, "spell_rog_improved_feint_helper"),
}
SCRIPTS = NEW_ID_SCRIPTS | {
    (SINISTER_STRIKE, "spell_rog_sinister_strike_combat"), (EVISCERATE, "spell_rog_eviscerate_combat"),
    (RIPOSTE, "spell_rog_riposte"), (BLADE_FLURRY, "spell_rog_blade_flurry_rework"),
    (KILLING_SPREE, "spell_rog_killing_spree_rework"), (-13960, "spell_rog_hack_and_slash"),
    (KICK, "spell_rog_kick_combat"),
}
KEPT_BINDINGS = {   # stay bound (S1 / S2 neighbours, brief section 8)
    (SINISTER_STRIKE, "spell_rog_sinister_strike_blindside"), (EVISCERATE, "spell_rog_eviscerate_subtlety"),
}
UNBOUND = {
    (BLADE_FLURRY, "spell_rog_blade_flurry"), (KILLING_SPREE, "spell_rog_killing_spree"),
    (-51685, "spell_rog_prey_on_the_weak"), (-35541, "spell_rog_combat_potency"),
    (-31130, "spell_rog_nerves_of_steel"),
}
PROC_REMOVED = (-35541, -31124)
PROC_ROWS = {   # spell id -> columns that must match (brief R1, section 8)
    -13960: {"ProcFlags": 0x14, "SpellTypeMask": 1, "SpellPhaseMask": 2, "Chance": 100.0},
    -51672: {"ProcFlags": 0x2028, "HitMask": 0x30, "Cooldown": 2000, "Chance": 0.0},
}
NO_PROC_ROWS = (HT_BUFF, OPP, OPP_COMP, PRIMED, SA_BUFF, BR_BUFF, ANTIC, BT_DEBUFF)
LINKS = {(OPP, OPP_COMP, 2), (SPRINT, SPRINT_HELPER, 2), (EVASION, ENDURANCE_HELPER, 2), (FEINT, FEINT_HELPER, 2)}
LINK_REMOVALS = {(KILLING_SPREE, 61851, 2)}
GROUPS = {1288: {ADRENALINE_RUSH, AR_CEL}}
GROUP_RULES = {1288: 1}
GROUP_1059_MEMBER = RIPOSTE
CUSTOM_ATTRS = {BF_COPY: 0x8000, EG: 0x6000000}
SDV_NEW = {1350: (SINISTER_STRIKE,), 1351: (PS,), 1352: (BTE,)}
SDV_ATTACH = {**SDV_NEW, 1323: (EVISCERATE,), 1335: (BACKSTAB,), 1336: (AMBUSH,)}
SDV_VARS = {   # variable names that must be defined by the entry (brief section 8)
    1350: {"impss", "surprise", "ssmult"}, 1351: {"surprise"}, 1352: {"cdg", "surprise", "btemult"},
    1323: {"seal", "cdg", "surprise", "evmult"}, 1335: {"bsmult", "surprise", "bsall"},
    1336: {"ammult", "surprise", "amall"},
}
TOOLTIP_TOKENS = {SINISTER_STRIKE: "ssmult", PS: "surprise", BTE: "btemult", EVISCERATE: "evmult",
                  BACKSTAB: "bsall", AMBUSH: "amall"}
CONSTS = {   # name -> (value, cpp type), brief section 6
    "ANTICIPATION_MAX_STACKS": (2, "int32"), "ANTICIPATION_POLL_MS": (100, "int32"),
    "ANTICIPATION_MISSILE_WAIT_MS": (1500, "int32"), "ADRENALINE_RUSH_EXTRA_POINTS": (1, "int32"),
    "CELERITY_DURATION_MS": (4000, "int32"), "OPPORTUNITY_EMPOWER_PCT": (50, "int32"),
    "SURPRISE_ATTACKS_EXTRA_SHOTS": (2, "int32"), "SURPRISE_SHOT_DELAY_MS": (200, "int32"),
    "IMPROVED_RIPOSTE_EXTRA_TARGETS": (2, "int32"), "IMPROVED_RIPOSTE_RADIUS_YD": (8.0, "float"),
    "DEFT_MANEUVERS_MIN_ENEMIES": (3, "int32"), "DEFT_MANEUVERS_MAX_POINTS": (5, "int32"),
    "DEFT_MANEUVERS_RADIUS_YD": (8.0, "float"), "BLADE_FLURRY_EXTRA_TARGETS": (4, "int32"),
    "BLADE_FLURRY_RADIUS_YD": (8.0, "float"), "BLADE_FLURRY_COPY_PCT": (20, "int32"),
    "PREY_DAMAGE_HEALTH_PCT": (35, "int32"), "PREY_CRIT_HEALTH_PCT": (90, "int32"),
    "HACK_AND_SLASH_CHANCE_PCT": (6, "int32"), "KILLING_SPREE_HOP_RANGE_YD": (10.0, "float"),
    "KILLING_SPREE_STRIKE_INTERVAL_MS": (500, "int32"), "GRAPPLE_SPEED_XY": (30.0, "float"),
    "GRAPPLE_APEX_YD": (1.0, "float"), "UNFAIR_ADVANTAGE_ICD_MS": (2000, "int32"), "EN_GARDE_PCT_PER_CP": (4, "int32"),
}
HEADER_NAMES = {   # brief section 2: generated RogueData:: name -> id
    "SPELL_QUICK_REFLEXES": 203950, "SPELL_QUICK_REFLEXES_203951": 203951, "SPELL_QUICK_REFLEXES_203952": 203952,
    "SPELL_ACCURACY": 203953, "SPELL_ACCURACY_203954": 203954, "SPELL_ACCURACY_203955": 203955,
    "SPELL_BETWEEN_THE_EYES_LEARN": LEARN, "SPELL_BETWEEN_THE_EYES_MARKER": MARKER, "SPELL_PISTOL_SHOT": PS,
    "SPELL_BETWEEN_THE_EYES": BTE, "SPELL_REINFORCED_LEATHER": 203960, "SPELL_REINFORCED_LEATHER_203961": 203961,
    "SPELL_REINFORCED_LEATHER_203962": 203962, "SPELL_GRAPPLING_HOOK": GH, "SPELL_QUICK_DRAW": QD,
    "SPELL_RESTLESS_BLADES": RB, "SPELL_IMPROVED_RIPOSTE": 203966, "SPELL_IMPROVED_RIPOSTE_203967": 203967,
    "SPELL_IMPROVED_RIPOSTE_203968": 203968, "SPELL_EN_GARDE": EG, "SPELL_COUP_DE_GRACE": 203970,
    "SPELL_COUP_DE_GRACE_203971": 203971, "SPELL_COUP_DE_GRACE_203972": 203972, "SPELL_DEFT_MANEUVERS": 203973,
    "SPELL_DEFT_MANEUVERS_203974": 203974, "SPELL_HAIR_TRIGGER": 203975, "SPELL_HAIR_TRIGGER_203976": 203976,
    "SPELL_CELERITY": 203977, "SPELL_CELERITY_203978": 203978, "SPELL_IMPROVED_FEINT": IFEINT, "SPELL_BLADE_RUSH": BR,
    "SPELL_SURPRISE_ATTACKS_203981": 203981, "SPELL_SURPRISE_ATTACKS_203982": 203982,
    "SPELL_OPPORTUNITY_BUFF": OPP, "SPELL_OPPORTUNITY_COMPANION": OPP_COMP, "SPELL_PRIMED_POWDER": PRIMED,
    "SPELL_SINISTER_STRIKE_SECOND_STRIKE": SECOND, "SPELL_HAIR_TRIGGER_BUFF": HT_BUFF,
    "SPELL_PISTOL_SHOT_EXTRA": PS_EXTRA, "SPELL_SURPRISE_ATTACKS_BUFF": SA_BUFF, "SPELL_BLADE_RUSH_BUFF": BR_BUFF,
    "SPELL_BLADE_FLURRY_COPY": BF_COPY, "SPELL_DEFT_MANEUVERS_STRIKE": DM_STRIKE,
    "SPELL_IMPROVED_RIPOSTE_CLEAVE": IR_CLEAVE, "SPELL_HACK_AND_SLASH_MAIN": HS_MAIN, "SPELL_HACK_AND_SLASH_OFF": HS_OFF,
    "SPELL_ADRENALINE_RUSH_CELERITY": AR_CEL, "SPELL_ANTICIPATION": ANTIC, "SPELL_BLADE_TWISTING_DEBUFF": BT_DEBUFF,
    "SPELL_IMPROVED_KICK_BUFF": IK_BUFF, "SPELL_IMPROVED_SPRINT_HELPER": SPRINT_HELPER,
    "SPELL_ENDURANCE_HELPER": ENDURANCE_HELPER, "SPELL_IMPROVED_FEINT_HELPER": FEINT_HELPER,
    "SPELL_PREY_ON_THE_WEAK_CRIT": PREY_DEBUFF,
    # collisions the brief forbids: the stock / S1 / S2 stems keep their own ids
    "SPELL_OPPORTUNITY": 14057, "SPELL_ADRENALINE_RUSH": 13750, "SPELL_SURPRISE_ATTACKS": 32601,
    # pulled stock rows (WP-0.2)
    "SPELL_PRECISION": 13705, "SPELL_LIGHTNING_REFLEXES": 13712, "SPELL_WEAPON_SPECIALIZATION": 13709,
    "SPELL_HACK_AND_SLASH": 13960, "SPELL_UNFAIR_ADVANTAGE": 51672, "SPELL_UNFAIR_ADVANTAGE_STRIKE": 51675,
    "SPELL_PREY_ON_THE_WEAK": 51685, "SPELL_KILLING_SPREE_MAIN": KS_MAIN, "SPELL_KILLING_SPREE_OFF": KS_OFF,
}

VISIBLE = (OPP, PRIMED, HT_BUFF, SA_BUFF, BR_BUFF, AR_CEL, ANTIC, IK_BUFF, BT_DEBUFF, EG, BLADE_FLURRY, ADRENALINE_RUSH)
HIDDEN = (LEARN, MARKER, OPP_COMP, SECOND, PS_EXTRA, BF_COPY, DM_STRIKE, IR_CLEAVE, HS_MAIN, HS_OFF, SPRINT_HELPER,
          ENDURANCE_HELPER, FEINT_HELPER, PREY_DEBUFF)
NOT_PASSIVE_HELPERS = (SPRINT_HELPER, ENDURANCE_HELPER, FEINT_HELPER)
EX1_SELF_BUFFS = (OPP, PRIMED, HT_BUFF, SA_BUFF, BR_BUFF, AR_CEL, ANTIC, IK_BUFF, SPRINT_HELPER, ENDURANCE_HELPER,
                  FEINT_HELPER)
WEAPON_ROWS = (SECOND, DM_STRIKE, IR_CLEAVE, HS_MAIN, HS_OFF, BR)   # weapon attacks keep a weapon requirement
NO_COMBO_ATTRS = (SECOND, PS_EXTRA, BF_COPY, DM_STRIKE, IR_CLEAVE, HS_MAIN, HS_OFF, PS)
TEXTS = {   # verbatim (brief section 10, doc sections 4-5)
    OPP: "Your next Pistol Shot is free and deals more damage.",
    PRIMED: "Your next Between the Eyes deals more damage.",
    HT_BUFF: "Your next Pistol Shot deals more damage.",
    SA_BUFF: "Your next Pistol Shot fires additional times.",
    BR_BUFF: "Your next finishing move deals more damage.",
    AR_CEL: "Energy regeneration increased. Your builders award more combo points.",
    ADRENALINE_RUSH: "Energy regeneration increased. Your builders award more combo points.",
    ANTIC: "Extra combo points are stored for after your next finishing move.",
    IK_BUFF: "Energy restored and attack speed increased.",
    BT_DEBUFF: "Taking more damage from the rogue's strikes.",
    EG: "Damage taken reduced.",
    BLADE_FLURRY: "Your attacks strike nearby enemies.",
}


def value_of(row: dict, effect: int) -> int:
    """The engine's CalcValue at level-independent terms: stored base points + 1 when DieSides is 1."""
    base = _i(row, f"EffectBasePoints_{effect}")
    if base >= 0x80000000:
        base -= 0x100000000
    return base + (1 if _i(row, f"EffectDieSides_{effect}") == 1 else 0)


def _lvl(tier: int, rank: int) -> int:
    return 9 + 5 * tier + rank


# ---- expectations ------------------------------------------------------------------------------------------------------

def expectations(idx: dict) -> tuple[dict, dict, dict]:
    """(EXACT, MUST_SET, MUST_CLEAR). `idx` carries reuse-minted duration indices: infinite, d<ms>."""
    inf = idx["infinite"]
    exact = {
        # ---- Between the Eyes talent: learn rank, marker, castables (brief 10.3, R25)
        LEARN: {"Effect_1": LEARN_SPELL, "EffectTriggerSpell_1": PS, "Effect_2": LEARN_SPELL,
                "EffectTriggerSpell_2": BTE, "Effect_3": LEARN_SPELL, "EffectTriggerSpell_3": MARKER,
                "SpellLevel": 20, "SpellIconID": 538},
        MARKER: {"Attributes": HIDDEN_PASSIVE_ATTR, "Effect_1": APPLY_AURA, "EffectAura_1": AURA_DUMMY,
                 "EquippedItemClass": -1},
        PS: {"Effect_1": SCHOOL_DAMAGE, "Effect_2": ADD_COMBO, "SchoolMask": 1, "ManaCost": 30, "RangeIndex": RANGE_20,
             "Speed": 0, "DefenseType": 2, "EquippedItemClass": -1, "FacingCasterFlags": 1,
             "StartRecoveryCategory": 133, "StartRecoveryTime": 1000, "SpellLevel": 20, "SpellVisualID_1": 90252,
             "SpellIconID": 90374, "ImplicitTargetA_1": 6},
        BTE: {"Effect_1": SCHOOL_DAMAGE, "Attributes": 327696, "AttributesEx": 0x100200, "PreventionType": 2,
              "SchoolMask": 1, "ManaCost": 35, "RangeIndex": RANGE_20, "Speed": 0, "DefenseType": 2,
              "EquippedItemClass": -1, "StartRecoveryCategory": 133, "StartRecoveryTime": 1000, "SpellLevel": 20,
              "SpellVisualID_1": 90252, "SpellIconID": 538},
        # ---- Opportunity / Primed Powder / Hair Trigger / Surprise Attacks buffs
        OPP: {"CumulativeAura": 3, "DurationIndex": idx["d20000"], "SpellIconID": 1631, "EquippedItemClass": -1},
        OPP_COMP: {"CumulativeAura": 0, "DurationIndex": idx["d20000"], "EquippedItemClass": -1},
        PRIMED: {"CumulativeAura": 5, "SpellIconID": 1196, "EquippedItemClass": -1},
        HT_BUFF: {"ProcCharges": 1, "DurationIndex": idx["d15000"], "SpellIconID": 351, "EquippedItemClass": -1},
        SA_BUFF: {"Effect_1": APPLY_AURA, "EffectAura_1": AURA_DUMMY, "DurationIndex": idx["d20000"],
                  "SpellIconID": 2334, "EquippedItemClass": -1},
        BR_BUFF: {"DurationIndex": idx["d15000"], "SpellIconID": 2769, "EquippedItemClass": -1, "ProcCharges": 0},
        AR_CEL: {"Effect_1": APPLY_AURA, "EffectAura_1": 110, "EffectMiscValue_1": 3, "DurationIndex": idx["d4000"],
                 "SpellIconID": 235, "EquippedItemClass": -1},
        ANTIC: {"Effect_1": APPLY_AURA, "EffectAura_1": AURA_DUMMY, "CumulativeAura": 2, "DurationIndex": idx["d20000"],
                "SpellIconID": 494, "EquippedItemClass": -1},
        BT_DEBUFF: {"Effect_1": APPLY_AURA, "EffectAura_1": 271, "CumulativeAura": 5, "DurationIndex": idx["d12000"],
                    "ImplicitTargetA_1": 6, "RangeIndex": RANGE_100, "FacingCasterFlags": 0, "SpellIconID": 2108,
                    "EquippedItemClass": -1},
        IK_BUFF: {"SpellIconID": 2022, "EquippedItemClass": -1},
        # ---- the second strike, extra shot, Blade Flurry copy (brief 10.15)
        SECOND: {"Effect_1": WEAPON_PCT, "Effect_2": NORMALIZED_WEAPON, "RangeIndex": RANGE_100, "FacingCasterFlags": 0,
                 "DefenseType": 2},
        PS_EXTRA: {"Effect_1": SCHOOL_DAMAGE, "RangeIndex": RANGE_100, "FacingCasterFlags": 0, "DefenseType": 2,
                   "EquippedItemClass": -1, "SchoolMask": 1},
        BF_COPY: {"Effect_1": SCHOOL_DAMAGE, "ImplicitTargetA_1": 6, "SchoolMask": 1, "DefenseType": 0,
                  "RangeIndex": RANGE_100, "FacingCasterFlags": 0, "EquippedItemClass": -1},
        # ---- weapon strikes (R13, R20)
        DM_STRIKE: {"Effect_1": WEAPON_PCT, "ImplicitTargetA_1": 22, "MaxTargets": 0, "SpellLevel": 40},
        IR_CLEAVE: {"Effect_1": WEAPON_PCT, "ImplicitTargetA_1": 6, "RangeIndex": RANGE_100, "FacingCasterFlags": 0,
                    "SpellLevel": 35},
        HS_MAIN: {"Effect_1": WEAPON_PCT, "ImplicitTargetA_1": 6, "RangeIndex": RANGE_100, "FacingCasterFlags": 0,
                  "DefenseType": 2, "SpellLevel": 30},
        HS_OFF: {"Effect_1": WEAPON_PCT, "ImplicitTargetA_1": 6, "RangeIndex": RANGE_100, "FacingCasterFlags": 0,
                 "DefenseType": 2, "SpellLevel": 30},
        # ---- castables: En Garde (R14 frame), Grappling Hook, Blade Rush
        EG: {"Effect_1": DUMMY_EFFECT, "ImplicitTargetA_1": 6, "Effect_2": APPLY_AURA, "EffectAura_2": 87,
             "EffectMiscValue_2": 127, "ImplicitTargetA_2": 1, "EffectPointsPerCombo_2": -4, "AttributesEx": 0x400420,
             "AttributesEx2": 0x4, "PreventionType": 2, "RangeIndex": RANGE_100, "DurationIndex": 8,
             "ManaCost": 0, "RecoveryTime": 0, "StartRecoveryCategory": 133, "StartRecoveryTime": 1000,
             "SpellLevel": 35, "SpellIconID": 2781, "EquippedItemClass": -1},
        GH: {"Targets": 0x40, "Effect_1": DUMMY_EFFECT, "ImplicitTargetA_1": 28, "RangeIndex": RANGE_40,
             "StartRecoveryCategory": 0, "ManaCost": 0, "RecoveryTime": 45000, "SpellLevel": 25,
             "SpellVisualID_1": 90253, "SpellMissileID": 0, "SpellIconID": 3149, "EquippedItemClass": -1},
        BR: {"Effect_1": CHARGE, "ImplicitTargetA_1": 6, "Effect_2": WEAPON_PCT, "ImplicitTargetA_2": 53,
             "ImplicitTargetB_2": 16, "EffectRadiusIndex_2": RADIUS_5YD, "RangeIndex": RANGE_20, "ManaCost": 0,
             "RecoveryTime": 45000, "StartRecoveryCategory": 133, "StartRecoveryTime": 1000, "SpellLevel": 50,
             "SpellVisualID_1": 90254, "SpellIconID": 457},
        # ---- helpers and debuffs (brief 10.8, section 9 item 16)
        SPRINT_HELPER: {"Effect_1": APPLY_AURA, "EffectAura_1": 232, "EffectMiscValue_1": 7, "Effect_2": APPLY_AURA,
                        "EffectAura_2": 305, "DurationIndex": inf, "EquippedItemClass": -1},
        ENDURANCE_HELPER: {"Effect_1": APPLY_AURA, "EffectAura_1": 87, "EffectMiscValue_1": 126, "DurationIndex": inf,
                           "EquippedItemClass": -1},
        FEINT_HELPER: {"Effect_1": APPLY_AURA, "EffectAura_1": 87, "DurationIndex": inf, "EquippedItemClass": -1},
        PREY_DEBUFF: {"Effect_1": APPLY_AURA, "EffectAura_1": 308, "ImplicitTargetA_1": 6, "RangeIndex": RANGE_100,
                      "FacingCasterFlags": 0, "DurationIndex": idx["d5000"], "EquippedItemClass": -1},
        # ---- stock rows edited
        BLADE_FLURRY: {"Effect_1": APPLY_AURA, "EffectAura_1": AURA_DUMMY, "DurationIndex": idx["d12000"],
                       "RecoveryTime": 30000, "ManaCost": 0, "StartRecoveryCategory": 133, "StartRecoveryTime": 1000,
                       "ProcTypeMask": 0, "ProcChance": 101},
        ADRENALINE_RUSH: {"StartRecoveryCategory": 0, "StartRecoveryTime": 0, "RecoveryTime": 120000},
        KILLING_SPREE: {"AttributesEx": 0x400400, "ManaCost": 25, "RecoveryTime": 120000, "DurationIndex": idx["d2000"]},
        RIPOSTE: {"Effect_3": ADD_COMBO},
        KS_MAIN: {"AttributesEx3": 0x10601, "AttributesEx4": 0x800000},
        KS_OFF: {"AttributesEx3": 0x1010201, "AttributesEx4": 0x800080},
        31124: {"ProcTypeMask": 0, "ProcChance": 101, "EquippedItemClass": -1, "EquippedItemSubclass": 0},
        31126: {"ProcTypeMask": 0, "ProcChance": 101, "EquippedItemClass": -1, "EquippedItemSubclass": 0},
        32601: {"ProcTypeMask": 0, "ProcChance": 101},
        51685: {"ProcTypeMask": 0, "ProcChance": 101}, 51686: {"ProcTypeMask": 0, "ProcChance": 101},
        51687: {"ProcTypeMask": 0, "ProcChance": 101},
        13960: {"ProcTypeMask": 0x14, "EquippedItemClass": -1, "EquippedItemSubclass": 0},
        13961: {"ProcTypeMask": 0x14, "EquippedItemClass": -1, "EquippedItemSubclass": 0},
        13962: {"ProcTypeMask": 0x14, "EquippedItemClass": -1, "EquippedItemSubclass": 0},
        51672: {"ProcTypeMask": 0x2028, "ProcChance": 100, "Effect_1": APPLY_AURA, "EffectAura_1": 42,
                "EffectTriggerSpell_1": 51675},
        51674: {"ProcTypeMask": 0x2028, "ProcChance": 100, "Effect_1": APPLY_AURA, "EffectAura_1": 42,
                "EffectTriggerSpell_1": 51677},
        51675: {"SpellClassSet": 8}, 51677: {"SpellClassSet": 8},
        13705: {"EquippedItemClass": -1, "EquippedItemSubclass": 0},
        13832: {"EquippedItemClass": -1, "EquippedItemSubclass": 0},
        13843: {"EquippedItemClass": -1, "EquippedItemSubclass": 0},
        13709: {"EquippedItemClass": -1, "EquippedItemSubclass": 0},
        13800: {"EquippedItemClass": -1, "EquippedItemSubclass": 0},
        13801: {"EquippedItemClass": -1, "EquippedItemSubclass": 0},
    }
    for sid, (tier, rank) in RANK_FRAMES.items():          # hidden passive frames (brief 10.15)
        exact.setdefault(sid, {}).update({"Attributes": HIDDEN_PASSIVE_ATTR, "EquippedItemClass": -1,
                                          "SpellLevel": _lvl(tier, rank), "ProcTypeMask": 0, "ProcChance": 101,
                                          "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0})
    must_set = {
        PS_EXTRA: {"AttributesEx3": EX3_SUPPRESS_CASTER, "Attributes": ATTR0_HIDDEN},
        SECOND: {"AttributesEx3": EX3_SUPPRESS_CASTER, "AttributesEx4": 0x800000, "Attributes": ATTR0_HIDDEN},
        BF_COPY: {"AttributesEx3": EX3_IGNORE_CASTER_MODS | EX3_ALWAYS_HIT | EX3_SUPPRESS_CASTER,
                  "AttributesEx2": EX2_CANT_CRIT, "Attributes": ATTR0_HIDDEN},
        DM_STRIKE: {"Attributes": ATTR0_HIDDEN, "AttributesEx3": EX3_REQ_MAIN | EX3_NOT_A_PROC, "SpellVisualID_1": 223},
        IR_CLEAVE: {"AttributesEx3": EX3_SUPPRESS_CASTER, "Attributes": ATTR0_HIDDEN},
        HS_MAIN: {"AttributesEx3": EX3_REQ_MAIN | EX3_SUPPRESS_CASTER, "Attributes": ATTR0_HIDDEN,
                 "SpellVisualID_1": 39},
        HS_OFF: {"AttributesEx3": EX3_REQ_OFF | EX3_SUPPRESS_CASTER, "Attributes": ATTR0_HIDDEN,
                 "SpellVisualID_1": 39},
        BT_DEBUFF: {"AttributesEx3": EX3_STACK_PER_CASTER},
        PREY_DEBUFF: {"AttributesEx": 0x400, "AttributesEx3": EX3_SUPPRESS_TARGET | EX3_STACK_PER_CASTER,
                      "Attributes": ATTR0_HIDDEN},
        BTE: {"AttributesEx": 0x100000},
        KILLING_SPREE: {"AttributesEx5": 0x200},
    }
    for sid in EX1_SELF_BUFFS:
        must_set.setdefault(sid, {})["AttributesEx"] = EX1_STEALTH_OK
    for sid in HIDDEN:
        must_set.setdefault(sid, {})["Attributes"] = must_set.get(sid, {}).get("Attributes", 0) | ATTR0_HIDDEN
    must_clear = {
        BTE: {"AttributesEx3": EX3_REQ_MAIN},                                  # R25: no REQUIRES_MAIN_HAND
        PS: {"AttributesEx3": EX3_REQ_MAIN},
        GH: {"AttributesEx2": 0x4},                                            # keeps its line-of-sight check
        DM_STRIKE: {"AttributesEx3": EX3_SUPPRESS_CASTER},                     # R13: poisons roll per enemy
        BR: {"AttributesEx3": EX3_SUPPRESS_CASTER},
        KILLING_SPREE: {"AttributesEx": 0x20},                                 # R6: the core ORs ALLOW_WHILE_STEALTHED
        ADRENALINE_RUSH: {"AttributesEx": 0x20},                               # user ruling: breaks Stealth like stock
    }
    for sid in VISIBLE:
        must_clear[sid] = {"Attributes": must_clear.get(sid, {}).get("Attributes", 0) | ATTR0_PASSIVE | ATTR0_HIDDEN}
    for sid in NOT_PASSIVE_HELPERS:
        must_clear.setdefault(sid, {})["Attributes"] = ATTR0_PASSIVE
    for sid in NO_COMBO_ATTRS:
        must_clear.setdefault(sid, {})["AttributesEx"] = COMBO_ATTRS
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


def check_names(rows: dict) -> list[str]:
    return [f"{sid}: name {rows.get(sid, {}).get('Name_Lang_enUS')!r}, expected 'Weapon Specialization'"
            for sid in WEAPON_SPEC_RANKS if rows.get(sid, {}).get("Name_Lang_enUS") != "Weapon Specialization"]


def check_s3_id_set(rows: dict) -> list[str]:
    bad = [f"{sid}: S3 row not built" for sid in S3_IDS if sid not in rows]
    bad += [f"{sid}: unexpected row (204004-204129 are spare / unassigned)" for sid in S3_SPARE if sid in rows]
    return bad


def check_texts(rows: dict) -> list[str]:
    bad = []
    for sid, text in TEXTS.items():
        got = rows.get(sid, {}).get("AuraDescription_Lang_enUS")
        if got != text:
            bad.append(f"{sid}: aura text {got!r}, expected {text!r}")
        elif re.search(r"\d", got):
            bad.append(f"{sid}: aura text {got!r} holds a number (aura texts are number-free)")
    return bad


def check_visibility(rows: dict) -> list[str]:
    bad = []
    for sid in VISIBLE:
        attrs = _u32(rows.get(sid, {}).get("Attributes"))
        if attrs & (ATTR0_PASSIVE | ATTR0_HIDDEN):
            bad.append(f"{sid}: a visible buff carries Attributes {attrs:#x} (passive 0x40 / hidden 0x80)")
    for sid in HIDDEN:
        if not _u32(rows.get(sid, {}).get("Attributes")) & ATTR0_HIDDEN:
            bad.append(f"{sid}: not hidden (Attributes 0x80)")
    for sid in S3_IDS:
        r = rows.get(sid)
        if r is None or sid in WEAPON_ROWS:
            continue
        if _u32(r.get("EquippedItemClass")) != 0xFFFFFFFF:
            bad.append(f"{sid}: EquippedItemClass {r.get('EquippedItemClass')!r}, expected -1 on a non-weapon row")
    return bad


def check_effect_absence(rows: dict) -> list[str]:
    """Emptied effects are type 0; Improved Sprint r1 keeps no aura 109; Endurance keeps no Sprint clause."""
    bad = []
    for sid, eff in EMPTY_EFFECTS:
        r = rows.get(sid)
        if r is None:
            bad.append(f"{sid}: not built")
        elif _i(r, f"Effect_{eff}") != 0:
            bad.append(f"{sid}: effect {eff} is type {r.get(f'Effect_{eff}')!r}, expected emptied (0)")
    for e in (1, 2, 3):
        if _i(rows.get(13743, {}), f"EffectAura_{e}") == 109:
            bad.append(f"13743: effect {e} still aura 109 (rank 1 carries the duration only)")
    for sid in (32601, 203981, 203982):
        for e in (1, 2, 3):
            if _i(rows.get(sid, {}), f"EffectAura_{e}") == 202:
                bad.append(f"{sid}: effect {e} still aura 202 (finishers undodgeable goes)")
    return bad


def check_second_effects(rows: dict) -> list[str]:
    """Riposte's third effect grants the points; 13867 holds the capstone marker; Improved Sprint r2's slow removal."""
    bad = []
    if _i(rows.get(13867, {}), "Effect_2") != APPLY_AURA or _i(rows.get(13867, {}), "EffectAura_2") != AURA_DUMMY:
        bad.append("13867: effect 2 is not the APPLY_AURA DUMMY capstone marker")
    if _i(rows.get(13875, {}), "Effect_3") != APPLY_AURA or _i(rows.get(13875, {}), "EffectAura_3") != AURA_DUMMY:
        bad.append("13875: effect 3 is not the APPLY_AURA DUMMY capstone marker")
    return bad


# ---- carriers, masks, readers --------------------------------------------------------------------------------------------

def check_carriers(rows: dict) -> list[str]:
    bad = []
    for (dword, bit), want in NEW_BIT_CARRIERS.items():
        have = {sid for sid, r in rows.items() if spell_mask(r)[dword] & bit}
        if have != want:
            bad.append(f"d{dword} {bit:#x}: carriers {sorted(have)}, expected exactly {sorted(want)}")
    for (dword, bit), want in GROUP_MEMBERS.items():
        have = {sid for sid, r in rows.items() if spell_mask(r)[dword] & bit}
        for sid in sorted(want - have):
            bad.append(f"d{dword} {bit:#x}: {sid} does not carry the group bit")
        for sid in sorted(have & set(COPY_ROWS) & set(CARRIER_CLASS if bit == D2_B19 else ())):
            bad.append(f"d{dword} {bit:#x}: copy {sid} carries the group bit")
    return bad


def check_new_masks(rows: dict) -> list[str]:
    """Every new row: SpellClassSet 8; own mask exactly the carrier mask or zero; never-bits; copies carry no builder bits."""
    bad = []
    for sid in S3_IDS + (KS_MAIN, KS_OFF) + UA_STRIKES:
        r = rows.get(sid)
        if r is None:
            bad.append(f"{sid}: not built")
            continue
        if sid not in RANK_FRAMES and _i(r, "SpellClassSet") != 8:
            bad.append(f"{sid}: SpellClassSet {r.get('SpellClassSet')!r}, expected 8")
        mask = spell_mask(r)
        want = CARRIER_CLASS.get(sid, (0, 0, 0))
        if mask != want:
            bad.append(f"{sid}: spell mask ({', '.join(hex(w) for w in mask)}), expected "
                       f"({', '.join(hex(w) for w in want)})")
        if mask[0] & FORBIDDEN_S3_D0:
            bad.append(f"{sid}: d0 holds a never-bit ({mask[0] & FORBIDDEN_S3_D0:#x}: b11 / b22 / b25 / b26)")
    for sid in (RIPOSTE, KILLING_SPREE):                       # stock rows whose whole mask S3 sets
        r = rows.get(sid)
        if r is not None and spell_mask(r) != CARRIER_CLASS[sid]:
            bad.append(f"{sid}: spell mask {tuple(hex(w) for w in spell_mask(r))}, expected "
                       f"{tuple(hex(w) for w in CARRIER_CLASS[sid])}")
    if _u32(rows.get(BTE, {}).get("SpellClassMask_1")) & D0_B17:
        bad.append(f"{BTE}: Between the Eyes carries d0 b17 (Eviscerate's AP hardcode / S1-S2 readers)")
    for sid in (SECOND, PS_EXTRA, BF_COPY, DM_STRIKE, IR_CLEAVE, HS_MAIN, HS_OFF, KS_MAIN, KS_OFF):
        mask = spell_mask(rows.get(sid, {}))
        for n in range(3):
            if mask[n] & FORBIDDEN_COPY[n]:
                bad.append(f"{sid}: a copy / triggered strike carries a builder bit (dword {n} {mask[n] & FORBIDDEN_COPY[n]:#x})")
    for sid in NO_BIT_ROWS + UA_STRIKES:
        if any(spell_mask(rows.get(sid, {}))):
            bad.append(f"{sid}: must carry no family bit at all ({tuple(hex(w) for w in spell_mask(rows.get(sid, {})))})")
    return bad


def check_readers(rows: dict) -> list[str]:
    bad = []
    for sid, eff, comp, aura, op in READERS:
        r = rows.get(sid)
        if r is None:
            bad.append(f"{sid}: not built")
            continue
        want = COMPOSITES[comp]
        got = effect_mask(r, eff)                 # letter = effect, number = dword (the raw keys)
        if got != want:
            bad.append(f"{sid}: effect {eff} mask {tuple(hex(w) for w in got)}, expected {comp} "
                       f"{tuple(hex(w) for w in want)}")
        if aura is not None and _i(r, f"EffectAura_{eff}") != aura:
            bad.append(f"{sid}: effect {eff} aura {r.get(f'EffectAura_{eff}')!r}, expected {aura}")
        if op is not None and _i(r, f"EffectMiscValue_{eff}") != op:
            bad.append(f"{sid}: effect {eff} SpellMod op {r.get(f'EffectMiscValue_{eff}')!r}, expected {op}")
    for sid, eff in EMPTY_MASKS:
        r = rows.get(sid)
        if r is None:
            bad.append(f"{sid}: not built")
        elif any(effect_mask(r, eff)):
            bad.append(f"{sid}: effect {eff} still reads a mask {tuple(hex(w) for w in effect_mask(r, eff))} (stale twin)")
    return bad


def check_composites(module) -> list[str]:
    bad = []
    for name, want in COMPOSITES.items():
        got = getattr(module, name, None)
        got = tuple(got) if isinstance(want, tuple) and got is not None else got
        if got != want:
            show = lambda v: tuple(hex(w) for w in v) if isinstance(v, tuple) else v  # noqa: E731
            bad.append(f"_masks.{name} = {show(got)}, expected {show(want)}")
    if getattr(module, "FORBIDDEN_S3_D0", None) != FORBIDDEN_S3_D0:
        bad.append(f"_masks.FORBIDDEN_S3_D0 = {getattr(module, 'FORBIDDEN_S3_D0', None)!r}, expected {FORBIDDEN_S3_D0:#x}")
    if getattr(module, "FORBIDDEN_BETWEEN_THE_EYES_D0", None) != D0_B17:
        bad.append("_masks.FORBIDDEN_BETWEEN_THE_EYES_D0 is not d0 b17")
    if tuple(getattr(module, "FORBIDDEN_COPY_S3", ())) != FORBIDDEN_COPY:
        bad.append(f"_masks.FORBIDDEN_COPY_S3 = {getattr(module, 'FORBIDDEN_COPY_S3', None)!r}, expected {FORBIDDEN_COPY!r}")
    return bad


# ---- grid / tables -----------------------------------------------------------------------------------------------------

def check_grid(talents: list[dict], retired: list[dict], tab_text: str) -> list[str]:
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
        if got != ranks:
            bad.append(f"talent {tid}: ranks {got}, expected {ranks}")
        if t.get("depends_on"):
            bad.append(f"talent {tid}: has an arrow (depends_on {t['depends_on']})")
        if tid in FLAGS and int(t.get("flags") or 0) != FLAGS[tid]:
            bad.append(f"talent {tid}: flags {t.get('flags')!r}, expected {FLAGS[tid]}")
        cells.setdefault((int(t["tier"]), int(t["column"])), []).append(tid)
        row_points[tier] += len(got)
    for cell, ids in cells.items():
        if len(ids) > 1:
            bad.append(f"cell {cell}: shared by {ids}")
    if len(seen) != TALENT_COUNT or sum(row_points) != POINT_COUNT:
        bad.append(f"{len(seen)} talents / {sum(row_points)} points, expected {TALENT_COUNT} / {POINT_COUNT}")
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
    if not re.search(r"combat_181_tab\s*=\s*tab\((?:[^()]|\([^()]*\))*?skill_line\s*=\s*38\b", tab_text, re.S):
        bad.append("tab 181 does not declare skill_line=38")
    return bad


def check_slas(slas: list[dict]) -> list[str]:
    by_id = {int(s["id"]): s for s in slas if int(s["id"]) in SLA_RANGE}
    bad = []
    if sorted(by_id) != sorted(SLA_ROWS):
        bad.append(f"SkillLineAbility ids in 30810-30824: {sorted(by_id)}, expected {sorted(SLA_ROWS)}")
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
    bad += [f"script {n} no longer bound to {s} (a neighbour's binding)" for s, n in sorted(KEPT_BINDINGS - bound)]
    for pair in sorted(bound & unbound):
        bad.append(f"{pair}: both bound and unbound")
    for pair in sorted(KEPT_BINDINGS & unbound):
        bad.append(f"{pair}: unbound, but the brief keeps it")
    taken = {s for s, _n in NEW_ID_SCRIPTS}
    for s in sorted({s for s, _n in bound if 203950 <= s <= 204129} - taken):
        bad.append(f"{s}: bound to a script (only {sorted(taken)} take one)")
    return bad


def check_procs(procs: list[dict], removals: list[dict]) -> list[str]:
    bad = []
    gone = {int(r["SpellId"]) for r in removals}
    for sid in PROC_REMOVED:
        if sid not in gone:
            bad.append(f"spell_proc {sid}: removal not declared")
    for sid, cols in PROC_ROWS.items():
        rows = [p for p in procs if int(p["SpellId"]) == sid]
        if len(rows) != 1:
            bad.append(f"{sid}: {len(rows)} spell_proc rows, expected 1")
            continue
        p = rows[0]
        for k, v in cols.items():
            got = float(p.get(k) or 0) if isinstance(v, float) else int(p.get(k) or 0)
            if got != v:
                bad.append(f"{sid}: {k} = {p.get(k)!r}, expected {v}")
    for sid in NO_PROC_ROWS:
        if any(int(p["SpellId"]) == sid for p in procs):
            bad.append(f"{sid}: has a spell_proc row (charged / stacked auras roll nothing)")
    return bad


def check_links_groups_attrs(links: list[dict], link_rem: list[dict], groups: list[dict], rules: list[dict],
                             attrs: list[dict]) -> list[str]:
    bad = []
    got = {(int(x["spell_trigger"]), int(x["spell_effect"]), int(x["type"])) for x in links
           if (int(x["spell_trigger"]), int(x["spell_effect"]), int(x["type"])) in LINKS}
    if got != LINKS:
        bad.append(f"S3 linked spells {sorted(got)}, expected {sorted(LINKS)}")
    gone = {(int(x["spell_trigger"]), int(x["spell_effect"]), int(x["type"])) for x in link_rem}
    for key in sorted(LINK_REMOVALS - gone):
        bad.append(f"linked spell {key}: removal not declared")
    for gid, want in GROUPS.items():
        have = {int(g["spell_id"]) for g in groups if int(g["id"]) == gid}
        if have != want:
            bad.append(f"group {gid} holds {sorted(have)}, expected {sorted(want)}")
    for gid, rule in GROUP_RULES.items():
        have = [int(r["stack_rule"]) for r in rules if int(r["group_id"]) == gid]
        if have != [rule]:
            bad.append(f"group {gid} stack rules {have}, expected one with stack_rule {rule}")
    if not any(int(g["id"]) == 1059 and int(g["spell_id"]) == GROUP_1059_MEMBER for g in groups):
        bad.append(f"spell_group 1059 lacks member {GROUP_1059_MEMBER} (Riposte's slow)")
    a = {int(x["spell_id"]): int(x["attributes"]) for x in attrs}
    for sid, want in CUSTOM_ATTRS.items():
        if a.get(sid) != want:
            bad.append(f"{sid}: custom attr {a.get(sid)!r}, expected {want:#x}")
    return bad


def check_sdv(entries: list[dict], rows: dict) -> list[str]:
    bad = []
    by_id = {int(e["id"]): e for e in entries}
    for sdv in SDV_ATTACH:
        if sdv not in by_id:
            bad.append(f"SDV {sdv}: not declared")
    for sdv in sorted(i for i in by_id if 1350 <= i <= 1364 and i not in SDV_NEW):
        bad.append(f"SDV {sdv}: unexpected (1353-1364 spare)")
    for sdv in SDV_ATTACH:
        e = by_id.get(sdv)
        if e is None:
            continue
        names = DEFINED_NAME.findall(str(e.get("Variables") or ""))
        for name in names:
            if len(name) > MAX_NAME_LENGTH:
                bad.append(f"SDV {sdv}: variable name {name!r} is {len(name)} chars (max {MAX_NAME_LENGTH})")
            if len(name) > 10:
                bad.append(f"SDV {sdv}: variable name {name!r} is {len(name)} chars (names <= 10 so helper suffixes fit)")
        for name in sorted(SDV_VARS[sdv] - set(names)):
            bad.append(f"SDV {sdv}: variable {name!r} not defined")
    for sdv, spells in SDV_ATTACH.items():
        for sid in spells:
            if _i(rows.get(sid, {}), "SpellDescriptionVariableID") != sdv:
                bad.append(f"{sid}: SpellDescriptionVariableID {rows.get(sid, {}).get('SpellDescriptionVariableID')!r}, "
                           f"expected {sdv}")
    return bad


def check_tooltips(rows: dict) -> list[str]:
    bad = []
    for sid, token in TOOLTIP_TOKENS.items():
        text = str(rows.get(sid, {}).get("Description_Lang_enUS") or "")
        if token not in text:
            bad.append(f"{sid}: tooltip lacks the talent factor `{token}`")
    return bad


def check_consts(consts: dict) -> list[str]:
    """`consts`: name -> (value, cpp_type)."""
    bad = []
    for k, (v, t) in CONSTS.items():
        if k not in consts:
            bad.append(f"const {k} missing")
            continue
        got_v, got_t = consts[k]
        if got_v != v:
            bad.append(f"const {k} = {got_v!r}, expected {v!r}")
        if got_t != t:
            bad.append(f"const {k} cpp type {got_t!r}, expected {t!r}")
    return bad


def check_header(text: str) -> list[str]:
    """Every brief section 2 name resolves to its id in the generated RogueData.h; the consts carry their values."""
    found = {n: int(v) for n, v in re.findall(r"constexpr\s+uint32\s+(\w+)\s*=\s*(\d+)\s*;", text)}
    bad = []
    for name, sid in HEADER_NAMES.items():
        if name not in found:
            bad.append(f"RogueData.h: {name} missing")
        elif found[name] != sid:
            bad.append(f"RogueData.h: {name} = {found[name]}, expected {sid}")
    for name, (v, _t) in CONSTS.items():
        mt = re.search(rf"constexpr\s+\w+\s+{name}\s*=\s*([-\d.]+)f?\s*;", text)
        if mt is None:
            bad.append(f"RogueData.h: const {name} missing")
        elif float(mt.group(1)) != float(v):
            bad.append(f"RogueData.h: const {name} = {mt.group(1)}, expected {v}")
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
        idx = {"infinite": reuse.duration_index(0)}
        for ms in (2000, 4000, 5000, 12000, 15000, 20000):
            idx[f"d{ms}"] = reuse.duration_index(ms)
        _CACHE.update(package=package, rows=by_id, idx=idx)
    return _CACHE


class RogueS3DataTest(unittest.TestCase):
    def assertClean(self, problems: list[str]):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_s3_row_set(self):
        self.assertClean(check_s3_id_set(_data()["rows"]))

    def test_rows(self):
        d = _data()
        self.assertClean(check_rows(d["rows"], *expectations(d["idx"])))

    def test_names(self):
        self.assertClean(check_names(_data()["rows"]))

    def test_value_cases(self):
        self.assertClean(check_value_cases(_data()["rows"], AMOUNTS))

    def test_effect_absence(self):
        self.assertClean(check_effect_absence(_data()["rows"]) + check_second_effects(_data()["rows"]))

    def test_tooltips(self):
        self.assertClean(check_tooltips(_data()["rows"]))

    def test_texts(self):
        self.assertClean(check_texts(_data()["rows"]))

    def test_visibility(self):
        self.assertClean(check_visibility(_data()["rows"]))

    def test_carriers(self):
        self.assertClean(check_carriers(_data()["rows"]))

    def test_new_row_masks(self):
        self.assertClean(check_new_masks(_data()["rows"]))

    def test_readers(self):
        self.assertClean(check_readers(_data()["rows"]))

    def test_masks_module_composites(self):
        self.assertClean(check_composites(m))

    def test_grid(self):
        p = _data()["package"]
        text = (ROGUE_DIR / "rogue_talents.py").read_text(encoding="utf-8")
        self.assertClean(check_grid(p.talents, p.retired_talents, text))

    def test_skill_line_abilities(self):
        self.assertClean(check_slas(_data()["package"].skill_line_abilities))

    def test_scripts(self):
        p = _data()["package"]
        self.assertClean(check_scripts(p.spell_script_names, p.script_removals))

    def test_procs(self):
        p = _data()["package"]
        self.assertClean(check_procs(p.spell_procs, p.proc_removals))

    def test_links_groups_and_custom_attrs(self):
        p = _data()["package"]
        self.assertClean(check_links_groups_attrs(p.linked_spells, p.linked_spell_removals, p.spell_groups,
                                                  p.spell_group_rules, p.custom_attrs))

    def test_sdv(self):
        d = _data()
        self.assertClean(check_sdv(d["package"].tooltip_vars, d["rows"]))

    def test_consts(self):
        self.assertClean(check_consts({c["name"]: (c["value"], c["cpp_type"]) for c in _data()["package"].consts}))


class RogueS3HeaderTest(unittest.TestCase):
    """The generated header (the orchestrator's regen): names and consts. Failing before the regen is expected."""

    def test_header(self):
        path = TOOL_ROOT.parents[1] / "src" / "server" / "game" / "Entities" / "Unit" / "Generated" / "RogueData.h"
        self.assertEqual(check_header(path.read_text(encoding="utf-8")), [])


# ---- negative fixtures: every check must fire on a minimal bad input -----------------------------------------------------

IDX = {"d2000": 39, "d5000": 9, "infinite": 21, "d4000": 35, "d12000": 29, "d15000": 8, "d20000": 18}


def _good_rows() -> dict:
    exact, must_set, _clear = expectations(IDX)
    rows: dict[int, dict] = {}
    for sid, cols in exact.items():
        rows.setdefault(sid, {"ID": sid}).update({c: (v & 0xFFFFFFFF if isinstance(v, int) and v < 0 else v)
                                                  for c, v in cols.items()})
    for sid, cols in must_set.items():
        row = rows.setdefault(sid, {"ID": sid})
        for col, bits in cols.items():
            row[col] = _u32(row.get(col)) | bits
    return rows


def _copy(rows: dict) -> dict:
    return {k: dict(v) for k, v in rows.items()}


def _good_full_rows() -> dict:
    """Rows satisfying the id-set / carrier / mask / reader / value / text / visibility checks too."""
    rows = _good_rows()
    for sid in S3_IDS + (KS_MAIN, KS_OFF) + UA_STRIKES:
        r = rows.setdefault(sid, {"ID": sid})
        r["SpellClassSet"] = 8
        for n, w in enumerate(CARRIER_CLASS.get(sid, (0, 0, 0)), 1):
            r[f"SpellClassMask_{n}"] = w
        if sid not in WEAPON_ROWS:
            r["EquippedItemClass"] = 0xFFFFFFFF
        if sid in HIDDEN:
            r["Attributes"] = _u32(r.get("Attributes")) | ATTR0_HIDDEN
    for sid in (RIPOSTE, KILLING_SPREE):
        for n, w in enumerate(CARRIER_CLASS[sid], 1):
            rows.setdefault(sid, {"ID": sid})[f"SpellClassMask_{n}"] = w
    for sid, eff, comp, aura, op in READERS:
        r = rows.setdefault(sid, {"ID": sid})
        for n, w in enumerate(COMPOSITES[comp], 1):
            r[f"EffectSpellClassMask{'ABC'[eff - 1]}_{n}"] = w
        if aura is not None:
            r[f"EffectAura_{eff}"] = aura
        if op is not None:
            r[f"EffectMiscValue_{eff}"] = op
    for sid, eff in EMPTY_MASKS:
        r = rows.setdefault(sid, {"ID": sid})
        for n in (1, 2, 3):
            r[f"EffectSpellClassMask{'ABC'[eff - 1]}_{n}"] = 0
    for sid, eff in EMPTY_EFFECTS:
        rows.setdefault(sid, {"ID": sid})[f"Effect_{eff}"] = 0
    for sid, eff, aura, value in AMOUNTS:
        r = rows.setdefault(sid, {"ID": sid})
        r[f"EffectBasePoints_{eff}"] = (value - 1) & 0xFFFFFFFF
        r[f"EffectDieSides_{eff}"] = 1
        if aura is not None:
            r[f"EffectAura_{eff}"] = aura
    rows.setdefault(13867, {"ID": 13867}).update({"Effect_2": APPLY_AURA, "EffectAura_2": AURA_DUMMY})
    rows.setdefault(13875, {"ID": 13875}).update({"Effect_3": APPLY_AURA, "EffectAura_3": AURA_DUMMY})
    for sid, text in TEXTS.items():
        rows.setdefault(sid, {"ID": sid})["AuraDescription_Lang_enUS"] = text
    for sid in VISIBLE:
        r = rows.setdefault(sid, {"ID": sid})
        r["Attributes"] = _u32(r.get("Attributes")) & ~(ATTR0_PASSIVE | ATTR0_HIDDEN)
    for sid, token in TOOLTIP_TOKENS.items():
        rows.setdefault(sid, {"ID": sid})["Description_Lang_enUS"] = f"x {{pot1*{token}}}"
    return rows


class RogueS3NegativeTest(unittest.TestCase):
    def test_rows_clean_fixture(self):
        self.assertEqual(check_rows(_good_rows(), *expectations(IDX)), [])

    def test_every_exact_expectation_can_fail(self):
        exact, ms, mc = expectations(IDX)
        for sid, cols in exact.items():
            for col, want in cols.items():
                rows = _good_rows()
                rows[sid][col] = "bogus" if isinstance(want, str) else ((_u32(want) ^ 0x4) if want else 0x4)
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
        for sid, col, val in ((PS, "Speed", 20), (BTE, "Speed", 30), (PS, "EquippedItemClass", 2),
                              (BTE, "AttributesEx3", EX3_REQ_MAIN), (PS, "AttributesEx3", EX3_REQ_MAIN),
                              (BTE, "DefenseType", 0), (PS, "DefenseType", 0), (KILLING_SPREE, "AttributesEx", 0x400420),
                              (KILLING_SPREE, "AttributesEx", 0x400), (ADRENALINE_RUSH, "StartRecoveryCategory", 133),
                              (ADRENALINE_RUSH, "RecoveryTime", 180000), (GH, "StartRecoveryCategory", 133),
                              (GH, "AttributesEx2", 0x4), (EG, "EffectPointsPerCombo_2", 4), (EG, "EffectPointsPerCombo_2", 0),
                              (EG, "DurationIndex", 185), (EG, "EffectMiscValue_2", 126), (OPP_COMP, "CumulativeAura", 3),
                              (HT_BUFF, "ProcCharges", 0), (ANTIC, "CumulativeAura", 3), (BT_DEBUFF, "CumulativeAura", 3),
                              (DM_STRIKE, "MaxTargets", 5), (DM_STRIKE, "AttributesEx3", EX3_SUPPRESS_CASTER),
                              (BR, "AttributesEx3", EX3_SUPPRESS_CASTER), (KS_MAIN, "AttributesEx3", 0x601),
                              (KS_OFF, "AttributesEx4", 0x80), (LEARN, "EffectTriggerSpell_3", BTE),
                              (BF_COPY, "DefenseType", 2), (BF_COPY, "FacingCasterFlags", 1),
                              (PREY_DEBUFF, "EffectAura_1", 305), (BLADE_FLURRY, "ProcChance", 100),
                              (51672, "ProcTypeMask", 0x2000), (13960, "ProcTypeMask", 0)):
            rows = _good_rows()
            if col == "AttributesEx3" and sid in (BTE, PS):
                rows[sid][col] = _u32(rows[sid].get(col)) | val
            elif col == "AttributesEx3" and val == EX3_SUPPRESS_CASTER:
                rows[sid][col] = _u32(rows[sid].get(col)) | val
            elif col == "AttributesEx2":
                rows[sid][col] = _u32(rows[sid].get(col)) | val
            else:
                rows[sid][col] = val
            self.assertGreaterEqual(len(check_rows(rows, exact, ms, mc)), 1, (sid, col, val))

    def test_missing_row(self):
        rows = _good_rows()
        del rows[PS]
        self.assertGreaterEqual(len(check_rows(rows, *expectations(IDX))), 1)

    def test_names(self):
        rows = {sid: {"Name_Lang_enUS": "Weapon Specialization"} for sid in WEAPON_SPEC_RANKS}
        self.assertEqual(check_names(rows), [])
        for sid in WEAPON_SPEC_RANKS:
            self.assertEqual(len(check_names({**rows, sid: {"Name_Lang_enUS": "Mace Specialization"}})), 1, sid)
        self.assertEqual(len(check_names({})), 3)

    def test_s3_row_set(self):
        rows = {sid: {} for sid in S3_IDS}
        self.assertEqual(check_s3_id_set(rows), [])
        self.assertEqual(len(check_s3_id_set({k: v for k, v in rows.items() if k != PS})), 1)
        for extra in (204004, 204029, 204030, 204129):
            self.assertEqual(len(check_s3_id_set({**rows, extra: {}})), 1, extra)
        self.assertEqual(len(check_s3_id_set({**rows, 204130: {}})), 0)       # S2's first row is not a stray

    def test_value_cases(self):
        rows = _good_full_rows()
        self.assertEqual(check_value_cases(rows, AMOUNTS), [])
        for sid, eff, aura, value in AMOUNTS:
            bad = _copy(rows)
            bad[sid][f"EffectBasePoints_{eff}"] = (value + 1) & 0xFFFFFFFF
            self.assertGreaterEqual(len(check_value_cases(bad, AMOUNTS)), 1, (sid, eff, "value"))
            if aura is not None:
                bad = _copy(rows)
                bad[sid][f"EffectAura_{eff}"] = aura + 1
                self.assertGreaterEqual(len(check_value_cases(bad, AMOUNTS)), 1, (sid, eff, "aura"))
        self.assertEqual(len(check_value_cases({k: v for k, v in rows.items() if k != QD}, AMOUNTS)), 1)
        self.assertEqual(value_of({"EffectBasePoints_1": (-101) & 0xFFFFFFFF, "EffectDieSides_1": 1}, 1), -100)
        self.assertEqual(value_of({"EffectBasePoints_1": 5, "EffectDieSides_1": 0}, 1), 5)

    def test_effect_absence(self):
        rows = _good_full_rows()
        self.assertEqual(check_effect_absence(rows) + check_second_effects(rows), [])
        for sid, eff in EMPTY_EFFECTS:
            bad = _copy(rows)
            bad[sid][f"Effect_{eff}"] = APPLY_AURA
            self.assertGreaterEqual(len(check_effect_absence(bad)), 1, (sid, eff))
        bad = _copy(rows)
        bad[13743]["EffectAura_2"] = 109
        self.assertEqual(len(check_effect_absence(bad)), 1)
        bad = _copy(rows)
        bad[203982]["EffectAura_1"] = 202
        self.assertEqual(len(check_effect_absence(bad)), 1)
        for sid, eff in ((13867, 2), (13875, 3)):
            bad = _copy(rows)
            bad[sid][f"Effect_{eff}"] = 0
            self.assertEqual(len(check_second_effects(bad)), 1, sid)

    def test_tooltips(self):
        rows = _good_full_rows()
        self.assertEqual(check_tooltips(rows), [])
        for sid in TOOLTIP_TOKENS:
            bad = _copy(rows)
            bad[sid]["Description_Lang_enUS"] = "no factor"
            self.assertEqual(len(check_tooltips(bad)), 1, sid)

    def test_texts_and_visibility(self):
        rows = _good_full_rows()
        self.assertEqual(check_texts(rows), [])
        self.assertEqual(check_visibility(rows), [])
        for sid in TEXTS:
            bad = _copy(rows)
            bad[sid]["AuraDescription_Lang_enUS"] = TEXTS[sid] + " "
            self.assertEqual(len(check_texts(bad)), 1, sid)
            bad[sid]["AuraDescription_Lang_enUS"] = TEXTS[sid] + " 5"
            self.assertGreaterEqual(len(check_texts(bad)), 1, sid)
        for sid in HIDDEN:
            bad = _copy(rows)
            bad[sid]["Attributes"] = 0
            self.assertEqual(len(check_visibility(bad)), 1, sid)
        for sid in VISIBLE:
            for flag in (ATTR0_PASSIVE, ATTR0_HIDDEN):
                bad = _copy(rows)
                bad[sid]["Attributes"] = _u32(bad[sid].get("Attributes")) | flag
                self.assertEqual(len(check_visibility(bad)), 1, (sid, flag))
        for sid in S3_IDS:                                   # R25 and the non-weapon rule: EquippedItemClass -1
            if sid in WEAPON_ROWS:
                continue
            bad = _copy(rows)
            bad[sid]["EquippedItemClass"] = 2
            self.assertEqual(len(check_visibility(bad)), 1, sid)

    def test_carriers(self):
        rows = _good_full_rows()
        self.assertEqual(check_carriers(rows), [])
        for (dword, bit), who in NEW_BIT_CARRIERS.items():
            col = f"SpellClassMask_{dword + 1}"
            gone = _copy(rows)                                   # a carrier loses the bit
            victim = sorted(who)[0]
            gone[victim][col] = _u32(gone[victim].get(col)) & ~bit
            self.assertGreaterEqual(len(check_carriers(gone)), 1, ((dword, bit), "missing"))
            extra = _copy(rows)                                   # a stranger gains it
            extra[203950][col] = _u32(extra[203950].get(col)) | bit
            self.assertGreaterEqual(len(check_carriers(extra)), 1, ((dword, bit), "extra"))
            extra = _copy(rows)                                   # a non-S3 row too (the bits are exact across all rows)
            extra[999999] = {"ID": 999999, col: bit}
            self.assertGreaterEqual(len(check_carriers(extra)), 1, ((dword, bit), "stranger"))
        for (dword, bit), who in GROUP_MEMBERS.items():
            col = f"SpellClassMask_{dword + 1}"
            gone = _copy(rows)
            victim = sorted(who)[0]
            gone[victim][col] = _u32(gone[victim].get(col)) & ~bit
            self.assertGreaterEqual(len(check_carriers(gone)), 1, ((dword, bit), "group member lost"))

    def test_new_masks(self):
        rows = _good_full_rows()
        self.assertEqual(check_new_masks(rows), [])
        bad = _copy(rows)
        bad[BF_COPY]["SpellClassMask_3"] = 0x1000
        self.assertGreaterEqual(len(check_new_masks(bad)), 1)               # the copy carries nothing
        bad = _copy(rows)
        bad[PS]["SpellClassSet"] = 0
        self.assertEqual(len(check_new_masks(bad)), 1)
        for sid, col, bit in ((PS, "SpellClassMask_1", D0_B11), (BTE, "SpellClassMask_1", D0_B22),
                              (EG, "SpellClassMask_1", D0_B25), (BR, "SpellClassMask_1", D0_B26),
                              (QR[0], "SpellClassMask_1", D0_B11),
                              (BTE, "SpellClassMask_1", D0_B17),                     # never d0 b17 on Between the Eyes
                              (SECOND, "SpellClassMask_1", D0_B1),                   # no Sinister Strike identity on a copy
                              (SECOND, "SpellClassMask_3", D2_B19), (PS_EXTRA, "SpellClassMask_3", D2_B4),
                              (PS_EXTRA, "SpellClassMask_3", D2_B19), (IR_CLEAVE, "SpellClassMask_3", D2_B19),
                              (KS_MAIN, "SpellClassMask_3", D2_B19), (KS_OFF, "SpellClassMask_1", D0_B1),
                              (HS_MAIN, "SpellClassMask_1", 0x1), (HS_OFF, "SpellClassMask_2", 0x1),
                              (SPRINT_HELPER, "SpellClassMask_3", 0x1), (PREY_DEBUFF, "SpellClassMask_2", 0x1),
                              (BT_DEBUFF, "SpellClassMask_3", 0x1), (51675, "SpellClassMask_1", 0x20006),
                              (51677, "SpellClassMask_3", 0x1), (RIPOSTE, "SpellClassMask_3", 0x40000),
                              (KILLING_SPREE, "SpellClassMask_3", 0x80000)):
            bad = _copy(rows)
            bad[sid][col] = _u32(bad[sid].get(col)) | bit
            self.assertGreaterEqual(len(check_new_masks(bad)), 1, (sid, col, bit))
        bad = _copy(rows)
        bad[51675]["SpellClassSet"] = 0                                          # C14: family 8 so the hooks see the strikes
        self.assertEqual(len(check_new_masks(bad)), 1)
        for sid in (RIPOSTE, KILLING_SPREE):                                     # whole-mask rows lose a bit
            bad = _copy(rows)
            col = "SpellClassMask_3"
            bad[sid][col] = _u32(bad[sid].get(col)) & ~(0x80000 | 0x40000)
            self.assertGreaterEqual(len(check_new_masks(bad)), 1, sid)

    def test_readers(self):
        rows = _good_full_rows()
        self.assertEqual(check_readers(rows), [])
        for sid, eff, comp, aura, op in READERS:
            for n in (1, 2, 3):                                              # each dword on its own
                if not COMPOSITES[comp][n - 1]:
                    continue
                bad = _copy(rows)
                col = f"EffectSpellClassMask{'ABC'[eff - 1]}_{n}"
                bad[sid][col] = _u32(bad[sid].get(col)) ^ 0x1
                self.assertGreaterEqual(len(check_readers(bad)), 1, (sid, eff, n, "mask"))
            wrong_letter = _copy(rows)          # the wrong-effect-letter trap (bug-doc :2178): mask on the neighbour effect
            for n in (1, 2, 3):
                wrong_letter[sid][f"EffectSpellClassMask{'ABC'[eff % 3]}_{n}"] = COMPOSITES[comp][n - 1]
                wrong_letter[sid][f"EffectSpellClassMask{'ABC'[eff - 1]}_{n}"] = 0
            self.assertGreaterEqual(len(check_readers(wrong_letter)), 1, (sid, eff, "letter"))
            swapped = _copy(rows)               # the letter/dword swap (A_2 where B_1 was meant)
            for n in (1, 2, 3):
                swapped[sid][f"EffectSpellClassMask{'ABC'[eff - 1]}_{n}"] = 0
            for n in (1, 2, 3):
                swapped[sid][f"EffectSpellClassMask{'ABC'[n - 1]}_{eff}"] = COMPOSITES[comp][n - 1]
            if effect_mask(swapped[sid], eff) != COMPOSITES[comp]:
                self.assertGreaterEqual(len(check_readers(swapped)), 1, (sid, eff, "dword swap"))
            if aura is not None:
                bad = _copy(rows)
                bad[sid][f"EffectAura_{eff}"] = aura + 1
                self.assertGreaterEqual(len(check_readers(bad)), 1, (sid, eff, "aura"))
            if op is not None:
                bad = _copy(rows)
                bad[sid][f"EffectMiscValue_{eff}"] = op + 1
                self.assertGreaterEqual(len(check_readers(bad)), 1, (sid, eff, "op"))
        for sid, eff in EMPTY_MASKS:                                       # a stale twin on an emptied effect
            for n in (1, 2, 3):
                bad = _copy(rows)
                bad[sid][f"EffectSpellClassMask{'ABC'[eff - 1]}_{n}"] = 0x400000
                self.assertGreaterEqual(len(check_readers(bad)), 1, (sid, eff, n, "stale twin"))
        self.assertGreaterEqual(len(check_readers({})), 1)

    def test_composites(self):
        class Mod:
            FORBIDDEN_S3_D0 = D0_B11 | D0_B22 | D0_B25 | D0_B26
            FORBIDDEN_BETWEEN_THE_EYES_D0 = D0_B17
            FORBIDDEN_COPY_S3 = FORBIDDEN_COPY
        good = Mod()
        for name, value in COMPOSITES.items():
            setattr(good, name, value)
        self.assertEqual(check_composites(good), [])
        for name, value in COMPOSITES.items():
            bad = Mod()
            for n, v in COMPOSITES.items():
                setattr(bad, n, v)
            setattr(bad, name, (value[0] ^ 1,) + value[1:] if isinstance(value, tuple) else value ^ 1)
            self.assertEqual(len(check_composites(bad)), 1, name)
        self.assertGreaterEqual(len(check_composites(Mod())), len(COMPOSITES))
        for attr, wrong in (("FORBIDDEN_S3_D0", 0), ("FORBIDDEN_BETWEEN_THE_EYES_D0", 0x40000),
                            ("FORBIDDEN_COPY_S3", (0, 0, 0))):
            bad = Mod()
            for n, v in COMPOSITES.items():
                setattr(bad, n, v)
            setattr(bad, attr, wrong)
            self.assertEqual(len(check_composites(bad)), 1, attr)

    def test_grid(self):
        def good():
            out = [{"id": tid, "tab_id": TAB, "tier": t, "column": c, "rank_spell_ids": list(r), "depends_on": None,
                    "flags": FLAGS.get(tid, 0)} for tid, (t, c, r) in GRID.items()]
            out += [{"id": tid, "tab_id": RETIRED_TAB, "tier": 0, "column": 0, "rank_spell_ids": [], "depends_on": None,
                     "flags": 0} for tid in RETIRED]
            return out
        tab_text = "combat_181_tab = tab(\n    id=181,\n    skill_line=38,  # (note)\n    raw_overrides={},\n)\n"
        ret = [{"id": t} for t in RETIRED]
        self.assertEqual(check_grid(good(), ret, tab_text), [])
        idx = lambda ts, tid: next(t for t in ts if t["id"] == tid)  # noqa: E731
        cases = []
        g = good(); idx(g, 60405)["tier"] = 1; cases.append(("moved", g))
        g = good(); idx(g, 206)["column"] = 3; cases.append(("moved col", g))
        g = good(); idx(g, 206)["tier"] = 3; idx(g, 206)["column"] = 0; cases.append(("Improved Kick back at (3,0)", g))
        g = good(); idx(g, 301)["depends_on"] = {"talent_id": 187, "rank": 1}; cases.append(("arrow (Riposte)", g))
        g = good(); idx(g, 1709)["depends_on"] = {"talent_id": 205, "rank": 1}; cases.append(("arrow (Surprise)", g))
        g = good(); idx(g, 181)["rank_spell_ids"] = [13705, 13832, 13843, 13844, 13845]; cases.append(("5 Precision ranks", g))
        g = good(); idx(g, 1709)["rank_spell_ids"] = [32601]; cases.append(("Surprise Attacks 1 rank", g))
        g = good(); idx(g, 60412)["rank_spell_ids"] = [203967, 203966, 203968]; cases.append(("rank order", g))
        g = good(); g = [t for t in g if t["id"] != 60419]; cases.append(("missing", g))
        g = good(); idx(g, 203)["tab_id"] = TAB; cases.append(("203 not retired", g))
        g = good(); idx(g, 1825)["rank_spell_ids"] = [35541]; cases.append(("1825 ranked", g))
        g = good(); g.append({"id": 9999, "tab_id": TAB, "tier": 7, "column": 0, "rank_spell_ids": [1], "depends_on": None,
                              "flags": 0})
        cases.append(("extra", g))
        g = good(); idx(g, 60406)["column"] = 2; cases.append(("shared cell", g))
        g = good(); g.append(dict(idx(g, 205))); cases.append(("duplicate", g))
        for tid in FLAGS:
            g = good(); idx(g, tid)["flags"] = 1 - FLAGS[tid]; cases.append((f"flags {tid}", g))
        for label, talents in cases:
            self.assertGreaterEqual(len(check_grid(talents, ret, tab_text)), 1, label)
        self.assertGreaterEqual(len(check_grid(good(), ret[1:], tab_text)), 1)
        self.assertGreaterEqual(len(check_grid(good(), ret, tab_text.replace("38", "253"))), 1)
        self.assertGreaterEqual(len(check_grid(good(), ret, tab_text.replace("    skill_line=38,  # (note)\n", ""))), 1)
        # the declared grid is self-consistent
        self.assertEqual(len(GRID), TALENT_COUNT)
        self.assertEqual(sum(len(r) for _t, _c, r in GRID.values()), POINT_COUNT)

    def test_slas(self):
        good = [{"id": sid, "skill_line": line, "spell_id": spell, "class_mask": 8, "acquire_method": 0}
                for sid, (line, spell) in SLA_ROWS.items()]
        self.assertEqual(check_slas(good), [])
        self.assertGreaterEqual(len(check_slas(good[1:])), 1)
        self.assertGreaterEqual(len(check_slas(good + [{**good[0], "id": 30815}])), 1)
        for i in range(len(good)):
            for col, val in (("skill_line", 253), ("spell_id", 5), ("class_mask", 0), ("acquire_method", 1)):
                bad = [dict(x) for x in good]
                bad[i][col] = val
                self.assertEqual(len(check_slas(bad)), 1, (i, col))

    def test_scripts(self):
        names = [{"spell_id": s, "ScriptName": n} for s, n in sorted(SCRIPTS | KEPT_BINDINGS)]
        rem = [{"spell_id": s, "ScriptName": n} for s, n in sorted(UNBOUND)]
        self.assertEqual(check_scripts(names, rem), [])
        self.assertEqual(len(SCRIPTS), 18)
        for i, n in enumerate(names):
            self.assertEqual(len(check_scripts(names[:i] + names[i + 1:], rem)), 1, n)
        for i in range(len(rem)):
            self.assertEqual(len(check_scripts(names, rem[:i] + rem[i + 1:])), 1, rem[i])
        self.assertEqual(len(check_scripts(names + [{"spell_id": 13877, "ScriptName": "spell_rog_blade_flurry"}], rem)), 1)
        for stray in (203983, 203991, 203997, 204003, 204129):
            self.assertEqual(len(check_scripts(names + [{"spell_id": stray, "ScriptName": "spell_x"}], rem)), 1, stray)

    def test_procs(self):
        rem = [{"SpellId": s} for s in PROC_REMOVED]

        def row(sid):
            return {"SpellId": sid, **{k: v for k, v in PROC_ROWS[sid].items()}}
        good = [row(-13960), row(-51672)]
        self.assertEqual(check_procs(good, rem), [])
        self.assertEqual(len(check_procs(good[1:], rem)), 1)
        self.assertEqual(len(check_procs(good + [good[0]], rem)), 1)
        for i in range(len(rem)):
            self.assertEqual(len(check_procs(good, rem[:i] + rem[i + 1:])), 1, rem[i])
        for which, sid in enumerate(PROC_ROWS):
            for col, val in (("ProcFlags", 0x4), ("SpellPhaseMask", 1), ("HitMask", 2), ("Chance", 50.0), ("Cooldown", 1),
                             ("SpellTypeMask", 2)):
                if col not in PROC_ROWS[sid]:
                    continue
                bad = [dict(good[0]), dict(good[1])]
                bad[which][col] = val if val != PROC_ROWS[sid][col] else val + 1
                self.assertGreaterEqual(len(check_procs(bad, rem)), 1, (sid, col))
        for sid in NO_PROC_ROWS:
            self.assertEqual(len(check_procs(good + [{"SpellId": sid}], rem)), 1, sid)

    def test_links_groups_attrs(self):
        links = [{"spell_trigger": a, "spell_effect": b, "type": t} for a, b, t in sorted(LINKS)]
        rem = [{"spell_trigger": a, "spell_effect": b, "type": t} for a, b, t in sorted(LINK_REMOVALS)]
        groups = [{"id": gid, "spell_id": s} for gid, ss in GROUPS.items() for s in sorted(ss)]
        groups.append({"id": 1059, "spell_id": RIPOSTE})
        rules = [{"group_id": gid, "stack_rule": r} for gid, r in GROUP_RULES.items()]
        attrs = [{"spell_id": s, "attributes": v} for s, v in CUSTOM_ATTRS.items()]
        self.assertEqual(check_links_groups_attrs(links, rem, groups, rules, attrs), [])
        for i in range(len(links)):
            self.assertEqual(len(check_links_groups_attrs(links[:i] + links[i + 1:], rem, groups, rules, attrs)), 1, i)
            bad = [dict(x) for x in links]
            bad[i]["type"] = 1
            self.assertEqual(len(check_links_groups_attrs(bad, rem, groups, rules, attrs)), 1, i)
        self.assertEqual(len(check_links_groups_attrs(links, [], groups, rules, attrs)), 1)       # 61851 unlink
        self.assertEqual(len(check_links_groups_attrs(links, rem, groups[1:], rules, attrs)), 1)  # a group 1288 member gone
        self.assertEqual(len(check_links_groups_attrs(links, rem, groups[:-1], rules, attrs)), 1)  # Riposte in 1059
        self.assertEqual(len(check_links_groups_attrs(links, rem, groups + [{"id": 1288, "spell_id": 5}], rules, attrs)), 1)
        self.assertEqual(len(check_links_groups_attrs(links, rem, groups, [], attrs)), 1)
        self.assertEqual(len(check_links_groups_attrs(links, rem, groups, [{**rules[0], "stack_rule": 0}], attrs)), 1)
        self.assertEqual(len(check_links_groups_attrs(links, rem, groups, rules + rules, attrs)), 1)
        self.assertEqual(len(check_links_groups_attrs(links, rem, groups, rules, attrs[1:])), 1)
        self.assertEqual(len(check_links_groups_attrs(links, rem, groups, rules, [{**attrs[0], "attributes": 0x4000}] + attrs[1:])), 1)
        self.assertEqual(len(check_links_groups_attrs(links, rem, groups, rules, [attrs[0], {**attrs[1], "attributes": 0x2000000}])), 1)

    def test_sdv(self):
        def body(sdv):
            return "".join(f"${n}=1\r\n" for n in sorted(SDV_VARS.get(sdv, ())))
        entries = [{"id": i, "Variables": body(i)} for i in sorted(SDV_ATTACH)]
        rows = {sid: {"SpellDescriptionVariableID": sdv} for sdv, ss in SDV_ATTACH.items() for sid in ss}
        self.assertEqual(check_sdv(entries, rows), [])
        for sdv in sorted(SDV_ATTACH):
            self.assertGreaterEqual(len(check_sdv([e for e in entries if e["id"] != sdv], rows)), 1, sdv)
        self.assertEqual(len(check_sdv(entries + [{"id": 1353, "Variables": ""}], rows)), 1)
        long_name = [{**e, "Variables": e["Variables"] + "$averyverylongname=1"} if e["id"] == 1350 else e for e in entries]
        self.assertGreaterEqual(len(check_sdv(long_name, rows)), 1)
        eleven = [{**e, "Variables": e["Variables"] + "$abcdefghijk=1"} if e["id"] == 1350 else e for e in entries]
        self.assertEqual(len(check_sdv(eleven, rows)), 1)                      # 11 chars: fits the 12 limit, not the 10 rule
        for sdv, names in SDV_VARS.items():
            for name in names:
                trimmed = [{**e, "Variables": e["Variables"].replace(f"${name}=1\r\n", "")} if e["id"] == sdv else e
                           for e in entries]
                self.assertEqual(len(check_sdv(trimmed, rows)), 1, (sdv, name))
        for sid in (SINISTER_STRIKE, PS, BTE, EVISCERATE, BACKSTAB, AMBUSH):
            bad = _copy(rows)
            bad[sid]["SpellDescriptionVariableID"] = 0
            self.assertEqual(len(check_sdv(entries, bad)), 1, sid)

    def test_consts(self):
        good = dict(CONSTS)
        self.assertEqual(check_consts(good), [])
        for name, (v, t) in CONSTS.items():
            self.assertEqual(len(check_consts({k: x for k, x in CONSTS.items() if k != name})), 1, name)
            self.assertEqual(len(check_consts({**CONSTS, name: (v + 1, t)})), 1, name)
            self.assertEqual(len(check_consts({**CONSTS, name: (v, "float" if t == "int32" else "int32")})), 1, name)

    def test_header(self):
        lines = [f"    constexpr uint32 {n} = {v};" for n, v in HEADER_NAMES.items()]
        lines += [f"    constexpr {'float' if t == 'float' else 'int32'} {n} = {v}{'f' if t == 'float' else ''};"
                  for n, (v, t) in CONSTS.items()]
        text = "\n".join(lines)
        self.assertEqual(check_header(text), [])
        for n in HEADER_NAMES:
            self.assertEqual(len(check_header(text.replace(f"uint32 {n} =", f"uint32 X_{n} ="))), 1, n)
            self.assertEqual(len(check_header(text.replace(f"uint32 {n} = {HEADER_NAMES[n]};",
                                                           f"uint32 {n} = {HEADER_NAMES[n] + 1};"))), 1, n)
        for n, (v, t) in CONSTS.items():
            self.assertEqual(len(check_header(text.replace(f" {n} =", f" X_{n} ="))), 1, n)
        self.assertGreaterEqual(len(check_header("")), len(HEADER_NAMES))


if __name__ == "__main__":
    unittest.main()
