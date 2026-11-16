-- Blackrock Spire build WP-B2: Shadow Hunter Vosh'gajin (9236), the rows dbc-tools cannot declare
-- (.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.5 row B2; build spec
-- docs/dungeons/blackrock-spire-rework.md SP 815-1021). Her template (boss_shadow_hunter_voshgajin_rework, AIName '',
-- health, DamageModifier 3.5, immunities, INSTANCE_BIND), the Voodoo Doll 300703 and her spells 210060-210075 are
-- apps/dbc-tools source/npcs/blackrock_spire/voshgajin.py. Her two SmartAI rows (Hex 16097, Curse of Blood 16098) are
-- removed by rev_blackrock_spire_skeleton.sql (WP-S0), not here.

-- The two Smolderthorn Shadow Priests that stand beside her (spawn guids 43550 and 43551, entry 9240) leave: they
-- Hex, Mana Burn and dispel, and were pulled with her at 8 yd (SP "Stock kit", ruling 27). The rest of the hall's
-- trash stays.
DELETE FROM `creature` WHERE `id` = 9240 AND `guid` IN (43550, 43551);
DELETE FROM `creature_addon` WHERE `guid` IN (43550, 43551);

-- Texts (SP "Text"; she had none): the pull, the 50% and the death lines are yells (14); the binding is a boss emote
-- (41), so it names the moment on screen. $n is the player the doll is bound to. No torment emotes (ruling 26): the
-- doll's tell is the warning.
DELETE FROM `creature_text` WHERE `CreatureID` = 9236;
INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, `Emote`,
    `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES
(9236, 0, 0, 'More pretty dolls for Vosh''gajin! Come, let me make you one.', 14, 0, 100, 0, 0, 0, 0, 0,
    'Shadow Hunter Vosh''gajin - Aggro'),
(9236, 1, 0, '%s binds the doll to $n!', 41, 0, 100, 0, 0, 0, 0, 0, 'Shadow Hunter Vosh''gajin - Bind (VG1)'),
(9236, 2, 0, 'You break so slow... Vosh''gajin play rough now!', 14, 0, 100, 0, 0, 0, 0, 0,
    'Shadow Hunter Vosh''gajin - Twin torments (heroic, 50%, VG6)'),
(9236, 3, 0, 'My dolls... who will play with them now?', 14, 0, 100, 0, 0, 0, 0, 0,
    'Shadow Hunter Vosh''gajin - Death');
