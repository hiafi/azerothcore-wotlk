"""
Random Classic Heroic (lfg-classic-heroic, .agents/plans/lfg-classic-heroic/lfg-classic-heroic.PLAN.md): a Dungeon
Finder random queue for levels 60-62 over every vanilla dungeon with a heroic, and a "Classic Heroic" section under
Specific Dungeons listing each of them by name. lib/dsl/lfg.py has the helpers, lib/lfg_dungeons.py builds the rows.

A vanilla dungeon that gains a heroic (`heroic=heroic(...)` in source/world/dungeons/) joins the pool with one more
lfg_heroic() line per finder entry of its map (next free id from ids.yaml's `lfgdungeons` block). generate.py prints a
note for a heroic map whose finder entries have no line here.

The rewards (lfg_dungeon_rewards row, the two quests and the satchel's item_template and loot) are hand-written pending
world SQL; the satchel's Item.dbc row is source/items.csv 70700.

Shared file (no --scope owns it): only a full generate.py run writes these rows. A dungeon scope's heroic final boss
names its finder entry here, so a scoped run of that dungeon stops until a full run has shipped the entry.
"""

from lib.dsl.lfg import lfg_group, lfg_heroic, lfg_override, lfg_random

CLASSIC_HEROIC = 12

# The section lists right above Classic Dungeons: the client lists sections by OrderIndex (stock: Lich King Heroic 1,
# Lich King Normal 2, Burning Crusade Heroic 3, Burning Crusade Normal 4, Classic Dungeons 5, raids 17-21), so Classic
# Dungeons moves down to 6 and Classic Heroic takes 5.
lfg_group(CLASSIC_HEROIC, name="Classic Heroic", order_index=5, type_id=5)
lfg_group(1, order_index=6)  # Classic Dungeons

# Ruling 1: available at 60, gone at 63. Shaped like stock 260 Random Burning Crusade Heroic (Difficulty 1, Flags 3).
lfg_random(300, "Random Classic Heroic", group=CLASSIC_HEROIC, like=260, expansion=0, min_level=60, max_level=62)

# Ruling 2: every vanilla dungeon with a declared heroic. Stratholme (map 329) has two finder entries, one per wing.
lfg_heroic(301, normal=6, group=CLASSIC_HEROIC)  # Deadmines
lfg_heroic(302, normal=8, group=CLASSIC_HEROIC)  # Shadowfang Keep
lfg_heroic(303, normal=2, group=CLASSIC_HEROIC)  # Scholomance
lfg_heroic(304, normal=40, group=CLASSIC_HEROIC)  # Stratholme - Main Gate
lfg_heroic(305, normal=274, group=CLASSIC_HEROIC)  # Stratholme - Service Entrance

# Blackrock Spire (map 229, the Blackrock Spire build, WP-H): two finder entries on one map, and the Upper half is a
# raid-type stock row the Finder cannot queue (LFGDungeons 44 is TypeID 2, Group 6, Flags 0; JoinLfg refuses a raid
# entry while the raid browser is off, DungeonFinder.OptionsMask 5). lfg_override() turns it into a normal dungeon
# entry in Classic Dungeons (TypeID 1, Group 1, Flags 3, levels 55-65 like every Classic dungeon row), so it queues and
# joins Random Classic (normal), and so lfg_heroic() can take it as a stock normal dungeon row. Its Finder start point:
# the stock row has no lfg_dungeon_template row and the map's entrance areatrigger is the Lower Spire's, so the
# declared position puts the group in the lower hall of the Upper Spire path, 19 yd short of the Dragonspire Hall
# trigger 2046 ((102.43, -319.17, 65.46), radius 10), on standable mesh 76 yd of walking from the Lower Spire entrance
# (navmesh report, ubrs_start check): (98.25, -300.75, 63.1), facing the hall. The heroic entry copies it. The spot is
# 0.25 yd inside the rework instance's self-start box (mod-dungeon-bosses BlackrockSpireRework.h kDragonspireHall /
# kUbrsFinderStart), so an arrival starts the rune-room check about 1 s later, by design; test_blackrock_spire_kit
# keeps this position, the checkpoint SQL and the C++ constant equal.
lfg_override(44, type_id=1, group=1, flags=3, min_level=55, max_level=65, position=(98.25, -300.75, 63.1, 4.94))

# Lower Spire (finder entry 32, Wyrmthalak completes the run) and Upper Spire (44, Drakkisath completes it): one heroic
# map with a 10-player row, so two heroic entries, each linked to its own final heroic encounter.
lfg_heroic(306, normal=32, group=CLASSIC_HEROIC)  # Lower Blackrock Spire
lfg_heroic(307, normal=44, group=CLASSIC_HEROIC)  # Upper Blackrock Spire

# Blackrock Depths (map 230, the Blackrock Depths build, WP-H): four sections of one 5-player heroic map, each a heroic
# entry of its normal row (30, 308, 309 and 276 are declared in source/world/lfg_classic_sections.py) that copies the
# normal row's start and completes on the heroic copy of the section's last boss: 1058 the Ring of Law, 1063 Bael'Gar,
# 1065 Argelmach, 1073 the Emperor. One map, one instance, one heroic lock for all four (a player who ran section 1
# heroic today is bound to the same instance for every section).
lfg_heroic(310, normal=30, group=CLASSIC_HEROIC)  # Blackrock Depths - Prison
lfg_heroic(311, normal=308, group=CLASSIC_HEROIC)  # Blackrock Depths - Shadowforge City
lfg_heroic(312, normal=309, group=CLASSIC_HEROIC)  # Blackrock Depths - Manufactory
lfg_heroic(313, normal=276, group=CLASSIC_HEROIC)  # Blackrock Depths - Upper City
