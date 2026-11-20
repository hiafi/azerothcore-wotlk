"""
Blackrock Depths build WP-D11, Lord Incendius: source/npcs/blackrock_depths/incendius.py against its C++
(modules/mod-dungeon-bosses src/BlackrockDepths/IncendiusLogic.h, boss_lord_incendius_rework.cpp), its SQL rev and G1's
bands drill row (mod-boss-mechanics src/MechanicDrill.h, when that source is on hand).

Checks:
  - the spells sit in Incendius's slice (211140-211179) and IncendiusLogic.h names the same ids;
  - 9017 is bound (SmartAI off, immunity 1973, INSTANCE_BIND, 100k at 5 players, DamageModifier 3.5);
  - the Ember of Incendius 300794: 6,000 health at level 53, an elite fire elemental of his faction, no immunities, no
    loot or XP, its heroic entry, display 1405, bound to its AI;
  - the three registry hits are Fire resolve copies the C++ names; Fiery Burst carries the header's percents on the
    kit's refflat script and is kickable; the Curse is +10% Fire damage taken in 45 yd for 60 s, a Curse;
  - the looks carry a SpellVisual; the SQL rev: texts 0-7 with the right types, nothing outside 0-7;
  - the header matches G1's bands row (the tags 13-15, the 4 yd neck band, the 2 yd crumble step, the 5 s warning).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_incendius.py
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
HEADER = MODULE_DIR / "IncendiusLogic.h"
REWORK = MODULE_DIR / "BlackrockDepthsRework.h"
SCRIPT = MODULE_DIR / "boss_lord_incendius_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_incendius_blackrock_depths.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_depths"
BM_DRILL = Path(os.environ.get("BOSS_MECHANICS_SRC", str(REPO_ROOT.parent / "boss-mechanics-brd" / "src"))) \
    / "MechanicDrill.h"

SLICE = range(211140, 211180)
(CURSE, BURST, STORM, STORM_CAST, STORM_PATCH, FIST, FIST_WAVE, FIST_RING, SURGE, SURGE_BURST, SHATTER, REBORN,
 EMBER_ARRIVES, CRUMBLE_BURST, CRUMBLED_EDGE, CRUMBLING_GROUND) = range(211140, 211156)
INCENDIUS, EMBER = 9017, 300794
WARRIOR_53_BASE = 2453
EMBER_HEROIC_ENTRY = 310405

SCHOOL_DAMAGE, DUMMY_EFFECT, APPLY_AURA = 2, 3, 6
AURA_DUMMY, AURA_MOD_DAMAGE_PERCENT_TAKEN = 4, 87
SCHOOL_FIRE = 4
FIRE_MASK = 4
DISPEL_CURSE = 2
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT = "spell_dungeon_refflat_damage"
IMMUNITY_FIRE_GIANT = 1973
INSTANCE_BIND = 0x1
FACTION_ELEMENTAL = 91
DISPLAY_EMBER = 1405
IGNORE_CASTER_MODIFIERS = 0x20000000
CAST_INDEX_1500 = 16


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


class IncendiusDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) == INCENDIUS}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == EMBER}
        cls.models = [e for e in reg.creature_template_models if int(e["CreatureID"]) == EMBER]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(CURSE, CRUMBLING_GROUND + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"spell": mine}), [])
        found = re.search(r"kSpellsIncendius\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(found)
        self.assertEqual((int(found.group(1)), int(found.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_IN_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))

    def test_incendius_is_bound(self):
        row = self.edits[INCENDIUS]
        self.assertEqual(row["ScriptName"], "boss_lord_incendius_rework")
        self.assertEqual(row["AIName"], "")
        self.assertEqual(row["CreatureImmunitiesId"], IMMUNITY_FIRE_GIANT)
        self.assertEqual(row["flags_extra"] & INSTANCE_BIND, INSTANCE_BIND)
        normal, heroic = _header_nh("kBossHealth")
        self.assertLessEqual(abs(math.ceil(WARRIOR_53_BASE * row["HealthModifier"]) - int(normal)), 2)
        self.assertEqual(int(heroic), 160_000)
        self.assertAlmostEqual(float(row["DamageModifier"]), 3.5)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_lord_incendius_rework,", self.cpp)
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_brd_ember_of_incendius,", self.cpp)

    def test_ember(self):
        add = self.creatures[EMBER]
        self.assertEqual(add["name"], "Ember of Incendius")
        self.assertEqual(add["ScriptName"], "npc_brd_ember_of_incendius")
        self.assertEqual(add["AIName"], "")
        self.assertEqual((add["minlevel"], add["maxlevel"]), (53, 53))
        self.assertEqual(add["unit_class"], 1)
        self.assertEqual(add["type"], 4)                    # elemental
        self.assertEqual(add["faction"], FACTION_ELEMENTAL)
        self.assertEqual(add["CreatureImmunitiesId"], 0)    # slows, roots and stuns hold it (a reward)
        self.assertEqual(add["lootid"], 0)
        self.assertEqual(float(add["ExperienceModifier"]), 0.0)
        normal, heroic = _header_nh("kEmberHealth")
        self.assertEqual(math.ceil(WARRIOR_53_BASE * float(add["HealthModifier"])), int(normal))
        self.assertEqual(int(heroic), 9_000)
        self.assertEqual(add["difficulty_entry_1"], EMBER_HEROIC_ENTRY)
        self.assertEqual([m["CreatureDisplayID"] for m in self.models], [DISPLAY_EMBER])

    def test_the_registry_hits_are_fire_resolve_copies(self):
        for spell_id, name in ((STORM, "SPELL_IN_FIRE_STORM"), (FIST, "SPELL_IN_MAGMA_FIST"),
                               (SURGE, "SPELL_IN_LAVA_SURGE")):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertEqual(spell["school"], SCHOOL_FIRE, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
            self.assertIn(f".Spell({name})", self.cpp)
        # Magma Fist and Lava Surge are single avoidable hits under 50%: Weakened; the patches tick (no Weakened).
        fist = self.cpp[self.cpp.index("MechanicHandle MagmaFist(Player* forced)"):self.cpp.index("void FistThrow(")]
        self.assertIn(".Weakened()", fist)
        surge = self.cpp[self.cpp.index("MechanicHandle LavaSurge("):self.cpp.index("void SurgeLanded(")]
        self.assertIn(".Weakened()", surge)
        storm = self.cpp[self.cpp.index("MechanicHandle FireStorm(Player* forced)"):
                         self.cpp.index("MechanicHandle MagmaFist(Player* forced)")]
        self.assertNotIn(".Weakened()", storm)
        self.assertIn(".Persistent(", storm)

    def test_fiery_burst(self):
        burst = self.spells[BURST]
        normal, heroic = _header_nh("kBurstPct")
        self.assertEqual(burst["effect1"]["base_points"] + 1, round(normal * 100))
        self.assertEqual(_raw(burst, "EffectMiscValueB_1"), round(heroic * 100))
        self.assertEqual(burst["effect1"]["radius_yards"], _header_value("kBurstRadiusYd"))
        self.assertEqual(burst["cast_time_ms"], int(_header_value("kBurstCastMs")))
        self.assertEqual(_raw(burst, "CastingTimeIndex"), CAST_INDEX_1500)
        self.assertEqual(_raw(burst, "InterruptFlags"), 15)          # kickable
        self.assertEqual(burst["school"], SCHOOL_FIRE)
        # D12 request 1 (F-1 QUEUE): the refflat percent times Firelord's Will (x1 off the hard mode).
        self.assertIn((BURST, "spell_brd_lake_scaled_hit"), self.scripts)
        self.assertTrue(int(_raw(burst, "AttributesEx3")) & IGNORE_CASTER_MODIFIERS)
        self.assertIn("d.interrupts.emplace_back(NPC_INCENDIUS, SPELL_IN_FIERY_BURST", self.cpp)

    def test_curse(self):
        curse = self.spells[CURSE]
        effect = curse["effect1"]
        self.assertEqual(effect["type"], APPLY_AURA)
        self.assertEqual(effect["apply_aura"], AURA_MOD_DAMAGE_PERCENT_TAKEN)
        self.assertEqual(effect["base_points"] + 1, int(_header_value("kCurseFirePct")))
        self.assertEqual(effect["misc_value"], FIRE_MASK)
        self.assertEqual(effect["radius_yards"], _header_value("kCurseRadiusYd"))
        self.assertEqual(curse["duration_ms"], int(_header_value("kCurseMs")))
        self.assertEqual(curse["dispel"], DISPEL_CURSE)
        self.assertIn("d.dispels.emplace_back(SPELL_IN_CURSE", self.cpp)
        self.assertIn("RemoveAurasDueToSpell(SPELL_IN_CURSE)", self.cpp)     # rule 6: off every player at the end

    def test_the_looks(self):
        for spell_id in (STORM_CAST, STORM_PATCH, FIST_WAVE, FIST_RING, SURGE_BURST, SHATTER, REBORN, EMBER_ARRIVES,
                         CRUMBLE_BURST, CRUMBLED_EDGE, CRUMBLING_GROUND):
            spell = self.spells[spell_id]
            self.assertNotEqual(_raw(spell, "SpellVisualID_1"), 0, spell_id)
            kind = spell["effect1"]
            self.assertTrue(kind["type"] == DUMMY_EFFECT or kind.get("apply_aura") == AURA_DUMMY, spell_id)
        self.assertEqual(self.spells[STORM_PATCH]["duration_ms"], int(_header_value("kFireStormLifeMs")))
        self.assertEqual(self.spells[CRUMBLED_EDGE]["duration_ms"], -1)
        self.assertIn("spec.pushSpell = SPELL_IN_CRUMBLING_GROUND;", self.cpp)

    def test_the_hard_mode_scales_and_the_necks_grip(self):
        # D12 request 1: Firelord's Will on Fire Storm and Magma Fist (the hook; Fiery Burst through its script);
        # R-1-B m3: the hard mode's Magma Fist starts at its near end; R-1-B m4: the sealed necks put players back.
        self.assertIn("kFireStormPct(_heroic) * HardModeScale()", self.cpp)
        self.assertIn("kFistPct(_heroic) * HardModeScale()", self.cpp)
        self.assertIn("FistStartOffset(distance)", self.cpp)
        self.assertIn("UpdateNeckGrip(diff);", self.cpp)
        self.assertIn("PastSealedNeck(", self.cpp)

    def test_the_sql_rev(self):
        sql = SQL.read_text(encoding="utf-8")
        types = {0: 14, 1: 14, 2: 41, 3: 14, 4: 14, 5: 41, 6: 41, 7: 41}
        for group, kind in types.items():
            self.assertRegex(sql, rf"\(9017, {group}, 0, '[^\n]*', {kind},")
            if kind == 41:      # R-1-B n1: the boss emotes are map-wide (TextRange 3)
                self.assertRegex(sql, rf"\(9017, {group}, 0, '[^\n]*', 41, 0, 100, 0, 0, 0, 0, 3,")
        self.assertEqual(len(re.findall(r"^\(9017, \d+,", sql, re.M)), 8)
        self.assertIn("I cannot be destroyed! By the will of Ragnaros, I shall be reborn!', 14, 0, 100, 0, 0, 0, "
                      "5061,", sql)
        self.assertIn("`GroupID` BETWEEN 0 AND 7", sql)                       # D12 owns 8-9
        self.assertNotIn("DELETE FROM `smart_scripts`", sql)                  # S0's rev owns the SmartAI delete
        # The text enum matches the rev's groups.
        for name, group in (("YELL_IN_SHATTER", 0), ("YELL_IN_REBORN", 1), ("EMOTE_IN_CRUMBLES", 2),
                            ("YELL_IN_DEATH", 3), ("EMOTE_IN_EDGE_CRACKS", 5)):
            self.assertEqual(_header_enum(name), group)


@unittest.skipUnless(BM_DRILL.is_file(), "no mod-boss-mechanics source (set BOSS_MECHANICS_SRC)")
class IncendiusMatchesTheBandsDrillTest(unittest.TestCase):
    """G1's bands row is the bots' gate for this fight (handoff 3.9): the live bands must use its numbers."""

    @classmethod
    def setUpClass(cls):
        cls.drill = BM_DRILL.read_text(encoding="utf-8")

    def _drill(self, name: str) -> float:
        match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f?;", self.drill)
        self.assertIsNotNone(match, name)
        return float(match.group(1))

    def test_tags(self):
        self.assertEqual(self._drill("kBrdTagEdgeBand"), _header_enum("TAG_IN_NECK_SEAL"))
        self.assertEqual(self._drill("kBrdTagCrumble"), _header_enum("TAG_IN_CRUMBLE"))
        self.assertEqual(self._drill("kBrdTagSweep"), _header_enum("TAG_IN_ARM_SWEEP"))

    def test_band_widths_and_warning(self):
        # tag 13: 4 yd lethal bands, 5 s; tag 14: 2 yd lethal bands, 5 s (the drill's line steps).
        self.assertIn('"line 22 5000 width=4 offset=90 shift=-11:-22 lethal=1', self.drill)
        self.assertIn('"line 48 5000 width=2 shift=-24:6 lethal=1', self.drill)
        self.assertEqual(_header_value("kNeckSealWidthYd"), 4.0)
        self.assertEqual(_header_value("kCrumbleStepYd"), 2.0)
        self.assertEqual(_header_value("kArenaSMax") - _header_value("kArenaSMin"), 48.0)    # the drill's 48 yd strip


if __name__ == "__main__":
    unittest.main()
