"""
Deadmines Pilot WP-B4: Gilnid, the iron shot and the land mine
(.agents/plans/deadmines-pilot/deadmines-pilot.HANDOFF.md s3.4 rows GI, s3.5 row B4; build spec
docs/dungeons/deadmines-rework.md "Gilnid"). WP-B4 owns this file (its spells: 205270-205289 only).

- 1763 Gilnid: bound to boss_gilnid_rework (SmartAI off; his out of combat say and Molten Metal 5213 move into C++,
  the Foundry Door opens through the instance's door data), normal 10.7k (HealthModifier 22.0), the new stun immunity
  set. Heroic 311k is deadmines.py's override.
- 300423 iron shot, 300424 Goblin land mine: summoned helpers (not selectable, not attackable, no loot or XP). The
  mine uses the stock Goblin Land Mine display 6271 (creature 7527 has no spawns; its SmartAI is not reused).

Spells (modules/mod-dungeon-bosses/src/Deadmines/GilnidLogic.h `GilnidSpells` names the same ids):

  205270  Roll Out the Shot  GI2, the registry's resolve copy, Physical (a ball hitting someone in its lane); impact
                             visual SV 1564 (Cannon Ball 4170)
  205271  Bowled Over        GI3, the 2 s stun a ball puts on Gilnid: MOD_STUN with mechanic 0, so the stun immunity
                             set 1972 (mechanic STUN) does not stop it; SV 522 (Knockdown 5164). The script deals the
                             5% of his health itself (logged under this spell)
  205272  Hot Shot           GI4 heroic, the registry's resolve copy, Fire (a molten trail tick)
  205273  Land Mine          GI6/GI7 heroic, the registry's resolve copy, Fire (the mine's blast)
  205274  Roll Out the Shot  visual: the pot pours (SV 380, Molten Metal 5213), on the ball at the pot
  205275  Roll Out the Shot  visual: the ball leaves the pot (SV 8030, Flaming Cannonball 29639)
  205276  Red Hot            visual: the ball's glow, a hidden DUMMY aura (SV 4101, the look of Lava 16455; 16455
                             itself is a periodic damage aura, so it is copied, never cast)
  205277  Land Mine Arming   visual: the mine's arming look, a hidden DUMMY aura (SV 34, Land Mine Arming 11816)
  205278  Land Mine          visual: the mine's blast (SV 148, Detonation 4043)
  205279  Land Mine Fizzle   visual: the oldest mine fizzles at the cap (SV 1931, Spawn Smoke 10389)
  205280  Toss Landmine      visual: Gilnid tosses a mine (SV 74, Goblin Land Mine 4100)
  205281  Hot Shot           GI4 heroic, visual: the molten slag on a trail segment (a 6 s dynamic object at the
                             segment's middle, SV 90340, WP-V's goo_flow_stateyellow pool, PersistentAreaKit)
  205282-205289 spare.

Registry damage (Damage(pct) through the resolve copies) carries SPELL_ATTR3_IGNORE_CASTER_MODIFIERS like the
module's own resolve spells. Stock Molten Metal 5213 (GI1) stays: DD scales it on heroic.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR4_NO_CAST_LOG,
    IMMUNITY_BOSS_STUN,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TEXT_MASKS,
)

creature_template_columns(
    1763, ScriptName='boss_gilnid_rework', AIName='', HealthModifier=22.0, CreatureImmunitiesId=IMMUNITY_BOSS_STUN,
)

# The iron shot's display. PLACEHOLDER: 22814 (Spells\Meteor_Ball_Missile.mdx, a flaming ball; the no-patch fallback of
# handoff s3.10 gap 3b, no client patch needed). WP-V mints the stock demolisher cannonball as a new
# CreatureDisplayInfo in 90700-90719; the orchestrator repoints this one constant to it. Never 15435 (the Fiery
# Boulder's display is the invisible man, handoff s2.7).
IRON_SHOT_DISPLAY = 90700  # WP-V: stock demolishercannonball.m2 (placeholder was 22814)
LAND_MINE_DISPLAY = 6271    # stock Goblin Land Mine 7527

iron_shot_300423 = creature_template(
    300423, 'Iron Shot', **{**KIT_HELPER, 'minlevel': 20, 'maxlevel': 20, 'rank': 0, 'unit_class': 1, 'type': 10,
                            'ScriptName': 'npc_dm_iron_shot'},
)
creature_model(300423, display_id=IRON_SHOT_DISPLAY)

land_mine_300424 = creature_template(
    300424, 'Goblin Land Mine', **{**KIT_HELPER, 'minlevel': 20, 'maxlevel': 20, 'rank': 0, 'unit_class': 1,
                                   'type': 9, 'ScriptName': 'npc_dm_land_mine'},
)
creature_model(300424, display_id=LAND_MINE_DISPLAY)

_TARGET_SRC_CASTER = 22
_TARGET_UNIT_SRC_AREA_ENEMY = 15

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
_ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000

# Stock icons and visuals (DM "Visual sources", Spell.dbc 3.3.5).
_ICON_CANNON_BALL = 965     # Cannon Ball 4170
_ICON_KNOCKDOWN = 148       # Knockdown 5164
_ICON_MOLTEN = 12           # Molten Metal 5213
_ICON_FLAMING_BALL = 320    # Flaming Cannonball 29639
_ICON_FIRE = 11             # Lava 16455, Detonation 4043
_ICON_LAND_MINE = 90        # Goblin Land Mine 4100
_ICON_ARMING = 656          # Land Mine Arming 11816
_SV_CANNON_BALL = 1564      # Cannon Ball 4170 (the impact on a player the ball hits)
_SV_KNOCKDOWN = 522         # Knockdown 5164
_SV_POUR = 380              # Molten Metal 5213
_SV_LAUNCH = 8030           # Flaming Cannonball 29639
_SV_RED_HOT = 4101          # Lava 16455 (Immolate_State_Base)
_SV_ARMING = 34             # Land Mine Arming 11816
_SV_BLAST = 148             # Detonation 4043
_SV_FIZZLE = 1931           # Spawn Smoke 10389
_SV_TOSS = 74               # Goblin Land Mine 4100
# WP-V (patch_deadmines_vfx_models.py): the slag pool's area form, a PersistentAreaKit for a dynamic object. The
# StateKit form 90341 (an aura on a stalker) stays unused: a dynamic object needs no stalker.
_SV_HOT_SHOT_AREA = 90340
_TARGET_DEST_DYNOBJ_ENEMY = 28
_TARGET_FLAG_DEST_LOCATION = 0x40

_MECHANIC_NONE = 0

_RESOLVE_EXCLUDED = ('mod-boss-mechanics resolve copy: the damage is set per target by spell_boss_mechanics_resolve '
                     'from the reference-health provider')


def _raw(desc: str = '', aura_desc: str = '', **more) -> dict:
    return {'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': 0, 'CastingTimeIndex': 1,
            'Description_Lang_enUS': desc, 'AuraDescription_Lang_enUS': aura_desc, **TEXT_MASKS, **more}


def _resolve_copy(spell_id: int, name: str, school: School, icon: int, note: str, visual: int = 0):
    s = spell(
        id=spell_id, name=name, school=school, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
        mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=_TARGET_SRC_CASTER,
                        implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=100.0,
                        potency_excluded=_RESOLVE_EXCLUDED)],
        spell_icon_id=icon,
        notes=f'Deadmines Pilot WP-B4: {note} A dungeon copy of the mod-boss-mechanics resolve spell (205001-205007, '
              'source/npcs/boss_mechanics.py) with its exact attribute set, so the combat log names the mechanic: '
              'bound to spell_boss_mechanics_resolve, which filters the targets to the shape and sets the damage.',
        raw_overrides={
            'Attributes': _ATTR0_NO_ACTIVE_DEFENSE,
            'AttributesEx': _ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION | _ATTR1_NO_THREAT,
            'AttributesEx2': _ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
            'AttributesEx3': _ATTR3_NOT_A_PROC | _ATTR3_ALWAYS_HIT | _ATTR3_IGNORE_CASTER_MODIFIERS,
            'AttributesEx4': ATTR4_NO_CAST_LOG,
            'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'SpellClassSet': 0, 'SpellLevel': 0,
            'SpellVisualID_1': visual,
        },
    )
    scripted_by(s, 'spell_boss_mechanics_resolve')
    return s


def _self_visual(spell_id: int, name: str, school: School, visual: int, icon: int, note: str):
    return spell(
        id=spell_id, name=name, school=school, attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon,
        notes=f'Deadmines Pilot WP-B4: visual only. {note} Cast on itself, triggered; DUMMY with no handler, '
              'DO_NOT_DISPLAY | DO_NOT_LOG. Copies the stock visual, never the stock spell (DM implementation notes).',
        raw_overrides=_raw(SpellVisualID_1=visual, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


def _state_visual(spell_id: int, name: str, school: School, visual: int, icon: int, note: str):
    # Not passive: a passive aura is never sent to the client, so its state visual would not show (custom-spells.md).
    return spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0,
        attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon,
        notes=f'Deadmines Pilot WP-B4: visual only. {note} A hidden DUMMY aura the helper puts on itself at spawn '
              '(not passive, so the client gets it and plays the state visual), until it despawns. Copies the stock '
              'visual, never the stock spell.',
        raw_overrides=_raw(SpellVisualID_1=visual, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- GI2 Roll Out the Shot --------------------------------------------------------------------------------------------
roll_out_the_shot_205270 = _resolve_copy(
    205270, 'Roll Out the Shot', School.NORMAL, _ICON_CANNON_BALL,
    'GI2: a ball rolling through its 4 yd lane, 30% Physical (registry Damage) + Weakened on anyone it passes; impact '
    'SV 1564 (Cannon Ball 4170).', visual=_SV_CANNON_BALL)

shot_pour_205274 = _self_visual(
    205274, 'Roll Out the Shot', School.FIRE, _SV_POUR, _ICON_MOLTEN,
    'The pot pours (SV 380, Molten Metal 5213): the ball casts it as it appears at the pot, with the lane markers.')

shot_launch_205275 = _self_visual(
    205275, 'Roll Out the Shot', School.FIRE, _SV_LAUNCH, _ICON_FLAMING_BALL,
    'The ball leaves the pot (SV 8030, Flaming Cannonball 29639), when its marker ends and it starts to roll.')

red_hot_205276 = _state_visual(
    205276, 'Red Hot', School.FIRE, _SV_RED_HOT, _ICON_FIRE,
    'The iron shot glows red hot (SV 4101, the Immolate state of Lava 16455; 16455 is a periodic damage aura).')

# --- GI3 Bowled Over --------------------------------------------------------------------------------------------------
bowled_over_205271 = spell(
    id=205271, name='Bowled Over', school=School.NORMAL, dispel=0, mechanic=_MECHANIC_NONE,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=2000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, base_points=0,
                    mechanic=_MECHANIC_NONE, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_KNOCKDOWN,
    notes='Deadmines Pilot WP-B4: GI3, a reward. A ball rolling through Gilnid knocks him down: he casts this on '
          'himself, triggered (boss_gilnid_rework). MOD_STUN 2 s with mechanic 0 on the spell and the effect, so the '
          "bosses' stun immunity set 1972 (a mechanic mask) does not stop it (DM implementation notes: a scripted "
          'stun the boss suffers from the fight must bypass the immunity); NO_IMMUNITIES as well. The script deals '
          'the 5% of his health itself, logged under this spell. Knockdown look SV 522 (Knockdown 5164).',
    raw_overrides=_raw('Knocked down by a rolling iron shot. Lasts $d.', 'Knocked down.',
                       SpellVisualID_1=_SV_KNOCKDOWN),
)

# --- GI4 Hot shot -----------------------------------------------------------------------------------------------------
hot_shot_205272 = _resolve_copy(
    205272, 'Hot Shot', School.FIRE, _ICON_FIRE,
    'GI4 heroic: a molten trail tick, 5% Fire per second for 6 s (registry Persistent) + the Standing in It slow, '
    'no Weakened, on a 4 yd segment of the lane the ball just passed.')

hot_shot_ground_205281 = spell(
    id=205281, name='Hot Shot', school=School.FIRE, attributes=_ATTR0_DO_NOT_DISPLAY | ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=6000,
    effects=[Effect(type=EffectType.PERSISTENT_AREA_AURA, apply_aura=AuraType.DUMMY,
                    implicit_target_a=_TARGET_DEST_DYNOBJ_ENEMY, radius_yards=2.0)],
    spell_icon_id=_ICON_FIRE,
    notes='Deadmines Pilot WP-F (from WP-B4\'s offer), GI4 heroic: the look of a molten trail segment. Gilnid casts '
          'it (triggered) at the middle of each 4 yd segment as the segment registers; the dynamic object lives the '
          'segment\'s 6 s and carries WP-V\'s slag pool SV 90340 (PersistentAreaKit, goo_flow_stateyellow scaled to '
          '4 yd). The shape of Rhahk\'Zor\'s Cave In rocks 205212; its DUMMY aura is hidden and does nothing (the '
          'registry zone owns the damage and the slow).',
    raw_overrides=_raw('Molten slag.', SpellVisualID_1=_SV_HOT_SHOT_AREA, Targets=_TARGET_FLAG_DEST_LOCATION,
                       AttributesEx=_ATTR1_NO_THREAT, AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT,
                       AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- GI6 / GI7 Landmine -----------------------------------------------------------------------------------------------
land_mine_205273 = _resolve_copy(
    205273, 'Land Mine', School.FIRE, _ICON_LAND_MINE,
    'GI6/GI7 heroic: the mine goes off, 35% Fire + Weakened on everyone within 4 yd (registry Mine: anyone inside '
    'when it arms, a player inside for 0.5 s once armed, or a ball rolling over it).')

land_mine_arming_205277 = _state_visual(
    205277, 'Land Mine Arming', School.FIRE, _SV_ARMING, _ICON_ARMING,
    'The mine arming (SV 34, Land Mine Arming 11816).')

land_mine_blast_205278 = _self_visual(
    205278, 'Land Mine', School.FIRE, _SV_BLAST, _ICON_FIRE,
    'The mine blast (SV 148, Detonation 4043), when the registry resolves the mine (players or a ball).')

land_mine_fizzle_205279 = _self_visual(
    205279, 'Land Mine Fizzle', School.NORMAL, _SV_FIZZLE, _ICON_LAND_MINE,
    'The oldest mine fizzles harmlessly when a 7th is tossed (cap 6; SV 1931, Spawn Smoke 10389).')

toss_landmine_205280 = _self_visual(
    205280, 'Toss Landmine', School.NORMAL, _SV_TOSS, _ICON_LAND_MINE,
    'Gilnid tosses a mine (SV 74, Goblin Land Mine 4100), with the emote "Gilnid tosses a landmine!".')
