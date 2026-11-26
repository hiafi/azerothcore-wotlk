"""
Zul'Farrak build WP-S0, the data skeleton: source/npcs/zul_farrak/ against the Zul'Farrak skeleton's C++
(modules/mod-dungeon-bosses src/ZulFarrak/ZulFarrakRework.h and the WPs' files), the S0 SQL rev and the checkpoint
row.

Checks:
  - each reworked boss is bound by a creature_template_columns() edit to a script name that a src/ZulFarrak/*.cpp
    registers, with SmartAI off, immunity 1972, INSTANCE_BIND with both assist flags (section 7 #23 A), detection range
    12, its DamageModifier, and the normal health of handoff s3.6 (the header's Health table);
  - the S0 rev drops the SmartAI of exactly the units the rework scripts (s3.2 item 6), the barrel's and the gong's
    (with the gong's condition), binds the crew's and the cages' new scripts and makes the gong not selectable;
  - every creature and gameobject script the C++ registers is bound (by a declaration or the S0 rev), and every script
    name bound there is registered (an unbound registered name logs "not assigned");
  - the instance's credit spells are declared inside the shared slice; every WP's spells sit in its file's slice;
  - the header's spell slices tile the `zul_farrak` spell reservation, and its new creature and gameobject ids sit in
    the reservation's blocks;
  - mod-dungeon-checkpoint's boss row (section 7 #26 A) and kCheckpoint in the header are one spot, after Zum'rah,
    with the entrance row left alone.

Only the skeleton's columns are looked at: the WPs add their own declarations to the same package.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_zul_farrak_npcs.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "ZulFarrak"
HEADER = MODULE_DIR / "ZulFarrakRework.h"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "zul_farrak"
S0_REV = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_skeleton_zul_farrak.sql"
CHECKPOINT_SQL = (REPO_ROOT / "modules" / "mod-dungeon-checkpoint" / "data" / "sql" / "db-world"
                  / "u_dungeon_checkpoint_2026_11_25_00.sql")

IMMUNITY_BOSS_STUN = 1972
BOSS_FLAGS_EXTRA = 0x1 | 0x02000000 | 0x04000000
BOSS_DETECTION_RANGE = 12.0

# entry: (script name, the header's Health name, class base basehp0 at the level, DamageModifier; live 2026-11-25:
# stock until T, Sezz'ziz and Nekrum by s7 #44 A)
BOSSES = {
    7272: ("boss_theka_rework", "kTheka", 1919, 2.4),
    8127: ("boss_antusul_rework", "kAntusul", 1535, 4.25),
    7271: ("boss_zumrah_rework", "kZumrah", 1535, 2.4),
    7274: ("boss_sandfury_executioner_rework", "kExecutioner", 1919, 2.4),
    7275: ("boss_sezzziz_rework", "kSezzziz", 1535, 2.4),
    7796: ("boss_nekrum_rework", "kNekrum", 1848, 3.0),
    7267: ("boss_ukorz_rework", "kUkorz", 1919, 2.4),
    7797: ("boss_ruuzlu_rework", "kRuuzlu", 1848, 2.4),
    7795: ("boss_velratha_rework", "kVelratha", 1343, 2.4),
    7273: ("boss_gahzrilla_rework", "kGahzrilla", 1919, 3.5),
}

# The units whose stock SmartAI the S0 rev drops (s3.2 item 6).
SMARTAI_DROPPED = {7274, 7796, 7605, 7606, 7608, 7272, 8127, 8156, 7271, 7267, 7797, 7795, 7273}

# The crew's and the cages' script names (the S0 rev binds them: no dbc-tools row).
CREW_SCRIPTS = {7604: "npc_bly_crew_bly", 7605: "npc_bly_crew_raven", 7606: "npc_bly_crew_oro",
                7607: "npc_bly_crew_weegli", 7608: "npc_bly_crew_murta"}
CAGES = {141070, 141071, 141072, 141073, 141074}

# The spell slices (ZulFarrakRework.h) by the declaration file that owns them.
SLICES = {
    "instance.py": (213840, 213844),
    "theka.py": (213860, 213889),
    "antusul.py": (213890, 213919),
    "zumrah.py": (213920, 213959),
    "sandfury_executioner.py": (213960, 213989),
    "pyramid_stair.py": (213990, 214029),
    "bly_crew_fight.py": (214030, 214069),
    "ukorz.py": (214070, 214109),
    "gahzrilla.py": (214110, 214149),
    "gahzrilla_crew_hard_mode.py": (214150, 214189),
    "gahzrilla_deluge.py": (214190, 214209),
}


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


class ZulFarrakSkeletonTest(unittest.TestCase):
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

    def test_every_boss_is_bound(self):
        for entry, (script, _health, _base, damage) in BOSSES.items():
            with self.subTest(entry=entry):
                self.assertIn(script, self.creature_scripts, "no C++ registers this name")
                row = self.edits.get(entry)
                self.assertIsNotNone(row, "no creature_template_columns() edit")
                self.assertEqual(row["ScriptName"], script)
                self.assertEqual(row["AIName"], "")
                self.assertEqual(row["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
                self.assertEqual(int(row["flags_extra"]), BOSS_FLAGS_EXTRA)
                self.assertEqual(float(row["detection_range"]), BOSS_DETECTION_RANGE)
                self.assertEqual(float(row["DamageModifier"]), damage)

    def test_normal_health_is_the_headers(self):
        for entry, (_script, name, base, _damage) in BOSSES.items():
            with self.subTest(entry=entry):
                # the engine's rounding (CreatureData.h GenerateHealth: ceil of base x float(mod))
                self.assertEqual(math.ceil(base * float(self.edits[entry]["HealthModifier"])),
                                 self._header_health(name))

    def test_the_skeleton_rev_drops_the_reworked_units_smartai(self):
        found = [re.fullmatch(r"DELETE FROM `smart_scripts` WHERE `source_type` = 0 AND `entryorguid` IN \(([\d, ]+)\)",
                              s) for s in self.rev]
        found = [m for m in found if m]
        self.assertEqual(len(found), 1)
        self.assertEqual(_ints(found[0].group(1)), SMARTAI_DROPPED)
        # the barrel and the gong, the gong's condition, their AIName, the gong not selectable
        self.assertIn("DELETE FROM `smart_scripts` WHERE `source_type` = 1 AND `entryorguid` IN (141612, 141832)",
                      self.rev)
        self.assertIn("DELETE FROM `conditions` WHERE `SourceTypeOrReferenceId` = 22 AND `SourceId` = 1 AND "
                      "`SourceEntry` IN (141612, 141832)", self.rev)
        self.assertIn("UPDATE `gameobject_template` SET `AIName` = '' WHERE `entry` IN (141612, 141832)", self.rev)
        self.assertIn("UPDATE `gameobject_template_addon` SET `flags` = `flags` | 16 WHERE `entry` = 141832", self.rev)
        # nothing else is deleted
        deletes = [s for s in self.rev if s.startswith("DELETE")]
        self.assertEqual(len(deletes), 3)

    def test_the_rev_binds_the_crew_and_the_cages(self):
        for entry, script in CREW_SCRIPTS.items():
            with self.subTest(entry=entry):
                self.assertIn(f"UPDATE `creature_template` SET `AIName` = '', `ScriptName` = '{script}' "
                              f"WHERE `entry` = {entry}", self.rev)
                self.assertIn(script, self.creature_scripts)
                self.assertNotIn(entry, self.edits, "one owner per column: the crew's script is the rev's")
        cages = [re.fullmatch(r"UPDATE `gameobject_template` SET `ScriptName` = 'go_zf_troll_cage' WHERE `entry` "
                              r"IN \(([\d, ]+)\)", s) for s in self.rev]
        cages = [m for m in cages if m]
        self.assertEqual(len(cages), 1)
        self.assertEqual(_ints(cages[0].group(1)), CAGES)
        self.assertEqual(self.go_scripts, {"go_zf_troll_cage"})

    def test_every_registered_creature_script_is_bound(self):
        bound = {r.get("ScriptName") for r in (*self.edits.values(), *self.rows.values())} - {None, ""}
        bound |= set(CREW_SCRIPTS.values())
        # the gear's hard_mode_items.py looks carry no script; every name bound is registered and vice versa
        self.assertEqual(self.creature_scripts, bound)

    def test_spells_sit_in_their_files_slice(self):
        self.assertEqual(self.spell_files.get(213840), "instance.py")
        self.assertEqual(self.spell_files.get(213841), "instance.py")
        for sid, name in self.spell_files.items():
            with self.subTest(spell=sid):
                self.assertTrue(name, "a declaration file")
                if name in SLICES:
                    first, last = SLICES[name]
                    self.assertTrue(first <= sid <= last, f"{name} declares {sid}")

    def test_slices_tile_the_reservation(self):
        spell = id_blocks.RESERVATIONS["zul_farrak"]["spell"]
        found = re.findall(r"IdSlice constexpr kSpells(\w+)\{ (\d+), (\d+) \}", self.header)
        slices = {name: (int(a), int(b)) for name, a, b in found}
        self.assertEqual(slices.pop("Reservation"), (spell["start"], spell["end"]))
        crew_ally = slices.pop("CrewAlly")
        parts = sorted(slices.values())
        self.assertEqual(parts[0][0], spell["start"])
        self.assertEqual(parts[-1][1], spell["end"])
        for (_a0, a1), (b0, _b1) in zip(parts, parts[1:]):
            self.assertEqual(b0, a1 + 1)
        self.assertTrue(slices["Shared"][0] <= crew_ally[0] <= crew_ally[1] <= slices["Shared"][1])
        for name, (first, last) in SLICES.items():
            if name != "instance.py":
                self.assertIn((first, last), parts, name)

    def test_new_ids_sit_in_the_reservation(self):
        res = id_blocks.RESERVATIONS["zul_farrak"]
        creatures = [int(v) for v in re.findall(r"NPC_ZF_\w+\s*=\s*(\d+)", self.header)]
        gameobjects = [int(v) for v in re.findall(r"GO_ZF_\w+\s*=\s*(\d+)", self.header)]
        self.assertEqual(len(creatures), 19)
        self.assertEqual(gameobjects, [301360, 301361])
        for value in creatures:
            self.assertTrue(res["creature"]["start"] <= value <= res["creature"]["end"], value)
        for value in gameobjects:
            self.assertTrue(res["gameobject"]["start"] <= value <= res["gameobject"]["end"], value)

    def test_the_checkpoint_row_is_the_headers_spot(self):
        num = r"(-?\d+(?:\.\d*)?)"
        cpp = re.findall(rf"Point3 constexpr kCheckpoint\{{ {num}f, {num}f, {num}f, {num}f \}};", self.header)
        sql = CHECKPOINT_SQL.read_text(encoding="utf-8")
        row = re.findall(rf"\(209, 7271, 0, 1, {num}, {num}, {num}, {num}, 0,", sql)
        self.assertEqual((len(cpp), len(row)), (1, 1))
        self.assertEqual([float(v) for v in row[0]], [float(v) for v in cpp[0]])
        # A boss row after Zum'rah (order 1, reach 0); the entrance row (creature 0, index 0) is not touched.
        statements = re.sub(r"^--.*$", "", sql, flags=re.M)
        self.assertEqual(re.findall(r"`creature_entry` = (\d+)", statements), ["7271"])
        self.assertNotIn("UPDATE", statements)


if __name__ == "__main__":
    unittest.main()
