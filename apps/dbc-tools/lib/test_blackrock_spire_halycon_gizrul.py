"""
Blackrock Spire build WP-B7, Halycon and Gizrul: source/npcs/blackrock_spire/halycon_gizrul.py against its C++
(modules/mod-dungeon-bosses src/BlackrockSpire/HalyconGizrulLogic.h, boss_halycon_gizrul_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in the pair's slice (210210-210249) and HalyconGizrulLogic.h names the same ids;
  - both wolves are bound to the one script (SmartAI off, immunity 1972, INSTANCE_BIND), 120k each at 5 players;
  - the five hits are resolve copies (Physical, the froth and trail Nature);
  - Rabies is a Disease DoT on the kit's percent script plus its own tick skipper, the header's numbers;
  - Call of the Pack is a 3 s Nature kick; the cast bars are not kicks and not Nature;
  - Pack Fury, Bloodied Pack and Grief are damage auras with the header's numbers; Torn Hide's duration keeps the
    user's taunt rule against the bite rates;
  - the trail puddle is the shipped goo area aura; the run-in sprint is +100% for 10 s;
  - the SQL rev writes Halycon 0-4 and Gizrul 0-3 as boss emotes.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_spire_halycon_gizrul.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockSpire"
HEADER = MODULE_DIR / "HalyconGizrulLogic.h"
REWORK = MODULE_DIR / "BlackrockSpireRework.h"
SCRIPT = MODULE_DIR / "boss_halycon_gizrul_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_halycon_gizrul_blackrock_spire.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_spire"

SLICE = range(210210, 210250)
(CHARGE_HIT, POUNCE_HIT, THRASH_HIT, FROTH_HIT, TRAIL_HIT, RABIES, CALL, PACK_FURY, BLOODIED, GRIEF, TORN_HIDE,
 CHARGE_BAR, THRASH_BAR, FROTH_BAR, CHARGE_LOOK, LEAP_LOOK, MAUL_LOOK, WHIRL_LOOK, FROTH_LOOK, SPRINT,
 PUDDLE) = range(210210, 210231)
HALYCON, GIZRUL = 10220, 10268
HEALTH_AT_5 = 120_000
WARRIOR_59_BASE, WARRIOR_60_BASE = 2961, 3052

SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT, PERSISTENT_AREA_AURA = 2, 6, 3, 27
AURA_DUMMY, AURA_PERIODIC_DAMAGE, AURA_MOD_INCREASE_SPEED, AURA_MOD_DAMAGE_PERCENT_DONE = 4, 3, 31, 79
SCHOOL_PHYSICAL, SCHOOL_NATURE = 1, 8
DISPEL_DISEASE = 3
RESOLVE = "spell_boss_mechanics_resolve"
IMMUNITY_BOSS_STUN = 1972
INSTANCE_BIND = 0x1
SV_GOO_PUDDLE = 90342


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


def _header_value(name: str) -> float:
    match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f?;", _header())
    assert match, name
    return float(match.group(1))


def _header_nh(name: str) -> tuple[float, float]:
    match = re.search(rf"\b{name}\{{\s*(-?[\d.]+)f?,\s*(-?[\d.]+)f?\s*\}};", _header())
    assert match, name
    return float(match.group(1)), float(match.group(2))


class HalyconGizrulDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) in (HALYCON, GIZRUL)}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(CHARGE_HIT, PUDDLE + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_spire", {"spell": mine}), [])
        first = re.search(r"kSpellsHalyconGizrul\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(first)
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_HG_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))

    def test_both_wolves_are_bound(self):
        for entry, base in ((HALYCON, WARRIOR_59_BASE), (GIZRUL, WARRIOR_60_BASE)):
            wolf = self.edits[entry]
            self.assertEqual(wolf["ScriptName"], "boss_halycon_gizrul_rework")
            self.assertEqual(wolf["AIName"], "")
            self.assertEqual(wolf["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
            self.assertEqual(wolf["flags_extra"] & INSTANCE_BIND, INSTANCE_BIND)
            # 120k each at 5 players (within 2 HP: the modifier is rounded to three decimals)
            self.assertLessEqual(abs(math.ceil(base * wolf["HealthModifier"]) - HEALTH_AT_5), 2)
        self.assertAlmostEqual(float(self.edits[HALYCON]["DamageModifier"]), 6.5)
        self.assertAlmostEqual(float(self.edits[GIZRUL]["DamageModifier"]), 3.5)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_halycon_gizrul_rework,", self.cpp)
        self.assertIn("RegisterSpellScript(spell_brs_hg_rabies);", self.cpp)

    def test_the_hits_are_resolve_copies(self):
        schools = {CHARGE_HIT: SCHOOL_PHYSICAL, POUNCE_HIT: SCHOOL_PHYSICAL, THRASH_HIT: SCHOOL_PHYSICAL,
                   FROTH_HIT: SCHOOL_NATURE, TRAIL_HIT: SCHOOL_NATURE}
        for spell_id, school in schools.items():
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
            self.assertEqual(spell["school"], school, spell_id)
        # the registry calls name them
        for name in ("SPELL_HG_SAVAGE_CHARGE", "SPELL_HG_PACK_POUNCE", "SPELL_HG_THRASH", "SPELL_HG_RABID_FROTH",
                     "SPELL_HG_RABID_TRAIL"):
            self.assertIn(f".Spell({name})", self.cpp)

    def test_rabies(self):
        rabies = self.spells[RABIES]
        effect = rabies["effect1"]
        self.assertEqual(effect["apply_aura"], AURA_PERIODIC_DAMAGE)
        self.assertEqual(effect["amplitude"], int(_header_value("kRabiesAmplitudeMs")))
        self.assertEqual(effect["amplitude"] * 2, int(_header_value("kRabiesTickMs")))
        self.assertEqual(rabies["dispel"], DISPEL_DISEASE)
        self.assertEqual(rabies["school"], SCHOOL_NATURE)
        self.assertEqual(rabies["duration_ms"], int(_header_value("kRabiesMs")))
        self.assertEqual(_raw(rabies, "CumulativeAura"), int(_header_value("kRabiesMaxStacks")))
        normal, heroic = _header_nh("kRabiesPctPerStack")
        self.assertEqual(effect["base_points"], round(normal * 100))
        self.assertEqual(_raw(rabies, "EffectMiscValueB_1"), round(heroic * 100))
        self.assertTrue(_raw(rabies, "AttributesEx3") & 0x20000000)     # IGNORE_CASTER_MODIFIERS
        self.assertIn((RABIES, "spell_dungeon_refflat_periodic"), self.scripts)
        self.assertIn((RABIES, "spell_brs_hg_rabies"), self.scripts)
        # the dispel list names it
        self.assertIn("d.dispels.emplace_back(SPELL_HG_RABIES", self.cpp)

    def test_call_of_the_pack_is_a_kick_and_the_bars_are_not(self):
        call = self.spells[CALL]
        self.assertEqual(call["cast_time_ms"], int(_header_value("kCallCastMs")))
        self.assertEqual(_raw(call, "InterruptFlags"), 15)
        self.assertEqual(_raw(call, "PreventionType"), 1)
        self.assertEqual(call["school"], SCHOOL_NATURE)
        for bar, warn in ((CHARGE_BAR, "kPawMs"), (THRASH_BAR, "kThrashWarnMs"), (FROTH_BAR, "kFrothWarnMs")):
            spell = self.spells[bar]
            self.assertEqual(spell["cast_time_ms"], int(_header_value(warn)), bar)
            self.assertEqual(_raw(spell, "InterruptFlags"), 0, bar)
            self.assertNotEqual(spell["school"], call["school"], bar)
        self.assertIn("d.interrupts.emplace_back(me->GetEntry(), SPELL_HG_CALL_OF_THE_PACK, priority", self.cpp)

    def test_the_damage_auras(self):
        for spell_id, pct_name in ((PACK_FURY, "kPackFuryDamagePct"), (BLOODIED, "kBloodiedPackDamagePct")):
            effect = self.spells[spell_id]["effect1"]
            self.assertEqual(effect["apply_aura"], AURA_MOD_DAMAGE_PERCENT_DONE, spell_id)
            self.assertEqual(effect["base_points"], int(_header_value(pct_name)), spell_id)
        self.assertEqual(self.spells[PACK_FURY]["duration_ms"], int(_header_value("kPackFuryMs")))
        self.assertEqual(_raw(self.spells[BLOODIED], "CumulativeAura"), int(_header_value("kBloodiedPackMax")))
        grief = self.spells[GRIEF]["effect1"]
        self.assertEqual(grief["apply_aura"], AURA_MOD_DAMAGE_PERCENT_DONE)
        self.assertEqual(grief["base_points"], int(_header_nh("kGriefDamagePct")[0]))

    def test_torn_hide_keeps_the_taunt_rule(self):
        hide = self.spells[TORN_HIDE]
        self.assertEqual(hide["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(hide["dispel"], 0)
        self.assertEqual(hide["duration_ms"], int(_header_value("kTornHideMs")))
        self.assertEqual(_raw(hide, "CumulativeAura"), 255)
        bite = int(_header_value("kTornHideBiteEveryMs"))
        swap_at = int(_header_value("kTornHideSwapAt"))
        for every, lasts in ((bite, int(_header_value("kTornHideMs"))),
                             (bite * 2 // 3, int(_header_value("kTornHideFuryMs")))):
            self.assertGreater(lasts, every)                        # stacks build
            self.assertLess(lasts, swap_at * every)                 # falls off before the other tank's count (D < 3I)
        # R-1 ruling 2: SP's 15 s at the normal bite, about 10-11 s under Pack Fury
        self.assertEqual(int(_header_value("kTornHideMs")), 15000)
        self.assertIn(int(_header_value("kTornHideFuryMs")), range(10000, 11001))
        # the hold while the wolf cannot bite (R-1-B M1)
        self.assertIn("HoldTornHide(diff)", self.cpp)
        # only at 10 players
        self.assertIn("DungeonKit::Flex::TankSwapOn(_players)", self.cpp)
        self.assertIn("d.tauntSwaps.emplace_back(me->GetEntry(), SPELL_HG_TORN_HIDE, kTornHideSwapAt)", self.cpp)
        self.assertIn("BossMechanics::Who::AssistTank", self.cpp)

    def test_the_trail_and_the_sprint(self):
        puddle = self.spells[PUDDLE]
        self.assertEqual(puddle["effect1"]["type"], PERSISTENT_AREA_AURA)
        self.assertAlmostEqual(float(puddle["effect1"]["radius_yards"]), _header_value("kPuddleRadius"))
        self.assertEqual(puddle["duration_ms"], int(_header_value("kTrailMs")))
        self.assertEqual(_raw(puddle, "SpellVisualID_1"), SV_GOO_PUDDLE)
        sprint = self.spells[SPRINT]
        self.assertEqual(sprint["effect1"]["apply_aura"], AURA_MOD_INCREASE_SPEED)
        self.assertEqual(sprint["effect1"]["base_points"], int(_header_value("kSprintSpeedPct")))
        self.assertEqual(sprint["duration_ms"], int(_header_value("kSprintMs")))

    def test_the_looks_are_self_visuals(self):
        for spell_id in (CHARGE_LOOK, LEAP_LOOK, MAUL_LOOK, WHIRL_LOOK, FROTH_LOOK):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], DUMMY_EFFECT, spell_id)
            self.assertNotEqual(_raw(spell, "SpellVisualID_1"), 0, spell_id)

    def test_the_sql_rev(self):
        sql = SQL.read_text(encoding="utf-8")
        for group in range(5):
            self.assertRegex(sql, rf"\({HALYCON}, {group}, 0, '[^\n]*', 41,")
        for group in range(4):
            self.assertRegex(sql, rf"\({GIZRUL}, {group}, 0, '[^\n]*', 41,")
        self.assertIn("'%s collapses. Gizrul howls in grief!'", sql)
        self.assertIn("'%s fixes his eyes on $n!'", sql)
        # S0's rev owns the SmartAI delete of 10268
        self.assertNotIn("DELETE FROM `smart_scripts`", sql)


if __name__ == "__main__":
    unittest.main()
