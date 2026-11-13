"""
Hunter pet families F2 (.agents/plans/hunter-pet-families/hunter-pet-families.PLAN.md §3.2, §4.1, §5;
hunter-pet-families.F2.HANDOFF.md): the 9 Tenacity families without a kit get their full kit. Per family, in the §3.2
table order (Boar, Crocolisk, Turtle, Crab, Scorpid, Gorilla, Warp Stalker, Worm, Rhino): Command I and II, their two
"Command I/II: <ability>" display passives, a slot 2 group effect and a slot 3 utility, and their two
SkillLineAbility rows (AcquireMethod 2, learned at the pet level = SpellLevel). Bear is done (F0).

Ids (PLAN §4.1, the F2 column): commands 201622-201639 (Command I then II per family), command helpers 201665-201667
(Gore's debuff, Pincer Crush's root, Burrow Attack's pulse), displays 202125-202142 (command order), slot 2
201762-201770, slot 3 201995-202003, SkillLineAbility 30618-30635 (slot 2 then slot 3 per family), spell_group 1232
(the new "raid damage taken" group, ruling 7). 201668-201669 and 202025-202031 stay free.

Rules (the F1 file's, hunter_pet_ferocity.py):
- Potency (ruling 1): every Command I is kits.command_potency(x, 'I'), every Command II kits.command_potency(x, 'II')
  of the §3.2 number (a DoT's or a pulse's number is its total; a channel's too). Ruling 23b (user 2026-11-13): every
  Tenacity command and damage helper also takes kits.TENACITY_COMMAND_SCALE (x0.80), passed as `tenacity=True`; the
  §3.2 number stays the first argument. The `notes` below quote the pre-ruling-23b numbers (x0.84 / x0.65 of §3.2);
  `_command` appends kits.RULING_23B_NOTE to each command note, and the Burrow Attack pulse note carries it too.
- Every slot 2 / slot 3 utility carries d1 b28 + b29 (kits.utility_raw), except Earthen Bulwark (ruling 10: b28 only,
  mobility=False, AttributesEx NO_AUTOCAST_AI). Group effects use TargetA 56 (ruling 7). Earthen Bulwark and every
  slot 3 are manual; the C++ kit row sets PET_KIT_GROUP_AUTOCAST for the other eight slot 2 spells.
- Unlock levels: the class equivalent's level on this server (trainer_spell, or the talent's row), never below 10 (a
  hunter tames at 10; a lower SpellLevel would only shift the per-level math); 30 where nothing matches (F0's Tail
  Sweep rule).
- Scripts (PLAN §5.2), bound below: gore (Gore's debuff, read by Hunter::GetPetFamilyTakenMultiplier from the
  HunterUnitScript damage hooks; no binding), refresh (Deadly Sting), pulse (Burrow Attack), absorb (Bubble Shield),
  boss (Boar Charge, Pincer Crush's root, Disarming Pincer), falloff (Tusk Sweep, Shell Spin, Bubble Burst,
  Thunderstomp, Burrow Attack's pulse, Stampede).
- A command with a control rider keeps the rider in its own helper spell (Pincer Crush -> 201666), so the boss filter
  refuses the root on a boss and the damage still lands (F1 review NIT 7).

Imports only helpers and constants from the sibling modules (never a spell object: lib/dsl/registry.py
_collect_var_names keeps the first module's name for an id).
"""

from lib.dsl import AuraType, Effect, EffectType, School
from lib.dsl.registry import pot_text, scripted_by, skill_line_ability, spell, spell_group, spell_group_rule
from . import _masks as m
from . import _pet_kits as kits
from .hunter_bm_spells import COMMAND_AOE_FALLOFF_PCT, _cmd_raw, _direct, _display, _dot, _PET_SCALING

# ---- unlock levels (pet level = SpellLevel; see the module docstring) ----
WAR_GRUNT_LEVEL = 40                # Trueshot Aura 19506 (BaseLevel 40, the hunter's own AP% aura)
BOAR_CHARGE_LEVEL = 30              # the stun: Intimidation 19577 (trainer 30), Paralytic Sting's level (F1)
ANKLE_CRACK_LEVEL = 10              # Thunder Clap 6343 (trainer 6), raised to 10
BAD_ATTITUDE_LEVEL = 10             # Thorns 467 (trainer 6), raised to 10
HARDENED_SHELL_LEVEL = 10           # Devotion Aura 465 (trainer 1), raised to 10
SHELL_SHIELD_LEVEL = 28             # Shield Wall 871 (trainer 28)
CRIPPLING_PINCH_LEVEL = 10          # Thunder Clap 6343 (trainer 6), raised to 10
BUBBLE_SHIELD_LEVEL = 10            # Power Word: Shield 17 (trainer 6), raised to 10
SCORPID_POISON_LEVEL = 15           # Heart of the Crusader (talent tier 2 = 15), Venomous Sting's level (F1)
DISARMING_PINCER_LEVEL = 18         # Disarm 676 (trainer 18)
PRIMAL_MIGHT_LEVEL = 10             # Roar of Courage 201715 / Strength of Earth (10)
PUMMEL_LEVEL = 16                   # Pummel 6552 (trainer 16)
TIME_WARP_LEVEL = 26                # Curse of Tongues 1714 (trainer 26), Sticky Webbing's level (F0)
WARP_LEVEL = 10                     # Evasion 5277 (trainer 8), raised to 10
EARTHEN_BULWARK_LEVEL = 30          # no class equivalent (a raid-wide cut): F0's Tail Sweep rule
BURROW_LEVEL = 30                   # Feign Death 5384 (trainer 30), the threat drop
HORN_OF_THE_HERD_LEVEL = 20         # Blessing of Kings 20217 (trainer 20)
LEAD_THE_HERD_LEVEL = 40            # Aspect of the Pack 13159 (trainer 40)

# Aura and effect types the DSL enum doesn't name (SpellAuraDefines.h / SharedDefines.h).
_AURA_DAMAGE_SHIELD = 15
_AURA_MOD_RESISTANCE = 22
_AURA_SCHOOL_IMMUNITY = 39
_AURA_MOD_RANGED_ATTACK_POWER_PCT = 167
_EFFECT_TELEPORT_UNITS = 5
_EFFECT_JUMP = 41
_EFFECT_SANCTUARY = 79
_MECHANIC_DISARM = 3
_MECHANIC_ROOT = 7
_MECHANIC_STUN = 12
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_UNIT_SRC_AREA_ENEMY = 15
_TARGET_UNIT_DEST_AREA_ENEMY = 16
_TARGET_SRC_CASTER = 22
_TARGET_UNIT_MASTER = 27
_TARGET_DEST_TARGET_ENEMY = 53
_TARGET_UNIT_CASTER_AREA_RAID = 56
_TARGET_DEST_TARGET_BACK = 65
_TARGET_UNIT_CONE_ENEMY = 104

_ATTR1_IS_CHANNELED = 0x4           # AttributesEx: a channel (SpellInfo::IsChanneled; the dispatcher keeps facing)
_ATTR1_NO_AUTOCAST_AI = 0x20000     # AttributesEx: the pet AI never autocasts it (F1's manual raid cooldowns)
_ATTR2_IGNORE_LOS = 0x4             # AttributesEx2 (Kill Command's teleport 201704, Shadowstep)
_SUPPRESS_CASTER_PROCS = 0x10000    # AttributesEx3: a helper procs nothing of its own
_ATTR3_DOT_STACKING_RULE = 0x80     # AttributesEx3: one copy per caster (SPELL_ATTR3_DOT_STACKING_RULE)
_SCHOOL_MASK_ALL = 127
_SCHOOL_MASK_PHYSICAL = 1
_GROUP_BUFF_RADIUS_YD = 100.0       # Roar of Courage / Furious Howl
_AREA_RADIUS_YD = 8.0               # every Tenacity AoE command (the F1 cones' radius)
_SPLASH_TAIL = '% damage.'
_FALLOFF_TEXT = f" Enemies other than the target take {COMMAND_AOE_FALLOFF_PCT['value']}{_SPLASH_TAIL}"

SPELL_GROUP_RAID_DAMAGE_TAKEN = 1232   # PLAN §4.1 / ruling 7: Earthen Bulwark now, F3's Gale Barrier later


def _command(spell_id, name, effects, visual, icon, description, *, school=School.NORMAL, range_yards=5.0,
             duration_ms=None, melee_range_index=True, notes='', **raw):
    """A commanded pet spell (the F1 template): pet-cast, instant, no cost / cooldown / GCD, d1 b28 + d2 b22,
    SpellLevel 1, melee DmgClass. Melee by default (RangeIndex 2, the pet's melee reach). `raw` wins."""
    raw_overrides = {**_cmd_raw(visual), 'SpellIconID': icon, 'Description_Lang_enUS': description, **raw}
    if melee_range_index:
        raw_overrides['RangeIndex'] = 2
    kwargs = {'duration_ms': duration_ms} if duration_ms is not None else {}
    return spell(
        id=spell_id, name=name, school=school, attributes=0x50010, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=range_yards, effects=effects,
        pet_owner_scaling=_PET_SCALING, notes=notes + kits.RULING_23B_NOTE,
        raw_overrides=raw_overrides, **kwargs,
    )


def _helper(spell_id, name, effects, icon, *, duration_ms, aura_description, notes, attributes_ex3=0):
    """A command's control or debuff rider: family 0, no carrier (it deals no damage), cast on the command's target
    by the command's TRIGGER_SPELL (so only on a hit), SUPPRESS_CASTER_PROCS, 10 yd (a triggered cast is range-checked
    strictly)."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=10.0, duration_ms=duration_ms, effects=effects, spell_icon_id=icon,
        notes=notes,
        raw_overrides={'EquippedItemClass': -1, 'SpellLevel': 1, 'BaseLevel': 1, 'CastingTimeIndex': 1,
                       'AttributesEx3': _SUPPRESS_CASTER_PROCS | attributes_ex3,
                       'AuraDescription_Lang_enUS': aura_description},
    )


def _dot_rate(total, duration_ms):
    """A periodic potency is a rate per 1.5 s, so the total over `duration_ms` is rate x duration / 1500."""
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


def _enemy_aura(aura, base_points, misc_value=0, mechanic=0):
    """One effect on the enemy target (the Tear Armor / Venomous Sting shape)."""
    return Effect(type=EffectType.APPLY_AURA, base_points=base_points, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
                  apply_aura=aura, misc_value=misc_value, mechanic=mechanic)


def _self_aura(aura, base_points, misc_value=0):
    return Effect(type=EffectType.APPLY_AURA, base_points=base_points, implicit_target_a=1, apply_aura=aura,
                  misc_value=misc_value)


def _cone(potency):
    """The F1 cone shape (Dazzling Wings, Lava Breath): cone damage (TargetA 104, 8 yd) and a DUMMY at the target that
    keeps the command's target as the spell's explicit target, the primary of spell_hun_command_aoe_falloff (which
    also puts a large primary back into the cone, F1 review MAJOR 1)."""
    return [Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=potency, potency_kind='direct',
                   implicit_target_a=_TARGET_UNIT_CONE_ENEMY, radius_yards=_AREA_RADIUS_YD),
            Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)]


def _around_pet(potency):
    """Damage to the enemies within 8 yd of the pet (TargetA 22 / B 15) and the F1 DUMMY anchor at the target, the
    primary of spell_hun_command_aoe_falloff (which adds the primary back when the area misses it)."""
    return [Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=potency, potency_kind='direct',
                   implicit_target_a=_TARGET_SRC_CASTER, implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY,
                   radius_yards=_AREA_RADIUS_YD),
            Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)]


def _jump_strike(potency):
    """The Lunge 201720 / Leaping Kick 201610 shape: eff0 JUMP to the target, eff1 the hit."""
    return [Effect(type=_EFFECT_JUMP, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY), _direct(potency)]


# =====================================================================================================================
# Boar (family 5, skill line 211, basic Bite)
# =====================================================================================================================

_GORE_MS = 30000
gore_debuff_201665 = _helper(
    201665, 'Gore',
    [_enemy_aura(AuraType.DUMMY, 3)],
    1578, duration_ms=_GORE_MS, attributes_ex3=_ATTR3_DOT_STACKING_RULE,
    aura_description='Takes $s1% more Physical damage from the hunter and pet that gored it.',
    notes='hunter-pet-families F2: Gore\'s owner-only debuff (ruling 9, PLAN §5.2 `gore`). DUMMY 4% on the target for '
          '30 s, cast by the pet through Gore 201622\'s TRIGGER_SPELL (so only on a hit). Hunter::'
          'GetPetFamilyTakenMultiplier reads it from the HunterUnitScript spell, melee and periodic hooks: +4% '
          'Physical damage taken from its caster\'s owner (the hunter) and that hunter\'s current pet only. '
          'AttributesEx3 0x80 (DOT_STACKING_RULE, F2 review MINOR 1): one copy per caster, so a second hunter\'s '
          'Boar never removes the first one\'s. Its own id so a sim can switch its share off. Icon 1578 (Boar).',
)

gore_command_201622 = _command(
    201622, 'Gore',
    [_direct(kits.command_potency(650, 'I', tenacity=True)),
     Effect(type=EffectType.TRIGGER_SPELL, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
            trigger_spell=gore_debuff_201665.id)],
    6762, 1578,
    'Gore the target, causing {pot1} Physical damage. For $201665d the target takes $201665s1% more Physical damage '
    'from you and your pet.',
    notes='hunter-pet-families F2: Boar I. eff0 650 x0.84 = 546 Physical, eff1 TRIGGER_SPELL the owner-only debuff '
          '201665 (+4% Physical taken from the hunter and pet, 30 s; ruling 9: priced into this command by the sim). '
          'Visual 6762 / icon 1578 from Gore 35290.',
)

tusk_sweep_command_201623 = _command(
    201623, 'Tusk Sweep',
    _cone(kits.command_potency(800, 'II', tenacity=True)),
    189, 496,
    'Sweep your tusks at the target and all enemies in a cone in front of your pet, causing {pot1} Physical damage.'
    + _FALLOFF_TEXT,
    notes='hunter-pet-families F2: Boar II, 800 x0.65 = 520 Physical, cone (TargetA 104) 8 yd + DUMMY anchor (the F1 '
          'cone shape), spell_hun_command_aoe_falloff. Visual 189 (Swipe), icon 496 (Druid Swipe).',
)

war_grunt_201762 = _utility(
    201762, 'War Grunt', WAR_GRUNT_LEVEL,
    [_raid_aura(AuraType.MOD_ATTACK_POWER_PCT, 4), _raid_aura(_AURA_MOD_RANGED_ATTACK_POWER_PCT, 4)],
    282, 7299,
    'Your pet grunts, increasing the melee and ranged attack power of all party and raid members by $s1% for $d. '
    "Does not stack with Trueshot Aura or Abomination's Might.",
    cooldown_ms=40000, duration_ms=120000, RangeIndex=1,
    AuraDescription_Lang_enUS='Attack power increased by $s1%.',
    notes='hunter-pet-families F2: Boar slot 2, autocast. Aura 166 + 167 +5% (ruling 22: Trueshot Aura\'s category at '
          'the PLAN\'s 5%, the Abomination\'s Might value), raid 100 yd, 2 min, 40 s cooldown (Roar of Courage shape). '
          'Group 1029 Percentage AP Buffs (rule 1). Visual 7299 (Furious Howl), icon 282 (War Cry).',
)

boar_charge_201995 = _utility(
    201995, 'Boar Charge', BOAR_CHARGE_LEVEL,
    [Effect(type=_EFFECT_JUMP, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
     _enemy_aura(AuraType.MOD_STUN, 0, mechanic=_MECHANIC_STUN)],
    1559, 519,
    'Your pet charges the target, stunning it for $d. Does not work on bosses.',
    cooldown_ms=60000, duration_ms=2000, range_yards=25.0, enemy_target=True, defense=2, FacingCasterFlags=1,
    AuraDescription_Lang_enUS='Stunned.',
    notes='hunter-pet-families F2: Boar slot 3, manual. eff0 JUMP to the target (the Lunge / Leaping Kick path; the '
          'stock pet Charge 61685 has an 8 yd minimum range), eff1 MOD_STUN 2 s, Mechanic 12, 25 yd, 1 min. '
          'spell_hun_pet_control_boss_filter refuses a world or dungeon boss (ruling 3). Visual 519 / icon 1559 from '
          'Charge 61685.',
)


# =====================================================================================================================
# Crocolisk (family 6, skill line 212, basic Bite)
# =====================================================================================================================

snap_command_201624 = _command(
    201624, 'Snap',
    [_direct(kits.command_potency(600, 'I', tenacity=True))],
    376, 1680,
    'Snap at the target, causing {pot1} Physical damage.',
    notes='hunter-pet-families F2: Crocolisk I, 600 x0.84 = 504 Physical. Visual 376 (Bite), icon 1680 (Ferocious '
          'Bite).',
)

_DEATH_ROLL_MS = 3000
death_roll_command_201625 = _command(
    201625, 'Death Roll',
    [_dot(_dot_rate(kits.command_potency(1300, 'II', tenacity=True), _DEATH_ROLL_MS), 1000,
          implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    5287, 1581,
    'Seize the target and roll, causing {pot1.total} Physical damage over $d. Your pet channels for the whole roll.',
    duration_ms=_DEATH_ROLL_MS, AttributesEx=0x200 | _ATTR1_IS_CHANNELED, ChannelInterruptFlags=0,
    notes='hunter-pet-families F2: Crocolisk II, 1300 x0.65 = 845 Physical over a 3 s channel (rule 16: the +30% '
          'channel bonus is in the 1300), PERIODIC_DAMAGE on the target, 1 s ticks (rate 422.5 per 1.5 s). '
          'AttributesEx 0x4 (channeled): Hunter::GetCommandCastFlags casts it without TRIGGERED_IGNORE_SET_FACING, so '
          'the pet keeps facing; the pet\'s melee stops while it channels (FE 10a). No ChannelInterruptFlags (stuns '
          'and interrupts still break it). Visual 5287 (Bad Attitude), icon 1581 (Crocolisk).',
)

ankle_crack_201763 = _utility(
    201763, 'Ankle Crack', ANKLE_CRACK_LEVEL,
    [_enemy_aura(AuraType.MOD_MELEE_HASTE, -11)],
    96, 145,
    "Your pet cracks the target's ankle, reducing its attack speed by ${$m1*-1}% for $d. Does not stack with Thunder "
    'Clap or Crippling Pinch.',
    cooldown_ms=10000, duration_ms=30000, range_yards=5.0, enemy_target=True, defense=2, RangeIndex=2,
    FacingCasterFlags=1,
    AuraDescription_Lang_enUS='Attack speed reduced.',
    notes='hunter-pet-families F2: Crocolisk slot 2, autocast. Aura 138 -10% attack speed (Thunder Clap 6343 live), '
          'single enemy, melee, 30 s, 10 s cooldown (Tear Armor shape). Group 1059 Attack Speed Debuffs (rule 3). '
          'Visual 145 (Thunder Clap), icon 96 (Cripple).',
)

bad_attitude_201996 = _utility(
    201996, 'Bad Attitude', BAD_ATTITUDE_LEVEL,
    [Effect(type=EffectType.APPLY_AURA, base_points=15, points_per_level=1.03797, implicit_target_a=1,
            apply_aura=_AURA_DAMAGE_SHIELD,
            potency_excluded='damage shield: the engine applies SpellDamageBonusDone at amount calc '
                             '(SpellAuraEffects.cpp:573) and again per hit (Unit.cpp:2236), so an AP coefficient '
                             'would double-dip')],
    53, 5287,
    'Your pet bristles for $d. Each melee attack against it causes the attacker $s1 Physical damage.',
    cooldown_ms=60000, duration_ms=15000, RangeIndex=1, MaxLevel=80,
    AuraDescription_Lang_enUS='Melee attackers take $s1 Physical damage.',
    notes='hunter-pet-families F2: Crocolisk slot 3, manual. Aura 15 DAMAGE_SHIELD on the pet, stock Bad Attitude '
          '50433\'s numbers moved to SpellLevel 10 (bp 6 + 9 x 1.038 = 15, 1.038/level: 67 per hit at 60). Not on '
          'potency: the generator refuses potency on a damage shield (S4 lint), so it keeps the stock flat values '
          '(FE 9d: "tiny"). 15 s, 1 min. Visual 5287 from 50433, icon 53 (Thorns).',
)


# =====================================================================================================================
# Turtle (family 21, skill line 251, basic Bite)
# =====================================================================================================================

snapping_bite_command_201626 = _command(
    201626, 'Snapping Bite',
    [_direct(kits.command_potency(800, 'I', tenacity=True))],
    376, 1680,
    'Snap your jaws on the target, causing {pot1} Physical damage.',
    notes='hunter-pet-families F2: Turtle I, 800 x0.84 = 672 Physical (800 = 600 + the AoE shift off Shell Spin, rule '
          '15). Visual 376 (Bite), icon 1680 (Ferocious Bite).',
)

shell_spin_command_201627 = _command(
    201627, 'Shell Spin',
    _around_pet(kits.command_potency(800, 'II', tenacity=True)),
    7425, 347,
    'Spin in your shell, causing {pot1} Physical damage to the target and all enemies within $a1 yards of your pet.'
    + _FALLOFF_TEXT,
    notes='hunter-pet-families F2: Turtle II, 800 x0.65 = 520 Physical to the enemies within 8 yd of the pet (TargetA '
          '22 / B 15) + DUMMY anchor at the target, spell_hun_command_aoe_falloff. Visual 7425 (Shell Shield), icon '
          '347 '
          '(Shell).',
)

hardened_shell_201764 = _utility(
    201764, 'Hardened Shell', HARDENED_SHELL_LEVEL,
    [_raid_aura(_AURA_MOD_RESISTANCE, 185, misc_value=_SCHOOL_MASK_PHYSICAL, points_per_level=14.557)],
    2553, 7425,
    'Your pet hardens its shell, increasing the armor of all party and raid members by $s1 for $d. Does not stack '
    'with Devotion Aura or Earth Attunement.',
    cooldown_ms=40000, duration_ms=120000, RangeIndex=1, MaxLevel=80,
    AuraDescription_Lang_enUS='Armor increased by $s1.',
    notes='hunter-pet-families F2: Turtle slot 2, autocast. Aura 22 armor, Devotion Aura 465\'s values moved to '
          'SpellLevel 10 (bp 54 + 9 x 14.557 = 185, 14.557/level: 914 at 60, as Devotion Aura), raid 100 yd, 2 min, '
          '40 s cooldown. Group 1086 Armor Buffs (rule 4). Visual 7425 (Shell Shield), icon 2553 (Shell).',
)

shell_shield_201997 = _utility(
    201997, 'Shell Shield', SHELL_SHIELD_LEVEL,
    [_self_aura(AuraType.MOD_DAMAGE_PERCENT_TAKEN, -51, misc_value=_SCHOOL_MASK_ALL)],
    1588, 7425,
    'Your pet withdraws into its shell, reducing all damage it takes by ${$m1*-1}% for $d.',
    cooldown_ms=60000, duration_ms=12000, RangeIndex=1,
    AuraDescription_Lang_enUS='Damage taken reduced.',
    notes='hunter-pet-families F2: Turtle slot 3, manual. Aura 87 -50% all schools on the pet, 12 s, 1 min (stock '
          'Shell Shield 26064, FE 9c). Visual 7425 / icon 1588 from 26064.',
)


# =====================================================================================================================
# Crab (family 8, skill line 214, basic Claw)
# =====================================================================================================================

pincer_crush_root_201666 = _helper(
    201666, 'Pincer Crush',
    [_enemy_aura(AuraType.MOD_ROOT, 0, mechanic=_MECHANIC_ROOT)],
    2679, duration_ms=2000,
    aura_description='Rooted.',
    notes='hunter-pet-families F2: Pincer Crush\'s root (free, ruling 3). MOD_ROOT 2 s, Mechanic 7, cast by the pet '
          'through 201628\'s TRIGGER_SPELL. Its own spell so spell_hun_pet_control_boss_filter refuses it on a boss '
          'while the command\'s damage still lands (F1 review NIT 7). Icon 2679 (Pin).',
)

pincer_crush_command_201628 = _command(
    201628, 'Pincer Crush',
    [_direct(kits.command_potency(800, 'I', tenacity=True)),
     Effect(type=EffectType.TRIGGER_SPELL, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
            trigger_spell=pincer_crush_root_201666.id)],
    5287, 2679,
    'Crush the target in your pincers, causing {pot1} Physical damage and rooting it for $201666d. The root does not '
    'work on bosses.',
    notes='hunter-pet-families F2: Crab I. eff0 800 x0.84 = 672 Physical, eff1 TRIGGER_SPELL the 2 s root 201666 '
          '(boss-filtered on its own). Visual 5287 / icon 2679 from Pin 50245.',
)

bubble_burst_command_201629 = _command(
    201629, 'Bubble Burst',
    [Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=kits.command_potency(800, 'II', tenacity=True),
            potency_kind='direct', implicit_target_a=_TARGET_DEST_TARGET_ENEMY,
            implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY, radius_yards=_AREA_RADIUS_YD)],
    17, 193,
    'Burst a bubble at the target, causing {pot1} Frost damage to it and all enemies within $a1 yards of it.'
    + _FALLOFF_TEXT,
    school=School.FROST,
    notes='hunter-pet-families F2: Crab II, 800 x0.65 = 520 Frost to the enemies within 8 yd of the target (TargetA '
          '53 / B 16: the target is the area\'s center and stays the explicit target, no anchor needed), '
          'spell_hun_command_aoe_falloff. Visual 17 / icon 193 from Frost Nova 122.',
)

crippling_pinch_201765 = _utility(
    201765, 'Crippling Pinch', CRIPPLING_PINCH_LEVEL,
    [_enemy_aura(AuraType.MOD_MELEE_HASTE, -11)],
    1580, 5287,
    "Your pet pinches the target's limbs, reducing its attack speed by ${$m1*-1}% for $d. Does not stack with Thunder "
    'Clap or Ankle Crack.',
    cooldown_ms=10000, duration_ms=30000, range_yards=5.0, enemy_target=True, defense=2, RangeIndex=2,
    FacingCasterFlags=1,
    AuraDescription_Lang_enUS='Attack speed reduced.',
    notes='hunter-pet-families F2: Crab slot 2, autocast. Ankle Crack 201763\'s shape (aura 138 -10%, Thunder Clap). '
          'Group 1059 (rule 3). Visual 5287 (Pin), icon 1580 (Crab).',
)

bubble_shield_201998 = _utility(
    201998, 'Bubble Shield', BUBBLE_SHIELD_LEVEL,
    [Effect(type=EffectType.APPLY_AURA, ap_potency=300.0, potency_kind='absorb', implicit_target_a=_TARGET_UNIT_MASTER,
            apply_aura=AuraType.SCHOOL_ABSORB, misc_value=_SCHOOL_MASK_ALL)],
    32, 4302,
    'Your pet wraps you in a bubble that absorbs {pot1} damage for $d.',
    school=School.FROST, cooldown_ms=60000, duration_ms=15000, RangeIndex=1, pet_owner_scaling=_PET_SCALING,
    AuraDescription_Lang_enUS='Absorbs damage.',
    notes='hunter-pet-families F2: Crab slot 3, manual. Aura 69 SCHOOL_ABSORB all schools on the hunter (TargetA 27 '
          'MASTER, FE 9f), 300 potency (Healing Dust\'s per-target amount, F1) on the heal scale, 15 s, 1 min. '
          'spell_hun_pet_absorb (PLAN §5.2 `absorb`) adds the generated ap_bonus x the pet\'s attack power (an absorb '
          'gets no engine bonus; pet spell power is 0); F3\'s Swarm Shield reuses it. Visual 4302 / icon 32 from Ice '
          'Barrier 11426.',
)


# =====================================================================================================================
# Scorpid (family 20, skill line 236, basic Claw)
# =====================================================================================================================

_STINGER_MS = 6000
stinger_command_201630 = _command(
    201630, 'Stinger',
    [_direct(kits.command_potency(300, 'I', tenacity=True)),
     _dot(_dot_rate(kits.command_potency(300, 'I', tenacity=True), _STINGER_MS), 2000,
          implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    19, 1585,
    'Sting the target for {pot1} Nature damage and poison it for an additional {pot2.total} Nature damage over $d.',
    school=School.NATURE, duration_ms=_STINGER_MS,
    notes='hunter-pet-families F2: Scorpid I, Nature (one school per spell, F1\'s Sting). eff0 300 x0.84 = 252, eff1 '
          '300 x0.84 = 252 over 6 s (rate 63, 2 s ticks). Visual 19 from Scorpid Poison 24640, icon 1585 (Scorpid).',
)

deadly_sting_command_201631 = _command(
    201631, 'Deadly Sting',
    [_direct(kits.command_potency(1000, 'II', tenacity=True)),
     Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
            trigger_spell=stinger_command_201630.id)],
    19, 1719,
    'Sting the target with a deadly poison, causing {pot1} Nature damage and refreshing your Stinger on it.',
    school=School.NATURE,
    notes='hunter-pet-families F2: Scorpid II, 1000 x0.65 = 650 Nature. eff1 DUMMY naming Stinger 201630 '
          '(TriggerSpell): spell_hun_command_refresh resets the pet\'s Stinger on the target to its full duration '
          '(PLAN §5.2 `refresh`). Visual 19 (Scorpid Poison), icon 1719 (Creature Poison).',
)

scorpid_poison_201766 = _utility(
    201766, 'Scorpid Poison', SCORPID_POISON_LEVEL,
    [_enemy_aura(AuraType.MOD_ATTACKER_SPELL_AND_WEAPON_CRIT_CHANCE, 2)],
    1736, 19,
    'Your pet poisons the target, increasing the chance that attacks and spells against it are critical strikes by '
    '$s1% for $d. Does not stack with Heart of the Crusader, Holy Guidance or Venomous Sting.',
    school=School.NATURE, cooldown_ms=10000, duration_ms=30000, range_yards=5.0, enemy_target=True, defense=2,
    RangeIndex=2, FacingCasterFlags=1,
    AuraDescription_Lang_enUS='Chance to be critically hit increased.',
    notes='hunter-pet-families F2: Scorpid slot 2, autocast. Venomous Sting 201758\'s shape (aura 197 +3% crit taken), '
          'single enemy, melee, 30 s, 10 s cooldown. Group 1058 (rule 3). Visual 19 (Scorpid Poison 24640), icon 1736 '
          '(Creature Poison).',
)

disarming_pincer_201999 = _utility(
    201999, 'Disarming Pincer', DISARMING_PINCER_LEVEL,
    [_enemy_aura(AuraType.MOD_DISARM, 0, mechanic=_MECHANIC_DISARM),
     _enemy_aura(AuraType.MOD_DAMAGE_PERCENT_DONE, -51, misc_value=_SCHOOL_MASK_PHYSICAL, mechanic=_MECHANIC_DISARM)],
    560, 398,
    "Your pet seizes the target's weapon, disarming it and reducing the Physical damage it deals by ${$m2*-1}% for $d. "
    'While disarmed, the target cannot use its weapon abilities. Does not work on bosses.',
    cooldown_ms=60000, duration_ms=6000, range_yards=5.0, enemy_target=True, defense=2, RangeIndex=2,
    FacingCasterFlags=1, Mechanic=_MECHANIC_DISARM,
    AuraDescription_Lang_enUS='Disarmed: cannot use weapon abilities. Physical damage dealt reduced.',
    notes='hunter-pet-families F2: Scorpid slot 3, manual (ruling 2): aura 67 MOD_DISARM for the visual (it does '
          'nothing to a creature\'s white swings, FE 8d, but Spell::CheckItems fails its MELEE / RANGED DmgClass '
          'spells while it lasts: F2 review MINOR 2, kept and stated in the tooltip) + aura 79 -50% Physical damage '
          'done, 6 s, both Mechanic 3 (disarm-immune creatures resist), melee, 1 min. '
          'spell_hun_pet_control_boss_filter refuses a boss (ruling 3). Visual 398 '
          '(Snatch / Disarm), icon 560 (Disarm).',
)


# =====================================================================================================================
# Gorilla (family 9, skill line 215, basic Smack)
# =====================================================================================================================

thunderstomp_command_201632 = _command(
    201632, 'Thunderstomp',
    _around_pet(kits.command_potency(500, 'I', tenacity=True)),
    7429, 148,
    'Stomp the ground, causing {pot1} Physical damage to the target and all enemies within $a1 yards of your pet.'
    + _FALLOFF_TEXT,
    notes='hunter-pet-families F2: Gorilla I, 500 x0.84 = 420 Physical (§3.2 marks no school: F1 decision 2) to the '
          'enemies within 8 yd of the pet + DUMMY anchor, spell_hun_command_aoe_falloff. Visual 7429 / icon 148 from '
          'Thunderstomp 63900.',
)

pound_command_201633 = _command(
    201633, 'Pound',
    [_direct(kits.command_potency(1100, 'II', tenacity=True))],
    166, 473,
    'Pound the target, causing {pot1} Physical damage.',
    notes='hunter-pet-families F2: Gorilla II, 1100 x0.65 = 715 Physical (1100 = 1000 + the AoE shift off '
          'Thunderstomp). Visual 166 (Maul), icon 473 (Bash).',
)

primal_might_201767 = _utility(
    201767, 'Primal Might', PRIMAL_MIGHT_LEVEL,
    [_raid_aura(AuraType.MOD_STAT, 9, misc_value=0, points_per_level=2.0714285714285716),
     _raid_aura(AuraType.MOD_STAT, 9, misc_value=1, points_per_level=2.0714285714285716)],
    1582, 7429,
    'Your pet beats its chest, increasing the Strength and Agility of all party and raid members by $s1 for $d. Does '
    'not stack with Roar of Courage or Horn of Winter.',
    cooldown_ms=40000, duration_ms=120000, RangeIndex=1, MaxLevel=80,
    AuraDescription_Lang_enUS='Increases Strength and Agility by $s1.',
    notes='hunter-pet-families F2: Gorilla slot 2, autocast. Roar of Courage 201715\'s effects (Strength of Earth '
          '8076: bp 9, 2.0714/level from 10 to 80), raid 100 yd, 2 min, 40 s cooldown. Group 1088 Strength and Agility '
          'Buffs (rule 4). Visual 7429 (Thunderstomp), icon 1582 (Gorilla).',
)

pummel_202000 = _utility(
    202000, 'Pummel', PUMMEL_LEVEL,
    [Effect(type=EffectType.INTERRUPT_CAST, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    756, 1023,
    'Your pet pummels the target, interrupting spellcasting and preventing any spell in that school from being cast '
    'for $d.',
    cooldown_ms=30000, duration_ms=4000, range_yards=5.0, enemy_target=True, defense=2, RangeIndex=2,
    FacingCasterFlags=1,
    notes='hunter-pet-families F2: Gorilla slot 3, manual (ruling 10). INTERRUPT_CAST on the target, 4 s lockout '
          '(Pummel 6552), melee, 30 s (stock pet Pummel 26090). Not boss-filtered (ruling 3: interrupts stay stock). '
          'Visual 1023 / icon 756 from Pummel 6552.',
)


# =====================================================================================================================
# Warp Stalker (family 32, skill line 766, basic Bite)
# =====================================================================================================================

warp_strike_command_201634 = _command(
    201634, 'Warp Strike',
    [Effect(type=_EFFECT_TELEPORT_UNITS, die_sides=0, implicit_target_a=1, implicit_target_b=_TARGET_DEST_TARGET_BACK,
            radius_yards=2.0),
     _direct(kits.command_potency(600, 'I', tenacity=True))],
    263, 1499,
    'Blink behind the target and strike it for {pot2} Physical damage.',
    range_yards=25.0, melee_range_index=False, AttributesEx2=_ATTR2_IGNORE_LOS,
    notes='hunter-pet-families F2: Warp Stalker I, one spell (FE 10e): eff0 TELEPORT_UNITS the pet to behind the '
          'target '
          '(TargetA 1 / B 65, radius 2: Kill Command\'s teleport 201704 / Shadowstep), eff1 600 x0.84 = 504 Physical. '
          '25 yd (the jump commands\' reach); AttributesEx2 IGNORE_LOS as 201704 (CheckPetCanAct still checks LoS at '
          'the press). Visual 263 (Warp / Blink), icon 1499 (Blink).',
)

phase_rend_command_201635 = _command(
    201635, 'Phase Rend',
    [_direct(kits.command_potency(1000, 'II', tenacity=True))],
    7749, 211,
    'Rend the target through the phases, causing {pot1} Arcane damage.',
    school=School.ARCANE,
    notes='hunter-pet-families F2: Warp Stalker II, 1000 x0.65 = 650 Arcane (melee DmgClass, the Venom Bite '
          'precedent). Visual 7749 (Arcane Blast), icon 211 (Phase Shift).',
)

time_warp_201768 = _utility(
    201768, 'Time Warp', TIME_WARP_LEVEL,
    [_enemy_aura(216, -26)],
    27, 339,
    'Your pet warps time around the target, increasing the casting time of its spells by ${$m1*-1}% for $d. Does not '
    'stack with Curse of Tongues, Mind-numbing Poison or Sticky Webbing.',
    school=School.ARCANE, cooldown_ms=10000, duration_ms=30000, range_yards=5.0, enemy_target=True, defense=1,
    prevention=1, RangeIndex=2, FacingCasterFlags=1,
    AuraDescription_Lang_enUS='Casting time increased.',
    notes='hunter-pet-families F2: Warp Stalker slot 2, autocast. Sticky Webbing 201753\'s effect (aura 216 '
          'HASTE_SPELLS -25%, Curse of Tongues 1714 live), single enemy, melee (a Tenacity pet; Spider\'s is 30 yd), '
          '30 s, 10 s cooldown. Group 1096 Cast Time Debuffs (rule 4). Visual 339 (Curse of Tongues), icon 27 (Slow).',
)

warp_202001 = _utility(
    202001, 'Warp', WARP_LEVEL,
    [_self_aura(AuraType.MOD_DODGE_PERCENT, 99)],
    1952, 263,
    'Your pet slips between moments, dodging all physical attacks for $d.',
    school=School.ARCANE, cooldown_ms=30000, duration_ms=4000, RangeIndex=1,
    AuraDescription_Lang_enUS='Dodging all physical attacks.',
    notes='hunter-pet-families F2: Warp Stalker slot 3, manual. Aura 49 MOD_DODGE_PERCENT +100 on the pet, 4 s (FE 9b: '
          'a creature dodges from any side; magic still lands, so the tooltip says physical, PLAN Q13), 30 s. Visual '
          '263 / icon 1952 from Warp 35346.',
)


# =====================================================================================================================
# Worm (family 42, skill line 784, basic Bite)
# =====================================================================================================================

_BURROW_ATTACK_MS = 3000
_BURROW_ATTACK_PULSES = 3
burrow_attack_pulse_201667 = spell(
    id=201667,
    name='Burrow Attack',
    school=School.NORMAL,
    attributes=0x50010,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=30.0,
    effects=_around_pet(round(kits.command_potency(500, 'I', tenacity=True) / _BURROW_ATTACK_PULSES, 4)),
    pet_owner_scaling=_PET_SCALING,
    notes='hunter-pet-families F2: Burrow Attack\'s pulse (command helper). 500 x0.84 = 420 over 3 pulses = 140 each, '
          'to the enemies within 8 yd of the pet (TargetA 22 / B 15) + DUMMY anchor at the primary, '
          'spell_hun_command_aoe_falloff. Cast by spell_hun_command_pulse\'s aura every second at the stashed primary. '
          'The commanded-spell carrier (Phoenix\'s Plume, Master\'s Command reach it), no kit slot (no Beast Cleave). '
          'Not SUPPRESS_CASTER_PROCS: the pulses are the command\'s only hits, procs per target hit like every AoE '
          'command. 30 yd so a pulse never fails its strict triggered range check. Visual 854 from Acid Spit 55749.'
          + kits.RULING_23B_NOTE,
    raw_overrides={**_cmd_raw(854), 'SpellIconID': 636},
)

burrow_attack_command_201636 = _command(
    201636, 'Burrow Attack',
    [Effect(type=EffectType.APPLY_AURA, implicit_target_a=1, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL,
            amplitude=_BURROW_ATTACK_MS // _BURROW_ATTACK_PULSES, trigger_spell=burrow_attack_pulse_201667.id),
     Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    7473, 252,
    'Burrow and erupt around your pet ' + str(_BURROW_ATTACK_PULSES) + ' times over $d, each eruption causing '
    + pot_text(burrow_attack_pulse_201667) + ' Physical damage to the target and all enemies within $201667a1 '
    'yards of your pet. Your pet keeps attacking.' + _FALLOFF_TEXT,
    duration_ms=_BURROW_ATTACK_MS,
    notes='hunter-pet-families F2: Worm I (PLAN §5.2 `pulse`, not a channel). eff0 PERIODIC_TRIGGER_SPELL on the pet, '
          '1 s, 3 s: spell_hun_command_pulse casts the pulse 201667 at the primary each tick (the command\'s target, '
          'stashed when the aura lands; the pet\'s victim if it is gone). eff1 DUMMY anchor keeps the target explicit. '
          'Visual 7473 / icon 252 from Burrow 26381.',
)

devour_command_201637 = _command(
    201637, 'Devour',
    [_direct(kits.command_potency(1100, 'II', tenacity=True))],
    376, 166,
    'Devour the target, causing {pot1} Physical damage.',
    notes='hunter-pet-families F2: Worm II, 1100 x0.65 = 715 Physical (1100 = 1000 + the AoE shift off Burrow Attack). '
          'Visual 376 (Bite), icon 166 (Devour).',
)

earthen_bulwark_201769 = _utility(
    201769, 'Earthen Bulwark', EARTHEN_BULWARK_LEVEL,
    [_raid_aura(AuraType.MOD_DAMAGE_PERCENT_TAKEN, -11, misc_value=_SCHOOL_MASK_ALL)],
    690, 7473,
    'Your pet raises the earth around your allies, reducing all damage taken by all party and raid members by '
    '${$m1*-1}% for $d.',
    school=School.NATURE, cooldown_ms=120000, duration_ms=10000, mobility=False, RangeIndex=1,
    AttributesEx=_ATTR1_NO_AUTOCAST_AI,
    AuraDescription_Lang_enUS='Damage taken reduced.',
    notes='hunter-pet-families F2: Worm slot 2 (rare, ruling 20), manual. Aura 87 -10% all schools, raid 100 yd '
          '(TargetA 56, FE 1c), 10 s, 2 min. d1 b28 only (ruling 10: Mobility does not shorten it), AttributesEx '
          'NO_AUTOCAST_AI (F1 review MINOR 2). New group 1232 (rule 4, highest wins; F3\'s Gale Barrier joins). '
          'Visual 7473 (Burrow), icon 690 (Stoneskin Totem).',
)

burrow_202002 = _utility(
    202002, 'Burrow', BURROW_LEVEL,
    [Effect(type=_EFFECT_SANCTUARY, implicit_target_a=1),
     _self_aura(_AURA_SCHOOL_IMMUNITY, 0, misc_value=_SCHOOL_MASK_ALL),
     _self_aura(AuraType.MOD_PACIFY, 0)],
    252, 7473,
    'Your pet burrows for $d, becoming immune to all damage and dropping its threat. It cannot attack while '
    'burrowed.',
    school=School.NATURE, cooldown_ms=60000, duration_ms=4000, RangeIndex=1,
    AuraDescription_Lang_enUS='Burrowed.',
    notes='hunter-pet-families F2: Worm slot 3, manual (FE 9a). eff0 SANCTUARY on the pet (a non-player: threat scaled '
          'to 0 on every enemy list, EvaluateSuppressed), eff1 aura 39 SCHOOL_IMMUNITY all schools (enemies pick '
          'another target), eff2 aura 25 MOD_PACIFY (no attacks while under), 4 s, 1 min. "Untargetable" is "immune '
          'and ignored" (no unit flags, cpp-scripts.md). Visual 7473 / icon 252 from Burrow 26381.',
)


# =====================================================================================================================
# Rhino (family 43, skill line 786, basic Smack)
# =====================================================================================================================

horn_charge_command_201638 = _command(
    201638, 'Horn Charge',
    _jump_strike(kits.command_potency(800, 'I', tenacity=True)),
    519, 457,
    'Charge the target and gore it with your horn for {pot2} Physical damage.',
    range_yards=25.0, melee_range_index=False,
    notes='hunter-pet-families F2: Rhino I, the Lunge 201720 shape: eff0 JUMP (41) to the target, eff1 800 x0.84 = '
          '672 Physical (800 = 600 + the AoE shift off Stampede). 25 yd, DmgClass MELEE. Visual 519 (pet Charge), icon '
          '457 (Charge).',
)

stampede_command_201639 = _command(
    201639, 'Stampede',
    _cone(kits.command_potency(800, 'II', tenacity=True)),
    9248, 3066,
    'Trample the target and all enemies in a cone in front of your pet, causing {pot1} Physical damage.'
    + _FALLOFF_TEXT,
    notes='hunter-pet-families F2: Rhino II, 800 x0.65 = 520 Physical, the F1 cone shape (104, 8 yd + DUMMY anchor), '
          'spell_hun_command_aoe_falloff. Visual 9248 / icon 3066 from Stampede 57386.',
)

horn_of_the_herd_201770 = _utility(
    201770, 'Horn of the Herd', HORN_OF_THE_HERD_LEVEL,
    [_raid_aura(AuraType.MOD_TOTAL_STAT_PERCENTAGE, 9, misc_value=-1)],
    1550, 9187,
    'Your pet sounds its horn, increasing the total stats of all party and raid members by $s1% for $d. Does not '
    'stack with Blessing of Kings.',
    cooldown_ms=40000, duration_ms=120000, RangeIndex=1,
    AuraDescription_Lang_enUS='Increases total stats by $s1%.',
    notes='hunter-pet-families F2: Rhino slot 2 (rare), autocast. Aura 137 +10% all stats (Blessing of Kings 20217 '
          'live), raid 100 yd, 2 min, 40 s cooldown. Group 1006 All Stats Percentage (rule 1). Visual 9187 (Blessing '
          'of Kings), icon 1550 (Horn).',
)

lead_the_herd_202003 = _utility(
    202003, 'Lead the Herd', LEAD_THE_HERD_LEVEL,
    [_raid_aura(AuraType.MOD_INCREASE_SPEED, 29)],
    916, 3405,
    'Your pet leads the herd, increasing the movement speed of all party and raid members by $s1% for $d.',
    cooldown_ms=60000, duration_ms=6000, RangeIndex=1,
    AuraDescription_Lang_enUS='Movement speed increased by $s1%.',
    notes='hunter-pet-families F2: Rhino slot 3, manual. Aura 31 +30% speed (Aspect of the Pack 13159), raid 100 yd '
          '(TargetA 56, ruling 7, FE 1e), 6 s, 1 min. Speed auras take the highest. Visual 3405 / icon 916 from Aspect '
          'of the Pack.',
)


# =====================================================================================================================
# Command display passives 202125-202142 (command order, the C++ COMMAND_DISPLAYS pairs)
# =====================================================================================================================

gore_display_202125 = _display(
    gore_command_201622, 'I', 1578,
    'Gore the target, causing ' + pot_text(gore_command_201622) + ' Physical damage. For $201665d the target takes '
    '$201665s1% more Physical damage from you and your pet.',
    display_id=202125,
)
tusk_sweep_display_202126 = _display(
    tusk_sweep_command_201623, 'II', 496,
    'Sweep your tusks at the target and all enemies in a cone in front of your pet, causing '
    + pot_text(tusk_sweep_command_201623) + ' Physical damage.' + _FALLOFF_TEXT,
    display_id=202126,
)
snap_display_202127 = _display(
    snap_command_201624, 'I', 1680,
    'Snap at the target, causing ' + pot_text(snap_command_201624) + ' Physical damage.',
    display_id=202127,
)
death_roll_display_202128 = _display(
    death_roll_command_201625, 'II', 1581,
    'Seize the target and roll, causing ' + pot_text(death_roll_command_201625, variant='total')
    + ' Physical damage over $201625d. Your pet channels for the whole roll.',
    display_id=202128,
)
snapping_bite_display_202129 = _display(
    snapping_bite_command_201626, 'I', 1680,
    'Snap your jaws on the target, causing ' + pot_text(snapping_bite_command_201626) + ' Physical damage.',
    display_id=202129,
)
shell_spin_display_202130 = _display(
    shell_spin_command_201627, 'II', 347,
    'Spin in your shell, causing ' + pot_text(shell_spin_command_201627) + ' Physical damage to the target and all '
    'enemies within $201627a1 yards of your pet.' + _FALLOFF_TEXT,
    display_id=202130,
)
pincer_crush_display_202131 = _display(
    pincer_crush_command_201628, 'I', 2679,
    'Crush the target in your pincers, causing ' + pot_text(pincer_crush_command_201628) + ' Physical damage and '
    'rooting it for $201666d. The root does not work on bosses.',
    display_id=202131,
)
bubble_burst_display_202132 = _display(
    bubble_burst_command_201629, 'II', 193,
    'Burst a bubble at the target, causing ' + pot_text(bubble_burst_command_201629) + ' Frost damage to it and all '
    'enemies within $201629a1 yards of it.' + _FALLOFF_TEXT,
    display_id=202132,
)
stinger_display_202133 = _display(
    stinger_command_201630, 'I', 1585,
    'Sting the target for ' + pot_text(stinger_command_201630) + ' Nature damage and poison it for an additional '
    + pot_text(stinger_command_201630, effect=2, variant='total') + ' Nature damage over $201630d.',
    display_id=202133,
)
deadly_sting_display_202134 = _display(
    deadly_sting_command_201631, 'II', 1719,
    'Sting the target with a deadly poison, causing ' + pot_text(deadly_sting_command_201631) + ' Nature damage and '
    'refreshing your Stinger on it.',
    display_id=202134,
)
thunderstomp_display_202135 = _display(
    thunderstomp_command_201632, 'I', 148,
    'Stomp the ground, causing ' + pot_text(thunderstomp_command_201632) + ' Physical damage to the target and all '
    'enemies within $201632a1 yards of your pet.' + _FALLOFF_TEXT,
    display_id=202135,
)
pound_display_202136 = _display(
    pound_command_201633, 'II', 473,
    'Pound the target, causing ' + pot_text(pound_command_201633) + ' Physical damage.',
    display_id=202136,
)
warp_strike_display_202137 = _display(
    warp_strike_command_201634, 'I', 1499,
    'Blink behind the target and strike it for ' + pot_text(warp_strike_command_201634, effect=2)
    + ' Physical damage.',
    display_id=202137,
)
phase_rend_display_202138 = _display(
    phase_rend_command_201635, 'II', 211,
    'Rend the target through the phases, causing ' + pot_text(phase_rend_command_201635) + ' Arcane damage.',
    display_id=202138,
)
burrow_attack_display_202139 = _display(
    burrow_attack_command_201636, 'I', 252,
    'Burrow and erupt around your pet ' + str(_BURROW_ATTACK_PULSES) + ' times over $201636d, each eruption causing '
    + pot_text(burrow_attack_pulse_201667) + ' Physical damage to the target and all enemies within $201667a1 '
    'yards of your pet. Your pet keeps attacking.' + _FALLOFF_TEXT,
    display_id=202139,
)
devour_display_202140 = _display(
    devour_command_201637, 'II', 166,
    'Devour the target, causing ' + pot_text(devour_command_201637) + ' Physical damage.',
    display_id=202140,
)
horn_charge_display_202141 = _display(
    horn_charge_command_201638, 'I', 457,
    'Charge the target and gore it with your horn for ' + pot_text(horn_charge_command_201638, effect=2)
    + ' Physical damage.',
    display_id=202141,
)
stampede_display_202142 = _display(
    stampede_command_201639, 'II', 3066,
    'Trample the target and all enemies in a cone in front of your pet, causing ' + pot_text(stampede_command_201639)
    + ' Physical damage.' + _FALLOFF_TEXT,
    display_id=202142,
)


# =====================================================================================================================
# SkillLineAbility rows (AcquireMethod 2, ClassMask 0): slot 2 then slot 3 per family, 30618-30635
# =====================================================================================================================

TENACITY_F2_SLA_ROWS = (
    (30618, 211, war_grunt_201762.id), (30619, 211, boar_charge_201995.id),                  # Boar
    (30620, 212, ankle_crack_201763.id), (30621, 212, bad_attitude_201996.id),               # Crocolisk
    (30622, 251, hardened_shell_201764.id), (30623, 251, shell_shield_201997.id),            # Turtle
    (30624, 214, crippling_pinch_201765.id), (30625, 214, bubble_shield_201998.id),          # Crab
    (30626, 236, scorpid_poison_201766.id), (30627, 236, disarming_pincer_201999.id),        # Scorpid
    (30628, 215, primal_might_201767.id), (30629, 215, pummel_202000.id),                    # Gorilla
    (30630, 766, time_warp_201768.id), (30631, 766, warp_202001.id),                         # Warp Stalker
    (30632, 784, earthen_bulwark_201769.id), (30633, 784, burrow_202002.id),                 # Worm
    (30634, 786, horn_of_the_herd_201770.id), (30635, 786, lead_the_herd_202003.id),         # Rhino
)
assert sorted(r[0] for r in TENACITY_F2_SLA_ROWS) == list(range(30618, 30636))
for _sla_id, _line, _spell_id in TENACITY_F2_SLA_ROWS:
    skill_line_ability(id=_sla_id, skill_line=_line, spell_id=_spell_id, class_mask=0, acquire_method=2)


# =====================================================================================================================
# Spell groups (stock groups, DI §4.1; ruling 7) and the new raid damage taken group 1232
# =====================================================================================================================

spell_group(1029, war_grunt_201762)          # Percentage AP Buffs (rule 1)
spell_group(1059, ankle_crack_201763)        # Attack Speed Debuffs (rule 3)
spell_group(1086, hardened_shell_201764)     # Armor Buffs (rule 4)
spell_group(1059, crippling_pinch_201765)    # Attack Speed Debuffs (rule 3)
spell_group(1058, scorpid_poison_201766)     # crit taken, "Poisons" (rule 3)
spell_group(1088, primal_might_201767)       # Strength and Agility Buffs (rule 4)
spell_group(1096, time_warp_201768)          # Cast Time Debuffs (rule 4)
spell_group(1006, horn_of_the_herd_201770)   # All Stats Percentage (rule 1)
spell_group_rule(SPELL_GROUP_RAID_DAMAGE_TAKEN, 4,
                 'Raid Damage Taken Buffs (hunter pets: Earthen Bulwark, Gale Barrier): the highest wins')
spell_group(SPELL_GROUP_RAID_DAMAGE_TAKEN, earthen_bulwark_201769)


# =====================================================================================================================
# Script bindings (PLAN §5.2). Positive keys only (L7).
# =====================================================================================================================

scripted_by(tusk_sweep_command_201623, 'spell_hun_command_aoe_falloff')
scripted_by(shell_spin_command_201627, 'spell_hun_command_aoe_falloff')
scripted_by(bubble_burst_command_201629, 'spell_hun_command_aoe_falloff')
scripted_by(thunderstomp_command_201632, 'spell_hun_command_aoe_falloff')
scripted_by(burrow_attack_pulse_201667, 'spell_hun_command_aoe_falloff')
scripted_by(stampede_command_201639, 'spell_hun_command_aoe_falloff')
scripted_by(burrow_attack_command_201636, 'spell_hun_command_pulse')
scripted_by(deadly_sting_command_201631, 'spell_hun_command_refresh')
scripted_by(pincer_crush_root_201666, 'spell_hun_pet_control_boss_filter')
scripted_by(boar_charge_201995, 'spell_hun_pet_control_boss_filter')
scripted_by(disarming_pincer_201999, 'spell_hun_pet_control_boss_filter')
scripted_by(bubble_shield_201998, 'spell_hun_pet_absorb')

# Every pet-cast spell above keeps the pet bit: the lint (c) contract of _masks.py.
assert m.PET_ABILITY == 0x10000000
