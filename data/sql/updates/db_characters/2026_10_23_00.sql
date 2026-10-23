-- DB update 2026_10_05_03 -> 2026_10_23_00
--
-- pet-stale-ranks Part B: drop superseded pet spell ranks from existing pets.
-- The single-rank conversion collapsed each rank chain into its rank-1 survivor and removed its spell_ranks rows,
-- but stock SkillLineAbility still lists the old ranks for pet level-up (SpellMgr::LoadPetLevelupSpellMap), so
-- pets learned every rank as a separate spell (Imp: Firebolt 3110 + 7799 ... 47964). The world-side
-- skilllineability_dbc overrides stop new learning; this cleans up what pets already know.
-- Ids: the non-survivor members of base spell_ranks chains whose survivor is a dbc-tools "single-rank bootstrap"
-- spell, limited to ranks with a stock SkillLineAbility row (AcquireMethod 2) on a CreatureFamily skill line.
DROP TEMPORARY TABLE IF EXISTS `pet_stale_rank`;
CREATE TEMPORARY TABLE `pet_stale_rank` (
    `stale` INT UNSIGNED NOT NULL,
    `survivor` INT UNSIGNED NOT NULL,
    PRIMARY KEY (`stale`)
) ENGINE=InnoDB;
DELETE FROM `pet_stale_rank`;
INSERT INTO `pet_stale_rank` (`stale`, `survivor`) VALUES
-- Anguish 33698 (Felguard)
(33699, 33698),
(33700, 33698),
(47993, 33698),
-- Blood Pact 6307 (Imp)
(7804, 6307),
(7805, 6307),
(11766, 6307),
(11767, 6307),
(27268, 6307),
(47982, 6307),
-- Cleave 30213 (Felguard)
(30219, 30213),
(30223, 30213),
(47994, 30213),
-- Consume Shadows 17767 (Voidwalker)
(17850, 17767),
(17851, 17767),
(17852, 17767),
(17853, 17767),
(17854, 17767),
(27272, 17767),
(47987, 17767),
(47988, 17767),
-- Devour Magic 19505 (Felhunter)
(19731, 19505),
(19734, 19505),
(19736, 19505),
(27276, 19505),
(27277, 19505),
(48011, 19505),
-- Fel Intelligence 54424 (Felhunter)
(57564, 54424),
(57565, 54424),
(57566, 54424),
(57567, 54424),
-- Fire Shield 2947 (Imp)
(8316, 2947),
(8317, 2947),
(11770, 2947),
(11771, 2947),
(27269, 2947),
(47983, 2947),
-- Firebolt 3110 (Imp)
(7799, 3110),
(7800, 3110),
(7801, 3110),
(7802, 3110),
(11762, 3110),
(11763, 3110),
(27267, 3110),
(47964, 3110),
-- Intercept 30151 (Felguard)
(30194, 30151),
(30198, 30151),
(47996, 30151),
-- Lash of Pain 7814 (Succubus)
(7815, 7814),
(7816, 7814),
(11778, 7814),
(11779, 7814),
(11780, 7814),
(27274, 7814),
(47991, 7814),
(47992, 7814),
-- Sacrifice 7812 (Voidwalker)
(19438, 7812),
(19440, 7812),
(19441, 7812),
(19442, 7812),
(19443, 7812),
(27273, 7812),
(47985, 7812),
(47986, 7812),
-- Shadow Bite 54049 (Felhunter)
(54050, 54049),
(54051, 54049),
(54052, 54049),
(54053, 54049),
-- Soothing Kiss 6360 (Succubus)
(7813, 6360),
(11784, 6360),
(11785, 6360),
(27275, 6360),
-- Spell Lock 19244 (Felhunter)
(19647, 19244),
-- Suffering 17735 (Voidwalker)
(17750, 17735),
(17751, 17735),
(17752, 17735),
(27271, 17735),
(33701, 17735),
(47989, 17735),
(47990, 17735),
-- Torment 3716 (Voidwalker)
(7809, 3716),
(7810, 3716),
(7811, 3716),
(11774, 3716),
(11775, 3716),
(27270, 3716),
(47984, 3716),
-- Acid Spit 55749 (Worm)
(55750, 55749),
(55751, 55749),
(55752, 55749),
(55753, 55749),
(55754, 55749),
-- Bad Attitude 50433 (Crocolisk)
(52395, 50433),
(52396, 50433),
(52397, 50433),
(52398, 50433),
(52399, 50433),
-- Bite 17253 (18 hunter families)
(17255, 17253),
(17256, 17253),
(17257, 17253),
(17258, 17253),
(17259, 17253),
(17260, 17253),
(17261, 17253),
(27050, 17253),
(52473, 17253),
(52474, 17253),
-- Claw 16827 (9 hunter families)
(16828, 16827),
(16829, 16827),
(16830, 16827),
(16831, 16827),
(16832, 16827),
(3010, 16827),
(3009, 16827),
(27049, 16827),
(52471, 16827),
(52472, 16827),
-- Demoralizing Screech 24423 (Carrion Bird)
(24577, 24423),
(24578, 24423),
(24579, 24423),
(27051, 24423),
(55487, 24423),
-- Fire Breath 34889 (Dragonhawk)
(35323, 34889),
(55482, 34889),
(55483, 34889),
(55484, 34889),
(55485, 34889),
-- Froststorm Breath 54644 (Chimaera)
(55488, 54644),
(55489, 54644),
(55490, 54644),
(55491, 54644),
(55492, 54644),
-- Furious Howl 24604 (Wolf)
(64491, 24604),
(64492, 24604),
(64493, 24604),
(64494, 24604),
(64495, 24604),
-- Gore 35290 (Boar)
(35291, 35290),
(35292, 35290),
(35293, 35290),
(35294, 35290),
(35295, 35290),
-- Growl 2649 (32 hunter families)
(14916, 2649),
(14917, 2649),
(14918, 2649),
(14919, 2649),
(14920, 2649),
(14921, 2649),
(27047, 2649),
(61676, 2649),
-- Lava Breath 58604 (Core Hound)
(58607, 58604),
(58608, 58604),
(58609, 58604),
(58610, 58604),
(58611, 58604),
-- Lightning Breath 24844 (Wind Serpent)
(25008, 24844),
(25009, 24844),
(25010, 24844),
(25011, 24844),
(25012, 24844),
-- Monstrous Bite 54680 (Devilsaur)
(55495, 54680),
(55496, 54680),
(55497, 54680),
(55498, 54680),
(55499, 54680),
-- Nether Shock 50479 (Nether Ray)
(53584, 50479),
(53586, 50479),
(53587, 50479),
(53588, 50479),
(53589, 50479),
-- Pin 50245 (Crab)
(53544, 50245),
(53545, 50245),
(53546, 50245),
(53547, 50245),
(53548, 50245),
-- Poison Spit 35387 (Serpent)
(35389, 35387),
(35392, 35387),
(55555, 35387),
(55556, 35387),
(55557, 35387),
-- Prowl 24450 (Cat, Spirit Beast)
(24452, 24450),
(24453, 24450),
-- Rake 59881 (Cat)
(59882, 59881),
(59883, 59881),
(59884, 59881),
(59885, 59881),
(59886, 59881),
-- Ravage 50518 (Ravager)
(53558, 50518),
(53559, 50518),
(53560, 50518),
(53561, 50518),
(53562, 50518),
-- Savage Rend 50498 (Raptor)
(53578, 50498),
(53579, 50498),
(53580, 50498),
(53581, 50498),
(53582, 50498),
-- Scorpid Poison 24640 (Scorpid)
(24583, 24640),
(24586, 24640),
(24587, 24640),
(27060, 24640),
(55728, 24640),
-- Serenity Dust 50318 (Moth)
(52012, 50318),
(52013, 50318),
(52014, 50318),
(52015, 50318),
(52016, 50318),
-- Smack 49966 (5 hunter families)
(49967, 49966),
(49968, 49966),
(49969, 49966),
(49970, 49966),
(49971, 49966),
(49972, 49966),
(49973, 49966),
(49974, 49966),
(52475, 49966),
(52476, 49966),
-- Snatch 50541 (Bird of Prey)
(53537, 50541),
(53538, 50541),
(53540, 50541),
(53542, 50541),
(53543, 50541),
-- Sonic Blast 50519 (Bat)
(53564, 50519),
(53565, 50519),
(53566, 50519),
(53567, 50519),
(53568, 50519),
-- Spirit Strike 61193 (Spirit Beast)
(61194, 61193),
(61195, 61193),
(61196, 61193),
(61197, 61193),
(61198, 61193),
-- Spore Cloud 50274 (Sporebat)
(53593, 50274),
(53594, 50274),
(53596, 50274),
(53597, 50274),
(53598, 50274),
-- Stampede 57386 (Rhino)
(57389, 57386),
(57390, 57386),
(57391, 57386),
(57392, 57386),
(57393, 57386),
-- Sting 56626 (Wasp)
(56627, 56626),
(56628, 56626),
(56629, 56626),
(56630, 56626),
(56631, 56626),
-- Swipe 50256 (Bear)
(53526, 50256),
(53528, 50256),
(53529, 50256),
(53532, 50256),
(53533, 50256),
-- Tendon Rip 50271 (Hyena)
(53571, 50271),
(53572, 50271),
(53573, 50271),
(53574, 50271),
(53575, 50271),
-- Venom Web Spray 54706 (Silithid)
(55505, 54706),
(55506, 54706),
(55507, 54706),
(55508, 54706),
(55509, 54706);

-- The survivor rows pets already have, before the merge below rewrites them: the abdata step needs a survivor's own
-- autocast state when it is not on the bar.
DROP TEMPORARY TABLE IF EXISTS `pet_stale_known`;
CREATE TEMPORARY TABLE `pet_stale_known` (
    `guid` INT UNSIGNED NOT NULL,
    `spell` INT UNSIGNED NOT NULL,
    `active` TINYINT UNSIGNED NOT NULL,
    PRIMARY KEY (`guid`, `spell`)
) ENGINE=InnoDB;
DELETE FROM `pet_stale_known`;
INSERT INTO `pet_stale_known` (`guid`, `spell`, `active`)
SELECT `ps`.`guid`, `ps`.`spell`, `ps`.`active`
FROM `pet_spell` AS `ps`
WHERE `ps`.`spell` IN (SELECT `survivor` FROM `pet_stale_rank`);

-- pet_spell: one survivor row per pet that knows any rank of a chain. Autocast (active 193) on any rank carries over
-- to the survivor; otherwise it keeps the survivor's own state (129 if only stale ranks were known).
DROP TEMPORARY TABLE IF EXISTS `pet_stale_spell`;
CREATE TEMPORARY TABLE `pet_stale_spell` (
    `guid` INT UNSIGNED NOT NULL,
    `spell` INT UNSIGNED NOT NULL,
    `active` TINYINT UNSIGNED NOT NULL,
    PRIMARY KEY (`guid`, `spell`)
) ENGINE=InnoDB;
DELETE FROM `pet_stale_spell`;
INSERT INTO `pet_stale_spell` (`guid`, `spell`, `active`)
SELECT
    `ps`.`guid`,
    COALESCE(`m`.`survivor`, `ps`.`spell`),
    IF(MAX(`ps`.`active` = 193) = 1, 193, MAX(`ps`.`active`))
FROM `pet_spell` AS `ps`
LEFT JOIN `pet_stale_rank` AS `m` ON `m`.`stale` = `ps`.`spell`
GROUP BY 1, 2
HAVING COUNT(`m`.`stale`) > 0;
DELETE FROM `pet_spell` WHERE (`guid`, `spell`) IN (SELECT `guid`, `spell` FROM `pet_stale_spell`);
INSERT INTO `pet_spell` (`guid`, `spell`, `active`) SELECT `guid`, `spell`, `active` FROM `pet_stale_spell`;
DELETE FROM `pet_spell` WHERE `spell` IN (SELECT `stale` FROM `pet_stale_rank`);

-- character_pet.abdata: ten "type action" pairs (Pet::GenerateActionBarData). On load, CharmInfo::LoadPetActionBar
-- keeps a slot whose spell still exists in the store, CharmInfo::AddSpellToActionBar can no longer match the
-- survivor to a stale slot (no chain), and Pet::CleanupActionBar then blanks the stale slot and re-applies autocast
-- from each slot's type. Left alone, the survivor misses a full bar and autocast set on a stale slot is lost.
-- Per pet and chain: the survivor's own slot (else the first stale slot) holds the survivor, autocast if any of the
-- chain's slots had it, or if the survivor was off the bar with autocast in pet_spell (its own state before the
-- merge); the chain's other slots are blanked to "1 0", what CleanupActionBar writes.
DROP TEMPORARY TABLE IF EXISTS `pet_stale_slot`;
CREATE TEMPORARY TABLE `pet_stale_slot` (
    `pet` INT UNSIGNED NOT NULL,
    `idx` TINYINT UNSIGNED NOT NULL,
    `type` INT UNSIGNED NOT NULL,
    `action` INT UNSIGNED NOT NULL,
    PRIMARY KEY (`pet`, `idx`)
) ENGINE=InnoDB;
DELETE FROM `pet_stale_slot`;
INSERT INTO `pet_stale_slot` (`pet`, `idx`, `type`, `action`)
SELECT
    `cp`.`id`,
    `n`.`idx`,
    CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(TRIM(`cp`.`abdata`), ' ', 2 * `n`.`idx` + 1), ' ', -1) AS UNSIGNED),
    CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(TRIM(`cp`.`abdata`), ' ', 2 * `n`.`idx` + 2), ' ', -1) AS UNSIGNED)
FROM `character_pet` AS `cp`
CROSS JOIN (
    SELECT 0 AS `idx` UNION ALL SELECT 1 UNION ALL SELECT 2 UNION ALL SELECT 3 UNION ALL SELECT 4
    UNION ALL SELECT 5 UNION ALL SELECT 6 UNION ALL SELECT 7 UNION ALL SELECT 8 UNION ALL SELECT 9
) AS `n`
WHERE
    `cp`.`abdata` REGEXP '^[0-9]+( [0-9]+){19} ?$';
DROP TEMPORARY TABLE IF EXISTS `pet_stale_bar`;
CREATE TEMPORARY TABLE `pet_stale_bar` (
    `pet` INT UNSIGNED NOT NULL,
    `survivor` INT UNSIGNED NOT NULL,
    `keep_idx` TINYINT UNSIGNED NOT NULL,
    `autocast` TINYINT UNSIGNED NOT NULL,
    `on_bar` TINYINT UNSIGNED NOT NULL,
    PRIMARY KEY (`pet`, `survivor`)
) ENGINE=InnoDB;
DELETE FROM `pet_stale_bar`;
INSERT INTO `pet_stale_bar` (`pet`, `survivor`, `keep_idx`, `autocast`, `on_bar`)
SELECT
    `s`.`pet`,
    COALESCE(`m`.`survivor`, `s`.`action`),
    COALESCE(MIN(IF(`m`.`stale` IS NULL, `s`.`idx`, NULL)), MIN(`s`.`idx`)),
    MAX(`s`.`type` = 193),
    MAX(`m`.`stale` IS NULL)
FROM `pet_stale_slot` AS `s`
LEFT JOIN `pet_stale_rank` AS `m` ON `m`.`stale` = `s`.`action`
WHERE `s`.`type` IN (1, 129, 193) AND `s`.`action` <> 0
GROUP BY 1, 2
HAVING COUNT(`m`.`stale`) > 0;
UPDATE `pet_stale_bar` AS `b`
INNER JOIN `pet_stale_known` AS `k` ON `k`.`guid` = `b`.`pet` AND `k`.`spell` = `b`.`survivor`
SET `b`.`autocast` = 1 WHERE `b`.`on_bar` = 0 AND `k`.`active` = 193;
UPDATE `pet_stale_slot` AS `s`
LEFT JOIN `pet_stale_rank` AS `m` ON `m`.`stale` = `s`.`action`
INNER JOIN `pet_stale_bar` AS `b` ON `b`.`pet` = `s`.`pet` AND `s`.`type` IN (1, 129, 193)
    AND `b`.`survivor` = COALESCE(`m`.`survivor`, `s`.`action`)
SET `s`.`type` = IF(`s`.`idx` = `b`.`keep_idx`, IF(`b`.`autocast` = 1, 193, `s`.`type`), 1);
UPDATE `pet_stale_slot` AS `s`
LEFT JOIN `pet_stale_rank` AS `m` ON `m`.`stale` = `s`.`action`
INNER JOIN `pet_stale_bar` AS `b` ON `b`.`pet` = `s`.`pet` AND `s`.`type` IN (1, 129, 193)
    AND `b`.`survivor` = COALESCE(`m`.`survivor`, `s`.`action`)
SET `s`.`action` = IF(`s`.`idx` = `b`.`keep_idx`, `b`.`survivor`, 0);
UPDATE `character_pet` AS `cp`
INNER JOIN (
    SELECT
        `pet`,
        CONCAT(GROUP_CONCAT(CONCAT(`type`, ' ', `action`)
            ORDER BY `idx`
            SEPARATOR ' '), ' ') AS `abdata`
    FROM `pet_stale_slot`
    GROUP BY `pet`
) AS `n` ON `n`.`pet` = `cp`.`id`
SET `cp`.`abdata` = `n`.`abdata` WHERE `cp`.`id` IN (SELECT `pet` FROM `pet_stale_bar`);

-- Saved auras and cooldowns of the stale ranks (a Fire Shield 11771 buff would reload at stock values).
DELETE FROM `pet_aura` WHERE `spell` IN (SELECT `stale` FROM `pet_stale_rank`);
DELETE FROM `pet_spell_cooldown` WHERE `spell` IN (SELECT `stale` FROM `pet_stale_rank`);

DROP TEMPORARY TABLE IF EXISTS `pet_stale_bar`;
DROP TEMPORARY TABLE IF EXISTS `pet_stale_slot`;
DROP TEMPORARY TABLE IF EXISTS `pet_stale_spell`;
DROP TEMPORARY TABLE IF EXISTS `pet_stale_known`;
DROP TEMPORARY TABLE IF EXISTS `pet_stale_rank`;
