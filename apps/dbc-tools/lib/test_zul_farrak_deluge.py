"""
Zul'Farrak build WP-D7Hb, the Deluge: source/npcs/zul_farrak/gahzrilla_deluge.py against its C++
(modules/mod-dungeon-bosses src/ZulFarrak/GahzrillaDelugeLogic.h, gahzrilla_deluge.cpp) and its SQL rev.

Checks:
  - the spells sit in the Deluge's slice (214190-214209), come from gahzrilla_deluge.py, and
    GahzrillaDelugeLogic.h names the same ids;
  - Storm Strike's damage is a Nature resolve copy bound to the registry's resolve script (rule 2: never reflected or
    redirected, ignores the caster's modifiers); the bolt is look-only, aimed at a point, with V's SV 90702;
  - the numbers the DT file restates are the header's (strike 30%, 3 yd, 1.5 s, three a second; V's rise scales);
  - the strike stalker 301033 is scripted, untouchable and not a trigger (its casts must show), wearing the stalker
    display; the C++ registers its script and the package, under the `deluge` test key, and never edits D7's file;
  - the SQL rev writes Gahz'rilla's emote line 1 (type 41) and nothing else of D7's or D7Ha's.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_zul_farrak_deluge.py
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
LOGIC = MODULE_DIR / "GahzrillaDelugeLogic.h"
SCRIPT = MODULE_DIR / "gahzrilla_deluge.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_gahzrilla_deluge_zul_farrak.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "zul_farrak"
DT_FILE = PACKAGE / "gahzrilla_deluge.py"
VISUALS = PACKAGE / "_visuals.py"

SLICE = range(214190, 214210)
STRIKE, STRIKE_LOOK = 214190, 214191
NAMES = ["SPELL_DELUGE_STORM_STRIKE", "SPELL_DELUGE_STORM_STRIKE_LOOK"]
STALKER = 301033
STALKER_DISPLAY = 11686

SCHOOL_NATURE = 8
SCHOOL_DAMAGE, DUMMY = 2, 3
TARGET_DEST_DEST = 87
ATTR1_NO_REDIRECTION, ATTR1_NO_REFLECTION = 0x8, 0x80
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
TRIGGER = 0x80
NOT_SELECTABLE, NON_ATTACKABLE = 0x02000000, 0x2


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


class DelugeDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        registry.record_provenance()
        try:
            cls.reg = _load()
            cls.files = {int(s["id"]): Path(registry.declared_in(s) or "").name for s in cls.reg.spells}
        finally:
            registry.stop_provenance()
        cls.spells = {int(s["id"]): s for s in cls.reg.spells if int(s["id"]) in SLICE}
        cls.rows = {int(r["entry"]): r for r in cls.reg.creature_templates}
        cls.logic = LOGIC.read_text()
        cls.script = SCRIPT.read_text()
        cls.sql = SQL.read_text()

    def _num(self, name: str) -> float:
        m = re.search(rf"{name} = ([\d.]+)f?;", self.logic)
        self.assertTrue(m, name)
        return float(m.group(1))

    def test_spells_are_the_headers(self):
        for offset, name in enumerate(NAMES):
            with self.subTest(name=name):
                self.assertRegex(self.logic, rf"{name}\s*= kSpellSlice\.first \+ {offset},")
                self.assertIn(214190 + offset, self.spells)
                self.assertEqual(self.files[214190 + offset], "gahzrilla_deluge.py")
        for sid, name in self.files.items():
            if name == "gahzrilla_deluge.py":
                self.assertIn(sid, SLICE)
        self.assertIn("kFirstSpareSpell = kSpellSlice.first + 2;", self.logic)

    def test_storm_strike(self):
        s = self.spells[STRIKE]
        self.assertEqual(s["school"], SCHOOL_NATURE)
        self.assertEqual(s["effect1"]["type"], SCHOOL_DAMAGE)
        raw = s["raw_overrides"]
        self.assertTrue(raw["AttributesEx"] & ATTR1_NO_REDIRECTION)
        self.assertTrue(raw["AttributesEx"] & ATTR1_NO_REFLECTION)
        self.assertTrue(raw["AttributesEx3"] & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertIn(".Spell(SPELL_DELUGE_STORM_STRIKE)", self.script)
        self.assertIn(".School(SPELL_SCHOOL_NATURE)", self.script)
        self.assertIn(".Weakened()", self.script)
        look = self.spells[STRIKE_LOOK]
        self.assertEqual(look["effect1"]["type"], DUMMY)
        self.assertEqual(look["effect1"]["implicit_target_a"], TARGET_DEST_DEST)
        self.assertEqual(look["raw_overrides"]["SpellVisualID_1"], _visual("GZ_STORM_STRIKE"))
        self.assertNotEqual(look["raw_overrides"]["SpellVisualID_1"], 4229)     # V: never wired

    def test_numbers_match_the_header(self):
        dt = DT_FILE.read_text()

        def dt_num(name: str) -> float:
            m = re.search(rf"^{name} = (\d+)", dt, re.M)
            self.assertTrue(m, name)
            return float(m.group(1))

        self.assertEqual(self._num("kStrikePct"), dt_num("STRIKE_PCT"))
        self.assertEqual(self._num("kStrikeRadiusYd"), dt_num("STRIKE_RADIUS_YD"))
        self.assertEqual(self._num("kStrikeWarnMs"), dt_num("STRIKE_WARN_MS"))
        self.assertEqual(self._num("kStrikesPerSecond"), dt_num("STRIKES_PER_SECOND"))
        self.assertIn("RISE_SCALES = (DELUGE_DISC_START_SCALE, DELUGE_DISC_SCALE)", dt)
        self.assertEqual((self._num("kRiseStartScale"), self._num("kRiseEndScale")),
                         (_visual("DELUGE_DISC_START_SCALE"), _visual("DELUGE_DISC_SCALE")))
        # Section 3.7 / SP GZ23: floes 8 and 12 yd, 30 s; Icicle every 5 s.
        self.assertEqual(self._num("kIcicleFloeYd"), 8)
        self.assertEqual(self._num("kFreezeSolidFloeYd"), 12)
        self.assertEqual(self._num("kFloeThawMs"), 30000)
        self.assertEqual(self._num("kIcicleEveryMs"), 5000)
        self.assertEqual(self._num("kDelugeHealthPct"), 40)

    def test_stalker(self):
        row = self.rows[STALKER]
        self.assertEqual(row["ScriptName"], "npc_zf_strike_stalker")
        self.assertFalse(row["flags_extra"] & TRIGGER, "a trigger's casts may not show: the bolt must")
        self.assertEqual(row["unit_flags"] & (NOT_SELECTABLE | NON_ATTACKABLE), NOT_SELECTABLE | NON_ATTACKABLE)
        models = [m for m in self.reg.creature_template_models if int(m["CreatureID"]) == STALKER]
        self.assertEqual([int(m["CreatureDisplayID"]) for m in models], [STALKER_DISPLAY])
        self.assertNotRegex(DT_FILE.read_text(), r"creature_template\w*\(\s*301032",
                            "the second head is D7Ha's (Twin Call), not declared here")

    def test_script(self):
        self.assertRegex(self.script, r"RegisterDungeonReworkCreatureAI\(npc_zf_strike_stalker,")
        self.assertIn("ZfPool::RegisterPoolHardMode(ZfPool::PoolPackage::Deluge", self.script)
        self.assertIn('ZfTest::RegisterBoss("deluge"', self.script)
        self.assertNotIn("spell_zf_static_discharge", self.script)
        self.assertIn("NPC_ZF_STRIKE_STALKER", self.script)

    def test_sql(self):
        self.assertIn("(7273, 1, 0, '%s sinks into the sacred pool, and the waters rise!', 41,", self.sql)
        self.assertIn("WHERE `CreatureID` = 7273 AND `GroupID` = 1;", self.sql)
        self.assertNotRegex(self.sql, r"\(7273, [02],")
        self.assertNotIn("7795", self.sql)


if __name__ == "__main__":
    unittest.main()
