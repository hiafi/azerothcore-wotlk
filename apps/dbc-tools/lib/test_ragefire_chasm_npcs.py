"""
Ragefire Chasm build WP-S0, the data skeleton: source/npcs/ragefire_chasm/ against the Ragefire Chasm skeleton's C++
(modules/mod-dungeon-bosses src/RagefireChasm/RagefireChasmRework.h and the boss files), the S0 SQL rev and the
checkpoint row.

Checks:
  - each boss is bound by a creature_template_columns() edit to a script name that a src/RagefireChasm/*.cpp registers,
    with SmartAI off, immunity 1972, INSTANCE_BIND with both assist flags (section 7 #12 A), detection range 12, the
    stock DamageModifier, and the build spec's normal health;
  - the S0 rev drops the SmartAI of exactly the four bosses (the trash and the Orb keep theirs);
  - every creature script the C++ registers is bound by a declaration (an unbound registered name logs "not assigned"),
    and every script name a declaration binds is registered;
  - the stalker 300988 is declared with a model;
  - the header's spell slices tile the `ragefire_chasm` spell reservation and its new creature and gameobject ids sit in
    the reservation's blocks (each WP's spells in its own slice);
  - every boss's UpdateAI zeroes his assistance timer before UpdateVictim() (section 7 #12 A);
  - mod-dungeon-checkpoint's reached-only row (section 7 #14 A) and kCheckpoint in the header are one spot, at
    checkpoint order 0, with the entrance row left alone.

Only the skeleton's columns are looked at: the boss WPs add their own declarations to the same package.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_ragefire_chasm_npcs.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "RagefireChasm"
HEADER = MODULE_DIR / "RagefireChasmRework.h"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "ragefire_chasm"
S0_REV = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_skeleton_ragefire_chasm.sql"
CHECKPOINT_SQL = (REPO_ROOT / "modules" / "mod-dungeon-checkpoint" / "data" / "sql" / "db-world"
                  / "u_dungeon_checkpoint_2026_11_24_00.sql")

IMMUNITY_BOSS_STUN = 1972
BOSS_FLAGS_EXTRA = 0x1 | 0x02000000 | 0x04000000
BOSS_DETECTION_RANGE = 12.0
STALKER = 300988

# entry: (script name, normal health, level 16 class base basehp0, stock DamageModifier; live 2026-11-24)
BOSSES = {
    11517: ("boss_oggleflint_rework", 8_544, 356, 2.2),
    11518: ("boss_jergosh_rework", 8_596, 307, 1.95),
    11519: ("boss_bazzalan_rework", 9_256, 356, 2.2),
    11520: ("boss_taragaman_rework", 12_816, 356, 2.4),
}

# The spell slices (RagefireChasmRework.h) by the declaration file that owns them.
SLICES = {
    "oggleflint.py": (213550, 213579),
    "jergosh.py": (213580, 213609),
    "bazzalan.py": (213610, 213649),
    "taragaman.py": (213650, 213689),
    "taragaman_hard_mode.py": (213690, 213719),
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


def _registered_creature_scripts() -> set[str]:
    names = set()
    for path in MODULE_DIR.glob("*.cpp"):
        names.update(re.findall(r"^\s*RegisterDungeonReworkCreatureAI\((\w+),", path.read_text(), re.M))
    return names


def _header_ints(pattern: str) -> list[int]:
    return [int(v) for v in re.findall(pattern, HEADER.read_text())]


class RagefireChasmSkeletonTest(unittest.TestCase):
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
        cls.scripts = _registered_creature_scripts()

    def test_every_boss_is_bound(self):
        for entry, (script, _health, _base, damage) in BOSSES.items():
            with self.subTest(entry=entry):
                self.assertIn(script, self.scripts, "no C++ registers this name")
                row = self.edits.get(entry)
                self.assertIsNotNone(row, "no creature_template_columns() edit")
                self.assertEqual(row["ScriptName"], script)
                self.assertEqual(row["AIName"], "")
                self.assertEqual(row["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
                self.assertEqual(int(row["flags_extra"]), BOSS_FLAGS_EXTRA)
                self.assertEqual(float(row["detection_range"]), BOSS_DETECTION_RANGE)
                self.assertGreater(float(row["DamageModifier"]), 0.0)
                self.assertEqual(float(row["DamageModifier"]), damage, "stock until T tunes it")

    def test_normal_health_is_the_build_spec(self):
        for entry, (_script, health, base, _damage) in BOSSES.items():
            with self.subTest(entry=entry):
                self.assertEqual(round(float(self.edits[entry]["HealthModifier"]) * base), health)

    def test_every_registered_creature_script_is_bound(self):
        bound = {r.get("ScriptName") for r in (*self.edits.values(), *self.rows.values())} - {None, ""}
        self.assertEqual(self.scripts, bound)

    def test_the_stalker_is_declared_with_a_model(self):
        self.assertIn(STALKER, self.rows)
        self.assertIn(STALKER, {int(m["CreatureID"]) for m in self.reg.creature_template_models})

    def test_the_skeleton_rev_drops_the_four_bosses_smartai_only(self):
        text = re.sub(r"^--.*$", "", S0_REV.read_text(encoding="utf-8"), flags=re.M)
        statements = [s.strip() for s in text.split(";") if s.strip()]
        self.assertEqual(len(statements), 1)
        found = re.fullmatch(r"DELETE FROM `smart_scripts` WHERE `entryorguid` IN \(([\d, ]+)\) AND `source_type` = 0",
                             statements[0])
        self.assertIsNotNone(found, statements[0])
        self.assertEqual({int(v) for v in found.group(1).split(",")}, set(BOSSES))

    def test_spells_sit_in_their_files_slice(self):
        for sid, name in self.spell_files.items():
            with self.subTest(spell=sid):
                self.assertTrue(name, "a declaration file")
                if name in SLICES:
                    first, last = SLICES[name]
                    self.assertTrue(first <= sid <= last, f"{name} declares {sid}")

    def test_slices_tile_the_reservation(self):
        spell = id_blocks.RESERVATIONS["ragefire_chasm"]["spell"]
        found = re.findall(r"IdSlice constexpr kSpells\w+\{ (\d+), (\d+) \}", HEADER.read_text())
        slices = sorted((int(a), int(b)) for a, b in found)
        reservation = next(s for s in slices if s == (spell["start"], spell["end"]))
        parts = [s for s in slices if s != reservation]
        self.assertEqual(parts[0][0], spell["start"])
        self.assertEqual(parts[-1][1], spell["end"])
        for (_a0, a1), (b0, _b1) in zip(parts, parts[1:]):
            self.assertEqual(b0, a1 + 1)
        self.assertTrue(set(SLICES.values()) <= set(parts))

    def test_new_ids_sit_in_the_reservation(self):
        res = id_blocks.RESERVATIONS["ragefire_chasm"]
        creatures = _header_ints(r"NPC_RFC_\w+\s*=\s*(\d+)")
        gameobjects = _header_ints(r"GO_RFC_\w+\s*=\s*(\d+)")
        self.assertEqual(creatures, [300985, 300986, 300987, 300988, 300989])
        self.assertEqual(gameobjects, [301340, 301341, 301342])
        for value in creatures:
            self.assertTrue(res["creature"]["start"] <= value <= res["creature"]["end"], value)
        for value in gameobjects:
            self.assertTrue(res["gameobject"]["start"] <= value <= res["gameobject"]["end"], value)

    def test_every_boss_ai_stops_its_assist_calls_before_the_victim_check(self):
        """Section 7 #12 A: DONT_CALL_ASSISTANCE stops only the first call (Unit::Attack); the timer it sets calls again
        every 3 s (Creature::Update), so each UpdateAI zeroes it first (R-1-FW MAJ-1)."""
        for script, *_rest in BOSSES.values():
            with self.subTest(script):
                text = (MODULE_DIR / f"{script}.cpp").read_text(encoding="utf-8")
                body = text[text.index("void UpdateAI("):]
                self.assertIn("UpdateVictim()", body)
                self.assertIn("me->SetAssistanceTimer(0);", body[:body.index("UpdateVictim()")])

    def test_the_checkpoint_row_is_the_headers_spot(self):
        num = r"(-?\d+(?:\.\d*)?)"
        cpp = re.findall(rf"Point3 constexpr kCheckpoint\{{ {num}f, {num}f, {num}f, {num}f \}};", HEADER.read_text())
        reach = re.findall(rf"float constexpr kCheckpointReachYd = {num}f;", HEADER.read_text())
        sql = CHECKPOINT_SQL.read_text(encoding="utf-8")
        row = re.findall(rf"\(389, 0, 1, 0, {num}, {num}, {num}, {num}, {num},", sql)
        self.assertEqual((len(cpp), len(reach), len(row)), (1, 1, 1))
        self.assertEqual([float(v) for v in row[0]], [float(v) for v in (*cpp[0], reach[0])])
        # Reached only; 5 yd could be run past between two of the module's 1 s looks (R-1-FW MIN-4)
        self.assertEqual(float(reach[0]), 10.0)
        # The entrance row (location_index 0, reach 0) is not touched.
        statements = re.sub(r"^--.*$", "", sql, flags=re.M)
        self.assertEqual(re.findall(r"`location_index` = (\d+)", statements), ["1"])
        self.assertNotIn("UPDATE", statements)


if __name__ == "__main__":
    unittest.main()
