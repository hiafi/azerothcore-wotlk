"""
Zul'Farrak item effects: the five summoned looks of Sergeant's Whistle, Sergeant Bly's crew. The spells are
source/items/zul_farrak_hard_mode_effects.py (the `zul_farrak_items` spell reservation 213800-213839); the creatures
fill the same reservation's creature slice 301000-301004 (source/ids.yaml).

spell_zf_sergeants_whistle (modules/mod-dungeon-bosses src/ZulFarrak/hard_mode_items.cpp) summons all five around the
wearer for the 12 sec of the Use (plus a short tail); they follow the wearer and Murta plays a cast on each copied heal.
The heal itself (213807) is the wearer's. Models: the stock crew's (7604-7608); their weapons are set by the script.

Looks the players never target: not selectable and not attackable, friendly to all (faction 35), no loot, no XP, no
melee (DamageModifier 0), passive (the script sets REACT_PASSIVE). Look-alike entries, never the stock 7604-7608 (the
Test's bosses and the hard mode's allies).
"""

from lib.dsl.registry import creature_model, creature_template

# The Deadmines boss-kit helper columns (source/npcs/deadmines/_common.py KIT_CREATURE + KIT_HELPER), copied as the
# Scarlet Monastery item look does: not selectable and not attackable (UNIT_FLAG_NON_ATTACKABLE 0x2 |
# UNIT_FLAG_NOT_SELECTABLE 0x02000000), no loot, no XP (flags_extra 0x40), no melee (DamageModifier 0).
_HELPER = dict(
    subname='', IconName='', exp=0, npcflag=0, speed_walk=1.0, speed_run=1.14286, speed_swim=1.0, speed_flight=1.0,
    detection_range=0.0, dmgschool=0, BaseAttackTime=2000, RangeAttackTime=2000, BaseVariance=1.0, RangeVariance=1.0,
    unit_flags=0x2 | 0x02000000, unit_flags2=2048, dynamicflags=0, family=0, type_flags=0, PetSpellDataId=0,
    VehicleId=0, MovementType=0, HoverHeight=1.0, HealthModifier=1.0, ManaModifier=1.0, ArmorModifier=1.0,
    DamageModifier=0.0, ExperienceModifier=1.0, RacialLeader=0, movementId=0, RegenHealth=1, CreatureImmunitiesId=0,
    flags_extra=0x40, AIName='', VerifiedBuild=0, lootid=0, pickpocketloot=0, skinloot=0, mingold=0, maxgold=0,
    faction=35, minlevel=60, maxlevel=60, rank=0, unit_class=1, ScriptName='',
)

_TYPE_HUMANOID = 7
_CREW = {**_HELPER, 'type': _TYPE_HUMANOID}

crew_bly_301000 = creature_template(301000, 'Sergeant Bly', **_CREW)
creature_model(301000, display_id=6433, idx=0)

crew_raven_301001 = creature_template(301001, 'Raven', **_CREW)
creature_model(301001, display_id=6435, idx=0)

crew_oro_301002 = creature_template(301002, 'Oro Eyegouge', **_CREW)
creature_model(301002, display_id=6432, idx=0)

crew_weegli_301003 = creature_template(301003, 'Weegli Blastfuse', **_CREW)
creature_model(301003, display_id=7222, idx=0)

crew_murta_301004 = creature_template(301004, 'Murta Grimgut', **_CREW)
creature_model(301004, display_id=6438, idx=0)
