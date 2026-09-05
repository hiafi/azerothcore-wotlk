-- Follow-up cleanup for the four test rings (70100-70103):
-- - BuyCount was left at 0, which ObjectMgr.cpp's load-time validation flags
--   and silently corrects to 1 every startup ("has wrong BuyCount value (0),
--   set to default(1)"); set it in the DB so the warning stops recurring.
-- - BuyPrice/SellPrice were left at 0 (no vendor price at all); match the stock
--   "Ring of Spell Power" (entry 19147, same item level bracket/quality) instead
--   of leaving them unsellable.

UPDATE `item_template` SET `BuyCount` = 1, `BuyPrice` = 365815, `SellPrice` = 91453
WHERE `entry` IN (70100, 70101, 70102, 70103) AND `BuyCount` = 0 AND `BuyPrice` = 0 AND `SellPrice` = 0;
