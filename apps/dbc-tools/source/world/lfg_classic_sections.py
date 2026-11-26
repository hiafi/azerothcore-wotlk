"""
Blackrock Depths' four Dungeon Finder sections (Blackrock Depths build, WP-H; lib/dsl/lfg.py `lfg_dungeon()` and
`lfg_override(last_encounter=)`, WP-FD; handoff 7.1 #3, #12 and 3.8): the normal side. Stock has two entries on map
230, 30 "Prison" and 276 "Upper City", both starting at the dungeon entrance and ending at Bael'Gar / the Emperor
only on paper (30's final boss was Gerstahn's row). The rework splits the dungeon into four runs, each with its own
start and its own last boss:

| Section | Finder entry | Window (target) | Start | Last boss (completes the run) |
| --- | --- | --- | --- | --- |
| 1 Detention Block | 30 (stock row) | 47-57 (51), stock | the stock entrance | the Ring of Law (230) |
| 2 Shadowforge City | 308 (new) | 48-58 (53) | S2g, the Ring's south gallery | Bael'Gar (235) |
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
section returns the group to its start: the S2g row is up in the gallery, 55 yd from the Ring's centre and 18 yd above
its floor, so nowhere near areatrigger 1526 (the arena trigger, the BRS K-m3 lesson), and the new rows sit away from
every boss pull.

A section's last boss moves `lastEncounterDungeon` (the Finder's completion link): 227 Gerstahn -> 0 (comes from the
section 1 edit, nothing to write by hand), 230 the Ring -> 30, 235 Bael'Gar -> 308, 237 Argelmach -> 309; 245 the
Emperor stays 276. The same edit is what the heroic copies follow.

Gnomeregan's two sections (14 and 320) follow at the end of the file.

Shared file (no --scope owns it): only a full generate.py run writes these rows. `instance_encounters` rows naming 308
and 309 need `lfgdungeons_dbc` 308 / 309 loaded first (ObjectMgr::LoadInstanceEncounters skips the row otherwise): the
Finder rows ship in the same full run.
"""

from lib.dsl.lfg import lfg_dungeon, lfg_override

# Section 1: the stock row ends at the Ring of Law now (Gerstahn 227 loses the link, the Ring 230 takes it).
lfg_override(30, last_encounter=230)

# Section 2: Shadowforge City, Bael'Gar ends the run. Start S2g (544.0, -181.3, -36.0), the flat south end of the Ring's
# spectator gallery (z -36, clearance 13.2 yd), on the first leg to Loregrain and facing it. The first pick, S2a
# (595, -92, -45) in the table hall north of the Ring, landed a group 5-7 yd from two patrolling Fireguards (guids 45943,
# 47836) and 16 yd from an Anvilrage pack: the brd-s2 bot smoke run (2026-11-18) wiped there in 41 s. The gallery units
# stand down for a section 2 instance (mod-dungeon-bosses GalleryStandsDownOnEntry); from S2g the nearest other hostile
# is 35 yd away (a Bloodhound 24 yd below) and the nearest patrol 64 yd.
lfg_dungeon(
    308, "Blackrock Depths - Shadowforge City", map_id=230, like=30, min_level=48, max_level=58, target_level=53,
    last_encounter=235, position=(544.0, -181.3, -36.0, 5.18),
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

# Gnomeregan's two Dungeon Finder sections (Gnomeregan build, WP-H; handoff 3.3, 3.8 and 7 #5 / #6 A). Stock has one
# entry on map 90, 14 "Gnomeregan" (levels 23-33, target 27, start (-332.22, -2.28, -150.86), Thermaplugg ends it). The
# rework splits the dungeon in two runs: section 1 (entry 14, the dungeon's front: Techbot, Viscous Fallout and
# Electrocutioner 6000) and section 2 (the new entry 320 "Gnomeregan - The Workshop": from the Train Depot through the
# Mobile Alert System, Crowd Pummeler and Thermaplugg). The heroic entries 321 and 322 (source/world/
# lfg_classic_heroic.py) copy each row's start and complete on the heroic copy of the same boss.
#
# | Section | Finder entry | Window (target) | Start | Last boss (completes the run) |
# | 1 | 14 (stock row) | 23-33 (27), stock | the stock start | Electrocutioner 6000 (380) |
# | 2 | 320 (new) | 23-33 (27) | the Train Depot landing | Mekgineer Thermaplugg (382) |
#
# Section 1: the stock row's final boss moves from Thermaplugg (382) to Electrocutioner (380); 382 loses the link and
# the new entry 320 takes it. The stock start stays (the Finder drops a group 2.0 yd above the floor, a harmless drop).
lfg_override(14, last_encounter=380)

# Section 2: The Workshop, Thermaplugg ends the run. The start is the Train Depot landing (area trigger 523's target,
# -736.51, 2.71, -249.99, facing 3.14; the NAVMESH report found it clean); the Workshop Door is sealed until the
# Mobile Alert System dies, which opens it. `like=14` gives the texture (GNOMEREGAN), descriptions, expansion and order
# of the stock row; the window is the stock row's. Its checkpoint row (the Depot landing, reached only) is in the
# checkpoint SQL of mod-dungeon-checkpoint.
lfg_dungeon(
    320, "Gnomeregan - The Workshop", map_id=90, like=14, min_level=23, max_level=33, target_level=27,
    last_encounter=382, position=(-736.51, 2.71, -249.99, 3.14),
)
