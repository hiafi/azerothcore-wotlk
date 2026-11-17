"""
Weapon scaling WS0b/WS0c (.agents/plans/weapon-scaling/weapon-scaling.PLAN.md rulings 3-6 and the WS0b rulings):
caster weapon spell power from weapon DPS (lib/weapon_spell_power.py, `item_itemization.spell_power_per_dps` read by
item_lib.budget, item_variants / item_emit carrying the multiplier m), against the fixture tables of
lib/test_item_variants.py.

Covered: the shipped constants are off and carry the ruled slot factors (staff 0.82, ranged 0); the role default
(caster 1.0, physical 0) and a declared override; the DSL range check and a non-weapon refusal; m = 0 writes no line
and a 0 coefficient; every minted tier inherits m and carries `lround(k x DPS x m)`; an m > 0 weapon has exactly one
Spell Power line and the same budget (effective, per side and spent) as without the rule; a Spell Power-only primary
hands its budget to the secondary shape; a Spell Power lead weapon stays caster; the coefficient and DPS go through
float32 like the C++; an undeclared itemized caster weapon gets its item_itemization row rewritten (an owned one and a
physical one do not, an unitemized caster-lead one is listed); k_sp = 0 changes nothing, and turning it back to 0
writes 0 back; a weapon above item level 100 keeps coefficient 0 and its budgeted Spell Power (declared tier by tier,
and undeclared); a negative k raises; the coefficient is rounded to 4 decimals; item_lib.budget refuses the rows
ItemBudget.cpp refuses (negative, or nonzero on a non-weapon).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_weapon_spell_power.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import item_emit, weapon_spell_power as W  # noqa: E402
from lib import test_item_variants as F  # noqa: E402
from lib.dsl import items as D  # noqa: E402

from item_lib import budget, shapes  # noqa: E402  (on the path once test_item_variants imported item_variants)

SP, SPI, INT, CRIT, STA = 45, 6, 5, 32, 7
K = W.k_table(3.0)
CASTER_ENTRY, UNDECLARED, PHYS_UNDECLARED, LITERAL_CASTER = 13964, 9001, 9002, 9003


def tables() -> dict:
    t = F.fixture_tables()
    for shape_id, name, stats in ((5, "Spirit/SpellPower, SpellPower lead", [SP, SPI]),
                                  (71, "Spirit (Solo)", [SPI]), (81, "Spell Power (Solo)", [SP])):
        t["item_shape"][(shape_id,)] = {"shape_id": shape_id, "name": name, "kind": 0,
                                        "dist_id": 3 if len(stats) > 1 else 1}
        for rank, stat in enumerate(stats, 1):
            t["item_shape_stat"][(shape_id, rank)] = {"stat_type": stat}
    # Unequal costs, so a spent-budget comparison means something.
    t["item_stat_cost"] = {(SP,): {"cost": 0.86}, (SPI,): {"cost": 1.0}, (CRIT,): {"cost": 1.0}, (43,): {"cost": 2.5}}
    for entry, primary in ((UNDECLARED, 5), (PHYS_UNDECLARED, 22)):
        t["item_itemization"][(entry,)] = {
            "entry": entry, "budget_mult": 0.507, "stamina_delta": 0, "dps_delta": -6.0, "absorbed_spell_slots": 0,
            "armor_delta": 0, "primary_shape_id": primary, "secondary_shape_id": 25, "primary_share": 6000,
            "block_value_delta": 0, "spell_power_per_dps": 0.0,
        }
    return t


def live_rows() -> dict[int, dict]:
    rows = F.live_rows()
    dagger = {"class": 2, "subclass": 15, "InventoryType": 13, "delay": 1800}
    rows[CASTER_ENTRY] = F._row(CASTER_ENTRY, ItemLevel=61, **dagger)
    rows[UNDECLARED] = F._row(UNDECLARED, ItemLevel=40, stat_type1=SP, stat_value1=20, stat_type2=SPI,
                              stat_value2=8, **dagger)
    rows[PHYS_UNDECLARED] = F._row(PHYS_UNDECLARED, ItemLevel=40, stat_type1=4, stat_value1=10, **dagger)
    rows[LITERAL_CASTER] = F._row(LITERAL_CASTER, ItemLevel=40, stat_type1=INT, stat_value1=7, **dagger)
    return rows


def caster(**kw) -> D.ItemDecl:
    args = dict(base=CASTER_ENTRY, primary="Spirit/SpellPower, SpellPower lead", secondary="Crit (Solo)",
                ladder=F.ladder_dungeon())
    args.update(kw)
    return D.item("scholo_witchblade", **args)


def run(items, k=None, tbl=None):
    tbl = tbl if tbl is not None else tables()
    exp = F.run(items, rows=live_rows(), tables=tbl, spell_power_k=k)
    return exp, item_emit.build(exp)


def lines(row: dict) -> list[tuple[int, int]]:
    return [(row[f"stat_type{n}"], row[f"stat_value{n}"]) for n in range(1, 11) if row[f"stat_type{n}"]]


def spent(b: dict, tbl: dict) -> float:
    """The budget the allocations spend, before rounding (exact points x cost)."""
    cost = {k[0]: v["cost"] for k, v in tbl["item_stat_cost"].items()}
    return sum(a["raw"] * cost.get(a["stat_type"], 1.0) for a in b["allocations"])


def undeclared(tbl, owned=(), k=K, rows=None):
    return W.undeclared_rows(rows or live_rows(), set(owned), tbl, shapes.catalog(tbl), k=k)


class ConstantsTest(unittest.TestCase):
    def test_shipped_constants(self):
        self.assertEqual(W.ONE_HAND_K, 0.0)
        self.assertTrue(all(v == 0 for v in W.K_SP.values()))
        self.assertFalse(W.enabled())
        self.assertEqual(W.SLOT_FACTORS, {"one_hand": 1.0, "two_hand": 0.82, "ranged": 0.0})
        self.assertEqual(W.k_table(4.0), {"one_hand": 4.0, "two_hand": 4.0 * 0.82, "ranged": 0.0})
        self.assertTrue(W.enabled(K))

    def test_coefficient(self):
        self.assertEqual(W.coefficient(2, 13, 1.0, K, item_level=60), 3.0)
        self.assertEqual(W.coefficient(2, 21, 1.0, K, item_level=60), 3.0)
        self.assertEqual(W.coefficient(2, 17, 0.5, K, item_level=60), round(3.0 * 0.82 * 0.5, 4))
        self.assertEqual(W.coefficient(2, 26, 1.0, K, item_level=60), 0.0)  # a wand gets none
        self.assertEqual(W.coefficient(4, 13, 1.0, K, item_level=60), 0.0)  # not a weapon
        self.assertEqual(W.coefficient(2, 13, 0.0, K, item_level=60), 0.0)
        self.assertEqual(W.coefficient(2, 13, 1.0, item_level=60), 0.0)  # the shipped constants
        # Rounded to 4 decimals (a FLOAT column read back as text): 3.4567 x 0.82 = 2.834494 -> 2.8345.
        self.assertEqual(W.coefficient(2, 17, 1.0, W.k_table(3.4567), item_level=60), 2.8345)

    def test_item_level_limit(self):
        self.assertEqual(W.MAX_ITEM_LEVEL, 100)
        self.assertEqual(W.coefficient(2, 13, 1.0, K, item_level=100), 3.0)
        self.assertEqual(W.coefficient(2, 13, 1.0, K, item_level=101), 0.0)
        self.assertEqual(W.coefficient(2, 17, 2.0, K, item_level=226), 0.0)

    def test_negative_k_refused(self):
        with self.assertRaisesRegex(ValueError, "must be a number >= 0"):
            W.k_table(-3.5)
        with self.assertRaisesRegex(ValueError, "must be a number >= 0"):
            W.coefficient(2, 13, 1.0, {"one_hand": -1.0, "two_hand": 0.0, "ranged": 0.0}, item_level=60)


class DslTest(unittest.TestCase):
    def test_range_check(self):
        for bad in (-0.1, 2.01, True, "1"):
            with self.assertRaisesRegex(D.ItemDeclarationError, "weapon_spell_power_mult"):
                caster(weapon_spell_power_mult=bad)
        for good in (0, 0.5, 2):
            self.assertEqual(caster(weapon_spell_power_mult=good).weapon_spell_power_mult, float(good))
        self.assertIsNone(caster().weapon_spell_power_mult)

    def test_non_weapon_refused(self):
        exp = F.run([F.girdle(weapon_spell_power_mult=1.0)], rows=live_rows(), tables=tables())
        self.assertTrue(any("weapon_spell_power_mult= needs a weapon" in e for e in exp.errors), exp.errors)


class RoleTest(unittest.TestCase):
    def test_role_default(self):
        exp, _ = run([caster(), F.hammer()], k=K)
        for item in exp.items:
            for tier in item.tiers:
                want = 1.0 if tier.key == "scholo_witchblade" else 0.0
                self.assertEqual(tier.spell_power_mult, want, tier)
                coef = W.coefficient(item.item_class, item.inventory_type, want, K, item_level=tier.ilvl)
                self.assertAlmostEqual(tier.itemization["spell_power_per_dps"], coef)

    def test_override(self):
        exp, _ = run([caster(weapon_spell_power_mult=0.0), F.hammer(weapon_spell_power_mult=0.5)], k=K)
        mults = {t.key: t.spell_power_mult for item in exp.items for t in item.tiers}
        self.assertEqual(mults, {"scholo_witchblade": 0.0, "dm_hammer": 0.5})
        hammer = next(t for item in exp.items for t in item.tiers if t.key == "dm_hammer")
        self.assertEqual(hammer.itemization["spell_power_per_dps"], round(3.0 * 0.82 * 0.5, 4))  # a two-hand
        exp, _ = run([caster(weapon_role="physical")], k=K)
        self.assertTrue(all(t.spell_power_mult == 0.0 for item in exp.items for t in item.tiers))

    def test_spell_power_lead_stays_caster(self):
        exp, em = run([caster()], k=K)
        self.assertEqual(em.errors, [])
        for tier_rows in em.tiers:
            self.assertEqual(tier_rows.tier.spell_power_mult, 1.0)
            self.assertEqual(tier_rows.tier.itemization["primary_shape_id"], 5)  # the shape itself is not changed
            self.assertEqual([s for s, _ in lines(tier_rows.row)].count(SP), 1)


class EmitTest(unittest.TestCase):
    def test_m_zero_writes_no_row(self):
        for items in ([F.hammer()], [caster(weapon_spell_power_mult=0)]):
            exp, em = run(items, k=K)
            _, off = run(items)
            self.assertEqual(em.errors, [])
            for on_rows, off_rows in zip(em.tiers, off.tiers):
                self.assertEqual(on_rows.row, off_rows.row)
                self.assertEqual(on_rows.breakdown["weapon_spell_power"], 0)
                self.assertEqual(on_rows.tier.itemization["spell_power_per_dps"], 0.0)
        exp, em = run([F.hammer()], k=K)
        self.assertFalse(any(s == SP for t in em.tiers for s, _ in lines(t.row)))

    def test_every_tier_inherits_m_and_one_line(self):
        exp, em = run([caster(weapon_spell_power_mult=0.5)], k=K)
        self.assertEqual(em.errors, [])
        self.assertEqual(len(em.tiers), 3)
        for tier_rows in em.tiers:
            self.assertEqual(tier_rows.tier.spell_power_mult, 0.5)
            self.assertEqual(tier_rows.tier.itemization["spell_power_per_dps"], 1.5)
            b = tier_rows.breakdown
            want = budget._round(1.5 * b["final_dps"])
            self.assertGreater(want, 0)
            self.assertEqual([v for s, v in lines(tier_rows.row) if s == SP], [want], tier_rows.tier.tier)
            self.assertEqual(lines(tier_rows.row)[-1][0], SP)  # after Stamina
            self.assertNotIn(SP, [a["stat_type"] for a in b["allocations"]])
        # The column reaches the item_itemization rows the emission writes.
        self.assertTrue(all(r["spell_power_per_dps"] == 1.5 for r in em.itemization_rows))
        self.assertIn("spell_power_per_dps", item_emit.ITEMIZATION_COLUMNS)

    def test_budget_total_unchanged(self):
        tbl = tables()
        exp, on = run([caster()], k=K, tbl=tbl)
        _, off = run([caster()], tbl=tbl)
        self.assertEqual(on.errors, [])
        for on_rows, off_rows in zip(on.tiers, off.tiers):
            a, b = on_rows.breakdown, off_rows.breakdown
            for key in ("budget", "effective_budget", "primary_budget", "secondary_budget", "final_dps",
                        "final_stamina"):
                self.assertEqual(a[key], b[key], key)
            self.assertAlmostEqual(spent(a, tbl), a["primary_budget"] + a["secondary_budget"], places=6)
            self.assertAlmostEqual(spent(a, tbl), spent(b, tbl), places=6)
            # Off: the budgeted Spell Power line; on: Spirit took its share, plus the DPS line.
            off_lines, on_lines = dict(lines(off_rows.row)), dict(lines(on_rows.row))
            self.assertIn(SP, off_lines)
            self.assertGreater(on_lines[SPI], off_lines[SPI])
            self.assertEqual(on_lines[SP], budget._round(3.0 * a["final_dps"]))
            self.assertEqual(len(on_lines), len(lines(on_rows.row)))  # one row per stat

    def test_k_zero_changes_nothing(self):
        items = [caster(), F.hammer()]
        _, default = run(items)
        _, zeros = run(items, k=W.k_table(0.0))
        self.assertEqual([t.row for t in default.tiers], [t.row for t in zeros.tiers])
        for tier_rows in default.tiers:
            self.assertFalse(tier_rows.breakdown["spell_power_stripped"])
            self.assertEqual(tier_rows.tier.itemization["spell_power_per_dps"], 0.0)
        # The caster keeps its budgeted Spell Power with the feature off.
        self.assertTrue(any(s == SP for t in default.tiers for s, _ in lines(t.row)))
        result = undeclared(tables(), k=None)
        self.assertEqual((result.rows, result.covered, result.unclassifiable, result.notes), ([], [], [], []))

    def test_missing_column_reads_as_zero(self):
        tbl = tables()
        row = dict(tbl["item_itemization"][(UNDECLARED,)])
        with_zero = budget.compute_breakdown(live_rows()[UNDECLARED], row, tbl, shapes.catalog(tbl))
        del row["spell_power_per_dps"]
        without = budget.compute_breakdown(live_rows()[UNDECLARED], row, tbl, shapes.catalog(tbl))
        self.assertEqual(with_zero, without)


class Float32Test(unittest.TestCase):
    def test_value_goes_through_float32(self):
        # float32(0.01) = 0.0099999997764..., so 0.01 x 50 DPS is 0.4999999888 and rounds to 0 in the C++
        # (`std::lround(double(coef) * double(FinalDps))`), where the plain double product 0.5 would round to 1.
        self.assertEqual(budget.weapon_spell_power_value(0.01, 50.0, 0.0), 0)
        self.assertEqual(budget._round(0.01 * 50.0), 1)
        self.assertEqual(budget.weapon_spell_power_value(3.0, 1.0, -2.0), 0)  # a negative DPS sum clamps to 0
        self.assertEqual(budget._f32(2.87), 2.869999885559082)


class SpellPowerOnlyTest(unittest.TestCase):
    def test_spell_power_only_primary_goes_to_secondary(self):
        tbl = tables()
        tbl["item_itemization"][(UNDECLARED,)]["primary_shape_id"] = 81
        catalog = shapes.catalog(tbl)
        row = live_rows()[UNDECLARED]
        itemization = dict(tbl["item_itemization"][(UNDECLARED,)])
        off = budget.compute_breakdown(row, itemization, tbl, catalog)
        on = budget.compute_breakdown(row, {**itemization, "spell_power_per_dps": 3.0}, tbl, catalog)
        self.assertTrue(on["spell_power_budget_to_secondary"])
        self.assertEqual([a["stat_type"] for a in on["allocations"]], [CRIT])
        self.assertAlmostEqual(spent(on, tbl), spent(off, tbl), places=6)
        self.assertEqual(on["effective_budget"], off["effective_budget"])
        fields = budget.materialized_item_fields(on)
        self.assertEqual([fields[f"stat_type{n}"] for n in range(1, 4)], [CRIT, STA, SP])


class ItemLevelLimitTest(unittest.TestCase):
    """User ruling 2026-11-17 (WS0 review): only caster weapons of item level 100 and below get the rule; a weapon
    above keeps coefficient 0 and its budgeted Spell Power, declared tier by tier and undeclared."""

    def test_declared_tier_above_100_keeps_budgeted_spell_power(self):
        ladder = D.ladder(
            "ws_ilvl_limit",
            normal=D.tier(step=0, label="Normal"),
            heroic=D.tier(step=1, ilvl=100, quality=D.Quality.EPIC, required_level=60, label="Heroic"),
            empowered_1=D.tier(step=2, ilvl=101, quality=D.Quality.EPIC, required_level=60, label="Empowered"),
        )
        exp, em = run([caster(ladder=ladder)], k=K)
        _, off = run([caster(ladder=ladder)])
        self.assertEqual(em.errors, [])
        by_tier = {t.tier.tier: t for t in em.tiers}
        self.assertEqual({name: t.tier.ilvl for name, t in by_tier.items()},
                         {"normal": 61, "heroic": 100, "empowered_1": 101})
        for name in ("normal", "heroic"):
            self.assertEqual(by_tier[name].tier.itemization["spell_power_per_dps"], 3.0)
            self.assertTrue(by_tier[name].breakdown["spell_power_stripped"])
        above = by_tier["empowered_1"]
        self.assertEqual(above.tier.itemization["spell_power_per_dps"], 0.0)
        self.assertFalse(above.breakdown["spell_power_stripped"])
        self.assertEqual(above.breakdown["weapon_spell_power"], 0)
        off_above = next(t for t in off.tiers if t.tier.tier == "empowered_1")
        self.assertEqual(above.row, off_above.row)  # exactly the feature-off stats, budgeted Spell Power included
        self.assertIn(SP, dict(lines(above.row)))

    def test_undeclared_above_100_left_alone_or_reset(self):
        rows = live_rows()
        for entry in (UNDECLARED, LITERAL_CASTER):
            rows[entry] = {**rows[entry], "ItemLevel": 101}
        tbl = tables()
        result = undeclared(tbl, rows=rows)
        self.assertEqual((result.rows, result.covered, result.unclassifiable), ([], [], []))
        # A coefficient a run gave it earlier goes back to 0.
        tbl["item_itemization"][(UNDECLARED,)]["spell_power_per_dps"] = 3.0
        [row] = undeclared(tbl, rows=rows).rows
        self.assertEqual((row["entry"], row["spell_power_per_dps"]), (UNDECLARED, 0.0))


class ValidationMirrorTest(unittest.TestCase):
    """ItemBudget.cpp refuses a negative spell_power_per_dps, or a nonzero one on a non-weapon (the item stays
    unmaterialized); item_lib.budget refuses the same rows, so a check fails first."""

    def test_negative_or_non_weapon_refused(self):
        tbl = tables()
        catalog = shapes.catalog(tbl)
        weapon = live_rows()[UNDECLARED]
        itemization = dict(tbl["item_itemization"][(UNDECLARED,)])
        with self.assertRaisesRegex(budget.BudgetError, "spell_power_per_dps"):
            budget.compute_breakdown(weapon, {**itemization, "spell_power_per_dps": -0.5}, tbl, catalog)
        armor = {**weapon, "class": 4, "subclass": 1, "InventoryType": 6}
        with self.assertRaisesRegex(budget.BudgetError, "spell_power_per_dps"):
            budget.compute_breakdown(armor, {**itemization, "spell_power_per_dps": 1.0}, tbl, catalog)
        budget.compute_breakdown(armor, itemization, tbl, catalog)  # 0 on a non-weapon is fine


class UndeclaredTest(unittest.TestCase):
    def test_undeclared_caster_covered(self):
        tbl = tables()
        result = undeclared(tbl, owned={CASTER_ENTRY, 5187})
        self.assertEqual(result.errors, [])
        self.assertEqual(result.covered, [UNDECLARED])
        [new_row] = result.rows
        self.assertEqual(new_row["entry"], UNDECLARED)
        self.assertEqual(new_row["spell_power_per_dps"], 3.0)
        for column in item_emit.ITEMIZATION_COLUMNS:
            self.assertIn(column, new_row)
        self.assertEqual({k: v for k, v in new_row.items() if k != "spell_power_per_dps"},
                         {k: v for k, v in tbl["item_itemization"][(UNDECLARED,)].items()
                          if k != "spell_power_per_dps"})
        b = budget.compute_breakdown(live_rows()[UNDECLARED], new_row, tbl, shapes.catalog(tbl))
        got = lines(budget.materialized_item_fields(b))
        self.assertEqual([s for s, _ in got].count(SP), 1)
        self.assertEqual(got[-1], (SP, budget._round(3.0 * b["final_dps"])))
        self.assertEqual(result.unclassifiable, [(LITERAL_CASTER, f"Item {LITERAL_CASTER}")])
        # Owned entries are the declarations'.
        self.assertEqual(undeclared(tbl, owned={UNDECLARED}).rows, [])

    def test_back_to_zero_writes_zero(self):
        tbl = tables()
        tbl["item_itemization"][(UNDECLARED,)]["spell_power_per_dps"] = 3.0  # a run with the feature on applied
        self.assertEqual(undeclared(tbl).rows, [])  # same constant: nothing changes
        [row] = undeclared(tbl, k=None).rows  # the constant back at 0
        self.assertEqual((row["entry"], row["spell_power_per_dps"]), (UNDECLARED, 0.0))

    def test_rendered_block(self):
        tbl = tables()
        exp, em = run([caster()], k=K, tbl=tbl)
        em.itemization_rows += undeclared(tbl, owned={CASTER_ENTRY}).rows
        rendered = item_emit.render(em, live_rows(), tbl)
        block = next(b for b in rendered.blocks if "item_itemization" in b)
        self.assertIn("`spell_power_per_dps`", block)
        self.assertIn(str(UNDECLARED), block)


if __name__ == "__main__":
    unittest.main()
