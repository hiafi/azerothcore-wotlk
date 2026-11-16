"""
Blackrock Spire build WP-B13, The Beast: source/npcs/blackrock_spire/the_beast.py against its C++
(modules/mod-dungeon-bosses src/BlackrockSpire/BeastLogic.h, boss_the_beast_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in the Beast's slice (210490-210519) and BeastLogic.h names the same ids;
  - the Beast 10430 is bound (SmartAI off) at 220k on the level 62 warrior base, the stock DamageModifier, stun immune,
    INSTANCE_BIND; the Molten Blood stalker 300735 sits in the reservation, is a helper with no heroic template;
  - Heat and Molten Fury are +10% damage done a stack with no cap; the roar and Magma Split bars last the header's
    seconds and cannot be interrupted; Dread lasts 30 s with 3 stacks, Panic is a 2 s fear;
  - the hits are the resolve copies or the kit's percent spells of the right school and the header's percent;
    Immolate is a Magic dispel of the stock duration; the pool looks are V-2's rungs 4 to 10, one hidden lasting
    aura each;
  - the SQL rev writes the three boss emotes and touches nothing else.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_spire_beast.py
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
from source.npcs.blackrock_spire import _visuals as V  # noqa: E402

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockSpire"
HEADER = MODULE_DIR / "BeastLogic.h"
REWORK = MODULE_DIR / "BlackrockSpireRework.h"
SCRIPT = MODULE_DIR / "boss_the_beast_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_the_beast_blackrock_spire.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_spire"

SLICE = range(210490, 210520)
(HEAT, FURY, ROAR, DREAD, PANIC, SPLIT_BAR, SPLIT_OTHERS, SPLIT_TARGET, LAVA, ERUPTION, IMMOLATE,
 HEAT_FLASH) = range(210490, 210502)
POOL_LOOKS = range(210502, 210509)
BEAST = 10430
POOL = 300735

SCHOOL_FIRE, SCHOOL_PHYSICAL, SCHOOL_SHADOW = 4, 1, 5
SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT = 2, 6, 3
AURA_DUMMY, AURA_PERIODIC_DAMAGE, AURA_MOD_FEAR, AURA_MOD_DAMAGE_PERCENT_DONE = 4, 3, 7, 79
MECHANIC_FEAR = 5
DISPEL_MAGIC = 1
AURA_INTERRUPT_CHANGE_MAP = 0x00080000
RESOLVE = "spell_boss_mechanics_resolve"
REFLAT_DAMAGE = "spell_dungeon_refflat_damage"
REFLAT_PERIODIC = "spell_dungeon_refflat_periodic"
WARRIOR_62_BASE = 3237      # creature_classlevelstats level 62 class 1 basehp0
ATTR0_PASSIVE = 0x00000040
ATTR0_DO_NOT_DISPLAY = 0x00000080


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


def _header() -> str:
    return HEADER.read_text(encoding="utf-8")


def _header_value(name: str) -> float:
    match = re.search(rf"{name}\s*=\s*(-?[\d.]+)f?;", _header())
    assert match, name
    return float(match.group(1))


class BeastDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) == BEAST}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == POOL}
        cls.models = [e for e in reg.creature_template_models if int(e["CreatureID"]) == POOL]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(HEAT, POOL_LOOKS.stop)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_spire", {"spell": mine}), [])
        first = re.search(r"kSpellsBeast\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(first)
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_BE_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets} | set(POOL_LOOKS), set(mine))
        # The pool looks: the header names the first and the last; the seven between are 1 yd rungs.
        self.assertEqual(len(POOL_LOOKS), len(V.MAGMA_POOL_RADII))
        self.assertEqual(V.MAGMA_POOL_RADII, tuple(range(4, 11)))

    def test_the_beast_is_bound(self):
        boss = self.edits[BEAST]
        self.assertEqual(boss["ScriptName"], "boss_the_beast_rework")
        self.assertEqual(boss["AIName"], "")
        # 220k at 5 players (the build spec), within the S0 skeleton's 2 HP.
        self.assertLessEqual(abs(math.ceil(WARRIOR_62_BASE * boss["HealthModifier"]) - 220000), 2)
        # Stock 3.5, not the live 10 the retired mod-progression left (the wave 1 precedent).
        self.assertAlmostEqual(float(boss["DamageModifier"]), 3.5)
        self.assertEqual(boss["CreatureImmunitiesId"], 1972)
        self.assertEqual(boss["flags_extra"], 1)
        for name in ("boss_the_beast_rework", "npc_brs_molten_blood"):
            self.assertIn(f"RegisterDungeonReworkCreatureAI({name},", self.cpp)
        self.assertIn("RegisterSpellScript(spell_brs_beast_immolate)", self.cpp)
        self.assertIn('BrsTest::RegisterBoss("beast"', self.cpp)

    def test_the_pool_stalker(self):
        self.assertEqual(id_blocks.out_of_reservation("blackrock_spire", {"creature": [POOL]}), [])
        stalker = self.creatures[POOL]
        self.assertEqual(stalker["ScriptName"], "npc_brs_molten_blood")
        self.assertEqual(stalker["AIName"], "")
        # A prop: untargetable, unattackable, no loot, no XP, no melee, and no heroic template (handoff s7 #23).
        self.assertEqual(stalker["unit_flags"], 0x2 | 0x02000000)
        self.assertEqual(stalker["DamageModifier"], 0.0)
        self.assertEqual(stalker["lootid"], 0)
        self.assertEqual(stalker["flags_extra"], 0x40)
        self.assertEqual(stalker["difficulty_entry_1"], 0)
        self.assertEqual([m["CreatureDisplayID"] for m in self.models], [V.DISPLAY_INVISIBLE_STALKER])
        self.assertRegex(REWORK.read_text(encoding="utf-8"), rf"NPC_BRS_MOLTEN_BLOOD\s*=\s*{POOL},")

    def test_heat_and_fury(self):
        for spell_id, visual in ((HEAT, V.BE_HEAT), (FURY, V.BE_HEAT_ALT)):
            spell = self.spells[spell_id]
            effect = spell["effect1"]
            self.assertEqual(effect["apply_aura"], AURA_MOD_DAMAGE_PERCENT_DONE, spell_id)
            self.assertEqual(effect["base_points"], int(_header_value("kHeatDamagePct")), spell_id)
            self.assertEqual(effect["misc_value"], 127, spell_id)       # every school
            self.assertEqual(spell["duration_ms"], -1, spell_id)        # for the fight
            self.assertEqual(_raw(spell, "CumulativeAura"), 255, spell_id)      # no cap
            self.assertEqual(_raw(spell, "SpellVisualID_1"), visual, spell_id)
            self.assertFalse(spell["attributes"] & ATTR0_PASSIVE, spell_id)     # a passive aura is never sent
        self.assertEqual(int(_header_value("kHeatDamagePct")), int(_header_value("kFuryDamagePct")))
        flash = self.spells[HEAT_FLASH]
        self.assertEqual(flash["effect1"]["type"], DUMMY_EFFECT)
        self.assertEqual(_raw(flash, "SpellVisualID_1"), V.BE_HEAT_STACK_FLASH)

    def test_the_cast_bars(self):
        for spell_id, ms_name, visual in ((ROAR, "kRoarCastMs", V.BE_ROAR), (SPLIT_BAR, "kSplitCastMs",
                                                                              V.BE_MAGMA_SPLIT)):
            bar = self.spells[spell_id]
            self.assertEqual(bar["cast_time_ms"], int(_header_value(ms_name)), spell_id)
            self.assertEqual(bar["cast_time_ms"], 2000, spell_id)
            # Not interruptible: a kick must not look as if it stopped a mechanic the registry still lands.
            self.assertEqual(_raw(bar, "InterruptFlags"), 0, spell_id)
            self.assertEqual(_raw(bar, "PreventionType"), 0, spell_id)
            self.assertEqual(_raw(bar, "SpellVisualID_1"), visual, spell_id)
            self.assertEqual(bar["effect1"]["type"], DUMMY_EFFECT, spell_id)

    def test_dread_and_panic(self):
        dread = self.spells[DREAD]
        self.assertEqual(dread["duration_ms"], int(_header_value("kDreadMs")))
        self.assertEqual(dread["duration_ms"], 30000)
        self.assertEqual(_raw(dread, "CumulativeAura"), int(_header_value("kDreadMaxStacks")))
        self.assertEqual(dread["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(_raw(dread, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)
        self.assertEqual(_raw(dread, "SpellVisualID_1"), V.BE_ROAR)
        panic = self.spells[PANIC]
        self.assertEqual(panic["effect1"]["apply_aura"], AURA_MOD_FEAR)
        self.assertEqual(panic["mechanic"], MECHANIC_FEAR)
        self.assertEqual(panic["duration_ms"], int(_header_value("kPanicMs")))
        self.assertEqual(panic["duration_ms"], 2000)        # the shared limit on loss of control
        self.assertEqual(_raw(panic, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)
        # The header's panic thresholds sit inside the aura's stack limit.
        self.assertRegex(_header(), r"kDreadPanicAt\{\s*3,\s*2\s*\}")

    def test_the_hits(self):
        for spell_id in (SPLIT_OTHERS, SPLIT_TARGET):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertEqual(spell["school"], SCHOOL_FIRE, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
            self.assertEqual(_raw(spell, "SpellVisualID_1"), V.VG_FIRE_BLAST_IMPACT, spell_id)
        # The lava and the eruption: the kit's percent spell, the header's 10% in hundredths (shown and heroic).
        for spell_id, name in ((LAVA, "kPoolTickPct"), (ERUPTION, "kEruptionPct")):
            spell = self.spells[spell_id]
            hundredths = int(_header_value(name) * 100)
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertEqual(spell["school"], SCHOOL_FIRE, spell_id)
            self.assertEqual(spell["effect1"]["base_points"] + spell["effect1"]["die_sides"], hundredths, spell_id)
            self.assertEqual(_raw(spell, "EffectMiscValueB_1"), hundredths, spell_id)
            self.assertIn((spell_id, REFLAT_DAMAGE), self.scripts)
            # The resolve attribute set: ignores caster modifiers, always hits, cannot crit.
            self.assertTrue(_raw(spell, "AttributesEx3") & 0x20000000, spell_id)
            self.assertEqual(spell["effect1"]["implicit_target_a"], 6, spell_id)
        self.assertEqual(int(_header_value("kPoolTickPct")), 10)
        self.assertEqual(int(_header_value("kEruptionPct")), 10)

    def test_immolate(self):
        spell = self.spells[IMMOLATE]
        self.assertEqual(spell["effect1"]["apply_aura"], AURA_PERIODIC_DAMAGE)
        self.assertEqual(spell["effect1"]["amplitude"], 1000)
        self.assertEqual(spell["effect1"]["base_points"], int(_header_value("kImmolateTickPct") * 100))
        self.assertEqual(_raw(spell, "EffectMiscValueB_1"), 300)
        self.assertEqual(spell["dispel"], DISPEL_MAGIC)
        self.assertEqual(spell["school"], SCHOOL_FIRE)
        self.assertEqual(spell["duration_ms"], int(_header_value("kImmolateMs")))
        self.assertEqual(spell["duration_ms"], 21000)       # the stock Immolate's duration
        self.assertTrue(_raw(spell, "AttributesEx3") & 0x20000000)
        self.assertEqual(_raw(spell, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)
        self.assertIn((IMMOLATE, REFLAT_PERIODIC), self.scripts)
        self.assertIn((IMMOLATE, "spell_brs_beast_immolate"), self.scripts)

    def test_the_pool_looks(self):
        for rung, spell_id in zip(V.MAGMA_POOL_RADII, POOL_LOOKS):
            spell = self.spells[spell_id]
            self.assertEqual(_raw(spell, "SpellVisualID_1"), V.SV_MAGMA_POOL_STATE[rung], spell_id)
            # A hidden, lasting aura on the stalker (not passive: a passive aura is never sent to the client).
            self.assertEqual(spell["duration_ms"], -1)
            self.assertEqual(spell["effect1"]["apply_aura"], AURA_DUMMY)
            self.assertFalse(spell["attributes"] & ATTR0_PASSIVE)
            self.assertTrue(spell["attributes"] & ATTR0_DO_NOT_DISPLAY)
            # The header's rung -> spell mapping is spell_id = first look + rung - 4.
            self.assertEqual(spell_id, 210502 + rung - 4)

    def test_the_cpp_uses_the_declared_names(self):
        for name in ("SPELL_BE_HEAT", "SPELL_BE_MOLTEN_FURY", "SPELL_BE_ROAR", "SPELL_BE_DREAD", "SPELL_BE_PANIC",
                     "SPELL_BE_MAGMA_SPLIT_BAR", "SPELL_BE_MAGMA_SPLIT", "SPELL_BE_MAGMA_SPLIT_TARGET",
                     "SPELL_BE_MOLTEN_BLOOD", "SPELL_BE_ERUPTION", "SPELL_BE_IMMOLATE", "SPELL_BE_HEAT_FLASH"):
            self.assertIn(name, self.cpp, name)
        self.assertIn("PoolLookSpell(", self.cpp)
        # The registry carries the header's percents, never a literal.
        self.assertIn("kSplitOthersPct * mult", self.cpp)
        self.assertIn("kSplitTargetPct * mult", self.cpp)
        self.assertNotIn("\t", self.cpp)


class BeastSqlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.header = _header()

    def test_the_texts(self):
        for group in (0, 1, 2):
            self.assertRegex(self.sql, rf"\({BEAST}, {group}, 0, '[^\n]*', 41, 0, 100, ", group)      # boss emotes
        self.assertRegex(self.sql, rf"\({BEAST}, 0, 0, '%s rears back to roar!'")
        self.assertRegex(self.sql, rf"\({BEAST}, 1, 0, '%s''s blood boils!'")
        self.assertRegex(self.sql, rf"\({BEAST}, 2, 0, 'The lair floor erupts in magma!'")
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 10430 AND `GroupID` BETWEEN 0 AND 2;",
                      self.sql)
        groups = dict(re.findall(r"TEXT_(\w+)\s*=\s*(\d+),", self.header))
        self.assertEqual(sorted(int(v) for v in groups.values()), [0, 1, 2])

    def test_the_rev_leaves_the_stock_rows_alone(self):
        # He has no SmartAI to drop, and the rev never touches his loot, his spawn or the Elites' and Finkle's lines.
        self.assertNotIn("smart_scripts", self.sql)
        self.assertNotIn("creature_loot_template", self.sql)
        self.assertNotIn("UPDATE `creature`", self.sql)
        self.assertNotRegex(self.sql, r"`CreatureID` = (10317|10776)")


if __name__ == "__main__":
    unittest.main()
