"""
The Deadmines (map 36). Dungeon difficulties E1: the heroic proof - a level 60 heroic with the stock 5-man heroic
lockout (one day) and the Utgarde Keep message mask and difficulty name, entered at level 60 or above. E2 (WP-T2):
the heroic boss list (DungeonEncounter 1000-1006 copy the normal 161-167, Rhahk'Zor 644 .. Edwin VanCleef 639, with
their kill credit) and every spawn on heroic. E1's WP-1D SQL already set spawnMask 3 on all 213 creature and 46
gameobject spawns, so the spawnMask emitter has nothing to add here. Heroic creature templates and their
difficulty_entry_1 / side-table rows come with WP-G's entry map.

MapDifficulty 1000, dungeon_access_template 122 and DungeonEncounter 1000-1006 are the first ids of their blocks
(source/ids.yaml); never move them once shipped.
"""

from lib.dsl.dungeon import dungeon, heroic

deadmines = dungeon(
    36, "Deadmines",
    heroic=heroic(
        map_difficulty_id=1000, access_id=122, min_level=60,
        encounter_ids=range(1000, 1007),  # Rhahk'Zor, Sneed, Gilnid, Mr. Smite, Cookie, Captain Greenskin, VanCleef
        spawn_mask=True,
    ),
)
