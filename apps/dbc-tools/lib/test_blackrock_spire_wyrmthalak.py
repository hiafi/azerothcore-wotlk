"""
Blackrock Spire build WP-B8, Overlord Wyrmthalak: source/npcs/blackrock_spire/wyrmthalak.py against its C++
(modules/mod-dungeon-bosses src/BlackrockSpire/WyrmthalakLogic.h, boss_overlord_wyrmthalak_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in his slice (210250-210289) and WyrmthalakLogic.h names the same ids;
  - Wyrmthalak 9568 is bound (SmartAI off, immunity 1972, INSTANCE_BIND), 200k at 5 players;
  - the six hits are resolve copies of the right school; Mortal Strike is the kit's percent spell at 30% of the tank
    row; Mortal Wounds is -10% healing a stack, 15 s, uncapped, and falls off before the next swap (the user ruling);
  - the breath bar is 2 s, not interruptible, Fire; the missiles cover the ledge in their warnings;
  - Overlord's Fury is +15% damage / +10% attack speed, 3 stacks;
  - the champions are 25k level 60 elites (stun immune) on their heroic entries, the rider is not attackable, the
    thrower is a hidden helper;
  - the SQL rev writes the ten texts (emotes as boss emotes 41) and the champions' weapons.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_spire_wyrmthalak.py
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
HEADER = MODULE_DIR / "WyrmthalakLogic.h"
SCRIPT = MODULE_DIR / "boss_overlord_wyrmthalak_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_wyrmthalak_blackrock_spire.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_spire"

SLICE = range(210250, 210290)
(DRAGONFIRE_BAR, DRAGONFIRE, BURN, BLACK_FLAME, TAIL, TAIL_LOOK, BOULDER, BOULDER_MISSILE, AXES, AXE_MARK, THROW_AXE,
 RIDERS, CHARGE_LOOK, FURY, MORTAL_STRIKE, MORTAL_WOUNDS) = range(210250, 210266)
WYRMTHALAK = 9568
CHAMPIONS = {300708: 310291, 300709: 310292, 300710: 310293}
RIDER, THROWER = 300711, 300712
WARRIOR_60_BASE = 3052
HEALTH_AT_5 = 200_000
CHAMPION_AT_5 = 25_000

SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT = 2, 6, 3
AURA_DUMMY, AURA_MOD_HEALING_PCT, AURA_MOD_DAMAGE_PERCENT_DONE, AURA_MOD_MELEE_HASTE = 4, 118, 79, 138
SCHOOL_PHYSICAL, SCHOOL_FIRE = 1, 4         # school masks
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT = "spell_dungeon_refflat_damage"
TARGET_DEST_DEST = 87
UNIT_FLAG_NON_ATTACKABLE = 0x2
UNIT_FLAG_NOT_SELECTABLE = 0x02000000
CREATURE_FLAG_EXTRA_TRIGGER = 0x80
IMMUNITY_BOSS_STUN = 1972
INSTANCE_BIND = 0x1
SV_SPIT_PATCH_STATE = 90601


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


def _header_nh(name: str) -> tuple[float, float]:
    match = re.search(rf"\b{name}\{{\s*(-?[\d.]+)f?,\s*(-?[\d.]+)f?\s*\}};", _header())
    assert match, name
    return float(match.group(1)), float(match.group(2))


class WyrmthalakDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) == WYRMTHALAK}
        mine = set(CHAMPIONS) | {RIDER, THROWER}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) in mine}
        cls.models = {int(e["CreatureID"]): e for e in reg.creature_template_models if int(e["CreatureID"]) in mine}

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(DRAGONFIRE_BAR, MORTAL_WOUNDS + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_spire", {"spell": mine}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_WT_\w+\s*=\s*(2102\d\d)", _header())}
        self.assertEqual(header_ids, set(mine))

    def test_the_boss_is_bound(self):
        edit = self.edits[WYRMTHALAK]
        self.assertEqual(edit["ScriptName"], "boss_overlord_wyrmthalak_rework")
        self.assertEqual(edit["AIName"], "")
        self.assertEqual(edit["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
        self.assertEqual(edit["flags_extra"] & INSTANCE_BIND, INSTANCE_BIND)
        # S0's 65.531 (within 2 HP of the build spec, as lib/test_blackrock_spire_kit.py allows).
        self.assertLessEqual(abs(math.ceil(WARRIOR_60_BASE * edit["HealthModifier"]) - HEALTH_AT_5), 2)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_overlord_wyrmthalak_rework",
                      SCRIPT.read_text(encoding="utf-8"))

    def test_the_hits_are_resolve_copies(self):
        for sid, school in ((DRAGONFIRE, SCHOOL_FIRE), (BURN, SCHOOL_FIRE), (TAIL, SCHOOL_PHYSICAL),
                            (BOULDER, SCHOOL_PHYSICAL), (AXES, SCHOOL_PHYSICAL), (RIDERS, SCHOOL_PHYSICAL)):
            with self.subTest(sid=sid):
                self.assertIn((sid, RESOLVE), self.scripts)
                self.assertEqual(int(self.spells[sid]["school"]), school)
                self.assertEqual(int(self.spells[sid]["effect1"]["type"]), SCHOOL_DAMAGE)
        # The burn's tick never replays the breath on him (no look of its own).
        self.assertEqual(_raw(self.spells[BURN], "SpellVisualID_1"), 0)

    def test_the_breath_bar(self):
        bar = self.spells[DRAGONFIRE_BAR]
        self.assertEqual(int(bar["cast_time_ms"]), int(_header_value("kBreathCastMs")))
        self.assertEqual(_raw(bar, "InterruptFlags"), 0)
        self.assertEqual(int(bar["school"]), SCHOOL_FIRE)

    def test_the_missiles_cover_the_ledge_in_their_warnings(self):
        boulder = self.spells[BOULDER_MISSILE]
        self.assertEqual(int(boulder["effect1"]["implicit_target_a"]), TARGET_DEST_DEST)
        self.assertEqual(_raw(boulder, "Speed"), _header_value("kBoulderMissileSpeed"))
        self.assertGreaterEqual(_raw(boulder, "Speed") * _header_value("kBoulderWarnMs") / 1000.0, 50.0)
        axe = self.spells[THROW_AXE]
        self.assertEqual(_raw(axe, "Speed"), _header_value("kAxeMissileSpeed"))
        self.assertEqual(int(self.spells[AXE_MARK]["duration_ms"]), int(_header_value("kAxeWarnMs")))

    def test_the_black_flame_patch_is_the_minted_state(self):
        flame = self.spells[BLACK_FLAME]
        self.assertEqual(int(flame["effect1"]["apply_aura"]), AURA_DUMMY)
        self.assertEqual(_raw(flame, "SpellVisualID_1"), SV_SPIT_PATCH_STATE)
        self.assertEqual(int(flame["duration_ms"]), -1)

    def test_overlords_fury(self):
        fury = self.spells[FURY]
        self.assertEqual(int(fury["effect1"]["apply_aura"]), AURA_MOD_DAMAGE_PERCENT_DONE)
        self.assertEqual(int(fury["effect1"]["base_points"]), int(_header_value("kFuryDamagePct")))
        self.assertEqual(int(fury["effect2"]["apply_aura"]), AURA_MOD_MELEE_HASTE)
        self.assertEqual(int(fury["effect2"]["base_points"]), int(_header_value("kFuryHastePct")))
        self.assertEqual(_raw(fury, "CumulativeAura"), _header_value("kFuryMaxStacks"))

    def test_mortal_strike_and_wounds(self):
        strike = self.spells[MORTAL_STRIKE]
        self.assertIn((MORTAL_STRIKE, REFFLAT), self.scripts)
        pct = _header_value("kMortalStrikeTankPct")
        self.assertEqual(int(strike["effect1"]["base_points"]) + 1, int(pct * 100))
        self.assertEqual(_raw(strike, "EffectMiscValueB_1"), pct * 100)
        wounds = self.spells[MORTAL_WOUNDS]
        self.assertEqual(int(wounds["effect1"]["apply_aura"]), AURA_MOD_HEALING_PCT)
        self.assertEqual(int(wounds["effect1"]["base_points"]), int(_header_value("kMortalWoundsHealingPct")))
        self.assertEqual(int(wounds["duration_ms"]), int(_header_value("kMortalWoundsMs")))
        self.assertEqual(_raw(wounds, "CumulativeAura"), 255)
        # The user ruling: the old tank's stacks are gone before the new holder reaches the swap count.
        every = _header_value("kMortalStrikeEveryMs")
        swap_at = _header_value("kMortalWoundsSwapAt")
        self.assertLess(int(wounds["duration_ms"]), (swap_at - 1) * every)

    def test_the_champions(self):
        for entry, heroic in CHAMPIONS.items():
            with self.subTest(entry=entry):
                c = self.creatures[entry]
                self.assertEqual(c["ScriptName"], "npc_brs_wyrmthalak_champion")
                self.assertEqual(int(c["minlevel"]), 60)
                self.assertEqual(int(c["rank"]), 1)
                self.assertEqual(int(c["CreatureImmunitiesId"]), IMMUNITY_BOSS_STUN)
                self.assertEqual(math.ceil(WARRIOR_60_BASE * float(c["HealthModifier"])), CHAMPION_AT_5)
                self.assertEqual(int(c["difficulty_entry_1"]), heroic)
                self.assertGreater(float(self.models[entry]["DisplayScale"]), 1.0)

    def test_the_rider_and_the_thrower(self):
        rider = self.creatures[RIDER]
        self.assertEqual(rider["ScriptName"], "npc_brs_bloodaxe_worg_rider")
        self.assertEqual(int(rider["unit_flags"]) & UNIT_FLAG_NON_ATTACKABLE, UNIT_FLAG_NON_ATTACKABLE)
        self.assertEqual(int(rider["difficulty_entry_1"]), 310294)
        thrower = self.creatures[THROWER]
        self.assertEqual(thrower["ScriptName"], "")
        self.assertEqual(int(thrower["unit_flags"]) & UNIT_FLAG_NOT_SELECTABLE, UNIT_FLAG_NOT_SELECTABLE)
        self.assertEqual(int(thrower["flags_extra"]) & CREATURE_FLAG_EXTRA_TRIGGER, CREATURE_FLAG_EXTRA_TRIGGER)
        self.assertEqual(int(thrower.get("difficulty_entry_1") or 0), 0)
        # The invisible stalker skin comes from ._visuals (F-1e / F-1d), value unchanged.
        from source.npcs.blackrock_spire import _visuals
        self.assertEqual(_visuals.DISPLAY_INVISIBLE_STALKER, 11686)
        self.assertEqual(int(self.models[THROWER]["CreatureDisplayID"]), 11686)

    def test_the_numbers_match_the_build_spec(self):
        self.assertEqual(_header_nh("kBreathPct"), (35.0, 45.0))
        self.assertEqual(_header_nh("kTailPct"), (20.0, 25.0))
        self.assertEqual(_header_nh("kBoulderPct"), (25.0, 30.0))
        self.assertEqual(_header_nh("kAxePct"), (25.0, 30.0))
        self.assertEqual(_header_nh("kRiderPct"), (30.0, 35.0))
        self.assertEqual(_header_nh("kOrderEveryMs"), (30000.0, 25000.0))


class WyrmthalakSqlTest(unittest.TestCase):
    def setUp(self):
        self.sql = SQL.read_text(encoding="utf-8")

    def test_the_ten_texts(self):
        rows = re.findall(r"^\(9568, (\d), 0, '((?:[^']|'')*)', (\d+),", self.sql, flags=re.M)
        self.assertEqual([int(g) for g, _, _ in rows], list(range(10)))
        types = {int(g): int(t) for g, _, t in rows}
        for group in (1, 5, 7, 8, 9):
            self.assertEqual(types[group], 41, group)
        for group in (0, 2, 3, 4, 6):
            self.assertEqual(types[group], 14, group)
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 9568", self.sql)

    def test_the_champions_weapons(self):
        self.assertIn("(300708, 1, 5286, 5286, 0, 0)", self.sql)
        self.assertIn("(300710, 1, 12142, 0, 0, 0)", self.sql)


if __name__ == "__main__":
    unittest.main()
