-- Single-rank spell system (docs/single-rank-spell-system.md), Druid pass, work item 3:
-- world-DB migration for the 56 bootstrapped Druid abilities. The Spell.dbc side (BasePoints,
-- RealPointsPerLevel, coefficients, MaxLevel, ManaCostPct) is handled by apps/dbc-tools/generate.py
-- (see the sibling rev_*.sql it produced). This file handles the tables that pipeline doesn't
-- touch: spell_ranks (the collapsed rank chains no longer exist as chains), trainer_spell (only
-- the surviving rank-1 spell should still be trainer-taught), and spell_bonus_data (stale
-- coefficient overrides confirmed redundant against the now-correct EffectBonusMultiplier).
--
-- Step 3's NPC/item/quest audit on the 287 superseded ranks found:
--   - 7 referenced by item_template (spellid_2 - proc/on-use trinkets: Idol-type items) and 3 by
--     quest_template (RewardSpell/RewardDisplaySpell) - kept in source/spells/druid.csv, annotated.
--   - 15 referenced only by smart_scripts/creature_template_spell (NPC casters, all well below the
--     level-20-50 risk band or using an unaffected superseded ID whose spell_dbc row we never
--     touch) - moved to source/spells/npc.csv.
--   - The remaining 262 have no reference anywhere - dropped from source entirely.
-- Step 5 found 20 survivors with a spell_bonus_data row: 16 have EffectBonusMultiplier populated
-- (nonzero) at both rank 1 and the max rank on the relevant effect - safe, redundant, deleted
-- below. Thorns (467) has EffectBonusMultiplier == 0 at every rank for its self-buff effect -
-- spell_bonus_data is the sole source of its scaling, left untouched. 4 more survivors
-- (Swipe (Bear) 779, Rake 1822, Pounce 9005, Lacerate 33745) have only ap_bonus/ap_dot_bonus rows
-- (the AP-scaling gotcha), confirmed flat across every rank - no write needed, same finding as
-- rogue/DK.

-- Every rank of each of the 56 collapsed chains (56 survivors + 287 superseded ranks) loses its
-- spell_ranks entry. GetRank() defaults to 1 with no chain entry, so this is safe -- matches what
-- a never-ranked spell already looks like.
DELETE FROM `spell_ranks` WHERE `first_spell_id` IN (
    99, 339, 467, 740, 774, 779, 1079, 1082, 1126, 1822, 1850, 2637, 2908, 2912, 5176, 5185, 5211,
    5217, 5221, 5487, 5570, 6785, 6807, 8921, 8936, 8998, 9005, 16689, 16914, 16952, 19975, 20484,
    21849, 22568, 22570, 33745, 33763, 33876, 33878, 33943, 42231, 44203, 45281, 47179, 48435,
    48438, 48505, 50170, 50286, 50288, 50294, 50516, 50769, 58179, 60431, 61391
);

-- Only the 287 superseded ranks lose their trainer_spell row; the 56 survivors' rows are
-- unchanged (same SpellId, same ReqLevel as before -- the collapse didn't move learn levels).
-- Applies regardless of which step-7 bucket a superseded ID landed in -- an item- or
-- quest-referenced rank still isn't trainer-taught any more, it's just still reachable through
-- that other mechanism, which doesn't touch trainer_spell at all.
DELETE FROM `trainer_spell` WHERE `SpellId` IN (
    769, 780, 782, 1058, 1062, 1075, 1430, 1735, 1823, 1824, 2090, 2091, 3029, 3627, 5177, 5178,
    5179, 5180, 5186, 5187, 5188, 5189, 5195, 5196, 5201, 5232, 5234, 6756, 6778, 6780, 6787, 6793,
    6798, 6800, 6808, 6809, 8903, 8905, 8907, 8910, 8914, 8918, 8924, 8925, 8926, 8927, 8928, 8929,
    8938, 8939, 8940, 8941, 8949, 8950, 8951, 8955, 8972, 8983, 8992, 9000, 9490, 9492, 9493, 9634,
    9745, 9747, 9750, 9752, 9754, 9756, 9758, 9821, 9823, 9827, 9829, 9830, 9833, 9834, 9835, 9839,
    9840, 9841, 9845, 9846, 9849, 9850, 9852, 9853, 9856, 9857, 9858, 9862, 9863, 9866, 9867, 9875,
    9876, 9880, 9881, 9884, 9885, 9888, 9889, 9892, 9894, 9896, 9898, 9901, 9904, 9908, 9910, 9912,
    16810, 16811, 16812, 16813, 16954, 17329, 17401, 17402, 18657, 18658, 19970, 19971, 19972,
    19973, 19974, 20739, 20742, 20747, 20748, 21850, 22827, 22828, 22829, 24248, 24974, 24975,
    24976, 24977, 25297, 25298, 25299, 26978, 26979, 26980, 26981, 26982, 26983, 26984, 26985,
    26986, 26987, 26988, 26989, 26990, 26991, 26992, 26994, 26995, 26996, 26997, 26998, 27000,
    27001, 27002, 27003, 27004, 27005, 27006, 27008, 27009, 27010, 27012, 27013, 31018, 31709,
    33357, 33982, 33983, 33986, 33987, 40120, 42230, 42232, 42233, 44205, 44206, 44207, 44208,
    45282, 45283, 47180, 48377, 48378, 48436, 48437, 48440, 48441, 48442, 48443, 48444, 48445,
    48446, 48447, 48450, 48451, 48459, 48461, 48462, 48463, 48464, 48465, 48466, 48467, 48468,
    48469, 48470, 48477, 48479, 48480, 48559, 48560, 48561, 48562, 48563, 48564, 48565, 48566,
    48567, 48568, 48569, 48570, 48571, 48572, 48573, 48574, 48575, 48576, 48577, 48578, 48579,
    49799, 49800, 49802, 49803, 50171, 50172, 50212, 50213, 50763, 50764, 50765, 50766, 50767,
    50768, 53188, 53189, 53190, 53191, 53194, 53195, 53196, 53197, 53198, 53199, 53200, 53201,
    53223, 53225, 53226, 53227, 53248, 53249, 53251, 53307, 53308, 53312, 53313, 58180, 58181,
    60432, 60433, 61384, 61387, 61388, 61390
);

-- The 16 confirmed-stale spell_bonus_data rows (see comment above) -- not every survivor with a
-- row, only the ones where EffectBonusMultiplier is already correct at both rank 1 and max rank.
DELETE FROM `spell_bonus_data` WHERE `entry` IN (
    339, 774, 2912, 5176, 5185, 5570, 8921, 8936, 19975, 33763, 42231, 44203, 48438, 50288, 50294,
    61391
);
