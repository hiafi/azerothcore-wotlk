"""
Blackrock Spire build WP-B1, Highlord Omokk: source/npcs/blackrock_spire/omokk.py against its C++
(modules/mod-dungeon-bosses src/BlackrockSpire/OmokkLogic.h, boss_highlord_omokk_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in Omokk's slice (210020-210059), OmokkLogic.h names the same ids, Frenzy 8269 and Knock Away 10101
    are not redeclared;
  - the crowd 300700 and the Brawler 300701 are unselectable props bound to their scripts with no heroic template; the
    Mojo Mystic 300702 is a 12k elite bound to its script with its heroic entry 310288;
  - the band, Haymaker, Pelting, Belly Slam and Bull Rush hits are resolve copies; the pile's shove is the kit's
    percent hit (25% / 35%); Pit Drop has its own script; the custom damage spells ignore caster modifiers;
  - Crowd's Roar stacks to 5 (+10% damage, +10% attack speed), Booed to 3 (+10% taken), Mojo Frenzy is the stock
    Frenzy's values for 15 s; Ogre Mojo is a 3 s kickable Nature cast;
  - the cast bars match the header's times and are not kickable; the looks are V-1's OM_ picks;
  - 9196 is bound with SmartAI off, HealthModifier 62.859, DamageModifier 3.5, immunity set 1972;
  - the SQL rev removes the two spawns beside him and gives him the eight build spec lines (yells 14, emotes 41).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_spire_omokk.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockSpire"
HEADER = MODULE_DIR / "OmokkLogic.h"
SCRIPT = MODULE_DIR / "boss_highlord_omokk_rework.cpp"
SQL_REV = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_highlord_omokk_blackrock_spire.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_spire"

SLICE = range(210020, 210060)
(SHOVE, PILE_SHOVE, HAY_CAST, HAY_TWO_CAST, HAYMAKER, PELTING) = range(210020, 210026)
BOTTLES = range(210026, 210032)
(ROAR, BOOED, ROCK, MOJO, FRENZY, FRENZY_LOOK, SLAM_CAST, SLAM, RUSH_CAST, RUSH, PIT_DROP, SLAM_LOOK,
 HAY_LOOK, SHOVED) = range(210032, 210046)
FAN, BRAWLER, MYSTIC = 300700, 300701, 300702
OMOKK = 9196
MYSTIC_HEROIC = 310288

SCHOOL_NORMAL, SCHOOL_NATURE = 1, 8                # School masks
SCHOOL_DAMAGE, APPLY_AURA = 2, 6
AURA_DONE, AURA_TAKEN, AURA_MELEE_HASTE = 79, 87, 138
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
UNIT_FLAG_NOT_SELECTABLE = 0x02000000
UNIT_FLAG_NON_ATTACKABLE = 0x2
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT_DAMAGE = "spell_dungeon_refflat_damage"

LOOKS = {
    SHOVE: 1023, PILE_SHOVE: 1023, HAYMAKER: 208, HAY_LOOK: 208, ROAR: 870, ROCK: 1506, MOJO: 7306, FRENZY: 7306,
    FRENZY_LOOK: 7306, SLAM: 8083, SLAM_LOOK: 12882, RUSH: 3783, PIT_DROP: 1023,
}
BOTTLE_LOOKS = [8943, 8944, 8945, 8947, 8949, 8950]


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


class OmokkDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates
                         if int(e["entry"]) in (FAN, BRAWLER, MYSTIC)}
        cls.models = [m for m in reg.creature_template_models if int(m["CreatureID"]) in (FAN, BRAWLER, MYSTIC)]
        cls.edits = [e for e in reg.creature_template_edits if int(e["entry"]) == OMOKK]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(SHOVE, SHOVED + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_spire", {"spell": mine}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_OM_\w+\s*=\s*kSpellSlice\.first \+ (\d+)", _header())}
        self.assertEqual({SHOVE + n for n in header_ids} | set(BOTTLES), set(mine))
        for retired in (8269, 10101):
            self.assertNotIn(retired, self.spells)

    def test_the_crowd(self):
        self.assertEqual(sorted(self.creatures), [FAN, BRAWLER, MYSTIC])
        self.assertEqual(id_blocks.out_of_reservation("blackrock_spire", {"creature": [FAN, BRAWLER, MYSTIC]}), [])
        for entry, script in ((FAN, "npc_brs_brawl_fan"), (BRAWLER, "npc_brs_brawler")):
            c = self.creatures[entry]
            self.assertTrue(c["unit_flags"] & UNIT_FLAG_NOT_SELECTABLE)
            self.assertTrue(c["unit_flags"] & UNIT_FLAG_NON_ATTACKABLE)
            self.assertEqual(c.get("difficulty_entry_1", 0), 0)
            self.assertEqual(c["ScriptName"], script)
            self.assertEqual(c["lootid"], 0)
            self.assertIn(f"RegisterDungeonReworkCreatureAI({script}", self.cpp)
        fan_looks = {int(m["CreatureDisplayID"]) for m in self.models if int(m["CreatureID"]) == FAN}
        self.assertEqual(len(fan_looks), 4)
        self.assertTrue(all(float(m["Probability"]) > 0 for m in self.models))

    def test_the_mystic(self):
        m = self.creatures[MYSTIC]
        self.assertEqual(m["ScriptName"], "npc_brs_mojo_mystic")
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_brs_mojo_mystic", self.cpp)
        self.assertEqual(int(m["difficulty_entry_1"]), MYSTIC_HEROIC)
        self.assertEqual(int(m["rank"]), 1)
        self.assertEqual(int(m["unit_flags"]) & UNIT_FLAG_NOT_SELECTABLE, 0)
        self.assertEqual(int(m.get("CreatureImmunitiesId", 0) or 0), 0)     # the chant is kickable
        # Level 60 mage base 2,136 x the modifier = the header's 12k.
        self.assertAlmostEqual(2136 * float(m["HealthModifier"]), _header_number("kMojoMysticHealth"), delta=1.0)

    def test_registry_hits_and_scripts(self):
        for spell_id in (SHOVE, HAYMAKER, PELTING, SLAM, RUSH):
            self.assertIn((spell_id, RESOLVE), self.scripts, spell_id)
            self.assertEqual(self.spells[spell_id]["school"], SCHOOL_NORMAL)
        pile = self.spells[PILE_SHOVE]
        self.assertIn((PILE_SHOVE, REFFLAT_DAMAGE), self.scripts)
        normal, heroic = _header_nh("kCrowdShovePct")
        self.assertEqual(pile["effect1"]["base_points"] + 1, int(normal * 100))
        self.assertEqual(_raw(pile, "EffectMiscValueB_1"), int(heroic * 100))
        self.assertIn((PIT_DROP, "spell_brs_omokk_pit_drop"), self.scripts)
        self.assertIn("RegisterSpellScript(spell_brs_omokk_pit_drop)", self.cpp)
        for spell_id in (PILE_SHOVE, PIT_DROP):
            self.assertTrue(_raw(self.spells[spell_id], "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS, spell_id)
            self.assertEqual(self.spells[spell_id]["effect1"]["type"], SCHOOL_DAMAGE)
        # The registry calls name their copies.
        for name in ("SPELL_OM_CROWD_SHOVE", "SPELL_OM_HAYMAKER", "SPELL_OM_PELTING", "SPELL_OM_BELLY_SLAM",
                     "SPELL_OM_BULL_RUSH"):
            self.assertIn(f".Spell({name})", self.cpp)

    def test_auras(self):
        roar = self.spells[ROAR]
        self.assertEqual(_raw(roar, "CumulativeAura"), int(_header_number("kRoarMaxStacks")))
        self.assertEqual(roar["effect1"]["apply_aura"], AURA_DONE)
        self.assertEqual(roar["effect1"]["base_points"], int(_header_number("kRoarDamagePct")))
        self.assertEqual(roar["effect2"]["apply_aura"], AURA_MELEE_HASTE)
        self.assertEqual(roar["effect2"]["base_points"], int(_header_number("kRoarHastePct")))
        self.assertEqual(roar["duration_ms"], -1)
        booed = self.spells[BOOED]
        self.assertEqual(_raw(booed, "CumulativeAura"), int(_header_number("kBooedMaxStacks")))
        self.assertEqual(booed["effect1"]["apply_aura"], AURA_TAKEN)
        self.assertEqual(booed["effect1"]["base_points"], int(_header_number("kBooedTakenPct")))
        frenzy = self.spells[FRENZY]
        self.assertEqual(frenzy["duration_ms"], int(_header_number("kMojoFrenzyMs")))
        self.assertEqual(frenzy["effect1"]["base_points"], int(_header_number("kMojoFrenzyDamagePct")))
        self.assertEqual(frenzy["effect2"]["apply_aura"], AURA_MELEE_HASTE)
        self.assertEqual(frenzy["effect2"]["base_points"], int(_header_number("kMojoFrenzyHastePct")))

    def test_casts(self):
        mojo = self.spells[MOJO]
        self.assertEqual(mojo["cast_time_ms"], int(_header_number("kMojoCastMs")))
        self.assertEqual(_raw(mojo, "InterruptFlags"), 15)
        self.assertEqual(_raw(mojo, "PreventionType"), 1)
        self.assertEqual(mojo["school"], SCHOOL_NATURE)
        self.assertEqual(float(mojo["range_yards"]), _header_number("kMojoRangeYd"))
        self.assertIn("SPELL_OM_OGRE_MOJO, kMojoKickPriority", self.cpp)
        for bar, name in ((HAY_CAST, "kHaymakerCastMs"), (HAY_TWO_CAST, "kHaymakerTwoMs"),
                          (SLAM_CAST, "kBellySlamCastMs"), (RUSH_CAST, "kBullRushWarnMs")):
            self.assertEqual(self.spells[bar]["cast_time_ms"], int(_header_number(name)), bar)
            self.assertEqual(_raw(self.spells[bar], "InterruptFlags"), 0, bar)
        for spell_id in BOTTLES:
            self.assertAlmostEqual(float(_raw(self.spells[spell_id], "Speed")), _header_number("kBottleSpeed"))

    def test_the_shove_lockout(self):
        # R-1-A m1: a hidden DUMMY aura as long as the lockout; the band's line skips its wearer.
        shoved = self.spells[SHOVED]
        self.assertEqual(shoved["duration_ms"], int(_header_number("kShoveLockoutMs")))
        self.assertGreater(shoved["duration_ms"], int(_header_number("kBandTickMs")))
        self.assertEqual(shoved["effect1"]["apply_aura"], 4)        # DUMMY
        self.assertEqual(shoved["dispel"], 0)
        self.assertIn(".Eligible(NotShoved())", self.cpp)
        self.assertIn("e.auraSpell = SPELL_OM_SHOVED;", self.cpp)
        self.assertIn("AddAura(SPELL_OM_SHOVED, hit)", self.cpp)

    def test_looks(self):
        for spell_id, visual in LOOKS.items():
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), visual, spell_id)
        self.assertEqual([_raw(self.spells[s], "SpellVisualID_1") for s in BOTTLES], BOTTLE_LOOKS)
        for wrong in (9766,):                                       # Axe Volley's flash is never a Pelting look
            self.assertNotIn(wrong, [_raw(s, "SpellVisualID_1") for s in self.spells.values()])

    def test_template(self):
        self.assertTrue(self.edits)
        cols = {}
        for e in self.edits:
            cols.update(e)
        self.assertEqual(cols["ScriptName"], "boss_highlord_omokk_rework")
        self.assertEqual(cols["AIName"], "")
        self.assertAlmostEqual(float(cols["HealthModifier"]), 62.859)
        self.assertAlmostEqual(float(cols["DamageModifier"]), 3.5)
        self.assertEqual(int(cols["CreatureImmunitiesId"]), 1972)

    def test_sql_rev(self):
        sql = SQL_REV.read_text(encoding="utf-8")
        self.assertIn("DELETE FROM `creature` WHERE `id` = 9198 AND `guid` = 43514;", sql)
        self.assertIn("DELETE FROM `creature` WHERE `id` = 9201 AND `guid` = 43515;", sql)
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 9196;", sql)
        lines = re.findall(r"\(9196, (\d), 0, '((?:[^']|'')*)', (\d+),", sql)
        self.assertEqual([int(g) for g, _, _ in lines], list(range(8)))
        types = {int(g): int(t) for g, _, t in lines}
        emotes = {1, 2, 3, 6}
        self.assertTrue(all(types[g] == 41 for g in emotes))
        self.assertTrue(all(t == 14 for g, t in types.items() if g not in emotes))
        self.assertIn("$n", dict((int(g), text) for g, text, _ in lines)[1])
        for name, group in (("SAY_OM_PULL", 0), ("EMOTE_OM_HAYMAKER", 1), ("EMOTE_OM_CROWD_ROARS", 2),
                            ("EMOTE_OM_CROWD_JEERS", 3), ("SAY_OM_STILL_STRONGEST", 4), ("SAY_OM_TO_THE_BRIDGE", 5),
                            ("EMOTE_OM_MOJO", 6), ("SAY_OM_DEATH", 7)):
            self.assertRegex(_header(), rf"\b{name}\s*=\s*{group},")
            self.assertIn(name, self.cpp)


if __name__ == "__main__":
    unittest.main()
