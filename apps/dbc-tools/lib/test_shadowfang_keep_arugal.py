"""
Shadowfang Keep build WP-S9, Archmage Arugal: source/npcs/shadowfang_keep/archmage_arugal.py against its C++
(modules/mod-dungeon-bosses src/ShadowfangKeep/ArugalLogic.h, boss_archmage_arugal_rework.cpp).

Checks:
  - the spells sit in Arugal's slice (206060-206084, never S10's 206085-206089) and ArugalLogic.h names the same ids;
  - the creatures (the lair prisoners 300513 / 300514, the ward stalker 300515) sit in the `shadowfang_keep` creature
    slice; the prisoners have their gossip menus, are not attackable and ignored by creatures; the stalker is an
    invisible, unselectable trigger; every scripted name is one the C++ registers;
  - the Worgen's Curse: 100 stacks, never dispellable, through immunities; Feral Power's +2% per stack, 9 at most;
  - Turned: one aura holding the charm (max level 100) and the Glutton's shape (3857), not dispellable, no mechanic;
  - Void Bolt: a real 3 s interruptible cast whose damage its SpellScript sets (ignores caster modifiers, no crit);
  - Thundershock: the 2 s bar, the Nature resolve copy, the 1.5 s stun rider;
  - 4275 is bound to boss_archmage_arugal_rework with SmartAI off, HealthModifier 37.25 and immunity set 1972.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_shadowfang_keep_arugal.py
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
HEADER = MODULE_DIR / "ArugalLogic.h"
SCRIPT = MODULE_DIR / "boss_archmage_arugal_rework.cpp"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "shadowfang_keep"

SLICE = range(206060, 206085)
S10_SLICE = range(206085, 206090)
(CURSE, CURSE_HEROIC, FERAL, SHOCK_BAR, SHOCK, SHOCK_STUN, VOID_BOLT, ARUGALS_CURSE, PORT, TURNED, TURNED_BURST,
 WARD_ASHCROMBE, WARD_ADAMANT, WARD_RUNE, WARD_SMOKE, WARD_PULSE, MOON_BAR, MOON, MOONLIGHT, GLOW,
 TINT) = range(206060, 206081)
ASHCROMBE, ADAMANT, WARD_STALKER = 300513, 300514, 300515
ARUGAL = 4275

SCHOOL_DAMAGE, APPLY_AURA = 2, 6
AURA_MOD_STUN, AURA_MOD_CHARM, AURA_TRANSFORM = 12, 6, 56
AURA_MOD_DAMAGE_PERCENT_DONE, AURA_MOD_HEALING_DONE_PERCENT = 79, 136
ATTR0_DO_NOT_DISPLAY = 0x00000080
ATTR0_NO_IMMUNITIES = 0x20000000
ATTR2_CANT_CRIT = 0x20000000
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
UNIT_FLAG_NON_ATTACKABLE = 0x2
UNIT_FLAG_IMMUNE_TO_NPC = 0x200
UNIT_FLAG_NOT_SELECTABLE = 0x02000000
CREATURE_FLAG_EXTRA_NO_XP = 0x40
CREATURE_FLAG_EXTRA_TRIGGER = 0x80


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


class ArugalDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE or int(e["id"]) in S10_SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates
                         if ASHCROMBE <= int(e["entry"]) <= WARD_STALKER}
        cls.models = {int(e["CreatureID"]): e for e in reg.creature_template_models
                      if ASHCROMBE <= int(e["CreatureID"]) <= WARD_STALKER}
        cls.edits = [e for e in reg.creature_template_edits if int(e["entry"]) == ARUGAL]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(i for i in self.spells if i in SLICE)
        self.assertEqual(mine, list(range(CURSE, TINT + 1)))
        self.assertEqual(id_blocks.out_of_reservation("shadowfang_keep", {"spell": mine}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_ARUGAL_\w+\s*=\s*(\d+)", HEADER.read_text(encoding="utf-8"))}
        self.assertEqual(header_ids, set(mine))
        self.assertFalse(header_ids & set(S10_SLICE))

    def test_creatures_sit_in_the_slice_with_looks_and_scripts(self):
        self.assertEqual(sorted(self.creatures), [ASHCROMBE, ADAMANT, WARD_STALKER])
        self.assertEqual(id_blocks.out_of_reservation("shadowfang_keep", {"creature": sorted(self.creatures)}), [])
        self.assertEqual(self.models[ASHCROMBE]["CreatureDisplayID"], 2005)
        self.assertEqual(self.models[ADAMANT]["CreatureDisplayID"], 2006)
        self.assertEqual(self.models[WARD_STALKER]["CreatureDisplayID"], 11686)
        for entry in (ASHCROMBE, ADAMANT):
            prisoner = self.creatures[entry]
            self.assertEqual(prisoner["ScriptName"], "npc_sfk_lair_prisoner")
            self.assertEqual(prisoner["gossip_menu_id"], entry)
            self.assertEqual(prisoner["npcflag"], 1)
            self.assertTrue(prisoner["unit_flags"] & UNIT_FLAG_NON_ATTACKABLE, entry)
            self.assertTrue(prisoner["unit_flags"] & UNIT_FLAG_IMMUNE_TO_NPC, entry)
            self.assertEqual(prisoner["lootid"], 0)
            self.assertEqual(prisoner.get("difficulty_entry_1", 0), 0)
        self.assertEqual(self.creatures[ASHCROMBE]["faction"], 12)
        self.assertEqual(self.creatures[ADAMANT]["faction"], 68)
        self.assertIn('CreatureScript("npc_sfk_lair_prisoner")', self.cpp)
        stalker = self.creatures[WARD_STALKER]
        self.assertTrue(stalker["unit_flags"] & UNIT_FLAG_NOT_SELECTABLE)
        self.assertTrue(stalker["flags_extra"] & CREATURE_FLAG_EXTRA_NO_XP)
        self.assertTrue(stalker["flags_extra"] & CREATURE_FLAG_EXTRA_TRIGGER)
        self.assertEqual(stalker["ScriptName"], "")
        self.assertEqual(stalker.get("difficulty_entry_1", 0), 0)

    def test_spell_scripts_are_registered(self):
        self.assertIn((VOID_BOLT, "spell_sfk_arugal_void_bolt"), self.scripts)
        self.assertIn((SHOCK, "spell_boss_mechanics_resolve"), self.scripts)
        self.assertIn("RegisterSpellScript(spell_sfk_arugal_void_bolt)", self.cpp)
        own = {name for _, name in self.scripts if name != "spell_boss_mechanics_resolve"}
        self.assertEqual(own, {"spell_sfk_arugal_void_bolt"})

    def test_the_curse_is_a_meter_nothing_removes(self):
        for spell_id in (CURSE, CURSE_HEROIC):
            curse = self.spells[spell_id]
            self.assertEqual(_raw(curse, "CumulativeAura"), 100)
            self.assertEqual(curse["dispel"], 0)
            self.assertEqual(curse["mechanic"], 0)
            self.assertTrue(curse["attributes"] & ATTR0_NO_IMMUNITIES)
            self.assertEqual(curse["duration_ms"], -1)
            self.assertTrue(curse["raw_overrides"]["AuraDescription_Lang_enUS"].startswith("Turning into a worgen."))
        self.assertIn("Damage and healing done increased",
                      self.spells[CURSE_HEROIC]["raw_overrides"]["AuraDescription_Lang_enUS"])
        feral = self.spells[FERAL]
        self.assertEqual(_raw(feral, "CumulativeAura"), 9)
        self.assertTrue(feral["attributes"] & ATTR0_DO_NOT_DISPLAY)
        auras = {feral["effect1"]["apply_aura"], feral["effect2"]["apply_aura"]}
        self.assertEqual(auras, {AURA_MOD_DAMAGE_PERCENT_DONE, AURA_MOD_HEALING_DONE_PERCENT})
        self.assertEqual(feral["effect1"]["base_points"] + 1, 2)    # +2% per stack (BasePoints + DieSides 1)
        self.assertEqual(feral["effect2"]["base_points"] + 1, 2)

    def test_turned_is_one_aura_for_charm_and_shape(self):
        turned = self.spells[TURNED]
        self.assertEqual(turned["effect1"]["type"], APPLY_AURA)
        self.assertEqual(turned["effect1"]["apply_aura"], AURA_MOD_CHARM)
        self.assertGreaterEqual(turned["effect1"]["base_points"] + 1, 80)   # max target level
        self.assertEqual(turned["effect2"]["apply_aura"], AURA_TRANSFORM)
        self.assertEqual(turned["effect2"]["misc_value"], 3857)
        self.assertEqual(turned["dispel"], 0)
        self.assertEqual(turned["mechanic"], 0)
        self.assertEqual(turned["duration_ms"], -1)
        self.assertTrue(turned["attributes"] & ATTR0_NO_IMMUNITIES)
        self.assertIn("hostilePlayerAuras = { SPELL_ARUGAL_TURNED }", self.cpp)

    def test_void_bolt_is_a_real_interruptible_cast(self):
        bolt = self.spells[VOID_BOLT]
        self.assertEqual(bolt["cast_time_ms"], 3000)
        self.assertEqual(_raw(bolt, "InterruptFlags"), 15)
        self.assertEqual(_raw(bolt, "PreventionType"), 1)
        self.assertEqual(bolt["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertTrue(bolt["effect1"].get("_potency_excluded"))
        self.assertTrue(_raw(bolt, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertTrue(_raw(bolt, "AttributesEx2") & ATTR2_CANT_CRIT)
        self.assertEqual(_raw(bolt, "SpellVisualID_1"), 758)
        self.assertIn("SPELL_ARUGAL_VOID_BOLT, 2", self.cpp)               # the interrupt list

    def test_thundershock(self):
        self.assertEqual(self.spells[SHOCK_BAR]["cast_time_ms"], 2000)
        self.assertEqual(_raw(self.spells[SHOCK_BAR], "InterruptFlags"), 0)
        self.assertEqual(self.spells[SHOCK]["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertTrue(_raw(self.spells[SHOCK], "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        stun = self.spells[SHOCK_STUN]
        self.assertEqual(stun["effect1"]["apply_aura"], AURA_MOD_STUN)
        self.assertEqual(stun["duration_ms"], 1500)
        self.assertEqual(self.spells[PORT]["cast_time_ms"], 1000)
        self.assertEqual(self.spells[MOON_BAR]["cast_time_ms"], 3000)

    def test_looks(self):
        expected = {SHOCK: 145, ARUGALS_CURSE: 760, PORT: 3303, TURNED: 7597, TURNED_BURST: 7199,
                    WARD_ADAMANT: 12483, WARD_RUNE: 13069, WARD_SMOKE: 9554, WARD_PULSE: 186, MOON_BAR: 11567,
                    MOON: 11571, MOONLIGHT: 7990, GLOW: 11338, TINT: 760}
        for spell_id, visual in expected.items():
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), visual, spell_id)
        self.assertGreater(float((self.spells[WARD_ADAMANT]["raw_overrides"] or {}).get("Speed", 0)), 0.0)

    def test_arugal_is_bound(self):
        self.assertEqual(len(self.edits), 1)
        edit = self.edits[0]
        self.assertEqual(edit["ScriptName"], "boss_archmage_arugal_rework")
        self.assertEqual(edit["AIName"], "")
        self.assertEqual(edit["HealthModifier"], 37.25)
        self.assertEqual(edit["CreatureImmunitiesId"], 1972)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_archmage_arugal_rework,", self.cpp)


if __name__ == "__main__":
    unittest.main()
