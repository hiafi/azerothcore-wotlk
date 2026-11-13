"""
Hunter pet families F1 (.agents/plans/hunter-pet-families/hunter-pet-families.PLAN.md §3.1, §4.1, §5;
hunter-pet-families.F1.HANDOFF.md): the 8 Ferocity families without a kit get their full kit. Per family, in the §3.1
table order (Carrion Bird, Hyena, Tallstrider, Moth, Wasp, Devilsaur, Core Hound, Spirit Beast): Command I and II,
their two "Command I/II: <ability>" display passives, a slot 2 group effect and a slot 3 utility, and their two
SkillLineAbility rows (AcquireMethod 2, learned at the pet level = SpellLevel).

Ids (PLAN §4.1, the F1 column): commands 201606-201621 (Command I then II per family), command helpers 201660-201662
(multi-hit strikes, Twin Bite's second bite), displays 202109-202124 (command order), slot 2 201754-201761, slot 3
201987-201994, utility helpers 202017-202018, SkillLineAbility 30556-30559 + 30606-30617 (slot 2 then slot 3 per
family).

Rules:
- Potency (ruling 1): every Command I is kits.command_potency(x, 'I'), every Command II kits.command_potency(x, 'II')
  of the §3.1 number (a DoT's number is its total over the duration; a multi-hit's is per hit).
- Ruling 24 (PLAN §11): every single-target command and its non-area damage helpers pass `ferocity=True,
  single_target=True` (x1.07, kits.FEROCITY_ST_COMMAND_SCALE) and append kits.ruling_24_note. The two AoE commands
  (Dazzling Wings, Lava Breath: Beast Cleave excludes them) keep the plain scale.
- Every slot 2 / slot 3 utility carries d1 b28 + b29 (kits.utility_raw), except Ancient Hysteria and Eternal Guardian
  (ruling 10: b28 only, mobility=False). Group effects use TargetA 56 (ruling 7). Ancient Hysteria, Eternal Guardian
  and every slot 3 are manual; the C++ kit row sets PET_KIT_GROUP_AUTOCAST for the other six slot 2 spells.
- Unlock levels: the class equivalent's level on this server (trainer_spell, or 10 + 5 x the talent tier), else 30
  (F0's Tail Sweep rule); a pet self-heal shares Lick Your Wounds' 36 (F0's rule).
- Scripts (PLAN §5.2), bound below: execute (Carrion Feast), multihit (Cackling Frenzy, Swarm), boss (Paralytic
  Sting, Earthshaking Stomp), res (Eternal Guardian), scavenge (Scavenge), Bloodlust (Ancient Hysteria, the stock
  spell_sha_bloodlust), falloff (Dazzling Wings, Lava Breath). twohit (Twin Bite) is multihit with one follow-up; the
  second bite is a command helper, which the F0 helper rule keeps out of Beast Cleave.

Imports only helpers and constants from the sibling modules (never a spell object: lib/dsl/registry.py
_collect_var_names keeps the first module's name for an id).
"""

from lib.dsl import AuraType, Effect, EffectType, School
from lib.dsl.registry import const, pot_text, scripted_by, skill_line_ability, spell, spell_group
from . import _masks as m
from . import _pet_kits as kits
from .hunter_bm_spells import COMMAND_AOE_FALLOFF_PCT, _cmd_raw, _direct, _display, _dot, _PET_SCALING

# ---- script numbers (the C++ reads them from HunterData.h) ----
COMMAND_EXECUTE_HEALTH_PCT = const(
    'COMMAND_EXECUTE_HEALTH_PCT', 35,
    'Execute commands (spell_hun_command_execute): the bonus applies below this target health, percent (FE 10g).',
)
COMMAND_EXECUTE_BONUS_PCT = const(
    'COMMAND_EXECUTE_BONUS_PCT', 50,
    'Execute commands (spell_hun_command_execute): extra damage below the threshold, percent (Carrion Feast).',
)
COMMAND_MULTIHIT_INTERVAL_MS = const(
    'COMMAND_MULTIHIT_INTERVAL_MS', 300,
    'Multi-hit commands (spell_hun_command_multihit): delay between two strikes, ms (FE 10f).',
)
SCAVENGE_RADIUS_YD = const(
    'SCAVENGE_RADIUS_YD', 20.0,
    'Scavenge (ruling 4): an enemy killed this close to a pet that knows Scavenge gives it Fresh Kill, yards.',
)

# ---- unlock levels (pet level = SpellLevel; see the module docstring) ----
DEMORALIZING_SCREECH_LEVEL = 14     # Demoralizing Shout 1160 (trainer 14)
SCAVENGE_LEVEL = 36                 # a pet self-heal: Lick Your Wounds / Frenzied Regeneration (F0)
CACKLING_HOWL_LEVEL = 32            # Air Attunement (32; Windfury Totem's old level, untrained by the shaman rework)
INFECTED_BITE_LEVEL = 20            # Mortal Strike (talent tier 3 = 20)
DUST_CLOUD_LEVEL = 20               # Insect Swarm (talent tier 3 = 20)
LONG_STRIDE_LEVEL = 16              # Aspect of the Cheetah 5118 (trainer 16)
MOONGLOW_DUST_LEVEL = 26            # Mana Spring Totem's old level (26; untrained, Water Attunement replaced it)
HEALING_DUST_LEVEL = 12             # Mend Pet 136 (trainer 12)
VENOMOUS_STING_LEVEL = 15           # Heart of the Crusader (talent tier 2 = 15)
PARALYTIC_STING_LEVEL = 30          # Intimidation 19577 (trainer 30)
PRIMAL_ROAR_LEVEL = 30              # Sanctified Retribution (talent tier 5 = 30; Ferocious Inspiration is 40)
EARTHSHAKING_STOMP_LEVEL = 30       # no class equivalent (War Stomp is racial): F0's Tail Sweep rule
ANCIENT_HYSTERIA_LEVEL = 60         # Bloodlust 2825 / Heroism 32182 (trainer 60)
MOLTEN_HIDE_LEVEL = 30              # no class equivalent at -30% for 10 s: F0's Tail Sweep rule
ETERNAL_GUARDIAN_LEVEL = 20         # Rebirth 20484 (trainer 20)
SPIRIT_MEND_LEVEL = 30              # Tranquility 740 (trainer 30)

# Aura and effect types the DSL enum doesn't name (SpellAuraDefines.h / SharedDefines.h).
_AURA_MOD_HIT_CHANCE = 54
_AURA_MOD_MELEE_RANGED_HASTE = 192
_AURA_MOD_POWER_REGEN = 85
_AURA_MOD_RANGED_HASTE = 140
_EFFECT_JUMP = 41
_EFFECT_RESURRECT = 18              # percent of max health and mana (Spell::EffectResurrect)
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

_SUPPRESS_CASTER_PROCS = 0x10000    # AttributesEx3: a command helper procs nothing (the command itself already did)
_ATTR1_NO_AUTOCAST_AI = 0x20000     # AttributesEx: the pet AI never autocasts it (as Bloodlust, Rebirth); clickable
_GROUP_BUFF_RADIUS_YD = 100.0       # Roar of Courage / Furious Howl
_SPLASH_TAIL = '% damage.'


def _command(spell_id, name, effects, visual, icon, description, *, school=School.NORMAL, range_yards=5.0,
             duration_ms=None, dmg_class=2, melee_range_index=True, notes=''):
    """A commanded pet spell (PET 4.9 template, hunter_bm_spells.py): pet-cast, instant, no cost / cooldown / GCD,
    d1 b28 + d2 b22, SpellLevel 1. Melee by default (RangeIndex 2, the pet's melee reach)."""
    raw = {**_cmd_raw(visual, dmg_class=dmg_class, prevention=2 if dmg_class == 2 else 1), 'SpellIconID': icon,
           'Description_Lang_enUS': description}
    if melee_range_index:
        raw['RangeIndex'] = 2
    kwargs = {'duration_ms': duration_ms} if duration_ms is not None else {}
    return spell(
        id=spell_id, name=name, school=school, attributes=0x50010, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=range_yards, effects=effects,
        pet_owner_scaling=_PET_SCALING, notes=notes, raw_overrides=raw, **kwargs,
    )


def _helper_strike(spell_id, name, potency, visual, *, school=School.NORMAL, notes=''):
    """A command helper hit (a multi-hit strike, a second bite): the commanded-spell carrier (so Phoenix's Plume and
    Master's Command reach it) that no kit slots, so Hunter::IsBeastCleaveExcluded keeps it out of Beast Cleave (F0's
    helper rule); SUPPRESS_CASTER_PROCS so a multi-hit command procs the pet talents once, like every other command.
    10 yd range: a triggered cast is range-checked strictly, and the pet may step back between two strikes."""
    return spell(
        id=spell_id, name=name, school=school, attributes=0x50010, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=10.0, effects=[_direct(potency)],
        pet_owner_scaling=_PET_SCALING, notes=notes,
        raw_overrides={**_cmd_raw(visual), 'AttributesEx3': _SUPPRESS_CASTER_PROCS},
    )


def _follow_ups(helper, count):
    """eff1 of a multi-hit command (spell_hun_command_multihit): DUMMY on the target naming the strike helper
    (TriggerSpell) and the follow-up count (its value; stored base points = count - 1)."""
    return Effect(type=EffectType.DUMMY, base_points=count - 1, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
                  trigger_spell=helper.id)


def _dot_rate(total, duration_ms):
    """A periodic potency is a rate per 1.5 s (lib/potency.py: per-tick value = rate x amplitude / 1.5 s), so the
    total over `duration_ms` is rate x duration / 1500."""
    return round(total * 1500.0 / duration_ms, 4)


def _utility(spell_id, name, level, effects, icon, visual, description, *, school=School.NORMAL, cooldown_ms,
             duration_ms=None, range_yards=0.0, enemy_target=False, mobility=True, defense=0, prevention=2,
             pet_owner_scaling=None, notes='', **raw):
    """A slot 2 / slot 3 pet utility: pet-cast, Focus 0, family 9 with d1 b28 (+ b29 unless `mobility=False`)."""
    kwargs = {'duration_ms': duration_ms} if duration_ms is not None else {}
    if pet_owner_scaling is not None:
        kwargs['pet_owner_scaling'] = pet_owner_scaling
    return spell(
        id=spell_id, name=name, school=school, attributes=kits.UTILITY_ATTRIBUTES, cast_time_ms=0,
        cooldown_ms=cooldown_ms, category_cooldown_ms=0, power_type=kits.UTILITY_POWER_TYPE, mana_cost=0,
        mana_cost_pct=0, range_yards=range_yards, effects=effects, spell_icon_id=icon, notes=notes,
        raw_overrides=kits.utility_raw(level, enemy_target=enemy_target, mobility=mobility, DefenseType=defense,
                                       PreventionType=prevention, SpellVisualID_1=visual,
                                       Description_Lang_enUS=description, **raw),
        **kwargs,
    )


def _raid_aura(aura, base_points, misc_value=0, points_per_level=0.0):
    """One effect of a raid buff: TargetA 56 (CASTER_AREA_RAID, ruling 7), 100 yd."""
    return Effect(type=EffectType.APPLY_AURA, base_points=base_points, points_per_level=points_per_level,
                  implicit_target_a=_TARGET_UNIT_CASTER_AREA_RAID, apply_aura=aura, misc_value=misc_value,
                  radius_yards=_GROUP_BUFF_RADIUS_YD)


def _multi_hit_text(verb, count, spell_ref, noun):
    return f'{verb} the target {count} times in quick succession, each {noun} causing {spell_ref} Physical damage.'


_EXECUTE_TEXT = (f" Deals {COMMAND_EXECUTE_BONUS_PCT['value']}% more damage to targets below "
                 f"{COMMAND_EXECUTE_HEALTH_PCT['value']}% health.")
_FALLOFF_TEXT = f" Enemies other than the target take {COMMAND_AOE_FALLOFF_PCT['value']}{_SPLASH_TAIL}"


# =====================================================================================================================
# Carrion Bird (family 7, skill line 213, basic Bite)
# =====================================================================================================================

_REND_FLESH_MS = 9000
rend_flesh_command_201606 = _command(
    201606, 'Rend Flesh',
    [_direct(kits.command_potency(150, 'I', ferocity=True, single_target=True)),
     _dot(_dot_rate(kits.command_potency(250, 'I', ferocity=True, single_target=True), _REND_FLESH_MS), 3000,
          mechanic=_MECHANIC_BLEED, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    372, 500,
    'Rend the target for {pot1} Physical damage and an additional {pot2.total} Physical damage over $d.',
    duration_ms=_REND_FLESH_MS,
    notes='hunter-pet-families F1: Carrion Bird I. eff0 150 x0.84 = 126 direct, eff1 bleed 250 x0.84 = 210 over 9 s '
          '(rate 35 per 1.5 s, 3 s ticks), Mechanic 15. Visual 372 from Rend 772, icon 500 (Rupture).'
          + kits.ruling_24_note('Ferocity', kits.command_potency(150, 'I'), kits.command_potency(250, 'I')),
)

carrion_feast_command_201607 = _command(
    201607, 'Carrion Feast',
    [_direct(kits.command_potency(800, 'II', ferocity=True, single_target=True))],
    2275, 116,
    'Feast on the target, causing {pot1} Physical damage.' + _EXECUTE_TEXT,
    notes='hunter-pet-families F1: Carrion Bird II. 800 x0.65 = 520 Physical; spell_hun_command_execute adds 50% '
          'below 35% target health (FE 10g). Visual 2275 from Ravage 6785, icon 116 (Carrion Swarm).'
          + kits.ruling_24_note('Ferocity', kits.command_potency(800, 'II')),
)

demoralizing_screech_201754 = _utility(
    201754, 'Demoralizing Screech', DEMORALIZING_SCREECH_LEVEL,
    [Effect(type=EffectType.APPLY_AURA, base_points=-36, points_per_level=-5.696969696969697,
            implicit_target_a=_TARGET_SRC_CASTER, implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY,
            apply_aura=AuraType.MOD_ATTACK_POWER, radius_yards=10.0)],
    1579, 7302,
    'Your pet screeches, reducing the attack power of all enemies within $a1 yards by $s1 for $d. Does not stack '
    'with Demoralizing Shout, Demoralizing Roar, Menacing Roar, Vindication or Curse of Weakness.',
    cooldown_ms=10000, duration_ms=30000, defense=1, prevention=1,
    MaxLevel=80, AttributesEx=kits.ATTR1_INITIATE_COMBAT, AttributesEx6=8388608, RangeIndex=1,
    AuraDescription_Lang_enUS='Attack power reduced.',
    notes='hunter-pet-families F1: Carrion Bird slot 2, autocast. Menacing Roar 201717 shape (Demoralizing Shout 1160: '
          'bp -36, -5.697/level from 14 to 80, around the pet 10 yd), 30 s, 10 s cooldown. Group 1062 AP Debuffs '
          '(rule 4, aura 99). Visual 7302 / icon 1579 from Demoralizing Screech 24423.',
)

fresh_kill_202018 = spell(
    id=202018,
    name='Fresh Kill',
    school=School.NORMAL,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.DUMMY),
    ],
    spell_icon_id=146,
    notes='hunter-pet-families F1: Scavenge window (ruling 4). A visible 10 s buff Hunter::OnScavengeKill puts on a '
          'hunter pet that knows Scavenge when an enemy dies within SCAVENGE_RADIUS_YD of it (a player-side kill); '
          'spell_hun_pet_scavenge needs it and consumes it. Family 0, not passive. Icon 146 (Cannibalize).',
    raw_overrides={'EquippedItemClass': -1, 'SpellLevel': 1,
                   'AuraDescription_Lang_enUS': 'An enemy fell nearby. Your pet can Scavenge.'},
)

scavenge_201987 = _utility(
    201987, 'Scavenge', SCAVENGE_LEVEL,
    [Effect(type=EffectType.HEAL_PCT, base_points=59, implicit_target_a=1)],
    2316, 9035,
    'Your pet feeds on a fresh kill, healing itself for $s1% of its maximum health. Usable only within '
    '$202018d of an enemy dying within ' + str(int(SCAVENGE_RADIUS_YD['value'])) + ' yards of your pet.',
    cooldown_ms=60000, RangeIndex=1,
    notes='hunter-pet-families F1: Carrion Bird slot 3, manual. eff0 HEAL_PCT 60% on the pet (ruling 4). '
          'spell_hun_pet_scavenge: CheckCast needs Fresh Kill 202018 on the pet (SPELL_FAILED_NO_EDIBLE_CORPSES '
          'otherwise), AfterCast removes it. 1 min. Visual 9035 / icon 2316 from Scavenge 44422.',
)


# =====================================================================================================================
# Hyena (family 25, skill line 654, basic Bite)
# =====================================================================================================================

_TENDON_RIP_MS = 6000
tendon_rip_command_201608 = _command(
    201608, 'Tendon Rip',
    [_direct(kits.command_potency(400, 'I', ferocity=True, single_target=True)),
     Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
            apply_aura=AuraType.MOD_DECREASE_SPEED, mechanic=_MECHANIC_SNARE)],
    842, 138,
    "Rip the target's tendons, causing {pot1} Physical damage and reducing its movement speed by ${$m2*-1}% for $d.",
    duration_ms=_TENDON_RIP_MS,
    notes='hunter-pet-families F1: Hyena I. eff0 400 x0.84 = 336 Physical, eff1 -50% speed 6 s (Mechanic 11, free per '
          'ruling 3). Visual 842 / icon 138 from Tendon Rip 50271.'
          + kits.ruling_24_note('Ferocity', kits.command_potency(400, 'I')),
)

cackling_frenzy_strike_201660 = _helper_strike(
    201660, 'Cackling Frenzy', kits.command_potency(333, 'II', ferocity=True, single_target=True), 376,
    notes='hunter-pet-families F1: Cackling Frenzy follow-up bite (command helper). 333 x0.65 = 216.45 Physical, cast '
          'twice by spell_hun_command_multihit after the command\'s own bite. Visual 376 from Bite 17253.'
          + kits.ruling_24_note('Ferocity', kits.command_potency(333, 'II')),
)

_CACKLING_FRENZY_HITS = 3
cackling_frenzy_command_201609 = _command(
    201609, 'Cackling Frenzy',
    [_direct(kits.command_potency(333, 'II', ferocity=True, single_target=True)),
     _follow_ups(cackling_frenzy_strike_201660, _CACKLING_FRENZY_HITS - 1)],
    376, 1565,
    _multi_hit_text('Bite', _CACKLING_FRENZY_HITS, '{pot1}', 'bite'),
    notes='hunter-pet-families F1: Hyena II, 3 x 333 (x0.65 = 216.45 each). eff0 the first bite, eff1 DUMMY: '
          'spell_hun_command_multihit casts 201660 twice, COMMAND_MULTIHIT_INTERVAL_MS apart. Visual 376 from Bite, '
          'icon 1565 (Hyena).'
          + kits.ruling_24_note('Ferocity', kits.command_potency(333, 'II')),
)

cackling_howl_201755 = _utility(
    201755, 'Cackling Howl', CACKLING_HOWL_LEVEL,
    [_raid_aura(AuraType.MOD_MELEE_HASTE, 9), _raid_aura(_AURA_MOD_RANGED_HASTE, 9)],
    1695, 7299,
    'Your pet howls, increasing the melee and ranged attack speed of all party and raid members by $s1% for $d. '
    'Does not stack with Improved Icy Talons or Air Attunement.',
    cooldown_ms=40000, duration_ms=120000, RangeIndex=1,
    AuraDescription_Lang_enUS='Melee and ranged attack speed increased.',
    notes='hunter-pet-families F1: Hyena slot 2, autocast. Aura 138 + 140, +10% each (Air Attunement 202210, the '
          'shaman version on this server), raid 100 yd, 2 min, 40 s cooldown (Roar of Courage shape). Group 1022 '
          'Melee Haste Buffs (rule 3, same effect). Visual 7299 (Furious Howl), icon 1695 (Battle Squawk).',
)

infected_bite_201988 = _utility(
    201988, 'Infected Bite', INFECTED_BITE_LEVEL,
    [Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
            apply_aura=AuraType.MOD_HEALING_PCT)],
    1614, 717,
    "Your pet's infected bite reduces all healing the target receives by ${$m1*-1}% for $d. Does not stack with "
    'Mortal Strike.',
    school=School.NATURE, cooldown_ms=30000, duration_ms=10000, range_yards=5.0, enemy_target=True, defense=2,
    RangeIndex=2, FacingCasterFlags=1,
    AuraDescription_Lang_enUS='Healing received reduced.',
    notes='hunter-pet-families F1: Hyena slot 3, manual. Aura 118 -50% healing received (Mortal Strike 12294 value), '
          '10 s, melee, 30 s. Group 1061 Healing Taken Debuffs (rule 4). Visual 717 / icon 1614 from Infected Bite '
          '16128.',
)


# =====================================================================================================================
# Tallstrider (family 12, skill line 218, basic Claw)
# =====================================================================================================================

leaping_kick_command_201610 = _command(
    201610, 'Leaping Kick',
    [Effect(type=_EFFECT_JUMP, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
     _direct(kits.command_potency(400, 'I', ferocity=True, single_target=True))],
    519, 246,
    'Leap to the target and kick it for {pot2} Physical damage.',
    range_yards=25.0, melee_range_index=False,
    notes='hunter-pet-families F1: Tallstrider I, the Lunge 201720 shape: eff0 JUMP (41) to the target, eff1 400 x0.84 '
          '= 336 Physical. 25 yd (the jump reach), DmgClass MELEE. Visual 519 (pet Charge), icon 246 (Kick).'
          + kits.ruling_24_note('Ferocity', kits.command_potency(400, 'I')),
)

stampeding_kick_command_201611 = _command(
    201611, 'Stampeding Kick',
    [_direct(kits.command_potency(1000, 'II', ferocity=True, single_target=True))],
    90, 1587,
    'Kick the target with great force, causing {pot1} Physical damage.',
    notes='hunter-pet-families F1: Tallstrider II, 1000 x0.65 = 650 Physical, no knockback (it would push the mob off '
          'the tank). Visual 90 from Kick 1766, icon 1587 (Tallstrider).'
          + kits.ruling_24_note('Ferocity', kits.command_potency(1000, 'II')),
)

dust_cloud_201756 = _utility(
    201756, 'Dust Cloud', DUST_CLOUD_LEVEL,
    [Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=_TARGET_DEST_TARGET_ENEMY,
            implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY, apply_aura=_AURA_MOD_HIT_CHANCE, radius_yards=10.0),
     Effect(type=EffectType.APPLY_AURA, base_points=-6, implicit_target_a=_TARGET_DEST_TARGET_ENEMY,
            implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY, apply_aura=AuraType.MOD_SPELL_HIT_CHANCE,
            radius_yards=10.0)],
    157, 804,
    'Your pet kicks up a cloud of dust, reducing the chance of the target and all enemies within $a1 yards of it to '
    'hit with melee, ranged attacks and spells by ${$m1*-1}% for $d.',
    school=School.NATURE, cooldown_ms=10000, duration_ms=30000, range_yards=5.0, enemy_target=True, defense=1,
    prevention=1, RangeIndex=2,
    AuraDescription_Lang_enUS='Chance to hit reduced.',
    notes='hunter-pet-families F1: Tallstrider slot 2, autocast. Aura 54 + 55, -5% hit (FE 4) on the target and '
          'enemies within 10 yd of it (TargetA 53 / B 16, stock 54404 shape), 30 s, 10 s cooldown. Group 1060 Hit '
          'Chance Debuffs (rule 3; its member Insect Swarm 5570 no longer carries aura 54 live). Visual 804 / icon 157 '
          'from Dust Cloud 50285.',
)

long_stride_201989 = _utility(
    201989, 'Long Stride', LONG_STRIDE_LEVEL,
    [Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=1, apply_aura=AuraType.MOD_INCREASE_SPEED),
     Effect(type=EffectType.APPLY_AURA, base_points=39, implicit_target_a=_TARGET_UNIT_MASTER,
            apply_aura=AuraType.MOD_INCREASE_SPEED)],
    516, 2276,
    'Your pet and you run $s1% faster for $d.',
    cooldown_ms=30000, duration_ms=6000, RangeIndex=1,
    AuraDescription_Lang_enUS='Movement speed increased.',
    notes='hunter-pet-families F1: Tallstrider slot 3, manual. Aura 31 +40% speed on the pet (TargetA 1) and the '
          'hunter (TargetA 27 MASTER, FE 9i), 6 s, 30 s. Speed auras take the highest. Visual 2276 (Dash), icon 516 '
          '(Sprint).',
)


# =====================================================================================================================
# Moth (family 37, skill line 775, basic Smack)
# =====================================================================================================================

serenity_dust_command_201612 = _command(
    201612, 'Serenity Dust',
    [_direct(kits.command_potency(600, 'I', ferocity=True, single_target=True))],
    8529, 1714,
    'Shake dust over the target, causing {pot1} Physical damage.',
    notes='hunter-pet-families F1: Moth I, 600 x0.84 = 504 Physical (600 = 400 + the 20% the AoE shift moved off '
          'Dazzling Wings, rule 15). Visual 8529 / icon 1714 from Serenity Dust 50318.'
          + kits.ruling_24_note('Ferocity', kits.command_potency(600, 'I')),
)

dazzling_wings_command_201613 = _command(
    201613, 'Dazzling Wings',
    [Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=kits.command_potency(800, 'II'), potency_kind='direct',
            implicit_target_a=_TARGET_UNIT_CONE_ENEMY, radius_yards=8.0),
     Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    4961, 1618,
    'Beat dazzling wings at the target and all enemies in a cone in front of your pet, causing {pot1} Physical '
    'damage.' + _FALLOFF_TEXT,
    notes='hunter-pet-families F1: Moth II, 800 x0.65 = 520 Physical, cone (TargetA 104) 8 yd. eff1 DUMMY on the '
          'target keeps the command\'s target as the spell\'s explicit target (a cone-only spell drops it, CORE-AUDIT '
          '2.2), which spell_hun_command_aoe_falloff reads as the primary; the dispatcher turns the pet to it first. '
          'Visual 4961 / icon 1618 from Wing Buffet 18500.',
)

moonglow_dust_201757 = _utility(
    201757, 'Moonglow Dust', MOONGLOW_DUST_LEVEL,
    [_raid_aura(_AURA_MOD_POWER_REGEN, 15, points_per_level=1.38889)],
    2261, 8529,
    'Your pet scatters glowing dust, restoring $s1 mana every 5 seconds to all party and raid members for $d. Does '
    'not stack with Blessing of Wisdom or Water Attunement.',
    school=School.NATURE, cooldown_ms=40000, duration_ms=120000, RangeIndex=1, MaxLevel=80,
    AuraDescription_Lang_enUS='Restores mana.',
    notes='hunter-pet-families F1: Moth slot 2, autocast. Aura 85 MOD_POWER_REGEN (mana), Mana Spring 5677 values '
          '(bp 15, +1.389/level from 26 to 80), raid 100 yd, 2 min, 40 s cooldown. Group 1105 MP5 Buffs (rule 3). '
          'Visual 8529 (Serenity Dust), icon 2261 (Arcane Dust).',
)

_HEALING_DUST_MS = 12000
healing_dust_201990 = _utility(
    201990, 'Healing Dust', HEALING_DUST_LEVEL,
    [Effect(type=EffectType.APPLY_AURA, ap_potency=_dot_rate(300, _HEALING_DUST_MS), potency_kind='heal_periodic',
            implicit_target_a=1, apply_aura=AuraType.PERIODIC_HEAL, amplitude=3000),
     Effect(type=EffectType.APPLY_AURA, ap_potency=_dot_rate(300, _HEALING_DUST_MS), potency_kind='heal_periodic',
            implicit_target_a=_TARGET_UNIT_MASTER, apply_aura=AuraType.PERIODIC_HEAL, amplitude=3000)],
    2315, 8529,
    'Your pet sheds healing dust, healing itself and you for {pot1.total} over $d.',
    school=School.NATURE, cooldown_ms=60000, duration_ms=_HEALING_DUST_MS, defense=1, prevention=1, RangeIndex=1,
    pet_owner_scaling=_PET_SCALING,
    AuraDescription_Lang_enUS='Healing over time.',
    notes='hunter-pet-families F1: Moth slot 3, manual. PERIODIC_HEAL on the pet (TargetA 1) and the hunter (TargetA '
          '27 MASTER, FE 9i), 300 potency each over 12 s (rate 37.5, 3 s ticks; Mend Pet 136 is 353 over 15 s), from '
          'the pet\'s AP (pet_owner_scaling). DefenseType 1 so the potency coefficient applies (custom-spells.md). '
          '1 min. Visual 8529 (Serenity Dust), icon 2315 (Dust).',
)


# =====================================================================================================================
# Wasp (family 44, skill line 785, basic Smack)
# =====================================================================================================================

_STING_MS = 6000
sting_command_201614 = _command(
    201614, 'Sting',
    [_direct(kits.command_potency(150, 'I', ferocity=True, single_target=True)),
     _dot(_dot_rate(kits.command_potency(250, 'I', ferocity=True, single_target=True), _STING_MS), 2000,
          implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    192, 110,
    'Sting the target for {pot1} Nature damage and poison it for an additional {pot2.total} Nature damage over $d.',
    school=School.NATURE, duration_ms=_STING_MS,
    notes='hunter-pet-families F1: Wasp I, Nature (the Venom Bite 201728 shape: one school per spell). eff0 150 x0.84 '
          '= 126, eff1 250 x0.84 = 210 over 6 s (rate 52.5, 2 s ticks). Visual 192 / icon 110 from Sting 56626.'
          + kits.ruling_24_note('Ferocity', kits.command_potency(150, 'I'), kits.command_potency(250, 'I')),
)

swarm_strike_201661 = _helper_strike(
    201661, 'Swarm', kits.command_potency(200, 'II', ferocity=True, single_target=True), 192,
    notes='hunter-pet-families F1: Swarm follow-up sting (command helper). 200 x0.65 = 130 Physical, cast four times '
          'by spell_hun_command_multihit after the command\'s own sting. Visual 192 from Sting 56626.'
          + kits.ruling_24_note('Ferocity', kits.command_potency(200, 'II')),
)

_SWARM_HITS = 5
swarm_command_201615 = _command(
    201615, 'Swarm',
    [_direct(kits.command_potency(200, 'II', ferocity=True, single_target=True)),
     _follow_ups(swarm_strike_201661, _SWARM_HITS - 1)],
    192, 1771,
    _multi_hit_text('Sting', _SWARM_HITS, '{pot1}', 'sting'),
    notes='hunter-pet-families F1: Wasp II, 5 x 200 (x0.65 = 130 each). eff0 the first sting, eff1 DUMMY: '
          'spell_hun_command_multihit casts 201661 four times. Visual 192 (Sting), icon 1771 (Insect Swarm).'
          + kits.ruling_24_note('Ferocity', kits.command_potency(200, 'II')),
)

venomous_sting_201758 = _utility(
    201758, 'Venomous Sting', VENOMOUS_STING_LEVEL,
    [Effect(type=EffectType.APPLY_AURA, base_points=2, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
            apply_aura=AuraType.MOD_ATTACKER_SPELL_AND_WEAPON_CRIT_CHANCE)],
    163, 192,
    'Your pet stings the target, increasing the chance that attacks and spells against it are critical strikes by '
    '$s1% for $d. Does not stack with Heart of the Crusader or Holy Guidance.',
    school=School.NATURE, cooldown_ms=10000, duration_ms=30000, range_yards=5.0, enemy_target=True, defense=2,
    RangeIndex=2, FacingCasterFlags=1,
    AuraDescription_Lang_enUS='Chance to be critically hit increased.',
    notes='hunter-pet-families F1: Wasp slot 2, autocast. Aura 197 +3% crit taken (ruling: crit taken 3%), single '
          'enemy, melee, 30 s, 10 s cooldown (Tear Armor shape). Group 1058 (rule 3, aura 197). Visual 192 (Sting), '
          'icon 163 (Poison Sting).',
)

paralytic_sting_201991 = _utility(
    201991, 'Paralytic Sting', PARALYTIC_STING_LEVEL,
    [Effect(type=EffectType.APPLY_AURA, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, apply_aura=AuraType.MOD_STUN,
            mechanic=_MECHANIC_STUN)],
    166, 2816,
    'Your pet stings the target, stunning it for $d. Does not work on bosses.',
    school=School.NATURE, cooldown_ms=60000, duration_ms=3000, range_yards=5.0, enemy_target=True, defense=2,
    RangeIndex=2, FacingCasterFlags=1,
    AuraDescription_Lang_enUS='Stunned.',
    notes='hunter-pet-families F1: Wasp slot 3, manual. Aura 12 MOD_STUN 3 s, Mechanic 12 (stun-immune creatures '
          'resist), melee, 1 min (Intimidation). spell_hun_pet_control_boss_filter refuses a world or dungeon boss '
          '(ruling 3). Visual 2816 / icon 166 from Intimidation 24394.',
)


# =====================================================================================================================
# Devilsaur (family 39, skill line 781, basic Bite)
# =====================================================================================================================

monstrous_bite_command_201616 = _command(
    201616, 'Monstrous Bite',
    [_direct(kits.command_potency(400, 'I', ferocity=True, single_target=True))],
    376, 599,
    'Bite the target, causing {pot1} Physical damage.',
    notes='hunter-pet-families F1: Devilsaur I, 400 x0.84 = 336 Physical. Visual 376 / icon 599 from Monstrous Bite '
          '54680.'
          + kits.ruling_24_note('Ferocity', kits.command_potency(400, 'I')),
)

primal_rampage_command_201617 = _command(
    201617, 'Primal Rampage',
    [_direct(kits.command_potency(1000, 'II', ferocity=True, single_target=True))],
    166, 2006,
    'Maul the target in a primal rage, causing {pot1} Physical damage.',
    notes='hunter-pet-families F1: Devilsaur II, 1000 x0.65 = 650 Physical. Visual 166 (Maul 6807), icon 2006 '
          '(Rampage).'
          + kits.ruling_24_note('Ferocity', kits.command_potency(1000, 'II')),
)

primal_roar_201759 = _utility(
    201759, 'Primal Roar', PRIMAL_ROAR_LEVEL,
    [_raid_aura(AuraType.MOD_DAMAGE_PERCENT_DONE, 2, misc_value=127)],
    2232, 7299,
    'Your pet roars, increasing the damage done by all party and raid members by $s1% for $d. Does not stack with '
    'Ferocious Inspiration, Sanctified Retribution or Arcane Empowerment.',
    cooldown_ms=40000, duration_ms=120000, RangeIndex=1,
    AuraDescription_Lang_enUS='Damage done increased.',
    notes='hunter-pet-families F1: Devilsaur slot 2 (rare), autocast. Aura 79 +3% all schools (Scroll of '
          'Empowerment / Ferocious Inspiration shape), raid 100 yd, 2 min, 40 s cooldown. Group 1056 Damage Done '
          'Buffs (rule 3). Visual 7299 (Furious Howl), icon 2232 (Ferocious Inspiration).',
)

earthshaking_stomp_201992 = _utility(
    201992, 'Earthshaking Stomp', EARTHSHAKING_STOMP_LEVEL,
    [Effect(type=EffectType.APPLY_AURA, implicit_target_a=_TARGET_SRC_CASTER,
            implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY, apply_aura=AuraType.MOD_STUN, mechanic=_MECHANIC_STUN,
            radius_yards=8.0)],
    129, 5719,
    'Your pet stomps the ground, stunning all enemies within $a1 yards for $d. Does not work on bosses.',
    cooldown_ms=60000, duration_ms=2000, defense=2, RangeIndex=1, AttributesEx=kits.ATTR1_INITIATE_COMBAT,
    AuraDescription_Lang_enUS='Stunned.',
    notes='hunter-pet-families F1: Devilsaur slot 3, manual. Aura 12 MOD_STUN 2 s around the pet (TargetA 22 / B 15) '
          '8 yd, Mechanic 12, 1 min. spell_hun_pet_control_boss_filter drops world and dungeon bosses from the area '
          '(ruling 3). No AttributesEx5 0x20 (the Mass Entanglement bug). Visual 5719 / icon 129 from War Stomp 20549.',
)


# =====================================================================================================================
# Core Hound (family 45, skill line 787, basic Bite)
# =====================================================================================================================

_LAVA_BREATH_MS = 6000
lava_breath_command_201618 = _command(
    201618, 'Lava Breath',
    [Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=kits.command_potency(300, 'I'), potency_kind='direct',
            implicit_target_a=_TARGET_UNIT_CONE_ENEMY, radius_yards=8.0),
     Effect(type=EffectType.APPLY_AURA, base_points=-51, implicit_target_a=_TARGET_UNIT_CONE_ENEMY,
            apply_aura=AuraType.MOD_DECREASE_SPEED, mechanic=_MECHANIC_SNARE, radius_yards=8.0),
     Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    8489, 1197,
    'Breathe lava at the target and all enemies in a cone in front of your pet, causing {pot1} Fire damage and '
    'reducing their movement speed by ${$m2*-1}% for $d.' + _FALLOFF_TEXT,
    school=School.FIRE, duration_ms=_LAVA_BREATH_MS,
    notes='hunter-pet-families F1: Core Hound I, 300 x0.84 = 252 Fire, cone (TargetA 104) 8 yd, eff1 -50% speed 6 s on '
          'the same cone (Mechanic 11, free). eff2 DUMMY on the target keeps it the explicit target, the primary of '
          'spell_hun_command_aoe_falloff (Dazzling Wings shape). Visual 8489 / icon 1197 from Lava Breath 58604.',
)

twin_bite_second_bite_201662 = _helper_strike(
    201662, 'Twin Bite', kits.command_potency(550, 'II', ferocity=True, single_target=True), 376,
    notes='hunter-pet-families F1: Twin Bite second bite (command helper, the twohit shape). 550 x0.65 = 357.5 '
          'Physical, cast once by spell_hun_command_multihit after 201619. Visual 376 from Bite 17253.'
          + kits.ruling_24_note('Ferocity', kits.command_potency(550, 'II')),
)

twin_bite_command_201619 = _command(
    201619, 'Twin Bite',
    [_direct(kits.command_potency(550, 'II', ferocity=True, single_target=True)),
     _follow_ups(twin_bite_second_bite_201662, 1)],
    376, 2108,
    'Bite the target twice, each bite causing {pot1} Physical damage.',
    notes='hunter-pet-families F1: Core Hound II, 2 x 550 (x0.65 = 357.5 each). twohit = spell_hun_command_multihit '
          'with one follow-up (F1 review MINOR 1: the second bite rolls its own hit, 300 ms after the cast): eff0 the '
          'first bite, eff1 DUMMY naming 201662. One school and one direct coefficient per spell (D6); F3 Chimaera '
          'reuses the shape with a Nature second bite. Visual 376 (Bite), icon 2108 (Blade Twisting).'
          + kits.ruling_24_note('Ferocity', kits.command_potency(550, 'II')),
)

ancient_hysteria_201760 = _utility(
    201760, 'Ancient Hysteria', ANCIENT_HYSTERIA_LEVEL,
    [_raid_aura(_AURA_MOD_MELEE_RANGED_HASTE, 29), _raid_aura(AuraType.MOD_SCALE, 29),
     _raid_aura(AuraType.MOD_CASTING_SPEED_NOT_STACK, 29)],
    95, 7870,
    'Your pet lets out a hysterical howl, increasing the melee, ranged and spell casting speed of all party and raid '
    'members by $s1% for $d. Allies who receive this effect cannot benefit from Ancient Hysteria, Bloodlust, Heroism '
    'or Time Warp again for 10 min.',
    school=School.NATURE, cooldown_ms=300000, duration_ms=40000, mobility=False, RangeIndex=1,
    AttributesEx=_ATTR1_NO_AUTOCAST_AI,
    AuraDescription_Lang_enUS='Melee, ranged and casting speed increased.',
    notes='hunter-pet-families F1: Core Hound slot 2 (rare), manual. Bloodlust 2825\'s effects (aura 192 + 61 + 65, '
          '+30%), raid 100 yd, 40 s, 5 min (ruling 9). Bound to the stock spell_sha_bloodlust (filters Sated / '
          'Exhaustion targets, applies Sated 57724). d1 b28 only: Mobility does not shorten it (ruling 10). Visual '
          '7870 (Bloodlust), icon 95 (Unholy Frenzy, the stock Ancient Hysteria 19372).',
)

molten_hide_201993 = _utility(
    201993, 'Molten Hide', MOLTEN_HIDE_LEVEL,
    [Effect(type=EffectType.APPLY_AURA, base_points=-31, implicit_target_a=1,
            apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127)],
    2307, 7425,
    'Your pet hardens its molten hide, reducing all damage it takes by ${$m1*-1}% for $d.',
    school=School.FIRE, cooldown_ms=60000, duration_ms=10000, RangeIndex=1,
    AuraDescription_Lang_enUS='Damage taken reduced.',
    notes='hunter-pet-families F1: Core Hound slot 3, manual. Aura 87 -30% all schools on the pet (Shell Shield 26064 '
          'shape, FE 9c), 10 s, 1 min. Visual 7425 (Shell Shield), icon 2307 (Molten Armor).',
)


# =====================================================================================================================
# Spirit Beast (family 46, skill line 788, basic Claw)
# =====================================================================================================================

spirit_strike_command_201620 = _command(
    201620, 'Spirit Strike',
    [_direct(kits.command_potency(400, 'I', ferocity=True, single_target=True))],
    1263, 225,
    'Strike the target with spirit energy, causing {pot1} Nature damage.',
    school=School.NATURE,
    notes='hunter-pet-families F1: Spirit Beast I, 400 x0.84 = 336 Nature (melee DmgClass, the Venom Bite precedent). '
          'Visual 1263 / icon 225 from Spirit Strike 61193.'
          + kits.ruling_24_note('Ferocity', kits.command_potency(400, 'I')),
)

spirit_pounce_command_201621 = _command(
    201621, 'Spirit Pounce',
    [_direct(kits.command_potency(1000, 'II', ferocity=True, single_target=True))],
    3942, 67,
    'Pounce on the target, causing {pot1} Physical damage.',
    notes='hunter-pet-families F1: Spirit Beast II, 1000 x0.65 = 650 Physical. Visual 3942 (Pounce 9005), icon 67 '
          '(Spirit Wolf).'
          + kits.ruling_24_note('Ferocity', kits.command_potency(1000, 'II')),
)

eternal_guardian_rebirth_202017 = spell(
    id=202017,
    name='Eternal Guardian',
    school=School.NATURE,
    attributes=0x10000,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=40.0,
    effects=[
        Effect(type=_EFFECT_RESURRECT, base_points=29),
    ],
    spell_icon_id=24,
    notes='hunter-pet-families F1: the hidden Rebirth of Eternal Guardian (ruling 8, FE 2). Cast by the hunter (not '
          'the pet) with TRIGGERED_FULL_MASK from spell_hun_pet_eternal_guardian on the dead raid member the hunter '
          'has selected. eff0 RESURRECT (18): 30% health and mana, a scaling percent rather than Rebirth 20484\'s flat '
          'RESURRECT_NEW; no TargetA, Targets 0x8000 (CORPSE_ALLY: an unreleased dead player is a unit target, '
          'IsAllowingDeadTarget). Rebirth\'s AttributesEx 0x20000 (NO_AUTOCAST_AI) and AttributesEx3 0x10 (no res '
          'timer), plus SUPPRESS_CASTER_PROCS. Family 0. 40 yd, the range the script checks. Visual 344 / icon 24 '
          'from Rebirth.',
    raw_overrides={'EquippedItemClass': -1, 'SpellLevel': ETERNAL_GUARDIAN_LEVEL, 'Targets': 0x8000,
                   'AttributesEx': 0x20000, 'AttributesEx3': 0x10 | _SUPPRESS_CASTER_PROCS, 'SpellVisualID_1': 344,
                   'CastingTimeIndex': 1,
                   'Description_Lang_enUS': 'Returns the spirit to the body, restoring $s1% of health and mana.'},
)

eternal_guardian_201761 = _utility(
    201761, 'Eternal Guardian', ETERNAL_GUARDIAN_LEVEL,
    [Effect(type=EffectType.DUMMY, implicit_target_a=1)],
    24, 344,
    'Your pet calls on the spirits to bring your selected party or raid member back to life with $202017s1% health '
    'and mana. The target must be dead and must not have released its spirit; usable in combat. Select the target, '
    'then use this ability.',
    school=School.NATURE, cooldown_ms=600000, mobility=False, RangeIndex=1, AttributesEx=_ATTR1_NO_AUTOCAST_AI,
    notes='hunter-pet-families F1: Spirit Beast slot 2 (rare), manual. Self-target DUMMY (no corpse targeting from the '
          'pet bar, FE 2): spell_hun_pet_eternal_guardian checks the hunter\'s selection (a dead player in the '
          'hunter\'s group, not released, within $202017r yards of the hunter and in line of sight, no res pending) '
          'and makes the hunter cast 202017 on it. 10 min on the pet spell (ruling 8, saved with the pet). d1 b28 '
          'only (ruling 10). Visual 344 / icon 24 from Rebirth 20484.',
)

_SPIRIT_MEND_MS = 10000
spirit_mend_201994 = _utility(
    201994, 'Spirit Mend', SPIRIT_MEND_LEVEL,
    [Effect(type=EffectType.APPLY_AURA, ap_potency=_dot_rate(150, _SPIRIT_MEND_MS), potency_kind='heal_periodic',
            implicit_target_a=_TARGET_UNIT_CASTER_AREA_RAID, apply_aura=AuraType.PERIODIC_HEAL, amplitude=2000,
            radius_yards=40.0)],
    1879, 280,
    'Your pet mends the spirits of all party and raid members within $a1 yards, healing them for {pot1.total} over '
    '$d.',
    school=School.NATURE, cooldown_ms=60000, duration_ms=_SPIRIT_MEND_MS, defense=1, prevention=1, RangeIndex=1,
    pet_owner_scaling=_PET_SCALING,
    AuraDescription_Lang_enUS='Healing over time.',
    notes='hunter-pet-families F1: Spirit Beast slot 3, manual. PERIODIC_HEAL on the raid within 40 yd of the pet '
          '(TargetA 56, ruling 7), 150 potency each over 10 s (rate 22.5, 2 s ticks), from the pet\'s AP '
          '(pet_owner_scaling). DefenseType 1 (custom-spells.md). 1 min. Visual 280 / icon 1879 from Spirit Mend '
          '42025.',
)


# =====================================================================================================================
# Command display passives 202109-202124 (command order, the C++ COMMAND_DISPLAYS pairs)
# =====================================================================================================================

rend_flesh_display_202109 = _display(
    rend_flesh_command_201606, 'I', 500,
    'Rend the target for ' + pot_text(rend_flesh_command_201606) + ' Physical damage and an additional '
    + pot_text(rend_flesh_command_201606, effect=2, variant='total') + ' Physical damage over $201606d.',
    display_id=202109,
)
carrion_feast_display_202110 = _display(
    carrion_feast_command_201607, 'II', 116,
    'Feast on the target, causing ' + pot_text(carrion_feast_command_201607) + ' Physical damage.' + _EXECUTE_TEXT,
    display_id=202110,
)
tendon_rip_display_202111 = _display(
    tendon_rip_command_201608, 'I', 138,
    "Rip the target's tendons, causing " + pot_text(tendon_rip_command_201608) + ' Physical damage and reducing its '
    'movement speed by ${$201608m2*-1}% for $201608d.',
    display_id=202111,
)
cackling_frenzy_display_202112 = _display(
    cackling_frenzy_command_201609, 'II', 1565,
    _multi_hit_text('Bite', _CACKLING_FRENZY_HITS, pot_text(cackling_frenzy_command_201609), 'bite'),
    display_id=202112,
)
leaping_kick_display_202113 = _display(
    leaping_kick_command_201610, 'I', 246,
    'Leap to the target and kick it for ' + pot_text(leaping_kick_command_201610, effect=2) + ' Physical damage.',
    display_id=202113,
)
stampeding_kick_display_202114 = _display(
    stampeding_kick_command_201611, 'II', 1587,
    'Kick the target with great force, causing ' + pot_text(stampeding_kick_command_201611) + ' Physical damage.',
    display_id=202114,
)
serenity_dust_display_202115 = _display(
    serenity_dust_command_201612, 'I', 1714,
    'Shake dust over the target, causing ' + pot_text(serenity_dust_command_201612) + ' Physical damage.',
    display_id=202115,
)
dazzling_wings_display_202116 = _display(
    dazzling_wings_command_201613, 'II', 1618,
    'Beat dazzling wings at the target and all enemies in a cone in front of your pet, causing '
    + pot_text(dazzling_wings_command_201613) + ' Physical damage.' + _FALLOFF_TEXT,
    display_id=202116,
)
sting_display_202117 = _display(
    sting_command_201614, 'I', 110,
    'Sting the target for ' + pot_text(sting_command_201614) + ' Nature damage and poison it for an additional '
    + pot_text(sting_command_201614, effect=2, variant='total') + ' Nature damage over $201614d.',
    display_id=202117,
)
swarm_display_202118 = _display(
    swarm_command_201615, 'II', 1771,
    _multi_hit_text('Sting', _SWARM_HITS, pot_text(swarm_command_201615), 'sting'),
    display_id=202118,
)
monstrous_bite_display_202119 = _display(
    monstrous_bite_command_201616, 'I', 599,
    'Bite the target, causing ' + pot_text(monstrous_bite_command_201616) + ' Physical damage.',
    display_id=202119,
)
primal_rampage_display_202120 = _display(
    primal_rampage_command_201617, 'II', 2006,
    'Maul the target in a primal rage, causing ' + pot_text(primal_rampage_command_201617) + ' Physical damage.',
    display_id=202120,
)
lava_breath_display_202121 = _display(
    lava_breath_command_201618, 'I', 1197,
    'Breathe lava at the target and all enemies in a cone in front of your pet, causing '
    + pot_text(lava_breath_command_201618) + ' Fire damage and reducing their movement speed by ${$201618m2*-1}% for '
    '$201618d.' + _FALLOFF_TEXT,
    display_id=202121,
)
twin_bite_display_202122 = _display(
    twin_bite_command_201619, 'II', 2108,
    'Bite the target twice, each bite causing ' + pot_text(twin_bite_command_201619) + ' Physical damage.',
    display_id=202122,
)
spirit_strike_display_202123 = _display(
    spirit_strike_command_201620, 'I', 225,
    'Strike the target with spirit energy, causing ' + pot_text(spirit_strike_command_201620) + ' Nature damage.',
    display_id=202123,
)
spirit_pounce_display_202124 = _display(
    spirit_pounce_command_201621, 'II', 67,
    'Pounce on the target, causing ' + pot_text(spirit_pounce_command_201621) + ' Physical damage.',
    display_id=202124,
)


# =====================================================================================================================
# SkillLineAbility rows (AcquireMethod 2, ClassMask 0): slot 2 then slot 3 per family, 30556-30559 then 30606-30617
# =====================================================================================================================

FEROCITY_F1_SLA_ROWS = (
    (30556, 213, demoralizing_screech_201754.id), (30557, 213, scavenge_201987.id),           # Carrion Bird
    (30558, 654, cackling_howl_201755.id), (30559, 654, infected_bite_201988.id),             # Hyena
    (30606, 218, dust_cloud_201756.id), (30607, 218, long_stride_201989.id),                  # Tallstrider
    (30608, 775, moonglow_dust_201757.id), (30609, 775, healing_dust_201990.id),              # Moth
    (30610, 785, venomous_sting_201758.id), (30611, 785, paralytic_sting_201991.id),          # Wasp
    (30612, 781, primal_roar_201759.id), (30613, 781, earthshaking_stomp_201992.id),          # Devilsaur
    (30614, 787, ancient_hysteria_201760.id), (30615, 787, molten_hide_201993.id),            # Core Hound
    (30616, 788, eternal_guardian_201761.id), (30617, 788, spirit_mend_201994.id),            # Spirit Beast
)
assert sorted(r[0] for r in FEROCITY_F1_SLA_ROWS) == [*range(30556, 30560), *range(30606, 30618)]
for _sla_id, _line, _spell_id in FEROCITY_F1_SLA_ROWS:
    skill_line_ability(id=_sla_id, skill_line=_line, spell_id=_spell_id, class_mask=0, acquire_method=2)


# =====================================================================================================================
# Spell groups (stock groups, DI §4.1; ruling 7: one category, the highest / same-effect rule of the group)
# =====================================================================================================================

spell_group(1062, demoralizing_screech_201754)   # AP Debuffs (rule 4)
spell_group(1022, cackling_howl_201755)          # Melee Haste Buffs (rule 3)
spell_group(1060, dust_cloud_201756)             # Hit Chance Debuffs (rule 3)
spell_group(1105, moonglow_dust_201757)          # MP5 Buffs (rule 3)
spell_group(1058, venomous_sting_201758)         # crit taken, "Poisons" (rule 3)
spell_group(1056, primal_roar_201759)            # Damage Done Buffs (rule 3)
spell_group(1061, infected_bite_201988)          # Healing Taken Debuffs (rule 4)


# =====================================================================================================================
# Script bindings (PLAN §5.2). Positive keys only (L7).
# =====================================================================================================================

scripted_by(carrion_feast_command_201607, 'spell_hun_command_execute')
scripted_by(cackling_frenzy_command_201609, 'spell_hun_command_multihit')
scripted_by(swarm_command_201615, 'spell_hun_command_multihit')
scripted_by(twin_bite_command_201619, 'spell_hun_command_multihit')     # twohit: one follow-up (review MINOR 1)
scripted_by(dazzling_wings_command_201613, 'spell_hun_command_aoe_falloff')
scripted_by(lava_breath_command_201618, 'spell_hun_command_aoe_falloff')
scripted_by(paralytic_sting_201991, 'spell_hun_pet_control_boss_filter')
scripted_by(earthshaking_stomp_201992, 'spell_hun_pet_control_boss_filter')
scripted_by(scavenge_201987, 'spell_hun_pet_scavenge')
scripted_by(eternal_guardian_201761, 'spell_hun_pet_eternal_guardian')
scripted_by(ancient_hysteria_201760, 'spell_sha_bloodlust')

# Every pet-cast spell above keeps the pet bit: the lint (c) contract of _masks.py.
assert m.PET_ABILITY == 0x10000000
