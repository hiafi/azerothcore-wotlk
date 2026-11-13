-- Custom: help text for the Class Advancement window GM command (classless-ui U2, custom_talent_ui.cpp).
DELETE FROM `command` WHERE `name` IN ('talentui', 'talentui allclasses');
INSERT INTO `command` (`name`, `security`, `help`) VALUES
('talentui', 2, 'Syntax: .talentui $subcommand\nType .talentui to see the list of possible subcommands or .help talentui $subcommand to see info on subcommands.'),
('talentui allclasses', 2, 'Syntax: .talentui allclasses [on|off]\nToggles (or sets) whether your Class Advancement window lists all ten classes\' talent trees. Your own session only, not saved. Learning another class\'s talents is still refused.');
