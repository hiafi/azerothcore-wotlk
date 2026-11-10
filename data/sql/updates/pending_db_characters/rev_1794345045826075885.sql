-- Custom: gathering ranks (crafting rework C3, .agents/plans/crafting-rework/crafting-rework.PLAN.md).
-- One row per character per material; a material is the main item of a gathering loot (Thorium Ore, Peacebloom,
-- Rugged Leather). Rank 1-5; rank 0 has no row. `skill` is the gathering skill the rank was earned with (182
-- Herbalism, 186 Mining, 393 Skinning), for the Professions page. Read at login and written on rank-up by
-- src/server/scripts/Custom/custom_gathering_ranks.cpp. Playerbots get no rows.
CREATE TABLE IF NOT EXISTS `character_gathering_rank` (
  `guid` int unsigned NOT NULL COMMENT 'characters.guid',
  `item_entry` int unsigned NOT NULL COMMENT 'item_template.entry of the material',
  `skill` smallint unsigned NOT NULL DEFAULT 0 COMMENT 'SkillLine.dbc ID of the gathering skill',
  `rank` tinyint unsigned NOT NULL DEFAULT 0 COMMENT 'Gathering rank 0-5',
  PRIMARY KEY (`guid`, `item_entry`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Custom gathering ranks';
