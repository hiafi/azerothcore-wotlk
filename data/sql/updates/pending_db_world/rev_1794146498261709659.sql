-- Scholomance build WP-S6: Doctor Theolen Krastinov (11261), the rows dbc-tools cannot declare
-- (.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row S6; build spec
-- docs/dungeons/scholomance-rework.md SC 1703-1764). His template (boss_doctor_theolen_krastinov_rework, AIName '',
-- health, DamageModifier 6.0, immunities, flags_extra 3), the Work Bench 300538 (VehicleId 6, its Wrench Free slot),
-- the Failed Patient 300539 and the spells 206225-206241 are apps/dbc-tools source/npcs/scholomance/
-- doctor_theolen_krastinov.py.

-- SmartAI 11261 goes (Backhand 18103, Rend 16509, Frenzy 8269 at 40%, the aggro / kill / death / out-of-combat Talk
-- rows and the stock DATA_MINI_BOSSES SetData(1, 1)): boss_doctor_theolen_krastinov_rework keeps texts 0-3 at the
-- same moments in C++, moves the frenzy emote (4) to the hands graft and the instance counts boss states.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 11261 AND `source_type` = 0;

-- Texts: groups 0-3 (stock) stay as they are. Group 4, the stock frenzy emote, now names the hands graft: a boss emote
-- (41). Groups 5-7 are new mechanic emotes (41): the strap (KR1), the eyes and the heart grafts (KR6).
DELETE FROM `creature_text` WHERE `CreatureID` = 11261 AND `GroupID` IN (4, 5, 6, 7);
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(11261, 4, 0, '%s goes into a frenzy!', 41, 0, 100, 0, 0, 0, 1191, 0, 'Doctor Theolen Krastinov - Grafted hands, Killing Frenzy (KR6)'),
(11261, 5, 0, '%s straps $n to the Work Bench!', 41, 0, 100, 0, 0, 0, 0, 0, 'Doctor Theolen Krastinov - Operation (KR1)'),
(11261, 6, 0, '%s stitches new eyes into his skull!', 41, 0, 100, 0, 0, 0, 0, 0, 'Doctor Theolen Krastinov - Grafted eyes (KR6)'),
(11261, 7, 0, '%s sews a fresh heart into his chest!', 41, 0, 100, 0, 0, 0, 0, 0, 'Doctor Theolen Krastinov - Grafted heart (KR6)');

-- The Work Bench's seat (Vehicle 6, VehicleSeat 441; no stock creature uses either): the seat has no exit of its own,
-- so every eject sets the patient down 2 yd in front of the bench and 2 yd to its left (ExitParamValue 1 = an offset
-- in the vehicle's frame; a point out of sight or under the floor falls back to the bench's own spot).
DELETE FROM `vehicle_seat_addon` WHERE `SeatEntry` = 441;
INSERT INTO `vehicle_seat_addon` (`SeatEntry`, `SeatOrientation`, `ExitParamX`, `ExitParamY`, `ExitParamZ`, `ExitParamO`, `ExitParamValue`) VALUES
(441, 0, 2, 2, 0, 0, 1);
