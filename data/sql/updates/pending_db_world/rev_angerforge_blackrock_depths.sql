-- Blackrock Depths build WP-D14: General Angerforge (9033) and his squads, the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D14; build spec
-- docs/dungeons/blackrock-depths-3-manufactory.md S3 "General Angerforge"). His template
-- (boss_general_angerforge_rework behind the wave switch, 150k, immunity 1972, INSTANCE_BIND), the three squad entries
-- 300830-300832 and spells 211300-211311 are apps/dbc-tools source/npcs/blackrock_depths/angerforge.py. He has no
-- stock smart_scripts rows (the stock script is C++), so there is nothing to drop; the stock Reservists 8901, Medics
-- 8894 and Officers 8895 (trash across the dungeon) are untouched. Wave 2: everything here is inert until the wave
-- switch flips (nothing spawns the squad entries or the machine, and the texts are read only by the reworked script).

-- His texts (S3 "Text"; he had none): the pull, the reinforcement call and the death are yells (14); the grenade is a
-- boss emote (41) so it reads on screen, with the target's name for $n.
DELETE FROM `creature_text` WHERE `CreatureID` = 9033 AND `GroupID` BETWEEN 0 AND 3;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(9033, 0, 0, 'Intruders in the Shadowforge! To arms!', 14, 0, 100, 0, 0, 0, 0, 0, 'General Angerforge - Pull'),
(9033, 1, 0, 'Reinforcements, up from below!', 14, 0, 100, 0, 0, 0, 0, 0,
    'General Angerforge - Deploy Mole Machine (AF3)'),
(9033, 2, 0, '%s lobs a Fireburst Grenade at $n!', 41, 0, 100, 0, 0, 0, 0, 0,
    'General Angerforge - Fireburst Grenade (AF6)'),
(9033, 3, 0, 'The Emperor... will avenge...', 14, 0, 100, 0, 0, 0, 0, 0, 'General Angerforge - Death');

-- 301289 Mole Machine (display 7510, the Dark Iron Mole Machine, size 0.6 = about 6.8 x 7 x 11.5 yd): a generic object
-- (type 5: no lock, no click, a collision model) the script summons at one of four fixed spots on the hall's edge,
-- keeps for 3 s and deletes. Not selectable (addon flags 16). No spawn: Angerforge summons it (a 12 s despawn timer
-- is the backstop).
-- Upserts: gameobject_template rows are never deleted (codestyle-sql not_delete).
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`,
    `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`,
    `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`,
    `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301289, 5, 7510, 'Mole Machine', '', '', '', 0.6, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, '', '', 0) ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`),
    `name` = VALUES(`name`), `size` = VALUES(`size`), `Data0` = VALUES(`Data0`), `AIName` = VALUES(`AIName`),
    `ScriptName` = VALUES(`ScriptName`);
DELETE FROM `gameobject_template_addon` WHERE `entry` = 301289;
INSERT INTO `gameobject_template_addon` (`entry`, `faction`, `flags`, `mingold`, `maxgold`, `artkit0`, `artkit1`,
    `artkit2`, `artkit3`) VALUES
(301289, 0, 16, 0, 0, 0, 0, 0, 0);

-- 300831 Anvilrage Squad Reservist: the stock Reservist's kit (S3 "the Reservist keeps its stock kit"), the stock
-- 8901 rows 0-3 as they are: Battle Shout 9128 on aggro, Shoot 6660 in combat (moving to cast), Hamstring 9080 every
-- 12-15 s, Strike 11976 every 6-9 s. Left out on purpose: row 4, "Between 0-15% Health - Flee For Assist" (a squad
-- member that runs off drags the lower level's pack into the fight and leaves the kill order). event_flags carry the
-- heroic bit (4) as well as the normal one (2; 1 = no repeat), so the rows run on both difficulties (rule 14: this rev
-- sorts after the generated heroic rev, so it widens its own rows).
DELETE FROM `smart_scripts` WHERE `entryorguid` = 300831 AND `source_type` = 0;
INSERT INTO `smart_scripts` (`entryorguid`, `source_type`, `id`, `link`, `event_type`, `event_phase_mask`,
    `event_chance`, `event_flags`, `event_param1`, `event_param2`, `event_param3`, `event_param4`, `event_param5`,
    `event_param6`, `action_type`, `action_param1`, `action_param2`, `action_param3`, `action_param4`, `action_param5`,
    `action_param6`, `target_type`, `target_param1`, `target_param2`, `target_param3`, `target_param4`, `target_x`,
    `target_y`, `target_z`, `target_o`, `comment`) VALUES
(300831, 0, 0, 0, 4, 0, 100, 7, 0, 0, 0, 0, 0, 0, 11, 9128, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'Anvilrage Squad Reservist - On Aggro - Cast ''Battle Shout'' (No Repeat)'),
(300831, 0, 1, 0, 0, 0, 100, 6, 0, 0, 2200, 3800, 0, 0, 11, 6660, 64, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0,
    'Anvilrage Squad Reservist - In Combat CMC - Cast ''Shoot'''),
(300831, 0, 2, 0, 0, 0, 100, 6, 4000, 6000, 12000, 15000, 0, 0, 11, 9080, 1, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0,
    'Anvilrage Squad Reservist - In Combat - Cast ''Hamstring'''),
(300831, 0, 3, 0, 0, 0, 100, 6, 8000, 11000, 6000, 9000, 0, 0, 11, 11976, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0,
    'Anvilrage Squad Reservist - In Combat - Cast ''Strike''');
