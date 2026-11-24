-- Scarlet Monastery build WP-D3, the council: Azshir the Sleepless (6490) and the Fallen Champion (6488)
-- (.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.5 row D3, s7 #18 A; build spec
-- docs/dungeons/scarlet-monastery-1-graveyard.md "Azshir and the Fallen Champion rework", Text). The templates, the
-- spells and their script bindings are apps/dbc-tools source/npcs/scarlet_monastery/council.py; WP-S0's rev dropped
-- both SmartAIs (the despawn rolls with them) and set Azshir's respawn to 86400.

-- Neither unit had stock lines. Yells 14, boss emotes 41 (handoff s3.5 rule 2).
DELETE FROM `creature_text` WHERE `CreatureID` IN (6490, 6488);
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(6490, 0, 0, 'Rise, brother! The vigil is not over!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Azshir the Sleepless - The Last Vigil (CV1)'),
(6490, 1, 0, 'Scourge! You will not have his grave!', 14, 0, 100, 0, 0, 0, 0, 0, 'Azshir the Sleepless - Aggro'),
(6490, 2, 0, 'A hammer of light hangs over $n!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Azshir the Sleepless - Execution Sentence (CV8, heroic)'),
(6488, 0, 0, '%s calls on the Seal of Command!', 41, 0, 100, 0, 0, 0, 0, 0, 'Fallen Champion - Seal of Command (CV6b)'),
(6488, 1, 0, '%s calls on the Seal of Righteousness!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Fallen Champion - Seal of Righteousness (CV6c)'),
(6488, 2, 0, '%s calls on the Seal of Justice!', 41, 0, 100, 0, 0, 0, 0, 0, 'Fallen Champion - Seal of Justice (CV6d)'),
(6488, 3, 0, '%s is consumed by grief!', 41, 0, 100, 0, 0, 0, 0, 0, 'Fallen Champion - Grief (CV1)');

-- Section 7 #18 A (NAVMESH misfit 4): the grave's dais has no walk route, so the council fights on the lawn disc
-- (1798.5, 1348.5, 18.6) (CouncilLogic.h kChampionLawnSpot / kAzshirLawnSpot): the Champion facing south (pi), the
-- way the group comes up the yard, and Azshir 3 yd behind him (north), facing the same way. Both stay where they stand
-- (MovementType 0). The Grave Moss at the old grave, the Hallow's End objects (section 7 #17 A) and the trash round
-- the old spots stay.
UPDATE `creature` SET `position_x` = 1798.5, `position_y` = 1348.5, `position_z` = 18.6, `orientation` = 3.14159,
    `wander_distance` = 0, `MovementType` = 0 WHERE `guid` = 39894 AND `id` = 6488;
UPDATE `creature` SET `position_x` = 1801.5, `position_y` = 1348.5, `position_z` = 18.6, `orientation` = 3.14159,
    `wander_distance` = 0, `MovementType` = 0 WHERE `guid` = 1975841 AND `id` = 6490;
