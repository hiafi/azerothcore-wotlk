"""
Blackrock Spire build WP-B9, Overlord Wyrmthalak's hard mode (the war horn): source/npcs/blackrock_spire/
wyrmthalak_hard_mode.py against its C++ (modules/mod-dungeon-bosses src/BlackrockSpire/WyrmthalakHardModeLogic.h,
wyrmthalak_hard_mode.cpp) and its SQL rev.

Checks:
  - the spells sit in the war horn's slice (210290-210339) and WyrmthalakHardModeLogic.h names the same ids;
  - the hits are resolve copies of the right school;
  - Tribal Ward is -20% damage taken a stack, 3 stacks; Caustic Poison and Rabies are the kit's periodic percent spell
    with the header's numbers, dispellable (Poison, Disease); the rider's bite procs Rabies on melee;
  - Caustic Roar is a 2.5 s Nature cast the bots can kick, bound to its SpellScript; the spear chain is a 20 s beam;
  - the missiles' speeds match the header;
  - the horn's object and spawn (301255, heroic only, at kWarHornSpot) and the script registrations.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_spire_wyrmthalak_hard_mode.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockSpire"
HEADER = MODULE_DIR / "WyrmthalakHardModeLogic.h"
REWORK = MODULE_DIR / "BlackrockSpireRework.h"
SCRIPT = MODULE_DIR / "wyrmthalak_hard_mode.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_wyrmthalak_hard_mode_blackrock_spire.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_spire"

SLICE = range(210290, 210340)
(WARD, HORN, POISON, ROAR, ROAR_HIT, SPEAR_THROW, SPEAR_IMPACT, SPEAR_CHAIN, SPEAR_CHAIN_HIT, SPIT, SPIT_MISSILE,
 SPIT_LANDING, SPIT_PATCH, AXE_CHAIN_HIT, HAUL, RABIES, RABID_BITE) = range(210290, 210307)
WAR_HORN_GO = 301255

SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT = 2, 6, 3
AURA_DUMMY, AURA_PERIODIC_DAMAGE, AURA_PROC_TRIGGER_SPELL, AURA_MOD_DAMAGE_PERCENT_TAKEN = 4, 3, 42, 87
SCHOOL_PHYSICAL, SCHOOL_NATURE, SCHOOL_SHADOW = 1, 8, 32       # school masks
DISPEL_DISEASE, DISPEL_POISON = 3, 4
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT_PERIODIC = "spell_dungeon_refflat_periodic"
ROAR_SCRIPT = "spell_brs_wyrmthalak_caustic_roar"
TARGET_DEST_DEST = 87
ATTR1_IS_CHANNELED = 0x4
PROC_DONE_MELEE_AUTO_ATTACK = 0x4
SV_HORN_BLOWN = 90602
SV_HARPOON_CHAIN = 10920
SV_SPEAR_THROW = 11993


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


def _raw(spell: dict, column: str) -> float:
    return float((spell.get("raw_overrides") or {}).get(column, 0) or 0)


def _header() -> str:
    return HEADER.read_text(encoding="utf-8")


def _header_value(name: str) -> float:
    match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f?;", _header())
    assert match, name
    return float(match.group(1))


def _value(effect: dict) -> int:
    """The DBC value of an effect: base points plus the die (1 when die_sides is 1, as the kit's percent spells)."""
    return int(effect["base_points"]) + (1 if int(effect.get("die_sides", 0) or 0) == 1 else 0)


class WarHornDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.procs = {int(e["SpellId"]): e for e in reg.spell_procs if int(e["SpellId"]) in SLICE}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(WARD, RABID_BITE + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_spire", {"spell": mine}), [])
        bounds = re.search(r"kSpellsWarHorn\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(bounds)
        self.assertEqual((int(bounds.group(1)), int(bounds.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_WH_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))

    def test_the_hits_are_resolve_copies(self):
        for sid, school in ((ROAR_HIT, SCHOOL_NATURE), (SPEAR_IMPACT, SCHOOL_PHYSICAL),
                            (SPEAR_CHAIN_HIT, SCHOOL_PHYSICAL), (SPIT, SCHOOL_SHADOW), (SPIT_PATCH, SCHOOL_SHADOW),
                            (AXE_CHAIN_HIT, SCHOOL_PHYSICAL), (HAUL, SCHOOL_PHYSICAL)):
            with self.subTest(sid=sid):
                self.assertIn((sid, RESOLVE), self.scripts)
                self.assertEqual(int(self.spells[sid]["school"]), school)
                self.assertEqual(int(self.spells[sid]["effect1"]["type"]), SCHOOL_DAMAGE)

    def test_tribal_ward(self):
        ward = self.spells[WARD]
        self.assertEqual(int(ward["effect1"]["apply_aura"]), AURA_MOD_DAMAGE_PERCENT_TAKEN)
        self.assertEqual(int(ward["effect1"]["base_points"]), int(_header_value("kTribalWardPctPerChampion")))
        self.assertEqual(int(ward["effect1"]["misc_value"]), 127)
        self.assertEqual(_raw(ward, "CumulativeAura"), _header_value("kTribalWardMaxStacks"))
        self.assertEqual(int(ward["duration_ms"]), -1)

    def test_the_periodic_debuffs(self):
        for sid, prefix, dispel in ((POISON, "kPoison", DISPEL_POISON), (RABIES, "kRabies", DISPEL_DISEASE)):
            with self.subTest(sid=sid):
                spell = self.spells[sid]
                self.assertIn((sid, REFFLAT_PERIODIC), self.scripts)
                effect = spell["effect1"]
                self.assertEqual(int(effect["apply_aura"]), AURA_PERIODIC_DAMAGE)
                per_stack = int(_header_value(f"{prefix}HundredthsPerStack"))
                self.assertEqual(_value(effect), per_stack)
                self.assertEqual(_raw(spell, "EffectMiscValueB_1"), per_stack)
                self.assertEqual(int(effect["amplitude"]), int(_header_value(f"{prefix}TickMs")))
                self.assertEqual(_raw(spell, "CumulativeAura"), _header_value(f"{prefix}MaxStacks"))
                self.assertEqual(int(spell["duration_ms"]), int(_header_value(f"{prefix}Ms")))
                self.assertEqual(int(spell["dispel"]), dispel)
                self.assertEqual(int(spell["school"]), SCHOOL_NATURE)

    def test_the_riders_bite(self):
        bite = self.spells[RABID_BITE]
        self.assertEqual(int(bite["effect1"]["apply_aura"]), AURA_PROC_TRIGGER_SPELL)
        self.assertEqual(int(bite["effect1"]["trigger_spell"]), RABIES)
        self.assertEqual(int(bite["duration_ms"]), -1)
        proc = self.procs[RABID_BITE]
        self.assertEqual(int(proc["ProcFlags"]), PROC_DONE_MELEE_AUTO_ATTACK)
        self.assertEqual(float(proc["Chance"]), 100.0)
        self.assertEqual(_raw(bite, "ProcTypeMask"), PROC_DONE_MELEE_AUTO_ATTACK)
        self.assertEqual(sorted(self.procs), [RABID_BITE])

    def test_caustic_roar(self):
        roar = self.spells[ROAR]
        self.assertEqual(int(roar["cast_time_ms"]), int(_header_value("kRoarCastMs")))
        self.assertEqual(int(roar["school"]), SCHOOL_NATURE)
        self.assertEqual(_raw(roar, "InterruptFlags"), 15)
        self.assertEqual(_raw(roar, "PreventionType"), 1)
        self.assertIn((ROAR, ROAR_SCRIPT), self.scripts)
        self.assertIn(f"RegisterSpellScript({ROAR_SCRIPT});", self.cpp)

    def test_the_spear(self):
        throw = self.spells[SPEAR_THROW]
        self.assertEqual(_raw(throw, "Speed"), _header_value("kSpearMissileSpeed"))
        self.assertEqual(_raw(throw, "SpellVisualID_1"), SV_SPEAR_THROW)
        chain = self.spells[SPEAR_CHAIN]
        self.assertEqual(int(chain["duration_ms"]), int(_header_value("kSpearChainMs")))
        self.assertEqual(int(chain["effect1"]["apply_aura"]), AURA_DUMMY)
        self.assertTrue(int(_raw(chain, "AttributesEx")) & ATTR1_IS_CHANNELED)
        self.assertEqual(_raw(chain, "ChannelInterruptFlags"), 0)
        self.assertEqual(_raw(chain, "SpellVisualID_1"), SV_HARPOON_CHAIN)

    def test_the_spit_and_the_horn_looks(self):
        missile = self.spells[SPIT_MISSILE]
        self.assertEqual(int(missile["effect1"]["implicit_target_a"]), TARGET_DEST_DEST)
        self.assertEqual(_raw(missile, "Speed"), _header_value("kSpitMissileSpeed"))
        self.assertEqual(int(self.spells[SPIT_LANDING]["effect1"]["implicit_target_a"]), TARGET_DEST_DEST)
        self.assertEqual(_raw(self.spells[HORN], "SpellVisualID_1"), SV_HORN_BLOWN)
        # V-1: Shadow Flame 22992's SV 6719 is a mouth stream with no ground: never the spit's look.
        for sid in self.spells:
            self.assertNotEqual(_raw(self.spells[sid], "SpellVisualID_1"), 6719, sid)

    def test_the_horn_object_and_its_spawn(self):
        sql = SQL.read_text(encoding="utf-8")
        template = re.search(r"\(301255, (\d+), (\d+), 'Bloodaxe War Horn', '', '', '', ([\d.]+),", sql)
        self.assertIsNotNone(template)
        self.assertEqual(int(template.group(1)), 10)             # a goober
        self.assertEqual(int(template.group(2)), 7352)           # V-1's display
        self.assertEqual(float(template.group(3)), 0.12)
        self.assertIn("'go_brs_war_horn', 0)", sql)
        spawn = re.search(r"\(3012550, 301255, 229, 0, 0, (\d+), 1, (-?[\d.]+), (-?[\d.]+), (-?[\d.]+),", sql)
        self.assertIsNotNone(spawn)
        self.assertEqual(int(spawn.group(1)), 2)                 # heroic only
        spot = re.search(r"kWarHornSpot\{\s*(-?[\d.]+)f,\s*(-?[\d.]+)f,\s*(-?[\d.]+)f\s*\}",
                         REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(spot)
        self.assertEqual(tuple(float(spawn.group(i)) for i in (2, 3, 4)),
                         tuple(float(spot.group(i)) for i in (1, 2, 3)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_spire", {"gameobject": [WAR_HORN_GO]}), [])

    def test_the_scripts_are_registered(self):
        self.assertIn("RegisterDungeonReworkGameObjectAI(go_brs_war_horn,", self.cpp)
        self.assertIn("RegisterWyrmthalakHardMode(", self.cpp)
        self.assertIn('BrsTest::RegisterBoss(kLogKey,', self.cpp)
        self.assertIn('char const* const kLogKey = "warhorn";', self.cpp)


if __name__ == "__main__":
    unittest.main()
