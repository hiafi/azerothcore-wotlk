"""
Blackrock Spire build WP-B12, Warchief Rend Blackhand and Gyth: source/npcs/blackrock_spire/rend_gyth.py against its C++
(modules/mod-dungeon-bosses src/BlackrockSpire/RendGythLogic.h, boss_rend_blackhand_rework.cpp, boss_gyth_rework.cpp)
and its SQL rev.

Checks:
  - the spells sit in the slice (210430-210489) and RendGythLogic.h names the same ids;
  - Rend 10429 and Gyth 10339 are bound (SmartAI off, immunity 1972, INSTANCE_BIND) at 160k / 140k at 5 players; the
    arena adds 10442 / 10447 / 10742 sit at the build spec's 4,000 / 15,000 / 9,000;
  - the kit creatures: the Nefarius copy (never attackable but able to hit players), the Banner (15,000, its heroic
    entry, the battle standard look), the frost wall (untargetable, the ice wall at 0.5); every ScriptName is
    registered in C++ behind the wave switch;
  - the hits are resolve copies of the right school; the percent spells carry the header's percents; the bars match
    the header and are not interruptible; Frozen is a 2 s stun; the pools are 6 yd dynamic objects (20 s / 25 s) with
    V-2's shadow quad; the swap debuffs fall off before the next swap (the user ruling);
  - the SQL rev rebinds spawn 137967 only, copies 10162's lines 0-11 and writes the new ones (boss emotes 41 at map
    range), and adds the Handler's Mend Dragon on Gyth.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_spire_rend_gyth.py
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
HEADER = MODULE_DIR / "RendGythLogic.h"
REND_CPP = MODULE_DIR / "boss_rend_blackhand_rework.cpp"
GYTH_CPP = MODULE_DIR / "boss_gyth_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_rend_gyth_blackrock_spire.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_spire"

SLICE = range(210430, 210490)
(MARK, BREATH, BREATH_LOOK, BREATH_BAR, SWEEP, FROZEN, FREEZING_BREATH, SHADOWFLAME, POOL_BURN, POOL, POOL_H, BITE,
 BITE_H, HUNTING, THUMBS, CRASH, WHIRL_BAR, WHIRL, WHIRL_LOOK, BANNER_BUFF, WOUNDS, IMPATIENT, BORED) = range(
    210430, 210453)
GYTH, REND, WHELP, DRAGONSPAWN, HANDLER = 10339, 10429, 10442, 10447, 10742
NEFARIUS, BANNER, WALL = 300732, 300733, 300734
WARRIOR_62_BASE, WARRIOR_60_BASE, PALADIN_58_BASE = 3237, 3052, 2297

SCHOOL_DAMAGE, APPLY_AURA, PERSISTENT_AREA_AURA = 2, 6, 27
AURA_DUMMY, AURA_MOD_STUN, AURA_MOD_HEALING_PCT = 4, 12, 118
SCHOOL_PHYSICAL, SCHOOL_FIRE, SCHOOL_FROST, SCHOOL_SHADOW = 1, 4, 16, 32   # school masks
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT = "spell_dungeon_refflat_damage"
IMMUNITY_BOSS_STUN = 1972
INSTANCE_BIND = 0x1
UNIT_FLAG_NON_ATTACKABLE, UNIT_FLAG_IMMUNE_TO_PC, UNIT_FLAG_NOT_SELECTABLE = 0x2, 0x100, 0x02000000
SV_POOL, SV_SKULL, DISPLAY_ICE_WALL, DISPLAY_BATTLE_STANDARD = 90604, 90506, 90740, 14542


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


def _raw(spell: dict, column: str) -> float:
    return float((spell.get("raw_overrides") or {}).get(column, 0) or 0)


def _header() -> str:
    return HEADER.read_text(encoding="utf-8")


def _header_value(name: str) -> float:
    match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f?;", _header())
    assert match, name
    return float(match.group(1))


class RendGythDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {}
        for e in reg.creature_template_edits:
            if int(e["entry"]) in (GYTH, REND, WHELP, DRAGONSPAWN, HANDLER):
                cls.edits.setdefault(int(e["entry"]), {}).update(e)
        cls.templates = {int(r["entry"]): r for r in reg.creature_templates if int(r["entry"]) in (NEFARIUS, BANNER,
                                                                                                    WALL)}
        cls.models = {int(r["CreatureID"]): r for r in reg.creature_template_models
                      if int(r["CreatureID"]) in (NEFARIUS, BANNER, WALL)}

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(MARK, BORED + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_spire", {"spell": mine}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_RG_\w+\s*=\s*(2104\d\d)", _header())}
        self.assertEqual(header_ids, set(mine))

    def test_the_bosses_and_the_arena_adds_are_bound(self):
        for entry, script, health in ((GYTH, "boss_gyth_rework", 140_000), (REND, "boss_rend_blackhand_rework",
                                                                            160_000)):
            with self.subTest(entry=entry):
                edit = self.edits[entry]
                self.assertEqual(edit["ScriptName"], script)
                self.assertEqual(edit["AIName"], "")
                self.assertEqual(edit["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
                self.assertEqual(edit["flags_extra"] & INSTANCE_BIND, INSTANCE_BIND)
                self.assertLessEqual(abs(math.ceil(WARRIOR_62_BASE * edit["HealthModifier"]) - health), 2)
        for entry, base, level, health in ((WHELP, PALADIN_58_BASE, 58, 4_000),
                                           (DRAGONSPAWN, WARRIOR_60_BASE, 60, 15_000),
                                           (HANDLER, WARRIOR_60_BASE, 60, 9_000)):
            with self.subTest(entry=entry):
                edit = self.edits[entry]
                self.assertEqual((int(edit["minlevel"]), int(edit["maxlevel"])), (level, level))
                self.assertEqual(math.ceil(base * edit["HealthModifier"]), health)
                self.assertNotIn("ScriptName", edit)    # SmartAI stays (the hunters get their AI on summon)

    def test_the_kit_creatures(self):
        nef = self.templates[NEFARIUS]
        self.assertEqual(nef["ScriptName"], "npc_brs_lord_victor_nefarius")
        self.assertTrue(int(nef["unit_flags"]) & UNIT_FLAG_NON_ATTACKABLE)
        self.assertFalse(int(nef["unit_flags"]) & UNIT_FLAG_IMMUNE_TO_PC)     # his own hits must reach players
        self.assertEqual(int(nef["lootid"]), 0)
        self.assertEqual(int(self.models[NEFARIUS]["CreatureDisplayID"]), 9472)
        banner = self.templates[BANNER]
        self.assertEqual(banner["ScriptName"], "npc_brs_banner_of_the_dark_horde")
        self.assertEqual(math.ceil(WARRIOR_60_BASE * float(banner["HealthModifier"])), 15_000)
        self.assertEqual(int(banner["difficulty_entry_1"]), 310296)
        self.assertEqual(int(banner["unit_flags"]), 0)
        self.assertEqual(int(self.models[BANNER]["CreatureDisplayID"]), DISPLAY_BATTLE_STANDARD)
        wall = self.templates[WALL]
        self.assertEqual(wall["ScriptName"], "npc_brs_frost_wall")
        self.assertTrue(int(wall["unit_flags"]) & UNIT_FLAG_NOT_SELECTABLE)
        self.assertEqual(int(self.models[WALL]["CreatureDisplayID"]), DISPLAY_ICE_WALL)
        self.assertAlmostEqual(float(self.models[WALL]["DisplayScale"]), 0.5)
        rend_cpp = REND_CPP.read_text(encoding="utf-8")
        gyth_cpp = GYTH_CPP.read_text(encoding="utf-8")
        for name in ("boss_rend_blackhand_rework", "npc_brs_lord_victor_nefarius",
                     "npc_brs_banner_of_the_dark_horde", "npc_brs_frost_wall"):
            self.assertRegex(rend_cpp, rf"if \(kWave2Bound\)\s*RegisterDungeonReworkCreatureAI\({name},")
        self.assertRegex(gyth_cpp, r"if \(kWave2Bound\)\s*RegisterDungeonReworkCreatureAI\(boss_gyth_rework,")

    def test_the_hits_are_resolve_copies(self):
        for sid, school in ((BREATH, SCHOOL_FIRE), (SWEEP, SCHOOL_FROST), (SHADOWFLAME, SCHOOL_SHADOW),
                            (WHIRL, SCHOOL_PHYSICAL)):
            with self.subTest(sid=sid):
                self.assertIn((sid, RESOLVE), self.scripts)
                self.assertEqual(int(self.spells[sid]["school"]), school)
                self.assertEqual(int(self.spells[sid]["effect1"]["type"]), SCHOOL_DAMAGE)

    def test_the_percent_spells(self):
        for sid, name, school in ((POOL_BURN, "kPoolPct", SCHOOL_SHADOW), (BITE, "kBitePct", SCHOOL_PHYSICAL),
                                  (BITE_H, "kBiteHeroicPct", SCHOOL_PHYSICAL)):
            with self.subTest(sid=sid):
                s = self.spells[sid]
                hundredths = round(_header_value(name) * 100)
                self.assertIn((sid, REFFLAT), self.scripts)
                self.assertEqual(int(s["school"]), school)
                self.assertEqual(int(s["effect1"]["base_points"]) + 1, hundredths)
                self.assertEqual(_raw(s, "EffectMiscValueB_1"), hundredths)
        crash = self.spells[CRASH]
        self.assertEqual(int(crash["school"]), SCHOOL_SHADOW)
        self.assertEqual((int(crash["effect1"]["base_points"]), int(crash["effect1"]["die_sides"])), (0, 0))
        self.assertNotIn((CRASH, REFFLAT), self.scripts)     # the share is the script's base points

    def test_the_bars_and_auras(self):
        for sid, name in ((BREATH_BAR, "kRiderlessCastMs"), (WHIRL_BAR, "kWhirlWindupMs")):
            with self.subTest(sid=sid):
                self.assertEqual(int(self.spells[sid]["cast_time_ms"]), int(_header_value(name)))
                self.assertEqual(_raw(self.spells[sid], "InterruptFlags"), 0)
        frozen = self.spells[FROZEN]
        self.assertEqual(int(frozen["effect1"]["apply_aura"]), AURA_MOD_STUN)
        self.assertEqual(int(frozen["duration_ms"]), int(_header_value("kFrozenMs")))
        self.assertEqual(int(self.spells[MARK]["duration_ms"]), int(_header_value("kMarkWarnMs")))
        self.assertEqual(int(self.spells[THUMBS]["duration_ms"]), int(_header_value("kThumbsWarnMs")))
        self.assertEqual(_raw(self.spells[THUMBS], "SpellVisualID_1"), SV_SKULL)
        self.assertEqual(int(self.spells[HUNTING]["duration_ms"]), int(_header_value("kRoundMs")))
        self.assertEqual(int(self.spells[WHIRL_LOOK]["duration_ms"]), int(_header_value("kWhirlMs")))
        for sid, name in ((POOL, "kPoolMs"), (POOL_H, "kPoolHeroicMs")):
            with self.subTest(sid=sid):
                pool = self.spells[sid]
                self.assertEqual(int(pool["effect1"]["type"]), PERSISTENT_AREA_AURA)
                self.assertEqual(float(pool["effect1"]["radius_yards"]), _header_value("kShadowflameRadius"))
                self.assertEqual(int(pool["duration_ms"]), int(_header_value(name)))
                self.assertEqual(_raw(pool, "SpellVisualID_1"), SV_POOL)
        for sid in (BANNER_BUFF, IMPATIENT, BORED):
            self.assertEqual(int(self.spells[sid]["effect1"]["apply_aura"]), AURA_DUMMY)

    def test_mortal_wounds_falls_off_before_the_next_swap(self):
        wounds = self.spells[WOUNDS]
        self.assertEqual(int(wounds["effect1"]["apply_aura"]), AURA_MOD_HEALING_PCT)
        self.assertEqual(int(wounds["effect1"]["base_points"]), -10)
        self.assertEqual(int(wounds["duration_ms"]), int(_header_value("kWoundsMs")))
        self.assertEqual(_raw(wounds, "CumulativeAura"), 255)
        every = _header_value("kWoundsEveryMs")
        swap_at = _header_value("kSwapAt")
        self.assertLess(int(wounds["duration_ms"]), swap_at * every)
        self.assertGreater(int(wounds["duration_ms"]), every)
        # Corrosive Acid (stock 16359) is shortened to the same 15 s by the script at 10.
        self.assertLess(_header_value("kAcidMs"), swap_at * _header_value("kAcidSwapEveryMs"))


class RendGythSqlTest(unittest.TestCase):
    def setUp(self):
        self.sql = SQL.read_text(encoding="utf-8")

    def test_the_spawn_rebind_touches_137967_only(self):
        # the heroic spawn mask rides along: the dbc-tools heroic rev sorts first and still sees 10162 there
        self.assertIn("UPDATE `creature` SET `id` = 300732, `spawnMask` = `spawnMask` | 2 WHERE `guid` = 137967 "
                      "AND `id` IN (10162, 300732);", self.sql)
        self.assertEqual(self.sql.count("UPDATE `creature`"), 1)
        self.assertNotRegex(self.sql, r"`guid` = 85785")     # Blackwing Lair's spawn

    def test_the_texts(self):
        rows = re.findall(r"^\((300732|10429), (\d+), 0, ((?:'(?:[^']|'')*'\s*)+),\s*(\d+), 0, 100, \d+, 0, 0, \d+, "
                          r"(\d+),", self.sql, flags=re.M)
        nef = {int(g): (int(t), int(r)) for e, g, _, t, r in rows if e == "300732"}
        rend = {int(g): (int(t), int(r)) for e, g, _, t, r in rows if e == "10429"}
        self.assertEqual(sorted(nef), list(range(20)))
        self.assertEqual(sorted(rend), [3, 4])
        for group in (14, 15, 16, 17):
            self.assertEqual(nef[group], (41, 3), group)
        for group in (3, 4):
            self.assertEqual(rend[group], (41, 3), group)
        self.assertEqual(nef[19][0], 12)
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 300732 AND `GroupID` BETWEEN 0 AND 19",
                      self.sql)
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 10429 AND `GroupID` BETWEEN 3 AND 4", self.sql)

    def test_the_handler_mends_gyth(self):
        self.assertIn("DELETE FROM `smart_scripts` WHERE `entryorguid` = 10742 AND `source_type` = 0 AND `id` = 1;",
                      self.sql)
        self.assertRegex(self.sql, r"\(10742, 0, 1, 0, 0, 0, 100, 0, .*, 11, 16637, .*, 19, 10339, 100,")
        self.assertNotIn("`entryorguid` = 10442", self.sql)
        self.assertNotIn("`entryorguid` = 10447", self.sql)


if __name__ == "__main__":
    unittest.main()
