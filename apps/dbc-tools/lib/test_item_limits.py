"""
Item variants IV10 follow-up 1: one unique-equip ItemLimitCategory per effect item, shared by all its tiers
(lib/item_limits.py).

Checks:
  - which items get one: `spells=` (scaled or not), `keep_spells=True` on a stock row with a spell, the
    `unique_equip=` override both ways; plain stat items and absorbed stock stat spells stay unrestricted;
  - the DSL: `ItemLimitCategory` cannot be passed as a column, `unique_equip=` takes a bool;
  - ids: minted from the item_limit_category block, skipping taken ids, stable over a rerun on the written lock and
    over another declaration order; the retire guard (dropped item, unique_equip=False) and a retired line still
    emitting its row, with 0 on the tiers of an item still declared;
  - the rows (name, Quantity 1, Flags 1 equip mode, the stock name mask) and the tiers' column through item_emit: a
    minted row whole, a stock entry as an owned column;
  - ItemLimitCategory.dbc: the stock file reads back and a merged row round-trips through the client packer;
  - the real source: the three VanCleef hard mode items get one category each, no other Deadmines item does.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_item_limits.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import dbcfile, dbcfmt, item_emit, item_limits, state  # noqa: E402
from lib import test_item_emit as E  # noqa: E402
from lib import test_item_variants as F  # noqa: E402
from lib.dsl import items as D  # noqa: E402

IDS_CFG = {"item_limit_category": {"start": 1000, "end": 1999}}


def belt(**kw) -> D.ItemDecl:
    args = dict(base=10403, primary="Agility (Solo)", secondary="Crit (Solo)", ladder=F.ladder_dungeon())
    args.update(kw)
    return D.item("dm_belt", **args)


def run(items, lock_text: str = "", taken=(), rows=None):
    exp, _ = E.run(items, rows=rows)
    assert not exp.errors, exp.errors
    out = item_limits.expand(exp, IDS_CFG, lock=item_limits.Lock(text=lock_text), taken_loader=lambda: taken,
                             today="2026-11-06")
    return exp, out


def tier_values(exp) -> dict[str, list]:
    return {item.decl.key: [t.columns.get("ItemLimitCategory") for t in item.tiers] for item in exp.items}


class WhichItemsTest(unittest.TestCase):
    def test_effect_items_only(self):
        exp, out = run([E.trinket(), F.hammer(), belt(), F.girdle()])
        self.assertFalse(out.errors, out.errors)
        self.assertEqual(out.categories, {E.trinket().key: 1000})
        values = tier_values(exp)
        self.assertEqual(values[E.trinket().key], [1000, 1000])  # every tier of the item
        self.assertEqual(values["dm_hammer"], [None, None, None])  # plain stat items: no column at all
        self.assertEqual(values["dm_belt"], [None, None, None])  # 9330 is a stat equip folded into the budget

    def test_kept_stock_spell_counts_and_overrides(self):
        _, out = run([belt(keep_spells=True)])
        self.assertEqual(out.categories, {"dm_belt": 1000})
        _, out = run([belt(keep_spells=True, unique_equip=False), F.hammer(unique_equip=True)])
        self.assertEqual(out.categories, {"dm_hammer": 1000})
        _, out = run([E.trinket(unique_equip=False)])
        self.assertEqual((out.categories, out.rows, out.lock_appended), ({}, [], []))

    def test_dsl_rules(self):
        with self.assertRaisesRegex(D.ItemDeclarationError, "unique_equip="):
            E.trinket(ItemLimitCategory=5)
        with self.assertRaisesRegex(D.ItemDeclarationError, "unique_equip="):
            E.trinket(unique_equip=1)
        with self.assertRaisesRegex(D.ItemDeclarationError, "unique_equip="):
            F.hammer(overrides={"heroic": {"ItemLimitCategory": 0}})


class IdTest(unittest.TestCase):
    def test_mint_skip_and_rerun(self):
        hammer = F.hammer(unique_equip=True)
        _, first = run([E.trinket(), hammer], taken={1000})
        self.assertEqual(first.lock_appended, [f"1001 {E.trinket().key}", "1002 dm_hammer"])
        _, second = run([E.trinket(), F.hammer(unique_equip=True)], lock_text=first.lock_text)
        self.assertEqual((second.lock_appended, second.lock_text, second.categories),
                         ([], first.lock_text, first.categories))
        self.assertEqual(second.rows, first.rows)
        _, third = run([F.hammer(unique_equip=True), E.trinket()], lock_text=first.lock_text)
        self.assertEqual(third.categories, first.categories)
        self.assertTrue(first.lock_text.startswith("# Item limit categories"))

    def test_retire_guard(self):
        _, first = run([E.trinket()])
        _, dropped = run([F.hammer()], lock_text=first.lock_text)
        self.assertIn("is no longer declared", dropped.errors[0])
        self.assertIn("1000 hm_keg retired 2026-11-06", dropped.errors[0])
        _, off = run([E.trinket(unique_equip=False)], lock_text=first.lock_text)
        self.assertIn("is no longer unique-equipped", off.errors[0])
        retired = first.lock_text + ""
        retired = retired.replace("1000 hm_keg", "1000 hm_keg retired 2026-11-06 Old Keg")
        exp, still = run([E.trinket(unique_equip=False)], lock_text=retired)
        self.assertFalse(still.errors, still.errors)
        self.assertEqual([r["Name_Lang_enUS"] for r in still.rows], ["Old Keg"])  # owned copies keep the limit
        self.assertEqual(tier_values(exp)[E.trinket().key], [0, 0])
        _, again = run([E.trinket()], lock_text=retired)
        self.assertIn("was retired on 2026-11-06", again.errors[0])

    def test_lock_errors_and_full_block(self):
        for text, why in (("1000 a\n1000 b\n", "already on line"), ("1000 a\n1001 a\n", "already on line"),
                          ("999 a\n", "outside"), ("x a\n", "expected")):
            _, out = run([E.trinket()], lock_text=text)
            self.assertTrue(out.errors and why in out.errors[0], (text, out.errors))
        exp, _ = E.run([E.trinket(), F.hammer(unique_equip=True)])
        out = item_limits.expand(exp, {"item_limit_category": {"start": 1000, "end": 1000}}, lock=item_limits.Lock(),
                                 taken_loader=tuple)
        self.assertTrue(any("is full" in e for e in out.errors))


class RowTest(unittest.TestCase):
    def test_rows_and_item_columns(self):
        exp, out = run([E.trinket(), belt(keep_spells=True)])
        rows = {r["ID"]: r for r in out.rows}
        keg, kept = rows[out.categories[E.trinket().key]], rows[out.categories["dm_belt"]]
        self.assertEqual((keg["Name_Lang_enUS"], keg["Quantity"], keg["Flags"], keg["Name_Lang_Mask"]),
                         ("Powder Keg Fuse", 1, 1, 16712190))
        self.assertEqual(kept["Name_Lang_enUS"], "Item 10403")  # a base= item takes its stock name
        self.assertEqual(keg["Name_Lang_deDE"], "")
        self.assertEqual(set(keg) - {"id"}, set(dbcfmt.ITEMLIMITCATEGORY.columns))
        emission = item_emit.build(exp)
        by_entry = emission.by_entry()
        for item in exp.items:
            for tier in item.tiers:
                rows_for_tier = by_entry[tier.entry]
                self.assertEqual(rows_for_tier.row["ItemLimitCategory"], out.categories[item.decl.key])
                if tier.stock:
                    self.assertIn("ItemLimitCategory", rows_for_tier.owned)  # the stock entry's owned edit
        self.assertEqual(item_limits.client_rows(out.rows)[keg["ID"]]["Flags"], 1)

    def test_client_dbc_round_trip(self):
        path = state.BASE_DBC_DIR / dbcfmt.ITEMLIMITCATEGORY.dbc_filename
        if not path.is_file():
            self.skipTest(f"no stock {path.name} in {path.parent}")
        base = state.read_dbc_cached(path, dbcfmt.ITEMLIMITCATEGORY)
        self.assertEqual((len(base), max(r["ID"] for r in base)), (83, 85))
        self.assertLess(max(r["ID"] for r in base), IDS_CFG["item_limit_category"]["start"])
        row = item_limits.client_rows([item_limits.category_row(1000, "Powder Keg Fuse")])
        merged = {r["ID"]: r for r in base}
        merged.update(row)
        blob = dbcfile.pack_client_dbc(dbcfmt.ITEMLIMITCATEGORY, list(merged.values()), base)
        out = Path(self.id().replace(".", "_") + ".dbc")
        tmp = Path(__import__("tempfile").mkdtemp()) / out
        tmp.write_bytes(blob)
        back = {r["ID"]: r for r in dbcfile.read_dbc(tmp, dbcfmt.ITEMLIMITCATEGORY)}
        self.assertEqual(back[1000]["Name_Lang_enUS"], "Powder Keg Fuse")
        self.assertEqual((back[1000]["Quantity"], back[1000]["Flags"]), (1, 1))
        self.assertEqual(back[85]["Name_Lang_enUS"], "Charred Twilight Scale")

    def test_missing_base_file(self):
        self.assertIsNone(item_limits.base_file_error([], Path("/nonexistent")))
        self.assertIn("docker cp", item_limits.base_file_error([{"ID": 1000}], Path("/nonexistent")))


class RealSourceTest(unittest.TestCase):
    def test_the_hard_mode_items_and_nothing_else(self):
        from lib import test_hard_mode_item_effects as hm  # noqa: PLC0415

        reg = hm._load_items_registry()
        decls = [e["_decl"] for e in reg.item_declarations]
        unique = sorted(d.key for d in decls if (d.unique_equip if d.unique_equip is not None else bool(d.spells)
                                                 or d.keep_spells))
        self.assertEqual(unique, ["dm_blackguards_signet", "dm_lantern_of_the_roaring_flame", "dm_powder_keg_fuse"])
        self.assertIn("item_limit_category", hm.id_blocks.IDS)


if __name__ == "__main__":
    unittest.main()
