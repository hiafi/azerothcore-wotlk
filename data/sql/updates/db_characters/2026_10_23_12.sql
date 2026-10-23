-- DB update 2026_10_23_11 -> 2026_10_23_12
-- shaman-rework S1a: Elemental character data cleanup. Run with the worldserver stopped.
-- force a talent reset for every shaman (the Elemental tree moves)
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 7;
-- every stock Elemental rank spell, dropped ranks included (orphan talent ranks crash login)
DELETE FROM `character_talent` WHERE `spell` IN (16039, 16109, 16110, 16111, 16112, 16035, 16105, 16106, 16107, 16108, 16038, 16160, 16161, 28996, 28997, 28998, 30160, 29179, 29180, 16040, 16113, 16114, 16115, 16116, 16164, 16089, 60184, 60185, 60187, 60188, 16086, 16544, 29062, 29064, 29065, 28999, 29000, 16041, 30664, 30665, 30666, 30672, 30673, 30674, 16578, 16579, 16580, 16581, 16582, 16166, 51483, 51485, 51486, 63370, 63372, 51466, 51470, 30675, 30678, 30679, 51474, 51478, 51479, 30706, 51480, 51481, 51482, 62097, 62098, 62099, 62100, 62101, 51490);
-- Thunderstorm moves to a new talent cell: drop the stored spell and its button (talent learning re-grants it).
-- Elemental Mastery 16166 is a spellbook talent: with its character_talent row gone the login reset would never remove
-- it, so drop its stored spell and button too
DELETE FROM `character_spell` WHERE `spell` IN (51490, 16166);
DELETE FROM `character_action` WHERE `type` = 0 AND `action` IN (51490, 16166);
-- reworked buffs: Elemental Mastery haste, Lava Flows haste, Clearcasting, Devastation (stock buff ids included)
DELETE FROM `character_aura` WHERE `spell` IN (16166, 64701, 64694, 65263, 65264, 16246, 30165, 29177, 29178);
-- spells whose cooldown category moved
DELETE FROM `character_spell_cooldown` WHERE `spell` IN (16166, 51490);
