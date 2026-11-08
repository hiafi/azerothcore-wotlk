"""
Shadowfang Keep build WP-S10, Arugal's hard mode "Face Him Alone": the data half of the whole path, against its C++
(modules/mod-dungeon-bosses src/ShadowfangKeep/FaceHimAloneLogic.h, face_him_alone.cpp).

The path: the prisoner's gossip lights DATA_HARD_MODE (C++), the prisoner says line 7 and leaves (S9's text rows),
the instance adds LOOT_MODE_HARD_MODE_1 to Arugal, and his heroic body (310051) rolls its own lootid, whose group 2
holds the hard mode items at LootMode 2 (WP-L). Checks:
  - S10 declares nothing (no spell, creature or text of its own); its slice 206085-206089 is free in the package;
  - Arugal's heroic body: the override's lootid and health are the ids and numbers the C++ header names, and when the
    heroic id is minted (heroic_ids.lock) it is 310051;
  - the loot: group 2 of 310051 is the only LootMode 2 group, holds the three hard mode items at the heroic_hm tier,
    and no loot on Arugal's normal lootid (4275) has the hard mode bit, so a normal kill never drops them;
  - the prisoner's line 7 exists for both lair copies (the SK lines), and no gossip_menu_option row sits on their menus
    (the option is C++, so its action id cannot collide).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_shadowfang_keep_face_him_alone.py
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import heroic_templates, source  # noqa: E402
from lib import test_shadowfang_keep_arugal as arugal_test  # noqa: E402
from lib.dsl import items as D  # noqa: E402
from lib.dsl import loot as L  # noqa: E402
from lib.dsl import registry  # noqa: E402

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "ShadowfangKeep"
HEADER = MODULE_DIR / "FaceHimAloneLogic.h"
SCRIPT = MODULE_DIR / "face_him_alone.cpp"
MY_FILE = TOOL_ROOT / "source" / "npcs" / "shadowfang_keep" / "face_him_alone.py"
SQL_DIR = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world"
IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")

S10_SLICE = range(206085, 206090)
ARUGAL, ARUGAL_HEROIC = 4275, 310051
ASHCROMBE, ADAMANT = 300513, 300514
HARD_MODE_ITEMS = {"sfk_vial_of_the_worgens_curse", "sfk_arugals_shadow_tome", "sfk_ashcrombes_locket"}
LINES = {
    ASHCROMBE: "Then may the Kirin Tor watch over you.",
    ADAMANT: "Your funeral. Try not to come back as a dog.",
}


def _header_int(name: str) -> int:
    m = re.search(rf"\b{name}\s*=\s*(\d+)", HEADER.read_text(encoding="utf-8"))
    if not m:
        raise AssertionError(f"{name} not found in {HEADER.name}")
    return int(m.group(1))


class FaceHimAloneDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        merged = D.load_items_dir(TOOL_ROOT / "source" / "items")
        cls.loot = [e["_decl"] for e in merged["loot_declarations"] if not e["_decl"].removal]
        reg = registry.load_class_package(TOOL_ROOT / "source" / "world" / "dungeons", ids_cfg=IDS)
        sfk = {e["map_id"]: e for e in reg.dungeons}[33]
        cls.overrides = {entry: dict(pairs) for entry, pairs in sfk["heroic"]["overrides"]}
        cls.sql = "\n".join(p.read_text(encoding="utf-8") for p in sorted(SQL_DIR.glob("*.sql")))

    def test_s10_declares_nothing_and_its_slice_is_free(self):
        text = MY_FILE.read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"^\s*(spell|creature_template|creature_text|aura)\w*\(", text, re.M))
        reg = arugal_test._load()  # the whole source/npcs/shadowfang_keep package, as S9's test loads it
        self.assertEqual(sorted(int(e["id"]) for e in reg.spells if int(e["id"]) in S10_SLICE), [])
        # The header names the slice and declares no spell id.
        self.assertIsNone(re.search(r"\bSPELL_\w+\s*=\s*\d+", HEADER.read_text(encoding="utf-8")))

    def test_arugals_heroic_body_matches_the_header(self):
        arugal = self.overrides[ARUGAL]
        self.assertEqual(_header_int("kArugalHeroicEntry"), ARUGAL_HEROIC)
        self.assertEqual(dict(arugal["columns"])["lootid"], ARUGAL_HEROIC)
        self.assertEqual(arugal["health"], _header_int("kArugalHeroicHealth"))
        pairs = dict(heroic_templates.parse_lock(heroic_templates.LOCK_PATH.read_text()).pairs)
        if ARUGAL in pairs:  # minted by the write run (WP-L's note): the lootid is the body's own entry
            self.assertEqual(pairs[ARUGAL], ARUGAL_HEROIC)

    def test_the_hard_mode_group_drops_only_on_a_hard_mode_kill(self):
        hard_mode = L.LOOT_MODE_HARD_MODE_1
        self.assertEqual(hard_mode, _header_int("kLootModeHardMode"))
        group = [d for d in self.loot if d.lootid == ARUGAL_HEROIC and d.group == _header_int("kHardModeLootGroup")]
        self.assertEqual(len(group), 1)
        self.assertEqual((group[0].loot_mode, group[0].tier), (hard_mode, "heroic_hm"))
        self.assertEqual(set(group[0].items), HARD_MODE_ITEMS)
        # Nothing else on either of Arugal's lootids carries the hard mode bit: a kill without the flag (normal map,
        # or heroic without the choice) never rolls them.
        others = [d for d in self.loot if d.lootid in (ARUGAL, ARUGAL_HEROIC) and d is not group[0]]
        self.assertTrue(others)
        for d in others:
            self.assertFalse(d.loot_mode & hard_mode, (d.lootid, d.group))
            self.assertFalse(set(d.items) & HARD_MODE_ITEMS, (d.lootid, d.group))
        self.assertFalse(any(d.loot_mode & hard_mode for d in self.loot if d.lootid == ARUGAL))

    def test_the_prisoners_hard_mode_line_and_no_db_option(self):
        for entry, line in LINES.items():
            row = re.search(rf"\({entry}, 7, 0, '([^']*(?:''[^']*)*)'", self.sql)
            self.assertIsNotNone(row, entry)
            self.assertEqual(row.group(1).replace("''", "'"), line)
        for menu in (ASHCROMBE, ADAMANT):
            self.assertIsNone(re.search(rf"INSERT INTO `gossip_menu_option`[^;]*\({menu},", self.sql), menu)
        cpp = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("SfkLairPrisoner::SetGossipHooks", cpp)
        self.assertIn("SfkLairPrisoner::LeaveForHardMode", cpp)
        self.assertIn("DATA_HARD_MODE, 1", cpp)


if __name__ == "__main__":
    unittest.main()
