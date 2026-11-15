"""
Blackrock Spire build WP-B6, Quartermaster Zigris: source/npcs/blackrock_spire/zigris.py against its C++
(modules/mod-dungeon-bosses src/BlackrockSpire/ZigrisLogic.h, boss_quartermaster_zigris_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in Zigris's slice (210180-210209) and ZigrisLogic.h names the same ids;
  - Zigris 9736 is bound (SmartAI off) at 140k on the level 59 warrior base, the stock DamageModifier, stun immune;
  - the Clockwork Sheep 300707 sits in the reservation, is bound, has 3,000 health, names its heroic entry, and wears
    display 3886 (not the engineering 2675);
  - the hits are resolve copies of the right school; the root and the stun last the header's seconds; the mortar look's
    speed is the header's; the fuse is a hidden lasting aura;
  - the SQL rev writes the six texts (yells, boss emotes), the three gameobjects and the three crate spawns at the
    header's crate spots.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_spire_zigris.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockSpire"
HEADER = MODULE_DIR / "ZigrisLogic.h"
REWORK = MODULE_DIR / "BlackrockSpireRework.h"
SCRIPT = MODULE_DIR / "boss_quartermaster_zigris_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_quartermaster_zigris_blackrock_spire.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_spire"

SLICE = range(210180, 210210)
(NET_TRAP, NETTED, KEG_BLAST, KEG_STUN, FUSE, BLAST_LOOK, MORTAR_SHELL, MORTAR_LOOK, SMOKE_BOMB, LEAP, SHEEP_BLAST,
 SHEEP_WINDUP) = range(210180, 210192)
ZIGRIS = 9736
SHEEP = 300707
SHEEP_HEROIC_ENTRY = 310290
GAMEOBJECTS = {301252: 5271, 301253: 7529, 301254: 457}     # the build spec's displays
ENGINEERING_SHEEP_DISPLAY_ENTRY = 2675

SCHOOL_PHYSICAL, SCHOOL_FIRE = 1, 4
SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT = 2, 6, 3
AURA_DUMMY, AURA_MOD_STUN, AURA_MOD_ROOT = 4, 12, 26
MECHANIC_ROOT, MECHANIC_STUN = 7, 12
AURA_INTERRUPT_CHANGE_MAP = 0x00080000
TARGET_FLAG_DEST_LOCATION = 0x40
RESOLVE = "spell_boss_mechanics_resolve"
WARRIOR_59_BASE = 2961      # creature_classlevelstats level 59 class 1 basehp0
WARRIOR_60_BASE = 3052      # level 60 class 1 basehp0


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


def _raw(spell: dict, column: str) -> int | float:
    return (spell.get("raw_overrides") or {}).get(column, 0) or 0


def _header() -> str:
    return HEADER.read_text(encoding="utf-8")


def _header_value(name: str) -> float:
    match = re.search(rf"{name}\s*=\s*(-?[\d.]+)f?;", _header())
    assert match, name
    return float(match.group(1))


class ZigrisDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) == ZIGRIS}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == SHEEP}
        cls.models = [e for e in reg.creature_template_models if int(e["CreatureID"]) == SHEEP]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(NET_TRAP, SHEEP_WINDUP + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_spire", {"spell": mine}), [])
        first = re.search(r"kSpellsZigris\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(first)
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_ZG_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))

    def test_zigris_is_bound(self):
        boss = self.edits[ZIGRIS]
        self.assertEqual(boss["ScriptName"], "boss_quartermaster_zigris_rework")
        self.assertEqual(boss["AIName"], "")
        # 140k at 5 players (the build spec), within the S0 skeleton's 2 HP.
        self.assertLessEqual(abs(math.ceil(WARRIOR_59_BASE * boss["HealthModifier"]) - 140000), 2)
        # Stock 3.5, not the live 5 the retired mod-progression left (the wave 1 precedent).
        self.assertAlmostEqual(float(boss["DamageModifier"]), 3.5)
        self.assertEqual(boss["CreatureImmunitiesId"], 1972)
        self.assertEqual(boss["flags_extra"], 1)
        for name in ("boss_quartermaster_zigris_rework", "npc_brs_clockwork_sheep"):
            self.assertIn(f"RegisterDungeonReworkCreatureAI({name},", self.cpp)
        self.assertIn('BrsTest::RegisterBoss("zigris"', self.cpp)

    def test_the_clockwork_sheep(self):
        self.assertEqual(id_blocks.out_of_reservation("blackrock_spire", {"creature": [SHEEP]}), [])
        sheep = self.creatures[SHEEP]
        self.assertEqual(sheep["ScriptName"], "npc_brs_clockwork_sheep")
        self.assertEqual(sheep["AIName"], "")
        self.assertEqual(sheep["difficulty_entry_1"], SHEEP_HEROIC_ENTRY)
        # 3,000 health at 5 players, the header's.
        self.assertEqual(math.ceil(WARRIOR_60_BASE * sheep["HealthModifier"]), int(_header_value("kSheepHealth")))
        self.assertEqual(int(_header_value("kSheepHealth")), 3000)
        # Attackable (the group kills it), harmless (no melee), no loot, no XP.
        self.assertEqual(sheep["unit_flags"], 0)
        self.assertEqual(sheep["DamageModifier"], 0.0)
        self.assertEqual(sheep["lootid"], 0)
        self.assertEqual(sheep["ExperienceModifier"], 0.0)
        # The SheepRobo display 3886, never the engineering sheep's creature.
        self.assertEqual([m["CreatureDisplayID"] for m in self.models], [3886])
        self.assertNotEqual(SHEEP, ENGINEERING_SHEEP_DISPLAY_ENTRY)
        self.assertRegex(REWORK.read_text(encoding="utf-8"), rf"NPC_BRS_CLOCKWORK_SHEEP\s*=\s*{SHEEP},")

    def test_hits_are_resolve_copies_of_the_right_school(self):
        for spell_id, school in ((NET_TRAP, SCHOOL_PHYSICAL), (KEG_BLAST, SCHOOL_FIRE), (MORTAR_SHELL, SCHOOL_FIRE),
                                 (SHEEP_BLAST, SCHOOL_FIRE)):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertEqual(spell["school"], school, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
        self.assertEqual({name for _, name in self.scripts}, {RESOLVE})

    def test_the_root_and_the_stun(self):
        netted = self.spells[NETTED]
        self.assertEqual(netted["effect1"]["apply_aura"], AURA_MOD_ROOT)
        self.assertEqual(netted["mechanic"], MECHANIC_ROOT)
        self.assertEqual(netted["duration_ms"], int(_header_value("kNettedMs")))
        self.assertEqual(netted["duration_ms"], 2000)
        stun = self.spells[KEG_STUN]
        self.assertEqual(stun["effect1"]["apply_aura"], AURA_MOD_STUN)
        self.assertEqual(stun["mechanic"], MECHANIC_STUN)
        self.assertEqual(stun["duration_ms"], int(_header_value("kKegStunMs")))
        self.assertEqual(stun["duration_ms"], 2000)
        for spell_id in (NETTED, KEG_STUN):
            self.assertEqual(_raw(self.spells[spell_id], "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP, spell_id)
        # The net look rides the root (Hooked Net 13608, SpellVisual 3519).
        self.assertEqual(_raw(netted, "SpellVisualID_1"), 3519)

    def test_the_looks(self):
        # The mortar shell flies at the header's speed, to a point.
        look = self.spells[MORTAR_LOOK]
        self.assertEqual(look["effect1"]["type"], DUMMY_EFFECT)
        self.assertAlmostEqual(float(_raw(look, "Speed")), _header_value("kShellMissileSpeed"))
        self.assertEqual(_raw(look, "SpellVisualID_1"), 3819)
        self.assertTrue(_raw(look, "Targets") & TARGET_FLAG_DEST_LOCATION)
        # The blast is a point look too (Goblin Sapper Charge's SpellVisual 2899).
        blast = self.spells[BLAST_LOOK]
        self.assertEqual(_raw(blast, "SpellVisualID_1"), 2899)
        self.assertTrue(_raw(blast, "Targets") & TARGET_FLAG_DEST_LOCATION)
        # The fuse is a hidden, lasting aura on the caster (not passive: a passive aura is never sent to the client).
        fuse = self.spells[FUSE]
        self.assertEqual(fuse["duration_ms"], -1)
        self.assertEqual(fuse["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(_raw(fuse, "SpellVisualID_1"), 791)
        self.assertFalse(fuse["attributes"] & 0x00000040)       # SPELL_ATTR0_PASSIVE
        # Self looks: the smoke bomb, the leap's animation, the sheep's wind-up.
        for spell_id, visual in ((SMOKE_BOMB, 804), (LEAP, 12305), (SHEEP_WINDUP, 88)):
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), visual, spell_id)
            self.assertEqual(self.spells[spell_id]["effect1"]["type"], DUMMY_EFFECT, spell_id)

    def test_the_cpp_uses_the_declared_names(self):
        for name in ("SPELL_ZG_NET_TRAP", "SPELL_ZG_NETTED", "SPELL_ZG_KEG_BLAST", "SPELL_ZG_KEG_STUN",
                     "SPELL_ZG_FUSE", "SPELL_ZG_BLAST_LOOK", "SPELL_ZG_MORTAR_SHELL", "SPELL_ZG_MORTAR_LOOK",
                     "SPELL_ZG_SMOKE_BOMB", "SPELL_ZG_LEAP", "SPELL_ZG_SHEEP_BLAST", "SPELL_ZG_SHEEP_WINDUP"):
            self.assertIn(name, self.cpp, name)
        # The registry carries the header's percents, never a literal.
        self.assertIn("kTrapPct(heroic)", self.cpp)
        self.assertIn("kKegPct(heroic)", self.cpp)
        self.assertIn("kMortarPct(IsHeroicMap(me))", self.cpp)
        self.assertIn("kSheepBlastPct", self.cpp)
        self.assertNotIn("\t", self.cpp)


class ZigrisSqlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.header = _header()

    def test_the_texts(self):
        types = {0: 14, 1: 41, 2: 41, 3: 41, 4: 41, 5: 14}      # yells (14) and boss emotes (41)
        for group, text_type in types.items():
            self.assertRegex(self.sql, rf"\({ZIGRIS}, {group}, 0, '[^\n]*', {text_type}, 0, 100, ", group)
        for group in (1, 2, 3, 4):
            self.assertRegex(self.sql, rf"\({ZIGRIS}, {group}, 0, '%s ")      # the emotes name him
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 9736 AND `GroupID` BETWEEN 0 AND 5;", self.sql)
        # The header's group names are those six.
        groups = dict(re.findall(r"TEXT_(\w+)\s*=\s*(\d+),", self.header))
        self.assertEqual(sorted(int(v) for v in groups.values()), [0, 1, 2, 3, 4, 5])

    def test_the_gameobjects(self):
        for entry, display in GAMEOBJECTS.items():
            self.assertRegex(self.sql, rf"\({entry}, 5, {display}, '")
            self.assertIn(f"({entry}, 0, 16, 0, 0, 0, 0, 0, 0)", self.sql)      # not selectable
        self.assertIn("ON DUPLICATE KEY UPDATE", self.sql)
        rework = REWORK.read_text(encoding="utf-8")
        for name, entry in (("GO_BRS_SUPPLY_CRATE", 301252), ("GO_BRS_NET_TRAP", 301253),
                            ("GO_BRS_POWDER_KEG", 301254)):
            self.assertRegex(rework, rf"{name}\s*=\s*{entry},")

    def test_the_crates_stand_at_the_header_spots(self):
        rework = REWORK.read_text(encoding="utf-8")
        block = re.search(r"kZigrisCrates\{(.*?)\}\s*\};", rework, re.S)
        self.assertIsNotNone(block)
        spots = [(float(x), float(y)) for x, y in re.findall(r"\{\s*(-?[\d.]+)f,\s*(-?[\d.]+)f\s*\}", block.group(1))]
        self.assertEqual(len(spots), 3)
        z = [float(v) for v in re.search(r"kCrateZ\{\s*\{\s*([\d.f, ]+)\}\s*\}", self.header).group(1)
             .replace("f", "").split(",")]
        rows = re.findall(r"\((\d+), 301252, 229, 0, 0, (\d+), 1, (-?[\d.]+), (-?[\d.]+), (-?[\d.]+), ", self.sql)
        self.assertEqual(len(rows), 3)
        for (guid, mask, x, y, zz), spot, height in zip(rows, spots, z):
            self.assertEqual(int(mask), 3)          # normal and heroic
            self.assertAlmostEqual(float(x), spot[0], places=1)
            self.assertAlmostEqual(float(y), spot[1], places=1)
            self.assertAlmostEqual(float(zz), height, places=1)
            self.assertIn(int(guid), (3012520, 3012521, 3012522))
        self.assertIn("DELETE FROM `gameobject` WHERE `id` = 301252 AND `guid` IN (3012520, 3012521, 3012522);",
                      self.sql)

    def test_the_rev_leaves_the_stock_rows_alone(self):
        # Zigris has no SmartAI to drop, and the rev never touches his loot or his spawn.
        self.assertNotIn("smart_scripts", self.sql)
        self.assertNotIn("creature_loot_template", self.sql)
        self.assertNotIn("UPDATE `creature`", self.sql)


if __name__ == "__main__":
    unittest.main()
