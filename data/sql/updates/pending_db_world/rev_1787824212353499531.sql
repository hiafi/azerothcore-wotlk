-- Conjure Refreshment's item (43518, Conjured Mana Pie): drop RequiredLevel from the real pulled
-- data's 74 to 1. The pulled RequiredLevel matched the old flat-value spell's level-gated tuning
-- (61828 "Refreshment" was learned at 75); now that Conjure Refreshment itself is learnable at 10
-- (see the mage.csv notes on 42955, docs/frost-mage-redesign.md sec 2) the item it conjures should
-- be usable immediately too, not gated 60+ levels above the spell that creates it. Plain UPDATE,
-- not DELETE+INSERT - item_template is on this repo's SQL linter's do-not-delete list (see the
-- Mana Agate/Mana Pie edits in rev_1787563173168071680.sql for the same reasoning). The
-- `RequiredLevel = 74` guard makes it a no-op on a second run.
UPDATE `item_template` SET `RequiredLevel` = 1 WHERE `entry` = 43518 AND `RequiredLevel` = 74;
