"""
Gnomeregan build WP-S0, the data skeleton: source/npcs/gnomeregan/ against the Gnomeregan skeleton's C++
(modules/mod-dungeon-bosses src/Gnomeregan/GnomereganRework.h and the WPs' files), the S0 SQL rev and the checkpoint
rows.

Checks:
  - each reworked boss is bound to a script name that a src/Gnomeregan/*.cpp registers, with SmartAI off, immunity
    1972, INSTANCE_BIND with both assist flags, detection range 12, DamageModifier 1.7 and the normal health of handoff
    s3.6 (the header's Health table): the four stock bosses by a creature_template_columns() edit, the two new ones
    (Techbot 301105, the Mobile Alert System 301110) by a full creature_template() row with a model;
  - the S0 rev drops the SmartAI of exactly the four stock bosses, the faces' and the buttons' (with the faces'
    conditions), cuts Emi's event, removes the hall's two packs and patroller 30205, stops the pocket's three patrols,
    moves Fallout and Pummeler to the header's spots, spawns the new bosses, the 3005-A copy and the console at the
    header's spots, and makes the Workshop Door keyless with its script;
  - every creature and gameobject script the C++ registers is bound, and every script name bound there is registered;
  - the header's spell slices tile the `gnomeregan` spell reservation; every WP's spells sit in its file's slice; its
    new creature and gameobject ids sit in the reservation's blocks;
  - mod-dungeon-checkpoint's three rows (s7 #25 A) and the header's checkpoint points are one set of spots.

Only the skeleton's columns are looked at: the WPs add their own declarations to the same package.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_gnomeregan_npcs.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Gnomeregan"
HEADER = MODULE_DIR / "GnomereganRework.h"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "gnomeregan"
S0_REV = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_skeleton_gnomeregan.sql"
CHECKPOINT_SQL = (REPO_ROOT / "modules" / "mod-dungeon-checkpoint" / "data" / "sql" / "db-world"
                  / "u_dungeon_checkpoint_2026_11_26_00.sql")

IMMUNITY_BOSS_STUN = 1972
BOSS_FLAGS_EXTRA = 0x1 | 0x02000000 | 0x04000000
BOSS_DETECTION_RANGE = 12.0
BASE_HEALTH_28 = 853

# entry: (script name, the header's Health name); every one at DamageModifier 1.7 until T
STOCK_BOSSES = {
    7079: ("boss_viscous_fallout_rework", "kViscousFallout"),
    6235: ("boss_electrocutioner_rework", "kElectrocutioner"),
    6229: ("boss_crowd_pummeler_rework", "kCrowdPummeler"),
    7800: ("boss_thermaplugg_rework", "kThermaplugg"),
}
NEW_BOSSES = {
    301105: ("boss_techbot_rework", "kTechbot", 7288, 1.0),
    301110: ("boss_mobile_alert_system_rework", "kAlertSystem", 6888, 3.0),
}

# The spell slices (GnomereganRework.h) by the declaration file that owns them.
SLICES = {
    "instance.py": (214280, 214299),
    "techbot.py": (214300, 214339),
    "viscous_fallout.py": (214340, 214379),
    "electrocutioner.py": (214380, 214419),
    "mobile_alert_system.py": (214420, 214459),
    "crowd_pummeler.py": (214460, 214489),
    "thermaplugg.py": (214490, 214539),
    "thermaplugg_hard_mode.py": (214540, 214579),
    "thermaplugg_hard_mode_machines.py": (214580, 214619),
}
CONSOLE_SPELLS = (214620, 214639)   # D6Ha's console, in kSpellsConsoleAndSpare

HALL_PACKS = {33423, 33426, 33427, 33428, 33429, 33444, 30390, 33438, 33439, 33440, 33441, 33442, 33488, 30304, 30205}

NUM = r"(-?\d+(?:\.\d*)?)"


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


def _registered(macro: str) -> set[str]:
    names = set()
    for path in MODULE_DIR.glob("*.cpp"):
        names.update(re.findall(rf"^\s*{macro}\((\w+),", path.read_text(), re.M))
    return names


def _statements(path: Path) -> list[str]:
    text = re.sub(r"^--.*$", "", path.read_text(encoding="utf-8"), flags=re.M)
    return [" ".join(s.split()) for s in text.split(";") if s.strip()]


def _ints(text: str) -> set[int]:
    return {int(v) for v in text.split(",")}


class GnomereganSkeletonTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        registry.record_provenance()
        try:
            cls.reg = _load()
            cls.spell_files = {int(s["id"]): Path(registry.declared_in(s) or "").name for s in cls.reg.spells}
        finally:
            registry.stop_provenance()
        cls.edits = {int(r["entry"]): r for r in cls.reg.creature_template_edits}
        cls.rows = {int(r["entry"]): r for r in cls.reg.creature_templates}
        cls.creature_scripts = _registered("RegisterDungeonReworkCreatureAI")
        cls.go_scripts = _registered("RegisterDungeonReworkGameObjectAI")
        cls.rev = _statements(S0_REV)
        cls.header = HEADER.read_text()

    def _header_health(self, name: str) -> int:
        found = re.findall(rf"NH<std::uint32_t> constexpr {name}\{{ (\d+), (\d+) \}};", self.header)
        self.assertEqual(len(found), 1, name)
        return int(found[0][0])

    def _header_point(self, name: str) -> list[float]:
        found = re.findall(rf"Point3 constexpr {name}\{{ {NUM}f, {NUM}f, {NUM}f, {NUM}f \}};", self.header)
        self.assertEqual(len(found), 1, name)
        return [float(v) for v in found[0]]

    def _check_boss(self, row: dict, script: str):
        self.assertEqual(row["ScriptName"], script)
        self.assertEqual(row["AIName"], "")
        self.assertEqual(row["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
        self.assertEqual(int(row["flags_extra"]), BOSS_FLAGS_EXTRA)
        self.assertEqual(float(row["detection_range"]), BOSS_DETECTION_RANGE)
        self.assertEqual(float(row["DamageModifier"]), 1.7)

    def test_every_stock_boss_is_bound(self):
        for entry, (script, name) in STOCK_BOSSES.items():
            with self.subTest(entry=entry):
                self.assertIn(script, self.creature_scripts, "no C++ registers this name")
                row = self.edits.get(entry)
                self.assertIsNotNone(row, "no creature_template_columns() edit")
                self._check_boss(row, script)
                # the engine's rounding (CreatureData.h GenerateHealth: ceil of base x float(mod))
                self.assertEqual(math.ceil(BASE_HEALTH_28 * float(row["HealthModifier"])), self._header_health(name))

    def test_the_new_bosses_are_declared_and_bound(self):
        for entry, (script, name, display, scale) in NEW_BOSSES.items():
            with self.subTest(entry=entry):
                self.assertIn(script, self.creature_scripts)
                row = self.rows.get(entry)
                self.assertIsNotNone(row, "no creature_template() row")
                self._check_boss(row, script)
                self.assertEqual((int(row["minlevel"]), int(row["maxlevel"]), int(row["rank"])), (28, 28, 1))
                self.assertEqual(int(row["faction"]), 63)
                self.assertEqual(int(row["type"]), 9)
                self.assertEqual(int(row["MovementType"]), 0)
                self.assertEqual(math.ceil(BASE_HEALTH_28 * float(row["HealthModifier"])), self._header_health(name))
                models = [m for m in self.reg.creature_template_models if int(m["CreatureID"]) == entry]
                self.assertEqual(len(models), 1)
                self.assertEqual(int(models[0]["CreatureDisplayID"]), display)
                self.assertAlmostEqual(float(models[0]["DisplayScale"]), scale)

    def test_the_skeleton_rev_drops_the_reworked_units_smartai(self):
        found = [re.fullmatch(r"DELETE FROM `smart_scripts` WHERE `source_type` = 0 AND `entryorguid` IN \(([\d, ]+)\)",
                              s) for s in self.rev]
        found = [m for m in found if m]
        self.assertEqual(len(found), 1)
        self.assertEqual(_ints(found[0].group(1)), {7079, 6235, 6229, 7800})
        for statement in (
            "DELETE FROM `smart_scripts` WHERE `source_type` = 1 AND `entryorguid` BETWEEN 142208 AND 142219",
            "DELETE FROM `conditions` WHERE `SourceTypeOrReferenceId` = 22 AND `SourceId` = 1 AND `SourceEntry` "
            "BETWEEN 142208 AND 142219",
            "UPDATE `gameobject_template` SET `AIName` = '' WHERE `entry` BETWEEN 142208 AND 142219",
            "UPDATE `gameobject_template_addon` SET `flags` = `flags` | 16 WHERE `entry` BETWEEN 142214 AND 142219",
        ):
            self.assertIn(statement, self.rev)

    def test_emi_is_cut(self):
        for statement in (
            "DELETE FROM `creature_addon` WHERE `guid` = 30136",
            "DELETE FROM `creature` WHERE `id` = 7998 AND `guid` = 30136",
            "DELETE FROM `smart_scripts` WHERE `source_type` = 0 AND `entryorguid` = 7998",
            "DELETE FROM `creature_summon_groups` WHERE `summonerId` = 7998 AND `summonerType` = 0",
            "DELETE FROM `waypoints` WHERE `entry` = 7998",
        ):
            self.assertIn(statement, self.rev)
        # the Cave Ins are not touched
        self.assertFalse([s for s in self.rev if "146085" in s or "146086" in s])

    def test_the_hall_packs_and_the_pocket_patrols(self):
        deleted = set()
        for s in self.rev:
            m = re.fullmatch(r"DELETE FROM `creature` WHERE `id` = (\d+) AND `guid` (?:= (\d+)|IN \(([\d, ]+)\))", s)
            if m and int(m.group(1)) != 7998 and int(m.group(1)) < 300000:
                deleted |= {int(m.group(2))} if m.group(2) else _ints(m.group(3))
        self.assertEqual(deleted, HALL_PACKS)
        addons = [re.fullmatch(r"DELETE FROM `creature_addon` WHERE `guid` IN \(([\d, ]+)\)", s) for s in self.rev]
        addons = [m for m in addons if m]
        self.assertEqual(len(addons), 1)
        self.assertEqual(_ints(addons[0].group(1)), HALL_PACKS)
        self.assertIn("DELETE FROM `waypoint_data` WHERE `id` = 302050", self.rev)
        self.assertIn("UPDATE `creature_addon` SET `path_id` = 0 WHERE `guid` IN (30141, 30305, 30391)", self.rev)
        for entry, guid in ((7849, 30141), (6227, 30305), (6226, 30391)):
            self.assertIn(f"UPDATE `creature` SET `MovementType` = 0, `wander_distance` = 0 WHERE `id` = {entry} AND "
                          f"`guid` = {guid}", self.rev)

    def test_the_moves_are_the_headers_spots(self):
        fallout = self._header_point("kFalloutSpawn")
        found = [re.fullmatch(rf"UPDATE `creature` SET `position_x` = {NUM}, `position_y` = {NUM}, `position_z` = "
                              rf"{NUM}, `orientation` = {NUM}, `MovementType` = 0, `wander_distance` = 0 WHERE `id` = "
                              r"7079 AND `guid` = 30137", s) for s in self.rev]
        found = [m for m in found if m]
        self.assertEqual(len(found), 1)
        self.assertEqual([float(v) for v in found[0].groups()], fallout)
        self.assertIn("DELETE FROM `waypoint_data` WHERE `id` = 70790", self.rev)
        pummeler = self._header_point("kPummelerSpot")
        found = [re.fullmatch(rf"UPDATE `creature` SET `position_x` = {NUM}, `position_y` = {NUM}, `position_z` = "
                              rf"{NUM}, `orientation` = {NUM} WHERE `id` = 6229 AND `guid` = 30121", s)
                 for s in self.rev]
        found = [m for m in found if m]
        self.assertEqual(len(found), 1)
        self.assertEqual([float(v) for v in found[0].groups()], pummeler)
        self.assertIn("INSERT INTO `creature_template_movement` (`CreatureId`, `Ground`, `Swim`, `Flight`, `Rooted`) "
                      "VALUES (6229, 1, 1, 1, 1)", self.rev)
        self.assertIn("UPDATE `creature` SET `MovementType` = 0, `wander_distance` = 0 WHERE `id` = 6235 AND "
                      "`guid` = 30133", self.rev)

    def test_the_new_spawns_are_the_headers_spots(self):
        spawns = {
            (301105, 3011050): "kTechbotSpawn",
            (301110, 3011100): "kAlertSystemSpawn",
        }
        for (entry, guid), name in spawns.items():
            with self.subTest(entry=entry):
                point = self._header_point(name)
                found = [re.search(rf"VALUES \({guid}, {entry}, 90, 0, 0, 3, 1, 0, {NUM}, {NUM}, {NUM}, {NUM}, 86400",
                                   s) for s in self.rev]
                found = [m for m in found if m]
                self.assertEqual(len(found), 1)
                self.assertEqual([float(v) for v in found[0].groups()], point)
        objects = {
            (142345, 3013800, 3): "kPunchographACopySpot",
            (301382, 3013820, 2): "kConsoleSpot",
        }
        for (entry, guid, mask), name in objects.items():
            with self.subTest(entry=entry):
                point = self._header_point(name)
                found = [re.search(rf"VALUES \({guid}, {entry}, 90, 0, 0, {mask}, 1, {NUM}, {NUM}, {NUM}, {NUM}, 0, 0, "
                                   rf"{NUM}, {NUM},", s) for s in self.rev]
                found = [m for m in found if m]
                self.assertEqual(len(found), 1)
                values = [float(v) for v in found[0].groups()]
                self.assertEqual(values[:4], point)
                half = (point[3] - 2 * math.pi) / 2
                self.assertAlmostEqual(values[4], math.sin(half), places=5)
                self.assertAlmostEqual(values[5], math.cos(half), places=5)

    def test_the_workshop_door_is_keyless_and_scripted(self):
        self.assertIn("UPDATE `gameobject_template_addon` SET `flags` = `flags` & ~2 WHERE `entry` = 90858", self.rev)
        self.assertIn("UPDATE `gameobject_template` SET `Data1` = 0, `ScriptName` = 'go_gnomer_workshop_door' WHERE "
                      "`entry` = 90858", self.rev)
        # The door's (S0) and the Clearance Console's (D6Ha: bound by rev_thermaplugg_hard_mode_gnomeregan.sql, checked
        # by lib/test_gnomeregan_hard_mode.py).
        self.assertEqual(self.go_scripts, {"go_gnomer_workshop_door", "go_gnomer_clearance_console"})

    def test_every_registered_creature_script_is_bound(self):
        bound = {r.get("ScriptName") for r in (*self.edits.values(), *self.rows.values())} - {None, ""}
        # the gear's hard_mode_items.py look carries no script; every name bound is registered and vice versa
        self.assertEqual(self.creature_scripts, bound)

    def test_spells_sit_in_their_files_slice(self):
        for sid, name in self.spell_files.items():
            with self.subTest(spell=sid):
                self.assertTrue(name, "a declaration file")
                if name in SLICES:
                    first, last = SLICES[name]
                    ok = first <= sid <= last
                    if name == "thermaplugg_hard_mode.py":
                        ok = ok or CONSOLE_SPELLS[0] <= sid <= CONSOLE_SPELLS[1]
                    self.assertTrue(ok, f"{name} declares {sid}")

    def test_slices_tile_the_reservation(self):
        spell = id_blocks.RESERVATIONS["gnomeregan"]["spell"]
        found = re.findall(r"IdSlice constexpr kSpells(\w+)\{ (\d+), (\d+) \}", self.header)
        slices = {name: (int(a), int(b)) for name, a, b in found}
        self.assertEqual(slices.pop("Reservation"), (spell["start"], spell["end"]))
        parts = sorted(slices.values())
        self.assertEqual(parts[0][0], spell["start"])
        self.assertEqual(parts[-1][1], spell["end"])
        for (_a0, a1), (b0, _b1) in zip(parts, parts[1:]):
            self.assertEqual(b0, a1 + 1)
        for name, (first, last) in SLICES.items():
            self.assertIn((first, last), parts, name)
        self.assertTrue(slices["ConsoleAndSpare"][0] <= CONSOLE_SPELLS[0] <= CONSOLE_SPELLS[1]
                        <= slices["ConsoleAndSpare"][1])

    def test_new_ids_sit_in_the_reservation(self):
        res = id_blocks.RESERVATIONS["gnomeregan"]
        block = self.header[self.header.index("// The build's own (section 3.3"):
                            self.header.index("// ----", self.header.index("// The build's own (section 3.3"))]
        creatures = [int(v) for v in re.findall(r"NPC_\w+\s*=\s*(\d+)", block)]
        gameobjects = [int(v) for v in re.findall(r"GO_\w+\s*=\s*(30\d{4})", self.header)]
        self.assertEqual(len(creatures), 23)
        self.assertEqual(sorted(gameobjects), [301380, 301381, 301382])
        for value in creatures:
            self.assertTrue(res["creature"]["start"] <= value <= res["creature"]["end"], value)
        for value in gameobjects:
            self.assertTrue(res["gameobject"]["start"] <= value <= res["gameobject"]["end"], value)

    def test_the_checkpoint_rows_are_the_headers_spots(self):
        sql = CHECKPOINT_SQL.read_text(encoding="utf-8")
        rows = re.findall(rf"\(90, (\d+), (\d+), (\d+), {NUM}, {NUM}, {NUM}, {NUM}, {NUM},", sql)
        got = {int(r[0]): (int(r[1]), int(r[2]), [float(v) for v in r[3:7]], float(r[7])) for r in rows}
        self.assertEqual(set(got), {0, 6235, 6229})
        depot = self._header_point("kCheckpointDepot")
        reach = float(re.findall(rf"float constexpr kCheckpointDepotReachYd = {NUM}f;", self.header)[0])
        self.assertEqual(got[0], (1, 0, depot, reach))
        self.assertEqual(got[6235], (0, 1, self._header_point("kCheckpointElectrocutioner"), 0.0))
        self.assertEqual(got[6229], (0, 2, self._header_point("kCheckpointPummeler"), 0.0))
        # the entrance row (location index 0) is not touched
        statements = re.sub(r"^--.*$", "", sql, flags=re.M)
        self.assertNotIn("UPDATE", statements)
        self.assertNotRegex(statements, r"`creature_entry` = 0 AND `location_index` = 0")


if __name__ == "__main__":
    unittest.main()
