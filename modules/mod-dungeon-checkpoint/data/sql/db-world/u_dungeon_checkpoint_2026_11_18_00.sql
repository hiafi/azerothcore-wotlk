-- Blackrock Depths: section 2's Dungeon Finder start moves (lfg_dungeon_template 308 / 311, dbc-tools
-- source/world/lfg_classic_sections.py; keep them equal). The first pick, S2a (595, -92, -45) in the table hall north
-- of the Ring, landed a group 5-7 yd from two patrolling Fireguards and 16 yd from an Anvilrage pack: the brd-s2 bot
-- smoke run of 2026-11-18 wiped there in 41 s. S2g (544, -181.3, -36) is the flat south end of the Ring's spectator
-- gallery, whose units stand down for a section 2 instance.
-- The spot is 18-22 yd from the Ring's floor, so the 25 yd reach radius of u_dungeon_checkpoint_2026_11_17_01.sql would
-- let a section 1 group fighting the Ring mark it reached and respawn a dead player in the (hostile, for section 1)
-- gallery. 12 yd still covers a Finder arrival, which lands on the spot. Re-runnable (UPDATE only).
UPDATE `dungeon_checkpoint_location`
    SET `position_x` = 544, `position_y` = -181.3, `position_z` = -36, `orientation` = 5.18, `reach_radius` = 12,
        `comment` = 'Blackrock Depths - Section 2 Finder start S2g, the Ring gallery (lfg_dungeon_template 308)'
    WHERE `map_id` = 230 AND `creature_entry` = 0 AND `location_index` = 1;
