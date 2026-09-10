-- DB update 2026_09_10_12 -> 2026_09_10_13
-- Arcane Mage rework (docs/arcane-mage-rework-design.md) - playtest bugfix pass (2026-09-09).
-- Fixes 2 of the 3 items in this pass; the 3rd ("Temporal Convergence and Arcane Overload need to
-- be in the Arcane School") was re-investigated and found already correct: spell_dbc rows 200078
-- (Temporal Convergence), 200079/200092/200093 (Arcane Overload's talent shell, damage sub-spell,
-- and follow-up buff) all already carry SchoolMask 64 (Arcane), and 200092's EffectMiscValue_1 is
-- already 6 (Arcane) - see the 2026-09-08 fix in rev_1788921755015417344.sql, which landed
-- correctly. No further data change needed there.
--
-- Root cause of the other 2 (Conjure Food/Water still trainable, 8 named spells not taught):
-- every trainer_spell fix this rework has shipped so far (see rev_1788921755015417344.sql's own
-- "investigated, not reproduced" note) targeted TrainerId 16 under the mistaken belief it was "the
-- one real mage trainer" - it is not. TrainerId 16 has ZERO rows in creature_default_trainer (no
-- NPC in the world actually uses it - orphaned, likely a leftover test/staging copy). The real
-- mage trainers, confirmed via creature_default_trainer joined to every creature_template whose
-- name/subname contains "Mage" (41 NPCs total, e.g. Maginor Dumas, Zaldimar Wefhellt, Khadgar-
-- adjacent trainers, etc.), are TrainerId 212 (36 NPCs, the "full" trainer, levels 1-34 today) and
-- TrainerId 213 (5 NPCs, a starting-zone stub capped at level 6 - same pattern as other classes'
-- starting-zone trainers, not itself a bug). TrainerId 30 is a separate "Portal Trainer" (Archmage
-- Celindra) unrelated to core spell training.
--
-- trainer_spell on 212/213 turns out to be an exact parallel of 16's design-intended content for
-- every level the two trainers currently share (same SpellId set, same ReqLevel per spell,
-- MoneyCost uniformly 5x - verified across all 27 overlapping rows with zero exceptions, e.g.
-- 122/level10 costs 80 on 16 vs 400 on 212, 6117/level34 costs 2600 vs 13000) - a pre-existing,
-- unrelated "real" trainers cost more than the internal reference" convention. This migration
-- extends that same 5x convention to the rows this rework needs added, rather than inventing new
-- pricing.
--
-- Conjure Food (587) and Conjure Water (5504) are the old multi-rank spells this rework retired in
-- favor of the single-rank Conjure Refreshment (42955, already correctly the only one on TrainerId
-- 16) - removed from 212 and 213 outright, and replaced with 42955 on 212 (213 doesn't reach
-- level 10, so nothing to add there - matches its existing low-level-only scope).
--
-- The 8 named spells (Brilliance Aura/Slow/Arcane Blast/Arcane Ward/Time Warp/Presence of
-- Mind/Mass Invisibility/Invisibility) are added to 212 only, at their designed ReqLevel (matching
-- TrainerId 16 exactly) and 5x MoneyCost. None apply to 213 (lowest ReqLevel among them is 10,
-- above 213's existing level-6 ceiling).
DELETE FROM `trainer_spell` WHERE (`TrainerId`, `SpellId`) IN ((212, 587), (212, 5504), (213, 587), (213, 5504), (212, 42955), (212, 30451), (212, 200068), (212, 31589), (212, 12043), (212, 200067), (212, 66), (212, 200070), (212, 200069));
INSERT INTO `trainer_spell` (`TrainerId`, `SpellId`, `MoneyCost`, `ReqSkillLine`, `ReqSkillRank`, `ReqAbility1`, `ReqAbility2`, `ReqAbility3`, `ReqLevel`, `VerifiedBuild`) VALUES
(212, 42955, 150000, 0, 0, 0, 0, 0, 10, 0),
(212, 30451, 2000, 0, 0, 0, 0, 0, 10, 0),
(212, 200068, 10000, 0, 0, 0, 0, 0, 20, 0),
(212, 31589, 20000, 0, 0, 0, 0, 0, 24, 0),
(212, 12043, 75000, 0, 0, 0, 0, 0, 40, 0),
(212, 200067, 175000, 0, 0, 0, 0, 0, 52, 0),
(212, 66, 200000, 0, 0, 0, 0, 0, 58, 0),
(212, 200070, 210000, 0, 0, 0, 0, 0, 60, 0),
(212, 200069, 200000, 0, 0, 0, 0, 0, 66, 0);
