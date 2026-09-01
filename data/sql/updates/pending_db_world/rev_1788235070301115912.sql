-- Fingers of Frost (74396) charge consumption: playtest bugfix. The stock spell_proc row's
-- SchoolMask was 84 (Fire|Frost|Arcane), inherited unchanged from the pre-rework live data -
-- that let a plain Fire spell like Fireball (pure school 4, no Frost component) consume a charge,
-- since SchoolMask matching only requires overlap. docs/frost-mage-redesign.md never intended
-- Fingers of Frost to be spent by non-Frost damage, so this restricts SchoolMask to Frost (16)
-- alone. Frostfire Bolt (school 20 = Fire|Frost) still matches since 20 & 16 != 0.
DELETE FROM `spell_proc` WHERE `SpellId` = 74396;
INSERT INTO `spell_proc` (`SpellId`, `SchoolMask`, `SpellFamilyName`, `SpellFamilyMask0`, `SpellFamilyMask1`, `SpellFamilyMask2`, `ProcFlags`, `SpellTypeMask`, `SpellPhaseMask`, `HitMask`, `AttributesMask`, `DisableEffectsMask`, `ProcsPerMinute`, `Chance`, `Cooldown`, `Charges`) VALUES
(74396, 16, 3, 685904631, 1151048, 0, 65536, 0, 3, 0, 2, 0, 0, 0, 0, 0);
