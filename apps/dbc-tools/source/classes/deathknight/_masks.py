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

# --- DK0b composites ---
# Runic Focus 61455: reader bits added on top of its stock mask (disease crits, Boiling Blight burst, Death's Caress).
RUNIC_FOCUS_READ_ADD = (0, BLOOD_PLAGUE_DISEASE | FROST_FEVER_DISEASE, ROT_DAMAGE | DEATHS_CARESS)
# Boiling Blight's proc mask: the two disease DoTs only.
DISEASES = (0, BLOOD_PLAGUE_DISEASE | FROST_FEVER_DISEASE, 0)
# Frost Vulnerability 51714 reader mask (replaces the stock 0x402 / 0x4048007 set): every Frost-school DK spell
# (DK0b-0VERIFY item 8: a zero mask would match every school, so it is a union instead). Icy Touch, Mind Freeze,
# Chains of Ice, Frozen Rune Weapon / Frost Strike, Howling Blast, Hungering Cold, Icy Clutch, Deathchill, Frost Fever.
FROST_VULN_READ = (0x2 | 0x4 | 0x400 | 0x200000, 0x1 | 0x2 | 0x4 | 0x9000 | 0xC000 | 0x40000 | FROST_FEVER_DISEASE, 0)

# --- S1 (Blood) ---
DEATH_AND_DECAY = 0x20                   # d0 b5 (stock 43265; Crimson Scourge's free-cast SpellMod reads it)
BLOOD_BOIL = 0x40000                     # d0 b18 (stock 48721)
DEATH_AND_DECAY_TICK = 0x8               # d2 b3 (stock 52212; Sanguine Ground's SpellMod reads it)
MARROWREND = 0x100                       # d2 b8 (S1 Marrowrend 203123; was MARROWREND_RESERVED)
BLOOD_OTHER_MAGIC = 0x2000               # d2 b13 (R1: Blood Nova eruption, Bonestorm tick; Runic Focus reads it)
DK_SELF_HEAL = 0x8000                    # d2 b15 (R3: own self-heal group, C++ readers only; was SELF_HEAL_GROUP_RESERVED)
# Subversion crit effect: Heart Strike, Marrowrend, Obliterate, Scourge Strike (+ the stock d2 b7 Scourge Strike component).
SUBVERSION_READ = (HEART_STRIKE, OBLITERATE | 0x8000000, 0x80 | MARROWREND)
# Might of Mograine: Death Strike, Blood Boil, Heart Strike, Marrowrend (Blood Strike's d0 b22 dropped).
MIGHT_OF_MOGRAINE_READ = (DEATH_STRIKE | BLOOD_BOIL | HEART_STRIKE, 0, MARROWREND)
# Sudden Doom spell_proc family mask: Heart Strike + Blood Boil (was 0x1400000: Heart Strike + Blood Strike's b22 + b20).
SUDDEN_DOOM_PROC = (HEART_STRIKE | BLOOD_BOIL, 0, 0)

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

# --- S2 (Frost; S2-HANDOFF section 5) ---
GLACIAL_ADVANCE = 0x200                  # d2 b9 (S2 Glacial Advance cast + Glacial Eruption; was GLACIAL_ADVANCE_RESERVED)
BREATH = 0x400                           # d2 b10 (S2 Breath of Sindragosa tick; was BREATH_RESERVED)
FROST_OTHER_MAGIC = 0x10000              # d2 b16 (S2 Avalanche + Hungering Cold storm tick; Runic Focus + Razorice read it)
HOWLING_BLAST = 0x2                      # d1 b1 (stock 49184; Guile HB, Deathchill, Merciless, Rime readers)
ICY_TOUCH = 0x2                          # d0 b1 (stock 45477)
CHAINS_OF_ICE = 0x4                      # d0 b2 (stock 45524)
PLAGUE_STRIKE = 0x1                      # d0 b0 (stock 45462; Threat of Thassarian, Gravefrost)
MIND_FREEZE = 0x400                      # d0 b10 (stock 47528; Endless Winter r2 cost mod)
ICEBOUND_FORTITUDE = 0x100000            # d0 b20 (stock; Guile eff1)
HORN_OF_WINTER = 0x40000000              # d1 b30 (stock 57330; Frostwyrm's Wrath CAST proc)

# Razorice Frost Vulnerability 51714 reader (S2): FROST_VULN_READ + the S2 magic bits (d2 b9 Glacial Advance, b10 Breath, b16 other magic).
FROST_VULN_READ_S2 = (FROST_VULN_READ[0], FROST_VULN_READ[1], GLACIAL_ADVANCE | BREATH | FROST_OTHER_MAGIC)
# Runic Focus 61455 d2 additions in S2 (magic-class only; melee-class strikes already crit 200%).
RUNIC_FOCUS_READ_S2 = (0, 0, GLACIAL_ADVANCE | BREATH | FROST_OTHER_MAGIC)
KILLING_MACHINE_READ = (0, OBLITERATE, 0)
DEATHCHILL_READ = (ICY_TOUCH, HOWLING_BLAST | FROST_STRIKE | OBLITERATE, 0)
GUILE_READ = (0, FROST_STRIKE | OBLITERATE, 0)
GUILE_HB_READ = (0, HOWLING_BLAST, 0)
# Threat of Thassarian proc: Heart Strike + Plague Strike + Death Strike (d0), Frost Strike + Obliterate (d1).
TOT_PROC = (HEART_STRIKE | PLAGUE_STRIKE | DEATH_STRIKE, FROST_STRIKE | OBLITERATE, 0)
CHILL_OF_THE_GRAVE_PROC = (0, HOWLING_BLAST | OBLITERATE, 0)
UNLEASHED_FRENZY_PROC = (0, FROST_STRIKE, GLACIAL_ADVANCE)
OBLITERATION_PROC = (0, HOWLING_BLAST | FROST_STRIKE, GLACIAL_ADVANCE)
IMPROVED_ICY_TOUCH_RANGE = (ICY_TOUCH | CHAINS_OF_ICE, HOWLING_BLAST, 0)
GRAVEFROST_READ = (HEART_STRIKE | PLAGUE_STRIKE, 0, 0)

# --- S3 (Unholy; S3-HANDOFF section 5) ---
LESSER_GHOUL = 0x4000                    # d2 b14 (S3 Lesser Ghoul summon 203469; Night of the Dead's duration mod reads it; was LESSER_GHOUL_RESERVED)
UNHOLY_OTHER_MAGIC = 0x20000             # d2 b17 (S3 On a Pale Horse damage 203477; Runic Focus reads it)
SCOURGE_STRIKE = 0x08000000              # d1 b27 (stock 55090; Subversion, GCD-haste 201565, Outbreak, Vicious Strikes, Dirge, Desecration)
SCOURGE_STRIKE_SHADOW = 0x80             # d2 b7 (stock 70890, Scourge Strike's Shadow part)
DEATH_COIL = 0x2000                      # d0 b13 (stock 47541 castable; Doomed Bidding CAST proc, Harbinger cost mod)
DEATH_COIL_DAMAGE = 0x1                  # d2 b0 (stock 47632 damage missile; Unholy Blight's HIT proc)
RAISE_DEAD = 0x1000                      # d0 b12 (stock 46584; Master of Ghouls)
ARMY_OF_THE_DEAD = 0x800                 # d0 b11 (stock 42650; Night of the Dead)
SUMMON_GARGOYLE = 0x80                   # d1 b7 (stock 49206)

# Runic Focus 61455 d2 addition in S3 (magic-class only).
RUNIC_FOCUS_READ_S3 = (0, 0, UNHOLY_OTHER_MAGIC)
# Plague Strike + Scourge Strike (Outbreak, Vicious Strikes crit, Dirge, Desecration).
PS_SS_READ = (PLAGUE_STRIKE, SCOURGE_STRIKE, 0)
# Vicious Strikes: Plague Strike + Scourge Strike + Scourge Strike's Shadow part 70890.
VICIOUS_READ = (PLAGUE_STRIKE, SCOURGE_STRIKE, SCOURGE_STRIKE_SHADOW)
