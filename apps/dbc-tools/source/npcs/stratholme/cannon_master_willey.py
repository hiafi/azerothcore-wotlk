"""
Stratholme build WP-S5: Cannon Master Willey (10997), "a firing range, and you're the targets"
(.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.4 rows WY, s3.5 row S5, s3.6; build spec
docs/dungeons/stratholme-rework.md ST 1293-1502, WY1-WY10). WP-S5 owns this file (its spells: kSpellsWilley
206500-206519 in modules/mod-dungeon-bosses src/Stratholme/StratholmeRework.h only; WilleyLogic.h names the same ids;
no creature of its own: the riflemen are the stock 11054, the guns and the ball are gameobjects 301200-301202 in the
core SQL rev rev_cannon_master_willey_stratholme.sql).

- 10997 Cannon Master Willey: boss_cannon_master_willey_rework (SmartAI off; the SQL rev drops stock rows 10997 x7),
  normal HealthModifier 60.616 (185k on the level 60 warrior base 3,052), stun immune (1972), INSTANCE_BIND.
  DamageModifier 7: the live value, kept (two hatchets; WP-T tunes melee). Heroic health 230k and the tier's melee are
  WP-H's heroic template (source/world/dungeons/stratholme.py).
- 11054 Crimson Rifleman (his alone): npc_st_crimson_rifleman (SmartAI off: the SQL rev drops its 4 stock rows),
  HealthModifier 1.638269: ceil(3,052 x 1.638269) = 5,000 (level 60 warrior base). Heroic 7,000 is WP-H's override
  (stratholme.py, heroic entry 310177). Stock displays 10820-10823 and the stock Shoot 17353 kept.

Spells (looks from ._visuals, WP-V-2's WI_* picks; every look unconfirmed until seen in game):

  206500  Aim                    WY2 the red arrow over the marked player (DUMMY debuff, WI_AIM_ARROW, Tag: Arrow
                                 20374's state kit), put on by the rifleman; Fire removes it
  206501  Taking Aim             WY2 the aiming rifleman's own aura (DUMMY buff): the bots' first kill target
                                 (descriptor TargetEntry HasAura) and a cue in its buff row
  206502  Fire                   WY3 the volley hit: Physical, 15% / 20% of the reference row (kit
                                 spell_dungeon_refflat_damage, hundredths 1500, heroic MiscValueB 2000); DmgClass none
                                 and always hits: not avoidable (armor still applies, as on every Physical kit hit)
  206503  Holding Cannonball     WY5 -30% speed for 30 s (mechanic none: freedom effects do not drop the ball)
  206504  Cannon Shot            WY6 the loaded gun's shot at him, Fire, base point 0 from the script (5% of his max
                                 health, never lethal); Cannon Fire 17278's explosion (WI_MUZZLE_BLAST_ALT_2) on him
  206505  Shaken                 WY7 +10% damage taken a stack, 3 stacks, 15 s
  206506  Cannon Fire            WY8 the lane's hit (resolve copy, Fire, 40%), the explosion on every player hit
  206507  Barrage                WY9 a blast's hit (resolve copy, Fire, 30% + Weakened), the same explosion
  206508  Cannon Fire            WY8 / WY9 a floor burst down the lane as it fires (DUMMY at a point, the explosion)
  206509  Mercy                  the gold glow ring under Mercy (DUMMY aura on its stalker, WI_MERCY_GLOW)
  206510  Zeal                   the orange glow ring under Zeal (DUMMY aura on its stalker, WI_ZEAL_GLOW)
  206511-206519 spare

Creature 300610 (the orchestrator's grant from the wave 2 spare range): the invisible glow stalker Willey summons on
each gun's spot at the pull (npc_st_willey_glow, KIT_HELPER, trigger); no heroic template (a stalker).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_2,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_INVISIBLE_STALKER,
    WI_AIM_ARROW,
    WI_MERCY_GLOW,
    WI_MUZZLE_BLAST_ALT_2,
    WI_SHOOT_GUN,
    WI_ZEAL_GLOW,
)

_S5 = 'Stratholme build WP-S5 (Cannon Master Willey)'

_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000      # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map
_SCHOOL_MASK_ALL = 127

_ATTR0_DO_NOT_DISPLAY = 0x00000080
_ATTR0_DO_NOT_LOG = 0x00000100
_ATTR0_NO_ACTIVE_DEFENSE = 0x00200000
_ATTR1_NO_REDIRECTION = 0x00000008
_ATTR1_NO_REFLECTION = 0x00000080
_ATTR1_NO_THREAT = 0x00000400
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_NOT_A_PROC = 0x00000200
_ATTR3_ALWAYS_HIT = 0x00040000

_ICON_ARROW = 1             # generic
_ICON_SHOOT = 1             # generic (no stock gun icon id read)
_ICON_CANNON = 1            # generic
_ICON_SHAKEN = 1            # generic

_VOLLEY_NORMAL_HUNDREDTHS = 1500     # WilleyLogic.h kVolleyPct.normal (15%)
_VOLLEY_HEROIC_HUNDREDTHS = 2000     # kVolleyPct.heroic (20%)
_SCRIPT_EXCLUDED = 'Stratholme: a percent of reference health, set by the script (DungeonKit::RefFlat)'
_SCRIPT_SHOT = 'Stratholme: 5% of his own maximum health, base point 0 set by boss_cannon_master_willey_rework'

# Held back until wave 2 binds this boss (_common.py BIND_WAVE_2). DamageModifier: stock 3.5, not the live 7 the
# retired mod-progression left (F-2 ruling; S4/S6/S7 precedent).
if BIND_WAVE_2:
    creature_template_columns(10997, **boss_columns(
        'boss_cannon_master_willey_rework', 60.616, damage_modifier=3.5,
    ))

    # 11054 Crimson Rifleman: 5,000 on normal (ceil(3,052 x 1.638269) = 5,000).
    creature_template_columns(11054, ScriptName='npc_st_crimson_rifleman', AIName='', HealthModifier=1.638269)

    # --- WY2 Aim -----------------------------------------------------------------------------------------------------

    aim_206500 = spell(
        id=206500, name='Aim', school=School.NORMAL, dispel=0, mechanic=0,
        attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=4000,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=_ICON_ARROW,
        notes=f'{_S5}, WY2 Aim: a rifleman of a formed rank marks a random player (distinct while there are enough; '
              'boss_cannon_master_willey_rework drives it) 6 s (heroic 4 s) after the rank forms, with Willey\'s '
              '"Aim!". The red arrow over the head is Tag: Arrow 20374\'s state kit (WI_AIM_ARROW, SV 5646). 4 s, '
              'longer than the 3 s (heroic 2 s) to Fire, which removes it; the rifleman\'s death removes it too. '
              'Dispel none, NO_IMMUNITIES; CHANGE_MAP drops it on leaving.',
        raw_overrides=kit_raw('Marks an enemy for the rifle volley.', 'A Crimson Rifleman has you in his sights. '
                              'Kill him before he fires.', CastingTimeIndex=1, SpellVisualID_1=WI_AIM_ARROW,
                              AttributesEx=_ATTR1_NO_THREAT, AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT,
                              AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )

    taking_aim_206501 = spell(
        id=206501, name='Taking Aim', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=4000,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_ARROW,
        notes=f'{_S5}, WY2 Aim: the aiming rifleman\'s own aura, cast on itself (triggered) beside Aim; Fire or its '
              'death ends it. The bots\' kill order reads it (descriptor TargetEntry(11054, 3, HasAura(206501)) above '
              'the plain rifleman, priority 2); players see it in its buff row. It does not shoot its stock Shoot '
              'while it carries it. No look.',
        raw_overrides=kit_raw('Takes aim.', 'Taking aim.', instant=True, AttributesEx=_ATTR1_NO_THREAT,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )

    # --- WY3 Fire ----------------------------------------------------------------------------------------------------

    fire_206502 = spell(
        id=206502, name='Fire', school=School.NORMAL, attributes=_ATTR0_NO_ACTIVE_DEFENSE, cast_time_ms=0,
        cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=_VOLLEY_NORMAL_HUNDREDTHS - 1, die_sides=1,
                        implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_EXCLUDED)],
        spell_icon_id=_ICON_SHOOT,
        notes=f'{_S5}, WY3 Fire: an aiming rifleman shoots its mark 3 s (heroic 2 s) after Aim, with Willey\'s '
              '"Fire!": 15% (heroic 20%) of the reference row, the tank row on the tank (the kit\'s '
              'spell_dungeon_refflat_damage reads the hundredths: shown value 1500, EffectMiscValueB 2000 on heroic). '
              'Not avoidable: DmgClass none (no dodge, parry or miss), always hits, ignores line of sight; it ignores '
              'caster modifiers and cannot crit. Physical, so armor applies (as on the kit\'s other Physical hits). A '
              'stunned, feared or polymorphed rifleman does not fire (the script). The bullet: the stock "Shoot Gun" look WI_SHOOT_GUN '
              '(SV 10208) at 40 yd/s (unchecked).',
        raw_overrides=kit_raw('Fires a rifle shot at the marked enemy.', instant=True, DefenseType=0, Speed=40.0,
                              SpellVisualID_1=WI_SHOOT_GUN, EffectMiscValueB_1=_VOLLEY_HEROIC_HUNDREDTHS,
                              AttributesEx=_ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION,
                              AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
                              AttributesEx3=_ATTR3_NOT_A_PROC | _ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )
    scripted_by(fire_206502, 'spell_dungeon_refflat_damage')

    # --- WY5 Holding Cannonball --------------------------------------------------------------------------------------

    holding_206503 = spell(
        id=206503, name='Holding Cannonball', school=School.NORMAL, dispel=0, mechanic=0,
        attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=30000,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DECREASE_SPEED, base_points=-31,
                        die_sides=1, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_CANNON,
        notes=f'{_S5}, WY5 Holding Cannonball: the carrier casts it on itself (triggered) on picking up a dropped ball '
              '(walk-over, one a player, never the tank). -30% movement speed for 30 s; when it runs out the ball is '
              'lost. Loading a gun (2 s in its load spot, WY6) removes it. Mechanic none, so Hand of Freedom and '
              'the like do not knock the ball loose; Dispel none. Leaving the map drops it (CHANGE_MAP). No look.',
        raw_overrides=kit_raw('Carrying a heavy cannonball.', 'Carrying a cannonball. Bring it to Mercy or Zeal '
                              'before it slips from your grip.', CastingTimeIndex=1, AttributesEx=_ATTR1_NO_THREAT,
                              AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )

    # --- WY6 the shot, WY7 Shaken ------------------------------------------------------------------------------------

    cannon_shot_206504 = spell(
        id=206504, name='Cannon Shot', school=School.FIRE, attributes=_ATTR0_NO_ACTIVE_DEFENSE, cast_time_ms=0,
        cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, implicit_target_a=TARGET_UNIT_CASTER,
                        potency_excluded=_SCRIPT_SHOT)],
        spell_icon_id=_ICON_CANNON,
        notes=f'{_S5}, WY6 Load: a carrier stood 2 s at Mercy or Zeal; the gun plays its firing animation and Willey '
              'takes the shot, cast by himself on himself (triggered, base point 0 from the script): 5% of his '
              'maximum health (9,250 normal / 11,500 heroic), divided by the Shaken he already carries so the hit '
              'stays 5%, and never the killing blow (it leaves him at 1 health at worst). Ignores caster modifiers, '
              'always hits, cannot crit, no threat. Cannon Fire 17278\'s explosion (WI_MUZZLE_BLAST_ALT_2, SV 30) on '
              'him.',
        raw_overrides=kit_raw('A loaded cannon fires point-blank.', instant=True, DefenseType=0,
                              SpellVisualID_1=WI_MUZZLE_BLAST_ALT_2,
                              AttributesEx=_ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION | _ATTR1_NO_THREAT,
                              AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
                              AttributesEx3=_ATTR3_NOT_A_PROC | _ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )

    shaken_206505 = spell(
        id=206505, name='Shaken', school=School.NORMAL, dispel=0, mechanic=0,
        attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=15000,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=10,
                        die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                        potency_excluded='Shaken: a flat +10% damage taken a stack, not a damage or heal value')],
        spell_icon_id=_ICON_SHAKEN,
        notes=f'{_S5}, WY7 Shaken: each load adds a stack on him (DungeonKit::AddStacks, which refreshes the 15 s), up '
              'to 3: +10% damage taken from every school a stack. A debuff on him, so the group reads the count in '
              'his debuff row; dispel none. Removed on his reset. No look of its own (the shot is the look).',
        raw_overrides=kit_raw('Increases damage taken.', 'Damage taken increased.', instant=True, CumulativeAura=3,
                              AttributesEx=_ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )

    # --- WY8 Cannon Fire, WY9 the Barrage ----------------------------------------------------------------------------

    cannon_fire_206506 = resolve_copy(
        206506, 'Cannon Fire', School.FIRE, 'A cannon fires down its half of the hall.',
        f'{_S5}, WY8 Cannon Fire (normal): he calls Mercy or Zeal (yell line 4 / 5) and the gun fires down its half of '
        'the hall, the full length (a 58 x 10 yd line on the hall frame, 2.5 s marker): 40% of the non-tank row, no '
        'Weakened, tank included. Resolve copy (Fire) of the mod-boss-mechanics spell 205001. Cannon Fire 17278\'s '
        'explosion (WI_MUZZLE_BLAST_ALT_2, SV 30) on every player hit.',
        visual=WI_MUZZLE_BLAST_ALT_2,
    )

    barrage_206507 = resolve_copy(
        206507, 'Barrage', School.FIRE, 'A cannon blast sweeps its half of the hall.',
        f'{_S5}, WY9 the Barrage (heroic): five blasts on the halves, 1.5 s apart, three on one half and two on the '
        'other, the order called as a boss emote 3 s before the first; no marker (NoTelegraph, ruling 23). Each: 30% '
        'of the non-tank row + 1 Weakened. Resolve copy (Fire). The explosion (WI_MUZZLE_BLAST_ALT_2, SV 30) on '
        'every player hit.',
        visual=WI_MUZZLE_BLAST_ALT_2,
    )

    blast_look_206508 = spell(
        id=206508, name='Cannon Fire', school=School.FIRE, attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
        spell_icon_id=_ICON_CANNON,
        notes=f'{_S5}, WY8 / WY9: the impact down a lane as it fires, cast by him (triggered) at four points down the '
              'fired half (frame X 16, 28, 40, 52). Cannon Fire 17278\'s Bomb_ExplosionA (WI_MUZZLE_BLAST_ALT_2, SV '
              '30) at the point (unchecked whether a dest-only spell plays it). Look only.',
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=WI_MUZZLE_BLAST_ALT_2,
                              Targets=_TARGET_FLAG_DEST_LOCATION, AttributesEx=_ATTR1_NO_THREAT,
                              AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )

    # --- The guns' glow rings ------------------------------------------------------------------------------------

    _FLAGS_EXTRA_NO_XP = 0x40
    _FLAGS_EXTRA_TRIGGER = 0x80

    gun_glow_300610 = creature_template(
        300610, 'Cannon Glow', **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1,
                                  'type': 10, 'flags_extra': _FLAGS_EXTRA_NO_XP | _FLAGS_EXTRA_TRIGGER,
                                  'ScriptName': 'npc_st_willey_glow'},
    )
    creature_model(300610, display_id=DISPLAY_INVISIBLE_STALKER)

    def _glow(spell_id: int, gun: str, visual: int, look: str):
        return spell(
            id=spell_id, name=gun, school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
            category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
            effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                            implicit_target_a=TARGET_UNIT_CASTER)],
            spell_icon_id=_ICON_CANNON,
            notes=f'{_S5}: {gun}\'s glow ring, a DUMMY aura the stalker 300610 casts on itself (triggered) as Willey '
                  f'summons it on the gun\'s spot at the pull ({look}). It names the gun on the floor beside the '
                  'yell and the object name (VISUALS-REPORT "Mercy and Zeal", rank 1); it reaches nobody. The '
                  'stalker despawns with his summons on his reset and death, which ends it.',
            raw_overrides=kit_raw(f'{gun}\'s glow.', f'{gun}\'s glow.', instant=True, SpellVisualID_1=visual,
                                  AttributesEx=_ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
        )

    mercy_glow_206509 = _glow(206509, 'Mercy', WI_MERCY_GLOW,
                              'WI_MERCY_GLOW: Holy Zone Visual 70571\'s gold HolyZone disc, about 3.3 yd, STATE')
    zeal_glow_206510 = _glow(206510, 'Zeal', WI_ZEAL_GLOW,
                             'WI_ZEAL_GLOW: Combustion Periodic 74629\'s orange FlameZone disc, about 3.7 yd, STATE')
