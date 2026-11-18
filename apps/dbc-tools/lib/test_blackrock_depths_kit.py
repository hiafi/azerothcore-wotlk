"""
Blackrock Depths build WP-S0, the data skeleton: source/npcs/blackrock_depths/ against the Blackrock Depths skeleton's
C++ (modules/mod-dungeon-bosses src/BlackrockDepths/BlackrockDepthsRework.h and the boss files).

Checks:
  - the wave switch agrees on both sides (BIND_WAVE_2 in _common.py, kWave2Bound in BlackrockDepthsRework.h);
  - each reworked boss entry S0 binds is bound by a creature_template_columns() edit to a script name that a
    src/BlackrockDepths/*.cpp registers (RegisterDungeonReworkCreatureAI), with SmartAI off, immunity 1972 (Incendius
    and Bael'Gar 1973), INSTANCE_BIND and the stock DamageModifier; a wave 2 boss is not edited while its wave is
    unbound;
  - its normal HealthModifier times its class base (level, unit_class; creature_classlevelstats basehp0) is the build
    spec's normal health at 5 players (handoff s3.6; the Seven keep their stock values until D21 sizes the pool);
  - the Ring's units (Grimstone, the six champions) follow the WPs' own switches (BrdRingOfLaw::kBound,
    BrdRingChampions::kBound, read from RingOfLawLogic.h / RingChampionsLogic.h): bound (script name, SmartAI off,
    INSTANCE_BIND on a champion) while the switch is true, untouched while it is false; their scripts register only
    behind those switches;
  - a wave 2 script registers its AI only behind kWave2Bound (an unbound registered name logs "not assigned"), and
    every script registered behind it is a boss of the table or a listed add;
  - INSTANCE_BIND rides only on the units that carry an encounter credit (handoff section 10, 2026-11-17): Ribbly,
    Plugger, Moira, the High Priestess and the Seven's six non-credit ghosts hold none, and Ribbly keeps his stock
    immunity -251;
  - BlackrockDepthsRework.h's spell slices tile the `blackrock_depths` spell reservation, and its new creature,
    gameobject and item ids sit in the reservation's blocks, wave 1 creatures below wave 2's.

Only the skeleton's columns are looked at: the boss WPs add their own declarations to the same package.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_kit.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockDepths"
HEADER = MODULE_DIR / "BlackrockDepthsRework.h"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_depths"

IMMUNITY_BOSS_STUN = 1972
IMMUNITY_FIRE_GIANT = 1973
INSTANCE_BIND = 0x1
FIRE_GIANTS = {9017, 9016}

# entry: (script name, normal health at 5 players or None (stock), level, class base basehp0 at that level and
# unit_class, wave, stock DamageModifier (base SQL); live 2026-11-17). The Seven: every ghost carries the pool's normal
# 320k (D21: the shared pool, mirrored per ghost; heroic 450k).
BOSSES = {
    9018: ("boss_high_interrogator_gerstahn_rework", 140_000, 52, 1897, 1, 3.5),
    9025: ("boss_lord_roccor_rework", 110_000, 51, 2292, 1, 3.5),
    9319: ("boss_houndmaster_grebmar_rework", 95_000, 52, 2371, 1, 3.5),
    9024: ("boss_pyromancer_loregrain_rework", 130_000, 52, 1660, 1, 3.5),
    9041: ("boss_warder_stilgiss_rework", 110_000, 54, 2026, 1, 3.5),
    9042: ("npc_verek_rework", 50_000, 53, 2453, 1, 3.5),
    9476: ("boss_watchman_doomgrip_rework", 110_000, 54, 2026, 1, 7.5),
    9056: ("npc_fineous_darkvire_rework", 50_000, 53, 1962, 1, 3.5),
    9017: ("boss_lord_incendius_rework", 100_000, 53, 2453, 1, 3.5),
    9016: ("boss_baelgar_rework", 200_000, 52, 2371, 1, 3.5),
    9033: ("boss_general_angerforge_rework", 150_000, 55, 2614, 2, 3.5),
    8983: ("boss_golem_lord_argelmach_rework", 150_000, 55, 2091, 2, 3.5),
    9537: ("boss_hurley_blackbreath_rework", 140_000, 55, 2614, 2, 7.5),
    9502: ("npc_phalanx_rework", 160_000, 55, 2614, 2, 3.5),
    9156: ("boss_ambassador_flamelash_rework", 150_000, 55, 2614, 2, 3.5),
    9034: ("boss_the_seven_rework", 320_000, 55, 2091, 2, 3.5),
    9035: ("boss_the_seven_rework", 320_000, 55, 2614, 2, 3.5),
    9036: ("boss_the_seven_rework", 320_000, 56, 2159, 2, 3.5),
    9037: ("boss_the_seven_rework", 320_000, 56, 2699, 2, 3.5),
    9038: ("boss_the_seven_rework", 320_000, 56, 2159, 2, 3.5),
    9039: ("boss_the_seven_rework", 320_000, 56, 2159, 2, 3.5),
    9040: ("boss_the_seven_rework", 320_000, 56, 2699, 2, 3.5),
    9938: ("boss_magmus_rework", 170_000, 56, 2699, 2, 3.5),
    9019: ("boss_emperor_dagran_thaurissan_rework", 160_000, 56, 2699, 2, 3.5),
    8929: ("boss_moira_bronzebeard_rework", 50_000, 55, 1830, 2, 3.5),
    10076: ("boss_moira_bronzebeard_rework", 50_000, 55, 1830, 2, 7.5),
}

# The Ring's units S0 leaves to D4 / D5 (entry: (script, the switch its registration hides behind)).
RING_UNITS = {
    10096: ("npc_grimstone_rework", "BrdRingOfLaw::kBound"),
    9027: ("boss_gorosh_the_dervish_rework", "BrdRingChampions::kBound"),
    9028: ("boss_grizzle_rework", "BrdRingChampions::kBound"),
    9029: ("boss_eviscerator_rework", "BrdRingChampions::kBound"),
    9030: ("boss_okthor_rework", "BrdRingChampions::kBound"),
    9031: ("boss_anubshiah_rework", "BrdRingChampions::kBound"),
    9032: ("boss_hedrum_rework", "BrdRingChampions::kBound"),
}
# The header holding each switch's `inline constexpr bool kBound = ...;`
RING_SWITCH_HEADERS = {"BrdRingOfLaw::kBound": "RingOfLawLogic.h", "BrdRingChampions::kBound": "RingChampionsLogic.h"}

# Wave 2 adds whose scripts register with their boss (behind kWave2Bound); each one's WP binds its own template.
WAVE_2_ADDS = {
    "npc_blackbreath_crony_rework",  # Hurley's Cronies (D18)
    "npc_brd_lager_keg",  # Hurley's keg
    "npc_burning_spirit_rework",  # Flamelash's spirits (D20)
    "npc_brd_portal_anchor_rework",  # Flamelash's anchor
    "npc_ironhand_guardian_rework",  # Magmus's statues (D22)
    "npc_brd_squad_officer",  # Angerforge's squad (D14); the Reservist runs the stock SmartAI copy
    "npc_brd_squad_medic",
    "npc_brd_rowdy_patron",  # Phalanx's heroic patrons (D19)
    "npc_brd_imperial_guard",  # the Emperor's guards and Ambassadors (D23)
    "npc_brd_twilight_ambassador",
}

# Units that carry no encounter credit and so no INSTANCE_BIND (handoff section 10, the orchestrator rulings of
# 2026-11-17; Anger'rel 9035 carries the Seven's credit, instance_encounters 243; row 233 credits Stilgiss' pair by
# spell; the Ring's credit 230 is Grimstone's): Moira, the High Priestess, the Seven's six other ghosts, Verek,
# Fineous, Doomgrip. The Ring champions and Theldren (RING_NO_BIND) are checked by the Ring tests; Ribbly and Plugger
# (GUZZLER_NO_BIND) are the Guzzler file's raw column dict.
NO_INSTANCE_BIND = {8929, 10076, 9034, 9036, 9037, 9038, 9039, 9040, 9042, 9056, 9476}
RING_NO_BIND = {9027, 9028, 9029, 9030, 9031, 9032, 16059}
ENCORE_NO_BIND = {16049, 16052, 16053, 16058}  # the Encore's other four (R-2-FW MIN-2: the heroic test checks the rows)
GUZZLER_NO_BIND = {9543, 9499}
RIBBLY_STOCK_IMMUNITY = -251


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


def _ring_switch(switch: str) -> bool:
    """`inline constexpr bool kBound = true;` of the header that declares `switch`."""
    text = (MODULE_DIR / RING_SWITCH_HEADERS[switch]).read_text(encoding="utf-8")
    found = re.findall(r"constexpr bool kBound = (true|false);", text)
    assert len(found) == 1, (switch, found)
    return found[0] == "true"


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


class BlackrockDepthsSkeletonTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load()
        cls.edits = {int(r["entry"]): r for r in cls.reg.creature_template_edits}
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
                want_immunity = IMMUNITY_FIRE_GIANT if entry in FIRE_GIANTS else IMMUNITY_BOSS_STUN
                self.assertEqual(row["CreatureImmunitiesId"], want_immunity)
                self.assertEqual(row["flags_extra"], 0 if entry in NO_INSTANCE_BIND else INSTANCE_BIND,
                                 "INSTANCE_BIND only on a unit that carries an encounter credit")
                self.assertEqual(float(row["DamageModifier"]), damage)

    def test_normal_health_is_the_build_spec(self):
        for entry, (_script, health, _level, base, _wave, _damage) in BOSSES.items():
            if not _bound(entry) or health is None:
                continue
            with self.subTest(entry=entry):
                got = float(self.edits[entry]["HealthModifier"]) * base
                self.assertLessEqual(abs(got - health), 2, f"{got:.0f} vs {health}")

    def test_wave_1_declares_no_wave_2_entry(self):
        if _dt_switch():
            self.skipTest("wave 2 is bound")
        wave2 = {entry for entry, row in BOSSES.items() if row[4] == 2}
        self.assertFalse(wave2 & set(self.edits))

    def test_the_ring_follows_its_wps_switches(self):
        for entry, (script, switch) in RING_UNITS.items():
            with self.subTest(entry=entry):
                self.assertIn(script, self.scripts)
                self.assertEqual(self.gated.get(script), switch, "registers only behind the WP's switch")
                row = self.edits.get(entry)
                if not _ring_switch(switch):
                    self.assertIsNone(row, "unbound until D4 / D5 flip the switch")
                    continue
                self.assertIsNotNone(row, "the switch is on: the WP binds the unit")
                self.assertEqual(row["ScriptName"], script)
                self.assertEqual(row["AIName"], "", "SmartAI off")
                if entry != 10096:  # Grimstone keeps his stock row; the champions are boss-tier rows
                    self.assertEqual(row["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
                    self.assertEqual(row["flags_extra"], 0, "no encounter credit: no INSTANCE_BIND")

    def test_the_guzzler_units_hold_no_instance_bind_and_ribbly_keeps_his_stock_immunity(self):
        if not _dt_switch():
            self.skipTest("wave 2 is not bound: the Guzzler rows are not declared")
        for entry in GUZZLER_NO_BIND:
            with self.subTest(entry=entry):
                self.assertEqual(self.edits[entry].get("flags_extra", 0) & INSTANCE_BIND, 0,
                                 "no encounter credit: no INSTANCE_BIND")
        self.assertIn(self.edits[9543].get("CreatureImmunitiesId", RIBBLY_STOCK_IMMUNITY), (RIBBLY_STOCK_IMMUNITY,),
                      "Ribbly keeps the stock -251, not 1972 (a non-boss: the spec's text)")

    def test_the_no_bind_set_of_the_common_file_matches_the_rows_checked_here(self):
        text = (PACKAGE / "_common.py").read_text(encoding="utf-8")
        found = re.search(r"^NO_INSTANCE_BIND = frozenset\(\{([^}]*)\}\)", text, re.M)
        self.assertIsNotNone(found)
        body = re.sub(r"#[^\n]*", "", found.group(1))
        self.assertEqual({int(v) for v in re.findall(r"\d+", body)},
                         NO_INSTANCE_BIND | GUZZLER_NO_BIND | RING_NO_BIND | ENCORE_NO_BIND)

    def test_wave_2_scripts_register_only_when_bound(self):
        for entry, (script, _health, _level, _base, wave, _damage) in BOSSES.items():
            with self.subTest(entry=entry):
                if wave == 2:
                    self.assertEqual(self.gated.get(script), "kWave2Bound")
                else:
                    self.assertNotIn(script, self.gated, "wave 1 registers always")
        for script in WAVE_2_ADDS:
            self.assertEqual(self.gated.get(script), "kWave2Bound", script)
        # no script hides behind the switch without being a table boss or a listed add
        known = {row[0] for row in BOSSES.values()} | WAVE_2_ADDS
        self.assertEqual(sorted(s for s, switch in self.gated.items() if switch == "kWave2Bound" and s not in known),
                         [])

    def test_slices_tile_the_reservation(self):
        spell = id_blocks.RESERVATIONS["blackrock_depths"]["spell"]
        found = re.findall(r"IdSlice constexpr kSpells\w+\{ (\d+), (\d+) \}", HEADER.read_text())
        slices = sorted((int(a), int(b)) for a, b in found)
        reservation = next(s for s in slices if s == (spell["start"], spell["end"]))
        parts = [s for s in slices if s != reservation]
        self.assertEqual(parts[0][0], spell["start"])
        self.assertEqual(parts[-1][1], spell["end"])
        for (_a0, a1), (b0, _b1) in zip(parts, parts[1:]):
            self.assertEqual(b0, a1 + 1)

    def test_new_ids_sit_in_the_reservation(self):
        res = id_blocks.RESERVATIONS["blackrock_depths"]
        creatures = _header_ints(r"NPC_BRD_\w+\s*=\s*(\d+)")
        gameobjects = _header_ints(r"GO_BRD_\w+\s*=\s*(\d+)")
        items = _header_ints(r"kItem(?:VaultTreasureBag|CinderOfTheFirelord|GuzzlerRope) = (\d+);")
        self.assertEqual(len(creatures), 33)
        self.assertEqual(len(gameobjects), 10)
        self.assertEqual(sorted(items), [70620, 70621, 70622])
        for value in creatures:
            self.assertTrue(res["creature"]["start"] <= value <= res["creature"]["end"], value)
        for value in gameobjects:
            self.assertTrue(res["gameobject"]["start"] <= value <= res["gameobject"]["end"], value)
        for value in items:
            self.assertTrue(res["item"]["start"] <= value <= res["item"]["end"], value)
        # The heroic mint order: every wave 1 add below every wave 2 add.
        self.assertLess(max(v for v in creatures if v < 300830), min(v for v in creatures if v >= 300830))


if __name__ == "__main__":
    unittest.main()
