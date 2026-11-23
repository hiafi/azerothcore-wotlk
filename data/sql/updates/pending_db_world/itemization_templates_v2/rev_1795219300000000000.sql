-- Secondary stat curve (level60-stat-curve): bumps item_budget_version 4 -> 5 (operator bookkeeping: item caches may
-- be stale). Every itemized item with a crit, haste, mastery, versatility, cooldown haste, proc, armor penetration,
-- dodge, parry or block line changes, as do caster and hunter ranged weapons. Clients should clear their Cache folder.
DELETE FROM `item_budget_version` WHERE `id` = 1;
INSERT INTO `item_budget_version` (`id`, `version`) VALUES
(1, 5);
