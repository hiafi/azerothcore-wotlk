"""
Blackrock Spire build WP-B5, Urok Doomhowl: source/npcs/blackrock_spire/urok.py against its C++
(modules/mod-dungeon-bosses src/BlackrockSpire/UrokLogic.h, UrokShards.h, boss_urok_doomhowl_rework.cpp; the Stratholme
Ramstein test is the precedent).

Checks:
  - the spells sit in Urok's slice (210150-210179) and UrokLogic.h names the same ids;
  - the Stolen Magic Shard 300706 (a passive helper with the Power Spark display, npc_brs_stolen_magic_shard, no
    heroic template) in the `blackrock_spire` creature reservation;
  - Warosh's Power and Stolen Power hold the header's caps, durations and percents;
  - the hits are resolve copies, the fear rider 2 s, Unstable a 6 s stacking debuff, the missile at 30 yd/s;
  - 10584 and the shard and the pile are bound and registered.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_spire_urok.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockSpire"
HEADER = MODULE_DIR / "UrokLogic.h"
REWORK = MODULE_DIR / "BlackrockSpireRework.h"
SCRIPT = MODULE_DIR / "boss_urok_doomhowl_rework.cpp"
SQL_REV = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_blackrock_spire_urok.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_spire"

SLICE = range(210150, 210180)
(WAROSH, STOLEN_POWER, RECLAIM, WILD_BOLT, MISSILE, LANDING, HOWL_CAST, HOWL, HOWL_FEAR, HOWL_LOOK, OVERCHARGE_CAST,
 OVERCHARGE, OVERCHARGE_LOOK, UNSTABLE, UNSTABLE_LOOK, UNSTABLE_BURST) = range(210150, 210166)
SHARD = 300706
UROK = 10584
POWER_SPARK_DISPLAY = 26753

SCHOOL_DAMAGE, APPLY_AURA = 2, 6
AURA_DUMMY, AURA_MOD_FEAR, AURA_MOD_DAMAGE_PERCENT_DONE, AURA_MOD_HEALING_DONE_PERCENT = 4, 7, 79, 136
UNIT_FLAG_NOT_SELECTABLE = 0x02000000
UNIT_FLAG_NON_ATTACKABLE = 0x2
RESOLVE = "spell_boss_mechanics_resolve"


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


def _raw(spell: dict, column: str):
    return (spell.get("raw_overrides") or {}).get(column, 0) or 0


def _header() -> str:
    return HEADER.read_text(encoding="utf-8")


def _header_const(name: str) -> float:
    match = re.search(rf"{name}\s*=\s*(-?[\d.]+)f?;", _header())
    assert match, name
    return float(match.group(1))


def _header_nh(name: str) -> tuple[float, float]:
    match = re.search(rf"{name}\{{\s*(-?[\d.]+)f?,\s*(-?[\d.]+)f?\s*\}}", _header())
    assert match, name
    return float(match.group(1)), float(match.group(2))


class UrokDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == SHARD}
        cls.models = [e for e in reg.creature_template_models if int(e["CreatureID"]) == SHARD]
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) == UROK}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(WAROSH, UNSTABLE_BURST + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_spire", {"spell": mine}), [])
        first = re.search(r"kSpellsUrok\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(first)
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_UR_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))

    def test_the_shard(self):
        self.assertEqual(sorted(self.creatures), [SHARD])
        self.assertEqual(id_blocks.out_of_reservation("blackrock_spire", {"creature": [SHARD]}), [])
        shard = self.creatures[SHARD]
        self.assertEqual(shard["ScriptName"], "npc_brs_stolen_magic_shard")
        self.assertTrue(shard["unit_flags"] & UNIT_FLAG_NOT_SELECTABLE)
        self.assertTrue(shard["unit_flags"] & UNIT_FLAG_NON_ATTACKABLE)
        self.assertEqual(shard.get("difficulty_entry_1", 0), 0)
        self.assertEqual(shard["lootid"], 0)
        self.assertEqual([int(m["CreatureDisplayID"]) for m in self.models], [POWER_SPARK_DISPLAY])
        self.assertIn("NPC_BRS_STOLEN_MAGIC_SHARD", (MODULE_DIR / "UrokShards.h").read_text(encoding="utf-8"))

    def test_the_buffs(self):
        warosh = self.spells[WAROSH]
        self.assertEqual(_raw(warosh, "CumulativeAura"), int(_header_const("kWaroshMaxStacks")))
        self.assertEqual(warosh["duration_ms"], int(_header_const("kWaroshMs")))
        self.assertEqual(warosh["effect1"]["apply_aura"], AURA_MOD_DAMAGE_PERCENT_DONE)
        self.assertEqual(warosh["effect2"]["apply_aura"], AURA_MOD_HEALING_DONE_PERCENT)
        pct = int(_header_const("kWaroshPctPerStack"))
        self.assertEqual((warosh["effect1"]["base_points"], warosh["effect2"]["base_points"]), (pct, pct))
        stolen = self.spells[STOLEN_POWER]
        normal_cap, heroic_cap = _header_nh("kStolenPowerCap")
        self.assertEqual(_raw(stolen, "CumulativeAura"), int(normal_cap))
        self.assertGreaterEqual(normal_cap, heroic_cap)
        self.assertEqual(stolen["duration_ms"], -1)
        self.assertEqual(stolen["effect1"]["apply_aura"], AURA_MOD_DAMAGE_PERCENT_DONE)
        self.assertEqual(stolen["effect1"]["base_points"], int(_header_const("kStolenPowerPctPerStack")))

    def test_hits_riders_and_looks(self):
        for spell_id in (WILD_BOLT, HOWL, OVERCHARGE, UNSTABLE_BURST):
            self.assertEqual(self.spells[spell_id]["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
        self.assertEqual({name for _, name in self.scripts}, {RESOLVE})
        fear = self.spells[HOWL_FEAR]
        self.assertEqual(fear["effect1"]["apply_aura"], AURA_MOD_FEAR)
        self.assertEqual(fear["duration_ms"], int(_header_const("kDoomhowlFearMs")))
        self.assertEqual(self.spells[HOWL_CAST]["cast_time_ms"], int(_header_const("kDoomhowlCastMs")))
        self.assertEqual(self.spells[OVERCHARGE_CAST]["cast_time_ms"], int(_header_const("kOverchargeCastMs")))
        unstable = self.spells[UNSTABLE]
        self.assertEqual(unstable["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(unstable["duration_ms"], int(_header_const("kUnstableFuseMs")))
        self.assertGreater(_raw(unstable, "CumulativeAura"), int(_header_const("kUnstableGrabMaxStacks")))
        self.assertEqual(float(_raw(self.spells[MISSILE], "Speed")), _header_const("kWildBoltMissileSpeed"))
        # V-1: the lob is Arcane Barrage's missile, never Arcane Bomb's SV 12302 (no missile).
        self.assertEqual(_raw(self.spells[MISSILE], "SpellVisualID_1"), 9947)
        for spell_id in self.spells:
            self.assertNotEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), 12302, spell_id)
        self.assertEqual(_raw(self.spells[LANDING], "SpellVisualID_1"), 965)
        self.assertEqual(_raw(self.spells[OVERCHARGE_LOOK], "SpellVisualID_1"), 8340)
        self.assertEqual(_raw(self.spells[HOWL_LOOK], "SpellVisualID_1"), 247)
        self.assertEqual(_raw(self.spells[RECLAIM], "SpellVisualID_1"), 12205)
        self.assertEqual(_raw(self.spells[UNSTABLE_LOOK], "SpellVisualID_1"), 969)

    def test_urok_and_his_helpers_are_bound(self):
        self.assertEqual(self.edits[UROK]["ScriptName"], "boss_urok_doomhowl_rework")
        for name in ("boss_urok_doomhowl_rework", "npc_brs_stolen_magic_shard"):
            self.assertIn(f"RegisterDungeonReworkCreatureAI({name},", self.cpp)
        self.assertIn("RegisterDungeonReworkGameObjectAI(go_brs_urok_pile,", self.cpp)

    def test_the_shard_rule_lets_humans_take_a_third(self):
        # SP UR10 via F-1a's bot-only claim order: anyone grabs at 0-2 stacks, bots stop at 2.
        self.assertEqual(int(_header_const("kUnstableGrabMaxStacks")), 2)
        self.assertEqual(int(_header_const("kUnstableBotCapStacks")), 2)
        self.assertIn("spec.who.maxStacks = kUnstableGrabMaxStacks;", self.cpp)
        self.assertIn("spec.order = BossMechanics::Ordering{ SPELL_UR_UNSTABLE, true, kUnstableBotCapStacks };",
                      self.cpp)
        # B9 shares the shard spec: the rule stays Urok's (ShardSpec sets no stack rule).
        shards = (MODULE_DIR / "UrokShards.h").read_text(encoding="utf-8")
        self.assertNotIn("maxStacks", shards)
        self.assertNotIn(".order", shards)

    def test_the_hidden_owner_is_not_immune_to_players(self):
        # R-1-A m4 / n1: the prelude's own hits land (no IMMUNE_TO_PC), combat stays locked while hidden, and the
        # challenge's grid hold ends with him.
        hide = self.cpp[self.cpp.index("void Hide()"):]
        hide = hide[:hide.index("}")]
        self.assertNotIn("SetImmuneToAll(true)", hide)
        self.assertNotIn("SetImmuneToPC(true)", hide)
        self.assertIn("SetIsCombatDisallowed(true)", hide)
        self.assertIn("SetIsCombatDisallowed(false)", self.cpp)
        self.assertEqual(self.cpp.count("me->setActive(false)"), 2)

    def test_the_ogre_smartai_block_is_rewritten_whole(self):
        # R-1-A m3: DELETE every row of the (entryorguid, source_type) pair, then INSERT the kept stock combat rows
        # with the heroic bit.
        sql = SQL_REV.read_text(encoding="utf-8")
        self.assertIn("DELETE FROM `smart_scripts` WHERE `entryorguid` IN (10601, 10602) AND `source_type` = 0;", sql)
        self.assertNotIn("`source_type` = 0 AND `id` BETWEEN", sql)
        rows = re.findall(r"^\((1060[12]), 0, (\d+), 0, \d+, 0, 100, (\d+),", sql, re.M)
        self.assertEqual([(int(e), int(i)) for e, i, _ in rows], [(10601, 0), (10602, 0), (10602, 1), (10602, 2)])
        for _, _, flags in rows:
            self.assertTrue(int(flags) & 4)
        for spell_id in ("14516", "15979", "13747", "6742"):
            self.assertIn(f", 11, {spell_id}, ", sql)


if __name__ == "__main__":
    unittest.main()
