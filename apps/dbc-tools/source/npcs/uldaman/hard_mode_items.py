"""
Uldaman item effects: the Waking Earthen the Waking Stone sends marching ahead of its wearer, look only. The spells are
source/items/uldaman_hard_mode_effects.py (the `uldaman_items` spell reservation 214680-214719); the creature is the
first of the same reservation's creature slice 301200-301204 (source/ids.yaml); 301201-301204 spare.

spell_uldaman_item_waking_stone (modules/mod-dungeon-bosses src/Uldaman/hard_mode_items.cpp) summons it 1 yd ahead of
the wearer and runs it (MovePoint, run) to the first obstacle or 20 yd ahead along the wearer's facing; the trample is
the wearer's own spell (214681), cast on the enemies its steps pass. It goes when it arrives, when the march's 4 sec run
out or when the wearer dies or leaves. It has no script and no AI of its own.

A look the players never target and that never takes part: not selectable and not attackable, friendly to all
(faction 35, so nothing aggroes on it and it aggroes nothing), no loot, no XP, no melee (DamageModifier 0), passive
(the script sets REACT_PASSIVE). Its own entry, never a stock earthen (7309, 7077, 7076: Archaedas's wall earthen and
Guardians, which the dungeon build drives as marchers) or a boss-kit unit. Model: the wall earthen's (display 6025,
creature_template_model 7309 and 7077) at 0.6 scale and its own name, so it never reads as one of Archaedas's marchers
(same model, full size) in the fight that drops the Stone. The dungeon build keys every marcher rule (registry, bots)
by its own entries, never by name or display. It runs at 8 yd per sec (speed_run 1.14286; the script sets run).
"""

from lib.dsl.registry import creature_model, creature_template

# The Deadmines boss-kit helper columns (source/npcs/deadmines/_common.py KIT_CREATURE + KIT_HELPER), copied as the
# Gnomeregan Launched Walking Bomb does: not selectable and not attackable (UNIT_FLAG_NON_ATTACKABLE 0x2 |
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

_TYPE_HUMANOID = 7              # the stock earthen's type
_DISPLAY_WALL_EARTHEN = 6025    # creature_template_model 7309 (Earthen Custodian) and 7077 (Earthen Hallshaper)

_EARTHEN_SCALE = 0.6  # smaller than Archaedas's marchers (1.0): the player's own, at a glance

waking_earthen_301200 = creature_template(301200, 'Waking Earthen', type=_TYPE_HUMANOID, **_HELPER)
creature_model(301200, display_id=_DISPLAY_WALL_EARTHEN, scale=_EARTHEN_SCALE, idx=0)
