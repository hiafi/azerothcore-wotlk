-- Scarlet Monastery gear: bumps item_budget_version 3 -> 4 (operator bookkeeping: item caches may be stale).
-- Already-live minted items 71364, 73194, 73202 and 73514 change stats, and 334 caster weapons gain weapon spell
-- power now that the item level 100 bound is gone. Clients should clear their Cache folder.
DELETE FROM `item_budget_version` WHERE `id` = 1;
INSERT INTO `item_budget_version` (`id`, `version`) VALUES
(1, 4);
