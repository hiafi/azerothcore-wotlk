-- shaman-rework S3a: Enhancement character data cleanup. Must be applied with the worldserver stopped.
-- Do NOT delete character_spell 3127 (Parry): it is a baseline spell, not a talent castable.
-- force a talent reset for every shaman (the Enhancement tree moves)
UPDATE `characters` SET `at_login` = `at_login` | 4 WHERE `class` = 7;
-- every stock Enhancement rank spell, dropped ranks included (orphan talent ranks crash login), plus the new rank spells
DELETE FROM `character_talent` WHERE `spell` IN (16259, 16295, 52456, 16043, 16130, 17485, 17486, 17487, 17488, 17489, 16258, 16293, 16255, 16302, 16303, 16304, 16305, 16262, 16287, 16261, 16290, 51881, 16266, 29079, 29080, 43338, 16254, 16271, 16272, 16256, 16281, 16282, 16283, 16284, 16252, 16306, 16307, 16308, 16309, 29192, 29193, 16268, 51883, 51884, 51885, 30802, 30808, 30809, 29082, 29084, 29086, 63373, 63374, 30816, 30818, 30819, 17364, 51525, 51526, 51527, 60103, 51521, 51522, 30812, 30813, 30814, 30823, 51523, 51524, 51528, 51529, 51530, 51531, 51532, 51533, 202360, 202361, 202362, 202363, 202364, 202365, 202366, 202367, 202368, 202369, 202370, 202371, 202372, 202373, 202374, 202375);
-- talent castables that move or are reworked: drop the stored spell and its button (talent learning re-grants it)
DELETE FROM `character_spell` WHERE `spell` IN (60103, 51533, 17364, 30823);
DELETE FROM `character_action` WHERE `type` = 0 AND `action` IN (60103, 51533, 17364, 30823);
-- reworked buffs: Flurry, Maelstrom Weapon, Shamanistic Rage, Feral Spirit, Frozen Power root, Stoneskin (a reset build starts clean)
DELETE FROM `character_aura` WHERE `spell` IN (16257, 16277, 16278, 16279, 16280, 53817, 30823, 51533, 63685, 202206);
DELETE FROM `character_spell_cooldown` WHERE `spell` IN (51533, 30823, 60103, 17364);
