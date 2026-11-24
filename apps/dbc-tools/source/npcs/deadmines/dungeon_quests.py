"""
Dungeon quests stage Q1 (.agents/plans/dungeon-quests/dungeon-quests.PLAN.md section 2): the two quest givers of the
Deadmines, People's Militia scouts, both in the `deadmines` creature reservation (spare 300431-300449, source/ids.yaml).

    300431  Scout Harlan   the entrance giver: starts all four dungeon quests (2040 Underground Assault, 214 Red Silk
                           Bandanas, 90100 The Juggernaut's Casting Plans, 90101 The Kingpin's Ledger) and ends them
    300432  Sergeant Wynne  the ship NPC: a plain static spawn at the end of the dungeon (no summon, no script), ends the
                           same four quests

Both are quest givers (npcflag 2) only, friendly to both factions (faction 35), civilians (flags_extra 2: they never
attack and are never attacked), level 20, no AI, no gossip, no loot. Looks: the stock People's Militia scouts' models
(Scout Galiaan 878 = display 2373, Captain Danuvin 821 = display 2372). The rows follow the Haunted set vendors'
(source/npcs/haunted_set/vendors.py), whose column set is Quartermaster Miranda Breechlock's without her gossip, quests
and SmartAI. The spawns (normal difficulty only, `spawnMask` 1), the quest starter and ender rows and the quests
themselves are the hand-written data/sql/updates/pending_db_world/rev_dungeon_quests_deadmines.sql; the row values
(positions, why) are in that file's header.
"""

from lib.dsl.registry import creature_model, creature_template

_GIVER = dict(
    IconName='', exp=0, faction=35, npcflag=2, minlevel=20, maxlevel=20, rank=0, unit_class=1, speed_walk=1.0,
    speed_run=1.14286, speed_swim=1.0, speed_flight=1.0, detection_range=18.0, dmgschool=0, DamageModifier=1.0,
    BaseAttackTime=2000, RangeAttackTime=2000, BaseVariance=1.0, RangeVariance=1.0, unit_flags=0, unit_flags2=2048,
    dynamicflags=0, family=0, type=7, type_flags=0, lootid=0, pickpocketloot=0, skinloot=0, PetSpellDataId=0,
    VehicleId=0, mingold=0, maxgold=0, AIName='', MovementType=0, HoverHeight=1.0, HealthModifier=1.0,
    ManaModifier=1.0, ArmorModifier=1.0, ExperienceModifier=1.0, RacialLeader=0, movementId=0, RegenHealth=1,
    CreatureImmunitiesId=0, flags_extra=2, ScriptName='', VerifiedBuild=0, gossip_menu_id=0,
)

entrance_giver_300431 = creature_template(
    300431, 'Scout Harlan', subname="The People's Militia", **_GIVER,
)
creature_model(300431, display_id=2373, idx=0)

ship_giver_300432 = creature_template(
    300432, 'Sergeant Wynne', subname="The People's Militia", **_GIVER,
)
creature_model(300432, display_id=2372, idx=0)
