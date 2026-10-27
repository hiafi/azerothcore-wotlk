"""
Rogue - named SpellFamilyFlags (SpellClassMask_{1,2,3} / EffectSpellClassMask{A,B,C}_{1,2,3}) constants for
SpellClassSet 8, shared across the RG0a / RG0b shared stages and the three spec stages.

Leading underscore = not loaded as a class file by lib/dsl/registry.py's load_class_package (see
source/classes/README.md), just an importable module - `from . import _masks as m`.

Values are the raw SpellFamilyFlags dword contents (the "final" masked value a row's SpellClassMask_N /
EffectSpellClassMaskX_N column carries), not bit positions. Source: .agents/plans/rogue-rework/
rogue-rework.RG0a-HANDOFF.md "Family bits" (FAMILY-BITS.md section 5, corrected by handoff C1). Append-only: a
renamed or retyped constant is a review blocker. `FORBIDDEN_*` are the "never" bits (FAMILY-BITS section 3.3);
test_rogue_rg0a.py asserts none of them sits on an RG0a row.
"""

# --- d0 (SpellClassMask_1 / EffectSpellClassMaskX_1) ---
GARROTE = 0x100                          # d0 b8 (stock; Wound Poison's damage-taken reader mask)
INSTANT_POISON = 0x2000                  # d0 b13 (stock payload 8680 identity bit)
CRIPPLING_POISON = 0x4000                # d0 b14 (stock payload 3409 identity bit)
MIND_NUMBING_POISON = 0x8000             # d0 b15 (stock payload 5760 identity bit)
DEADLY_POISON = 0x10000                  # d0 b16 (ONLY payload 2818: AURA_STATE_DEADLY_POISON + Envenom's dose key)
RUPTURE = 0x100000                       # d0 b20 (ONLY Rupture; Wound Poison's damage-taken reader mask)
ENVENOM = 0x800000                       # d0 b23 (stock Envenom 32645)
WOUND_POISON = 0x10000000                # d0 b28 (stock payload 13218 identity bit)

# --- d1 (SpellClassMask_2 / EffectSpellClassMaskX_2) ---
ENVENOM_D1 = 0x8                         # d1 b3 (stock Envenom 32645; Mutilate shares the bit, SpellEffects.cpp dose key)
ANESTHETIC_POISON = 0x10                 # d1 b4 (stock payload 26688 identity bit)
POISON_GROUP = 0x80000                   # d1 b19 (the poison group: all six payloads + Envenom; damage readers only)

# --- d2 (SpellClassMask_3 / EffectSpellClassMaskX_3) ---
LETHAL_AURA = 0x2                        # d2 b1 (Lethal poison self auras 203701-203703; Envenom's +15, S1 Improved Poisons)
CRIPPLING_AURA = 0x4                     # d2 b2 (Crippling poison self aura 203704)
NONLETHAL_AURA = 0x8                     # d2 b3 (Mind-numbing + Anesthetic self auras 203705-203706)

# --- composites ---
# Wound Poison's aura-271 reader mask (MOD_DAMAGE_FROM_CASTER): Rupture + Garrote, d0 only.
WOUND_BLEED_READ = (RUPTURE | GARROTE, 0, 0)
# Envenom's reader on the 107 (CHANCE_OF_SUCCESS) buff: every Lethal poison self aura.
ENVENOM_CHANCE_READ = (0, 0, LETHAL_AURA)

# --- "never" bits (FAMILY-BITS section 3.3; T1 lints the first three on custom ids) ---
# d0 b11, d0 b22, d0 b25 on any RG0a row; d0 b16 on anything but 2818; d0 b20 on anything but Rupture;
# d1 b1, b2, b3 on anything but Mutilate / Envenom; a non-damage SpellMod on d1 b19.
FORBIDDEN_D0 = 0x800 | 0x400000 | 0x2000000
FORBIDDEN_D1 = 0x2 | 0x4 | 0x8
FORBIDDEN_D0_EXCEPT_DEADLY = DEADLY_POISON     # only payload 2818 may carry it
FORBIDDEN_D0_EXCEPT_RUPTURE = RUPTURE          # only Rupture may carry it
