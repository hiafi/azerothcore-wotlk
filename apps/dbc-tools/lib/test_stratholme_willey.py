"""
Stratholme build WP-S5, Cannon Master Willey: source/npcs/stratholme/cannon_master_willey.py against its C++
(modules/mod-dungeon-bosses src/Stratholme/WilleyLogic.h, boss_cannon_master_willey_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in Willey's slice (206500-206519) and WilleyLogic.h names the same ids;
  - Willey 10997 and the rifleman 11054 are bound (SmartAI off), the rifleman at 5,000 health;
  - the volley carries the header's 15% / 20% in hundredths through the kit's refflat script, not avoidable;
  - Holding Cannonball slows by 30% for the header's 30 s; Shaken stacks to the header's cap, +10% a stack;
  - the lane and the Barrage are resolve copies; the auras the players carry drop on a map change;
  - the SQL rev drops the stock SmartAI, writes the eight texts and the three gameobjects, and moves the stock cannons'
    spawns onto Mercy and Zeal.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_stratholme_willey.py
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
HEADER = MODULE_DIR / "WilleyLogic.h"
REWORK = MODULE_DIR / "StratholmeRework.h"
SCRIPT = MODULE_DIR / "boss_cannon_master_willey_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_cannon_master_willey_stratholme.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "stratholme"

SLICE = range(206500, 206520)
(AIM, TAKING_AIM, FIRE, HOLDING, SHOT, SHAKEN, CANNON_FIRE, BARRAGE, BLAST_LOOK, MERCY_GLOW,
 ZEAL_GLOW) = range(206500, 206511)
GLOW = 300610
GLOW_VISUALS = {MERCY_GLOW: 14914, ZEAL_GLOW: 15672}     # _visuals.py WI_MERCY_GLOW / WI_ZEAL_GLOW
UNIT_FLAG_NOT_SELECTABLE = 0x02000000
CREATURE_FLAG_EXTRA_TRIGGER = 0x80
WILLEY = 10997
RIFLEMAN = 11054

SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT = 2, 6, 3
AURA_MOD_DECREASE_SPEED, AURA_MOD_DAMAGE_PERCENT_TAKEN = 33, 87
AURA_INTERRUPT_CHANGE_MAP = 0x00080000
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
ATTR3_ALWAYS_HIT = 0x00040000
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT = "spell_dungeon_refflat_damage"
WARRIOR_60_BASE = 3052      # creature_classlevelstats level 60 class 1 basehp0


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


def _header_value(name: str) -> float:
    match = re.search(rf"{name}\s*=\s*(-?[\d.]+)f?;", _header())
    assert match, name
    return float(match.group(1))


class WilleyDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) in (WILLEY, RIFLEMAN)}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == GLOW}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(AIM, ZEAL_GLOW + 1)))
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"spell": mine}), [])
        first = re.search(r"kSpellsWilley\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(first)
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_WY_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))

    def test_willey_and_the_riflemen_are_bound(self):
        willey = self.edits[WILLEY]
        self.assertEqual(willey["ScriptName"], "boss_cannon_master_willey_rework")
        self.assertEqual(willey["AIName"], "")
        self.assertEqual(math.ceil(WARRIOR_60_BASE * willey["HealthModifier"]), 185001)
        # Stock 3.5, not the live 7 the retired mod-progression left (F-2 ruling, the rest of wave 2's precedent).
        self.assertAlmostEqual(float(willey["DamageModifier"]), 3.5)
        rifleman = self.edits[RIFLEMAN]
        self.assertEqual(rifleman["ScriptName"], "npc_st_crimson_rifleman")
        self.assertEqual(rifleman["AIName"], "")
        normal, _ = _header_nh("kRiflemanHealth")
        self.assertEqual(math.ceil(WARRIOR_60_BASE * rifleman["HealthModifier"]), int(normal))
        for name in ("boss_cannon_master_willey_rework", "npc_st_crimson_rifleman"):
            self.assertIn(f"RegisterDungeonReworkCreatureAI({name},", self.cpp)

    def test_the_volley(self):
        fire = self.spells[FIRE]
        normal, heroic = _header_nh("kVolleyPct")
        effect = fire["effect1"]
        self.assertEqual(effect["type"], SCHOOL_DAMAGE)
        self.assertEqual(effect["base_points"] + effect["die_sides"], int(normal * 100))
        self.assertEqual(_raw(fire, "EffectMiscValueB_1"), int(heroic * 100))
        self.assertIn((FIRE, REFFLAT), self.scripts)
        self.assertEqual(_raw(fire, "DefenseType"), 0)
        self.assertTrue(_raw(fire, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertTrue(_raw(fire, "AttributesEx3") & ATTR3_ALWAYS_HIT)

    def test_carrying_and_shaken(self):
        holding = self.spells[HOLDING]
        self.assertEqual(holding["duration_ms"], int(_header_value("kHoldingMs")))
        self.assertEqual(holding["effect1"]["apply_aura"], AURA_MOD_DECREASE_SPEED)
        self.assertEqual(holding["effect1"]["base_points"] + holding["effect1"]["die_sides"], -30)
        shaken = self.spells[SHAKEN]
        self.assertEqual(_raw(shaken, "CumulativeAura"), int(_header_value("kShakenMaxStacks")))
        self.assertEqual(shaken["effect1"]["apply_aura"], AURA_MOD_DAMAGE_PERCENT_TAKEN)
        self.assertEqual(shaken["effect1"]["base_points"], int(_header_value("kShakenPctPerStack")))
        self.assertEqual(shaken["duration_ms"], 15000)
        shot = self.spells[SHOT]
        self.assertEqual(shot["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertTrue(_raw(shot, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        for spell_id in (AIM, HOLDING):
            self.assertEqual(_raw(self.spells[spell_id], "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP, spell_id)

    def test_lanes_are_resolve_copies(self):
        for spell_id in (CANNON_FIRE, BARRAGE):
            self.assertEqual(self.spells[spell_id]["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
            self.assertNotEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), 0, spell_id)
        self.assertEqual(self.spells[BLAST_LOOK]["effect1"]["type"], DUMMY_EFFECT)
        self.assertEqual({name for _, name in self.scripts}, {RESOLVE, REFFLAT})
        self.assertIn(".NoTelegraph()", self.cpp)

    def test_the_glow_stalker_and_rings(self):
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"creature": [GLOW]}), [])
        glow = self.creatures[GLOW]
        self.assertEqual(glow["ScriptName"], "npc_st_willey_glow")
        self.assertTrue(glow["unit_flags"] & UNIT_FLAG_NOT_SELECTABLE)
        self.assertTrue(glow["flags_extra"] & CREATURE_FLAG_EXTRA_TRIGGER)
        self.assertEqual(glow.get("difficulty_entry_1", 0), 0)
        self.assertRegex(_header(), rf"kNpcGunGlow = {GLOW};")
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_st_willey_glow,", self.cpp)
        for spell_id, visual in GLOW_VISUALS.items():
            ring = self.spells[spell_id]
            self.assertEqual(ring["duration_ms"], -1, spell_id)
            self.assertEqual(ring["effect1"]["apply_aura"], 4, spell_id)    # SPELL_AURA_DUMMY
            self.assertEqual(_raw(ring, "SpellVisualID_1"), visual, spell_id)

    def test_the_sql_rev(self):
        sql = SQL.read_text(encoding="utf-8")
        for entry in (WILLEY, RIFLEMAN):
            self.assertIn(f"DELETE FROM `smart_scripts` WHERE `entryorguid` = {entry} AND `source_type` = 0;", sql)
        for group in range(8):
            self.assertRegex(sql, rf"\({WILLEY}, {group}, 0, ")
        for entry in (301200, 301201, 301202):
            self.assertRegex(sql, rf"\({entry}, \d+, \d+, '")
        self.assertIn("SET `id` = 301200 WHERE `id` = 176216 AND `guid` = 20761", sql)
        self.assertIn("SET `id` = 301201 WHERE `id` = 176217 AND `guid` = 20768", sql)
        self.assertIn("`id` = 176215 AND `guid` IN (20756, 20757, 20758, 20759, 20760)", sql)


if __name__ == "__main__":
    unittest.main()
