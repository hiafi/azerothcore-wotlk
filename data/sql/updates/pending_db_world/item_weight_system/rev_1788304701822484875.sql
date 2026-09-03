--
-- Percentage-allocation itemization system: item_budget_curve population.
-- See docs/itemization-changes.md §4.5. Phase 1 follow-up to rev_1788303168592708486.
--
-- Derivation: median normalized budget per item level, from every Epic-
-- quality armor item in item_template (14 known QA/test entries excluded --
-- the 4 Zul'Gurub items plus 10 more found during the sweep), fit with a
-- sample-size-weighted isotonic regression (pool-adjacent-violators) to get
-- a monotonic curve without hand-picking anchor points. Linear interpolation
-- fills every item level between fitted anchors; linear extrapolation
-- (floored at 1) covers ilvl 1-35 below the lowest anchor and ilvl 285-300
-- above the highest, for headroom on future content.
--
-- ilvl 219 (raw median, excluded outlier) is skipped in the fit, not just
-- smoothed over: it's catch-up/badge gear from three patches after the
-- first ilvl-213 raid tier, deliberately itemized richer than its item
-- level would otherwise justify. Its curve value here is interpolated from
-- ilvl 213 and 226 like any other gap, not measured from its own items.
--
-- Revision 2 (replaces the original fit): the first pass summed every
-- stat_type on an item -- including stamina -- into one normalized_budget
-- per item level. But ApplyItemBudgetAllocation() (src/server/game/Globals/
-- ItemBudget.cpp) treats item_budget_curve as the on-budget total BEFORE
-- adding item_stamina_curve's baseline on top, per §9.3's off-budget-stamina
-- design. Feeding a stamina-inclusive curve into that formula double-spent
-- every item's stamina weight: once baked into the inflated curve, once
-- again as the separate stamina line. This pass excludes stat_type=7 from
-- the sum entirely (it's what item_stamina_curve.sql now regresses instead)
-- and additionally resolves each item's on-equip passive spell effects
-- (spelltrigger_N=1, parsed directly from the client's Spell.dbc -- spell_dbc
-- in this repo only covers hand-curated custom-class-rework spells and
-- resolved just 4.5% of the ~2600 needed Vanilla/TBC on-equip auras) into
-- the same stat-type buckets: SPELL_AURA_MOD_STAT(29), MOD_ATTACK_POWER(99),
-- MOD_RATING(189) crit/haste bits, MOD_DAMAGE_DONE(13) masked to a real
-- magic school (treated as spell power; its Vanilla-era twin MOD_HEALING_
-- DONE(135) is intentionally skipped so the same bonus isn't counted twice).
-- Net effect: WotLK item levels drop (stamina was a large share of their
-- budget and is no longer double counted), Vanilla/TBC item levels rise
-- (on-equip procs on those items were previously invisible to the fit).
--

--
-- Revision 3 (replaces revision 2): MOD_RATING (aura 189) spell-effect
-- resolution only ever mapped Crit/Haste combat-rating bits. Confirmed via
-- src/server/game/Entities/Unit/Unit.h's CombatRating enum that Hit
-- (CR_HIT_MELEE/RANGED/SPELL, item_stat_cost 31), Expertise
-- (CR_EXPERTISE, 37), and Armor Penetration (CR_ARMOR_PENETRATION, 44)
-- were silently dropped -- not folded into the stat block, not even
-- counted toward the item's budget total -- despite all three already
-- having real item_stat_cost entries. 37 of 759 resolved on-equip spells
-- hit this (33 of them Armor Penetration, a dominant late-WotLK melee
-- stat, not a corner case). This pass also adds Defense/Dodge/Parry/Block
-- (CR_DEFENSE_SKILL/DODGE/PARRY/BLOCK, new item_stat_cost rows 12/13/14/15,
-- cost 1.0 each) -- 24 more spells grant one of these on-equip and had no
-- home in the budget at all before now. CR_WEAPON_SKILL never appears in
-- this dataset (obsolete for this era's real itemization) and still isn't
-- priced. Elemental resistances remain explicitly out of scope -- a
-- different item_template column and a different spell aura entirely, not
-- something this regression was ever pricing.
--
-- item_stamina_curve is unaffected (none of the newly-mapped bits touch
-- Stamina) and was not regenerated for this revision -- its revision-2
-- data is still current.
--

--
-- Revision 3 (replaces revision 2): MOD_RATING (aura 189) spell-effect
-- resolution only ever mapped Crit/Haste combat-rating bits. Confirmed via
-- src/server/game/Entities/Unit/Unit.h's CombatRating enum that Hit
-- (CR_HIT_MELEE/RANGED/SPELL, item_stat_cost 31), Expertise
-- (CR_EXPERTISE, 37), and Armor Penetration (CR_ARMOR_PENETRATION, 44)
-- were silently dropped -- not folded into the stat block, not even
-- counted toward the item's budget total -- despite all three already
-- having real item_stat_cost entries. 37 of 759 resolved on-equip spells
-- hit this (33 of them Armor Penetration, a dominant late-WotLK melee
-- stat, not a corner case). This pass also adds Defense/Dodge/Parry/Block
-- (CR_DEFENSE_SKILL/DODGE/PARRY/BLOCK, new item_stat_cost rows 12/13/14/15,
-- cost 1.0 each) -- 24 more spells grant one of these on-equip and had no
-- home in the budget at all before now. CR_WEAPON_SKILL never appears in
-- this dataset (obsolete for this era's real itemization) and still isn't
-- priced. Elemental resistances remain explicitly out of scope -- a
-- different item_template column and a different spell aura entirely, not
-- something this regression was ever pricing.
--
-- item_stamina_curve is unaffected (none of the newly-mapped bits touch
-- Stamina) and was not regenerated for this revision -- its revision-2
-- data is still current.
--

DELETE FROM `item_budget_curve` WHERE `ilvl` BETWEEN 1 AND 300;
INSERT INTO `item_budget_curve` (`ilvl`, `budget`) VALUES
(1,1),(2,1),(3,1),(4,1),(5,1),(6,1),(7,1),(8,1),(9,1),(10,1),
(11,1),(12,1),(13,1),(14,1),(15,1),(16,1),(17,1),(18,1),(19,1),(20,1),
(21,1),(22,1),(23,1),(24,1),(25,1),(26,1),(27,1),(28,1),(29,1),(30,1),
(31,1),(32,1),(33,1),(34,1),(35,1),(36,1),(37,1),(38,1),(39,1),(40,3),
(41,12),(42,21),(43,30),(44,31),(45,32),(46,33),(47,34),(48,35),(49,35),(50,36),
(51,36),(52,37),(53,38),(54,38),(55,39),(56,39),(57,40),(58,43),(59,45),(60,47),
(61,49),(62,50),(63,51),(64,51),(65,52),(66,52),(67,53),(68,53),(69,54),(70,54),
(71,55),(72,55),(73,55),(74,56),(75,56),(76,57),(77,57),(78,57),(79,57),(80,58),
(81,58),(82,58),(83,59),(84,59),(85,59),(86,59),(87,60),(88,60),(89,60),(90,61),
(91,61),(92,61),(93,62),(94,62),(95,63),(96,64),(97,65),(98,66),(99,67),(100,68),
(101,69),(102,69),(103,70),(104,71),(105,72),(106,73),(107,74),(108,75),(109,77),(110,78),
(111,80),(112,80),(113,80),(114,81),(115,81),(116,82),(117,82),(118,82),(119,83),(120,83),
(121,84),(122,85),(123,86),(124,87),(125,87),(126,93),(127,99),(128,99),(129,99),(130,99),
(131,100),(132,100),(133,102),(134,104),(135,106),(136,107),(137,109),(138,111),(139,113),(140,115),
(141,117),(142,119),(143,121),(144,122),(145,123),(146,124),(147,125),(148,126),(149,127),(150,128),
(151,129),(152,130),(153,132),(154,134),(155,135),(156,137),(157,139),(158,143),(159,148),(160,153),
(161,158),(162,164),(163,169),(164,174),(165,175),(166,176),(167,177),(168,178),(169,179),(170,180),
(171,181),(172,182),(173,182),(174,183),(175,184),(176,185),(177,186),(178,187),(179,188),(180,189),
(181,190),(182,191),(183,192),(184,193),(185,194),(186,195),(187,196),(188,197),(189,198),(190,199),
(191,199),(192,200),(193,201),(194,202),(195,203),(196,204),(197,205),(198,206),(199,207),(200,208),
(201,210),(202,213),(203,215),(204,217),(205,220),(206,222),(207,224),(208,226),(209,229),(210,231),
(211,233),(212,236),(213,238),(214,241),(215,243),(216,246),(217,249),(218,251),(219,254),(220,257),
(221,259),(222,262),(223,264),(224,267),(225,270),(226,272),(227,275),(228,278),(229,280),(230,285),
(231,291),(232,298),(233,304),(234,311),(235,317),(236,324),(237,330),(238,337),(239,343),(240,344),
(241,344),(242,345),(243,345),(244,346),(245,347),(246,347),(247,348),(248,352),(249,359),(250,366),
(251,373),(252,381),(253,388),(254,395),(255,403),(256,410),(257,417),(258,425),(259,425),(260,426),
(261,427),(262,427),(263,428),(264,429),(265,429),(266,438),(267,447),(268,456),(269,466),(270,475),
(271,484),(272,508),(273,510),(274,511),(275,513),(276,514),(277,516),(278,521),(279,527),(280,532),
(281,538),(282,543),(283,549),(284,554),(285,559),(286,565),(287,570),(288,576),(289,581),(290,587),
(291,592),(292,597),(293,603),(294,608),(295,614),(296,619),(297,625),(298,630),(299,635),(300,641);
