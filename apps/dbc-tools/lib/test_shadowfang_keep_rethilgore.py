"""
Shadowfang Keep build WP-S1, Rethilgore: source/npcs/shadowfang_keep/rethilgore.py against its C++
(modules/mod-dungeon-bosses src/ShadowfangKeep/RethilgoreLogic.h, boss_rethilgore_rework.cpp).

Checks:
  - the spells sit in Rethilgore's slice (205910-205929) and RethilgoreLogic.h names the same ids;
  - the creatures 300500-300502 sit in the `shadowfang_keep` creature slice, with their looks and script names, and
    every scripted name (creatures and spells) is one boss_rethilgore_rework.cpp registers;
  - the Pilot lessons on the custom damage spells: the tick and the tainted pop ignore caster modifiers, the tick's
    damage is set by its SpellScript, the pop is the registry's resolve copy;
  - the Soul Drain channel: channeled, not interruptible (no interrupt flags, PreventionType 0), not dispellable, he
    keeps acting while he channels, ignores LoS;
  - the heals carry no caster bonus (DefenseType 0, ignores caster modifiers) and every damage or heal effect is
    excluded from potency;
  - the Cell Door stand-in: 720 on normal from its HealthModifier, its heroic template id (STAGE-H: 310057), no XP,
    no loot, no armor; the fragments are not selectable;
  - 3914 is bound to boss_rethilgore_rework with SmartAI off, HealthModifier 25 and immunity set 1972.

Only this boss's ids are looked at: the other Shadowfang Keep bosses declare in the same package.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_shadowfang_keep_rethilgore.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "ShadowfangKeep"
HEADER = MODULE_DIR / "RethilgoreLogic.h"
SCRIPT = MODULE_DIR / "boss_rethilgore_rework.cpp"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "shadowfang_keep"

SLICE = range(205910, 205930)
LEAP, CAST_BAR, FLASH, CHANNEL, TICK, RETURN, STREAK, FEAST, KEY, TAINTED = range(205910, 205920)
DOOR, FRAGMENT, TAINTED_LOOK = 300500, 300501, 300502
DOOR_HEROIC = 310057
RETHILGORE = 3914

SCHOOL_DAMAGE, HEAL = 2, 10
ATTR1_IS_CHANNELED = 0x00000004
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
ATTR5_ALLOW_ACTION_DURING_CHANNEL = 0x00000001
ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004
UNIT_FLAG_NOT_SELECTABLE = 0x02000000
CREATURE_FLAG_EXTRA_NO_XP = 0x40


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


class RethilgoreDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if DOOR <= int(e["entry"]) <= TAINTED_LOOK}
        cls.models = {int(e["CreatureID"]): e for e in reg.creature_template_models
                      if DOOR <= int(e["CreatureID"]) <= TAINTED_LOOK}
        cls.edits = [e for e in reg.creature_template_edits if int(e["entry"]) == RETHILGORE]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        self.assertEqual(sorted(self.spells), list(range(LEAP, TAINTED + 1)))
        self.assertEqual(id_blocks.out_of_reservation("shadowfang_keep", {"spell": sorted(self.spells)}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_\w+\s*=\s*(\d+)", HEADER.read_text(encoding="utf-8"))}
        self.assertEqual(header_ids, set(self.spells))

    def test_creatures_sit_in_the_slice_with_looks_and_scripts(self):
        self.assertEqual(sorted(self.creatures), [DOOR, FRAGMENT, TAINTED_LOOK])
        self.assertEqual(id_blocks.out_of_reservation("shadowfang_keep", {"creature": sorted(self.creatures)}), [])
        self.assertEqual(self.models[DOOR]["CreatureDisplayID"], 11686)
        self.assertEqual(self.models[FRAGMENT]["CreatureDisplayID"], 1825)
        self.assertEqual(self.models[TAINTED_LOOK]["CreatureDisplayID"], 24465)
        self.assertEqual(self.models[TAINTED_LOOK]["DisplayScale"], 1.0)
        for entry, name in ((DOOR, "npc_sfk_cell_door"), (FRAGMENT, "npc_sfk_soul_fragment"),
                            (TAINTED_LOOK, "npc_sfk_soul_fragment")):
            self.assertEqual(self.creatures[entry]["ScriptName"], name)
            self.assertIn(f"RegisterDungeonReworkCreatureAI({name},", self.cpp)

    def test_spell_scripts_are_registered(self):
        self.assertIn((TICK, "spell_sfk_rethilgore_soul_drain"), self.scripts)
        self.assertIn((TAINTED, "spell_boss_mechanics_resolve"), self.scripts)
        self.assertIn("RegisterSpellScript(spell_sfk_rethilgore_soul_drain)", self.cpp)
        own = {name for _, name in self.scripts if name != "spell_boss_mechanics_resolve"}
        self.assertEqual(own, {"spell_sfk_rethilgore_soul_drain"})

    def test_damage_spells_ignore_caster_modifiers(self):
        for spell_id in (TICK, TAINTED):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE)
            self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS, spell_id)
            self.assertEqual(_raw(spell, "DefenseType"), 1, spell_id)
            self.assertTrue(_raw(spell, "AttributesEx2") & ATTR2_IGNORE_LINE_OF_SIGHT, spell_id)
            self.assertTrue(spell["effect1"].get("_potency_excluded"), spell_id)

    def test_soul_drain_is_a_channel_that_cannot_be_stopped(self):
        channel = self.spells[CHANNEL]
        self.assertTrue(_raw(channel, "AttributesEx") & ATTR1_IS_CHANNELED)
        self.assertTrue(_raw(channel, "AttributesEx5") & ATTR5_ALLOW_ACTION_DURING_CHANNEL)
        self.assertTrue(_raw(channel, "AttributesEx2") & ATTR2_IGNORE_LINE_OF_SIGHT)
        for column in ("InterruptFlags", "ChannelInterruptFlags", "AuraInterruptFlags", "PreventionType"):
            self.assertEqual(_raw(channel, column), 0, column)
        self.assertEqual(channel["dispel"], 0)
        self.assertEqual(_raw(channel, "SpellVisualID_1"), 680)    # the soul beam: on a channel only

    def test_heals_carry_no_caster_bonus(self):
        for spell_id in (RETURN, FEAST):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], HEAL)
            self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS, spell_id)
            self.assertEqual(_raw(spell, "DefenseType"), 0, spell_id)
            self.assertTrue(spell["effect1"].get("_potency_excluded"), spell_id)

    def test_visual_spells_and_the_key(self):
        self.assertEqual(_raw(self.spells[LEAP], "SpellVisualID_1"), 11546)
        self.assertEqual(_raw(self.spells[FLASH], "SpellVisualID_1"), 3303)
        self.assertEqual(_raw(self.spells[STREAK], "SpellVisualID_1"), 9253)
        self.assertGreater(float((self.spells[STREAK]["raw_overrides"] or {}).get("Speed", 0)), 0.0)
        self.assertEqual(self.spells[CAST_BAR]["cast_time_ms"], 1500)
        key = self.spells[KEY]
        self.assertEqual(key["dispel"], 0)
        self.assertEqual(key["duration_ms"], 600000)
        self.assertTrue(key["raw_overrides"]["AuraDescription_Lang_enUS"])

    def test_the_door_stand_in(self):
        door = self.creatures[DOOR]
        self.assertEqual(round(door["HealthModifier"] * 484), 720)
        self.assertEqual(door["difficulty_entry_1"], DOOR_HEROIC)
        self.assertEqual(door["lootid"], 0)
        self.assertEqual(door["ArmorModifier"], 0.0)
        self.assertEqual(door["DamageModifier"], 0.0)
        self.assertTrue(door["flags_extra"] & CREATURE_FLAG_EXTRA_NO_XP)
        self.assertFalse(door["unit_flags"] & UNIT_FLAG_NOT_SELECTABLE)
        for entry in (FRAGMENT, TAINTED_LOOK):
            self.assertTrue(self.creatures[entry]["unit_flags"] & UNIT_FLAG_NOT_SELECTABLE)
            self.assertEqual(self.creatures[entry]["difficulty_entry_1"], 0)

    def test_rethilgore_is_bound(self):
        self.assertEqual(len(self.edits), 1)
        edit = self.edits[0]
        self.assertEqual(edit["ScriptName"], "boss_rethilgore_rework")
        self.assertEqual(edit["AIName"], "")
        self.assertEqual(edit["HealthModifier"], 25)
        self.assertEqual(edit["CreatureImmunitiesId"], 1972)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_rethilgore_rework,", self.cpp)


if __name__ == "__main__":
    unittest.main()
