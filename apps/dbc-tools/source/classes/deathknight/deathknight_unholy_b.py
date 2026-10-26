"""
Death Knight - S3a Unholy: spec-only rows 203456-203478 (Festering Wound and its bursts, the Necromancy / Rotten Touch /
Harbinger buffs, the minion helpers, the putrid cloud, the Gargoyle buffs, On a Pale Horse's damage, Unholy Blight's
new DoT), the creatures 300320 / 300321 and the 27829 ScriptName override. Owner: A6.
Source of truth: docs/reworks/death-knight-unholy-rework.md (tooltips and aura texts verbatim, minus cost / cooldown
sentences), .agents/plans/death-knight-rework/death-knight-rework.S3a-WP-BRIEF.md (sections 0-4, 7, decisions D3 / D4 /
D6 / D9), S3-HANDOFF U8-U10, U14, U16, U19-U26.

Ids and header names (the generator names a row from its VARIABLE name, so the variable names are frozen; the visible
`name=` is what the client shows): 203456 Festering Wound debuff - 203457 burst - 203458 overflow - 203459 death
explosion - 203460 Runic Power energize - 203461 Necromantic Energy - 203462 Rotten Touch buff - 203463 Harbinger of
Doom buff - 203464 Shadow Infusion - 203465 Dark Transformation marker - 203466 Dark Transformation cleave - 203467
Infected Claws proc aura - 203468 Infected Claws pet-spellbook display - 203469 Lesser Ghoul summon - 203470 Lesser Ghoul
counter - 203471 Corpse Explosion detonation - 203472 putrid cloud - 203473 cloud tick - 203474 area-damage ward - 203475
Gargoyle Necromancy - 203476 Gargoyle ramp - 203477 On a Pale Horse damage - 203478 Unholy Blight DoT.

Conventions: SpellClassSet 15 and EquippedItemClass -1 on every row (SpellClassSet 0 on the rows a MINION casts, so no
owner-family reader can match them), CastingTimeIndex 1, SpellLevel only on the potency rows (L6: 20 / 25 / 30 / 50),
aura texts number-free, tooltips verbatim. Family bits come from _masks.py: d2 b11 ROT_DAMAGE on the wound bursts, d2 b14
LESSER_GHOUL on the Lesser Ghoul summon, d2 b17 UNHOLY_OTHER_MAGIC on On a Pale Horse's damage, d0 b13 DEATH_COIL in the
Harbinger cost mod's effect mask; none on any buff / helper / minion spell.
"""

from lib.dsl import AuraType, Effect, EffectType, RANGE_SELF, School, SpellModOp
from lib.dsl.registry import (
    creature_model, creature_template, custom_attr, pot_text, procs_on, scripted_by, spell,
)

from . import _masks as m

# ---- Spell.dbc flag values (src/server/shared/SharedDefines.h) ----
_ATTR0_PASSIVE = 0x40
_ATTR0_DO_NOT_DISPLAY = 0x80
_ATTR0_NO_ACTIVE_DEFENSE = 0x200000
_ATTR0_AURA_IS_DEBUFF = 0x04000000
_ATTR0_NO_AURA_CANCEL = 0x80000000
_ATTR1_NO_AURA_ICON = 0x10000000
_ATTR3_DOT_STACKING_RULE = 0x80
_ATTR3_SUPPRESS_CASTER_PROCS = 0x10000
_ATTR3_ALWAYS_HIT = 0x40000
_ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
_ATTR2_CANT_CRIT = 0x20000000
_ATTR5_SPELL_HASTE_AFFECTS_PERIODIC = 0x2000
_ATTR6_IGNORE_CASTER_DAMAGE_MODIFIERS = 0x20000000
_CU_AURA_CANNOT_BE_SAVED = 0x01000000      # SpellCustomAttributes (SpellInfo.h:201)
_HIDDEN_PASSIVE = _ATTR0_PASSIVE | _ATTR0_DO_NOT_DISPLAY
_SPELLFAMILY_DEATHKNIGHT = 15
_MECHANIC_INFECTED = 22                    # Crypt Fever / Ebon Plague raise it (Unit.cpp SpellDamageBonusTaken)
_MISC_ALL_SCHOOLS = 127

# ---- Targets (SharedDefines.h) ----
_TARGET_UNIT_CASTER = 1
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_UNIT_DEST_AREA_ENEMY = 16
_TARGET_DEST_TARGET_ENEMY = 53
_TARGET_DEST_DEST = 87

# ---- Proc constants (SpellMgr.h) ----
_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS = 0x10
_PROC_SPELL_TYPE_DAMAGE = 0x1
_PROC_SPELL_PHASE_HIT = 0x2

# ---- Stock icons / visuals (WP-BRIEF section 7, 0-verify A item 4) ----
_ICON_FESTERING_WOUND = 1959               # Ability_Creature_Disease_03 (NOT 2857: hardcoded in spell_generic.cpp)
_ICON_NECROMANTIC_ENERGY = 1591
_ICON_ROTTEN_TOUCH = 1910
_ICON_HARBINGER = 3223
_ICON_SHADOW_INFUSION = 173
_ICON_DT_MARKER = 2179
_ICON_DARK_TRANSFORMATION = 90             # the talent's icon, on the hidden cleave
_ICON_INFECTED_CLAWS = 1116
_ICON_LESSER_GHOUL = 2786
_ICON_CORPSE_EXPLOSION = 1737
_ICON_RAISE_ABOMINATION = 313
_ICON_GARGOYLE_NECROMANCY = 1076
_ICON_GARGOYLE_RAMP = 2210
_ICON_ON_A_PALE_HORSE = 3005
_ICON_UNHOLY_BLIGHT = 1494
_SV_WOUND_BURST = 11452                    # Shadow_ImpactDD_Low_Chest (stock 52212 Death and Decay)
_SV_EXPLOSION = 11080                      # stock 50444 Corpse Explosion (DeathKnight_CorpseExplosion + BloodyExplosionGreen)
_SV_PUTRID_CLOUD = 8132                    # StateKit 6742: Poison_Cloud_Grobbulus.mdx on the aura's unit

# ---- Doc text (verbatim minus cost / cooldown sentences) ----
_WOUND_AURA_TEXT = 'Festering. Bursts for Shadow damage when struck by Scourge Strike, and explodes when the target dies.'
_NECROMANTIC_ENERGY_TEXT = 'Your next Scourge Strike raises a Lesser Ghoul.'
_ROTTEN_TOUCH_AURA_TEXT = 'Your next Death Coil bursts Festering Wounds on its target.'
_HARBINGER_AURA_TEXT = 'Your next Death Coil costs no Runic Power.'
_SHADOW_INFUSION_TEXT = 'Gathering shadow. At 5 stacks, your ghoul can transform.'
_SHADOW_INFUSION_AURA_TEXT = 'Gathering shadow. At full stacks, your ghoul can transform.'
_INFECTED_CLAWS_TEXT = ("Your ghoul's Claw has a 15/30% chance to infect the target with a Festering Wound. If you know "
                        "Necromancy, it instead grants your ghoul 1 Shadow Infusion.")
_LESSER_GHOUL_AURA_TEXT = 'Lesser Ghouls fight beside you.'
_GARGOYLE_NECROMANCY_AURA_TEXT = 'Your minions deal more damage.'
_GARGOYLE_RAMP_AURA_TEXT = 'Damage increased.'
_UNHOLY_BLIGHT_AURA_TEXT = 'Surrounded by a swarm of unholy insects.'


def _raw(description, aura_description=None, level=0, magic=False, melee=False, **extra):
    """The per-spell defaults of every row below, plus `extra` raw columns (applied last)."""
    raw = {
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'EquippedItemClass': -1, 'CastingTimeIndex': 1, 'RuneCostID': 0,
        'ProcChance': 101, 'SpellLevel': level,
        'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '',
        'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': description,
        'AuraDescription_Lang_Mask': 16712188 if aura_description is None else 16712190,
    }
    if aura_description is not None:
        raw['AuraDescription_Lang_enUS'] = aura_description
    if magic:
        raw['DefenseType'] = 1
        raw['PreventionType'] = 1
    if melee:
        raw['DefenseType'] = 2
        raw['PreventionType'] = 2
    raw.update(extra)
    return raw


def _chain(effects):
    return {f'EffectChainAmplitude_{i}': 1.0 for i in range(1, len(effects) + 1)}


def _self_aura(apply_aura=AuraType.DUMMY, base_points=0, misc_value=0):
    """An APPLY_AURA effect on the caster."""
    return Effect(type=EffectType.APPLY_AURA, base_points=base_points, implicit_target_a=_TARGET_UNIT_CASTER,
                  apply_aura=apply_aura, misc_value=misc_value)


def _buff(spell_id, name, effects, icon, duration_ms, description, aura_description, note, stacks=0, attributes=0,
          school=School.NORMAL, **extra):
    """A visible self buff: non-passive, no Consolidated Buffs flag, number-free aura text (custom-spells.md)."""
    raw = _raw(description, aura_description, **_chain(effects), **extra)
    if stacks:
        raw['CumulativeAura'] = stacks
    return spell(
        id=spell_id, name=name, school=school, attributes=attributes, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=duration_ms,
        effects=effects, spell_icon_id=icon, notes=note, raw_overrides=raw,
    )


def _wound_burst(spell_id, name_note, role):
    """203457 / 203458 (same data, own ids: sim and log visibility). eff0 Shadow damage with ap_potency 25 per wound,
    eff1 the DUMMY carrier of the wound count n (SPELLVALUE_BASE_POINT1; the script's OnHit multiplies by n)."""
    effects = [
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=25.0, potency_kind='direct',
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
        Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ]
    return spell(
        id=spell_id, name='Festering Wound', school=School.SHADOW, mechanic=_MECHANIC_INFECTED, attributes=0,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0,
        duration_ms=0, effects=effects, spell_icon_id=_ICON_FESTERING_WOUND,
        notes=(
            f'S3a Unholy (U8): the {role}. Shadow, DmgClass MAGIC (DefenseType 1: spell crit, Runic Focus doubles it), '
            'one cast per burst event with an n multiplier (the AP term is added once per cast, Unit.cpp:8726-8733): eff0 '
            'SCHOOL_DAMAGE ap_potency 25 direct per wound [tune] (RETUNE 2026-10-25: was 30), SpellLevel 20 (L6); '
            'eff1 DUMMY carrying n through '
            'SPELLVALUE_BASE_POINT1 (both effects target the explicit enemy so the two target lists are identical). The '
            'script (spell_dk_festering_wound_damage) OnHit multiplies by n and by Dread Host. Spell-level Mechanic 22 '
            '(INFECTED): Crypt Fever / Ebon Plague raise it (caster-scoped, max not sum); known effect (D4): the 18 '
            'INFECTED-immune templates take no wound damage. d2 b11 ROT_DAMAGE (Runic Focus, Rage of Rivendare read it). '
            'AttributesEx3 ALWAYS_HIT (the Scourge Strike / Coil already rolled the hit; a resisted burst would eat '
            f'wounds for nothing). SpellVisual 11452 (Shadow impact only). {name_note}'
        ),
        raw_overrides=_raw(
            'Bursts for {pot1} Shadow damage.', level=20, magic=True, SpellClassMask_3=m.ROT_DAMAGE,
            AttributesEx3=_ATTR3_ALWAYS_HIT, SpellVisualID_1=_SV_WOUND_BURST, **_chain(effects),
        ),
    )


# =====================================================================================================================
# Festering Wound (U8-U10): the burst 203457, the overflow 203458, the death explosion 203459 (defined first: the debuff's
# tooltip quotes the burst's potency), then the debuff itself 203456.
# =====================================================================================================================

festering_wound_burst_203457 = _wound_burst(
    203457, 'RP (3 per wound) and Wandering Plague are granted in the script AfterHit, by source.',
    'wound burst (Scourge Strike, Rotten Touch, Pestilence overflow rules in the script)')
scripted_by(festering_wound_burst_203457, 'spell_dk_festering_wound_damage')

festering_wound_overflow_203458 = _wound_burst(
    203458, 'Its own id so the combat log and the sim tell an overflow from a burst; damage only.',
    'overflow burst (a wound added at 10 stacks bursts at once)')
scripted_by(festering_wound_overflow_203458, 'spell_dk_festering_wound_damage')

# The explosion: cast by the Death Knight at the dying enemy's position (an explicit dest captured at death), 8 yd around
# it, at most 5 enemies (the script's OnObjectAreaTargetSelect: Engagement filter -> by distance -> resize(5); it must be
# registered on EFFECT_0 and EFFECT_1 because the two effects select the same area independently).
_explosion_effects = [
    Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=7.5, potency_kind='direct', implicit_target_a=_TARGET_DEST_DEST,
           implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY, radius_yards=8.0),
    Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST, implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY,
           radius_yards=8.0),
]
festering_wound_explosion_203459 = spell(
    id=203459, name='Festering Wound', school=School.SHADOW, mechanic=_MECHANIC_INFECTED, attributes=0, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0, duration_ms=0,
    effects=_explosion_effects, spell_icon_id=_ICON_FESTERING_WOUND,
    notes=(
        'S3a Unholy (U10): the death explosion of a wounded enemy. Shadow, magic class, eff0 SCHOOL_DAMAGE '
        'ap_potency 7.5 direct PER WOUND (= 30% of the 25-potency burst; RETUNE 2026-10-25: was 9 of 30),'
        ' multiplied by n (eff1 DUMMY, SPELLVALUE_BASE_POINT1) by the '
        'same damage script as the burst. SpellLevel 20 (L6). Targets: A TARGET_DEST_DEST (87, the explicit x,y,z the '
        'event casts at, captured with the map id at death) + B TARGET_UNIT_DEST_AREA_ENEMY (16), 8 yd on both effects '
        '(the script keeps the 5 nearest engaged enemies). d2 b11 ROT_DAMAGE, spell-level Mechanic 22 (D4), ALWAYS_HIT. '
        'No Runic Power, no wounds, no Wandering Plague (the script grants nothing). SpellVisual 11080 (stock Corpse '
        'Explosion: ImpactAreaKit DeathKnight_CorpseExplosion + BloodyExplosionGreen).'
    ),
    raw_overrides=_raw(
        'Explodes for {pot1} Shadow damage per wound to enemies within 8 yards.', level=20, magic=True,
        SpellClassMask_3=m.ROT_DAMAGE, AttributesEx3=_ATTR3_ALWAYS_HIT, SpellVisualID_1=_SV_EXPLOSION,
        **_chain(_explosion_effects),
    ),
)
scripted_by(festering_wound_explosion_203459, 'spell_dk_festering_wound_damage')

# The debuff: a DUMMY aura with 10 stacks, 30 s refreshed on gain (ModStackAmount(+n) refreshes), one aura per Death Knight
# (DOT_STACKING_RULE: a DUMMY from a second caster would replace it otherwise, SpellAuras.cpp:2017-2048), Dispel none, no
# class bits, never periodic or LINKED (GetDiseasesByCaster would count it, Unit.cpp:6018-6060), never d2 b1.
_wound_effects = [
    Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
]
festering_wound_203456 = spell(
    id=203456, name='Festering Wound', school=School.SHADOW, attributes=_ATTR0_AURA_IS_DEBUFF, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=30000,
    effects=_wound_effects, spell_icon_id=_ICON_FESTERING_WOUND,
    notes=(
        'S3a Unholy (U8): the Festering Wound debuff. Visible enemy debuff (AURA_IS_DEBUFF), eff0 APPLY_AURA DUMMY on the '
        'explicit enemy, 30 s, CumulativeAura 10 (stack count = wounds), AttributesEx3 DOT_STACKING_RULE (one aura per '
        'caster: another Death Knight\'s wounds are separate), Dispel none, no class bits, not periodic, not LINKED, '
        'Mechanic 0. The aura\'s caster is always the Death Knight, even when a minion adds the wound (bots read '
        'stacks(target, 203456, own)). Every adder goes through DeathKnight::AddFesteringWounds; AfterEffectRemove with '
        'AURA_REMOVE_BY_DEATH schedules the explosion (spell_dk_festering_wound). Icon 1959 (not 2857). The pulsing sore '
        'visual is V\'s. Tooltip quotes the burst\'s potency.'
    ),
    raw_overrides=_raw(
        'A festering wound. Bursts for ' + pot_text(festering_wound_burst_203457) + ' Shadow damage when struck by '
        'Scourge Strike, and explodes on nearby enemies when the target dies.',
        _WOUND_AURA_TEXT, CumulativeAura=10, AttributesEx3=_ATTR3_DOT_STACKING_RULE, **_chain(_wound_effects),
    ),
)
scripted_by(festering_wound_203456, 'spell_dk_festering_wound')

# =====================================================================================================================
# Runic Power energize, Necromantic Energy, Rotten Touch and Harbinger of Doom buffs
# =====================================================================================================================

# The self energize: the caller passes the amount (30 x wounds for bursts, 100 for a Necromancy Scourge Strike) through
# SPELLVALUE_BASE_POINT0 (RP x 10); the data value is one wound's 3 RP.
_energize_effects = [
    Effect(type=EffectType.ENERGIZE, base_points=29, implicit_target_a=_TARGET_UNIT_CASTER, misc_value=6),
]
unholy_rp_energize_203460 = spell(
    id=203460, name='Unholy Power', school=School.NORMAL, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=_energize_effects, spell_icon_id=_ICON_NECROMANTIC_ENERGY,
    notes=(
        'S3a Unholy (U9 / U14): the self energize. ENERGIZE Runic Power (misc 6) on the caster; the data value (stored 29 = '
        '3 RP) is overridden by the callers through CastCustomSpell SPELLVALUE_BASE_POINT0 = 30 x wounds (burst RP) or '
        '100 (the Necromancy Scourge Strike\'s extra 10 RP); CalcBaseValue subtracts the 1 itself (RotFC precedent '
        '203296). No cost, no family bits, SpellLevel 0.'
    ),
    raw_overrides=_raw('Generates Runic Power.', **_chain(_energize_effects)),
)

necromantic_energy_203461 = _buff(
    203461, 'Necromantic Energy', [_self_aura()], _ICON_NECROMANTIC_ENERGY, 30000,
    _NECROMANTIC_ENERGY_TEXT, _NECROMANTIC_ENERGY_TEXT,
    'S3a Unholy (U14): Necromancy\'s counter. Visible self buff (not passive, no consolidation flag), 30 s refreshed on '
    'gain, CumulativeAura 6 (the energy shows as the stack count), one DUMMY effect. Granted by Plague Strike (+3), spent by '
    'Scourge Strike (-1) in the Unholy scripts. Aura text verbatim from the doc.',
    stacks=6,
)

rotten_touch_buff_203462 = _buff(
    203462, 'Rotten Touch', [_self_aura()], _ICON_ROTTEN_TOUCH, 20000,
    'Your next Death Coil bursts Festering Wounds on its target.', _ROTTEN_TOUCH_AURA_TEXT,
    'S3a Unholy (Rotten Touch): the armed charge. Visible self buff, 20 s, one DUMMY effect, no stacks (a second proc '
    'refreshes the duration). Granted by the Plague Strike CAST proc on the Rotten Touch ranks, removed by '
    'spell_dk_death_coil_unholy when a Coil is cast at an enemy (the target is recorded on CustomData).',
)

# Harbinger: a charged cost mod, one charge, 20 s, NO spell_proc row and no trigger aura (legal: Player::RemoveSpellMods
# drops the charge of a mod without a proc entry when the affected Coil is cast, 0-verify A item 17; Death Coil is the
# only castable on d0 b13). The Coil's cost drops to 0, which is also why OnRunicPowerSpent never sees it (D10).
harbinger_of_doom_buff_203463 = _buff(
    203463, 'Harbinger of Doom',
    [_self_aura(AuraType.ADD_PCT_MODIFIER, base_points=-101, misc_value=int(SpellModOp.COST))],
    _ICON_HARBINGER, 20000, 'Your next Death Coil costs no Runic Power.', _HARBINGER_AURA_TEXT,
    'S3a Unholy (Harbinger of Doom, U24): the free Coil charge. Visible self buff, 20 s, ProcCharges 1, eff0 '
    'ADD_PCT_MODIFIER SPELLMOD_COST stored -101 (-100%) on m.DEATH_COIL (d0 b13, EffectSpellClassMaskA_1) of family 15. '
    'NO spell_proc row and no trigger aura (a second proc refreshes the duration; the Coil cast consumes the charge). '
    'Granted by the main-hand swing proc on the Harbinger ranks.',
    ProcChance=101, ProcCharges=1, EffectSpellClassMaskA_1=m.DEATH_COIL,
)

# =====================================================================================================================
# Ghoul: Shadow Infusion, the Dark Transformation marker and cleave, Infected Claws
# =====================================================================================================================

shadow_infusion_203464 = _buff(
    203464, 'Shadow Infusion', [_self_aura()], _ICON_SHADOW_INFUSION, 30000, _SHADOW_INFUSION_TEXT,
    _SHADOW_INFUSION_AURA_TEXT,
    'S3a Unholy (U22): the permanent ghoul\'s stack aura. Added with owner->AddAura(203464, ghoul) (caster = the Death '
    'Knight) by Death Coil casts and Necromancy Infected Claws procs; visible pet aura, 30 s refreshed on gain (under 60 s, '
    'so Pet::_SaveAuras skips it), CumulativeAura 5, one DUMMY effect. spell_dk_shadow_infusion sets the marker 203465 at '
    '5 stacks and clears it below. The stacks show as the count.',
    stacks=5,
)
scripted_by(shadow_infusion_203464, 'spell_dk_shadow_infusion')

# The marker: CasterAuraSpell of the castable 203448 (the Dark Transformation button greys without it). Permanent, never
# saved (a relog leaves a ghoul with no stacks), not cancellable (the player cannot drop it to grey the button).
dark_transformation_ready_203465 = _buff(
    203465, 'Dark Transformation', [_self_aura()], _ICON_DT_MARKER, -1, 'Your ghoul is ready to transform.',
    'Your ghoul is ready to transform.',
    'S3a Unholy (U22): the DK marker, CasterAuraSpell of the castable 203448 (the P0 shape: non-passive visible self '
    'DUMMY). Permanent; NO_AURA_CANCEL (0x80000000 in Attributes) so it cannot be right-clicked off; '
    'CU_AURA_CANNOT_BE_SAVED so a relog cannot restore it without the ghoul\'s stacks. Set at 5 Shadow Infusion stacks by '
    'spell_dk_shadow_infusion, removed below 5, and removed by the linked_spell row (deathknight_unholy.py) on the cast of 203448.',
    attributes=_ATTR0_NO_AURA_CANCEL,
)
custom_attr(dark_transformation_ready_203465, attributes=_CU_AURA_CANNOT_BE_SAVED)
# The linked_spell(203448, -203465, 0) row that removes the marker on the cast lives with the castable (deathknight_unholy.py).

# The cleave: cast BY THE GHOUL at its Claw / melee victim; bp = 50% of the hit's unmitigated damage (SPELLVALUE_BASE_POINT0,
# so the effect is potency_excluded), the primary is excluded by the script. Physical, melee class, 8 yd around the
# victim. ATTR3 IGNORE_CASTER_MODIFIERS: the amount is built from damage that already carries the +80%, so the engine's
# done-bonus must not boost it again (U16: excluded from the minion seam).
_cleave_effects = [
    Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=_TARGET_DEST_TARGET_ENEMY,
           implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY, radius_yards=8.0,
           potency_excluded='a share (50%) of the ghoul\'s own hit, computed by the script'),
]
dark_transformation_cleave_203466 = spell(
    id=203466, name='Dark Transformation', school=School.NORMAL, attributes=_ATTR0_NO_ACTIVE_DEFENSE, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=_cleave_effects, spell_icon_id=_ICON_DARK_TRANSFORMATION,
    notes=(
        'S3a Unholy (U22): the transformed ghoul\'s cleave, cast by the ghoul (family 0, no bits: nothing of the owner\'s '
        'matches it) at the victim of its melee / Claw hit. SCHOOL_DAMAGE potency_excluded (bp = 50% of '
        'GetUnmitigatedDamage via SPELLVALUE_BASE_POINT0), Physical, DmgClass MELEE (DefenseType 2), cannot be dodged / '
        'parried / blocked. Area: A TARGET_DEST_TARGET_ENEMY (53, the victim\'s position) + B TARGET_UNIT_DEST_AREA_ENEMY (16), '
        '8 yd; the script drops the primary and keeps only enemies engaged with the owner or group. AttributesEx3 '
        'SUPPRESS_CASTER_PROCS (never retriggers the cleave) | ALWAYS_HIT | IGNORE_CASTER_MODIFIERS (the amount already '
        'carries the +80%; excluded from the seam) | AttributesEx2 CANT_CRIT (the amount already includes the hit\'s crit). SpellLevel 0 (no potency).'
    ),
    raw_overrides=_raw(
        'Strikes the enemies around the target for a share of the damage dealt.', melee=True, SpellClassSet=0,
        AttributesEx2=_ATTR2_CANT_CRIT,
        AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS | _ATTR3_ALWAYS_HIT | _ATTR3_IGNORE_CASTER_MODIFIERS,
        **_chain(_cleave_effects),
    ),
)
scripted_by(dark_transformation_cleave_203466, 'spell_dk_dark_transformation_cleave')

# Infected Claws: the hidden proc aura on the permanent ghoul. It is added with owner->AddAura (caster = the Death Knight:
# the engine multiplies the proc chance by the DK's Proc Chance only for a player caster, SpellAuras.cpp:2330-2333). The pet
# holds it, so the pet's Claw 47468 (melee-class spell, DmgClass MELEE) procs it: the spell_proc row catches melee-class
# spell hits (flag 0x10) in the HIT phase; spell_dk_infected_claws_pet.CheckProc keeps only Claw, rolls the talent rank %
# (15 / 30) x Proc Chance once per Claw, and Proc adds the wound or the Shadow Infusion.
_infected_claws_effects = [_self_aura()]
infected_claws_aura_203467 = spell(
    id=203467, name='Infected Claws', school=School.SHADOW, attributes=_HIDDEN_PASSIVE, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=_infected_claws_effects, spell_icon_id=_ICON_INFECTED_CLAWS,
    notes=(
        'S3a Unholy (U23): the hidden owner-cast proc aura on the Master of Ghouls pet. Hidden passive (0x40 | 0x80; a '
        'passive is never saved, so it is re-added on OnPetAddToWorld), duration -1, one DUMMY effect. spell_proc row: '
        'PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS (0x10; the Claw\'s procAttacker is 0x10 | main-hand, 0-verify B 13), family 0 '
        '(Claw has none), spell type DAMAGE, phase HIT (2), chance 100: the rank chance (15 / 30%) x Proc Chance is '
        'rolled in the script\'s CheckProc, which also keeps only Claw 47468 and once per Claw. Wound / Shadow Infusion in '
        'Proc. The display passive 203468 is separate.'
    ),
    raw_overrides=_raw(_INFECTED_CLAWS_TEXT, ProcChance=100, **_chain(_infected_claws_effects)),
)
procs_on(infected_claws_aura_203467, proc_flags=_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS,
         spell_type_mask=_PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=_PROC_SPELL_PHASE_HIT, chance=100.0)
scripted_by(infected_claws_aura_203467, 'spell_dk_infected_claws_pet')

# The pet-spellbook display (D6): the pet learns it in DeathKnight::ApplyInfectedClaws (learnSpell / removeSpell by whether
# the owner knows a rank). A passive DUMMY with SpellLevel 0 and no aura icon, so the spellbook shows it and the aura bar
# does not; no SkillLineAbility, no creature_template_spell.
_infected_claws_display_effects = [_self_aura()]
infected_claws_display_203468 = spell(
    id=203468, name='Infected Claws', school=School.SHADOW, attributes=_ATTR0_PASSIVE, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=_infected_claws_display_effects, spell_icon_id=_ICON_INFECTED_CLAWS,
    notes=(
        'S3a Unholy (D6 / U23 Q6): display-only pet passive. Attributes PASSIVE (0x40, not DO_NOT_DISPLAY: the pet '
        'spellbook / bar lists it), AttributesEx NO_AURA_ICON (0x10000000: no aura-bar icon), one DUMMY effect, SpellLevel 0, '
        'no aura text, tooltip = the talent\'s. learnSpell(203468) / removeSpell(203468) by DeathKnight::ApplyInfectedClaws; '
        'no SkillLineAbility, no creature_template_spell (26125\'s four slots are full). Does nothing itself.'
    ),
    raw_overrides=_raw(_INFECTED_CLAWS_TEXT, AttributesEx=_ATTR1_NO_AURA_ICON, **_chain(_infected_claws_display_effects)),
)

# =====================================================================================================================
# Lesser Ghoul: the summon, the counter, the detonation (Corpse Explosion)
# =====================================================================================================================

# D3: a dest-only SUMMON has no unit TargetInfo, so the script runs in AfterCast. Props 61 (ALLY guardian, no slot, no pet
# bar), implicit A 87 (an explicit dest at the target's position, D17), finite 11 s (RETUNE 2026-10-25, user ruling: was
# 15 s; a SPELLMOD_DURATION skips
# infinite durations, Player.cpp:10066), d2 b14 so Night of the Dead's flat +2 / 4 s duration mod reaches it.
_lesser_ghoul_summon_effects = [
    Effect(type=EffectType.SUMMON, implicit_target_a=_TARGET_DEST_DEST, misc_value=300320),
]
lesser_ghoul_summon_203469 = spell(
    id=203469, name='Raise Lesser Ghoul', school=School.NORMAL, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=11000,
    effects=_lesser_ghoul_summon_effects, spell_icon_id=_ICON_LESSER_GHOUL,
    notes=(
        'S3a Unholy (U19): summons the Lesser Ghoul guardian (creature 300320). eff0 SUMMON, implicit A 87 '
        '(TARGET_DEST_DEST, D17: the caster passes an explicit dest at the target\'s position, so a Coil at the friendly ghoul '
        'or a dead target still summons), EffectMiscValueB 61 '
        '(SummonProperties 61: Category ALLY, Type GUARDIAN, Slot 0: no pet bar, SummonGuardian path), finite 11 s '
        '(RETUNE 2026-10-25, user ruling: was 15 s; 15 s with Night of the Dead 2/2) '
        '(the duration SPELLMOD_DURATION reaches, applied at SpellEffects.cpp:6465 for guardians), d2 b14 LESSER_GHOUL '
        '(Night of the Dead\'s +2 / 4 s). Cast TRIGGERED_FULL_MASK. Dest-only: no TargetInfo, so '
        'spell_dk_lesser_ghoul_summon runs in AfterCast (D3: start timer on CustomData, CapMinions(300320, 8), counter '
        'recount). SpellLevel 0.'
    ),
    raw_overrides=_raw(
        'Raises a Lesser Ghoul to fight beside you.', SpellClassMask_3=m.LESSER_GHOUL, EffectMiscValueB_1=61,
        **_chain(_lesser_ghoul_summon_effects),
    ),
)
scripted_by(lesser_ghoul_summon_203469, 'spell_dk_lesser_ghoul_summon')

# The counter: stack = Lesser Ghouls alive, recounted on add / remove world. Infinite and never saved (a relog must not
# bring back a count with no ghouls). The cap is 8 [tune]; the stack ceiling leaves headroom for a retune.
lesser_ghoul_counter_203470 = _buff(
    203470, 'Lesser Ghouls', [_self_aura()], _ICON_LESSER_GHOUL, -1, _LESSER_GHOUL_AURA_TEXT, _LESSER_GHOUL_AURA_TEXT,
    'S3a Unholy (U19, Q5 = yes): the Lesser Ghoul counter. Visible self buff (not passive, no consolidation flag), '
    'permanent, one DUMMY effect, CumulativeAura 20 (cap 8 [tune] plus headroom), CU_AURA_CANNOT_BE_SAVED so a relog never '
    'restores a count with no ghouls. SetStackAmount(alive count) by DeathKnight::RefreshLesserGhoulCounter; removed at 0.',
    stacks=20,
)
custom_attr(lesser_ghoul_counter_203470, attributes=_CU_AURA_CANNOT_BE_SAVED)

# The detonation: cast at a POSITION in both branches (the ghoul at its own position, the Death Knight at the corpse
# position): A TARGET_DEST_DEST (87) + B TARGET_UNIT_DEST_AREA_ENEMY (16), like the death explosion 203459.
_detonation_effects = [
    Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=80.0, potency_kind='direct', implicit_target_a=_TARGET_DEST_DEST,
           implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY, radius_yards=8.0),
]
corpse_explosion_detonation_203471 = spell(
    id=203471, name='Corpse Explosion', school=School.SHADOW, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0, duration_ms=0,
    effects=_detonation_effects, spell_icon_id=_ICON_CORPSE_EXPLOSION,
    notes=(
        'S3a Unholy (U20): the Corpse Explosion detonation. Shadow, magic class (DefenseType 1), eff0 SCHOOL_DAMAGE '
        'ap_potency 80 direct [tune], SpellLevel 30 (L6), 8 yd around the explicit dest '
        '(A TARGET_DEST_DEST 87 + B TARGET_UNIT_DEST_AREA_ENEMY 16): the Lesser Ghoul casts it at its own position, the Death '
        'Knight at the corpse position (CastSpell x, y, z). Family 0 / no bits: Impurity (a lookup on the caster) never applies to the ghoul branch and '
        'the corpse branch applies the minion terms in its own script. Triggered; ALWAYS_HIT. The script (OnHit) scales by '
        'the ghoul\'s remaining-duration fraction, filters to engaged enemies and unsummons the ghoul in AfterCast. '
        'SpellVisual 11080 (stock Corpse Explosion).'
    ),
    raw_overrides=_raw(
        'Detonates for {pot1} Shadow damage to all enemies within 8 yards.', level=30, magic=True, SpellClassSet=0,
        AttributesEx3=_ATTR3_ALWAYS_HIT, SpellVisualID_1=_SV_EXPLOSION, **_chain(_detonation_effects),
    ),
)
scripted_by(corpse_explosion_detonation_203471, 'spell_dk_corpse_explosion_detonation')

# =====================================================================================================================
# Raise Abomination: the putrid cloud, its tick, and the area-damage ward
# =====================================================================================================================

# The tick: cast by the Abomination (family 0) at each engaged enemy within 8 yd of it (the cloud aura's periodic script
# collects them). time_basis_ms 1000: the cloud ticks on a fixed 1 s timer (L2).
_cloud_tick_effects = [
    Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=9.0, potency_kind='direct', time_basis_ms=1000,
           implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
]
putrid_cloud_tick_203473 = spell(
    id=203473, name='Putrid Cloud', school=School.SHADOW, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=_cloud_tick_effects, spell_icon_id=_ICON_RAISE_ABOMINATION,
    notes=(
        'S3a Unholy (U21): one cloud tick on one enemy, cast by the Abomination. Shadow, magic class, eff0 SCHOOL_DAMAGE '
        'ap_potency 9 direct [tune] (RETUNE 2026-10-25: was 12) '
        'with time_basis_ms 1000 (L2: the fixed 1 s cadence), SpellLevel 50 (L6). Explicit enemy '
        'target. Family 0 / no bits (minion damage: Mastery once and All Will Serve through the seam; not Impurity). '
        'AttributesEx3 SUPPRESS_CASTER_PROCS (rolls no procs) | ALWAYS_HIT (a minion\'s tick must not miss).'
    ),
    raw_overrides=_raw(
        'The cloud deals {pot1} Shadow damage.', level=50, magic=True, SpellClassSet=0,
        AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS | _ATTR3_ALWAYS_HIT, **_chain(_cloud_tick_effects),
    ),
)

# The cloud: PERIODIC_DUMMY on the Abomination, fixed 1000 ms (no SPELL_HASTE_AFFECTS_PERIODIC bit: haste never adds
# ticks), visible so the Grobbulus cloud state kit (SV 8132) shows on the unit.
_cloud_effects = [
    Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=1000,
           implicit_target_a=_TARGET_UNIT_CASTER),
]
putrid_cloud_203472 = spell(
    id=203472, name='Putrid Cloud', school=School.SHADOW, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=_cloud_effects, spell_icon_id=_ICON_RAISE_ABOMINATION,
    notes=(
        'S3a Unholy (U21): the Abomination\'s cloud. eff0 APPLY_AURA PERIODIC_DUMMY amplitude 1000, no '
        'SPELL_HASTE_AFFECTS_PERIODIC (fixed cadence), permanent (the Abomination leaves at 20 s). Aura '
        'on the unit so AttributesEx NO_AURA_ICON (client-only: no buff-bar icon; the aura keeps its slot so the visual should still attach, UNTESTED in the client; fall back to dropping the flag if the cloud vanishes), no aura text. SpellVisualID_1 8132 (StateKit 6742 = Poison_Cloud_Grobbulus.mdx, attached to the unit and following '
        'it; 0-verify A item 4) shows. spell_dk_putrid_cloud OnEffectPeriodic casts the tick 203473 from the Abomination at '
        'each engaged enemy within 8 yd and adds a wound every 3rd tick per enemy (not under Necromancy). Family 0.'
    ),
    raw_overrides=_raw(
        'A putrid cloud deals ' + pot_text(putrid_cloud_tick_203473) + ' Shadow damage every 1 sec to all enemies within '
        '8 yards, and infects each enemy inside with a Festering Wound every 3 sec.',
        None,
        SpellClassSet=0, SpellVisualID_1=_SV_PUTRID_CLOUD, AttributesEx=_ATTR1_NO_AURA_ICON, **_chain(_cloud_effects),
    ),
)
scripted_by(putrid_cloud_203472, 'spell_dk_putrid_cloud')

# The ward ("like a totem"): aura 310 (creature area damage) and aura 229 (area damage), -100% for all schools, read in
# CalculateAOEDamageReduction (Unit.cpp:16076-16083). Area CC and debuffs still land. Hidden passive, applied by the
# Abomination's / Gargoyle's AI on spawn.
_ward_effects = [
    _self_aura(310, base_points=-101, misc_value=_MISC_ALL_SCHOOLS),
    _self_aura(AuraType.MOD_AOE_DAMAGE_AVOIDANCE, base_points=-101, misc_value=_MISC_ALL_SCHOOLS),
]
minion_area_ward_203474 = spell(
    id=203474, name='Unholy Ward', school=School.SHADOW, attributes=_HIDDEN_PASSIVE, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=_ward_effects, spell_icon_id=_ICON_RAISE_ABOMINATION,
    notes=(
        'S3a Unholy (U21, Q12 = yes): the area-damage ward of the Abomination and the Gargoyle. Hidden passive, permanent, '
        'eff0 aura 310 MOD_CREATURE_AOE_DAMAGE_AVOIDANCE and eff1 aura 229 MOD_AOE_DAMAGE_AVOIDANCE, both stored -101 (-100%) '
        'misc 127 (all schools). "Like a totem" holds for damage only. Family 0.'
    ),
    raw_overrides=_raw('Takes no damage from area effects.', SpellClassSet=0, **_chain(_ward_effects)),
)

# =====================================================================================================================
# Summon Gargoyle: the Death Knight's Necromancy stacks and the Gargoyle's Runic Power ramp
# =====================================================================================================================

# 30 s duration only as a safety net (the Gargoyle lives at most 26 s; the script removes the aura when it leaves): a
# missed removal can never leave a permanent minion buff. Never saved.
gargoyle_necromancy_203475 = _buff(
    203475, 'Gargoyle Necromancy', [_self_aura()], _ICON_GARGOYLE_NECROMANCY, 30000, 'Your minions deal 3% more damage.',
    _GARGOYLE_NECROMANCY_AURA_TEXT,
    'S3a Unholy (U16 / U18): the Necromancy build\'s Gargoyle Strike buff on the Death Knight. Visible self buff, '
    'CumulativeAura 10, one DUMMY effect read by the minion damage seam (3% per stack, DeathKnightData const). The '
    '30 s duration is only a safety net (the Gargoyle lives at most 26 s; the AI removes the aura at fly-away and on '
    'remove-world); CU_AURA_CANNOT_BE_SAVED so a relog cannot restore it.',
    stacks=10,
)
custom_attr(gargoyle_necromancy_203475, attributes=_CU_AURA_CANNOT_BE_SAVED)

# The ramp on the Gargoyle: +1% per stack to all schools (aura 79), one stack per 10 Runic Power the Death Knight spends.
gargoyle_ramp_203476 = _buff(
    203476, 'Gargoyle Frenzy',
    [_self_aura(AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=0, misc_value=_MISC_ALL_SCHOOLS)],
    _ICON_GARGOYLE_RAMP, 30000, 'Damage increased.', _GARGOYLE_RAMP_AURA_TEXT,
    'S3a Unholy (U18): the Gargoyle\'s Runic Power ramp. Visible aura on the Gargoyle (added with the Death Knight as '
    'caster), eff0 MOD_DAMAGE_PERCENT_DONE misc 127 stored 0 (+1% per stack), CumulativeAura 100 (an upper bound: a 20 s '
    'window never spends that much), 30 s as a safety net (the Gargoyle lives at most 26 s). One stack per 10 RP spent '
    '(OnRunicPowerSpent ramp branch).',
    stacks=100,
)

# =====================================================================================================================
# On a Pale Horse's damage and Unholy Blight's DoT
# =====================================================================================================================

_oph_effects = [
    Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=40.0, potency_kind='direct',
           implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
]
on_a_pale_horse_damage_203477 = spell(
    id=203477, name='On a Pale Horse', school=School.SHADOW, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0, duration_ms=0,
    effects=_oph_effects, spell_icon_id=_ICON_ON_A_PALE_HORSE,
    notes=(
        'S3a Unholy (U26): On a Pale Horse\'s hit on each enemy Pestilence hits, the primary included. Shadow, magic class, '
        'eff0 SCHOOL_DAMAGE ap_potency 40 direct [tune], SpellLevel 25 (L6), explicit enemy target, 50000 yd (cast from the '
        'Pestilence script at any engaged enemy within the widened radius). Family 15 with d2 b17 UNHOLY_OTHER_MAGIC only '
        '(Runic Focus reads it; a spell for Impurity, not disease damage). Triggered. AttributesEx3 SUPPRESS_CASTER_PROCS '
        '(rolls no procs). SpellVisual 11452 (a Shadow burst on each enemy).'
    ),
    raw_overrides=_raw(
        'Deals {pot1} Shadow damage.', level=25, magic=True, SpellClassMask_3=m.UNHOLY_OTHER_MAGIC,
        AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS, SpellVisualID_1=_SV_WOUND_BURST, **_chain(_oph_effects),
    ),
)

# Unholy Blight's DoT (both 50536 hardcodes go inert: the disease-dispel block and the friendly zero). Per-tick amount =
# 10% of the Coil's damage x hasted amplitude / max duration, set by spell_dk_unholy_blight_rework through
# CastDelayedSpellWithPeriodicAmount (so the effect is potency_excluded). Haste shortens the tick (the hasted tick count the
# doc's carry-over rule needs); the duration stays 10 s. Dispel none, no class bits, cannot crit, ignores caster modifiers.
_blight_effects = [
    Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=1000,
           implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, misc_value=_MISC_ALL_SCHOOLS,
           potency_excluded='a share of the Coil\'s damage'),
]
unholy_blight_dot_203478 = spell(
    id=203478, name='Unholy Blight', school=School.SHADOW, attributes=_ATTR0_AURA_IS_DEBUFF, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0, duration_ms=10000,
    effects=_blight_effects, spell_icon_id=_ICON_UNHOLY_BLIGHT,
    notes=(
        'S3a Unholy (U25): the new Unholy Blight DoT (stock 50536 has two core hardcodes, the disease-dispel clause in '
        'Unit.cpp and the friendly zero in SpellAuras.cpp, both inert for a new id). Shadow, visible enemy debuff, 10 s, eff0 '
        'PERIODIC_DAMAGE amplitude 1000, potency_excluded (the amount is a share of the Coil\'s damage, set per cast by '
        'CastDelayedSpellWithPeriodicAmount). Dispel none, no class bits (family 15 only), AttributesEx2 CANT_CRIT, '
        'AttributesEx3 IGNORE_CASTER_MODIFIERS | ALWAYS_HIT (as stock 50536) + AttributesEx6 IGNORE_CASTER_DAMAGE_MODIFIERS (the Coil\'s damage already '
        'carries its modifiers), AttributesEx5 SPELL_HASTE_AFFECTS_PERIODIC (the hasted tick count of the carry-over rule).'
    ),
    raw_overrides=_raw(
        'Surrounded by a vile swarm of unholy insects, taking damage over 10 sec.', _UNHOLY_BLIGHT_AURA_TEXT, magic=True,
        AttributesEx2=_ATTR2_CANT_CRIT,
        AttributesEx3=_ATTR3_IGNORE_CASTER_MODIFIERS | _ATTR3_ALWAYS_HIT, AttributesEx5=_ATTR5_SPELL_HASTE_AFFECTS_PERIODIC,
        AttributesEx6=_ATTR6_IGNORE_CASTER_DAMAGE_MODIFIERS, **_chain(_blight_effects),
    ),
)

# =====================================================================================================================
# Creatures (keep the variable names: they fix NPC_LESSER_GHOUL / NPC_ABOMINATION / NPC_EBON_GARGOYLE)
# =====================================================================================================================

# Lesser Ghoul 300320 (U19): a copy of the Risen Ghoul 26125 template columns (live: unit_class 4, family 40, type 6,
# type_flags 4096, unit_flags2 2048, speed_run 1.14286, 2.0 s swings, CreatureImmunitiesId -93, HealthModifier 1,
# flags_extra 0) as its own entry: 26125 would bring IsPetGhoul's 802 AP, Pet.cpp's ghoul branch and the stock Corpse
# Explosion check. Faction 35 (SummonGuardian copies the owner's faction at summon), levels 1/1 (set from the owner), NOT
# selectable-flagged: it takes area damage and the detonation targets it. Displays 24992-24995 (the stock ghoul's four
# looks, one chosen by probability) at scale 0.6.
lesser_ghoul_300320 = creature_template(
    300320, 'Lesser Ghoul', ScriptName='npc_dk_lesser_ghoul', minlevel=1, maxlevel=1, faction=35, speed_walk=1.0,
    speed_run=1.14286, detection_range=20.0, DamageModifier=1.0, BaseAttackTime=2000, RangeAttackTime=2000,
    unit_class=4, unit_flags=0, unit_flags2=2048, family=40, type=6, type_flags=4096, HealthModifier=1.0,
    RegenHealth=1, CreatureImmunitiesId=-93, flags_extra=0,
)
creature_model(300320, display_id=24992, scale=0.6, idx=0, probability=1.0)
creature_model(300320, display_id=24993, scale=0.6, idx=1, probability=1.0)
creature_model(300320, display_id=24994, scale=0.6, idx=2, probability=1.0)
creature_model(300320, display_id=24995, scale=0.6, idx=3, probability=1.0)

# Abomination 300321 (U21): a plain melee guardian (warrior stats, undead), Stitched Horror 1693. Common guardian columns
# of the warlock guardians (faction 35, flags_extra 66 = CIVILIAN | NO_XP, detection 0, 2.0 s swings); selectable and
# attackable (no unit_flags): it takes no area damage through the ward 203474, not through flags.
abomination_300321 = creature_template(
    300321, 'Abomination', ScriptName='npc_dk_abomination', minlevel=1, maxlevel=1, faction=35, speed_walk=1.0,
    speed_run=1.14286, detection_range=0.0, DamageModifier=1.0, BaseAttackTime=2000, RangeAttackTime=2000,
    unit_class=1, unit_flags=0, family=0, type=6, HealthModifier=1.0, RegenHealth=0, flags_extra=66,
)
creature_model(300321, display_id=1693, scale=1.0)

# The Gargoyle (U17): the stock entry 27829 keeps EVERY column (the helper starts from the live row; Pet.cpp:1346-1361 adds
# the scaling auras only to 27829, so no clone); only the AI changes.
ebon_gargoyle_27829 = creature_template(27829, 'Ebon Gargoyle', ScriptName='npc_dk_ebon_gargoyle_rework')
