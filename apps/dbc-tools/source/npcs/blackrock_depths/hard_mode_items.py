"""
Blackrock Depths item effects (wave 2 dungeon items): the two summoned looks of the hard mode items. The spells are
source/items/blackrock_depths_hard_mode_effects.py (the `blackrock_depths_items` spell reservation 206830-206899); the
creatures sit in the same reservation's creature slice 300655-300669 (source/ids.yaml); 300657-300669 are spare.

- 300655 Lava Spawn: the Scepter of the Molten Lake look. spell_brd_scepter_of_the_molten_lake
  (modules/mod-dungeon-bosses src/BlackrockDepths/hard_mode_items.cpp) summons it beside the wearer for 10 sec (plus a
  short tail); it follows the wearer and, on every tick of the wearer's own Lava Spawn buff (206840), faces the
  wearer's target and plays its cast while the wearer's triggered Molten Hurl (206841) deals the damage, so the number
  scales with the wearer (potency). Model: the stock Lava Spawn's (12265, display 2172).
- 300656 Mending Servo: the Golemwright's Mending Rod look. spell_brd_golemwrights_mending_rod deploys it at the
  healed target for 10 sec (plus a short tail), rooted; on every tick of the healer's Mending Servo buff (206845) it
  plays its cast while the healer's triggered Servo Mend (206846) heals the most injured group member near it. Model:
  the stock Field Repair Bot 74A's (14337, display 14379).

Both are looks the players never target: not selectable and not attackable, friendly to all (faction 35), no loot, no
XP, no melee (DamageModifier 0), passive (the scripts set REACT_PASSIVE). Look-alike entries, never the stock 12265 /
14337 (12265 is a Molten Core add with its own AI and loot).
"""

from lib.dsl.registry import creature_model, creature_template

# The Deadmines boss-kit helper columns (source/npcs/deadmines/_common.py KIT_CREATURE + KIT_HELPER), copied as the
# Scholomance and Shadowfang Keep item looks do: not selectable and not attackable (UNIT_FLAG_NON_ATTACKABLE 0x2 |
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

_TYPE_ELEMENTAL = 4
_TYPE_MECHANICAL = 9

lava_spawn_300655 = creature_template(300655, 'Lava Spawn', **{**_HELPER, 'type': _TYPE_ELEMENTAL})
creature_model(300655, display_id=2172, idx=0)

mending_servo_300656 = creature_template(300656, 'Mending Servo', **{**_HELPER, 'type': _TYPE_MECHANICAL})
creature_model(300656, display_id=14379, idx=0)
