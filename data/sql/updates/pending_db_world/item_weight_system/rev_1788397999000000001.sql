-- Phase 5 content, Bucket 2: removes the budget-system rows for entry 40832
-- (ObsoleteSigil of Pestilential Touch), excluded from the budget system --
-- see the companion item_template revert in this same batch for why.
DELETE FROM `item_budget_template` WHERE `template_id` = 6592;
DELETE FROM `item_budget_template_name` WHERE `template_id` = 6592;
DELETE FROM `item_budget_assign` WHERE `entry` = 40832;
