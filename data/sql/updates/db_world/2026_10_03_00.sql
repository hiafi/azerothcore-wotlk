-- DB update 2026_09_05_38 -> 2026_10_03_00
-- Custom: potency-system - low-level correction + variance roll (docs/potency-system.md).
-- Loaded by SpellPotency::Load() (src/server/game/Spells/SpellPotency.cpp) via
-- OnLoadCustomDatabaseTable, applied in SpellEffectInfo::CalcValue (SpellInfo.cpp).
-- cp_* columns are the finisher per-combo-point scaling (PLAN P6 step 4) - 0 for every non-finisher row.
CREATE TABLE IF NOT EXISTS `spell_potency_correction` (
    `spell_id`              INT UNSIGNED NOT NULL,
    `effect_index`          TINYINT UNSIGNED NOT NULL,
    `correction_per_level`  FLOAT NOT NULL DEFAULT 0           COMMENT 'K: added per level below breakpoint_level',
    `breakpoint_level`      TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Level 25 today; stored per row so the number lives only in the generator',
    `variance_pct`          FLOAT NOT NULL DEFAULT 0           COMMENT '10 on direct damage effects, 0 on periodic',
    `cp_line`               FLOAT NOT NULL DEFAULT 0           COMMENT 'Finisher: flat value per combo point',
    `cp_correction_per_level` FLOAT NOT NULL DEFAULT 0         COMMENT 'Finisher: low-level correction per combo point',
    `cp_ap`                 FLOAT NOT NULL DEFAULT 0           COMMENT 'Finisher: attack power per combo point',
    `comment`               VARCHAR(255) DEFAULT ''            COMMENT 'Generator source, e.g. "potency 100, 3.0s cast"',
    PRIMARY KEY (`spell_id`, `effect_index`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
