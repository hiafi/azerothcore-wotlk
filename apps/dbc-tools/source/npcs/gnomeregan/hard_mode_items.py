"""
Gnomeregan item effects: the Launched Walking Bomb the Walking Bomb Launcher sends at its target, look only. The
spells are source/items/gnomeregan_hard_mode_effects.py (the `gnomeregan_items` spell reservation 214240-214279); the
creature is the first of the same reservation's creature slice 301100-301104 (source/ids.yaml); 301101-301104 spare.

spell_gnomer_item_walking_bomb_launcher (modules/mod-dungeon-bosses src/Gnomeregan/hard_mode_items.cpp) summons it
beside the wearer and runs it at the target (MoveFollow: a chase never starts without a victim, and this bomb has
none); spell_gnomer_item_walking_bomb blows it when it arrives (the blast is the wearer's own spell, 214244) or makes
it fall apart when the mark ends. It has no script and no AI of its own.

A look the players never target and that never takes part: not selectable and not attackable, friendly to all
(faction 35, so nothing aggroes on it and it aggroes nothing), no loot, no XP, no melee (DamageModifier 0), passive
(the script sets REACT_PASSIVE). Its own entry, never the stock Walking Bomb 7915 (Thermaplugg's) or the dungeon
build's boss-kit bombs. Model: the stock Walking Bomb's (creature_template_model 7915, display 6977) at 0.6 scale,
and its own name, so it never reads as Thermaplugg's hostile Walking Bomb (same model, full size) in the fight that
drops the gun. The dungeon build keys every Walking Bomb rule (registry, bots, kill order) by the boss-kit entry, never
by name or display. It runs at 8 yd per sec (speed_run 1.14286; the script sets run and does not inherit the target's
speed; the stock bomb runs at 6).
"""

from lib.dsl.registry import creature_model, creature_template

# The Deadmines boss-kit helper columns (source/npcs/deadmines/_common.py KIT_CREATURE + KIT_HELPER), copied as the
# Zul'Farrak crew does: not selectable and not attackable (UNIT_FLAG_NON_ATTACKABLE 0x2 | UNIT_FLAG_NOT_SELECTABLE
# 0x02000000), no loot, no XP (flags_extra 0x40), no melee (DamageModifier 0).
_HELPER = dict(
    subname='', IconName='', exp=0, npcflag=0, speed_walk=1.0, speed_run=1.14286, speed_swim=1.0, speed_flight=1.0,
    detection_range=0.0, dmgschool=0, BaseAttackTime=2000, RangeAttackTime=2000, BaseVariance=1.0, RangeVariance=1.0,
    unit_flags=0x2 | 0x02000000, unit_flags2=2048, dynamicflags=0, family=0, type_flags=0, PetSpellDataId=0,
    VehicleId=0, MovementType=0, HoverHeight=1.0, HealthModifier=1.0, ManaModifier=1.0, ArmorModifier=1.0,
    DamageModifier=0.0, ExperienceModifier=1.0, RacialLeader=0, movementId=0, RegenHealth=1, CreatureImmunitiesId=0,
    flags_extra=0x40, AIName='', VerifiedBuild=0, lootid=0, pickpocketloot=0, skinloot=0, mingold=0, maxgold=0,
    faction=35, minlevel=60, maxlevel=60, rank=0, unit_class=1, ScriptName='',
)

_TYPE_MECHANICAL = 9
_DISPLAY_WALKING_BOMB = 6977  # creature_template_model 7915

_BOMB_SCALE = 0.6  # smaller than the stock bomb (1.0): the player's own, at a glance

launcher_walking_bomb_301100 = creature_template(301100, 'Launched Walking Bomb', type=_TYPE_MECHANICAL, **_HELPER)
creature_model(301100, display_id=_DISPLAY_WALKING_BOMB, scale=_BOMB_SCALE, idx=0)
