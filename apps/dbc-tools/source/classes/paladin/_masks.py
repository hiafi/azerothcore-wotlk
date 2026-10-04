"""
Paladin - named SpellFamilyFlags (SpellClassMask_{1,2,3} / EffectSpellClassMask{A,B,C}_{1,2,3})
constants, composite (d0, d1, d2) masks, plus `spell_proc` PROC_* constants, shared across the
Retribution / Holy / Protection rework passes.

Leading underscore = not loaded as a class file by lib/dsl/registry.py's load_class_package (see
source/classes/README.md), just an importable module - `from . import _masks as m`.

Bit values below are the raw SpellFamilyFlags dword contents (the "final" masked value a row's
SpellClassMask_N / EffectSpellClassMaskX_N column carries), not bit positions. Sources: stock
bits from .agents/plans/paladin-rework/paladin-rework.FAMILY-BITS.md §3; custom bits SHARED.md A3 /
B6 item 2 / C5.1 item 2 and RETRIBUTION.md §2.4 / §2.5 (created in S1 WP-0).

Never put a bit marked "never reuse" (SHARED A3) on a non-carrier: SEAL_SPECIFIC_*, HAND d0 0x2190,
AURA d2 0x20, JOV_HARDCODE_NEVER d1 0x400000, HAND_OF_RECKONING_VINDICATION_HARDCODE d1 0x40000000,
HotR / Shield of Righteousness / Flash of Light, the DR keys, d2 b25-27 (load-time).
"""

# --- dword 1 (SpellClassMask_1 / EffectSpellClassMaskX_1) ---
RIGHTEOUS_FURY = 0x1
BLESSING_OF_MIGHT = 0x2
REPENTANCE = 0x4
RETRIBUTION_AURA = 0x8
HAND_OF_FREEDOM = 0x10
CONSECRATION = 0x20
DEVOTION_AURA = 0x40
HAND_OF_PROTECTION = 0x80
HAND_OF_SALVATION = 0x100
OLD_SOJ_STUN = 0x200
OLD_JUDGEMENT_OF_RIGHTEOUSNESS = 0x400
HAMMER_OF_JUSTICE = 0x800
CLEANSE_PURIFY = 0x1000
HAND_OF_SACRIFICE = 0x2000
AVENGERS_SHIELD = 0x4000
LAY_ON_HANDS = 0x8000
BLESSING_OF_WISDOM = 0x10000
CONCENTRATION_AURA = 0x20000
OLD_SEAL_HEAL_MANA_PROC = 0x40000
JUDGEMENT_LIGHT_WISDOM_DEBUFF = 0x80000
JUDGEMENT_OF_JUSTICE_DEBUFF = 0x100000
HOLY_SHOCK = 0x200000
DIVINE_PROTECTION_SHIELD = 0x400000
UNLEASH = 0x800000  # U - the 12 damaging unleashes (reclaimed old Judgement bit)
BLESSING_OF_KINGS = 0x1000000
SEAL_OF_COMMAND = 0x2000000
RESISTANCE_AURAS = 0x4000000  # reclaimed / free after S1 (SHARED C1.3)
SEAL_OF_RIGHTEOUSNESS_JUSTICE = 0x8000000
BLESSING_OF_SANCTUARY = 0x10000000
HOTC_DEBUFF_RV_DOT = 0x20000000
FLASH_OF_LIGHT = 0x40000000
HOLY_LIGHT = 0x80000000

# --- dword 2 (SpellClassMask_2 / EffectSpellClassMaskX_2) ---
JOL_HEAL = 0x1
EXORCISM = 0x2
RIGHTEOUS_DEFENSE = 0x4
OLD_SEAL_JUDGEMENT = 0x8
RESISTANCE_AURAS_D1 = 0x10  # reclaimed / free after S1 (SHARED C1.3)
D1_FREE_B5 = 0x20  # the only free d1 bit
HOLY_SHIELD = 0x40
HAMMER_OF_WRATH = 0x80
DIVINE_FAVOR = 0x100
OLD_JUDGEMENT_OF_COMMAND = 0x200
NPC_SEAL_BLOOD_MARTYR = 0x400
SEAL_OF_VENGEANCE = 0x800
SPIRITUAL_ATTUNEMENT = 0x1000
AVENGING_WRATH = 0x2000
CLUSTER_D1_B14 = 0x4000  # 12 carriers, useless for scoping
CRUSADER_STRIKE = 0x8000
HOLY_SHOCK_HEAL = 0x10000
DIVINE_STORM = 0x20000
HAMMER_OF_THE_RIGHTEOUS = 0x40000
SACRED_SHIELD = 0x80000
SHIELD_OF_RIGHTEOUSNESS = 0x100000
HOLY_WRATH = 0x200000
JOV_HARDCODE_NEVER = 0x400000  # Unit.cpp:8462 with icon 2292
TURN_EVIL = 0x800000
BEACON_OF_LIGHT = 0x1000000
SEAL_OF_LIGHT = 0x2000000
SEAL_OF_WISDOM = 0x4000000
SENSE_UNDEAD = 0x8000000
MOUNTS = 0x10000000
SEAL_OF_RIGHTEOUSNESS_D1 = 0x20000000
HAND_OF_RECKONING_VINDICATION_HARDCODE = 0x40000000  # Spell.cpp:9144
CLUSTER_D1_B31 = 0x80000000

# --- dword 3 (SpellClassMask_3 / EffectSpellClassMaskX_3) ---
DIVINE_PLEA = 0x1
ART_OF_WAR_BUFF = 0x2
DIVINE_SACRIFICE = 0x4
JUDGEMENT = 0x8  # J - Judgement 201060
OLD_JUDGEMENT_BLOOD = 0x10
AURA = 0x20  # HARDCODE (SpellInfo.cpp:2227) - never on a non-aura
OLD_JOTJ = 0x40
FORBEARANCE = 0x80
DIVINE_PROTECTION = 0x100
SEAL_PASSIVE = 0x200  # P - 12 seal passives + Ret's BoJ echoes
SEAL_PASSIVE_COMMAND = 0x400  # C - Command passives + Command echo
BLADE_OF_JUSTICE = 0x800  # Ret, 201400 only (echoes carry P)
WAKE_OF_ASHES = 0x1000  # Ret, 201413 only (stun 201414 carries none)
EXECUTION_SENTENCE = 0x2000  # Ret, 201410 / 201411 / 201412
LIGHTS_HAMMER = 0x4000  # Holy; never on a spell with MOD_DECREASE_SPEED (spell_warrior.cpp:1099)
DIVINE_SHIELD = 0x8000  # Divine Shield 642 (added, keeps d0 0x400000)
DELIVERANCE = 0x10000  # Dv - Deliverance 201061
SUNLIGHT_OPT = 0x20000  # optional, Holy Sunlight hit
AURA_BURST = 0x40000  # AB - the five aura bursts 201160-201164 (Part C); in LOADTIME_IMP_* comments below
UNLEASH_COMMAND = 0x80000  # CU - 201070 / 201076 only (in addition to U), never 201100
LOADTIME_IMP_DEVOTION = 0x2000000  # load-time (SIC:489-510); also carried by the burst 201161 retarget (C1.7)
LOADTIME_IMP_CONCENTRATION = 0x4000000  # load-time (SIC:483-522); also carried by the burst 201164 retarget
LOADTIME_SANCTIFIED_RETRIBUTION = 0x8000000  # load-time (SIC:495-539)

# --- composites: (d0, d1, d2) = (SpellClassMask_1, _2, _3) ---
SEAL_SPECIFIC_D0 = 0x0A000000  # never on a non-seal
SEAL_SPECIFIC_D1 = 0x26000C00  # never on a non-seal
ALL_PLAYER_SEALS = (0x0A000000, 0x26000800, 0)  # excludes the NPC-only d1 0x400
JUDGEMENT_CASTS = (0, 0, 0x10008)  # J | Dv
JUDGEMENT_ALL = (0x800000, 0, 0x10008)  # U | J | Dv
SEAL_DAMAGE = (0x800000, 0, 0x200)  # U | P (C carriers also carry P)
COMMAND_ALL = (0, 0, 0x80400)  # C | CU: Command passives + Command unleashes (Prot's Improved Seal of Command)
AURA_BURSTS = (0, 0, 0x40000)  # AB
MULTI_TARGET_ATTACKS = (0, 0x260000, 0x1000)  # Divine Storm, HotR, Holy Wrath; Wake of Ashes

# Retribution composites (RETRIBUTION.md §2.5)
RET_HOLY_DAMAGE = (0xA04020, 0x3400C2, 0x13E08)  # excludes Light's Hammer d2 0x4000 and the bit-free Vindication hit
AOW_DAMAGE = (0x800000, 0x28000, 0x12008)  # U, CS, DS, J, Dv, ES
AOW_DOT = (0x800000, 0, 0x2000)  # U (Vengeance unleash DoT), ES DoT
AOW_PROC = (0, 0x28000, 0x12008)  # CS, DS, J, Dv, ES (no U: one roll per cast)
SANCTITY_DAMAGE = (0x20, 0x28002, 0x3000)  # Consecration, Exorcism, CS, DS, WoA, ES
SANCTITY_DOT = (0x20, 0, 0x2000)  # Consecration, ES DoT
PURIFY_DAMAGE = (0x20, 0x220000, 0x11400)  # Consecration, DS, Holy Wrath, C, WoA, Dv
PURIFY_DOT = (0x20, 0, 0)  # Consecration
RV_PROC = (0x800000, 0x168082, 0x10008)  # U, Exorcism, HoW, CS, DS, HotR, SotR, J, Dv
CONVICTION_PROC = (0, 0x28082, 0)  # Exorcism, HoW, CS, DS
SWIFT_RET_PROC = (0, 0x8000, 0x8)  # CS, J
VENGEANCE_STRIKES = (0, 0x28000, 0)  # CS, DS

# --- spell_proc constants (SpellMgr.h:113-277) ---
PROC_FLAG_DONE_MELEE_AUTO_ATTACK = 0x4
PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS = 0x10
PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG = 0x10000
PROC_SPELL_TYPE_DAMAGE = 1
PROC_SPELL_PHASE_CAST = 1
PROC_SPELL_PHASE_HIT = 2
PROC_HIT_CRITICAL = 2
PROC_ATTR_TRIGGERED_CAN_PROC = 0x2
SEAL_PROC_FLAGS = (
    PROC_FLAG_DONE_MELEE_AUTO_ATTACK | PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS | PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG
)  # 0x10014
