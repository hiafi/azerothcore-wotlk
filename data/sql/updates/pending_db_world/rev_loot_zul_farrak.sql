-- Zul'Farrak build WP-L-1: the loot the DSL cannot declare (apps/dbc-tools' loot DSL writes creature loot only; the
-- creature lists, the rares' pool, the hard mode list and the cut stock rows are
-- apps/dbc-tools/source/items/zul_farrak_loot.py). Handoff section 7 #19 A and #49 A; docs/dungeons/
-- zul-farrak-rework.md "Loot list" (Sergeant Bly's crew, one list).

-- The crew's stash chest (GO 301360 on normal, 301361 on heroic; WP-D5's rev makes the templates with Data1 = the loot
-- entry = the GO's own id, and the crew fight spawns the chest of the map's difficulty when the fight ends, on the
-- betrayal path and on Bly's Test). It holds, and the five bodies carry nothing:
--   - group 1: the crew's list, one item per kill, equal chance, at the Normal tier on 301360 (the three stock entries
--     2040 / 9480 / 9483 and the six new items) and the Heroic tier on 301361;
--   - group 0: Bly's Divino-matic Rod (quest 2768, QuestRequired, 100%) and the members' own small tables, one row per
--     item: the chance of at least one of the members' stock rows (1 - the product of the misses), the largest count.
--     Gutwrencher, Witch Doctor's Cane, Bloodletter Scalpel and Blackmetal Cape (0.02% to 0.18% rows of Bly, Raven, Oro
--     and Murta) are on other bosses' lists now and are not here;
--   - group 2: the members' world level pools (references 24036 to 24081) at the sum of the members' chances; the group
--     yields at most one of them, as each member's own group did.
-- gameobject_loot_template is keyed (Entry, Item): every item appears once per chest (BRD LESSONS section 5).
DELETE FROM `gameobject_loot_template` WHERE `Entry` IN (301360, 301361);
INSERT INTO `gameobject_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, `LootMode`,
    `GroupId`, `MinCount`, `MaxCount`, `Comment`) VALUES
(301360, 2040, 0, 0, 0, 1, 1, 1, 1, 'Treasure Sack - Troll Protector (Normal)'),
(301360, 9480, 0, 0, 0, 1, 1, 1, 1, 'Treasure Sack - Eyegouger (Normal)'),
(301360, 9483, 0, 0, 0, 1, 1, 1, 1, 'Treasure Sack - Flaming Incinerator (Normal)'),
(301360, 74629, 0, 0, 0, 1, 1, 1, 1, 'Treasure Sack - Sergeant''s Dented Breastplate (Normal)'),
(301360, 74634, 0, 0, 0, 1, 1, 1, 1, 'Treasure Sack - Raven''s Soft-step Gloves (Normal)'),
(301360, 74639, 0, 0, 0, 1, 1, 1, 1, 'Treasure Sack - Murta''s Mending Wraps (Normal)'),
(301360, 74644, 0, 0, 0, 1, 1, 1, 1, 'Treasure Sack - Blastfuse Bandolier (Normal)'),
(301360, 74649, 0, 0, 0, 1, 1, 1, 1, 'Treasure Sack - Ill-gotten Coin (Normal)'),
(301360, 74654, 0, 0, 0, 1, 1, 1, 1, 'Treasure Sack - Weegli''s Blunderbuss (Normal)'),
(301360, 1645, 0, 12.706, 0, 1, 0, 1, 1, 'Treasure Sack - Moonberry Juice'),
(301360, 1685, 0, 0.1, 0, 1, 0, 1, 1, 'Treasure Sack - Troll-hide Bag'),
(301360, 3357, 0, 66.7, 0, 1, 0, 1, 1, 'Treasure Sack - Liferoot'),
(301360, 3832, 0, 0.06, 0, 1, 0, 1, 1, 'Treasure Sack - Recipe: Elixir of Detect Lesser Invisibility'),
(301360, 3864, 0, 0.373, 0, 1, 0, 1, 1, 'Treasure Sack - Citrine'),
(301360, 3914, 0, 0.4393, 0, 1, 0, 1, 1, 'Treasure Sack - Journeyman''s Backpack'),
(301360, 3927, 0, 8.1974, 0, 1, 0, 1, 1, 'Treasure Sack - Fine Aged Cheddar'),
(301360, 3928, 0, 4.9244, 0, 1, 0, 1, 1, 'Treasure Sack - Superior Healing Potion'),
(301360, 4306, 0, 40.813, 0, 1, 0, 1, 4, 'Treasure Sack - Silk Cloth'),
(301360, 4338, 0, 52.6458, 0, 1, 0, 1, 4, 'Treasure Sack - Mageweave Cloth'),
(301360, 4417, 0, 0.06, 0, 1, 0, 1, 1, 'Treasure Sack - Schematic: Large Seaforium Charge'),
(301360, 4419, 0, 1.3338, 0, 1, 0, 1, 1, 'Treasure Sack - Scroll of Intellect III'),
(301360, 4421, 0, 1.6708, 0, 1, 0, 1, 1, 'Treasure Sack - Scroll of Protection III'),
(301360, 4422, 0, 0.7778, 0, 1, 0, 1, 1, 'Treasure Sack - Scroll of Stamina III'),
(301360, 4424, 0, 1.9065, 0, 1, 0, 1, 1, 'Treasure Sack - Scroll of Spirit III'),
(301360, 4599, 0, 5.8384, 0, 1, 0, 1, 1, 'Treasure Sack - Cured Ham Steak'),
(301360, 4601, 0, 6.0901, 0, 1, 0, 1, 1, 'Treasure Sack - Soft Banana Bread'),
(301360, 4637, 0, 1.7386, 0, 1, 0, 1, 1, 'Treasure Sack - Steel Lockbox'),
(301360, 6149, 0, 4.8896, 0, 1, 0, 1, 1, 'Treasure Sack - Greater Mana Potion'),
(301360, 7909, 0, 1.3143, 0, 1, 0, 1, 1, 'Treasure Sack - Aquamarine'),
(301360, 7910, 0, 0.9761, 0, 1, 0, 1, 1, 'Treasure Sack - Star Ruby'),
(301360, 7989, 0, 0.02, 0, 1, 0, 1, 1, 'Treasure Sack - Plans: Mithril Spurs'),
(301360, 8548, 0, 100, 1, 1, 0, 1, 1, 'Treasure Sack - Divino-matic Rod'),
(301360, 8623, 0, 3.0651, 0, 1, 0, 1, 1, 'Treasure Sack - OOX-17/TN Distress Beacon'),
(301360, 9242, 0, 67.1771, 0, 1, 0, 1, 1, 'Treasure Sack - Ancient Tablet'),
(301360, 9293, 0, 0.2399, 0, 1, 0, 1, 1, 'Treasure Sack - Recipe: Magic Resistance Potion'),
(301360, 9295, 0, 0.06, 0, 1, 0, 1, 1, 'Treasure Sack - Recipe: Invisibility Potion'),
(301360, 9298, 0, 0.1, 0, 1, 0, 1, 1, 'Treasure Sack - Recipe: Elixir of Giants'),
(301360, 10606, 0, 0.2199, 0, 1, 0, 1, 1, 'Treasure Sack - Schematic: Parachute Cloak'),
(301360, 24036, 24036, 20, 0, 1, 2, 1, 1, 'Treasure Sack - (ReferenceTable)'),
(301360, 24039, 24039, 4, 0, 1, 2, 1, 1, 'Treasure Sack - (ReferenceTable)'),
(301360, 24040, 24040, 2, 0, 1, 2, 1, 1, 'Treasure Sack - (ReferenceTable)'),
(301360, 24041, 24041, 4, 0, 1, 2, 1, 1, 'Treasure Sack - (ReferenceTable)'),
(301360, 24042, 24042, 2, 0, 1, 2, 1, 1, 'Treasure Sack - (ReferenceTable)'),
(301360, 24043, 24043, 4, 0, 1, 2, 1, 1, 'Treasure Sack - (ReferenceTable)'),
(301360, 24044, 24044, 1, 0, 1, 2, 1, 1, 'Treasure Sack - (ReferenceTable)'),
(301360, 24045, 24045, 3, 0, 1, 2, 1, 1, 'Treasure Sack - (ReferenceTable)'),
(301360, 24080, 24080, 0.2, 0, 1, 2, 1, 1, 'Treasure Sack - (ReferenceTable)'),
(301360, 24081, 24081, 0.3, 0, 1, 2, 1, 1, 'Treasure Sack - (ReferenceTable)'),
(301361, 74617, 0, 0, 0, 1, 1, 1, 1, 'Treasure Sack (heroic) - Troll Protector (Heroic)'),
(301361, 74621, 0, 0, 0, 1, 1, 1, 1, 'Treasure Sack (heroic) - Eyegouger (Heroic)'),
(301361, 74625, 0, 0, 0, 1, 1, 1, 1, 'Treasure Sack (heroic) - Flaming Incinerator (Heroic)'),
(301361, 74630, 0, 0, 0, 1, 1, 1, 1, 'Treasure Sack (heroic) - Sergeant''s Dented Breastplate (Heroic)'),
(301361, 74635, 0, 0, 0, 1, 1, 1, 1, 'Treasure Sack (heroic) - Raven''s Soft-step Gloves (Heroic)'),
(301361, 74640, 0, 0, 0, 1, 1, 1, 1, 'Treasure Sack (heroic) - Murta''s Mending Wraps (Heroic)'),
(301361, 74645, 0, 0, 0, 1, 1, 1, 1, 'Treasure Sack (heroic) - Blastfuse Bandolier (Heroic)'),
(301361, 74650, 0, 0, 0, 1, 1, 1, 1, 'Treasure Sack (heroic) - Ill-gotten Coin (Heroic)'),
(301361, 74655, 0, 0, 0, 1, 1, 1, 1, 'Treasure Sack (heroic) - Weegli''s Blunderbuss (Heroic)'),
(301361, 1645, 0, 12.706, 0, 1, 0, 1, 1, 'Treasure Sack (heroic) - Moonberry Juice'),
(301361, 1685, 0, 0.1, 0, 1, 0, 1, 1, 'Treasure Sack (heroic) - Troll-hide Bag'),
(301361, 3357, 0, 66.7, 0, 1, 0, 1, 1, 'Treasure Sack (heroic) - Liferoot'),
(301361, 3832, 0, 0.06, 0, 1, 0, 1, 1, 'Treasure Sack (heroic) - Recipe: Elixir of Detect Lesser Invisibility'),
(301361, 3864, 0, 0.373, 0, 1, 0, 1, 1, 'Treasure Sack (heroic) - Citrine'),
(301361, 3914, 0, 0.4393, 0, 1, 0, 1, 1, 'Treasure Sack (heroic) - Journeyman''s Backpack'),
(301361, 3927, 0, 8.1974, 0, 1, 0, 1, 1, 'Treasure Sack (heroic) - Fine Aged Cheddar'),
(301361, 3928, 0, 4.9244, 0, 1, 0, 1, 1, 'Treasure Sack (heroic) - Superior Healing Potion'),
(301361, 4306, 0, 40.813, 0, 1, 0, 1, 4, 'Treasure Sack (heroic) - Silk Cloth'),
(301361, 4338, 0, 52.6458, 0, 1, 0, 1, 4, 'Treasure Sack (heroic) - Mageweave Cloth'),
(301361, 4417, 0, 0.06, 0, 1, 0, 1, 1, 'Treasure Sack (heroic) - Schematic: Large Seaforium Charge'),
(301361, 4419, 0, 1.3338, 0, 1, 0, 1, 1, 'Treasure Sack (heroic) - Scroll of Intellect III'),
(301361, 4421, 0, 1.6708, 0, 1, 0, 1, 1, 'Treasure Sack (heroic) - Scroll of Protection III'),
(301361, 4422, 0, 0.7778, 0, 1, 0, 1, 1, 'Treasure Sack (heroic) - Scroll of Stamina III'),
(301361, 4424, 0, 1.9065, 0, 1, 0, 1, 1, 'Treasure Sack (heroic) - Scroll of Spirit III'),
(301361, 4599, 0, 5.8384, 0, 1, 0, 1, 1, 'Treasure Sack (heroic) - Cured Ham Steak'),
(301361, 4601, 0, 6.0901, 0, 1, 0, 1, 1, 'Treasure Sack (heroic) - Soft Banana Bread'),
(301361, 4637, 0, 1.7386, 0, 1, 0, 1, 1, 'Treasure Sack (heroic) - Steel Lockbox'),
(301361, 6149, 0, 4.8896, 0, 1, 0, 1, 1, 'Treasure Sack (heroic) - Greater Mana Potion'),
(301361, 7909, 0, 1.3143, 0, 1, 0, 1, 1, 'Treasure Sack (heroic) - Aquamarine'),
(301361, 7910, 0, 0.9761, 0, 1, 0, 1, 1, 'Treasure Sack (heroic) - Star Ruby'),
(301361, 7989, 0, 0.02, 0, 1, 0, 1, 1, 'Treasure Sack (heroic) - Plans: Mithril Spurs'),
(301361, 8548, 0, 100, 1, 1, 0, 1, 1, 'Treasure Sack (heroic) - Divino-matic Rod'),
(301361, 8623, 0, 3.0651, 0, 1, 0, 1, 1, 'Treasure Sack (heroic) - OOX-17/TN Distress Beacon'),
(301361, 9242, 0, 67.1771, 0, 1, 0, 1, 1, 'Treasure Sack (heroic) - Ancient Tablet'),
(301361, 9293, 0, 0.2399, 0, 1, 0, 1, 1, 'Treasure Sack (heroic) - Recipe: Magic Resistance Potion'),
(301361, 9295, 0, 0.06, 0, 1, 0, 1, 1, 'Treasure Sack (heroic) - Recipe: Invisibility Potion'),
(301361, 9298, 0, 0.1, 0, 1, 0, 1, 1, 'Treasure Sack (heroic) - Recipe: Elixir of Giants'),
(301361, 10606, 0, 0.2199, 0, 1, 0, 1, 1, 'Treasure Sack (heroic) - Schematic: Parachute Cloak'),
(301361, 24036, 24036, 20, 0, 1, 2, 1, 1, 'Treasure Sack (heroic) - (ReferenceTable)'),
(301361, 24039, 24039, 4, 0, 1, 2, 1, 1, 'Treasure Sack (heroic) - (ReferenceTable)'),
(301361, 24040, 24040, 2, 0, 1, 2, 1, 1, 'Treasure Sack (heroic) - (ReferenceTable)'),
(301361, 24041, 24041, 4, 0, 1, 2, 1, 1, 'Treasure Sack (heroic) - (ReferenceTable)'),
(301361, 24042, 24042, 2, 0, 1, 2, 1, 1, 'Treasure Sack (heroic) - (ReferenceTable)'),
(301361, 24043, 24043, 4, 0, 1, 2, 1, 1, 'Treasure Sack (heroic) - (ReferenceTable)'),
(301361, 24044, 24044, 1, 0, 1, 2, 1, 1, 'Treasure Sack (heroic) - (ReferenceTable)'),
(301361, 24045, 24045, 3, 0, 1, 2, 1, 1, 'Treasure Sack (heroic) - (ReferenceTable)'),
(301361, 24080, 24080, 0.2, 0, 1, 2, 1, 1, 'Treasure Sack (heroic) - (ReferenceTable)'),
(301361, 24081, 24081, 0.3, 0, 1, 2, 1, 1, 'Treasure Sack (heroic) - (ReferenceTable)');

-- The five bodies carry nothing (#19 A): Bly 7604, Raven 7605, Oro Eyegouge 7606, Weegli 7607 and Murta 7608 lose their
-- stock tables (their rows moved to the chest above or onto boss lists: Gutwrencher, Witch Doctor's Cane, Bloodletter
-- Scalpel, Blackmetal Cape). The templates' own `lootid`, `mingold` and `maxgold` are set to 0 elsewhere (the normal
-- five by the crew's creature_template changes, their heroic copies 310518 to 310522 by `_crew()` in source/world/
-- dungeons/zul_farrak.py), so no template names a table that is gone (a boot ERROR) and no body drops copper;
-- lib/test_zul_farrak_loot.py pins both halves.
DELETE FROM `creature_loot_template` WHERE `Entry` IN (7604, 7605, 7606, 7607, 7608);
