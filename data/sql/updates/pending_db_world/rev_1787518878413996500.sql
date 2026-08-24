-- Single-rank spell system (docs/single-rank-spell-system.md), Warrior pass, work item 3:
-- world-DB migration for the 23 bootstrapped Warrior abilities -- the last class in this
-- conversion (mage, priest, rogue, Death Knight, Druid, Hunter, Paladin, Shaman, Warlock, Warrior
-- all done). The Spell.dbc side (BasePoints, RealPointsPerLevel, coefficients, MaxLevel,
-- ManaCostPct) is handled by apps/dbc-tools/generate.py (see the sibling rev_*.sql it produced).
-- This file handles the tables that pipeline doesn't touch: spell_ranks (the collapsed rank chains
-- no longer exist as chains) and trainer_spell (only the surviving rank-1 spell should still be
-- trainer-taught).
--
-- No spell_bonus_data deletes this pass: all 3 survivors with a row (Thunder Clap, Revenge,
-- Cleave) are pure ap_bonus (the AP-scaling gotcha, expected for a 100% melee/AP class per step 0)
-- with direct_bonus/dot_bonus == 0, confirmed flat across every rank of each chain -- same finding
-- as rogue/DK.
--
-- Step 3's NPC/item/quest audit on the 116 superseded ranks found:
--   - 3 referenced by item_template (spellid_2) - kept in source/spells/warrior.csv, annotated.
--     No quest_template/glyph hits.
--   - 11 referenced only by smart_scripts/creature_template_spell (NPC casters) - moved to
--     source/spells/npc.csv.
--   - The remaining 102 have no reference anywhere - dropped from source entirely.

-- Every rank of each of the 23 collapsed chains (23 survivors + 116
-- superseded ranks) loses its spell_ranks entry. GetRank() defaults to 1 with no chain entry, so
-- this is safe -- matches what a never-ranked spell already looks like.
DELETE FROM `spell_ranks` WHERE `first_spell_id` IN (
    78, 100, 469, 772, 845, 1160, 1464, 5308, 6343, 6572, 6673, 12294, 12303, 12325, 12327, 12966,
    13491, 19870, 20243, 23922, 29559, 29841, 30213
);

-- Only the superseded ranks lose their trainer_spell row; the survivors' rows are unchanged (same
-- SpellId, same ReqLevel as before -- the collapse didn't move learn levels).
DELETE FROM `trainer_spell` WHERE `SpellId` IN (
    284, 285, 1608, 2048, 5242, 6178, 6190, 6192, 6546, 6547, 6548, 6554, 6555, 6574, 7369, 7379,
    8198, 8204, 8205, 8820, 11549, 11550, 11551, 11554, 11555, 11556, 11564, 11565, 11566, 11567,
    11572, 11573, 11574, 11578, 11580, 11581, 11600, 11601, 11604, 11605, 11608, 11609, 12788,
    12789, 12863, 12864, 12865, 12866, 12886, 12967, 12968, 12969, 12970, 19871, 20569, 20658,
    20660, 20661, 20662, 21551, 21552, 21553, 23923, 23924, 23925, 25202, 25203, 25208, 25231,
    25234, 25236, 25241, 25242, 25248, 25258, 25264, 25269, 25286, 25288, 25289, 29588, 29589,
    29707, 29842, 30016, 30022, 30219, 30223, 30324, 30330, 30356, 30357, 46845, 47436, 47437,
    47439, 47440, 47449, 47450, 47465, 47470, 47471, 47474, 47475, 47485, 47486, 47487, 47488,
    47497, 47498, 47501, 47502, 47519, 47520, 47994, 57823
);
