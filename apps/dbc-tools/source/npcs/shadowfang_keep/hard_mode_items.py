"""
Shadowfang Keep item effects (item variants, wave 1): the creature of the Archmage Arugal hard mode items. The spells
are source/items/shadowfang_keep_hard_mode_effects.py (the `shadowfang_items` spell reservation 205600-205619).

- 300460 Arugal's Voidwalker: the Arugal's Shadow Tome look. spell_sfk_arugals_shadow_tome (modules/mod-dungeon-bosses
  src/ShadowfangKeep/hard_mode_items.cpp) summons it at the wearer's target for 10 sec, at the wearer's level, passive;
  it chases the target and swings on every tick of the wearer's own triggered Arugal's Voidwalker (205602), which deals
  the damage, so the number scales with the wearer (potency). Never targetable or attackable, friendly to all
  (faction 35), no loot, no XP, no melee (DamageModifier 0); not a trigger (flags_extra 0x80 would hide it). Model:
  the stock Arugal's Voidwalker's (4627, display 1131). A look-alike entry, never the stock 4627: that one runs
  SmartAI and its death opens the Sorcerer's Gate in Shadowfang Keep.

The `shadowfang_items` creature reservation (300460-300464, source/ids.yaml) holds it.
"""

from lib.dsl.registry import creature_model, creature_template

# The Deadmines boss-kit helper columns (source/npcs/deadmines/_common.py KIT_CREATURE + KIT_HELPER), copied: a
# summoned look the players never target. Not selectable and not attackable (UNIT_FLAG_NON_ATTACKABLE 0x2 |
# UNIT_FLAG_NOT_SELECTABLE 0x02000000), no loot, no XP (flags_extra 0x40), no melee (DamageModifier 0).
_HELPER = dict(
    subname='', IconName='', exp=0, npcflag=0, speed_walk=1.0, speed_run=1.14286, speed_swim=1.0, speed_flight=1.0,
    detection_range=0.0, dmgschool=0, BaseAttackTime=2000, RangeAttackTime=2000, BaseVariance=1.0, RangeVariance=1.0,
    unit_flags=0x2 | 0x02000000, unit_flags2=2048, dynamicflags=0, family=0, type=3, type_flags=0, PetSpellDataId=0,
    VehicleId=0, MovementType=0, HoverHeight=1.0, HealthModifier=1.0, ManaModifier=1.0, ArmorModifier=1.0,
    DamageModifier=0.0, ExperienceModifier=1.0, RacialLeader=0, movementId=0, RegenHealth=1, CreatureImmunitiesId=0,
    flags_extra=0x40, AIName='', VerifiedBuild=0, lootid=0, pickpocketloot=0, skinloot=0, mingold=0, maxgold=0,
)

tome_voidwalker_300460 = creature_template(
    300460, "Arugal's Voidwalker", **{**_HELPER, 'faction': 35, 'minlevel': 60, 'maxlevel': 60, 'rank': 0,
                                      'unit_class': 1, 'ScriptName': ''},
)
creature_model(300460, display_id=1131, idx=0)
