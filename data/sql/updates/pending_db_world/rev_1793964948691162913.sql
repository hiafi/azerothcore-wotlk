-- Deadmines Pilot WP-B3: Sneed's Shredder (642) and Sneed (643), the rows dbc-tools cannot declare
-- (.agents/plans/deadmines-pilot/deadmines-pilot.HANDOFF.md s3.5 row B3). Their templates (boss_sneeds_shredder_rework,
-- boss_sneed_rework, AIName '', health, immunities) and spells are apps/dbc-tools source/npcs/deadmines/sneed.py. The
-- Shredder's spawn 79223 and its patrol (creature_addon path 792230) stay: mod-dungeon-clear anchors Sneed's encounter
-- at that spawn. Its loot (Gnoam Sprecklesprocket 7365 at 100%) is untouched.

-- SmartAI 642 (Terrify 7399, Distracting Pain 3603, Eject Sneed 5141 on death) and 643 (Disarm 6713, the Mast Room
-- door on death) are replaced by the two scripts: Terrify, Distracting Pain and Disarm are removed (ruling 21), the
-- eject is boss_sneeds_shredder_rework's and the door is the instance's door data (BOSS_SNEED DONE). Both blocks go.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 642 AND `source_type` = 0;
DELETE FROM `smart_scripts` WHERE `entryorguid` = 643 AND `source_type` = 0;

-- Texts (neither had any). The malfunction, repair and overload emotes are boss emotes (41), so they name the
-- mechanic on screen; Sneed's eject line is a yell.
DELETE FROM `creature_text` WHERE `CreatureID` IN (642, 643);
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(642, 0, 0, 'Sneed''s Shredder''s saws spin out of control!', 41, 0, 100, 0, 0, 0, 0, 0, 'Sneed''s Shredder - Haywire: Saw Spin (SN1)'),
(642, 1, 0, 'Sneed''s Shredder spews splinters!', 41, 0, 100, 0, 0, 0, 0, 0, 'Sneed''s Shredder - Haywire: Splinter Spray (SN2)'),
(642, 2, 0, 'Sneed''s Shredder lurches out of control!', 41, 0, 100, 0, 0, 0, 0, 0, 'Sneed''s Shredder - Haywire: Runaway (SN3)'),
(642, 3, 0, 'Sneed''s Shredder begins to overload!', 41, 0, 100, 0, 0, 0, 0, 0, 'Sneed''s Shredder - Wreck Overload (SN9)'),
(643, 0, 0, 'You break it, you buy it!', 14, 0, 100, 0, 0, 0, 0, 0, 'Sneed - Eject'),
(643, 1, 0, '%s scrambles back to his Shredder!', 41, 0, 100, 0, 0, 0, 0, 0, 'Sneed - Emergency Repairs (SN7)'),
(643, 2, 0, '%s is back in business!', 41, 0, 100, 0, 0, 0, 0, 0, 'Sneed - Reboot (SN8)'),
(643, 3, 0, '%s pries a saw blade out of the wreckage!', 41, 0, 100, 0, 0, 0, 0, 0, 'Sneed - Salvaged Saw (SN12)');
