"""
Dungeon finder exclusions: one lfg_exclude(map_id, name) per instance map to keep out of the
dungeon finder. Each becomes a `disables` row of sourceType 8 (DISABLE_TYPE_LFG_MAP), so the
dungeon is gone from both the random queue and the "Specific Dungeons" list, for every player.
The instance itself stays enterable on foot.

Takes a Map.dbc id, not an LFGDungeons id, and covers every finder entry on that map: all wings
(Dire Maul East/West/North are all map 429), normal and heroic, and seasonal boss entries (Coren
Direbrew is on Blackrock Depths, map 230). generate.py prints what each exclusion covers and
stops on a map with no finder entry. Deleting a line re-enables the dungeon (the prune pass
emits the DELETE). Applies on worldserver start or `.reload disables`.

    lfg_exclude(230, "Blackrock Depths")
"""

from lib.dsl.registry import lfg_exclude

lfg_exclude(43, "Wailing Caverns")
lfg_exclude(109, "Sunken Temple")
