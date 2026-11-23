"""
Scarlet Monastery build WP-S0, the data skeleton: source/npcs/scarlet_monastery/ against the Scarlet Monastery
skeleton's C++ (modules/mod-dungeon-bosses src/ScarletMonastery/ScarletMonasteryRework.h and the boss files).

Checks:
  - the wave switch agrees on both sides (BIND_WAVE_2 in _common.py, kWave2Bound in ScarletMonasteryRework.h);
  - each stock boss S0 binds is bound by a creature_template_columns() edit to a script name that a
    src/ScarletMonastery/*.cpp registers (RegisterDungeonReworkCreatureAI), with SmartAI off, immunity 1972,
    INSTANCE_BIND only on a credit carrier (not the council's pair, not Mograine) and the stock DamageModifier; a wave
    2 boss is not edited while its wave is unbound;
  - its normal HealthModifier times its class base (level, unit_class; creature_classlevelstats basehp0) is the build
    spec's normal health at 5 players (handoff s3.6);
  - the new bosses (Kell, Hollis Grey) register only behind their WPs' own switches (SmKell::kBound,
    SmHollisGrey::kBound) and every wave 2 script only behind kWave2Bound;
  - the credit spells 212300 / 212301 are declared, agree with the header and sit in the shared slice;
  - the header's spell slices tile the `scarlet_monastery` spell reservation, and its new creature and gameobject ids
    sit in the reservation's blocks, wave 1 creatures below wave 2's.

Only the skeleton's columns are looked at: the boss WPs add their own declarations to the same package.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scarlet_monastery_kit.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "ScarletMonastery"
HEADER = MODULE_DIR / "ScarletMonasteryRework.h"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "scarlet_monastery"

IMMUNITY_BOSS_STUN = 1972
INSTANCE_BIND = 0x1

# entry: (script name, normal health at 5 players, level, class base basehp0 at that level and the bound unit_class,
# wave, stock DamageModifier (base SQL); live 2026-11-20). The Fallen Champion's class becomes paladin (s3.5 row D3).
BOSSES = {
    3983: ("boss_interrogator_vishas_rework", 40_000, 32, 888, 1, 2.0),
    6489: ("boss_ironspine_rework", 36_000, 32, 1057, 1, 2.4),
    6488: ("boss_fallen_champion_rework", 24_000, 32, 888, 1, 2.4),
    6490: ("boss_azshir_the_sleepless_rework", 18_000, 32, 888, 1, 7.5),
    4543: ("boss_bloodmage_thalnos_rework", 48_000, 32, 888, 1, 1.7),
    3974: ("boss_houndmaster_loksey_rework", 38_000, 34, 967, 1, 2.4),
    6487: ("boss_arcanist_doan_rework", 46_000, 35, 902, 1, 2.4),
    3975: ("boss_herod_rework", 66_000, 37, 1336, 2, 3.8),
    3976: ("boss_mograine_rework", 55_000, 40, 1226, 2, 2.6),
    3977: ("boss_whitemane_rework", 50_000, 40, 1226, 2, 2.2),
}

# Units with no credit of their own: the council (a spell credit once both are dead) and Mograine (the Last Stand's
# spell credit at his fall).
NO_INSTANCE_BIND = {6490, 6488, 3976}

# New bosses: their WPs declare the creature; the stub registers behind the WP's own switch (wave 1) or kWave2Bound.
NEW_BOSSES = {
    "boss_ambrose_kell_rework": ("SmKell::kBound", "KellLogic.h"),
    "boss_lector_hollis_grey_rework": ("SmHollisGrey::kBound", "HollisGreyLogic.h"),
    "boss_forgemaster_gideon_crell_rework": ("kWave2Bound", None),
    "boss_drillmaster_corin_halden_rework": ("kWave2Bound", None),
    "boss_gardener_rework": ("kWave2Bound", None),
}


def _dt_switch() -> bool:
    text = (PACKAGE / "_common.py").read_text(encoding="utf-8")
    found = re.findall(r"^BIND_WAVE_2\s*=\s*(True|False)\s*$", text, re.M)
    assert len(found) == 1, found
    return found[0] == "True"


def _cpp_switch() -> bool:
    found = re.findall(r"constexpr bool kWave2Bound = (true|false);", HEADER.read_text())
    assert len(found) == 1, found
    return found[0] == "true"


def _bound(entry: int) -> bool:
    return BOSSES[entry][4] == 1 or _dt_switch()


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


def _registered_scripts() -> set[str]:
    names = set()
    for path in MODULE_DIR.glob("*.cpp"):
        names.update(re.findall(r"RegisterDungeonReworkCreatureAI\((\w+),", path.read_text()))
    return names


def _gated_scripts() -> dict[str, str]:
    """Script name -> the switch its registration hides behind."""
    gated = {}
    for path in MODULE_DIR.glob("*.cpp"):
        for switch, name in re.findall(r"if \(([\w:]+)\)\s*RegisterDungeonReworkCreatureAI\((\w+),",
                                       path.read_text()):
            gated[name] = switch
    return gated


def _header_ints(pattern: str) -> list[int]:
    return [int(v) for v in re.findall(pattern, HEADER.read_text())]


class ScarletMonasterySkeletonTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load()
        cls.edits = {int(r["entry"]): r for r in cls.reg.creature_template_edits}
        cls.spells = {int(s["id"]): s for s in cls.reg.spells}
        cls.scripts = _registered_scripts()
        cls.gated = _gated_scripts()

    def test_the_wave_switch_agrees(self):
        self.assertEqual(_dt_switch(), _cpp_switch())

    def test_every_boss_is_bound(self):
        for entry, (script, _health, _level, _base, _wave, damage) in BOSSES.items():
            with self.subTest(entry=entry):
                self.assertIn(script, self.scripts, "no C++ registers this name")
                row = self.edits.get(entry)
                if not _bound(entry):
                    self.assertIsNone(row, "a wave 2 boss stays stock until its wave")
                    continue
                self.assertIsNotNone(row, "no creature_template_columns() edit")
                self.assertEqual(row["ScriptName"], script)
                self.assertEqual(row["AIName"], "")
                self.assertEqual(row["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
                self.assertEqual(row["flags_extra"], 0 if entry in NO_INSTANCE_BIND else INSTANCE_BIND,
                                 "INSTANCE_BIND only on a unit that carries its own encounter credit")
                self.assertEqual(float(row["DamageModifier"]), damage)

    def test_normal_health_is_the_build_spec(self):
        for entry, (_script, health, _level, base, _wave, _damage) in BOSSES.items():
            if not _bound(entry):
                continue
            with self.subTest(entry=entry):
                got = float(self.edits[entry]["HealthModifier"]) * base
                self.assertLessEqual(abs(got - health), 2, f"{got:.0f} vs {health}")

    def test_the_fallen_champion_becomes_a_paladin(self):
        self.assertEqual(int(self.edits[6488]["unit_class"]), 2, "24k = 27.027 on the paladin base 888")

    def test_wave_1_declares_no_wave_2_entry(self):
        if _dt_switch():
            self.skipTest("wave 2 is bound")
        wave2 = {entry for entry, row in BOSSES.items() if row[4] == 2}
        self.assertFalse(wave2 & set(self.edits))

    def test_the_no_bind_set_of_the_common_file_matches(self):
        text = (PACKAGE / "_common.py").read_text(encoding="utf-8")
        found = re.search(r"^NO_INSTANCE_BIND = frozenset\(\{([^}]*)\}\)", text, re.M)
        self.assertIsNotNone(found)
        body = re.sub(r"#[^\n]*", "", found.group(1))
        self.assertEqual({int(v) for v in re.findall(r"\d+", body)}, NO_INSTANCE_BIND)

    def test_scripts_register_only_behind_their_switch(self):
        for entry, (script, _health, _level, _base, wave, _damage) in BOSSES.items():
            with self.subTest(entry=entry):
                if wave == 2:
                    self.assertEqual(self.gated.get(script), "kWave2Bound")
                else:
                    self.assertNotIn(script, self.gated, "wave 1 registers always")
        for script, (switch, header) in NEW_BOSSES.items():
            with self.subTest(script=script):
                self.assertIn(script, self.scripts)
                self.assertEqual(self.gated.get(script), switch)
                if header:
                    text = (MODULE_DIR / header).read_text(encoding="utf-8")
                    found = re.findall(r"constexpr bool kBound = (true|false);", text)
                    self.assertEqual(len(found), 1, header)

    def test_the_credit_spells(self):
        common = (PACKAGE / "_common.py").read_text(encoding="utf-8")
        for name, cpp in (("SPELL_COUNCIL_CREDIT", "kSpellCouncilCredit"),
                          ("SPELL_LAST_STAND_CREDIT", "kSpellLastStandCredit")):
            with self.subTest(name=name):
                dt = int(re.search(rf"^{name} = (\d+)$", common, re.M).group(1))
                (cpp_value,) = _header_ints(rf"std::uint32_t constexpr {cpp} = (\d+);")
                self.assertEqual(dt, cpp_value)
                self.assertIn(dt, self.spells, "declared (the core drops a credit row whose spell is missing)")
                self.assertTrue(212300 <= dt <= 212319, "the shared slice")
        self.assertEqual((_header_ints(r"kSpellCouncilCredit = (\d+);")[0],
                          _header_ints(r"kSpellLastStandCredit = (\d+);")[0]), (212300, 212301))

    def test_slices_tile_the_reservation(self):
        spell = id_blocks.RESERVATIONS["scarlet_monastery"]["spell"]
        found = re.findall(r"IdSlice constexpr kSpells\w+\{ (\d+), (\d+) \}", HEADER.read_text())
        slices = sorted((int(a), int(b)) for a, b in found)
        reservation = next(s for s in slices if s == (spell["start"], spell["end"]))
        parts = [s for s in slices if s != reservation]
        self.assertEqual(parts[0][0], spell["start"])
        self.assertEqual(parts[-1][1], spell["end"])
        for (_a0, a1), (b0, _b1) in zip(parts, parts[1:]):
            self.assertEqual(b0, a1 + 1)

    def test_new_ids_sit_in_the_reservation(self):
        res = id_blocks.RESERVATIONS["scarlet_monastery"]
        creatures = _header_ints(r"NPC_SM_\w+\s*=\s*(\d+)")
        gameobjects = _header_ints(r"GO_SM_\w+\s*=\s*(\d+)")
        self.assertEqual(len(creatures), 42)
        self.assertEqual(len(gameobjects), 22)
        for value in creatures:
            self.assertTrue(res["creature"]["start"] <= value <= res["creature"]["end"], value)
        for value in gameobjects:
            self.assertTrue(res["gameobject"]["start"] <= value <= res["gameobject"]["end"], value)
        # The heroic mint order: every wave 1 creature below every wave 2 creature.
        self.assertLess(max(v for v in creatures if v < 300940), min(v for v in creatures if v >= 300940))


if __name__ == "__main__":
    unittest.main()
