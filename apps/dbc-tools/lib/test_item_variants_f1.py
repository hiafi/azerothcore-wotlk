"""Item variants F1 (the R1 review fixes): weapon-tier budget defaults from live role cells (S1), durability per
minted tier (S2), the both-sides lock refusal (S3), explicit tier steps (N1), retired tiers keep their label (N2).

    cd apps/dbc-tools && .venv/bin/python -m unittest lib.test_item_variants_f1
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

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
