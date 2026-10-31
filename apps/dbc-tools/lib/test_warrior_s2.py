"""
Warrior S2 (Arms) data gate (warrior-rework S2-HANDOFF WP-A row A4, S2-WP-BRIEF rulings R1-R21).

Loads the real warrior DSL package (source/classes/warrior/) through the S1 / W0b loaders and asserts on the BUILT rows
(stock base + DSL + raw_overrides via `build.build_spell_row`, the way generate.py pairs them) for the Arms delta: the
33-cell grid and the nine retired talents, every rank row's effects and SpellMod masks per dword, the carriers, the
zeroed proc fields, the 55 new spell ids (durations by index, decoded attributes, visible vs hidden helpers, custom
attrs), the script / spell_proc / spell_group bindings, the SpellDescriptionVariables rows, the talent tooltips against
docs/reworks/warrior-arms-rework.md and the capstones (four since 2026-10-30). Every check is a pure function over built rows / package
tables; the negative tests mutate a copy of the real rows and prove each check can fail.

Reading rule for the masks (S1-0VERIFY top): EffectSpellClassMask{A,B,C}_{1,2,3}: the LETTER is the effect index
(A = effect 0, B = effect 1, C = effect 2), the NUMBER is the dword (1 = d0, 2 = d1, 3 = d2). Effects in the
comments below are 0-based ("e0"); the DBC columns and the entry keys (`effect1`..`effect3`) are 1-based.

Not driven here: the generated GCD-haste aura 201560 (lib/gcd_haste computes it from the merged spell data; its d2 mask
becomes 0xA once Colossus Smash 204490 (d2 0xA) is on the GCD, R19). 204490's mask and GCD are pinned below and
`generate.py --check --class warrior` owns the generated row.

Run: cd /home/plex/wow_server/azerothcore-wotlk && PYTHONDONTWRITEBYTECODE=1 apps/dbc-tools/.venv/bin/python3 \
     -m pytest apps/dbc-tools/lib/test_warrior_s2.py -q -p no:cacheprovider
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import test_capstone_format as capfmt  # noqa: E402
from lib import test_warrior_s1 as s1  # noqa: E402
from lib.test_warrior_s1 import (  # noqa: E402
    _aura_effect, _data, _effect_empty, _emask, _hex3, _i, _missing, _mut, _u32,
)

# effect types / auras
EFF_APPLY_AURA = 6
AURA_DUMMY, AURA_PERIODIC_TRIGGER = 4, 23
AURA_PERIODIC_ENERGIZE, AURA_PROC_TRIGGER, AURA_MOD_SCALE = 24, 42, 61
AURA_CRIT_PCT_WEAPON, AURA_DMG_DONE_PCT, AURA_SPELLMOD_FLAT, AURA_SPELLMOD_PCT = 52, 79, 107, 108
AURA_MOD_STAT_PCT, AURA_MELEE_HASTE, AURA_CRIT_DAMAGE_BONUS, AURA_ARMOR_PEN = 137, 138, 163, 280
AURA_MOD_RAGE_FROM_DAMAGE, AURA_MOD_MAX_POWER, AURA_DMG_TAKEN_PCT = 213, 35, 87
AURA_CUSTOM_STAT_PCT, AURA_PERIODIC_DUMMY = 306, 226
AURA_APPLY_DAMAGE_AURA_FORBIDDEN = 271   # MOD_DAMAGE_PERCENT_TAKEN_FROM_CASTER-style aura the core already reads
EFF_SCHOOL_DAMAGE, EFF_HEAL, EFF_WEAPON_PERCENT, EFF_TRIGGER_SPELL = 2, 10, 31, 64
# spellmod ops (EffectMiscValue of aura 107 / 108; R21)
OP_DAMAGE, OP_DURATION, OP_EFFECT1, OP_RANGE, OP_RADIUS, OP_CRIT, OP_COOLDOWN = 0, 1, 3, 5, 6, 7, 11
OP_COST, OP_CRIT_DAMAGE_BONUS, OP_DOT = 14, 15, 22
CR_MASTERY_BIT = 1 << 20

ATTR0_PASSIVE, ATTR0_DO_NOT_DISPLAY = 0x40, 0x80
ATTR0_NOT_SHAPESHIFTED = 0x10000
ATTR2_CANT_CRIT = 0x20000000
ATTR2_IGNORE_LINE_OF_SIGHT = 0x4   # fix pass m2: the Deep Wounds tick must not die behind a corner
ATTR3_ONE_INSTANCE_PER_CASTER = 0x80
CU_IGNORE_ARMOR = 0x8000
Z = (0, 0, 0)

# ---- the grid ------------------------------------------------------------------------------------------------------
ARMS_TAB, HOLDING_TAB = 161, 60800

# docs/reworks/warrior-arms-rework.md section 4: talent id -> ((tier, column), rank spells)
GRID = {
    124: ((0, 0), (12282, 12663, 12664)),          # Heavy Blows
    60450: ((0, 1), (204521, 204522, 204523)),     # Martial Prowess (minted)
    127: ((0, 2), (12286, 12658, 204540)),         # Improved Rend (+1 rank)
    126: ((1, 0), (12285, 12697)),                 # Improved Charge
    60451: ((1, 1), (204524, 204525)),             # Two-Handed Weapon Mastery (minted)
    60452: ((1, 2), (204526, 204527, 204528)),     # Lingering Wounds (minted)
    137: ((2, 0), (12296, 204541, 204542)),        # Anger Management (moved, +2 ranks)
    135: ((2, 1), (12294,)),                       # Mortal Strike (moved)
    662: ((2, 2), (16493, 16494)),                 # Impale
    121: ((2, 3), (12834, 12849, 12867)),          # Deep Wounds
    131: ((3, 0), (12290, 12963)),                 # Improved Overpower (moved)
    136: ((3, 1), (12163, 12711, 12712)),          # Two-Handed Weapon Specialization
    2232: ((3, 2), (56636, 56637, 56638)),         # Taste for Blood
    133: ((4, 1), (204493,)),                      # Sweeping Strikes (new rank spell)
    60453: ((4, 2), (204529, 204530)),             # Improved Sweeping Strikes (minted)
    123: ((4, 3), (12281, 12812, 12813)),          # Weapon Specialization
    60454: ((5, 0), (204531, 204532)),             # Exploiter (minted)
    60455: ((5, 1), (204533, 204534)),             # Battlelord (minted)
    1859: ((5, 3), (46854, 46855)),                # Trauma
    1663: ((6, 0), (29834, 29838)),                # Second Wind
    60456: ((6, 1), (204490,)),                    # Colossus Smash (minted)
    1862: ((6, 2), (46865, 46866)),                # Strength of Arms
    60457: ((6, 3), (204535, 204536)),             # Momentum (minted)
    2283: ((7, 0), (64976, 204543)),               # Juggernaut (+1 rank)
    1824: ((7, 1), (35446, 35448)),                # Improved Mortal Strike (35449 dropped)
    60458: ((7, 2), (204537,)),                    # Weight of the Earth (minted)
    60459: ((7, 3), (204538, 204539)),             # Seismic Reverberation (minted)
    1662: ((8, 0), (29723, 29725, 29724)),         # Sudden Death
    1863: ((8, 1), (46924,)),                      # Bladestorm (moved)
    1664: ((8, 2), (29836, 29859)),                # Blood Frenzy
    1661: ((8, 3), (29623, 204544)),               # Endless Rage (moved, +1 rank)
    2231: ((9, 1), (46867, 56611, 56612)),         # Wrecking Crew (5 -> 3 ranks)
    60460: ((10, 1), (204492,)),                   # Avatar (minted)
}
MINTED = tuple(range(60450, 60461))
RETIRED = (125, 128, 129, 130, 132, 134, 641, 1860, 2233)
FLAGGED = {135, 133, 1863, 60456, 60460}          # the castables keep Flags 1; everything else 0
GRID_POINTS = 71
GRID_ROW_POINTS = (9, 7, 9, 8, 6, 6, 7, 7, 8, 3, 1)   # doc section 4, tiers 0..10

# ---- ids -----------------------------------------------------------------------------------------------------------
CS_BUTTON, CS_DEBUFF, AVATAR, SWEEPING, SWEEPING_COPY, WHIRL = 204490, 204491, 204492, 204493, 204494, 204495
DW_HOLDER, DW_TICK, MOMENTUM_BUFF, JUGGERNAUT_BUFF, JUGGERNAUT_CRIT = 204496, 204497, 204498, 204499, 204500
SOA_BUFFS, ENDLESS_RAGE_BUFF, EXPLOITER_DEBUFF = (204501, 204502), 204503, 204504
WRECKING_BUFFS = (204505, 204506, 204507)
ANGER_CAPSTONE, SEISMIC_ECHO, SECOND_WIND_HEAL, SWORD_STRIKE = 204508, 204509, 204510, 204511
WEAPON_SPEC_AXE, WEAPON_SPEC_MACE, WEAPON_SPEC_SWORD = (204512, 204515, 204518), (204513, 204516, 204519), \
    (204514, 204517, 204520)
BLADESTORM, MORTAL_STRIKE, REND, HEROIC_LEAP_LANDING = 46924, 12294, 772, 204401
SUDDEN_DEATH = (29723, 29725, 29724)
S2_FIRST, S2_LAST = 204490, 204544
S2_IDS = tuple(range(S2_FIRST, S2_LAST + 1))
S2_RESERVED_UNUSED = 204545       # R9: the wide landing variant is NOT created

IMPALE = (16493, 16494)
IMPROVED_MS = (35446, 35448)

# ---- the rank rows: (effect index, aura, misc, base points per rank (None = the effect is empty), mask) ------------
# SPECS[name] = (rank ids, effects, columns pinned on every rank, columns pinned per rank)
PASSIVE_ROW = {"SpellClassSet": 4}
GATE_2H = {"EquippedItemClass": 2, "EquippedItemSubclass": 354}      # the stock THWS gate (0x162)
NO_PROC = {"ProcTypeMask": 0, "ProcChance": 0}
SPECS: dict[str, tuple] = {
    "Heavy Blows": ((12282, 12663, 12664),
                    [(0, AURA_SPELLMOD_PCT, OP_DAMAGE, (4, 9, 14), (0x200040, 0, 0))], {}, {}),
    "Martial Prowess": ((204521, 204522, 204523),
                        [(0, AURA_CUSTOM_STAT_PCT, CR_MASTERY_BIT, (0, 1, 2), Z)], PASSIVE_ROW, {}),
    "Improved Rend": ((12286, 12658, 204540),
                      [(0, AURA_SPELLMOD_PCT, OP_DOT, (9, 19, 29), (0x20, 0, 0)),
                       (1, AURA_SPELLMOD_FLAT, OP_CRIT, (2, 5, 9), (0x20, 0, 0))], PASSIVE_ROW, {}),
    "Improved Charge": ((12285, 12697),
                        [(0, AURA_SPELLMOD_FLAT, 8, (49, 99), (0x1, 0, 0)),
                         (1, AURA_SPELLMOD_FLAT, OP_DURATION, (499, 999), (0x1000000, 0, 0)),
                         (2, AURA_SPELLMOD_FLAT, OP_RANGE, (None, 4), (0x1, 0, 0))], PASSIVE_ROW, {}),
    "Two-Handed Weapon Mastery": ((204524, 204525),
                                  [(0, AURA_MOD_RAGE_FROM_DAMAGE, 0, (14, 29), Z),
                                   (1, AURA_DMG_DONE_PCT, 1, (2, 5), Z),
                                   (2, AURA_SPELLMOD_FLAT, OP_DURATION, (999, 1999), (0, 0, 0x2))],
                                  {**PASSIVE_ROW, **GATE_2H}, {}),
    "Lingering Wounds": ((204526, 204527, 204528),
                         [(0, AURA_SPELLMOD_FLAT, OP_DURATION, (1999, 3999, 5999), (0x20, 0, 0))], PASSIVE_ROW, {}),
    "Anger Management": ((12296, 204541, 204542),
                         [(0, AURA_PERIODIC_ENERGIZE, 1, (19, 39, 59), Z),
                          (1, AURA_SPELLMOD_FLAT, 8, (49, 99, 149), (0x1, 0, 0)),
                          (2, AURA_DUMMY, 0, (0, 0, 0), Z)], {**PASSIVE_ROW, "EffectAuraPeriod_1": 3000}, {}),
    "Impale": (IMPALE, [(0, AURA_SPELLMOD_PCT, OP_CRIT_DAMAGE_BONUS, (9, 19), (0x26604CEE, 0xC745, 0xF))],
               PASSIVE_ROW, {}),
    "Deep Wounds": ((12834, 12849, 12867),
                    [(0, AURA_PROC_TRIGGER, 0, (0, 0, 0), Z), (1, AURA_DUMMY, 0, (10, 21, 32), Z)], PASSIVE_ROW,
                    {"EffectTriggerSpell_1": (12162, 12850, 12868)}),
    "Improved Overpower": ((12290, 12963), [(0, AURA_SPELLMOD_FLAT, OP_CRIT, (19, 39), (0x4, 0, 0))],
                           PASSIVE_ROW, {}),
    "Two-Handed Weapon Specialization": ((12163, 12711, 12712),
                                         [(0, AURA_DMG_DONE_PCT, 1, (0, 1, 2), Z),
                                          (1, AURA_CRIT_PCT_WEAPON, 0, (0, 1, 2), Z)], GATE_2H, {}),
    "Taste for Blood": ((56636, 56637, 56638), [(0, AURA_PROC_TRIGGER, 11, (-1, -1, -1), Z)],
                        {**PASSIVE_ROW, "EffectTriggerSpell_1": 204403, "ProcTypeMask": 262144},
                        {"ProcChance": (10, 20, 30)}),
    "Improved Sweeping Strikes": ((204529, 204530),
                                  [(0, AURA_SPELLMOD_FLAT, OP_DURATION, (1999, 3999), (0, 0x100000, 0)),
                                   (1, AURA_DUMMY, 0, (44, 49), Z)], PASSIVE_ROW, {}),
    "Weapon Specialization": ((12281, 12812, 12813), [(0, AURA_DUMMY, 0, (0, 0, 0), Z)],
                              {**NO_PROC, "EquippedItemClass": -1, "EquippedItemSubclass": 0}, {}),
    "Exploiter": ((204531, 204532), [(0, AURA_DUMMY, 0, (14, 29), Z)], {**PASSIVE_ROW, **NO_PROC}, {}),
    "Battlelord": ((204533, 204534), [(0, AURA_SPELLMOD_PCT, OP_DAMAGE, (9, 19), (0x4, 0, 0))], PASSIVE_ROW, {}),
    "Trauma": ((46854, 46855), [(0, AURA_DUMMY, 0, (14, 29), Z)], NO_PROC, {}),
    "Second Wind": ((29834, 29838), [(0, AURA_DUMMY, 0, (1, 3), Z)], NO_PROC, {}),
    "Strength of Arms": ((46865, 46866),
                         [(0, AURA_MOD_STAT_PCT, 0, (1, 3), Z), (1, AURA_MOD_STAT_PCT, 2, (0, 1), Z),
                          (2, AURA_PROC_TRIGGER, 0, (0, 0), Z)], {"ProcTypeMask": 16, "ProcChance": 100},
                         {"EffectTriggerSpell_3": (204501, 204502)}),
    "Momentum": ((204535, 204536), [(0, AURA_PROC_TRIGGER, 0, (0, 0), Z)],
                 {**PASSIVE_ROW, "ProcTypeMask": 16, "EffectTriggerSpell_1": 204498},
                 {"ProcChance": (15, 30)}),
    "Juggernaut": ((64976, 204543),
                   [(0, None, None, (None, None), None), (1, AURA_DUMMY, 0, (49, 99), Z),
                    (2, AURA_SPELLMOD_FLAT, OP_COOLDOWN, (-2001, -4001), (0, 0, 0x1))], {**PASSIVE_ROW, **NO_PROC}, {}),
    "Improved Mortal Strike": (IMPROVED_MS, [(0, AURA_SPELLMOD_PCT, OP_DAMAGE, (4, 9), (0x2000000, 0, 0)),
                                             (1, AURA_SPELLMOD_FLAT, OP_EFFECT1, (-6, -11), (0x2000000, 0, 0))],
                               PASSIVE_ROW, {}),
    "Weight of the Earth": ((204537,), [(0, AURA_SPELLMOD_FLAT, OP_RADIUS, (7,), (0, 0, 0x1)),
                                        (1, AURA_DUMMY, 0, (0,), Z)], PASSIVE_ROW, {}),
    "Seismic Reverberation": ((204538, 204539), [(0, AURA_DUMMY, 0, (24, 49), Z)], PASSIVE_ROW, {}),
    "Blood Frenzy": ((29836, 29859), [(0, None, None, (None, None), None),
                                      (1, AURA_MELEE_HASTE, 0, (1, 3), Z)], {}, {}),
    "Endless Rage": ((29623, 204544), [(0, AURA_MOD_MAX_POWER, 1, (99, 199), Z),
                                       (1, AURA_DUMMY, 0, (None, 0), Z)], PASSIVE_ROW, {}),
    "Wrecking Crew": ((46867, 56611, 56612), [(0, AURA_PROC_TRIGGER, 0, (-1, -1, -1), Z)],
                      {"ProcTypeMask": 20, "ProcChance": 100},
                      {"EffectTriggerSpell_1": (204505, 204506, 204507)}),
    "Weapon Specialization (axe, polearm)": (WEAPON_SPEC_AXE,
                                             [(0, AURA_CRIT_PCT_WEAPON, 0, (1, 3, 5), Z),
                                              (1, AURA_CRIT_DAMAGE_BONUS, 1, (1, 3, 5), Z)],
                                             {**PASSIVE_ROW, "Attributes": 0xC0}, {}),
    "Weapon Specialization (mace)": (WEAPON_SPEC_MACE, [(0, AURA_ARMOR_PEN, 0, (4, 9, 14), Z)],
                                     {**PASSIVE_ROW, "Attributes": 0xC0}, {}),
    "Weapon Specialization (sword)": (WEAPON_SPEC_SWORD, [(0, AURA_PROC_TRIGGER, 0, (0, 0, 0), Z)],
                                      {**PASSIVE_ROW, "Attributes": 0xC0, "ProcTypeMask": 20,
                                       "EffectTriggerSpell_1": SWORD_STRIKE}, {"ProcChance": (3, 6, 10)}),
}

# the SpellMod rank rows (ranks that must never carry an empty mask on a 107 / 108 effect)
S2_SPELLMOD_RANK_IDS = tuple(sid for name, spec in SPECS.items() for sid in spec[0])

# Sudden Death keeps the stock lookup shape (Execute's rage-kept clause reads effect index 1)
SUDDEN_DEATH_E0_BP, SUDDEN_DEATH_E1_BP, SUDDEN_DEATH_CHANCE = (4, 9, 14), (2, 6, 9), (5, 10, 15)

# ---- the new ids: exact column pins ------------------------------------------------------------------------------
# durations by index (R21)
DUR = {"4s": 35, "6s": 32, "8s": 31, "10s": 1, "12s": 29, "14s": 305, "15s": 8, "20s": 18, "21s": 86, "30s": 9,
       "inf": 21}
DUR_MS = {35: 4000, 32: 6000, 31: 8000, 1: 10000, 29: 12000, 305: 14000, 8: 15000, 18: 20000, 86: 21000, 9: 30000,
          21: -1}
WRECKING_MASK = {"EffectSpellClassMaskA_1": 0x22000084, "EffectSpellClassMaskA_2": 0x4000,
                 "EffectSpellClassMaskA_3": 0x3, "EffectSpellClassMaskB_1": 0x20, "EffectSpellClassMaskB_2": 0,
                 "EffectSpellClassMaskB_3": 0}


def _wrecking(bp: int) -> dict:
    return {"Name_Lang_enUS": "Wrecking Crew", "SpellClassSet": 4, "DurationIndex": DUR["12s"],
            "EquippedItemClass": -1, "Attributes": 0, "Effect_1": EFF_APPLY_AURA, "EffectAura_1": AURA_SPELLMOD_PCT,
            "EffectMiscValue_1": OP_DAMAGE, "EffectBasePoints_1": bp, "Effect_2": EFF_APPLY_AURA,
            "EffectAura_2": AURA_SPELLMOD_PCT, "EffectMiscValue_2": OP_DOT, "EffectBasePoints_2": bp, **WRECKING_MASK}


NEW_ROW_PINS: dict[int, dict] = {
    # D3 Colossus Smash: the castable (GCD, melee, 20 s via RecoveryTime, d2 0xA = b1 identity + b3 group) ...
    CS_BUTTON: {"Name_Lang_enUS": "Colossus Smash", "Attributes": 0x50010, "AttributesEx": 0x8000200,
                "AttributesEx3": 0x400, "SpellClassSet": 4, "SpellClassMask_1": 0, "SpellClassMask_2": 0,
                "SpellClassMask_3": 0xA, "DurationIndex": DUR["inf"], "RangeIndex": 2, "EquippedItemClass": 2,
                "EquippedItemSubclass": 173555, "SpellLevel": 40, "BaseLevel": 40, "RecoveryTime": 20000,
                "Category": 0, "CategoryRecoveryTime": 0, "ManaCost": 200, "StartRecoveryCategory": 133,
                "StartRecoveryTime": 1500, "DefenseType": 2, "Effect_1": EFF_WEAPON_PERCENT,
                "EffectBasePoints_1": 419, "Effect_2": EFF_TRIGGER_SPELL, "EffectTriggerSpell_2": CS_DEBUFF},
    # ... and its debuff: a visible DUMMY (never aura 271), per caster, d2 0x2
    CS_DEBUFF: {"Name_Lang_enUS": "Colossus Smash", "Attributes": 0, "AttributesEx3": ATTR3_ONE_INSTANCE_PER_CASTER,
                "SpellClassSet": 4, "SpellClassMask_3": 0x2, "DurationIndex": DUR["6s"], "EquippedItemClass": -1,
                "Effect_1": EFF_APPLY_AURA, "EffectAura_1": AURA_DUMMY, "EffectBasePoints_1": 0,
                "Effect_2": 0, "Effect_3": 0, "ImplicitTargetA_1": 6},
    # D7 Avatar: off the GCD, no cost, 90 s, 20 s, aura 61 (+30%), level 60, no family bit
    AVATAR: {"Name_Lang_enUS": "Avatar", "Attributes": 0x10, "SpellClassSet": 4, "SpellClassMask_1": 0,
             "SpellClassMask_2": 0, "SpellClassMask_3": 0, "DurationIndex": DUR["20s"], "SpellLevel": 60,
             "BaseLevel": 60, "RecoveryTime": 90000, "ManaCost": 0, "StartRecoveryCategory": 0,
             "StartRecoveryTime": 0, "Effect_1": EFF_APPLY_AURA, "EffectAura_1": AURA_MOD_SCALE,
             "EffectBasePoints_1": 29},
    # D4 Sweeping Strikes: off the GCD, 30 rage, 30 s, 10 s, NO NOT_SHAPESHIFTED (0x10000), visible self DUMMY
    SWEEPING: {"Name_Lang_enUS": "Sweeping Strikes", "Attributes": 0x40010, "SpellClassSet": 4,
               "SpellClassMask_2": 0x100000, "DurationIndex": DUR["10s"], "SpellLevel": 30, "BaseLevel": 30,
               "RecoveryTime": 30000, "Category": 0, "ManaCost": 300, "StartRecoveryCategory": 0,
               "StartRecoveryTime": 0, "ProcTypeMask": 0, "ProcCharges": 0, "Effect_1": EFF_APPLY_AURA,
               "EffectAura_1": AURA_DUMMY, "EffectBasePoints_1": 0},
    # the copy: a school-damage helper that can crit (no CANT_CRIT), melee DmgClass
    SWEEPING_COPY: {"Name_Lang_enUS": "Sweeping Strikes", "Attributes": 0, "AttributesEx2": 0,
                    "AttributesEx3": 0x20050000, "AttributesEx4": 0x800000, "SpellClassSet": 4,
                    "DefenseType": 2, "RangeIndex": 13, "Effect_1": EFF_SCHOOL_DAMAGE},
    # D10 the whirl: 170% weapon (balance 2026-10-30 +70%), MaxTargets 5, d1 0x4000 only, melee DmgClass, level 50
    WHIRL: {"Name_Lang_enUS": "Bladestorm", "Attributes": 0x50010, "AttributesEx3": 0x10000,
            "SpellClassSet": 4, "SpellClassMask_1": 0, "SpellClassMask_2": 0x4000, "SpellClassMask_3": 0,
            "MaxTargets": 5, "DefenseType": 2, "SpellLevel": 50, "BaseLevel": 50, "Effect_1": EFF_WEAPON_PERCENT,
            "EffectBasePoints_1": 169, "ImplicitTargetA_1": 22, "ImplicitTargetB_1": 15, "EffectRadiusIndex_1": 14},
    # D5 Deep Wounds holder (visible, 6 s, periodic dummy every 1000 ms, d1 0x10) and the hidden tick (no crit)
    DW_HOLDER: {"Name_Lang_enUS": "Deep Wounds", "Attributes": 0, "SpellClassSet": 4, "SpellClassMask_2": 0x10,
                "DurationIndex": DUR["6s"], "Effect_1": EFF_APPLY_AURA, "EffectAura_1": AURA_PERIODIC_DUMMY,
                "EffectAuraPeriod_1": 1000},
    DW_TICK: {"Name_Lang_enUS": "Deep Wounds", "Attributes": 0x80,
              "AttributesEx2": ATTR2_CANT_CRIT | ATTR2_IGNORE_LINE_OF_SIGHT,
              "AttributesEx3": 0x20050000, "SpellClassSet": 4, "DefenseType": 0, "Effect_1": EFF_SCHOOL_DAMAGE},
    # D24 Momentum: next Slam free (-100% cost) and +30% damage, 15 s, one charge, visible
    MOMENTUM_BUFF: {"Name_Lang_enUS": "Momentum", "Attributes": 0, "DurationIndex": DUR["15s"], "ProcCharges": 1,
                    "Effect_1": EFF_APPLY_AURA, "EffectAura_1": AURA_SPELLMOD_PCT, "EffectMiscValue_1": OP_COST,
                    "EffectBasePoints_1": -101, "EffectSpellClassMaskA_1": 0x200000, "Effect_2": EFF_APPLY_AURA,
                    "EffectAura_2": AURA_SPELLMOD_PCT, "EffectMiscValue_2": OP_DAMAGE, "EffectBasePoints_2": 29,
                    "EffectSpellClassMaskB_1": 0x200000},
    # D13 Juggernaut: the visible marker and the hidden +100 crit on Slam d0 0x200000, one charge
    JUGGERNAUT_BUFF: {"Name_Lang_enUS": "Juggernaut", "Attributes": 0, "DurationIndex": DUR["20s"],
                      "Effect_1": EFF_APPLY_AURA, "EffectAura_1": AURA_DUMMY},
    JUGGERNAUT_CRIT: {"Name_Lang_enUS": "Juggernaut", "Attributes": 0x80, "DurationIndex": DUR["20s"],
                      "ProcCharges": 1, "Effect_1": EFF_APPLY_AURA, "EffectAura_1": AURA_SPELLMOD_FLAT,
                      "EffectMiscValue_1": OP_CRIT, "EffectBasePoints_1": 99, "EffectSpellClassMaskA_1": 0x200000},
    # D14 Strength of Arms: +5 / +10% Mortal Strike damage per stack, 2 stacks, no ProcCharges
    204501: {"Name_Lang_enUS": "Strength of Arms", "Attributes": 0, "DurationIndex": DUR["20s"], "ProcCharges": 0,
             "CumulativeAura": 2, "Effect_1": EFF_APPLY_AURA, "EffectAura_1": AURA_SPELLMOD_PCT,
             "EffectMiscValue_1": OP_DAMAGE, "EffectBasePoints_1": 4, "EffectSpellClassMaskA_1": 0x2000000},
    204502: {"Name_Lang_enUS": "Strength of Arms", "Attributes": 0, "DurationIndex": DUR["20s"], "ProcCharges": 0,
             "CumulativeAura": 2, "Effect_1": EFF_APPLY_AURA, "EffectAura_1": AURA_SPELLMOD_PCT,
             "EffectMiscValue_1": OP_DAMAGE, "EffectBasePoints_1": 9, "EffectSpellClassMaskA_1": 0x2000000},
    # D11 Endless Rage overflow: stacks to 20, +1% per stack on Mortal Strike (the script writes the amount)
    ENDLESS_RAGE_BUFF: {"Name_Lang_enUS": "Endless Rage", "Attributes": 0, "DurationIndex": DUR["20s"],
                        "ProcCharges": 0, "CumulativeAura": 20, "Effect_1": EFF_APPLY_AURA,
                        "EffectAura_1": AURA_SPELLMOD_PCT, "EffectMiscValue_1": OP_DAMAGE,
                        "EffectSpellClassMaskA_1": 0x2000000},
    # D15 Exploiter debuff: per caster, 2 stacks, 20 s, visible, a DUMMY the multiplier reads
    EXPLOITER_DEBUFF: {"Name_Lang_enUS": "Exploiter", "Attributes": 0, "AttributesEx3": ATTR3_ONE_INSTANCE_PER_CASTER,
                       "DurationIndex": DUR["20s"], "CumulativeAura": 2, "Effect_1": EFF_APPLY_AURA,
                       "EffectAura_1": AURA_DUMMY, "ImplicitTargetA_1": 6},
    204505: _wrecking(4), 204506: _wrecking(9), 204507: _wrecking(14),
    # D12 Anger Management capstone buff: -30% damage taken for 4 s, visible
    ANGER_CAPSTONE: {"Name_Lang_enUS": "Anger Management", "Attributes": 0, "DurationIndex": DUR["4s"],
                     "Effect_1": EFF_APPLY_AURA, "EffectAura_1": AURA_DMG_TAKEN_PCT, "EffectBasePoints_1": -31,
                     "EffectMiscValue_1": 127},
    # D19 the Seismic echo: Blade Flurry copy shape, hidden, no crit, post-armor (custom attr 0x8000)
    SEISMIC_ECHO: {"Name_Lang_enUS": "Seismic Reverberation", "Attributes": 0x80, "AttributesEx2": ATTR2_CANT_CRIT,
                   "AttributesEx3": 0x20050000, "SpellClassSet": 4, "SpellClassMask_1": 0, "SpellClassMask_2": 0,
                   "SpellClassMask_3": 0, "DefenseType": 0, "Effect_1": EFF_SCHOOL_DAMAGE},
    # D18 Second Wind heal: hidden HEAL
    SECOND_WIND_HEAL: {"Name_Lang_enUS": "Second Wind", "Attributes": 0x80, "Effect_1": EFF_HEAL,
                       "AttributesEx2": 0},
    # D17 the sword strike: 120% weapon, melee DmgClass, hidden, not crit-locked
    SWORD_STRIKE: {"Name_Lang_enUS": "Weapon Specialization", "Attributes": 0x80, "AttributesEx2": 0,
                   "AttributesEx3": 0x10000, "AttributesEx4": 0x800000, "DefenseType": 2, "RangeIndex": 13,
                   "Effect_1": EFF_WEAPON_PERCENT, "EffectBasePoints_1": 119},
}
VISIBLE_IDS = (CS_DEBUFF, AVATAR, SWEEPING, SWEEPING_COPY, WHIRL, DW_HOLDER, MOMENTUM_BUFF, JUGGERNAUT_BUFF,
               *SOA_BUFFS, ENDLESS_RAGE_BUFF, EXPLOITER_DEBUFF, *WRECKING_BUFFS, ANGER_CAPSTONE)
HIDDEN_IDS = (DW_TICK, JUGGERNAUT_CRIT, SEISMIC_ECHO, SECOND_WIND_HEAL, SWORD_STRIKE, *range(204512, 204521))
CANT_CRIT_IDS = (DW_TICK, SEISMIC_ECHO)
MELEE_DMGCLASS_IDS = (SWEEPING_COPY, WHIRL, SWORD_STRIKE)       # DefenseType 2 (DmgClass MELEE): they can crit
CUSTOM_ATTR_IDS = {DW_TICK: CU_IGNORE_ARMOR, SEISMIC_ECHO: CU_IGNORE_ARMOR}

# the learn levels (D3, D4, D7, D10, W0a), SpellLevel == BaseLevel, no slope
SPELL_LEVELS = {12294: 20, 204493: 30, 204490: 40, 46924: 50, 204495: 50, 204492: 60}

# aura texts of the visible buffs ("Shows a buff" lines of docs/reworks/warrior-arms-rework.md)
AURA_TEXTS = {
    CS_DEBUFF: "Taking more damage from the warrior who smashed it.",
    AVATAR: "Your attacks smash through enemy defenses.",
    SWEEPING: "Your melee abilities strike nearby enemies.",
    DW_HOLDER: "Bleeding.",
    MOMENTUM_BUFF: "Your next Slam is free and stronger.",
    JUGGERNAUT_BUFF: "Your next Slam will critically strike and your next Mortal Strike applies Rend.",
    204501: "Your next Mortal Strike is stronger.", 204502: "Your next Mortal Strike is stronger.",
    ENDLESS_RAGE_BUFF: "Your next Mortal Strike deals more damage.",
    EXPLOITER_DEBUFF: "Takes more damage from the warrior's next Mortal Strike.",
    204505: "Your strikes hit harder.", 204506: "Your strikes hit harder.", 204507: "Your strikes hit harder.",
    ANGER_CAPSTONE: "Taking less damage.",
    BLADESTORM: "Spinning. Cannot use other abilities.",
}

# ---- script / proc / group bindings ---------------------------------------------------------------------------------
S2_BINDINGS = {
    MORTAL_STRIKE: {"spell_warr_mortal_strike_arms"}, REND: {"spell_warr_rend_arms"},
    -12834: {"spell_warr_deep_wounds_rework"}, DW_HOLDER: {"spell_warr_deep_wounds_holder"},
    -29723: {"spell_warr_sudden_death_reset"}, HEROIC_LEAP_LANDING: {"spell_warr_heroic_leap_landing"},
    WHIRL: {"spell_warr_bladestorm_whirl"}, 1680: {"spell_warr_whirlwind_seismic"},
    -12296: {"spell_warr_anger_management"}, 204514: {"spell_warr_weapon_spec_sword"},
    204517: {"spell_warr_weapon_spec_sword"}, 204520: {"spell_warr_weapon_spec_sword"},
    SWEEPING: {"spell_warr_sweeping_strikes_rework"},
}
S2_UNBINDINGS = {(-12834, "spell_warr_deep_wounds_aura"), (-12162, "spell_warr_deep_wounds"),
                 (-29723, "spell_war_sudden_death_aura"), (-29723, "spell_warr_extra_proc"),
                 (-29834, "spell_warr_second_wind")}
# S2 kept the Fury row of spell_warr_extra_proc (-46913) bound; S3 (D15) replaced it with the 204652 trigger and
# unbinds it (test_warrior_s3.py pins the unbinding), so nothing is "kept" any more
S2_KEPT_BINDINGS: set[tuple[int, str]] = set()
S2_PROC_REMOVALS = {-12281, -29834, -46854, 64976, -12289}
# ids that must carry no S2 script at all (helpers whose logic lives in other hooks)
S2_UNSCRIPTED = (SWEEPING_COPY, DW_TICK, SEISMIC_ECHO, SWORD_STRIKE, CS_BUTTON, CS_DEBUFF, AVATAR)

# spell_proc rows: id -> {column: value}
S2_PROC_ROWS = {
    -29723: {"SpellFamilyName": 4, "SpellFamilyMask0": 0, "SpellFamilyMask1": 0, "SpellFamilyMask2": 0,
             "ProcFlags": 0x14, "SpellPhaseMask": 1, "Cooldown": 6000},                    # R10 / D9
    -56636: {"SpellFamilyName": 4, "SpellFamilyMask0": 0x20, "SpellPhaseMask": 2, "Cooldown": 0},   # D6
    -46865: {"SpellFamilyName": 4, "SpellFamilyMask0": 0x20200004, "ProcFlags": 0x10, "SpellPhaseMask": 1,
             "Chance": 100.0, "Cooldown": 0},                                              # D14
    204514: {"SpellFamilyName": 0, "ProcFlags": 0x14, "SpellPhaseMask": 1, "Cooldown": 3000},   # D17
    204517: {"SpellFamilyName": 0, "ProcFlags": 0x14, "SpellPhaseMask": 1, "Cooldown": 3000},
    204520: {"SpellFamilyName": 0, "ProcFlags": 0x14, "SpellPhaseMask": 1, "Cooldown": 3000},
    204535: {"SpellFamilyName": 4, "SpellFamilyMask0": 0x4, "ProcFlags": 0x10, "SpellPhaseMask": 1},   # D24
    204536: {"SpellFamilyName": 4, "SpellFamilyMask0": 0x4, "ProcFlags": 0x10, "SpellPhaseMask": 1},
}
S2_NO_PROC_ROW = (204531, 204532, -204531, -204532, 12294)       # R7: Exploiter is a dispatcher branch, no procs_on

# SpellDescriptionVariables (D27): id -> rank spells it reads; spell -> the token its description reads
SDV_ROWS = {1385: (12282, 12663, 12664), 1386: (204533, 204534), 1387: (35446, 35448),
            1388: (12286, 12658, 204540)}
# S3 (D37) moved Heroic Strike (78) and Slam (1464) from S2's 1385 (`$<hb>`) to 1405 / 1406, whose tooltip multiplier is
# `$<mult>` (Heavy Blows x the Fury talents); SDV 1385 itself stays defined (test_warrior_s3.py pins 1405-1409 and 1385)
SDV_READERS = {78: "$<mult>", 1464: "$<mult>", 7384: "$<bl>", 12294: "$<ims>", 772: "$<ir>"}

# SkillLineAbility rows (D3 / D4 / D7): id -> spell (skill line 26 = Arms, class mask 1)
SLA_ROWS = {30850: 204490, 30851: 204492, 30852: 204493}

# docs/reworks/warrior-arms-rework.md "Tooltip" lines: sid -> fragments the built description must contain
TOOLTIP_FRAGMENTS = {
    12282: ("damage of your Heroic Strike and Slam by 5%",), 12663: ("Heroic Strike and Slam by 10%",),
    12664: ("Heroic Strike and Slam by 15%",),
    204521: ("Increases your Mastery by 1%",), 204522: ("Mastery by 2%",), 204523: ("Mastery by 3%",),
    12286: ("bleed damage done by your Rend by 10%", "critical strike chance by 3%"),
    12658: ("Rend by 20%", "critical strike chance by 6%"),
    204540: ("Rend by 30%", "critical strike chance by 10%"),
    12285: ("rage generated by your Charge by 5", "stun by 0.5 sec",
            "The range of your Charge is increased by 5 yards"),
    12697: ("Charge by 10", "stun by 1 sec", "The range of your Charge is increased by 5 yards"),
    204524: ("15% more rage from damage dealt", "3% more Physical melee damage", "Colossus Smash lasts 1 sec longer",
             "does not work with Titan's Grip"),
    204525: ("30% more rage", "6% more Physical melee damage", "Colossus Smash lasts 2 sec longer"),
    204526: ("duration of your Rend by 2 sec",), 204527: ("Rend by 4 sec",), 204528: ("Rend by 6 sec",),
    12296: ("Generates 2 rage every 3 sec", "Charge by 5", "reduces your damage taken by 30% for 4 sec"),
    204541: ("Generates 4 rage every 3 sec", "Charge by 10"), 204542: ("Generates 6 rage every 3 sec", "Charge by 15"),
    16493: ("critical strike damage bonus of your Warrior abilities by 10%",),
    16494: ("critical strike damage bonus of your Warrior abilities by 20%",),
    12834: ("bleed for 11% of your melee weapon's average damage over 6 sec",),
    12849: ("22% of your melee weapon's average damage",), 12867: ("33% of your melee weapon's average damage",),
    12290: ("critical strike chance of your Overpower by 20%",), 12963: ("Overpower by 40%",),
    12163: ("two-handed melee weapons by 1%", "critical strike chance by 1%"),
    12711: ("two-handed melee weapons by 2%", "critical strike chance by 2%"),
    12712: ("two-handed melee weapons by 3%", "critical strike chance by 3%"),
    56636: ("Your Rend damage has a 10% chance to grant a charge of Overpower, stacking up to 5 times",
            "Your Mortal Strike has a 50% chance to grant a charge of Overpower"),
    56637: ("20% chance to grant a charge of Overpower",), 56638: ("30% chance to grant a charge of Overpower",),
    204493: ("For 10 sec", "strike up to 4 additional nearby enemies for 40% of their damage",
             "Rend and Colossus Smash apply in full to each enemy struck", "Shares a cooldown with Blade Flurry"),
    204529: ("duration of your Sweeping Strikes by 2 sec", "from 40% to 45%"),
    204530: ("Sweeping Strikes by 4 sec", "from 40% to 50%"),
    12281: ("Axes and polearms: critical strike chance and critical strike damage increased by 2%",
            "Maces: armor penetration increased by 5%", "have a 3% chance to grant an extra attack",
            "120% weapon damage, no more than once every 3 sec"),
    12812: ("increased by 4%", "armor penetration increased by 10%", "have a 6% chance"),
    12813: ("increased by 6%", "armor penetration increased by 15%", "have a 10% chance"),
    204531: ("15% more damage from your next Mortal Strike", "stacking up to 2 times", "Lasts 20 sec"),
    204532: ("30% more damage from your next Mortal Strike",),
    204533: ("damage of your Overpower by 10%",), 204534: ("damage of your Overpower by 20%",),
    46854: ("damage of your Deep Wounds by 15%",), 46855: ("damage of your Deep Wounds by 30%",),
    29834: ("heal you for 2% of the damage they deal", "doubled while you are below 35% health"),
    29838: ("heal you for 4% of the damage they deal",),
    204490: ("420% weapon damage", "for 6 sec", "damage it takes from you by 15% plus your Mastery",
             "reduces the remaining cooldown of Colossus Smash by 2 sec"),
    46865: ("total Strength by 2% and Stamina by 1%", "next Mortal Strike deals 5% more damage",
            "stacking up to 2 times"),
    46866: ("Strength by 4% and Stamina by 2%", "Mortal Strike deals 10% more damage"),
    204535: ("15% chance to make your next Slam cost no rage and deal 30% more damage",),
    204536: ("30% chance to make your next Slam cost no rage and deal 30% more damage",),
    64976: ("more than 20 yards away or at a target above 90% health",
            "50% chance for your next Slam to critically hit",
            "next Mortal Strike to apply Rend", "cooldown of your Heroic Leap by 2 sec"),
    204543: ("100% chance for your next Slam to critically hit", "cooldown of your Heroic Leap by 4 sec"),
    35446: ("damage of your Mortal Strike by 5% and its healing reduction by 5%",),
    35448: ("Mortal Strike by 10% and its healing reduction by 10%",),
    204537: ("radius of your Heroic Leap's landing from 8 to 16 yards", "afflicted by your Colossus Smash",
             "only strikes enemies already in combat"),
    204538: ("strikes 3 or more enemies", "again 0.5 sec later for 25% of its damage"),
    204539: ("again 0.5 sec later for 50% of its damage",),
    29723: ("5% chance to reset the cooldown of your Mortal Strike", "more than once every 6 sec",
            "Mortal Strike cannot trigger this effect", "keep at least 3 rage after using Execute"),
    29725: ("10% chance to reset the cooldown", "keep at least 7 rage"),
    29724: ("15% chance to reset the cooldown", "keep at least 10 rage"),
    29836: ("melee attack speed by 2%", "increase all physical damage the target takes by 2%"),
    29859: ("melee attack speed by 4%", "increase all physical damage the target takes by 4%"),
    29623: ("maximum rage by 10", "Rage you would gain above your maximum instead increases the damage of your next "
                                  "Mortal Strike by 1% per point, up to 20%, for 20 sec"),
    204544: ("maximum rage by 20",),
    46867: ("main-hand and melee ability critical strikes increase the damage of your Overpower, Mortal Strike, "
            "Execute, Rend, Thunder Clap, Heroic Leap, Colossus Smash and Bladestorm by 5% for 12 sec",),
    56611: ("Bladestorm by 10% for 12 sec",), 56612: ("Bladestorm by 15% for 12 sec",),
    204492: ("grow larger for 20 sec", "applies your Colossus Smash to every enemy it strikes"),
    204491: ("Taking more damage from the warrior who smashed it",),
    204505: ("Overpower, Mortal Strike, Execute, Rend, Thunder Clap, Heroic Leap, Colossus Smash and Bladestorm "
             "by 5%",),
    204506: ("Bladestorm by 10%",), 204507: ("Bladestorm by 15%",),
    204501: ("next Mortal Strike deals 5% more damage per stack",),
    204502: ("next Mortal Strike deals 10% more damage per stack",),
    MOMENTUM_BUFF: ("next Slam costs no rage and deals 30% more damage",),
    BLADESTORM: ("striking up to 5 nearby enemies",),
    WHIRL: ("up to 5 nearby enemies",),
}
# the capstones (D26): name -> rank spells. Colossus Smash dropped 2026-10-30 (user: its Mastery line is main text)
CAPSTONE_RANKS = {
    "Improved Charge": (12285, 12697), "Anger Management": (12296, 204541, 204542),
    "Taste for Blood": (56636, 56637, 56638), "Endless Rage": (29623, 204544),
}
# ids whose Description may keep a '$' (stock variables `$t1` / `$d`, SDV tokens); everything else S2 must be plain
S2_DOLLAR_EXEMPT = {BLADESTORM}
S2_DOLLAR_SCAN = tuple(sorted(set(S2_IDS) | set(S2_SPELLMOD_RANK_IDS) | {BLADESTORM} | set(AURA_TEXTS)))


# ---- checks (pure: take built rows / package tables, return problem strings) ------------------------------------

def check_grid(talents: list[dict]) -> list[str]:
    bad = []
    arms = {int(t["id"]): t for t in talents if int(t["tab_id"]) == ARMS_TAB}
    if sorted(arms) != sorted(GRID):
        bad.append(f"Arms tab talents {sorted(arms)}, expected exactly the {len(GRID)} doc talents {sorted(GRID)}")
    seen: dict[tuple[int, int], int] = {}
    points = 0
    for tid, (cell, ranks) in sorted(GRID.items()):
        t = arms.get(tid)
        if t is None:
            bad.append(f"talent {tid}: not in the Arms tab")
            continue
        got = (int(t["tier"]), int(t["column"]))
        if got != cell:
            bad.append(f"talent {tid}: cell (tier, column) {got}, expected {cell}")
        if tuple(int(x) for x in t["rank_spell_ids"]) != ranks:
            bad.append(f"talent {tid}: ranks {t['rank_spell_ids']}, expected {list(ranks)}")
        points += len(t["rank_spell_ids"])
        if t.get("depends_on"):
            bad.append(f"talent {tid}: has a prerequisite {t['depends_on']} (the doc grid has no arrows)")
        want_flags = 1 if tid in FLAGGED else 0
        if int(t.get("flags") or 0) != want_flags:
            bad.append(f"talent {tid}: Flags {t.get('flags')!r}, expected {want_flags}")
    for tid, t in sorted(arms.items()):
        cell = (int(t["tier"]), int(t["column"]))
        if cell in seen:
            bad.append(f"talents {seen[cell]} and {tid} share the cell {cell}")
        seen[cell] = tid
        if not (0 <= cell[0] <= 10 and 0 <= cell[1] <= 3):
            bad.append(f"talent {tid}: cell {cell} is off the grid")
    if points != GRID_POINTS:
        bad.append(f"the grid carries {points} points, expected {GRID_POINTS}")
    for tier, want in enumerate(GRID_ROW_POINTS):
        got = sum(len(t["rank_spell_ids"]) for t in arms.values() if int(t["tier"]) == tier)
        if got != want:
            bad.append(f"tier {tier} carries {got} points, expected {want}")
    minted = sorted(tid for tid in arms if 60450 <= tid <= 60464)
    if minted != list(MINTED):
        bad.append(f"minted talents {minted}, expected {list(MINTED)}")
    holding = {int(t["id"]): t for t in talents if int(t["tab_id"]) == HOLDING_TAB}
    for tid in RETIRED:
        t = holding.get(tid)
        if t is None:
            bad.append(f"talent {tid}: not retired to the holding tab {HOLDING_TAB}")
        elif t["rank_spell_ids"]:
            bad.append(f"talent {tid}: retired but still lists ranks {t['rank_spell_ids']}")
        if tid in arms:
            bad.append(f"talent {tid}: retired but still in the Arms tab")
    return bad


def check_rank_specs(rows: dict) -> list[str]:
    """Every rank row: its effects (aura, misc, base points per rank, the mask on the effect's own letter), the columns
    pinned on every rank / per rank, and the empty slots (stale residue cleared)."""
    bad = []
    for name, (ids, effects, cols, rank_cols) in SPECS.items():
        bad += _missing(rows, *ids)
        if any(sid not in rows for sid in ids):
            continue
        for rank, sid in enumerate(ids):
            r = rows[sid]
            for idx, aura, misc, bps, mask in effects:
                if aura is None or bps[rank] is None:
                    bad += _effect_empty(r, idx, sid, name)
                else:
                    bad += _aura_effect(r, idx, aura, misc, bps[rank], mask, sid, name)
            for idx in sorted({0, 1, 2} - {e[0] for e in effects}):      # an effect the spec does not name is empty
                bad += _effect_empty(r, idx, sid, name)
            for col, val in cols.items():
                if _i(r, col) != val:
                    bad.append(f"{sid}: {name} {col} {r.get(col)!r}, expected {val!r}")
            for col, vals in rank_cols.items():
                if _i(r, col) != vals[rank]:
                    bad.append(f"{sid}: {name} {col} {r.get(col)!r}, expected {vals[rank]!r}")
    return bad


def check_empty_mask_spellmods(rows: dict) -> list[str]:
    """No S2 SpellMod (aura 107 / 108) on a built row may have an empty mask on its own letter (it would leak into
    every spell, or into none)."""
    bad = []
    for sid in sorted(set(S2_SPELLMOD_RANK_IDS) | set(S2_IDS)):
        r = rows.get(sid)
        if r is None:
            continue
        for idx in range(3):
            typ, aura, _misc, _bp = s1._eff(r, idx)
            if typ == EFF_APPLY_AURA and aura in (AURA_SPELLMOD_FLAT, AURA_SPELLMOD_PCT) and not any(_emask(r, idx)):
                bad.append(f"{sid}: e{idx} is a SpellMod with an empty mask")
    return bad


def check_sudden_death(rows: dict) -> list[str]:
    bad = _missing(rows, *SUDDEN_DEATH)
    if bad:
        return bad
    for rank, sid in enumerate(SUDDEN_DEATH):
        r = rows[sid]
        # Execute's rage-kept lookup (spell_warrior.cpp:445-450) reads SpellFamilyGeneric + icon 1989 + e0 PROC_TRIGGER
        # and Effects[EFFECT_1].CalcValue(): the shape must not move
        if _i(r, "SpellClassSet") != 0:
            bad.append(f"{sid}: SpellClassSet {r.get('SpellClassSet')!r}, expected 0 (Execute's lookup)")
        if _i(r, "SpellIconID") != 1989:
            bad.append(f"{sid}: icon {r.get('SpellIconID')!r}, expected 1989")
        bad += _aura_effect(r, 0, AURA_PROC_TRIGGER, None, SUDDEN_DEATH_E0_BP[rank], Z, sid, "Sudden Death")
        if _i(r, "EffectBasePoints_2") != SUDDEN_DEATH_E1_BP[rank]:
            bad.append(f"{sid}: e1 bp {r.get('EffectBasePoints_2')!r}, expected {SUDDEN_DEATH_E1_BP[rank]} "
                       f"(kept rage {SUDDEN_DEATH_E1_BP[rank] + 1})")
        if _i(r, "ProcChance") != SUDDEN_DEATH_CHANCE[rank]:
            bad.append(f"{sid}: ProcChance {r.get('ProcChance')!r}, expected {SUDDEN_DEATH_CHANCE[rank]}")
        if _i(r, "ProcTypeMask") != 20:
            bad.append(f"{sid}: ProcTypeMask {r.get('ProcTypeMask')!r}, expected 20")
    return bad


def check_new_row_pins(rows: dict) -> list[str]:
    bad = _missing(rows, *NEW_ROW_PINS)
    for sid, pins in NEW_ROW_PINS.items():
        r = rows.get(sid)
        if r is None:
            continue
        for col, val in pins.items():
            got = r.get(col)
            if isinstance(val, str):
                if got != val:
                    bad.append(f"{sid}: {col} {got!r}, expected {val!r}")
            elif _u32(got) != _u32(val):
                bad.append(f"{sid}: {col} {hex(_u32(got))}, expected {hex(_u32(val))}"
                           if col.startswith(("Attributes", "SpellClassMask", "EffectSpellClassMask"))
                           else f"{sid}: {col} {got!r}, expected {val!r}")
    return bad


def check_visibility(rows: dict) -> list[str]:
    """D28: the buffs the doc says are shown carry neither PASSIVE 0x40 nor DO_NOT_DISPLAY 0x80; the helpers hide."""
    bad = _missing(rows, *VISIBLE_IDS, *HIDDEN_IDS)
    for sid in VISIBLE_IDS:
        if sid in rows and _i(rows[sid], "Attributes") & (ATTR0_PASSIVE | ATTR0_DO_NOT_DISPLAY):
            bad.append(f"{sid}: should be visible but Attributes {hex(_i(rows[sid], 'Attributes'))}")
    for sid in HIDDEN_IDS:
        if sid in rows and not _i(rows[sid], "Attributes") & ATTR0_DO_NOT_DISPLAY:
            bad.append(f"{sid}: should be hidden (0x80) but Attributes {hex(_i(rows[sid], 'Attributes'))}")
    for sid in CANT_CRIT_IDS:
        if sid in rows and not _i(rows[sid], "AttributesEx2") & ATTR2_CANT_CRIT:
            bad.append(f"{sid}: lost CANT_CRIT (0x20000000)")
    if DW_TICK in rows and not _i(rows[DW_TICK], "AttributesEx2") & ATTR2_IGNORE_LINE_OF_SIGHT:
        bad.append(f"{DW_TICK}: lost IGNORE_LINE_OF_SIGHT (0x4): a tick behind a corner would be lost")
    for sid in MELEE_DMGCLASS_IDS:
        if sid in rows:
            if _i(rows[sid], "DefenseType") != 2:
                bad.append(f"{sid}: DmgClass {rows[sid].get('DefenseType')!r}, expected 2 (MELEE)")
            if _i(rows[sid], "AttributesEx2") & ATTR2_CANT_CRIT:
                bad.append(f"{sid}: carries CANT_CRIT but must be able to crit")
    if SWEEPING in rows and _i(rows[SWEEPING], "Attributes") & ATTR0_NOT_SHAPESHIFTED:
        bad.append(f"{SWEEPING}: carries NOT_SHAPESHIFTED 0x10000 (the stock row's correction is not wanted)")
    if CS_BUTTON in rows and not _i(rows[CS_BUTTON], "AttributesEx3") & 0x400:
        bad.append(f"{CS_BUTTON}: lost AttrEx3 0x400")
    for sid in (CS_BUTTON, SWEEPING):
        if sid in rows and _i(rows[sid], "Attributes") & ATTR0_DO_NOT_DISPLAY:
            bad.append(f"{sid}: the castable is hidden")
    return bad


def check_no_aura_271(rows: dict) -> list[str]:
    """204491 is a DUMMY: aura 271 is already read by the core on weapon strikes and would apply twice."""
    bad = []
    for sid in S2_IDS:
        r = rows.get(sid)
        if r is None:
            continue
        for idx in range(3):
            if s1._eff(r, idx)[1] == AURA_APPLY_DAMAGE_AURA_FORBIDDEN:
                bad.append(f"{sid}: e{idx} uses aura 271")
    return bad


def check_durations(rows: dict, dur_ms) -> list[str]:
    """R21: the duration indexes resolve to the intended times through the stock SpellDuration table."""
    bad = []
    for idx, ms in sorted(DUR_MS.items()):
        got = dur_ms({"DurationIndex": idx})
        if got != ms:
            bad.append(f"SpellDuration index {idx}: {got} ms, expected {ms} ms (R21)")
    return bad


def check_custom_attrs(custom_attrs: dict) -> list[str]:
    bad = []
    for sid, flag in CUSTOM_ATTR_IDS.items():
        if custom_attrs.get(sid) != flag:
            bad.append(f"{sid}: custom attr {custom_attrs.get(sid)!r}, expected {flag:#x}")
    extra = sorted(sid for sid in custom_attrs if S2_FIRST <= sid <= S2_LAST and sid not in CUSTOM_ATTR_IDS)
    if extra:
        bad.append(f"unexpected custom attrs on S2 ids {extra}")
    return bad


def check_spell_levels(rows: dict) -> list[str]:
    bad = _missing(rows, *SPELL_LEVELS)
    if bad:
        return bad
    for sid, level in sorted(SPELL_LEVELS.items()):
        r = rows[sid]
        got = (_i(r, "SpellLevel"), _i(r, "BaseLevel"))
        if got != (level, level):
            bad.append(f"{sid}: SpellLevel/BaseLevel {got}, expected {(level, level)}")
        if _i(r, "MaxLevel") != 0:
            bad.append(f"{sid}: MaxLevel {r.get('MaxLevel')!r}, expected 0 (no slope)")
    return bad


def check_bladestorm(rows: dict) -> list[str]:
    """D10: 46924 retargets its tick to the 204495 whirl; the stock aura effects around it stay."""
    bad = _missing(rows, BLADESTORM, WHIRL)
    if bad:
        return bad
    r = rows[BLADESTORM]
    bad += _aura_effect(r, 0, AURA_PERIODIC_TRIGGER, None, -1, Z, BLADESTORM, "Bladestorm")
    if _i(r, "EffectTriggerSpell_1") != WHIRL:
        bad.append(f"{BLADESTORM}: e0 triggers {r.get('EffectTriggerSpell_1')!r}, expected {WHIRL}")
    if _i(r, "EffectAuraPeriod_1") != 1000:
        bad.append(f"{BLADESTORM}: e0 period {r.get('EffectAuraPeriod_1')!r}, expected 1000")
    if _u32(r.get("SpellClassMask_2")) != 0x4000:
        bad.append(f"{BLADESTORM}: identity bit d1 0x4000 changed ({hex(_u32(r.get('SpellClassMask_2')))})")
    if _i(r, "DurationIndex") != DUR["6s"]:
        bad.append(f"{BLADESTORM}: duration index {r.get('DurationIndex')!r}, expected {DUR['6s']} (6 s)")
    return bad


def check_mortal_strike_and_rend(rows: dict) -> list[str]:
    bad = _missing(rows, MORTAL_STRIKE, REND)
    if bad:
        return bad
    ms, rend = rows[MORTAL_STRIKE], rows[REND]
    if _u32(ms.get("SpellClassMask_1")) != 0x2000000 or _u32(ms.get("SpellClassMask_3")) & 0x8 == 0:
        bad.append(f"{MORTAL_STRIKE}: identity bit d0 0x2000000 / group d2 0x8 changed")
    if (_i(ms, "RecoveryTime"), _i(ms, "ManaCost")) != (6000, 250):
        bad.append(f"{MORTAL_STRIKE}: cooldown / cost {(_i(ms, 'RecoveryTime'), _i(ms, 'ManaCost'))}, "
                   "expected (6000, 250) (Q2: row unchanged)")
    if _i(ms, "EffectBasePoints_2") != 227:
        bad.append(f"{MORTAL_STRIKE}: weapon percent bp {ms.get('EffectBasePoints_2')!r}, expected 227 "
                   "(D29 130%, balance 2026-10-30 x1.5 x1.4 x0.8 x1.1 x0.95: 228%)")
    # Q9 (user ruling 2026-10-30): Rend needs any melee weapon (the stock gate); the weapon talents fold into it
    # through the core's normal item-gated aura-79 path (second ruling 2026-10-30: no divide-out hook)
    if (_i(rend, "EquippedItemClass"), _i(rend, "EquippedItemSubclass")) != (2, 173555):
        bad.append(f"{REND}: weapon gate {(rend.get('EquippedItemClass'), rend.get('EquippedItemSubclass'))!r}, "
                   "expected (2, 173555) (Q9: any melee weapon)")
    if _u32(rend.get("SpellClassMask_1")) & 0x20 == 0:
        bad.append(f"{REND}: lost its identity bit d0 0x20")
    return bad


def check_new_ids(rows: dict) -> list[str]:
    bad = []
    # S2's block is 204490-204629 (ids.yaml); S3 owns 204630-204769 (test_warrior_s3.py pins 204630-204680) and S1's
    # 204770-204799 are not scanned here either
    got = sorted(sid for sid in rows if S2_FIRST <= sid <= 204629 or 204800 <= sid <= 204899)
    want = sorted(S2_IDS)
    if got != want:
        bad.append(f"ids in the S2 block: missing {sorted(set(want) - set(got))}, "
                   f"unexpected {sorted(set(got) - set(want))}")
    if S2_RESERVED_UNUSED in rows:
        bad.append(f"{S2_RESERVED_UNUSED} exists (R9: the Weight of the Earth radius mod reaches the landing)")
    reserved = sorted(sid for sid in rows if 204869 <= sid <= 204899)
    if reserved:
        bad.append(f"ids in the reserved 204869-204899 range: {reserved}")
    return bad


def check_bindings(names: list[dict], removals: list[dict]) -> list[str]:
    bad = []
    have: dict[int, set[str]] = {}
    for n in names:
        have.setdefault(int(n["spell_id"]), set()).add(n["ScriptName"])
    for sid, expect in sorted(S2_BINDINGS.items()):
        if have.get(sid, set()) != expect:
            bad.append(f"scripted_by on {sid}: {sorted(have.get(sid, set()))}, expected exactly {sorted(expect)}")
    gone = {(int(n["spell_id"]), n["ScriptName"]) for n in removals}
    for b in sorted(S2_UNBINDINGS - gone):
        bad.append(f"unbind_script {b} is not declared")
    for b in sorted(S2_KEPT_BINDINGS & gone):
        bad.append(f"unbind_script {b} is declared (the Fury row stays bound)")
    for sid, name in sorted(S2_UNBINDINGS):
        if name in have.get(sid, set()):
            bad.append(f"{name} is both bound and unbound on {sid}")
    for sid in S2_UNSCRIPTED:
        if have.get(sid):
            bad.append(f"{sid}: carries a script {sorted(have[sid])} (its logic lives in the shared hooks)")
    return bad


def check_proc_rows(procs: list[dict], proc_removals: list[dict]) -> list[str]:
    bad = []
    by_id = {int(p["SpellId"]): p for p in procs}
    for sid, cols in sorted(S2_PROC_ROWS.items()):
        row = by_id.get(sid)
        if row is None:
            bad.append(f"{sid}: no spell_proc row")
            continue
        for col, val in cols.items():
            got = row.get(col)
            if float(got or 0) != float(val):
                bad.append(f"{sid}: spell_proc {col} {got!r}, expected {val!r}")
    gone = {int(r["SpellId"]) for r in proc_removals}
    for sid in sorted(S2_PROC_REMOVALS - gone):
        bad.append(f"remove_spell_proc({sid}) is not declared")
    for sid in S2_PROC_REMOVALS:
        if sid in by_id:
            bad.append(f"{sid}: a spell_proc row is still declared")
    for sid in S2_NO_PROC_ROW:
        if sid in by_id:
            bad.append(f"{sid}: has a spell_proc row (R7: Exploiter is a dispatcher branch)")
    return bad


def check_spell_groups(groups: list[dict]) -> list[str]:
    bad = []
    for g in groups:
        if int(g["id"]) == 1108 or int(g["spell_id"]) == 30070:
            bad.append(f"spell_group {g['id']}/{g['spell_id']} declared (R8: 30070 is rank 2 of 30069)")
        if int(g["id"]) == 1305 or S2_FIRST <= int(g["spell_id"]) <= S2_LAST:
            bad.append(f"spell_group {g['id']}/{g['spell_id']} declared by S2 (1305 is reserved)")
    return bad


def check_slas(slas: list[dict]) -> list[str]:
    by_id = {int(s["id"]): s for s in slas}
    bad = []
    for sid, spell in SLA_ROWS.items():
        s = by_id.get(sid)
        if s is None:
            bad.append(f"SkillLineAbility {sid} is not declared")
            continue
        got = (int(s["spell_id"]), int(s["skill_line"]), int(s.get("class_mask") or 0),
               int(s.get("acquire_method") or 0))
        if got != (spell, 26, 1, 0):
            bad.append(f"SkillLineAbility {sid}: (spell, skill line, class mask, acquire) {got}, expected "
                       f"{(spell, 26, 1, 0)}")
    forbidden = [sid for sid in by_id if sid in (30868, 30869)]
    if forbidden:
        bad.append(f"SkillLineAbility ids {forbidden} are reserved")
    return bad


def check_sdv(tooltip_vars: list[dict], rows: dict) -> list[str]:
    bad = []
    by_id = {int(t["id"]): t for t in tooltip_vars}
    for vid, ranks in sorted(SDV_ROWS.items()):
        t = by_id.get(vid)
        if t is None:
            bad.append(f"SpellDescriptionVariables {vid}: not declared")
            continue
        for rank in ranks:
            if f"${rank}m" not in t["Variables"]:
                bad.append(f"SDV {vid}: Variables do not read rank spell {rank}")
    for sid, token in sorted(SDV_READERS.items()):
        text = str((rows.get(sid) or {}).get("Description_Lang_enUS") or "")
        if token not in text:
            bad.append(f"{sid}: description does not read {token}")
    return bad


def check_no_stray_dollar(rows: dict) -> list[str]:
    bad = []
    for sid in S2_DOLLAR_SCAN:
        r = rows.get(sid)
        if r is None:
            continue
        if "$" in str(r.get("AuraDescription_Lang_enUS") or ""):
            bad.append(f"{sid}: AuraDescription has a '$': {r.get('AuraDescription_Lang_enUS')!r}")
        if sid not in S2_DOLLAR_EXEMPT and "$" in str(r.get("Description_Lang_enUS") or ""):
            bad.append(f"{sid}: Description has a '$': {r.get('Description_Lang_enUS')!r}")
    return bad


def check_tooltips(rows: dict) -> list[str]:
    bad = []
    for sid, frags in sorted(TOOLTIP_FRAGMENTS.items()):
        r = rows.get(sid)
        if r is None:
            bad.append(f"{sid}: not built")
            continue
        text = str(r.get("Description_Lang_enUS") or "")
        for frag in frags:
            if frag not in text:
                bad.append(f"{sid}: tooltip lacks {frag!r}: {text!r}")
    for sid, text in sorted(AURA_TEXTS.items()):
        r = rows.get(sid)
        if r is None:
            bad.append(f"{sid}: not built")
        elif r.get("AuraDescription_Lang_enUS") != text:
            bad.append(f"{sid}: aura text {r.get('AuraDescription_Lang_enUS')!r}, expected {text!r}")
    return bad


def check_capstones(rows: dict) -> list[str]:
    """The five Arms capstones in the T1 format: grey below the last rank, plain on it, one clause on every rank."""
    bad = []
    for name, ranks in CAPSTONE_RANKS.items():
        if any(sid not in rows for sid in ranks):
            bad += _missing(rows, *ranks)
            continue
        if rows[ranks[0]].get("Name_Lang_enUS") != name:
            bad.append(f"{ranks[0]}: rank 1 is named {rows[ranks[0]].get('Name_Lang_enUS')!r}, expected {name!r}")
        descs = [rows[s].get("Description_Lang_enUS", "") for s in ranks]
        auras = [rows[s].get("AuraDescription_Lang_enUS", "") for s in ranks]
        bad += capfmt.rank_problems(name, descs, auras, list(ranks))
    expected = set(capfmt.EXPECTED_CAPSTONES["warrior"])
    if not set(CAPSTONE_RANKS) <= expected:
        bad.append(f"EXPECTED_CAPSTONES['warrior'] is {sorted(expected)}, S2 expects {sorted(CAPSTONE_RANKS)} in it")
    return bad


# ---- real data ----------------------------------------------------------------------------------------------------

class WarriorS2DataTest(unittest.TestCase):
    def assertClean(self, problems: list[str]):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_grid(self):
        self.assertClean(check_grid(_data()["talents"]))

    def test_rank_rows(self):
        self.assertClean(check_rank_specs(_data()["rows"]))

    def test_no_empty_mask_spellmod(self):
        self.assertClean(check_empty_mask_spellmods(_data()["rows"]))

    def test_sudden_death_keeps_the_stock_lookup_shape(self):
        self.assertClean(check_sudden_death(_data()["rows"]))

    def test_new_rows(self):
        self.assertClean(check_new_row_pins(_data()["rows"]))

    def test_visible_and_hidden_rows(self):
        self.assertClean(check_visibility(_data()["rows"]))

    def test_no_aura_271(self):
        self.assertClean(check_no_aura_271(_data()["rows"]))

    def test_durations(self):
        self.assertClean(check_durations(_data()["rows"], s1._dur_ms))

    def test_custom_attrs(self):
        self.assertClean(check_custom_attrs(_data()["custom_attrs"]))

    def test_spell_levels(self):
        self.assertClean(check_spell_levels(_data()["rows"]))

    def test_bladestorm(self):
        self.assertClean(check_bladestorm(_data()["rows"]))

    def test_mortal_strike_and_rend(self):
        self.assertClean(check_mortal_strike_and_rend(_data()["rows"]))

    def test_new_ids(self):
        self.assertClean(check_new_ids(_data()["rows"]))

    def test_bindings(self):
        d = _data()
        self.assertClean(check_bindings(d["names"], d["removals"]))

    def test_proc_rows(self):
        d = _data()
        self.assertClean(check_proc_rows(d["procs"], d["proc_removals"]))

    def test_spell_groups(self):
        self.assertClean(check_spell_groups(_data()["package"].spell_groups))

    def test_skill_line_abilities(self):
        self.assertClean(check_slas(_data()["package"].skill_line_abilities))

    def test_spell_description_variables(self):
        d = _data()
        self.assertClean(check_sdv(d["tooltip_vars"], d["rows"]))

    def test_no_stray_dollar(self):
        self.assertClean(check_no_stray_dollar(_data()["rows"]))

    def test_tooltips_match_the_doc(self):
        self.assertClean(check_tooltips(_data()["rows"]))

    def test_capstone_format(self):
        self.assertClean(check_capstones(_data()["rows"]))


# ---- negative fixtures: every check must fire on a minimal bad mutation of the real built rows -------------------

def _bump(val):
    """A different value of the same kind."""
    return val + "x" if isinstance(val, str) else val + 1


class WarriorS2NegativeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = _data()
        cls.rows = cls.d["rows"]

    def fires(self, check, mutations, *extra, missing=True):
        """`check(rows, *extra)` is clean on the real rows and reports on each (sid, column, value) mutation, and (when
        `missing`) on the first mutated row never having been built."""
        self.assertEqual(check(self.rows, *extra), [], check.__name__)
        for sid, col, val in mutations:
            self.assertGreaterEqual(len(check(_mut(self.rows, sid, **{col: val}), *extra)), 1,
                                    (check.__name__, sid, col, val))
        if missing:
            sid = mutations[0][0]
            self.assertGreaterEqual(len(check({k: v for k, v in self.rows.items() if k != sid}, *extra)), 1)

    def test_grid(self):
        talents = self.d["talents"]
        self.assertEqual(check_grid(talents), [])
        for tid, (cell, ranks) in GRID.items():
            for field, val in (("tier", cell[0] + 1), ("column", (cell[1] + 1) % 4), ("flags", 1 - (tid in FLAGGED))):
                mutated = [{**t, field: val} if int(t["id"]) == tid else t for t in talents]
                self.assertGreaterEqual(len(check_grid(mutated)), 1, (tid, field))
            dropped = [{**t, "rank_spell_ids": list(t["rank_spell_ids"])[:-1]} if int(t["id"]) == tid else t
                       for t in talents]
            self.assertGreaterEqual(len(check_grid(dropped)), 1, tid)
            gone = [t for t in talents if int(t["id"]) != tid]
            self.assertGreaterEqual(len(check_grid(gone)), 1, tid)
            dep = [{**t, "depends_on": {"talent_id": 124, "rank": 1}} if int(t["id"]) == tid else t for t in talents]
            self.assertGreaterEqual(len(check_grid(dep)), 1, tid)
        # a collision: Avatar onto Colossus Smash's cell
        collide = [{**t, "tier": 6, "column": 1} if int(t["id"]) == 60460 else t for t in talents]
        self.assertTrue(any("share the cell" in p for p in check_grid(collide)))
        # a retired talent back in the Arms tab / missing from the holding tab / still listing ranks
        for tid in RETIRED:
            back = [{**t, "tab_id": ARMS_TAB} if int(t["id"]) == tid else t for t in talents]
            self.assertGreaterEqual(len(check_grid(back)), 1, tid)
            absent = [t for t in talents if int(t["id"]) != tid]
            self.assertGreaterEqual(len(check_grid(absent)), 1, tid)
            ranked = [{**t, "rank_spell_ids": [12282]} if int(t["id"]) == tid else t for t in talents]
            self.assertGreaterEqual(len(check_grid(ranked)), 1, tid)
        # a stray extra talent in the Arms tab
        extra = [*talents, {"id": 60461, "tab_id": ARMS_TAB, "tier": 0, "column": 3, "rank_spell_ids": [1],
                            "depends_on": None, "flags": 0}]
        self.assertGreaterEqual(len(check_grid(extra)), 1)

    def test_rank_rows(self):
        self.assertEqual(check_rank_specs(self.rows), [])
        for name, (ids, effects, cols, rank_cols) in SPECS.items():
            for rank, sid in enumerate(ids):
                for idx, aura, misc, bps, mask in effects:
                    n = idx + 1
                    letter = "ABC"[idx]
                    if aura is None or bps[rank] is None:
                        # an empty slot grows an aura
                        mutated = _mut(self.rows, sid, **{f"EffectAura_{n}": 4, f"Effect_{n}": EFF_APPLY_AURA})
                        self.assertGreaterEqual(len(check_rank_specs(mutated)), 1, (name, sid, idx, "empty"))
                        continue
                    for col in (f"EffectBasePoints_{n}", f"EffectAura_{n}", f"Effect_{n}"):
                        self.assertGreaterEqual(len(check_rank_specs(_mut(self.rows, sid, **{col: _bump(
                            self.rows[sid][col])}))), 1, (name, sid, idx, col))
                    if misc is not None:
                        col = f"EffectMiscValue_{n}"
                        self.assertGreaterEqual(len(check_rank_specs(_mut(self.rows, sid, **{col: _bump(
                            self.rows[sid][col])}))), 1, (name, sid, idx, col))
                    # every dword of the mask (the right dword on the right letter, or a stray one elsewhere)
                    for dword in (1, 2, 3):
                        col = f"EffectSpellClassMask{letter}_{dword}"
                        cur = _u32(self.rows[sid].get(col))
                        self.assertGreaterEqual(len(check_rank_specs(_mut(self.rows, sid, **{col: cur ^ 0x1}))), 1,
                                                (name, sid, idx, col))
                    # the mask on the neighbour letter (the classic wrong-letter bug)
                    other = "ABC"[(idx + 1) % 3]
                    wrong = f"EffectSpellClassMask{other}_1"
                    if not _u32(self.rows[sid].get(wrong)):
                        self.assertGreaterEqual(len(check_rank_specs(_mut(self.rows, sid, **{wrong: 0x1}))), 1,
                                                (name, sid, idx, wrong))
                for col, val in cols.items():
                    self.assertGreaterEqual(len(check_rank_specs(_mut(self.rows, sid, **{col: _bump(val)}))), 1,
                                            (name, sid, col))
                for col, vals in rank_cols.items():
                    self.assertGreaterEqual(len(check_rank_specs(_mut(self.rows, sid, **{col: _bump(vals[rank])}))),
                                            1, (name, sid, col))
            # a rank never built
            self.assertGreaterEqual(len(check_rank_specs({k: v for k, v in self.rows.items() if k != ids[0]})), 1)

    def test_impale_mask_is_0xf(self):
        # S2 pinned 0xB (group bit + Heroic Leap + Colossus Smash); S3 (D35) adds Rampage's d2 b2: 0xF
        for sid in IMPALE:
            for bad in (0xB, 0x8, 0x1, 0x3, 0xA, 0x0):
                self.assertGreaterEqual(len(check_rank_specs(_mut(self.rows, sid, EffectSpellClassMaskA_3=bad))), 1,
                                        (sid, bad))

    def test_wrecking_crew_masks(self):
        for sid in (204505, 204506, 204507):
            for col, val in (("EffectSpellClassMaskA_1", 0x22000080), ("EffectSpellClassMaskA_2", 0),
                             ("EffectSpellClassMaskA_3", 0x1), ("EffectSpellClassMaskB_1", 0),
                             ("EffectSpellClassMaskB_1", 0x24), ("EffectMiscValue_2", 0), ("EffectMiscValue_2", 3)):
                self.assertGreaterEqual(len(check_new_row_pins(_mut(self.rows, sid, **{col: val}))), 1,
                                        (sid, col, val))

    def test_empty_mask_spellmod(self):
        self.assertEqual(check_empty_mask_spellmods(self.rows), [])
        for sid, idx in ((12282, 0), (204521, 0), (12286, 1), (12285, 2), (204526, 0), (16493, 0), (12290, 0),
                         (204533, 0), (35446, 1), (204537, 0), (204498, 1), (204505, 1), (204501, 0)):
            letter = "ABC"[idx]
            r = self.rows[sid]
            if s1._eff(r, idx)[1] not in (AURA_SPELLMOD_FLAT, AURA_SPELLMOD_PCT):
                continue
            mutated = _mut(self.rows, sid, **{f"EffectSpellClassMask{letter}_{n}": 0 for n in (1, 2, 3)})
            self.assertGreaterEqual(len(check_empty_mask_spellmods(mutated)), 1, (sid, idx))

    def test_sudden_death(self):
        self.fires(check_sudden_death, [
            (29723, "SpellClassSet", 4), (29725, "SpellIconID", 1990), (29724, "Effect_1", 2),
            (29723, "EffectBasePoints_1", 5), (29725, "EffectBasePoints_2", 5), (29724, "EffectBasePoints_2", 10),
            (29723, "ProcChance", 6), (29725, "ProcChance", 0), (29724, "ProcTypeMask", 0),
            (29723, "EffectAura_1", 4), (29725, "EffectSpellClassMaskA_1", 0x1),
        ])

    def test_new_rows(self):
        self.assertEqual(check_new_row_pins(self.rows), [])
        for sid, pins in NEW_ROW_PINS.items():
            for col, val in pins.items():
                self.assertGreaterEqual(len(check_new_row_pins(_mut(self.rows, sid, **{col: _bump(val)}))), 1,
                                        (sid, col))
            self.assertGreaterEqual(len(check_new_row_pins({k: v for k, v in self.rows.items() if k != sid})), 1)

    def test_visibility(self):
        self.assertEqual(check_visibility(self.rows), [])
        for sid in VISIBLE_IDS:
            for flag in (ATTR0_PASSIVE, ATTR0_DO_NOT_DISPLAY):
                mutated = _mut(self.rows, sid, Attributes=_i(self.rows[sid], "Attributes") | flag)
                self.assertGreaterEqual(len(check_visibility(mutated)), 1, (sid, flag))
        for sid in HIDDEN_IDS:
            mutated = _mut(self.rows, sid, Attributes=_i(self.rows[sid], "Attributes") & ~ATTR0_DO_NOT_DISPLAY)
            self.assertGreaterEqual(len(check_visibility(mutated)), 1, sid)
        for sid in CANT_CRIT_IDS:
            self.assertGreaterEqual(len(check_visibility(_mut(self.rows, sid, AttributesEx2=0))), 1, sid)
        self.assertGreaterEqual(len(check_visibility(_mut(self.rows, DW_TICK, AttributesEx2=ATTR2_CANT_CRIT))), 1)
        for sid in MELEE_DMGCLASS_IDS:
            self.assertGreaterEqual(len(check_visibility(_mut(self.rows, sid, DefenseType=0))), 1, sid)
            self.assertGreaterEqual(len(check_visibility(_mut(self.rows, sid, AttributesEx2=ATTR2_CANT_CRIT))), 1, sid)
        # the Sweeping Strikes id must not carry NOT_SHAPESHIFTED
        mutated = _mut(self.rows, SWEEPING, Attributes=_i(self.rows[SWEEPING], "Attributes") | ATTR0_NOT_SHAPESHIFTED)
        self.assertGreaterEqual(len(check_visibility(mutated)), 1)
        self.assertGreaterEqual(len(check_visibility(_mut(self.rows, CS_BUTTON, AttributesEx3=0))), 1)
        self.assertGreaterEqual(len(check_visibility({k: v for k, v in self.rows.items() if k != DW_HOLDER})), 1)

    def test_no_aura_271(self):
        self.assertEqual(check_no_aura_271(self.rows), [])
        for sid in (CS_DEBUFF, CS_BUTTON, AVATAR, 204501):
            self.assertGreaterEqual(len(check_no_aura_271(_mut(self.rows, sid, EffectAura_1=271, Effect_1=6))), 1, sid)

    def test_durations(self):
        self.assertEqual(check_durations(self.rows, s1._dur_ms), [])
        self.assertGreaterEqual(len(check_durations(self.rows, lambda _row: 1234)), 1)
        self.assertGreaterEqual(len(check_durations(self.rows, lambda row: DUR_MS[_i(row, "DurationIndex")] + 1)), 1)

    def test_custom_attrs(self):
        ca = self.d["custom_attrs"]
        self.assertEqual(check_custom_attrs(ca), [])
        for sid in CUSTOM_ATTR_IDS:
            self.assertGreaterEqual(len(check_custom_attrs({k: v for k, v in ca.items() if k != sid})), 1, sid)
            self.assertGreaterEqual(len(check_custom_attrs({**ca, sid: 0x4000})), 1, sid)
        self.assertGreaterEqual(len(check_custom_attrs({**ca, 204511: CU_IGNORE_ARMOR})), 1)
        self.assertGreaterEqual(len(check_custom_attrs({**ca, SWEEPING_COPY: CU_IGNORE_ARMOR})), 1)

    def test_spell_levels(self):
        self.fires(check_spell_levels, [
            (12294, "SpellLevel", 40), (12294, "BaseLevel", 1), (204493, "SpellLevel", 20), (204490, "BaseLevel", 30),
            (46924, "SpellLevel", 60), (204495, "BaseLevel", 60), (204492, "SpellLevel", 50), (204492, "MaxLevel", 80),
        ])

    def test_bladestorm(self):
        self.fires(check_bladestorm, [
            (BLADESTORM, "EffectTriggerSpell_1", 50622), (BLADESTORM, "EffectAura_1", 4),
            (BLADESTORM, "EffectAuraPeriod_1", 2000), (BLADESTORM, "SpellClassMask_2", 0x4),
            (BLADESTORM, "DurationIndex", DUR["8s"]), (BLADESTORM, "EffectBasePoints_1", 0),
        ])

    def test_mortal_strike_and_rend(self):
        self.fires(check_mortal_strike_and_rend, [
            (MORTAL_STRIKE, "SpellClassMask_1", 0), (MORTAL_STRIKE, "SpellClassMask_3", 0),
            (MORTAL_STRIKE, "RecoveryTime", 5000), (MORTAL_STRIKE, "ManaCost", 300),
            (MORTAL_STRIKE, "EffectBasePoints_2", 159), (REND, "EquippedItemClass", -1),
            (REND, "EquippedItemSubclass", 0),
            (REND, "SpellClassMask_1", 0),
        ])

    def test_new_ids(self):
        self.assertEqual(check_new_ids(self.rows), [])
        for extra in (204545, 204546, 204629, 204800, 204869, 204899):
            self.assertGreaterEqual(len(check_new_ids({**self.rows, extra: {}})), 1, extra)
        for sid in S2_IDS:
            self.assertGreaterEqual(len(check_new_ids({k: v for k, v in self.rows.items() if k != sid})), 1, sid)

    def test_bindings(self):
        names, rem = self.d["names"], self.d["removals"]
        self.assertEqual(check_bindings(names, rem), [])
        for i, n in enumerate(names):
            if int(n["spell_id"]) in S2_BINDINGS:
                self.assertGreaterEqual(len(check_bindings(names[:i] + names[i + 1:], rem)), 1, n)
        for sid in (*S2_BINDINGS, *S2_UNSCRIPTED):
            extra = {"spell_id": sid, "ScriptName": "spell_warr_something_else"}
            self.assertGreaterEqual(len(check_bindings([*names, extra], rem)), 1, sid)
        for i in range(len(rem)):
            if (int(rem[i]["spell_id"]), rem[i]["ScriptName"]) in S2_UNBINDINGS:
                self.assertGreaterEqual(len(check_bindings(names, rem[:i] + rem[i + 1:])), 1, rem[i])
        for sid, name in S2_UNBINDINGS:
            self.assertGreaterEqual(len(check_bindings([*names, {"spell_id": sid, "ScriptName": name}], rem)), 1,
                                    (sid, name))
        for sid, name in S2_KEPT_BINDINGS:
            self.assertGreaterEqual(len(check_bindings(names, [*rem, {"spell_id": sid, "ScriptName": name}])), 1)

    def test_proc_rows(self):
        procs, rem = self.d["procs"], self.d["proc_removals"]
        self.assertEqual(check_proc_rows(procs, rem), [])
        for sid, cols in S2_PROC_ROWS.items():
            self.assertGreaterEqual(len(check_proc_rows([p for p in procs if int(p["SpellId"]) != sid], rem)), 1, sid)
            for col, val in cols.items():
                mutated = [{**p, col: float(val) + 1} if int(p["SpellId"]) == sid else p for p in procs]
                self.assertGreaterEqual(len(check_proc_rows(mutated, rem)), 1, (sid, col))
        for i, r in enumerate(rem):
            if int(r["SpellId"]) in S2_PROC_REMOVALS:
                self.assertGreaterEqual(len(check_proc_rows(procs, rem[:i] + rem[i + 1:])), 1, r)
        for sid in S2_PROC_REMOVALS:
            self.assertGreaterEqual(len(check_proc_rows([*procs, {"SpellId": sid, "SpellPhaseMask": 1}], rem)), 1, sid)
        for sid in S2_NO_PROC_ROW:
            self.assertGreaterEqual(len(check_proc_rows([*procs, {"SpellId": sid, "SpellPhaseMask": 1}], rem)), 1, sid)

    def test_spell_groups(self):
        groups = self.d["package"].spell_groups
        self.assertEqual(check_spell_groups(groups), [])
        for bad in ({"id": 1108, "spell_id": 30070}, {"id": 1305, "spell_id": 200065}, {"id": 1400, "spell_id": 204491},
                    {"id": 1108, "spell_id": 30069}):
            self.assertGreaterEqual(len(check_spell_groups([*groups, bad])), 1, bad)

    def test_slas(self):
        slas = self.d["package"].skill_line_abilities
        self.assertEqual(check_slas(slas), [])
        for sid in SLA_ROWS:
            self.assertGreaterEqual(len(check_slas([s for s in slas if int(s["id"]) != sid])), 1, sid)
            for col, val in (("skill_line", 256), ("class_mask", 2), ("spell_id", 78), ("acquire_method", 2)):
                bad = [{**s, col: val} if int(s["id"]) == sid else s for s in slas]
                self.assertGreaterEqual(len(check_slas(bad)), 1, (sid, col))
        reserved = {"id": 30868, "spell_id": 1, "skill_line": 26, "class_mask": 1}
        self.assertGreaterEqual(len(check_slas([*slas, reserved])), 1)

    def test_sdv(self):
        tv = self.d["tooltip_vars"]
        self.assertEqual(check_sdv(tv, self.rows), [])
        for vid, ranks in SDV_ROWS.items():
            self.assertGreaterEqual(len(check_sdv([t for t in tv if int(t["id"]) != vid], self.rows)), 1, vid)
            broken = [{**t, "Variables": t["Variables"].replace(f"${ranks[0]}m", "$99m")} if int(t["id"]) == vid else t
                      for t in tv]
            self.assertGreaterEqual(len(check_sdv(broken, self.rows)), 1, vid)
        for sid, token in SDV_READERS.items():
            text = self.rows[sid]["Description_Lang_enUS"].replace(token, "1")
            self.assertGreaterEqual(len(check_sdv(tv, _mut(self.rows, sid, Description_Lang_enUS=text))), 1, sid)

    def test_no_stray_dollar(self):
        self.assertEqual(check_no_stray_dollar(self.rows), [])
        for sid in (*S2_IDS, 12282, 12296, 12834, 46924, 204490, 204541):
            if sid not in self.rows:
                continue
            for col in ("Description_Lang_enUS", "AuraDescription_Lang_enUS"):
                if sid in S2_DOLLAR_EXEMPT and col == "Description_Lang_enUS":
                    continue
                self.assertGreaterEqual(len(check_no_stray_dollar(_mut(self.rows, sid, **{col: "reduces by $s1%"}))), 1,
                                        (sid, col))

    def test_tooltips(self):
        self.assertEqual(check_tooltips(self.rows), [])
        for sid, frags in TOOLTIP_FRAGMENTS.items():
            for frag in frags:
                text = self.rows[sid]["Description_Lang_enUS"].replace(frag, "X")
                self.assertGreaterEqual(len(check_tooltips(_mut(self.rows, sid, Description_Lang_enUS=text))), 1,
                                        (sid, frag))
        for sid, text in AURA_TEXTS.items():
            self.assertGreaterEqual(len(check_tooltips(_mut(self.rows, sid, AuraDescription_Lang_enUS=text + "!"))), 1,
                                    sid)

    def test_capstones(self):
        self.assertEqual(check_capstones(self.rows), [])
        for name, ranks in CAPSTONE_RANKS.items():
            grey, last = ranks[0], ranks[-1]
            clause_gone = self.rows[last]["Description_Lang_enUS"].split("\n\n")[0]
            self.assertGreaterEqual(len(check_capstones(_mut(self.rows, last, Description_Lang_enUS=clause_gone))), 1,
                                    name)
            if len(ranks) > 1:
                plain = self.rows[grey]["Description_Lang_enUS"].replace(capfmt.GREY, "")
                self.assertGreaterEqual(len(check_capstones(_mut(self.rows, grey, Description_Lang_enUS=plain))), 1,
                                        name)
            coloured = self.rows[last]["Description_Lang_enUS"].replace(
                "\n\nCapstone", f"\n\n{capfmt.GREY}Capstone") + capfmt.RESET
            self.assertGreaterEqual(len(check_capstones(_mut(self.rows, last, Description_Lang_enUS=coloured))), 1,
                                    name)
            in_aura = _mut(self.rows, grey, AuraDescription_Lang_enUS="Capstone Bonus: x")
            self.assertGreaterEqual(len(check_capstones(in_aura)), 1, name)
            self.assertGreaterEqual(len(check_capstones({k: v for k, v in self.rows.items() if k != last})), 1, name)
            self.assertGreaterEqual(len(check_capstones(_mut(self.rows, grey, Name_Lang_enUS="Not The Name"))), 1, name)


if __name__ == "__main__":
    unittest.main()
