-- Blackrock Depths build WP-D8: Warder Stilgiss (9041) and Verek (9042), the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D8; build spec
-- docs/dungeons/blackrock-depths-2-shadowforge-city.md "Warder Stilgiss and Verek", Build spec). Their templates
-- (boss_warder_stilgiss_rework / npc_verek_rework, AIName '', health, DamageModifier 3.5, immunity 1972,
-- INSTANCE_BIND) and the spells 211050-211065 are apps/dbc-tools source/npcs/blackrock_depths/stilgiss_verek.py. Their
-- SmartAI rows (Frost Armor, Frostbolt, Frost Nova, Frost Ward and the flee for Stilgiss; Curse of Blood and Enrage for
-- Verek) are removed by rev_blackrock_depths_skeleton.sql (WP-S0), not here; the script casts Frost Armor out of combat
-- and Verek's two beats itself.

-- Texts (SP "Text"; Stilgiss had none): the pull and the death lines are yells (14); each artifact's draw is a boss
-- emote (41), so it names the moment on screen ("%s" is Stilgiss).
DELETE FROM `creature_text` WHERE `CreatureID` = 9041;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(9041, 0, 0, 'Thieves, in my Vault? Then let me show you what you came for.', 14, 0, 100, 0, 0, 0, 0, 0,
    'Warder Stilgiss - Aggro'),
(9041, 1, 0, '%s draws the Eye of Kajal from a coffer!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Warder Stilgiss - Draw the Eye of Kajal (SV1)'),
(9041, 2, 0, '%s draws the Black Steel Bindings from a coffer!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Warder Stilgiss - Draw the Black Steel Bindings (SV1)'),
(9041, 3, 0, '%s draws the Magma Forged Band from a coffer!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Warder Stilgiss - Draw the Magma Forged Band (SV1)'),
(9041, 4, 0, '%s draws the Wand of Eternal Light from a coffer!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Warder Stilgiss - Draw the Wand of Eternal Light (SV1)'),
(9041, 5, 0, '%s draws the Black Blood of the Tormented from a coffer!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Warder Stilgiss - Draw the Black Blood of the Tormented (SV1)'),
(9041, 6, 0, 'My... collection...', 14, 0, 100, 0, 0, 0, 0, 0, 'Warder Stilgiss - Death');

-- Verek's stock group 0 ("%s becomes enraged!", broadcast text 10677) was an emote (16) no script ever said; the
-- Enrage at 30% says it now, as a boss emote (41) like every other boss emote of the dungeon.
UPDATE `creature_text` SET `Type` = 41 WHERE `CreatureID` = 9042 AND `GroupID` = 0 AND `ID` = 0;
