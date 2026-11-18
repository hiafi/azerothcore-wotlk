"""
Blackrock Depths' four Dungeon Finder sections (Blackrock Depths build, WP-H; lib/dsl/lfg.py `lfg_dungeon()` and
`lfg_override(last_encounter=)`, WP-FD; handoff 7.1 #3, #12 and 3.8): the normal side. Stock has two entries on map
230, 30 "Prison" and 276 "Upper City", both starting at the dungeon entrance and ending at Bael'Gar / the Emperor
only on paper (30's final boss was Gerstahn's row). The rework splits the dungeon into four runs, each with its own
start and its own last boss:

| Section | Finder entry | Window (target) | Start | Last boss (completes the run) |
| --- | --- | --- | --- | --- |
| 1 Detention Block | 30 (stock row) | 47-57 (51), stock | the stock entrance | the Ring of Law (230) |
| 2 Shadowforge City | 308 (new) | 48-58 (53) | S2a, the open hall north of the Ring | Bael'Gar (235) |
| 3 Manufactory | 309 (new) | 50-60 (55) | the Shadowforge Lock lever room | Golem Lord Argelmach (237) |
| 4 Imperial Seat | 276 (stock row, start moved) | 51-61 (55), stock | S4b, lower Guzzler floor | the Emperor (245) |

The heroic entries 310-313 (source/world/lfg_classic_heroic.py) copy each row's start and complete on the heroic copy of
the same boss. All four normal rows sit in Classic Dungeons (group 1), so Random Classic Dungeon (258) draws them.

The two new windows are a designer pick (handoff 7 #3, built as recommended). `like=30` gives the texture
(BLACKROCKDEPTHS), descriptions, expansion and order of the stock Prison row.

The starts come from the NAVMESH report (.agents/plans/blackrock-depths-build/blackrock-depths-build.NAVMESH-REPORT.md,
"Section 2/3/4"; the handoff's 3.8 table); the x axis is north, y west, and every spot is `[navmesh estimate]` until
`.gps` confirms it in game (the playtest guide lists the checks). Facing is cosmetic: each start faces the first leg of
its own route. Every start has a matching entrance-type row in mod-dungeon-checkpoint (module SQL), so a wipe in a
section returns the group to its start: the S2a row is 55 yd north of the Ring's north gate, outside areatrigger 1526
(the arena trigger, the BRS K-m3 lesson), and the new rows sit away from every boss pull.

A section's last boss moves `lastEncounterDungeon` (the Finder's completion link): 227 Gerstahn -> 0 (comes from the
section 1 edit, nothing to write by hand), 230 the Ring -> 30, 235 Bael'Gar -> 308, 237 Argelmach -> 309; 245 the
Emperor stays 276. The same edit is what the heroic copies follow.

Shared file (no --scope owns it): only a full generate.py run writes these rows. `instance_encounters` rows naming 308
and 309 need `lfgdungeons_dbc` 308 / 309 loaded first (ObjectMgr::LoadInstanceEncounters skips the row otherwise): the
Finder rows ship in the same full run.
"""

from lib.dsl.lfg import lfg_dungeon, lfg_override

# Section 1: the stock row ends at the Ring of Law now (Gerstahn 227 loses the link, the Ring 230 takes it).
lfg_override(30, last_encounter=230)

# Section 2: Shadowforge City, Bael'Gar ends the run. Start S2a (595.0, -92.0, -45.0), the open table hall 55 yd
# north of the Ring's north gate (clearance 14.4 yd); faces the way out to the East Garrison, (568, -10).
lfg_dungeon(
    308, "Blackrock Depths - Shadowforge City", map_id=230, like=30, min_level=48, max_level=58, target_level=53,
    last_encounter=235, position=(595.0, -92.0, -45.0, 1.89),
)

# Section 3: Manufactory, Golem Lord Argelmach ends the run. Start (607.2, -47.8, -59.8), 8 yd from the Shadowforge Lock
# lever 161460 (615.6, -49.8, -60.1) and facing it: the group pulls the lever itself (door 161516 must be open on the
# way, handoff 7.1 #12).
lfg_dungeon(
    309, "Blackrock Depths - Manufactory", map_id=230, like=30, min_level=50, max_level=60, target_level=55,
    last_encounter=237, position=(607.2, -47.8, -59.8, 6.05),
)

# Section 4: Imperial Seat (stock entry 276; the Emperor already ends it). The start moves from the dungeon entrance
# to S4b (843.8, -167.8, -49.7), the lower Guzzler floor (clearance 20.3 yd, 36-47 yd from Hurley, Ribbly and Plugger),
# facing the Bar Door.
lfg_override(276, position=(843.8, -167.8, -49.7, 4.64))
