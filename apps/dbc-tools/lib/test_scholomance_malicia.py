"""
Scholomance build WP-S5, Instructor Malicia: source/npcs/scholomance/instructor_malicia.py against its C++
(modules/mod-dungeon-bosses src/Scholomance/MaliciaLogic.h, boss_instructor_malicia_rework.cpp).

Checks:
  - the spells sit in her slice (206205-206224) and MaliciaLogic.h names the same ids;
  - the shade 300536 is a 12k elite on the stock Dark Shade look with its heroic entry, bound to npc_sc_malicias_shade;
    the Loose Soul 300537 is an unselectable wisp (not the invisible 30233) with no heroic template;
  - Soul: a 40-stack meter nobody cancels or dispels, and its hidden weight (damage, healing, max health) set by its
    AuraScript; Bound Soul: +2% a stack, 20 stacks;
  - the casts: Soul Drain and Soulstorm bars are not interruptible; Shadow Heal and the shades' Volley are kickable
    (and the Volley triggers the stock 17228); the nova and Soul Lost set their damage by script (ignores caster
    modifiers, no crit); the blast is a resolve copy; cast times match the header;
  - every SpellScript / AuraScript named here is registered in the C++, and the examiner script name matches
    MaliciaFight.h;
  - the looks are WP-V's picks;
  - 10505 is bound to boss_instructor_malicia_rework with SmartAI off, HealthModifier 65.52, DamageModifier 3.5 and
    immunity set 1972.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scholomance_malicia.py
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
from lib.dsl import registry  # noqa: E402

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Scholomance"
HEADER = MODULE_DIR / "MaliciaLogic.h"
FIGHT_HEADER = MODULE_DIR / "MaliciaFight.h"
SCRIPT = MODULE_DIR / "boss_instructor_malicia_rework.cpp"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "scholomance"

SLICE = range(206205, 206225)
(SOUL, SOUL_WEIGHT, DRAIN_CAST, DRAIN, BOUND, SHADE_VOLLEY, STORM_CAST, STORM_FALL, STORM_BLAST, STORM_BURST,
 SHADOW_HEAL, SHADOW_NOVA, SOUL_LOST) = range(206205, 206218)
SHADE = 300536
SOUL_UNIT = 300537
MALICIA = 10505

SCHOOL_DAMAGE, DUMMY, APPLY_AURA, HEAL, TRIGGER_SPELL = 2, 3, 6, 10, 64
AURA_DUMMY, AURA_MOD_DAMAGE_PERCENT_DONE, AURA_MOD_INCREASE_HEALTH_PERCENT, AURA_MOD_HEALING_DONE_PERCENT = (
    4, 79, 133, 136)
ATTR0_DO_NOT_DISPLAY = 0x00000080
ATTR0_NO_IMMUNITIES = 0x20000000
ATTR0_NO_AURA_CANCEL = 0x80000000
ATTR2_CANT_CRIT = 0x20000000
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
AURA_INTERRUPT_FLAG_CHANGE_MAP = 0x00080000
UNIT_FLAG_NOT_SELECTABLE = 0x02000000
UNIT_FLAG_NON_ATTACKABLE = 0x2
CREATURE_FLAG_EXTRA_NO_XP = 0x40
RESOLVE = "spell_boss_mechanics_resolve"
OWN_SCRIPTS = {
    SOUL: "spell_scholo_malicia_soul",
    SOUL_WEIGHT: "spell_scholo_malicia_soul_weight",
    SHADOW_HEAL: "spell_scholo_malicia_shadow_heal",
    SHADOW_NOVA: "spell_scholo_malicia_shadow_nova",
    SOUL_LOST: "spell_scholo_malicia_soul_lost",
}


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


def _header_int(name: str) -> int:
    match = re.search(rf"\b{name}\s*=\s*(-?\d+)", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return int(match.group(1))


def _header_nh(name: str) -> tuple[float, float]:
    match = re.search(rf"\b{name}\{{\s*([\d.]+)f?,\s*([\d.]+)f?\s*\}}", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return float(match.group(1)), float(match.group(2))


class MaliciaDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) in (SHADE, SOUL_UNIT)}
        cls.models = {int(e["CreatureID"]): e for e in reg.creature_template_models
                      if int(e["CreatureID"]) in (SHADE, SOUL_UNIT)}
        cls.edits = [e for e in reg.creature_template_edits if int(e["entry"]) == MALICIA]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(SOUL, SOUL_LOST + 1)))
        self.assertEqual(id_blocks.out_of_reservation("scholomance", {"spell": mine}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_MA_\w+\s*=\s*(\d{6})",
                                                 HEADER.read_text(encoding="utf-8"))}
        self.assertEqual(header_ids, set(mine))

    def test_the_shade_and_the_soul(self):
        self.assertEqual(sorted(self.creatures), [SHADE, SOUL_UNIT])
        self.assertEqual(id_blocks.out_of_reservation("scholomance", {"creature": [SHADE, SOUL_UNIT]}), [])
        shade = self.creatures[SHADE]
        self.assertEqual(shade["ScriptName"], "npc_sc_malicias_shade")
        self.assertEqual(shade["rank"], 1)
        self.assertEqual(shade["minlevel"], 60)
        self.assertEqual(shade["unit_class"], 1)
        # 12k at level 60: the warrior base 3,052 (heroic 18k is WP-H's override on 310114).
        self.assertEqual(-(-3052 * shade["HealthModifier"] // 1), _header_nh("kShadeHealth")[0])
        self.assertEqual(shade["difficulty_entry_1"], 310114)
        self.assertEqual(shade["lootid"], 0)
        self.assertFalse(shade["unit_flags"] & UNIT_FLAG_NOT_SELECTABLE)
        self.assertEqual(self.models[SHADE]["CreatureDisplayID"], 4629)
        soul = self.creatures[SOUL_UNIT]
        self.assertTrue(soul["unit_flags"] & UNIT_FLAG_NOT_SELECTABLE)
        self.assertTrue(soul["unit_flags"] & UNIT_FLAG_NON_ATTACKABLE)
        self.assertTrue(soul["flags_extra"] & CREATURE_FLAG_EXTRA_NO_XP)
        self.assertFalse(soul["flags_extra"] & 0x80)     # not a trigger: the wisp must show
        self.assertEqual(soul["ScriptName"], "")
        self.assertEqual(soul.get("difficulty_entry_1", 0), 0)
        self.assertEqual(self.models[SOUL_UNIT]["CreatureDisplayID"], 1825)
        self.assertNotEqual(self.models[SOUL_UNIT]["CreatureDisplayID"], 30233)

    def test_soul_is_a_meter_nobody_removes(self):
        soul = self.spells[SOUL]
        self.assertEqual(_raw(soul, "CumulativeAura"), _header_int("kSoulCap"))
        self.assertEqual(soul["dispel"], 0)
        self.assertEqual(soul["mechanic"], 0)
        self.assertTrue(soul["attributes"] & ATTR0_NO_AURA_CANCEL)
        self.assertTrue(soul["attributes"] & ATTR0_NO_IMMUNITIES)
        self.assertEqual(soul["duration_ms"], -1)
        self.assertEqual(soul["effect1"]["apply_aura"], AURA_DUMMY)
        weight = self.spells[SOUL_WEIGHT]
        self.assertTrue(weight["attributes"] & ATTR0_DO_NOT_DISPLAY)
        self.assertTrue(weight["attributes"] & ATTR0_NO_AURA_CANCEL)
        self.assertEqual(weight["duration_ms"], -1)
        self.assertEqual(_raw(weight, "CumulativeAura"), 0)      # one stack: the amount is the script's, unmultiplied
        auras = [weight[f"effect{i}"]["apply_aura"] for i in (1, 2, 3)]
        self.assertEqual(auras, [AURA_MOD_DAMAGE_PERCENT_DONE, AURA_MOD_HEALING_DONE_PERCENT,
                                 AURA_MOD_INCREASE_HEALTH_PERCENT])
        self.assertEqual(weight["effect1"]["misc_value"], 127)

    def test_soul_never_leaves_the_map(self):
        # R-B S5 SF-1: a logout or a map change drops the meter and its weight (no +100% / -50% outside the fight).
        for spell_id in (SOUL, SOUL_WEIGHT):
            self.assertTrue(_raw(self.spells[spell_id], "AuraInterruptFlags") & AURA_INTERRUPT_FLAG_CHANGE_MAP,
                            spell_id)

    def test_bound_soul(self):
        bound = self.spells[BOUND]
        self.assertEqual(_raw(bound, "CumulativeAura"), _header_int("kBoundCap"))
        self.assertEqual(bound["effect1"]["apply_aura"], AURA_MOD_DAMAGE_PERCENT_DONE)
        self.assertEqual(bound["effect1"]["base_points"], _header_int("kBoundPctPerStack"))
        self.assertEqual(bound["effect1"]["die_sides"], 0)
        self.assertEqual(bound["effect1"]["misc_value"], 127)
        self.assertEqual(bound["duration_ms"], -1)

    def test_casts(self):
        self.assertEqual(self.spells[DRAIN_CAST]["cast_time_ms"], _header_int("kDrainCastMs"))
        self.assertEqual(self.spells[STORM_CAST]["cast_time_ms"], 3500)
        for spell_id in (DRAIN_CAST, STORM_CAST):
            self.assertEqual(_raw(self.spells[spell_id], "InterruptFlags"), 0)
            # Physical: a kick on Shadow Heal (or Corruption) locks Shadow; a Shadow bar would then be refused.
            self.assertEqual(int(self.spells[spell_id]["school"]), 1, spell_id)
        heal = self.spells[SHADOW_HEAL]
        self.assertEqual(heal["cast_time_ms"], _header_int("kHealCastMs"))
        self.assertEqual(_raw(heal, "InterruptFlags"), 15)
        self.assertEqual(_raw(heal, "PreventionType"), 1)
        self.assertEqual(heal["effect1"]["type"], HEAL)
        self.assertEqual(heal["effect2"]["type"], TRIGGER_SPELL)
        self.assertEqual(heal["effect2"]["trigger_spell"], SHADOW_NOVA)
        self.assertTrue(_raw(heal, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        volley = self.spells[SHADE_VOLLEY]
        self.assertEqual(volley["cast_time_ms"], _header_int("kShadeVolleyCastMs"))
        self.assertEqual(_raw(volley, "InterruptFlags"), 15)
        self.assertEqual(_raw(volley, "PreventionType"), 1)
        self.assertEqual(volley["effect1"]["type"], TRIGGER_SPELL)
        self.assertEqual(volley["effect1"]["trigger_spell"], _header_int("SPELL_MA_STOCK_SHADOW_BOLT_VOLLEY"))
        for spell_id in (SHADOW_NOVA, SOUL_LOST):
            s = self.spells[spell_id]
            self.assertEqual(s["effect1"]["type"], SCHOOL_DAMAGE)
            self.assertTrue(s["effect1"].get("_potency_excluded"))
            self.assertTrue(_raw(s, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
            self.assertTrue(_raw(s, "AttributesEx2") & ATTR2_CANT_CRIT)
        self.assertEqual(self.spells[STORM_BLAST]["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertTrue(_raw(self.spells[STORM_BLAST], "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertEqual(float(_raw(self.spells[STORM_FALL], "Speed")), 20.0)
        self.assertIn("kStormFallSpeed = 20.f", HEADER.read_text(encoding="utf-8"))

    def test_scripts_are_bound_and_registered(self):
        self.assertIn((STORM_BLAST, RESOLVE), self.scripts)
        for spell_id, name in OWN_SCRIPTS.items():
            self.assertIn((spell_id, name), self.scripts)
            self.assertIn(f"RegisterSpellScript({name})", self.cpp)
        own = {name for _, name in self.scripts if name != RESOLVE}
        self.assertEqual(own, set(OWN_SCRIPTS.values()))
        for ai in ("boss_instructor_malicia_rework", "npc_sc_examiner_malicia", "npc_sc_malicias_shade"):
            self.assertIn(f"RegisterDungeonReworkCreatureAI({ai},", self.cpp)
        # The examiner is bound in wave C (S13): registered only then, so wave B boots with no unassigned name.
        self.assertRegex(self.cpp, r"if \(kWaveCBound\)\s*RegisterDungeonReworkCreatureAI\(npc_sc_examiner_malicia,")
        self.assertIn('kExaminerScriptName[] = "npc_sc_examiner_malicia"', FIGHT_HEADER.read_text(encoding="utf-8"))
        self.assertIn("RegisterSoloLesson(Classroom::Coven,", self.cpp)

    def test_looks_are_the_visual_picks(self):
        expected = {DRAIN: 12656, BOUND: 7784, STORM_CAST: 14509, STORM_FALL: 14512, STORM_BLAST: 7180,
                    STORM_BURST: 7180, SHADOW_HEAL: 7380, SHADOW_NOVA: 7951, SOUL_LOST: 12656}
        for spell_id, visual in expected.items():
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), visual, spell_id)

    def test_malicia_is_bound(self):
        self.assertEqual(len(self.edits), 1)
        edit = self.edits[0]
        self.assertEqual(edit["ScriptName"], "boss_instructor_malicia_rework")
        self.assertEqual(edit["AIName"], "")
        self.assertEqual(edit["HealthModifier"], 65.52)
        self.assertEqual(edit["DamageModifier"], 3.5)
        self.assertEqual(edit["CreatureImmunitiesId"], 1972)
        self.assertEqual(edit["flags_extra"], 1)


if __name__ == "__main__":
    unittest.main()
