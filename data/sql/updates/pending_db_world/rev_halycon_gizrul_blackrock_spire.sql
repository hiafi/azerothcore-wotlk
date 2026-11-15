-- Blackrock Spire build WP-B7: Halycon (10220) and Gizrul the Slavener (10268), the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.5 row B7; build spec
-- docs/dungeons/blackrock-spire-rework.md SP "Halycon and Gizrul"). Their templates (boss_halycon_gizrul_rework,
-- AIName '', health, immunity 1972, INSTANCE_BIND) and spells 210210-210230 are apps/dbc-tools
-- source/npcs/blackrock_spire/halycon_gizrul.py; Gizrul's three stock smart_scripts rows are dropped by WP-S0's
-- rev_blackrock_spire_skeleton.sql.

-- Their texts (SP "Text"): every line a boss emote (41) so it names the mechanic on screen. Halycon's stock line 0 (her
-- death emote, broadcast text 5548) becomes the Grief line: it plays only when she falls while Gizrul lives.
DELETE FROM `creature_text` WHERE `CreatureID` = 10220 AND `GroupID` BETWEEN 0 AND 4;
DELETE FROM `creature_text` WHERE `CreatureID` = 10268 AND `GroupID` BETWEEN 0 AND 3;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10220, 0, 0, '%s collapses. Gizrul howls in grief!', 41, 0, 100, 0, 0, 0, 0, 0, 'Halycon - Grief (HG8)'),
(10220, 1, 0, '%s throws back her head and howls. Something answers from the halls above!', 41, 0, 100, 0, 0, 0, 0,
    0, 'Halycon - The pull (HG1)'),
(10220, 2, 0, '%s crouches low!', 41, 0, 100, 0, 0, 0, 0, 0, 'Halycon - Thrash (HG4)'),
(10220, 3, 0, '%s howls for the pack!', 41, 0, 100, 0, 0, 0, 0, 0, 'Halycon - Call of the Pack (HG7)'),
(10220, 4, 0, '%s screams and fixes her eyes on $n!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Halycon - Savage Charge under Grief (HG8)'),
(10268, 0, 0, '%s fixes his eyes on $n!', 41, 0, 100, 0, 0, 0, 0, 0, 'Gizrul the Slavener - Savage Charge (HG2)'),
(10268, 1, 0, '%s froths at the mouth!', 41, 0, 100, 0, 0, 0, 0, 0, 'Gizrul the Slavener - Rabid Froth (HG5)'),
(10268, 2, 0, '%s falls. Halycon''s howl turns to a scream!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Gizrul the Slavener - Grief (HG8)'),
(10268, 3, 0, '%s howls for his mate!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Gizrul the Slavener - Call of the Pack under Grief (HG7)');
