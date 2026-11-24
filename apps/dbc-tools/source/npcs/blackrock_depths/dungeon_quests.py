"""
Dungeon quests stage Q4 (.agents/plans/dungeon-quests/dungeon-quests.PLAN.md section 8): the two Thorium Brotherhood
quest givers of Blackrock Depths, in the `blackrock_depths` creature reservation's wave 1 spare 300797-300827
(source/ids.yaml; _common.py lists the files):

    300797  Kragen Ashvein     The Thorium Brotherhood   level 52   the Detention Block entrance: gives and ends 4081,
                                                                    4082, 3802, 4123, 4263; ends 4322 Jail Break!
    300798  Durn Cinderbrew    Guzzler Regular           level 55   the Grim Guzzler, a Thorium Brotherhood agent
                                                                    posing as a patron: gives and ends 4136, 4134, 4286

Quest givers (npcflag 2) only, friendly to both factions (faction 35), civilians (flags_extra 2: never attack, never
attacked), no AI, no gossip, no loot. Levels: the Detention Block's bosses (51-52) and the Imperial Seat's door (the
Guzzler's patrons are 48-52, Plugger and Ribbly 53-55). Looks: Kragen wears the stock Thorium Brotherhood Lookout's
(14622, display 14669), a Dark Iron in the Brotherhood's colors; Durn a stock Grim Patron's (9545, display 8676, its
fourth model), so he blends in with the 68 patrons. The Guzzler's bar events (Plugger's death, the theft, Ribbly's
gossip) set faction 14 by entry only (smart_scripts 9499 ids 9-12, 9543 ids 0-1, actionlist 949900): Durn is never one
of them. The row follows the earlier dungeon quest givers' column set (source/npcs/scarlet_monastery/dungeon_quests.py).
The spawns (normal difficulty only, `spawnMask` 1), the starter and ender rows and the quest edits are the
hand-written data/sql/updates/pending_db_world/rev_dungeon_quests_blackrock_depths.sql; the row values (positions,
measurements) are in that file's header.
"""

from lib.dsl.registry import creature_model, creature_template

_GIVER = dict(
    IconName='', exp=0, faction=35, npcflag=2, rank=0, unit_class=1, speed_walk=1.0, speed_run=1.14286,
    speed_swim=1.0, speed_flight=1.0, detection_range=18.0, dmgschool=0, DamageModifier=1.0, BaseAttackTime=2000,
    RangeAttackTime=2000, BaseVariance=1.0, RangeVariance=1.0, unit_flags=0, unit_flags2=2048, dynamicflags=0,
    family=0, type=7, type_flags=0, lootid=0, pickpocketloot=0, skinloot=0, PetSpellDataId=0, VehicleId=0, mingold=0,
    maxgold=0, AIName='', MovementType=0, HoverHeight=1.0, HealthModifier=1.0, ManaModifier=1.0, ArmorModifier=1.0,
    ExperienceModifier=1.0, RacialLeader=0, movementId=0, RegenHealth=1, CreatureImmunitiesId=0, flags_extra=2,
    ScriptName='', VerifiedBuild=0, gossip_menu_id=0,
)

entrance_giver_300797 = creature_template(
    300797, 'Kragen Ashvein', subname='The Thorium Brotherhood', minlevel=52, maxlevel=52, **_GIVER,
)
creature_model(300797, display_id=14669, idx=0)

guzzler_agent_300798 = creature_template(
    300798, 'Durn Cinderbrew', subname='Guzzler Regular', minlevel=55, maxlevel=55, **_GIVER,
)
creature_model(300798, display_id=8676, idx=0)
