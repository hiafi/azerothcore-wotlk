-- Blackrock Depths build WP-L-2: the gameobject loot of sections 3 and 4, the rows apps/dbc-tools' loot DSL cannot
-- declare (it writes creature loot only; the creature lists, the Emperor's pool, tokens, hard mode lists and the Dark
-- Keeper Key rows are source/items/blackrock_depths_loot.py, wave 2 section).
-- .agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.6 and s4.2 row L-2; docs/dungeons/
-- blackrock-depths-rework.md "## Loot" (Section 4: the Chest of The Seven, rulings 85-87).

-- The Chest of The Seven 169243 (loot 12260; stock: 2 rolls of the 8 blue items of reference 12005, nothing else uses
-- the pool). The stock pool becomes the approved six (docs/dungeons/blackrock-depths-rework.md Section 4: Wraith
-- Scythe, Blood-etched Blade, The Hammer of Grace, Deathdealer Breastplate, and Moira's Ebonsteel Spaulders and
-- Swiftwalker Boots): 2 distinct items per kill. The Seven drop no corpse loot (lootid 0), so the chest is their only
-- gear. Impervious Giant, Ghostshroud, Legplates of the Eternal Guardian and Haunting Specter Leggings are cut.
--
-- One chest object serves both difficulties, so the pool holds both tiers: group 1 the Normal tier (LootMode 1),
-- group 2 the Heroic tier (LootMode 2). The reference row rolls under either mode (LootMode 3, MaxCount 2 = two
-- distinct picks: a group roll skips an equippable item the loot already holds from the same group); only the pool
-- group whose LootMode bit the chest carries has valid entries. The instance script sets LootMode 2 on the chest on
-- heroic (instance_blackrock_depths_rework.cpp OnGameObjectCreate, case GO_CHEST_SEVEN: SetLootMode, not AddLootMode);
-- without that line a heroic chest drops the Normal tier like the normal one (it never drops nothing).
DELETE FROM `reference_loot_template` WHERE `Entry` = 12005;
INSERT INTO `reference_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, `LootMode`, `GroupId`,
    `MinCount`, `MaxCount`, `Comment`) VALUES
(12005, 11920, 0, 0, 0, 1, 1, 1, 1, 'Chest of The Seven pool - Wraith Scythe (Normal)'),
(12005, 11922, 0, 0, 0, 1, 1, 1, 1, 'Chest of The Seven pool - Blood-etched Blade (Normal)'),
(12005, 11923, 0, 0, 0, 1, 1, 1, 1, 'Chest of The Seven pool - The Hammer of Grace (Normal)'),
(12005, 11926, 0, 0, 0, 1, 1, 1, 1, 'Chest of The Seven pool - Deathdealer Breastplate (Normal)'),
(12005, 12557, 0, 0, 0, 1, 1, 1, 1, 'Chest of The Seven pool - Ebonsteel Spaulders (Normal)'),
(12005, 12553, 0, 0, 0, 1, 1, 1, 1, 'Chest of The Seven pool - Swiftwalker Boots (Normal)'),
(12005, 73082, 0, 0, 0, 2, 2, 1, 1, 'Chest of The Seven pool - Wraith Scythe (Heroic)'),
(12005, 73086, 0, 0, 0, 2, 2, 1, 1, 'Chest of The Seven pool - Blood-etched Blade (Heroic)'),
(12005, 73090, 0, 0, 0, 2, 2, 1, 1, 'Chest of The Seven pool - The Hammer of Grace (Heroic)'),
(12005, 73094, 0, 0, 0, 2, 2, 1, 1, 'Chest of The Seven pool - Deathdealer Breastplate (Heroic)'),
(12005, 73098, 0, 0, 0, 2, 2, 1, 1, 'Chest of The Seven pool - Ebonsteel Spaulders (Heroic)'),
(12005, 73102, 0, 0, 0, 2, 2, 1, 1, 'Chest of The Seven pool - Swiftwalker Boots (Heroic)');

DELETE FROM `gameobject_loot_template` WHERE `Entry` = 12260;
INSERT INTO `gameobject_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, `LootMode`,
    `GroupId`, `MinCount`, `MaxCount`, `Comment`) VALUES
(12260, 12005, 12005, 0, 0, 3, 1, 2, 2, 'Chest of The Seven - 2 of the 6 pool items (Normal, or Heroic at LootMode 2)');
