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
writes 0 back; a weapon above item level 100 gets the rule too (no item level limit, user ruling 2026-11-20; declared
tier by tier, and undeclared); a negative k raises; the coefficient is rounded to 4 decimals; item_lib.budget refuses
the rows ItemBudget.cpp refuses (negative, or nonzero on a non-weapon).

LS4 (secondary stat curve, handoff 1.8): a caster Main Hand / One-Hand / Two-Hand takes the physical role cell's
budget_mult and dps_delta 0 (declared tiers, a live first tier, undeclared rows); a declared budget_mult= / extra_dps=
wins; a melee physical weapon, a wand and a thrown weapon are unchanged; a bow, gun and crossbow get dps_delta 0 and
keep their budget_mult; a missing or `none` physical cell falls back (same slot, nearest bucket, then the other
Quality) and the fallback is reported; the lock is never appended to; the staff factor is 0.835.

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
OFF = W.k_table(0.0)  # the feature off (the shipped constant is 3.75 since 2026-11-20)
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


# The frozen physical cells of the fixtures (a subset of the real lock's lines): One-Hand and Two-Hand at 1-59 and
# 60-100, a ranged slot, thrown, and the caster cells a wand and the old rule read.
PHYS_LOCK = """\
physical 13 3 1-59 0.7180 0.0000
physical 13 3 60-100 0.4450 0.0000
physical 13 4 60-100 0.4450 -0.0010
physical 15 3 60-100 0.4050 -0.1379
physical 17 3 1-59 1.0000 0.0552
physical 17 3 60-100 0.7910 0.1013
physical 17 4 60-100 0.7910 0.0695
physical 25 3 60-100 0.3890 0.1119
physical 26 3 60-100 0.4150 -0.1394
caster 13 3 1-59 0.6850 -0.2000
caster 13 3 60-100 0.5070 -0.2000
caster 13 4 60-100 0.5070 -0.2000
caster 17 3 60-100 1.0150 -0.2000
caster 26 3 60-100 0.5160 -0.2000
"""


def run(items, k=None, tbl=None, rows=None, lock=PHYS_LOCK):
    tbl = tbl if tbl is not None else tables()
    exp = F.run(items, rows=rows or live_rows(), tables=tbl, spell_power_k=k, cells_lock_text=lock)
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
        self.assertEqual(W.ONE_HAND_K, 3.75)  # user ruling 2026-11-20 (level60-stat-curve 1.9)
        self.assertEqual(W.K_SP, W.k_table(3.75))
        self.assertAlmostEqual(W.K_SP["two_hand"], 3.75 * 0.835)
        self.assertEqual(W.K_SP["ranged"], 0.0)
        self.assertTrue(W.enabled())
        self.assertEqual(W.SLOT_FACTORS, {"one_hand": 1.0, "two_hand": 0.835, "ranged": 0.0})
        self.assertEqual(W.k_table(4.0), {"one_hand": 4.0, "two_hand": 4.0 * 0.835, "ranged": 0.0})
        self.assertTrue(W.enabled(K))

    def test_coefficient(self):
        self.assertEqual(W.coefficient(2, 13, 1.0, K), 3.0)
        self.assertEqual(W.coefficient(2, 21, 1.0, K), 3.0)
        self.assertEqual(W.coefficient(2, 17, 0.5, K), round(3.0 * 0.835 * 0.5, 4))
        self.assertEqual(W.coefficient(2, 26, 1.0, K), 0.0)  # a wand gets none
        self.assertEqual(W.coefficient(4, 13, 1.0, K), 0.0)  # not a weapon
        self.assertEqual(W.coefficient(2, 13, 0.0, K), 0.0)
        self.assertEqual(W.coefficient(2, 13, 1.0), 3.75)  # the shipped constants
        self.assertEqual(W.coefficient(2, 13, 1.0, OFF), 0.0)
        # Rounded to 4 decimals (a FLOAT column read back as text): 3.4567 x 0.835 = 2.88634 -> 2.8863.
        self.assertEqual(W.coefficient(2, 17, 1.0, W.k_table(3.4567)), 2.8863)

    def test_no_item_level_limit(self):
        # User ruling 2026-11-20 (Scarlet gear review M2): no upper item level bound, so no constant and no argument.
        self.assertFalse(hasattr(W, "MAX_ITEM_LEVEL"))
        self.assertNotIn("item_level", W.coefficient.__code__.co_varnames)

    def test_negative_k_refused(self):
        with self.assertRaisesRegex(ValueError, "must be a number >= 0"):
            W.k_table(-3.5)
        with self.assertRaisesRegex(ValueError, "must be a number >= 0"):
            W.coefficient(2, 13, 1.0, {"one_hand": -1.0, "two_hand": 0.0, "ranged": 0.0})


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
                coef = W.coefficient(item.item_class, item.inventory_type, want, K)
                self.assertAlmostEqual(tier.itemization["spell_power_per_dps"], coef)

    def test_override(self):
        exp, _ = run([caster(weapon_spell_power_mult=0.0), F.hammer(weapon_spell_power_mult=0.5)], k=K)
        mults = {t.key: t.spell_power_mult for item in exp.items for t in item.tiers}
        self.assertEqual(mults, {"scholo_witchblade": 0.0, "dm_hammer": 0.5})
        hammer = next(t for item in exp.items for t in item.tiers if t.key == "dm_hammer")
        self.assertEqual(hammer.itemization["spell_power_per_dps"], round(3.0 * 0.835 * 0.5, 4))  # a two-hand
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
        # Declared budget_mult= / extra_dps= win over the physical stat budget rule (LS4), so both sides get the same.
        exp, on = run([caster(budget_mult=0.5, extra_dps=-0.2)], k=K, tbl=tbl)
        _, off = run([caster(budget_mult=0.5, extra_dps=-0.2)], k=OFF, tbl=tbl)
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
        _, default = run(items, k=OFF)
        _, zeros = run(items, k=W.k_table(0.0))
        self.assertEqual([t.row for t in default.tiers], [t.row for t in zeros.tiers])
        for tier_rows in default.tiers:
            self.assertFalse(tier_rows.breakdown["spell_power_stripped"])
            self.assertEqual(tier_rows.tier.itemization["spell_power_per_dps"], 0.0)
        # The caster keeps its budgeted Spell Power with the feature off.
        self.assertTrue(any(s == SP for t in default.tiers for s, _ in lines(t.row)))
        result = undeclared(tables(), k=OFF)
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


class NoItemLevelLimitTest(unittest.TestCase):
    """User ruling 2026-11-20 (Scarlet gear review M2, replacing the 2026-11-17 WS0 review limit at item level 100):
    weapon spell power scales through TBC and WotLK, so a weapon above item level 100 gets the rule like any other,
    declared tier by tier and undeclared."""

    def test_declared_tier_above_100_gets_weapon_spell_power(self):
        ladder = D.ladder(
            "ws_ilvl_limit",
            normal=D.tier(step=0, label="Normal"),
            heroic=D.tier(step=1, ilvl=100, quality=D.Quality.EPIC, required_level=60, label="Heroic"),
            empowered_1=D.tier(step=2, ilvl=101, quality=D.Quality.EPIC, required_level=60, label="Empowered"),
        )
        exp, em = run([caster(ladder=ladder)], k=K)
        self.assertEqual(em.errors, [])
        by_tier = {t.tier.tier: t for t in em.tiers}
        self.assertEqual({name: t.tier.ilvl for name, t in by_tier.items()},
                         {"normal": 61, "heroic": 100, "empowered_1": 101})
        for name in ("normal", "heroic", "empowered_1"):
            tier = by_tier[name]
            self.assertEqual(tier.tier.itemization["spell_power_per_dps"], 3.0, name)
            self.assertTrue(tier.breakdown["spell_power_stripped"], name)
            self.assertGreater(tier.breakdown["weapon_spell_power"], 0, name)
            self.assertEqual([s for s, _ in lines(tier.row)].count(SP), 1, name)

    def test_undeclared_above_100_covered(self):
        rows = live_rows()
        for entry in (UNDECLARED, LITERAL_CASTER):
            rows[entry] = {**rows[entry], "ItemLevel": 101}
        tbl = tables()
        result = undeclared(tbl, owned={CASTER_ENTRY, 5187}, rows=rows)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.covered, [UNDECLARED])
        [row] = result.rows
        self.assertEqual((row["entry"], row["spell_power_per_dps"]), (UNDECLARED, 3.0))
        self.assertEqual(result.unclassifiable, [(LITERAL_CASTER, f"Item {LITERAL_CASTER}")])


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
        [row] = undeclared(tbl, k=OFF).rows  # the constant back at 0
        self.assertEqual((row["entry"], row["spell_power_per_dps"]), (UNDECLARED, 0.0))

    def test_rendered_block(self):
        tbl = tables()
        exp, em = run([caster()], k=K, tbl=tbl)
        em.itemization_rows += undeclared(tbl, owned={CASTER_ENTRY}).rows
        rendered = item_emit.render(em, live_rows(), tbl)
        block = next(b for b in rendered.blocks if "item_itemization" in b)
        self.assertIn("`spell_power_per_dps`", block)
        self.assertIn(str(UNDECLARED), block)


# ---------------------------------------------------------------------------------------------------------------------
# LS4: the physical stat budget


MH_CASTER, STAFF_CASTER, BOW, GUN, CROSSBOW, WAND, THROWN, MELEE_2H, LIVE_CASTER = (
    9101, 9102, 9103, 9104, 9105, 9106, 9107, 9108, 9109)
UNDECLARED_BOW = 9110
SPIRIT_LEAD = "Spirit/SpellPower, SpellPower lead"


def ls4_tables() -> dict:
    t = tables()
    for inv in (15, 21, 22, 25, 26):
        t["item_slot_mult"][(inv,)] = {"mult": 0.5625}
    t["item_itemization"][(LIVE_CASTER,)] = {
        "entry": LIVE_CASTER, "budget_mult": 0.507, "stamina_delta": 0, "dps_delta": -6.0, "absorbed_spell_slots": 0,
        "armor_delta": 0, "primary_shape_id": 5, "secondary_shape_id": 25, "primary_share": 6000,
        "block_value_delta": 0, "spell_power_per_dps": 0.0,
    }
    t["item_itemization"][(UNDECLARED_BOW,)] = {
        "entry": UNDECLARED_BOW, "budget_mult": 0.405, "stamina_delta": 0, "dps_delta": -3.0,
        "absorbed_spell_slots": 0, "armor_delta": 0, "primary_shape_id": 23, "secondary_shape_id": 25,
        "primary_share": 6000, "block_value_delta": 0, "spell_power_per_dps": 0.0,
    }
    return t


def ls4_rows() -> dict[int, dict]:
    rows = live_rows()
    for entry, sub, inv, delay in ((MH_CASTER, 15, 21, 1800), (STAFF_CASTER, 10, 17, 3000), (BOW, 2, 15, 2800),
                                   (GUN, 3, 26, 2800), (CROSSBOW, 18, 26, 2800), (WAND, 19, 26, 1500),
                                   (THROWN, 16, 25, 1500), (MELEE_2H, 5, 17, 3000), (LIVE_CASTER, 15, 13, 1800),
                                   (UNDECLARED_BOW, 2, 15, 2800)):
        rows[entry] = F._row(entry, ItemLevel=40 if entry == UNDECLARED_BOW else 61, Quality=3,
                             **{"class": 2, "subclass": sub, "InventoryType": inv, "delay": delay, "displayid": 1})
    return rows


def ls4_item(key, entry, **kw) -> D.ItemDecl:
    args = dict(base=entry, ladder=F.ladder_dungeon())
    args.update(kw)
    return D.item(key, **args)


def ls4_run(items, lock=PHYS_LOCK, k=None):
    return run(items, k=k, tbl=ls4_tables(), rows=ls4_rows(), lock=lock)


def tiers_of(exp, key):
    return {t.tier: t for item in exp.items for t in item.tiers if t.key == key}


def curve_dps(tier) -> float:
    return tier.baselines["dps"]


class PhysicalBudgetTest(unittest.TestCase):
    def assert_physical(self, exp, key, cells):
        """Every tier takes the physical cell `cells[tier]` and no DPS credit."""
        for name, mult in cells.items():
            tier = tiers_of(exp, key)[name]
            self.assertEqual(exp.errors, [])
            self.assertEqual(tier.itemization["budget_mult"], mult, (key, name))
            self.assertEqual(tier.itemization["dps_delta"], 0.0, (key, name))
            self.assertGreater(tier.itemization["spell_power_per_dps"], 0.0, (key, name))

    def test_one_hand_takes_the_physical_cell(self):
        exp, _ = ls4_run([caster()])  # Witchblade: ilvl 61 Rare, 66 / 76 Epic
        self.assert_physical(exp, "scholo_witchblade", {"normal": 0.445, "heroic": 0.445, "empowered_1": 0.445})
        self.assertIn("physical", tiers_of(exp, "scholo_witchblade")["normal"].budget_source)

    def test_main_hand_uses_the_one_hand_cell(self):
        exp, _ = ls4_run([ls4_item("ws_mh", MH_CASTER, primary=SPIRIT_LEAD, secondary="Crit (Solo)")])
        self.assert_physical(exp, "ws_mh", {"normal": 0.445, "heroic": 0.445})

    def test_two_hand_takes_the_physical_cell(self):
        exp, _ = ls4_run([ls4_item("ws_staff", STAFF_CASTER, primary=SPIRIT_LEAD, secondary="Crit (Solo)")])
        self.assert_physical(exp, "ws_staff", {"normal": 0.791, "heroic": 0.791, "empowered_1": 0.791})
        for tier in tiers_of(exp, "ws_staff").values():
            self.assertAlmostEqual(tier.itemization["spell_power_per_dps"], W.coefficient(2, 17, 1.0), places=4)

    def test_declared_budget_mult_and_extra_dps_win(self):
        exp, _ = ls4_run([caster(budget_mult=0.9)])
        for tier in tiers_of(exp, "scholo_witchblade").values():
            self.assertEqual(tier.itemization["budget_mult"], 0.9)
            self.assertEqual(tier.itemization["dps_delta"], 0.0)
        exp, _ = ls4_run([caster(extra_dps=0.1)])
        for tier in tiers_of(exp, "scholo_witchblade").values():
            self.assertEqual(tier.itemization["budget_mult"], 0.445)
            self.assertEqual(tier.itemization["dps_delta"], round(0.1 * curve_dps(tier), 4))

    def test_live_first_tier_and_higher_tiers(self):
        tbl = ls4_tables()
        exp = F.run([ls4_item("ws_live", LIVE_CASTER, itemization="live")], rows=ls4_rows(), tables=tbl,
                    cells_lock_text=PHYS_LOCK)
        self.assertEqual(exp.errors, [])
        for tier in tiers_of(exp, "ws_live").values():
            self.assertEqual((tier.itemization["budget_mult"], tier.itemization["dps_delta"]), (0.445, 0.0), tier.tier)

    def test_melee_wand_and_thrown_are_unchanged(self):
        exp, _ = ls4_run([
            ls4_item("ws_melee", MELEE_2H, primary="Strength (Solo)", secondary="Crit (Solo)"),
            ls4_item("ws_wand", WAND, primary=SPIRIT_LEAD, secondary="Crit (Solo)"),
            ls4_item("ws_thrown", THROWN, primary="Agility (Solo)", secondary="Crit (Solo)"),
        ])
        self.assertEqual(exp.errors, [])
        melee = tiers_of(exp, "ws_melee")["normal"]  # physical 2H at 60-100 Rare: its own mult and DPS fraction
        self.assertEqual(melee.itemization["budget_mult"], 0.791)
        self.assertEqual(melee.itemization["dps_delta"], round(0.1013 * curve_dps(melee), 4))
        self.assertEqual(melee.itemization["spell_power_per_dps"], 0.0)
        wand = tiers_of(exp, "ws_wand")["normal"]  # a caster wand keeps the caster cell and its -20% DPS
        self.assertEqual(wand.itemization["budget_mult"], 0.516)
        self.assertEqual(wand.itemization["dps_delta"], round(-0.2 * curve_dps(wand), 4))
        self.assertEqual(wand.itemization["spell_power_per_dps"], 0.0)
        thrown = tiers_of(exp, "ws_thrown")["normal"]
        self.assertEqual(thrown.itemization["budget_mult"], 0.389)
        self.assertEqual(thrown.itemization["dps_delta"], round(0.1119 * curve_dps(thrown), 4))

    def test_bow_gun_crossbow_get_no_dps_credit_and_keep_budget_mult(self):
        exp, _ = ls4_run([
            ls4_item("ws_bow", BOW, primary="Agility (Solo)", secondary="Crit (Solo)"),
            ls4_item("ws_gun", GUN, primary="Agility (Solo)", secondary="Crit (Solo)"),
            ls4_item("ws_xbow", CROSSBOW, primary="Agility (Solo)", secondary="Crit (Solo)"),
        ])
        self.assertEqual(exp.errors, [])
        for key, mult in (("ws_bow", 0.405), ("ws_gun", 0.415), ("ws_xbow", 0.415)):
            tier = tiers_of(exp, key)["normal"]
            self.assertEqual(tier.itemization["budget_mult"], mult, key)
            self.assertEqual(tier.itemization["dps_delta"], 0.0, key)
            self.assertEqual(tier.itemization["spell_power_per_dps"], 0.0, key)
        # A declared extra_dps= wins over the rule.
        exp, _ = ls4_run([ls4_item("ws_bow", BOW, primary="Agility (Solo)", secondary="Crit (Solo)", extra_dps=-0.1)])
        tier = tiers_of(exp, "ws_bow")["normal"]
        self.assertEqual(tier.itemization["dps_delta"], round(-0.1 * curve_dps(tier), 4))

    def test_dps_feeds_only_the_power(self):
        """The curve DPS is higher by exactly the credit the old rule took off, and the stats follow."""
        exp, em = ls4_run([caster()])
        _, old = run([caster()], tbl=ls4_tables(), rows=ls4_rows(),
                     lock=PHYS_LOCK.replace("physical 13 3 60-100 0.4450 0.0000", "physical 13 3 60-100 0.5070 -0.2"))
        self.assertEqual(em.errors, [])
        new = em.tiers[0].breakdown
        self.assertAlmostEqual(new["final_dps"], tiers_of(exp, "scholo_witchblade")["normal"].baselines["dps"], 3)
        self.assertLess(new["effective_budget"], old.tiers[0].breakdown["effective_budget"])

    def test_off_switch_changes_nothing(self):
        exp, _ = ls4_run([caster()], k=OFF)
        for tier in tiers_of(exp, "scholo_witchblade").values():
            self.assertEqual(tier.itemization["spell_power_per_dps"], 0.0)
            self.assertEqual(tier.itemization["budget_mult"], 0.507)  # the caster cell
            self.assertEqual(tier.itemization["dps_delta"], round(-0.2 * curve_dps(tier), 4))

    def test_missing_physical_cell_falls_back_and_is_reported(self):
        # Level 101+ has no physical One-Hand cell: the nearest bucket (60-100) answers and the run says so.
        ladder = D.ladder(
            "ws_high",
            normal=D.tier(step=0, label="Normal"),
            empowered_1=D.tier(step=1, ilvl=101, quality=D.Quality.EPIC, required_level=60, label="Empowered"),
        )
        exp, _ = ls4_run([caster(ladder=ladder)])
        self.assertEqual(exp.errors, [])
        self.assertEqual(tiers_of(exp, "scholo_witchblade")["empowered_1"].itemization["budget_mult"], 0.445)
        self.assertIn("fallback", tiers_of(exp, "scholo_witchblade")["empowered_1"].budget_source)
        self.assertEqual(len(exp.physical_cells.fallbacks), 1)
        [text] = exp.physical_cells.fallbacks.values()
        self.assertIn("Quality 4 101-200 -> Quality 4 60-100", text)
        self.assertIn("fallback", exp.physical_cells.notes()[0])

    def test_no_physical_cell_at_all_is_an_error(self):
        exp, _ = ls4_run([caster()], lock="caster 13 3 60-100 0.5070 -0.2000\n")
        self.assertTrue(any("no physical role cell" in e for e in exp.errors), exp.errors)

    def test_lock_is_never_appended(self):
        exp, _ = ls4_run([caster()])
        self.assertEqual(exp.errors, [])
        self.assertEqual(exp.cells_lock_appended, [])  # the physical cells are read, not frozen


class PhysicalCellsTest(unittest.TestCase):
    def cells(self, text, live=None):
        from lib import item_variants as V  # noqa: PLC0415

        return W.PhysicalCells(V.parse_cells_lock(text), live or V.RoleCells())

    def test_exact_cell_and_slot_mapping(self):
        pc = self.cells(PHYS_LOCK)
        self.assertEqual(pc.lookup(13, 3, 70)[0], 0.445)
        self.assertEqual(pc.lookup(21, 3, 70)[0], 0.445)  # Main Hand reads One-Hand
        self.assertEqual(pc.lookup(22, 3, 70)[0], 0.445)  # so does an Off Hand weapon
        self.assertEqual(pc.lookup(17, 4, 70)[0], 0.791)
        self.assertIsNone(pc.lookup(99, 3, 70))  # a slot without a physical cell mapping
        self.assertEqual(pc.fallbacks, {})

    def test_none_cell_falls_back_to_the_other_quality(self):
        pc = self.cells("physical 13 4 60-100 none\nphysical 13 3 60-100 0.5000 0.0\n")
        self.assertEqual(pc.lookup(13, 4, 70)[0], 0.5)
        self.assertEqual(len(pc.fallbacks), 1)

    def test_same_quality_wins_over_a_nearer_bucket_of_another(self):
        pc = self.cells("physical 13 4 1-59 0.6000 0.0\nphysical 13 3 101-200 0.9000 0.0\n")
        self.assertEqual(pc.lookup(13, 4, 150)[0], 0.6)

    def test_tie_takes_the_lower_bucket(self):
        pc = self.cells("physical 13 3 1-59 0.7000 0.0\nphysical 13 3 101-200 0.9000 0.0\n")
        self.assertEqual(pc.lookup(13, 3, 70)[0], 0.7)

    def test_nothing_at_all(self):
        pc = self.cells("caster 13 3 60-100 0.5 -0.2\n")
        self.assertIsNone(pc.lookup(13, 3, 70))

    def test_live_sample_for_an_absent_cell_and_the_lock_stays_put(self):
        from lib import item_variants as V  # noqa: PLC0415

        live = V.RoleCells()
        for mult in (0.30, 0.31, 0.32):
            live.add("physical", 13, 3, 70, mult, 0.0)
        frozen = V.parse_cells_lock("")
        pc = W.PhysicalCells(frozen, live)
        self.assertEqual(pc.lookup(13, 3, 70)[0], 0.31)
        self.assertEqual(frozen, {})  # read only

    def test_frozen_none_beats_the_live_sample(self):
        from lib import item_variants as V  # noqa: PLC0415

        live = V.RoleCells()
        for mult in (0.30, 0.31, 0.32):
            live.add("physical", 13, 3, 70, mult, 0.0)
        pc = W.PhysicalCells(V.parse_cells_lock("physical 13 3 60-100 none\n"), live)
        # The frozen `none` is a miss; the fallback scan then reaches the live sample of another key (same slot).
        self.assertEqual(pc.lookup(13, 3, 70)[0], 0.31)
        self.assertEqual(len(pc.fallbacks), 1)


class UndeclaredPhysicalTest(unittest.TestCase):
    def cells(self):
        from lib import item_variants as V  # noqa: PLC0415

        return W.PhysicalCells(V.parse_cells_lock(PHYS_LOCK), V.RoleCells())

    def result(self, cells=True):
        tbl = ls4_tables()
        return W.undeclared_rows(ls4_rows(), {CASTER_ENTRY, 5187}, tbl, shapes.catalog(tbl), k=K,
                                 cells=self.cells() if cells else None)

    def test_caster_and_bow_rows(self):
        result = self.result()
        self.assertEqual(result.errors, [])
        rows = {r["entry"]: r for r in result.rows}
        caster_row = rows[UNDECLARED]  # ilvl 40 Rare One-Hand: 1-59 physical cell
        self.assertEqual((caster_row["budget_mult"], caster_row["dps_delta"], caster_row["spell_power_per_dps"]),
                         (0.718, 0.0, 3.0))
        bow = rows[UNDECLARED_BOW]
        self.assertEqual((bow["budget_mult"], bow["dps_delta"], bow["spell_power_per_dps"]), (0.405, 0.0, 0.0))
        self.assertNotIn(PHYS_UNDECLARED, rows)  # a physical melee weapon is untouched
        self.assertNotIn(WAND, rows)  # so is a wand
        kinds = {t[0]: t[5] for t in result.stat_budget}
        self.assertEqual(kinds[UNDECLARED], "caster")
        self.assertEqual(kinds[UNDECLARED_BOW], "hunter ranged")

    def test_second_run_changes_nothing(self):
        tbl = ls4_tables()
        for row in self.result().rows:
            tbl["item_itemization"][(row["entry"],)] = row
        again = W.undeclared_rows(ls4_rows(), {CASTER_ENTRY, 5187}, tbl, shapes.catalog(tbl), k=K, cells=self.cells())
        self.assertEqual(again.rows, [])

    def test_no_cells_leaves_the_budget_mult(self):
        rows = {r["entry"]: r for r in self.result(cells=False).rows}
        self.assertEqual(rows[UNDECLARED]["budget_mult"], 0.507)
        self.assertEqual(rows[UNDECLARED]["dps_delta"], -6.0)
        self.assertEqual(rows[UNDECLARED_BOW]["dps_delta"], 0.0)  # the bow rule needs no cells

    def test_the_budget_still_resolves(self):
        tbl = ls4_tables()
        row = next(r for r in self.result().rows if r["entry"] == UNDECLARED)
        b = budget.compute_breakdown(ls4_rows()[UNDECLARED], row, tbl, shapes.catalog(tbl))
        self.assertGreater(b["weapon_spell_power"], 0)


if __name__ == "__main__":
    unittest.main()
