-- progression-slim PS7 fix: delete the 4 blockers mod-progression phase 00 spawned in front of the Northrend
-- transports (phase_00-gameobject.sql guids 5300004-5300007; its phase 13 deleted them again). The content gate now
-- holds Northrend at the transport, so they only blocked the old-world docks.
-- 5300004 Wintergrasp Keep Collision Wall 194323: the Stormwind Harbor entrance (also cut off The Bravery's dock)
-- 5300005 Gate 177371: Orgrimmar zeppelin tower; 5300006, 5300007 Gate 177371: Tirisfal zeppelin tower
-- 5300003 CavernDoor01 176996 at the Caverns of Time entrance goes too (no stock spawn; user 2026-11-05: the instance
-- gate closes the Caverns of Time). The AQ gate (5300000-5300002) stays.
DELETE FROM `gameobject` WHERE `guid` IN (5300003, 5300004, 5300005, 5300006, 5300007)
    AND `id` IN (176996, 177371, 194323);

-- Burkrum <Heavy Armor Merchant> 6028: no quivers or ammo pouches with ammo gone (user 2026-11-05). The vendor
-- restore (rev_1793874072714777555) no longer adds them; this removes them where it already did.
-- 2102 Small Ammo Pouch, 5439 Small Quiver, 11363 Medium Shot Pouch
DELETE FROM `npc_vendor` WHERE `entry` = 6028 AND `item` IN (2102, 5439, 11363);
