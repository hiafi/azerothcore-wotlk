-- Death Knight rework DK0a (PLAN 1C.2, shared doc "Starting a Death Knight",
-- docs/reworks/death-knight-shared-rework.md): the Ebon Hold chain is replaced by the new start
-- (Heroic start at the class trainer), so every Death Knight only quest (quest_template_addon.AllowableClasses = 32)
-- is disabled. 12626 (Company of the Damned) is already disabled and keeps its row.
-- Hand written: no dbc-tools table owns these sourceType 1 rows.
--
-- P0 spike removal: creature 300339 no longer runs a script.
UPDATE `creature_template` SET `ScriptName` = '' WHERE `entry` = 300339;

DELETE FROM `disables` WHERE `sourceType` = 1 AND `entry` IN (12593, 12619, 12625, 12636, 12641, 12657, 12670, 12678);
INSERT INTO `disables` (`sourceType`, `entry`, `flags`, `params_0`, `params_1`, `comment`) VALUES
(1, 12593, 0, '', '', 'In Service Of The Lich King'),
(1, 12619, 0, '', '', 'The Emblazoned Runeblade'),
(1, 12625, 0, '', '', 'Dominion Over Acherus'),
(1, 12636, 0, '', '', 'The Eye Of Acherus'),
(1, 12641, 0, '', '', 'Death Comes From On High'),
(1, 12657, 0, '', '', 'The Might Of The Scourge'),
(1, 12670, 0, '', '', 'The Scarlet Harvest'),
(1, 12678, 0, '', '', 'If Chaos Drives, Let Suffering Hold The Reins');

DELETE FROM `disables` WHERE `sourceType` = 1 AND `entry` IN (12679, 12680, 12687, 12697, 12698, 12700, 12701, 12706);
INSERT INTO `disables` (`sourceType`, `entry`, `flags`, `params_0`, `params_1`, `comment`) VALUES
(1, 12679, 0, '', '', 'Tonight We Dine In Havenshire'),
(1, 12680, 0, '', '', 'Grand Theft Palomino'),
(1, 12687, 0, '', '', 'Into the Realm of Shadows'),
(1, 12697, 0, '', '', 'Gothik the Harvester'),
(1, 12698, 0, '', '', 'The Gift That Keeps On Giving'),
(1, 12700, 0, '', '', 'An Attack Of Opportunity'),
(1, 12701, 0, '', '', 'Massacre At Light\'s Point'),
(1, 12706, 0, '', '', 'Victory At Death\'s Breach!');

DELETE FROM `disables` WHERE `sourceType` = 1 AND `entry` IN (12711, 12714, 12715, 12716, 12717, 12718, 12719, 12720);
INSERT INTO `disables` (`sourceType`, `entry`, `flags`, `params_0`, `params_1`, `comment`) VALUES
(1, 12711, 0, '', '', 'Abandoned Mail'),
(1, 12714, 0, '', '', 'The Will Of The Lich King'),
(1, 12715, 0, '', '', 'The Crypt of Remembrance'),
(1, 12716, 0, '', '', 'The Plaguebringer\'s Request'),
(1, 12717, 0, '', '', 'Noth\'s Special Brew'),
(1, 12718, 0, '', '', 'More Skulls For Brew'),
(1, 12719, 0, '', '', 'Nowhere To Run And Nowhere To Hide'),
(1, 12720, 0, '', '', 'How To Win Friends And Influence Enemies');

DELETE FROM `disables` WHERE `sourceType` = 1 AND `entry` IN (12722, 12723, 12724, 12725, 12727, 12733, 12738, 12739);
INSERT INTO `disables` (`sourceType`, `entry`, `flags`, `params_0`, `params_1`, `comment`) VALUES
(1, 12722, 0, '', '', 'Lambs To The Slaughter'),
(1, 12723, 0, '', '', 'Behind Scarlet Lines'),
(1, 12724, 0, '', '', 'The Path Of The Righteous Crusader'),
(1, 12725, 0, '', '', 'Brothers In Death'),
(1, 12727, 0, '', '', 'Bloody Breakout'),
(1, 12733, 0, '', '', 'Death\'s Challenge'),
(1, 12738, 0, '', '', 'A Cry For Vengeance!'),
(1, 12739, 0, '', '', 'A Special Surprise');

DELETE FROM `disables` WHERE `sourceType` = 1 AND `entry` IN (12742, 12743, 12744, 12745, 12746, 12747, 12748, 12749);
INSERT INTO `disables` (`sourceType`, `entry`, `flags`, `params_0`, `params_1`, `comment`) VALUES
(1, 12742, 0, '', '', 'A Special Surprise'),
(1, 12743, 0, '', '', 'A Special Surprise'),
(1, 12744, 0, '', '', 'A Special Surprise'),
(1, 12745, 0, '', '', 'A Special Surprise'),
(1, 12746, 0, '', '', 'A Special Surprise'),
(1, 12747, 0, '', '', 'A Special Surprise'),
(1, 12748, 0, '', '', 'A Special Surprise'),
(1, 12749, 0, '', '', 'A Special Surprise');

DELETE FROM `disables` WHERE `sourceType` = 1 AND `entry` IN (12750, 12751, 12754, 12755, 12756, 12757, 12778, 12779);
INSERT INTO `disables` (`sourceType`, `entry`, `flags`, `params_0`, `params_1`, `comment`) VALUES
(1, 12750, 0, '', '', 'A Special Surprise'),
(1, 12751, 0, '', '', 'A Sort Of Homecoming'),
(1, 12754, 0, '', '', 'Ambush At The Overlook'),
(1, 12755, 0, '', '', 'A Meeting With Fate'),
(1, 12756, 0, '', '', 'The Scarlet Onslaught Emerges'),
(1, 12757, 0, '', '', 'Scarlet Armies Approach...'),
(1, 12778, 0, '', '', 'The Scarlet Apocalypse'),
(1, 12779, 0, '', '', 'An End To All Things...');

DELETE FROM `disables` WHERE `sourceType` = 1 AND `entry` IN (12800, 12801, 12842, 12848, 12849, 12850, 13105, 13165);
INSERT INTO `disables` (`sourceType`, `entry`, `flags`, `params_0`, `params_1`, `comment`) VALUES
(1, 12800, 0, '', '', 'The Lich King\'s Command'),
(1, 12801, 0, '', '', 'The Light of Dawn'),
(1, 12842, 0, '', '', 'Runeforging: Preparation For Battle'),
(1, 12848, 0, '', '', 'The Endless Hunger'),
(1, 12849, 0, '', '', 'The Power Of Blood, Frost And Unholy'),
(1, 12850, 0, '', '', 'Report To Scourge Commander Thalanor'),
(1, 13105, 0, '', '', 'Once More Unto The Breach, Hero'),
(1, 13165, 0, '', '', 'Taking Back Acherus');

DELETE FROM `disables` WHERE `sourceType` = 1 AND `entry` IN (13166, 13188, 13189, 13410, 13411, 13788, 13791, 13793);
INSERT INTO `disables` (`sourceType`, `entry`, `flags`, `params_0`, `params_1`, `comment`) VALUES
(1, 13166, 0, '', '', 'The Battle For The Ebon Hold'),
(1, 13188, 0, '', '', 'Where Kings Walk'),
(1, 13189, 0, '', '', 'Warchief\'s Blessing'),
(1, 13410, 0, '', '', 'Hellfire Fortifications'),
(1, 13411, 0, '', '', 'Hellfire Fortifications'),
(1, 13788, 0, '', '', 'Threat From Above'),
(1, 13791, 0, '', '', 'Taking Battle To The Enemy'),
(1, 13793, 0, '', '', 'Among the Champions');

DELETE FROM `disables` WHERE `sourceType` = 1 AND `entry` IN (13795, 13812, 13813, 13814, 13863, 13864);
INSERT INTO `disables` (`sourceType`, `entry`, `flags`, `params_0`, `params_1`, `comment`) VALUES
(1, 13795, 0, '', '', 'The Scourgebane'),
(1, 13812, 0, '', '', 'Threat From Above'),
(1, 13813, 0, '', '', 'Taking Battle To The Enemy'),
(1, 13814, 0, '', '', 'Among the Champions'),
(1, 13863, 0, '', '', 'Battle Before The Citadel'),
(1, 13864, 0, '', '', 'Battle Before The Citadel');
