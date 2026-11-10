-- Stratholme build WP-S1: The Unforgiven (10516), the rows dbc-tools cannot declare
-- (.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.5 row S1; build spec
-- docs/dungeons/stratholme-rework.md ST 616-676). His template (boss_the_unforgiven_rework, AIName '', health,
-- DamageModifier 3.7, immunities, INSTANCE_BIND), the phantom 10387's columns and models, the Spectral Footman
-- 300600, the house fire stalker 300601 and his spells 206420-206433 are apps/dbc-tools
-- source/npcs/stratholme/the_unforgiven.py.

-- SmartAI 10516 x8 (the invisibility roll on AI init and the visible switch on aggro, four Vengeful Phantoms summoned
-- on aggro, the 8 s Frost Nova 14907, Incorporeal Defense 16331 on reset) is removed (ST "Stock kit", approved
-- 2026-11-02): boss_the_unforgiven_rework raises the phantoms with the Accusation and casts its own 1.5 s Frost Nova
-- copy. SmartAI 10387 x1 (Frost Shock 15089 in combat) is removed: the phantoms do not fight (npc_st_vengeful_phantom).
DELETE FROM `smart_scripts` WHERE `entryorguid` IN (10516, 10387) AND `source_type` = 0;

-- Texts (ST "Text"; none stock): the yells are type 14; the house fire is a boss emote (41), so it names the moment on
-- screen.
DELETE FROM `creature_text` WHERE `CreatureID` = 10516;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10516, 0, 0, 'You came back. They always come back.', 14, 0, 100, 0, 0, 0, 0, 0, 'The Unforgiven - Aggro'),
(10516, 1, 0, 'They came down this street at dawn, in ranks!', 14, 0, 100, 0, 0, 0, 0, 0,
    'The Unforgiven - The March (UF1)'),
(10516, 2, 0, 'You! I saw you there that night!', 14, 0, 100, 0, 0, 0, 0, 0, 'The Unforgiven - The Accusation (UF5)'),
(10516, 3, 0, 'A house on the square bursts into flames!', 41, 0, 100, 0, 0, 0, 0, 0,
    'The Unforgiven - House fire (UF2)'),
(10516, 4, 0, 'Every soul you left me... come back to me now!', 14, 0, 100, 0, 0, 0, 0, 0,
    'The Unforgiven - The Last Soul (UF9)'),
(10516, 5, 0, 'Forgive you? Never...', 14, 0, 100, 0, 0, 0, 0, 0, 'The Unforgiven - Death');

-- The Spectral Footman's sword and shield: the Halls of Reflection Spectral Footman 38173's (items 1899 and 1984).
DELETE FROM `creature_equip_template` WHERE `CreatureID` = 300600;
INSERT INTO `creature_equip_template` (`CreatureID`, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, `VerifiedBuild`) VALUES
(300600, 1, 1899, 1984, 0, 0);
