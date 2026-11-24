-- Scarlet Monastery build WP-W2-SETUP: the wave 2 SmartAI drop (.agents/plans/scarlet-monastery-build/
-- scarlet-monastery-build.HANDOFF.md s3.2 item 4, s4.2 row W2-SETUP, s10; STAGE-S0-REPORT s5 #9). Ships with the wave
-- switch (BIND_WAVE_2 in apps/dbc-tools source/npcs/scarlet_monastery/_common.py, kWave2Bound in modules/
-- mod-dungeon-bosses src/ScarletMonastery/ScarletMonasteryRework.h): Herod 3975, Mograine 3976 and Whitemane 3977 are
-- C++ from here on (D11, D13, D14), so their stock SmartAI goes. Row ids checked against the live DB (read-only
-- SELECT 2026-11-20). Every statement is idempotent.

-- Herod 3975: rows 0-9 (every row he has). The Scarlet Trainee 6575 keeps its own SmartAI (row 0 "set in combat with
-- zone"): D11 still summons the stock trainees on his death (STAGE-D11 report).
DELETE FROM `smart_scripts` WHERE `entryorguid` = 3975 AND `source_type` = 0 AND `id` BETWEEN 0 AND 9;

-- Mograine 3976: rows 0-28 and the action lists 397600-397602. The Ashbringer cameo (row 0, rows 25-27, list 397602)
-- now lives in D13's AI, armed by the instance only when it accepts the Ashbringer (HANDOFF s10, STAGE-R-1-KIT m-1
-- default c). Highlord Mograine 16062 and his list 1606200 stay stock (the cameo summons him).
DELETE FROM `smart_scripts` WHERE `entryorguid` = 3976 AND `source_type` = 0 AND `id` BETWEEN 0 AND 28;
DELETE FROM `smart_scripts` WHERE `entryorguid` IN (397600, 397601, 397602) AND `source_type` = 9;

-- Whitemane 3977: rows 0-19 and the action lists 397700-397701 (rows 0 and 10 opened / shut the High Inquisitor's
-- Door, guid 11877: the instance owns it now and opens it, latched, when the Last Stand is DONE).
DELETE FROM `smart_scripts` WHERE `entryorguid` = 3977 AND `source_type` = 0 AND `id` BETWEEN 0 AND 19;
DELETE FROM `smart_scripts` WHERE `entryorguid` IN (397700, 397701) AND `source_type` = 9;

-- Their SmartAI conditions (source type 22, SourceGroup = row id + 1): Mograine groups 1, 3, 18, 19, 26, 27, Whitemane
-- groups 17, 19 (live: nothing else names these two entries; Herod has none).
DELETE FROM `conditions` WHERE `SourceTypeOrReferenceId` = 22 AND `SourceId` = 0 AND `SourceEntry` = 3976
    AND `SourceGroup` IN (1, 3, 18, 19, 26, 27);
DELETE FROM `conditions` WHERE `SourceTypeOrReferenceId` = 22 AND `SourceId` = 0 AND `SourceEntry` = 3977
    AND `SourceGroup` IN (17, 19);

-- The Ashbringer areatrigger 4089 (SmartTrigger): rows 0-1 stay (the item and "data 2 is 0" conditions on row 0, then
-- SetData(2, 1) to the instance, which runs the guard); rows 2-3 go (they told Mograine whatever the guard decided, as
-- linked rows that no condition can stop: STAGE-F-1a s6). The instance tells him now. Row 1 stops linking to the
-- dropped row 2 (a link to a missing row logs an error at every trigger).
DELETE FROM `smart_scripts` WHERE `entryorguid` = 4089 AND `source_type` = 2 AND `id` IN (2, 3);
UPDATE `smart_scripts` SET `link` = 0 WHERE `entryorguid` = 4089 AND `source_type` = 2 AND `id` = 1;
