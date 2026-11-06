"""
The Deadmines (map 36). Dungeon difficulties E1: the heroic proof - a level 60 heroic with the stock 5-man heroic
lockout (one day) and the Utgarde Keep message mask and difficulty name, entered at level 60 or above. No heroic
creature templates yet (E2); spawnMask and INSTANCE_BIND ship as SQL in E1 (WP-1D).

MapDifficulty 1000 and dungeon_access_template 122 are the first ids of their blocks (source/ids.yaml); never move
them once shipped.
"""

from lib.dsl.dungeon import dungeon, heroic

deadmines = dungeon(
    36, "Deadmines",
    heroic=heroic(map_difficulty_id=1000, access_id=122, min_level=60),
)
