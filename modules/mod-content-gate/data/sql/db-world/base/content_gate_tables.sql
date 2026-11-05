-- mod-content-gate: unlock bundles (README "Bundles"). Rows are shipped as pending world SQL, not here.
CREATE TABLE IF NOT EXISTS `content_gate_bundle` (
    `name` VARCHAR(32) NOT NULL COMMENT 'Bundle name, [a-z0-9_], used in ContentGate.Open.Bundles',
    `gameEvent` TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT 'Always-on custom game_event of the spawns, 0 = none',
    `opensWith` VARCHAR(64) NOT NULL DEFAULT '' COMMENT 'map:<id>:<mode> | bg:<id> | outland | northrend | empty',
    `comment` VARCHAR(255) NOT NULL DEFAULT '',
    PRIMARY KEY (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='mod-content-gate unlock bundles';

CREATE TABLE IF NOT EXISTS `content_gate_bundle_disable` (
    `bundle` VARCHAR(32) NOT NULL COMMENT 'content_gate_bundle.name',
    `sourceType` TINYINT UNSIGNED NOT NULL COMMENT 'DisableType: 1 quest, 4 achievement criteria, 10 loot',
    `entry` INT UNSIGNED NOT NULL,
    `comment` VARCHAR(255) NOT NULL DEFAULT '',
    PRIMARY KEY (`bundle`, `sourceType`, `entry`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='mod-content-gate bundle members';
