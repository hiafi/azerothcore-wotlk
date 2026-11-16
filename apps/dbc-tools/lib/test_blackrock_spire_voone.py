"""
Blackrock Spire build WP-B3, War Master Voone: source/npcs/blackrock_spire/voone.py against its C++
(modules/mod-dungeon-bosses src/BlackrockSpire/VooneLogic.h, boss_warmaster_voone_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in Voone's slice (210090-210119) and VooneLogic.h names the same ids;
  - Voone 9237 is bound (SmartAI off, immunity 1972, INSTANCE_BIND), 174k at 5 players;
  - the five hits are resolve copies (Physical), the throw, fan and rain carry the Throw Axe missile look;
  - the two flight looks are destination DUMMYs whose missile speed covers a 30 yd lane in the warning;
  - the chain beam is a channeled aura with the harpoon chain's look; War Cry is interruptible and silence-preventable
    and 2.5 s as the header says; Berserking is +30% attack speed; the Recall bar is not interruptible and not Nature;
  - the Chain Anchor 300704 is a hidden helper on the stalker display (no trigger bit), no heroic row;
  - the SQL rev writes the six texts (the Recall line a boss emote) and the Stuck Axe gameobject 301250.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_spire_voone.py
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
HEADER = MODULE_DIR / "VooneLogic.h"
REWORK = MODULE_DIR / "BlackrockSpireRework.h"
SCRIPT = MODULE_DIR / "boss_warmaster_voone_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_warmaster_voone_blackrock_spire.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_spire"

SLICE = range(210090, 210120)
(AXE_THROW, AXE_FAN, AXE_RAIN, RECALL_HIT, CHAIN_HIT, AXE_FLIGHT, AXE_RETURN, CHAINED_AXE, WAR_CRY, BERSERKING,
 CHARGE, RECALL_BAR) = range(210090, 210102)
VOONE = 9237
ANCHOR = 300704
STUCK_AXE_GO = 301250
STALKER_DISPLAY = 11686
VOONE_HEALTH_AT_5 = 174_000
WARRIOR_58_BASE = 2871      # creature_classlevelstats level 58 class 1 basehp0

SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT = 2, 6, 3
AURA_DUMMY, AURA_MOD_MELEE_HASTE = 4, 138
SCHOOL_PHYSICAL, SCHOOL_NATURE = 1, 8      # school masks
UNIT_FLAG_NOT_SELECTABLE = 0x02000000
CREATURE_FLAG_EXTRA_TRIGGER = 0x80
RESOLVE = "spell_boss_mechanics_resolve"
TARGET_DEST_DEST = 87
TARGET_FLAG_DEST_LOCATION = 0x40
ATTR1_IS_CHANNELED = 0x00000004
IMMUNITY_BOSS_STUN = 1972
INSTANCE_BIND = 0x1
VISUAL_THROW_AXE = 3962
VISUAL_HARPOON_CHAIN = 10920
VISUAL_BERSERKING = 6943
VISUAL_BERSERKER_CHARGE = 4259


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


def _rawf(spell: dict, column: str) -> float:
    return float((spell.get("raw_overrides") or {}).get(column, 0) or 0)


def _header() -> str:
    return HEADER.read_text(encoding="utf-8")


def _header_value(name: str) -> float:
    match = re.search(rf"{name}\s*=\s*(-?[\d.]+)f?;", _header())
    assert match, name
    return float(match.group(1))


class VooneDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        mine = {int(e["id"]) for e in reg.spells if int(e["id"]) in SLICE}
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) == VOONE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == ANCHOR}
        cls.models = [e for e in reg.creature_template_models if int(e["CreatureID"]) == ANCHOR]
        cls.mine = mine
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.mine)
        self.assertEqual(mine, list(range(AXE_THROW, RECALL_BAR + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_spire", {"spell": mine}), [])
        first = re.search(r"kSpellsVoone\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(first)
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_VO_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))

    def test_voone_is_bound(self):
        voone = self.edits[VOONE]
        self.assertEqual(voone["ScriptName"], "boss_warmaster_voone_rework")
        self.assertEqual(voone["AIName"], "")
        self.assertEqual(voone["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
        self.assertEqual(voone["flags_extra"] & INSTANCE_BIND, INSTANCE_BIND)
        self.assertAlmostEqual(float(voone["DamageModifier"]), 3.5)
        # 174k at 5 players (within 2 HP: the modifier is rounded to three decimals)
        self.assertLessEqual(abs(math.ceil(WARRIOR_58_BASE * voone["HealthModifier"]) - VOONE_HEALTH_AT_5), 2)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_warmaster_voone_rework,", self.cpp)

    def test_the_hits_are_resolve_copies(self):
        for spell_id in (AXE_THROW, AXE_FAN, AXE_RAIN, RECALL_HIT, CHAIN_HIT):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
            self.assertEqual(spell["school"], SCHOOL_PHYSICAL, spell_id)
        # the three throws carry the missile; the recall and chain hits have no look of their own
        for spell_id in (AXE_THROW, AXE_FAN, AXE_RAIN):
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), VISUAL_THROW_AXE, spell_id)
        for spell_id in (RECALL_HIT, CHAIN_HIT):
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), 0, spell_id)
        self.assertEqual({name for _, name in self.scripts}, {RESOLVE})

    def test_the_flight_looks_cover_a_lane_in_the_warning(self):
        lane = _header_value("kLaneLength")
        for spell_id, speed_name, warn_name in ((AXE_FLIGHT, "kThrowMissileSpeed", "kThrowWarnMs"),
                                                (AXE_RETURN, "kReturnMissileSpeed", "kRecallWarnMs")):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], DUMMY_EFFECT, spell_id)
            self.assertEqual(spell["effect1"]["implicit_target_a"], TARGET_DEST_DEST, spell_id)
            self.assertTrue(_raw(spell, "Targets") & TARGET_FLAG_DEST_LOCATION, spell_id)
            self.assertEqual(_raw(spell, "SpellVisualID_1"), VISUAL_THROW_AXE, spell_id)
            speed = _rawf(spell, "Speed")
            self.assertAlmostEqual(speed, _header_value(speed_name))
            self.assertAlmostEqual(lane / speed * 1000.0, _header_value(warn_name), delta=1.0)

    def test_the_chain_beam(self):
        beam = self.spells[CHAINED_AXE]
        self.assertEqual(beam["effect1"]["type"], APPLY_AURA)
        self.assertEqual(beam["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertTrue(_raw(beam, "AttributesEx") & ATTR1_IS_CHANNELED)
        self.assertEqual(_raw(beam, "SpellVisualID_1"), VISUAL_HARPOON_CHAIN)
        self.assertGreater(beam["duration_ms"], int(_header_value("kChainLifeMs")) // 10)
        self.assertIn("anchor->CastSpell(me, SPELL_VO_CHAINED_AXE, true)", self.cpp)

    def test_war_cry_is_a_kick(self):
        cry = self.spells[WAR_CRY]
        self.assertEqual(cry["cast_time_ms"], int(_header_value("kWarCryCastMs")))
        self.assertEqual(_raw(cry, "InterruptFlags"), 15)
        self.assertEqual(_raw(cry, "PreventionType"), 1)         # silence can stop it (immunity 1972 has no silence)
        self.assertEqual(cry["school"], SCHOOL_NATURE)
        # the Recall bar is not a kick and not in the War Cry's school (a kick on the cry never locks the bar)
        bar = self.spells[RECALL_BAR]
        self.assertEqual(bar["cast_time_ms"], int(_header_value("kRecallWarnMs")))
        self.assertEqual(_raw(bar, "InterruptFlags"), 0)
        self.assertEqual(_raw(bar, "PreventionType"), 0)
        self.assertNotEqual(bar["school"], cry["school"])
        self.assertIn("d.interrupts.emplace_back(NPC_VOONE, SPELL_VO_WAR_CRY, kWarCryKickPriority", self.cpp)

    def test_berserking_and_the_charge(self):
        berserking = self.spells[BERSERKING]
        self.assertEqual(berserking["effect1"]["apply_aura"], AURA_MOD_MELEE_HASTE)
        self.assertEqual(berserking["effect1"]["base_points"], int(_header_value("kBerserkingPct")))
        self.assertEqual(_raw(berserking, "SpellVisualID_1"), VISUAL_BERSERKING)
        charge = self.spells[CHARGE]
        self.assertEqual(charge["effect1"]["type"], DUMMY_EFFECT)
        self.assertEqual(_raw(charge, "SpellVisualID_1"), VISUAL_BERSERKER_CHARGE)

    def test_the_chain_anchor(self):
        self.assertEqual(id_blocks.out_of_reservation("blackrock_spire", {"creature": [ANCHOR]}), [])
        anchor = self.creatures[ANCHOR]
        self.assertTrue(anchor["unit_flags"] & UNIT_FLAG_NOT_SELECTABLE)
        # no trigger bit: a hidden unit draws no beam (Greenskin's rope anchor is the same)
        self.assertFalse(anchor["flags_extra"] & CREATURE_FLAG_EXTRA_TRIGGER)
        self.assertEqual(anchor["ScriptName"], "")
        self.assertEqual(anchor.get("difficulty_entry_1", 0), 0)
        self.assertEqual(len(self.models), 1)
        self.assertEqual(int(self.models[0]["CreatureDisplayID"]), STALKER_DISPLAY)
        shared = REWORK.read_text(encoding="utf-8")
        self.assertRegex(shared, rf"NPC_BRS_CHAIN_ANCHOR\s*=\s*{ANCHOR},")
        self.assertRegex(shared, rf"GO_BRS_STUCK_AXE\s*=\s*{STUCK_AXE_GO},")

    def test_the_hold_answers_ranged_damage(self):
        # R-1 ruling 1: while he holds after the charge, a player damaging him from beyond 12 yd gets one Axe Throw
        # (the resolve copy 210090, Physical, no Weakened) every 2 s, landing with the 210095 flight.
        self.assertEqual(_header_value("kHoldReleaseYd"), 12.0)
        self.assertEqual(_header_value("kHoldThrowEveryMs"), 2000)
        self.assertIn("void DamageTaken(Unit* attacker", self.cpp)
        self.assertIn("AnswerRangedHit(attacker)", self.cpp)
        self.assertIn("spec.spellId = SPELL_VO_AXE_THROW;", self.cpp)
        self.assertIn("spec.weakened = false;", self.cpp)
        self.assertIn("SPELL_VO_AXE_FLIGHT", self.cpp)
        self.assertEqual(self.spells[AXE_THROW]["school"], SCHOOL_PHYSICAL)
        self.assertRegex(self.spells[AXE_THROW]["notes"], r"hold")

    def test_the_anchor_uses_the_shared_stalker_display(self):
        source = (PACKAGE / "voone.py").read_text(encoding="utf-8")
        self.assertIn("DISPLAY_INVISIBLE_STALKER", source)
        self.assertNotRegex(source, r"=\s*11686")

    def test_the_sql_rev(self):
        sql = SQL.read_text(encoding="utf-8")
        for group in range(6):
            self.assertRegex(sql, rf"\({VOONE}, {group}, 0, ")
        # the Recall line is a boss emote (41), the rest are yells (14)
        self.assertRegex(sql, rf"\({VOONE}, 4, 0, '%s calls his axes home!', 41,")
        for group in (0, 1, 2, 3, 5):
            self.assertRegex(sql, rf"\({VOONE}, {group}, 0, '[^\n]*', 14,")
        self.assertRegex(sql, rf"\({STUCK_AXE_GO}, 5, 8494, 'Stuck Axe'")
        self.assertIn("INSERT INTO `gameobject_template_addon`", sql)
        # no SmartAI to remove: the stock script is C++ (and S0's rev owns the wave 1 SmartAI deletes)
        self.assertNotIn("DELETE FROM `smart_scripts`", sql)


if __name__ == "__main__":
    unittest.main()
