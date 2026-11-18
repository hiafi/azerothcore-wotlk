-- Blackrock Depths build WP-D23: Emperor Dagran Thaurissan (9019), Princess Moira Bronzebeard (8929) and the High
-- Priestess of Thaurissan (10076), the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D23; build spec
-- docs/dungeons/blackrock-depths-4-imperial-seat.md "Emperor Dagran Thaurissan"). Their templates (the reworked
-- scripts, AIName '', health, 1972, INSTANCE_BIND), the Imperial Guard 300843, the Twilight's Hammer Ambassador 300844
-- and spells 211610-211631 are apps/dbc-tools source/npcs/blackrock_depths/emperor.py. None of the three has a
-- smart_scripts row (live SELECT 2026-11-17: none for 9019, 8929 or 10076), so there is nothing to drop; Dagran keeps
-- guid 47613 and Moira her spawn (the High Priestess has none: the instance summons her). The adds are summoned by his
-- script: this rev inserts no creature spawn and no SmartAI row (rule 14: nothing for the heroic spawn mask to miss).
-- Moira's lootid 8929 (shared with the Priestess) is L-2's to empty into his list.

-- Dagran's texts (S4 "Text"; handoff gap 38): groups 0-7 are the stock rows (aggro with the council alive / dead, the
-- kill line, the five senator lines) and stay untouched. 8-10 are the spec's new yells (the guard wave, the enrage,
-- Ragnaros Awakens); 11-13 the boss emotes gap 38 asks for (type 41, rule 2): 11 Magma Clap and 12 Volcanic Blast are
-- said by D24's Avatar (EM12, EM13; 12 names the marked player), 13 Hammer Slam (EM10). All map-wide (TextRange 3): the
-- throne room is 130 yd long, a boss emote's own range is 25.
DELETE FROM `creature_text` WHERE `CreatureID` = 9019 AND `GroupID` BETWEEN 8 AND 13;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(9019, 8, 0, 'Guards! Defend your Emperor!', 14, 0, 100, 0, 0, 0, 0, 3,
    'Emperor Dagran Thaurissan - Imperial Guard wave (EM3)'),
(9019, 9, 0, 'You will pay for her with fire!', 14, 0, 100, 0, 0, 0, 0, 3,
    'Emperor Dagran Thaurissan - Avatar of Flame, the enrage (EM8)'),
(9019, 10, 0, 'Ragnaros! Your servant calls! Lend me your fury!', 14, 0, 100, 0, 0, 0, 0, 3,
    'Emperor Dagran Thaurissan - Ragnaros Awakens (EM11, the hard mode)'),
(9019, 11, 0, '%s brings his hands together, and magma surges around him! Get away from him!', 41, 0, 100, 0, 0, 0,
    0, 3, 'Emperor Dagran Thaurissan - Magma Clap (EM12, the hard mode; gap 38)'),
(9019, 12, 0, '%s marks $n for a Volcanic Blast! Stand with $g him:her; to share the blast!', 41, 0, 100, 0, 0, 0,
    0, 3, 'Emperor Dagran Thaurissan - Volcanic Blast (EM13, the hard mode; gap 38)'),
(9019, 13, 0, '%s raises his hammer!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Emperor Dagran Thaurissan - Hammer Slam (EM10; gap 38)');

-- Moira and the High Priestess run one kit (S4: the swap keeps Moira's new kit). Group 0 of each is stock (Moira's
-- stand-down emote, the Priestess's aggro yell) and stays; group 1 is the Nemesis emote (EM2), a boss emote (type 41)
-- on both, map-wide.
DELETE FROM `creature_text` WHERE `CreatureID` IN (8929, 10076) AND `GroupID` = 1;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(8929, 1, 0, '%s channels a beam of holy fire into the Emperor!', 41, 0, 100, 0, 0, 0, 0, 3,
    'Princess Moira Bronzebeard - Shadow Word: Nemesis (EM2)'),
(10076, 1, 0, '%s channels a beam of holy fire into the Emperor!', 41, 0, 100, 0, 0, 0, 0, 3,
    'High Priestess of Thaurissan - Shadow Word: Nemesis (EM2)');
