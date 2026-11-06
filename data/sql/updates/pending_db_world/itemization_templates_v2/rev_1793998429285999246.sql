-- Item variants IV0: the item_budget_variant tier column (split out of rev_1793991695404125757.sql, R1 N7: a plain
-- ALTER cannot be re-applied, so it does not share a file with re-runnable DELETE/INSERTs; never edit this file
-- after it is imported).
--
-- item_budget_variant.tier: the variant's step on its ladder, set explicitly per tier in dbc-tools
-- (`tier(step=N)`, source/items/ladders.py): 0 = Normal, 1 = Heroic, 2.. = the empowered tiers, the same number for
-- the same step on every ladder, so the empowered module can look up (base_entry, tier) -> entry from the database.
-- A ladder's base tier has no row (it is the base); a hard mode base (Heroic Hard Mode) is step 1.
-- ItemBudget.cpp reads the table as "SELECT entry, base_entry", so an extra column changes nothing at boot.
ALTER TABLE `item_budget_variant`
  ADD COLUMN `tier` tinyint unsigned NOT NULL DEFAULT '0'
    COMMENT 'ladder step: 0 = Normal, 1 = Heroic, 2.. = empowered, the base tier has no row'
    AFTER `base_entry`;
