"""
Hunter pet families F3 (.agents/plans/hunter-pet-families/hunter-pet-families.PLAN.md §3.3, §4.1, §5;
hunter-pet-families.F3.HANDOFF.md on top of F1.HANDOFF): the 10 Cunning families without a kit get their full kit. Per
family, in the §3.3 table order (Bat, Bird of Prey, Wind Serpent, Dragonhawk, Ravager, Serpent, Sporebat, Nether Ray,
Chimaera, Silithid): Command I and II, their two "Command I/II: <ability>" display passives, a slot 2 group effect and a
slot 3 utility, and their two SkillLineAbility rows (AcquireMethod 2, learned at the pet level = SpellLevel). Spider is
done (F0).

Ids (PLAN §4.1, the F3 column): commands 201640-201659 (Command I then II per family), command helpers 201670-201675
(Chimaera's Twin Bite second bite, Froststorm Breath's tick, Constrict's and Venom Web Spray's roots, Fungal Bloom's and
Spore Burst's splashes), displays 202143-202162 (command order), slot 2 201771-201780, slot 3 202004-202013, utility
helper 202032 (Shed Skin's cleanse + heal), SkillLineAbility 30636-30639 + 30870-30885 (slot 2 then slot 3 per family),
spell_group 1233 (the new aura 65 spell haste group, F3 review MAJOR 1). 202033-202039 stay free.

Rules (the F1 / F2 files' rules, with the Cunning specifics):
- Potency (ruling 1): every Command I is kits.command_potency(x, 'I'), every Command II kits.command_potency(x, 'II')
  of the §3.3 number (a DoT's or a channel's number is its total). Ruling 23 (user 2026-11-13): every Cunning damage
  potency also takes kits.CUNNING_DAMAGE_SCALE (x0.39), passed as `cunning=True`; the §3.3 number stays the first
  argument. The `notes` strings below quote the pre-ruling-23 numbers (x0.84 / x0.65 of §3.3); `_command` and
  `_damage_helper` append kits.RULING_23_NOTE to each. Ruling 24 (PLAN §11): every single-target command and its
  non-area damage helper (Twin Bite's Nature bite) also passes `single_target=True` (a further x0.94,
  kits.CUNNING_ST_COMMAND_SCALE) and its notes carry kits.ruling_24_note; the AoE commands (Sonic Bite, Shriek, Chain
  Lightning, Flame Nova, Spore Burst, Fungal Bloom, Froststorm Breath, Swarm Spit), their splashes and the Froststorm
  tick are Beast Cleave-excluded and keep ruling 23's numbers.
- Range: Cunning commands reach 30 yd (PLAN §3.3) with the Cunning defaults' DmgClass RANGED (Feint Strike 201734,
  Venomous Cloud 201729). The two cones (Shriek, Froststorm Breath) keep the F1 / F2 cone range, the pet's melee reach:
  a cone starts at the pet, so a 30 yd press would land an 8 yd cone on nothing.
- Every slot 2 / slot 3 utility carries d1 b28 + b29 (kits.utility_raw). No Cunning utility is a ruling 10 exception.
  Group effects use TargetA 56 (ruling 7). Every slot 3 is manual; every slot 2 autocasts (PET_KIT_GROUP_AUTOCAST on
  all ten kit rows). Enemy-target Cunning utilities reach 30 yd (Sticky Webbing / Web Pull, F0).
- Rule 17 exceptions keep full potency: Bat (Sonic Bite's one bounce at 50% is EffectChainAmplitude 0.5, the Leaping
  Tear shape) and Sporebat (its extra targets take 50% through a splash helper bound to spell_hun_command_splash, the
  Venomous Cloud shape). Neither is bound to spell_hun_command_aoe_falloff.
- Scripts (PLAN §5.2), bound below, all F0-F2 generic scripts: falloff (Shriek, Chain Lightning, Flame Nova,
  Froststorm Breath's tick, Swarm Spit), multihit (Chimaera's Twin Bite, one follow-up), pulse (Froststorm Breath: the
  channel's periodic trigger casts the cone tick at the stashed primary), splash (Spore Burst's and Fungal Bloom's
  splashes), boss (Snatch, Blinding Flash, Frost Nova, the Constrict and Venom Web Spray roots), absorb (Swarm Shield).
- Unlock levels: the class equivalent's level on this server (trainer_spell, or the spell row's SpellLevel), never
  below 10; 30 where nothing matches (F0's Tail Sweep rule).

Imports only helpers and constants from the sibling modules (never a spell object: lib/dsl/registry.py
_collect_var_names keeps the first module's name for an id).
"""

from lib.dsl import AuraType, Effect, EffectType, School
from lib.dsl.registry import pot_text, scripted_by, skill_line_ability, spell, spell_group, spell_group_rule
from . import _masks as m
from . import _pet_kits as kits
from .hunter_bm_spells import COMMAND_AOE_FALLOFF_PCT, _cmd_raw, _direct, _display, _dot, _PET_SCALING

# ---- unlock levels (pet level = SpellLevel; see the module docstring) ----
SCREECH_LEVEL = 14                  # Demoralizing Shout 1160 (trainer 14), Demoralizing Screech's level (F1)
SONIC_BLAST_LEVEL = 16              # Pummel 6552 (trainer 16), the Gorilla's Pummel (F2)
KEEN_SIGHT_LEVEL = 40               # Moonkin Aura 24907 (SpellLevel 40)
SNATCH_LEVEL = 18                   # Disarm 676 (trainer 18), Disarming Pincer's level (F2)
STORM_BREATH_LEVEL = 32             # Curse of the Elements 1490 (SpellLevel 32)
GALE_BARRIER_LEVEL = 30             # no class equivalent (a raid magic cut): F0's Tail Sweep rule, Earthen Bulwark's
SCORCHING_BREATH_LEVEL = 32         # Curse of the Elements 1490 (SpellLevel 32)
BLINDING_FLASH_LEVEL = 30           # no class equivalent at 2 s AoE: Earthshaking Stomp's level (F1)
RENDING_CLAWS_LEVEL = 10            # Sunder Armor 7386 (trainer 10)
CHITINOUS_SHELL_LEVEL = 30          # no class equivalent at -30% for 10 s: Molten Hide's level (F1)
PARALYZING_VENOM_LEVEL = 26         # Curse of Tongues 1714 (trainer 26), Sticky Webbing's level (F0)
SHED_SKIN_LEVEL = 30                # no class equivalent: F0's Tail Sweep rule
ENERGIZING_SPORES_LEVEL = 26        # Fire Attunement 202209 (SpellLevel 26, the shaman's 5% spell haste)
RESTORATIVE_SPORES_LEVEL = 30       # Tranquility 740 (trainer 30), Spirit Mend's level (F1)
NETHER_CURRENTS_LEVEL = 26          # Fire Attunement 202209 (SpellLevel 26)
NETHER_PULSE_LEVEL = 16             # Pummel 6552 (trainer 16)
ARCANE_RESONANCE_LEVEL = 26         # Fire Attunement Spell Power 202212 (SpellLevel 26, BaseLevel 28)
FROST_NOVA_LEVEL = 10               # Frost Nova 122 (trainer 10)
QIRAJI_FORTITUDE_LEVEL = 10         # Power Word: Fortitude 1243 (trainer 1), raised to 10
SWARM_SHIELD_LEVEL = 10             # Power Word: Shield 17 (trainer 6), raised to 10, Bubble Shield's level (F2)

# Aura and effect types the DSL enum doesn't name (SpellAuraDefines.h / SharedDefines.h).
_AURA_MOD_RESISTANCE_PCT = 101
_AURA_HASTE_SPELLS = 216
_EFFECT_DISPEL_MECHANIC = 108
_DISPEL_POISON = 4
_MECHANIC_DISARM = 3
_MECHANIC_ROOT = 7
_MECHANIC_SNARE = 11
_MECHANIC_STUN = 12
_MECHANIC_BLEED = 15
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_UNIT_SRC_AREA_ENEMY = 15
_TARGET_UNIT_DEST_AREA_ENEMY = 16
_TARGET_SRC_CASTER = 22
_TARGET_UNIT_MASTER = 27
_TARGET_DEST_TARGET_ENEMY = 53
_TARGET_UNIT_CASTER_AREA_RAID = 56
_TARGET_UNIT_CONE_ENEMY = 104

_ATTR1_IS_CHANNELED = 0x4           # AttributesEx: a channel (SpellInfo::IsChanneled; the dispatcher keeps facing)
_ATTR1_NO_AUTOCAST_AI = 0x20000     # AttributesEx: the pet AI never autocasts it (the manual raid cooldowns)
_SUPPRESS_CASTER_PROCS = 0x10000    # AttributesEx3: a helper procs nothing of its own
_SCHOOL_MASK_ALL = 127
_SCHOOL_MASK_MAGIC = 126            # every school but Physical
_SCHOOL_MASK_PHYSICAL = 1
_GROUP_BUFF_RADIUS_YD = 100.0       # Roar of Courage / Furious Howl
_AREA_RADIUS_YD = 8.0               # every Cunning AoE command (the F1 / F2 radius)
_CUNNING_RANGE_YD = 30.0            # PLAN §3.3: Cunning commands and enemy-target utilities
_HELPER_RANGE_YD = 40.0             # a helper a 30 yd command triggers: a triggered cast is range-checked strictly
_SPLASH_RANGE_YD = 50000.0          # Venomous Cloud's splash 201736 (the DEST area sits at the primary)
_SPLASH_PCT = COMMAND_AOE_FALLOFF_PCT['value']
_SPLASH_TAIL = '% damage.'
_FALLOFF_TEXT = f" Enemies other than the target take {_SPLASH_PCT}{_SPLASH_TAIL}"
_BOUNCE_AMPLITUDE = 0.5             # Sonic Bite's bounce (the Leaping Tear 201725 shape)

SPELL_GROUP_RAID_DAMAGE_TAKEN = 1232   # PLAN §4.1 / ruling 7: F2 declared it (rule 4) with Earthen Bulwark
# F3 review MAJOR 1: aura 65 (MOD_CASTING_SPEED_NOT_STACK) does not limit itself in this core. AuraEffect::
# HandleModCastingSpeed keeps only the largest copy solely through rule 3 (same effect) spell_group rows
# (Unit::GetHighestExclusiveSameEffectSpellGroupValue), and no stock group held an aura 65 spell. So the two pet buffs,
# Fire Attunement 202209 and Wrath of Air 2895 share this new group; the auras stay, only the highest applies.
SPELL_GROUP_SPELL_HASTE = 1233
_FIRE_ATTUNEMENT = 202209              # shaman_attunements.py (also in its own group 1252, rule 2)
_WRATH_OF_AIR = 2895                   # the stock totem's aura (Wrath of Air Totem 3738, still trained at 64)


def _command(spell_id, name, effects, visual, icon, description, *, school=School.NORMAL, ranged=True,
             duration_ms=None, notes='', **raw):
    """A commanded pet spell (the F1 / F2 template): pet-cast, instant, no cost / cooldown / GCD, d1 b28 + d2 b22,
    SpellLevel 1. Ranged by default (30 yd, DmgClass RANGED, PreventionType 1: the Cunning defaults); `ranged=False`
    is the melee cone shape (RangeIndex 2, DmgClass MELEE). `raw` wins."""
    raw_overrides = {**_cmd_raw(visual, dmg_class=3 if ranged else 2, prevention=1 if ranged else 2),
                     'SpellIconID': icon, 'Description_Lang_enUS': description, **raw}
    if not ranged:
        raw_overrides['RangeIndex'] = 2
    kwargs = {'duration_ms': duration_ms} if duration_ms is not None else {}
    return spell(
        id=spell_id, name=name, school=school, attributes=0x50010, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=_CUNNING_RANGE_YD if ranged else 5.0,
        effects=effects, pet_owner_scaling=_PET_SCALING, notes=notes + kits.RULING_23_NOTE,
        raw_overrides=raw_overrides, **kwargs,
    )


def _damage_helper(spell_id, name, effects, visual, icon, *, school, range_yards, duration_ms=None,
                   suppress_procs=False, notes=''):
    """A command helper that deals damage (a second bite, a channel tick, a splash): the commanded-spell carrier
    (Phoenix's Plume and Master's Command reach it) that no kit slots, so Hunter::IsBeastCleaveExcluded keeps it out of
    Beast Cleave (F0's helper rule). DmgClass RANGED (the Cunning commands'). `suppress_procs` for a follow-up strike
    (F1's multi-hit rule: the command already procced the pet talents)."""
    raw = {**_cmd_raw(visual, dmg_class=3, prevention=1), 'SpellIconID': icon}
    if suppress_procs:
        raw['AttributesEx3'] = _SUPPRESS_CASTER_PROCS
    kwargs = {'duration_ms': duration_ms} if duration_ms is not None else {}
    return spell(
        id=spell_id, name=name, school=school, attributes=0x50010, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=range_yards, effects=effects,
        pet_owner_scaling=_PET_SCALING, notes=notes + kits.RULING_23_NOTE, raw_overrides=raw, **kwargs,
    )


def _root_rider(spell_id, name, icon, *, notes):
    """A command's root rider (the F2 Pincer Crush 201666 shape): family 0, no carrier, cast on the command's target by
    its TRIGGER_SPELL (so only on a hit), SUPPRESS_CASTER_PROCS, its own spell so spell_hun_pet_control_boss_filter
    refuses the root on a boss while the command's damage lands (F1 review NIT 7). 2 s, Mechanic 7. 40 yd (a 30 yd
    command's trigger is range-checked strictly)."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=_HELPER_RANGE_YD, duration_ms=2000,
        effects=[_enemy_aura(AuraType.MOD_ROOT, 0, mechanic=_MECHANIC_ROOT)], spell_icon_id=icon, notes=notes,
        raw_overrides={'EquippedItemClass': -1, 'SpellLevel': 1, 'BaseLevel': 1, 'CastingTimeIndex': 1,
                       'AttributesEx3': _SUPPRESS_CASTER_PROCS, 'AuraDescription_Lang_enUS': 'Rooted.'},
    )


def _dot_rate(total, duration_ms):
    """A periodic potency is a rate per 1.5 s, so the total over `duration_ms` is rate x duration / 1500."""
    return round(total * 1500.0 / duration_ms, 4)


def _utility(spell_id, name, level, effects, icon, visual, description, *, school=School.NORMAL, cooldown_ms,
             duration_ms=None, range_yards=0.0, enemy_target=False, defense=0, prevention=2, pet_owner_scaling=None,
             notes='', **raw):
    """A slot 2 / slot 3 pet utility: pet-cast, Focus 0, family 9 with d1 b28 + b29 (no Cunning utility is a ruling 10
    exception)."""
    kwargs = {'duration_ms': duration_ms} if duration_ms is not None else {}
    if pet_owner_scaling is not None:
        kwargs['pet_owner_scaling'] = pet_owner_scaling
    return spell(
        id=spell_id, name=name, school=school, attributes=kits.UTILITY_ATTRIBUTES, cast_time_ms=0,
        cooldown_ms=cooldown_ms, category_cooldown_ms=0, power_type=kits.UTILITY_POWER_TYPE, mana_cost=0,
        mana_cost_pct=0, range_yards=range_yards, effects=effects, spell_icon_id=icon, notes=notes,
        raw_overrides=kits.utility_raw(level, enemy_target=enemy_target, DefenseType=defense,
                                       PreventionType=prevention, SpellVisualID_1=visual,
                                       Description_Lang_enUS=description, **raw),
        **kwargs,
    )


def _raid_aura(aura, base_points, misc_value=0, points_per_level=0.0):
    """One effect of a raid buff: TargetA 56 (CASTER_AREA_RAID, ruling 7), 100 yd."""
    return Effect(type=EffectType.APPLY_AURA, base_points=base_points, points_per_level=points_per_level,
                  implicit_target_a=_TARGET_UNIT_CASTER_AREA_RAID, apply_aura=aura, misc_value=misc_value,
                  radius_yards=_GROUP_BUFF_RADIUS_YD)


def _enemy_aura(aura, base_points, misc_value=0, mechanic=0):
    """One effect on the enemy target (the Tear Armor / Sticky Webbing shape)."""
    return Effect(type=EffectType.APPLY_AURA, base_points=base_points, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
                  apply_aura=aura, misc_value=misc_value, mechanic=mechanic)


def _self_aura(aura, base_points, misc_value=0):
    return Effect(type=EffectType.APPLY_AURA, base_points=base_points, implicit_target_a=1, apply_aura=aura,
                  misc_value=misc_value)


def _around_pet_aura(aura, mechanic, radius):
    """A control aura on every enemy around the pet (TargetA 22 / B 15, the Earthshaking Stomp 201992 shape)."""
    return Effect(type=EffectType.APPLY_AURA, implicit_target_a=_TARGET_SRC_CASTER,
                  implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY, apply_aura=aura, mechanic=mechanic,
                  radius_yards=radius)


def _cone(potency):
    """The F1 cone shape: cone damage (TargetA 104, 8 yd) and a DUMMY at the target that keeps the command's target as
    the spell's explicit target, the primary of spell_hun_command_aoe_falloff (which also puts a large primary back
    into the cone, F1 review MAJOR 1)."""
    return [Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=potency, potency_kind='direct',
                   implicit_target_a=_TARGET_UNIT_CONE_ENEMY, radius_yards=_AREA_RADIUS_YD),
            Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)]


def _at_target(potency):
    """Damage to the target and every enemy within 8 yd of it (TargetA 53 / B 16, the Bubble Burst 201629 shape): the
    target is the area's center and stays the explicit target, no anchor needed."""
    return [Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=potency, potency_kind='direct',
                   implicit_target_a=_TARGET_DEST_TARGET_ENEMY, implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY,
                   radius_yards=_AREA_RADIUS_YD)]


def _rider(helper):
    """eff: TRIGGER_SPELL on the command's target casting `helper` (only on a hit)."""
    return Effect(type=EffectType.TRIGGER_SPELL, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, trigger_spell=helper.id)


# =====================================================================================================================
# Bat (family 24, skill line 653, basic Spit)
# =====================================================================================================================

sonic_bite_command_201640 = _command(
    201640, 'Sonic Bite',
    [_direct(kits.command_potency(900, 'I', cunning=True), chain_targets=2)],
    376, 87,
    'Bite the target with a sonic shriek, causing {pot1} Physical damage. The shriek bounces to one more nearby enemy, '
    'which takes ' + str(round(_BOUNCE_AMPLITUDE * 100)) + _SPLASH_TAIL,
    EffectChainAmplitude_1=_BOUNCE_AMPLITUDE,
    notes='hunter-pet-families F3: Bat I, 900 x0.84 = 756 Physical (rule 17: full potency, the bounce is the AoE). '
          'chain_targets 2 with EffectChainAmplitude 0.5: the second enemy takes 50% (the Leaping Tear 201725 shape, '
          'no falloff script). 30 yd, DmgClass RANGED. Visual 376 (Bite), icon 87 (Sonic Burst 8281).',
)

shriek_command_201641 = _command(
    201641, 'Shriek',
    _cone(kits.command_potency(1800, 'II', cunning=True)),
    9478, 458,
    'Shriek at the target and all enemies in a cone in front of your pet, causing {pot1} Physical damage.'
    + _FALLOFF_TEXT,
    ranged=False,
    notes='hunter-pet-families F3: Bat II, 1800 x0.65 = 1170 Physical (rule 17: full potency, no AoE shift), the F1 '
          'cone shape (104, 8 yd + DUMMY anchor), spell_hun_command_aoe_falloff (extra targets 50%, the AoE rule every '
          'other cone follows). Melee reach, not 30 yd: the cone starts at the pet. Visual 9478 (Screech 31273), icon '
          '458 (Sonic Boom 33666).',
)

screech_201771 = _utility(
    201771, 'Screech', SCREECH_LEVEL,
    [Effect(type=EffectType.APPLY_AURA, base_points=-36, points_per_level=-5.696969696969697,
            implicit_target_a=_TARGET_SRC_CASTER, implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY,
            apply_aura=AuraType.MOD_ATTACK_POWER, radius_yards=10.0)],
    91, 7302,
    'Your pet screeches, reducing the attack power of all enemies within $a1 yards by $s1 for $d. Does not stack '
    'with Demoralizing Shout, Demoralizing Roar, Demoralizing Screech, Menacing Roar, Vindication or Curse of '
    'Weakness.',
    cooldown_ms=10000, duration_ms=30000, defense=1, prevention=1,
    MaxLevel=80, AttributesEx=kits.ATTR1_INITIATE_COMBAT, AttributesEx6=8388608, RangeIndex=1,
    AuraDescription_Lang_enUS='Attack power reduced.',
    notes='hunter-pet-families F3: Bat slot 2, autocast. Demoralizing Screech 201754\'s shape (Demoralizing Shout '
          '1160: bp -36, -5.697/level from 14 to 80, around the pet 10 yd), 30 s, 10 s cooldown. Group 1062 AP Debuffs '
          '(rule '
          '4, aura 99). Visual 7302 (Demoralizing Screech 24423), icon 91 (Screech 31273).',
)

sonic_blast_202004 = _utility(
    202004, 'Sonic Blast', SONIC_BLAST_LEVEL,
    [Effect(type=EffectType.INTERRUPT_CAST, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    1577, 7642,
    'Your pet blasts the target with sound, interrupting spellcasting and preventing any spell in that school from '
    'being cast for $d.',
    school=School.NATURE, cooldown_ms=30000, duration_ms=4000, range_yards=_CUNNING_RANGE_YD, enemy_target=True,
    defense=1, prevention=1, FacingCasterFlags=1,
    notes='hunter-pet-families F3: Bat slot 3, manual (ruling 10 of the brainstorm: three interrupt pets). '
          'INTERRUPT_CAST on the target, 4 s lockout and 30 s cooldown (the Gorilla\'s Pummel 202000), 30 yd (FE 8e), '
          'DmgClass MAGIC as Spell Lock 19244. Not boss-filtered (ruling 3: interrupts stay stock). Visual 7642 '
          '(Sonic Blast 29300), icon 1577 (Sonic Blast 50519).',
)


# =====================================================================================================================
# Bird of Prey (family 26, skill line 655, basic Spit)
# =====================================================================================================================

_TALON_RAKE_MS = 6000
talon_rake_command_201642 = _command(
    201642, 'Talon Rake',
    [_direct(kits.command_potency(600, 'I', cunning=True, single_target=True)),
     _dot(_dot_rate(kits.command_potency(300, 'I', cunning=True, single_target=True), _TALON_RAKE_MS), 2000,
          mechanic=_MECHANIC_BLEED, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    750, 2328,
    'Rake the target with your talons for {pot1} Physical damage and an additional {pot2.total} Physical damage over '
    '$d.',
    duration_ms=_TALON_RAKE_MS,
    notes='hunter-pet-families F3: Bird of Prey I. eff0 600 x0.84 = 504 direct, eff1 bleed 300 x0.84 = 252 over 6 s '
          '(rate 63, 2 s ticks), Mechanic 15. 30 yd. Visual 750 (Rake), icon 2328 (Swoop 52825).'
          + kits.ruling_24_note('Cunning', kits.command_potency(600, 'I', cunning=True),
                                kits.command_potency(300, 'I', cunning=True)),
)

swoop_command_201643 = _command(
    201643, 'Swoop',
    [_direct(kits.command_potency(1800, 'II', cunning=True, single_target=True))],
    1104, 277,
    'Swoop down on the target, causing {pot1} Physical damage.',
    notes='hunter-pet-families F3: Bird of Prey II, 1800 x0.65 = 1170 Physical, 30 yd (PLAN §3.3: a plain hit, no '
          'charge). Visual 1104 (Swoop 52825), icon 277 (Swoop 5708).'
          + kits.ruling_24_note('Cunning', kits.command_potency(1800, 'II', cunning=True)),
)

keen_sight_201772 = _utility(
    201772, 'Keen Sight', KEEN_SIGHT_LEVEL,
    [_raid_aura(AuraType.MOD_SPELL_CRIT_CHANCE, 4)],
    46, 13457,
    'Your pet spots weak points for its allies, increasing the spell critical strike chance of all party and raid '
    'members by $s1% for $d. Does not stack with Moonkin Aura or Elemental Oath.',
    cooldown_ms=40000, duration_ms=120000, RangeIndex=1,
    AuraDescription_Lang_enUS='Spell critical strike chance increased by $s1%.',
    notes='hunter-pet-families F3: Bird of Prey slot 2, autocast. Aura 57 +5% spell crit (Moonkin Aura 24907 live), '
          'raid 100 yd, 2 min, 40 s cooldown (Roar of Courage shape). Group 1036 Spell Crit Buffs (rule 4, highest per '
          'aura). Visual 13457 / icon 46 from Moonkin Aura 24907.',
)

snatch_202005 = _utility(
    202005, 'Snatch', SNATCH_LEVEL,
    [_enemy_aura(AuraType.MOD_DISARM, 0, mechanic=_MECHANIC_DISARM),
     _enemy_aura(AuraType.MOD_DAMAGE_PERCENT_DONE, -51, misc_value=_SCHOOL_MASK_PHYSICAL, mechanic=_MECHANIC_DISARM)],
    168, 398,
    "Your pet snatches the target's weapon, disarming it and reducing the Physical damage it deals by ${$m2*-1}% for "
    '$d. While disarmed, the target cannot use its weapon abilities. Does not work on bosses.',
    cooldown_ms=60000, duration_ms=6000, range_yards=_CUNNING_RANGE_YD, enemy_target=True, defense=1, prevention=1,
    FacingCasterFlags=1, Mechanic=_MECHANIC_DISARM,
    AuraDescription_Lang_enUS='Disarmed: cannot use weapon abilities. Physical damage dealt reduced.',
    notes='hunter-pet-families F3: Bird of Prey slot 3, manual (ruling 2, the Disarming Pincer 201999 shape): aura 67 '
          'MOD_DISARM for the visual (it does nothing to a creature\'s white swings, FE 8d, but Spell::CheckItems '
          'fails its MELEE / RANGED DmgClass spells while it lasts: F2 review MINOR 2, kept and stated in the '
          'tooltip) + aura 79 -50% Physical damage done, 6 s, both Mechanic 3 (disarm-immune creatures resist), 30 yd, '
          '1 min. '
          'spell_hun_pet_control_boss_filter refuses a boss (ruling 3). Visual 398 / icon 168 from Snatch 50541.',
)


# =====================================================================================================================
# Wind Serpent (family 27, skill line 656, basic Spit)
# =====================================================================================================================

lightning_breath_command_201644 = _command(
    201644, 'Lightning Breath',
    [_direct(kits.command_potency(1250, 'I', cunning=True, single_target=True))],
    173, 62,
    'Breathe lightning at the target, causing {pot1} Nature damage.',
    school=School.NATURE,
    notes='hunter-pet-families F3: Wind Serpent I, 1250 x0.84 = 1050 Nature (1250 = 900 + the AoE shift off Chain '
          'Lightning, rule 15), single target, 30 yd. Visual 173 / icon 62 from Lightning Breath 24844.'
          + kits.ruling_24_note('Cunning', kits.command_potency(1250, 'I', cunning=True)),
)

chain_lightning_command_201645 = _command(
    201645, 'Chain Lightning',
    [_direct(kits.command_potency(1450, 'II', cunning=True), chain_targets=3)],
    36, 165,
    'Strike the target with lightning that jumps to 2 more nearby enemies, causing {pot1} Nature damage. Each jump '
    'deals ' + str(_SPLASH_PCT) + _SPLASH_TAIL,
    school=School.NATURE, EffectChainAmplitude_1=1.0,
    notes='hunter-pet-families F3: Wind Serpent II, 1450 x0.65 = 942.5 Nature, chain_targets 3 with '
          'EffectChainAmplitude 1.0: spell_hun_command_aoe_falloff gives each jump a flat 50% (ruling 6, not the '
          'engine\'s compounding 100/50/25). 30 yd. Visual 36 / icon 165 from Chain Lightning 421.',
)

storm_breath_201773 = _utility(
    201773, 'Storm Breath', STORM_BREATH_LEVEL,
    [_enemy_aura(AuraType.MOD_DAMAGE_PERCENT_TAKEN, 9, misc_value=_SCHOOL_MASK_MAGIC)],
    2991, 4200,
    'Your pet breathes a charged storm on the target, increasing the magic damage it takes by $s1% for $d. Does not '
    'stack with Earth and Moon, Curse of the Elements, Ebon Plague or Scorching Breath.',
    school=School.NATURE, cooldown_ms=10000, duration_ms=30000, range_yards=_CUNNING_RANGE_YD, enemy_target=True,
    defense=1, prevention=1, FacingCasterFlags=1,
    AuraDescription_Lang_enUS='Magic damage taken increased.',
    notes='hunter-pet-families F3: Wind Serpent slot 2, autocast. Aura 87 +10% magic schools (misc 126, Earth and Moon '
          '60431 live; ruling 5: 10%), single enemy, 30 yd, 30 s, 10 s cooldown (Sticky Webbing shape). Group 1101 '
          'Spell Damage Taken Debuffs (rule 3, same aura). Visual 4200 (Lightning Breath 15797), icon 2991 (Earth and '
          'Moon).',
)

gale_barrier_202006 = _utility(
    202006, 'Gale Barrier', GALE_BARRIER_LEVEL,
    [_raid_aura(AuraType.MOD_DAMAGE_PERCENT_TAKEN, -11, misc_value=_SCHOOL_MASK_MAGIC)],
    1985, 11648,
    'Your pet whips up a barrier of wind around your allies, reducing the magic damage taken by all party and raid '
    'members by ${$m1*-1}% for $d. Does not stack with Earthen Bulwark.',
    school=School.NATURE, cooldown_ms=60000, duration_ms=8000, RangeIndex=1, AttributesEx=_ATTR1_NO_AUTOCAST_AI,
    AuraDescription_Lang_enUS='Magic damage taken reduced.',
    notes='hunter-pet-families F3: Wind Serpent slot 3, manual. Aura 87 -10% magic schools (misc 126), raid 100 yd '
          '(TargetA 56, ruling 7), 8 s, 1 min. One effect, the same aura type as Earthen Bulwark 201769: group 1232 '
          '(rule 4, highest wins) compares within one aura type, then the effect count, then the duration (F2 review). '
          'd1 b28 + b29 (not a ruling 10 spell: Mobility shortens it). AttributesEx NO_AUTOCAST_AI: a raid cooldown, '
          'never autocast (F1 review MINOR 2). Visual 11648 / icon 1985 from Anti-Magic Zone 52894.',
)


# =====================================================================================================================
# Dragonhawk (family 30, skill line 763, basic Spit)
# =====================================================================================================================

_FIRE_BREATH_MS = 6000
fire_breath_command_201646 = _command(
    201646, 'Fire Breath',
    [_direct(kits.command_potency(600, 'I', cunning=True, single_target=True)),
     _dot(_dot_rate(kits.command_potency(650, 'I', cunning=True, single_target=True), _FIRE_BREATH_MS), 2000,
          implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    8256, 2128,
    'Breathe fire at the target for {pot1} Fire damage and an additional {pot2.total} Fire damage over $d.',
    school=School.FIRE, duration_ms=_FIRE_BREATH_MS,
    notes='hunter-pet-families F3: Dragonhawk I. eff0 600 x0.84 = 504 Fire, eff1 650 x0.84 = 546 over 6 s (rate 136.5, '
          '2 s ticks); 1250 = 900 + the AoE shift off Flame Nova. 30 yd. Visual 8256 / icon 2128 from Fire Breath '
          '34889.'
          + kits.ruling_24_note('Cunning', kits.command_potency(600, 'I', cunning=True),
                                kits.command_potency(650, 'I', cunning=True)),
)

flame_nova_command_201647 = _command(
    201647, 'Flame Nova',
    _at_target(kits.command_potency(1450, 'II', cunning=True)),
    10383, 33,
    'Engulf the target in flame, causing {pot1} Fire damage to it and all enemies within $a1 yards of it.'
    + _FALLOFF_TEXT,
    school=School.FIRE,
    notes='hunter-pet-families F3: Dragonhawk II, 1450 x0.65 = 942.5 Fire to the target and the enemies within 8 yd of '
          'it (TargetA 53 / B 16, the Bubble Burst shape), spell_hun_command_aoe_falloff. 30 yd. Visual 10383 '
          '(Flamestrike 2120), icon 33 (Fire Nova).',
)

scorching_breath_201774 = _utility(
    201774, 'Scorching Breath', SCORCHING_BREATH_LEVEL,
    [_enemy_aura(AuraType.MOD_DAMAGE_PERCENT_TAKEN, 9, misc_value=_SCHOOL_MASK_MAGIC)],
    816, 945,
    'Your pet scorches the target, increasing the magic damage it takes by $s1% for $d. Does not stack with Earth and '
    'Moon, Curse of the Elements, Ebon Plague or Storm Breath.',
    school=School.FIRE, cooldown_ms=10000, duration_ms=30000, range_yards=_CUNNING_RANGE_YD, enemy_target=True,
    defense=1, prevention=1, FacingCasterFlags=1,
    AuraDescription_Lang_enUS='Magic damage taken increased.',
    notes='hunter-pet-families F3: Dragonhawk slot 2, autocast. Storm Breath 201773\'s shape (aura 87 +10% magic). '
          'Group 1101 (rule 3). Visual 945 / icon 816 from Scorch 2948.',
)

blinding_flash_202007 = _utility(
    202007, 'Blinding Flash', BLINDING_FLASH_LEVEL,
    [_around_pet_aura(AuraType.MOD_STUN, _MECHANIC_STUN, 8.0)],
    1548, 7860,
    'Your pet unleashes a blinding flash, stunning all enemies within $a1 yards for $d. Does not work on bosses.',
    school=School.FIRE, cooldown_ms=60000, duration_ms=2000, defense=1, prevention=1, RangeIndex=1,
    AttributesEx=kits.ATTR1_INITIATE_COMBAT,
    AuraDescription_Lang_enUS='Stunned.',
    notes='hunter-pet-families F3: Dragonhawk slot 3, manual (ruling 5: a 2 s AoE stun, not a disorient that breaks on '
          'the first cleave). Aura 12 MOD_STUN 2 s around the pet (TargetA 22 / B 15) 8 yd, Mechanic 12, 1 min (the '
          'Earthshaking Stomp 201992 shape). spell_hun_pet_control_boss_filter drops world and dungeon bosses from the '
          'area (ruling 3). Visual 7860 / icon 1548 from Dragon\'s Breath 31661.',
)


# =====================================================================================================================
# Ravager (family 31, skill line 767, basic Spit)
# =====================================================================================================================

_RAVAGE_MS = 6000
ravage_command_201648 = _command(
    201648, 'Ravage',
    [_direct(kits.command_potency(600, 'I', cunning=True, single_target=True)),
     _dot(_dot_rate(kits.command_potency(300, 'I', cunning=True, single_target=True), _RAVAGE_MS), 2000,
          mechanic=_MECHANIC_BLEED, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    8102, 2253,
    'Ravage the target for {pot1} Physical damage and an additional {pot2.total} Physical damage over $d.',
    duration_ms=_RAVAGE_MS,
    notes='hunter-pet-families F3: Ravager I. eff0 600 x0.84 = 504 direct, eff1 bleed 300 x0.84 = 252 over 6 s (rate '
          '63, 2 s ticks), Mechanic 15. 30 yd. Visual 8102 / icon 2253 from Ravage 50518.'
          + kits.ruling_24_note('Cunning', kits.command_potency(600, 'I', cunning=True),
                                kits.command_potency(300, 'I', cunning=True)),
)

gut_rip_command_201649 = _command(
    201649, 'Gut Rip',
    [_direct(kits.command_potency(1800, 'II', cunning=True, single_target=True))],
    8009, 2046,
    'Rip into the target, causing {pot1} Physical damage.',
    notes='hunter-pet-families F3: Ravager II, 1800 x0.65 = 1170 Physical, 30 yd. Visual 8009 / icon 2046 from Gut Rip '
          '32022.'
          + kits.ruling_24_note('Cunning', kits.command_potency(1800, 'II', cunning=True)),
)

rending_claws_201775 = _utility(
    201775, 'Rending Claws', RENDING_CLAWS_LEVEL,
    [_enemy_aura(_AURA_MOD_RESISTANCE_PCT, -21, misc_value=_SCHOOL_MASK_PHYSICAL)],
    563, 3441,
    "Your pet rends the target's armor, reducing it by ${$m1*-1}% for $d. Does not stack with Sunder Armor, Expose "
    'Armor or Tear Armor.',
    cooldown_ms=10000, duration_ms=30000, range_yards=_CUNNING_RANGE_YD, enemy_target=True, defense=1, prevention=1,
    FacingCasterFlags=1,
    AuraDescription_Lang_enUS='Armor decreased.',
    notes='hunter-pet-families F3: Ravager slot 2, autocast. Tear Armor 201716\'s effect (aura 101 -20% armor, Expose '
          'Armor 8647 value), single enemy, 30 yd, 30 s, 10 s cooldown. Group 1015 Major Armor Debuffs (rule 3). '
          'Visual 3441 / icon 563 from Expose Armor 8647.',
)

chitinous_shell_202008 = _utility(
    202008, 'Chitinous Shell', CHITINOUS_SHELL_LEVEL,
    [_self_aura(AuraType.MOD_DAMAGE_PERCENT_TAKEN, -31, misc_value=_SCHOOL_MASK_ALL)],
    2015, 6633,
    'Your pet hardens its chitin, reducing all damage it takes by ${$m1*-1}% for $d.',
    cooldown_ms=60000, duration_ms=10000, RangeIndex=1,
    AuraDescription_Lang_enUS='Damage taken reduced.',
    notes='hunter-pet-families F3: Ravager slot 3, manual. Aura 87 -30% all schools on the pet, 10 s, 1 min (Molten '
          'Hide 201993\'s values, Shell Shield 26064 shape, FE 9c). Visual 6633 / icon 2015 from Harden Skin 22693.',
)


# =====================================================================================================================
# Serpent (family 35, skill line 768, basic Spit)
# =====================================================================================================================

_POISON_SPIT_MS = 9000
poison_spit_command_201650 = _command(
    201650, 'Poison Spit',
    [_dot(_dot_rate(kits.command_potency(900, 'I', cunning=True, single_target=True), _POISON_SPIT_MS), 3000,
          implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    7910, 68,
    'Spit poison at the target, causing {pot1.total} Nature damage over $d.',
    school=School.NATURE, duration_ms=_POISON_SPIT_MS,
    AuraDescription_Lang_enUS='Nature damage inflicted every $t1 sec.',
    notes='hunter-pet-families F3: Serpent I, 900 x0.84 = 756 Nature over 9 s (rate 126, 3 s ticks), all periodic. '
          '30 yd. Visual 7910 / icon 68 from Poison Spit 35387.'
          + kits.ruling_24_note('Cunning', kits.command_potency(900, 'I', cunning=True)),
)

constrict_root_201672 = _root_rider(
    201672, 'Constrict', 2678,
    notes='hunter-pet-families F3: Constrict\'s root (free, ruling 3). MOD_ROOT 2 s (Pincer Crush 201666\'s length), '
          'Mechanic 7, cast by the pet through 201651\'s TRIGGER_SPELL; boss-filtered on its own. Icon 2678 (Crush '
          '50234).',
)

_CONSTRICT_MS = 6000
constrict_command_201651 = _command(
    201651, 'Constrict',
    [_dot(_dot_rate(kits.command_potency(1800, 'II', cunning=True, single_target=True), _CONSTRICT_MS), 2000,
          implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
     _rider(constrict_root_201672)],
    11023, 2678,
    'Coil around the target, causing {pot1.total} Physical damage over $d and rooting it for $201672d. The root does '
    'not work on bosses.',
    duration_ms=_CONSTRICT_MS,
    AuraDescription_Lang_enUS='Physical damage inflicted every $t1 sec.',
    notes='hunter-pet-families F3: Serpent II, 1800 x0.65 = 1170 Physical over 6 s (rate 292.5, 2 s ticks; §3.3 marks '
          'no school: F1 decision 2), eff1 TRIGGER_SPELL the 2 s root 201672 (boss-filtered on its own). 30 yd. '
          'Visual 11023 / icon 2678 from Crush 50234.'
          + kits.ruling_24_note('Cunning', kits.command_potency(1800, 'II', cunning=True)),
)

paralyzing_venom_201776 = _utility(
    201776, 'Paralyzing Venom', PARALYZING_VENOM_LEVEL,
    [_enemy_aura(_AURA_HASTE_SPELLS, -26)],
    71, 809,
    'Your pet spits a paralyzing venom at the target, increasing the casting time of its spells by ${$m1*-1}% for $d. '
    'Does not stack with Curse of Tongues, Mind-numbing Poison, Sticky Webbing or Time Warp.',
    school=School.NATURE, cooldown_ms=10000, duration_ms=30000, range_yards=_CUNNING_RANGE_YD, enemy_target=True,
    defense=1, prevention=1, FacingCasterFlags=1,
    AuraDescription_Lang_enUS='Casting time increased.',
    notes='hunter-pet-families F3: Serpent slot 2, autocast. Sticky Webbing 201753\'s effect (aura 216 HASTE_SPELLS '
          '-25%, Curse of Tongues 1714 live), single enemy, 30 yd, 30 s, 10 s cooldown. Group 1096 Cast Time Debuffs '
          '(rule 4). Visual 809 (Toxic Spit 7951), icon 71 (Paralyze 23414).',
)

shed_skin_heal_202032 = spell(
    id=202032,
    name='Shed Skin',
    school=School.NATURE,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    effects=[
        Effect(type=EffectType.DISPEL, base_points=9, implicit_target_a=1, misc_value=_DISPEL_POISON),
        Effect(type=EffectType.HEAL_PCT, base_points=19, implicit_target_a=1),
    ],
    spell_icon_id=2769,
    notes='hunter-pet-families F3: Shed Skin\'s second half (utility helper), cast on the pet by 202009\'s '
          'TRIGGER_SPELL: eff0 DISPEL Poison (up to 10 poisons), eff1 HEAL_PCT 20% (a spell has three effects; the '
          'root and snare cleanse fill 202009). Family 0, no carrier, SUPPRESS_CASTER_PROCS. Icon 2769 (Bullheaded).',
    raw_overrides={'EquippedItemClass': -1, 'SpellLevel': 1, 'BaseLevel': 1, 'CastingTimeIndex': 1, 'RangeIndex': 1,
                   'AttributesEx3': _SUPPRESS_CASTER_PROCS},
)

shed_skin_202009 = _utility(
    202009, 'Shed Skin', SHED_SKIN_LEVEL,
    [Effect(type=_EFFECT_DISPEL_MECHANIC, implicit_target_a=1, misc_value=_MECHANIC_ROOT),
     Effect(type=_EFFECT_DISPEL_MECHANIC, implicit_target_a=1, misc_value=_MECHANIC_SNARE),
     Effect(type=EffectType.TRIGGER_SPELL, implicit_target_a=1, trigger_spell=shed_skin_heal_202032.id)],
    2769, 86,
    'Your pet sheds its skin, removing all roots, movement slowing effects and poisons from itself and healing itself '
    'for $202032s2% of its maximum health.',
    school=School.NATURE, cooldown_ms=60000, RangeIndex=1,
    notes='hunter-pet-families F3: Serpent slot 3, manual. eff0 / eff1 DISPEL_MECHANIC (108) root (7) and snare (11) '
          'on the pet, eff2 TRIGGER_SPELL 202032 (Poison dispel + HEAL_PCT 20%), 1 min. No immunity window (an instant '
          'cleanse, not Bullheaded\'s mechanic immunity). Visual 86 / icon 2769 from Bullheaded 53490 (DI 4.3).',
)


# =====================================================================================================================
# Sporebat (family 33, skill line 765, basic Spit)
# =====================================================================================================================

spore_burst_splash_201675 = _damage_helper(
    201675, 'Spore Burst',
    [Effect(type=EffectType.SCHOOL_DAMAGE,
            ap_potency=round(kits.command_potency(900, 'I', cunning=True) * _SPLASH_PCT / 100, 4),
            potency_kind='direct', implicit_target_a=_TARGET_DEST_TARGET_ENEMY,
            implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY, radius_yards=_AREA_RADIUS_YD)],
    195, 170, school=School.NATURE, range_yards=_SPLASH_RANGE_YD,
    notes='hunter-pet-families F3: Spore Burst\'s splash (command helper), 900 x0.84 x 50% = 378 Nature to the enemies '
          'within 8 yd of the primary (TargetA 53 / B 16); spell_hun_command_splash drops the primary (the Venomous '
          'Cloud splash 201736 shape: rule 17 keeps the primary at full potency, no falloff script). Triggered by '
          '201652 with the primary as its explicit target. Visual 195 / icon 170 from Spore Burst 5100.',
)

spore_burst_command_201652 = _command(
    201652, 'Spore Burst',
    [_direct(kits.command_potency(900, 'I', cunning=True)), _rider(spore_burst_splash_201675)],
    195, 170,
    'Burst spores on the target, causing {pot1} Nature damage, and ' + pot_text(spore_burst_splash_201675)
    + ' Nature damage to all other enemies within $201675a1 yards of it.',
    school=School.NATURE,
    notes='hunter-pet-families F3: Sporebat I, 900 x0.84 = 756 Nature to the target (rule 17: full potency), eff1 '
          'TRIGGER_SPELL the 50% splash 201675 at the enemies around it. 30 yd. Visual 195 / icon 170 from Spore '
          'Burst 5100.',
)

_FUNGAL_BLOOM_MS = 12000
fungal_bloom_splash_201674 = _damage_helper(
    201674, 'Fungal Bloom',
    [_dot(round(_dot_rate(kits.command_potency(1800, 'II', cunning=True), _FUNGAL_BLOOM_MS) * _SPLASH_PCT / 100, 4),
          3000,
          implicit_target_a=_TARGET_DEST_TARGET_ENEMY, implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY,
          radius_yards=_AREA_RADIUS_YD)],
    10409, 2681, school=School.NATURE, range_yards=_SPLASH_RANGE_YD, duration_ms=_FUNGAL_BLOOM_MS,
    notes='hunter-pet-families F3: Fungal Bloom\'s splash (command helper), half the primary\'s rate (73.125, 3 s '
          'ticks, 12 s: 585 total) on the enemies within 8 yd of the primary (TargetA 53 / B 16); '
          'spell_hun_command_splash drops the primary. The Venomous Cloud splash 201736 shape (rule 17: its AoE is a '
          'DoT). Visual 10409 / icon 2681 from Spore Cloud 50274.',
)

fungal_bloom_command_201653 = _command(
    201653, 'Fungal Bloom',
    [_dot(_dot_rate(kits.command_potency(1800, 'II', cunning=True), _FUNGAL_BLOOM_MS), 3000,
          implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
     _rider(fungal_bloom_splash_201674)],
    10409, 2681,
    'Seed a fungal bloom on the target, causing {pot1.total} Nature damage over $d to it and '
    + pot_text(fungal_bloom_splash_201674, variant='total') + ' Nature damage over $d to all other enemies within '
    '$201674a1 yards of it.',
    school=School.NATURE, duration_ms=_FUNGAL_BLOOM_MS,
    AuraDescription_Lang_enUS='Nature damage inflicted every $t1 sec.',
    notes='hunter-pet-families F3: Sporebat II, 1800 x0.65 = 1170 Nature over 12 s on the target (rate 146.25, 3 s '
          'ticks; rule 17: full potency), eff1 TRIGGER_SPELL the 50% splash DoT 201674 (Venomous Cloud 201729 shape). '
          '30 yd. Visual 10409 / icon 2681 from Spore Cloud 50274.',
)

energizing_spores_201777 = _utility(
    201777, 'Energizing Spores', ENERGIZING_SPORES_LEVEL,
    [_raid_aura(AuraType.MOD_CASTING_SPEED_NOT_STACK, 4)],
    41, 6099,
    'Your pet releases energizing spores, increasing the spell casting speed of all party and raid members by $s1% for '
    '$d. Does not stack with Fire Attunement, Wrath of Air Totem or Nether Currents.',
    school=School.NATURE, cooldown_ms=40000, duration_ms=120000, RangeIndex=1,
    AuraDescription_Lang_enUS='Spell casting speed increased by $s1%.',
    notes='hunter-pet-families F3: Sporebat slot 2, autocast. Aura 65 MOD_CASTING_SPEED_NOT_STACK +5% (Fire Attunement '
          '202209, the shaman\'s spell haste on this server; Wrath of Air 2895), raid 100 yd, 2 min, 40 s cooldown. '
          'Group 1233 Spell Haste Buffs (rule 3, with Nether Currents, Fire Attunement and Wrath of Air: only the '
          'highest aura 65 applies; F3 review MAJOR 1). Visual 6099 / icon 41 from Spore Cloud 21547.',
)

_RESTORATIVE_SPORES_MS = 10000
restorative_spores_202010 = _utility(
    202010, 'Restorative Spores', RESTORATIVE_SPORES_LEVEL,
    [Effect(type=EffectType.APPLY_AURA, ap_potency=_dot_rate(150, _RESTORATIVE_SPORES_MS),
            potency_kind='heal_periodic', implicit_target_a=_TARGET_UNIT_CASTER_AREA_RAID,
            apply_aura=AuraType.PERIODIC_HEAL, amplitude=2000, radius_yards=40.0)],
    1737, 7847,
    'Your pet releases restorative spores over all party and raid members within $a1 yards, healing them for '
    '{pot1.total} over $d.',
    school=School.NATURE, cooldown_ms=60000, duration_ms=_RESTORATIVE_SPORES_MS, defense=1, prevention=1,
    RangeIndex=1, pet_owner_scaling=_PET_SCALING,
    AuraDescription_Lang_enUS='Healing over time.',
    notes='hunter-pet-families F3: Sporebat slot 3, manual. PERIODIC_HEAL on the raid within 40 yd of the pet (TargetA '
          '56, ruling 7), Spirit Mend 201994\'s numbers: 150 potency each over 10 s (rate 22.5, 2 s ticks), from the '
          'pet\'s AP (pet_owner_scaling). DefenseType 1 (custom-spells.md). 1 min. Visual 7847 / icon 1737 from Spore '
          'Explosion 32327.',
)


# =====================================================================================================================
# Nether Ray (family 34, skill line 764, basic Spit)
# =====================================================================================================================

nether_shock_command_201654 = _command(
    201654, 'Nether Shock',
    [_direct(kits.command_potency(900, 'I', cunning=True, single_target=True))],
    4209, 2027,
    'Shock the target with nether energy, causing {pot1} Arcane damage.',
    school=School.ARCANE,
    notes='hunter-pet-families F3: Nether Ray I, 900 x0.84 = 756 Arcane, 30 yd. Visual 4209 / icon 2027 from Nether '
          'Shock 35334.'
          + kits.ruling_24_note('Cunning', kits.command_potency(900, 'I', cunning=True)),
)

nether_lash_command_201655 = _command(
    201655, 'Nether Lash',
    [_direct(kits.command_potency(1800, 'II', cunning=True, single_target=True))],
    8037, 1485,
    'Lash the target with nether energy, causing {pot1} Arcane damage.',
    school=School.ARCANE,
    notes='hunter-pet-families F3: Nether Ray II, 1800 x0.65 = 1170 Arcane, 30 yd. Visual 8037 (Arcane Shock 33175), '
          'icon 1485 (Arcane Bolt 13748).'
          + kits.ruling_24_note('Cunning', kits.command_potency(1800, 'II', cunning=True)),
)

nether_currents_201778 = _utility(
    201778, 'Nether Currents', NETHER_CURRENTS_LEVEL,
    [_raid_aura(AuraType.MOD_CASTING_SPEED_NOT_STACK, 4)],
    340, 366,
    'Your pet stirs the nether currents, increasing the spell casting speed of all party and raid members by $s1% for '
    '$d. Does not stack with Fire Attunement, Wrath of Air Totem or Energizing Spores.',
    school=School.ARCANE, cooldown_ms=40000, duration_ms=120000, RangeIndex=1,
    AuraDescription_Lang_enUS='Spell casting speed increased by $s1%.',
    notes='hunter-pet-families F3: Nether Ray slot 2, autocast. Energizing Spores 201777\'s effect (aura 65 +5%), '
          'group 1233 (rule 3), raid 100 yd, 2 min, 40 s cooldown. Visual 366 / icon 340 from Wrath of Air Totem '
          '2895.',
)

nether_pulse_202011 = _utility(
    202011, 'Nether Pulse', NETHER_PULSE_LEVEL,
    [Effect(type=EffectType.INTERRUPT_CAST, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    212, 7346,
    'Your pet sends a pulse of nether energy at the target, interrupting spellcasting and preventing any spell in that '
    'school from being cast for $d.',
    school=School.ARCANE, cooldown_ms=30000, duration_ms=4000, range_yards=_CUNNING_RANGE_YD, enemy_target=True,
    defense=1, prevention=1, FacingCasterFlags=1,
    notes='hunter-pet-families F3: Nether Ray slot 3, manual. Sonic Blast 202004\'s shape (INTERRUPT_CAST, 4 s '
          'lockout, 30 s, 30 yd, DmgClass MAGIC). Not boss-filtered (ruling 3). Visual 7346 (Arcane Torrent 25046), '
          'icon 212 '
          '(Mana Burn).',
)


# =====================================================================================================================
# Chimaera (family 38, skill line 780, basic Spit)
# =====================================================================================================================

twin_bite_second_bite_201670 = _damage_helper(
    201670, 'Twin Bite',
    [_direct(kits.command_potency(650, 'I', cunning=True, single_target=True))],
    4200, 2108, school=School.NATURE, range_yards=_HELPER_RANGE_YD, suppress_procs=True,
    notes='hunter-pet-families F3: Chimaera Twin Bite\'s second bite (command helper, the twohit shape), 650 x0.84 = '
          '546 Nature (the second school, D6: one school per spell), cast once by spell_hun_command_multihit 300 ms '
          'after 201656. SUPPRESS_CASTER_PROCS (F1\'s strike rule), 40 yd (the command reaches 30). Visual 4200 '
          '(Froststorm Breath 54644), icon 2108 (the Core Hound\'s Twin Bite).'
          + kits.ruling_24_note('Cunning', kits.command_potency(650, 'I', cunning=True)),
)

twin_bite_command_201656 = _command(
    201656, 'Twin Bite',
    [_direct(kits.command_potency(600, 'I', cunning=True, single_target=True)),
     Effect(type=EffectType.DUMMY, base_points=0, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
            trigger_spell=twin_bite_second_bite_201670.id)],
    4200, 2108,
    'Bite the target twice: a frost bite causing {pot1} Frost damage, then a venom bite causing '
    + pot_text(twin_bite_second_bite_201670) + ' Nature damage.',
    school=School.FROST,
    notes='hunter-pet-families F3: Chimaera I, 600 Frost + 650 Nature (x0.84 = 504 + 546; 1250 = 900 + the AoE shift '
          'off Froststorm Breath). twohit = spell_hun_command_multihit with one follow-up (the F1 Core Hound Twin Bite '
          'shape): eff0 the Frost bite, eff1 DUMMY naming the Nature second bite 201670 (value 1). 30 yd. Visual 4200 '
          '(Froststorm Breath 54644), icon 2108 (Blade Twisting).'
          + kits.ruling_24_note('Cunning', kits.command_potency(600, 'I', cunning=True)),
)

_FROSTSTORM_BREATH_MS = 3000
_FROSTSTORM_BREATH_TICKS = 3
froststorm_breath_tick_201671 = _damage_helper(
    201671, 'Froststorm Breath',
    _cone(round(kits.command_potency(1850, 'II', cunning=True) / _FROSTSTORM_BREATH_TICKS, 4)),
    4200, 62, school=School.FROST, range_yards=_CUNNING_RANGE_YD,
    notes='hunter-pet-families F3: Froststorm Breath\'s tick (command helper). 1850 x0.65 = 1202.5 over 3 ticks = '
          '400.8333 each, the F1 cone shape (104, 8 yd + DUMMY anchor at the primary), spell_hun_command_aoe_falloff. '
          'Cast by spell_hun_command_pulse\'s aura every second at the stashed primary. Not SUPPRESS_CASTER_PROCS: the '
          'ticks are the command\'s only hits (Burrow Attack\'s pulse rule, F2). 30 yd so a tick never fails its '
          'strict triggered range check. Visual 4200 / icon 62 from Froststorm Breath 54644.',
)

froststorm_breath_command_201657 = _command(
    201657, 'Froststorm Breath',
    [Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL,
            amplitude=_FROSTSTORM_BREATH_MS // _FROSTSTORM_BREATH_TICKS,
            trigger_spell=froststorm_breath_tick_201671.id),
     Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    4200, 62,
    'Breathe a frost storm at the target for $d, causing ' + pot_text(froststorm_breath_tick_201671) + ' Frost damage '
    'every second to it and all enemies in a cone in front of your pet. Your pet channels for the whole breath.'
    + _FALLOFF_TEXT,
    school=School.FROST, ranged=False, duration_ms=_FROSTSTORM_BREATH_MS,
    AttributesEx=0x200 | _ATTR1_IS_CHANNELED, ChannelInterruptFlags=0,
    notes='hunter-pet-families F3: Chimaera II, 1850 x0.65 = 1202.5 Frost over a 3 s channeled cone (rule 18: the AoE '
          'shift and the +30% channel bonus are both in the 1850). eff0 PERIODIC_TRIGGER_SPELL on the pet, 1 s, 3 s, '
          'eff1 DUMMY anchor keeps the target explicit: spell_hun_command_pulse casts the cone tick 201671 at the '
          'primary each second (FE 10a: a cone channel ticks through a triggered spell; the tick reads the primary '
          'from the stash, CA 2.3). AttributesEx 0x4 (channeled): Hunter::GetCommandCastFlags keeps the pet facing; '
          'the pet\'s melee stops while it channels (Death Roll 201625\'s rule). No ChannelInterruptFlags. Melee '
          'reach, '
          'not 30 yd: the cone starts at the pet. Visual 4200 / icon 62 from Froststorm Breath 54644.',
)

arcane_resonance_201779 = _utility(
    201779, 'Arcane Resonance', ARCANE_RESONANCE_LEVEL,
    [_raid_aura(AuraType.MOD_DAMAGE_DONE, 29, misc_value=_SCHOOL_MASK_MAGIC, points_per_level=3.24546),
     _raid_aura(AuraType.MOD_HEALING_DONE, 29, misc_value=_SCHOOL_MASK_ALL, points_per_level=3.24546)],
    3220, 965,
    'Your pet resonates with arcane power, increasing the spell damage and healing of all party and raid members by '
    '$s1 for $d. Does not stack with Fire Attunement, Flametongue Totem, Totem of Wrath or Demonic Pact.',
    school=School.ARCANE, cooldown_ms=40000, duration_ms=120000, RangeIndex=1, BaseLevel=28, MaxLevel=60,
    AuraDescription_Lang_enUS='Spell damage and healing increased by $s1.',
    notes='hunter-pet-families F3: Chimaera slot 2 (rare), autocast. Fire Attunement Spell Power 202212\'s effects '
          '(aura 13 misc 126 + aura 135 misc 127, bp 29, 3.24546/level, SpellLevel 26, BaseLevel 28, MaxLevel 60: the '
          'same value at every level), raid 100 yd, 2 min, 40 s cooldown. Group 1048 Spell Power Buffs (rule 4). '
          'Visual '
          '965 (Arcane Explosion 1449), icon 3220 (Demonic Pact).',
)

frost_nova_202012 = _utility(
    202012, 'Frost Nova', FROST_NOVA_LEVEL,
    [_around_pet_aura(AuraType.MOD_ROOT, _MECHANIC_ROOT, 10.0)],
    193, 17,
    'Your pet blasts the ground with frost, rooting all enemies within $a1 yards in place for $d. Does not work on '
    'bosses.',
    school=School.FROST, cooldown_ms=60000, duration_ms=4000, defense=1, prevention=1, RangeIndex=1,
    AttributesEx=kits.ATTR1_INITIATE_COMBAT,
    AuraDescription_Lang_enUS='Frozen in place.',
    notes='hunter-pet-families F3: Chimaera slot 3, manual. Aura 26 MOD_ROOT 4 s (brainstorm) around the pet (TargetA '
          '22 / B 15) 10 yd (Frost Nova 122\'s radius), Mechanic 7, no damage (roots are free, ruling 3), 1 min (the '
          'Earthshaking Stomp cooldown). spell_hun_pet_control_boss_filter drops bosses from the area. A new id in no '
          'spell_group: it does not join group 1097 ("Frost Novas", exclusive with the mage\'s, DI 4.3). Visual 17 / '
          'icon 193 from Frost Nova 122.',
)


# =====================================================================================================================
# Silithid (family 41, skill line 783, basic Spit)
# =====================================================================================================================

venom_web_spray_root_201673 = _root_rider(
    201673, 'Venom Web Spray', 272,
    notes='hunter-pet-families F3: Venom Web Spray\'s root (free, ruling 3). MOD_ROOT 2 s (Pincer Crush 201666\'s '
          'length), Mechanic 7, cast by the pet through 201658\'s TRIGGER_SPELL; boss-filtered on its own. Icon 272 '
          '(Venom Web Spray 54706).',
)

_VENOM_WEB_SPRAY_MS = 6000
venom_web_spray_command_201658 = _command(
    201658, 'Venom Web Spray',
    [_dot(_dot_rate(kits.command_potency(1250, 'I', cunning=True, single_target=True), _VENOM_WEB_SPRAY_MS), 2000,
          implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
     _rider(venom_web_spray_root_201673)],
    12013, 272,
    'Spray venomous webbing on the target, causing {pot1.total} Nature damage over $d and rooting it for $201673d. The '
    'root does not work on bosses.',
    school=School.NATURE, duration_ms=_VENOM_WEB_SPRAY_MS,
    AuraDescription_Lang_enUS='Nature damage inflicted every $t1 sec.',
    notes='hunter-pet-families F3: Silithid I, 1250 x0.84 = 1050 Nature over 6 s (rate 262.5, 2 s ticks; 1250 = 900 + '
          'the AoE shift off Swarm Spit), eff1 TRIGGER_SPELL the 2 s root 201673 (boss-filtered on its own). 30 yd. '
          'Visual 12013 / icon 272 from Venom Web Spray 54706.'
          + kits.ruling_24_note('Cunning', kits.command_potency(1250, 'I', cunning=True)),
)

swarm_spit_command_201659 = _command(
    201659, 'Swarm Spit',
    _at_target(kits.command_potency(1450, 'II', cunning=True)),
    854, 636,
    'Spit a swarm of insects at the target, causing {pot1} Nature damage to it and all enemies within $a1 yards of it.'
    + _FALLOFF_TEXT,
    school=School.NATURE,
    notes='hunter-pet-families F3: Silithid II, 1450 x0.65 = 942.5 Nature to the target and the enemies within 8 yd of '
          'it (TargetA 53 / B 16), spell_hun_command_aoe_falloff. 30 yd. Visual 854 / icon 636 from Acid Spit 55749.',
)

qiraji_fortitude_201780 = _utility(
    201780, 'Qiraji Fortitude', QIRAJI_FORTITUDE_LEVEL,
    [_raid_aura(AuraType.MOD_STAT, 10, misc_value=2, points_per_level=0.8644)],
    685, 278,
    'Your pet hardens its allies with Qiraji resilience, increasing the Stamina of all party and raid members by $s1 '
    'for $d. Does not stack with Power Word: Fortitude or Prayer of Fortitude.',
    school=School.NATURE, cooldown_ms=40000, duration_ms=120000, RangeIndex=1, MaxLevel=80,
    AuraDescription_Lang_enUS='Stamina increased by $s1.',
    notes='hunter-pet-families F3: Silithid slot 2 (rare), autocast. Aura 29 Stamina, Power Word: Fortitude 1243\'s '
          'values moved to SpellLevel 10 (bp 2 + 9 x 0.8644 = 10, 0.8644/level: 54 at 60, as 1243), raid 100 yd, 2 '
          'min, 40 s cooldown. Group 1084 Single Stamina Buffs (rule 4). Visual 278 / icon 685 from Power Word: '
          'Fortitude 1243.',
)

swarm_shield_202013 = _utility(
    202013, 'Swarm Shield', SWARM_SHIELD_LEVEL,
    [Effect(type=EffectType.APPLY_AURA, ap_potency=300.0, potency_kind='absorb', implicit_target_a=_TARGET_UNIT_MASTER,
            apply_aura=AuraType.SCHOOL_ABSORB, misc_value=_SCHOOL_MASK_ALL)],
    566, 784,
    'Your pet surrounds you with a swarm that absorbs {pot1} damage for $d.',
    school=School.NATURE, cooldown_ms=60000, duration_ms=15000, RangeIndex=1, pet_owner_scaling=_PET_SCALING,
    AuraDescription_Lang_enUS='Absorbs damage.',
    notes='hunter-pet-families F3: Silithid slot 3, manual. Bubble Shield 201998\'s shape: aura 69 SCHOOL_ABSORB all '
          'schools on the hunter (TargetA 27 MASTER, FE 9f), 300 potency on the heal scale, 15 s, 1 min; '
          'spell_hun_pet_absorb (F2, PLAN §5.2 `absorb`) adds the generated ap_bonus x the pet\'s attack power. Visual '
          '784 / icon 566 from Power Word: Shield 17.',
)


# =====================================================================================================================
# Command display passives 202143-202162 (command order, the C++ COMMAND_DISPLAYS pairs)
# =====================================================================================================================

sonic_bite_display_202143 = _display(
    sonic_bite_command_201640, 'I', 87,
    'Bite the target with a sonic shriek, causing ' + pot_text(sonic_bite_command_201640) + ' Physical damage. The '
    'shriek bounces to one more nearby enemy, which takes ' + str(round(_BOUNCE_AMPLITUDE * 100)) + _SPLASH_TAIL,
    display_id=202143,
)
shriek_display_202144 = _display(
    shriek_command_201641, 'II', 458,
    'Shriek at the target and all enemies in a cone in front of your pet, causing ' + pot_text(shriek_command_201641)
    + ' Physical damage.' + _FALLOFF_TEXT,
    display_id=202144,
)
talon_rake_display_202145 = _display(
    talon_rake_command_201642, 'I', 2328,
    'Rake the target with your talons for ' + pot_text(talon_rake_command_201642) + ' Physical damage and an '
    'additional ' + pot_text(talon_rake_command_201642, effect=2, variant='total') + ' Physical damage over '
    '$201642d.',
    display_id=202145,
)
swoop_display_202146 = _display(
    swoop_command_201643, 'II', 277,
    'Swoop down on the target, causing ' + pot_text(swoop_command_201643) + ' Physical damage.',
    display_id=202146,
)
lightning_breath_display_202147 = _display(
    lightning_breath_command_201644, 'I', 62,
    'Breathe lightning at the target, causing ' + pot_text(lightning_breath_command_201644) + ' Nature damage.',
    display_id=202147,
)
chain_lightning_display_202148 = _display(
    chain_lightning_command_201645, 'II', 165,
    'Strike the target with lightning that jumps to 2 more nearby enemies, causing '
    + pot_text(chain_lightning_command_201645) + ' Nature damage. Each jump deals ' + str(_SPLASH_PCT) + _SPLASH_TAIL,
    display_id=202148,
)
fire_breath_display_202149 = _display(
    fire_breath_command_201646, 'I', 2128,
    'Breathe fire at the target for ' + pot_text(fire_breath_command_201646) + ' Fire damage and an additional '
    + pot_text(fire_breath_command_201646, effect=2, variant='total') + ' Fire damage over $201646d.',
    display_id=202149,
)
flame_nova_display_202150 = _display(
    flame_nova_command_201647, 'II', 33,
    'Engulf the target in flame, causing ' + pot_text(flame_nova_command_201647) + ' Fire damage to it and all enemies '
    'within $201647a1 yards of it.' + _FALLOFF_TEXT,
    display_id=202150,
)
ravage_display_202151 = _display(
    ravage_command_201648, 'I', 2253,
    'Ravage the target for ' + pot_text(ravage_command_201648) + ' Physical damage and an additional '
    + pot_text(ravage_command_201648, effect=2, variant='total') + ' Physical damage over $201648d.',
    display_id=202151,
)
gut_rip_display_202152 = _display(
    gut_rip_command_201649, 'II', 2046,
    'Rip into the target, causing ' + pot_text(gut_rip_command_201649) + ' Physical damage.',
    display_id=202152,
)
poison_spit_display_202153 = _display(
    poison_spit_command_201650, 'I', 68,
    'Spit poison at the target, causing ' + pot_text(poison_spit_command_201650, variant='total') + ' Nature damage '
    'over $201650d.',
    display_id=202153,
)
constrict_display_202154 = _display(
    constrict_command_201651, 'II', 2678,
    'Coil around the target, causing ' + pot_text(constrict_command_201651, variant='total') + ' Physical damage over '
    '$201651d and rooting it for $201672d. The root does not work on bosses.',
    display_id=202154,
)
spore_burst_display_202155 = _display(
    spore_burst_command_201652, 'I', 170,
    'Burst spores on the target, causing ' + pot_text(spore_burst_command_201652) + ' Nature damage, and '
    + pot_text(spore_burst_splash_201675) + ' Nature damage to all other enemies within $201675a1 yards of it.',
    display_id=202155,
)
fungal_bloom_display_202156 = _display(
    fungal_bloom_command_201653, 'II', 2681,
    'Seed a fungal bloom on the target, causing ' + pot_text(fungal_bloom_command_201653, variant='total')
    + ' Nature damage over $201653d to it and ' + pot_text(fungal_bloom_splash_201674, variant='total')
    + ' Nature damage over $201653d to all other enemies within $201674a1 yards of it.',
    display_id=202156,
)
nether_shock_display_202157 = _display(
    nether_shock_command_201654, 'I', 2027,
    'Shock the target with nether energy, causing ' + pot_text(nether_shock_command_201654) + ' Arcane damage.',
    display_id=202157,
)
nether_lash_display_202158 = _display(
    nether_lash_command_201655, 'II', 1485,
    'Lash the target with nether energy, causing ' + pot_text(nether_lash_command_201655) + ' Arcane damage.',
    display_id=202158,
)
twin_bite_display_202159 = _display(
    twin_bite_command_201656, 'I', 2108,
    'Bite the target twice: a frost bite causing ' + pot_text(twin_bite_command_201656) + ' Frost damage, then a '
    'venom bite causing ' + pot_text(twin_bite_second_bite_201670) + ' Nature damage.',
    display_id=202159,
)
froststorm_breath_display_202160 = _display(
    froststorm_breath_command_201657, 'II', 62,
    'Breathe a frost storm at the target for $201657d, causing ' + pot_text(froststorm_breath_tick_201671)
    + ' Frost damage every second to it and all enemies in a cone in front of your pet. Your pet channels for the '
    'whole breath.' + _FALLOFF_TEXT,
    display_id=202160,
)
venom_web_spray_display_202161 = _display(
    venom_web_spray_command_201658, 'I', 272,
    'Spray venomous webbing on the target, causing ' + pot_text(venom_web_spray_command_201658, variant='total')
    + ' Nature damage over $201658d and rooting it for $201673d. The root does not work on bosses.',
    display_id=202161,
)
swarm_spit_display_202162 = _display(
    swarm_spit_command_201659, 'II', 636,
    'Spit a swarm of insects at the target, causing ' + pot_text(swarm_spit_command_201659) + ' Nature damage to it '
    'and all enemies within $201659a1 yards of it.' + _FALLOFF_TEXT,
    display_id=202162,
)


# =====================================================================================================================
# SkillLineAbility rows (AcquireMethod 2, ClassMask 0): slot 2 then slot 3 per family, 30636-30639 then 30870-30885
# =====================================================================================================================

CUNNING_F3_SLA_ROWS = (
    (30636, 653, screech_201771.id), (30637, 653, sonic_blast_202004.id),                    # Bat
    (30638, 655, keen_sight_201772.id), (30639, 655, snatch_202005.id),                      # Bird of Prey
    (30870, 656, storm_breath_201773.id), (30871, 656, gale_barrier_202006.id),              # Wind Serpent
    (30872, 763, scorching_breath_201774.id), (30873, 763, blinding_flash_202007.id),        # Dragonhawk
    (30874, 767, rending_claws_201775.id), (30875, 767, chitinous_shell_202008.id),          # Ravager
    (30876, 768, paralyzing_venom_201776.id), (30877, 768, shed_skin_202009.id),             # Serpent
    (30878, 765, energizing_spores_201777.id), (30879, 765, restorative_spores_202010.id),   # Sporebat
    (30880, 764, nether_currents_201778.id), (30881, 764, nether_pulse_202011.id),           # Nether Ray
    (30882, 780, arcane_resonance_201779.id), (30883, 780, frost_nova_202012.id),            # Chimaera
    (30884, 783, qiraji_fortitude_201780.id), (30885, 783, swarm_shield_202013.id),          # Silithid
)
assert sorted(r[0] for r in CUNNING_F3_SLA_ROWS) == [*range(30636, 30640), *range(30870, 30886)]
for _sla_id, _line, _spell_id in CUNNING_F3_SLA_ROWS:
    skill_line_ability(id=_sla_id, skill_line=_line, spell_id=_spell_id, class_mask=0, acquire_method=2)


# =====================================================================================================================
# Spell groups (stock groups, DI §4.1; ruling 7) and the raid damage taken group 1232 (F2 declared its rule 4)
# =====================================================================================================================

spell_group(1062, screech_201771)            # AP Debuffs (rule 4)
spell_group(1036, keen_sight_201772)         # Spell Crit Buffs (rule 4)
spell_group(1101, storm_breath_201773)       # Spell Damage Taken Debuffs (rule 3)
spell_group(1101, scorching_breath_201774)   # Spell Damage Taken Debuffs (rule 3)
spell_group(1015, rending_claws_201775)      # Major Armor Debuffs (rule 3)
spell_group(1096, paralyzing_venom_201776)   # Cast Time Debuffs (rule 4)
spell_group(1048, arcane_resonance_201779)   # Spell Power Buffs (rule 4)
spell_group(1084, qiraji_fortitude_201780)   # Single Stamina Buffs (rule 4)
spell_group(SPELL_GROUP_RAID_DAMAGE_TAKEN, gale_barrier_202006)    # with Earthen Bulwark (rule 4, ruling 7)
spell_group_rule(SPELL_GROUP_SPELL_HASTE, 3,
                 'Spell Haste Buffs (aura 65): Fire Attunement, Wrath of Air, Energizing Spores, Nether Currents; only '
                 'the highest applies')
spell_group(SPELL_GROUP_SPELL_HASTE, energizing_spores_201777, nether_currents_201778, _FIRE_ATTUNEMENT, _WRATH_OF_AIR)


# =====================================================================================================================
# Script bindings (PLAN §5.2). Positive keys only (L7).
# =====================================================================================================================

scripted_by(shriek_command_201641, 'spell_hun_command_aoe_falloff')
scripted_by(chain_lightning_command_201645, 'spell_hun_command_aoe_falloff')
scripted_by(flame_nova_command_201647, 'spell_hun_command_aoe_falloff')
scripted_by(froststorm_breath_tick_201671, 'spell_hun_command_aoe_falloff')
scripted_by(swarm_spit_command_201659, 'spell_hun_command_aoe_falloff')
scripted_by(twin_bite_command_201656, 'spell_hun_command_multihit')     # twohit: one follow-up
scripted_by(froststorm_breath_command_201657, 'spell_hun_command_pulse')
scripted_by(spore_burst_splash_201675, 'spell_hun_command_splash')
scripted_by(fungal_bloom_splash_201674, 'spell_hun_command_splash')
scripted_by(snatch_202005, 'spell_hun_pet_control_boss_filter')
scripted_by(blinding_flash_202007, 'spell_hun_pet_control_boss_filter')
scripted_by(frost_nova_202012, 'spell_hun_pet_control_boss_filter')
scripted_by(constrict_root_201672, 'spell_hun_pet_control_boss_filter')
scripted_by(venom_web_spray_root_201673, 'spell_hun_pet_control_boss_filter')
scripted_by(swarm_shield_202013, 'spell_hun_pet_absorb')

# Every pet-cast spell above keeps the pet bit: the lint (c) contract of _masks.py.
assert m.PET_ABILITY == 0x10000000
