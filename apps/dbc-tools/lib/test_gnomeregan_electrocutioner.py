"""
Gnomeregan build WP-D3, Electrocutioner 6000: source/npcs/gnomeregan/electrocutioner.py (his columns, the Blast
Stalker 301132 and the spells 214380-214393), data/sql/updates/pending_db_world/rev_electrocutioner_gnomeregan.sql (his
texts), and the C++ they must agree with (modules/mod-dungeon-bosses src/Gnomeregan/ElectrocutionerLogic.h,
ElectrocutionerMachine.cpp and boss_electrocutioner_rework.cpp).

With BM_SRC set to mod-boss-mechanics' src, the Logic header's drill tag table is diffed against MechanicDrill.h
(LESSONS A.3 #4); without it that test is skipped.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_gnomeregan_electrocutioner.py
"""

from __future__ import annotations

import ast
import os
import re
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import test_gnomeregan_npcs as skeleton  # noqa: E402
from lib import test_id_blocks as id_blocks  # noqa: E402
from source.npcs.gnomeregan import _visuals as visuals  # noqa: E402

MDB = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Gnomeregan"
LOGIC = MDB / "ElectrocutionerLogic.h"
MACHINE = MDB / "ElectrocutionerMachine.cpp"
SCRIPT = MDB / "boss_electrocutioner_rework.cpp"
HEADER = MDB / "GnomereganRework.h"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_electrocutioner_gnomeregan.sql"
DT_FILE = TOOL_ROOT / "source" / "npcs" / "gnomeregan" / "electrocutioner.py"


def _dt_constants() -> SimpleNamespace:
    """electrocutioner.py's top-level literal constants (the module itself only loads inside the registry)."""
    tree = ast.parse(DT_FILE.read_text(encoding="utf-8"))
    values = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            try:
                values[node.targets[0].id] = ast.literal_eval(node.value)
            except ValueError:
                continue
    return SimpleNamespace(**values)


el = _dt_constants()

FIRST = 214380
SLICE = range(214380, 214420)
NAMES = ("SPELL_VOLTAGE", "SPELL_VOLTAGE_CHARGED", "SPELL_JUSTICE_BAR", "SPELL_JUSTICE_HIT", "SPELL_JUSTICE_BLAST",
         "SPELL_MEGAVOLT_BAR", "SPELL_MEGAVOLT_HIT", "SPELL_CHAIN_BOLT", "SPELL_CHAIN_BOLT_HIT", "SPELL_SHOCK",
         "SPELL_SHOCK_HIT", "SPELL_STATIC", "SPELL_DISCHARGE_HIT", "SPELL_DISCHARGE_LOOK")
(VOLTAGE, CHARGED, JUSTICE_BAR, JUSTICE_HIT, JUSTICE_BLAST, MEGAVOLT_BAR, MEGAVOLT_HIT, CHAIN_BOLT, CHAIN_HIT, SHOCK,
 SHOCK_HIT, STATIC, DISCHARGE_HIT, DISCHARGE_LOOK) = range(FIRST, FIRST + len(NAMES))
HITS = (JUSTICE_HIT, MEGAVOLT_HIT, CHAIN_HIT, SHOCK_HIT, DISCHARGE_HIT)
EFFECT_SCHOOL_DAMAGE, EFFECT_DUMMY, EFFECT_APPLY_AURA = 2, 3, 6
AURA_DUMMY = 4
SCHOOL_PHYSICAL, SCHOOL_NATURE = 1, 8
ELECTROCUTIONER, BLAST_STALKER = 6235, 301132
IGNORE_CASTER_MODIFIERS = 0x20000000
DO_NOT_RESET_COMBAT_TIMERS = 0x00020000
NO_IMMUNITIES = 0x20000000
AURA_IS_DEBUFF = 0x04000000
DO_NOT_DISPLAY = 0x80
WRONG_VISUALS = {2048, 4229, 7678}      # V / s3.10: Supercharge, Electric Discharge, Overload: never wired


class ElectrocutionerTest(unittest.TestCase):
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
        cls.machine = MACHINE.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.tune = cls.logic[cls.logic.index("namespace Tune"):cls.logic.index("// Beats: RB-17")]

    def _tune(self, name: str) -> str:
        match = re.search(rf"\b{name}\s*(?:=\s*|\{{)([^;}}]+?)\s*(?:;|\}};)", self.tune)
        self.assertIsNotNone(match, name)
        return match.group(1).replace(" ", "")

    # --- the spells ---------------------------------------------------------------------------------------------------

    def test_the_spells_sit_in_the_d3_slice(self):
        self.assertEqual(sorted(self.spells), list(range(FIRST, FIRST + len(NAMES))))
        self.assertEqual(id_blocks.out_of_reservation("gnomeregan", {"spell": list(self.spells)}), [])
        self.assertIn("kSpellsElectrocutioner{ 214380, 214419 }", self.header)
        self.assertRegex(self.logic, rf"kSpellCount = {len(NAMES)};")

    def test_the_cpp_names_the_same_ids(self):
        for offset, name in enumerate(NAMES):
            self.assertRegex(self.logic, rf"{name}\s*=\s*kSpellSlice\.first \+ {offset},", name)

    def test_the_hits_are_nature_resolve_copies(self):
        for spell_id in HITS:
            with self.subTest(spell=spell_id):
                spell = self.spells[spell_id]
                self.assertEqual(spell["school"], SCHOOL_NATURE)
                self.assertEqual(spell["effect1"]["type"], EFFECT_SCHOOL_DAMAGE)
                self.assertIn((spell_id, "spell_boss_mechanics_resolve"), self.scripts)
                self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & IGNORE_CASTER_MODIFIERS)
        # the C++ hands each to the registry, the tank row with it (rule 17)
        for name in ("SPELL_MEGAVOLT_HIT", "SPELL_CHAIN_BOLT_HIT", "SPELL_SHOCK_HIT", "SPELL_DISCHARGE_HIT"):
            self.assertIn(name, self.script)
        self.assertIn(".Spell(SPELL_JUSTICE_HIT)", self.machine)
        self.assertIn(".Damage(pct).TankDamage(pct)", self.machine)
        self.assertIn(".Damage(pct).TankDamage(pct)", self.script)
        self.assertEqual(self.script.count("spec.tankPct = pct;"), 3)

    def test_only_chain_bolt_can_be_kicked(self):
        # s7 #9 A: Chain Bolt is the Nature kick; Megavolt and Justice are Physical bars nobody can interrupt.
        for spell_id, spell in self.spells.items():
            raw = spell["raw_overrides"]
            with self.subTest(spell=spell_id):
                if spell_id == CHAIN_BOLT:
                    self.assertEqual((raw["InterruptFlags"], raw["PreventionType"]), (15, 1))
                    self.assertEqual(spell["school"], SCHOOL_NATURE)
                else:
                    self.assertEqual(int(raw.get("InterruptFlags", 0)), 0)
        for spell_id, cast_ms in ((JUSTICE_BAR, el.JUSTICE_CAST_MS), (MEGAVOLT_BAR, el.MEGAVOLT_CAST_MS)):
            spell = self.spells[spell_id]
            self.assertEqual(spell["school"], SCHOOL_PHYSICAL, spell_id)
            self.assertEqual(int(spell["raw_overrides"]["PreventionType"]), 0, spell_id)
            self.assertEqual(spell["cast_time_ms"], cast_ms, spell_id)
            self.assertEqual(spell["effect1"]["type"], EFFECT_DUMMY, spell_id)
            self.assertTrue(spell["raw_overrides"]["AttributesEx2"] & DO_NOT_RESET_COMBAT_TIMERS, spell_id)
        # the casts the script makes untriggered, at a target in range
        chain, shock = self.spells[CHAIN_BOLT], self.spells[SHOCK]
        self.assertEqual(chain["cast_time_ms"], el.CHAIN_CAST_MS)
        self.assertEqual(shock["cast_time_ms"], 0)
        self.assertEqual(shock["school"], SCHOOL_NATURE)
        for spell in (chain, shock):
            self.assertEqual(float(spell["range_yards"]), 100.0)
            self.assertEqual(spell["effect1"]["type"], EFFECT_DUMMY)
        self.assertIn("me->CastSpell(target, SPELL_CHAIN_BOLT, false)", self.script)
        self.assertIn("me->CastSpell(target, SPELL_SHOCK, false)", self.script)
        self.assertIn("me->CastSpell(me, SPELL_MEGAVOLT_BAR, false)", self.script)
        self.assertIn("owner->CastSpell(owner, j.barSpellId, false)", self.machine)
        # the descriptor's interrupt entry names Chain Bolt only
        self.assertIn("d.interrupts.emplace_back(0u, uint32(SPELL_CHAIN_BOLT)", self.script)
        self.assertEqual(self.script.count("d.interrupts."), 1)

    def test_the_header_numbers_are_the_dts(self):
        self.assertEqual(self._tune("kJusticeCastMs"), str(el.JUSTICE_CAST_MS))
        self.assertEqual(self._tune("kMegavoltCastMs"), str(el.MEGAVOLT_CAST_MS))
        self.assertEqual(self._tune("kChainCastMs"), str(el.CHAIN_CAST_MS))
        self.assertEqual(self._tune("kVoltageStackLimit"), str(el.STACK_LIMIT))
        self.assertEqual(self._tune("kMegavoltPct"), "40.f,60.f")
        self.assertEqual(self._tune("kChainPct"), "20.f,40.f")
        self.assertEqual(self._tune("kShockPct"), "10.f,15.f")
        self.assertEqual(self._tune("kJusticePct"), "75.f")
        self.assertEqual(self._tune("kDischargePct"), "40.f")
        self.assertEqual(self._tune("kLightningPctPerStack"), "0.f,3.f")
        # BM-G's names (STAGE-BM-G-REPORT, shared-file request): the move cost and the band
        self.assertEqual(self._tune("kStaticBotStandAbove"), "12")
        self.assertEqual(self._tune("kRangedBandMinYd"), "11.f")
        self.assertEqual(self._tune("kRangedBandMaxYd"), "12.f")
        self.assertIn("d.moveCosts.emplace_back(uint32(SPELL_STATIC), Tune::kStaticBotStandAbove)", self.script)
        self.assertIn("d.rangeBands.emplace_back(Tune::kRangedBandMinYd, Tune::kRangedBandMaxYd)", self.script)

    def test_static_and_voltage_stack_and_cannot_be_dispelled(self):
        for spell_id in (VOLTAGE, CHARGED, STATIC):
            spell = self.spells[spell_id]
            raw = spell["raw_overrides"]
            with self.subTest(spell=spell_id):
                self.assertEqual(spell["dispel"], 0)
                self.assertTrue(spell["attributes"] & NO_IMMUNITIES)
                self.assertEqual(raw["CumulativeAura"], el.STACK_LIMIT)
                self.assertEqual(spell["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertTrue(self.spells[STATIC]["attributes"] & AURA_IS_DEBUFF)
        self.assertEqual(self.spells[STATIC]["duration_ms"], el.STATIC_MS)
        self.assertFalse(self.spells[VOLTAGE]["attributes"] & AURA_IS_DEBUFF)
        self.assertEqual(self.spells[VOLTAGE]["duration_ms"], -1)
        self.assertTrue(self.spells[CHARGED]["attributes"] & DO_NOT_DISPLAY)

    def test_the_looks_are_the_approved_picks(self):
        for spell_id, visual in ((VOLTAGE, visuals.EL_VOLTAGE), (CHARGED, visuals.EL_VOLTAGE_2),
                                 (JUSTICE_BAR, visuals.EL_JUSTICE_CAST), (JUSTICE_BLAST, visuals.EL_JUSTICE_BLAST),
                                 (MEGAVOLT_BAR, visuals.EL_MEGAVOLT), (CHAIN_BOLT, visuals.EL_CHAIN),
                                 (CHAIN_HIT, visuals.EL_CHAIN), (SHOCK, visuals.EL_SHOCK), (STATIC, visuals.EL_STATIC),
                                 (DISCHARGE_LOOK, visuals.EL_DISCHARGE)):
            self.assertEqual(self.spells[spell_id]["raw_overrides"]["SpellVisualID_1"], visual, spell_id)
        wired = {self.spells[s]["raw_overrides"].get("SpellVisualID_1") for s in self.spells}
        self.assertFalse(wired & WRONG_VISUALS)

    # --- the creatures ------------------------------------------------------------------------------------------------

    def test_his_row_and_the_stalker(self):
        row = self.edits[ELECTROCUTIONER]
        self.assertEqual(row["ScriptName"], "boss_electrocutioner_rework")
        self.assertEqual(float(row["HealthModifier"]), el.HEALTH_MODIFIER)
        self.assertIn(f"float constexpr kElectrocutioner = {el.HEALTH_MODIFIER}f;", self.header)
        stalker = self.creatures[BLAST_STALKER]
        self.assertEqual(stalker.get("ScriptName", ""), "")
        self.assertEqual(int(stalker["unit_flags"]), 0x2 | 0x02000000)
        self.assertEqual(int(stalker["flags_extra"]), 0x40)
        self.assertEqual(int(self.models[BLAST_STALKER]["CreatureDisplayID"]), visuals.DISPLAY_INVISIBLE_STALKER)
        self.assertIn(f"NPC_BLAST_STALKER           = {BLAST_STALKER},", self.header)
        self.assertIn("NPC_BLAST_STALKER", self.machine)

    # --- the texts ----------------------------------------------------------------------------------------------------

    def test_the_texts(self):
        # rule 35: the stock group 0 stays (never deleted); the new groups are the Logic header's.
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 6235 AND `GroupID` BETWEEN 1 AND 3;", self.sql)
        self.assertNotRegex(self.sql, r"`GroupID` (=|BETWEEN) 0")
        rows = re.findall(r"\(6235, (\d), 0, '((?:[^']|'')*)', (\d+),", self.sql)
        self.assertEqual([(int(g), int(t)) for g, _text, t in rows], [(1, 14), (2, 41), (3, 41)])
        self.assertEqual(rows[0][1], "Court is in session!")
        self.assertEqual(rows[1][1], "%s reaches 6000 volts! Get under the machine!")
        self.assertEqual(rows[2][1], "%s overloads! Get away from the machine!")
        for name, group in (("SAY_JUSTICE", 0), ("SAY_AGGRO", 1), ("EMOTE_JUSTICE_DONUT", 2),
                            ("EMOTE_JUSTICE_CIRCLE", 3)):
            self.assertRegex(self.logic, rf"{name}\s*=\s*{group},", name)

    # --- the drill ----------------------------------------------------------------------------------------------------

    def test_the_drill_tags_match_bm(self):
        bm_src = os.environ.get("BM_SRC")
        drill = Path(bm_src) / "MechanicDrill.h" if bm_src else None
        if not drill or not drill.is_file():
            self.skipTest("BM_SRC is not set to mod-boss-mechanics' src")
        bm = dict((name, int(value)) for name, value in re.findall(
            r"constexpr std::uint32_t (kGnTag\w+) = (\d+);", drill.read_text(encoding="utf-8")))
        table = re.findall(r"\{ (TAG_\w+), \"(kGnTag\w+)\" \}", self.logic)
        self.assertEqual(len(table), 9)
        for tag_name, drill_name in table:
            value = int(re.search(rf"\b{tag_name}\s*=\s*(\d+),", self.logic).group(1))
            self.assertEqual(bm.get(drill_name), value, drill_name)


if __name__ == "__main__":
    unittest.main()
