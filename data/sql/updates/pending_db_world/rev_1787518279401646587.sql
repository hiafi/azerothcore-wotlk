-- Single-rank spell system (docs/single-rank-spell-system.md), Shaman pass, work item 3:
-- world-DB migration for the 60 bootstrapped Shaman abilities. The Spell.dbc side (BasePoints,
-- RealPointsPerLevel, coefficients, MaxLevel, ManaCostPct) is handled by apps/dbc-tools/generate.py
-- (see the sibling rev_*.sql it produced). This file handles the tables that pipeline doesn't
-- touch: spell_ranks (the collapsed rank chains no longer exist as chains), trainer_spell (only
-- the surviving rank-1 spell should still be trainer-taught), and spell_bonus_data (stale
-- coefficient overrides confirmed redundant against the now-correct EffectBonusMultiplier).
--
-- Two chains (2075 "Searing Totem", 8073 "Stoneskin Totem") turned out to pair a real player
-- shaman spell (rank 2: 38116/38115, SpellClassSet=11) with a rank-1 entry that's actually
-- SpellClassSet=0 (generic) with BaseLevel=0 -- an internal/engine plumbing spell, not real player
-- content, and never pulled into shaman.csv at all. Left both untouched (single, unscaled, exactly
-- as pulled) rather than guess at a bootstrap using a fake rank 1 -- see the playbook's Gotchas.
--
-- Step 3's NPC/item/quest audit on the 387 superseded ranks found:
--   - 3 referenced by item_template (spellid_2) - kept in source/spells/shaman.csv, annotated.
--   - 95 referenced by smart_scripts/creature_template_spell OR (3 of them: 10405, 10461, 11307)
--     only by a hardcoded C++ hit in boss_nefarian.cpp -- the SPELL_*-constant grep in step 3 only
--     covers src/server/scripts/ by convention, but a same-repo full-text grep for the raw IDs
--     still catches this; moved to source/spells/npc.csv.
--   - The rest have no reference anywhere - dropped from source entirely.
--
-- Step 5 found 17 survivors with a spell_bonus_data row where EffectBonusMultiplier is confirmed
-- correct at both rank 1 and the max rank on the relevant effect (matched by aura type, not just
-- effect index -- Earthliving's dot_bonus maps to effect 1 itself, a periodic-heal aura, not a
-- separate effect 2) - safe, redundant, deleted below. Flametongue Weapon Proc (8026) is left
-- untouched: its only effect is the dummy-trigger embedded-spell-ID pattern (skipped from scaling
-- entirely, so its own EffectBonusMultiplier is 0 at every rank) and its direct_bonus has no other
-- confirmed source, so it's kept as a possible sole source rather than guessed away. No survivor
-- had a nonzero ap_bonus/ap_dot_bonus this pass (no mixed-row risk, unlike Paladin/Hunter).

-- Every rank of each of the 60 collapsed chains (60 survivors + 387
-- superseded ranks) loses its spell_ranks entry. GetRank() defaults to 1 with no chain entry, so
-- this is safe -- matches what a never-ranked spell already looks like.
DELETE FROM `spell_ranks` WHERE `first_spell_id` IN (
    324, 331, 370, 403, 421, 974, 1064, 1535, 2008, 3599, 3606, 5394, 5672, 5675, 5677, 5730, 8004,
    8017, 8024, 8026, 8033, 8034, 8042, 8050, 8056, 8071, 8072, 8075, 8076, 8181, 8182, 8184, 8185,
    8187, 8190, 8227, 8232, 8349, 10400, 10595, 10596, 16177, 16257, 26364, 30165, 30669, 30701,
    30706, 45284, 45297, 51490, 51505, 51730, 51940, 51945, 52109, 52127, 57658, 61295, 64694
);

-- Only the superseded ranks lose their trainer_spell row; the survivors' rows are unchanged (same
-- SpellId, same ReqLevel as before -- the collapse didn't move learn levels).
DELETE FROM `trainer_spell` WHERE `SpellId` IN (
    325, 332, 529, 547, 548, 905, 913, 915, 930, 939, 943, 945, 959, 2860, 6041, 6350, 6351, 6352,
    6363, 6364, 6365, 6371, 6372, 6375, 6377, 6390, 6391, 6392, 8005, 8008, 8010, 8012, 8018, 8019,
    8027, 8028, 8029, 8030, 8037, 8038, 8044, 8045, 8046, 8052, 8053, 8058, 8134, 8154, 8155, 8156,
    8157, 8160, 8161, 8162, 8163, 8235, 8249, 8498, 8499, 8502, 8503, 10391, 10392, 10395, 10396,
    10399, 10403, 10404, 10405, 10406, 10407, 10408, 10412, 10413, 10414, 10427, 10428, 10431,
    10432, 10435, 10436, 10437, 10438, 10441, 10442, 10445, 10447, 10448, 10456, 10458, 10460,
    10461, 10462, 10463, 10466, 10467, 10468, 10472, 10473, 10476, 10477, 10478, 10479, 10486,
    10491, 10493, 10494, 10495, 10496, 10497, 10526, 10534, 10535, 10537, 10538, 10579, 10580,
    10581, 10585, 10586, 10587, 10598, 10599, 10600, 10601, 10605, 10622, 10623, 11306, 11307,
    11314, 11315, 15207, 15208, 15567, 15568, 15569, 16236, 16237, 16277, 16278, 16279, 16280,
    16311, 16312, 16313, 16339, 16341, 16342, 16343, 16344, 16352, 16353, 16355, 16356, 16362,
    16387, 20609, 20610, 20776, 20777, 24398, 25357, 25361, 25362, 25391, 25396, 25420, 25422,
    25423, 25439, 25442, 25448, 25449, 25454, 25457, 25464, 25469, 25472, 25488, 25489, 25500,
    25501, 25505, 25506, 25507, 25508, 25509, 25525, 25527, 25528, 25530, 25533, 25535, 25537,
    25546, 25547, 25550, 25552, 25557, 25559, 25560, 25562, 25563, 25566, 25567, 25569, 25570,
    25573, 25574, 25590, 26363, 26365, 26366, 26367, 26369, 26370, 26371, 26372, 29177, 29178,
    29228, 30670, 30671, 30702, 30703, 30704, 30705, 32593, 32594, 33736, 45286, 45287, 45288,
    45289, 45290, 45291, 45292, 45293, 45294, 45295, 45296, 45298, 45299, 45300, 45301, 45302,
    49230, 49231, 49232, 49233, 49235, 49236, 49237, 49238, 49239, 49240, 49268, 49269, 49270,
    49271, 49272, 49273, 49275, 49276, 49277, 49278, 49279, 49280, 49281, 49283, 49284, 51988,
    51989, 51990, 51991, 51992, 51993, 51994, 51997, 51998, 51999, 52000, 52004, 52005, 52007,
    52008, 52110, 52111, 52112, 52113, 52129, 52131, 52134, 52136, 52138, 55458, 55459, 57621,
    57622, 57660, 57662, 57663, 57720, 57721, 57722, 57960, 58580, 58581, 58582, 58643, 58646,
    58649, 58651, 58652, 58654, 58655, 58656, 58699, 58700, 58701, 58702, 58703, 58704, 58731,
    58732, 58734, 58735, 58737, 58738, 58739, 58740, 58741, 58742, 58744, 58745, 58746, 58748,
    58749, 58750, 58751, 58752, 58753, 58754, 58755, 58756, 58757, 58763, 58764, 58765, 58771,
    58773, 58774, 58775, 58776, 58777, 58784, 58785, 58786, 58787, 58788, 58789, 58790, 58791,
    58792, 58794, 58795, 58796, 58797, 58798, 58799, 58801, 58803, 58804, 59156, 59158, 59159,
    60043, 61299, 61300, 61301, 61649, 61650, 61654, 61657, 65263, 65264
);

-- The 17 confirmed-stale spell_bonus_data rows (see comment above).
DELETE FROM `spell_bonus_data` WHERE `entry` IN (
    331, 403, 421, 974, 1064, 3606, 8004, 8034, 8042, 8050, 8056, 8187, 8349, 26364, 51505, 51945,
    61295
);
