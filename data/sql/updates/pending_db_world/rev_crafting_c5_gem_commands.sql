-- Custom: help text for the gem test command (crafting rework C5, custom_crafting_gems.cpp).
DELETE FROM `command` WHERE `name` IN ('gems', 'gems count');
INSERT INTO `command` (`name`, `security`, `help`) VALUES
('gems', 2, 'Syntax: .gems $subcommand\nType .gems to see the list of possible subcommands or .help gems $subcommand to see info on subcommands.'),
('gems count', 2, 'Syntax: .gems count\nShows the selected player\'s (or your own) socketed gem counts by color and what each meta gem gives at those counts.');
