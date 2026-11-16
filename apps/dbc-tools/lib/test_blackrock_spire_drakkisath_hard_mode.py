"""
Blackrock Spire build WP-B15, General Drakkisath's hard mode (the General's Army):
source/npcs/blackrock_spire/drakkisath_hard_mode.py against its C++ (modules/mod-dungeon-bosses
src/BlackrockSpire/DrakkisathHardModeLogic.h, drakkisath_hard_mode.cpp) and its SQL rev.

Checks:
  - the spells sit in its slice (210560-210619) and DrakkisathHardModeLogic.h names the same ids;
  - the squads 300736-300739 are level 60 elite dragonkin copies on npc_brs_army_soldier at the hard mode's health at 5
    players, naming WP-H's predicted heroic entries; the herald 300740 is a friendly gossip unit on menu 300740; the
    ring's carrier 300741 is an invisible helper; every script name is registered behind kWave2Bound;
  - the ring's strike is an INSTAKILL bound to the kit's lethal strike; its look is a 12 yd dynamic object (and the
    fallback state is V-2's minted ring);
  - the hits are resolve copies of the right school; the bars match the header and only the Fire Tongue's volley is
    interruptible (bound to its landing script);
  - Finesse, Humbled, Trophy and the Captain's command carry the header's percents and stacks;
  - the SQL rev writes Drakkisath's line 9 and the herald's line 0 (never Nefarius's 18-19, B12's), the gossip, the
    option's conditions, the squads' weapons and a heroic-only herald spawn.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_spire_drakkisath_hard_mode.py
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
HEADER = MODULE_DIR / "DrakkisathHardModeLogic.h"
SCRIPT = MODULE_DIR / "drakkisath_hard_mode.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_drakkisath_hard_mode_blackrock_spire.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_spire"

SLICE = range(210560, 210620)
(RING_STRIKE, RING_LOOK, RING_LOOK_ALT, CHALLENGE_BAR, CHALLENGER, SWEEP, CLEAVE, FIRE_BLAST, RING_OF_FLAME, CLAP,
 FIRE_BLAST_LOOK, RING_OF_FLAME_LOOK, FINESSE, HUMBLED, TROPHY, CC_BAR, CC, CC_LOOK, COMMAND, COMMAND_LOOK, SCATTER,
 SCATTER_MARK, VOLLEY, VOLLEY_HIT, SHIELD_FRONT, SC_BAR, SC) = range(210560, 210587)
DRAGONSPAWN, CAPTAIN, FIRE_TONGUE, DRAGON_GUARD, HERALD, RING = range(300736, 300742)
SQUADS = {DRAGONSPAWN: (17_000, 310297), CAPTAIN: (23_000, 310298), FIRE_TONGUE: (13_000, 310299),
          DRAGON_GUARD: (21_000, 310300)}
WARRIOR_60_BASE = 3052

SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT, INSTAKILL, PERSISTENT_AREA_AURA = 2, 6, 3, 1, 27
AURA_DUMMY, AURA_MOD_DAMAGE_PERCENT_TAKEN, AURA_MOD_DAMAGE_PERCENT_DONE = 4, 87, 79
SCHOOL_PHYSICAL, SCHOOL_FIRE = 1, 4         # school masks
RESOLVE = "spell_boss_mechanics_resolve"
SV_RING_OF_FIRE_STATE, SV_RING_OF_FIRE = 90616, 8386


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


class GeneralsArmyDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(c["entry"]): c for c in reg.creature_templates if DRAGONSPAWN <= int(c["entry"]) <= RING}
        cls.models = {int(m["CreatureID"]): m for m in reg.creature_template_models
                      if DRAGONSPAWN <= int(m["CreatureID"]) <= RING}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(RING_STRIKE, SC + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_spire", {"spell": mine}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_GA_\w+\s*=\s*(2105\d\d)", _header())}
        self.assertEqual(header_ids, set(mine))

    def test_the_creatures(self):
        self.assertEqual(sorted(self.creatures), list(range(DRAGONSPAWN, RING + 1)))
        for entry, (health, heroic) in SQUADS.items():
            with self.subTest(entry=entry):
                c = self.creatures[entry]
                self.assertEqual(c["ScriptName"], "npc_brs_army_soldier")
                self.assertEqual(c["AIName"], "")
                self.assertEqual((int(c["minlevel"]), int(c["maxlevel"]), int(c["rank"])), (60, 60, 1))
                self.assertEqual(int(c["type"]), 2)
                self.assertLessEqual(abs(math.ceil(WARRIOR_60_BASE * float(c["HealthModifier"])) - health), 1)
                self.assertEqual(int(c["difficulty_entry_1"]), heroic)
                self.assertIn(entry, self.models)
        herald = self.creatures[HERALD]
        self.assertEqual(herald["ScriptName"], "npc_brs_generals_herald")
        self.assertEqual(int(herald["gossip_menu_id"]), 300740)
        self.assertEqual(int(herald["npcflag"]) & 1, 1)
        self.assertEqual(int(herald["faction"]), 35)
        self.assertEqual(int(herald["difficulty_entry_1"]), 0)
        ring = self.creatures[RING]
        self.assertEqual(ring["ScriptName"], "npc_brs_challenge_ring")
        self.assertEqual(int(ring["unit_flags"]) & 0x02000000, 0x02000000)    # not selectable
        self.assertEqual(int(self.models[RING]["CreatureDisplayID"]), 11686)
        for script in ("npc_brs_army_soldier", "npc_brs_generals_herald", "npc_brs_challenge_ring"):
            self.assertRegex(self.cpp, rf"if \(kWave2Bound\)\s*RegisterDungeonReworkCreatureAI\({script},")
        # The health the script sets equals the declaration (the header's 5-player values).
        for entry, name in ((DRAGONSPAWN, "kDragonspawnHealthAt5"), (CAPTAIN, "kCaptainHealthAt5"),
                            (FIRE_TONGUE, "kFireTongueHealthAt5"), (DRAGON_GUARD, "kDragonGuardHealthAt5")):
            self.assertEqual(int(_header_value(name)), SQUADS[entry][0])

    def test_the_ring(self):
        strike = self.spells[RING_STRIKE]
        self.assertEqual(int(strike["effect1"]["type"]), INSTAKILL)
        self.assertIn((RING_STRIKE, "spell_dungeon_lethal_strike"), self.scripts)
        look = self.spells[RING_LOOK]
        self.assertEqual(int(look["effect1"]["type"]), PERSISTENT_AREA_AURA)
        self.assertEqual(float(look["effect1"]["radius_yards"]), 12.0)
        self.assertEqual(int(look["duration_ms"]), int(_header_value("kChallengeMs")))
        self.assertEqual(_raw(look, "SpellVisualID_1"), SV_RING_OF_FIRE)
        self.assertEqual(_raw(self.spells[RING_LOOK_ALT], "SpellVisualID_1"), SV_RING_OF_FIRE_STATE)
        self.assertIn("ring.killSpell = SPELL_GA_RING_STRIKE", self.cpp)
        self.assertIn("ring.carrierEntry = NPC_BRS_CHALLENGE_RING", self.cpp)

    def test_the_hits_are_resolve_copies(self):
        for sid, school in ((SWEEP, SCHOOL_PHYSICAL), (CLEAVE, SCHOOL_PHYSICAL), (FIRE_BLAST, SCHOOL_FIRE),
                            (RING_OF_FLAME, SCHOOL_FIRE), (CLAP, SCHOOL_PHYSICAL), (CC, SCHOOL_PHYSICAL),
                            (SCATTER, SCHOOL_FIRE), (VOLLEY_HIT, SCHOOL_FIRE), (SC, SCHOOL_PHYSICAL)):
            with self.subTest(sid=sid):
                self.assertIn((sid, RESOLVE), self.scripts)
                self.assertEqual(int(self.spells[sid]["school"]), school)
                self.assertEqual(int(self.spells[sid]["effect1"]["type"]), SCHOOL_DAMAGE)

    def test_the_bars(self):
        for sid, name in ((CHALLENGE_BAR, "kChallengeMs"), (CC_BAR, "kCleavingChargeCastMs"),
                          (SC_BAR, "kShieldChargeCastMs"), (VOLLEY, "kVolleyCastMs")):
            with self.subTest(sid=sid):
                self.assertEqual(int(self.spells[sid]["cast_time_ms"]), int(_header_value(name)))
        for sid in (CHALLENGE_BAR, CC_BAR, SC_BAR):
            self.assertEqual(_raw(self.spells[sid], "InterruptFlags"), 0)
            self.assertEqual(int(self.spells[sid]["school"]), SCHOOL_PHYSICAL)
        # His duel bar is Physical: a kick on his Fire Flamestrike never locks it.
        self.assertEqual(_raw(self.spells[VOLLEY], "InterruptFlags"), 15)
        self.assertEqual(_raw(self.spells[VOLLEY], "PreventionType"), 1)
        self.assertIn((VOLLEY, "spell_brs_army_fireball_volley"), self.scripts)
        self.assertIn("RegisterSpellScript(spell_brs_army_fireball_volley)", self.cpp)

    def test_the_buffs(self):
        for sid, aura, pct, stacks in ((FINESSE, AURA_MOD_DAMAGE_PERCENT_DONE, "kFinessePctPerStack", "kFinesseMax"),
                                       (TROPHY, AURA_MOD_DAMAGE_PERCENT_DONE, "kTrophyPctPerStack", "kTrophyMax"),
                                       (COMMAND, AURA_MOD_DAMAGE_PERCENT_DONE, "kCommandPct", None),
                                       (HUMBLED, AURA_MOD_DAMAGE_PERCENT_TAKEN, "kHumbledPct", None)):
            with self.subTest(sid=sid):
                s = self.spells[sid]
                self.assertEqual(int(s["effect1"]["apply_aura"]), aura)
                self.assertEqual(int(s["effect1"]["base_points"]), int(_header_value(pct)))
                if stacks:
                    self.assertEqual(_raw(s, "CumulativeAura"), _header_value(stacks))
        self.assertEqual(int(self.spells[HUMBLED]["duration_ms"]), int(_header_value("kHumbledMs")))
        self.assertEqual(int(self.spells[COMMAND]["duration_ms"]), int(_header_value("kCommandAuraMs")))
        self.assertGreater(int(self.spells[FINESSE]["duration_ms"]), int(_header_value("kChallengeMs")))
        for sid in (CHALLENGER, SCATTER_MARK, SHIELD_FRONT):
            self.assertEqual(int(self.spells[sid]["effect1"]["apply_aura"]), AURA_DUMMY)
        self.assertEqual(int(self.spells[SCATTER_MARK]["duration_ms"]), int(_header_value("kScatteringWarnMs")))


class GeneralsArmySqlTest(unittest.TestCase):
    def setUp(self):
        self.sql = SQL.read_text(encoding="utf-8")

    def test_the_texts(self):
        self.assertRegex(self.sql, r"\(10363, 9, 0, 'So you are the ones who mocked Lord Victor\.")
        self.assertRegex(self.sql, r"\(300740, 0, 0, '")
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 10363 AND `GroupID` = 9;", self.sql)
        # Nefarius's insult lines are B12's rev: never written here.
        self.assertNotRegex(self.sql, r"\(300732, 1[89], ")

    def test_the_gossip_and_its_conditions(self):
        self.assertIn("(300740, 300740);", self.sql)
        self.assertIn("'Let them come.'", self.sql)
        self.assertIn("The general''s legions await your word.", self.sql)
        rows = re.findall(r"^\(15, 300740, 0, 0, 0, (\d+), 0, (\d+), (\d+), (\d+), (\d),", self.sql, flags=re.M)
        self.assertEqual(set(rows), {("49", "1", "0", "0", "0"), ("13", "30", "1", "0", "0"),
                                     ("13", "34", "0", "0", "0"), ("13", "13", "1", "2", "1"),
                                     ("13", "13", "3", "2", "1")})

    def test_the_spawn_and_the_weapons(self):
        self.assertRegex(self.sql, r"\(3007400, 300740, 229, 0, 0, 2, 1, 0, 5\.0, -320\.0, 111\.04,")
        for entry in (300736, 300737, 300738, 300739):
            self.assertRegex(self.sql, rf"\({entry}, 1, \d+, \d+, 0, 0\)")
        # The spawn matches the header's entrance.
        match = re.search(r"kHeraldEntrance\{ ([\d.-]+)f, ([\d.-]+)f, ([\d.-]+)f \}", _header())
        self.assertEqual(tuple(float(v) for v in match.groups()), (5.0, -320.0, 111.04))


if __name__ == "__main__":
    unittest.main()
