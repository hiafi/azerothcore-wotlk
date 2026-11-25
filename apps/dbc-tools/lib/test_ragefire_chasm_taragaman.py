"""
Ragefire Chasm build WP-D4, Taragaman the Hungerer: source/npcs/ragefire_chasm/taragaman.py (the spells 213650-213668;
his columns are test_ragefire_chasm_npcs.py's), data/sql/updates/pending_db_world/rev_taragaman_ragefire_chasm.sql (his
texts 0-6 and the Searing Spike's template) and the C++ they must agree with (modules/mod-dungeon-bosses
src/RagefireChasm/TaragamanLogic.h, TaragamanFight.h, boss_taragaman_rework.cpp and RagefireChasmRework.h).

Checks:
  - the nineteen spells sit in the D4 slice and the C++ names the same ids; the ring, the spot and the Nova are resolve
    copies in their schools; the script's hits and heals carry no amount of their own, always hit and ignore caster
    modifiers;
  - rule 25: Devour is a kickable Shadow channel of 5 s whose school no bar shares; the three bars are Fire, as long as
    the header says and not interruptible;
  - the bite, the Devour tick and the pulse are neither reflected nor redirected;
  - Gorged is +10% damage, every school, and nothing else (rule 29: no scale); the mark is not dispellable and dropped
    on a map change; the looks use the V constants (the bite's look never on the channel);
  - the SQL: seven texts (0 a zone yell, the emotes type 41), the spike a generic, non-selectable object with the V
    display and size and the header's;
  - the numbers the dbc-tools file pins are the header's;
  - the hard mode's hooks: TaragamanFight.h declares the factory and the two hooks, the AI defines and calls them, and
    Reset ends with the gate.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_ragefire_chasm_taragaman.py
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
from lib import test_ragefire_chasm_npcs as npcs_test  # noqa: E402
from source.npcs.ragefire_chasm import _visuals as visuals  # noqa: E402

MDB = REPO_ROOT / "modules" / "mod-dungeon-bosses"
SRC = MDB / "src" / "RagefireChasm"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_taragaman_ragefire_chasm.sql"

FIRST = 213650
NAMES = ("SPELL_TG_FEAST_MARK", "SPELL_TG_LEAP_LOOK", "SPELL_TG_BITE", "SPELL_TG_GORGED", "SPELL_TG_GORGE_HEAL",
         "SPELL_TG_DEVOUR", "SPELL_TG_DEVOUR_TICK", "SPELL_TG_DEVOUR_HEAL", "SPELL_TG_FELSTORM_CAST",
         "SPELL_TG_FELSTORM_SPIN", "SPELL_TG_FELSTORM", "SPELL_TG_FEL_PULSE", "SPELL_TG_FEL_SPOT",
         "SPELL_TG_FEL_SPOT_LOOK", "SPELL_TG_SPIKE_LOOK", "SPELL_TG_SPIKE_DIRT", "SPELL_TG_NOVA_CAST",
         "SPELL_TG_NOVA_CAST_HM", "SPELL_TG_NOVA")
ID = {name: FIRST + offset for offset, name in enumerate(NAMES)}
EFFECT_SCHOOL_DAMAGE, EFFECT_DUMMY, EFFECT_APPLY_AURA, EFFECT_HEAL = 2, 3, 6, 10
AURA_DUMMY, AURA_MOD_DAMAGE_PERCENT_DONE = 4, 79
PHYSICAL, FIRE, SHADOW = 1, 4, 32
ATTR1_IS_CHANNELED = 0x4
ATTR1_NO_REDIRECTION, ATTR1_NO_REFLECTION = 0x8, 0x80
ATTR2_IGNORE_LOS = 0x4
ATTR3_ALWAYS_HIT, ATTR3_IGNORE_CASTER_MODIFIERS = 0x00040000, 0x20000000
CHANGE_MAP = 0x00080000
SPIKE_GO = 301342


class TaragamanTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = npcs_test._load()
        cls.spells = {int(e["id"]): e for e in reg.spells if FIRST <= int(e["id"]) <= 213689}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if FIRST <= int(e["spell_id"]) <= 213689}
        cls.logic = (SRC / "TaragamanLogic.h").read_text(encoding="utf-8")
        cls.fight = (SRC / "TaragamanFight.h").read_text(encoding="utf-8")
        cls.script = (SRC / "boss_taragaman_rework.cpp").read_text(encoding="utf-8")
        header = (SRC / "RagefireChasmRework.h").read_text(encoding="utf-8")
        cls.header = header
        cls.tune = header[header.index("namespace Taragaman"):]
        cls.sql = SQL.read_text(encoding="utf-8")

    def _raw(self, name: str) -> dict:
        return self.spells[ID[name]]["raw_overrides"]

    def _tune(self, name: str) -> list[float]:
        match = re.search(rf"\b{name}(?:\{{ ([^}}]+) \}}| = ([^;]+));", self.tune)
        self.assertIsNotNone(match, name)
        return [float(v.strip().rstrip("f")) for v in (match.group(1) or match.group(2)).split(",")]

    # --- the spells ---------------------------------------------------------------------------------------------------

    def test_the_spells_sit_in_the_d4_slice(self):
        self.assertEqual(sorted(self.spells), sorted(ID.values()))
        self.assertEqual(id_blocks.out_of_reservation("ragefire_chasm", {"spell": list(self.spells)}), [])
        self.assertIn("kSpellsTaragaman{ 213650, 213689 }", self.header)

    def test_the_cpp_names_the_same_ids(self):
        for offset, name in enumerate(NAMES):
            self.assertRegex(self.logic, rf"{name}\s*=\s*kSpellSlice\.first \+ {offset},\s+// {FIRST + offset} ", name)
        self.assertRegex(self.logic, r"kLastSpell = SPELL_TG_NOVA;")

    def test_the_registry_hits_are_resolve_copies(self):
        for name, school in (("SPELL_TG_FELSTORM", PHYSICAL), ("SPELL_TG_FEL_SPOT", FIRE), ("SPELL_TG_NOVA", FIRE)):
            with self.subTest(spell=name):
                spell = self.spells[ID[name]]
                self.assertEqual(spell["school"], school)
                self.assertEqual(spell["effect1"]["type"], EFFECT_SCHOOL_DAMAGE)
                self.assertIn((ID[name], "spell_boss_mechanics_resolve"), self.scripts)
                self.assertTrue(self._raw(name)["AttributesEx3"] & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertEqual({sid for sid, _ in self.scripts},
                         {ID["SPELL_TG_FELSTORM"], ID["SPELL_TG_FEL_SPOT"], ID["SPELL_TG_NOVA"]})

    def test_the_scripts_hits_and_heals_take_their_amount_from_the_script(self):
        for name, school in (("SPELL_TG_BITE", PHYSICAL), ("SPELL_TG_DEVOUR_TICK", PHYSICAL),
                             ("SPELL_TG_FEL_PULSE", FIRE)):
            with self.subTest(spell=name):
                spell = self.spells[ID[name]]
                self.assertEqual(spell["school"], school)
                self.assertEqual(spell["effect1"]["type"], EFFECT_SCHOOL_DAMAGE)
                self.assertEqual((spell["effect1"]["base_points"], spell["effect1"]["die_sides"]), (0, 0))
                self.assertEqual(spell["range_yards"], 100.0)
                attr3 = self._raw(name)["AttributesEx3"]
                self.assertTrue(attr3 & ATTR3_ALWAYS_HIT and attr3 & ATTR3_IGNORE_CASTER_MODIFIERS)
                self.assertTrue(self._raw(name)["AttributesEx2"] & ATTR2_IGNORE_LOS)
                # Magic class: Spell Reflection or a Grounding Totem would take it (ALWAYS_HIT does not stop the roll).
                both = ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION
                self.assertEqual(self._raw(name)["AttributesEx"] & both, both)
                self.assertEqual(self._raw(name)["PreventionType"], 0)
        for name in ("SPELL_TG_GORGE_HEAL", "SPELL_TG_DEVOUR_HEAL"):
            with self.subTest(spell=name):
                effect = self.spells[ID[name]]["effect1"]
                self.assertEqual((effect["type"], effect["base_points"], effect["die_sides"]), (EFFECT_HEAL, 0, 0))

    def test_devour_is_a_kickable_shadow_channel_no_bar_shares_its_school(self):
        devour = self.spells[ID["SPELL_TG_DEVOUR"]]
        raw = self._raw("SPELL_TG_DEVOUR")
        self.assertEqual(devour["school"], SHADOW)
        self.assertEqual(devour["duration_ms"], int(self._tune("kDevourTicks")[0] * self._tune("kDevourTickMs")[0]))
        self.assertEqual(devour["range_yards"], self._tune("kDevourRangeYd")[0])
        self.assertEqual(devour["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertTrue(raw["AttributesEx"] & ATTR1_IS_CHANNELED)
        self.assertTrue(raw["AttributesEx2"] & ATTR2_IGNORE_LOS)
        self.assertEqual((raw["ChannelInterruptFlags"], raw["PreventionType"]), (0x08, 1))
        self.assertTrue(raw["AuraInterruptFlags"] & CHANGE_MAP)
        cast_ms = self._tune("kNovaCastMs")
        for name, ms in (("SPELL_TG_FELSTORM_CAST", self._tune("kFelstormCastMs")[0]),
                         ("SPELL_TG_NOVA_CAST", cast_ms[0]), ("SPELL_TG_NOVA_CAST", cast_ms[1]),
                         ("SPELL_TG_NOVA_CAST_HM", cast_ms[2])):
            with self.subTest(spell=name):
                bar = self.spells[ID[name]]
                self.assertEqual(bar["school"], FIRE)
                self.assertFalse(bar["school"] & devour["school"])
                self.assertEqual(bar["cast_time_ms"], ms)
                self.assertEqual(bar["effect1"]["type"], EFFECT_DUMMY)
                self.assertEqual((self._raw(name)["InterruptFlags"], self._raw(name)["PreventionType"]), (0, 0))

    def test_gorged_is_damage_only(self):
        gorged = self.spells[ID["SPELL_TG_GORGED"]]
        effect = gorged["effect1"]
        self.assertEqual((effect["apply_aura"], effect["base_points"] + effect["die_sides"], effect["misc_value"]),
                         (AURA_MOD_DAMAGE_PERCENT_DONE, self._tune("kGorgedPct")[0], 127))
        self.assertFalse((gorged.get("effect2") or {}).get("type"))
        self.assertEqual((gorged["duration_ms"], gorged["dispel"]), (-1, 0))
        self.assertEqual(self._raw("SPELL_TG_GORGED")["CumulativeAura"], 255)
        self.assertEqual(self._tune("kGorgedCap"), [3, 0, 0])

    def test_the_mark(self):
        mark = self.spells[ID["SPELL_TG_FEAST_MARK"]]
        self.assertEqual(mark["dispel"], 0)
        self.assertEqual(mark["duration_ms"], max(self._tune("kFeastMarkMs")))
        self.assertTrue(self._raw("SPELL_TG_FEAST_MARK")["AuraInterruptFlags"] & CHANGE_MAP)

    def test_the_spin_look_outlasts_every_spin(self):
        self.assertEqual(self.spells[ID["SPELL_TG_FELSTORM_SPIN"]]["duration_ms"], max(self._tune("kFelstormSpinMs")))

    def test_the_looks_are_the_visual_constants(self):
        for name, visual in (("SPELL_TG_FEAST_MARK", visuals.TG_FEAST_MARK), ("SPELL_TG_LEAP_LOOK", visuals.TG_LEAP),
                             ("SPELL_TG_BITE", visuals.TG_BITE), ("SPELL_TG_DEVOUR", visuals.TG_DEVOUR_CHANNEL),
                             ("SPELL_TG_FELSTORM_SPIN", visuals.TG_FELSTORM),
                             ("SPELL_TG_FEL_PULSE", visuals.TG_FEL_PULSE),
                             ("SPELL_TG_FEL_SPOT_LOOK", visuals.TG_FEL_SPOT),
                             ("SPELL_TG_SPIKE_LOOK", visuals.TG_SPIKE_RISE),
                             ("SPELL_TG_SPIKE_DIRT", visuals.TG_SPIKE_RISE_DIRT),
                             ("SPELL_TG_NOVA_CAST", visuals.TG_NOVA), ("SPELL_TG_NOVA_CAST_HM", visuals.TG_NOVA)):
            self.assertEqual(self._raw(name)["SpellVisualID_1"], visual, name)
        self.assertNotEqual(self._raw("SPELL_TG_DEVOUR")["SpellVisualID_1"], visuals.TG_BITE)

    # --- the SQL ------------------------------------------------------------------------------------------------------

    def test_the_texts(self):
        rows = re.findall(r"\(11520, (\d+), 0, '((?:[^']|'')*)', (\d+), 0, 100, 0, 0, 0, 0, (\d+),", self.sql)
        self.assertEqual([int(r[0]) for r in rows], list(range(7)))
        self.assertEqual([int(r[2]) for r in rows], [14, 14, 41, 41, 41, 41, 14])
        self.assertEqual(int(rows[0][3]), 2)        # the zone
        self.assertIn("BETWEEN 0 AND 6", self.sql)  # 7 to 9 are D4H's
        for group in (2, 5):
            self.assertIn("$n", rows[group][1])

    def test_the_searing_spike(self):
        match = re.search(rf"\({SPIKE_GO}, (\d+), (\d+), 'Searing Spike', '', '', '', ([\d.]+),", self.sql)
        self.assertIsNotNone(match)
        self.assertEqual(int(match.group(1)), 5)
        self.assertEqual(int(match.group(2)), visuals.GODI_SEARING_SPIKE)
        self.assertEqual(float(match.group(3)), visuals.SEARING_SPIKE_SIZE)
        self.assertEqual(float(match.group(3)), self._tune("kSpikeGoSize")[0])
        self.assertIn(f"({SPIKE_GO}, 0, 16,", self.sql)
        self.assertRegex(self.header, rf"GO_RFC_SEARING_SPIKE\s*= {SPIKE_GO},")
        statements = re.sub(r"^--.*$", "", self.sql, flags=re.M)
        for table in ("`creature`", "`gameobject`", "smart_scripts"):
            self.assertNotIn(table, statements)

    # --- the C++ ------------------------------------------------------------------------------------------------------

    def test_the_registry_shapes_are_the_drills(self):
        tags = dict(re.findall(r"(TAG_TG_\w+)\s*= (\d+),", self.logic))
        self.assertEqual(tags, {"TAG_TG_RING": "10", "TAG_TG_SPOT": "11", "TAG_TG_NOVA": "12",
                                "TAG_TG_NOVA_PAIR": "13"})
        self.assertEqual(self.script.count(".Within(TaragamanFloorBounds())"), 3)
        self.assertIn("spec.Range(Tune::kNovaRangeYd).Eye(Tune::kNovaEyeYd);", self.script)
        self.assertNotIn(".Behind(", self.script)
        # the fel pulses are never registered
        pulse = self.script[self.script.index("void FelPulse()"):self.script.index("bool FelSpot(")]
        self.assertNotIn("Mechanic::", pulse)

    def test_the_leash_never_turns_him_at_the_rim(self):
        # R-1-BOSS M-1 on the plateau, F-1b's shape: a leash on himself, a reach guard, the edge walk.
        self.assertIn("_arena(TaragamanArena(), SelfLeash(kBoss))", self.script)
        self.assertIn("_reach(ReachArena(), ReachLeash(kBoss))", self.script)
        kit = (SRC / "RagefireChasmKit.cpp").read_text(encoding="utf-8")
        leash = kit[kit.index("ArenaGuardOptions SelfLeash("):]
        leash = leash[:leash.index("return o;")]
        self.assertIn("o.switchWhenVictimOff = false;", leash)
        self.assertIn("o.holdWhileVictimOff = false;", leash)
        resume = self.script[self.script.index("void ResumeFighting()"):]
        self.assertLess(resume.index("ClearFixate()"), resume.index("SelectVictim()"))
        self.assertIn("if (!HoldsNoTarget() && (!_arena.Update(me, diff) || !_reach.Update(me, diff)))", self.script)

    def test_no_assist_calls(self):
        update = self.script[self.script.index("void UpdateAI(uint32 diff)"):]
        self.assertLess(update.index("me->SetAssistanceTimer(0);"), update.index("UpdateVictim()"))

    def test_the_gate_is_last_in_reset(self):
        reset = re.search(r"void Reset\(\) override\s*\{(.*?)\n    \}", self.script, re.S).group(1)
        self.assertTrue(reset.rstrip().endswith("ApplyTaragamanGate(me);"))
        self.assertNotIn("SetHardModeLoot", self.script)

    def test_the_hard_mode_hooks(self):
        for name in ("RegisterTaragamanHardMode", "RegisterTaragamanIdleHook", "RegisterTaragamanActionHook",
                     "CreateTaragamanHardMode"):
            self.assertIn(f" {name}(", self.fight)
            self.assertIn(f"RfcTaragaman::{name}(", self.script)
        for hook in re.findall(r"virtual \S+(?: \S+)? (\w+)\(TaragamanFight", self.fight):
            self.assertIn(f"_hardMode->{hook}(*this", self.script, hook)
        interface = self.fight[self.fight.index("class TaragamanFight\n"):self.fight.index("class TaragamanHardMode\n")]
        methods = re.findall(r"virtual [^~(]*?(\w+)\([^)]*\)(?: const)? = 0;", interface)
        self.assertGreater(len(methods), 20)
        for method in methods:
            self.assertRegex(self.script, rf"\b{method}\([^)]*\)(?: const)? override", method)

    def test_he_walks_back_onto_his_arena(self):
        # RF-1 RF-M1: the engine's step back is held every tick he has a target.
        update = self.script[self.script.index("void UpdateAI("):self.script.index("void StartDueBeat(")]
        self.assertLess(update.index("_edge.HoldBackstep(me);"), update.index("UpdateAct();"))
        self.assertIn("_edge.Update(me, _arena, _reach);", update)


if __name__ == "__main__":
    unittest.main()
