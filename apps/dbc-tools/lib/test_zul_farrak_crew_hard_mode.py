"""
Zul'Farrak build WP-D7Ha, the crew at the pool: source/npcs/zul_farrak/gahzrilla_crew_hard_mode.py against its C++
(modules/mod-dungeon-bosses src/ZulFarrak/GahzrillaCrewHardModeLogic.h, gahzrilla_crew_hard_mode.cpp) and its SQL rev.

Checks:
  - the spells sit in the package's slice (214150-214189), come from gahzrilla_crew_hard_mode.py, and
    GahzrillaCrewHardModeLogic.h names the same ids;
  - the player hits (the Blasting Charge's resolve copy, Storm's Chosen's bolt) are never reflected or redirected and
    ignore the caster's modifiers (rule 2); the second head's Call the Waters is D7's heroic one, kickable; nothing new
    is dispellable; the looks are V's constants;
  - the numbers the DT file restates are the header's (the plant, the marks, the channels, the casts);
  - the Wellspring 301031 and the second head 301032 are scripted, attackable, hostile; the spring names WP-H's
    heroic entry and its 40,000 health, the head has no heroic entry; the C++ registers both scripts, the package, the
    crew handler and the `poolcrew` test key;
  - the SQL rev writes Gahz'rilla's emote line 2 (type 41) and nothing else of D7's, D7Hb's or CR's.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_zul_farrak_crew_hard_mode.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "ZulFarrak"
LOGIC = MODULE_DIR / "GahzrillaCrewHardModeLogic.h"
SCRIPT = MODULE_DIR / "gahzrilla_crew_hard_mode.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_gahzrilla_crew_hard_mode_zul_farrak.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "zul_farrak"
DT_FILE = PACKAGE / "gahzrilla_crew_hard_mode.py"
D7_FILE = PACKAGE / "gahzrilla.py"
VISUALS = PACKAGE / "_visuals.py"
DUNGEON = TOOL_ROOT / "source" / "world" / "dungeons" / "zul_farrak.py"

SLICE = range(214150, 214190)
NAMES = [
    "SPELL_HM_WELLSPRING", "SPELL_HM_BLASTING_CHARGE", "SPELL_HM_BLAST_LOOK", "SPELL_HM_PLANT_CHARGE",
    "SPELL_HM_STORMS_CHOSEN", "SPELL_HM_STORMS_CHOSEN_BOLT", "SPELL_HM_STORM_BOLT_LOOK", "SPELL_HM_BODYGUARD",
    "SPELL_HM_OVERCHARGE", "SPELL_HM_SIPHON_CHARGE", "SPELL_HM_MASS_DISPEL", "SPELL_HM_GREATER_HEAL",
    "SPELL_HM_TWIN_CALL",
]
WELLSPRING, BLAST, BLAST_LOOK, PLANT, CHOSEN, BOLT, BOLT_LOOK, BODYGUARD = range(214150, 214158)
OVERCHARGE, SIPHON, MASS_DISPEL, GREATER_HEAL, TWIN_CALL = range(214158, 214163)
SPRING, HEAD = 301031, 301032
STALKER_DISPLAY = 11686
FACTION_BEAST = 107

SCHOOL_FIRE, SCHOOL_NATURE, SCHOOL_ARCANE = 4, 8, 64
SCHOOL_DAMAGE, DUMMY, APPLY_AURA = 2, 3, 6
ATTR1_IS_CHANNELED = 0x4
ATTR1_NO_REDIRECTION, ATTR1_NO_REFLECTION = 0x8, 0x80
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
NOT_SELECTABLE, NON_ATTACKABLE = 0x02000000, 0x2
RESOLVE_SCRIPT = "spell_boss_mechanics_resolve"


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


def _visual(name: str) -> float:
    text = VISUALS.read_text()
    m = re.search(rf"^{name} = ([\w.]+)", text, re.M)
    assert m, name
    value = m.group(1)
    try:
        return float(value)
    except ValueError:
        return _visual(value)


class CrewHardModeDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        registry.record_provenance()
        try:
            cls.reg = _load()
            cls.files = {int(s["id"]): Path(registry.declared_in(s) or "").name for s in cls.reg.spells}
            cls.creature_files = {int(r["entry"]): Path(registry.declared_in(r) or "").name
                                  for r in cls.reg.creature_templates}
        finally:
            registry.stop_provenance()
        cls.spells = {int(s["id"]): s for s in cls.reg.spells if int(s["id"]) in SLICE}
        cls.rows = {int(r["entry"]): r for r in cls.reg.creature_templates}
        cls.logic = LOGIC.read_text()
        cls.script = SCRIPT.read_text()
        cls.sql = SQL.read_text()
        cls.dt = DT_FILE.read_text()

    def _num(self, name: str) -> float:
        m = re.search(rf"{name} = ([\d.]+)f?;", self.logic)
        self.assertTrue(m, name)
        return float(m.group(1))

    def _dt_num(self, name: str) -> float:
        m = re.search(rf"^{name} = ([\d_]+)", self.dt, re.M)
        self.assertTrue(m, name)
        return float(m.group(1).replace("_", ""))

    def test_spells_are_the_headers(self):
        for offset, name in enumerate(NAMES):
            with self.subTest(name=name):
                self.assertRegex(self.logic, rf"{name}\s*= kSpellSlice\.first \+ {offset},")
                self.assertIn(214150 + offset, self.spells)
                self.assertEqual(self.files[214150 + offset], "gahzrilla_crew_hard_mode.py")
        for sid, name in self.files.items():
            if name == "gahzrilla_crew_hard_mode.py":
                self.assertIn(sid, SLICE)
        self.assertIn(f"kFirstSpareSpell = kSpellSlice.first + {len(NAMES)};", self.logic)

    def test_player_hits(self):
        blast = self.spells[BLAST]
        self.assertEqual(blast["school"], SCHOOL_FIRE)
        self.assertEqual(blast["effect1"]["type"], SCHOOL_DAMAGE)
        bound = {r["ScriptName"] for r in self.reg.spell_script_names if int(r["spell_id"]) == BLAST}
        self.assertEqual(bound, {RESOLVE_SCRIPT})
        self.assertIn(".Spell(SPELL_HM_BLASTING_CHARGE)", self.script)
        self.assertIn(".School(SPELL_SCHOOL_FIRE)", self.script)
        self.assertNotIn(".Weakened()", self.script, "SP: the blast's 60% is its own penalty")
        for sid in (BLAST, BOLT):
            with self.subTest(spell=sid):
                raw = self.spells[sid]["raw_overrides"]
                self.assertTrue(raw["AttributesEx"] & ATTR1_NO_REDIRECTION)
                self.assertTrue(raw["AttributesEx"] & ATTR1_NO_REFLECTION)
                self.assertTrue(raw["AttributesEx3"] & ATTR3_IGNORE_CASTER_MODIFIERS)
        bolt = self.spells[BOLT]
        self.assertEqual(bolt["school"], SCHOOL_NATURE)
        self.assertEqual(bolt["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertEqual(bolt["effect1"]["die_sides"], 0)
        self.assertEqual(bolt["raw_overrides"]["SpellVisualID_1"], _visual("GZ_STORM_STRIKE"))

    def test_twin_call_is_d7s_call(self):
        twin = self.spells[TWIN_CALL]
        raw = twin["raw_overrides"]
        self.assertEqual(twin["school"], SCHOOL_ARCANE)
        self.assertEqual(raw["InterruptFlags"], 15)
        self.assertEqual(raw["PreventionType"], 1)
        call = re.search(r"^CALL_CAST_MS = \((\d+), (\d+)\)", D7_FILE.read_text(), re.M)
        self.assertTrue(call)
        self.assertEqual(twin["cast_time_ms"], int(call.group(2)), "the heroic Call the Waters' 2 s")
        self.assertEqual(self._dt_num("TWIN_CALL_CAST_MS"), int(call.group(2)))
        self.assertIn("kTwinCallCastMs = ZfPool::Tune::kCallCastMs.heroic;", self.logic)

    def test_nothing_new_is_dispellable_and_the_looks_are_vs(self):
        for sid, s in self.spells.items():
            with self.subTest(spell=sid):
                self.assertEqual(int(s.get("dispel") or 0), 0)
        looks = {WELLSPRING: "GZ_GEYSER", BLAST_LOOK: "GZ_BLAST", BOLT_LOOK: "GZ_STORM_STRIKE",
                 BODYGUARD: "BC_INTERVENE", CHOSEN: "BC_MARK", OVERCHARGE: "GZ_CONDUCTIVE", SIPHON: "GZ_OVERCHARGE",
                 MASS_DISPEL: "GZ_MASS_DISPEL", GREATER_HEAL: "BC_GREATER_HEAL", TWIN_CALL: "GZ_TIDAL_CHARM"}
        for sid, name in looks.items():
            with self.subTest(spell=sid):
                self.assertEqual(self.spells[sid]["raw_overrides"]["SpellVisualID_1"], _visual(name))
        self.assertNotEqual(self.spells[BOLT]["raw_overrides"]["SpellVisualID_1"], 4229)    # V: never wired
        self.assertTrue(self.spells[SIPHON]["raw_overrides"]["AttributesEx"] & ATTR1_IS_CHANNELED)

    def test_numbers_match_the_header(self):
        pairs = {"PLANT_MS": "kPlantMs", "CHOSEN_MARK_MS": "kChosenMarkMs", "OVERCHARGE_MS": "kOverchargeMs",
                 "SIPHON_MS": "kSiphonMs", "MASS_DISPEL_CAST_MS": "kMassDispelCastMs",
                 "GREATER_HEAL_CAST_MS": "kGreaterHealCastMs"}
        for dt, cpp in pairs.items():
            with self.subTest(name=dt):
                self.assertEqual(self._dt_num(dt), self._num(cpp))
        self.assertEqual(self.spells[PLANT]["cast_time_ms"], self._num("kPlantMs"))
        self.assertEqual(self.spells[CHOSEN]["duration_ms"], self._num("kChosenMarkMs"))
        self.assertEqual(self.spells[OVERCHARGE]["duration_ms"], self._num("kOverchargeMs"))
        self.assertEqual(self.spells[SIPHON]["duration_ms"], self._num("kSiphonMs"))
        self.assertEqual(self.spells[MASS_DISPEL]["cast_time_ms"], self._num("kMassDispelCastMs"))
        self.assertEqual(self.spells[GREATER_HEAL]["cast_time_ms"], self._num("kGreaterHealCastMs"))
        # SP GZ15-GZ18 and section 3.6.
        self.assertEqual(self._num("kBlastPct"), 60)
        self.assertEqual(self._num("kBlastRadiusYd"), 10)
        self.assertEqual(self._num("kChosenPct"), 150)
        self.assertEqual(self._num("kOverchargeStacks"), 5)
        self.assertEqual(self._num("kWellspringRadiusYd"), 6)
        self.assertEqual(self._num("kWellspringMinFromPlayerYd"), 15)

    def test_creatures(self):
        heroic = re.search(r"301031: (\d+)", DUNGEON.read_text())
        self.assertTrue(heroic, "WP-H's predicted heroic entry for the Wellspring")
        health = re.search(r"301031: dict\(health=([\d_]+)\)", DUNGEON.read_text())
        self.assertTrue(health)
        self.assertEqual(self._dt_num("WELLSPRING_HEROIC"), int(heroic.group(1)))
        self.assertEqual(self._dt_num("WELLSPRING_HEALTH"), int(health.group(1).replace("_", "")))
        for entry, script in ((SPRING, "npc_zf_wellspring"), (HEAD, "npc_zf_second_head")):
            with self.subTest(entry=entry):
                row = self.rows[entry]
                self.assertEqual(self.creature_files[entry], "gahzrilla_crew_hard_mode.py")
                self.assertEqual(row["ScriptName"], script)
                self.assertEqual(row["AIName"], "")
                self.assertEqual(int(row["faction"]), FACTION_BEAST)
                self.assertEqual(int(row["unit_flags"]) & (NOT_SELECTABLE | NON_ATTACKABLE), 0,
                                 "the spring is killed, the head kicked")
                self.assertEqual(int(row["lootid"]), 0)
                models = [m for m in self.reg.creature_template_models if int(m["CreatureID"]) == entry]
                self.assertEqual([int(m["CreatureDisplayID"]) for m in models], [STALKER_DISPLAY])
                self.assertRegex(self.script, rf"RegisterDungeonReworkCreatureAI\({script},")
        spring = self.rows[SPRING]
        self.assertEqual(int(spring["difficulty_entry_1"]), int(heroic.group(1)))
        self.assertAlmostEqual(float(spring["HealthModifier"]) * 3052, 40_000, delta=20)
        self.assertEqual(int(self.rows[HEAD].get("difficulty_entry_1") or 0), 0)

    def test_script(self):
        self.assertIn("ZfPool::RegisterPoolHardMode(ZfPool::PoolPackage::Crew", self.script)
        self.assertIn("ZfCrew::RegisterCrewModeHandler(CrewMode::PoolAlly", self.script)
        self.assertIn('ZfTest::RegisterBoss("poolcrew"', self.script)
        self.assertIn("AddSC_gahzrilla_crew_hard_mode()", self.script)
        self.assertNotIn("spell_zf_static_discharge", self.script)
        # Rule 28: the crew are moved, hurt, healed and killed through BlyCrew.h only; their faction is CR's.
        self.assertNotIn("SetFaction(", self.script.replace("head->SetFaction(", ""))
        self.assertNotIn("Unit::Kill(", self.script)
        self.assertIn("ZfCrew::DamageCrew(", self.script)
        self.assertIn("ZfCrew::HealCrew(", self.script)
        self.assertIn("ZfCrew::KillCrew(", self.script)
        # Rule 1: no loot or hard mode bit here (the instance's).
        self.assertNotIn("SetHardModeLoot", self.script)
        self.assertNotIn("DATA_GONG_STRUCK", self.script)

    def test_sql(self):
        self.assertIn("(7273, 2, 0, '%s devours $n!', 41,", self.sql)
        self.assertIn("WHERE `CreatureID` = 7273 AND `GroupID` = 2;", self.sql)
        self.assertNotRegex(self.sql, r"\(7273, [01],")
        for other in ("7795", "(7604,", "(7607,"):
            self.assertNotIn(other, self.sql)


if __name__ == "__main__":
    unittest.main()
