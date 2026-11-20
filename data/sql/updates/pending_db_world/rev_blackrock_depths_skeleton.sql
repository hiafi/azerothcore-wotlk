-- Blackrock Depths build, WP-S0 (the skeleton; .agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md
-- s3.2 item 4).
--
-- 1. The wave 1 bosses S0 binds to their C++ scripts with AIName '' (apps/dbc-tools source/npcs/blackrock_depths/):
--    their stock SmartAI rows go, or SmartAIMgr logs an error at boot for a creature not using SmartAI. The boss WPs
--    re-create what they keep in C++ (no actionlists and no guid rows exist for them, checked 2026-11-17).
--    Roccor 9025 (3), Grebmar 9319 (3), Loregrain 9024 (4), Stilgiss 9041 (5), Verek 9042 (2), Doomgrip 9476 (3),
--    Fineous 9056 (6), Incendius 9017 (5), Bael'Gar 9016 (5). Gerstahn 9018 had none (C++ already). The Ring's
--    units (Grimstone, the wave mobs, the champions, Theldren's team) stay until D4 / D5 / D6 bind them; the wave 2
--    bosses' rows go with WP 0-2's rev.
DELETE FROM `smart_scripts` WHERE `source_type` = 0
    AND `entryorguid` IN (9016, 9017, 9024, 9025, 9041, 9042, 9056, 9319, 9476);

-- 2. The Vault's trigger moves to the Dark Coffer (section 7 #17): its gossip also tells the instance (SetData(57, 1),
--    DATA_VAULT_TRIGGER in BlackrockDepthsRework.h), which starts the Vault only once Warder Stilgiss and Verek are
--    DONE and the Vault is NOT_STARTED (a wipe makes it NOT_STARTED again: the opened coffer's gossip restarts it).
--    The stock row 0 (unlock the Dark Coffer chest 160845) is kept as it was. The twelve Relic Coffer Doors keep their
--    "set data 30" rows: the instance only counts them now (inert).
DELETE FROM `smart_scripts` WHERE `entryorguid` = 174565 AND `source_type` = 1;
INSERT INTO `smart_scripts` (`entryorguid`, `source_type`, `id`, `link`, `event_type`, `event_phase_mask`,
    `event_chance`, `event_flags`, `event_param1`, `event_param2`, `event_param3`, `event_param4`, `event_param5`,
    `event_param6`, `action_type`, `action_param1`, `action_param2`, `action_param3`, `action_param4`, `action_param5`,
    `action_param6`, `target_type`, `target_param1`, `target_param2`, `target_param3`, `target_param4`, `target_x`,
    `target_y`, `target_z`, `target_o`, `comment`) VALUES
(174565, 1, 0, 0, 64, 0, 100, 0, 0, 0, 0, 0, 0, 0, 106, 16, 0, 0, 0, 0, 0, 20, 160845, 10, 0, 0, 0, 0, 0, 0,
    'On Gossip Hello - Remove GO Flag'),
(174565, 1, 1, 0, 64, 0, 100, 0, 0, 0, 0, 0, 0, 0, 34, 57, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0,
    'On Gossip Hello - Set Instance Data 57 to 1 (the Vault trigger, BRD build S0)'),
(174565, 1, 2, 0, 64, 0, 100, 0, 0, 0, 0, 0, 0, 0, 35, 72, 0, 0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0,
    'On Gossip Hello - Set Instance Data64 72 to the invoker (the Vault opener, BRD build F-1a)');
