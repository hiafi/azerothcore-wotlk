-- Scholomance build WP-S3: Marduk Blackpool (10433) and Vectus (10432), the rows dbc-tools cannot declare
-- (.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row S3; build spec
-- docs/dungeons/scholomance-rework.md SC 934-991). Their templates (boss_marduk_blackpool_rework / boss_vectus_rework,
-- AIName '', the shared pool's health, DamageModifier 3.5, immunities), the students 10475 (npc_sc_student, props),
-- the Graduate 300533 and the spells 206150-206166 are apps/dbc-tools source/npcs/scholomance/marduk_and_vectus.py.

-- SmartAI 10433 (Marduk), 10432 (Vectus) and 10475 (the students) is removed (SC "Stock kit", approved). The C++
-- carries what stays: Defiling Aura on the pull, Blast Wave, the idle lecture, the pull of the partner, and Dawn's
-- Gambit (GO 176110's SetData(2, n): Marduk's "We are betrayed!", Vectus's yell, the students' fall and transform).
-- Cleave 15284, Shadow Bolt Volley 17228, Shadow Shield 12040 and Flamestrike 18399 are retired; the students no
-- longer join the fight (SetData(3, 3)): they are props that cast the lessons.
DELETE FROM `smart_scripts` WHERE `entryorguid` IN (10432, 10433, 10475) AND `source_type` = 0;

-- Texts (SC "Text"). Vectus: group 0 is the idle lecture, the seven stock say lines only (the stray type 16 row 0,
-- "%s goes into a killing frenzy!", made Talk(0) emote as idle chatter: DB-REPORT 0.7; it moves to the unused group 6);
-- 1 the stock yell (aggro and Dawn's Gambit); 2-4 the lesson calls; 5 the heroic double period. Marduk: 0 and 1 the
-- stock Dawn's Gambit lines; 2 and 3 the mechanic emotes, type 41 (RAID_BOSS_EMOTE, center screen).
DELETE FROM `creature_text` WHERE `CreatureID` IN (10432, 10433);
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10432, 0, 0, 'Tomorrow we will begin training of our promising dragons, so don''t forget your chew toys.', 12, 0, 100, 0, 0, 0, 7193, 0, 'Vectus - idle lecture'),
(10432, 0, 1, 'When preparing the dragon''s meal, be sure to torture the prisoner in view of the dragon. It responds well to pre-meal entertainment.', 12, 0, 100, 0, 0, 0, 0, 0, 'Vectus - idle lecture'),
(10432, 0, 2, 'The Lich King''s forces are building. It is imperative that our timetable supports his plans.', 12, 0, 100, 0, 0, 0, 0, 0, 'Vectus - idle lecture'),
(10432, 0, 3, 'Our oldest clutch of dragons are still far from maturity, but with patience and study, we are confident the dragonflight will soon be ready.', 12, 0, 100, 0, 0, 0, 7191, 0, 'Vectus - idle lecture'),
(10432, 0, 4, 'Now if you turn to page 34 in your text, you see an illustration of a dwarf undergoing dissection...', 12, 0, 100, 0, 0, 0, 7188, 0, 'Vectus - idle lecture'),
(10432, 0, 5, 'From yesterday''s field trip, Marduk showed us that the dragons will tolerate the meat of recently killed humanoids, but only if they died slowly and painfully.', 12, 0, 100, 0, 0, 0, 7192, 0, 'Vectus - idle lecture'),
(10432, 0, 6, 'We await a batch of black dragon eggs from the Burning Steppes. We believe that, through their study, we will advance our knowledge dramatically.', 12, 0, 100, 0, 0, 0, 0, 0, 'Vectus - idle lecture'),
(10432, 1, 0, 'What is this?! How dare you!', 14, 0, 100, 0, 0, 0, 0, 3, 'Vectus - aggro, Dawn''s Gambit'),
(10432, 2, 0, 'Lesson one: Flamestrike! Mind your aim, class!', 14, 0, 100, 0, 0, 0, 0, 0, 'Vectus - Flamestrike Drill (MV1)'),
(10432, 3, 0, 'Group exercise! Everyone, on that one!', 14, 0, 100, 0, 0, 0, 0, 0, 'Vectus - Group Exercise (MV2)'),
(10432, 4, 0, 'Pop quiz! You there, show them!', 14, 0, 100, 0, 0, 0, 0, 0, 'Vectus - Pop Quiz (MV3)'),
(10432, 5, 0, 'Double period! Keep up, class!', 14, 0, 100, 0, 0, 0, 0, 0, 'Vectus - double period (heroic)'),
(10432, 6, 0, '%s goes into a killing frenzy!', 16, 0, 100, 0, 0, 0, 24143, 0, 'Vectus - stock frenzy emote (unused, was the stray idle row)'),
(10433, 0, 0, 'We are betrayed!', 12, 0, 100, 0, 0, 0, 6234, 0, 'Marduk Blackpool - Dawn''s Gambit'),
(10433, 1, 0, 'We are betrayed!', 12, 0, 100, 0, 0, 0, 6234, 3, 'Marduk Blackpool - Dawn''s Gambit'),
(10433, 2, 0, '%s raises his runeblade!', 41, 0, 100, 0, 0, 0, 0, 0, 'Marduk Blackpool - Ebon Sweep (MV4)'),
(10433, 3, 0, '%s begins to whirl his runeblade!', 41, 0, 100, 0, 0, 0, 0, 0, 'Marduk Blackpool - Whirlwind (MV6, heroic)');

-- The Graduate 300533 holds the student's black book (the stock students' creature_equip_template 10475: item 12862).
DELETE FROM `creature_equip_template` WHERE `CreatureID` = 300533;
INSERT INTO `creature_equip_template` (`CreatureID`, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, `VerifiedBuild`) VALUES
(300533, 1, 12862, 0, 0, 0);
