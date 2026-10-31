"""
Warrior S3 (Fury) data gate (warrior-rework S3-HANDOFF WP-A row A4, S3-WP-BRIEF sections 2, 3, 3b, 6, 7).

Loads the real warrior DSL package (source/classes/warrior/) through the S1 / S2 / W0b loaders and asserts on the BUILT
rows (stock base + DSL + raw_overrides via `build.build_spell_row`, the way generate.py pairs them) for the Fury delta:
the 31-cell grid / 78 points and the seven retired talents, every rank row's effects and SpellMod masks per dword, the
carriers (value = bp + 1), the zeroed proc fields, the 51 new spell ids (durations by index, decoded attributes,
visible vs hidden helpers, custom attrs), the script / spell_proc / spell_group / SkillLineAbility bindings, the
const() rows, the SpellDescriptionVariables rows, the talent tooltips against docs/reworks/warrior-fury-rework.md and
the nine capstones. Every check is a pure function over built rows / package tables; the negative tests mutate a copy
of the real rows and prove each check can fail.

Reading rule for the masks (S1-0VERIFY top): EffectSpellClassMask{A,B,C}_{1,2,3}: the LETTER is the effect index
(A = effect 0, B = effect 1, C = effect 2), the NUMBER is the dword (1 = d0, 2 = d1, 3 = d2). Effects in the
comments below are 0-based ("e0"); the DBC columns and the entry keys (`effect1`..`effect3`) are 1-based.

Not driven here: the generated GCD-haste aura 201560 (lib/gcd_haste computes it; `generate.py --check --class warrior`
owns it).

Run: cd /home/plex/wow_server/azerothcore-wotlk && PYTHONDONTWRITEBYTECODE=1 apps/dbc-tools/.venv/bin/python3 \
     -m pytest apps/dbc-tools/lib/test_warrior_s3.py -q -p no:cacheprovider
"""

from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import test_capstone_format as capfmt  # noqa: E402
from lib import test_warrior_s1 as s1  # noqa: E402
from lib import test_warrior_s2 as s2  # noqa: E402
from lib.test_warrior_s1 import (  # noqa: E402
    _aura_effect, _data, _effect_empty, _emask, _hex3, _i, _missing, _mut, _u32,
)

TOOL_ROOT = Path(__file__).resolve().parents[1]

# effect types / auras
EFF_APPLY_AURA, EFF_DUMMY, EFF_SCHOOL_DAMAGE, EFF_HEAL, EFF_WEAPON_PERCENT = 6, 3, 2, 10, 31
EFF_ENERGIZE, EFF_TRIGGER_SPELL, EFF_WEAPON_DAMAGE_FLAT = 30, 64, 58
AURA_DUMMY, AURA_PROC_TRIGGER, AURA_CRIT_PCT_WEAPON, AURA_DMG_DONE_PCT = 4, 42, 52, 79
AURA_SPELLMOD_FLAT, AURA_SPELLMOD_PCT, AURA_MOD_SILENCE, AURA_MOD_STAT = 107, 108, 27, 29
AURA_HEAL_DONE_PCT, AURA_MOD_STAT_PCT, AURA_MELEE_HASTE, AURA_ARMOR_PER_AP = 136, 137, 138, 285
AURA_PERIODIC_DUMMY, AURA_DMG_TAKEN_PCT, AURA_HASTE_ALL, AURA_ARMOR_PEN = 226, 87, 193, 280
AURA_IGNORE_AURASTATE, AURA_CRIT_ALL = 262, 290
# spellmod ops (EffectMiscValue of aura 107 / 108)
OP_DAMAGE, OP_DURATION, OP_JUMP_TARGETS, OP_CRIT, OP_COOLDOWN, OP_COST = 0, 1, 17, 7, 11, 14

ATTR0_PASSIVE, ATTR0_DO_NOT_DISPLAY = 0x40, 0x80
ATTR3_SUPPRESS_CASTER_PROCS, ATTR3_ALLOW_AURA_WHILE_DEAD, ATTR3_REQUIRES_OFF_HAND_WEAPON = 0x10000, 0x100000, 0x1000000
ATTR4_SUPPRESS_WEAPON_PROCS = 0x800000
CU_AURA_CANNOT_BE_SAVED = 0x01000000
Z = (0, 0, 0)
NO_PROC = {"ProcTypeMask": 0, "ProcChance": 0}
PASSIVE_RANK = {"SpellClassSet": 4, "Attributes": 464, "EquippedItemClass": -1}

# durations by index (stock SpellDuration.dbc); S2's DUR_MS plus the three S3 adds
DUR = {**s2.DUR, "3s": 27, "5s": 28, "2s": 39}
DUR_MS = {**s2.DUR_MS, 27: 3000, 28: 5000, 39: 2000}

# ---- ids -----------------------------------------------------------------------------------------------------------
S3_FIRST, S3_LAST, S3_BLOCK_END = 204630, 204680, 204769
S3_IDS = tuple(range(S3_FIRST, S3_LAST + 1))
RAMPAGE, STRIKE_MH, STRIKE_OH, FB_HS, FB_CLEAVE = 204630, 204631, 204632, 204633, 204634
METER, ENRAGE, BLOOD_RUSH_BUFF, DEATHMAKER_BUFF = 204635, 204636, 204637, 204638
DOD_CRIT, DOD_HEAL, IE_STACK, CADENCE, WOTB_CRIT = 204639, 204640, 204641, 204642, 204643
SHRED_BUFFS = (204644, 204645, 204646)
MERCILESS_FREE, IR_SILENCE, FRESH_MEAT_CRIT, BC_HEAL, TG_PENALTY, BLOODSURGE_BUFF = (
    204647, 204648, 204649, 204650, 204651, 204652)
SNAPSHOT, IR_BLOODRAGE = 204679, 204680
BLOODTHIRST, BT_HEAL_BUFF, DEATH_WISH, RECKLESSNESS = 23881, 23885, 12292, 1719
BATTLE_SHOUT, COMMANDING_SHOUT, HEROIC_STRIKE, CLEAVE, SLAM, WHIRLWIND = 6673, 469, 78, 845, 1464, 1680
EXECUTE, PUMMEL = 5308, 6552
FLURRY_BUFFS = (12966, 12967, 12968)
IMPALE = (16493, 16494)

# ---- the grid ------------------------------------------------------------------------------------------------------
FURY_TAB, HOLDING_TAB = 164, 60800

# docs/reworks/warrior-fury-rework.md section 4: talent id -> ((tier, column), rank spells)
GRID = {
    2250: ((0, 0), (61216, 61221, 61222)),                    # Armored to the Teeth
    60465: ((0, 1), (204653, 204654, 204655)),                # Dance of Death (minted)
    157: ((0, 2), (12320, 12852, 12853)),                     # Cruelty (5 -> 3 ranks)
    60466: ((0, 3), (204656, 204657, 204658)),                # Merciless (minted)
    166: ((1, 0), (12329, 12950, 20496)),                     # Improved Cleave (moved)
    60467: ((1, 1), (204659, 204660)),                        # Frenzied Blows (minted)
    159: ((1, 2), (12322, 12999)),                            # Unbridled Wrath (5 -> 2)
    167: ((2, 1), (23881,)),                                  # Bloodthirst (moved)
    661: ((2, 2), (16487, 16489, 16492)),                     # Blood Craze
    154: ((2, 3), (12318, 12857)),                            # Commanding Presence (5 -> 2)
    1581: ((3, 0), (23584, 23585, 23586, 23587, 23588)),      # Dual Wield Specialization
    1542: ((3, 1), (20502, 20503)),                           # Improved Execute
    155: ((3, 2), (12317, 13045, 13046, 13047, 13048)),       # Enrage
    60468: ((4, 0), (204661, 204662, 204663)),                # Quick Execution (minted)
    165: ((4, 1), (12292,)),                                  # Death Wish
    60469: ((4, 2), (204664, 204665)),                        # Fresh Meat (minted)
    60470: ((5, 0), (204666, 204667)),                        # Improved Bloodthirst (minted)
    160: ((5, 1), (12323,)),                                  # Piercing Howl (moved)
    156: ((5, 2), (12319, 12971, 12972)),                     # Flurry
    1864: ((6, 0), (46908, 46909, 56924)),                    # Intensify Rage
    60471: ((6, 1), (204668, 204669, 204670)),                # Unshackled Fury (minted)
    1655: ((6, 3), (29721, 29776)),                           # Improved Whirlwind
    60472: ((7, 0), (204671, 204672)),                        # Deathmaker (minted)
    60473: ((7, 1), (204673, 204674, 204675)),                # Shredding Blows (minted)
    1658: ((7, 3), (29759, 29760, 29761, 29762, 29763)),      # Improved Berserker Stance
    60474: ((8, 0), (204676,)),                               # Will of the Berserker (minted)
    1659: ((8, 1), (RAMPAGE,)),                               # Rampage (castable 204630)
    1866: ((8, 2), (46913, 46914, 46915)),                    # Bloodsurge
    60475: ((9, 0), (204677, 204678)),                        # Blood Rush (minted)
    2234: ((9, 1), (56927, 56929, 56930)),                    # Unending Fury
    1867: ((10, 1), (46917,)),                                # Titan's Grip
}
MINTED = tuple(range(60465, 60476))
RETIRED = (158, 161, 1541, 1543, 1657, 1865, 1868)
FLAGGED = {167, 165, 160, 1659}            # Bloodthirst, Death Wish, Piercing Howl, Rampage keep Flags 1; the rest 0
GRID_POINTS = 78
GRID_ROW_POINTS = (12, 7, 6, 12, 6, 6, 8, 10, 5, 5, 1)       # doc section 4, tiers 0..10

# ---- the rank rows: (effect index, aura, misc, base points per rank (None = the effect is empty), mask) ------------
# SPECS[name] = (rank ids, effects, columns pinned on every rank, columns pinned per rank)
SPECS: dict[str, tuple] = {
    # D29 (pure data): Armored to the Teeth is checked by ROW_PINS (its e1 is a DUMMY effect, not an aura)
    "Cruelty": ((12320, 12852, 12853),
                [(0, AURA_CRIT_PCT_WEAPON, 0, (0, 1, 2), Z), (1, AURA_MOD_STAT_PCT, 0, (0, 1, 2), Z)],
                {"EquippedItemClass": -1, "EquippedItemSubclass": 0}, {}),
    "Improved Cleave": ((12329, 12950, 20496),
                        [(0, AURA_SPELLMOD_PCT, OP_DAMAGE, (4, 9, 14), (0x400000, 0, 0)),
                         (1, AURA_SPELLMOD_FLAT, OP_JUMP_TARGETS, (None, None, 0), (0x400000, 0, 0))],
                        {"SpellClassSet": 4}, {}),
    "Unbridled Wrath": ((12322, 12999), [(0, AURA_PROC_TRIGGER, 0, (-1, -1), Z)],
                        {"SpellClassSet": 0, "EquippedItemClass": -1, "EquippedItemSubclass": 0, "ProcTypeMask": 20,
                         "EffectTriggerSpell_1": 12964}, {"ProcChance": (15, 30)}),
    "Blood Craze": ((16487, 16489, 16492), [(0, AURA_DUMMY, 0, (4, 9, 14), Z)], {**NO_PROC, "EquippedItemClass": -1},
                    {}),
    "Improved Execute": ((20502, 20503), [(0, AURA_DUMMY, 0, (7, 15), Z)], {"SpellClassSet": 4}, {}),
    "Enrage": ((12317, 13045, 13046, 13047, 13048),
               [(0, AURA_DUMMY, 0, (1, 3, 5, 7, 9), Z), (1, AURA_DUMMY, 0, (1, 3, 5, 7, 9), Z)],
               {**NO_PROC, "EquippedItemClass": -1}, {}),
    "Flurry": ((12319, 12971, 12972), [(0, AURA_PROC_TRIGGER, 0, (0, 0, 0), Z)],
               {"ProcTypeMask": 20, "ProcChance": 100, "EquippedItemClass": -1},
               {"EffectTriggerSpell_1": FLURRY_BUFFS}),
    "Flurry buff": (FLURRY_BUFFS, [(0, AURA_MELEE_HASTE, 0, (7, 15, 24), Z)],
                    {"SpellClassSet": 4, "ProcCharges": 3, "ProcTypeMask": 4, "DurationIndex": DUR["15s"],
                     "EffectRealPointsPerLevel_1": 0, "MaxLevel": 0}, {}),
    "Commanding Presence": ((12318, 12857), [(0, AURA_DUMMY, 0, (0, 1), Z)], {"SpellClassSet": 4}, {}),
    "Improved Whirlwind": ((29721, 29776),
                           [(0, AURA_SPELLMOD_PCT, OP_DAMAGE, (2, 5), (0, 0x4, 0)),
                            (1, AURA_SPELLMOD_FLAT, OP_COOLDOWN, (-1001, -2001), (0, 0x4, 0))],
                           {"SpellClassSet": 4}, {}),
    "Intensify Rage": ((46908, 46909, 56924),
                       [(0, AURA_SPELLMOD_PCT, OP_COOLDOWN, (-12, -23, -34), (0x100010, 0, 0)),
                        (1, AURA_SPELLMOD_PCT, OP_COST, (-26, -51, -76), (0x100, 0, 0))],
                       {"SpellClassSet": 4}, {}),
    "Bloodsurge": ((46913, 46914, 46915), [(0, AURA_PROC_TRIGGER, 127, (-1, -1, -1), Z)],
                   {"SpellClassSet": 4, "ProcTypeMask": 16, "EffectTriggerSpell_1": BLOODSURGE_BUFF},
                   {"ProcChance": (10, 20, 30)}),
    "Unending Fury": ((56927, 56929, 56930),
                      [(0, AURA_SPELLMOD_PCT, OP_DAMAGE, (4, 9, 14), (0x600040, 0, 0)),
                       (1, AURA_SPELLMOD_PCT, OP_DAMAGE, (4, 9, 14), (0, 0x404, 0))],
                      {"SpellClassSet": 4}, {}),
    "Impale": (IMPALE, [(0, AURA_SPELLMOD_PCT, 15, (9, 19), (0x26604CEE, 0xC745, 0xF))], {"SpellClassSet": 4}, {}),
    # ---- the 11 minted talents' rank rows (passive talent shape: Attributes 464, set 4, class -1)
    "Dance of Death": ((204653, 204654, 204655), [(0, AURA_DUMMY, 0, (1, 3, 5), Z)],
                       {**PASSIVE_RANK, "ProcTypeMask": 2, "ProcChance": 100}, {}),
    "Merciless": ((204656, 204657, 204658), [(0, AURA_DUMMY, 0, (2, 5, 8), Z)], {**PASSIVE_RANK, **NO_PROC}, {}),
    "Frenzied Blows": ((204659, 204660), [(0, AURA_SPELLMOD_PCT, OP_DAMAGE, (4, 9), (0x400040, 0, 0))],
                       {**PASSIVE_RANK, **NO_PROC}, {}),
    "Quick Execution": ((204661, 204662, 204663),
                        [(0, AURA_HASTE_ALL, 0, (0, 1, 2), Z), (1, AURA_PROC_TRIGGER, 0, (None, None, 0), Z)],
                        PASSIVE_RANK, {"ProcTypeMask": (0, 0, 16), "ProcChance": (0, 0, 100),
                                       "EffectTriggerSpell_2": (0, 0, CADENCE)}),
    "Fresh Meat": ((204664, 204665), [(0, AURA_DUMMY, 0, (89, 79), Z)], {**PASSIVE_RANK, **NO_PROC}, {}),
    "Improved Bloodthirst": ((204666, 204667), [(0, AURA_DUMMY, 0, (2, 5), Z)], {**PASSIVE_RANK, **NO_PROC}, {}),
    "Unshackled Fury": ((204668, 204669, 204670), [(0, AURA_DUMMY, 0, (1, 3, 5), Z)], {**PASSIVE_RANK, **NO_PROC}, {}),
    "Deathmaker": ((204671, 204672), [(0, AURA_PROC_TRIGGER, 0, (0, 0), Z)],
                   {**PASSIVE_RANK, "ProcTypeMask": 20, "EffectTriggerSpell_1": DEATHMAKER_BUFF},
                   {"ProcChance": (3, 6)}),
    "Shredding Blows": ((204673, 204674, 204675), [(0, AURA_PROC_TRIGGER, 0, (0, 0, 0), Z)],
                        {**PASSIVE_RANK, "ProcTypeMask": 20, "ProcChance": 100},
                        {"EffectTriggerSpell_1": SHRED_BUFFS}),
    "Will of the Berserker": ((204676,), [(0, AURA_DUMMY, 0, (0,), Z)], {**PASSIVE_RANK, **NO_PROC}, {}),
    "Blood Rush": ((204677, 204678), [(0, AURA_PROC_TRIGGER, 0, (0, 0), Z)],
                   {**PASSIVE_RANK, "ProcTypeMask": 16, "EffectTriggerSpell_1": BLOOD_RUSH_BUFF},
                   {"ProcChance": (20, 40)}),
}
S3_RANK_IDS = tuple(sid for spec in SPECS.values() for sid in spec[0])
PROC_ZEROED_RANKS = (*SPECS["Enrage"][0], *SPECS["Blood Craze"][0], *SPECS["Improved Bloodthirst"][0],
                     *SPECS["Merciless"][0], *SPECS["Frenzied Blows"][0], *SPECS["Fresh Meat"][0],
                     *SPECS["Will of the Berserker"][0], 204661, 204662)

# column pins on rows that are not plain aura carriers (a non-aura effect, a second effect of another type)
ROW_PINS: dict[int, dict] = {
    # D29 Armored to the Teeth: aura 285 armor-per-AP amount 100 / 50 / (100 + 50), e1 DUMMY 0/1/2 (tooltip),
    # e2 only on rank 3
    61216: {"Effect_1": EFF_APPLY_AURA, "EffectAura_1": AURA_ARMOR_PER_AP, "EffectMiscValue_1": 1,
            "EffectBasePoints_1": 99, "Effect_2": EFF_DUMMY, "EffectBasePoints_2": 0, "Effect_3": 0},
    61221: {"Effect_1": EFF_APPLY_AURA, "EffectAura_1": AURA_ARMOR_PER_AP, "EffectMiscValue_1": 1,
            "EffectBasePoints_1": 49, "Effect_2": EFF_DUMMY, "EffectBasePoints_2": 1, "Effect_3": 0},
    61222: {"Effect_1": EFF_APPLY_AURA, "EffectAura_1": AURA_ARMOR_PER_AP, "EffectMiscValue_1": 1,
            "EffectBasePoints_1": 99, "Effect_2": EFF_DUMMY, "EffectBasePoints_2": 2, "Effect_3": EFF_APPLY_AURA,
            "EffectAura_3": AURA_ARMOR_PER_AP, "EffectMiscValue_3": 1, "EffectBasePoints_3": 49},
    # D20 Unbridled Wrath energize: 4 rage (tenths), the proc rank rows skip the weapon gate
    12964: {"Effect_1": EFF_ENERGIZE, "EffectMiscValue_1": 1, "EffectBasePoints_1": 39},
}

# ---- the new ids: exact column pins ---------------------------------------------------------------------------------
STRIKE_BASE = {"Attributes": 0x80, "AttributesEx3": ATTR3_SUPPRESS_CASTER_PROCS,
               "AttributesEx4": ATTR4_SUPPRESS_WEAPON_PROCS, "SpellClassSet": 4, "DefenseType": 2, "RangeIndex": 13,
               "EquippedItemClass": -1, "FacingCasterFlags": 0,
               "ManaCost": 0, "StartRecoveryTime": 0, "ImplicitTargetA_1": 6, "Effect_1": EFF_WEAPON_PERCENT,
               "EffectChainTargets_1": 0, "EffectChainTargets_2": 0}
OFFHAND_STRIKE = {"AttributesEx3": ATTR3_SUPPRESS_CASTER_PROCS | ATTR3_REQUIRES_OFF_HAND_WEAPON}


def _buff(name: str, dur: str, **pins) -> dict:
    return {"Name_Lang_enUS": name, "SpellClassSet": 4, "DurationIndex": DUR[dur], "EquippedItemClass": -1, **pins}


NEW_ROW_PINS: dict[int, dict] = {
    # D7 Rampage castable: GCD 133/1500, 50 rage (60 before the 2026-10-30 balance pass), 10 s, melee range, DUMMY on
    # the enemy (DmgClass 2), level 50, d2 b2
    RAMPAGE: {"Name_Lang_enUS": "Rampage", "Attributes": 0x50010, "AttributesEx": 0x8000200, "AttributesEx3": 0x400,
              "FacingCasterFlags": 1, "SpellClassSet": 4, "SpellClassMask_1": 0, "SpellClassMask_2": 0,
              "SpellClassMask_3": 0x4, "RecoveryTime": 10000, "StartRecoveryCategory": 133, "StartRecoveryTime": 1500,
              "ManaCost": 500, "PowerType": 1, "RangeIndex": 2, "SpellLevel": 50, "BaseLevel": 50, "DefenseType": 2,
              "Effect_1": EFF_DUMMY, "Effect_2": 0, "Effect_3": 0, "ImplicitTargetA_1": 6, "SpellIconID": 2006,
              "EquippedItemClass": 2, "EquippedItemSubclass": 173555},
    # strikes: d2 b2 only (never b3), 185% weapon [tune] (bp 184, balance 2026-10-30 x1.1 x1.1 x0.85), hidden,
    # triggered-only, suppress, 50000 yd, no facing
    STRIKE_MH: {**STRIKE_BASE, "Name_Lang_enUS": "Rampage", "SpellClassMask_1": 0, "SpellClassMask_2": 0,
                "SpellClassMask_3": 0x4, "EffectBasePoints_1": 184, "Effect_2": 0},
    STRIKE_OH: {**STRIKE_BASE, **OFFHAND_STRIKE, "Name_Lang_enUS": "Rampage", "SpellClassMask_1": 0,
                "SpellClassMask_2": 0, "SpellClassMask_3": 0x4, "EffectBasePoints_1": 184, "Effect_2": 0},
    # D19 Frenzied Blows strikes: copies of the Heroic Strike / Cleave damage rows, d0 b6 / b22 + d2 b3, chain 0
    FB_HS: {**STRIKE_BASE, **OFFHAND_STRIKE, "Name_Lang_enUS": "Frenzied Blows", "SpellClassMask_1": 0x40,
            "SpellClassMask_2": 0, "SpellClassMask_3": 0x8, "EffectBasePoints_1": 182,
            "Effect_2": EFF_WEAPON_DAMAGE_FLAT, "EffectBasePoints_2": -10},
    FB_CLEAVE: {**STRIKE_BASE, **OFFHAND_STRIKE, "Name_Lang_enUS": "Frenzied Blows", "SpellClassMask_1": 0x400000,
                "SpellClassMask_2": 0, "SpellClassMask_3": 0x8, "EffectBasePoints_1": 143,
                "Effect_2": EFF_WEAPON_DAMAGE_FLAT, "EffectBasePoints_2": -1},
    # D3 the meter: visible DUMMY, 20 stacks (user 2026-10-30, was 19), permanent, survives death
    METER: _buff("Rage Meter", "inf", Attributes=0, AttributesEx3=ATTR3_ALLOW_AURA_WHILE_DEAD, CumulativeAura=20,
                 Effect_1=EFF_APPLY_AURA, EffectAura_1=AURA_DUMMY, Effect_2=0, ProcTypeMask=0),
    # D4 Enrage: no dispel / mechanic, 12 s, e0 79 physical, e1 138 attack speed (never 193), e2 the 1 s Mastery poll
    ENRAGE: _buff("Enrage", "12s", Attributes=0, DispelType=0, Mechanic=0, ProcTypeMask=0, Effect_1=EFF_APPLY_AURA,
                  EffectAura_1=AURA_DMG_DONE_PCT, EffectMiscValue_1=1, Effect_2=EFF_APPLY_AURA,
                  EffectAura_2=AURA_MELEE_HASTE, Effect_3=EFF_APPLY_AURA, EffectAura_3=AURA_PERIODIC_DUMMY,
                  EffectAuraPeriod_3=1000),
    # D14 Blood Rush: next Rampage free (-100% cost on d2 0x4), one charge, 5 s, no spell_proc
    BLOOD_RUSH_BUFF: _buff("Blood Rush", "5s", Attributes=0, ProcCharges=1, ProcTypeMask=0, Effect_1=EFF_APPLY_AURA,
                           EffectAura_1=AURA_SPELLMOD_PCT, EffectMiscValue_1=OP_COST, EffectBasePoints_1=-101,
                           EffectSpellClassMaskA_1=0, EffectSpellClassMaskA_2=0, EffectSpellClassMaskA_3=0x4),
    # D16 Deathmaker: aura 262 on Execute's d0 0x20000000, 10 s, no charges, no spell_proc, set 4 (load-bearing)
    DEATHMAKER_BUFF: _buff("Deathmaker", "10s", Attributes=0, ProcCharges=0, ProcTypeMask=0, Effect_1=EFF_APPLY_AURA,
                           EffectAura_1=AURA_IGNORE_AURASTATE, EffectSpellClassMaskA_1=0x20000000,
                           EffectSpellClassMaskA_2=0, EffectSpellClassMaskA_3=0),
    # D26 Dance of Death: the crit buff (8 s, aura 290) and the hidden heal
    DOD_CRIT: _buff("Dance of Death", "8s", Attributes=0, Effect_1=EFF_APPLY_AURA, EffectAura_1=AURA_CRIT_ALL),
    DOD_HEAL: _buff("Dance of Death", "inf", Attributes=0x80, Effect_1=EFF_HEAL, Effect_2=0),
    # D17 Improved Execute capstone stack: +10 crit per stack, 3 stacks, 5 s
    IE_STACK: _buff("Improved Execute", "5s", Attributes=0, CumulativeAura=3, ProcTypeMask=0, Effect_1=EFF_APPLY_AURA,
                    EffectAura_1=AURA_CRIT_PCT_WEAPON, EffectBasePoints_1=9),
    # D13 Cadence: +1% haste (193) per stack, 3 stacks, 12 s
    CADENCE: _buff("Cadence", "12s", Attributes=0, CumulativeAura=3, Effect_1=EFF_APPLY_AURA,
                   EffectAura_1=AURA_HASTE_ALL, EffectBasePoints_1=0),
    # D24 Will of the Berserker: +10 crit (all), 12 s
    WOTB_CRIT: _buff("Will of the Berserker", "12s", Attributes=0, Effect_1=EFF_APPLY_AURA, EffectAura_1=AURA_CRIT_ALL,
                     EffectBasePoints_1=9),
    # D27 Shredding Blows buffs: aura 280 bp 3/7/11 read on the sentinel d2 0x100, 3 charges, 15 s, ProcTypeMask 4
    **{sid: _buff("Shredding Blows", "15s", Attributes=0, ProcCharges=3, ProcTypeMask=4, Effect_1=EFF_APPLY_AURA,
                  EffectAura_1=AURA_ARMOR_PEN, EffectMiscValue_1=0, EffectBasePoints_1=bp, EffectSpellClassMaskA_1=0,
                  EffectSpellClassMaskA_2=0, EffectSpellClassMaskA_3=0x100)
       for sid, bp in zip(SHRED_BUFFS, (3, 7, 11))},
    # D18 Merciless capstone: permanent hidden -100% cost on Rampage, no charges
    MERCILESS_FREE: _buff("Merciless", "inf", Attributes=0x80, ProcCharges=0, ProcTypeMask=0, Effect_1=EFF_APPLY_AURA,
                          EffectAura_1=AURA_SPELLMOD_PCT, EffectMiscValue_1=OP_COST, EffectBasePoints_1=-101,
                          EffectSpellClassMaskA_1=0, EffectSpellClassMaskA_2=0, EffectSpellClassMaskA_3=0x4),
    # D25 Intensify Rage capstone silence: 3 s, Mechanic 9, aura 27, a ranged debuff on the target
    IR_SILENCE: {"Name_Lang_enUS": "Intensify Rage", "SpellClassSet": 4, "Mechanic": 9, "EffectMechanic_1": 9,
                 "DurationIndex": DUR["3s"], "RangeIndex": 13, "Effect_1": EFF_APPLY_AURA,
                 "EffectAura_1": AURA_MOD_SILENCE, "ImplicitTargetA_1": 6, "EquippedItemClass": -1, "Attributes": 0},
    # D10 Fresh Meat crit: hidden, one charge, no spell_proc, +100 flat crit on Bloodthirst (d1 0x400)
    FRESH_MEAT_CRIT: _buff("Fresh Meat", "3s", Attributes=0x80, ProcCharges=1, ProcTypeMask=0, Effect_1=EFF_APPLY_AURA,
                           EffectAura_1=AURA_SPELLMOD_FLAT, EffectMiscValue_1=OP_CRIT, EffectBasePoints_1=99,
                           EffectSpellClassMaskA_1=0, EffectSpellClassMaskA_2=0x400, EffectSpellClassMaskA_3=0),
    # D11 Blood Craze heal: hidden instant HEAL that Titan's Grip's -10% healing reaches (no IGNORE_CASTER_MODIFIERS)
    BC_HEAL: _buff("Blood Craze", "inf", Attributes=0x80, AttributesEx3=0, Effect_1=EFF_HEAL, Effect_2=0),
    # D31 Titan's Grip: visible all-damage / all-healing -10% (final bp -11), not passive, class -1
    TG_PENALTY: _buff("Titan's Grip", "inf", Attributes=0, Effect_1=EFF_APPLY_AURA, EffectAura_1=AURA_DMG_DONE_PCT,
                      EffectMiscValue_1=127, EffectBasePoints_1=-11, Effect_2=EFF_APPLY_AURA,
                      EffectAura_2=AURA_HEAL_DONE_PCT, EffectBasePoints_2=-11, Effect_3=0),
    # D15 Bloodsurge buff: next Slam | Cleave free (e0 d0 0x600000) and +20% damage (e1), 15 s, one charge,
    # no spell_proc
    BLOODSURGE_BUFF: _buff("Bloodsurge", "15s", Attributes=0, ProcCharges=1, ProcTypeMask=0, Effect_1=EFF_APPLY_AURA,
                           EffectAura_1=AURA_SPELLMOD_PCT, EffectMiscValue_1=OP_COST, EffectBasePoints_1=-101,
                           EffectSpellClassMaskA_1=0x600000, Effect_2=EFF_APPLY_AURA, EffectAura_2=AURA_SPELLMOD_PCT,
                           EffectMiscValue_2=OP_DAMAGE, EffectBasePoints_2=19, EffectSpellClassMaskB_1=0x600000),
    # D7 the press snapshot: +100 flat crit on d2 b2 only (the four strikes), no charges, 2 s, hidden
    SNAPSHOT: _buff("Rampage", "2s", Attributes=0x80, ProcCharges=0, ProcTypeMask=0, Effect_1=EFF_APPLY_AURA,
                    EffectAura_1=AURA_SPELLMOD_FLAT, EffectMiscValue_1=OP_CRIT, EffectBasePoints_1=99,
                    EffectSpellClassMaskA_1=0, EffectSpellClassMaskA_2=0, EffectSpellClassMaskA_3=0x4),
    # D25 the Bloodrage copy: hidden ENERGIZE 20 rage (tenths) + TRIGGER the 10 s regen, no cost, no cooldown
    IR_BLOODRAGE: _buff("Bloodrage", "inf", Attributes=0x80, ManaCost=0, RecoveryTime=0, Effect_1=EFF_ENERGIZE,
                        EffectMiscValue_1=1, EffectBasePoints_1=199, Effect_2=EFF_TRIGGER_SPELL,
                        EffectTriggerSpell_2=29131),
    # D9 Bloodthirst's next-hit heal buff (first-declared stock row): one charge (was 3), 8 s, trigger 23880
    BT_HEAL_BUFF: {"Name_Lang_enUS": "Bloodthirst", "ProcCharges": 1, "DurationIndex": DUR["8s"], "ProcTypeMask": 20,
                   "Effect_1": EFF_APPLY_AURA, "EffectAura_1": AURA_PROC_TRIGGER, "EffectTriggerSpell_1": 23880,
                   "EquippedItemClass": -1},
}
# D38: the visible list carries neither PASSIVE 0x40 nor DO_NOT_DISPLAY 0x80; the hidden list hides
VISIBLE_IDS = (RAMPAGE, METER, ENRAGE, BLOOD_RUSH_BUFF, DEATHMAKER_BUFF, DOD_CRIT, IE_STACK, CADENCE, WOTB_CRIT,
               *SHRED_BUFFS, IR_SILENCE, TG_PENALTY, BLOODSURGE_BUFF, BT_HEAL_BUFF)
HIDDEN_IDS = (STRIKE_MH, STRIKE_OH, FB_HS, FB_CLEAVE, DOD_HEAL, MERCILESS_FREE, FRESH_MEAT_CRIT, BC_HEAL, SNAPSHOT,
              IR_BLOODRAGE)
MELEE_DMGCLASS_IDS = (RAMPAGE, STRIKE_MH, STRIKE_OH, FB_HS, FB_CLEAVE)      # DmgClass 2: a landed strike can crit
OH_WEAPON_IDS = (STRIKE_OH, FB_HS, FB_CLEAVE)                                # REQUIRES_OFF_HAND_WEAPON
STRIKE_IDS = (STRIKE_MH, STRIKE_OH, FB_HS, FB_CLEAVE)
# Frenzied Blows' strikes copy the damage rows of the parent (same weapon percent and flat part)
STRIKE_PARENTS = {FB_HS: HEROIC_STRIKE, FB_CLEAVE: CLEAVE}
# custom attrs: CU_AURA_CANNOT_BE_SAVED on the meter and the Titan's Grip penalty only (reset on login)
CUSTOM_ATTR_IDS = {METER: CU_AURA_CANNOT_BE_SAVED, TG_PENALTY: CU_AURA_CANNOT_BE_SAVED}
# consuming rows / helpers that must carry no spell_proc row at all (ProcTypeMask 0 charged buffs, plain auras)
NO_PROC_ROW_IDS = (STRIKE_MH, STRIKE_OH, FB_HS, FB_CLEAVE, METER, ENRAGE, BLOOD_RUSH_BUFF, DEATHMAKER_BUFF, DOD_CRIT,
                   DOD_HEAL, IE_STACK, CADENCE, WOTB_CRIT, MERCILESS_FREE, IR_SILENCE, FRESH_MEAT_CRIT, BC_HEAL,
                   TG_PENALTY, BLOODSURGE_BUFF, SNAPSHOT, IR_BLOODRAGE, RAMPAGE, RECKLESSNESS,
                   *PROC_ZEROED_RANKS, -12317, -16487)

SPELL_LEVELS = {BLOODTHIRST: 20, RAMPAGE: 50}

# aura texts of the visible buffs ("Shows a buff" lines of docs/reworks/warrior-fury-rework.md)
AURA_TEXTS = {
    METER: "Spending rage builds toward Enrage.",
    ENRAGE: "Your physical damage and attack speed are increased.",
    BLOOD_RUSH_BUFF: "Your next Rampage costs no rage.",
    DEATHMAKER_BUFF: "Execute is usable on any target.",
    DOD_CRIT: "Critical strike chance increased.",
    IE_STACK: "Critical strike chance increased.",
    CADENCE: "Haste increased.",
    WOTB_CRIT: "Critical strike chance increased.",
    **{sid: "Your attacks ignore some of the target's armor." for sid in SHRED_BUFFS},
    IR_SILENCE: "Silenced.",
    TG_PENALTY: "Your damage and healing are reduced.",
    BLOODSURGE_BUFF: "Your next Slam or Cleave costs no rage and deals more damage.",
    BT_HEAL_BUFF: "Your next melee attack restores health.",
    DEATH_WISH: "Your Enrage is stronger and will not fade. You take more damage.",
    FLURRY_BUFFS[0]: "Attack speed increased.",
}
# the doc's Flurry aura text ("Attack speed increased.", doc line "Shows a buff") on the other two ranks: A2b pasted the
# stock "Attack speed increased by $s1%." (D36 says aura texts come from the doc). Pinned as an expected failure so the
# discrepancy stays visible; remove the decorator when the rows are fixed.
FLURRY_AURA_TEXT = "Attack speed increased."
# the shouts' aura text gains one clause each (doc: "Strength increased." / "Stamina increased.")
SHOUT_AURA_CLAUSES = {BATTLE_SHOUT: "Strength increased.", COMMANDING_SHOUT: "Stamina increased."}

# ---- script / proc / group bindings (brief section 2) ---------------------------------------------------------------
S3_BINDINGS = {
    BLOODTHIRST: {"spell_warr_bloodthirst_fury"}, -EXECUTE: {"spell_warr_execute_fury"},
    RAMPAGE: {"spell_warr_rampage_fury"}, ENRAGE: {"spell_warr_enrage_fury"},
    DEATH_WISH: {"spell_warr_death_wish_fury"}, RECKLESSNESS: {"spell_warr_recklessness_fury"},
    HEROIC_STRIKE: {"spell_warr_hs_cleave_fury"}, CLEAVE: {"spell_warr_hs_cleave_fury"},
    49152: {"spell_warr_titans_grip_hardcode"}, -204524: {"spell_warr_two_handed_weapon_mastery_gate"},
    PUMMEL: {"spell_warr_pummel_fury"}, -204653: {"spell_warr_dance_of_death"},
    BATTLE_SHOUT: {"spell_warr_commanding_presence"}, COMMANDING_SHOUT: {"spell_warr_commanding_presence"},
    -204671: {"spell_warr_deathmaker"},
}
S3_UNBINDINGS = {(BLOODTHIRST, "spell_warr_bloodthirst"), (-EXECUTE, "spell_warr_execute"),
                 (-46913, "spell_warr_extra_proc"), (-12317, "spell_gen_proc_from_direct_damage")}
# the scripted ids S3 declares exactly 15 times; every other S3 helper (strikes, buffs, ranks) carries no script
S3_UNSCRIPTED = (STRIKE_MH, STRIKE_OH, FB_HS, FB_CLEAVE, METER, BLOOD_RUSH_BUFF, DEATHMAKER_BUFF, DOD_CRIT, DOD_HEAL,
                 IE_STACK, CADENCE, WOTB_CRIT, *SHRED_BUFFS, MERCILESS_FREE, IR_SILENCE, FRESH_MEAT_CRIT, BC_HEAL,
                 TG_PENALTY, BLOODSURGE_BUFF, SNAPSHOT, IR_BLOODRAGE, BT_HEAL_BUFF)

# spell_proc rows: id -> {column: value}
S3_PROC_ROWS = {
    -46913: {"SpellFamilyName": 4, "SpellFamilyMask0": 0, "SpellFamilyMask1": 0x404, "ProcFlags": 0x10,
             "SpellPhaseMask": 1},                                                   # D15 Bloodthirst | Whirlwind
    -46867: {"ProcFlags": 0x400010, "SpellTypeMask": 1, "SpellPhaseMask": 2, "HitMask": 2},   # D33 Wrecking Crew
    BT_HEAL_BUFF: {"ProcFlags": 0x14, "SpellTypeMask": 1, "SpellPhaseMask": 2},      # D9 damaging hit only
    -204671: {"SpellFamilyName": 4, "SpellFamilyMask0": 0, "ProcFlags": 0x14, "SpellPhaseMask": 1},   # D16 Deathmaker
    -204653: {"ProcFlags": 0x2, "AttributesMask": 0x1},                              # D26 kill (REQ_EXP_OR_HONOR)
    12322: {"SpellFamilyName": 4, "SpellFamilyMask0": 0x400040, "ProcFlags": 0x14, "SpellPhaseMask": 1,
            "Chance": 15.0},                                                         # D20 Unbridled Wrath
    12999: {"SpellFamilyName": 4, "SpellFamilyMask0": 0x400040, "ProcFlags": 0x14, "SpellPhaseMask": 1,
            "Chance": 30.0},
    204663: {"SpellFamilyName": 4, "SpellFamilyMask1": 0x400, "ProcFlags": 0x10, "SpellPhaseMask": 2},   # D13 Cadence
    # D14 Blood Rush: once per Bloodthirst cast
    204677: {"SpellFamilyName": 4, "SpellFamilyMask1": 0x400, "ProcFlags": 0x10, "SpellPhaseMask": 1},
    204678: {"SpellFamilyName": 4, "SpellFamilyMask1": 0x400, "ProcFlags": 0x10, "SpellPhaseMask": 1},
    # D27 Shredding Blows: the grant (any melee crit) ...
    **{sid: {"ProcFlags": 0x14, "SpellTypeMask": 1, "SpellPhaseMask": 2, "HitMask": 2}
       for sid in (204673, 204674, 204675)},
    # ... and the EXPLICIT consuming row on each buff: flags 0x4 only (any phase / type field without a spell flag is a
    # boot ERROR, 0-verify B difference 7)
    **{sid: {"ProcFlags": 0x4, "SpellTypeMask": 0, "SpellPhaseMask": 0, "HitMask": 0} for sid in SHRED_BUFFS},
}
S3_PROC_REMOVALS = {-12317, -16487, -20500, 46910, 46911, 13000, 13001, 13002, RECKLESSNESS}

# SpellDescriptionVariables (D37): id -> rank spells it reads; spell -> (the token its description reads, SDV id)
SDV_ROWS = {1405: (12282, 12663, 12664, 204659, 204660, 56927, 56929, 56930),
            1406: (12282, 12663, 12664, 56927, 56929, 56930),
            1407: (12329, 12950, 20496, 204659, 204660, 56927, 56929, 56930),
            1408: (56927, 56929, 56930),
            1409: (29721, 29776, 56927, 56929, 56930)}
SDV_READERS = {HEROIC_STRIKE: ("$<mult>", 1405), SLAM: ("$<mult>", 1406), CLEAVE: ("$<mult>", 1407),
               BLOODTHIRST: ("$<uf>", 1408), WHIRLWIND: ("$<mult>", 1409)}
SDV_KEPT = (1385,)

# const() rows (brief section 2): name -> (value, cpp type)
CONSTS = {
    "ENRAGE_METER_FILL": (200, "int32"), "ENRAGE_METER_STACK": (10, "int32"),
    "COMMANDING_PRESENCE_AT_60": (30, "int32"), "RAMPAGE_STRIKE_2_MS": (330, "uint32"),
    "RAMPAGE_STRIKE_3_MS": (660, "uint32"), "RAMPAGE_STRIKE_4_MS": (1000, "uint32"),
    "WILL_OF_THE_BERSERKER_CDR_MS": (2000, "uint32"), "DANCE_OF_DEATH_HEAL_ICD_MS": (5000, "uint32"),
    "BLOODTHIRST_RAGE": (10, "int32"), "BLOODTHIRST_BLEED_BONUS_PCT": (8, "int32"),
    "BLOODTHIRST_BLEED_BONUS_MAX_PCT": (40, "int32"), "MERCILESS_HEALTH_PCT": (35, "int32"),
    "IMPROVED_EXECUTE_HEALTH_PCT": (20, "int32"), "UNENDING_FURY_WHIRLWIND_CUT_MS": (1500, "uint32"),
}

# docs/reworks/warrior-fury-rework.md "Tooltip" lines: sid -> fragments the built description must contain
TOOLTIP_FRAGMENTS = {
    61216: ("attack power by 1 for every 100 armor",), 61221: ("by 2 for every 100 armor",),
    61222: ("by 3 for every 100 armor",),
    204653: ("critical strike chance is increased by 2% for 8 sec", "resets the cooldown of your Charge",
             "once every 5 sec"),
    204654: ("increased by 4% for 8 sec",), 204655: ("increased by 6% for 8 sec",),
    12320: ("critical strike chance by 1%", "total Strength by 1%"), 12852: ("by 2%", "Strength by 2%"),
    12853: ("by 3%", "Strength by 3%"),
    204656: ("Berserker Stance", "below 35% health is increased by 3%", "doubled while you are Enraged",
             "While Recklessness is active, Rampage costs no rage"),
    204657: ("increased by 6%",), 204658: ("increased by 9%",),
    12329: ("damage done by your Cleave ability by 5%", "Your Cleave strikes 1 additional target"),
    12950: ("Cleave ability by 10%",), 20496: ("Cleave ability by 15%",),
    204659: ("damage of your Heroic Strike and Cleave by 5%",
             "While you are Enraged, your Heroic Strike and Cleave also strike with your off-hand weapon"),
    204660: ("Heroic Strike and Cleave by 10%",),
    12322: ("auto attacks, Heroic Strike and Cleave have a 15% chance to generate 4 additional rage",),
    12999: ("30% chance to generate 4 additional rage",),
    16487: ("heals you for 0.5% of your maximum health", "doubled while you are Enraged"),
    16489: ("for 1% of your maximum health",), 16492: ("for 1.5% of your maximum health",),
    12318: ("Battle Shout also increases Strength", "Commanding Shout also increases Stamina",
            "Rank 1 gives half the bonus"),
    12857: ("Rank 1 gives half the bonus",),
    20502: ("damage of your Execute ability by 8%", "doubled against targets below 20% health",
            "increases your melee critical strike chance by 10% for 5 sec, stacking up to 3 times"),
    20503: ("Execute ability by 16%",),
    12317: ("Every 200 rage you spend Enrages you", "physical damage by 2%", "melee haste by 2%", "for 12 sec",
            "Recklessness also Enrages you"),
    13045: ("physical damage by 4%", "melee haste by 4%"), 13046: ("by 6%", "haste by 6%"),
    13047: ("by 8%", "haste by 8%"), 13048: ("by 10%", "haste by 10%"),
    204661: ("Increases your haste by 1%",), 204662: ("haste by 2%",),
    204663: ("haste by 3%", "Your Bloodthirst grants Cadence", "haste by 1% for 12 sec", "stacking up to 3 times"),
    204664: ("Bloodthirst always critically strikes targets above 90% health",),
    204665: ("above 80% health",),
    204666: ("Bloodthirst generates 3 additional rage",), 204667: ("generates 6 additional rage",),
    12319: ("attack speed by $12966s1%", "next 3 swings after dealing a melee critical strike"),
    12971: ("$12967s1%",), 12972: ("$12968s1%",),
    46908: ("cooldown of your Recklessness and Death Wish abilities by 11%", "health cost of your Bloodrage by 25%",
            "successful interrupts with Pummel silence the target for 3 sec"),
    46909: ("by 22%", "Bloodrage by 50%"), 56924: ("by 33%", "Bloodrage by 75%"),
    204668: ("physical damage bonus of your Enrage by 2%", "Mastery further increases"),
    204669: ("Enrage by 4%",), 204670: ("Enrage by 6%",),
    29721: ("damage of your Whirlwind ability by 3%", "reduces its cooldown by 1 sec"),
    29776: ("Whirlwind ability by 6%", "cooldown by 2 sec"),
    204671: ("melee hits have a 3% chance to make your next Execute usable regardless of the target's health",
             "Lasts 10 sec"),
    204672: ("6% chance",),
    204673: ("critical strike, your next 3 swings ignore 4% of the target's armor",),
    204674: ("ignore 8% of the target's armor",), 204675: ("ignore 12% of the target's armor",),
    204676: ("Each Rampage reduces the remaining cooldown of Recklessness by 2 sec",
             "critical strike chance is increased by 10% for 12 sec"),
    204677: ("After you use Bloodthirst, your next Rampage within 5 sec has a 20% chance to cost no rage",),
    204678: ("has a 40% chance to cost no rage",),
    46913: ("Your Bloodthirst and Whirlwind hits have a 10% chance",
            "next Slam or Cleave cost no rage and deal 20% more damage"),
    46914: ("20% chance",), 46915: ("30% chance",),
    56927: ("damage done by your Bloodthirst, Whirlwind, Slam, Heroic Strike and Cleave by 5%",
            "Each Cleave reduces the remaining cooldown of your Whirlwind by 1.5 sec"),
    56929: ("Cleave by 10%",), 56930: ("Cleave by 15%",),
    RAMPAGE: ("Strike the target 4 times", "alternating main hand and off hand", "185% weapon damage",
              "increased by your Enrage bonus a second time"),
    BLOODTHIRST: ("generating 10 rage",
                  "Each bleed applied by you increases the damage of Bloodthirst by 8%, up to 40%",
                  "next successful melee attack restores $m2% of your maximum health"),
    DEATH_WISH: ("Enrages you", "physical damage bonus of your Enrage by 50%", "Your Enrage cannot expire while Death "
                 "Wish is active", "take $s3% more damage"),
    BT_HEAL_BUFF: ("next melee attack restores health", "Lasts 8 sec"),
    DOD_CRIT: ("Critical strike chance increased",), METER: ("Spending rage builds toward Enrage",),
    BLOOD_RUSH_BUFF: ("Your next Rampage costs no rage",), BLOODSURGE_BUFF: ("Your next Slam or Cleave costs no rage",),
    TG_PENALTY: ("Your damage and healing are reduced",),
}
# the nine capstones (D36): name -> rank spells
CAPSTONE_RANKS = {
    "Dance of Death": (204653, 204654, 204655), "Merciless": (204656, 204657, 204658),
    "Improved Cleave": (12329, 12950, 20496), "Frenzied Blows": (204659, 204660),
    "Improved Execute": (20502, 20503), "Quick Execution": (204661, 204662, 204663),
    "Intensify Rage": (46908, 46909, 56924), "Unshackled Fury": (204668, 204669, 204670),
    "Unending Fury": (56927, 56929, 56930),
}
# Description may keep a '$' only where the doc's tooltip reads a stock variable or the pot_text() expansion
# (Dance of Death's heal clause: $max / $AP / $PL, A2b report); the S3 aura texts allow nothing beyond $sN
S3_DOLLAR_EXEMPT = {204653, 204654, 204655, 12319, 12971, 12972, 12967, 12968}   # + stock Flurry buff text ($<id>s1)
S3_DOLLAR_SCAN = tuple(sorted({*S3_IDS, *S3_RANK_IDS, 61216, 61221, 61222} | set(AURA_TEXTS)))
POT_TEXT_TOKENS = re.compile(r"\$(max|AP|PL|SP)\b|\$\{")


# ---- checks (pure: take built rows / package tables, return problem strings) ------------------------------------

def check_grid(talents: list[dict]) -> list[str]:
    bad = []
    fury = {int(t["id"]): t for t in talents if int(t["tab_id"]) == FURY_TAB}
    if sorted(fury) != sorted(GRID):
        bad.append(f"Fury tab talents {sorted(fury)}, expected exactly the {len(GRID)} doc talents {sorted(GRID)}")
    seen: dict[tuple[int, int], int] = {}
    points = 0
    for tid, (cell, ranks) in sorted(GRID.items()):
        t = fury.get(tid)
        if t is None:
            bad.append(f"talent {tid}: not in the Fury tab")
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
    for tid, t in sorted(fury.items()):
        cell = (int(t["tier"]), int(t["column"]))
        if cell in seen:
            bad.append(f"talents {seen[cell]} and {tid} share the cell {cell}")
        seen[cell] = tid
        if not (0 <= cell[0] <= 10 and 0 <= cell[1] <= 3):
            bad.append(f"talent {tid}: cell {cell} is off the grid")
    if len(fury) != 31:
        bad.append(f"the Fury tab holds {len(fury)} talents, expected 31")
    if points != GRID_POINTS:
        bad.append(f"the grid carries {points} points, expected {GRID_POINTS}")
    for tier, want in enumerate(GRID_ROW_POINTS):
        got = sum(len(t["rank_spell_ids"]) for t in fury.values() if int(t["tier"]) == tier)
        if got != want:
            bad.append(f"tier {tier} carries {got} points, expected {want}")
    minted = sorted(tid for tid in fury if 60465 <= tid <= 60479)
    if minted != list(MINTED):
        bad.append(f"minted talents {minted}, expected {list(MINTED)}")
    holding = {int(t["id"]): t for t in talents if int(t["tab_id"]) == HOLDING_TAB}
    for tid in RETIRED:
        t = holding.get(tid)
        if t is None:
            bad.append(f"talent {tid}: not retired to the holding tab {HOLDING_TAB}")
        elif t["rank_spell_ids"]:
            bad.append(f"talent {tid}: retired but still lists ranks {t['rank_spell_ids']}")
        if tid in fury:
            bad.append(f"talent {tid}: retired but still in the Fury tab")
    return bad


def check_tab_skill_line(slas: list[dict], tabs: list[dict]) -> list[str]:
    """The Fury tab declares skill_line 256 (not a TalentTab column): it derives Rampage's SkillLineAbility 30855."""
    bad = []
    if 164 not in {int(t["id"]) for t in tabs}:
        bad.append("the Fury tab 164 is not declared")
    row = next((s for s in slas if int(s["id"]) == 30855), None)
    if row is None:
        return bad + ["SkillLineAbility 30855 is not declared"]
    got = (int(row["spell_id"]), int(row["skill_line"]), int(row.get("class_mask") or 0),
           int(row.get("race_mask") or 0))
    if got != (RAMPAGE, 256, 1, 0):
        bad.append(f"SkillLineAbility 30855: (spell, skill line, class mask, race mask) {got}, expected "
                   f"{(RAMPAGE, 256, 1, 0)}")
    if [s for s in slas if int(s["id"]) in (30868, 30869)]:
        bad.append("SkillLineAbility ids 30868 / 30869 are reserved")
    return bad


def check_rank_specs(rows: dict, specs: dict | None = None) -> list[str]:
    """Every rank row: its effects (aura, misc, base points per rank, the mask on the effect's own letter), the columns
    pinned on every rank / per rank, and the empty slots (stale residue cleared)."""
    bad = []
    for name, (ids, effects, cols, rank_cols) in (specs or SPECS).items():
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
            for idx in sorted({0, 1, 2} - {e[0] for e in effects}):
                bad += _effect_empty(r, idx, sid, name)
            for col, val in cols.items():
                if _u32(r.get(col)) != _u32(val):
                    bad.append(f"{sid}: {name} {col} {r.get(col)!r}, expected {val!r}")
            for col, vals in rank_cols.items():
                want = vals[rank] if isinstance(vals, (tuple, list)) else vals
                if _u32(r.get(col)) != _u32(want):
                    bad.append(f"{sid}: {name} {col} {r.get(col)!r}, expected {want!r}")
    return bad


def check_pins(rows: dict, pins: dict) -> list[str]:
    bad = _missing(rows, *pins)
    for sid, cols in pins.items():
        r = rows.get(sid)
        if r is None:
            continue
        for col, val in cols.items():
            got = r.get(col)
            if isinstance(val, str):
                if got != val:
                    bad.append(f"{sid}: {col} {got!r}, expected {val!r}")
            elif _u32(got) != _u32(val):
                hexy = col.startswith(("Attributes", "SpellClassMask", "EffectSpellClassMask"))
                bad.append(f"{sid}: {col} {hex(_u32(got))}, expected {hex(_u32(val))}" if hexy
                           else f"{sid}: {col} {got!r}, expected {val!r}")
    return bad


def check_row_pins(rows: dict) -> list[str]:
    return check_pins(rows, ROW_PINS)


def check_new_row_pins(rows: dict) -> list[str]:
    return check_pins(rows, NEW_ROW_PINS)


def check_carriers(rows: dict) -> list[str]:
    """Every SpellMod (aura 107 / 108) has a non-empty mask on its own letter; every carrier of a mask aura (107, 108,
    262, 280) is SpellClassSet 4 (load-bearing on 262 / 280: set 0 would reach every class's spells)."""
    bad = []
    for sid in sorted(set(S3_RANK_IDS) | set(S3_IDS) | {RECKLESSNESS}):
        r = rows.get(sid)
        if r is None:
            continue
        for idx in range(3):
            typ, aura, _misc, _bp = s1._eff(r, idx)
            if typ != EFF_APPLY_AURA or aura not in (107, 108, 262, 280):
                continue
            if not any(_emask(r, idx)):
                bad.append(f"{sid}: e{idx} (aura {aura}) has an empty mask")
            if _i(r, "SpellClassSet") != 4:
                bad.append(f"{sid}: e{idx} (aura {aura}) is carried by SpellClassSet {r.get('SpellClassSet')!r}, "
                           "expected 4")
    return bad


def check_mask_dwords(rows: dict) -> list[str]:
    """Each S3 SpellMod mask sits in exactly the dwords the doc names (no stray bit on another dword of the same
    effect): the sum of the three dwords' populated count equals the pinned one."""
    bad = []
    named = {}
    for _name, (ids, effects, _cols, _rc) in SPECS.items():
        for idx, aura, _misc, bps, mask in effects:
            if aura in (107, 108):
                for rank, sid in enumerate(ids):
                    if bps[rank] is not None:
                        named[(sid, idx)] = mask
    for sid, pins in NEW_ROW_PINS.items():
        for idx in range(3):
            letter = "ABC"[idx]
            cols = [f"EffectSpellClassMask{letter}_{n}" for n in (1, 2, 3)]
            if any(c in pins for c in cols) and rows.get(sid) is not None:
                named[(sid, idx)] = tuple(pins.get(c, 0) for c in cols)
    for (sid, idx), mask in sorted(named.items()):
        r = rows.get(sid)
        if r is not None and _emask(r, idx) != tuple(mask):
            bad.append(f"{sid}: e{idx} mask {_hex3(_emask(r, idx))}, expected {_hex3(mask)}")
    return bad


def check_strikes(rows: dict, range_yd) -> list[str]:
    """D7 / D19 strikes: DmgClass 2 on every strike, REQUIRES_OFF_HAND_WEAPON on the three off-hand strikes only,
    both SUPPRESS flags on all four, 50000 yd and no facing flag, chain 0 on 204634's two effects, the Frenzied Blows
    strikes copy their parent's damage rows."""
    bad = _missing(rows, *STRIKE_IDS, HEROIC_STRIKE, CLEAVE)
    if bad:
        return bad
    for sid in STRIKE_IDS:
        r = rows[sid]
        if _i(r, "DefenseType") != 2:
            bad.append(f"{sid}: DmgClass {r.get('DefenseType')!r}, expected 2 (MELEE)")
        if not _i(r, "AttributesEx3") & ATTR3_SUPPRESS_CASTER_PROCS:
            bad.append(f"{sid}: lost SUPPRESS_CASTER_PROCS (Ex3 0x10000)")
        if not _i(r, "AttributesEx4") & ATTR4_SUPPRESS_WEAPON_PROCS:
            bad.append(f"{sid}: lost SUPPRESS_WEAPON_PROCS (Ex4 0x800000)")
        has_oh = bool(_i(r, "AttributesEx3") & ATTR3_REQUIRES_OFF_HAND_WEAPON)
        if has_oh != (sid in OH_WEAPON_IDS):
            bad.append(f"{sid}: REQUIRES_OFF_HAND_WEAPON is {has_oh}, expected {sid in OH_WEAPON_IDS}")
        if range_yd(r) != 50000.0:
            bad.append(f"{sid}: range {range_yd(r)} yd, expected 50000 (no range failure on a triggered cast)")
        if _i(r, "FacingCasterFlags"):
            bad.append(f"{sid}: FacingCasterFlags {r.get('FacingCasterFlags')!r}, expected none")
        if _i(r, "EquippedItemClass") != -1:
            bad.append(f"{sid}: EquippedItemClass {r.get('EquippedItemClass')!r}, expected -1")
        for idx in (1, 2):
            if _i(r, f"EffectChainTargets_{idx}"):
                bad.append(f"{sid}: EffectChainTargets_{idx} {r.get(f'EffectChainTargets_{idx}')!r}, expected 0 "
                           "(the parent's chain 2 + Improved Cleave's JUMP_TARGETS would hit three per target)")
        if _i(r, "Attributes") & ATTR0_DO_NOT_DISPLAY == 0:
            bad.append(f"{sid}: a strike must be hidden (0x80)")
    for sid, parent in STRIKE_PARENTS.items():
        for n in (1, 2):
            for col in (f"Effect_{n}", f"EffectBasePoints_{n}", f"EffectDieSides_{n}", f"EffectRealPointsPerLevel_{n}"):
                if rows[sid].get(col) != rows[parent].get(col):
                    bad.append(f"{sid}: {col} {rows[sid].get(col)!r} differs from {parent}'s {rows[parent].get(col)!r}")
    if rows[RAMPAGE].get("DefenseType") != 2:
        bad.append(f"{RAMPAGE}: DmgClass {rows[RAMPAGE].get('DefenseType')!r}, expected 2 (one CAST-phase melee event)")
    return bad


def check_visibility(rows: dict) -> list[str]:
    """D38: the buffs the doc says are shown carry neither PASSIVE 0x40 nor DO_NOT_DISPLAY 0x80; the helpers hide."""
    bad = _missing(rows, *VISIBLE_IDS, *HIDDEN_IDS)
    for sid in VISIBLE_IDS:
        if sid in rows and _i(rows[sid], "Attributes") & (ATTR0_PASSIVE | ATTR0_DO_NOT_DISPLAY):
            bad.append(f"{sid}: should be visible but Attributes {hex(_i(rows[sid], 'Attributes'))}")
    for sid in HIDDEN_IDS:
        if sid in rows and not _i(rows[sid], "Attributes") & ATTR0_DO_NOT_DISPLAY:
            bad.append(f"{sid}: should be hidden (0x80) but Attributes {hex(_i(rows[sid], 'Attributes'))}")
    return bad


def check_equipped_class(rows: dict) -> list[str]:
    """R2 (user ruling 2026-10-30): Enrage and Titan's Grip's penalty are EquippedItemClass -1 so they reach Rend."""
    bad = _missing(rows, ENRAGE, TG_PENALTY)
    for sid in (ENRAGE, TG_PENALTY):
        if sid in rows and (_i(rows[sid], "EquippedItemClass"), _i(rows[sid], "EquippedItemSubclass")) != (-1, 0):
            gate = (rows[sid].get("EquippedItemClass"), rows[sid].get("EquippedItemSubclass"))
            bad.append(f"{sid}: weapon gate {gate!r}, expected (-1, 0)")
    return bad


def check_zeroed_procs(rows: dict) -> list[str]:
    """The charged / carrier buffs the build keeps off the proc system: ProcTypeMask 0 (any non-zero DBC value on a
    mod aura auto-generates a per-target HIT consumer) and the carriers whose stock proc fields were cleared."""
    bad = _missing(rows, *PROC_ZEROED_RANKS, BLOOD_RUSH_BUFF, DEATHMAKER_BUFF, MERCILESS_FREE, FRESH_MEAT_CRIT,
                   BLOODSURGE_BUFF, RECKLESSNESS, SNAPSHOT)
    for sid in (*PROC_ZEROED_RANKS, BLOOD_RUSH_BUFF, DEATHMAKER_BUFF, MERCILESS_FREE, FRESH_MEAT_CRIT, BLOODSURGE_BUFF,
                SNAPSHOT, RECKLESSNESS):
        r = rows.get(sid)
        if r is not None and _i(r, "ProcTypeMask") != 0:
            bad.append(f"{sid}: ProcTypeMask {r.get('ProcTypeMask')!r}, expected 0")
    for sid in PROC_ZEROED_RANKS:
        r = rows.get(sid)
        if r is not None and _i(r, "ProcChance") != 0:
            bad.append(f"{sid}: ProcChance {r.get('ProcChance')!r}, expected 0")
    return bad


def check_durations(rows: dict, dur_ms) -> list[str]:
    bad = []
    for idx, ms in sorted(DUR_MS.items()):
        got = dur_ms({"DurationIndex": idx})
        if got != ms:
            bad.append(f"SpellDuration index {idx}: {got} ms, expected {ms} ms")
    return bad


def check_custom_attrs(custom_attrs: dict) -> list[str]:
    bad = []
    for sid, flag in CUSTOM_ATTR_IDS.items():
        if custom_attrs.get(sid) != flag:
            bad.append(f"{sid}: custom attr {custom_attrs.get(sid)!r}, expected {flag:#x}")
    extra = sorted(sid for sid in custom_attrs if S3_FIRST <= sid <= S3_BLOCK_END and sid not in CUSTOM_ATTR_IDS
                   and not 204770 <= sid <= 204799)
    if extra:
        bad.append(f"unexpected custom attrs on S3 ids {extra}")
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


def check_bloodthirst(rows: dict) -> list[str]:
    """D9: free (cost 0), 6 s, e0 SCHOOL_DAMAGE / e1 DUMMY at index 1 (the stock heal script reads Effects[1]), NO
    ENERGIZE effect anywhere (a caster-target effect makes the caster a second target), stock family bits."""
    bad = _missing(rows, BLOODTHIRST)
    if bad:
        return bad
    r = rows[BLOODTHIRST]
    if _i(r, "ManaCost") != 0:
        bad.append(f"{BLOODTHIRST}: ManaCost {r.get('ManaCost')!r}, expected 0 (free)")
    if _i(r, "RecoveryTime") != 6000:
        bad.append(f"{BLOODTHIRST}: RecoveryTime {r.get('RecoveryTime')!r}, expected 6000")
    if (_i(r, "Category"), _i(r, "CategoryRecoveryTime")) != (0, 0):
        bad.append(f"{BLOODTHIRST}: category {(r.get('Category'), r.get('CategoryRecoveryTime'))!r}, expected (0, 0)")
    if _i(r, "Effect_1") != EFF_SCHOOL_DAMAGE:
        bad.append(f"{BLOODTHIRST}: e0 type {r.get('Effect_1')!r}, expected SCHOOL_DAMAGE")
    if _i(r, "Effect_2") != EFF_DUMMY:
        bad.append(f"{BLOODTHIRST}: e1 type {r.get('Effect_2')!r}, expected DUMMY at index 1")
    for n in (1, 2, 3):
        if _i(r, f"Effect_{n}") == EFF_ENERGIZE:
            bad.append(f"{BLOODTHIRST}: effect {n} is ENERGIZE (the rage is granted in C++ on the landed hit)")
    bad += _effect_empty(r, 2, BLOODTHIRST, "Bloodthirst")
    if _u32(r.get("SpellClassMask_2")) != 0x400 or _u32(r.get("SpellClassMask_3")) != 0x8:
        bad.append(f"{BLOODTHIRST}: family bits d1 0x400 / d2 0x8 changed")
    if (_i(r, "StartRecoveryCategory"), _i(r, "StartRecoveryTime")) != (133, 1500):
        bad.append(f"{BLOODTHIRST}: GCD {(r.get('StartRecoveryCategory'), r.get('StartRecoveryTime'))!r}, expected "
                   "(133, 1500)")
    return bad


def check_death_wish(rows: dict, group_removals: list[dict], groups: list[dict]) -> list[str]:
    """D5: e0 gone, e1 PERIODIC_DUMMY 1000 ms, e2 +5% damage taken, 15 s, 120 s, off the GCD, 10 rage, stock dispel /
    mechanic kept, left spell_group 1107 (its aura 79 is gone)."""
    bad = _missing(rows, DEATH_WISH)
    if bad:
        return bad
    r = rows[DEATH_WISH]
    bad += _effect_empty(r, 0, DEATH_WISH, "Death Wish")
    bad += _aura_effect(r, 1, AURA_PERIODIC_DUMMY, None, None, Z, DEATH_WISH, "Death Wish")
    if _i(r, "EffectAuraPeriod_2") != 1000:
        bad.append(f"{DEATH_WISH}: e1 period {r.get('EffectAuraPeriod_2')!r}, expected 1000")
    bad += _aura_effect(r, 2, AURA_DMG_TAKEN_PCT, 127, 4, Z, DEATH_WISH, "Death Wish")
    if _i(r, "DurationIndex") != DUR["15s"]:
        bad.append(f"{DEATH_WISH}: duration index {r.get('DurationIndex')!r}, expected {DUR['15s']} (15 s)")
    if _i(r, "RecoveryTime") != 120000:
        bad.append(f"{DEATH_WISH}: RecoveryTime {r.get('RecoveryTime')!r}, expected 120000")
    if (_i(r, "StartRecoveryCategory"), _i(r, "StartRecoveryTime")) != (0, 0):
        bad.append(f"{DEATH_WISH}: GCD {(r.get('StartRecoveryCategory'), r.get('StartRecoveryTime'))!r}, expected "
                   "(0, 0) (off the GCD)")
    if _i(r, "ManaCost") != 100:
        bad.append(f"{DEATH_WISH}: ManaCost {r.get('ManaCost')!r}, expected 100 (10 rage)")
    if (_i(r, "DispelType"), _i(r, "Mechanic")) != (9, 31):
        bad.append(f"{DEATH_WISH}: dispel / mechanic {(r.get('DispelType'), r.get('Mechanic'))!r}, expected (9, 31)")
    if (1107, DEATH_WISH) not in {(int(g["id"]), int(g["spell_id"])) for g in group_removals}:
        bad.append("leave_spell_group(1107, 12292) is not declared")
    if (1107, DEATH_WISH) in {(int(g["id"]), int(g["spell_id"])) for g in groups}:
        bad.append("spell_group 1107 / 12292 is declared (Death Wish left the group)")
    return bad


def check_recklessness(rows: dict, procs: list[dict], proc_removals: list[dict]) -> list[str]:
    """B-R1: no spell_proc row for 1719, raw ProcTypeMask 0 (so none is auto-generated), the live phase-2 row removed,
    3 charges and the W0b crit mod kept (Player::RemoveSpellMods spends one charge per Spell at finish)."""
    bad = _missing(rows, RECKLESSNESS)
    if bad:
        return bad
    r = rows[RECKLESSNESS]
    if _i(r, "ProcTypeMask") != 0:
        bad.append(f"{RECKLESSNESS}: ProcTypeMask {r.get('ProcTypeMask')!r}, expected 0")
    if _i(r, "ProcChance") != 0:
        bad.append(f"{RECKLESSNESS}: ProcChance {r.get('ProcChance')!r}, expected 0")
    if _i(r, "ProcCharges") != 3:
        bad.append(f"{RECKLESSNESS}: ProcCharges {r.get('ProcCharges')!r}, expected 3")
    if any(int(p["SpellId"]) == RECKLESSNESS for p in procs):
        bad.append(f"{RECKLESSNESS}: a spell_proc row is declared (B-R1: none)")
    if RECKLESSNESS not in {int(p["SpellId"]) for p in proc_removals}:
        bad.append(f"remove_spell_proc({RECKLESSNESS}) is not declared (the live phase-2 row would survive)")
    bad += _aura_effect(r, 0, AURA_SPELLMOD_FLAT, OP_CRIT, 99, (0, 0, 0x8), RECKLESSNESS, "Recklessness")
    return bad


def check_shouts(rows: dict) -> list[str]:
    """D30: Battle Shout's new e2 (aura 29 Strength) and Commanding Shout's new e1 (aura 29 Stamina), the same
    target / radius as the shout's other effects; the script writes the amount (bp -1 = value 0)."""
    bad = _missing(rows, BATTLE_SHOUT, COMMANDING_SHOUT)
    if bad:
        return bad
    bs, cs = rows[BATTLE_SHOUT], rows[COMMANDING_SHOUT]
    bad += _aura_effect(bs, 2, AURA_MOD_STAT, 0, -1, Z, BATTLE_SHOUT, "Battle Shout")
    bad += _aura_effect(cs, 1, AURA_MOD_STAT, 2, -1, Z, COMMANDING_SHOUT, "Commanding Shout")
    for r, sid, idx, ref in ((bs, BATTLE_SHOUT, 2, 0), (cs, COMMANDING_SHOUT, 1, 0)):
        n, m = idx + 1, ref + 1
        for col in ("ImplicitTargetA", "ImplicitTargetB", "EffectRadiusIndex"):
            if r.get(f"{col}_{n}") != r.get(f"{col}_{m}"):
                bad.append(f"{sid}: e{idx} {col} {r.get(f'{col}_{n}')!r} differs from e{ref}'s {r.get(f'{col}_{m}')!r}")
    if (_i(bs, "EffectAura_1"), _i(bs, "EffectAura_2")) != (99, 124):
        bad.append(f"{BATTLE_SHOUT}: stock e0 / e1 auras changed")
    if _i(cs, "EffectAura_1") != 230:
        bad.append(f"{COMMANDING_SHOUT}: stock e0 aura changed")
    for sid, clause in SHOUT_AURA_CLAUSES.items():
        if clause not in str(rows[sid].get("AuraDescription_Lang_enUS") or ""):
            bad.append(f"{sid}: aura text lacks {clause!r}")
    return bad


def check_impale(rows: dict) -> list[str]:
    """D35: Impale's CRIT_DAMAGE mask d2 0xB -> 0xF (adds Rampage b2: the strikes are abilities)."""
    bad = _missing(rows, *IMPALE)
    for sid in IMPALE:
        if sid in rows and _emask(rows[sid], 0)[2] != 0xF:
            bad.append(f"{sid}: Impale d2 mask {hex(_emask(rows[sid], 0)[2])}, expected 0xf")
    return bad


def check_new_ids(rows: dict) -> list[str]:
    bad = []
    got = sorted(sid for sid in rows if S3_FIRST <= sid <= S3_BLOCK_END and not 204770 <= sid <= 204799)
    want = sorted(S3_IDS)
    if got != want:
        bad.append(f"ids in the S3 block: missing {sorted(set(want) - set(got))}, "
                   f"unexpected {sorted(set(got) - set(want))}")
    reserved = sorted(sid for sid in rows if 204869 <= sid <= 204899)
    if reserved:
        bad.append(f"ids in the reserved 204869-204899 range: {reserved}")
    return bad


def check_bindings(names: list[dict], removals: list[dict]) -> list[str]:
    bad = []
    have: dict[int, set[str]] = {}
    for n in names:
        have.setdefault(int(n["spell_id"]), set()).add(n["ScriptName"])
    for sid, expect in sorted(S3_BINDINGS.items()):
        if have.get(sid, set()) != expect:
            bad.append(f"scripted_by on {sid}: {sorted(have.get(sid, set()))}, expected exactly {sorted(expect)}")
    declared = sum(1 for n in names
                   if n["ScriptName"] in S3_BINDINGS.get(int(n["spell_id"]), ()))
    if declared != 15:
        bad.append(f"{declared} S3 scripted_by rows declared, expected 15")
    gone = {(int(n["spell_id"]), n["ScriptName"]) for n in removals}
    for b in sorted(S3_UNBINDINGS - gone):
        bad.append(f"unbind_script {b} is not declared")
    for sid, name in sorted(S3_UNBINDINGS):
        if name in have.get(sid, set()):
            bad.append(f"{name} is both bound and unbound on {sid}")
    if (23880, "spell_warr_bloodthirst_heal") in gone:
        bad.append("unbind_script(23880, spell_warr_bloodthirst_heal) is declared (the heal script is kept)")
    for sid in S3_UNSCRIPTED:
        if have.get(sid):
            bad.append(f"{sid}: carries a script {sorted(have[sid])} (its logic lives in the shared scripts)")
    return bad


def check_proc_rows(procs: list[dict], proc_removals: list[dict]) -> list[str]:
    bad = []
    by_id = {int(p["SpellId"]): p for p in procs}
    for sid, cols in sorted(S3_PROC_ROWS.items()):
        row = by_id.get(sid)
        if row is None:
            bad.append(f"{sid}: no spell_proc row")
            continue
        for col, val in cols.items():
            got = row.get(col)
            if float(got or 0) != float(val):
                bad.append(f"{sid}: spell_proc {col} {got!r}, expected {val!r}")
    gone = {int(r["SpellId"]) for r in proc_removals}
    for sid in sorted(S3_PROC_REMOVALS - gone):
        bad.append(f"remove_spell_proc({sid}) is not declared")
    for sid in S3_PROC_REMOVALS:
        if sid in by_id:
            bad.append(f"{sid}: a spell_proc row is still declared")
    for sid in NO_PROC_ROW_IDS:
        if sid in by_id:
            bad.append(f"{sid}: has a spell_proc row (charged / carrier buff: ProcTypeMask 0, no row)")
    return bad


def check_spell_groups(groups: list[dict]) -> list[str]:
    bad = []
    for g in groups:
        if int(g["id"]) in (1302, 1303, 1305) or S3_FIRST <= int(g["spell_id"]) <= S3_LAST:
            bad.append(f"spell_group {g['id']}/{g['spell_id']} declared by S3 (S3 mints no spell_group)")
    return bad


def check_consts(consts: list[dict]) -> list[str]:
    bad = []
    by_name = {c["name"]: c for c in consts}
    for name, (value, cpp) in sorted(CONSTS.items()):
        c = by_name.get(name)
        if c is None:
            bad.append(f"const {name} is not declared")
            continue
        if c["value"] != value:
            bad.append(f"const {name}: value {c['value']!r}, expected {value!r}")
        if c["cpp_type"] != cpp:
            bad.append(f"const {name}: type {c['cpp_type']!r}, expected {cpp!r}")
    return bad


def check_sentinel(rows: dict, sentinel: int) -> list[str]:
    """_masks.SHREDDING_SENTINEL = 0x100 (d2 b8) and no warrior spell carries it: only the three Shredding buffs READ it
    (white swings only, Unit.cpp:2316), so a carrier bit would leak the armor penetration to an ability."""
    bad = []
    if sentinel != 0x100:
        bad.append(f"_masks.SHREDDING_SENTINEL is {sentinel:#x}, expected 0x100")
    for sid, r in rows.items():
        if _i(r, "SpellClassSet") != 4:
            continue
        if _u32(r.get("SpellClassMask_3")) & sentinel:
            bad.append(f"{sid}: carries the Shredding sentinel d2 {sentinel:#x} in its own family mask")
        if sid not in SHRED_BUFFS:
            for idx in range(3):
                if _emask(r, idx)[2] & sentinel and s1._eff(r, idx)[1] == AURA_ARMOR_PEN:
                    bad.append(f"{sid}: e{idx} reads the Shredding sentinel without being a Shredding buff")
    for sid in SHRED_BUFFS:
        if sid in rows and _emask(rows[sid], 0) != (0, 0, sentinel):
            bad.append(f"{sid}: Shredding mask {_hex3(_emask(rows[sid], 0))}, expected (0, 0, {sentinel:#x})")
    return bad


# ---- S3 fix pass (S3-CODE-REVIEW M1 / m1) ----------------------------------------------------------------------------
WHIRLWIND_OH = 44949
# M1: the synchronous children of one press that read a charged mod, and the charged auras Warrior::PressChargeGuard
# bumps around them (spell_warr_hs_cleave_fury's AfterHit strike, spell_warr_whirlwind_seismic's 1680 e1 launch).
PRESS_CHILDREN = {FB_HS: HEROIC_STRIKE, FB_CLEAVE: CLEAVE, WHIRLWIND_OH: WHIRLWIND}
PRESS_CHARGED = (RECKLESSNESS, BLOODSURGE_BUFF)


def _own_mask(row: dict) -> tuple[int, int, int]:
    return tuple(_u32(row.get(f"SpellClassMask_{n}")) for n in (1, 2, 3))


def _reads(aura: dict, child: dict) -> bool:
    return any(a & c for a, c in zip(_emask(aura, 0), _own_mask(child)))


def check_press_charge_guard(rows: dict, names: list[dict], procs: list[dict]) -> list[str]:
    """M1: the data the charge guard rests on. Recklessness and Bloodsurge are charged mods spent by
    Player::RemoveSpellMods (charges > 0, ProcTypeMask 0, no spell_proc row); the children the guard wraps really read
    them (Recklessness: all three; Bloodsurge: the Frenzied Cleave strike), and the parent reads what its child reads
    (so the parent's finish is the one spender); Whirlwind's effect 1 is the TRIGGER_SPELL -> 44949 the OnEffectLaunch
    hook replays, on the script bound to 1680."""
    bad = _missing(rows, *PRESS_CHILDREN, *PRESS_CHILDREN.values(), *PRESS_CHARGED)
    if bad:
        return bad
    proc_ids = {int(p["SpellId"]) for p in procs}
    for sid in PRESS_CHARGED:
        r = rows[sid]
        if _i(r, "ProcCharges") < 1:
            bad.append(f"{sid}: ProcCharges {r.get('ProcCharges')!r}, expected a charged aura")
        if _i(r, "ProcTypeMask") or sid in proc_ids:
            bad.append(f"{sid}: has a proc (ProcTypeMask / spell_proc): RemoveSpellMods would skip it")
    for child, parent in PRESS_CHILDREN.items():
        if not _reads(rows[RECKLESSNESS], rows[child]):
            bad.append(f"{child}: no longer reads Recklessness' mask (drop the guard, or fix the mask)")
        for aura in PRESS_CHARGED:
            if _reads(rows[aura], rows[child]) and not _reads(rows[aura], rows[parent]):
                bad.append(f"{child} reads {aura} but its parent {parent} does not: nothing would spend the charge")
    if not _reads(rows[BLOODSURGE_BUFF], rows[FB_CLEAVE]):
        bad.append(f"{FB_CLEAVE}: no longer reads Bloodsurge's mask (D15 / D19: +20% on every Frenzied Cleave strike)")
    ww = rows[WHIRLWIND]
    if _i(ww, "Effect_2") != EFF_TRIGGER_SPELL or _i(ww, "EffectTriggerSpell_2") != WHIRLWIND_OH:
        bad.append(f"{WHIRLWIND}: e1 is {ww.get('Effect_2')!r} -> {ww.get('EffectTriggerSpell_2')!r}, expected "
                   f"TRIGGER_SPELL -> {WHIRLWIND_OH} (spell_warr_whirlwind_seismic's EFFECT_1 launch hook)")
    bound = {n["ScriptName"] for n in names if int(n["spell_id"]) == WHIRLWIND}
    if bound != {"spell_warr_whirlwind_seismic"}:
        bad.append(f"{WHIRLWIND}: scripts {sorted(bound)}, expected exactly spell_warr_whirlwind_seismic")
    return bad


def check_blood_craze_bonus(bonus: list[dict]) -> list[str]:
    """m1: an all-zero spell_bonus_data row for 204650, so Unit::SpellHealingBonusDone reaches DoneTotalMod (Titan's
    Grip's -10% healing, D11) instead of returning the DmgClass NONE heal untouched."""
    found = [b for b in bonus if int(b["entry"]) == BC_HEAL]
    if len(found) != 1:
        return [f"{BC_HEAL}: {len(found)} spell_bonus_data rows, expected 1"]
    return [f"{BC_HEAL}: spell_bonus_data {col} {found[0].get(col)!r}, expected 0"
            for col in ("direct_bonus", "dot_bonus", "ap_bonus", "ap_dot_bonus") if float(found[0].get(col) or 0)]


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
    for vid in SDV_KEPT:
        if vid not in by_id:
            bad.append(f"SpellDescriptionVariables {vid}: S2's row must stay defined")
    for sid, (token, vid) in sorted(SDV_READERS.items()):
        r = rows.get(sid) or {}
        if token not in str(r.get("Description_Lang_enUS") or ""):
            bad.append(f"{sid}: description does not read {token}")
        if _i(r, "SpellDescriptionVariableID") != vid:
            bad.append(f"{sid}: SpellDescriptionVariableID {r.get('SpellDescriptionVariableID')!r}, expected {vid}")
    return bad


def check_no_stray_dollar(rows: dict) -> list[str]:
    bad = []
    for sid in S3_DOLLAR_SCAN:
        r = rows.get(sid)
        if r is None:
            continue
        aura = str(r.get("AuraDescription_Lang_enUS") or "")
        if "$" in re.sub(r"\$s\d", "", aura) or "{pot" in aura:
            bad.append(f"{sid}: AuraDescription has a '$' beyond $sN: {aura!r}")
        desc = str(r.get("Description_Lang_enUS") or "")
        if "{pot" in desc or "pot_text" in desc:
            bad.append(f"{sid}: Description keeps an unexpanded pot template: {desc!r}")
        if sid in S3_DOLLAR_EXEMPT:
            if sid in (204653, 204654, 204655) and not POT_TEXT_TOKENS.search(desc):
                bad.append(f"{sid}: the Dance of Death heal clause lost its pot_text expansion")
            continue
        if sid in AURA_TEXTS and sid not in S3_IDS and sid not in S3_RANK_IDS:
            continue        # stock spells (Death Wish, ...) keep their own $d / $s3 tokens
        if "$" in desc:
            bad.append(f"{sid}: Description has a '$': {desc!r}")
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
    """The nine Fury capstones in the T1 format: grey below the last rank, plain on it, one clause on every rank."""
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
        bad.append(f"EXPECTED_CAPSTONES['warrior'] is {sorted(expected)}, S3 expects {sorted(CAPSTONE_RANKS)} in it")
    return bad


def _load_masks():
    spec = importlib.util.spec_from_file_location("warrior_masks_s3", TOOL_ROOT / "source" / "classes" / "warrior" /
                                                  "_masks.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---- real data ----------------------------------------------------------------------------------------------------

class WarriorS3DataTest(unittest.TestCase):
    def assertClean(self, problems: list[str]):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_grid(self):
        self.assertClean(check_grid(_data()["talents"]))

    def test_tab_skill_line_and_rampage_sla(self):
        d = _data()
        self.assertClean(check_tab_skill_line(d["package"].skill_line_abilities, d["package"].tabs))

    def test_rank_rows(self):
        self.assertClean(check_rank_specs(_data()["rows"]))

    def test_non_aura_rows(self):
        self.assertClean(check_row_pins(_data()["rows"]))

    def test_carriers_have_masks_and_set_4(self):
        self.assertClean(check_carriers(_data()["rows"]))

    def test_masks_per_dword(self):
        self.assertClean(check_mask_dwords(_data()["rows"]))

    def test_new_rows(self):
        self.assertClean(check_new_row_pins(_data()["rows"]))

    def test_strikes(self):
        _data()
        self.assertClean(check_strikes(_data()["rows"], s1._range_yd))

    def test_visible_and_hidden_rows(self):
        self.assertClean(check_visibility(_data()["rows"]))

    def test_enrage_and_titans_grip_reach_rend(self):
        self.assertClean(check_equipped_class(_data()["rows"]))

    def test_proc_fields_zeroed(self):
        self.assertClean(check_zeroed_procs(_data()["rows"]))

    def test_durations(self):
        _data()
        self.assertClean(check_durations(_data()["rows"], s1._dur_ms))

    def test_custom_attrs(self):
        self.assertClean(check_custom_attrs(_data()["custom_attrs"]))

    def test_spell_levels(self):
        self.assertClean(check_spell_levels(_data()["rows"]))

    def test_bloodthirst(self):
        self.assertClean(check_bloodthirst(_data()["rows"]))

    def test_death_wish(self):
        d = _data()
        self.assertClean(check_death_wish(d["rows"], d["package"].spell_group_removals, d["package"].spell_groups))

    def test_recklessness(self):
        d = _data()
        self.assertClean(check_recklessness(d["rows"], d["procs"], d["proc_removals"]))

    def test_shouts(self):
        self.assertClean(check_shouts(_data()["rows"]))

    def test_impale(self):
        self.assertClean(check_impale(_data()["rows"]))

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

    def test_consts(self):
        self.assertClean(check_consts(_data()["package"].consts))

    def test_shredding_sentinel(self):
        self.assertClean(check_sentinel(_data()["rows"], _load_masks().SHREDDING_SENTINEL))

    def test_spell_description_variables(self):
        d = _data()
        self.assertClean(check_sdv(d["tooltip_vars"], d["rows"]))

    def test_no_stray_dollar(self):
        self.assertClean(check_no_stray_dollar(_data()["rows"]))

    def test_tooltips_match_the_doc(self):
        self.assertClean(check_tooltips(_data()["rows"]))

    def test_flurry_buff_aura_text_on_ranks_2_and_3_matches_the_doc(self):
        rows = _data()["rows"]
        self.assertClean([f"{sid}: aura text {rows[sid].get('AuraDescription_Lang_enUS')!r}, expected "
                          f"{FLURRY_AURA_TEXT!r}" for sid in FLURRY_BUFFS
                          if rows[sid].get("AuraDescription_Lang_enUS") != FLURRY_AURA_TEXT])

    def test_capstone_format(self):
        self.assertClean(check_capstones(_data()["rows"]))

    def test_press_charge_guard_data(self):
        d = _data()
        self.assertClean(check_press_charge_guard(d["rows"], d["names"], d["procs"]))

    def test_blood_craze_heal_has_an_all_zero_bonus_row(self):
        self.assertClean(check_blood_craze_bonus(_data()["bonus"]))


# ---- negative fixtures: every check must fire on a minimal bad mutation of the real built rows -------------------

def _bump(val):
    """A different value of the same kind."""
    return val + "x" if isinstance(val, str) else val + 1


class WarriorS3NegativeTest(unittest.TestCase):
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
            dep = [{**t, "depends_on": {"talent_id": 2250, "rank": 1}} if int(t["id"]) == tid else t for t in talents]
            self.assertGreaterEqual(len(check_grid(dep)), 1, tid)
        # a collision: Rampage onto Bloodsurge's cell
        collide = [{**t, "tier": 8, "column": 2} if int(t["id"]) == 1659 else t for t in talents]
        self.assertTrue(any("share the cell" in p for p in check_grid(collide)))
        # a retired talent back in the Fury tab / missing from the holding tab / still listing ranks
        for tid in RETIRED:
            back = [{**t, "tab_id": FURY_TAB} if int(t["id"]) == tid else t for t in talents]
            self.assertGreaterEqual(len(check_grid(back)), 1, tid)
            absent = [t for t in talents if int(t["id"]) != tid]
            self.assertGreaterEqual(len(check_grid(absent)), 1, tid)
            ranked = [{**t, "rank_spell_ids": [12282]} if int(t["id"]) == tid else t for t in talents]
            self.assertGreaterEqual(len(check_grid(ranked)), 1, tid)
        # a stray extra talent in the Fury tab / a minted talent out of range
        extra = [*talents, {"id": 60476, "tab_id": FURY_TAB, "tier": 0, "column": 0, "rank_spell_ids": [1],
                            "depends_on": None, "flags": 0}]
        self.assertGreaterEqual(len(check_grid(extra)), 1)

    def test_tab_skill_line(self):
        slas, tabs = self.d["package"].skill_line_abilities, self.d["package"].tabs
        self.assertEqual(check_tab_skill_line(slas, tabs), [])
        self.assertGreaterEqual(len(check_tab_skill_line([s for s in slas if int(s["id"]) != 30855], tabs)), 1)
        for col, val in (("skill_line", 26), ("class_mask", 2), ("spell_id", 78), ("race_mask", 1)):
            bad = [{**s, col: val} if int(s["id"]) == 30855 else s for s in slas]
            self.assertGreaterEqual(len(check_tab_skill_line(bad, tabs)), 1, col)
        self.assertGreaterEqual(len(check_tab_skill_line(slas, [t for t in tabs if int(t["id"]) != 164])), 1)
        reserved = {"id": 30868, "spell_id": 1, "skill_line": 256, "class_mask": 1}
        self.assertGreaterEqual(len(check_tab_skill_line([*slas, reserved], tabs)), 1)

    def test_rank_rows(self):
        self.assertEqual(check_rank_specs(self.rows), [])
        for name, (ids, effects, cols, rank_cols) in SPECS.items():
            for rank, sid in enumerate(ids):
                for idx, aura, misc, bps, mask in effects:
                    n = idx + 1
                    letter = "ABC"[idx]
                    if aura is None or bps[rank] is None:
                        mutated = _mut(self.rows, sid, **{f"EffectAura_{n}": 4, f"Effect_{n}": EFF_APPLY_AURA})
                        self.assertGreaterEqual(len(check_rank_specs(mutated)), 1, (name, sid, idx, "empty"))
                        continue
                    for col in (f"EffectBasePoints_{n}", f"EffectAura_{n}", f"Effect_{n}"):
                        self.assertGreaterEqual(len(check_rank_specs(_mut(self.rows, sid, **{col: _bump(
                            self.rows[sid][col])}))), 1, (name, sid, idx, col))
                    if misc is not None:
                        col = f"EffectMiscValue_{n}"
                        self.assertGreaterEqual(len(check_rank_specs(_mut(self.rows, sid, **{col: _bump(
                            self.rows[sid].get(col, 0))}))), 1, (name, sid, idx, col))
                    for dword in (1, 2, 3):
                        col = f"EffectSpellClassMask{letter}_{dword}"
                        cur = _u32(self.rows[sid].get(col))
                        self.assertGreaterEqual(len(check_rank_specs(_mut(self.rows, sid, **{col: cur ^ 0x1}))), 1,
                                                (name, sid, idx, col))
                    other = "ABC"[(idx + 1) % 3]
                    wrong = f"EffectSpellClassMask{other}_1"
                    if not _u32(self.rows[sid].get(wrong)):
                        self.assertGreaterEqual(len(check_rank_specs(_mut(self.rows, sid, **{wrong: 0x1}))), 1,
                                                (name, sid, idx, wrong))
                for col, val in cols.items():
                    self.assertGreaterEqual(len(check_rank_specs(_mut(self.rows, sid, **{col: _bump(
                        self.rows[sid].get(col, 0))}))), 1, (name, sid, col))
                for col in rank_cols:
                    self.assertGreaterEqual(len(check_rank_specs(_mut(self.rows, sid, **{col: _bump(
                        self.rows[sid].get(col, 0))}))), 1, (name, sid, col))
            self.assertGreaterEqual(len(check_rank_specs({k: v for k, v in self.rows.items() if k != ids[0]})), 1)

    def test_impale_mask_is_0xf(self):
        self.assertEqual(check_impale(self.rows), [])
        for sid in IMPALE:
            for bad in (0xB, 0x8, 0x3, 0x7, 0x0):
                self.assertGreaterEqual(len(check_impale(_mut(self.rows, sid, EffectSpellClassMaskA_3=bad))), 1,
                                        (sid, bad))
                self.assertGreaterEqual(len(check_rank_specs(_mut(self.rows, sid, EffectSpellClassMaskA_3=bad))), 1,
                                        (sid, bad))
        self.assertGreaterEqual(len(check_impale({k: v for k, v in self.rows.items() if k != 16493})), 1)

    def test_non_aura_rows(self):
        self.assertEqual(check_row_pins(self.rows), [])
        for sid, pins in ROW_PINS.items():
            for col, val in pins.items():
                self.assertGreaterEqual(len(check_row_pins(_mut(self.rows, sid, **{col: _bump(val)}))), 1, (sid, col))
            self.assertGreaterEqual(len(check_row_pins({k: v for k, v in self.rows.items() if k != sid})), 1)

    def test_carriers(self):
        self.assertEqual(check_carriers(self.rows), [])
        # an empty mask on every SpellMod / mask-aura carrier
        for sid, idx in ((204659, 0), (204637, 0), (204652, 0), (204652, 1), (204647, 0), (204649, 0), (204679, 0),
                         (46908, 1), (56927, 1), (29721, 1), (20496, 1), (204638, 0), (204644, 0), (204645, 0),
                         (204646, 0), (1719, 0)):
            letter = "ABC"[idx]
            mutated = _mut(self.rows, sid, **{f"EffectSpellClassMask{letter}_{n}": 0 for n in (1, 2, 3)})
            self.assertGreaterEqual(len(check_carriers(mutated)), 1, (sid, idx))
        # SpellClassSet 0 on any carrier (the aura-262 / aura-280 buffs above all)
        for sid in (204638, 204644, 204645, 204646, 204637, 204652, 204647, 204649, 204679, 204659, 46908, 56927,
                    29721, 20496, 1719):
            self.assertGreaterEqual(len(check_carriers(_mut(self.rows, sid, SpellClassSet=0))), 1, sid)

    def test_masks_per_dword(self):
        self.assertEqual(check_mask_dwords(self.rows), [])
        for sid, idx in ((204637, 0), (204652, 0), (204652, 1), (204649, 0), (204679, 0), (56927, 0), (56927, 1),
                         (29721, 0), (46908, 0), (204659, 0), (204644, 0), (204638, 0)):
            letter = "ABC"[idx]
            for dword in (1, 2, 3):
                col = f"EffectSpellClassMask{letter}_{dword}"
                cur = _u32(self.rows[sid].get(col))
                self.assertGreaterEqual(len(check_mask_dwords(_mut(self.rows, sid, **{col: cur ^ 0x1}))), 1,
                                        (sid, idx, dword))
        # a mask moved onto the wrong dword (the classic bug): Recklessness-style d2 bit in d0
        self.assertGreaterEqual(len(check_mask_dwords(_mut(
            self.rows, 204637, EffectSpellClassMaskA_3=0, EffectSpellClassMaskA_1=0x4))), 1)

    def test_new_rows(self):
        self.assertEqual(check_new_row_pins(self.rows), [])
        for sid, pins in NEW_ROW_PINS.items():
            for col, val in pins.items():
                self.assertGreaterEqual(len(check_new_row_pins(_mut(self.rows, sid, **{col: _bump(val)}))), 1,
                                        (sid, col))
            self.assertGreaterEqual(len(check_new_row_pins({k: v for k, v in self.rows.items() if k != sid})), 1)

    def test_strikes(self):
        self.assertEqual(check_strikes(self.rows, s1._range_yd), [])
        for sid in STRIKE_IDS:
            r = self.rows[sid]
            for mutation in ({"DefenseType": 0},
                             {"AttributesEx3": _i(r, "AttributesEx3") & ~ATTR3_SUPPRESS_CASTER_PROCS},
                             {"AttributesEx4": 0}, {"FacingCasterFlags": 1}, {"EquippedItemClass": 2},
                             {"RangeIndex": 2}, {"EffectChainTargets_1": 2}, {"EffectChainTargets_2": 2},
                             {"Attributes": 0},
                             {"AttributesEx3": _i(r, "AttributesEx3") ^ ATTR3_REQUIRES_OFF_HAND_WEAPON}):
                self.assertGreaterEqual(len(check_strikes(_mut(self.rows, sid, **mutation), s1._range_yd)), 1,
                                        (sid, mutation))
        for sid, parent in STRIKE_PARENTS.items():
            for col in ("EffectBasePoints_1", "EffectBasePoints_2", "Effect_2", "EffectRealPointsPerLevel_2"):
                self.assertGreaterEqual(len(check_strikes(_mut(self.rows, sid, **{col: _bump(self.rows[sid][col])}),
                                                          s1._range_yd)), 1, (sid, col))
        self.assertGreaterEqual(len(check_strikes(_mut(self.rows, RAMPAGE, DefenseType=0), s1._range_yd)), 1)
        self.assertGreaterEqual(len(check_strikes({k: v for k, v in self.rows.items() if k != FB_CLEAVE},
                                                  s1._range_yd)), 1)
        self.assertGreaterEqual(len(check_strikes(self.rows, lambda _row: 5.0)), 1)

    def test_visibility(self):
        self.assertEqual(check_visibility(self.rows), [])
        for sid in VISIBLE_IDS:
            for flag in (ATTR0_PASSIVE, ATTR0_DO_NOT_DISPLAY):
                mutated = _mut(self.rows, sid, Attributes=_i(self.rows[sid], "Attributes") | flag)
                self.assertGreaterEqual(len(check_visibility(mutated)), 1, (sid, flag))
        for sid in HIDDEN_IDS:
            mutated = _mut(self.rows, sid, Attributes=_i(self.rows[sid], "Attributes") & ~ATTR0_DO_NOT_DISPLAY)
            self.assertGreaterEqual(len(check_visibility(mutated)), 1, sid)
        self.assertGreaterEqual(len(check_visibility({k: v for k, v in self.rows.items() if k != METER})), 1)

    def test_equipped_class(self):
        self.fires(check_equipped_class, [(ENRAGE, "EquippedItemClass", 2), (TG_PENALTY, "EquippedItemClass", 2),
                                          (ENRAGE, "EquippedItemSubclass", 8), (TG_PENALTY, "EquippedItemSubclass", 8)])

    def test_proc_fields_zeroed(self):
        self.assertEqual(check_zeroed_procs(self.rows), [])
        for sid in PROC_ZEROED_RANKS:
            for col in ("ProcTypeMask", "ProcChance"):
                self.assertGreaterEqual(len(check_zeroed_procs(_mut(self.rows, sid, **{col: 20}))), 1, (sid, col))
        for sid in (BLOOD_RUSH_BUFF, DEATHMAKER_BUFF, MERCILESS_FREE, FRESH_MEAT_CRIT, BLOODSURGE_BUFF, SNAPSHOT,
                    RECKLESSNESS):
            self.assertGreaterEqual(len(check_zeroed_procs(_mut(self.rows, sid, ProcTypeMask=16))), 1, sid)
        self.assertGreaterEqual(len(check_zeroed_procs({k: v for k, v in self.rows.items() if k != 12317})), 1)

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
        self.assertGreaterEqual(len(check_custom_attrs({**ca, ENRAGE: CU_AURA_CANNOT_BE_SAVED})), 1)

    def test_spell_levels(self):
        self.fires(check_spell_levels, [
            (BLOODTHIRST, "SpellLevel", 40), (BLOODTHIRST, "BaseLevel", 40), (RAMPAGE, "SpellLevel", 60),
            (RAMPAGE, "BaseLevel", 1), (RAMPAGE, "MaxLevel", 80), (BLOODTHIRST, "MaxLevel", 80),
        ])

    def test_bloodthirst(self):
        self.fires(check_bloodthirst, [
            (BLOODTHIRST, "ManaCost", 200), (BLOODTHIRST, "RecoveryTime", 4000), (BLOODTHIRST, "Category", 971),
            (BLOODTHIRST, "CategoryRecoveryTime", 6000), (BLOODTHIRST, "Effect_1", EFF_DUMMY),
            (BLOODTHIRST, "Effect_2", EFF_SCHOOL_DAMAGE), (BLOODTHIRST, "Effect_3", EFF_ENERGIZE),
            (BLOODTHIRST, "Effect_2", EFF_ENERGIZE), (BLOODTHIRST, "EffectAura_3", 4),
            (BLOODTHIRST, "SpellClassMask_2", 0x4), (BLOODTHIRST, "SpellClassMask_3", 0x4),
            (BLOODTHIRST, "StartRecoveryTime", 0),
        ])

    def test_death_wish(self):
        gr, groups = self.d["package"].spell_group_removals, self.d["package"].spell_groups
        self.assertEqual(check_death_wish(self.rows, gr, groups), [])
        for sid, col, val in ((DEATH_WISH, "Effect_1", EFF_APPLY_AURA), (DEATH_WISH, "EffectAura_1", AURA_DMG_DONE_PCT),
                              (DEATH_WISH, "EffectAura_2", AURA_DMG_DONE_PCT), (DEATH_WISH, "EffectAuraPeriod_2", 0),
                              (DEATH_WISH, "EffectAura_3", 4), (DEATH_WISH, "EffectBasePoints_3", 19),
                              (DEATH_WISH, "DurationIndex", DUR["12s"]), (DEATH_WISH, "RecoveryTime", 180000),
                              (DEATH_WISH, "StartRecoveryTime", 1500), (DEATH_WISH, "StartRecoveryCategory", 133),
                              (DEATH_WISH, "ManaCost", 0), (DEATH_WISH, "DispelType", 0), (DEATH_WISH, "Mechanic", 0),
                              (DEATH_WISH, "EffectSpellClassMaskA_1", 0x1)):
            self.assertGreaterEqual(len(check_death_wish(_mut(self.rows, sid, **{col: val}), gr, groups)), 1,
                                    (col, val))
        self.assertGreaterEqual(len(check_death_wish(self.rows, [], groups)), 1)
        self.assertGreaterEqual(len(check_death_wish(self.rows, gr, [*groups, {"id": 1107, "spell_id": DEATH_WISH}])),
                                1)
        self.assertGreaterEqual(len(check_death_wish({k: v for k, v in self.rows.items() if k != DEATH_WISH}, gr,
                                                     groups)), 1)

    def test_recklessness(self):
        procs, rem = self.d["procs"], self.d["proc_removals"]
        self.assertEqual(check_recklessness(self.rows, procs, rem), [])
        for col, val in (("ProcTypeMask", 4368), ("ProcChance", 100), ("ProcCharges", 1), ("EffectBasePoints_1", 49),
                         ("EffectSpellClassMaskA_3", 0x4)):
            self.assertGreaterEqual(len(check_recklessness(_mut(self.rows, RECKLESSNESS, **{col: val}), procs, rem)), 1,
                                    col)
        extra_row = {"SpellId": RECKLESSNESS, "SpellPhaseMask": 1}
        self.assertGreaterEqual(len(check_recklessness(self.rows, [*procs, extra_row], rem)), 1)
        self.assertGreaterEqual(len(check_recklessness(
            self.rows, procs, [r for r in rem if int(r["SpellId"]) != RECKLESSNESS])), 1)

    def test_shouts(self):
        self.fires(check_shouts, [
            (BATTLE_SHOUT, "EffectAura_3", 99), (BATTLE_SHOUT, "EffectMiscValue_3", 2), (BATTLE_SHOUT, "Effect_3", 0),
            (BATTLE_SHOUT, "ImplicitTargetA_3", 1), (BATTLE_SHOUT, "EffectRadiusIndex_3", 4),
            (BATTLE_SHOUT, "EffectBasePoints_3", 14), (COMMANDING_SHOUT, "EffectAura_2", 99),
            (COMMANDING_SHOUT, "EffectMiscValue_2", 0), (COMMANDING_SHOUT, "ImplicitTargetA_2", 1),
            (COMMANDING_SHOUT, "EffectRadiusIndex_2", 4), (COMMANDING_SHOUT, "EffectAura_1", 99),
            (BATTLE_SHOUT, "EffectAura_2", 99),
            (BATTLE_SHOUT, "AuraDescription_Lang_enUS", "Increases your attack power."),
            (COMMANDING_SHOUT, "AuraDescription_Lang_enUS", "Maximum health increased."),
        ])

    def test_new_ids(self):
        self.assertEqual(check_new_ids(self.rows), [])
        for extra in (204681, 204700, 204769, 204869, 204899):
            self.assertGreaterEqual(len(check_new_ids({**self.rows, extra: {}})), 1, extra)
        for sid in S3_IDS:
            self.assertGreaterEqual(len(check_new_ids({k: v for k, v in self.rows.items() if k != sid})), 1, sid)

    def test_bindings(self):
        names, rem = self.d["names"], self.d["removals"]
        self.assertEqual(check_bindings(names, rem), [])
        for i, n in enumerate(names):
            if int(n["spell_id"]) in S3_BINDINGS and n["ScriptName"] in S3_BINDINGS[int(n["spell_id"])]:
                self.assertGreaterEqual(len(check_bindings(names[:i] + names[i + 1:], rem)), 1, n)
        for sid in (*S3_BINDINGS, *S3_UNSCRIPTED):
            extra = {"spell_id": sid, "ScriptName": "spell_warr_something_else"}
            self.assertGreaterEqual(len(check_bindings([*names, extra], rem)), 1, sid)
        for i in range(len(rem)):
            if (int(rem[i]["spell_id"]), rem[i]["ScriptName"]) in S3_UNBINDINGS:
                self.assertGreaterEqual(len(check_bindings(names, rem[:i] + rem[i + 1:])), 1, rem[i])
        for sid, name in S3_UNBINDINGS:
            self.assertGreaterEqual(len(check_bindings([*names, {"spell_id": sid, "ScriptName": name}], rem)), 1,
                                    (sid, name))
        kept = {"spell_id": 23880, "ScriptName": "spell_warr_bloodthirst_heal"}
        self.assertGreaterEqual(len(check_bindings(names, [*rem, kept])), 1)

    def test_proc_rows(self):
        procs, rem = self.d["procs"], self.d["proc_removals"]
        self.assertEqual(check_proc_rows(procs, rem), [])
        for sid, cols in S3_PROC_ROWS.items():
            self.assertGreaterEqual(len(check_proc_rows([p for p in procs if int(p["SpellId"]) != sid], rem)), 1, sid)
            for col, val in cols.items():
                mutated = [{**p, col: float(val) + 1} if int(p["SpellId"]) == sid else p for p in procs]
                self.assertGreaterEqual(len(check_proc_rows(mutated, rem)), 1, (sid, col))
        for i, r in enumerate(rem):
            if int(r["SpellId"]) in S3_PROC_REMOVALS:
                self.assertGreaterEqual(len(check_proc_rows(procs, rem[:i] + rem[i + 1:])), 1, r)
        for sid in S3_PROC_REMOVALS:
            self.assertGreaterEqual(len(check_proc_rows([*procs, {"SpellId": sid, "SpellPhaseMask": 1}], rem)), 1, sid)
        for sid in NO_PROC_ROW_IDS:
            self.assertGreaterEqual(len(check_proc_rows([*procs, {"SpellId": sid, "SpellPhaseMask": 1}], rem)), 1, sid)

    def test_spell_groups(self):
        groups = self.d["package"].spell_groups
        self.assertEqual(check_spell_groups(groups), [])
        for bad in ({"id": 1302, "spell_id": 200065}, {"id": 1305, "spell_id": 200065},
                    {"id": 1400, "spell_id": 204636},
                    {"id": 1303, "spell_id": 1}):
            self.assertGreaterEqual(len(check_spell_groups([*groups, bad])), 1, bad)

    def test_consts(self):
        consts = self.d["package"].consts
        self.assertEqual(check_consts(consts), [])
        for name, (value, cpp) in CONSTS.items():
            self.assertGreaterEqual(len(check_consts([c for c in consts if c["name"] != name])), 1, name)
            self.assertGreaterEqual(len(check_consts([{**c, "value": value + 1} if c["name"] == name else c
                                                      for c in consts])), 1, name)
            self.assertGreaterEqual(len(check_consts([{**c, "cpp_type": "float"} if c["name"] == name else c
                                                      for c in consts])), 1, name)

    def test_shredding_sentinel(self):
        self.assertEqual(check_sentinel(self.rows, 0x100), [])
        self.assertGreaterEqual(len(check_sentinel(self.rows, 0x200)), 1)
        # a family-4 spell carrying d2 b8 in its own mask would be read by the buffs' sentinel
        self.assertGreaterEqual(len(check_sentinel(_mut(self.rows, 12294, SpellClassMask_3=0x108), 0x100)), 1)
        # a non-Shredding armor-penetration carrier on the sentinel
        self.assertGreaterEqual(len(check_sentinel(_mut(self.rows, ENRAGE, EffectAura_1=AURA_ARMOR_PEN,
                                                        EffectSpellClassMaskA_3=0x100), 0x100)), 1)
        for sid in SHRED_BUFFS:
            self.assertGreaterEqual(len(check_sentinel(_mut(self.rows, sid, EffectSpellClassMaskA_3=0x80), 0x100)), 1)

    def test_sdv(self):
        tv = self.d["tooltip_vars"]
        self.assertEqual(check_sdv(tv, self.rows), [])
        for vid, ranks in SDV_ROWS.items():
            self.assertGreaterEqual(len(check_sdv([t for t in tv if int(t["id"]) != vid], self.rows)), 1, vid)
            for rank in ranks:
                broken = [{**t, "Variables": t["Variables"].replace(f"${rank}m", "$99m")} if int(t["id"]) == vid else t
                          for t in tv]
                self.assertGreaterEqual(len(check_sdv(broken, self.rows)), 1, (vid, rank))
        self.assertGreaterEqual(len(check_sdv([t for t in tv if int(t["id"]) != 1385], self.rows)), 1)
        for sid, (token, vid) in SDV_READERS.items():
            text = self.rows[sid]["Description_Lang_enUS"].replace(token, "1")
            self.assertGreaterEqual(len(check_sdv(tv, _mut(self.rows, sid, Description_Lang_enUS=text))), 1, sid)
            self.assertGreaterEqual(len(check_sdv(tv, _mut(self.rows, sid, SpellDescriptionVariableID=1385))), 1, sid)

    def test_no_stray_dollar(self):
        self.assertEqual(check_no_stray_dollar(self.rows), [])
        for sid in (*S3_IDS, 12329, 12317, 204656, 61216):
            for col in ("Description_Lang_enUS", "AuraDescription_Lang_enUS"):
                if sid in S3_DOLLAR_EXEMPT and col == "Description_Lang_enUS":
                    continue
                if sid not in self.rows:
                    continue
                self.assertGreaterEqual(len(check_no_stray_dollar(_mut(self.rows, sid, **{col: "reduces by $t1%"}))), 1,
                                        (sid, col))
        for sid in AURA_TEXTS:
            if sid in self.rows and sid in (S3_IDS):
                self.assertGreaterEqual(len(check_no_stray_dollar(_mut(
                    self.rows, sid, AuraDescription_Lang_enUS="x ${pot1}"))), 1, sid)
        # Dance of Death keeps its documented pot_text expansion, and only there
        self.assertGreaterEqual(len(check_no_stray_dollar(_mut(
            self.rows, 204653, Description_Lang_enUS="After you kill an enemy, heals you."))), 1)
        self.assertGreaterEqual(len(check_no_stray_dollar(_mut(
            self.rows, 204653, Description_Lang_enUS="heals {pot50}"))), 1)

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


    def test_press_charge_guard_data(self):
        names, procs = self.d["names"], self.d["procs"]
        self.assertEqual(check_press_charge_guard(self.rows, names, procs), [])
        for sid, col, val in ((RECKLESSNESS, "ProcCharges", 0), (BLOODSURGE_BUFF, "ProcTypeMask", 0x10),
                              (FB_HS, "SpellClassMask_3", 0), (WHIRLWIND_OH, "SpellClassMask_3", 0),
                              (FB_CLEAVE, "SpellClassMask_1", 0), (CLEAVE, "SpellClassMask_1", 0),
                              (WHIRLWIND, "EffectTriggerSpell_2", 50622), (WHIRLWIND, "Effect_2", EFF_DUMMY)):
            self.assertGreaterEqual(len(check_press_charge_guard(_mut(self.rows, sid, **{col: val}), names, procs)), 1,
                                    (sid, col))
        self.assertGreaterEqual(len(check_press_charge_guard(self.rows, names, [*procs, {"SpellId": RECKLESSNESS}])), 1)
        unbound = [n for n in names if int(n["spell_id"]) != WHIRLWIND]
        self.assertGreaterEqual(len(check_press_charge_guard(self.rows, unbound, procs)), 1)
        self.assertGreaterEqual(len(check_press_charge_guard({k: v for k, v in self.rows.items() if k != WHIRLWIND_OH},
                                                             names, procs)), 1)

    def test_blood_craze_bonus(self):
        bonus = self.d["bonus"]
        self.assertEqual(check_blood_craze_bonus(bonus), [])
        self.assertGreaterEqual(len(check_blood_craze_bonus([b for b in bonus if int(b["entry"]) != BC_HEAL])), 1)
        for col in ("direct_bonus", "dot_bonus", "ap_bonus", "ap_dot_bonus"):
            mutated = [{**b, col: 0.1} if int(b["entry"]) == BC_HEAL else b for b in bonus]
            self.assertGreaterEqual(len(check_blood_craze_bonus(mutated)), 1, col)

if __name__ == "__main__":
    unittest.main()
