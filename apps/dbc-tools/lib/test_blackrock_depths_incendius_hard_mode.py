"""
Blackrock Depths build WP-D12, Lord of the Lake (Lord Incendius's heroic hard mode):
source/npcs/blackrock_depths/incendius_hard_mode.py against its C++ (modules/mod-dungeon-bosses
src/BlackrockDepths/IncendiusHardModeLogic.h, incendius_hard_mode.cpp), its SQL rev, the shared visuals, WP-H's heroic
row, IT's Cinder spell and G1's bands drill row (mod-boss-mechanics src/MechanicDrill.h, when that source is on hand).

Checks:
  - the spells sit in Lord of the Lake's slice (211180-211229) and IncendiusHardModeLogic.h names the same ids;
  - the Lava Spawn 300795: 6,000 health (normal row at level 53, WP-H's heroic override), an elite fire elemental of
    his faction, no immunities, no loot or XP, its heroic entry, display 2172, bound to its AI;
  - the two registry hits are Fire resolve copies the C++ names (Crushing Fist spares the tank and carries Weakened;
    the Arm Sweep is a lethal line on the drill's tag); the scaled hits carry the header's percents on the WP's script;
    the Arm Sweep's bar is a 4 s Physical cast nobody can kick; Firelord's Will is +10% damage a stack, 10 at most;
  - the looks carry a SpellVisual; the giant's display and scale are V-1's; IT's Cinder spell is bound to the script
    the C++ registers;
  - the SQL rev: texts 8-9, boss emotes, nothing outside 8-9;
  - the header matches G1's bands drill (the sweep: tag 15, 4 s, 10 yd, 30%).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_incendius_hard_mode.py
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
from source.npcs.blackrock_depths import _visuals as visuals  # noqa: E402

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockDepths"
HEADER = MODULE_DIR / "IncendiusHardModeLogic.h"
D11_HEADER = MODULE_DIR / "IncendiusLogic.h"
REWORK = MODULE_DIR / "BlackrockDepthsRework.h"
SCRIPT = MODULE_DIR / "incendius_hard_mode.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_incendius_hard_mode_blackrock_depths.sql"
HEROIC = TOOL_ROOT / "source" / "world" / "dungeons" / "blackrock_depths.py"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_depths"
BM_DRILL = Path(os.environ.get("BOSS_MECHANICS_SRC", str(REPO_ROOT.parent / "boss-mechanics-brd" / "src"))) \
    / "MechanicDrill.h"

SLICE = range(211180, 211230)
(FIST, FIST_TANK, FIST_LOOK, SWEEP_CAST, SWEEP, BREATH, WILL, SPAWN_CLIMB, ERUPTION, SPAWN_ARRIVES, RISES,
 CINDER_TOSS) = range(211180, 211192)
CINDER_USE = 211260
LAVA_SPAWN = 300795
HAND = 300828           # R-1-B M2: the giant's stand-in on the rim (IncendiusHardModeLogic.h NPC_LAKE_HAND)
LAVA_SPAWN_HEROIC_ENTRY = 310406
WARRIOR_53_BASE = 2453

SCHOOL_DAMAGE, DUMMY_EFFECT, APPLY_AURA = 2, 3, 6
AURA_DUMMY, AURA_MOD_DAMAGE_PERCENT_DONE = 4, 79
SCHOOL_PHYSICAL, SCHOOL_FIRE = 1, 4         # school masks
RESOLVE = "spell_boss_mechanics_resolve"
SCALED = "spell_brd_lake_scaled_hit"
CINDER_SCRIPT = "spell_brd_cinder_of_the_firelord"
FACTION_ELEMENTAL = 91
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


def _value(name: str, text: str | None = None) -> float:
    match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f?;", text if text is not None else _header())
    assert match, name
    return float(match.group(1))


def _enum(name: str, text: str | None = None) -> int:
    match = re.search(rf"\b{name}\s*=\s*(\d+),", text if text is not None else _header())
    assert match, name
    return int(match.group(1))


class LordOfTheLakeDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE or int(e["id"]) == CINDER_USE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE or int(e["spell_id"]) == CINDER_USE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) in (LAVA_SPAWN, HAND)}
        cls.models = [e for e in reg.creature_template_models if int(e["CreatureID"]) == LAVA_SPAWN]
        cls.hand_models = [e for e in reg.creature_template_models if int(e["CreatureID"]) == HAND]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(i for i in self.spells if i in SLICE)
        self.assertEqual(mine, list(range(FIST, CINDER_TOSS + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"spell": mine}), [])
        found = re.search(r"kSpellsLordOfTheLake\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(found)
        self.assertEqual((int(found.group(1)), int(found.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_LAKE_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))

    def test_lava_spawn(self):
        add = self.creatures[LAVA_SPAWN]
        self.assertEqual(add["name"], "Lava Spawn")
        self.assertEqual(add["ScriptName"], "npc_brd_lava_spawn")
        self.assertEqual(add["AIName"], "")
        self.assertEqual((add["minlevel"], add["maxlevel"]), (53, 53))
        self.assertEqual(add["type"], 4)                    # elemental
        self.assertEqual(add["faction"], FACTION_ELEMENTAL)
        self.assertEqual(add["CreatureImmunitiesId"], 0)    # slows, roots and stuns hold it (a reward)
        self.assertEqual(add["lootid"], 0)
        self.assertEqual(float(add["ExperienceModifier"]), 0.0)
        health = int(_value("kLavaSpawnHealth"))
        self.assertEqual(math.ceil(WARRIOR_53_BASE * float(add["HealthModifier"])), health)
        self.assertEqual(add["difficulty_entry_1"], LAVA_SPAWN_HEROIC_ENTRY)
        self.assertEqual([m["CreatureDisplayID"] for m in self.models], [visuals.DISPLAY_LAVA_SPAWN])
        # The fighting template is WP-H's heroic one (the hard mode is heroic only): the same 6,000.
        self.assertRegex(HEROIC.read_text(encoding="utf-8"), rf"\b{LAVA_SPAWN}: dict\(health=6_000\)")
        self.assertEqual(health, 6000)
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_brd_lava_spawn,", self.cpp)

    def test_the_registry_hits(self):
        for spell_id, name in ((FIST, "SPELL_LAKE_CRUSHING_FIST"), (SWEEP, "SPELL_LAKE_ARM_SWEEP")):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertEqual(spell["school"], SCHOOL_FIRE, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
            self.assertIn(f".Spell({name})", self.cpp)
        fist = self.cpp[self.cpp.index("MechanicHandle CrushingFist("):self.cpp.index("void CrushingLanded(")]
        self.assertIn(".TankExempt()", fist)               # the tank's hit is the script's (211181)
        self.assertIn(".Weakened()", fist)
        self.assertIn("kCrushingOthersPct", fist)
        self.assertIn("Tag(TAG_LAKE_CRUSHING_FIST)", fist)
        sweep = self.cpp[self.cpp.index("MechanicHandle ArmSweep("):self.cpp.index("uint32 SpawnLava(")]
        self.assertIn(".Lethal()", sweep)                   # the drill's lethal=1
        self.assertIn("Tag(TAG_LAKE_ARM_SWEEP)", sweep)
        self.assertIn("ThrowOff(hit, bearing", sweep)
        self.assertIn("SPELL_LAKE_ARM_SWEEP_CAST", sweep)

    def test_the_scaled_hits(self):
        for spell_id, pct_name in ((FIST_TANK, "kCrushingTankPct"), (BREATH, "kBreathPct")):
            spell = self.spells[spell_id]
            hundredths = round(_value(pct_name) * 100)
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertEqual(spell["effect1"]["base_points"] + 1, hundredths, spell_id)
            self.assertEqual(_raw(spell, "EffectMiscValueB_1"), hundredths, spell_id)    # heroic: the same
            self.assertEqual(spell["school"], SCHOOL_FIRE)
            self.assertTrue(int(_raw(spell, "AttributesEx3")) & IGNORE_CASTER_MODIFIERS)
            self.assertIn((spell_id, SCALED), self.scripts)
        self.assertIn("RegisterSpellScript(spell_brd_lake_scaled_hit);", self.cpp)
        self.assertNotEqual(_raw(self.spells[BREATH], "SpellVisualID_1"), 0)
        self.assertEqual(_raw(self.spells[BREATH], "SpellVisualID_1"), visuals.IN_FIRELORDS_BREATH)

    def test_the_sweep_bar_cannot_be_kicked(self):
        bar = self.spells[SWEEP_CAST]
        self.assertEqual(bar["cast_time_ms"], int(_value("kSweepCastMs")))
        self.assertEqual(bar["school"], SCHOOL_PHYSICAL)    # rule 5: Fiery Burst, the kick, is Fire
        self.assertEqual(_raw(bar, "InterruptFlags"), 0)
        self.assertEqual(_raw(bar, "PreventionType"), 0)
        self.assertEqual(_raw(bar, "SpellVisualID_1"), visuals.IN_ARM_SWEEP)

    def test_firelords_will(self):
        will = self.spells[WILL]
        effect = will["effect1"]
        self.assertEqual(effect["type"], APPLY_AURA)
        self.assertEqual(effect["apply_aura"], AURA_MOD_DAMAGE_PERCENT_DONE)
        self.assertEqual(effect["base_points"], int(_value("kWillPctPerStack")))
        self.assertEqual(_raw(will, "CumulativeAura"), int(_value("kWillMaxStacks")))
        self.assertEqual(will["duration_ms"], -1)
        self.assertIn("RemoveAurasDueToSpell(SPELL_LAKE_FIRELORDS_WILL)", self.cpp)    # rule 6

    def test_the_looks(self):
        expected = {FIST_LOOK: visuals.IN_CRUSHING_FIST, SPAWN_CLIMB: visuals.IN_LAVA_SPAWN_CLIMB,
                    ERUPTION: visuals.IN_SHATTER_INTO_EMBERS, SPAWN_ARRIVES: visuals.IN_FIERY_BURST,
                    RISES: visuals.IN_LAVA_SPAWN_CLIMB, CINDER_TOSS: visuals.IN_CINDER_TOSS}
        for spell_id, visual in expected.items():
            spell = self.spells[spell_id]
            self.assertEqual(_raw(spell, "SpellVisualID_1"), visual, spell_id)
            kind = spell["effect1"]
            self.assertTrue(kind["type"] == DUMMY_EFFECT or kind.get("apply_aura") == AURA_DUMMY, spell_id)

    def test_the_giant_is_v1s(self):
        self.assertEqual(int(_value("kGiantDisplay")), visuals.DISPLAY_INCENDIUS_GIANT)
        low, high = visuals.INCENDIUS_GIANT_SCALE_RANGE
        self.assertTrue(low <= _value("kGiantScale") <= high)

    def test_the_cinder(self):
        cinder = self.spells[CINDER_USE]
        self.assertEqual(cinder["effect1"]["type"], DUMMY_EFFECT)
        self.assertIn((CINDER_USE, CINDER_SCRIPT), self.scripts)              # IT's binding
        self.assertIn(f"RegisterSpellScript({CINDER_SCRIPT});", self.cpp)     # this WP's script
        self.assertIn("OnCheckCast += SpellCheckCastFn(spell_brd_cinder_of_the_firelord::CheckCast)", self.cpp)
        self.assertIn("SPELL_FAILED_DONT_REPORT", self.cpp)                   # a refusal keeps the item

    def test_the_hand_of_incendius(self):
        # R-1-B M2 (orchestrator default): the giant keeps a small reach; the melee and the tank hit his Hand, which
        # shares his health. Same faction and immunity as him, passive, no loot or XP, no heroic template (only ever
        # summoned on the heroic hard mode: the normal row fights, at his level).
        hand = self.creatures[HAND]
        self.assertEqual(hand["ScriptName"], "npc_brd_lake_hand")
        self.assertEqual(hand["AIName"], "")
        self.assertEqual(hand["faction"], FACTION_ELEMENTAL)
        self.assertEqual(hand["CreatureImmunitiesId"], 1973)
        self.assertEqual(hand["lootid"], 0)
        self.assertEqual(float(hand["ExperienceModifier"]), 0.0)
        self.assertEqual(int(hand.get("difficulty_entry_1") or 0), 0)
        self.assertEqual([m["CreatureDisplayID"] for m in self.hand_models], [visuals.DISPLAY_INCENDIUS_GIANT])
        self.assertRegex(_header(), rf"NPC_LAKE_HAND = {HAND};")
        self.assertNotRegex(HEROIC.read_text(encoding="utf-8"), rf"\b{HAND}\b")
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_brd_lake_hand,", self.cpp)
        self.assertIn("Unit::DealDamage(attacker, giant, dealt", self.cpp)
        # His own reach is small; his swing and Firelord's Will on D11's hits are the script's.
        self.assertRegex(_header(), r"kGiantReachYd = 1\.5f;")
        self.assertIn("bool Melee(IncendiusFight const& /*fight*/) const override { return false; }", self.cpp)
        self.assertIn("return WillOf(fight.Boss());", self.cpp)

    def test_the_sql_rev(self):
        sql = SQL.read_text(encoding="utf-8")
        for group in (8, 9):
            self.assertRegex(sql, rf"\(9017, {group}, 0, '[^\n]*', 41, 0, 100, 0, 0, 0, 0, 3,")   # map-wide (n1)
        self.assertEqual(len(re.findall(r"^\(9017, \d+,", sql, re.M)), 2)
        self.assertIn("`GroupID` BETWEEN 8 AND 9", sql)                       # D11 owns 0-7
        self.assertNotIn("smart_scripts", sql)
        self.assertEqual(_enum("EMOTE_LAKE_RISES"), 8)
        self.assertEqual(_enum("EMOTE_LAKE_SPAWNS"), 9)
        for line in sql.splitlines():
            self.assertLessEqual(len(line), 120)
            self.assertEqual(line, line.rstrip())


@unittest.skipUnless(BM_DRILL.is_file(), "no mod-boss-mechanics source (set BOSS_MECHANICS_SRC)")
class LordOfTheLakeMatchesTheBandsDrillTest(unittest.TestCase):
    """G1's bands row is the bots' gate for this fight (handoff 3.9): the live sweep must use its numbers."""

    @classmethod
    def setUpClass(cls):
        cls.drill = BM_DRILL.read_text(encoding="utf-8")

    def test_the_sweep(self):
        match = re.search(r"\bkBrdTagSweep\s*=\s*(\d+);", self.drill)
        self.assertIsNotNone(match)
        self.assertEqual(int(match.group(1)), _enum("TAG_IN_ARM_SWEEP", D11_HEADER.read_text(encoding="utf-8")))
        self.assertIn("TAG_LAKE_ARM_SWEEP      = BrdIncendius::TAG_IN_ARM_SWEEP", _header())
        cast = int(_value("kSweepCastMs"))
        width = int(_value("kSweepWidthYd"))
        pct = int(_value("kSweepPct"))
        self.assertRegex(self.drill, rf'"line 22 {cast} width={width} offset=90 [^"]*lethal=1 school=fire pct={pct} ')


if __name__ == "__main__":
    unittest.main()
