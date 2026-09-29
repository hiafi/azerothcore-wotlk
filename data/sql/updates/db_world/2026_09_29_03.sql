-- DB update 2026_09_29_02 -> 2026_09_29_03
-- Training dummies take real damage (never lethal) and refill to full every 3 sec, so leech and
-- damage-based self-heals (Drain Life, ...) work on them. The stock npc_training_dummy zeroes all
-- damage; npc_custom_training_dummy (src/server/scripts/Custom/custom_training_dummy.cpp) replaces
-- it on every entry that used it. The mod-dpssim dummies (900004-900006) are left on their own AI.
UPDATE `creature_template` SET `ScriptName` = 'npc_custom_training_dummy' WHERE `entry` IN
(4952, 16111, 17578, 24792, 30527, 31143, 31144, 31146, 32541, 32542, 32543, 32545, 32546, 32547, 32666, 32667,
900001, 900002, 900003) AND `ScriptName` = 'npc_training_dummy';
