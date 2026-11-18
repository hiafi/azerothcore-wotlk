-- Blackrock Depths build WP-D5: the Ring of Law's six champions (9027-9032), the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D5; build spec
-- docs/dungeons/blackrock-depths-1-detention-block.md S1 "Champion: ..." sections). Their templates (the six
-- boss_*_rework scripts, AIName '', 90k, immunity 1972, INSTANCE_BIND), the Risen beasts 300782-300787, the Risen
-- Champion 300788 and spells 210870-210923 are apps/dbc-tools source/npcs/blackrock_depths/ring_champions.py. The
-- champions have no smart_scripts rows (C++ BossAI in stock); this rev inserts no spawn and no SmartAI row (rule 14).

-- Grizzle's stock "%s goes into a killing frenzy!" stays on each Killing Frenzy stack (S1 "Text"), as a boss emote so
-- it reads on screen (rule 2: boss emotes are type 41; stock 16, a monster emote).
UPDATE `creature_text` SET `Type` = 41 WHERE `CreatureID` = 9028 AND `GroupID` = 0;

-- Hedrum's template aura Hate to Zero 13767 (a 20% chance on hit to wipe the hit target's threat) is removed (S1
-- "Hedrum": a threat wipe breaks bot tanking). Its addon row keeps its other columns.
UPDATE `creature_template_addon` SET `auras` = NULL WHERE `entry` = 9032;
