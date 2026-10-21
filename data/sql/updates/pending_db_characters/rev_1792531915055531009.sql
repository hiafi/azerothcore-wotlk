-- shaman-rework S2a: Restoration character data cleanup. Run with the worldserver stopped.
-- force a talent reset for every shaman (the Restoration tree moves)
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 7;
-- every stock Restoration rank spell, dropped ranks included (orphan talent ranks crash login)
DELETE FROM `character_talent` WHERE `spell` IN (16182, 16226, 16227, 16228, 16229, 16173, 16222, 16223, 16224, 16225, 16184, 16209, 29187, 29189, 29191, 16179, 16214, 16215, 16216, 16217, 16180, 16196, 16198, 16181, 16230, 16232, 55198, 16176, 16235, 16240, 16187, 16205, 16206, 16194, 16218, 16219, 16220, 16221, 29202, 29205, 29206, 16188, 30864, 30865, 30866, 16178, 16210, 16211, 16212, 16213, 30881, 30883, 30884, 30885, 30886, 16190, 51554, 51555, 30872, 30873, 30867, 30868, 30869, 51556, 51557, 51558, 51560, 51561, 51562, 51563, 51564, 51565, 51566, 61295);
-- talent spellbook spells that move or retire: drop the stored spell and its button (talent learning re-grants it)
DELETE FROM `character_spell` WHERE `spell` IN (61295, 16190, 55198, 16188);
DELETE FROM `character_action` WHERE `type` = 0 AND `action` IN (61295, 16190, 55198, 16188);
-- reworked buffs: Tidal Waves, Tidal Force, Nature's Swiftness, Ancestral Fortitude, Riptide
DELETE FROM `character_aura` WHERE `spell` IN (53390, 55166, 55198, 16188, 16177, 16236, 16237, 61295);
DELETE FROM `character_spell_cooldown` WHERE `spell` IN (16188, 16190, 55198, 61295);
