"""
`budget.materialized_item_fields` leaves out stat lines of value 0, like the C++ `ApplyItemizationAllocation`
(ItemBudget.cpp): an allocation that rounds to 0 and a 0 Stamina line are skipped and the later lines move up, so the
client never prints a "+0 <stat>" line (item variants R1 S6). A weapon's off-budget Spell Power line (weapon scaling
WS0c, `weapon_spell_power`) comes after Stamina, as the C++ writes it, and only when above 0.

    apps/dbc-tools/.venv/bin/python3 -m unittest discover -s apps/item-tools/tests
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from item_lib import budget  # noqa: E402

AGILITY, CRIT, HASTE, MP5 = 3, 32, 36, 43


def _breakdown(allocations, stamina, weapon_spell_power=0):
    return {
        "weapon_spell_power": weapon_spell_power,
        "allocations": [{"stat_type": stat, "rounded": value} for stat, value in allocations],
        "final_stamina": stamina,
        "has_armor_curve": False,
        "has_block_value_curve": False,
        "is_weapon": False,
    }


def _lines(fields):
    return [(fields[f"stat_type{n}"], fields[f"stat_value{n}"]) for n in range(1, budget.MAX_ITEM_PROTO_STATS + 1)]


class ZeroLinesTest(unittest.TestCase):
    def test_zero_allocations_are_skipped_and_later_lines_move_up(self):
        fields = budget.materialized_item_fields(_breakdown([(AGILITY, 7), (MP5, 0), (HASTE, 0), (CRIT, 3)], 9))
        lines = _lines(fields)
        self.assertEqual(lines[:3], [(AGILITY, 7), (CRIT, 3), (budget.ITEM_MOD_STAMINA, 9)])
        self.assertEqual(lines[3:], [(0, 0)] * (budget.MAX_ITEM_PROTO_STATS - 3))

    def test_zero_stamina_is_skipped(self):
        lines = _lines(budget.materialized_item_fields(_breakdown([(CRIT, 4)], 0)))
        self.assertEqual(lines[0], (CRIT, 4))
        self.assertEqual(lines[1:], [(0, 0)] * (budget.MAX_ITEM_PROTO_STATS - 1))

    def test_no_zero_line_keeps_every_line(self):
        lines = _lines(budget.materialized_item_fields(_breakdown([(AGILITY, 5), (CRIT, 2)], 6)))
        self.assertEqual(lines[:3], [(AGILITY, 5), (CRIT, 2), (budget.ITEM_MOD_STAMINA, 6)])

    def test_every_line_zero_clears_all_slots(self):
        lines = _lines(budget.materialized_item_fields(_breakdown([(MP5, 0)], 0)))
        self.assertEqual(lines, [(0, 0)] * budget.MAX_ITEM_PROTO_STATS)

    def test_weapon_spell_power_line_follows_stamina(self):
        lines = _lines(budget.materialized_item_fields(_breakdown([(AGILITY, 5), (MP5, 0), (CRIT, 2)], 6, 98)))
        self.assertEqual(lines[:4], [(AGILITY, 5), (CRIT, 2), (budget.ITEM_MOD_STAMINA, 6),
                                     (budget.ITEM_MOD_SPELL_POWER, 98)])
        lines = _lines(budget.materialized_item_fields(_breakdown([(CRIT, 2)], 0, 40)))
        self.assertEqual(lines[:2], [(CRIT, 2), (budget.ITEM_MOD_SPELL_POWER, 40)])

    def test_no_weapon_spell_power_line_at_zero(self):
        lines = _lines(budget.materialized_item_fields(_breakdown([(CRIT, 2)], 6, 0)))
        self.assertEqual(lines[2:], [(0, 0)] * (budget.MAX_ITEM_PROTO_STATS - 2))

    def test_no_slot_left_for_the_line(self):
        allocations = [(CRIT, 1)] * (budget.MAX_ITEM_PROTO_STATS - 1)
        with self.assertRaises(budget.BudgetError):
            budget.materialized_item_fields(_breakdown(allocations, 6, 50))

    def test_slots_counted_like_the_server(self):
        # ItemBudget.cpp counts every allocation (zero ones too), Stamina (even 0) and the Spell Power line before it
        # drops zero lines, and skips the item above 10; a save must refuse what the server would skip.
        nine = [(AGILITY, 5)] * 8 + [(MP5, 0)]
        self.assertEqual(budget.stat_line_count(_breakdown(nine, 0, 40)), 11)
        with self.assertRaisesRegex(budget.BudgetError, "the server would skip the item"):
            budget.materialized_item_fields(_breakdown(nine, 0, 40))  # 8 real lines + SP would fit after the drop
        ten = [(AGILITY, 5)] * 9 + [(MP5, 0)]
        with self.assertRaises(budget.BudgetError):
            budget.materialized_item_fields(_breakdown(ten, 6))  # the Stamina gap that predates weapon scaling
        self.assertEqual(budget.stat_line_count(_breakdown(nine, 6)), 10)
        lines = _lines(budget.materialized_item_fields(_breakdown(nine, 6)))
        self.assertEqual(lines[8], (budget.ITEM_MOD_STAMINA, 6))


if __name__ == "__main__":
    unittest.main()
