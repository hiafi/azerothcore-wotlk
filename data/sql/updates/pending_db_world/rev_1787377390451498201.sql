-- Custom: repurpose the (previously-unused) CR_WEAPON_SKILL_MAINHAND/OFFHAND/RANGED combat rating
-- slots (ids 20/21/22) into CR_MASTERY/CR_VERSATILITY/CR_COOLDOWN_REDUCTION - see Unit.h.
-- Their old `gtcombatratings_dbc` curves are shaped for converting rating into weapon-skill points,
-- not a percent, so they are overwritten here with a copy of the CR_CRIT_MELEE (id 8) percentage
-- curve, giving the 3 new stats a sane, already level-tuned percent-per-rating baseline. Balance can
-- be retuned later by editing `Data` directly - no code change needed.
-- `gtoctclasscombatratingscalar_dbc` needs no change: its rows for ids 20/21/22 are already a flat
-- `1` scalar per class, identical to CR_CRIT_MELEE's own scalar rows.
DELETE FROM `gtcombatratings_dbc` WHERE `ID` BETWEEN 2000 AND 2099;
INSERT INTO `gtcombatratings_dbc` (`ID`, `Data`) SELECT `ID` + 1200, `Data` FROM `gtcombatratings_dbc` WHERE `ID` BETWEEN 800 AND 899;
DELETE FROM `gtcombatratings_dbc` WHERE `ID` BETWEEN 2100 AND 2199;
INSERT INTO `gtcombatratings_dbc` (`ID`, `Data`) SELECT `ID` + 1300, `Data` FROM `gtcombatratings_dbc` WHERE `ID` BETWEEN 800 AND 899;
DELETE FROM `gtcombatratings_dbc` WHERE `ID` BETWEEN 2200 AND 2299;
INSERT INTO `gtcombatratings_dbc` (`ID`, `Data`) SELECT `ID` + 1400, `Data` FROM `gtcombatratings_dbc` WHERE `ID` BETWEEN 800 AND 899;
