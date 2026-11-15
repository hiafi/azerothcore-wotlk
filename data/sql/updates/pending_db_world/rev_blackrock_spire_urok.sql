-- Blackrock Spire build WP-B5: Urok Doomhowl (10584), the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.5 row B5; build spec
-- docs/dungeons/blackrock-spire-rework.md SP 1617-1688, UR1-UR11, rulings 37-39). His template, the shard 300706 and
-- the spells are apps/dbc-tools source/npcs/blackrock_spire/urok.py; the C++ is modules/mod-dungeon-bosses
-- src/BlackrockSpire/boss_urok_doomhowl_rework.cpp.

-- UR1: the challenge moves into C++ (Urok owns the prelude; the pile's script starts it). The stock gameobject SmartAI
-- goes: Urok's Tribute Pile 175621 (Spawn Challenge to Urok 16447 hit: summon the challenge, the 20-count fail),
-- the Challenge to Urok 175584 (the action list and its cast) and the action list 17558400 (6 circles, 11 ogres, Urok).
DELETE FROM `smart_scripts` WHERE `entryorguid` = 175621 AND `source_type` = 1;
DELETE FROM `smart_scripts` WHERE `entryorguid` = 175584 AND `source_type` = 1;
DELETE FROM `smart_scripts` WHERE `entryorguid` = 17558400 AND `source_type` = 9;

-- The ogres keep their stock combat rows (Urok Enforcer 10601: Strike 14516, id 0; Urok Ogre Magus 10602: Arcane Bolt
-- 15979, Slow 13747 and Bloodlust 6742, ids 0-2) and lose the fail and pike rows (the 30 s out-of-combat fail, the
-- teleport, the walk to the pike and its emotes, the phase rows): the boss script sends them at the players and owns
-- the 30 s fail (SP 1640-1642). The whole block is rewritten (sql-guidelines). The kept rows carry the heroic
-- difficulty bit (event_flags | 4): this rev sorts after the generated revs that widen map 229's normal-only rows.
DELETE FROM `smart_scripts` WHERE `entryorguid` IN (10601, 10602) AND `source_type` = 0;
INSERT INTO `smart_scripts` (`entryorguid`, `source_type`, `id`, `link`, `event_type`, `event_phase_mask`,
    `event_chance`, `event_flags`, `event_param1`, `event_param2`, `event_param3`, `event_param4`, `event_param5`,
    `event_param6`, `action_type`, `action_param1`, `action_param2`, `action_param3`, `action_param4`,
    `action_param5`, `action_param6`, `target_type`, `target_param1`, `target_param2`, `target_param3`,
    `target_param4`, `target_x`, `target_y`, `target_z`, `target_o`, `comment`) VALUES
(10601, 0, 0, 0, 9, 0, 100, 6, 0, 0, 5000, 9000, 0, 5, 11, 14516, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0,
    'Urok Enforcer - Within 0-5 Range - Cast ''Strike'''),
(10602, 0, 0, 0, 0, 0, 100, 6, 0, 0, 4400, 5700, 0, 0, 11, 15979, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0,
    'Urok Ogre Magus - In Combat CMC - Cast ''Arcane Bolt'''),
(10602, 0, 1, 0, 0, 0, 100, 6, 8000, 11000, 17000, 24000, 0, 0, 11, 13747, 1, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0,
    'Urok Ogre Magus - In Combat - Cast ''Slow'''),
(10602, 0, 2, 0, 2, 0, 100, 7, 0, 30, 30000, 35000, 0, 0, 11, 6742, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Urok Ogre Magus - Between 0-30% Health - Cast ''Bloodlust'' (No Repeat)');

-- The pile becomes a usable object (ruling 39: no item; it works once Omokk is dead, and again after a wipe): a goober
-- (type 10, no lock, no quest) bound to go_brs_urok_pile, which reads the instance's pile state. It was a spell focus
-- (type 8, focus 743) for Spawn Challenge to Urok 16447 (the Roughshod Pike and Omokk's Head are cut by WP-L-1). The
-- challenge's pike 175584 is a prop now (the script spawns it not selectable): no SmartAI either.
UPDATE `gameobject_template` SET `type` = 10, `Data0` = 0, `Data1` = 0, `Data2` = 0, `Data3` = 0, `AIName` = '',
    `ScriptName` = 'go_brs_urok_pile' WHERE `entry` = 175621;
UPDATE `gameobject_template` SET `AIName` = '' WHERE `entry` = 175584;

-- Texts: lines 0 (the arrival yell) and 1 (the aggro say, now called) are stock; 2-5 are new (emotes are type 41, a
-- boss emote).
DELETE FROM `creature_text` WHERE `CreatureID` = 10584 AND `GroupID` BETWEEN 2 AND 5;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10584, 2, 0, '%s draws a deep breath!', 41, 0, 100, 0, 0, 0, 0, 0, 'Urok Doomhowl - Doomhowl'),
(10584, 3, 0, '%s drinks in the stolen magic!', 41, 0, 100, 0, 0, 0, 0, 0, 'Urok Doomhowl - Stolen Power'),
(10584, 4, 0, 'The stolen magic boils inside %s!', 41, 0, 100, 0, 0, 0, 0, 0, 'Urok Doomhowl - Overcharge'),
(10584, 5, 0, 'Magic... was... Urok''s...', 14, 0, 100, 0, 0, 0, 0, 0, 'Urok Doomhowl - Death');
