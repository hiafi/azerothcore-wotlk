"""
Zul'Farrak build WP-D7, Velratha and Gahz'rilla: source/npcs/zul_farrak/gahzrilla.py against its C++
(modules/mod-dungeon-bosses src/ZulFarrak/GahzrillaLogic.h, boss_gahzrilla_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in the pool's slice (214110-214149) and GahzrillaLogic.h names the same ids;
  - the cast times are the header's (s10 #40 B: Spill 4 s / 3 s, Icicle 2.5 s);
  - kicks (rule 24): Call the Waters and Healing Wave are kickable; every must-land bar is not and never shares a
    school with that unit's kickable casts; Icicle and Freeze Solid have no interrupt flags;
  - every damage spell takes the script's base point (or the weapon) and is never reflected or redirected, the script
    hits ignore caster modifiers (rule 2, LESSONS L7); the Slam has no knock back;
  - the looks are V's; the disc displays are the header's;
  - 7795 and 7273 are bound, 7273 stands still, the stalker 301030 is scripted, untouchable and not a trigger;
  - the C++ registers its three scripts and calls NoAssist in both bosses;
  - the SQL rev writes the three texts and stops the patrol with guarded UPDATEs.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_zul_farrak_gahzrilla.py
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
LOGIC = MODULE_DIR / "GahzrillaLogic.h"
SCRIPT = MODULE_DIR / "boss_gahzrilla_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_gahzrilla_zul_farrak.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "zul_farrak"
VISUALS = PACKAGE / "_visuals.py"

SLICE = range(214110, 214150)
(SPILL, SPILL_H, SPILL_MARK, STATIC_CHARGE, DISCHARGE_BAR, DISCHARGE, STATIC_SHOCK, CALL, CALL_H, ICICLE,
 FREEZE_SOLID, FREEZE_LOOK, SLAM, HEAL, HEAL_H, ACID_SPIT, CHARGED, CONDUCTIVE, CONDUCTIVE_ARC,
 GONG_STRIKE) = range(214110, 214130)
NAMES = ["SPELL_GZ_SPILL", "SPELL_GZ_SPILL_HEROIC", "SPELL_GZ_SPILL_MARK", "SPELL_GZ_STATIC_CHARGE",
         "SPELL_GZ_DISCHARGE_BAR", "SPELL_GZ_DISCHARGE", "SPELL_GZ_STATIC_SHOCK", "SPELL_GZ_CALL_THE_WATERS",
         "SPELL_GZ_CALL_THE_WATERS_HEROIC", "SPELL_GZ_ICICLE", "SPELL_GZ_FREEZE_SOLID", "SPELL_GZ_FREEZE_LOOK",
         "SPELL_GZ_SLAM", "SPELL_GZ_HEALING_WAVE", "SPELL_GZ_HEALING_WAVE_HEROIC", "SPELL_GZ_ACID_SPIT",
         "SPELL_GZ_CHARGED", "SPELL_GZ_CONDUCTIVE", "SPELL_GZ_CONDUCTIVE_ARC", "SPELL_GZ_GONG_STRIKE"]
VELRATHA, GAHZRILLA, PUDDLE = 7795, 7273, 301030

SCHOOL_NATURE, SCHOOL_FROST, SCHOOL_ARCANE = 8, 16, 64
SCHOOL_DAMAGE, WEAPON_PERCENT, KNOCK_BACK = 2, 31, 98
KICKABLE = 15
PREVENTION_SILENCE = 1
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


def _visual(name: str) -> int:
    text = VISUALS.read_text()
    m = re.search(rf"^{name} = (\w+)", text, re.M)
    assert m, name
    value = m.group(1)
    return int(value) if value.isdigit() else _visual(value)


class GahzrillaDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        registry.record_provenance()
        try:
            cls.reg = _load()
            cls.files = {int(s["id"]): Path(registry.declared_in(s) or "").name for s in cls.reg.spells}
        finally:
            registry.stop_provenance()
        cls.spells = {int(s["id"]): s for s in cls.reg.spells if int(s["id"]) in SLICE}
        cls.edits = {int(r["entry"]): r for r in cls.reg.creature_template_edits}
        cls.rows = {int(r["entry"]): r for r in cls.reg.creature_templates}
        cls.logic = LOGIC.read_text()
        cls.script = SCRIPT.read_text()
        cls.sql = SQL.read_text()

    def _const(self, name: str) -> int:
        m = re.search(rf"{name}\s*=\s*(\d+)", self.logic)
        self.assertTrue(m, name)
        return int(m.group(1))

    def _nh(self, name: str) -> tuple[int, int]:
        m = re.search(rf"NH<std::uint32_t> {name}\{{ (\d+), (\d+) \}}", self.logic)
        self.assertTrue(m, name)
        return int(m.group(1)), int(m.group(2))

    def test_spells_are_the_headers(self):
        for offset, name in enumerate(NAMES):
            with self.subTest(name=name):
                self.assertRegex(self.logic, rf"{name}\s*= kSpellSlice\.first \+ {offset},")
                self.assertIn(214110 + offset, self.spells)
                self.assertEqual(self.files[214110 + offset], "gahzrilla.py")
        for sid, name in self.files.items():
            if name == "gahzrilla.py":
                self.assertIn(sid, SLICE)

    def test_cast_times(self):
        spill = self._nh("kSpillCastMs")
        self.assertEqual(spill, (4000, 3000))      # s10 #40 B
        self.assertEqual(self.spells[SPILL]["cast_time_ms"], spill[0])
        self.assertEqual(self.spells[SPILL_H]["cast_time_ms"], spill[1])
        call = self._nh("kCallCastMs")
        self.assertEqual((self.spells[CALL]["cast_time_ms"], self.spells[CALL_H]["cast_time_ms"]), call)
        heal = self._nh("kHealCastMs")
        self.assertEqual((self.spells[HEAL]["cast_time_ms"], self.spells[HEAL_H]["cast_time_ms"]), heal)
        self.assertEqual(self._const("kIcicleCastMs"), 2500)   # s10 #40 B
        self.assertEqual(self.spells[ICICLE]["cast_time_ms"], 2500)
        self.assertEqual(self.spells[FREEZE_SOLID]["cast_time_ms"], self._const("kFreezeSolidCastMs"))
        self.assertEqual(self.spells[DISCHARGE_BAR]["cast_time_ms"], self._const("kDischargeCastMs"))
        self.assertEqual(self.spells[STATIC_SHOCK]["duration_ms"], self._const("kStaticShockMs"))
        self.assertEqual(self.spells[FREEZE_SOLID]["duration_ms"], self._const("kFreezeSolidStunMs"))
        self.assertEqual(self.spells[CONDUCTIVE]["duration_ms"], self._const("kConductiveMs"))
        self.assertEqual(self.spells[STATIC_CHARGE]["raw_overrides"]["CumulativeAura"],
                         self._const("kStaticChargeMax"))
        self.assertEqual(self.spells[CHARGED]["raw_overrides"]["CumulativeAura"], self._const("kChargedMaxStacks"))

    def test_kicks_and_schools(self):
        def raw(sid):
            return self.spells[sid]["raw_overrides"]

        for sid in (CALL, CALL_H, HEAL, HEAL_H):
            self.assertEqual(raw(sid)["InterruptFlags"], KICKABLE, sid)
            self.assertEqual(raw(sid)["PreventionType"], PREVENTION_SILENCE, sid)
        for sid in (SPILL, SPILL_H, DISCHARGE_BAR, ICICLE, FREEZE_SOLID):
            self.assertEqual(raw(sid)["InterruptFlags"], 0, sid)
            self.assertEqual(raw(sid)["PreventionType"], 0, sid)
        # Velratha: kickable Frostbolt (Frost) and Healing Wave (Nature); the Spill bar is Arcane.
        self.assertEqual(self.spells[HEAL]["school"], SCHOOL_NATURE)
        self.assertEqual(self.spells[SPILL]["school"], SCHOOL_ARCANE)
        self.assertEqual(self.spells[SPILL_H]["school"], SCHOOL_ARCANE)
        # Gahz'rilla: kickable Call the Waters (Arcane); the Discharge bar Nature, the freezes Frost.
        self.assertEqual(self.spells[CALL]["school"], SCHOOL_ARCANE)
        self.assertEqual(self.spells[DISCHARGE_BAR]["school"], SCHOOL_NATURE)
        self.assertEqual(self.spells[ICICLE]["school"], SCHOOL_FROST)
        self.assertEqual(self.spells[FREEZE_SOLID]["school"], SCHOOL_FROST)

    def test_damage_spells(self):
        for sid in (DISCHARGE, ICICLE, FREEZE_SOLID, ACID_SPIT, CONDUCTIVE_ARC):
            with self.subTest(spell=sid):
                s = self.spells[sid]
                self.assertEqual(s["effect1"]["type"], SCHOOL_DAMAGE)
                self.assertEqual(s["effect1"]["base_points"], 0)
                self.assertEqual(s["effect1"]["die_sides"], 0)
                raw = s["raw_overrides"]
                self.assertTrue(raw["AttributesEx"] & ATTR1_NO_REDIRECTION)
                self.assertTrue(raw["AttributesEx"] & ATTR1_NO_REFLECTION)
                self.assertTrue(raw["AttributesEx3"] & ATTR3_IGNORE_CASTER_MODIFIERS)
        slam = self.spells[SLAM]
        self.assertEqual(slam["effect1"]["type"], WEAPON_PERCENT)
        self.assertEqual(slam["effect1"]["radius_yards"], 20.0)
        for key in ("effect2", "effect3"):
            self.assertNotEqual((slam.get(key) or {}).get("type"), KNOCK_BACK)
        # The stuns: Freeze Solid's is Magic (a reward), Static Shock's is not dispellable.
        self.assertEqual(self.spells[FREEZE_SOLID]["dispel"], 1)
        self.assertEqual(self.spells[STATIC_SHOCK]["dispel"], 0)
        self.assertEqual(self.spells[CONDUCTIVE]["dispel"], 1)
        self.assertEqual(self.spells[CHARGED]["dispel"], 0)

    def test_looks_are_vs(self):
        expect = {
            SPILL: "GZ_TIDAL_CHARM", SPILL_H: "GZ_TIDAL_CHARM", SPILL_MARK: "GZ_TIDAL_CHARM",
            STATIC_CHARGE: "GZ_STATIC_CHARGE", DISCHARGE_BAR: "GZ_DISCHARGE", DISCHARGE: "GZ_DISCHARGE",
            CALL: "GZ_ACID_SPIT", ICICLE: "GZ_ICICLE", FREEZE_SOLID: "GZ_FREEZE_SOLID",
            FREEZE_LOOK: "GZ_FREEZE_EVENT", SLAM: "GZ_SLAM", ACID_SPIT: "GZ_ACID_SPIT",
            CONDUCTIVE: "GZ_CONDUCTIVE", HEAL: "AS_HEAL",
        }
        for sid, name in expect.items():
            with self.subTest(spell=sid):
                self.assertEqual(self.spells[sid]["raw_overrides"]["SpellVisualID_1"], _visual(name))
        self.assertEqual(self._const("kDisplayWaterDisc"), _visual("GZ_WATER_DISC"))
        self.assertEqual(self._const("kDisplayIceDisc"), _visual("GZ_ICE_DISC"))
        self.assertEqual(self._const("kDisplayStormDisc"), _visual("GZ_STORM_DISC"))
        self.assertIn("kDiscYdPerScale = 4.8f", self.logic)
        self.assertIn("DISC_QUAD_RADIUS = 4.8", VISUALS.read_text())

    def test_units(self):
        self.assertEqual(self.edits[VELRATHA]["ScriptName"], "boss_velratha_rework")
        self.assertEqual(self.edits[GAHZRILLA]["ScriptName"], "boss_gahzrilla_rework")
        self.assertEqual(self.edits[GAHZRILLA]["MovementType"], 0)
        puddle = self.rows[PUDDLE]
        self.assertEqual(puddle["ScriptName"], "npc_zf_puddle")
        self.assertFalse(puddle["flags_extra"] & TRIGGER, "a trigger is invisible to players: the disc must show")
        self.assertEqual(puddle["unit_flags"] & (NOT_SELECTABLE | NON_ATTACKABLE), NOT_SELECTABLE | NON_ATTACKABLE)

    def test_script(self):
        for name in ("boss_velratha_rework", "boss_gahzrilla_rework", "npc_zf_puddle"):
            self.assertRegex(self.script, rf"RegisterDungeonReworkCreatureAI\({name},")
        self.assertEqual(self.script.count("ZulFarrak::NoAssist(me);"), 2)
        self.assertIn('ZfTest::RegisterBoss("pool"', self.script)
        self.assertNotIn("spell_zf_static_discharge", self.script)

    def test_sql(self):
        self.assertIn("(7795, 0, 0, 'The sacred pool is not for outlanders!', 14,", self.sql)
        self.assertIn("(7795, 1, 0, 'Rise, Gahz''rilla! The waters are yours!', 14,", self.sql)
        self.assertIn("(7273, 0, 0, '%s''s scales crackle with building charge!', 41,", self.sql)
        self.assertIn("WHERE `guid` = 81570 AND `id` = 7795;", self.sql)
        self.assertIn("WHERE `guid` = 81570 AND `path_id` = 815700;", self.sql)
        # Groups 1 and 2 of 7273 are the hard mode packages'.
        self.assertNotRegex(self.sql, r"\(7273, [12],")
        # F-2 M1 / R-Q m1: her later bodies roll only the quest rows (bit 0x20, kLootModeVelrathaQuest)
        self.assertIn("UPDATE `creature_loot_template` SET `LootMode` = `LootMode` | 32\n    WHERE `Entry` = 7795 AND "
                      "`Item` IN (9234, 10661) AND `Reference` = 0 AND `GroupId` = 0 AND `QuestRequired` = 1;",
                      self.sql)


if __name__ == "__main__":
    unittest.main()
