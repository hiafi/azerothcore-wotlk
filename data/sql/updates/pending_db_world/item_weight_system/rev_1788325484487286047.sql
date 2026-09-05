--
-- Phase 2 smoke test, now a real conversion: item 16800 (Arcanist Boots --
-- Mage T1, Molten Core, ilvl 66, part of item set 201). Its two on-equip
-- spells were pure passive stat auras (spell 18384: +14 Critical Strike
-- Rating; spell 9416: +11 spell power via SPELL_AURA_MOD_DAMAGE_DONE) --
-- see docs/itemization-changes.md §4.5's revision-2 note and §9.8. Both are
-- folded into the plain stat block as stat_type 32 (Crit Rating) and 45
-- (Spell Power) instead of staying hidden behind a spellid, and both spell
-- slots are marked absorbed so ApplyItemBudgetAllocation() clears them --
-- otherwise the item would grant the same bonus twice, once as a stat and
-- once as a still-live proc.
--
-- template_id 1 (Caster Int/Spirit) stays defined as a placeholder/generic
-- shape; template 2 below is Arcanist Boots' actual shape, weighted by
-- item_stat_cost same as the curve regression:
--   Int 14 * cost 1.000 = 14.000
--   Spirit 11 * cost 1.000 = 11.000
--   Crit Rating 14 * cost 1.000 = 14.000
--   Spell Power 11 * cost 0.855 = 9.405
--   total weighted = 48.405 -> alloc (ten-thousandths, largest-remainder rounded):
--   Int 2892, Spirit 2273, Crit 2892, Spell Power 1943 (sums to 10000)
--
-- Predicted by hand against the loaded curves (docs/itemization-changes.md,
-- curve revision 2 -- see §4.5); budget_mult/set_discount are unchanged
-- from the earlier test, so effective_budget is still 34:
--   budget = curve[66]=51 * slotmult(feet)=0.75 * qualitymult(epic)=1.0
--          * effective_mult(budget_mult=1.0 * set_discount=0.9) = 34.425 -> 34
--   stamina = round(stamina_curve[66]=20 * 0.75 * 1.0) = 15
--   Int: 34*0.2892/1.000 = 9.833 -> floor 9, remainder 0.833
--   Spirit: 34*0.2273/1.000 = 7.728 -> floor 7, remainder 0.728
--   Crit: 34*0.2892/1.000 = 9.833 -> floor 9, remainder 0.833
--   Spell Power: 34*0.1943/0.855 = 7.727 -> floor 7, remainder 0.727
--   exact sum 35.120 -> target 35, 3 remainder points to the 3 largest
--   remainders (Int, Crit, Spirit) -- Spell Power stays at its floor
--   final stats: Stamina 15, Intellect 10, Spirit 8, Crit Rating 10, Spell Power 7
--   final spells: none (both slots absorbed into the stats above)
--
-- Armor (§9.3a, off-budget, unrelated to template/absorption above) is also
-- materialized now that item_armor_curve is loaded:
--   baseline_armor = armor_curve[66][Cloth]=116 * armor_slotmult(feet)=0.6875
--                   * armor_qualitymult(epic)=1.0 = 79.75 -> 80
--   armor_delta 0 -> final_armor 80
-- Confirmed live via `.item budget 16800`: matches on every line, including
-- an exact match to Arcanist Boots' original, hand-authored Armor (80) --
-- expected, since this item is not a PvP-season/catch-up-gear outlier.
--

DELETE FROM `item_budget_template` WHERE `template_id` = 1;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(1, 5, 6000), -- Intellect 60%
(1, 6, 4000); -- Spirit 40%

DELETE FROM `item_budget_template_name` WHERE `template_id` = 1;
INSERT INTO `item_budget_template_name` (`template_id`, `name`) VALUES
(1, 'Caster Int/Spirit (generic placeholder)');

DELETE FROM `item_budget_template` WHERE `template_id` = 2;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(2, 5, 2892),  -- Intellect
(2, 6, 2273),  -- Spirit
(2, 32, 2892), -- Critical Strike Rating
(2, 45, 1943); -- Spell Power

DELETE FROM `item_budget_template_name` WHERE `template_id` = 2;
INSERT INTO `item_budget_template_name` (`template_id`, `name`) VALUES
(2, 'Caster Int/Spirit/Crit/SpellPower (Arcanist Boots shape)');

DELETE FROM `item_budget_assign` WHERE `entry` = 16800;
INSERT INTO `item_budget_assign` (`entry`, `template_id`, `budget_mult`, `stamina_delta`, `dps_delta`, `absorbed_spell_slots`) VALUES
(16800, 2, 1.0, 0, 0.0, 3); -- bits 0+1: absorb spellid_1 (18384) and spellid_2 (9416)
