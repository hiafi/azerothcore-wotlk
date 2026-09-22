-- Priest Holy rework (docs/reworks/priest-holy-rework.md sec 3 "Lightwell",
-- priest-rework.HOLY.md 6,1): Lightwell now heals automatically (npc_pet_pri_lightwell,
-- src/server/scripts/Pet/pet_priest.cpp) with no player click-to-drink interaction. Confirmed via
-- data/sql/base/db_world/creature_template.sql: all six Lightwell entries carry
-- npcflag=16777216 (UNIT_NPC_FLAG_SPELLCLICK) and data/sql/base/db_world/npc_spellclick_spells.sql
-- has a matching row for each (spell 60123, spell_pri_lightwell's own bound spell) - both removed.

UPDATE `creature_template` SET `npcflag` = `npcflag` & ~0x01000000 WHERE `entry` IN (31883, 31893, 31894, 31895, 31896, 31897);

DELETE FROM `npc_spellclick_spells` WHERE `npc_entry` IN (31883, 31893, 31894, 31895, 31896, 31897) AND `spell_id` = 60123;
