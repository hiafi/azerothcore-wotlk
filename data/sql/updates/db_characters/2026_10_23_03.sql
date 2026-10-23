-- DB update 2026_10_23_02 -> 2026_10_23_03
-- hunter-rework H0-FIX: the AQ20 class spell books no longer teach their spell (dbc-tools source/world/aq_books.py), so a
-- character that already learned one of those rank-upgrade spells loses it. Idempotent; run with the worldserver stopped.
DELETE FROM `character_spell` WHERE `spell` IN (25286, 25288, 25289, 25290, 25291, 25292, 25294, 25295, 25296, 25297, 25298, 25299, 25300, 25302, 25304, 25306, 25307, 25309, 25311, 25314, 25315, 25316, 25345, 31016, 25357, 25361);
DELETE FROM `character_action` WHERE `type` = 0 AND `action` IN (25286, 25288, 25289, 25290, 25291, 25292, 25294, 25295, 25296, 25297, 25298, 25299, 25300, 25302, 25304, 25306, 25307, 25309, 25311, 25314, 25315, 25316, 25345, 31016, 25357, 25361);
