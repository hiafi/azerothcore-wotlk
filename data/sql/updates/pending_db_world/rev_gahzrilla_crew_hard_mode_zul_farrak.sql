-- Zul'Farrak build WP-D7Ha: the crew at the pool (the hard mode "The Crew at the Pool", GZ21), the row dbc-tools
-- cannot declare (.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.5 row D7Ha, s3.7; build spec
-- docs/dungeons/zul-farrak-rework.md "Hydromancer Velratha and Gahz'rilla", Text). The Wellspring 301031, the second
-- head 301032 and the spells 214150-214162 are apps/dbc-tools source/npcs/zul_farrak/gahzrilla_crew_hard_mode.py.
-- Gahz'rilla's group 0 is D7's rev (rev_gahzrilla_zul_farrak.sql), group 1 D7Hb's; Bly's line 5 and Weegli's line 4
-- are CR's rev (rev_crew_zul_farrak.sql).

-- The boss emote (41: center-screen and in the raid warning area) when a crew member falls at the pool in the hard
-- mode: Gahz'rilla eats it and heals 5%. $n is the fallen crew member.
DELETE FROM `creature_text` WHERE `CreatureID` = 7273 AND `GroupID` = 2;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(7273, 2, 0, '%s devours $n!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Gahz''rilla - Devours a fallen crew member (GZ21, hard mode)');
