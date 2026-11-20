-- Blackrock Depths build WP-D7: Pyromancer Loregrain (9024), the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D7; build spec
-- docs/dungeons/blackrock-depths-2-shadowforge-city.md S2 165-219). His template (boss_pyromancer_loregrain_rework,
-- AIName '', health, DamageModifier 3.5, immunities, INSTANCE_BIND), the Defiling Totem 300792 and his spells
-- 211020-211035 are apps/dbc-tools source/npcs/blackrock_depths/loregrain.py. His four SmartAI rows are removed by
-- rev_blackrock_depths_skeleton.sql (WP-S0), not here. No spawn is inserted or re-entered (rule 14: nothing here needs
-- the heroic spawn bit).

-- The two Twilight Emissaries at his feet (spawn guids 47772 and 47773, entry 8913) leave (S2 "Stock kit"): they cast
-- Fireball, Frostbolt and Blizzard and buff him with Fury of Ragnaros. The entry's other spawns stay. No formation,
-- pool, linked respawn or game event row names either spawn (checked 2026-11-17).
DELETE FROM `creature` WHERE `id` = 8913 AND `guid` IN (47772, 47773);
DELETE FROM `creature_addon` WHERE `guid` IN (47772, 47773);

-- His stock addon aura Fury of Ragnaros 15288 (+25 magic damage done) becomes the Fury meter 211031, which the script
-- builds from 0 at each pull (S2 "Stock kit"). The rest of the row (the kneel at the statue, bytes1 8) is kept.
UPDATE `creature_addon` SET `auras` = NULL WHERE `guid` = 47771;

-- Texts (S2 "Text"; he had none): yells are type 14, the ward's move is a boss emote (41) so it names the moment on
-- screen (rule 2). Franclorn's Spirit 9542 (no spawns; summoned by the boss script) thanks the group at the statue on
-- the kill: a say (12). Its group 1 is D10's (the short-lived copy at Fineous's corpse) and is left alone.
DELETE FROM `creature_text` WHERE `CreatureID` = 9024;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(9024, 0, 0, 'This shrine belongs to the Firelord now!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Pyromancer Loregrain - Aggro'),
(9024, 1, 0, 'Drown in Ragnaros''s fire!', 14, 0, 100, 0, 0, 0, 0, 0, 'Pyromancer Loregrain - Fire Tide (LG1)'),
(9024, 2, 0, 'The Firelord''s fury overflows!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Pyromancer Loregrain - Wrath of Ragnaros (LG7)'),
(9024, 3, 0, 'The flame... gutters...', 14, 0, 100, 0, 0, 0, 0, 0, 'Pyromancer Loregrain - Death'),
(9024, 4, 0, 'Franclorn''s spirit moves to new ground!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Pyromancer Loregrain - The ward moves (LG2)');

DELETE FROM `creature_text` WHERE `CreatureID` = 9542 AND `GroupID` = 0;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(9542, 0, 0, 'My shrine stands, and so does my legacy. You have my thanks.', 12, 0, 100, 0, 0, 0, 0, 0,
    'Franclorn''s Spirit - Pyromancer Loregrain killed');
