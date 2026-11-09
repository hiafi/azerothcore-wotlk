-- Stratholme build WP-S7: Grand Crusader Dathrohan (10812) and Balnazzar (10813), the rows dbc-tools cannot declare
-- (.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.5 row S7; build spec
-- docs/dungeons/stratholme-rework.md ST 2077-2166). Their templates (boss_dathrohan_balnazzar_rework on both, AIName
-- '', health, DamageModifier, immunities, INSTANCE_BIND), the Infernal 300608 and the spells 206545-206571 are
-- apps/dbc-tools source/npcs/stratholme/dathrohan_balnazzar.py.

-- SmartAI 10812 (eighteen rows: the aggro line, Crusader Strike, Crusader's Hammer, Holy Strike, the transform 17288
-- and its timed UpdateEntry 10813, Shadow Shock, Mind Blast, Psychic Scream, Sleep, Mind Control, the death line and
-- summon group 1, the UpdateEntry 10812 out of combat) is removed: boss_dathrohan_balnazzar_rework replaces every row
-- (it keeps the strikes, the transform, Mind Blast, the death skeletons and the revert). 10813 has none.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 10812 AND `source_type` = 0;

-- Texts (ST "Text", handoff s7 #14: the rows go on the entry that speaks; the script talks after UpdateEntry with the
-- new entry's groups). Dathrohan 10812: group 0 stock (aggro) kept; groups 1 and 2 held the stock copies of
-- Balnazzar's reveal and death lines (they move to 10813 groups 5 and 7) and become DB1 / DB2's calls. True lines say
-- "the Light"; lies never do (ruling 28). Balnazzar 10813: groups 5-7 new (the stock groups 1 and 2 stay, unused).
-- Groups 8 and 9 (10812) and 10-16 (10813) are S8's (the Grand Lie) and are not touched here. $n is the marked player.
DELETE FROM `creature_text` WHERE `CreatureID` = 10812 AND `GroupID` IN (1, 2, 3, 4);
DELETE FROM `creature_text` WHERE `CreatureID` = 10813 AND `GroupID` IN (5, 6, 7);
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10812, 1, 0, 'Gather in the Light!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Grand Crusader Dathrohan - Sacred Ground, true (DB1)'),
(10812, 2, 0, 'Bow before my Might!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Grand Crusader Dathrohan - Sacred Ground, lie (DB1)'),
(10812, 3, 0, '$n, share the Light''s judgment!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Grand Crusader Dathrohan - Judgment, true (DB2)'),
(10812, 4, 0, '$n, fear my judgment!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Grand Crusader Dathrohan - Judgment, lie (DB2)'),
(10813, 5, 0, 'You fools think you can defeat me so easily? Face the true might of the Nathrezim!', 14, 0, 100, 0,
    0, 0, 0, 0, 'Balnazzar - The Unmasking (DB3)'),
(10813, 6, 0, 'Rise, servant of the Legion!', 14, 0, 100, 0, 0, 0, 0, 0, 'Balnazzar - Inferno (BZ2)'),
(10813, 7, 0, 'Damn you mortals! All my plans of revenge, all my hate...I will be avenged...', 14, 0, 100, 0, 0, 0,
    0, 0, 'Balnazzar - Death');
