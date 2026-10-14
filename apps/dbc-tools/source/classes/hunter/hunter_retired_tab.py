"""
The retired-talent holding tab (TalentTab 60800) that `retire_talent()` moves talents to.

Class-agnostic and SHARED-owned (hunter-rework SHARED §A4, §C7.7): it sits in the hunter package only because a
`retire_talent()` caller has to be able to see one `tab()` declaration, and the hunter rework is the first caller.
Any later class may call `retire_talent()` without declaring its own - do not duplicate this row.

ClassMask 0 and PetTalentMask 0, so no class and no pet type matches it: every core path that walks Talent.dbc rows
and every mod-playerbots path skips a row on it, and the client never shows the tab. A real tab, not TabID 0:
mod-playerbots' InitPetTalents dereferences the tab of every Talent.dbc row without a null check.

order_index 3: past the three real tabs of any class, so mod-multibot-bridge's per-tab point summary
(`tabpage >= tabs.size()`) skips a stale character_talent row on a retired talent, and the tab packs last in
TalentTab.dbc. `CharacterDatabaseCleaner::TalentCheck` keeps such rows (the tab is valid), so the characters SQL
that retires a talent must delete its `character_talent` rows itself.
"""

from lib.dsl.registry import tab

retired_60800_tab = tab(id=60800, name='Retired', class_mask=0, pet_talent_mask=0, order_index=3)
