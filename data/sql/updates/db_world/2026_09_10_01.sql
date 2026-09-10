-- DB update 2026_09_10_00 -> 2026_09_10_01
-- Death Knight starting position: spawn in the normal racial starting zone instead of Ebon Hold
-- (map 609), matching the level-1 DK starting experience (see docs/bugs-and-fixes.md and the
-- trainer work in rev_1788687658359759602.sql / rev_1788689427900916967.sql).
--
-- Copied from each race's Warrior (`class` = 1) row, since Warrior has no race restrictions for
-- every race Death Knight also covers -- except Blood Elf (`race` = 10), which Warrior can't be in
-- this expansion; copied from Paladin (`class` = 2) instead, whose Blood Elf row is identical to
-- every other Blood Elf class (Hunter/Rogue/Priest/Mage/Warlock all match).
--
-- Scoped by `map` = 609 so this is a no-op if re-run after already applying.
UPDATE `playercreateinfo` SET `map` = 0,   `zone` = 12,   `position_x` = -8949.95, `position_y` = -132.493,  `position_z` = 83.5312,  `orientation` = 0
    WHERE `race` = 1  AND `class` = 6 AND `map` = 609; -- Human, from Warrior
UPDATE `playercreateinfo` SET `map` = 1,   `zone` = 14,   `position_x` = -618.518, `position_y` = -4251.67,  `position_z` = 38.718,   `orientation` = 0
    WHERE `race` = 2  AND `class` = 6 AND `map` = 609; -- Orc, from Warrior
UPDATE `playercreateinfo` SET `map` = 0,   `zone` = 1,    `position_x` = -6240.32, `position_y` = 331.033,   `position_z` = 382.758,  `orientation` = 6.17716
    WHERE `race` = 3  AND `class` = 6 AND `map` = 609; -- Dwarf, from Warrior
UPDATE `playercreateinfo` SET `map` = 1,   `zone` = 141,  `position_x` = 10311.3,  `position_y` = 832.463,   `position_z` = 1326.41,  `orientation` = 5.69632
    WHERE `race` = 4  AND `class` = 6 AND `map` = 609; -- Night Elf, from Warrior
UPDATE `playercreateinfo` SET `map` = 0,   `zone` = 85,   `position_x` = 1676.71,  `position_y` = 1678.31,   `position_z` = 121.67,   `orientation` = 2.70526
    WHERE `race` = 5  AND `class` = 6 AND `map` = 609; -- Undead, from Warrior
UPDATE `playercreateinfo` SET `map` = 1,   `zone` = 215,  `position_x` = -2917.58, `position_y` = -257.98,   `position_z` = 52.9968,  `orientation` = 0
    WHERE `race` = 6  AND `class` = 6 AND `map` = 609; -- Tauren, from Warrior
UPDATE `playercreateinfo` SET `map` = 0,   `zone` = 1,    `position_x` = -6240.32, `position_y` = 331.033,   `position_z` = 382.758,  `orientation` = 0
    WHERE `race` = 7  AND `class` = 6 AND `map` = 609; -- Gnome, from Warrior
UPDATE `playercreateinfo` SET `map` = 1,   `zone` = 14,   `position_x` = -618.518, `position_y` = -4251.67,  `position_z` = 38.718,   `orientation` = 0
    WHERE `race` = 8  AND `class` = 6 AND `map` = 609; -- Troll, from Warrior
UPDATE `playercreateinfo` SET `map` = 530, `zone` = 3431, `position_x` = 10349.6,  `position_y` = -6357.29,  `position_z` = 33.4026,  `orientation` = 5.31605
    WHERE `race` = 10 AND `class` = 6 AND `map` = 609; -- Blood Elf, from Paladin (no Warrior row)
UPDATE `playercreateinfo` SET `map` = 530, `zone` = 3526, `position_x` = -3961.64, `position_y` = -13931.2,  `position_z` = 100.615,  `orientation` = 2.08364
    WHERE `race` = 11 AND `class` = 6 AND `map` = 609; -- Draenei, from Warrior
