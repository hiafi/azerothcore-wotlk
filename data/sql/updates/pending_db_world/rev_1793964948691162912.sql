-- Deadmines Pilot WP-B2: Miner Johnson and the Working Miners (.agents/plans/deadmines-pilot/deadmines-pilot.HANDOFF.md
-- s3.5 row B2; build spec docs/dungeons/deadmines-rework.md "Miner Johnson"). The rows dbc-tools cannot declare.
-- Script binding, health, immunities, the Working Miner entry 300422 and the spells 205230-205234 are
-- apps/dbc-tools source/npcs/deadmines/miner_johnson.py; the 40% spawn roll is the instance script's.

-- Miner Johnson runs boss_miner_johnson_rework (AIName '' from dbc-tools): his SmartAI block goes (the 60% despawn on
-- AI init moves to instance_deadmines_rework, Pierce Armor 12097 to the script, cut to 10 s).
DELETE FROM `smart_scripts` WHERE `entryorguid` = 3586 AND `source_type` = 0;

-- The four nearest stock Defias Miners (598) give way to the summoned Working Miners, which stand on their spots
-- (MinerJohnsonLogic.h kCrew). None has an addon, formation, pool or game event row (read-only SELECTs 2026-11-06);
-- each was respawn-linked to Sneed's Shredder (79223), so those linked_respawn rows go too.
DELETE FROM `creature` WHERE `id` = 598 AND `guid` IN (79194, 79190, 79191, 79185);
DELETE FROM `linked_respawn` WHERE `guid` IN (79194, 79190, 79191, 79185) AND `linkType` = 0;

-- Texts (build spec "Text"; Johnson had no stock lines). Type 14 yell, 41 boss emote (center screen).
DELETE FROM `creature_text` WHERE `CreatureID` IN (3586, 300422);
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(3586, 0, 0, 'Payroll''s spoken for! Get out of my mine!', 14, 0, 100, 0, 0, 0, 0, 0, 'Miner Johnson - Aggro'),
(3586, 1, 0, '%s tosses the crew''s pay!', 41, 0, 100, 0, 0, 0, 0, 0, 'Miner Johnson - Payday'),
(3586, 2, 0, '%s has nobody left to pay!', 41, 0, 100, 0, 0, 0, 0, 0, 'Miner Johnson - Payday stops'),
(300422, 0, 0, '%s pockets his pay and grabs his pick!', 41, 0, 100, 0, 0, 0, 0, 0, 'Working Miner - Paid, joins the fight');
