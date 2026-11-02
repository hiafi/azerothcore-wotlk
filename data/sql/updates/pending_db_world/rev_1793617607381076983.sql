-- Will of the Necropolis aura ranks: restore the stock spell_ranks chain that the single-rank rollout
-- (2026_09_01_26) deleted, so spell_dk_will_of_the_necropolis (bound to -52284) attaches to ranks 2 and 3 again
-- (without the chain 52285 / 52286 were plain 10 / 15 point absorbs spent on the first hit).
DELETE FROM `spell_ranks` WHERE `first_spell_id` = 52284;
INSERT INTO `spell_ranks` (`first_spell_id`, `spell_id`, `rank`) VALUES
(52284, 52284, 1),
(52284, 52285, 2),
(52284, 52286, 3);
