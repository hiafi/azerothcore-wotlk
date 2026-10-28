"""
Rogue S2a data gate (rogue-rework S2a-HANDOFF WP-A row A5, S2a-WP-BRIEF sections 2-6, 8, 10, 12 and the harness addenda).

Loads the real rogue DSL package (source/classes/rogue/) and asserts on the BUILT rows (stock base + DSL + raw_overrides via
`build.build_spell_row`), like test_rogue_s1.py. Every check is a pure function over built rows / package tables; the
negative tests prove each can fail (every single expectation is mutated on its own against a fixture that satisfies all of
them). Expected values are written out here from the brief, never imported from `_masks.py` (the module's composites are
pinned against the brief's literals instead).

  1. Talent grid: tab 183 = the 31 talents in the doc's cells, ranks, 69 points, row totals 8/9/9/9/6/7/7/5/6/2/1, no arrows,
     flags, tab skill line 39, tab 181 = 27 talents without 2072, the six retired on 60800, SLA 30825 (Death from Above).
  2. Row expectations (EXACT / MUST_SET / MUST_CLEAR): the 44 new rows 204130-204173 and the stock rows S2 edits (51713,
     36554, 45182, the rank spells), brief R1-R3, R10-R12, R15, R19, R22; spare ids absent.
  3. Family bits on exactly their carriers, new-row masks, the never-bits, every reader mask equal to its brief literal
     READ THROUGH THE RAW KEYS (letter = effect, number = dword) with its aura / SpellMod op; `_masks` composites and the
     raw-key helpers.
  4. Rank amounts the C++ reads (brief section 5), talent rank frames (attributes 464, SpellLevel 9 + 5 x row + rank).
  5. Script bindings / unbinds, proc rows (every S2 procs_on phase 2, the removed ones gone), links, custom attrs, SDV
     1335 / 1336 + the extended 1321-1323 (names <= 12 chars), consts, creature 300350.

Run: apps/dbc-tools/.venv/bin/python3 -m pytest apps/dbc-tools/lib/test_rogue_s2.py -q
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

S2_IDS = tuple(range(204130, 204174))                 # 44 new rows
S2_SPARE = tuple(range(204174, 204280))               # fix-pass spare + unassigned: nothing may be built here
(DS, SR, SV, LS, FIN, EXE, AE, MOMA_R) = ((204130, 204131, 204132), (204133, 204134, 204135), (204136, 204137),
                                          (204138, 204139), (204140, 204141), (204142, 204143), (204144, 204145),
                                          (204146, 204147))
MOS_R = (204149, 204150, 204151)
(DFA, HEM_R, PRE_R) = (204148, 204152, 204153)
(MOS_BUFF, RS_BUFF, LS_BUFF, FIN_EV, FIN_RUP, FIN_DT) = (204154, 204155, 204156, 204157, 204158, 204159)
(HEM_BLEED, HEM_TICK, ECHO, TINT, MOMA_BUFF, VOLLEY) = (204160, 204161, 204162, 204163, 204164, 204165)
(SV_MAIN, SV_OFF, DT_COPY, DFA_AREA, DFA_LAND, DFA_FLIGHT) = (204166, 204167, 204168, 204169, 204170, 204171)
(HAT_BUFF, ES_HELPER) = (204172, 204173)
SHADOW_DANCE, SHADOWSTEP, PREPARATION, CHEATING_DEATH, FOK, FOK_OH = 51713, 36554, 14185, 45182, 51723, 52874
EVISCERATE, RUPTURE, DEADLY_THROW, BACKSTAB, AMBUSH, GARROTE = 2098, 1943, 26679, 53, 8676, 703
HFB, WOUND = 51662, 13218
AKAARI_CLONE = 300350

HIDDEN_PASSIVE_ATTR = 464
D0_B9, D0_B11, D0_B17, D0_B20, D0_B22, D0_B25, D0_B26 = 0x200, 0x800, 0x20000, 0x100000, 0x400000, 0x2000000, 0x4000000
FORBIDDEN_S2_D0 = D0_B11 | D0_B22 | D0_B25 | D0_B26          # brief section 4: on no S2 row
COMBO_ATTRS = 0x100000 | 0x400000                              # AttributesEx: NeedsComboPoints()
EX1_STEALTH_OK = 0x20
EX1_IMMUNITY_PURGES = 0x8000                                  # SPELL_ATTR1_IMMUNITY_PURGES_EFFECT
EX3_SUPPRESS_CASTER, EX3_ALWAYS_HIT, EX3_IGNORE_CASTER_MODS, EX3_STACK_PER_CASTER = 0x10000, 0x40000, 0x20000000, 0x80
EX2_CANT_CRIT = 0x20000000

APPLY_AURA, TRIGGER_SPELL, ADD_COMBO, SCHOOL_DAMAGE, DUMMY_EFFECT, WEAPON_PCT = 6, 64, 80, 2, 3, 31
AURA_DUMMY, AURA_FLAT, AURA_PCT, AURA_PERIODIC_DUMMY = 4, 107, 108, 226
OP = {"DAMAGE": 0, "DURATION": 1, "EFFECT1": 3, "RANGE": 5, "CRIT": 7, "COOLDOWN": 11, "EFFECT2": 12, "COST": 14,
      "CRIT_DAMAGE": 15, "CHANCE": 18, "ACTIVATION": 19, "DOT": 22}
RANGE_SELF, RANGE_MELEE, RANGE_100, RANGE_15 = 1, 2, 6, 11

# ---- grid (S2a brief 10.1; tab 183) ------------------------------------------------------------------------------------

TAB = 183
COMBAT_TAB = 181
RETIRED_TAB = 60800
RETIRED = (241, 1700, 262, 246, 265, 2079)
GRID = {
    261: (0, 0, [14057, 14072]), 60425: (0, 1, list(DS)), 2244: (0, 2, [14179, 58422, 58423]),
    244: (1, 0, [13975, 14062, 14063]), 60426: (1, 1, list(SR)), 1711: (1, 3, [31211, 31212, 31213]),
    247: (2, 0, [13981, 14066]), 2081: (2, 1, [51713]), 1123: (2, 2, [14171, 14172, 14173]),
    2080: (2, 3, [51708, 51709, 51710]),
    263: (3, 0, [14079, 14080]), 245: (3, 1, [13976, 13979, 13980]), 60427: (3, 2, list(SV)), 60428: (3, 3, list(LS)),
    1701: (4, 0, [30894, 30895]), 284: (4, 1, [14185]), 60429: (4, 2, list(FIN)), 681: (4, 3, [HEM_R]),
    60430: (5, 1, list(EXE)), 2072: (5, 2, [5952, 51679]), 1702: (5, 3, [30902, 30903, 30904]),
    381: (6, 0, [PRE_R]), 1713: (6, 1, list(MOS_R)), 1722: (6, 3, [31228, 31229, 31230]),
    2077: (7, 1, [51692, 51696]), 1712: (7, 2, [31216, 31217, 31218]),
    60431: (8, 0, list(AE)), 1714: (8, 1, [36554]), 2078: (8, 2, [51698, 51700, 51701]),
    60432: (9, 1, list(MOMA_R)), 60433: (10, 1, [DFA]),
}
ROW_TOTALS = [8, 9, 9, 9, 6, 7, 7, 5, 6, 2, 1]
FLAGS = {681: 0, 381: 0, 284: 1, 1714: 1, 2081: 1, 60433: 1}
SLA_ROW = (30825, 39, DFA)                      # id, skill line, spell
COMBAT_TAB_TALENTS = 36                      # S3: the reworked Combat tab

# ---- family bits (brief section 4) ----------------------------------------------------------------------------------------

CARRIER_CLASS = {   # own SpellClassMask_1/_2/_3 of the new carrier rows, written out from the brief's table
    DFA: (0, 0, 0x40080), DFA_AREA: (0, 0, 0x40080), DFA_LAND: (0, 0, 0x40100),
    HEM_BLEED: (0, 0, 0x1000), HEM_TICK: (0, 0, 0x1000), VOLLEY: (0, 0, 0x20000),
    SV_MAIN: (0, 0x40000, 0), SV_OFF: (0, 0x40000, 0), DT_COPY: (0, 0x1, 0),
}
NEW_BIT_CARRIERS = {   # (dword index, bit value) -> exact carrier set across every built row
    (2, 0x80): {DFA, DFA_AREA}, (2, 0x100): {DFA_LAND}, (2, 0x1000): {HEM_BLEED, HEM_TICK}, (2, 0x20000): {VOLLEY},
}
S2_SHARED_BIT_CARRIERS = {   # existing bits: the S2 id range carries them on exactly these rows
    (2, 0x40000): {DFA, DFA_AREA, DFA_LAND}, (1, 0x40000): {SV_MAIN, SV_OFF}, (1, 0x1): {DT_COPY},
}

# reader literals from brief section 4 (+ harness addendum: MOMA_READ also holds Riposte d1 b8 = 0x100)
COMPOSITES = {
    "FROM_THE_SHADOWS_READ": (0x204, 0, 0x100000),
    "FROM_THE_SHADOWS_DOT_READ": (0x100, 0, 0),
    "SHADOWED_HIDDEN_READ": (0x700, 0, 0),
    "ELUSIVENESS_VANISH_READ": (0x800, 0, 0),
    "SLAUGHTER_READ": (0x4, 0, 0),
    "IMPROVED_AMBUSH_READ": (0x200, 0, 0),
    "WAYLAY_READ": (0x200, 0, 0),
    "INITIATIVE_PROC_READ": (0x700, 0, 0),
    "FINALITY_EVISCERATE_READ": (0x20000, 0, 0x100),
    "FINALITY_RUPTURE_READ": (0x100000, 0, 0),
    "FINALITY_DEADLY_THROW_READ": (0, 0x1, 0),
    "THROWING_SPEC_READ": (0, 0x40001, 0),
    "DEADLINESS_DOT_READ": (0x100100, 0, 0),
    "SERRATED_BLADES_DOT_READ": (0x100000, 0, 0),
    "MOMA_READ": (0x20000, 0x40109, 0x1A0580),
    "HUNGER_FOR_BLOOD_READ_S2": (0x110100, 0, 0x1A00),
    "WOUND_BLEED_READ_S2": (0x100100, 0, 0x1800),
    "FIND_WEAKNESS_READ_S2": (0x100, 0xC0100, 0x1E0780),
    "MOMA_READ_S3": (0x20000, 0x40109, 0x1A85A0),                       # S3 (U65): + Between the Eyes, Blade Rush
    "FIND_WEAKNESS_READ_S3": (0x100, 0xC0100, 0x1E87A0),
    "VANISH": 0x800,
    "DEATH_FROM_ABOVE": 0x80,
    "DFA_LANDING": 0x100,
    "HEMORRHAGE": 0x1000,
    "SINISTER_CALLING_VOLLEY": 0x20000,
    "DEATH_FROM_ABOVE_CLASS": (0, 0, 0x40080),
    "DFA_LANDING_CLASS": (0, 0, 0x40100),
    "HEMORRHAGE_CLASS": (0, 0, 0x1000),
    "SINISTER_CALLING_VOLLEY_CLASS": (0, 0, 0x20000),
    "SECOND_VOLLEY_CLASS": (0, 0x40000, 0),
    "DEADLY_THROW_COPY_CLASS": (0, 0x1, 0),
}
# (spell id, effect 1-based (= letter A/B/C), composite, aura, SpellMod op or None)
READERS = (
    [(i, 1, "FROM_THE_SHADOWS_READ", AURA_PCT, OP["DAMAGE"]) for i in (14057, 14072)]
    + [(i, 2, "FROM_THE_SHADOWS_DOT_READ", AURA_PCT, OP["DOT"]) for i in (14057, 14072)]
    + [(SHADOW_DANCE, 1, "SHADOWED_HIDDEN_READ", 275, None)]
    + [(i, 1, "ELUSIVENESS_VANISH_READ", AURA_FLAT, OP["COOLDOWN"]) for i in (13981, 14066)]
    + [(i, 1, "SLAUGHTER_READ", AURA_PCT, OP["DAMAGE"]) for i in (51708, 51709, 51710)]
    + [(i, 1, "IMPROVED_AMBUSH_READ", AURA_FLAT, OP["CRIT"]) for i in (14079, 14080)]
    + [(i, 1, "WAYLAY_READ", AURA_PCT, OP["DAMAGE"]) for i in (51692, 51696)]
    + [(FIN_EV, 1, "FINALITY_EVISCERATE_READ", AURA_PCT, OP["DAMAGE"]),
       (FIN_RUP, 1, "FINALITY_RUPTURE_READ", AURA_PCT, OP["DOT"]),
       (FIN_DT, 1, "FINALITY_DEADLY_THROW_READ", AURA_PCT, OP["DAMAGE"])]
    + [(i, 1, "THROWING_SPEC_READ", AURA_PCT, OP["DAMAGE"]) for i in (5952, 51679)]
    + [(i, 2, "DEADLINESS_DOT_READ", AURA_PCT, OP["DOT"]) for i in (30902, 30903, 30904)]
    + [(i, 1, "SERRATED_BLADES_DOT_READ", AURA_PCT, OP["DOT"]) for i in (14171, 14172, 14173)]
    + [(MOMA_BUFF, 1, "MOMA_READ_S3", AURA_FLAT, OP["CRIT"]),
       (HFB, 1, "HUNGER_FOR_BLOOD_READ_S2", AURA_PCT, OP["ACTIVATION"]),
       (WOUND, 1, "WOUND_BLEED_READ_S2", 271, None)]
    + [(i, 1, "FIND_WEAKNESS_READ_S3", AURA_FLAT, OP["CRIT"]) for i in (31234, 31235, 31236)]
)
# effects that must read NO mask at all (stale twins cleared): (spell id, effect 1-based)
EMPTY_MASKS = (
    [(SHADOW_DANCE, 2), (SHADOW_DANCE, 3)]
    + [(i, e) for i in (51708, 51709, 51710) for e in (2, 3)]
    + [(51692, 2), (51696, 2)]                                         # Waylay: eff1 emptied / 51693 proc effect
    + [(i, 2) for i in (5952, 51679)]
    + [(i, 1) for i in (14179, 58422, 58423)]                          # Relentless: the stock A mask cleared
    + [(i, 2) for i in (31216, 31217, 31218)]                          # Sinister Calling: stale B_1 0x2000004
    + [(CHEATING_DEATH, 1), (CHEATING_DEATH, 2)]                       # stale 0x400000
    + [(i, 2) for i in (51698, 51700, 51701)]                          # Honor Among Thieves: eff1's junk B_1
)
ELUSIVENESS_CLOAK_B = (0, 0x10000, 0)                                  # eff1 Cloak mask unchanged (brief section 4)

# ---- rank amounts the C++ reads (brief section 5, 10): (id, effect 1-based, aura or None, engine value) ----------------
AMOUNTS = (
    [(i, 1, AURA_DUMMY, v) for i, v in zip((14179, 58422, 58423), (10, 20, 30))]              # Relentless Strikes
    + [(i, 2, AURA_DUMMY, v) for i, v in zip((51708, 51709, 51710), (33, 66, 100))]           # Slaughter
    + [(i, 1, AURA_PCT, v) for i, v in zip((51708, 51709, 51710), (5, 10, 15))]
    + [(i, 1, AURA_DUMMY, v) for i, v in zip(SV, (20, 40))]                                   # Second Volley
    + [(i, 1, AURA_DUMMY, v) for i, v in zip(LS, (1, 2))]                                     # Lingering Shadow
    + [(i, 1, AURA_DUMMY, v) for i, v in zip(FIN, (20, 40))]                                  # Finality (M2a)
    + [(HEM_R, 1, AURA_DUMMY, 30)]                                                             # Hemorrhage
    + [(i, 1, AURA_DUMMY, v) for i, v in zip(EXE, (10, 20))]                                  # Executioner
    + [(PRE_R, 1, AURA_DUMMY, 2)]                                                              # Premeditation
    + [(i, 1, AURA_DUMMY, v) for i, v in zip(MOS_R, (4, 8, 12))]                              # Master of Subtlety
    + [(i, 1, AURA_DUMMY, v) for i, v in zip((31211, 31212, 31213), (2, 4, 6))]               # Enveloping Shadows
    + [(i, 1, AURA_DUMMY, v) for i, v in zip(AE, (25, 50))]                                   # Akaari's Echo (M2a)
    + [(i, 1, AURA_DUMMY, v) for i, v in zip(MOMA_R, (50, 100))]                              # Mark of the Master Assassin
    + [(i, 1, 306, v) for i, v in zip(DS, (1, 2, 3))] + [(i, 1, 306, v) for i, v in zip(SR, (1, 2, 3))]
    + [(i, 1, 69, v) for i, v in zip((31228, 31229, 31230), (33, 66, 100))]                   # Cheat Death (R22)
    + [(i, 1, 42, 0) for i in (13976, 13979, 13980)]                                          # Initiative (R1)
    + [(i, 1, 290, v) for i, v in zip((30894, 30895), (1, 2))] + [(30895, 2, 17, 6)]          # Heightened Senses (R10)
    + [(i, 1, 290, v) for i, v in zip((51698, 51700, 51701), (1, 2, 3))]                      # Honor Among Thieves (R10)
    + [(i, 1, AURA_PCT, v) for i, v in zip((14057, 14072), (10, 20))]                         # From the Shadows
    + [(i, 2, AURA_PCT, v) for i, v in zip((14057, 14072), (10, 20))]
    + [(i, 1, AURA_FLAT, v) for i, v in zip((14079, 14080), (15, 30))]                        # Improved Ambush
    + [(51692, 1, AURA_PCT, 20), (51696, 1, AURA_PCT, 40), (51696, 2, 42, 0)]                 # Waylay (M2a)
    + [(i, 1, AURA_PCT, v) for i, v in zip((5952, 51679), (30, 60))]                          # Throwing Spec (M2a)
    + [(i, 1, 166, v) for i, v in zip((30902, 30903, 30904), (2, 4, 6))]                      # Deadliness
    + [(i, 2, AURA_PCT, v) for i, v in zip((30902, 30903, 30904), (2, 4, 6))]
    + [(i, 1, 137, v) for i, v in zip((31216, 31217, 31218), (1, 2, 3))]                      # Sinister Calling
    + [(SHADOW_DANCE, 2, 110, 75), (SHADOW_DANCE, 3, 36, 0)]                                   # Shadowed
    + [(CHEATING_DEATH, 1, 87, -90), (HAT_BUFF, 1, 79, 3), (RS_BUFF, 1, 280, 10)]
)
# rank frames: id -> (tier row, rank); hidden passives, attributes 464 (brief section 10.15)
RANK_FRAMES = {}
for _row, _ids in ((0, DS), (1, SR), (3, SV), (3, LS), (4, FIN), (5, EXE), (8, AE), (9, MOMA_R), (6, MOS_R),
                   (4, (HEM_R,)), (6, (PRE_R,))):
    for _rank, _id in enumerate(_ids, 1):
        RANK_FRAMES[_id] = (_row, _rank)

# ---- scripts, procs, links, attrs, SDV, consts ------------------------------------------------------------------------------

SCRIPTS = {
    (DFA, "spell_rog_death_from_above"), (DFA_AREA, "spell_rog_death_from_above_area"),
    (DFA_LAND, "spell_rog_death_from_above_landing"), (EVISCERATE, "spell_rog_eviscerate_subtlety"),
    (RUPTURE, "spell_rog_rupture_finality"), (DEADLY_THROW, "spell_rog_deadly_throw_subtlety"),
    (BACKSTAB, "spell_rog_backstab_subtlety"), (AMBUSH, "spell_rog_ambush_subtlety"),
    (HEM_BLEED, "spell_rog_hemorrhage"), (VOLLEY, "spell_rog_sinister_calling_volley"),
    (MOS_BUFF, "spell_rog_master_of_subtlety_buff"), (ES_HELPER, "spell_rog_enveloping_shadows"),
    (-31228, "spell_rog_cheat_death_rework"), (SV_MAIN, "spell_rog_fan_of_knives"),
}
NEW_ID_SCRIPTED = {DFA, DFA_AREA, DFA_LAND, HEM_BLEED, VOLLEY, MOS_BUFF, ES_HELPER, SV_MAIN}   # S2 ids with a script
UNBOUND = {
    (51698, "spell_rog_honor_among_thieves"), (51700, "spell_rog_honor_among_thieves"),
    (51701, "spell_rog_honor_among_thieves"), (52916, "spell_rog_honor_among_thieves_proc"),
    (-13983, "spell_rog_setup"), (-31228, "spell_rog_cheat_death"),
}
KEPT_BINDINGS = {(31666, "spell_rog_master_of_subtlety"), (14185, "spell_rog_preparation")}   # stay bound (brief 8)
PROC_REMOVED = (-13983, -51692, -5952, 32748, 51698, 51700, 51701)
PROC_ROWS = {   # spell id -> (family mask, ProcFlags, Chance); family name 8, SpellPhaseMask 2 (HIT)
    -13976: ((0x700, 0, 0), 0x10, 0.0),
    51696: ((0x200, 0, 0), 0x10, 100.0),
}
LINKS = {(SV_MAIN, SV_OFF, 0), (203723, ES_HELPER, 2)}
CUSTOM_ATTRS = {HEM_TICK: 0x8000, ECHO: 0x8000}
SDV_NEW = {1335: (BACKSTAB,), 1336: (AMBUSH,)}
SDV_ATTACH = {**SDV_NEW, 1321: (FOK,), 1322: (GARROTE, RUPTURE), 1323: (EVISCERATE, DEADLY_THROW)}
SDV_VARS = {   # variable names that must be defined by the entry (brief section 8)
    1335: {"fts", "slaughter", "bsmult"}, 1336: {"fts", "waylay", "ammult"},
    1321: {"fan", "throwspec", "fanmult"}, 1322: {"blood", "seal", "mult", "ftsdot", "deadly", "serrated", "garmult", "rupmult"},
    1323: {"seal", "throwspec", "dtmult"},
}
TOOLTIP_TOKENS = {BACKSTAB: "bsall", AMBUSH: "amall", GARROTE: "garmult", RUPTURE: "rupmult", DEADLY_THROW: "dtmult",
                  FOK: "fanmult"}
CONSTS = {   # name -> (value, cpp type), brief section 6
    "SHADOW_DANCE_CDR_PER_CP_MS": (1000, "int32"), "EXECUTIONER_CDR_PER_CP_MS": (500, "int32"),
    "SLAUGHTER_CDR_MS": (500, "int32"), "EXECUTIONER_HEALTH_PCT": (35, "int32"),
    "SINISTER_CALLING_PCT_PER_CP": (4, "int32"), "SINISTER_CALLING_MAX_TARGETS": (3, "int32"),
    "SECOND_VOLLEY_DELAY_MS": (300, "int32"), "THROWING_SPEC_EXTRA_TARGETS": (2, "int32"),
    "THROWING_SPEC_RADIUS_YD": (8.0, "float"), "AKAARI_ECHO_DELAY_MS": (2000, "int32"),
    "AKAARI_ECHO_SHARE_PCT": (50, "int32"), "AKAARI_CLONE_DESPAWN_MS": (1500, "int32"),
    "AKAARI_CLONE_BEHIND_YD": (1.5, "float"), "AKAARI_CLONE_SWING_DELAY_MS": (200, "int32"),
    "MASTER_OF_SUBTLETY_TAIL_MS": (8000, "int32"), "MOMA_TAIL_MS": (3000, "int32"),
    "HONOR_AMONG_THIEVES_ALLY_RANGE_YD": (40.0, "float"), "CHEAT_DEATH_CAP_MAX_HEALTH_PCT": (15, "int32"),
    "DFA_LANDING_RANGE_YD": (8.0, "float"), "DFA_LANDING_PAST_YD": (1.5, "float"), "DFA_MIN_JUMP_YD": (1.5, "float"),
    "DFA_APEX_HEIGHT_YD": (8.0, "float"), "DFA_RISE_FRACTION": (0.5, "float"), "DFA_RISE_MS": (500, "int32"),
    "DFA_DIVE_MS": (400, "int32"), "DFA_UNREACHABLE_Z_YD": (5.0, "float"),
    "DFA_DRIFT_MS": (400, "int32"), "DFA_DRIFT_DROP_YD": (2.0, "float"), "DFA_DRIFT_FORWARD_YD": (1.0, "float"),
}

VISIBLE = (MOS_BUFF, RS_BUFF, LS_BUFF, FIN_EV, FIN_RUP, FIN_DT, HEM_BLEED, MOMA_BUFF, DFA_FLIGHT, HAT_BUFF,
           CHEATING_DEATH, SHADOW_DANCE)
HIDDEN = (HEM_TICK, ECHO, VOLLEY, SV_MAIN, SV_OFF, DT_COPY, DFA_AREA, DFA_LAND, ES_HELPER)
EX1_SELF_BUFFS = (MOS_BUFF, RS_BUFF, LS_BUFF, FIN_EV, FIN_RUP, FIN_DT, MOMA_BUFF, DFA_FLIGHT, HAT_BUFF, ES_HELPER)
WEAPON_ROWS = (SV_MAIN, SV_OFF, DT_COPY)            # weapon attacks keep their source's weapon requirement
NO_COMBO_ATTRS = (DT_COPY, DFA_AREA, DFA_LAND, SV_MAIN, SV_OFF, VOLLEY, HEM_TICK, ECHO)
TEXTS = {   # verbatim (brief section 10, doc section 5)
    MOS_BUFF: "Your physical attacks deal more damage.",
    RS_BUFF: "Your attacks ignore some of your target's armor.",
    LS_BUFF: "Your next Backstab awards an additional combo point.",
    FIN_EV: "Your next Eviscerate deals more damage.",
    FIN_RUP: "Your next Rupture deals more damage.",
    FIN_DT: "Your next Deadly Throw deals more damage.",
    HEM_BLEED: "Bleeding.",
    MOMA_BUFF: "Critical strike chance increased.",
    DFA_FLIGHT: "Leaping.",
    HAT_BUFF: "Damage increased.",
    CHEATING_DEATH: "Damage taken reduced.",
    SHADOW_DANCE: "Shadowed. You are Hidden and regenerate energy faster.",
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
        # ---- Death from Above castable (R15): Eviscerate's frame, DefenseType 0
        DFA: {"Attributes": 327696, "AttributesEx": 1049088, "EquippedItemClass": 2, "EquippedItemSubclass": 173555,
              "PreventionType": 2, "FacingCasterFlags": 1, "DefenseType": 0, "ManaCost": 25, "RangeIndex": RANGE_15,
              "RecoveryTime": 20000, "StartRecoveryCategory": 133, "StartRecoveryTime": 1000, "BaseLevel": 60,
              "SpellLevel": 60, "Effect_1": DUMMY_EFFECT, "ImplicitTargetA_1": 6,
              "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0x40080},
        DFA_AREA: {"Effect_1": SCHOOL_DAMAGE, "ImplicitTargetA_1": 53, "ImplicitTargetB_1": 16, "DefenseType": 2,
                   "PreventionType": 0, "EquippedItemClass": -1, "SpellLevel": 60, "SchoolMask": 1,
                   "RangeIndex": RANGE_100, "FacingCasterFlags": 0,
                   "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0x40080},
        DFA_LAND: {"Effect_1": SCHOOL_DAMAGE, "ImplicitTargetA_1": 6, "DefenseType": 2, "PreventionType": 0,
                   "EquippedItemClass": -1, "SpellLevel": 60, "RangeIndex": RANGE_100, "FacingCasterFlags": 0,
                   "SpellVisualID_1": 671, "SchoolMask": 1,
                   "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0x40100},
        DFA_FLIGHT: {"Effect_1": APPLY_AURA, "EffectAura_1": 77, "EffectMiscValue_1": 7, "Effect_2": APPLY_AURA,
                     "EffectAura_2": 144, "Effect_3": APPLY_AURA, "EffectAura_3": 25, "DurationIndex": idx["d2500"],
                     "EquippedItemClass": -1, "SpellIconID": 3139},
        # ---- Hemorrhage
        HEM_BLEED: {"Effect_1": APPLY_AURA, "EffectAura_1": AURA_PERIODIC_DUMMY, "EffectAuraPeriod_1": 2000,
                    "DurationIndex": idx["d8000"], "Mechanic": 15, "EquippedItemClass": -1, "SpellIconID": 153,
                    "RangeIndex": RANGE_100, "FacingCasterFlags": 0, "ImplicitTargetA_1": 6,
                    "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0x1000},
        HEM_TICK: {"Effect_1": SCHOOL_DAMAGE, "Mechanic": 15, "DefenseType": 0, "EquippedItemClass": -1,
                   "RangeIndex": RANGE_100, "FacingCasterFlags": 0,
                   "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0x1000},
        # ---- Akaari's Echo (R11: keeps melee range, no facing; no family bit at all)
        ECHO: {"Effect_1": SCHOOL_DAMAGE, "DefenseType": 0, "EquippedItemClass": -1, "RangeIndex": RANGE_MELEE,
               "FacingCasterFlags": 0, "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0},
        TINT: {"Effect_1": APPLY_AURA, "SpellVisualID_1": 3619, "DurationIndex": idx["d2000"]},
        # ---- buffs
        MOS_BUFF: {"Effect_1": APPLY_AURA, "EffectAura_1": 79, "EffectMiscValue_1": 1, "EffectBasePoints_1": 0,
                   "Effect_2": APPLY_AURA, "EffectAura_2": AURA_PERIODIC_DUMMY, "EffectAuraPeriod_2": 1000,
                   "DurationIndex": inf, "EquippedItemClass": -1, "SpellIconID": 2114},
        RS_BUFF: {"Effect_1": APPLY_AURA, "EffectAura_1": 280, "EffectMiscValue_1": 1, "DurationIndex": idx["d5000"],
                  "EquippedItemClass": -1, "SpellIconID": 559},
        LS_BUFF: {"Effect_1": APPLY_AURA, "EffectAura_1": AURA_DUMMY, "CumulativeAura": 2,
                  "DurationIndex": idx["d15000"], "EquippedItemClass": -1, "SpellIconID": 2206},
        FIN_EV: {"Effect_1": APPLY_AURA, "EffectAura_1": AURA_PCT, "EffectMiscValue_1": OP["DAMAGE"],
                 "DurationIndex": idx["d30000"], "EquippedItemClass": -1, "SpellIconID": 169, "ProcCharges": 0,
                 "EffectBasePoints_1": 0},
        FIN_RUP: {"Effect_1": APPLY_AURA, "EffectAura_1": AURA_PCT, "EffectMiscValue_1": OP["DOT"],
                  "DurationIndex": idx["d30000"], "EquippedItemClass": -1, "SpellIconID": 169, "ProcCharges": 0,
                  "EffectBasePoints_1": 0},
        FIN_DT: {"Effect_1": APPLY_AURA, "EffectAura_1": AURA_PCT, "EffectMiscValue_1": OP["DAMAGE"],
                 "DurationIndex": idx["d30000"], "EquippedItemClass": -1, "SpellIconID": 169, "ProcCharges": 0,
                 "EffectBasePoints_1": 0},
        MOMA_BUFF: {"Effect_1": APPLY_AURA, "EffectAura_1": AURA_FLAT, "EffectMiscValue_1": OP["CRIT"],
                    "EffectBasePoints_1": 0, "DurationIndex": inf, "EquippedItemClass": -1, "SpellIconID": 2984},
        HAT_BUFF: {"Effect_1": APPLY_AURA, "EffectAura_1": 79, "EffectMiscValue_1": 127, "ImplicitTargetA_1": 21,
                   "RangeIndex": RANGE_100, "DurationIndex": idx["d10000"], "EquippedItemClass": -1,
                   "SpellIconID": 2903},
        ES_HELPER: {"Effect_1": APPLY_AURA, "EffectAura_1": 87, "EffectMiscValue_1": 1, "EffectBasePoints_1": 0,
                    "DurationIndex": inf, "EquippedItemClass": -1},
        # ---- Sinister Calling volley (R11, R12)
        VOLLEY: {"SchoolMask": 0x21, "ImplicitTargetA_1": 53, "ImplicitTargetB_1": 16, "SpellLevel": 47,
                 "RangeIndex": RANGE_100, "FacingCasterFlags": 0, "EquippedItemClass": -1,
                 "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0x20000},
        # ---- Second Volley copies, Throwing Specialization copy
        SV_MAIN: {"SpellLevel": 24, "Effect_2": ADD_COMBO, "RangeIndex": RANGE_SELF,    # self-cast: caster-centred (R11)
                  "SpellClassMask_1": 0, "SpellClassMask_2": 0x40000, "SpellClassMask_3": 0},
        SV_OFF: {"SpellClassMask_1": 0, "SpellClassMask_2": 0x40000, "SpellClassMask_3": 0},
        DT_COPY: {"SpellLevel": 36, "Speed": 50, "RangeIndex": RANGE_100, "FacingCasterFlags": 0, "Effect_1": SCHOOL_DAMAGE,
                  "Effect_2": APPLY_AURA, "EffectAura_2": 33, "Effect_3": 0,
                  "SpellClassMask_1": 0, "SpellClassMask_2": 0x1, "SpellClassMask_3": 0},
        # ---- stock rows edited
        SHADOW_DANCE: {"DurationIndex": idx["d8000"], "RecoveryTime": 30000, "StartRecoveryCategory": 0, "ManaCost": 0,
                       "BaseLevel": 20, "SpellLevel": 20, "AttributesEx": 0x20400, "StanceBarOrder": 1,
                       "Effect_1": APPLY_AURA, "EffectAura_1": 275, "Effect_2": APPLY_AURA, "EffectAura_2": 110,
                       "EffectMiscValue_2": 3, "Effect_3": APPLY_AURA, "EffectAura_3": 36, "EffectMiscValue_3": 30},
        SHADOWSTEP: {"Effect_1": TRIGGER_SPELL, "EffectTriggerSpell_1": 203726, "Effect_2": 0, "RecoveryTime": 30000,
                     "ManaCost": 10, "StartRecoveryCategory": 0, "RangeIndex": idx["r25"]},
        CHEATING_DEATH: {"Effect_1": APPLY_AURA, "EffectAura_1": 87, "EffectMiscValue_1": 127, "EffectBasePoints_1": -91,
                         "DurationIndex": idx["d3000"]},
        51692: {"ProcTypeMask": 0, "ProcChance": 101},
        51696: {"ProcTypeMask": 16, "ProcChance": 100, "Effect_2": APPLY_AURA, "EffectTriggerSpell_2": 51693},
        13976: {"ProcChance": 33, "ProcTypeMask": 0, "EffectTriggerSpell_1": 13977},
        13979: {"ProcChance": 66, "ProcTypeMask": 0, "EffectTriggerSpell_1": 13977},
        13980: {"ProcChance": 100, "ProcTypeMask": 0, "EffectTriggerSpell_1": 13977},
        30894: {"Effect_2": 0, "Effect_3": 0}, 30895: {"Effect_2": APPLY_AURA, "Effect_3": 0},
        51698: {"Effect_1": APPLY_AURA, "EffectBasePoints_2": 0, "EffectDieSides_2": 0, "ProcTypeMask": 0,
                "ProcChance": 101},
        51700: {"Effect_1": APPLY_AURA, "EffectBasePoints_2": 0, "EffectDieSides_2": 0, "ProcTypeMask": 0,
                "ProcChance": 101},
        51701: {"Effect_1": APPLY_AURA, "EffectBasePoints_2": 0, "EffectDieSides_2": 0, "ProcTypeMask": 0,
                "ProcChance": 101},
        5952: {"Effect_2": 0, "ProcTypeMask": 0, "ProcChance": 101},
        51679: {"Effect_2": 0, "ProcTypeMask": 0, "ProcChance": 101},
        14179: {"ProcTypeMask": 0}, 58422: {"ProcTypeMask": 0}, 58423: {"ProcTypeMask": 0},
        31216: {"Effect_2": 0}, 31217: {"Effect_2": 0}, 31218: {"Effect_2": 0},
    }
    for sid, (tier, rank) in RANK_FRAMES.items():          # hidden passive frames (brief 10.15)
        exact.setdefault(sid, {}).update({"Attributes": HIDDEN_PASSIVE_ATTR, "EquippedItemClass": -1,
                                          "SpellLevel": _lvl(tier, rank), "ProcTypeMask": 0,
                                          "SpellClassMask_1": 0, "SpellClassMask_2": 0, "SpellClassMask_3": 0})
    must_set = {
        DFA_AREA: {"Attributes": ATTR0_HIDDEN}, DFA_LAND: {"Attributes": ATTR0_HIDDEN},
        HEM_BLEED: {"AttributesEx3": EX3_STACK_PER_CASTER},
        HEM_TICK: {"AttributesEx3": EX3_IGNORE_CASTER_MODS | EX3_ALWAYS_HIT | EX3_SUPPRESS_CASTER,
                   "AttributesEx2": EX2_CANT_CRIT, "Attributes": ATTR0_HIDDEN},
        ECHO: {"AttributesEx3": EX3_IGNORE_CASTER_MODS | EX3_ALWAYS_HIT | EX3_SUPPRESS_CASTER,
               "AttributesEx2": EX2_CANT_CRIT, "Attributes": ATTR0_HIDDEN},
        VOLLEY: {"AttributesEx3": EX3_SUPPRESS_CASTER, "Attributes": ATTR0_HIDDEN},
        SV_MAIN: {"AttributesEx3": EX3_SUPPRESS_CASTER, "Attributes": ATTR0_HIDDEN},
        SV_OFF: {"AttributesEx3": EX3_SUPPRESS_CASTER, "Attributes": ATTR0_HIDDEN},
        DT_COPY: {"AttributesEx3": EX3_SUPPRESS_CASTER, "Attributes": ATTR0_HIDDEN},
        DFA: {"AttributesEx3": 0x400},
        ES_HELPER: {"Attributes": ATTR0_HIDDEN},
        SHADOW_DANCE: {"SpellClassMask_2": 0x2000000},     # keeps its own d1 b25
    }
    for sid in EX1_SELF_BUFFS:                              # R19
        must_set.setdefault(sid, {})["AttributesEx"] = EX1_STEALTH_OK
    must_set[DFA_FLIGHT]["AttributesEx"] |= EX1_IMMUNITY_PURGES     # S2-CODE-REVIEW L2: purges an existing root
    must_clear = {
        ES_HELPER: {"Attributes": ATTR0_PASSIVE},           # an aura link needs a real aura, not PASSIVE
        SHADOW_DANCE: {"SpellClassMask_1": D0_B11 | D0_B22},
    }
    for sid in VISIBLE:
        must_clear[sid] = {"Attributes": must_clear.get(sid, {}).get("Attributes", 0) | ATTR0_PASSIVE | ATTR0_HIDDEN}
    for sid in NO_COMBO_ATTRS:
        must_clear.setdefault(sid, {})["AttributesEx"] = COMBO_ATTRS
    for sid in (DFA_AREA, DFA_LAND):                         # R12 also for the DFA hits (in NO_COMBO_ATTRS)
        must_clear[sid]["AttributesEx"] = COMBO_ATTRS
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


def check_s2_id_set(rows: dict) -> list[str]:
    bad = [f"{sid}: S2 row not built" for sid in S2_IDS if sid not in rows]
    bad += [f"{sid}: unexpected row (204174-204279 are spare / unassigned)" for sid in S2_SPARE if sid in rows]
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
    for sid in S2_IDS:
        r = rows.get(sid)
        if r is None:
            continue
        if sid in HIDDEN + VISIBLE and sid not in WEAPON_ROWS and _u32(r.get("EquippedItemClass")) != 0xFFFFFFFF:
            bad.append(f"{sid}: EquippedItemClass {r.get('EquippedItemClass')!r}, expected -1 on a non-weapon row")
    return bad


def check_effect_absence(rows: dict) -> list[str]:
    """Relentless ranks keep no aura 109 (C5); Shadow Dance has no MOD_STEALTH (16); Slaughter has no COST / aura 79."""
    bad = []
    for sid in (14179, 58422, 58423):
        for e in (1, 2, 3):
            if _i(rows.get(sid, {}), f"EffectAura_{e}") == 109:
                bad.append(f"{sid}: effect {e} still aura 109 (ADD_CALLER_TARGET_PCT energize; C5)")
    for e in (1, 2, 3):
        if _i(rows.get(SHADOW_DANCE, {}), f"EffectAura_{e}") == 16:
            bad.append(f"{SHADOW_DANCE}: effect {e} is MOD_STEALTH (aura 16): Shadowed is a form, not Stealth")
    for sid in (51708, 51709, 51710):
        for e in (1, 2, 3):
            r = rows.get(sid, {})
            if _i(r, f"EffectAura_{e}") == 79 or (_i(r, f"EffectAura_{e}") in (107, 108)
                                                  and _i(r, f"EffectMiscValue_{e}") == OP["COST"]):
                bad.append(f"{sid}: effect {e} keeps a COST / aura 79 effect (dropped in S2)")
    for e in (1, 2, 3):
        if _i(rows.get(DFA_FLIGHT, {}), f"Effect_{e}") != APPLY_AURA:
            bad.append(f"{DFA_FLIGHT}: effect {e} is not APPLY_AURA (root immunity / safe fall / pacify)")
    return bad


def check_copy_frames(rows: dict) -> list[str]:
    """Copies take their source's frame (brief 10.7 / 10.8): Deadly Throw copy vs 26679, Second Volley vs 51723 / 52874."""
    bad = []
    pairs = ((DT_COPY, DEADLY_THROW, ("EquippedItemClass", "EquippedItemSubclass", "DefenseType", "SpellVisualID_1",
                                       "EffectAura_2", "SchoolMask")),
             (SV_MAIN, FOK, ("SpellVisualID_1", "ImplicitTargetA_1", "ImplicitTargetB_1", "EffectRadiusIndex_1",
                             "ImplicitTargetA_2", "ImplicitTargetB_2", "EffectRadiusIndex_2", "DefenseType")),
             )   # 52874 (stock, not in the DSL package) is not compared
    for copy, src, cols in pairs:
        rc, rs = rows.get(copy), rows.get(src)
        if rc is None or rs is None:
            bad.append(f"{copy} / {src}: not built")
            continue
        for col in cols:
            if _u32(rc.get(col)) != _u32(rs.get(col)):
                bad.append(f"{copy}: {col} {rc.get(col)!r} differs from {src}'s {rs.get(col)!r}")
    return bad


def check_tooltips(rows: dict) -> list[str]:
    bad = []
    for sid, token in TOOLTIP_TOKENS.items():
        text = str(rows.get(sid, {}).get("Description_Lang_enUS") or "")
        if token not in text:
            bad.append(f"{sid}: tooltip lacks the talent factor `{token}`")
    return bad


# ---- carriers, masks, readers --------------------------------------------------------------------------------------------

def check_carriers(rows: dict) -> list[str]:
    bad = []
    for (dword, bit), want in NEW_BIT_CARRIERS.items():
        have = {sid for sid, r in rows.items() if spell_mask(r)[dword] & bit}
        if have != want:
            bad.append(f"d{dword} {bit:#x}: carriers {sorted(have)}, expected exactly {sorted(want)}")
    s2 = set(S2_IDS)
    for (dword, bit), want in S2_SHARED_BIT_CARRIERS.items():
        have = {sid for sid, r in rows.items() if sid in s2 and spell_mask(r)[dword] & bit}
        if have != want:
            bad.append(f"d{dword} {bit:#x} on the S2 rows: {sorted(have)}, expected exactly {sorted(want)}")
    return bad


def check_new_masks(rows: dict) -> list[str]:
    """Every new row: SpellClassSet 8; own mask exactly the carrier mask or zero; never-bits; the echo carries nothing."""
    bad = []
    for sid in S2_IDS:
        r = rows.get(sid)
        if r is None:
            continue
        if sid not in RANK_FRAMES and _i(r, "SpellClassSet") != 8:
            bad.append(f"{sid}: SpellClassSet {r.get('SpellClassSet')!r}, expected 8")
        mask = spell_mask(r)
        want = CARRIER_CLASS.get(sid, (0, 0, 0))
        if mask != want:
            bad.append(f"{sid}: spell mask ({', '.join(hex(w) for w in mask)}), expected "
                       f"({', '.join(hex(w) for w in want)})")
        if mask[0] & FORBIDDEN_S2_D0:
            bad.append(f"{sid}: d0 holds a never-bit ({mask[0] & FORBIDDEN_S2_D0:#x}: b11 / b22 / b25 / b26)")
    if _u32(rows.get(DFA_LAND, {}).get("SpellClassMask_1")) & D0_B17:
        bad.append(f"{DFA_LAND}: landing carries d0 b17 (Eviscerate's AP hardcode / Opportunity)")
    for sid in (HEM_BLEED, HEM_TICK):
        if _u32(rows.get(sid, {}).get("SpellClassMask_1")) & D0_B20:
            bad.append(f"{sid}: Hemorrhage carries d0 b20 (Rupture's bit: Glyph of Backstab)")
    if any(spell_mask(rows.get(ECHO, {}))):
        bad.append(f"{ECHO}: the echo carries a family bit (it must carry none, not even d0 b9)")
    sd = _u32(rows.get(SHADOW_DANCE, {}).get("SpellClassMask_1"))
    if sd & (D0_B11 | D0_B22):
        bad.append(f"{SHADOW_DANCE}: own mask d0 {sd:#x} holds b11 / b22")
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
    for sid in (13981, 14066):
        r = rows.get(sid)
        if r is not None and effect_mask(r, 2) != ELUSIVENESS_CLOAK_B:
            bad.append(f"{sid}: effect 2 (Cloak) mask {tuple(hex(w) for w in effect_mask(r, 2))}, expected unchanged "
                       f"{tuple(hex(w) for w in ELUSIVENESS_CLOAK_B)}")
    return bad


def check_composites(module) -> list[str]:
    bad = []
    for name, want in COMPOSITES.items():
        got = getattr(module, name, None)
        got = tuple(got) if isinstance(want, tuple) and got is not None else got
        if got != want:
            show = lambda v: tuple(hex(w) for w in v) if isinstance(v, tuple) else v  # noqa: E731
            bad.append(f"_masks.{name} = {show(got)}, expected {show(want)}")
    return bad


def check_mask_helpers(module) -> list[str]:
    """read_mask_keys picks the LETTER from the effect and the NUMBER from the dword; zeros included; bad index raises."""
    bad = []
    keys = module.read_mask_keys(1, (1, 2, 3))
    if keys != {"EffectSpellClassMaskB_1": 1, "EffectSpellClassMaskB_2": 2, "EffectSpellClassMaskB_3": 3}:
        bad.append(f"read_mask_keys(1, (1, 2, 3)) = {keys}")
    keys = module.read_mask_keys(0, (0x700, 0, 0))
    if keys != {"EffectSpellClassMaskA_1": 0x700, "EffectSpellClassMaskA_2": 0, "EffectSpellClassMaskA_3": 0}:
        bad.append(f"read_mask_keys(0, (0x700, 0, 0)) = {keys} (zeros must be emitted)")
    keys = module.read_mask_keys(2, (7, 8, 9))
    if keys != {"EffectSpellClassMaskC_1": 7, "EffectSpellClassMaskC_2": 8, "EffectSpellClassMaskC_3": 9}:
        bad.append(f"read_mask_keys(2, (7, 8, 9)) = {keys}")
    want_clear = {f"EffectSpellClassMask{l}_{n}": 0 for l in "AC" for n in (1, 2, 3)}
    if module.clear_mask_keys(0, 2) != want_clear:
        bad.append(f"clear_mask_keys(0, 2) = {module.clear_mask_keys(0, 2)}")
    if module.class_mask_keys((1, 2, 3)) != {"SpellClassMask_1": 1, "SpellClassMask_2": 2, "SpellClassMask_3": 3}:
        bad.append(f"class_mask_keys((1, 2, 3)) = {module.class_mask_keys((1, 2, 3))}")
    for bad_index in (3, -1):
        try:
            module.read_mask_keys(bad_index, (0, 0, 0))
        except ValueError:
            continue
        bad.append(f"read_mask_keys({bad_index}, ...) did not raise")
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
    if len(seen) != 31 or sum(row_points) != 69:
        bad.append(f"{len(seen)} talents / {sum(row_points)} points, expected 31 / 69")
    if row_points != ROW_TOTALS:
        bad.append(f"row point totals {row_points}, expected {ROW_TOTALS}")
    combat = [t for t in talents if int(t["tab_id"]) == COMBAT_TAB]
    if len(combat) != COMBAT_TAB_TALENTS:
        bad.append(f"tab {COMBAT_TAB}: {len(combat)} talents, expected {COMBAT_TAB_TALENTS}")
    if any(int(t["id"]) == 2072 for t in combat):
        bad.append("talent 2072 (Throwing Specialization) still on the Combat tab")
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
    if not re.search(r"subtlety_183_tab\s*=\s*tab\((?:[^()]|\([^()]*\))*?skill_line\s*=\s*39\b", tab_text, re.S):
        bad.append("tab 183 does not declare skill_line=39")
    return bad


def check_slas(slas: list[dict]) -> list[str]:
    sid, line, spell = SLA_ROW
    by_id = {int(s["id"]): s for s in slas if 30825 <= int(s["id"]) <= 30834}
    bad = []
    if sorted(by_id) != [sid]:
        bad.append(f"SkillLineAbility ids in 30825-30834: {sorted(by_id)}, expected {[sid]}")
    s = by_id.get(sid)
    if s is not None:
        got = (int(s["skill_line"]), int(s["spell_id"]), int(s.get("class_mask") or 0), int(s.get("acquire_method") or 0))
        if got != (line, spell, 8, 0):
            bad.append(f"SLA {sid}: {got}, expected {(line, spell, 8, 0)}")
    return bad


def check_scripts(names: list[dict], removals: list[dict]) -> list[str]:
    bound = {(int(n["spell_id"]), n["ScriptName"]) for n in names}
    unbound = {(int(n["spell_id"]), n["ScriptName"]) for n in removals}
    bad = [f"script {n} not bound to {s}" for s, n in sorted(SCRIPTS - bound)]
    bad += [f"script {n} not unbound from {s}" for s, n in sorted(UNBOUND - unbound)]
    for pair in sorted(bound & unbound):
        bad.append(f"{pair}: both bound and unbound")
    for pair in sorted(KEPT_BINDINGS & unbound):
        bad.append(f"{pair}: unbound, but the brief keeps it")
    extra = {s for s, _n in bound if 204130 <= s <= 204279} - NEW_ID_SCRIPTED
    for s in sorted(extra):
        bad.append(f"{s}: bound to a script (only {sorted(NEW_ID_SCRIPTED)} take one)")
    return bad


def check_procs(procs: list[dict], removals: list[dict]) -> list[str]:
    bad = []
    gone = {int(r["SpellId"]) for r in removals}
    for sid in PROC_REMOVED:
        if sid not in gone:
            bad.append(f"spell_proc {sid}: removal not declared")
    for sid, (mask, flags, chance) in PROC_ROWS.items():
        rows = [p for p in procs if int(p["SpellId"]) == sid]
        if len(rows) != 1:
            bad.append(f"{sid}: {len(rows)} spell_proc rows, expected 1")
            continue
        p = rows[0]
        got = (int(p.get("SpellFamilyMask0") or 0), int(p.get("SpellFamilyMask1") or 0), int(p.get("SpellFamilyMask2") or 0))
        if got != mask:
            bad.append(f"{sid}: family mask {tuple(hex(w) for w in got)}, expected {tuple(hex(w) for w in mask)}")
        want = {"SpellFamilyName": 8, "SpellPhaseMask": 2, "HitMask": 0, "ProcFlags": flags}
        for k, v in want.items():
            if int(p.get(k) or 0) != v:
                bad.append(f"{sid}: {k} = {p.get(k)!r}, expected {v}")
        if float(p.get("Chance") or 0) != chance:
            bad.append(f"{sid}: Chance = {p.get('Chance')!r}, expected {chance}")
    for p in procs:                                   # every S2 procs_on is phase HIT
        sid = int(p["SpellId"])
        if (204130 <= sid <= 204279 or sid in PROC_ROWS) and int(p.get("SpellPhaseMask") or 0) != 2:
            bad.append(f"{sid}: procs_on SpellPhaseMask {p.get('SpellPhaseMask')!r}, expected 2 (HIT)")
    return bad


def check_links_attrs(links: list[dict], attrs: list[dict]) -> list[str]:
    bad = []
    got = {(int(x["spell_trigger"]), int(x["spell_effect"]), int(x["type"])) for x in links
           if int(x["spell_trigger"]) in (SV_MAIN, 203723) and int(x["spell_effect"]) in (SV_OFF, ES_HELPER)}
    if got != LINKS:
        bad.append(f"S2 linked spells {sorted(got)}, expected {sorted(LINKS)}")
    a = {int(x["spell_id"]): int(x["attributes"]) for x in attrs}
    for sid, want in CUSTOM_ATTRS.items():
        if a.get(sid) != want:
            bad.append(f"{sid}: custom attr {a.get(sid)!r}, expected {want:#x} (stored share of post-armor damage)")
    for sid in (DFA, DFA_AREA, DFA_LAND, HEM_BLEED):
        if a.get(sid):
            bad.append(f"{sid}: unexpected custom attr {a[sid]:#x}")
    return bad


def check_sdv(entries: list[dict], rows: dict) -> list[str]:
    bad = []
    by_id = {int(e["id"]): e for e in entries if 1320 <= int(e["id"]) <= 1349}
    for sdv in SDV_ATTACH:
        if sdv not in by_id:
            bad.append(f"SDV {sdv}: not declared")
    for sdv in sorted(set(by_id) - {1320, 1321, 1322, 1323, 1335, 1336}):
        bad.append(f"SDV {sdv}: unexpected (1337-1349 spare)")
    for sdv, e in by_id.items():
        names = DEFINED_NAME.findall(str(e.get("Variables") or ""))
        for name in names:
            if len(name) > MAX_NAME_LENGTH:
                bad.append(f"SDV {sdv}: variable name {name!r} is {len(name)} chars (max {MAX_NAME_LENGTH})")
        if sdv in SDV_VARS:
            for name in sorted(SDV_VARS[sdv] - set(names)):
                bad.append(f"SDV {sdv}: variable {name!r} not defined")
    for sdv, spells in SDV_ATTACH.items():
        for sid in spells:
            if _i(rows.get(sid, {}), "SpellDescriptionVariableID") != sdv:
                bad.append(f"{sid}: SpellDescriptionVariableID {rows.get(sid, {}).get('SpellDescriptionVariableID')!r}, "
                           f"expected {sdv}")
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


def check_creature(creatures: list[dict], models: list[dict]) -> list[str]:
    bad = []
    mine = [c for c in creatures if int(c["entry"]) == AKAARI_CLONE]
    if len(mine) != 1:
        bad.append(f"creature {AKAARI_CLONE}: {len(mine)} templates, expected 1")
    elif mine[0].get("name") != "Akaari Clone":
        bad.append(f"creature {AKAARI_CLONE}: name {mine[0].get('name')!r}, expected 'Akaari Clone'")
    mm = [x for x in models if int(x["CreatureID"]) == AKAARI_CLONE]
    if len(mm) != 1 or (int(mm[0]["CreatureDisplayID"]), int(mm[0]["Idx"])) != (11686, 0):
        bad.append(f"creature {AKAARI_CLONE}: models {[(x['CreatureDisplayID'], x['Idx']) for x in mm]}, "
                   f"expected one display 11686 at idx 0")
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
        idx = {"infinite": reuse.duration_index(0), "r25": reuse.range_index(25.0)}
        for ms in (2000, 2500, 3000, 5000, 8000, 10000, 15000, 30000):
            idx[f"d{ms}"] = reuse.duration_index(ms)
        _CACHE.update(package=package, rows=by_id, idx=idx)
    return _CACHE


class RogueS2DataTest(unittest.TestCase):
    def assertClean(self, problems: list[str]):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_s2_row_set(self):
        self.assertClean(check_s2_id_set(_data()["rows"]))

    def test_rows(self):
        d = _data()
        self.assertClean(check_rows(d["rows"], *expectations(d["idx"])))

    def test_value_cases(self):
        self.assertClean(check_value_cases(_data()["rows"], AMOUNTS))

    def test_effect_absence(self):
        self.assertClean(check_effect_absence(_data()["rows"]))

    def test_copy_frames(self):
        self.assertClean(check_copy_frames(_data()["rows"]))

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

    def test_mask_helpers(self):
        self.assertClean(check_mask_helpers(m))

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

    def test_links_and_custom_attrs(self):
        p = _data()["package"]
        self.assertClean(check_links_attrs(p.linked_spells, p.custom_attrs))

    def test_sdv(self):
        d = _data()
        self.assertClean(check_sdv(d["package"].tooltip_vars, d["rows"]))

    def test_consts(self):
        self.assertClean(check_consts({c["name"]: (c["value"], c["cpp_type"]) for c in _data()["package"].consts}))

    def test_creature(self):
        p = _data()["package"]
        self.assertClean(check_creature(p.creature_templates, p.creature_template_models))


# ---- negative fixtures: every check must fire on a minimal bad input -----------------------------------------------------

IDX = {"r25": 34, "infinite": 21, "d2000": 39, "d2500": 225, "d3000": 27, "d5000": 28, "d8000": 31, "d10000": 1, "d15000": 8, "d30000": 9}


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


def _copy(rows: dict) -> dict:
    return {k: dict(v) for k, v in rows.items()}


def _good_full_rows() -> dict:
    """Rows satisfying the id-set / carrier / mask / reader / value / text / visibility / copy checks too."""
    rows = _good_rows()
    for sid in S2_IDS:
        r = rows.setdefault(sid, {"ID": sid})
        r["SpellClassSet"] = 8
        for n, w in enumerate(CARRIER_CLASS.get(sid, (0, 0, 0)), 1):
            r[f"SpellClassMask_{n}"] = w
        if sid in HIDDEN:
            r["Attributes"] = _u32(r.get("Attributes")) | ATTR0_HIDDEN
    rows[SHADOW_DANCE]["SpellClassMask_2"] = 0x2000000
    for sid, eff, comp, aura, op in READERS:
        r = rows.setdefault(sid, {"ID": sid})
        for n, w in enumerate(COMPOSITES[comp], 1):
            r[f"EffectSpellClassMask{'ABC'[eff - 1]}_{n}"] = w
        if aura is not None:
            r[f"EffectAura_{eff}"] = aura
        if op is not None:
            r[f"EffectMiscValue_{eff}"] = op
    for sid in (13981, 14066):
        for n, w in enumerate(ELUSIVENESS_CLOAK_B, 1):
            rows.setdefault(sid, {"ID": sid})[f"EffectSpellClassMaskB_{n}"] = w
    for sid, eff in EMPTY_MASKS:
        r = rows.setdefault(sid, {"ID": sid})
        for n in (1, 2, 3):
            r[f"EffectSpellClassMask{'ABC'[eff - 1]}_{n}"] = 0
    for sid, eff, aura, value in AMOUNTS:
        r = rows.setdefault(sid, {"ID": sid})
        r[f"EffectBasePoints_{eff}"] = (value - 1) & 0xFFFFFFFF
        r[f"EffectDieSides_{eff}"] = 1
        if aura is not None:
            r[f"EffectAura_{eff}"] = aura
    for sid, text in TEXTS.items():
        rows.setdefault(sid, {"ID": sid})["AuraDescription_Lang_enUS"] = text
    for sid in VISIBLE:
        r = rows.setdefault(sid, {"ID": sid})
        r["Attributes"] = _u32(r.get("Attributes")) & ~(ATTR0_PASSIVE | ATTR0_HIDDEN)
    for sid in (HEM_BLEED, DFA_FLIGHT):
        r = rows.setdefault(sid, {"ID": sid})
        r["EquippedItemClass"] = -1
    for e in (1, 2, 3):
        rows[DFA_FLIGHT][f"Effect_{e}"] = APPLY_AURA
    for e in (1, 2, 3):                                      # Shadowed is MOD_SHAPESHIFT 36 / 110 / 275: never MOD_STEALTH
        pass
    for src, cols in ((DEADLY_THROW, {"EquippedItemClass": 2, "EquippedItemSubclass": 173555, "DefenseType": 2,
                                      "SpellVisualID_1": 7, "SchoolMask": 1}),
                      (FOK, {"SpellVisualID_1": 8, "ImplicitTargetA_1": 22, "ImplicitTargetB_1": 15,
                             "EffectRadiusIndex_1": 9, "ImplicitTargetA_2": 22, "ImplicitTargetB_2": 15,
                             "EffectRadiusIndex_2": 9, "DefenseType": 2}),
                      (FOK_OH, {"ImplicitTargetA_1": 22, "ImplicitTargetB_1": 15, "EffectRadiusIndex_1": 9,
                                "DefenseType": 2})):
        rows.setdefault(src, {"ID": src}).update(cols)
    rows[DT_COPY].update({"EquippedItemClass": 2, "EquippedItemSubclass": 173555, "DefenseType": 2,
                          "SpellVisualID_1": 7, "SchoolMask": 1})
    rows[SV_MAIN].update(rows[FOK] | {"ID": SV_MAIN, "SpellLevel": 24, "Effect_2": ADD_COMBO,
                                      "SpellClassMask_2": 0x40000, "Attributes": rows[SV_MAIN]["Attributes"],
                                      "AttributesEx3": rows[SV_MAIN]["AttributesEx3"], "RangeIndex": RANGE_100,
                                      "FacingCasterFlags": 0, "SpellClassMask_1": 0, "SpellClassMask_3": 0,
                                      "SpellClassSet": 8})
    rows[SV_OFF].update({"DefenseType": 2, "ImplicitTargetA_1": 22, "ImplicitTargetB_1": 15, "EffectRadiusIndex_1": 9})
    rows[DT_COPY]["EffectAura_2"] = 33
    rows[DEADLY_THROW]["EffectAura_2"] = 33
    for sid, token in TOOLTIP_TOKENS.items():
        rows.setdefault(sid, {"ID": sid})["Description_Lang_enUS"] = f"x {{pot1*{token}}}"
    return rows


class RogueS2NegativeTest(unittest.TestCase):
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
        for sid, col, val in ((DFA, "DefenseType", 2), (DFA, "RangeIndex", 2), (DFA, "RecoveryTime", 10000),
                              (DFA, "ManaCost", 35), (DFA_LAND, "SpellClassMask_3", 0x40000),
                              (DFA_AREA, "DefenseType", 0), (DFA_FLIGHT, "EffectAura_3", 60),
                              (HEM_TICK, "DefenseType", 2), (HEM_BLEED, "RangeIndex", 2),
                              (ECHO, "FacingCasterFlags", 1), (ECHO, "RangeIndex", RANGE_100),
                              (SHADOW_DANCE, "StartRecoveryCategory", 133), (SHADOW_DANCE, "EffectMiscValue_3", 13),
                              (SHADOW_DANCE, "AttributesEx", 0x20400 | 0x20), (SHADOW_DANCE, "RecoveryTime", 60000),
                              (SHADOWSTEP, "Effect_2", 6), (CHEATING_DEATH, "EffectBasePoints_1", 0),
                              (13976, "ProcChance", 101), (51696, "ProcChance", 101), (51701, "ProcChance", 0)):
            rows = _good_rows()
            rows[sid][col] = val
            self.assertGreaterEqual(len(check_rows(rows, exact, ms, mc)), 1, (sid, col, val))

    def test_missing_row(self):
        rows = _good_rows()
        del rows[DFA]
        self.assertGreaterEqual(len(check_rows(rows, *expectations(IDX))), 1)

    def test_s2_row_set(self):
        rows = {sid: {} for sid in S2_IDS}
        self.assertEqual(check_s2_id_set(rows), [])
        self.assertEqual(len(check_s2_id_set({k: v for k, v in rows.items() if k != DFA})), 1)
        for extra in (204174, 204199, 204200, 204279):
            self.assertEqual(len(check_s2_id_set({**rows, extra: {}})), 1, extra)

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
        self.assertEqual(len(check_value_cases({k: v for k, v in rows.items() if k != HEM_R}, AMOUNTS)), 1)
        # negative base points read as signed (Cheating Death -90%)
        self.assertEqual(value_of({"EffectBasePoints_1": (-91) & 0xFFFFFFFF, "EffectDieSides_1": 1}, 1), -90)
        self.assertEqual(value_of({"EffectBasePoints_1": 5, "EffectDieSides_1": 0}, 1), 5)
        # R10: crit talents are aura 290, not 52 / 57
        for crit_aura in (52, 57):
            bad = _copy(rows)
            bad[30894]["EffectAura_1"] = crit_aura
            self.assertGreaterEqual(len(check_value_cases(bad, AMOUNTS)), 1)

    def test_effect_absence(self):
        rows = _good_full_rows()
        self.assertEqual(check_effect_absence(rows), [])
        for sid, col, val in ((14179, "EffectAura_1", 109), (58423, "EffectAura_2", 109), (SHADOW_DANCE, "EffectAura_1", 16),
                              (SHADOW_DANCE, "EffectAura_3", 16), (51708, "EffectAura_3", 79),
                              (51709, "EffectAura_2", 107), (DFA_FLIGHT, "Effect_3", 0)):
            bad = _copy(rows)
            bad[sid][col] = val
            if sid == 51709:
                bad[sid]["EffectMiscValue_2"] = OP["COST"]
            self.assertGreaterEqual(len(check_effect_absence(bad)), 1, (sid, col, val))

    def test_copy_frames(self):
        rows = _good_full_rows()
        self.assertEqual(check_copy_frames(rows), [])
        for sid, col in ((DT_COPY, "EquippedItemSubclass"), (DT_COPY, "DefenseType"), (DT_COPY, "SpellVisualID_1"),
                         (DT_COPY, "EffectAura_2"), (SV_MAIN, "SpellVisualID_1"), (SV_MAIN, "EffectRadiusIndex_1"),
                         ):
            bad = _copy(rows)
            bad[sid][col] = _u32(bad[sid].get(col)) ^ 0x2
            self.assertGreaterEqual(len(check_copy_frames(bad)), 1, (sid, col))
        self.assertGreaterEqual(len(check_copy_frames({})), 1)

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

    def test_carriers(self):
        rows = _good_full_rows()
        self.assertEqual(check_carriers(rows), [])
        for (dword, bit), who in {**NEW_BIT_CARRIERS, **S2_SHARED_BIT_CARRIERS}.items():
            col = f"SpellClassMask_{dword + 1}"
            gone = _copy(rows)                                   # a carrier loses the bit
            victim = sorted(who)[0]
            gone[victim][col] = _u32(gone[victim].get(col)) & ~bit
            self.assertGreaterEqual(len(check_carriers(gone)), 1, ((dword, bit), "missing"))
            extra = _copy(rows)                                   # a stranger gains it
            extra[204130][col] = _u32(extra[204130].get(col)) | bit
            self.assertGreaterEqual(len(check_carriers(extra)), 1, ((dword, bit), "extra"))
        for (dword, bit) in NEW_BIT_CARRIERS:                      # a non-S2 row too (new bits are exact across all rows)
            extra = _copy(rows)
            extra[999999] = {"ID": 999999, f"SpellClassMask_{dword + 1}": bit}
            self.assertGreaterEqual(len(check_carriers(extra)), 1, ((dword, bit), "stranger"))

    def test_new_masks(self):
        rows = _good_full_rows()
        self.assertEqual(check_new_masks(rows), [])
        bad = _copy(rows)
        bad[ECHO]["SpellClassMask_3"] = 0x1000
        self.assertGreaterEqual(len(check_new_masks(bad)), 1)               # the echo carries nothing
        bad = _copy(rows)
        bad[ECHO]["SpellClassMask_1"] = D0_B9
        self.assertGreaterEqual(len(check_new_masks(bad)), 1)               # not even Ambush's d0 b9
        bad = _copy(rows)
        bad[DFA]["SpellClassSet"] = 0
        self.assertEqual(len(check_new_masks(bad)), 1)
        for sid, col, bit in ((HEM_TICK, "SpellClassMask_1", D0_B20), (HEM_BLEED, "SpellClassMask_1", D0_B20),
                              (DFA_LAND, "SpellClassMask_1", D0_B17), (DFA, "SpellClassMask_1", D0_B11),
                              (VOLLEY, "SpellClassMask_1", D0_B22), (SV_MAIN, "SpellClassMask_1", D0_B25),
                              (DT_COPY, "SpellClassMask_1", D0_B26), (MOS_R[0], "SpellClassMask_3", 0x1),
                              (SHADOW_DANCE, "SpellClassMask_1", D0_B11), (SHADOW_DANCE, "SpellClassMask_1", D0_B22),
                              (DFA_AREA, "SpellClassMask_3", 0x100)):
            bad = _copy(rows)
            bad[sid][col] = _u32(bad[sid].get(col)) | bit
            self.assertGreaterEqual(len(check_new_masks(bad)), 1, (sid, col, bit))

    def test_readers(self):
        rows = _good_full_rows()
        self.assertEqual(check_readers(rows), [])
        for sid, eff, comp, aura, op in READERS:
            bad = _copy(rows)
            col = f"EffectSpellClassMask{'ABC'[eff - 1]}_1"
            bad[sid][col] = _u32(bad[sid].get(col)) ^ 0x1
            self.assertGreaterEqual(len(check_readers(bad)), 1, (sid, eff, "mask"))
            wrong_letter = _copy(rows)          # the wrong-effect-letter trap (bug-doc :2178): mask on the neighbour effect
            for n in (1, 2, 3):
                wrong_letter[sid][f"EffectSpellClassMask{'ABC'[eff % 3]}_{n}"] = COMPOSITES[comp][n - 1]
                wrong_letter[sid][f"EffectSpellClassMask{'ABC'[eff - 1]}_{n}"] = 0
            self.assertGreaterEqual(len(check_readers(wrong_letter)), 1, (sid, eff, "letter"))
            # the letter/dword swap (A_2 where B_1 was meant): transpose the mask over the (letter, number) grid
            if any(COMPOSITES[comp]):
                swapped = _copy(rows)
                for n in (1, 2, 3):
                    swapped[sid][f"EffectSpellClassMask{'ABC'[eff - 1]}_{n}"] = 0
                for n in (1, 2, 3):
                    swapped[sid][f"EffectSpellClassMask{'ABC'[n - 1]}_{eff}"] = COMPOSITES[comp][n - 1]
                if COMPOSITES[comp] != tuple(COMPOSITES[comp][eff - 1] if i == eff - 1 else 0 for i in range(3)) or eff != 1:
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
            bad = _copy(rows)
            bad[sid][f"EffectSpellClassMask{'ABC'[eff - 1]}_1"] = 0x400000
            self.assertGreaterEqual(len(check_readers(bad)), 1, (sid, eff, "stale twin"))
        for sid in (13981, 14066):
            bad = _copy(rows)
            bad[sid]["EffectSpellClassMaskB_2"] = 0
            self.assertGreaterEqual(len(check_readers(bad)), 1, (sid, "Cloak"))
        self.assertGreaterEqual(len(check_readers({})), 1)

    def test_composites(self):
        class Mod:
            pass
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
        self.assertEqual(len(check_composites(Mod())), len(COMPOSITES))

    def test_mask_helpers(self):
        class Mod:
            read_mask_keys = staticmethod(m.read_mask_keys)
            clear_mask_keys = staticmethod(m.clear_mask_keys)
            class_mask_keys = staticmethod(m.class_mask_keys)
        self.assertEqual(check_mask_helpers(Mod), [])

        def swapped(eff_index, triple):          # letter and number mixed up: the S1-caught trap
            return {f"EffectSpellClassMask{'ABC'[n]}_{eff_index + 1}": int(w) for n, w in enumerate(triple)}

        def no_zeros(eff_index, triple):
            return {k: v for k, v in m.read_mask_keys(eff_index, triple).items() if v}

        for broken in (swapped, no_zeros):
            class Bad(Mod):
                read_mask_keys = staticmethod(broken)
            self.assertGreaterEqual(len(check_mask_helpers(Bad)), 1, broken.__name__)

        class NoRaise(Mod):
            read_mask_keys = staticmethod(lambda e, t: {**m.read_mask_keys(e % 3, t)})
        self.assertGreaterEqual(len(check_mask_helpers(NoRaise)), 1)

        class BadClear(Mod):
            clear_mask_keys = staticmethod(lambda *e: m.clear_mask_keys(*e[:1]))
        self.assertGreaterEqual(len(check_mask_helpers(BadClear)), 1)

    def test_grid(self):
        def good():
            out = [{"id": tid, "tab_id": TAB, "tier": t, "column": c, "rank_spell_ids": list(r), "depends_on": None,
                    "flags": FLAGS.get(tid, 0)} for tid, (t, c, r) in GRID.items()]
            out += [{"id": 5000 + i, "tab_id": COMBAT_TAB, "tier": 0, "column": 0, "rank_spell_ids": [1],
                     "depends_on": None, "flags": 0} for i in range(COMBAT_TAB_TALENTS)]
            out += [{"id": tid, "tab_id": RETIRED_TAB, "tier": 0, "column": 0, "rank_spell_ids": [], "depends_on": None,
                     "flags": 0} for tid in RETIRED]
            return out
        tab_text = "subtlety_183_tab = tab(\n    id=183,\n    skill_line=39,\n    raw_overrides={},\n)\n"
        ret = [{"id": t} for t in RETIRED]
        self.assertEqual(check_grid(good(), ret, tab_text), [])
        idx = lambda ts, tid: next(t for t in ts if t["id"] == tid)  # noqa: E731
        cases = []
        g = good(); idx(g, 60425)["tier"] = 1; cases.append(("moved", g))
        g = good(); idx(g, 261)["column"] = 2; cases.append(("moved col", g))
        g = good(); idx(g, 681)["depends_on"] = {"talent_id": 284, "rank": 1}; cases.append(("arrow", g))
        g = good(); idx(g, 1713)["rank_spell_ids"] = [31221, 31222, 31223]; cases.append(("old MoS ranks", g))
        g = good(); idx(g, 2244)["rank_spell_ids"] = [14179, 58422, 58423, 58424, 58425]; cases.append(("5 ranks", g))
        g = good(); idx(g, 60427)["rank_spell_ids"] = [204137, 204136]; cases.append(("rank order", g))
        g = good(); g = [t for t in g if t["id"] != 60433]; cases.append(("missing", g))
        g = good(); idx(g, 241)["tab_id"] = TAB; cases.append(("241 not retired", g))
        g = good(); idx(g, 2079)["rank_spell_ids"] = [58414]; cases.append(("2079 ranked", g))
        g = good(); g.append({"id": 9999, "tab_id": TAB, "tier": 7, "column": 3, "rank_spell_ids": [1], "depends_on": None,
                              "flags": 0})
        cases.append(("extra", g))
        g = good(); idx(g, 60428)["column"] = 2; cases.append(("shared cell", g))
        g = good(); g.append(dict(idx(g, 284))); cases.append(("duplicate", g))
        for tid, wrong in ((681, 1), (381, 1), (284, 0), (1714, 0), (2081, 0), (60433, 0)):
            g = good(); idx(g, tid)["flags"] = wrong; cases.append((f"flags {tid}", g))
        g = good(); g.append({"id": 2072, "tab_id": COMBAT_TAB, "tier": 7, "column": 0, "rank_spell_ids": [5952],
                              "depends_on": None, "flags": 0})
        cases.append(("2072 back on Combat", g))
        g = good(); g = [t for t in g if t["id"] != 5000]; cases.append(("Combat 26", g))
        for label, talents in cases:
            self.assertGreaterEqual(len(check_grid(talents, ret, tab_text)), 1, label)
        self.assertGreaterEqual(len(check_grid(good(), ret[1:], tab_text)), 1)
        self.assertGreaterEqual(len(check_grid(good(), ret, tab_text.replace("39", "253"))), 1)
        self.assertGreaterEqual(len(check_grid(good(), ret, tab_text.replace("    skill_line=39,\n", ""))), 1)

    def test_slas(self):
        sid, line, spell = SLA_ROW
        good = [{"id": sid, "skill_line": line, "spell_id": spell, "class_mask": 8, "acquire_method": 0}]
        self.assertEqual(check_slas(good), [])
        self.assertGreaterEqual(len(check_slas([])), 1)
        self.assertGreaterEqual(len(check_slas(good + [{**good[0], "id": 30826}])), 1)
        for col, val in (("skill_line", 253), ("spell_id", 5), ("class_mask", 0), ("acquire_method", 1)):
            self.assertEqual(len(check_slas([{**good[0], col: val}])), 1, col)

    def test_scripts(self):
        names = [{"spell_id": s, "ScriptName": n} for s, n in sorted(SCRIPTS)]
        rem = [{"spell_id": s, "ScriptName": n} for s, n in sorted(UNBOUND)]
        self.assertEqual(check_scripts(names, rem), [])
        for i in range(len(names)):
            self.assertEqual(len(check_scripts(names[:i] + names[i + 1:], rem)), 1, names[i])
        for i in range(len(rem)):
            self.assertEqual(len(check_scripts(names, rem[:i] + rem[i + 1:])), 1, rem[i])
        self.assertEqual(len(check_scripts(names + [{"spell_id": 51698, "ScriptName": "spell_rog_honor_among_thieves"}], rem)), 1)
        self.assertEqual(len(check_scripts(names, rem + [{"spell_id": 14185, "ScriptName": "spell_rog_preparation"}])), 1)
        self.assertEqual(len(check_scripts(names + [{"spell_id": 204162, "ScriptName": "spell_x"}], rem)), 1)
        self.assertEqual(len(check_scripts(names + [{"spell_id": 204161, "ScriptName": "spell_x"}], rem)), 1)

    def test_procs(self):
        rem = [{"SpellId": s} for s in PROC_REMOVED]

        def row(sid):
            mask, flags, chance = PROC_ROWS[sid]
            return {"SpellId": sid, "SpellFamilyName": 8, "SpellFamilyMask0": mask[0], "SpellFamilyMask1": mask[1],
                    "SpellFamilyMask2": mask[2], "ProcFlags": flags, "SpellPhaseMask": 2, "HitMask": 0, "Chance": chance}
        good = [row(-13976), row(51696)]
        self.assertEqual(check_procs(good, rem), [])
        self.assertEqual(len(check_procs(good[1:], rem)), 1)
        self.assertEqual(len(check_procs(good + [good[0]], rem)), 1)
        for i in range(len(rem)):
            self.assertEqual(len(check_procs(good, rem[:i] + rem[i + 1:])), 1, rem[i])
        for i, (col, val) in enumerate((("SpellFamilyName", 0), ("SpellFamilyMask0", 0x100), ("SpellFamilyMask2", 1),
                                        ("SpellPhaseMask", 1), ("HitMask", 2), ("ProcFlags", 0x4), ("Chance", 50.0))):
            for which in (0, 1):
                bad = [dict(good[0]), dict(good[1])]
                bad[which][col] = val
                self.assertGreaterEqual(len(check_procs(bad, rem)), 1, (which, col))
        stray = {**good[0], "SpellId": 204137, "SpellPhaseMask": 0}
        self.assertGreaterEqual(len(check_procs(good + [stray], rem)), 1)
        self.assertGreaterEqual(len(check_procs([{**good[0], "SpellPhaseMask": 0}, good[1]], rem)), 1)

    def test_links_attrs(self):
        links = [{"spell_trigger": a, "spell_effect": b, "type": t} for a, b, t in sorted(LINKS)]
        attrs = [{"spell_id": s, "attributes": v} for s, v in CUSTOM_ATTRS.items()]
        self.assertEqual(check_links_attrs(links, attrs), [])
        self.assertEqual(len(check_links_attrs(links[1:], attrs)), 1)
        self.assertEqual(len(check_links_attrs(links[:-1] + [{**links[-1], "type": 1}], attrs)), 1)
        self.assertEqual(len(check_links_attrs(links, attrs[1:])), 1)
        self.assertEqual(len(check_links_attrs(links, [{**attrs[0], "attributes": 0x20000}] + attrs[1:])), 1)
        self.assertEqual(len(check_links_attrs(links, attrs + [{"spell_id": DFA, "attributes": 0x8000}])), 1)

    def test_sdv(self):
        def body(sdv):
            return "".join(f"${n}=1\r\n" for n in sorted(SDV_VARS.get(sdv, ())))
        entries = [{"id": i, "Variables": body(i)} for i in (1320, 1321, 1322, 1323, 1335, 1336)]
        rows = {sid: {"SpellDescriptionVariableID": sdv} for sdv, ss in SDV_ATTACH.items() for sid in ss}
        self.assertEqual(check_sdv(entries, rows), [])
        self.assertGreaterEqual(len(check_sdv([e for e in entries if e["id"] != 1335], rows)), 1)
        self.assertEqual(len(check_sdv(entries + [{"id": 1337, "Variables": ""}], rows)), 1)
        long_name = [{**e, "Variables": e["Variables"] + "$averyverylongname=1"} if e["id"] == 1335 else e for e in entries]
        self.assertEqual(len(check_sdv(long_name, rows)), 1)
        for sdv, names in SDV_VARS.items():
            for name in names:
                trimmed = [{**e, "Variables": e["Variables"].replace(f"${name}=1\r\n", "")} if e["id"] == sdv else e
                           for e in entries]
                self.assertEqual(len(check_sdv(trimmed, rows)), 1, (sdv, name))
        for sid in (BACKSTAB, AMBUSH, 2098):
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

    def test_creature(self):
        creatures = [{"entry": AKAARI_CLONE, "name": "Akaari Clone"}]
        models = [{"CreatureID": AKAARI_CLONE, "CreatureDisplayID": 11686, "Idx": 0}]
        self.assertEqual(check_creature(creatures, models), [])
        self.assertEqual(len(check_creature([], models)), 1)
        self.assertEqual(len(check_creature([{**creatures[0], "name": "Clone"}], models)), 1)
        self.assertEqual(len(check_creature(creatures, [])), 1)
        self.assertEqual(len(check_creature(creatures, [{**models[0], "CreatureDisplayID": 1}])), 1)
        self.assertEqual(len(check_creature(creatures, models + models)), 1)


if __name__ == "__main__":
    unittest.main()
