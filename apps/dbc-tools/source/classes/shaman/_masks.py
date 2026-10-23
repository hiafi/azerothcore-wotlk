"""
Shaman - named SpellFamilyFlags (SpellClassMask_{1,2,3} / EffectSpellClassMask{A,B,C}_{1,2,3}) constants
for SpellClassSet 11, shared across the SH0a / SH0b shared stages and the three spec stages.

Leading underscore = not loaded as a class file by lib/dsl/registry.py's load_class_package (see
source/classes/README.md), just an importable module - `from . import _masks as m`.

Values are the raw SpellFamilyFlags dword contents (the "final" masked value a row's SpellClassMask_N /
EffectSpellClassMaskX_N column carries), not bit positions. Source: .agents/plans/shaman-rework/
shaman-rework.SH0-HANDOFF.md "Family bits" (FAMILY-BITS.md section 5 + PLAN section 4). Append-only: a
renamed or retyped constant is a review blocker. `FORBIDDEN_*` are the "never" bits; test_shaman_sh0a.py
asserts none of them sits on an SH0a row (some are allowed on specific rows, named per constant).
"""

# --- d0 (SpellClassMask_1 / EffectSpellClassMaskX_1) ---
EARTHEN_WALL_SUMMON = 0x8                # d0 b3 (+ SUMMON_D0_B29); SH0b
MAGMA_SUMMON_D0_B12 = 0x1000             # d0 b12, stock Magma summon identity bit (FAMILY-BITS C4; SH0b)
MAGMA_PULSE_B2 = 0x4                     # d0 b2, stock Magma pulse 8187 (SH0b)
HEALING_STREAM_HEAL = 0x2000             # d0 b13 (SH0b)
TREMOR_SUMMON = 0x8000                   # d0 b15, added to 8143's d0 b29 (SH0b)
CLEANSING_SUMMON = 0x10000               # d0 b16, added to 8170's d0 b29 (SH0b)
FLAMETONGUE_ATTACK = 0x200000            # d0 b21 (H8 Elemental Focus exclusion)
ROCKBITER = 0x400000                     # d0 b22 (Rockbiter 8017; inert without effect 54)
WINDFURY_ATTACK = 0x800000               # d0 b23 (H7 Flurry, Spirit Weapons); MH and OH
FROSTBRAND_ATTACK = 0x1000000            # d0 b24 (H8 Elemental Focus exclusion)
MANA_TIDE_RESERVED = 0x2000000           # d0 b25, reserved for the Restoration stage
SUMMON_D0_B29 = 0x20000000               # d0 b29: summon-family bit (Earthen Wall, Windwalk, Capacitor, elementals)
SEARING_MAGMA_BOLT = 0x40000000          # d0 b30 (Searing bolt; Magma pulse adds MAGMA_PULSE_B2)

# --- d1 (SpellClassMask_2 / EffectSpellClassMaskX_2) ---
STORM_ELEMENTAL_SUMMON = 0x100           # d1 b8 (SH0b)
EARTHLIVING_AURA = 0x100000              # d1 b20 (Earthliving aura 51730, R4)
WATER_ELEMENTAL_SUMMON = 0x200000        # d1 b21 (SH0b)
EARTH_ELEMENTAL_SUMMON = 0x400000        # d1 b22 (stock 2062)
FIRE_ELEMENTAL_SUMMON = 0x800000         # d1 b23 (stock 2894)

# --- d2 (SpellClassMask_3 / EffectSpellClassMaskX_3) ---
EARTHBIND_ROOT = 0x20                    # d2 b5 (Earthbind 2484 keeps it; new root adds ROOT_DR)
ROOT_DR = 0x4000                         # d2 b14: controlled-root DR, roots only
EARTHEN_WALL_SHIELD = 0x8000             # d2 b15 (SH0b)
LIVING_EARTH_RESERVED = 0x10000          # d2 b16, reserved for the Enhancement stage
IMBUE_AURA = 0x20000                     # d2 b17: Flametongue / Frostbrand / Windfury auras (8024 / 8033 / 8232)
GUST_RESERVED = 0x40000                  # d2 b18, reserved for the Enhancement stage
EARTHQUAKE = 0x80000                     # d2 b19 (SH0b)
ELEMENTAL_BLAST = 0x100000               # d2 b20 (SH0b)
HEALING_RAIN = 0x200000                  # d2 b21 (SH0b)
TORRENT_RESERVED = 0x400000              # d2 b22, reserved
CHAIN_HEAL_TOTEM_RESERVED = 0x800000     # d2 b23, reserved
WATER_BOLT_HEAL = 0x1000000              # d2 b24 (SH0b)
WATER_BOLT_DAMAGE = 0x2000000            # d2 b25 (SH0b)
EM_HASTE_RESERVED = 0x4000000            # d2 b26, reserved for the Elemental stage
EM_HASTE = EM_HASTE_RESERVED             # d2 b26, Elemental Mastery haste 64701 (S1a)

# --- Never (FORBIDDEN_*): A6's test asserts none sits on an SH0a row ---
# Allowed only on stock shields: d1 b5, d1 b10, d0 b10.
FORBIDDEN_D0_B0 = 0x1                    # Lightning Bolt
FORBIDDEN_D0_B1 = 0x2                    # Chain Lightning
FORBIDDEN_D0_B10 = 0x400                 # stock shields (+ NO_THREAT readers)
FORBIDDEN_D0_B14 = 0x4000
FORBIDDEN_D0_B28 = 0x10000000            # Flame Shock
FORBIDDEN_D1_B4 = 0x10                   # magic-GCD haste (gcd_haste)
FORBIDDEN_D1_B5 = 0x20                   # stock shields
FORBIDDEN_D1_B10 = 0x400                 # stock shields
FORBIDDEN_D1_B11 = 0x800                 # never on imbues
FORBIDDEN_D1_B12 = 0x1000                # Lava Burst
FORBIDDEN_D1_B17 = 0x20000               # magic-GCD haste (gcd_haste)
FORBIDDEN_D1_B24 = 0x1000000             # magic-GCD haste (gcd_haste)
FORBIDDEN_D2_B2 = 0x4                    # magic-GCD haste (gcd_haste)
FORBIDDEN_D2_B11 = 0x800
FORBIDDEN_D2_B31 = 0x80000000

# Per-dword never-lists for the SH0a test (new spells and imbue auras).
FORBIDDEN_D0 = (FORBIDDEN_D0_B0 | FORBIDDEN_D0_B1 | FORBIDDEN_D0_B10 | FORBIDDEN_D0_B14 | FORBIDDEN_D0_B28)
FORBIDDEN_D1 = (FORBIDDEN_D1_B4 | FORBIDDEN_D1_B5 | FORBIDDEN_D1_B10 | FORBIDDEN_D1_B11 | FORBIDDEN_D1_B12
                | FORBIDDEN_D1_B17 | FORBIDDEN_D1_B24)
FORBIDDEN_D2 = (FORBIDDEN_D2_B2 | FORBIDDEN_D2_B11 | FORBIDDEN_D2_B31)

# --- S2a (Restoration) aliases for the reserved bits ---
TORRENT = TORRENT_RESERVED                       # d2 b22, Healing Rain torrent heal
UNDULATING_HEAL = CHAIN_HEAL_TOTEM_RESERVED      # d2 b23, Undulating Currents Totem heal
MANA_TIDE_SUMMON = MANA_TIDE_RESERVED            # d0 b25, Mana Tide Totem summon
MINOR_HEAL = 0x8000000                           # d2 b27, Purification reach: Totemic Focus placement heal + Nature's Guardian heal
TIDAL_FORCE_CAST = 0x10000000                    # d2 b28, the Tidal Force castable 202654 (Tidal Mastery's cooldown cut)

# --- S3a (Enhancement) aliases for the reserved bits ---
LIVING_EARTH = LIVING_EARTH_RESERVED             # d2 b16, Living Earth castable 202361 (Guardian Totems absorb mod)
GUST = GUST_RESERVED                             # d2 b18, Gust 202391 / splash 202392 (Improved Windfury)
ENH_SPELL_HIT = 0x20000000                       # d2 b29, Flame Burst / Storm Burst / Blizzard tick (Improved Stormstrike aura 271 mask)
