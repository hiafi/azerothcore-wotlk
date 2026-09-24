-- Custom: the Bear Form appearance NPC (900012) now also offers Cat Form, under a generic script
-- (npc_shapeshift_appearance, src/server/scripts/Custom/custom_shapeshift_appearance.cpp).
UPDATE `creature_template` SET `subname` = 'Shapeshift Appearances', `ScriptName` = 'npc_shapeshift_appearance'
WHERE `entry` = 900012;

DELETE FROM `npc_text` WHERE `ID` = 900012;
INSERT INTO `npc_text` (`ID`, `text0_0`, `text0_1`, `Probability0`)
VALUES (900012, 'The wild wears many coats, and so may you. Choose the shape your bear or cat form will take.$B$BIf you speak to me while already shifted, you will see each choice as you make it.',
    'The wild wears many coats, and so may you. Choose the shape your bear or cat form will take.$B$BIf you speak to me while already shifted, you will see each choice as you make it.', 1);
