-- progression-slim PS3 D1: transports, Onyxia/Maraudon doors, Archmage Timear.

-- Transports: restore the 6 routes phase 00 deleted (phase_00-transports.sql): guids 9, 10, 11, 12, 17, 20.
-- Rows copied from data/sql/base/db_world/transports.sql (live table has 14 of the 20 base rows).
-- Crews and passengers' creature spawns (maps 587-591, 647) are un-hidden by the bundle/spawn SQL (WP-D2).
DELETE FROM `transports` WHERE `guid` IN (9, 10, 11, 12, 17, 20);
INSERT INTO `transports` (`guid`, `entry`, `name`, `ScriptName`) VALUES
(9,181646,'Auberdine, Darkshore and Valaar\'s Berth, Azuremyst Isle (Boat, Alliance (\"Elune\'s Blessing\"))',''),
(10,181688,'Menethil Harbor, Wetlands and Valgarde, Howling Fjord (Boat, Alliance (\"Northspear\"))',''),
(11,181689,'Undercity, Tirisfal Glades and Vengeance Landing, Howling Fjord (Zeppelin, Horde (\"Cloudkisser\"))',''),
(12,186238,'Orgrimmar, Durotar and Warsong Hold, Borean Tundra (Zeppelin, Horde (\"The Mighty Wind\"))',''),
(17,190536,'Valiance Keep, Borean Tundra and Stormwind Harbor (Boat, Alliance (\"The Kraken\"))',''),
(20,190549,'Orgrimmar, Durotar and Thunder Bluff, Mulgore (Zeppelin, Horde (\"The Zephyr\"))','');

-- The Bravery 176310 back to its stock Stormwind Harbor <-> Auberdine path 967 (TaxiPath 300 -> 24); phase 00 set
-- the vanilla Menethil <-> Auberdine path 295 (phase_00-gameobject_template.sql), phase 13 set it back.
UPDATE `gameobject_template` SET `Data0` = 967 WHERE `entry` = 176310 AND `Data0` = 295; -- Ship (The Bravery)

-- Doors: Onyxia's Gate 177928 and the Maraudon Stone Door 177444 back to stock flags 32 (phase 00 added flag 4,
-- gameobject_template_addon phase_00-gameobject_template_addon.sql). Stock: base gameobject_template_addon
-- (177444 -> 32, 177928 -> 32). The instance gate now blocks entry, so the doors need no extra lock.
-- The AQ gate objects (176146-176148, 176996) and the Karazhan doors (176694, 184164) keep their locks.
-- 177444 Stone Door (Maraudon); 177928 Onyxia's Gate
UPDATE `gameobject_template_addon` SET `flags` = 32 WHERE `entry` IN (
    177444, 177928
);

-- Archmage Timear: the phase 00 script npc_archmage_timear leaves with mod-progression; core has no such script
-- (stock ScriptName is empty, base creature_template).
UPDATE `creature_template` SET `ScriptName` = '' WHERE `entry` = 31439 AND `ScriptName` = 'npc_archmage_timear'; -- Archmage Timear
