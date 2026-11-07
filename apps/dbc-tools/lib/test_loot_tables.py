"""
Item variants IV7 (.agents/plans/item-variants/item-variants.PLAN.md s7.3): the boss loot DSL (lib/dsl/loot.py) and
its rows, rules and rendering (lib/loot_tables.py).

Covered: the DSL's argument checks and one declaration per (lootid, group); the rows (Chance 0 equal chance, one
group per list, the Normal tier on a normal lootid and the Heroic tier on a heroic one, a picks=2 list as one
reference row x2 into a pool, a hard mode group with LootMode 2); the rules (a wrong tier for the difficulty, a hard
mode group with bit 1 or without a default list, a heroic row whose lootid is not its own, a reference outside the
block or reused, a pool of unequippable items, a generic pool or foreign row a declared group would drop, a list item
also in another group, an unowned reference entry in the block); rendering (DELETE + INSERT per changed group, a
removal as a lone DELETE) and a rerun after replaying the rendered SQL emits nothing; an engine model of LootMgr's
group roll (each list drops exactly one item at equal chance, Sneed's pool two distinct items, the hard mode item only
with the loot mode bit); and the real source/items/deadmines_loot.py declarations.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_loot_tables.py
"""

from __future__ import annotations

import random
import sys
import unittest
from collections import Counter
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import item_variants, loot_tables, sql_dump  # noqa: E402
from lib.dsl import items as D  # noqa: E402
from lib.dsl import loot as L  # noqa: E402
from lib.dsl import registry  # noqa: E402

IDS_CFG = {"loot_reference": {"start": 1700000, "end": 1700999}}
DUNGEON = D.ladder(
    "vanilla_dungeon",
    normal=D.tier(step=0, label="Normal"),
    heroic=D.tier(step=1, ilvl=66, quality=D.Quality.EPIC, required_level=60, heroic_flag=True, label="Heroic"),
    empowered_1=D.tier(step=2, ilvl=76, quality=D.Quality.EPIC, required_level=60, label="Molten Empowered"),
)
HARD_MODE = D.ladder(
    "vanilla_hard_mode",
    heroic_hm=D.tier(step=1, ilvl=71, quality=D.Quality.EPIC, required_level=60, label="Heroic Hard Mode"),
    empowered_1_hm=D.tier(
        step=2, ilvl=81, quality=D.Quality.EPIC, required_level=60, label="Molten Empowered Hard Mode",
    ),
)
HEROIC_PAIRS = {644: 310008, 643: 310007, 639: 310004}
NEXT_ID = [71000]


def _item(key: str, *, base: int | None = None, ladder=DUNGEON, inventory_type: int = 13) -> item_variants.ResolvedItem:
    decl = D.item(key, base=base, name=None if base else key.title(), ladder=ladder, primary="Strength (Solo)",
                  **({} if base else {"like": 1, **({"ilvl": 20} if ladder.tiers[0].ilvl is None else {})}))
    item = item_variants.ResolvedItem(
        decl=decl, source_row={"name": f"Stock {key}"} if base else {}, like_columns={},
        inventory_type=inventory_type, item_class=2, subclass=0, sockets=(),
    )
    for number, spec in enumerate(ladder.tiers):
        if base is not None and number == 0:
            entry = base
        else:
            entry = NEXT_ID[0]
            NEXT_ID[0] += 1
        item.tiers.append(item_variants.ResolvedTier(
            key=key, tier=spec.name, label=spec.label, entry=entry, stock=base is not None and entry == base,
            ilvl=spec.ilvl or 20, quality=spec.quality or 3, required_level=spec.required_level or 15,
            heroic_flag=spec.heroic_flag, variant_base=None, itemization={}, columns={}, number=number,
        ))
    return item


def _expansion(*items: item_variants.ResolvedItem) -> item_variants.ItemExpansion:
    return item_variants.ItemExpansion(items=list(items))


def _creatures(**lootids) -> dict[int, dict]:
    rows = {
        644: {"entry": 644, "name": "Rhahk'Zor", "lootid": 644},
        643: {"entry": 643, "name": "Sneed", "lootid": 643},
        639: {"entry": 639, "name": "Edwin VanCleef", "lootid": 639},
        310008: {"entry": 310008, "name": "Rhahk'Zor", "lootid": 310008},
        310007: {"entry": 310007, "name": "Sneed", "lootid": 310007},
        310004: {"entry": 310004, "name": "Edwin VanCleef", "lootid": 310004},
    }
    for entry, lootid in lootids.items():
        rows[int(entry.lstrip("e"))]["lootid"] = lootid
    return rows


def _declare(*calls) -> list[dict]:
    """Runs boss_loot()/remove_loot_group() calls under an active registry; returns its loot declarations."""
    reg = registry.Registry()
    registry._active = reg
    try:
        for fn, args, kwargs in calls:
            fn(*args, **kwargs)
    finally:
        registry._active = None
    return reg.loot_declarations


def _build(decls, expansion, creatures=None, strict=True) -> loot_tables.LootPlan:
    return loot_tables.build(decls, expansion, ids_cfg=IDS_CFG, heroic_pairs=HEROIC_PAIRS,
                             creature_rows=creatures or _creatures(), strict_lootid=strict)


def _row(entry, item, group=1, chance=0.0, reference=0, loot_mode=1, max_count=1, comment="stock"):
    return {"Entry": entry, "Item": item, "Reference": reference, "Chance": chance, "QuestRequired": 0,
            "LootMode": loot_mode, "GroupId": group, "MinCount": max_count if reference else 1, "MaxCount": max_count, "Comment": comment}


class DslTest(unittest.TestCase):
    def test_argument_checks(self):
        bad = [
            dict(args=(644, ("a",)), kwargs=dict(tier="normal", group=0)),
            dict(args=(644, ("a",)), kwargs=dict(tier="normal", group=128)),
            dict(args=(0, ("a",)), kwargs=dict(tier="normal")),
            dict(args=(644, ()), kwargs=dict(tier="normal")),
            dict(args=(644, "a"), kwargs=dict(tier="normal")),
            dict(args=(644, ("a", "a")), kwargs=dict(tier="normal")),
            dict(args=(644, ("a", "b")), kwargs=dict(tier="")),
            dict(args=(644, ("a", "b")), kwargs=dict(tier="normal", picks=2)),
            dict(args=(644, ("a", "b")), kwargs=dict(tier="normal", picks=3, reference=1700000)),
            dict(args=(644, ("a", "b")), kwargs=dict(tier="normal", reference=1700000)),
            dict(args=(644, ("a",)), kwargs=dict(tier="normal", loot_mode=0)),
        ]
        for case in bad:
            with self.subTest(case=case), self.assertRaises(L.LootDeclarationError):
                L.boss_loot(*case["args"], **case["kwargs"])
        with self.assertRaises(L.LootDeclarationError):
            L.remove_loot_group(642, group=1, why=" ")
        with self.assertRaises(L.LootDeclarationError):
            L.remove_loot_group(642, group=0, why="x")

    def test_one_declaration_per_group(self):
        with self.assertRaises(registry.DuplicateIdError):
            _declare(
                (L.boss_loot, (644, ("a",)), dict(tier="normal")),
                (L.remove_loot_group, (644,), dict(group=1, why="x")),
            )
        decls = _declare(
            (L.boss_loot, (644, ("a",)), dict(tier="normal")),
            (L.boss_loot, (644, ("b",)), dict(tier="normal", group=2)),
        )
        self.assertEqual([d["id"] for d in decls], [("loot", 644, 1), ("loot", 644, 2)])


class BuildTest(unittest.TestCase):
    def setUp(self):
        self.hammer = _item("dm_hammer", base=5187)
        self.girdle = _item("dm_girdle")
        self.blade = _item("dm_blade", base=2169)
        self.saw = _item("dm_saw", base=1937)
        self.fuse = _item("dm_fuse", ladder=HARD_MODE, inventory_type=12)
        self.exp = _expansion(self.hammer, self.girdle, self.blade, self.saw, self.fuse)

    def entry(self, item, tier):
        return next(t.entry for t in item.tiers if t.tier == tier)

    def test_equal_chance_one_group_per_tier(self):
        plan = _build(_declare(
            (L.boss_loot, (644, ("dm_hammer", "dm_girdle")), dict(tier="normal")),
            (L.boss_loot, (310008, ("dm_hammer", "dm_girdle")), dict(tier="heroic")),
        ), self.exp)
        self.assertEqual(plan.errors, [])
        normal, heroic = plan.groups[(644, 1)], plan.groups[(310008, 1)]
        self.assertEqual([r["Item"] for r in normal], [5187, self.entry(self.girdle, "normal")])
        self.assertEqual([r["Item"] for r in heroic], [self.entry(self.hammer, "heroic"),
                                                       self.entry(self.girdle, "heroic")])
        for row in normal + heroic:
            self.assertEqual((row["Chance"], row["GroupId"], row["MinCount"], row["MaxCount"], row["LootMode"],
                              row["Reference"], row["QuestRequired"]), (0, 1, 1, 1, 1, 0, 0))
        self.assertEqual(normal[0]["Comment"], "Rhahk'Zor - Stock dm_hammer (Normal)")
        self.assertEqual(heroic[1]["Comment"], "Rhahk'Zor - Dm_Girdle (Heroic)")

    def test_tier_must_match_difficulty(self):
        plan = _build(_declare(
            (L.boss_loot, (644, ("dm_hammer",)), dict(tier="heroic")),
            (L.boss_loot, (310008, ("dm_hammer",)), dict(tier="normal")),
            (L.boss_loot, (310004, ("dm_hammer",)), dict(tier="empowered_1")),
            (L.boss_loot, (639, ("dm_hammer",)), dict(tier="mythic")),
            (L.boss_loot, (643, ("dm_nothing",)), dict(tier="normal")),
        ), self.exp)
        self.assertEqual(len(plan.errors), 5, plan.errors)
        self.assertIn("a normal lootid drops 'normal'", plan.errors[0])
        self.assertIn("a heroic creature's lootid drops 'heroic'", plan.errors[1])
        self.assertIn("has no tier 'mythic'", plan.errors[3])
        self.assertIn("not a resolved item() key", plan.errors[4])

    def test_picks_two_is_one_reference_row_into_a_pool(self):
        plan = _build(_declare(
            (L.boss_loot, (643, ("dm_blade", "dm_saw")), dict(tier="normal", picks=2, reference=1700000)),
            (L.boss_loot, (310007, ("dm_blade", "dm_saw")), dict(tier="heroic", picks=2, reference=1700001)),
        ), self.exp)
        self.assertEqual(plan.errors, [])
        (ref_row,) = plan.groups[(643, 1)]
        self.assertEqual((ref_row["Item"], ref_row["Reference"], ref_row["Chance"], ref_row["MinCount"],
                          ref_row["MaxCount"], ref_row["GroupId"]), (1700000, 1700000, 0, 2, 2, 1))
        self.assertEqual([r["Item"] for r in plan.references[1700000]], [2169, 1937])
        self.assertEqual({(r["GroupId"], r["Chance"], r["MaxCount"]) for r in plan.references[1700001]}, {(1, 0, 1)})
        self.assertEqual([r["Item"] for r in plan.references[1700001]],
                         [self.entry(self.blade, "heroic"), self.entry(self.saw, "heroic")])

    def test_reference_rules(self):
        plan = _build(_declare(
            (L.boss_loot, (643, ("dm_blade", "dm_saw")), dict(tier="normal", picks=2, reference=1699999)),
            (L.boss_loot, (310007, ("dm_blade", "dm_saw")), dict(tier="heroic", picks=2, reference=1700001)),
            (L.boss_loot, (310008, ("dm_blade", "dm_saw")), dict(tier="heroic", picks=2, reference=1700001)),
        ), self.exp)
        self.assertTrue(any("outside source/ids.yaml's loot_reference block" in e for e in plan.errors))
        self.assertTrue(any("already another list's pool" in e for e in plan.errors))
        unequippable = _item("dm_token", inventory_type=0)
        plan = _build(_declare(
            (L.boss_loot, (643, ("dm_blade", "dm_token")), dict(tier="normal", picks=2, reference=1700000)),
        ), _expansion(self.blade, unequippable))
        self.assertTrue(any("need equippable items" in e for e in plan.errors), plan.errors)

    def test_hard_mode_group(self):
        decls = _declare(
            (L.boss_loot, (310004, ("dm_hammer",)), dict(tier="heroic")),
            (L.boss_loot, (310004, ("dm_fuse",)), dict(tier="heroic_hm", group=2, loot_mode=L.LOOT_MODE_HARD_MODE_1)),
        )
        plan = _build(decls, self.exp)
        self.assertEqual(plan.errors, [])
        (row,) = plan.groups[(310004, 2)]
        self.assertEqual((row["Item"], row["LootMode"], row["GroupId"], row["Chance"]),
                         (self.entry(self.fuse, "heroic_hm"), 2, 2, 0))
        self.assertEqual(row["Comment"], "Edwin VanCleef - Dm_Fuse (Heroic Hard Mode)")
        lone = _build(_declare(
            (L.boss_loot, (310004, ("dm_fuse",)), dict(tier="heroic_hm", group=2, loot_mode=2)),
        ), self.exp)
        self.assertTrue(any("declares no default list group" in e for e in lone.errors), lone.errors)
        always = _build(_declare(
            (L.boss_loot, (310004, ("dm_hammer",)), dict(tier="heroic")),
            (L.boss_loot, (310004, ("dm_fuse",)), dict(tier="heroic_hm", group=2, loot_mode=3)),
        ), self.exp)
        self.assertTrue(any("includes LOOT_MODE_DEFAULT" in e for e in always.errors), always.errors)
        normal = _build(_declare(
            (L.boss_loot, (639, ("dm_hammer",)), dict(tier="normal")),
            (L.boss_loot, (639, ("dm_fuse",)), dict(tier="heroic_hm", group=2, loot_mode=2)),
        ), self.exp)
        self.assertTrue(any("a normal lootid drops no tier" in e for e in normal.errors), normal.errors)

    def test_heroic_lootid_must_be_its_own(self):
        decls = _declare(
            (L.boss_loot, (644, ("dm_hammer",)), dict(tier="normal")),
            (L.boss_loot, (310008, ("dm_hammer",)), dict(tier="heroic")),
        )
        creatures = _creatures(e310008=644)
        strict = _build(decls, self.exp, creatures)
        self.assertEqual(len(strict.errors), 1)
        self.assertIn("heroic creature 310008's lootid is 644", strict.errors[0])
        lenient = _build(decls, self.exp, creatures, strict=False)
        self.assertEqual(lenient.errors, [])
        self.assertTrue(any("a full run emits the heroic row" in w for w in lenient.warnings))
        shared = _build(_declare((L.boss_loot, (644, ("dm_hammer",)), dict(tier="normal")),), self.exp, creatures)
        self.assertTrue(any("still uses the normal lootid 644" in w for w in shared.warnings), shared.warnings)
        orphan = _build(_declare((L.boss_loot, (9999, ("dm_hammer",)), dict(tier="normal")),), self.exp)
        self.assertTrue(any("no creature_template row has lootid 9999" in w for w in orphan.warnings))

    def test_lint_rows_catches_hand_built_breakage(self):
        plan = loot_tables.LootPlan(groups={
            (644, 1): [_row(644, 5187, chance=95.0), _row(644, 872, chance=5.0)],
            (643, 1): [_row(643, 1700000, reference=1700000, max_count=3)],
            (645, 1): [_row(645, 1, max_count=2), _row(645, 1, max_count=2)],
        }, references={1700000: [_row(1700000, 2169), _row(1700000, 1937, group=2)]}, picks={1700000: 3})
        errors = loot_tables.lint_rows(plan)
        self.assertTrue(any("Chance 95.0" in e for e in errors))
        self.assertTrue(any("3 picks from a pool of 2" in e for e in errors))
        self.assertTrue(any("MaxCount 2" in e for e in errors))
        self.assertTrue(any("listed twice" in e for e in errors))
        self.assertTrue(any("the pool must be one group" in e for e in errors))


class LiveTest(unittest.TestCase):
    def setUp(self):
        self.hammer = _item("dm_hammer", base=5187)
        self.rock = _item("dm_rock", base=872)
        self.blade = _item("dm_blade", base=2169)
        self.saw = _item("dm_saw", base=1937)
        self.exp = _expansion(self.hammer, self.rock, self.blade, self.saw)
        self.live = [
            _row(644, 2589, group=0, chance=13.0), _row(644, 5187, chance=95.0), _row(644, 872, chance=5.0),
            _row(642, 7365, group=0, chance=100.0), _row(642, 2169, chance=90.0), _row(642, 1937, chance=10.0),
            _row(643, 5195, chance=65.0),
        ]
        self.decls = _declare(
            (L.boss_loot, (644, ("dm_hammer", "dm_rock")), dict(tier="normal")),
            (L.boss_loot, (643, ("dm_blade", "dm_saw")), dict(tier="normal", picks=2, reference=1700000)),
            (L.remove_loot_group, (642,), dict(group=1, why="moved into Sneed's pool")),
        )

    def test_generic_pool_never_dropped(self):
        plan = _build(self.decls, self.exp)
        loot_tables.check_live(plan, self.live, [], IDS_CFG)
        self.assertEqual(len(plan.errors), 1, plan.errors)
        self.assertIn("643 group 1: the declaration would drop item 5195", plan.errors[0])
        plan = _build(self.decls, self.exp)
        live = [r for r in self.live if r["Item"] != 5195] + [_row(644, 1, reference=1000319)]
        loot_tables.check_live(plan, live, [], IDS_CFG)
        self.assertEqual(len(plan.errors), 1, plan.errors)
        self.assertIn("would drop reference 1000319", plan.errors[0])

    def test_list_item_in_another_group_and_unowned_reference(self):
        plan = _build(self.decls, self.exp)
        live = [r for r in self.live if r["Item"] != 5195] + [_row(644, 872, group=3, chance=1.0)]
        loot_tables.check_live(plan, live, [_row(1700005, 1, comment="x")], IDS_CFG)
        self.assertTrue(any("[872] also drop from live group 3" in w for w in plan.warnings), plan.warnings)
        self.assertTrue(any("Entry 1700005 sits in the loot_reference block" in e for e in plan.errors), plan.errors)

    def test_render_then_rerun_is_silent(self):
        live = [r for r in self.live if r["Item"] != 5195]
        plan = _build(self.decls, self.exp)
        loot_tables.check_live(plan, live, [], IDS_CFG)
        self.assertEqual(plan.errors, [])
        first = loot_tables.render(plan, live, [])
        self.assertEqual(first.groups, [(642, 1), (643, 1), (644, 1)])
        self.assertEqual(first.references, [1700000])
        text = "\n\n".join(first.blocks) + "\n"
        self.assertIn("DELETE FROM `creature_loot_template` WHERE `Entry` = 642 AND `GroupId` = 1;\n\n", text)
        self.assertNotIn("INSERT INTO `creature_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, "
                         "`QuestRequired`, `LootMode`, `GroupId`, `MinCount`, `MaxCount`, `Comment`) VALUES\n(642",
                         text)
        # Replay the rendered SQL over the live rows with the same parser generate.py's replay uses.
        creature = {tuple(r[c] for c in loot_tables.KEY_COLUMNS): dict(r) for r in live}
        reference: dict[tuple, dict] = {}
        for rows, table in ((creature, loot_tables.CREATURE_LOOT), (reference, loot_tables.REFERENCE_LOOT)):
            sql_dump.apply_composite_key_statements(rows, loot_tables.COLUMNS, loot_tables.KEY_COLUMNS, table, text)
        self.assertNotIn((642, 2169, 0, 1), creature)
        self.assertIn((642, 7365, 0, 0), creature)
        self.assertIn((644, 2589, 0, 0), creature)
        second = loot_tables.render(_build(self.decls, self.exp), list(creature.values()), list(reference.values()))
        self.assertEqual(second.blocks, [])


class HeroicCopyTest(unittest.TestCase):
    """Follow-up 1: a heroic lootid keeps every non-list group of its normal boss, copied unchanged."""

    def setUp(self):
        self.hammer = _item("dm_hammer", base=5187)
        self.fuse = _item("dm_fuse", ladder=HARD_MODE)
        self.exp = _expansion(self.hammer, self.fuse)
        self.live = [
            _row(639, 2589, group=0, chance=13.0, comment="cloth"), _row(639, 2874, group=0, chance=100.0),
            {**_row(639, 3637, group=0, chance=100.0), "QuestRequired": 1}, _row(639, 5187, chance=30.0),
            _row(639, 1, group=5, reference=1000319, comment="world loot"),
        ]
        self.decls = _declare(
            (L.boss_loot, (639, ("dm_hammer",)), dict(tier="normal")),
            (L.boss_loot, (310004, ("dm_hammer",)), dict(tier="heroic")),
            (L.boss_loot, (310004, ("dm_fuse",)), dict(tier="heroic_hm", group=2, loot_mode=2)),
        )

    def plan(self, live):
        plan = _build(self.decls, self.exp)
        loot_tables.derive_heroic_copies(plan, live)
        loot_tables.check_live(plan, live, [], IDS_CFG)
        return plan

    def test_non_list_groups_copied_unchanged(self):
        plan = self.plan(self.live)
        self.assertEqual(plan.errors, [])
        self.assertEqual(plan.heroic_sources, {310004: 639})
        self.assertEqual(sorted(plan.copies), [(310004, 0), (310004, 5)])
        group0 = {r["Item"]: r for r in plan.copies[(310004, 0)]}
        self.assertEqual(set(group0), {2589, 2874, 3637})
        self.assertEqual((group0[3637]["QuestRequired"], group0[3637]["Chance"]), (1, 100.0))
        self.assertEqual(group0[2589]["Comment"], "cloth")
        (ref,) = plan.copies[(310004, 5)]
        self.assertEqual((ref["Entry"], ref["Reference"], ref["GroupId"]), (310004, 1000319, 5))
        self.assertNotIn((310004, 1), plan.copies)  # the list group is the heroic list, not a copy

    def test_rerun_silent_and_clash(self):
        plan = self.plan(self.live)
        first = loot_tables.render(plan, self.live, [])
        self.assertEqual(first.copies, [(310004, 0), (310004, 5)])
        text = "\n\n".join(first.blocks) + "\n"
        creature = {tuple(r[c] for c in loot_tables.KEY_COLUMNS): dict(r) for r in self.live}
        reference: dict[tuple, dict] = {}
        for rows, table in ((creature, loot_tables.CREATURE_LOOT), (reference, loot_tables.REFERENCE_LOOT)):
            sql_dump.apply_composite_key_statements(rows, loot_tables.COLUMNS, loot_tables.KEY_COLUMNS, table, text)
        self.assertIn((310004, 3637, 0, 0), creature)
        live = list(creature.values())
        second = loot_tables.render(self.plan(live), live, list(reference.values()))
        self.assertEqual(second.blocks, [])
        clash = self.plan(self.live + [_row(639, 2592, group=2, chance=17.0)])
        self.assertTrue(any("normal lootid 639's group 2 is copied" in e for e in clash.errors), clash.errors)

    def test_foreign_row_in_a_copy_group_is_an_error(self):
        # a row of the heroic lootid's own in a group the copy rewrites would be deleted silently: ERROR
        for extra in (_row(310004, 9999, group=0, chance=100.0), _row(310004, 1, group=5, reference=1000777)):
            plan = self.plan(self.live + [extra])
            self.assertTrue(
                any(f"{loot_tables.CREATURE_LOOT} 310004 group {extra['GroupId']}: the copy of normal lootid 639's "
                    f"group {extra['GroupId']} would drop" in e for e in plan.errors), plan.errors)
        self.assertTrue(any("item 9999" in e for e in self.plan(
            self.live + [_row(310004, 9999, group=0, chance=100.0)]).errors))
        self.assertTrue(any("reference 1000777" in e for e in self.plan(
            self.live + [_row(310004, 1, group=5, reference=1000777)]).errors))

    def test_copy_rows_already_live_and_other_groups_are_fine(self):
        copy = [{**r, "Entry": 310004} for r in self.live if r["Entry"] == 639 and r["GroupId"] in (0, 5)]
        # the copy as a previous run wrote it, plus a heroic row in a group the copy does not rewrite
        plan = self.plan(self.live + copy + [_row(310004, 9999, group=7, chance=100.0)])
        self.assertEqual(plan.errors, [])
        self.assertTrue(any("group 7: live, but neither declared nor a copy" in w for w in plan.warnings),
                        plan.warnings)


class EngineModelTest(unittest.TestCase):
    """A model of LootMgr.cpp's fill for one creature (LootTemplate::Process, LootGroup::Roll/Process,
    LootGroupInvalidSelector): equal-chance rows of a group, the duplicate skip for an equippable item already in the
    loot from the same group, LootMode filtering, references processed MaxCount times with group 0."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.equippable: dict[int, bool] = {}

    def process(self, rows, references, loot, loot_mode, rng):
        groups: dict[int, list[dict]] = {}
        for row in rows:
            if row["GroupId"]:
                groups.setdefault(row["GroupId"], []).append(row)
            elif row["LootMode"] & loot_mode and rng.random() * 100 < row["Chance"]:
                loot.append((row["Item"], 0))
        for group_rows in groups.values():
            self.assertTrue(all(r["Chance"] == 0 for r in group_rows), "only equal-chance groups are modeled")
            valid = [r for r in group_rows if r["LootMode"] & loot_mode and not (
                not r["Reference"] and self.equippable.get(r["Item"], True)
                and (r["Item"], r["GroupId"]) in loot)]
            if not valid:
                continue
            pick = rng.choice(valid)
            if pick["Reference"]:
                for _ in range(pick["MaxCount"]):
                    self.process(references[pick["Reference"]], references, loot, loot_mode, rng)
            else:
                loot.append((pick["Item"], pick["GroupId"]))
        return loot

    def setUp(self):
        hammer, rock = _item("dm_hammer", base=5187), _item("dm_rock", base=872)
        blades = [_item(f"dm_blade{n}") for n in range(5)]
        fuse, signet, lantern = (_item(k, ladder=HARD_MODE) for k in ("dm_fuse", "dm_signet", "dm_lantern"))
        exp = _expansion(hammer, rock, *blades, fuse, signet, lantern)
        self.plan = _build(_declare(
            (L.boss_loot, (644, ("dm_hammer", "dm_rock")), dict(tier="normal")),
            (L.boss_loot, (643, tuple(b.decl.key for b in blades)), dict(tier="normal", picks=2,
                                                                          reference=1700000)),
            (L.boss_loot, (310004, ("dm_hammer", "dm_rock")), dict(tier="heroic")),
            (L.boss_loot, (310004, ("dm_fuse", "dm_signet", "dm_lantern")),
             dict(tier="heroic_hm", group=2, loot_mode=2)),
        ), exp)
        self.assertEqual(self.plan.errors, [])
        self.hard_mode = {next(t.entry for t in i.tiers if t.tier == "heroic_hm") for i in (fuse, signet, lantern)}

    def kill(self, lootid, loot_mode, rng):
        rows = [r for (entry, _), group in self.plan.groups.items() if entry == lootid for r in group]
        rows.append(_row(lootid, 2589, group=0, chance=13.0))  # stock cloth in group 0 rolls on its own
        return [item for item, _ in self.process(rows, self.plan.references, [], loot_mode, rng) if item != 2589]

    def test_each_list_drops_one_item_at_equal_chance(self):
        rng = random.Random(7)
        counts = Counter()
        for _ in range(4000):
            drop = self.kill(644, 1, rng)
            self.assertEqual(len(drop), 1)
            counts[drop[0]] += 1
        self.assertEqual(set(counts), {5187, *(r["Item"] for r in self.plan.groups[(644, 1)])})
        for n in counts.values():
            self.assertAlmostEqual(n / 4000, 0.5, delta=0.04)

    def test_sneed_drops_two_distinct_items(self):
        rng = random.Random(11)
        pool = {r["Item"] for r in self.plan.references[1700000]}
        pairs = Counter()
        for _ in range(3000):
            drop = self.kill(643, 1, rng)
            self.assertEqual(len(drop), 2)
            self.assertEqual(len(set(drop)), 2)
            self.assertTrue(set(drop) <= pool)
            pairs[frozenset(drop)] += 1
        self.assertEqual(len(pairs), 10)  # every pair of the 5 items occurs

    def test_hard_mode_item_only_on_a_lit_kill(self):
        rng = random.Random(3)
        for _ in range(500):
            unlit = self.kill(310004, 1, rng)
            self.assertEqual(len(unlit), 1)
            self.assertFalse(set(unlit) & self.hard_mode)
            lit = self.kill(310004, 1 | 2, rng)  # AddLootMode(LOOT_MODE_HARD_MODE_1)
            self.assertEqual(len(lit), 2)
            self.assertEqual(len(set(lit) & self.hard_mode), 1)


class DeadminesSourceTest(unittest.TestCase):
    """The real declarations in source/items/deadmines_loot.py (item keys from deadmines.py)."""

    @classmethod
    def setUpClass(cls):
        merged = D.load_items_dir(TOOL_ROOT / "source" / "items")
        # Deadmines only (the dm_ keys): other dungeons declare items whose loot tables come with their boss builds.
        cls.items = {e["id"]: e["_decl"] for e in merged["item_declarations"] if e["id"].startswith("dm_")}
        cls.loot = [e["_decl"] for e in merged["loot_declarations"]]

    def test_every_item_drops_once_per_difficulty(self):
        normal = [k for d in self.loot if not d.removal and d.tier == "normal" for k in d.items]
        heroic = [k for d in self.loot if not d.removal and d.tier == "heroic" for k in d.items]
        hard_mode = [k for d in self.loot if not d.removal and d.tier == "heroic_hm" for k in d.items]
        self.assertEqual(len(normal), 29)
        self.assertEqual(sorted(normal), sorted(set(normal)))
        self.assertEqual(sorted(normal), sorted(heroic))
        self.assertEqual(sorted(hard_mode), ["dm_blackguards_signet", "dm_lantern_of_the_roaring_flame",
                                             "dm_powder_keg_fuse"])
        self.assertEqual(set(normal) | set(hard_mode), set(self.items))

    def test_sneed_hard_mode_and_shredder(self):
        by_key = {(d.lootid, d.group): d for d in self.loot}
        for lootid, ref in ((643, 1700000), (310007, 1700001)):
            sneed = by_key[(lootid, 1)]
            self.assertEqual((sneed.picks, sneed.reference, len(sneed.items)), (2, ref, 5))
        self.assertTrue(by_key[(642, 1)].removal)
        hard_mode = by_key[(310004, 2)]
        self.assertEqual((hard_mode.loot_mode, hard_mode.tier), (L.LOOT_MODE_HARD_MODE_1, "heroic_hm"))
        self.assertFalse(any(d.loot_mode != 1 for d in self.loot if d.lootid != 310004))
        self.assertEqual(len(self.loot), 18)


if __name__ == "__main__":
    unittest.main()
