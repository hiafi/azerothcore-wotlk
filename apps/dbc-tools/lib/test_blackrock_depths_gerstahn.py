"""
Blackrock Depths build WP-D1, High Interrogator Gerstahn: source/npcs/blackrock_depths/gerstahn.py against its C++
(modules/mod-dungeon-bosses src/BlackrockDepths/GerstahnLogic.h, boss_high_interrogator_gerstahn_rework.cpp) and its
SQL rev.

Checks:
  - the spells sit in her slice (210720-210749) and GerstahnLogic.h names the same ids;
  - Gerstahn 9018 is bound (SmartAI off) at 140k on the level 52 paladin base, stun immune, INSTANCE_BIND;
  - Doubt stacks to the header's break count with no duration and no dispel; the swirl and Broken carry V-1's looks;
    Broken is a 2 s fear;
  - the DoTs (Shadow Word: Pain, Mind Flay, Dread) carry the header's percents (hundredths, heroic in
    EffectMiscValueB), ticks and durations and her periodic script; Shadow Word: Pain is Magic with the dispel script;
    Mind Flay is a kickable channel, never dispellable;
  - the Circle's bar is not interruptible, not Shadow and lasts the header's 2.5 s; its hit is a Shadow resolve copy;
  - the sear tick carries the header's percents and her damage script; Shadow Shield absorbs the header's amounts and
    is Magic; Knowledge is +10% damage done;
  - no stock id of her old kit is cast by the rework, and the looks are V-1's;
  - the SQL rev writes the five texts (yells and boss emotes) and touches nothing else.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_gerstahn.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockDepths"
HEADER = MODULE_DIR / "GerstahnLogic.h"
REWORK = MODULE_DIR / "BlackrockDepthsRework.h"
SCRIPT = MODULE_DIR / "boss_high_interrogator_gerstahn_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_gerstahn_blackrock_depths.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_depths"

SLICE = range(210720, 210750)
(DOUBT, SWIRL, BROKEN, DREAD, KNOWLEDGE, PAIN, FLAY, CIRCLE_CAST, CIRCLE, SEAR, SEAR_TICK, SHIELD, SHIELD_HEROIC,
 LINGERING) = range(210720, 210734)
GERSTAHN = 9018
PALADIN_52_BASE = 1897      # creature_classlevelstats level 52 class 2 basehp0

SCHOOL_SHADOW, SCHOOL_ARCANE = 32, 64
SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT = 2, 6, 3
AURA_DUMMY, AURA_PERIODIC_DAMAGE, AURA_MOD_FEAR, AURA_DAMAGE_SHIELD = 4, 3, 7, 15
AURA_SCHOOL_ABSORB, AURA_MOD_DAMAGE_PERCENT_DONE = 69, 79
MECHANIC_FEAR = 5
DISPEL_MAGIC = 1
ATTR1_IS_CHANNELED = 0x4
CHANNEL_INTERRUPT_KICK = 0x8
AURA_INTERRUPT_CHANGE_MAP = 0x00080000
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
RESOLVE = "spell_boss_mechanics_resolve"
PERIODIC = "spell_brd_gerstahn_periodic"
PAIN_SCRIPT = "spell_brd_gerstahn_shadow_word_pain"
DAMAGE = "spell_brd_gerstahn_damage"
# V-1's picks (_visuals.py): the swirl, Broken / the burst, Mind Flay, Mind Sear, Shadow Word: Pain, the pool.
SV_SWIRL, SV_SCREAM, SV_FLAY, SV_SEAR, SV_PAIN, SV_POOL = 7433, 247, 277, 12121, 71, 90605
STOCK_KIT = (14032, 14033, 13704, 12040)


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


def _raw(spell: dict, column: str) -> int | float:
    return (spell.get("raw_overrides") or {}).get(column, 0) or 0


def _header() -> str:
    return HEADER.read_text(encoding="utf-8")


def _header_value(name: str) -> float:
    match = re.search(rf"{name}\s*=\s*(-?[\d.]+)f?;", _header())
    assert match, name
    return float(match.group(1))


def _nh_values(name: str) -> tuple[float, float]:
    match = re.search(rf"{name}\{{\s*(-?[\d.]+)f?,\s*(-?[\d.]+)f?\s*\}}", _header())
    assert match, name
    return float(match.group(1)), float(match.group(2))


class GerstahnDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) == GERSTAHN}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(DOUBT, LINGERING + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"spell": mine}), [])
        first = re.search(r"kSpellsGerstahn\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(first)
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_GE_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))

    def test_gerstahn_is_bound(self):
        boss = self.edits[GERSTAHN]
        self.assertEqual(boss["ScriptName"], "boss_high_interrogator_gerstahn_rework")
        self.assertEqual(boss["AIName"], "")
        # 140k at 5 players (the build spec), within 2 HP.
        self.assertLessEqual(abs(math.ceil(PALADIN_52_BASE * boss["HealthModifier"]) - 140000), 2)
        self.assertEqual(boss["CreatureImmunitiesId"], 1972)
        self.assertEqual(boss["flags_extra"], 1)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_high_interrogator_gerstahn_rework,", self.cpp)
        for name in ("spell_brd_gerstahn_periodic", "spell_brd_gerstahn_shadow_word_pain", "spell_brd_gerstahn_damage"):
            self.assertIn(f"RegisterSpellScript({name})", self.cpp)
        self.assertIn('BrdTest::RegisterBoss("gerstahn"', self.cpp)

    def test_doubt_swirl_and_broken(self):
        doubt = self.spells[DOUBT]
        self.assertEqual(doubt["name"], "Doubt")
        self.assertEqual(doubt["dispel"], 0)
        self.assertEqual(doubt["duration_ms"], -1)
        self.assertEqual(doubt["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(_raw(doubt, "CumulativeAura"), int(_header_value("kDoubtBreakAt")))
        self.assertEqual(_raw(doubt, "CumulativeAura"), 5)
        self.assertEqual(_raw(doubt, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)
        swirl = self.spells[SWIRL]
        self.assertEqual(swirl["duration_ms"], -1)
        self.assertEqual(swirl["dispel"], 0)
        self.assertEqual(_raw(swirl, "SpellVisualID_1"), SV_SWIRL)
        broken = self.spells[BROKEN]
        self.assertEqual(broken["effect1"]["apply_aura"], AURA_MOD_FEAR)
        self.assertEqual(broken["mechanic"], MECHANIC_FEAR)
        self.assertEqual(broken["duration_ms"], int(_header_value("kBrokenMs")))
        self.assertEqual(broken["duration_ms"], 2000)       # the shared doc's 2 s limit
        self.assertEqual(broken["dispel"], 0)
        self.assertEqual(_raw(broken, "SpellVisualID_1"), SV_SCREAM)

    def test_the_dots(self):
        cases = (
            (PAIN, "kPainPct", "kPainTickMs", "kPainMs", DISPEL_MAGIC),
            (FLAY, "kFlayPct", "kFlayTickMs", "kFlayMs", 0),
            (DREAD, "kDreadTickPct", "kDreadTickMs", "kDreadMs", 0),
        )
        for spell_id, pct, tick, duration, dispel in cases:
            spell = self.spells[spell_id]
            effect = spell["effect1"]
            self.assertEqual(spell["school"], SCHOOL_SHADOW, spell_id)
            self.assertEqual(effect["apply_aura"], AURA_PERIODIC_DAMAGE, spell_id)
            normal, heroic = _nh_values(pct)
            self.assertEqual(int(effect["base_points"]), int(normal * 100), spell_id)
            self.assertEqual(_raw(spell, "EffectMiscValueB_1"), int(heroic * 100), spell_id)
            self.assertEqual(effect["amplitude"], int(_header_value(tick)), spell_id)
            self.assertEqual(spell["duration_ms"], int(_header_value(duration)), spell_id)
            self.assertEqual(spell["dispel"], dispel, spell_id)
            self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS, spell_id)
            self.assertIn((spell_id, PERIODIC), self.scripts)
        self.assertEqual(_nh_values("kPainPct"), (2, 3))
        self.assertEqual(_nh_values("kFlayPct"), (6, 8))
        self.assertEqual(_nh_values("kDreadTickPct"), (6, 8))
        self.assertIn((PAIN, PAIN_SCRIPT), self.scripts)
        self.assertEqual(_raw(self.spells[PAIN], "SpellVisualID_1"), SV_PAIN)

    def test_mind_flay_is_a_kickable_channel(self):
        flay = self.spells[FLAY]
        self.assertTrue(_raw(flay, "AttributesEx") & ATTR1_IS_CHANNELED)
        self.assertEqual(_raw(flay, "ChannelInterruptFlags"), CHANNEL_INTERRUPT_KICK)
        self.assertEqual(_raw(flay, "PreventionType"), 1)
        self.assertEqual(_raw(flay, "SpellVisualID_1"), SV_FLAY)
        # Not triggered (the bar shows, a kick stops it), and the kick clears the target's Doubt.
        self.assertIn("me->CastSpell(target, SPELL_GE_MIND_FLAY, false)", self.cpp)
        self.assertIn('ClearDoubt(target, "interrupt")', self.cpp)
        self.assertIn("d.interrupts.emplace_back(NPC_GERSTAHN, SPELL_GE_MIND_FLAY, 3", self.cpp)
        self.assertIn("DispelEntry(SPELL_GE_SHADOW_WORD_PAIN, 2).MostStacksFirst(SPELL_GE_DOUBT)", self.cpp)

    def test_mind_flay_stops_her_before_the_channel(self):
        # R-1-A M1: the 0x08 channel flag is the move bit, so a cast while chasing would end itself on the next spline
        # step and count as a kick. She stops first (before the channel adds the bit).
        self.assertTrue(CHANNEL_INTERRUPT_KICK & 0x08)
        stop = self.cpp.index("me->StopMoving();\n        SpellCastResult const result = me->CastSpell(target, "
                              "SPELL_GE_MIND_FLAY, false);")
        self.assertGreater(stop, self.cpp.index("bool StartMindFlay(Player* forced)"))

    def test_the_circle(self):
        bar = self.spells[CIRCLE_CAST]
        self.assertEqual(bar["effect1"]["type"], DUMMY_EFFECT)
        self.assertEqual(_raw(bar, "InterruptFlags"), 0)
        self.assertEqual(_raw(bar, "PreventionType"), 0)
        self.assertEqual(bar["cast_time_ms"], int(_header_value("kCircleCastMs")))
        self.assertEqual(bar["cast_time_ms"], 2500)
        # Rule 5: a kicked Mind Flay locks Shadow; the must-play bar is another school.
        self.assertNotEqual(bar["school"], SCHOOL_SHADOW)
        self.assertEqual(bar["school"], SCHOOL_ARCANE)
        hit = self.spells[CIRCLE]
        self.assertEqual(hit["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertEqual(hit["school"], SCHOOL_SHADOW)
        self.assertIn((CIRCLE, RESOLVE), self.scripts)
        self.assertEqual(_raw(hit, "SpellVisualID_1"), SV_SCREAM)
        self.assertEqual(_nh_values("kCirclePct"), (15, 25))
        # The tank included (ruling 88): its own row, no exemption; Doubt, never Weakened (ruling 11).
        self.assertIn(".Damage(pct).TankDamage(pct).Spell(SPELL_GE_CIRCLE)", self.cpp)
        self.assertNotIn("TankExempt", self.cpp)
        self.assertNotIn("Weakened()", self.cpp)

    def test_mind_sear(self):
        look = self.spells[SEAR]
        self.assertEqual(look["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(look["duration_ms"], int(_header_value("kSearMs")))
        self.assertEqual(_raw(look, "SpellVisualID_1"), SV_SEAR)
        tick = self.spells[SEAR_TICK]
        self.assertEqual(tick["effect1"]["type"], SCHOOL_DAMAGE)
        normal, heroic = _nh_values("kSearPct")
        self.assertEqual(int(tick["effect1"]["base_points"]) + 1, int(normal * 100))
        self.assertEqual(_raw(tick, "EffectMiscValueB_1"), int(heroic * 100))
        self.assertTrue(_raw(tick, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertIn((SEAR_TICK, DAMAGE), self.scripts)

    def test_shadow_shield_and_knowledge(self):
        absorb = _nh_values("kShieldAbsorb")
        reflect = _nh_values("kShieldReflect")
        for spell_id, i in ((SHIELD, 0), (SHIELD_HEROIC, 1)):
            shield = self.spells[spell_id]
            self.assertEqual(shield["dispel"], DISPEL_MAGIC)
            self.assertEqual(shield["duration_ms"], int(_header_value("kShieldMs")))
            self.assertEqual(shield["effect1"]["apply_aura"], AURA_SCHOOL_ABSORB)
            self.assertEqual(int(shield["effect1"]["base_points"]) + 1, int(absorb[i]))
            self.assertEqual(shield["effect2"]["apply_aura"], AURA_DAMAGE_SHIELD)
            self.assertEqual(int(shield["effect2"]["base_points"]) + 1, int(reflect[i]))
        self.assertEqual(absorb, (4000, 6500))
        knowledge = self.spells[KNOWLEDGE]
        self.assertEqual(knowledge["effect1"]["apply_aura"], AURA_MOD_DAMAGE_PERCENT_DONE)
        self.assertEqual(int(knowledge["effect1"]["base_points"]), int(_header_value("kKnowledgePctPerStack")))
        self.assertEqual(_raw(knowledge, "CumulativeAura"), int(_header_value("kKnowledgeAuraCap")))
        self.assertEqual(_nh_values("kKnowledgeCap"), (5, 0))
        self.assertIn("d.purges.emplace_back(NPC_GERSTAHN, ShieldSpell(_heroic), 1)", self.cpp)

    def test_the_pool_look(self):
        pool = self.spells[LINGERING]
        self.assertEqual(pool["duration_ms"], int(_header_value("kPoolMs")))
        self.assertEqual(_raw(pool, "SpellVisualID_1"), SV_POOL)

    def test_scripts_are_hers_and_the_resolve(self):
        self.assertEqual({name for _, name in self.scripts}, {RESOLVE, PERIODIC, PAIN_SCRIPT, DAMAGE})

    def test_the_stock_kit_is_retired(self):
        # Mana Burn and Psychic Scream are gone; Shadow Word: Pain and Shadow Shield are copies (rule 15).
        code = "\n".join(line for line in self.cpp.splitlines() if not line.lstrip().startswith(("//", "*", "/*")))
        for stock in STOCK_KIT:
            self.assertNotIn(str(stock), code)
        self.assertNotIn("SPELL_STOCK_", code)
        self.assertNotIn("\t", self.cpp)

    def test_the_cpp_uses_the_header_numbers(self):
        for name in ("kCirclePct", "kCircleRadius", "kSearRadius", "kPoolRadius", "kCircleDoubt",
                     "kSearDoubtPerTick", "kPoolDoubtPerTick", "kFlayDoubtPerTick", "PainTickAddsDoubt",
                     "KnowledgeAfterBreak", "ScaledPct"):
            self.assertIn(name, self.cpp + _header(), name)


class GerstahnSqlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.header = _header()

    def test_the_texts(self):
        types = {0: 14, 1: 14, 2: 41, 3: 41, 4: 14}
        for group, kind in types.items():
            self.assertRegex(self.sql, rf"\(9018, {group}, 0, '[^\n]*', {kind}, 0, 100, ", group)
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 9018 AND `GroupID` BETWEEN 0 AND 4;", self.sql)
        groups = dict(re.findall(r"(?:SAY|EMOTE)_(\w+)\s*=\s*(\d+),", self.header))
        self.assertEqual(sorted(int(v) for v in groups.values()), [0, 1, 2, 3, 4])
        self.assertIn("Everyone talks eventually", self.sql)
        self.assertIn("%s sears the mind of $n!", self.sql)

    def test_the_rev_touches_only_the_texts(self):
        code = "\n".join(line for line in self.sql.splitlines() if not line.startswith("--"))
        self.assertNotIn("smart_scripts", code)
        self.assertNotIn("creature_loot_template", code)
        self.assertNotIn("UPDATE `creature`", code)
        self.assertNotIn("creature_template", code)


if __name__ == "__main__":
    unittest.main()
