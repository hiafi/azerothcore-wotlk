-- Stratholme build WP-S14: Baron Rivendare (10440), the rows dbc-tools cannot declare
-- (.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.5 row S14; build spec
-- docs/dungeons/stratholme-rework.md ST 3842-3906). His template (boss_baron_rivendare_rework, AIName '', health,
-- DamageModifier 8, immunity -419), the Mindless Skeleton's (npc_st_mindless_skeleton, AIName '', 6,000 health), the
-- rot stalker 300588 and the spells 206705-206711 are apps/dbc-tools source/npcs/stratholme/baron_rivendare.py.

-- SmartAI 10440 (twenty rows: Cleave, Shadow Bolt, Mortal Strike, Unholy Aura 17467, Raise Dead 17473 and
-- 17475-17480 with emote line 7, the Death Pact emote line 8, Ysida's release, the door rows on spawn guid 35848, the
-- leash and the summon cleanup) is removed: boss_baron_rivendare_rework replaces every row (the instance shuts and
-- opens his door by BOSS_BARON; the script keeps the leash and frees Ysida on his death).
DELETE FROM `smart_scripts` WHERE `entryorguid` = 10440 AND `source_type` = 0;
-- The leash rows' conditions (SourceGroup 18 = row 17 + 1): 21 yd from Ramstein's door 175405, or 4 yd from his own
-- door 175796 while more than 13 yd from Menethil's Gift 176631. The script keeps the same rule (BaronLogic.h
-- StockLeashBreached).
DELETE FROM `conditions`
    WHERE `SourceTypeOrReferenceId` = 22 AND `SourceGroup` = 18 AND `SourceEntry` = 10440 AND `SourceId` = 0;

-- SmartAI 11197 (three rows: attack the closest player out of combat, despawn after 10 s out of combat, die on Death
-- Pact's hit) is removed: npc_st_mindless_skeleton strikes the Baron's victim, and he despawns his skeletons.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 11197 AND `source_type` = 0;

-- Texts (ST "Text"). Groups 0-8 are stock; group 7 (BR1, "raises an undead servant") becomes a boss emote (41), so it
-- names the mechanic on screen; group 8 (Death Pact) stays, unused. Groups 9, 10 and 15 are new; 11-14 are S15's (the
-- Ultimatum) and are not touched here. $n is the marked player.
UPDATE `creature_text` SET `Type` = 41 WHERE `CreatureID` = 10440 AND `GroupID` = 7 AND `ID` = 0;
DELETE FROM `creature_text` WHERE `CreatureID` = 10440 AND `GroupID` IN (9, 10, 15);
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10440, 9, 0, 'Your bones will serve me before the hour is out.', 14, 0, 100, 0, 0, 0, 0, 0, 'Baron Rivendare - Aggro'),
(10440, 10, 0, '%s rots the ground beneath $n!', 41, 0, 100, 0, 0, 0, 0, 0, 'Baron Rivendare - Death and Decay (BR3)'),
(10440, 15, 0, 'The Lich King... will raise me... again...', 14, 0, 100, 0, 0, 0, 0, 0, 'Baron Rivendare - Death');

-- 301207 Bone Pile: where a Mindless Skeleton dies (BR2; handoff s3.10 gap 22 top pick). Stock display 6328 (the
-- Blasted Lands spine and skull, about 0.9 yd at size 1; the troll skull pile 293 of Pile of Bones 177604 was the
-- build spec's first pick, replaced per s3.10) at size 1.4, GENERIC (type 5, no data, no script) and not selectable
-- (gameobject_template_addon flags 16 = GO_FLAG_NOT_SELECTABLE). Summoned by boss_baron_rivendare_rework, deleted when
-- a heroic rot raises it and at the fight's end. Upserts: gameobject_template rows are never deleted (codestyle-sql
-- not_delete).
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`, `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`, `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`, `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301207, 5, 6328, 'Bone Pile', '', '', '', 1.4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, '', '', 0) ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`), `name` = VALUES(`name`), `size` = VALUES(`size`), `AIName` = VALUES(`AIName`), `ScriptName` = VALUES(`ScriptName`);
DELETE FROM `gameobject_template_addon` WHERE `entry` = 301207;
INSERT INTO `gameobject_template_addon` (`entry`, `faction`, `flags`, `mingold`, `maxgold`, `artkit0`, `artkit1`, `artkit2`, `artkit3`) VALUES
(301207, 0, 16, 0, 0, 0, 0, 0, 0);
