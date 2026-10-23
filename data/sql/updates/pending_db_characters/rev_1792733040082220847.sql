-- shaman-rework playtest fix pass 2 / P6: Call of Thunder's capstone no longer grants a second, stun-castable Thunderstorm (spell 202594 is removed). Must be applied with the worldserver stopped.
-- keep the shaman's action bar button: point it at the one remaining Thunderstorm
UPDATE `character_action` SET `action` = 51490 WHERE `type` = 0 AND `action` = 202594;
-- drop the removed spell and its cooldown from every character
DELETE FROM `character_spell` WHERE `spell` = 202594;
DELETE FROM `character_spell_cooldown` WHERE `spell` = 202594;
