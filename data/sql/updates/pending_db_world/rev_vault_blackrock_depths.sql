-- Blackrock Depths build WP-D9: the Vault (Watchman Doomgrip 9476, the Vault Sentinels 300793, the Secret Safe
-- 161495), the rows dbc-tools cannot declare (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md
-- s3.5 row D9; build spec docs/dungeons/blackrock-depths-2-shadowforge-city.md "The Vault", Build spec). The templates
-- (Doomgrip bound to boss_watchman_doomgrip_rework, the Vault Sentinel 300793 with npc_brd_vault_sentinel) and the
-- spells 211090-211102 are apps/dbc-tools source/npcs/blackrock_depths/vault.py. Doomgrip's SmartAI rows are removed
-- by rev_blackrock_depths_skeleton.sql (WP-S0), not here; the Dark Coffer's trigger row is S0's too.

-- 1. Texts (SP "Text"): group 0 is the stock yell (the lockdown, said at his pull) and stays. A sentinel waking and the
--    loot clock's three seals are boss emotes (41); the death line is a yell (14).
DELETE FROM `creature_text` WHERE `CreatureID` = 9476 AND `GroupID` BETWEEN 1 AND 5;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(9476, 1, 0, 'A Vault Sentinel grinds to life!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Watchman Doomgrip - A Vault Sentinel wakes (VA2)'),
(9476, 2, 0, 'The vault seals away a treasure bag!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Watchman Doomgrip - The loot clock, 75 s (VA8)'),
(9476, 3, 0, 'The vault seals away a treasure!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Watchman Doomgrip - The loot clock, 90 s (VA8)'),
(9476, 4, 0, 'The vault seals away the last treasure bag!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Watchman Doomgrip - The loot clock, 110 s (VA8)'),
(9476, 5, 0, 'The vault... is breached...', 14, 0, 100, 0, 0, 0, 0, 0, 'Watchman Doomgrip - Death');

-- 2. The four event constructs become Vault Sentinels (SP "Implementation": the Warbringer Construct 8905 is trash
--    elsewhere in the Black Vault). Same spots, same addon rows; the instance freezes them on create (both entries)
--    and the sentinel's script keeps them stone until their turn. A spawn whose entry a hand rev changes carries the
--    heroic bit itself (handoff s3.5 rule 14: the generated heroic rev sorts before this one); the heroic map runs
--    the heroic template 310404 (WP-H).
UPDATE `creature` SET `id` = 300793, `spawnMask` = 3 WHERE `id` = 8905 AND `guid` IN (46608, 46610, 46611, 46612);

-- 3. The Secret Safe runs the event's clock and fills itself when opened (go_brd_vault_secret_safe, the loot hook
--    brd_vault_safe_loot): the lockdown, the wakes, the seals, the Cinder, the gear and the bags. Its loot table
--    (gameobject_loot_template 161495, WP-L-1) must keep at least one row, or the engine never fills the chest and the
--    hook never runs. It respawns after a week instead of 10 minutes, so a looted Safe cannot be filled a second time
--    in one instance (the clock is saved; a respawned Safe would read it again).
UPDATE `gameobject_template` SET `ScriptName` = 'go_brd_vault_secret_safe' WHERE `entry` = 161495;
UPDATE `gameobject` SET `spawntimesecs` = 604800 WHERE `id` = 161495 AND `guid` = 43137;
