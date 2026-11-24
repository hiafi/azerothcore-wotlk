-- Scarlet Monastery build WP-D2: Ironspine (6489), the rows dbc-tools cannot declare
-- (.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.5 row D2, s3.8, s7 #24 A; build spec
-- docs/dungeons/scarlet-monastery-1-graveyard.md GY 378-433). His template (boss_ironspine_rework, 36k, immunity 1972,
-- INSTANCE_BIND), the parts 300900-300902 and spells 212350-212366 are apps/dbc-tools
-- source/npcs/scarlet_monastery/ironspine.py; his stock SmartAI (the 90% despawn on AI init, Curse of Weakness 702,
-- Poison Cloud 3815) went with WP-S0's rev_skeleton_scarlet_monastery.sql.

-- Section 7 #24 A: his stock spawn sits in a walled 22 x 55 yd plot where the pool math fails; he moves to the open
-- lawn (1796.5, 1285.5, 18.8): clearance 18.3, 1,242 sq yd within 20 yd (99% floor) [navmesh estimate]. Facing the
-- yard's entry (south-west). Same guid, same entry, same spawnMask (WP-H's generated heroic rev widens it).
UPDATE `creature` SET `position_x` = 1796.5, `position_y` = 1285.5, `position_z` = 18.8, `orientation` = 4.28
    WHERE `guid` = 12164 AND `id` = 6489;

-- His texts (GY "Text"; Ironspine had none) and the Eye's: boss emotes (41), $n the Ribcage's prisoner. The Eye's
-- Glare (hits to 40 yd) and the Ribcage (lands 15-20 yd out) emote to the map (TextRange 3): a type 41 emote's
-- default range is 25 yd (R-1-GY MN-2).
DELETE FROM `creature_text` WHERE `CreatureID` = 6489 AND `GroupID` BETWEEN 0 AND 3;
DELETE FROM `creature_text` WHERE `CreatureID` = 300902 AND `GroupID` = 0;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(6489, 0, 0, '%s retches up grave rot.', 41, 0, 100, 0, 0, 0, 0, 0, 'Ironspine - Grave Rot (IR1)'),
(6489, 1, 0, '%s''s bones crack apart!', 41, 0, 100, 0, 0, 0, 0, 0, 'Ironspine - Shatter (IR2)'),
(6489, 2, 0, '%s is nothing but rot and iron!', 41, 0, 100, 0, 0, 0, 0, 0, 'Ironspine - all three parts killed (IR2)'),
(6489, 3, 0, 'The ribcage closes over $n!', 41, 0, 100, 0, 0, 0, 0, 3, 'Ironspine - the Ribcage (IR4)'),
(300902, 0, 0, '%s opens wide!', 41, 0, 100, 0, 0, 0, 0, 3, 'Ironspine''s Eye - Glare (IR6, heroic)');
