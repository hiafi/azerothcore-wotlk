"""
Dungeon quests stage Q2 (.agents/plans/dungeon-quests/dungeon-quests.PLAN.md section 3): the entrance quest giver of
Shadowfang Keep, a Kirin Tor mage from Dalaran, in the `shadowfang_keep` creature reservation (spare 300517-300529,
source/ids.yaml).

    300517  Magus Aldren Voss  starts all four dungeon quests (1098 Deathstalkers in Shadowfang, 1013 The Book of Ur,
                               1014 Arugal Must Die, 90110 The Baron's Rest) and ends 1013, 1014 and 90110. He does not
                               end 1098: Deathstalker Vincent (4444, inside) stays its only ender, as stock (designer
                               2026-11-23).

A quest giver (npcflag 2) only, friendly to both factions (faction 35), a civilian (flags_extra 2: never attacks, never
attacked), level 24, no AI, no gossip, no loot. Arugal was a Dalaran mage and Dalar Dawnweaver (Silverpine) already hunts
him for Dalaran, so the entrance giver is the Kirin Tor's. The look is the stock Kirin Tor Mage's (20422, display 19612:
a human male in the Dalaran robes). The row follows the Deadmines quest givers' (source/npcs/deadmines/dungeon_quests.py)
column set. The spawn (normal difficulty only, `spawnMask` 1), the quest starter and ender rows and the quest itself are
the hand-written data/sql/updates/pending_db_world/rev_dungeon_quests_shadowfang_keep.sql; the row values (position, why)
are in that file's header.
"""

from lib.dsl.registry import creature_model, creature_template

_GIVER = dict(
    IconName='', exp=0, faction=35, npcflag=2, minlevel=24, maxlevel=24, rank=0, unit_class=8, speed_walk=1.0,
    speed_run=1.14286, speed_swim=1.0, speed_flight=1.0, detection_range=18.0, dmgschool=0, DamageModifier=1.0,
    BaseAttackTime=2000, RangeAttackTime=2000, BaseVariance=1.0, RangeVariance=1.0, unit_flags=0, unit_flags2=2048,
    dynamicflags=0, family=0, type=7, type_flags=0, lootid=0, pickpocketloot=0, skinloot=0, PetSpellDataId=0,
    VehicleId=0, mingold=0, maxgold=0, AIName='', MovementType=0, HoverHeight=1.0, HealthModifier=1.0,
    ManaModifier=1.0, ArmorModifier=1.0, ExperienceModifier=1.0, RacialLeader=0, movementId=0, RegenHealth=1,
    CreatureImmunitiesId=0, flags_extra=2, ScriptName='', VerifiedBuild=0, gossip_menu_id=0,
)

entrance_giver_300517 = creature_template(
    300517, 'Magus Aldren Voss', subname='Kirin Tor', **_GIVER,
)
creature_model(300517, display_id=19612, idx=0)
