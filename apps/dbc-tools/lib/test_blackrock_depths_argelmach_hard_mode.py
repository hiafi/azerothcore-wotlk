"""
Blackrock Depths build WP-D16, Golem Lord Argelmach's hard mode (the Prototype):
source/npcs/blackrock_depths/argelmach_hard_mode.py against its C++ (modules/mod-dungeon-bosses
src/BlackrockDepths/ArgelmachHardModeLogic.h, argelmach_hard_mode.cpp) and its SQL rev.

Checks (the declarations directly: none of them waits for BIND_WAVE_2):
  - the spells sit in the Prototype's slice (211370-211409) and ArgelmachHardModeLogic.h names the same ids;
  - Magmatron 300836: 100,000 health at level 55, elite mechanical of his faction, stun immunity, no loot or XP, its
    heroic entry 310413 (and WP-H's 100k), display 8179, bound to D15's golem AI; the Salvaged Core 300838: a helper
    with no heroic template, bound to the same AI;
  - the registry hits are Fire resolve copies the C++ names; the two bars are Fire, not kickable, as long as the
    header's timers; the looks are V-1's molten fire, never a look VISUALS calls WRONG;
  - the SQL rev: text group 4 (a yell), the console and the fourth pedestal (templates, heroic-only spawns at the
    header's spots, the console's script registered by the C++);
  - the C++ registers the hard mode factory, the idle hook and the console; the tags are the ones D15 reserved.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_argelmach_hard_mode.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockDepths"
HEADER = MODULE_DIR / "ArgelmachHardModeLogic.h"
D15_HEADER = MODULE_DIR / "ArgelmachLogic.h"
REWORK = MODULE_DIR / "BlackrockDepthsRework.h"
SCRIPT = MODULE_DIR / "argelmach_hard_mode.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_argelmach_hard_mode_blackrock_depths.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_depths"
HEROIC_SOURCE = TOOL_ROOT / "source" / "world" / "dungeons" / "blackrock_depths.py"

SLICE = range(211370, 211410)
(INCINERATION, INCINERATION_HIT, INCINERATION_LOOK, CLOUD_BURST, FLAMETHROWER, FLAMETHROWER_HIT, FLAMETHROWER_LOOK,
 CORE_LOOK) = range(211370, 211378)
MAGMATRON = 300836
CORE = 300838
MAGMATRON_HEROIC = 310413
WARRIOR_55_BASE = 2614

SCHOOL_DAMAGE, DUMMY_EFFECT, APPLY_AURA = 2, 3, 6
AURA_DUMMY = 4
SCHOOL_FIRE = 4
RESOLVE = "spell_boss_mechanics_resolve"
IMMUNITY_BOSS_STUN = 1972
FACTION_DARK_IRON = 54
NOT_SELECTABLE = 0x02000000
GOLEM_AI = "npc_brd_argelmach_golem"
CONSOLE_SCRIPT = "go_brd_activation_console"
# VISUALS-REPORT's WRONG looks this fight must never wire (lib/test_blackrock_depths_vfx.py holds the full list).
WRONG = {13174: "Activate Construct (a fire strike)", 11840: "Living Bomb (a fire whirl)",
         10407: "Chemical Flames (fel green)"}
HEAT_WAVE, FIRE_NOVA = 3119, 6899


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
    return (spell.get("raw_overrides") or {}).get(column, 0) or 0


def _header() -> str:
    return HEADER.read_text(encoding="utf-8")


def _header_value(name: str) -> float:
    match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f?;", _header())
    assert match, name
    return float(match.group(1))


def _point(text: str, name: str) -> tuple[float, float, float]:
    match = re.search(rf"\b{name}\{{\s*([\d.-]+)f,\s*([\d.-]+)f,\s*([\d.-]+)f\s*\}};", text)
    assert match, name
    return tuple(float(v) for v in match.groups())


class PrototypeDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) in (MAGMATRON, CORE)}
        cls.models = {int(e["CreatureID"]): int(e["CreatureDisplayID"]) for e in reg.creature_template_models
                      if int(e["CreatureID"]) in (MAGMATRON, CORE)}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.sql = SQL.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(INCINERATION, CORE_LOOK + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"spell": mine}), [])
        found = re.search(r"kSpellsPrototype\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(found)
        self.assertEqual((int(found.group(1)), int(found.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_PT_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))

    def test_magmatron(self):
        row = self.creatures[MAGMATRON]
        self.assertEqual(row["name"], "Magmatron")
        self.assertEqual(row["ScriptName"], GOLEM_AI)
        self.assertEqual(row["AIName"], "")
        self.assertEqual((row["minlevel"], row["maxlevel"], row["rank"]), (55, 55, 1))
        self.assertEqual(row["type"], 9)                            # mechanical
        self.assertEqual(row["faction"], FACTION_DARK_IRON)
        self.assertEqual(row["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
        self.assertEqual(row["unit_flags"], 0)                      # the script makes the statue unselectable
        self.assertEqual(row["lootid"], 0)
        self.assertEqual(float(row["ExperienceModifier"]), 0.0)
        self.assertEqual(math.ceil(WARRIOR_55_BASE * float(row["HealthModifier"])),
                         int(_header_value("kMagmatronHealth")))
        self.assertEqual(row["difficulty_entry_1"], MAGMATRON_HEROIC)
        self.assertEqual(self.models[MAGMATRON], 8179)
        # WP-H's heroic row carries the same 100k.
        self.assertRegex(HEROIC_SOURCE.read_text(encoding="utf-8"), r"300836: dict\(health=100_000\)")

    def test_the_statue_is_dormant_by_state_and_wears_the_copy(self):
        # R-2-A MA-1: the stock Stoned never landed (immunity 1972 drops FREEZE), so an aura-keyed IsDormant re-summoned
        # the statue every second and left it after a kill. Dormancy is the statue's own state; the look is D15's copy.
        self.assertIn("StatueDormant(golem->IsAlive(), golem->IsInCombat(), "
                      "golem->HasUnitFlag(UNIT_FLAG_NOT_SELECTABLE))", self.cpp)
        self.assertNotIn("kSpellStoned", self.cpp)
        self.assertIn("golem->AddAura(BrdArgelmach::SPELL_AR_STATUE, golem);", self.cpp)
        self.assertIn("magmatron->RemoveAurasDueToSpell(BrdArgelmach::SPELL_AR_STATUE);", self.cpp)
        self.assertIn("LacksAura(BrdArgelmach::SPELL_AR_STATUE)", self.cpp)
        self.assertIn("constexpr bool StatueDormant(", HEADER.read_text(encoding="utf-8"))

    def test_the_salvaged_core(self):
        row = self.creatures[CORE]
        self.assertEqual(row["name"], "Salvaged Core")
        self.assertEqual(row["ScriptName"], GOLEM_AI)
        self.assertTrue(int(row["unit_flags"]) & NOT_SELECTABLE)
        self.assertEqual(row.get("difficulty_entry_1", 0), 0)      # no heroic template (handoff 7 #2)
        self.assertEqual(self.models[CORE], 11686)
        self.assertIn("NPC_BRD_SALVAGED_CORE", self.cpp)

    def test_the_registry_hits_are_fire_resolve_copies(self):
        for spell_id, name in ((INCINERATION_HIT, "SPELL_PT_INCINERATION_HIT"),
                               (CLOUD_BURST, "SPELL_PT_CLOUD_BURST"),
                               (FLAMETHROWER_HIT, "SPELL_PT_FLAMETHROWER_HIT")):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertEqual(spell["school"], SCHOOL_FIRE, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
            self.assertRegex(self.cpp, rf"(spellId = |\.Spell\(){name}\b")
        # The bursts and the cone carry Weakened; Incineration's 15% does not; the cone burns Poison Mist off.
        # the tank takes the same percent of the tank row (the TankDamage convention, ORCH-NOTES 2026-11-17)
        self.assertRegex(self.cpp, r"\.Damage\(kBurstPct\)\.TankDamage\(kBurstPct\)\s*\.Spell\(SPELL_PT_CLOUD_BURST\)"
                                   r"\.Weakened\(\)")
        self.assertRegex(self.cpp, r"\.Damage\(kFlamePct\)\.TankDamage\(kFlamePct\)\s*"
                                   r"\.Spell\(SPELL_PT_FLAMETHROWER_HIT\)\.Weakened\(\)")
        self.assertIn("RemoveAurasDueToSpell(BrdArgelmach::SPELL_AR_POISON_MIST)", self.cpp)

    def test_the_bars_cannot_be_kicked(self):
        for spell_id, ms in ((INCINERATION, "kIncinerationCastMs"), (FLAMETHROWER, "kFlameWarnMs")):
            bar = self.spells[spell_id]
            self.assertEqual(bar["cast_time_ms"], int(_header_value(ms)))
            self.assertEqual(bar["school"], SCHOOL_FIRE)             # the kick (Chain Lightning) is Nature: rule 5
            self.assertEqual(_raw(bar, "InterruptFlags"), 0)
            self.assertEqual(_raw(bar, "PreventionType"), 0)
            self.assertEqual(bar["effect1"]["type"], DUMMY_EFFECT)

    def test_the_looks(self):
        for spell_id, spell in self.spells.items():
            visual = int(_raw(spell, "SpellVisualID_1"))
            self.assertNotIn(visual, WRONG, f"{spell_id}: {WRONG.get(visual)}")
        self.assertEqual(_raw(self.spells[INCINERATION_LOOK], "SpellVisualID_1"), FIRE_NOVA)
        self.assertEqual(_raw(self.spells[FLAMETHROWER_LOOK], "SpellVisualID_1"), HEAT_WAVE)
        core = self.spells[CORE_LOOK]
        self.assertNotEqual(_raw(core, "SpellVisualID_1"), 0)
        self.assertEqual(core["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(core["duration_ms"], -1)

    def test_the_sql_rev(self):
        sql = self.sql
        self.assertRegex(sql, r"\(8983, 4, 0, 'The prototype\? Oh, you will regret that\.', 14,")
        self.assertEqual(len(re.findall(r"^\(8983, \d+,", sql, re.M)), 1)
        self.assertIn("WHERE `CreatureID` = 8983 AND `GroupID` = 4;", sql)
        self.assertEqual(int(re.search(r"\bYELL_AR_CONSOLE\s*=\s*(\d+),", D15_HEADER.read_text(encoding="utf-8"))
                             .group(1)), 4)
        # The console (a goober with its script) and the fourth pedestal (as D15's three).
        self.assertRegex(sql, rf"\(301284, 10, 6424, 'Activation Console',[^\n]*\n[^\n]*'{CONSOLE_SCRIPT}', 0\)")
        self.assertRegex(sql, r"\(301288, 5, 3311, 'Golem Pedestal', '', '', '', 0\.5,")
        self.assertIn("(301288, 0, 16, 0, 0, 0, 0, 0, 0)", sql)            # not selectable
        self.assertIn(f"RegisterDungeonReworkGameObjectAI({CONSOLE_SCRIPT},", self.cpp)
        # Heroic-only spawns (spawnMask 2) at the headers' spots.
        x, y, z = _point(_header(), "kConsole")
        self.assertRegex(sql, rf"\(3012840, 301284, 230, 0, 0, 2, 1, {x:g}, {y:g}, {z:g},")
        x, y, z = _point(D15_HEADER.read_text(encoding="utf-8"), "kPedestal4")
        self.assertRegex(sql, rf"\(3012880, 301288, 230, 0, 0, 2, 1, {x:g}, {y:g}, {z:g},")
        # The rotations are the orientations about z.
        for o, r2, r3 in re.findall(r", -?[\d.]+, ([\d.]+), 0, 0, (-?[\d.]+), (-?[\d.]+), 300, 255, 1,", sql):
            self.assertAlmostEqual(math.sin(float(o) / 2), float(r2), places=4)
            self.assertAlmostEqual(math.cos(float(o) / 2), float(r3), places=4)

    def test_the_hooks_and_tags(self):
        self.assertIn("BrdArgelmach::RegisterArgelmachHardMode(", self.cpp)
        self.assertIn("BrdArgelmach::RegisterArgelmachIdleHook(", self.cpp)
        self.assertIn('BrdTest::RegisterBoss("prototype", ', self.cpp)
        d15 = D15_HEADER.read_text(encoding="utf-8")
        self.assertRegex(d15, r"TAG_AR_INCINERATION\s*=\s*6,")
        self.assertRegex(d15, r"TAG_AR_FLAMETHROWER\s*=\s*7,")
        self.assertIn("kTagIncineration = BrdArgelmach::TAG_AR_INCINERATION;", _header())
        self.assertIn("kTagFlamethrower = BrdArgelmach::TAG_AR_FLAMETHROWER;", _header())
        # The hard mode's health and the wake thresholds (S3 tuning table, AR4 hard).
        self.assertEqual(int(_header_value("kBossHealth")), 500_000)
        self.assertEqual(int(_header_value("kGolemHealth")), 50_000)
        self.assertRegex(_header(), r"kWakePct\{ 80\.f, 60\.f, 40\.f \}")


if __name__ == "__main__":
    unittest.main()
