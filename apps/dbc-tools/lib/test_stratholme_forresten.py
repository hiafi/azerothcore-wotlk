"""
Stratholme build WP-S2, Hearthsinger Forresten: source/npcs/stratholme/hearthsinger_forresten.py against its C++
(modules/mod-dungeon-bosses src/Stratholme/ForrestenLogic.h, boss_hearthsinger_forresten_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in his slice (206440-206459) and ForrestenLogic.h names the same ids;
  - the Gutter Rat 300602 (1,000 health on the level 57 warrior base, his faction, the three rat displays, its heroic
    row 310192) and the hearth stalker 300603 (a trigger, not selectable, no heroic row);
  - the note, the rat line and the big line are resolve copies bound to spell_boss_mechanics_resolve; Plague Bite is
    a stacking 10 s Disease on the kit's generic percent DoT (1% a second a stack); Drowsy stacks to 3; the sleep is a
    2 s stun with the sleep mechanic that damage does not break; the dance carries its script;
  - the Crescendo is a real 3 s cast that a kick or a silence stops;
  - the looks are WP-V-2's picks;
  - 10558 is bound to boss_hearthsinger_forresten_rework with SmartAI off, HealthModifier 62.859, DamageModifier 3.5
    and immunity set 1972;
  - the SQL rev drops his five SmartAI rows and gives him the six build spec lines (yells 14, the Crescendo emote 41).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_stratholme_forresten.py
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
HEADER = MODULE_DIR / "ForrestenLogic.h"
SCRIPT = MODULE_DIR / "boss_hearthsinger_forresten_rework.cpp"
REWORK = MODULE_DIR / "StratholmeRework.h"
SQL_REV = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_hearthsinger_forresten_stratholme.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "stratholme"

SLICE = range(206440, 206460)
(NOTE, DANCE, DROWSY, ASLEEP, RAT_LINE, CRESCENDO_LINE, CRESCENDO, PLAGUE_BITE, HEARTH_GLOW) = range(206440, 206449)
FORRESTEN, RAT, HEARTH = 10558, 300602, 300603
RAT_HEROIC = 310192
LEVEL_57_WARRIOR_BASE = 2784

SCHOOL_NORMAL, SCHOOL_NATURE, SCHOOL_ARCANE = 1, 8, 64
SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT = 2, 6, 3
AURA_DUMMY, AURA_MOD_STUN, AURA_PERIODIC_DAMAGE = 4, 12, 3
MECHANIC_SLEEP = 10
DISPEL_DISEASE = 3
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
AURA_INTERRUPT_CHANGE_MAP = 0x00080000
UNIT_FLAG_NOT_SELECTABLE = 0x02000000
CREATURE_FLAG_EXTRA_TRIGGER = 0x80
RESOLVE = "spell_boss_mechanics_resolve"
REFLAT_PERIODIC = "spell_dungeon_refflat_periodic"

# The picks of source/npcs/stratholme/_visuals.py (WP-V-2, handoff s3.10).
LOOKS = {
    NOTE: 11381,            # FO_LISTENING_MUSIC
    DROWSY: 4999,           # FO_DROWSY_ALT
    ASLEEP: 87,             # FO_DROWSY
    RAT_LINE: 39,           # RG_GORE
    CRESCENDO_LINE: 371,    # FO_SIREN_SONG
    CRESCENDO: 371,
    PLAGUE_BITE: 717,       # FO_BLACK_ROT
    HEARTH_GLOW: 90508,     # SV_FLAMEZONE_8_STATE
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


def _header() -> str:
    return HEADER.read_text(encoding="utf-8")


def _header_pair(name: str) -> tuple[int, int]:
    match = re.search(rf"{name}\{{\s*(\d+),\s*(\d+)\s*\}}", _header())
    assert match, name
    return int(match.group(1)), int(match.group(2))


def _header_int(name: str) -> int:
    match = re.search(rf"\b{name}\s*=\s*(-?\d+);", _header())
    assert match, name
    return int(match.group(1))


class ForrestenDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) in (RAT, HEARTH)}
        cls.models = [m for m in reg.creature_template_models if int(m["CreatureID"]) in (RAT, HEARTH)]
        cls.edits = [e for e in reg.creature_template_edits if int(e["entry"]) == FORRESTEN]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.header = _header()

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(NOTE, HEARTH_GLOW + 1)))
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"spell": mine}), [])
        first = re.search(r"kSpellsForresten\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(first)
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_HF_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", self.header)
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))
        # The retired stock kit is never re-declared; the bow stays stock.
        for retired in (16244, 16798, 16331):
            self.assertNotIn(retired, self.spells)
        self.assertIn("SPELL_SHOOT_FORRESTEN", self.cpp)
        self.assertIn("SPELL_MULTI_SHOT", self.cpp)

    def test_the_rat_and_the_hearth_stalker(self):
        self.assertEqual(sorted(self.creatures), [RAT, HEARTH])
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"creature": [RAT, HEARTH]}), [])
        rat = self.creatures[RAT]
        self.assertEqual(rat["ScriptName"], "npc_st_gutter_rat")
        self.assertEqual(rat["difficulty_entry_1"], RAT_HEROIC)
        self.assertEqual(math.ceil(LEVEL_57_WARRIOR_BASE * rat["HealthModifier"]), 1000)
        self.assertEqual((rat["minlevel"], rat["maxlevel"]), (57, 57))
        self.assertEqual(rat["faction"], 7)                  # his own faction
        self.assertEqual(rat["lootid"], 0)
        rat_models = sorted((int(m["Idx"]), int(m["CreatureDisplayID"])) for m in self.models
                            if int(m["CreatureID"]) == RAT)
        self.assertEqual(rat_models, [(0, 1141), (1, 1418), (2, 2176)])      # the Plagued Rat's three skins
        stalker = self.creatures[HEARTH]
        self.assertEqual(stalker["ScriptName"], "npc_st_hearth_stalker")
        self.assertTrue(stalker["unit_flags"] & UNIT_FLAG_NOT_SELECTABLE)
        self.assertTrue(stalker["flags_extra"] & CREATURE_FLAG_EXTRA_TRIGGER)
        self.assertEqual(stalker.get("difficulty_entry_1", 0), 0)
        for name in ("boss_hearthsinger_forresten_rework", "npc_st_gutter_rat", "npc_st_hearth_stalker"):
            self.assertIn(f"RegisterDungeonReworkCreatureAI({name},", self.cpp)
        self.assertIn("RegisterSpellScript(spell_st_forresten_dance)", self.cpp)

    def test_the_hits_are_resolve_copies(self):
        for spell_id, school in ((NOTE, SCHOOL_ARCANE), (RAT_LINE, SCHOOL_NORMAL), (CRESCENDO_LINE, SCHOOL_NORMAL)):
            hit = self.spells[spell_id]
            self.assertEqual(hit["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertEqual(hit["school"], school, spell_id)
            self.assertTrue(_raw(hit, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
        # The numbers of the build spec, Weakened on every one (each under 50%), and the note's rider.
        self.assertIn("kNotePct = 20.f", self.header)
        self.assertIn("kRatLinePct = 15.f", self.header)
        self.assertIn("kBigLinePct = 30.f", self.header)
        self.assertRegex(self.cpp, r"Damage\(kNotePct\)\.TankDamage\(kNotePct\)\.School\(SPELL_SCHOOL_ARCANE\)"
                                   r"\.Spell\(SPELL_HF_NOTE\)\.Weakened\(\)\s*\.Rider\(SPELL_HF_DANCE\)")
        self.assertRegex(self.cpp, r"Spell\(SPELL_HF_RAT_LINE\)\.Weakened\(\)")
        self.assertRegex(self.cpp, r"Spell\(SPELL_HF_CRESCENDO_LINE\)\s*\.Weakened\(\)")

    def test_the_rat_line_is_a_tracked_out_and_back_projectile(self):
        self.assertRegex(self.cpp, r"Projectile\(kRatLineSpeed\)\.ProjectileUnit\(rat\)\.OutAndBack\(\)")
        self.assertEqual(_header_int("kRatLineWarnMs"), 2000)
        self.assertEqual(_header_int("kVolleyLineEveryMs"), 500)
        self.assertEqual(_header_int("kVolleyFirstMs"), 4000)
        # The line is capped at 30 yd and a rat's declared speed is under its real one.
        self.assertIn("kRatLineCapYd = 30.f", self.header)
        self.assertIn("static_assert(kRatLineSpeed < kRatRunSpeed", self.header)

    def test_plague_bite(self):
        bite = self.spells[PLAGUE_BITE]
        self.assertEqual(bite["duration_ms"], _header_int("kBiteMs"))
        self.assertEqual(bite["duration_ms"], 10000)
        self.assertEqual(bite["dispel"], DISPEL_DISEASE)
        self.assertEqual(bite["school"], SCHOOL_NATURE)
        self.assertEqual(bite["effect1"]["apply_aura"], AURA_PERIODIC_DAMAGE)
        self.assertEqual(bite["effect1"]["base_points"], 100)           # 1.00% in hundredths
        self.assertEqual(bite["effect1"].get("die_sides", 0), 0)
        self.assertEqual(bite["effect1"]["amplitude"], 1000)             # every second
        self.assertEqual(_raw(bite, "CumulativeAura"), _header_int("kBiteMaxStacks"))
        self.assertEqual(_raw(bite, "CumulativeAura"), 5)
        self.assertTrue(_raw(bite, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertEqual(_raw(bite, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)
        self.assertIn((PLAGUE_BITE, REFLAT_PERIODIC), self.scripts)
        # The stacks are the boss's own (he is the caster), and the dispel list names the aura.
        self.assertIn("DungeonKit::AddStacks(victim, SPELL_HF_PLAGUE_BITE, 1, caster, kBiteMaxStacks)", self.cpp)
        self.assertIn("d.dispels.emplace_back(SPELL_HF_PLAGUE_BITE, 1)", self.cpp)

    def test_drowsy_and_the_sleep(self):
        drowsy = self.spells[DROWSY]
        self.assertEqual(drowsy["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(drowsy["dispel"], 0)
        self.assertEqual(_raw(drowsy, "CumulativeAura"), 3)
        self.assertEqual(_raw(drowsy, "CumulativeAura"), _header_int("kDrowsyToSleep"))
        self.assertEqual(drowsy["duration_ms"], _header_int("kDrowsyMs"))
        self.assertEqual(_raw(drowsy, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)
        asleep = self.spells[ASLEEP]
        self.assertEqual(asleep["duration_ms"], _header_int("kSleepMs"))
        self.assertEqual(asleep["duration_ms"], 2000)
        self.assertEqual(asleep["effect1"]["apply_aura"], AURA_MOD_STUN)
        self.assertEqual(asleep["effect1"]["mechanic"], MECHANIC_SLEEP)
        self.assertEqual(asleep["mechanic"], MECHANIC_SLEEP)
        self.assertEqual(asleep["dispel"], 0)
        # Damage does not wake it: only the map change interrupt flag.
        self.assertEqual(_raw(asleep, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)
        self.assertEqual(_header_int("kDrowsyTickMs"), 2000)

    def test_the_dance_has_its_script(self):
        dance = self.spells[DANCE]
        self.assertEqual(dance["duration_ms"], _header_int("kDanceMs"))
        self.assertEqual(dance["duration_ms"], 1500)
        self.assertEqual(dance["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertIn((DANCE, "spell_st_forresten_dance"), self.scripts)
        self.assertIn("class spell_st_forresten_dance : public AuraScript", self.cpp)
        self.assertEqual(_header_int("kEmoteStateDance"), 10)
        self.assertEqual(_raw(dance, "SpellVisualID_1"), 0)      # Piccolo's SV 4682 is a sound only: never wired

    def test_the_crescendo_is_a_kickable_cast(self):
        cast = self.spells[CRESCENDO]
        self.assertEqual(cast["cast_time_ms"], _header_int("kCrescendoCastMs"))
        self.assertEqual(cast["cast_time_ms"], 3000)
        self.assertEqual(_raw(cast, "InterruptFlags"), 15)
        self.assertEqual(_raw(cast, "PreventionType"), 1)
        self.assertEqual(cast["effect1"]["type"], DUMMY_EFFECT)
        self.assertEqual(_header_pair("kCrescendoWindowMs"), (5000, 12000))
        # The interrupt list (top priority, once per song + break) and the completion hook.
        self.assertIn("SPELL_HF_CRESCENDO, 3, Ms(kSongMs(_heroic) + kBreakMs(_heroic))", self.cpp)
        self.assertIn("void OnSpellCast(SpellInfo const* spell) override", self.cpp)
        self.assertIn("void OnSpellFailed(SpellInfo const* spell) override", self.cpp)

    def test_hearth_glow(self):
        glow = self.spells[HEARTH_GLOW]
        self.assertEqual(glow["duration_ms"], -1)
        self.assertEqual(glow["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertIn("kHearthRadius = 8.f", self.header)

    def test_looks_are_the_visual_picks(self):
        for spell_id, visual in LOOKS.items():
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), visual, spell_id)

    def test_forresten_is_bound(self):
        self.assertEqual(len(self.edits), 1)
        edit = self.edits[0]
        self.assertEqual(edit["ScriptName"], "boss_hearthsinger_forresten_rework")
        self.assertEqual(edit["AIName"], "")
        self.assertEqual(edit["HealthModifier"], 62.859)
        self.assertEqual(edit["DamageModifier"], 3.5)
        self.assertEqual(edit["CreatureImmunitiesId"], 1972)
        self.assertEqual(edit["flags_extra"] & 0x1, 0x1)
        # 175k on the level 57 warrior base 2,784.
        self.assertAlmostEqual(62.859 * LEVEL_57_WARRIOR_BASE, 175_000, delta=100)

    def test_his_sql_rev(self):
        text = SQL_REV.read_text(encoding="utf-8")
        self.assertIn("DELETE FROM `smart_scripts` WHERE `entryorguid` = 10558 AND `source_type` = 0;", text)
        rows = re.findall(r"^\(10558, (\d+), 0, '((?:[^'\\]|\\.|'')*)', (\d+),", text, re.M)
        self.assertEqual([int(r[0]) for r in rows], [0, 1, 2, 3, 4, 5])
        types = {int(r[0]): int(r[2]) for r in rows}
        self.assertEqual(types, {0: 14, 1: 14, 2: 14, 3: 14, 4: 41, 5: 14})
        by_group = {int(r[0]): r[1] for r in rows}
        self.assertEqual(by_group[1], "Something lively! On your feet, everyone, dance!")
        self.assertEqual(by_group[2], "Hush now. Gather round the hearth.")
        self.assertEqual(by_group[4], "%s builds toward a crescendo!")
        # The enum in StratholmeRework.h numbers the same groups.
        for name, group in (("YELL_FORRESTEN_AGGRO", 0), ("YELL_FORRESTEN_JIG", 1), ("YELL_FORRESTEN_LULLABY", 2),
                            ("YELL_FORRESTEN_PIPER", 3), ("EMOTE_FORRESTEN_CRESCENDO", 4),
                            ("YELL_FORRESTEN_DEATH", 5)):
            match = re.search(rf"{name}\s*=\s*(\d+)", REWORK.read_text(encoding="utf-8"))
            self.assertIsNotNone(match, name)
            self.assertEqual(int(match.group(1)), group, name)


if __name__ == "__main__":
    unittest.main()
