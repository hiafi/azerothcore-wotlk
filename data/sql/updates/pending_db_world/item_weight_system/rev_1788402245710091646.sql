-- Phase 5 content, Bucket 4 (ilvl 1-59): converts every remaining Rare/Epic armor and weapon item in this ilvl range
-- (trinkets, 8 QA/Monster-prefixed debug items, and 24 Tabard/Shirt-slot cosmetics excluded) to the budget-template
-- system, against the just-refit item_budget_curve (was flat at 1 for ilvl 1-39 -- see the companion curve migration in
-- this same batch). 19 Tabard/Shirt-slot cosmetics and 5 deliberate-negative-stat items also excluded, same precedent as
-- prior buckets. Weapon secondary stats are role-classified (physical/caster/tank, by dominant on-budget stat -- see
-- docs/itemization-changes.md's Bucket 1 note, same methodology) and corrected via a per-item budget_mult so e.g. a
-- caster Main Hand weapon isn't computed against the same slot_mult tier as a dual-wielder's One-Hand piece. Unlike
-- Bucket 1, every weapon's dps_delta is set at conversion time (not a later follow-up pass) to close the gap back to
-- that weapon's original (pre-conversion) DPS as closely as its own stat budget allows, for all three roles, not just
-- physical -- see the companion report for which items couldn't be fully matched. Each item gets its own dedicated
-- template (no consolidation classifier yet), template_id 12366-13454.

DELETE FROM `item_budget_template` WHERE `template_id` = 12366;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12366, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12367;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12367, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12368;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12368, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12369;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12369, 5, 7632),
(12369, 6, 2368);

DELETE FROM `item_budget_template` WHERE `template_id` = 12370;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12370, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12371;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12371, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12372;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12372, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12373;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12373, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12374;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12374, 5, 2487),
(12374, 6, 2487),
(12374, 45, 5026);

DELETE FROM `item_budget_template` WHERE `template_id` = 12375;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12375, 3, 6364),
(12375, 4, 3636);

DELETE FROM `item_budget_template` WHERE `template_id` = 12376;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12376, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12377;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12377, 5, 6250),
(12377, 6, 3750);

DELETE FROM `item_budget_template` WHERE `template_id` = 12378;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12378, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12379;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12379, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12380;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12380, 3, 7273),
(12380, 4, 2727);

DELETE FROM `item_budget_template` WHERE `template_id` = 12381;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12381, 5, 5238),
(12381, 6, 4762);

DELETE FROM `item_budget_template` WHERE `template_id` = 12382;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12382, 5, 7500),
(12382, 31, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 12383;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12383, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12384;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12384, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12385;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12385, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12386;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12386, 4, 7143),
(12386, 3, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 12387;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12387, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12388;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12388, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12389;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12389, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12390;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12390, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12391;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12391, 5, 5097),
(12391, 45, 4903);

DELETE FROM `item_budget_template` WHERE `template_id` = 12392;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12392, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12393;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12393, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12394;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12394, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12395;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12395, 3, 6667),
(12395, 6, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 12396;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12396, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12397;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12397, 3, 4545),
(12397, 4, 5455);

DELETE FROM `item_budget_template` WHERE `template_id` = 12398;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12398, 6, 7027),
(12398, 5, 2973);

DELETE FROM `item_budget_template` WHERE `template_id` = 12399;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12399, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12400;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12400, 5, 5000),
(12400, 6, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12401;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12401, 3, 6538),
(12401, 38, 3462);

DELETE FROM `item_budget_template` WHERE `template_id` = 12402;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12402, 5, 2013),
(12402, 6, 1677),
(12402, 45, 6310);

DELETE FROM `item_budget_template` WHERE `template_id` = 12403;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12403, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12404;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12404, 3, 8750),
(12404, 31, 1250);

DELETE FROM `item_budget_template` WHERE `template_id` = 12405;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12405, 6, 4831),
(12405, 4, 2415),
(12405, 45, 2754);

DELETE FROM `item_budget_template` WHERE `template_id` = 12406;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12406, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12407;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12407, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12408;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12408, 3, 5714),
(12408, 4, 4286);

DELETE FROM `item_budget_template` WHERE `template_id` = 12409;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12409, 3, 5714),
(12409, 4, 4286);

DELETE FROM `item_budget_template` WHERE `template_id` = 12410;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12410, 6, 7222),
(12410, 4, 2778);

DELETE FROM `item_budget_template` WHERE `template_id` = 12411;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12411, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12412;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12412, 3, 5455),
(12412, 4, 4545);

DELETE FROM `item_budget_template` WHERE `template_id` = 12413;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12413, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12414;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12414, 6, 3690),
(12414, 45, 6310);

DELETE FROM `item_budget_template` WHERE `template_id` = 12415;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12415, 6, 8276),
(12415, 3, 1724);

DELETE FROM `item_budget_template` WHERE `template_id` = 12416;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12416, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12417;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12417, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12418;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12418, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12419;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12419, 15, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12420;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12420, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12421;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12421, 6, 6875),
(12421, 5, 3125);

DELETE FROM `item_budget_template` WHERE `template_id` = 12422;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12422, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12423;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12423, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12424;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12424, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12425;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12425, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12426;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12426, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12427;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12427, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12428;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12428, 4, 3333),
(12428, 32, 6667);

DELETE FROM `item_budget_template` WHERE `template_id` = 12429;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12429, 3, 4194),
(12429, 6, 5806);

DELETE FROM `item_budget_template` WHERE `template_id` = 12430;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12430, 4, 5882),
(12430, 3, 4118);

DELETE FROM `item_budget_template` WHERE `template_id` = 12431;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12431, 3, 7692),
(12431, 31, 2308);

DELETE FROM `item_budget_template` WHERE `template_id` = 12432;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12432, 6, 2125),
(12432, 45, 7875);

DELETE FROM `item_budget_template` WHERE `template_id` = 12433;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12433, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12434;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12434, 5, 6166),
(12434, 45, 3834);

DELETE FROM `item_budget_template` WHERE `template_id` = 12435;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12435, 3, 6875),
(12435, 4, 3125);

DELETE FROM `item_budget_template` WHERE `template_id` = 12436;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12436, 5, 4936),
(12436, 45, 5064);

DELETE FROM `item_budget_template` WHERE `template_id` = 12437;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12437, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12438;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12438, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12439;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12439, 6, 3062),
(12439, 5, 1701),
(12439, 45, 5237);

DELETE FROM `item_budget_template` WHERE `template_id` = 12440;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12440, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12441;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12441, 5, 6667),
(12441, 6, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 12442;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12442, 6, 2805),
(12442, 45, 7195);

DELETE FROM `item_budget_template` WHERE `template_id` = 12443;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12443, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12444;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12444, 3, 5000),
(12444, 4, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12445;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12445, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12446;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12446, 6, 1150),
(12446, 45, 8850);

DELETE FROM `item_budget_template` WHERE `template_id` = 12447;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12447, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12448;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12448, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12449;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12449, 4, 5000),
(12449, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12450;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12450, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12451;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12451, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12452;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12452, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12453;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12453, 6, 2308),
(12453, 3, 2308),
(12453, 4, 2307),
(12453, 5, 3077);

DELETE FROM `item_budget_template` WHERE `template_id` = 12454;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12454, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12455;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12455, 3, 8333),
(12455, 4, 1667);

DELETE FROM `item_budget_template` WHERE `template_id` = 12456;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12456, 45, 2995),
(12456, 5, 7005);

DELETE FROM `item_budget_template` WHERE `template_id` = 12457;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12457, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12458;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12458, 5, 2003),
(12458, 6, 2003),
(12458, 45, 5994);

DELETE FROM `item_budget_template` WHERE `template_id` = 12459;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12459, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12460;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12460, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12461;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12461, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12462;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12462, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12463;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12463, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12464;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12464, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12465;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12465, 6, 7857),
(12465, 5, 2143);

DELETE FROM `item_budget_template` WHERE `template_id` = 12466;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12466, 14, 3846),
(12466, 4, 6154);

DELETE FROM `item_budget_template` WHERE `template_id` = 12467;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12467, 6, 4000),
(12467, 4, 6000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12468;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12468, 5, 5729),
(12468, 6, 3183),
(12468, 45, 1088);

DELETE FROM `item_budget_template` WHERE `template_id` = 12469;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12469, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12470;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12470, 3, 5333),
(12470, 4, 4667);

DELETE FROM `item_budget_template` WHERE `template_id` = 12471;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12471, 32, 5000),
(12471, 5, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12472;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12472, 5, 2181),
(12472, 6, 4089),
(12472, 45, 3730);

DELETE FROM `item_budget_template` WHERE `template_id` = 12473;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12473, 6, 3750),
(12473, 5, 6250);

DELETE FROM `item_budget_template` WHERE `template_id` = 12474;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12474, 3, 6667),
(12474, 32, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 12475;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12475, 45, 6310),
(12475, 5, 3690);

DELETE FROM `item_budget_template` WHERE `template_id` = 12476;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12476, 45, 6494),
(12476, 6, 3506);

DELETE FROM `item_budget_template` WHERE `template_id` = 12477;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12477, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12478;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12478, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12479;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12479, 3, 7143),
(12479, 6, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 12480;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12480, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12481;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12481, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12482;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12482, 6, 4596),
(12482, 45, 5404);

DELETE FROM `item_budget_template` WHERE `template_id` = 12483;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12483, 15, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12484;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12484, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12485;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12485, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12486;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12486, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12487;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12487, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12488;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12488, 5, 5006),
(12488, 45, 4994);

DELETE FROM `item_budget_template` WHERE `template_id` = 12489;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12489, 4, 5000),
(12489, 31, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12490;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12490, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12491;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12491, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12492;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12492, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12493;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12493, 6, 3846),
(12493, 5, 6154);

DELETE FROM `item_budget_template` WHERE `template_id` = 12494;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12494, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12495;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12495, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12496;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12496, 3, 7143),
(12496, 4, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 12497;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12497, 6, 6667),
(12497, 5, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 12498;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12498, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12499;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12499, 4, 6923),
(12499, 32, 3077);

DELETE FROM `item_budget_template` WHERE `template_id` = 12500;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12500, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12501;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12501, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12502;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12502, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12503;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12503, 5, 5006),
(12503, 45, 4994);

DELETE FROM `item_budget_template` WHERE `template_id` = 12504;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12504, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12505;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12505, 13, 5455),
(12505, 3, 4545);

DELETE FROM `item_budget_template` WHERE `template_id` = 12506;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12506, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12507;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12507, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12508;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12508, 13, 3333),
(12508, 4, 6667);

DELETE FROM `item_budget_template` WHERE `template_id` = 12509;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12509, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12510;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12510, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12511;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12511, 6, 1348),
(12511, 5, 4043),
(12511, 45, 4609);

DELETE FROM `item_budget_template` WHERE `template_id` = 12512;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12512, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12513;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12513, 6, 8571),
(12513, 5, 1429);

DELETE FROM `item_budget_template` WHERE `template_id` = 12514;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12514, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12515;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12515, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12516;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12516, 5, 6798),
(12516, 6, 2039),
(12516, 45, 1163);

DELETE FROM `item_budget_template` WHERE `template_id` = 12517;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12517, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12518;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12518, 3, 4286),
(12518, 4, 5714);

DELETE FROM `item_budget_template` WHERE `template_id` = 12519;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12519, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12520;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12520, 4, 7273),
(12520, 3, 2727);

DELETE FROM `item_budget_template` WHERE `template_id` = 12521;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12521, 6, 6667),
(12521, 5, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 12522;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12522, 6, 5006),
(12522, 45, 4994);

DELETE FROM `item_budget_template` WHERE `template_id` = 12523;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12523, 3, 6250),
(12523, 31, 3750);

DELETE FROM `item_budget_template` WHERE `template_id` = 12524;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12524, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12525;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12525, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12526;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12526, 5, 5000),
(12526, 6, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12527;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12527, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12528;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12528, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12529;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12529, 6, 3333),
(12529, 5, 6667);

DELETE FROM `item_budget_template` WHERE `template_id` = 12530;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12530, 6, 7005),
(12530, 45, 2995);

DELETE FROM `item_budget_template` WHERE `template_id` = 12531;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12531, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12532;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12532, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12533;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12533, 32, 6250),
(12533, 4, 3750);

DELETE FROM `item_budget_template` WHERE `template_id` = 12534;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12534, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12535;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12535, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12536;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12536, 5, 3077),
(12536, 6, 2308),
(12536, 32, 4615);

DELETE FROM `item_budget_template` WHERE `template_id` = 12537;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12537, 5, 3956),
(12537, 6, 1695),
(12537, 45, 4349);

DELETE FROM `item_budget_template` WHERE `template_id` = 12538;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12538, 4, 5000),
(12538, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12539;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12539, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12540;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12540, 5, 2696),
(12540, 6, 2695),
(12540, 45, 4609);

DELETE FROM `item_budget_template` WHERE `template_id` = 12541;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12541, 5, 2500),
(12541, 6, 7500);

DELETE FROM `item_budget_template` WHERE `template_id` = 12542;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12542, 4, 4800),
(12542, 3, 5200);

DELETE FROM `item_budget_template` WHERE `template_id` = 12543;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12543, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12544;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12544, 6, 4545),
(12544, 4, 5455);

DELETE FROM `item_budget_template` WHERE `template_id` = 12545;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12545, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12546;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12546, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12547;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12547, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12548;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12548, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12549;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12549, 6, 2714),
(12549, 5, 5429),
(12549, 45, 1857);

DELETE FROM `item_budget_template` WHERE `template_id` = 12550;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12550, 3, 3334),
(12550, 4, 3333),
(12550, 6, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 12551;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12551, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12552;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12552, 4, 7500),
(12552, 3, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 12553;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12553, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12554;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12554, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12555;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12555, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12556;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12556, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12557;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12557, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12558;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12558, 6, 7273),
(12558, 5, 2727);

DELETE FROM `item_budget_template` WHERE `template_id` = 12559;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12559, 4, 4000),
(12559, 3, 6000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12560;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12560, 5, 3009),
(12560, 6, 2580),
(12560, 45, 4411);

DELETE FROM `item_budget_template` WHERE `template_id` = 12561;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12561, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12562;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12562, 5, 3690),
(12562, 45, 6310);

DELETE FROM `item_budget_template` WHERE `template_id` = 12563;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12563, 5, 2500),
(12563, 6, 7500);

DELETE FROM `item_budget_template` WHERE `template_id` = 12564;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12564, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12565;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12565, 6, 6667),
(12565, 5, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 12566;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12566, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12567;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12567, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12568;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12568, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12569;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12569, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12570;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12570, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12571;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12571, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12572;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12572, 5, 3060),
(12572, 31, 2754),
(12572, 45, 4186);

DELETE FROM `item_budget_template` WHERE `template_id` = 12573;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12573, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12574;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12574, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12575;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12575, 4, 7333),
(12575, 3, 2667);

DELETE FROM `item_budget_template` WHERE `template_id` = 12576;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12576, 5, 3339),
(12576, 45, 6661);

DELETE FROM `item_budget_template` WHERE `template_id` = 12577;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12577, 5, 3339),
(12577, 45, 6661);

DELETE FROM `item_budget_template` WHERE `template_id` = 12578;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12578, 5, 2125),
(12578, 45, 7875);

DELETE FROM `item_budget_template` WHERE `template_id` = 12579;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12579, 5, 909),
(12579, 6, 9091);

DELETE FROM `item_budget_template` WHERE `template_id` = 12580;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12580, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12581;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12581, 5, 3636),
(12581, 6, 1818),
(12581, 32, 4546);

DELETE FROM `item_budget_template` WHERE `template_id` = 12582;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12582, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12583;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12583, 3, 6923),
(12583, 4, 3077);

DELETE FROM `item_budget_template` WHERE `template_id` = 12584;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12584, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12585;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12585, 4, 6667),
(12585, 3, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 12586;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12586, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12587;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12587, 4, 4000),
(12587, 3, 6000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12588;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12588, 5, 4789),
(12588, 45, 5211);

DELETE FROM `item_budget_template` WHERE `template_id` = 12589;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12589, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12590;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12590, 6, 5206),
(12590, 45, 4794);

DELETE FROM `item_budget_template` WHERE `template_id` = 12591;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12591, 5, 3600),
(12591, 6, 2800),
(12591, 31, 3600);

DELETE FROM `item_budget_template` WHERE `template_id` = 12592;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12592, 5, 6000),
(12592, 32, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12593;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12593, 5, 4279),
(12593, 6, 1605),
(12593, 45, 4116);

DELETE FROM `item_budget_template` WHERE `template_id` = 12594;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12594, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12595;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12595, 4, 4815),
(12595, 32, 5185);

DELETE FROM `item_budget_template` WHERE `template_id` = 12596;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12596, 6, 5000),
(12596, 5, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12597;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12597, 6, 5391),
(12597, 45, 4609);

DELETE FROM `item_budget_template` WHERE `template_id` = 12598;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12598, 5, 5000),
(12598, 6, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12599;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12599, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12600;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12600, 12, 5000),
(12600, 4, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12601;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12601, 4, 4286),
(12601, 3, 5714);

DELETE FROM `item_budget_template` WHERE `template_id` = 12602;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12602, 6, 4000),
(12602, 5, 6000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12603;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12603, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12604;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12604, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12605;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12605, 4, 7000),
(12605, 6, 3000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12606;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12606, 3, 6000),
(12606, 4, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12607;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12607, 4, 3333),
(12607, 3, 6667);

DELETE FROM `item_budget_template` WHERE `template_id` = 12608;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12608, 4, 5000),
(12608, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12609;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12609, 5, 5938),
(12609, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 12610;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12610, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12611;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12611, 4, 6000),
(12611, 32, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12612;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12612, 5, 1991),
(12612, 6, 6306),
(12612, 45, 1703);

DELETE FROM `item_budget_template` WHERE `template_id` = 12613;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12613, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12614;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12614, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12615;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12615, 15, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12616;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12616, 5, 909),
(12616, 6, 9091);

DELETE FROM `item_budget_template` WHERE `template_id` = 12617;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12617, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12618;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12618, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12619;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12619, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12620;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12620, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12621;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12621, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12622;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12622, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12623;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12623, 31, 3636),
(12623, 32, 6364);

DELETE FROM `item_budget_template` WHERE `template_id` = 12624;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12624, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12625;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12625, 45, 5192),
(12625, 31, 2784),
(12625, 5, 2024);

DELETE FROM `item_budget_template` WHERE `template_id` = 12626;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12626, 32, 5000),
(12626, 31, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12627;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12627, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12628;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12628, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12629;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12629, 3, 2273),
(12629, 37, 7727);

DELETE FROM `item_budget_template` WHERE `template_id` = 12630;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12630, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12631;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12631, 14, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12632;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12632, 4, 5455),
(12632, 3, 4545);

DELETE FROM `item_budget_template` WHERE `template_id` = 12633;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12633, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12634;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12634, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12635;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12635, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12636;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12636, 6, 2805),
(12636, 45, 7195);

DELETE FROM `item_budget_template` WHERE `template_id` = 12637;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12637, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12638;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12638, 5, 2941),
(12638, 6, 7059);

DELETE FROM `item_budget_template` WHERE `template_id` = 12639;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12639, 3, 5000),
(12639, 31, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12640;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12640, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12641;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12641, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12642;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12642, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12643;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12643, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12644;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12644, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12645;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12645, 4, 7059),
(12645, 12, 2941);

DELETE FROM `item_budget_template` WHERE `template_id` = 12646;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12646, 5, 6316),
(12646, 4, 3684);

DELETE FROM `item_budget_template` WHERE `template_id` = 12647;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12647, 6, 6609),
(12647, 45, 3391);

DELETE FROM `item_budget_template` WHERE `template_id` = 12648;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12648, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12649;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12649, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12650;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12650, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12651;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12651, 4, 1515),
(12651, 32, 8485);

DELETE FROM `item_budget_template` WHERE `template_id` = 12652;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12652, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12653;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12653, 6, 4399),
(12653, 5, 1571),
(12653, 45, 4030);

DELETE FROM `item_budget_template` WHERE `template_id` = 12654;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12654, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12655;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12655, 32, 4375),
(12655, 3, 5625);

DELETE FROM `item_budget_template` WHERE `template_id` = 12656;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12656, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12657;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12657, 3, 6667),
(12657, 4, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 12658;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12658, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12659;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12659, 4, 6667),
(12659, 3, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 12660;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12660, 6, 1286),
(12660, 5, 3216),
(12660, 45, 5498);

DELETE FROM `item_budget_template` WHERE `template_id` = 12661;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12661, 5, 4688),
(12661, 6, 2482),
(12661, 45, 2830);

DELETE FROM `item_budget_template` WHERE `template_id` = 12662;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12662, 4, 5000),
(12662, 32, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12663;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12663, 5, 7782),
(12663, 45, 2218);

DELETE FROM `item_budget_template` WHERE `template_id` = 12664;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12664, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12665;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12665, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12666;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12666, 3, 4545),
(12666, 4, 5455);

DELETE FROM `item_budget_template` WHERE `template_id` = 12667;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12667, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12668;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12668, 4, 7619),
(12668, 3, 2381);

DELETE FROM `item_budget_template` WHERE `template_id` = 12669;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12669, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12670;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12670, 5, 4915),
(12670, 6, 2458),
(12670, 45, 2627);

DELETE FROM `item_budget_template` WHERE `template_id` = 12671;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12671, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12672;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12672, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12673;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12673, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12674;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12674, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12675;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12675, 5, 3420),
(12675, 45, 6580);

DELETE FROM `item_budget_template` WHERE `template_id` = 12676;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12676, 45, 7108),
(12676, 5, 2892);

DELETE FROM `item_budget_template` WHERE `template_id` = 12677;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12677, 5, 7005),
(12677, 45, 2995);

DELETE FROM `item_budget_template` WHERE `template_id` = 12678;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12678, 4, 6000),
(12678, 32, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12679;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12679, 32, 3846),
(12679, 4, 6154);

DELETE FROM `item_budget_template` WHERE `template_id` = 12680;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12680, 3, 6970),
(12680, 4, 3030);

DELETE FROM `item_budget_template` WHERE `template_id` = 12681;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12681, 6, 3846),
(12681, 4, 6154);

DELETE FROM `item_budget_template` WHERE `template_id` = 12682;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12682, 6, 2805),
(12682, 45, 7195);

DELETE FROM `item_budget_template` WHERE `template_id` = 12683;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12683, 5, 3371),
(12683, 45, 6629);

DELETE FROM `item_budget_template` WHERE `template_id` = 12684;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12684, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12685;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12685, 4, 7368),
(12685, 3, 2632);

DELETE FROM `item_budget_template` WHERE `template_id` = 12686;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12686, 5, 4872),
(12686, 6, 3045),
(12686, 45, 2083);

DELETE FROM `item_budget_template` WHERE `template_id` = 12687;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12687, 6, 4444),
(12687, 5, 5556);

DELETE FROM `item_budget_template` WHERE `template_id` = 12688;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12688, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12689;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12689, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12690;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12690, 3, 5000),
(12690, 4, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12691;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12691, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12692;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12692, 5, 2984),
(12692, 45, 7016);

DELETE FROM `item_budget_template` WHERE `template_id` = 12693;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12693, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12694;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12694, 5, 7188),
(12694, 6, 2812);

DELETE FROM `item_budget_template` WHERE `template_id` = 12695;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12695, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12696;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12696, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12697;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12697, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12698;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12698, 3, 8571),
(12698, 4, 1429);

DELETE FROM `item_budget_template` WHERE `template_id` = 12699;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12699, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12700;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12700, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12701;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12701, 5, 872),
(12701, 6, 4653),
(12701, 45, 4475);

DELETE FROM `item_budget_template` WHERE `template_id` = 12702;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12702, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12703;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12703, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12704;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12704, 4, 5000),
(12704, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12705;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12705, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12706;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12706, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12707;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12707, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12708;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12708, 6, 2652),
(12708, 5, 1516),
(12708, 45, 5832);

DELETE FROM `item_budget_template` WHERE `template_id` = 12709;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12709, 31, 3647),
(12709, 5, 2344),
(12709, 45, 4009);

DELETE FROM `item_budget_template` WHERE `template_id` = 12710;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12710, 6, 3003),
(12710, 5, 2503),
(12710, 45, 4494);

DELETE FROM `item_budget_template` WHERE `template_id` = 12711;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12711, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12712;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12712, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12713;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12713, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12714;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12714, 3, 4286),
(12714, 4, 5714);

DELETE FROM `item_budget_template` WHERE `template_id` = 12715;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12715, 4, 3571),
(12715, 3, 6429);

DELETE FROM `item_budget_template` WHERE `template_id` = 12716;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12716, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12717;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12717, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12718;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12718, 3, 5455),
(12718, 4, 4545);

DELETE FROM `item_budget_template` WHERE `template_id` = 12719;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12719, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12720;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12720, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12721;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12721, 4, 7619),
(12721, 3, 2381);

DELETE FROM `item_budget_template` WHERE `template_id` = 12722;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12722, 6, 1991),
(12722, 5, 6306),
(12722, 45, 1703);

DELETE FROM `item_budget_template` WHERE `template_id` = 12723;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12723, 5, 3158),
(12723, 6, 6842);

DELETE FROM `item_budget_template` WHERE `template_id` = 12724;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12724, 5, 3810),
(12724, 6, 6190);

DELETE FROM `item_budget_template` WHERE `template_id` = 12725;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12725, 6, 3615),
(12725, 45, 2318),
(12725, 5, 4067);

DELETE FROM `item_budget_template` WHERE `template_id` = 12726;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12726, 3, 7037),
(12726, 4, 2963);

DELETE FROM `item_budget_template` WHERE `template_id` = 12727;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12727, 4, 5882),
(12727, 32, 4118);

DELETE FROM `item_budget_template` WHERE `template_id` = 12728;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12728, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12729;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12729, 5, 2502),
(12729, 6, 3754),
(12729, 45, 3744);

DELETE FROM `item_budget_template` WHERE `template_id` = 12730;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12730, 5, 4834),
(12730, 45, 5166);

DELETE FROM `item_budget_template` WHERE `template_id` = 12731;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12731, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12732;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12732, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12733;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12733, 4, 6667),
(12733, 3, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 12734;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12734, 5, 5097),
(12734, 45, 4903);

DELETE FROM `item_budget_template` WHERE `template_id` = 12735;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12735, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12736;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12736, 13, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12737;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12737, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12738;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12738, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12739;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12739, 6, 6667),
(12739, 3, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 12740;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12740, 5, 4236),
(12740, 6, 4486),
(12740, 45, 1278);

DELETE FROM `item_budget_template` WHERE `template_id` = 12741;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12741, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12742;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12742, 4, 5238),
(12742, 3, 4762);

DELETE FROM `item_budget_template` WHERE `template_id` = 12743;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12743, 5, 4167),
(12743, 32, 5833);

DELETE FROM `item_budget_template` WHERE `template_id` = 12744;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12744, 4, 6818),
(12744, 3, 3182);

DELETE FROM `item_budget_template` WHERE `template_id` = 12745;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12745, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12746;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12746, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12747;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12747, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12748;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12748, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12749;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12749, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12750;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12750, 32, 6820),
(12750, 45, 3180);

DELETE FROM `item_budget_template` WHERE `template_id` = 12751;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12751, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12752;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12752, 5, 4936),
(12752, 45, 5064);

DELETE FROM `item_budget_template` WHERE `template_id` = 12753;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12753, 4, 4545),
(12753, 3, 5455);

DELETE FROM `item_budget_template` WHERE `template_id` = 12754;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12754, 4, 5556),
(12754, 3, 4444);

DELETE FROM `item_budget_template` WHERE `template_id` = 12755;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12755, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12756;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12756, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12757;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12757, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12758;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12758, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12759;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12759, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12760;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12760, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12761;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12761, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12762;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12762, 45, 7054),
(12762, 5, 2946);

DELETE FROM `item_budget_template` WHERE `template_id` = 12763;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12763, 6, 5391),
(12763, 45, 4609);

DELETE FROM `item_budget_template` WHERE `template_id` = 12764;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12764, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12765;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12765, 5, 2340),
(12765, 6, 3830),
(12765, 32, 3830);

DELETE FROM `item_budget_template` WHERE `template_id` = 12766;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12766, 6, 4505),
(12766, 5, 1001),
(12766, 45, 4494);

DELETE FROM `item_budget_template` WHERE `template_id` = 12767;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12767, 6, 2027),
(12767, 45, 7973);

DELETE FROM `item_budget_template` WHERE `template_id` = 12768;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12768, 3, 909),
(12768, 6, 9091);

DELETE FROM `item_budget_template` WHERE `template_id` = 12769;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12769, 6, 4936),
(12769, 45, 5064);

DELETE FROM `item_budget_template` WHERE `template_id` = 12770;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12770, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12771;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12771, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12772;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12772, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12773;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12773, 4, 3750),
(12773, 31, 6250);

DELETE FROM `item_budget_template` WHERE `template_id` = 12774;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12774, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12775;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12775, 6, 1909),
(12775, 5, 2727),
(12775, 45, 5364);

DELETE FROM `item_budget_template` WHERE `template_id` = 12776;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12776, 5, 2063),
(12776, 45, 7937);

DELETE FROM `item_budget_template` WHERE `template_id` = 12777;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12777, 6, 5097),
(12777, 45, 4903);

DELETE FROM `item_budget_template` WHERE `template_id` = 12778;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12778, 3, 1429),
(12778, 12, 8571);

DELETE FROM `item_budget_template` WHERE `template_id` = 12779;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12779, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12780;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12780, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12781;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12781, 6, 7782),
(12781, 45, 2218);

DELETE FROM `item_budget_template` WHERE `template_id` = 12782;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12782, 6, 3830),
(12782, 5, 3830),
(12782, 3, 2340);

DELETE FROM `item_budget_template` WHERE `template_id` = 12783;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12783, 6, 6471),
(12783, 5, 3529);

DELETE FROM `item_budget_template` WHERE `template_id` = 12784;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12784, 5, 3339),
(12784, 45, 6661);

DELETE FROM `item_budget_template` WHERE `template_id` = 12785;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12785, 6, 4936),
(12785, 45, 5064);

DELETE FROM `item_budget_template` WHERE `template_id` = 12786;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12786, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12787;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12787, 5, 1908),
(12787, 6, 2384),
(12787, 45, 5708);

DELETE FROM `item_budget_template` WHERE `template_id` = 12788;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12788, 5, 4198),
(12788, 6, 1937),
(12788, 45, 3865);

DELETE FROM `item_budget_template` WHERE `template_id` = 12789;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12789, 5, 2677),
(12789, 45, 7323);

DELETE FROM `item_budget_template` WHERE `template_id` = 12790;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12790, 4, 3000),
(12790, 3, 7000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12791;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12791, 3, 7917),
(12791, 5, 2083);

DELETE FROM `item_budget_template` WHERE `template_id` = 12792;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12792, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12793;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12793, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12794;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12794, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12795;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12795, 4, 5000),
(12795, 32, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12796;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12796, 4, 5938),
(12796, 31, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 12797;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12797, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12798;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12798, 5, 3759),
(12798, 31, 2734),
(12798, 45, 3507);

DELETE FROM `item_budget_template` WHERE `template_id` = 12799;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12799, 5, 3435),
(12799, 6, 2748),
(12799, 45, 3817);

DELETE FROM `item_budget_template` WHERE `template_id` = 12800;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12800, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12801;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12801, 4, 4762),
(12801, 3, 5238);

DELETE FROM `item_budget_template` WHERE `template_id` = 12802;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12802, 4, 5000),
(12802, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12803;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12803, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12804;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12804, 4, 3793),
(12804, 3, 3448),
(12804, 31, 2759);

DELETE FROM `item_budget_template` WHERE `template_id` = 12805;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12805, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12806;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12806, 4, 5714),
(12806, 3, 4286);

DELETE FROM `item_budget_template` WHERE `template_id` = 12807;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12807, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12808;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12808, 5, 5938),
(12808, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 12809;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12809, 3, 3333),
(12809, 32, 6667);

DELETE FROM `item_budget_template` WHERE `template_id` = 12810;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12810, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12811;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12811, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12812;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12812, 3, 4286),
(12812, 5, 5714);

DELETE FROM `item_budget_template` WHERE `template_id` = 12813;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12813, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12814;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12814, 4, 1765),
(12814, 32, 8235);

DELETE FROM `item_budget_template` WHERE `template_id` = 12815;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12815, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12816;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12816, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12817;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12817, 4, 6207),
(12817, 12, 3793);

DELETE FROM `item_budget_template` WHERE `template_id` = 12818;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12818, 6, 3258),
(12818, 5, 1222),
(12818, 31, 2037),
(12818, 45, 3483);

DELETE FROM `item_budget_template` WHERE `template_id` = 12819;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12819, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12820;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12820, 3, 5000),
(12820, 5, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12821;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12821, 6, 2048),
(12821, 5, 2458),
(12821, 32, 2867),
(12821, 45, 2627);

DELETE FROM `item_budget_template` WHERE `template_id` = 12822;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12822, 4, 3333),
(12822, 13, 6667);

DELETE FROM `item_budget_template` WHERE `template_id` = 12823;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12823, 5, 2892),
(12823, 45, 7108);

DELETE FROM `item_budget_template` WHERE `template_id` = 12824;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12824, 5, 2625),
(12824, 45, 7375);

DELETE FROM `item_budget_template` WHERE `template_id` = 12825;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12825, 5, 4223),
(12825, 45, 5777);

DELETE FROM `item_budget_template` WHERE `template_id` = 12826;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12826, 13, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12827;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12827, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12828;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12828, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12829;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12829, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12830;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12830, 5, 3305),
(12830, 32, 3305),
(12830, 45, 3390);

DELETE FROM `item_budget_template` WHERE `template_id` = 12831;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12831, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12832;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12832, 5, 5238),
(12832, 3, 4762);

DELETE FROM `item_budget_template` WHERE `template_id` = 12833;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12833, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12834;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12834, 4, 4000),
(12834, 3, 6000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12835;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12835, 4, 2727),
(12835, 3, 7273);

DELETE FROM `item_budget_template` WHERE `template_id` = 12836;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12836, 5, 3236),
(12836, 45, 6764);

DELETE FROM `item_budget_template` WHERE `template_id` = 12837;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12837, 5, 4273),
(12837, 6, 1709),
(12837, 45, 4018);

DELETE FROM `item_budget_template` WHERE `template_id` = 12838;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12838, 6, 1763),
(12838, 31, 1762),
(12838, 5, 3084),
(12838, 45, 3391);

DELETE FROM `item_budget_template` WHERE `template_id` = 12839;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12839, 5, 4167),
(12839, 32, 5833);

DELETE FROM `item_budget_template` WHERE `template_id` = 12840;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12840, 6, 4190),
(12840, 5, 1630),
(12840, 45, 4180);

DELETE FROM `item_budget_template` WHERE `template_id` = 12841;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12841, 5, 5219),
(12841, 45, 4781);

DELETE FROM `item_budget_template` WHERE `template_id` = 12842;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12842, 6, 6190),
(12842, 4, 3810);

DELETE FROM `item_budget_template` WHERE `template_id` = 12843;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12843, 31, 2632),
(12843, 32, 7368);

DELETE FROM `item_budget_template` WHERE `template_id` = 12844;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12844, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12845;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12845, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12846;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12846, 3, 6129),
(12846, 4, 3871);

DELETE FROM `item_budget_template` WHERE `template_id` = 12847;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12847, 4, 2222),
(12847, 32, 7778);

DELETE FROM `item_budget_template` WHERE `template_id` = 12848;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12848, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12849;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12849, 6, 7000),
(12849, 5, 3000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12850;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12850, 14, 5882),
(12850, 32, 4118);

DELETE FROM `item_budget_template` WHERE `template_id` = 12851;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12851, 6, 2946),
(12851, 45, 7054);

DELETE FROM `item_budget_template` WHERE `template_id` = 12852;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12852, 6, 2063),
(12852, 45, 7937);

DELETE FROM `item_budget_template` WHERE `template_id` = 12853;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12853, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12854;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12854, 4, 5263),
(12854, 6, 2632),
(12854, 3, 2105);

DELETE FROM `item_budget_template` WHERE `template_id` = 12855;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12855, 5, 6000),
(12855, 6, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12856;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12856, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12857;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12857, 6, 2036),
(12857, 5, 2885),
(12857, 45, 5079);

DELETE FROM `item_budget_template` WHERE `template_id` = 12858;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12858, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12859;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12859, 6, 3062),
(12859, 5, 1701),
(12859, 45, 5237);

DELETE FROM `item_budget_template` WHERE `template_id` = 12860;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12860, 13, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12861;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12861, 5, 3940),
(12861, 6, 2424),
(12861, 31, 3636);

DELETE FROM `item_budget_template` WHERE `template_id` = 12862;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12862, 3, 6538),
(12862, 31, 1154),
(12862, 38, 2308);

DELETE FROM `item_budget_template` WHERE `template_id` = 12863;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12863, 6, 7647),
(12863, 5, 2353);

DELETE FROM `item_budget_template` WHERE `template_id` = 12864;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12864, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12865;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12865, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12866;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12866, 5, 5000),
(12866, 6, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12867;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12867, 5, 7143),
(12867, 6, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 12868;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12868, 6, 2831),
(12868, 5, 3538),
(12868, 45, 3631);

DELETE FROM `item_budget_template` WHERE `template_id` = 12869;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12869, 5, 7266),
(12869, 45, 2734);

DELETE FROM `item_budget_template` WHERE `template_id` = 12870;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12870, 4, 7000),
(12870, 12, 3000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12871;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12871, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12872;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12872, 3, 8400),
(12872, 4, 1600);

DELETE FROM `item_budget_template` WHERE `template_id` = 12873;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12873, 5, 3219),
(12873, 6, 2971),
(12873, 45, 3810);

DELETE FROM `item_budget_template` WHERE `template_id` = 12874;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12874, 3, 4815),
(12874, 4, 5185);

DELETE FROM `item_budget_template` WHERE `template_id` = 12875;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12875, 6, 4056),
(12875, 45, 5944);

DELETE FROM `item_budget_template` WHERE `template_id` = 12876;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12876, 3, 5385),
(12876, 4, 4615);

DELETE FROM `item_budget_template` WHERE `template_id` = 12877;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12877, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12878;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12878, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12879;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12879, 6, 3148),
(12879, 45, 6852);

DELETE FROM `item_budget_template` WHERE `template_id` = 12880;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12880, 6, 3371),
(12880, 45, 6629);

DELETE FROM `item_budget_template` WHERE `template_id` = 12881;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12881, 5, 4785),
(12881, 6, 1709),
(12881, 45, 3506);

DELETE FROM `item_budget_template` WHERE `template_id` = 12882;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12882, 5, 3126),
(12882, 45, 6874);

DELETE FROM `item_budget_template` WHERE `template_id` = 12883;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12883, 3, 2308),
(12883, 31, 7692);

DELETE FROM `item_budget_template` WHERE `template_id` = 12884;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12884, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12885;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12885, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12886;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12886, 14, 5000),
(12886, 31, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12887;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12887, 4, 6207),
(12887, 3, 3793);

DELETE FROM `item_budget_template` WHERE `template_id` = 12888;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12888, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12889;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12889, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12890;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12890, 6, 4444),
(12890, 5, 5556);

DELETE FROM `item_budget_template` WHERE `template_id` = 12891;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12891, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12892;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12892, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12893;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12893, 4, 4444),
(12893, 6, 5556);

DELETE FROM `item_budget_template` WHERE `template_id` = 12894;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12894, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12895;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12895, 6, 4615),
(12895, 5, 5385);

DELETE FROM `item_budget_template` WHERE `template_id` = 12896;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12896, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12897;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12897, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12898;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12898, 4, 6667),
(12898, 6, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 12899;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12899, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12900;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12900, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12901;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12901, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12902;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12902, 5, 6780),
(12902, 45, 3220);

DELETE FROM `item_budget_template` WHERE `template_id` = 12903;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12903, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12904;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12904, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12905;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12905, 4, 4848),
(12905, 3, 5152);

DELETE FROM `item_budget_template` WHERE `template_id` = 12906;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12906, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12907;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12907, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12908;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12908, 6, 7353),
(12908, 5, 2647);

DELETE FROM `item_budget_template` WHERE `template_id` = 12909;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12909, 3, 3846),
(12909, 4, 6154);

DELETE FROM `item_budget_template` WHERE `template_id` = 12910;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12910, 5, 6780),
(12910, 45, 3220);

DELETE FROM `item_budget_template` WHERE `template_id` = 12911;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12911, 4, 6667),
(12911, 3, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 12912;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12912, 5, 6802),
(12912, 45, 3198);

DELETE FROM `item_budget_template` WHERE `template_id` = 12913;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12913, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12914;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12914, 4, 6970),
(12914, 31, 3030);

DELETE FROM `item_budget_template` WHERE `template_id` = 12915;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12915, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12916;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12916, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12917;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12917, 4, 7500),
(12917, 6, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 12918;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12918, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12919;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12919, 4, 2353),
(12919, 3, 2353),
(12919, 6, 2941),
(12919, 5, 2353);

DELETE FROM `item_budget_template` WHERE `template_id` = 12920;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12920, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12921;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12921, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12922;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12922, 6, 4006),
(12922, 45, 5994);

DELETE FROM `item_budget_template` WHERE `template_id` = 12923;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12923, 6, 5455),
(12923, 5, 4545);

DELETE FROM `item_budget_template` WHERE `template_id` = 12924;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12924, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12925;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12925, 4, 1765),
(12925, 32, 8235);

DELETE FROM `item_budget_template` WHERE `template_id` = 12926;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12926, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12927;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12927, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12928;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12928, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12929;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12929, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12930;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12930, 4, 4444),
(12930, 6, 5556);

DELETE FROM `item_budget_template` WHERE `template_id` = 12931;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12931, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12932;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12932, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12933;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12933, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12934;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12934, 4, 5385),
(12934, 6, 4615);

DELETE FROM `item_budget_template` WHERE `template_id` = 12935;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12935, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12936;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12936, 6, 2105),
(12936, 12, 7895);

DELETE FROM `item_budget_template` WHERE `template_id` = 12937;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12937, 4, 909),
(12937, 31, 9091);

DELETE FROM `item_budget_template` WHERE `template_id` = 12938;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12938, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12939;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12939, 14, 5000),
(12939, 31, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12940;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12940, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12941;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12941, 4, 3714),
(12941, 3, 3714),
(12941, 6, 2572);

DELETE FROM `item_budget_template` WHERE `template_id` = 12942;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12942, 5, 6667),
(12942, 6, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 12943;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12943, 4, 6000),
(12943, 3, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12944;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12944, 4, 6190),
(12944, 3, 3810);

DELETE FROM `item_budget_template` WHERE `template_id` = 12945;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12945, 3, 3750),
(12945, 4, 6250);

DELETE FROM `item_budget_template` WHERE `template_id` = 12946;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12946, 3, 3913),
(12946, 4, 6087);

DELETE FROM `item_budget_template` WHERE `template_id` = 12947;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12947, 4, 5000),
(12947, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12948;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12948, 6, 6296),
(12948, 4, 3704);

DELETE FROM `item_budget_template` WHERE `template_id` = 12949;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12949, 4, 7097),
(12949, 12, 2903);

DELETE FROM `item_budget_template` WHERE `template_id` = 12950;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12950, 4, 6667),
(12950, 3, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 12951;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12951, 4, 2433),
(12951, 6, 2703),
(12951, 5, 2432),
(12951, 3, 2432);

DELETE FROM `item_budget_template` WHERE `template_id` = 12952;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12952, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12953;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12953, 4, 6667),
(12953, 3, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 12954;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12954, 6, 7059),
(12954, 5, 2941);

DELETE FROM `item_budget_template` WHERE `template_id` = 12955;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12955, 5, 2500),
(12955, 6, 2500),
(12955, 4, 2500),
(12955, 3, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 12956;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12956, 5, 7778),
(12956, 6, 2222);

DELETE FROM `item_budget_template` WHERE `template_id` = 12957;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12957, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12958;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12958, 4, 5714),
(12958, 6, 4286);

DELETE FROM `item_budget_template` WHERE `template_id` = 12959;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12959, 4, 2381),
(12959, 3, 6190),
(12959, 6, 1429);

DELETE FROM `item_budget_template` WHERE `template_id` = 12960;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12960, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12961;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12961, 6, 4706),
(12961, 3, 2941),
(12961, 4, 2353);

DELETE FROM `item_budget_template` WHERE `template_id` = 12962;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12962, 6, 8000),
(12962, 5, 2000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12963;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12963, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12964;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12964, 3, 2727),
(12964, 4, 7273);

DELETE FROM `item_budget_template` WHERE `template_id` = 12965;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12965, 6, 7005),
(12965, 45, 2995);

DELETE FROM `item_budget_template` WHERE `template_id` = 12966;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12966, 6, 6957),
(12966, 5, 3043);

DELETE FROM `item_budget_template` WHERE `template_id` = 12967;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12967, 6, 3322),
(12967, 5, 3322),
(12967, 45, 3356);

DELETE FROM `item_budget_template` WHERE `template_id` = 12968;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12968, 6, 3140),
(12968, 45, 6860);

DELETE FROM `item_budget_template` WHERE `template_id` = 12969;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12969, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12970;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12970, 5, 6250),
(12970, 6, 3750);

DELETE FROM `item_budget_template` WHERE `template_id` = 12971;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12971, 5, 7005),
(12971, 45, 2995);

DELETE FROM `item_budget_template` WHERE `template_id` = 12972;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12972, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12973;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12973, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12974;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12974, 3, 8500),
(12974, 31, 1500);

DELETE FROM `item_budget_template` WHERE `template_id` = 12975;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12975, 6, 7143),
(12975, 5, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 12976;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12976, 5, 3023),
(12976, 45, 6977);

DELETE FROM `item_budget_template` WHERE `template_id` = 12977;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12977, 3, 7778),
(12977, 38, 2222);

DELETE FROM `item_budget_template` WHERE `template_id` = 12978;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12978, 45, 7303),
(12978, 5, 2697);

DELETE FROM `item_budget_template` WHERE `template_id` = 12979;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12979, 4, 5000),
(12979, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12980;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12980, 3, 6087),
(12980, 4, 3913);

DELETE FROM `item_budget_template` WHERE `template_id` = 12981;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12981, 6, 7143),
(12981, 5, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 12982;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12982, 3, 7895),
(12982, 4, 2105);

DELETE FROM `item_budget_template` WHERE `template_id` = 12983;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12983, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12984;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12984, 3, 7143),
(12984, 6, 2857);

DELETE FROM `item_budget_template` WHERE `template_id` = 12985;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12985, 31, 6250),
(12985, 4, 3750);

DELETE FROM `item_budget_template` WHERE `template_id` = 12986;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12986, 3, 7200),
(12986, 31, 2800);

DELETE FROM `item_budget_template` WHERE `template_id` = 12987;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12987, 3, 3478),
(12987, 38, 6522);

DELETE FROM `item_budget_template` WHERE `template_id` = 12988;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12988, 4, 5000),
(12988, 32, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12989;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12989, 32, 5000),
(12989, 5, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12990;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12990, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12991;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12991, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12992;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12992, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12993;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12993, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12994;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12994, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12995;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12995, 4, 2414),
(12995, 6, 2758),
(12995, 5, 2414),
(12995, 3, 2414);

DELETE FROM `item_budget_template` WHERE `template_id` = 12996;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12996, 3, 7273),
(12996, 4, 2727);

DELETE FROM `item_budget_template` WHERE `template_id` = 12997;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12997, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 12998;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12998, 4, 7059),
(12998, 6, 2941);

DELETE FROM `item_budget_template` WHERE `template_id` = 12999;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(12999, 5, 3448),
(12999, 45, 6552);

DELETE FROM `item_budget_template` WHERE `template_id` = 13000;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13000, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13001;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13001, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13002;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13002, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13003;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13003, 32, 6774),
(13003, 31, 3226);

DELETE FROM `item_budget_template` WHERE `template_id` = 13004;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13004, 31, 5385),
(13004, 3, 4615);

DELETE FROM `item_budget_template` WHERE `template_id` = 13005;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13005, 32, 6957),
(13005, 5, 3043);

DELETE FROM `item_budget_template` WHERE `template_id` = 13006;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13006, 5, 5000),
(13006, 32, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13007;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13007, 5, 3684),
(13007, 32, 6316);

DELETE FROM `item_budget_template` WHERE `template_id` = 13008;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13008, 3, 6296),
(13008, 5, 3704);

DELETE FROM `item_budget_template` WHERE `template_id` = 13009;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13009, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13010;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13010, 3, 2500),
(13010, 6, 2500),
(13010, 4, 2500),
(13010, 5, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 13011;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13011, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13012;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13012, 4, 2632),
(13012, 6, 2368),
(13012, 5, 2632),
(13012, 3, 2368);

DELETE FROM `item_budget_template` WHERE `template_id` = 13013;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13013, 4, 6786),
(13013, 12, 3214);

DELETE FROM `item_budget_template` WHERE `template_id` = 13014;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13014, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13015;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13015, 4, 3000),
(13015, 32, 7000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13016;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13016, 3, 6071),
(13016, 5, 3929);

DELETE FROM `item_budget_template` WHERE `template_id` = 13017;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13017, 6, 3704),
(13017, 5, 6296);

DELETE FROM `item_budget_template` WHERE `template_id` = 13018;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13018, 31, 5882),
(13018, 32, 4118);

DELETE FROM `item_budget_template` WHERE `template_id` = 13019;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13019, 4, 7368),
(13019, 12, 2632);

DELETE FROM `item_budget_template` WHERE `template_id` = 13020;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13020, 5, 2984),
(13020, 45, 7016);

DELETE FROM `item_budget_template` WHERE `template_id` = 13021;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13021, 6, 6000),
(13021, 5, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13022;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13022, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13023;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13023, 6, 2696),
(13023, 5, 2695),
(13023, 45, 4609);

DELETE FROM `item_budget_template` WHERE `template_id` = 13024;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13024, 3, 5000),
(13024, 4, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13025;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13025, 5, 5000),
(13025, 32, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13026;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13026, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13027;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13027, 3, 3684),
(13027, 13, 6316);

DELETE FROM `item_budget_template` WHERE `template_id` = 13028;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13028, 3, 5556),
(13028, 31, 4444);

DELETE FROM `item_budget_template` WHERE `template_id` = 13029;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13029, 31, 5278),
(13029, 37, 4722);

DELETE FROM `item_budget_template` WHERE `template_id` = 13030;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13030, 6, 4000),
(13030, 12, 6000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13031;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13031, 45, 6494),
(13031, 5, 3506);

DELETE FROM `item_budget_template` WHERE `template_id` = 13032;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13032, 45, 6310),
(13032, 5, 3690);

DELETE FROM `item_budget_template` WHERE `template_id` = 13033;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13033, 5, 6609),
(13033, 45, 3391);

DELETE FROM `item_budget_template` WHERE `template_id` = 13034;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13034, 5, 6182),
(13034, 45, 3818);

DELETE FROM `item_budget_template` WHERE `template_id` = 13035;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13035, 38, 6579),
(13035, 3, 3421);

DELETE FROM `item_budget_template` WHERE `template_id` = 13036;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13036, 32, 7000),
(13036, 13, 3000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13037;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13037, 32, 7000),
(13037, 13, 3000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13038;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13038, 32, 5385),
(13038, 13, 4615);

DELETE FROM `item_budget_template` WHERE `template_id` = 13039;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13039, 6, 6762),
(13039, 45, 3238);

DELETE FROM `item_budget_template` WHERE `template_id` = 13040;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13040, 45, 4062),
(13040, 5, 2969),
(13040, 6, 2969);

DELETE FROM `item_budget_template` WHERE `template_id` = 13041;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13041, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13042;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13042, 38, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13043;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13043, 38, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13044;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13044, 45, 6560),
(13044, 5, 3440);

DELETE FROM `item_budget_template` WHERE `template_id` = 13045;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13045, 45, 5448),
(13045, 5, 2731),
(13045, 6, 1821);

DELETE FROM `item_budget_template` WHERE `template_id` = 13046;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13046, 6, 4406),
(13046, 5, 2203),
(13046, 45, 3391);

DELETE FROM `item_budget_template` WHERE `template_id` = 13047;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13047, 5, 3277),
(13047, 45, 6723);

DELETE FROM `item_budget_template` WHERE `template_id` = 13048;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13048, 5, 3277),
(13048, 45, 6723);

DELETE FROM `item_budget_template` WHERE `template_id` = 13049;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13049, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13050;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13050, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13051;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13051, 38, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13052;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13052, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13053;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13053, 5, 5185),
(13053, 6, 4815);

DELETE FROM `item_budget_template` WHERE `template_id` = 13054;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13054, 5, 2500),
(13054, 6, 2500),
(13054, 4, 2500),
(13054, 3, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 13055;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13055, 6, 2500),
(13055, 5, 2500),
(13055, 3, 2500),
(13055, 4, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 13056;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13056, 5, 2500),
(13056, 6, 2500),
(13056, 4, 2500),
(13056, 3, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 13057;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13057, 5, 2500),
(13057, 6, 2500),
(13057, 4, 2500),
(13057, 3, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 13058;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13058, 32, 5455),
(13058, 31, 4545);

DELETE FROM `item_budget_template` WHERE `template_id` = 13059;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13059, 6, 6538),
(13059, 3, 3462);

DELETE FROM `item_budget_template` WHERE `template_id` = 13060;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13060, 5, 5000),
(13060, 6, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13061;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13061, 6, 4572),
(13061, 5, 2857),
(13061, 4, 2571);

DELETE FROM `item_budget_template` WHERE `template_id` = 13062;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13062, 5, 5152),
(13062, 4, 2727),
(13062, 6, 2121);

DELETE FROM `item_budget_template` WHERE `template_id` = 13063;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13063, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13064;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13064, 3, 3448),
(13064, 6, 3448),
(13064, 5, 3104);

DELETE FROM `item_budget_template` WHERE `template_id` = 13065;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13065, 31, 3056),
(13065, 3, 1944),
(13065, 5, 2500),
(13065, 38, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 13066;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13066, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13067;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13067, 6, 5000),
(13067, 5, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13068;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13068, 5, 7500),
(13068, 6, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 13069;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13069, 6, 5000),
(13069, 5, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13070;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13070, 5, 7778),
(13070, 6, 2222);

DELETE FROM `item_budget_template` WHERE `template_id` = 13071;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13071, 6, 6296),
(13071, 5, 3704);

DELETE FROM `item_budget_template` WHERE `template_id` = 13072;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13072, 6, 6296),
(13072, 5, 3704);

DELETE FROM `item_budget_template` WHERE `template_id` = 13073;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13073, 5, 6897),
(13073, 6, 3103);

DELETE FROM `item_budget_template` WHERE `template_id` = 13074;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13074, 5, 5000),
(13074, 6, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13075;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13075, 5, 6538),
(13075, 6, 3462);

DELETE FROM `item_budget_template` WHERE `template_id` = 13076;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13076, 5, 5882),
(13076, 6, 4118);

DELETE FROM `item_budget_template` WHERE `template_id` = 13077;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13077, 6, 5263),
(13077, 5, 4737);

DELETE FROM `item_budget_template` WHERE `template_id` = 13078;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13078, 6, 6087),
(13078, 5, 3913);

DELETE FROM `item_budget_template` WHERE `template_id` = 13079;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13079, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13080;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13080, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13081;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13081, 3, 4243),
(13081, 38, 3030),
(13081, 31, 2727);

DELETE FROM `item_budget_template` WHERE `template_id` = 13082;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13082, 3, 4375),
(13082, 31, 2813),
(13082, 38, 2812);

DELETE FROM `item_budget_template` WHERE `template_id` = 13083;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13083, 5, 6818),
(13083, 4, 3182);

DELETE FROM `item_budget_template` WHERE `template_id` = 13084;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13084, 6, 6538),
(13084, 5, 3462);

DELETE FROM `item_budget_template` WHERE `template_id` = 13085;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13085, 5, 6296),
(13085, 6, 3704);

DELETE FROM `item_budget_template` WHERE `template_id` = 13086;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13086, 6, 7000),
(13086, 5, 3000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13087;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13087, 6, 4211),
(13087, 4, 3684),
(13087, 3, 2105);

DELETE FROM `item_budget_template` WHERE `template_id` = 13088;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13088, 5, 4839),
(13088, 6, 1935),
(13088, 4, 3226);

DELETE FROM `item_budget_template` WHERE `template_id` = 13089;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13089, 6, 5000),
(13089, 4, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13090;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13090, 6, 5294),
(13090, 4, 4706);

DELETE FROM `item_budget_template` WHERE `template_id` = 13091;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13091, 4, 5333),
(13091, 3, 2667),
(13091, 6, 2000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13092;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13092, 4, 5833),
(13092, 3, 2500),
(13092, 6, 1667);

DELETE FROM `item_budget_template` WHERE `template_id` = 13093;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13093, 4, 5600),
(13093, 3, 2800),
(13093, 6, 1600);

DELETE FROM `item_budget_template` WHERE `template_id` = 13094;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13094, 4, 6071),
(13094, 6, 2857),
(13094, 3, 1072);

DELETE FROM `item_budget_template` WHERE `template_id` = 13095;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13095, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13096;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13096, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13097;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13097, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13098;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13098, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13099;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13099, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13100;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13100, 5, 5294),
(13100, 6, 4706);

DELETE FROM `item_budget_template` WHERE `template_id` = 13101;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13101, 5, 5556),
(13101, 6, 4444);

DELETE FROM `item_budget_template` WHERE `template_id` = 13102;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13102, 6, 6667),
(13102, 5, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 13103;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13103, 6, 5000),
(13103, 5, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13104;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13104, 5, 5455),
(13104, 6, 4545);

DELETE FROM `item_budget_template` WHERE `template_id` = 13105;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13105, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13106;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13106, 45, 3439),
(13106, 5, 3598),
(13106, 6, 2963);

DELETE FROM `item_budget_template` WHERE `template_id` = 13107;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13107, 5, 6250),
(13107, 6, 3750);

DELETE FROM `item_budget_template` WHERE `template_id` = 13108;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13108, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13109;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13109, 4, 6667),
(13109, 32, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 13110;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13110, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13111;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13111, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13112;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13112, 5, 6452),
(13112, 6, 3548);

DELETE FROM `item_budget_template` WHERE `template_id` = 13113;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13113, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13114;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13114, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13115;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13115, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13116;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13116, 3, 8000),
(13116, 31, 2000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13117;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13117, 5, 6071),
(13117, 6, 3929);

DELETE FROM `item_budget_template` WHERE `template_id` = 13118;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13118, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13119;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13119, 12, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13120;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13120, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13121;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13121, 5, 3305),
(13121, 6, 3305),
(13121, 45, 3390);

DELETE FROM `item_budget_template` WHERE `template_id` = 13122;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13122, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13123;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13123, 5, 2439),
(13123, 45, 7561);

DELETE FROM `item_budget_template` WHERE `template_id` = 13124;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13124, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13125;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13125, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13126;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13126, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13127;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13127, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13128;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13128, 5, 3336),
(13128, 6, 3336),
(13128, 45, 3328);

DELETE FROM `item_budget_template` WHERE `template_id` = 13129;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13129, 3, 6154),
(13129, 4, 3846);

DELETE FROM `item_budget_template` WHERE `template_id` = 13130;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13130, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13131;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13131, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13132;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13132, 3, 5263),
(13132, 5, 2369),
(13132, 31, 2368);

DELETE FROM `item_budget_template` WHERE `template_id` = 13133;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13133, 5, 5938),
(13133, 45, 4062);

DELETE FROM `item_budget_template` WHERE `template_id` = 13134;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13134, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13135;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13135, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13136;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13136, 4, 3704),
(13136, 3, 6296);

DELETE FROM `item_budget_template` WHERE `template_id` = 13137;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13137, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13138;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13138, 5, 3577),
(13138, 45, 6423);

DELETE FROM `item_budget_template` WHERE `template_id` = 13139;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13139, 5, 5238),
(13139, 6, 4762);

DELETE FROM `item_budget_template` WHERE `template_id` = 13140;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13140, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13141;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13141, 5, 3339),
(13141, 45, 6661);

DELETE FROM `item_budget_template` WHERE `template_id` = 13142;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13142, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13143;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13143, 3, 5455),
(13143, 31, 4545);

DELETE FROM `item_budget_template` WHERE `template_id` = 13144;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13144, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13145;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13145, 4, 5000),
(13145, 14, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13146;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13146, 5, 5862),
(13146, 6, 4138);

DELETE FROM `item_budget_template` WHERE `template_id` = 13147;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13147, 5, 3448),
(13147, 45, 6552);

DELETE FROM `item_budget_template` WHERE `template_id` = 13148;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13148, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13149;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13149, 5, 6923),
(13149, 6, 3077);

DELETE FROM `item_budget_template` WHERE `template_id` = 13150;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13150, 4, 5200),
(13150, 5, 4800);

DELETE FROM `item_budget_template` WHERE `template_id` = 13151;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13151, 13, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13152;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13152, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13153;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13153, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13154;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13154, 5, 2593),
(13154, 6, 2222),
(13154, 32, 5185);

DELETE FROM `item_budget_template` WHERE `template_id` = 13155;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13155, 5, 5982),
(13155, 45, 4018);

DELETE FROM `item_budget_template` WHERE `template_id` = 13156;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13156, 3, 5000),
(13156, 32, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13157;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13157, 5, 2946),
(13157, 45, 7054);

DELETE FROM `item_budget_template` WHERE `template_id` = 13158;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13158, 5, 1798),
(13158, 6, 1798),
(13158, 45, 6404);

DELETE FROM `item_budget_template` WHERE `template_id` = 13159;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13159, 3, 2308),
(13159, 31, 7692);

DELETE FROM `item_budget_template` WHERE `template_id` = 13160;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13160, 4, 6500),
(13160, 32, 3500);

DELETE FROM `item_budget_template` WHERE `template_id` = 13161;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13161, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13162;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13162, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13163;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13163, 5, 3968),
(13163, 45, 6032);

DELETE FROM `item_budget_template` WHERE `template_id` = 13164;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13164, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13165;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13165, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13166;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13166, 5, 5000),
(13166, 36, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13167;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13167, 4, 5000),
(13167, 13, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13168;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13168, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13169;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13169, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13170;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13170, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13171;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13171, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13172;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13172, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13173;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13173, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13174;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13174, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13175;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13175, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13176;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13176, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13177;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13177, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13178;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13178, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13179;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13179, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13180;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13180, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13181;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13181, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13182;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13182, 6, 4545),
(13182, 5, 5455);

DELETE FROM `item_budget_template` WHERE `template_id` = 13183;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13183, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13184;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13184, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13185;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13185, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13186;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13186, 5, 6000),
(13186, 6, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13187;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13187, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13188;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13188, 4, 3549),
(13188, 5, 3548),
(13188, 6, 2903);

DELETE FROM `item_budget_template` WHERE `template_id` = 13189;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13189, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13190;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13190, 3, 5000),
(13190, 31, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13191;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13191, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13192;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13192, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13193;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13193, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13194;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13194, 6, 3000),
(13194, 32, 7000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13195;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13195, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13196;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13196, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13197;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13197, 5, 1921),
(13197, 6, 1921),
(13197, 45, 6158);

DELETE FROM `item_budget_template` WHERE `template_id` = 13198;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13198, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13199;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13199, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13200;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13200, 5, 4422),
(13200, 6, 2792),
(13200, 45, 2786);

DELETE FROM `item_budget_template` WHERE `template_id` = 13201;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13201, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13202;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13202, 38, 5000),
(13202, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13203;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13203, 38, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13204;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13204, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13205;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13205, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13206;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13206, 31, 6111),
(13206, 3, 3889);

DELETE FROM `item_budget_template` WHERE `template_id` = 13207;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13207, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13208;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13208, 6, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13209;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13209, 5, 4673),
(13209, 45, 5327);

DELETE FROM `item_budget_template` WHERE `template_id` = 13210;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13210, 3, 6000),
(13210, 4, 4000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13211;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13211, 5, 4974),
(13211, 45, 5026);

DELETE FROM `item_budget_template` WHERE `template_id` = 13212;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13212, 38, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13213;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13213, 4, 5263),
(13213, 3, 4737);

DELETE FROM `item_budget_template` WHERE `template_id` = 13214;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13214, 4, 5000),
(13214, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13215;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13215, 4, 5000),
(13215, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13216;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13216, 4, 5000),
(13216, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13217;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13217, 4, 5263),
(13217, 3, 4737);

DELETE FROM `item_budget_template` WHERE `template_id` = 13218;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13218, 4, 5000),
(13218, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13219;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13219, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13220;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13220, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13221;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13221, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13222;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13222, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13223;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13223, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13224;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13224, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13225;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13225, 6, 3690),
(13225, 45, 6310);

DELETE FROM `item_budget_template` WHERE `template_id` = 13226;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13226, 6, 3939),
(13226, 45, 6061);

DELETE FROM `item_budget_template` WHERE `template_id` = 13227;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13227, 6, 4006),
(13227, 45, 5994);

DELETE FROM `item_budget_template` WHERE `template_id` = 13228;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13228, 6, 3690),
(13228, 45, 6310);

DELETE FROM `item_budget_template` WHERE `template_id` = 13229;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13229, 6, 3939),
(13229, 45, 6061);

DELETE FROM `item_budget_template` WHERE `template_id` = 13230;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13230, 6, 4006),
(13230, 45, 5994);

DELETE FROM `item_budget_template` WHERE `template_id` = 13231;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13231, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13232;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13232, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13233;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13233, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13234;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13234, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13235;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13235, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13236;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13236, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13237;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13237, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13238;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13238, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13239;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13239, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13240;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13240, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13241;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13241, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13242;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13242, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13243;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13243, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13244;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13244, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13245;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13245, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13246;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13246, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13247;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13247, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13248;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13248, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13249;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13249, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13250;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13250, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13251;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13251, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13252;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13252, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13253;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13253, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13254;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13254, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13255;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13255, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13256;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13256, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13257;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13257, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13258;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13258, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13259;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13259, 4, 7083),
(13259, 3, 2917);

DELETE FROM `item_budget_template` WHERE `template_id` = 13260;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13260, 4, 7000),
(13260, 3, 3000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13261;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13261, 5, 5000),
(13261, 6, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13262;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13262, 5, 5455),
(13262, 6, 4545);

DELETE FROM `item_budget_template` WHERE `template_id` = 13263;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13263, 3, 6538),
(13263, 4, 3462);

DELETE FROM `item_budget_template` WHERE `template_id` = 13264;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13264, 3, 6364),
(13264, 4, 3636);

DELETE FROM `item_budget_template` WHERE `template_id` = 13265;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13265, 5, 2062),
(13265, 6, 2062),
(13265, 45, 5876);

DELETE FROM `item_budget_template` WHERE `template_id` = 13266;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13266, 5, 2431),
(13266, 6, 2026),
(13266, 45, 5543);

DELETE FROM `item_budget_template` WHERE `template_id` = 13267;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13267, 3, 5833),
(13267, 31, 4167);

DELETE FROM `item_budget_template` WHERE `template_id` = 13268;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13268, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13269;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13269, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13270;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13270, 3, 2857),
(13270, 31, 7143);

DELETE FROM `item_budget_template` WHERE `template_id` = 13271;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13271, 3, 3077),
(13271, 37, 6923);

DELETE FROM `item_budget_template` WHERE `template_id` = 13272;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13272, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13273;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13273, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13274;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13274, 5, 3049),
(13274, 45, 6951);

DELETE FROM `item_budget_template` WHERE `template_id` = 13275;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13275, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13276;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13276, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13277;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13277, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13278;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13278, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13279;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13279, 3, 5714),
(13279, 5, 4286);

DELETE FROM `item_budget_template` WHERE `template_id` = 13280;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13280, 3, 7000),
(13280, 5, 3000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13281;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13281, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13282;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13282, 5, 4381),
(13282, 45, 5619);

DELETE FROM `item_budget_template` WHERE `template_id` = 13283;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13283, 5, 3049),
(13283, 45, 6951);

DELETE FROM `item_budget_template` WHERE `template_id` = 13284;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13284, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13285;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13285, 5, 1873),
(13285, 32, 5244),
(13285, 45, 2883);

DELETE FROM `item_budget_template` WHERE `template_id` = 13286;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13286, 5, 2505),
(13286, 45, 7495);

DELETE FROM `item_budget_template` WHERE `template_id` = 13287;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13287, 5, 2418),
(13287, 45, 7582);

DELETE FROM `item_budget_template` WHERE `template_id` = 13288;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13288, 3, 5333),
(13288, 5, 4667);

DELETE FROM `item_budget_template` WHERE `template_id` = 13289;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13289, 3, 5455),
(13289, 5, 4545);

DELETE FROM `item_budget_template` WHERE `template_id` = 13290;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13290, 3, 5556),
(13290, 5, 4444);

DELETE FROM `item_budget_template` WHERE `template_id` = 13291;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13291, 5, 4167),
(13291, 32, 5833);

DELETE FROM `item_budget_template` WHERE `template_id` = 13292;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13292, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13293;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13293, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13294;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13294, 4, 3333),
(13294, 5, 2424),
(13294, 32, 4243);

DELETE FROM `item_budget_template` WHERE `template_id` = 13295;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13295, 4, 6667),
(13295, 5, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 13296;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13296, 4, 6875),
(13296, 5, 3125);

DELETE FROM `item_budget_template` WHERE `template_id` = 13297;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13297, 4, 4074),
(13297, 3, 3704),
(13297, 5, 2222);

DELETE FROM `item_budget_template` WHERE `template_id` = 13298;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13298, 4, 3810),
(13298, 3, 3809),
(13298, 5, 2381);

DELETE FROM `item_budget_template` WHERE `template_id` = 13299;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13299, 4, 3750),
(13299, 3, 3750),
(13299, 5, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 13300;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13300, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13301;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13301, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13302;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13302, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13303;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13303, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13304;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13304, 5, 4167),
(13304, 32, 5833);

DELETE FROM `item_budget_template` WHERE `template_id` = 13305;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13305, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13306;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13306, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13307;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13307, 3, 5714),
(13307, 5, 4286);

DELETE FROM `item_budget_template` WHERE `template_id` = 13308;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13308, 3, 7000),
(13308, 5, 3000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13309;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13309, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13310;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13310, 4, 4167),
(13310, 32, 5833);

DELETE FROM `item_budget_template` WHERE `template_id` = 13311;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13311, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13312;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13312, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13313;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13313, 4, 5238),
(13313, 3, 4762);

DELETE FROM `item_budget_template` WHERE `template_id` = 13314;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13314, 4, 5000),
(13314, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13315;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13315, 4, 5000),
(13315, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13316;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13316, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13317;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13317, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13318;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13318, 3, 5714),
(13318, 5, 4286);

DELETE FROM `item_budget_template` WHERE `template_id` = 13319;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13319, 3, 7000),
(13319, 5, 3000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13320;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13320, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13321;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13321, 5, 4381),
(13321, 45, 5619);

DELETE FROM `item_budget_template` WHERE `template_id` = 13322;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13322, 5, 3049),
(13322, 45, 6951);

DELETE FROM `item_budget_template` WHERE `template_id` = 13323;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13323, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13324;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13324, 5, 2418),
(13324, 45, 7582);

DELETE FROM `item_budget_template` WHERE `template_id` = 13325;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13325, 5, 1873),
(13325, 32, 5244),
(13325, 45, 2883);

DELETE FROM `item_budget_template` WHERE `template_id` = 13326;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13326, 5, 2505),
(13326, 45, 7495);

DELETE FROM `item_budget_template` WHERE `template_id` = 13327;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13327, 3, 5455),
(13327, 5, 4545);

DELETE FROM `item_budget_template` WHERE `template_id` = 13328;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13328, 3, 5556),
(13328, 5, 4444);

DELETE FROM `item_budget_template` WHERE `template_id` = 13329;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13329, 3, 5333),
(13329, 5, 4667);

DELETE FROM `item_budget_template` WHERE `template_id` = 13330;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13330, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13331;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13331, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13332;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13332, 5, 4167),
(13332, 32, 5833);

DELETE FROM `item_budget_template` WHERE `template_id` = 13333;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13333, 4, 6875),
(13333, 5, 3125);

DELETE FROM `item_budget_template` WHERE `template_id` = 13334;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13334, 4, 3333),
(13334, 5, 2424),
(13334, 32, 4243);

DELETE FROM `item_budget_template` WHERE `template_id` = 13335;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13335, 4, 6667),
(13335, 5, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 13336;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13336, 4, 3750),
(13336, 3, 3750),
(13336, 5, 2500);

DELETE FROM `item_budget_template` WHERE `template_id` = 13337;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13337, 4, 3810),
(13337, 3, 3809),
(13337, 5, 2381);

DELETE FROM `item_budget_template` WHERE `template_id` = 13338;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13338, 4, 4074),
(13338, 3, 3704),
(13338, 5, 2222);

DELETE FROM `item_budget_template` WHERE `template_id` = 13339;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13339, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13340;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13340, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13341;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13341, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13342;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13342, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13343;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13343, 5, 4167),
(13343, 32, 5833);

DELETE FROM `item_budget_template` WHERE `template_id` = 13344;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13344, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13345;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13345, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13346;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13346, 3, 7000),
(13346, 5, 3000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13347;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13347, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13348;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13348, 3, 5714),
(13348, 5, 4286);

DELETE FROM `item_budget_template` WHERE `template_id` = 13349;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13349, 4, 4167),
(13349, 32, 5833);

DELETE FROM `item_budget_template` WHERE `template_id` = 13350;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13350, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13351;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13351, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13352;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13352, 4, 5000),
(13352, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13353;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13353, 4, 5000),
(13353, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13354;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13354, 4, 5238),
(13354, 3, 4762);

DELETE FROM `item_budget_template` WHERE `template_id` = 13355;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13355, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13356;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13356, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13357;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13357, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13358;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13358, 45, 6423),
(13358, 5, 3577);

DELETE FROM `item_budget_template` WHERE `template_id` = 13359;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13359, 3, 1818),
(13359, 5, 2121),
(13359, 6, 1818),
(13359, 32, 4243);

DELETE FROM `item_budget_template` WHERE `template_id` = 13360;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13360, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13361;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13361, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13362;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13362, 6, 3187),
(13362, 45, 6813);

DELETE FROM `item_budget_template` WHERE `template_id` = 13363;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13363, 6, 3187),
(13363, 45, 6813);

DELETE FROM `item_budget_template` WHERE `template_id` = 13364;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13364, 4, 5000),
(13364, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13365;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13365, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13366;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13366, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13367;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13367, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13368;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13368, 4, 5000),
(13368, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13369;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13369, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13370;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13370, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13371;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13371, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13372;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13372, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13373;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13373, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13374;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13374, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13375;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13375, 4, 4474),
(13375, 45, 5526);

DELETE FROM `item_budget_template` WHERE `template_id` = 13376;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13376, 4, 3359),
(13376, 5, 3359),
(13376, 45, 3282);

DELETE FROM `item_budget_template` WHERE `template_id` = 13377;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13377, 4, 3334),
(13377, 3, 3333),
(13377, 31, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 13378;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13378, 4, 4286),
(13378, 32, 3333),
(13378, 31, 2381);

DELETE FROM `item_budget_template` WHERE `template_id` = 13379;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13379, 4, 5152),
(13379, 3, 4848);

DELETE FROM `item_budget_template` WHERE `template_id` = 13380;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13380, 5, 6667),
(13380, 6, 3333);

DELETE FROM `item_budget_template` WHERE `template_id` = 13381;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13381, 5, 3810),
(13381, 45, 6190);

DELETE FROM `item_budget_template` WHERE `template_id` = 13382;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13382, 31, 3187),
(13382, 45, 6813);

DELETE FROM `item_budget_template` WHERE `template_id` = 13383;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13383, 4, 2326),
(13383, 5, 2093),
(13383, 31, 2325),
(13383, 32, 3256);

DELETE FROM `item_budget_template` WHERE `template_id` = 13384;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13384, 5, 2262),
(13384, 45, 7738);

DELETE FROM `item_budget_template` WHERE `template_id` = 13385;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13385, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13386;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13386, 5, 2882),
(13386, 45, 7118);

DELETE FROM `item_budget_template` WHERE `template_id` = 13387;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13387, 32, 6552),
(13387, 31, 3448);

DELETE FROM `item_budget_template` WHERE `template_id` = 13388;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13388, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13389;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13389, 45, 6469),
(13389, 32, 3531);

DELETE FROM `item_budget_template` WHERE `template_id` = 13390;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13390, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13391;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13391, 4, 5882),
(13391, 3, 4118);

DELETE FROM `item_budget_template` WHERE `template_id` = 13392;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13392, 32, 5000),
(13392, 4, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13393;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13393, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13394;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13394, 4, 4688),
(13394, 3, 5312);

DELETE FROM `item_budget_template` WHERE `template_id` = 13395;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13395, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13396;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13396, 5, 4789),
(13396, 45, 5211);

DELETE FROM `item_budget_template` WHERE `template_id` = 13397;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13397, 5, 3649),
(13397, 45, 3432),
(13397, 31, 2919);

DELETE FROM `item_budget_template` WHERE `template_id` = 13398;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13398, 3, 6071),
(13398, 4, 3929);

DELETE FROM `item_budget_template` WHERE `template_id` = 13399;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13399, 3, 5000),
(13399, 5, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13400;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13400, 5, 2778),
(13400, 6, 4320),
(13400, 45, 2902);

DELETE FROM `item_budget_template` WHERE `template_id` = 13401;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13401, 5, 5839),
(13401, 45, 4161);

DELETE FROM `item_budget_template` WHERE `template_id` = 13402;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13402, 3, 6316),
(13402, 4, 3684);

DELETE FROM `item_budget_template` WHERE `template_id` = 13403;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13403, 5, 3472),
(13403, 6, 2210),
(13403, 45, 4318);

DELETE FROM `item_budget_template` WHERE `template_id` = 13404;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13404, 5, 3663),
(13404, 6, 3205),
(13404, 45, 3132);

DELETE FROM `item_budget_template` WHERE `template_id` = 13405;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13405, 5, 2946),
(13405, 45, 7054);

DELETE FROM `item_budget_template` WHERE `template_id` = 13406;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13406, 4, 3793),
(13406, 31, 2759),
(13406, 3, 3448);

DELETE FROM `item_budget_template` WHERE `template_id` = 13407;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13407, 5, 5230),
(13407, 45, 4770);

DELETE FROM `item_budget_template` WHERE `template_id` = 13408;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13408, 5, 2010),
(13408, 6, 1759),
(13408, 45, 6231);

DELETE FROM `item_budget_template` WHERE `template_id` = 13409;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13409, 5, 5172),
(13409, 32, 4828);

DELETE FROM `item_budget_template` WHERE `template_id` = 13410;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13410, 4, 5152),
(13410, 3, 4848);

DELETE FROM `item_budget_template` WHERE `template_id` = 13411;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13411, 5, 6568),
(13411, 45, 3432);

DELETE FROM `item_budget_template` WHERE `template_id` = 13412;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13412, 45, 5236),
(13412, 32, 4764);

DELETE FROM `item_budget_template` WHERE `template_id` = 13413;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13413, 6, 2857),
(13413, 5, 7143);

DELETE FROM `item_budget_template` WHERE `template_id` = 13414;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13414, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13415;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13415, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13416;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13416, 5, 5006),
(13416, 45, 4994);

DELETE FROM `item_budget_template` WHERE `template_id` = 13417;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13417, 4, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13418;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13418, 5, 5097),
(13418, 45, 4903);

DELETE FROM `item_budget_template` WHERE `template_id` = 13419;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13419, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13420;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13420, 5, 5391),
(13420, 45, 4609);

DELETE FROM `item_budget_template` WHERE `template_id` = 13421;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13421, 4, 5333),
(13421, 32, 4667);

DELETE FROM `item_budget_template` WHERE `template_id` = 13422;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13422, 5, 3305),
(13422, 6, 3305),
(13422, 45, 3390);

DELETE FROM `item_budget_template` WHERE `template_id` = 13423;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13423, 4, 5000),
(13423, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13424;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13424, 3, 5652),
(13424, 31, 4348);

DELETE FROM `item_budget_template` WHERE `template_id` = 13425;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13425, 5, 2686),
(13425, 6, 2930),
(13425, 45, 4384);

DELETE FROM `item_budget_template` WHERE `template_id` = 13426;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13426, 32, 5217),
(13426, 5, 4783);

DELETE FROM `item_budget_template` WHERE `template_id` = 13427;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13427, 4, 6154),
(13427, 32, 3846);

DELETE FROM `item_budget_template` WHERE `template_id` = 13428;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13428, 3, 3556),
(13428, 38, 3556),
(13428, 31, 1555),
(13428, 5, 1333);

DELETE FROM `item_budget_template` WHERE `template_id` = 13429;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13429, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13430;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13430, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13431;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13431, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13432;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13432, 5, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13433;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13433, 13, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13434;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13434, 5, 4936),
(13434, 45, 5064);

DELETE FROM `item_budget_template` WHERE `template_id` = 13435;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13435, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13436;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13436, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13437;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13437, 32, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13438;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13438, 3, 6111),
(13438, 5, 3889);

DELETE FROM `item_budget_template` WHERE `template_id` = 13439;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13439, 4, 5455),
(13439, 32, 4545);

DELETE FROM `item_budget_template` WHERE `template_id` = 13440;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13440, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13441;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13441, 45, 4609),
(13441, 5, 5391);

DELETE FROM `item_budget_template` WHERE `template_id` = 13442;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13442, 32, 5455),
(13442, 31, 4545);

DELETE FROM `item_budget_template` WHERE `template_id` = 13443;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13443, 36, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13444;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13444, 45, 5327),
(13444, 32, 4673);

DELETE FROM `item_budget_template` WHERE `template_id` = 13445;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13445, 31, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13446;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13446, 45, 3506),
(13446, 32, 3076),
(13446, 5, 3418);

DELETE FROM `item_budget_template` WHERE `template_id` = 13447;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13447, 45, 3630),
(13447, 6, 3185),
(13447, 5, 3185);

DELETE FROM `item_budget_template` WHERE `template_id` = 13448;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13448, 38, 5000),
(13448, 3, 5000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13449;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13449, 45, 4903),
(13449, 32, 3186),
(13449, 5, 1911);

DELETE FROM `item_budget_template` WHERE `template_id` = 13450;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13450, 3, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13451;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13451, 38, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13452;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13452, 45, 10000);

DELETE FROM `item_budget_template` WHERE `template_id` = 13453;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13453, 31, 5391),
(13453, 45, 4609);

DELETE FROM `item_budget_template` WHERE `template_id` = 13454;
INSERT INTO `item_budget_template` (`template_id`, `stat_type`, `alloc`) VALUES
(13454, 31, 10000);

DELETE FROM `item_budget_template_name` WHERE `template_id` IN (
  12366, 12367, 12368, 12369, 12370, 12371, 12372, 12373, 12374, 12375, 12376, 12377, 12378, 12379, 12380,
  12381, 12382, 12383, 12384, 12385, 12386, 12387, 12388, 12389, 12390, 12391, 12392, 12393, 12394, 12395,
  12396, 12397, 12398, 12399, 12400, 12401, 12402, 12403, 12404, 12405, 12406, 12407, 12408, 12409, 12410,
  12411, 12412, 12413, 12414, 12415, 12416, 12417, 12418, 12419, 12420, 12421, 12422, 12423, 12424, 12425,
  12426, 12427, 12428, 12429, 12430, 12431, 12432, 12433, 12434, 12435, 12436, 12437, 12438, 12439, 12440,
  12441, 12442, 12443, 12444, 12445, 12446, 12447, 12448, 12449, 12450, 12451, 12452, 12453, 12454, 12455,
  12456, 12457, 12458, 12459, 12460, 12461, 12462, 12463, 12464, 12465, 12466, 12467, 12468, 12469, 12470,
  12471, 12472, 12473, 12474, 12475, 12476, 12477, 12478, 12479, 12480, 12481, 12482, 12483, 12484, 12485,
  12486, 12487, 12488, 12489, 12490, 12491, 12492, 12493, 12494, 12495, 12496, 12497, 12498, 12499, 12500,
  12501, 12502, 12503, 12504, 12505, 12506, 12507, 12508, 12509, 12510, 12511, 12512, 12513, 12514, 12515,
  12516, 12517, 12518, 12519, 12520, 12521, 12522, 12523, 12524, 12525, 12526, 12527, 12528, 12529, 12530,
  12531, 12532, 12533, 12534, 12535, 12536, 12537, 12538, 12539, 12540, 12541, 12542, 12543, 12544, 12545,
  12546, 12547, 12548, 12549, 12550, 12551, 12552, 12553, 12554, 12555, 12556, 12557, 12558, 12559, 12560,
  12561, 12562, 12563, 12564, 12565, 12566, 12567, 12568, 12569, 12570, 12571, 12572, 12573, 12574, 12575,
  12576, 12577, 12578, 12579, 12580, 12581, 12582, 12583, 12584, 12585, 12586, 12587, 12588, 12589, 12590,
  12591, 12592, 12593, 12594, 12595, 12596, 12597, 12598, 12599, 12600, 12601, 12602, 12603, 12604, 12605,
  12606, 12607, 12608, 12609, 12610, 12611, 12612, 12613, 12614, 12615, 12616, 12617, 12618, 12619, 12620,
  12621, 12622, 12623, 12624, 12625, 12626, 12627, 12628, 12629, 12630, 12631, 12632, 12633, 12634, 12635,
  12636, 12637, 12638, 12639, 12640, 12641, 12642, 12643, 12644, 12645, 12646, 12647, 12648, 12649, 12650,
  12651, 12652, 12653, 12654, 12655, 12656, 12657, 12658, 12659, 12660, 12661, 12662, 12663, 12664, 12665,
  12666, 12667, 12668, 12669, 12670, 12671, 12672, 12673, 12674, 12675, 12676, 12677, 12678, 12679, 12680,
  12681, 12682, 12683, 12684, 12685, 12686, 12687, 12688, 12689, 12690, 12691, 12692, 12693, 12694, 12695,
  12696, 12697, 12698, 12699, 12700, 12701, 12702, 12703, 12704, 12705, 12706, 12707, 12708, 12709, 12710,
  12711, 12712, 12713, 12714, 12715, 12716, 12717, 12718, 12719, 12720, 12721, 12722, 12723, 12724, 12725,
  12726, 12727, 12728, 12729, 12730, 12731, 12732, 12733, 12734, 12735, 12736, 12737, 12738, 12739, 12740,
  12741, 12742, 12743, 12744, 12745, 12746, 12747, 12748, 12749, 12750, 12751, 12752, 12753, 12754, 12755,
  12756, 12757, 12758, 12759, 12760, 12761, 12762, 12763, 12764, 12765, 12766, 12767, 12768, 12769, 12770,
  12771, 12772, 12773, 12774, 12775, 12776, 12777, 12778, 12779, 12780, 12781, 12782, 12783, 12784, 12785,
  12786, 12787, 12788, 12789, 12790, 12791, 12792, 12793, 12794, 12795, 12796, 12797, 12798, 12799, 12800,
  12801, 12802, 12803, 12804, 12805, 12806, 12807, 12808, 12809, 12810, 12811, 12812, 12813, 12814, 12815,
  12816, 12817, 12818, 12819, 12820, 12821, 12822, 12823, 12824, 12825, 12826, 12827, 12828, 12829, 12830,
  12831, 12832, 12833, 12834, 12835, 12836, 12837, 12838, 12839, 12840, 12841, 12842, 12843, 12844, 12845,
  12846, 12847, 12848, 12849, 12850, 12851, 12852, 12853, 12854, 12855, 12856, 12857, 12858, 12859, 12860,
  12861, 12862, 12863, 12864, 12865, 12866, 12867, 12868, 12869, 12870, 12871, 12872, 12873, 12874, 12875,
  12876, 12877, 12878, 12879, 12880, 12881, 12882, 12883, 12884, 12885, 12886, 12887, 12888, 12889, 12890,
  12891, 12892, 12893, 12894, 12895, 12896, 12897, 12898, 12899, 12900, 12901, 12902, 12903, 12904, 12905,
  12906, 12907, 12908, 12909, 12910, 12911, 12912, 12913, 12914, 12915, 12916, 12917, 12918, 12919, 12920,
  12921, 12922, 12923, 12924, 12925, 12926, 12927, 12928, 12929, 12930, 12931, 12932, 12933, 12934, 12935,
  12936, 12937, 12938, 12939, 12940, 12941, 12942, 12943, 12944, 12945, 12946, 12947, 12948, 12949, 12950,
  12951, 12952, 12953, 12954, 12955, 12956, 12957, 12958, 12959, 12960, 12961, 12962, 12963, 12964, 12965,
  12966, 12967, 12968, 12969, 12970, 12971, 12972, 12973, 12974, 12975, 12976, 12977, 12978, 12979, 12980,
  12981, 12982, 12983, 12984, 12985, 12986, 12987, 12988, 12989, 12990, 12991, 12992, 12993, 12994, 12995,
  12996, 12997, 12998, 12999, 13000, 13001, 13002, 13003, 13004, 13005, 13006, 13007, 13008, 13009, 13010,
  13011, 13012, 13013, 13014, 13015, 13016, 13017, 13018, 13019, 13020, 13021, 13022, 13023, 13024, 13025,
  13026, 13027, 13028, 13029, 13030, 13031, 13032, 13033, 13034, 13035, 13036, 13037, 13038, 13039, 13040,
  13041, 13042, 13043, 13044, 13045, 13046, 13047, 13048, 13049, 13050, 13051, 13052, 13053, 13054, 13055,
  13056, 13057, 13058, 13059, 13060, 13061, 13062, 13063, 13064, 13065, 13066, 13067, 13068, 13069, 13070,
  13071, 13072, 13073, 13074, 13075, 13076, 13077, 13078, 13079, 13080, 13081, 13082, 13083, 13084, 13085,
  13086, 13087, 13088, 13089, 13090, 13091, 13092, 13093, 13094, 13095, 13096, 13097, 13098, 13099, 13100,
  13101, 13102, 13103, 13104, 13105, 13106, 13107, 13108, 13109, 13110, 13111, 13112, 13113, 13114, 13115,
  13116, 13117, 13118, 13119, 13120, 13121, 13122, 13123, 13124, 13125, 13126, 13127, 13128, 13129, 13130,
  13131, 13132, 13133, 13134, 13135, 13136, 13137, 13138, 13139, 13140, 13141, 13142, 13143, 13144, 13145,
  13146, 13147, 13148, 13149, 13150, 13151, 13152, 13153, 13154, 13155, 13156, 13157, 13158, 13159, 13160,
  13161, 13162, 13163, 13164, 13165, 13166, 13167, 13168, 13169, 13170, 13171, 13172, 13173, 13174, 13175,
  13176, 13177, 13178, 13179, 13180, 13181, 13182, 13183, 13184, 13185, 13186, 13187, 13188, 13189, 13190,
  13191, 13192, 13193, 13194, 13195, 13196, 13197, 13198, 13199, 13200, 13201, 13202, 13203, 13204, 13205,
  13206, 13207, 13208, 13209, 13210, 13211, 13212, 13213, 13214, 13215, 13216, 13217, 13218, 13219, 13220,
  13221, 13222, 13223, 13224, 13225, 13226, 13227, 13228, 13229, 13230, 13231, 13232, 13233, 13234, 13235,
  13236, 13237, 13238, 13239, 13240, 13241, 13242, 13243, 13244, 13245, 13246, 13247, 13248, 13249, 13250,
  13251, 13252, 13253, 13254, 13255, 13256, 13257, 13258, 13259, 13260, 13261, 13262, 13263, 13264, 13265,
  13266, 13267, 13268, 13269, 13270, 13271, 13272, 13273, 13274, 13275, 13276, 13277, 13278, 13279, 13280,
  13281, 13282, 13283, 13284, 13285, 13286, 13287, 13288, 13289, 13290, 13291, 13292, 13293, 13294, 13295,
  13296, 13297, 13298, 13299, 13300, 13301, 13302, 13303, 13304, 13305, 13306, 13307, 13308, 13309, 13310,
  13311, 13312, 13313, 13314, 13315, 13316, 13317, 13318, 13319, 13320, 13321, 13322, 13323, 13324, 13325,
  13326, 13327, 13328, 13329, 13330, 13331, 13332, 13333, 13334, 13335, 13336, 13337, 13338, 13339, 13340,
  13341, 13342, 13343, 13344, 13345, 13346, 13347, 13348, 13349, 13350, 13351, 13352, 13353, 13354, 13355,
  13356, 13357, 13358, 13359, 13360, 13361, 13362, 13363, 13364, 13365, 13366, 13367, 13368, 13369, 13370,
  13371, 13372, 13373, 13374, 13375, 13376, 13377, 13378, 13379, 13380, 13381, 13382, 13383, 13384, 13385,
  13386, 13387, 13388, 13389, 13390, 13391, 13392, 13393, 13394, 13395, 13396, 13397, 13398, 13399, 13400,
  13401, 13402, 13403, 13404, 13405, 13406, 13407, 13408, 13409, 13410, 13411, 13412, 13413, 13414, 13415,
  13416, 13417, 13418, 13419, 13420, 13421, 13422, 13423, 13424, 13425, 13426, 13427, 13428, 13429, 13430,
  13431, 13432, 13433, 13434, 13435, 13436, 13437, 13438, 13439, 13440, 13441, 13442, 13443, 13444, 13445,
  13446, 13447, 13448, 13449, 13450, 13451, 13452, 13453, 13454
);
INSERT INTO `item_budget_template_name` (`template_id`, `name`) VALUES
(12366, 'Brawler Gloves shape'),
(12367, 'Vendetta shape'),
(12368, 'Gnarled Ash Staff shape'),
(12369, 'Glowing Brightwood Staff shape'),
(12370, 'Runed Ring shape'),
(12371, 'Gloves of Holy Might shape'),
(12372, 'Ardent Custodian shape'),
(12373, 'Rockslicer shape'),
(12374, 'Staff of Jordan shape'),
(12375, 'Naga Battle Gloves shape'),
(12376, 'Twisted Chanter''s Staff shape'),
(12377, 'Robes of Insight shape'),
(12378, 'Freezing Band shape'),
(12379, 'Warden Staff shape'),
(12380, 'Feet of the Lynx shape'),
(12381, 'Rod of the Sleepwalker shape'),
(12382, 'Lavishly Jeweled Ring shape'),
(12383, 'Blackskull Shield shape'),
(12384, 'Aegis of Stormwind shape'),
(12385, 'The Green Tower shape'),
(12386, 'Butcher''s Cleaver shape'),
(12387, 'Lei of Lilies shape'),
(12388, 'Ring of Saviors shape'),
(12389, 'Axe of the Enforcer shape'),
(12390, 'Face Smasher shape'),
(12391, 'Witching Stave shape'),
(12392, 'Tree Bark Jacket shape'),
(12393, 'Avenger''s Armor shape'),
(12394, 'Gloomshroud Armor shape'),
(12395, 'Ring of Precision shape'),
(12396, 'Heavy Marauder Scimitar shape'),
(12397, 'Sickle Axe shape'),
(12398, 'Soulkeeper shape'),
(12399, 'Black Ogre Kickers shape'),
(12400, 'Necklace of Calisea shape'),
(12401, 'Polished Jazeraint Armor shape'),
(12402, 'Robe of the Magi shape'),
(12403, 'Double Link Tunic shape'),
(12404, 'Basilisk Hide Pants shape'),
(12405, 'Tanglewood Staff shape'),
(12406, 'Viking Warhammer shape'),
(12407, 'Thornstone Sledgehammer shape'),
(12408, 'Assassin''s Blade shape'),
(12409, 'Buzz Saw shape'),
(12410, 'Pysan''s Old Greatsword shape'),
(12411, 'Slaghammer shape'),
(12412, 'Wolfclaw Gloves shape'),
(12413, 'Wall of the Dead shape'),
(12414, 'Underworld Band shape'),
(12415, 'Icemail Jerkin shape'),
(12416, 'Swampchill Fetish shape'),
(12417, 'Twisted Sabre shape'),
(12418, 'Plains Ring shape'),
(12419, 'Troll Protector shape'),
(12420, 'Tunic of Westfall shape'),
(12421, 'Staff of Westfall shape'),
(12422, 'Crescent of Forlorn Spirits shape'),
(12423, 'Sentry Cloak shape'),
(12424, 'Precisely Calibrated Boomstick shape'),
(12425, 'Buzzer Blade shape'),
(12426, 'Diamond Hammer shape'),
(12427, 'Blackfang shape'),
(12428, 'Krol Blade shape'),
(12429, 'Helm of Narv shape'),
(12430, 'Myrmidon''s Signet shape'),
(12431, 'Mantle of Thieves shape'),
(12432, 'Staff of the Blessed Seer shape'),
(12433, 'Swampwalker Boots shape'),
(12434, 'Necromancer Leggings shape'),
(12435, 'Forest Tracker Epaulets shape'),
(12436, 'Kam''s Walking Stick shape'),
(12437, 'Necrology Robes shape'),
(12438, 'Staff of the Shade shape'),
(12439, 'Elven Spirit Claws shape'),
(12440, 'Rod of Molten Fire shape'),
(12441, 'Evocator''s Blade shape'),
(12442, 'Holy Shroud shape'),
(12443, 'Black Velvet Robes shape'),
(12444, 'Guillotine Axe shape'),
(12445, 'Curve-bladed Ripper shape'),
(12446, 'Death Speaker Scepter shape'),
(12447, 'Shining Silver Breastplate shape'),
(12448, 'Combatant Claymore shape'),
(12449, 'Bearded Boneaxe shape'),
(12450, 'Antipodean Rod shape'),
(12451, 'Keller''s Girdle shape'),
(12452, 'Claw of the Shadowmancer shape'),
(12453, 'Seal of Wrynn shape'),
(12454, 'Prison Shank shape'),
(12455, 'Ring of the Underwood shape'),
(12456, 'Enduring Cap shape'),
(12457, 'Ranger Bow shape'),
(12458, 'Eye of Flame shape'),
(12459, 'Naga Heartpiercer shape'),
(12460, 'Arced War Axe shape'),
(12461, 'Dense Triangle Mace shape'),
(12462, 'Jimmied Handcuffs shape'),
(12463, 'Doomspike shape'),
(12464, 'Crested Scepter shape'),
(12465, 'Staff of the Friar shape'),
(12466, 'Martyr''s Chain shape'),
(12467, 'Onyx Claymore shape'),
(12468, 'Feline Mantle shape'),
(12469, 'Green Iron Hauberk shape'),
(12470, 'Widowmaker shape'),
(12471, 'Robe of Crystal Waters shape'),
(12472, 'Nimboya''s Mystical Staff shape'),
(12473, 'Berylline Pads shape'),
(12474, 'Toughened Leather Gloves shape'),
(12475, 'Spidersilk Boots shape'),
(12476, 'Icy Cloak shape'),
(12477, 'Pugilist Bracers shape'),
(12478, 'Blackvenom Blade shape'),
(12479, 'Talon of Vultros shape'),
(12480, 'Pit Fighter''s Shield shape'),
(12481, 'Blood-tinged Armor shape'),
(12482, 'Pulsating Crystalline Shard shape'),
(12483, 'Vigilant Buckler shape'),
(12484, 'Pulsating Hydra Heart shape'),
(12485, 'Thief''s Blade shape'),
(12486, 'Cape of the Brotherhood shape'),
(12487, 'Taskmaster Axe shape'),
(12488, 'Gold-flecked Gloves shape'),
(12489, 'Smite''s Reaver shape'),
(12490, 'Cookie''s Tenderizer shape'),
(12491, 'Smelting Pants shape'),
(12492, 'Impaling Harpoon shape'),
(12493, 'Emberstone Staff shape'),
(12494, 'Corsair''s Overshirt shape'),
(12495, 'Rugged Spaulders shape'),
(12496, 'Dark Hooded Cape shape'),
(12497, 'Eye of Adaegus shape'),
(12498, 'Serpent''s Shoulders shape'),
(12499, 'Boahn''s Fang shape'),
(12500, 'Runescale Girdle shape'),
(12501, 'Gold-plated Buckler shape'),
(12502, 'Sunblaze Coif shape'),
(12503, 'Serpent Gloves shape'),
(12504, 'Chausses of Westfall shape'),
(12505, 'Wolfmaster Cape shape'),
(12506, 'Odo''s Ley Staff shape'),
(12507, 'Girdle of the Blindwatcher shape'),
(12508, 'Commander''s Crest shape'),
(12509, 'Silverlaine''s Family Seal shape'),
(12510, 'Baron''s Scepter shape'),
(12511, 'Robes of Arugal shape'),
(12512, 'The Pacifier shape'),
(12513, 'Black Pearl Ring shape'),
(12514, 'Fenrus'' Hide shape'),
(12515, 'Eerie Stable Lantern shape'),
(12516, 'Belt of Arugal shape'),
(12517, 'Seal of Sylvanas shape'),
(12518, 'Tail Spike shape'),
(12519, 'Glowing Lizardscale Cloak shape'),
(12520, 'Cobrahn''s Grasp shape'),
(12521, 'Deep Fathom Ring shape'),
(12522, 'Robe of the Moccasin shape'),
(12523, 'Deviate Scale Belt shape'),
(12524, 'Armor of the Fang shape'),
(12525, 'Wingblade shape'),
(12526, 'Crescent Staff shape'),
(12527, 'Mutant Scale Breastplate shape'),
(12528, 'Sporid Cape shape'),
(12529, 'Seedcloud Buckler shape'),
(12530, 'Living Root shape'),
(12531, 'Feyscale Cloak shape'),
(12532, 'Butcher''s Slicer shape'),
(12533, 'Phantom Armor shape'),
(12534, 'Armor Piercer shape'),
(12535, 'Thornspike shape'),
(12536, 'Death Speaker Robes shape'),
(12537, 'Death Speaker Mantle shape'),
(12538, 'Tusken Helm shape'),
(12539, 'Corpsemaker shape'),
(12540, 'Whisperwind Headdress shape'),
(12541, 'Wind Spirit Staff shape'),
(12542, 'Ferine Leggings shape'),
(12543, 'Swinetusk Shank shape'),
(12544, 'Pronged Reaver shape'),
(12545, 'Agamaggan''s Clutch shape'),
(12546, 'Heart of Agamaggan shape'),
(12547, 'Stygian Bone Amulet shape'),
(12548, 'Nightstalker Bow shape'),
(12549, 'Batwing Mantle shape'),
(12550, 'Marbled Buckler shape'),
(12551, 'Stonefist Girdle shape'),
(12552, 'Sword of Omen shape'),
(12553, 'Prophetic Cane shape'),
(12554, 'Windstorm Hammer shape'),
(12555, 'Sword of Serenity shape'),
(12556, 'Bonebiter shape'),
(12557, 'Enchanted Gold Bloodrobe shape'),
(12558, 'Glowing Thresher Cape shape'),
(12559, 'Bands of Serra''kis shape'),
(12560, 'Gaze Dreamer Pants shape'),
(12561, 'Algae Fists shape'),
(12562, 'Ghamoo-ra''s Bind shape'),
(12563, 'Leech Pants shape'),
(12564, 'Moss Cinch shape'),
(12565, 'Verigan''s Fist shape'),
(12566, 'Fire Hardened Hauberk shape'),
(12567, 'Whirlwind Axe shape'),
(12568, 'Whirlwind Warhammer shape'),
(12569, 'Whirlwind Sword shape'),
(12570, 'Gravestone Scepter shape'),
(12571, 'Arctic Buckler shape'),
(12572, 'Robe of Power shape'),
(12573, 'Brutal Hauberk shape'),
(12574, 'VanCleef''s Boots shape'),
(12575, 'Smite''s Mighty Hammer shape'),
(12576, 'Ragefire Wand shape'),
(12577, 'Icefury Wand shape'),
(12578, 'Celestial Orb shape'),
(12579, 'Talvash''s Enhancing Necklace shape'),
(12580, 'Bloody Brass Knuckles shape'),
(12581, 'Bloodmage Mantle shape'),
(12582, 'Orb of the Forgotten Seer shape'),
(12583, 'Ironspine''s Eye shape'),
(12584, 'Ironspine''s Fist shape'),
(12585, 'Ironspine''s Ribcage shape'),
(12586, 'Morbid Dawn shape'),
(12587, 'Ebon Vise shape'),
(12588, 'Embalmed Shroud shape'),
(12589, 'Blighted Leggings shape'),
(12590, 'Robe of Doan shape'),
(12591, 'Mantle of Doan shape'),
(12592, 'Illusionary Rod shape'),
(12593, 'Hypnotic Blade shape'),
(12594, 'Herod''s Shoulder shape'),
(12595, 'Raging Berserker''s Helm shape'),
(12596, 'Whitemane''s Chapeau shape'),
(12597, 'Hand of Righteousness shape'),
(12598, 'Triune Amulet shape'),
(12599, 'Mograine''s Might shape'),
(12600, 'Aegis of the Scarlet Commander shape'),
(12601, 'Watchman Pauldrons shape'),
(12602, 'Beguiler Robes shape'),
(12603, 'Ghostshard Talisman shape'),
(12604, 'Fight Club shape'),
(12605, 'Dreamslayer shape'),
(12606, 'Harbinger Boots shape'),
(12607, 'Flintrock Shoulders shape'),
(12608, 'Dog Training Gloves shape'),
(12609, 'Windweaver Staff shape'),
(12610, 'Ruthless Shiv shape'),
(12611, 'Archon Chestpiece shape'),
(12612, 'Warchief Kilt shape'),
(12613, 'Steelclaw Reaver shape'),
(12614, 'Headsplitter shape'),
(12615, 'Resplendent Guardian shape'),
(12616, 'Jarkal''s Enhancing Necklace shape'),
(12617, 'Steel Plate Helm shape'),
(12618, 'Truesilver Gauntlets shape'),
(12619, 'Comfortable Leather Hat shape'),
(12620, 'The Butcher shape'),
(12621, 'Wolfshead Helm shape'),
(12622, 'Gauntlets of the Sea shape'),
(12623, 'Dragonscale Gauntlets shape'),
(12624, 'Helm of Fire shape'),
(12625, 'Feathered Breastplate shape'),
(12626, 'Dragonscale Breastplate shape'),
(12627, 'Mallet of Zul''Farrak shape'),
(12628, 'Wirt''s Third Leg shape'),
(12629, 'Expert Goldminer''s Helmet shape'),
(12630, 'Shovelphlange''s Mining Axe shape'),
(12631, 'Sang''thraze the Deflector shape'),
(12632, 'Obsidian Cleaver shape'),
(12633, 'Stonevault Shiv shape'),
(12634, 'Archaic Defender shape'),
(12635, 'Annealed Blade shape'),
(12636, 'Beacon of Hope shape'),
(12637, 'Horned Viking Helmet shape'),
(12638, 'Gloves of Old shape'),
(12639, 'Legguards of the Vault shape'),
(12640, 'Energy Cloak shape'),
(12641, 'Worn Running Boots shape'),
(12642, 'Baelog''s Shortbow shape'),
(12643, 'Nordic Longshank shape'),
(12644, 'Battered Viking Shield shape'),
(12645, 'Girdle of Golem Strength shape'),
(12646, 'Spirewind Fetter shape'),
(12647, 'Stoneweaver Leggings shape'),
(12648, 'Ironshod Bludgeon shape'),
(12649, 'Cragfists shape'),
(12650, 'Rockshard Pauldrons shape'),
(12651, 'The Rockpounder shape'),
(12652, 'Oilskin Leggings shape'),
(12653, 'Grimlok''s Tribal Vestments shape'),
(12654, 'Grimlok''s Charge shape'),
(12655, 'Adventurer''s Pith Helmet shape'),
(12656, 'Shadowforge Bushmaster shape'),
(12657, 'Ginn-su Sword shape'),
(12658, 'Monolithic Bow shape'),
(12659, 'Stonevault Bonebreaker shape'),
(12660, 'Miner''s Hat of the Deep shape'),
(12661, 'Papal Fez shape'),
(12662, 'Skullplate Bracers shape'),
(12663, 'Forgotten Wraps shape'),
(12664, 'Elemental Raiment shape'),
(12665, 'Reticulated Bone Gauntlets shape'),
(12666, 'Grubbis Paws shape'),
(12667, 'Electrocutioner Lagnut shape'),
(12668, 'Manual Crowd Pummeler shape'),
(12669, 'Gnomebot Operating Boots shape'),
(12670, 'Acidic Walkers shape'),
(12671, 'Royal Diplomatic Scepter shape'),
(12672, 'Thermaplugg''s Central Core shape'),
(12673, 'Thermaplugg''s Left Arm shape'),
(12674, 'Digmaster 5000 shape'),
(12675, 'Bad Mojo Mask shape'),
(12676, 'Jinxed Hoodoo Skin shape'),
(12677, 'Jinxed Hoodoo Kilt shape'),
(12678, 'Big Bad Pauldrons shape'),
(12679, 'Embrace of the Lycan shape'),
(12680, 'Eyegouger shape'),
(12681, 'The Minotaur shape'),
(12682, 'Witch Doctor''s Cane shape'),
(12683, 'Spellshock Leggings shape'),
(12684, 'Oscillating Power Hammer shape'),
(12685, 'Gizmotron Megachopper shape'),
(12686, 'Hotshot Pilot''s Gloves shape'),
(12687, 'Electromagnetic Gigaflux Reactivator shape'),
(12688, 'Mechbuilder''s Overalls shape'),
(12689, 'Petrolspill Leggings shape'),
(12690, 'Caverndeep Trudgers shape'),
(12691, 'Blackmetal Cape shape'),
(12692, 'Celestial Stave shape'),
(12693, 'Masons Fraternity Ring shape'),
(12694, 'Engineer''s Guild Headpiece shape'),
(12695, 'Talvash''s Gold Ring shape'),
(12696, 'Nogg''s Gold Ring shape'),
(12697, 'Civinad Robes shape'),
(12698, 'Triprunner Dungarees shape'),
(12699, 'Dual Reinforced Leggings shape'),
(12700, 'Lifeblood Amulet shape'),
(12701, 'Royal Highmark Vestments shape'),
(12702, 'Honorguard Chestpiece shape'),
(12703, 'Gryphon Rider''s Stormhammer shape'),
(12704, 'Gryphon Rider''s Leggings shape'),
(12705, 'Strength of the Treant shape'),
(12706, 'Force of the Hippogryph shape'),
(12707, 'Reforged Blade of Heroes shape'),
(12708, 'Dreamweave Gloves shape'),
(12709, 'Dreamweave Vest shape'),
(12710, 'Dreamweave Circlet shape'),
(12711, 'Scarlet Chestpiece shape'),
(12712, 'Scarlet Leggings shape'),
(12713, 'Scarlet Boots shape'),
(12714, 'Blackened Defias Armor shape'),
(12715, 'Leggings of the Fang shape'),
(12716, 'Footpads of the Fang shape'),
(12717, 'Belt of the Fang shape'),
(12718, 'Gloves of the Fang shape'),
(12719, 'Ebony Boneclub shape'),
(12720, 'Freezing Shard shape'),
(12721, 'Boneslasher shape'),
(12722, 'Corpseshroud shape'),
(12723, 'Thoughtcast Boots shape'),
(12724, 'Death''s Head Vestment shape'),
(12725, 'Briar Tredders shape'),
(12726, 'Quillward Harness shape'),
(12727, 'Stormgale Fists shape'),
(12728, 'Stinging Bow shape'),
(12729, 'Mistwalker Boots shape'),
(12730, 'Soulcatcher Halo shape'),
(12731, 'Murkwater Gauntlets shape'),
(12732, 'Slimescale Bracers shape'),
(12733, 'Silvershell Leggings shape'),
(12734, 'Mindseye Circle shape'),
(12735, 'Will of the Mountain Giant shape'),
(12736, 'Aegis of Battle shape'),
(12737, 'Dragonclaw Ring shape'),
(12738, 'Dragon''s Blood Necklace shape'),
(12739, 'Avenguard Helm shape'),
(12740, 'Gemburst Circlet shape'),
(12741, 'X''caliboar shape'),
(12742, 'Swine Fists shape'),
(12743, 'Robes of the Lich shape'),
(12744, 'Icemetal Barbute shape'),
(12745, 'Deathchill Armor shape'),
(12746, 'Bonefingers shape'),
(12747, 'Plaguerot Sprig shape'),
(12748, 'Savage Boar''s Guard shape'),
(12749, 'Boar Champion''s Belt shape'),
(12750, 'Glowing Eye of Mordresh shape'),
(12751, 'Mordresh''s Lifeless Skull shape'),
(12752, 'Deathmage Sash shape'),
(12753, 'Fleshhide Shoulders shape'),
(12754, 'Carapace of Tuten''kash shape'),
(12755, 'Silky Spider Cape shape'),
(12756, 'Atal''ai Gloves shape'),
(12757, 'Drakeclaw Band shape'),
(12758, 'Drakestone shape'),
(12759, 'Atal''alarion''s Tusk Ring shape'),
(12760, 'Headspike shape'),
(12761, 'Darkwater Bracers shape'),
(12762, 'Slitherscale Boots shape'),
(12763, 'Wingveil Cloak shape'),
(12764, 'Fist of the Damned shape'),
(12765, 'Vestments of the Atal''ai Prophet shape'),
(12766, 'Kilt of the Atal''ai Prophet shape'),
(12767, 'Gloves of the Atal''ai Prophet shape'),
(12768, 'Amberglow Talisman shape'),
(12769, 'The Dragon''s Eye shape'),
(12770, 'Horns of Eranikus shape'),
(12771, 'Crest of Supremacy shape'),
(12772, 'Rod of Corrosion shape'),
(12773, 'Tooth of Eranikus shape'),
(12774, 'Might of Hakkar shape'),
(12775, 'Windscale Sarong shape'),
(12776, 'Featherskin Cape shape'),
(12777, 'Spire of Hakkar shape'),
(12778, 'Warrior''s Embrace shape'),
(12779, 'Bloodshot Greaves shape'),
(12780, 'Darkwater Talwar shape'),
(12781, 'Rainstrider Leggings shape'),
(12782, 'Helm of Exile shape'),
(12783, 'Orb of Lorica shape'),
(12784, 'Nether Force Wand shape'),
(12785, 'Flameseer Mantle shape'),
(12786, 'Emberscale Cape shape'),
(12787, 'Spritecaster Cape shape'),
(12788, 'Kentic Amice shape'),
(12789, 'Enthralled Sphere shape'),
(12790, 'Blackveil Cape shape'),
(12791, 'Fleetfoot Greaves shape'),
(12792, 'Houndmaster''s Bow shape'),
(12793, 'Houndmaster''s Rifle shape'),
(12794, 'Stoneshell Guard shape'),
(12795, 'Earthslag Shoulders shape'),
(12796, 'Spiderfang Carapace shape'),
(12797, 'Silkweb Gloves shape'),
(12798, 'Ban''thok Sash shape'),
(12799, 'Ogreseer Fists shape'),
(12800, 'Naglering shape'),
(12801, 'Shadefiend Boots shape'),
(12802, 'Carapace of Anub''shiah shape'),
(12803, 'Rubicund Armguards shape'),
(12804, 'Splinthide Shoulders shape'),
(12805, 'Girdle of Beastial Fury shape'),
(12806, 'Grizzle''s Skinner shape'),
(12807, 'Stonewall Girdle shape'),
(12808, 'Dregmetal Spaulders shape'),
(12809, 'Savage Gladiator Chain shape'),
(12810, 'Savage Gladiator Leggings shape'),
(12811, 'Savage Gladiator Helm shape'),
(12812, 'Savage Gladiator Grips shape'),
(12813, 'Savage Gladiator Greaves shape'),
(12814, 'Ragefury Eyepatch shape'),
(12815, 'Rockfist shape'),
(12816, 'Fists of Phalanx shape'),
(12817, 'Golem Skull Helm shape'),
(12818, 'Flamestrider Robes shape'),
(12819, 'Pyric Caduceus shape'),
(12820, 'Searingscale Leggings shape'),
(12821, 'Kindling Stave shape'),
(12822, 'Verek''s Collar shape'),
(12823, 'Boreal Mantle shape'),
(12824, 'Chillsteel Girdle shape'),
(12825, 'Arbiter''s Blade shape'),
(12826, 'Shalehusk Boots shape'),
(12827, 'Lavacrest Leggings shape'),
(12828, 'Force of Magma shape'),
(12829, 'Rubidium Hammer shape'),
(12830, 'Sash of the Burning Heart shape'),
(12831, 'Circle of Flame shape'),
(12832, 'Molten Fists shape'),
(12833, 'Angerforge''s Battle Axe shape'),
(12834, 'Royal Decorated Armor shape'),
(12835, 'Warstrife Leggings shape'),
(12836, 'Omnicast Boots shape'),
(12837, 'Luminary Kilt shape'),
(12838, 'Cyclopean Band shape'),
(12839, 'Chief Architect''s Monocle shape'),
(12840, 'Senior Designer''s Pantaloons shape'),
(12841, 'Lead Surveyor''s Mantle shape'),
(12842, 'Nagmara''s Whipping Belt shape'),
(12843, 'Impervious Giant shape'),
(12844, 'Blood-etched Blade shape'),
(12845, 'The Hammer of Grace shape'),
(12846, 'Ghostshroud shape'),
(12847, 'Deathdealer Breastplate shape'),
(12848, 'Legplates of the Eternal Guardian shape'),
(12849, 'Haunting Specter Leggings shape'),
(12850, 'Dreadforge Retaliator shape'),
(12851, 'Guiding Stave of Wisdom shape'),
(12852, 'Magmus Stone shape'),
(12853, 'Manacle Cuffs shape'),
(12854, 'Conqueror''s Medallion shape'),
(12855, 'Pridemail Leggings shape'),
(12856, 'Smoldering Claw shape'),
(12857, 'Embrace of the Wind Serpent shape'),
(12858, 'Drakefang Butcher shape'),
(12859, 'Bloodfire Talons shape'),
(12860, 'Nightfall Drape shape'),
(12861, 'Dawnspire Cord shape'),
(12862, 'Sandstalker Ankleguards shape'),
(12863, 'Desertwalker Cane shape'),
(12864, 'Spire of the Stoneshaper shape'),
(12865, 'Doomforged Straightedge shape'),
(12866, 'Funeral Pyre Vestment shape'),
(12867, 'Aristocratic Cuffs shape'),
(12868, 'Mar Alom''s Grip shape'),
(12869, 'Braincage shape'),
(12870, 'Runed Golem Shackles shape'),
(12871, 'Blisterbane Wrap shape'),
(12872, 'Swiftwalker Boots shape'),
(12873, 'Hands of the Exalted Herald shape'),
(12874, 'Battlechaser''s Greaves shape'),
(12875, 'High Priestess Boots shape'),
(12876, 'Ebonsteel Spaulders shape'),
(12877, 'Serpentine Skuller shape'),
(12878, 'Butcher''s Apron shape'),
(12879, 'Wildthorn Mail shape'),
(12880, 'Dawnbringer Shoulders shape'),
(12881, 'Funeral Cuffs shape'),
(12882, 'Storm Gauntlets shape'),
(12883, 'Blackcrow shape'),
(12884, 'Bleakwood Hew shape'),
(12885, 'Dawn''s Edge shape'),
(12886, 'Enchanted Battlehammer shape'),
(12887, 'Mixologist''s Tunic shape'),
(12888, 'Prospector Axe shape'),
(12889, 'Ironpatch Blade shape'),
(12890, 'Magefist Gloves shape'),
(12891, 'Stormbringer Belt shape'),
(12892, 'Silver-linked Footguards shape'),
(12893, 'Rakzur Club shape'),
(12894, 'Ring of Defense shape'),
(12895, 'Darkweave Breeches shape'),
(12896, 'Starsight Tunic shape'),
(12897, 'Gargoyle''s Bite shape'),
(12898, 'Razor''s Edge shape'),
(12899, 'Thorbia''s Gauntlets shape'),
(12900, 'Band of Purification shape'),
(12901, 'Redbeard Crest shape'),
(12902, 'Magician''s Mantle shape'),
(12903, 'Drakewing Bands shape'),
(12904, 'Lady Alizabeth''s Pendant shape'),
(12905, 'Lord Alexander''s Battle Axe shape'),
(12906, 'Amy''s Blanket shape'),
(12907, 'Mageflame Cloak shape'),
(12908, 'Dalewind Trousers shape'),
(12909, 'Dreamsinger Legguards shape'),
(12910, 'Silver-lined Belt shape'),
(12911, 'Yorgen Bracers shape'),
(12912, 'Elder Wizard''s Mantle shape'),
(12913, 'Axe of Rin''ji shape'),
(12914, 'Executioner''s Cleaver shape'),
(12915, 'Needle Threader shape'),
(12916, 'Gryphonwing Long Bow shape'),
(12917, 'Beazel''s Basher shape'),
(12918, 'Deadwood Sledge shape'),
(12919, 'Heaven''s Light shape'),
(12920, 'Bonesnapper shape'),
(12921, 'Umbral Crystal shape'),
(12922, 'Orb of Mistmantle shape'),
(12923, 'Zealot Blade shape'),
(12924, 'Speedsteel Rapier shape'),
(12925, 'Assassination Blade shape'),
(12926, 'Swiftwind shape'),
(12927, 'Skull Splitting Crossbow shape'),
(12928, 'Heartseeking Crossbow shape'),
(12929, 'Guardian Blade shape'),
(12930, 'Sword of the Magistrate shape'),
(12931, 'Blade of the Titans shape'),
(12932, 'Viscous Hammer shape'),
(12933, 'Blanchard''s Stout shape'),
(12934, 'Twig of the World Tree shape'),
(12935, 'Looming Gavel shape'),
(12936, 'Deanship Claymore shape'),
(12937, 'Warmonger shape'),
(12938, 'Bonechewer shape'),
(12939, 'Frenzied Striker shape'),
(12940, 'Khoo''s Point shape'),
(12941, 'Stoneraven shape'),
(12942, 'Jaina''s Firestarter shape'),
(12943, 'Wyrmslayer Spaulders shape'),
(12944, 'Hydralick Armor shape'),
(12945, 'Obsidian Greaves shape'),
(12946, 'Sapphiron''s Scale Boots shape'),
(12947, 'Plated Fist of Hakoo shape'),
(12948, 'Mugthol''s Helm shape'),
(12949, 'Golem Shard Leggings shape'),
(12950, 'Giantslayer Bracers shape'),
(12951, 'Girdle of Uther shape'),
(12952, 'Shield of Thorsen shape'),
(12953, 'Skullance Shield shape'),
(12954, 'Mountainside Buckler shape'),
(12955, 'Kaleidoscope Chain shape'),
(12956, 'Horizon Choker shape'),
(12957, 'River Pride Choker shape'),
(12958, 'Gazlowe''s Charm shape'),
(12959, 'Skibi''s Pendant shape'),
(12960, 'Medallion of Grand Marshal Morris shape'),
(12961, 'Blush Ember Ring shape'),
(12962, 'The Queen''s Jewel shape'),
(12963, 'Assault Band shape'),
(12964, 'Thunderbrow Ring shape'),
(12965, 'Moccasins of the White Hare shape'),
(12966, 'Furen''s Boots shape'),
(12967, 'Wolfrunner Shoes shape'),
(12968, 'Cassandra''s Grace shape'),
(12969, 'Pads of the Venom Spider shape'),
(12970, 'Sutarn''s Ring shape'),
(12971, 'Glowing Magical Bracelets shape'),
(12972, 'Tigerstrike Mantle shape'),
(12973, 'Blackflame Cape shape'),
(12974, 'Wolffear Harness shape'),
(12975, 'Sandals of the Insurgent shape'),
(12976, 'Winged Helm shape'),
(12977, 'Troll''s Bane Leggings shape'),
(12978, 'Sheepshear Mantle shape'),
(12979, 'Ogron''s Sash shape'),
(12980, 'Serpentine Sash shape'),
(12981, 'Enchanted Kodo Bracers shape'),
(12982, 'Deepfury Bracers shape'),
(12983, 'Wing of the Whelpling shape'),
(12984, 'Dark Phantom Cape shape'),
(12985, 'Ravasaur Scale Boots shape'),
(12986, 'Elven Chain Boots shape'),
(12987, 'Battlecaller Gauntlets shape'),
(12988, 'Frostreaver Crown shape'),
(12989, 'High Bergg Helm shape'),
(12990, 'Firemane Leggings shape'),
(12991, 'Windrunner Legguards shape'),
(12992, 'Sparkleshell Mantle shape'),
(12993, 'Skeletal Shoulders shape'),
(12994, 'Belt of the Gladiator shape'),
(12995, 'Lordly Armguards shape'),
(12996, 'Guttbuster shape'),
(12997, 'Serenity Belt shape'),
(12998, 'Enormous Ogre Belt shape'),
(12999, 'Demonskin Gloves shape'),
(13000, 'Phase Blade shape'),
(13001, 'Crushridge Bindings shape'),
(13002, 'Kresh''s Back shape'),
(13003, 'Trueaim Gauntlets shape'),
(13004, 'Demonic Runed Spaulders shape'),
(13005, 'Globe of D''sak shape'),
(13006, 'Ogreseer Tower Boots shape'),
(13007, 'Magus Ring shape'),
(13008, 'Swiftdart Battleboots shape'),
(13009, 'Royal Tribunal Cloak shape'),
(13010, 'Songbird Blouse shape'),
(13011, 'Woollies of the Prancing Minstrel shape'),
(13012, 'Rainbow Girdle shape'),
(13013, 'Skul''s Cold Embrace shape'),
(13014, 'Skul''s Ghastly Touch shape'),
(13015, 'Vambraces of the Sadist shape'),
(13016, 'Timmy''s Galoshes shape'),
(13017, 'Grimgore Noose shape'),
(13018, 'Mask of the Unforgiven shape'),
(13019, 'Wailing Nightbane Pauldrons shape'),
(13020, 'Robe of Winter Night shape'),
(13021, 'Mooncloth Leggings shape'),
(13022, 'Cavedweller Bracers shape'),
(13023, 'Crystalline Cuffs shape'),
(13024, 'Subterranean Cape shape'),
(13025, 'Robe of Evocation shape'),
(13026, 'Chanting Blade shape'),
(13027, 'Boots of Avoidance shape'),
(13028, 'Bladebane Armguards shape'),
(13029, 'Edgemaster''s Handguards shape'),
(13030, 'Stockade Pauldrons shape'),
(13031, 'Green Dragonscale Breastplate shape'),
(13032, 'Green Dragonscale Leggings shape'),
(13033, 'Blue Dragonscale Breastplate shape'),
(13034, 'Blue Dragonscale Shoulders shape'),
(13035, 'Black Dragonscale Breastplate shape'),
(13036, 'Stormshroud Armor shape'),
(13037, 'Stormshroud Pants shape'),
(13038, 'Stormshroud Shoulders shape'),
(13039, 'Living Leggings shape'),
(13040, 'Living Shoulders shape'),
(13041, 'Devilsaur Gauntlets shape'),
(13042, 'Warbear Harness shape'),
(13043, 'Warbear Woolies shape'),
(13044, 'Ironfeather Breastplate shape'),
(13045, 'Ironfeather Shoulders shape'),
(13046, 'Wingborne Boots shape'),
(13047, 'Orb of Noh''Orahil shape'),
(13048, 'Orb of Dar''Orahil shape'),
(13049, 'Senior Sergeant''s Insignia shape'),
(13050, 'Heroic Commendation Medal shape'),
(13051, 'Intrepid Shortsword shape'),
(13052, 'Valiant Shortsword shape'),
(13053, 'Mooncloth Boots shape'),
(13054, 'Sergeant Major''s Cape shape'),
(13055, 'Sergeant''s Insignia shape'),
(13056, 'Sergeant Major''s Cape shape'),
(13057, 'First Sergeant''s Cloak shape'),
(13058, 'Aquarius Belt shape'),
(13059, 'Boots of Elements shape'),
(13060, 'Bindings of Elements shape'),
(13061, 'Gauntlets of Elements shape'),
(13062, 'Cord of Elements shape'),
(13063, 'Beaststalker''s Boots shape'),
(13064, 'Beaststalker''s Gloves shape'),
(13065, 'Beaststalker''s Belt shape'),
(13066, 'Beaststalker''s Bindings shape'),
(13067, 'Magister''s Boots shape'),
(13068, 'Magister''s Bindings shape'),
(13069, 'Magister''s Gloves shape'),
(13070, 'Magister''s Belt shape'),
(13071, 'Devout Sandals shape'),
(13072, 'Devout Gloves shape'),
(13073, 'Devout Belt shape'),
(13074, 'Devout Bracers shape'),
(13075, 'Dreadmist Belt shape'),
(13076, 'Dreadmist Bracers shape'),
(13077, 'Dreadmist Sandals shape'),
(13078, 'Dreadmist Wraps shape'),
(13079, 'Shadowcraft Bracers shape'),
(13080, 'Shadowcraft Boots shape'),
(13081, 'Shadowcraft Gloves shape'),
(13082, 'Shadowcraft Belt shape'),
(13083, 'Wildheart Bracers shape'),
(13084, 'Wildheart Boots shape'),
(13085, 'Wildheart Belt shape'),
(13086, 'Wildheart Gloves shape'),
(13087, 'Lightforge Bracers shape'),
(13088, 'Lightforge Belt shape'),
(13089, 'Lightforge Gauntlets shape'),
(13090, 'Lightforge Boots shape'),
(13091, 'Boots of Valor shape'),
(13092, 'Bracers of Valor shape'),
(13093, 'Belt of Valor shape'),
(13094, 'Gauntlets of Valor shape'),
(13095, 'Witch''s Finger shape'),
(13096, 'Warsong Sash shape'),
(13097, 'Warsong Boots shape'),
(13098, 'Warsong Gauntlets shape'),
(13099, 'Corehound Boots shape'),
(13100, 'Fiery Chain Girdle shape'),
(13101, 'Royal Seal of Alexis shape'),
(13102, 'Stonerender Gauntlets shape'),
(13103, 'Chan''s Imperial Robes shape'),
(13104, 'Changuk Smasher shape'),
(13105, 'Juno''s Shadow shape'),
(13106, 'Scepter of Celebras shape'),
(13107, 'Gemshard Heart shape'),
(13108, 'Charstone Dirk shape'),
(13109, 'Elemental Rockridge Leggings shape'),
(13110, 'Blackstone Ring shape'),
(13111, 'Bracers of the Stone Princess shape'),
(13112, 'Eye of Theradras shape'),
(13113, 'Megashot Rifle shape'),
(13114, 'Gizlock''s Hypertech Buckler shape'),
(13115, 'Inventor''s Focal Sword shape'),
(13116, 'Albino Crocscale Boots shape'),
(13117, 'Rotgrip Mantle shape'),
(13118, 'Fist of Stone shape'),
(13119, 'Helm of the Mountain shape'),
(13120, 'Rockgrip Gauntlets shape'),
(13121, 'Cloud Stone shape'),
(13122, 'Grovekeeper''s Drape shape'),
(13123, 'Soothsayer''s Headdress shape'),
(13124, 'Nature''s Embrace shape'),
(13125, 'Fungus Shroud Armor shape'),
(13126, 'Noxious Shooter shape'),
(13127, 'Noxxion''s Shackles shape'),
(13128, 'Vinerot Sandals shape'),
(13129, 'Phytoskin Spaulders shape'),
(13130, 'Chloromesh Girdle shape'),
(13131, 'Brusslehide Leggings shape'),
(13132, 'Infernal Trickster Leggings shape'),
(13133, 'Satyrmane Sash shape'),
(13134, 'Bloomsprout Headpiece shape'),
(13135, 'Blood Ruby Pendant shape'),
(13136, 'Coal Miner Boots shape'),
(13137, 'Hurley''s Tankard shape'),
(13138, 'Zum''rah''s Vexing Cane shape'),
(13139, 'Jumanza Grips shape'),
(13140, 'Shadowskin Gloves shape'),
(13141, 'Barbed Thorn Necklace shape'),
(13142, 'Phasing Boots shape'),
(13143, 'Marksman Bands shape'),
(13144, 'Unbridled Leggings shape'),
(13145, 'Nimble Buckler shape'),
(13146, 'Greenroot Mail shape'),
(13147, 'Gloves of Restoration shape'),
(13148, 'Fiendish Machete shape'),
(13149, 'Quel''dorei Channeling Rod shape'),
(13150, 'Energized Chestplate shape'),
(13151, 'Helm of Awareness shape'),
(13152, 'Ring of Demonic Guile shape'),
(13153, 'Obsidian Bauble shape'),
(13154, 'Tempest Talisman shape'),
(13155, 'Merciful Greaves shape'),
(13156, 'Demonheart Spaulders shape'),
(13157, 'Energetic Rod shape'),
(13158, 'Waterspout Boots shape'),
(13159, 'Satyr''s Bow shape'),
(13160, 'Waveslicer shape'),
(13161, 'Felhide Cap shape'),
(13162, 'Razor Gauntlets shape'),
(13163, 'Whipvine Cord shape'),
(13164, 'Shadewood Cloak shape'),
(13165, 'Wand of Arcane Potency shape'),
(13166, 'Quel''dorei Sash shape'),
(13167, 'Quel''dorei Guard shape'),
(13168, 'Stonebark Gauntlets shape'),
(13169, 'Senior Sergeant''s Insignia shape'),
(13170, 'First Sergeant''s Plate Bracers shape'),
(13171, 'First Sergeant''s Mail Wristguards shape'),
(13172, 'First Sergeant''s Leather Armguards shape'),
(13173, 'First Sergeant''s Dragonhide Armguards shape'),
(13174, 'First Sergeant''s Silk Cuffs shape'),
(13175, 'Master Sergeant''s Insignia shape'),
(13176, 'Master Sergeant''s Insignia shape'),
(13177, 'Sergeant Major''s Plate Wristguards shape'),
(13178, 'Sergeant Major''s Chain Armguards shape'),
(13179, 'Sergeant Major''s Leather Armsplints shape'),
(13180, 'Sergeant Major''s Dragonhide Armsplints shape'),
(13181, 'Sergeant Major''s Silk Cuffs shape'),
(13182, 'Lorespinner shape'),
(13183, 'Milli''s Shield shape'),
(13184, 'Milli''s Lexicon shape'),
(13185, 'Band of Allegiance shape'),
(13186, 'Lonetree''s Circle shape'),
(13187, 'Baron Charr''s Sceptre shape'),
(13188, 'Death Knight Sabatons shape'),
(13189, 'Coldstone Slippers shape'),
(13190, 'Tattered Leather Hood shape'),
(13191, 'Icy Tomb Spaulders shape'),
(13192, 'Malefic Bracers shape'),
(13193, 'Innervating Band shape'),
(13194, 'Arena Wristguards shape'),
(13195, 'Arena Bracers shape'),
(13196, 'Peacemaker shape'),
(13197, 'Crimson Felt Hat shape'),
(13198, 'Gracious Cape shape'),
(13199, 'Plaguebat Fur Gloves shape'),
(13200, 'Sacred Cloth Leggings shape'),
(13201, 'Shard of the Green Flame shape'),
(13202, 'Barbaric Bracers shape'),
(13203, 'Might of the Timbermaw shape'),
(13204, 'Wisdom of the Timbermaw shape'),
(13205, 'Girdle of the Dawn shape'),
(13206, 'Dawn Treaders shape'),
(13207, 'Argent Boots shape'),
(13208, 'Emerald Circle shape'),
(13209, 'Deep Woodlands Cloak shape'),
(13210, 'Woven Ivy Necklace shape'),
(13211, 'Inquisitor''s Shawl shape'),
(13212, 'Branded Leather Bracers shape'),
(13213, 'Legionnaire''s Band shape'),
(13214, 'Legionnaire''s Band shape'),
(13215, 'Legionnaire''s Band shape'),
(13216, 'Protector''s Band shape'),
(13217, 'Protector''s Band shape'),
(13218, 'Protector''s Band shape'),
(13219, 'Advisor''s Ring shape'),
(13220, 'Advisor''s Ring shape'),
(13221, 'Advisor''s Ring shape'),
(13222, 'Lorekeeper''s Ring shape'),
(13223, 'Lorekeeper''s Ring shape'),
(13224, 'Lorekeeper''s Ring shape'),
(13225, 'Battle Healer''s Cloak shape'),
(13226, 'Battle Healer''s Cloak shape'),
(13227, 'Battle Healer''s Cloak shape'),
(13228, 'Caretaker''s Cape shape'),
(13229, 'Caretaker''s Cape shape'),
(13230, 'Caretaker''s Cape shape'),
(13231, 'Scout''s Medallion shape'),
(13232, 'Scout''s Medallion shape'),
(13233, 'Scout''s Medallion shape'),
(13234, 'Sentinel''s Medallion shape'),
(13235, 'Sentinel''s Medallion shape'),
(13236, 'Sentinel''s Medallion shape'),
(13237, 'Scout''s Blade shape'),
(13238, 'Scout''s Blade shape'),
(13239, 'Scout''s Blade shape'),
(13240, 'Sentinel''s Blade shape'),
(13241, 'Sentinel''s Blade shape'),
(13242, 'Sentinel''s Blade shape'),
(13243, 'Legionnaire''s Sword shape'),
(13244, 'Legionnaire''s Sword shape'),
(13245, 'Legionnaire''s Sword shape'),
(13246, 'Protector''s Sword shape'),
(13247, 'Protector''s Sword shape'),
(13248, 'Protector''s Sword shape'),
(13249, 'Outrider''s Bow shape'),
(13250, 'Outrider''s Bow shape'),
(13251, 'Outrunner''s Bow shape'),
(13252, 'Outrunner''s Bow shape'),
(13253, 'Advisor''s Gnarled Staff shape'),
(13254, 'Advisor''s Gnarled Staff shape'),
(13255, 'Advisor''s Gnarled Staff shape'),
(13256, 'Lorekeeper''s Staff shape'),
(13257, 'Lorekeeper''s Staff shape'),
(13258, 'Lorekeeper''s Staff shape'),
(13259, 'Berserker Bracers shape'),
(13260, 'Berserker Bracers shape'),
(13261, 'Windtalker''s Wristguards shape'),
(13262, 'Windtalker''s Wristguards shape'),
(13263, 'Forest Stalker''s Bracers shape'),
(13264, 'Forest Stalker''s Bracers shape'),
(13265, 'Dryad''s Wrist Bindings shape'),
(13266, 'Dryad''s Wrist Bindings shape'),
(13267, 'Duskbat Drape shape'),
(13268, 'Ebon Mask shape'),
(13269, 'Pirate''s Eye Patch shape'),
(13270, 'Devilsaur Claws shape'),
(13271, 'Devilsaur Claws shape'),
(13272, 'Circle of Hope shape'),
(13273, 'Glacial Spike shape'),
(13274, 'Arcane Crystal Pendant shape'),
(13275, 'Woestave shape'),
(13276, 'Hunting Spear shape'),
(13277, 'Highlander''s Chain Girdle shape'),
(13278, 'Highlander''s Chain Girdle shape'),
(13279, 'Highlander''s Chain Greaves shape'),
(13280, 'Highlander''s Chain Greaves shape'),
(13281, 'Highlander''s Padded Greaves shape'),
(13282, 'Highlander''s Cloth Boots shape'),
(13283, 'Highlander''s Cloth Boots shape'),
(13284, 'Highlander''s Cloth Boots shape'),
(13285, 'Highlander''s Cloth Girdle shape'),
(13286, 'Highlander''s Cloth Girdle shape'),
(13287, 'Highlander''s Cloth Girdle shape'),
(13288, 'Highlander''s Lizardhide Boots shape'),
(13289, 'Highlander''s Lizardhide Boots shape'),
(13290, 'Highlander''s Lizardhide Boots shape'),
(13291, 'Highlander''s Lizardhide Girdle shape'),
(13292, 'Highlander''s Lizardhide Girdle shape'),
(13293, 'Highlander''s Lizardhide Girdle shape'),
(13294, 'Highlander''s Lamellar Girdle shape'),
(13295, 'Highlander''s Lamellar Girdle shape'),
(13296, 'Highlander''s Lamellar Girdle shape'),
(13297, 'Highlander''s Lamellar Greaves shape'),
(13298, 'Highlander''s Lamellar Greaves shape'),
(13299, 'Highlander''s Lamellar Greaves shape'),
(13300, 'Highlander''s Leather Boots shape'),
(13301, 'Highlander''s Leather Boots shape'),
(13302, 'Highlander''s Leather Boots shape'),
(13303, 'Highlander''s Leather Girdle shape'),
(13304, 'Highlander''s Mail Girdle shape'),
(13305, 'Highlander''s Mail Girdle shape'),
(13306, 'Highlander''s Mail Girdle shape'),
(13307, 'Highlander''s Mail Greaves shape'),
(13308, 'Highlander''s Mail Greaves shape'),
(13309, 'Highlander''s Mail Greaves shape'),
(13310, 'Highlander''s Plate Girdle shape'),
(13311, 'Highlander''s Plate Girdle shape'),
(13312, 'Highlander''s Mail Girdle shape'),
(13313, 'Highlander''s Plate Greaves shape'),
(13314, 'Highlander''s Plate Greaves shape'),
(13315, 'Highlander''s Mail Greaves shape'),
(13316, 'Defiler''s Chain Girdle shape'),
(13317, 'Defiler''s Chain Girdle shape'),
(13318, 'Defiler''s Chain Greaves shape'),
(13319, 'Defiler''s Chain Greaves shape'),
(13320, 'Defiler''s Chain Greaves shape'),
(13321, 'Defiler''s Cloth Boots shape'),
(13322, 'Defiler''s Cloth Boots shape'),
(13323, 'Defiler''s Cloth Boots shape'),
(13324, 'Defiler''s Cloth Girdle shape'),
(13325, 'Defiler''s Cloth Girdle shape'),
(13326, 'Defiler''s Cloth Girdle shape'),
(13327, 'Defiler''s Lizardhide Boots shape'),
(13328, 'Defiler''s Lizardhide Boots shape'),
(13329, 'Defiler''s Lizardhide Boots shape'),
(13330, 'Defiler''s Lizardhide Girdle shape'),
(13331, 'Defiler''s Lizardhide Girdle shape'),
(13332, 'Defiler''s Lizardhide Girdle shape'),
(13333, 'Defiler''s Lamellar Girdle shape'),
(13334, 'Defiler''s Lamellar Girdle shape'),
(13335, 'Defiler''s Lamellar Girdle shape'),
(13336, 'Defiler''s Lamellar Greaves shape'),
(13337, 'Defiler''s Lamellar Greaves shape'),
(13338, 'Defiler''s Lamellar Greaves shape'),
(13339, 'Defiler''s Leather Boots shape'),
(13340, 'Defiler''s Leather Boots shape'),
(13341, 'Defiler''s Leather Boots shape'),
(13342, 'Defiler''s Leather Girdle shape'),
(13343, 'Defiler''s Mail Girdle shape'),
(13344, 'Defiler''s Padded Girdle shape'),
(13345, 'Defiler''s Mail Girdle shape'),
(13346, 'Defiler''s Mail Greaves shape'),
(13347, 'Defiler''s Mail Greaves shape'),
(13348, 'Defiler''s Mail Greaves shape'),
(13349, 'Defiler''s Plate Girdle shape'),
(13350, 'Defiler''s Plate Girdle shape'),
(13351, 'Defiler''s Mail Girdle shape'),
(13352, 'Defiler''s Plate Greaves shape'),
(13353, 'Defiler''s Mail Greaves shape'),
(13354, 'Defiler''s Plate Greaves shape'),
(13355, 'Faded Hakkari Cloak shape'),
(13356, 'Tattered Hakkari Cape shape'),
(13357, 'Whisperwalk Boots shape'),
(13358, 'Green Dragonscale Gauntlets shape'),
(13359, 'Azurite Fists shape'),
(13360, 'Advisor''s Gnarled Staff shape'),
(13361, 'Advisor''s Ring shape'),
(13362, 'Battle Healer''s Cloak shape'),
(13363, 'Caretaker''s Cape shape'),
(13364, 'Legionnaire''s Band shape'),
(13365, 'Legionnaire''s Sword shape'),
(13366, 'Lorekeeper''s Ring shape'),
(13367, 'Lorekeeper''s Staff shape'),
(13368, 'Protector''s Band shape'),
(13369, 'Protector''s Sword shape'),
(13370, 'Scout''s Blade shape'),
(13371, 'Scout''s Medallion shape'),
(13372, 'Sentinel''s Blade shape'),
(13373, 'Sentinel''s Medallion shape'),
(13374, 'Ironbark Shield shape'),
(13375, 'Lightforged Blade shape'),
(13376, 'Chivalrous Signet shape'),
(13377, 'Razorsteel Shoulders shape'),
(13378, 'Fury Visor shape'),
(13379, 'Feral Staff shape'),
(13380, 'Shadowhide Leggings shape'),
(13381, 'Robes of Servitude shape'),
(13382, 'Soul Harvester shape'),
(13383, 'Wildstaff shape'),
(13384, 'Black Crystal Dagger shape'),
(13385, 'Moonsoul Crown shape'),
(13386, 'Ruby Crown of Restoration shape'),
(13387, 'Stormshroud Gloves shape'),
(13388, 'Gem Studded Band shape'),
(13389, 'Emerald Crown of Destruction shape'),
(13390, 'Living Emerald Pendant shape'),
(13391, 'Black Steel Bindings shape'),
(13392, 'Lavastone Hammer shape'),
(13393, 'Golem Fitted Pauldrons shape'),
(13394, 'Foreman''s Head Protector shape'),
(13395, 'Frightmaw Hide shape'),
(13396, 'Mantle of Lost Hope shape'),
(13397, 'Greaves of Withering Despair shape'),
(13398, 'Dark Warder''s Pauldrons shape'),
(13399, 'Verek''s Leash shape'),
(13400, 'Soot Encrusted Footwear shape'),
(13401, 'Wand of Eternal Light shape'),
(13402, 'Magma Forged Band shape'),
(13403, 'Mana Shaping Handwraps shape'),
(13404, 'Bloodclot Band shape'),
(13405, 'Flarethorn shape'),
(13406, 'Entrenching Boots shape'),
(13407, 'Leggings of Frenzied Magic shape'),
(13408, 'Forest''s Embrace shape'),
(13409, 'Moonshadow Hood shape'),
(13410, 'Grizzled Pelt shape'),
(13411, 'Firemoss Boots shape'),
(13412, 'Moonshadow Stave shape'),
(13413, 'Staff of the Sun shape'),
(13414, 'Sin''dorei Warblade shape'),
(13415, 'Scorn''s Focal Dagger shape'),
(13416, 'Scorn''s Icy Choker shape'),
(13417, 'The Axe of Severing shape'),
(13418, 'Abomination Skin Leggings shape'),
(13419, 'Lady Falther''ess'' Finger shape'),
(13420, 'Mantle of Lady Falther''ess shape'),
(13421, 'Blood-Tempered Ranseur shape'),
(13422, 'Golden Ring of Power shape'),
(13423, 'Truesilver Commander''s Ring shape'),
(13424, 'Blackstorm Leggings shape'),
(13425, 'Wildfeather Leggings shape'),
(13426, 'Dragonstrike Leggings shape'),
(13427, 'Earthforged Leggings shape'),
(13428, 'Windforged Leggings shape'),
(13429, 'Light Earthforged Blade shape'),
(13430, 'Light Skyforged Axe shape'),
(13431, 'Bronze Band of Force shape'),
(13432, 'Tattered Shoulderpads shape'),
(13433, 'Crystaline Shard Shield shape'),
(13434, 'Gloves of the Dune shape'),
(13435, 'Marauder''s Handwraps shape'),
(13436, 'Scrying Wand shape'),
(13437, 'Thorium Flight Blade shape'),
(13438, 'Cave Crawler''s Mail Treads shape'),
(13439, 'Tempered Thorium Boots shape'),
(13440, 'Mystic Tome shape'),
(13441, 'Tome of the Dawn shape'),
(13442, 'Tome of Kings shape'),
(13443, 'Royal Guide of Escape Routes shape'),
(13444, 'Fire Eater''s Guide shape'),
(13445, 'Book of Stars shape'),
(13446, 'Stormbound Tome shape'),
(13447, 'Manual of Clouds shape'),
(13448, 'Darkmoon Pendant shape'),
(13449, 'Darkmoon Necklace shape'),
(13450, 'Darkmoon Dirk shape'),
(13451, 'Darkmoon Executioner shape'),
(13452, 'Darkmoon Magestaff shape'),
(13453, 'Spidersilk Drape shape'),
(13454, 'Amulet of Truesight shape');

DELETE FROM `item_budget_assign` WHERE `entry` IN (
  720, 776, 791, 812, 862, 867, 868, 872, 873, 888, 890, 940, 942, 943, 1121,
  1155, 1156, 1169, 1203, 1204, 1292, 1315, 1447, 1454, 1483, 1484, 1486, 1488, 1489, 1491,
  1493, 1602, 1607, 1678, 1714, 1715, 1716, 1717, 1718, 1720, 1721, 1722, 1935, 1937, 1975,
  1976, 1978, 1979, 1980, 1981, 1992, 2011, 2039, 2040, 2041, 2042, 2044, 2059, 2100, 2169,
  2194, 2236, 2244, 2245, 2246, 2264, 2271, 2276, 2277, 2278, 2280, 2292, 2549, 2564, 2565,
  2567, 2721, 2800, 2807, 2815, 2816, 2870, 2877, 2878, 2879, 2911, 2912, 2933, 2941, 2951,
  3020, 3021, 3075, 3078, 3191, 3203, 3228, 3413, 3414, 3415, 3416, 3417, 3748, 3844, 4091,
  4120, 4134, 4197, 4253, 4320, 4327, 4438, 4446, 4454, 4507, 4508, 4743, 4975, 5183, 5192,
  5193, 5194, 5195, 5196, 5197, 5199, 5200, 5201, 5202, 5254, 5257, 5266, 5404, 5423, 5425,
  5443, 5819, 5970, 6087, 6314, 6318, 6319, 6320, 6321, 6323, 6324, 6327, 6332, 6340, 6341,
  6392, 6414, 6448, 6449, 6460, 6463, 6465, 6468, 6473, 6504, 6505, 6627, 6629, 6630, 6631,
  6632, 6633, 6642, 6679, 6681, 6682, 6685, 6686, 6687, 6688, 6689, 6690, 6691, 6692, 6693,
  6694, 6695, 6696, 6697, 6725, 6742, 6802, 6803, 6804, 6829, 6830, 6900, 6901, 6902, 6903,
  6906, 6908, 6910, 6911, 6953, 6972, 6975, 6976, 6977, 7001, 7002, 7054, 7133, 7187, 7230,
  7513, 7514, 7515, 7673, 7683, 7684, 7685, 7686, 7687, 7688, 7689, 7690, 7691, 7709, 7711,
  7712, 7713, 7714, 7718, 7719, 7720, 7721, 7722, 7723, 7726, 7727, 7728, 7731, 7736, 7752,
  7754, 7755, 7756, 7757, 7758, 7759, 7760, 7761, 7786, 7787, 7888, 7922, 7938, 8174, 8226,
  8345, 8346, 8347, 8348, 8349, 8367, 9240, 9359, 9375, 9378, 9379, 9383, 9384, 9385, 9392,
  9393, 9394, 9395, 9396, 9397, 9398, 9400, 9401, 9403, 9405, 9406, 9407, 9408, 9410, 9411,
  9413, 9414, 9415, 9416, 9420, 9422, 9424, 9426, 9427, 9429, 9431, 9432, 9433, 9434, 9435,
  9445, 9447, 9449, 9450, 9454, 9457, 9458, 9459, 9465, 9470, 9473, 9474, 9476, 9479, 9480,
  9481, 9482, 9484, 9488, 9490, 9491, 9492, 9508, 9509, 9510, 9512, 9517, 9533, 9534, 9538,
  9588, 9623, 9624, 9625, 9641, 9649, 9650, 9651, 9652, 9683, 9684, 9718, 10019, 10021, 10041,
  10328, 10330, 10332, 10399, 10410, 10411, 10412, 10413, 10571, 10572, 10573, 10574, 10578, 10581, 10582,
  10583, 10584, 10624, 10629, 10630, 10631, 10632, 10633, 10634, 10652, 10686, 10710, 10711, 10749, 10751,
  10758, 10760, 10762, 10763, 10764, 10765, 10766, 10767, 10768, 10769, 10770, 10771, 10774, 10775, 10776,
  10787, 10795, 10796, 10798, 10799, 10800, 10801, 10802, 10804, 10806, 10807, 10808, 10824, 10829, 10833,
  10835, 10836, 10837, 10838, 10842, 10843, 10844, 10845, 10846, 11121, 11123, 11124, 11262, 11263, 11310,
  11311, 11623, 11624, 11625, 11626, 11627, 11628, 11629, 11631, 11632, 11633, 11634, 11662, 11665, 11669,
  11675, 11678, 11679, 11685, 11686, 11702, 11703, 11722, 11726, 11728, 11729, 11730, 11731, 11735, 11743,
  11745, 11746, 11747, 11748, 11749, 11750, 11755, 11782, 11783, 11784, 11787, 11802, 11803, 11805, 11807,
  11808, 11814, 11816, 11820, 11821, 11822, 11823, 11824, 11839, 11841, 11842, 11866, 11921, 11922, 11923,
  11925, 11926, 11927, 11929, 11931, 11932, 11935, 11962, 12059, 12105, 12243, 12462, 12463, 12464, 12465,
  12466, 12470, 12471, 12532, 12535, 12542, 12546, 12547, 12549, 12550, 12552, 12553, 12554, 12555, 12556,
  12557, 12605, 12608, 12624, 12625, 12626, 12632, 12651, 12769, 12774, 12776, 12793, 12975, 12976, 12977,
  12978, 12982, 12983, 12985, 12987, 12988, 12989, 12990, 12994, 12996, 12997, 12998, 12999, 13002, 13003,
  13005, 13007, 13008, 13010, 13011, 13012, 13013, 13014, 13018, 13021, 13022, 13024, 13025, 13026, 13027,
  13029, 13031, 13033, 13034, 13036, 13038, 13039, 13040, 13041, 13042, 13043, 13045, 13046, 13047, 13048,
  13049, 13052, 13055, 13056, 13058, 13059, 13064, 13066, 13067, 13068, 13070, 13071, 13073, 13074, 13076,
  13077, 13079, 13081, 13082, 13084, 13085, 13087, 13088, 13089, 13091, 13093, 13094, 13095, 13097, 13099,
  13100, 13101, 13102, 13103, 13105, 13106, 13108, 13109, 13110, 13111, 13112, 13114, 13115, 13117, 13118,
  13119, 13120, 13121, 13122, 13124, 13125, 13126, 13127, 13128, 13129, 13130, 13131, 13132, 13134, 13135,
  13139, 13144, 13145, 13181, 13182, 13199, 13245, 13255, 13257, 13261, 13282, 13283, 13284, 13376, 13378,
  13383, 13384, 13394, 13396, 13400, 13402, 13403, 13404, 13405, 14136, 14137, 14147, 14148, 14149, 14150,
  14151, 14549, 14550, 14551, 14552, 15045, 15046, 15048, 15049, 15050, 15056, 15057, 15058, 15060, 15061,
  15063, 15064, 15065, 15066, 15067, 15104, 15107, 15108, 15200, 15799, 15800, 15801, 15802, 16315, 16334,
  16336, 16340, 16608, 16670, 16671, 16672, 16673, 16675, 16676, 16680, 16681, 16682, 16683, 16684, 16685,
  16691, 16692, 16696, 16697, 16702, 16703, 16704, 16705, 16710, 16711, 16712, 16713, 16714, 16715, 16716,
  16717, 16722, 16723, 16724, 16725, 16734, 16735, 16736, 16737, 16887, 16975, 16977, 16978, 16982, 16989,
  16999, 17007, 17050, 17055, 17061, 17191, 17707, 17710, 17711, 17713, 17714, 17715, 17717, 17718, 17719,
  17728, 17732, 17733, 17734, 17736, 17737, 17739, 17740, 17741, 17742, 17745, 17746, 17748, 17749, 17750,
  17751, 17754, 17755, 17767, 18023, 18043, 18044, 18082, 18083, 18238, 18289, 18295, 18296, 18298, 18303,
  18304, 18309, 18310, 18311, 18312, 18313, 18314, 18316, 18317, 18318, 18320, 18321, 18322, 18323, 18324,
  18325, 18326, 18327, 18328, 18338, 18341, 18342, 18344, 18428, 18430, 18432, 18435, 18436, 18437, 18442,
  18444, 18447, 18449, 18453, 18455, 18457, 18491, 18535, 18536, 18585, 18586, 18671, 18692, 18697, 18698,
  18699, 18700, 18701, 18709, 18710, 18725, 18727, 18743, 18744, 18745, 18762, 18948, 19044, 19047, 19051,
  19052, 19056, 19065, 19121, 19159, 19507, 19508, 19511, 19512, 19513, 19515, 19516, 19517, 19519, 19520,
  19521, 19523, 19524, 19525, 19527, 19528, 19529, 19531, 19532, 19533, 19535, 19536, 19537, 19539, 19540,
  19541, 19543, 19544, 19545, 19547, 19548, 19549, 19551, 19552, 19553, 19555, 19556, 19557, 19559, 19560,
  19563, 19564, 19567, 19568, 19569, 19571, 19572, 19573, 19580, 19581, 19583, 19584, 19589, 19590, 19596,
  19597, 19982, 19984, 19986, 20003, 20005, 20006, 20035, 20037, 20082, 20083, 20088, 20089, 20091, 20092,
  20093, 20094, 20095, 20096, 20097, 20098, 20099, 20100, 20101, 20102, 20103, 20104, 20105, 20106, 20107,
  20108, 20109, 20110, 20111, 20112, 20113, 20114, 20115, 20118, 20119, 20120, 20121, 20122, 20123, 20124,
  20125, 20126, 20127, 20128, 20129, 20151, 20153, 20155, 20156, 20157, 20160, 20161, 20162, 20164, 20165,
  20166, 20168, 20169, 20170, 20172, 20173, 20174, 20178, 20179, 20180, 20182, 20183, 20185, 20187, 20188,
  20189, 20193, 20196, 20197, 20198, 20200, 20201, 20202, 20205, 20206, 20207, 20209, 20210, 20211, 20218,
  20219, 20255, 20296, 20369, 20425, 20426, 20427, 20428, 20429, 20430, 20431, 20434, 20439, 20440, 20441,
  20442, 20443, 20444, 20502, 20504, 20505, 20517, 20521, 20522, 20524, 20530, 20536, 20556, 20647, 20832,
  20969, 21278, 21753, 21774, 21791, 22205, 22208, 22212, 22223, 22230, 22234, 22240, 22241, 22242, 22245,
  22254, 22255, 22256, 22257, 22266, 22270, 22271, 22272, 22273, 22274, 22275, 22458, 22980, 22995, 23168,
  23169, 23171, 23173, 23177, 23178, 25464, 29157, 29158, 29964, 29970, 29971, 30069, 30070, 30071, 30072,
  30804, 34107, 34415, 34416, 34417, 34418, 34419, 34421, 34422, 43515, 43654, 43656, 43657, 43660, 43661,
  43663, 43664, 44213, 44215, 44217, 44218, 44219, 45626, 45627
);
INSERT INTO `item_budget_assign` (`entry`, `template_id`, `budget_mult`, `stamina_delta`, `dps_delta`, `absorbed_spell_slots`, `armor_delta`) VALUES
(720, 12366, 1, 0, 0.0, 0, 0),
(776, 12367, 0.718, 0, -2.27, 0, 0),
(791, 12368, 1.188, 0, 4.12, 0, 0),
(812, 12369, 1.188, 0, 10.02, 0, 0),
(862, 12370, 1, 0, 0.0, 1, 0),
(867, 12371, 1, 0, 0.0, 1, 0),
(868, 12372, 1.014, 0, -3.36, 1, 0),
(872, 12373, 1, 0, 2.58, 0, 0),
(873, 12374, 1.188, 0, 5.89, 1, 0),
(888, 12375, 1, 0, 0.0, 0, 0),
(890, 12376, 1.188, 0, 4.24, 0, 0),
(940, 12377, 1, 0, 0.0, 0, 0),
(942, 12378, 1, 0, 0.0, 1, 0),
(943, 12379, 1.204, 0, 6.78, 1, 0),
(1121, 12380, 1, 0, 0.0, 0, 0),
(1155, 12381, 1.188, 0, 3.15, 0, 0),
(1156, 12382, 1, 0, 0.0, 0, 0),
(1169, 12383, 0.638, 0, 0.0, 0, 0),
(1203, 12384, 0.864, 0, 0.0, 0, 0),
(1204, 12385, 0.638, 0, 0.0, 1, 0),
(1292, 12386, 0.718, 0, -0.11, 0, 0),
(1315, 12387, 1, 0, 0.0, 0, 0),
(1447, 12388, 1, 0, 0.0, 0, 0),
(1454, 12389, 0.718, 0, -2.57, 0, 0),
(1483, 12390, 0.718, 0, -1.71, 0, 0),
(1484, 12391, 1.188, 0, 3.25, 1, 0),
(1486, 12392, 1, 0, 0.0, 0, 0),
(1488, 12393, 1, 0, 0.0, 0, 0),
(1489, 12394, 1, 0, 0.0, 0, 0),
(1491, 12395, 1, 0, 0.0, 0, 0),
(1493, 12396, 0.718, 0, -2.61, 0, 0),
(1602, 12397, 0.718, 0, -1.53, 0, 0),
(1607, 12398, 1.188, 0, 6.15, 0, 0),
(1678, 12399, 1, 0, 0.0, 0, 0),
(1714, 12400, 1, 0, 0.0, 0, 0),
(1715, 12401, 1, 0, 0.0, 0, 0),
(1716, 12402, 1, 0, 0.0, 1, 0),
(1717, 12403, 1, 0, 0.0, 2, 0),
(1718, 12404, 1, 0, 0.0, 0, 0),
(1720, 12405, 1.188, 0, 6.56, 1, 0),
(1721, 12406, 0.718, 0, -4.6, 0, 0),
(1722, 12407, 1, 0, 6.53, 0, 0),
(1935, 12408, 0.718, 0, -0.67, 0, 0),
(1937, 12409, 0.718, 0, -1.79, 0, 0),
(1975, 12410, 1.188, 0, 2.74, 0, 0),
(1976, 12411, 1, 0, 3.15, 0, 0),
(1978, 12412, 1, 0, 0.0, 0, 0),
(1979, 12413, 0.864, 0, 0.0, 0, 0),
(1980, 12414, 1, 0, 0.0, 1, 0),
(1981, 12415, 1, 0, 0.0, 0, 0),
(1992, 12416, 1.186, 0, 0.0, 1, 0),
(2011, 12417, 0.685, 0, -0.08, 0, 0),
(2039, 12418, 1, 0, 0.0, 0, 0),
(2040, 12419, 0.732, 0, 0.0, 1, 0),
(2041, 12420, 1, 0, 0.0, 0, 0),
(2042, 12421, 1.188, 0, 4.3, 0, 0),
(2044, 12422, 0.718, 0, -0.61, 0, 0),
(2059, 12423, 1, 0, 0.0, 0, 0),
(2100, 12424, 0.581, 0, -5.01, 0, 0),
(2169, 12425, 0.718, 0, -1.75, 0, 0),
(2194, 12426, 0.718, 0, -0.09, 0, 0),
(2236, 12427, 0.685, 0, 0.04, 0, 0),
(2244, 12428, 0.718, 0, -1.88, 1, 0),
(2245, 12429, 1, 0, 0.0, 0, 0),
(2246, 12430, 1, 0, 0.0, 0, 0),
(2264, 12431, 1, 0, 0.0, 0, 0),
(2271, 12432, 1.188, 0, 3.58, 1, 0),
(2276, 12433, 1, 0, 0.0, 0, 0),
(2277, 12434, 1, 0, 0.0, 1, 0),
(2278, 12435, 1, 0, 0.0, 0, 0),
(2280, 12436, 1.188, 0, 2.63, 1, 0),
(2292, 12437, 1, 0, 0.0, 0, 0),
(2549, 12438, 1.188, 0, 2.62, 1, 0),
(2564, 12439, 1, 0, 0.0, 1, 0),
(2565, 12440, 1.186, 0, 0.0, 1, 0),
(2567, 12441, 0.685, 0, -0.78, 0, 0),
(2721, 12442, 1, 0, 0.0, 1, 0),
(2800, 12443, 1, 0, 0.0, 0, 0),
(2807, 12444, 0.718, 0, -1.09, 0, 0),
(2815, 12445, 0.718, 0, -2.75, 0, 0),
(2816, 12446, 0.8, 0, -0.96, 1, 0),
(2870, 12447, 1, 0, 0.0, 0, 0),
(2877, 12448, 1.188, 0, 5.37, 0, 0),
(2878, 12449, 0.718, 0, -2.1, 0, 0),
(2879, 12450, 1.186, 0, 0.0, 1, 0),
(2911, 12451, 1, 0, 0.0, 0, 0),
(2912, 12452, 0.685, 0, -1.42, 0, 0),
(2933, 12453, 1, 0, 0.0, 0, 0),
(2941, 12454, 0.718, 0, -0.08, 0, 0),
(2951, 12455, 1, 0, 0.0, 0, 0),
(3020, 12456, 1, 0, 0.0, 0, 0),
(3021, 12457, 0.269, 0, -0.18, 0, 0),
(3075, 12458, 1, 0, 0.0, 1, 0),
(3078, 12459, 0.269, 0, -0.08, 0, 0),
(3191, 12460, 1, 0, 4.92, 0, 0),
(3203, 12461, 1, 0, 2.78, 0, 0),
(3228, 12462, 1, 0, 0.0, 0, 0),
(3413, 12463, 0.718, 0, 0.04, 0, 0),
(3414, 12464, 0.685, 0, -2.57, 0, 0),
(3415, 12465, 1.188, 0, 4.18, 0, 0),
(3416, 12466, 1, 0, 0.0, 0, 0),
(3417, 12467, 1, 0, 4.86, 0, 0),
(3748, 12468, 1, 0, 0.0, 1, 0),
(3844, 12469, 1, 0, 0.0, 0, 0),
(4091, 12470, 0.718, 0, -2.86, 0, 0),
(4120, 12471, 1, 0, 0.0, 0, 0),
(4134, 12472, 1.188, 0, 6.7, 1, 0),
(4197, 12473, 1, 0, 0.0, 0, 0),
(4253, 12474, 1, 0, 0.0, 0, 0),
(4320, 12475, 1, 0, 0.0, 0, 0),
(4327, 12476, 1, 0, 0.0, 0, 0),
(4438, 12477, 1, 0, 0.0, 0, 0),
(4446, 12478, 0.718, 0, -0.08, 0, 0),
(4454, 12479, 0.718, 0, 0.0, 0, 0),
(4507, 12480, 0.864, 0, 0.0, 0, 0),
(4508, 12481, 1, 0, 0.0, 0, 0),
(4743, 12482, 1, 0, 0.0, 1, 0),
(4975, 12483, 0.732, 0, 0.0, 1, 0),
(5183, 12484, 1.186, 0, 0.0, 1, 0),
(5192, 12485, 0.718, 0, -1.51, 0, 0),
(5193, 12486, 1, 0, 0.0, 0, 0),
(5194, 12487, 1.188, 0, 3.54, 0, 0),
(5195, 12488, 1, 0, 0.0, 1, 0),
(5196, 12489, 0.718, 0, -1.45, 0, 0),
(5197, 12490, 0.718, 0, -1.82, 0, 0),
(5199, 12491, 1, 0, 0.0, 0, 0),
(5200, 12492, 1, 0, 3.04, 0, 0),
(5201, 12493, 1.188, 0, 3.58, 0, 0),
(5202, 12494, 1, 0, 0.0, 0, 0),
(5254, 12495, 1, 0, 0.0, 0, 0),
(5257, 12496, 1, 0, 0.0, 0, 0),
(5266, 12497, 1, 0, 0.0, 0, 0),
(5404, 12498, 1, 0, 0.0, 0, 0),
(5423, 12499, 1, 0, 2.73, 0, 0),
(5425, 12500, 1, 0, 0.0, 0, 0),
(5443, 12501, 0.864, 0, 0.0, 0, 0),
(5819, 12502, 1, 0, 0.0, 0, 0),
(5970, 12503, 1, 0, 0.0, 1, 0),
(6087, 12504, 1, 0, 0.0, 0, 0),
(6314, 12505, 1, 0, 0.0, 0, 0),
(6318, 12506, 1.188, 0, 4.97, 0, 0),
(6319, 12507, 1, 0, 0.0, 0, 0),
(6320, 12508, 0.732, 0, 0.0, 0, 0),
(6321, 12509, 1, 0, 0.0, 0, 0),
(6323, 12510, 0.718, 0, -0.04, 0, 0),
(6324, 12511, 1, 0, 0.0, 1, 0),
(6327, 12512, 1, 0, 6.83, 0, 0),
(6332, 12513, 1, 0, 0.0, 0, 0),
(6340, 12514, 1, 0, 0.0, 0, 0),
(6341, 12515, 1.186, 0, 0.0, 1, 0),
(6392, 12516, 1, 0, 0.0, 1, 0),
(6414, 12517, 1, 0, 0.0, 0, 0),
(6448, 12518, 0.718, 0, -1.48, 0, 0),
(6449, 12519, 1, 0, 0.0, 0, 0),
(6460, 12520, 1, 0, 0.0, 0, 0),
(6463, 12521, 1, 0, 0.0, 0, 0),
(6465, 12522, 1, 0, 0.0, 1, 0),
(6468, 12523, 1, 0, 0.0, 0, 0),
(6473, 12524, 1, 0, 0.0, 0, 0),
(6504, 12525, 0.718, 0, -0.52, 0, 0),
(6505, 12526, 1.188, 0, 4.14, 0, 0),
(6627, 12527, 1, 0, 0.0, 0, 0),
(6629, 12528, 1, 0, 0.0, 0, 0),
(6630, 12529, 0.638, 0, 0.0, 0, 0),
(6631, 12530, 1.188, 0, 4.92, 1, 0),
(6632, 12531, 1, 0, 0.0, 1, 0),
(6633, 12532, 0.718, 0, -1.09, 0, 0),
(6642, 12533, 1, 0, 0.0, 0, 0),
(6679, 12534, 1, 0, 3.05, 0, 0),
(6681, 12535, 0.718, 0, -1.36, 0, 0),
(6682, 12536, 1, 0, 0.0, 0, 0),
(6685, 12537, 1, 0, 0.0, 1, 0),
(6686, 12538, 1, 0, 0.0, 0, 0),
(6687, 12539, 1, 0, 6.11, 0, 0),
(6688, 12540, 1, 0, 0.0, 1, 0),
(6689, 12541, 1.188, 0, 4.72, 0, 0),
(6690, 12542, 1, 0, 0.0, 0, 0),
(6691, 12543, 0.685, 0, -0.42, 0, 0),
(6692, 12544, 0.718, 0, -0.16, 0, 0),
(6693, 12545, 1, 0, 0.0, 0, 0),
(6694, 12546, 0.638, 0, 0.0, 0, 0),
(6695, 12547, 1, 0, 0.0, 0, 0),
(6696, 12548, 0.269, 0, -1.66, 0, 0),
(6697, 12549, 1, 0, 0.0, 1, 0),
(6725, 12550, 0.864, 0, 0.0, 0, 0),
(6742, 12551, 1, 0, 0.0, 0, 0),
(6802, 12552, 0.718, 0, -2.55, 0, 0),
(6803, 12553, 1.186, 0, 0.0, 0, 0),
(6804, 12554, 0.718, 0, 1.21, 0, 0),
(6829, 12555, 0.685, 0, -2.29, 0, 0),
(6830, 12556, 1, 0, 6.53, 0, 0),
(6900, 12557, 1, 0, 0.0, 0, 0),
(6901, 12558, 1, 0, 0.0, 0, 0),
(6902, 12559, 1, 0, 0.0, 0, 0),
(6903, 12560, 1, 0, 0.0, 1, 0),
(6906, 12561, 1, 0, 0.0, 0, 0),
(6908, 12562, 1, 0, 0.0, 1, 0),
(6910, 12563, 1, 0, 0.0, 0, 0),
(6911, 12564, 1, 0, 0.0, 0, 0),
(6953, 12565, 1.188, 0, 4.12, 0, 0),
(6972, 12566, 1, 0, 0.0, 0, 0),
(6975, 12567, 1, 0, 6.63, 0, 0),
(6976, 12568, 1, 0, 6.81, 0, 0),
(6977, 12569, 1, 0, 6.59, 0, 0),
(7001, 12570, 0.627, 0, 4.0, 0, 0),
(7002, 12571, 0.638, 0, 0.0, 0, 0),
(7054, 12572, 1, 0, 0.0, 0, 0),
(7133, 12573, 1, 0, 0.0, 0, 0),
(7187, 12574, 1, 0, 0.0, 0, 0),
(7230, 12575, 1, 0, 3.62, 0, 0),
(7513, 12576, 0.627, 0, 7.0, 1, 0),
(7514, 12577, 0.627, 0, 7.0, 1, 0),
(7515, 12578, 1.186, 0, 0.0, 1, 0),
(7673, 12579, 1, 0, 0.0, 0, 0),
(7683, 12580, 0.718, 0, -0.96, 0, 0),
(7684, 12581, 1, 0, 0.0, 0, 0),
(7685, 12582, 1.186, 0, 0.0, 1, 0),
(7686, 12583, 1, 0, 0.0, 0, 0),
(7687, 12584, 0.718, 0, -0.5, 0, 0),
(7688, 12585, 1, 0, 0.0, 0, 0),
(7689, 12586, 1, 0, 6.75, 0, 0),
(7690, 12587, 1, 0, 0.0, 0, 0),
(7691, 12588, 1, 0, 0.0, 1, 0),
(7709, 12589, 1, 0, 0.0, 1, 0),
(7711, 12590, 1, 0, 0.0, 1, 0),
(7712, 12591, 1, 0, 0.0, 0, 0),
(7713, 12592, 1.188, 0, 6.64, 0, 0),
(7714, 12593, 0.8, 0, -1.28, 1, 0),
(7718, 12594, 1, 0, 0.0, 0, 0),
(7719, 12595, 1, 0, 0.0, 1, 0),
(7720, 12596, 1, 0, 0.0, 0, 0),
(7721, 12597, 0.8, 0, -2.48, 1, 0),
(7722, 12598, 1, 0, 0.0, 0, 0),
(7723, 12599, 1, 0, 6.64, 0, 0),
(7726, 12600, 0.732, 0, 0.0, 0, 0),
(7727, 12601, 1, 0, 0.0, 0, 0),
(7728, 12602, 1, 0, 0.0, 0, 0),
(7731, 12603, 1, 0, 0.0, 1, 0),
(7736, 12604, 0.718, 0, -1.48, 0, 0),
(7752, 12605, 0.718, 0, -0.96, 0, 0),
(7754, 12606, 1, 0, 0.0, 0, 0),
(7755, 12607, 1, 0, 0.0, 0, 0),
(7756, 12608, 1, 0, 0.0, 0, 0),
(7757, 12609, 1.188, 0, 6.75, 1, 0),
(7758, 12610, 1, 0, 6.74, 0, 0),
(7759, 12611, 1, 0, 0.0, 0, 0),
(7760, 12612, 1, 0, 0.0, 0, 0),
(7761, 12613, 0.718, 0, -1.38, 0, 0),
(7786, 12614, 0.718, 0, -2.14, 0, 0),
(7787, 12615, 0.732, 0, 0.0, 1, 0),
(7888, 12616, 1, 0, 0.0, 0, 0),
(7922, 12617, 1, 0, 0.0, 0, 0),
(7938, 12618, 1, 0, 0.0, 0, 0),
(8174, 12619, 1, 0, 0.0, 0, 0),
(8226, 12620, 0.718, 0, -1.86, 0, 0),
(8345, 12621, 1, 0, 0.0, 0, 0),
(8346, 12622, 1, 0, 0.0, 0, 0),
(8347, 12623, 1, 0, 0.0, 1, 0),
(8348, 12624, 1, 0, 0.0, 0, 0),
(8349, 12625, 1, 0, 0.0, 0, 0),
(8367, 12626, 1, 0, 0.0, 0, 0),
(9240, 12627, 0.718, 0, -3.2, 0, 0),
(9359, 12628, 0.718, 0, -2.58, 0, 0),
(9375, 12629, 1, 0, 0.0, 0, 0),
(9378, 12630, 0.718, 0, -1.5, 0, 0),
(9379, 12631, 1.014, 0, -2.94, 1, 0),
(9383, 12632, 1, 0, 6.68, 0, 0),
(9384, 12633, 0.718, 0, -0.12, 0, 0),
(9385, 12634, 1.204, 0, 7.17, 1, 0),
(9392, 12635, 0.718, 0, -1.71, 0, 0),
(9393, 12636, 1.186, 0, 0.0, 1, 0),
(9394, 12637, 1, 0, 0.0, 0, 0),
(9395, 12638, 1, 0, 0.0, 0, 0),
(9396, 12639, 1, 0, 0.0, 0, 0),
(9397, 12640, 1, 0, 0.0, 0, 0),
(9398, 12641, 1, 0, 0.0, 0, 0),
(9400, 12642, 0.269, 0, -2.19, 0, 0),
(9401, 12643, 0.718, 0, -2.2, 0, 0),
(9403, 12644, 0.732, 0, 0.0, 0, 0),
(9405, 12645, 1, 0, 0.0, 1, 0),
(9406, 12646, 1, 0, 0.0, 0, 0),
(9407, 12647, 1, 0, 0.0, 1, 0),
(9408, 12648, 1, 0, 6.54, 0, 0),
(9410, 12649, 1, 0, 0.0, 1, 0),
(9411, 12650, 1, 0, 0.0, 0, 0),
(9413, 12651, 1, 0, 6.82, 1, 0),
(9414, 12652, 1, 0, 0.0, 0, 0),
(9415, 12653, 1, 0, 0.0, 1, 0),
(9416, 12654, 1, 0, 6.49, 0, 0),
(9420, 12655, 1, 0, 0.0, 0, 0),
(9422, 12656, 0.581, 0, -2.73, 0, 0),
(9424, 12657, 0.718, 0, -1.86, 0, 0),
(9426, 12658, 0.269, 0, -2.21, 0, 0),
(9427, 12659, 0.718, 0, -1.96, 0, 0),
(9429, 12660, 1, 0, 0.0, 1, 0),
(9431, 12661, 1, 0, 0.0, 1, 0),
(9432, 12662, 1, 0, 0.0, 0, 0),
(9433, 12663, 1, 0, 0.0, 1, 0),
(9434, 12664, 1, 0, 0.0, 1, 0),
(9435, 12665, 1, 0, 0.0, 0, 0),
(9445, 12666, 1, 0, 0.0, 0, 0),
(9447, 12667, 1, 0, 0.0, 0, 0),
(9449, 12668, 1, 0, 6.16, 0, 0),
(9450, 12669, 1, 0, 0.0, 0, 0),
(9454, 12670, 1, 0, 0.0, 1, 0),
(9457, 12671, 0.685, 0, -0.38, 0, 0),
(9458, 12672, 0.638, 0, 0.0, 1, 0),
(9459, 12673, 1, 0, 6.92, 0, 0),
(9465, 12674, 0.718, 0, -2.73, 0, 0),
(9470, 12675, 1, 0, 0.0, 1, 0),
(9473, 12676, 1, 0, 0.0, 0, 0),
(9474, 12677, 1, 0, 0.0, 0, 0),
(9476, 12678, 1, 0, 0.0, 0, 0),
(9479, 12679, 1, 0, 0.0, 0, 0),
(9480, 12680, 1, 0, 6.67, 0, 0),
(9481, 12681, 1, 0, 6.78, 0, 0),
(9482, 12682, 1.188, 0, 6.65, 1, 0),
(9484, 12683, 1, 0, 0.0, 1, 0),
(9488, 12684, 0.718, 0, -2.64, 0, 0),
(9490, 12685, 1, 0, 3.31, 0, 0),
(9491, 12686, 1, 0, 0.0, 1, 0),
(9492, 12687, 1, 0, 0.0, 0, 0),
(9508, 12688, 1, 0, 0.0, 0, 0),
(9509, 12689, 1, 0, 0.0, 0, 0),
(9510, 12690, 1, 0, 0.0, 0, 0),
(9512, 12691, 1, 0, 0.0, 0, 0),
(9517, 12692, 1.188, 0, 6.74, 1, 0),
(9533, 12693, 1, 0, 0.0, 0, 0),
(9534, 12694, 1, 0, 0.0, 0, 0),
(9538, 12695, 1, 0, 0.0, 0, 0),
(9588, 12696, 1, 0, 0.0, 0, 0),
(9623, 12697, 1, 0, 0.0, 0, 0),
(9624, 12698, 1, 0, 0.0, 0, 0),
(9625, 12699, 1, 0, 0.0, 2, 0),
(9641, 12700, 1, 0, 0.0, 1, 0),
(9649, 12701, 1, 0, 0.0, 1, 0),
(9650, 12702, 1, 0, 0.0, 0, 0),
(9651, 12703, 0.718, 0, -4.07, 0, 0),
(9652, 12704, 1, 0, 0.0, 0, 0),
(9683, 12705, 1.188, 0, 7.01, 0, 0),
(9684, 12706, 0.718, 0, -3.35, 0, 0),
(9718, 12707, 0.718, 0, -1.53, 0, 0),
(10019, 12708, 1, 0, 0.0, 1, 0),
(10021, 12709, 1, 0, 0.0, 1, 0),
(10041, 12710, 1, 0, 0.0, 1, 0),
(10328, 12711, 1, 0, 0.0, 0, 0),
(10330, 12712, 1, 0, 0.0, 0, 0),
(10332, 12713, 1, 0, 0.0, 0, 0),
(10399, 12714, 1, 0, 0.0, 0, 0),
(10410, 12715, 1, 0, 0.0, 0, 0),
(10411, 12716, 1, 0, 0.0, 0, 0),
(10412, 12717, 1, 0, 0.0, 0, 0),
(10413, 12718, 1, 0, 0.0, 0, 0),
(10571, 12719, 0.718, 0, -0.67, 0, 0),
(10572, 12720, 0.627, 0, 6.0, 1, 0),
(10573, 12721, 1, 0, 6.92, 0, 0),
(10574, 12722, 1, 0, 0.0, 1, 0),
(10578, 12723, 1, 0, 0.0, 0, 0),
(10581, 12724, 1, 0, 0.0, 0, 0),
(10582, 12725, 1, 0, 0.0, 0, 0),
(10583, 12726, 1, 0, 0.0, 0, 0),
(10584, 12727, 1, 0, 0.0, 0, 0),
(10624, 12728, 0.269, 0, -3.19, 0, 0),
(10629, 12729, 1, 0, 0.0, 1, 0),
(10630, 12730, 1, 0, 0.0, 1, 0),
(10631, 12731, 1, 0, 0.0, 0, 0),
(10632, 12732, 1, 0, 0.0, 0, 0),
(10633, 12733, 1, 0, 0.0, 0, 0),
(10634, 12734, 1, 0, 0.0, 1, 0),
(10652, 12735, 1, 0, 6.98, 0, 0),
(10686, 12736, 0.732, 0, 0.0, 0, 0),
(10710, 12737, 1, 0, 0.0, 0, 0),
(10711, 12738, 1, 0, 0.0, 0, 0),
(10749, 12739, 1, 0, 0.0, 0, 0),
(10751, 12740, 1, 0, 0.0, 1, 0),
(10758, 12741, 1, 0, 6.61, 0, 0),
(10760, 12742, 1, 0, 0.0, 0, 0),
(10762, 12743, 1, 0, 0.0, 0, 0),
(10763, 12744, 1, 0, 0.0, 0, 0),
(10764, 12745, 1, 0, 0.0, 0, 0),
(10765, 12746, 1, 0, 0.0, 0, 0),
(10766, 12747, 0.627, 0, 7.0, 1, 0),
(10767, 12748, 0.864, 0, 0.0, 0, 0),
(10768, 12749, 1, 0, 0.0, 0, 0),
(10769, 12750, 1, 0, 0.0, 1, 0),
(10770, 12751, 1.186, 0, 0.0, 1, 0),
(10771, 12752, 1, 0, 0.0, 1, 0),
(10774, 12753, 1, 0, 0.0, 0, 0),
(10775, 12754, 1, 0, 0.0, 0, 0),
(10776, 12755, 1, 0, 0.0, 0, 0),
(10787, 12756, 1, 0, 0.0, 1, 0),
(10795, 12757, 1, 0, 0.0, 1, 0),
(10796, 12758, 1.186, 0, 0.0, 1, 0),
(10798, 12759, 1, 0, 0.0, 0, 0),
(10799, 12760, 1, 0, 6.86, 0, 0),
(10800, 12761, 1, 0, 0.0, 0, 0),
(10801, 12762, 1, 0, 0.0, 0, 0),
(10802, 12763, 1, 0, 0.0, 1, 0),
(10804, 12764, 0.718, 0, -4.64, 0, 0),
(10806, 12765, 1, 0, 0.0, 0, 0),
(10807, 12766, 1, 0, 0.0, 1, 0),
(10808, 12767, 1, 0, 0.0, 1, 0),
(10824, 12768, 1, 0, 0.0, 0, 0),
(10829, 12769, 1, 0, 0.0, 1, 0),
(10833, 12770, 1, 0, 0.0, 0, 0),
(10835, 12771, 0.638, 0, 0.0, 0, 0),
(10836, 12772, 0.581, 0, 10.0, 0, 0),
(10837, 12773, 0.718, 0, -5.69, 0, 0),
(10838, 12774, 0.718, 0, -4.6, 0, 0),
(10842, 12775, 1, 0, 0.0, 1, 0),
(10843, 12776, 1, 0, 0.0, 1, 0),
(10844, 12777, 1.188, 0, 6.04, 1, 0),
(10845, 12778, 1, 0, 0.0, 0, 0),
(10846, 12779, 1, 0, 0.0, 0, 0),
(11121, 12780, 0.718, 0, -0.16, 0, 0),
(11123, 12781, 1, 0, 0.0, 1, 0),
(11124, 12782, 1, 0, 0.0, 0, 0),
(11262, 12783, 1.186, 0, 0.0, 0, 0),
(11263, 12784, 0.627, 0, 7.0, 1, 0),
(11310, 12785, 1, 0, 0.0, 1, 0),
(11311, 12786, 1, 0, 0.0, 0, 0),
(11623, 12787, 1, 0, 0.0, 1, 0),
(11624, 12788, 1, 0, 0.0, 1, 0),
(11625, 12789, 1.186, 0, 0.0, 1, 0),
(11626, 12790, 1, 0, 0.0, 0, 0),
(11627, 12791, 1, 0, 0.0, 0, 0),
(11628, 12792, 0.269, 0, -4.26, 0, 0),
(11629, 12793, 0.581, 0, -4.48, 0, 0),
(11631, 12794, 0.864, 0, 0.0, 0, 0),
(11632, 12795, 1, 0, 0.0, 0, 0),
(11633, 12796, 1, 0, 0.0, 0, 0),
(11634, 12797, 1, 0, 0.0, 0, 0),
(11662, 12798, 1, 0, 0.0, 3, 0),
(11665, 12799, 1, 0, 0.0, 1, 0),
(11669, 12800, 1, 0, 0.0, 2, 0),
(11675, 12801, 1, 0, 0.0, 0, 0),
(11678, 12802, 1, 0, 0.0, 0, 0),
(11679, 12803, 1, 0, 0.0, 0, 0),
(11685, 12804, 1, 0, 0.0, 0, 0),
(11686, 12805, 1, 0, 0.0, 0, 0),
(11702, 12806, 0.718, 0, -5.14, 0, 0),
(11703, 12807, 1, 0, 0.0, 0, 0),
(11722, 12808, 1, 0, 0.0, 2, 0),
(11726, 12809, 1, 0, 0.0, 2, 0),
(11728, 12810, 1, 0, 0.0, 0, 0),
(11729, 12811, 1, 0, 0.0, 0, 0),
(11730, 12812, 1, 0, 0.0, 0, 0),
(11731, 12813, 1, 0, 0.0, 0, 0),
(11735, 12814, 1, 0, 0.0, 1, 0),
(11743, 12815, 0.718, 0, -5.53, 0, 0),
(11745, 12816, 1, 0, 0.0, 0, 0),
(11746, 12817, 1, 0, 0.0, 1, 0),
(11747, 12818, 1, 0, 0.0, 1, 0),
(11748, 12819, 0.627, 0, 10.0, 1, 0),
(11749, 12820, 1, 0, 0.0, 0, 0),
(11750, 12821, 1.188, 0, 6.6, 2, 0),
(11755, 12822, 1, 0, 0.0, 1, 0),
(11782, 12823, 1, 0, 0.0, 1, 0),
(11783, 12824, 1, 0, 0.0, 2, 0),
(11784, 12825, 0.8, 0, -4.05, 1, 0),
(11787, 12826, 1, 0, 0.0, 1, 0),
(11802, 12827, 1, 0, 0.0, 0, 0),
(11803, 12828, 1, 0, 5.35, 0, 0),
(11805, 12829, 0.718, 0, -6.02, 0, 0),
(11807, 12830, 1, 0, 0.0, 1, 0),
(11808, 12831, 1, 0, 0.0, 2, 0),
(11814, 12832, 1, 0, 0.0, 0, 0),
(11816, 12833, 1, 0, 5.31, 0, 0),
(11820, 12834, 1, 0, 0.0, 0, 0),
(11821, 12835, 1, 0, 0.0, 0, 0),
(11822, 12836, 1, 0, 0.0, 1, 0),
(11823, 12837, 1, 0, 0.0, 1, 0),
(11824, 12838, 1, 0, 0.0, 1, 0),
(11839, 12839, 1, 0, 0.0, 0, 0),
(11841, 12840, 1, 0, 0.0, 1, 0),
(11842, 12841, 1, 0, 0.0, 1, 0),
(11866, 12842, 1, 0, 0.0, 0, 0),
(11921, 12843, 1, 0, 5.49, 3, 0),
(11922, 12844, 0.8, 0, -5.73, 1, 0),
(11923, 12845, 0.8, 0, -5.81, 1, 0),
(11925, 12846, 1, 0, 0.0, 0, 0),
(11926, 12847, 1, 0, 0.0, 1, 0),
(11927, 12848, 1, 0, 0.0, 2, 0),
(11929, 12849, 1, 0, 0.0, 0, 0),
(11931, 12850, 1.204, 0, 6.84, 3, 0),
(11932, 12851, 1.188, 0, 6.75, 1, 0),
(11935, 12852, 1.186, 0, 0.0, 1, 0),
(11962, 12853, 1, 0, 0.0, 0, 0),
(12059, 12854, 1, 0, 0.0, 0, 0),
(12105, 12855, 1, 0, 0.0, 0, 0),
(12243, 12856, 1, 0, 6.12, 0, 0),
(12462, 12857, 1, 0, 0.0, 1, 0),
(12463, 12858, 1, 0, 6.67, 0, 0),
(12464, 12859, 1, 0, 0.0, 1, 0),
(12465, 12860, 1, 0, 0.0, 0, 0),
(12466, 12861, 1, 0, 0.0, 0, 0),
(12470, 12862, 1, 0, 0.0, 0, 0),
(12471, 12863, 1.186, 0, 0.0, 0, 0),
(12532, 12864, 1.188, 0, 5.47, 0, 0),
(12535, 12865, 0.718, 0, -4.64, 0, 0),
(12542, 12866, 1, 0, 0.0, 0, 0),
(12546, 12867, 1, 0, 0.0, 0, 0),
(12547, 12868, 1, 0, 0.0, 1, 0),
(12549, 12869, 1, 0, 0.0, 1, 0),
(12550, 12870, 1, 0, 0.0, 1, 0),
(12552, 12871, 1, 0, 0.0, 0, 0),
(12553, 12872, 1, 0, 0.0, 0, 0),
(12554, 12873, 1, 0, 0.0, 1, 0),
(12555, 12874, 1, 0, 0.0, 0, 0),
(12556, 12875, 1, 0, 0.0, 1, 0),
(12557, 12876, 1, 0, 0.0, 0, 0),
(12605, 12877, 0.581, 0, 10.0, 0, 0),
(12608, 12878, 1, 0, 0.0, 0, 0),
(12624, 12879, 1, 0, 0.0, 1, 0),
(12625, 12880, 1, 0, 0.0, 1, 0),
(12626, 12881, 1, 0, 0.0, 1, 0),
(12632, 12882, 1, 0, 0.0, 3, 0),
(12651, 12883, 0.581, 0, -4.95, 1, 0),
(12769, 12884, 1, 0, 6.05, 0, 0),
(12774, 12885, 0.718, 0, -5.17, 1, 0),
(12776, 12886, 1.204, 0, 5.31, 3, 0),
(12793, 12887, 1, 0, 0.0, 0, 0),
(12975, 12888, 1, 0, 2.63, 0, 0),
(12976, 12889, 0.718, 0, -1.41, 0, 0),
(12977, 12890, 1, 0, 0.0, 0, 0),
(12978, 12891, 1, 0, 0.0, 0, 0),
(12982, 12892, 1, 0, 0.0, 0, 0),
(12983, 12893, 1.188, 0, 2.52, 0, 0),
(12985, 12894, 1, 0, 0.0, 1, 0),
(12987, 12895, 1, 0, 0.0, 0, 0),
(12988, 12896, 1, 0, 0.0, 0, 0),
(12989, 12897, 1, 0, 3.05, 0, 0),
(12990, 12898, 0.718, 0, -0.88, 0, 0),
(12994, 12899, 1, 0, 0.0, 0, 0),
(12996, 12900, 1, 0, 0.0, 0, 0),
(12997, 12901, 0.864, 0, 0.0, 0, 0),
(12998, 12902, 1, 0, 0.0, 1, 0),
(12999, 12903, 1, 0, 0.0, 0, 0),
(13002, 12904, 1, 0, 0.0, 0, 0),
(13003, 12905, 1, 0, 5.35, 0, 0),
(13005, 12906, 1, 0, 0.0, 0, 0),
(13007, 12907, 1, 0, 0.0, 1, 0),
(13008, 12908, 1, 0, 0.0, 0, 0),
(13010, 12909, 1, 0, 0.0, 0, 0),
(13011, 12910, 1, 0, 0.0, 0, 0),
(13012, 12911, 1, 0, 0.0, 0, 0),
(13013, 12912, 1, 0, 0.0, 1, 0),
(13014, 12913, 0.718, 0, -4.26, 0, 0),
(13018, 12914, 1, 0, 6.68, 1, 0),
(13021, 12915, 0.293, 0, -3.44, 0, 0),
(13022, 12916, 0.269, 0, -5.49, 0, 0),
(13024, 12917, 0.718, 0, -2.2, 0, 0),
(13025, 12918, 0.685, 0, -0.67, 0, 0),
(13026, 12919, 0.685, 0, -2.64, 0, 0),
(13027, 12920, 0.718, 0, -4.07, 0, 0),
(13029, 12921, 1.186, 0, 0.0, 1, 0),
(13031, 12922, 1.186, 0, 0.0, 2, 0),
(13033, 12923, 0.685, 0, -0.7, 0, 0),
(13034, 12924, 0.718, 0, -1.74, 0, 0),
(13036, 12925, 0.718, 0, -5.81, 1, 0),
(13038, 12926, 0.581, 0, -1.93, 0, 0),
(13039, 12927, 0.581, 0, -3.43, 0, 0),
(13040, 12928, 0.581, 0, -6.0, 0, 0),
(13041, 12929, 1.204, 0, 4.97, 1, 0),
(13042, 12930, 1.188, 0, 6.72, 0, 0),
(13043, 12931, 1, 0, 6.7, 0, 0),
(13045, 12932, 1, 0, 6.75, 0, 0),
(13046, 12933, 1, 0, 6.79, 0, 0),
(13047, 12934, 1, 0, 6.15, 0, 0),
(13048, 12935, 0.718, 0, -1.71, 0, 0),
(13049, 12936, 1.204, 0, 3.15, 1, 0),
(13052, 12937, 1, 0, 6.91, 0, 0),
(13055, 12938, 1, 0, 6.8, 0, 0),
(13056, 12939, 1.204, 0, 5.44, 3, 0),
(13058, 12940, 1.188, 0, 6.51, 0, 0),
(13059, 12941, 1, 0, 6.76, 0, 0),
(13064, 12942, 0.627, 0, 7.0, 0, 0),
(13066, 12943, 1, 0, 0.0, 0, 0),
(13067, 12944, 1, 0, 0.0, 0, 0),
(13068, 12945, 1, 0, 0.0, 0, 0),
(13070, 12946, 1, 0, 0.0, 0, 0),
(13071, 12947, 1, 0, 0.0, 0, 0),
(13073, 12948, 1, 0, 0.0, 0, 0),
(13074, 12949, 1, 0, 0.0, 1, 0),
(13076, 12950, 1, 0, 0.0, 0, 0),
(13077, 12951, 1, 0, 0.0, 0, 0),
(13079, 12952, 0.864, 0, 0.0, 0, 0),
(13081, 12953, 0.864, 0, 0.0, 0, 0),
(13082, 12954, 0.638, 0, 0.0, 0, 0),
(13084, 12955, 1, 0, 0.0, 0, 0),
(13085, 12956, 1, 0, 0.0, 0, 0),
(13087, 12957, 1, 0, 0.0, 0, 0),
(13088, 12958, 1, 0, 0.0, 0, 0),
(13089, 12959, 1, 0, 0.0, 0, 0),
(13091, 12960, 1, 0, 0.0, 1, 0),
(13093, 12961, 1, 0, 0.0, 0, 0),
(13094, 12962, 1, 0, 0.0, 0, 0),
(13095, 12963, 1, 0, 0.0, 0, 0),
(13097, 12964, 1, 0, 0.0, 0, 0),
(13099, 12965, 1, 0, 0.0, 1, 0),
(13100, 12966, 1, 0, 0.0, 0, 0),
(13101, 12967, 1, 0, 0.0, 1, 0),
(13102, 12968, 1, 0, 0.0, 1, 0),
(13103, 12969, 1, 0, 0.0, 0, 0),
(13105, 12970, 1, 0, 0.0, 0, 0),
(13106, 12971, 1, 0, 0.0, 1, 0),
(13108, 12972, 1, 0, 0.0, 0, 0),
(13109, 12973, 1, 0, 0.0, 0, 0),
(13110, 12974, 1, 0, 0.0, 0, 0),
(13111, 12975, 1, 0, 0.0, 0, 0),
(13112, 12976, 1, 0, 0.0, 0, 0),
(13114, 12977, 1, 0, 0.0, 0, 0),
(13115, 12978, 1, 0, 0.0, 0, 0),
(13117, 12979, 1, 0, 0.0, 0, 0),
(13118, 12980, 1, 0, 0.0, 0, 0),
(13119, 12981, 1, 0, 0.0, 0, 0),
(13120, 12982, 1, 0, 0.0, 0, 0),
(13121, 12983, 1, 0, 0.0, 0, 0),
(13122, 12984, 1, 0, 0.0, 0, 0),
(13124, 12985, 1, 0, 0.0, 0, 0),
(13125, 12986, 1, 0, 0.0, 0, 0),
(13126, 12987, 1, 0, 0.0, 0, 0),
(13127, 12988, 1, 0, 0.0, 0, 0),
(13128, 12989, 1, 0, 0.0, 0, 0),
(13129, 12990, 1, 0, 0.0, 0, 0),
(13130, 12991, 1, 0, 0.0, 0, 0),
(13131, 12992, 1, 0, 0.0, 0, 0),
(13132, 12993, 1, 0, 0.0, 0, 0),
(13134, 12994, 1, 0, 0.0, 0, 0),
(13135, 12995, 1, 0, 0.0, 0, 0),
(13139, 12996, 0.581, 0, -3.64, 0, 0),
(13144, 12997, 1, 0, 0.0, 0, 0),
(13145, 12998, 1, 0, 0.0, 0, 0),
(13181, 12999, 1, 0, 0.0, 1, 0),
(13182, 13000, 0.718, 0, -5.78, 0, 0),
(13199, 13001, 1, 0, 0.0, 0, 0),
(13245, 13002, 0.732, 0, 0.0, 1, 0),
(13255, 13003, 1, 0, 0.0, 0, 0),
(13257, 13004, 1, 0, 0.0, 0, 0),
(13261, 13005, 1.186, 0, 0.0, 0, 0),
(13282, 13006, 1, 0, 0.0, 0, 0),
(13283, 13007, 1, 0, 0.0, 0, 0),
(13284, 13008, 1, 0, 0.0, 0, 0),
(13376, 13009, 1, 0, 0.0, 0, 0),
(13378, 13010, 1, 0, 0.0, 0, 0),
(13383, 13011, 1, 0, 0.0, 0, 0),
(13384, 13012, 1, 0, 0.0, 0, 0),
(13394, 13013, 1, 0, 0.0, 1, 0),
(13396, 13014, 0.627, 0, 11.0, 1, 0),
(13400, 13015, 1, 0, 0.0, 1, 0),
(13402, 13016, 1, 0, 0.0, 0, 0),
(13403, 13017, 1, 0, 0.0, 0, 0),
(13404, 13018, 1, 0, 0.0, 0, 0),
(13405, 13019, 1, 0, 0.0, 1, 0),
(14136, 13020, 1, 0, 0.0, 1, 0),
(14137, 13021, 1, 0, 0.0, 0, 0),
(14147, 13022, 1, 0, 0.0, 0, 0),
(14148, 13023, 1, 0, 0.0, 1, 0),
(14149, 13024, 1, 0, 0.0, 0, 0),
(14150, 13025, 1, 0, 0.0, 0, 0),
(14151, 13026, 0.718, 0, -0.15, 0, 0),
(14549, 13027, 1, 0, 0.0, 1, 0),
(14550, 13028, 1, 0, 0.0, 0, 0),
(14551, 13029, 1, 0, 0.0, 0, 0),
(14552, 13030, 1, 0, 0.0, 1, 0),
(15045, 13031, 1, 0, 0.0, 0, 0),
(15046, 13032, 1, 0, 0.0, 0, 0),
(15048, 13033, 1, 0, 0.0, 0, 0),
(15049, 13034, 1, 0, 0.0, 0, 0),
(15050, 13035, 1, 0, 0.0, 0, 0),
(15056, 13036, 1, 0, 0.0, 3, 0),
(15057, 13037, 1, 0, 0.0, 3, 0),
(15058, 13038, 1, 0, 0.0, 3, 0),
(15060, 13039, 1, 0, 0.0, 1, 0),
(15061, 13040, 1, 0, 0.0, 0, 0),
(15063, 13041, 1, 0, 0.0, 2, 0),
(15064, 13042, 1, 0, 0.0, 0, 0),
(15065, 13043, 1, 0, 0.0, 0, 0),
(15066, 13044, 1, 0, 0.0, 0, 0),
(15067, 13045, 1, 0, 0.0, 0, 0),
(15104, 13046, 1, 0, 0.0, 1, 0),
(15107, 13047, 1.186, 0, 0.0, 1, 0),
(15108, 13048, 1.186, 0, 0.0, 1, 0),
(15200, 13049, 1, 0, 0.0, 0, 0),
(15799, 13050, 1, 0, 0.0, 0, 0),
(15800, 13051, 0.718, 0, -5.31, 0, 0),
(15801, 13052, 0.685, 0, -5.25, 0, 0),
(15802, 13053, 1, 0, 0.0, 0, 0),
(16315, 13054, 1, 0, 0.0, 0, 0),
(16334, 13055, 1, 0, 0.0, 0, 0),
(16336, 13056, 1, 0, 0.0, 0, 0),
(16340, 13057, 1, 0, 0.0, 0, 0),
(16608, 13058, 1, 0, 0.0, 0, 0),
(16670, 13059, 1, 0, 0.0, 0, 0),
(16671, 13060, 1, 0, 0.0, 0, 0),
(16672, 13061, 1, 0, 0.0, 0, 0),
(16673, 13062, 1, 0, 0.0, 0, 0),
(16675, 13063, 1, 0, 0.0, 0, 0),
(16676, 13064, 1, 0, 0.0, 0, 0),
(16680, 13065, 1, 0, 0.0, 0, 0),
(16681, 13066, 1, 0, 0.0, 0, 0),
(16682, 13067, 1, 0, 0.0, 0, 0),
(16683, 13068, 1, 0, 0.0, 0, 0),
(16684, 13069, 1, 0, 0.0, 0, 0),
(16685, 13070, 1, 0, 0.0, 0, 0),
(16691, 13071, 1, 0, 0.0, 0, 0),
(16692, 13072, 1, 0, 0.0, 0, 0),
(16696, 13073, 1, 0, 0.0, 0, 0),
(16697, 13074, 1, 0, 0.0, 0, 0),
(16702, 13075, 1, 0, 0.0, 0, 0),
(16703, 13076, 1, 0, 0.0, 0, 0),
(16704, 13077, 1, 0, 0.0, 0, 0),
(16705, 13078, 1, 0, 0.0, 0, 0),
(16710, 13079, 1, 0, 0.0, 0, 0),
(16711, 13080, 1, 0, 0.0, 0, 0),
(16712, 13081, 1, 0, 0.0, 0, 0),
(16713, 13082, 1, 0, 0.0, 0, 0),
(16714, 13083, 1, 0, 0.0, 0, 0),
(16715, 13084, 1, 0, 0.0, 0, 0),
(16716, 13085, 1, 0, 0.0, 0, 0),
(16717, 13086, 1, 0, 0.0, 0, 0),
(16722, 13087, 1, 0, 0.0, 0, 0),
(16723, 13088, 1, 0, 0.0, 0, 0),
(16724, 13089, 1, 0, 0.0, 0, 0),
(16725, 13090, 1, 0, 0.0, 0, 0),
(16734, 13091, 1, 0, 0.0, 0, 0),
(16735, 13092, 1, 0, 0.0, 0, 0),
(16736, 13093, 1, 0, 0.0, 0, 0),
(16737, 13094, 1, 0, 0.0, 0, 0),
(16887, 13095, 1.186, 0, 0.0, 0, 0),
(16975, 13096, 1, 0, 0.0, 0, 0),
(16977, 13097, 1, 0, 0.0, 0, 0),
(16978, 13098, 1, 0, 0.0, 0, 0),
(16982, 13099, 1, 0, 0.0, 0, 0),
(16989, 13100, 1, 0, 0.0, 0, 0),
(16999, 13101, 1, 0, 0.0, 0, 0),
(17007, 13102, 1, 0, 0.0, 0, 0),
(17050, 13103, 1, 0, 0.0, 0, 0),
(17055, 13104, 0.685, 0, -3.18, 0, 0),
(17061, 13105, 1, 0, 0.0, 0, 0),
(17191, 13106, 1.188, 0, 6.57, 0, 0),
(17707, 13107, 1, 0, 0.0, 0, 0),
(17710, 13108, 0.685, 0, -4.49, 0, 0),
(17711, 13109, 1, 0, 0.0, 0, 0),
(17713, 13110, 1, 0, 0.0, 2, 0),
(17714, 13111, 1, 0, 0.0, 0, 0),
(17715, 13112, 1, 0, 0.0, 0, 0),
(17717, 13113, 0.581, 0, -4.55, 0, 0),
(17718, 13114, 0.638, 0, 0.0, 0, 0),
(17719, 13115, 0.718, 0, -4.03, 1, 0),
(17728, 13116, 1, 0, 0.0, 0, 0),
(17732, 13117, 1, 0, 0.0, 0, 0),
(17733, 13118, 0.685, 0, -3.98, 0, 0),
(17734, 13119, 1, 0, 0.0, 1, 0),
(17736, 13120, 1, 0, 0.0, 0, 0),
(17737, 13121, 1.186, 0, 0.0, 1, 0),
(17739, 13122, 1, 0, 0.0, 0, 0),
(17740, 13123, 1, 0, 0.0, 1, 0),
(17741, 13124, 1, 0, 0.0, 1, 0),
(17742, 13125, 1, 0, 0.0, 0, 0),
(17745, 13126, 0.581, 0, 9.0, 0, 0),
(17746, 13127, 1, 0, 0.0, 0, 0),
(17748, 13128, 1, 0, 0.0, 1, 0),
(17749, 13129, 1, 0, 0.0, 0, 0),
(17750, 13130, 1, 0, 0.0, 1, 0),
(17751, 13131, 1, 0, 0.0, 0, 0),
(17754, 13132, 1, 0, 0.0, 0, 0),
(17755, 13133, 1, 0, 0.0, 1, 0),
(17767, 13134, 1, 0, 0.0, 0, 0),
(18023, 13135, 1, 0, 0.0, 0, 0),
(18043, 13136, 1, 0, 0.0, 0, 0),
(18044, 13137, 0.718, 0, -5.81, 0, 0),
(18082, 13138, 1.188, 0, 6.49, 1, 0),
(18083, 13139, 1, 0, 0.0, 0, 0),
(18238, 13140, 1, 0, 0.0, 1, 0),
(18289, 13141, 1, 0, 0.0, 1, 0),
(18295, 13142, 1, 0, 0.0, 0, 0),
(18296, 13143, 1, 0, 0.0, 0, 0),
(18298, 13144, 1, 0, 0.0, 0, 0),
(18303, 13145, 0.732, 0, 0.0, 0, 0),
(18304, 13146, 1, 0, 0.0, 0, 0),
(18309, 13147, 1, 0, 0.0, 1, 0),
(18310, 13148, 0.718, 0, -4.95, 0, 0),
(18311, 13149, 1.188, 0, 6.06, 0, 0),
(18312, 13150, 1, 0, 0.0, 0, 0),
(18313, 13151, 1, 0, 0.0, 1, 0),
(18314, 13152, 1, 0, 0.0, 0, 0),
(18316, 13153, 1.186, 0, 0.0, 0, 0),
(18317, 13154, 1, 0, 0.0, 1, 0),
(18318, 13155, 1, 0, 0.0, 1, 0),
(18320, 13156, 1, 0, 0.0, 0, 0),
(18321, 13157, 0.8, 0, -5.0, 1, 0),
(18322, 13158, 1, 0, 0.0, 1, 0),
(18323, 13159, 0.269, 0, -5.45, 1, 0),
(18324, 13160, 1, 0, 6.1, 1, 0),
(18325, 13161, 1, 0, 0.0, 0, 0),
(18326, 13162, 1, 0, 0.0, 0, 0),
(18327, 13163, 1, 0, 0.0, 2, 0),
(18328, 13164, 1, 0, 0.0, 0, 0),
(18338, 13165, 0.627, 0, 12.0, 1, 0),
(18341, 13166, 1, 0, 0.0, 0, 0),
(18342, 13167, 0.732, 0, 0.0, 0, 0),
(18344, 13168, 1, 0, 0.0, 0, 0),
(18428, 13169, 1, 0, 0.0, 0, 0),
(18430, 13170, 1, 0, 0.0, 0, 0),
(18432, 13171, 1, 0, 0.0, 0, 0),
(18435, 13172, 1, 0, 0.0, 0, 0),
(18436, 13173, 1, 0, 0.0, 0, 0),
(18437, 13174, 1, 0, 0.0, 0, 0),
(18442, 13175, 1, 0, 0.0, 0, 0),
(18444, 13176, 1, 0, 0.0, 0, 0),
(18447, 13177, 1, 0, 0.0, 0, 0),
(18449, 13178, 1, 0, 0.0, 0, 0),
(18453, 13179, 1, 0, 0.0, 0, 0),
(18455, 13180, 1, 0, 0.0, 0, 0),
(18457, 13181, 1, 0, 0.0, 0, 0),
(18491, 13182, 0.685, 0, -5.73, 0, 0),
(18535, 13183, 0.638, 0, 0.0, 0, 0),
(18536, 13184, 1.186, 0, 0.0, 0, 0),
(18585, 13185, 1, 0, 0.0, 0, 0),
(18586, 13186, 1, 0, 0.0, 0, 0),
(18671, 13187, 0.718, 0, -4.85, 0, 0),
(18692, 13188, 1, 0, 0.0, 0, 0),
(18697, 13189, 1, 0, 0.0, 0, 0),
(18698, 13190, 1, 0, 0.0, 1, 0),
(18699, 13191, 1, 0, 0.0, 0, 0),
(18700, 13192, 1, 0, 0.0, 0, 0),
(18701, 13193, 1, 0, 0.0, 0, 0),
(18709, 13194, 1, 0, 0.0, 1, 0),
(18710, 13195, 1, 0, 0.0, 0, 0),
(18725, 13196, 1, 0, 6.74, 1, 0),
(18727, 13197, 1, 0, 0.0, 1, 0),
(18743, 13198, 1, 0, 0.0, 0, 0),
(18744, 13199, 1, 0, 0.0, 0, 0),
(18745, 13200, 1, 0, 0.0, 1, 0),
(18762, 13201, 1.186, 0, 0.0, 1, 0),
(18948, 13202, 1, 0, 0.0, 0, 0),
(19044, 13203, 1, 0, 0.0, 0, 0),
(19047, 13204, 1, 0, 0.0, 0, 0),
(19051, 13205, 1, 0, 0.0, 0, 0),
(19052, 13206, 1, 0, 0.0, 0, 0),
(19056, 13207, 1, 0, 0.0, 0, 0),
(19065, 13208, 1, 0, 0.0, 0, 0),
(19121, 13209, 1, 0, 0.0, 1, 0),
(19159, 13210, 1, 0, 0.0, 0, 0),
(19507, 13211, 1, 0, 0.0, 0, 0),
(19508, 13212, 1, 0, 0.0, 0, 0),
(19511, 13213, 1, 0, 0.0, 0, 0),
(19512, 13214, 1, 0, 0.0, 0, 0),
(19513, 13215, 1, 0, 0.0, 0, 0),
(19515, 13216, 1, 0, 0.0, 0, 0),
(19516, 13217, 1, 0, 0.0, 0, 0),
(19517, 13218, 1, 0, 0.0, 0, 0),
(19519, 13219, 1, 0, 0.0, 1, 0),
(19520, 13220, 1, 0, 0.0, 1, 0),
(19521, 13221, 1, 0, 0.0, 1, 0),
(19523, 13222, 1, 0, 0.0, 1, 0),
(19524, 13223, 1, 0, 0.0, 1, 0),
(19525, 13224, 1, 0, 0.0, 1, 0),
(19527, 13225, 1, 0, 0.0, 1, 0),
(19528, 13226, 1, 0, 0.0, 1, 0),
(19529, 13227, 1, 0, 0.0, 1, 0),
(19531, 13228, 1, 0, 0.0, 1, 0),
(19532, 13229, 1, 0, 0.0, 1, 0),
(19533, 13230, 1, 0, 0.0, 1, 0),
(19535, 13231, 1, 0, 0.0, 0, 0),
(19536, 13232, 1, 0, 0.0, 0, 0),
(19537, 13233, 1, 0, 0.0, 0, 0),
(19539, 13234, 1, 0, 0.0, 0, 0),
(19540, 13235, 1, 0, 0.0, 0, 0),
(19541, 13236, 1, 0, 0.0, 0, 0),
(19543, 13237, 0.718, 0, -4.26, 0, 0),
(19544, 13238, 0.718, 0, -2.4, 0, 0),
(19545, 13239, 0.718, 0, -1.21, 0, 0),
(19547, 13240, 0.718, 0, -4.26, 0, 0),
(19548, 13241, 0.718, 0, -2.4, 0, 0),
(19549, 13242, 0.718, 0, -1.21, 0, 0),
(19551, 13243, 0.718, 0, -4.07, 0, 0),
(19552, 13244, 0.718, 0, -2.26, 0, 0),
(19553, 13245, 0.718, 0, -1.09, 0, 0),
(19555, 13246, 0.718, 0, -4.07, 0, 0),
(19556, 13247, 0.718, 0, -2.26, 0, 0),
(19557, 13248, 0.718, 0, -1.09, 0, 0),
(19559, 13249, 0.269, 0, -4.47, 0, 0),
(19560, 13250, 0.269, 0, -2.77, 0, 0),
(19563, 13251, 0.269, 0, -4.47, 0, 0),
(19564, 13252, 0.269, 0, -2.77, 0, 0),
(19567, 13253, 1.188, 0, 6.6, 0, 0),
(19568, 13254, 1.188, 0, 6.58, 0, 0),
(19569, 13255, 1.188, 0, 5.37, 0, 0),
(19571, 13256, 1.188, 0, 6.6, 0, 0),
(19572, 13257, 1.188, 0, 6.58, 0, 0),
(19573, 13258, 1.188, 0, 5.37, 0, 0),
(19580, 13259, 1, 0, 0.0, 0, 0),
(19581, 13260, 1, 0, 0.0, 0, 0),
(19583, 13261, 1, 0, 0.0, 0, 0),
(19584, 13262, 1, 0, 0.0, 0, 0),
(19589, 13263, 1, 0, 0.0, 0, 0),
(19590, 13264, 1, 0, 0.0, 0, 0),
(19596, 13265, 1, 0, 0.0, 1, 0),
(19597, 13266, 1, 0, 0.0, 1, 0),
(19982, 13267, 1, 0, 0.0, 0, 0),
(19984, 13268, 1, 0, 0.0, 1, 0),
(19986, 13269, 1, 0, 0.0, 0, 0),
(20003, 13270, 0.864, 0, 0.0, 0, 0),
(20005, 13271, 0.802, 0, 0.0, 0, 0),
(20006, 13272, 1, 0, 0.0, 0, 0),
(20035, 13273, 0.685, 0, -3.47, 0, 0),
(20037, 13274, 1, 0, 0.0, 1, 0),
(20082, 13275, 0.627, 0, 10.0, 1, 0),
(20083, 13276, 1, 0, 6.91, 1, 0),
(20088, 13277, 1, 0, 0.0, 1, 0),
(20089, 13278, 1, 0, 0.0, 1, 0),
(20091, 13279, 1, 0, 0.0, 0, 0),
(20092, 13280, 1, 0, 0.0, 0, 0),
(20093, 13281, 1, 0, 0.0, 0, 0),
(20094, 13282, 1, 0, 0.0, 2, 0),
(20095, 13283, 1, 0, 0.0, 2, 0),
(20096, 13284, 1, 0, 0.0, 2, 0),
(20097, 13285, 1, 0, 0.0, 3, 0),
(20098, 13286, 1, 0, 0.0, 1, 0),
(20099, 13287, 1, 0, 0.0, 1, 0),
(20100, 13288, 1, 0, 0.0, 0, 0),
(20101, 13289, 1, 0, 0.0, 0, 0),
(20102, 13290, 1, 0, 0.0, 0, 0),
(20103, 13291, 1, 0, 0.0, 1, 0),
(20104, 13292, 1, 0, 0.0, 0, 0),
(20105, 13293, 1, 0, 0.0, 0, 0),
(20106, 13294, 1, 0, 0.0, 1, 0),
(20107, 13295, 1, 0, 0.0, 0, 0),
(20108, 13296, 1, 0, 0.0, 0, 0),
(20109, 13297, 1, 0, 0.0, 0, 0),
(20110, 13298, 1, 0, 0.0, 0, 0),
(20111, 13299, 1, 0, 0.0, 0, 0),
(20112, 13300, 1, 0, 0.0, 0, 0),
(20113, 13301, 1, 0, 0.0, 0, 0),
(20114, 13302, 1, 0, 0.0, 0, 0),
(20115, 13303, 1, 0, 0.0, 1, 0),
(20118, 13304, 1, 0, 0.0, 1, 0),
(20119, 13305, 1, 0, 0.0, 0, 0),
(20120, 13306, 1, 0, 0.0, 0, 0),
(20121, 13307, 1, 0, 0.0, 0, 0),
(20122, 13308, 1, 0, 0.0, 0, 0),
(20123, 13309, 1, 0, 0.0, 0, 0),
(20124, 13310, 1, 0, 0.0, 1, 0),
(20125, 13311, 1, 0, 0.0, 0, 0),
(20126, 13312, 1, 0, 0.0, 0, 0),
(20127, 13313, 1, 0, 0.0, 0, 0),
(20128, 13314, 1, 0, 0.0, 0, 0),
(20129, 13315, 1, 0, 0.0, 0, 0),
(20151, 13316, 1, 0, 0.0, 1, 0),
(20153, 13317, 1, 0, 0.0, 1, 0),
(20155, 13318, 1, 0, 0.0, 0, 0),
(20156, 13319, 1, 0, 0.0, 0, 0),
(20157, 13320, 1, 0, 0.0, 0, 0),
(20160, 13321, 1, 0, 0.0, 2, 0),
(20161, 13322, 1, 0, 0.0, 2, 0),
(20162, 13323, 1, 0, 0.0, 2, 0),
(20164, 13324, 1, 0, 0.0, 1, 0),
(20165, 13325, 1, 0, 0.0, 3, 0),
(20166, 13326, 1, 0, 0.0, 1, 0),
(20168, 13327, 1, 0, 0.0, 0, 0),
(20169, 13328, 1, 0, 0.0, 0, 0),
(20170, 13329, 1, 0, 0.0, 0, 0),
(20172, 13330, 1, 0, 0.0, 0, 0),
(20173, 13331, 1, 0, 0.0, 0, 0),
(20174, 13332, 1, 0, 0.0, 1, 0),
(20178, 13333, 1, 0, 0.0, 0, 0),
(20179, 13334, 1, 0, 0.0, 1, 0),
(20180, 13335, 1, 0, 0.0, 0, 0),
(20182, 13336, 1, 0, 0.0, 0, 0),
(20183, 13337, 1, 0, 0.0, 0, 0),
(20185, 13338, 1, 0, 0.0, 0, 0),
(20187, 13339, 1, 0, 0.0, 0, 0),
(20188, 13340, 1, 0, 0.0, 0, 0),
(20189, 13341, 1, 0, 0.0, 0, 0),
(20193, 13342, 1, 0, 0.0, 1, 0),
(20196, 13343, 1, 0, 0.0, 1, 0),
(20197, 13344, 1, 0, 0.0, 0, 0),
(20198, 13345, 1, 0, 0.0, 0, 0),
(20200, 13346, 1, 0, 0.0, 0, 0),
(20201, 13347, 1, 0, 0.0, 0, 0),
(20202, 13348, 1, 0, 0.0, 0, 0),
(20205, 13349, 1, 0, 0.0, 1, 0),
(20206, 13350, 1, 0, 0.0, 0, 0),
(20207, 13351, 1, 0, 0.0, 0, 0),
(20209, 13352, 1, 0, 0.0, 0, 0),
(20210, 13353, 1, 0, 0.0, 0, 0),
(20211, 13354, 1, 0, 0.0, 0, 0),
(20218, 13355, 1, 0, 0.0, 0, 0),
(20219, 13356, 1, 0, 0.0, 0, 0),
(20255, 13357, 1, 0, 0.0, 0, 0),
(20296, 13358, 1, 0, 0.0, 0, 0),
(20369, 13359, 1, 0, 0.0, 1, 0),
(20425, 13360, 1.188, 0, 3.57, 0, 0),
(20426, 13361, 1, 0, 0.0, 1, 0),
(20427, 13362, 1, 0, 0.0, 1, 0),
(20428, 13363, 1, 0, 0.0, 1, 0),
(20429, 13364, 1, 0, 0.0, 0, 0),
(20430, 13365, 0.718, 0, -1.09, 0, 0),
(20431, 13366, 1, 0, 0.0, 1, 0),
(20434, 13367, 1.188, 0, 3.57, 0, 0),
(20439, 13368, 1, 0, 0.0, 0, 0),
(20440, 13369, 0.718, 0, -1.09, 0, 0),
(20441, 13370, 0.718, 0, -0.8, 0, 0),
(20442, 13371, 1, 0, 0.0, 0, 0),
(20443, 13372, 0.718, 0, -0.8, 0, 0),
(20444, 13373, 1, 0, 0.0, 0, 0),
(20502, 13374, 0.864, 0, 0.0, 0, 0),
(20504, 13375, 1.188, 0, 6.76, 1, 0),
(20505, 13376, 1, 0, 0.0, 1, 0),
(20517, 13377, 1, 0, 0.0, 1, 0),
(20521, 13378, 1, 0, 0.0, 3, 0),
(20522, 13379, 1, 0, 0.0, 0, 0),
(20524, 13380, 1, 0, 0.0, 0, 0),
(20530, 13381, 1, 0, 0.0, 1, 0),
(20536, 13382, 1.188, 0, 6.76, 3, 0),
(20556, 13383, 1, 0, 6.91, 3, 0),
(20647, 13384, 0.8, 0, -4.81, 2, 0),
(20832, 13385, 1, 0, 0.0, 0, 0),
(20969, 13386, 1, 0, 0.0, 1, 0),
(21278, 13387, 1, 0, 0.0, 0, 0),
(21753, 13388, 1, 0, 0.0, 1, 0),
(21774, 13389, 1, 0, 0.0, 3, 0),
(21791, 13390, 1, 0, 0.0, 1, 0),
(22205, 13391, 1, 0, 0.0, 0, 0),
(22208, 13392, 1, 0, 6.13, 0, 0),
(22212, 13393, 1, 0, 0.0, 0, 0),
(22223, 13394, 1, 0, 0.0, 0, 0),
(22230, 13395, 1, 0, 0.0, 0, 0),
(22234, 13396, 1, 0, 0.0, 1, 0),
(22240, 13397, 1, 0, 0.0, 3, 0),
(22241, 13398, 1, 0, 0.0, 0, 0),
(22242, 13399, 1, 0, 0.0, 0, 0),
(22245, 13400, 1, 0, 0.0, 1, 0),
(22254, 13401, 0.627, 0, 11.0, 2, 0),
(22255, 13402, 1, 0, 0.0, 0, 0),
(22256, 13403, 1, 0, 0.0, 1, 0),
(22257, 13404, 1, 0, 0.0, 1, 0),
(22266, 13405, 0.685, 0, -5.9, 1, 0),
(22270, 13406, 1, 0, 0.0, 0, 0),
(22271, 13407, 1, 0, 0.0, 1, 0),
(22272, 13408, 1, 0, 0.0, 1, 0),
(22273, 13409, 1, 0, 0.0, 0, 0),
(22274, 13410, 1, 0, 0.0, 0, 0),
(22275, 13411, 1, 0, 0.0, 1, 0),
(22458, 13412, 1.188, 0, 6.91, 5, 0),
(22980, 13413, 1.188, 0, 2.58, 0, 0),
(22995, 13414, 1, 0, 2.49, 0, 0),
(23168, 13415, 0.8, 0, -0.56, 1, 0),
(23169, 13416, 1, 0, 0.0, 1, 0),
(23171, 13417, 1, 0, 4.71, 0, 0),
(23173, 13418, 1, 0, 0.0, 1, 0),
(23177, 13419, 0.627, 0, 7.0, 1, 0),
(23178, 13420, 1, 0, 0.0, 1, 0),
(25464, 13421, 1, 0, 2.52, 0, 0),
(29157, 13422, 1, 0, 0.0, 1, 0),
(29158, 13423, 1, 0, 0.0, 0, 0),
(29964, 13424, 1, 0, 0.0, 0, 0),
(29970, 13425, 1, 0, 0.0, 1, 0),
(29971, 13426, 1, 0, 0.0, 0, 0),
(30069, 13427, 1, 0, 0.0, 0, 0),
(30070, 13428, 1, 0, 0.0, 0, 0),
(30071, 13429, 0.718, 0, -3.49, 0, 0),
(30072, 13430, 0.718, 0, -3.49, 0, 0),
(30804, 13431, 1, 0, 0.0, 2, 0),
(34107, 13432, 1, 0, 0.0, 0, 0),
(34415, 13433, 0.732, 0, 0.0, 0, 0),
(34416, 13434, 1, 0, 0.0, 1, 0),
(34417, 13435, 1, 0, 0.0, 0, 0),
(34418, 13436, 0.627, 0, 9.0, 1, 0),
(34419, 13437, 0.409, 0, 6.0, 0, 0),
(34421, 13438, 1, 0, 0.0, 0, 0),
(34422, 13439, 1, 0, 0.0, 0, 0),
(43515, 13440, 1.186, 0, 0.0, 0, 0),
(43654, 13441, 1.186, 0, 0.0, 0, 0),
(43656, 13442, 1.144, 0, 0.0, 0, 0),
(43657, 13443, 1.144, 0, 0.0, 0, 0),
(43660, 13444, 1.186, 0, 0.0, 0, 0),
(43661, 13445, 1.144, 0, 0.0, 0, 0),
(43663, 13446, 1.186, 0, 0.0, 0, 0),
(43664, 13447, 1.186, 0, 0.0, 0, 0),
(44213, 13448, 1, 0, 0.0, 0, 0),
(44215, 13449, 1, 0, 0.0, 0, 0),
(44217, 13450, 0.718, 0, -2.73, 0, 0),
(44218, 13451, 1, 0, 6.7, 0, 0),
(44219, 13452, 1.188, 0, 6.52, 0, 0),
(45626, 13453, 1, 0, 0.0, 0, 0),
(45627, 13454, 1, 0, 0.0, 0, 0);

