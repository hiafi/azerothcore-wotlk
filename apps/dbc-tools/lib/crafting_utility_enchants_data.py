"""
Crafting rework C7 follow-up (user 2026-11-12): the stock utility enchants become scrolls like the C6 enchants.

The 27 Enchanting utility enchants C6 kept (decision 1d: armor, resistances, absorption, Minor Speed, gathering and
riding gloves, Threat, Stealth) were the last direct enchants; Subtlety 25084 retired instead (the C7 premium
"Scroll of Enchant Cloak - Subtlety" from T1 is the same enchant, review 2026-11-12). Each recipe keeps its spell id (so its
trainer row, its drop or vendor recipe item and every character that knows it keep working), its rod and its
reagents, but now creates the stock 3.3.5 scroll of that enchant ("Scroll of Enchant Cloak - Greater Resistance",
the item the vellum used to make). The scroll's on-use spell is a new spell (209000 + n) that applies the stock
enchant, shaped like the C6 use spells; anyone can use it, so the scrolls trade. No vellum.

Reagents are the stock ones with the C6 squish applied (`SURVIVOR`, the copy of `source/world/crafting_squish.py`'s
map, so the recipes that only drop or come from vendors stop asking for dusts and essences that no longer drop) and
the five Ahn'Qiraj recipes' Outland materials (3.3.5 moved them to Outland reagents) taken back to vanilla ones
(`OUTLAND`). Declared by `source/world/crafting_utility_enchants.py`; the trade skill window puts them under their
slot (write_crafting_categories.py). Row order fixes the ids: never reorder, append.
"""

from __future__ import annotations

from dataclasses import dataclass

ENCHANTING = 333
USE_SPELL_BASE = 209000
ILLUSION_DUST, LESSER_ETERNAL, GREATER_ETERNAL = 16204, 16202, 16203
SMALL_BRILLIANT, LARGE_BRILLIANT = 14343, 14344
BLACK_LOTUS, ESSENCE_OF_UNDEATH, LIVING_ESSENCE = 13468, 12808, 12803

# Old vanilla enchanting material -> its squished survivor (copy of crafting_squish.SURVIVOR; the test compares them).
SURVIVOR = {
    10940: ILLUSION_DUST, 11083: ILLUSION_DUST, 11137: ILLUSION_DUST, 11176: ILLUSION_DUST,
    10938: LESSER_ETERNAL, 10998: LESSER_ETERNAL, 11134: LESSER_ETERNAL, 11174: LESSER_ETERNAL,
    10939: GREATER_ETERNAL, 11082: GREATER_ETERNAL, 11135: GREATER_ETERNAL, 11175: GREATER_ETERNAL,
    10978: SMALL_BRILLIANT, 11138: SMALL_BRILLIANT, 11177: SMALL_BRILLIANT,
    11084: SMALL_BRILLIANT, 11139: SMALL_BRILLIANT, 11178: SMALL_BRILLIANT,
}
# Outland materials in the 3.3.5 Ahn'Qiraj enchant recipes -> the vanilla material of the same role.
OUTLAND = {
    22448: LARGE_BRILLIANT,  # Small Prismatic Shard
    22446: GREATER_ETERNAL,  # Greater Planar Essence
    22794: BLACK_LOTUS,  # Fel Lotus
    22456: ESSENCE_OF_UNDEATH,  # Primal Shadow
    21886: LIVING_ESSENCE,  # Primal Life
}


@dataclass(frozen=True)
class Utility:
    recipe: int  # the stock recipe spell, re-declared to create the scroll
    name: str
    scroll: int  # the stock scroll item
    enchant: int  # the stock SpellItemEnchantment
    target: tuple[int, int, int]  # EquippedItemClass, EquippedItemSubclass mask, EquippedItemInvTypes mask
    rod: int  # RequiredTotemCategoryID_1 (the runed rod)
    stock_reagents: tuple[tuple[int, int], ...]
    description: str

    @property
    def slot(self) -> str:
        """The slot word of the name ("Enchant Cloak - Defense" -> "Cloak")."""
        return self.name.removeprefix("Enchant ").split(" - ")[0]

    @property
    def scroll_name(self) -> str:
        """The scroll's name, also the recipe's (as the C6 and premium recipes are named after their item)."""
        return f"Scroll of {self.name}"

    @property
    def reagents(self) -> tuple[tuple[int, int], ...]:
        merged: dict[int, int] = {}
        for item, count in self.stock_reagents:
            item = OUTLAND.get(item, SURVIVOR.get(item, item))
            merged[item] = merged.get(item, 0) + count
        return tuple(merged.items())


UTILITY = (
    Utility(13890, 'Enchant Boots - Minor Speed', 38837, 911, (4, 30, 256), 9,
            ((11177, 1), (7909, 1), (11174, 1)),
            'Permanently enchant boots to give a slight movement speed increase.'),
    Utility(13538, 'Enchant Chest - Lesser Absorption', 38798, 63, (4, 31, 1048608), 7,
            ((10940, 2), (11082, 1), (11084, 1)),
            'Enchant a piece of chest armor so it has a 5% chance per hit of giving you 25 points of damage '
            'absorption.'),
    Utility(7426, 'Enchant Chest - Minor Absorption', 38767, 44, (4, 31, 1048608), 6,
            ((10940, 2), (10938, 1)),
            'Enchant a piece of chest armor so it has a 2% chance per hit of giving you 10 points of damage '
            'absorption.'),
    Utility(13635, 'Enchant Cloak - Defense', 38806, 848, (4, 30, 65536), 8,
            ((11138, 1), (11083, 3)),
            'Permanently enchant a cloak to give 30 additional armor.'),
    Utility(13657, 'Enchant Cloak - Fire Resistance', 38815, 2463, (4, 30, 65536), 8,
            ((11134, 1), (7068, 1)),
            'Permanently enchant a cloak to give 7 Fire Resistance.'),
    Utility(13746, 'Enchant Cloak - Greater Defense', 38825, 884, (4, 30, 65536), 9,
            ((11137, 3),),
            'Permanently enchant a cloak to give 50 additional armor.'),
    Utility(25081, 'Enchant Cloak - Greater Fire Resistance', 38891, 2619, (4, 31, 65536), 10,
            ((22448, 3), (22446, 3), (7078, 4)),
            'Permanently enchant a cloak to increase fire resistance by 15.'),
    Utility(25082, 'Enchant Cloak - Greater Nature Resistance', 38892, 2620, (4, 31, 65536), 10,
            ((22448, 2), (22446, 3), (12803, 4)),
            'Permanently enchant a cloak to increase nature resistance by 15.'),
    Utility(20014, 'Enchant Cloak - Greater Resistance', 38858, 1888, (4, 30, 65536), 9,
            ((7077, 1), (7075, 1), (7079, 1), (7081, 1), (7972, 1)),
            'Permanently enchant a cloak to increase all resistances by 5.'),
    Utility(7861, 'Enchant Cloak - Lesser Fire Resistance', 38784, 256, (4, 31, 65536), 7,
            ((6371, 1), (10998, 1)),
            'Permanently enchant a cloak so that it increases resistance to fire by 5.'),
    Utility(13421, 'Enchant Cloak - Lesser Protection', 38790, 744, (4, 0, 65536), 6,
            ((10940, 6), (10978, 1)),
            'Permanently enchant a cloak to increase armor by 20.'),
    Utility(13522, 'Enchant Cloak - Lesser Shadow Resistance', 38795, 804, (4, 31, 65536), 7,
            ((11082, 1), (6048, 1)),
            'Permanently enchant a cloak to increase shadow resistance by 10.'),
    Utility(7771, 'Enchant Cloak - Minor Protection', 38775, 783, (4, 31, 65536), 6,
            ((10940, 3), (10939, 1)),
            'Enchant a cloak to provide 10 additional points of armor.'),
    Utility(7454, 'Enchant Cloak - Minor Resistance', 38770, 65, (4, 31, 65536), 6,
            ((10940, 1), (10938, 2)),
            'Permanently enchant a cloak so that it increases the resistance to all schools of magic by 1.'),
    Utility(13794, 'Enchant Cloak - Resistance', 38826, 903, (4, 30, 65536), 9,
            ((11174, 1),),
            'Permanently enchant a cloak to give 3 to all resistances.'),
    Utility(25083, 'Enchant Cloak - Stealth', 38893, 910, (4, 31, 65536), 10,
            ((22448, 3), (22446, 3), (22794, 2)),
            'Permanently enchant a cloak to increase stealth.'),
    Utility(20015, 'Enchant Cloak - Superior Defense', 38859, 1889, (4, 30, 65536), 9,
            ((16204, 8),),
            'Permanently enchant a cloak to increase armor by 70.'),
    Utility(13868, 'Enchant Gloves - Advanced Herbalism', 38834, 909, (4, 31, 1024), 9,
            ((11137, 3), (8838, 3)),
            'Permanently enchant gloves to increase herbalism skill by 5.'),
    Utility(13841, 'Enchant Gloves - Advanced Mining', 38831, 906, (4, 31, 1024), 9,
            ((11137, 3), (6037, 3)),
            'Permanently enchant gloves to increase mining skill by 5.'),
    Utility(13620, 'Enchant Gloves - Fishing', 38802, 2603, (4, 31, 1024), 7,
            ((11083, 1), (6370, 3)),
            'Permanently enchant gloves to increase fishing skill by 2.'),
    Utility(13617, 'Enchant Gloves - Herbalism', 38801, 845, (4, 31, 1024), 7,
            ((11083, 1), (3356, 3)),
            'Permanently enchant gloves to increase herbalism skill by 2.'),
    Utility(13612, 'Enchant Gloves - Mining', 38800, 844, (4, 31, 1024), 7,
            ((11083, 1), (2772, 3)),
            'Permanently enchant gloves to increase mining skill by 2.'),
    Utility(13947, 'Enchant Gloves - Riding Skill', 38850, 930, (4, 31, 1024), 9,
            ((11178, 2), (11176, 3)),
            'Permanently enchant gloves to increase mount speed by 2%.  Must be level 70 or lower to gain this '
            'benefit.'),
    Utility(13698, 'Enchant Gloves - Skinning', 38823, 865, (4, 31, 1024), 8,
            ((11137, 1), (7392, 3)),
            'Permanently enchant gloves to increase skinning skill by 5.'),
    Utility(25072, 'Enchant Gloves - Threat', 38885, 2613, (4, 31, 1024), 10,
            ((22448, 4), (22446, 2), (21886, 8)),
            'Permanently enchant gloves to increase threat from all attacks and spells by 2%.'),
    Utility(13933, 'Enchant Shield - Frost Resistance', 38843, 926, (4, 64, 0), 9,
            ((11178, 1), (3829, 1)),
            'Permanently enchant a shield to increase Frost resistance by 8.'),
    Utility(13464, 'Enchant Shield - Lesser Protection', 38791, 848, (4, 64, 0), 7,
            ((10998, 1), (10940, 1), (10978, 1)),
            'Permanently enchant a shield to increase armor by 30.'),
)


def use_spell(n: int) -> int:
    return USE_SPELL_BASE + n
