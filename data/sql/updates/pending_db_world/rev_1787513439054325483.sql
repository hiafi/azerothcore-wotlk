-- Single-rank spell system (docs/single-rank-spell-system.md), rogue pass, work item 3:
-- world-DB migration for the 30 bootstrapped rogue abilities. The Spell.dbc side (BasePoints,
-- RealPointsPerLevel, coefficients, MaxLevel, ManaCostPct) is handled by apps/dbc-tools/generate.py
-- (see the sibling rev_*.sql it produced). This file handles the tables that pipeline doesn't
-- touch: spell_ranks (the collapsed rank chains no longer exist as chains) and trainer_spell (only
-- the surviving rank-1 spell should still be trainer-taught).
--
-- No spell_bonus_data deletes this pass: step 5's check found every existing ap_bonus/ap_dot_bonus
-- row (Garrote, Gouge, Instant/Wound/Deadly Poison) already correct, already flat across every rank,
-- and already keyed to the surviving rank-1 ID -- nothing stale to remove.

-- Every rank of each of the 30 collapsed chains (30 survivors + 150 superseded ranks) loses its
-- spell_ranks entry. GetRank() defaults to 1 with no chain entry, so this is safe -- matches what a
-- never-ranked spell already looks like.
DELETE FROM `spell_ranks` WHERE `first_spell_id` IN (
    53, 408, 703, 1329, 1752, 1856, 1943, 1966, 2098, 2818, 2823, 2983, 5171, 5277, 5374, 6770,
    8676, 8679, 8680, 11327, 13218, 13219, 14143, 16511, 26679, 26688, 26785, 27576, 32645, 51630
);

-- Only the 150 superseded ranks lose their trainer_spell row; the 30 survivors' rows are
-- unchanged (same SpellId, same ReqLevel as before -- the collapse didn't move learn levels).
-- Applies regardless of which step-7 bucket a superseded ID landed in (dropped from source /
-- moved to npc.csv / kept in rogue.csv as item-referenced) -- none of those are trainer-taught
-- any more even if still reachable through an item or NPC.
DELETE FROM `trainer_spell` WHERE `SpellId` IN (
    1757, 1758, 1759, 1760, 1857, 2070, 2589, 2590, 2591, 2819, 2824, 6760, 6761, 6762, 6768, 6774,
    8621, 8623, 8624, 8631, 8632, 8633, 8637, 8639, 8640, 8643, 8685, 8686, 8688, 8689, 8696, 8721,
    8724, 8725, 11267, 11268, 11269, 11273, 11274, 11275, 11279, 11280, 11281, 11289, 11290, 11293,
    11294, 11297, 11299, 11300, 11303, 11305, 11329, 11335, 11336, 11337, 11338, 11339, 11340,
    11353, 11354, 11355, 11356, 13222, 13223, 13224, 13225, 13226, 13227, 14149, 17347, 17348,
    25300, 25302, 25349, 25351, 26669, 26839, 26861, 26862, 26863, 26864, 26865, 26867, 26884,
    26888, 26889, 26890, 26891, 26967, 26968, 27186, 27187, 27188, 27189, 27441, 27448, 31016,
    32684, 34411, 34412, 34413, 34414, 34415, 34416, 34417, 34418, 34419, 48637, 48638, 48656,
    48657, 48658, 48659, 48660, 48661, 48662, 48663, 48664, 48665, 48666, 48667, 48668, 48671,
    48672, 48673, 48674, 48675, 48676, 48689, 48690, 48691, 51631, 51724, 57964, 57965, 57967,
    57968, 57969, 57970, 57972, 57973, 57974, 57975, 57977, 57978, 57981, 57982, 57992, 57993
);
