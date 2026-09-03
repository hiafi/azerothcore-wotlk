--
-- RBAC permission for the `.item budget` debug command (Phase 2 of the
-- percentage-allocation itemization system, see docs/itemization-changes.md
-- §6.4). Custom permission id, per RBAC.h's own "custom permissions 1000+"
-- convention -- keeps this out of upstream's numbered range.
--

DELETE FROM `rbac_permissions` WHERE `id` = 1000;
INSERT INTO `rbac_permissions` (`id`, `name`) VALUES
(1000, 'Command: item budget');

DELETE FROM `rbac_linked_permissions` WHERE `id` = 196 AND `linkedId` = 1000;
INSERT INTO `rbac_linked_permissions` (`id`, `linkedId`) VALUES
(196, 1000);
