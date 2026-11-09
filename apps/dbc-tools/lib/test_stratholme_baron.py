"""
Stratholme build WP-S14, Baron Rivendare: source/npcs/stratholme/baron_rivendare.py against its C++
(modules/mod-dungeon-bosses src/Stratholme/BaronLogic.h, boss_baron_rivendare_rework.cpp).

Checks:
  - the spells sit in the Baron's slice (206705-206719, never S15's 206720-206734) and BaronLogic.h names the same ids;
  - the rot stalker 300588 is an invisible, unselectable trigger in the `stratholme` creature reservation, with no
    heroic template;
  - Unholy Aura triggers its pulse every 2 s; the pulse is a 100 yd area Shadow hit whose damage its SpellScript sets
    (bound, registered, ignores caster modifiers, no crit, always hits);
  - the rot: a resolve copy for the ticks, a 45 s area look on the stalker, the 3 s mark on the target;
  - the skeletons' strike carries BaronLogic.h's percents for the kit's generic percent script (hundredths, heroic in
    MiscValueB), a melee hit;
  - 10440 keeps -419 with its script; 11197 is bound to npc_st_mindless_skeleton with SmartAI off and 6,000 health.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_stratholme_baron.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Stratholme"
HEADER = MODULE_DIR / "BaronLogic.h"
SCRIPT = MODULE_DIR / "boss_baron_rivendare_rework.cpp"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "stratholme"

SLICE = range(206705, 206720)
S15_SLICE = range(206720, 206735)
UNHOLY_AURA, UNHOLY_PULSE, RISE, DEATH_AND_DECAY, ROT, ROT_LOOK, STRIKE = range(206705, 206712)
ROT_STALKER = 300588
BARON = 10440
SKELETON = 11197

SCHOOL_DAMAGE, APPLY_AURA, PERSISTENT_AREA_AURA = 2, 6, 27
AURA_DUMMY, AURA_PERIODIC_TRIGGER_SPELL = 4, 23
TARGET_UNIT_SRC_AREA_ENEMY = 15
TARGET_UNIT_TARGET_ENEMY = 6
ATTR0_DO_NOT_DISPLAY = 0x00000080
ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004
ATTR2_CANT_CRIT = 0x20000000
ATTR3_ALWAYS_HIT = 0x00040000
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
UNIT_FLAG_NOT_SELECTABLE = 0x02000000
CREATURE_FLAG_EXTRA_NO_XP = 0x40
CREATURE_FLAG_EXTRA_TRIGGER = 0x80
RESOLVE = "spell_boss_mechanics_resolve"
PULSE_SCRIPT = "spell_strat_baron_unholy_aura_pulse"
REFFLAT_SCRIPT = "spell_dungeon_refflat_damage"
WARRIOR_62_BASE = 3237      # creature_classlevelstats level 62 class 1 basehp0 (live 2026-11-09)


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


def _header_number(name: str) -> float:
    match = re.search(rf"{name}\s*=\s*(-?[\d.]+)f?;", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return float(match.group(1))


def _header_nh(name: str) -> tuple[float, float]:
    match = re.search(rf"{name}\{{\s*(-?[\d.]+)f?,\s*(-?[\d.]+)f?\s*\}}", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return float(match.group(1)), float(match.group(2))


class BaronDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE or int(e["id"]) in S15_SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == ROT_STALKER}
        cls.models = {int(e["CreatureID"]): e for e in reg.creature_template_models
                      if int(e["CreatureID"]) == ROT_STALKER}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) in (BARON, SKELETON)}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(i for i in self.spells if i in SLICE)
        self.assertEqual(mine, list(range(UNHOLY_AURA, STRIKE + 1)))
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"spell": mine}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_BR_\w+\s*=\s*(\d+)", HEADER.read_text(encoding="utf-8"))}
        self.assertEqual(header_ids, set(mine))
        self.assertFalse(header_ids & set(S15_SLICE))

    def test_the_rot_stalker_is_an_invisible_trigger(self):
        self.assertEqual(sorted(self.creatures), [ROT_STALKER])
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"creature": [ROT_STALKER]}), [])
        stalker = self.creatures[ROT_STALKER]
        self.assertTrue(stalker["unit_flags"] & UNIT_FLAG_NOT_SELECTABLE)
        self.assertTrue(stalker["flags_extra"] & CREATURE_FLAG_EXTRA_NO_XP)
        self.assertTrue(stalker["flags_extra"] & CREATURE_FLAG_EXTRA_TRIGGER)
        self.assertEqual(stalker["ScriptName"], "")
        self.assertEqual(stalker["lootid"], 0)
        self.assertEqual(stalker.get("difficulty_entry_1", 0), 0)
        self.assertEqual(self.models[ROT_STALKER]["CreatureDisplayID"], 11686)
        self.assertIn("NPC_ST_ROT", self.cpp)

    def test_unholy_aura_pulses_every_two_seconds(self):
        aura = self.spells[UNHOLY_AURA]
        self.assertEqual(aura["effect1"]["apply_aura"], AURA_PERIODIC_TRIGGER_SPELL)
        self.assertEqual(aura["effect1"]["amplitude"], int(_header_number("kUnholyAuraPeriodMs")))
        self.assertEqual(aura["effect1"]["trigger_spell"], UNHOLY_PULSE)
        self.assertEqual(aura["duration_ms"], -1)
        pulse = self.spells[UNHOLY_PULSE]
        self.assertEqual(pulse["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertEqual(pulse["effect1"]["implicit_target_b"], TARGET_UNIT_SRC_AREA_ENEMY)
        self.assertEqual(pulse["effect1"]["radius_yards"], _header_number("kUnholyAuraRadius"))
        self.assertTrue(_raw(pulse, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertTrue(_raw(pulse, "AttributesEx3") & ATTR3_ALWAYS_HIT)
        self.assertTrue(_raw(pulse, "AttributesEx2") & ATTR2_CANT_CRIT)
        self.assertTrue(_raw(pulse, "AttributesEx2") & ATTR2_IGNORE_LINE_OF_SIGHT)
        # The script's area hook must name the same implicit target the spell carries (a mismatch unbinds it).
        self.assertIn("EFFECT_0, TARGET_UNIT_SRC_AREA_ENEMY", self.cpp)

    def test_spell_scripts_are_bound_and_registered(self):
        self.assertIn((UNHOLY_PULSE, PULSE_SCRIPT), self.scripts)
        self.assertIn(f"RegisterSpellScript({PULSE_SCRIPT})", self.cpp)
        self.assertIn((ROT, RESOLVE), self.scripts)
        self.assertIn((STRIKE, REFFLAT_SCRIPT), self.scripts)
        own = {name for _, name in self.scripts if name not in (RESOLVE, REFFLAT_SCRIPT)}
        self.assertEqual(own, {PULSE_SCRIPT})

    def test_death_and_decay(self):
        mark = self.spells[DEATH_AND_DECAY]
        self.assertEqual(mark["duration_ms"], int(_header_number("kDeathAndDecayWarnMs")))
        self.assertEqual(mark["dispel"], 0)
        self.assertEqual(self.spells[ROT]["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertTrue(_raw(self.spells[ROT], "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        look = self.spells[ROT_LOOK]
        self.assertEqual(look["effect1"]["type"], PERSISTENT_AREA_AURA)
        self.assertEqual(look["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(look["effect1"]["radius_yards"], _header_number("kRotRadius"))
        self.assertEqual(look["duration_ms"], int(_header_number("kRotLookMs")))
        self.assertTrue(look["attributes"] & ATTR0_DO_NOT_DISPLAY)
        normal, heroic = _header_nh("kRotLifeMs")
        self.assertLessEqual(heroic, look["duration_ms"])
        self.assertEqual(_raw(look, "SpellVisualID_1"), 9735)

    def test_the_skeleton_strike_carries_the_percents(self):
        strike = self.spells[STRIKE]
        effect = strike["effect1"]
        self.assertEqual(effect["type"], SCHOOL_DAMAGE)
        self.assertEqual(effect["implicit_target_a"], TARGET_UNIT_TARGET_ENEMY)
        normal, heroic = _header_nh("kSkeletonStrikePct")
        self.assertEqual(effect["base_points"] + 1, round(normal * 100))
        self.assertEqual(effect["die_sides"], 1)
        self.assertEqual(_raw(strike, "EffectMiscValueB_1"), round(heroic * 100))
        self.assertEqual(_raw(strike, "DefenseType"), 2)
        self.assertTrue(_raw(strike, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertTrue(_raw(strike, "AttributesEx2") & ATTR2_CANT_CRIT)
        self.assertTrue(effect.get("_potency_excluded"))
        self.assertIn("SPELL_BR_SKELETON_STRIKE", self.cpp)

    def test_the_baron_and_his_skeletons_are_bound(self):
        baron = self.edits[BARON]
        self.assertEqual(baron["ScriptName"], "boss_baron_rivendare_rework")
        self.assertEqual(baron["CreatureImmunitiesId"], -419)
        skeleton = self.edits[SKELETON]
        self.assertEqual(skeleton["ScriptName"], "npc_st_mindless_skeleton")
        self.assertEqual(skeleton["AIName"], "")
        normal, _ = _header_nh("kSkeletonHealth")
        self.assertEqual(int(WARRIOR_62_BASE * skeleton["HealthModifier"]), int(normal))
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_st_mindless_skeleton", self.cpp)
        self.assertNotIn("CreatureImmunitiesId", skeleton)       # the stock -122 stays

    def test_looks(self):
        expected = {UNHOLY_AURA: 682, UNHOLY_PULSE: 4322, RISE: 634, ROT_LOOK: 9735, STRIKE: 39}
        for spell_id, visual in expected.items():
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), visual, spell_id)


if __name__ == "__main__":
    unittest.main()
