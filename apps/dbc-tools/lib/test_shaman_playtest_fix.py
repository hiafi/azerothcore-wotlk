"""
Shaman playtest fix pass (2026-10-22, .agents/plans/shaman-rework/shaman-rework.PLAYTEST-FIX-REPORT.md).

P1  base mana costs: Lightning Bolt 7 %, Elemental Blast 6 %, Frost Shock 4 % (the other shocks stay 6 %).
P3  Restoration talent moves (cells are pinned in test_shaman_s2a.GRID) and the bot links 7.2 / 7.5 re-encoded for them.
P4  the Undulating Currents Totem heal carries Chain Heal's SpellVisual (the beam).
(P2, the Ascendance transform removal and the ascend bursts, is pinned in test_shaman_s3a.)

Run: apps/dbc-tools/.venv/bin/python3 -m pytest apps/dbc-tools/lib/test_shaman_playtest_fix.py -q
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.test_shaman_s2a import GRID as RESTO_GRID  # noqa: E402
from lib.test_shaman_sh0b import _data as _shaman_data  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
BOT_CONF = REPO_ROOT / "modules" / "mod-playerbots" / "conf" / "playerbots.conf.dist"

# spell id -> ManaCostPct
BASE_COSTS = {403: 7, 202282: 6, 8056: 4, 8042: 6, 8050: 6}
CHAIN_HEAL_VISUAL = 3659          # Chain Heal 1064's SpellVisual: cast kit 3169 carries the beam
UCT_HEAL = 202663


def check_base_costs(rows: dict, costs=BASE_COSTS) -> list[str]:
    bad = []
    for sid, pct in costs.items():
        row = rows.get(sid)
        if row is None:
            bad.append(f"{sid}: no row")
        elif int(row.get("ManaCostPct") or 0) != pct or int(row.get("ManaCost") or 0):
            bad.append(f"{sid}: ManaCost {row.get('ManaCost')} / ManaCostPct {row.get('ManaCostPct')}, expected {pct} %")
    return bad


def check_uct_beam(rows: dict) -> list[str]:
    row = rows.get(UCT_HEAL)
    if row is None:
        return [f"{UCT_HEAL}: no row"]
    if int(row.get("SpellVisualID_1") or 0) != CHAIN_HEAL_VISUAL:
        return [f"{UCT_HEAL}: SpellVisualID_1 {row.get('SpellVisualID_1')}, expected Chain Heal's {CHAIN_HEAL_VISUAL}"]
    return []


def resto_cells():
    """Restoration tab order, row by row and left to right: [(tier, col, name, max ranks)]."""
    return [(t, c, name, len(ranks)) for (t, c), (name, ranks) in sorted(RESTO_GRID.items())]


def decode_link(link: str, cells=None) -> dict[str, int]:
    cells = cells or resto_cells()
    digits = [int(ch) for ch in link.lstrip("-")]
    return {name: d for (_t, _c, name, _m), d in zip(cells, digits)}


def check_link(link: str, points: int, cells=None) -> list[str]:
    """Every bought talent within its max rank, the points total, and each row gate (5 x tier points in the rows above)."""
    cells = cells or resto_cells()
    bought = decode_link(link, cells)
    bad = []
    if len(link.lstrip("-")) > len(cells):
        bad.append(f"{link}: longer than the tab's {len(cells)} talents")
    if sum(bought.values()) != points:
        bad.append(f"{link}: {sum(bought.values())} points, expected {points}")
    for tier, _col, name, maxrank in cells:
        d = bought.get(name, 0)
        if d > maxrank:
            bad.append(f"{link}: {name} rank {d} over its max {maxrank}")
        above = sum(bought.get(n, 0) for t, _c, n, _m in cells if t < tier)
        if d and above < 5 * tier:
            bad.append(f"{link}: {name} (row {tier}) needs {5 * tier} points above, has {above}")
    return bad


def check_nesting(links: list[str], cells=None) -> list[str]:
    bought = [decode_link(link, cells) for link in links]
    bad = []
    for i in range(len(bought) - 1):
        for name, d in bought[i].items():
            if d > bought[i + 1].get(name, 0):
                bad.append(f"link {i} has {name} {d}, the next link {bought[i + 1].get(name, 0)}")
    return bad


def _conf_links(text: str, slot: str) -> list[str]:
    return [re.search(rf"^Playerbots\.PremadeSpecLink\.{re.escape(slot)}\.{lv} = (\S+)$", text, re.M).group(1)
            for lv in (30, 45, 60, 80)]


class ShamanPlaytestFixTest(unittest.TestCase):
    def assertClean(self, problems):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_base_mana_costs(self):
        self.assertClean(check_base_costs(_shaman_data()["rows_by_id"]))

    def test_uct_heal_has_chain_heal_visual(self):
        self.assertClean(check_uct_beam(_shaman_data()["rows_by_id"]))

    def test_chain_heal_visual_is_chain_heals_own(self):
        rows = _shaman_data()["rows_by_id"]
        self.assertEqual(int(rows[1064]["SpellVisualID_1"]), CHAIN_HEAL_VISUAL)

    def test_resto_cells_are_the_moved_layout(self):
        cells = {(t, c): n for t, c, n, _m in resto_cells()}
        self.assertEqual(cells[(5, 1)], "Mana Tide Totem")
        self.assertEqual(cells[(3, 1)], "Tidal Force")
        self.assertEqual(cells[(6, 1)], "Spirit Link Totem")
        self.assertNotIn((2, 2), cells)
        self.assertNotIn((6, 2), cells)

    @unittest.skipUnless(BOT_CONF.is_file(), "mod-playerbots is not checked out")
    def test_bot_resto_links_are_legal_and_nested(self):
        text = BOT_CONF.read_text()
        for slot in ("7.2", "7.5"):
            links = _conf_links(text, slot)
            for link, pts in zip(links, (21, 36, 51, 51)):
                self.assertClean(check_link(link, pts))
            self.assertClean(check_nesting(links))

    def test_link_gate_negative(self):
        good = "--3020323121301"
        self.assertEqual(check_link(good, 21), [])
        self.assertEqual(len(check_link(good, 22)), 1)
        # Tidal Force (row 3) with only 14 points above it: drop one Totemic Focus point
        bought = decode_link(good)
        self.assertGreaterEqual(sum(v for n, v in bought.items() if n in {
            "Flowing Tides", "Improved Healing Wave", "Totemic Focus", "Improved Reincarnation", "Improved Healing Stream",
            "Tidal Focus", "Improved Water Shield", "Earthen Bulwark", "Ancestral Healing"}), 15)
        self.assertTrue(check_link("--3000323121301", 19))
        self.assertTrue(check_nesting(["--3020323121301", "--3010323121301"]))

    def test_cost_gate_negative(self):
        rows = {403: {"ManaCostPct": 10}, 202282: {"ManaCostPct": 6}, 8056: {"ManaCostPct": 4}, 8042: {"ManaCostPct": 6},
                8050: {"ManaCostPct": 6}}
        self.assertEqual(len(check_base_costs(rows)), 1)
        self.assertEqual(len(check_uct_beam({UCT_HEAL: {"SpellVisualID_1": 0}})), 1)


if __name__ == "__main__":
    unittest.main()
