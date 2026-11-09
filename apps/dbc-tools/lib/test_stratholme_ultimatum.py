"""
Stratholme build WP-S15, the Ultimatum (Baron Rivendare's hard mode): source/npcs/stratholme/baron_hard_mode.py against
its C++ (modules/mod-dungeon-bosses src/Stratholme/BaronHardModeLogic.h, baron_hard_mode.cpp) and its SQL rev
(data/sql/updates/pending_db_world/rev_baron_hard_mode_stratholme.sql).

Checks:
  - the spells fill the Ultimatum's slice (206720-206734, never S14's 206705-206719) and BaronHardModeLogic.h names the
    same ids; the boss's Condemned is its own id, never the W1 item effect 205669 (handoff s11 #1);
  - Ysida, Risen 300589: 40,000 health on the level 60 warrior base, the Scourge's faction, stun immune, no heroic
    template, bound to npc_st_ysida_risen;
  - the percent spells carry BaronHardModeLogic.h's numbers (hundredths, the heroic value in MiscValueB too) and their
    scripts are bound and registered; the lane and the trail are resolve copies;
  - Condemned stacks without a cap and clears on a map change; the execution is a 3 s channel with the purple beam;
  - the SQL rev: the gossip option, its conditions (49 / 1 / 13), Ysida's full SmartAI block with the select row
    (SetData(20, 1)) and the texts 11-14 and her line 2.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_stratholme_ultimatum.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Stratholme"
HEADER = MODULE_DIR / "BaronHardModeLogic.h"
SCRIPT = MODULE_DIR / "baron_hard_mode.cpp"
REWORK = MODULE_DIR / "StratholmeRework.h"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_baron_hard_mode_stratholme.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "stratholme"

SLICE = range(206720, 206735)
S14_SLICE = range(206705, 206720)
(EXECUTION, EXECUTION_HIT, EXECUTION_YSIDA, CONDEMNED, CONDEMNED_DOT, PRICE, MARK, TRAMPLE, LANE, TRAIL, TRAIL_LOOK,
 ROT_HEAL, DEATH_COIL, RISEN_STRIKE, RISEN_LOOK) = SLICE
W1_ITEM_CONDEMNED = 205669
YSIDA_RISEN = 300589

SCHOOL_DAMAGE, APPLY_AURA, HEAL, PERSISTENT_AREA_AURA = 2, 6, 10, 27
AURA_PERIODIC_DAMAGE, AURA_DUMMY, AURA_MOD_DAMAGE_PERCENT_DONE = 3, 4, 79
ATTR1_IS_CHANNELED = 0x00000004
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
AURA_INTERRUPT_CHANGE_MAP = 0x00080000
FACTION_SCOURGE = 21
IMMUNITY_BOSS_STUN = 1972
WARRIOR_60_BASE = 3052          # creature_classlevelstats level 60 class 1 basehp0 (live 2026-11-09)
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT = "spell_dungeon_refflat_damage"
REFFLAT_PERIODIC = "spell_dungeon_refflat_periodic"
EXECUTION_SCRIPT = "spell_strat_ultimatum_execution"


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


def _header_number(name: str) -> float:
    match = re.search(rf"{name}\s*=\s*(-?[\d.]+)f?;", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return float(match.group(1))


class UltimatumDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE or int(e["id"]) in S14_SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == YSIDA_RISEN}
        cls.models = {int(e["CreatureID"]): e for e in reg.creature_template_models
                      if int(e["CreatureID"]) == YSIDA_RISEN}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.sql = SQL.read_text(encoding="utf-8")

    def test_spells_fill_the_slice_and_match_the_header(self):
        mine = sorted(i for i in self.spells if i in SLICE)
        self.assertEqual(mine, list(SLICE))
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"spell": mine}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_HM_\w+\s*=\s*(\d+)", self.header)}
        self.assertEqual(header_ids, set(mine))
        self.assertFalse(header_ids & set(S14_SLICE))
        self.assertNotIn(W1_ITEM_CONDEMNED, header_ids)
        rework = REWORK.read_text(encoding="utf-8")
        self.assertIn("kSpellsUltimatum{ 206720, 206734 }", rework)

    def test_ysida_risen(self):
        self.assertEqual(sorted(self.creatures), [YSIDA_RISEN])
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"creature": [YSIDA_RISEN]}), [])
        risen = self.creatures[YSIDA_RISEN]
        self.assertEqual(risen["ScriptName"], "npc_st_ysida_risen")
        self.assertEqual(risen["faction"], FACTION_SCOURGE)
        self.assertEqual(risen["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
        self.assertEqual(risen["minlevel"], 60)
        self.assertEqual(risen["unit_class"], 1)
        self.assertEqual(risen.get("difficulty_entry_1", 0), 0)     # hard mode only: no heroic template (s7 #15)
        self.assertEqual(risen["lootid"], 0)
        health = int(_header_number("kRisenHealth"))
        self.assertGreaterEqual(WARRIOR_60_BASE * risen["HealthModifier"], health - 1)
        self.assertLess(WARRIOR_60_BASE * risen["HealthModifier"], health + 5)
        self.assertEqual(self.models[YSIDA_RISEN]["CreatureDisplayID"], 25355)
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_st_ysida_risen", self.cpp)

    def test_scripts_are_bound_and_registered(self):
        expected = {
            (EXECUTION_HIT, EXECUTION_SCRIPT), (CONDEMNED_DOT, REFFLAT_PERIODIC), (TRAMPLE, REFFLAT),
            (DEATH_COIL, REFFLAT), (RISEN_STRIKE, REFFLAT), (LANE, RESOLVE), (TRAIL, RESOLVE),
        }
        self.assertEqual(self.scripts, expected)
        self.assertIn(f"RegisterSpellScript({EXECUTION_SCRIPT})", self.cpp)
        # The execution's launch hook names the effect the spell carries (a mismatch unbinds it at boot).
        self.assertEqual(self.spells[EXECUTION_HIT]["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertIn("EFFECT_0,\n            SPELL_EFFECT_SCHOOL_DAMAGE", self.cpp)

    def test_percents_match_the_header(self):
        cases = {
            EXECUTION_HIT: "kExecutionPct", CONDEMNED_DOT: "kCondemnedDotPct", TRAMPLE: "kTargetHitPct",
            DEATH_COIL: "kDeathCoilPct", RISEN_STRIKE: "kRisenStrikePct",
        }
        for spell_id, name in cases.items():
            spell = self.spells[spell_id]
            hundredths = round(_header_number(name) * 100)
            self.assertEqual(spell["effect1"]["base_points"] + 1, hundredths, name)
            self.assertEqual(_raw(spell, "EffectMiscValueB_1"), hundredths, name)     # heroic only: the same
            self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS, name)
            self.assertTrue(spell["effect1"].get("_potency_excluded"), name)
        self.assertEqual(_raw(self.spells[TRAMPLE], "Speed"), int(_header_number("kChargeSpeed")))

    def test_condemned_and_the_price(self):
        stack = self.spells[CONDEMNED]
        self.assertEqual(stack["name"], "Condemned")
        self.assertEqual(stack["duration_ms"], -1)
        self.assertEqual(_raw(stack, "CumulativeAura"), 255)
        self.assertTrue(_raw(stack, "AuraInterruptFlags") & AURA_INTERRUPT_CHANGE_MAP)
        self.assertEqual(stack["dispel"], 0)
        dot = self.spells[CONDEMNED_DOT]
        self.assertEqual(dot["name"], "Condemned")
        self.assertEqual(dot["effect1"]["apply_aura"], AURA_PERIODIC_DAMAGE)
        self.assertEqual(dot["effect1"]["amplitude"], 1000)
        self.assertEqual(dot["duration_ms"], int(_header_number("kCondemnedDotMs")))
        self.assertTrue(_raw(dot, "AuraInterruptFlags") & AURA_INTERRUPT_CHANGE_MAP)
        price = self.spells[PRICE]
        self.assertEqual(price["effect1"]["apply_aura"], AURA_MOD_DAMAGE_PERCENT_DONE)
        self.assertEqual(price["effect1"]["base_points"], int(_header_number("kPriceOfDefiancePct")))
        self.assertEqual(price["effect1"]["misc_value"], 127)

    def test_execution_lane_and_trail(self):
        channel = self.spells[EXECUTION]
        self.assertEqual(channel["duration_ms"], int(_header_number("kExecutionCastMs")))
        self.assertTrue(_raw(channel, "AttributesEx") & ATTR1_IS_CHANNELED)
        self.assertEqual(_raw(channel, "SpellVisualID_1"), 7785)
        self.assertEqual(self.spells[MARK]["duration_ms"], int(_header_number("kLaneWarnMs")))
        for spell_id in (LANE, TRAIL):
            self.assertEqual(self.spells[spell_id]["effect1"]["type"], SCHOOL_DAMAGE)
        look = self.spells[TRAIL_LOOK]
        self.assertEqual(look["effect1"]["type"], PERSISTENT_AREA_AURA)
        self.assertEqual(look["effect1"]["radius_yards"], _header_number("kTrailRadius"))
        self.assertEqual(look["duration_ms"], int(_header_number("kTrailLifeMs")))
        self.assertEqual(self.spells[ROT_HEAL]["effect1"]["type"], HEAL)
        self.assertEqual(_raw(self.spells[RISEN_LOOK], "SpellVisualID_1"), 11514)

    def test_the_sql_rev(self):
        sql = self.sql
        self.assertIn("DELETE FROM `gossip_menu_option` WHERE `MenuID` = 7091 AND `OptionID` = 0;", sql)
        self.assertRegex(sql, r"\(7091, 0, 0, '[^']+")
        # Conditions on the option: heroic, the clock's aura, the flag 0, the Baron neither fighting nor dead.
        self.assertIn("(15, 7091, 0, 0, 0, 49, 0, 1, 0, 0, 0,", sql)
        self.assertIn("(15, 7091, 0, 0, 0, 1, 0, 27861, 0, 0, 0,", sql)
        self.assertIn("(15, 7091, 0, 0, 0, 13, 0, 20, 0, 0, 0,", sql)
        self.assertIn("(15, 7091, 0, 0, 0, 13, 0, 14, 1, 2, 1,", sql)
        self.assertIn("(15, 7091, 0, 0, 0, 13, 0, 14, 3, 2, 1,", sql)
        # The SmartAI block: the full block for (16031, 0), stock rows 0-9 and the select row SetData(20, 1).
        self.assertIn("DELETE FROM `smart_scripts` WHERE `entryorguid` = 16031 AND `source_type` = 0;", sql)
        ids = [int(m) for m in re.findall(r"^\(16031, 0, (\d+),", sql, re.M)]
        self.assertEqual(ids, list(range(13)))
        self.assertIn("(16031, 0, 10, 11, 62, 0, 100, 0, 7091, 0, 0, 0, 0, 0, 34, 20, 1, 0,", sql)
        # DATA_ULTIMATUM is 20 in the instance header, BOSS_BARON 14.
        rework = REWORK.read_text(encoding="utf-8")
        self.assertRegex(rework, r"DATA_ULTIMATUM\s*=\s*20,")
        self.assertRegex(rework, r"BOSS_BARON\s*=\s*14,")
        # Texts: the Baron's 11-14, Ysida's 2.
        for group in (11, 12, 13, 14):
            self.assertIn(f"(10440, {group}, 0, '", sql)
        self.assertIn("(16031, 2, 0, 'Don''t wait on me. End him, whatever he does to me.', 12,", sql)


if __name__ == "__main__":
    unittest.main()
