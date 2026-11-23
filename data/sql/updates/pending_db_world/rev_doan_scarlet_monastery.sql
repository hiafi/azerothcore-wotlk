-- Scarlet Monastery build WP-D8: Arcanist Doan (6487), the rows dbc-tools cannot declare
-- (.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.5 row D8, s7 #22 A; build spec
-- docs/dungeons/scarlet-monastery-2-library.md "Arcanist Doan"). His template columns (boss_arcanist_doan_rework,
-- AIName '', 46k, immunity 1972, INSTANCE_BIND), the Arcane Anchor 300919 and the spells 212670-212686 are
-- apps/dbc-tools source/npcs/scarlet_monastery/doan.py; S0's rev (rev_skeleton_scarlet_monastery.sql) drops his 7
-- SmartAI rows. His stock spawn (guid 40124) and patrol path 401240 are unchanged. The anchors and the seal are
-- summoned by the script (no spawn here).

-- His new texts (LIB "Text": groups 0-1 are the stock rows, kept; 2-3 are D8H's, the Heresy). Both are boss emotes
-- (type 41), map-wide (TextRange 3: an emote's own range is 25 yd, and the seal's must reach the stragglers it pulls in
-- from the outer hall).
DELETE FROM `creature_text` WHERE `CreatureID` = 6487 AND `GroupID` BETWEEN 4 AND 5;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(6487, 4, 0, '%s seals his chamber with an arcane barrier!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Arcanist Doan - the Chamber Seal (DN0)'),
(6487, 5, 0, 'The bubble shatters! %s is Overloaded!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Arcanist Doan - Overloaded (DN1, every anchor broken)');

-- DN0 the Chamber Seal (section 7 #22 A; S0 section 5 #2: the template is D8's). The kit's SealedArena summons it
-- across the 1.5-2.8 yd doorway to the outer hall 3 s after the pull and despawns it on his death, a wipe or an evade
-- (no spawn: a summoned object never outlives the fight or a reload). A DOOR (type 0) summoned closed
-- (GO_STATE_READY) on GODI 523 RazorfenForceField01 (0.6 x 9.5 x 9.2 yd at size 1, VR) at size 0.42: about 4 yd wide
-- and tall (NAVMESH misfit 6). The display is DoanLogic.h kSealDisplay, the size kSealSize (pinned by
-- lib/test_scarlet_monastery_doan.py). Not selectable and locked (addon flags 0x2 | 0x10 | 0x20: nobody opens it by
-- hand; NODESPAWN). Upserts: gameobject_template rows are never deleted (codestyle-sql not_delete).
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`,
    `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`,
    `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`,
    `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301319, 0, 523, 'Chamber Seal', '', '', '', 0.42, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, '', '', 0)
ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`), `name` = VALUES(`name`),
    `size` = VALUES(`size`), `Data0` = VALUES(`Data0`), `Data1` = VALUES(`Data1`), `AIName` = VALUES(`AIName`),
    `ScriptName` = VALUES(`ScriptName`);
DELETE FROM `gameobject_template_addon` WHERE `entry` = 301319;
INSERT INTO `gameobject_template_addon` (`entry`, `faction`, `flags`, `mingold`, `maxgold`, `artkit0`, `artkit1`,
    `artkit2`, `artkit3`) VALUES
(301319, 0, 50, 0, 0, 0, 0, 0, 0);
