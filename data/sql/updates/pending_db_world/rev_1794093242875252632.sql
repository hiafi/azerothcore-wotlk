-- Shadowfang Keep build WP-S8: Wolf Master Nandos (3927) and his pack, the rows dbc-tools cannot declare
-- (.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md s3.6 row S8). His template
-- (boss_wolf_master_nandos_rework, AIName '', health, immunities), the pack copies 300509-300512 (npc_sfk_pack_wolf)
-- and the spells are apps/dbc-tools source/npcs/shadowfang_keep/wolf_master_nandos.py.

-- SmartAI 3927 is removed (SK "Stock kit", approved): Call Lupine Horror 7489 and Call Bleak Worg 7487 are dropped;
-- the instance data, the Arugal's Lair door, the pack counter, the yell and the late attack are the script's and the
-- instance's now (he fights from the pull; door data opens the lair on his death).
DELETE FROM `smart_scripts` WHERE `entryorguid` = 3927 AND `source_type` = 0;

-- The four wolves' guid SmartAI (Wavering Will 7127, Summon Lupine Delusions 7132, the death counter on Nandos): the
-- pack copies' script does it now.
DELETE FROM `smart_scripts` WHERE `entryorguid` IN (-16238, -16239, -16240, -16241) AND `source_type` = 0;

-- The four spawns on Nandos's platform become the boss-kit copies (the stock entries stay stock: they are trash
-- elsewhere in the keep). spawnMask 3: normal and heroic (STAGE-H report s6 #4).
-- 16238 Lupine Horror 3863 -> 300510, 16239 Bleak Worg 3861 -> 300509, 16240 Slavering Worg 3862 -> 300511,
-- 16241 Wolfguard Worg 5058 -> 300512.
UPDATE `creature` SET `id` = 300510, `spawnMask` = 3, `Comment` = NULL WHERE `guid` = 16238 AND `id` IN (3863, 300510);
UPDATE `creature` SET `id` = 300509, `spawnMask` = 3, `Comment` = NULL WHERE `guid` = 16239 AND `id` IN (3861, 300509);
UPDATE `creature` SET `id` = 300511, `spawnMask` = 3, `Comment` = NULL WHERE `guid` = 16240 AND `id` IN (3862, 300511);
UPDATE `creature` SET `id` = 300512, `spawnMask` = 3, `Comment` = NULL WHERE `guid` = 16241 AND `id` IN (5058, 300512);

-- Mark the Prey (NA6; SK "Text", approved): a boss emote (41), so it names the mechanic on screen; $n is the prey.
-- Line 0 (the stock yell, now on the last wolf's death) stays.
DELETE FROM `creature_text` WHERE `CreatureID` = 3927 AND `GroupID` = 1;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(3927, 1, 0, '%s whistles, and the pack turns on $n!', 41, 0, 100, 0, 0, 0, 0, 0, 'Wolf Master Nandos - Mark the Prey (NA6)');
