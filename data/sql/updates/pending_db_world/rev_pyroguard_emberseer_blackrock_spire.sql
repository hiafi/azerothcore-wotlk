-- Blackrock Spire build WP-B10: Pyroguard Emberseer (9816), the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.5 row B10; build spec
-- docs/dungeons/blackrock-spire-rework.md SP 2523-2790). His template (boss_pyroguard_emberseer_rework, AIName '',
-- health, DamageModifier 3.5 (stock), immunity 1973), the Incarcerators' rebinding (10316), the Binding Post 300730 and
-- the spells 210350-210367 are apps/dbc-tools source/npcs/blackrock_spire/emberseer.py. Neither he nor the
-- Incarcerators have SmartAI rows, so none to drop. His stock lines 0-3 stay as they are (the script says 0 and 1 at 7
-- and 14 stacks now); the Incarcerators' flee line (10316 group 0) is retired with the flee and left in place.

-- His immunity set 1973 (handoff s7 #16 A; review R-2-A M-1: declared nowhere, so he had none): the Deadmines set 1972
-- ("-229 + STUN", MechanicsMask 1217821862, rev_1793964948691162910.sql) plus the Fire school (SchoolMask 4, the stock
-- -252's). Interrupts and silences stay possible (no INTERRUPT / SILENCE bit: Pyroblast is kickable). Live max is 1972
-- (checked 2026-11-15); nothing else uses 1973.
DELETE FROM `creature_immunities` WHERE `ID` = 1973;
INSERT INTO `creature_immunities` (`ID`, `SchoolMask`, `DispelTypeMask`, `MechanicsMask`, `Effects`, `Auras`,
    `ImmuneAoE`, `ImmuneChain`, `Comment`) VALUES
(1973, 4, 0, 1217821862, '', '', 0, 0, 'Blackrock Spire Emberseer: 1972 (-229 + STUN) + Fire school');

-- His new lines (SP "Text"): the posts smolder, Pyroblast feeds him, Full Strength, the unstable posts (heroic). Boss
-- emotes are type 41 (center-screen and in the raid warning area); line 5 is a plain emote (type 16, as his stock 0-2).
DELETE FROM `creature_text` WHERE `CreatureID` = 9816 AND `GroupID` BETWEEN 4 AND 7;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(9816, 4, 0, 'The binding posts begin to smolder!', 41, 0, 100, 0, 0, 0, 0, 0, 'Emberseer - posts smolder (EM6)'),
(9816, 5, 0, '%s draws the flames into itself!', 16, 0, 100, 0, 0, 0, 0, 0, 'Emberseer - Pyroblast landed (EM9)'),
(9816, 6, 0, '%s burns at full strength!', 41, 0, 100, 0, 0, 0, 0, 0, 'Emberseer - Full Strength (EM5)'),
(9816, 7, 0, 'Unstable posts crackle with fire!', 41, 0, 100, 0, 0, 0, 0, 0, 'Emberseer - Unstable Posts (EM8)');
