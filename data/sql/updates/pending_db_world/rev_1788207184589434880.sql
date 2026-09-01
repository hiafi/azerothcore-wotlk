-- Frost Mage rework - buff/debuff-bar tooltips ("no text" playtest report, 2026-08-31):
-- the client renders a buff/debuff icon's mouseover tooltip from `AuraDescription_Lang_enUS`,
-- not `Description_Lang_enUS` (the latter is what the spellbook/cast-bar tooltip uses). Six
-- rows in this session's new content set `Description_Lang_enUS` but never `AuraDescription_*`,
-- so their icon showed with no text even though the spell itself had a description - confirmed
-- against a working control (Refreshment, 200006, already had both fields and was never
-- reported broken) and against real Blizzard buff/debuff spells (Mage Armor, Ice Barrier, Slow,
-- Icy Veins, ...), which always populate AuraDescription for anything shown on a unit frame.
--
-- Per user direction, AuraDescription is set to the same text as the existing Description for
-- each: Icicles (200001), Shattering Cold (200003), Frozen Core's stacking Frost-damage buff
-- (200016/200017/200018), Frozen Core: Piercing Cold (200019), and Empowering Frostbolt
-- (200023/200024). Source of truth: apps/dbc-tools/source/spells/mage.csv and mage_talents.csv.
-- The `AuraDescription_Lang_enUS IS NULL` guard makes this a no-op on a second run.
UPDATE `spell_dbc` SET `AuraDescription_Lang_Mask` = 16712188, `AuraDescription_Lang_enUS` = 'Frost energy has gathered around you. Stacks up to 5 times; consumed by Glacial Spike.' WHERE `ID` = 200001 AND `AuraDescription_Lang_enUS` IS NULL;
UPDATE `spell_dbc` SET `AuraDescription_Lang_Mask` = 16712188, `AuraDescription_Lang_enUS` = 'This target''s frozen state is being exploited by the caster''s spells and abilities.' WHERE `ID` = 200003 AND `AuraDescription_Lang_enUS` IS NULL;
UPDATE `spell_dbc` SET `AuraDescription_Lang_Mask` = 16712188, `AuraDescription_Lang_enUS` = 'Increases Frost damage dealt by 2%.' WHERE `ID` = 200016 AND `AuraDescription_Lang_enUS` IS NULL;
UPDATE `spell_dbc` SET `AuraDescription_Lang_Mask` = 16712188, `AuraDescription_Lang_enUS` = 'Increases Frost damage dealt by 4%.' WHERE `ID` = 200017 AND `AuraDescription_Lang_enUS` IS NULL;
UPDATE `spell_dbc` SET `AuraDescription_Lang_Mask` = 16712188, `AuraDescription_Lang_enUS` = 'Increases Frost damage dealt by 6%.' WHERE `ID` = 200018 AND `AuraDescription_Lang_enUS` IS NULL;
UPDATE `spell_dbc` SET `AuraDescription_Lang_Mask` = 16712188, `AuraDescription_Lang_enUS` = 'Frost damage over time, pierced into the target''s core.' WHERE `ID` = 200019 AND `AuraDescription_Lang_enUS` IS NULL;
UPDATE `spell_dbc` SET `AuraDescription_Lang_Mask` = 16712188, `AuraDescription_Lang_enUS` = 'Increases critical strike damage bonus and Frost damage dealt.' WHERE `ID` = 200023 AND `AuraDescription_Lang_enUS` IS NULL;
UPDATE `spell_dbc` SET `AuraDescription_Lang_Mask` = 16712188, `AuraDescription_Lang_enUS` = 'Increases critical strike damage bonus and Frost damage dealt.' WHERE `ID` = 200024 AND `AuraDescription_Lang_enUS` IS NULL;
