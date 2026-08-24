-- Remove the level-83 training dummy (entry 900000, guid 5300682) added in
-- rev_1787529689976088420.sql -- no longer needed now that the level-bracket dummies
-- (900001/900002/900003, rev_1787545308095684126.sql) cover at-level testing.

DELETE FROM `creature` WHERE `guid` = 5300682;
DELETE FROM `creature_template_model` WHERE `CreatureID` = 900000;
DELETE FROM `creature_template` WHERE `entry` = 900000;
