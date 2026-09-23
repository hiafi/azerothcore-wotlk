"""
Priest - named SpellFamilyFlags (SpellClassMask_{1,2,3} / EffectSpellClassMask{A,B,C}_{1,2,3})
constants, shared across the Disc/Holy/Shadow rework passes.

Leading underscore = not loaded as a class file by lib/dsl/registry.py's load_class_package (see
source/classes/README.md), just an importable module - `from ._masks import PWS, ...`.

Bit values below are the raw SpellFamilyFlags dword contents (already the "final" masked value a
row's SpellClassMask_N / EffectSpellClassMaskX_N column would carry), not bit positions. Sourced
from the existing stock priest rows in priest_spells.py/priest_trigger_spells.py (dword 1/2/3 stock
bits) and .agents/plans/priest-rework/priest-rework.PLAN.md §4.4 (dword 3 custom-spell bits, one
named constant per row of that table).
"""

# --- dword 1 (SpellClassMask_1 / EffectSpellClassMaskX_1) ---
PWS = 1
RENEW = 64
SMITE = 128
POH = 512
FLASH_HEAL = 2048
GREATER_HEAL = 4096
MIND_BLAST = 8192
SWP = 32768
HOLY_FIRE = 1048576
HOLY_NOVA_DMG = 4194304
# 58381, the helper spell Mind Flay's PERIODIC_TRIGGER_SPELL_WITH_VALUE effect fires once per tick -
# the spell that actually deals Mind Flay damage, and so the SpellInfo any "Mind Flay damage" proc
# or SpellMod is matched against. Same "the tick is a different row from the button" shape as
# MIND_SEAR_TICK below. 15407 itself carries only the dword-3 MIND_FLAY bit, so a modifier scoped to
# dword 3 alone never reaches the player's own Mind Flay damage.
MIND_FLAY_TICK = 8388608
DESPERATE_PRAYER = 16777216
DEVOURING_PLAGUE = 33554432
HOLY_NOVA_HEAL = 134217728
COH = 268435456
WEAKENED_SOUL = 536870912
# Not in PLAN §4.4's list (that table only covers dword 3's free/custom bits) - this is Lightwell's
# own existing stock bit (priest_spells.py's lightwell_724 raw_overrides SpellClassMask_1), needed
# here because PRIEST_HEAL_MASK below includes Lightwell per DISC.md WP-0 step 2.
LIGHTWELL = 1073741824

# --- dword 2 (SpellClassMask_2 / EffectSpellClassMaskX_2) ---
DISPEL_MAGIC = 1
SWD = 2
BINDING_HEAL = 4
POM = 32
MASS_DISPEL = 128
VT = 1024
PENANCE_HEAL_BOLT = 65536
DISPERSION = 262144
MIND_SEAR_TICK = 524288  # 49821, the spell that actually deals damage
MIND_SEAR = 1048576  # 48045, the cast
DIVINE_HYMN = 4194304
PENANCE = 8388608  # the (8388608,0,0) "Mind Sear" a naive family scan shows is NPC spell 32000, not this

# --- dword 3 (SpellClassMask_3 / EffectSpellClassMaskX_3) ---
MIND_FLAY = 64
PENANCE_BOLT = 128
PRIEST_GENERIC = 1024
# PLAN §4.4 - one named constant per row, in bit order.
DIVINE_STAR = 0x00010000  # bit 16 - Divine Star 200133 and its pulse 200134
HALO = 0x00020000  # bit 17 - Halo 200135 and its pulse 200136
LEAP_OF_FAITH = 0x00040000  # bit 18 - Leap of Faith 200137 (+ jump 200138)
PW_BARRIER = 0x00080000  # bit 19 - Power Word: Barrier 200132
VOID_ERUPTION = 0x00100000  # bit 20 - Void Eruption 200139
SPIRIT_SHELL = 0x00200000  # bit 21 - Spirit Shell 200166
GREATER_PWS = 0x00400000  # bit 22 - Greater Power Word: Shield 200155
HW_SERENITY = 0x00800000  # bit 23 - Holy Word: Serenity 200197
HW_SANCTIFY = 0x01000000  # bit 24 - Holy Word: Sanctify 200198
HW_CHASTISE = 0x02000000  # bit 25 - Holy Word: Chastise 200223
APOTHEOSIS = 0x04000000  # bit 26 - Apotheosis 200225
CALL_OF_THE_VOID = 0x08000000  # bit 27 - Call of the Void 200248
SURRENDER = 0x10000000  # bit 28 - Surrender to Madness 200269
ANGELIC_FEATHER = 0x20000000  # bit 29 - Angelic Feather 200130/200141 (reserved, unused for now)
# bits 30, 8, 1 (dword 3) and dword 2 bit 4 are spare (PLAN §4.4).

# OR of every priest healing spell's family bit (Renew, PoH, FH, GH, Holy Nova heal, Desperate
# Prayer, CoH, Binding Heal, PoM, Penance heal bolt, Divine Hymn, Divine Star, Halo, Serenity,
# Sanctify, Lightwell), as a (dword1, dword2, dword3) tuple - Holy uses this heavily (PLAN §4.4).
PRIEST_HEAL_MASK = (
    RENEW | POH | FLASH_HEAL | GREATER_HEAL | HOLY_NOVA_HEAL | DESPERATE_PRAYER | COH | LIGHTWELL,
    BINDING_HEAL | POM | PENANCE_HEAL_BOLT | DIVINE_HYMN,
    DIVINE_STAR | HALO | HW_SERENITY | HW_SANCTIFY,
)
