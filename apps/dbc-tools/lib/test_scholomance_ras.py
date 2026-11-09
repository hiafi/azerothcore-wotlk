"""
Scholomance build WP-S4, Ras Frostwhisper: source/npcs/scholomance/ras_frostwhisper.py against its C++
(modules/mod-dungeon-bosses src/Scholomance/RasLogic.h, boss_ras_frostwhisper_rework.cpp).

Checks:
  - the spells sit in Ras's slice (206170-206189, never S12's 206190-206204) and RasLogic.h names the same ids;
  - the Blizzard anchor 300534 is an invisible, unselectable trigger in the `scholomance` creature reservation, with no
    heroic template;
  - Chill: a 20-stack meter nothing removes; Entombed: a 2 s stun no trinket breaks; Warmth: not cancellable;
  - the resolve copies (thaw, Chill Nova, Blizzard tick) are bound to spell_boss_mechanics_resolve; the Volley is a
    real 3 s interruptible cast whose damage its SpellScript sets (ignores caster modifiers, no crit), with the slow;
  - the Nova's knockback rider carries RasLogic.h's numbers; the looks are WP-V's picks;
  - 10508 is bound to boss_ras_frostwhisper_rework with SmartAI off, HealthModifier 75.29, DamageModifier 3.5 and
    immunity set 1972.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scholomance_ras.py
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
HEADER = MODULE_DIR / "RasLogic.h"
SCRIPT = MODULE_DIR / "boss_ras_frostwhisper_rework.cpp"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "scholomance"

SLICE = range(206170, 206190)
S12_SLICE = range(206190, 206205)
(CHILL, DEEP_CHILL, WARMTH, ENTOMBED, THAW, FROST_MARK, CHILL_NOVA, NOVA_KNOCK, BLIZZARD_CAST, BLIZZARD,
 BLIZZARD_LOOK, BLIZZARD_DRIFT, VOLLEY) = range(206170, 206183)
ANCHOR = 300534
RAS = 10508

SCHOOL_DAMAGE, APPLY_AURA, KNOCK_BACK, PERSISTENT_AREA_AURA = 2, 6, 98, 27
AURA_DUMMY, AURA_MOD_STUN, AURA_MOD_DECREASE_SPEED = 4, 12, 33
ATTR0_DO_NOT_DISPLAY = 0x00000080
ATTR0_NO_IMMUNITIES = 0x20000000
AURA_INTERRUPT_FLAG_CHANGE_MAP = 0x00080000
ATTR0_NO_AURA_CANCEL = 0x80000000
ATTR2_CANT_CRIT = 0x20000000
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
UNIT_FLAG_NOT_SELECTABLE = 0x02000000
CREATURE_FLAG_EXTRA_NO_XP = 0x40
CREATURE_FLAG_EXTRA_TRIGGER = 0x80
RESOLVE = "spell_boss_mechanics_resolve"
VOLLEY_SCRIPT = "spell_scholo_ras_frostbolt_volley"


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
    match = re.search(rf"{name}\s*=\s*(-?\d+)", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return int(match.group(1))


class RasDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE or int(e["id"]) in S12_SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == ANCHOR}
        cls.models = {int(e["CreatureID"]): e for e in reg.creature_template_models if int(e["CreatureID"]) == ANCHOR}
        cls.edits = [e for e in reg.creature_template_edits if int(e["entry"]) == RAS]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(i for i in self.spells if i in SLICE)
        self.assertEqual(mine, list(range(CHILL, VOLLEY + 1)))
        self.assertEqual(id_blocks.out_of_reservation("scholomance", {"spell": mine}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_RF_\w+\s*=\s*(\d+)", HEADER.read_text(encoding="utf-8"))}
        self.assertEqual(header_ids, set(mine))
        self.assertFalse(header_ids & set(S12_SLICE))

    def test_the_anchor_is_an_invisible_trigger(self):
        self.assertEqual(sorted(self.creatures), [ANCHOR])
        self.assertEqual(id_blocks.out_of_reservation("scholomance", {"creature": [ANCHOR]}), [])
        anchor = self.creatures[ANCHOR]
        self.assertTrue(anchor["unit_flags"] & UNIT_FLAG_NOT_SELECTABLE)
        self.assertTrue(anchor["flags_extra"] & CREATURE_FLAG_EXTRA_NO_XP)
        self.assertTrue(anchor["flags_extra"] & CREATURE_FLAG_EXTRA_TRIGGER)
        self.assertEqual(anchor["ScriptName"], "")
        self.assertEqual(anchor["lootid"], 0)
        self.assertEqual(anchor.get("difficulty_entry_1", 0), 0)
        self.assertEqual(self.models[ANCHOR]["CreatureDisplayID"], 11686)

    def test_spell_scripts_are_bound_and_registered(self):
        for spell_id in (THAW, CHILL_NOVA, BLIZZARD):
            self.assertIn((spell_id, RESOLVE), self.scripts)
        self.assertIn((VOLLEY, VOLLEY_SCRIPT), self.scripts)
        self.assertIn(f"RegisterSpellScript({VOLLEY_SCRIPT})", self.cpp)
        own = {name for _, name in self.scripts if name != RESOLVE}
        self.assertEqual(own, {VOLLEY_SCRIPT})

    def test_chill_is_a_meter_nothing_removes(self):
        chill = self.spells[CHILL]
        self.assertEqual(_raw(chill, "CumulativeAura"), _header_int("kChillMax"))
        self.assertEqual(chill["dispel"], 0)
        self.assertEqual(chill["mechanic"], 0)
        self.assertTrue(chill["attributes"] & ATTR0_NO_IMMUNITIES)
        self.assertEqual(chill["duration_ms"], -1)
        self.assertEqual(chill["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertTrue(self.spells[DEEP_CHILL]["attributes"] & ATTR0_DO_NOT_DISPLAY)
        self.assertEqual(self.spells[DEEP_CHILL]["duration_ms"], -1)
        warmth = self.spells[WARMTH]
        self.assertTrue(warmth["attributes"] & ATTR0_NO_AURA_CANCEL)
        self.assertEqual(warmth["duration_ms"], -1)

    def test_entombed_is_a_two_second_stun_nothing_breaks(self):
        tomb = self.spells[ENTOMBED]
        self.assertEqual(tomb["effect1"]["apply_aura"], AURA_MOD_STUN)
        self.assertEqual(tomb["duration_ms"], _header_int("kTombMs"))
        self.assertEqual(tomb["mechanic"], 0)
        self.assertEqual(tomb["effect1"].get("mechanic", 0), 0)
        self.assertEqual(tomb["dispel"], 0)
        self.assertTrue(tomb["attributes"] & ATTR0_NO_IMMUNITIES)

    def test_fight_auras_never_leave_the_map(self):
        # R-C KEEPSAKE B-1 / N-5: Chill, Deep Chill, Warmth and Entombed (which S12 makes permanent) are dropped before
        # the logout save, after the login load and on a map change; a same-map teleport (detention) keeps them.
        for spell_id in (CHILL, DEEP_CHILL, WARMTH, ENTOMBED):
            self.assertTrue(_raw(self.spells[spell_id], "AuraInterruptFlags") & AURA_INTERRUPT_FLAG_CHANGE_MAP,
                            spell_id)

    def test_frost_mark_and_the_nova(self):
        self.assertEqual(self.spells[FROST_MARK]["duration_ms"], _header_int("kFrostMarkWarnMs"))
        self.assertEqual(self.spells[CHILL_NOVA]["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertTrue(_raw(self.spells[CHILL_NOVA], "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        knock = self.spells[NOVA_KNOCK]
        self.assertEqual(knock["effect1"]["type"], KNOCK_BACK)
        self.assertEqual(knock["effect1"]["misc_value"], _header_int("kNovaKnockMisc"))
        self.assertEqual(knock["effect1"]["base_points"], _header_int("kNovaKnockBasePoints"))
        self.assertEqual(knock["effect1"]["die_sides"], 0)
        self.assertIn("Rider(SPELL_RF_CHILL_NOVA_KNOCK)", self.cpp)

    def test_blizzard(self):
        self.assertEqual(self.spells[BLIZZARD_CAST]["cast_time_ms"], _header_int("kBlizzardCastMs"))
        self.assertEqual(_raw(self.spells[BLIZZARD_CAST], "InterruptFlags"), 0)
        self.assertEqual(self.spells[BLIZZARD]["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertEqual(self.spells[BLIZZARD_LOOK]["duration_ms"], _header_int("kBlizzardLifeMs"))
        for spell_id in (BLIZZARD_LOOK, BLIZZARD_DRIFT):
            look = self.spells[spell_id]
            self.assertEqual(look["effect1"]["type"], PERSISTENT_AREA_AURA)
            self.assertTrue(look["attributes"] & ATTR0_DO_NOT_DISPLAY)
        # The drifting storm's 3 s pieces overlap its 2 s re-cast beat.
        self.assertGreater(self.spells[BLIZZARD_DRIFT]["duration_ms"], _header_int("kBlizzardDriftLookEveryMs"))

    def test_the_volley_is_a_real_interruptible_cast(self):
        volley = self.spells[VOLLEY]
        self.assertEqual(volley["cast_time_ms"], _header_int("kVolleyCastMs"))
        self.assertEqual(_raw(volley, "InterruptFlags"), 15)
        self.assertEqual(_raw(volley, "PreventionType"), 1)
        self.assertEqual(volley["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertTrue(volley["effect1"].get("_potency_excluded"))
        self.assertEqual(volley["effect2"]["apply_aura"], AURA_MOD_DECREASE_SPEED)
        self.assertEqual(volley["effect2"]["base_points"] + 1, -50)
        self.assertTrue(_raw(volley, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertTrue(_raw(volley, "AttributesEx2") & ATTR2_CANT_CRIT)
        self.assertIn("SPELL_RF_FROSTBOLT_VOLLEY, 2", self.cpp)            # the interrupt list
        self.assertIn("EFFECT_0,\n            SPELL_EFFECT_SCHOOL_DAMAGE", self.cpp)

    def test_looks_are_the_visual_picks(self):
        expected = {CHILL: 675, DEEP_CHILL: 6778, WARMTH: 6591, ENTOMBED: 4340, THAW: 14726, FROST_MARK: 15254,
                    CHILL_NOVA: 4823, BLIZZARD_LOOK: 13698, BLIZZARD_DRIFT: 13698, VOLLEY: 13}
        for spell_id, visual in expected.items():
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), visual, spell_id)

    def test_ras_is_bound(self):
        self.assertEqual(len(self.edits), 1)
        edit = self.edits[0]
        self.assertEqual(edit["ScriptName"], "boss_ras_frostwhisper_rework")
        self.assertEqual(edit["AIName"], "")
        self.assertEqual(edit["HealthModifier"], 75.29)
        self.assertEqual(edit["DamageModifier"], 3.5)
        self.assertEqual(edit["CreatureImmunitiesId"], 1972)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_ras_frostwhisper_rework,", self.cpp)


if __name__ == "__main__":
    unittest.main()
