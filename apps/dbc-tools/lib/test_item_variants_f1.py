"""Item variants F1 (the R1 review fixes): weapon-tier budget defaults from live role cells (S1), durability per
minted tier (S2), the both-sides lock refusal (S3), explicit tier steps (N1), retired tiers keep their label (N2).

    cd apps/dbc-tools && .venv/bin/python -m unittest lib.test_item_variants_f1
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Run as a script, lib/ is sys.path[0] and lib/source.py would shadow the source/ namespace package.
sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != Path(__file__).resolve().parent]
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import item_emit, item_ids, item_variants  # noqa: E402
from lib import test_item_variants as F  # noqa: E402
from lib.dsl import items as D  # noqa: E402

PHYSICAL_2H = {"class": 2, "subclass": 5, "InventoryType": 17, "delay": 3000}


def run(items, rows=None, tables=None, lock_text="", labels=None):
    return F.run(items, lock_text=lock_text, rows=rows, tables=tables,
                 labels_loader=lambda: dict(labels or {}))


def with_cell(entries, *, quality=4, ilvl=66, mult=0.8, dps_delta=None, primary=22, secondary=25, cols=PHYSICAL_2H,
              durability=None):
    """Fixture rows and tables plus live itemized items in one (role, slot, quality, bucket) cell."""
    rows, tables = F.live_rows(), F.fixture_tables()
    for n, entry in enumerate(entries):
        rows[entry] = F._row(entry, Quality=quality, ItemLevel=ilvl + n % 3, MaxDurability=durability or 0, **cols)
        base_dps = tables["item_weapon_dps_curve"][(ilvl + n % 3, quality, 1)]["dps"]
        delta = 0.0 if dps_delta is None else dps_delta * base_dps
        tables["item_itemization"][(entry,)] = {
            "entry": entry, "budget_mult": mult + 0.01 * n, "stamina_delta": 0, "dps_delta": delta,
            "absorbed_spell_slots": 0, "armor_delta": 0, "primary_shape_id": primary,
            "secondary_shape_id": secondary, "primary_share": 6000, "block_value_delta": 0,
        }
    return rows, tables


def tier(exp, key, name):
    return next(t for item in exp.items for t in item.tiers if t.key == key and t.tier == name)


class RoleCellTest(unittest.TestCase):
    def test_shape_role(self):
        from item_lib import shapes  # noqa: PLC0415

        cat = shapes.catalog(F.fixture_tables())
        self.assertEqual(item_variants.shape_role(cat[22], cat[25]), "physical")
        self.assertEqual(item_variants.shape_role(cat[22], cat[54]), "tank")  # Dodge secondary
        self.assertEqual(item_variants.shape_role(cat[6], cat[25]), "caster")  # Spirit lead
        self.assertEqual(item_variants.shape_role(cat[0], cat[25]), "physical")  # primary-less

    def test_lookup_median_and_fallback(self):
        cells = item_variants.RoleCells()
        for mult, frac in ((0.4, -0.1), (0.5, 0.0), (0.9, 0.1)):
            cells.add("physical", 13, 4, 66, mult, frac)
        mult, frac, where = cells.lookup("physical", 13, 4, 70)
        self.assertEqual((mult, frac), (0.5, 0.0))
        self.assertIn("ilvl 60-100", where)
        self.assertIsNone(cells.lookup("caster", 13, 4, 70))
        # Too few in the quality's cell: the bucket without the quality.
        cells.add("physical", 13, 3, 66, 0.7, None)
        self.assertEqual(cells.lookup("physical", 13, 3, 66)[0], 0.6)  # median of 0.4 0.5 0.7 0.9
        # Another bucket: any level.
        self.assertEqual(cells.lookup("physical", 13, 4, 20)[0], 0.5)

    def test_weapon_tiers_take_the_cell(self):
        rows, tables = with_cell([9001, 9002, 9003], mult=0.8, dps_delta=0.05)
        exp = run([F.hammer()], rows=rows, tables=tables)
        self.assertEqual(exp.errors, [])
        heroic = tier(exp, "dm_hammer", "heroic")
        self.assertEqual(heroic.itemization["budget_mult"], 0.81)  # median of 0.80 0.81 0.82
        self.assertAlmostEqual(heroic.itemization["dps_delta"], round(0.05 * heroic.baselines["dps"], 4), places=3)
        self.assertIn("role cell physical InventoryType 17 Quality 4", heroic.budget_source)
        # The Normal tier (Rare, ilvl 20) has no sample in its quality or bucket: it falls back to the slot's cell
        # at any quality and level.
        normal = tier(exp, "dm_hammer", "normal")
        self.assertEqual(normal.itemization["budget_mult"], 0.81)

    def test_declared_values_win(self):
        rows, tables = with_cell([9001, 9002, 9003], mult=0.8, dps_delta=0.05)
        exp = run([F.hammer(budget_mult=1.2, extra_dps=0.0)], rows=rows, tables=tables)
        heroic = tier(exp, "dm_hammer", "heroic")
        self.assertEqual((heroic.itemization["budget_mult"], heroic.itemization["dps_delta"]), (1.2, 0.0))
        self.assertEqual(heroic.budget_source, "declared")

    def test_weapon_role_override(self):
        rows, tables = with_cell([9001, 9002, 9003], mult=0.3, secondary=54)  # a tank cell
        plain = run([F.hammer()], rows=rows, tables=tables)
        self.assertEqual(tier(plain, "dm_hammer", "heroic").budget_source, "default")
        tank = run([F.hammer(weapon_role="tank")], rows=rows, tables=tables)
        self.assertEqual(tier(tank, "dm_hammer", "heroic").itemization["budget_mult"], 0.31)
        with self.assertRaises(D.ItemDeclarationError):
            F.hammer(weapon_role="healer")
        armor = run([F.girdle(weapon_role="tank")], rows=rows, tables=tables)
        self.assertTrue(any("weapon_role= needs a weapon-tier slot" in e for e in armor.errors))

    def test_no_cell_keeps_the_plain_default(self):
        exp = run([F.hammer()])
        heroic = tier(exp, "dm_hammer", "heroic")
        self.assertEqual((heroic.itemization["budget_mult"], heroic.itemization["dps_delta"]), (1.0, 0.0))

    def test_owned_and_block_entries_are_not_samples(self):
        # Two of the three samples are the generator's own (inside the item block / owned by the lock), so the cell
        # is too small and the default stays: the generator's rows never feed back into the defaults.
        rows, tables = with_cell([9001, 71500, 70050], mult=0.8)
        exp = run([F.hammer()], rows=rows, tables=tables, lock_text="")
        self.assertEqual(tier(exp, "dm_hammer", "heroic").budget_source, "default")
        rows, tables = with_cell([9001, 9002, 9003], mult=0.8)
        exp = run([F.hammer(), F.D.item("dm_other", base=9003, primary="Strength (Solo)", ladder=F.ladder_dungeon())],
                  rows=rows, tables=tables)
        self.assertEqual(tier(exp, "dm_hammer", "heroic").budget_source, "default")

    def test_live_item_higher_tiers_take_the_cell(self):
        cols = {"class": 2, "subclass": 7, "InventoryType": 13, "delay": 1800}
        rows, tables = with_cell([9001, 9002, 9003], mult=0.4, primary=23, secondary=25, cols=cols)
        exp = run([F.D.item("dm_thief", base=5192, itemization="live", ladder=F.ladder_dungeon())],
                  rows=rows, tables=tables)
        self.assertEqual(exp.errors, [])
        self.assertEqual(tier(exp, "dm_thief", "normal").itemization["budget_mult"], 0.718)  # the live row
        heroic = tier(exp, "dm_thief", "heroic")
        self.assertEqual(heroic.itemization["budget_mult"], 0.41)
        # The live DPS fraction is kept: -0.5 over the Normal tier's baseline, scaled to the Heroic one.
        normal_dps = tier(exp, "dm_thief", "normal").baselines["dps"]
        self.assertAlmostEqual(heroic.itemization["dps_delta"], round(-0.5 / normal_dps * heroic.baselines["dps"], 4))


class FreeDpsTest(unittest.TestCase):
    """`free_dps=True` (quest reward ruling 40): the declared DPS over the role cell's is funded by budget_mult, so the
    stat line is the role-cell version's."""

    @staticmethod
    def breakdown(exp, rows, tables, key, name):
        from item_lib import budget, shapes  # noqa: PLC0415

        t = tier(exp, key, name)
        row = {**rows[5187], "ItemLevel": t.ilvl, "Quality": t.quality}
        return budget.compute_breakdown(row, {"entry": 5187, **t.itemization}, tables, shapes.catalog(tables))

    @staticmethod
    def stats(b):
        return [(a["stat_type"], a["rounded"]) for a in b["allocations"]]

    def test_free_dps_keeps_the_cell_stats_with_full_dps(self):
        rows, tables = with_cell([9001, 9002, 9003], mult=0.8, dps_delta=-0.2)
        cut = run([F.hammer()], rows=rows, tables=tables)
        free = run([F.hammer(extra_dps=0.0, free_dps=True)], rows=rows, tables=tables)
        paid = run([F.hammer(extra_dps=0.0)], rows=rows, tables=tables)
        for exp in (cut, free, paid):
            self.assertEqual(exp.errors, [])
        for name in ("normal", "heroic", "empowered_1"):
            b_cut = self.breakdown(cut, rows, tables, "dm_hammer", name)
            b_free = self.breakdown(free, rows, tables, "dm_hammer", name)
            b_paid = self.breakdown(paid, rows, tables, "dm_hammer", name)
            self.assertEqual(tier(free, "dm_hammer", name).itemization["dps_delta"], 0.0)
            self.assertEqual(b_free["final_dps"], b_free["baseline_dps"])
            self.assertGreater(b_free["final_dps"], b_cut["final_dps"])
            self.assertGreater(tier(free, "dm_hammer", name).itemization["budget_mult"],
                               tier(cut, "dm_hammer", name).itemization["budget_mult"])
            self.assertLessEqual(abs(b_free["effective_budget"] - b_cut["effective_budget"]), 1)
            self.assertEqual(self.stats(b_free), self.stats(b_cut), name)
            self.assertEqual(b_free["final_stamina"], b_cut["final_stamina"], name)
            # Without free_dps the DPS is paid out of the stats.
            self.assertLess(b_paid["effective_budget"], b_free["effective_budget"])
            self.assertIn("free DPS", tier(free, "dm_hammer", name).budget_source)

    def test_errors(self):
        with self.assertRaises(D.ItemDeclarationError):
            F.hammer(free_dps=True)  # no extra_dps=
        with self.assertRaises(D.ItemDeclarationError):
            F.hammer(extra_dps=0.0, free_dps="yes")
        with self.assertRaises(D.ItemDeclarationError):
            D.item("dm_thief", base=5192, itemization="live", free_dps=True, ladder=F.ladder_dungeon())
        no_cell = run([F.hammer(extra_dps=0.0, free_dps=True)])
        self.assertTrue(any("free_dps=True needs a role cell" in e for e in no_cell.errors), no_cell.errors)
        armor = run([F.girdle(extra_dps=0.0, free_dps=True)])
        self.assertTrue(any("free_dps=True needs a weapon" in e for e in armor.errors), armor.errors)
        # A cut so deep the raised multiplier leaves (0, 2].
        rows, tables = with_cell([9001, 9002, 9003], mult=1.9, dps_delta=-0.9)
        over = run([F.hammer(extra_dps=0.0, free_dps=True)], rows=rows, tables=tables)
        self.assertTrue(any("outside (0, 2]" in e for e in over.errors), over.errors)


class FrozenCellTest(unittest.TestCase):
    """R-W1 S2: a cell's values are frozen the first time a declaration asks for it, so a later declaration that
    takes over another sample of the cell never retunes an earlier item."""

    def other(self):
        return F.D.item("dm_other", base=9003, primary="Strength (Solo)", ladder=F.ladder_dungeon())

    def rows_by_entry(self, exp, key):
        return {t.entry: t.itemization for item in exp.items for t in item.tiers if t.key == key}

    def test_adding_a_declaration_never_changes_another_items_row(self):
        rows, tables = with_cell([9001, 9002, 9003, 9004], ilvl=60, mult=0.8, dps_delta=0.05)
        first = F.run([F.hammer()], rows=rows, tables=tables, labels_loader=dict)
        self.assertEqual(first.errors, [])
        self.assertTrue(first.cells_lock_appended)
        self.assertTrue(first.cells_lock_text.startswith(item_variants.CELLS_LOCK_HEADER))
        before = self.rows_by_entry(first, "dm_hammer")
        self.assertEqual(before[71000]["budget_mult"], 0.815)  # median of 0.80 0.81 0.82 0.83
        # Unfrozen, the new declaration takes 9003 out of the sample and moves the hammer's median.
        moved = F.run([F.hammer(), self.other()], rows=rows, tables=tables, labels_loader=dict)
        self.assertNotEqual(self.rows_by_entry(moved, "dm_hammer"), before)
        # Frozen by the first run's lock: the hammer's rows stay exactly as they were.
        frozen = F.run([F.hammer(), self.other()], rows=rows, tables=tables, labels_loader=dict,
                       cells_lock_text=first.cells_lock_text)
        self.assertEqual(frozen.errors, [])
        self.assertEqual(self.rows_by_entry(frozen, "dm_hammer"), before)
        self.assertIn("(frozen)", tier(frozen, "dm_hammer", "heroic").budget_source)
        self.assertEqual(frozen.cells_lock_text, first.cells_lock_text)  # the same cells: nothing appended
        self.assertEqual(frozen.cells_lock_appended, [])

    def test_no_cell_is_frozen_too(self):
        exp = F.run([F.hammer()], labels_loader=dict)
        self.assertTrue(exp.cells_lock_appended)
        self.assertTrue(all(line.endswith(" none") for line in exp.cells_lock_appended))
        # A later sample in that cell does not retune the item: the plain default stays.
        rows, tables = with_cell([9001, 9002, 9003], mult=0.8, dps_delta=0.05)
        again = F.run([F.hammer()], rows=rows, tables=tables, labels_loader=dict,
                      cells_lock_text=exp.cells_lock_text)
        heroic = tier(again, "dm_hammer", "heroic")
        self.assertEqual((heroic.itemization["budget_mult"], heroic.itemization["dps_delta"]), (1.0, 0.0))

    def test_lock_round_trip_and_errors(self):
        text = item_variants.render_cells_lock("", ["physical 17 4 60-100 0.8150 0.0500  # cell 2026-11-07",
                                                    "tank 14 3 any none"])
        cells = item_variants.parse_cells_lock(text)
        self.assertEqual(cells[("physical", 17, 4, 1)][:2], (0.815, 0.05))
        self.assertIsNone(cells[("tank", 14, 3, None)])
        for bad, message in (("physical 17 4 60-100 0.8", "malformed"), ("healer 17 4 any none", "unknown role"),
                             ("tank 14 3 any none\ntank 14 3 any none", "already frozen")):
            with self.assertRaisesRegex(item_variants.CellsLockError, message):
                item_variants.parse_cells_lock(bad)
        exp = F.run([F.hammer()], labels_loader=dict, cells_lock_text="physical 17 4 1-2 none\n")
        self.assertTrue(any("malformed" in e for e in exp.errors))


class DurabilityTest(unittest.TestCase):
    def test_minted_tiers_take_the_live_median(self):
        plate_waist = {"class": 4, "subclass": 4, "InventoryType": 6}
        rows, tables = with_cell([9001, 9002, 9003], cols=plate_waist, durability=55)
        rows[9004] = F._row(9004, Quality=4, ItemLevel=66, MaxDurability=1000, **plate_waist)  # an outlier
        rows[6087]["MaxDurability"] = 30  # the like= donor
        exp = run([F.girdle()], rows=rows, tables=tables)
        self.assertEqual(exp.errors, [])
        self.assertEqual(tier(exp, "dm_girdle", "heroic").max_durability, 55)
        # Rare at ilvl 20 has no live sample: the donor's.
        self.assertEqual(tier(exp, "dm_girdle", "normal").max_durability, 30)
        em = item_emit.build(exp)
        by = em.by_entry()
        self.assertEqual(by[tier(exp, "dm_girdle", "heroic").entry].row["MaxDurability"], 55)

    def test_stock_base_keeps_its_own_and_explicit_wins(self):
        rows = F.live_rows()
        rows[5187]["MaxDurability"] = 75
        exp = run([F.hammer(MaxDurability=90)], rows=rows)
        self.assertIsNone(tier(exp, "dm_hammer", "normal").max_durability)
        self.assertIsNone(tier(exp, "dm_hammer", "heroic").max_durability)
        em = item_emit.build(exp)
        self.assertEqual(em.by_entry()[tier(exp, "dm_hammer", "heroic").entry].row["MaxDurability"], 90)
        plain = item_emit.build(run([F.hammer()], rows=rows))
        heroic = next(t for t in plain.tiers if t.tier.tier == "heroic")
        self.assertEqual(heroic.row["MaxDurability"], 75)  # no sample in the fixture: the stock donor's
        self.assertNotIn("MaxDurability", plain.by_entry()[5187].owned)


class LockMergeTest(unittest.TestCase):
    def test_both_sides_of_a_merge_conflict_are_refused_naming_the_entry(self):
        ours = "5187 dm_hammer normal base\n71000 dm_hammer heroic\n"
        theirs = "71000 dm_girdle normal\n71001 dm_girdle heroic\n"
        with self.assertRaisesRegex(item_ids.LockError, r"line 3: entry 71000 is already on line 2"):
            item_ids.parse_lock(ours + theirs, F.BLOCK)
        exp = run([F.hammer()], lock_text=ours + theirs)
        self.assertTrue(any("entry 71000 is already on line 2" in e for e in exp.errors))

    def test_header_documents_the_recovery(self):
        self.assertIn("drop the other side's minted", item_ids.LOCK_HEADER)
        self.assertIn("drop the other side's minted lines", item_ids.LOCK_PATH.read_text())


class StepTest(unittest.TestCase):
    def test_variant_rows_carry_the_declared_step(self):
        lad = D.ladder("l", normal=D.tier(step=0, label="Normal"),
                       heroic=D.tier(step=1, ilvl=66, quality=4, required_level=60, heroic_flag=True, label="Heroic"),
                       empowered_3=D.tier(step=4, ilvl=96, quality=4, required_level=60, label="Chthonic"))
        exp = run([F.hammer(ladder=lad)])
        em = item_emit.build(exp)
        self.assertEqual(sorted(r["tier"] for r in em.variant_rows), [1, 4])

    def test_real_ladders(self):
        from source.items import ladders  # noqa: PLC0415

        self.assertEqual([t.step for t in ladders.VANILLA_DUNGEON.tiers], [0, 1, 2, 3, 4])
        self.assertEqual([t.step for t in ladders.VANILLA_HARD_MODE.tiers], [1, 2, 3, 4])


class RetiredLabelTest(unittest.TestCase):
    def test_retired_line_keeps_its_label(self):
        lock = item_ids.parse_lock("71900 dm_gone empowered_1 retired 2026-11-01 4 4 -1 6 4242 6 0 Molten Empowered\n"
                                   "71901 dm_gone heroic retired 2026-11-01 4 4 -1 6 4242 6 0\n", F.BLOCK)
        self.assertEqual(lock.by_entry[71900].label, "Molten Empowered")
        self.assertIsNone(lock.by_entry[71901].label)
        with self.assertRaisesRegex(item_ids.LockError, "label"):
            item_ids.parse_lock('71900 dm_gone heroic retired 2026-11-01 4 4 -1 6 4242 6 0 Bad"Label\n', F.BLOCK)
        em = item_emit.build(run([F.hammer()], lock_text=lock.text))
        self.assertEqual(em.labels.get(71900), "Molten Empowered")
        self.assertNotIn(71901, em.labels)  # a Heroic tier: the client prints its line from flag 0x8

    def test_retire_suggestion_carries_the_current_label(self):
        first = run([F.hammer(), F.girdle()])
        girdle_e1 = tier(first, "dm_girdle", "empowered_1").entry
        rows = F.live_rows()
        rows[girdle_e1] = F._row(girdle_e1, **{"class": 4, "subclass": 4, "InventoryType": 6, "displayid": 4242,
                                               "Material": 6, "sheath": 0, "SoundOverrideSubclass": -1})
        dropped = run([F.hammer()], lock_text=first.lock_text, rows=rows,
                      labels={girdle_e1: "Molten Empowered"})
        self.assertTrue(any(f"`{girdle_e1} dm_girdle empowered_1 retired 2026-11-06 4 4 -1 6 4242 6 0 Molten "
                            f"Empowered`" in e for e in dropped.errors), dropped.errors)

    def test_label_table_round_trip(self):
        import tempfile  # noqa: PLC0415

        from lib import item_labels  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ItemTierLabels.lua"
            self.assertEqual(item_labels.read_table(path), {})
            path.write_text(item_labels.render_lua({71001: "Molten Empowered", 5187: "Normal"}))
            self.assertEqual(item_labels.read_table(path), {5187: "Normal", 71001: "Molten Empowered"})


class InheritedColumnsTest(unittest.TestCase):
    def test_base_with_resistance_or_script_warns(self):
        rows = F.live_rows()
        rows[5187].update(fire_res=5, ScriptName="item_x")
        exp = run([F.hammer()], rows=rows)
        self.assertTrue(any("fire_res=5" in w and "ScriptName='item_x'" in w for w in exp.warnings), exp.warnings)
        self.assertEqual(run([F.hammer()]).warnings, [])


class RetuneNoteTest(unittest.TestCase):
    def test_live_minted_row_with_new_stats_is_noted(self):
        exp = run([F.hammer()])
        em = item_emit.build(exp)
        heroic = tier(exp, "dm_hammer", "heroic").entry
        rows = F.live_rows()
        tables = exp.tables
        first = item_emit.render(em, rows, tables)
        self.assertEqual(first.retuned, [])  # not live yet
        rows[heroic] = dict(em.by_entry()[heroic].row, stat_value1=1)
        rendered = item_emit.render(em, rows, tables)
        self.assertEqual(rendered.retuned, [heroic])
        self.assertTrue(any("item_budget_version" in n for n in item_emit.summary_notes(em, rendered)))
        rows[heroic] = dict(em.by_entry()[heroic].row, name="Renamed")  # not a cached stat
        self.assertEqual(item_emit.render(em, rows, tables).retuned, [])


if __name__ == "__main__":
    unittest.main()
