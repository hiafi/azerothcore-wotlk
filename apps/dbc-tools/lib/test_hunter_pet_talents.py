"""
The hunter pet talent reference copies (source/classes/hunter/hunter_pet_talents.py, hunter-rework SHARED §C7.1,
T1 step 5): 3 tabs and 63 talents that resolve as unchanged against the live rows, so generate.py emits nothing
for them. Reads the real Talent/TalentTab state (base client DBC plus promoted migrations).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_hunter_pet_talents.py
"""

from __future__ import annotations

import sys
import unittest
from collections import Counter
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import build, dbcfmt, resolve, source, state  # noqa: E402
from lib.dsl import registry  # noqa: E402

PET_TALENTS = TOOL_ROOT / "source" / "classes" / "hunter" / "hunter_pet_talents.py"
HAVE_DBC = (state.BASE_DBC_DIR / dbcfmt.TALENT.dbc_filename).is_file()


@unittest.skipUnless(HAVE_DBC, "needs the extracted base Talent.dbc (var/extractors/dbc)")
class HunterPetTalentsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = registry.load_class_file(PET_TALENTS)
        cls.ids_cfg = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
        cls.existing_talents = state.load_existing_rows(dbcfmt.TALENT)
        cls.existing_tabs = state.load_existing_rows(dbcfmt.TALENTTAB)

    def test_three_tabs_and_63_talents(self):
        self.assertEqual(sorted(t["id"] for t in self.reg.tabs), [409, 410, 411])
        self.assertEqual(len(self.reg.talents), 63)
        per_tab = Counter(t["tab_id"] for t in self.reg.talents)
        self.assertEqual((per_tab[409], per_tab[410], per_tab[411]), (20, 21, 22))

    def test_tab_pet_masks_are_the_live_ones(self):
        self.assertEqual({t["id"]: t["pet_talent_mask"] for t in self.reg.tabs}, {409: 2, 410: 1, 411: 4})
        self.assertTrue(all(t["class_mask"] == 0 for t in self.reg.tabs))

    def test_no_skill_line_ability_is_derived(self):
        self.assertEqual(self.reg.skill_line_abilities, [])
        self.assertEqual(self.reg.spells, [])

    def test_all_66_rows_resolve_as_unchanged(self):
        talents = resolve.resolve_rows(
            self.reg.talents, self.ids_cfg["talent"], self.existing_talents, build.build_talent_row,
        )
        tabs = resolve.resolve_rows(
            self.reg.tabs, self.ids_cfg["talenttab"], self.existing_tabs, build.build_talenttab_row,
        )
        self.assertEqual(talents.edited_ids, [])
        self.assertEqual(tabs.edited_ids, [])
        self.assertEqual((talents.unchanged, tabs.unchanged), (63, 3))
        self.assertEqual((talents.entries, tabs.entries), ([], []))

    def test_unchanged_against_the_pure_stock_baseline_too(self):
        # The client-patch pass compares against stock rows, not the promoted-aware state.
        talents = resolve.resolve_rows(
            self.reg.talents, self.ids_cfg["talent"], state.load_stock_rows(dbcfmt.TALENT), build.build_talent_row,
        )
        tabs = resolve.resolve_rows(
            self.reg.tabs, self.ids_cfg["talenttab"], state.load_stock_rows(dbcfmt.TALENTTAB),
            build.build_talenttab_row,
        )
        self.assertEqual((talents.edited_ids, tabs.edited_ids), ([], []))


if __name__ == "__main__":
    unittest.main()
