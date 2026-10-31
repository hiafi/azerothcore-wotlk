"""
Warrior - named SpellFamilyFlags (SpellClassMask_{1,2,3} / EffectSpellClassMaskX_{1,2,3}) constants for
SpellClassSet 4, shared across the W0a / W0b shared stages and the three spec stages.

Leading underscore = not loaded as a class file by lib/dsl/registry.py's load_class_package (see
source/classes/README.md), just an importable module - `from . import _masks as m`.

Values are the raw SpellFamilyFlags dword contents (the "final" masked value a row's SpellClassMask_N /
EffectSpellClassMaskX_N column carries), not bit positions. Source: .agents/plans/warrior-rework/
warrior-rework.FAMILY-BITS.md section 5 (the allocation) and section 3.3 (the "never take" bits), as registered by
.agents/plans/warrior-rework/warrior-rework.T1-HANDOFF.md WP2. Append-only: a renamed or retyped constant is a review
blocker. `FORBIDDEN_*` are the "never" bits; lib/lint.py's WARRIOR_FAMILY_RULES holds the same values as literals (a
lint must not import the thing it checks) and lib/test_warrior_family_rules.py asserts the two agree.

All new bits go in d2: no stock reader (talent, glyph, set, item) masks d2 below b31, so a new bit cannot collide with
a stale mask. A SpellMod on effect 1 reading a d2 bit is `EffectSpellClassMaskA_3`, on effect 2
`EffectSpellClassMaskB_3`, and so on; `SpellClassMask_3` is the carrier column. Keep every new spell's
`SpellClassSet = 4`.
"""

# --- d2 (SpellClassMask_3 / EffectSpellClassMaskX_3): the FAMILY-BITS section 5 allocation ---
HEROIC_LEAP = 0x1                        # d2 b0 (cast, landing strike, outer-ring strike)
COLOSSUS_SMASH = 0x2                     # d2 b1 (button, hit and the debuff aura, unless C1 splits the debuff off)
RAMPAGE = 0x4                            # d2 b2 (cast + 4 strikes)
DAMAGING_ABILITY_GROUP = 0x8             # d2 b3 (R1: the warrior damaging-ability group)
# S3 (Fury): the one read-only sentinel. Shredding Blows' buffs 204644-204646 (aura 280) read this bit so that only
# white swings (null spell, EquippedItemClass -1) get the armor penetration: no spell carries d2 b8, so no ability
# ever matches it. A "never carried" bit: the scope audit and the lint must not "fix" it, nothing may carry it.
SHREDDING_SENTINEL = 0x100               # d2 b8, never carried by any spell (WP-BRIEF S3 D27)

# Reserved, not named until a stage takes them (a name here would read as taken):
#   d2 b4 (0x10)  Colossus Smash debuff, if C1 splits it from the button
#   d2 b5 (0x20)  Avatar
#   d2 b6 (0x40)  Skull Banner
#   d2 b7 (0x80)  the rage-cost group
# d2 b8-b30 are spare (W0a deleted the P0 spike that held b28-b30); nothing here names them yet. Never d2 b31.

# --- "never take" bits (FAMILY-BITS section 3.3; lib/lint.py WARRIOR_FAMILY_RULES bans them on custom carriers) ---
# d0 b0, b1, b17, b24: Charge's bit (and its readers: Improved Charge, Glyph of Charge, Juggernaut's proc row), the DR
#   bits d0 b1 / b24, the "Shout" CC marker d0 b17.
# d1 b5, b6: the other "Shout" CC marker (Piercing Howl), Devastate's Sunder cast.
# d2 b31: Gift of the Naaru (all seven classes) and Shadow Resistance 59221.
FORBIDDEN_D0 = 0x1 | 0x2 | 0x20000 | 0x1000000    # 0x01020003
FORBIDDEN_D1 = 0x20 | 0x40                          # 0x60
FORBIDDEN_D2 = 0x80000000

# Role bits the lint cannot express (a carrier list is all-or-nothing); W0b and the spec stages pin them with targeted
# tests: d0 b7 only Thunder Clap and its echo, d0 b10 only Revenge, d1 b8 Victory Rush damage / glyph, d1 b9 (+ category
# 1209) Shield Slam, d1 b18 the Victorious aura state, d1 b21 (a carrier counts as Dazed for Heroic
# Strike's bonus, spell_warrior.cpp:1080), d0 b23 the stances.
