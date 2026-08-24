-- Single-rank spell system (docs/single-rank-spell-system.md), Paladin pass, work item 3:
-- world-DB migration for the 30 bootstrapped Paladin abilities. The Spell.dbc side (BasePoints,
-- RealPointsPerLevel, coefficients, MaxLevel, ManaCostPct) is handled by apps/dbc-tools/generate.py
-- (see the sibling rev_*.sql it produced). This file handles the tables that pipeline doesn't
-- touch: spell_ranks (the collapsed rank chains no longer exist as chains), trainer_spell (only
-- the surviving rank-1 spell should still be trainer-taught), and spell_bonus_data (stale
-- coefficient overrides confirmed redundant against the now-correct EffectBonusMultiplier).
--
-- Step 3's NPC/item/quest audit on the 144 superseded ranks found:
--   - 3 referenced by item_template (spellid_2 - Holy Light ranks via a Libram-type item) - kept
--     in source/spells/paladin.csv, annotated. No quest_template/glyph hits.
--   - 13 referenced only by smart_scripts/creature_template_spell (NPC casters) - moved to
--     source/spells/npc.csv.
--   - The rest have no reference anywhere - dropped from source entirely.
--
-- Step 5 found 11 survivors with a spell_bonus_data row. This pass caught a bug from the
-- immediately-preceding Hunter pass (see rev_1787517751894347328.sql): a row can carry BOTH a
-- redundant direct_bonus/dot_bonus (safe once EffectBonusMultiplier is confirmed correct at rank 1
-- and max rank) AND a real, sole-source ap_bonus/ap_dot_bonus (no Spell.dbc equivalent) at the
-- same time - deleting the whole row would destroy the AP part. Checked every row for this before
-- deciding delete vs. update:
--   - 5 pure direct/dot, confirmed redundant, deleted outright: Holy Light (635), Retribution Aura
--     (7294), Flash of Light (19750), both Holy Shock triggered spells (25912, 25914).
--   - 6 mixed rows (Exorcism 879, Holy Wrath 2812, Holy Shield 20925, Hammer of Wrath 24275,
--     Consecration 26573, Avenger's Shield 31935) - direct_bonus (or dot_bonus for Consecration)
--     zeroed via UPDATE, ap_bonus/ap_dot_bonus left untouched.
-- All of this was already applied directly against the dev DB during the pass; the statements
-- below make the same state reproducible from a clean DB.

-- Every rank of each of the 30 collapsed chains (30 survivors + 144
-- superseded ranks) loses its spell_ranks entry. GetRank() defaults to 1 with no chain entry, so
-- this is safe -- matches what a never-ranked spell already looks like.
DELETE FROM `spell_ranks` WHERE `first_spell_id` IN (
    67, 465, 633, 635, 853, 879, 1022, 2812, 7294, 19740, 19742, 19750, 19876, 19888, 19891, 20194,
    20233, 20249, 20473, 20925, 21183, 24275, 25782, 25894, 25912, 25914, 26573, 31935, 53600, 53655
);

-- Only the superseded ranks lose their trainer_spell row; the survivors' rows are unchanged (same
-- SpellId, same ReqLevel as before -- the collapse didn't move learn levels).
DELETE FROM `trainer_spell` WHERE `SpellId` IN (
    639, 643, 647, 1026, 1032, 1042, 2800, 3472, 5588, 5589, 5599, 5614, 5615, 10278, 10290, 10291,
    10292, 10293, 10298, 10299, 10300, 10301, 10308, 10310, 10312, 10313, 10314, 10318, 10328,
    10329, 19834, 19835, 19836, 19837, 19838, 19850, 19852, 19853, 19854, 19895, 19896, 19897,
    19898, 19899, 19900, 19939, 19940, 19941, 19942, 19943, 20116, 20195, 20236, 20250, 20251,
    20922, 20923, 20924, 20927, 20928, 20929, 20930, 24239, 24274, 25290, 25291, 25292, 25902,
    25903, 25911, 25913, 25916, 25918, 26017, 27135, 27136, 27137, 27138, 27139, 27140, 27141,
    27142, 27143, 27149, 27150, 27151, 27152, 27153, 27154, 27173, 27174, 27175, 27176, 27179,
    27180, 32699, 32700, 33072, 33073, 33074, 48781, 48782, 48784, 48785, 48788, 48800, 48801,
    48805, 48806, 48816, 48817, 48818, 48819, 48820, 48821, 48822, 48823, 48824, 48825, 48826,
    48827, 48931, 48932, 48933, 48934, 48935, 48936, 48937, 48938, 48941, 48942, 48943, 48945,
    48947, 48951, 48952, 53656, 53657, 54043, 54152, 54153, 54498, 54499, 61411
);

-- The 5 confirmed pure-redundant spell_bonus_data rows (see comment above).
DELETE FROM `spell_bonus_data` WHERE `entry` IN (635, 7294, 19750, 25912, 25914);

-- The 6 mixed rows -- zero the now-redundant Spell.dbc-mirroring column, keep the sole-source
-- AP column(s) untouched.
UPDATE `spell_bonus_data` SET `direct_bonus` = 0 WHERE `entry` IN (879, 2812, 20925, 24275, 31935);
UPDATE `spell_bonus_data` SET `dot_bonus` = 0 WHERE `entry` = 26573;
