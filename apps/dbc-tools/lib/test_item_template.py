"""
item_template() and the stock-item content built on it (hunter-rework SHARED §C7.3; T1 step 7): the helper, its
upsert rendering, the items.csv stock-row edit path, and the real quiver / ranged-weapon declarations against the
live item_template overlay.

The real-data tests read the live overlay (base dump + every migration) and the stock Item.dbc, so they assert
relations (declared == selected, emitted + unchanged == declared) rather than the 2026-10-14 counts, which become
0 changed once the migration applies. Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_item_template.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import build, dbcfile, dbcfmt, lint, resolve, source, spell_tables, sql_out, state  # noqa: E402
from lib.dsl import registry  # noqa: E402

COLUMNS = ("entry", "name", "class", "subclass", "ammo_type", "BagFamily", "ContainerSlots")
DEFAULTS = {"name": "", "class": 0, "subclass": 0, "ammo_type": 0, "BagFamily": 0, "ContainerSlots": 0}
LIVE = {
    2101: {"entry": 2101, "name": "Light Quiver", "class": 11, "subclass": 2, "ammo_type": 0, "BagFamily": 1,
           "ContainerSlots": 6},
    18323: {"entry": 18323, "name": "Satyr's Bow", "class": 2, "subclass": 2, "ammo_type": 2, "BagFamily": 0,
            "ContainerSlots": 0},
}


def _live_data(rows=LIVE) -> dict:
    return {"item_template_rows": rows, "item_template_columns": COLUMNS, "item_template_defaults": DEFAULTS}


def _load(text: str, rows=LIVE) -> registry.Registry:
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "world.py"
        path.write_text(text)
        return registry.load_class_file(path, live_data=_live_data(rows))


class ItemTemplateHelperTest(unittest.TestCase):
    def test_unmentioned_columns_keep_their_live_value(self):
        reg = _load('from lib.dsl.registry import item_template\nitem_template(2101, **{"class": 1, "subclass": 0, "BagFamily": 0})\n')
        row = reg.item_templates[0]
        self.assertEqual((row["class"], row["subclass"], row["BagFamily"]), (1, 0, 0))
        self.assertEqual((row["name"], row["ContainerSlots"], row["entry"]), ("Light Quiver", 6, 2101))
        self.assertEqual(row["_update_columns"], ("class", "subclass", "BagFamily"))

    def test_entry_that_does_not_exist_is_an_error(self):
        with self.assertRaisesRegex(ValueError, "no live item_template row"):
            _load("from lib.dsl.registry import item_template\nitem_template(999999, ammo_type=0)\n")

    def test_unknown_column_is_a_key_error_naming_it(self):
        with self.assertRaisesRegex(KeyError, "ammo_typo"):
            _load("from lib.dsl.registry import item_template\nitem_template(2101, ammo_typo=0)\n")

    def test_missing_live_data_is_a_clear_error(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "w.py"
            path.write_text("from lib.dsl.registry import item_template\nitem_template(2101, ammo_type=0)\n")
            with self.assertRaisesRegex(RuntimeError, "item template"):
                registry.load_class_file(path)

    def test_live_item_templates_exposes_the_rows_for_a_selector(self):
        reg = _load(
            "from lib.dsl.registry import item_template, live_item_templates\n"
            "for e, r in live_item_templates().items():\n"
            "    if r['class'] == 2:\n"
            "        item_template(e, ammo_type=0)\n"
        )
        self.assertEqual([r["entry"] for r in reg.item_templates], [18323])

    def test_declaring_one_entry_twice_is_a_duplicate_id_error(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("a.py", "b.py"):
                (Path(d) / name).write_text("from lib.dsl.registry import item_template\nitem_template(18323, ammo_type=0)\n")
            with self.assertRaises(registry.DuplicateIdError):
                registry.load_classes_dir(Path(d), live_data=_live_data())


class ItemUpdateRenderTest(unittest.TestCase):
    def _rows(self, text):
        return _load(text).item_templates

    def test_update_names_only_the_declared_columns(self):
        rows = self._rows("from lib.dsl.registry import item_template\nitem_template(18323, ammo_type=0)\n")
        sql = sql_out.render_update_block("item_template", COLUMNS, "entry", rows)
        self.assertEqual(sql, "UPDATE `item_template` SET `ammo_type` = 0 WHERE `entry` IN (18323);")

    def test_rows_with_the_same_assignments_share_one_statement(self):
        live = {**LIVE, 5748: {**LIVE[18323], "entry": 5748}}
        rows = _load(
            "from lib.dsl.registry import item_template\n"
            'item_template(2101, **{"class": 1, "subclass": 0, "BagFamily": 0})\n'
            "item_template(18323, ammo_type=0)\nitem_template(5748, ammo_type=0)\n", live,
        ).item_templates
        sql = sql_out.render_update_block("item_template", COLUMNS, "entry", rows)
        self.assertEqual(sql.count("UPDATE"), 2)
        self.assertIn("SET `class` = 1, `subclass` = 0, `BagFamily` = 0 WHERE `entry` IN (2101);", sql)
        self.assertIn("SET `ammo_type` = 0 WHERE `entry` IN (5748, 18323);", sql)
        self.assertNotIn("INSERT", sql)
        self.assertNotIn("DELETE", sql)

    def test_empty_rows_render_nothing(self):
        self.assertEqual(sql_out.render_update_block("item_template", COLUMNS, "entry", []), "")

    def test_creature_style_rows_still_update_every_column(self):
        sql = sql_out.render_upsert_block("t", ("id", "a", "b"), ("id",), [{"id": 1, "a": 2, "b": 3}])
        self.assertTrue(sql.endswith("ON DUPLICATE KEY UPDATE `a` = VALUES(`a`), `b` = VALUES(`b`);"))

    def test_an_already_applied_edit_is_not_emitted_again(self):
        rows = self._rows("from lib.dsl.registry import item_template\nitem_template(18323, ammo_type=0)\n")
        spec = spell_tables.TableSpec("item_template", COLUMNS, ("entry",), "item_templates", defaults=DEFAULTS)
        index = spell_tables.SpellTableIndex({"item_template": list(LIVE.values())}, tables=(spec,))
        self.assertEqual([r["entry"] for r in index.rows_to_emit(spec, rows)], [18323])
        applied = {**LIVE, 18323: {**LIVE[18323], "ammo_type": 0}}
        index = spell_tables.SpellTableIndex({"item_template": list(applied.values())}, tables=(spec,))
        self.assertEqual(index.rows_to_emit(spec, rows), [])


class StockItemDbcEditPathTest(unittest.TestCase):
    """7a: a source/items.csv row for a stock id (< 56806) is an edit: an item_dbc delta and a client Item.dbc row."""

    @staticmethod
    def _stock_row(**kw) -> dict:
        row = dbcfile.empty_row(dbcfmt.ITEM)
        row.update(ID=2101, ClassID=11, SubclassID=2, Sound_Override_Subclassid=-1, Material=-1,
                   DisplayInfoID=21328, InventoryType=18, SheatheType=0)
        row.update(kw)
        return row

    ENTRY = {"id": 2101, "class_id": 1, "subclass_id": 0, "sound_override_subclass_id": -1, "material": -1,
             "display_info_id": 21328, "inventory_type": 18, "sheathe_type": 0, "notes": ""}
    IDS = {"item": {"start": 70000, "end": 79999}}

    def test_a_changed_stock_row_resolves_as_an_edit(self):
        resolved = resolve.resolve_rows([self.ENTRY], self.IDS["item"], {2101: self._stock_row()}, build.build_item_row)
        self.assertEqual(resolved.edited_ids, [2101])
        self.assertEqual(resolved.unchanged, 0)

    def test_the_edit_renders_an_item_dbc_delta(self):
        rows = [build.build_item_row(self.ENTRY)]
        sql = sql_out._table_block(dbcfmt.ITEM, self.IDS["item"], rows, [2101])
        self.assertIn("DELETE FROM `item_dbc` WHERE `ID` IN (2101);", sql)
        self.assertIn("INSERT INTO `item_dbc`", sql)
        self.assertIn("(2101, 1, 0, -1, -1, 21328, 18, 0)", sql)

    def test_the_client_item_dbc_gets_the_row_replaced(self):
        base = [self._stock_row(), self._stock_row(ID=2102, SubclassID=3)]
        merged = {r["ID"]: r for r in base}
        merged.update({2101: build.build_item_row(self.ENTRY)})
        packed = dbcfile.pack_client_dbc(dbcfmt.ITEM, list(merged.values()), base)
        self.assertNotEqual(packed, dbcfile.pack_client_dbc(dbcfmt.ITEM, base, base))
        again = dbcfile.pack_dbc_bytes(dbcfmt.ITEM, [merged[2101], base[1]])
        self.assertEqual(packed, again)   # only the one row changed
        self.assertEqual(len(packed), len(dbcfile.pack_client_dbc(dbcfmt.ITEM, base, base)))

    def test_an_applied_edit_resolves_as_unchanged(self):
        applied = self._stock_row(ClassID=1, SubclassID=0)
        resolved = resolve.resolve_rows([self.ENTRY], self.IDS["item"], {2101: applied}, build.build_item_row)
        self.assertEqual((resolved.edited_ids, resolved.unchanged), ([], 1))


HAVE_REAL_DATA = (state.BASE_DBC_DIR / dbcfmt.ITEM.dbc_filename).is_file()


@unittest.skipUnless(HAVE_REAL_DATA, "needs the extracted base Item.dbc (var/extractors/dbc)")
class _RealItemData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = cls._rows_without_generated_migrations()
        cls.live_data = spell_tables.dsl_live_data({}, cls.rows)
        cls.ids_cfg = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
        cls.quivers = registry.load_class_file(TOOL_ROOT / "source" / "world" / "quivers.py", live_data=cls.live_data)
        cls.ranged = registry.load_class_file(
            TOOL_ROOT / "source" / "world" / "ranged_weapons.py", live_data=cls.live_data,
        )
        spec = spell_tables.ITEM_TABLES[0]
        cls.spec = spec
        cls.index = spell_tables.SpellTableIndex({"item_template": list(cls.rows.values())}, tables=spell_tables.ITEM_TABLES)
        cls.items_csv = source.load_items_csv(TOOL_ROOT / "source" / "items.csv")

    @staticmethod
    def _rows_without_generated_migrations() -> dict[int, dict]:
        """The base dump plus every hand-written migration, with generate.py's own output left out: those tests
        start from the pre-generate state, whichever generated files happen to be merged or pending on disk.
        Uses the uncached resolve so the overlay's shared cache never holds the filtered rows."""
        from unittest import mock

        spell_tables.load_live_item_template_rows()  # puts apps/item-tools on sys.path
        from item_lib import overlay  # noqa: PLC0415

        hand_written = [p for p in overlay._contributing_files() if not spell_tables._is_generated(p)]
        with mock.patch.object(overlay, "_contributing_files", return_value=hand_written):
            return overlay.resolve_current_rows()


@unittest.skipUnless(HAVE_REAL_DATA, "needs the extracted base Item.dbc (var/extractors/dbc)")
class RealQuiverAndRangedContentTest(_RealItemData):
    def test_33_quivers_and_pouches_are_declared_without_29889(self):
        entries = [r["entry"] for r in self.quivers.item_templates]
        self.assertEqual(len(entries), 33)
        self.assertNotIn(29889, entries)
        self.assertEqual(len(set(entries)), 33)
        for row in self.quivers.item_templates:
            self.assertEqual((row["class"], row["subclass"], row["BagFamily"]), (1, 0, 0))
            self.assertEqual(row["InventoryType"], 18)
            self.assertEqual(row["ContainerSlots"], self.rows[row["entry"]]["ContainerSlots"])

    def test_every_live_bow_gun_and_crossbow_is_declared_with_ammo_type_zero(self):
        selected = {e for e, r in self.rows.items() if r["class"] == 2 and r["subclass"] in (2, 3, 18)}
        declared = {r["entry"] for r in self.ranged.item_templates}
        self.assertEqual(declared, selected)
        self.assertGreater(len(selected), 700)
        self.assertTrue(all(r["ammo_type"] == 0 for r in self.ranged.item_templates))
        self.assertTrue(all(r["_update_columns"] == ("ammo_type",) for r in self.ranged.item_templates))

    def test_only_the_rows_that_still_need_ammo_emit_and_the_rest_are_silent(self):
        emitted = self.index.rows_to_emit(self.spec, self.ranged.item_templates)
        needing = {r["entry"] for r in self.ranged.item_templates if self.rows[r["entry"]]["ammo_type"] != 0}
        self.assertEqual({r["entry"] for r in emitted}, needing)
        by_subclass = Counter(self.rows[r["entry"]]["subclass"] for r in emitted)
        self.assertEqual(set(by_subclass) - {2, 3, 18}, set())
        # Thori'dal (34334), Centaur Longbow (5748), Skull-Forged Blunderbuss (38246): already 0, no delta.
        for entry in (34334, 5748, 38246):
            self.assertNotIn(entry, {r["entry"] for r in emitted})

    def test_the_33_items_csv_rows_resolve_as_edits_against_stock_and_are_consistent(self):
        quiver_ids = {r["entry"] for r in self.quivers.item_templates}
        csv_rows = [e for e in self.items_csv if e["id"] in quiver_ids]
        self.assertEqual(len(csv_rows), 33)
        self.assertTrue(all((e["class_id"], e["subclass_id"]) == (1, 0) for e in csv_rows))
        stock = state.load_stock_rows(dbcfmt.ITEM)
        resolved = resolve.resolve_rows(csv_rows, self.ids_cfg["item"], stock, build.build_item_row)
        self.assertEqual((len(resolved.edited_ids), resolved.unchanged), (33, 0))   # stock never changes
        for entry in csv_rows:   # everything but class/subclass is the stock row
            row, was = build.build_item_row(entry), stock[entry["id"]]
            self.assertEqual({k: v for k, v in row.items() if k not in ("ClassID", "SubclassID")},
                             {k: v for k, v in was.items() if k not in ("ClassID", "SubclassID")})

    def test_both_lints_are_silent_on_the_real_declarations(self):
        declared = self.quivers.item_templates + self.ranged.item_templates
        dbc = {int(e["id"]): build.build_item_row(e) for e in self.items_csv}
        quiver_templates = self.quivers.item_templates
        self.assertEqual(lint.check_item_dbc_consistency(quiver_templates, dbc), [])
        self.assertEqual(lint.check_ranged_ammo_type(declared, self.items_csv, self.rows), [])

    def test_a_rendered_quiver_and_bow_pass_the_sql_codestyle_check(self):
        quiver = next(r for r in self.quivers.item_templates if r["entry"] == 2101)
        bow = next(r for r in self.ranged.item_templates if r["entry"] == 18323)
        upsert = sql_out.render_update_block("item_template", spell_tables.ITEM_TEMPLATE_COLUMNS, "entry", [quiver, bow])
        csv_row = next(e for e in self.items_csv if e["id"] == 2101)
        item_dbc = sql_out._table_block(dbcfmt.ITEM, self.ids_cfg["item"], [build.build_item_row(csv_row)], [2101])
        text = "-- Generated by apps/dbc-tools/generate.py — DO NOT hand-edit.\n\n" + item_dbc + "\n\n" + upsert + "\n"
        self.assertIn("SET `ammo_type` = 0 WHERE `entry` IN (18323);", upsert)
        with tempfile.TemporaryDirectory() as d:
            pending = Path(d) / "data" / "sql" / "updates" / "pending_db_world"
            pending.mkdir(parents=True)
            (pending / "rev_1.sql").write_text(text, encoding="utf-8")
            # codestyle-sql.py ends with `git fetch` + `git diff` against origin/Playerbot (for the base/archive
            # directory check). A no-op `git` first on PATH keeps this test off the network; the per-file SQL checks
            # on the scratch pending file are what it is for.
            fake_bin = Path(d) / "bin"
            fake_bin.mkdir()
            (fake_bin / "git").write_text("#!/bin/sh\nexit 0\n")
            (fake_bin / "git").chmod(0o755)
            done = subprocess.run(
                [sys.executable, str(REPO_ROOT / "apps" / "codestyle" / "codestyle-sql.py")],
                cwd=d, capture_output=True, text=True, env={**os.environ, "PATH": f"{fake_bin}:{os.environ['PATH']}"},
            )
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertNotIn("❌", done.stdout)


@unittest.skipUnless(HAVE_REAL_DATA, "needs the extracted base Item.dbc (var/extractors/dbc)")
class RoundTripTest(_RealItemData):
    """T-FIX T1-1: what render_item_blocks emits must be read back by the overlay generate.py diffs against,
    so a second build emits zero item_template rows (the multi-row INSERT it replaced never converged)."""

    def test_a_second_build_over_the_replayed_overlay_emits_nothing(self):
        import copy

        sys.path.insert(0, str(REPO_ROOT / "apps" / "item-tools"))
        from item_lib import overlay  # noqa: PLC0415

        dsl = {"item_templates": self.quivers.item_templates + self.ranged.item_templates}
        first = spell_tables.render_item_blocks(self.index, dsl)
        self.assertEqual(len(first), 1)
        self.assertNotIn("INSERT", first[0])
        replayed = copy.deepcopy(self.rows)
        overlay._apply_updates(first[0], replayed, "emitted")
        overlay._apply_inserts(first[0], replayed, "emitted")
        index = spell_tables.SpellTableIndex({"item_template": list(replayed.values())}, tables=spell_tables.ITEM_TABLES)
        self.assertEqual(index.rows_to_emit(self.spec, dsl["item_templates"]), [])
        self.assertEqual(spell_tables.render_item_blocks(index, dsl), [])
        # and the emitted entries are exactly the ones that changed
        changed = {r["entry"] for r in self.index.rows_to_emit(self.spec, dsl["item_templates"])}
        self.assertEqual({e for e in replayed if replayed[e] != self.rows[e]}, changed)

    def test_the_generated_entries_loader_reads_the_update_shape(self):
        from unittest import mock

        from lib import trainer_state

        dsl = {"item_templates": self.quivers.item_templates + self.ranged.item_templates}
        sql = spell_tables.render_item_blocks(self.index, dsl)[0]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "rev_1.sql"
            path.write_text(spell_tables.GENERATED_MARKER + "\n\n" + sql + "\n", encoding="utf-8")
            with mock.patch.object(trainer_state, "_migration_files_mentioning", return_value=[path]):
                entries = {r["entry"] for r in spell_tables.load_generated_item_entries()}
        self.assertEqual(entries, {r["entry"] for r in self.index.rows_to_emit(self.spec, dsl["item_templates"])})


if __name__ == "__main__":
    unittest.main()
