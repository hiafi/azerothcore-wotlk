-- DB update 2026_10_23_31 -> 2026_10_23_32
-- Shaman rework SH0a: Shaman quests no longer teach/display the retired spells (item rewards stay)
UPDATE `quest_template` SET `RewardSpell` = 0, `RewardDisplaySpell` = 0 WHERE `ID` IN (1518, 1521, 9451);
-- Shaman rework SH0a: remove Frost Shock bonus threat
DELETE FROM `spell_threat` WHERE `entry` = 8056;
