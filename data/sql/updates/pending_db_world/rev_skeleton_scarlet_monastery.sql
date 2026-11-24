-- Scarlet Monastery build WP-S0, the skeleton (.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md
-- s3.2 item 4, s7 #14 A, #15 A, s3.5 row D3). Wave 1 only: the wave 2 bosses' SmartAI goes with W2-SETUP's rev.

-- The stock SmartAI of the seven wave 1 bosses bound to C++ by apps/dbc-tools source/npcs/scarlet_monastery/
-- (Vishas, Ironspine, Azshir, the Fallen Champion, Thalnos, Loksey, Doan), the rares' 90% despawn on AI init included,
-- so no boss WP deletes them again. Two stock side effects are kept by the C++ stubs: Vishas's death line to Vorrel
-- 3981 (row 5) and Thalnos's Scorn 14693 summon while game event 120 runs (row 7). The SmartAI conditions bound to
-- these rows (source type 22; live: only 4543 group 8, the event 120 check) go with them.
DELETE FROM `smart_scripts` WHERE `entryorguid` IN (3983, 6489, 6490, 6488, 4543, 3974, 6487) AND `source_type` = 0;
DELETE FROM `conditions` WHERE `SourceTypeOrReferenceId` = 22 AND `SourceId` = 0
    AND `SourceEntry` IN (3983, 6489, 6490, 6488, 4543, 3974, 6487);

-- Section 7 #14 A: the interior keyed doors go keyless (GO_FLAG_LOCKED 0x2 cleared, NODESPAWN 0x20 kept): the Chapel
-- Door 104591 (anyone opens it; it starts the Last Stand once wave 2 binds) and Herod's Door 101854 (D11's sealed arena
-- shuts it at his pull). The outdoor Cathedral and Armory doors on map 0 (101850, 101851) stay keyed.
UPDATE `gameobject_template_addon` SET `flags` = `flags` & ~2 WHERE `entry` IN (104591, 101854);
-- Their lock 299 (the Scarlet Key) goes too: the 3.3.5 client enforces a door's lock from the query data even without
-- GO_FLAG_LOCKED, and no server code reads a door's lock; both entries spawn only on map 189 (R-1-KIT M-3).
UPDATE `gameobject_template` SET `Data1` = 0 WHERE `entry` IN (104591, 101854);

-- The Chapel Door's AI (go_sm_chapel_door, instance_scarlet_monastery_rework.cpp): its use, the lever's activation
-- and the Ashbringer path all reach it; the instance tells them apart.
UPDATE `gameobject_template` SET `ScriptName` = 'go_sm_chapel_door' WHERE `entry` = 104591;

-- Section 7 #15 A: the wing portal (a GOOBER, no lock; InstancePortal_Red GODI 4711 at 0.45, VR). The instance summons
-- it at P1 / P1h / P2 / P3 on the end bosses' DONE and after a reload; go_sm_wing_portal handles the use in GossipHello
-- before any type-specific handling (GameObject::Use), so the goober never changes state.
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`, `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`, `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`, `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301324, 10, 4711, 'Scarlet Monastery Portal', '', '', '', 0.45, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', 'go_sm_wing_portal', 0) ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`), `name` = VALUES(`name`), `IconName` = VALUES(`IconName`), `castBarCaption` = VALUES(`castBarCaption`), `unk1` = VALUES(`unk1`), `size` = VALUES(`size`), `Data0` = VALUES(`Data0`), `Data1` = VALUES(`Data1`), `Data2` = VALUES(`Data2`), `Data3` = VALUES(`Data3`), `Data4` = VALUES(`Data4`), `Data5` = VALUES(`Data5`), `Data6` = VALUES(`Data6`), `Data7` = VALUES(`Data7`), `Data8` = VALUES(`Data8`), `Data9` = VALUES(`Data9`), `Data10` = VALUES(`Data10`), `Data11` = VALUES(`Data11`), `Data12` = VALUES(`Data12`), `Data13` = VALUES(`Data13`), `Data14` = VALUES(`Data14`), `Data15` = VALUES(`Data15`), `Data16` = VALUES(`Data16`), `Data17` = VALUES(`Data17`), `Data18` = VALUES(`Data18`), `Data19` = VALUES(`Data19`), `Data20` = VALUES(`Data20`), `Data21` = VALUES(`Data21`), `Data22` = VALUES(`Data22`), `Data23` = VALUES(`Data23`), `AIName` = VALUES(`AIName`), `ScriptName` = VALUES(`ScriptName`), `VerifiedBuild` = VALUES(`VerifiedBuild`);

-- Section 3.5 row D3: Azshir the Sleepless respawned in 300 s (a rare's timer); a boss's 86400 now.
UPDATE `creature` SET `spawntimesecs` = 86400 WHERE `id` = 6490 AND `guid` = 1975841;
