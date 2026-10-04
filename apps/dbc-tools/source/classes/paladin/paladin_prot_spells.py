"""
Paladin - Protection (S3) new castable, helpers and hidden passives (paladin-rework S3, WP-A2a).

Source of truth: .agents/plans/paladin-rework/paladin-rework.PROTECTION.md - §2.1 (id map + DSL variable names),
§2.4 (icons), §2.7 (script bindings), §4 common rules, §4.2 - §4.12 (spell data), §4.13 (values at 60), §7
(spell_proc) and §10 (tooltip variables). Brief: paladin-rework.Protection-WP-BRIEF.md.

Declared here, in id order:
    201356 Guardian of Ancient Kings (castable; SLA 30520 is A3's granted_by_talent), 201360 / 201361 Bulwark and its
    grant, 201362 / 201363 Radiant Bulwark buff and absorb, 201364 - 201367 Touched by the Light / Shroud of Light,
    201368 GoAK periodic, 201369 Avenging Light buff, 201370 extra Avenger's Shield, 201371 Improved SoC DoT,
    201372 Improved Consecration slow (spell_group 1059), 201373 Light's Reservoir heal, 201374 Shield of the Templar
    capstone, 201375 Ardent Defender buff, 201376 / 201377 Blessing of Sanctuary helpers,
    tooltip_vars 1135 (`prot_sor_tooltip`) and 1136 (`prot_holy_shield_tooltip`), imported by paladin_spells.py.

Not declared here: the 36 talent rank spells (paladin_prot_ranks.py), stock edits (paladin_trigger_spells.py /
paladin_spells.py), talents (paladin_talents.py). Other agents' spells are referenced by bare id only (the rank ids
inside the two tooltip_vars, the trigger ids inside the proc auras, linked_spell triggers).

Conventions (PROTECTION §4 common): SpellClassSet 10 on every row; no family bits on any helper (§2.1); every
helper whose target is not the caster has range_yards=50000.0 (CR1) and, because the paladin casts it at another
unit, AttributesEx2 IGNORE_LINE_OF_SIGHT (S1 carry-over; 201370-201373, 201376); SUPPRESS_CASTER_PROCS where §4 says;
DUMMY-with-proc effects carry trigger_spell 0 / misc 0 (X5); script-valued effects are potency_excluded with
points_per_level 0, EffectBonusMultiplier 0 and no spell_bonus_data row. "DUMMY" on an aura-type spell is
APPLY_AURA DUMMY (the rank reader and the proc need an aura effect); only 201361 is a real SPELL_EFFECT_DUMMY.
Effect class masks are raw_overrides EffectSpellClassMask{A,B,C}_{1,2,3} keys (letter = effect, digit = dword).
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, RANGE_SELF, School, SpellModOp
from lib.dsl.registry import (
    linked_spell, procs_on, scripted_by, spell, spell_group, talent_mult, tooltip_vars,
)

from . import _masks as m


# --- Spell.dbc flag values used below (SharedDefines.h) -------------------------------------------------------
_ATTR0_PASSIVE_HIDDEN = 0x1D0  # PASSIVE | DO_NOT_DISPLAY | ... : the talent-rank / hidden passive shape
_ATTR0_DO_NOT_DISPLAY = 0x80
_ATTR0_GCD_CASTABLE = 65536  # the Holy castables' (Divine Toll) Attributes word
_ATTR1_NO_THREAT = 0x400
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x4  # paladin casts at secondary targets; the area / unit pick already did the LoS test
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_SUPPRESS_CASTER_PROCS = 0x10000
_ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000

_DMG_NONE = 0
_DMG_MAGIC = 1
_DMG_RANGED = 3

_HOLY = School.HOLY
_FAR_RANGE = 50000.0  # range_yards for every non-self helper (PROTECTION §4 common, CR1)

_SCRIPT_BP = 'script-supplied bp (PROTECTION §4 common: the value lives in the C++ call, the DBC fields are dead)'
_PCT_OF_OVERHEAL = 'percent of overheal; script bp (PROTECTION §4.3)'

# Proc flags / spell_proc masks (SpellMgr.h)
_PROC_TAKEN_DIRECT_ANY_DAMAGE = 0x222A8  # TAKEN melee/ranged auto + spell melee/ranged + magic neg (§7)
_PROC_TAKEN_MELEE_RANGED = 0x2A8
_PROC_BLOCK = 0x40  # PROC_HIT_BLOCK


def _text(description: str = "", aura: str = "") -> dict:
    """The four text-mask / enUS keys every row carries (16712190 = text present, 16712188 = blank)."""
    return {
        'Description_Lang_Mask': 16712190 if description else 16712188,
        'Description_Lang_enUS': description,
        'AuraDescription_Lang_Mask': 16712190 if aura else 16712188,
        'AuraDescription_Lang_enUS': aura,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_Mask': 16712188,
    }


def _raw(description: str = "", aura: str = "", level: int = 1, dmg_class: int = _DMG_NONE, **extra) -> dict:
    """Common raw_overrides for a new Protection spell: family 10, no equipped item, instant, all-language masks,
    SpellLevel `level`, DmgClass `dmg_class`. `extra` wins."""
    raw = {
        **_text(description, aura),
        'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0,
        'CastingTimeIndex': 1,
        'DefenseType': dmg_class,
        'EquippedItemClass': -1,
        'ProcChance': 101,
        'SpellClassSet': 10,
        'SpellLevel': level,
    }
    raw.update(extra)
    return raw


def _emask(effect: int, mask) -> dict:
    """EffectSpellClassMask{A,B,C}_{1,2,3}: the LETTER is the effect (1 -> A), the number the dword
    (dbcfmt.py:127-139). `mask` is an int (dword 0) or a (d0, d1, d2) tuple."""
    letter = 'ABC'[effect - 1]
    dwords = mask if isinstance(mask, tuple) else (mask, 0, 0)
    return {f'EffectSpellClassMask{letter}_{i + 1}': value for i, value in enumerate(dwords) if value}


def _mod(op: SpellModOp, pct: bool, base_points: int, **kw) -> Effect:
    """A self-targeted SpellMod effect (the scope mask goes in raw_overrides through `_emask`)."""
    return Effect(
        type=EffectType.APPLY_AURA, apply_aura=AuraType.ADD_PCT_MODIFIER if pct else AuraType.ADD_FLAT_MODIFIER,
        misc_value=int(op), base_points=base_points, implicit_target_a=1, **kw,
    )


def _aura(aura_type, base_points: int = 0, target: int = 1, **kw) -> Effect:
    return Effect(type=EffectType.APPLY_AURA, apply_aura=aura_type, base_points=base_points,
                  implicit_target_a=target, **kw)


def _buff_spell(spell_id: int, name: str, effects: list, icon: int, duration_ms: int, description: str = "",
                aura: str = "", notes: str = "", attributes: int = 0, **raw_extra):
    """A self-only helper aura: target 1, RangeIndex 1 (self), no family bits."""
    return spell(
        id=spell_id, name=name, school=_HOLY, attributes=attributes,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=RANGE_SELF, duration_ms=duration_ms,
        effects=effects, spell_icon_id=icon,
        notes=notes, raw_overrides=_raw(description, aura, **raw_extra),
    )


def _hidden_passive(spell_id: int, name: str, effects: list, icon: int, notes: str, **raw_extra):
    """A hidden passive (attributes 0x1D0, duration -1) - the talent-rank / capstone-helper shape."""
    return _buff_spell(spell_id, name, effects, icon, -1, notes=notes, attributes=_ATTR0_PASSIVE_HIDDEN, **raw_extra)


# ===========================================================================================================
# §10 - tooltip variables, entries 1135 / 1136 (Prot block 1135-1149). The rank spells are declared in
# paladin_prot_ranks.py (A2c); referenced by bare id. paladin_spells.py imports both for 53600 / 20925.
# ===========================================================================================================

# Prot-tree talent multipliers for Prot-owned spell tooltips (PROTECTION.md §10).
prot_sor_tooltip = tooltip_vars(
    1135, "Prot-tree talent multiplier for Shield of Righteousness",
    il=talent_mult([201348, 201349, 201350]),  # Inner Light eff1 +5/10/15%
)
prot_holy_shield_tooltip = tooltip_vars(
    1136, "Prot-tree talent multiplier for Holy Shield",
    ld=talent_mult([201351, 201352], effect=2),  # Light's Defender eff2 +50/100% Holy damage
)


# ===========================================================================================================
# §4.5 - Guardian of Ancient Kings 201356 (castable) + 201368 (periodic grant).
# ===========================================================================================================

guardian_of_ancient_kings_periodic_201368 = _buff_spell(
    201368, 'Guardian of Ancient Kings',
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000,
            trigger_spell=201361, implicit_target_a=1)],
    icon=2268, duration_ms=15000,
    aura="Gaining a stack of Bulwark every sec.",
    notes="paladin-rework PROTECTION §4.5: self PERIODIC_TRIGGER_SPELL 1 s -> 201361 (Bulwark grant), 15 s = 15 grants "
          "into a five-stack cap. Not a proc aura (no spell_proc row, DBC ProcTypeMask 0). No family bits.",
)

guardian_of_ancient_kings_201356 = spell(
    id=201356, name='Guardian of Ancient Kings', school=_HOLY, attributes=_ATTR0_GCD_CASTABLE,
    cast_time_ms=0, cooldown_ms=180000, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=8000,
    effects=[
        _aura(AuraType.MOD_DAMAGE_PERCENT_TAKEN, -51, misc_value=127),
        Effect(type=EffectType.TRIGGER_SPELL, trigger_spell=201368, implicit_target_a=1),
    ],
    spell_icon_id=2268,
    notes="paladin-rework PROTECTION §4.5: talent-taught (60151 (10,0), A3 declares the talent + SLA 30520), learn 60, "
          "3 min (Cooldown-Haste eligible, >= 30 s), on the GCD (1500 / category 133, guess like DS / DP), no mana "
          "(guess), self. eff0 -50% damage taken all schools 8 s, eff1 TRIGGER_SPELL -> 201368 (+1 Bulwark / s for "
          "15 s). Does not consume Bulwark. No family bits, no script, no potency.",
    raw_overrides=_raw(
        "Calls upon the Guardian of Ancient Kings, reducing all damage you take by $s1% for $d. For the next "
        "$201368d, you gain a stack of Bulwark every sec.",
        "Damage taken reduced by $s1%.",
        level=60, PreventionType=1, StartRecoveryCategory=133, StartRecoveryTime=1500,
    ),
)


# ===========================================================================================================
# §4.2 - Bulwark 201360 (the resource aura) and 201361 (the "+1 stack" grant).
# ===========================================================================================================

bulwark_201360 = _buff_spell(
    201360, 'Bulwark',
    [_aura(AuraType.DUMMY, 0)],
    icon=90200, duration_ms=20000,
    description="Stacks up to 5 times. Your next Holy Light consumes all stacks.",
    aura="Your next Holy Light consumes Bulwark.",
    notes="paladin-rework PROTECTION §4.2: the Bulwark resource, APPLY_AURA DUMMY, 5 stacks (CumulativeAura), 20 s, "
          "positive, not dispellable, cancellable, no AuraInterruptFlags, no family bits. ModStackAmount refreshes "
          "the duration even at the cap. spell_pal_bulwark removes 201362 in AfterEffectRemove. Icon 90200 "
          "(Ascension holybulwark, patch-I).",
    CumulativeAura=5,
)
scripted_by(bulwark_201360, 'spell_pal_bulwark')

bulwark_grant_201361 = spell(
    id=201361, name='Bulwark', school=_HOLY,
    attributes=_ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=1)],
    spell_icon_id=90200,
    notes="paladin-rework PROTECTION §4.2: the only real SPELL_EFFECT_DUMMY of the block (§4 common), triggered only, "
          "DO_NOT_DISPLAY, NO_THREAT, SUPPRESS_CASTER_PROCS, no cost / cooldown / GCD. spell_pal_bulwark_grant: "
          "OnEffectHit(EFFECT_0, DUMMY) -> Paladin::GrantBulwark(player, 1). Shared by Anticipation r3, Vengeful "
          "Bulwark, Bulwark of Faith, the TbtL capstone (201367) and GoAK's periodic (201368).",
    raw_overrides=_raw(AttributesEx=_ATTR1_NO_THREAT, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)
scripted_by(bulwark_grant_201361, 'spell_pal_bulwark_grant')


# ===========================================================================================================
# §4.3 - Radiant Bulwark buff 201362 and absorb 201363 (the rank spells 201343-201345 are A2c's).
# ===========================================================================================================

radiant_bulwark_buff_201362 = _buff_spell(
    201362, 'Radiant Bulwark',
    [_mod(SpellModOp.CASTING_TIME, True, -101), _mod(SpellModOp.COST, True, -101)],
    icon=1801, duration_ms=20000,
    aura="Your next Holy Light is instant and costs no mana.",
    notes="paladin-rework PROTECTION §4.3: eff0 -100% cast time, eff1 -100% cost, both on Holy Light (d0 0x80000000); "
          "20 s, no charges - removed with Bulwark (spell_pal_bulwark) and applied by GrantBulwark at 5 stacks when a "
          "Radiant Bulwark rank is known. Holy Light's GCD and threat unchanged (C13).",
    **_emask(1, m.HOLY_LIGHT), **_emask(2, m.HOLY_LIGHT),
)

radiant_bulwark_absorb_201363 = _buff_spell(
    201363, 'Radiant Bulwark',
    [_aura(AuraType.SCHOOL_ABSORB, 0, misc_value=127, points_per_level=0.0, potency_excluded=_PCT_OF_OVERHEAL)],
    icon=1801, duration_ms=10000,
    aura="Absorbs damage.",
    notes="paladin-rework PROTECTION §4.3: SCHOOL_ABSORB all schools 10 s, positive, amount supplied by "
          "spell_pal_radiant_bulwark (17 / 33 / 50% of the overheal, cap 50% max health; user ruling F4). Percent of "
          "another heal, so potency_excluded; EffectBonusMultiplier 0, no spell_bonus_data.",
    EffectBonusMultiplier_1=0.0,
)


# ===========================================================================================================
# §4.4 - Touched by the Light 201364-201367 (the ranks 53590-53592 are stock rows edited by A2b).
# ===========================================================================================================

touched_by_the_light_buff_201364 = _buff_spell(
    201364, 'Touched by the Light',
    [_aura(AuraType.MOD_HEALING_RECEIVED, 0), _aura(AuraType.DUMMY, 0)],
    icon=3024, duration_ms=20000,
    aura="Your next direct heal on yourself is increased.",
    notes="paladin-rework PROTECTION §4.4: eff0 aura 283 bp 0 (the script sets 10 / 20 / 30), class mask "
          "PROT_SELF_DIRECT_HEALS (Holy Light | Flash of Light | Holy Shock heal; Lay on Hands dropped, PLAN #82) on "
          "BOTH this effect and the spell_proc row so the boosted set equals the consuming set (§0.2 item 17); the "
          "engine already limits aura 283 to heals from the aura's own caster. eff1 DUMMY bp 0 (proc carrier, "
          "DisableEffectsMask 0x1 on the row keeps eff0 off the proc), 1 charge, 20 s, refresh on reapply.",
    ProcCharges=1, **_emask(1, m.PROT_SELF_DIRECT_HEALS),
)
scripted_by(touched_by_the_light_buff_201364, 'spell_pal_touched_by_the_light_buff')
procs_on(
    touched_by_the_light_buff_201364, proc_flags=0x4400, family_name=10, family_mask=m.PROT_SELF_DIRECT_HEALS,
    spell_type_mask=2, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, hit_mask=0, attributes_mask=0,
    disable_effects_mask=0x1, chance=100.0, cooldown_ms=0,
)

shroud_of_light_buff_201365 = _buff_spell(
    201365, 'Shroud of Light',
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=201366,
            implicit_target_a=1)],
    icon=2177, duration_ms=20000,
    aura="The next direct damage you take heals you.",
    notes="paladin-rework PROTECTION §4.4: PROC_TRIGGER_SPELL -> 201366, 20 s (guess, P silent), 1 charge; default "
          "handler (201366 is self-targeted, so the attacker target is dropped); direct damage taken only. Row "
          "AttributesMask 0x2 so triggered NPC damage counts as 'the next direct damage you take'.",
    ProcCharges=1,
)
procs_on(
    shroud_of_light_buff_201365, proc_flags=_PROC_TAKEN_DIRECT_ANY_DAMAGE, spell_type_mask=1,
    spell_phase_mask=m.PROC_SPELL_PHASE_HIT, hit_mask=0, attributes_mask=m.PROC_ATTR_TRIGGERED_CAN_PROC,
    chance=100.0, cooldown_ms=0,
)

shroud_of_light_heal_201366 = spell(
    id=201366, name='Shroud of Light', school=_HOLY, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF,
    effects=[Effect(type=EffectType.HEAL, sp_potency=60.0, potency_kind='heal', implicit_target_a=1)],
    spell_icon_id=2177,
    notes="paladin-rework PROTECTION §4.4: Shroud of Light heal, self, 60 heal potency (636 at 60, no gear), learn / "
          "anchor level 35, can crit (DefenseType MAGIC), SUPPRESS_CASTER_PROCS. No family bits - so neither the TbtL "
          "buff nor Light's Reservoir reads it.",
    raw_overrides=_raw(
        "Heals you for {pot1}.", level=35, dmg_class=_DMG_MAGIC, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS,
    ),
)

touched_by_the_light_block_201367 = _hidden_passive(
    201367, 'Touched by the Light',
    [Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=201361,
            implicit_target_a=1)],
    icon=3024,
    notes="paladin-rework PROTECTION §4.4: hidden passive, a block grants a Bulwark stack (-> 201361). Applied by "
          "linked_spell(53592, 201367, type=2) while TbtL rank 3 is on the player. Data only, no script.",
)
procs_on(
    touched_by_the_light_block_201367, proc_flags=_PROC_TAKEN_MELEE_RANGED, spell_type_mask=0,
    spell_phase_mask=m.PROC_SPELL_PHASE_HIT, hit_mask=_PROC_BLOCK, chance=100.0, cooldown_ms=0,
)
linked_spell(53592, touched_by_the_light_block_201367.id, type=2)


# ===========================================================================================================
# §4.6 - Avenging Light buff 201369 and the extra Avenger's Shield 201370 (ranks 201353-201355 are A2c's).
# ===========================================================================================================

avenging_light_buff_201369 = _buff_spell(
    201369, 'Avenging Light',
    [_aura(AuraType.DUMMY, 0)],
    icon=1951, duration_ms=15000,
    aura="Your next Avenger's Shield throws three shields.",
    notes="paladin-rework PROTECTION §4.6: APPLY_AURA DUMMY bp 0, self, 15 s (guess). Consumed by "
          "spell_pal_avengers_shield_prot. No proc row, DBC ProcTypeMask 0.",
)

avengers_shield_extra_201370 = spell(
    id=201370, name="Avenger's Shield", school=_HOLY, dispel=DispelType.MAGIC, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=_FAR_RANGE, duration_ms=10000,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=132.35, ap_potency=132.35, potency_kind='direct',
               implicit_target_a=6, chain_targets=3),
        Effect(type=EffectType.APPLY_AURA, base_points=-51, mechanic=11, implicit_target_a=6,
               apply_aura=AuraType.MOD_DECREASE_SPEED, chain_targets=3),
    ],
    spell_icon_id=2172,
    notes="paladin-rework PROTECTION §4.6: copy of 31935's effects (132.35 / 132.35 hybrid, T 1.5, chain 3; daze -50% "
          "10 s) with NO family bits - above all not AS (d0 0x4000), so no Shield of the Templar roll; triggered "
          "only, no cost / cooldown, range 50000, IGNORE_LINE_OF_SIGHT, SUPPRESS_CASTER_PROCS (one cast for procs), "
          "learn / anchor level 40. Speed 35, DmgClass RANGED, visual 7886 as 31935. Not bound to "
          "spell_pal_seal_builder (no seal stack). Cast x2 by spell_pal_avengers_shield_prot.",
    raw_overrides=_raw(
        "", "Dazed.", level=40, dmg_class=_DMG_RANGED,
        AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS,
        AttributesEx4=262144, AttributesEx6=256, Speed=35.0, SpellVisualID_1=7886,
    ),
)


# ===========================================================================================================
# §4.7 - Improved Seal of Command DoT 201371.
# ===========================================================================================================

improved_soc_dot_201371 = spell(
    id=201371, name='Improved Seal of Command', school=_HOLY | School.FIRE, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=_FAR_RANGE, duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=2000, sp_potency=20.0,
               potency_kind='periodic', implicit_target_a=6),
    ],
    spell_icon_id=561,
    notes="paladin-rework PROTECTION §4.7: Holy|Fire (school 6, matches Command) DoT, 20 spell potency per 2 s tick "
          "(T = the amplitude: 71 per tick, 214 per target at 60), 6 s = 3 ticks; one per caster per target (a same-"
          "caster recast replaces). Learn / anchor level 15, no family bits, range 50000, IGNORE_LINE_OF_SIGHT, "
          "SUPPRESS_CASTER_PROCS. Cast by spell_pal_improved_soc_dot on every Deliverance target.",
    raw_overrides=_raw(
        "", "{pot1} Holy and Fire damage every $t1 sec.", level=15, dmg_class=_DMG_MAGIC,
        AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS,
    ),
)


# ===========================================================================================================
# §4.8 - Improved Consecration slow 201372 (spell_group 1059 = stock melee-attack-speed slows).
# ===========================================================================================================

improved_consecration_slow_201372 = spell(
    id=201372, name='Improved Consecration', school=_HOLY, dispel=DispelType.MAGIC, attributes=2426880,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=_FAR_RANGE, duration_ms=15000,
    effects=[_aura(AuraType.MOD_MELEE_HASTE, 0, target=6)],
    spell_icon_id=51,
    notes="paladin-rework PROTECTION §4.8: melee attack-speed slow (aura 138), bp supplied by "
          "spell_pal_improved_consecration_slow on every 201140 hit (live -6 / -13 / -20), 15 s, negative, Magic "
          "dispel (guess; Attributes word copied from Judgements of the Just 68055). NO family bits - never d2 b14 "
          "(spell_warrior.cpp:1099). range 50000, IGNORE_LINE_OF_SIGHT, SUPPRESS_CASTER_PROCS. spell_group 1059 "
          "(stock EXCLUSIVE_SAME_EFFECT group of attack-speed slows) so it does not stack with Thunder Clap etc.",
    raw_overrides=_raw(
        "", "Melee attack speed slowed.", level=1, dmg_class=_DMG_MAGIC,
        AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS,
    ),
)
spell_group(1059, improved_consecration_slow_201372)


# ===========================================================================================================
# §4.9 - Light's Reservoir heal 201373.
# ===========================================================================================================

lights_reservoir_heal_201373 = spell(
    id=201373, name="Light's Reservoir", school=_HOLY, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=_FAR_RANGE,
    effects=[Effect(type=EffectType.HEAL, base_points=0, points_per_level=0.0, implicit_target_a=21,
                    potency_excluded='percent of another heal; script bp (PROTECTION §4.9)')],
    spell_icon_id=3033,
    notes="paladin-rework PROTECTION §4.9: heal on another party member, the value is a percent of the paladin's own "
          "Holy Light / Flash of Light heal, supplied by spell_pal_lights_reservoir (SPELLVALUE_BASE_POINT0). "
          "IGNORE_CASTER_MODIFIERS + SUPPRESS_CASTER_PROCS, CANT_CRIT, EffectBonusMultiplier 0, no spell_bonus_data, "
          "range 50000, IGNORE_LINE_OF_SIGHT, learn level 25. No family bits.",
    raw_overrides=_raw(
        "", level=25, dmg_class=_DMG_MAGIC,
        AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
        AttributesEx3=_ATTR3_IGNORE_CASTER_MODIFIERS | _ATTR3_SUPPRESS_CASTER_PROCS,
        EffectBonusMultiplier_1=0.0,
    ),
)


# ===========================================================================================================
# §4.10 - Shield of the Templar capstone helper 201374 (rank 3's linked passive).
# ===========================================================================================================

shield_of_the_templar_capstone_201374 = _hidden_passive(
    201374, 'Shield of the Templar',
    [_aura(AuraType.DUMMY, 0)],
    icon=3016,
    notes="paladin-rework PROTECTION §4.10: hidden passive, healed by others (HoTs included) -> Divine Protection "
          "cooldown -1 s in real seconds, 1 s ICD. APPLY_AURA DUMMY with trigger 0 / misc 0 (X5); the AuraScript "
          "handles the proc. Applied by linked_spell(53711, 201374, type=2). One row per spell: -53709 already "
          "holds the silence, so the capstone needs this helper.",
)
scripted_by(shield_of_the_templar_capstone_201374, 'spell_pal_shield_of_the_templar_capstone')
procs_on(
    shield_of_the_templar_capstone_201374, proc_flags=0x88800, spell_type_mask=2,
    spell_phase_mask=m.PROC_SPELL_PHASE_HIT, hit_mask=0, attributes_mask=m.PROC_ATTR_TRIGGERED_CAN_PROC,
    chance=100.0, cooldown_ms=1000,
)
linked_spell(53711, shield_of_the_templar_capstone_201374.id, type=2)


# ===========================================================================================================
# §4.11 / §4.12 - Ardent Defender buff 201375, Blessing of Sanctuary helpers 201376 / 201377.
# ===========================================================================================================

ardent_defender_buff_201375 = _buff_spell(
    201375, 'Ardent Defender',
    [_aura(AuraType.MOD_HEALING_PCT, 19)],
    icon=2135, duration_ms=3000,
    aura="Healing received increased by $s1%.",
    notes="paladin-rework PROTECTION §4.12: self buff, healing received +20% for 3 s, applied by "
          "spell_pal_ardent_defender_prot after the lethal-save heal (stock 66235). Not a proc aura, no family bits.",
)

blessing_of_sanctuary_dr_201376 = spell(
    id=201376, name='Blessing of Sanctuary', school=_HOLY, attributes=_ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=_FAR_RANGE, duration_ms=1800000,
    effects=[_aura(AuraType.MOD_DAMAGE_PERCENT_TAKEN, 0, target=21, misc_value=127,
                   potency_excluded=_SCRIPT_BP)],
    spell_icon_id=19,
    notes="paladin-rework PROTECTION §4.11: Improved Blessing of Sanctuary's extra damage reduction, aura 87 all "
          "schools, bp supplied by spell_pal_blessing_of_sanctuary_prot (live -1 / -2), 30 min = the blessing's own "
          "duration (re-cast on every blessing reapply and removed with it), positive, not dispellable, "
          "DO_NOT_DISPLAY. Multiplies with the generic 68066 3% DR (user ruling F5). range 50000, "
          "IGNORE_LINE_OF_SIGHT, SUPPRESS_CASTER_PROCS. No family bits.",
    raw_overrides=_raw(
        "", "Damage taken reduced.",
        AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS,
    ),
)

blessing_of_sanctuary_mana_201377 = spell(
    id=201377, name='Blessing of Sanctuary', school=_HOLY, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF,
    effects=[Effect(type=EffectType.ENERGIZE, base_points=0, points_per_level=0.0, misc_value=0,
                    implicit_target_a=1)],
    spell_icon_id=19,
    notes="paladin-rework PROTECTION §4.11: ENERGIZE mana (misc 0), target self, bp supplied by "
          "spell_pal_blessing_of_sanctuary_prot (6% of the blessed unit's base mana), SUPPRESS_CASTER_PROCS. Self "
          "target, so it keeps RANGE_SELF. No family bits.",
    raw_overrides=_raw(AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)
