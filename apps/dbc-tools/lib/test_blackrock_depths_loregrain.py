"""
Blackrock Depths build WP-D7, Pyromancer Loregrain: source/npcs/blackrock_depths/loregrain.py against its C++
(modules/mod-dungeon-bosses src/BlackrockDepths/LoregrainLogic.h, boss_pyromancer_loregrain_rework.cpp) and its SQL
rev.

Checks:
  - the spells sit in the slice (211020-211049), LoregrainLogic.h names the same ids, nothing else is declared there;
  - Loregrain is bound (SmartAI off, 130k at 5 players, immunity 1972, INSTANCE_BIND);
  - the Defiling Totem is a 4k rooted totem with its heroic entry and its script; the C++ registers that script;
  - the four hits are resolve copies (Fire), named by the registry calls;
  - the cast bars are not kicks, not Fire, and last the header's warnings; Molten Blast is a 2 s Fire kick;
  - Molten Blast, Flame Shock and Searing Bolt carry the header's percents for the kit's percent scripts;
  - Fire Ward is a Magic any-school absorb, Fury a 100-stack meter, the looks are V-1's;
  - the descriptor names the kill order, the kick, the purge and the dispel; the tide's tags are the G1 drill's;
  - the SQL rev writes the texts as the header numbers them and removes the two Emissaries and the 15288 aura.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_loregrain.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockDepths"
HEADER = MODULE_DIR / "LoregrainLogic.h"
REWORK = MODULE_DIR / "BlackrockDepthsRework.h"
SCRIPT = MODULE_DIR / "boss_pyromancer_loregrain_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_loregrain_blackrock_depths.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_depths"

SLICE = range(211020, 211050)
(TIDE_HIT, TIDE_CAST, WRATH_CAST_N, WRATH_CAST_H, WRATH_HIT, WARD_REPEL, DEFILING_PRESENCE, SPLASH_LOB, SPLASH_HIT,
 PATCH_HIT, PATCH_LOOK, FURY, FIRE_WARD, MOLTEN_BLAST, FLAME_SHOCK, SEARING_BOLT) = range(211020, 211036)
LOREGRAIN, TOTEM, SPIRIT = 9024, 300792, 9542
HEALTH_AT_5 = 130_000
MAGE_52_BASE, WARRIOR_52_BASE = 1660, 2371
TOTEM_HEALTH = 4_000
TOTEM_HEROIC_ENTRY = 310403         # STAGE-H-REPORT section 3

SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT = 2, 6, 3
AURA_DUMMY, AURA_PERIODIC_DAMAGE, AURA_SCHOOL_ABSORB = 4, 3, 69
SCHOOL_PHYSICAL, SCHOOL_FIRE = 1, 4
DISPEL_MAGIC = 1
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT, REFFLAT_PERIODIC = "spell_dungeon_refflat_damage", "spell_dungeon_refflat_periodic"
IMMUNITY_BOSS_STUN = 1972
INSTANCE_BIND = 0x1
IGNORE_CASTER_MODIFIERS = 0x20000000
SV_LAVA_POOL_4, SV_FIRE_TIDE, SV_LAVA_BURST, SV_FURY, SV_FIRE_WARD, SV_WRATH = 90606, 13372, 11565, 141, 6764, 143


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


class LoregrainDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) == LOREGRAIN}
        cls.templates = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == TOTEM}
        cls.models = [e for e in reg.creature_template_models if int(e["CreatureID"]) == TOTEM]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(TIDE_HIT, SEARING_BOLT + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"spell": mine}), [])
        first = re.search(r"kSpellsLoregrain\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(first)
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_LG_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))

    def test_loregrain_is_bound(self):
        boss = self.edits[LOREGRAIN]
        self.assertEqual(boss["ScriptName"], "boss_pyromancer_loregrain_rework")
        self.assertEqual(boss["AIName"], "")
        self.assertEqual(boss["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
        self.assertEqual(boss["flags_extra"] & INSTANCE_BIND, INSTANCE_BIND)
        self.assertAlmostEqual(float(boss["DamageModifier"]), 3.5)
        self.assertLessEqual(abs(math.ceil(MAGE_52_BASE * boss["HealthModifier"]) - HEALTH_AT_5), 2)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_pyromancer_loregrain_rework,", self.cpp)

    def test_the_defiling_totem(self):
        totem = self.templates[TOTEM]
        self.assertEqual(totem["name"], "Defiling Totem")
        self.assertEqual(totem["ScriptName"], "npc_brd_defiling_totem")
        self.assertEqual(totem["difficulty_entry_1"], TOTEM_HEROIC_ENTRY)
        self.assertEqual((totem["minlevel"], totem["maxlevel"], totem["unit_class"]), (52, 52, 1))
        self.assertLessEqual(abs(math.ceil(WARRIOR_52_BASE * totem["HealthModifier"]) - TOTEM_HEALTH), 2)
        self.assertEqual(float(totem["DamageModifier"]), 0.0)
        self.assertEqual(totem["faction"], 54)
        self.assertEqual(totem["type"], 11)
        self.assertEqual(totem["lootid"], 0)
        self.assertEqual(totem["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
        self.assertEqual([int(m["CreatureDisplayID"]) for m in self.models], [4589])
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_brd_defiling_totem,", self.cpp)
        # the kill order names it
        self.assertIn("TargetEntry(NPC_BRD_DEFILING_TOTEM, 2, BossMechanics::Who::Dps)", self.cpp)

    def test_the_hits_are_resolve_copies(self):
        for spell_id, name in ((TIDE_HIT, "SPELL_LG_TIDE_HIT"), (WRATH_HIT, "SPELL_LG_WRATH_HIT"),
                               (SPLASH_HIT, "SPELL_LG_SPLASH_HIT"), (PATCH_HIT, "SPELL_LG_PATCH_HIT")):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
            self.assertEqual(spell["school"], SCHOOL_FIRE, spell_id)
            self.assertIn(name, self.cpp)
        self.assertIn(".Spell(SPELL_LG_SPLASH_HIT)", self.cpp)
        self.assertIn(".Spell(SPELL_LG_PATCH_HIT)", self.cpp)
        self.assertIn(".Spell(wrath ? SPELL_LG_WRATH_HIT : SPELL_LG_TIDE_HIT)", self.cpp)

    def test_the_cast_bars(self):
        warn = int(_header_value("kTideWarnMs"))
        wrath_n, wrath_h = _header_nh("kWrathWarnMs")
        for bar, ms in ((TIDE_CAST, warn), (WRATH_CAST_N, int(wrath_n)), (WRATH_CAST_H, int(wrath_h))):
            spell = self.spells[bar]
            self.assertEqual(spell["cast_time_ms"], ms, bar)
            self.assertEqual(_raw(spell, "InterruptFlags"), 0, bar)
            self.assertEqual(_raw(spell, "PreventionType"), 0, bar)
            # never the kick's school: a Molten Blast kick locks Fire
            self.assertNotEqual(spell["school"], self.spells[MOLTEN_BLAST]["school"], bar)
        self.assertEqual(_raw(self.spells[TIDE_CAST], "SpellVisualID_1"), SV_FIRE_TIDE)
        self.assertEqual(_raw(self.spells[WRATH_CAST_N], "SpellVisualID_1"), SV_WRATH)
        self.assertEqual((int(wrath_n), int(wrath_h)), (4000, 2000))    # section 7 #21

    def test_molten_blast_is_a_two_second_fire_kick(self):
        blast = self.spells[MOLTEN_BLAST]
        self.assertEqual(blast["cast_time_ms"], int(_header_value("kMoltenBlastCastMs")))
        self.assertEqual(blast["school"], SCHOOL_FIRE)
        self.assertEqual(_raw(blast, "InterruptFlags"), 15)
        self.assertEqual(_raw(blast, "PreventionType"), 1)
        self.assertEqual(blast["range_yards"], _header_value("kMoltenBlastRangeYd"))
        self.assertIn("d.interrupts.emplace_back(NPC_LOREGRAIN, SPELL_LG_MOLTEN_BLAST", self.cpp)

    def test_the_percent_spells_carry_the_header(self):
        cases = ((MOLTEN_BLAST, 1, "kMoltenBlastPct"), (FLAME_SHOCK, 1, "kFlameShockPct"),
                 (SEARING_BOLT, 1, "kSearingBoltPct"))
        for spell_id, index, name in cases:
            spell = self.spells[spell_id]
            effect = spell[f"effect{index}"]
            normal, heroic = _header_nh(name)
            self.assertEqual(effect["type"], SCHOOL_DAMAGE, spell_id)
            self.assertEqual(effect["base_points"] + 1, round(normal * 100), spell_id)
            self.assertEqual(effect["die_sides"], 1, spell_id)
            self.assertEqual(_raw(spell, f"EffectMiscValueB_{index}"), round(heroic * 100), spell_id)
            self.assertTrue(_raw(spell, "AttributesEx3") & IGNORE_CASTER_MODIFIERS, spell_id)
            self.assertIn((spell_id, REFFLAT), self.scripts)
        shock = self.spells[FLAME_SHOCK]
        tick = shock["effect2"]
        normal, heroic = _header_nh("kFlameShockTickPct")
        self.assertEqual(tick["apply_aura"], AURA_PERIODIC_DAMAGE)
        self.assertEqual(tick["base_points"], round(normal * 100))
        self.assertEqual(_raw(shock, "EffectMiscValueB_2"), round(heroic * 100))
        self.assertEqual(tick["amplitude"], int(_header_value("kFlameShockTickMs")))
        self.assertEqual(shock["duration_ms"], int(_header_value("kFlameShockMs")))
        self.assertEqual(shock["dispel"], DISPEL_MAGIC)
        self.assertIn((FLAME_SHOCK, REFFLAT_PERIODIC), self.scripts)
        self.assertIn("d.dispels.emplace_back(SPELL_LG_FLAME_SHOCK", self.cpp)

    def test_fire_ward_fury_and_the_looks(self):
        ward = self.spells[FIRE_WARD]
        self.assertEqual(ward["effect1"]["apply_aura"], AURA_SCHOOL_ABSORB)
        self.assertEqual(ward["effect1"]["misc_value"], 127)
        self.assertEqual(ward["effect1"]["base_points"], 0)
        self.assertEqual(ward["effect1"]["die_sides"], 0)       # the script's amount, exact
        self.assertEqual(ward["dispel"], DISPEL_MAGIC)
        self.assertEqual(ward["duration_ms"], int(_header_value("kFireWardMs")))
        self.assertEqual(_raw(ward, "SpellVisualID_1"), SV_FIRE_WARD)
        self.assertIn("d.purges.emplace_back(NPC_LOREGRAIN, SPELL_LG_FIRE_WARD", self.cpp)
        self.assertIn("CastCustomSpell(me, SPELL_LG_FIRE_WARD, &absorb", self.cpp)

        fury = self.spells[FURY]
        self.assertEqual(fury["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(_raw(fury, "CumulativeAura"), int(_header_value("kFuryMax")))
        self.assertEqual(fury["duration_ms"], -1)
        self.assertEqual(fury["dispel"], 0)
        self.assertEqual(_raw(fury, "SpellVisualID_1"), SV_FURY)

        self.assertEqual(_raw(self.spells[PATCH_LOOK], "SpellVisualID_1"), SV_LAVA_POOL_4)
        self.assertEqual(_raw(self.spells[SPLASH_LOB], "SpellVisualID_1"), SV_LAVA_BURST)
        self.assertEqual(self.spells[PATCH_LOOK]["duration_ms"], -1)
        for look in (WARD_REPEL, SPLASH_LOB, DEFILING_PRESENCE, PATCH_LOOK):
            effect = self.spells[look]["effect1"]
            self.assertIn(effect["type"], (DUMMY_EFFECT, APPLY_AURA), look)
            if effect["type"] == APPLY_AURA:
                self.assertEqual(effect["apply_aura"], AURA_DUMMY, look)

    def test_the_tide_registers_the_g1_ward_row(self):
        tags = dict(re.findall(r"\b(TAG_LG_\w+)\s*=\s*(\d+),", _header()))
        self.assertEqual((tags["TAG_LG_WARD"], tags["TAG_LG_TIDE"]), ("11", "12"))    # G1 Stack/11, Zone/12
        self.assertIn("Mechanic::Stack(me, at, radius, Ms(warn))", self.cpp)
        self.assertIn("Mechanic::Donut(me, at, radius, kTideOuterYd, Ms(warn))", self.cpp)
        self.assertEqual(_header_value("kTideOuterYd"), 45.0)
        self.assertEqual(_header_nh("kPatchPct"), (4.0, 6.0))    # gap 20 default


class LoregrainSqlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8")

    def _rows(self, entry: int) -> dict[int, int]:
        rows = re.findall(rf"\({entry}, (\d+), 0, '(?:[^']|'')*', (\d+),", self.sql)
        return {int(group): int(kind) for group, kind in rows}

    def test_the_texts(self):
        header = _header()
        groups = {name: int(value) for name, value in re.findall(r"\b((?:YELL|EMOTE|SAY)_\w+)\s*=\s*(\d+),", header)}
        lg = self._rows(LOREGRAIN)
        self.assertEqual(lg, {groups["YELL_LG_PULL"]: 14, groups["YELL_LG_TIDE"]: 14, groups["YELL_LG_WRATH"]: 14,
                              groups["YELL_LG_DEATH"]: 14, groups["EMOTE_LG_WARD_MOVE"]: 41})
        self.assertEqual(self._rows(SPIRIT), {groups["SAY_FRANCLORN_THANKS"]: 12})
        # D10's copy line (group 1) is never touched
        self.assertIn(f"DELETE FROM `creature_text` WHERE `CreatureID` = {SPIRIT} AND `GroupID` = 0;", self.sql)

    def test_the_emissaries_and_the_addon_aura(self):
        self.assertIn("DELETE FROM `creature` WHERE `id` = 8913 AND `guid` IN (47772, 47773);", self.sql)
        self.assertIn("DELETE FROM `creature_addon` WHERE `guid` IN (47772, 47773);", self.sql)
        self.assertRegex(self.sql, r"UPDATE `creature_addon` SET `auras` = (NULL|'') WHERE `guid` = 47771;")
        self.assertNotIn("smart_scripts", self.sql)     # the S0 rev drops his rows


if __name__ == "__main__":
    unittest.main()
