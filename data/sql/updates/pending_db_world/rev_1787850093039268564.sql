-- Frozen Orb's projectile (300001, npc_mage_frozen_orb) previously used the stock Invisible
-- Stalker model (1126) as a functional placeholder (see rev_1787563173168071680.sql). Swapping it
-- for the real "Charged Sphere" model used by Ulduar's Summon Charged Sphere
-- (https://www.wowhead.com/wotlk/spell=63527/summon-charged-sphere -> npc 33715 "Charged Sphere")
-- so the orb actually looks like a glowing sphere. DisplayID 26753 is npc 33715's own
-- creature_template_model row (data/sql/base/db_world/creature_template_model.sql), already a
-- valid, in-use CreatureDisplayID (also used by npcs 33138/33756) - not a new/invented value.
DELETE FROM `creature_template_model` WHERE `CreatureID` = 300001;
INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, `VerifiedBuild`) VALUES
(300001, 0, 26753, 1, 1, 0);
