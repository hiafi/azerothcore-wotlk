-- Zul'Farrak build WP-D4b: the Stair and the Altar of the Pyramid, the rows dbc-tools cannot declare
-- (.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.5 row D4b; build spec
-- docs/dungeons/zul-farrak-rework.md "The Pyramid", Text). Sezz'ziz's and Nekrum's templates (boss_sezzziz_rework,
-- boss_nekrum_rework), the specialists 301015-301017, Weegli's barrel 301018 and the spells 213990-214029 are
-- apps/dbc-tools source/npcs/zul_farrak/pyramid_stair.py; Nekrum's SmartAI rows and Sezz'ziz's stock ScriptName go
-- with rev_skeleton_zul_farrak.sql; Weegli's barrel yell (7607 group 3) is CR's rev_crew_zul_farrak.sql.

-- PY12 Blood Offering: the emote as the cast starts, new (Sezz'ziz has no stock text).
DELETE FROM `creature_text` WHERE `CreatureID` = 7275 AND `GroupID` = 0;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(7275, 0, 0, '%s offers $n''s blood to the loa!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Shadowpriest Sezz''ziz - Blood Offering (PY12)');

-- The specialists carry their sources' weapons (Blood Drinker 5649, Shadowcaster 5648, Witch Doctor 5650).
DELETE FROM `creature_equip_template` WHERE `CreatureID` IN (301015, 301016, 301017) AND `ID` = 1;
INSERT INTO `creature_equip_template` (`CreatureID`, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, `VerifiedBuild`) VALUES
(301015, 1, 4991, 0, 0, 0),
(301016, 1, 6230, 0, 0, 0),
(301017, 1, 1908, 0, 0, 0);
