-- Blackrock Spire build WP-B13: The Beast (10430), the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.5 row B13; build spec
-- docs/dungeons/blackrock-spire-rework.md SP 3465-3698). His template (boss_the_beast_rework, AIName '', health,
-- DamageModifier 3.5 (stock), immunity 1972), the Molten Blood pool stalker 300735 and the spells 210490-210508 are
-- apps/dbc-tools source/npcs/blackrock_spire/the_beast.py. He has no SmartAI (the stock boss is C++ only), so no row to
-- drop; the Elites' text (10317 group 0, "We're doomed!") and Finkle's (10776 group 0) are stock and untouched.

-- His texts (SP "Text"; he had none): three boss emotes (type 41: center-screen and in the raid warning area), for the
-- roar, each Heat stack and the Eruption.
DELETE FROM `creature_text` WHERE `CreatureID` = 10430 AND `GroupID` BETWEEN 0 AND 2;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10430, 0, 0, '%s rears back to roar!', 41, 0, 100, 0, 0, 0, 0, 0, 'The Beast - Roar (BE5)'),
(10430, 1, 0, '%s''s blood boils!', 41, 0, 100, 0, 0, 0, 0, 0, 'The Beast - Heat (BE2)'),
(10430, 2, 0, 'The lair floor erupts in magma!', 41, 0, 100, 0, 0, 0, 0, 0, 'The Beast - Eruption (BE7)');
