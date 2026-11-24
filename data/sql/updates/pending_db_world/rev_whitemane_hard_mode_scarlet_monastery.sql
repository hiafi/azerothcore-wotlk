-- Scarlet Monastery build WP-D14H: High Inquisitor Whitemane's hard mode, The Truth (heroic only), the rows dbc-tools
-- cannot declare (.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.7, s3.5 row D14H,
-- s7 #21 A; build spec docs/dungeons/scarlet-monastery-4-cathedral.md "Hard mode: The Truth", "Text (hard mode)").
-- The vigil Fairbanks 300956, the spirit 300957 and the spells 213190-213207 are apps/dbc-tools
-- source/npcs/scarlet_monastery/whitemane_hard_mode.py; the engine side is modules/mod-dungeon-bosses
-- src/ScarletMonastery/whitemane_hard_mode.cpp. This rev inserts no spawn (both units are summoned by the script) and
-- no SmartAI row (rule 14).

-- The texts. The vigil Fairbanks's line at his death (HM2, say); the spirit's: 0 and 1 copied from Highlord Mograine
-- 16062's lines 0 and 2 (broadcast 12469 / 12473, the Ashbringer event's; the cameo keeps its own), 2 the Verdict's
-- raid emote (type 41, hub ruling 54); Whitemane's group 6 (HM2, yell: D14 owns 3-5 and 7). Mograine's lines 4-5
-- ("Father... But... How?", "Forgive me, father! Please...") are his stock rows, used as they are.
DELETE FROM `creature_text` WHERE `CreatureID` IN (300956, 300957);
DELETE FROM `creature_text` WHERE `CreatureID` = 3977 AND `GroupID` = 6;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(300956, 0, 0, 'Ask him... how his father died.', 12, 0, 100, 0, 0, 0, 0, 0,
    'High Inquisitor Fairbanks (at the vigil) - his death: the Truth (D14H, HM2)'),
(300957, 0, 0, 'Renault...', 12, 0, 100, 25, 0, 0, 12469, 0,
    'Highlord Mograine (the spirit of Alexandros) - he rises over the altar (D14H, HM2)'),
(300957, 1, 0, 'You are forgiven...', 12, 0, 100, 0, 0, 0, 12473, 0,
    'Highlord Mograine (the spirit of Alexandros) - the pair dies: the ending (D14H, HM5)'),
(300957, 2, 0, '%s raises the Ashbringer!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Highlord Mograine (the spirit of Alexandros) - the Verdict (D14H, HM3a)'),
(3977, 6, 0, 'Lies! He is the Crusade''s champion!', 14, 0, 100, 0, 0, 0, 0, 0,
    'High Inquisitor Whitemane - she refuses the Truth (D14H, HM2)');

-- The Torch 97701 (section 7 #21 A): its SmartGameObjectAI row ("on state changed: activate the Secret Door", guid
-- 11876) gives way to go_sm_torch, which opens the Secret Door as stock on normal (and on every difficulty while wave 2
-- is unbound) and is the hard mode's trigger on heroic. Bound on every wave together with the script's registration
-- (a ScriptName with no script, or SmartAI rows on a scripted object, are boot errors).
DELETE FROM `smart_scripts` WHERE `entryorguid` = 97701 AND `source_type` = 1;
UPDATE `gameobject_template` SET `AIName` = '', `ScriptName` = 'go_sm_torch' WHERE `entry` = 97701;
