"""
Hunter S3a (Survival) built-row guards (hunter-rework S3a-HANDOFF WP-A table row A5, A1-A20; S3a-WP-BRIEF resolutions
1-13; S3-HANDOFF stale lines 1-29, lessons N1-N15 and user rulings 1-10; SURVIVAL.md 2.1-2.5, 5, 6, 8.1, 9.3).

Written from the spec, not from the DSL: every expected value below is the spec's. Loads the real hunter DSL package
(the shared loader of `test_hunter_pet_data.py`, one load per process) and asserts on the BUILT rows (stock base + DSL +
raw_overrides via `build.build_spell_row`), so a stale raw twin that wins fails here too:

  (a) tab 362 (A1, SURVIVAL 2.2 / 6): the 34 talents at their cells with their rank lists, 83 points, one talent per
      cell, no prerequisite (entry, raw override, built row), castable rows flags=1 and every other row flags=0,
      SkillLineAbility 30547-30550 on skill line 51 / class mask 4 (the tab's skill_line=51 derives them) and no other
      derived SLA row for a tab-362 rank, no trainer row for a talent spell (L13); tab 363 still 33 / 81 with Sniper
      Training 2143 at (7,2); Talent.dbc's tab blocks contiguous after order_talent_rows; every rank of tab 362 and
      every 202080-202108 rank in exactly one talent row, under a DSL variable;
  (b) the 25 orphaned ranks (0-chars / 0-verify 5b) in no talent row of stock Talent.dbc overlaid by the package;
  (c) the four castables (A4, stale line 14): Attributes 0x50000 (no USES_RANGED_SLOT), CastingTimeIndex 1, live cast
      0, EquippedItemClass -1, GCD 1500 / 133, their one family bit, not an `_is_hunter_shot` row, SpellLevel = learn
      level (N2), plus the per-spell shape of 5.1 / 5.3 / 5.4 / 5.8;
  (d) Explosive Shot 53301 (A5, stale line 1, brief 7): index 18 / live cast 0 / class 2, eff0 SCHOOL_DAMAGE 76.5 AP
      direct, eff1 bare PERIODIC_DUMMY 1000 ms (no potency, no potency_excluded), Ex5 0x200 cleared, SpellLevel 30 and
      no raw BaseLevel / MaxLevel key in its spell() call; `check_ranged_shot_cast_bars` sees it; the blast 53352
      carries the only blast potency (26 AP, generated spell_bonus_data replaces 0.16), Ex2 0x4, class -1, no stale
      A_1 mask; the splashes 202054 / 202055 are A 87 / B 16 + Targets 0x40 (brief 2), SUPPRESS + IGNORE_CASTER_MODS;
  (e) LoS / procs (stale line 12, N3): AttributesEx2 0x4 on exactly {202048, 202049, 202050, 202053, 202056, 202057,
      202059} among 202040-202159 (and stock 53352); AttributesEx3 0x10000 on the no-proc helpers only;
  (f) M1 visibility (stale line 13): the visible buffs / debuffs and the hidden helpers;
  (g) N5: EquippedItemClass -1 on every id S3a declares or edits except 53301 / 19386 / 19503 / 3674 (class 2), and
      those four in both exemption sets (test_hunter_bm_data / test_hunter_mm_data);
  (h) SpellMods (N7): every aura 107/108 effect of an S3a id is SpellClassSet 9 with a non-zero mask; the SURVIVAL 6
      ops and masks; `_masks.py` holds the SURVIVAL 2.5 composites;
  (i) spell_proc rows (SURVIVAL 8.1, stale line 8, A11 / A12; S3b A4): the 14 S3a rows and the 3 S3b rows (202048,
      -56342, 56453) exactly once, their columns, no negative / positive twin; the proc carriers' DBC ProcTypeMask /
      ProcChance / trigger (Lock and Load included); N8: every tab-362 rank with ProcTypeMask != 0 has a row (nothing is
      listed inert any more), no mask on an absent effect;
  (j) Thrill of the Hunt (SV-B1, stale line 9): ProcChance 50 / 100, ProcTypeMask 0x100, eff1 DUMMY 1000 ms live on
      both, no A_1 mask, 34498's family bits stripped;
  (k) family bits (SURVIVAL 2.4, 0.17): d1 b19 / b6 / b26 / b27 and d2 b5 on exactly their carriers, 3674 / 19306 /
      34498 stripped, no bit on any buff / helper / rank; no reader mask of an S3a id holds d1 b28;
  (l) stale line 19: Serpent Sting 1978 eff1 amount 0 and no taught hunter SPELLMOD_EFFECT2 reader on d0 0x4000; the
      stale raw readers S3a deletes (Ferocious Inspiration, Invigoration, Point of No Escape, Black Arrow eff1);
  (m) Favored Prey spell_group 1242 = 202063-202072, rule 1 (exclusive); the four linked_spell type-2 rows;
  (n) bindings (brief script table): every S3a and S3b class on exactly its positive keys, the exact unbinds (-53301,
      -53290; S3b: -56342, -19386); stock spell_hun_thrill_of_the_hunt / spell_hun_glaive_toss / shot mana /
      spell_hun_disengage kept;
  (o) user ruling 6: 202081's eff2 marker (live 5, no mask), Raptor Strike 2973's text has no mana clause, Deadly
      Focus r2's capstone names Raptor Strike's 5% base mana;
  (p) the S2-FIX guards (N1) still pass on the whole package with the SV rows in it;
  (q) S3b data (S3b-HANDOFF A4 row, 0-verify binding decisions): Lock and Load 56342-56344 / 56453 / 67544 values, the
      Explosive Trap pair 13812 eff1 (aura 226, stock bp / amplitude) and 202057 (ppl 0, potency_excluded, Ex3), Wyvern
      Sting 19386 (aura 79 / misc 127 / bp -31, 2000 ms, no interrupt / proc mask / mechanic, class 2), the S3b helpers'
      CastingTimeIndex 1 (C-3) and the 0x4 list.

Every check is a pure function; the negative-fixture class feeds each one a good input (must pass) and crafted bad
copies (must fail), so a check that silently passes everything is caught.

Run directly:

    apps/dbc-tools/.venv/bin/python3 -m pytest apps/dbc-tools/lib/test_hunter_sv_data.py -q
"""

from __future__ import annotations

import copy
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import build, dbcfile, dbcfmt, state  # noqa: E402
from lib.dsl import SpellModOp  # noqa: E402
from lib.test_hunter_mm_data import (  # noqa: E402
    _amount_nonzero, _cast_times, _hex, _i, _is_hunter_shot, check_equipped_item_class, check_instant_cast_mods,
    check_no_pet_bit_readers, check_orphans, check_ranged_shot_cast_bars, check_visibility, effect_mask,
    live_cast_ms, load_masks_module, proc_mask, resolve_mask, spell_mask,
)
from lib.test_hunter_pet_data import package_data  # noqa: E402

TOOL_ROOT = Path(__file__).resolve().parents[1]
HUNTER_DIR = TOOL_ROOT / "source" / "classes" / "hunter"
HUNTER_SPELLS_PY = HUNTER_DIR / "hunter_spells.py"

SPELLFAMILY_HUNTER = 9
LETTERS = ("A", "B", "C")

# effect / aura ids (SpellEffects.h, SpellAuraDefines.h)
EFFECT_SCHOOL_DAMAGE = 2
EFFECT_DUMMY = 3
EFFECT_APPLY_AURA = 6
EFFECT_TRIGGER_SPELL = 64
AURA_DUMMY = 4
AURA_MOD_ROOT = 26
AURA_PROC_TRIGGER_SPELL = 42
AURA_MOD_TOTAL_STAT_PERCENTAGE = 137
AURA_MOD_RANGED_ATTACK_POWER_PCT = 167
AURA_MOD_RANGED_AP_OF_STAT_PERCENT = 212
AURA_PERIODIC_DUMMY = 226
AURA_PROC_TRIGGER_SPELL_WITH_VALUE = 231
AURA_MOD_DAMAGE_FROM_CASTER = 271
AURA_MOD_CRIT_PCT = 290
AURA_ADD_FLAT_MODIFIER = 107
AURA_ADD_PCT_MODIFIER = 108
SPELLMOD_AURAS = {AURA_ADD_FLAT_MODIFIER, AURA_ADD_PCT_MODIFIER}
FLAT, PCT = AURA_ADD_FLAT_MODIFIER, AURA_ADD_PCT_MODIFIER
OP = SpellModOp
MECHANIC_ROOT = 7

ATTR_USES_RANGED_SLOT = 0x2
ATTR_PASSIVE = 0x40
ATTR_DO_NOT_DISPLAY = 0x80
ATTR_CASTABLE = 0x50000                    # SURVIVAL 5 common rules (castables), stale line 14
ATTR_EXPLOSIVE_SHOT = 0x10802              # stock 53301, kept (stale line 1)
ATTR_EX2_IGNORE_LINE_OF_SIGHT = 0x4
ATTR_EX2_CANT_CRIT = 0x20000000
ATTR_EX3_SUPPRESS_CASTER_PROCS = 0x10000
ATTR_EX3_IGNORE_CASTER_MODIFIERS = 0x20000000
ATTR_EX5_EXTRA_INITIAL_TICK = 0x200        # SPELL_ATTR5_EXTRA_INITIAL_PERIOD (3 ticks instead of 2)
TARGET_FLAG_DEST_LOCATION = 0x40
DEFENSE_RANGED = 3
SCHOOL_FIRE = 4

D0_MONGOOSE_BITE = 0x2
D0_EXPLOSIVE_TRAP_EFFECT = 0x4
D0_FROST_TRAP_AURA = 0x10
D0_TRAP = 0x80
D0_SERPENT_STING = 0x4000
D1_DETERRENCE = 0x2
D1_WILDFIRE_BOMB = 0x40                    # d1 b6
D1_WYVERN_STING = 0x1000                   # d1 b12
D1_SNAKE_TRAP_EFFECT = 0x2000
D1_DISENGAGE = 0x4000
D1_MANTIS_STRIKE = 0x80000                 # d1 b19
D1_TAR_BOMB = 0x4000000                    # d1 b26
D1_BURNING_TAR = 0x8000000                 # d1 b27
D1_PET_BIT = 0x10000000                    # d1 b28
D1_EXPLOSIVE_SHOT = 0x80000000             # d1 b31
D2_CLUSTER_BOMBS = 0x20                    # d2 b5
D2_GLAIVE_TOSS = 0x40
D2_EXPLOSIVE_SHOT_TICK = 0x200             # d2 b9

PROC_PHASE_CAST, PROC_PHASE_HIT, PROC_PHASE_FINISH = 0x1, 0x2, 0x4
PROC_FLAG_DONE_RANGED_AUTO = 0x40
PROC_FLAG_DONE_SPELL_RANGED = 0x100
PROC_FLAG_TRAP_ACTIVATION = 0x200000
PROC_ATTR_TRIGGERED_CAN_PROC = 0x2

# ---- ids -------------------------------------------------------------------------------------------------------------
TAB, MM_TAB = 362, 363
SNIPER_TRAINING_ROW, SNIPER_TRAINING_RANKS = 2143, (53302, 53303, 53304)
MANTIS_STRIKE, MANTIS_ENABLE, MONGOOSE_FURY, PREDATORS_GUARD_BUFF, SCAVENGER = 202040, 202041, 202042, 202043, 202044
WILDFIRE_BOMB, TAR_BOMB, TARRED, TAR, BURNING_TAR = 202045, 202047, 202048, 202049, 202050
CLUSTER_BOMBS, CLUSTER_BOMBS_BLAST, SHRAPNEL_HIT = 202051, 202052, 202053
SPLASH, BLAST_SPLASH, IGT_SLOW, TRAP_FIRE, PONE_MARKER = 202054, 202055, 202056, 202057, 202058
WYVERN_SLEEP, SURVIVALIST_SPEED, SURVIVALIST_DETERRENCE, TNT_MASTERY = 202059, 202060, 202061, 202062
FAVORED_PREY_BUFFS = tuple(range(202063, 202073))
EXPLOSIVE_SHOT, EXPLOSIVE_BLAST = 53301, 53352
EXPOSE_WEAKNESS_BUFF, MASTER_TACTICIAN_BUFF, ENTRAPMENT_ROOT, GLYPH_EXPLOSIVE_SHOT = 34501, 34837, 64804, 63066
RAPTOR_STRIKE, MONGOOSE_BITE, SERPENT_STING, BLACK_ARROW, COUNTERATTACK, GLAIVE_TOSS = 2973, 1495, 1978, 3674, 19306, \
    201600
SCATTER_SHOT, WYVERN_STING = 19503, 19386
DEADLY_FOCUS = (202080, 202081)
THRILL = (34497, 34498)
LOCK_AND_LOAD = (56342, 56343, 56344)
LOCK_AND_LOAD_BUFF, LOCK_AND_LOAD_MARKER = 56453, 67544
LOCK_AND_LOAD_PROC_TYPE = 0x240000                  # DBC ProcTypeMask of 56342-56344 (stock, kept)
EXPLOSIVE_TRAP_EFFECT, FROST_TRAP_AURA, FREEZING_TRAP_EFFECT = 13812, 13810, 3355
CASTABLES = (MANTIS_STRIKE, WILDFIRE_BOMB, TAR_BOMB, CLUSTER_BOMBS)
SPLASHES = (SPLASH, BLAST_SPLASH)
NEW_HELPER_IDS = (*range(202040, 202046), *range(202047, 202073))      # 202046 stays reserved (SURVIVAL 2.1)
NEW_RANK_IDS = tuple(range(202080, 202109))
NEW_IDS = (*NEW_HELPER_IDS, *NEW_RANK_IDS)                              # 61 new rows
SV_BLOCK = range(202040, 202160)

# SURVIVAL 2.2 / 6 (A1, stale line 7): talent id -> ((tier, column), rank spell ids)
TAB_LAYOUT = {
    1820: ((0, 0), DEADLY_FOCUS),
    1310: ((0, 1), (19290, 19294, 24283)),
    1623: ((0, 3), (202082, 202083, 202084)),
    1621: ((1, 0), (202085, 202086, 202087)),
    60250: ((1, 1), (202088, 202089, 202090)),
    1305: ((1, 2), (19376, 63457, 63458)),
    1810: ((1, 3), (34494, 34496, 202091)),
    60251: ((2, 1), (WILDFIRE_BOMB,)),
    1814: ((2, 2), (SCATTER_SHOT,)),
    1622: ((2, 3), (19255, 19256, 19257)),
    1311: ((3, 0), (202092, 202093, 202094)),
    60252: ((3, 1), (202095, 202096, 202097)),
    1306: ((3, 2), LOCK_AND_LOAD),
    1309: ((3, 3), (19286, 19287)),
    1312: ((4, 0), (MANTIS_STRIKE,)),
    2145: ((4, 1), (EXPLOSIVE_SHOT,)),
    1304: ((4, 2), (19184, 19387, 19388)),
    2228: ((4, 3), (56339, 56340, 56341)),
    1321: ((5, 0), (19370, 19371, 19373)),
    60253: ((5, 1), (202098, 202099)),
    1809: ((5, 2), (34491, 34492, 34493)),
    1303: ((5, 3), (19168, 19180, 19181)),
    60254: ((6, 0), (202100, 202101, 202102)),
    1325: ((6, 1), (WYVERN_STING,)),
    1811: ((6, 2), THRILL),
    1812: ((6, 3), (34500, 34502, 34503)),
    60255: ((7, 1), (202103, 202104, 202105)),
    2142: ((7, 2), (53298, 53299, 202106)),
    1813: ((7, 3), (34506, 34507, 34508)),
    1322: ((8, 1), (TAR_BOMB,)),
    2229: ((8, 2), (56333, 56336, 56337)),
    2141: ((9, 1), (202107, 202108)),
    2144: ((9, 3), (53290, 53291, 53292)),
    60256: ((10, 1), (CLUSTER_BOMBS,)),
}
TAB_TALENT_COUNT, TAB_POINTS = 34, 83
MM_TAB_TALENT_COUNT, MM_TAB_POINTS = 33, 81
CASTABLE_ROWS = frozenset({60251, 1814, 1312, 2145, 1325, 1322, 60256})
SV_SLA = {30547: MANTIS_STRIKE, 30548: WILDFIRE_BOMB, 30549: TAR_BOMB, 30550: CLUSTER_BOMBS}
SKILL_LINE_SV = 51
CLASSMASK_HUNTER = 4
TAB_RANKS = tuple(sorted({sid for _, ranks in TAB_LAYOUT.values() for sid in ranks}))
# 0-verify 5b / 0-chars "verified orphan list" (25 ids; 53302-53304 are Sniper Training's live tab-363 ranks, not
# orphans of tab 362, and are checked separately)
ORPHANS = (3674, 19159, 19160, 19258, 19259, 19295, 19297, 19298, 19306, 19498, 19499, 19500, 24296, 24297, 34499,
           34838, 34839, 52783, 52785, 52786, 52787, 52788, 53295, 53296, 53297)

# (c) the castables: id -> (SpellClassMask, SpellLevel = learn level, unit-targeted)
CASTABLE_SPECS = {
    MANTIS_STRIKE: ((0, D1_MANTIS_STRIKE, 0), 30, True),
    WILDFIRE_BOMB: ((0, D1_WILDFIRE_BOMB, 0), 20, True),
    TAR_BOMB: ((0, D1_TAR_BOMB, 0), 50, True),
    CLUSTER_BOMBS: ((0, 0, D2_CLUSTER_BOMBS), 60, False),
}
CASTABLE_FIELDS = {
    "Attributes": ATTR_CASTABLE, "CastingTimeIndex": 1, "EquippedItemClass": -1, "StartRecoveryCategory": 133,
    "StartRecoveryTime": 1500, "DefenseType": DEFENSE_RANGED, "PreventionType": 2, "SpellClassSet": SPELLFAMILY_HUNTER,
}
CASTABLE_EXTRA = {   # SURVIVAL 5.1 / 5.3 / 5.4 / 5.8, A4
    MANTIS_STRIKE: {"CasterAuraSpell": MANTIS_ENABLE, "CasterAuraState": 0, "RangeIndex": 12, "RecoveryTime": 0,
                    "Category": 0, "Effect_2": EFFECT_APPLY_AURA, "EffectAura_2": AURA_MOD_ROOT,
                    "EffectMechanic_2": MECHANIC_ROOT, "Effect_1": EFFECT_SCHOOL_DAMAGE},
    WILDFIRE_BOMB: {"RecoveryTime": 18000, "Category": 0, "SchoolMask": SCHOOL_FIRE, "Effect_1": EFFECT_SCHOOL_DAMAGE,
                    "ImplicitTargetA_1": 53, "ImplicitTargetB_1": 16, "Effect_2": EFFECT_APPLY_AURA,
                    "EffectAura_2": 3, "ImplicitTargetA_2": 53, "ImplicitTargetB_2": 16},
    TAR_BOMB: {"RecoveryTime": 30000, "Category": 0, "Effect_1": EFFECT_SCHOOL_DAMAGE, "ImplicitTargetA_1": 53,
               "ImplicitTargetB_1": 16, "Effect_2": EFFECT_TRIGGER_SPELL, "EffectTriggerSpell_2": TARRED,
               "ImplicitTargetA_2": 53, "ImplicitTargetB_2": 16, "Effect_3": EFFECT_TRIGGER_SPELL,
               "EffectTriggerSpell_3": TAR, "ImplicitTargetA_3": 53, "ImplicitTargetB_3": 16},
    CLUSTER_BOMBS: {"RecoveryTime": 50000, "Category": 0, "Targets": TARGET_FLAG_DEST_LOCATION,
                    "SchoolMask": SCHOOL_FIRE, "Effect_1": EFFECT_SCHOOL_DAMAGE, "ImplicitTargetA_1": 87,
                    "ImplicitTargetB_1": 16, "Effect_2": EFFECT_DUMMY, "ImplicitTargetA_2": 87},
}
# N2: every SV potency spell's SpellLevel (= its potency BaseLevel) is its talent row's learn level
POTENCY_LEVELS = {MANTIS_STRIKE: 30, WILDFIRE_BOMB: 20, TAR_BOMB: 50, BURNING_TAR: 50, CLUSTER_BOMBS: 60,
                  CLUSTER_BOMBS_BLAST: 60, SHRAPNEL_HIT: 35, EXPLOSIVE_SHOT: 30, EXPLOSIVE_BLAST: 30}

# (d) Explosive Shot 53301 (A5, stale line 1): fixed built fields. RangeIndex 35 (0-35 yd, no ranged flag): no
# minimum range (user 2026-10-17; was 114 Hunter Range)
EXPLOSIVE_SHOT_FIELDS = {
    "Attributes": ATTR_EXPLOSIVE_SHOT, "CastingTimeIndex": 18, "EquippedItemClass": 2, "EquippedItemSubclass": 262156,
    "DefenseType": DEFENSE_RANGED, "RangeIndex": 35, "Category": 1173, "CategoryRecoveryTime": 6000,
    "ManaCostPct": 7, "SpellLevel": 30, "BaseLevel": 30, "MaxLevel": 0, "SchoolMask": SCHOOL_FIRE,
    "Effect_1": EFFECT_SCHOOL_DAMAGE, "ImplicitTargetA_1": 6, "Effect_2": EFFECT_APPLY_AURA,
    "EffectAura_2": AURA_PERIODIC_DUMMY, "ImplicitTargetA_2": 6, "EffectAuraPeriod_2": 1000,
    "EffectBasePoints_2": -1, "Effect_3": 0, "SpellDescriptionVariableID": 1180,
}
EXPLOSIVE_SHOT_AP, BLAST_AP, BLAST_STALE_AP_BONUS = 76.5, 26.0, 0.16
EXPLOSIVE_SHOT_DURATION_MS = 2000
SPLASH_PCT = 40

# (e) stale line 12 / A3: the exact IGNORE_LINE_OF_SIGHT list of the SV block, and the no-proc helpers
IGNORE_LOS_IDS = frozenset({TARRED, TAR, BURNING_TAR, SHRAPNEL_HIT, IGT_SLOW, TRAP_FIRE, WYVERN_SLEEP})
NO_PROC_HELPERS = frozenset({CLUSTER_BOMBS_BLAST, SHRAPNEL_HIT, SPLASH, BLAST_SPLASH, TRAP_FIRE})
PROC_RAISERS = (*CASTABLES, EXPLOSIVE_SHOT)     # once-per-cast procs / IsAspectRollSource / Tarred's row

# (f) M1 (stale line 13). 56453 / 67544 are S3b's rows.
VISIBLE = (MANTIS_ENABLE, MONGOOSE_FURY, PREDATORS_GUARD_BUFF, SURVIVALIST_SPEED, *FAVORED_PREY_BUFFS,
           EXPOSE_WEAKNESS_BUFF, MASTER_TACTICIAN_BUFF, TARRED, TAR, BURNING_TAR, IGT_SLOW, WYVERN_SLEEP)
HIDDEN = (PONE_MARKER, SURVIVALIST_DETERRENCE, TNT_MASTERY)

# (g) N5: the player-cast ranged shots S3 keeps at class 2; every other S3a id is -1
SV_CLASS_TWO = frozenset({EXPLOSIVE_SHOT, WYVERN_STING, SCATTER_SHOT, BLACK_ARROW})
EDITED_STOCK_IDS = (EXPLOSIVE_BLAST, EXPOSE_WEAKNESS_BUFF, MASTER_TACTICIAN_BUFF, ENTRAPMENT_ROOT,
                    GLYPH_EXPLOSIVE_SHOT, COUNTERATTACK, MONGOOSE_BITE, RAPTOR_STRIKE, 13795, 13813, GLAIVE_TOSS,
                    34455, 34459, 34460, 53252, 53253)

# (h) SURVIVAL 6 / 5: (spell ids, 1-based effect, aura or None, SpellModOp or None, `_masks.py` name or literal mask)
SPELLMOD_SPECS = (
    (DEADLY_FOCUS, 1, PCT, OP.DAMAGE, "STRIKE_HITS"),
    ((202081,), 2, FLAT, OP.RANGE, "THREE_STRIKES"),
    ((202085, 202086, 202087), 1, PCT, OP.IGNORE_ARMOR, "THREE_STRIKES"),
    ((202088, 202089, 202090), 1, PCT, OP.DAMAGE, (0, 0, D2_GLAIVE_TOSS)),
    ((202090,), 2, FLAT, OP.JUMP_TARGETS, (0, 0, D2_GLAIVE_TOSS)),
    ((19376, 63457, 63458), 1, PCT, OP.DURATION, (D0_FROST_TRAP_AURA, 0, 0)),
    ((19376, 63457, 63458), 2, PCT, OP.DOT, "TRAP_MASTERY_DOT"),
    ((19376, 63457, 63458), 3, FLAT, OP.ALL_EFFECTS, (0, D1_SNAKE_TRAP_EFFECT, 0)),
    ((34494, 34496, 202091), 2, FLAT, OP.CRITICAL_CHANCE, "SURVIVAL_INSTINCTS_CRIT"),
    ((19255, 19256, 19257), 3, FLAT, OP.COOLDOWN, (0, D1_DETERRENCE, 0)),
    ((202095, 202096, 202097), 1, PCT, OP.DAMAGE, "DEMOLITIONS_DAMAGE"),
    ((202095, 202096, 202097), 2, PCT, OP.DOT, "DEMOLITIONS_DOT"),
    ((19286, 19287), 2, FLAT, OP.COOLDOWN, (0, D1_DISENGAGE, 0)),
    ((19184, 19387, 19388), 1, FLAT, OP.EFFECT1, (D0_FROST_TRAP_AURA, 0, 0)),
    ((56339, 56340, 56341), 3, FLAT, OP.ALL_EFFECTS, "TAMED_PET_PASSIVE_01_MASK"),
    ((34491, 34492, 34493), 1, PCT, OP.COST, "RESOURCEFULNESS_COST"),
    ((34491, 34492, 34493), 2, FLAT, OP.COOLDOWN, (D0_TRAP, 0, 0)),
    ((202100, 202101, 202102), 1, PCT, OP.DAMAGE, (0, D1_MANTIS_STRIKE, 0)),
    ((202103, 202104, 202105), 1, PCT, OP.DAMAGE, (D0_EXPLOSIVE_TRAP_EFFECT, 0, 0)),
    ((56333, 56336, 56337), 1, PCT, OP.DAMAGE, "SV_TNT_DAMAGE"),
    ((56333, 56336, 56337), 2, PCT, OP.DOT, "SV_TNT_DOT"),
    ((202107, 202108), 1, PCT, OP.DOT, (0, D1_BURNING_TAR, 0)),
    ((202108,), 2, FLAT, OP.COOLDOWN, (0, D1_TAR_BOMB, 0)),
    ((MONGOOSE_FURY,), 1, PCT, OP.DAMAGE, (D0_MONGOOSE_BITE, 0, 0)),
    ((PREDATORS_GUARD_BUFF,), 2, PCT, OP.DAMAGE, "THREE_STRIKES"),
    ((SURVIVALIST_DETERRENCE,), 1, FLAT, OP.DURATION, (0, D1_DETERRENCE, 0)),
    ((TNT_MASTERY,), 1, PCT, OP.DAMAGE, "SV_TNT_DAMAGE"),
    ((TNT_MASTERY,), 2, PCT, OP.DOT, "SV_MASTERY_DOT"),
    ((GLYPH_EXPLOSIVE_SHOT,), 1, FLAT, OP.CRITICAL_CHANCE, "GLYPH_EXPLOSIVE_SHOT"),
    ((PONE_MARKER,), 1, AURA_MOD_DAMAGE_FROM_CASTER, None, "PONE_ALL_EXCEPT_BURNING_TAR"),   # a reader, not a mod
)
# SURVIVAL 2.5 / 0-dsl (b): the composites, literal (d0, d1, d2)
SPEC_MASKS = {
    "STRIKE_HITS": (0x2, 0x80000, 0),
    "RELENTLESS_PROC": (0, 0x80000, 0x10000),
    "KILLER_INSTINCT_PROC": (0x2, 0x80000000, 0x40),
    "SV_TNT_DAMAGE": (0x4, 0x84000040, 0x220),
    "SV_TNT_DOT": (0x4, 0x8000040, 0x20000),
    "SV_MASTERY_DOT": (0x4, 0x8000040, 0),
    "DEMOLITIONS_DAMAGE": (0, 0x80000040, 0x200),
    "DEMOLITIONS_DOT": (0, 0x40, 0),
    "TRAP_MASTERY_DOT": (0x4, 0, 0x20000),
    "SURVIVAL_INSTINCTS_CRIT": (0x800, 0x80000040, 0x20000240),
    "RESOURCEFULNESS_COST": (0x82, 0x80000, 0x10000),
    "HUNTING_PARTY_PROC": (0x802, 0x80080000, 0x20010040),
    "THRILL_PROC": (0x61800, 0x80800000, 0x28000001),
    "LOCK_AND_LOAD_PROC": (0x18, 0x8000000, 0x24000),
    "PONE_ALL_EXCEPT_BURNING_TAR": (0xFFFFFFFF, 0xE7FFFFFF, 0xFFFFFFFF),
    "GLYPH_EXPLOSIVE_SHOT": (0, 0x80000000, 0x200),
    "TAMED_PET_PASSIVE_01_MASK": (0x2000000, 0, 0),
    "THREE_STRIKES": (0x2, 0x80000, 0x10000),
}
# Effects S3a turns to None (no effect, no mask): (ids, 1-based effect)
REMOVED_EFFECTS = (
    ((56333, 56336, 56337), 3),              # T.N.T. eff2
    ((53298, 53299, 202106), 2),             # Point of No Escape eff1
    ((53298, 53299, 202106), 3),
    ((EXPOSE_WEAKNESS_BUFF,), 2),            # 34501 eff1 (aura 268, SURVIVAL 0.7)
)

# (i) SURVIVAL 8.1 rows (stale line 8 keys). Columns the spec fixes; "mask" is a `_masks.py` name or a literal.
_ROW = {"SpellFamilyName": SPELLFAMILY_HUNTER, "Chance": 0.0, "Cooldown": 0}
PROC_ROWS = {
    19373: {**_ROW, "ProcFlags": 0x100, "mask": "KILLER_INSTINCT_PROC", "SpellTypeMask": 0,
            "SpellPhaseMask": PROC_PHASE_CAST, "HitMask": 0, "AttributesMask": 0, "DisableEffectsMask": 0x1},
    202087: {**_ROW, "ProcFlags": 0x100, "mask": "RELENTLESS_PROC", "SpellTypeMask": 0,
             "SpellPhaseMask": PROC_PHASE_CAST, "HitMask": 0, "AttributesMask": 0, "DisableEffectsMask": 0x1},
    202094: {**_ROW, "ProcFlags": 0x100, "mask": "STRIKE_HITS", "SpellTypeMask": 1, "SpellPhaseMask": PROC_PHASE_HIT,
             "HitMask": 0x3, "AttributesMask": 0, "DisableEffectsMask": 0x1},
    34493: {**_ROW, "ProcFlags": 0x100, "mask": "STRIKE_HITS", "SpellTypeMask": 1, "SpellPhaseMask": PROC_PHASE_HIT,
            "HitMask": 0x3, "AttributesMask": 0, "DisableEffectsMask": 0x3},
    202097: {**_ROW, "ProcFlags": 0x100, "mask": (0, D1_EXPLOSIVE_SHOT, 0), "SpellTypeMask": 1,
             "SpellPhaseMask": PROC_PHASE_HIT, "HitMask": 0x2, "AttributesMask": 0, "DisableEffectsMask": 0x3},
    202105: {**_ROW, "ProcFlags": 0x100, "mask": (0, D1_WILDFIRE_BOMB, 0), "SpellTypeMask": 0,
             "SpellPhaseMask": PROC_PHASE_CAST, "HitMask": 0, "AttributesMask": 0, "DisableEffectsMask": 0x1},
    202084: {**_ROW, "ProcFlags": 0x140, "mask": (0, 0, 0), "SpellTypeMask": 0,
             "SpellPhaseMask": PROC_PHASE_CAST | PROC_PHASE_HIT, "HitMask": 0, "AttributesMask": 0,
             "DisableEffectsMask": 0x1},
    -34500: {**_ROW, "ProcFlags": 0x140, "mask": (0, 0, 0), "SpellTypeMask": 1,
             "SpellPhaseMask": PROC_PHASE_CAST | PROC_PHASE_HIT, "HitMask": 0x2, "AttributesMask": 0,
             "DisableEffectsMask": 0},
    **{key: {**_ROW, "ProcFlags": 0x140, "mask": (0, 0, 0), "SpellTypeMask": 1,
             "SpellPhaseMask": PROC_PHASE_CAST | PROC_PHASE_HIT, "HitMask": 0x3, "AttributesMask": 0,
             "DisableEffectsMask": 0} for key in (34506, 34507, 34508)},
    -53290: {**_ROW, "ProcFlags": 0x100, "mask": "HUNTING_PARTY_PROC", "SpellTypeMask": 1,
             "SpellPhaseMask": PROC_PHASE_HIT, "HitMask": 0x2, "AttributesMask": 0, "DisableEffectsMask": 0x6},
    -34497: {**_ROW, "ProcFlags": 0x100, "mask": "THRILL_PROC", "SpellTypeMask": 1,
             "SpellPhaseMask": PROC_PHASE_CAST, "HitMask": 0x2, "AttributesMask": 0, "DisableEffectsMask": 0x2},
    -19184: {**_ROW, "ProcFlags": PROC_FLAG_TRAP_ACTIVATION, "mask": (D0_FROST_TRAP_AURA, D1_SNAKE_TRAP_EFFECT, 0),
             "SpellTypeMask": 0, "SpellPhaseMask": PROC_PHASE_FINISH, "HitMask": 0,
             "AttributesMask": PROC_ATTR_TRIGGERED_CAN_PROC, "DisableEffectsMask": 0x1},
}
# S3b rows (S3b-HANDOFF B1 / B4, 0-verify V-m1 / V-m17): Tarred's TAKEN-flag row (phase 0, Fire, trigger-capable), the
# exact live key -56342 re-declared (HIT | FINISH, no cooldown, chance 0 kept), 56453's CAST row (no
# TRIGGERED_CAN_PROC).
PROC_PHASE_HIT_FINISH = PROC_PHASE_HIT | PROC_PHASE_FINISH
S3B_PROC_ROWS = {
    TARRED: {"SpellFamilyName": 0, "Chance": 100.0, "Cooldown": 0, "ProcFlags": 0x20200, "SchoolMask": SCHOOL_FIRE,
             "mask": (0, 0, 0), "SpellTypeMask": 1, "SpellPhaseMask": 0, "HitMask": 0,
             "AttributesMask": PROC_ATTR_TRIGGERED_CAN_PROC, "DisableEffectsMask": 0},
    -56342: {**_ROW, "ProcFlags": 0, "mask": "LOCK_AND_LOAD_PROC", "SpellTypeMask": 0,
             "SpellPhaseMask": PROC_PHASE_HIT_FINISH, "HitMask": 0, "AttributesMask": PROC_ATTR_TRIGGERED_CAN_PROC,
             "DisableEffectsMask": 0x4},
    56453: {**_ROW, "Chance": 100.0, "ProcFlags": 0x100, "mask": (0x800, D1_EXPLOSIVE_SHOT, 0), "SpellTypeMask": 0,
            "SpellPhaseMask": PROC_PHASE_CAST, "HitMask": 0, "AttributesMask": 0, "DisableEffectsMask": 0},
}
ALL_PROC_ROWS = {**PROC_ROWS, **S3B_PROC_ROWS}
# Proc carriers (SURVIVAL 6 + stale lines 9 / 22, A11): id -> (ProcTypeMask, ProcChance, 1-based carrier effect,
# aura of that effect, trigger spell). Every DUMMY carrier has trigger 0 (PLAN 2 DUMMY-carrier rule).
PROC_CARRIERS = {
    19373: (0x100, 20, 2, AURA_PROC_TRIGGER_SPELL, MANTIS_ENABLE),
    202087: (0x100, 15, 2, AURA_PROC_TRIGGER_SPELL, MONGOOSE_FURY),
    202094: (0x100, 10, 2, AURA_PROC_TRIGGER_SPELL, PREDATORS_GUARD_BUFF),
    34493: (0x100, 30, 3, AURA_PROC_TRIGGER_SPELL, SCAVENGER),
    202097: (0x100, 100, 3, AURA_DUMMY, 0),
    202105: (0x100, 30, 2, AURA_DUMMY, 0),
    202084: (0x140, 5, 2, AURA_DUMMY, 0),
    **{i: (0x140, 100, 1, AURA_PROC_TRIGGER_SPELL_WITH_VALUE, EXPOSE_WEAKNESS_BUFF) for i in (34500, 34502, 34503)},
    34506: (0x140, 5, 1, AURA_PROC_TRIGGER_SPELL, MASTER_TACTICIAN_BUFF),
    34507: (0x140, 10, 1, AURA_PROC_TRIGGER_SPELL, MASTER_TACTICIAN_BUFF),
    34508: (0x140, 15, 1, AURA_PROC_TRIGGER_SPELL, MASTER_TACTICIAN_BUFF),
    **{i: (0x100, 100, 1, AURA_DUMMY, 0) for i in (53290, 53291, 53292)},
    **{i: (LOCK_AND_LOAD_PROC_TYPE, 100, 1, AURA_PROC_TRIGGER_SPELL, LOCK_AND_LOAD_BUFF) for i in LOCK_AND_LOAD},
    34497: (0x100, 50, 1, AURA_DUMMY, 0),
    34498: (0x100, 100, 1, AURA_DUMMY, 0),
    19388: (PROC_FLAG_TRAP_ACTIVATION, None, 2, AURA_PROC_TRIGGER_SPELL, ENTRAPMENT_ROOT),
}
# Ranks / helpers that must carry ProcTypeMask 0 (no row, no default entry; SURVIVAL 8.1 "No-row DUMMY carriers")
ZERO_PROC_TYPE = (*(i for i in NEW_RANK_IDS if i not in PROC_CARRIERS), 53298, 53299, 19287, 19184, 19387, 19370,
                  19371, MONGOOSE_FURY, 56333, 56336, 56337)
# N8: tab-362 ranks with a non-zero ProcTypeMask and no row in the package on purpose. None since S3b: -56342 is
# declared (B4) and Wyvern Sting 19386's stock 0x100000 is zeroed (B7).
M15_ACCEPTED: frozenset[int] = frozenset()

# (k) SURVIVAL 2.4: (dword index 0-2, bit) -> the exact carriers (family-9 rows of the package)
BIT_CARRIERS = {
    (1, D1_MANTIS_STRIKE): frozenset({MANTIS_STRIKE}),
    (1, D1_WILDFIRE_BOMB): frozenset({WILDFIRE_BOMB}),
    (1, D1_TAR_BOMB): frozenset({TAR_BOMB}),
    (1, D1_BURNING_TAR): frozenset({BURNING_TAR}),
    (2, D2_CLUSTER_BOMBS): frozenset({CLUSTER_BOMBS, CLUSTER_BOMBS_BLAST}),
}
EXACT_SPELL_MASKS = {
    MANTIS_STRIKE: (0, D1_MANTIS_STRIKE, 0), WILDFIRE_BOMB: (0, D1_WILDFIRE_BOMB, 0), TAR_BOMB: (0, D1_TAR_BOMB, 0),
    BURNING_TAR: (0, D1_BURNING_TAR, 0), CLUSTER_BOMBS: (0, 0, D2_CLUSTER_BOMBS),
    CLUSTER_BOMBS_BLAST: (0, 0, D2_CLUSTER_BOMBS), EXPLOSIVE_SHOT: (0, D1_EXPLOSIVE_SHOT, 0),
    EXPLOSIVE_BLAST: (0, 0, D2_EXPLOSIVE_SHOT_TICK), WYVERN_SLEEP: (0, D1_WYVERN_STING, 0),
    BLACK_ARROW: (0, 0, 0), COUNTERATTACK: (0, 0, 0), 34498: (0, 0, 0),
}
NO_BIT_IDS = frozenset({*range(202041, 202045), TARRED, TAR, *range(202053, 202059), *range(202060, 202073),
                        *NEW_RANK_IDS})

# (n) the brief's script table (positive keys) and the exact unbinds
SCRIPT_BINDINGS = {
    "spell_hun_mantis_strike": frozenset({MANTIS_STRIKE}),
    "spell_hun_explosive_shot_rework": frozenset({EXPLOSIVE_SHOT}),
    "spell_hun_explosive_shot_blast": frozenset({EXPLOSIVE_BLAST}),
    "spell_hun_explosive_shot_splash": frozenset(SPLASHES),
    "spell_hun_shrapnel": frozenset({SHRAPNEL_HIT}),
    "spell_hun_cluster_bombs": frozenset({CLUSTER_BOMBS}),
    "spell_hun_cluster_bombs_blast": frozenset({CLUSTER_BOMBS_BLAST}),
    "spell_hun_demolitions": frozenset({202097}),
    "spell_hun_volatile_payload": frozenset({202105}),
    "spell_hun_favored_prey": frozenset({202084}),
    "spell_hun_sv_ranged_cast_proc": frozenset({34500, 34502, 34503, 34506, 34507, 34508}),
    "spell_hun_hunting_party_rework": frozenset({53290, 53291, 53292}),
    "spell_hun_thrill_of_the_hunt_sv": frozenset(THRILL),
    "spell_hun_tnt_mastery": frozenset({TNT_MASTERY}),
    "spell_hun_glaive_toss_sv": frozenset({GLAIVE_TOSS}),
    # S3b (brief script table; every key positive, the two unbinds below are the only negative ones)
    "spell_hun_tarred": frozenset({TARRED}),
    "spell_hun_burning_tar": frozenset({BURNING_TAR}),
    "spell_hun_point_of_no_escape": frozenset({PONE_MARKER}),
    "spell_hun_frost_trap_aura_sv": frozenset({FROST_TRAP_AURA}),
    "spell_hun_lock_and_load_rework": frozenset(LOCK_AND_LOAD),
    "spell_hun_explosive_trap_fire": frozenset({EXPLOSIVE_TRAP_EFFECT}),
    "spell_hun_explosive_trap_fire_tick": frozenset({TRAP_FIRE}),
    "spell_hun_freezing_trap_sv": frozenset({FREEZING_TRAP_EFFECT}),
    "spell_hun_wyvern_sting_rework": frozenset({WYVERN_STING}),
    "spell_hun_deterrence_sv": frozenset({19263}),
    "spell_hun_disengage_sv": frozenset({781}),
    "spell_hun_feign_death_sv": frozenset({5384}),
}
S3A_UNBINDS = frozenset({(-EXPLOSIVE_SHOT, "spell_hun_explosive_shot"), (-53290, "spell_hun_hunting_party")})
S3B_UNBINDS = frozenset({(-56342, "spell_hun_lock_and_load"), (-WYVERN_STING, "spell_hun_wyvern_sting")})
KEPT_STOCK_CLASSES = frozenset({"spell_hun_thrill_of_the_hunt", "spell_hun_glaive_toss", "spell_hun_shot_mana",
                                "spell_hun_disengage", "spell_hun_lock_and_load", "spell_hun_wyvern_sting"})
SHOT_MANA_BINDING = (RAPTOR_STRIKE, "spell_hun_shot_mana")      # ruling 6: no new binding, the existing path
LINKS = ((19255, SURVIVALIST_DETERRENCE, 2), (19256, SURVIVALIST_DETERRENCE, 2), (19257, SURVIVALIST_DETERRENCE, 2),
         (56337, TNT_MASTERY, 2))
FAVORED_PREY_GROUP, GROUP_RULE_EXCLUSIVE = 1242, 1

# (o) user ruling 6
RAPTOR_MANA_PCT = 25  # user 2026-10-18: 5 -> 15 -> 25% base mana
DEADLY_FOCUS_MANA_TEXT = re.compile(r"Raptor Strike restores (25|\$202081s3|\$s3)% of your base mana")

# (l) stale line 19 / brief 13: stale raw readers S3a deletes: (id, 1-based effect) whose mask must be zero
STALE_READERS = (
    ((34455, 34459, 34460), 2),        # Ferocious Inspiration B_2 0x40 on a None eff1
    ((53252, 53253), 2),               # Invigoration B_2 0x40 on a missing eff1
    ((53298, 53299, 202106), 1),       # Point of No Escape eff0 becomes a DUMMY (masks cleared)
    ((53298, 53299, 202106), 3),       # ... and C_2 0x4000000 on a missing eff2
    ((BLACK_ARROW,), 2),               # Black Arrow eff1 aura-271 reader, untaught (brief 13)
    ((34494, 34496, 202091), 1),       # Survival Instincts A_1 0xDE on aura 87
    ((19286, 19287), 1),               # Survival Tactics A_1 / A_2 on the resist effect
    ((*THRILL,), 1),                   # Thrill A_1 0xDE on the DUMMY carrier
    ((34506, 34507, 34508), 1), ((34506, 34507, 34508), 2),   # Master Tactician trigger masks
    ((MASTER_TACTICIAN_BUFF,), 1), ((MASTER_TACTICIAN_BUFF,), 2),
    ((EXPLOSIVE_BLAST,), 1),           # 53352 A_1 0xC00017 on SCHOOL_DAMAGE
)
INVIGORATION_D1_B27 = 53252            # its eff0 A_2 0x8000000 (d1 b27) goes too (brief 13)
OP_EFFECT2 = int(OP.EFFECT2)

# (p) S2-FIX
INSTANT_MODS_SEEN_MIN = 2


# ---- small helpers ---------------------------------------------------------------------------------------------------

def live_amount(row: dict, n: int) -> int:
    """A static effect's live value: stored base points + 1 when die sides is 1 (stored = live - 1), + 0 at 0."""
    return _i(row, f"EffectBasePoints_{n}") + (1 if _i(row, f"EffectDieSides_{n}") >= 1 else 0)


def is_dummy(row: dict, n: int) -> bool:
    """A DUMMY marker / carrier: SPELL_EFFECT_DUMMY, or APPLY_AURA SPELL_AURA_DUMMY."""
    effect = _i(row, f"Effect_{n}")
    return effect == EFFECT_DUMMY or (effect == EFFECT_APPLY_AURA and _i(row, f"EffectAura_{n}") == AURA_DUMMY)


def _potency(entry: dict | None, n: int) -> dict:
    return ((entry or {}).get(f"effect{n}") or {}).get("_potency") or {}


def _potency_excluded(entry: dict | None, n: int):
    return ((entry or {}).get(f"effect{n}") or {}).get("_potency_excluded")


def spell_call_source(text: str, spell_id: int) -> str | None:
    """The source of the module-level `spell(...)` call that declares `id=<spell_id>` (up to its closing `)` line)."""
    m = re.search(rf"^\s+id={spell_id},\s*$", text, re.M) or re.search(rf"\bid={spell_id}\b", text)
    if m is None:
        return None
    start = text.rfind("spell(", 0, m.start())
    end = text.find("\n)\n", m.end())
    return text[max(start, 0):end if end >= 0 else len(text)]


# ---- (a) / (b) the tab -----------------------------------------------------------------------------------------------

def check_tab_362(talents: list[dict], built_talents: list[dict], sla_entries: list[dict],
                  trainer_spells: list[dict]) -> list[str]:
    """(a) SURVIVAL 2.2 / 6 + A1: 34 talents, 83 points, exact cells and rank lists, one talent per cell, no
    prerequisite, castable rows flags=1 and the rest 0, the SV SLA rows (skill line 51 = the tab's skill_line), no other
    derived SLA row for a tab-362 rank, no trainer row for a tab-362 rank (L13)."""
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
            bad.append(f"talent {tid}: depends_on {t['depends_on']} (no prerequisite arrows, D7 / stale line 6)")
        for key in (t.get("raw_overrides") or {}):
            if str(key).startswith(("PrereqTalent", "PrereqRank")):
                bad.append(f"talent {tid}: raw override {key}")
        flags = int(t.get("flags") or 0) & 1
        if tid in CASTABLE_ROWS and not flags:
            bad.append(f"talent {tid}: castable-teaching row without flags=1")
        if tid not in CASTABLE_ROWS and flags:
            bad.append(f"talent {tid}: flags=1 on a passive row (only the castable rows {sorted(CASTABLE_ROWS)})")
    for cell, talent_ids in sorted(cells.items()):
        if len(talent_ids) > 1:
            bad.append(f"cell {cell} holds talents {talent_ids}")
    for row in built_talents:
        if _i(row, "TabID") != TAB:
            continue
        for n in (1, 2, 3):
            if _i(row, f"PrereqTalent_{n}"):
                bad.append(f"talent {row['ID']}: built PrereqTalent_{n} {row.get(f'PrereqTalent_{n}')}")
    sla = {int(e["id"]): e for e in sla_entries}
    for sla_id, spell_id in SV_SLA.items():
        e = sla.get(sla_id)
        got = None if e is None else (int(e["spell_id"]), int(e["skill_line"]), int(e.get("class_mask") or 0))
        if got != (spell_id, SKILL_LINE_SV, CLASSMASK_HUNTER):
            bad.append(f"SkillLineAbility {sla_id}: (spell, skill line, class mask) {got}, "
                       f"expected {(spell_id, SKILL_LINE_SV, CLASSMASK_HUNTER)} (survival_362_tab skill_line=51)")
    tab_ranks = set(TAB_RANKS)
    for e in sla_entries:
        if int(e["spell_id"]) in tab_ranks and int(e["id"]) not in SV_SLA:
            bad.append(f"SkillLineAbility {e['id']} teaches tab-{TAB} rank {e['spell_id']} (player_castable=False rows "
                       f"derive none)")
    for t in trainer_spells:
        sid = int(t.get("SpellId") or t.get("spell_id") or 0)
        if sid in tab_ranks:
            bad.append(f"trainer row for talent spell {sid} (L13: talent spells get none)")
    return bad


def check_tab_363_kept(talents: list[dict], built_talents: list[dict]) -> list[str]:
    """(a) MM's tab 363 is untouched by S3a: 33 talents / 81 points, Sniper Training 2143 on 363 at (7,2) with its
    three ranks, on no other tab."""
    bad = []
    mine = [t for t in talents if t.get("tab_id") == MM_TAB]
    points = sum(len(t.get("rank_spell_ids") or []) for t in mine)
    if (len(mine), points) != (MM_TAB_TALENT_COUNT, MM_TAB_POINTS):
        bad.append(f"tab {MM_TAB}: {len(mine)} talents / {points} points, expected {MM_TAB_TALENT_COUNT} / "
                   f"{MM_TAB_POINTS}")
    st = [t for t in talents if int(t["id"]) == SNIPER_TRAINING_ROW]
    if len(st) != 1 or st[0].get("tab_id") != MM_TAB or (int(st[0]["tier"]), int(st[0]["column"])) != (7, 2) \
            or tuple(int(s) for s in st[0].get("rank_spell_ids") or []) != SNIPER_TRAINING_RANKS:
        bad.append(f"talent {SNIPER_TRAINING_ROW}: declared {[(t.get('tab_id'), t.get('tier'), t.get('column'))
                                                             for t in st]}, expected once on {MM_TAB} at (7, 2) with "
                   f"{list(SNIPER_TRAINING_RANKS)}")
    for row in built_talents:
        if _i(row, "ID") == SNIPER_TRAINING_ROW and _i(row, "TabID") != MM_TAB:
            bad.append(f"talent {SNIPER_TRAINING_ROW}: built TabID {row.get('TabID')}, expected {MM_TAB}")
    return bad


def check_sniper_training_off_sv(talent_rows: list[dict]) -> list[str]:
    """(b) 53302-53304 (Sniper Training's live ranks, MM) are taught by no tab-362 row of the overlay."""
    wanted = set(SNIPER_TRAINING_RANKS)
    return [f"talent {row.get('ID')} (tab {TAB}) teaches Sniper Training rank {_i(row, f'SpellRank_{n}')}"
            for row in talent_rows if _i(row, "TabID") == TAB
            for n in range(1, 10) if _i(row, f"SpellRank_{n}") in wanted]


def check_talent_blocks(ordered_rows: list[dict]) -> list[str]:
    """(a) after `dbcfile.order_talent_rows`: every hunter tab block contiguous, and tab 362's block is the 34 layout
    rows in (tier, column) order."""
    bad = []
    for tab in (361, TAB, MM_TAB):
        positions = [i for i, r in enumerate(ordered_rows) if _i(r, "TabID") == tab]
        if positions and positions[-1] - positions[0] + 1 != len(positions):
            bad.append(f"tab {tab}: Talent.dbc rows not contiguous (positions {positions[0]}..{positions[-1]}, "
                       f"{len(positions)} rows)")
    block = [_i(r, "ID") for r in ordered_rows if _i(r, "TabID") == TAB]
    want = [tid for tid, _ in sorted(TAB_LAYOUT.items(), key=lambda kv: kv[1][0])]
    if block != want:
        bad.append(f"tab {TAB} physical order {block}, expected {want}")
    return bad


def check_rank_rows_unique(talents: list[dict], declared: set[int], var_names: dict[int, str],
                           rank_ids=TAB_RANKS, new_ranks=NEW_RANK_IDS) -> list[str]:
    """(a) every tab-362 rank and every 202080-202108 rank spell is a rank of exactly one talent row (any tab) and is
    declared under a DSL variable."""
    bad = []
    count: dict[int, list[int]] = {}
    for t in talents:
        for sid in t.get("rank_spell_ids") or []:
            count.setdefault(int(sid), []).append(int(t["id"]))
    for sid in sorted({*rank_ids, *new_ranks}):
        rows = count.get(sid, [])
        if len(rows) != 1:
            bad.append(f"rank {sid}: in talent rows {rows}, expected exactly one")
        if sid not in declared:
            bad.append(f"rank {sid}: not declared")
        elif sid >= 200000 and not var_names.get(sid):
            bad.append(f"rank {sid}: declared under no DSL variable")
    return bad


# ---- (c) the castables -----------------------------------------------------------------------------------------------

def check_castables(rows_by_id: dict[int, dict], cast_times: dict[int, int]) -> list[str]:
    bad = []
    for spell_id, (mask, level, unit_targeted) in CASTABLE_SPECS.items():
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
            continue
        for key, want in {**CASTABLE_FIELDS, **CASTABLE_EXTRA[spell_id]}.items():
            if _i(row, key) != want:
                bad.append(f"{spell_id}: {key} {row.get(key)}, expected {want}")
        if _i(row, "Attributes") & ATTR_USES_RANGED_SLOT:
            bad.append(f"{spell_id}: USES_RANGED_SLOT (0x2) set (stale line 14: no ranged slot)")
        if _is_hunter_shot(row):
            bad.append(f"{spell_id}: is an _is_hunter_shot row (Attributes 0x{_i(row, 'Attributes'):X})")
        if live_cast_ms(row, cast_times) != 0:
            bad.append(f"{spell_id}: live cast {live_cast_ms(row, cast_times)} ms, expected 0")
        if spell_mask(row) != mask:
            bad.append(f"{spell_id}: SpellClassMask {_hex(spell_mask(row))}, expected {_hex(mask)}")
        if (_i(row, "SpellLevel"), _i(row, "BaseLevel"), _i(row, "MaxLevel")) != (level, level, 0):
            bad.append(f"{spell_id}: SpellLevel / BaseLevel / MaxLevel {row.get('SpellLevel')} / {row.get('BaseLevel')}"
                       f" / {row.get('MaxLevel')}, expected {level} / {level} / 0 (N2: learn level)")
        if unit_targeted and _i(row, "FacingCasterFlags") != 1:
            bad.append(f"{spell_id}: FacingCasterFlags {row.get('FacingCasterFlags')}, expected 1 (unit-targeted)")
        if _i(row, "AttributesEx3") & ATTR_EX3_SUPPRESS_CASTER_PROCS:
            bad.append(f"{spell_id}: SUPPRESS_CASTER_PROCS on a castable (it rolls the once-per-cast procs)")
    return bad


def check_potency_levels(rows_by_id: dict[int, dict], levels=POTENCY_LEVELS) -> list[str]:
    """N2: SpellLevel = BaseLevel = the learn level, MaxLevel 0, on every SV potency spell."""
    bad = []
    for spell_id, level in sorted(levels.items()):
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
        elif (_i(row, "SpellLevel"), _i(row, "BaseLevel"), _i(row, "MaxLevel")) != (level, level, 0):
            bad.append(f"{spell_id}: SpellLevel / BaseLevel / MaxLevel {row.get('SpellLevel')} / "
                       f"{row.get('BaseLevel')} / {row.get('MaxLevel')}, expected {level} / {level} / 0")
    return bad


# ---- (d) Explosive Shot ----------------------------------------------------------------------------------------------

def check_explosive_shot(row: dict | None, entry: dict | None, source: str | None, cast_times: dict[int, int],
                         duration_index: int) -> list[str]:
    """(d) A5 + stale line 1 + brief 7."""
    if row is None or entry is None:
        return [f"{EXPLOSIVE_SHOT}: not declared"]
    bad = []
    for key, want in EXPLOSIVE_SHOT_FIELDS.items():
        if _i(row, key) != want:
            bad.append(f"{key} {row.get(key)}, expected {want}")
    if float(row.get("Speed") or 0) != 40.0:
        bad.append(f"Speed {row.get('Speed')}, expected 40")
    if not _is_hunter_shot(row):
        bad.append("not an _is_hunter_shot row (USES_RANGED_SLOT | 0x10000, family 9)")
    if live_cast_ms(row, cast_times) != 0:
        bad.append(f"live cast {live_cast_ms(row, cast_times)} ms, expected 0 (index 18)")
    if spell_mask(row) != (0, D1_EXPLOSIVE_SHOT, 0):
        bad.append(f"SpellClassMask {_hex(spell_mask(row))}, expected (0x0, 0x80000000, 0x0) (d1 b31 kept)")
    if _i(row, "DurationIndex") != duration_index:
        bad.append(f"DurationIndex {row.get('DurationIndex')}, expected {duration_index} "
                   f"({EXPLOSIVE_SHOT_DURATION_MS} ms)")
    if _i(row, "AttributesEx5") & ATTR_EX5_EXTRA_INITIAL_TICK:
        bad.append(f"AttributesEx5 0x{_i(row, 'AttributesEx5'):X} keeps 0x200 (3 blasts instead of 2)")
    if _i(row, "AttributesEx3") & ATTR_EX3_SUPPRESS_CASTER_PROCS:
        bad.append("SUPPRESS_CASTER_PROCS set (the hit raises Tarred's row and the aspect rolls, H0-9)")
    pot = _potency(entry, 1)
    if pot.get("kind") != "direct" or float(pot.get("total_potency") or 0) != EXPLOSIVE_SHOT_AP \
            or not float(pot.get("ap_coefficient") or 0):
        bad.append(f"eff0 potency {pot.get('kind')} {pot.get('total_potency')} ap {pot.get('ap_coefficient')}, "
                   f"expected direct {EXPLOSIVE_SHOT_AP} AP")
    if _potency(entry, 2) or _potency_excluded(entry, 2):
        bad.append("eff1 carries a potency or potency_excluded (a bare PERIODIC_DUMMY timer, SURVIVAL 0.1)")
    if source is None:
        bad.append("its spell() call was not found in hunter_spells.py")
    else:
        for key in ("MaxLevel", "BaseLevel"):
            if re.search(rf"['\"]{key}['\"]\s*:", source):
                bad.append(f"its spell() call still sets raw '{key}' (brief 7: delete both, set SpellLevel 30)")
    return [f"{EXPLOSIVE_SHOT}: {b}" for b in bad]


def check_explosive_blast(row: dict | None, entry: dict | None, bonus_rows: list[dict]) -> list[str]:
    """(d) 53352: the only blast potency (26 AP direct), SpellLevel 30, the generated bonus row (not 0.16), d2 b9,
    Ex2 0x4 (stock), class -1, no stale A_1."""
    if row is None or entry is None:
        return [f"{EXPLOSIVE_BLAST}: not declared"]
    bad = []
    if _i(row, "Effect_1") != EFFECT_SCHOOL_DAMAGE:
        bad.append(f"eff0 type {row.get('Effect_1')}, expected SCHOOL_DAMAGE")
    pot = _potency(entry, 1)
    if pot.get("kind") != "direct" or float(pot.get("total_potency") or 0) != BLAST_AP:
        bad.append(f"eff0 potency {pot.get('kind')} {pot.get('total_potency')}, expected direct {BLAST_AP} AP")
    for key, want in (("SpellLevel", 30), ("BaseLevel", 30), ("MaxLevel", 0), ("EquippedItemClass", -1)):
        if _i(row, key) != want:
            bad.append(f"{key} {row.get(key)}, expected {want}")
    if spell_mask(row) != (0, 0, D2_EXPLOSIVE_SHOT_TICK):
        bad.append(f"SpellClassMask {_hex(spell_mask(row))}, expected (0x0, 0x0, 0x200) (d2 b9 kept)")
    if any(effect_mask(row, 1)):
        bad.append(f"eff0 keeps the stale mask {_hex(effect_mask(row, 1))} (L12)")
    if not _i(row, "AttributesEx2") & ATTR_EX2_IGNORE_LINE_OF_SIGHT:
        bad.append(f"AttributesEx2 0x{_i(row, 'AttributesEx2'):X} lost the stock IGNORE_LINE_OF_SIGHT 0x4")
    mine = [b for b in bonus_rows if int(b["entry"]) == EXPLOSIVE_BLAST]
    if len(mine) != 1:
        bad.append(f"{len(mine)} spell_bonus_data rows, expected one (the generated potency row)")
    elif abs(float(mine[0].get("ap_bonus") or 0) - float(pot.get("ap_coefficient") or -1)) > 1e-6 \
            or abs(float(mine[0].get("ap_bonus") or 0) - BLAST_STALE_AP_BONUS) < 1e-6:
        bad.append(f"spell_bonus_data ap_bonus {mine[0].get('ap_bonus')}, expected the potency's "
                   f"{pot.get('ap_coefficient')} (the stale {BLAST_STALE_AP_BONUS} replaced, L16)")
    return [f"{EXPLOSIVE_BLAST}: {b}" for b in bad]


def check_splashes(rows_by_id: dict[int, dict], entries: dict[int, dict]) -> list[str]:
    """(d) brief 2 + SURVIVAL 5.6: dest-targeted splashes (A 87 / B 16 + Targets 0x40), no LoS bypass, CANT_CRIT,
    IGNORE_CASTER_MODIFIERS | SUPPRESS_CASTER_PROCS, script BP0 (potency_excluded), no bit, SpellLevel 30; 202054
    eff1 DUMMY live 40 (the splash percent of both)."""
    bad = []
    for spell_id in SPLASHES:
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
            continue
        for key, want in (("Effect_1", EFFECT_SCHOOL_DAMAGE), ("ImplicitTargetA_1", 87), ("ImplicitTargetB_1", 16),
                          ("Targets", TARGET_FLAG_DEST_LOCATION), ("EquippedItemClass", -1),
                          ("SpellClassSet", SPELLFAMILY_HUNTER), ("DefenseType", DEFENSE_RANGED), ("SpellLevel", 30),
                          ("SchoolMask", SCHOOL_FIRE)):
            if _i(row, key) != want:
                bad.append(f"{spell_id}: {key} {row.get(key)}, expected {want}")
        ex2, ex3 = _i(row, "AttributesEx2"), _i(row, "AttributesEx3")
        if ex2 & ATTR_EX2_IGNORE_LINE_OF_SIGHT:
            bad.append(f"{spell_id}: AttributesEx2 0x{ex2:X} has IGNORE_LINE_OF_SIGHT (stale line 12: none)")
        if not ex2 & ATTR_EX2_CANT_CRIT:
            bad.append(f"{spell_id}: AttributesEx2 0x{ex2:X} lacks CANT_CRIT")
        if ex3 & (ATTR_EX3_IGNORE_CASTER_MODIFIERS | ATTR_EX3_SUPPRESS_CASTER_PROCS) != \
                ATTR_EX3_IGNORE_CASTER_MODIFIERS | ATTR_EX3_SUPPRESS_CASTER_PROCS:
            bad.append(f"{spell_id}: AttributesEx3 0x{ex3:X} lacks IGNORE_CASTER_MODIFIERS | SUPPRESS_CASTER_PROCS")
        if any(spell_mask(row)):
            bad.append(f"{spell_id}: SpellClassMask {_hex(spell_mask(row))}, expected none")
        if not _potency_excluded(entries.get(spell_id), 1) or _potency(entries.get(spell_id), 1):
            bad.append(f"{spell_id}: eff0 must be potency_excluded (script BP0) with no potency")
    row = rows_by_id.get(SPLASH)
    if row is not None and (not is_dummy(row, 2) or live_amount(row, 2) != SPLASH_PCT):
        bad.append(f"{SPLASH}: eff1 {row.get('Effect_2')}/{row.get('EffectAura_2')} live {live_amount(row, 2)}, "
                   f"expected a DUMMY of {SPLASH_PCT} (the splash percent)")
    return bad


# ---- (e) LoS / no-proc lists -----------------------------------------------------------------------------------------

def check_ignore_los(rows_by_id: dict[int, dict], expected=IGNORE_LOS_IDS) -> list[str]:
    bad = []
    have = {i for i, r in rows_by_id.items()
            if i in SV_BLOCK and _i(r, "AttributesEx2") & ATTR_EX2_IGNORE_LINE_OF_SIGHT}
    if have != set(expected):
        bad.append(f"AttributesEx2 0x4 on {sorted(have)}, expected exactly {sorted(expected)} (stale line 12): "
                   f"extra {sorted(have - set(expected))}, missing {sorted(set(expected) - have)}")
    blast = rows_by_id.get(EXPLOSIVE_BLAST)
    if blast is not None and not _i(blast, "AttributesEx2") & ATTR_EX2_IGNORE_LINE_OF_SIGHT:
        bad.append(f"{EXPLOSIVE_BLAST}: lost the stock AttributesEx2 0x4")
    return bad


def check_no_proc_helpers(rows_by_id: dict[int, dict], suppressed=NO_PROC_HELPERS, raisers=PROC_RAISERS) -> list[str]:
    bad = []
    for spell_id in sorted(suppressed):
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
        elif not _i(row, "AttributesEx3") & ATTR_EX3_SUPPRESS_CASTER_PROCS:
            bad.append(f"{spell_id}: AttributesEx3 0x{_i(row, 'AttributesEx3'):X} lacks SUPPRESS_CASTER_PROCS 0x10000")
    for spell_id in raisers:
        row = rows_by_id.get(spell_id)
        if row is not None and _i(row, "AttributesEx3") & ATTR_EX3_SUPPRESS_CASTER_PROCS:
            bad.append(f"{spell_id}: SUPPRESS_CASTER_PROCS on a proc-raising cast")
    return bad


# ---- (g) N5 exemption sets -------------------------------------------------------------------------------------------

def check_exemption_sets(bm_exempt, mm_shots, sv_class_two=SV_CLASS_TWO) -> list[str]:
    bad = []
    if set(bm_exempt) != set(mm_shots):
        bad.append(f"test_hunter_bm_data.EQUIPPED_ITEM_CLASS_EXEMPT {sorted(bm_exempt)} != test_hunter_mm_data."
                   f"PLAYER_CAST_SHOTS {sorted(mm_shots)}")
    for name, ids in (("EQUIPPED_ITEM_CLASS_EXEMPT", bm_exempt), ("PLAYER_CAST_SHOTS", mm_shots)):
        if not set(sv_class_two) <= set(ids):
            bad.append(f"{name} lacks {sorted(set(sv_class_two) - set(ids))} (N5)")
    return bad


# ---- (h) SpellMods ---------------------------------------------------------------------------------------------------

def check_masks_module(masks, expected=SPEC_MASKS) -> list[str]:
    bad = []
    for name, want in expected.items():
        got = getattr(masks, name, None)
        if got is None or tuple(got) != want:
            bad.append(f"_masks.{name} = {got}, expected {_hex(want)} (SURVIVAL 2.5)")
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
            got = (_i(row, f"Effect_{effect}"), _i(row, f"EffectAura_{effect}"))
            if got != (EFFECT_APPLY_AURA, aura):
                bad.append(f"{spell_id}: eff{effect - 1} effect / aura {got}, expected APPLY_AURA / {aura}")
            if op is not None and _i(row, f"EffectMiscValue_{effect}") != int(op):
                bad.append(f"{spell_id}: eff{effect - 1} op {row.get(f'EffectMiscValue_{effect}')}, expected "
                           f"{int(op)} ({op.name})")
            if _i(row, "SpellClassSet") != SPELLFAMILY_HUNTER:
                bad.append(f"{spell_id}: SpellClassSet {row.get('SpellClassSet')}, expected 9 (N7)")
            if effect_mask(row, effect) != want_mask:
                bad.append(f"{spell_id}: eff{effect - 1} mask {_hex(effect_mask(row, effect))}, expected "
                           f"{_hex(want_mask)}" + (f" ({ref})" if isinstance(ref, str) else ""))
    return bad


def check_spellmod_scoping(rows_by_id: dict[int, dict], ids) -> list[str]:
    """N7: every aura 107/108 effect of an S3a id is SpellClassSet 9 with a non-zero mask on that effect."""
    bad = []
    for spell_id in sorted(set(ids)):
        row = rows_by_id.get(spell_id)
        if row is None:
            continue
        for n in (1, 2, 3):
            if _i(row, f"Effect_{n}") != EFFECT_APPLY_AURA or _i(row, f"EffectAura_{n}") not in SPELLMOD_AURAS:
                continue
            if _i(row, "SpellClassSet") != SPELLFAMILY_HUNTER:
                bad.append(f"{spell_id}: eff{n - 1} SpellMod with SpellClassSet {row.get('SpellClassSet')} "
                           f"(family 0 matches every spell)")
            if not any(effect_mask(row, n)):
                bad.append(f"{spell_id}: eff{n - 1} SpellMod with an all-zero mask")
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


# ---- (i) spell_proc rows, carriers, N8 -------------------------------------------------------------------------------

def check_proc_rows(procs: list[dict], masks, expected=ALL_PROC_ROWS) -> list[str]:
    bad = []
    by_key: dict[int, list[dict]] = {}
    for p in procs:
        by_key.setdefault(int(p["SpellId"]), []).append(p)
    for key in expected:
        rows = by_key.get(key, [])
        if len(rows) != 1:
            bad.append(f"spell_proc {key}: declared {len(rows)} times, expected exactly once")
        if -key in by_key:
            bad.append(f"spell_proc {-key}: sign twin of the {key} row (live keys kept, positive new keys, L7)")
    for key, cols in expected.items():
        rows = by_key.get(key)
        if not rows:
            continue
        p = rows[0]
        for col, want in cols.items():
            if col == "mask":
                want, got = resolve_mask(masks, want), proc_mask(p)
                if got != want:
                    bad.append(f"spell_proc {key}: family mask {_hex(got)}, expected {_hex(want)}")
                continue
            got = float(p.get(col) or 0) if col == "Chance" else _i(p, col)
            if got != want:
                bad.append(f"spell_proc {key}: {col} {got if col == 'Chance' else hex(got)}, expected "
                           f"{want if col == 'Chance' else hex(want)} (SURVIVAL 8.1)")
    return bad


def check_proc_carriers(rows_by_id: dict[int, dict], carriers=PROC_CARRIERS, zero=ZERO_PROC_TYPE) -> list[str]:
    bad = []
    for spell_id, (proc_type, chance, effect, aura, trigger) in carriers.items():
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
            continue
        if _i(row, "ProcTypeMask") != proc_type:
            bad.append(f"{spell_id}: ProcTypeMask 0x{_i(row, 'ProcTypeMask'):X}, expected 0x{proc_type:X}")
        if chance is not None and _i(row, "ProcChance") != chance:
            bad.append(f"{spell_id}: ProcChance {row.get('ProcChance')}, expected {chance} (the row keeps chance 0)")
        got = (_i(row, f"Effect_{effect}"), _i(row, f"EffectAura_{effect}"), _i(row, f"EffectTriggerSpell_{effect}"))
        if got != (EFFECT_APPLY_AURA, aura, trigger):
            bad.append(f"{spell_id}: eff{effect - 1} effect / aura / trigger {got}, expected "
                       f"{(EFFECT_APPLY_AURA, aura, trigger)}")
        if aura == AURA_DUMMY and _i(row, f"EffectMiscValue_{effect}"):
            bad.append(f"{spell_id}: DUMMY carrier eff{effect - 1} misc {row.get(f'EffectMiscValue_{effect}')}, "
                       f"expected 0")
    for spell_id in sorted(set(zero)):
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
        elif _i(row, "ProcTypeMask"):
            bad.append(f"{spell_id}: ProcTypeMask 0x{_i(row, 'ProcTypeMask'):X}, expected 0 (no row: N8)")
    return bad


def check_m15(rows_by_id: dict[int, dict], talents: list[dict], procs: list[dict],
              accepted=M15_ACCEPTED) -> list[str]:
    """N8 / M15 on tab 362: a non-zero ProcTypeMask needs a spell_proc row (own id, or -first rank of its chain) unless
    listed inert, and no EffectSpellClassMask sits on an absent effect."""
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
                           f"({spell_id} / -{ranks[0]}) and not listed inert: the default entry reads stale masks")
            for n in (1, 2, 3):
                if not _i(row, f"Effect_{n}") and any(effect_mask(row, n)):
                    bad.append(f"{spell_id}: mask {_hex(effect_mask(row, n))} on absent eff{n - 1}")
    return bad


# ---- (j) Thrill of the Hunt ------------------------------------------------------------------------------------------

def check_thrill(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for spell_id, chance in zip(THRILL, (50, 100)):
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
            continue
        if (_i(row, "ProcChance"), _i(row, "ProcTypeMask")) != (chance, PROC_FLAG_DONE_SPELL_RANGED):
            bad.append(f"{spell_id}: ProcChance / ProcTypeMask {row.get('ProcChance')} / "
                       f"0x{_i(row, 'ProcTypeMask'):X}, expected {chance} / 0x100 (SV-B1)")
        if not is_dummy(row, 1) or _i(row, "EffectTriggerSpell_1"):
            bad.append(f"{spell_id}: eff0 is not the stock DUMMY carrier (trigger 0)")
        if not is_dummy(row, 2) or live_amount(row, 2) != 1000:
            bad.append(f"{spell_id}: eff1 {row.get('Effect_2')}/{row.get('EffectAura_2')} live {live_amount(row, 2)}, "
                       f"expected a DUMMY of 1000 ms (stored 999, both ranks)")
        for n in (1, 2, 3):
            if any(effect_mask(row, n)):
                bad.append(f"{spell_id}: eff{n - 1} mask {_hex(effect_mask(row, n))} (stale A_1 0xDE deleted)")
        if any(spell_mask(row)):
            bad.append(f"{spell_id}: SpellClassMask {_hex(spell_mask(row))}, expected none (0.17)")
    return bad


# ---- (k) family bits -------------------------------------------------------------------------------------------------

def check_family_bit_carriers(rows: list[dict]) -> list[str]:
    bad = []
    for row in rows:
        sid, mask = int(row["ID"]), spell_mask(row)
        if _i(row, "SpellClassSet") != SPELLFAMILY_HUNTER and sid < 200000:
            continue
        for (dword, bit), carriers in BIT_CARRIERS.items():
            if mask[dword] & bit and sid not in carriers:
                bad.append(f"{sid}: carries d{dword} 0x{bit:X} (only {sorted(carriers)}, SURVIVAL 2.4)")
        if sid in NO_BIT_IDS and any(mask):
            bad.append(f"{sid}: SpellClassMask {_hex(mask)}, expected no family bit (FAMILY-BITS 0.6)")
        if sid in EXACT_SPELL_MASKS and mask != EXACT_SPELL_MASKS[sid]:
            bad.append(f"{sid}: SpellClassMask {_hex(mask)}, expected {_hex(EXACT_SPELL_MASKS[sid])}")
    have = {int(r["ID"]) for r in rows}
    for sid in sorted(set(EXACT_SPELL_MASKS) - have):
        bad.append(f"{sid}: not declared")
    return bad


# ---- (l) stale line 19 -----------------------------------------------------------------------------------------------

def check_serpent_sting(rows_by_id: dict[int, dict], untaught) -> list[str]:
    """1978 eff1 (aura 271) amount 0, and no hunter SPELLMOD_EFFECT2 (misc 12) reader masking d0 0x4000 outside the
    untaught orphans (Noxious Stings 53295-53297 did)."""
    bad = []
    row = rows_by_id.get(SERPENT_STING)
    if row is None:
        bad.append(f"{SERPENT_STING}: not declared")
    elif _i(row, "EffectAura_2") != AURA_MOD_DAMAGE_FROM_CASTER or _amount_nonzero(row, 2):
        bad.append(f"{SERPENT_STING}: eff1 aura {row.get('EffectAura_2')} bp {row.get('EffectBasePoints_2')} die "
                   f"{row.get('EffectDieSides_2')}, expected aura 271 with amount 0")
    for spell_id, r in sorted(rows_by_id.items()):
        if spell_id in untaught:
            continue
        for n in (1, 2, 3):
            if _i(r, f"Effect_{n}") == EFFECT_APPLY_AURA and _i(r, f"EffectAura_{n}") in SPELLMOD_AURAS \
                    and _i(r, f"EffectMiscValue_{n}") == OP_EFFECT2 and effect_mask(r, n)[0] & D0_SERPENT_STING:
                bad.append(f"{spell_id}: eff{n - 1} SPELLMOD_EFFECT2 on d0 0x4000 makes Serpent Sting's aura 271 live "
                           f"(stale line 19)")
    return bad


def check_stale_readers(rows_by_id: dict[int, dict], readers=STALE_READERS) -> list[str]:
    bad = []
    for ids, effect in readers:
        for spell_id in ids:
            row = rows_by_id.get(spell_id)
            if row is None:
                bad.append(f"{spell_id}: not declared")
            elif any(effect_mask(row, effect)):
                bad.append(f"{spell_id}: eff{effect - 1} keeps mask {_hex(effect_mask(row, effect))} (stale raw, "
                           f"stale line 19 / brief 13)")
    row = rows_by_id.get(INVIGORATION_D1_B27)
    if row is not None and effect_mask(row, 1)[1] & D1_BURNING_TAR:
        bad.append(f"{INVIGORATION_D1_B27}: eff0 mask {_hex(effect_mask(row, 1))} still reads d1 b27 (Burning Tar)")
    return bad


# ---- (m) group and links ---------------------------------------------------------------------------------------------

def check_favored_prey_group(groups: list[dict], rules: list[dict]) -> list[str]:
    bad = []
    members = sorted(int(g["spell_id"]) for g in groups if int(g["id"]) == FAVORED_PREY_GROUP)
    if members != list(FAVORED_PREY_BUFFS):
        bad.append(f"spell_group {FAVORED_PREY_GROUP} members {members}, expected {list(FAVORED_PREY_BUFFS)}")
    mine = [r for r in rules if int(r.get("group_id") or r["id"]) == FAVORED_PREY_GROUP]
    if [int(r["stack_rule"]) for r in mine] != [GROUP_RULE_EXCLUSIVE]:
        bad.append(f"spell_group_rule({FAVORED_PREY_GROUP}) {[r.get('stack_rule') for r in mine]}, expected exactly "
                   f"one with rule {GROUP_RULE_EXCLUSIVE} (exclusive)")
    for g in groups:
        if int(g["spell_id"]) in FAVORED_PREY_BUFFS and int(g["id"]) != FAVORED_PREY_GROUP:
            bad.append(f"Favored Prey buff {g['spell_id']} also in spell_group {g['id']}")
    return bad


def check_links(linked: list[dict], links=LINKS) -> list[str]:
    have = [(int(r["spell_trigger"]), int(r["spell_effect"]), int(r["type"])) for r in linked]
    bad = [f"linked_spell{link} not declared" for link in links if link not in have]
    for link in links:
        if have.count(link) > 1:
            bad.append(f"linked_spell{link} declared {have.count(link)} times")
    effects = {link[1] for link in links}
    for trigger, effect, kind in have:
        if effect in effects and (trigger, effect, kind) not in links:
            bad.append(f"linked_spell({trigger}, {effect}, {kind}) not in the spec (only {sorted(links)})")
    return bad


# ---- (n) bindings ----------------------------------------------------------------------------------------------------

def check_bindings(bound: list[dict], removals: list[dict], expected=SCRIPT_BINDINGS) -> list[str]:
    bad = []
    for name, ids in expected.items():
        have = {int(r["spell_id"]) for r in bound if r["ScriptName"] == name}
        if have != set(ids):
            bad.append(f"{name}: bound to {sorted(have)}, expected {sorted(ids)} (positive keys, L7)")
    got = {(int(r["spell_id"]), r["ScriptName"]) for r in removals}
    for key in sorted((S3A_UNBINDS | S3B_UNBINDS) - got):
        bad.append(f"unbind_script{key} not declared")
    for spell_id, name in sorted(got):
        if name in KEPT_STOCK_CLASSES and (spell_id, name) not in S3B_UNBINDS:
            bad.append(f"unbind_script({spell_id}, {name}): that stock class stays bound")
    for r in bound:
        if int(r["spell_id"]) < 0:
            bad.append(f"{r['ScriptName']} bound to the negative key {r['spell_id']} (positive keys, L7)")
    if SHOT_MANA_BINDING not in {(int(r["spell_id"]), r["ScriptName"]) for r in bound}:
        bad.append(f"scripted_by{SHOT_MANA_BINDING} missing (ruling 6 restores through the existing shot-mana path)")
    return bad


# ---- (o) user ruling 6 and Lock and Load -----------------------------------------------------------------------------

def check_ruling_6(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    r1, r2 = rows_by_id.get(DEADLY_FOCUS[0]), rows_by_id.get(DEADLY_FOCUS[1])
    raptor = rows_by_id.get(RAPTOR_STRIKE)
    if r1 is None or r2 is None or raptor is None:
        return [f"{DEADLY_FOCUS} / {RAPTOR_STRIKE}: not declared"]
    if not is_dummy(r2, 3) or live_amount(r2, 3) != RAPTOR_MANA_PCT:
        bad.append(f"{DEADLY_FOCUS[1]}: eff2 {r2.get('Effect_3')}/{r2.get('EffectAura_3')} live {live_amount(r2, 3)}, "
                   f"expected a DUMMY marker of {RAPTOR_MANA_PCT} (ruling 6)")
    if any(effect_mask(r2, 3)) or _i(r2, "EffectTriggerSpell_3"):
        bad.append(f"{DEADLY_FOCUS[1]}: eff2 marker carries mask {_hex(effect_mask(r2, 3))} / trigger "
                   f"{r2.get('EffectTriggerSpell_3')} (no SpellMod, no family-0 leak)")
    if _i(r1, "Effect_3"):
        bad.append(f"{DEADLY_FOCUS[0]}: has an eff2 {r1.get('Effect_3')} (only rank 2 carries the capstone marker)")
    if not DEADLY_FOCUS_MANA_TEXT.search(str(r2.get("Description_Lang_enUS") or "")):
        bad.append(f"{DEADLY_FOCUS[1]}: capstone text does not say 'Raptor Strike restores 5% of your base mana.'")
    if "mana" in str(raptor.get("Description_Lang_enUS") or "").lower():
        bad.append(f"{RAPTOR_STRIKE}: text keeps a mana clause: {raptor.get('Description_Lang_enUS')!r} (ruling 6)")
    return bad


# 56342-56344 (SURVIVAL 6.1, B4): eff0 trigger bp, eff1 DUMMY bp (live 3 / 6 / 10 %), eff2 DUMMY bp
LOCK_AND_LOAD_VALUES = {
    56342: (32, 2, 0), 56343: (65, 5, 0), 56344: (99, 9, 1999),     # 56344 eff2 = Chain Reaction 2000 ms (0-verify 4l)
}
LOCK_AND_LOAD_MARKER_MS = 5000
ATTR_EX3_SUPPRESS_AND_IGNORE = ATTR_EX3_IGNORE_CASTER_MODIFIERS | ATTR_EX3_SUPPRESS_CASTER_PROCS


def check_lock_and_load(rows_by_id: dict[int, dict], marker_duration_index: int) -> list[str]:
    """(q) B4 + 0-verify binding decision 1: the three ranks keep the stock DBC ProcTypeMask 0x240000 / chance 100, the
    trigger eff0 (-> 56453) with bp 32 / 65 / 99, the DUMMY eff1 bp 2 / 5 / 9, and an aura eff2 on EVERY rank (inert
    DUMMY bp 0 on 56342 / 56343, Chain Reaction bp 1999 on 56344) so -56342's disable_effects_mask 0x4 is valid; no
    SpellMod mask on any of them. 56453 is the one-charge, free-shot buff with the new text; 67544 lasts 5000 ms and has
    no stale reader masks."""
    bad = []
    for spell_id, (trigger_bp, dummy_bp, eff2_bp) in LOCK_AND_LOAD_VALUES.items():
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
            continue
        if _i(row, "ProcTypeMask") != LOCK_AND_LOAD_PROC_TYPE:
            bad.append(f"{spell_id}: ProcTypeMask 0x{_i(row, 'ProcTypeMask'):X}, expected "
                       f"0x{LOCK_AND_LOAD_PROC_TYPE:X}")
        if _i(row, "ProcChance") != 100:
            bad.append(f"{spell_id}: ProcChance {row.get('ProcChance')}, expected 100")
        if (_i(row, "Effect_1"), _i(row, "EffectAura_1"), _i(row, "EffectTriggerSpell_1")) != \
                (EFFECT_APPLY_AURA, AURA_PROC_TRIGGER_SPELL, LOCK_AND_LOAD_BUFF):
            bad.append(f"{spell_id}: eff0 is not PROC_TRIGGER_SPELL -> {LOCK_AND_LOAD_BUFF}")
        if _i(row, "EffectBasePoints_1") != trigger_bp:
            bad.append(f"{spell_id}: eff0 bp {row.get('EffectBasePoints_1')}, expected {trigger_bp}")
        if not is_dummy(row, 2) or _i(row, "EffectBasePoints_2") != dummy_bp:
            bad.append(f"{spell_id}: eff1 is not a DUMMY of bp {dummy_bp} (live {dummy_bp + 1} %): "
                       f"{row.get('Effect_2')}/{row.get('EffectAura_2')} bp {row.get('EffectBasePoints_2')}")
        if _i(row, "Effect_3") != EFFECT_APPLY_AURA or _i(row, "EffectAura_3") != AURA_DUMMY:
            bad.append(f"{spell_id}: eff2 {row.get('Effect_3')}/{row.get('EffectAura_3')}, expected an aura DUMMY on "
                       f"every rank (-56342 disable_effects_mask 0x4 needs an aura effect, SpellMgr.cpp:2125)")
        elif _i(row, "EffectBasePoints_3") != eff2_bp:
            bad.append(f"{spell_id}: eff2 bp {row.get('EffectBasePoints_3')}, expected {eff2_bp}"
                       + (" (Chain Reaction 2000 ms)" if eff2_bp else " (inert marker)"))
        if _i(row, "CastingTimeIndex") != 1 or _i(row, "EquippedItemClass") != -1:
            bad.append(f"{spell_id}: CastingTimeIndex / EquippedItemClass {row.get('CastingTimeIndex')} / "
                       f"{row.get('EquippedItemClass')}, expected 1 / -1")
        for n in (1, 2, 3):
            if any(effect_mask(row, n)):
                bad.append(f"{spell_id}: eff{n - 1} carries the SpellMod mask {_hex(effect_mask(row, n))}")
    buff = rows_by_id.get(LOCK_AND_LOAD_BUFF)
    if buff is None:
        bad.append(f"{LOCK_AND_LOAD_BUFF}: not declared")
    else:
        if _i(buff, "ProcCharges") != 1:
            bad.append(f"{LOCK_AND_LOAD_BUFF}: ProcCharges {buff.get('ProcCharges')}, expected 1 (one free shot)")
        text = str(buff.get("Description_Lang_enUS") or "") + str(buff.get("AuraDescription_Lang_enUS") or "")
        if "$56342s3" in text or "cooldown" not in text.lower():
            bad.append(f"{LOCK_AND_LOAD_BUFF}: text {text!r} keeps the stale '$56342s3 sec cooldown' wording")
    marker = rows_by_id.get(LOCK_AND_LOAD_MARKER)
    if marker is None:
        bad.append(f"{LOCK_AND_LOAD_MARKER}: not declared")
    else:
        if _i(marker, "DurationIndex") != marker_duration_index:
            bad.append(f"{LOCK_AND_LOAD_MARKER}: DurationIndex {marker.get('DurationIndex')}, expected "
                       f"{marker_duration_index} ({LOCK_AND_LOAD_MARKER_MS} ms)")
        for n in (1, 2, 3):
            if any(effect_mask(marker, n)):
                bad.append(f"{LOCK_AND_LOAD_MARKER}: eff{n - 1} keeps the stale mask {_hex(effect_mask(marker, n))}")
    return bad


# ---- (q) Explosive Trap pair, Wyvern Sting, S3b helpers --------------------------------------------------------------

TRAP_EFFECT_STOCK_BP, TRAP_EFFECT_STOCK_AMPLITUDE = 11, 2000      # 13812 eff1 (aura 3 -> 226 keeps the amplitude); bp stock 14 x0.8 (TUNE1)
EFFECT_PERSISTENT_AREA_AURA = 27
WYVERN_DURATION_MS = 2000
WYVERN_FIELDS = {"Effect_1": EFFECT_APPLY_AURA, "EffectAura_1": 79, "EffectMiscValue_1": 127, "EffectBasePoints_1": -31,
                 "AuraInterruptFlags": 0, "ProcTypeMask": 0, "Mechanic": 0, "EffectMechanic_1": 0,
                 "EquippedItemClass": 2}      # aura 79 = MOD_DAMAGE_PERCENT_DONE, misc 127 = all schools, live -30 %


def check_explosive_trap_effect(row: dict | None) -> list[str]:
    """(q) B5: 13812 eff1 becomes the PERIODIC_DUMMY (aura 226) persistent area aura with the stock bp / amplitude (the
    script pays the tick; a stock aura 3 would double-damage); eff0 stays the SCHOOL_DAMAGE blast."""
    if row is None:
        return [f"{EXPLOSIVE_TRAP_EFFECT}: not declared"]
    bad = []
    if (_i(row, "Effect_2"), _i(row, "EffectAura_2")) != (EFFECT_PERSISTENT_AREA_AURA, AURA_PERIODIC_DUMMY):
        bad.append(f"{EXPLOSIVE_TRAP_EFFECT}: eff1 {row.get('Effect_2')}/{row.get('EffectAura_2')}, expected "
                   f"PERSISTENT_AREA_AURA / PERIODIC_DUMMY ({EFFECT_PERSISTENT_AREA_AURA}/{AURA_PERIODIC_DUMMY})")
    if _i(row, "EffectBasePoints_2") != TRAP_EFFECT_STOCK_BP:
        bad.append(f"{EXPLOSIVE_TRAP_EFFECT}: eff1 bp {row.get('EffectBasePoints_2')}, expected the stock "
                   f"{TRAP_EFFECT_STOCK_BP}")
    if _i(row, "EffectAuraPeriod_2") != TRAP_EFFECT_STOCK_AMPLITUDE:
        bad.append(f"{EXPLOSIVE_TRAP_EFFECT}: eff1 amplitude {row.get('EffectAuraPeriod_2')}, expected the stock "
                   f"{TRAP_EFFECT_STOCK_AMPLITUDE}")
    if (_i(row, "Effect_1"), _i(row, "EffectAura_1")) != (EFFECT_SCHOOL_DAMAGE, 0):
        bad.append(f"{EXPLOSIVE_TRAP_EFFECT}: eff0 {row.get('Effect_1')}/{row.get('EffectAura_1')}, expected the "
                   f"unchanged SCHOOL_DAMAGE blast")
    return bad


def check_trap_fire_tick(row: dict | None, entry: dict | None) -> list[str]:
    """(q) B5: 202057's BP0 is the script's snapshot, exact because ppl 0 and die sides <= 1 (CalcBaseValue -1 /
    CalcValue +1; die sides 1 is the DSL convention, 0-verify decision 5 - not 0), potency_excluded, no potency,
    IGNORE_CASTER_MODIFIERS | SUPPRESS_CASTER_PROCS."""
    if row is None or entry is None:
        return [f"{TRAP_FIRE}: not declared"]
    bad = []
    if _i(row, "Effect_1") != EFFECT_SCHOOL_DAMAGE:
        bad.append(f"{TRAP_FIRE}: eff0 {row.get('Effect_1')}, expected SCHOOL_DAMAGE")
    if float(row.get("EffectRealPointsPerLevel_1") or 0) != 0.0:
        bad.append(f"{TRAP_FIRE}: ppl {row.get('EffectRealPointsPerLevel_1')}, expected 0 (BP0 must not level-scale)")
    if _i(row, "EffectDieSides_1") > 1:
        bad.append(f"{TRAP_FIRE}: die sides {row.get('EffectDieSides_1')}, expected <= 1 (no random spread)")
    if not _potency_excluded(entry, 1) or _potency(entry, 1):
        bad.append(f"{TRAP_FIRE}: eff0 must be potency_excluded (script BP0) with no potency")
    if _i(row, "AttributesEx3") & ATTR_EX3_SUPPRESS_AND_IGNORE != ATTR_EX3_SUPPRESS_AND_IGNORE:
        bad.append(f"{TRAP_FIRE}: AttributesEx3 0x{_i(row, 'AttributesEx3'):X} lacks IGNORE_CASTER_MODIFIERS | "
                   f"SUPPRESS_CASTER_PROCS")
    return bad


def check_wyvern_sting(row: dict | None, duration_index: int) -> list[str]:
    """(q) B7 / SURVIVAL 5.12: 19386 is MOD_DAMAGE_PERCENT_DONE (aura 79, misc 127) bp -31 (live -30 %) for 2000 ms; the
    stock sleep interrupt flags, proc mask and mechanics are zeroed (the 202059 sleep is the only sleep); the
    player-cast shot keeps EquippedItemClass 2 (N5)."""
    if row is None:
        return [f"{WYVERN_STING}: not declared"]
    bad = [f"{WYVERN_STING}: {key} {row.get(key)}, expected {want}" for key, want in WYVERN_FIELDS.items()
           if _i(row, key) != want]
    if _i(row, "DurationIndex") != duration_index:
        bad.append(f"{WYVERN_STING}: DurationIndex {row.get('DurationIndex')}, expected {duration_index} "
                   f"({WYVERN_DURATION_MS} ms)")
    return bad


def check_s3b_helper_cast_time(rows_by_id: dict[int, dict], ids=NEW_HELPER_IDS) -> list[str]:
    """(q) C-3: every S3a / S3b helper is an instant cast through CastingTimeIndex 1 (the DSL's 0 is no cast time)."""
    return [f"{i}: CastingTimeIndex {rows_by_id[i].get('CastingTimeIndex')}, expected 1 (C-3)"
            for i in ids if i in rows_by_id and _i(rows_by_id[i], "CastingTimeIndex") != 1] + \
           [f"{i}: not declared" for i in ids if i not in rows_by_id]


# ---- (p) S2-FIX ------------------------------------------------------------------------------------------------------

def check_s2fix_guards(rows_by_id: dict[int, dict], cast_times: dict[int, int]) -> list[str]:
    bad = []
    problems, seen = check_ranged_shot_cast_bars(rows_by_id, cast_times)
    bad += problems
    row = rows_by_id.get(EXPLOSIVE_SHOT)
    if row is None or not _is_hunter_shot(row):
        bad.append(f"check_ranged_shot_cast_bars does not see {EXPLOSIVE_SHOT}")
    else:
        mine, one = check_ranged_shot_cast_bars({EXPLOSIVE_SHOT: row}, cast_times)
        if one != 1 or mine:
            bad.append(f"{EXPLOSIVE_SHOT}: cast-bar guard saw {one} row(s), problems {mine}")
    problems, seen = check_instant_cast_mods(rows_by_id, cast_times)
    bad += problems
    if seen < INSTANT_MODS_SEEN_MIN:
        bad.append(f"check_instant_cast_mods saw {seen} instant mods, expected >= {INSTANT_MODS_SEEN_MIN}")
    return bad


# ---- real data -------------------------------------------------------------------------------------------------------

def _touched_ids() -> set[int]:
    return {*NEW_IDS, *TAB_RANKS, *EDITED_STOCK_IDS, *SV_CLASS_TWO, 34498}


def _minus_one_ids() -> set[int]:
    return _touched_ids() - SV_CLASS_TWO


def _overlay_talents(package) -> dict[int, dict]:
    return {**state.load_stock_rows(dbcfmt.TALENT),
            **{int(r["ID"]): r for r in map(build.build_talent_row, package.talents)}}


class HunterSvDataTest(unittest.TestCase):
    def assertClean(self, problems: list[str]):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_tab_362_layout(self):
        package = package_data()["package"]
        built = [build.build_talent_row(t) for t in package.talents]
        self.assertClean(check_tab_362(package.talents, built, package.skill_line_abilities, package.trainer_spells))

    def test_tab_363_untouched(self):
        package = package_data()["package"]
        self.assertClean(check_tab_363_kept(package.talents, [build.build_talent_row(t) for t in package.talents]))

    def test_orphaned_ranks_in_no_talent_row(self):
        talents = _overlay_talents(package_data()["package"])
        self.assertClean(check_orphans(list(talents.values()), ORPHANS))
        self.assertClean(check_sniper_training_off_sv(list(talents.values())))

    def test_talent_dbc_blocks_contiguous(self):
        package = package_data()["package"]
        stock = state.load_stock_rows(dbcfmt.TALENT)
        overlay = _overlay_talents(package)
        ordered = dbcfile.order_talent_rows(list(overlay.values()), list(stock.values()))
        self.assertClean(check_talent_blocks(ordered))

    def test_every_rank_in_exactly_one_talent_row(self):
        data = package_data()
        package = data["package"]
        self.assertClean(check_rank_rows_unique(package.talents, set(data["rows_by_id"]),
                                                dict(getattr(package, "spell_var_names", {}) or {})))

    def test_castables(self):
        data = package_data()
        self.assertClean(check_castables(data["rows_by_id"], _cast_times(data["reuse"])))
        self.assertClean(check_potency_levels(data["rows_by_id"]))

    def test_explosive_shot(self):
        data = package_data()
        rows, package = data["rows_by_id"], data["package"]
        entries = {int(e["id"]): e for e in package.spells}
        source = spell_call_source(HUNTER_SPELLS_PY.read_text(encoding="utf-8"), EXPLOSIVE_SHOT)
        self.assertClean(check_explosive_shot(rows.get(EXPLOSIVE_SHOT), entries.get(EXPLOSIVE_SHOT), source,
                                              _cast_times(data["reuse"]),
                                              data["reuse"].duration_index(EXPLOSIVE_SHOT_DURATION_MS)))
        self.assertClean(check_explosive_blast(rows.get(EXPLOSIVE_BLAST), entries.get(EXPLOSIVE_BLAST),
                                               package.spell_bonus_data))
        self.assertClean(check_splashes(rows, entries))

    def test_line_of_sight_and_no_proc_lists(self):
        rows = package_data()["rows_by_id"]
        self.assertClean(check_ignore_los(rows))
        self.assertClean(check_no_proc_helpers(rows))

    def test_visibility_lists(self):
        self.assertClean(check_visibility(package_data()["rows_by_id"], VISIBLE, HIDDEN, ()))

    def test_equipped_item_class(self):
        rows = package_data()["rows_by_id"]
        self.assertClean(check_equipped_item_class(rows, _minus_one_ids(), SV_CLASS_TWO))
        from lib.test_hunter_bm_data import EQUIPPED_ITEM_CLASS_EXEMPT  # noqa: PLC0415
        from lib.test_hunter_mm_data import PLAYER_CAST_SHOTS  # noqa: PLC0415
        self.assertClean(check_exemption_sets(EQUIPPED_ITEM_CLASS_EXEMPT, PLAYER_CAST_SHOTS))

    def test_masks_module_holds_the_spec_composites(self):
        self.assertClean(check_masks_module(load_masks_module()))

    def test_spellmod_rows(self):
        rows = package_data()["rows_by_id"]
        self.assertClean(check_spellmod_specs(rows, load_masks_module()))
        self.assertClean(check_spellmod_scoping(rows, _touched_ids()))
        self.assertClean(check_removed_effects(rows))

    def test_spell_proc_rows(self):
        self.assertClean(check_proc_rows(package_data()["package"].spell_procs, load_masks_module()))

    def test_proc_carriers_and_m15(self):
        data = package_data()
        package = data["package"]
        self.assertClean(check_proc_carriers(data["rows_by_id"]))
        self.assertClean(check_m15(data["rows_by_id"], package.talents, package.spell_procs))

    def test_thrill_of_the_hunt(self):
        self.assertClean(check_thrill(package_data()["rows_by_id"]))

    def test_family_bit_carriers(self):
        self.assertClean(check_family_bit_carriers(package_data()["rows"]))

    def test_no_reader_holds_the_pet_bit(self):
        data = package_data()
        self.assertClean(check_no_pet_bit_readers(data["rows_by_id"], _touched_ids(), data["package"].spell_procs))

    def test_serpent_sting_and_stale_readers(self):
        rows = package_data()["rows_by_id"]
        self.assertClean(check_serpent_sting(rows, set(ORPHANS)))
        self.assertClean(check_stale_readers(rows))

    def test_favored_prey_group_and_links(self):
        package = package_data()["package"]
        self.assertClean(check_favored_prey_group(package.spell_groups, package.spell_group_rules))
        self.assertClean(check_links(package.linked_spells))

    def test_script_bindings(self):
        package = package_data()["package"]
        self.assertClean(check_bindings(package.spell_script_names, package.script_removals))

    def test_ruling_6(self):
        self.assertClean(check_ruling_6(package_data()["rows_by_id"]))

    def test_lock_and_load_s3b(self):
        data = package_data()
        self.assertClean(check_lock_and_load(data["rows_by_id"],
                                             data["reuse"].duration_index(LOCK_AND_LOAD_MARKER_MS)))

    def test_explosive_trap_pair_s3b(self):
        data = package_data()
        rows = data["rows_by_id"]
        entries = {int(e["id"]): e for e in data["package"].spells}
        self.assertClean(check_explosive_trap_effect(rows.get(EXPLOSIVE_TRAP_EFFECT)))
        self.assertClean(check_trap_fire_tick(rows.get(TRAP_FIRE), entries.get(TRAP_FIRE)))

    def test_wyvern_sting_s3b(self):
        data = package_data()
        self.assertClean(check_wyvern_sting(data["rows_by_id"].get(WYVERN_STING),
                                            data["reuse"].duration_index(WYVERN_DURATION_MS)))

    def test_s3b_helper_cast_time_and_los_list(self):
        rows = package_data()["rows_by_id"]
        self.assertClean(check_s3b_helper_cast_time(rows))
        self.assertEqual(IGNORE_LOS_IDS, frozenset({202048, 202049, 202050, 202053, 202056, 202057, 202059}))
        self.assertClean(check_ignore_los(rows))

    def test_s2fix_guards_still_pass(self):
        data = package_data()
        self.assertClean(check_s2fix_guards(data["rows_by_id"], _cast_times(data["reuse"])))


# ---- negative fixtures: every check passes a good input and fires on a crafted bad copy ------------------------------

def changed(row: dict, **cols) -> dict:
    out = copy.deepcopy(row)
    out.update(cols)
    return out


CAST_TIMES = {0: 0, 1: 0, 4: 1000, 5: 2000, 16: 1500, 18: -1000000}
DUR2000 = 32
DUR5000 = 33
MASKS = load_masks_module()


def good_tab() -> list[dict]:
    return [{"id": tid, "tab_id": TAB, "tier": cell[0], "column": cell[1], "rank_spell_ids": list(ranks),
             "depends_on": None, "raw_overrides": None, "flags": 1 if tid in CASTABLE_ROWS else 0}
            for tid, (cell, ranks) in TAB_LAYOUT.items()]


GOOD_SLA = [{"id": k, "spell_id": v, "skill_line": SKILL_LINE_SV, "class_mask": CLASSMASK_HUNTER}
            for k, v in SV_SLA.items()]


def good_mm_tab() -> list[dict]:
    rows = [{"id": 5000 + n, "tab_id": MM_TAB, "tier": n // 4, "column": n % 4,
             "rank_spell_ids": [1, 2, 3] if n < 14 else [1, 2]} for n in range(32)]          # 32 rows, 78 points
    rows.append({"id": SNIPER_TRAINING_ROW, "tab_id": MM_TAB, "tier": 7, "column": 2,
                 "rank_spell_ids": list(SNIPER_TRAINING_RANKS)})
    return rows


def good_castable_rows() -> dict[int, dict]:
    rows = {}
    for spell_id, (mask, level, unit) in CASTABLE_SPECS.items():
        row = {"ID": spell_id, **CASTABLE_FIELDS, **CASTABLE_EXTRA[spell_id], "SpellLevel": level, "BaseLevel": level,
               "MaxLevel": 0, "FacingCasterFlags": 1 if unit else 0}
        for n, word in enumerate(mask, start=1):
            row[f"SpellClassMask_{n}"] = word
        rows[spell_id] = row
    return rows


def good_explosive() -> tuple[dict, dict, str]:
    row = {"ID": EXPLOSIVE_SHOT, **EXPLOSIVE_SHOT_FIELDS, "Speed": 40.0, "SpellClassSet": 9,
           "SpellClassMask_2": D1_EXPLOSIVE_SHOT, "DurationIndex": DUR2000, "AttributesEx5": 0,
           "AttributesEx2": 0x20000}
    entry = {"id": EXPLOSIVE_SHOT, "effect1": {"_potency": {"kind": "direct", "total_potency": 76.5,
                                                            "ap_coefficient": 0.43}},
             "effect2": {}}
    source = ("explosive_shot_53301 = spell(\n    id=53301,\n    raw_overrides={'SpellLevel': 30, "
              "'CastingTimeIndex': 18},\n")
    return row, entry, source


def good_blast() -> tuple[dict, dict, list[dict]]:
    row = {"ID": EXPLOSIVE_BLAST, "Effect_1": EFFECT_SCHOOL_DAMAGE, "SpellLevel": 30, "BaseLevel": 30, "MaxLevel": 0,
           "EquippedItemClass": -1, "SpellClassMask_3": D2_EXPLOSIVE_SHOT_TICK, "AttributesEx2": 0x4}
    entry = {"id": EXPLOSIVE_BLAST, "effect1": {"_potency": {"kind": "direct", "total_potency": 26.0,
                                                             "ap_coefficient": 0.1429}}}
    return row, entry, [{"entry": EXPLOSIVE_BLAST, "ap_bonus": 0.1429}]


def good_splash_rows() -> tuple[dict[int, dict], dict[int, dict]]:
    rows, entries = {}, {}
    for spell_id in SPLASHES:
        rows[spell_id] = {"ID": spell_id, "Effect_1": EFFECT_SCHOOL_DAMAGE, "ImplicitTargetA_1": 87,
                          "ImplicitTargetB_1": 16, "Targets": 0x40, "EquippedItemClass": -1, "SpellClassSet": 9,
                          "DefenseType": 3, "SpellLevel": 30, "SchoolMask": SCHOOL_FIRE,
                          "AttributesEx2": ATTR_EX2_CANT_CRIT, "AttributesEx3": 0x20010000}
        entries[spell_id] = {"id": spell_id, "effect1": {"_potency_excluded": "40% share (script BP0)"}}
    rows[SPLASH].update(Effect_2=EFFECT_APPLY_AURA, EffectAura_2=AURA_DUMMY, EffectBasePoints_2=39, EffectDieSides_2=1)
    return rows, entries


def good_spellmod_rows() -> dict[int, dict]:
    rows: dict[int, dict] = {}
    for ids, effect, aura, op, ref in SPELLMOD_SPECS:
        mask = resolve_mask(MASKS, ref)
        for spell_id in ids:
            row = rows.setdefault(spell_id, {"ID": spell_id, "SpellClassSet": 9})
            row.update({f"Effect_{effect}": EFFECT_APPLY_AURA, f"EffectAura_{effect}": aura,
                        f"EffectMiscValue_{effect}": int(op) if op is not None else 0})
            for n, word in enumerate(mask, start=1):
                row[f"EffectSpellClassMask{LETTERS[effect - 1]}_{n}"] = word
    return rows


def good_procs() -> list[dict]:
    procs = []
    for key, cols in ALL_PROC_ROWS.items():
        p = {"SpellId": key}
        for col, want in cols.items():
            if col == "mask":
                m = resolve_mask(MASKS, want)
                p.update(SpellFamilyMask0=m[0], SpellFamilyMask1=m[1], SpellFamilyMask2=m[2])
            else:
                p[col] = want
        procs.append(p)
    return procs


def good_carrier_rows() -> dict[int, dict]:
    rows = {}
    for spell_id, (proc_type, chance, effect, aura, trigger) in PROC_CARRIERS.items():
        rows[spell_id] = {"ID": spell_id, "ProcTypeMask": proc_type, "ProcChance": chance or 100,
                          f"Effect_{effect}": EFFECT_APPLY_AURA, f"EffectAura_{effect}": aura,
                          f"EffectTriggerSpell_{effect}": trigger}
    for spell_id in ZERO_PROC_TYPE:
        rows.setdefault(spell_id, {"ID": spell_id, "ProcTypeMask": 0})
    return rows


def good_thrill_rows() -> dict[int, dict]:
    return {i: {"ID": i, "ProcChance": c, "ProcTypeMask": 0x100, "Effect_1": EFFECT_APPLY_AURA,
                "EffectAura_1": AURA_DUMMY, "EffectBasePoints_1": 32, "Effect_2": EFFECT_APPLY_AURA,
                "EffectAura_2": AURA_DUMMY, "EffectBasePoints_2": 999, "EffectDieSides_2": 1}
            for i, c in zip(THRILL, (50, 100))}


def good_bit_rows() -> list[dict]:
    rows = []
    for sid, mask in EXACT_SPELL_MASKS.items():
        rows.append({"ID": sid, "SpellClassSet": 9, "SpellClassMask_1": mask[0], "SpellClassMask_2": mask[1],
                     "SpellClassMask_3": mask[2]})
    rows += [{"ID": sid, "SpellClassSet": 9} for sid in sorted(NO_BIT_IDS)]
    rows.append({"ID": 1495, "SpellClassSet": 9, "SpellClassMask_1": D0_MONGOOSE_BITE})
    return rows


def good_bindings() -> tuple[list[dict], list[dict]]:
    bound = [{"spell_id": i, "ScriptName": n} for n, ids in SCRIPT_BINDINGS.items() for i in ids]
    bound.append({"spell_id": SHOT_MANA_BINDING[0], "ScriptName": SHOT_MANA_BINDING[1]})
    removals = [{"spell_id": k, "ScriptName": n} for k, n in sorted(S3A_UNBINDS | S3B_UNBINDS)]
    return bound, removals


def good_ruling_rows() -> dict[int, dict]:
    pct = {"Effect_1": EFFECT_APPLY_AURA, "EffectAura_1": PCT}
    return {
        202080: {"ID": 202080, **pct, "Description_Lang_enUS": "Increases ... by $s1%.\n\n|cFF9D9D9DCapstone Bonus: "
                                                               "Raptor Strike restores 5% of your base mana.|r"},
        202081: {"ID": 202081, **pct, "Effect_2": EFFECT_APPLY_AURA, "EffectAura_2": FLAT,
                 "Effect_3": EFFECT_APPLY_AURA, "EffectAura_3": AURA_DUMMY, "EffectBasePoints_3": 24,
                 "EffectDieSides_3": 1,
                 "Description_Lang_enUS": "Increases ... by $s1%.\n\nCapstone Bonus: ... more range. Raptor Strike "
                                          "restores $s3% of your base mana."},
        RAPTOR_STRIKE: {"ID": RAPTOR_STRIKE, "Description_Lang_enUS": "A quick strike that deals {pot1} Physical "
                                                                      "damage."},
    }


def good_lnl_rows() -> dict[int, dict]:
    rows = {}
    for spell_id, (trigger_bp, dummy_bp, eff2_bp) in LOCK_AND_LOAD_VALUES.items():
        rows[spell_id] = {"ID": spell_id, "ProcTypeMask": LOCK_AND_LOAD_PROC_TYPE, "ProcChance": 100,
                          "CastingTimeIndex": 1, "EquippedItemClass": -1,
                          "Effect_1": EFFECT_APPLY_AURA, "EffectAura_1": AURA_PROC_TRIGGER_SPELL,
                          "EffectTriggerSpell_1": LOCK_AND_LOAD_BUFF, "EffectBasePoints_1": trigger_bp,
                          "Effect_2": EFFECT_APPLY_AURA, "EffectAura_2": AURA_DUMMY, "EffectBasePoints_2": dummy_bp,
                          "Effect_3": EFFECT_APPLY_AURA, "EffectAura_3": AURA_DUMMY, "EffectBasePoints_3": eff2_bp}
    rows[LOCK_AND_LOAD_BUFF] = {"ID": LOCK_AND_LOAD_BUFF, "ProcCharges": 1,
                                "Description_Lang_enUS": "Your next Arcane Shot or Explosive Shot triggers no "
                                                         "cooldown and costs no mana."}
    rows[LOCK_AND_LOAD_MARKER] = {"ID": LOCK_AND_LOAD_MARKER, "DurationIndex": DUR5000}
    return rows


def good_trap_effect_row() -> dict:
    return {"ID": EXPLOSIVE_TRAP_EFFECT, "Effect_1": EFFECT_SCHOOL_DAMAGE, "EffectAura_1": 0,
            "Effect_2": EFFECT_PERSISTENT_AREA_AURA, "EffectAura_2": AURA_PERIODIC_DUMMY,
            "EffectBasePoints_2": TRAP_EFFECT_STOCK_BP, "EffectAuraPeriod_2": TRAP_EFFECT_STOCK_AMPLITUDE}


def good_trap_fire_tick() -> tuple[dict, dict]:
    row = {"ID": TRAP_FIRE, "Effect_1": EFFECT_SCHOOL_DAMAGE, "EffectRealPointsPerLevel_1": 0.0,
           "EffectDieSides_1": 1, "AttributesEx3": ATTR_EX3_SUPPRESS_AND_IGNORE}
    entry = {"id": TRAP_FIRE, "effect1": {"_potency_excluded": "snapshot BP from spell_hun_explosive_trap_fire"}}
    return row, entry


def good_wyvern_row() -> dict:
    return {"ID": WYVERN_STING, **WYVERN_FIELDS, "DurationIndex": DUR2000}


class HunterSvDataNegativeTest(unittest.TestCase):
    def test_tab_362_guard(self):
        talents = good_tab()
        self.assertEqual(len(talents), TAB_TALENT_COUNT)
        self.assertEqual(sum(len(t["rank_spell_ids"]) for t in talents), TAB_POINTS)
        self.assertEqual(check_tab_362(talents, [], GOOD_SLA, []), [])
        self.assertTrue(check_tab_362(talents[:-1], [], GOOD_SLA, []))                          # 33 talents
        clash = copy.deepcopy(talents)
        clash[1]["tier"], clash[1]["column"] = 0, 0                                               # two in (0,0)
        self.assertTrue(any("holds talents" in b for b in check_tab_362(clash, [], GOOD_SLA, [])))
        prereq = copy.deepcopy(talents)
        prereq[0]["depends_on"] = {"talent_id": 0, "rank": 4}
        self.assertTrue(check_tab_362(prereq, [], GOOD_SLA, []))
        raw = copy.deepcopy(talents)
        raw[0]["raw_overrides"] = {"PrereqTalent_1": 1321}
        self.assertTrue(check_tab_362(raw, [], GOOD_SLA, []))
        self.assertTrue(check_tab_362(talents, [{"ID": 1325, "TabID": TAB, "PrereqTalent_1": 1321}], GOOD_SLA, []))
        unflagged = [changed(t, flags=0) if t["id"] == 1312 else t for t in talents]
        self.assertTrue(check_tab_362(unflagged, [], GOOD_SLA, []))
        flagged = [changed(t, flags=1) if t["id"] == 1820 else t for t in talents]
        self.assertTrue(check_tab_362(flagged, [], GOOD_SLA, []))
        ranks = [changed(t, rank_spell_ids=[34497, 34498, 34499]) if t["id"] == 1811 else t for t in talents]
        self.assertTrue(check_tab_362(ranks, [], GOOD_SLA, []))                                    # 34499 kept
        bad_sla = [changed(e, skill_line=50) if e["id"] == 30547 else e for e in GOOD_SLA]
        self.assertTrue(check_tab_362(talents, [], bad_sla, []))                                   # wrong skill line
        self.assertTrue(check_tab_362(talents, [], GOOD_SLA[1:], []))                              # missing SLA
        self.assertTrue(check_tab_362(talents, [], [*GOOD_SLA, {"id": 30551, "spell_id": 202080, "skill_line": 51}],
                                      []))
        self.assertTrue(check_tab_362(talents, [], GOOD_SLA, [{"SpellId": MANTIS_STRIKE}]))      # trainer row
        moved = [changed(t, tier=10, column=1) if t["id"] == 2145 else t for t in talents]
        self.assertTrue(check_tab_362(moved, [], GOOD_SLA, []))

    def test_tab_363_guard(self):
        talents = good_mm_tab()
        self.assertEqual(check_tab_363_kept(talents, []), [])
        self.assertTrue(check_tab_363_kept(talents[1:], []))
        moved = [changed(t, tab_id=TAB) if t["id"] == SNIPER_TRAINING_ROW else t for t in talents]
        self.assertTrue(check_tab_363_kept(moved, []))
        self.assertTrue(check_tab_363_kept(talents, [{"ID": SNIPER_TRAINING_ROW, "TabID": TAB}]))

    def test_orphan_guards(self):
        good = [{"ID": 1820, "TabID": TAB, "SpellRank_1": 202080, "SpellRank_2": 202081}]
        self.assertEqual(check_orphans(good, ORPHANS), [])
        self.assertEqual(len(check_orphans([{"ID": 1820, "TabID": TAB, "SpellRank_3": 19500}], ORPHANS)), 1)
        self.assertEqual(len(check_orphans([{"ID": 1322, "TabID": TAB, "SpellRank_1": BLACK_ARROW}], ORPHANS)), 1)
        self.assertEqual(check_sniper_training_off_sv([{"ID": 2143, "TabID": MM_TAB, "SpellRank_1": 53302}]), [])
        self.assertEqual(len(check_sniper_training_off_sv([{"ID": 2143, "TabID": TAB, "SpellRank_1": 53302}])), 1)

    def test_talent_block_guard(self):
        sv = [{"ID": tid, "TabID": TAB, "TierID": cell[0], "ColumnIndex": cell[1]}
              for tid, (cell, _r) in sorted(TAB_LAYOUT.items(), key=lambda kv: kv[1][0])]
        bm = [{"ID": 1, "TabID": 361, "TierID": 0, "ColumnIndex": 0}]
        mm = [{"ID": 2, "TabID": MM_TAB, "TierID": 0, "ColumnIndex": 0}]
        self.assertEqual(check_talent_blocks(bm + sv + mm), [])
        self.assertTrue(check_talent_blocks(bm + sv[:5] + mm + sv[5:]))                          # split block
        self.assertTrue(check_talent_blocks(bm + sv[1:] + sv[:1] + mm))                          # wrong order
        # the real ordering function puts a minted row inside its tab's block
        base = [*bm, *(r for r in sv if r["ID"] < 60000), *mm]
        ordered = dbcfile.order_talent_rows([*bm, *mm, *sv], base)
        self.assertEqual(check_talent_blocks(ordered), [])

    def test_rank_uniqueness_guard(self):
        talents = good_tab()
        declared = set(TAB_RANKS) | set(NEW_RANK_IDS)
        names = {i: f"x_{i}" for i in declared}
        self.assertEqual(check_rank_rows_unique(talents, declared, names), [])
        twice = [*talents, {"id": 9999, "tab_id": 361, "rank_spell_ids": [202080]}]
        self.assertTrue(check_rank_rows_unique(twice, declared, names))
        orphan = [changed(t, rank_spell_ids=[202107]) if t["id"] == 2141 else t for t in talents]
        self.assertTrue(check_rank_rows_unique(orphan, declared, names))                         # 202108 in no row
        self.assertTrue(check_rank_rows_unique(talents, declared - {202091}, names))             # undeclared
        self.assertTrue(check_rank_rows_unique(talents, declared, {k: v for k, v in names.items() if k != 202100}))

    def test_castable_guard(self):
        rows = good_castable_rows()
        self.assertEqual(check_castables(rows, CAST_TIMES), [])
        for spell_id, cols in ((MANTIS_STRIKE, {"Attributes": 0x50002}), (WILDFIRE_BOMB, {"CastingTimeIndex": 18}),
                               (TAR_BOMB, {"EquippedItemClass": 2}), (CLUSTER_BOMBS, {"StartRecoveryCategory": 0}),
                               (MANTIS_STRIKE, {"StartRecoveryTime": 1000}), (TAR_BOMB, {"SpellClassMask_2": 0}),
                               (WILDFIRE_BOMB, {"SpellClassMask_2": 0x40 | 0x80000}),
                               (CLUSTER_BOMBS, {"Attributes": 0x10002}), (MANTIS_STRIKE, {"SpellLevel": 60}),
                               (TAR_BOMB, {"CastingTimeIndex": 4}), (MANTIS_STRIKE, {"CasterAuraSpell": 0}),
                               (TAR_BOMB, {"Category": 1250}), (CLUSTER_BOMBS, {"Targets": 0}),
                               (WILDFIRE_BOMB, {"FacingCasterFlags": 0}), (MANTIS_STRIKE, {"AttributesEx3": 0x10000})):
            bad = copy.deepcopy(rows)
            bad[spell_id].update(cols)
            self.assertTrue(check_castables(bad, CAST_TIMES), (spell_id, cols))
        self.assertTrue(check_castables({k: v for k, v in rows.items() if k != CLUSTER_BOMBS}, CAST_TIMES))
        levels = {i: {"ID": i, "SpellLevel": lv, "BaseLevel": lv, "MaxLevel": 0} for i, lv in POTENCY_LEVELS.items()}
        self.assertEqual(check_potency_levels(levels), [])
        levels[SHRAPNEL_HIT]["SpellLevel"] = 60
        self.assertEqual(len(check_potency_levels(levels)), 1)

    def test_explosive_shot_guard(self):
        row, entry, source = good_explosive()
        self.assertEqual(check_explosive_shot(row, entry, source, CAST_TIMES, DUR2000), [])
        for cols in ({"CastingTimeIndex": 1}, {"EquippedItemClass": -1}, {"AttributesEx5": 0x200},
                     {"SpellLevel": 60}, {"MaxLevel": 80}, {"EffectAura_2": 3}, {"Effect_1": 6},
                     {"Attributes": 0x50000}, {"DurationIndex": 1}, {"SpellClassMask_2": 0},
                     {"EffectBasePoints_2": 142}, {"AttributesEx3": 0x10000}, {"Category": 1250}):
            self.assertTrue(check_explosive_shot(changed(row, **cols), entry, source, CAST_TIMES, DUR2000), cols)
        bad = copy.deepcopy(entry)
        bad["effect2"] = {"_potency": {"kind": "periodic", "total_potency": 50.0}}
        self.assertTrue(check_explosive_shot(row, bad, source, CAST_TIMES, DUR2000))
        bad = copy.deepcopy(entry)
        bad["effect2"] = {"_potency_excluded": "timer"}
        self.assertTrue(check_explosive_shot(row, bad, source, CAST_TIMES, DUR2000))
        bad = copy.deepcopy(entry)
        bad["effect1"]["_potency"]["total_potency"] = 143.0
        self.assertTrue(check_explosive_shot(row, bad, source, CAST_TIMES, DUR2000))
        self.assertTrue(check_explosive_shot(row, entry, source + "'MaxLevel': 80,", CAST_TIMES, DUR2000))
        self.assertTrue(check_explosive_shot(row, entry, source + "'BaseLevel': 60,", CAST_TIMES, DUR2000))
        self.assertTrue(check_explosive_shot(row, entry, None, CAST_TIMES, DUR2000))
        self.assertTrue(check_explosive_shot(None, entry, source, CAST_TIMES, DUR2000))
        text = ("a = spell(\n    id=1,\n)\nexplosive_shot_53301 = spell(\n    id=53301,\n"
                "    raw_overrides={'X': 1},\n)\n")
        self.assertNotIn("id=1,", spell_call_source(text, EXPLOSIVE_SHOT))
        self.assertIn("'X': 1", spell_call_source(text, EXPLOSIVE_SHOT))

    def test_explosive_blast_guard(self):
        row, entry, bonus = good_blast()
        self.assertEqual(check_explosive_blast(row, entry, bonus), [])
        for cols in ({"SpellLevel": 0}, {"EquippedItemClass": 0}, {"EffectSpellClassMaskA_1": 0xC00017},
                     {"AttributesEx2": 0}, {"SpellClassMask_3": 0}, {"Effect_1": 3}):
            self.assertTrue(check_explosive_blast(changed(row, **cols), entry, bonus), cols)
        self.assertTrue(check_explosive_blast(row, entry, [{"entry": EXPLOSIVE_BLAST, "ap_bonus": 0.16}]))
        self.assertTrue(check_explosive_blast(row, entry, bonus + bonus))
        self.assertTrue(check_explosive_blast(row, entry, []))
        bad = copy.deepcopy(entry)
        bad["effect1"] = {}
        self.assertTrue(check_explosive_blast(row, bad, bonus))

    def test_splash_guard(self):
        rows, entries = good_splash_rows()
        self.assertEqual(check_splashes(rows, entries), [])
        for spell_id, cols in ((SPLASH, {"ImplicitTargetA_1": 53}), (BLAST_SPLASH, {"Targets": 0}),
                               (SPLASH, {"AttributesEx2": ATTR_EX2_CANT_CRIT | 0x4}),
                               (BLAST_SPLASH, {"AttributesEx3": 0x10000}), (SPLASH, {"AttributesEx2": 0}),
                               (BLAST_SPLASH, {"SpellClassMask_2": 0x80000000}), (SPLASH, {"EffectBasePoints_2": 49}),
                               (BLAST_SPLASH, {"EquippedItemClass": 0})):
            bad = copy.deepcopy(rows)
            bad[spell_id].update(cols)
            self.assertTrue(check_splashes(bad, entries), (spell_id, cols))
        bad = copy.deepcopy(entries)
        bad[BLAST_SPLASH]["effect1"] = {"_potency": {"kind": "direct", "total_potency": 50.0}}
        self.assertTrue(check_splashes(rows, bad))

    def test_line_of_sight_and_no_proc_guards(self):
        rows = {i: {"ID": i, "AttributesEx2": 0x4} for i in IGNORE_LOS_IDS}
        rows.update({SPLASH: {"ID": SPLASH}, EXPLOSIVE_BLAST: {"ID": EXPLOSIVE_BLAST, "AttributesEx2": 0x4}})
        self.assertEqual(check_ignore_los(rows), [])
        extra = copy.deepcopy(rows)
        extra[SPLASH]["AttributesEx2"] = 0x4                                                      # stale line 12: none
        self.assertTrue(check_ignore_los(extra))
        missing = copy.deepcopy(rows)
        missing[TARRED]["AttributesEx2"] = 0
        self.assertTrue(check_ignore_los(missing))
        lost = copy.deepcopy(rows)
        lost[EXPLOSIVE_BLAST]["AttributesEx2"] = 0
        self.assertTrue(check_ignore_los(lost))
        procs = {i: {"ID": i, "AttributesEx3": 0x10000} for i in NO_PROC_HELPERS}
        procs.update({i: {"ID": i} for i in PROC_RAISERS})
        self.assertEqual(check_no_proc_helpers(procs), [])
        bad = copy.deepcopy(procs)
        bad[SHRAPNEL_HIT]["AttributesEx3"] = 0
        self.assertTrue(check_no_proc_helpers(bad))
        bad = copy.deepcopy(procs)
        bad[EXPLOSIVE_SHOT]["AttributesEx3"] = 0x10000
        self.assertTrue(check_no_proc_helpers(bad))

    def test_visibility_guard(self):
        rows = {i: {"ID": i, "Attributes": 0} for i in VISIBLE}
        rows.update({i: {"ID": i, "Attributes": 464} for i in HIDDEN})
        rows[PONE_MARKER]["Attributes"] = ATTR_DO_NOT_DISPLAY
        self.assertEqual(check_visibility(rows, VISIBLE, HIDDEN, ()), [])
        bad = copy.deepcopy(rows)
        bad[TARRED]["Attributes"] = ATTR_DO_NOT_DISPLAY
        self.assertTrue(check_visibility(bad, VISIBLE, HIDDEN, ()))
        bad = copy.deepcopy(rows)
        bad[BURNING_TAR]["Attributes"] = 464
        self.assertTrue(check_visibility(bad, VISIBLE, HIDDEN, ()))
        bad = copy.deepcopy(rows)
        bad[PONE_MARKER]["Attributes"] = 0
        self.assertTrue(check_visibility(bad, VISIBLE, HIDDEN, ()))

    def test_equipped_item_class_guard(self):
        rows = {i: {"ID": i, "EquippedItemClass": -1} for i in (MANTIS_STRIKE, EXPLOSIVE_BLAST, 202080)}
        rows.update({i: {"ID": i, "EquippedItemClass": 2} for i in SV_CLASS_TWO})
        self.assertEqual(check_equipped_item_class(rows, (MANTIS_STRIKE, EXPLOSIVE_BLAST, 202080), SV_CLASS_TWO), [])
        bad = copy.deepcopy(rows)
        bad[EXPLOSIVE_BLAST] = {"ID": EXPLOSIVE_BLAST, "EquippedItemClass": 0}
        self.assertTrue(check_equipped_item_class(bad, (EXPLOSIVE_BLAST,), ()))
        bad[EXPLOSIVE_SHOT] = {"ID": EXPLOSIVE_SHOT, "EquippedItemClass": -1}
        self.assertTrue(check_equipped_item_class(bad, (), (EXPLOSIVE_SHOT,)))
        self.assertTrue(SV_CLASS_TWO.isdisjoint(_minus_one_ids()))
        self.assertIn(EXPLOSIVE_BLAST, _minus_one_ids())
        exempt = {56641, *SV_CLASS_TWO}
        self.assertEqual(check_exemption_sets(exempt, set(exempt)), [])
        self.assertTrue(check_exemption_sets(exempt - {BLACK_ARROW}, exempt))
        self.assertTrue(check_exemption_sets(exempt - {BLACK_ARROW}, exempt - {BLACK_ARROW}))

    def test_masks_module_guard(self):
        class Fake:
            pass
        fake = Fake()
        for name, value in SPEC_MASKS.items():
            setattr(fake, name, value)
        self.assertEqual(check_masks_module(fake), [])
        fake.THRILL_PROC = (0x61800, 0x80800000, 0x28000201)                                     # d2 b9 left in
        self.assertEqual(len(check_masks_module(fake)), 1)
        del fake.STRIKE_HITS
        self.assertEqual(len(check_masks_module(fake)), 2)

    def test_spellmod_guard(self):
        rows = good_spellmod_rows()
        self.assertEqual(check_spellmod_specs(rows, MASKS), [])
        self.assertEqual(check_spellmod_scoping(rows, rows), [])
        family_zero = copy.deepcopy(rows)
        family_zero[202081]["SpellClassSet"] = 0
        self.assertTrue(check_spellmod_specs(family_zero, MASKS))
        self.assertTrue(check_spellmod_scoping(family_zero, family_zero))
        wrong_letter = copy.deepcopy(rows)                                                     # mask on A, not B
        for n in (1, 2, 3):
            wrong_letter[202081][f"EffectSpellClassMaskA_{n}"] = wrong_letter[202081].pop(f"EffectSpellClassMaskB_{n}")
        self.assertTrue(check_spellmod_specs(wrong_letter, MASKS))
        zero = copy.deepcopy(rows)
        for n in (1, 2, 3):
            zero[56337][f"EffectSpellClassMaskB_{n}"] = 0
        self.assertTrue(check_spellmod_specs(zero, MASKS))
        self.assertTrue(check_spellmod_scoping(zero, zero))
        op = copy.deepcopy(rows)
        op[202062]["EffectMiscValue_2"] = int(OP.DAMAGE)
        self.assertTrue(check_spellmod_specs(op, MASKS))
        stale = copy.deepcopy(rows)
        stale[56333]["EffectSpellClassMaskB_2"] = 0x80000000                                    # the pre-S3 B_2
        self.assertTrue(check_spellmod_specs(stale, MASKS))
        self.assertTrue(check_spellmod_specs({k: v for k, v in rows.items() if k != 202091}, MASKS))
        removed = {i: {"ID": i} for ids, _e in REMOVED_EFFECTS for i in ids}
        self.assertEqual(check_removed_effects(removed), [])
        bad = copy.deepcopy(removed)
        bad[56337]["Effect_3"] = 6
        self.assertTrue(check_removed_effects(bad))
        bad = copy.deepcopy(removed)
        bad[53298]["EffectSpellClassMaskC_2"] = 0x4000000
        self.assertTrue(check_removed_effects(bad))

    def test_proc_row_guard(self):
        procs = good_procs()
        self.assertEqual(len(procs), 17)                                                          # 14 S3a + 3 S3b
        self.assertEqual(check_proc_rows(procs, MASKS), [])
        self.assertTrue(check_proc_rows(procs[1:], MASKS))                                       # a row missing
        self.assertTrue(check_proc_rows(procs + [procs[0]], MASKS))                               # declared twice
        self.assertTrue(check_proc_rows(procs + [{"SpellId": -34506}], MASKS))                    # negative twin
        self.assertTrue(check_proc_rows(procs + [{"SpellId": 34500}], MASKS))                     # positive twin
        self.assertTrue(check_proc_rows(procs + [{"SpellId": TARRED}], MASKS))                    # declared twice
        self.assertTrue(check_proc_rows(procs + [{"SpellId": -56342}], MASKS))
        self.assertTrue(check_proc_rows(procs + [{"SpellId": 56342}], MASKS))                     # positive twin
        self.assertTrue(check_proc_rows(procs + [{"SpellId": -TARRED}], MASKS))
        self.assertTrue(check_proc_rows(procs + [{"SpellId": -56453}], MASKS))
        for key in (TARRED, -56342, 56453):                                                       # an S3b row missing
            self.assertTrue(check_proc_rows([p for p in procs if p["SpellId"] != key], MASKS), key)
        for key, col, value in ((-34497, "SpellPhaseMask", PROC_PHASE_HIT), (-34497, "SpellFamilyMask2", 0x20000201),
                                (-53290, "AttributesMask", 0x2), (-53290, "DisableEffectsMask", 0),
                                (-53290, "ProcFlags", 0), (202084, "SpellPhaseMask", PROC_PHASE_CAST),
                                (19373, "SpellPhaseMask", PROC_PHASE_HIT), (202097, "HitMask", 0x3),
                                (-19184, "AttributesMask", 0), (34507, "HitMask", 0x2), (202105, "Chance", 30.0),
                                (34493, "DisableEffectsMask", 0x1), (-34500, "SpellFamilyName", 0),
                                # S3b: 202048 flags 0x20200, phase 0, Fire, attr 0x2
                                (TARRED, "ProcFlags", 0x200), (TARRED, "ProcFlags", 0x20000),
                                (TARRED, "SpellPhaseMask", PROC_PHASE_HIT), (TARRED, "SchoolMask", 0x20),
                                (TARRED, "SchoolMask", 0), (TARRED, "AttributesMask", 0),
                                (TARRED, "SpellFamilyName", SPELLFAMILY_HUNTER), (TARRED, "Chance", 0.0),
                                (TARRED, "SpellFamilyMask1", D1_TAR_BOMB),
                                # S3b: -56342 HIT | FINISH, attr 0x2, disable 0x4, cooldown 0, LOCK_AND_LOAD_PROC
                                (-56342, "SpellPhaseMask", PROC_PHASE_HIT),
                                (-56342, "SpellPhaseMask", PROC_PHASE_FINISH),
                                (-56342, "SpellPhaseMask", PROC_PHASE_CAST | PROC_PHASE_HIT_FINISH),
                                (-56342, "AttributesMask", 0), (-56342, "DisableEffectsMask", 0),
                                (-56342, "DisableEffectsMask", 0x6), (-56342, "Cooldown", 22000),
                                (-56342, "SpellFamilyMask0", 0), (-56342, "SpellFamilyMask2", 0),
                                (-56342, "SpellFamilyName", 0), (-56342, "Chance", 100.0),
                                (-56342, "ProcFlags", 0x240000),
                                # S3b: 56453 CAST row without the triggered-can-proc attribute
                                (56453, "AttributesMask", PROC_ATTR_TRIGGERED_CAN_PROC),
                                (56453, "SpellPhaseMask", PROC_PHASE_HIT), (56453, "SpellPhaseMask", 0),
                                (56453, "ProcFlags", 0x11100), (56453, "SpellFamilyMask0", 0),
                                (56453, "SpellFamilyMask1", 0), (56453, "Chance", 0.0),
                                (56453, "DisableEffectsMask", 0x4)):
            bad = [changed(p, **{col: value}) if p["SpellId"] == key else p for p in procs]
            self.assertTrue(check_proc_rows(bad, MASKS), (key, col, value))

    def test_proc_carrier_guard(self):
        rows = good_carrier_rows()
        self.assertEqual(check_proc_carriers(rows), [])
        for spell_id, cols in ((34497, {"ProcChance": 33}), (34498, {"ProcChance": 66}),
                               (34500, {"ProcTypeMask": 0x40140}), (53292, {"ProcTypeMask": 0x44540}),
                               (34506, {"EffectTriggerSpell_1": 34833}), (19373, {"ProcChance": 101}),
                               (202084, {"EffectTriggerSpell_2": 202063}), (202097, {"EffectMiscValue_3": 1}),
                               (34500, {"EffectAura_1": AURA_PROC_TRIGGER_SPELL}),
                               (202098, {"ProcTypeMask": 0x100}), (19287, {"ProcTypeMask": 0x4400}),
                               (19387, {"ProcTypeMask": 0x200000}),
                               (56342, {"ProcTypeMask": 0}), (56343, {"ProcChance": 50}),
                               (56344, {"EffectTriggerSpell_1": 0}), (56344, {"EffectAura_1": AURA_DUMMY})):
            bad = copy.deepcopy(rows)
            bad[spell_id].update(cols)
            self.assertTrue(check_proc_carriers(bad), (spell_id, cols))
        talents = [{"tab_id": TAB, "rank_spell_ids": [34500, 34502, 34503]},
                   {"tab_id": TAB, "rank_spell_ids": list(LOCK_AND_LOAD)},
                   {"tab_id": 361, "rank_spell_ids": [19559]}]
        m15_rows = {i: {"ID": i, "ProcTypeMask": 0x140, "Effect_1": 6} for i in (34500, 34502, 34503)}
        m15_rows.update({i: {"ID": i, "ProcTypeMask": LOCK_AND_LOAD_PROC_TYPE, "Effect_1": 6} for i in LOCK_AND_LOAD})
        m15_rows[19559] = {"ID": 19559, "ProcTypeMask": 0x100}
        both = [{"SpellId": -34500}, {"SpellId": -56342}]
        self.assertEqual(check_m15(m15_rows, talents, both), [])
        self.assertTrue(check_m15(m15_rows, talents, []))                                         # no row
        self.assertTrue(check_m15(m15_rows, talents, [{"SpellId": -34500}]))                      # no -56342 row (B4)
        self.assertEqual(check_m15(m15_rows, talents, [{"SpellId": -34500}], accepted=frozenset(LOCK_AND_LOAD)), [])
        self.assertEqual(M15_ACCEPTED, frozenset())                                               # nothing inert in S3b
        stale = copy.deepcopy(m15_rows)
        stale[34502]["EffectSpellClassMaskB_2"] = 1                                               # absent eff1
        self.assertTrue(check_m15(stale, talents, both))

    def test_thrill_guard(self):
        rows = good_thrill_rows()
        self.assertEqual(check_thrill(rows), [])
        for spell_id, cols in ((34497, {"ProcChance": 100}), (34498, {"ProcChance": 66}),
                               (34497, {"EffectBasePoints_2": 499}), (34498, {"Effect_2": 0}),
                               (34498, {"SpellClassMask_2": 0x80800000}), (34497, {"EffectSpellClassMaskA_1": 222}),
                               (34497, {"ProcTypeMask": 0x40100}), (34498, {"EffectTriggerSpell_1": 34720})):
            bad = copy.deepcopy(rows)
            bad[spell_id].update(cols)
            self.assertTrue(check_thrill(bad), (spell_id, cols))

    def test_family_bit_guard(self):
        rows = good_bit_rows()
        self.assertEqual(check_family_bit_carriers(rows), [])
        for sid, cols in ((COUNTERATTACK, {"SpellClassMask_2": D1_MANTIS_STRIKE}),          # 19306 not stripped
                          (BLACK_ARROW, {"SpellClassMask_2": D1_BURNING_TAR}),                  # 3674 not stripped
                          (34498, {"SpellClassMask_2": 0x80800000}),
                          (TARRED, {"SpellClassMask_2": D1_TAR_BOMB}),                          # a debuff with a bit
                          (202097, {"SpellClassMask_2": D1_EXPLOSIVE_SHOT}),                    # a rank with a bit
                          (CLUSTER_BOMBS_BLAST, {"SpellClassMask_3": 0}),
                          (WILDFIRE_BOMB, {"SpellClassMask_2": D1_WILDFIRE_BOMB | D1_TAR_BOMB})):
            bad = [changed(r, **cols) if r["ID"] == sid else r for r in rows]
            self.assertTrue(check_family_bit_carriers(bad), (sid, cols))
        stock = rows + [{"ID": 61385, "SpellClassSet": 9, "SpellClassMask_2": D1_TAR_BOMB}]    # a family-9 stock row
        self.assertTrue(check_family_bit_carriers(stock))
        npc = rows + [{"ID": 51753, "SpellClassSet": 0, "SpellClassMask_3": D2_CLUSTER_BOMBS}]  # family 0: not ours
        self.assertEqual(check_family_bit_carriers(npc), [])
        self.assertTrue(check_family_bit_carriers([r for r in rows if r["ID"] != BURNING_TAR]))

    def test_pet_bit_reader_guard(self):
        rows = {TNT_MASTERY: {"ID": TNT_MASTERY, "EffectSpellClassMaskA_2": 0x84000040}}
        self.assertEqual(check_no_pet_bit_readers(rows, {TNT_MASTERY}, []), [])
        rows[TNT_MASTERY]["EffectSpellClassMaskA_2"] |= D1_PET_BIT
        self.assertEqual(len(check_no_pet_bit_readers(rows, {TNT_MASTERY}, [])), 1)
        procs = [{"SpellId": -53290, "SpellFamilyMask1": D1_PET_BIT}]
        self.assertEqual(len(check_no_pet_bit_readers({}, {53290}, procs)), 1)

    def test_serpent_sting_and_stale_reader_guard(self):
        sting = {"ID": SERPENT_STING, "Effect_2": 6, "EffectAura_2": AURA_MOD_DAMAGE_FROM_CASTER,
                 "EffectBasePoints_2": -1, "EffectDieSides_2": 1}
        noxious = {"ID": 53295, "Effect_1": 6, "EffectAura_1": FLAT, "EffectMiscValue_1": OP_EFFECT2,
                   "EffectSpellClassMaskA_1": D0_SERPENT_STING}
        self.assertEqual(check_serpent_sting({SERPENT_STING: sting, 53295: noxious}, {53295}), [])
        self.assertTrue(check_serpent_sting({SERPENT_STING: sting, 53295: noxious}, set()))      # taught reader
        self.assertTrue(check_serpent_sting({SERPENT_STING: changed(sting, EffectBasePoints_2=5)}, set()))
        self.assertTrue(check_serpent_sting({}, set()))
        readers = {i: {"ID": i} for ids, _e in STALE_READERS for i in ids}
        self.assertEqual(check_stale_readers(readers), [])
        for sid, col in ((34455, "EffectSpellClassMaskB_2"), (53253, "EffectSpellClassMaskB_2"),
                         (53299, "EffectSpellClassMaskC_2"), (BLACK_ARROW, "EffectSpellClassMaskB_3"),
                         (34494, "EffectSpellClassMaskA_1"), (34837, "EffectSpellClassMaskB_1"),
                         (EXPLOSIVE_BLAST, "EffectSpellClassMaskA_1"), (34497, "EffectSpellClassMaskA_1"),
                         (INVIGORATION_D1_B27, "EffectSpellClassMaskA_2")):
            bad = copy.deepcopy(readers)
            bad[sid][col] = D1_BURNING_TAR if col.endswith("A_2") else 0x40
            self.assertTrue(check_stale_readers(bad), (sid, col))

    def test_group_and_link_guard(self):
        groups = [{"id": FAVORED_PREY_GROUP, "spell_id": i} for i in FAVORED_PREY_BUFFS]
        rules = [{"id": FAVORED_PREY_GROUP, "group_id": FAVORED_PREY_GROUP, "stack_rule": 1}]
        self.assertEqual(check_favored_prey_group(groups, rules), [])
        self.assertTrue(check_favored_prey_group(groups[:-1], rules))                             # 9 members
        self.assertTrue(check_favored_prey_group(groups + [{"id": FAVORED_PREY_GROUP, "spell_id": 202073}], rules))
        self.assertTrue(check_favored_prey_group(groups, [changed(rules[0], stack_rule=0)]))
        self.assertTrue(check_favored_prey_group(groups, []))
        self.assertTrue(check_favored_prey_group(groups + [{"id": 1243, "spell_id": 202063}], rules))
        linked = [{"spell_trigger": a, "spell_effect": b, "type": t} for a, b, t in LINKS]
        self.assertEqual(check_links(linked), [])
        self.assertTrue(check_links(linked[1:]))
        self.assertTrue(check_links(linked + [{"spell_trigger": 56336, "spell_effect": TNT_MASTERY, "type": 2}]))
        self.assertTrue(check_links([changed(r, type=0) if r["spell_trigger"] == 56337 else r for r in linked]))

    def test_binding_guard(self):
        bound, removals = good_bindings()
        self.assertEqual(check_bindings(bound, removals), [])
        self.assertEqual(len(S3B_UNBINDS), 2)
        for name in ("spell_hun_tarred", "spell_hun_burning_tar", "spell_hun_point_of_no_escape",
                     "spell_hun_frost_trap_aura_sv", "spell_hun_lock_and_load_rework", "spell_hun_explosive_trap_fire",
                     "spell_hun_explosive_trap_fire_tick", "spell_hun_freezing_trap_sv",
                     "spell_hun_wyvern_sting_rework", "spell_hun_deterrence_sv", "spell_hun_disengage_sv",
                     "spell_hun_feign_death_sv"):                                           # every S3b class positive
            self.assertIn(name, SCRIPT_BINDINGS)
            self.assertTrue(check_bindings([r for r in bound if r["ScriptName"] != name], removals), name)
            self.assertTrue(check_bindings(bound + [{"spell_id": 1, "ScriptName": name}], removals), name)
            self.assertTrue(check_bindings([changed(r, spell_id=-r["spell_id"]) if r["ScriptName"] == name else r
                                            for r in bound], removals), name)                   # negative key
        for key in S3B_UNBINDS:                                                                   # each S3b unbind
            self.assertTrue(check_bindings(bound, [r for r in removals
                                                   if (r["spell_id"], r["ScriptName"]) != key]), key)
        self.assertTrue(check_bindings(bound, [r for r in removals if r["spell_id"] != -56342]))
        self.assertTrue(check_bindings(bound, [r for r in removals if r["spell_id"] != -WYVERN_STING]))
        self.assertTrue(check_bindings(bound, removals + [{"spell_id": 781, "ScriptName": "spell_hun_disengage"}]))
        self.assertTrue(check_bindings(bound, removals + [{"spell_id": -56343,
                                                           "ScriptName": "spell_hun_lock_and_load"}]))
        neg = [changed(r, spell_id=-34500) if r["spell_id"] == 34500 else r for r in bound]
        self.assertTrue(check_bindings(neg, removals))                                           # negative key
        self.assertTrue(check_bindings([r for r in bound if r["spell_id"] != 34508], removals))
        self.assertTrue(check_bindings(bound + [{"spell_id": SPLASH, "ScriptName": "spell_hun_tarred"}], removals))
        self.assertTrue(check_bindings(bound, removals[:1]))                                      # an unbind missing
        self.assertTrue(check_bindings(bound, removals + [{"spell_id": -34497,
                                                           "ScriptName": "spell_hun_thrill_of_the_hunt"}]))
        self.assertTrue(check_bindings([r for r in bound if r["spell_id"] != RAPTOR_STRIKE], removals))
        self.assertTrue(check_bindings(bound + [{"spell_id": SPLASH, "ScriptName": "spell_hun_shrapnel"}], removals))

    def test_ruling_6_and_lock_and_load_guard(self):
        rows = good_ruling_rows()
        self.assertEqual(check_ruling_6(rows), [])
        for sid, cols in ((202081, {"EffectBasePoints_3": 4}), (202081, {"Effect_3": 0}),
                          (202081, {"EffectSpellClassMaskC_3": 0x10000}), (202080, {"Effect_3": 3}),
                          (202081, {"Description_Lang_enUS": "Increases ... by $s1%."}),
                          (RAPTOR_STRIKE, {"Description_Lang_enUS": "A quick strike that deals {pot1} Physical "
                                                                    "damage and restores ${$m2/10}.1% of your "
                                                                    "maximum mana."})):
            bad = copy.deepcopy(rows)
            bad[sid].update(cols)
            self.assertTrue(check_ruling_6(bad), (sid, cols))
        effect_dummy = copy.deepcopy(rows)                                                        # SPELL_EFFECT_DUMMY
        effect_dummy[202081].update(Effect_3=EFFECT_DUMMY, EffectAura_3=0)
        self.assertEqual(check_ruling_6(effect_dummy), [])

    def test_lock_and_load_guard(self):
        rows = good_lnl_rows()
        self.assertEqual(check_lock_and_load(rows, DUR5000), [])
        self.assertTrue(check_lock_and_load(rows, DUR2000))                                       # 67544 not 5000 ms
        self.assertTrue(check_lock_and_load({k: v for k, v in rows.items() if k != 67544}, DUR5000))
        for spell_id, cols in (
                (56342, {"ProcTypeMask": 0}), (56343, {"ProcTypeMask": 0x11100}), (56344, {"ProcChance": 0}),
                (56342, {"EffectTriggerSpell_1": 0}), (56343, {"EffectAura_1": AURA_DUMMY}),
                (56342, {"EffectBasePoints_1": 33}), (56343, {"EffectBasePoints_1": 64}),
                (56344, {"EffectBasePoints_1": 98}),
                (56342, {"EffectBasePoints_2": 1}), (56343, {"EffectBasePoints_2": 3}),     # the old 1 / 3 / 5
                (56344, {"EffectBasePoints_2": 5}), (56344, {"EffectAura_2": 0}),
                (56342, {"Effect_3": 0}), (56343, {"Effect_3": 0}),                    # eff2 gone: 0x4 would be invalid
                (56344, {"Effect_3": 0}), (56344, {"EffectAura_3": 0}), (56342, {"EffectAura_3": 0}),
                (56344, {"EffectBasePoints_3": 0}), (56344, {"EffectBasePoints_3": 2000}),
                (56342, {"EffectBasePoints_3": 21}), (56343, {"EffectBasePoints_3": 1999}),
                (56342, {"CastingTimeIndex": 0}), (56344, {"EquippedItemClass": 2}),
                (56343, {"EffectSpellClassMaskA_1": 0x800}), (56344, {"EffectSpellClassMaskB_3": 1}),
                (56453, {"ProcCharges": 2}), (56453, {"ProcCharges": 0}),
                (56453, {"Description_Lang_enUS": "Your next Arcane Shot or Explosive Shot triggers a $56342s3 sec "
                                                  "cooldown and costs no mana."}),
                (67544, {"DurationIndex": DUR2000}), (67544, {"EffectSpellClassMaskA_1": 64}),
                (67544, {"EffectSpellClassMaskB_2": 16777216})):
            bad = copy.deepcopy(rows)
            bad[spell_id].update(cols)
            self.assertTrue(check_lock_and_load(bad, DUR5000), (spell_id, cols))
        for spell_id in (*LOCK_AND_LOAD, LOCK_AND_LOAD_BUFF, LOCK_AND_LOAD_MARKER):
            self.assertTrue(check_lock_and_load({k: v for k, v in rows.items() if k != spell_id}, DUR5000), spell_id)

    def test_explosive_trap_effect_guard(self):
        row = good_trap_effect_row()
        self.assertEqual(check_explosive_trap_effect(row), [])
        self.assertTrue(check_explosive_trap_effect(None))
        for cols in ({"EffectAura_2": 3}, {"EffectAura_2": 0}, {"Effect_2": 6}, {"EffectBasePoints_2": 15},
                     {"EffectBasePoints_2": 0}, {"EffectAuraPeriod_2": 1000}, {"EffectAuraPeriod_2": 0},
                     {"Effect_1": 6}, {"EffectAura_1": 3}, {"Effect_1": 0}):
            self.assertTrue(check_explosive_trap_effect(changed(row, **cols)), cols)

    def test_trap_fire_tick_guard(self):
        row, entry = good_trap_fire_tick()
        self.assertEqual(check_trap_fire_tick(row, entry), [])
        self.assertTrue(check_trap_fire_tick(None, entry))
        self.assertTrue(check_trap_fire_tick(row, None))
        self.assertEqual(check_trap_fire_tick(changed(row, EffectDieSides_1=0), entry), [])        # 0 is also exact
        for cols in ({"EffectRealPointsPerLevel_1": 1.44}, {"EffectDieSides_1": 5}, {"Effect_1": 6},
                     {"AttributesEx3": ATTR_EX3_SUPPRESS_CASTER_PROCS},
                     {"AttributesEx3": ATTR_EX3_IGNORE_CASTER_MODIFIERS}, {"AttributesEx3": 0}):
            self.assertTrue(check_trap_fire_tick(changed(row, **cols), entry), cols)
        self.assertTrue(check_trap_fire_tick(row, {**entry, "effect1": {}}))                      # not excluded
        potent = {**entry, "effect1": {**entry["effect1"], "_potency": {"kind": "direct", "total_potency": 10.0}}}
        self.assertTrue(check_trap_fire_tick(row, potent))                                        # carries a potency

    def test_wyvern_sting_guard(self):
        row = good_wyvern_row()
        self.assertEqual(check_wyvern_sting(row, DUR2000), [])
        self.assertTrue(check_wyvern_sting(None, DUR2000))
        self.assertTrue(check_wyvern_sting(row, DUR5000))
        for cols in ({"EffectAura_1": 3}, {"EffectAura_1": 0}, {"Effect_1": 3}, {"EffectMiscValue_1": 1},
                     {"EffectMiscValue_1": 0}, {"EffectBasePoints_1": -11}, {"EffectBasePoints_1": -1},
                     {"DurationIndex": DUR5000}, {"AuraInterruptFlags": 4718594}, {"ProcTypeMask": 1048576},
                     {"Mechanic": 10}, {"EffectMechanic_1": 10}, {"EquippedItemClass": -1}, {"EquippedItemClass": 0}):
            self.assertTrue(check_wyvern_sting(changed(row, **cols), DUR2000), cols)

    def test_s3b_helper_cast_time_guard(self):
        rows = {i: {"ID": i, "CastingTimeIndex": 1} for i in NEW_HELPER_IDS}
        self.assertEqual(check_s3b_helper_cast_time(rows), [])
        for i in (TARRED, BURNING_TAR, TRAP_FIRE, WYVERN_SLEEP, SURVIVALIST_SPEED, PONE_MARKER):
            self.assertTrue(check_s3b_helper_cast_time({**rows, i: {"ID": i, "CastingTimeIndex": 0}}), i)
            self.assertTrue(check_s3b_helper_cast_time({**rows, i: {"ID": i, "CastingTimeIndex": 18}}), i)
            self.assertTrue(check_s3b_helper_cast_time({k: v for k, v in rows.items() if k != i}), i)

    def test_los_list_guard(self):
        rows = {i: {"ID": i, "AttributesEx2": 0} for i in SV_BLOCK}
        for i in IGNORE_LOS_IDS:
            rows[i]["AttributesEx2"] = ATTR_EX2_IGNORE_LINE_OF_SIGHT
        rows[EXPLOSIVE_BLAST] = {"ID": EXPLOSIVE_BLAST, "AttributesEx2": ATTR_EX2_IGNORE_LINE_OF_SIGHT}
        self.assertEqual(check_ignore_los(rows), [])
        for i in sorted(IGNORE_LOS_IDS):                                                          # one of the 7 missing
            self.assertTrue(check_ignore_los({**rows, i: {"ID": i, "AttributesEx2": 0}}), i)
        for i in (202058, 202060, 202054, 202055, 202052, 202051, 202045):                         # an 8th carrier
            self.assertTrue(check_ignore_los({**rows, i: {"ID": i, "AttributesEx2": ATTR_EX2_IGNORE_LINE_OF_SIGHT}}), i)

    def test_s2fix_guard(self):
        row, _entry, _source = good_explosive()
        fire = {"ID": 201940, "Effect_1": 6, "EffectAura_1": FLAT, "EffectMiscValue_1": 10, "EffectBasePoints_1": -3001,
                "EffectSpellClassMaskA_1": 0x20000}
        cobra = changed(fire, ID=201811)
        aimed = {"ID": 19434, "Attributes": 0x410012, "SpellClassSet": 9, "CastingTimeIndex": 16,
                 "AttributesEx4": 0x18000000, "SpellClassMask_1": 0x20000}
        rows = {EXPLOSIVE_SHOT: row, 19434: aimed, 201940: fire, 201811: cobra}
        self.assertEqual(check_s2fix_guards(rows, CAST_TIMES), [])
        self.assertTrue(check_s2fix_guards({**rows, EXPLOSIVE_SHOT: changed(row, CastingTimeIndex=1)},
                                           CAST_TIMES))                                           # hidden 0.5 s cast
        self.assertTrue(check_s2fix_guards({**rows, EXPLOSIVE_SHOT: changed(row, Attributes=0x50000)}, CAST_TIMES))
        self.assertTrue(check_s2fix_guards({k: v for k, v in rows.items() if k != 201811}, CAST_TIMES))


if __name__ == "__main__":
    unittest.main()
