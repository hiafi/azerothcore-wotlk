"""
Item variants IV2 (.agents/plans/item-variants/item-variants.PLAN.md s5): the emission in lib/item_emit.py, against
the fixture tables of lib/test_item_variants.py.

Covered: a `base=` weapon (owned-column edit of the stock entry, full minted rows above it, flag 0x8 on the Heroic
tier only, labels without the Heroic tier); the stats of every tier equal `compute_breakdown` on the emitted row; no
stat line of value 0 (a Null-primary ring, a `secondary=None` item); sockets and the socket bonus on every tier, with
the socket discount in the budget; a shield takeover keeps its live `armor_delta` on the Normal tier while the minted
tiers take the curve; a trinket with a Use spell at `budget_mult` 0.7 carries the spell on every tier; absorbed stock
spells cleared in the minted rows only; `item_budget_variant` rows and tier numbers (the hard mode ladder starts at
1); Item.dbc entries equal the template (minted, retired, a stock entry only when its Item.dbc fields change); a
duplicate Item.dbc id; the rendered SQL passes the real codestyle-sql.py; a second run over the replayed first run
renders nothing.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_item_emit.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import item_emit, item_variants, spell_tables, sql_dump, sql_out  # noqa: E402
from lib import test_item_variants as F  # noqa: E402
from lib.dsl import items as D  # noqa: E402
from lib.table_testkit import codestyle_sql  # noqa: E402

item_variants._item_lib()
from item_lib import budget, shapes  # noqa: E402

TEMPLATE_COLUMNS = tuple(spell_tables.ITEM_TEMPLATE_COLUMNS)
STAMINA = 7


def tables() -> dict:
    t = F.fixture_tables()
    for i in range(1, 301):
        t["item_armor_curve"][(i, 6)] = {"armor": 20.0 * i}
    t["item_armor_slot_mult"][(14,)] = {"mult": 1.0}
    t["item_itemization"][(5443,)] = {
        "entry": 5443, "budget_mult": 1.0, "stamina_delta": 0, "dps_delta": 0.0, "absorbed_spell_slots": 0,
        "armor_delta": 14, "primary_shape_id": 22, "secondary_shape_id": 25, "primary_share": 6000,
        "block_value_delta": 0,
    }
    t["item_budget_variant"] = {}
    return t


def live_rows() -> dict[int, dict]:
    rows = F.live_rows()
    rows[5443].update(armor=471, block=9, displayid=18484, Material=6, sheath=4)
    rows[5187].update(displayid=8586, Material=1, sheath=1, SoundOverrideSubclass=-1)
    rows[19147] = F._row(19147, **{"class": 4, "subclass": 0, "InventoryType": 12, "displayid": 31664,
                                    "Material": 3})
    return rows


def run(items, rows=None, tbl=None, lock_text=""):
    tbl = tbl if tbl is not None else tables()
    rows = rows if rows is not None else live_rows()
    exp = item_variants.expand(
        F.decls(*items), ids_cfg=F.IDS_CFG, live_rows=rows, columns=TEMPLATE_COLUMNS,
        tables_loader=lambda: (tbl, shapes.catalog(tbl)), lock=item_variants.item_ids.Lock(text=lock_text),
        today=F.TODAY, labels_loader=dict,
    )
    return exp, item_emit.build(exp)


def lines(row: dict) -> list[tuple[int, int]]:
    return [(row[f"stat_type{n}"], row[f"stat_value{n}"]) for n in range(1, 11) if row[f"stat_type{n}"]]


def shield(**kw) -> D.ItemDecl:
    args = dict(base=5443, primary="Strength (Solo)", secondary="Crit (Solo)", ladder=F.ladder_dungeon())
    args.update(kw)
    return D.item("dm_buckler", **args)


def ring(**kw) -> D.ItemDecl:
    args = dict(base=1156, secondary="Crit (Solo)", ladder=F.ladder_dungeon())
    args.update(kw)
    return D.item("dm_ring", **args)


def trinket(**kw) -> D.ItemDecl:
    args = dict(name="Powder Keg Fuse", like=19147, primary="Agility (Solo)", secondary="Crit (Solo)",
                spells=(D.use_spell(205400, cooldown=120000),), ladder=F.HARD_MODE)
    args.update(kw)
    return D.item("hm_keg", **args)


def all_items():
    return (F.hammer(), F.girdle(sockets=(D.Socket.RED, D.Socket.BLUE), socket_bonus=3312), shield(), ring(),
            trinket(), D.item("dm_belt", base=10403, primary="Agility (Solo)", secondary="Haste (Solo)",
                              ladder=F.ladder_dungeon(), overrides={"heroic": {"itemset": 0}}))


class EmissionRowsTest(unittest.TestCase):
    def test_stock_weapon_edit_and_minted_tiers(self):
        exp, em = run([F.hammer()])
        self.assertEqual(em.errors, [])
        by = em.by_entry()
        self.assertEqual(sorted(by), [5187, 71000, 71001])
        stock = by[5187]
        self.assertIsNotNone(stock.owned)
        self.assertIn("dmg_min1", stock.owned)
        self.assertIn("stat_value10", stock.owned)
        for column in ("ItemLevel", "Quality", "RequiredLevel", "name", "Flags", "spellid_1", "socketColor_1",
                       "armor", "displayid"):
            self.assertNotIn(column, stock.owned)
        [edit] = em.template_edits
        self.assertEqual(edit["entry"], 5187)
        self.assertEqual(set(edit["_update_columns"]), set(stock.owned))
        heroic, emp = by[71000].row, by[71001].row
        self.assertEqual((heroic["ItemLevel"], heroic["Quality"], heroic["RequiredLevel"]), (66, 4, 60))
        self.assertEqual(heroic["Flags"] & D.HEROIC_TOOLTIP_FLAG, D.HEROIC_TOOLTIP_FLAG)
        self.assertEqual(emp["Flags"] & D.HEROIC_TOOLTIP_FLAG, 0)
        self.assertEqual(heroic["name"], "Item 5187")
        self.assertEqual(heroic["displayid"], 8586)
        self.assertEqual([r["entry"] for r in em.template_rows], [71000, 71001])
        self.assertEqual(em.labels, {5187: "Normal", 71001: "Molten Empowered"})

    def test_stats_equal_compute_breakdown_per_tier(self):
        tbl = tables()
        exp, em = run(all_items(), tbl=tbl)
        self.assertEqual(em.errors, [])
        catalog = shapes.catalog(tbl)
        self.assertEqual(len(em.tiers), 17)
        for tier_rows in em.tiers:
            row = tier_rows.row
            b = budget.compute_breakdown(row, {"entry": row["entry"], **tier_rows.tier.itemization}, tbl, catalog)
            want = [(a["stat_type"], a["rounded"]) for a in b["allocations"]] + [(STAMINA, b["final_stamina"])]
            self.assertEqual(lines(row), [w for w in want if w[1]], tier_rows.tier)
            if b["has_armor_curve"]:
                self.assertEqual(row["armor"], b["final_armor"] + b.get("bonus_armor", 0))
            if b["has_block_value_curve"]:
                self.assertEqual(row["block"], b["final_block_value"])
            if b["is_weapon"]:
                self.assertEqual((row["dmg_min1"], row["dmg_max1"]), (b["dmg_min"], b["dmg_max"]))
                self.assertGreater(row["dmg_max1"], row["dmg_min1"])
            self.assertEqual(row["ItemLevel"], tier_rows.tier.ilvl)

    def test_no_zero_stat_lines(self):
        # Null primary (no stats) and a primary-only item (the default secondary gets no budget).
        exp, em = run([ring(), F.hammer(secondary=None)])
        self.assertEqual(em.errors, [])
        hammer_tier = em.by_entry()[5187]
        self.assertIn(0, [a["rounded"] for a in hammer_tier.breakdown["allocations"]])  # the C++ would write it
        for tier_rows in em.tiers:
            self.assertTrue(all(value for _, value in lines(tier_rows.row)), tier_rows.tier)
            self.assertNotIn(F.CRIT, [t for t, _ in lines(tier_rows.row)] if tier_rows.tier.key == "dm_hammer"
                             else [])
        ring_itemization = em.by_entry()[1156].tier.itemization
        self.assertEqual((ring_itemization["primary_shape_id"], ring_itemization["primary_share"]), (0, 0))

    def test_sockets_on_every_tier_with_the_discount(self):
        socketed = F.girdle(sockets=(D.Socket.RED, D.Socket.BLUE), socket_bonus=3312)
        _, em = run([socketed])
        _, plain = run([F.girdle()])
        for tier_rows, plain_rows in zip(em.tiers, plain.tiers):
            row = tier_rows.row
            self.assertEqual((row["socketColor_1"], row["socketColor_2"], row["socketColor_3"]), (2, 8, 0))
            self.assertEqual(row["socketBonus"], 3312)
            self.assertEqual(tier_rows.breakdown["socket_count"], 2)
            self.assertLess(tier_rows.breakdown["budget"], plain_rows.breakdown["budget"])

    def test_tier_without_sockets(self):
        lad = D.ladder(
            "vanilla_dungeon",
            normal=D.tier(step=0, label="Normal", sockets=False),
            heroic=D.tier(step=1, ilvl=66, quality=D.Quality.EPIC, required_level=60, heroic_flag=True, label="Heroic"),
        )
        socketed = F.girdle(sockets=(D.Socket.RED, D.Socket.BLUE), socket_bonus=3312, ladder=lad)
        exp, em = run([socketed])
        self.assertEqual(em.errors, [])
        _, plain = run([F.girdle(ladder=lad)])
        normal, heroic = em.tiers
        self.assertFalse(normal.tier.sockets)
        self.assertEqual([normal.row[c] for c in item_emit.SOCKET_COLUMNS], [0] * 7)
        self.assertEqual(normal.breakdown["socket_count"], 0)
        self.assertEqual(normal.breakdown["budget"], plain.tiers[0].breakdown["budget"])  # no socket discount
        self.assertEqual((heroic.row["socketColor_1"], heroic.row["socketColor_2"], heroic.row["socketBonus"]),
                         (2, 8, 3312))
        self.assertEqual(heroic.breakdown["socket_count"], 2)
        # A stock entry with stock sockets: the switch clears (and owns) its socket columns.
        rows = live_rows()
        rows[5187].update(socketColor_1=2, socketBonus=2874)
        _, stock = run([F.hammer(ladder=lad)], rows=rows)
        tier = stock.by_entry()[5187]
        self.assertIn("socketColor_1", tier.owned)
        self.assertEqual((tier.row["socketColor_1"], tier.row["socketBonus"]), (0, 0))
        self.assertEqual(stock.by_entry()[71000].row["socketColor_1"], 2)
        with self.assertRaises(D.ItemDeclarationError):
            D.tier(step=0, label="Normal", sockets="no")

    def test_shield_takeover_keeps_its_pin_on_normal_only(self):
        _, em = run([shield()])
        by = em.by_entry()
        self.assertEqual(by[5443].tier.itemization["armor_delta"], 14)
        self.assertEqual(by[5443].row["armor"], 20 * 20 + 14)
        self.assertIn("armor", by[5443].owned)
        self.assertIn("block", by[5443].owned)
        for entry in (71000, 71001):
            self.assertEqual(by[entry].tier.itemization["armor_delta"], 0)
            self.assertEqual(by[entry].row["armor"], by[entry].breakdown["baseline_armor"])
        _, declared = run([shield(extra_armor=0.1)])
        self.assertEqual(declared.by_entry()[5443].tier.itemization["armor_delta"], 40)

    def test_trinket_effect_on_every_tier(self):
        _, em = run([trinket()])
        self.assertEqual(em.errors, [])
        self.assertEqual(len(em.tiers), 2)
        for tier_rows in em.tiers:
            row = tier_rows.row
            self.assertEqual(tier_rows.tier.itemization["budget_mult"], 0.7)
            self.assertEqual((row["spellid_1"], row["spelltrigger_1"], row["spellcooldown_1"]), (205400, 0, 120000))
            self.assertEqual((row["spellid_2"], row["spellcooldown_2"]), (0, -1))
            self.assertEqual(row["Flags"] & D.HEROIC_TOOLTIP_FLAG, 0)
            self.assertEqual(row["InventoryType"], 12)

    def test_absorbed_stock_spells_cleared_in_minted_rows_only(self):
        _, em = run([all_items()[-1]])
        by = em.by_entry()
        self.assertEqual(by[10403].tier.itemization["absorbed_spell_slots"], 1)
        self.assertEqual(by[10403].row["spellid_1"], 9330)
        self.assertNotIn("spellid_1", by[10403].owned)
        self.assertEqual((by[71000].row["spellid_1"], by[71000].row["spellcooldown_1"]), (0, -1))
        self.assertEqual(by[10403].row["itemset"], 161)
        self.assertEqual(by[71000].row["itemset"], 0)
        self.assertEqual(by[71001].row["itemset"], 161)

    def test_variant_rows_and_tier_numbers(self):
        _, em = run([F.hammer(), trinket()])
        variants = {r["entry"]: r for r in em.variant_rows}
        self.assertEqual(variants[71000], {"entry": 71000, "base_entry": 5187, "tier": 1})
        self.assertEqual(variants[71001], {"entry": 71001, "base_entry": 5187, "tier": 2})
        keg = {t.tier.tier: t.tier.entry for t in em.tiers if t.tier.key == "hm_keg"}
        self.assertNotIn(keg["heroic_hm"], variants)  # the base
        self.assertEqual(variants[keg["empowered_1_hm"]], {"entry": keg["empowered_1_hm"],
                                                            "base_entry": keg["heroic_hm"], "tier": 2})
        self.assertEqual(em.labels[keg["heroic_hm"]], "Heroic Hard Mode")

    def test_item_dbc_entries_equal_the_template(self):
        lock = "71900 dm_gone heroic retired 2026-11-01 4 4 -1 6 4242 6 0\n"
        _, em = run([F.hammer(), F.girdle(), shield(displayid=99999)], lock_text=lock)
        by_id = {e["id"]: e for e in em.dbc_entries}
        rows = {t.tier.entry: t.row for t in em.tiers}
        self.assertNotIn(5187, by_id)  # a stock entry whose Item.dbc fields do not change
        self.assertIn(5443, by_id)  # displayid declared
        for entry, dbc in by_id.items():
            if entry == 71900:
                continue
            for field_name, column in item_emit.DBC_FIELDS:
                self.assertEqual(dbc[field_name], int(rows[entry][column]), (entry, column))
        self.assertEqual(by_id[71900]["display_info_id"], 4242)
        self.assertEqual(by_id[71900]["class_id"], 4)
        from lib import build  # noqa: PLC0415

        girdle_entry = next(t.tier.entry for t in em.tiers if t.tier.key == "dm_girdle" and t.tier.tier == "normal")
        self.assertGreater(girdle_entry, 71900)  # minting continues after the highest id in the lock
        dbc_row = build.build_item_row(by_id[girdle_entry])
        girdle = rows[girdle_entry]
        self.assertEqual(
            (dbc_row["ClassID"], dbc_row["SubclassID"], dbc_row["DisplayInfoID"], dbc_row["InventoryType"],
             dbc_row["Material"], dbc_row["SheatheType"], dbc_row["Sound_Override_Subclassid"]),
            (girdle["class"], girdle["subclass"], girdle["displayid"], girdle["InventoryType"], girdle["Material"],
             girdle["sheath"], girdle["SoundOverrideSubclass"]),
        )

    def test_duplicate_item_dbc_id_is_an_error(self):
        _, em = run([F.girdle()])
        merged, errors = item_emit.merge_dbc_entries([{"id": 71000, "notes": "csv"}], em)
        self.assertEqual(len(errors), 1)
        self.assertIn("71000", errors[0])
        self.assertEqual(sum(1 for e in merged if e["id"] == 71000), 1)
        merged, errors = item_emit.merge_dbc_entries([{"id": 70100, "notes": "ring"}], em)
        self.assertEqual(errors, [])
        self.assertEqual(len(merged), 1 + len(em.dbc_entries))


def _changed_edits(edits: list[dict], rows: dict[int, dict]) -> list[dict]:
    spec = spell_tables.ITEM_TABLES[0]
    return [e for e in edits if not spell_tables._same_row(rows.get(e["entry"], {}), e, spec)]


def _render_all(em, rows, tbl) -> tuple[str, item_emit.Rendered, list[dict]]:
    rendered = item_emit.render(em, rows, tbl)
    edits = _changed_edits(em.template_edits, rows)
    edit_block = sql_out.render_update_block("item_template", TEMPLATE_COLUMNS, "entry", edits)
    text = "\n\n".join(b for b in (edit_block, *rendered.blocks) if b)
    return text, rendered, edits


def _apply(text: str, rows: dict[int, dict], tbl: dict) -> None:
    keyed = {(e,): r for e, r in rows.items()}
    sql_dump.apply_composite_key_statements(
        keyed, TEMPLATE_COLUMNS, ("entry",), "item_template", text, defaults=spell_tables.ITEM_TEMPLATE_DEFAULTS,
    )
    rows.clear()
    rows.update({k[0]: r for k, r in keyed.items()})
    sql_dump.apply_composite_key_statements(
        tbl["item_itemization"], item_emit.ITEMIZATION_COLUMNS, ("entry",), "item_itemization", text,
    )
    sql_dump.apply_composite_key_statements(
        tbl["item_budget_variant"], item_emit.VARIANT_COLUMNS, ("entry",), "item_budget_variant", text,
    )


class RenderTest(unittest.TestCase):
    def test_rendered_sql_passes_codestyle(self):
        rows, tbl = live_rows(), tables()
        _, em = run(all_items(), rows=rows, tbl=tbl)
        text, rendered, edits = _render_all(em, rows, tbl)
        self.assertEqual(len(rendered.blocks), 3)
        self.assertEqual(len(edits), 4)
        self.assertIn("DELETE FROM `item_itemization` WHERE `entry` IN (", text)
        self.assertIn("ON DUPLICATE KEY UPDATE", text)
        self.assertNotIn("DELETE FROM `item_template`", text)
        done = codestyle_sql(text)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

    def test_second_run_is_silent(self):
        rows, tbl = live_rows(), tables()
        items = all_items()
        lock_exp, em = run(items, rows=rows, tbl=tbl)
        text, rendered, edits = _render_all(em, rows, tbl)
        self.assertTrue(rendered.template_rows and rendered.itemization_rows and rendered.variant_rows and edits)
        _apply(text, rows, tbl)
        self.assertIn(71000, rows)
        self.assertEqual(rows[71000]["ItemLevel"], 66)
        self.assertEqual(tbl["item_budget_variant"][(71000,)]["tier"], 1)
        lock = "".join(f"{line}\n" for line in lock_exp.lock_appended)
        exp2, em2 = run(items, rows=rows, tbl=tbl, lock_text=lock)
        self.assertEqual(exp2.lock_appended, [])
        text2, rendered2, edits2 = _render_all(em2, rows, tbl)
        self.assertEqual(text2, "", text2[:2000])

    def test_a_changed_shape_rerenders_only_that_item(self):
        rows, tbl = live_rows(), tables()
        items = all_items()
        exp, em = run(items, rows=rows, tbl=tbl)
        text, _, _ = _render_all(em, rows, tbl)
        _apply(text, rows, tbl)
        lock = "".join(f"{line}\n" for line in exp.lock_appended)
        changed = (F.hammer(secondary="Haste (Solo)"), *items[1:])
        _, em2 = run(changed, rows=rows, tbl=tbl, lock_text=lock)
        _, rendered2, edits2 = _render_all(em2, rows, tbl)
        self.assertEqual([e["entry"] for e in edits2], [5187])
        self.assertEqual(sorted(r["entry"] for r in rendered2.template_rows), [71000, 71001])
        self.assertEqual(sorted(r["entry"] for r in rendered2.itemization_rows), [5187, 71000, 71001])
        self.assertEqual(rendered2.variant_rows, [])


if __name__ == "__main__":
    unittest.main()
