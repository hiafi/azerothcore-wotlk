"""
Scarlet Monastery build WP-D11, Herod: source/npcs/scarlet_monastery/herod.py (his columns and the Scarlet Trainee's
health behind the wave switch, the spells 212980-212993) and the C++ they must agree with (modules/mod-dungeon-bosses
src/ScarletMonastery/HerodLogic.h, HerodFight.h and boss_herod_rework.cpp).

Checks:
  - the fourteen spells sit in the D11 slice and the C++ names the same ids; the registry's (and RegistryHit's) hits
    are resolve copies in their schools (the blades Holy, the rest Physical); the cleave's tank hit carries 15 / 25 in
    hundredths and binds the kit's percent script; Frenzy is +30% melee haste, +20% Physical damage, +15% size for the
    fight, not dispellable; the cyclone carries no immunity (the stock Whirlwind's is gone); no spell has a cast time
    (nothing to interrupt: the build spec's interrupt list is empty); the looks use the V constants (never SV 6664 or
    9220) and the missiles fly;
  - the wave gate: the AI registers behind kWave2Bound, `.dbtest sm herod` always; his columns (script, 66k, the stock
    DamageModifier 3.8, immunity 1972, INSTANCE_BIND) and the trainee's 400 only once wave 2 binds;
  - the numbers the dbc-tools file pins are the header's; the text range is S0's (0-4 stock, 5-8 the hard mode's), and
    D11 writes no text of its own (no SQL rev);
  - the hard mode's hooks: HerodFight.h declares the factory, the taunt handler and the idle hook; the AI routes the
    /taunt (text emote 136) to it and defines all three.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scarlet_monastery_herod.py
"""

from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import test_id_blocks as id_blocks  # noqa: E402
from lib import test_scarlet_monastery_kit as kit_test  # noqa: E402
from source.npcs.scarlet_monastery import _common as common  # noqa: E402
from source.npcs.scarlet_monastery import _visuals as visuals  # noqa: E402

MDB = REPO_ROOT / "modules" / "mod-dungeon-bosses"
LOGIC = MDB / "src" / "ScarletMonastery" / "HerodLogic.h"
FIGHT = MDB / "src" / "ScarletMonastery" / "HerodFight.h"
SCRIPT = MDB / "src" / "ScarletMonastery" / "boss_herod_rework.cpp"
HEADER = MDB / "src" / "ScarletMonastery" / "ScarletMonasteryRework.h"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_herod_scarlet_monastery.sql"
DT_FILE = TOOL_ROOT / "source" / "npcs" / "scarlet_monastery" / "herod.py"

SLICE = range(212980, 213020)
FIRST = 212980
NAMES = ("SPELL_HB_CYCLONE", "SPELL_HB_OUT", "SPELL_HB_LAP", "SPELL_HB_BLADE", "SPELL_HB_BLADE_LOOK", "SPELL_HB_HOME",
         "SPELL_HB_THROW", "SPELL_HB_THROW_LOOK", "SPELL_HB_AXE_SPIN", "SPELL_HB_RETURN", "SPELL_HB_WHIRL",
         "SPELL_HB_CLEAVE", "SPELL_HB_CLEAVE_TANK", "SPELL_HB_FRENZY")
EFFECT_SCHOOL_DAMAGE, EFFECT_APPLY_AURA, EFFECT_DUMMY = 2, 6, 3
AURA_DUMMY, AURA_SCHOOL_IMMUNITY, AURA_MOD_SCALE = 4, 39, 61
AURA_MOD_DAMAGE_PERCENT_DONE, AURA_MOD_MELEE_HASTE = 79, 138
SCHOOL_PHYSICAL, SCHOOL_HOLY = 1, 2
TARGET_DEST_DEST = 87
HEROD, TRAINEE = 3975, 6575
RESOLVE_PHYSICAL = (1, 2, 5, 6, 9, 10, 11)      # out, lap, home, throw, return, whirl, cleave (offsets)
RESOLVE_HOLY = (3,)                             # the blade


class HerodTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = kit_test._load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits}
        cls.logic = LOGIC.read_text(encoding="utf-8")
        cls.fight = FIGHT.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.dt = DT_FILE.read_text(encoding="utf-8")

    def _dt(self, name: str):
        """A module constant of herod.py, read from its text (importing it outside a load registers nothing)."""
        match = re.search(rf"^{name} = (.+?)(?:\s+#.*)?$", self.dt, re.M)
        self.assertIsNotNone(match, name)
        return ast.literal_eval(match.group(1))

    def _const(self, name: str) -> str:
        match = re.search(rf"{name}\s*(?:=|\{{)\s*([^;}}]+?)\s*(?:;|\}};)", self.logic)
        self.assertIsNotNone(match, name)
        return match.group(1).replace(" ", "")

    # --- the spells ---------------------------------------------------------------------------------------------------

    def test_the_spells_sit_in_the_d11_slice(self):
        self.assertEqual(sorted(self.spells), list(range(FIRST, FIRST + len(NAMES))))
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery", {"spell": list(self.spells)}), [])
        self.assertIn("kSpellsHerod{ 212980, 213019 }", re.sub(r"\s+", " ", self.header))

    def test_the_cpp_names_the_same_ids(self):
        for offset, name in enumerate(NAMES):
            self.assertRegex(self.logic, rf"{name}\s*=\s*kSpellSlice\.first \+ {offset},", name)
        self.assertRegex(self.logic, r"static_assert\(SPELL_HB_FRENZY <= kSpellSlice\.last")

    def test_the_hits_are_resolve_copies_in_their_schools(self):
        for offsets, school in ((RESOLVE_PHYSICAL, SCHOOL_PHYSICAL), (RESOLVE_HOLY, SCHOOL_HOLY)):
            for offset in offsets:
                spell_id = FIRST + offset
                spell = self.spells[spell_id]
                self.assertEqual(spell["school"], school, spell_id)
                self.assertEqual(spell["effect1"]["type"], EFFECT_SCHOOL_DAMAGE, spell_id)
                self.assertIn((spell_id, "spell_boss_mechanics_resolve"), self.scripts, spell_id)
                self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & 0x20000000, spell_id)   # rule 2
        # the C++ hands each hit its own copy and school
        for name, school in (("SPELL_HB_OUT", "NORMAL"), ("SPELL_HB_LAP", "NORMAL"), ("SPELL_HB_BLADE", "HOLY"),
                             ("SPELL_HB_HOME", "NORMAL"), ("SPELL_HB_THROW", "NORMAL"), ("SPELL_HB_RETURN", "NORMAL"),
                             ("SPELL_HB_WHIRL", "NORMAL"), ("SPELL_HB_CLEAVE", "NORMAL")):
            self.assertRegex(self.script, rf"SPELL_SCHOOL_{school}\b[^;]*?\b{name}\b|"
                                          rf"spellId = {name};", name)

    def test_the_cleave_tank_hit_binds_the_kit_script(self):
        spell = self.spells[FIRST + 12]
        effect = spell["effect1"]
        self.assertEqual(effect["type"], EFFECT_SCHOOL_DAMAGE)
        self.assertEqual(effect["base_points"] + effect["die_sides"], 1500)
        self.assertEqual(spell["raw_overrides"]["EffectMiscValueB_1"], 2500)
        self.assertIn((FIRST + 12, "spell_dungeon_refflat_damage"), self.scripts)
        self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & 0x20000000)
        self.assertEqual(self._const("kCleaveTankPct"), "15.f,25.f")
        self.assertEqual(self._dt("CLEAVE_TANK_PCT"), (1500, 2500))

    def test_frenzy(self):
        spell = self.spells[FIRST + 13]
        self.assertEqual(spell["duration_ms"], -1)
        self.assertEqual((spell["dispel"], spell["mechanic"]), (0, 0))
        auras = {spell[f"effect{i}"]["apply_aura"]: spell[f"effect{i}"] for i in (1, 2, 3)}
        for aura, value in ((AURA_MOD_MELEE_HASTE, 30), (AURA_MOD_DAMAGE_PERCENT_DONE, 20), (AURA_MOD_SCALE, 15)):
            self.assertEqual(auras[aura]["base_points"] + auras[aura]["die_sides"], value, aura)
        self.assertEqual(auras[AURA_MOD_DAMAGE_PERCENT_DONE]["misc_value"], 1)              # Physical only
        self.assertEqual(self._const("kFrenzyHastePct"), "30.f")
        self.assertEqual(self._const("kFrenzyDamagePct"), "20.f")
        self.assertEqual(self._const("kFrenzyAtPct"), "50.f")
        self.assertEqual((self._dt("FRENZY_HASTE_PCT"), self._dt("FRENZY_DAMAGE_PCT")), (30, 20))

    def test_the_cyclone_has_no_immunity_and_nothing_casts(self):
        cyclone = self.spells[FIRST]
        self.assertEqual((cyclone["effect1"]["type"], cyclone["effect1"]["apply_aura"]),
                         (EFFECT_APPLY_AURA, AURA_DUMMY))
        for spell_id, spell in self.spells.items():
            for i in (1, 2, 3):
                effect = spell.get(f"effect{i}")
                if effect:
                    self.assertNotEqual(effect.get("apply_aura"), AURA_SCHOOL_IMMUNITY, spell_id)
            self.assertEqual(spell["cast_time_ms"], 0, spell_id)        # no cast bar, nothing to kick
            self.assertFalse(spell["raw_overrides"].get("InterruptFlags", 0), spell_id)

    def test_the_looks_use_the_v_constants(self):
        for offset, visual in ((0, visuals.HB_CYCLONE), (4, visuals.HB_BLADE), (7, visuals.HB_THROW),
                               (8, visuals.HB_FLOOR_SPIN), (11, visuals.HB_CLEAVE), (12, visuals.HB_CLEAVE)):
            self.assertEqual(self.spells[FIRST + offset]["raw_overrides"]["SpellVisualID_1"], visual, offset)
        # the VR corrections: never the doc's dust cloud (6664) or the axe-less throw (9220)
        self.assertEqual((visuals.HB_CYCLONE, visuals.HB_BLADE, visuals.HB_THROW), (7428, 8618, 3962))
        # the missiles fly to a point
        for offset in (4, 7):
            spell = self.spells[FIRST + offset]
            self.assertGreater(spell["raw_overrides"]["Speed"], 0, offset)
            self.assertEqual(spell["effect1"]["implicit_target_a"], TARGET_DEST_DEST, offset)
        # the lasting looks have no duration
        for offset in (0, 8):
            self.assertEqual(self.spells[FIRST + offset]["duration_ms"], -1, offset)

    # --- the creatures and the wave gate ------------------------------------------------------------------------------

    def test_the_wave_gate(self):
        self.assertRegex(self.script, r"if \(kWave2Bound\)\s*RegisterDungeonReworkCreatureAI\(boss_herod_rework,")
        self.assertRegex(self.script, r'\n    SmTest::RegisterBoss\("herod",')
        self.assertIn("if BIND_WAVE_2:", self.dt)
        if not common.BIND_WAVE_2:
            self.assertNotIn(HEROD, self.edits)
            self.assertNotIn(TRAINEE, self.edits)
            return
        h = self.edits[HEROD]
        self.assertEqual(h["ScriptName"], "boss_herod_rework")
        self.assertEqual(h["AIName"], "")
        self.assertEqual(h["CreatureImmunitiesId"], 1972)
        self.assertEqual(h["flags_extra"], 1)
        self.assertAlmostEqual(h["HealthModifier"] * 1336, 66000, delta=5)
        self.assertEqual(h["DamageModifier"], 3.8)
        self.assertAlmostEqual(self.edits[TRAINEE]["HealthModifier"] * 737, 400, delta=1)
        self.assertEqual(set(self.edits[TRAINEE]["_update_columns"]), {"HealthModifier"})

    def test_the_numbers_are_the_headers(self):
        self.assertAlmostEqual(self._dt("HEROD_HEALTH_MODIFIER") * int(self._const("kHerodBaseHealthL37Warrior")),
                               int(self._const("kHerodHealth").split(",")[0]), delta=5)
        self.assertAlmostEqual(self._dt("TRAINEE_HEALTH_MODIFIER") * int(self._const("kTraineeBaseHealthL30Mage")),
                               int(self._const("kTraineeHealth").split(",")[0]), delta=1)
        self.assertEqual(self._const("kHerodHealth"), "66000,320000")
        self.assertEqual(self._const("kTraineeHealth"), "400,2500")
        self.assertEqual(self._const("kHitPct"), "30.f,45.f")
        self.assertEqual(self._const("kItemRavager"), "7612")

    def test_the_texts_are_s0s_range_and_d11_writes_none(self):
        self.assertRegex(re.sub(r"\s+", " ", self.header), r"\{ NPC_HEROD, 0, 9, 5 \}")
        self.assertRegex(re.sub(r"\s+", " ", self.header), r"\{ NPC_SCARLET_TRAINEE, 0, 0, 1 \}")
        for name, group in (("SAY_AGGRO", 0), ("SAY_BLADES", 1), ("SAY_STRENGTH", 2), ("SAY_KILL", 3),
                            ("EMOTE_ENRAGED", 4), ("SAY_TAUNT_ANSWERED", 5), ("SAY_TAUNT_WORDS", 6),
                            ("SAY_RISING", 7), ("EMOTE_GARRISON", 8), ("EMOTE_SEAL", 9)):
            self.assertRegex(self.logic, rf"{name}\s*=\s*{group},", name)
        self.assertFalse(SQL.exists(), "D11 keeps the stock lines 0-4; 5-9 are D11H's rev (9 the seal, F-2c)")
        self.assertRegex(self.script, r"spec\.emoteGroup = EMOTE_SEAL;")

    # --- the hard mode's hooks ----------------------------------------------------------------------------------------

    def test_the_hard_mode_hooks(self):
        for decl in ("void RegisterHerodHardMode(HerodHardModeFactory factory);",
                     "void RegisterHerodTauntHandler(HerodTauntHandler handler);",
                     "void RegisterHerodIdleHook(HerodIdleHook hook);",
                     "std::unique_ptr<HerodHardMode> CreateHerodHardMode(Creature* herod);"):
            self.assertIn(decl, self.fight)
        for name in ("RegisterHerodHardMode", "RegisterHerodTauntHandler", "RegisterHerodIdleHook",
                     "CreateHerodHardMode", "HasHerodHardMode"):
            self.assertRegex(self.script, rf"\bSmHerod::{name}\(", name)
        self.assertRegex(self.logic, r"kTextEmoteTaunt = 136;")
        self.assertRegex(self.script, r"void ReceiveEmote\(Player\* player, uint32 emote\) override")
        self.assertRegex(self.script, r"emote != kTextEmoteTaunt")
        # the instance's flag is read at the pull, heroic only
        self.assertRegex(self.script, r"_heroic && instance && instance->GetData\(DATA_HARD_MODE_HEROD\)")

    def test_the_pull_line_logs_the_hard_modes_health(self):
        # R-2-ARM m-1: the rule-23 pull line comes after the hard mode's OnEngage (400k, not the heroic 320k).
        engage = self.script[self.script.index("void JustEngagedWith(Unit* who) override"):]
        engage = engage[:engage.index("void EnterEvadeMode")]
        self.assertEqual(engage.count("OnBossPull(me, kBossLogName, _hardModeLit);"), 1)
        self.assertLess(engage.index("_hardMode->OnEngage(*this);"),
                        engage.index("OnBossPull(me, kBossLogName, _hardModeLit);"))

    def test_the_threshold_runs_again_before_the_next_beat(self):
        # R-2-ARM M-2: after the spin and the axe update, the threshold again; a pending one holds the next beat.
        update = re.sub(r"\s+", " ", self.script)
        self.assertIn("UpdateThreshold(); UpdateSpin(); UpdateAxe(); UpdateThreshold();", update)
        self.assertIn("!BeatMayStart(ThresholdPending(", update)


if __name__ == "__main__":
    unittest.main()
