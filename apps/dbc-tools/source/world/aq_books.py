"""
The AQ20 class spell books become gray vendor junk (hunter-rework H0-FIX, user ruling 2026-10-14).

Every class book that drops from the Ruins of Ahn'Qiraj (reference_loot_template 34024: Tome of / Grimoire of /
Codex of / Libram: / Tablet of / Book of / Manual of / Handbook of / Guide:) teaches a stock rank-upgrade spell
(e.g. 25295 Serpent Sting IX). The class rework collapsed those rank chains (no spell_ranks rows are left), so
the taught spell would be a second, unscaled copy of the survivor. Each book now has no use effect: Quality 0
(gray), SellPrice 200000 (20 gold), spellid_1 (the 483 "Learning" effect), spellid_2 and its trigger cleared, and
a description that no longer promises a spell.

Entries: the 25 books in reference 34024, plus 21293 "Tablet of Grace of Air Totem III" and 21302 "Handbook of
Deadly Poison V", the same AQ series (their spell ids 25359 / 25347 are serverside placeholders) that no
loot table drops here, and 24102 "Manual of Eviscerate IX" (Blackhand Assassin, Blackrock Spire): not an AQ book, but
the same kind of rank-upgrade book (user, 2026-10-14).

The item query cache: clients only see the gray name after deleting their Cache folder.
"""

from lib.dsl.registry import item_template

AQ_BOOK_ENTRIES = (
    21214, 21279, 21280, 21281, 21282, 21283, 21284, 21285, 21287, 21288, 21289, 21290, 21291, 21292, 21293,
    21294, 21295, 21296, 21297, 21298, 21299, 21300, 21302, 21303, 21304, 21306, 21307,
    24102,
)

for _entry in AQ_BOOK_ENTRIES:
    item_template(_entry, Quality=0, SellPrice=200000, spellid_1=0, spelltrigger_1=0, spellid_2=0, spelltrigger_2=0,
                  description="Its lessons are long out of date.")
