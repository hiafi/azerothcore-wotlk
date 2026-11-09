"""
Stratholme build WP-S10, Baroness Anastari: source/npcs/stratholme/baroness_anastari.py against its C++
(modules/mod-dungeon-bosses src/Stratholme/BaronessLogic.h, boss_baroness_anastari_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in the Baroness's slice (206625-206644) and BaronessLogic.h names the same ids; she declares no
    creature;
  - Keened lasts the build spec's 6 s, Death's Echo 45 s with no cap, both debuffs that nothing dispels, with the
    CHANGE_MAP aura interrupt flag; the Death Knell is the script's share (base point 0), Shadow, ignoring caster
    modifiers;
  - the cast bars are 3 s (Wail), 2 s and 1.5 s (Visage) and not interruptible; the Lament is a real 2.5 s cast that a
    kick or a silence stops;
  - the Wail, its echo and the Visage hits are resolve copies bound to spell_boss_mechanics_resolve;
  - the heroic echo's hit is a hidden 8 / 60 yd donut, drawn by a separate 8 / 32 yd Decoy (F-1 ruling);
  - Terrified is a 2 s mechanic-Fear aura that is not a cure target;
  - the looks are WP-V-1's picks;
  - 10436 is bound to boss_baroness_anastari_rework with SmartAI off, HealthModifier 71.76, DamageModifier 3.5 and
    immunity set 1972;
  - the SQL rev gives her the six build spec lines (yells 14, mechanic emotes 41).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_stratholme_baroness.py
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
HEADER = MODULE_DIR / "BaronessLogic.h"
SCRIPT = MODULE_DIR / "boss_baroness_anastari_rework.cpp"
SQL_REV = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_baroness_stratholme.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "stratholme"

SLICE = range(206625, 206645)
(KEENED, DEATH_KNELL, DEATHS_ECHO, WAIL_BAR, WAIL_HIT, TERRIFIED, WAIL_ECHO_HIT, VISAGE_BAR, VISAGE_BAR_HEROIC,
 VISAGE_HIT, LAMENT) = range(206625, 206636)
BARONESS = 10436

SCHOOL_SHADOW = 32
SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT = 2, 6, 3
AURA_DUMMY, AURA_MOD_FEAR = 4, 7
MECHANIC_FEAR = 5
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
AURA_INTERRUPT_CHANGE_MAP = 0x00080000
RESOLVE = "spell_boss_mechanics_resolve"

# The picks of source/npcs/stratholme/_visuals.py (handoff s3.10, V-1).
LOOKS = {
    KEENED: 90506,          # SV_KEENED_SKULL_STATE
    DEATH_KNELL: 45,        # BA_DEATH_KNELL
    WAIL_BAR: 569,          # BA_BANSHEE_SHRIEK
    WAIL_HIT: 4341,         # BA_WAIL
    TERRIFIED: 4801,        # BA_TERRIFIED
    WAIL_ECHO_HIT: 4341,
    VISAGE_BAR: 7945,       # BA_VISAGE
    VISAGE_BAR_HEROIC: 7945,
    VISAGE_HIT: 7945,       # BA_WAIL_ALT
    LAMENT: 4341,
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


def _raw(spell: dict, column: str) -> int:
    return int((spell.get("raw_overrides") or {}).get(column, 0) or 0)


def _header_int(name: str) -> int:
    match = re.search(rf"{name}\s*=\s*(-?\d+)", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return int(match.group(1))


def _header_float(name: str) -> float:
    match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f?;", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return float(match.group(1))


def _header_pair(name: str) -> tuple[int, int]:
    match = re.search(rf"{name}\{{\s*(\d+),\s*(\d+)\s*\}}", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return int(match.group(1)), int(match.group(2))


class BaronessDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = [e for e in reg.creature_template_edits if int(e["entry"]) == BARONESS]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(KEENED, LAMENT + 1)))
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"spell": mine}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_BA_\w+\s*=\s*kSpellSlice\.first \+ (\d+)", self.header)}
        self.assertEqual({KEENED + n for n in header_ids}, set(mine))
        self.assertTrue(all(i in SLICE for i in mine))
        # The possession loop is retired, never re-declared; the stock Wail is the one she keeps.
        for retired in (16867, 18327, 17244, 17246, 17250):
            self.assertNotIn(retired, self.spells)
        self.assertIn("SPELL_BANSHEE_WAIL", self.cpp)

    def test_keened_and_the_echo(self):
        keened = self.spells[KEENED]
        self.assertEqual(keened["duration_ms"], _header_pair("kKeenMs")[0])
        self.assertEqual(keened["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(keened["dispel"], 0)
        self.assertEqual(_raw(keened, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)
        # Heroic 5 s: the script shortens the aura at the cast.
        self.assertEqual(_header_pair("kKeenMs"), (6000, 5000))
        self.assertIn("aura->SetMaxDuration", self.cpp)
        echo = self.spells[DEATHS_ECHO]
        self.assertEqual(echo["duration_ms"], _header_int("kEchoDurationMs"))
        self.assertEqual(echo["duration_ms"], 45000)
        self.assertEqual(echo["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(echo["dispel"], 0)
        self.assertEqual(_raw(echo, "CumulativeAura"), 255)       # no cap
        self.assertEqual(_raw(echo, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)
        for spell_id in (KEENED, DEATHS_ECHO):
            self.assertEqual(self.spells[spell_id]["school"], SCHOOL_SHADOW)

    def test_the_death_knell_is_the_scripts_share(self):
        knell = self.spells[DEATH_KNELL]
        self.assertEqual(knell["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertEqual(knell["school"], SCHOOL_SHADOW)
        self.assertEqual(knell["effect1"]["base_points"], 0)
        self.assertEqual(knell["effect1"].get("die_sides", 0), 0)
        self.assertTrue(_raw(knell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertIn("SPELL_BA_DEATH_KNELL, SPELLVALUE_BASE_POINT0", self.cpp)
        self.assertIn("WeightedShares(me, takers,", self.cpp)

    def test_cast_bars_and_the_lament(self):
        self.assertEqual(self.spells[WAIL_BAR]["cast_time_ms"], _header_int("kWailCastMs"))
        self.assertEqual(self.spells[VISAGE_BAR]["cast_time_ms"], _header_pair("kVisageCastMs")[0])
        self.assertEqual(self.spells[VISAGE_BAR_HEROIC]["cast_time_ms"], _header_pair("kVisageCastMs")[1])
        self.assertEqual(self.spells[VISAGE_BAR_HEROIC]["cast_time_ms"], 1500)
        for spell_id in (WAIL_BAR, VISAGE_BAR, VISAGE_BAR_HEROIC):
            self.assertEqual(_raw(self.spells[spell_id], "InterruptFlags"), 0)
            self.assertEqual(_raw(self.spells[spell_id], "PreventionType"), 0)
        lament = self.spells[LAMENT]
        self.assertEqual(lament["cast_time_ms"], _header_int("kLamentCastMs"))
        self.assertEqual(lament["cast_time_ms"], 2500)
        self.assertEqual(_raw(lament, "InterruptFlags"), 15)
        self.assertEqual(_raw(lament, "PreventionType"), 1)
        self.assertEqual(lament["effect1"]["type"], DUMMY_EFFECT)
        # The descriptor's interrupt list and the lament's completion hook.
        self.assertIn("SPELL_BA_LAMENT, 3, Ms(kLament.every)", self.cpp)
        self.assertIn("void OnSpellCast(SpellInfo const* spell) override", self.cpp)

    def test_hits_are_resolve_copies(self):
        for spell_id in (WAIL_HIT, WAIL_ECHO_HIT, VISAGE_HIT):
            hit = self.spells[spell_id]
            self.assertEqual(hit["effect1"]["type"], SCHOOL_DAMAGE)
            self.assertEqual(hit["school"], SCHOOL_SHADOW)
            self.assertTrue(_raw(hit, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
            self.assertIn((spell_id, RESOLVE), self.scripts)
        self.assertIn("Spell(SPELL_BA_WAIL_HIT)", self.cpp)
        self.assertIn("Spell(SPELL_BA_WAIL_ECHO_HIT)", self.cpp)
        self.assertIn("Spell(SPELL_BA_VISAGE_HIT)", self.cpp)
        # Weakened on the Visage only (ST: the Wail and its echo are over 30%, no Weakened).
        visage = re.search(r"Spell\(SPELL_BA_VISAGE_HIT\)\s*\.Weakened\(\)", self.cpp)
        self.assertIsNotNone(visage)
        self.assertNotRegex(self.cpp, r"Spell\(SPELL_BA_WAIL_HIT\)\s*\.Weakened")
        self.assertNotRegex(self.cpp, r"Spell\(SPELL_BA_WAIL_ECHO_HIT\)\s*\.Weakened")
        # Every hit carries the Terrified rider.
        self.assertEqual(self.cpp.count("Rider(SPELL_BA_TERRIFIED)"), 3)

    def test_the_echo_is_a_hidden_hit_and_a_drawn_decoy(self):
        # F-1 ruling (R-1-A M-1): the hit reaches everyone beyond 8 yd (a hidden 8 / 60 donut); the drawn 8 / 32
        # donut is a Decoy that hits nobody (the marker's hole needs an inner / outer ratio of 0.25 or more).
        self.assertEqual(_header_float("kWailEchoInner"), 8.0)
        self.assertEqual(_header_float("kWailEchoReachYd"), 60.0)
        self.assertEqual(_header_float("kWailEchoDrawnOuter"), 32.0)
        self.assertGreaterEqual(_header_float("kWailEchoInner") / _header_float("kWailEchoDrawnOuter"), 0.25)
        self.assertRegex(self.cpp, r"Donut\(me, me, kWailEchoInner, kWailEchoDrawnOuter, [^;]*;\s*"
                                   r"drawn\.Decoy\(\)")
        hit = re.search(r"Donut\(me, me, kWailEchoInner, kWailEchoReachYd, [^;]*;\s*ref\.([^;]*);", self.cpp)
        self.assertIsNotNone(hit)
        self.assertIn("Spell(SPELL_BA_WAIL_ECHO_HIT)", hit.group(1))
        self.assertIn(".NoTelegraph()", hit.group(1))
        self.assertNotIn("Decoy", hit.group(1))

    def test_terrified_is_a_two_second_fear(self):
        fear = self.spells[TERRIFIED]
        self.assertEqual(fear["duration_ms"], _header_int("kTerrifiedMs"))
        self.assertEqual(fear["duration_ms"], 2000)
        self.assertEqual(fear["mechanic"], MECHANIC_FEAR)
        self.assertEqual(fear["effect1"]["apply_aura"], AURA_MOD_FEAR)
        self.assertEqual(fear["effect1"]["mechanic"], MECHANIC_FEAR)
        self.assertEqual(fear["dispel"], 0)
        # A fear break is a reward: it must not ignore immunities.
        self.assertFalse(fear.get("attributes", 0) & 0x20000000)

    def test_looks_are_the_visual_picks(self):
        for spell_id, visual in LOOKS.items():
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), visual, spell_id)

    def test_the_baroness_is_bound(self):
        self.assertEqual(len(self.edits), 1)
        edit = self.edits[0]
        self.assertEqual(edit["ScriptName"], "boss_baroness_anastari_rework")
        self.assertEqual(edit["AIName"], "")
        self.assertEqual(edit["HealthModifier"], 71.76)
        self.assertEqual(edit["DamageModifier"], 3.5)
        self.assertEqual(edit["CreatureImmunitiesId"], 1972)
        self.assertEqual(edit["flags_extra"] & 0x1, 0x1)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_baroness_anastari_rework", self.cpp)
        # 170k on the level 59 paladin base 2,369.
        self.assertAlmostEqual(71.76 * 2369, 170_000, delta=100)

    def test_her_texts(self):
        text = SQL_REV.read_text(encoding="utf-8")
        rows = re.findall(r"^\(10436, (\d+), 0, '((?:[^'\\]|\\.)*)', (\d+),", text, re.M)
        self.assertEqual([int(r[0]) for r in rows], [0, 1, 2, 3, 4, 5])
        types = {int(r[0]): int(r[2]) for r in rows}
        self.assertEqual(types, {0: 14, 1: 41, 2: 41, 3: 41, 4: 14, 5: 14})
        by_group = {int(r[0]): r[1] for r in rows}
        self.assertEqual(by_group[1], "%s keens for $n!")
        self.assertEqual(by_group[2], "%s begins to wail!")
        self.assertEqual(by_group[3], "%s lifts her veil toward $n.")
        self.assertEqual(by_group[4], "Weep for the living!")
        # The enum in StratholmeRework.h numbers the same groups.
        for name, group in (("YELL_BARONESS_AGGRO", 0), ("EMOTE_BARONESS_KEEN", 1), ("EMOTE_BARONESS_WAIL", 2),
                            ("EMOTE_BARONESS_VEIL", 3), ("YELL_BARONESS_LAMENT", 4), ("YELL_BARONESS_DEATH", 5)):
            match = re.search(rf"{name}\s*=\s*(\d+)", (MODULE_DIR / "StratholmeRework.h").read_text(encoding="utf-8"))
            self.assertIsNotNone(match, name)
            self.assertEqual(int(match.group(1)), group, name)
        # She had no smart_scripts rows: the rev removes none, and says so.
        self.assertNotIn("DELETE FROM `smart_scripts`", text)


if __name__ == "__main__":
    unittest.main()
