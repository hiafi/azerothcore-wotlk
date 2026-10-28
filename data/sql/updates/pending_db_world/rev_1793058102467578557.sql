-- rogue-rework RG0a: poison items leave every vendor (PLAN §1C.3); quest 2359 stops teaching Poisons 2842
DELETE FROM `npc_vendor` WHERE `item` IN (
    6947, 6949, 6950, 8926, 8927, 8928, 21927, 43230, 43231, 2892, 2893, 8984, 8985, 20844, 22053,
    22054, 43232, 43233, 10918, 10920, 10921, 10922, 22055, 43234, 43235, 3775, 5237, 21835, 43237
);

UPDATE `quest_template` SET `RewardSpell` = 0 WHERE `ID` = 2359;
