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

# --- RG0b (append-only): stock identities the shared stage reads or rewrites ---
SINISTER_STRIKE = 0x2                    # d0 b1 (stock 1752)
BACKSTAB = 0x4                           # d0 b2 (stock 53)
AMBUSH = 0x200                           # d0 b9 (stock 8676)
CHEAP_SHOT = 0x400                       # d0 b10 (stock 1833)
FEINT = 0x8000000                        # d0 b27 (stock 1966; Bloodfang 5P reader later)
SHIV = 0x20000000                        # d0 b29 (stock Shiv's identity, carried by the new Shiv 203725)
GHOSTLY_STRIKE = 0x40000000              # d0 b30 (stock 14278, minus b26)
GHOSTLY_STRIKE_DAGGER = 0x4000000        # d0 b26 (the dagger +50% hardcode; DROPPED from Ghostly Strike by RG0b)
DEADLY_THROW_D1 = 0x1                    # d1 b0 (stock 26679)
FAN_OF_KNIVES_D1 = 0x40000               # d1 b18 (stock 51723; kept on purpose, the dagger +50% hardcode)
FORBIDDEN_DAGGER_D0 = 0x6000000          # d0 b25 | b26: the dagger hardcode bits, never on a new RG0b row
FORBIDDEN_DAGGER_D1 = 0x40000            # d1 b18

# --- S1 Assassination (append-only; S1-HANDOFF section 5, S1a WP-BRIEF) ---
# Stock identities the S1 readers name (no new carrier).
GOUGE = 0x8                              # d0 b3 (stock 1776)
EVISCERATE = 0x20000                     # d0 b17 (ONLY Eviscerate 2098; Seal Fate / Cold Blood readers)
RIPOSTE_D1 = 0x100                       # d1 b8 (stock 14251; Cold Blood / Find Weakness readers)
# New d2 bits (carriers in the comment; the WP-BRIEF bit table is the authority).
KINGSBANE_DOT = 0x200                    # d2 b9 (203842)
POISON_STRIKE = 0x400                    # d2 b10 (Kingsbane hands 203840 / 203841; NOT Blindside's 203832, WP-BRIEF R9)
DOOMBLADE = 0x800                        # d2 b11 (203829 bleed, 203830 tick)
SHATTERING_VIAL = 0x2000                 # d2 b13 (203836)
POISON_BOMB = 0x4000                     # d2 b14 (203807, 203835)
FINISHER_GROUP = 0x40000                 # d2 b18 (2098, 5171, 8647, 1943, 408, 26679, 32645; S2/S3 add theirs)
DIRECT_BUILDER_GROUP = 0x80000           # d2 b19 (1752, 53, 8676, 1776, 14278, 203725: single-strike builders only)
MUTILATE_HANDS = 0x100000                # d2 b20 (203827, 203828)
GHOSTLY_STRIKE_ID = 0x200000             # d2 b21 (14278, beside d0 b30)
KINGSBANE_PARENT = 0x400000              # d2 b22 (203822 only; Cold Blood's RANGE reader, S1a review M1)

# --- S1 reader composites, (d0, d1, d2) ---
MUTILATE_HAND_BITS = (0, 0, MUTILATE_HANDS)
# Lethality pct CRIT_DAMAGE_BONUS (U11, U16): single-strike builders (Ambush and Gouge included), Mutilate hands, Fan of
# Knives (51723 + 52874), Kingsbane hands, Instant and Wound Poison hits.
LETHALITY_READ = (
    INSTANT_POISON | WOUND_POISON,
    FAN_OF_KNIVES_D1,
    DIRECT_BUILDER_GROUP | MUTILATE_HANDS | POISON_STRIKE,
)
# Cold Blood 14177 (crit +100, damage +20, range +5): every direct-damage rogue ability.
COLD_BLOOD_READ = (
    EVISCERATE,
    FAN_OF_KNIVES_D1 | ENVENOM_D1 | DEADLY_THROW_D1 | RIPOSTE_D1,
    DIRECT_BUILDER_GROUP | MUTILATE_HANDS | POISON_STRIKE,
)
# Cold Blood eff2 (flat RANGE +5): SpellMod RANGE is applied by the PARENT cast's own family flags (Spell::CheckRange), so
# the reader also names the two parents that deal no damage themselves: Mutilate 1329 (d1 b21) and Kingsbane 203822.
MUTILATE_PARENT_D1 = 0x200000            # d1 b21 (stock Mutilate parent 1329)
COLD_BLOOD_RANGE_READ = (
    COLD_BLOOD_READ[0],
    COLD_BLOOD_READ[1] | MUTILATE_PARENT_D1,
    COLD_BLOOD_READ[2] | KINGSBANE_PARENT,
)
# Remorseless Attacks crit buff 203838: SS, Backstab, Ambush, Mutilate hands, Ghostly Strike.
REMORSELESS_READ = (SINISTER_STRIKE | BACKSTAB | AMBUSH, 0, MUTILATE_HANDS | GHOSTLY_STRIKE_ID)
# Remorseless capstone buff 203839 (pct DAMAGE + DOT): rogue poisons and Envenom.
REMORSELESS_POISON_READ = (0, POISON_GROUP, 0)
# Seal Fate spell_proc -14186 SpellFamilyMask (C2: single-strike builders only; multi-hit casts call RollSealFate).
SEAL_FATE_PROC_READ = (0, 0, DIRECT_BUILDER_GROUP)
# Seal Fate pct DAMAGE on Eviscerate + Deadly Throw; its pct DOT reads Rupture alone.
SEAL_FATE_DAMAGE_READ = (EVISCERATE, DEADLY_THROW_D1, 0)
SEAL_FATE_DOT_READ = (RUPTURE, 0, 0)
# Hunger for Blood pct ACTIVATION_TIME: Deadly Poison, Garrote, Rupture, Kingsbane DoT, Doomblade (dummy bleed).
HUNGER_FOR_BLOOD_READ = (DEADLY_POISON | GARROTE | RUPTURE, 0, KINGSBANE_DOT | DOOMBLADE)
# Wound Poison 13218 aura-271 reader: WOUND_BLEED_READ + Doomblade (S2 adds Hemorrhage d2 b12).
WOUND_BLEED_READ_S1 = (RUPTURE | GARROTE, 0, DOOMBLADE)
# Find Weakness flat CRITICAL_CHANCE: every rogue damage ability and poison (never a zero mask).
FIND_WEAKNESS_READ = (
    GARROTE,
    FAN_OF_KNIVES_D1 | RIPOSTE_D1 | POISON_GROUP,
    FINISHER_GROUP | DIRECT_BUILDER_GROUP | MUTILATE_HANDS | POISON_STRIKE | KINGSBANE_DOT,
)
# Ruthlessness pct DAMAGE + DOT: the finisher group.
RUTHLESSNESS_READ = (0, 0, FINISHER_GROUP)
# Rogue poison damage (d1 b19): Vile Poisons DAMAGE + DOT, Toxic Blade's aura 271, Dashing Scoundrel's crit
# (Envenom eff1).
POISON_DAMAGE_READ = (0, POISON_GROUP, 0)
# Venomous Fan pct DAMAGE: Fan of Knives (51723 + 52874).
VENOMOUS_FAN_READ = (0, FAN_OF_KNIVES_D1, 0)
# Murder pct DOT: Garrote.
MURDER_DOT_READ = (GARROTE, 0, 0)
# Toxic Blade ranks flat EFFECT2 on Shiv 203725 (its index-1 ADD_COMBO_POINTS).
TOXIC_BLADE_SHIV_READ = (SHIV, 0, 0)
# Improved Poisons flat CHANCE_OF_SUCCESS: the Lethal self auras.
IMPROVED_POISONS_READ = (0, 0, LETHAL_AURA)
# Blindside buff 203831 pct COST -100: Sinister Strike.
BLINDSIDE_COST_READ = (SINISTER_STRIKE, 0, 0)
# Vile Poisons pct EFFECT1 on Mind-numbing 5760; helper flat DURATION on Wound 13218.
VILE_POISONS_MIND_NUMBING_READ = (MIND_NUMBING_POISON, 0, 0)
VILE_POISONS_WOUND_DURATION_READ = (WOUND_POISON, 0, 0)

# --- S2 Subtlety (append-only; S2-HANDOFF section 5, S2a WP-BRIEF section 4) ---
# Stock identity the S2 readers name (no new carrier). NEVER put it on an S2 row: Stealth strips d0 b11 auras.
VANISH = 0x800                           # d0 b11 (stock 1856; Elusiveness' COOLDOWN reader)
# New d2 bits (carriers in the comment; the WP-BRIEF bit table is the authority).
DEATH_FROM_ABOVE = 0x80                  # d2 b7 (204148 castable, 204169 area hit)
DFA_LANDING = 0x100                      # d2 b8 (204170 landing; "counts as an Eviscerate", never d0 b17)
HEMORRHAGE = 0x1000                      # d2 b12 (204160 bleed, 204161 tick)
SINISTER_CALLING_VOLLEY = 0x20000        # d2 b17 (204165)

# --- S2 carrier masks (the row's own SpellClassMask_1/_2/_3), (d0, d1, d2) ---
DEATH_FROM_ABOVE_CLASS = (0, 0, DEATH_FROM_ABOVE | FINISHER_GROUP)        # 204148, 204169
DFA_LANDING_CLASS = (0, 0, DFA_LANDING | FINISHER_GROUP)                  # 204170
HEMORRHAGE_CLASS = (0, 0, HEMORRHAGE)                                     # 204160, 204161
SINISTER_CALLING_VOLLEY_CLASS = (0, 0, SINISTER_CALLING_VOLLEY)           # 204165
SECOND_VOLLEY_CLASS = (0, FAN_OF_KNIVES_D1, 0)                            # 204166, 204167 (keeps the dagger +50%)
DEADLY_THROW_COPY_CLASS = (0, DEADLY_THROW_D1, 0)                         # 204168

# --- S2 reader composites, (d0, d1, d2) ---
# From the Shadows eff0 pct DAMAGE: Backstab, Ambush, Mutilate hands (the stock d1 b1 / b2 hand bits go).
FROM_THE_SHADOWS_READ = (BACKSTAB | AMBUSH, 0, MUTILATE_HANDS)
# From the Shadows eff1 pct DOT: Garrote.
FROM_THE_SHADOWS_DOT_READ = (GARROTE, 0, 0)
# Shadow Dance 51713 eff0 aura 275 (IGNORE_SHAPESHIFT / Hidden casts): Ambush, Garrote, Cheap Shot, exactly.
SHADOWED_HIDDEN_READ = (AMBUSH | GARROTE | CHEAP_SHOT, 0, 0)
# Elusiveness eff0 flat COOLDOWN: Vanish only (stock also had Blind d0 b24).
ELUSIVENESS_VANISH_READ = (VANISH, 0, 0)
# Slaughter from the Shadows eff0 pct DAMAGE: Backstab.
SLAUGHTER_READ = (BACKSTAB, 0, 0)
# Improved Ambush eff0 flat CRITICAL_CHANCE: Ambush.
IMPROVED_AMBUSH_READ = (AMBUSH, 0, 0)
# Waylay eff0 pct DAMAGE, and the 51696 spell_proc family mask: Ambush.
WAYLAY_READ = (AMBUSH, 0, 0)
# Initiative spell_proc -13976 family mask: Ambush, Garrote, Cheap Shot.
INITIATIVE_PROC_READ = (AMBUSH | GARROTE | CHEAP_SHOT, 0, 0)
# Finality buffs: 204157 pct DAMAGE (Eviscerate + the landing), 204158 pct DOT (Rupture), 204159 pct DAMAGE (Deadly
# Throw and its copies).
FINALITY_EVISCERATE_READ = (EVISCERATE, 0, DFA_LANDING)
FINALITY_RUPTURE_READ = (RUPTURE, 0, 0)
FINALITY_DEADLY_THROW_READ = (0, DEADLY_THROW_D1, 0)
# Throwing Specialization eff0 pct DAMAGE: Deadly Throw + Fan of Knives (51723, 52874 and the S2 copies).
THROWING_SPEC_READ = (0, DEADLY_THROW_D1 | FAN_OF_KNIVES_D1, 0)
# Deadliness eff1 pct DOT: Garrote, Rupture.
DEADLINESS_DOT_READ = (GARROTE | RUPTURE, 0, 0)
# Serrated Blades eff0 pct DOT (stock, unchanged): Rupture.
SERRATED_BLADES_DOT_READ = (RUPTURE, 0, 0)
# Mark of the Master Assassin buff 204164 flat CRITICAL_CHANCE (U36): every rogue button's direct hit, never poison
# hits, autos or periodic damage. Riposte (d1 b8) is a direct ability hit too (harness, S2a unsettled 1).
MOMA_READ = (
    EVISCERATE,
    ENVENOM_D1 | DEADLY_THROW_D1 | FAN_OF_KNIVES_D1 | RIPOSTE_D1,
    DIRECT_BUILDER_GROUP | DEATH_FROM_ABOVE | DFA_LANDING | MUTILATE_HANDS | POISON_STRIKE | SINISTER_CALLING_VOLLEY,
)
# Hunger for Blood 51662 (U37), Wound Poison 13218's aura 271 and Find Weakness gain S2's new bits.
HUNGER_FOR_BLOOD_READ_S2 = (HUNGER_FOR_BLOOD_READ[0], HUNGER_FOR_BLOOD_READ[1], HUNGER_FOR_BLOOD_READ[2] | HEMORRHAGE)
WOUND_BLEED_READ_S2 = (WOUND_BLEED_READ_S1[0], WOUND_BLEED_READ_S1[1], WOUND_BLEED_READ_S1[2] | HEMORRHAGE)
FIND_WEAKNESS_READ_S2 = (
    FIND_WEAKNESS_READ[0],
    FIND_WEAKNESS_READ[1],
    FIND_WEAKNESS_READ[2] | DEATH_FROM_ABOVE | DFA_LANDING | SINISTER_CALLING_VOLLEY,
)

# --- S2 "never" sets (tests) ---
FORBIDDEN_S2_D0 = FORBIDDEN_D0 | GHOSTLY_STRIKE_DAGGER    # d0 b11, b22, b25, b26 on any S2 row
FORBIDDEN_DFA_LANDING_D0 = EVISCERATE                     # never d0 b17 on 204170 (AP hardcode, Opportunity)
FORBIDDEN_HEMORRHAGE_D0 = RUPTURE                         # never d0 b20 on 204160 / 204161 (Glyph of Backstab)


# --- S2 raw-key helpers: use these, never hand-write EffectSpellClassMask / SpellClassMask keys ---
_EFFECT_LETTER = ("A", "B", "C")


def read_mask_keys(eff_index, triple):
    """Raw keys of one effect's reader mask: {'EffectSpellClassMask<L>_<n>': value} for all three dwords.

    `eff_index` is the 0-based SpellEffIndex (the brief's eff0 / eff1 / eff2), which picks the LETTER: eff0 = A,
    eff1 = B, eff2 = C. The NUMBER is the dword: _1 = d0, _2 = d1, _3 = d2 (dbcfmt.py; the S1 tests caught a
    letter/dword swap). Zero dwords are emitted too, so merging the result over a pulled row's raw_overrides
    overwrites a stale twin.
    """
    if eff_index not in (0, 1, 2):
        raise ValueError(f"read_mask_keys: eff_index must be 0, 1 or 2 (got {eff_index!r})")
    d0, d1, d2 = triple
    letter = _EFFECT_LETTER[eff_index]
    return {f"EffectSpellClassMask{letter}_1": int(d0), f"EffectSpellClassMask{letter}_2": int(d1),
            f"EffectSpellClassMask{letter}_3": int(d2)}


def clear_mask_keys(*eff_indexes):
    """Zero every dword of the given 0-based effects' reader masks (stale twins on effects that read nothing)."""
    keys = {}
    for eff_index in eff_indexes:
        keys.update(read_mask_keys(eff_index, (0, 0, 0)))
    return keys


def class_mask_keys(triple):
    """Raw keys of a row's OWN family flags: {'SpellClassMask_1': d0, '_2': d1, '_3': d2}, zeros included."""
    d0, d1, d2 = triple
    return {"SpellClassMask_1": int(d0), "SpellClassMask_2": int(d1), "SpellClassMask_3": int(d2)}


# --- S3 Combat (append-only; S3-HANDOFF section 5, S3a WP-BRIEF section 4) ---
# Stock identities the S3 readers name (no new carrier).
SLICE_AND_DICE = 0x40000                 # d0 b18 (stock 5171; Improved Slice and Dice's readers)
EVASION = 0x20                           # d0 b5 (stock 5277; Endurance's COOLDOWN reader)
SPRINT = 0x40                            # d0 b6 (stock 2983; Improved Sprint's DURATION / aura 109 readers)
ADRENALINE_RUSH_D1 = 0x80                # d1 b7 (stock 13750)
BLADE_FLURRY_D1 = 0x800                  # d1 b11 (stock 13877; it also carries d0 b30, Ghostly Strike's stock bit)
KILLING_SPREE_D1 = 0x800000              # d1 b23 (stock 51690; S3 adds the strikes 57841 / 57842)
# New d2 bits (carriers in the comment; the WP-BRIEF bit table is the authority).
PISTOL_SHOT = 0x10                       # d2 b4 (203958 only; never on a copy)
BETWEEN_THE_EYES = 0x20                  # d2 b5 (203959; never with d0 b17)
EN_GARDE = 0x40                          # d2 b6 (203969)
BLADE_RUSH = 0x8000                      # d2 b15 (203980)
GRAPPLING_HOOK = 0x10000                 # d2 b16 (203963)
SS_SECOND_STRIKE = 0x800000              # d2 b23 (203986: Sinister Strike's second strike, C9)
PISTOL_SHOT_EXTRA = 0x1000000            # d2 b24 (203988: Surprise Attacks' extra shots, C9)

# --- S3 carrier masks (the row's own SpellClassMask_1/_2/_3), (d0, d1, d2) ---
PISTOL_SHOT_CLASS = (0, 0, PISTOL_SHOT | DIRECT_BUILDER_GROUP)            # 203958
BETWEEN_THE_EYES_CLASS = (0, 0, BETWEEN_THE_EYES | FINISHER_GROUP)        # 203959
EN_GARDE_CLASS = (0, 0, EN_GARDE | FINISHER_GROUP)                        # 203969
BLADE_RUSH_CLASS = (0, 0, BLADE_RUSH)                                     # 203980
GRAPPLING_HOOK_CLASS = (0, 0, GRAPPLING_HOOK)                             # 203963
SS_SECOND_STRIKE_CLASS = (0, 0, SS_SECOND_STRIKE)                         # 203986
PISTOL_SHOT_EXTRA_CLASS = (0, 0, PISTOL_SHOT_EXTRA)                       # 203988
KILLING_SPREE_STRIKE_CLASS = (0, KILLING_SPREE_D1, 0)                     # 57841, 57842
RIPOSTE_CLEAVE_CLASS = (0, RIPOSTE_D1, 0)                                 # 203993
# Stock rows S3 extends (U65 / U62; the row's whole own mask after S3): Riposte joins the direct-builder group,
# Killing Spree the finisher group.
RIPOSTE_CLASS_S3 = (0, RIPOSTE_D1, DIRECT_BUILDER_GROUP)                  # 14251
KILLING_SPREE_CLASS_S3 = (0, KILLING_SPREE_D1, FINISHER_GROUP)            # 51690

# --- S3 reader composites, (d0, d1, d2) ---
# Improved Sinister Strike pct DAMAGE: Sinister Strike and its second strike.
IMPROVED_SS_READ = (SINISTER_STRIKE, 0, SS_SECOND_STRIKE)
# Aggression flat CRITICAL_CHANCE: Sinister Strike, Pistol Shot, Eviscerate, Between the Eyes, the second strike and
# the extra shots.
AGGRESSION_READ = (
    SINISTER_STRIKE | EVISCERATE,
    0,
    PISTOL_SHOT | BETWEEN_THE_EYES | SS_SECOND_STRIKE | PISTOL_SHOT_EXTRA,
)
# Surprise Attacks pct DAMAGE: Sinister Strike, Pistol Shot, Eviscerate, Between the Eyes, Backstab, Ambush, Shiv, the
# second strike and the extra shots.
SURPRISE_ATTACKS_READ = (
    SINISTER_STRIKE | EVISCERATE | BACKSTAB | AMBUSH | SHIV,
    0,
    PISTOL_SHOT | BETWEEN_THE_EYES | SS_SECOND_STRIKE | PISTOL_SHOT_EXTRA,
)
# Coup de Grace pct DAMAGE: Eviscerate, Between the Eyes, Killing Spree's strikes (d1 b23; also the inert 51690).
COUP_DE_GRACE_READ = (EVISCERATE, KILLING_SPREE_D1, BETWEEN_THE_EYES)
# Blade Rush's buff 203990 pct DAMAGE: the same three damaging finishers.
BLADE_RUSH_EMPOWER_READ = COUP_DE_GRACE_READ
# Opportunity's companion 203984 (pct COST -100, pct DAMAGE +50) and Hair Trigger's buff 203987: Pistol Shot only (the
# extra shots carry their own bit and never see them).
OPPORTUNITY_READ = (0, 0, PISTOL_SHOT)
HAIR_TRIGGER_READ = (0, 0, PISTOL_SHOT)
# Primed Powder 203985 pct DAMAGE: Between the Eyes.
PRIMED_POWDER_READ = (0, 0, BETWEEN_THE_EYES)
# Blade Twisting's debuff 203998 aura 271 (Q13: read by every combo point builder's direct hit): the direct-builder
# group (Sinister Strike, Backstab, Ambush, Gouge, Ghostly Strike, Shiv, Pistol Shot, Riposte), Mutilate and Kingsbane
# hands, Fan of Knives (and Second Volley), the second strike and the extra shots. Bleeds (Garrote) are not hits.
BLADE_TWISTING_READ = (
    0,
    FAN_OF_KNIVES_D1,
    DIRECT_BUILDER_GROUP | MUTILATE_HANDS | POISON_STRIKE | SS_SECOND_STRIKE | PISTOL_SHOT_EXTRA,
)
# Improved Riposte pct THREAT: Riposte (and its cleave 203993, d1 b8) and Ghostly Strike (d2 b21).
IMPROVED_RIPOSTE_THREAT_READ = (0, RIPOSTE_D1, GHOSTLY_STRIKE_ID)
# Improved Slice and Dice pct DURATION and flat EFFECT2: Slice and Dice.
IMPROVED_SND_READ = (SLICE_AND_DICE, 0, 0)
# Endurance flat COOLDOWN: Evasion only (the stock Sprint clause goes).
ENDURANCE_EVASION_READ = (EVASION, 0, 0)
# Improved Sprint flat DURATION (both ranks) and rank 2's aura 109 trigger (30918): Sprint.
IMPROVED_SPRINT_DURATION_READ = (SPRINT, 0, 0)
IMPROVED_SPRINT_TRIGGER_READ = (SPRINT, 0, 0)
# U65: S1 / S2 "every ability" readers gain Between the Eyes (d2 b5) and Blade Rush (d2 b15). Pistol Shot and Riposte
# reach them through the direct-builder group (d2 b19); the copies (d2 b23 / b24, d1 b23 strikes) join none.
COLD_BLOOD_READ_S3 = (COLD_BLOOD_READ[0], COLD_BLOOD_READ[1], COLD_BLOOD_READ[2] | BETWEEN_THE_EYES | BLADE_RUSH)
COLD_BLOOD_RANGE_READ_S3 = (
    COLD_BLOOD_RANGE_READ[0],
    COLD_BLOOD_RANGE_READ[1],
    COLD_BLOOD_RANGE_READ[2] | BETWEEN_THE_EYES | BLADE_RUSH,
)
# U74 ruling 2026-10-27: Ruthlessness's damage / DoT readers reach Killing Spree's strikes (57841 / 57842, d1 b23) too.
RUTHLESSNESS_READ_S3 = (0, KILLING_SPREE_D1, FINISHER_GROUP)
MOMA_READ_S3 = (MOMA_READ[0], MOMA_READ[1], MOMA_READ[2] | BETWEEN_THE_EYES | BLADE_RUSH)
FIND_WEAKNESS_READ_S3 = (
    FIND_WEAKNESS_READ_S2[0],
    FIND_WEAKNESS_READ_S2[1],
    FIND_WEAKNESS_READ_S2[2] | BETWEEN_THE_EYES | BLADE_RUSH,
)

# --- S3 "never" sets (tests) ---
FORBIDDEN_S3_D0 = FORBIDDEN_S2_D0                          # d0 b11, b22, b25, b26 on any S3 row
FORBIDDEN_BETWEEN_THE_EYES_D0 = EVISCERATE                 # never d0 b17 on 203959 (AP hardcode, Eviscerate readers)
# Never on a copy or triggered strike (203986, 203988, 203991-203995, 57841, 57842): Sinister Strike's identity, Pistol
# Shot's identity, the direct-builder group.
FORBIDDEN_COPY_S3 = (SINISTER_STRIKE, 0, PISTOL_SHOT | DIRECT_BUILDER_GROUP)
