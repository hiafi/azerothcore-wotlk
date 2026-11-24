-- Scarlet Monastery build WP-L-2: the gameobject loot of section 4, the one list apps/dbc-tools' loot DSL cannot
-- declare (it writes creature loot only; the creature lists, the Zealot's tokens, the hard mode lists and the cut
-- stock rows of Crell, Halden, Herod, Thorne, Mograine, Whitemane and Fairbanks are
-- source/items/scarlet_monastery_loot.py, wave 2 section).
-- .agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.6 and s7 #20 A; docs/dungeons/
-- scarlet-monastery-rework.md "Boss lists" (The Last Stand).

-- The Chest of the Last Stand (GO 301330 on normal, 301331 on heroic; rev_last_stand_scarlet_monastery.sql made the
-- templates and Data1 = the loot entry; the Last Stand script summons the chest of the map's difficulty when Mograine
-- falls at 1%, no corpse). The approved list, one item per kill (group 1, equal chance): Aegis of the Scarlet
-- Commander, Mograine's Might, Gauntlets of Divinity, Captain's Legguards and Libram of the Last Stand, at the Normal
-- tier on 301330 (item level 44: the three stock entries 7726 / 7723 / 7724 and the two new ones) and the Heroic tier
-- on 301331. The two chests are two loot entries, so every row is LootMode 1 (no hard mode for this encounter). The
-- chest drops no cloth (the placeholder rows of the D13 rev go): Mograine's own table keeps the Silk Cloth and the
-- Heart of Zeal for his real death in Whitemane's fight, and the chest carries no gold (gameobject_template_addon
-- 0 / 0; Mograine's gold drops at that second death).
DELETE FROM `gameobject_loot_template` WHERE `Entry` IN (301330, 301331);
INSERT INTO `gameobject_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, `LootMode`,
    `GroupId`, `MinCount`, `MaxCount`, `Comment`) VALUES
(301330, 7726, 0, 0, 0, 1, 1, 1, 1, 'Chest of the Last Stand - Aegis of the Scarlet Commander (Normal)'),
(301330, 7723, 0, 0, 0, 1, 1, 1, 1, 'Chest of the Last Stand - Mograine''s Might (Normal)'),
(301330, 7724, 0, 0, 0, 1, 1, 1, 1, 'Chest of the Last Stand - Gauntlets of Divinity (Normal)'),
(301330, 74131, 0, 0, 0, 1, 1, 1, 1, 'Chest of the Last Stand - Captain''s Legguards (Normal)'),
(301330, 74136, 0, 0, 0, 1, 1, 1, 1, 'Chest of the Last Stand - Libram of the Last Stand (Normal)'),
(301331, 74119, 0, 0, 0, 1, 1, 1, 1, 'Chest of the Last Stand (heroic) - Aegis of the Scarlet Commander (Heroic)'),
(301331, 74123, 0, 0, 0, 1, 1, 1, 1, 'Chest of the Last Stand (heroic) - Mograine''s Might (Heroic)'),
(301331, 74127, 0, 0, 0, 1, 1, 1, 1, 'Chest of the Last Stand (heroic) - Gauntlets of Divinity (Heroic)'),
(301331, 74132, 0, 0, 0, 1, 1, 1, 1, 'Chest of the Last Stand (heroic) - Captain''s Legguards (Heroic)'),
(301331, 74137, 0, 0, 0, 1, 1, 1, 1, 'Chest of the Last Stand (heroic) - Libram of the Last Stand (Heroic)');
