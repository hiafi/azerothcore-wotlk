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

Every check is a pure function; the negative-fixture class feeds each one a good input (must pass) and a crafted bad
copy (must fail), so a check that silently passes everything is caught.

Run directly:

    apps/dbc-tools/.venv/bin/python3 -m pytest apps/dbc-tools/lib/test_hunter_mm_data.py -q
"""

from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import build, dbcfmt, state  # noqa: E402
from lib.test_hunter_pet_data import package_data  # noqa: E402

TOOL_ROOT = Path(__file__).resolve().parents[1]
MASKS_PY = TOOL_ROOT / "source" / "classes" / "hunter" / "_masks.py"

LETTERS = ("A", "B", "C")
SPELLFAMILY_HUNTER = 9

# effect / aura / SpellModOp ids (SpellEffects.h, SpellAuraDefines.h, SpellDefines.h)
EFFECT_SCHOOL_DAMAGE = 2
EFFECT_DUMMY = 3
EFFECT_APPLY_AURA = 6
EFFECT_WEAPON_PERCENT_DAMAGE = 31
EFFECT_SCRIPT_EFFECT = 77
EFFECT_NORMALIZED_WEAPON_DMG = 121
AURA_PERIODIC_DAMAGE = 3
AURA_DUMMY = 4
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
ATTR_EX3_SUPPRESS_CASTER_PROCS = 0x10000
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
S2B_IDS = (201934, 201935, 201936, 201937, 201950, 201952)        # declared by S2b, never by S2a
# stock non-rank rows S2a edits whose built row must be -1 (helpers / buffs / triggered; M4)
EDITED_STOCK_HELPERS = (CHIMERA_SERPENT, WILD_QUIVER_SHOT, RAPID_KILLING_BUFF_ID, *SNIPER_TRAINING_BUFFS, 42243)
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
    SNIPERS_MARK: (SCHOOL_PHYSICAL, 20000, 30, 3524),
    VIPERS_MARK: (SCHOOL_NATURE, 30000, 40, 1630),
    FALCONS_MARK: (SCHOOL_PHYSICAL, 45000, 50, 1530),
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
           EFFICIENCY_BUFF, PRECISE_SHOTS_BUFF, FALCONS_EDGE, RAPID_KILLING_BUFF_ID, *SNIPER_TRAINING_BUFFS)
HIDDEN = (AIMED_CRIT_HELPER, CHIMERA_CRIT_HELPER, MASTERY)
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
    ((53241, 53243, MFD_R3), 3, AURA_ADD_PCT_MODIFIER, OP_DAMAGE, (0, 0, D2_MARK_PRESS)),            # Marked for Death (eff2: SpellInfoCorrections.cpp:409 rewrites eff0 mask at load)
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
}
# M15: ranks whose non-zero DBC ProcTypeMask has no spell_proc row on purpose (A18: Barrage's interim default entry)
M15_ACCEPTED = frozenset({24691})

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
S2A_UNBINDS = {(CHIMERA_SHOT, "spell_hun_chimera_shot"), (-53234, "spell_hun_piercing_shots")}
FREE_ARCANE_SHOT_SCRIPTS = frozenset({"spell_hun_shot_mana", "spell_hun_arcane_shot_mm"})
MASTERY_LINK = (MFD_R3, MASTERY, 2)


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


def check_free_arcane_shot(row: dict | None, arcane: dict | None, bound: list[dict]) -> list[str]:
    """(e) A9 + stale line 3: 201933's eff1 equals 3044's built eff1 column by column (the mana restore of
    spell_hun_shot_mana reads it: a literal that drifts from 3044 is a finding), index 18, class -1, d0 b11 only,
    no cost / category / cooldown, SUPPRESS_CASTER_PROCS, the two scripts and not BM's Stomp class."""
    if row is None or arcane is None:
        return [f"{ARCANE_SHOT_FREE}/{ARCANE_SHOT}: not declared"]
    bad = []
    for col in EFFECT_COLUMNS:
        if float(row.get(f"{col}_2") or 0) != float(arcane.get(f"{col}_2") or 0):
            bad.append(f"eff1 {col} {row.get(f'{col}_2')} differs from Arcane Shot's {arcane.get(f'{col}_2')}")
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
    bad = []
    no_bit = {*range(201940, 201950), MASTERY, CONVERGENCE, *range(201960, 201983)}
    for row in rows:
        sid, mask = int(row["ID"]), spell_mask(row)
        if mask[2] & D2_MARK_PRESS and sid not in MARKS:
            bad.append(f"{sid}: carries d2 b27 (mark press) but is no mark")
        if mask[2] & D2_MARK_DOT and sid not in (VIPERS_BITE, VIPERS_VENOM):
            bad.append(f"{sid}: carries d2 b28 (mark DoT) but is not 201930 / 201931")
        if sid >= 200000 and mask[0] & D0_ARCANE_SHOT and sid != ARCANE_SHOT_FREE:
            bad.append(f"{sid}: custom id on d0 b11 (only 201933 reuses Arcane Shot's bit)")
        if sid >= 200000 and mask[0] & D0_AIMED_SHOT and sid not in (201934, 201935):
            bad.append(f"{sid}: custom id on d0 b17 (only S2b's ricochet / bounce reuse Aimed Shot's bit)")
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
                   expected=S2A_SCRIPT_BINDINGS, unbinds=S2A_UNBINDS) -> list[str]:
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
    if any(r["ScriptName"] == "spell_hun_readiness_rework" for r in bound):
        bad.append("spell_hun_readiness_rework bound (dropped by stale line 4)")
    have = {(int(r["spell_trigger"]), int(r["spell_effect"]), int(r["type"])) for r in linked}
    if MASTERY_LINK not in have:
        bad.append(f"linked_spell{MASTERY_LINK} not declared")
    return bad


# ---- real data -------------------------------------------------------------------------------------------------------

def _cast_times(reuse) -> dict[int, int]:
    rows = {**state.load_stock_rows(dbcfmt.SPELLCASTTIMES),
            **{r["ID"]: r for r in reuse.minted.get("spellcasttimes", [])}}
    return {int(i): int(r.get("Base") or 0) for i, r in rows.items()}


def _touched_ids() -> set[int]:
    return {*NEW_S2A_IDS, *TAB_RANKS, *EDITED_STOCK_HELPERS}


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

    def test_s2b_ids_not_declared_in_s2a(self):
        rows = package_data()["rows_by_id"]
        self.assertEqual(sorted(i for i in S2B_IDS if i in rows), [])

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
                                                data["package"].spell_script_names))

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
    arcane = {"ID": ARCANE_SHOT, "Effect_2": EFFECT_DUMMY, "EffectBasePoints_2": 199, "EffectDieSides_2": 1}
    free = {"ID": ARCANE_SHOT_FREE, "Effect_1": EFFECT_SCHOOL_DAMAGE, "Effect_2": EFFECT_DUMMY,
            "EffectBasePoints_2": 199, "EffectDieSides_2": 1, "CastingTimeIndex": 18, "EquippedItemClass": -1,
            "SpellClassSet": 9, "SpellClassMask_1": D0_ARCANE_SHOT, "SchoolMask": SCHOOL_ARCANE,
            "DefenseType": DEFENSE_RANGED, "AttributesEx3": ATTR_EX3_SUPPRESS_CASTER_PROCS}
    return free, arcane


GOOD_FREE_BOUND = [{"spell_id": ARCANE_SHOT_FREE, "ScriptName": n} for n in sorted(FREE_ARCANE_SHOT_SCRIPTS)]


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
    bound = [{"spell_id": i, "ScriptName": n} for n, ids in S2A_SCRIPT_BINDINGS.items() for i in ids]
    removals = [{"spell_id": k, "ScriptName": n} for k, n in S2A_UNBINDS]
    linked = [{"spell_trigger": MFD_R3, "spell_effect": MASTERY, "type": 2}]
    return bound, removals, linked


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
        self.assertEqual(len(check_mark(SNIPERS_MARK, changed(good, RecoveryTime=30000), CAST_TIMES, DUR15)), 1)
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
        self.assertEqual(check_free_arcane_shot(free, arcane, GOOD_FREE_BOUND), [])
        # the stale MM 5.10 literal (bp 4 = 0.5%) diverges from 3044's 199
        self.assertEqual(len(check_free_arcane_shot(changed(free, EffectBasePoints_2=4), arcane, GOOD_FREE_BOUND)), 1)
        # 3044 retuned while 201933 keeps a literal 199: must fail too
        self.assertEqual(len(check_free_arcane_shot(free, changed(arcane, EffectBasePoints_2=149), GOOD_FREE_BOUND)), 1)
        self.assertEqual(len(check_free_arcane_shot(changed(free, EffectDieSides_2=0), arcane, GOOD_FREE_BOUND)), 1)
        for key, value in (("CastingTimeIndex", 1), ("EquippedItemClass", 2), ("Category", 1173), ("ManaCostPct", 3),
                           ("RecoveryTime", 6000), ("SpellClassMask_1", D0_ARCANE_SHOT | D0_AIMED_SHOT),
                           ("AttributesEx3", 0)):
            self.assertEqual(len(check_free_arcane_shot(changed(free, **{key: value}), arcane, GOOD_FREE_BOUND)), 1,
                             key)
        bm = GOOD_FREE_BOUND + [{"spell_id": ARCANE_SHOT_FREE, "ScriptName": "spell_hun_arcane_shot_bm"}]
        self.assertEqual(len(check_free_arcane_shot(free, arcane, bm)), 1)
        self.assertEqual(len(check_free_arcane_shot(free, arcane, GOOD_FREE_BOUND[:1])), 1)

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
        procs = [{"SpellId": -53215}]
        self.assertEqual(check_m15(rows, talents, procs), [])
        self.assertEqual(len(check_m15(rows, talents, [])), 2)                                  # Wild Quiver unrowed
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
        self.assertEqual(len(check_bindings(bound, removals, [])), 1)
        rebind = removals + [{"spell_id": 23989, "ScriptName": "spell_hun_readiness"}]
        self.assertEqual(len(check_bindings(bound, rebind, linked)), 1)
        self.assertEqual(len(check_bindings([b for b in bound if b["spell_id"] != ARCANE_SHOT_FREE], removals,
                                            linked)), 1)


if __name__ == "__main__":
    unittest.main()
