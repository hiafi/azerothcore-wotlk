"""
Scholomance build WP-S8, The Ravenian and Master Corvane: source/npcs/scholomance/the_ravenian.py against its C++
(modules/mod-dungeon-bosses src/Scholomance/RavenianLogic.h, boss_the_ravenian_rework.cpp).

Checks:
  - the spells sit in the Ravenian's slice (206270-206289) and RavenianLogic.h names the same ids;
  - the orders are 2 s kickable casts, the transition Mend cannot be stopped, the phase 2 Mend can; both heal through
    their script; the leash is a channel his casts do not break;
  - the order hits are resolve copies bound to spell_boss_mechanics_resolve, with the stock moves' looks;
  - Driven and Bereaved stack +10% damage, uncapped; Unbound and the bolt run their scripts, which the C++ registers;
  - Sundering Cleave is the stock 25174 on one target;
  - Master Corvane 300542: mage, 50k, stun immune 1972, unselectable at spawn, his script, his heroic entry, display
    23277; 10507 is bound to boss_the_ravenian_rework with SmartAI off, HealthModifier 52.425, DamageModifier 3.5;
  - the examiner script names in the C++ match RavenianLogic.h and are registered only with wave C.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scholomance_ravenian.py
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
HEADER = MODULE_DIR / "RavenianLogic.h"
SCRIPT = MODULE_DIR / "boss_the_ravenian_rework.cpp"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "scholomance"

SLICE = range(206270, 206290)
(LEASH, ORDER_TRAMPLE, ORDER_SWEEP, ORDER_SMASH, TRAMPLE, SWEEP, SMASH, MEND_TRANSITION, MEND, TELEPORT,
 UNBOUND_STRIKE, UNBOUND, DRIVEN, SHADOW_BOLT, BEREAVED, SUNDERING_CLEAVE) = range(206270, 206286)
RAVENIAN = 10507
CORVANE = 300542
CORVANE_HEROIC = 310118

SCHOOL_DAMAGE, DUMMY, APPLY_AURA, HEAL, WEAPON_PERCENT_DAMAGE = 2, 3, 6, 10, 31
AURA_DUMMY, AURA_MOD_RESISTANCE, AURA_MOD_DAMAGE_PERCENT_DONE = 4, 22, 79
ATTR1_IS_CHANNELED = 0x4
ATTR5_ALLOW_ACTION_DURING_CHANNEL = 0x1
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
RESOLVE = "spell_boss_mechanics_resolve"
MEND_SCRIPT = "spell_scholo_ravenian_mend"
BOLT_SCRIPT = "spell_scholo_corvane_shadow_bolt"
UNBOUND_SCRIPT = "spell_scholo_ravenian_unbound_strike"


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


class RavenianDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = [e for e in reg.creature_template_edits if int(e["entry"]) == RAVENIAN]
        cls.corvane = [e for e in reg.creature_templates if int(e["entry"]) == CORVANE]
        cls.models = [e for e in reg.creature_template_models if int(e["CreatureID"]) == CORVANE]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(LEASH, SUNDERING_CLEAVE + 1)))
        self.assertEqual(id_blocks.out_of_reservation("scholomance", {"spell": mine, "creature": [CORVANE]}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_RV_\w+\s*=\s*(\d+)", self.header)}
        self.assertEqual(header_ids, set(mine))
        for stock in (15550, 25174, 10101, 20691):
            self.assertNotIn(stock, self.spells)

    def test_the_leash_is_a_channel_his_casts_do_not_break(self):
        leash = self.spells[LEASH]
        self.assertEqual(leash["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertTrue(_raw(leash, "AttributesEx") & ATTR1_IS_CHANNELED)
        self.assertTrue(_raw(leash, "AttributesEx5") & ATTR5_ALLOW_ACTION_DURING_CHANNEL)
        self.assertEqual(_raw(leash, "InterruptFlags"), 0)
        self.assertEqual(_raw(leash, "ChannelInterruptFlags"), 0)
        self.assertEqual(_raw(leash, "SpellVisualID_1"), 9843)
        self.assertIn("CastSpell(rav, SPELL_RV_LEASH, true)", self.cpp)

    def test_orders_are_two_second_kickable_casts(self):
        for spell_id in (ORDER_TRAMPLE, ORDER_SWEEP, ORDER_SMASH):
            order = self.spells[spell_id]
            self.assertEqual(order["cast_time_ms"], _header_int("kOrderCastMs"))
            self.assertEqual(order["effect1"]["type"], DUMMY)
            self.assertEqual(_raw(order, "InterruptFlags"), 15)
            self.assertEqual(_raw(order, "PreventionType"), 1)
        self.assertTrue(self.spells[ORDER_TRAMPLE]["name"].endswith("Trample"))
        self.assertTrue(self.spells[ORDER_SWEEP]["name"].endswith("Sweep"))
        self.assertTrue(self.spells[ORDER_SMASH]["name"].endswith("Smash"))

    def test_order_hits_are_resolve_copies_with_the_stock_looks(self):
        looks = {TRAMPLE: 672, SWEEP: 219, SMASH: 2069}
        for spell_id, visual in looks.items():
            hit = self.spells[spell_id]
            self.assertEqual(hit["effect1"]["type"], SCHOOL_DAMAGE)
            self.assertTrue(_raw(hit, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
            self.assertIn((spell_id, RESOLVE), self.scripts)
            self.assertEqual(_raw(hit, "SpellVisualID_1"), visual)
        self.assertIn("spec.spellId = SPELL_RV_TRAMPLE", self.cpp)
        self.assertIn("Spell(SPELL_RV_SWEEP)", self.cpp)
        self.assertIn("Spell(SPELL_RV_SMASH).Weakened()", self.cpp)

    def test_mend_construct(self):
        transition = self.spells[MEND_TRANSITION]
        mend = self.spells[MEND]
        self.assertEqual(transition["cast_time_ms"], _header_int("kTransitionCastMs"))
        self.assertEqual(mend["cast_time_ms"], _header_int("kMendCastMs"))
        # The transition always lands (out of reach, no interrupt flags); phase 2's is the must-kick.
        self.assertEqual(_raw(transition, "InterruptFlags"), 0)
        self.assertEqual(_raw(transition, "PreventionType"), 0)
        self.assertEqual(_raw(mend, "InterruptFlags"), 15)
        self.assertEqual(_raw(mend, "PreventionType"), 1)
        for spell_id in (MEND_TRANSITION, MEND):
            self.assertEqual(self.spells[spell_id]["effect1"]["type"], HEAL)
            self.assertIn((spell_id, MEND_SCRIPT), self.scripts)
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), 27)
        self.assertIn(f"RegisterSpellScript({MEND_SCRIPT})", self.cpp)
        self.assertIn("d.interrupts.emplace_back(corvane, SPELL_RV_MEND, 3, Milliseconds(kMendEveryMs))", self.cpp)

    def test_stacks_unbound_and_the_bolt(self):
        for spell_id in (DRIVEN, BEREAVED):
            s = self.spells[spell_id]
            self.assertEqual(s["effect1"]["apply_aura"], AURA_MOD_DAMAGE_PERCENT_DONE)
            self.assertEqual(s["effect1"]["base_points"], 10)
            self.assertEqual(_raw(s, "CumulativeAura"), 255)
            self.assertEqual(s["duration_ms"], -1)
        self.assertEqual(_raw(self.spells[BEREAVED], "SpellVisualID_1"), 47)
        self.assertEqual(self.spells[UNBOUND_STRIKE]["effect1"]["type"], DUMMY)
        self.assertIn((UNBOUND_STRIKE, UNBOUND_SCRIPT), self.scripts)
        self.assertEqual(self.spells[UNBOUND]["duration_ms"], _header_int("kUnboundStandMs"))
        bolt = self.spells[SHADOW_BOLT]
        self.assertEqual(bolt["cast_time_ms"], _header_int("kShadowBoltCastMs"))
        self.assertEqual(bolt["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertTrue(_raw(bolt, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertIn((SHADOW_BOLT, BOLT_SCRIPT), self.scripts)
        for script in (UNBOUND_SCRIPT, BOLT_SCRIPT):
            self.assertIn(f"RegisterSpellScript({script})", self.cpp)
        own = {name for _, name in self.scripts if name != RESOLVE}
        self.assertEqual(own, {MEND_SCRIPT, BOLT_SCRIPT, UNBOUND_SCRIPT})

    def test_sundering_cleave_on_one_target(self):
        cleave = self.spells[SUNDERING_CLEAVE]
        self.assertEqual(cleave["effect1"]["type"], WEAPON_PERCENT_DAMAGE)
        self.assertEqual(cleave["effect2"]["apply_aura"], AURA_MOD_RESISTANCE)
        self.assertEqual(cleave["effect2"]["base_points"], -240)
        self.assertEqual(cleave["duration_ms"], 30000)
        for effect in ("effect1", "effect2"):
            self.assertEqual(int(cleave[effect].get("chain_targets", 0) or 0), 0)

    def test_corvane(self):
        self.assertEqual(len(self.corvane), 1)
        row = self.corvane[0]
        self.assertEqual(row["unit_class"], 8)
        self.assertEqual(row["CreatureImmunitiesId"], 1972)
        self.assertEqual(row["unit_flags"], 0x02000002)
        self.assertEqual(row["ScriptName"], "npc_sc_master_corvane")
        self.assertEqual(row["difficulty_entry_1"], CORVANE_HEROIC)
        self.assertEqual(row["lootid"], 0)
        # 50,000 on the level 60 mage base 2,136 (creature_classlevelstats, the health rounds up).
        self.assertEqual(-(-2136 * row["HealthModifier"] // 1), 50000)
        self.assertEqual([int(m["CreatureDisplayID"]) for m in self.models], [23277])
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_sc_master_corvane", self.cpp)

    def test_ravenian_is_bound(self):
        self.assertEqual(len(self.edits), 1)
        edit = self.edits[0]
        self.assertEqual(edit["ScriptName"], "boss_the_ravenian_rework")
        self.assertEqual(edit["AIName"], "")
        self.assertEqual(edit["HealthModifier"], 52.425)
        self.assertEqual(edit["DamageModifier"], 3.5)
        self.assertEqual(edit["CreatureImmunitiesId"], 1972)

    def test_examiners_are_wave_c(self):
        for name in ("kExaminerRavenianScriptName", "kExaminerCorvaneScriptName"):
            match = re.search(rf'{name}\[\]\s*=\s*"(\w+)"', self.header)
            self.assertTrue(match, name)
            self.assertIn(f"struct {match.group(1)} :", self.cpp)
        wave_c = self.cpp.index("if (kWaveCBound)")
        self.assertGreater(self.cpp.index("RegisterDungeonReworkCreatureAI(npc_sc_examiner_ravenian"), wave_c)
        self.assertGreater(self.cpp.index("RegisterDungeonReworkCreatureAI(npc_sc_examiner_corvane"), wave_c)
        self.assertIn("kExaminerRavenianHealth = 60000", self.header)
        self.assertIn("kExaminerCorvaneHealth = 20000", self.header)


if __name__ == "__main__":
    unittest.main()
