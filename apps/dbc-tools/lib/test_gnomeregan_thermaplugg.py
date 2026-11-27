"""
Gnomeregan build WP-D6, Mekgineer Thermaplugg: source/npcs/gnomeregan/thermaplugg.py (spells 214490-214511, the boss
kit 301120-301127; 7800's columns are test_gnomeregan_npcs.py's), data/sql/updates/pending_db_world/
rev_thermaplugg_gnomeregan.sql (texts 7800) and the C++ they must agree with (modules/mod-dungeon-bosses
src/Gnomeregan/ThermapluggLogic.h and boss_thermaplugg_rework.cpp).

Checks:
  - the spells sit in the D6 slice and ThermapluggLogic.h names the same ids; every blast is a resolve copy in its
    school (Fire, Frost for the Frost Bomb, Nature for the Radioactive Bomb);
  - the kick table (rule 26): Remote Detonator is the only kickable cast (Fire, InterruptFlags 15, PreventionType 1,
    the header's 3 s); every other spell is instant;
  - rule 27: the Frost root is Magic and the Radioactive Poison is Poison (rewards); Locked Out, the bomb mark and the
    Sticky Bomb are not dispellable, go through immunities and drop on a map change; the Poison's tick is the kit's
    percent script (4.00% in hundredths, 12 s, ignores caster modifiers);
  - Knock Away is the stock 10101's copy (100% weapon damage and the stock knockback);
  - the looks use the V constants (appendix C4); the numbers thermaplugg.py pins are ThermapluggLogic.h's;
  - the creatures: the bombs are their own entries (never the gear's 301100, s7 #40 A), faction 63, level 28,
    passive bodies on npc_gnomer_walking_bomb, The Big One not attackable at BIG_ONE_SCALE; the stalkers are helpers;
  - the SQL: stock group 1 loses its second row, five new emote lines (groups 4-8, type 41), nothing else.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_gnomeregan_thermaplugg.py
"""

from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import test_gnomeregan_npcs as npcs_test  # noqa: E402
from source.npcs.gnomeregan import _visuals as visuals  # noqa: E402

MDB = REPO_ROOT / "modules" / "mod-dungeon-bosses"
SRC = MDB / "src" / "Gnomeregan"
LOGIC = SRC / "ThermapluggLogic.h"
BOSS = SRC / "boss_thermaplugg_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_thermaplugg_gnomeregan.sql"
DECLARATIONS = TOOL_ROOT / "source" / "npcs" / "gnomeregan" / "thermaplugg.py"

FIRST, LAST = 214490, 214539
EFFECT_SCHOOL_DAMAGE, EFFECT_DUMMY, EFFECT_APPLY_AURA = 2, 3, 6
EFFECT_WEAPON_PERCENT_DAMAGE, EFFECT_KNOCK_BACK = 31, 98
AURA_DUMMY, AURA_PERIODIC_DAMAGE, AURA_MOD_ROOT = 4, 3, 26
PHYSICAL, FIRE, NATURE, FROST = 1, 4, 8, 16
ATTR0_NO_IMMUNITIES = 0x20000000
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
CHANGE_MAP = 0x00080000

RESOLVES = {
    "SPELL_MT_BOMB_BLAST": FIRE, "SPELL_MT_MINE_BLAST": FIRE, "SPELL_MT_INCENDIARY_BLAST": FIRE,
    "SPELL_MT_FIRE_PATCH": FIRE, "SPELL_MT_FROST_BLAST": FROST, "SPELL_MT_RADIO_BLAST": NATURE,
    "SPELL_MT_STICKY_BLAST": FIRE, "SPELL_MT_BIG_ONE_BLAST": FIRE,
}
LOOKS = {
    "SPELL_MT_FACE_BEAM": "MT_FACE_BEAM", "SPELL_MT_BOMB_MARK": "MT_BOMB_MARK", "SPELL_MT_BLAST_LOOK": "MT_BLAST",
    "SPELL_MT_BLAST_FLASH": "MT_BLAST_FLASH", "SPELL_MT_LOCKED_OUT": "MT_LOCKED_OUT",
    "SPELL_MT_MINE_LOB": "MT_MINE_LOB", "SPELL_MT_MINE_LOOK": "MT_DETONATE_MINE",
    "SPELL_MT_FIRE_PATCH_LOOK": "MT_FIRE_PATCH", "SPELL_MT_FIRE_PATCH_CAST": "MT_FIRE_PATCH_CAST",
    "SPELL_MT_FROST_ROOT": "MT_FROST", "SPELL_MT_RADIO_POISON": "MT_RADIO", "SPELL_MT_STICKY_BOMB": "MT_STICKY",
}
NOT_DISPELLABLE = ("SPELL_MT_BOMB_MARK", "SPELL_MT_LOCKED_OUT", "SPELL_MT_STICKY_BOMB")
BOMBS = {301120: "DISPLAY_BOMB", 301121: "DISPLAY_BOMB", 301122: "DISPLAY_BOMB_FROST",
         301123: "DISPLAY_BOMB_RADIO", 301124: "DISPLAY_BIG_ONE"}
STALKERS = {301125: "DISPLAY_INVISIBLE_STALKER", 301126: "DISPLAY_MINE", 301127: "DISPLAY_INVISIBLE_STALKER"}


class _Constants:
    """The module-level constants thermaplugg.py pins (the declaration file needs the registry's loader to import)."""

    def __init__(self, path: Path):
        for name, value in re.findall(r"^([A-Z][A-Z_0-9]+) = ([^#\n]+?)\s*(?:#.*)?$", path.read_text(), re.M):
            try:
                setattr(self, name, ast.literal_eval(value))
            except (ValueError, SyntaxError):
                pass


thermaplugg = _Constants(DECLARATIONS)


def _logic_ids() -> dict[str, int]:
    text = LOGIC.read_text()
    block = text[text.index("enum ThermapluggSpells"):text.index("};", text.index("enum ThermapluggSpells"))]
    return {name: int(value) for name, value in re.findall(r"(SPELL_MT_\w+)\s*=\s*(\d+)", block)}


def _tune(name: str) -> str:
    found = re.findall(rf"inline constexpr [\w:<>, ]+ {name}(?:\{{|\s*=\s*)([^;]+?)\}}?;", LOGIC.read_text())
    if not found:
        raise AssertionError(f"{name} not in ThermapluggLogic.h")
    return found[0].strip().strip("{} ")


class ThermapluggTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = npcs_test._load()
        cls.spells = {int(e["id"]): e for e in reg.spells if FIRST <= int(e["id"]) <= LAST}
        cls.scripts = {}
        for row in reg.spell_script_names:
            cls.scripts.setdefault(int(row["spell_id"]), set()).add(row["ScriptName"])
        cls.rows = {int(r["entry"]): r for r in reg.creature_templates}
        cls.models = {int(m["CreatureID"]): m for m in reg.creature_template_models}
        cls.ids = _logic_ids()

    def _spell(self, name: str) -> dict:
        return self.spells[self.ids[name]]

    def _raw(self, name: str) -> dict:
        return self._spell(name).get("raw_overrides", {})

    def test_ids_agree_with_the_header(self):
        self.assertEqual(len(self.ids), 22)
        self.assertEqual(set(self.ids.values()), set(self.spells))
        for name, sid in self.ids.items():
            self.assertTrue(FIRST <= sid <= LAST, name)

    def test_blasts_are_resolve_copies(self):
        for name, school in RESOLVES.items():
            with self.subTest(name=name):
                s = self._spell(name)
                self.assertEqual(int(s["school"]), school)
                self.assertEqual(int(s["effect1"]["type"]), EFFECT_SCHOOL_DAMAGE)
                self.assertIn("spell_boss_mechanics_resolve", self.scripts.get(self.ids[name], set()))

    def test_the_detonator_is_the_only_kickable_cast(self):
        det = self._spell("SPELL_MT_DETONATOR")
        self.assertEqual(int(det["school"]), FIRE)
        self.assertEqual(int(self._raw("SPELL_MT_DETONATOR")["InterruptFlags"]), 15)
        self.assertEqual(int(self._raw("SPELL_MT_DETONATOR")["PreventionType"]), 1)
        self.assertEqual(str(det.get("_spell").cast_time_ms), _tune("kDetonatorCastMs"))
        self.assertEqual(thermaplugg.DETONATOR_CAST_MS, int(_tune("kDetonatorCastMs")))
        for name, sid in self.ids.items():
            if name == "SPELL_MT_DETONATOR":
                continue
            with self.subTest(name=name):
                self.assertEqual(self.spells[sid]["_spell"].cast_time_ms, 0)

    def test_dispels(self):
        root = self._spell("SPELL_MT_FROST_ROOT")
        self.assertEqual(int(root["dispel"]), 1)
        self.assertEqual(int(root["effect1"]["apply_aura"]), AURA_MOD_ROOT)
        self.assertEqual(int(root["duration_ms"]), thermaplugg.FROST_ROOT_MS)
        poison = self._spell("SPELL_MT_RADIO_POISON")
        self.assertEqual(int(poison["dispel"]), 4)
        self.assertEqual(int(poison["effect1"]["apply_aura"]), AURA_PERIODIC_DAMAGE)
        self.assertEqual(int(poison["effect1"]["base_points"]), int(_tune("kRadioPoisonHundredths")))
        self.assertEqual(int(poison["effect1"]["amplitude"]), 1000)
        self.assertEqual(int(poison["duration_ms"]), int(_tune("kRadioPoisonMs")))
        self.assertTrue(int(self._raw("SPELL_MT_RADIO_POISON")["AttributesEx3"]) & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertGreater(int(self._raw("SPELL_MT_RADIO_POISON")["CumulativeAura"]), 1)
        self.assertIn("spell_dungeon_refflat_periodic", self.scripts.get(self.ids["SPELL_MT_RADIO_POISON"], set()))
        for name in NOT_DISPELLABLE:
            with self.subTest(name=name):
                s = self._spell(name)
                self.assertEqual(int(s["dispel"]), 0)
                self.assertTrue(int(s["attributes"]) & ATTR0_NO_IMMUNITIES)
                self.assertTrue(int(self._raw(name)["AuraInterruptFlags"]) & CHANGE_MAP)
                self.assertEqual(int(s["effect1"]["apply_aura"]), AURA_DUMMY)
        self.assertEqual(int(self._spell("SPELL_MT_LOCKED_OUT")["duration_ms"]), int(_tune("kLockedOutMs")))
        self.assertEqual(int(self._spell("SPELL_MT_STICKY_BOMB")["duration_ms"]), int(_tune("kStickyFuseMs")))
        self.assertEqual(thermaplugg.LOCKED_OUT_MS, int(_tune("kLockedOutMs")))
        self.assertEqual(thermaplugg.STICKY_FUSE_MS, int(_tune("kStickyFuseMs")))
        self.assertEqual(thermaplugg.FIRE_PATCH_MS, int(_tune("kFirePatchMs")))

    def test_knock_away_is_the_stock_copy(self):
        s = self._spell("SPELL_MT_KNOCK_AWAY")
        self.assertEqual(int(s["school"]), PHYSICAL)
        self.assertEqual(int(s["effect1"]["type"]), EFFECT_WEAPON_PERCENT_DAMAGE)
        self.assertEqual(int(s["effect2"]["type"]), EFFECT_KNOCK_BACK)
        self.assertEqual((int(s["effect2"]["base_points"]), int(s["effect2"]["die_sides"]),
                          int(s["effect2"]["misc_value"])), (112, 75, 75))

    def test_looks_are_the_visual_constants(self):
        for name, constant in LOOKS.items():
            with self.subTest(name=name):
                self.assertEqual(int(self._raw(name)["SpellVisualID_1"]), getattr(visuals, constant))
        self.assertNotIn("SpellVisualID_1", self._raw("SPELL_MT_DETONATOR"))     # 354 is never wired
        self.assertEqual(int(self._raw("SPELL_MT_KNOCK_AWAY")["SpellVisualID_1"]), 2069)

    def test_the_creatures(self):
        for entry, display in BOMBS.items():
            with self.subTest(entry=entry):
                row = self.rows[entry]
                self.assertEqual(row["ScriptName"], "npc_gnomer_walking_bomb")
                self.assertEqual(int(row["faction"]), 63)
                self.assertEqual((int(row["minlevel"]), int(row["maxlevel"])), (28, 28))
                self.assertEqual(int(row["type"]), 9)
                self.assertEqual(int(row["lootid"]), 0)
                self.assertEqual(int(self.models[entry]["CreatureDisplayID"]), getattr(visuals, display))
        self.assertTrue(int(self.rows[301124]["unit_flags"]) & 0x2)
        self.assertFalse(int(self.rows[301120]["unit_flags"]) & 0x2)
        self.assertAlmostEqual(float(self.models[301124]["DisplayScale"]), visuals.BIG_ONE_SCALE)
        self.assertAlmostEqual(float(self.models[301120]["DisplayScale"]), visuals.BOMB_SCALE)
        self.assertNotIn(301100, BOMBS)
        for entry, display in STALKERS.items():
            with self.subTest(entry=entry):
                row = self.rows[entry]
                self.assertEqual(row["ScriptName"], "npc_gnomer_thermaplugg_stalker")
                self.assertTrue(int(row["unit_flags"]) & 0x02000000)
                self.assertEqual(int(self.models[entry]["CreatureDisplayID"]), getattr(visuals, display))
        low, high = visuals.MINE_SCALE_RANGE
        self.assertTrue(low <= float(self.models[301126]["DisplayScale"]) <= high)
        # the header's entries are these
        header = (SRC / "GnomereganRework.h").read_text()
        for name, entry in (("NPC_WALKING_BOMB", 301120), ("NPC_THE_BIG_ONE", 301124), ("NPC_MINE", 301126),
                            ("NPC_ZONE_STALKER", 301127)):
            self.assertRegex(header, rf"{name}\s*=\s*{entry},")

    def test_the_sql(self):
        text = re.sub(r"^--.*$", "", SQL.read_text(encoding="utf-8"), flags=re.M)
        statements = [" ".join(s.split()) for s in text.split(";") if s.strip()]
        self.assertEqual(statements[0],
                         "DELETE FROM `creature_text` WHERE `CreatureID` = 7800 AND `GroupID` = 1 AND `ID` = 1")
        self.assertEqual(statements[1],
                         "DELETE FROM `creature_text` WHERE `CreatureID` = 7800 AND `GroupID` BETWEEN 4 AND 8")
        rows = re.findall(r"\(7800, (\d+), 0, '((?:[^']|'')*)', (\d+), 0, 100, 0, 0, 0, 0, (\d+),", statements[2])
        self.assertEqual([int(r[0]) for r in rows], [4, 5, 6, 7, 8])
        self.assertTrue(all(int(r[2]) == 41 and int(r[3]) == 3 for r in rows))
        self.assertIn("$n", rows[2][1])
        self.assertEqual(len(statements), 3)

    def test_the_cpp_registers_and_reads_these(self):
        boss = BOSS.read_text()
        for name in ("npc_gnomer_walking_bomb", "npc_gnomer_thermaplugg_stalker", "boss_thermaplugg_rework"):
            self.assertIn(f"RegisterDungeonReworkCreatureAI({name},", boss)
        self.assertIn("GnomereganRework::NoAssist(me);", boss)
        self.assertNotIn("301100", boss)


if __name__ == "__main__":
    unittest.main()
