"""
Stratholme build WP-S6, Archivist Galford: source/npcs/stratholme/archivist_galford.py against its C++
(modules/mod-dungeon-bosses src/Stratholme/GalfordLogic.h, boss_archivist_galford_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in Galford's slice (206520-206544), GalfordLogic.h names the same ids, the two stalkers 300606 /
    300607 are invisible unselectable props bound to their NullCreatureAI scripts with no heroic template;
  - Holy Fire is a 6 s periodic Holy burn of 10% (kit percent periodic), no dispel type, dropped on a map change;
  - Pyroblast is a 4 s kickable cast with its own SpellScript, the Fire Nova and Burning Winds bars are not kickable;
  - the landing and the Nova burst are resolve copies; the tick has its own script; Scorched stacks to 20 for 4 s;
  - Kindled is +25% done / -50% taken, 1 s; the looks are V-2's GF_ / SV_HOLYZONE_ picks;
  - the walls strike with the shared 206400 and the gust is cut short of the Pyre (GustDistance in the script);
  - 10811 is bound with SmartAI off, HealthModifier 69.615, DamageModifier 3.5, immunity set 1972;
  - the SQL rev drops the SmartAI rows and gives him the seven build spec lines (yells 14, the Nova emote 41).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_stratholme_galford.py
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
HEADER = MODULE_DIR / "GalfordLogic.h"
SCRIPT = MODULE_DIR / "boss_archivist_galford_rework.cpp"
SQL_REV = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_archivist_galford_stratholme.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "stratholme"

SLICE = range(206520, 206545)
(HOLY_FIRE, LANDING, PYROBLAST, NOVA_CAST, NOVA, NOVA_LOOK, TICK, SCORCHED, KINDLED, WINDS, GUST, LOOK_4, LOOK_5,
 LOOK_6, LOOK_8, WALL_LOOK) = range(206520, 206536)
PUDDLE, WALL = 300606, 300607
GALFORD = 10811

SCHOOL_HOLY, SCHOOL_FIRE = 2, 4
SCHOOL_DAMAGE, APPLY_AURA = 2, 6
AURA_DUMMY, AURA_PERIODIC_DAMAGE, AURA_DONE, AURA_TAKEN = 4, 3, 79, 87
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
AURA_INTERRUPT_CHANGE_MAP = 0x00080000
UNIT_FLAG_NOT_SELECTABLE = 0x02000000
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT_PERIODIC = "spell_dungeon_refflat_periodic"

LOOKS = {
    HOLY_FIRE: 3400, LANDING: 3400, PYROBLAST: 2253, NOVA: 963, NOVA_LOOK: 963, TICK: 7634, KINDLED: 46,
    GUST: 4486, LOOK_4: 90509, LOOK_5: 90510, LOOK_6: 90511, LOOK_8: 90512, WALL_LOOK: 9701,
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


def _header() -> str:
    return HEADER.read_text(encoding="utf-8")


def _header_number(name: str) -> float:
    match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f?;", _header())
    assert match, name
    return float(match.group(1))


def _header_nh(name: str) -> tuple[float, float]:
    match = re.search(rf"\b{name}\{{\s*(-?[\d.]+)f?,\s*(-?[\d.]+)f?\s*\}}", _header())
    assert match, name
    return float(match.group(1)), float(match.group(2))


class GalfordDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) in (PUDDLE, WALL)}
        cls.edits = [e for e in reg.creature_template_edits if int(e["entry"]) == GALFORD]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(HOLY_FIRE, WALL_LOOK + 1)))
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"spell": mine}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_GF_\w+\s*=\s*kSpellSlice\.first \+ (\d+)", _header())}
        self.assertEqual({HOLY_FIRE + n for n in header_ids}, set(mine))
        for retired in (17293, 17366, 17274):
            self.assertNotIn(retired, self.spells)

    def test_the_stalkers(self):
        self.assertEqual(sorted(self.creatures), [PUDDLE, WALL])
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"creature": [PUDDLE, WALL]}), [])
        for entry, script in ((PUDDLE, "npc_st_holy_fire_puddle"), (WALL, "npc_st_pyre_wall")):
            c = self.creatures[entry]
            self.assertTrue(c["unit_flags"] & UNIT_FLAG_NOT_SELECTABLE)
            self.assertEqual(c.get("difficulty_entry_1", 0), 0)
            self.assertEqual(c["ScriptName"], script)
            self.assertEqual(c["lootid"], 0)
            self.assertIn(f"RegisterDungeonReworkCreatureAI({script}", self.cpp)

    def test_holy_fire(self):
        burn = self.spells[HOLY_FIRE]
        self.assertEqual(burn["duration_ms"], int(_header_number("kHolyFireBurnMs")))
        self.assertEqual(burn["dispel"], 0)
        self.assertEqual(burn["school"], SCHOOL_HOLY)
        tick = burn["effect1"]
        self.assertEqual(tick["apply_aura"], AURA_PERIODIC_DAMAGE)
        self.assertEqual(tick["amplitude"], int(_header_number("kHolyFireTickMs")))
        self.assertEqual(tick["base_points"] + 1, int(_header_number("kHolyFireTickHundredths")))
        self.assertEqual(_raw(burn, "EffectMiscValueB_1"), int(_header_number("kHolyFireTickHundredths")))
        self.assertIn((HOLY_FIRE, REFFLAT_PERIODIC), self.scripts)
        self.assertIn((LANDING, RESOLVE), self.scripts)
        self.assertIn("impact.spellId = SPELL_GF_HOLY_FIRE_LANDING", self.cpp)
        self.assertIn("ref.DropSpot(DropRule())", self.cpp)

    def test_casts(self):
        pyro = self.spells[PYROBLAST]
        self.assertEqual(pyro["cast_time_ms"], int(_header_number("kPyroCastMs")))
        self.assertEqual(_raw(pyro, "InterruptFlags"), 15)
        self.assertEqual(_raw(pyro, "PreventionType"), 1)
        self.assertEqual(pyro["school"], SCHOOL_FIRE)
        self.assertIn((PYROBLAST, "spell_st_galford_pyroblast"), self.scripts)
        self.assertIn("RegisterSpellScript(spell_st_galford_pyroblast)", self.cpp)
        self.assertIn("SPELL_GF_PYROBLAST, kPyroKickPriority", self.cpp)
        for bar, name in ((NOVA_CAST, "kNovaCastMs"), (WINDS, "kWindsCastMs")):
            self.assertEqual(self.spells[bar]["cast_time_ms"], int(_header_number(name)))
            self.assertEqual(_raw(self.spells[bar], "InterruptFlags"), 0)
        self.assertIn((NOVA, RESOLVE), self.scripts)

    def test_fire_scorched_kindled(self):
        self.assertIn((TICK, "spell_st_galford_holy_fire_tick"), self.scripts)
        self.assertIn("RegisterSpellScript(spell_st_galford_holy_fire_tick)", self.cpp)
        scorched = self.spells[SCORCHED]
        self.assertEqual(scorched["duration_ms"], int(_header_number("kScorchedFadeMs")))
        self.assertEqual(_raw(scorched, "CumulativeAura"), int(_header_number("kScorchedMaxStacks")))
        kindled = self.spells[KINDLED]
        self.assertEqual(kindled["duration_ms"], int(_header_number("kKindledAuraMs")))
        self.assertEqual(kindled["effect1"]["apply_aura"], AURA_DONE)
        self.assertEqual(kindled["effect1"]["base_points"], int(_header_number("kKindledDamageDonePct")))
        self.assertEqual(kindled["effect2"]["apply_aura"], AURA_TAKEN)
        self.assertEqual(kindled["effect2"]["base_points"], int(_header_number("kKindledDamageTakenPct")))
        for spell_id in (TICK, PYROBLAST, HOLY_FIRE):
            self.assertTrue(_raw(self.spells[spell_id], "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS, spell_id)
        for spell_id in (HOLY_FIRE, SCORCHED, GUST):
            self.assertTrue(_raw(self.spells[spell_id], "AuraInterruptFlags") & AURA_INTERRUPT_CHANGE_MAP, spell_id)

    def test_looks(self):
        for spell_id, visual in LOOKS.items():
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), visual, spell_id)

    def test_walls_and_gust(self):
        self.assertIn("spec.killSpell = SPELL_ST_CROSSED_THE_LINE", self.cpp)
        self.assertNotRegex(_header(), r"=\s*206400")      # the shared strike is never defined twice
        self.assertIn("GustDistance(player->GetPositionX())", self.cpp)
        self.assertIn("o.gripOnPull = true", self.cpp)

    def test_template(self):
        self.assertTrue(self.edits)
        cols = {}
        for e in self.edits:
            cols.update(e)
        self.assertEqual(cols["ScriptName"], "boss_archivist_galford_rework")
        self.assertEqual(cols["AIName"], "")
        self.assertAlmostEqual(float(cols["HealthModifier"]), 69.615)
        self.assertAlmostEqual(float(cols["DamageModifier"]), 3.5)
        self.assertEqual(int(cols["CreatureImmunitiesId"]), 1972)

    def test_sql_rev(self):
        sql = SQL_REV.read_text(encoding="utf-8")
        self.assertIn("DELETE FROM `smart_scripts` WHERE `entryorguid` = 10811 AND `source_type` = 0;", sql)
        lines = re.findall(r"\(10811, (\d), 0, '((?:[^']|'')*)', (\d+),", sql)
        self.assertEqual([int(g) for g, _, _ in lines], list(range(7)))
        types = {int(g): int(t) for g, _, t in lines}
        self.assertEqual(types[1], 41)
        self.assertTrue(all(t == 14 for g, t in types.items() if g != 1))
        groups = set(re.findall(r"(YELL|EMOTE)_GALFORD_\w+", self.cpp))
        self.assertTrue(groups)


if __name__ == "__main__":
    unittest.main()
