-- Root cause of the four test rings (70100-70103) showing a blank bag icon and not
-- auto-equipping on right-click: ObjectMgr::LoadItemTemplates() requires every
-- item_template entry to resolve against sItemStore (Item.dbc, loaded from the
-- "Item.dbc" file overlaid by the `item_dbc` table -- see DBCStores.cpp's
-- LOAD_DBC(sItemStore, "Item.dbc", "item_dbc")). The shipped Item.dbc file only
-- covers entries up to 56806 (the last real client item, asserted in
-- DBCStores.cpp). Any entry above that -- including custom ones -- needs its own
-- row in `item_dbc`, or ObjectMgr.cpp's `if (!dbcitem) continue;` skips the rest of
-- that item's load pass, leaving it only partially populated: fields set earlier in
-- the function (name, stats, DisplayInfoID, InventoryType) come through fine
-- (hence the correct tooltip and the ability to drag-equip manually), but whatever
-- the client needs for the bag icon and right-click auto-equip depends on
-- processing later in that same pass, which never runs.
--
-- Fix: give each ring an `item_dbc` row mirroring the real Item.dbc entry for
-- displayid 31664 (borrowed from the stock "Ring of Spell Power", entry 19147, which
-- already works and needs no `item_dbc` override since it's within the file's
-- range). Also correct `item_template.Material` to 3 to match -- it was left at the
-- generic default (0) when these rows were authored, which would otherwise get
-- flagged/corrected at load time (ObjectMgr.cpp's enforceDBCAttributes pass) and
-- gives the ring the wrong equip sound in the meantime.

DELETE FROM `item_dbc` WHERE `ID` IN (70100, 70101, 70102, 70103);
INSERT INTO `item_dbc` (`ID`, `ClassID`, `SubclassID`, `Sound_Override_Subclassid`, `Material`, `DisplayInfoID`, `InventoryType`, `SheatheType`) VALUES
  (70100, 4, 0, -1, 3, 31664, 11, 0),
  (70101, 4, 0, -1, 3, 31664, 11, 0),
  (70102, 4, 0, -1, 3, 31664, 11, 0),
  (70103, 4, 0, -1, 3, 31664, 11, 0);

UPDATE `item_template` SET `Material` = 3 WHERE `entry` IN (70100, 70101, 70102, 70103) AND `Material` = 0;
