-- Scholomance build WP-S7: Lorekeeper Polkelt (10901), the rows dbc-tools cannot declare
-- (.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row S7; build spec
-- docs/dungeons/scholomance-rework.md SC 1979-2036). His template (boss_lorekeeper_polkelt_rework, AIName '', health,
-- DamageModifier, immunities), the Unstable Specimen 300540, the Rooted Specimen 300541 and the spells 206250-206264
-- are apps/dbc-tools source/npcs/scholomance/lorekeeper_polkelt.py.

-- Lorekeeper Polkelt: SmartAI 10901 is removed (SC "Stock kit"): Volatile Infection 18149 is cast by the script (the
-- stock timers), Corrosive Acid 8245 becomes Corroded (206260) and Noxious Catalyst 18151 leaves his kit (the heroic
-- 206263 reuses the name). The death row's SetData(1, 1) is the retired mini-boss counter: the instance follows his
-- boss state instead.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 10901 AND `source_type` = 0;

-- His lines (SC "Text"; he has none stock): the raise is a boss emote (41), so it names the mechanic on screen; the
-- aggro and death lines are yells.
DELETE FROM `creature_text` WHERE `CreatureID` = 10901;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10901, 0, 0, '%s raises fresh specimens!', 41, 0, 100, 0, 0, 0, 0, 0, 'Lorekeeper Polkelt - Raise Specimens (PK1)'),
(10901, 1, 0, 'The formulae demand fresh samples.', 14, 0, 100, 0, 0, 0, 0, 0, 'Lorekeeper Polkelt - aggro'),
(10901, 2, 0, 'The reaction... was... unstable...', 14, 0, 100, 0, 0, 0, 0, 0, 'Lorekeeper Polkelt - death');
