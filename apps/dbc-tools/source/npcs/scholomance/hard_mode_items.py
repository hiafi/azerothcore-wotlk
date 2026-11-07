"""
Scholomance item effects (item variants, wave 1): the creature of the Darkmaster Gandling hard mode items. The spells
are source/items/scholomance_hard_mode_effects.py (the `scholomance_items` spell reservation 205620-205659); the
creature sits in the `scholomance_items` creature slice 300465-300469 (source/ids.yaml).

- 300465 Darkmaster's Portal: the Darkmaster's Portal Rod look. spell_scholo_darkmasters_portal_rod
  (modules/mod-dungeon-bosses src/Scholomance/scholomance_items.cpp) summons it behind the wearer's target for the
  barrage (3 sec, plus a short tail), facing the target, and it carries the stock Summoning Portal ground look 205642.
  The wearer's own triggered Portal Barrage (205641) deals the damage, so the number scales with the wearer (potency).
  Never targetable or attackable, friendly to all (faction 35), no loot, no XP, no melee (DamageModifier 0), rooted
  (it never moves). Model: the stock Portal of Shadows' (16420, display 9510), the demon portal swirl.
"""

from lib.dsl.registry import creature_model, creature_template

# The Deadmines boss-kit helper columns (source/npcs/deadmines/_common.py KIT_CREATURE + KIT_HELPER), copied: a
# summoned look the players never target. Not selectable and not attackable (UNIT_FLAG_NON_ATTACKABLE 0x2 |
# UNIT_FLAG_NOT_SELECTABLE 0x02000000), no loot, no XP (flags_extra 0x40), no melee (DamageModifier 0).
_HELPER = dict(
    subname='', IconName='', exp=0, npcflag=0, speed_walk=1.0, speed_run=1.14286, speed_swim=1.0, speed_flight=1.0,
    detection_range=0.0, dmgschool=0, BaseAttackTime=2000, RangeAttackTime=2000, BaseVariance=1.0, RangeVariance=1.0,
    unit_flags=0x2 | 0x02000000, unit_flags2=2048, dynamicflags=0, family=0, type=10, type_flags=0, PetSpellDataId=0,
    VehicleId=0, MovementType=0, HoverHeight=1.0, HealthModifier=1.0, ManaModifier=1.0, ArmorModifier=1.0,
    DamageModifier=0.0, ExperienceModifier=1.0, RacialLeader=0, movementId=0, RegenHealth=1, CreatureImmunitiesId=0,
    flags_extra=0x40, AIName='', VerifiedBuild=0, lootid=0, pickpocketloot=0, skinloot=0, mingold=0, maxgold=0,
)

darkmasters_portal_300465 = creature_template(
    300465, "Darkmaster's Portal", **{**_HELPER, 'faction': 35, 'minlevel': 60, 'maxlevel': 60, 'rank': 0,
                                      'unit_class': 1, 'ScriptName': ''},
)
creature_model(300465, display_id=9510, idx=0)
