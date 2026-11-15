"""
The six Blackrock Spire hard mode item effects: Overlord Wyrmthalak, the war horn (Bloodaxe War Horn, Ward of the Three
Tribes, Shardstaff of Stolen Power) and General Drakkisath, the General's Army (Trophy of the Champion, Orders of the
General, The Humbler). Designer text: docs/dungeons/blackrock-spire-rework.md ## Loot "Hard mode: ...", copied in
docs/dungeons/dungeon-loot-vanilla.md. Wave 2 dungeon items, after the Stratholme precedent
(stratholme_hard_mode_effects.py).

None of the six deals damage or heals, so none has a potency value: every number is a percent (damage taken or done,
stacks) or a time, the same on every tier ("percentages stay as declared", lib/item_spell_copies.py). Nothing here
needs `scale="budget"`; the designer text names no number that grows with item level. The scripts are
modules/mod-dungeon-bosses src/BlackrockSpire/hard_mode_items.cpp (ids mirrored in BlackrockSpireHardModeItemsLogic.h).

Ids: the `blackrock_spire_items` reservation 206800-206829 (source/ids.yaml); this file takes 206800-206811. The
creature reservation 300650-300654 is unused (no summons).

Overlord Wyrmthalak
  206800  Bloodaxe War Horn       trinket, Use (2 min, off the GCD): enemies within 10 yd are interrupted (the
                                  interrupted school is locked for the spell's 4 sec) and get 206801. Data only, no
                                  script.
  206801  Bloodaxe War Cry        the debuff: -10% damage done, all schools, 10 sec, a refresh by a second horn.
  206802  Ward of the Three Tribes  shield, Equip: a passive PERIODIC_DUMMY aura, every 0.5 sec (amount 5 = the cap,
                                  radius 8 yd). spell_brs_ward_of_the_three_tribes counts the enemies within the radius
                                  that are attacking the wearer and holds that many stacks of 206803.
  206803  Ward of the Three Tribes  the buff: -1% damage taken per stack, up to 5 stacks, 3 sec (the script refreshes it
                                  every tick and removes it when nobody is attacking the wearer).
  206804  Shardstaff of Stolen Power  staff, Equip: a passive PROC_TRIGGER_SPELL aura. A done spell critical strike
                                  (direct damage or heal, no periodic tick), 100%, casts 206805 on the wearer. Data
                                  only.
  206805  Stolen Power            +1% spell damage and +1% healing done, 10 sec, up to 5 stacks, each crit refreshes it.

General Drakkisath
  206806  Trophy of the Champion  trinket, Equip: a passive PROC_TRIGGER_SPELL aura. Any done damage (melee, ranged,
                                  harmful spells, periodic ticks), 100%, casts the mark 206807 on the victim.
  206807  Champion's Mark         the "damaged in the last 5 sec" window: a 5 sec debuff from the wearer, refreshed by
                                  every hit. spell_brs_champions_mark: when it ends because the target died, the wearer
                                  (if still wearing the Trophy) gets 206808.
  206808  Champion's Trophy       +1% damage and healing done, all schools, 30 sec, up to 5 stacks.
  206809  Orders of the General   held in off-hand, Use (2 min, off the GCD): the wearer and party members within 30 yd
                                  take 10% less damage for 8 sec (TARGET_UNIT_CASTER_AREA_PARTY). Data only.
  206810  The Humbler             mace, Equip: a passive PROC_TRIGGER_SPELL aura. Landed melee hits (auto attacks and
                                  melee-class spells), 15%, casts 206811 on the target. Data only.
  206811  Humbled                 the debuff: -5% damage done, all schools, 8 sec.
  206812-206829  spare

Chances, durations, the 4 sec lockout, radii and the hit-based proc flags are proposals waiting for the designer
(STAGE-BRS report, designer questions). None of the looks were checked in game.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.registry import procs_on, scripted_by, spell

_TEXT_MASKS = {
    'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '',
    'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712190,
}

# Implicit targets (SharedDefines.h Targets)
_TARGET_UNIT_CASTER = 1
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_UNIT_SRC_AREA_ENEMY = 15
_TARGET_UNIT_CASTER_AREA_PARTY = 20
_TARGET_SRC_CASTER = 22

_ATTR0_PASSIVE = 0x00000040
_ATTR0_AURA_IS_DEBUFF = 0x04000000
_ATTR4_NO_CAST_LOG = 0x00000001

_MECHANIC_INTERRUPT = 26      # the effect mechanic of Pummel and Counterspell: interrupt immunity applies to it
_SCHOOL_MASK_ALL = 127
_SCHOOL_MASK_SPELLS = 126     # every school but Physical: "spell damage"

# spell_proc (SpellMgr.h)
_PROC_FLAG_DONE_MELEE_AUTO_ATTACK = 0x00000004
_PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS = 0x00000010
_PROC_FLAG_DONE_RANGED_AUTO_ATTACK = 0x00000040
_PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS = 0x00000100
_PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS = 0x00000400
_PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_NEG = 0x00001000
_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS = 0x00004000
_PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG = 0x00010000
_PROC_FLAG_DONE_PERIODIC = 0x00040000
_PROC_SPELL_TYPE_DAMAGE = 0x1
_PROC_SPELL_TYPE_HEAL = 0x2
_PROC_SPELL_PHASE_HIT = 0x2
_PROC_HIT_NORMAL = 0x1
_PROC_HIT_CRITICAL = 0x2
_PROC_HIT_NORMAL_OR_CRITICAL = _PROC_HIT_NORMAL | _PROC_HIT_CRITICAL

_MELEE_HITS = _PROC_FLAG_DONE_MELEE_AUTO_ATTACK | _PROC_FLAG_DONE_SPELL_MELEE_DMG_CLASS
_RANGED_HITS = _PROC_FLAG_DONE_RANGED_AUTO_ATTACK | _PROC_FLAG_DONE_SPELL_RANGED_DMG_CLASS
_HARMFUL_SPELLS = _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG | _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_NEG
_HELPFUL_SPELLS = _PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_POS | _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_POS
# Every spell cast that can crit: the harmful and helpful magic and none class spells (direct, so no periodic flag).
_SPELL_CRITS = _HARMFUL_SPELLS | _HELPFUL_SPELLS
# Every kind of damage the wearer does, ticks of damage over time included.
_ALL_DAMAGE = _MELEE_HITS | _RANGED_HITS | _HARMFUL_SPELLS | _PROC_FLAG_DONE_PERIODIC

# Stock looks and icons, picked by name (none checked in game yet).
_SV_BATTLE_SHOUT = 246          # Battle Shout 6673
_SV_DEMORALIZING_SHOUT = 210    # Demoralizing Shout 1160
_SV_SHIELD_WALL = 345           # Shield Wall 871
_SV_POWER_INFUSION = 7553       # Power Infusion 10060
_SV_WARCHIEFS_BLESSING = 4230   # Warchief's Blessing 16609
_SV_CRIPPLE = 351               # Cripple 89
_ICON_HORN = 1417               # INV_Misc_Horn_03
_ICON_DEMORALIZING_SHOUT = 282
_ICON_SHIELD_WALL = 281
_ICON_ARCANE_POWER = 62
_ICON_POWER_INFUSION = 1872
_ICON_CHAMPIONS_GRACE = 1946    # Spell_Holy_ChampionsGrace
_ICON_PROCLAIM_CHAMPION = 1951  # Spell_Holy_ProclaimChampion
_ICON_EMPOWER_CHAMPION = 1950   # Spell_Holy_EmpowerChampion
_ICON_RALLYING_CRY = 1934
_ICON_CRIPPLE = 96

_WAR_HORN_RADIUS = 10.0
_WARD_RADIUS = 8.0
_ORDERS_RADIUS = 30.0


def _raw(desc: str = '', aura_desc: str = '', spell_level: int = 0, **more) -> dict:
    return {'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': spell_level, 'CastingTimeIndex': 1,
            'Description_Lang_enUS': desc, 'AuraDescription_Lang_enUS': aura_desc, **_TEXT_MASKS, **more}


def _off_gcd() -> dict:
    return {'StartRecoveryCategory': 0, 'StartRecoveryTime': 0}


# =====================================================================================================================
# Overlord Wyrmthalak, the war horn

# --- Bloodaxe War Horn (trinket, Use) --------------------------------------------------------------------------------

bloodaxe_war_cry_206801 = spell(
    id=206801, name='Bloodaxe War Cry', school=School.NORMAL, attributes=_ATTR0_AURA_IS_DEBUFF, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=10000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=-11,
                    misc_value=_SCHOOL_MASK_ALL, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_DEMORALIZING_SHOUT,
    notes='Blackrock Spire hard mode, Bloodaxe War Horn: the war cry\'s weakness, cast on every enemy the horn reaches '
          '(triggered by 206800). The target deals 10% less damage in every school (MOD_DAMAGE_PERCENT_DONE, '
          'BasePoints -11 + DieSides 1), 10 s, a second horn refreshes it. AURA_IS_DEBUFF so it shows as a debuff. Not '
          'dispellable. Look: stock Demoralizing Shout SV 210.',
    raw_overrides=_raw('Deals $s1% less damage.', 'Weakened by a war cry. Deals less damage.',
                       SpellVisualID_1=_SV_DEMORALIZING_SHOUT),
)

bloodaxe_war_horn_206800 = spell(
    id=206800, name='Bloodaxe War Horn', school=School.NORMAL, cast_time_ms=0, cooldown_ms=120000,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=4000,
    effects=[
        Effect(type=EffectType.INTERRUPT_CAST, base_points=0, mechanic=_MECHANIC_INTERRUPT,
               implicit_target_a=_TARGET_SRC_CASTER, implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY,
               radius_yards=_WAR_HORN_RADIUS),
        Effect(type=EffectType.TRIGGER_SPELL, base_points=0, trigger_spell=bloodaxe_war_cry_206801.id,
               implicit_target_a=_TARGET_SRC_CASTER, implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY,
               radius_yards=_WAR_HORN_RADIUS),
    ],
    spell_icon_id=_ICON_HORN,
    notes='Blackrock Spire hard mode, Bloodaxe War Horn (Wyrmthalak hard mode trinket), the Use: 2 min cooldown, off '
          'the GCD, no cast time. Effect 1 interrupts the spellcasting of every enemy within 10 yd of the wearer '
          '(TARGET_SRC_CASTER / TARGET_UNIT_SRC_AREA_ENEMY, effect mechanic INTERRUPT like Pummel, so interrupt '
          'immunity applies); the interrupted school is locked out for the spell\'s duration, 4 s (a proposal: the '
          'doc says only "interrupts"; Pummel here is 6 s, Counterspell 4 s). Effect 2 triggers 206801 on the same '
          'enemies, which does not depend on the interrupt landing. Data only. Bots: UseTrinketAction refuses a '
          'spell that is not positive, so the horn is never used by a bot (see the STAGE-BRS report).',
    raw_overrides=_raw(
        'Sound a war cry that interrupts the spellcasting of enemies within $a1 yards, preventing any spell in that '
        'school from being cast for $d. Those enemies also deal $206801s1% less damage for $206801d.',
        SpellVisualID_1=_SV_BATTLE_SHOUT, **_off_gcd(),
    ),
)

# --- Ward of the Three Tribes (shield, Equip) ------------------------------------------------------------------------

ward_of_the_three_tribes_buff_206803 = spell(
    id=206803, name='Ward of the Three Tribes', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=3000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=-2,
                    misc_value=_SCHOOL_MASK_ALL, implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_SHIELD_WALL,
    notes='Blackrock Spire hard mode, Ward of the Three Tribes: the buff. -1% damage taken per stack in every school '
          '(MOD_DAMAGE_PERCENT_TAKEN, BasePoints -2 + DieSides 1; the engine multiplies the amount by the stacks), up '
          'to 5 stacks (CumulativeAura 5). 3 s, refreshed every 0.5 s by spell_brs_ward_of_the_three_tribes while at '
          'least one enemy within the radius is attacking the wearer; the script sets the stack count to the number of '
          'those enemies and removes the aura at none. Look: stock Shield Wall SV 345.',
    raw_overrides=_raw('Damage taken reduced by $s1% per stack.', 'The Three Tribes ward you. Damage taken reduced.',
                       CumulativeAura=5, SpellVisualID_1=_SV_SHIELD_WALL),
)

ward_of_the_three_tribes_206802 = spell(
    id=206802, name='Ward of the Three Tribes', school=School.NORMAL, attributes=_ATTR0_PASSIVE, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, base_points=4, amplitude=500,
                    implicit_target_a=_TARGET_UNIT_CASTER, radius_yards=_WARD_RADIUS)],
    spell_icon_id=_ICON_SHIELD_WALL,
    notes='Blackrock Spire hard mode, Ward of the Three Tribes (Wyrmthalak hard mode shield), the Equip: a passive '
          'PERIODIC_DUMMY aura every 0.5 s, amount 5 (BasePoints 4 + DieSides 1) = the stack cap, radius 8 yd. '
          'spell_brs_ward_of_the_three_tribes counts the enemies within the radius that are attacking the wearer '
          '(Unit::GetVictim) and holds that many stacks (at most the cap) of 206803.',
    raw_overrides=_raw(
        'You take $206803s1% less damage for each enemy within $a1 yards that is attacking you, up to $s1 enemies.'),
)
scripted_by(ward_of_the_three_tribes_206802, 'spell_brs_ward_of_the_three_tribes')

# --- Shardstaff of Stolen Power (staff, Equip) -----------------------------------------------------------------------

stolen_power_206805 = spell(
    id=206805, name='Stolen Power', school=School.ARCANE, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=0,
               misc_value=_SCHOOL_MASK_SPELLS, implicit_target_a=_TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_HEALING_DONE_PERCENT, base_points=0,
               implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_POWER_INFUSION,
    notes='Blackrock Spire hard mode, Shardstaff of Stolen Power: the buff. +1% spell damage (MOD_DAMAGE_PERCENT_DONE, '
          'every school but Physical: mask 126) and +1% healing done (BasePoints 0 + DieSides 1), 10 s, up to 5 stacks '
          '(CumulativeAura 5), each crit refreshes it. Triggered by 206804 on the wearer whatever the proc target '
          '(TARGET_UNIT_CASTER). Look: stock Power Infusion SV 7553.',
    raw_overrides=_raw('Spell damage and healing increased by $s1%.', 'Stolen Power. Spell damage and healing '
                       'increased.', CumulativeAura=5, SpellVisualID_1=_SV_POWER_INFUSION),
)

shardstaff_of_stolen_power_206804 = spell(
    id=206804, name='Shardstaff of Stolen Power', school=School.ARCANE, attributes=_ATTR0_PASSIVE, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PROC_TRIGGER_SPELL, base_points=0,
                    trigger_spell=stolen_power_206805.id, implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_ARCANE_POWER,
    notes='Blackrock Spire hard mode, Shardstaff of Stolen Power (Wyrmthalak hard mode staff), the Equip: a passive '
          'PROC_TRIGGER_SPELL aura that casts 206805. spell_proc: done harmful and helpful spells of the magic and '
          'none class (0x15400, damage or heal type, hit phase), CRITICAL hits only, 100%, no internal cooldown. '
          'Periodic '
          'ticks are not in the flags (a tick crit is no "spell critical strike" here; to change that add 0x40000). '
          'Data only.',
    raw_overrides=_raw(
        'Your spell critical strikes give Stolen Power, increasing your spell damage and healing done by '
        '$206805s1% for $206805d. Stacks up to $206805u times.',
        ProcTypeMask=_SPELL_CRITS, ProcChance=100,
    ),
)
procs_on(shardstaff_of_stolen_power_206804, proc_flags=_SPELL_CRITS,
         spell_type_mask=_PROC_SPELL_TYPE_DAMAGE | _PROC_SPELL_TYPE_HEAL, spell_phase_mask=_PROC_SPELL_PHASE_HIT,
         hit_mask=_PROC_HIT_CRITICAL, chance=100.0)

# =====================================================================================================================
# General Drakkisath, the General's Army

# --- Trophy of the Champion (trinket, Equip) -------------------------------------------------------------------------

champions_trophy_206808 = spell(
    id=206808, name="Champion's Trophy", school=School.HOLY, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=0,
               misc_value=_SCHOOL_MASK_ALL, implicit_target_a=_TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_HEALING_DONE_PERCENT, base_points=0,
               implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_EMPOWER_CHAMPION,
    notes='Blackrock Spire hard mode, Trophy of the Champion: the Trophy. +1% damage done (every school) and +1% '
          'healing done (BasePoints 0 + DieSides 1), 30 s, up to 5 stacks (CumulativeAura 5), each Trophy refreshes '
          'it. Cast by the wearer on themselves from spell_brs_champions_mark. Look: stock Warchief\'s Blessing SV '
          '4230.',
    raw_overrides=_raw('Damage and healing done increased by $s1%.', 'A Trophy of the Champion. Damage and healing '
                       'increased.', CumulativeAura=5, SpellVisualID_1=_SV_WARCHIEFS_BLESSING),
)

champions_mark_206807 = spell(
    id=206807, name="Champion's Mark", school=School.HOLY, attributes=_ATTR0_AURA_IS_DEBUFF, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=5000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_PROCLAIM_CHAMPION,
    notes='Blackrock Spire hard mode, Trophy of the Champion: "an enemy you damaged in the last 5 sec". A 5 s DUMMY '
          'debuff the wearer puts on every enemy they damage (triggered by 206806; each hit refreshes it, and each '
          'wearer owns their own mark). spell_brs_champions_mark: when the aura ends because the target died, the '
          'wearer, if still wearing the Trophy and alive, casts 206808 on themselves. Every other way the aura ends '
          '(it ran out, it was removed, the target evaded) gives nothing. Not shown to the target as a number.',
    raw_overrides=_raw(aura_desc='Marked by a champion.', AttributesEx4=_ATTR4_NO_CAST_LOG),
)
scripted_by(champions_mark_206807, 'spell_brs_champions_mark')

trophy_of_the_champion_206806 = spell(
    id=206806, name='Trophy of the Champion', school=School.HOLY, attributes=_ATTR0_PASSIVE, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PROC_TRIGGER_SPELL, base_points=0,
                    trigger_spell=champions_mark_206807.id, implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_CHAMPIONS_GRACE,
    notes='Blackrock Spire hard mode, Trophy of the Champion (Drakkisath hard mode trinket), the Equip: a passive '
          'PROC_TRIGGER_SPELL aura that casts the mark 206807 on the damaged target. spell_proc: every kind of damage '
          'the wearer does (melee and ranged auto attacks and class spells, harmful magic and none class spells, '
          'periodic ticks: 0x51154), damage type, hit phase, normal '
          'or critical, 100%, NO internal cooldown (a cooldown is per wearer, so an area attack would mark only one '
          'target). Known gap: an enemy killed by one hit of the wearer that nothing of theirs hit in the 5 s before '
          'is not marked in time and gives no Trophy.',
    raw_overrides=_raw(
        'When an enemy you damaged in the last $206807d dies, you gain a Trophy, increasing your damage and healing '
        'done by $206808s1% for $206808d. Stacks up to $206808u times.',
        ProcTypeMask=_ALL_DAMAGE, ProcChance=100,
    ),
)
procs_on(trophy_of_the_champion_206806, proc_flags=_ALL_DAMAGE, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=100.0)

# --- Orders of the General (held in off-hand, Use) -------------------------------------------------------------------

orders_of_the_general_206809 = spell(
    id=206809, name='Orders of the General', school=School.NORMAL, cast_time_ms=0, cooldown_ms=120000,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=8000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=-11,
                    misc_value=_SCHOOL_MASK_ALL, implicit_target_a=_TARGET_UNIT_CASTER_AREA_PARTY,
                    radius_yards=_ORDERS_RADIUS)],
    spell_icon_id=_ICON_RALLYING_CRY,
    notes='Blackrock Spire hard mode, Orders of the General (Drakkisath hard mode off-hand), the Use: 2 min cooldown, '
          'off the GCD. The wearer and the party members within 30 yd (TARGET_UNIT_CASTER_AREA_PARTY, the Paladin '
          'aura pattern) take 10% less damage in every school (BasePoints -11 + DieSides 1) for 8 s. Data only. '
          'Look: stock Battle Shout SV 246.',
    raw_overrides=_raw('Party members within $a1 yards take $s1% less damage for $d.',
                       'The General\'s orders. Damage taken reduced.', SpellVisualID_1=_SV_BATTLE_SHOUT,
                       **_off_gcd()),
)

# --- The Humbler (mace, Equip) ---------------------------------------------------------------------------------------

humbled_206811 = spell(
    id=206811, name='Humbled', school=School.NORMAL, attributes=_ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=8000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=-6,
                    misc_value=_SCHOOL_MASK_ALL, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_CRIPPLE,
    notes='Blackrock Spire hard mode, The Humbler: the debuff. The target deals 5% less damage in every school '
          '(MOD_DAMAGE_PERCENT_DONE, BasePoints -6 + DieSides 1), 8 s, a new proc refreshes it (it does not stack). '
          'Not dispellable. Look: stock Cripple SV 351.',
    raw_overrides=_raw('Deals $s1% less damage.', 'Humbled. Deals less damage.', SpellVisualID_1=_SV_CRIPPLE),
)

the_humbler_206810 = spell(
    id=206810, name='The Humbler', school=School.NORMAL, attributes=_ATTR0_PASSIVE, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PROC_TRIGGER_SPELL, base_points=0,
                    trigger_spell=humbled_206811.id, implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_CRIPPLE,
    notes='Blackrock Spire hard mode, The Humbler (Drakkisath hard mode mace), the Equip: a passive PROC_TRIGGER_SPELL '
          'aura that casts 206811 on the target. spell_proc: done melee auto attacks and melee-class spells (0x14), '
          'damage type, hit phase, normal or critical, 15%, no internal cooldown (the chance is the throttle; 8 s '
          'lasts about 16 hits). Data only.',
    raw_overrides=_raw(
        'Your melee hits have a chance to Humble the target, reducing the damage it deals by $206811s1% for '
        '$206811d.',
        ProcTypeMask=_MELEE_HITS, ProcChance=15,
    ),
)
procs_on(the_humbler_206810, proc_flags=_MELEE_HITS, spell_type_mask=_PROC_SPELL_TYPE_DAMAGE,
         spell_phase_mask=_PROC_SPELL_PHASE_HIT, hit_mask=_PROC_HIT_NORMAL_OR_CRITICAL, chance=15.0)
