-- Shadowfang Keep build WP-F (R1 cross-scope, R2 S-5): Rethilgore's stock Rugged Spaulders 5254 drops at 100% from
-- group 0 of his loot (3914), next to the food and the Sharp Claw. The SFK loot list
-- (apps/dbc-tools source/items/shadowfang_keep_loot.py) already rolls sfk_rugged_spaulders, whose normal tier is 5254
-- itself, in group 1; without this the normal kill can drop it twice, and the heroic copy of group 0 on 310048
-- (derive_heroic_copies) always drops the level 21 piece. Only the 5254 row goes: group 0 keeps 1205, 3770 and 5635.
DELETE FROM `creature_loot_template` WHERE `Entry` = 3914 AND `Item` = 5254 AND `GroupId` = 0;
