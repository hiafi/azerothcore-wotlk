-- Two real bugs found via live playtest (docs/frost-mage-playtest-script.md section 8 / Frozen
-- Orb section 4), both leftovers from earlier passes that never got a matching SQL fix:
--
-- 1. Ice Lance (30455) was re-leveled to BaseLevel/SpellLevel 15 in spell_dbc back when the
--    single-rank relearn landed (docs/frost-mage-handoff.md Phase 2), but the `trainer_spell` row
--    that actually gates when a real Mage trainer will teach it was never updated to match - it
--    was still ReqLevel 66, the old pre-rework value. Confirmed via live DB: only one trainer_spell
--    row exists for 30455 (TrainerId 16), guard matches the pre-fix value exactly.
UPDATE `trainer_spell` SET `ReqLevel` = 15 WHERE `SpellId` = 30455 AND `ReqLevel` = 66;

-- 2. Frozen Orb's projectile creature (npc_mage_frozen_orb, 300001 - spell_mage.cpp) was left on
--    display 1126, the stock Invisible Stalker model, per that file's own comment ("Display left as
--    the stock invisible-stalker model") - a known placeholder, not a real Frost Orb visual.
--    Repointed to 25144 ("Frost Sphere", Toravon the Ice Watcher's ability in Vault of Archavon) -
--    a real, already-used-in-3.3.5 rolling ice-orb model, confirmed via live DB that displayID
--    25144 is otherwise only used by other "Frost Sphere" template rows (34606/34649/3460602/
--    3460603) plus one "Lightning" elemental orb - not a stalker/invisible fallback.
UPDATE `creature_template_model` SET `CreatureDisplayID` = 25144 WHERE `CreatureID` = 300001 AND `CreatureDisplayID` = 1126;
