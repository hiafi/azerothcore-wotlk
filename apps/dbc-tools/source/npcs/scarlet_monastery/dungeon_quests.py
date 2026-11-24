"""
Dungeon quests stage Q3 (.agents/plans/dungeon-quests/dungeon-quests.PLAN.md section 5): the four Argent Dawn agents of
the Scarlet Monastery, one at each wing's entrance, in the `scarlet_monastery` creature reservation's spare 300923-
300939 (source/ids.yaml). Each gives and ends only the quests with an objective in its wing:

    300923  Agent Corwin Hale          Graveyard  level 31   1113 Hearts of Zeal
    300924  Archivist Tobias Merrow    Library    level 34   1113, 1049 Compendium of the Fallen, 1050 Mythology of the
                                                             Titans, 1048 Into The Scarlet Monastery
    300925  Captain Dorrin Ashe        Armory     level 36   1113, 1048
    300926  Father Anselm Gray         Cathedral  level 39   1113, 1053 In the Name of the Light

Quest givers (npcflag 2) only, friendly to both factions (faction 35), civilians (flags_extra 2: never attack, never
attacked), no AI, no gossip, no loot. The levels are the wings' Finder targets
(docs/dungeons/scarlet-monastery-rework.md "Sections": 31, 34, 36, 39). The subname is the stock Argent Dawn one; each look is a stock Argent Dawn human, none
shared: Dawnwatcher Selgorm (4783, display 5226), the Keeper of the Rolls (16281, display 16105), Commander Thomas
Helleran (16361, display 16132) and Father Gavin (1253, display 1616). The row follows the Deadmines and Shadowfang Keep
quest givers' column set. The spawns (normal difficulty only, `spawnMask` 1), the starter and ender rows and the quest
edits are the hand-written data/sql/updates/pending_db_world/rev_dungeon_quests_scarlet_monastery.sql; the row values
(positions, measurements) are in that file's header.
"""

from lib.dsl.registry import creature_model, creature_template

_AGENT = dict(
    IconName='', exp=0, faction=35, npcflag=2, rank=0, unit_class=1, speed_walk=1.0, speed_run=1.14286,
    speed_swim=1.0, speed_flight=1.0, detection_range=18.0, dmgschool=0, DamageModifier=1.0, BaseAttackTime=2000,
    RangeAttackTime=2000, BaseVariance=1.0, RangeVariance=1.0, unit_flags=0, unit_flags2=2048, dynamicflags=0,
    family=0, type=7, type_flags=0, lootid=0, pickpocketloot=0, skinloot=0, PetSpellDataId=0, VehicleId=0, mingold=0,
    maxgold=0, AIName='', MovementType=0, HoverHeight=1.0, HealthModifier=1.0, ManaModifier=1.0, ArmorModifier=1.0,
    ExperienceModifier=1.0, RacialLeader=0, movementId=0, RegenHealth=1, CreatureImmunitiesId=0, flags_extra=2,
    ScriptName='', VerifiedBuild=0, gossip_menu_id=0,
)

graveyard_agent_300923 = creature_template(
    300923, 'Agent Corwin Hale', subname='The Argent Dawn', minlevel=31, maxlevel=31, **_AGENT,
)
creature_model(300923, display_id=5226, idx=0)

library_agent_300924 = creature_template(
    300924, 'Archivist Tobias Merrow', subname='The Argent Dawn', minlevel=34, maxlevel=34, **_AGENT,
)
creature_model(300924, display_id=16105, idx=0)

armory_agent_300925 = creature_template(
    300925, 'Captain Dorrin Ashe', subname='The Argent Dawn', minlevel=36, maxlevel=36, **_AGENT,
)
creature_model(300925, display_id=16132, idx=0)

cathedral_agent_300926 = creature_template(
    300926, 'Father Anselm Gray', subname='The Argent Dawn', minlevel=39, maxlevel=39, **_AGENT,
)
creature_model(300926, display_id=1616, idx=0)
