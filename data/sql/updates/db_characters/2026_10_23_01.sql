-- DB update 2026_10_23_00 -> 2026_10_23_01
-- hunter-rework T2: ammo is no longer used (46699 also clears it at login; this tidies offline characters, §0.17)
UPDATE `characters` SET `ammoId` = 0 WHERE `ammoId` <> 0;
