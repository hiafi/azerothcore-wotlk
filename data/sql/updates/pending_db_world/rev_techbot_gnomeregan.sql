-- Gnomeregan build WP-D1: Techbot (301105) and his Dupe Bug (301106), the rows dbc-tools cannot declare
-- (.agents/plans/gnomeregan-build/gnomeregan-build.HANDOFF.md s3.5 row D1, rule 35; build spec
-- docs/dungeons/gnomeregan-rework.md "## Techbot", Text). The templates (boss_techbot_rework, npc_gnomer_dupe_bug,
-- npc_gnomer_lag_echo) and the spells 214300-214339 are apps/dbc-tools source/npcs/gnomeregan/techbot.py; his spawn
-- (guid 3011050) is rev_skeleton_gnomeregan.sql; his loot (the Memory Core 9277, Guts 9309) is WP-L-1's. The outside
-- Techbot 6231 keeps every stock row (section 7 #14 A).

-- Techbot: group 0, the 13 stock help desk lines of 6231 group 0 copied as they stand (Say, probability 9 each,
-- broadcast ids on lines 9 to 12; SELECT 2026-11-26), one every 15 s in combat; groups 1 to 6, new (SP Text).
DELETE FROM `creature_text` WHERE `CreatureID` = 301105;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(301105, 0, 0, 'There is no COW level!... really! I repeat: there is no COW level. Well,maby there is...', 12, 0, 9, 0, 0, 0, 0, 0,
    'Techbot - chatter (stock 6231 group 0)'),
(301105, 0, 1, 'You are welcome,have a nice day.', 12, 0, 9, 0, 0, 0, 0, 0,
    'Techbot - chatter (stock 6231 group 0)'),
(301105, 0, 2, 'Please be patient,we will call your name when it is your turn. We are helping people in the order they appear to us on the screen.', 12, 0, 9, 0, 0, 0, 0, 0,
    'Techbot - chatter (stock 6231 group 0)'),
(301105, 0, 3, 'People think I like corndogs,but actually,they give me indigestion !!!', 12, 0, 9, 0, 0, 0, 0, 0,
    'Techbot - chatter (stock 6231 group 0)'),
(301105, 0, 4, 'Techbot is sensitive and those words hurt my ears. :[ Please be nice to me. I just want to help.', 12, 0, 9, 0, 0, 0, 0, 0,
    'Techbot - chatter (stock 6231 group 0)'),
(301105, 0, 5, 'I am a BOT. I have tons of information. To find out what I know whisper me.', 12, 0, 9, 0, 0, 0, 0, 0,
    'Techbot - chatter (stock 6231 group 0)'),
(301105, 0, 6, 'When the rep is talking to you,he will start each line with your name. If you don''t see your name,he''s not speaking to you.', 12, 0, 9, 0, 0, 0, 0, 0,
    'Techbot - chatter (stock 6231 group 0)'),
(301105, 0, 7, 'Remember,if you harass the rep or spam the channel,your account may be kicked,banned or worse.', 12, 0, 9, 0, 0, 0, 0, 0,
    'Techbot - chatter (stock 6231 group 0)'),
(301105, 0, 8, 'If you have been muted,or have questions about the Muting/UnMuting process,please visit...zzzzttt!!', 12, 0, 9, 0, 0, 0, 0, 0,
    'Techbot - chatter (stock 6231 group 0)'),
(301105, 0, 9, 'Some topics I can help you with are: | drivers | commands | lag | bots... zzzttt!', 12, 0, 9, 0, 0, 0, 2435, 0,
    'Techbot - chatter (stock 6231 group 0)'),
(301105, 0, 10, 'I love you too. :)', 12, 0, 9, 0, 0, 0, 2437, 0,
    'Techbot - chatter (stock 6231 group 0)'),
(301105, 0, 11, 'Please be patient,we will call your name when it is your turn.', 12, 0, 9, 0, 0, 0, 2437, 0,
    'Techbot - chatter (stock 6231 group 0)'),
(301105, 0, 12, 'We are helping people in the order they appear to us on our screen. $N!', 12, 0, 9, 0, 0, 0, 2437, 0,
    'Techbot - chatter (stock 6231 group 0)'),
(301105, 1, 0, '$n''s connection is unstable.', 41, 0, 100, 0, 0, 0, 0, 0,
    'Techbot - Lag Spike (TB1)'),
(301105, 2, 0, 'Downloading patch. Please do not turn off your Techbot.', 14, 0, 100, 0, 0, 0, 0, 0,
    'Techbot - Patch: Backup Restore (TB4)'),
(301105, 3, 0, 'Patch complete. Known issues resolved. Thank you for your patience.', 14, 0, 100, 0, 0, 0, 0, 0,
    'Techbot - Patch with bugs deleted (TB4)'),
(301105, 4, 0, 'No known issues found... zzzttt!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Techbot - Patch with no bug (TB4)'),
(301105, 5, 0, 'Shutting down. Thank you for contacting Technical Support. Have a nice day.', 14, 0, 100, 0, 0, 0, 0, 0,
    'Techbot - Shutdown (TB9)'),
(301105, 6, 0, '$n is rubber-banding!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Techbot - Rubber Band (TB6, heroic)');

-- Dupe Bug: group 0, the Duplication emote (TB3; the Duplicator machine says it as the bar starts).
DELETE FROM `creature_text` WHERE `CreatureID` = 301106;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(301106, 0, 0, '%s begins to duplicate!', 41, 0, 100, 0, 0, 0, 0, 0, 'Dupe Bug - Duplication (TB3)');
