-- DB update 2026_10_23_14 -> 2026_10_23_15
-- shaman-rework playtest fix pass P3: Restoration talents moved (Mana Tide Totem to row 5, Tidal Force to row 3, Spirit Link Totem to row 6, column 1). Force a talent reset for every shaman so no build keeps a talent in a cell it no longer fills.
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 7;
