"""
Stratholme build WP-S13, Ramstein the Gorger: source/npcs/stratholme/ramstein_the_gorger.py against its C++
(modules/mod-dungeon-bosses src/Stratholme/RamsteinLogic.h, boss_ramstein_the_gorger_rework.cpp). R-1-B B-6 (the
Scholomance Krastinov precedent).

Checks:
  - the spells sit in Ramstein's slice (206685-206704) and RamsteinLogic.h names the same ids;
  - the Half-Digested Corpse 300586 (3,000 health, its heroic 310191, npc_st_half_digested_corpse) and the gut puddle
    stalker 300587 (an invisible trigger, no heroic template), both in the `stratholme` creature reservation;
  - the meat 11030's columns: npc_st_meat, SmartAI off, level 57, 4,000 health;
  - Gorged holds the heroic cap, +15% size and +10% damage a stack; Exposed +50% for the normal length;
  - the puddle and the stomp are resolve copies (the stomp with its hit flash), the meal a heal from the script;
  - 10439 and the three helpers are bound and registered.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_stratholme_ramstein.py
"""

from __future__ import annotations

import math
import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import test_id_blocks as id_blocks  # noqa: E402
from lib.dsl import registry  # noqa: E402

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Stratholme"
HEADER = MODULE_DIR / "RamsteinLogic.h"
REWORK = MODULE_DIR / "StratholmeRework.h"
SCRIPT = MODULE_DIR / "boss_ramstein_the_gorger_rework.cpp"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "stratholme"

SLICE = range(206685, 206705)
(GORGE_LOOK, GORGE_HEAL, GORGED, SEAMS_LOOK, EXPOSED, GUT_PUDDLE, GUT_PUDDLE_LOOK, TRAMPLE_HIT, TRAMPLE_LOOK,
 TRAMPLE_TANK, KNOCKOUT) = range(206685, 206696)
CORPSE = 300586
CORPSE_HEROIC = 310191
PUDDLE_STALKER = 300587
RAMSTEIN = 10439
MEAT = 11030

SCHOOL_DAMAGE, APPLY_AURA, HEAL = 2, 6, 10
AURA_MOD_DAMAGE_PERCENT_DONE, AURA_MOD_DAMAGE_PERCENT_TAKEN, AURA_MOD_SCALE = 79, 87, 61
UNIT_FLAG_NOT_SELECTABLE = 0x02000000
CREATURE_FLAG_EXTRA_TRIGGER = 0x80
RESOLVE = "spell_boss_mechanics_resolve"
WARRIOR_60_BASE = 3052      # creature_classlevelstats level 60 class 1 basehp0
WARRIOR_57_BASE = 2784      # level 57


def _load():
    t = id_blocks
    return registry.load_class_package(
        PACKAGE, ids_cfg=t.IDS, trainer_index=t._AnyTrainer(), existing_group_ids=t._AnySet(),
        shapeshift_index={}, existing_creature_rows=t._AnyRows(),
        creature_columns=t.spell_tables.CREATURE_TEMPLATE_COLUMNS,
        creature_defaults=t.spell_tables.CREATURE_TEMPLATE_DEFAULTS,
        live_data=t.spell_tables.dsl_live_data(
            {}, t.spell_tables.load_live_item_template_rows,
            lambda: t.state.load_existing_rows(t.dbcfmt.SKILLLINEABILITY),
            lambda: t.state.load_stock_rows(t.dbcfmt.CHRCLASSES),
            lambda: t.state.load_stock_rows(t.dbcfmt.SKILLLINEABILITY),
        ),
    )


def _raw(spell: dict, column: str) -> int:
    return int((spell.get("raw_overrides") or {}).get(column, 0) or 0)


def _header() -> str:
    return HEADER.read_text(encoding="utf-8")


def _header_nh(name: str) -> tuple[float, float]:
    match = re.search(rf"{name}\{{\s*(-?[\d.]+)f?,\s*(-?[\d.]+)f?\s*\}}", _header())
    assert match, name
    return float(match.group(1)), float(match.group(2))


class RamsteinDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates
                         if int(e["entry"]) in (CORPSE, PUDDLE_STALKER)}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) in (RAMSTEIN, MEAT)}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(GORGE_LOOK, KNOCKOUT + 1)))
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"spell": mine}), [])
        first = re.search(r"kSpellsRamstein\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(first)
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_RG_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))

    def test_the_corpse_and_the_puddle_stalker(self):
        self.assertEqual(sorted(self.creatures), [CORPSE, PUDDLE_STALKER])
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"creature": [CORPSE, PUDDLE_STALKER]}), [])
        corpse = self.creatures[CORPSE]
        self.assertEqual(corpse["ScriptName"], "npc_st_half_digested_corpse")
        self.assertEqual(corpse["difficulty_entry_1"], CORPSE_HEROIC)
        self.assertEqual(math.ceil(WARRIOR_60_BASE * corpse["HealthModifier"]), 3000)
        self.assertEqual(corpse["lootid"], 0)
        stalker = self.creatures[PUDDLE_STALKER]
        self.assertEqual(stalker["ScriptName"], "npc_st_gut_puddle")
        self.assertTrue(stalker["unit_flags"] & UNIT_FLAG_NOT_SELECTABLE)
        self.assertTrue(stalker["flags_extra"] & CREATURE_FLAG_EXTRA_TRIGGER)
        self.assertEqual(stalker.get("difficulty_entry_1", 0), 0)
        self.assertIn("NPC_ST_HALF_DIGESTED_CORPSE", self.cpp)

    def test_the_meat_columns(self):
        meat = self.edits[MEAT]
        self.assertEqual(meat["ScriptName"], "npc_st_meat")
        self.assertEqual(meat["AIName"], "")
        self.assertEqual((meat["minlevel"], meat["maxlevel"]), (57, 57))
        self.assertEqual(math.ceil(WARRIOR_57_BASE * meat["HealthModifier"]), 4000)

    def test_gorged_and_exposed(self):
        gorged = self.spells[GORGED]
        _, heroic_cap = _header_nh("kGorgedMaxStacks")
        self.assertGreaterEqual(_raw(gorged, "CumulativeAura"), int(heroic_cap))
        self.assertEqual(gorged["duration_ms"], -1)
        self.assertEqual(gorged["effect1"]["apply_aura"], AURA_MOD_SCALE)
        self.assertEqual(gorged["effect1"]["base_points"], 15)
        self.assertEqual(gorged["effect2"]["apply_aura"], AURA_MOD_DAMAGE_PERCENT_DONE)
        self.assertEqual(gorged["effect2"]["base_points"], 10)
        exposed = self.spells[EXPOSED]
        normal, _ = _header_nh("kExposedMs")
        self.assertEqual(exposed["duration_ms"], int(normal))
        self.assertEqual(exposed["effect1"]["apply_aura"], AURA_MOD_DAMAGE_PERCENT_TAKEN)
        self.assertEqual(exposed["effect1"]["base_points"], 50)

    def test_hits_and_heals(self):
        for spell_id in (GUT_PUDDLE, TRAMPLE_HIT):
            self.assertEqual(self.spells[spell_id]["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
        self.assertEqual(_raw(self.spells[TRAMPLE_HIT], "SpellVisualID_1"), 39)
        self.assertEqual(self.spells[GORGE_HEAL]["effect1"]["type"], HEAL)
        self.assertEqual({name for _, name in self.scripts}, {RESOLVE})

    def test_ramstein_and_his_helpers_are_bound(self):
        self.assertEqual(self.edits[RAMSTEIN]["ScriptName"], "boss_ramstein_the_gorger_rework")
        for name in ("boss_ramstein_the_gorger_rework", "npc_st_meat", "npc_st_gut_puddle",
                     "npc_st_half_digested_corpse"):
            self.assertIn(f"RegisterDungeonReworkCreatureAI({name},", self.cpp)


if __name__ == "__main__":
    unittest.main()
