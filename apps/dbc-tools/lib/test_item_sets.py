"""
Dungeon sets (lib/dsl/sets.py, lib/item_sets.py): item sets, set tokens and token vendors.

Checks:
  - the DSL: item_set() / set_token() / set_vendor() refuse bad thresholds, duplicates, tiers the ladder does not
    have, non-armor slots, owned token columns, and register under their own ids (a duplicate is a DuplicateIdError);
  - item sets: a stock set keeps its stock name and gets the declared bonuses (stock bonuses gone), a new set needs
    a name and an id from the `item_set` block, the item list is each piece's first tier, every tier of a piece must
    carry the set's itemset, a piece sits in one set only;
  - tokens: one row per non-deferred ladder tier, copied from the like= token, the tier's level and quality (the
    first tier: the token's own), the Heroic flag only on the heroic tier, the tier label on the others, one Item.dbc
    entry and one ItemExtendedCost row (one token of that tier) each, ids inside their blocks and never taken twice;
  - vendors: every tier of every piece of its sets at the token of the piece's slot and tier, ordered tier, slot,
    set; the 150 / 255 row limits; a slot no token buys is an error;
  - rendering: the three tables are emitted as DELETE + INSERT of the rows that differ from live, silent on a rerun,
    and the ItemSet / ItemExtendedCost rows pack into their client files.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_item_sets.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import dbcfile, item_sets, spell_tables, state  # noqa: E402
from lib import test_item_emit as E  # noqa: E402
from lib import test_item_variants as F  # noqa: E402
from lib.dsl import items as D  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.dsl import sets as S  # noqa: E402

IDS_CFG = {
    **F.IDS_CFG, "item_set_token": {"start": 70500, "end": 70599}, "item_set": {"start": 1000, "end": 1099},
    "item_extended_cost": {"start": 3000, "end": 3199},
}
TOKEN_LOOK = 22353


def live_rows() -> dict[int, dict]:
    rows = E.live_rows()
    rows[TOKEN_LOOK] = F._row(TOKEN_LOOK, name="Desecrated Helmet", Quality=4, ItemLevel=60, RequiredLevel=60,
                              bonding=1, stackable=1, **{"class": 15, "subclass": 0, "InventoryType": 0,
                                                         "displayid": 35336, "Material": -1})
    return rows


def stock_set(set_id: int = 161, name: str = "Defias Leather") -> dict:
    row = item_sets._empty_row(item_sets.ITEMSET)
    row.update(ID=set_id, Name_Lang_enUS=name, Name_Lang_Mask=item_sets.NAME_LANG_MASK, ItemID_1=10403,
               ItemID_2=10399, SetSpellID_1=7516, SetThreshold_1=2, SetSpellID_2=7517, SetThreshold_2=3)
    return row


def belt(**kw) -> D.ItemDecl:
    args = dict(base=10403, primary="Agility (Solo)", secondary="Crit (Solo)", ladder=F.ladder_dungeon())
    args.update(kw)
    return D.item("set_belt", **args)


def girdle(**kw) -> D.ItemDecl:
    args = dict(itemset=1000)
    args.update(kw)
    return F.girdle(**args)


def token(key: str = "tok_waist", slots=(6,), base: int = 70500, cost: int = 3000, **kw) -> S.SetTokenDecl:
    ladder = kw.pop("ladder", F.ladder_dungeon())
    names = [t.name for t in ladder.tiers if not t.deferred]
    args = dict(name="Haunted Belt", slots=slots, ladder=ladder, like=TOKEN_LOOK, ilvl=60,
                quality=D.Quality.RARE, required_level=0, description="Trade it.",
                entries={t: base + n for n, t in enumerate(names)}, costs={t: cost + n for n, t in enumerate(names)})
    args.update(kw)
    return S.set_token(key, **args)


def run(items, set_decls, rows=None, stock=None, creatures=()):
    rows = rows if rows is not None else live_rows()
    exp, em = E.run(items, rows=rows)
    assert not exp.errors and not em.errors, (exp.errors, em.errors)
    dsl = {"item_set_declarations": [{"id": ("x", n), "_decl": d} for n, d in enumerate(set_decls)],
           "spells": [{"id": 205700}, {"id": 205701}], "creature_templates": list(creatures)}
    out = item_sets.expand(dsl, exp, em, ids_cfg=IDS_CFG, live_item_rows=rows, base_dir=Path("/nonexistent"),
                           stock_sets={161: stock_set()} if stock is None else stock)
    return exp, em, out, dsl


VENDOR = {"entry": 300480, "npcflag": 128}


class DslTest(unittest.TestCase):
    def test_item_set_rules(self):
        S.item_set(1000, name="Ok", items=("a", "b", "c"), bonuses=((3, 205700),))
        with self.assertRaisesRegex(S.SetDeclarationError, "threshold"):
            S.item_set(1000, name="X", items=("a", "b"), bonuses=((3, 205700),))
        with self.assertRaisesRegex(S.SetDeclarationError, "twice"):
            S.item_set(1000, name="X", items=("a", "a"), bonuses=((1, 205700),))
        with self.assertRaisesRegex(S.SetDeclarationError, "bonuses"):
            S.item_set(1000, name="X", items=("a",), bonuses=())
        with self.assertRaisesRegex(S.SetDeclarationError, "bonus spell"):
            S.item_set(1000, name="X", items=("a", "b"), bonuses=((1, 205700), (2, 205700)))
        with self.assertRaisesRegex(S.SetDeclarationError, "17"):
            S.item_set(1000, name="X", items=tuple(f"i{n}" for n in range(18)), bonuses=((1, 205700),))

    def test_token_rules(self):
        token()
        with self.assertRaisesRegex(S.SetDeclarationError, "exactly the ladder's tiers"):
            token(entries={"normal": 70500})
        with self.assertRaisesRegex(S.SetDeclarationError, "armor InventoryTypes"):
            token(slots=(12,))
        with self.assertRaisesRegex(S.SetDeclarationError, "come from the declaration"):
            token(ItemLevel=60)
        with self.assertRaisesRegex(S.SetDeclarationError, "first tier"):
            token(ilvl=None)
        with self.assertRaisesRegex(S.SetDeclarationError, "distinct"):
            token(costs={"normal": 3000, "heroic": 3000, "empowered_1": 3002})

    def test_vendor_rules(self):
        S.set_vendor(300480, sets=(181,), tokens=("tok",))
        with self.assertRaisesRegex(S.SetDeclarationError, "sets="):
            S.set_vendor(300480, sets=(), tokens=("tok",))
        with self.assertRaisesRegex(S.SetDeclarationError, "tokens="):
            S.set_vendor(300480, sets=(181,), tokens=("tok", "tok"))
        with self.assertRaisesRegex(S.SetDeclarationError, "tiers="):
            S.set_vendor(300480, sets=(181,), tokens=("tok",), tiers=("heroic", "heroic"))
        with self.assertRaisesRegex(S.SetDeclarationError, "tiers="):
            S.set_vendor(300480, sets=(181,), tokens=("tok",), tiers=())

    def test_registers_under_own_ids(self):
        reg = registry.Registry()
        previous = registry._active
        registry._active = reg
        try:
            S.item_set(1000, name="X", items=("a",), bonuses=((1, 205700),))
            token()
            S.set_vendor(300480, sets=(1000,), tokens=("tok_waist",))
            with self.assertRaises(registry.DuplicateIdError):
                S.item_set(1000, name="Y", items=("b",), bonuses=((1, 205701),))
            with self.assertRaises(registry.DuplicateIdError):
                token()
        finally:
            registry._active = previous
        self.assertEqual([e["id"] for e in reg.item_set_declarations],
                         [("set", 1000), ("token", "tok_waist"), ("vendor", 300480)])


class ItemSetTest(unittest.TestCase):
    def test_stock_set_keeps_name_and_gets_the_bonuses(self):
        exp, _, out, dsl = run([belt()], [S.item_set(161, items=("set_belt",), bonuses=((1, 205700),))])
        self.assertFalse(out.errors, out.errors)
        (row,) = out.set_rows
        self.assertEqual((row["ID"], row["Name_Lang_enUS"], row["ItemID_1"], row["ItemID_2"]),
                         (161, "Defias Leather", 10403, 0))
        self.assertEqual([(row[f"SetSpellID_{n}"], row[f"SetThreshold_{n}"]) for n in (1, 2, 3)],
                         [(205700, 1), (0, 0), (0, 0)])  # the stock 7516 / 7517 bonuses are gone
        self.assertEqual(dsl["item_set_rows"], out.set_rows)

    def test_new_set_from_its_block_lists_first_tiers(self):
        exp, _, out, _ = run([girdle()], [S.item_set(1000, name="Protector's", items=("dm_girdle",),
                                                     bonuses=((1, 205700),))])
        self.assertFalse(out.errors, out.errors)
        first = exp.items[0].tiers[0].entry
        self.assertEqual((out.set_rows[0]["Name_Lang_enUS"], out.set_rows[0]["ItemID_1"]), ("Protector's", first))

    def test_new_set_rules(self):
        _, _, out, _ = run([girdle()], [S.item_set(1000, items=("dm_girdle",), bonuses=((1, 205700),))])
        self.assertIn("needs name=", " ".join(out.errors))
        _, _, out, _ = run([girdle(itemset=500)], [S.item_set(500, name="X", items=("dm_girdle",),
                                                              bonuses=((1, 205700),))])
        self.assertIn("item_set block", " ".join(out.errors))

    def test_every_tier_must_carry_the_set(self):
        _, _, out, _ = run([belt(overrides={"heroic": {"itemset": 0}})],
                           [S.item_set(161, items=("set_belt",), bonuses=((1, 205700),))])
        self.assertIn("tier 'heroic'", " ".join(out.errors))
        _, _, out, _ = run([girdle(itemset=0)], [S.item_set(1000, name="X", items=("dm_girdle",),
                                                             bonuses=((1, 205700),))])
        self.assertIn("has itemset 0", " ".join(out.errors))

    def test_one_set_per_piece_and_known_keys(self):
        _, _, out, _ = run([belt()], [S.item_set(161, items=("set_belt",), bonuses=((1, 205700),)),
                                      S.item_set(1000, name="X", items=("set_belt",), bonuses=((1, 205701),))])
        self.assertIn("already in item_set(161)", " ".join(out.errors))
        _, _, out, _ = run([belt()], [S.item_set(161, items=("nope",), bonuses=((1, 205700),))])
        self.assertIn("not a resolved item() key", " ".join(out.errors))

    def test_undeclared_bonus_spell_warns(self):
        _, _, out, _ = run([belt()], [S.item_set(161, items=("set_belt",), bonuses=((1, 99999),))])
        self.assertFalse(out.errors)
        self.assertIn("99999", " ".join(out.warnings))


class TokenTest(unittest.TestCase):
    def test_rows_per_tier(self):
        _, em, out, _ = run([belt()], [token()])
        self.assertFalse(out.errors, out.errors)
        rows = {r["entry"]: r for r in out.token_rows}
        self.assertEqual(sorted(rows), [70500, 70501, 70502])
        self.assertEqual([(rows[e]["ItemLevel"], rows[e]["Quality"], rows[e]["RequiredLevel"], rows[e]["Flags"])
                          for e in sorted(rows)], [(60, 3, 0, 0), (66, 4, 60, 8), (76, 4, 60, 0)])
        for row in rows.values():
            self.assertEqual((row["name"], row["class"], row["displayid"], row["bonding"], row["description"]),
                             ("Haunted Belt", 15, 35336, 1, "Trade it."))
        minted = {r["entry"] for r in em.template_rows}
        self.assertTrue(set(rows) <= minted)
        self.assertEqual({e["id"] for e in em.dbc_entries} & set(rows), set(rows))
        self.assertEqual({k: v for k, v in em.labels.items() if k in rows},
                         {70500: "Normal", 70502: "Molten Empowered"})  # Heroic is the flag's own line
        self.assertEqual([(c["ID"], c["ItemID_1"], c["ItemCount_1"]) for c in out.cost_rows],
                         [(3000, 70500, 1), (3001, 70501, 1), (3002, 70502, 1)])

    def test_deferred_tier_is_skipped(self):
        ladder = F.ladder_dungeon(deferred=True)
        _, _, out, _ = run([belt()], [token(ladder=ladder)])
        self.assertFalse(out.errors, out.errors)
        self.assertEqual(sorted(r["entry"] for r in out.token_rows), [70500, 70501])

    def test_ids_in_their_blocks_and_free(self):
        _, _, out, _ = run([belt()], [token(base=71000)])
        self.assertIn("item_set_token block", " ".join(out.errors))
        _, _, out, _ = run([belt()], [token(cost=2990)])
        self.assertIn("item_extended_cost block", " ".join(out.errors))
        _, _, out, _ = run([belt()], [token(), token(key="tok_other", cost=3010)])
        self.assertIn("already taken", " ".join(out.errors))
        _, _, out, _ = run([belt()], [token(), token(key="tok_other", base=70510)])
        self.assertIn("is also", " ".join(out.errors))

    def test_like_must_be_a_token(self):
        _, _, out, _ = run([belt()], [token(like=10403)])
        self.assertIn("not a class 15 token", " ".join(out.errors))


class VendorTest(unittest.TestCase):
    def decls(self, **vendor):
        return [S.item_set(161, items=("set_belt",), bonuses=((1, 205700),)),
                S.item_set(1000, name="X", items=("dm_girdle",), bonuses=((1, 205701),)),
                token(), S.set_vendor(300480, **{"sets": (1000, 161), "tokens": ("tok_waist",), **vendor})]

    def test_rows_tier_then_slot_then_set(self):
        exp, _, out, dsl = run([belt(), girdle()], self.decls(), creatures=[VENDOR])
        self.assertFalse(out.errors, out.errors)
        by_key = {item.decl.key: [t.entry for t in item.tiers] for item in exp.items}
        expected = []
        for n in range(3):
            expected += [(by_key["dm_girdle"][n], 3000 + n), (by_key["set_belt"][n], 3000 + n)]
        self.assertEqual([(r["item"], r["ExtendedCost"]) for r in out.vendor_rows], expected)
        self.assertEqual([r["slot"] for r in out.vendor_rows], list(range(6)))
        self.assertEqual({r["entry"] for r in out.vendor_rows}, {300480})
        self.assertEqual(dsl["npc_vendor_rows"], out.vendor_rows)
        self.assertEqual(len(dsl["item_extended_cost_rows"]), 3)

    def test_vendor_problems(self):
        _, _, out, _ = run([belt(), girdle()], self.decls(), creatures=[{"entry": 300480, "npcflag": 1}])
        self.assertIn("no vendor flag", " ".join(out.errors))
        _, _, out, _ = run([belt(), girdle()], self.decls())
        self.assertIn("no creature_template()", " ".join(out.warnings))
        decls = self.decls()
        decls[2] = token(slots=(8,))
        _, _, out, _ = run([belt(), girdle()], decls, creatures=[VENDOR])
        self.assertIn("no token buys", " ".join(out.errors))
        _, _, out, _ = run([belt(), girdle()], self.decls(sets=(1000, 777)), creatures=[VENDOR])
        self.assertIn("777 is not an item_set() id", " ".join(out.errors))

    def test_tier_split(self):
        exp, _, out, _ = run([belt(), girdle()], self.decls(tiers=("normal", "heroic")), creatures=[VENDOR])
        self.assertFalse(out.errors, out.errors)
        self.assertEqual([r["ExtendedCost"] for r in out.vendor_rows], [3000, 3000, 3001, 3001])
        self.assertEqual([r["slot"] for r in out.vendor_rows], [0, 1, 2, 3])
        decls = self.decls(tiers=("empowered_1",))
        decls.append(S.set_vendor(300481, sets=(1000, 161), tokens=("tok_waist",), tiers=("normal", "heroic")))
        _, _, out, _ = run([belt(), girdle()], decls, creatures=[VENDOR, {"entry": 300481, "npcflag": 128}])
        self.assertFalse(out.errors, out.errors)
        rows = {(r["entry"], r["ExtendedCost"]) for r in out.vendor_rows}
        self.assertEqual(rows, {(300480, 3002), (300481, 3000), (300481, 3001)})
        self.assertEqual(len(out.vendor_rows), 6)  # every tier sold once across the two vendors
        _, _, out, _ = run([belt(), girdle()], self.decls(tiers=("mythic",)), creatures=[VENDOR])
        self.assertIn("on no token's ladder", " ".join(out.errors))
        self.assertIn("sells nothing", " ".join(out.errors))

    def test_row_limits(self):
        old = item_sets.MAX_VENDOR_ITEMS, item_sets.MAX_VENDOR_ROWS
        try:
            item_sets.MAX_VENDOR_ITEMS, item_sets.MAX_VENDOR_ROWS = 4, 10
            _, _, out, _ = run([belt(), girdle()], self.decls(), creatures=[VENDOR])
            self.assertIn("first 4", " ".join(out.warnings))
            item_sets.MAX_VENDOR_ITEMS, item_sets.MAX_VENDOR_ROWS = 2, 5
            _, _, out, _ = run([belt(), girdle()], self.decls(), creatures=[VENDOR])
            self.assertIn("keeps 5", " ".join(out.errors))
        finally:
            item_sets.MAX_VENDOR_ITEMS, item_sets.MAX_VENDOR_ROWS = old

    def test_no_declarations_no_rows(self):
        _, em, out, dsl = run([belt()], [])
        self.assertFalse(out.declared)
        self.assertNotIn("item_set_rows", dsl)


class RenderTest(unittest.TestCase):
    def test_emit_then_silent(self):
        _, _, out, dsl = run([belt(), girdle()], VendorTest().decls(), creatures=[VENDOR])
        empty = spell_tables.SpellTableIndex({}, tables=item_sets.SET_TABLES)
        blocks, report = item_sets.render_blocks(empty, dsl)
        text = "\n".join(blocks)
        self.assertEqual(report, [])
        for table in ("itemset_dbc", "itemextendedcost_dbc", "npc_vendor"):
            self.assertIn(f"DELETE FROM `{table}`", text)
            self.assertIn(f"INSERT INTO `{table}`", text)
        live = {spec.name: [dict(r) for r in dsl[spec.registry_key]] for spec in item_sets.SET_TABLES}
        rerun = spell_tables.SpellTableIndex(live, emitted={k: v for k, v in live.items()},
                                             tables=item_sets.SET_TABLES)
        self.assertEqual(item_sets.render_blocks(rerun, dsl), ([], []))
        self.assertEqual(item_sets.differ_notes(rerun, dsl)[0],
                         "item sets: differ from live: 0 of 2 itemset_dbc, 0 of 3 itemextendedcost_dbc, "
                         "0 of 6 npc_vendor")
        self.assertIsNone(item_sets.not_live_warning(rerun, dsl))
        self.assertIn("11 itemset_dbc", item_sets.not_live_warning(empty, dsl))

    def test_prune_a_dropped_vendor_row(self):
        _, _, out, dsl = run([belt(), girdle()], VendorTest().decls(), creatures=[VENDOR])
        live = {spec.name: [dict(r) for r in dsl[spec.registry_key]] for spec in item_sets.SET_TABLES}
        index = spell_tables.SpellTableIndex(live, emitted=live, tables=item_sets.SET_TABLES)
        dsl["npc_vendor_rows"] = dsl["npc_vendor_rows"][1:]
        blocks, report = item_sets.render_blocks(index, dsl)
        self.assertEqual(len(report), 1)
        self.assertIn("removing npc_vendor", report[0])
        self.assertIn("DELETE FROM `npc_vendor`", blocks[0])

    @unittest.skipUnless((state.BASE_DBC_DIR / item_sets.ITEMSET.dbc_filename).is_file(), "no stock ItemSet.dbc")
    def test_client_rows_pack_into_the_stock_files(self):
        stock = item_sets.stock_set_rows(state.BASE_DBC_DIR)
        self.assertEqual(stock[181]["Name_Lang_enUS"], "Magister's Regalia")
        self.assertEqual(stock[181]["ItemID_1"], 16685)
        _, _, out, _ = run([girdle()], [S.item_set(1000, name="X", items=("dm_girdle",), bonuses=((1, 205700),)),
                                        token()], stock=stock)
        for table, rows in out.client_rows().items():
            base = dbcfile.read_dbc(state.BASE_DBC_DIR / table.dbc_filename, table)
            merged = {r["ID"]: r for r in base}
            merged.update(rows)
            packed = dbcfile.pack_client_dbc(table, list(merged.values()), base)
            path = Path(self.id().replace(".", "_") + table.dbc_filename)
            try:
                path.write_bytes(packed)
                back = {r["ID"]: r for r in dbcfile.read_dbc(path, table)}
            finally:
                path.unlink(missing_ok=True)
            for row_id, row in rows.items():
                self.assertEqual({c: back[row_id][c] for c in table.columns if c != "Name_Lang_Mask"},
                                 {c: row[c] for c in table.columns if c != "Name_Lang_Mask"})


if __name__ == "__main__":
    unittest.main()
