"""
Scarlet Monastery item effects: the one summoned look of the hard mode items. The spells are
source/items/scarlet_monastery_hard_mode_effects.py (the `scarlet_monastery_items` spell reservation 212000-212099);
the creature sits in the same reservation's creature slice 300880-300889 (source/ids.yaml); 300881-300889 are spare.

- 300880 Rallying Standard: Galvar's banner, the Pureblood's Rallying Standard look.
  spell_sm_pureblood_rallying_standard (modules/mod-dungeon-bosses src/ScarletMonastery/hard_mode_items.cpp) plants it
  at the wearer's feet for the 15 sec of the Use (plus a short tail), rooted; the wearer's party members within 10 yd
  of it get Rallied (212001). Model: the stock Blessed Banner of the Crusade's (30891, display 27399), a Scarlet
  Crusade banner.

A look the players never target: not selectable and not attackable, friendly to all (faction 35), no loot, no XP, no
melee (DamageModifier 0), passive (the script sets REACT_PASSIVE and roots it). A look-alike entry, never the stock
30891 (an Ebon Hold quest creature).
"""

from lib.dsl.registry import creature_model, creature_template

# The Deadmines boss-kit helper columns (source/npcs/deadmines/_common.py KIT_CREATURE + KIT_HELPER), copied as the
# Blackrock Depths item looks do: not selectable and not attackable (UNIT_FLAG_NON_ATTACKABLE 0x2 |
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

_TYPE_NOT_SPECIFIED = 10

rallying_standard_300880 = creature_template(300880, 'Rallying Standard', **{**_HELPER, 'type': _TYPE_NOT_SPECIFIED})
creature_model(300880, display_id=27399, idx=0)
