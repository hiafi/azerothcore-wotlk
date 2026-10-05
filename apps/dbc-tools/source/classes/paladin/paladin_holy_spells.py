"""
Paladin - Holy (S2) new castables, helpers and hidden passives (paladin-rework S2, WP-A2a).

Source of truth: .agents/plans/paladin-rework/paladin-rework.HOLY.md - §2.1 (id map), §2.6 (family bits,
spell_group), §2.7 (script bindings), §4 common rules, §4.2 - §4.5 (spell data), §4.6 (values at 60), §4.7
(tooltip variables) and §7 (spell_proc). Brief: paladin-rework.Holy-WP-BRIEF.md.

Declared here, in id order:
    201200 Light's Hammer, 201203 Divine Toll (castables; SLA 30510 / 30511 are A3's granted_by_talent)
    201201 / 201202 Light's Hammer ticks, 201281 / 201282 hidden snapshot sources
    201204 / 201205 Divine Toll Shocks, 201206 resolver (+ SLA 30512), 201207-201210 Glimmer of Light
    201211-201238 buffs and script-valued hits, 201239 / 201280 Purifying Power Consecration passives
    spell_group 1058 member 201234, tooltip_vars 1105 (`holy_heal_tooltip`, imported by paladin_spells.py).

Not declared here: the 37 talent rank spells and the three top-rank clones (paladin_holy_ranks.py), stock edits
(paladin_trigger_spells.py / paladin_spells.py), talents (paladin_talents.py). Other agents' spells are
referenced by bare id only.

Conventions (HOLY §4 common): SpellClassSet 10 on every row (a family-0 row's SpellMod would match every spell);
every helper whose target is not the caster has range_yards=50000.0 (CR1), AttributesEx3 SUPPRESS_CASTER_PROCS and,
because the paladin casts it at another unit, AttributesEx2 IGNORE_LINE_OF_SIGHT (S1 carry-over). Script-valued
heals / damage are potency_excluded with points_per_level 0 (CalcValue adds level scaling to a supplied bp),
EffectBonusMultiplier 0, IGNORE_CASTER_MODIFIERS and no spell_bonus_data row. SpellMod ranks store live - 1.
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, RANGE_SELF, School, SpellModOp
from lib.dsl.registry import (
    linked_spell, pot_text, procs_on, product, scripted_by, skill_line_ability, spell, spell_group, talent_mult,
    tooltip_vars,
)

from . import _masks as m


# --- Spell.dbc flag values used below (SharedDefines.h) -------------------------------------------------------
_ATTR0_PASSIVE_HIDDEN = 0x1D0  # PASSIVE | DO_NOT_DISPLAY | ... : the talent-rank / hidden passive shape
_ATTR0_DO_NOT_DISPLAY = 0x80
_ATTR0_NO_AURA_CANCEL = 0x80000000  # SPELL_ATTR0_CANT_CANCEL
_ATTR1_NO_THREAT = 0x400
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x4  # paladin casts at secondary / ally targets; the area pick already did the LoS test
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_DOT_STACKING_RULE = 0x80
_ATTR3_SUPPRESS_CASTER_PROCS = 0x10000
_ATTR3_ALWAYS_HIT = 0x40000
_ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
_ATTR5_SPELL_HASTE_AFFECTS_PERIODIC = 0x2000

# DmgClass (the column the DSL calls DefenseType)
_DMG_NONE = 0
_DMG_MAGIC = 1

_HOLY = School.HOLY
_FAR_RANGE = 50000.0  # range_yards for every non-self helper (HOLY §4 "Range on every triggered helper")

_SCRIPT_BP = 'script-supplied bp (HOLY §4 common: potency lives in the C++ value, the DBC fields are dead)'


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
    """Common raw_overrides for a new Holy spell: family 10, no equipped item, instant, all-language masks,
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


def _script_heal(target_a: int = 21, **kw) -> Effect:
    return Effect(type=EffectType.HEAL, base_points=0, points_per_level=0.0, implicit_target_a=target_a,
                  potency_excluded=_SCRIPT_BP, **kw)


def _script_damage(target_a: int = 6, **kw) -> Effect:
    return Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, points_per_level=0.0, implicit_target_a=target_a,
                  potency_excluded=_SCRIPT_BP, **kw)


def _carrier_raw(description: str = "", aura: str = "", level: int = 1, cant_crit: bool = False, **extra) -> dict:
    """A script-valued heal / damage carrier cast by the paladin at another unit: IGNORE_LINE_OF_SIGHT,
    IGNORE_CASTER_MODIFIERS + SUPPRESS_CASTER_PROCS, coefficient 0, MAGIC DmgClass (bonus / crit paths)."""
    raw = _raw(
        description, aura, level=level, dmg_class=_DMG_MAGIC,
        AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT | (_ATTR2_CANT_CRIT if cant_crit else 0),
        AttributesEx3=_ATTR3_IGNORE_CASTER_MODIFIERS | _ATTR3_SUPPRESS_CASTER_PROCS,
        EffectBonusMultiplier_1=0.0,
    )
    raw.update(extra)
    return raw


def _buff_spell(spell_id: int, name: str, effects: list, icon: int, duration_ms: int, description: str = "",
                aura: str = "", notes: str = "", **raw_extra):
    """A self-only helper buff: target 1, RangeIndex 1, no family bits, no description by default."""
    return spell(
        id=spell_id, name=name, school=_HOLY, attributes=0,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=RANGE_SELF, duration_ms=duration_ms,
        effects=effects, spell_icon_id=icon,
        notes=notes, raw_overrides=_raw(description, aura, **raw_extra),
    )


# ===========================================================================================================
# §4.7 - tooltip variables, entry 1105 (Holy block 1105-1119). One entry serves every Holy-owned spell that
# shares Healing Light: Holy Light 635, Flash of Light 19750, Holy Shock 20473 / 25912 / 25914, Light's Hammer
# 201200. paladin_spells.py / paladin_trigger_spells.py import `holy_heal_tooltip` from this module.
# ===========================================================================================================

# Holy-tree talent multipliers for Holy heal / Holy Shock / Light's Hammer tooltips (HOLY.md §4.7).
# talent_mult reads each rank's own $<rank>m<effect>, so retuning a rank updates every tooltip.
holy_heal_tooltip = tooltip_vars(
    1105, "Holy-tree talent multipliers for Holy heal, Holy Shock and Light's Hammer tooltips",
    hl=talent_mult([20237, 20238, 20239]),  # Healing Light eff1 +4/8/12% (HL, FoL, Shock heal AND damage, LH)
    glim=talent_mult([201268, 201269, 201270]),  # Glimmer of Light eff1: r1/r2 SpellMod +5/10%, r3 DUMMY 15 (static)
    illum=talent_mult([20210, 20212, 20213], effect=3),  # Illumination eff3 +10/20/30% Light's Hammer
    shock=product("hl", "glim"),
    lh=product("hl", "illum"),
)

# 1106: Concentration Aura 19746 and Concentration Burst 201164 (HOLY §5.2). Improved Concentration Aura 20254-6 eff0
# is an ADD_PCT_MODIFIER EFFECT1 +10/20/30%, which never moves a tooltip's $s1. Bare ids: the rank spells are
# declared in paladin_trigger_spells.py, which imports this module.
concentration_tooltip = tooltip_vars(
    1106, "Improved Concentration Aura multiplier for Concentration Aura and Concentration Burst tooltips",
    ic=talent_mult([20254, 20255, 20256]),
)


# ===========================================================================================================
# §4.3 - Light's Hammer 201200-201202 + hidden snapshot sources 201281 / 201282 (Rain of Fire C5 pattern).
# Potency lives on the sources (T = 2 s, learn level 20); the ticks are pure carriers. Bit LH (d2 0x4000) on all
# five and never on a spell with MOD_DECREASE_SPEED (spell_warrior.cpp:1099).
# ===========================================================================================================

light_s_hammer_heal_source_201281 = spell(
    id=201281, name="Light's Hammer", school=_HOLY, attributes=_ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF,
    effects=[Effect(type=EffectType.HEAL, sp_potency=20.0, potency_kind='heal', time_basis_ms=2000,
                    implicit_target_a=1)],
    spell_icon_id=1664,
    notes="paladin-rework HOLY §4.3 (review-2 X4): hidden, never cast or learned. Carries the heal tick's potency "
          "(20 per 2 s, 282 at 60) so the generator owns the coefficient; read once per cast by "
          "spell_pal_lights_hammer_aura. Bit LH so Healing Light / Illumination SpellMods match it in the snapshot.",
    raw_overrides=_raw(level=20, dmg_class=_DMG_MAGIC, SpellClassMask_3=m.LIGHTS_HAMMER),
)

light_s_hammer_damage_source_201282 = spell(
    id=201282, name="Light's Hammer", school=_HOLY, attributes=_ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=27.0, potency_kind='direct', time_basis_ms=2000,
                    implicit_target_a=1)],
    spell_icon_id=1664,
    notes="paladin-rework HOLY §4.3 (review-2 X4): hidden damage snapshot source, 27 per 2 s (96 at 60, pure SP like "
          "Holy Shock). DmgClass MAGIC so SPELL_DIRECT_DAMAGE reads the direct coefficient. Bit LH.",
    raw_overrides=_raw(level=20, dmg_class=_DMG_MAGIC, SpellClassMask_3=m.LIGHTS_HAMMER),
)

light_s_hammer_heal_tick_201201 = spell(
    id=201201, name="Light's Hammer", school=_HOLY, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=_FAR_RANGE,
    effects=[
        _script_heal(
            87, implicit_target_b=31, radius_yards=10.0,
        ),
    ],
    spell_icon_id=1664,
    notes="paladin-rework HOLY §4.3: heal tick, pure carrier (snapshot bp from 201281 passed as SPELLVALUE_BASE_POINT0, "
          "Rain of Fire C5 pattern), TARGET_DEST_DEST + UNIT_DEST_AREA_ALLY radius 10, MaxTargets 5. "
          "IGNORE_CASTER_MODIFIERS (the snapshot already holds the done-mods; taken mods stay live).",
    raw_overrides=_carrier_raw(level=20, MaxTargets=5, SpellClassMask_3=m.LIGHTS_HAMMER, SpellVisualID_1=90043),
)
scripted_by(light_s_hammer_heal_tick_201201, 'spell_pal_lights_hammer_tick')

light_s_hammer_damage_tick_201202 = spell(
    id=201202, name="Light's Hammer", school=_HOLY, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=_FAR_RANGE,
    effects=[
        _script_damage(
            87, implicit_target_b=16, radius_yards=10.0,
        ),
    ],
    spell_icon_id=1664,
    notes="paladin-rework HOLY §4.3: damage tick, pure carrier (snapshot from 201282), TARGET_DEST_DEST + "
          "UNIT_DEST_AREA_ENEMY radius 10, MaxTargets 5. Can crit (DmgClass MAGIC). No script (the OnHit rescale is gone).",
    raw_overrides=_carrier_raw(level=20, MaxTargets=5, SpellClassMask_3=m.LIGHTS_HAMMER, SpellVisualID_1=90042),
)

light_s_hammer_201200 = spell(
    id=201200, name="Light's Hammer", school=_HOLY, attributes=65536,
    cast_time_ms=0, cooldown_ms=60000, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=15,
    range_yards=30.0, duration_ms=14000,
    effects=[
        Effect(type=EffectType.PERSISTENT_AREA_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=28,
               radius_yards=10.0),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=2000, implicit_target_a=1),
    ],
    spell_icon_id=90220,  # build_patch_i.py ICON_ID_LIGHTS_HAMMER
    tooltip_vars=holy_heal_tooltip,
    notes="paladin-rework HOLY §4.3: Rain of Fire C5 shape - eff0 ground reticle + dynobj (no potency), eff1 2 s "
          "PERIODIC_DUMMY (7 ticks, hasted via AttributesEx5 0x2000). Learn 20, 15% mana, 60 s (Cooldown-Haste "
          "eligible), GCD. Bit LH, no MOD_DECREASE_SPEED anywhere. Ground-target flags (AttributesEx 0x88, "
          "AttributesEx2 0x400000, Targets 64) copied from the reworked Rain of Fire 5740. Visual 90040 "
          "(patch_paladin_vfx_models.py): Ascension's grounded hammer + impact.",
    raw_overrides=_raw(
        "Hurls a Light's Hammer to the ground. Every 2 sec for 14 sec it heals up to 5 allies within 10 yards for "
        + pot_text(light_s_hammer_heal_source_201281, var="lh")
        + " and deals " + pot_text(light_s_hammer_damage_source_201282, var="lh")
        + " Holy damage to up to 5 enemies within 10 yards. Only one Light's Hammer can be active at a time.",
        "Light's Hammer is active.",
        level=20, dmg_class=_DMG_MAGIC,
        AttributesEx=136, AttributesEx2=4194304, AttributesEx5=_ATTR5_SPELL_HASTE_AFFECTS_PERIODIC,
        PreventionType=1, StartRecoveryCategory=133, StartRecoveryTime=1500,
        SpellClassMask_3=m.LIGHTS_HAMMER, SpellVisualID_1=90040, Targets=64,
    ),
)
scripted_by(light_s_hammer_201200, 'spell_pal_lights_hammer')


# ===========================================================================================================
# §4.4 - Divine Toll 201203-201205 (castable + two script-valued Shock carriers).
# ===========================================================================================================

divine_toll_heal_shock_201204 = spell(
    id=201204, name='Divine Toll', school=_HOLY, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=_FAR_RANGE,
    effects=[_script_heal(21)],
    spell_icon_id=2845,
    notes="paladin-rework HOLY §4.4: Divine Toll heal Shock, script-valued (ComputeShockValue), CANT_CRIT (a crit is "
          "shown with SPELLVALUE_FORCED_CRIT_RESULT), no family bits, no NOT_A_PROC. Visual 135 (Holy Shock heal).",
    raw_overrides=_carrier_raw(cant_crit=True, SpellVisualID_1=135),
)

divine_toll_damage_shock_201205 = spell(
    id=201205, name='Divine Toll', school=_HOLY, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=_FAR_RANGE,
    effects=[_script_damage(6)],
    spell_icon_id=2845,
    notes="paladin-rework HOLY §4.4: Divine Toll damage Shock, script-valued, CANT_CRIT, no family bits. "
          "Visual 128 (Holy Shock damage).",
    raw_overrides=_carrier_raw(cant_crit=True, SpellVisualID_1=128),
)

divine_toll_201203 = spell(
    id=201203, name='Divine Toll', school=_HOLY, attributes=65536,
    cast_time_ms=0, cooldown_ms=60000, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=30,
    range_yards=RANGE_SELF,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=1)],
    spell_icon_id=2845,
    notes="paladin-rework HOLY §4.4: talent-taught (1433, A3 declares the talent + SLA 30511), learn 60, 30% mana, 60 s "
          "(Cooldown-Haste eligible), GCD, self-target dummy so it casts with any or no target. No family bits. "
          "Visual 90041 (patch_paladin_vfx_models.py): Holy Nova cast + Kyrian bell.",
    raw_overrides=_raw(
        "Instantly casts Holy Shock 10 times, divided among up to 5 targets within 30 yards. Each target's first "
        "Holy Shock is at full strength and places Glimmer of Light on it; the others are at 50% strength. Heals "
        "allies if your last Holy Shock healed, otherwise damages enemies in combat with you.",
        level=60, PreventionType=1, StartRecoveryCategory=133, StartRecoveryTime=1500, SpellVisualID_1=90041,
    ),
)
scripted_by(divine_toll_201203, 'spell_pal_divine_toll')


# ===========================================================================================================
# §4.2 - Holy Shock resolver 201206 (hidden passive, auto-learned by every paladin: SLA 30512) and Glimmer of
# Light 201207-201210.
# ===========================================================================================================

holy_shock_resolver_201206 = spell(
    id=201206, name='Holy Shock', school=_HOLY, attributes=_ATTR0_PASSIVE_HIDDEN,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[_aura(AuraType.DUMMY)],
    spell_icon_id=156,
    notes="paladin-rework HOLY §4.2: hidden passive, HIT-phase proc on 25912 / 25914 (once per Shock; depends on "
          "NOT_A_PROC 0x200 AttributesEx3 staying on both - HOLY §11 risk 2). DUMMY with trigger 0 by construction "
          "(X5). SLA 30512 (AcquireMethod 2) auto-learns it at login.",
    raw_overrides=_raw(),
)
scripted_by(holy_shock_resolver_201206, 'spell_pal_holy_shock_resolver')
skill_line_ability(id=30512, skill_line=594, spell_id=holy_shock_resolver_201206.id, class_mask=2,
                   min_skill_line_rank=1, raw_overrides={'AcquireMethod': 2})
procs_on(
    holy_shock_resolver_201206, proc_flags=0x14000, family_name=10, family_mask=m.HOLY_SHOCK_ALL,
    spell_type_mask=3, spell_phase_mask=m.PROC_SPELL_PHASE_HIT, hit_mask=0,
    attributes_mask=m.PROC_ATTR_TRIGGERED_CAN_PROC, chance=100.0, cooldown_ms=0,
)

glimmer_of_light_ally_201207 = spell(
    id=201207, name='Glimmer of Light', school=_HOLY, attributes=_ATTR0_NO_AURA_CANCEL,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=_FAR_RANGE, duration_ms=30000,
    effects=[_aura(AuraType.DUMMY, target=21)],
    spell_icon_id=3645,
    notes="paladin-rework HOLY §4.2: ally marker, 30 s, not dispellable, cannot be clicked off, DOT_STACKING_RULE (one "
          "per paladin per target).",
    raw_overrides=_raw(
        "", "Healed by the paladin's Holy Shocks.", dmg_class=_DMG_MAGIC,
        AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT,
        AttributesEx3=_ATTR3_DOT_STACKING_RULE | _ATTR3_SUPPRESS_CASTER_PROCS,
    ),
)
scripted_by(glimmer_of_light_ally_201207, 'spell_pal_glimmer_marker')

glimmer_of_light_enemy_201208 = spell(
    id=201208, name='Glimmer of Light', school=_HOLY, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=_FAR_RANGE, duration_ms=30000,
    effects=[_aura(AuraType.DUMMY, target=6)],
    spell_icon_id=3645,
    notes="paladin-rework HOLY §4.2: enemy marker (one id cannot be both friendly and hostile), 30 s, NO_THREAT, "
          "ALWAYS_HIT (a missed marker would desync the Glimmer deque), not dispellable, DOT_STACKING_RULE.",
    raw_overrides=_raw(
        "", "Damaged by the paladin's Holy Shocks.", dmg_class=_DMG_MAGIC,
        AttributesEx=_ATTR1_NO_THREAT, AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT,
        AttributesEx3=_ATTR3_DOT_STACKING_RULE | _ATTR3_SUPPRESS_CASTER_PROCS | _ATTR3_ALWAYS_HIT,
    ),
)
scripted_by(glimmer_of_light_enemy_201208, 'spell_pal_glimmer_marker')

glimmer_of_light_heal_pulse_201209 = spell(
    id=201209, name='Glimmer of Light', school=_HOLY, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=_FAR_RANGE,
    effects=[_script_heal(21)],
    spell_icon_id=3645,
    notes="paladin-rework HOLY §4.2: Glimmer heal pulse, script-valued (15% of the Shock; 238 at 60), CANT_CRIT "
          "(inherited crit via SPELLVALUE_FORCED_CRIT_RESULT). Visual 135.",
    raw_overrides=_carrier_raw(cant_crit=True, SpellVisualID_1=135),
)

glimmer_of_light_damage_pulse_201210 = spell(
    id=201210, name='Glimmer of Light', school=_HOLY, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=_FAR_RANGE,
    effects=[_script_damage(6)],
    spell_icon_id=3645,
    notes="paladin-rework HOLY §4.2: Glimmer damage pulse, script-valued (15% of the Shock; 100 at 60), CANT_CRIT. "
          "Visual 128.",
    raw_overrides=_carrier_raw(cant_crit=True, SpellVisualID_1=128),
)


# ===========================================================================================================
# §4.5 - helper buffs and hits 201211-201238.
# ===========================================================================================================

daybreak_201211 = _buff_spell(
    201211, 'Daybreak',
    [_mod(SpellModOp.COOLDOWN, True, -101)], icon=2900, duration_ms=12000,
    description="Your next Holy Shock triggers no cooldown.", aura="Your next Holy Shock triggers no cooldown.",
    notes="paladin-rework HOLY §4.5: -100% category cooldown on Holy Shock 20473 (d0 0x200000), 1 charge, 12 s. Divine "
          "Toll never consumes it (its Shocks carry no Holy Shock bit).",
    ProcCharges=1, **_emask(1, m.HOLY_SHOCK_CAST_DMG),
)

awe_201212 = _buff_spell(
    201212, 'Awe',
    [_mod(SpellModOp.CASTING_TIME, True, -101), _mod(SpellModOp.DAMAGE, True, 29)], icon=2603, duration_ms=20000,
    description="Your next Exorcism is instant and deals 30% more damage.",
    aura="Your next Exorcism is instant and deals 30% more damage.",
    notes="paladin-rework HOLY §4.5: eff1 -100% cast time, eff2 +30% damage (Q1), both on Exorcism (d1 0x2), 1 charge, 20 s.",
    ProcCharges=1, **_emask(1, (0, m.EXORCISM, 0)), **_emask(2, (0, m.EXORCISM, 0)),
)

crusader_s_zeal_201213 = _buff_spell(
    201213, "Crusader's Zeal",
    [_aura(AuraType.MOD_MELEE_HASTE, 9)], icon=2171, duration_ms=8000,
    description="Increases your melee attack speed by $s1% for $d.", aura="Melee attack speed increased by $s1%.",
    notes="paladin-rework HOLY §4.5: +10% melee attack speed, 8 s, refreshes. Granted by Blessed Crusade r3's "
          "PROC_TRIGGER_SPELL (target dropped to self).",
)

shock_and_awe_buff_r1_201214 = _buff_spell(
    201214, 'Shock and Awe',
    [_aura(AuraType.MOD_ATTACK_POWER_OF_STAT_PERCENT, 32, misc_value=3),
     _aura(AuraType.MOD_THREAT, -11, misc_value=127)],
    icon=2603, duration_ms=30000,
    aura="Attack power increased by $s1% of your Intellect. Threat caused reduced by $s2%.",
    notes="paladin-rework HOLY §4.5: AP from Intellect 33% (aura 268, misc 3 = Int) + threat -10%; the threat amount is "
          "zeroed by spell_pal_shock_and_awe_buff while Righteous Fury is up. 30 s.",
)
shock_and_awe_buff_r2_201215 = _buff_spell(
    201215, 'Shock and Awe',
    [_aura(AuraType.MOD_ATTACK_POWER_OF_STAT_PERCENT, 65, misc_value=3),
     _aura(AuraType.MOD_THREAT, -21, misc_value=127)],
    icon=2603, duration_ms=30000,
    aura="Attack power increased by $s1% of your Intellect. Threat caused reduced by $s2%.",
    notes="paladin-rework HOLY §4.5: rank 2, AP from Intellect 66%, threat -20%.",
)
shock_and_awe_buff_r3_201216 = _buff_spell(
    201216, 'Shock and Awe',
    [_aura(AuraType.MOD_ATTACK_POWER_OF_STAT_PERCENT, 99, misc_value=3),
     _aura(AuraType.MOD_THREAT, -31, misc_value=127)],
    icon=2603, duration_ms=30000,
    aura="Attack power increased by $s1% of your Intellect. Threat caused reduced by $s2%.",
    notes="paladin-rework HOLY §4.5: rank 3, AP from Intellect 100%, threat -30%.",
)
for _shock_and_awe in (shock_and_awe_buff_r1_201214, shock_and_awe_buff_r2_201215, shock_and_awe_buff_r3_201216):
    scripted_by(_shock_and_awe, 'spell_pal_shock_and_awe_buff')

_MERCIFUL_WINDOW_MASK = m.MERCIFUL_WINDOW  # (0, CS d1 0x8000, J d2 0x8): CS + Judgement own hit, never U, never Dv
merciful_strikes_window_r1_201217 = _buff_spell(
    201217, 'Merciful Strikes',
    [_mod(SpellModOp.DAMAGE, True, 4)], icon=2819, duration_ms=10000,
    aura="Crusader Strike and the direct damage of Judgement increased by $s1%.",
    notes="paladin-rework HOLY §4.5: window +5% (CS + Judgement own hit), 10 s.",
    **_emask(1, _MERCIFUL_WINDOW_MASK),
)
merciful_strikes_window_r2_201218 = _buff_spell(
    201218, 'Merciful Strikes',
    [_mod(SpellModOp.DAMAGE, True, 9)], icon=2819, duration_ms=10000,
    aura="Crusader Strike and the direct damage of Judgement increased by $s1%.",
    notes="paladin-rework HOLY §4.5: window +10%, 10 s.",
    **_emask(1, _MERCIFUL_WINDOW_MASK),
)
merciful_strikes_window_r3_201219 = _buff_spell(
    201219, 'Merciful Strikes',
    [_mod(SpellModOp.DAMAGE, True, 14)], icon=2819, duration_ms=10000,
    aura="Crusader Strike and the direct damage of Judgement increased by $s1%.",
    notes="paladin-rework HOLY §4.5: window +15%, 10 s.",
    **_emask(1, _MERCIFUL_WINDOW_MASK),
)

merciful_strikes_heal_201220 = spell(
    id=201220, name='Merciful Strikes', school=_HOLY, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=_FAR_RANGE,
    effects=[_script_heal(21)],
    spell_icon_id=2819,
    notes="paladin-rework HOLY §4.5: Merciful Strikes heal, script-valued (a share of the Crusader Strike / Judgement "
          "damage), up to 3 allies. CANT_CRIT (user ruling).",
    raw_overrides=_carrier_raw(cant_crit=True),
)

light_s_grace_flash_r1_201221 = _buff_spell(
    201221, "Light's Grace", [_mod(SpellModOp.DAMAGE, True, 9)], icon=2141, duration_ms=15000,
    aura="Your next Flash of Light heals for $s1% more.",
    notes="paladin-rework HOLY §4.5: next Flash of Light +10%, 1 charge, 15 s. New ids avoid SIC 248-262 (31834's forced charges).",
    ProcCharges=1, **_emask(1, m.FLASH_OF_LIGHT),
)
light_s_grace_flash_r2_201222 = _buff_spell(
    201222, "Light's Grace", [_mod(SpellModOp.DAMAGE, True, 19)], icon=2141, duration_ms=15000,
    aura="Your next Flash of Light heals for $s1% more.",
    notes="paladin-rework HOLY §4.5: next Flash of Light +20%, 1 charge, 15 s.",
    ProcCharges=1, **_emask(1, m.FLASH_OF_LIGHT),
)
light_s_grace_flash_r3_201223 = _buff_spell(
    201223, "Light's Grace", [_mod(SpellModOp.DAMAGE, True, 29)], icon=2141, duration_ms=15000,
    aura="Your next Flash of Light heals for $s1% more.",
    notes="paladin-rework HOLY §4.5: next Flash of Light +30%, 1 charge, 15 s.",
    ProcCharges=1, **_emask(1, m.FLASH_OF_LIGHT),
)
light_s_grace_holy_light_r1_201224 = _buff_spell(
    201224, "Light's Grace", [_mod(SpellModOp.DAMAGE, True, 4)], icon=2141, duration_ms=15000,
    aura="Your next Holy Light heals for $s1% more.",
    notes="paladin-rework HOLY §4.5: next Holy Light +5%, 1 charge, 15 s.",
    ProcCharges=1, **_emask(1, m.HOLY_LIGHT),
)
light_s_grace_holy_light_r2_201225 = _buff_spell(
    201225, "Light's Grace", [_mod(SpellModOp.DAMAGE, True, 9)], icon=2141, duration_ms=15000,
    aura="Your next Holy Light heals for $s1% more.",
    notes="paladin-rework HOLY §4.5: next Holy Light +10%, 1 charge, 15 s.",
    ProcCharges=1, **_emask(1, m.HOLY_LIGHT),
)
light_s_grace_holy_light_r3_201226 = _buff_spell(
    201226, "Light's Grace", [_mod(SpellModOp.DAMAGE, True, 14)], icon=2141, duration_ms=15000,
    aura="Your next Holy Light heals for $s1% more.",
    notes="paladin-rework HOLY §4.5: next Holy Light +15%, 1 charge, 15 s.",
    ProcCharges=1, **_emask(1, m.HOLY_LIGHT),
)

dawn_before_dusk_buff_r1_201227 = _buff_spell(
    201227, 'Dawn before Dusk', [_mod(SpellModOp.CRITICAL_CHANCE, False, 0)], icon=2063, duration_ms=30000,
    aura="Critical strike chance of your Holy Light, Flash of Light and Holy Shock increased by $s1% per stack.",
    notes="paladin-rework HOLY §4.5: +1% crit per stack (CalculateAmount multiplies by stacks), CumulativeAura 3, 30 s "
          "(refreshed by ModStackAmount), no charges.",
    CumulativeAura=3, **_emask(1, m.HOLY_HEAL_CASTS_AND_SHOCK),
)
dawn_before_dusk_buff_r2_201228 = _buff_spell(
    201228, 'Dawn before Dusk', [_mod(SpellModOp.CRITICAL_CHANCE, False, 1)], icon=2063, duration_ms=30000,
    aura="Critical strike chance of your Holy Light, Flash of Light and Holy Shock increased by $s1% per stack.",
    notes="paladin-rework HOLY §4.5: +2% crit per stack, CumulativeAura 3, 30 s.",
    CumulativeAura=3, **_emask(1, m.HOLY_HEAL_CASTS_AND_SHOCK),
)
dawn_before_dusk_buff_r3_201229 = _buff_spell(
    201229, 'Dawn before Dusk', [_mod(SpellModOp.CRITICAL_CHANCE, False, 2)], icon=2063, duration_ms=30000,
    aura="Critical strike chance of your Holy Light, Flash of Light and Holy Shock increased by $s1% per stack.",
    notes="paladin-rework HOLY §4.5: +3% crit per stack, CumulativeAura 3, 30 s.",
    CumulativeAura=3, **_emask(1, m.HOLY_HEAL_CASTS_AND_SHOCK),
)

pure_of_heart_mana_201230 = _buff_spell(
    201230, 'Pure of Heart', [_aura(AuraType.PERIODIC_ENERGIZE, 0, misc_value=0, amplitude=1000)],
    icon=2142, duration_ms=5000,
    aura="Restoring mana every sec.",
    notes="paladin-rework HOLY §4.5: PERIODIC_ENERGIZE mana every 1 s for 5 s, amount from the script (rank % x "
          "Intellect, [TUNE]); same caster refreshes, never stacks.",
)

spiritual_focus_crit_201231 = _buff_spell(
    201231, 'Spiritual Focus', [_mod(SpellModOp.CRITICAL_CHANCE, False, 29)], icon=1499, duration_ms=3000,
    aura="Your next Holy Light has $s1% increased critical strike chance.",
    notes="paladin-rework HOLY §4.5: +30% Holy Light crit, 1 charge; base 3 s, set by the script to the casting Holy "
          "Light's remaining cast time + 100 ms.",
    ProcCharges=1, **_emask(1, m.HOLY_LIGHT),
)

sunlight_hit_201232 = spell(
    id=201232, name='Sunlight', school=_HOLY, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=_FAR_RANGE,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=7.5, ap_potency=7.5, potency_kind='direct',
                    implicit_target_a=6)],
    spell_icon_id=2176,
    notes="paladin-rework HOLY §4.5: Sunlight hit, 15 potency hybrid (7.5 SP + 7.5 AP, [TUNE], Q10), learn 25; "
          "spell_pal_sunlight_hit scales it per rank in OnHit (33 / 66 / 100%: 13 / 27 / 40 at 60). Visual 128 stand-in. "
          "A2c's rank tooltips copy this potency as a literal expression (HOLY §4.1 exception).",
    raw_overrides=_raw(
        "Calls down Sunlight on the target, dealing {pot1} Holy damage.", level=25, dmg_class=_DMG_MAGIC,
        AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS, SpellVisualID_1=128,
    ),
)

sunlight_echo_201233 = spell(
    id=201233, name='Sunlight', school=_HOLY, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=_FAR_RANGE,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=7.5, ap_potency=7.5, potency_kind='direct',
                    implicit_target_a=6)],
    spell_icon_id=2176,
    notes="paladin-rework HOLY §4.5: Sunlight echo - identical data to 201232 (same scaling script); never rolls an echo itself.",
    raw_overrides=_raw(
        "Calls down Sunlight on the target, dealing {pot1} Holy damage.", level=25, dmg_class=_DMG_MAGIC,
        AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS, SpellVisualID_1=128,
    ),
)
scripted_by(sunlight_hit_201232, 'spell_pal_sunlight_hit')
scripted_by(sunlight_echo_201233, 'spell_pal_sunlight_hit')

holy_guidance_exposed_201234 = spell(
    id=201234, name='Holy Guidance', school=_HOLY, dispel=DispelType.MAGIC, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=_FAR_RANGE, duration_ms=20000,
    effects=[_aura(AuraType.MOD_ATTACKER_SPELL_AND_WEAPON_CRIT_CHANCE, 4, target=6)],
    spell_icon_id=2139,
    notes="paladin-rework HOLY §4.5: enemy debuff, +5% crit taken from all attackers (aura 197), 20 s, Magic dispel; "
          "joins stock spell_group 1058 (EXCLUSIVE_SAME_EFFECT).",
    raw_overrides=_raw(
        "", "Attacks against this target have $s1% increased critical strike chance.", dmg_class=_DMG_MAGIC,
        AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS | _ATTR3_ALWAYS_HIT,
    ),
)
spell_group(1058, holy_guidance_exposed_201234)

holy_guidance_guided_201235 = spell(
    id=201235, name='Holy Guidance', school=_HOLY, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=_FAR_RANGE, duration_ms=20000,
    effects=[_aura(AuraType.MOD_CRIT_CHANCE_FOR_CASTER, 4, target=21)],
    spell_icon_id=2139,
    notes="paladin-rework HOLY §4.5: ally buff, +5% crit chance of the paladin's own heals on this target (aura 308, "
          "caster-scoped, §0.2 item 4), 20 s.",
    raw_overrides=_raw(
        "", "The paladin's heals on you have $s1% increased critical strike chance.",
        AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS,
    ),
)

radiant_exorcism_cleave_201236 = spell(
    id=201236, name='Radiant Exorcism', school=_HOLY, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=_FAR_RANGE,
    effects=[_script_damage(6)],
    spell_icon_id=177,
    notes="paladin-rework HOLY §4.5: Radiant Exorcism cleave, script-valued (50% of the Exorcism), may crit on its own, "
          "no creature-type category (so C3's guaranteed Demon / Undead crit does not apply), never a seal builder. "
          "Visual 324.",
    raw_overrides=_carrier_raw(SpellVisualID_1=324),
)

overflowing_light_splash_201237 = spell(
    id=201237, name='Overflowing Light', school=_HOLY, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=_FAR_RANGE,
    effects=[_script_heal(21)],
    spell_icon_id=1868,
    notes="paladin-rework HOLY §4.5: Overflowing Light splash heal, script-valued (a share of the crit heal), CANT_CRIT.",
    raw_overrides=_carrier_raw(cant_crit=True),
)

blessed_hands_buff_201238 = spell(
    id=201238, name='Blessed Hands', school=_HOLY, attributes=_ATTR0_NO_AURA_CANCEL,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=_FAR_RANGE, duration_ms=12000,
    effects=[_aura(AuraType.MOD_HEALING_RECEIVED, 14, target=21)],
    spell_icon_id=3022,
    notes="paladin-rework HOLY §4.5 (scope fixed 2026-10-03): +15% healing received from the paladin (aura 283 applies "
          "only to its own caster's heals). SpellClassSet 10 explicit with eff1's class mask deliberately all-zero = "
          "every paladin-family heal by this caster (SpellInfo.cpp:1359-1371). Base duration 12 s is a fallback: the "
          "script sets it to the Hand's remaining duration.",
    raw_overrides=_raw(
        "", "Healing received from the paladin increased by $s1%.",
        AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS,
    ),
)


# ===========================================================================================================
# §2.1 / §5 - Purifying Power's Consecration clause: SPELLMOD_DOT on linked passives (SHARED B5.6a snapshots
# Consecration with DOT, so SPELLMOD_DAMAGE on d0 0x20 would do nothing).
# ===========================================================================================================

purifying_power_consecration_r1_201239 = spell(
    id=201239, name='Purifying Power', school=_HOLY, attributes=_ATTR0_PASSIVE_HIDDEN,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[_mod(SpellModOp.DOT, True, 9)],
    spell_icon_id=2173,
    notes="paladin-rework HOLY §2.1: hidden passive, Consecration +10% (SPELLMOD_DOT, d0 0x20), applied by "
          "linked_spell(31825, 201239, type=2) while Purifying Power rank 1 is on the player.",
    raw_overrides=_raw(**_emask(1, m.CONSECRATION)),
)
linked_spell(31825, purifying_power_consecration_r1_201239.id, type=2)

purifying_power_consecration_r2_201280 = spell(
    id=201280, name='Purifying Power', school=_HOLY, attributes=_ATTR0_PASSIVE_HIDDEN,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[_mod(SpellModOp.DOT, True, 19)],
    spell_icon_id=2173,
    notes="paladin-rework HOLY §2.1: as 201239 for rank 2, Consecration +20%; linked_spell(31826, 201280, type=2).",
    raw_overrides=_raw(**_emask(1, m.CONSECRATION)),
)
linked_spell(31826, purifying_power_consecration_r2_201280.id, type=2)
