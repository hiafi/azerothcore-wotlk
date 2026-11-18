-- Blackrock Depths build WP-H: the three normal encounter credits the rework drops (handoff 7.1 #4, recommendation A;
-- rulings 46, 62 and 69: Fineous Darkvire, Ribbly Screwspigot and Plugger Spazzring are no longer encounters). The
-- three DungeonEncounter rows (234, 240, 241) and their heroic copies (1062, 1068, 1069) stay in the client's lockout
-- list; only the server's kill credit goes, so killing them completes nothing and sets no encounter bit. The heroic
-- copies get no instance_encounters row either: apps/dbc-tools source/world/dungeons/blackrock_depths.py
-- `no_credit=(234, 240, 241)` (generate.py never deletes a stock key, so the normal side is this hand DELETE). The
-- three keep role `boss` there (INSTANCE_BIND on their heroic templates) and their slots in the rework instance
-- (doors, save, .dbtest brd).
--
-- Row 233 (Warder Stilgiss and Verek, WP-F-1g, D8 designer question 1): the credit was Stilgiss's kill alone; the
-- spec's encounter is both of them dead. Once both are dead the instance calls UpdateEncounterState with the credit
-- spell 211066 (declared in source/npcs/blackrock_depths/stilgiss_verek.py, never cast) and the row credits on it
-- (creditType 1, ENCOUNTER_CREDIT_CAST_SPELL).
-- The heroic copy (1061) is generated from the replayed normal row, so it names the same spell.
--
-- Sorts after the generated heroic rev (rev_17...): the two touch different rows of `instance_encounters`.
DELETE FROM `instance_encounters` WHERE `entry` IN (234, 240, 241)
    AND `creditType` = 0 AND `creditEntry` IN (9056, 9543, 9499);

UPDATE `instance_encounters` SET `creditType` = 1, `creditEntry` = 211066
    WHERE `entry` = 233 AND `creditType` = 0 AND `creditEntry` = 9041;
