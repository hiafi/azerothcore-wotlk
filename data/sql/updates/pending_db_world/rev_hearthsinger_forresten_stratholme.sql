-- Stratholme build WP-S2: Hearthsinger Forresten (10558), the rows dbc-tools cannot declare
-- (.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.5 row S2; build spec
-- docs/dungeons/stratholme-rework.md ST 826-882). His template (boss_hearthsinger_forresten_rework, AIName '', health,
-- DamageModifier 3.5, immunities, INSTANCE_BIND), the Gutter Rat 300602, the hearth stalker 300603 and his spells
-- 206440-206448 are apps/dbc-tools source/npcs/stratholme/hearthsinger_forresten.py.

-- Hearthsinger Forresten: SmartAI 10558 is removed (ST "Stock kit"), all five rows: Incorporeal Defense 16331 on
-- reset (dead on this server), Shoot 16100 and Multi-Shot 14443 (the script casts them, in the breaks between songs),
-- Demoralizing Shout 16244 (retired) and Enchanting Lullaby 16798 (The Lullaby is the hearth and Drowsy now).
DELETE FROM `smart_scripts` WHERE `entryorguid` = 10558 AND `source_type` = 0;

-- His lines (ST "Text"; he had none): the yells are type 14; the Crescendo line is a boss emote (41), so it names the
-- mechanic on screen.
DELETE FROM `creature_text` WHERE `CreatureID` = 10558;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10558, 0, 0, 'An audience! It has been so long since anyone stayed for the whole set.', 14, 0, 100, 0, 0, 0, 0, 0,
    'Hearthsinger Forresten - Aggro'),
(10558, 1, 0, 'Something lively! On your feet, everyone, dance!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Hearthsinger Forresten - The Jig (HF1)'),
(10558, 2, 0, 'Hush now. Gather round the hearth.', 14, 0, 100, 0, 0, 0, 0, 0,
    'Hearthsinger Forresten - The Lullaby (HF1)'),
(10558, 3, 0, 'Come out, little ones. Come and hear me play!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Hearthsinger Forresten - The Piper''s Tune (HF1)'),
(10558, 4, 0, '%s builds toward a crescendo!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Hearthsinger Forresten - Crescendo (HF8)'),
(10558, 5, 0, 'The song... was never meant to end...', 14, 0, 100, 0, 0, 0, 0, 0,
    'Hearthsinger Forresten - Death');
