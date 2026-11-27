"""
Gnomeregan build WP-D6Ha, the Whole Workshop part a: source/npcs/gnomeregan/thermaplugg_hard_mode.py against its C++
(modules/mod-dungeon-bosses src/Gnomeregan/ThermapluggHardModeLogic.h, thermaplugg_hard_mode.cpp), WP-V's _visuals.py,
WP-H's heroic id table, BM's gnomeregan-shapes drill table (when the BM worktree is on hand) and its SQL rev.

Checks:
  - the spells sit in part a's slice (214540-214579) and ThermapluggHardModeLogic.h names the same ids;
  - the hard mode dose: +3% damage and healing done and +3% damage taken a stack (ruling 49), 255 shown, no dispel,
    NO_IMMUNITIES, CHANGE_MAP;
  - the only cast is the bombs' Duplication: 2 s, Nature, kickable (the kick and dispel table), a 1 s aura of itself;
  - every hit is a Nature resolve copy; nothing is dispellable; the Leak's screen effect is V's;
  - the looks and sounds are V's; the three units are inert helpers bound to their scripts, none with a heroic
    template (INT reconcile);
  - the C++ keeps the contract: D1's Duplicator and D2's DoseField from GnomereganMachines.h, D2's Halve on a plate
    touch (never a halving of its own), D6's AdoptBomb, BM-G's minStacks claim on its own Soak, every shape within
    the room, the tank row on every hit, bots refused at the console, the package registered;
  - the drill tag of the puddles equals BM's MechanicDrill.h kGnTagHmPuddles, and part b's tags are left alone;
  - the SQL rev: the console's template, gossip and npc_text, his line 9 and the alarm's lines 0-4 (type 41).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_gnomeregan_hard_mode.py
"""

from __future__ import annotations

import os
import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import test_id_blocks as id_blocks  # noqa: E402
from lib.dsl import registry  # noqa: E402
from source.npcs.gnomeregan import _visuals as visuals  # noqa: E402

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Gnomeregan"
HEADER = MODULE_DIR / "ThermapluggHardModeLogic.h"
REWORK = MODULE_DIR / "GnomereganRework.h"
SCRIPT = MODULE_DIR / "thermaplugg_hard_mode.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_thermaplugg_hard_mode_gnomeregan.sql"
S0_SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_skeleton_gnomeregan.sql"
HEROIC = TOOL_ROOT / "source" / "world" / "dungeons" / "gnomeregan.py"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "gnomeregan"
BM_DRILL = Path(os.environ.get("BM_SRC", str(REPO_ROOT.parent / "boss-mechanics-gnomer" / "src"))) / "MechanicDrill.h"

SLICE = range(214540, 214580)
(DOSE, GLOW, DUPLICATION, VENT, PUDDLE, MELTDOWN, MELTDOWN_AURA, LEAK, LEAK_AURA) = range(214540, 214549)
PUDDLE_NPC, ALARM, VENT_NPC = 301135, 301137, 301138
CONSOLE, CONSOLE_GUID, GOSSIP, NPC_TEXT = 301382, 3013820, 5300022, 900029

SCHOOL_NATURE = 8
SCHOOL_DAMAGE, APPLY_AURA = 2, 6
AURA_DUMMY, AURA_MOD_DAMAGE_PERCENT_TAKEN, AURA_MOD_DAMAGE_PERCENT_DONE = 4, 87, 79
AURA_MOD_HEALING_DONE_PERCENT, AURA_SCREEN_EFFECT = 136, 260
PREVENTION_SILENCE = 1
ATTR0_AURA_IS_DEBUFF, ATTR0_NO_IMMUNITIES = 0x04000000, 0x20000000
ATTR1_NO_REDIRECTION, ATTR1_NO_REFLECTION = 0x8, 0x80
ATTR2_DO_NOT_RESET_COMBAT_TIMERS = 0x00020000
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
CHANGE_MAP = 0x00080000
RESOLVE = "spell_boss_mechanics_resolve"
UNIT_FLAG_NON_ATTACKABLE, UNIT_FLAG_NOT_SELECTABLE = 0x2, 0x02000000
PART_B_TAGS = {80, 82, 83, 84, 85}


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


def _raw(spell: dict, column: str) -> int | float:
    return (spell.get("raw_overrides") or {}).get(column, 0) or 0


def _value(name: str) -> float:
    match = re.search(rf"\b{name} = (-?[\d.]+)f?;", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return float(match.group(1))


def _code(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith(("//", "*", "/*")))


class HardModeDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates
                         if int(e["entry"]) in (PUDDLE_NPC, ALARM, VENT_NPC)}
        cls.models = {int(m["CreatureID"]): m for m in reg.creature_template_models
                      if int(m["CreatureID"]) in (PUDDLE_NPC, ALARM, VENT_NPC)}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(DOSE, LEAK_AURA + 1)))
        self.assertEqual(id_blocks.out_of_reservation("gnomeregan", {"spell": mine}), [])
        first = re.search(r"kSpellsHardModeA\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_HM_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", self.header)
        self.assertEqual([SLICE.start + int(o) for o in offsets], mine)

    def test_the_dose(self):
        dose = self.spells[DOSE]
        self.assertEqual((dose["dispel"], dose["mechanic"], dose["duration_ms"], dose["school"]),
                         (0, 0, -1, SCHOOL_NATURE))
        self.assertTrue(dose["attributes"] & ATTR0_AURA_IS_DEBUFF and dose["attributes"] & ATTR0_NO_IMMUNITIES)
        pct = int(_value("kDosePctPerStack"))
        auras = [(dose[f"effect{i}"]["apply_aura"], int(dose[f"effect{i}"]["base_points"]),
                  dose[f"effect{i}"]["die_sides"]) for i in (1, 2, 3)]
        self.assertEqual(auras, [(AURA_MOD_DAMAGE_PERCENT_DONE, pct, 0), (AURA_MOD_HEALING_DONE_PERCENT, pct, 0),
                                 (AURA_MOD_DAMAGE_PERCENT_TAKEN, pct, 0)])
        self.assertEqual((dose["effect1"]["misc_value"], dose["effect3"]["misc_value"]), (127, 127))
        self.assertEqual(_raw(dose, "CumulativeAura"), 255)     # D2's kAuraStackLimit, the header's static_assert
        self.assertTrue(_raw(dose, "AuraInterruptFlags") & CHANGE_MAP)
        for spell_id in (GLOW, VENT, MELTDOWN_AURA, LEAK_AURA):
            self.assertEqual(self.spells[spell_id]["dispel"], 0)
            self.assertTrue(self.spells[spell_id]["attributes"] & ATTR0_NO_IMMUNITIES)
            self.assertTrue(_raw(self.spells[spell_id], "AuraInterruptFlags") & CHANGE_MAP)
        # Nothing of the package is dispellable (rule 27: the dose, Meltdown, the Leak).
        self.assertEqual({i for i, s in self.spells.items() if s.get("dispel")}, set())

    def test_the_only_cast_is_the_duplication(self):
        kickable = {i for i, s in self.spells.items() if _raw(s, "PreventionType") == PREVENTION_SILENCE
                    or _raw(s, "InterruptFlags")}
        self.assertEqual(kickable, {DUPLICATION})
        self.assertEqual({i for i, s in self.spells.items() if s.get("cast_time_ms")}, {DUPLICATION})
        bar = self.spells[DUPLICATION]
        self.assertEqual((bar["school"], bar["cast_time_ms"], bar["duration_ms"]),
                         (SCHOOL_NATURE, int(_value("kDupCastMs")), 1000))
        self.assertEqual((bar["effect1"]["type"], bar["effect1"]["apply_aura"], bar["effect1"]["implicit_target_a"]),
                         (APPLY_AURA, AURA_DUMMY, 1))
        self.assertTrue(_raw(bar, "AttributesEx2") & ATTR2_DO_NOT_RESET_COMBAT_TIMERS)

    def test_every_hit_is_a_nature_resolve_copy(self):
        damaging = {i for i, s in self.spells.items() if (s.get("effect1") or {}).get("type") == SCHOOL_DAMAGE}
        self.assertEqual(damaging, {PUDDLE, MELTDOWN, LEAK})
        for spell_id in damaging:
            spell = self.spells[spell_id]
            self.assertEqual(spell["school"], SCHOOL_NATURE, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
            self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS, spell_id)
            self.assertTrue(_raw(spell, "AttributesEx") & ATTR1_NO_REDIRECTION, spell_id)
            self.assertTrue(_raw(spell, "AttributesEx") & ATTR1_NO_REFLECTION, spell_id)
        leak = self.spells[LEAK_AURA]["effect1"]
        self.assertEqual((leak["apply_aura"], leak["misc_value"]), (AURA_SCREEN_EFFECT, visuals.MT_LEAK_SCREEN_EFFECT))

    def test_the_looks_are_vs(self):
        looks = {DOSE: visuals.MT_DOSE, GLOW: visuals.MT_DOSE_BRIGHT, DUPLICATION: visuals.MT_DUPLICATE,
                 VENT: visuals.MT_VENT}
        self.assertEqual({i: _raw(s, "SpellVisualID_1") for i, s in self.spells.items() if i in looks}, looks)
        for spell_id in set(self.spells) - set(looks):
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), 0, spell_id)
        self.assertEqual(int(_value("kDisplayNatureDisc")), visuals.MT_PUDDLE)
        self.assertEqual(int(_value("kDisplayNatureDisc")), visuals.MT_LEAK)
        self.assertEqual(int(_value("kSoundGeiger")), visuals.MT_GEIGER)
        self.assertEqual(int(_value("kSoundAlarm")), visuals.MT_LEAK_ALARM_SOUND)
        self.assertEqual(_value("kLeakDiscScale"), visuals.LEAK_DISC_SCALE)
        self.assertAlmostEqual(visuals.disc_scale(_value("kPuddleYd")), visuals.PUDDLE_DISC_SCALE, places=2)

    def test_the_units(self):
        scripts = {PUDDLE_NPC: "npc_gnomer_wandering_puddle", ALARM: "npc_gnomer_workshop_stalker",
                   VENT_NPC: "npc_gnomer_workshop_stalker"}
        for entry, script in scripts.items():
            row = self.creatures[entry]
            self.assertEqual(row["ScriptName"], script)
            self.assertEqual(row["unit_flags"] & (UNIT_FLAG_NON_ATTACKABLE | UNIT_FLAG_NOT_SELECTABLE),
                             UNIT_FLAG_NON_ATTACKABLE | UNIT_FLAG_NOT_SELECTABLE)
            self.assertEqual(row.get("lootid", 0), 0)
            self.assertIn(f"RegisterDungeonReworkCreatureAI({script},", self.cpp)
        self.assertEqual(int(self.models[PUDDLE_NPC]["CreatureDisplayID"]), visuals.MT_PUDDLE)
        # The puddle is a visible disc: not a trigger (flags_extra 0x80).
        self.assertEqual(int(self.creatures[PUDDLE_NPC]["flags_extra"]) & 0x80, 0)
        for entry in (ALARM, VENT_NPC):
            self.assertEqual(int(self.models[entry]["CreatureDisplayID"]), visuals.DISPLAY_INVISIBLE_STALKER)
        # INT reconcile: all three run on their normal entry on heroic (helpers; Thermaplugg deals every hit), so none
        # names a heroic entry or sits in WP-H's `extra=` / `_HEROIC_ID`.
        heroic = HEROIC.read_text(encoding="utf-8")
        for entry in (PUDDLE_NPC, ALARM, VENT_NPC):
            self.assertEqual(self.creatures[entry].get("difficulty_entry_1", 0), 0)
            self.assertNotIn(f"creature({entry},", heroic)
            self.assertIsNone(re.search(rf"\b{entry}: \d+", heroic))
        # The header's enum (S0's) names the same units.
        rework = REWORK.read_text(encoding="utf-8")
        for name, entry in (("NPC_WANDERING_PUDDLE", PUDDLE_NPC), ("NPC_ROOM_ALARM", ALARM),
                            ("NPC_VENT_STALKER", VENT_NPC), ("GO_CLEARANCE_CONSOLE", CONSOLE)):
            self.assertRegex(rework, rf"\b{name}\s*= {entry},")

    def test_the_cpp_keeps_the_contract(self):
        code = _code(self.cpp)
        # D1's and D2's machines through the contract, D6's hooks.
        self.assertIn("GnomereganMachines::MakeDuplicator(owner,", code)
        self.assertIn("GnomereganMachines::MakeDoseField(owner,", code)
        self.assertIn("spec.auraSpellId = SPELL_HM_IRRADIATED;", code)
        self.assertIn("spec.barSpellId = SPELL_HM_DUPLICATION;", code)
        self.assertIn("_fight.AdoptBomb(source, copy)", code)
        self.assertIn("RegisterThermapluggHardMode(GnomerThermaplugg::HardModePackage::SchematicsA,", code)
        # The plate halves with D2's rule, never one of its own.
        touched = code[code.index("void OnPlateTouched("):]
        self.assertIn("_dose->Halve(player,", touched[:touched.index("\n        }")])
        self.assertNotRegex(code, r"/\s*2\b")
        # F-1d (STAGE-R-1-C Minor-1, DQ1): no Soak group of its own on the plates; D6's plate Soak takes the dose
        # ordering (no floor: bots under 8 keep pressing plates) and PlatePlan's serve order through SetPlatePlan.
        plan = code[code.index("void PlanPlates("):]
        plan = plan[:plan.index("\n        }\n")]
        for piece in ("order.auraSpell = SPELL_HM_IRRADIATED;", "order.ascending = false;",
                      "TankPlatesLast(players)", "PlatePlan(std::move(plates), players, tankLast)",
                      "_fight.SetPlatePlan(order, _plan, PlatePlanBots(players, tankLast));",
                      "player->GetAuraCount(SPELL_HM_IRRADIATED)",
                      "_fight.LockedOut(player)"):
            self.assertIn(piece, plan)
        self.assertNotIn("minStacks", code)
        self.assertNotIn("DwellSoaks", code)
        self.assertNotIn("TAG_HM_DOSE_CLAIM", code)
        self.assertNotIn("TAG_MT_PLATE", code)
        self.assertIn("PlanPlates(diff, false);", code)
        self.assertIn("PlanPlates(0, true);", code)
        # RB-16 (STAGE-R-1-C Nit-1): one NextDue, D6's (due, period, now); the header keeps no copy.
        self.assertNotRegex(HEADER.read_text(encoding="utf-8"), r"(?:constexpr|inline)[^;{]*\bNextDue\s*\(")
        self.assertEqual(len(re.findall(r"\bNextDue\(", code)), len(re.findall(r"GnomerThermaplugg::NextDue\(", code)))
        # Every bot shape keeps to the room (rule 14), the tank row on every hit (rule 17), no Weakened (Penalty none).
        shapes = len(re.findall(r"Mechanic::(?:Zone|Circle|Spread|Stack|Soak)\(", code))
        self.assertGreaterEqual(shapes, 2)
        self.assertEqual(code.count(".Within(_bounds)"), shapes)
        self.assertEqual(code.count("spec.pct = "), code.count("spec.tankPct = "))
        self.assertIn(".TankDamage(Tune::kMeltdownPct)", code)
        self.assertNotIn("weakened = true", code)
        self.assertNotIn(".Weakened()", code)
        # Bots never use the console (rule 34).
        self.assertIn("session->IsSocketClosed()", code)
        self.assertIn("if (verdict == CONSOLE_BOT)", code)
        self.assertIn("RegisterDungeonReworkGameObjectAI(go_gnomer_clearance_console, kInstanceScriptName);", code)
        self.assertIn('GnomerTest::RegisterBoss("workshop"', code)
        # MT15: part a's two lines in D6Hb's form (no 7800 group 10 or 11 of part a's)
        self.assertIn("boss->Talk(LoadLine(s), CHAT_MSG_RAID_BOSS_EMOTE, LANG_UNIVERSAL, Tune::kConsoleLineYd, "
                      "nullptr);", code)
        # RB-1: OnEnd undoes everything the package made.
        end = code[code.index("void OnEnd(ThermapluggFight& fight, bool won) override"):]
        end = end[:end.index("\n        }\n")]
        for piece in ("_dup->Clear()", "_dose->Clear()", "_plan.clear()", "Cancel(boss, p.ring)",
                      "Cancel(boss, handle)", "Despawn(boss, _alarm)", "Despawn(boss, _leakDisc)",
                      "DoRemoveAurasDueToSpellOnPlayers(spell)", "Unregister()"):
            self.assertIn(piece, end)
        for text in (self.cpp, self.header):
            self.assertNotIn("\t", text)

    @unittest.skipUnless(BM_DRILL.exists(), "BM worktree not on hand (set BM_SRC)")
    def test_drill_tags_match_bm(self):
        drill = BM_DRILL.read_text(encoding="utf-8")
        theirs = re.search(r"\bkGnTagHmPuddles = (\d+);", drill)
        ours = re.search(r"\bTAG_HM_PUDDLE\s*= (\d+),", self.header)
        self.assertTrue(theirs and ours)
        self.assertEqual(int(theirs.group(1)), int(ours.group(1)))
        part_b = {int(v) for name, v in re.findall(r"\b(kGnTagHm\w+) = (\d+);", drill) if name != "kGnTagHmPuddles"}
        self.assertTrue(part_b <= PART_B_TAGS, part_b)
        mine = {int(v) for v in re.findall(r"\bTAG_HM_\w+\s*= (\d+),", self.header)}
        self.assertEqual(mine & part_b, set())
        self.assertTrue(all(80 <= tag <= 89 for tag in mine))


class HardModeSqlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8")

    def test_the_console(self):
        template = f"({CONSOLE}, 2, {visuals.GODI_CONSOLE}, 'Clearance Console', '', '', '', 1.5, 0, 0, 0, {GOSSIP},"
        self.assertIn(template, self.sql)
        self.assertIn("'go_gnomer_clearance_console', 0) ON DUPLICATE KEY UPDATE", self.sql)
        self.assertIn(f"({GOSSIP}, {NPC_TEXT});", self.sql)
        self.assertIn(f"({GOSSIP}, 0, 0, 'Insert the Prismatic Punch Card.', 0, 1, 1, 0, 0, 0, 0,", self.sql)
        self.assertIn(f"DELETE FROM `npc_text` WHERE `ID` = {NPC_TEXT};", self.sql)
        header = HEADER.read_text(encoding="utf-8")
        for name, value in (("kConsoleGossipMenu", GOSSIP), ("kConsoleNpcText", NPC_TEXT)):
            self.assertEqual(int(_value(name)), value)
        self.assertIn("kConsoleGossipOption = 0;", header)
        # S0's spawn: heroic only (spawnMask 2) at the console spot.
        self.assertIn(f"({CONSOLE_GUID}, {CONSOLE}, 90, 0, 0, 2, 1,", S0_SQL.read_text(encoding="utf-8"))
        # No spawn, no SmartAI of this rev's own.
        self.assertNotIn("INSERT INTO `gameobject` ", self.sql)
        self.assertNotIn("INSERT INTO `creature` ", self.sql)
        self.assertNotIn("smart_scripts", self.sql)

    def test_the_texts(self):
        # SP's text and no voice: 5808 says the whole stock line (the Override's yell; STAGE-R-1-C Nit-2).
        self.assertIn("(7800, 9, 0, 'My machines are the future!', 14, 0, 100, 0, 0, 0, 0, 0,", self.sql)
        self.assertNotRegex(self.sql, r"\(7800, 9, 0, '[^']*', 14, 0, 100, 0, 0, [1-9]")
        alarm = r"\(301137, (\d+), 0, '[^']+', 41, 0, 100, 0, 0, 0, 0, 3,"
        groups = sorted(int(g) for g in re.findall(alarm, self.sql))
        self.assertEqual(groups, list(range(5)))
        self.assertNotRegex(self.sql, r"\(\d+, \d+, 0, 'Loading schematic")   # raid boss emotes from him (D6Hb's form)
        self.assertIn("'Warning! Reactor containment failure!'", self.sql)
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 7800 AND `GroupID` = 9;", self.sql)
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 301137;", self.sql)


if __name__ == "__main__":
    unittest.main()
