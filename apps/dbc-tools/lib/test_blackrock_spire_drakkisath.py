"""
Blackrock Spire build WP-B14, General Drakkisath: source/npcs/blackrock_spire/drakkisath.py against its C++
(modules/mod-dungeon-bosses src/BlackrockSpire/DrakkisathLogic.h, boss_drakkisath_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in his slice (210520-210559) and DrakkisathLogic.h names the same ids;
  - Drakkisath 10363 is bound (SmartAI off, immunity 1972, INSTANCE_BIND), 260k at 5 players; the Chromatic Elite
    Guard 10814 is bound to its C++ AI at level 60, 25,000 at 5 players;
  - the brands are 12 s DUMMY debuffs with V-2's minted runes; their ticks are the kit's percent spell at the header's
    percents;
  - the hits are resolve copies of the right school; the bars match the header, his Physical bars and the normal
    Flamestrike are not interruptible, the heroic Flamestrike is (Fire, his only Fire bar on heroic);
  - Thunderclap's slow is 3 s; the Flamestrike patch is a 5 yd, 15 s dynamic object with the stock spiral;
  - Seared Flesh stacks without a cap, lasts 15 s and falls off before the next swap (the user ruling);
  - the SQL rev writes texts 0-8 (the brand emotes as boss emotes 41) and drops the Guards' SmartAI rows.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_spire_drakkisath.py
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
HEADER = MODULE_DIR / "DrakkisathLogic.h"
SCRIPT = MODULE_DIR / "boss_drakkisath_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_drakkisath_blackrock_spire.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_spire"

SLICE = range(210520, 210560)
(SEARING, COLLAPSING, SEARING_BURN, SEARING_FLARE, COLLAPSING_BURN, COLLAPSING_SHARED, CLAP_BAR, CLAP, CLAP_SLOW,
 CLAP_LOOK, FS_BAR, FS_BAR_H, FS, FS_BURN, FS_PATCH, SWEEP_BAR, SWEEP, SWEEP_LOOK, SEARED) = range(210520, 210539)
DRAKKISATH, GUARD = 10363, 10814
WARRIOR_62_BASE = 3237
WARRIOR_60_BASE = 3052
HEALTH_AT_5 = 260_000
GUARD_AT_5 = 25_000

SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT, PERSISTENT_AREA_AURA = 2, 6, 3, 27
AURA_DUMMY, AURA_MOD_DECREASE_SPEED = 4, 33
SCHOOL_PHYSICAL, SCHOOL_FIRE = 1, 4         # school masks
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT = "spell_dungeon_refflat_damage"
IMMUNITY_BOSS_STUN = 1972
INSTANCE_BIND = 0x1
AURA_INTERRUPT_CHANGE_MAP = 0x00080000
SV_BRAND_SEARING, SV_BRAND_COLLAPSING = 90613, 90614
SV_FLAMESTRIKE, SV_THUNDERCLAP, SV_SWEEP, SV_SEARED_FLESH = 10383, 145, 399, 9112


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


class DrakkisathDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {}
        for e in reg.creature_template_edits:
            if int(e["entry"]) in (DRAKKISATH, GUARD):
                cls.edits.setdefault(int(e["entry"]), {}).update(e)

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(SEARING, SEARED + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_spire", {"spell": mine}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_DR_\w+\s*=\s*(2105\d\d)", _header())}
        self.assertEqual(header_ids, set(mine))

    def test_the_boss_and_the_guards_are_bound(self):
        edit = self.edits[DRAKKISATH]
        self.assertEqual(edit["ScriptName"], "boss_drakkisath_rework")
        self.assertEqual(edit["AIName"], "")
        self.assertEqual(edit["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
        self.assertEqual(edit["flags_extra"] & INSTANCE_BIND, INSTANCE_BIND)
        self.assertLessEqual(abs(math.ceil(WARRIOR_62_BASE * edit["HealthModifier"]) - HEALTH_AT_5), 2)
        guard = self.edits[GUARD]
        self.assertEqual(guard["ScriptName"], "npc_brs_chromatic_elite_guard")
        self.assertEqual(guard["AIName"], "")
        self.assertEqual((int(guard["minlevel"]), int(guard["maxlevel"])), (60, 60))
        self.assertEqual(math.ceil(WARRIOR_60_BASE * guard["HealthModifier"]), GUARD_AT_5)
        script = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_drakkisath_rework", script)
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_brs_chromatic_elite_guard", script)

    def test_the_brands(self):
        for sid, visual in ((SEARING, SV_BRAND_SEARING), (COLLAPSING, SV_BRAND_COLLAPSING)):
            with self.subTest(sid=sid):
                brand = self.spells[sid]
                self.assertEqual(int(brand["effect1"]["apply_aura"]), AURA_DUMMY)
                self.assertEqual(int(brand["duration_ms"]), int(_header_value("kBrandMs")))
                self.assertEqual(_raw(brand, "SpellVisualID_1"), visual)
                self.assertEqual(int(_raw(brand, "AuraInterruptFlags")), AURA_INTERRUPT_CHANGE_MAP)
        for sid, name in ((SEARING_BURN, "kSearingBearerPct"), (SEARING_FLARE, "kSearingOthersPct"),
                          (COLLAPSING_BURN, "kCollapsingAlonePct"), (COLLAPSING_SHARED, "kCollapsingPairedPct")):
            with self.subTest(sid=sid):
                tick = self.spells[sid]
                hundredths = round(_header_value(name) * 100)
                self.assertIn((sid, REFFLAT), self.scripts)
                self.assertEqual(int(tick["school"]), SCHOOL_FIRE)
                self.assertEqual(int(tick["effect1"]["type"]), SCHOOL_DAMAGE)
                self.assertEqual(int(tick["effect1"]["base_points"]) + 1, hundredths)
                self.assertEqual(_raw(tick, "EffectMiscValueB_1"), hundredths)
        # SP: Collapsing is 80% less with company.
        self.assertAlmostEqual(_header_value("kCollapsingPairedPct"), _header_value("kCollapsingAlonePct") * 0.2)

    def test_the_hits_are_resolve_copies(self):
        for sid, school in ((CLAP, SCHOOL_PHYSICAL), (FS, SCHOOL_FIRE), (FS_BURN, SCHOOL_FIRE),
                            (SWEEP, SCHOOL_PHYSICAL)):
            with self.subTest(sid=sid):
                self.assertIn((sid, RESOLVE), self.scripts)
                self.assertEqual(int(self.spells[sid]["school"]), school)
                self.assertEqual(int(self.spells[sid]["effect1"]["type"]), SCHOOL_DAMAGE)
                self.assertEqual(_raw(self.spells[sid], "SpellVisualID_1"), 0)

    def test_the_bars(self):
        for sid, name, school in ((CLAP_BAR, "kThunderclapCastMs", SCHOOL_PHYSICAL),
                                  (FS_BAR, "kFlamestrikeCastMs", SCHOOL_FIRE),
                                  (FS_BAR_H, "kFlamestrikeCastMs", SCHOOL_FIRE),
                                  (SWEEP_BAR, "kSweepCastMs", SCHOOL_PHYSICAL)):
            with self.subTest(sid=sid):
                self.assertEqual(int(self.spells[sid]["cast_time_ms"]), int(_header_value(name)))
                self.assertEqual(int(self.spells[sid]["school"]), school)
        for sid in (CLAP_BAR, FS_BAR, SWEEP_BAR):
            self.assertEqual(_raw(self.spells[sid], "InterruptFlags"), 0)
        # The heroic bar is the expected kick, and the only Fire bar on heroic: a kick locks nothing else of his.
        self.assertEqual(_raw(self.spells[FS_BAR_H], "InterruptFlags"), 15)
        self.assertEqual(_raw(self.spells[FS_BAR_H], "PreventionType"), 1)
        self.assertIn("SPELL_DR_FLAMESTRIKE_CAST_H", SCRIPT.read_text(encoding="utf-8"))

    def test_the_looks_and_riders(self):
        slow = self.spells[CLAP_SLOW]
        self.assertEqual(int(slow["effect1"]["apply_aura"]), AURA_MOD_DECREASE_SPEED)
        self.assertEqual(int(slow["duration_ms"]), int(_header_value("kThunderclapSlowMs")))
        self.assertEqual(int(slow["effect1"]["base_points"]) + 1, -int(_header_value("kThunderclapSlowPct")))
        patch = self.spells[FS_PATCH]
        self.assertEqual(int(patch["effect1"]["type"]), PERSISTENT_AREA_AURA)
        self.assertEqual(float(patch["effect1"]["radius_yards"]), _header_value("kFlamestrikeRadius"))
        self.assertEqual(int(patch["duration_ms"]), int(_header_value("kFlamestrikePatchMs")))
        self.assertEqual(_raw(patch, "SpellVisualID_1"), SV_FLAMESTRIKE)
        self.assertEqual(_raw(self.spells[CLAP_LOOK], "SpellVisualID_1"), SV_THUNDERCLAP)
        self.assertEqual(_raw(self.spells[SWEEP_LOOK], "SpellVisualID_1"), SV_SWEEP)

    def test_seared_flesh(self):
        seared = self.spells[SEARED]
        self.assertEqual(int(seared["effect1"]["apply_aura"]), AURA_DUMMY)
        self.assertEqual(int(seared["duration_ms"]), int(_header_value("kSearedFleshMs")))
        self.assertEqual(_raw(seared, "CumulativeAura"), 255)
        self.assertEqual(_raw(seared, "SpellVisualID_1"), SV_SEARED_FLESH)
        # The user ruling: the old tank's stacks are gone before the new holder reaches the swap count, and a stack
        # outlasts one strike.
        every = _header_value("kSearedFleshEveryMs")
        swap_at = _header_value("kSearedFleshSwapAt")
        self.assertLess(int(seared["duration_ms"]), swap_at * every)
        self.assertGreater(int(seared["duration_ms"]), every)


class DrakkisathSqlTest(unittest.TestCase):
    def setUp(self):
        self.sql = SQL.read_text(encoding="utf-8")

    def test_the_texts(self):
        rows = re.findall(r"^\(10363, (\d), 0, '((?:[^']|'')*)', (\d+),", self.sql, flags=re.M)
        self.assertEqual([int(g) for g, _, _ in rows], list(range(9)))
        types = {int(g): int(t) for g, _, t in rows}
        for group in (1, 2):
            self.assertEqual(types[group], 41, group)
        for group in (0, 3, 4, 5, 6, 7, 8):
            self.assertEqual(types[group], 14, group)
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 10363 AND `GroupID` BETWEEN 0 AND 8", self.sql)

    def test_the_guards_leave_smart_ai(self):
        self.assertIn("DELETE FROM `smart_scripts` WHERE `entryorguid` = 10814 AND `source_type` = 0;", self.sql)
        self.assertNotIn("INSERT INTO `smart_scripts`", self.sql)


if __name__ == "__main__":
    unittest.main()
