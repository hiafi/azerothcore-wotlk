-- Single-rank spell system (docs/single-rank-spell-system.md), Hunter pass, work item 3:
-- world-DB migration for the 69 bootstrapped Hunter abilities. The Spell.dbc side (BasePoints,
-- RealPointsPerLevel, coefficients, MaxLevel, ManaCostPct) is handled by apps/dbc-tools/generate.py
-- (see the sibling rev_*.sql it produced). This file handles the tables that pipeline doesn't
-- touch: spell_ranks (the collapsed rank chains no longer exist as chains), trainer_spell (only
-- the surviving rank-1 spell should still be trainer-taught), and spell_bonus_data (stale
-- coefficient overrides confirmed redundant against the now-correct EffectBonusMultiplier).
--
-- Also fixed in this pass (not part of this migration, see SpellAuraEffects.cpp):
-- HandlePeriodicDummyAuraTick's Feeding Frenzy talent-rank dispatcher hardcoded the now-superseded
-- rank 2 (60097); remapped both talent ranks to cast the surviving rank-1 ID (60096).
--
-- Step 3's NPC/item/quest audit on the 339 superseded ranks found:
--   - 3 referenced by item_template (spellid_2 - Aspect of the Hawk ranks via an Idol-type item) -
--     kept in source/spells/hunter.csv, annotated. No quest_template/glyph hits.
--   - 12 referenced only by smart_scripts/creature_template_spell (NPC casters) - moved to
--     source/spells/npc.csv.
--   - The remaining 324 have no reference anywhere - dropped from source entirely.
-- Step 5 found 34 survivors with a spell_bonus_data row. 6 (Claw, Bite, Demoralizing Screech,
-- Lightning Breath, Pin, Acid Spit) have EffectBonusMultiplier populated (nonzero) at both rank 1
-- and the max rank on the relevant effect - safe, redundant, deleted below. The other 28 either
-- have EffectBonusMultiplier == 0 at every rank (spell_bonus_data is the sole source of their
-- direct_bonus/dot_bonus scaling - most of the "Pet Skills"-family abilities) or are pure
-- ap_bonus/ap_dot_bonus rows (the AP-scaling gotcha) confirmed flat across every rank - no write
-- needed for either, same finding as rogue/DK/Druid.

-- Every rank of each of the 69 collapsed chains (69 survivors + 339 superseded ranks) loses its
-- spell_ranks entry. GetRank() defaults to 1 with no chain entry, so this is safe -- matches what
-- a never-ranked spell already looks like.
DELETE FROM `spell_ranks` WHERE `first_spell_id` IN (
    136, 1130, 1495, 1499, 1510, 1513, 1978, 2643, 2649, 2973, 3044, 3355, 3674, 13165, 13795,
    13797, 13812, 13813, 16827, 17253, 19306, 19386, 19434, 19491, 19557, 19603, 20043, 24131,
    24423, 24450, 24604, 24640, 24844, 34472, 34478, 34833, 34889, 35098, 35290, 35387, 42243,
    49966, 50245, 50256, 50271, 50274, 50318, 50433, 50479, 50498, 50518, 50519, 50541, 53301,
    53351, 54644, 54680, 54706, 55749, 56626, 56641, 57386, 58604, 59881, 60096, 61193, 61846,
    64418, 75593
);

-- Only the 339 superseded ranks lose their trainer_spell row; the 69 survivors' rows are
-- unchanged (same SpellId, same ReqLevel as before -- the collapse didn't move learn levels).
DELETE FROM `trainer_spell` WHERE `SpellId` IN (
    3009, 3010, 3111, 3661, 3662, 13542, 13543, 13544, 13549, 13550, 13551, 13552, 13553, 13554,
    13555, 14260, 14261, 14262, 14263, 14264, 14265, 14266, 14269, 14270, 14271, 14281, 14282,
    14283, 14284, 14285, 14286, 14287, 14288, 14289, 14290, 14294, 14295, 14298, 14299, 14300,
    14301, 14302, 14303, 14304, 14305, 14308, 14309, 14310, 14311, 14314, 14315, 14316, 14317,
    14318, 14319, 14320, 14321, 14322, 14323, 14324, 14325, 14326, 14327, 14916, 14917, 14918,
    14919, 14920, 14921, 16828, 16829, 16830, 16831, 16832, 17255, 17256, 17257, 17258, 17259,
    17260, 17261, 19493, 19494, 19558, 19605, 19606, 19607, 19608, 20190, 20900, 20901, 20902,
    20903, 20904, 20909, 20910, 24132, 24133, 24134, 24135, 24452, 24453, 24577, 24578, 24579,
    24583, 24586, 24587, 25008, 25009, 25010, 25011, 25012, 25294, 25295, 25296, 27014, 27016,
    27019, 27021, 27022, 27023, 27024, 27025, 27026, 27044, 27045, 27046, 27047, 27049, 27050,
    27051, 27060, 27065, 27067, 27068, 27069, 34120, 34473, 34474, 34479, 34481, 34834, 34835,
    34836, 34837, 35099, 35291, 35292, 35293, 35294, 35295, 35323, 35389, 35392, 36916, 42234,
    42244, 42245, 48989, 48990, 48995, 48996, 48998, 48999, 49000, 49001, 49009, 49010, 49011,
    49012, 49044, 49045, 49047, 49048, 49049, 49050, 49051, 49052, 49053, 49054, 49055, 49056,
    49064, 49065, 49066, 49067, 49071, 49967, 49968, 49969, 49970, 49971, 49972, 49973, 49974,
    52012, 52013, 52014, 52015, 52016, 52395, 52396, 52397, 52398, 52399, 52471, 52472, 52473,
    52474, 52475, 52476, 53338, 53339, 53526, 53528, 53529, 53532, 53533, 53537, 53538, 53540,
    53542, 53543, 53544, 53545, 53546, 53547, 53548, 53558, 53559, 53560, 53561, 53562, 53564,
    53565, 53566, 53567, 53568, 53571, 53572, 53573, 53574, 53575, 53578, 53579, 53580, 53581,
    53582, 53584, 53586, 53587, 53588, 53589, 53593, 53594, 53596, 53597, 53598, 55482, 55483,
    55484, 55485, 55487, 55488, 55489, 55490, 55491, 55492, 55495, 55496, 55497, 55498, 55499,
    55505, 55506, 55507, 55508, 55509, 55555, 55556, 55557, 55728, 55750, 55751, 55752, 55753,
    55754, 56627, 56628, 56629, 56630, 56631, 57389, 57390, 57391, 57392, 57393, 58431, 58432,
    58433, 58434, 58607, 58608, 58609, 58610, 58611, 59882, 59883, 59884, 59885, 59886, 60051,
    60052, 60053, 60097, 61005, 61006, 61194, 61195, 61196, 61197, 61198, 61676, 61847, 63668,
    63669, 63670, 63671, 63672, 64419, 64420, 64491, 64492, 64493, 64494, 64495, 75446, 75447
);

-- The 6 confirmed-stale spell_bonus_data rows (see comment above) -- not every survivor with a
-- row, only the ones where EffectBonusMultiplier is already correct at both rank 1 and max rank.
DELETE FROM `spell_bonus_data` WHERE `entry` IN (
    16827, 17253, 24423, 24844, 50245, 55749
);
