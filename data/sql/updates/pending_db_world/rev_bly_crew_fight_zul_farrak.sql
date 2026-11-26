-- Zul'Farrak build WP-D5: Sergeant Bly's crew as a boss, the rows dbc-tools cannot declare
-- (.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.5 row D5, s7 #19 A, #49 A; build spec
-- docs/dungeons/zul-farrak-rework.md "Sergeant Bly's crew"). The crew's template columns and spells 214030-214049 are
-- apps/dbc-tools source/npcs/zul_farrak/bly_crew_fight.py; their scripts are bound by rev_skeleton_zul_farrak.sql and
-- their texts inserted by rev_crew_zul_farrak.sql (CR). This rev inserts no spawn: the script summons the chest.

-- Section 7 #19 A: the crew's stash, normal 301360 and heroic 301361 (CHEST, lock 57 = no key, consumable, the loot
-- window keeps it closed, group loot: the Scarlet Monastery Last Stand chest's values). Data1 is the loot entry, the
-- GO's own id: rev_loot_zul_farrak.sql (L-1) fills gameobject_loot_template 301360 / 301361 with the crew's list, the
-- Divino-matic Rod 8548 (quest 2768) and the members' own tables. The display is a stock lootable sack (TaurenSack02,
-- display 323: Stolen Supply Sack 3290's). bly_crew_fight_rework.cpp summons the entry of the map's difficulty on the
-- plaza when the fight ends, on both paths, for a day or until looted.
-- Upserts: gameobject_template rows are never deleted (codestyle-sql not_delete).
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`,
    `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`,
    `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`,
    `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301360, 3, 323, 'Treasure Sack', '', '', '', 1, 57, 301360, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0,
    0, 0, 0, '', '', 0),
(301361, 3, 323, 'Treasure Sack', '', '', '', 1, 57, 301361, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0,
    0, 0, 0, '', '', 0) ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`),
    `name` = VALUES(`name`), `size` = VALUES(`size`), `Data0` = VALUES(`Data0`), `Data1` = VALUES(`Data1`),
    `Data3` = VALUES(`Data3`), `Data11` = VALUES(`Data11`), `Data15` = VALUES(`Data15`), `AIName` = VALUES(`AIName`),
    `ScriptName` = VALUES(`ScriptName`);
DELETE FROM `gameobject_template_addon` WHERE `entry` IN (301360, 301361);
INSERT INTO `gameobject_template_addon` (`entry`, `faction`, `flags`, `mingold`, `maxgold`, `artkit0`, `artkit1`,
    `artkit2`, `artkit3`) VALUES
(301360, 0, 0, 0, 0, 0, 0, 0, 0),
(301361, 0, 0, 0, 0, 0, 0, 0, 0);
