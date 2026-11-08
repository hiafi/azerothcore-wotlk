"""
Scholomance build WP-S10, Lady Illucia Barov: source/npcs/scholomance/lady_illucia_barov.py against its C++
(modules/mod-dungeon-bosses src/Scholomance/IlluciaLogic.h, boss_lady_illucia_barov_rework.cpp).

Checks:
  - the spells sit in Illucia's slice (206315-206329) and IlluciaLogic.h names the same ids; she declares no creature;
  - the Foresight cast bar is 1.5 s and not interruptible; the read debuff lasts the cast plus the heroic chain;
  - the marker, trail and end-marker hits are resolve copies bound to spell_boss_mechanics_resolve;
  - the Fear is a real 1.5 s interruptible cast of a 2 s Magic fear (mechanic fear), bound to its aura script, which
    the C++ registers; it is never the stock 12542;
  - the looks are WP-V's picks;
  - 10502 is bound to boss_lady_illucia_barov_rework with SmartAI off, HealthModifier 65.52, DamageModifier 3.5 and
    immunity set 1972; the examiner script name in the C++ matches IlluciaLogic.h and is registered only with wave C.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scholomance_illucia.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Scholomance"
HEADER = MODULE_DIR / "IlluciaLogic.h"
SCRIPT = MODULE_DIR / "boss_lady_illucia_barov_rework.cpp"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "scholomance"

SLICE = range(206315, 206330)
FORESIGHT_CAST, READ, FORESIGHT, MEMORY, FEAR, FEAR_END = range(206315, 206321)
ILLUCIA = 10502

SCHOOL_SHADOW = 32
SCHOOL_DAMAGE, APPLY_AURA = 2, 6
AURA_DUMMY, AURA_MOD_FEAR = 4, 7
DISPEL_MAGIC = 1
MECHANIC_FEAR = 5
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
RESOLVE = "spell_boss_mechanics_resolve"
FEAR_SCRIPT = "spell_scholo_illucia_fear"


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


def _header_int(name: str) -> int:
    match = re.search(rf"{name}\s*=\s*(-?\d+)", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return int(match.group(1))


class IlluciaDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = [e for e in reg.creature_template_edits if int(e["entry"]) == ILLUCIA]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(FORESIGHT_CAST, FEAR_END + 1)))
        self.assertEqual(id_blocks.out_of_reservation("scholomance", {"spell": mine}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_IB_\w+\s*=\s*(\d+)", self.header)}
        self.assertEqual(header_ids, set(mine))
        self.assertNotIn(12542, self.spells)

    def test_foresight(self):
        cast = self.spells[FORESIGHT_CAST]
        self.assertEqual(cast["cast_time_ms"], _header_int("kForesightCastMs"))
        self.assertEqual(_raw(cast, "InterruptFlags"), 0)
        read = self.spells[READ]
        self.assertEqual(read["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(read["dispel"], 0)
        # ReadAuraMs(5): the cast plus five 1.5 s markers.
        self.assertEqual(read["duration_ms"], _header_int("kForesightCastMs") + 5 * _header_int("kForesightMarkerMs"))
        self.assertIn("CastSpell(player, SPELL_IB_READ, true)", self.cpp)

    def test_hits_are_resolve_copies(self):
        for spell_id in (FORESIGHT, MEMORY, FEAR_END):
            hit = self.spells[spell_id]
            self.assertEqual(hit["effect1"]["type"], SCHOOL_DAMAGE)
            self.assertEqual(hit["school"], SCHOOL_SHADOW)
            self.assertTrue(_raw(hit, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
            self.assertIn((spell_id, RESOLVE), self.scripts)
        self.assertIn("Spell(SPELL_IB_FORESIGHT)", self.cpp)
        self.assertIn("linger.spellId = SPELL_IB_MEMORY", self.cpp)
        self.assertIn("Spell(SPELL_IB_FEAR_END)", self.cpp)

    def test_the_fear_is_a_real_interruptible_two_second_fear(self):
        fear = self.spells[FEAR]
        self.assertEqual(fear["cast_time_ms"], _header_int("kFearCastMs"))
        self.assertEqual(fear["duration_ms"], _header_int("kFearMs"))
        self.assertEqual(fear["dispel"], DISPEL_MAGIC)
        self.assertEqual(fear["mechanic"], MECHANIC_FEAR)
        self.assertEqual(fear["effect1"]["apply_aura"], AURA_MOD_FEAR)
        self.assertEqual(fear["effect1"]["mechanic"], MECHANIC_FEAR)
        self.assertEqual(_raw(fear, "InterruptFlags"), 15)
        self.assertEqual(_raw(fear, "PreventionType"), 1)
        self.assertEqual(fear["range_yards"], float(_header_int("kFearRange")))
        self.assertIn((FEAR, FEAR_SCRIPT), self.scripts)
        self.assertIn(f"RegisterSpellScript({FEAR_SCRIPT})", self.cpp)
        own = {name for _, name in self.scripts if name != RESOLVE}
        self.assertEqual(own, {FEAR_SCRIPT})
        # The interrupt and dispel lists of the descriptor.
        self.assertIn("SPELL_IB_FEAR, 2, Milliseconds(kFearEveryMs)", self.cpp)
        self.assertIn("d.dispels.emplace_back(SPELL_IB_FEAR, 3, true)", self.cpp)
        self.assertIn("d.dispels.emplace_back(SPELL_CURSE_OF_AGONY, 1)", self.cpp)

    def test_looks_are_the_visual_picks(self):
        expected = {READ: 4839, FORESIGHT: 13255, MEMORY: 12121, FEAR: 13757, FEAR_END: 3057}
        for spell_id, visual in expected.items():
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), visual, spell_id)

    def test_illucia_is_bound(self):
        self.assertEqual(len(self.edits), 1)
        edit = self.edits[0]
        self.assertEqual(edit["ScriptName"], "boss_lady_illucia_barov_rework")
        self.assertEqual(edit["AIName"], "")
        self.assertEqual(edit["HealthModifier"], 65.52)
        self.assertEqual(edit["DamageModifier"], 3.5)
        self.assertEqual(edit["CreatureImmunitiesId"], 1972)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_lady_illucia_barov_rework,", self.cpp)

    def test_the_examiner_script_name_matches_and_waits_for_wave_c(self):
        name = re.search(r'kExaminerScriptName\[\]\s*=\s*"(\w+)"', self.header).group(1)
        self.assertIn(f"struct {name} : public ScriptedAI", self.cpp)
        self.assertRegex(self.cpp, rf"if \(kWaveCBound\)\s*\n\s*RegisterDungeonReworkCreatureAI\({name},")
        self.assertEqual(_header_int("kExaminerHealth"), 80000)

    def test_the_lesson_is_registered(self):
        self.assertIn("RegisterSoloLesson(Classroom::ShadowVault,", self.cpp)


if __name__ == "__main__":
    unittest.main()
