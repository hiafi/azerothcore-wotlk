-- Stratholme build WP-S9: Magistrate Barthilas (10435), the rows dbc-tools cannot declare
-- (.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.5 row S9; build spec
-- docs/dungeons/stratholme-rework.md ST 2355-2407). His template (boss_magistrate_barthilas_rework, AIName '', health,
-- DamageModifier, immunities, INSTANCE_BIND), the stalkers 300580 / 300581 and the spells 206605-206614 are
-- apps/dbc-tools source/npcs/stratholme/magistrate_barthilas.py.

-- Magistrate Barthilas: SmartAI 10435 is removed (ST "Stock kit"), all 19 rows: Furious Anger 16791 becomes Fever
-- (206613), Crowd Pummel 10887 leaves his kit, Mighty Blow 14099, Draining Blow 16793 and the Transformation 16794
-- look are cast by the script, the portcullises 175377 / 175372 are the rework instance's door data on his boss state,
-- and his run (path 104350, the Slaughterhouse teleport and the home on respawn) is gone.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 10435 AND `source_type` = 0;
-- The three conditions on those rows (SourceGroup = row id + 1: the run's invoker check, the attack-player state and
-- the respawn teleport's instance data check) go with them.
DELETE FROM `conditions` WHERE `SourceTypeOrReferenceId` = 22 AND `SourceEntry` = 10435 AND `SourceId` = 0;

-- The Service Entrance Gate 175368: its gossip row set data on him (the run). The rework instance opens the gate on
-- create (handoff s10, section 2 entry), so the row and its SmartAI binding go; the Key to the City lock stays.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 175368 AND `source_type` = 1;
UPDATE `gameobject_template` SET `AIName` = '' WHERE `entry` = 175368;

-- His lines (ST "Text"): group 0 is stock (BroadcastText 6162, now his aggro yell) and stays; 1-5 are new. The cough is
-- a boss emote (41), so it names the mechanic on screen; the rest are yells, lines 3 and 5 his own Culling lines.
DELETE FROM `creature_text` WHERE `CreatureID` = 10435 AND `GroupID` BETWEEN 1 AND 5;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10435, 1, 0, '%s coughs on $n.', 41, 0, 100, 0, 0, 0, 0, 0, 'Magistrate Barthilas - Infection (BT1)'),
(10435, 2, 0, 'Quarantine! Separate the sick from the well!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Magistrate Barthilas - Quarantine (BT6)'),
(10435, 3, 0, 'The city will fall into bedlam!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Magistrate Barthilas - Bedlam (BT9, heroic)'),
(10435, 4, 0, 'It was the grain... it was always the grain!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Magistrate Barthilas - Plagued Grain (BT4)'),
(10435, 5, 0, 'What can one simple man do in the face of disaster?', 14, 0, 100, 0, 0, 0, 0, 0,
    'Magistrate Barthilas - Death');
