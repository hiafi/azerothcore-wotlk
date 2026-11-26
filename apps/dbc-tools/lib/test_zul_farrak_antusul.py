"""
Zul'Farrak build WP-D2, Antu'sul: source/npcs/zul_farrak/antusul.py against its C++ (modules/mod-dungeon-bosses
src/ZulFarrak/AntusulLogic.h, boss_antusul_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in his slice (213890-213919) and AntusulLogic.h names the same ids;
  - Antu'sul 8127 is bound (SmartAI off) at 159,947 on the level 46 paladin base; the Servant 8156 is bound to its
    script as a beast (crowd control works on it);
  - Healing Wave is the only kickable cast (Nature); every bar is Physical, not kickable and keeps his swing timer
    (s3.5 kick table, LESSONS L2, L3); the gaze is not interruptible;
  - Calcify: Magic, 6 stacks, 30 s, -5% taken and -7% speed a stack, mechanic none, the dispel script; Stoneflesh: 3
    stacks, -10% taken, not dispellable; Petrified: a 2 s stun no trinket breaks; the header's numbers;
  - every damage spell is a resolve copy (ignores caster modifiers, no redirection or reflection: LESSONS L7);
  - the looks are V's;
  - the C++ keeps the rules: NoAssist first, the wake on SetData(1, 1), the dispel rule, the kill order, the
    interrupt, the tank in every hit, the floor filter, the cleanup;
  - the SQL rev writes the one new emote (group 3, type 41) and touches nothing else.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_zul_farrak_antusul.py
"""

from __future__ import annotations

import math
import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import test_id_blocks as id_blocks  # noqa: E402
from lib.dsl import registry  # noqa: E402

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "ZulFarrak"
HEADER = MODULE_DIR / "AntusulLogic.h"
REWORK = MODULE_DIR / "ZulFarrakRework.h"
SCRIPT = MODULE_DIR / "boss_antusul_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_antusul_zul_farrak.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "zul_farrak"

SLICE = range(213890, 213920)
(CALCIFY, GAZE, PETRIFIED, BOLT_BAR, BOLT_BAR_H, BOLT_HIT, BOLT_LOOK, SHATTER, CRACK, WAVE_BAR, WAVE_HIT, WAVE_LOOK,
 HEAL, HEAL_H, STONEFLESH, RISE) = range(213890, 213906)
ANTUSUL, SERVANT = 8127, 8156
PALADIN_46_BASE = 1535      # creature_classlevelstats level 46 class 2 basehp0

SCHOOL_PHYSICAL, SCHOOL_NATURE = 1, 8
SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT, HEAL_EFFECT = 2, 6, 3, 10
AURA_DUMMY, AURA_MOD_STUN, AURA_MOD_DECREASE_SPEED, AURA_MOD_DAMAGE_PERCENT_TAKEN = 4, 12, 33, 87
PREVENTION_SILENCE = 1
DISPEL_MAGIC = 1
ATTR0_NO_IMMUNITIES = 0x20000000
ATTR1_NO_REDIRECTION, ATTR1_IS_CHANNELED, ATTR1_NO_REFLECTION = 0x8, 0x4, 0x80
ATTR2_DO_NOT_RESET_COMBAT_TIMERS = 0x00020000
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
CHANGE_MAP = 0x00080000
RESOLVE = "spell_boss_mechanics_resolve"
# V's picks (_visuals.py).
SV_CALCIFY, SV_PETRIFIED, SV_GAZE, SV_SHATTER, SV_BOLT, SV_WAVE, SV_STONEFLESH, SV_RISE, SV_HEAL = (
    711, 1845, 90704, 8097, 36, 8083, 7627, 7443, 135)


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


def _tune() -> str:
    text = HEADER.read_text(encoding="utf-8")
    return text[text.index("namespace Tune"):]


def _value(name: str) -> float:
    match = re.search(rf"\b{name} = (-?[\d.]+)f?;", _tune())
    assert match, name
    return float(match.group(1))


def _pair(name: str) -> tuple[float, float]:
    match = re.search(rf"\b{name}\{{ (-?[\d.]+)f?, (-?[\d.]+)f? \}};", _tune())
    assert match, name
    return float(match.group(1)), float(match.group(2))


def _code(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith(("//", "*", "/*")))


class AntusulDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) in (ANTUSUL, SERVANT)}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(CALCIFY, RISE + 1)))
        self.assertEqual(id_blocks.out_of_reservation("zul_farrak", {"spell": mine}), [])
        first = re.search(r"kSpellsAntusul\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_AS_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", HEADER.read_text(encoding="utf-8"))
        self.assertEqual([SLICE.start + int(o) for o in offsets], mine)

    def test_antusul_and_the_servant_are_bound(self):
        boss = self.edits[ANTUSUL]
        self.assertEqual((boss["ScriptName"], boss["AIName"]), ("boss_antusul_rework", ""))
        health = re.search(r"kAntusul\{ (\d+), (\d+) \}", REWORK.read_text(encoding="utf-8"))
        self.assertEqual(math.ceil(PALADIN_46_BASE * boss["HealthModifier"]), int(health.group(1)))
        self.assertEqual((boss["DamageModifier"], boss["CreatureImmunitiesId"]), (4.25, 1972))
        servant = self.edits[SERVANT]
        self.assertEqual((servant["ScriptName"], servant["AIName"], servant["type"]),
                         ("npc_antusul_servant_rework", "", 1))
        self.assertNotIn("HealthModifier", servant)     # stock 5,757
        for script in ("boss_antusul_rework", "npc_antusul_servant_rework"):
            self.assertIn(f"RegisterDungeonReworkCreatureAI({script},", self.cpp)
        self.assertIn('ZfTest::RegisterBoss("antusul"', self.cpp)

    def test_kickable_casts_and_the_bars(self):
        kickable = {i for i, s in self.spells.items() if _raw(s, "PreventionType") == PREVENTION_SILENCE}
        self.assertEqual(kickable, {HEAL, HEAL_H})
        for spell_id in (HEAL, HEAL_H):
            heal = self.spells[spell_id]
            self.assertEqual((heal["school"], _raw(heal, "InterruptFlags")), (SCHOOL_NATURE, 15))
            self.assertEqual(heal["effect1"]["type"], HEAL_EFFECT)
            self.assertEqual((int(heal["effect1"]["base_points"]), int(heal["effect1"]["die_sides"])), (0, 0))
            self.assertTrue(_raw(heal, "AttributesEx2") & ATTR2_DO_NOT_RESET_COMBAT_TIMERS)
            self.assertTrue(_raw(heal, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        # Rule 24: a kick refuses every non-triggered cast of the school it locked: the bars are Physical.
        for spell_id in (BOLT_BAR, BOLT_BAR_H, WAVE_BAR):
            bar = self.spells[spell_id]
            self.assertEqual(bar["school"], SCHOOL_PHYSICAL)
            self.assertEqual((_raw(bar, "InterruptFlags"), _raw(bar, "PreventionType")), (0, 0))
            self.assertEqual(bar["effect1"]["type"], DUMMY_EFFECT)
            self.assertTrue(_raw(bar, "AttributesEx2") & ATTR2_DO_NOT_RESET_COMBAT_TIMERS)
        self.assertEqual((self.spells[BOLT_BAR]["cast_time_ms"], self.spells[BOLT_BAR_H]["cast_time_ms"]),
                         tuple(int(v) for v in _pair("kBoltCastMs")))
        self.assertEqual(self.spells[WAVE_BAR]["cast_time_ms"], int(_value("kShockwaveCastMs")))
        self.assertEqual((self.spells[HEAL]["cast_time_ms"], self.spells[HEAL_H]["cast_time_ms"]),
                         tuple(int(v) for v in _pair("kHealCastMs")))
        gaze = self.spells[GAZE]
        self.assertEqual((_raw(gaze, "InterruptFlags"), _raw(gaze, "ChannelInterruptFlags"),
                          _raw(gaze, "PreventionType")), (0, 0, 0))
        self.assertTrue(_raw(gaze, "AttributesEx") & ATTR1_IS_CHANNELED)
        self.assertEqual(gaze["duration_ms"], int(_value("kGazeMs")))
        # Earth Shock stays stock and is cast triggered (a kicked Nature school never refuses it).
        self.assertIn("me->CastSpell(victim, SPELL_EARTH_SHOCK, true);", self.cpp)

    def test_calcify(self):
        spell = self.spells[CALCIFY]
        taken, slow = spell["effect1"], spell["effect2"]
        self.assertEqual((spell["dispel"], spell["mechanic"]), (DISPEL_MAGIC, 0))
        self.assertEqual(_raw(spell, "CumulativeAura"), int(_value("kCalcifyMaxStacks")))
        self.assertEqual(spell["duration_ms"], int(_value("kCalcifyDurationMs")))
        self.assertEqual((taken["apply_aura"], int(taken["base_points"]), taken["die_sides"], taken["misc_value"]),
                         (AURA_MOD_DAMAGE_PERCENT_TAKEN, -int(_value("kCalcifyTakenPctPerStack")), 0, 127))
        self.assertEqual((slow["apply_aura"], int(slow["base_points"]), slow["die_sides"], slow.get("mechanic", 0)),
                         (AURA_MOD_DECREASE_SPEED, -int(_value("kCalcifySlowPctPerStack")), 0, 0))
        self.assertTrue(_raw(spell, "AuraInterruptFlags") & CHANGE_MAP)
        self.assertIn((CALCIFY, "spell_zf_antusul_calcify"), self.scripts)
        self.assertIn("RegisterSpellScript(spell_zf_antusul_calcify);", self.cpp)

    def test_stoneflesh_and_petrified(self):
        stone = self.spells[STONEFLESH]
        effect = stone["effect1"]
        self.assertEqual((stone["dispel"], stone["mechanic"], stone["duration_ms"]), (0, 0, -1))
        self.assertEqual(_raw(stone, "CumulativeAura"), int(_value("kStonefleshStacks")))
        self.assertEqual((effect["apply_aura"], int(effect["base_points"]), effect["die_sides"], effect["misc_value"]),
                         (AURA_MOD_DAMAGE_PERCENT_TAKEN, -int(_value("kStonefleshTakenPctPerStack")), 0, 127))
        statue = self.spells[PETRIFIED]
        self.assertEqual((statue["effect1"]["apply_aura"], statue["mechanic"], statue["dispel"]),
                         (AURA_MOD_STUN, 0, 0))
        self.assertEqual(statue["duration_ms"], int(_value("kPetrifyMs")))
        self.assertTrue(statue["attributes"] & ATTR0_NO_IMMUNITIES)
        self.assertTrue(_raw(statue, "AuraInterruptFlags") & CHANGE_MAP)

    def test_the_hits_are_resolve_copies(self):
        hits = {BOLT_HIT: SCHOOL_NATURE, SHATTER: SCHOOL_PHYSICAL, CRACK: SCHOOL_PHYSICAL, WAVE_HIT: SCHOOL_NATURE}
        for spell_id, school in hits.items():
            spell = self.spells[spell_id]
            self.assertEqual(spell["school"], school, spell_id)
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE)
            self.assertIn((spell_id, RESOLVE), self.scripts)
            self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
            self.assertTrue(_raw(spell, "AttributesEx") & ATTR1_NO_REDIRECTION)
            self.assertTrue(_raw(spell, "AttributesEx") & ATTR1_NO_REFLECTION)
        damaging = {i for i, s in self.spells.items() if (s.get("effect1") or {}).get("type") == SCHOOL_DAMAGE}
        self.assertEqual(damaging, set(hits))
        self.assertEqual({sid for sid, name in self.scripts if name == RESOLVE}, set(hits))

    def test_the_looks_are_vs(self):
        looks = {CALCIFY: SV_CALCIFY, GAZE: SV_GAZE, PETRIFIED: SV_PETRIFIED, BOLT_LOOK: SV_BOLT, SHATTER: SV_SHATTER,
                 WAVE_LOOK: SV_WAVE, HEAL: SV_HEAL, HEAL_H: SV_HEAL, STONEFLESH: SV_STONEFLESH, RISE: SV_RISE}
        self.assertEqual({i: _raw(s, "SpellVisualID_1") for i, s in self.spells.items() if i in looks}, looks)
        for spell_id in set(self.spells) - set(looks):
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), 0, spell_id)

    def test_the_numbers(self):
        self.assertEqual(_pair("kRiseEveryMs"), (25000, 20000))
        self.assertEqual(_pair("kGazeTickMs"), (2000, 1500))
        self.assertEqual(_pair("kBoltPct"), (15, 25))
        self.assertEqual(_pair("kShatterPctPerStack"), (6, 9))
        self.assertEqual(_pair("kCrackPct"), (25, 35))
        self.assertEqual(_pair("kShockwavePct"), (50, 70))
        self.assertEqual(_pair("kShockwaveEveryMs"), (20000, 18000))
        self.assertEqual(_pair("kHealPct"), (4, 8))
        self.assertEqual(_pair("kStoneDustStacks"), (0, 2))
        self.assertEqual((_value("kServantCap"), _value("kShatterRadius"), _value("kDispelMinStacks")), (3, 6, 4))

    def test_the_cpp_keeps_the_rules(self):
        code = _code(self.cpp)
        # No assist calls, every tick before UpdateVictim (rule 27).
        self.assertRegex(code, r"ZulFarrak::NoAssist\(me\);[^\n]*\n\s+if \(!UpdateVictim\(\)\)")
        # The wake (s7 #25 A): area trigger 1447's and DC's SetData(1, 1) on his AI.
        self.assertIn("if (type == kWakeDataId && data == kWakeDataValue)", code)
        self.assertIn("me->EngageWithTarget(target);", code)
        # Boss data: kick the heal, Calcify under the spacing and stack rule, Servants first.
        self.assertIn("d.interrupts.emplace_back(NPC_ANTUSUL, HealSpell()", code)
        self.assertIn("Condition::Not(Condition::NearPlayer(Tune::kDispelSpacingYd))", code)
        self.assertIn(">= Tune::kDispelMinStacks", code)
        self.assertIn("antusul->GetVictim() != unit", code)
        self.assertIn("TargetEntry(NPC_ANTUSUL_SERVANT, Tune::kServantTargetPriority", code)
        # Mechanics include the tank (rule 17): every damage registration names the tank's share.
        self.assertEqual(code.count(".Damage(pct).TankDamage(pct)"), 2)
        self.assertEqual(code.count("spec.tankPct ="), 3)
        self.assertNotIn("TankExempt", code)
        # Bot shapes inside his floor (rule 14); every pick on his floor (rule 5).
        self.assertGreaterEqual(code.count(".Within(AntusulFloorBounds())"), 4)
        self.assertIn("if (!_arena.Contains(player))", code)
        # Never a registration inside the registry's resolve: stone dust is applied on the next tick.
        self.assertIn("ai->_dust.push_back(player->GetGUID());", code)
        # RB-1: everything goes on reset, evade and death.
        cleanup = code[code.index("void Cleanup()"):]
        for piece in ("summons.DespawnAll()", "StopStonefleshStack()", "SPELL_AS_CALCIFY", "SPELL_AS_PETRIFIED",
                      "SPELL_AS_GAZE", "RemoveAurasDueToSpell(SPELL_AS_STONEFLESH)", "_statues.clear()",
                      "_timeline = Timeline{}"):
            self.assertIn(piece, cleanup)
        for hook in ("void Reset() override", "void EnterEvadeMode(EvadeReason why) override",
                     "void JustDied(Unit* killer) override"):
            body = code[code.index(hook):]
            self.assertIn("Cleanup();", body[:body.index("\n    }")])
        self.assertNotIn("\t", self.cpp)


class AntusulSqlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8")

    def test_the_emote(self):
        self.assertIn("(8127, 3, 0, '%s draws the stone beneath his feet!', 41, 0, 100, ", self.sql)
        groups = re.findall(r"(?:YELL|EMOTE)_\w+\s*=\s*(\d+),", HEADER.read_text(encoding="utf-8"))
        self.assertEqual(sorted(int(g) for g in groups), [0, 1, 2, 3])

    def test_the_rev_touches_only_the_new_text(self):
        code = "\n".join(line for line in self.sql.splitlines() if not line.startswith("--"))
        self.assertEqual(re.findall(r"(?:DELETE FROM|INSERT INTO|UPDATE) `(\w+)`", code),
                         ["creature_text", "creature_text"])
        self.assertIn("WHERE `CreatureID` = 8127 AND `GroupID` = 3;", code)
        self.assertNotIn("6066", code)      # the Earthgrab totem keeps its SmartAI (seven other casters)


if __name__ == "__main__":
    unittest.main()
