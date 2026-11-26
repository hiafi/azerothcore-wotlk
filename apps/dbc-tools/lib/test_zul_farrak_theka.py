"""
Zul'Farrak build WP-D1, Theka the Martyr: source/npcs/zul_farrak/theka.py (his columns, the two swarms and the spells
213860-213874), data/sql/updates/pending_db_world/rev_theka_zul_farrak.sql (his texts, his stopped patrol), and the C++
they must agree with (modules/mod-dungeon-bosses src/ZulFarrak/ThekaLogic.h and boss_theka_rework.cpp).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_zul_farrak_theka.py
"""

from __future__ import annotations

import ast
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
from source.npcs.zul_farrak import _common as common  # noqa: E402
from source.npcs.zul_farrak import _visuals as visuals  # noqa: E402

MDB = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "ZulFarrak"
LOGIC = MDB / "ThekaLogic.h"
SCRIPT = MDB / "boss_theka_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_theka_zul_farrak.sql"
DT_FILE = TOOL_ROOT / "source" / "npcs" / "zul_farrak" / "theka.py"


def _dt_constants() -> SimpleNamespace:
    """theka.py's top-level literal constants (the module itself only loads inside the registry)."""
    tree = ast.parse(DT_FILE.read_text(encoding="utf-8"))
    values = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                values[node.targets[0].id] = ast.literal_eval(node.value)
            except ValueError:
                continue
    return SimpleNamespace(**values)


theka = _dt_constants()

FIRST = 213860
SLICE = range(213860, 213890)
NAMES = ("SPELL_TK_BITE", "SPELL_TK_DEVOUR", "SPELL_TK_HALLOWED", "SPELL_TK_PLAGUE", "SPELL_TK_PLAGUE_HEROIC",
         "SPELL_TK_PLAGUE_SPREAD", "SPELL_TK_PLAGUE_LOOK", "SPELL_TK_RISING", "SPELL_TK_ERUPTION", "SPELL_TK_LAMENT",
         "SPELL_TK_SWARM_AURA", "SPELL_TK_RISE_BURST", "SPELL_TK_ERUPTION_LOOK", "SPELL_TK_SWARM_ON_THEKA",
         "SPELL_TK_HUNT_TRAIL")
(BITE, DEVOUR, HALLOWED, PLAGUE, PLAGUE_H, SPREAD, PLAGUE_LOOK, RISING, ERUPTION, LAMENT, CLOUD, RISE_BURST,
 ERUPTION_LOOK, ON_THEKA, TRAIL) = range(FIRST, FIRST + len(NAMES))
EFFECT_SCHOOL_DAMAGE, EFFECT_DUMMY, EFFECT_APPLY_AURA = 2, 3, 6
AURA_DUMMY, AURA_PERIODIC_DAMAGE = 4, 3
SCHOOL_HOLY, SCHOOL_NATURE = 2, 8
DISPEL_DISEASE = 3
THEKA, PERSECUTOR, PENITENT = 7272, 301005, 301006
IGNORE_CASTER_MODIFIERS = 0x20000000
DO_NOT_RESET_COMBAT_TIMERS = 0x00020000
DO_NOT_DISPLAY = 0x80


class ThekaTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = skeleton._load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits}
        cls.models = {int(e["CreatureID"]): e for e in reg.creature_template_models}
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.logic = LOGIC.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.tune = cls.logic[cls.logic.index("namespace Tune"):cls.logic.index("// Values the build spec leaves open")]

    def _tune(self, name: str) -> str:
        match = re.search(rf"\b{name}\s*(?:=\s*|\{{)([^;}}]+?)\s*(?:;|\}};)", self.tune)
        self.assertIsNotNone(match, name)
        return match.group(1).replace(" ", "")

    def _logic(self, name: str) -> str:
        match = re.search(rf"\b{name}\s*=\s*([^;]+);", self.logic)
        self.assertIsNotNone(match, name)
        return match.group(1).strip()

    # --- the spells ---------------------------------------------------------------------------------------------------

    def test_the_spells_sit_in_the_d1_slice(self):
        self.assertEqual(sorted(self.spells), list(range(FIRST, FIRST + len(NAMES))))
        self.assertEqual(id_blocks.out_of_reservation("zul_farrak", {"spell": list(self.spells)}), [])
        self.assertIn("kSpellsTheka{ 213860, 213889 }", (MDB / "ZulFarrakRework.h").read_text(encoding="utf-8"))

    def test_the_cpp_names_the_same_ids(self):
        for offset, name in enumerate(NAMES):
            self.assertRegex(self.logic, rf"{name}\s*=\s*kSpellSlice\.first \+ {offset},", name)

    def test_the_registry_hits_are_nature_resolve_copies(self):
        for spell_id in (BITE, DEVOUR, ERUPTION):
            spell = self.spells[spell_id]
            self.assertEqual(spell["school"], SCHOOL_NATURE, spell_id)
            self.assertEqual(spell["effect1"]["type"], EFFECT_SCHOOL_DAMAGE, spell_id)
            self.assertIn((spell_id, "spell_boss_mechanics_resolve"), self.scripts, spell_id)
            self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & IGNORE_CASTER_MODIFIERS, spell_id)
        for name in ("BITE", "DEVOUR", "ERUPTION"):
            self.assertIn(f".Spell(SPELL_TK_{name})", self.script)
        # mechanics include the tank (rule 17), and Weakened on every one (rule 22, ruling 25)
        self.assertEqual(self.script.count(".TankDamage(pct)"), 3)
        self.assertEqual(self.script.count(".Weakened()"), 3)

    def test_the_plague_is_the_kick_and_its_values_are_the_headers(self):
        for spell_id, heroic in ((PLAGUE, False), (PLAGUE_H, True)):
            with self.subTest(heroic=heroic):
                spell = self.spells[spell_id]
                raw = spell["raw_overrides"]
                i = 1 if heroic else 0
                self.assertEqual(spell["school"], SCHOOL_NATURE)
                self.assertEqual(spell["dispel"], DISPEL_DISEASE)
                self.assertEqual((raw["InterruptFlags"], raw["PreventionType"]), (15, 1))
                self.assertTrue(raw["AttributesEx2"] & DO_NOT_RESET_COMBAT_TIMERS)
                self.assertTrue(raw["AttributesEx3"] & IGNORE_CASTER_MODIFIERS)
                self.assertEqual(spell["cast_time_ms"], theka.PLAGUE_CAST_MS[i])
                self.assertEqual(spell["duration_ms"], theka.PLAGUE_MS[i])
                hit, dot = spell["effect1"], spell["effect2"]
                self.assertEqual((hit["type"], dot["type"], dot["apply_aura"]),
                                 (EFFECT_SCHOOL_DAMAGE, EFFECT_APPLY_AURA, AURA_PERIODIC_DAMAGE))
                self.assertEqual(hit["base_points"] + hit["die_sides"], theka.PLAGUE_HIT[i])
                self.assertEqual(dot["base_points"] + dot["die_sides"], theka.PLAGUE_TICK[i])
                self.assertEqual(dot["amplitude"], theka.PLAGUE_TICK_MS[i])
                self.assertEqual(int(raw.get("EffectMiscValueB_1", 0)), 0)
                self.assertEqual(int(raw.get("EffectMiscValueB_2", 0)), 0)
                self.assertIn((spell_id, "spell_dungeon_refflat_damage"), self.scripts)
                self.assertIn((spell_id, "spell_dungeon_refflat_periodic"), self.scripts)
                # A spell row without a range lands at 0 yd: the cast would fail.
                self.assertEqual(float(spell["range_yards"]), 100.0)
                self.assertEqual(raw["SpellVisualID_1"], visuals.TK_PLAGUE_CAST)
        # the header's numbers, the DT's numbers
        self.assertEqual(self._tune("kPlagueCastMs"), "4000,2000")
        self.assertEqual(self._tune("kPlagueMs"), "12000,10000")
        self.assertEqual(self._tune("kPlagueTickMs"), "3000,2000")
        self.assertEqual(self._tune("kPlagueHitPct"), "10.f,20.f")
        self.assertEqual(self._tune("kPlagueDotPct"), "15.f,40.f")
        self.assertEqual(theka.PLAGUE_TICK, (1500 // 4, 4000 // 5))

    def test_the_spread_copy_never_spreads_and_cannot_be_kicked(self):
        spell = self.spells[SPREAD]
        raw = spell["raw_overrides"]
        self.assertEqual(spell["cast_time_ms"], 0)
        self.assertEqual(int(raw.get("InterruptFlags", 0)), 0)
        self.assertEqual(spell["dispel"], DISPEL_DISEASE)
        self.assertEqual(spell["effect1"]["apply_aura"], AURA_PERIODIC_DAMAGE)
        self.assertEqual(spell["effect1"]["base_points"] + spell["effect1"]["die_sides"], theka.PLAGUE_TICK[1])
        self.assertIn((SPREAD, "spell_dungeon_refflat_periodic"), self.scripts)
        self.assertEqual(raw["SpellVisualID_1"], visuals.TK_PLAGUE_SPREAD)
        # the script spreads only the heroic plague
        self.assertIn("carrier.spell == SPELL_TK_PLAGUE_HEROIC", self.script)

    def test_only_the_plague_can_be_kicked(self):
        for spell_id, spell in self.spells.items():
            if spell_id in (PLAGUE, PLAGUE_H):
                continue
            self.assertEqual(int(spell["raw_overrides"].get("InterruptFlags", 0)), 0, spell_id)
            self.assertEqual(int(spell["raw_overrides"].get("PreventionType", 0)), 0, spell_id)

    def test_hallowed_suffering_stacks_and_cannot_be_dispelled(self):
        spell = self.spells[HALLOWED]
        self.assertEqual(spell["dispel"], 0)
        self.assertEqual(spell["raw_overrides"]["CumulativeAura"], theka.HALLOWED_MAX_STACKS)
        self.assertEqual(self._tune("kStackCapHeroic"), str(theka.HALLOWED_MAX_STACKS))
        self.assertEqual(self._tune("kStackCapNormal"), "5")
        self.assertEqual(spell["raw_overrides"]["AuraDescription_Lang_enUS"], "Sanctified by his persecutors' bites.")

    def test_the_lament_is_the_scripts_holy_amount(self):
        spell = self.spells[LAMENT]
        self.assertEqual(spell["school"], SCHOOL_HOLY)
        self.assertEqual((spell["effect1"]["base_points"], spell["effect1"]["die_sides"]), (0, 0))
        self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & IGNORE_CASTER_MODIFIERS)
        self.assertEqual(float(spell["range_yards"]), 100.0)
        self.assertIn("SPELL_TK_LAMENT, args", self.script)

    def test_the_looks_are_the_approved_picks(self):
        for spell_id, visual in ((CLOUD, visuals.TK_SWARM_AURA), (RISE_BURST, visuals.TK_RISE_BURST),
                                 (ERUPTION_LOOK, visuals.TK_HUNT_ERUPTION), (ON_THEKA, visuals.TK_SWARM_ON_THEKA),
                                 (TRAIL, visuals.TK_HUNT_TRAIL), (RISING, visuals.TK_RISING),
                                 (PLAGUE_LOOK, visuals.TK_PLAGUE_STATE)):
            self.assertEqual(self.spells[spell_id]["raw_overrides"]["SpellVisualID_1"], visual, spell_id)
        for spell_id in (BITE, DEVOUR, ERUPTION, HALLOWED, LAMENT):
            self.assertNotIn("SpellVisualID_1", self.spells[spell_id]["raw_overrides"], spell_id)
        # never the WRONG picks (s3.10)
        wired = {self.spells[s]["raw_overrides"].get("SpellVisualID_1") for s in self.spells}
        self.assertFalse(wired & {8325, 7621, 11778})
        for spell_id in (CLOUD, TRAIL, PLAGUE_LOOK):
            self.assertTrue(self.spells[spell_id]["attributes"] & DO_NOT_DISPLAY, spell_id)
        self.assertEqual(self.spells[ON_THEKA]["duration_ms"], int(self._tune("kHoldMs")))

    # --- the numbers --------------------------------------------------------------------------------------------------

    def test_the_header_is_the_build_spec(self):
        for name, value in (("kSwarmFirstMs", "12000,20000"), ("kSwarmEveryMs", "20000"),
                            ("kSwarmsPerRise", "1,2"), ("kSwarmSpeed", "4.f,5.f"), ("kSwarmWidth", "4.f"),
                            ("kRiseMs", "2000"), ("kBitePct", "30.f,45.f"), ("kArrivalWarnMs", "2500"),
                            ("kDevourRadius", "6.f"), ("kDevourPct", "40.f,60.f"), ("kHoldMs", "2500"),
                            ("kPlagueFirstMs", "8000"), ("kPlagueEveryMinMs", "12000"),
                            ("kPlagueEveryMaxMs", "16000"), ("kPlagueRangeYd", "30.f"), ("kSpreadYd", "6.f"),
                            ("kSpreadEveryMs", "2000"), ("kRisingPct", "30.f"), ("kRisingMs", "2000"),
                            ("kHuntEveryMs", "15000,12000"), ("kChaseMs", "5000"), ("kChaseSpeed", "5.f"),
                            ("kChaseRadius", "3.f"), ("kEruptionWarnMs", "1500"), ("kEruptionRadius", "5.f"),
                            ("kEruptionPct", "30.f,45.f"), ("kLamentEveryMs", "3000"),
                            ("kLamentPctPerStack", "1.5f")):
            self.assertEqual(self._tune(name), value, name)

    def test_the_swarm_scale_and_the_risen_look(self):
        low, high = visuals.SWARM_SCALE_RANGE
        scale = float(self._logic("float constexpr kSwarmScale").rstrip("f"))
        self.assertTrue(low <= scale <= high)
        self.assertEqual(scale, theka.SWARM_SCALE)
        self.assertEqual(int(self._logic("std::uint32_t constexpr kRisenDisplay")), visuals.DISPLAY_THEKA_RISEN)
        # one call (rule 4): the display and its object scale; CDI 6697 carries its own 1.2
        self.assertIn("me->SetDisplayId(kRisenDisplay, kRisenObjectScale);", self.script)
        self.assertNotIn("SetObjectScale(", self.script)

    def test_no_assist_calls(self):
        # The flag stops the first call only: every tick, before UpdateVictim (rule 27).
        self.assertRegex(self.script, r"ZulFarrak::NoAssist\(me\);[^\n]*\n\s+if \(!UpdateVictim\(\)\)")

    # --- the creatures ------------------------------------------------------------------------------------------------

    def test_the_boss_keeps_the_skeletons_columns(self):
        row = self.edits[THEKA]
        self.assertEqual(row["ScriptName"], "boss_theka_rework")
        self.assertEqual(row["CreatureImmunitiesId"], common.IMMUNITY_BOSS_STUN)
        self.assertEqual(float(row["HealthModifier"]), 91.7)

    def test_the_swarms_are_hazards_never_targets(self):
        for entry, name, script in ((PERSECUTOR, "Persecutor Swarm", "npc_zf_persecutor_swarm"),
                                    (PENITENT, "Penitent Swarm", "npc_zf_penitent_swarm")):
            with self.subTest(entry=entry):
                row = self.creatures[entry]
                self.assertEqual(row["name"], name)
                self.assertEqual(row["ScriptName"], script)
                self.assertEqual(row["AIName"], "")
                self.assertEqual(int(row["unit_flags"]), 0x2 | 0x02000000)
                self.assertFalse(int(row["flags_extra"]) & 0x80, "a trigger's model is invisible: the swarm must show")
                self.assertEqual(float(row["DamageModifier"]), 0.0)
                self.assertNotIn("difficulty_entry_1", {k for k, v in row.items() if v})
                self.assertEqual(int(self.models[entry]["CreatureDisplayID"]), visuals.DISPLAY_SWARM)
                self.assertEqual(float(self.models[entry]["DisplayScale"]), theka.SWARM_SCALE)
                self.assertIn(f"RegisterDungeonReworkCreatureAI({script},", self.script)

    # --- the SQL ------------------------------------------------------------------------------------------------------

    def test_the_texts_are_the_build_spec(self):
        rows = re.findall(r"\(7272, (\d), 0, '((?:[^']|'')*)', (\d+), 0, 100, 0, 0, 0, 0, 0,", self.sql)
        self.assertEqual(rows, [
            ("0", "Who disturbs da Martyr''s tomb?", "14"),
            ("1", "%s cries out, and his persecutors stir in the sand!", "41"),
            ("2", "The persecutors swarm over %s!", "41"),
            ("3", "Ya cannot kill a martyr twice!", "14"),
            ("4", "A penitent swarm burrows toward $n!", "41"),
        ])
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 7272 AND `GroupID` BETWEEN 0 AND 4;", self.sql)
        statements = re.sub(r"^--.*$", "", self.sql, flags=re.M)
        self.assertNotIn("smart_scripts", statements)      # S0's rev owns it

    def test_his_patrol_is_stopped(self):
        self.assertIn("UPDATE `creature` SET `MovementType` = 0, `wander_distance` = 0 WHERE `guid` = 81463 AND "
                      "`id` = 7272;", self.sql)
        self.assertIn("UPDATE `creature_addon` SET `path_id` = 0 WHERE `guid` = 81463 AND `path_id` = 814630;",
                      self.sql)


if __name__ == "__main__":
    unittest.main()
