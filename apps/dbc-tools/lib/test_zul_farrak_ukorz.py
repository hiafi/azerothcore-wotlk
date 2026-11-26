"""
Zul'Farrak build WP-D6, Chief Ukorz Sandscalp and Ruuzlu: source/npcs/zul_farrak/ukorz.py (spells 214070-214093, the
stalkers 301025-301026; the two bosses' columns are test_zul_farrak_npcs.py's),
data/sql/updates/pending_db_world/rev_ukorz_zul_farrak.sql (texts 7267 4-7, 7797 0-2) and the C++ they must agree with
(modules/mod-dungeon-bosses src/ZulFarrak/UkorzLogic.h and boss_ukorz_rework.cpp).

Checks:
  - the spells sit in the D6 slice and UkorzLogic.h names the same ids; the Bladestorm and the Creeping Sands ticks are
    resolve copies in their schools; the script's hits carry no amount of their own, always hit, ignore caster
    modifiers and are neither reflected nor redirected (LESSONS L7);
  - rule 24 (the kick lockout): Battle Roar is the only kickable cast (Fire, InterruptFlags 15, PreventionType 1, the
    header's cast times); every bar that must land is Physical and not interruptible;
  - rule 25: Sunk, the quicksand slow and the Lash's debuff are not dispellable; Sunk and the debuff drop on a map
    change; Fury is +3% / +4% damage a stack, 10 stacks, nothing else;
  - the looks use the V constants (appendix C3); the numbers ukorz.py pins are UkorzLogic.h's;
  - the SQL: four new Ukorz lines (the emote type 41 with $n), three Ruuzlu lines, nothing else;
  - the C++: both bosses call NoAssist before UpdateVictim, the stalkers are registered and declared as helpers, the
    descriptor's DPS-only ignore and the kill-together entries are there (s7 #10 A).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_zul_farrak_ukorz.py
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
from lib import test_zul_farrak_npcs as npcs_test  # noqa: E402
from source.npcs.zul_farrak import _visuals as visuals  # noqa: E402

MDB = REPO_ROOT / "modules" / "mod-dungeon-bosses"
SRC = MDB / "src" / "ZulFarrak"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_ukorz_zul_farrak.sql"
DECLARATIONS = TOOL_ROOT / "source" / "npcs" / "zul_farrak" / "ukorz.py"

FIRST, LAST = 214070, 214109
NAMES = ("SPELL_UK_FURY", "SPELL_UK_FURY_HEROIC", "SPELL_UK_FURY_FULL", "SPELL_UK_ROAR", "SPELL_UK_ROAR_HEROIC",
         "SPELL_UK_STORM_WINDUP", "SPELL_UK_STORM_SPIN", "SPELL_UK_STORM", "SPELL_UK_STAMP", "SPELL_UK_STAMP_HEROIC",
         "SPELL_UK_PIT_LOOK", "SPELL_UK_TRAIL_LOOK", "SPELL_UK_QUICKSAND", "SPELL_UK_SUNK", "SPELL_UK_EXECUTE_BAR",
         "SPELL_UK_EXECUTE", "SPELL_UK_CALL", "SPELL_UK_LASH_BAR", "SPELL_UK_LASH_MARK", "SPELL_UK_LASH",
         "SPELL_UK_LASH_DEBUFF", "SPELL_UK_CREEPING", "SPELL_UK_HELD", "SPELL_UK_VENGEANCE")
ID = {name: FIRST + offset for offset, name in enumerate(NAMES)}
BARS = ("SPELL_UK_STORM_WINDUP", "SPELL_UK_STAMP", "SPELL_UK_STAMP_HEROIC", "SPELL_UK_EXECUTE_BAR", "SPELL_UK_CALL",
        "SPELL_UK_LASH_BAR")
EFFECT_SCHOOL_DAMAGE, EFFECT_DUMMY, EFFECT_APPLY_AURA = 2, 3, 6
AURA_DUMMY, AURA_MOD_ROOT, AURA_MOD_DECREASE_SPEED = 4, 26, 33
AURA_MOD_DAMAGE_PERCENT_DONE, AURA_MOD_TOTAL_STAT_PERCENTAGE = 79, 137
PHYSICAL, FIRE, SHADOW = 1, 4, 32
ATTR1_NO_REDIRECTION, ATTR1_NO_REFLECTION = 0x8, 0x80
ATTR2_IGNORE_LOS, ATTR2_DO_NOT_RESET_COMBAT_TIMERS = 0x4, 0x20000
ATTR3_ALWAYS_HIT, ATTR3_IGNORE_CASTER_MODIFIERS = 0x00040000, 0x20000000
CHANGE_MAP = 0x00080000


class _Constants:
    """The module-level constants ukorz.py pins (the declaration file needs the registry's loader to import)."""

    def __init__(self, path: Path):
        for name, value in re.findall(r"^([A-Z][A-Z_0-9]+) = ([^#\n]+?)\s*(?:#.*)?$", path.read_text(), re.M):
            setattr(self, name, ast.literal_eval(value))


ukorz = _Constants(DECLARATIONS)


class UkorzTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = npcs_test._load()
        cls.spells = {int(e["id"]): e for e in reg.spells if FIRST <= int(e["id"]) <= LAST}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if FIRST <= int(e["spell_id"]) <= LAST}
        cls.rows = {int(r["entry"]): r for r in reg.creature_templates}
        cls.logic = (SRC / "UkorzLogic.h").read_text(encoding="utf-8")
        cls.tune = cls.logic[cls.logic.index("namespace Tune"):]
        cls.script = (SRC / "boss_ukorz_rework.cpp").read_text(encoding="utf-8")
        cls.header = (SRC / "ZulFarrakRework.h").read_text(encoding="utf-8")
        cls.sql = SQL.read_text(encoding="utf-8")

    def _raw(self, name: str) -> dict:
        return self.spells[ID[name]]["raw_overrides"]

    def _tune(self, name: str) -> list[float]:
        match = re.search(rf"\b{name}(?:\{{ ([^}}]+) \}}| = ([^;]+));", self.tune)
        self.assertIsNotNone(match, name)
        return [float(v.strip().rstrip("f")) for v in (match.group(1) or match.group(2)).split(",")]

    # --- the spells ---------------------------------------------------------------------------------------------------

    def test_the_spells_sit_in_the_d6_slice(self):
        self.assertEqual(sorted(self.spells), sorted(ID.values()))
        self.assertEqual(id_blocks.out_of_reservation("zul_farrak", {"spell": list(self.spells)}), [])
        self.assertIn(f"kSpellsUkorz{{ {FIRST}, {LAST} }}", self.header)

    def test_the_cpp_names_the_same_ids(self):
        for name, sid in ID.items():
            self.assertRegex(self.logic, rf"\b{name}\s*= {sid},", name)

    def test_the_registry_ticks_are_resolve_copies(self):
        for name, school in (("SPELL_UK_STORM", PHYSICAL), ("SPELL_UK_CREEPING", SHADOW)):
            with self.subTest(spell=name):
                spell = self.spells[ID[name]]
                self.assertEqual(spell["school"], school)
                self.assertEqual(spell["effect1"]["type"], EFFECT_SCHOOL_DAMAGE)
                self.assertIn((ID[name], "spell_boss_mechanics_resolve"), self.scripts)
                self.assertTrue(self._raw(name)["AttributesEx3"] & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertEqual({sid for sid, _ in self.scripts}, {ID["SPELL_UK_STORM"], ID["SPELL_UK_CREEPING"]})

    def test_the_scripts_hits_take_their_amount_from_the_script(self):
        for name, school in (("SPELL_UK_EXECUTE", PHYSICAL), ("SPELL_UK_LASH", SHADOW)):
            with self.subTest(spell=name):
                spell = self.spells[ID[name]]
                raw = self._raw(name)
                self.assertEqual(spell["school"], school)
                self.assertEqual(spell["effect1"]["type"], EFFECT_SCHOOL_DAMAGE)
                self.assertEqual((spell["effect1"]["base_points"], spell["effect1"]["die_sides"]), (0, 0))
                self.assertEqual(spell["range_yards"], 100.0)
                self.assertTrue(raw["AttributesEx3"] & ATTR3_ALWAYS_HIT and raw["AttributesEx3"]
                                & ATTR3_IGNORE_CASTER_MODIFIERS)
                both = ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION
                self.assertEqual(raw["AttributesEx"] & both, both)
                self.assertEqual((raw["InterruptFlags"], raw["PreventionType"]), (0, 0))

    def test_battle_roar_is_the_only_kickable_cast(self):
        cast_ms = self._tune("kRoarCastMs")
        for name, ms in (("SPELL_UK_ROAR", cast_ms[0]), ("SPELL_UK_ROAR_HEROIC", cast_ms[1])):
            with self.subTest(spell=name):
                roar = self.spells[ID[name]]
                raw = self._raw(name)
                self.assertEqual(roar["school"], FIRE)
                self.assertEqual(roar["cast_time_ms"], ms)
                self.assertEqual((raw["InterruptFlags"], raw["PreventionType"]), (15, 1))
                self.assertTrue(raw["AttributesEx2"] & ATTR2_DO_NOT_RESET_COMBAT_TIMERS)
        # Rule 24: a kick locks Fire; every bar that must land is Physical and cannot be interrupted.
        for name in BARS:
            with self.subTest(spell=name):
                bar = self.spells[ID[name]]
                self.assertEqual(bar["school"], PHYSICAL)
                self.assertFalse(bar["school"] & FIRE)
                self.assertEqual(bar["effect1"]["type"], EFFECT_DUMMY)
                self.assertEqual((self._raw(name)["InterruptFlags"], self._raw(name)["PreventionType"]), (0, 0))
                self.assertTrue(self._raw(name)["AttributesEx2"] & ATTR2_DO_NOT_RESET_COMBAT_TIMERS)
        kickable = [sid for sid, s in self.spells.items() if s["raw_overrides"].get("InterruptFlags")]
        self.assertEqual(sorted(kickable), [ID["SPELL_UK_ROAR"], ID["SPELL_UK_ROAR_HEROIC"]])

    def test_the_bar_lengths_are_the_headers(self):
        stamp = self._tune("kStampCastMs")
        for name, ms in (("SPELL_UK_STORM_WINDUP", self._tune("kStormWindupMs")[0]),
                         ("SPELL_UK_STAMP", stamp[0]), ("SPELL_UK_STAMP_HEROIC", stamp[1]),
                         ("SPELL_UK_EXECUTE_BAR", self._tune("kExecuteCastMs")[0]),
                         ("SPELL_UK_CALL", self._tune("kCallCastMs")[0]),
                         ("SPELL_UK_LASH_BAR", self._tune("kLashWarnMs")[0])):
            self.assertEqual(self.spells[ID[name]]["cast_time_ms"], ms, name)
        # the spin's look outlasts every spin (the script cuts it)
        spins = self._tune("kStormSpinMs") + self._tune("kStormRoaredSpinMs")
        self.assertEqual(self.spells[ID["SPELL_UK_STORM_SPIN"]]["duration_ms"], max(spins))

    def test_fury_is_damage_only(self):
        pct = self._tune("kFuryDamagePctPerStack")
        for name, value in (("SPELL_UK_FURY", pct[0]), ("SPELL_UK_FURY_HEROIC", pct[1])):
            with self.subTest(spell=name):
                fury = self.spells[ID[name]]
                effect = fury["effect1"]
                self.assertEqual((effect["apply_aura"], effect["base_points"] + effect["die_sides"],
                                  effect["misc_value"]), (AURA_MOD_DAMAGE_PERCENT_DONE, value, 127))
                self.assertFalse((fury.get("effect2") or {}).get("type"))
                self.assertEqual((fury["duration_ms"], fury["dispel"]), (-1, 0))
                self.assertEqual(self._raw(name)["CumulativeAura"], self._tune("kFuryMaxStacks")[0])
        self.assertEqual(list(ukorz.FURY_PCT), pct)

    def test_nothing_the_fight_needs_can_be_dispelled(self):
        sunk = self.spells[ID["SPELL_UK_SUNK"]]
        self.assertEqual((sunk["effect1"]["apply_aura"], sunk["dispel"], sunk["mechanic"]), (AURA_MOD_ROOT, 0, 0))
        self.assertEqual(sunk["duration_ms"], self._tune("kSunkMs")[0])
        self.assertTrue(self._raw("SPELL_UK_SUNK")["AuraInterruptFlags"] & CHANGE_MAP)
        slow = self.spells[ID["SPELL_UK_QUICKSAND"]]
        self.assertEqual((slow["effect1"]["apply_aura"], slow["effect1"]["base_points"], slow["dispel"]),
                         (AURA_MOD_DECREASE_SPEED, -51, 0))
        debuff = self.spells[ID["SPELL_UK_LASH_DEBUFF"]]
        self.assertEqual((debuff["effect1"]["apply_aura"], debuff["effect1"]["base_points"],
                          debuff["effect1"]["misc_value"], debuff["dispel"]),
                         (AURA_MOD_TOTAL_STAT_PERCENTAGE, -self._tune("kLashStatPct")[0], -1, 0))
        self.assertEqual(debuff["duration_ms"], self._tune("kLashDebuffMs")[0])
        self.assertTrue(self._raw("SPELL_UK_LASH_DEBUFF")["AuraInterruptFlags"] & CHANGE_MAP)
        self.assertEqual(self.spells[ID["SPELL_UK_LASH_MARK"]]["dispel"], 0)
        self.assertNotIn("d.dispels", self.script)

    def test_the_looks_are_the_visual_constants(self):
        for name, visual in (("SPELL_UK_FURY_FULL", visuals.UK_FURY), ("SPELL_UK_ROAR", visuals.UK_ROAR),
                             ("SPELL_UK_ROAR_HEROIC", visuals.UK_ROAR),
                             ("SPELL_UK_STORM_SPIN", visuals.UK_BLADESTORM),
                             ("SPELL_UK_STAMP", visuals.UK_STAMP), ("SPELL_UK_STAMP_HEROIC", visuals.UK_STAMP),
                             ("SPELL_UK_PIT_LOOK", visuals.UK_PIT), ("SPELL_UK_TRAIL_LOOK", visuals.UK_TRAIL),
                             ("SPELL_UK_SUNK", visuals.UK_SUNK), ("SPELL_UK_EXECUTE_BAR", visuals.UK_EXECUTE),
                             ("SPELL_UK_EXECUTE", visuals.UK_EXECUTE), ("SPELL_UK_CALL", visuals.UK_CALL),
                             ("SPELL_UK_LASH_BAR", visuals.UK_LASH), ("SPELL_UK_LASH", visuals.UK_LASH),
                             ("SPELL_UK_HELD", visuals.UK_HELD)):
            self.assertEqual(self._raw(name)["SpellVisualID_1"], visual, name)
        # Never a WRONG look (handoff s3.10): Ground Stomp 5285 is only the stamp's alternate.
        for sid, spell in self.spells.items():
            self.assertNotIn(spell["raw_overrides"].get("SpellVisualID_1"), (5285, 7422), sid)

    def test_the_numbers_are_the_headers(self):
        self.assertEqual(ukorz.FURY_MAX_STACKS, self._tune("kFuryMaxStacks")[0])
        self.assertEqual(list(ukorz.ROAR_CAST_MS), self._tune("kRoarCastMs"))
        self.assertEqual(ukorz.STORM_WINDUP_MS, self._tune("kStormWindupMs")[0])
        self.assertEqual(ukorz.STORM_SPIN_MS, self._tune("kStormRoaredSpinMs")[0])
        self.assertEqual(list(ukorz.STAMP_CAST_MS), self._tune("kStampCastMs"))
        self.assertEqual(ukorz.SUNK_MS, self._tune("kSunkMs")[0])
        self.assertEqual(ukorz.EXECUTE_CAST_MS, self._tune("kExecuteCastMs")[0])
        self.assertEqual(ukorz.CALL_CAST_MS, self._tune("kCallCastMs")[0])
        self.assertEqual(ukorz.LASH_WARN_MS, self._tune("kLashWarnMs")[0])
        self.assertEqual(ukorz.LASH_DEBUFF_MS, self._tune("kLashDebuffMs")[0])
        self.assertEqual(ukorz.LASH_STAT_PCT, self._tune("kLashStatPct")[0])
        self.assertEqual(ukorz.TRAIL_LIFE_MS, self._tune("kTrailLifeMs")[0])

    # --- the stalkers -------------------------------------------------------------------------------------------------

    def test_the_stalkers_are_helpers(self):
        for entry, script in ((301025, "npc_zf_quicksand"), (301026, "npc_zf_creeping_sands")):
            with self.subTest(entry=entry):
                row = self.rows[entry]
                self.assertEqual(row["ScriptName"], script)
                self.assertEqual(row["unit_flags"] & (0x2 | 0x02000000), 0x2 | 0x02000000)
                self.assertEqual(row["flags_extra"], 0x40)
                self.assertEqual(row["lootid"], 0)
                self.assertRegex(self.script, rf"RegisterDungeonReworkCreatureAI\({script},")
                self.assertRegex(self.header, rf"NPC_ZF_\w+\s*= {entry},")

    # --- the SQL ------------------------------------------------------------------------------------------------------

    def test_the_texts(self):
        ukorz_rows = re.findall(r"\(7267, (\d+), 0, '((?:[^']|\\')*)', (\d+), 0, 100, 0, 0, 0, 0, (\d+),", self.sql)
        self.assertEqual([int(r[0]) for r in ukorz_rows], [4, 5, 6, 7])
        self.assertEqual([int(r[2]) for r in ukorz_rows], [14, 14, 14, 41])
        self.assertIn("$n", ukorz_rows[3][1])
        self.assertIn("BETWEEN 4 AND 7", self.sql)     # 0 to 3 are stock
        ruuzlu_rows = re.findall(r"\(7797, (\d+), 0, '((?:[^']|\\')*)', (\d+), 0, 100,", self.sql)
        self.assertEqual([int(r[0]) for r in ruuzlu_rows], [0, 1, 2])
        self.assertEqual({int(r[2]) for r in ruuzlu_rows}, {14})
        statements = re.sub(r"^--.*$", "", self.sql, flags=re.M)
        for table in ("`creature`", "`gameobject`", "smart_scripts"):
            self.assertNotIn(table, statements)
        # the text groups the C++ says
        for name, group in (("SAY_UKORZ_STORM", 4), ("SAY_UKORZ_HOLD", 5), ("SAY_UKORZ_CALL", 6),
                            ("EMOTE_UKORZ_STAMP", 7), ("SAY_RUUZLU_STORM", 0), ("SAY_RUUZLU_HOLD", 1),
                            ("SAY_RUUZLU_CALL", 2)):
            self.assertRegex(self.logic, rf"\b{name}\s*= {group},", name)

    # --- the C++ ------------------------------------------------------------------------------------------------------

    def test_no_assist_calls(self):
        for struct in ("struct boss_ukorz_rework", "struct boss_ruuzlu_rework"):
            body = self.script[self.script.index(struct):]
            update = body[body.index("void UpdateAI(uint32 diff)"):]
            self.assertLess(update.index("ZulFarrak::NoAssist(me);"), update.index("UpdateVictim()"), struct)

    def test_the_boss_data(self):
        # s7 #10 A: the disfavored boss ignored by DPS bots only; KillTogether 10 both ways; neither AoeOk.
        self.assertIn(".For(Who::Dps)", self.script)
        self.assertIn(".KillTogether(partner, Tune::kKillTogetherPct)", self.script)
        self.assertNotIn(".AoeOk()", self.script)
        self.assertEqual(self._tune("kKillTogetherPct"), [10.0])
        self.assertIn("d.interrupts.emplace_back(NPC_UKORZ, RoarSpell(), Tune::kRoarKickPriority);", self.script)
        self.assertIn("d.interrupts.emplace_back(NPC_RUUZLU, RoarSpell(), Tune::kRoarKickPriority);", self.script)


if __name__ == "__main__":
    unittest.main()
