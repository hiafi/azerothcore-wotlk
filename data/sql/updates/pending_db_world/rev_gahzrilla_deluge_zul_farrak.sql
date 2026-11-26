-- Zul'Farrak build WP-D7Hb: the Deluge, phase 3 of the hard mode "The Crew at the Pool" (GZ22), the row dbc-tools
-- cannot declare (.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.5 row D7Hb, s3.7; build spec
-- docs/dungeons/zul-farrak-rework.md "Hydromancer Velratha and Gahz'rilla", Text). The strike stalker 301033 and the
-- spells 214190-214191 are apps/dbc-tools source/npcs/zul_farrak/gahzrilla_deluge.py. Gahz'rilla's group 0 is D7's
-- rev (rev_gahzrilla_zul_farrak.sql), group 2 D7Ha's.

-- The boss emote (41: center-screen and in the raid warning area) at his 40% in the hard mode.
DELETE FROM `creature_text` WHERE `CreatureID` = 7273 AND `GroupID` = 1;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(7273, 1, 0, '%s sinks into the sacred pool, and the waters rise!', 41, 0, 100, 0, 0, 0, 0, 0,
    'Gahz''rilla - The Deluge (GZ22, hard mode)');
