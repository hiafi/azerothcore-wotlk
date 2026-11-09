"""
Stratholme build WP-S4, Malor the Zealous: source/npcs/stratholme/malor_the_zealous.py against its C++
(modules/mod-dungeon-bosses src/Stratholme/MalorLogic.h, boss_malor_the_zealous_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in Malor's slice (206480-206499), MalorLogic.h names the same ids, and the Medallion stalker 300605
    is the one creature (an invisible, unselectable trigger with no heroic template);
  - the blaze is a 12 s channel; Faith is +5% damage done per stack with 10 stacks, Searing Faith a periodic Holy
    DoT at 2% (heroic 3%) with 12 stacks, both for the AI's clock (no duration), Unclean an 8 s debuff;
  - Judgment, Searing Faith's ticks carry the header's percents through the kit's generic percent spells;
  - the Smash bar is 2 s and not kickable, Holy Light a 2.5 s kickable cast, the Miracle a 3 s bar that is not;
  - the Smash and Aftershock hits are resolve copies; the heals are exact amounts from the script;
  - auras that must not survive a map change carry CHANGE_MAP;
  - the looks are V-2's ML_ picks;
  - 11032 is bound to boss_malor_the_zealous_rework with SmartAI off, HealthModifier 71.663, DamageModifier 3.5 and
    immunity set 1972;
  - the SQL rev gives him the six build spec lines (yells 14, mechanic emotes 41) and drops the four SmartAI rows.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_stratholme_malor.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Stratholme"
HEADER = MODULE_DIR / "MalorLogic.h"
SCRIPT = MODULE_DIR / "boss_malor_the_zealous_rework.cpp"
SQL_REV = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_malor_stratholme.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "stratholme"

SLICE = range(206480, 206500)
(BLAZE, FAITH, SEARING, SEARING_LOOK, UNCLEAN, JUDGMENT, SMASH_BAR, SMASH_HIT, STUNNED, AFTERSHOCK_HIT, HOLY_LIGHT,
 HOLY_LIGHT_HEAL, MIRACLE, MIRACLE_HEAL) = range(206480, 206494)
STALKER = 300605
MALOR = 11032

SCHOOL_HOLY, SCHOOL_PHYSICAL = 2, 1
SCHOOL_DAMAGE, APPLY_AURA, HEAL = 2, 6, 10
AURA_DUMMY, AURA_PERIODIC_DAMAGE, AURA_MOD_STUN, AURA_MOD_DAMAGE_PERCENT_DONE = 4, 3, 12, 79
MECHANIC_STUN = 12
ATTR0_AURA_IS_DEBUFF = 0x04000000
ATTR0_NO_IMMUNITIES = 0x20000000
ATTR1_IS_CHANNELED = 0x00000004
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
AURA_INTERRUPT_CHANGE_MAP = 0x00080000
UNIT_FLAG_NOT_SELECTABLE = 0x02000000
CREATURE_FLAG_EXTRA_TRIGGER = 0x80
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT = "spell_dungeon_refflat_damage"
REFFLAT_PERIODIC = "spell_dungeon_refflat_periodic"

# V-2's picks (source/npcs/stratholme/_visuals.py ML_*) and the Holy Light SV that has no ML_ name.
LOOKS = {
    BLAZE: 11500,           # ML_BLAZE_BEAM
    FAITH: 211,             # ML_ZEAL
    SEARING_LOOK: 3400,     # ML_HOLY_FIRE
    UNCLEAN: 339,           # ML_TAINTED_MIND
    JUDGMENT: 5651,         # ML_JUDGMENT
    SMASH_HIT: 9612,        # ML_SMASH_BURST
    AFTERSHOCK_HIT: 9612,
    HOLY_LIGHT: 2936,       # Holy Light 635
    HOLY_LIGHT_HEAL: 2936,
    MIRACLE: 132,           # ML_LAY_ON_HANDS
    MIRACLE_HEAL: 132,
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


def _header_number(name: str) -> float:
    match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f?;", _header())
    assert match, name
    return float(match.group(1))


def _header_nh(name: str) -> tuple[float, float]:
    match = re.search(rf"\b{name}\{{\s*(-?[\d.]+)f?,\s*(-?[\d.]+)f?\s*\}}", _header())
    assert match, name
    return float(match.group(1)), float(match.group(2))


class MalorDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == STALKER}
        cls.edits = [e for e in reg.creature_template_edits if int(e["entry"]) == MALOR]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(BLAZE, MIRACLE_HEAL + 1)))
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"spell": mine}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_MZ_\w+\s*=\s*kSpellSlice\.first \+ (\d+)", _header())}
        self.assertEqual({BLAZE + n for n in header_ids}, set(mine))
        # His stock kit is retired, never re-declared (ids below the custom range).
        for retired in (12734, 16172, 10310, 15493):
            self.assertNotIn(retired, self.spells)

    def test_the_medallion_stalker(self):
        self.assertEqual(sorted(self.creatures), [STALKER])
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"creature": [STALKER]}), [])
        stalker = self.creatures[STALKER]
        self.assertTrue(stalker["unit_flags"] & UNIT_FLAG_NOT_SELECTABLE)
        self.assertTrue(stalker["flags_extra"] & CREATURE_FLAG_EXTRA_TRIGGER)
        self.assertEqual(stalker.get("difficulty_entry_1", 0), 0)       # not a combat add: no heroic template
        self.assertEqual(stalker["ScriptName"], "")
        self.assertEqual(stalker["lootid"], 0)
        self.assertIn("NPC_ST_MEDALLION", self.cpp)
        self.assertIn("SummonCreature(NPC_ST_MEDALLION", self.cpp)

    def test_the_blaze_and_unclean(self):
        blaze = self.spells[BLAZE]
        self.assertEqual(blaze["duration_ms"], int(_header_number("kBlazeMs")))
        self.assertEqual(blaze["duration_ms"], 12000)
        self.assertTrue(_raw(blaze, "AttributesEx") & ATTR1_IS_CHANNELED)
        self.assertEqual(_raw(blaze, "InterruptFlags"), 0)
        self.assertEqual(_raw(blaze, "ChannelInterruptFlags"), 0)
        self.assertEqual(blaze["effect1"]["apply_aura"], AURA_DUMMY)
        unclean = self.spells[UNCLEAN]
        self.assertEqual(unclean["duration_ms"], int(_header_number("kUncleanMs")))
        self.assertEqual(unclean["duration_ms"], 8000)
        self.assertEqual(unclean["dispel"], 0)
        self.assertTrue(unclean["attributes"] & ATTR0_AURA_IS_DEBUFF)
        self.assertTrue(unclean["attributes"] & ATTR0_NO_IMMUNITIES)
        self.assertEqual(unclean["effect1"]["apply_aura"], AURA_DUMMY)

    def test_faith(self):
        faith = self.spells[FAITH]
        self.assertEqual(faith["duration_ms"], -1)              # the AI's clock fades it
        self.assertEqual(faith["effect1"]["apply_aura"], AURA_MOD_DAMAGE_PERCENT_DONE)
        self.assertEqual(faith["effect1"]["base_points"], int(_header_number("kFaithDamagePct")))
        self.assertEqual(_raw(faith, "CumulativeAura"), int(_header_number("kFaithMax")))
        self.assertEqual(faith["dispel"], 0)
        self.assertTrue(faith["attributes"] & ATTR0_NO_IMMUNITIES)
        self.assertFalse(faith["attributes"] & ATTR0_AURA_IS_DEBUFF)    # a buff on him

    def test_searing_faith(self):
        searing = self.spells[SEARING]
        normal, heroic = _header_nh("kSearingPct")
        self.assertEqual(searing["duration_ms"], -1)
        self.assertEqual(searing["school"], SCHOOL_HOLY)
        self.assertEqual(searing["dispel"], 0)
        tick = searing["effect1"]
        self.assertEqual(tick["apply_aura"], AURA_PERIODIC_DAMAGE)
        self.assertEqual(tick["amplitude"], int(_header_number("kBlazeTickMs")))
        self.assertEqual(tick["base_points"] + 1, round(normal * 100))
        self.assertEqual(_raw(searing, "EffectMiscValueB_1"), round(heroic * 100))
        self.assertEqual(_raw(searing, "CumulativeAura"), int(_header_number("kSearingMaxStacks")))
        self.assertTrue(_raw(searing, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertIn((SEARING, REFFLAT_PERIODIC), self.scripts)
        # The blaze is 12 s long: a stack a second, so 12 stacks is the longest a blocker can hold.
        self.assertEqual(int(_header_number("kSearingMaxStacks")),
                         int(_header_number("kBlazeMs") // _header_number("kBlazeTickMs")))

    def test_judgment_carries_the_percent(self):
        judgment = self.spells[JUDGMENT]
        normal, heroic = _header_nh("kJudgmentPct")
        self.assertEqual(judgment["school"], SCHOOL_HOLY)
        self.assertEqual(judgment["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertEqual(judgment["effect1"]["base_points"] + 1, round(normal * 100))
        self.assertEqual(_raw(judgment, "EffectMiscValueB_1"), round(heroic * 100))
        self.assertTrue(_raw(judgment, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertIn((JUDGMENT, REFFLAT), self.scripts)
        # No Weakened on a single-target hit (ST MZ6): the script casts it directly.
        self.assertIn("SPELL_MZ_JUDGMENT, TRIGGERED_FULL_MASK", self.cpp)

    def test_smash_and_aftershock(self):
        bar = self.spells[SMASH_BAR]
        self.assertEqual(bar["cast_time_ms"], int(_header_number("kSmashCastMs")))
        self.assertEqual(bar["cast_time_ms"], 2000)
        self.assertEqual(_raw(bar, "InterruptFlags"), 0)
        self.assertEqual(_raw(bar, "PreventionType"), 0)
        for spell_id in (SMASH_HIT, AFTERSHOCK_HIT):
            hit = self.spells[spell_id]
            self.assertEqual(hit["effect1"]["type"], SCHOOL_DAMAGE)
            self.assertEqual(hit["school"], SCHOOL_PHYSICAL)
            self.assertTrue(_raw(hit, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
            self.assertIn((spell_id, RESOLVE), self.scripts)
        stun = self.spells[STUNNED]
        self.assertEqual(stun["duration_ms"], int(_header_number("kSmashStunMs")))
        self.assertEqual(stun["duration_ms"], 1000)
        self.assertEqual(stun["effect1"]["apply_aura"], AURA_MOD_STUN)
        self.assertEqual(stun["mechanic"], MECHANIC_STUN)
        # The registry call: the circle with the tank row, Weakened and the stun rider; the heroic ring chained after.
        self.assertRegex(self.cpp, r"Spell\(SPELL_MZ_SMASH_HIT\)\.Weakened\(\)\s*\.Rider\(SPELL_MZ_STUNNED\)")
        self.assertIn("TankDamage(kSmashPct)", self.cpp)
        self.assertRegex(self.cpp, r"Spell\(SPELL_MZ_AFTERSHOCK_HIT\)\.Weakened\(\)")
        self.assertIn("Mechanic::Donut(me, me, kAftershockInner, kAftershockOuter", self.cpp)
        self.assertIn("if (heroic)\n            ref.OnResolve", self.cpp)

    def test_holy_light_and_the_miracle(self):
        light = self.spells[HOLY_LIGHT]
        self.assertEqual(light["cast_time_ms"], int(_header_number("kHolyLightCastMs")))
        self.assertEqual(light["cast_time_ms"], 2500)
        self.assertEqual(_raw(light, "InterruptFlags"), 15)
        self.assertEqual(_raw(light, "PreventionType"), 1)
        miracle = self.spells[MIRACLE]
        self.assertEqual(miracle["cast_time_ms"], int(_header_number("kMiracleCastMs")))
        self.assertEqual(miracle["cast_time_ms"], 3000)
        self.assertEqual(_raw(miracle, "InterruptFlags"), 0)        # not interruptible
        self.assertEqual(_raw(miracle, "PreventionType"), 0)
        # The descriptor lists Holy Light: a reward on normal, expected on heroic.
        self.assertEqual(_header_nh("kHolyLightKickPriority"), (1.0, 3.0))
        self.assertIn("SPELL_MZ_HOLY_LIGHT, kHolyLightKickPriority(heroic)", self.cpp)
        self.assertIn("void OnSpellCast(SpellInfo const* spell) override", self.cpp)
        for spell_id in (HOLY_LIGHT_HEAL, MIRACLE_HEAL):
            heal = self.spells[spell_id]
            self.assertEqual(heal["effect1"]["type"], HEAL)
            self.assertEqual(heal["effect1"]["base_points"], 0)
            self.assertEqual(heal["effect1"].get("die_sides", 0), 0)
            self.assertTrue(_raw(heal, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertIn("SPELL_MZ_HOLY_LIGHT_HEAL, SPELLVALUE_BASE_POINT0", self.cpp)
        self.assertIn("SPELL_MZ_MIRACLE_HEAL, SPELLVALUE_BASE_POINT0", self.cpp)
        self.assertEqual(_header_nh("kHolyLightBasePct"), (0.0, 3.0))
        self.assertEqual(_header_number("kMiracleHealPerStackPct"), 8.0)

    def test_scripts_and_map_changes(self):
        own = {name for _, name in self.scripts}
        self.assertEqual(own, {RESOLVE, REFFLAT, REFFLAT_PERIODIC})
        for spell_id in (SEARING, UNCLEAN, STUNNED):
            self.assertTrue(_raw(self.spells[spell_id], "AuraInterruptFlags") & AURA_INTERRUPT_CHANGE_MAP, spell_id)

    def test_looks_are_the_visual_picks(self):
        for spell_id, visual in LOOKS.items():
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), visual, spell_id)
        visuals = (PACKAGE / "_visuals.py").read_text(encoding="utf-8")
        for name, value in (("ML_BLAZE_BEAM", 11500), ("ML_ZEAL", 211), ("ML_HOLY_FIRE", 3400),
                            ("ML_TAINTED_MIND", 339), ("ML_JUDGMENT", 5651), ("ML_LAY_ON_HANDS", 132),
                            ("ML_SMASH_BURST", 9612)):
            self.assertIsNotNone(re.search(rf"^{name}\s*=\s*{value}\b", visuals, re.M), name)

    def test_malor_is_bound(self):
        self.assertEqual(len(self.edits), 1)
        edit = self.edits[0]
        self.assertEqual(edit["ScriptName"], "boss_malor_the_zealous_rework")
        self.assertEqual(edit["AIName"], "")
        self.assertEqual(edit["HealthModifier"], 71.663)
        self.assertEqual(edit["DamageModifier"], 3.5)
        self.assertEqual(edit["CreatureImmunitiesId"], 1972)
        self.assertEqual(edit["flags_extra"] & 0x1, 0x1)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_malor_the_zealous_rework", self.cpp)
        # 175k on the level 60 paladin base 2,442.
        self.assertAlmostEqual(71.663 * 2442, 175_000, delta=100)

    def test_his_texts_and_stock_rows(self):
        text = SQL_REV.read_text(encoding="utf-8")
        rows = re.findall(r"^\(11032, (\d+), 0, '((?:[^'\\]|'')*)', (\d+),", text, re.M)
        self.assertEqual([int(r[0]) for r in rows], [0, 1, 2, 3, 4, 5])
        types = {int(r[0]): int(r[2]) for r in rows}
        self.assertEqual(types, {0: 14, 1: 41, 2: 14, 3: 41, 4: 14, 5: 14})
        by_group = {int(r[0]): r[1] for r in rows}
        self.assertEqual(by_group[2], "Unclean! I can smell the plague on you!")
        self.assertEqual(by_group[3], "%s raises his warhammer high!")
        for name, group in (("YELL_MALOR_AGGRO", 0), ("EMOTE_MALOR_MEDALLION", 1), ("YELL_MALOR_UNCLEAN", 2),
                            ("EMOTE_MALOR_WARHAMMER", 3), ("YELL_MALOR_STRENGTH", 4), ("YELL_MALOR_DEATH", 5)):
            match = re.search(rf"{name}\s*=\s*(\d+)", (MODULE_DIR / "StratholmeRework.h").read_text(encoding="utf-8"))
            self.assertIsNotNone(match, name)
            self.assertEqual(int(match.group(1)), group, name)
        # The four SmartAI rows go (Ground Smash, Head Crack, Holy Light, Lay on Hands).
        self.assertIn("DELETE FROM `smart_scripts` WHERE `entryorguid` = 11032 AND `source_type` = 0;", text)
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 11032;", text)


if __name__ == "__main__":
    unittest.main()
