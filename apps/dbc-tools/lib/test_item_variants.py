"""
Item variants IV1 (.agents/plans/item-variants/item-variants.PLAN.md s3, s4, s5.3): the item DSL (lib/dsl/items.py),
the id lock (lib/item_ids.py) and the resolution checks (lib/item_variants.py), against fixture tables.

Covered: tier / ladder / item argument checks (labels, levels, only the first tier implicit, stat columns and keyword
columns rejected, the 0x8 flag, base= / like= / itemization="live" combinations, shares, fractions, spells, sockets,
overrides, a repeated key); the lock parser (malformed lines, repeats, block bounds, retired lines); id assignment
(stable across reruns, rename-safe, gaps never reused, taken ids skipped, a full block, deferred tiers minted only
when flipped, the file kept byte for byte); the retire guard (a dropped tier or item stops the run with the line to
write, a retired line is accepted and kept for IV2, a retired pair cannot come back, a dropped base is only reported);
check mode (the notes list the same lines a full run appends); one owner per entry (base= against item_template(),
items.csv, another item, the item block; a minted id another source declares; a live row in the block no line owns);
shapes (unknown, wrong kind, a secondary whose rules fail, the default secondary); slots (not budgetable, a shield
without an armor curve, armor passed on a curved slot, extra_armor / extra_dps / extra_block on the wrong slot);
ladder levels per item and the quality WARNING; missing curve rows; the itemization row per tier (defaults, absorbed
stock spells, the effect multiplier, fractions resolved per tier, "live" kept on the first tier and scaled above);
source/items/ loading as one package.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_item_variants.py
"""

from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import item_ids, item_variants, spell_tables  # noqa: E402
from lib.dsl import items as D  # noqa: E402
from lib.dsl import registry  # noqa: E402

BLOCK = {"start": 71000, "end": 79999}
IDS_CFG = {"item": {"start": 70000, "end": 79999}, "item_minted": BLOCK}
COLUMNS = tuple(spell_tables.ITEM_TEMPLATE_COLUMNS)
TODAY = "2026-11-06"

STR, AGI, SPI, DODGE, CRIT, HASTE, MP5, SP = 4, 3, 6, 13, 32, 36, 43, 45


def _shape_tables() -> dict:
    shapes = {
        0: ("Null (jewelry, 100% secondary)", 0, 1, []),
        6: ("Spirit/SpellPower, Spirit lead", 0, 3, [SPI, SP]),
        22: ("Strength (Solo)", 0, 1, [STR]),
        23: ("Agility (Solo)", 0, 1, [AGI]),
        25: ("Crit (Solo)", 1, 1, [CRIT]),
        26: ("Haste (Solo)", 1, 1, [HASTE]),
        47: ("MP5 (Solo)", 1, 1, [MP5]),
        54: ("Dodge (Solo)", 1, 1, [DODGE]),
    }
    tables = {"item_shape": {}, "item_shape_stat": {}, "item_shape_rule": {}}
    for shape_id, (name, kind, dist, stats) in shapes.items():
        tables["item_shape"][(shape_id,)] = {"shape_id": shape_id, "name": name, "kind": kind, "dist_id": dist}
        for rank, stat in enumerate(stats, 1):
            tables["item_shape_stat"][(shape_id, rank)] = {"stat_type": stat}
    for key in ((54, 1, AGI), (54, 1, STR), (47, 2, SPI)):
        tables["item_shape_rule"][key] = {}
    tables["item_alloc_dist"] = {(1, 1): {"alloc": 10000}, (3, 1): {"alloc": 6000}, (3, 2): {"alloc": 4000}}
    tables["item_alloc_dist_name"] = {(1,): {"name": "Solo"}, (3,): {"name": "Lead"}}
    return tables


def fixture_tables() -> dict:
    t = _shape_tables()
    levels = range(1, 301)
    t["item_slot_mult"] = {(inv,): {"mult": m} for inv, m in ((6, 0.5625), (11, 0.5625), (12, 0.5625), (13, 0.5625),
                                                                (14, 0.5625), (17, 1.0), (20, 1.0))}
    t["item_quality_mult"] = {(3,): {"mult": 1.0}, (4,): {"mult": 1.2}}
    t["item_budget_curve"] = {(i,): {"budget": 2.0 * i} for i in levels}
    t["item_stamina_curve"] = {(i,): {"stamina": 0.5 * i} for i in levels}
    t["item_armor_curve"] = {(i, c): {"armor": 10.0 * i} for i in levels for c in (1, 2, 3, 4)}
    t["item_armor_slot_mult"] = {(inv,): {"mult": m} for inv, m in ((6, 0.5625), (20, 1.0))}
    t["item_armor_quality_mult"] = {(3,): {"mult": 1.0}, (4,): {"mult": 1.1}}
    t["item_stat_cost"] = {}
    t["item_gem_value_curve"] = {(i,): {"gem_budget": 1.0 * i} for i in levels}
    t["item_block_value_curve"] = {(i, q): {"block_value": 1.0 * i} for i in levels for q in (3, 4)}
    t["item_budget_set_discount"] = {(1,): {"discount": 0.9}}
    t["item_weapon_dps_curve"] = {(i, q, s): {"dps": i * (1.3 if s else 1.0) + q} for i in levels for q in (3, 4)
                                  for s in (0, 1)}
    t["item_weapon_dps_cost"] = {(1,): {"cost": 1.0}}
    t["item_weapon_dps_spread"] = {(1,): {"spread": 0.3}}
    t["item_itemization"] = {(5192,): {
        "entry": 5192, "budget_mult": 0.718, "stamina_delta": 2, "dps_delta": -0.5, "absorbed_spell_slots": 0,
        "armor_delta": 0, "primary_shape_id": 23, "secondary_shape_id": 47, "primary_share": 10000,
        "block_value_delta": 0,
    }}
    return t


def _row(entry: int, **cols) -> dict:
    row = dict(spell_tables.ITEM_TEMPLATE_DEFAULTS)
    row.update(entry=entry, name=f"Item {entry}", Quality=3, ItemLevel=20, RequiredLevel=15)
    row.update(cols)
    return row


def live_rows() -> dict[int, dict]:
    return {
        5187: _row(5187, **{"class": 2, "subclass": 5, "InventoryType": 17, "delay": 3000, "displayid": 1}),
        5192: _row(5192, ItemLevel=22, **{"class": 2, "subclass": 7, "InventoryType": 13, "delay": 1800}),
        10403: _row(10403, ItemLevel=22, itemset=161, spellid_1=9330, spelltrigger_1=1,
                    **{"class": 4, "subclass": 2, "InventoryType": 6, "displayid": 777, "Material": 8}),
        1156: _row(1156, ItemLevel=22, **{"class": 4, "subclass": 0, "InventoryType": 11}),
        5443: _row(5443, **{"class": 4, "subclass": 6, "InventoryType": 14}),
        6087: _row(6087, **{"class": 4, "subclass": 4, "InventoryType": 6, "displayid": 4242, "Material": 6,
                            "sheath": 0, "SoundOverrideSubclass": -1}),
    }


def ladder_dungeon(**extra) -> D.Ladder:
    return D.ladder(
        "vanilla_dungeon",
        normal=D.tier(step=0, label="Normal"),
        heroic=D.tier(step=1, ilvl=66, quality=D.Quality.EPIC, required_level=60, heroic_flag=True, label="Heroic"),
        empowered_1=D.tier(step=2, ilvl=76, quality=D.Quality.EPIC, required_level=60, label="Molten Empowered",
                           **extra),
    )


HARD_MODE = D.ladder(
    "vanilla_hard_mode",
    heroic_hm=D.tier(step=1, ilvl=71, quality=D.Quality.EPIC, required_level=60, label="Heroic Hard Mode"),
    empowered_1_hm=D.tier(step=2, ilvl=81, quality=D.Quality.EPIC, required_level=60,
                          label="Molten Empowered Hard Mode"),
)


def decls(*items: D.ItemDecl) -> list[dict]:
    return [{"id": d.key, "_decl": d} for d in items]


def run(items, lock_text: str = "", rows=None, tables=None, **kwargs) -> item_variants.ItemExpansion:
    tables = tables or fixture_tables()
    kwargs.setdefault("labels_loader", dict)  # never the real client label table
    from item_lib import shapes  # noqa: PLC0415 - on the path once item_variants._item_lib() ran

    return item_variants.expand(
        decls(*items), ids_cfg=kwargs.pop("ids_cfg", IDS_CFG), live_rows=rows or live_rows(), columns=COLUMNS,
        tables_loader=lambda: (tables, shapes.catalog(tables)), lock=item_ids.Lock(text=lock_text), today=TODAY,
        **kwargs,
    )


item_variants._item_lib()  # puts apps/item-tools on sys.path for `run`


def hammer(**kw) -> D.ItemDecl:
    args = dict(base=5187, primary="Strength (Solo)", secondary="Crit (Solo)", ladder=ladder_dungeon())
    args.update(kw)
    return D.item("dm_hammer", **args)


def girdle(**kw) -> D.ItemDecl:
    args = dict(name="Doorman's Girdle", like=6087, ilvl=20, primary="Strength (Solo)", secondary="Haste (Solo)",
                ladder=ladder_dungeon())
    args.update(kw)
    return D.item("dm_girdle", **args)


def entries(exp) -> dict[tuple[str, str], int]:
    return {(t.key, t.tier): t.entry for item in exp.items for t in item.tiers}


# ---------------------------------------------------------------------------------------------------------------------


class DslTest(unittest.TestCase):
    def test_tier_label_rules(self):
        for bad in ("", " Normal", "Nor\"mal", "a|b", "x\ny"):
            with self.assertRaises(D.ItemDeclarationError):
                D.tier(step=0, label=bad)
        with self.assertRaises(D.ItemDeclarationError):
            D.tier(step=1, label="Heroic", ilvl=66)  # all three or none
        with self.assertRaises(D.ItemDeclarationError):
            D.tier(step=1, label="Heroic", ilvl=301, quality=4, required_level=60)
        with self.assertRaises(D.ItemDeclarationError):
            D.tier(step=1, label="Heroic", ilvl=66, quality=9, required_level=60)

    def test_tier_step_is_explicit(self):
        with self.assertRaises(TypeError):
            D.tier(label="Normal")  # step= is required
        for bad in (-1, 256, 1.0, True, "1"):
            with self.assertRaisesRegex(D.ItemDeclarationError, "step="):
                D.tier(step=bad, label="Normal")
        self.assertEqual(D.tier(step=3, label="X", ilvl=86, quality=4, required_level=60).step, 3)

    def test_ladder_rules(self):
        normal = D.tier(step=0, label="Normal")
        heroic = D.tier(step=1, ilvl=66, quality=4, required_level=60, label="Heroic")
        with self.assertRaisesRegex(D.ItemDeclarationError, "only the first tier"):
            D.ladder("l", heroic=heroic, normal=normal)
        with self.assertRaisesRegex(D.ItemDeclarationError, "strictly increase"):
            D.ladder("l", a=heroic, b=D.tier(step=2, ilvl=66, quality=4, required_level=60, label="B"))
        with self.assertRaisesRegex(D.ItemDeclarationError, "share a label"):
            D.ladder("l", a=normal, b=D.tier(step=1, ilvl=66, quality=4, required_level=60, label="Normal"))
        with self.assertRaises(D.ItemDeclarationError):
            D.ladder("Bad Name", a=normal)
        with self.assertRaisesRegex(D.ItemDeclarationError, "steps must strictly increase"):
            D.ladder("l", a=normal, b=D.tier(step=0, ilvl=66, quality=4, required_level=60, label="B"))
        lad = D.ladder("l", normal=normal, heroic=heroic)
        self.assertEqual(lad.names, ("normal", "heroic"))
        self.assertEqual(lad.tier("heroic").label, "Heroic")

    def test_stat_columns_rejected(self):
        for column in ("stat_type1", "stat_value10", "dmg_min1", "dmg_max2", "block"):
            with self.assertRaisesRegex(D.ItemDeclarationError, "itemization budget"):
                hammer(**{column: 5})
        with self.assertRaisesRegex(D.ItemDeclarationError, "itemization budget"):
            hammer(overrides={"heroic": {"stat_value1": 3}})

    def test_keyword_columns_and_heroic_flag(self):
        with self.assertRaisesRegex(D.ItemDeclarationError, "ilvl="):
            hammer(ItemLevel=30)
        with self.assertRaisesRegex(D.ItemDeclarationError, "spells="):
            hammer(spellid_1=123)
        with self.assertRaisesRegex(D.ItemDeclarationError, "0x8"):
            hammer(Flags=0x8)
        hammer(Flags=0x80000)  # other flags are fine

    def test_item_argument_rules(self):
        with self.assertRaisesRegex(D.ItemDeclarationError, "exclude"):
            hammer(like=6087)
        with self.assertRaisesRegex(D.ItemDeclarationError, "needs name="):
            girdle(name=None)
        with self.assertRaisesRegex(D.ItemDeclarationError, "needs ilvl="):
            girdle(ilvl=None)
        with self.assertRaisesRegex(D.ItemDeclarationError, "needs base="):
            girdle(itemization="live", primary=None, secondary=None)
        with self.assertRaisesRegex(D.ItemDeclarationError, "drop primary"):
            hammer(itemization="live")
        with self.assertRaisesRegex(D.ItemDeclarationError, "primary_share"):
            hammer(primary_share=5000)
        with self.assertRaisesRegex(D.ItemDeclarationError, "primary_share 0"):
            hammer(primary=None, primary_share=6000)
        with self.assertRaisesRegex(D.ItemDeclarationError, "fraction"):
            hammer(extra_stamina=5)
        with self.assertRaisesRegex(D.ItemDeclarationError, "primary= and/or secondary="):
            hammer(primary=None, secondary=None)
        with self.assertRaisesRegex(D.ItemDeclarationError, "needs base="):
            girdle(keep_spells=True)
        with self.assertRaisesRegex(D.ItemDeclarationError, "drop keep_spells"):
            hammer(keep_spells=True, spells=(D.use_spell(1),))
        with self.assertRaisesRegex(D.ItemDeclarationError, "at most 3"):
            hammer(sockets=(D.Socket.RED,) * 4)
        with self.assertRaisesRegex(D.ItemDeclarationError, "socket_bonus"):
            hammer(socket_bonus=3312)
        with self.assertRaisesRegex(D.ItemDeclarationError, "does not have"):
            hammer(overrides={"mythic": {"itemset": 0}})
        with self.assertRaisesRegex(D.ItemDeclarationError, "stock row itself"):
            hammer(overrides={"normal": {"itemset": 0}})
        with self.assertRaisesRegex(D.ItemDeclarationError, "sets every tier"):
            D.item("hm", name="X", like=1156, ilvl=70, secondary="Crit (Solo)", ladder=HARD_MODE)
        with self.assertRaisesRegex(D.ItemDeclarationError, "first tier"):
            D.item("hm", base=1156, secondary="Crit (Solo)", ladder=HARD_MODE)

    def test_repeated_key_in_one_load(self):
        reg = registry.Registry()
        registry._active = reg
        try:
            hammer()
            with self.assertRaises(registry.DuplicateIdError):
                hammer()
        finally:
            registry._active = None
        self.assertEqual([e["id"] for e in reg.item_declarations], ["dm_hammer"])


class LockParseTest(unittest.TestCase):
    def test_parses_every_line_form(self):
        lock = item_ids.parse_lock(
            "# header\n\n5187 dm_hammer normal base\n71000 dm_hammer heroic\n"
            "71001 dm_old heroic retired 2026-11-01 4 2 -1 8 777 6 0\n1156 dm_ring normal base retired 2026-11-02\n",
            BLOCK,
        )
        by = lock.by_pair
        self.assertTrue(by[("dm_hammer", "normal")].base)
        self.assertEqual(by[("dm_hammer", "heroic")].entry, 71000)
        self.assertEqual(by[("dm_old", "heroic")].dbc_row()["displayid"], 777)
        self.assertEqual(by[("dm_ring", "normal")].retired, "2026-11-02")

    def test_bad_lines(self):
        for text, why in (
            ("71000 dm_hammer\n", "expected"),
            ("71000 dm_a heroic\n71000 dm_b heroic\n", "already on line"),
            ("71000 dm_a heroic\n71001 dm_a heroic\n", "already on line"),
            ("70500 dm_a heroic\n", "outside"),
            ("71000 dm_a normal base\n", "inside"),
            ("71000 dm_a heroic retired 2026-11-01 4 2\n", "Item.dbc fields"),
            ("71000 dm_a heroic retired yesterday\n", "may follow"),
            ("1156 dm_a normal base retired 2026-11-01 1 2 3 4 5 6 7\n", "no Item.dbc fields"),
        ):
            with self.subTest(text=text), self.assertRaisesRegex(item_ids.LockError, why):
                item_ids.parse_lock(text, BLOCK)


class IdTest(unittest.TestCase):
    def test_stable_ids_and_byte_for_byte_lock(self):
        first = run([hammer(), girdle()])
        self.assertEqual(first.errors, [])
        self.assertEqual(entries(first), {
            ("dm_hammer", "normal"): 5187, ("dm_hammer", "heroic"): 71000, ("dm_hammer", "empowered_1"): 71001,
            ("dm_girdle", "normal"): 71002, ("dm_girdle", "heroic"): 71003, ("dm_girdle", "empowered_1"): 71004,
        })
        self.assertIn("5187 dm_hammer normal base", first.lock_appended)
        self.assertEqual(len(first.minted), 5)
        second = run([hammer(), girdle()], lock_text=first.lock_text)
        self.assertEqual(second.lock_appended, [])
        self.assertEqual(entries(second), entries(first))
        self.assertEqual(second.lock_text, first.lock_text)
        header = "# my header, kept\n71000 dm_hammer heroic"  # no trailing newline: kept, then a newline added
        kept = item_ids.lock_text(item_ids.parse_lock(header, BLOCK), ["71001 x heroic"])
        self.assertTrue(kept.startswith(header + "\n"))

    def test_rename_safe(self):
        first = run([hammer(), girdle()])
        renamed = run([
            hammer(primary="Agility (Solo)", secondary="Haste (Solo)", ilvl=21),
            girdle(name="Renamed Girdle", ilvl=22, secondary="Crit (Solo)"),
        ], lock_text=first.lock_text)
        self.assertEqual(renamed.errors, [])
        self.assertEqual(entries(renamed), entries(first))
        self.assertEqual(renamed.lock_appended, [])

    def test_order_of_declarations_does_not_move_locked_ids(self):
        first = run([hammer(), girdle()])
        swapped = run([girdle(), hammer()], lock_text=first.lock_text)
        self.assertEqual(entries(swapped), entries(first))

    def test_gaps_never_reused_and_taken_ids_skipped(self):
        lock = "71000 dm_old heroic retired 2026-11-01 4 2 -1 8 777 6 0\n71005 dm_other heroic retired " \
               "2026-11-01 4 2 -1 8 777 6 0\n"
        rows = live_rows()
        rows[71006] = _row(71006)  # someone else's row in the block: an ERROR, and never minted over
        exp = run([girdle()], lock_text=lock, rows=rows)
        self.assertTrue(any("71006" in e and "no item_ids.lock line owns" in e for e in exp.errors))
        exp = run([girdle()], lock_text=lock, items_csv_ids=[71006], item_dbc_ids_loader=lambda: [71007])
        self.assertEqual(sorted(entries(exp).values()), [71008, 71009, 71010])

    def test_block_full(self):
        exp = run([girdle()], ids_cfg={"item_minted": {"start": 71000, "end": 71001}})
        self.assertTrue(any("is full" in e for e in exp.errors))
        self.assertEqual(exp.lock_appended, [])

    def test_deferred_tier_minted_only_when_flipped(self):
        deferred = run([girdle(ladder=ladder_dungeon(deferred=True))])
        self.assertEqual(deferred.errors, [])
        self.assertNotIn(("dm_girdle", "empowered_1"), entries(deferred))
        self.assertEqual(len(deferred.minted), 2)
        flipped = run([girdle()], lock_text=deferred.lock_text)
        self.assertEqual(flipped.lock_appended, ["71002 dm_girdle empowered_1"])

    def test_retire_guard(self):
        first = run([hammer(), girdle()])
        rows = live_rows()
        rows[71003] = _row(71003, **{"class": 4, "subclass": 4, "InventoryType": 6, "displayid": 4242,
                                     "Material": 6, "sheath": 0, "SoundOverrideSubclass": -1})
        for i in (71000, 71001, 71002, 71004):
            rows[i] = _row(i)
        dropped = run([hammer()], lock_text=first.lock_text, rows=rows)
        msgs = [e for e in dropped.errors if "no longer declared" in e]
        self.assertEqual(len(msgs), 3)
        self.assertTrue(any("`71003 dm_girdle heroic retired 2026-11-06 4 4 -1 6 4242 6 0`" in e for e in msgs))
        self.assertEqual(dropped.lock_appended, [])
        # a dropped tier (now deferred) is the same
        deferred = ladder_dungeon(deferred=True)
        tier_dropped = run([hammer(ladder=deferred), girdle(ladder=deferred)], lock_text=first.lock_text, rows=rows)
        self.assertEqual(len(tier_dropped.errors), 2)  # both items' empowered_1
        self.assertTrue(all("empowered_1" in e for e in tier_dropped.errors))
        # retired: accepted, kept for IV2's item_dbc rows
        retired_text = first.lock_text.replace(
            "71004 dm_girdle empowered_1\n", "71004 dm_girdle empowered_1 retired 2026-11-06 4 4 -1 6 4242 6 0\n",
        )
        ok = run([hammer(), D.item("dm_girdle", name="G", like=6087, ilvl=20, primary="Strength (Solo)",
                                   ladder=D.ladder("other", normal=D.tier(step=0, label="Normal"),
                                                   heroic=ladder_dungeon().tier("heroic")))],
                 lock_text=retired_text, rows=rows)
        self.assertEqual(ok.errors, [])
        self.assertEqual([line.entry for line in ok.assignment.retired], [71004])
        # a retired pair cannot come back
        back = run([hammer(), girdle()], lock_text=retired_text, rows=rows)
        self.assertTrue(any("was retired on 2026-11-06" in e for e in back.errors))
        # a dropped base= item is only reported
        no_hammer = run([girdle()], lock_text=first.lock_text.replace("71000 dm_hammer heroic\n", "71000 dm_hammer "
                        "heroic retired 2026-11-06 2 5 -1 0 1 17 0\n").replace(
                        "71001 dm_hammer empowered_1\n", "71001 dm_hammer empowered_1 retired 2026-11-06 2 5 -1 0 1 "
                        "17 0\n"), rows=rows)
        self.assertEqual(no_hammer.errors, [])
        self.assertTrue(any("stock entry 5187" in n and "base retired 2026-11-06" in n for n in no_hammer.notes))

    def test_base_changes_are_errors(self):
        first = run([hammer()])
        other_base = run([hammer(base=1156, primary=None, secondary="Crit (Solo)")], lock_text=first.lock_text)
        self.assertTrue(any("records base=5187, not base=1156" in e for e in other_base.errors))
        now_new = run([D.item("dm_hammer", name="H", like=5187, ilvl=20, primary="Strength (Solo)",
                              ladder=ladder_dungeon())], lock_text=first.lock_text)
        self.assertTrue(any("records it as stock entry 5187" in e for e in now_new.errors))
        minted = run([girdle()])
        now_base = run([D.item("dm_girdle", base=6087, primary="Strength (Solo)", ladder=ladder_dungeon())],
                       lock_text=minted.lock_text)
        self.assertTrue(any("cannot become a stock item" in e for e in now_base.errors))

    def test_check_mode_reports_the_lines_a_full_run_writes(self):
        exp = run([hammer()])
        notes = item_variants.summary_notes(exp, check=True)
        self.assertEqual([n.split(": ", 2)[2] for n in notes if "would append" in n], exp.lock_appended)
        self.assertFalse(any("would append" in n for n in item_variants.summary_notes(exp, check=False)))

    def test_empty_source_and_lock_is_a_no_op(self):
        exp = item_variants.expand([], ids_cfg={}, live_rows={}, columns=COLUMNS, lock=item_ids.Lock(),
                                   tables_loader=lambda: self.fail("tables loaded for nothing"))
        self.assertEqual((exp.errors, exp.items, exp.lock_appended), ([], [], []))


class OwnerTest(unittest.TestCase):
    def test_one_owner_per_entry(self):
        exp = run([hammer()], item_template_decl_ids=[5187])
        self.assertTrue(any("also edited by item_template(5187" in e for e in exp.errors))
        exp = run([hammer()], items_csv_ids=[5187])
        self.assertTrue(any("source/items.csv" in e for e in exp.errors))
        exp = run([hammer(), D.item("dm_other", base=5187, primary="Strength (Solo)", ladder=ladder_dungeon())])
        self.assertTrue(any("already item 'dm_hammer'" in e for e in exp.errors))
        rows = live_rows()
        rows[70100] = _row(70100, **{"class": 4, "subclass": 0, "InventoryType": 11})
        exp = run([D.item("dm_ring", base=70100, secondary="Crit (Solo)", ladder=ladder_dungeon())], rows=rows)
        self.assertTrue(any("custom item block" in e for e in exp.errors))
        exp = run([girdle()], lock_text="71000 dm_girdle normal\n", items_csv_ids=[71000])
        self.assertTrue(any("minted entry 71000" in e for e in exp.errors))

    def test_ladder_name_used_twice(self):
        other = D.ladder("vanilla_dungeon", normal=D.tier(step=0, label="Normal"),
                         heroic=D.tier(step=1, ilvl=70, quality=4, required_level=60, label="Heroic"))
        exp = run([hammer(), girdle(ladder=other)])
        self.assertTrue(any("two different ladders" in e for e in exp.errors))


class CheckTest(unittest.TestCase):
    def assertError(self, exp, text):
        self.assertTrue(any(text in e for e in exp.errors), exp.errors)

    def test_shapes(self):
        self.assertError(run([hammer(primary="Strenght (Solo)")]), "did you mean ['Strength (Solo)'")
        self.assertError(run([hammer(primary="Crit (Solo)")]), "is not a primary shape")
        self.assertError(run([hammer(secondary="Agility (Solo)")]), "is not a secondary shape")
        rule = run([hammer(primary="Spirit/SpellPower, Spirit lead", secondary="MP5 (Solo)")])
        self.assertError(rule, "does not go with")
        dodge = run([hammer(primary="Spirit/SpellPower, Spirit lead", secondary="Dodge (Solo)")])
        self.assertError(dodge, "does not go with")
        default = run([hammer(secondary=None)])
        self.assertEqual(default.errors, [])
        tier = default.items[0].tiers[0]
        self.assertEqual((tier.itemization["secondary_shape_id"], tier.itemization["primary_share"]), (25, 10000))
        ring = run([D.item("dm_ring", base=1156, secondary="Crit (Solo)", ladder=ladder_dungeon())])
        self.assertEqual(ring.items[0].tiers[0].itemization["primary_shape_id"], 0)
        self.assertEqual(ring.items[0].tiers[0].itemization["primary_share"], 0)

    def test_slots(self):
        shield = run([D.item("dm_buckler", base=5443, primary="Strength (Solo)", secondary="Crit (Solo)",
                             ladder=ladder_dungeon())])
        self.assertError(shield, "shields wait for IV0b")
        tables = fixture_tables()
        del tables["item_slot_mult"][(13,)]
        self.assertError(run([D.item("dm_blade", base=5192, itemization="live", ladder=ladder_dungeon())],
                             tables=tables), "not budgetable")
        self.assertError(run([girdle(armor=100)]), "armor comes from the armor curve")
        self.assertError(run([hammer(extra_armor=0.1)]), "extra_armor= needs")
        self.assertError(run([girdle(extra_dps=0.1)]), "extra_dps= needs a weapon")
        self.assertError(run([girdle(extra_block=0.1)]), "extra_block= needs a shield")
        self.assertError(run([D.item("dm_girdle", name="G", ilvl=20, primary="Strength (Solo)",
                                     ladder=ladder_dungeon())]), "like=<stock entry> or the column(s)")
        self.assertError(run([hammer(base=99999)]), "base=99999 has no live item_template row")
        self.assertError(run([girdle(like=99999)]), "like=99999 has no live item_template row")
        self.assertError(run([girdle(NoSuchColumn=1)]), "no such item_template column(s): NoSuchColumn")

    def test_levels_per_item_and_quality_warning(self):
        self.assertError(run([girdle(ilvl=70)]), "does not rise above tier 'normal'")
        warned = run([girdle(quality=D.Quality.LEGENDARY)], tables={
            **fixture_tables(), "item_quality_mult": {(q,): {"mult": 1.0} for q in (3, 4, 5)},
            "item_armor_quality_mult": {(q,): {"mult": 1.0} for q in (3, 4, 5)},
        })
        self.assertEqual(warned.errors, [])
        self.assertTrue(any("lowers the quality (5 -> 4)" in w for w in warned.warnings))

    def test_the_inherited_column_warning_honors_declared_columns(self):
        rows = live_rows()
        rows[5187] = {**rows[5187], "fire_res": 10, "RandomProperty": 3306}
        warned = run([hammer()], rows=rows)
        self.assertTrue(any("carries fire_res=10, RandomProperty=3306" in w for w in warned.warnings), warned.warnings)
        cleared = run([hammer(fire_res=0, RandomProperty=0)], rows=rows)
        self.assertFalse(any("carries" in w for w in cleared.warnings), cleared.warnings)
        half = run([hammer(fire_res=0)], rows=rows)
        self.assertTrue(any("carries RandomProperty=3306;" in w for w in half.warnings), half.warnings)
        changed = run([hammer(fire_res=5, RandomProperty=0)], rows=rows)
        self.assertTrue(any("carries fire_res=5;" in w for w in changed.warnings), changed.warnings)
        # a unique-equipped item replaces the stock (or an earlier run's) category on every tier: no warning
        rows[5187] = {**rows[5187], "fire_res": 0, "RandomProperty": 0, "ItemLimitCategory": 1003}
        self.assertTrue(any("carries ItemLimitCategory=1003" in w for w in run([hammer()], rows=rows).warnings))
        unique = run([hammer(unique_equip=True)], rows=rows)
        self.assertFalse(any("carries" in w for w in unique.warnings), unique.warnings)

    def test_missing_curve_rows(self):
        tables = fixture_tables()
        del tables["item_budget_curve"][(76,)]
        del tables["item_weapon_dps_curve"][(66, 4, 1)]
        exp = run([hammer()], tables=tables)
        self.assertError(exp, "tier 'empowered_1': item_budget_curve has no ilvl 76")
        self.assertError(exp, "tier 'heroic': item_weapon_dps_curve has no (ilvl 66, Quality 4, single slot 1)")
        self.assertError(run([D.item("dm_blade", base=5192, itemization="live", ladder=ladder_dungeon())],
                             tables={**fixture_tables(), "item_itemization": {}}), "no live item_itemization row")

    def test_itemization_rows(self):
        exp = run([
            girdle(extra_stamina=0.25, extra_armor=-0.1),
            D.item("dm_belt", base=10403, primary="Agility (Solo)", secondary="Haste (Solo)", ladder=ladder_dungeon(),
                   overrides={"heroic": {"itemset": 0}}),
            D.item("dm_ring", base=1156, secondary="Crit (Solo)", ladder=ladder_dungeon(),
                   spells=(D.equip_spell(9330),)),
        ])
        self.assertEqual(exp.errors, [])
        girdle_tiers, belt, ring = (item.tiers for item in exp.items)
        normal, heroic, emp = girdle_tiers
        # stamina baseline = round(0.5 * ilvl * slot 0.5625 * quality); armor = round(10 * ilvl * 0.5625 * quality)
        self.assertEqual(normal.baselines["stamina"], 6)
        self.assertEqual(normal.itemization["stamina_delta"], 2)  # round(0.25 * 6) = 1.5 -> 2 (half away from 0)
        self.assertEqual(heroic.baselines["stamina"], round(0.5 * 66 * 0.5625 * 1.2))
        self.assertEqual(heroic.itemization["stamina_delta"], round(0.25 * heroic.baselines["stamina"]))
        self.assertEqual(heroic.itemization["armor_delta"], -round(0.1 * heroic.baselines["armor"]))
        self.assertEqual((normal.ilvl, normal.quality, normal.required_level), (20, 3, 15))
        self.assertEqual((heroic.ilvl, heroic.quality, heroic.required_level, heroic.heroic_flag), (66, 4, 60, True))
        self.assertFalse(heroic.writes_label)
        self.assertTrue(emp.writes_label)
        self.assertEqual([t.variant_base for t in girdle_tiers], [None, normal.entry, normal.entry])
        self.assertEqual(exp.items[0].like_columns["displayid"], 4242)
        self.assertNotIn("itemset", exp.items[0].like_columns)
        # stock spell slot 1 (9330) folded in; the heroic override is that tier's only
        self.assertEqual({t.itemization["absorbed_spell_slots"] for t in belt}, {1})
        self.assertEqual(belt[0].itemization["budget_mult"], 1.0)
        self.assertTrue(belt[0].stock)
        self.assertEqual((belt[1].columns, belt[2].columns), ({"itemset": 0}, {}))
        # an Equip effect pays 0.7 of the budget
        self.assertEqual(ring[0].itemization["budget_mult"], 0.7)
        self.assertEqual(ring[0].itemization["absorbed_spell_slots"], 0)

    def test_live_itemization_kept_then_scaled(self):
        exp = run([D.item("dm_blade", base=5192, itemization="live", ladder=ladder_dungeon())])
        self.assertEqual(exp.errors, [])
        normal, heroic, emp = exp.items[0].tiers
        live = fixture_tables()["item_itemization"][(5192,)]
        self.assertEqual(normal.itemization, {c: live[c] for c in item_variants.ITEMIZATION_COLUMNS})
        stamina_fraction = 2 / normal.baselines["stamina"]
        dps_fraction = -0.5 / normal.baselines["dps"]
        self.assertEqual(heroic.itemization["stamina_delta"], round(stamina_fraction * heroic.baselines["stamina"]))
        self.assertAlmostEqual(heroic.itemization["dps_delta"], round(dps_fraction * heroic.baselines["dps"], 4))
        self.assertEqual((heroic.itemization["primary_shape_id"], heroic.itemization["budget_mult"]), (23, 0.718))

    def test_hard_mode_ladder_mints_every_tier(self):
        exp = run([D.item("hm_fuse", name="Powder Keg Fuse", secondary="Crit (Solo)", ladder=HARD_MODE,
                          **{"class": 4, "subclass": 0, "InventoryType": 12, "displayid": 1})])
        self.assertEqual(exp.errors, [])
        self.assertEqual([(t.tier, t.entry, t.ilvl) for t in exp.items[0].tiers],
                         [("heroic_hm", 71000, 71), ("empowered_1_hm", 71001, 81)])
        self.assertEqual([t.label for t in exp.items[0].tiers], ["Heroic Hard Mode", "Molten Empowered Hard Mode"])


class LoadTest(unittest.TestCase):
    def test_source_items_is_one_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(D.load_items_dir(root / "missing")["item_declarations"], [])
            (root / "item_ids.lock").write_text("# header only\n")
            self.assertEqual(D.load_items_dir(root)["item_declarations"], [])
            (root / "ladders.py").write_text(textwrap.dedent("""
                from lib.dsl.items import ladder, tier
                LADDER = ladder("vanilla_dungeon", normal=tier(step=0, label="Normal"),
                                heroic=tier(step=1, ilvl=66, quality=4, required_level=60, label="Heroic"))
            """))
            (root / "deadmines.py").write_text(textwrap.dedent("""
                from lib.dsl.items import item
                from .ladders import LADDER
                item("dm_a", base=5187, primary="Strength (Solo)", ladder=LADDER)
                item("dm_b", base=872, primary="Strength (Solo)", ladder=LADDER)
            """))
            merged = D.load_items_dir(root)
            self.assertEqual([e["id"] for e in merged["item_declarations"]], ["dm_a", "dm_b"])
            first, second = (e["_decl"] for e in merged["item_declarations"])
            self.assertIs(first.ladder, second.ladder)
            (root / "shadowfang.py").write_text("from lib.dsl.items import item\nfrom .ladders import LADDER\n"
                                                "item('dm_a', base=3, primary='Strength (Solo)', ladder=LADDER)\n")
            with self.assertRaises(registry.DuplicateIdError):
                D.load_items_dir(root)


if __name__ == "__main__":
    unittest.main()
