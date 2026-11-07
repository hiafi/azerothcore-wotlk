"""
The six Stratholme hard mode item effects: Balnazzar, the Grand Lie (Carrion Signet, Dust of the Nathrezim, Two-Faced
Tome) and Baron Rivendare, the Ultimatum (Ysida's Locket, Blade of the Condemned, Deathcharger's Spur). Designer text:
docs/dungeons/stratholme-rework.md "Hard mode lists", copied in dungeon-loot-vanilla.md. Wave 1 dungeon items, after
the Deadmines precedent (deadmines_hard_mode_effects.py, stages IV6 / IV10).

Every damage and absorb number comes from potency (docs/potency-system.md; user rule: everything on potency, no hand
coefficients and no hand spell_bonus_data), except the Two-Faced Tome's lie, which is a share of the heal that
triggered it (`potency_excluded`). The effects the designer scales by item level (the Carrion Swarm, Ysida's ward, the
Deathcharger's trample) are declared with scale="budget" on the item (stratholme.py): every tier above 71 gets its own
copies (lib/item_spell_copies.py). The scripts are modules/mod-dungeon-bosses src/Stratholme/hard_mode_items.cpp (ids
mirrored in StratholmeHardModeItemsLogic.h).

Ids: the `stratholme_items` reservation 205660-205699 (source/ids.yaml).

  205660  Carrion Signet         Equip: a passive PROC_TRIGGER_SPELL aura. Landed damaging attacks and spells (melee,
                                 ranged and harmful magic, not periodic ticks) have a 10% chance, 10 sec internal
                                 cooldown, to cast 205661. Data only, no script.
  205661  Carrion Swarm          the cone: Shadow, enemies in a 10 yd cone in front of the wearer, hybrid potency
                                 100 SP + 100 AP per target (T 1.5 s, an off-GCD payout). Cannot trigger procs.
  205662  Dust of the Nathrezim  Use (2 min): put a non-boss enemy creature within 30 yd to sleep for 20 sec (stun aura,
                                 mechanic Sleep, any damage wakes it). spell_strat_dust_of_the_nathrezim refuses a boss
                                 or a player. No numbers to scale.
  205663  Two-Faced Tome         Equip: a passive DUMMY proc aura (amount 25 = the share of the heal). A landed direct
                                 heal has a 20% chance to fire spell_strat_two_faced_tome: the enemy nearest the healed
                                 target, within 10 yd of it and in combat, takes 205664.
  205664  The Lie                the lie: Shadow, one enemy, the damage is 25% of the heal (set by the script). No
                                 potency (a share of another spell), never crits, ignores the healer's damage bonuses
                                 (the heal already had them), cannot trigger procs.
  205665  Ysida's Locket         Equip: a passive PERIODIC_DUMMY aura, every 0.5 sec (amount 20 = the health threshold,
                                 radius 20 yd). spell_strat_ysidas_locket wards the first group member within 20 yd
                                 below 20% health with 205666 and marks the wearer with 205667.
  205666  Ysida's Ward           the shield: absorbs all schools, base potency 300 (a set amount, no spell power: the
                                 designer's "set amount, scaled by item level"), 10 sec.
  205667  Ysida's Locket         the 60 sec lockout on the wearer (a debuff, so it cannot be clicked off). Its duration
                                 is the internal cooldown; the tooltip shows it ($205667d).
  205668  Blade of the Condemned Equip: a passive DUMMY proc aura. Landed melee hits (auto attacks and melee-class
                                 spells), 100%, fire spell_strat_blade_of_the_condemned: one stack of 205669 on the
                                 target; a hit on another target first removes the wearer's Condemned from the last one.
  205669  Condemned              the debuff: 1% more damage taken from the wearer per stack, up to 5 stacks, 30 sec. The
                                 damage hook is the module's UnitScript (melee, spell and periodic damage from the
                                 aura's caster only); the amount is this spell's effect.
  205670  Deathcharger's Spur    Use (2 min): 6 sec, +60% movement speed (mounted and unmounted, so the look's mount
                                 does not cancel it), and a 0.25 sec PERIODIC_DUMMY (radius 3 yd):
                                 spell_strat_deathchargers_spur strikes every enemy the wearer passes through once with
                                 205671 and puts the spectral Deathcharger look 205672 under the wearer.
  205671  Deathcharger Trample   the trample: Shadow, one enemy, hybrid potency 120 SP + 120 AP (T 1.5 s). Not the
                                 swarm's 100: two spells with the same tooltip numbers would join one copy family.
  205672  Spectral Deathcharger  the look: a hidden MOUNTED aura on the stock Rivendare's Deathcharger (creature 30542).
                                 The script adds it with AddAura (a mount spell cast would fail its "no mounts in
                                 dungeons" check) and removes it with the Spur. Casting a spell or attacking dismounts
                                 the look as for any mount; the speed and the trample go on.
  205673-205699  spare

Proc chances, internal cooldowns, potencies, durations, radii and the shares are proposals waiting for the designer
(STAGE-W1-STRAT report, designer questions). None of the looks were checked in game.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.registry import pot_text, procs_on, scripted_by, spell

_TEXT_MASKS = {
    'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '',
    'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712190,
}

_TARGET_UNIT_CASTER = 1
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_UNIT_TARGET_ALLY = 21
_TARGET_UNIT_CONE_ENEMY_24 = 24

_ATTR0_PASSIVE = 0x00000040
_ATTR0_DO_NOT_DISPLAY = 0x00000080
_ATTR0_DO_NOT_LOG = 0x00000100
_ATTR0_AURA_IS_DEBUFF = 0x04000000
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_SUPPRESS_CASTER_PROCS = 0x00010000
_ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
_ATTR4_NO_CAST_LOG = 0x00000001

_DMG_CLASS_MAGIC = 1
_DISPEL_MAGIC = 1
_MECHANIC_SLEEP = 10
_AURA_INTERRUPT_TAKE_DAMAGE = 0x00000002
_ALL_SCHOOLS = 127
_AURA_MOUNTED = 78  # SPELL_AURA_MOUNTED (no AuraType member yet)
_NPC_RIVENDARES_DEATHCHARGER = 30542  # stock creature of the mount 17481, display 10718

# spell_proc (SpellMgr.h)
_PROC_FLAG_DONE_MELEE_AUTO_ATTACK = 0x00000004
_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS = 0x00000010
_PROC_FLAG_DONE_RANGED_AUTO_ATTACK = 0x00000040
_PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS = 0x00000100
_PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS = 0x00000400
_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS = 0x00004000
_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG = 0x00010000
_PROC_SPELL_TYPE_DAMAGE = 0x1
_PROC_SPELL_TYPE_HEAL = 0x2
_PROC_SPELL_PHASE_HIT = 0x2
_PROC_HIT_NORMAL_OR_CRITICAL = 0x1 | 0x2

# Stock looks (none checked in game yet).
_SV_CARRION_SWARM = 9099        # Carrion Swarm 34240: a dreadlord's cone of bats
_SV_SLEEP = 87                  # Sleep 700
_SV_MIND_BLAST = 3057           # Mind Blast 8092: the lie's Shadow hit
_SV_POWER_WORD_SHIELD = 784     # Power Word: Shield 17
_SV_RIVENDARES_DEATHCHARGER = 1706  # Rivendare's Deathcharger 17481
_SV_TRAMPLE = 672               # Trample 5568
_ICON_CARRION_SWARM = 116
_ICON_SLEEP = 44
_ICON_MIND_BLAST = 95
_ICON_POWER_WORD_SHIELD = 566
_ICON_MARK_OF_BLOOD = 2285
_ICON_DEATHCHARGER = 1241

_CONE_RANGE = 10.0
_LIE_RANGE = 10.0
_LOCKET_RADIUS = 20.0
_TRAMPLE_RADIUS = 3.0


def _raw(desc: str = '', aura_desc: str = '', spell_level: int = 0, **more) -> dict:
    return {'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': spell_level, 'CastingTimeIndex': 1,
            'Description_Lang_enUS': desc, 'AuraDescription_Lang_enUS': aura_desc, **_TEXT_MASKS, **more}


def _off_gcd() -> dict:
    return {'StartRecoveryCategory': 0, 'StartRecoveryTime': 0}


# --- Carrion Signet (ring, Equip) -------------------------------------------------------------------------------------

carrion_swarm_205661 = spell(
    id=205661, name='Carrion Swarm', school=School.SHADOW, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=_CONE_RANGE, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=100.0, ap_potency=100.0, potency_kind='direct',
                    time_basis_ms=1500, implicit_target_a=_TARGET_UNIT_CONE_ENEMY_24, radius_yards=_CONE_RANGE)],
    spell_icon_id=_ICON_CARRION_SWARM,
    notes='Stratholme hard mode, Carrion Signet: the swarm, cast by the Signet aura 205660 (PROC_TRIGGER_SPELL, '
          'triggered). Shadow, every enemy in a 10 yd cone in front of the wearer (TARGET_UNIT_CONE_ENEMY_24, the '
          'stock Carrion Swarm 34240 shape). Hybrid potency 100 SP + 100 AP per target, T 1.5 s (an off-GCD payout): '
          'a ring with no primary, so casters and melee both scale off it. DefenseType MAGIC. SUPPRESS_CASTER_PROCS: '
          'the swarm never procs the Signet or anything else. Look: stock Carrion Swarm SV 9099.',
    raw_overrides=_raw('Deals {pot1} Shadow damage to enemies in a cone in front of you.', spell_level=1,
                       DefenseType=_DMG_CLASS_MAGIC, SpellVisualID_1=_SV_CARRION_SWARM,
                       AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS),
)

_SIGNET_PROC_FLAGS = (_PROC_FLAG_DONE_MELEE_AUTO_ATTACK | _PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS
                      | _PROC_FLAG_DONE_RANGED_AUTO_ATTACK | _PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS
                      | _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG)

carrion_signet_205660 = spell(
    id=205660, name='Carrion Signet', school=School.SHADOW, attributes=_ATTR0_PASSIVE, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PROC_TRIGGER_SPELL, base_points=0,
                    trigger_spell=carrion_swarm_205661.id, implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_CARRION_SWARM,
    notes='Stratholme hard mode, Carrion Signet (Balnazzar hard mode ring), the Equip: a passive PROC_TRIGGER_SPELL '
          'aura that casts 205661. spell_proc: done melee and ranged auto attacks, melee and ranged class spells and '
          'harmful magic spells (0x10154), damage type, hit phase, normal or critical hits only, 10% chance, 10 s '
          'internal cooldown (the throttle against haste and cleaves; Systems.md section 5). Periodic ticks are not '
          'in the flags. Item auras get no Proc Chance (Systems.md section 5). Data only, no script.',
    raw_overrides=_raw(
        'Your damaging attacks and spells have a chance to loose a Carrion Swarm, dealing '
        + pot_text(carrion_swarm_205661) + ' Shadow damage to enemies in a cone in front of you.',
        ProcTypeMask=_SIGNET_PROC_FLAGS, ProcChance=10,
    ),
)
procs_on(carrion_signet_205660, proc_flags=_SIGNET_PROC_FLAGS, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=10.0,
         cooldown_ms=10000)

# --- Dust of the Nathrezim (trinket, Use) -----------------------------------------------------------------------------

dust_of_the_nathrezim_205662 = spell(
    id=205662, name='Dust of the Nathrezim', school=School.SHADOW, cast_time_ms=0, cooldown_ms=120000,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=30.0, duration_ms=20000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, base_points=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_SLEEP,
    notes='Stratholme hard mode, Dust of the Nathrezim (Balnazzar hard mode trinket), the Use: 2 min cooldown, off '
          'the GCD, an enemy within 30 yd sleeps for 20 s (MOD_STUN, Mechanic SLEEP like stock Sleep 700 and '
          'Hibernate, DispelType Magic). AuraInterruptFlags TAKE_DAMAGE: any damage wakes it. '
          'spell_strat_dust_of_the_nathrezim refuses a player or a boss (SPELL_FAILED_BAD_TARGETS). Look: stock Sleep '
          'SV 87. Nothing scales, so the item carries the spell unscaled; full stat budget (designer).',
    raw_overrides=_raw(
        'Puts a non-boss enemy to sleep for up to $d. Any damage will awaken the target.',
        'Asleep.', Mechanic=_MECHANIC_SLEEP, DispelType=_DISPEL_MAGIC, DefenseType=_DMG_CLASS_MAGIC,
        AuraInterruptFlags=_AURA_INTERRUPT_TAKE_DAMAGE, SpellVisualID_1=_SV_SLEEP, **_off_gcd(),
    ),
)
scripted_by(dust_of_the_nathrezim_205662, 'spell_strat_dust_of_the_nathrezim')

# --- Two-Faced Tome (held in off-hand, Equip) -------------------------------------------------------------------------

the_lie_205664 = spell(
    id=205664, name='The Lie', school=School.SHADOW, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0,
                    potency_excluded='a share of the heal that triggered it, set by spell_strat_two_faced_tome',
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_MIND_BLAST,
    notes='Stratholme hard mode, Two-Faced Tome: the lie, cast by the healer (triggered) from '
          'spell_strat_two_faced_tome with its damage set to the Tome aura amount (25%) of the heal. No potency: a '
          'share of another spell. Never crits (CANT_CRIT) and ignores the healer\'s damage done bonuses '
          '(IGNORE_CASTER_MODIFIERS): the heal already had both. SUPPRESS_CASTER_PROCS. DefenseType MAGIC. Look: '
          'stock Mind Blast SV 3057.',
    raw_overrides=_raw('Deals Shadow damage.', spell_level=1, DefenseType=_DMG_CLASS_MAGIC,
                       SpellVisualID_1=_SV_MIND_BLAST, AttributesEx2=_ATTR2_CANT_CRIT,
                       AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS | _ATTR3_IGNORE_CASTER_MODIFIERS),
)

_TOME_PROC_FLAGS = _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS | _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS

two_faced_tome_205663 = spell(
    id=205663, name='Two-Faced Tome', school=School.SHADOW, attributes=_ATTR0_PASSIVE, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=24,
                    implicit_target_a=_TARGET_UNIT_CASTER, radius_yards=_LIE_RANGE)],
    spell_icon_id=_ICON_MIND_BLAST,
    notes='Stratholme hard mode, Two-Faced Tome (Balnazzar hard mode off-hand), the Equip: a passive DUMMY aura, '
          'amount 25 (BasePoints 24 + DieSides 1) = the share of the heal the lie deals, radius 10 yd = how far from '
          'the healed target the lie looks for an enemy. spell_proc: done positive spells of the magic or none damage '
          'class (0x4400), heal type, hit phase (direct heals only: a HoT cast heals nothing then, and its ticks are '
          'periodic), normal or critical, 20% chance, no internal cooldown. spell_strat_two_faced_tome casts 205664.',
    raw_overrides=_raw(
        'Your direct heals have a chance to tell a lie: the enemy nearest your target, within $a1 yd of it, also '
        'takes Shadow damage equal to $s1% of the heal.',
        ProcTypeMask=_TOME_PROC_FLAGS, ProcChance=20,
    ),
)
procs_on(two_faced_tome_205663, proc_flags=_TOME_PROC_FLAGS, spell_type_mask=_PROC_SPELL_TYPE_HEAL,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=20.0)
scripted_by(two_faced_tome_205663, 'spell_strat_two_faced_tome')

# --- Ysida's Locket (neck, Equip) -------------------------------------------------------------------------------------

ysidas_ward_205666 = spell(
    id=205666, name="Ysida's Ward", school=School.HOLY, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=10000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.SCHOOL_ABSORB, base_potency=300.0,
                    potency_kind='absorb', misc_value=_ALL_SCHOOLS, implicit_target_a=_TARGET_UNIT_TARGET_ALLY)],
    spell_icon_id=_ICON_POWER_WORD_SHIELD,
    notes='Stratholme hard mode, Ysida\'s Locket: the ward, cast by the wearer (triggered) on the group member in '
          'danger. Absorbs all schools for 10 s. A set amount: base potency 300 (about 3,250 at level 60), no spell '
          'power or attack power (the designer\'s "absorbs a set amount, scaled by item level"; the tier copies '
          'scale it). Look: stock Power Word: Shield SV 784.',
    raw_overrides=_raw('Absorbs {pot1} damage.', 'Absorbs damage.', spell_level=1,
                       SpellVisualID_1=_SV_POWER_WORD_SHIELD),
)

ysidas_locket_lockout_205667 = spell(
    id=205667, name="Ysida's Locket", school=School.HOLY, attributes=_ATTR0_AURA_IS_DEBUFF, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=60000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_POWER_WORD_SHIELD,
    notes='Stratholme hard mode, Ysida\'s Locket: the internal cooldown, a 60 s DUMMY debuff on the wearer '
          '(AURA_IS_DEBUFF, so it cannot be clicked off). spell_strat_ysidas_locket wards nobody while it is up; its '
          'duration is the cooldown and the Locket tooltip shows it ($205667d).',
    raw_overrides=_raw(aura_desc="Ysida's Locket cannot ward again yet.", AttributesEx4=_ATTR4_NO_CAST_LOG),
)

ysidas_locket_205665 = spell(
    id=205665, name="Ysida's Locket", school=School.HOLY, attributes=_ATTR0_PASSIVE, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, base_points=19, amplitude=500,
                    implicit_target_a=_TARGET_UNIT_CASTER, radius_yards=_LOCKET_RADIUS)],
    spell_icon_id=_ICON_POWER_WORD_SHIELD,
    notes='Stratholme hard mode, Ysida\'s Locket (Baron Rivendare hard mode neck), the Equip: a passive '
          'PERIODIC_DUMMY aura every 0.5 s, amount 20 (BasePoints 19 + DieSides 1) = the health threshold in percent, '
          'radius 20 yd. spell_strat_ysidas_locket: unless the lockout 205667 is up, the first group member (the '
          'wearer included) alive within 20 yd under 20% health gets the ward 205666 and the wearer gets 205667.',
    raw_overrides=_raw(
        'When a party member within $a1 yd falls below $s1% health, you ward them with a shield that absorbs '
        + pot_text(ysidas_ward_205666) + ' damage for $205666d. This effect cannot occur more than once every '
        '$205667d.',
    ),
)
scripted_by(ysidas_locket_205665, 'spell_strat_ysidas_locket')

# --- Blade of the Condemned (one-hand sword, Equip) -------------------------------------------------------------------

condemned_205669 = spell(
    id=205669, name='Condemned', school=School.SHADOW, attributes=_ATTR0_AURA_IS_DEBUFF, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=30000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_MARK_OF_BLOOD,
    notes='Stratholme hard mode, Blade of the Condemned: the debuff, cast by the wearer (triggered) on the target it '
          'hits. A DUMMY aura, amount 1 (BasePoints 0 + DieSides 1) = percent more damage taken from its caster per '
          'stack; CumulativeAura 5; 30 s, refreshed by every hit. The damage is applied by the module\'s UnitScript '
          '(StratholmeCondemnedDamage: melee, spell and periodic damage whose attacker is the aura\'s caster), not by '
          'an aura type: SPELL_AURA_MOD_DAMAGE_FROM_CASTER needs a spell class mask and skips auto attacks.',
    raw_overrides=_raw('Increases the damage the target takes from you by $s1% per application.',
                       'Taking more damage from the one who condemned it.', spell_level=1, CumulativeAura=5,
                       DefenseType=_DMG_CLASS_MAGIC, AttributesEx4=_ATTR4_NO_CAST_LOG),
)

_BLADE_PROC_FLAGS = _PROC_FLAG_DONE_MELEE_AUTO_ATTACK | _PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS

blade_of_the_condemned_205668 = spell(
    id=205668, name='Blade of the Condemned', school=School.SHADOW, attributes=_ATTR0_PASSIVE, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_MARK_OF_BLOOD,
    notes='Stratholme hard mode, Blade of the Condemned (Baron Rivendare hard mode sword), the Equip: a passive DUMMY '
          'proc aura. spell_proc: done melee auto attacks and melee-class spells (0x14), damage type, hit phase, '
          'normal or critical hits only, 100%. spell_strat_blade_of_the_condemned puts one stack of 205669 on the '
          'target and, when the target changed, first removes the wearer\'s Condemned from the last one.',
    raw_overrides=_raw(
        'Your melee hits Condemn the target, increasing the damage it takes from you by $205669s1% per application, '
        'stacking up to $205669u times. Attacking another target resets it.',
        ProcTypeMask=_BLADE_PROC_FLAGS, ProcChance=100,
    ),
)
procs_on(blade_of_the_condemned_205668, proc_flags=_BLADE_PROC_FLAGS, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=100.0)
scripted_by(blade_of_the_condemned_205668, 'spell_strat_blade_of_the_condemned')

# --- Deathcharger's Spur (trinket, Use) -------------------------------------------------------------------------------

deathcharger_trample_205671 = spell(
    id=205671, name='Deathcharger Trample', school=School.SHADOW, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=120.0, ap_potency=120.0, potency_kind='direct',
                    time_basis_ms=1500, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_DEATHCHARGER,
    notes='Stratholme hard mode, Deathcharger\'s Spur: the trample, cast by the wearer (triggered) from '
          'spell_strat_deathchargers_spur on each enemy the charge passes through, once per enemy per use. Shadow, '
          'hybrid potency 120 SP + 120 AP, T 1.5 s (a trinket with no primary). DefenseType MAGIC. Look: stock '
          'Trample SV 672.',
    raw_overrides=_raw('Deals {pot1} Shadow damage.', spell_level=1, DefenseType=_DMG_CLASS_MAGIC,
                       SpellVisualID_1=_SV_TRAMPLE),
)

spectral_deathcharger_205672 = spell(
    id=205672, name='Spectral Deathcharger', school=School.SHADOW,
    attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=6000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_MOUNTED, misc_value=_NPC_RIVENDARES_DEATHCHARGER,
                    implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_DEATHCHARGER,
    notes='Stratholme hard mode, Deathcharger\'s Spur: the look, a hidden MOUNTED aura on the stock Rivendare\'s '
          'Deathcharger (creature 30542, the mount of 17481). spell_strat_deathchargers_spur adds it with AddAura (a '
          'cast would fail Spell::CheckCast\'s no-mounts-in-dungeons rule) and removes it when the Spur ends. Look: '
          'stock SV 1706.',
    raw_overrides=_raw(SpellVisualID_1=_SV_RIVENDARES_DEATHCHARGER, AttributesEx4=_ATTR4_NO_CAST_LOG),
)

deathchargers_spur_205670 = spell(
    id=205670, name="Deathcharger's Spur", school=School.SHADOW, cast_time_ms=0, cooldown_ms=120000,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=6000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_INCREASE_SPEED, base_points=59,
               implicit_target_a=_TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_INCREASE_MOUNTED_SPEED, base_points=59,
               implicit_target_a=_TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, base_points=0, amplitude=250,
               implicit_target_a=_TARGET_UNIT_CASTER, radius_yards=_TRAMPLE_RADIUS),
    ],
    spell_icon_id=_ICON_DEATHCHARGER,
    notes='Stratholme hard mode, Deathcharger\'s Spur (Baron Rivendare hard mode trinket), the Use: 2 min cooldown, '
          'off the GCD, 6 s. +60% movement speed twice (MOD_INCREASE_SPEED and MOD_INCREASE_MOUNTED_SPEED, BasePoints '
          '59 + DieSides 1: the engine reads only the mounted one while the look 205672 is up). A PERIODIC_DUMMY '
          'every 0.25 s, radius 3 yd: spell_strat_deathchargers_spur strikes every enemy in it once per use with '
          '205671.',
    raw_overrides=_raw(
        'Ride a spectral Deathcharger for $d, increasing your movement speed by $s1%. Every enemy you pass through '
        'takes ' + pot_text(deathcharger_trample_205671) + ' Shadow damage.',
        'Riding a spectral Deathcharger. Movement speed increased.', **_off_gcd(),
    ),
)
scripted_by(deathchargers_spur_205670, 'spell_strat_deathchargers_spur')
