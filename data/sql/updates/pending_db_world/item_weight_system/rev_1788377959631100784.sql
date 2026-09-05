-- item-tools: 'Arcanist Crown' (16795) budget assignment -> template 3. Hit -> Proc

DELETE FROM `item_budget_template` WHERE `template_id` = 3;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(3, 5, 4348),
(3, 6, 1610),
(3, 33, 1288),
(3, 45, 2754);

DELETE FROM `item_budget_template_name` WHERE `template_id` IN (3);
INSERT INTO `item_budget_template_name` (`template_id`, `name`) VALUES
(3, 'Arcanist Crown shape');

DELETE FROM `item_budget_assign` WHERE `entry` IN (16795);
INSERT INTO `item_budget_assign` (`entry`, `template_id`, `budget_mult`, `stamina_delta`, `dps_delta`, `absorbed_spell_slots`, `armor_delta`) VALUES
(16795, 3, 1.0, 0, 0.0, 3, 0);

UPDATE `item_template` SET `stat_type1` = 5, `stat_value1` = 20, `stat_type2` = 6, `stat_value2` = 8, `stat_type3` = 33, `stat_value3` = 6, `stat_type4` = 45, `stat_value4` = 15, `stat_type5` = 7, `stat_value5` = 20, `spellid_1` = 0, `spelltrigger_1` = 0, `spellid_2` = 0, `spelltrigger_2` = 0 WHERE `entry` = 16795 AND `stat_type1` = 7 AND `stat_value1` = 16 AND `stat_type2` = 5 AND `stat_value2` = 27 AND `stat_type3` = 6 AND `stat_value3` = 10 AND `stat_type4` = 0 AND `stat_value4` = 0 AND `stat_type5` = 0 AND `stat_value5` = 0 AND `spellid_1` = 14799 AND `spelltrigger_1` = 1 AND `spellid_2` = 23727 AND `spelltrigger_2` = 1;
