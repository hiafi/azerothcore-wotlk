-- Scholomance build WP-S4: Ras Frostwhisper (10508), the rows dbc-tools cannot declare
-- (.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row S4). His template
-- (boss_ras_frostwhisper_rework, AIName '', health, DamageModifier 3.5, immunities), the Blizzard anchor 300534 and his
-- spells are apps/dbc-tools source/npcs/scholomance/ras_frostwhisper.py.

-- SmartAI 10508 (Frost Armor 18100 out of combat, Fear 12096, Frostbolt Volley 8398, Freeze 18763, Chill Nova 18099) is
-- removed (SC "Stock kit", approved): boss_ras_frostwhisper_rework keeps Frost Armor out of combat, reworks the Volley
-- and the Nova, and retires Fear and Freeze. The quest Boon of Life (spell_scholomance_boon_of_life_aura) is C++ and
-- stays. His patrol (creature_template_addon path 488500) is untouched.
DELETE FROM `smart_scripts` WHERE `entryorguid` = 10508 AND `source_type` = 0;

-- Texts (SC "Text"): group 0 is the stock yell, kept as it is (the Boon of Life and S12's hard mode transition); the
-- two new lines are boss emotes (41), so they name the mechanic on screen. $n is the marked player. Line 2 is the hard
-- mode's Siphon Warmth (S12 says it).
DELETE FROM `creature_text` WHERE `CreatureID` = 10508;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(10508, 0, 0, 'THIS CANNOT BE!!', 14, 0, 100, 0, 0, 0, 6371, 0, 'Ras Frostwhisper'),
(10508, 1, 0, '%s marks $n with the frost of the grave!', 41, 0, 100, 0, 0, 0, 0, 0, 'Ras Frostwhisper - Frost Mark (RF5)'),
(10508, 2, 0, '%s reaches for the warmth of the living!', 41, 0, 100, 0, 0, 0, 0, 0, 'Ras Frostwhisper - Siphon Warmth (RF10, hard mode)');
