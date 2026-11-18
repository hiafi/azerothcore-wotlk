-- Weapon scaling WS0c: item_itemization.spell_power_per_dps (a plain ALTER cannot be re-applied, so it gets a file of
-- its own; never edit this file after it is imported).
--
-- Spell power per point of weapon DPS (k_sp of the slot times the spell power multiplier m of the weapon), written by
-- dbc-tools (apps/dbc-tools/lib/weapon_spell_power.py) for every weapon it covers. ItemBudget.cpp reads it: a weapon
-- with a value above 0 loses the Spell Power its shapes budget (the share goes to the other stats of the shape) and
-- gets lround(spell_power_per_dps x final DPS) Spell Power (stat 45) as an off-budget line after Stamina. 0 (the
-- default) materializes exactly as before.
--
-- ItemBudget.cpp selects this column, so a worldserver built with WS0c needs this file imported first.
ALTER TABLE `item_itemization`
  ADD COLUMN `spell_power_per_dps` float NOT NULL DEFAULT '0'
    COMMENT 'weapons only: off-budget Spell Power per point of final DPS (k_sp x m), 0 = none'
    AFTER `block_value_delta`;
