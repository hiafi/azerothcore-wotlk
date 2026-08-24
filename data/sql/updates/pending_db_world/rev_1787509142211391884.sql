-- Single-rank spell system (docs/single-rank-spell-system.md), priest pass, work item 3:
-- world-DB migration for the 49 bootstrapped priest abilities. The Spell.dbc side (BasePoints,
-- RealPointsPerLevel, coefficients, MaxLevel, ManaCostPct) is handled by apps/dbc-tools/generate.py
-- (see the sibling rev_*.sql it produced). This file handles the tables that pipeline doesn't
-- touch: spell_ranks (the collapsed rank chains no longer exist as chains), trainer_spell (only
-- the surviving rank-1 spell should still be trainer-taught), and spell_bonus_data (stale
-- pre-bootstrap coefficient overrides that would otherwise silently shadow the corrected
-- EffectBonusMultiplier the DBC-side migration just wrote).

-- Every rank of each of the 49 collapsed chains (49 survivors + 239 superseded ranks) loses its
-- spell_ranks entry. GetRank() defaults to 1 with no chain entry, so this is safe -- matches what a
-- never-ranked spell already looks like.
DELETE FROM `spell_ranks` WHERE `first_spell_id` IN (
    17, 139, 527, 585, 588, 589, 596, 724, 976, 1243, 2006, 2050, 2054, 2060, 2061, 2096, 2944,
    7001, 8092, 8122, 9484, 14743, 14752, 14893, 14914, 15237, 15407, 19236, 21562, 23455, 27681,
    27683, 27813, 32379, 32546, 33076, 33196, 34861, 34914, 41635, 45237, 47540, 47666, 47750,
    47757, 47758, 48045, 49694, 49821
);

-- Only the 239 superseded ranks lose their trainer_spell row; the 49 survivors' rows are
-- unchanged (same SpellId, same ReqLevel as before -- the collapse didn't move learn levels).
DELETE FROM `trainer_spell` WHERE `SpellId` IN (
    591, 592, 594, 598, 600, 602, 970, 984, 988, 992, 996, 1004, 1006, 1244, 1245, 2010, 2052,
    2053, 2055, 2767, 2791, 3747, 6060, 6063, 6064, 6065, 6066, 6074, 6075, 6076, 6077, 6078, 7128,
    8102, 8103, 8104, 8105, 8106, 8124, 9472, 9473, 9474, 9485, 10880, 10881, 10888, 10890, 10892,
    10893, 10894, 10898, 10899, 10900, 10901, 10909, 10915, 10916, 10917, 10927, 10928, 10929,
    10933, 10934, 10937, 10938, 10945, 10946, 10947, 10951, 10952, 10955, 10957, 10958, 10960,
    10961, 10963, 10964, 10965, 14818, 14819, 15261, 15262, 15263, 15264, 15265, 15266, 15267,
    15357, 15359, 15430, 15431, 17311, 17312, 17313, 17314, 18807, 19238, 19240, 19241, 19242,
    19243, 19276, 19277, 19278, 19279, 19280, 20770, 21564, 23458, 23459, 25210, 25213, 25217,
    25218, 25221, 25222, 25233, 25235, 25308, 25312, 25314, 25315, 25316, 25329, 25331, 25363,
    25364, 25367, 25368, 25372, 25375, 25384, 25387, 25389, 25392, 25431, 25433, 25435, 25437,
    25467, 27799, 27800, 27801, 27803, 27804, 27805, 27817, 27818, 27828, 27841, 27870, 27871,
    27873, 27874, 28275, 28276, 32996, 32999, 33197, 33198, 34863, 34864, 34865, 34866, 34916,
    34917, 39374, 45241, 45242, 48040, 48062, 48063, 48065, 48066, 48067, 48068, 48070, 48071,
    48072, 48073, 48074, 48075, 48076, 48077, 48078, 48084, 48085, 48086, 48087, 48088, 48089,
    48110, 48111, 48112, 48113, 48119, 48120, 48122, 48123, 48124, 48125, 48126, 48127, 48134,
    48135, 48155, 48156, 48157, 48158, 48159, 48160, 48161, 48162, 48168, 48169, 48170, 48171,
    48172, 48173, 48299, 48300, 52983, 52984, 52985, 52986, 52987, 52988, 52998, 52999, 53000,
    53001, 53002, 53003, 53005, 53006, 53007, 53022, 53023, 59000
);

-- 23 of the 49 survivors already had a spell_bonus_data override; only 20 of those are stale
-- (hold an old rank-era direct_bonus/dot_bonus -- e.g. Renew's was 0.207, the pre-bootstrap
-- rank-1 value, vs. the corrected 0.376 -- or are simply redundant with a coefficient the DBC-side
-- migration already set correctly). The other 3 (589 Shadow Word: Pain, 7001 Lightwell Renew,
-- 34433 Shadowfiend) are NOT included here: their EffectBonusMultiplier is 0 in Spell.dbc across
-- every rank, meaning spell_bonus_data is the *sole* source of their scaling, not a stale mirror
-- of it -- deleting those would silently zero out real, live spellpower scaling. All 20 below have
-- an ap_bonus/ap_dot_bonus of 0 (checked), so deleting is lossless: it just lets
-- EffectBonusMultiplier (already correct) take over, same as the other 26 survivors that never
-- had an override row.
DELETE FROM `spell_bonus_data` WHERE `entry` IN (
    139, 585, 596, 2050, 2054, 2060, 2061, 2944, 8092, 14914, 15237, 19236, 23455, 32379, 32546,
    34861, 34914, 47666, 47750, 49821
);
