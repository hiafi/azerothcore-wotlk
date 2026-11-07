"""
The Shadowfang Keep items (item variants, wave 1): source/items/shadowfang_keep.py (the 24 list items and the 3 Archmage
Arugal hard mode items), source/items/shadowfang_keep_hard_mode_effects.py (their effects and the Meteor Shard's
Firebolt), the creature in source/npcs/shadowfang_keep/hard_mode_items.py and the scripts in modules/mod-dungeon-bosses
(src/ShadowfangKeep/sfk_hard_mode_items.cpp, SfkHardModeItemsLogic.h).

Checks:
  - the spells sit in the `shadowfang_items` reservation, the creature in its creature slice (300460-300464);
  - the C++ header names the same ids, and every scripted_by() name is a script sfk_hard_mode_items.cpp registers;
  - the list: 24 items on the vanilla dungeon ladder and 3 on the hard mode ladder, rings and necks without a primary,
    sockets per the loot rules (trinkets none, hard mode items at most 1, a list item at most 2);
  - each effect item carries its spell with the right trigger, scaled per tier where it deals damage;
  - the damage comes from potency only, every tooltip placeholder is expanded, aura texts are number-free and the item
    spells pass the triggered-cast rules (EquippedItemClass -1, a damage spell is never DmgClass NONE);
  - the Vial's and the Locket's data, and the Tome's proc row.

Only this dungeon's ids are looked at: the other wave 1 dungeons declare in the same package.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_shadowfang_keep_hard_mode_items.py
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import test_id_blocks as id_blocks  # noqa: E402
from lib.dsl.items import SpellTrigger  # noqa: E402
from lib.test_hard_mode_item_effects import _load_items_registry  # noqa: E402

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "ShadowfangKeep"
HEADER = MODULE_DIR / "SfkHardModeItemsLogic.h"
SCRIPT = MODULE_DIR / "sfk_hard_mode_items.cpp"

VIAL, TOME, VOIDWALKER, LOCKET, FIREBOLT = range(205600, 205605)
NORMAL_RATIO = 0.2423  # Meteor Shard Normal stat budget / Heroic (the copy 205485 note in the generated rev)
MINE = range(205600, 205620)
TOME_VOIDWALKER = 300460

SCHOOL_DAMAGE = 2
DISPEL = 38
APPLY_AURA = 6
AURA_PERIODIC_DAMAGE = 3
AURA_MOD_INCREASE_SPEED = 31
AURA_DISPEL_IMMUNITY = 41
AURA_MOD_RATING = 189
DISPEL_CURSE = 2
HASTE_RATING_MASK = (1 << 17) | (1 << 18) | (1 << 19)
TARGET_UNIT_TARGET_ALLY = 21
INV_TRINKET, INV_NECK, INV_FINGER = 12, 2, 11

LIST_ITEMS = 24
HARD_MODE_ITEMS = ("sfk_vial_of_the_worgens_curse", "sfk_arugals_shadow_tome", "sfk_ashcrombes_locket")


class ShadowfangKeepItemsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load_items_registry()
        cls.spells = {int(e["id"]): e for e in cls.reg.spells if int(e["id"]) in MINE}
        cls.decls = {e["id"]: e["_decl"] for e in cls.reg.item_declarations if e["id"].startswith("sfk_")}
        cls.npc_ids = id_blocks.declared_ids(TOOL_ROOT / "source" / "npcs" / "shadowfang_keep")

    def test_ids_sit_in_their_reservations(self):
        self.assertEqual(sorted(self.spells), list(range(VIAL, FIREBOLT + 1)))
        self.assertEqual(id_blocks.out_of_reservation("shadowfang_items", {"spell": sorted(self.spells)}), [])
        self.assertEqual(sorted(set(self.npc_ids["creature"])), [TOME_VOIDWALKER])
        self.assertEqual(id_blocks.out_of_reservation("shadowfang_items", {"creature": [TOME_VOIDWALKER]}), [])

    def test_the_cpp_header_names_the_same_ids(self):
        text = HEADER.read_text()
        named = {name: int(value) for name, value in re.findall(r"\b((?:SPELL|NPC)_[A-Z_]+)\s*=\s*(\d+)", text)}
        self.assertEqual(named, {
            "SPELL_VIAL_OF_THE_WORGENS_CURSE": VIAL, "SPELL_ARUGALS_SHADOW_TOME": TOME,
            "SPELL_ARUGALS_VOIDWALKER": VOIDWALKER, "SPELL_ASHCROMBES_LOCKET": LOCKET,
            "SPELL_METEOR_SHARD_FIREBOLT": FIREBOLT, "NPC_TOME_VOIDWALKER": TOME_VOIDWALKER,
        })

    def test_every_binding_is_a_registered_script(self):
        registered = set(re.findall(r"RegisterSpellScript\((\w+)\)", SCRIPT.read_text()))
        bound = {(int(r["spell_id"]), r["ScriptName"]) for r in self.reg.spell_script_names
                 if int(r["spell_id"]) in MINE}
        self.assertEqual(bound, {(TOME, "spell_sfk_arugals_shadow_tome"),
                                 (VOIDWALKER, "spell_sfk_arugals_voidwalker")})
        self.assertEqual({name for _, name in bound}, registered)

    def test_the_list(self):
        self.assertEqual(len(self.decls), LIST_ITEMS + len(HARD_MODE_ITEMS))
        ladders = {key: decl.ladder.name for key, decl in self.decls.items()}
        self.assertEqual({k for k, v in ladders.items() if v == "vanilla_hard_mode"}, set(HARD_MODE_ITEMS))
        self.assertEqual(sum(1 for v in ladders.values() if v == "vanilla_dungeon"), LIST_ITEMS)
        # 19 stock items (2 kept) and 5 new ones on the list
        listed = [d for d in self.decls.values() if d.ladder.name == "vanilla_dungeon"]
        self.assertEqual(sum(1 for d in listed if d.base is not None), 19)
        self.assertEqual(sum(1 for d in listed if d.itemization == "live"), 2)
        # rings and necks carry secondaries only
        for key in ("sfk_silverlaines_family_seal", "sfk_ashcrombes_locket", "sfk_vial_of_the_worgens_curse"):
            self.assertIsNone(self.decls[key].primary, key)
            self.assertEqual(self.decls[key].primary_share, 0, key)
        # the Bloody Apron turns leather
        self.assertEqual(dict(self.decls["sfk_bloody_apron"].columns)["subclass"], 2)

    def test_sockets(self):
        socketed = {key: decl.sockets for key, decl in self.decls.items() if decl.sockets}
        self.assertNotIn("sfk_vial_of_the_worgens_curse", socketed)  # trinkets never
        for key in HARD_MODE_ITEMS:
            self.assertLessEqual(len(self.decls[key].sockets or ()), 1, key)
        for key, sockets in socketed.items():
            self.assertLessEqual(len(sockets), 2, key)
            self.assertIsNotNone(self.decls[key].socket_bonus, key)
        # one socketed standalone piece or weapon per boss (9 bosses), plus two hard mode items
        self.assertEqual(len(socketed), 9 + 2)

    def test_items_carry_their_spell(self):
        expected = {
            "sfk_vial_of_the_worgens_curse": (VIAL, SpellTrigger.USE, "budget"),
            "sfk_arugals_shadow_tome": (TOME, SpellTrigger.ON_EQUIP, "budget"),
            "sfk_ashcrombes_locket": (LOCKET, SpellTrigger.USE, None),  # no number to scale
            "sfk_meteor_shard": (FIREBOLT, SpellTrigger.CHANCE_ON_HIT, "budget"),  # declared at Heroic (66)
        }
        for key, (spell_id, trigger, scale) in expected.items():
            decl = self.decls[key]
            self.assertEqual(len(decl.spells), 1, key)
            spell = decl.spells[0]
            self.assertEqual((spell.spell_id, spell.trigger, spell.scale), (spell_id, trigger, scale), key)
            self.assertEqual(spell.cooldown, -1, key)  # the spell's own cooldown
        self.assertEqual(self.decls["sfk_meteor_shard"].spells[0].ppm, 2.0)  # the stock rate
        for key in ("sfk_vial_of_the_worgens_curse", "sfk_ashcrombes_locket"):
            self.assertEqual(self.decls[key].budget_mult, 0.7, key)
        # weapon-tier slots take their role cell's median (times 0.7 for an effect), never a hand multiplier
        for key in ("sfk_arugals_shadow_tome", "sfk_meteor_shard"):
            self.assertIsNone(self.decls[key].budget_mult, key)
        # plain stat items carry no spell (the Haunting Blade's stock +AP folds into the budget)
        for key, decl in self.decls.items():
            if key not in expected:
                self.assertIsNone(decl.spells, key)
                self.assertFalse(decl.keep_spells, key)

    def test_meteor_shard_normal_is_a_slightly_weaker_stock_firebolt(self):
        # User 2026-11-07 (plan s13, then "a slightly weaker Normal"): the Normal tier (level 29 Rare, budget ratio
        # 0.2423 to the Heroic reference) hits for about 28 at level 25 (80% of the stock Firebolt 13442's 35), base
        # line before attack power.
        from lib import potency  # noqa: PLC0415

        declared = self.spells[FIREBOLT]["effect1"]["_potency"]["total_potency"]
        self.assertEqual(declared, 200.0)
        normal_average = declared * NORMAL_RATIO * potency.c_of_level(25)
        self.assertAlmostEqual(normal_average, 28, delta=1)

    def test_damage_comes_from_potency_only(self):
        for spell_id, kind in ((VOIDWALKER, "periodic"), (FIREBOLT, "direct")):
            effect = self.spells[spell_id]["effect1"]
            self.assertTrue(effect.get("_potency"), spell_id)
            self.assertEqual(effect["_potency"]["kind"], kind, spell_id)
            self.assertNotEqual(int(self.spells[spell_id]["raw_overrides"]["DefenseType"]), 0, spell_id)
        self.assertEqual(self.spells[VOIDWALKER]["effect1"]["apply_aura"], AURA_PERIODIC_DAMAGE)
        self.assertEqual(self.spells[FIREBOLT]["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertGreater(self.spells[VOIDWALKER]["effect1"]["_potency"]["sp_coefficient"], 0)  # a caster item
        self.assertGreater(self.spells[FIREBOLT]["effect1"]["_potency"]["ap_coefficient"], 0)  # an Agility dagger
        bonus = {int(r["entry"]) for r in self.reg.spell_bonus_data if int(r["entry"]) in MINE}
        self.assertEqual(bonus, {FIREBOLT})  # the generated attack power row, nothing by hand
        self.assertEqual({int(r["spell_id"]) for r in self.reg.potency_corrections if int(r["spell_id"]) in MINE},
                         {VOIDWALKER, FIREBOLT})
        # nothing else deals damage
        for spell_id in (VIAL, TOME, LOCKET):
            for n in (1, 2, 3):
                effect = self.spells[spell_id].get(f"effect{n}") or {}
                self.assertNotEqual(effect.get("type"), SCHOOL_DAMAGE, spell_id)
                self.assertNotEqual(effect.get("apply_aura"), AURA_PERIODIC_DAMAGE, spell_id)

    def test_tooltips(self):
        for spell_id, spell in self.spells.items():
            raw = spell["raw_overrides"]
            self.assertEqual(raw["EquippedItemClass"], -1, spell_id)
            self.assertNotIn("{pot", raw["Description_Lang_enUS"], spell_id)
            self.assertNotRegex(raw.get("AuraDescription_Lang_enUS", ""), r"\$", spell_id)  # aura texts number-free
        self.assertIn("$SP", self.spells[TOME]["raw_overrides"]["Description_Lang_enUS"])
        self.assertIn("$205602d", self.spells[TOME]["raw_overrides"]["Description_Lang_enUS"])
        self.assertIn("$AP", self.spells[FIREBOLT]["raw_overrides"]["Description_Lang_enUS"])
        self.assertIn("Worgen's Curse", self.spells[LOCKET]["raw_overrides"]["Description_Lang_enUS"])

    def test_the_vial(self):
        vial = self.spells[VIAL]
        rating, speed = vial["effect1"], vial["effect2"]
        self.assertEqual((rating["type"], rating["apply_aura"], rating["misc_value"]),
                         (APPLY_AURA, AURA_MOD_RATING, HASTE_RATING_MASK))
        self.assertGreater(rating["base_points"], 0)
        self.assertEqual((speed["apply_aura"], speed["base_points"] + speed["die_sides"]),
                         (AURA_MOD_INCREASE_SPEED, 30))
        self.assertEqual((vial["duration_ms"], vial["cooldown_ms"]), (15000, 120000))
        self.assertEqual(vial["raw_overrides"]["StartRecoveryCategory"], 0)  # off the GCD

    def test_the_locket(self):
        locket = self.spells[LOCKET]
        dispel, ward = locket["effect1"], locket["effect2"]
        self.assertEqual((dispel["type"], dispel["misc_value"], dispel["implicit_target_a"]),
                         (DISPEL, DISPEL_CURSE, TARGET_UNIT_TARGET_ALLY))
        self.assertGreater(dispel["base_points"] + dispel["die_sides"], 1)  # "all" Curses, not one
        self.assertEqual((ward["apply_aura"], ward["misc_value"], ward["implicit_target_a"]),
                         (AURA_DISPEL_IMMUNITY, DISPEL_CURSE, TARGET_UNIT_TARGET_ALLY))
        self.assertEqual(int(locket["raw_overrides"]["AttributesEx"]) & 0x00008000, 0x00008000)  # purges leftovers
        self.assertEqual((locket["duration_ms"], locket["cooldown_ms"], locket["range_yards"]), (6000, 120000, 40.0))

    def test_the_voidwalker(self):
        attack = self.spells[VOIDWALKER]
        self.assertEqual(attack["duration_ms"], 10000)  # "for 10 sec"
        self.assertEqual(attack["effect1"]["amplitude"], 2000)
        self.assertEqual(int(attack["dispel"]), 0)

    def test_proc_row(self):
        procs = {int(r["SpellId"]): r for r in self.reg.spell_procs if int(r["SpellId"]) in MINE}
        self.assertEqual(set(procs), {TOME})
        tome = procs[TOME]
        self.assertEqual(tome["ProcFlags"], 0x00010000)  # done harmful magic-class spells
        self.assertEqual(tome["ProcFlags"] & 0x00040000, 0)  # no periodic ticks
        self.assertEqual((tome["SpellTypeMask"], tome["SpellPhaseMask"], tome["HitMask"]), (0x1, 0x2, 0x3))
        self.assertTrue(0 < tome["Chance"] < 100)
        # one Voidwalker at a time: the internal cooldown outlasts it
        self.assertGreaterEqual(tome["Cooldown"], self.spells[VOIDWALKER]["duration_ms"])

    def test_hard_mode_item_names(self):
        names = {key: self.decls[key].name for key in HARD_MODE_ITEMS}
        self.assertEqual(names, {
            "sfk_vial_of_the_worgens_curse": "Vial of the Worgen's Curse",
            "sfk_arugals_shadow_tome": "Arugal's Shadow Tome",
            "sfk_ashcrombes_locket": "Ashcrombe's Locket",
        })


if __name__ == "__main__":
    unittest.main()
