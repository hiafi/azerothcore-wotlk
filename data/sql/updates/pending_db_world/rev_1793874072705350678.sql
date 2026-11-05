-- progression-slim PS3 D1: disables cleanup for the mod-progression cutover.
-- Source of the row lists: mod-progression 8c765a1 src/phase_00/sql/phase_00-disables.sql; every list below was
-- compared with the live table (read-only SELECT 2026-11-05): types 2, 3, 5 and 9 match phase 0 exactly (57/13/7/58
-- rows, same flags), so deleting them removes only phase 0's rows and no stock row.
-- INTENDED DELETEs: these statements delete rows (codestyle-sql flags DELETE without INSERT; that is deliberate).
-- DisableMgr::AddDisable never overwrites a DB row, so every row the content-gate module now owns must leave the
-- table in the same restart that removes mod-progression (PLAN 3.4 "Ownership").
-- Not touched here: stock rows, dbc-tools' sourceType 8 (lfg_exclude), types 0/6/7, the TBC/WotLK quest rows
-- (11009, 11130, 11481 and their tier peers) and loot rows 21877, 27859, 27860, 31952, which stay until their tier
-- bundles are written.

-- sourceType 2 (map): the module owns every instance map; closed unless ContentGate.Open.Instances lists it.
-- 249 Onyxia's Lair; 269 The Black Morass; 309 Zul'Gurub; 349 Maraudon; 409 Molten Core; 429 Dire Maul; 469 Blackwing
-- Lair; 509 Ruins of Ahn'Qiraj; 531 Temple of Ahn'Qiraj; 532 Karazhan; 533 Naxxramas; 534 Hyjal Summit; 540 The
-- Shattered Halls; 542 The Blood Furnace; 543 Hellfire Ramparts; 544 Magtheridon's Lair; 545 The Steamvault; 546 The
-- Underbog; 547 The Slave Pens; 548 Serpentshrine Cavern; 550 Tempest Keep; 552 The Arcatraz; 553 The Botanica; 554 The
-- Mechanar; 555 Shadow Labyrinth; 556 Sethekk Halls; 557 Mana-Tombs; 558 Auchenai Crypts; 560 Old Hillsbrad Foothills;
-- 564 Black Temple; 565 Gruul's Lair; 568 Zul'Aman; 574 Utgarde Keep; 575 Utgarde Pinnacle; 576 The Nexus; 578 The
-- Oculus; 580 Sunwell Plateau; 585 Magister's Terrace; 595 The Culling of Stratholme; 599 Halls of Stone; 600
-- Drak'Tharon Keep; 601 Azjol-Nerub; 602 Halls of Lightning; 603 Ulduar; 604 Gundrak; 608 Violet Hold; 615 The Obsidian
-- Sanctum; 616 The Eye of Eternity; 619 Ahn'kahet: The Old Kingdom; 624 Vault of Archavon; 631 Icecrown Citadel; 632
-- The Forge of Souls; 649 Trial of The Crusader; 650 Trial of the Champion; 658 Pit of Saron; 668 Halls of Reflection;
-- 724 The Ruby Sanctum
DELETE FROM `disables` WHERE `sourceType` = 2 AND `entry` IN (
    249, 269, 309, 349, 409, 429, 469, 509, 531, 532, 533, 534, 540, 542, 543, 544, 545, 546, 547, 548, 550, 552, 553,
    554, 555, 556, 557, 558, 560, 564, 565, 568, 574, 575, 576, 578, 580, 585, 595, 599, 600, 601, 602, 603, 604, 608,
    615, 616, 619, 624, 631, 632, 649, 650, 658, 668, 724
);

-- sourceType 3 (battleground and arena): the module owns them (ContentGate.Open.Battlegrounds).
-- 1 Alterac Valley; 2 Warsong Gulch; 3 Arathi Basin; 4 Ring of Trials; 5 Circle of Blood; 6 All Arenas; 7 Eye of the
-- Storm; 8 Ruins of Lordaeron; 9 Strand of the Ancients; 10 Dalaran Arena; 11 Ring of Valor; 30 Isle of Conquest; 32
-- Random Battleground
DELETE FROM `disables` WHERE `sourceType` = 3 AND `entry` IN (
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 30, 32
);

-- sourceType 5 (outdoor PvP): the module owns them (ContentGate.Open.OutdoorPvP).
-- 1 Hellfire Peninsula; 2 Nagrand; 3 Terokkar Forest; 4 Zangarmarsh; 5 Silithus; 6 Eastern Plaguelands; 7 Grizzly Hills
DELETE FROM `disables` WHERE `sourceType` = 5 AND `entry` IN (
    1, 2, 3, 4, 5, 6, 7
);

-- sourceType 9 (game event): the module owns the gated holidays (ContentGate.Closed.Events), and the
-- vanilla ones (DMF, STV Fishing, AV/WSG/AB Call to Arms) run on their stock schedule from day one.
-- 3 Darkmoon Faire (Terokkar Forest); 4 Darkmoon Faire (Elwynn Forest); 5 Darkmoon Faire (Mulgore); 14 Stranglethorn
-- Fishing Extravaganza Announce; 15 Stranglethorn Fishing Extravaganza Fishing Pools; 18 Call to Arms: Alterac Valley!;
-- 19 Call to Arms: Warsong Gulch!; 20 Call to Arms: Arathi Basin!; 21 Call to Arms: Eye of the Storm!; 23 Darkmoon
-- Faire Building (Elwynn Forest, 0, XXX); 24 Brewfest; 26 Pilgrim's Bounty; 34 Brew of the Month October; 35 Brew of
-- the Month November; 36 Brew of the Month December; 37 Brew of the Month January; 38 Brew of the Month February; 39
-- Brew of the Month March; 40 Brew of the Month April; 41 Brew of the Month May; 42 Brew of the Month June; 43 Brew of
-- the Month July; 44 Brew of the Month August; 45 Brew of the Month September; 50 Pirates' Day; 51 Day of the Dead; 53
-- Call to Arms: Strand of the Ancients!; 54 Call to Arms: Isle of Conquest!; 55 Arena Season 3; 56 Arena Season 4; 57
-- Arena Season 5; 58 Arena Season 6; 59 Arena Season 7; 60 Arena Season 8; 61 Zalazane's Fall; 62 Stranglethorn Fishing
-- Extravaganza - The Crew; 63 Kalu'ak Fishing Derby Turn-ins; 64 Kalu'ak Fishing Derby Fishing Pools; 70 Brewfest
-- Building (Iron Forge, 0, XXX); 71 Darkmoon Faire Building (Mulgore, 0, XXX); 76 Arena Season 2; 77 Darkmoon Faire
-- Building (Terokkar Forest, 0, XXX); 90 Stranglethorn Fishing Extravaganza - Turn-ins; 101 Sun's Reach Reclamation
-- Phase 1; 102 Sun's Reach Reclamation Phase 2 Only; 103 Sun's Reach Reclamation Phase 2 Permanent; 104 Sun's Reach
-- Reclamation Phase No Portal; 105 Sun's Reach Reclamation Phase Portal; 106 Sun's Reach Reclamation Phase 3 Only; 107
-- Sun's Reach Reclamation Phase 3 Permanent; 108 Sun's Reach Reclamation Phase No Anvil; 109 Sun's Reach Reclamation
-- Phase Anvil; 110 Sun's Reach Reclamation Phase 4; 111 Sun's Reach Reclamation Phase No Monument; 112 Sun's Reach
-- Reclamation Phase Monument; 113 Sun's Reach Reclamation Phase No Alchemy Lab; 114 Sun's Reach Reclamation Phase
-- Alchemy Lab; 115 Sun's Reach Reclamation Phase K'iru
DELETE FROM `disables` WHERE `sourceType` = 9 AND `entry` IN (
    3, 4, 5, 14, 15, 18, 19, 20, 21, 23, 24, 26, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 50, 51, 53, 54, 55, 56,
    57, 58, 59, 60, 61, 62, 63, 64, 70, 71, 76, 77, 90, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113,
    114, 115
);

-- sourceType 4 (achievement criteria): achievements unlocked from the start (DECISIONS, PLAN 7 answer 16). The 8
-- rows are Onyxia's Lair criteria; no other phase 0 achievement row exists.
-- 12558 Onyxia's Lair (10 player); 12559 Onyxia's Lair (25 player); 12564 More Dots! (10 player); 12565 Many Whelps!
-- Handle It! (10 player); 12566 She Deep Breaths More (10 player); 12567 More Dots! (25 player); 12568 Many Whelps!
-- Handle It! (25 player); 12569 She Deep Breaths More (25 player)
DELETE FROM `disables` WHERE `sourceType` = 4 AND `entry` IN (
    12558, 12559, 12564, 12565, 12566, 12567, 12568, 12569
);

-- sourceType 1 (quest), day one: the old-world later-tier quests open with their NPCs (DECISIONS 16 cont.):
-- Inspecting the Ruins, Help for Mudsprocket, Relic of the Earthen Ring, Battle of Hillsbrad.
-- 11123 Inspecting the Ruins; 11124 Inspecting the Ruins; 11211 Help for Mudsprocket; 11215 Help Mudsprocket; 14100
-- Relic of the Earthen Ring; 14111 Relic of the Earthen Ring; 14351 Battle of Hillsbrad
DELETE FROM `disables` WHERE `sourceType` = 1 AND `entry` IN (
    11123, 11124, 11211, 11215, 14100, 14111, 14351
);

-- sourceType 1 (quest), bundle members: Onyxia 4903; Maraudon 7028-7070; Dire Maul 7441/7492/7494; ZG 8181;
-- AQ 8286/8556-8558/8689-8712/8800/9023/9248; the Dungeon Set 2 device chain 8922/8923 (open on day one,
-- PLAN 7 #8). Their gating moves to content_gate_bundle_disable (WP-D2 seeds the members; a closed bundle
-- applies them as disables, an open one leaves them out). Must ship together with that seed.
-- 4903 Warlord's Command; 7028 Twisted Evils; 7029 Vyletongue Corruption; 7041 Vyletongue Corruption; 7064 Corruption
-- of Earth and Seed; 7065 Corruption of Earth and Seed; 7067 The Pariah's Instructions; 7068 Shadowshard Fragments;
-- 7070 Shadowshard Fragments; 7441 Pusillin and the Elder Azj'Tordin; 7492 Camp Mojache; 7494 Feathermoon Stronghold;
-- 8181 Confront Yeh'kinya; 8800 Cenarion Battlegear; 8286 What Tomorrow Brings; 8556 Signet of Unyielding Strength;
-- 8557 Drape of Unyielding Strength; 8558 Sickle of Unyielding Strength; 8689 Shroud of Infinite Wisdom; 8690 Cloak of
-- the Gathering Storm; 8691 Drape of Vaulted Secrets; 8692 Cloak of Unending Life; 8693 Cloak of Veiled Shadows; 8694
-- Shroud of Unspoken Names; 8695 Cape of Eternal Justice; 8696 Cloak of the Unseen Path; 8697 Ring of Infinite Wisdom;
-- 8698 Ring of the Gathering Storm; 8699 Band of Vaulted Secrets; 8700 Band of Unending Life; 8701 Band of Veiled
-- Shadows; 8702 Ring of Unspoken Names; 8703 Ring of Eternal Justice; 8704 Signet of the Unseen Path; 8705 Gavel of
-- Infinite Wisdom; 8706 Hammer of the Gathering Storm; 8707 Blade of Vaulted Secrets; 8708 Mace of Unending Life; 8709
-- Dagger of Veiled Shadows; 8710 Kris of Unspoken Names; 8711 Blade of Eternal Justice; 8712 Scythe of the Unseen Path;
-- 9023 The Perfect Poison; 9248 A Humble Offering; 8922 A Supernatural Device; 8923 A Supernatural Device
DELETE FROM `disables` WHERE `sourceType` = 1 AND `entry` IN (
    4903, 7028, 7029, 7041, 7064, 7065, 7067, 7068, 7070, 7441, 7492, 7494, 8181, 8800, 8286, 8556, 8557, 8558, 8689,
    8690, 8691, 8692, 8693, 8694, 8695, 8696, 8697, 8698, 8699, 8700, 8701, 8702, 8703, 8704, 8705, 8706, 8707, 8708,
    8709, 8710, 8711, 8712, 9023, 9248, 8922, 8923
);

-- sourceType 10 (loot): the six Blackwing Lair loot disables become blackwing_lair bundle members (WP-D2).
-- 18563 Bindings of the Windseeker; 18564 Bindings of the Windseeker; 18646 The Eye of Divinity; 18665 The Eye of
-- Shadow; 18705 Mature Black Dragon Sinew; 18987 Blackhand's Command
DELETE FROM `disables` WHERE `sourceType` = 10 AND `entry` IN (
    18563, 18564, 18646, 18665, 18705, 18987
);
