"""
Shaman - the server-wide temporary-haste groups (S1a A4; shaman-rework.HASTE-GROUP-PROPOSAL.md "Recommendation", confirmed by
the user in PLAN 1C-4 Q10, S1a WP brief Decision 10).

The rule (user, 2026-10-20): Bloodlust / Heroism stack with every other haste increase; the other temporary haste cooldowns
share one exclusive group, the higher wins. Group stack rule 3 (EXCLUSIVE_SAME_EFFECT) keeps both auras and counts only the
highest amount of ONE aura type, guessed at load from the most frequent type among the members (SpellMgr.cpp:1834-1925): a
member without that type logs "does not share aura assigned for group" at boot (must stay 0), so the two aura types get
two groups.

  1122 "Temporary Haste Buffs" (stock, rule 3, spell casting speed, aura 65): Bloodlust 2825 and Heroism 32182 LEAVE it
        (they carry a 65 effect and would otherwise be excluded by Power Infusion); Power Infusion 10060 stays; Icy Veins
        12472 (aura 65 +20) and Elemental Mastery's haste 64701 (aura 65, +10 / +15 with Shamanism r3) JOIN.
  1258 new (rule 3, all haste, aura 193): Berserking 26297, Rapid Fire 3045, Dark Soul: Misery 200732 (all three carry 193).

Not in a haste group, on purpose (proposal tables A / B): Time Warp 200070 (a Bloodlust copy), Blade Flurry 13877 (alone in its aura
family) and every talent proc / rotation buff (Lava Flows, Unrelenting Storm, Wind Rush, Fusion, Flurry, ...). Group 1123
(Power Infusion vs Arcane Power, rule 4) is untouched. A 65-type buff and a 193-type buff still stack with each other (accepted,
proposal judgment call 2a: a Troll Elemental shaman gets Elemental Mastery + Berserking).

The non-shaman members are bare stock ids: spell_group() accepts them, and importing the other classes' spell objects would
couple the files for nothing (the declarations live in mage_spells.py, hunter_spells.py, warlock_spells.py, the stock DBC).
"""

from lib.dsl.registry import leave_spell_group, spell_group, spell_group_rule

from .shaman_spells import elemental_mastery_haste_64701

_BLOODLUST = 2825
_HEROISM = 32182
_ICY_VEINS = 12472
_BERSERKING = 26297
_RAPID_FIRE = 3045
_DARK_SOUL_MISERY = 200732

_HASTE_ALL_GROUP = 1258

leave_spell_group(1122, _BLOODLUST)
leave_spell_group(1122, _HEROISM)
spell_group(1122, _ICY_VEINS, elemental_mastery_haste_64701)

spell_group(_HASTE_ALL_GROUP, _BERSERKING, _RAPID_FIRE, _DARK_SOUL_MISERY)
spell_group_rule(_HASTE_ALL_GROUP, 3, 'Temporary haste cooldowns, all haste (193): highest counts')
