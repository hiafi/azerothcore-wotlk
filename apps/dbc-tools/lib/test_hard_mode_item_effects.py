"""
The Edwin VanCleef hard mode item effects (item variants plan section 7.2, stage IV6):
source/items/deadmines_hard_mode_effects.py, the creature in source/npcs/deadmines/hard_mode_items.py and the scripts in
modules/mod-dungeon-bosses (hard_mode_items.cpp, HardModeItemsLogic.h).

Checks:
  - the spells sit in the `items` reservation and the creature in the `deadmines` one;
  - the C++ header names the same ids, and every scripted_by() name is a script hard_mode_items.cpp registers;
  - each hard mode item carries its spell with the right trigger (Use / Equip), on every tier;
  - the damage comes from potency only (no hand base points, the only spell_bonus_data rows are the generated ones),
    every tooltip placeholder is expanded, and the item spells pass the triggered-cast rules (EquippedItemClass -1,
    a damage spell is never DmgClass NONE);
  - the proc rows (Signet: landed melee hits with an internal cooldown; Lantern: one charge on a heal).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_hard_mode_item_effects.py
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
from lib.dsl import registry  # noqa: E402
from lib.dsl.items import SpellTrigger  # noqa: E402

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Deadmines"
HEADER = MODULE_DIR / "HardModeItemsLogic.h"
SCRIPT = MODULE_DIR / "hard_mode_items.cpp"

KEG, KEG_LOOK, KEG_BLAST, SIGNET, STRIKE, AMBUSH, LANTERN, ZONE = range(205400, 205408)
BLACKGUARD = 300430

SCHOOL_DAMAGE = 2
PERSISTENT_AREA_AURA = 27


def _load_items_registry():
    """source/items as generate.py loads it (the same live-data stand-ins as test_id_blocks.declared_ids)."""
    t = id_blocks
    return registry.load_class_package(
        TOOL_ROOT / "source" / "items", ids_cfg=t.IDS, trainer_index=t._AnyTrainer(), existing_group_ids=t._AnySet(),
        shapeshift_index={}, existing_creature_rows=t._AnyRows(),
        creature_columns=t.spell_tables.CREATURE_TEMPLATE_COLUMNS,
        creature_defaults=t.spell_tables.CREATURE_TEMPLATE_DEFAULTS,
        live_data=t.spell_tables.dsl_live_data(
            t.state.load_stock_rows(t.dbcfmt.TALENT) if (t.state.BASE_DBC_DIR / t.dbcfmt.TALENT.dbc_filename).is_file()
            else {},
            t.spell_tables.load_live_item_template_rows,
            lambda: t.state.load_existing_rows(t.dbcfmt.SKILLLINEABILITY),
            lambda: t.state.load_stock_rows(t.dbcfmt.CHRCLASSES),
            lambda: t.state.load_stock_rows(t.dbcfmt.SKILLLINEABILITY),
        ),
    )


class HardModeItemEffectsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load_items_registry()
        cls.spells = {int(e["id"]): e for e in cls.reg.spells}
        cls.decls = {e["id"]: e["_decl"] for e in cls.reg.item_declarations}
        cls.deadmines_ids = id_blocks.declared_ids(TOOL_ROOT / "source" / "npcs" / "deadmines")

    def test_ids_sit_in_their_reservations(self):
        self.assertEqual(sorted(self.spells), list(range(KEG, ZONE + 1)))
        self.assertEqual(id_blocks.out_of_reservation("items", id_blocks.declared_ids(TOOL_ROOT / "source" / "items")),
                         [])
        self.assertIn(BLACKGUARD, self.deadmines_ids["creature"])
        self.assertEqual(id_blocks.out_of_reservation("deadmines", self.deadmines_ids), [])

    def test_the_cpp_header_names_the_same_ids(self):
        text = HEADER.read_text()
        named = {name: int(value) for name, value in re.findall(r"\b((?:SPELL|NPC)_[A-Z_]+)\s*=\s*(\d+)", text)}
        self.assertEqual(named, {
            "SPELL_POWDER_KEG_FUSE": KEG, "SPELL_POWDER_KEG_FUSE_LOOK": KEG_LOOK, "SPELL_POWDER_KEG_BLAST": KEG_BLAST,
            "SPELL_BLACKGUARDS_SIGNET": SIGNET, "SPELL_BLACKGUARD_STRIKE": STRIKE,
            "SPELL_BLACKGUARD_AMBUSH_LOOK": AMBUSH, "SPELL_LANTERN_OF_ROARING_FLAME": LANTERN,
            "SPELL_ROARING_FLAME_ZONE": ZONE, "NPC_SIGNET_BLACKGUARD": BLACKGUARD,
        })

    def test_every_binding_is_a_registered_script(self):
        registered = set(re.findall(r"RegisterSpellScript\((\w+)\)", SCRIPT.read_text()))
        bound = {(int(r["spell_id"]), r["ScriptName"]) for r in self.reg.spell_script_names}
        self.assertEqual(bound, {(KEG, "spell_dm_powder_keg_fuse"), (SIGNET, "spell_dm_blackguards_signet"),
                                 (LANTERN, "spell_dm_lantern_of_the_roaring_flame")})
        self.assertEqual({name for _, name in bound}, registered)

    def test_items_carry_their_spell(self):
        expected = {
            "dm_powder_keg_fuse": (KEG, SpellTrigger.USE),
            "dm_blackguards_signet": (SIGNET, SpellTrigger.ON_EQUIP),
            "dm_lantern_of_the_roaring_flame": (LANTERN, SpellTrigger.USE),
        }
        for key, (spell_id, trigger) in expected.items():
            decl = self.decls[key]
            self.assertEqual(len(decl.spells), 1, key)
            self.assertEqual((decl.spells[0].spell_id, decl.spells[0].trigger), (spell_id, trigger), key)
            self.assertEqual(decl.spells[0].cooldown, -1, key)  # the spell's own cooldown
            self.assertEqual(decl.spells[0].scale, "budget", key)  # IV10: per-tier copies above 71
            self.assertEqual(decl.budget_mult, 0.7, key)

    def test_damage_comes_from_potency_only(self):
        for spell_id in (KEG_BLAST, STRIKE):
            effect = self.spells[spell_id]["effect1"]
            self.assertEqual(effect["type"], SCHOOL_DAMAGE)
            self.assertTrue(effect.get("_potency"), spell_id)
            self.assertNotEqual(int(self.spells[spell_id]["raw_overrides"]["DefenseType"]), 0, spell_id)
        self.assertEqual({int(r["entry"]) for r in self.reg.spell_bonus_data}, {KEG_BLAST, STRIKE})
        blast = next(r for r in self.reg.spell_bonus_data if int(r["entry"]) == KEG_BLAST)
        self.assertGreater(blast["direct_bonus"], 0)  # casters and melee both scale off the Crit trinket
        self.assertGreater(blast["ap_bonus"], 0)
        strike = next(r for r in self.reg.spell_bonus_data if int(r["entry"]) == STRIKE)
        self.assertEqual(strike["direct_bonus"], 0)
        self.assertGreater(strike["ap_bonus"], 0)
        self.assertEqual({int(r["spell_id"]) for r in self.reg.potency_corrections}, {KEG_BLAST, STRIKE})

    def test_tooltips(self):
        for spell_id, spell in self.spells.items():
            raw = spell["raw_overrides"]
            self.assertEqual(raw["EquippedItemClass"], -1, spell_id)
            self.assertNotIn("{pot", raw["Description_Lang_enUS"], spell_id)
            self.assertNotRegex(raw.get("AuraDescription_Lang_enUS", ""), r"\$", spell_id)  # aura texts number-free
        self.assertIn("$SP", self.spells[KEG]["raw_overrides"]["Description_Lang_enUS"])
        self.assertIn("$205401d", self.spells[KEG]["raw_overrides"]["Description_Lang_enUS"])
        self.assertIn("$AP", self.spells[SIGNET]["raw_overrides"]["Description_Lang_enUS"])
        self.assertIn("$205407s1%", self.spells[LANTERN]["raw_overrides"]["Description_Lang_enUS"])

    def test_the_zone_and_the_fuse(self):
        zone = self.spells[ZONE]["effect1"]
        self.assertEqual((zone["type"], zone["implicit_target_a"], zone["implicit_target_b"]),
                         (PERSISTENT_AREA_AURA, 87, 29))  # placed by the script, holds allies
        self.assertEqual((zone["base_points"], zone["die_sides"], zone["misc_value"]), (-11, 1, 127))  # -10%, all
        self.assertEqual(self.spells[ZONE]["duration_ms"], 10000)
        self.assertEqual(self.spells[KEG_LOOK]["duration_ms"], 2000)  # the fuse
        self.assertEqual(self.spells[KEG_BLAST]["effect1"]["radius_yards"], 6.0)

    def test_keg_spells_skip_the_caster_line_of_sight_check(self):
        # the wearer casts both at a spot (Spell::CheckCast checks caster-to-dest sight for every spell with a dest,
        # triggered ones too): ALWAYS_AOE_LINE_OF_SIGHT drops that check, while IGNORE_LINE_OF_SIGHT (no blast
        # through walls) stays clear
        for spell_id in (KEG_LOOK, KEG_BLAST):
            raw = self.spells[spell_id]["raw_overrides"]
            self.assertEqual(int(raw["AttributesEx5"]) & 0x04000000, 0x04000000, spell_id)
            self.assertEqual(int(raw.get("AttributesEx2", 0)) & 0x4, 0, spell_id)

    def test_keg_tooltip_names_the_spot(self):
        self.assertIn("where the enemy stood", self.spells[KEG]["raw_overrides"]["Description_Lang_enUS"])

    def test_proc_rows(self):
        procs = {int(r["SpellId"]): r for r in self.reg.spell_procs}
        self.assertEqual(set(procs), {SIGNET, LANTERN})
        signet = procs[SIGNET]
        self.assertEqual(signet["ProcFlags"], 0x4 | 0x10)  # done melee auto attacks and melee-class spells
        self.assertEqual(signet["HitMask"], 0x3)  # landed: normal or critical
        self.assertGreater(signet["Cooldown"], 0)  # the throttle against haste and cleaves
        self.assertTrue(0 < signet["Chance"] < 100)
        lantern = procs[LANTERN]
        self.assertEqual(lantern["SpellTypeMask"], 0x2)  # heals
        self.assertEqual(lantern["SpellPhaseMask"], 0x2)  # hit: a heal over time's cast heals nothing
        self.assertEqual(lantern["ProcFlags"] & 0x00040000, 0)  # no periodic ticks
        self.assertEqual(lantern["Charges"], 1)
        self.assertEqual(lantern["Chance"], 100.0)


if __name__ == "__main__":
    unittest.main()
