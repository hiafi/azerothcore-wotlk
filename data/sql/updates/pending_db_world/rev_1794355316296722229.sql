-- Custom: help text for the gathering rank commands (crafting rework C3, custom_gathering_ranks.cpp).
DELETE FROM `command` WHERE `name` IN ('gathering', 'gathering ranks', 'gathering setrank', 'gathering sim', 'gathering reload');
INSERT INTO `command` (`name`, `security`, `help`) VALUES
('gathering', 0, 'Syntax: .gathering $subcommand\nType .gathering to see the list of possible subcommands or .help gathering $subcommand to see info on subcommands.'),
('gathering ranks', 0, 'Syntax: .gathering ranks\nLists your gathering rank (0-5) in every ore, herb and leather you have ranked up.'),
('gathering setrank', 2, 'Syntax: .gathering setrank #itemId #rank\nSets the selected player\'s (or your own) gathering rank 0-5 in the material #itemId (e.g. 10620 Thorium Ore). Test command; refused for playerbots.'),
('gathering sim', 2, 'Syntax: .gathering sim $source #lootId #rank [#gathers]\n$source is node or skin; #lootId is the gameobject or skinning loot id (Copper Vein 1502, Small Thorium Vein 9597, Peacebloom 1415). Generates the loot #gathers times (default 5000, max 20000) at rank 0 and at #rank and compares the main material count, the rare extra rates and the rank-up rate with the design. Nothing is given and no rank changes.'),
('gathering reload', 2, 'Syntax: .gathering reload\nRebuilds the gathering material cache from the loaded loot tables.');
