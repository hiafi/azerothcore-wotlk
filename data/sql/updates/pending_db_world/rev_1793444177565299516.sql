-- Priest "Garments of ..." quests: Lesser Heal is retired for players; npc_garments_of_quests also accepts Greater Heal.
UPDATE `quest_template` SET `LogDescription` = REPLACE(`LogDescription`, 'using Lesser Heal (Rank 2)', 'using Greater Heal') WHERE `ID` IN (5621, 5624, 5625, 5648, 5650);
