"""
Stratholme build WP-S3, Timmy the Cruel: source/npcs/stratholme/timmy_the_cruel.py against its C++
(modules/mod-dungeon-bosses src/Stratholme/TimmyLogic.h, boss_timmy_the_cruel_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in his slice (206460-206479) and TimmyLogic.h names the same ids; the stock kit stays stock;
  - the Playmate 300604 (5,000 health on the level 58 warrior base, his faction, display 571 at 0.8, heroic 310193);
  - the shatter and the trip are resolve copies; the rope is one registry Jump per skip (warning = the cast);
  - Frozen: a -70% slow and the kit's 2% periodic, outlasting a round, no mechanic, CHANGE_MAP;
  - Patty Cake: a kickable 4 s self channel of four claps; the clap is 10% / 20% (MiscValueB), filtered to the square;
  - the looks are WP-V-2's picks; 10808 is bound (59.213, DamageModifier 13, 1972, INSTANCE_BIND);
  - the SQL rev drops his SmartAI, the actionlist and the gate conditions, and adds lines 1-6 and the Playmate's.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_stratholme_timmy.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Stratholme"
HEADER = MODULE_DIR / "TimmyLogic.h"
SCRIPT = MODULE_DIR / "boss_timmy_the_cruel_rework.cpp"
REWORK = MODULE_DIR / "StratholmeRework.h"
SQL_REV = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_timmy_the_cruel_stratholme.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "stratholme"

SLICE = range(206460, 206480)
(TAGGED, FROZEN, SHATTER, PATTY_CAKE, CLAP, JUMP_ROPE, JUMP_ROPE_FAST, TRIP, TRIPPED) = range(206460, 206469)
TIMMY, PLAYMATE = 10808, 300604
PLAYMATE_HEROIC = 310193
LEVEL_58_WARRIOR_BASE = 2871

SCHOOL_NORMAL, SCHOOL_FROST, SCHOOL_SHADOW = 1, 16, 32
SCHOOL_DAMAGE, APPLY_AURA = 2, 6
AURA_DUMMY, AURA_MOD_STUN, AURA_PERIODIC_DAMAGE, AURA_PERIODIC_TRIGGER_SPELL, AURA_MOD_DECREASE_SPEED = 4, 12, 3, 23, 33
ATTR0_NO_IMMUNITIES = 0x20000000
ATTR1_IS_SELF_CHANNELED = 0x40
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
AURA_INTERRUPT_CHANGE_MAP = 0x00080000
RESOLVE = "spell_boss_mechanics_resolve"
REFLAT_PERIODIC = "spell_dungeon_refflat_periodic"
TARGET_UNIT_SRC_AREA_ENEMY = 15

# The picks of source/npcs/stratholme/_visuals.py (WP-V-2, handoff s3.10).
LOOKS = {
    FROZEN: 2335,           # TM_FREEZE
    SHATTER: 17,            # MK_SHATTER
    CLAP: 145,              # TM_THUNDER_CLAP
    JUMP_ROPE: 9612,        # TM_SWEEP_BURST
    JUMP_ROPE_FAST: 9612,
    TRIPPED: 413,           # TM_TRIP
}


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


def _kickable(spell: dict) -> bool:
    """A kick or a silence stops it: InterruptFlags or ChannelInterruptFlags INTERRUPT (0x08), or PreventionType 1."""
    return bool(_raw(spell, "InterruptFlags") & 0x08 or _raw(spell, "ChannelInterruptFlags") & 0x08
                or _raw(spell, "PreventionType") == 1)


def _school_clash(spells: dict) -> list[tuple[int, int]]:
    """R-2-A A-3 (ORCH F-2 ruling): a kick locks the kicked cast's school, and a creature's untriggered cast in a
    locked school is refused. The (bar, kickable) pairs where a cast bar that must play (a cast time, not kickable)
    shares a school with one of the boss's kickable casts."""
    kickable = [s for s in spells.values() if _kickable(s)]
    bars = [s for s in spells.values() if int(s.get("cast_time_ms") or 0) > 0 and not _kickable(s)]
    return [(int(b["id"]), int(k["id"])) for b in bars for k in kickable if int(b["school"]) & int(k["school"])]


def _header() -> str:
    return HEADER.read_text(encoding="utf-8")


def _header_int(name: str) -> int:
    match = re.search(rf"\b{name}\s*=\s*(-?\d+);", _header())
    assert match, name
    return int(match.group(1))




class TimmyDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == PLAYMATE}
        cls.models = [m for m in reg.creature_template_models if int(m["CreatureID"]) == PLAYMATE]
        cls.edits = [e for e in reg.creature_template_edits if int(e["entry"]) == TIMMY]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.header = _header()

    def test_must_play_bars_never_share_a_kickable_school(self):
        self.assertTrue(_kickable(self.spells[PATTY_CAKE]))
        self.assertEqual(_school_clash(self.spells), [])
        for spell_id in (JUMP_ROPE, JUMP_ROPE_FAST):
            self.assertEqual(self.spells[spell_id]["school"], SCHOOL_SHADOW)
        # The yell and the emote go out with the first skip that really starts, never at the rope's queueing.
        start = self.cpp[self.cpp.index("bool StartRope(bool doubleDutch)"):self.cpp.index("void UpdateRope()")]
        self.assertNotIn("Talk(YELL_TIMMY_JUMP)", start)
        self.assertRegex(self.cpp, r"if \(_rope\.index == 0\)\s*\{\s*Talk\(YELL_TIMMY_JUMP\);\s*"
                                   r"Talk\(EMOTE_TIMMY_JUMP_ROPE\);\s*\}\s*RegisterSweep")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(TAGGED, TRIPPED + 1)))
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"spell": mine}), [])
        first = re.search(r"kSpellsTimmy\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(first)
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_TC_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", self.header)
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))
        # The stock kit stays stock (never re-declared).
        for stock in (12787, 17470, 8599):
            self.assertNotIn(stock, self.spells)
        for name in ("SPELL_RAVENOUS_CLAW", "SPELL_ENRAGE_TIMMY", "SPELL_THRASH"):
            self.assertIn(name, self.cpp)

    def test_the_playmate(self):
        self.assertEqual(sorted(self.creatures), [PLAYMATE])
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"creature": [PLAYMATE]}), [])
        mate = self.creatures[PLAYMATE]
        self.assertEqual(mate["ScriptName"], "npc_st_playmate")
        self.assertEqual(mate["difficulty_entry_1"], PLAYMATE_HEROIC)
        self.assertEqual(math.ceil(LEVEL_58_WARRIOR_BASE * mate["HealthModifier"]), 5000)
        self.assertEqual((mate["minlevel"], mate["maxlevel"]), (58, 58))
        self.assertEqual(mate["faction"], 21)
        self.assertEqual(mate["lootid"], 0)
        models = [(int(m["CreatureDisplayID"]), float(m["DisplayScale"])) for m in self.models]
        self.assertEqual(models, [(571, 0.8)])               # his white ghoul, a little smaller
        for name in ("boss_timmy_the_cruel_rework", "npc_st_playmate"):
            self.assertIn(f"RegisterDungeonReworkCreatureAI({name},", self.cpp)
        self.assertIn("RegisterSpellScript(spell_st_timmy_clap)", self.cpp)

    def test_the_hits_are_resolve_copies(self):
        for spell_id, school in ((SHATTER, SCHOOL_FROST), (TRIP, SCHOOL_NORMAL)):
            hit = self.spells[spell_id]
            self.assertEqual(hit["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertEqual(hit["school"], school, spell_id)
            self.assertTrue(_raw(hit, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
        self.assertIn("kShatterPct = 30.f", self.header)
        self.assertIn("kTripPct = 25.f", self.header)
        self.assertIn("spec.spellId = SPELL_TC_SHATTER;", self.cpp)
        self.assertIn("spec.weakened = true;", self.cpp)
        # One registry Jump per skip, its warning the cast; never a bare IsFalling test (X3).
        self.assertRegex(self.cpp, r"Mechanic::Jump\(me, center, kRopeRadius, Ms\(castMs\)\)")
        self.assertRegex(self.cpp, r"Spell\(SPELL_TC_TRIP\)\.Weakened\(\)\s*\.Rider\(SPELL_TC_TRIPPED\)")
        self.assertNotIn("IsFalling", self.cpp.replace("never a bare IsFalling test", ""))

    def test_frozen(self):
        frozen = self.spells[FROZEN]
        self.assertEqual(frozen["school"], SCHOOL_FROST)
        self.assertEqual(frozen["duration_ms"], _header_int("kFrozenMs"))
        self.assertGreater(frozen["duration_ms"], _header_int("kRoundMs"))
        self.assertEqual(frozen["dispel"], 0)
        self.assertEqual(frozen["mechanic"], 0)
        self.assertTrue(frozen["attributes"] & ATTR0_NO_IMMUNITIES)
        self.assertEqual(frozen["effect1"]["apply_aura"], AURA_MOD_DECREASE_SPEED)
        self.assertEqual(frozen["effect1"]["base_points"] + 1, -_header_int("kFrozenSlowPct"))
        self.assertEqual(frozen["effect2"]["apply_aura"], AURA_PERIODIC_DAMAGE)
        self.assertEqual(frozen["effect2"]["base_points"], 200)          # 2.00% in hundredths
        self.assertEqual(frozen["effect2"].get("die_sides", 0), 0)
        self.assertEqual(frozen["effect2"]["amplitude"], 1000)
        self.assertTrue(_raw(frozen, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertEqual(_raw(frozen, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)
        self.assertIn((FROZEN, REFLAT_PERIODIC), self.scripts)
        self.assertIn("kFrozenTickPct = 2.f", self.header)
        tagged = self.spells[TAGGED]
        self.assertEqual(tagged["duration_ms"], _header_int("kTagWarnMs"))
        self.assertEqual(tagged["effect1"]["apply_aura"], AURA_DUMMY)
        # The thaw is a lasting Soak for players without Frozen.
        self.assertIn("unfrozen.auraSpell = SPELL_TC_FROZEN;", self.cpp)
        self.assertIn("unfrozen.maxStacks = 0;", self.cpp)

    def test_patty_cake_is_a_kickable_channel_of_four_claps(self):
        channel = self.spells[PATTY_CAKE]
        self.assertEqual(channel["duration_ms"], _header_int("kPattyCakeMs"))
        self.assertTrue(_raw(channel, "AttributesEx") & ATTR1_IS_SELF_CHANNELED)
        self.assertEqual(_raw(channel, "ChannelInterruptFlags"), 0x08)
        self.assertEqual(_raw(channel, "PreventionType"), 1)
        self.assertEqual(channel["effect1"]["apply_aura"], AURA_PERIODIC_TRIGGER_SPELL)
        self.assertEqual(channel["effect1"]["amplitude"], _header_int("kClapEveryMs"))
        self.assertEqual(channel["effect1"]["trigger_spell"], CLAP)
        clap = self.spells[CLAP]
        self.assertEqual(clap["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertEqual(clap["effect1"]["implicit_target_b"], TARGET_UNIT_SRC_AREA_ENEMY)
        self.assertEqual(clap["effect1"]["base_points"] + 1, 1000)        # 10% in hundredths
        self.assertEqual(_raw(clap, "EffectMiscValueB_1"), 2000)          # heroic 20%
        self.assertIn("kClapPct{ 10.f, 20.f }", self.header)
        self.assertTrue(_raw(clap, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertIn((CLAP, "spell_st_timmy_clap"), self.scripts)
        # The script's filter hook matches the clap's implicit target.
        self.assertIn("EFFECT_0,\n            TARGET_UNIT_SRC_AREA_ENEMY)", self.cpp)
        self.assertIn("d.interrupts.emplace_back(NPC_TIMMY, SPELL_TC_PATTY_CAKE, 3,", self.cpp)
        self.assertIn("d.purges.emplace_back(NPC_TIMMY, SPELL_ENRAGE_TIMMY, 1)", self.cpp)
        self.assertIn("TargetEntry(NPC_ST_PLAYMATE, 2).AoeOk()", self.cpp)

    def test_the_rope(self):
        self.assertEqual(self.spells[JUMP_ROPE]["cast_time_ms"], _header_int("kSkipMs"))
        self.assertEqual(self.spells[JUMP_ROPE_FAST]["cast_time_ms"], _header_int("kFastSkipMs"))
        for spell_id in (JUMP_ROPE, JUMP_ROPE_FAST):
            self.assertEqual(_raw(self.spells[spell_id], "InterruptFlags"), 0)
            self.assertEqual(_raw(self.spells[spell_id], "PreventionType"), 0)
        tripped = self.spells[TRIPPED]
        self.assertEqual(tripped["duration_ms"], _header_int("kTrippedMs"))
        self.assertEqual(tripped["effect1"]["apply_aura"], AURA_MOD_STUN)
        self.assertEqual(_raw(tripped, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)

    def test_looks_are_the_visual_picks(self):
        for spell_id, visual in LOOKS.items():
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), visual, spell_id)

    def test_timmy_is_bound(self):
        self.assertEqual(len(self.edits), 1)
        edit = self.edits[0]
        self.assertEqual(edit["ScriptName"], "boss_timmy_the_cruel_rework")
        self.assertEqual(edit["AIName"], "")
        self.assertEqual(edit["HealthModifier"], 59.213)
        self.assertEqual(edit["DamageModifier"], 13)
        self.assertEqual(edit["CreatureImmunitiesId"], 1972)
        self.assertEqual(edit["flags_extra"] & 0x1, 0x1)
        self.assertAlmostEqual(59.213 * LEVEL_58_WARRIOR_BASE, 170_000, delta=100)

    def test_his_sql_rev(self):
        text = SQL_REV.read_text(encoding="utf-8")
        self.assertIn("DELETE FROM `smart_scripts` WHERE `entryorguid` = 10808 AND `source_type` = 0;", text)
        self.assertIn("DELETE FROM `smart_scripts` WHERE `entryorguid` = 1080800 AND `source_type` = 9;", text)
        self.assertIn("DELETE FROM `conditions` WHERE `SourceTypeOrReferenceId` = 22 AND `SourceEntry` = 10808", text)
        # Group 0 stays stock; 1-6 are new.
        self.assertIn("`CreatureID` = 10808 AND `GroupID` BETWEEN 1 AND 6;", text)
        rows = re.findall(r"^\(10808, (\d+), 0, '((?:[^'\\]|\\.|'')*)', (\d+),", text, re.M)
        self.assertEqual([int(r[0]) for r in rows], [1, 2, 3, 4, 5, 6])
        types = {int(r[0]): int(r[2]) for r in rows}
        self.assertEqual(types, {1: 14, 2: 41, 3: 14, 4: 14, 5: 41, 6: 14})
        self.assertIn("(300604, 0, 0, 'TIMMY!', 14,", text)
        rework = REWORK.read_text(encoding="utf-8")
        for name, group in (("YELL_TIMMY_AGGRO", 0), ("YELL_TIMMY_TAG", 1), ("EMOTE_TIMMY_CLAP", 2),
                            ("YELL_TIMMY_TIMMIES", 3), ("YELL_TIMMY_JUMP", 4), ("EMOTE_TIMMY_JUMP_ROPE", 5),
                            ("YELL_TIMMY_DEATH", 6)):
            match = re.search(rf"{name}\s*=\s*(\d+)", rework)
            self.assertIsNotNone(match, name)
            self.assertEqual(int(match.group(1)), group, name)


if __name__ == "__main__":
    unittest.main()
