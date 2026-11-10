"""
Stratholme build WP-S0, the data skeleton: source/npcs/stratholme/ against the Stratholme skeleton's C++
(modules/mod-dungeon-bosses src/Stratholme/StratholmeRework.h and the boss files).

Checks:
  - the wave switch agrees on both sides (BIND_WAVE_2 in _common.py, kWave2Bound in StratholmeRework.h);
  - each of the fourteen reworked boss entries is bound by a creature_template_columns() edit to a script name that a
    src/Stratholme/*.cpp registers (RegisterDungeonReworkCreatureAI), with SmartAI off, stun immunity 1972 (the Baron
    keeps -419), INSTANCE_BIND (Maleki keeps his stock 0x4000000 too) and a DamageModifier; a wave 2 boss is not
    edited while its wave is unbound;
  - its normal HealthModifier times its class base (level, unit_class; creature_classlevelstats basehp0) is the build
    spec's normal health (handoff s3.6);
  - StratholmeRework.h's spell slices tile the `stratholme` spell reservation, and its new creature and gameobject ids
    sit in the reservation's blocks, wave 1 creatures below wave 2's;
  - the lethal walls' strike 206400 is an outright kill (INSTAKILL, NO_IMMUNITIES, spell_dungeon_lethal_strike).

Only the skeleton's columns are looked at: the boss WPs add their own declarations to the same package.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_stratholme_kit.py
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
HEADER = MODULE_DIR / "StratholmeRework.h"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "stratholme"

IMMUNITY_BOSS_STUN = 1972
IMMUNITY_BARON_STOCK = -419
INSTANCE_BIND = 0x1
MALEKI_STOCK_FLAGS = 0x4000000
CROSSED_THE_LINE = 206400           # the lethal walls' strike (shared.py)
SPELL_EFFECT_INSTAKILL = 1
ATTR0_NO_IMMUNITIES = 0x20000000

# entry: (script name, normal health, level, class base basehp0 at that level and unit_class, wave; live 2026-11-09)
BOSSES = {
    10435: ("boss_magistrate_barthilas_rework", 180_000, 58, 2871, 1),
    10436: ("boss_baroness_anastari_rework", 170_000, 59, 2369, 1),
    10437: ("boss_nerubenkan_rework", 170_000, 60, 3052, 1),
    10438: ("boss_maleki_the_pallid_rework", 170_000, 61, 2201, 1),
    10439: ("boss_ramstein_the_gorger_rework", 210_000, 61, 3144, 1),
    10440: ("boss_baron_rivendare_rework", 250_000, 62, 2590, 1),
    10516: ("boss_the_unforgiven_rework", 185_000, 57, 2784, 2),
    10558: ("boss_hearthsinger_forresten_rework", 175_000, 57, 2784, 2),
    10808: ("boss_timmy_the_cruel_rework", 170_000, 58, 2871, 2),
    11032: ("boss_malor_the_zealous_rework", 175_000, 60, 2442, 2),
    10997: ("boss_cannon_master_willey_rework", 185_000, 60, 3052, 2),
    10811: ("boss_archivist_galford_rework", 170_000, 60, 2442, 2),
    10812: ("boss_dathrohan_balnazzar_rework", 250_000, 62, 2590, 2),
    10813: ("boss_dathrohan_balnazzar_rework", 220_000, 62, 2590, 2),
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


def _header_ints(pattern: str) -> list[int]:
    return [int(v) for v in re.findall(pattern, HEADER.read_text())]


class StratholmeSkeletonTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load()
        cls.edits = {int(r["entry"]): r for r in cls.reg.creature_template_edits}
        cls.scripts = _registered_scripts()

    def test_the_wave_switch_agrees(self):
        self.assertEqual(_dt_switch(), _cpp_switch())

    def test_every_boss_is_bound(self):
        for entry, (script, _health, _level, _base, _wave) in BOSSES.items():
            with self.subTest(entry=entry):
                self.assertIn(script, self.scripts, "no C++ registers this name")
                row = self.edits.get(entry)
                if not _bound(entry):
                    self.assertIsNone(row, "a wave 2 boss stays stock until its wave")
                    continue
                self.assertIsNotNone(row, "no creature_template_columns() edit")
                self.assertEqual(row["ScriptName"], script)
                self.assertEqual(row["AIName"], "")
                want_immunity = IMMUNITY_BARON_STOCK if entry == 10440 else IMMUNITY_BOSS_STUN
                self.assertEqual(row["CreatureImmunitiesId"], want_immunity)
                want_flags = INSTANCE_BIND | (MALEKI_STOCK_FLAGS if entry == 10438 else 0)
                self.assertEqual(row["flags_extra"], want_flags)
                self.assertGreater(float(row["DamageModifier"]), 0)

    def test_normal_health_is_the_build_spec(self):
        for entry, (_script, health, _level, base, _wave) in BOSSES.items():
            if not _bound(entry):
                continue
            with self.subTest(entry=entry):
                got = float(self.edits[entry]["HealthModifier"]) * base
                self.assertLessEqual(abs(got - health), 2, f"{got:.0f} vs {health}")

    def test_wave_1_declares_no_wave_2_entry(self):
        if _dt_switch():
            self.skipTest("wave 2 is bound")
        wave2 = {entry for entry, row in BOSSES.items() if row[4] == 2}
        self.assertFalse(wave2 & set(self.edits))

    def test_the_lethal_strike_is_an_outright_kill(self):
        # User ruling (F-2): the walls' strike 206400 is SPELL_EFFECT_INSTAKILL (no absorb or reduction applies), not
        # damage, with NO_IMMUNITIES, and bound to the kit's spell_dungeon_lethal_strike (it kills a survivor).
        spell = next(e for e in self.reg.spells if int(e["id"]) == CROSSED_THE_LINE)
        self.assertEqual(spell["effect1"]["type"], SPELL_EFFECT_INSTAKILL)
        self.assertIsNone(spell["effect2"])
        self.assertIsNone(spell["effect3"])
        self.assertTrue(int(spell["attributes"]) & ATTR0_NO_IMMUNITIES)
        bound = {e["ScriptName"] for e in self.reg.spell_script_names if int(e["spell_id"]) == CROSSED_THE_LINE}
        self.assertEqual(bound, {"spell_dungeon_lethal_strike"})

    def test_slices_tile_the_reservation(self):
        spell = id_blocks.RESERVATIONS["stratholme"]["spell"]
        found = re.findall(r"IdSlice constexpr kSpells\w+\{ (\d+), (\d+) \}", HEADER.read_text())
        slices = sorted((int(a), int(b)) for a, b in found)
        reservation = next(s for s in slices if s == (spell["start"], spell["end"]))
        parts = [s for s in slices if s != reservation]
        self.assertEqual(parts[0][0], spell["start"])
        self.assertEqual(parts[-1][1], spell["end"])
        for (a0, a1), (b0, _b1) in zip(parts, parts[1:]):
            self.assertEqual(b0, a1 + 1)

    def test_new_ids_sit_in_the_reservation(self):
        res = id_blocks.RESERVATIONS["stratholme"]
        creatures = _header_ints(r"NPC_ST_\w+\s*=\s*(\d+)")
        gameobjects = _header_ints(r"GO_ST_\w+\s*=\s*(\d+)")
        self.assertEqual(len(creatures), 20)
        self.assertEqual(len(gameobjects), 8)
        for value in creatures:
            self.assertTrue(res["creature"]["start"] <= value <= res["creature"]["end"], value)
        for value in gameobjects:
            self.assertTrue(res["gameobject"]["start"] <= value <= res["gameobject"]["end"], value)
        # The heroic mint order (Scholomance R-A N-2): every wave 1 add below every wave 2 add.
        self.assertLess(max(v for v in creatures if v < 300600), min(v for v in creatures if v >= 300600))
        self.assertTrue(all(v <= 300599 or v >= 300600 for v in creatures))


if __name__ == "__main__":
    unittest.main()
