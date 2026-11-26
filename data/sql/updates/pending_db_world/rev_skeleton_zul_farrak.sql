-- Zul'Farrak build WP-S0, the skeleton (.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.2 items 5, 6
-- and 8, s7 #2 A, #13 A, #15 A). The stock event is re-implemented in modules/mod-dungeon-bosses src/ZulFarrak/
-- (instance_zulfarrak_rework.cpp and the WPs' files); the stock scripts in src/server/scripts/Kalimdor/ZulFarrak/ stay
-- registered and unbound.

-- The stock SmartAI of every unit the rework scripts, so no boss WP deletes them again: the Executioner 7274, Nekrum
-- 7796, Raven 7605, Oro 7606, Murta 7608, Theka 7272, Antu'sul 8127, his Servant 8156, Zum'rah 7271, Ukorz 7267,
-- Ruuzlu 7797, Velratha 7795, Gahz'rilla 7273 (s3.2 item 6). AIName '' of the bosses comes with the dbc-tools rows
-- (boss_columns, next to the ScriptName: one owner per column); the crew's is below. None of them has an action list
-- (source type 9); the only SmartAI condition on these sources is the gong's (SELECT 2026-11-25). The trash, the
-- graves, the Earthgrab totem 6066 (D2's) and the two area triggers (962: Zum'rah's faction 37, DC hook 5 reads it;
-- 1447: Antu'sul's wake, s7 #25 A) keep theirs.
DELETE FROM `smart_scripts` WHERE `source_type` = 0
    AND `entryorguid` IN (7274, 7796, 7605, 7606, 7608, 7272, 8127, 8156, 7271, 7267, 7797, 7795, 7273);

-- Weegli's Armed Barrel 141612 (the End Door's stock opener: the instance opens the door now, s7 #13 A) and the Gong of
-- Zul'Farrak 141832 (Gahz'rilla's stock summon: the instance summons him at Velratha's strike, s3.2 item 6). The
-- gong's condition (source type 22, group 1, "Run event if GetData(1) == 0") goes with its row.
DELETE FROM `smart_scripts` WHERE `source_type` = 1 AND `entryorguid` IN (141612, 141832);
DELETE FROM `conditions` WHERE `SourceTypeOrReferenceId` = 22 AND `SourceId` = 1 AND `SourceEntry` IN (141612, 141832);
UPDATE `gameobject_template` SET `AIName` = '' WHERE `entry` IN (141612, 141832);
-- The gong is inert to players (GO_FLAG_NOT_SELECTABLE 0x10; its addon row exists with flags 0): Velratha strikes it.
UPDATE `gameobject_template_addon` SET `flags` = `flags` | 16 WHERE `entry` = 141832;

-- The five Troll Cages: go_zf_troll_cage (instance_zulfarrak_rework.cpp) in place of go_troll_cage; the key's lock and
-- spell_zulfarrak_unlocking 10738 are untouched (the stage 2 gate opens on the first cage).
UPDATE `gameobject_template` SET `ScriptName` = 'go_zf_troll_cage'
    WHERE `entry` IN (141070, 141071, 141072, 141073, 141074);

-- Sergeant Bly's crew: CR's AI (BlyCrew.cpp) in place of npc_sergeant_bly, npc_weegli_blastfuse and the SmartAI of
-- Raven, Oro and Murta (whose rows went above). Band's Escape (11365) goes with npc_sergeant_bly (s7 #15 A). The
-- crew's other columns (type_flags, texts, flags_extra) are CR's and D5's revs; their health D5's.
UPDATE `creature_template` SET `AIName` = '', `ScriptName` = 'npc_bly_crew_bly' WHERE `entry` = 7604;
UPDATE `creature_template` SET `AIName` = '', `ScriptName` = 'npc_bly_crew_raven' WHERE `entry` = 7605;
UPDATE `creature_template` SET `AIName` = '', `ScriptName` = 'npc_bly_crew_oro' WHERE `entry` = 7606;
UPDATE `creature_template` SET `AIName` = '', `ScriptName` = 'npc_bly_crew_weegli' WHERE `entry` = 7607;
UPDATE `creature_template` SET `AIName` = '', `ScriptName` = 'npc_bly_crew_murta' WHERE `entry` = 7608;
