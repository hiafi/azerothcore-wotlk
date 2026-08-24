-- Single-rank spell system (docs/single-rank-spell-system.md), Warlock pass, work item 3:
-- world-DB migration for the 62 bootstrapped Warlock abilities. The Spell.dbc side (BasePoints,
-- RealPointsPerLevel, coefficients, MaxLevel, ManaCostPct) is handled by apps/dbc-tools/generate.py
-- (see the sibling rev_*.sql it produced). This file handles the tables that pipeline doesn't
-- touch: spell_ranks (the collapsed rank chains no longer exist as chains), trainer_spell (only
-- the surviving rank-1 spell should still be trainer-taught), and spell_bonus_data (stale
-- coefficient overrides confirmed redundant against the now-correct EffectBonusMultiplier).
--
-- Pure caster class (no AP-scaling gotcha, per step 0) - confirmed empty ap_bonus/ap_dot_bonus on
-- every survivor's spell_bonus_data row, so no mixed-row risk like Paladin/Hunter this pass.
--
-- Step 3's NPC/item/quest audit on the 295 superseded ranks found:
--   - 5 referenced by item_template (spellid_2) - kept in source/spells/warlock.csv, annotated.
--     No quest_template/glyph hits.
--   - 23 referenced only by smart_scripts/creature_template_spell (NPC casters) - moved to
--     source/spells/npc.csv.
--   - The rest have no reference anywhere - dropped from source entirely.
--
-- Step 5 found 27 survivors with a spell_bonus_data row:
--   - 24 confirmed redundant (EffectBonusMultiplier nonzero at both rank 1 and max rank on the
--     relevant effect) - deleted below.
--   - Corruption (172) is a new case: EffectBonusMultiplier_1 was nonzero at rank 1 (0.0624) but
--     bootstrap set the survivor's coefficient to the max rank's own value, which is 0 -- so
--     post-collapse the DBC coefficient is 0 and spell_bonus_data.dot_bonus (0.0624) is now the
--     SOLE source. The "nonzero at both ends" check must use the coefficient the survivor will
--     actually ship with (max rank's value), not just rank 1's -- kept, not deleted.
--   - Dark Pact (18220) and Haunt (48181): EffectBonusMultiplier == 0 at every real (populated)
--     effect on both ends - sole source, kept.

-- Every rank of each of the 62 collapsed chains (62 survivors + 295
-- superseded ranks) loses its spell_ranks entry. GetRank() defaults to 1 with no chain entry, so
-- this is safe -- matches what a never-ranked spell already looks like.
DELETE FROM `spell_ranks` WHERE `first_spell_id` IN (
    172, 348, 603, 686, 687, 689, 693, 702, 706, 710, 755, 980, 1098, 1120, 1454, 1490, 1714, 1949,
    2362, 2947, 3110, 3716, 5484, 5676, 5740, 5782, 5857, 6201, 6229, 6307, 6353, 6360, 6366, 6789,
    7812, 7814, 17735, 17767, 17877, 18220, 19244, 19505, 27243, 27285, 28176, 29722, 29893, 30049,
    30108, 30151, 30251, 30283, 33698, 42223, 43991, 47261, 47263, 47897, 48181, 50796, 54049, 54424
);

-- Only the superseded ranks lose their trainer_spell row; the survivors' rows are unchanged (same
-- SpellId, same ReqLevel as before -- the collapse didn't move learn levels).
DELETE FROM `trainer_spell` WHERE `SpellId` IN (
    695, 696, 699, 705, 707, 709, 1014, 1086, 1088, 1094, 1106, 1108, 1455, 1456, 2941, 3698, 3699,
    3700, 5699, 6202, 6205, 6213, 6215, 6217, 6219, 6222, 6223, 7641, 7646, 7648, 7651, 7799, 7800,
    7801, 7802, 7804, 7805, 7809, 7810, 7811, 7813, 7815, 7816, 8288, 8289, 8316, 8317, 11659,
    11660, 11661, 11665, 11667, 11668, 11671, 11672, 11675, 11677, 11678, 11681, 11682, 11683,
    11684, 11687, 11688, 11689, 11693, 11694, 11695, 11699, 11700, 11707, 11708, 11711, 11712,
    11713, 11719, 11721, 11722, 11725, 11726, 11729, 11730, 11733, 11734, 11735, 11739, 11740,
    11762, 11763, 11766, 11767, 11770, 11771, 11774, 11775, 11778, 11779, 11780, 11784, 11785,
    17727, 17728, 17750, 17751, 17752, 17850, 17851, 17852, 17853, 17854, 17919, 17920, 17921,
    17922, 17923, 17924, 17925, 17926, 17928, 17951, 17952, 17953, 18647, 18867, 18868, 18869,
    18870, 18871, 18937, 18938, 19438, 19440, 19441, 19442, 19443, 19647, 19731, 19734, 19736,
    20752, 20755, 20756, 20757, 25307, 25309, 25311, 27209, 27210, 27211, 27212, 27213, 27214,
    27215, 27216, 27217, 27218, 27219, 27220, 27222, 27223, 27224, 27228, 27230, 27238, 27250,
    27259, 27260, 27263, 27265, 27267, 27268, 27269, 27270, 27271, 27272, 27273, 27274, 27275,
    27276, 27277, 28172, 28189, 28610, 30051, 30052, 30194, 30198, 30256, 30404, 30405, 30413,
    30414, 30459, 30545, 30546, 30909, 30910, 32231, 33699, 33700, 33701, 42218, 42224, 42225,
    42226, 47262, 47264, 47265, 47793, 47808, 47809, 47810, 47811, 47812, 47813, 47814, 47815,
    47817, 47818, 47819, 47820, 47822, 47823, 47824, 47825, 47826, 47827, 47831, 47832, 47833,
    47834, 47835, 47836, 47837, 47838, 47841, 47843, 47846, 47847, 47855, 47856, 47857, 47859,
    47860, 47863, 47864, 47865, 47867, 47871, 47878, 47884, 47886, 47888, 47889, 47890, 47891,
    47892, 47893, 47964, 47982, 47983, 47984, 47985, 47986, 47987, 47988, 47989, 47990, 47991,
    47992, 47993, 47996, 48011, 50511, 54050, 54051, 54052, 54053, 57564, 57565, 57566, 57567,
    57946, 58887, 59092, 59161, 59163, 59164, 59170, 59171, 59172, 60219, 60220, 61191, 61290
);

-- The 24 confirmed-stale spell_bonus_data rows (see comment above).
DELETE FROM `spell_bonus_data` WHERE `entry` IN (
    348, 603, 686, 689, 755, 980, 1120, 1949, 3110, 5676, 5857, 6353, 6789, 7814, 17877, 27243,
    27285, 29722, 30108, 30283, 42223, 47897, 50796, 54049
);
