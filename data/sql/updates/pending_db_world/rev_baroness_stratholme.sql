-- Stratholme build WP-S10: Baroness Anastari (10436), the rows dbc-tools cannot declare
-- (.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.5 row S10; build spec
-- docs/dungeons/stratholme-rework.md ST 2630-2677). Her template (boss_baroness_anastari_rework, AIName '', health,
-- DamageModifier 3.5, immunities, INSTANCE_BIND) and her spells 206625-206635 are apps/dbc-tools
-- source/npcs/stratholme/baroness_anastari.py.
--
-- She has no smart_scripts rows (the stock boss was C++ only: boss_baroness_anastari, which stays registered and is
-- unbound by the template edit), so none are removed here. Her stock creature_text is empty too.

-- Texts (ST "Text", approved 2026-11-04; she had none): the yells are type 14; the three mechanic lines are boss emotes
-- (41), so each names the moment on screen. $n is the player: the doomed (line 1) or the one she turns to (line 3).
DELETE FROM `creature_text` WHERE `CreatureID` = 10436;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10436, 0, 0, 'Who disturbs my mourning?', 14, 0, 100, 0, 0, 0, 0, 0, 'Baroness Anastari - Aggro'),
(10436, 1, 0, '%s keens for $n!', 41, 0, 100, 0, 0, 0, 0, 0, 'Baroness Anastari - The Keening (BA1)'),
(10436, 2, 0, '%s begins to wail!', 41, 0, 100, 0, 0, 0, 0, 0, 'Baroness Anastari - Wail of the Banshee (BA4)'),
(10436, 3, 0, '%s lifts her veil toward $n.', 41, 0, 100, 0, 0, 0, 0, 0, 'Baroness Anastari - Horrifying Visage (BA6)'),
(10436, 4, 0, 'Weep for the living!', 14, 0, 100, 0, 0, 0, 0, 0, 'Baroness Anastari - Lament for the Living (heroic BA7)'),
(10436, 5, 0, 'At last... silence.', 14, 0, 100, 0, 0, 0, 0, 0, 'Baroness Anastari - Death');
