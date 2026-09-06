-- Shield Specialization (200031-200033, Protection Warrior rework phase 2) grants a chance to
-- generate 5 rage "when a block, dodge, or parry occurs" via a PROC_TRIGGER_SPELL effect, but its
-- DBC ProcTypeMask (87376) is made up entirely of PROC_FLAG_DONE_* bits (things the warrior does),
-- so it never matches a taken-hit event; and with no spell_proc row, SpellMgr's auto-generated
-- fallback sets HitMask to 0, which for taken procs defaults to normal/critical hits only -
-- excluding dodge/parry/block outright even if the flags did match. Net effect: the talent has
-- never actually granted rage. Override ProcFlags to taken melee auto-attacks and taken melee-class
-- spell attacks, and HitMask to dodge/parry/(full) block; leave Chance at 0 so each rank keeps its
-- own DBC ProcChance (33/66/100).
DELETE FROM `spell_proc` WHERE `SpellId` IN (200031, 200032, 200033);
INSERT INTO `spell_proc` (`SpellId`, `ProcFlags`, `HitMask`)
    VALUES
    (200031, 0x00000028, 0x00002070),
    (200032, 0x00000028, 0x00002070),
    (200033, 0x00000028, 0x00002070);
