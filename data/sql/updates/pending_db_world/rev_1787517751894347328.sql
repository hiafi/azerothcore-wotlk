-- Corrective fix for a bug in the Hunter pass's step 5 (spell_bonus_data cleanup, see
-- rev_1787517331291286907.sql). That migration deleted 6 "stale" spell_bonus_data rows because
-- their direct_bonus was confirmed redundant against a correct, nonzero EffectBonusMultiplier at
-- both rank 1 and the max rank -- but the staleness check only looked at direct_bonus/dot_bonus,
-- not at whether the SAME row also carried a real, sole-source ap_bonus/ap_dot_bonus value (no
-- Spell.dbc equivalent exists for those -- see the playbook's AP-scaling gotcha). 3 of the 6
-- deleted rows (Claw, Bite, Demoralizing Screech -- all "Pet Skills" family) had exactly that:
-- direct_bonus 0.119658 (genuinely redundant, safe to drop) alongside ap_bonus 0.07 (NOT
-- redundant, no other source of that scaling). Deleting the whole row silently zeroed pet AP
-- scaling on these three abilities. Restoring the row with direct_bonus zeroed but ap_bonus
-- intact -- an UPDATE-in-place would work too, but INSERT after the prior DELETE keeps this file
-- self-contained and correct even if replayed against a DB that still has the stale row deleted.
-- The other 3 of the original 6 (Lightning Breath, Pin, Acid Spit) had ap_bonus/ap_dot_bonus == 0
-- already, so deleting those rows outright was correct and is not touched here.
INSERT INTO `spell_bonus_data` (`entry`, `direct_bonus`, `dot_bonus`, `ap_bonus`, `ap_dot_bonus`, `comments`) VALUES
(16827, 0, 0, 0.07, 0, 'Pet Skills - Claw'),
(17253, 0, 0, 0.07, 0, 'Pet Skills - Bite'),
(24423, 0, 0, 0.07, 0, 'Pet Skills - Demoralizing Screech');
