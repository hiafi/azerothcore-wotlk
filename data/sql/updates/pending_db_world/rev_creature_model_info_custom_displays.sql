-- Missing creature_model_info rows for four live custom creature displays (Blackrock Depths build, fix F-1e; review
-- R-1-KIT M2, found by a scan of every creature_template_model row on a display in 90000-90999).
--
-- Creature::InitEntry cancels the load of a creature whose display has no creature_model_info row
-- (ObjectMgr::GetCreatureModelRandomGender returns null: "has no model ... can't load"), so the creature can never
-- spawn. The four displays already have their creaturedisplayinfo_dbc / creaturemodeldata_dbc rows live (checked
-- 2026-11-17: ObjectMgr::LoadCreatureModelInfo dereferences the display row, so a model-info row for a display the DBC
-- lacks crashes the boot; these four are safe).
--
--   90740  Blackrock Spire: the Frost Wall carrier 300734 (Rend and Gyth RG6; the Ascension icewall at scale 0.6 on the
--          display, 0.5 on the template row: an untargetable hitbox carrier, so a small box)
--   90002  Mage: Frozen Orb 300001
--   90003  Mage: Meteor Missile 300002
--   90004  Priest: Divine Star 300100
--
-- The Blackrock Depths keg displays 90770 / 90771 get theirs from patch_blackrock_depths_vfx_models.py --sql-out, in
-- the same import as their creaturedisplayinfo_dbc rows (the pairing rule above).
-- Same shape as the Deadmines iron shot (90700): 0.85 bounding radius, 1.0 combat reach.
DELETE FROM `creature_model_info` WHERE `DisplayID` IN (90002, 90003, 90004, 90740);
INSERT INTO `creature_model_info` (`DisplayID`, `BoundingRadius`, `CombatReach`, `Gender`, `DisplayID_Other_Gender`)
VALUES
(90002, 0.85, 1.0, 2, 0),
(90003, 0.85, 1.0, 2, 0),
(90004, 0.85, 1.0, 2, 0),
(90740, 0.85, 1.0, 2, 0);
