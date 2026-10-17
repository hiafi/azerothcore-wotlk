"""
Hunter S2a (Marksmanship) built-row guards (hunter-rework S2a-HANDOFF WP-A table row A5, A1-A21; S2-HANDOFF stale
lines 1, 2, 5, 6, 11 and lessons M1-M4, M8, M15; MARKSMANSHIP.md 2.2, 2.4, 4.1, 5.1, 5.6-5.11, 6, 8).

Written from the spec, not from the DSL: every expected value below is the spec's. Loads the real hunter DSL package
(shared loader of `test_hunter_pet_data.py`, one load per process) and asserts on the BUILT rows (stock base + DSL +
raw_overrides via `build.build_spell_row`), so a stale raw twin that wins fails here too:

  (a) tab 363: the 33 talents of MM 2.2 at their cells with their 6 rank lists, 81 points, one talent per cell, no
      prerequisite (entry, raw override, built row), Sniper Training 2143 on 363 at (7,2) and on no other tab, the
      seven castable rows flagged, SLA 30544-30546 (skill line 163, class mask 4), no trainer row for a mark (L13);
  (b) the 23 orphaned rank spells (MM 6.1 / 0-verify 6) in no talent row of stock Talent.dbc overlaid by the package;
  (c) the three marks (A1, MM 4.1, stale line 2): d2 b27 only, CastingTimeIndex 18 (live 0 ms), EquippedItemClass 2,
      CumulativeAura 10, the three effects with eff2 APPLY_AURA DUMMY bp -1, shot fields, cooldowns, levels, icons;
  (d) Aimed Shot 19434 (A6, stale line 1, M3): live cast 2000 ms (CastingTimeIndex 16 = 1500 + the 500 ms ranged-slot
      add), category 1301 declared, 10 s category cooldown and no second cooldown, no ap / sp potency, d0 b17 only;
  (e) the free Arcane Shot 201933 (A9, stale line 3): eff1 equals Arcane Shot 3044's built eff1 (mana semantics), index
      18, class -1, d0 b11 only, free and cooldown-less, bound to the shot-mana and MM Arcane Shot scripts only;
  (f) M1 visibility: the visible buff / debuff list and the hidden helper list; Falcon's Haste 201942 (stale line 5);
  (g) M4: EquippedItemClass -1 on every id S2a declares or edits, except the player-cast shots (2);
  (h) family-bit carriers (FAMILY-BITS 0.6): d2 b27 only on the marks, d2 b28 only on 201930 / 201931, no custom id
      but 201933 on d0 b11, none but S2b's 201934 / 201935 on d0 b17, no bit on the S2a helpers, buffs and ranks;
  (i) SpellMod rows (M8, A5, A16, MM 5.7-5.11, 6): SpellClassSet 9 and the spec's op / mask on the helpers, the
      Mastery passive, the charged buffs, Marked for Death; Mortal Shots / Improved Stings / RWS / Lethal Shots /
      Sniper Training masks equal the `_masks.py` composites (and the composites equal MM 2.4); 53353 = 0x800; no
      reader mask (effect mask or spell_proc family mask) on an S2a id holds d1 b28;
  (j) spell_proc rows (A13-A15, A17, MM 8): each key declared exactly once; the four charged-buff CAST rows lack
      attributes_mask 0x2; 201965 HIT / CRIT; 201981 kill row; -34485 / -53215 / -53234 masks;
  (k) M15: every tab-363 rank has ProcTypeMask 0 or an explicit spell_proc row (Barrage 24691 accepted, A18), and no
      effect mask sits on an absent effect; Rapid Killing r1/r2 DUMMY with no trigger, r3 kill trigger;
  (l) A19: Stampede 201802 stays SpellClassSet 0 (stock Readiness never resets it; no Readiness rebind);
  (m) bindings: the brief's script classes on positive keys, the two exact stock unbinds and
      linked_spell(53244, 201951, 2).

S2b (S2b-HANDOFF WP-A row A2, B2 / B6 / B7 / B9, the S2a review's m-1 and the 34082 ruling) adds:

  (n) the ricochet 201934 / bounce 201935 (B2): d0 b17 only, Speed 0, CastingTimeIndex 18, EquippedItemClass -1,
      SUPPRESS_CASTER_PROCS, eff0 NORMALIZED_WEAPON_DMG bp -1, eff1 live weapon potency = PACK_SHOT_DAMAGE_PCT of
      Aimed Shot 19434's (A1 derives it from a private literal 220: the built equality is the guard), 110 today;
  (o) the half Volley 201936 / tick 201937 (B6): 201936 d2 b30 only, hidden (0x80), 3 s / 1 s = 3 unhasted ticks
      (no AttributesEx5 0x2000), eff0 the dynobj with ap potency 75.5 direct time_basis 1500 (spell_bonus_data equal
      to the Volley tick 42243's); 201937 potency_excluded (no bonus row), no family bit, AttributesEx3 0x20010000;
      VOLLEY_DAMAGE / BARRAGE_DAMAGE hold d2 b30 and the Barrage / Rain of Arrows ranks carry them;
  (p) Barrage r3's spell_proc row 24691 (CAST, 10 s cooldown, Multi-Shot mask, disable_effects_mask 0x1, flags
      0x100), no chain-key twin;
  (q) Lone Survivor 201950 visible (M1, AttributesEx7 0), Combat Experience 201952 hidden + linked_spell(201982,
      201952, 2); the S2b bindings (201935 unscripted, -42243 kept);
  (r) a source guard: every CastSpell / CastCustomSpell of 201934 / 201935 in the hunter C++ passes
      TRIGGERED_FULL_MASK and no other TRIGGERED_* flag (R3: the d0 b17 load fix's 10 s RecoveryTime);
  (s) 34082 (user ruling 2026-10-16): no aura 140 effect left, eff0 PROC_TRIGGER_SPELL -> 34084 kept; no
      hunter-learnable passive (SLA auto-learn, talent rank, trainer row, linked type 2) carries aura 140 with a
      non-zero amount (the orphans 34469 / 34470 are not learnable: 0-verify finding 4);
  (t) Multi-Shot 2643 left as it is (B1 "data unchanged"; the hidden 0.5 s cast is the user's open question);
  (u) the S2b review fixes: 201936 SpellLevel = the Volley tick 42243's (R-data M-1: the potency BaseLevel),
      AttributesEx2 IGNORE_LINE_OF_SIGHT (0x4) on 201934 / 201935 / 201932 (R-cpp m-1), and exactly one
      CANNOT_BE_SAVED (0x01000000) spell_custom_attr row on 201950 and 201936 (R-cpp m-4).

Every check is a pure function; the negative-fixture class feeds each one a good input (must pass) and a crafted bad
copy (must fail), so a check that silently passes everything is caught.

Run directly:

    apps/dbc-tools/.venv/bin/python3 -m pytest apps/dbc-tools/lib/test_hunter_mm_data.py -q
"""

from __future__ import annotations

import copy
import importlib.util
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import build, dbcfmt, state  # noqa: E402
from lib.test_hunter_pet_data import package_data  # noqa: E402

TOOL_ROOT = Path(__file__).resolve().parents[1]
MASKS_PY = TOOL_ROOT / "source" / "classes" / "hunter" / "_masks.py"
REPO_ROOT = TOOL_ROOT.parents[1]
# (r) the C++ that may cast the ricochet / bounce (B1 writes the casts into the first one)
PACK_SHOT_CASTER_SOURCES = (
    REPO_ROOT / "src" / "server" / "scripts" / "Spells" / "spell_hunter_marksmanship.cpp",
    REPO_ROOT / "src" / "server" / "scripts" / "Spells" / "hunter_hooks.cpp",
    REPO_ROOT / "src" / "server" / "game" / "Entities" / "Unit" / "HunterMechanics.cpp",
)

LETTERS = ("A", "B", "C")
SPELLFAMILY_HUNTER = 9

# effect / aura / SpellModOp ids (SpellEffects.h, SpellAuraDefines.h, SpellDefines.h)
EFFECT_SCHOOL_DAMAGE = 2
EFFECT_DUMMY = 3
EFFECT_APPLY_AURA = 6
EFFECT_WEAPON_PERCENT_DAMAGE = 31
EFFECT_PERSISTENT_AREA_AURA = 27
EFFECT_SCRIPT_EFFECT = 77
EFFECT_NORMALIZED_WEAPON_DMG = 121
AURA_PERIODIC_DAMAGE = 3
AURA_DUMMY = 4
AURA_MOD_STAT = 29
AURA_MOD_DAMAGE_PERCENT_DONE = 79
AURA_MOD_RANGED_HASTE = 140
AURA_PERIODIC_TRIGGER_SPELL = 23
AURA_PROC_TRIGGER_SPELL = 42
AURA_ADD_FLAT_MODIFIER = 107
AURA_ADD_PCT_MODIFIER = 108
AURA_HASTE_ALL = 193
AURA_PERIODIC_DUMMY = 226
SPELLMOD_AURAS = {AURA_ADD_FLAT_MODIFIER, AURA_ADD_PCT_MODIFIER}
OP_DAMAGE = 0
OP_CRITICAL_CHANCE = 7
OP_CASTING_TIME = 10
OP_COST = 14
OP_CRIT_DAMAGE_BONUS = 15
OP_GLOBAL_COOLDOWN = 21
OP_DOT = 22

ATTR_USES_RANGED_SLOT = 0x2
ATTR_PASSIVE = 0x40
ATTR_DO_NOT_DISPLAY = 0x80
ATTR_EX_NO_AURA_ICON = 0x10000000          # SPELL_ATTR1_DONT_DISPLAY_IN_AURA_BAR
ATTR_EX2_IGNORE_LINE_OF_SIGHT = 0x4        # SPELL_ATTR2_IGNORE_LINE_OF_SIGHT (SharedDefines.h)
ATTR_EX3_SUPPRESS_CASTER_PROCS = 0x10000
CUSTOM_ATTR_CANNOT_BE_SAVED = 0x01000000    # SPELL_ATTR0_CU_AURA_CANNOT_BE_SAVED (SpellInfo.h)
ATTR_EX3_IGNORE_CASTER_MODIFIERS = 0x20000000
ATTR_EX5_HASTE_AFFECT_DURATION = 0x2000     # SPELL_ATTR5_SPELL_HASTE_AFFECTS_PERIODIC (hasted ticks)
ATTR_EX7_CONSOLIDATE = 0x10000000
RANGED_SLOT_ADD_MS = 500                    # SpellInfo::CalcCastTime, SpellInfo.cpp:2815-2816
DEFENSE_RANGED = 3
SCHOOL_PHYSICAL, SCHOOL_NATURE, SCHOOL_ARCANE = 1, 8, 64

D1_PET_BIT = 0x10000000
D0_ARCANE_SHOT = 0x800                      # d0 b11
D0_AIMED_SHOT = 0x20000                     # d0 b17
D2_MARK_PRESS = 0x8000000                   # d2 b27
D2_MARK_DOT = 0x10000000                    # d2 b28
D2_STEADY_SHOT = 0x20000000                 # d2 b29
D2_HALF_VOLLEY = 0x40000000                 # d2 b30
D0_MULTI_SHOT = 0x1000                      # d0 b12

PROC_FLAG_KILL = 0x2
PROC_FLAG_DONE_SPELL_RANGED = 0x100
PROC_PHASE_CAST = 0x1
PROC_PHASE_HIT = 0x2
PROC_HIT_CRITICAL = 0x2
PROC_ATTR_REQ_EXP_OR_HONOR = 0x1
PROC_ATTR_TRIGGERED_CAN_PROC = 0x2

# ---- ids -------------------------------------------------------------------------------------------------------------
TAB = 363
SV_TAB = 362
SNIPER_TRAINING_ROW = 2143
MARKS = (201920, 201921, 201922)
SNIPERS_MARK, VIPERS_MARK, FALCONS_MARK = MARKS
VIPERS_BITE, VIPERS_VENOM, CONVERGENCE, ARCANE_SHOT_FREE = 201930, 201931, 201932, 201933
FIRE, QUICKENING, FALCONS_HASTE, TRICK_SHOTS_BUFF, ROA_BUFF = 201940, 201941, 201942, 201943, 201944
EFFICIENCY_BUFF, PRECISE_SHOTS_BUFF, FALCONS_EDGE = 201945, 201946, 201947
AIMED_CRIT_HELPER, CHIMERA_CRIT_HELPER, MASTERY = 201948, 201949, 201951
AIMED_SHOT, CHIMERA_SHOT, ARCANE_SHOT, STEADY_SHOT, MULTI_SHOT = 19434, 53209, 3044, 56641, 2643
CHIMERA_SERPENT, WILD_QUIVER_SHOT, RAPID_KILLING_BUFF_ID = 53353, 53254, 35098
SNIPER_TRAINING_BUFFS = (64418, 64419, 64420)
SNIPER_TRAINING_RANKS = (53302, 53303, 53304)
STAMPEDE = 201802
PRECISION_R3, RAPID_KILLING_R3, MFD_R3 = 201965, 201981, 53244
NEW_S2A_IDS = (*MARKS, VIPERS_BITE, VIPERS_VENOM, CONVERGENCE, ARCANE_SHOT_FREE, *range(201940, 201950), MASTERY,
               *range(201960, 201983))
RICOCHET, BOUNCE, HALF_VOLLEY, HALF_VOLLEY_TICK = 201934, 201935, 201936, 201937
LONE_SURVIVOR_BUFF, COMBAT_EXPERIENCE_CAPSTONE = 201950, 201952
PACK_SHOTS = (RICOCHET, BOUNCE)
NEW_S2B_IDS = (RICOCHET, BOUNCE, HALF_VOLLEY, HALF_VOLLEY_TICK, LONE_SURVIVOR_BUFF, COMBAT_EXPERIENCE_CAPSTONE)
VOLLEY, VOLLEY_TICK, BARRAGE_R3, COMBAT_EXPERIENCE_R3 = 1510, 42243, 24691, 201982
LONE_SURVIVOR_RANKS = (19407, 19412)
BARRAGE_RANKS = (19461, 19462, BARRAGE_R3)
RAIN_OF_ARROWS_RANKS = (201979, 201980)
ADVANTAGED_STATE, ADVANTAGED_STATE_PROC = 34082, 34084
SERPENTS_SWIFTNESS_ORPHANS = (34469, 34470)       # aura 140 kept, taught by nothing (0-verify finding 4)
# stock non-rank rows S2a edits whose built row must be -1 (helpers / buffs / triggered; M4)
EDITED_STOCK_HELPERS = (CHIMERA_SERPENT, WILD_QUIVER_SHOT, RAPID_KILLING_BUFF_ID, *SNIPER_TRAINING_BUFFS, 42243)
# S2b: ids it declares or binds whose built row must be -1 (Volley 1510 is a player-cast channel: class 2, untouched)
S2B_MINUS_ONE_IDS = (*NEW_S2B_IDS, BARRAGE_R3, *LONE_SURVIVOR_RANKS, CONVERGENCE, ADVANTAGED_STATE)
# M4 exemption: the player-cast ranged shots (S2-HANDOFF M4 / stale line 6). Mirrors test_hunter_bm_data's set.
PLAYER_CAST_SHOTS = frozenset({STEADY_SHOT, ARCANE_SHOT, AIMED_SHOT, CHIMERA_SHOT, MULTI_SHOT, *MARKS})

# MM 2.2 / 6: talent id -> ((tier, column), rank spell ids)
TAB_LAYOUT = {
    1344: ((0, 0), (19426, 19427, 19429)),
    2197: ((0, 1), (53620, 53621, 53622)),
    60225: ((0, 2), (201960, 201961, 201962)),
    1341: ((0, 3), (19407, 19412)),
    1349: ((1, 0), (19485, 19487, 19488)),
    1343: ((1, 1), (19421, 19422, 19423)),
    60226: ((1, 2), (201963, 201964, 201965)),
    1806: ((1, 3), (34482, 34483, 34484)),
    1818: ((2, 0), (201966, 201967, 201968)),
    1345: ((2, 1), (AIMED_SHOT,)),
    1346: ((2, 2), (19454, 19455, 19456)),
    1819: ((2, 3), (34948, 34949, 201981)),
    2133: ((3, 0), (201969, 201970, 201971)),
    1807: ((3, 1), (34485, 34486, 34487)),
    1342: ((3, 2), (19416, 19417, 19418)),
    1348: ((3, 3), (19464, 19465, 19466)),
    60227: ((4, 1), (SNIPERS_MARK,)),
    1351: ((4, 2), (201972, 201973, 201974)),
    1347: ((4, 3), (19461, 19462, 24691)),
    1804: ((5, 0), (34475, 34476, 201982)),
    1353: ((5, 1), (23989,)),
    1362: ((5, 2), (19507, 19508, 19509)),
    2131: ((5, 3), (201975,)),
    2130: ((6, 0), (53234, 53237, 53238)),
    60228: ((6, 1), (VIPERS_MARK,)),
    1821: ((6, 2), (201976, 201977, 201978)),
    60229: ((6, 3), (201979, 201980)),
    1361: ((7, 1), (19506,)),
    SNIPER_TRAINING_ROW: ((7, 2), SNIPER_TRAINING_RANKS),
    1808: ((8, 1), (FALCONS_MARK,)),
    2132: ((8, 2), (53215, 53216, 53217)),
    2134: ((9, 1), (53241, 53243, MFD_R3)),
    2135: ((10, 1), (CHIMERA_SHOT,)),
}
TAB_TALENT_COUNT = 33
TAB_POINTS = 81
CASTABLE_ROWS = frozenset({1345, 60227, 1353, 60228, 1361, 1808, 2135})
MARK_SLA = {30544: SNIPERS_MARK, 30545: VIPERS_MARK, 30546: FALCONS_MARK}
SKILL_LINE_MM = 163
CLASSMASK_HUNTER = 4
TAB_RANKS = tuple(sorted({sid for _, ranks in TAB_LAYOUT.values() for sid in ranks}))
# MM 6.1 / 0-verify 6: every rank the old tab-363 chains (+ 2143) taught that no new chain keeps, 34490 included.
ORPHANS = (19419, 19420, 19430, 19431, 19489, 19490, 34488, 34489, 34490, 34950, 34954, 35100, 35102, 35104, 35110,
           35111, 53221, 53222, 53224, 53228, 53232, 53245, 53246)

# MM 4.1 per mark: school mask, RecoveryTime, SpellLevel, icon
MARK_DATA = {
    SNIPERS_MARK: (SCHOOL_PHYSICAL, 30000, 30, 3524),
    VIPERS_MARK: (SCHOOL_NATURE, 45000, 40, 1630),
    FALCONS_MARK: (SCHOOL_PHYSICAL, 60000, 50, 1530),
}
MARK_FIELDS = {          # common built fields (MM 4.1 + A1)
    "SpellClassSet": SPELLFAMILY_HUNTER, "SpellClassMask_1": 0, "SpellClassMask_2": 0,
    "SpellClassMask_3": D2_MARK_PRESS,
    "DefenseType": DEFENSE_RANGED, "CastingTimeIndex": 18, "StartRecoveryCategory": 133, "StartRecoveryTime": 1500,
    "Speed": 40, "FacingCasterFlags": 1, "EquippedItemClass": 2, "EquippedItemSubclass": 262156, "PreventionType": 2,
    "ManaCostPct": 4, "DispelType": 0, "CumulativeAura": 10, "Attributes": 65538, "ModalNextSpell": 75,
}
MARK_DURATION_MS = 15000

# M1: visible (non-passive, displayed, not consolidated) and hidden-on-purpose S2a rows
VISIBLE = (*MARKS, VIPERS_BITE, VIPERS_VENOM, FIRE, QUICKENING, FALCONS_HASTE, TRICK_SHOTS_BUFF, ROA_BUFF,
           EFFICIENCY_BUFF, PRECISE_SHOTS_BUFF, FALCONS_EDGE, RAPID_KILLING_BUFF_ID, *SNIPER_TRAINING_BUFFS,
           LONE_SURVIVOR_BUFF)
# 201936: the half Volley's caster aura is hidden (S2b A1 question 2, A3 sets Attributes 0x80)
HIDDEN = (AIMED_CRIT_HELPER, CHIMERA_CRIT_HELPER, MASTERY, COMBAT_EXPERIENCE_CAPSTONE, HALF_VOLLEY)
HIDDEN_NO_AURA_ICON = (AIMED_CRIT_HELPER, CHIMERA_CRIT_HELPER)     # A5: Attributes 0x80 + AttributesEx 0x10000000

# MM 2.4, literal (tuples are (d0, d1, d2)); `_masks.py` must hold exactly these
SPEC_MASKS = {
    "AIMED_SHOT_MASK": (0x20000, 0, 0),
    "CHIMERA_SHOT_MASK": (0, 0, 0x1),
    "STEADY_AIMED": (0x20000, 0, 0x20000000),
    "HUNTER_SHOTS": (0x61800, 0x800000, 0x28000001),
    "RWS_SHOTS": (0x61801, 0x800000, 0x28000001),
    "MORTAL_SHOTS_MASK": (0x63800, 0x80800000, 0x78000A41),
    "RAPID_KILLING_BUFF": (0x20800, 0x800000, 0x1),
    "IMPROVED_STINGS_MASK": (0x4000, 0, 0x10000000),
    "VOLLEY_DAMAGE": (0x2000, 0, 0x40000000),
    "BARRAGE_DAMAGE": (0x3000, 0, 0x40000000),
    "WILD_QUIVER_PROC": (0x1, 0, 0x20000000),
}
STEADY_ONLY = (0, 0, D2_STEADY_SHOT)

# (spell ids, 1-based effect, aura, SpellModOp, `_masks.py` composite name or a literal mask)
SPELLMOD_SPECS = (
    ((19426, 19427, 19429), 1, AURA_ADD_FLAT_MODIFIER, OP_CRITICAL_CHANCE, (D0_ARCANE_SHOT, 0, 0)),  # Lethal Shots
    ((19485, 19487, 19488), 1, AURA_ADD_PCT_MODIFIER, OP_CRIT_DAMAGE_BONUS, "MORTAL_SHOTS_MASK"),     # Mortal Shots
    ((19464, 19465, 19466), 1, AURA_ADD_PCT_MODIFIER, OP_DOT, "IMPROVED_STINGS_MASK"),               # Improved Stings
    ((19507, 19508, 19509), 1, AURA_ADD_PCT_MODIFIER, OP_DAMAGE, "RWS_SHOTS"),                       # RWS
    (SNIPER_TRAINING_BUFFS, 1, AURA_ADD_PCT_MODIFIER, OP_DAMAGE, "HUNTER_SHOTS"),                    # Sniper Training
    (SNIPER_TRAINING_BUFFS, 2, AURA_ADD_PCT_MODIFIER, OP_DOT, (0, 0, D2_MARK_DOT)),
    # Marked for Death (eff2: SpellInfoCorrections.cpp:409 rewrites eff0 mask at load)
    ((53241, 53243, MFD_R3), 3, AURA_ADD_PCT_MODIFIER, OP_DAMAGE, (0, 0, D2_MARK_PRESS)),
    ((53241, 53243, MFD_R3), 2, AURA_ADD_PCT_MODIFIER, OP_DOT, (0, 0, D2_MARK_DOT)),
    ((MASTERY,), 1, AURA_ADD_PCT_MODIFIER, OP_DAMAGE, (0, 0, D2_MARK_PRESS)),                       # 201951
    ((MASTERY,), 2, AURA_ADD_PCT_MODIFIER, OP_DOT, (0, 0, D2_MARK_DOT)),
    ((AIMED_CRIT_HELPER,), 1, AURA_ADD_FLAT_MODIFIER, OP_CRITICAL_CHANCE, "AIMED_SHOT_MASK"),        # 201948
    ((AIMED_CRIT_HELPER,), 2, AURA_ADD_PCT_MODIFIER, OP_CRIT_DAMAGE_BONUS, "AIMED_SHOT_MASK"),
    ((CHIMERA_CRIT_HELPER,), 1, AURA_ADD_FLAT_MODIFIER, OP_CRITICAL_CHANCE, "CHIMERA_SHOT_MASK"),    # 201949
    ((CHIMERA_CRIT_HELPER,), 2, AURA_ADD_PCT_MODIFIER, OP_CRIT_DAMAGE_BONUS, "CHIMERA_SHOT_MASK"),
    ((FIRE,), 1, AURA_ADD_PCT_MODIFIER, OP_CASTING_TIME, "AIMED_SHOT_MASK"),                         # Fire!
    ((FIRE,), 2, AURA_ADD_PCT_MODIFIER, OP_COST, "AIMED_SHOT_MASK"),
    ((EFFICIENCY_BUFF,), 1, AURA_ADD_PCT_MODIFIER, OP_CASTING_TIME, "STEADY_AIMED"),                 # 201945
    ((EFFICIENCY_BUFF,), 2, AURA_ADD_PCT_MODIFIER, OP_GLOBAL_COOLDOWN, "STEADY_AIMED"),
    ((PRECISE_SHOTS_BUFF,), 1, AURA_ADD_PCT_MODIFIER, OP_DAMAGE, STEADY_ONLY),                       # 201946
    ((RAPID_KILLING_BUFF_ID,), 1, AURA_ADD_PCT_MODIFIER, OP_DAMAGE, "RAPID_KILLING_BUFF"),           # 35098
    ((201966, 201967, 201968), 1, AURA_ADD_PCT_MODIFIER, OP_DAMAGE, "AIMED_SHOT_MASK"),              # Improved Aimed
    ((201969, 201970, 201971), 1, AURA_ADD_FLAT_MODIFIER, OP_CRITICAL_CHANCE, "AIMED_SHOT_MASK"),    # Deadeye
    ((19454, 19455, 19456), 1, AURA_ADD_PCT_MODIFIER, OP_DAMAGE, STEADY_ONLY),                       # Precise Shots
)
# Effects MM 6 turns to `None` (no effect left, no mask left): (ids, 1-based effect)
REMOVED_EFFECTS = (
    ((19485, 19487, 19488), 2),                      # Mortal Shots eff1 (Serpent Sting)
    ((19464, 19465, 19466), 2), ((19464, 19465, 19466), 3),     # Improved Stings eff1 / eff2
    (SNIPER_TRAINING_RANKS, 2),                      # Sniper Training eff1 (Kill Shot crit)
    ((34485, 34486, 34487), 2),                      # Master Marksman eff1
)
# Charged buffs (ProcCharges) and their CAST consumption rows (MM 5.8-5.10, 8; A14)
CHARGED_BUFFS = {
    FIRE: (1, (0x20000, 0, 0)),
    EFFICIENCY_BUFF: (2, (0x20000, 0, 0x20000000)),
    PRECISE_SHOTS_BUFF: (2, (0, 0, 0x20000000)),
    RAPID_KILLING_BUFF_ID: (2, (0x20800, 0x800000, 0x1)),
}
# MM 8 rows: key -> expected columns (only the ones the spec fixes)
PROC_ROWS = {
    -34485: {"ProcFlags": 0x100, "SpellFamilyName": 9, "mask": (0, 0, 0x20000000), "SpellPhaseMask": PROC_PHASE_CAST},
    -53215: {"ProcFlags": 0x140, "SpellFamilyName": 9, "mask": (0x1, 0, 0x20000000), "SpellTypeMask": 1,
             "SpellPhaseMask": PROC_PHASE_HIT},
    -53234: {"ProcFlags": 0x100, "SpellFamilyName": 9, "mask": (0x20000, 0, 0x20000000), "SpellTypeMask": 1,
             "SpellPhaseMask": PROC_PHASE_HIT, "HitMask": PROC_HIT_CRITICAL},
    PRECISION_R3: {"ProcFlags": 0x100, "SpellFamilyName": 9, "SpellTypeMask": 1, "SpellPhaseMask": PROC_PHASE_HIT,
                   "HitMask": PROC_HIT_CRITICAL, "Chance": 100.0, "DisableEffectsMask": 0x1},
    RAPID_KILLING_R3: {"ProcFlags": PROC_FLAG_KILL, "AttributesMask": PROC_ATTR_REQ_EXP_OR_HONOR, "Chance": 100.0,
                       "DisableEffectsMask": 0x3},
    # S2b B6: Barrage r3, non-triggered Multi-Shot CAST (no 0x2), the DBC 25% (chance 0), 10 s ICD, eff0 never procs
    BARRAGE_R3: {"ProcFlags": PROC_FLAG_DONE_SPELL_RANGED, "SpellFamilyName": 9, "mask": (D0_MULTI_SHOT, 0, 0),
                 "SpellPhaseMask": PROC_PHASE_CAST, "Cooldown": 10000, "DisableEffectsMask": 0x1,
                 "AttributesMask": 0, "Chance": 0.0},
}
# M15: ranks whose non-zero DBC ProcTypeMask has no spell_proc row on purpose. Empty since S2b gave Barrage r3 its row
# (A18's interim default entry is gone).
M15_ACCEPTED = frozenset()

# (m) the brief's bindings (positive keys) and exact stock unbinds
S2A_SCRIPT_BINDINGS = {
    "spell_hun_mark": frozenset(MARKS),
    "spell_hun_aimed_shot_mm": frozenset({AIMED_SHOT}),
    "spell_hun_chimera_shot_mm": frozenset({CHIMERA_SHOT}),
    "spell_hun_arcane_shot_mm": frozenset({ARCANE_SHOT, ARCANE_SHOT_FREE}),
    "spell_hun_steady_shot_mm": frozenset({STEADY_SHOT}),
    "spell_hun_precision_capstone": frozenset({PRECISION_R3}),
    "spell_hun_rapid_killing_capstone": frozenset({RAPID_KILLING_R3}),
    "spell_hun_mm_mastery": frozenset({MASTERY}),
    "spell_hun_piercing_shots_mm": frozenset({53234, 53237, 53238}),
}
S2B_SCRIPT_BINDINGS = {
    "spell_hun_multi_shot_mm": frozenset({MULTI_SHOT}),
    "spell_hun_aimed_shot_ricochet": frozenset({RICOCHET}),
    "spell_hun_convergence": frozenset({CONVERGENCE}),
    "spell_hun_volley_mm": frozenset({VOLLEY}),
    "spell_hun_barrage_capstone": frozenset({BARRAGE_R3}),
    "spell_hun_half_volley_aura": frozenset({HALF_VOLLEY}),
    "spell_hun_half_volley_tick": frozenset({HALF_VOLLEY_TICK}),
    "spell_hun_lone_survivor": frozenset(LONE_SURVIVOR_RANKS),
    "spell_hun_combat_experience_capstone": frozenset({COMBAT_EXPERIENCE_CAPSTONE}),
}
SCRIPT_BINDINGS = {**S2A_SCRIPT_BINDINGS, **S2B_SCRIPT_BINDINGS}
S2A_UNBINDS = {(CHIMERA_SHOT, "spell_hun_chimera_shot"), (-53234, "spell_hun_piercing_shots")}
UNSCRIPTED_S2B_IDS = frozenset({BOUNCE, LONE_SURVIVOR_BUFF})        # B2: the bounce has no script; 201950 is set by B7
KEPT_STOCK_BINDING = (-VOLLEY_TICK, "spell_hun_volley_trigger")     # stays bound (no unbind, B5)
FREE_ARCANE_SHOT_SCRIPTS = frozenset({"spell_hun_shot_mana", "spell_hun_arcane_shot_mm"})
MASTERY_LINK = (MFD_R3, MASTERY, 2)
COMBAT_EXPERIENCE_LINK = (COMBAT_EXPERIENCE_R3, COMBAT_EXPERIENCE_CAPSTONE, 2)
LINKS = (MASTERY_LINK, COMBAT_EXPERIENCE_LINK)

# (n) the pack shots: built fields fixed by B2
PACK_SHOT_FIELDS = {
    "SpellClassSet": SPELLFAMILY_HUNTER, "SpellClassMask_1": D0_AIMED_SHOT, "SpellClassMask_2": 0,
    "SpellClassMask_3": 0, "CastingTimeIndex": 18, "EquippedItemClass": -1, "DefenseType": DEFENSE_RANGED,
    "SchoolMask": SCHOOL_PHYSICAL, "SpellLevel": 20, "SpellIconID": 253, "Category": 0, "RecoveryTime": 0,
    "CategoryRecoveryTime": 0, "ManaCost": 0, "ManaCostPct": 0,
    "Effect_1": EFFECT_NORMALIZED_WEAPON_DMG, "EffectBasePoints_1": -1, "ImplicitTargetA_1": 6,
    "Effect_2": EFFECT_WEAPON_PERCENT_DAMAGE, "ImplicitTargetA_2": 6, "Effect_3": 0,
}
PACK_SHOT_WEAPON_POTENCY = 110           # B2 literal: half of Aimed Shot's 220 today
# (o) the half Volley
HALF_VOLLEY_DURATION_MS, HALF_VOLLEY_AMPLITUDE_MS, HALF_VOLLEY_TICKS = 3000, 1000, 3
HALF_VOLLEY_AP_POTENCY, HALF_VOLLEY_TIME_BASIS_S = 75.5, 1.5
HALF_VOLLEY_TICK_EX3 = ATTR_EX3_IGNORE_CASTER_MODIFIERS | ATTR_EX3_SUPPRESS_CASTER_PROCS     # 0x20010000
# (s) learnable-spell sources: hunter talent tabs (BM 361, SV 362, MM 363), the hunter class skill lines whose
# class-mask-0 rows still belong to the hunter, the SLA auto-learn methods (1 on skill value, 2 on skill learn)
HUNTER_TALENT_TABS = frozenset({361, 362, 363})
HUNTER_SKILL_LINES = frozenset({50, 51, 163})
SLA_AUTO_LEARN = frozenset({1, 2})
# (t) Multi-Shot 2643 as it stands (B1 "data unchanged"; index 1 = the stock hidden 0.5 s ranged-slot cast, an open
# question for the user, 0-verify 4a: change this pin only together with that ruling)
MULTI_SHOT_FIELDS = {
    "SpellClassSet": SPELLFAMILY_HUNTER, "SpellClassMask_1": D0_MULTI_SHOT, "SpellClassMask_2": 0,
    "SpellClassMask_3": 0, "CastingTimeIndex": 1, "EquippedItemClass": 2, "Category": 85,
    "CategoryRecoveryTime": 10000, "Effect_1": EFFECT_NORMALIZED_WEAPON_DMG, "ImplicitTargetA_1": 6,
    "EffectChainTargets_1": 3, "Effect_2": 0, "Effect_3": 0, "DefenseType": DEFENSE_RANGED,
}
# (u) the S2b review fixes
IGNORE_LOS_IDS = (RICOCHET, BOUNCE, CONVERGENCE)                  # R-cpp m-1: the pack is defined around the primary
CANNOT_BE_SAVED_S2B_IDS = (LONE_SURVIVOR_BUFF, HALF_VOLLEY)       # non-passive script-driven auras (B7, R-cpp m-4)


# ---- helpers ---------------------------------------------------------------------------------------------------------

def _u32(value) -> int:
    return int(value or 0) & 0xFFFFFFFF


def _i(row: dict, key: str) -> int:
    return int(row.get(key) or 0)


def effect_mask(row: dict, effect: int) -> tuple[int, int, int]:
    """Effect `effect` (1-based): letter = effect index, number = dword (README Gotcha)."""
    return tuple(_u32(row.get(f"EffectSpellClassMask{LETTERS[effect - 1]}_{n}")) for n in (1, 2, 3))


def spell_mask(row: dict) -> tuple[int, int, int]:
    return tuple(_u32(row.get(f"SpellClassMask_{n}")) for n in (1, 2, 3))


def proc_mask(proc: dict) -> tuple[int, int, int]:
    return tuple(_u32(proc.get(f"SpellFamilyMask{n}")) for n in (0, 1, 2))


def _hex(mask) -> str:
    return "(" + ", ".join(f"0x{w:X}" for w in mask) + ")"


def live_cast_ms(row: dict, cast_times: dict[int, int]) -> int:
    """SpellInfo::CalcCastTime before mods: the SpellCastTimes Base, + 500 ms for a USES_RANGED_SLOT spell, clamped at
    0 (index 18 = -1,000,000 stays 0); a missing entry (index 0) is 0."""
    index = _i(row, "CastingTimeIndex")
    if index not in cast_times:
        return 0
    cast = cast_times[index]
    if _i(row, "Attributes") & ATTR_USES_RANGED_SLOT:
        cast += RANGED_SLOT_ADD_MS
    return max(cast, 0)


def load_masks_module():
    """`source/classes/hunter/_masks.py` as a plain module (it has no imports)."""
    spec = importlib.util.spec_from_file_location("_hunter_masks_under_test", MASKS_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def resolve_mask(masks, ref) -> tuple[int, int, int]:
    return tuple(getattr(masks, ref)) if isinstance(ref, str) else tuple(ref)


# ---- (a) / (b) the tab -----------------------------------------------------------------------------------------------

def check_tab_363(talents: list[dict], built_talents: list[dict], sla_entries: list[dict],
                  trainer_spells: list[dict]) -> list[str]:
    """(a) MM 2.2 / 6.1: 33 talents, 81 points, exact cells and rank lists, one talent per cell, no prerequisite, 2143
    on 363 only, castable rows flagged, the mark SLA rows, no trainer row for a mark."""
    bad = []
    mine = [t for t in talents if t.get("tab_id") == TAB]
    if len(mine) != TAB_TALENT_COUNT:
        bad.append(f"tab {TAB} has {len(mine)} talents, expected {TAB_TALENT_COUNT}")
    ids = {int(t["id"]) for t in mine}
    if ids != set(TAB_LAYOUT):
        bad.append(f"tab {TAB} talent ids differ: unexpected {sorted(ids - set(TAB_LAYOUT))}, "
                   f"missing {sorted(set(TAB_LAYOUT) - ids)}")
    points = sum(len(t.get("rank_spell_ids") or []) for t in mine)
    if points != TAB_POINTS:
        bad.append(f"tab {TAB} totals {points} points, expected {TAB_POINTS}")
    cells: dict[tuple[int, int], list[int]] = {}
    for t in mine:
        tid, cell = int(t["id"]), (int(t["tier"]), int(t["column"]))
        cells.setdefault(cell, []).append(tid)
        want = TAB_LAYOUT.get(tid)
        if want is not None:
            if cell != want[0]:
                bad.append(f"talent {tid} at {cell}, expected {want[0]}")
            if tuple(int(s) for s in t.get("rank_spell_ids") or []) != want[1]:
                bad.append(f"talent {tid} ranks {t.get('rank_spell_ids')}, expected {list(want[1])}")
        if t.get("depends_on"):
            bad.append(f"talent {tid}: depends_on {t['depends_on']} (no prerequisite arrows, D7)")
        for key in (t.get("raw_overrides") or {}):
            if str(key).startswith(("PrereqTalent", "PrereqRank")):
                bad.append(f"talent {tid}: raw override {key}")
        if tid in CASTABLE_ROWS and not int(t.get("flags") or 0) & 1:
            bad.append(f"talent {tid}: castable-teaching row without flags=1")
    for cell, talent_ids in sorted(cells.items()):
        if len(talent_ids) > 1:
            bad.append(f"cell {cell} holds talents {talent_ids}")
    others = [t for t in talents if int(t["id"]) == SNIPER_TRAINING_ROW and t.get("tab_id") != TAB]
    if others:
        bad.append(f"talent {SNIPER_TRAINING_ROW} also declared on tab(s) {[t.get('tab_id') for t in others]}")
    for row in built_talents:
        if _i(row, "TabID") != TAB:
            if _i(row, "ID") == SNIPER_TRAINING_ROW:
                bad.append(f"talent {SNIPER_TRAINING_ROW}: built TabID {row.get('TabID')}, expected {TAB}")
            continue
        for n in (1, 2, 3):
            if _i(row, f"PrereqTalent_{n}"):
                bad.append(f"talent {row['ID']}: built PrereqTalent_{n} {row.get(f'PrereqTalent_{n}')}")
        if _i(row, "ID") == SNIPER_TRAINING_ROW and (_i(row, "TierID"), _i(row, "ColumnIndex")) != (7, 2):
            bad.append(f"talent {SNIPER_TRAINING_ROW}: built cell {(row.get('TierID'), row.get('ColumnIndex'))}, "
                       f"expected (7, 2)")
    if not any(_i(r, "ID") == SNIPER_TRAINING_ROW and _i(r, "TabID") == TAB for r in built_talents):
        bad.append(f"talent {SNIPER_TRAINING_ROW}: no built row on tab {TAB}")
    sla = {int(e["id"]): e for e in sla_entries}
    for sla_id, spell_id in MARK_SLA.items():
        e = sla.get(sla_id)
        got = None if e is None else (int(e["spell_id"]), int(e["skill_line"]), int(e.get("class_mask") or 0))
        if got != (spell_id, SKILL_LINE_MM, CLASSMASK_HUNTER):
            bad.append(f"SkillLineAbility {sla_id}: (spell, skill line, class mask) {got}, "
                       f"expected {(spell_id, SKILL_LINE_MM, CLASSMASK_HUNTER)}")
    for t in trainer_spells:
        if int(t.get("SpellId") or t.get("spell_id") or 0) in MARKS:
            bad.append(f"trainer row for mark {t.get('SpellId') or t.get('spell_id')} (L13: talent spells get none)")
    return bad


def check_orphans(talent_rows: list[dict], orphans=ORPHANS) -> list[str]:
    """(b) no talent row of the overlay (stock Talent.dbc + the package's built rows) teaches an orphaned rank."""
    wanted = set(orphans)
    bad = []
    for row in talent_rows:
        for n in range(1, 10):
            sid = _i(row, f"SpellRank_{n}")
            if sid in wanted:
                bad.append(f"talent {row.get('ID')} (tab {row.get('TabID')}) still teaches orphaned rank {sid}")
    return bad


# ---- (c) marks -------------------------------------------------------------------------------------------------------

def check_mark(spell_id: int, row: dict | None, cast_times: dict[int, int], duration_index: int) -> list[str]:
    """(c) one mark, MM 4.1 + A1 + stale line 2."""
    if row is None:
        return [f"{spell_id}: not declared"]
    bad = []
    for key, want in MARK_FIELDS.items():
        if _i(row, key) != want:
            bad.append(f"{key} {row.get(key)}, expected {want}")
    if live_cast_ms(row, cast_times) != 0:
        bad.append(f"live cast {live_cast_ms(row, cast_times)} ms, expected 0 (a hidden ranged-slot cast)")
    school, recovery, level, icon = MARK_DATA[spell_id]
    for key, want in (("SchoolMask", school), ("RecoveryTime", recovery), ("SpellLevel", level),
                      ("SpellIconID", icon), ("DurationIndex", duration_index)):
        if _i(row, key) != want:
            bad.append(f"{key} {row.get(key)}, expected {want}")
    shapes = ((1, EFFECT_NORMALIZED_WEAPON_DMG, 0), (2, EFFECT_WEAPON_PERCENT_DAMAGE, 0),
              (3, EFFECT_APPLY_AURA, AURA_DUMMY))
    for index, effect, aura in shapes:
        if (_i(row, f"Effect_{index}"), _i(row, f"EffectAura_{index}")) != (effect, aura):
            bad.append(f"eff{index - 1} is {row.get(f'Effect_{index}')}/{row.get(f'EffectAura_{index}')}, "
                       f"expected {effect}/{aura}")
        if _i(row, f"ImplicitTargetA_{index}") != 6:
            bad.append(f"eff{index - 1} target {row.get(f'ImplicitTargetA_{index}')}, expected 6")
    if _i(row, "EffectBasePoints_3") != -1:
        bad.append(f"eff2 (the mark) stored base points {row.get('EffectBasePoints_3')}, expected -1 (amount 0)")
    if _i(row, "EffectBasePoints_1") != -1:
        bad.append(f"eff0 stored base points {row.get('EffectBasePoints_1')}, expected -1")
    return [f"{spell_id}: {b}" for b in bad]


# ---- (d) Aimed Shot --------------------------------------------------------------------------------------------------

def check_aimed_shot(row: dict | None, entry: dict | None, cast_times: dict[int, int], categories: list[dict],
                     bonus_rows: list[dict], corrections: list[dict]) -> list[str]:
    """(d) A6 + stale line 1 + M3."""
    if row is None or entry is None:
        return [f"{AIMED_SHOT}: not declared"]
    bad = []
    if live_cast_ms(row, cast_times) != 2000:
        bad.append(f"live cast {live_cast_ms(row, cast_times)} ms (index {row.get('CastingTimeIndex')}), "
                   f"expected 2000 (index 16 = 1500 + 500)")
    if _i(row, "CastingTimeIndex") != 16:
        bad.append(f"CastingTimeIndex {row.get('CastingTimeIndex')}, expected 16")
    if entry.get("cast_time_ms") != 1500:
        bad.append(f"cast_time_ms {entry.get('cast_time_ms')}, expected 1500")
    if _i(row, "Category") != 1301:
        bad.append(f"Category {row.get('Category')}, expected 1301")
    if not any(int(c["id"]) == 1301 for c in categories):
        bad.append("spell_category(1301) not declared")
    if _i(row, "CategoryRecoveryTime") != 10000 or _i(row, "RecoveryTime") != 0:
        bad.append(f"cooldowns RecoveryTime {row.get('RecoveryTime')} / CategoryRecoveryTime "
                   f"{row.get('CategoryRecoveryTime')}, expected 0 / 10000 (no second cooldown, SHARED B14)")
    if spell_mask(row) != (D0_AIMED_SHOT, 0, 0):
        bad.append(f"SpellClassMask {_hex(spell_mask(row))}, expected (0x20000, 0x0, 0x0) (d0 b17 kept)")
    if _i(row, "EquippedItemClass") != 2:
        bad.append(f"EquippedItemClass {row.get('EquippedItemClass')}, expected 2 (player-cast shot)")
    for n in (1, 2, 3):
        effect = entry.get(f"effect{n}") or {}
        potency = effect.get("_potency") or {}
        if potency.get("ap_coefficient") or potency.get("sp_coefficient"):
            bad.append(f"effect {n} carries ap/sp potency {potency.get('ap_coefficient')}/"
                       f"{potency.get('sp_coefficient')} (M3: none on 19434, or it needs time_basis_ms=2000)")
    if any(int(b["entry"]) == AIMED_SHOT for b in bonus_rows):
        bad.append("has a spell_bonus_data row (an ap/sp potency effect)")
    if any(int(c["spell_id"]) == AIMED_SHOT for c in corrections):
        bad.append("has a spell_potency_correction row (a non-weapon potency effect)")
    if (_i(row, "Effect_1"), _i(row, "EffectBasePoints_1")) != (EFFECT_NORMALIZED_WEAPON_DMG, -1) \
            or float(row.get("EffectRealPointsPerLevel_1") or 0):
        bad.append(f"eff0 {row.get('Effect_1')} bp {row.get('EffectBasePoints_1')} ppl "
                   f"{row.get('EffectRealPointsPerLevel_1')}, expected NORMALIZED_WEAPON_DMG bp -1 ppl 0")
    if _i(row, "Effect_2") != EFFECT_WEAPON_PERCENT_DAMAGE:
        bad.append(f"eff1 type {row.get('Effect_2')}, expected WEAPON_PERCENT_DAMAGE (healing debuff dropped)")
    if _i(row, "InterruptFlags") != 15 or _i(row, "SpellLevel") != 20 or _i(row, "MaxLevel"):
        bad.append(f"InterruptFlags {row.get('InterruptFlags')} SpellLevel {row.get('SpellLevel')} MaxLevel "
                   f"{row.get('MaxLevel')}, expected 15 / 20 / 0")
    return [f"{AIMED_SHOT}: {b}" for b in bad]


# ---- (e) the free Arcane Shot ----------------------------------------------------------------------------------------

EFFECT_COLUMNS = ("Effect", "EffectAura", "EffectBasePoints", "EffectDieSides", "EffectMiscValue",
                  "EffectRealPointsPerLevel")


BONUS_COLUMNS = ("direct_bonus", "dot_bonus", "ap_bonus", "ap_dot_bonus")


def check_free_arcane_shot(row: dict | None, arcane: dict | None, bound: list[dict],
                           bonus_rows: list[dict]) -> list[str]:
    """(e) A9 + stale line 3: 201933's eff1 equals 3044's built eff1 column by column (the mana restore of
    spell_hun_shot_mana reads it: a literal that drifts from 3044 is a finding), index 18, class -1, d0 b11 only,
    no cost / category / cooldown, SUPPRESS_CASTER_PROCS, the two scripts and not BM's Stomp class.
    S2a review m-1: the damage is a copy too (`ap_potency=130.0` literal), so eff0 and the spell_bonus_data row must
    equal 3044's as well."""
    if row is None or arcane is None:
        return [f"{ARCANE_SHOT_FREE}/{ARCANE_SHOT}: not declared"]
    bad = []
    for col in EFFECT_COLUMNS:
        if float(row.get(f"{col}_2") or 0) != float(arcane.get(f"{col}_2") or 0):
            bad.append(f"eff1 {col} {row.get(f'{col}_2')} differs from Arcane Shot's {arcane.get(f'{col}_2')}")
        if float(row.get(f"{col}_1") or 0) != float(arcane.get(f"{col}_1") or 0):
            bad.append(f"eff0 {col} {row.get(f'{col}_1')} differs from Arcane Shot's {arcane.get(f'{col}_1')} "
                       f"(m-1: the damage is copied as a literal)")
    bonus = {int(b["entry"]): b for b in bonus_rows}
    mine, theirs = bonus.get(ARCANE_SHOT_FREE), bonus.get(ARCANE_SHOT)
    if mine is None or theirs is None:
        bad.append(f"spell_bonus_data: free {'present' if mine else 'missing'}, Arcane Shot "
                   f"{'present' if theirs else 'missing'} (m-1: both carry the ap potency)")
    else:
        for col in BONUS_COLUMNS:
            if float(mine.get(col) or 0) != float(theirs.get(col) or 0):
                bad.append(f"spell_bonus_data {col} {mine.get(col)} differs from Arcane Shot's {theirs.get(col)} "
                           f"(m-1)")
    if _i(row, "Effect_2") != EFFECT_DUMMY:
        bad.append(f"eff1 type {row.get('Effect_2')}, expected DUMMY (the mana percent)")
    for key, want in (("CastingTimeIndex", 18), ("EquippedItemClass", -1), ("SpellClassSet", SPELLFAMILY_HUNTER),
                      ("Category", 0), ("RecoveryTime", 0), ("CategoryRecoveryTime", 0), ("ManaCost", 0),
                      ("ManaCostPct", 0), ("SchoolMask", SCHOOL_ARCANE), ("DefenseType", DEFENSE_RANGED),
                      ("Effect_1", EFFECT_SCHOOL_DAMAGE)):
        if _i(row, key) != want:
            bad.append(f"{key} {row.get(key)}, expected {want}")
    if spell_mask(row) != (D0_ARCANE_SHOT, 0, 0):
        bad.append(f"SpellClassMask {_hex(spell_mask(row))}, expected (0x800, 0x0, 0x0) (d0 b11 only)")
    if not _i(row, "AttributesEx3") & ATTR_EX3_SUPPRESS_CASTER_PROCS:
        bad.append(f"AttributesEx3 0x{_i(row, 'AttributesEx3'):X} lacks SUPPRESS_CASTER_PROCS (0x10000)")
    names = {r["ScriptName"] for r in bound if int(r["spell_id"]) == ARCANE_SHOT_FREE}
    if names != FREE_ARCANE_SHOT_SCRIPTS:
        bad.append(f"bound to {sorted(names)}, expected {sorted(FREE_ARCANE_SHOT_SCRIPTS)}")
    return [f"{ARCANE_SHOT_FREE}: {b}" for b in bad]


# ---- (f) M1 visibility -----------------------------------------------------------------------------------------------

def check_visibility(rows_by_id: dict[int, dict], visible=VISIBLE, hidden=HIDDEN,
                     hidden_no_icon=HIDDEN_NO_AURA_ICON) -> list[str]:
    bad = []
    for spell_id in visible:
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
            continue
        if _i(row, "Attributes") & ATTR_PASSIVE:
            bad.append(f"{spell_id}: passive (0x40), never sent to the client")
        if _i(row, "Attributes") & ATTR_DO_NOT_DISPLAY:
            bad.append(f"{spell_id}: Attributes DO_NOT_DISPLAY (0x80)")
        if _i(row, "AttributesEx") & ATTR_EX_NO_AURA_ICON:
            bad.append(f"{spell_id}: AttributesEx 0x10000000 (no aura icon)")
        if _i(row, "AttributesEx7") & ATTR_EX7_CONSOLIDATE:
            bad.append(f"{spell_id}: AttributesEx7 0x10000000 (Consolidated Buffs, S1a PT-1)")
    for spell_id in hidden:
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
            continue
        if not _i(row, "Attributes") & ATTR_DO_NOT_DISPLAY:
            bad.append(f"{spell_id}: hidden on purpose but lacks Attributes 0x80")
        if spell_id in hidden_no_icon and not _i(row, "AttributesEx") & ATTR_EX_NO_AURA_ICON:
            bad.append(f"{spell_id}: hidden helper lacks AttributesEx 0x10000000")
    return bad


def check_falcons_haste(row: dict | None, permanent_index: int) -> list[str]:
    """(f) stale line 5 / A4: visible, HASTE_ALL bp -1, permanent, icon 1530, the X8 name."""
    if row is None:
        return [f"{FALCONS_HASTE}: not declared"]
    bad = []
    if (_i(row, "Effect_1"), _i(row, "EffectAura_1"), _i(row, "EffectBasePoints_1")) != (EFFECT_APPLY_AURA,
                                                                                       AURA_HASTE_ALL, -1):
        bad.append(f"eff0 {row.get('Effect_1')}/{row.get('EffectAura_1')} bp {row.get('EffectBasePoints_1')}, "
                   f"expected APPLY_AURA / HASTE_ALL (193) bp -1")
    if _i(row, "DurationIndex") != permanent_index:
        bad.append(f"DurationIndex {row.get('DurationIndex')}, expected {permanent_index} (duration -1)")
    if _i(row, "SpellIconID") != 1530 or row.get("Name_Lang_enUS") != "Falcon's Haste":
        bad.append(f"icon {row.get('SpellIconID')} name {row.get('Name_Lang_enUS')!r}, expected 1530 / Falcon's Haste")
    if _i(row, "AttributesEx7"):
        bad.append(f"AttributesEx7 0x{_i(row, 'AttributesEx7'):X}, expected 0")
    return [f"{FALCONS_HASTE}: {b}" for b in bad]


# ---- (g) M4 ----------------------------------------------------------------------------------------------------------

def check_equipped_item_class(rows_by_id: dict[int, dict], minus_one_ids, class_two_ids) -> list[str]:
    bad = []
    for spell_id in sorted(set(minus_one_ids)):
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
        elif _i(row, "EquippedItemClass") != -1:
            bad.append(f"{spell_id}: built EquippedItemClass {row.get('EquippedItemClass')}, expected -1 (M4)")
    for spell_id in sorted(set(class_two_ids)):
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
        elif _i(row, "EquippedItemClass") != 2:
            bad.append(f"{spell_id}: built EquippedItemClass {row.get('EquippedItemClass')}, expected 2 "
                       f"(player-cast shot)")
    return bad


# ---- (h) family-bit carriers -----------------------------------------------------------------------------------------

def check_family_bit_carriers(rows: list[dict]) -> list[str]:
    """FAMILY-BITS 0.6 + the S2b classmask audit: d0 b17 only on 19434 / 201934 / 201935 and d2 b30 only on 201936
    (any custom id, or a family-9 stock row of the package), no bit on the helpers, buffs, ranks and 201937 / 201950 /
    201952."""
    bad = []
    no_bit = {*range(201940, 201950), MASTERY, CONVERGENCE, *range(201960, 201983), HALF_VOLLEY_TICK,
              LONE_SURVIVOR_BUFF, COMBAT_EXPERIENCE_CAPSTONE}
    for row in rows:
        sid, mask = int(row["ID"]), spell_mask(row)
        ours = sid >= 200000 or _i(row, "SpellClassSet") == SPELLFAMILY_HUNTER
        if mask[2] & D2_MARK_PRESS and sid not in MARKS:
            bad.append(f"{sid}: carries d2 b27 (mark press) but is no mark")
        if mask[2] & D2_MARK_DOT and sid not in (VIPERS_BITE, VIPERS_VENOM):
            bad.append(f"{sid}: carries d2 b28 (mark DoT) but is not 201930 / 201931")
        if sid >= 200000 and mask[0] & D0_ARCANE_SHOT and sid != ARCANE_SHOT_FREE:
            bad.append(f"{sid}: custom id on d0 b11 (only 201933 reuses Arcane Shot's bit)")
        if ours and mask[0] & D0_AIMED_SHOT and sid not in (AIMED_SHOT, *PACK_SHOTS):
            bad.append(f"{sid}: carries d0 b17 (only Aimed Shot 19434 and S2b's ricochet / bounce)")
        if ours and mask[2] & D2_HALF_VOLLEY and sid != HALF_VOLLEY:
            bad.append(f"{sid}: carries d2 b30 (only the half Volley 201936)")
        if sid in PACK_SHOTS and mask != (D0_AIMED_SHOT, 0, 0):
            bad.append(f"{sid}: SpellClassMask {_hex(mask)}, expected (0x20000, 0x0, 0x0)")
        if sid == HALF_VOLLEY and mask != (0, 0, D2_HALF_VOLLEY):
            bad.append(f"{sid}: SpellClassMask {_hex(mask)}, expected (0x0, 0x0, 0x40000000)")
        if sid in no_bit and any(mask):
            bad.append(f"{sid}: SpellClassMask {_hex(mask)}, expected no family bit (FAMILY-BITS 0.6)")
        if sid in MARKS and mask != (0, 0, D2_MARK_PRESS):
            bad.append(f"{sid}: SpellClassMask {_hex(mask)}, expected (0x0, 0x0, 0x8000000)")
        if sid in (VIPERS_BITE, VIPERS_VENOM) and mask != (0, 0, D2_MARK_DOT):
            bad.append(f"{sid}: SpellClassMask {_hex(mask)}, expected (0x0, 0x0, 0x10000000)")
    return bad


# ---- (i) SpellMods ---------------------------------------------------------------------------------------------------

def check_masks_module(masks) -> list[str]:
    bad = []
    for name, want in SPEC_MASKS.items():
        got = getattr(masks, name, None)
        if got is None or tuple(got) != want:
            bad.append(f"_masks.{name} = {got}, expected {_hex(want)} (MM 2.4)")
    return bad


def check_spellmod_specs(rows_by_id: dict[int, dict], masks, specs=SPELLMOD_SPECS) -> list[str]:
    bad = []
    for ids, effect, aura, op, ref in specs:
        want_mask = resolve_mask(masks, ref)
        for spell_id in ids:
            row = rows_by_id.get(spell_id)
            if row is None:
                bad.append(f"{spell_id}: not declared")
                continue
            got = (_i(row, f"Effect_{effect}"), _i(row, f"EffectAura_{effect}"), _i(row, f"EffectMiscValue_{effect}"))
            if got != (EFFECT_APPLY_AURA, aura, op):
                bad.append(f"{spell_id}: eff{effect - 1} {got}, expected APPLY_AURA / aura {aura} / op {op}")
            if _i(row, "SpellClassSet") != SPELLFAMILY_HUNTER:
                bad.append(f"{spell_id}: SpellClassSet {row.get('SpellClassSet')}, expected 9 (M8)")
            if effect_mask(row, effect) != want_mask:
                bad.append(f"{spell_id}: eff{effect - 1} mask {_hex(effect_mask(row, effect))}, expected "
                           f"{_hex(want_mask)}" + (f" ({ref})" if isinstance(ref, str) else ""))
    return bad


def check_removed_effects(rows_by_id: dict[int, dict], removed=REMOVED_EFFECTS) -> list[str]:
    bad = []
    for ids, effect in removed:
        for spell_id in ids:
            row = rows_by_id.get(spell_id)
            if row is None:
                bad.append(f"{spell_id}: not declared")
                continue
            if _i(row, f"Effect_{effect}"):
                bad.append(f"{spell_id}: eff{effect - 1} type {row.get(f'Effect_{effect}')}, expected none")
            if any(effect_mask(row, effect)):
                bad.append(f"{spell_id}: eff{effect - 1} keeps mask {_hex(effect_mask(row, effect))} (stale raw)")
    return bad


def check_sniper_training_ranks(rows_by_id: dict[int, dict]) -> list[str]:
    """MM 6 row (7,2): eff0 PERIODIC_TRIGGER_SPELL with no mask left (stale A_1 0xDE / A_2 0x84000 deleted)."""
    bad = []
    for spell_id in SNIPER_TRAINING_RANKS:
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
            continue
        if _i(row, "EffectAura_1") != AURA_PERIODIC_TRIGGER_SPELL:
            bad.append(f"{spell_id}: eff0 aura {row.get('EffectAura_1')}, expected PERIODIC_TRIGGER_SPELL (23)")
        if any(effect_mask(row, 1)):
            bad.append(f"{spell_id}: eff0 keeps mask {_hex(effect_mask(row, 1))} (stale raw)")
    return bad


def check_chimera_serpent(row: dict | None) -> list[str]:
    if row is None:
        return [f"{CHIMERA_SERPENT}: not declared"]
    if spell_mask(row) != (0, 0, 0x800):
        return [f"{CHIMERA_SERPENT}: SpellClassMask {_hex(spell_mask(row))}, expected (0x0, 0x0, 0x800) (d2 b10 strip)"]
    return []


def check_charged_buffs(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for spell_id, (charges, _mask) in CHARGED_BUFFS.items():
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
            continue
        if _i(row, "ProcCharges") != charges:
            bad.append(f"{spell_id}: ProcCharges {row.get('ProcCharges')}, expected {charges}")
    row = rows_by_id.get(RAPID_KILLING_BUFF_ID)
    if row is not None:
        if _i(row, "ProcTypeMask"):
            bad.append(f"{RAPID_KILLING_BUFF_ID}: ProcTypeMask 0x{_i(row, 'ProcTypeMask'):X}, expected 0 (A14)")
        if _i(row, "EffectBasePoints_1") != 29 or float(row.get("EffectRealPointsPerLevel_1") or 0):
            bad.append(f"{RAPID_KILLING_BUFF_ID}: eff0 bp {row.get('EffectBasePoints_1')} ppl "
                       f"{row.get('EffectRealPointsPerLevel_1')}, expected 29 / 0 (+30%)")
    return bad


def check_no_pet_bit_readers(rows_by_id: dict[int, dict], ids, procs: list[dict]) -> list[str]:
    """(i) no effect mask of an S2a id and no spell_proc family mask keyed on one holds d1 b28 (lint (c))."""
    wanted = set(ids)
    bad = []
    for spell_id in sorted(wanted):
        row = rows_by_id.get(spell_id)
        if row is None:
            continue
        for index in (1, 2, 3):
            if effect_mask(row, index)[1] & D1_PET_BIT:
                bad.append(f"{spell_id}: eff{index - 1} mask {_hex(effect_mask(row, index))} holds d1 b28")
    for proc in procs:
        if abs(int(proc["SpellId"])) in wanted and proc_mask(proc)[1] & D1_PET_BIT:
            bad.append(f"spell_proc {proc['SpellId']}: family mask {_hex(proc_mask(proc))} holds d1 b28")
    return bad


# ---- (j) spell_proc rows ---------------------------------------------------------------------------------------------

def check_proc_rows(procs: list[dict], expected=PROC_ROWS, charged=CHARGED_BUFFS) -> list[str]:
    bad = []
    by_key: dict[int, list[dict]] = {}
    for p in procs:
        by_key.setdefault(int(p["SpellId"]), []).append(p)
    for key in (*expected, *charged):
        rows = by_key.get(key, [])
        twin = key > 0 and -key in by_key
        if len(rows) != 1:
            bad.append(f"spell_proc {key}: declared {len(rows)} times, expected exactly once"
                       + (f" (a {-key} row exists: positive keys, L7)" if twin else ""))
        elif twin:
            bad.append(f"spell_proc {-key}: negative twin of the positive-keyed row {key}")
    for key, cols in expected.items():
        rows = by_key.get(key)
        if not rows:
            continue
        p = rows[0]
        for col, want in cols.items():
            got = proc_mask(p) if col == "mask" else (float(p.get(col) or 0) if col == "Chance" else _i(p, col))
            if got != want:
                bad.append(f"spell_proc {key}: {col} {got if col != 'mask' else _hex(got)}, expected "
                           f"{want if col != 'mask' else _hex(want)}")
    for key, (_charges, mask) in charged.items():
        rows = by_key.get(key)
        if not rows:
            continue
        p = rows[0]
        if _i(p, "AttributesMask") & PROC_ATTR_TRIGGERED_CAN_PROC:
            bad.append(f"spell_proc {key}: AttributesMask 0x{_i(p, 'AttributesMask'):X} holds 0x2 (only non-triggered "
                       f"casts spend a charge, M6)")
        if _i(p, "SpellPhaseMask") != PROC_PHASE_CAST:
            bad.append(f"spell_proc {key}: SpellPhaseMask {p.get('SpellPhaseMask')}, expected CAST 0x1")
        if _i(p, "ProcFlags") != PROC_FLAG_DONE_SPELL_RANGED or _i(p, "SpellFamilyName") != SPELLFAMILY_HUNTER:
            bad.append(f"spell_proc {key}: ProcFlags 0x{_i(p, 'ProcFlags'):X} family {p.get('SpellFamilyName')}, "
                       f"expected 0x100 / 9")
        if proc_mask(p) != mask:
            bad.append(f"spell_proc {key}: mask {_hex(proc_mask(p))}, expected {_hex(mask)}")
    return bad


# ---- (k) M15 + Rapid Killing -----------------------------------------------------------------------------------------

def check_m15(rows_by_id: dict[int, dict], talents: list[dict], procs: list[dict],
              accepted=M15_ACCEPTED) -> list[str]:
    """Every tab-363 rank: a non-zero ProcTypeMask needs a spell_proc row (own id, or -first rank of its chain), and
    no EffectSpellClassMask sits on an absent effect (a stale twin the engine's default proc entry would read)."""
    keys = {int(p["SpellId"]) for p in procs}
    bad = []
    for t in talents:
        if t.get("tab_id") != TAB:
            continue
        ranks = [int(s) for s in t.get("rank_spell_ids") or []]
        for spell_id in ranks:
            row = rows_by_id.get(spell_id)
            if row is None:
                bad.append(f"{spell_id}: not declared")
                continue
            if _i(row, "ProcTypeMask") and spell_id not in accepted \
                    and spell_id not in keys and -ranks[0] not in keys:
                bad.append(f"{spell_id}: ProcTypeMask 0x{_i(row, 'ProcTypeMask'):X} with no spell_proc row "
                           f"({spell_id} / -{ranks[0]}): the default entry reads stale masks (M15)")
            for index in (1, 2, 3):
                if not _i(row, f"Effect_{index}") and any(effect_mask(row, index)):
                    bad.append(f"{spell_id}: mask {_hex(effect_mask(row, index))} on absent eff{index - 1}")
    return bad


def check_rapid_killing(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for spell_id in (34948, 34949, RAPID_KILLING_R3):
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
            continue
        if (_i(row, "Effect_1"), _i(row, "EffectAura_1"), _i(row, "EffectTriggerSpell_1")) != (EFFECT_APPLY_AURA,
                                                                                          AURA_DUMMY, 0):
            bad.append(f"{spell_id}: eff0 {row.get('Effect_1')}/{row.get('EffectAura_1')} trigger "
                       f"{row.get('EffectTriggerSpell_1')}, expected APPLY_AURA / DUMMY / 0 (execute clause)")
        if spell_id != RAPID_KILLING_R3 and _i(row, "ProcTypeMask"):
            bad.append(f"{spell_id}: ProcTypeMask 0x{_i(row, 'ProcTypeMask'):X}, expected 0")
        if effect_mask(row, 2) != (0x20, 0, 0):
            bad.append(f"{spell_id}: eff1 mask {_hex(effect_mask(row, 2))}, expected (0x20, 0x0, 0x0) (Rapid Fire)")
    row = rows_by_id.get(RAPID_KILLING_R3)
    if row is not None:
        got = (_i(row, "EffectAura_3"), _i(row, "EffectTriggerSpell_3"), _i(row, "ProcTypeMask"), _i(row, "ProcChance"))
        if got != (AURA_PROC_TRIGGER_SPELL, RAPID_KILLING_BUFF_ID, PROC_FLAG_KILL, 100):
            bad.append(f"{RAPID_KILLING_R3}: eff2 aura / trigger / ProcTypeMask / ProcChance {got}, "
                       f"expected (42, 35098, 0x2, 100)")
    return bad


# ---- (l) / (m) -------------------------------------------------------------------------------------------------------

def check_stampede_family(row: dict | None) -> list[str]:
    if row is None:
        return [f"{STAMPEDE}: not declared"]
    if _i(row, "SpellClassSet") != 0:
        return [f"{STAMPEDE}: SpellClassSet {row.get('SpellClassSet')}, expected 0 (stock Readiness must not reset it; "
                f"family 9 needs the Readiness rebind back, A19)"]
    return []


def check_bindings(bound: list[dict], removals: list[dict], linked: list[dict],
                   expected=SCRIPT_BINDINGS, unbinds=S2A_UNBINDS, links=LINKS) -> list[str]:
    """(m) + (q): every brief class on exactly its positive keys, the exact stock unbinds, Readiness untouched, the
    bounce and the Lone Survivor buff unscripted, stock -42243 spell_hun_volley_trigger not unbound, the two type-2
    links."""
    bad = []
    for name, ids in expected.items():
        have = {int(r["spell_id"]) for r in bound if r["ScriptName"] == name}
        if have != set(ids):
            bad.append(f"{name}: bound to {sorted(have)}, expected {sorted(ids)} (positive keys, L7)")
    got_unbinds = {(int(r["spell_id"]), r["ScriptName"]) for r in removals}
    for key in sorted(unbinds):
        if key not in got_unbinds:
            bad.append(f"unbind_script{key} not declared")
    for spell_id, name in got_unbinds:
        if name in ("spell_hun_readiness", "spell_hun_readiness_rework"):
            bad.append(f"unbind_script({spell_id}, {name}): Readiness keeps the stock binding (stale line 4)")
    if KEPT_STOCK_BINDING in got_unbinds:
        bad.append(f"unbind_script{KEPT_STOCK_BINDING}: the stock Volley trigger stays bound (B5)")
    if any(r["ScriptName"] == "spell_hun_readiness_rework" for r in bound):
        bad.append("spell_hun_readiness_rework bound (dropped by stale line 4)")
    for r in bound:
        if abs(int(r["spell_id"])) in UNSCRIPTED_S2B_IDS:
            bad.append(f"{r['spell_id']} bound to {r['ScriptName']} (B2 / B7: no script on 201935 / 201950)")
    have = {(int(r["spell_trigger"]), int(r["spell_effect"]), int(r["type"])) for r in linked}
    for link in links:
        if link not in have:
            bad.append(f"linked_spell{link} not declared")
    return bad


# ---- (n) the ricochet / bounce ---------------------------------------------------------------------------------------

def live_weapon_potency(row: dict, effect: int) -> int:
    """A WEAPON_PERCENT_DAMAGE effect's live percent: stored base points + 1 (die sides 1), stored = live - 1."""
    return _i(row, f"EffectBasePoints_{effect}") + (1 if _i(row, f"EffectDieSides_{effect}") >= 1 else 0)


def check_pack_shots(rows_by_id: dict[int, dict], pack_pct) -> list[str]:
    """(n) B2 on both built rows: the PACK_SHOT_FIELDS, Speed 0, SUPPRESS_CASTER_PROCS, and eff1's live weapon potency
    = pack_pct % of Aimed Shot 19434's built eff1 (A1 computes it from a private copy of 220: a retune of Aimed Shot
    that leaves the copy behind fails here) and = 110 today (B2)."""
    aimed = rows_by_id.get(AIMED_SHOT)
    if aimed is None:
        return [f"{AIMED_SHOT}: not declared"]
    if pack_pct is None:
        return ["const PACK_SHOT_DAMAGE_PCT not declared"]
    aimed_potency = live_weapon_potency(aimed, 2)
    want_potency = aimed_potency * int(pack_pct) // 100
    bad = []
    if want_potency != PACK_SHOT_WEAPON_POTENCY:
        bad.append(f"{pack_pct}% of Aimed Shot's {aimed_potency} is {want_potency}, B2 says "
                   f"{PACK_SHOT_WEAPON_POTENCY} (update the B2 literal with the ruling)")
    for spell_id in PACK_SHOTS:
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
            continue
        for key, want in PACK_SHOT_FIELDS.items():
            if _i(row, key) != want:
                bad.append(f"{spell_id}: {key} {row.get(key)}, expected {want}")
        if float(row.get("Speed") or 0) != 0.0:
            bad.append(f"{spell_id}: Speed {row.get('Speed')}, expected 0 (launch and hit inside the CastSpell)")
        if not _i(row, "AttributesEx3") & ATTR_EX3_SUPPRESS_CASTER_PROCS:
            bad.append(f"{spell_id}: AttributesEx3 0x{_i(row, 'AttributesEx3'):X} lacks SUPPRESS_CASTER_PROCS "
                       f"(0x10000)")
        if live_weapon_potency(row, 2) != want_potency:
            bad.append(f"{spell_id}: eff1 weapon potency {live_weapon_potency(row, 2)}, expected {want_potency} "
                       f"(= {pack_pct}% of Aimed Shot 19434's {aimed_potency})")
    return bad


# ---- (o) the half Volley ---------------------------------------------------------------------------------------------

def check_half_volley(volley: dict | None, volley_entry: dict | None, tick: dict | None, tick_entry: dict | None,
                      bonus_rows: list[dict], duration_index_3s: int) -> list[str]:
    """(o) B6: 201936 the dynobj + snapshot source (3 unhasted 1 s ticks, ap potency 75.5 direct T 1.5, bonus row =
    the Volley tick 42243's), hidden; 201937 the potency-excluded tick (no bonus row, no bit, Ex3 0x20010000)."""
    if volley is None or tick is None or volley_entry is None or tick_entry is None:
        return [f"{HALF_VOLLEY}/{HALF_VOLLEY_TICK}: not declared"]
    bad = []
    for key, want in (("SpellClassSet", SPELLFAMILY_HUNTER), ("SchoolMask", SCHOOL_ARCANE),
                      ("DefenseType", DEFENSE_RANGED), ("EquippedItemClass", -1), ("Targets", 0x40),
                      ("DurationIndex", duration_index_3s),
                      ("Effect_1", EFFECT_PERSISTENT_AREA_AURA), ("EffectAura_1", AURA_DUMMY),
                      ("ImplicitTargetA_1", 28), ("Effect_2", EFFECT_APPLY_AURA),
                      ("EffectAura_2", AURA_PERIODIC_DUMMY), ("EffectAuraPeriod_2", HALF_VOLLEY_AMPLITUDE_MS),
                      ("ImplicitTargetA_2", 1), ("Effect_3", 0)):
        if _i(volley, key) != want:
            bad.append(f"{HALF_VOLLEY}: {key} {volley.get(key)}, expected {want}")
    if spell_mask(volley) != (0, 0, D2_HALF_VOLLEY):
        bad.append(f"{HALF_VOLLEY}: SpellClassMask {_hex(spell_mask(volley))}, expected (0x0, 0x0, 0x40000000) "
                   f"(d2 b30: Barrage / Rain of Arrows reach the snapshot)")
    if _i(volley, "AttributesEx5") & ATTR_EX5_HASTE_AFFECT_DURATION:
        bad.append(f"{HALF_VOLLEY}: AttributesEx5 0x{_i(volley, 'AttributesEx5'):X} holds 0x2000 (hasted ticks; B6 "
                   f"wants {HALF_VOLLEY_TICKS} unhasted)")
    if not _i(volley, "Attributes") & ATTR_DO_NOT_DISPLAY:
        bad.append(f"{HALF_VOLLEY}: Attributes 0x{_i(volley, 'Attributes'):X} lacks DO_NOT_DISPLAY (0x80)")
    if not _i(volley, "AttributesEx3") & ATTR_EX3_SUPPRESS_CASTER_PROCS:
        bad.append(f"{HALF_VOLLEY}: AttributesEx3 lacks SUPPRESS_CASTER_PROCS (0x10000)")
    if HALF_VOLLEY_DURATION_MS // max(_i(volley, "EffectAuraPeriod_2"), 1) != HALF_VOLLEY_TICKS:
        bad.append(f"{HALF_VOLLEY}: {HALF_VOLLEY_DURATION_MS} ms / {volley.get('EffectAuraPeriod_2')} ms is not "
                   f"{HALF_VOLLEY_TICKS} ticks")
    potency = (volley_entry.get("effect1") or {}).get("_potency") or {}
    got = (potency.get("kind"), potency.get("total_potency"), potency.get("t_seconds"))
    if got != ("direct", HALF_VOLLEY_AP_POTENCY, HALF_VOLLEY_TIME_BASIS_S) or not potency.get("ap_coefficient"):
        bad.append(f"{HALF_VOLLEY}: eff0 potency (kind, total, T s) {got} ap {potency.get('ap_coefficient')}, "
                   f"expected ('direct', {HALF_VOLLEY_AP_POTENCY}, {HALF_VOLLEY_TIME_BASIS_S}) with an ap part "
                   f"(time_basis_ms 1500)")
    bonus = {int(b["entry"]): b for b in bonus_rows}
    mine, tick_row = bonus.get(HALF_VOLLEY), bonus.get(VOLLEY_TICK)
    if mine is None or tick_row is None or float(mine.get("ap_bonus") or 0) != float(tick_row.get("ap_bonus") or 0):
        bad.append(f"{HALF_VOLLEY}: spell_bonus_data ap {None if mine is None else mine.get('ap_bonus')}, expected "
                   f"the Volley tick {VOLLEY_TICK}'s {None if tick_row is None else tick_row.get('ap_bonus')}")
    for key, want in (("SpellClassSet", SPELLFAMILY_HUNTER), ("SchoolMask", SCHOOL_ARCANE),
                      ("DefenseType", DEFENSE_RANGED), ("EquippedItemClass", -1),
                      ("AttributesEx3", HALF_VOLLEY_TICK_EX3), ("Effect_1", EFFECT_SCHOOL_DAMAGE),
                      ("ImplicitTargetA_1", 87), ("ImplicitTargetB_1", 16), ("Effect_2", 0), ("Effect_3", 0)):
        if _i(tick, key) != want:
            bad.append(f"{HALF_VOLLEY_TICK}: {key} {tick.get(key)}, expected {want}")
    if any(spell_mask(tick)):
        bad.append(f"{HALF_VOLLEY_TICK}: SpellClassMask {_hex(spell_mask(tick))}, expected none (no SpellMod may "
                   f"touch the tick a second time)")
    if not (tick_entry.get("effect1") or {}).get("_potency_excluded"):
        bad.append(f"{HALF_VOLLEY_TICK}: eff0 not potency_excluded (the amount is the BP0 snapshot)")
    if HALF_VOLLEY_TICK in bonus:
        bad.append(f"{HALF_VOLLEY_TICK}: has a spell_bonus_data row (a second AP pass on the snapshot)")
    return bad


def check_half_volley_reach(masks, rows_by_id: dict[int, dict]) -> list[str]:
    """(o) VOLLEY_DAMAGE / BARRAGE_DAMAGE hold d2 b30 and the Barrage / Rain of Arrows ranks' eff0 carry them."""
    bad = []
    for name, ranks in (("VOLLEY_DAMAGE", RAIN_OF_ARROWS_RANKS), ("BARRAGE_DAMAGE", BARRAGE_RANKS)):
        composite = tuple(getattr(masks, name, (0, 0, 0)))
        if not composite[2] & D2_HALF_VOLLEY:
            bad.append(f"_masks.{name} {_hex(composite)} lacks d2 b30 (the half Volley)")
        for spell_id in ranks:
            row = rows_by_id.get(spell_id)
            if row is None:
                bad.append(f"{spell_id}: not declared")
            elif effect_mask(row, 1) != composite:
                bad.append(f"{spell_id}: eff0 mask {_hex(effect_mask(row, 1))}, expected {name} {_hex(composite)}")
    return bad


# ---- (p) Barrage r3's row --------------------------------------------------------------------------------------------

def check_barrage_chain_proc(procs: list[dict]) -> list[str]:
    """(p) the 24691 row is positive-keyed on r3 alone: no -19461 chain key (it would give r1 / r2 the capstone) and no
    row on r1 / r2 (their ProcTypeMask is 0)."""
    keys = {int(p["SpellId"]) for p in procs}
    return [f"spell_proc {k}: only {BARRAGE_R3} carries the half Volley row" for k in sorted(keys)
            if abs(k) in BARRAGE_RANKS and k != BARRAGE_R3]


# ---- (q) Lone Survivor / Combat Experience ---------------------------------------------------------------------------

def check_lone_survivor_and_capstone(rows_by_id: dict[int, dict], permanent_index: int) -> list[str]:
    bad = []
    row = rows_by_id.get(LONE_SURVIVOR_BUFF)
    if row is None:
        bad.append(f"{LONE_SURVIVOR_BUFF}: not declared")
    else:
        for key, want in (("Effect_1", EFFECT_APPLY_AURA), ("EffectAura_1", AURA_MOD_DAMAGE_PERCENT_DONE),
                          ("EffectMiscValue_1", 127), ("DurationIndex", permanent_index), ("AttributesEx7", 0),
                          ("EquippedItemClass", -1), ("SpellIconID", 535)):
            if _i(row, key) != want:
                bad.append(f"{LONE_SURVIVOR_BUFF}: {key} {row.get(key)}, expected {want}")
    row = rows_by_id.get(COMBAT_EXPERIENCE_CAPSTONE)
    if row is None:
        bad.append(f"{COMBAT_EXPERIENCE_CAPSTONE}: not declared")
    else:
        for key, want in (("Effect_1", EFFECT_APPLY_AURA), ("EffectAura_1", AURA_MOD_STAT), ("EffectMiscValue_1", 3),
                          ("EffectBasePoints_1", -1), ("Effect_2", EFFECT_APPLY_AURA),
                          ("EffectAura_2", AURA_PERIODIC_DUMMY), ("EffectAuraPeriod_2", 1000),
                          ("EquippedItemClass", -1)):
            if _i(row, key) != want:
                bad.append(f"{COMBAT_EXPERIENCE_CAPSTONE}: {key} {row.get(key)}, expected {want}")
        if _i(row, "Attributes") & (ATTR_PASSIVE | ATTR_DO_NOT_DISPLAY) != ATTR_PASSIVE | ATTR_DO_NOT_DISPLAY:
            bad.append(f"{COMBAT_EXPERIENCE_CAPSTONE}: Attributes 0x{_i(row, 'Attributes'):X}, expected a hidden "
                       f"passive (0x40 | 0x80)")
    return bad


# ---- (u) the S2b review fixes ----------------------------------------------------------------------------------------

def check_half_volley_level(rows_by_id: dict[int, dict]) -> list[str]:
    """(u) R-data M-1: potency derives BaseLevel from SpellLevel and SpellEffectInfo::CalcValue lifts a lower caster
    level to BaseLevel, so 201936 must share the Volley tick 42243's SpellLevel to be one tick at every level."""
    volley, tick = rows_by_id.get(HALF_VOLLEY), rows_by_id.get(VOLLEY_TICK)
    if volley is None or tick is None:
        return [f"{HALF_VOLLEY}/{VOLLEY_TICK}: not declared"]
    if not _i(tick, "SpellLevel") or _i(volley, "SpellLevel") != _i(tick, "SpellLevel"):
        return [f"{HALF_VOLLEY}: SpellLevel {volley.get('SpellLevel')}, expected the Volley tick {VOLLEY_TICK}'s "
                f"{tick.get('SpellLevel')} (the potency BaseLevel; a higher one gives low-level hunters its base)"]
    return []


def check_ignore_line_of_sight(rows_by_id: dict[int, dict], ids=IGNORE_LOS_IDS) -> list[str]:
    """(u) R-cpp m-1: the ricochet, the bounce and Convergence carry AttributesEx2 IGNORE_LINE_OF_SIGHT (0x4)."""
    bad = []
    for spell_id in ids:
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
        elif not _i(row, "AttributesEx2") & ATTR_EX2_IGNORE_LINE_OF_SIGHT:
            bad.append(f"{spell_id}: AttributesEx2 0x{_i(row, 'AttributesEx2'):X} lacks IGNORE_LINE_OF_SIGHT (0x4)")
    return bad


def check_cannot_be_saved(custom_attrs: list[dict], ids=CANNOT_BE_SAVED_S2B_IDS) -> list[str]:
    """(u) R-cpp m-4: exactly one spell_custom_attr row per id (the table is keyed on the spell id), holding
    CANNOT_BE_SAVED (0x01000000)."""
    bad = []
    for spell_id in ids:
        attrs = [int(c["attributes"]) for c in custom_attrs if int(c["spell_id"]) == spell_id]
        if len(attrs) != 1 or not attrs[0] & CUSTOM_ATTR_CANNOT_BE_SAVED:
            bad.append(f"{spell_id}: spell_custom_attr {[hex(a) for a in attrs]}, expected one row with "
                       f"CANNOT_BE_SAVED (0x01000000)")
    return bad


# ---- (r) the TRIGGERED_FULL_MASK source guard ------------------------------------------------------------------------

PACK_SHOT_TOKENS = ("SPELL_AIMED_SHOT_RICOCHET", "SPELL_AIMED_SHOT_BOUNCE", str(RICOCHET), str(BOUNCE))
_CAST_CALL_RE = re.compile(r"\b(CastSpell|CastCustomSpell)\s*\(")
_COMMENT_RE = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)
_TRIGGERED_FLAG_RE = re.compile(r"\bTRIGGERED_[A-Z_]+\b")


def _call_args(text: str, open_paren: int) -> str:
    depth = 0
    for i in range(open_paren, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return text[open_paren + 1:i]
    return text[open_paren + 1:]


def check_pack_shot_casts(text: str) -> tuple[list[str], int]:
    """(r) every CastSpell / CastCustomSpell whose arguments name 201934 / 201935 (the header name, the literal, or a
    local alias assigned from either, e.g. `uint32 const shot = ... SPELL_AIMED_SHOT_BOUNCE`) passes TRIGGERED_FULL_MASK
    and no other TRIGGERED_* flag (R3). Returns (problems, casts seen): zero casts is fine (B1 may not have written
    them yet)."""
    code = _COMMENT_RE.sub("", text)
    tokens = set(PACK_SHOT_TOKENS)
    pattern = "|".join(re.escape(t) for t in PACK_SHOT_TOKENS)
    for m in re.finditer(r"\b(\w+)\s*(?<![=!<>+\-*/])=(?!=)[^;{}]*?\b(?:" + pattern + r")\b", code):
        if not _CAST_CALL_RE.search(m.group(0)):      # `result = CastSpell(... RICOCHET ...)` is a cast, not an alias
            tokens.add(m.group(1))
    token_re = re.compile(r"\b(?:" + "|".join(re.escape(t) for t in sorted(tokens)) + r")\b")
    bad, seen = [], 0
    for m in _CAST_CALL_RE.finditer(code):
        args = _call_args(code, m.end() - 1)
        if not token_re.search(args):
            continue
        seen += 1
        line = code.count("\n", 0, m.start()) + 1
        flags = set(_TRIGGERED_FLAG_RE.findall(args))
        if flags != {"TRIGGERED_FULL_MASK"}:
            bad.append(f"line ~{line}: {m.group(1)}({' '.join(args.split())}) passes {sorted(flags) or 'no flag'}, "
                       f"expected TRIGGERED_FULL_MASK only (R3: the d0 b17 10 s RecoveryTime)")
    return bad, seen


# ---- (s) 34082 and aura 140 ------------------------------------------------------------------------------------------

def check_advantaged_state(row: dict | None) -> list[str]:
    """(s) the user's ruling: no MOD_RANGED_HASTE effect left on 34082; eff0 PROC_TRIGGER_SPELL -> 34084 and the proc
    fields stay stock; still a hidden passive with EquippedItemClass -1."""
    if row is None:
        return [f"{ADVANTAGED_STATE}: not declared (the stock edit is missing: the 15% ranged haste is back)"]
    bad = []
    for n in (1, 2, 3):
        if _i(row, f"EffectAura_{n}") == AURA_MOD_RANGED_HASTE:
            bad.append(f"eff{n - 1} still MOD_RANGED_HASTE (140) bp {row.get(f'EffectBasePoints_{n}')}")
    for key, want in (("Effect_1", EFFECT_APPLY_AURA), ("EffectAura_1", AURA_PROC_TRIGGER_SPELL),
                      ("EffectTriggerSpell_1", ADVANTAGED_STATE_PROC), ("Effect_2", 0), ("Effect_3", 0),
                      ("ProcTypeMask", 65876), ("ProcChance", 100), ("Attributes", 464), ("EquippedItemClass", -1)):
        if _i(row, key) != want:
            bad.append(f"{key} {row.get(key)}, expected {want}")
    return [f"{ADVANTAGED_STATE}: {b}" for b in bad]


def hunter_learnable_ids(sla_rows, talent_rows, trainer_spells, linked) -> set[int]:
    """(s) spells a hunter actually learns: SLA auto-learn rows (AcquireMethod 1/2) for the hunter class mask (or class
    mask 0 on a hunter skill line), hunter talent tab ranks, trainer rows, then linked type-2 passives of those."""
    ids: set[int] = set()
    for r in sla_rows:
        if _i(r, "AcquireMethod") not in SLA_AUTO_LEARN:
            continue
        mask = _i(r, "ClassMask")
        if mask & CLASSMASK_HUNTER or (not mask and _i(r, "SkillLine") in HUNTER_SKILL_LINES):
            ids.add(_i(r, "Spell"))
    for row in talent_rows:
        if _i(row, "TabID") in HUNTER_TALENT_TABS:
            ids.update(_i(row, f"SpellRank_{n}") for n in range(1, 10))
    ids.update(int(t.get("SpellId") or t.get("spell_id") or 0) for t in trainer_spells)
    links = [(int(r["spell_trigger"]), int(r["spell_effect"]), int(r["type"])) for r in linked]
    grown = True
    while grown:
        new = {effect for trigger, effect, kind in links if kind == 2 and trigger in ids and effect > 0} - ids
        ids |= new
        grown = bool(new)
    ids.discard(0)
    return ids


def _amount_nonzero(row: dict, n: int) -> bool:
    die = _i(row, f"EffectDieSides_{n}")
    return die > 1 or _i(row, f"EffectBasePoints_{n}") + (1 if die == 1 else 0) != 0


def check_no_learnable_ranged_haste(spell_rows: dict[int, dict], learnable: set[int]) -> list[str]:
    """(s) no learnable passive (built row, else stock) carries aura 140 with a non-zero amount."""
    bad = []
    for spell_id in sorted(learnable):
        row = spell_rows.get(spell_id)
        if row is None or not _i(row, "Attributes") & ATTR_PASSIVE:
            continue
        for n in (1, 2, 3):
            if _i(row, f"Effect_{n}") and _i(row, f"EffectAura_{n}") == AURA_MOD_RANGED_HASTE \
                    and _amount_nonzero(row, n):
                bad.append(f"{spell_id}: learnable passive with MOD_RANGED_HASTE (140) on eff{n - 1}, bp "
                           f"{row.get(f'EffectBasePoints_{n}')} (user ruling 2026-10-16: no hidden ranged haste)")
    return bad


# ---- (t) Multi-Shot --------------------------------------------------------------------------------------------------

def check_multi_shot(row: dict | None) -> list[str]:
    if row is None:
        return [f"{MULTI_SHOT}: not declared"]
    bad = [f"{MULTI_SHOT}: {key} {row.get(key)}, expected {want} (B1: data unchanged)"
           for key, want in MULTI_SHOT_FIELDS.items() if _i(row, key) != want]
    if float(row.get("Speed") or 0) != 30.0:
        bad.append(f"{MULTI_SHOT}: Speed {row.get('Speed')}, expected 30 (B1: data unchanged)")
    return bad


# ---- real data -------------------------------------------------------------------------------------------------------

def _cast_times(reuse) -> dict[int, int]:
    rows = {**state.load_stock_rows(dbcfmt.SPELLCASTTIMES),
            **{r["ID"]: r for r in reuse.minted.get("spellcasttimes", [])}}
    return {int(i): int(r.get("Base") or 0) for i, r in rows.items()}


def _touched_ids() -> set[int]:
    return {*NEW_S2A_IDS, *TAB_RANKS, *EDITED_STOCK_HELPERS, *S2B_MINUS_ONE_IDS}


def _const(package, name: str):
    return next((c["value"] for c in package.consts if c["name"] == name), None)


class HunterMmDataTest(unittest.TestCase):
    def assertClean(self, problems: list[str]):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_tab_363_layout(self):
        package = package_data()["package"]
        built = [build.build_talent_row(t) for t in package.talents]
        self.assertClean(check_tab_363(package.talents, built, package.skill_line_abilities, package.trainer_spells))

    def test_orphaned_ranks_in_no_talent_row(self):
        package = package_data()["package"]
        talents = {**state.load_stock_rows(dbcfmt.TALENT),
                   **{int(r["ID"]): r for r in map(build.build_talent_row, package.talents)}}
        self.assertClean(check_orphans(list(talents.values())))
        sv = [r for r in talents.values() if _i(r, "TabID") == SV_TAB and _i(r, "ID") == SNIPER_TRAINING_ROW]
        self.assertEqual(sv, [], "Sniper Training 2143 still on tab 362 in the overlay")

    def test_s2b_ids_declared(self):
        rows = package_data()["rows_by_id"]
        self.assertEqual(sorted(i for i in NEW_S2B_IDS if i not in rows), [])

    def test_pack_shots(self):
        data = package_data()
        self.assertClean(check_pack_shots(data["rows_by_id"], _const(data["package"], "PACK_SHOT_DAMAGE_PCT")))

    def test_half_volley(self):
        data = package_data()
        rows, package = data["rows_by_id"], data["package"]
        entries = {int(e["id"]): e for e in package.spells}
        self.assertClean(check_half_volley(rows.get(HALF_VOLLEY), entries.get(HALF_VOLLEY), rows.get(HALF_VOLLEY_TICK),
                                           entries.get(HALF_VOLLEY_TICK), package.spell_bonus_data,
                                           data["reuse"].duration_index(HALF_VOLLEY_DURATION_MS)))
        self.assertClean(check_half_volley_reach(load_masks_module(), rows))

    def test_barrage_proc_chain(self):
        self.assertClean(check_barrage_chain_proc(package_data()["package"].spell_procs))

    def test_lone_survivor_and_combat_experience(self):
        data = package_data()
        self.assertClean(check_lone_survivor_and_capstone(data["rows_by_id"], data["reuse"].duration_index(-1)))

    def test_s2b_review_fixes(self):
        data = package_data()
        rows = data["rows_by_id"]
        self.assertClean(check_half_volley_level(rows))
        self.assertClean(check_ignore_line_of_sight(rows))
        self.assertClean(check_cannot_be_saved(data["package"].custom_attrs))

    def test_pack_shot_casts_pass_full_mask(self):
        problems = []
        for path in PACK_SHOT_CASTER_SOURCES:
            if path.is_file():
                bad, _seen = check_pack_shot_casts(path.read_text(encoding="utf-8"))
                problems += [f"{path.name}: {b}" for b in bad]
        self.assertClean(problems)

    def test_advantaged_state_and_no_learnable_ranged_haste(self):
        data = package_data()
        package, rows = data["package"], data["rows_by_id"]
        self.assertClean(check_advantaged_state(rows.get(ADVANTAGED_STATE)))
        sla = {**state.load_stock_rows(dbcfmt.SKILLLINEABILITY), **{int(r["ID"]): r for r in data["sla_rows"]}}
        talents = {**state.load_stock_rows(dbcfmt.TALENT),
                   **{int(r["ID"]): r for r in map(build.build_talent_row, package.talents)}}
        learnable = hunter_learnable_ids(sla.values(), talents.values(), package.trainer_spells,
                                         package.linked_spells)
        self.assertIn(ADVANTAGED_STATE, learnable)              # the guard sees 34082 (SLA 15148, AcquireMethod 2)
        self.assertFalse(learnable & set(SERPENTS_SWIFTNESS_ORPHANS), "an aura-140 orphan became learnable")
        self.assertClean(check_no_learnable_ranged_haste({**data["stock_spells"], **rows}, learnable))

    def test_multi_shot_unchanged(self):
        self.assertClean(check_multi_shot(package_data()["rows_by_id"].get(MULTI_SHOT)))

    def test_marks(self):
        data = package_data()
        rows, reuse = data["rows_by_id"], data["reuse"]
        cast_times = _cast_times(reuse)
        self.assertClean([b for i in MARKS
                          for b in check_mark(i, rows.get(i), cast_times, reuse.duration_index(MARK_DURATION_MS))])
        for i in MARKS:   # R-data S1: SPELL_RANGE_RANGED (too-close check), like 3044 / 19434
            self.assertEqual(_i(rows[i], "RangeIndex"), 114, i)

    def test_aimed_shot(self):
        data = package_data()
        package = data["package"]
        entries = {int(e["id"]): e for e in package.spells}
        self.assertClean(check_aimed_shot(data["rows_by_id"].get(AIMED_SHOT), entries.get(AIMED_SHOT),
                                          _cast_times(data["reuse"]), package.spell_categories,
                                          package.spell_bonus_data, package.potency_corrections))

    def test_free_arcane_shot(self):
        data = package_data()
        rows = data["rows_by_id"]
        self.assertClean(check_free_arcane_shot(rows.get(ARCANE_SHOT_FREE), rows.get(ARCANE_SHOT),
                                                data["package"].spell_script_names, data["package"].spell_bonus_data))

    def test_visibility_lists(self):
        self.assertClean(check_visibility(package_data()["rows_by_id"]))

    def test_falcons_haste(self):
        data = package_data()
        self.assertClean(check_falcons_haste(data["rows_by_id"].get(FALCONS_HASTE), data["reuse"].duration_index(-1)))
        # R-cpp S1: AURA_INTERRUPT_FLAG_CHANGE_MAP, the haste drops with the marks on a map change.
        self.assertEqual(_i(data["rows_by_id"][FALCONS_HASTE], "AuraInterruptFlags"), 0x00080000)

    def test_equipped_item_class(self):
        rows = package_data()["rows_by_id"]
        self.assertClean(check_equipped_item_class(rows, _touched_ids() - PLAYER_CAST_SHOTS, PLAYER_CAST_SHOTS))

    def test_family_bit_carriers(self):
        self.assertClean(check_family_bit_carriers(package_data()["rows"]))

    def test_masks_module_holds_the_spec_composites(self):
        self.assertClean(check_masks_module(load_masks_module()))

    def test_spellmod_rows(self):
        rows = package_data()["rows_by_id"]
        masks = load_masks_module()
        self.assertClean(check_spellmod_specs(rows, masks))
        self.assertClean(check_removed_effects(rows))
        self.assertClean(check_sniper_training_ranks(rows))
        self.assertClean(check_chimera_serpent(rows.get(CHIMERA_SERPENT)))
        self.assertClean(check_charged_buffs(rows))

    def test_no_reader_holds_the_pet_bit(self):
        data = package_data()
        self.assertClean(check_no_pet_bit_readers(data["rows_by_id"], _touched_ids(), data["package"].spell_procs))

    def test_spell_proc_rows(self):
        self.assertClean(check_proc_rows(package_data()["package"].spell_procs))

    def test_m15_proc_type_masks_and_stale_masks(self):
        data = package_data()
        package = data["package"]
        self.assertClean(check_m15(data["rows_by_id"], package.talents, package.spell_procs))
        self.assertClean(check_rapid_killing(data["rows_by_id"]))

    def test_stampede_stays_family_zero(self):
        self.assertClean(check_stampede_family(package_data()["rows_by_id"].get(STAMPEDE)))

    def test_script_bindings_and_mastery_link(self):
        package = package_data()["package"]
        self.assertClean(check_bindings(package.spell_script_names, package.script_removals, package.linked_spells))


# ---- negative fixtures: every check passes a good input and fires on a crafted bad copy ------------------------------

def changed(row: dict, **cols) -> dict:
    out = copy.deepcopy(row)
    out.update(cols)
    return out


CAST_TIMES = {0: 0, 1: 0, 4: 1000, 5: 2000, 16: 1500, 18: -1000000}
DUR15, DUR_PERM = 7, 21


def good_mark(spell_id: int = SNIPERS_MARK) -> dict:
    school, recovery, level, icon = MARK_DATA[spell_id]
    return {"ID": spell_id, **MARK_FIELDS, "SchoolMask": school, "RecoveryTime": recovery, "SpellLevel": level,
            "SpellIconID": icon, "DurationIndex": DUR15,
            "Effect_1": EFFECT_NORMALIZED_WEAPON_DMG, "EffectBasePoints_1": -1, "ImplicitTargetA_1": 6,
            "Effect_2": EFFECT_WEAPON_PERCENT_DAMAGE, "EffectBasePoints_2": 109, "ImplicitTargetA_2": 6,
            "Effect_3": EFFECT_APPLY_AURA, "EffectAura_3": AURA_DUMMY, "EffectBasePoints_3": -1, "ImplicitTargetA_3": 6}


def good_tab() -> list[dict]:
    return [{"id": tid, "tab_id": TAB, "tier": cell[0], "column": cell[1], "rank_spell_ids": list(ranks),
             "depends_on": None, "raw_overrides": None, "flags": 1 if tid in CASTABLE_ROWS else 0}
            for tid, (cell, ranks) in TAB_LAYOUT.items()]


GOOD_SLA = [{"id": k, "spell_id": v, "skill_line": SKILL_LINE_MM, "class_mask": CLASSMASK_HUNTER}
            for k, v in MARK_SLA.items()]
GOOD_ST_BUILT = {"ID": SNIPER_TRAINING_ROW, "TabID": TAB, "TierID": 7, "ColumnIndex": 2}


def good_aimed() -> tuple[dict, dict]:
    row = {"ID": AIMED_SHOT, "CastingTimeIndex": 16, "Attributes": 0x10012, "Category": 1301,
           "CategoryRecoveryTime": 10000, "RecoveryTime": 0, "SpellClassMask_1": D0_AIMED_SHOT, "EquippedItemClass": 2,
           "Effect_1": EFFECT_NORMALIZED_WEAPON_DMG, "EffectBasePoints_1": -1, "Effect_2": EFFECT_WEAPON_PERCENT_DAMAGE,
           "InterruptFlags": 15, "SpellLevel": 20, "MaxLevel": 0}
    entry = {"id": AIMED_SHOT, "cast_time_ms": 1500, "effect1": {}, "effect2": {"_potency": {"ap_coefficient": 0.0,
                                                                                            "sp_coefficient": 0.0}}}
    return row, entry


def good_arcane_pair() -> tuple[dict, dict]:
    damage = {"Effect_1": EFFECT_SCHOOL_DAMAGE, "EffectBasePoints_1": -71, "EffectDieSides_1": 1,
              "EffectRealPointsPerLevel_1": 7.428571428571428}
    arcane = {"ID": ARCANE_SHOT, **damage, "Effect_2": EFFECT_DUMMY, "EffectBasePoints_2": 199, "EffectDieSides_2": 1}
    free = {"ID": ARCANE_SHOT_FREE, **damage, "Effect_2": EFFECT_DUMMY,
            "EffectBasePoints_2": 199, "EffectDieSides_2": 1, "CastingTimeIndex": 18, "EquippedItemClass": -1,
            "SpellClassSet": 9, "SpellClassMask_1": D0_ARCANE_SHOT, "SchoolMask": SCHOOL_ARCANE,
            "DefenseType": DEFENSE_RANGED, "AttributesEx3": ATTR_EX3_SUPPRESS_CASTER_PROCS}
    return free, arcane


GOOD_FREE_BOUND = [{"spell_id": ARCANE_SHOT_FREE, "ScriptName": n} for n in sorted(FREE_ARCANE_SHOT_SCRIPTS)]
GOOD_ARCANE_BONUS = [{"entry": i, "direct_bonus": 0.0, "dot_bonus": 0.0, "ap_bonus": 0.5571428571428572,
                      "ap_dot_bonus": 0.0} for i in (ARCANE_SHOT, ARCANE_SHOT_FREE)]


def good_spellmod_rows(masks) -> dict[int, dict]:
    rows: dict[int, dict] = {}
    for ids, effect, aura, op, ref in SPELLMOD_SPECS:
        mask = resolve_mask(masks, ref)
        for spell_id in ids:
            row = rows.setdefault(spell_id, {"ID": spell_id, "SpellClassSet": 9})
            row.update({f"Effect_{effect}": EFFECT_APPLY_AURA, f"EffectAura_{effect}": aura,
                        f"EffectMiscValue_{effect}": op})
            for n, word in enumerate(mask, start=1):
                row[f"EffectSpellClassMask{LETTERS[effect - 1]}_{n}"] = word
    return rows


def good_procs() -> list[dict]:
    procs = []
    for key, cols in PROC_ROWS.items():
        p = {"SpellId": key}
        for col, want in cols.items():
            if col == "mask":
                p.update(SpellFamilyMask0=want[0], SpellFamilyMask1=want[1], SpellFamilyMask2=want[2])
            else:
                p[col] = want
        procs.append(p)
    for key, (_charges, mask) in CHARGED_BUFFS.items():
        procs.append({"SpellId": key, "ProcFlags": 0x100, "SpellFamilyName": 9, "SpellPhaseMask": 0x1,
                      "AttributesMask": 0, "Chance": 100.0, "SpellFamilyMask0": mask[0], "SpellFamilyMask1": mask[1],
                      "SpellFamilyMask2": mask[2]})
    return procs


def good_rapid_killing() -> dict[int, dict]:
    base = {"Effect_1": EFFECT_APPLY_AURA, "EffectAura_1": AURA_DUMMY, "EffectTriggerSpell_1": 0,
            "Effect_2": EFFECT_APPLY_AURA, "EffectAura_2": AURA_ADD_FLAT_MODIFIER, "EffectSpellClassMaskB_1": 0x20}
    rows = {i: {"ID": i, **base} for i in (34948, 34949, RAPID_KILLING_R3)}
    rows[RAPID_KILLING_R3].update(Effect_3=EFFECT_APPLY_AURA, EffectAura_3=AURA_PROC_TRIGGER_SPELL,
                                  EffectTriggerSpell_3=RAPID_KILLING_BUFF_ID, ProcTypeMask=0x2, ProcChance=100)
    return rows


def good_bindings() -> tuple[list[dict], list[dict], list[dict]]:
    bound = [{"spell_id": i, "ScriptName": n} for n, ids in SCRIPT_BINDINGS.items() for i in ids]
    removals = [{"spell_id": k, "ScriptName": n} for k, n in S2A_UNBINDS]
    linked = [{"spell_trigger": a, "spell_effect": b, "type": t} for a, b, t in LINKS]
    return bound, removals, linked


def good_pack_rows() -> dict[int, dict]:
    aimed = {"ID": AIMED_SHOT, "Effect_2": EFFECT_WEAPON_PERCENT_DAMAGE, "EffectBasePoints_2": 219,
             "EffectDieSides_2": 1}
    rows = {AIMED_SHOT: aimed}
    for i in PACK_SHOTS:
        rows[i] = {"ID": i, **PACK_SHOT_FIELDS, "Speed": 0.0, "AttributesEx3": ATTR_EX3_SUPPRESS_CASTER_PROCS,
                   "EffectBasePoints_2": 109, "EffectDieSides_2": 1, "EffectDieSides_1": 1}
    return rows


def good_half_volley() -> tuple[dict, dict, dict, dict, list[dict]]:
    volley = {"ID": HALF_VOLLEY, "SpellClassSet": 9, "SchoolMask": SCHOOL_ARCANE, "DefenseType": DEFENSE_RANGED,
              "EquippedItemClass": -1, "Targets": 0x40, "DurationIndex": 30112, "Attributes": ATTR_DO_NOT_DISPLAY,
              "AttributesEx3": ATTR_EX3_SUPPRESS_CASTER_PROCS, "SpellClassMask_3": D2_HALF_VOLLEY,
              "Effect_1": EFFECT_PERSISTENT_AREA_AURA, "EffectAura_1": AURA_DUMMY, "ImplicitTargetA_1": 28,
              "Effect_2": EFFECT_APPLY_AURA, "EffectAura_2": AURA_PERIODIC_DUMMY, "EffectAuraPeriod_2": 1000,
              "ImplicitTargetA_2": 1}
    volley_entry = {"id": HALF_VOLLEY, "effect1": {"_potency": {"kind": "direct", "total_potency": 75.5,
                                                                "t_seconds": 1.5, "ap_coefficient": 0.3236}}}
    tick = {"ID": HALF_VOLLEY_TICK, "SpellClassSet": 9, "SchoolMask": SCHOOL_ARCANE, "DefenseType": DEFENSE_RANGED,
            "EquippedItemClass": -1, "AttributesEx3": 0x20010000, "Effect_1": EFFECT_SCHOOL_DAMAGE,
            "ImplicitTargetA_1": 87, "ImplicitTargetB_1": 16}
    tick_entry = {"id": HALF_VOLLEY_TICK, "effect1": {"_potency_excluded": "snapshot"}}
    bonus = [{"entry": HALF_VOLLEY, "ap_bonus": 0.3236}, {"entry": VOLLEY_TICK, "ap_bonus": 0.3236}]
    return volley, volley_entry, tick, tick_entry, bonus


def good_lone_and_capstone() -> dict[int, dict]:
    return {
        LONE_SURVIVOR_BUFF: {"ID": LONE_SURVIVOR_BUFF, "Effect_1": EFFECT_APPLY_AURA,
                             "EffectAura_1": AURA_MOD_DAMAGE_PERCENT_DONE, "EffectMiscValue_1": 127,
                             "DurationIndex": DUR_PERM, "AttributesEx7": 0, "EquippedItemClass": -1,
                             "SpellIconID": 535},
        COMBAT_EXPERIENCE_CAPSTONE: {"ID": COMBAT_EXPERIENCE_CAPSTONE, "Attributes": 464, "Effect_1": EFFECT_APPLY_AURA,
                                     "EffectAura_1": AURA_MOD_STAT, "EffectMiscValue_1": 3, "EffectBasePoints_1": -1,
                                     "Effect_2": EFFECT_APPLY_AURA, "EffectAura_2": AURA_PERIODIC_DUMMY,
                                     "EffectAuraPeriod_2": 1000, "EquippedItemClass": -1},
    }


# (r) fixtures in the shape B1 is expected to write (S2b B3 steps 7 / 8)
GOOD_CASTS_CPP = """
    // a comment naming CastSpell(unit, HunterData::SPELL_AIMED_SHOT_RICOCHET, TRIGGERED_NONE) is ignored
    player->CastSpell(unit, HunterData::SPELL_AIMED_SHOT_RICOCHET, TRIGGERED_FULL_MASK);
    player->CastSpell(bounceTarget, HunterData::SPELL_AIMED_SHOT_BOUNCE,
                      TRIGGERED_FULL_MASK);
    uint32 const shotId = ricochet ? HunterData::SPELL_AIMED_SHOT_RICOCHET : HunterData::SPELL_AIMED_SHOT_BOUNCE;
    player->CastSpell(unit, shotId, TRIGGERED_FULL_MASK);
    player->CastSpell(player, HunterData::SPELL_RAIN_OF_ARROWS_BOUNCE, TRIGGERED_IGNORE_GCD);
    if (x == y) player->CastSpell(player, HunterData::SPELL_TRICK_SHOTS_BUFF, true);
"""


def good_learnable_sources() -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    sla = [{"ID": 15148, "SkillLine": 183, "Spell": ADVANTAGED_STATE, "ClassMask": 4, "AcquireMethod": 2},
           {"ID": 15219, "SkillLine": 50, "Spell": 34469, "ClassMask": 4, "AcquireMethod": 0},
           {"ID": 1, "SkillLine": 6, "Spell": 116, "ClassMask": 128, "AcquireMethod": 2}]     # a mage spell
    talents = [{"ID": 1803, "TabID": 361, "SpellRank_1": 34466, "SpellRank_2": 34467, "SpellRank_3": 34468},
               {"ID": 1, "TabID": 41, "SpellRank_1": 44972}]                                  # another class's tab
    trainer = [{"SpellId": 3045}]
    linked = [{"spell_trigger": COMBAT_EXPERIENCE_R3, "spell_effect": COMBAT_EXPERIENCE_CAPSTONE, "type": 2},
              {"spell_trigger": 34466, "spell_effect": 201999, "type": 2}]
    return sla, talents, trainer, linked


def haste_passive(spell_id: int, bp: int = 14, die: int = 1, effect: int = 2, attributes: int = 464) -> dict:
    return {"ID": spell_id, "Attributes": attributes, f"Effect_{effect}": EFFECT_APPLY_AURA,
            f"EffectAura_{effect}": AURA_MOD_RANGED_HASTE, f"EffectBasePoints_{effect}": bp,
            f"EffectDieSides_{effect}": die}


GOOD_ADVANTAGED = {"ID": ADVANTAGED_STATE, "Attributes": 464, "ProcTypeMask": 65876, "ProcChance": 100,
                   "EquippedItemClass": -1, "Effect_1": EFFECT_APPLY_AURA, "EffectAura_1": AURA_PROC_TRIGGER_SPELL,
                   "EffectTriggerSpell_1": ADVANTAGED_STATE_PROC}


class HunterMmDataNegativeTest(unittest.TestCase):
    def test_tab_363_guard(self):
        talents = good_tab()
        self.assertEqual(sum(len(t["rank_spell_ids"]) for t in talents), TAB_POINTS)
        self.assertEqual(len(talents), TAB_TALENT_COUNT)
        self.assertEqual(check_tab_363(talents, [GOOD_ST_BUILT], GOOD_SLA, []), [])
        self.assertTrue(check_tab_363(talents[:-1], [GOOD_ST_BUILT], GOOD_SLA, []))                 # 32 talents
        clash = copy.deepcopy(talents)
        clash[1]["tier"], clash[1]["column"] = clash[0]["tier"], clash[0]["column"]
        self.assertGreaterEqual(len(check_tab_363(clash, [GOOD_ST_BUILT], GOOD_SLA, [])), 2)     # clash + wrong cell
        prereq = copy.deepcopy(talents)
        prereq[3]["depends_on"] = {"talent_id": 1344, "rank": 3}
        self.assertEqual(len(check_tab_363(prereq, [GOOD_ST_BUILT], GOOD_SLA, [])), 1)
        raw = copy.deepcopy(talents)
        raw[3]["raw_overrides"] = {"PrereqTalent_1": 1344}
        self.assertEqual(len(check_tab_363(raw, [GOOD_ST_BUILT], GOOD_SLA, [])), 1)
        built_prereq = {"ID": 1345, "TabID": TAB, "PrereqTalent_1": 1349}
        self.assertEqual(len(check_tab_363(talents, [GOOD_ST_BUILT, built_prereq], GOOD_SLA, [])), 1)
        five = copy.deepcopy(talents)                                                               # 19430 / 19431 back
        next(t for t in five if t["id"] == 1344)["rank_spell_ids"] += [19430, 19431]
        self.assertEqual(len(check_tab_363(five, [GOOD_ST_BUILT], GOOD_SLA, [])), 2)               # points + ranks
        flags = copy.deepcopy(talents)
        next(t for t in flags if t["id"] == 1808)["flags"] = 0
        self.assertEqual(len(check_tab_363(flags, [GOOD_ST_BUILT], GOOD_SLA, [])), 1)
        sv = talents + [{"id": SNIPER_TRAINING_ROW, "tab_id": SV_TAB, "tier": 8, "column": 3,
                         "rank_spell_ids": list(SNIPER_TRAINING_RANKS)}]
        self.assertEqual(len(check_tab_363(sv, [GOOD_ST_BUILT], GOOD_SLA, [])), 1)
        self.assertEqual(len(check_tab_363(talents, [{**GOOD_ST_BUILT, "TabID": SV_TAB}], GOOD_SLA, [])), 2)
        self.assertEqual(len(check_tab_363(talents, [{**GOOD_ST_BUILT, "TierID": 8}], GOOD_SLA, [])), 1)
        bad_sla = [dict(e) for e in GOOD_SLA]
        bad_sla[0]["skill_line"] = 202
        self.assertEqual(len(check_tab_363(talents, [GOOD_ST_BUILT], bad_sla, [])), 1)
        self.assertEqual(len(check_tab_363(talents, [GOOD_ST_BUILT], GOOD_SLA[1:], [])), 1)
        self.assertEqual(len(check_tab_363(talents, [GOOD_ST_BUILT], GOOD_SLA, [{"SpellId": FALCONS_MARK}])), 1)

    def test_orphan_guard(self):
        self.assertEqual(check_orphans([{"ID": 1344, "TabID": TAB, "SpellRank_1": 19426}]), [])
        self.assertEqual(len(check_orphans([{"ID": 1344, "TabID": TAB, "SpellRank_4": 19430}])), 1)
        self.assertEqual(len(check_orphans([{"ID": 1808, "TabID": TAB, "SpellRank_1": 34490}])), 1)
        self.assertEqual(len(ORPHANS), 23)

    def test_live_cast_helper(self):
        self.assertEqual(live_cast_ms({"CastingTimeIndex": 16, "Attributes": 0x2}, CAST_TIMES), 2000)
        self.assertEqual(live_cast_ms({"CastingTimeIndex": 5, "Attributes": 0x2}, CAST_TIMES), 2500)
        self.assertEqual(live_cast_ms({"CastingTimeIndex": 1, "Attributes": 0x2}, CAST_TIMES), 500)
        self.assertEqual(live_cast_ms({"CastingTimeIndex": 18, "Attributes": 0x2}, CAST_TIMES), 0)
        self.assertEqual(live_cast_ms({"CastingTimeIndex": 16, "Attributes": 0}, CAST_TIMES), 1500)

    def test_mark_guard(self):
        for spell_id in MARKS:
            self.assertEqual(check_mark(spell_id, good_mark(spell_id), CAST_TIMES, DUR15), [], spell_id)
        good = good_mark()
        self.assertEqual(len(check_mark(SNIPERS_MARK, None, CAST_TIMES, DUR15)), 1)
        self.assertEqual(len(check_mark(SNIPERS_MARK, changed(good, CastingTimeIndex=1), CAST_TIMES, DUR15)), 2)
        for key, value in (("SpellClassMask_3", 0x10000000), ("EquippedItemClass", -1), ("CumulativeAura", 0),
                           ("SpellClassMask_2", D1_PET_BIT), ("Attributes", 0x10000), ("ManaCostPct", 0)):
            self.assertEqual(len(check_mark(SNIPERS_MARK, changed(good, **{key: value}), CAST_TIMES, DUR15)), 1, key)
        self.assertEqual(len(check_mark(SNIPERS_MARK, changed(good, EffectAura_3=3), CAST_TIMES, DUR15)), 1)
        self.assertEqual(len(check_mark(SNIPERS_MARK, changed(good, EffectBasePoints_3=0), CAST_TIMES, DUR15)), 1)
        self.assertEqual(len(check_mark(SNIPERS_MARK, changed(good, RecoveryTime=20000), CAST_TIMES, DUR15)), 1)
        self.assertEqual(len(check_mark(SNIPERS_MARK, good, CAST_TIMES, DUR_PERM)), 1)              # duration

    def test_aimed_shot_guard(self):
        row, entry = good_aimed()
        cats = [{"id": 1301}]
        self.assertEqual(check_aimed_shot(row, entry, CAST_TIMES, cats, [], []), [])
        self.assertEqual(len(check_aimed_shot(row, entry, CAST_TIMES, [], [], [])), 1)
        # MM 5.1 as written (index 5): a 2.5 s live cast
        self.assertEqual(len(check_aimed_shot(changed(row, CastingTimeIndex=5), entry, CAST_TIMES, cats, [], [])), 2)
        self.assertEqual(len(check_aimed_shot(changed(row, CastingTimeIndex=18), entry, CAST_TIMES, cats, [], [])), 2)
        self.assertEqual(len(check_aimed_shot(changed(row, Category=85), entry, CAST_TIMES, cats, [], [])), 1)
        self.assertEqual(len(check_aimed_shot(changed(row, RecoveryTime=10000), entry, CAST_TIMES, cats, [], [])), 1)
        self.assertEqual(len(check_aimed_shot(changed(row, SpellClassMask_1=0), entry, CAST_TIMES, cats, [], [])), 1)
        self.assertEqual(len(check_aimed_shot(changed(row, MaxLevel=80), entry, CAST_TIMES, cats, [], [])), 1)
        self.assertEqual(len(check_aimed_shot(changed(row, Effect_2=6), entry, CAST_TIMES, cats, [], [])), 1)
        potent = changed(entry, effect1={"_potency": {"ap_coefficient": 0.43, "sp_coefficient": 0.0}})
        self.assertEqual(len(check_aimed_shot(row, potent, CAST_TIMES, cats, [{"entry": AIMED_SHOT}],
                                              [{"spell_id": AIMED_SHOT}])), 3)

    def test_free_arcane_shot_guard(self):
        free, arcane = good_arcane_pair()
        bonus = GOOD_ARCANE_BONUS

        def check(f=free, a=arcane, bound=GOOD_FREE_BOUND, b=bonus):
            return check_free_arcane_shot(f, a, bound, b)

        self.assertEqual(check(), [])
        # the stale MM 5.10 literal (bp 4 = 0.5%) diverges from 3044's 199
        self.assertEqual(len(check(f=changed(free, EffectBasePoints_2=4))), 1)
        # 3044 retuned while 201933 keeps a literal 199: must fail too
        self.assertEqual(len(check(a=changed(arcane, EffectBasePoints_2=149))), 1)
        self.assertEqual(len(check(f=changed(free, EffectDieSides_2=0))), 1)
        for key, value in (("CastingTimeIndex", 1), ("EquippedItemClass", 2), ("Category", 1173), ("ManaCostPct", 3),
                           ("RecoveryTime", 6000), ("SpellClassMask_1", D0_ARCANE_SHOT | D0_AIMED_SHOT),
                           ("AttributesEx3", 0)):
            self.assertEqual(len(check(f=changed(free, **{key: value}))), 1, key)
        bm = GOOD_FREE_BOUND + [{"spell_id": ARCANE_SHOT_FREE, "ScriptName": "spell_hun_arcane_shot_bm"}]
        self.assertEqual(len(check(bound=bm)), 1)
        self.assertEqual(len(check(bound=GOOD_FREE_BOUND[:1])), 1)
        # m-1: 3044's damage retuned (flat part and per-level slope) while 201933 keeps the old literal
        self.assertEqual(len(check(a=changed(arcane, EffectBasePoints_1=-60, EffectRealPointsPerLevel_1=8.0))), 2)
        self.assertEqual(len(check(f=changed(free, Effect_1=EFFECT_DUMMY))), 2)      # type differs + not SCHOOL_DAMAGE
        # m-1: 3044's ap coefficient retuned (ap_potency 130 -> 150) while 201933's stays
        retuned = [changed(b, ap_bonus=0.64) if b["entry"] == ARCANE_SHOT else b for b in bonus]
        self.assertEqual(len(check(b=retuned)), 1)
        self.assertEqual(len(check(b=[b for b in bonus if b["entry"] != ARCANE_SHOT_FREE])), 1)  # free row lost

    def test_visibility_guard(self):
        rows = {i: {"ID": i, "Attributes": 0, "AttributesEx": 0, "AttributesEx7": 0} for i in VISIBLE}
        rows.update({i: {"ID": i, "Attributes": 0x80 | 0x40, "AttributesEx": ATTR_EX_NO_AURA_ICON} for i in HIDDEN})
        self.assertEqual(check_visibility(rows), [])
        for key, value in (("Attributes", ATTR_PASSIVE), ("Attributes", ATTR_DO_NOT_DISPLAY),
                           ("AttributesEx7", ATTR_EX7_CONSOLIDATE), ("AttributesEx", ATTR_EX_NO_AURA_ICON)):
            bad = {**rows, FALCONS_HASTE: changed(rows[FALCONS_HASTE], **{key: value})}
            self.assertEqual(len(check_visibility(bad)), 1, key)
        self.assertEqual(len(check_visibility({**rows, MASTERY: changed(rows[MASTERY], Attributes=0x40)})), 1)
        self.assertEqual(len(check_visibility({**rows, AIMED_CRIT_HELPER: changed(rows[AIMED_CRIT_HELPER],
                                                                                 AttributesEx=0)})), 1)
        self.assertEqual(len(check_visibility({k: v for k, v in rows.items() if k != FIRE})), 1)

    def test_falcons_haste_guard(self):
        good = {"ID": FALCONS_HASTE, "Effect_1": 6, "EffectAura_1": AURA_HASTE_ALL, "EffectBasePoints_1": -1,
                "DurationIndex": DUR_PERM, "SpellIconID": 1530, "Name_Lang_enUS": "Falcon's Haste", "AttributesEx7": 0}
        self.assertEqual(check_falcons_haste(good, DUR_PERM), [])
        self.assertEqual(len(check_falcons_haste(changed(good, EffectBasePoints_1=1), DUR_PERM)), 1)
        self.assertEqual(len(check_falcons_haste(changed(good, DurationIndex=DUR15), DUR_PERM)), 1)
        self.assertEqual(len(check_falcons_haste(changed(good, Name_Lang_enUS="Falcon's Mark"), DUR_PERM)), 1)
        self.assertEqual(len(check_falcons_haste(changed(good, AttributesEx7=ATTR_EX7_CONSOLIDATE), DUR_PERM)), 1)

    def test_equipped_item_class_guard(self):
        rows = {201930: {"ID": 201930, "EquippedItemClass": -1}, 19426: {"ID": 19426, "EquippedItemClass": 2},
                SNIPERS_MARK: {"ID": SNIPERS_MARK, "EquippedItemClass": 2},
                AIMED_SHOT: {"ID": AIMED_SHOT, "EquippedItemClass": -1}}
        self.assertEqual(check_equipped_item_class(rows, (201930,), (SNIPERS_MARK,)), [])
        self.assertEqual(len(check_equipped_item_class(rows, (19426,), ())), 1)        # pulled Lethal Shots stock 2
        self.assertEqual(len(check_equipped_item_class(rows, (), (AIMED_SHOT,))), 1)   # player-cast shot lost its 2
        self.assertEqual(len(check_equipped_item_class(rows, (201931,), ())), 1)       # undeclared
        self.assertFalse(PLAYER_CAST_SHOTS & set(NEW_S2A_IDS) - set(MARKS))
        self.assertFalse(PLAYER_CAST_SHOTS & set(EDITED_STOCK_HELPERS))
        from lib.test_hunter_bm_data import EQUIPPED_ITEM_CLASS_EXEMPT  # noqa: PLC0415
        self.assertEqual(PLAYER_CAST_SHOTS, EQUIPPED_ITEM_CLASS_EXEMPT, "the two M4 exemption lists must agree")

    def test_family_bit_carrier_guard(self):
        good = [{"ID": i, "SpellClassMask_3": D2_MARK_PRESS} for i in MARKS] + \
               [{"ID": i, "SpellClassMask_3": D2_MARK_DOT} for i in (VIPERS_BITE, VIPERS_VENOM)] + \
               [{"ID": ARCANE_SHOT_FREE, "SpellClassMask_1": D0_ARCANE_SHOT}, {"ID": FIRE},
                {"ID": AIMED_SHOT, "SpellClassMask_1": D0_AIMED_SHOT}, {"ID": ARCANE_SHOT, "SpellClassMask_1": 0x800}]
        self.assertEqual(check_family_bit_carriers(good), [])
        for bad_row in ({"ID": FIRE, "SpellClassMask_1": D0_AIMED_SHOT},           # buff with Aimed's bit: 2 hits
                        {"ID": 201966, "SpellClassMask_3": D2_MARK_PRESS},          # rank with the mark bit: 2 hits
                        {"ID": CONVERGENCE, "SpellClassMask_3": D2_MARK_DOT}):      # Convergence with the DoT bit
            self.assertEqual(len(check_family_bit_carriers(good + [bad_row])), 2, bad_row)
        self.assertEqual(len(check_family_bit_carriers(good + [{"ID": 201999, "SpellClassMask_1": D0_ARCANE_SHOT}])), 1)
        self.assertEqual(check_family_bit_carriers(good + [{"ID": 201934, "SpellClassMask_1": D0_AIMED_SHOT}]), [])
        both = [dict(r) for r in good]
        both[0]["SpellClassMask_1"] = D0_AIMED_SHOT                                  # a mark with a second bit
        self.assertEqual(len(check_family_bit_carriers(both)), 2)

    def test_masks_module_guard(self):
        masks = load_masks_module()
        self.assertEqual(check_masks_module(masks), [])
        fake = type("M", (), {k: v for k, v in SPEC_MASKS.items()})
        self.assertEqual(check_masks_module(fake), [])
        fake.MORTAL_SHOTS_MASK = (0x63A00, 0x80800000, 0x20000A41)                   # the stale stock mask
        self.assertEqual(len(check_masks_module(fake)), 1)

    def test_spellmod_guard(self):
        masks = type("M", (), {k: v for k, v in SPEC_MASKS.items()})
        rows = good_spellmod_rows(masks)
        self.assertEqual(check_spellmod_specs(rows, masks), [])
        # Mortal Shots keeps the stale stock A masks (0x63a00 / 0x20000a41): the stale twin wins
        stale = {**rows, 19485: changed(rows[19485], EffectSpellClassMaskA_1=0x63A00,
                                        EffectSpellClassMaskA_3=0x20000A41)}
        self.assertEqual(len(check_spellmod_specs(stale, masks)), 1)
        # Lethal Shots left at the stock family 0
        self.assertEqual(len(check_spellmod_specs({**rows, 19426: changed(rows[19426], SpellClassSet=0)}, masks)), 1)
        # right dwords on the wrong letter (Sniper Training's DOT mask on effect A instead of B)
        moved = changed(rows[64418], EffectSpellClassMaskB_3=0, EffectSpellClassMaskA_3=D2_MARK_DOT)
        self.assertEqual(len(check_spellmod_specs({**rows, 64418: moved}, masks)), 2)
        # Marked for Death keeps the stale A_2 0x10820000 (pet bit)
        mfd = changed(rows[53241], EffectSpellClassMaskC_2=0x10820000)
        self.assertEqual(len(check_spellmod_specs({**rows, 53241: mfd}, masks)), 1)
        # wrong op on a helper (crit damage on eff0)
        helper = changed(rows[AIMED_CRIT_HELPER], EffectMiscValue_1=OP_CRIT_DAMAGE_BONUS)
        self.assertEqual(len(check_spellmod_specs({**rows, AIMED_CRIT_HELPER: helper}, masks)), 1)
        self.assertEqual(len(check_spellmod_specs({k: v for k, v in rows.items() if k != MASTERY}, masks)), 2)

    def test_removed_effects_and_small_guards(self):
        rows = {i: {"ID": i} for ids, _ in REMOVED_EFFECTS for i in ids}
        self.assertEqual(check_removed_effects(rows), [])
        self.assertEqual(len(check_removed_effects({**rows, 19464: {"ID": 19464, "EffectSpellClassMaskB_2": 128}})), 1)
        self.assertEqual(len(check_removed_effects({**rows, 34485: {"ID": 34485, "Effect_2": 6}})), 1)
        st = {i: {"ID": i, "EffectAura_1": AURA_PERIODIC_TRIGGER_SPELL} for i in SNIPER_TRAINING_RANKS}
        self.assertEqual(check_sniper_training_ranks(st), [])
        stale_st = {**st, 53302: changed(st[53302], EffectSpellClassMaskA_1=0xDE)}
        self.assertEqual(len(check_sniper_training_ranks(stale_st)), 1)
        self.assertEqual(check_chimera_serpent({"ID": CHIMERA_SERPENT, "SpellClassMask_3": 0x800}), [])
        self.assertEqual(len(check_chimera_serpent({"ID": CHIMERA_SERPENT, "SpellClassMask_3": 0xC00})), 1)
        self.assertEqual(check_stampede_family({"ID": STAMPEDE, "SpellClassSet": 0}), [])
        self.assertEqual(len(check_stampede_family({"ID": STAMPEDE, "SpellClassSet": 9})), 1)
        charged = {i: {"ID": i, "ProcCharges": c} for i, (c, _m) in CHARGED_BUFFS.items()}
        charged[RAPID_KILLING_BUFF_ID].update(EffectBasePoints_1=29)
        self.assertEqual(check_charged_buffs(charged), [])
        self.assertEqual(len(check_charged_buffs({**charged, FIRE: {"ID": FIRE, "ProcCharges": 2}})), 1)
        rk = changed(charged[RAPID_KILLING_BUFF_ID], ProcTypeMask=320, EffectRealPointsPerLevel_1=0.167)
        self.assertEqual(len(check_charged_buffs({**charged, RAPID_KILLING_BUFF_ID: rk})), 2)

    def test_pet_bit_reader_guard(self):
        rows = {34482: {"ID": 34482, "EffectSpellClassMaskB_2": 0x90881181}, 53241: {"ID": 53241}}
        self.assertEqual(len(check_no_pet_bit_readers(rows, (34482, 53241), [])), 1)       # Careful Aim r1 stale B_2
        self.assertEqual(check_no_pet_bit_readers(rows, (53241,), []), [])
        self.assertEqual(len(check_no_pet_bit_readers({}, (53234,), [{"SpellId": -53234,
                                                                      "SpellFamilyMask1": D1_PET_BIT}])), 1)

    def test_proc_row_guard(self):
        procs = good_procs()
        self.assertEqual(check_proc_rows(procs), [])
        self.assertEqual(len(check_proc_rows(procs + [dict(procs[2])])), 1)            # -53234 twice (0-verify S5)
        self.assertEqual(len(check_proc_rows([p for p in procs if p["SpellId"] != -34485])), 1)

        def edited(key, **cols):
            return [changed(p, **cols) if p["SpellId"] == key else p for p in procs]

        self.assertEqual(len(check_proc_rows(edited(FIRE, AttributesMask=0x2))), 1)    # triggered casts spend Fire!
        self.assertEqual(len(check_proc_rows(edited(EFFICIENCY_BUFF, SpellPhaseMask=0x2))), 1)
        self.assertEqual(len(check_proc_rows(edited(RAPID_KILLING_BUFF_ID, SpellFamilyMask1=0))), 1)
        self.assertEqual(len(check_proc_rows(edited(PRECISION_R3, HitMask=0))), 1)
        self.assertEqual(len(check_proc_rows(edited(PRECISION_R3, SpellPhaseMask=0x1))), 1)
        self.assertEqual(len(check_proc_rows(edited(RAPID_KILLING_R3, AttributesMask=0))), 1)
        self.assertEqual(len(check_proc_rows(edited(-53234, SpellFamilyMask2=0x20000001))), 1)   # Chimera kept
        self.assertEqual(len(check_proc_rows(edited(-53215, SpellFamilyMask2=0))), 1)            # Steady not added
        neg = [changed(p, SpellId=-PRECISION_R3) if p["SpellId"] == PRECISION_R3 else p for p in procs]
        self.assertEqual(len(check_proc_rows(neg)), 1)                                           # missing positive

    def test_m15_guard(self):
        talents = [{"id": 1806, "tab_id": TAB, "rank_spell_ids": [34482, 34483]},
                   {"id": 1347, "tab_id": TAB, "rank_spell_ids": [19461, 24691]},
                   {"id": 2132, "tab_id": TAB, "rank_spell_ids": [53215, 53217]}]
        rows = {34482: {"ID": 34482, "Effect_1": 6}, 34483: {"ID": 34483, "Effect_1": 6},
                19461: {"ID": 19461, "Effect_1": 6}, 24691: {"ID": 24691, "Effect_1": 6, "ProcTypeMask": 0x100},
                53215: {"ID": 53215, "Effect_1": 6, "ProcTypeMask": 0x140},
                53217: {"ID": 53217, "Effect_1": 6, "ProcTypeMask": 0x140}}
        procs = [{"SpellId": -53215}, {"SpellId": BARRAGE_R3}]
        self.assertEqual(check_m15(rows, talents, procs), [])
        self.assertEqual(len(check_m15(rows, talents, [])), 3)                     # Wild Quiver + Barrage r3 unrowed
        self.assertEqual(len(check_m15(rows, talents, procs[:1])), 1)             # S2b: 24691 is no longer accepted
        stale = {**rows, 34482: changed(rows[34482], EffectSpellClassMaskB_1=0x73A01)}        # mask on absent eff1
        self.assertEqual(len(check_m15(stale, talents, procs)), 1)
        proc = {**rows, 34483: changed(rows[34483], ProcTypeMask=0x100)}
        self.assertEqual(len(check_m15(proc, talents, procs)), 1)
        rk = good_rapid_killing()
        self.assertEqual(check_rapid_killing(rk), [])
        self.assertEqual(len(check_rapid_killing({**rk, 34949: changed(rk[34949], EffectAura_1=42,
                                                                       EffectTriggerSpell_1=35099)})), 1)
        self.assertEqual(len(check_rapid_killing({**rk, 34948: changed(rk[34948], ProcTypeMask=2)})), 1)
        self.assertEqual(len(check_rapid_killing({**rk, RAPID_KILLING_R3: changed(rk[RAPID_KILLING_R3],
                                                                                  ProcTypeMask=0)})), 1)

    def test_binding_guard(self):
        bound, removals, linked = good_bindings()
        self.assertEqual(check_bindings(bound, removals, linked), [])
        self.assertEqual(len(check_bindings(bound + [{"spell_id": -53234, "ScriptName": "spell_hun_piercing_shots_mm"}],
                                            removals, linked)), 1)
        self.assertEqual(len(check_bindings(bound, removals[:1], linked)), 1)
        self.assertEqual(len(check_bindings(bound, removals, [])), 2)                           # both links
        rebind = removals + [{"spell_id": 23989, "ScriptName": "spell_hun_readiness"}]
        self.assertEqual(len(check_bindings(bound, rebind, linked)), 1)
        self.assertEqual(len(check_bindings([b for b in bound if b["spell_id"] != ARCANE_SHOT_FREE], removals,
                                            linked)), 1)
        # S2b (q)
        self.assertEqual(len(check_bindings(bound, removals, linked[:1])), 1)                   # 201982 link lost
        self.assertEqual(len(check_bindings(bound, removals, [{**linked[1], "type": 0}, linked[0]])), 1)
        neg = [changed(b, spell_id=-19407) if b["spell_id"] == 19407 else b for b in bound]
        self.assertEqual(len(check_bindings(neg, removals, linked)), 1)                         # chain key
        bounce = bound + [{"spell_id": BOUNCE, "ScriptName": "spell_hun_aimed_shot_ricochet"}]
        self.assertEqual(len(check_bindings(bounce, removals, linked)), 2)                      # wrong set + no script
        self.assertEqual(len(check_bindings(bound + [{"spell_id": LONE_SURVIVOR_BUFF, "ScriptName": "x"}], removals,
                                            linked)), 1)
        unbound = removals + [{"spell_id": -VOLLEY_TICK, "ScriptName": "spell_hun_volley_trigger"}]
        self.assertEqual(len(check_bindings(bound, unbound, linked)), 1)
        self.assertEqual(len(check_bindings([b for b in bound if b["spell_id"] != HALF_VOLLEY_TICK], removals,
                                            linked)), 1)

    def test_pack_shot_guard(self):
        rows = good_pack_rows()
        self.assertEqual(check_pack_shots(rows, 50), [])
        self.assertEqual(len(check_pack_shots(rows, None)), 1)
        for key, value in (("SpellClassMask_1", 0), ("SpellClassMask_3", D2_HALF_VOLLEY), ("CastingTimeIndex", 1),
                           ("EquippedItemClass", 2), ("DefenseType", 1), ("RecoveryTime", 10000),
                           ("Speed", 40.0), ("AttributesEx3", 0), ("EffectBasePoints_1", 0),
                           ("EffectBasePoints_2", 219)):
            bad = {**rows, RICOCHET: changed(rows[RICOCHET], **{key: value})}
            self.assertEqual(len(check_pack_shots(bad, 50)), 1, key)
        # Aimed Shot retuned to 250 while A1's private 220 stays: the copies keep 110, expected 125 (+ the B2 literal)
        aimed = {**rows, AIMED_SHOT: changed(rows[AIMED_SHOT], EffectBasePoints_2=249)}
        self.assertEqual(len(check_pack_shots(aimed, 50)), 3)
        self.assertEqual(len(check_pack_shots({k: v for k, v in rows.items() if k != BOUNCE}, 50)), 1)
        self.assertEqual(live_weapon_potency({"EffectBasePoints_2": 109, "EffectDieSides_2": 1}, 2), 110)

    def test_half_volley_guard(self):
        volley, v_entry, tick, t_entry, bonus = good_half_volley()

        def check(v=volley, ve=v_entry, t=tick, te=t_entry, b=bonus):
            return check_half_volley(v, ve, t, te, b, 30112)

        self.assertEqual(check(), [])
        for key, value in (("SpellClassMask_3", 0), ("AttributesEx5", ATTR_EX5_HASTE_AFFECT_DURATION),
                           ("Attributes", 0), ("DurationIndex", 30100), ("EquippedItemClass", 2),
                           ("AttributesEx3", 0), ("Targets", 0)):
            self.assertEqual(len(check(v=changed(volley, **{key: value}))), 1, key)
        self.assertEqual(len(check(v=changed(volley, EffectAuraPeriod_2=500))), 2)        # period + 6 ticks
        no_basis = changed(v_entry, effect1={"_potency": {**v_entry["effect1"]["_potency"], "t_seconds": 3.0}})
        self.assertEqual(len(check(ve=no_basis)), 1)                                        # time_basis_ms dropped
        self.assertEqual(len(check(b=[bonus[0], {"entry": VOLLEY_TICK, "ap_bonus": 0.4}])), 1)
        for key, value in (("SpellClassMask_3", D2_HALF_VOLLEY), ("AttributesEx3", ATTR_EX3_SUPPRESS_CASTER_PROCS),
                           ("EquippedItemClass", 2), ("ImplicitTargetB_1", 15)):
            self.assertEqual(len(check(t=changed(tick, **{key: value}))), 1, key)
        self.assertEqual(len(check(te={"id": HALF_VOLLEY_TICK, "effect1": {}})), 1)         # potency not excluded
        self.assertEqual(len(check(b=bonus + [{"entry": HALF_VOLLEY_TICK, "ap_bonus": 0.3}])), 1)
        self.assertEqual(len(check(t=None)), 1)

    def test_half_volley_reach_guard(self):
        fake = type("M", (), dict(SPEC_MASKS))

        def eff0(spell_id, name):
            return {"ID": spell_id, **{f"EffectSpellClassMaskA_{n}": w for n, w in enumerate(SPEC_MASKS[name], 1)}}

        rows = {i: eff0(i, "BARRAGE_DAMAGE") for i in BARRAGE_RANKS}
        rows.update({i: eff0(i, "VOLLEY_DAMAGE") for i in RAIN_OF_ARROWS_RANKS})
        self.assertEqual(check_half_volley_reach(fake, rows), [])
        lost = type("M", (), {**SPEC_MASKS, "VOLLEY_DAMAGE": (0x2000, 0, 0)})
        self.assertEqual(len(check_half_volley_reach(lost, rows)), 3)                       # mask + both RoA ranks
        stale = {**rows, BARRAGE_R3: changed(rows[BARRAGE_R3], EffectSpellClassMaskA_3=0)}
        self.assertEqual(len(check_half_volley_reach(fake, stale)), 1)

    def test_family_bit_s2b_guard(self):
        good = [{"ID": AIMED_SHOT, "SpellClassSet": 9, "SpellClassMask_1": D0_AIMED_SHOT},
                {"ID": RICOCHET, "SpellClassSet": 9, "SpellClassMask_1": D0_AIMED_SHOT},
                {"ID": BOUNCE, "SpellClassSet": 9, "SpellClassMask_1": D0_AIMED_SHOT},
                {"ID": HALF_VOLLEY, "SpellClassSet": 9, "SpellClassMask_3": D2_HALF_VOLLEY},
                {"ID": HALF_VOLLEY_TICK, "SpellClassSet": 9}, {"ID": 20900, "SpellClassSet": 4,
                                                               "SpellClassMask_1": D0_AIMED_SHOT}]   # other family
        self.assertEqual(check_family_bit_carriers(good), [])
        self.assertEqual(len(check_family_bit_carriers(good + [{"ID": 20901, "SpellClassSet": 9,
                                                                "SpellClassMask_1": D0_AIMED_SHOT}])), 1)
        self.assertEqual(len(check_family_bit_carriers(good + [{"ID": 42243, "SpellClassSet": 9,
                                                                "SpellClassMask_3": D2_HALF_VOLLEY}])), 1)
        tick = [changed(r, SpellClassMask_3=D2_HALF_VOLLEY) if r["ID"] == HALF_VOLLEY_TICK else r for r in good]
        self.assertEqual(len(check_family_bit_carriers(tick)), 2)                           # d2 b30 + no-bit id
        for sid in (LONE_SURVIVOR_BUFF, COMBAT_EXPERIENCE_CAPSTONE):
            self.assertEqual(len(check_family_bit_carriers(good + [{"ID": sid, "SpellClassMask_2": 0x1}])), 1, sid)
        extra = [changed(r, SpellClassMask_2=0x1) if r["ID"] == BOUNCE else r for r in good]
        self.assertEqual(len(check_family_bit_carriers(extra)), 1)                          # bounce mask not exact
        wide = [changed(r, SpellClassMask_1=D0_MULTI_SHOT) if r["ID"] == HALF_VOLLEY else r for r in good]
        self.assertEqual(len(check_family_bit_carriers(wide)), 1)

    def test_barrage_proc_guard(self):
        procs = good_procs()
        self.assertEqual(check_proc_rows(procs), [])
        self.assertEqual(check_barrage_chain_proc(procs), [])

        def edited(**cols):
            return [changed(p, **cols) if p["SpellId"] == BARRAGE_R3 else p for p in procs]

        for key, value in (("SpellPhaseMask", PROC_PHASE_HIT), ("Cooldown", 0), ("DisableEffectsMask", 0),
                           ("ProcFlags", 0x110), ("SpellFamilyMask0", 0x3000), ("AttributesMask", 0x2),
                           ("SpellFamilyName", 0), ("Chance", 100.0)):
            self.assertEqual(len(check_proc_rows(edited(**{key: value}))), 1, key)
        self.assertEqual(len(check_proc_rows([p for p in procs if p["SpellId"] != BARRAGE_R3])), 1)
        chain = [changed(p, SpellId=-19461) if p["SpellId"] == BARRAGE_R3 else p for p in procs]
        self.assertEqual(len(check_barrage_chain_proc(chain)), 1)
        self.assertEqual(len(check_barrage_chain_proc(procs + [{"SpellId": 19462}])), 1)

    def test_lone_survivor_and_capstone_guard(self):
        rows = good_lone_and_capstone()
        self.assertEqual(check_lone_survivor_and_capstone(rows, DUR_PERM), [])
        for key, value in (("AttributesEx7", ATTR_EX7_CONSOLIDATE), ("DurationIndex", DUR15),
                           ("EffectMiscValue_1", 1), ("EquippedItemClass", 2)):
            bad = {**rows, LONE_SURVIVOR_BUFF: changed(rows[LONE_SURVIVOR_BUFF], **{key: value})}
            self.assertEqual(len(check_lone_survivor_and_capstone(bad, DUR_PERM)), 1, key)
        for key, value in (("Attributes", 0x40), ("EffectMiscValue_1", 1), ("EffectAuraPeriod_2", 500)):
            bad = {**rows, COMBAT_EXPERIENCE_CAPSTONE: changed(rows[COMBAT_EXPERIENCE_CAPSTONE], **{key: value})}
            self.assertEqual(len(check_lone_survivor_and_capstone(bad, DUR_PERM)), 1, key)
        self.assertEqual(len(check_lone_survivor_and_capstone({}, DUR_PERM)), 2)
        # M1 lists: 201950 visible, 201952 / 201936 hidden
        vis = {i: {"ID": i} for i in VISIBLE}
        vis.update({i: {"ID": i, "Attributes": 0x80 | 0x40, "AttributesEx": ATTR_EX_NO_AURA_ICON} for i in HIDDEN})
        self.assertEqual(check_visibility(vis), [])
        self.assertEqual(len(check_visibility({**vis, LONE_SURVIVOR_BUFF: {"ID": LONE_SURVIVOR_BUFF,
                                                                           "Attributes": 0x40}})), 1)
        self.assertEqual(len(check_visibility({**vis, COMBAT_EXPERIENCE_CAPSTONE: {"ID": COMBAT_EXPERIENCE_CAPSTONE,
                                                                                   "Attributes": 0x40}})), 1)
        self.assertEqual(len(check_visibility({**vis, HALF_VOLLEY: {"ID": HALF_VOLLEY, "Attributes": 0}})), 1)

    def test_half_volley_level_guard(self):
        rows = {HALF_VOLLEY: {"ID": HALF_VOLLEY, "SpellLevel": 40}, VOLLEY_TICK: {"ID": VOLLEY_TICK, "SpellLevel": 40}}
        self.assertEqual(check_half_volley_level(rows), [])
        self.assertEqual(len(check_half_volley_level({**rows, HALF_VOLLEY: changed(rows[HALF_VOLLEY],
                                                                                   SpellLevel=60)})), 1)
        both_zero = {i: changed(r, SpellLevel=0) for i, r in rows.items()}
        self.assertEqual(len(check_half_volley_level(both_zero)), 1)
        self.assertEqual(len(check_half_volley_level({HALF_VOLLEY: rows[HALF_VOLLEY]})), 1)

    def test_ignore_line_of_sight_guard(self):
        rows = {i: {"ID": i, "AttributesEx2": ATTR_EX2_IGNORE_LINE_OF_SIGHT} for i in IGNORE_LOS_IDS}
        self.assertEqual(check_ignore_line_of_sight(rows), [])
        for spell_id in IGNORE_LOS_IDS:
            bad = {**rows, spell_id: changed(rows[spell_id], AttributesEx2=0x20000)}    # another Ex2 bit only
            self.assertEqual(len(check_ignore_line_of_sight(bad)), 1, spell_id)
        self.assertEqual(len(check_ignore_line_of_sight({k: v for k, v in rows.items() if k != CONVERGENCE})), 1)

    def test_cannot_be_saved_guard(self):
        attrs = [{"spell_id": i, "attributes": CUSTOM_ATTR_CANNOT_BE_SAVED} for i in CANNOT_BE_SAVED_S2B_IDS]
        self.assertEqual(check_cannot_be_saved(attrs), [])
        self.assertEqual(len(check_cannot_be_saved([a for a in attrs if a["spell_id"] != HALF_VOLLEY])), 1)
        wrong = [changed(a, attributes=0x200000) if a["spell_id"] == HALF_VOLLEY else a for a in attrs]
        self.assertEqual(len(check_cannot_be_saved(wrong)), 1)
        self.assertEqual(len(check_cannot_be_saved(attrs + [{"spell_id": HALF_VOLLEY, "attributes": 0x1}])), 1)

    def test_pack_shot_cast_guard(self):
        self.assertEqual(check_pack_shot_casts(""), ([], 0))                                  # no casts yet
        self.assertEqual(check_pack_shot_casts(GOOD_CASTS_CPP), ([], 3))
        for bad_line in ("player->CastSpell(unit, HunterData::SPELL_AIMED_SHOT_RICOCHET, TRIGGERED_NONE);",
                         "player->CastSpell(unit, HunterData::SPELL_AIMED_SHOT_BOUNCE, true);",
                         "player->CastSpell(unit, 201934, TRIGGERED_IGNORE_GCD);",
                         "player->CastSpell(unit, HunterData::SPELL_AIMED_SHOT_RICOCHET,\n"
                         "    TriggerCastFlags(TRIGGERED_FULL_MASK & ~TRIGGERED_IGNORE_SPELL_AND_CATEGORY_CD));",
                         "player->CastSpell(unit, shotId, TRIGGERED_IGNORE_POWER_AND_REAGENT_COST);",
                         "player->CastCustomSpell(HunterData::SPELL_AIMED_SHOT_BOUNCE, SPELLVALUE_BASE_POINT0, bp, "
                         "unit, TRIGGERED_NONE);"):
            problems, seen = check_pack_shot_casts(GOOD_CASTS_CPP + bad_line)
            self.assertEqual((len(problems), seen), (1, 4), bad_line)
        info = ("SpellInfo const* info = sSpellMgr->GetSpellInfo(HunterData::SPELL_AIMED_SHOT_RICOCHET);\n"
                "player->CastSpell(targets, info, nullptr, TRIGGERED_IGNORE_GCD);")
        self.assertEqual(len(check_pack_shot_casts(info)[0]), 1)                               # alias through a lookup

    def test_advantaged_state_guard(self):
        self.assertEqual(check_advantaged_state(GOOD_ADVANTAGED), [])
        self.assertEqual(len(check_advantaged_state(None)), 1)
        stock = changed(GOOD_ADVANTAGED, Effect_2=EFFECT_APPLY_AURA, EffectAura_2=AURA_MOD_RANGED_HASTE,
                        EffectBasePoints_2=14, EffectDieSides_2=1)
        self.assertEqual(len(check_advantaged_state(stock)), 2)                            # haste back + eff1 present
        zeroed = changed(GOOD_ADVANTAGED, Effect_2=EFFECT_APPLY_AURA, EffectAura_2=AURA_MOD_RANGED_HASTE,
                         EffectBasePoints_2=-1, EffectDieSides_2=1)
        self.assertEqual(len(check_advantaged_state(zeroed)), 2)                           # an aura 140 effect is left
        self.assertEqual(len(check_advantaged_state(changed(GOOD_ADVANTAGED, Effect_1=0, EffectAura_1=0,
                                                            EffectTriggerSpell_1=0))), 3)   # eff0 dropped too
        self.assertEqual(len(check_advantaged_state(changed(GOOD_ADVANTAGED, EquippedItemClass=2))), 1)

    def test_learnable_ranged_haste_guard(self):
        sla, talents, trainer, linked = good_learnable_sources()
        learnable = hunter_learnable_ids(sla, talents, trainer, linked)
        self.assertEqual(learnable, {ADVANTAGED_STATE, 34466, 34467, 34468, 3045, 201999})
        clean = {ADVANTAGED_STATE: GOOD_ADVANTAGED, 34469: haste_passive(34469, bp=15, effect=1),
                 34470: haste_passive(34470, bp=19, effect=1), 44972: haste_passive(44972),
                 3045: haste_passive(3045, bp=39, effect=1, attributes=0x40010)}       # castable: not passive
        self.assertEqual(check_no_learnable_ranged_haste(clean, learnable), [])
        # the stock 34082 back: fails
        self.assertEqual(len(check_no_learnable_ranged_haste({**clean, ADVANTAGED_STATE: haste_passive(
            ADVANTAGED_STATE)}, learnable)), 1)
        # an orphan wired back into a talent: fails
        wired = talents + [{"ID": 1803, "TabID": 361, "SpellRank_1": 34469}]
        self.assertEqual(len(check_no_learnable_ranged_haste(clean, hunter_learnable_ids(sla, wired, trainer,
                                                                                          linked))), 1)
        # an auto-learned orphan (AcquireMethod 0 -> 2): fails
        auto = [changed(r, AcquireMethod=2) if r["Spell"] == 34469 else r for r in sla]
        self.assertEqual(len(check_no_learnable_ranged_haste(clean, hunter_learnable_ids(auto, talents, trainer,
                                                                                         linked))), 1)
        # a linked type-2 passive of a talent rank: fails
        self.assertEqual(len(check_no_learnable_ranged_haste({**clean, 201999: haste_passive(201999)}, learnable)), 1)
        # aura 140 with amount 0 (bp -1 die 1) is not haste; die sides > 1 is
        self.assertEqual(check_no_learnable_ranged_haste({**clean, 34466: haste_passive(34466, bp=-1)}, learnable),
                         [])
        self.assertEqual(len(check_no_learnable_ranged_haste({**clean, 34466: haste_passive(34466, bp=-1, die=3)},
                                                             learnable)), 1)

    def test_multi_shot_guard(self):
        good = {"ID": MULTI_SHOT, **MULTI_SHOT_FIELDS, "Speed": 30.0}
        self.assertEqual(check_multi_shot(good), [])
        for key, value in (("CastingTimeIndex", 18), ("EffectChainTargets_1", 5), ("SpellClassMask_1", 0x3000),
                           ("EquippedItemClass", -1), ("Speed", 0.0)):
            self.assertEqual(len(check_multi_shot(changed(good, **{key: value}))), 1, key)
        self.assertEqual(len(check_multi_shot(None)), 1)


if __name__ == "__main__":
    unittest.main()
