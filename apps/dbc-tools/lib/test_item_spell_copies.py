"""
Item variants IV10: per-tier copies of the `scale="budget"` item effect spells (lib/item_spell_copies.py).

Checks:
  - the ratio formula, and the four ratios of the hard mode ladder (71 / 81 / 91 / 101 Epic) on the replayed
    itemization tables, trinket and ring slots alike;
  - stable ids: minted from the item_spell_copy block after the lock's highest id, skipping declared and live ids; a
    rerun over the written lock mints nothing and gives the same ids; the declaration order never moves a locked id;
    the retire guard;
  - the copies: potency scaled by the ratio (and nothing else: durations, cooldowns, radius, proc chance, aura
    amounts), every family id remapped inside the tier (trigger spells, $<id> tokens, pot_text expressions, linked
    spells, procs and script bindings), each tier's tooltip carrying its own numbers;
  - the refusals (a damage effect without potency, a hand bonus row, a bare id with scale=);
  - the real source: the three VanCleef hard mode items get 21 copies at 205410-205430 with the expected families,
    and the committed ItemSpellCopies.h matches what those copies render.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_item_spell_copies.py
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import item_spell_copies as C  # noqa: E402
from lib import item_variants  # noqa: E402
from lib.dsl import items as D  # noqa: E402
from lib.dsl.model import Effect, Spell  # noqa: E402
from lib.dsl.registry import pot_text  # noqa: E402

IDS_CFG = {"item_spell_copy": {"start": 205410, "end": 205599}}
EPIC = int(D.Quality.EPIC)
TRINKET, RING = 12, 11
LADDER = D.ladder(
    "hm",
    heroic_hm=D.tier(step=1, ilvl=71, quality=EPIC, required_level=60, label="Heroic Hard Mode"),
    empowered_1_hm=D.tier(step=2, ilvl=81, quality=EPIC, required_level=60, label="Molten Empowered Hard Mode"),
    empowered_2_hm=D.tier(step=3, ilvl=91, quality=EPIC, required_level=60, label="Draconic Empowered Hard Mode"),
    empowered_3_hm=D.tier(step=4, ilvl=101, quality=EPIC, required_level=60, label="Chthonic Empowered Hard Mode"),
)
BUDGET = {71: 55, 81: 58, 91: 61, 101: 69}  # item_budget_curve, live 2026-11-06
DIRECT, SCHOOL_DAMAGE, DUMMY, APPLY_AURA, AURA_DUMMY, HEAL = "direct", 2, 3, 6, 4, 10


def fixture_tables() -> dict:
    return {
        "item_budget_curve": {(ilvl,): {"ilvl": ilvl, "budget": b} for ilvl, b in BUDGET.items()},
        "item_quality_mult": {(EPIC,): {"quality": EPIC, "mult": 1.0}},
        "item_slot_mult": {(TRINKET,): {"mult": 0.5625}, (RING,): {"mult": 0.5625}},
    }


def _raw(desc: str = "", aura: str = "", **more) -> dict:
    return {"SpellLevel": 1, "EquippedItemClass": -1, "Description_Lang_enUS": desc,
            "AuraDescription_Lang_enUS": aura, **more}


class Family:
    """A synthetic effect family: use 100 (lob, $101d / $102a1 / pot_text(102) in its text), look 101 (2 s), blast
    102 (potency 150 SP + 150 AP, 6 yd), and an aura 103 whose effect triggers heal 104 (potency 80) and whose text
    shows pot_text(104); 105 is linked from 100 (cast). 106 is a stock-like spell outside source/items."""

    def __init__(self):
        self.blast = Spell(id=102, name="Blast", school=4, duration_ms=0, cooldown_ms=0, effects=[
            Effect(type=SCHOOL_DAMAGE, sp_potency=150.0, ap_potency=150.0, potency_kind=DIRECT, time_basis_ms=1500,
                   implicit_target_a=16, radius_yards=6.0)],
            raw_overrides=_raw("Deals {pot1} Fire damage within $a1 yd.", DefenseType=1))
        self.look = Spell(id=101, name="Look", duration_ms=2000, effects=[Effect(type=DUMMY)], raw_overrides=_raw())
        self.use = Spell(id=100, name="Use", cooldown_ms=120000, effects=[Effect(type=DUMMY)], raw_overrides=_raw(
            "Lob it. It explodes $101d later for " + pot_text(self.blast) + " damage within $102a1 yd. Not $106d."))
        self.heal = Spell(id=104, name="Heal", effects=[
            Effect(type=HEAL, sp_potency=80.0, potency_kind="heal", time_basis_ms=1500, implicit_target_a=1)],
            raw_overrides=_raw("Heals {pot1}.", DefenseType=1))
        self.aura = Spell(id=103, name="Aura", duration_ms=20000, effects=[
            Effect(type=APPLY_AURA, apply_aura=AURA_DUMMY, trigger_spell=104, base_points=-11, implicit_target_a=1)],
            raw_overrides=_raw("Heals for " + pot_text(self.heal) + ", -$s1%.", "Number-free."))
        self.linked = Spell(id=105, name="Linked", effects=[Effect(type=DUMMY)], raw_overrides=_raw())
        self.spells = [self.use, self.look, self.blast, self.aura, self.heal, self.linked]

    def dsl_classes(self, extra_bonus=()) -> dict:
        out = {key: [] for key in ("spells", "spell_bonus_data", "potency_corrections", "spell_procs",
                                   "spell_script_names", "custom_attrs", "linked_spells")}
        for spell in self.spells:
            entry = spell.to_entry()
            entry.update(_spell=spell, _source_class="items")
            out["spells"].append(entry)
            if spell.potency_bonus_row:
                out["spell_bonus_data"].append(spell.potency_bonus_row)
            out["potency_corrections"] += spell.potency_correction_rows
        out["spell_bonus_data"] += list(extra_bonus)
        out["spells"].append({"id": 106, "name": "Stock", "_source_class": "mage", "_spell": None})
        out["spell_procs"].append({"id": 103, "SpellId": 103, "Chance": 10.0, "Cooldown": 10000})
        out["spell_script_names"] += [{"id": "100:spell_use", "spell_id": 100, "ScriptName": "spell_use"},
                                      {"id": "103:spell_aura", "spell_id": 103, "ScriptName": "spell_aura"}]
        out["custom_attrs"].append({"id": 102, "spell_id": 102, "attributes": 8})
        out["linked_spells"].append({"id": "100:105:0", "spell_trigger": 100, "spell_effect": 105, "type": 0,
                                     "comment": "use -> linked"})
        return out


def resolved_item(decl: D.ItemDecl, inv_type: int, first_entry: int) -> item_variants.ResolvedItem:
    item = item_variants.ResolvedItem(decl=decl, source_row={}, like_columns={}, inventory_type=inv_type,
                                      item_class=4, subclass=0, sockets=())
    for n, spec in enumerate(decl.ladder.tiers):
        item.tiers.append(item_variants.ResolvedTier(
            key=decl.key, tier=spec.name, label=spec.label, entry=first_entry + n, stock=False, ilvl=spec.ilvl,
            quality=spec.quality, required_level=60, heroic_flag=False, variant_base=None, itemization={},
            columns={}, number=spec.step))
    return item


def expansion(*items, tables=None) -> item_variants.ItemExpansion:
    return item_variants.ItemExpansion(items=list(items), tables=tables or fixture_tables())


def keg(family: Family, key: str = "keg", scale: str | None = "budget",
        entry: int = 72000) -> item_variants.ResolvedItem:
    decl = D.item(key, name="Keg", like=10587, ladder=LADDER, primary=None, secondary="Crit (Solo)",
                  spells=(D.use_spell(family.use, scale=scale),))
    return resolved_item(decl, TRINKET, entry)


def ring(family: Family, key: str = "ring", entry: int = 72100) -> item_variants.ResolvedItem:
    decl = D.item(key, name="Ring", like=1076, ladder=LADDER, primary=None, secondary="Crit (Solo)",
                  spells=(D.equip_spell(family.aura, scale="budget"),))
    return resolved_item(decl, RING, entry)


def run(items, family=None, lock_text: str = "", taken=(), dsl=None):
    family = family or Family()
    dsl = dsl if dsl is not None else family.dsl_classes()
    out = C.expand(expansion(*items), dsl, IDS_CFG, lock=C.Lock(text=lock_text), taken_loader=lambda: taken,
                   today="2026-11-06")
    return out, dsl


def by_id(out) -> dict[int, dict]:
    return {int(e["id"]): e for e in out.spells}


class RatioTest(unittest.TestCase):
    def test_formula_on_the_fixture(self):
        t = fixture_tables()
        tiers = resolved_item(D.item("x", name="X", like=1, ladder=LADDER, primary=None, secondary="Crit (Solo)"),
                              TRINKET, 1).tiers
        self.assertEqual([C.tier_ratio(t, tiers[0], tier, TRINKET) for tier in tiers], [1.0, 1.0545, 1.1091, 1.2545])
        self.assertEqual(C.stat_budget(t, 81, EPIC, TRINKET), 58 * 1.0 * 0.5625)
        self.assertIsNone(C.stat_budget(t, 82, EPIC, TRINKET))  # no curve row

    def test_the_hard_mode_ladder_on_the_replayed_tables(self):
        try:
            tables, _ = item_variants.load_itemization_tables()
        except Exception as error:  # noqa: BLE001 - the replay needs the repo's SQL; skip on a bare checkout
            self.skipTest(f"itemization tables unavailable: {error}")
        first = item_variants.ResolvedTier("k", "a", "a", 1, False, 71, EPIC, 60, False, None, {}, {})
        for slot in (TRINKET, RING):
            got = []
            for ilvl in (71, 81, 91, 101):
                tier = item_variants.ResolvedTier("k", "b", "b", 2, False, ilvl, EPIC, 60, False, None, {}, {})
                got.append(C.tier_ratio(tables, first, tier, slot))
            self.assertEqual(got, [1.0, 1.0545, 1.1091, 1.2545], slot)


class IdTest(unittest.TestCase):
    def test_minted_in_order_after_the_lock_skipping_taken_ids(self):
        out, _ = run([keg(Family())], taken={205411})
        self.assertFalse(out.errors, out.errors)
        # family of the use: 100 (itself), 101, 102 (text), 105 (linked); 3 tiers above the first
        self.assertEqual(out.lock_appended[:5], [
            "205410 keg empowered_1_hm 100", "205412 keg empowered_1_hm 101", "205413 keg empowered_1_hm 102",
            "205414 keg empowered_1_hm 105", "205415 keg empowered_2_hm 100",
        ])
        self.assertEqual(len(out.lock_appended), 12)

    def test_rerun_over_the_written_lock_is_silent_and_stable(self):
        first, _ = run([keg(Family()), ring(Family())])
        second, _ = run([keg(Family()), ring(Family())], lock_text=first.lock_text)
        self.assertEqual(second.lock_appended, [])
        self.assertEqual(second.lock_text, first.lock_text)
        self.assertEqual([(t.key, t.tier, t.remap) for t in second.tiers],
                         [(t.key, t.tier, t.remap) for t in first.tiers])
        self.assertEqual(second.header_text, first.header_text)
        strip = [{k: v for k, v in e.items() if k != "_spell"} for e in first.spells]
        self.assertEqual([{k: v for k, v in e.items() if k != "_spell"} for e in second.spells], strip)
        # another order of the declarations keeps every locked id
        third, _ = run([ring(Family()), keg(Family())], lock_text=first.lock_text)
        self.assertEqual({(t.key, t.tier): t.remap for t in third.tiers},
                         {(t.key, t.tier): t.remap for t in first.tiers})

    def test_new_copies_go_after_the_highest_locked_id(self):
        first, _ = run([keg(Family())])
        lock = first.lock_text + "205599 gone empowered_1_hm 7 retired 2026-11-01\n"
        lock = lock.replace("205599", "205500")
        second, _ = run([keg(Family()), ring(Family())], lock_text=lock)
        self.assertFalse(second.errors, second.errors)
        self.assertEqual(min(int(line.split()[0]) for line in second.lock_appended), 205501)

    def test_retire_guard(self):
        first, _ = run([keg(Family())])
        out, _ = run([], lock_text=first.lock_text)
        self.assertEqual(len(out.errors), 12)
        self.assertIn("205410 keg empowered_1_hm 100 retired 2026-11-06", out.errors[0])
        retired = "".join(line + " retired 2026-11-06\n" if line[:1].isdigit() else line + "\n"
                          for line in first.lock_text.splitlines())
        self.assertFalse(run([], lock_text=retired)[0].errors)
        again, _ = run([keg(Family())], lock_text=retired)
        self.assertIn("retired on 2026-11-06", again.errors[0])

    def test_lock_parse_errors(self):
        for text, why in (("205410 keg t 100\n205410 keg u 100\n", "already on line"),
                          ("205410 keg t 100\n205411 keg t 100\n", "already on line"),
                          ("205409 keg t 100\n", "outside"), ("x keg t 100\n", "expected")):
            out, _ = run([keg(Family())], lock_text=text)
            self.assertTrue(out.errors and why in out.errors[0], (text, out.errors))

    def test_block_full(self):
        out = C.expand(expansion(keg(Family())), Family().dsl_classes(), {"item_spell_copy": {"start": 205410,
                                                                                           "end": 205412}},
                       lock=C.Lock(), taken_loader=tuple)
        self.assertTrue(any("is full" in e for e in out.errors))

    def test_no_scaled_spell_no_copies(self):
        out, _ = run([keg(Family(), scale=None)])
        self.assertEqual((out.errors, out.spells, out.lock_appended), ([], [], []))
        self.assertIn("kCopyCount = 0", out.header_text)


class CopyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.family = Family()
        cls.item = keg(cls.family)
        cls.out, cls.dsl = run([cls.item, ring(cls.family)], family=cls.family)
        assert not cls.out.errors, cls.out.errors
        cls.copies = by_id(cls.out)
        cls.tiers = {(t.key, t.tier): t for t in cls.out.tiers}

    def copy(self, key, tier, base) -> dict:
        return self.copies[self.tiers[(key, tier)].remap[base]]

    def test_family_is_what_the_root_reaches(self):
        self.assertEqual(sorted(self.tiers[("keg", "empowered_1_hm")].remap), [100, 101, 102, 105])
        self.assertEqual(sorted(self.tiers[("ring", "empowered_1_hm")].remap), [103, 104])  # trigger_spell 104
        self.assertNotIn(106, {b for t in self.out.tiers for b in t.remap})  # outside source/items: shared
        self.assertEqual(len(self.out.tiers), 6)  # 3 tiers above the first, 2 items; the first keeps the base ids

    def test_potency_scales_and_nothing_else(self):
        base = next(e for e in self.dsl["spells"] if e["id"] == 102)
        for tier, ratio in (("empowered_1_hm", 1.0545), ("empowered_2_hm", 1.1091), ("empowered_3_hm", 1.2545)):
            copy = self.copy("keg", tier, 102)
            spell = copy["_spell"]
            self.assertAlmostEqual(spell.effects[0].sp_potency, 150.0 * ratio)
            self.assertAlmostEqual(spell.effects[0].ap_potency, 150.0 * ratio)
            bonus = next(r for r in self.out.spell_bonus_data if r["entry"] == copy["id"])
            base_bonus = self.family.blast.potency_bonus_row
            self.assertAlmostEqual(bonus["direct_bonus"], base_bonus["direct_bonus"] * ratio)
            self.assertAlmostEqual(bonus["ap_bonus"], base_bonus["ap_bonus"] * ratio)
            self.assertGreater(copy["effect1"]["points_per_level"], base["effect1"]["points_per_level"])
            for key in ("radius_yards", "implicit_target_a", "type"):
                self.assertEqual(copy["effect1"][key], base["effect1"][key], key)
            self.assertEqual({r["spell_id"] for r in self.out.potency_corrections if r["spell_id"] == copy["id"]},
                             {copy["id"]})
            self.assertEqual(copy["name"], "Blast")
        use = self.copy("keg", "empowered_3_hm", 100)
        self.assertEqual((use["cooldown_ms"], use["duration_ms"]), (120000, None))
        look = self.copy("keg", "empowered_3_hm", 101)
        self.assertEqual(look["duration_ms"], 2000)
        aura = self.copy("ring", "empowered_3_hm", 103)
        self.assertEqual((aura["effect1"]["base_points"], aura["duration_ms"]), (-11, 20000))  # -10% stays
        heal = self.copy("ring", "empowered_3_hm", 104)
        self.assertAlmostEqual(heal["_spell"].effects[0].sp_potency, 80.0 * 1.2545)

    def test_trigger_chain_stays_in_the_tier(self):
        for tier in ("empowered_1_hm", "empowered_2_hm", "empowered_3_hm"):
            remap = self.tiers[("ring", tier)].remap
            aura = self.copies[remap[103]]
            self.assertEqual(aura["effect1"]["trigger_spell"], remap[104])
            remap = self.tiers[("keg", tier)].remap
            linked = [r for r in self.out.linked_spells if r["spell_trigger"] == remap[100]]
            self.assertEqual([(r["spell_effect"], r["type"], r["id"]) for r in linked],
                             [(remap[105], 0, f"{remap[100]}:{remap[105]}:0")])
            self.assertEqual([r for r in self.out.spell_procs if r["SpellId"] == self.tiers[("ring", tier)].remap[103]],
                             [{"id": remap_id, "SpellId": remap_id, "Chance": 10.0, "Cooldown": 10000,
                               "_source_class": "items"} for remap_id in [self.tiers[("ring", tier)].remap[103]]])
            names = {(r["spell_id"], r["ScriptName"]) for r in self.out.spell_script_names}
            self.assertIn((remap[100], "spell_use"), names)
            self.assertIn((self.tiers[("ring", tier)].remap[103], "spell_aura"), names)
            self.assertIn({"id": remap[102], "spell_id": remap[102], "attributes": 8, "_source_class": "items"},
                          self.out.custom_attrs)

    def test_tooltips_show_each_tier_its_own_numbers(self):
        base_text = self.family.use.raw_overrides["Description_Lang_enUS"]
        texts = []
        for tier in ("empowered_1_hm", "empowered_2_hm", "empowered_3_hm"):
            remap = self.tiers[("keg", tier)].remap
            use = self.copies[remap[100]]
            text = use["raw_overrides"]["Description_Lang_enUS"]
            blast = self.copies[remap[102]]
            self.assertIn(f"${remap[101]}d", text)
            self.assertIn(f"${remap[102]}a1", text)
            self.assertIn("$106d", text)  # a spell outside the family keeps its id
            self.assertNotRegex(text, r"\$10[0-5][a-z]")
            # the blast copy's own tooltip expressions, nothing of the base blast's
            own = C.tooltip_expressions(blast)[1]
            self.assertIn("${" + own[0] + "}", text)
            self.assertIn("${" + own[1] + "}", text)
            for expression in C.tooltip_expressions(next(e for e in self.dsl["spells"] if e["id"] == 102))[1]:
                self.assertNotIn(expression, text)
            self.assertNotIn("{pot", blast["raw_overrides"]["Description_Lang_enUS"])
            self.assertEqual(text.replace(f"${remap[101]}d", "$101d").replace(f"${remap[102]}a1", "$102a1")
                             .split(" for ")[0], base_text.split(" for ")[0])
            texts.append(text)
            ring_text = self.copies[self.tiers[("ring", tier)].remap[103]]["raw_overrides"]
            heal = self.copies[self.tiers[("ring", tier)].remap[104]]
            self.assertIn("${" + C.tooltip_expressions(heal)[1][0] + "}", ring_text["Description_Lang_enUS"])
            self.assertEqual(ring_text["AuraDescription_Lang_enUS"], "Number-free.")
        self.assertEqual(len(set(texts)), 3)
        coefficients = [float(re.search(r"([\d.]+)\*\$SP", t).group(1)) for t in texts]
        self.assertEqual(coefficients, sorted(coefficients))

    def test_item_tiers_name_their_copies(self):
        tiers = self.item.tiers
        self.assertIsNone(tiers[0].spells)  # the first tier keeps the declared spell
        for tier in tiers[1:]:
            self.assertEqual(tier.spells[0].spell_id, self.tiers[("keg", tier.tier)].remap[100])
            self.assertEqual(tier.spells[0].trigger, D.SpellTrigger.USE)

    def test_header(self):
        text = self.out.header_text
        rows = re.findall(r"\{ (\d+), (\d+), (\d+) \},  // (\w+) (\w+)", text)
        self.assertEqual(len(rows), len(self.out.spells))
        for copy, base, group, key, tier in rows:
            remap = self.tiers[(key, tier)].remap
            self.assertEqual(remap[int(base)], int(copy))
            self.assertEqual(int(group), min(remap.values()))
        self.assertTrue(all(len(line) <= 120 for line in text.splitlines()))


class RefusalTest(unittest.TestCase):
    def test_damage_without_potency(self):
        family = Family()
        family.blast = Spell(id=102, name="Blast", effects=[Effect(type=SCHOOL_DAMAGE, base_points=99)],
                             raw_overrides=_raw("x"))
        family.spells[2] = family.blast
        out, _ = run([keg(family)], family=family)
        self.assertTrue(any("without potency" in e for e in out.errors), out.errors)

    def test_hand_bonus_row(self):
        family = Family()
        hand = {"id": 101, "entry": 101, "direct_bonus": 0.5, "dot_bonus": 0, "ap_bonus": 0, "ap_dot_bonus": 0}
        out, _ = run([keg(family)], family=family, dsl=family.dsl_classes(extra_bonus=[hand]))
        self.assertTrue(any("bonus_coefficients" in e and "101" in e for e in out.errors), out.errors)

    def test_scale_needs_the_declared_spell(self):
        with self.assertRaises(D.ItemDeclarationError):
            D.use_spell(205400, scale="budget")
        with self.assertRaises(D.ItemDeclarationError):
            D.use_spell(Family().use, scale="ilvl")

    def test_spell_not_in_source_items(self):
        family = Family()
        dsl = family.dsl_classes()
        for entry in dsl["spells"]:
            if entry["id"] == 100:
                entry["_source_class"] = "mage"
        out, _ = run([keg(family)], family=family, dsl=dsl)
        self.assertTrue(any("declared in source/items" in e for e in out.errors), out.errors)


class ReferenceTierTest(unittest.TestCase):
    """Wave 1 integration: a ladder's `effect_reference` tier keeps the declared spells; every other tier, below it
    too, gets a copy scaled by budget(tier) / budget(reference)."""

    LADDER = D.ladder(
        "dungeon", effect_reference="heroic",
        normal=D.tier(step=0, label="Normal", sockets=False),
        heroic=D.tier(step=1, ilvl=71, quality=EPIC, required_level=60, label="Heroic"),
        empowered_1=D.tier(step=2, ilvl=81, quality=EPIC, required_level=60, label="Molten Empowered"),
    )

    def _item(self, family):
        decl = D.item("dagger", name="Dagger", like=10587, ilvl=91, quality=EPIC, required_level=60,
                      ladder=self.LADDER, primary=None, secondary="Crit (Solo)",
                      spells=(D.use_spell(family.use, scale="budget"),))
        item = resolved_item(decl, TRINKET, 73000)
        item.tiers[0].ilvl, item.tiers[0].quality = 91, EPIC  # the "Normal" tier sits above the reference here
        return item

    def test_the_reference_tier_keeps_the_declared_spells_and_the_first_tier_gets_a_copy(self):
        family = Family()
        out, _ = run([self._item(family)], family=family)
        self.assertFalse(out.errors, out.errors)
        tiers = {t.tier: t for t in out.tiers}
        self.assertEqual(set(tiers), {"normal", "empowered_1"})  # heroic keeps 100..105
        self.assertEqual(tiers["normal"].ratio, round(61 / 55, 4))
        self.assertEqual(tiers["empowered_1"].ratio, round(58 / 55, 4))
        blast = by_id(out)[tiers["normal"].remap[102]]["_spell"]
        self.assertAlmostEqual(blast.effects[0].sp_potency, 150.0 * round(61 / 55, 4))

    def test_a_reference_below_one(self):
        t = fixture_tables()
        low = item_variants.ResolvedTier("k", "n", "n", 1, False, 71, EPIC, 60, False, None, {}, {})
        ref = item_variants.ResolvedTier("k", "h", "h", 2, False, 101, EPIC, 60, False, None, {}, {})
        self.assertEqual(C.tier_ratio(t, ref, low, TRINKET), round(55 / 69, 4))
        self.assertLess(C.tier_ratio(t, ref, low, TRINKET), 1.0)

    def test_the_ladder_checks_its_reference(self):
        with self.assertRaises(D.ItemDeclarationError):
            D.ladder("x", effect_reference="nope", a=D.tier(step=0, label="A"))
        with self.assertRaises(D.ItemDeclarationError):  # deferred: never minted
            D.ladder("x", effect_reference="b", a=D.tier(step=0, label="A"),
                     b=D.tier(step=1, ilvl=70, quality=EPIC, required_level=60, label="B", deferred=True))
        self.assertIsNone(D.ladder("x", a=D.tier(step=0, label="A")).effect_reference)
        self.assertEqual(LADDER.effect_reference, None)

    def test_the_real_ladders(self):
        from source.items import ladders  # noqa: PLC0415

        self.assertEqual(ladders.VANILLA_DUNGEON.effect_reference, "heroic")
        self.assertEqual(ladders.VANILLA_HARD_MODE.effect_reference, "heroic_hm")


class StatAuraTest(unittest.TestCase):
    """Wave 1 integration: a copy scales stat-like aura amounts (STAT_AURAS) by the ratio; percentages and every
    effect with potency stay as they are."""

    MOD_RATING, MOD_STAT, MOD_RESISTANCE, MOD_INCREASE_SPEED, SCHOOL_ABSORB = 189, 29, 22, 31, 69

    def _copy(self, effects, ratio=1.2545):
        spell = Spell(id=110, name="Buff", duration_ms=15000, effects=effects, raw_overrides=_raw("$s1 rating."))
        index = C.SpellIndex(spells={110: spell}, entries={110: spell.to_entry()})
        return C.build_copies(index, [110], {110: 205500}, ratio, "test")[110]

    def test_ratings_stats_and_armor_scale_and_percentages_stay(self):
        copy = self._copy([
            Effect(type=APPLY_AURA, apply_aura=self.MOD_RATING, base_points=79, misc_value=917504),  # +80
            Effect(type=APPLY_AURA, apply_aura=self.MOD_INCREASE_SPEED, base_points=29),  # +30%
            Effect(type=APPLY_AURA, apply_aura=self.MOD_RESISTANCE, base_points=999, misc_value=1),  # +1000 armor
        ])
        self.assertEqual([e.base_points for e in copy.effects], [round(80 * 1.2545) - 1, 29, round(1000 * 1.2545) - 1])
        self.assertEqual(copy.effects[0].misc_value, 917504)

    def test_a_ratio_below_one_shrinks_the_amount(self):
        copy = self._copy([Effect(type=APPLY_AURA, apply_aura=self.MOD_STAT, base_points=9, misc_value=3)], 0.25)
        self.assertEqual(copy.effects[0].base_points, round(10 * 0.25) - 1)

    def test_a_potency_absorb_scales_by_potency_only(self):
        copy = self._copy([Effect(type=APPLY_AURA, apply_aura=self.SCHOOL_ABSORB, base_potency=300.0,
                                  potency_kind="absorb", implicit_target_a=1)])
        self.assertAlmostEqual(copy.effects[0].base_potency, 300.0 * 1.2545)
        self.assertEqual(copy.effects[0].base_points, 0)  # generated from potency by to_entry(), not scaled here

    def test_a_flat_absorb_scales(self):
        copy = self._copy([Effect(type=APPLY_AURA, apply_aura=self.SCHOOL_ABSORB, base_points=499,
                                  potency_excluded="test")], 2.0)
        self.assertEqual(copy.effects[0].base_points, 499)  # potency_excluded: a script sizes it, left alone
        copy = self._copy([Effect(type=APPLY_AURA, apply_aura=self.SCHOOL_ABSORB, base_points=499)], 2.0)
        self.assertEqual(copy.effects[0].base_points, 999)

    def test_the_aura_list(self):
        self.assertEqual(sorted(C.STAT_AURAS), [13, 22, 29, 34, 69, 83, 85, 97, 99, 101, 124, 135, 158, 189])


class PotTextRefTest(unittest.TestCase):
    """Wave 1 integration (the Stratholme trap): two spells with equal potency print the same pot_text() expression;
    the registry records which one each text named, so a family no longer swallows the other."""

    def test_equal_potency_spells_stay_apart(self):
        from lib.dsl import registry  # noqa: PLC0415

        reg = registry.Registry()
        old = registry._active
        registry._active = reg
        try:
            def strike(spell_id):
                return registry.spell(id=spell_id, name=f"Strike {spell_id}", school=32, duration_ms=0, effects=[
                    Effect(type=SCHOOL_DAMAGE, sp_potency=100.0, ap_potency=100.0, potency_kind=DIRECT,
                           time_basis_ms=1500, implicit_target_a=6)],
                    raw_overrides=_raw("Deals {pot1}.", DefenseType=1))

            swarm, trample = strike(201), strike(202)
            registry.spell(id=200, name="Signet", effects=[Effect(type=DUMMY)],
                           raw_overrides=_raw("Swarm for " + pot_text(swarm) + "."))
            registry.spell(id=203, name="Spur", effects=[Effect(type=DUMMY)],
                           raw_overrides=_raw("Trample for " + pot_text(trample) + "."))
        finally:
            registry._active = old
        for entry in reg.spells:
            entry["_source_class"] = "items"
        index = C.SpellIndex.build({"spells": reg.spells, "linked_spells": []})
        self.assertEqual(index.family(200), [200, 201])
        self.assertEqual(index.family(203), [202, 203])
        # without the record (a text built outside the registry) the expression alone is ambiguous: both join
        for entry in reg.spells:
            entry.pop("_pot_text_refs", None)
        self.assertEqual(index.family(203), [201, 202, 203])


class RealSourceTest(unittest.TestCase):
    """The VanCleef hard mode items as declared, on stand-in tiers of their real ladder."""

    @classmethod
    def setUpClass(cls):
        from lib import test_hard_mode_item_effects as hm  # noqa: PLC0415

        reg = hm._load_items_registry()
        cls.dsl = {key: list(getattr(reg, key)) for key in ("spells", "spell_bonus_data", "potency_corrections",
                                                            "spell_procs", "spell_script_names", "custom_attrs",
                                                            "linked_spells")}
        for entry in cls.dsl["spells"]:
            entry["_source_class"] = "items"
        decls = {e["id"]: e["_decl"] for e in reg.item_declarations}
        cls.items = [resolved_item(decls[key], slot, 74000 + 10 * n) for n, (key, slot) in enumerate((
            ("dm_powder_keg_fuse", TRINKET), ("dm_blackguards_signet", RING),
            ("dm_lantern_of_the_roaring_flame", TRINKET)))]
        cls.out = C.expand(expansion(*cls.items), cls.dsl, hm.id_blocks.IDS, lock=C.Lock(), taken_loader=tuple)

    def test_twenty_one_copies_from_205410(self):
        self.assertFalse(self.out.errors, self.out.errors)
        self.assertEqual(self.out.copy_ids, list(range(205410, 205431)))
        families = {t.key: sorted(t.remap) for t in self.out.tiers}
        self.assertEqual(families, {"dm_powder_keg_fuse": [205400, 205401, 205402],
                                    "dm_blackguards_signet": [205403, 205404],
                                    "dm_lantern_of_the_roaring_flame": [205406, 205407]})
        self.assertEqual(sorted({t.ratio for t in self.out.tiers}), [1.0545, 1.1091, 1.2545])

    def test_the_committed_header_holds_these_copies(self):
        # The committed header is rendered from every source/items file (other dungeons add rows of their own), so
        # each Deadmines row must be in it, as rendered here.
        committed = C.HEADER_PATH.read_text(encoding="utf-8")
        rows = [line for line in self.out.header_text.splitlines() if line.strip().startswith("{ 2054")]
        self.assertEqual(len(rows), 21)
        for row in rows:
            self.assertIn(row, committed)

    def test_copies_keep_the_tooltip_rules(self):
        for entry in self.out.spells:
            raw = entry["raw_overrides"]
            self.assertNotIn("{pot", raw["Description_Lang_enUS"], entry["id"])
            self.assertNotRegex(raw["Description_Lang_enUS"], r"\$20540\d[a-z]", entry["id"])
            self.assertNotRegex(raw.get("AuraDescription_Lang_enUS", ""), r"\$", entry["id"])
            self.assertEqual(raw["EquippedItemClass"], -1)
        zone = by_id(self.out)[self.out.tiers[-1].remap[205407]]
        self.assertEqual((zone["effect1"]["base_points"], zone["effect1"]["radius_yards"], zone["duration_ms"]),
                         (-11, 8.0, 10000))
        keg_tier = next(t for t in self.out.tiers if t.key == "dm_powder_keg_fuse")
        text = by_id(self.out)[keg_tier.remap[205400]]["raw_overrides"]["Description_Lang_enUS"]
        self.assertIn(f"${keg_tier.remap[205401]}d", text)
        self.assertIn(f"${keg_tier.remap[205402]}a1", text)


if __name__ == "__main__":
    unittest.main()
