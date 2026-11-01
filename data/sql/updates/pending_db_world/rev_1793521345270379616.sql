-- Champion Lightrend / Champion Sunstriker (quest 9686 'The Second Trial'): the paladin rework made seals last
-- 10 sec and left Judgement of Light 20271 without a script (a no-op), so recast the seal every 9 sec in combat
-- and use the new Judgement 201060 (its own Holy hit; the seal unleash is player-only).
DELETE FROM `smart_scripts` WHERE `entryorguid` IN (17810, 17812) AND `source_type` = 0;
INSERT INTO `smart_scripts` (`entryorguid`, `source_type`, `id`, `link`, `event_type`, `event_phase_mask`, `event_chance`, `event_flags`, `event_param1`, `event_param2`, `event_param3`, `event_param4`, `event_param5`, `event_param6`, `action_type`, `action_param1`, `action_param2`, `action_param3`, `action_param4`, `action_param5`, `action_param6`, `target_type`, `target_param1`, `target_param2`, `target_param3`, `target_param4`, `target_x`, `target_y`, `target_z`, `target_o`, `comment`) VALUES
(17810, 0, 0, 11, 11, 0, 100, 512, 0, 0, 0, 0, 0, 0, 18, 256, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Champion Lightrend - On Respawn - Set Flag Immune To Players'),
(17810, 0, 1, 0, 38, 0, 100, 512, 1, 1, 0, 0, 0, 0, 80, 1780900, 2, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Champion Lightrend - On Data Set 1 1 - Run Script'),
(17810, 0, 3, 0, 6, 0, 100, 512, 0, 0, 0, 0, 0, 0, 45, 1, 3, 0, 0, 0, 0, 10, 63509, 17807, 0, 0, 0, 0, 0, 0, 'Champion Lightrend - On Just Died - Set Data 1 3'),
(17810, 0, 4, 5, 5, 0, 100, 512, 0, 0, 0, 0, 0, 0, 6, 9686, 0, 0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0, 'Champion Lightrend - On Killed Unit - Fail Quest \'The Second Trial\''),
(17810, 0, 5, 0, 61, 0, 100, 512, 0, 0, 0, 0, 0, 0, 45, 1, 5, 0, 0, 0, 0, 10, 63509, 17807, 0, 0, 0, 0, 0, 0, 'Champion Lightrend - On Killed Unit - Set Data 1 5'),
(17810, 0, 6, 0, 0, 0, 100, 0, 0, 0, 9000, 9000, 0, 0, 11, 20164, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Champion Lightrend - In Combat - Cast \'Seal of Justice\''),
(17810, 0, 7, 0, 0, 0, 100, 0, 0, 6000, 6000, 8000, 0, 0, 11, 201060, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 'Champion Lightrend - In Combat - Cast \'Judgement\''),
(17810, 0, 9, 0, 21, 0, 100, 512, 0, 0, 0, 0, 0, 0, 45, 1, 5, 0, 0, 0, 0, 10, 63509, 17807, 0, 0, 0, 0, 0, 0, 'Champion Lightrend - On Reached Home - Set Data 1 5'),
(17810, 0, 10, 0, 38, 0, 100, 512, 1, 2, 0, 0, 0, 0, 41, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Champion Lightrend - On Data Set 1 2 - Despawn Instant'),
(17810, 0, 11, 0, 61, 0, 100, 512, 0, 0, 0, 0, 0, 0, 53, 1, 17810, 0, 0, 0, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Champion Lightrend - On Killed Unit - Start Waypoint'),
(17810, 0, 12, 0, 40, 0, 100, 512, 5, 0, 0, 0, 0, 0, 90, 8, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Champion Lightrend - On Waypoint 5 Reached - Set Flag Standstate Kneel'),
(17812, 0, 0, 13, 11, 0, 100, 512, 0, 0, 0, 0, 0, 0, 18, 256, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Champion Sunstriker - On Respawn - Set Flag Immune To Players'),
(17812, 0, 1, 0, 38, 0, 100, 512, 1, 1, 0, 0, 0, 0, 80, 1780900, 2, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Champion Sunstriker - On Data Set 1 1 - Run Script'),
(17812, 0, 2, 3, 6, 0, 100, 512, 0, 0, 0, 0, 0, 0, 26, 9686, 0, 0, 0, 0, 0, 16, 0, 0, 0, 0, 0, 0, 0, 0, 'Champion Sunstriker - On Just Died - Quest Credit \'The Second Trial\''),
(17812, 0, 3, 12, 61, 0, 100, 512, 0, 0, 0, 0, 0, 0, 45, 1, 5, 0, 0, 0, 0, 10, 63509, 17807, 0, 0, 0, 0, 0, 0, 'Champion Sunstriker - On Just Died - Set Data 1 5'),
(17812, 0, 4, 5, 5, 0, 100, 512, 0, 0, 0, 0, 0, 0, 6, 9686, 0, 0, 0, 0, 0, 7, 0, 0, 0, 0, 0, 0, 0, 0, 'Champion Sunstriker - On Killed Unit - Fail Quest \'The Second Trial\''),
(17812, 0, 5, 0, 61, 0, 100, 512, 0, 0, 0, 0, 0, 0, 45, 1, 5, 0, 0, 0, 0, 10, 63509, 17807, 0, 0, 0, 0, 0, 0, 'Champion Sunstriker - On Killed Unit - Set Data 1 5'),
(17812, 0, 6, 0, 0, 0, 100, 0, 0, 0, 9000, 9000, 0, 0, 11, 20375, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Champion Sunstriker - In Combat - Cast \'Seal of Command\''),
(17812, 0, 7, 0, 2, 0, 100, 0, 0, 50, 8000, 13000, 0, 0, 11, 19939, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Champion Sunstriker - Between 0-50% Health - Cast \'Flash of Light\''),
(17812, 0, 8, 0, 0, 0, 100, 0, 0, 6000, 6000, 6000, 0, 0, 11, 201060, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 'Champion Sunstriker - In Combat - Cast \'Judgement\''),
(17812, 0, 10, 0, 21, 0, 100, 512, 0, 0, 0, 0, 0, 0, 45, 1, 5, 0, 0, 0, 0, 10, 63509, 17807, 0, 0, 0, 0, 0, 0, 'Champion Sunstriker - On Reached Home - Set Data 1 5'),
(17812, 0, 11, 0, 38, 0, 100, 512, 1, 2, 0, 0, 0, 0, 41, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Champion Sunstriker - On Data Set 1 2 - Despawn Instant'),
(17812, 0, 12, 0, 61, 0, 100, 512, 0, 0, 0, 0, 0, 0, 45, 1, 6, 0, 0, 0, 0, 10, 63509, 17807, 0, 0, 0, 0, 0, 0, 'Champion Sunstriker - On Killed Unit - Set Data 1 6'),
(17812, 0, 13, 0, 61, 0, 100, 512, 0, 0, 0, 0, 0, 0, 53, 1, 17812, 0, 0, 0, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Champion Sunstriker - On Killed Unit - Start Waypoint'),
(17812, 0, 14, 0, 40, 0, 100, 512, 5, 0, 0, 0, 0, 0, 90, 8, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'Champion Sunstriker - On Waypoint 5 Reached - Set Flag Standstate Kneel');
