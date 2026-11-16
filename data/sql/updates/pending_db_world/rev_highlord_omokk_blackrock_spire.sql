-- Blackrock Spire build WP-B1: Highlord Omokk (9196), the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.5 row B1; build spec
-- docs/dungeons/blackrock-spire-rework.md "Highlord Omokk"). His template (boss_highlord_omokk_rework, AIName '',
-- health, DamageModifier 3.5, immunities, INSTANCE_BIND), the crowd 300700-300702 and his spells 210020-210044 are
-- apps/dbc-tools source/npcs/blackrock_spire/omokk.py. He has no SmartAI rows (the stock script was C++).

-- The Spirestone Mystic 43514 and the Spirestone Ogre Magus 43515 beside him are removed (SP "Stock kit", ruling 16):
-- they would heal and buff him; the crowd replaces them. No addon, formation, pool, linked respawn or event row names
-- either spawn (checked 2026-11-15).
DELETE FROM `creature` WHERE `id` = 9198 AND `guid` = 43514;
DELETE FROM `creature` WHERE `id` = 9201 AND `guid` = 43515;

-- Texts (SP "Text"; none stock): yells are type 14, the crowd's moments and the Haymaker call are boss emotes (41).
DELETE FROM `creature_text` WHERE `CreatureID` = 9196;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(9196, 0, 0, 'Ogres! Make ring! Omokk show who strongest!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Highlord Omokk - Aggro, the crowd runs in (OM1)'),
(9196, 1, 0, '%s winds up a haymaker at $n!', 41, 0, 100, 0, 0, 0, 0, 0, 'Highlord Omokk - Haymaker (OM2)'),
(9196, 2, 0, 'The crowd roars for Omokk!', 41, 0, 100, 0, 0, 0, 0, 0, 'Highlord Omokk - The judge, fed (OM5)'),
(9196, 3, 0, 'The crowd jeers at Omokk!', 41, 0, 100, 0, 0, 0, 0, 0, 'Highlord Omokk - The judge, booed (OM5)'),
(9196, 4, 0, 'Omokk still strongest! No ogre take Omokk''s place!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Highlord Omokk - Third Booed stack (OM5)'),
(9196, 5, 0, 'Enough! To the bridge! Loser go in the pit!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Highlord Omokk - To the bridge at 25% (OM7, heroic)'),
(9196, 6, 0, 'A Spirestone Mojo Mystic starts chanting mojo into %s!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Highlord Omokk - Ogre Mojo chant (OM6, heroic)'),
(9196, 7, 0, 'Omokk... not... weak...', 14, 0, 100, 0, 0, 0, 0, 0, 'Highlord Omokk - Death');
