"""
Death Knight - named SpellFamilyFlags (SpellClassMask_{1,2,3} / EffectSpellClassMask{A,B,C}_{1,2,3}) constants
for SpellClassSet 15, shared across the DK0a / DK0b shared stages and the three spec stages.

Leading underscore = not loaded as a class file by lib/dsl/registry.py's load_class_package (see
source/classes/README.md), just an importable module - `from . import _masks as m`.

Values are the raw SpellFamilyFlags dword contents (the "final" masked value a row's SpellClassMask_N /
EffectSpellClassMaskX_N column carries), not bit positions. Source: .agents/plans/death-knight-rework/
death-knight-rework.DK0-HANDOFF.md "Family bits" (FAMILY-BITS.md section 5 + PLAN section 4). Append-only: a
renamed or retyped constant is a review blocker. `FORBIDDEN_*` are the "never" bits (FAMILY-BITS section 3.3);
test_deathknight_dk0a.py asserts none of them sits on a DK0a row.
"""

# --- d0 (SpellClassMask_1 / EffectSpellClassMaskX_1) ---
DEATH_STRIKE = 0x10                      # d0 b4 (stock; Threat of Thassarian, Death Strike readers)
ERW = 0x4000                             # d0 b14 (stock Empower Rune Weapon)
BLOOD_PRESENCE = 0x800000                # d0 b23 (stock)
HEART_STRIKE = 0x1000000                 # d0 b24 (stock; every Heart Strike reader masks it)
RUNE_TAP = 0x8000000                     # d0 b27 (stock)

# --- d1 (SpellClassMask_2 / EffectSpellClassMaskX_2) ---
FROST_STRIKE = 0x4                       # d1 b2 (stock)
LICHBORNE = 0x10                         # d1 b4 (stock)
BONE_SHIELD = 0x40                       # d1 b6 (stock)
PESTILENCE = 0x10000                     # d1 b16 (stock)
OBLITERATE = 0x20000                     # d1 b17 (stock; Threat of Thassarian, Deathchill, Killing Machine; DK0b)
AMZ = 0x80000                            # d1 b19 (stock Anti-Magic Zone 51052 + 50461)
BLOOD_PLAGUE_DISEASE = 0x2000000         # d1 b25 (stock; disease readers, Runic Focus; DK0b)
FROST_FEVER_DISEASE = 0x4000000          # d1 b26 (stock; disease readers, Runic Focus; DK0b)

# --- d2 (SpellClassMask_3 / EffectSpellClassMaskX_3) ---
DEATH_STRIKE_HEAL = 0x4                  # d2 b2 (stock 45470)
ROT_DAMAGE = 0x800                       # d2 b11 (N4 Rot damage group; DK0b Boiling Blight burst)
DEATHS_CARESS = 0x1000                   # d2 b12 (N5 Death's Caress, new in DK0a)

# --- Reserved for spec stages (do not take) ---
MARROWREND_RESERVED = 0x100              # d2 b8 (S1)
GLACIAL_ADVANCE_RESERVED = 0x200         # d2 b9 (S2)
BREATH_RESERVED = 0x400                  # d2 b10 (S2)
OTHER_MAGIC_DAMAGE_RESERVED = 0x2000     # d2 b13 (R1)
LESSER_GHOUL_RESERVED = 0x4000           # d2 b14 (R2, S3)
SELF_HEAL_GROUP_RESERVED = 0x8000        # d2 b15 (R3, S1)

# --- Never (FORBIDDEN_*): FAMILY-BITS section 3.3 ---
FORBIDDEN_D0_B0 = 0x1                    # strike family: Threat of Thassarian only on purpose
FORBIDDEN_D0_B6 = 0x40                   # server Icy Touch alias
FORBIDDEN_D0_B17 = 0x20000
FORBIDDEN_D0_B22 = 0x400000              # Blood Strike's core block: never on a weapon strike
FORBIDDEN_D1_B10 = 0x400                 # Orc racial pet bit (readers)
FORBIDDEN_D1_B11 = 0x800                 # magic-class GCD spells
FORBIDDEN_D1_B23 = 0x800000              # Orc racial pet bit
FORBIDDEN_D1_B24 = 0x1000000             # Orc racial pet bit
FORBIDDEN_D2_B1 = 0x2                    # only a real disease DoT
FORBIDDEN_D2_B31 = 0x80000000

# Per-dword never-lists for the DK0a test (new spells). Stock-kept bits are exempt per row in the test.
FORBIDDEN_D0 = FORBIDDEN_D0_B6 | FORBIDDEN_D0_B17 | FORBIDDEN_D0_B22
FORBIDDEN_D1 = FORBIDDEN_D1_B10 | FORBIDDEN_D1_B11 | FORBIDDEN_D1_B23 | FORBIDDEN_D1_B24
FORBIDDEN_D2 = FORBIDDEN_D2_B1 | FORBIDDEN_D2_B31
