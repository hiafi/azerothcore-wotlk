"""
Zul'Farrak build WP-D5, Sergeant Bly's crew as a boss: source/npcs/zul_farrak/bly_crew_fight.py (the crew's fight
columns and the spells 214030-214049), data/sql/updates/pending_db_world/rev_bly_crew_fight_zul_farrak.sql (the stash
chest's templates), and the C++ they must agree with (modules/mod-dungeon-bosses src/ZulFarrak/CrewFightLogic.h and
bly_crew_fight_rework.cpp).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_zul_farrak_bly_crew_fight.py
"""

from __future__ import annotations

import ast
import math
import re
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import test_id_blocks as id_blocks  # noqa: E402
from lib import test_zul_farrak_npcs as skeleton  # noqa: E402
from source.npcs.zul_farrak import _visuals as visuals  # noqa: E402

MDB = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "ZulFarrak"
LOGIC = MDB / "CrewFightLogic.h"
HEADER = MDB / "ZulFarrakRework.h"
SCRIPT = MDB / "bly_crew_fight_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_bly_crew_fight_zul_farrak.sql"
DT_FILE = TOOL_ROOT / "source" / "npcs" / "zul_farrak" / "bly_crew_fight.py"


def _dt_constants() -> SimpleNamespace:
    """bly_crew_fight.py's top-level literal constants (the module itself only loads inside the registry)."""
    tree = ast.parse(DT_FILE.read_text(encoding="utf-8"))
    values = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                values[node.targets[0].id] = ast.literal_eval(node.value)
            except ValueError:
                continue
    return SimpleNamespace(**values)


dt = _dt_constants()

FIRST = 214030
SLICE = range(214030, 214070)
NAMES = ("SPELL_BC_GANG_UP_MARK", "SPELL_BC_GANG_UP_SHARE", "SPELL_BC_GUARDED", "SPELL_BC_INTERVENE",
         "SPELL_BC_REFLECT", "SPELL_BC_VANISH", "SPELL_BC_AMBUSH", "SPELL_BC_GOUGE", "SPELL_BC_KIDNEY_SHOT",
         "SPELL_BC_WOUND_POISON", "SPELL_BC_RAIN_LOOK", "SPELL_BC_RAIN", "SPELL_BC_SEED", "SPELL_BC_SEED_BURST",
         "SPELL_BC_GREATER_HEAL", "SPELL_BC_GREATER_HEAL_H", "SPELL_BC_RESURRECTION", "SPELL_BC_SOULSTONE",
         "SPELL_BC_AVENGE", "SPELL_BC_WOUND_POISON_LOOK")
(MARK, SHARE, GUARDED, INTERVENE, REFLECT, VANISH, AMBUSH, GOUGE, KIDNEY, POISON, RAIN_LOOK, RAIN, SEED, SEED_BURST,
 HEAL, HEAL_H, RES, SOULSTONE, AVENGE, POISON_LOOK) = range(FIRST, FIRST + len(NAMES))
EFFECT_SCHOOL_DAMAGE, EFFECT_DUMMY, EFFECT_APPLY_AURA, EFFECT_HEAL, EFFECT_PERSISTENT_AREA_AURA = 2, 3, 6, 10, 27
AURA_STUN, AURA_REFLECT, AURA_DAMAGE_DONE, AURA_HEALING_PCT = 12, 28, 79, 118
AURA_MELEE_HASTE, AURA_CAST_SPEED = 138, 65
SCHOOL_NORMAL, SCHOOL_HOLY, SCHOOL_FIRE, SCHOOL_SHADOW = 1, 2, 4, 32
IGNORE_CASTER_MODIFIERS = 0x20000000
# Base health of the crew's class and level (creature_classlevelstats, the Build spec and handoff 3.6)
BASE_HEALTH = {7604: 1848, 7605: 1782, 7606: 1247, 7608: 1426}
HEALTH_NAMES = {7604: "kBly", 7605: "kRaven", 7606: "kOro", 7608: "kMurta"}


class BlyCrewFightTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = skeleton._load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {}
        for e in reg.creature_template_edits:
            cls.edits.setdefault(int(e["entry"]), {}).update(e)
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.logic = LOGIC.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.tune = cls.logic[cls.logic.index("namespace Tune"):cls.logic.index("// BC1 Gang Up and heroic")]

    def _tune(self, name: str) -> str:
        match = re.search(rf"\b{name}\s*(?:=\s*|\{{)([^;}}]+?)\s*(?:;|\}};)", self.tune)
        self.assertIsNotNone(match, name)
        return match.group(1).replace(" ", "")

    # --- the spells ---------------------------------------------------------------------------------------------------

    def test_the_spells_sit_in_the_d5_slice(self):
        self.assertEqual(sorted(self.spells), list(range(FIRST, FIRST + len(NAMES))))
        self.assertEqual(id_blocks.out_of_reservation("zul_farrak", {"spell": list(self.spells)}), [])
        self.assertIn("kSpellsCrewFight{ 214030, 214069 }", self.header)

    def test_the_cpp_names_the_same_ids(self):
        for offset, name in enumerate(NAMES):
            self.assertRegex(self.logic, rf"{name}\s*=\s*{FIRST + offset},", name)
            self.assertIn(name, self.script, name)

    def test_the_registry_hits_are_resolve_copies(self):
        for spell_id, school in ((AMBUSH, SCHOOL_NORMAL), (RAIN, SCHOOL_FIRE)):
            spell = self.spells[spell_id]
            self.assertEqual(spell["school"], school, spell_id)
            self.assertIn((spell_id, "spell_boss_mechanics_resolve"), self.scripts, spell_id)
            self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & IGNORE_CASTER_MODIFIERS, spell_id)
        self.assertIn(".Spell(SPELL_BC_AMBUSH)", self.script)
        self.assertIn(".Spell(SPELL_BC_RAIN)", self.script)
        # rule 17: both reach the tank; rule 22: Weakened on the Ambush only (Rain is a lingering patch)
        self.assertEqual(self.script.count(".TankDamage("), 2)
        self.assertEqual(self.script.count(".Weakened()"), 1)

    def test_the_script_hits_take_the_exact_base_point(self):
        for spell_id, school in ((SHARE, SCHOOL_NORMAL), (SEED_BURST, SCHOOL_SHADOW)):
            spell = self.spells[spell_id]
            effect = spell["effect1"]
            self.assertEqual(spell["school"], school)
            self.assertEqual((effect["type"], effect["base_points"], effect["die_sides"]), (EFFECT_SCHOOL_DAMAGE, 0, 0))
            self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & IGNORE_CASTER_MODIFIERS)
            self.assertEqual(float(spell["range_yards"]), 100.0)
        self.assertIn("SPELL_BC_GANG_UP_SHARE, SPELLVALUE_BASE_POINT0", self.script)
        self.assertIn("SPELL_BC_SEED_BURST, SPELLVALUE_BASE_POINT0", self.script)

    def test_murtas_casts_are_kickable_holy_and_nothing_else_is(self):
        for spell_id, cast_ms in ((HEAL, dt.GREATER_HEAL_CAST_MS[0]), (HEAL_H, dt.GREATER_HEAL_CAST_MS[1]),
                                  (RES, dt.RESURRECTION_CAST_MS)):
            spell = self.spells[spell_id]
            raw = spell["raw_overrides"]
            self.assertEqual(spell["school"], SCHOOL_HOLY, spell_id)
            self.assertEqual((raw["InterruptFlags"], raw["PreventionType"]), (15, 1), spell_id)
            self.assertEqual(spell["cast_time_ms"], cast_ms, spell_id)
            self.assertEqual(float(spell["range_yards"]), 40.0, spell_id)
        self.assertEqual(self.spells[HEAL]["effect1"]["type"], EFFECT_HEAL)
        self.assertEqual(self.spells[RES]["effect1"]["type"], EFFECT_DUMMY)
        for spell_id, spell in self.spells.items():
            if spell_id not in (HEAL, HEAL_H, RES):
                self.assertEqual(int(spell["raw_overrides"].get("InterruptFlags", 0)), 0, spell_id)
                self.assertEqual(spell["cast_time_ms"], 0, spell_id)
        self.assertEqual(self._tune("kGreaterHealCastMs"), f"{dt.GREATER_HEAL_CAST_MS[0]},{dt.GREATER_HEAL_CAST_MS[1]}")
        self.assertEqual(self._tune("kResurrectionCastMs"), str(dt.RESURRECTION_CAST_MS))

    def test_the_auras_match_the_header(self):
        self.assertEqual(self.spells[GUARDED]["duration_ms"], dt.GUARDED_MS)
        self.assertEqual(self._tune("kGuardedMs"), str(dt.GUARDED_MS))
        self.assertEqual(self.spells[REFLECT]["effect1"]["apply_aura"], AURA_REFLECT)
        self.assertEqual(self.spells[REFLECT]["raw_overrides"]["ProcCharges"], 1)
        for spell_id, ms, name in ((GOUGE, dt.GOUGE_MS, "kGougeMs"), (KIDNEY, dt.KIDNEY_SHOT_MS, "kKidneyShotMs")):
            self.assertEqual(self.spells[spell_id]["effect1"]["apply_aura"], AURA_STUN)
            self.assertEqual(self.spells[spell_id]["duration_ms"], ms)
            self.assertEqual(self._tune(name), str(ms))
        # Gouge breaks on damage (an incapacitate), Kidney Shot does not
        self.assertTrue(self.spells[GOUGE]["raw_overrides"]["AuraInterruptFlags"] & 0x2)
        self.assertFalse(self.spells[KIDNEY]["raw_overrides"]["AuraInterruptFlags"] & 0x2)
        poison = self.spells[POISON]
        self.assertEqual(poison["dispel"], 4)
        self.assertEqual(poison["effect1"]["apply_aura"], AURA_HEALING_PCT)
        self.assertEqual(poison["effect1"]["base_points"] + poison["effect1"]["die_sides"],
                         -dt.WOUND_POISON_HEALING_PCT)
        self.assertEqual(poison["duration_ms"], dt.WOUND_POISON_MS)
        self.assertEqual(self.spells[POISON_LOOK]["duration_ms"], dt.WOUND_POISON_MS)
        self.assertEqual(self._tune("kWoundPoisonMs"), str(dt.WOUND_POISON_MS))
        seed = self.spells[SEED]
        self.assertEqual(seed["dispel"], 1)
        self.assertEqual(seed["duration_ms"], dt.SEED_AURA_MS)
        self.assertEqual(self._tune("kSeedAuraMs"), str(dt.SEED_AURA_MS))
        avenge = self.spells[AVENGE]
        self.assertEqual([avenge[f"effect{i}"]["apply_aura"] for i in (1, 2, 3)],
                         [AURA_DAMAGE_DONE, AURA_MELEE_HASTE, AURA_CAST_SPEED])
        self.assertTrue(all(avenge[f"effect{i}"]["base_points"] == dt.AVENGE_PCT for i in (1, 2, 3)))
        self.assertEqual(self._tune("kAvengePctPerStack"), str(dt.AVENGE_PCT))
        rain = self.spells[RAIN_LOOK]
        self.assertEqual(rain["effect1"]["type"], EFFECT_PERSISTENT_AREA_AURA)
        self.assertEqual(rain["duration_ms"], int(self._tune("kRainWarnMs")) + int(self._tune("kRainMs")))

    def test_the_looks_are_the_visuals_picks(self):
        looks = {MARK: visuals.BC_MARK, GUARDED: visuals.BC_GUARDED, INTERVENE: visuals.BC_INTERVENE,
                 REFLECT: visuals.BC_REFLECT, VANISH: visuals.BC_VANISH, AMBUSH: visuals.BC_SHADOWSTEP,
                 GOUGE: visuals.BC_GOUGE, KIDNEY: visuals.BC_KIDNEY, POISON: visuals.BC_POISON,
                 POISON_LOOK: visuals.BC_POISON_STATE, RAIN_LOOK: visuals.BC_ROF, SEED: visuals.BC_SEED,
                 SEED_BURST: visuals.BC_SEED_BURST, HEAL: visuals.BC_GREATER_HEAL, HEAL_H: visuals.BC_GREATER_HEAL,
                 RES: visuals.BC_RES, SOULSTONE: visuals.BC_SOULSTONE, AVENGE: visuals.BC_AVENGE}
        for spell_id, visual in looks.items():
            self.assertEqual(self.spells[spell_id]["raw_overrides"]["SpellVisualID_1"], visual, spell_id)

    # --- the crew's columns -------------------------------------------------------------------------------------------

    def test_the_crews_normal_health_is_the_headers(self):
        for entry, modifier in dt.HEALTH_MODIFIER.items():
            with self.subTest(entry=entry):
                self.assertEqual(self.edits[entry]["HealthModifier"], modifier)
                match = re.search(rf"{HEALTH_NAMES[entry]}\{{ (\d+), (\d+) \}}", self.header)
                self.assertIsNotNone(match)
                self.assertEqual(math.ceil(BASE_HEALTH[entry] * modifier - 1e-6), int(match.group(1)))

    def test_bly_is_stun_immune_and_the_rest_diminish(self):
        self.assertEqual(self.edits[7604]["CreatureImmunitiesId"], 1972)
        self.assertNotIn("flags_extra", self.edits[7604])
        for entry in (7605, 7606, 7608):
            self.assertEqual(self.edits[entry]["flags_extra"], 0x00100000, entry)
            self.assertNotIn("CreatureImmunitiesId", self.edits[entry])
        self.assertNotIn(7607, self.edits)      # Weegli is not in the fight
        for entry in (7604, 7605, 7606, 7608):
            for column in ("faction", "ScriptName", "AIName", "lootid"):
                self.assertNotIn(column, self.edits[entry], (entry, column))

    # --- the stash ----------------------------------------------------------------------------------------------------

    def test_the_stash_templates(self):
        for entry in (301360, 301361):
            self.assertRegex(self.sql, rf"\({entry}, 3, \d+, '[^']+', '', '', '', [\d.]+, 57, {entry}, 0, 1, ")
        self.assertIn("GO_ZF_CREW_STASH        = 301360", self.header)
        self.assertIn("GO_ZF_CREW_STASH_HEROIC = 301361", self.header)
        self.assertNotIn("DELETE FROM `gameobject_template`", self.sql)
        for number, line in enumerate(self.sql.split("\n"), 1):
            self.assertLessEqual(len(line), 120, number)
            self.assertEqual(line, line.rstrip(), number)


if __name__ == "__main__":
    unittest.main()
