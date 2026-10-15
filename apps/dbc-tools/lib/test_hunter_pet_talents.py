"""
The reworked hunter pet talent tree (source/classes/hunter/hunter_pet_talents.py, hunter-rework PET.md
sections 7.1-7.3 and 9.6): 3 tabs of 11 talents each at identical positions, 30 stock rows retired through
retire_talent(). Reads the real Talent/TalentTab state (base client DBC plus promoted migrations).

Each rule is a plain function over the declared entries, and every rule has a negative fixture that must trip it.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_hunter_pet_talents.py
"""

from __future__ import annotations

import copy
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


# Rank-spell tuple -> talent name (PET 7.1). Ranks are shared across the three tabs.
NAME_BY_RANKS = {
    (61686, 61687, 61688): "GS",
    (61689, 61690): "NA",
    (53203, 53204, 53205): "SB",
    (53481, 53482): "BotR",
    (53175, 53176): "PB",
    (19596, 201750, 201751): "BS",
    (53409, 53411): "LH",
    (53427, 53429, 53430): "GR",
    (53450, 53451): "GotM",
    (53483, 53485): "Mob",
    (53186, 53187): "BT",
}
POSITIONS = {
    "GS": (0, 0), "NA": (0, 1), "SB": (0, 2), "BotR": (1, 0), "PB": (1, 1), "BS": (1, 2),
    "LH": (2, 0), "GR": (2, 1), "GotM": (3, 0), "Mob": (3, 1), "BT": (4, 0),
}
LINK_ORDER = ["GS", "NA", "SB", "BotR", "PB", "BS", "LH", "GR", "GotM", "Mob", "BT"]
RANK_COUNTS = [3, 2, 3, 2, 2, 3, 2, 3, 2, 2, 2]
RETIRED = {
    409: [2110, 2123, 2277, 2171, 2170, 2172, 2169, 2258, 2255],
    410: [2109, 2203, 2111, 2219, 2156, 2155, 2153, 2157, 2254, 2253],
    411: [2119, 2201, 2208, 2206, 2177, 2183, 2181, 2184, 2175, 2256, 2278],
}
RETIRED_IDS = sorted(i for ids in RETIRED.values() for i in ids)
BOT_FILTER_IDS = {2109, 2111, 2119, 2201, 2203, 2207, 2208, 2219}
REPURPOSED_IDS = {2114, 2237, 2126, 2107, 2124, 2125, 2106, 2118, 2182, 2127, 2166}


def kept(talents: list[dict]) -> list[dict]:
    """The talent() entries (retire_talent() entries sit on the holding tab)."""
    return [t for t in talents if t["tab_id"] != registry.RETIRED_TAB_ID]


def name_of(t: dict) -> str | None:
    return NAME_BY_RANKS.get(tuple(t.get("rank_spell_ids") or ()))


def check_layout(talents: list[dict]) -> list[str]:
    """11 talents per tab; the same (tier, column) -> name map on all three (PET 7.1)."""
    problems = []
    for tab_id in (409, 410, 411):
        rows = [t for t in kept(talents) if t["tab_id"] == tab_id]
        if len(rows) != 11:
            problems.append(f"tab {tab_id} has {len(rows)} talents, not 11")
        got = {(t["tier"], t["column"]): name_of(t) for t in rows}
        want = {pos: name for name, pos in POSITIONS.items()}
        if got != want:
            problems.append(f"tab {tab_id} layout {got} != {want}")
    return problems


def check_points(talents: list[dict]) -> list[str]:
    """Rank counts in link order 3/2/3/2/2/3/2/3/2/2/2, 26 per tab, row totals 8/7/5/4/2, row 5 empty."""
    problems = []
    for tab_id in (409, 410, 411):
        rows = sorted((t for t in kept(talents) if t["tab_id"] == tab_id), key=lambda t: (t["tier"], t["column"]))
        counts = [len(t["rank_spell_ids"]) for t in rows]
        if counts != RANK_COUNTS:
            problems.append(f"tab {tab_id} rank counts {counts} != {RANK_COUNTS}")
        if sum(counts) != 26:
            problems.append(f"tab {tab_id} has {sum(counts)} points, not 26")
        totals = Counter()
        for t in rows:
            totals[t["tier"]] += len(t["rank_spell_ids"])
        if [totals[r] for r in range(6)] != [8, 7, 5, 4, 2, 0]:
            problems.append(f"tab {tab_id} row totals {[totals[r] for r in range(6)]}")
    return problems


def check_clean(talents: list[dict]) -> list[str]:
    """No prereqs, Flags 0, CategoryMask 0 on every kept talent."""
    problems = []
    for t in kept(talents):
        raw = t.get("raw_overrides") or {}
        if t.get("depends_on"):
            problems.append(f"{t['id']} has a prerequisite")
        if t.get("flags"):
            problems.append(f"{t['id']} has Flags {t['flags']}")
        for key in ("CategoryMask_1", "CategoryMask_2"):
            if raw.get(key):
                problems.append(f"{t['id']} has {key} {raw[key]}")
    return problems


def check_retired(talents: list[dict], retired: list[dict]) -> list[str]:
    """The 30 retired ids go through retire_talent() and are never also declared as talent()."""
    problems = []
    ids = sorted(r["id"] for r in retired)
    if ids != RETIRED_IDS:
        problems.append(f"retired ids {ids} != {RETIRED_IDS}")
    both = {t["id"] for t in kept(talents)} & set(ids)
    if both:
        problems.append(f"ids both retired and talent(): {sorted(both)}")
    return problems


def check_bot_filter(talents: list[dict], repurposed: set[int] = frozenset(REPURPOSED_IDS)) -> list[str]:
    """No repurposed id is one of mod-playerbots' Dash/Dive filter ids (2207 is a kept row, not repurposed)."""
    return [
        f"repurposed id {t['id']} is a bot filter id"
        for t in kept(talents) if t["id"] in repurposed and t["id"] in BOT_FILTER_IDS
    ]


def check_link_order(talents: list[dict]) -> list[str]:
    """Sorted by (row, column) every tab reads GS, NA, SB, BotR, PB, BS, LH, GR, GotM, Mob, BT (PET 9.6)."""
    problems = []
    for tab_id in (409, 410, 411):
        rows = sorted((t for t in kept(talents) if t["tab_id"] == tab_id), key=lambda t: (t["tier"], t["column"]))
        order = [name_of(t) for t in rows]
        if order != LINK_ORDER:
            problems.append(f"tab {tab_id} link order {order}")
    return problems


@unittest.skipUnless(HAVE_DBC, "needs the extracted base Talent.dbc (var/extractors/dbc)")
class HunterPetTalentsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ids_cfg = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
        cls.existing_talents = state.load_existing_rows(dbcfmt.TALENT)
        cls.existing_tabs = state.load_existing_rows(dbcfmt.TALENTTAB)
        cls.reg = registry.load_class_file(PET_TALENTS, live_data={"talent_rows": cls.existing_talents})

    def fresh(self) -> list[dict]:
        return copy.deepcopy(self.reg.talents)

    def test_three_tabs_and_33_talents_plus_30_retired(self):
        self.assertEqual(sorted(t["id"] for t in self.reg.tabs), [409, 410, 411])
        self.assertEqual(len(kept(self.reg.talents)), 33)
        self.assertEqual(len(self.reg.talents), 63)
        self.assertEqual(len({t["id"] for t in self.reg.talents}), 63)

    def test_tab_pet_masks_are_the_live_ones(self):
        self.assertEqual({t["id"]: t["pet_talent_mask"] for t in self.reg.tabs}, {409: 2, 410: 1, 411: 4})
        self.assertTrue(all(t["class_mask"] == 0 for t in self.reg.tabs))

    def test_no_skill_line_ability_is_derived(self):
        self.assertEqual(self.reg.skill_line_abilities, [])
        self.assertEqual(self.reg.spells, [])

    def test_tabs_resolve_unchanged(self):
        tabs = resolve.resolve_rows(
            self.reg.tabs, self.ids_cfg["talenttab"], self.existing_tabs, build.build_talenttab_row,
        )
        self.assertEqual(tabs.edited_ids, [])
        self.assertEqual((tabs.unchanged, tabs.entries), (3, []))

    def test_layout(self):
        self.assertEqual(check_layout(self.fresh()), [])
        bad = self.fresh()
        next(t for t in bad if t["id"] == 2116)["column"] = 3
        self.assertTrue(check_layout(bad))
        short = [t for t in self.fresh() if t["id"] != 2112]
        self.assertTrue(check_layout(short))

    def test_points(self):
        self.assertEqual(check_points(self.fresh()), [])
        bad = self.fresh()
        next(t for t in bad if t["id"] == 2128)["rank_spell_ids"] = [53186]
        self.assertTrue(check_points(bad))
        row5 = self.fresh()
        next(t for t in row5 if t["id"] == 2128)["tier"] = 5
        self.assertTrue(check_points(row5))

    def test_boars_speed_ranks(self):
        for t in kept(self.reg.talents):
            if (t["tier"], t["column"]) == (1, 2):
                self.assertEqual(t["rank_spell_ids"], [19596, 201750, 201751])

    def test_clean(self):
        self.assertEqual(check_clean(self.fresh()), [])
        for mutate in (
            lambda t: t.__setitem__("depends_on", {"talent_id": 2116, "rank": 1}),
            lambda t: t.__setitem__("flags", 1),
            lambda t: t.__setitem__("raw_overrides", {"CategoryMask_1": 212992}),
            lambda t: t.__setitem__("raw_overrides", {"CategoryMask_2": 2147483648}),
        ):
            bad = self.fresh()
            mutate(next(t for t in bad if t["id"] == 2207))
            self.assertTrue(check_clean(bad))

    def test_retired(self):
        self.assertEqual(check_retired(self.reg.talents, self.reg.retired_talents), [])
        self.assertTrue(all(
            t["tab_id"] == registry.RETIRED_TAB_ID for t in self.reg.talents if t["id"] in RETIRED_IDS
        ))
        # negative: one id missing from the retirements; one id declared both ways
        self.assertTrue(check_retired(self.reg.talents, self.reg.retired_talents[1:]))
        both = self.fresh() + [{"id": 2110, "tab_id": 409, "tier": 0, "column": 0}]
        self.assertTrue(check_retired(both, self.reg.retired_talents))

    def test_no_repurposed_id_is_a_bot_filter_id(self):
        self.assertEqual(check_bot_filter(self.fresh()), [])
        self.assertTrue(set(REPURPOSED_IDS).isdisjoint(BOT_FILTER_IDS))
        self.assertTrue(check_bot_filter(self.fresh(), REPURPOSED_IDS | {2207}))

    def test_link_order(self):
        self.assertEqual(check_link_order(self.fresh()), [])
        bad = self.fresh()
        a = next(t for t in bad if t["id"] == 2116)
        b = next(t for t in bad if t["id"] == 2117)
        a["column"], b["column"] = b["column"], a["column"]
        self.assertTrue(check_link_order(bad))


if __name__ == "__main__":
    unittest.main()
