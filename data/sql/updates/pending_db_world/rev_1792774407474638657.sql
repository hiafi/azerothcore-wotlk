-- P0 spike (death-knight-rework): no Blood Presence cast at creation; re-inserted at removal
-- (P0-HANDOFF item 5, Decision D2). Removal re-inserts (0, 32, 48266, 'Death Knight - Blood Presence') unless DK0a
-- deletes the row in the same deploy.
DELETE FROM `playercreateinfo_cast_spell` WHERE `raceMask` = 0 AND `classMask` = 32 AND `spell` = 48266;
