-- Blackrock Depths build WP-D12: Lord Incendius's hard mode, Lord of the Lake (9017), the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D12, s3.7; build spec
-- docs/dungeons/blackrock-depths-2-shadowforge-city.md "Hard mode", Text). The Lava Spawn 300795 and the spells
-- 211180-211191 are apps/dbc-tools source/npcs/blackrock_depths/incendius_hard_mode.py; the Cinder of the Firelord
-- (item 70621, spell 211260) is rev_event_items_blackrock_depths.sql and event_items.py; D11's rev holds his texts 0-7
-- (4, 6 and 7 are the hard mode's lines, said by this WP's C++).

-- His texts, groups 8-9 (D11 owns 0-7 and deletes only those): boss emotes (41), map-wide (TextRange 3, R-1-B n1).
DELETE FROM `creature_text` WHERE `CreatureID` = 9017 AND `GroupID` BETWEEN 8 AND 9;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(9017, 8, 0, '%s rises from the lake of fire!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Lord Incendius - Lord of the Lake rises (IN9, D12)'),
(9017, 9, 0, 'Lava Spawn climb out of the lake!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Lord Incendius - Lava Spawn (IN12, D12)');
