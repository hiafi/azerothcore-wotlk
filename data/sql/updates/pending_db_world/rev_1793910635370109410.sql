-- progression-slim PS7 fix: delete the 4 blockers mod-progression phase 00 spawned in front of the Northrend
-- transports (phase_00-gameobject.sql guids 5300004-5300007; its phase 13 deleted them again). The content gate now
-- holds Northrend at the transport, so they only blocked the old-world docks.
-- 5300004 Wintergrasp Keep Collision Wall 194323: the Stormwind Harbor entrance (also cut off The Bravery's dock)
-- 5300005 Gate 177371: Orgrimmar zeppelin tower; 5300006, 5300007 Gate 177371: Tirisfal zeppelin tower
-- The AQ gate (5300000-5300002) and the Caverns of Time door (5300003) stay.
DELETE FROM `gameobject` WHERE `guid` IN (5300004, 5300005, 5300006, 5300007) AND `id` IN (177371, 194323);
