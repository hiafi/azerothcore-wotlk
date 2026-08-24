-- Single-rank spell system (docs/single-rank-spell-system.md), mage pilot, work item 3:
-- world-DB migration for the 46 bootstrapped mage abilities. The Spell.dbc side (BasePoints,
-- RealPointsPerLevel, coefficients, MaxLevel, ManaCostPct) is handled by apps/dbc-tools/generate.py
-- (see the sibling rev_*.sql it produced). This file handles the two tables that pipeline doesn't
-- touch: spell_ranks (the collapsed rank chains no longer exist as chains) and trainer_spell
-- (only the surviving rank-1 spell should still be trainer-taught).

-- Every rank of each of the 46 collapsed chains (46 survivors + 257 superseded ranks) loses its
-- spell_ranks entry. GetRank() defaults to 1 with no chain entry, so this is safe -- matches what a
-- never-ranked spell already looks like.
DELETE FROM `spell_ranks` WHERE `first_spell_id` IN (
    10, 116, 118, 120, 122, 133, 168, 491, 543, 587, 604, 700, 759, 1008, 1449, 1459, 1463, 2120, 2136,
    2948, 5143, 5405, 5504, 6117, 6143, 7268, 7302, 11113, 11366, 11426, 12484, 18469, 23028, 30451,
    30455, 30482, 31661, 34913, 42208, 42955, 43987, 44425, 44440, 44457, 44461, 44614
);

-- Only the 257 superseded ranks lose their trainer_spell row; the 46 survivors' rows are
-- unchanged (same SpellId, same ReqLevel as before -- the collapse didn't move learn levels).
DELETE FROM `trainer_spell` WHERE `SpellId` IN (
    143, 145, 205, 597, 837, 857, 865, 990, 1090, 1460, 1461, 2121, 2137, 2138, 3140, 3552, 5144, 5145,
    5505, 5506, 6127, 6129, 6131, 6141, 7269, 7270, 7300, 7301, 7320, 7322, 8400, 8401, 8402, 8406,
    8407, 8408, 8412, 8413, 8416, 8417, 8418, 8419, 8422, 8423, 8427, 8437, 8438, 8439, 8444, 8445,
    8446, 8450, 8451, 8455, 8457, 8458, 8461, 8462, 8492, 8494, 8495, 10052, 10053, 10054, 10057, 10058,
    10138, 10139, 10140, 10144, 10145, 10148, 10149, 10150, 10151, 10156, 10157, 10159, 10160, 10161,
    10165, 10166, 10169, 10170, 10173, 10174, 10177, 10179, 10180, 10181, 10185, 10186, 10187, 10191,
    10192, 10193, 10197, 10199, 10201, 10202, 10205, 10206, 10207, 10211, 10212, 10215, 10216, 10219,
    10220, 10223, 10225, 10230, 10273, 10274, 12485, 12486, 12505, 12522, 12523, 12524, 12525, 12526,
    12824, 12825, 12826, 13018, 13019, 13020, 13021, 13031, 13032, 13033, 18809, 22782, 22783, 25304,
    25306, 25345, 25346, 27070, 27071, 27072, 27073, 27074, 27075, 27076, 27078, 27079, 27080, 27082,
    27085, 27086, 27087, 27088, 27090, 27101, 27103, 27124, 27125, 27126, 27127, 27128, 27130, 27131,
    27132, 27133, 27134, 28609, 28612, 32796, 33041, 33042, 33043, 33405, 33717, 33933, 33938, 33944,
    33946, 37420, 38692, 38697, 38699, 38700, 38703, 38704, 42198, 42209, 42210, 42211, 42212, 42213,
    42832, 42833, 42841, 42842, 42843, 42844, 42845, 42846, 42858, 42859, 42872, 42873, 42890, 42891,
    42894, 42896, 42897, 42913, 42914, 42917, 42920, 42921, 42925, 42926, 42930, 42931, 42937, 42938,
    42939, 42940, 42944, 42945, 42949, 42950, 42956, 42985, 42987, 42988, 42995, 43002, 43008, 43010,
    43012, 43015, 43017, 43019, 43020, 43023, 43024, 43038, 43039, 43043, 43044, 43045, 43046, 44441,
    44780, 44781, 47610, 55021, 55359, 55360, 55361, 55362, 58659
);

-- 19 of the 46 survivors already had a spell_bonus_data override, and it's stale: it holds the
-- OLD rank-1 coefficient (e.g. Frostbolt's direct_bonus was 0.172, the pre-bootstrap rank-1 value),
-- which Unit::SpellBaseDamageBonusDone (Unit.cpp:8895-8897) prefers over Spell.dbc's
-- EffectBonusMultiplier whenever a row exists here -- silently overriding the corrected coefficient
-- the DBC-side migration just wrote. None of the 19 carry a nonzero ap_bonus/ap_dot_bonus (checked),
-- so deleting is lossless: it just lets EffectBonusMultiplier (already correct) take over, same as
-- the other 27 survivors that never had an override row.
DELETE FROM `spell_bonus_data` WHERE `entry` IN (
    116, 120, 122, 133, 1449, 2120, 2136, 2948, 7268, 11113, 11366, 30451, 30455, 31661, 42208, 44425,
    44457, 44461, 44614
);
