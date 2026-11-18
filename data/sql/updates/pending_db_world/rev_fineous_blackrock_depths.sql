-- Blackrock Depths build WP-D10: Fineous Darkvire (9056) and the Guzzler rope, the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D10; build spec
-- docs/dungeons/blackrock-depths-2-shadowforge-city.md "Fineous Darkvire"). His template (npc_fineous_darkvire_rework,
-- AIName '', health, DamageModifier, immunity 1972) and the spells 211120-211123 are apps/dbc-tools
-- source/npcs/blackrock_depths/fineous.py; his six SmartAI rows went in rev_blackrock_depths_skeleton.sql (the script
-- casts the stock Devotion Aura, Holy Strike, Kick and Seal of Reckoning itself); the credit row 234 went in
-- rev_credit_drops_blackrock_depths.sql. He keeps his patrol (creature 47631, path 476310): nothing here touches it.

-- Franclorn's Spirit (9542), a short-lived copy by Fineous's corpse (S2 749, handoff section 8 #13): the spirit's
-- group 0 is the Loregrain kill line (WP-D7's rev); group 1 is this one line, a say.
DELETE FROM `creature_text` WHERE `CreatureID` = 9542 AND `GroupID` = 1;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(9542, 1, 0, 'Ironfel... return it to my statue, friends.', 12, 0, 100, 0, 0, 0, 0, 0,
    'Franclorn''s Spirit - Fineous''s death (BRD D10)');

-- 301282 Hanging Rope (display 7717 Borean_Rope_01, size 0.5 = about 32 yd of rope for the 22 yd climb) and 301283
-- Shoddy Pillar (display 5073 Stalagmite01, size 1.0, a prop).
-- 301282 is a goober (type 10, no lock, no spell, no loot, no despawn) whose script owns the click
-- (go_brd_hanging_rope: a near teleport to the floor past the Bar Door) and hides it (CanBeSeen, not selectable) until
-- the instance's rope is placed (DATA_GUZZLER_ROPE, saved), so a reload brings it back with no respawn code.
-- 301283 is GENERIC (type 5: no lock, no key item, no click) and not selectable (addon flags 16), summoned by Fineous
-- at a player's spot for the 3 s before the collapse.
-- Upserts: gameobject_template rows are never deleted (codestyle-sql not_delete).
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`,
    `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`,
    `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`,
    `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301282, 10, 7717, 'Hanging Rope', '', '', '', 0.5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, '', 'go_brd_hanging_rope', 0),
(301283, 5, 5073, 'Shoddy Pillar', '', '', '', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, '', '', 0) ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`),
    `name` = VALUES(`name`), `size` = VALUES(`size`), `Data0` = VALUES(`Data0`), `AIName` = VALUES(`AIName`),
    `ScriptName` = VALUES(`ScriptName`);
DELETE FROM `gameobject_template_addon` WHERE `entry` IN (301282, 301283);
INSERT INTO `gameobject_template_addon` (`entry`, `faction`, `flags`, `mingold`, `maxgold`, `artkit0`, `artkit1`,
    `artkit2`, `artkit3`) VALUES
(301282, 0, 0, 0, 0, 0, 0, 0, 0),
(301283, 0, 16, 0, 0, 0, 0, 0, 0);

-- The hanging rope's one spawn (normal and heroic: spawnMask 3) at FineousLogic.h kRopeHang, the climb spot behind Lord
-- Incendius (893.5, -267.1, -71.9; his spawn, so the use spell's 12 yd disc and the click's reach meet there). Guid
-- 3012820 (the entry x 10 convention of the kit spawns; free in the live DB, read-only check 2026-11-17). Rotation =
-- the orientation about z (o 2.0: rotation2 = sin(o/2), rotation3 = cos(o/2)). The object stands hidden for the whole
-- instance until the rope is hung; the pillar has no spawn (Fineous summons it).
DELETE FROM `gameobject` WHERE `id` = 301282 AND `guid` = 3012820;
INSERT INTO `gameobject` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `position_x`,
    `position_y`, `position_z`, `orientation`, `rotation0`, `rotation1`, `rotation2`, `rotation3`, `spawntimesecs`,
    `animprogress`, `state`, `ScriptName`, `VerifiedBuild`, `Comment`) VALUES
(3012820, 301282, 230, 0, 0, 3, 1, 893.5, -267.1, -71.9, 2, 0, 0, 0.841471, 0.540302, 300, 255, 1, '', 0,
    'Blackrock Depths D10: Hanging Rope (the Guzzler skip, shown once the rope is hung behind Lord Incendius)');
