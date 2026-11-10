-- Stratholme build WP-S5: Cannon Master Willey (10997), the rows dbc-tools cannot declare
-- (.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.5 row S5; build spec
-- docs/dungeons/stratholme-rework.md ST 1444-1502). His template (boss_cannon_master_willey_rework, AIName '',
-- health, DamageModifier 3.5 (stock), immunity 1972), the Crimson Rifleman's (npc_st_crimson_rifleman, AIName '',
-- 5,000 health) and the spells 206500-206508 are apps/dbc-tools source/npcs/stratholme/cannon_master_willey.py.

-- SmartAI 10997 (seven rows: Knock Away, Pummel, Summon Crimson Rifleman 17279 in combat and three times on death, the
-- respawn on reaching home) is removed: boss_cannon_master_willey_rework keeps Knock Away and Pummel, summons the
-- ranks itself (capped, none on death).
DELETE FROM `smart_scripts` WHERE `entryorguid` = 10997 AND `source_type` = 0;

-- SmartAI 11054 (four rows: Shoot, attack and despawn out of combat, die on the click Cannon Fire 17278) is removed:
-- npc_st_crimson_rifleman shoots between volleys, Willey drives Aim and Fire, and his reset despawns his riflemen.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 11054 AND `source_type` = 0;

-- His texts (ST "Text"; he had none). Yells (14); the Barrage's order is a built boss emote, not a row here.
DELETE FROM `creature_text` WHERE `CreatureID` = 10997 AND `GroupID` BETWEEN 0 AND 7;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10997, 0, 0, 'Clear the range! Riflemen, to me!', 14, 0, 100, 0, 0, 0, 0, 0, 'Cannon Master Willey - Aggro'),
(10997, 1, 0, 'Ready!', 14, 0, 100, 0, 0, 0, 0, 0, 'Cannon Master Willey - The Drill (WY1)'),
(10997, 2, 0, 'Aim!', 14, 0, 100, 0, 0, 0, 0, 0, 'Cannon Master Willey - Aim (WY2)'),
(10997, 3, 0, 'Fire!', 14, 0, 100, 0, 0, 0, 0, 0, 'Cannon Master Willey - Fire (WY3)'),
(10997, 4, 0, 'Mercy, fire!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Cannon Master Willey - Cannon Fire, Mercy (WY8)'),
(10997, 5, 0, 'Zeal, fire!', 14, 0, 100, 0, 0, 0, 0, 0, 'Cannon Master Willey - Cannon Fire, Zeal (WY8)'),
(10997, 6, 0, 'Who loaded my guns?!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Cannon Master Willey - First cannon shot on him (WY6)'),
(10997, 7, 0, 'Cease... fire...', 14, 0, 100, 0, 0, 0, 0, 0, 'Cannon Master Willey - Death');

-- 301200 Mercy and 301201 Zeal (ruling 24): the stock Scarlet Cannon's display 245 (G_Cannon01) at its size 0.75, as
-- GENERIC (type 5: no lock, no key item, no click; Data1 highlight shows the name). The script plays their firing
-- animation (SendCustomAnim) when a lane or a loaded shot fires. 301202 Scarlet Cannonball: the ball a rank drops
-- (handoff s3.10: display 153 CatapultBall01, the stock 176211 is the invisible trap display 1287) at size 0.45 (about
-- 1.1 yd), GENERIC and not selectable: picked up by walking over it (the script's walk-over pickup), summoned for 20 s.
-- Upserts: gameobject_template rows are never deleted (codestyle-sql not_delete).
INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, `size`,
    `Data0`, `Data1`, `Data2`, `Data3`, `Data4`, `Data5`, `Data6`, `Data7`, `Data8`, `Data9`, `Data10`, `Data11`,
    `Data12`, `Data13`, `Data14`, `Data15`, `Data16`, `Data17`, `Data18`, `Data19`, `Data20`, `Data21`, `Data22`,
    `Data23`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES
(301200, 5, 245, 'Mercy', '', '', '', 0.75, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    '', '', 0),
(301201, 5, 245, 'Zeal', '', '', '', 0.75, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    '', '', 0),
(301202, 5, 153, 'Scarlet Cannonball', '', '', '', 0.45, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, '', '', 0) ON DUPLICATE KEY UPDATE `type` = VALUES(`type`), `displayId` = VALUES(`displayId`),
    `name` = VALUES(`name`), `size` = VALUES(`size`), `Data1` = VALUES(`Data1`), `AIName` = VALUES(`AIName`),
    `ScriptName` = VALUES(`ScriptName`);
DELETE FROM `gameobject_template_addon` WHERE `entry` IN (301200, 301201, 301202);
INSERT INTO `gameobject_template_addon` (`entry`, `faction`, `flags`, `mingold`, `maxgold`, `artkit0`, `artkit1`,
    `artkit2`, `artkit3`) VALUES
(301200, 0, 0, 0, 0, 0, 0, 0, 0),
(301201, 0, 0, 0, 0, 0, 0, 0, 0),
(301202, 0, 16, 0, 0, 0, 0, 0, 0);

-- The stock Scarlet Cannons' spawns become Mercy and Zeal in place (same guid, position, rotation and spawnMask 3):
-- Mercy on 176216's spot (the east half), Zeal on 176217's (the west half). The stock templates and their SmartAI stay
-- (nothing else spawns them).
UPDATE `gameobject` SET `id` = 301200 WHERE `id` = 176216 AND `guid` = 20761;
UPDATE `gameobject` SET `id` = 301201 WHERE `id` = 176217 AND `guid` = 20768;

-- The five Cannonball Stacks (176215) leave the fight (ST "Stock kit": balls come from the riflemen now; the key item
-- 12973 they gave loaded only the stock cannons).
DELETE FROM `gameobject` WHERE `id` = 176215 AND `guid` IN (20756, 20757, 20758, 20759, 20760);
