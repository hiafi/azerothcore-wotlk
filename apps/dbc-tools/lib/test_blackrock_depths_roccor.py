"""
Blackrock Depths build WP-D2, Lord Roccor: source/npcs/blackrock_depths/roccor.py against its C++
(modules/mod-dungeon-bosses src/BlackrockDepths/RoccorLogic.h, boss_lord_roccor_rework.cpp), its SQL rev and G1's walk
drill row (mod-boss-mechanics src/MechanicDrill.h, when that source is on hand).

Checks:
  - the spells sit in Roccor's slice (210750-210779) and RoccorLogic.h names the same ids;
  - 9025 is bound (SmartAI off, immunity 1972, INSTANCE_BIND, 110k at 5 players, speed_walk 0.6);
  - Loosed Earth 300780: 7,000 health at level 51, an elite earth elemental of Roccor's faction, stunnable, no loot or
    XP, its heroic entry and the display 1161;
  - the two registry hits are resolve copies and the C++ names them; the cast bars are not kicks and match the header;
  - Flame Shock, Earth Shock and Hurl Stone carry the header's percents as hundredths on the kit's scripts;
  - the SQL rev: the road's two points at the header's ends and walk speed, the texts 0-3 as boss emotes;
  - the header matches G1's walk row (walk speed, leash radii and tags, Rampage's lane).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_roccor.py
"""

from __future__ import annotations

import math
import os
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
HEADER = MODULE_DIR / "RoccorLogic.h"
REWORK = MODULE_DIR / "BlackrockDepthsRework.h"
SCRIPT = MODULE_DIR / "boss_lord_roccor_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_roccor_blackrock_depths.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_depths"
# G1's drill (blackrock-depths-shapes): BOSS_MECHANICS_SRC, else the BM worktree beside this one.
BM_DRILL = Path(os.environ.get("BOSS_MECHANICS_SRC", str(REPO_ROOT.parent / "boss-mechanics-brd" / "src"))) \
    / "MechanicDrill.h"

SLICE = range(210750, 210780)
(RAMPAGE_CAST, RAMPAGE, SURGE, TREMOR, RISE, RETURN, MERGE, UNDERFOOT, CRACK, BOULDERS, BOULDER_LOOK, FLAME_SHOCK,
 EARTH_SHOCK, HURL) = range(210750, 210764)
ROCCOR, LOOSED_EARTH = 9025, 300780
WARRIOR_51_BASE = 2292
LOOSED_HEROIC_ENTRY = 310391

SCHOOL_DAMAGE, DUMMY_EFFECT, APPLY_AURA, HEAL, INTERRUPT_CAST = 2, 3, 6, 10, 68
AURA_DUMMY, AURA_PERIODIC_DAMAGE = 4, 3
SCHOOL_PHYSICAL, SCHOOL_FIRE, SCHOOL_NATURE = 1, 4, 8
DISPEL_MAGIC = 1
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT = "spell_dungeon_refflat_damage"
REFFLAT_PERIODIC = "spell_dungeon_refflat_periodic"
IMMUNITY_BOSS_STUN = 1972
INSTANCE_BIND = 0x1
FACTION_ELEMENTAL = 91
DISPLAY_LOOSED_EARTH = 1161
IGNORE_CASTER_MODIFIERS = 0x20000000


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
    return (spell.get("raw_overrides") or {}).get(column, 0) or 0


def _header() -> str:
    return HEADER.read_text(encoding="utf-8")


def _header_value(name: str) -> float:
    match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f?;", _header())
    assert match, name
    return float(match.group(1))


def _header_enum(name: str) -> int:
    match = re.search(rf"\b{name}\s*=\s*(\d+),", _header())
    assert match, name
    return int(match.group(1))


def _header_nh(name: str) -> tuple[float, float]:
    match = re.search(rf"\b{name}\{{\s*(-?[\d.]+)f?,\s*(-?[\d.]+)f?\s*\}};", _header())
    assert match, name
    return float(match.group(1)), float(match.group(2))


def _header_point(name: str) -> tuple[float, float, float]:
    match = re.search(rf"\b{name}\{{\s*(-?[\d.]+)f,\s*(-?[\d.]+)f,\s*(-?[\d.]+)f\s*\}};", _header())
    assert match, name
    return float(match.group(1)), float(match.group(2)), float(match.group(3))


class RoccorDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) == ROCCOR}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == LOOSED_EARTH}
        cls.models = [e for e in reg.creature_template_models if int(e["CreatureID"]) == LOOSED_EARTH]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(RAMPAGE_CAST, HURL + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"spell": mine}), [])
        found = re.search(r"kSpellsRoccor\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(found)
        self.assertEqual((int(found.group(1)), int(found.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_RO_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))

    def test_roccor_is_bound(self):
        row = self.edits[ROCCOR]
        self.assertEqual(row["ScriptName"], "boss_lord_roccor_rework")
        self.assertEqual(row["AIName"], "")
        self.assertEqual(row["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
        self.assertEqual(row["flags_extra"] & INSTANCE_BIND, INSTANCE_BIND)
        self.assertLessEqual(abs(math.ceil(WARRIOR_51_BASE * row["HealthModifier"]) - 110_000), 2)
        self.assertAlmostEqual(float(row["DamageModifier"]), 3.5)
        self.assertAlmostEqual(float(row["speed_walk"]), _header_value("kSpeedWalkRate"))
        self.assertAlmostEqual(float(row["speed_walk"]) * 2.5, _header_value("kWalkYdS"))
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_lord_roccor_rework,", self.cpp)
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_brd_loosed_earth,", self.cpp)

    def test_loosed_earth(self):
        add = self.creatures[LOOSED_EARTH]
        self.assertEqual(add["name"], "Loosed Earth")
        self.assertEqual(add["ScriptName"], "npc_brd_loosed_earth")
        self.assertEqual(add["AIName"], "")
        self.assertEqual((add["minlevel"], add["maxlevel"]), (51, 51))
        self.assertEqual(add["unit_class"], 1)
        self.assertEqual(add["type"], 4)                    # elemental
        self.assertEqual(add["faction"], FACTION_ELEMENTAL)
        self.assertEqual(add["CreatureImmunitiesId"], 0)    # stunnable (section 8 #4)
        self.assertEqual(add["lootid"], 0)
        self.assertEqual(float(add["ExperienceModifier"]), 0.0)
        normal, heroic = _header_nh("kLoosedHealth")
        self.assertEqual(math.ceil(WARRIOR_51_BASE * float(add["HealthModifier"])), int(normal))
        self.assertEqual(int(heroic), 12_000)
        self.assertEqual(add["difficulty_entry_1"], LOOSED_HEROIC_ENTRY)
        self.assertEqual([m["CreatureDisplayID"] for m in self.models], [DISPLAY_LOOSED_EARTH])

    def test_the_hits_are_resolve_copies(self):
        for spell_id, name in ((RAMPAGE, "SPELL_RO_RAMPAGE"), (BOULDERS, "SPELL_RO_FLUNG_BOULDERS")):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertEqual(spell["school"], SCHOOL_PHYSICAL, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
            self.assertIn(f".Spell({name})", self.cpp)
        # Rampage: no Weakened (the heroic hit is over 50%); the boulders: Weakened (under 50%)
        self.assertGreater(_header_nh("kRampagePct")[1], 50.0)
        self.assertLess(_header_value("kBoulderPct"), 50.0)
        rampage = self.cpp[self.cpp.index("void StartRampage()"):self.cpp.index("void UpdateRampage()")]
        self.assertNotIn("Weakened", rampage)
        boulders = self.cpp[self.cpp.index("uint32 FlingBoulders()"):]
        self.assertIn(".Weakened()", boulders[:boulders.index("return placed;")])

    def test_the_cast_bars(self):
        for bar, cast in ((RAMPAGE_CAST, "kRampageWarnMs"), (TREMOR, "kTremorCastMs")):
            spell = self.spells[bar]
            self.assertEqual(spell["cast_time_ms"], int(_header_value(cast)), bar)
            self.assertEqual(_raw(spell, "InterruptFlags"), 0, bar)
            self.assertNotEqual(_raw(spell, "SpellVisualID_1"), 0, bar)

    def test_the_shocks_and_the_stone(self):
        flame = self.spells[FLAME_SHOCK]
        normal, heroic = _header_nh("kFlameShockPct")
        self.assertEqual(flame["effect1"]["base_points"] + 1, round(normal * 100))
        self.assertEqual(_raw(flame, "EffectMiscValueB_1"), round(heroic * 100))
        tick_n, tick_h = _header_nh("kFlameShockTickPct")
        self.assertEqual(flame["effect2"]["apply_aura"], AURA_PERIODIC_DAMAGE)
        self.assertEqual(flame["effect2"]["base_points"] + 1, round(tick_n * 100))
        self.assertEqual(_raw(flame, "EffectMiscValueB_2"), round(tick_h * 100))
        self.assertEqual(flame["effect2"]["amplitude"], int(_header_value("kFlameShockTickMs")))
        self.assertEqual(flame["duration_ms"], int(_header_value("kFlameShockMs")))
        self.assertEqual(flame["dispel"], DISPEL_MAGIC)
        self.assertEqual(flame["school"], SCHOOL_FIRE)
        self.assertIn((FLAME_SHOCK, REFFLAT), self.scripts)
        self.assertIn((FLAME_SHOCK, REFFLAT_PERIODIC), self.scripts)
        self.assertIn("d.dispels.emplace_back(SPELL_RO_FLAME_SHOCK", self.cpp)

        earth = self.spells[EARTH_SHOCK]
        normal, heroic = _header_nh("kEarthShockPct")
        self.assertEqual(earth["effect1"]["base_points"] + 1, round(normal * 100))
        self.assertEqual(_raw(earth, "EffectMiscValueB_1"), round(heroic * 100))
        self.assertEqual(earth["effect2"]["type"], INTERRUPT_CAST)
        self.assertEqual(earth["duration_ms"], int(_header_value("kEarthShockLockoutMs")))
        self.assertEqual(earth["school"], SCHOOL_NATURE)
        self.assertIn((EARTH_SHOCK, REFFLAT), self.scripts)

        hurl = self.spells[HURL]
        normal, heroic = _header_nh("kHurlPct")
        self.assertEqual(hurl["effect1"]["base_points"] + 1, round(normal * 100))
        self.assertEqual(_raw(hurl, "EffectMiscValueB_1"), round(heroic * 100))
        self.assertIn((HURL, REFFLAT), self.scripts)
        # R-1-A m1: the stone waits out the tank's catch-up after a surge (HurlReady reads _tankGraceUntil)
        self.assertIn("HurlReady(_outOfReachMs, _clockMs, _nextHurlMs, _tankGraceUntil)", self.cpp)

        for spell_id in (FLAME_SHOCK, EARTH_SHOCK, HURL):
            self.assertTrue(int(_raw(self.spells[spell_id], "AttributesEx3")) & IGNORE_CASTER_MODIFIERS, spell_id)
            self.assertEqual(self.spells[spell_id]["cast_time_ms"], 0, spell_id)
        self.assertEqual(self.spells[FLAME_SHOCK]["range_yards"], _header_value("kShockRangeYd"))
        self.assertEqual(self.spells[EARTH_SHOCK]["range_yards"], _header_value("kShockRangeYd"))

    def test_the_looks(self):
        for spell_id in (SURGE, RISE, RETURN):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["apply_aura"], AURA_DUMMY, spell_id)
            self.assertGreater(spell["duration_ms"], 0, spell_id)
            self.assertNotEqual(_raw(spell, "SpellVisualID_1"), 0, spell_id)
        for spell_id in (UNDERFOOT, CRACK, BOULDER_LOOK):
            self.assertEqual(self.spells[spell_id]["effect1"]["type"], DUMMY_EFFECT, spell_id)
            self.assertNotEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), 0, spell_id)
        self.assertEqual(self.spells[SURGE]["duration_ms"], int(_header_value("kSurgeLookMs")))
        self.assertEqual(self.spells[RETURN]["duration_ms"], int(_header_value("kLoosedFadeMs")))
        merge = self.spells[MERGE]
        self.assertEqual(merge["effect1"]["type"], HEAL)
        self.assertIn("CastCustomSpell(me, SPELL_RO_EARTHEN_MERGE", self.cpp)

    def test_the_sql_rev(self):
        sql = SQL.read_text(encoding="utf-8")
        walk = _header_value("kWalkYdS")
        for point, name in ((1, "kRoadWest"), (2, "kRoadEast")):
            x, y, z = _header_point(name)
            self.assertIn(f"(473040, {point}, {x}, {y}, {z}, NULL, {walk}, 0, 0, 0, 0, 100, 0)", sql)
        self.assertEqual(len(re.findall(r"^\(473040, \d+,", sql, re.M)), 2)
        for group in range(4):
            self.assertRegex(sql, rf"\(9025, {group}, 0, '[^\n]*', 41,")
        self.assertIn("'%s rears up and Rampages down the road!'", sql)
        # S0's rev owns the SmartAI delete of 9025
        self.assertNotIn("DELETE FROM `smart_scripts`", sql)


@unittest.skipUnless(BM_DRILL.is_file(), "no mod-boss-mechanics source (set BOSS_MECHANICS_SRC)")
class RoccorMatchesTheWalkDrillTest(unittest.TestCase):
    """G1's walk row is the bots' gate for this fight (handoff 3.9): the live judge must use its numbers."""

    @classmethod
    def setUpClass(cls):
        cls.drill = BM_DRILL.read_text(encoding="utf-8")

    def _drill(self, name: str) -> float:
        match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f?;", self.drill)
        self.assertIsNotNone(match, name)
        return float(match.group(1))

    def test_numbers(self):
        self.assertEqual(self._drill("kRoccorWalkYdS"), _header_value("kWalkYdS"))
        self.assertEqual(self._drill("kTankLeashYd"), _header_value("kTankLeashYd"))
        self.assertEqual(self._drill("kRangeLeashYd"), _header_value("kRangeLeashYd"))
        self.assertEqual(self._drill("kRampageLength"), _header_value("kRampageLengthYd"))
        self.assertEqual(self._drill("kRampageWidth"), _header_value("kRampageWidthYd"))
        self.assertEqual(self._drill("kRampageMs"), _header_value("kRampageWarnMs"))
        self.assertEqual(self._drill("kBrdTagRampage"), _header_enum("TAG_RAMPAGE"))
        self.assertEqual(self._drill("kBrdTagTankLeash"), _header_enum("TAG_TANK_LEASH"))
        self.assertEqual(self._drill("kBrdTagRangeLeash"), _header_enum("TAG_RANGE_LEASH"))
        # the walk row's lane is the heroic hit
        self.assertIn('"line 20 2500 width=8 anchor=target cycle=0/2 pct=60 tag=1"', self.drill)
        self.assertEqual(_header_nh("kRampagePct")[1], 60.0)


if __name__ == "__main__":
    unittest.main()
