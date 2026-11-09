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

Scholomance (WP-L): `replaces_items=` / `replaces_references=` (a list drops the named stock rows on purpose, any other
foreign row is still an ERROR), `remove_loot_rows()` (single item rows, rendered as one DELETE, silent on a rerun,
kept out of the heroic copies), `set_token()` keys in a list (resolved to the token of the kill's tier), and the real
source/items/scholomance_loot.py declarations.

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
from lib.dsl import sets as S  # noqa: E402

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
        for kwargs in (dict(replaces_items=(0,)), dict(replaces_items=(5, 5)), dict(replaces_references="35031"),
                       dict(replaces_references=(True,))):
            with self.subTest(kwargs=kwargs), self.assertRaises(L.LootDeclarationError):
                L.boss_loot(644, ("a",), tier="normal", **kwargs)
        for args, kwargs in (((644, ()), dict(why="x")), ((644, (5, 5)), dict(why="x")), ((644, (5,)), dict(why=" ")),
                             ((644, (5,)), dict(why="x", group=128)), ((0, (5,)), dict(why="x")),
                             ((644, ("5",)), dict(why="x"))):
            with self.subTest(args=args, kwargs=kwargs), self.assertRaises(L.LootDeclarationError):
                L.remove_loot_rows(*args, **kwargs)

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


class ReplacesAndRowsTest(unittest.TestCase):
    """WP-L: the stock rows a list replaces, single row removals, and set tokens in a list."""

    def setUp(self):
        self.hammer = _item("sc_hammer", base=5187)
        self.rock = _item("sc_rock", base=872)
        self.exp = _expansion(self.hammer, self.rock)
        self.live = [
            _row(639, 2589, group=0, chance=13.0, comment="cloth"), _row(639, 7777, group=0, chance=1.0),
            _row(639, 5187, chance=30.0), _row(639, 4444, chance=17.0), _row(639, 1, reference=35031, chance=30.0),
        ]
        self.decls = _declare(
            (L.boss_loot, (639, ("sc_hammer", "sc_rock")), dict(tier="normal", replaces_items=(4444,),
                                                                replaces_references=(35031,))),
            (L.boss_loot, (310004, ("sc_hammer", "sc_rock")), dict(tier="heroic")),
            (L.remove_loot_rows, (639, (7777,)), dict(group=0, why="cut")),
        )

    STOCK_POOL = [_row(35031, 4445, chance=10.0)]  # the shared pool the list replaces, live in reference_loot_template

    def plan(self, live, decls=None, exp=None):
        plan = _build(decls or self.decls, exp or self.exp)
        loot_tables.derive_heroic_copies(plan, live)
        loot_tables.check_live(plan, live, self.STOCK_POOL, IDS_CFG)
        return plan

    def test_named_stock_rows_may_go_and_any_other_foreign_row_may_not(self):
        plan = self.plan(self.live)
        self.assertEqual(plan.errors, [])
        self.assertEqual(plan.replaces[(639, 1)], (frozenset({4444}), frozenset({35031})))
        for extra, text in ((_row(639, 5555, chance=1.0), "item 5555"),
                            (_row(639, 1, reference=1000319), "reference 1000319")):
            errors = self.plan(self.live + [extra]).errors
            self.assertEqual(len(errors), 1, errors)
            self.assertIn(f"would drop {text}", errors[0])
            self.assertIn("replaces_items=", errors[0])
        # without the allow-list the same stock rows are foreign
        bare = _declare((L.boss_loot, (639, ("sc_hammer", "sc_rock")), dict(tier="normal")))
        errors = self.plan(self.live, bare).errors
        self.assertTrue(any("item 4444, reference 35031" in e for e in errors), errors)

    def test_a_group_removal_takes_replaces_too(self):
        live = self.live + [_row(639, 6666, group=2, chance=2.0), _row(639, 5187, group=2, chance=0.0)]
        decls = _declare(
            (L.boss_loot, (639, ("sc_hammer",)), dict(tier="normal", replaces_items=(4444,),
                                                      replaces_references=(35031,))),
            (L.remove_loot_group, (639,), dict(group=2, why="x", replaces_items=(6666,))),
        )
        self.assertEqual(self.plan(live, decls).errors, [])
        bare = _declare(
            (L.boss_loot, (639, ("sc_hammer",)), dict(tier="normal", replaces_items=(4444,),
                                                      replaces_references=(35031,))),
            (L.remove_loot_group, (639,), dict(group=2, why="x")),
        )
        self.assertTrue(any("639 group 2: the declaration would drop item 6666" in e
                            for e in self.plan(live, bare).errors))

    def test_row_removal_renders_once_and_keeps_the_heroic_copy_clean(self):
        plan = self.plan(self.live)
        self.assertEqual(plan.row_removals, {(639, 0): ((7777,), "cut")})
        self.assertEqual({r["Item"] for r in plan.copies[(310004, 0)]}, {2589})
        first = loot_tables.render(plan, self.live, [])
        self.assertEqual(first.row_removals, [(639, 0)])
        text = "\n\n".join(first.blocks) + "\n"
        self.assertIn("DELETE FROM `creature_loot_template` WHERE `Entry` = 639 AND `GroupId` = 0 AND `Reference` = 0 "
                      "AND `Item` IN (7777);", text)
        creature = {tuple(r[c] for c in loot_tables.KEY_COLUMNS): dict(r) for r in self.live}
        sql_dump.apply_composite_key_statements(creature, loot_tables.COLUMNS, loot_tables.KEY_COLUMNS,
                                                loot_tables.CREATURE_LOOT, text)
        self.assertNotIn((639, 7777, 0, 0), creature)
        self.assertIn((639, 2589, 0, 0), creature)  # the rest of the group stays
        live = list(creature.values())
        second = loot_tables.render(self.plan(live), live, [])
        self.assertEqual(second.blocks, [])
        notes = loot_tables.summary_notes(self.plan(live), second)
        self.assertIn("1 row removal group(s) (1 row(s))", notes[0])

    def test_row_removal_cannot_target_a_declared_group(self):
        decls = _declare(
            (L.boss_loot, (639, ("sc_hammer",)), dict(tier="normal", replaces_items=(4444,),
                                                      replaces_references=(35031,))),
            (L.remove_loot_rows, (639, (5187,)), dict(group=1, why="x")),
        )
        self.assertTrue(any("also declared by boss_loot()" in e for e in self.plan(self.live, decls).errors))

    def test_a_list_item_in_a_removed_row_is_no_double_drop(self):
        live = self.live + [_row(639, 872, group=0, chance=1.0)]
        decls = _declare(
            (L.boss_loot, (639, ("sc_hammer", "sc_rock")), dict(tier="normal", replaces_items=(4444,),
                                                                replaces_references=(35031,))),
            (L.remove_loot_rows, (639, (872, 7777)), dict(group=0, why="in the list now")),
        )
        plan = self.plan(live, decls)
        self.assertEqual(plan.errors, [])
        self.assertFalse(any("also drop from live group" in w for w in plan.warnings), plan.warnings)

    def test_set_tokens_resolve_to_the_kills_tier(self):
        token = S.set_token(
            "tok_belt", name="Haunted Belt", slots=(6,), ladder=DUNGEON, like=22356, ilvl=60, quality=D.Quality.RARE,
            required_level=0, entries={"normal": 70520, "heroic": 70521, "empowered_1": 70522},
            costs={"normal": 3020, "heroic": 3021, "empowered_1": 3022},
        )
        decls = _declare(
            (L.boss_loot, (639, ("sc_hammer",)), dict(tier="normal")),
            (L.boss_loot, (639, ("tok_belt",)), dict(tier="normal", group=3)),
            (L.boss_loot, (310004, ("sc_hammer",)), dict(tier="heroic")),
            (L.boss_loot, (310004, ("tok_belt",)), dict(tier="heroic", group=3)),
        )
        plan = loot_tables.build(decls, self.exp, ids_cfg=IDS_CFG, heroic_pairs=HEROIC_PAIRS,
                                 creature_rows=_creatures(), tokens={"tok_belt": token})
        self.assertEqual(plan.errors, [])
        self.assertEqual([(r["Item"], r["GroupId"], r["Chance"]) for r in plan.groups[(639, 3)]], [(70520, 3, 0)])
        self.assertEqual([r["Item"] for r in plan.groups[(310004, 3)]], [70521])
        self.assertIn("Haunted Belt (Normal)", plan.groups[(639, 3)][0]["Comment"])
        self.assertTrue({70520, 70521, 70522} <= plan.owned_items)
        # a token tier that does not fit the difficulty, and an unknown key
        bad = _declare(
            (L.boss_loot, (639, ("tok_belt",)), dict(tier="heroic", group=3)),
            (L.boss_loot, (644, ("tok_missing",)), dict(tier="normal", group=3)),
        )
        plan = loot_tables.build(bad, self.exp, ids_cfg=IDS_CFG, heroic_pairs=HEROIC_PAIRS,
                                 creature_rows=_creatures(), tokens={"tok_belt": token})
        self.assertEqual(len(plan.errors), 2, plan.errors)
        self.assertIn("a normal lootid drops 'normal'", plan.errors[0])
        self.assertIn("not a resolved item() key", plan.errors[1])
        # a live token row in its own group is no foreign row once the declaration owns it
        live = [_row(639, 70520, group=3)]
        plan = loot_tables.build(decls[:2], self.exp, ids_cfg=IDS_CFG, heroic_pairs=HEROIC_PAIRS,
                                 creature_rows=_creatures(), tokens={"tok_belt": token})
        loot_tables.check_live(plan, live, [], IDS_CFG)
        self.assertEqual(plan.errors, [])


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


def _cond(group, entry, ctype, v1=0, v2=0, source=loot_tables.SOURCE_CREATURE_LOOT, comment=None) -> dict:
    row = {c: 0 for c in loot_tables.CONDITION_COLUMNS}
    row.update(SourceTypeOrReferenceId=source, SourceGroup=group, SourceEntry=entry, ConditionTypeOrReference=ctype,
               ConditionValue1=v1, ConditionValue2=v2, ScriptName="", Comment=comment)
    return row


def _replay(rows_by_table: dict[str, list[dict]], text: str) -> dict[str, list[dict]]:
    """`rows_by_table` (creature, reference loot and conditions) after applying `text` the way the import would."""
    out = {}
    for table, rows in rows_by_table.items():
        columns, keys = ((loot_tables.CONDITION_COLUMNS, loot_tables.CONDITION_KEY_COLUMNS)
                         if table == loot_tables.CONDITIONS else (loot_tables.COLUMNS, loot_tables.KEY_COLUMNS))
        keyed = {tuple(r[c] for c in keys): dict(r) for r in rows}
        sql_dump.apply_composite_key_statements(keyed, columns, keys, table, text)
        out[table] = list(keyed.values())
    return out


class ConditionsAndPoolsTest(unittest.TestCase):
    """F-C4 (R-C LOOT S-1, S-3, N-1, N-2): heroic copies carry their loot conditions, a dropped row takes its
    conditions with it, remove_reference_pool() and copy_normal_loot(), and the hand-named ids exist."""

    def setUp(self):
        self.hammer = _item("sc_hammer", base=5187)
        self.exp = _expansion(self.hammer)
        self.creature = [
            _row(639, 2589, group=0, chance=13.0), {**_row(639, 3637, group=0, chance=100.0), "QuestRequired": 1},
            _row(639, 7777, group=0, chance=1.0), _row(639, 5187, chance=30.0), _row(639, 4444, chance=17.0),
            _row(639, 1, reference=35031, chance=30.0),
            _row(643, 12843, group=0, chance=100.0), _row(643, 14047, group=0, chance=20.0),
            _row(643, 14576, chance=8.0),
        ]
        self.reference = [_row(35031, 4445, chance=10.0), _row(35031, 4446, chance=10.0)]
        self.conditions = [
            _cond(639, 3637, 13, 2, 1, comment="human form"), _cond(639, 7777, 8, 5384),
            _cond(639, 4444, 7, 171, 1), _cond(643, 12843, 1, 17670),
            _cond(35031, 4445, 8, 5384, source=loot_tables.SOURCE_REFERENCE_LOOT),
        ]
        self.decls = _declare(
            (L.boss_loot, (639, ("sc_hammer",)), dict(tier="normal", replaces_items=(4444,),
                                                      replaces_references=(35031,))),
            (L.boss_loot, (310004, ("sc_hammer",)), dict(tier="heroic")),
            (L.remove_loot_rows, (639, (7777,)), dict(group=0, why="cut")),
            (L.remove_loot_group, (643,), dict(group=1, why="moved", replaces_items=(14576,))),
            (L.copy_normal_loot, (310007,), dict(why="the list is on another boss")),
            (L.remove_reference_pool, (35031,), dict(why="the list replaces it")),
        )
        self.creatures = _creatures()

    def plan(self, creature=None, reference=None, conditions=None, decls=None, other_loot=None, items=None):
        plan = _build(decls or self.decls, self.exp, self.creatures)
        loot_tables.derive_heroic_copies(plan, creature or self.creature,
                                         self.conditions if conditions is None else conditions)
        loot_tables.check_live(plan, creature or self.creature, self.reference if reference is None else reference,
                               IDS_CFG, item_entries=items, other_loot=other_loot)
        return plan

    def test_heroic_copies_carry_the_conditions(self):
        plan = self.plan()
        self.assertEqual(plan.errors, [])
        items, rows = plan.conditions[(1, 310004)]
        self.assertEqual(items, frozenset({2589, 3637}))  # the copied rows (7777 is removed, so not copied)
        self.assertEqual([(r["SourceGroup"], r["SourceEntry"], r["ConditionTypeOrReference"], r["ConditionValue1"],
                           r["ConditionValue2"], r["Comment"]) for r in rows], [(310004, 3637, 13, 2, 1, "human form")])
        # copy_normal_loot(): the heroic lootid with no list copies group 0, the Scourgestone keeps its aura gate
        self.assertEqual({r["Item"] for r in plan.copies[(310007, 0)]}, {12843, 14047})
        self.assertNotIn((310007, 1), plan.copies)  # the removed group is no copy
        items, rows = plan.conditions[(1, 310007)]
        self.assertEqual([(r["SourceEntry"], r["ConditionTypeOrReference"], r["ConditionValue1"]) for r in rows],
                         [(12843, 1, 17670)])

    def test_a_dropped_row_takes_its_conditions(self):
        plan = self.plan()
        # 7777 (remove_loot_rows) and 4444 (replaces_items) leave lootid 639: their conditions go; 3637 stays
        self.assertEqual(plan.conditions[(1, 639)], (frozenset({4444, 7777}), []))
        self.assertEqual(plan.conditions[(10, 35031)], (None, []))  # the removed pool's conditions
        # an item that still drops from the lootid (another group) keeps its condition
        creature = self.creature + [_row(639, 4444, group=4, chance=5.0)]
        self.assertEqual(self.plan(creature).conditions[(1, 639)][0], frozenset({7777}))

    def test_render_then_rerun_is_silent(self):
        plan = self.plan()
        first = loot_tables.render(plan, self.creature, self.reference, self.conditions)
        self.assertEqual(first.pool_removals, [35031])
        self.assertEqual(sorted(first.conditions), [(1, 639), (1, 310004), (1, 310007), (10, 35031)])
        text = "\n\n".join(first.blocks) + "\n"
        self.assertIn("DELETE FROM `reference_loot_template` WHERE `Entry` = 35031;", text)
        self.assertIn("DELETE FROM `conditions` WHERE `SourceTypeOrReferenceId` = 1 AND `SourceGroup` = 310004 AND "
                      "`SourceEntry` IN (3637);", text)
        after = _replay({loot_tables.CREATURE_LOOT: self.creature, loot_tables.REFERENCE_LOOT: self.reference,
                         loot_tables.CONDITIONS: self.conditions}, text)
        conds = {(r["SourceTypeOrReferenceId"], r["SourceGroup"], r["SourceEntry"]) for r in after["conditions"]}
        self.assertEqual(conds, {(1, 639, 3637), (1, 643, 12843), (1, 310004, 3637), (1, 310007, 12843)})
        self.assertEqual(after[loot_tables.REFERENCE_LOOT], [])
        creature, reference = after[loot_tables.CREATURE_LOOT], after[loot_tables.REFERENCE_LOOT]
        replan = self.plan(creature, reference, after["conditions"])
        self.assertEqual(replan.errors, [])
        second = loot_tables.render(replan, creature, reference, after["conditions"])
        self.assertEqual(second.blocks, [])

    def test_a_pool_still_used_is_refused(self):
        self.assertEqual(self.plan().errors, [])  # its only user is the group the list replaces
        for creature, other, where in (
            (self.creature + [_row(644, 1, group=2, reference=35031)], None, "creature_loot_template 644 group 2"),
            (None, {"gameobject_loot_template": [_row(9000, 1, reference=35031)]}, "gameobject_loot_template 9000"),
        ):
            errors = self.plan(creature, other_loot=other).errors
            self.assertTrue(any(f"remove_reference_pool(35031): still referenced by {where}" in e for e in errors),
                            errors)
        in_block = _declare((L.remove_reference_pool, (1700001,), dict(why="x")))
        self.assertTrue(any("loot_reference block" in e for e in self.plan(decls=in_block).errors))

    def test_copy_normal_loot_needs_a_heroic_lootid_without_a_list(self):
        for decls, text in (
            (_declare((L.copy_normal_loot, (643,), dict(why="x"))), "is not a heroic creature"),
            (_declare((L.boss_loot, (310004, ("sc_hammer",)), dict(tier="heroic")),
                      (L.copy_normal_loot, (310004,), dict(why="x"))), "also declares a list"),
        ):
            errors = _build(decls, self.exp).errors
            self.assertTrue(any(text in e for e in errors), errors)
        creatures = _creatures(e310007=643)  # heroic Sneed still on the normal lootid
        plan = _build(_declare((L.copy_normal_loot, (310007,), dict(why="x"))), self.exp, creatures)
        self.assertTrue(any("heroic creature 310007's lootid is 643" in e for e in plan.errors), plan.errors)

    def test_hand_named_ids_must_exist(self):
        known = {2589, 3637, 7777, 5187, 4444, 12843, 14047, 14576}
        self.assertEqual(self.plan(items=known).errors, [])
        typo = _declare(
            (L.boss_loot, (639, ("sc_hammer",)), dict(tier="normal", replaces_items=(4444, 4447),
                                                      replaces_references=(35031, 35099))),
            (L.remove_loot_rows, (639, (7777, 7778)), dict(group=0, why="cut")),
        )
        errors = self.plan(decls=typo, items=known).errors
        self.assertTrue(any("replaces_references= names [35099]" in e for e in errors), errors)
        self.assertTrue(any("replaces_items= names [4447]" in e for e in errors), errors)
        self.assertTrue(any("remove_loot_rows(639, group=0): [7778] has no item_template row" in e for e in errors),
                        errors)

    def test_dsl_checks(self):
        for fn, args, kwargs in ((L.remove_reference_pool, (0,), dict(why="x")),
                                 (L.remove_reference_pool, (35031,), dict(why=" ")),
                                 (L.copy_normal_loot, (-1,), dict(why="x")),
                                 (L.copy_normal_loot, (310070,), dict(why=""))):
            with self.subTest(fn=fn.__name__, args=args), self.assertRaises(L.LootDeclarationError):
                fn(*args, **kwargs)
        with self.assertRaises(registry.DuplicateIdError):
            _declare((L.remove_reference_pool, (35031,), dict(why="x")),
                     (L.remove_reference_pool, (35031,), dict(why="y")))


class ScholomanceConditionsTest(unittest.TestCase):
    """F-C4 (R-C LOOT S-3), on the replayed live tables: the heroic copies of the real Scholomance declarations keep
    the loot conditions (Ras's head needs his human form, a Scourgestone the Argent Dawn Commission), and Marduk's
    normal condition still points at a real row."""

    HEROIC = {10503: 310093, 11622: 310110, 10432: 310069, 10433: 310070, 10508: 310098, 10505: 310095,
              11261: 310103, 10901: 310100, 10507: 310097, 10504: 310094, 10502: 310092, 1853: 310068}

    @classmethod
    def setUpClass(cls):
        _merged, scholo = _loot_of("scholomance_loot.py")
        cls.creature, _reference = loot_tables.load_live()
        cls.conditions = loot_tables.load_live_conditions()
        plan = loot_tables.LootPlan()
        for decl in scholo:
            if decl.listing:
                plan.groups[(decl.lootid, decl.group)] = []  # the list rows are new items, no conditions
            elif decl.row_removal:
                plan.row_removals[(decl.lootid, decl.group)] = (decl.rows, decl.why)
            elif decl.pool_removal:
                plan.pool_removals[decl.reference] = decl.why
        plan.heroic_sources = {heroic: normal for normal, heroic in cls.HEROIC.items()}
        loot_tables.derive_heroic_copies(plan, cls.creature, cls.conditions)
        cls.plan = plan

    def wanted(self, lootid):
        return {(r["SourceEntry"], r["ConditionTypeOrReference"], r["ConditionValue1"], r["ConditionValue2"])
                for r in self.plan.conditions.get((1, lootid), (frozenset(), []))[1]}

    def test_ras_head_keeps_the_human_form_condition_on_heroic(self):
        self.assertIn(13626, {r["Item"] for r in self.plan.copies[(310098, 0)]})
        self.assertIn((13626, 13, 2, 1), self.wanted(310098))  # CONDITION_INSTANCE_INFO data 2 = 1 (human form)

    def test_scourgestones_keep_the_aura_gate_on_heroic(self):
        for normal, heroic in self.HEROIC.items():
            stones = {r["SourceEntry"] for r in self.conditions
                      if (r["SourceTypeOrReferenceId"], r["SourceGroup"]) == (1, normal)
                      and r["SourceEntry"] in (12841, 12843)}
            for stone in stones:
                with self.subTest(boss=normal, item=stone):
                    self.assertIn((stone, 1, 17670, 0), self.wanted(heroic))  # CONDITION_AURA Argent Dawn Commission
        self.assertIn((12843, 1, 17670, 0), self.wanted(310070))  # Marduk's heroic copy (copy_normal_loot)

    def test_marduk_condition_keeps_its_row(self):
        marduk = {_int(r["Item"]) for r in self.creature if _int(r["Entry"]) == 10433 and _int(r["GroupId"]) == 0}
        self.assertIn(12843, marduk)
        self.assertNotIn((1, 10433), self.plan.conditions)  # no condition of 10433 is dropped (none of his rows is)
        # the only dropped rows with a condition are none: the replaced stock rows carry no loot condition
        self.assertEqual([k for k, (items, rows) in self.plan.conditions.items() if not rows and k[0] == 1], [])


def _int(value) -> int:
    return int(float(value))


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


def _loot_of(file_name: str) -> tuple[dict, list[L.LootDecl]]:
    """source/items/ loaded once, and the loot declarations `file_name` (e.g. "deadmines_loot.py") made: the file
    that declared each one, not an item-key prefix or a hard-coded lootid."""
    registry.record_provenance()
    try:
        merged = D.load_items_dir(TOOL_ROOT / "source" / "items")
        mine = [e["_decl"] for e in merged["loot_declarations"]
                if Path(registry.declared_in(e) or "").name == file_name]
    finally:
        registry.stop_provenance()
    return merged, mine


class DeadminesSourceTest(unittest.TestCase):
    """The real declarations in source/items/deadmines_loot.py (item keys from deadmines.py)."""

    @classmethod
    def setUpClass(cls):
        merged, cls.loot = _loot_of("deadmines_loot.py")
        # Deadmines only (the dm_ keys): other dungeons declare items whose loot tables come with their boss builds.
        cls.items = {e["id"]: e["_decl"] for e in merged["item_declarations"] if e["id"].startswith("dm_")}

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


class ShadowfangKeepSourceTest(unittest.TestCase):
    """The real declarations in source/items/shadowfang_keep_loot.py (item keys from shadowfang_keep.py)."""

    @classmethod
    def setUpClass(cls):
        merged, cls.loot = _loot_of("shadowfang_keep_loot.py")
        cls.items = {e["id"]: e["_decl"] for e in merged["item_declarations"] if e["id"].startswith("sfk_")}

    def test_every_item_drops_once_per_difficulty(self):
        normal = [k for d in self.loot if d.tier == "normal" for k in d.items]
        heroic = [k for d in self.loot if d.tier == "heroic" for k in d.items]
        hard_mode = [k for d in self.loot if d.tier == "heroic_hm" for k in d.items]
        self.assertEqual(len(normal), 24)
        self.assertEqual(sorted(normal), sorted(set(normal)))
        self.assertEqual(sorted(normal), sorted(heroic))
        self.assertEqual(sorted(hard_mode), ["sfk_arugals_shadow_tome", "sfk_ashcrombes_locket",
                                             "sfk_vial_of_the_worgens_curse"])
        self.assertEqual(set(normal) | set(hard_mode), set(self.items))

    def test_arugals_hard_mode_group_is_the_only_special_one(self):
        by_key = {(d.lootid, d.group): d for d in self.loot}
        hard_mode = by_key[(310051, 2)]
        self.assertEqual((hard_mode.loot_mode, hard_mode.tier), (L.LOOT_MODE_HARD_MODE_1, "heroic_hm"))
        self.assertFalse(any(d.loot_mode != 1 for d in self.loot if (d.lootid, d.group) != (310051, 2)))
        self.assertTrue(all(d.group == 1 for d in self.loot if (d.lootid, d.group) != (310051, 2)))
        self.assertEqual(len(self.loot), 19)


class ScholomanceSourceTest(unittest.TestCase):
    """The real declarations in source/items/scholomance_loot.py (item keys from scholomance.py, tokens from
    haunted_set.py)."""

    # normal lootid -> heroic lootid -> expected list size; Ras and Gandling drop two
    BOSSES = {  # name: (normal, heroic, list size, picks, token key)
        "Jandice": (10503, 310093, 5, 1, "haunted_token_waist"),
        "Rattlegore": (11622, 310110, 4, 1, None),
        "Vectus": (10432, 310069, 4, 1, "haunted_token_hands"),
        "Ras": (10508, 310098, 6, 2, "haunted_token_shoulders"),
        "Malicia": (10505, 310095, 4, 1, None),
        "Krastinov": (11261, 310103, 5, 1, None),
        "Polkelt": (10901, 310100, 4, 1, None),
        "Ravenian": (10507, 310097, 4, 1, None),
        "Alexei": (10504, 310094, 4, 1, None),
        "Illucia": (10502, 310092, 4, 1, None),
        "Gandling": (1853, 310068, 8, 2, "haunted_token_head"),
    }

    @classmethod
    def setUpClass(cls):
        merged, scholo = _loot_of("scholomance_loot.py")
        cls.items = {e["id"]: e["_decl"] for e in merged["item_declarations"] if e["id"].startswith("scholo_")}
        cls.tokens = {e["id"][1] for e in merged["item_set_declarations"] if e["id"][0] == "token"}
        cls.lists = [d for d in scholo if d.listing and not d.removal]
        cls.removals = [d for d in scholo if d.removal]
        cls.row_removals = [d for d in scholo if d.row_removal]
        cls.pool_removals = [d for d in scholo if d.pool_removal]
        cls.copies = [d for d in scholo if d.copy_only]

    def groups(self, group):
        return {(d.lootid, d.group): d for d in self.lists if d.group == group}

    def test_every_item_drops_once_per_difficulty(self):
        normal = [k for d in self.lists if d.tier == "normal" and d.group == 1 for k in d.items]
        heroic = [k for d in self.lists if d.tier == "heroic" and d.group == 1 for k in d.items]
        hard_mode = [k for d in self.lists if d.tier == "heroic_hm" for k in d.items]
        self.assertEqual(len(normal), 52)
        self.assertEqual(sorted(normal), sorted(set(normal)))
        self.assertEqual(sorted(normal), sorted(heroic))
        self.assertEqual(len(hard_mode), 6)
        self.assertEqual(set(normal) | set(hard_mode), set(self.items))

    def test_each_boss_list_and_picks(self):
        by_key = self.groups(1)
        for name, (normal, heroic, size, picks, _token) in self.BOSSES.items():
            for lootid, tier in ((normal, "normal"), (heroic, "heroic")):
                with self.subTest(boss=name, lootid=lootid):
                    decl = by_key[(lootid, 1)]
                    self.assertEqual((decl.tier, len(decl.items), decl.picks, decl.loot_mode), (tier, size, picks, 1))
                    self.assertEqual(decl.reference is not None, picks > 1)
            self.assertEqual(by_key[(normal, 1)].items, by_key[(heroic, 1)].items)
        refs = sorted(d.reference for d in by_key.values() if d.reference)
        self.assertEqual(refs, [1700002, 1700003, 1700004, 1700005])

    def test_the_four_haunted_tokens_are_their_own_group_at_the_kills_tier(self):
        by_key = self.groups(3)
        wanted = {name: spec for name, spec in self.BOSSES.items() if spec[4]}
        self.assertEqual(sorted(wanted), ["Gandling", "Jandice", "Ras", "Vectus"])
        for name, (normal, heroic, _size, _picks, token) in wanted.items():
            self.assertIn(token, self.tokens)
            for lootid, tier in ((normal, "normal"), (heroic, "heroic")):
                decl = by_key[(lootid, 3)]
                self.assertEqual((decl.items, decl.tier, decl.picks, decl.loot_mode), ((token,), tier, 1, 1), name)
        self.assertEqual(len(by_key), 8)

    def test_hard_mode_is_group_two_of_the_heroic_lootids_only(self):
        by_key = self.groups(2)
        self.assertEqual(sorted(by_key), [(310068, 2), (310098, 2)])
        for key, expected in (((310098, 2), {"scholo_phylactery_shard", "scholo_frostwhispers_chillband",
                                             "scholo_bonechill_blade"}),
                              ((310068, 2), {"scholo_transfer_papers", "scholo_honor_roll_ribbon",
                                             "scholo_darkmasters_portal_rod"})):
            decl = by_key[key]
            self.assertEqual((decl.loot_mode, decl.tier, decl.picks, set(decl.items)),
                             (L.LOOT_MODE_HARD_MODE_1, "heroic_hm", 1, expected))
        self.assertFalse(any(d.loot_mode != 1 for d in self.lists if d.group != 2))
        # Gandling's stock group 2 (his list) is removed so the heroic lootid's group 2 is the hard mode one
        removed = {(d.lootid, d.group): d for d in self.removals}
        self.assertEqual(sorted(removed), [(1853, 2), (10433, 1)])
        self.assertEqual(removed[(1853, 2)].replaces_items, (13944,))

    # Every boss's list, pinned by key (docs/dungeons/scholomance-rework.md ## Loot): a swap between two same-size lists
    # fails here (R-C LOOT N-3).
    LISTS = {
        10503: {"scholo_barovian_family_sword", "scholo_phantasmal_cloak", "scholo_wraithplate_leggings",
                "scholo_staff_of_metanoia", "scholo_ghostloom_leggings"},
        11622: {"scholo_rattlecage_buckler", "scholo_frightskull_shaft", "scholo_corpselight_greaves",
                "scholo_spare_rib"},
        10432: {"scholo_ebon_hilt_of_marduk", "scholo_death_knight_sabatons", "scholo_skullsmoke_pants",
                "scholo_dark_advisors_pendant"},
        10508: {"scholo_alannas_embrace", "scholo_iceblade_hacker", "scholo_maelstrom_leggings",
                "scholo_shadowy_mail_greaves", "scholo_spellbound_tome", "scholo_intricately_runed_shield"},
        10505: {"scholo_necropile_robe", "scholo_cadaverous_leggings", "scholo_dimly_opalescent_ring",
                "scholo_jar_of_torn_souls"},
        11261: {"scholo_cadaverous_armor", "scholo_deathbone_sabatons", "scholo_hammer_of_the_vesper",
                "scholo_krastinovs_suture_kit", "scholo_rib_spreader"},
        10901: {"scholo_cadaverous_walkers", "scholo_bloodmail_bracers", "scholo_ghoul_skin_leggings",
                "scholo_polkelts_specimen_launcher"},
        10507: {"scholo_deathbone_chestplate", "scholo_necropile_boots", "scholo_ancient_bone_bow",
                "scholo_corvanes_goad"},
        10504: {"scholo_bloodmail_hauberk", "scholo_libram_of_divinity", "scholo_barov_heirs_breastplate",
                "scholo_the_deans_rod"},
        10502: {"scholo_necropile_cuffs", "scholo_bloodmail_legguards", "scholo_totem_of_sustaining",
                "scholo_shroud_of_foresight"},
        1853: {"scholo_headmasters_charge", "scholo_don_mauricios_band", "scholo_witchblade", "scholo_silent_fang",
               "scholo_vigorsteel_vambraces", "scholo_bonecreeper_stylus", "scholo_boots_of_the_shrieker",
               "scholo_detention_strap"},
    }

    def test_each_boss_drops_its_own_items(self):
        by_key = self.groups(1)
        self.assertEqual(sum(len(v) for v in self.LISTS.values()), 52)
        for name, (normal, heroic, *_rest) in self.BOSSES.items():
            for lootid in (normal, heroic):
                with self.subTest(boss=name, lootid=lootid):
                    self.assertEqual(set(by_key[(lootid, 1)].items), self.LISTS[normal])

    def test_marduk_keeps_his_reagents_and_the_stock_rows_removed(self):
        lootids = {d.lootid for d in self.lists}
        self.assertNotIn(10433, lootids)
        self.assertNotIn(310070, lootids)
        # F-C4 ruling: Marduk keeps lootid 10433 and its group 0 (no row removal there); only group 1 goes, and his
        # heroic body (310070) drops the copy of that group 0
        self.assertEqual([(d.lootid, d.why != "") for d in self.copies], [(310070, True)])
        rows = {(d.lootid, d.group): d.rows for d in self.row_removals}
        self.assertNotIn(10433, {lootid for lootid, _ in rows})
        self.assertEqual(rows[(1853, 0)], (13950,))
        self.assertEqual(rows[(10503, 0)], (14543,))
        trash = {k: v for k, v in rows.items() if k[0] not in (1853, 10503)}
        self.assertEqual(len(trash), 12)
        self.assertEqual(sum(len(v) for v in trash.values()), 14)
        self.assertTrue(all(group == 0 for _, group in rows))
        # the Tier 0 trash drops are sets 181-189 items, the group 1 replacements only on the normal lootids
        tier_0 = {16684, 16685, 16710, 16702, 16705, 16671, 16722, 16714, 16716}
        self.assertTrue(all(set(v) <= tier_0 for v in trash.values()))
        replaced = {d.lootid: d for d in self.lists if d.group == 1 and d.tier == "normal"}
        self.assertEqual(replaced[10508].replaces_references, (35030,))
        self.assertEqual(replaced[10504].replaces_references, (35095,))
        for lootid in (10505, 11261, 10901, 10507, 10502):
            self.assertEqual(replaced[lootid].replaces_references, (35031,), lootid)
        self.assertEqual(len(replaced[1853].replaces_items), 9)
        self.assertFalse(any(d.replaces_items or d.replaces_references for d in self.lists if d.tier != "normal"))

    def test_the_replaced_pools_are_deleted(self):
        # R-C LOOT S-1: nothing else uses the three stock pools, and an unused reference Entry is a boot ERROR
        self.assertEqual(sorted(d.reference for d in self.pool_removals), [35030, 35031, 35095])
        replaced = {r for d in self.lists for r in d.replaces_references}
        self.assertEqual(replaced, {35030, 35031, 35095})

if __name__ == "__main__":
    unittest.main()
