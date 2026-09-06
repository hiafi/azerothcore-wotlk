-- DB update 2026_09_05_37 -> 2026_09_05_38
--
-- Shape-based itemization (docs/itemization-phase-2.md), implementation order step 13 (final):
-- bump `item_budget_version` from 1 to 2 -- the marker for "itemization data changed, client-side
-- item caches may be stale," bumped on any budget/itemization table change per that table's own
-- comment. It has never been bumped before now (seeded at 1 by the Phase-1 file,
-- rev_1788303168592708486.sql, and untouched since -- confirmed against live `acore_world`, still
-- reads (1,1) today).
--
-- Note on what this actually does: `item_budget_version` has no reader anywhere in `src/` --
-- confirmed by grep. There is no live code path that pushes this value to clients or forces a WDB
-- cache purge automatically; it is operator-facing bookkeeping only (a signal to whoever runs this
-- server that itemization changed and players may want to clear a stale item-cache.wdb), not a
-- mechanism this migration needs to wire up. Bumping it is still worth doing as the documented
-- final step of this system's own convention, not because any code reads it today.
--
-- *** Held with the rest of the batch, not because bumping this number could break anything on its
-- own (it's inert either way) -- but because "the itemization data changed" should become true at
-- the same moment steps 5-12 actually go live, not before. Apply together with steps 5, 6, 7, 9's
-- weapon fix, 11, and 12. ***
--
DELETE FROM `item_budget_version` WHERE `id` = 1;
INSERT INTO `item_budget_version` (`id`, `version`) VALUES
(1, 2);
