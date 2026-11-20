"""
Blackrock Depths build F-1a (R-1-KIT n1, R-1-B n5): the three Finder section starts agree three ways.

The starts of sections 2-4 live in three places that nothing else ties together:
  - C++: `kSections` in modules/mod-dungeon-bosses/src/BlackrockDepths/BlackrockDepthsRework.h (the instance's gallery
    stand-down reads section 2's start; `.dbtest brd section`);
  - dbc-tools: the lfg_dungeon_template positions in source/world/lfg_classic_sections.py (308, 309, 276);
  - the checkpoint rows (map 230, location_index 1-3) in modules/mod-dungeon-checkpoint/data/sql/db-world/
    u_dungeon_checkpoint_2026_11_17_00.sql, with the later files' UPDATEs on top (_2026_11_18_00 moved section 2's
    start to the Ring gallery, S2g).
Each start must be the same x, y, z and orientation in all three (to 0.01).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_finder_starts.py
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
HEADER = REPO_ROOT / "modules/mod-dungeon-bosses/src/BlackrockDepths/BlackrockDepthsRework.h"
SECTIONS = TOOL_ROOT / "source/world/lfg_classic_sections.py"
CHECKPOINT_DIR = REPO_ROOT / "modules/mod-dungeon-checkpoint/data/sql/db-world"
CHECKPOINT = CHECKPOINT_DIR / "u_dungeon_checkpoint_2026_11_17_00.sql"

_NUM = r"(-?\d+(?:\.\d+)?)f?"


def _header_starts() -> dict[int, tuple[float, ...]]:
    """lfgNormal -> (x, y, z, o) from kSections."""
    text = HEADER.read_text()
    block = text[text.index("kSections{"):]
    block = block[:block.index("} };")]
    out = {}
    for m in re.finditer(r"\{\s*(\d),\s*\"[^\"]+\",\s*(\d+),\s*(\d+),\s*\{\s*" + r",\s*".join([_NUM] * 4) + r"\s*\}",
                         block):
        out[int(m.group(2))] = tuple(float(m.group(i)) for i in range(4, 8))
    return out


def _finder_starts() -> dict[int, tuple[float, ...]]:
    """LFG id -> (x, y, z, o) from the lfg_dungeon / lfg_override calls."""
    text = SECTIONS.read_text()
    out = {}
    for m in re.finditer(r"lfg_(?:dungeon|override)\(\s*(\d+),[^()]*?position=\(" + r",\s*".join([_NUM] * 4) + r"\)",
                         text, re.S):
        out[int(m.group(1))] = tuple(float(m.group(i)) for i in range(2, 6))
    return out


def _checkpoint_starts() -> dict[int, tuple[float, ...]]:
    """location_index -> (x, y, z, o) of the map 230 entrance-type rows."""
    text = CHECKPOINT.read_text()
    out = {}
    for m in re.finditer(r"\(230,\s*0,\s*(\d),\s*0,\s*" + r",\s*".join([_NUM] * 4), text):
        out[int(m.group(1))] = tuple(float(m.group(i)) for i in range(2, 6))
    # Later files move a start with an UPDATE of the four columns (applied in file-name order, as db-import does).
    update = re.compile(r"UPDATE `dungeon_checkpoint_location`\s+SET `position_x` = " + _NUM
                        + r", `position_y` = " + _NUM + r", `position_z` = " + _NUM + r", `orientation` = " + _NUM
                        + r"[^;]*?WHERE `map_id` = 230 AND `creature_entry` = 0 AND `location_index` = (\d)", re.S)
    for path in sorted(CHECKPOINT_DIR.glob("u_dungeon_checkpoint_*.sql")):
        if path.name <= CHECKPOINT.name:
            continue
        for m in update.finditer(path.read_text()):
            out[int(m.group(5))] = tuple(float(m.group(i)) for i in range(1, 5))
    return out


class FinderStartsTest(unittest.TestCase):
    def test_the_three_sources_agree(self):
        header = _header_starts()
        finder = _finder_starts()
        checkpoint = _checkpoint_starts()
        self.assertEqual(sorted(header), [30, 276, 308, 309])
        for index, lfg in ((1, 308), (2, 309), (3, 276)):
            with self.subTest(lfg=lfg):
                self.assertIn(lfg, finder)
                self.assertIn(index, checkpoint)
                for a, b, c in zip(header[lfg], finder[lfg], checkpoint[index]):
                    self.assertAlmostEqual(a, b, delta=0.01)
                    self.assertAlmostEqual(a, c, delta=0.01)


if __name__ == "__main__":
    unittest.main()
