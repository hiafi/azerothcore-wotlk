"""
Blackrock Depths build WP-D3, Houndmaster Grebmar: source/npcs/blackrock_depths/grebmar.py against its C++
(modules/mod-dungeon-bosses src/BlackrockDepths/GrebmarLogic.h, boss_houndmaster_grebmar_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in his slice (210780-210809) and GrebmarLogic.h names the same ids;
  - he is bound (SmartAI off, immunity 1972, INSTANCE_BIND), 95k at 5 players, DamageModifier 3.5;
  - the Kennel Hound 300781: its own template on the Bloodhound display, 5,000 health, its script, no stun immunity,
    WP-H's heroic lock line;
  - the three whistles are 2 s kicks, each in its own school; the leap's two hits are resolve copies;
  - Snatched, Lick Wounds (a kickable self channel), Frenzy (an Enrage), Rend and Pummel carry the header's numbers;
  - every look is a self visual on one of V-1's ids;
  - the SQL rev deletes the five Bloodhounds and writes his seven lines (the horn a boss emote).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_grebmar.py
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
HEADER = MODULE_DIR / "GrebmarLogic.h"
REWORK = MODULE_DIR / "BlackrockDepthsRework.h"
SCRIPT = MODULE_DIR / "boss_houndmaster_grebmar_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_grebmar_blackrock_depths.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_depths"
VISUALS = PACKAGE / "_visuals.py"

SLICE = range(210780, 210810)
(WHISTLE_SIC_EM, WHISTLE_FETCH, WHISTLE_HEEL, MARK, LANDING, LEAP, LEAP_LOOK, SNATCHED, RUNNER, LICK, FRENZY,
 FRENZY_FLASH, HORN, HORN_BURST, RELEASE, REND, PUMMEL) = range(210780, 210797)
GREBMAR, KENNEL_HOUND, KENNEL_HOUND_HEROIC = 9319, 300781, 310392
WARRIOR_52_BASE = 2371
HEALTH_AT_5, HOUND_HEALTH = 95_000, 5_000
BLOODHOUND_DISPLAY = 8180

SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT, INTERRUPT_CAST = 2, 6, 3, 68
AURA_DUMMY, AURA_PERIODIC_DAMAGE, AURA_OBS_MOD_HEALTH = 4, 3, 20
AURA_MOD_DAMAGE_PERCENT_DONE, AURA_MOD_DAMAGE_PERCENT_TAKEN = 79, 87
AURA_MOD_HEALING_DONE_PERCENT, AURA_MOD_MELEE_HASTE = 136, 138
SCHOOL_PHYSICAL, SCHOOL_NATURE, SCHOOL_ARCANE = 1, 8, 64
DISPEL_ENRAGE, MECHANIC_BLEED = 9, 15
ATTR1_IS_SELF_CHANNELED, CHANNEL_INTERRUPT_FLAG_INTERRUPT = 0x40, 0x08
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
RESOLVE = "spell_boss_mechanics_resolve"
IMMUNITY_BOSS_STUN = 1972
INSTANCE_BIND = 0x1
BLOODHOUND_GUIDS = (46271, 46273, 46281, 46297, 46298)


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


def _visual(name: str) -> int:
    text = VISUALS.read_text(encoding="utf-8")
    match = re.search(rf"^{name}\s*=\s*(\w+)", text, re.MULTILINE)
    assert match, name
    value = match.group(1)
    return int(value) if value.isdigit() else _visual(value)


class GrebmarDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) == GREBMAR}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == KENNEL_HOUND}
        cls.models = [e for e in reg.creature_template_models if int(e["CreatureID"]) == KENNEL_HOUND]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(WHISTLE_SIC_EM, PUMMEL + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"spell": mine}), [])
        first = re.search(r"kSpellsGrebmar\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(first)
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_GR_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))

    def test_grebmar_is_bound(self):
        boss = self.edits[GREBMAR]
        self.assertEqual(boss["ScriptName"], "boss_houndmaster_grebmar_rework")
        self.assertEqual(boss["AIName"], "")
        self.assertEqual(boss["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
        self.assertEqual(boss["flags_extra"] & INSTANCE_BIND, INSTANCE_BIND)
        self.assertLessEqual(abs(math.ceil(WARRIOR_52_BASE * boss["HealthModifier"]) - HEALTH_AT_5), 2)
        self.assertAlmostEqual(float(boss["DamageModifier"]), 3.5)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_houndmaster_grebmar_rework,", self.cpp)
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_brd_kennel_hound,", self.cpp)

    def test_the_kennel_hound(self):
        hound = self.creatures[KENNEL_HOUND]
        self.assertEqual(hound["name"], "Kennel Hound")
        self.assertEqual(hound["ScriptName"], "npc_brd_kennel_hound")
        self.assertEqual(hound["AIName"], "")
        self.assertEqual(int(hound["difficulty_entry_1"]), KENNEL_HOUND_HEROIC)
        self.assertEqual((int(hound["minlevel"]), int(hound["maxlevel"])), (52, 52))
        self.assertEqual(int(hound["unit_class"]), 1)
        self.assertEqual(math.ceil(WARRIOR_52_BASE * float(hound["HealthModifier"])), HOUND_HEALTH)
        self.assertEqual(HOUND_HEALTH, int(_header_nh("kHoundHealth")[0]))
        self.assertEqual(int(hound["CreatureImmunitiesId"]), 0)        # an AoE stun stops Lick Wounds
        self.assertEqual(int(hound["type"]), 3)                         # a demon, as the stock Bloodhound
        self.assertEqual(int(hound["faction"]), 54)
        self.assertEqual(int(hound["lootid"]), 0)
        self.assertTrue(int(hound["flags_extra"]) & 0x40)               # no XP
        self.assertEqual([int(m["CreatureDisplayID"]) for m in self.models], [BLOODHOUND_DISPLAY])
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"creature": [KENNEL_HOUND]}), [])

    def test_the_whistles_are_kicks_in_three_schools(self):
        schools = set()
        for spell_id in (WHISTLE_SIC_EM, WHISTLE_FETCH, WHISTLE_HEEL):
            spell = self.spells[spell_id]
            self.assertEqual(spell["cast_time_ms"], int(_header_value("kWhistleCastMs")), spell_id)
            self.assertEqual(_raw(spell, "InterruptFlags"), 15, spell_id)
            self.assertEqual(_raw(spell, "PreventionType"), 1, spell_id)
            self.assertEqual(spell["effect1"]["type"], DUMMY_EFFECT, spell_id)
            schools.add(spell["school"])
        self.assertEqual(schools, {SCHOOL_PHYSICAL, SCHOOL_NATURE, SCHOOL_ARCANE})
        self.assertIn("d.interrupts.emplace_back(NPC_GREBMAR, WhistleSpell(", self.cpp)

    def test_the_leap_hits_are_resolve_copies(self):
        for spell_id in (LANDING, LEAP):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
            self.assertEqual(spell["school"], SCHOOL_PHYSICAL, spell_id)
        self.assertIn(".Spell(SPELL_GR_SIC_EM_LANDING).Tag(TAG_GR_LEAP_LANDING)", self.cpp)
        self.assertIn(".Spell(SPELL_GR_SIC_EM_LEAP).Tag(TAG_GR_LEAP_LINE)", self.cpp)
        self.assertIn("ref.Rider(SPELL_GR_REND)", self.cpp)
        self.assertEqual(self.spells[MARK]["duration_ms"], int(_header_value("kWhistleCastMs"))
                         + int(_header_value("kLeapMs")))
        self.assertEqual(_raw(self.spells[MARK], "SpellVisualID_1"), _visual("SV_PURPLE_RING"))

    def test_snatched_and_the_runner(self):
        snatched = self.spells[SNATCHED]
        pct = int(_header_value("kSnatchedPct"))
        self.assertEqual(snatched["duration_ms"], int(_header_value("kSnatchedMs")))
        self.assertEqual(snatched["effect1"]["apply_aura"], AURA_MOD_DAMAGE_PERCENT_DONE)
        self.assertEqual(snatched["effect1"]["base_points"], -pct)
        self.assertEqual(snatched["effect2"]["apply_aura"], AURA_MOD_HEALING_DONE_PERCENT)
        self.assertEqual(snatched["effect2"]["base_points"], -pct)
        self.assertEqual(snatched["dispel"], 0)
        self.assertEqual(_raw(snatched, "SpellVisualID_1"), _visual("GR_SNATCHED"))
        runner = self.spells[RUNNER]
        self.assertGreater(runner["duration_ms"], int(_header_value("kFetchWindowMs")))
        self.assertEqual(_raw(runner, "SpellVisualID_1"), _visual("GR_FETCH_RUNNER_RING"))
        self.assertIn("Condition::HasAura(SPELL_GR_FETCH_RUNNER)", self.cpp)

    def test_crowd_controlled_hounds_ignore_orders(self):
        # R-1-A m2: Sic 'em, Fetch and Heel pick only hounds that are free of crowd control; a hound CC'd on its line
        # drops its leap.
        self.assertIn("return HoundObeys(me->IsAlive(), _state == State::Fight, CrowdControlled());", self.cpp)
        self.assertIn("if (!ai->IsRunner() && !ai->CrowdControlled())", self.cpp)
        self.assertIn("if (_state != State::Fight || CrowdControlled())", self.cpp)
        self.assertIn("DropLeap();", self.cpp)

    def test_lick_wounds_is_a_kickable_self_channel(self):
        lick = self.spells[LICK]
        self.assertEqual(lick["duration_ms"], int(_header_value("kLickMs")))
        self.assertEqual(lick["cast_time_ms"], 0)
        self.assertTrue(_raw(lick, "AttributesEx") & ATTR1_IS_SELF_CHANNELED)
        self.assertEqual(_raw(lick, "ChannelInterruptFlags"), CHANNEL_INTERRUPT_FLAG_INTERRUPT)
        self.assertEqual(_raw(lick, "PreventionType"), 1)
        self.assertEqual(lick["effect1"]["apply_aura"], AURA_OBS_MOD_HEALTH)
        self.assertEqual(lick["effect1"]["base_points"], int(_header_value("kLickHealPctPerSec")))
        self.assertEqual(lick["effect1"]["amplitude"], int(_header_value("kLickTickMs")))
        self.assertEqual(lick["effect2"]["apply_aura"], AURA_MOD_DAMAGE_PERCENT_TAKEN)
        self.assertEqual(lick["effect2"]["base_points"], int(_header_value("kLickDamageTakenPct")))
        self.assertEqual(_raw(lick, "SpellVisualID_1"), _visual("GR_LICK_WOUNDS"))
        self.assertIn("d.interrupts.emplace_back(NPC_BRD_KENNEL_HOUND, SPELL_GR_LICK_WOUNDS", self.cpp)
        self.assertIn("void OnChannelFinished(SpellInfo const* spell) override", self.cpp)

    def test_frenzy_is_an_enrage_on_the_purge_list(self):
        frenzy = self.spells[FRENZY]
        self.assertEqual(frenzy["dispel"], DISPEL_ENRAGE)
        self.assertEqual(frenzy["duration_ms"], int(_header_value("kFrenzyMs")))
        self.assertEqual(frenzy["effect1"]["apply_aura"], AURA_MOD_MELEE_HASTE)
        self.assertEqual(frenzy["effect1"]["base_points"], int(_header_value("kFrenzyHastePct")))
        self.assertEqual(_raw(frenzy, "CumulativeAura"), 0)                # does not stack
        self.assertEqual(_raw(frenzy, "SpellVisualID_1"), _visual("GR_FRENZY"))
        self.assertIn("d.purges.emplace_back(NPC_BRD_KENNEL_HOUND, SPELL_GR_FRENZY", self.cpp)
        self.assertIn("d.purges.emplace_back(NPC_GREBMAR, SPELL_STOCK_BLOODLUST", self.cpp)
        self.assertEqual(int(_header_value("SPELL_STOCK_BLOODLUST")), 21049)

    def test_rend_and_pummel(self):
        rend = self.spells[REND]
        normal, heroic = _header_nh("kRendPctPerTick")
        self.assertEqual(rend["effect1"]["apply_aura"], AURA_PERIODIC_DAMAGE)
        self.assertEqual(rend["effect1"]["base_points"], round(normal * 100))
        self.assertEqual(_raw(rend, "EffectMiscValueB_1"), round(heroic * 100))
        self.assertEqual(rend["effect1"]["amplitude"], int(_header_value("kRendTickMs")))
        self.assertEqual(rend["duration_ms"], int(_header_value("kRendMs")))
        self.assertEqual(rend["mechanic"], MECHANIC_BLEED)
        self.assertTrue(_raw(rend, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertIn((REND, "spell_dungeon_refflat_periodic"), self.scripts)
        pummel = self.spells[PUMMEL]
        normal, heroic = _header_nh("kPummelPct")
        effect = pummel["effect1"]
        self.assertEqual(effect["type"], SCHOOL_DAMAGE)
        self.assertEqual(effect["base_points"] + effect["die_sides"], round(normal * 100))
        self.assertEqual(_raw(pummel, "EffectMiscValueB_1"), round(heroic * 100))
        self.assertEqual(pummel["effect2"]["type"], INTERRUPT_CAST)
        self.assertEqual(pummel["duration_ms"], int(_header_value("kPummelLockoutMs")))
        self.assertTrue(_raw(pummel, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertIn((PUMMEL, "spell_dungeon_refflat_damage"), self.scripts)

    def test_the_looks_are_self_visuals_on_v1_ids(self):
        looks = {LEAP_LOOK: "GR_SIC_LEAP", FRENZY_FLASH: "GR_FRENZY_FLASH", HORN: "GR_KENNEL_HORN",
                 HORN_BURST: "GR_KENNEL_HORN_BURST", RELEASE: "GR_RELEASE_THE_HOUNDS"}
        for spell_id, name in looks.items():
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], DUMMY_EFFECT, spell_id)
            self.assertEqual(_raw(spell, "SpellVisualID_1"), _visual(name), spell_id)
        # never Horn of Winter's icy breath (V-1)
        self.assertNotEqual(_raw(self.spells[HORN], "SpellVisualID_1"), 12396)

    def test_the_sql_rev(self):
        sql = SQL.read_text(encoding="utf-8")
        for guid in BLOODHOUND_GUIDS:
            self.assertIn(str(guid), sql)
        self.assertIn("DELETE FROM `creature` WHERE `id` = 8921 AND `guid` IN (46271, 46273, 46281, 46297, 46298);",
                      sql)
        self.assertIn("DELETE FROM `creature_addon` WHERE `guid` IN (46271, 46273, 46281, 46297, 46298);", sql)
        # the three rim Bloodhounds on the horn doors and the Fetch exit (R-1-A m3, orchestrator ruling: delete)
        self.assertIn("DELETE FROM `creature` WHERE `id` = 8921 AND `guid` IN (46301, 46302, 46607);", sql)
        self.assertIn("DELETE FROM `creature_addon` WHERE `guid` IN (46301, 46302, 46607);", sql)
        for group in (0, 1, 2, 3, 4, 6):
            self.assertRegex(sql, rf"\({GREBMAR}, {group}, 0, '[^\n]*', 14,")
        self.assertRegex(sql, rf"\({GREBMAR}, 5, 0, '%s blows his kennel horn!', 41,")
        # WP-S0's rev owns the SmartAI delete of 9319; nothing here inserts a spawn or SmartAI row (rule 14)
        self.assertNotIn("`smart_scripts`", sql)
        self.assertNotIn("INSERT INTO `creature` ", sql)


if __name__ == "__main__":
    unittest.main()
