"""
Hunter - named SpellFamilyFlags (SpellClassMask_{1,2,3} / EffectSpellClassMask{A,B,C}_{1,2,3})
constants, composite (d0, d1, d2) masks, plus `spell_proc` PROC_* constants, shared across the
Beast Mastery / Marksmanship / Survival rework passes and the pet kit work.

Leading underscore = not loaded as a class file by lib/dsl/registry.py's load_class_package (see
source/classes/README.md), just an importable module - `from . import _masks as m`.

Bit values below are the raw SpellFamilyFlags dword contents (the "final" masked value a row's
SpellClassMask_N / EffectSpellClassMaskX_N column carries), not bit positions. Source:
.agents/plans/hunter-rework/hunter-rework.SHARED.md A3.2 (created in H0 WP-0, append-only; a
renamed or retyped constant is a review blocker).

Never put a "poisoned" bit (SHARED A3.1) on a non-carrier, and no new reader mask may contain
d1 b28 (the pet bit).
"""

# --- d0 (SpellClassMask_1 / EffectSpellClassMaskX_1) ---
AUTO_SHOT = 0x1                      # 75, Wild Quiver Auto Shot 53254
MONGOOSE_BITE = 0x2                  # 1495 only after H0 (Raptor Strike leaves it)
EXPLOSIVE_TRAP_EFFECT = 0x4          # 13812
FREEZING_TRAP_EFFECT = 0x8           # 3355, 60210 - trap-activation key, Glyph of Freezing Trap
FROST_TRAP_AURA = 0x10               # 13810 - trap-activation key
RAPID_FIRE = 0x20                    # poisoned: spell_hun_rapid_recuperation
WING_CLIP = 0x40
TRAP = 0x80                          # every trap place spell, Freezing Arrow, Black Arrow 3674 (until S3)
FEIGN_DEATH = 0x100
CONCUSSIVE_SHOT = 0x200
HUNTERS_MARK = 0x400                 # poisoned: DR / duration / MOD_STALKED readers
ARCANE_SHOT = 0x800
MULTI_SHOT = 0x1000
VOLLEY = 0x2000
SERPENT_STING = 0x4000
SCORPID_STING = 0x8000
TRANQUILIZING_DISTRACTING = 0x10000  # 19801 + 20736 (+ pet Roar of Sacrifice 53480)
AIMED_SHOT = 0x20000                 # poisoned: load fix
SCATTER_SILENCING = 0x40000          # 19503, 37506, 34490
ASPECT_OF_THE_MONKEY = 0x80000       # aspect bit
ASPECT_OF_THE_HAWK = 0x100000        # aspect bit
ASPECT_OF_THE_CHEETAH_PACK = 0x200000  # aspect bit
EYES_OF_THE_BEAST = 0x400000
MEND_PET = 0x800000
REVIVE_PET = 0x1000000
TAMED_PET_PASSIVE_01 = 0x2000000     # .. 07 = 0x80000000 (d0 b25-b31), pet channels
TAMED_PET_PASSIVE_02 = 0x4000000
TAMED_PET_PASSIVE_03 = 0x8000000
TAMED_PET_PASSIVE_04 = 0x10000000
TAMED_PET_PASSIVE_05 = 0x20000000    # backup bit
TAMED_PET_PASSIVE_06 = 0x40000000
TAMED_PET_PASSIVE_07 = 0x80000000    # backup bit

# --- d1 (SpellClassMask_2 / EffectSpellClassMaskX_2) ---
OLD_STEADY_SHOT_NEVER = 0x1          # poisoned: SpellEffects.cpp:672 hardcode, Glyph of Steady Shot
DETERRENCE = 0x2
TAMED_PET_PASSIVE_08 = 0x4           # backup bit
TAMED_PET_PASSIVE_09 = 0x8
TAMED_PET_PASSIVE_10 = 0x10          # backup bit
FEROCIOUS_INSPIRATION_PET = 0x20     # 75593
WILDFIRE_BOMB = 0x40                 # S3
VIPER_STING = 0x80
WYVERN_STING_DOT = 0x100             # 24131
HAWK_PROC = 0x200                    # Quick Shots 6150, rewritten in H0
FIRE_BREATH_PET = 0x400
KILL_COMMAND = 0x800
WYVERN_STING = 0x1000                # poisoned: DR, PvP duration, Noxious Stings
SNAKE_TRAP_EFFECT = 0x2000           # 45145, 57879
DISENGAGE = 0x4000
FLARE = 0x8000
SCARE_BEAST = 0x10000
DISTRACTING_SHOT = 0x20000
ASPECT_OF_THE_VIPER = 0x40000        # aspect bit
MANTIS_STRIKE = 0x80000              # S3 (Counterattack 19306 until then)
MISDIRECTION = 0x100000
TRUESHOT_AURA = 0x200000
ASPECT_OF_THE_WILD = 0x400000        # aspect bit
KILL_SHOT = 0x800000                 # poisoned: +0.4 RAP hardcode
RAPID_KILLING = 0x1000000
BESTIAL_WRATH = 0x2000000
TAR_BOMB = 0x4000000                 # S3
BURNING_TAR = 0x8000000              # S3 (Black Arrow 3674 until then)
PET_ABILITY = 0x10000000             # every pet-cast family-9 spell keeps it; never in a reader mask
DASH_DIVE = 0x20000000
SAVAGE_REND = 0x40000000
EXPLOSIVE_SHOT = 0x80000000          # poisoned: periodic -> 53352 hardcode

# --- d2 (SpellClassMask_3 / EffectSpellClassMaskX_3) ---
CHIMERA_SHOT = 0x1
TRACKING = 0x2
MASTERS_CALL = 0x4
INTIMIDATION = 0x8
ASPECT_OF_THE_BEAST = 0x10           # aspect bit
CLUSTER_BOMBS = 0x20                 # S3
GLAIVE_TOSS = 0x40                   # H0
WILD_QUIVER = 0x80
TRANQUILIZING_SHOT = 0x100
EXPLOSIVE_SHOT_TICK = 0x200          # 53352
CHIMERA_TRIGGERS = 0x400             # backup bit after S2
CHIMERA_SERPENT = 0x800              # 53353
ASPECT_OF_THE_DRAGONHAWK = 0x1000    # aspect bit
DRAGONHAWK_DODGE = 0x2000            # 61848 (inert after H0)
EXPLOSIVE_TRAP_EFFECT_D2 = 0x4000    # trap-activation key
SCATTER_SHOT = 0x8000
RAPTOR_STRIKE = 0x10000
IMMOLATION_TRAP_EFFECT = 0x20000     # trap-activation key
FROST_TRAP_63487 = 0x40000
MASTERS_CALL_TRIGGERS = 0x80000
CALL_STABLED_PET = 0x100000
COMMAND_PRESS = 0x200000             # S1
COMMANDED_PET_SPELL = 0x400000       # S1, always with PET_ABILITY
PET_BASIC_ATTACK = 0x800000          # H0-P, always with PET_ABILITY
STOMP = 0x1000000                    # S1, always with PET_ABILITY
DRAGONHAWK_EXPLOSION = 0x2000000     # H0
VIPER_POISON = 0x4000000             # H0
MARK_PRESS = 0x8000000               # S2
MARK_DOT = 0x10000000                # S2
STEADY_SHOT = 0x20000000             # H0
HALF_VOLLEY = 0x40000000             # S2
GIFT_OF_THE_NAARU = 0x80000000       # racial 59543 (Readiness excludes it by id)

# --- composites (d0, d1, d2) ---
STEADY_SHOT_MASK = (0, 0, STEADY_SHOT)
THREE_STRIKES = (MONGOOSE_BITE, MANTIS_STRIKE, RAPTOR_STRIKE)
ASPECT_SPECIFIC = (0x380000, 0x440000, 0x1010)          # never on a non-aspect (SpellInfo.cpp:2207-2208)
TRAP_ACTIVATION_KEYS = (0x18, 0, 0x24000)               # + Snake Trap 57879 by id (Spell.cpp:2350-2356)
# Pet groups. *_CARRIER = what the carrier spells hold (d1 b28 + the group's d2 bit); never use one as a talent's
# EffectSpellClassMask or a spell_proc family mask, because IsAffected matches on ANY shared bit and d1 b28 would reach
# Growl, Dash, Furious Howl, every command and Stomp. Readers use *_READER (the d2 bit alone). Lint (c), §C7.6.
PET_BASIC_ATTACKS_CARRIER = (0, PET_ABILITY, PET_BASIC_ATTACK)
COMMANDED_PET_SPELLS_CARRIER = (0, PET_ABILITY, COMMANDED_PET_SPELL)
STOMP_CARRIER = (0, PET_ABILITY, STOMP)
PET_BASIC_READER = (0, 0, PET_BASIC_ATTACK)          # PET kit auras 201706-201708, BM Culling the Herd / Improved Viper
COMMANDED_READER = (0, 0, COMMANDED_PET_SPELL)       # BM Phoenix's Plume, Master's Command
STOMP_READER = (0, 0, STOMP)                         # BM Earthshaker
COMMAND_PRESS_READER = (0, 0, COMMAND_PRESS)          # BM Longevity (Command I / II cooldown)
BM_PET_PROC_MASK = (0, 0, COMMANDED_PET_SPELL | PET_BASIC_ATTACK)  # spell_proc family mask, no d1 b28 (BM 2.4)
KC_READER = (0, KILL_COMMAND, 0)                     # BM Focused Fire, Catlike Reflexes, 201812

# --- spell_proc constants (SpellMgr.h) ---
PROC_FLAG_DONE_RANGED_AUTO_ATTACK = 0x40
PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS = 0x100
PROC_FLAG_TAKEN_DAMAGE = 0x100000
PROC_FLAG_DONE_PERIODIC = 0x40000
PROC_FLAG_DONE_TRAP_ACTIVATION = 0x200000
ASPECT_PROC_FLAGS = PROC_FLAG_DONE_RANGED_AUTO_ATTACK | PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS  # 0x140
PROC_SPELL_PHASE_CAST = 0x1
PROC_SPELL_PHASE_HIT = 0x2
PROC_SPELL_PHASE_FINISH = 0x4
PROC_HIT_NORMAL = 0x1
PROC_HIT_CRITICAL = 0x2
PROC_ATTR_TRIGGERED_CAN_PROC = 0x2
