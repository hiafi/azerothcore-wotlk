"""
Ragefire Chasm build WP-D4H, Starving (Taragaman's hard mode): source/npcs/ragefire_chasm/taragaman_hard_mode.py (the
spells 213690-213695 and the Blood Globule 300987), data/sql/updates/pending_db_world/
rev_taragaman_hard_mode_ragefire_chasm.sql (his lines 7-9, the Blood Shrine and the pour spot) and the C++ they must
agree with (modules/mod-dungeon-bosses src/RagefireChasm/TaragamanHardModeLogic.h, taragaman_hard_mode.cpp and
RagefireChasmRework.h).

Checks:
  - the six spells sit in the D4H slice and the C++ names the same ids; the burst is a Shadow resolve copy; the
    carrier's aura is 10 min, dropped on a map change and not dispellable; the red aura holds a wipe; the looks use the
    V constants;
  - the globule: level 60, 6,000 health, its heroic entry the last of WP-H's mint order, no taunt, no knockback, no
    assistance calls, no loot, the stock crimson slime;
  - the SQL: three texts (8 a boss emote), two goobers with the V displays and the scripts the C++ registers, heroic
    spawns only, at the header's spots;
  - the trigger: bots are refused first and silently, the pour reads the flag back before it takes the blood;
  - the burst's tag is the drill's, and its bots' bounds are his arena's.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_ragefire_chasm_taragaman_hard_mode.py
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

SRC = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "RagefireChasm"
SQL = (REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world"
       / "rev_taragaman_hard_mode_ragefire_chasm.sql")

FIRST, LAST = 213690, 213719
NAMES = ("SPELL_HM_HUNGERERS_BLOOD", "SPELL_HM_POUR", "SPELL_HM_STARVING", "SPELL_HM_BLOOD_LAKE", "SPELL_HM_BURST",
         "SPELL_HM_BURST_LOOK")
ID = {name: FIRST + offset for offset, name in enumerate(NAMES)}
GLOBULE, SHRINE, POUR = 300987, 301340, 301341
EFFECT_SCHOOL_DAMAGE, EFFECT_DUMMY, EFFECT_APPLY_AURA, AURA_DUMMY = 2, 3, 6, 4
SHADOW = 32
TARGET_UNIT_CASTER = 1
CHANGE_MAP = 0x00080000
ATTR0_NO_IMMUNITIES = 0x20000000
ATTR1_AURA_STAYS_AFTER_COMBAT = 0x02000000
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
ATTR3_DEATH_PERSISTENT = 0x00100000


def _fields(row: str) -> list:
    """A VALUES tuple's fields: quoted strings and numbers."""
    out: list = []
    for quoted, number in re.findall(r"'((?:[^']|'')*)'|(-?\d+(?:\.\d+)?)", row):
        out.append(float(number) if number else quoted.replace("''", "'"))
    return out


class StarvingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = npcs_test._load()
        cls.spells = {int(e["id"]): e for e in reg.spells if FIRST <= int(e["id"]) <= LAST}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if FIRST <= int(e["spell_id"]) <= LAST}
        cls.globule = next(e for e in reg.creature_templates if int(e["entry"]) == GLOBULE)
        cls.models = [int(m["CreatureDisplayID"]) for m in reg.creature_template_models
                      if int(m["CreatureID"]) == GLOBULE]
        cls.logic = (SRC / "TaragamanHardModeLogic.h").read_text(encoding="utf-8")
        cls.script = (SRC / "taragaman_hard_mode.cpp").read_text(encoding="utf-8")
        cls.header = (SRC / "RagefireChasmRework.h").read_text(encoding="utf-8")
        cls.tune = cls.header[cls.header.index("namespace Taragaman"):]
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.statements = re.sub(r"^--.*$", "", cls.sql, flags=re.M)

    def _raw(self, name: str) -> dict:
        return self.spells[ID[name]]["raw_overrides"]

    def _tune(self, name: str) -> float:
        match = re.search(rf"\b{name} = ([^;]+);", self.tune)
        self.assertIsNotNone(match, name)
        return float(eval(re.sub(r"(?<=\d)\.f|(?<=\d)f", "", match.group(1)), {"__builtins__": {}}))

    def _point(self, name: str) -> list[float]:
        match = re.search(rf"Point3 constexpr {name}\{{ ([^}}]+) \}};", self.header)
        self.assertIsNotNone(match, name)
        return [float(v.strip().rstrip("f")) for v in match.group(1).split(",")]

    # --- the spells ---------------------------------------------------------------------------------------------------

    def test_the_spells_sit_in_the_d4h_slice(self):
        self.assertEqual(sorted(self.spells), sorted(ID.values()))
        self.assertEqual(id_blocks.out_of_reservation("ragefire_chasm", {"spell": list(self.spells)}), [])
        self.assertIn(f"kSpellsStarving{{ {FIRST}, {LAST} }}", self.header)

    def test_the_cpp_names_the_same_ids(self):
        for offset, name in enumerate(NAMES):
            self.assertRegex(self.logic, rf"{name}\s*=\s*kSpellSlice\.first \+ {offset},\s+// {FIRST + offset} ", name)
        self.assertRegex(self.logic, r"kLastSpell = SPELL_HM_BURST_LOOK;")

    def test_the_carriers_aura(self):
        blood = self.spells[ID["SPELL_HM_HUNGERERS_BLOOD"]]
        raw = self._raw("SPELL_HM_HUNGERERS_BLOOD")
        self.assertEqual((blood["effect1"]["type"], blood["effect1"]["apply_aura"],
                          blood["effect1"]["implicit_target_a"]), (EFFECT_APPLY_AURA, AURA_DUMMY, TARGET_UNIT_CASTER))
        self.assertEqual(blood["duration_ms"], self._tune("kHungerersBloodMs"))
        self.assertEqual(blood["dispel"], 0)
        self.assertTrue(raw["AuraInterruptFlags"] & CHANGE_MAP)     # off the map and at logout
        self.assertFalse(raw.get("AttributesEx3", 0) & ATTR3_DEATH_PERSISTENT)
        self.assertFalse(int(blood.get("attributes") or 0) & ATTR0_NO_IMMUNITIES)

    def test_the_red_aura_holds_a_wipe(self):
        aura = self.spells[ID["SPELL_HM_STARVING"]]
        self.assertEqual((aura["effect1"]["type"], aura["effect1"]["apply_aura"]), (EFFECT_APPLY_AURA, AURA_DUMMY))
        self.assertEqual(aura["duration_ms"], -1)
        self.assertTrue(self._raw("SPELL_HM_STARVING")["AttributesEx"] & ATTR1_AURA_STAYS_AFTER_COMBAT)
        self.assertEqual(self.spells[ID["SPELL_HM_BLOOD_LAKE"]]["duration_ms"], -1)

    def test_the_burst_is_a_shadow_resolve_copy(self):
        burst = self.spells[ID["SPELL_HM_BURST"]]
        self.assertEqual(burst["school"], SHADOW)
        self.assertEqual(burst["effect1"]["type"], EFFECT_SCHOOL_DAMAGE)
        self.assertEqual(self.scripts, {(ID["SPELL_HM_BURST"], "spell_boss_mechanics_resolve")})
        self.assertTrue(self._raw("SPELL_HM_BURST")["AttributesEx3"] & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertRegex(self.logic, r"TAG_HM_BURST\s*= 17,")       # BM's kRfcTagBurst
        self.assertIn(".Within(TaragamanFloorBounds()).Tag(TAG_HM_BURST)", self.script)
        self.assertIn(".Weakened()", self.script)

    def test_the_looks_are_the_visual_constants(self):
        for name, visual in (("SPELL_HM_POUR", visuals.TG_POUR), ("SPELL_HM_STARVING", visuals.TG_HM_AURA),
                             ("SPELL_HM_BLOOD_LAKE", visuals.TG_BLOOD_LAKE),
                             ("SPELL_HM_BURST_LOOK", visuals.TG_GLOBULE_BURST)):
            self.assertEqual(self._raw(name)["SpellVisualID_1"], visual, name)
        for name in ("SPELL_HM_POUR", "SPELL_HM_BURST_LOOK"):
            self.assertEqual(self.spells[ID[name]]["effect1"]["type"], EFFECT_DUMMY, name)

    # --- the globule --------------------------------------------------------------------------------------------------

    def test_the_blood_globule(self):
        g = self.globule
        self.assertEqual((g["name"], g["ScriptName"], g["AIName"]), ("Blood Globule", "npc_rfc_blood_globule", ""))
        self.assertEqual((g["minlevel"], g["maxlevel"], g["rank"], g["unit_class"], g["faction"], g["type"]),
                         (60, 60, 0, 1, 554, 10))
        self.assertAlmostEqual(float(g["HealthModifier"]) * 3052, self._tune("kGlobuleHealth"), delta=1.0)
        self.assertEqual((float(g["DamageModifier"]), int(g["unit_flags"])), (0.0, 0))
        self.assertEqual(int(g["flags_extra"]), 0x40 | 0x100 | 0x40000000 | 0x02000000 | 0x04000000)
        self.assertEqual((g["lootid"], g["mingold"], g["maxgold"], g["CreatureImmunitiesId"]), (0, 0, 0, 0))
        # The extraction's 12 units are minted first, from 310488; the globule after them (STAGE-H s3).
        self.assertEqual(int(g["difficulty_entry_1"]), 310488 + 12)
        self.assertEqual(self.models, [visuals.DISPLAY_BLOOD_GLOBULE])
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_rfc_blood_globule, "
                      "RagefireChasmRework::kInstanceScriptName);", self.script)

    # --- the SQL ------------------------------------------------------------------------------------------------------

    def test_the_texts(self):
        rows = re.findall(r"\(11520, (\d+), 0, '((?:[^']|'')*)', (\d+), 0, 100, 0, 0, 0, 0, (\d+),", self.sql)
        self.assertEqual([(int(r[0]), int(r[2]), int(r[3])) for r in rows], [(7, 14, 0), (8, 41, 3), (9, 14, 0)])
        self.assertEqual([r[1] for r in rows], [
            "The lake bleeds for me! Drink, drink!", "Blood crawls up from the lake toward %s!",
            "That taste... MORE! Bring me MORE!"])
        self.assertIn("BETWEEN 7 AND 9", self.statements)       # 0 to 6 are D4's

    def test_the_trigger_objects(self):
        for entry, display, script in ((SHRINE, visuals.GODI_HM_OBJECT, "go_rfc_blood_shrine"),
                                       (POUR, visuals.GODI_HM_OBJECT_ALT, "go_rfc_pour_spot")):
            with self.subTest(entry=entry):
                row = re.search(rf"\({entry}, 10, [^)]*\)", self.statements)
                self.assertIsNotNone(row)
                fields = _fields(row.group(0))
                # entry, type, display, 4 texts, size, Data0-23, AIName, ScriptName, build
                self.assertEqual(len(fields), 8 + 24 + 3)
                self.assertEqual((fields[2], fields[7]), (display, 1.0))
                self.assertEqual(set(fields[8:32]), {0.0})      # no lock, no spell, no despawn
                self.assertEqual(fields[32:34], ["", script])
                self.assertIn(f"RegisterDungeonReworkGameObjectAI({script}, "
                              "RagefireChasmRework::kInstanceScriptName);", self.script)
                self.assertIn(f"({entry}, 0, 0, 0, 0, 0, 0, 0, 0)", self.statements)
        self.assertRegex(self.header, rf"GO_RFC_BLOOD_SHRINE\s*= {SHRINE},")
        self.assertRegex(self.header, rf"GO_RFC_POUR_SPOT\s*= {POUR},")

    def test_the_spawns_are_heroic_only_and_at_the_headers_spots(self):
        for guid, entry, point in ((3013400, SHRINE, "kBloodShrine"), (3013410, POUR, "kPourSpot")):
            with self.subTest(entry=entry):
                row = re.search(rf"\({guid}, {entry}, [^)]*\)", self.statements)
                self.assertIsNotNone(row)
                fields = _fields(row.group(0).replace("(Starving, heroic only", ""))
                self.assertEqual(fields[:7], [guid, entry, 389, 0, 0, 2, 1])
                self.assertEqual(fields[7:10], self._point(point)[:3])
        for table in ("`creature`", "smart_scripts"):
            self.assertNotIn(table, self.statements)

    # --- the C++ ------------------------------------------------------------------------------------------------------

    def test_the_trigger_is_human_only(self):
        self.assertIn("s.bot = !player->GetSession() || player->GetSession()->IsHeadless();", self.script)
        refusal = re.search(r"Refusal ShrineRefusal\(.*?\n    \}", self.logic, re.S).group(0)
        self.assertLess(refusal.index("s.bot"), refusal.index("ClosedFor"))     # refused before anything else
        for name in ("ShrineRefusal", "PourRefusal"):
            self.assertIn(f"{name}(StateFor(player, instance))", self.script)

    def test_the_pour_reads_the_flag_back_before_it_takes_the_blood(self):
        pour = self.script[self.script.index("Refusal PourBlood("):]
        pour = pour[:pour.index("\n    }")]
        order = [pour.index(s) for s in ("SetData(DATA_HARD_MODE, 1)", "!instance->GetData(DATA_HARD_MODE)",
                                         "DoRemoveAurasDueToSpellOnPlayers(SPELL_HM_HUNGERERS_BLOOD)")]
        self.assertEqual(order, sorted(order))
        self.assertEqual(self.script.count("SetData(DATA_HARD_MODE"), 1)

    def test_the_instance_keeps_the_loot_bit_and_the_kill_slot(self):
        for name in ("SetHardModeLoot", "AddLootMode", "SetBossState"):
            self.assertNotIn(name, self.script)

    def test_the_summons_and_handles_are_d4s_to_clean_up(self):
        fight = self.script[self.script.index("class StarvingFight"):]
        fight = fight[:fight.index("// `.dbtest rfc starving` (the")]
        self.assertNotIn("SummonCreature(", fight)
        self.assertEqual(fight.count("fight.Summon("), 3)
        self.assertEqual(fight.count("Mechanic::Circle("), fight.count("fight.Track("))

    def test_the_timer_feast_yields_to_a_due_combo(self):
        # RF-1 RF-M2: the rule the host test runs is the one the fight asks.
        self.assertIn("return TimerFeastMay(fight.ClockMs(), fight.LastFeastMs(), _combo);", self.script)

    def test_the_bots_kill_order(self):
        self.assertIn("Condition::NearUnit(NPC_TARAGAMAN, tier.withinYd)", self.script)
        self.assertIn("TargetEntry(NPC_RFC_BLOOD_GLOBULE, -1, Who::Tank)", self.script)


if __name__ == "__main__":
    unittest.main()
