-- Three more bugs found via live playtest (docs/frost-mage-playtest-script.md):
--
-- 1. Conjure Refreshment (42955) kept rank 1's original learn level (75, `BaseLevel`/`SpellLevel`
--    in spell_dbc, `ReqLevel` in trainer_spell) from the single-rank bootstrap - see
--    apps/dbc-tools/source/spells/mage.csv's notes on this row. Conjure Refreshment replaces
--    Conjure Food/Water (docs/frost-mage-redesign.md sec 2, "Conjure Food / Water: This will be
--    replaced in favor of Conjure Refreshment"), which were learnable in the level 8-20 range, so
--    gating the replacement behind level 75 leaves mages without any self-sustain food/water spell
--    for most of leveling. Dropped to level 10 (both the spell itself and the one trainer_spell row
--    that teaches it - confirmed via live DB only TrainerId 16 has a row for this spell).
UPDATE `spell_dbc` SET `BaseLevel` = 10, `SpellLevel` = 10 WHERE `ID` = 42955 AND `BaseLevel` = 75 AND `SpellLevel` = 75;
UPDATE `trainer_spell` SET `ReqLevel` = 10 WHERE `SpellId` = 42955 AND `ReqLevel` = 75;

-- 2. Frozen Orb's projectile creature (npc_mage_frozen_orb, 300001 - spell_mage.cpp) was given
--    UNIT_FLAG_IMMUNE_TO_PC | UNIT_FLAG_IMMUNE_TO_NPC (0x100 | 0x200) alongside UNIT_FLAG_NOT_
--    SELECTABLE (0x2000000), evidently meant to keep the trigger from being targeted/attacked by
--    anything. That backfires: Unit::_IsValidAttackTarget (Unit.cpp) treats a caster's own
--    IsImmuneToNPC()/IsImmuneToPC() as blocking *outgoing* attacks too, not just incoming ones -
--    `(!target->HasUnitFlag(UNIT_FLAG_PLAYER_CONTROLLED) && IsImmuneToNPC())` and
--    `(target->HasUnitFlag(UNIT_FLAG_PLAYER_CONTROLLED) && IsImmuneToPC())` both key off `this`
--    (the attacker, i.e. the orb) being immune - so the orb could never register a valid attack
--    target against either mobs or players, and its periodic pulse (200009 -> 200008,
--    TARGET_UNIT_SRC_AREA_ENEMY) landed on nobody. UNIT_FLAG_NOT_SELECTABLE alone already makes
--    isTargetableForAttack() return false (Unit.cpp), so it's sufficient on its own to keep the
--    orb from being attacked - the two IMMUNE flags were both redundant for that purpose and
--    actively broke the orb's own damage. Removed, keeping NOT_SELECTABLE.
UPDATE `creature_template` SET `unit_flags` = 33554432 WHERE `entry` = 300001 AND `unit_flags` = 33555200;
