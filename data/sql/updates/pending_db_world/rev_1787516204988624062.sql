-- Single-rank spell system (docs/single-rank-spell-system.md), Death Knight pass, work item 3:
-- world-DB migration for the 30 bootstrapped Death Knight abilities. The Spell.dbc side
-- (BasePoints, RealPointsPerLevel, coefficients, MaxLevel, ManaCostPct) is handled by
-- apps/dbc-tools/generate.py (see the sibling rev_*.sql it produced). This file handles the
-- tables that pipeline doesn't touch: spell_ranks (the collapsed rank chains no longer exist as
-- chains) and trainer_spell (only the surviving rank-1 spell should still be trainer-taught).
--
-- No spell_bonus_data deletes this pass: step 5's check found only three survivors with a row
-- (Icy Touch, Blood Boil, Howling Blast), all ap_bonus-only (0 direct_bonus/dot_bonus), already
-- flat across every rank of their chain, and already keyed to the surviving rank-1 ID -- nothing
-- stale to remove (same finding as rogue's AP-scaling check).
--
-- Also fixed in this pass (not part of this migration): src/server/game/Spells/Auras/
-- SpellAuras.cpp's disease-spread proc handler hardcoded the superseded ranks 51734/51735
-- (Ebon Plague) and 50509/50510 (Crypt Fever) by talent rank; remapped to always cast the
-- surviving rank-1 ID (51726/50508), since the debuff now scales by caster level instead of by
-- which talent rank was known.

-- Every rank of each of the 30 collapsed chains (30 survivors + 101 superseded ranks) loses its
-- spell_ranks entry. GetRank() defaults to 1 with no chain entry, so this is safe -- matches what
-- a never-ranked spell already looks like.
DELETE FROM `spell_ranks` WHERE `first_spell_id` IN (
    43265, 45462, 45477, 45902, 47541, 48721, 49020, 49038, 49143, 49158, 49184, 49601, 49998,
    50096, 50508, 51726, 51789, 51969, 51983, 52284, 55050, 55090, 57330, 59133, 61274, 62900,
    66188, 66196, 66198, 66215
);

-- Only the 101 superseded ranks lose their trainer_spell row; the 30 survivors' rows are
-- unchanged (same SpellId, same ReqLevel as before -- the collapse didn't move learn levels).
-- Applies regardless of which step-7 bucket a superseded ID landed in -- step 3's NPC audit and
-- the item/quest/glyph checks all came back clean for every one of these 101 IDs (no reference
-- anywhere), so all were dropped from source/spells/deathknight.csv entirely, not moved to
-- npc.csv.
DELETE FROM `trainer_spell` WHERE `SpellId` IN (
    45463, 49595, 49596, 49602, 49892, 49893, 49894, 49895, 49896, 49903, 49904, 49909, 49917,
    49918, 49919, 49920, 49921, 49923, 49924, 49926, 49927, 49928, 49929, 49930, 49936, 49937,
    49938, 49939, 49940, 49941, 49999, 50108, 50109, 50110, 50111, 50509, 50510, 51325, 51326,
    51327, 51328, 51409, 51410, 51411, 51416, 51417, 51418, 51419, 51423, 51424, 51425, 51734,
    51735, 51970, 51986, 52285, 52286, 55258, 55259, 55260, 55261, 55262, 55265, 55268, 55270,
    55271, 57623, 61275, 61276, 61277, 61278, 62901, 62902, 62903, 62904, 64855, 64856, 64858,
    64859, 66950, 66951, 66952, 66953, 66958, 66959, 66960, 66961, 66962, 66972, 66973, 66974,
    66975, 66976, 66977, 66978, 66979, 66988, 66989, 66990, 66991, 66992
);
