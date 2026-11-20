"""
Blackrock Depths build WP-D4, the Ring of Law's frame and waves: source/npcs/blackrock_depths/ring_of_law.py against its
C++ (modules/mod-dungeon-bosses src/BlackrockDepths/RingOfLawLogic.h, npc_grimstone_rework.cpp,
npc_ring_beast_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in the Ring's slice (210810-210869) and RingOfLawLogic.h names the same ids;
  - the binding goes together: kBound true, Grimstone and the six wave mobs bound, their SmartAI dropped by the rev;
  - the wave mobs' health is the build spec's (and the header's table), at the level 51 base;
  - Crowd Favor (a 10-stack buff), the gift and Roar of the Crowd carry the header's numbers;
  - every registry hit is a resolve copy; the rescaled stock casts and the poisons go through the refflat scripts;
  - Screech is a 2 s kick with a 10 yd hit and a silence; the crowd's throws are dest missiles at the header's speed;
  - every look is one of V-1's ids;
  - the rev drops the 14 SmartAI rows and writes Grimstone's lines 6-14 (10, 13, 14 boss emotes).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_ring_of_law.py
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
HEADER = MODULE_DIR / "RingOfLawLogic.h"
REWORK = MODULE_DIR / "BlackrockDepthsRework.h"
GRIMSTONE_CPP = MODULE_DIR / "npc_grimstone_rework.cpp"
BEAST_CPP = MODULE_DIR / "npc_ring_beast_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_ring_of_law_blackrock_depths.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_depths"
VISUALS = PACKAGE / "_visuals.py"

SLICE = range(210810, 210870)
(FAVOR, GIFT, ROAR, GIFT_TOSS, JEER, JEER_BOTTLE, JEER_APPLE, JEER_BANANA, TRIAL_FIRE, TRIAL_FIRE_BAR, TRIAL_BURST,
 BURROW, BURROW_SINK, BURROW_ERUPT, STING_BAR, STING, STING_POISON, SCREECH, CLAP_BAR, CLAP, CLAP_SLOW, SPIT,
 SPIT_POOL, ACID, ACID_SWELL, ACID_LOOK, WORM_POISON, WORM_SPIT, LIZARD_BOLT) = range(210810, 210839)
GRIMSTONE = 10096
WAVE_MOBS = {8925: 18_000, 8926: 18_000, 8927: 18_000, 8928: 26_000, 8933: 18_000, 8932: 9_000}
WAVE_BASE = 2292

SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT = 2, 6, 3
AURA_DUMMY, AURA_PERIODIC_DAMAGE, AURA_MOD_SILENCE, AURA_MOD_DECREASE_SPEED = 4, 3, 27, 33
AURA_MOD_SCALE, AURA_MOD_DAMAGE_PERCENT_DONE = 61, 79
SCHOOL_PHYSICAL, SCHOOL_NATURE, SCHOOL_FIRE = 1, 8, 4
DISPEL_POISON = 4
TARGET_DEST_DEST = 87
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT_DAMAGE = "spell_dungeon_refflat_damage"
REFFLAT_PERIODIC = "spell_dungeon_refflat_periodic"


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


def _header_value(name: str) -> float:
    match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f?;", _header())
    assert match, name
    return float(match.group(1))


def _header_nh(name: str) -> tuple[float, float]:
    match = re.search(rf"\b{name}\{{\s*(-?[\d.]+)f?,\s*(-?[\d.]+)f?\s*\}};", _header())
    assert match, name
    return float(match.group(1)), float(match.group(2))


def _visual(name: str) -> int:
    text = VISUALS.read_text(encoding="utf-8")
    match = re.search(rf"^{name}\s*=\s*(\w+)", text, re.MULTILINE)
    assert match, name
    value = match.group(1)
    return int(value) if value.isdigit() else _visual(value)


class RingOfLawDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits
                     if int(e["entry"]) in (GRIMSTONE, *WAVE_MOBS)}
        cls.grimstone_cpp = GRIMSTONE_CPP.read_text(encoding="utf-8")
        cls.beast_cpp = BEAST_CPP.read_text(encoding="utf-8")
        cls.sql = SQL.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(FAVOR, LIZARD_BOLT + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"spell": mine}), [])
        first = re.search(r"kSpellsRingOfLaw\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(first)
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_R[LW]_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))

    def test_the_binding_goes_together(self):
        # kBound, the two AIs registered behind it, the DT bindings, the SmartAI drop: one change.
        self.assertIn("inline constexpr bool kBound = true;", _header())
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_grimstone_rework,", self.grimstone_cpp)
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_ring_beast_rework,", self.beast_cpp)
        self.assertEqual(self.edits[GRIMSTONE]["ScriptName"], "npc_grimstone_rework")
        for entry in WAVE_MOBS:
            edit = self.edits[entry]
            self.assertEqual(edit["ScriptName"], "npc_ring_beast_rework", entry)
            self.assertEqual(edit["AIName"], "", entry)
        self.assertIn("DELETE FROM `smart_scripts` WHERE `entryorguid` IN (8925, 8926, 8927, 8928, 8932, 8933) "
                      "AND `source_type` = 0;", self.sql)

    def test_the_wave_health(self):
        # The build spec's per mob health (3-mob waves 18k, Thundersnouts 26k, Beetles 9k) at the level 51 base.
        self.assertEqual(int(_header_value("kWaveBaseHealth")), WAVE_BASE)
        table = re.findall(r"(\d+), (\d+), ([\d.]+)f,", _header())
        header_rows = sorted((int(n), float(m)) for n, _, m in table)
        mine = []
        for entry, health in WAVE_MOBS.items():
            modifier = float(self.edits[entry]["HealthModifier"])
            self.assertEqual(math.ceil(WAVE_BASE * modifier), health, entry)
            mine.append((health, modifier))
        self.assertEqual(sorted(mine), header_rows)

    def test_crowd_favor_the_gift_and_the_roar(self):
        favor = self.spells[FAVOR]
        self.assertEqual(favor["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(_raw(favor, "CumulativeAura"), 10)                 # kFavorMax (kRingFavorMax)
        self.assertIn("kRingFavorMax = 10;", REWORK.read_text(encoding="utf-8"))
        self.assertEqual(favor["duration_ms"], -1)
        gift = self.spells[GIFT]
        self.assertEqual(gift["effect1"]["apply_aura"], AURA_MOD_DAMAGE_PERCENT_DONE)
        self.assertEqual(gift["effect1"]["base_points"], int(_header_value("kGiftDamagePct")))
        self.assertEqual(gift["duration_ms"], int(_header_value("kGiftMs")))
        roar = self.spells[ROAR]
        self.assertEqual(roar["effect1"]["base_points"], int(_header_value("kRoarDamagePct")))
        self.assertEqual(roar["duration_ms"], -1)
        # The heal is the script's (HealBySpell, no spell power), on the gift's own name.
        self.assertIn("HealInfo healInfo(player, player, heal, info, info->GetSchoolMask());", self.grimstone_cpp)

    def test_the_registry_hits_are_resolve_copies(self):
        schools = {JEER: SCHOOL_PHYSICAL, TRIAL_FIRE: SCHOOL_FIRE, BURROW: SCHOOL_PHYSICAL, STING: SCHOOL_NATURE,
                   CLAP: SCHOOL_NATURE, SPIT: SCHOOL_NATURE, ACID: SCHOOL_NATURE}
        for spell_id, school in schools.items():
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
            self.assertEqual(spell["school"], school, spell_id)
        cpp = self.grimstone_cpp + self.beast_cpp
        for needle in (".Spell(SPELL_RL_JEER).Tag(TAG_RL_JEER)",
                       ".Spell(SPELL_RL_TRIAL_BY_FIRE).Tag(TAG_RL_TRIAL_FIRE)",
                       ".Spell(SPELL_RW_BURROW).Tag(TAG_RW_BURROW)", ".Rider(SPELL_RW_TAIL_STING_POISON)",
                       ".Rider(SPELL_RW_THUNDERCLAP_SLOW)", ".Spell(SPELL_RW_VENOM_SPIT).Tag(TAG_RW_VENOM_SPIT)",
                       ".Spell(SPELL_RW_ACID_BURST).Tag(TAG_RW_ACID_BURST)"):
            self.assertIn(needle, cpp)

    def test_the_refflat_casts_and_poisons(self):
        for spell_id, header_name in ((STING_POISON, "kTailStingPoisonPct"), (WORM_POISON, "kWormPoisonPct")):
            spell = self.spells[spell_id]
            normal, heroic = _header_nh(header_name)
            self.assertEqual(spell["effect1"]["apply_aura"], AURA_PERIODIC_DAMAGE, spell_id)
            self.assertEqual(spell["effect1"]["base_points"], round(normal * 100), spell_id)
            self.assertEqual(_raw(spell, "EffectMiscValueB_1"), round(heroic * 100), spell_id)
            self.assertEqual(spell["dispel"], DISPEL_POISON, spell_id)
            self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS, spell_id)
            self.assertIn((spell_id, REFFLAT_PERIODIC), self.scripts)
        self.assertEqual(self.spells[STING_POISON]["effect1"]["amplitude"],
                         int(_header_value("kTailStingPoisonTickMs")))
        self.assertEqual(self.spells[STING_POISON]["duration_ms"], int(_header_value("kTailStingPoisonMs")))
        self.assertEqual(self.spells[WORM_POISON]["duration_ms"], int(_header_value("kWormPoisonMs")))
        for spell_id, header_name, cast in ((WORM_SPIT, "kWormVenomSpitPct", "kWormVenomSpitCastMs"),
                                            (LIZARD_BOLT, "kLizardBoltPct", "kLizardBoltCastMs")):
            spell = self.spells[spell_id]
            normal, heroic = _header_nh(header_name)
            effect = spell["effect1"]
            self.assertEqual(effect["type"], SCHOOL_DAMAGE, spell_id)
            self.assertEqual(effect["base_points"] + effect["die_sides"], round(normal * 100), spell_id)
            self.assertEqual(_raw(spell, "EffectMiscValueB_1"), round(heroic * 100), spell_id)
            self.assertEqual(spell["cast_time_ms"], int(_header_value(cast)), spell_id)
            self.assertEqual(_raw(spell, "InterruptFlags"), 15, spell_id)
            self.assertIn((spell_id, REFFLAT_DAMAGE), self.scripts)
        self.assertIn("d.interrupts.emplace_back(NPC_THUNDERSNOUT, SPELL_RW_LIZARD_BOLT", self.grimstone_cpp)
        self.assertIn("d.interrupts.emplace_back(NPC_DREDGE_WORM, SPELL_RW_WORM_VENOM_SPIT", self.grimstone_cpp)
        self.assertIn("d.dispels.emplace_back(SPELL_RW_TAIL_STING_POISON", self.grimstone_cpp)
        self.assertIn("d.dispels.emplace_back(SPELL_RW_WORM_POISON", self.grimstone_cpp)

    def test_the_fix_pass_rules(self):
        # R-1-RING MN-1 (orchestrator default): the opening debuff waits until the opener is inside the floor.
        self.assertIn("_openingPending = _slot == 1 && w.openingDebuff != 0;", self.beast_cpp)
        self.assertIn("if (OpeningDebuffDue(_openingPending, DungeonKit::PlaneOf(me)))", self.beast_cpp)
        self.assertNotIn("if (_slot == 1 && w.openingDebuff)\n            DoCastSelf(w.openingDebuff);",
                         self.beast_cpp)
        # D5 request 3: the frame's end (a wipe despawns living champions) takes the champions' player auras too.
        self.assertIn("for (uint32 const spell : BrdRingChampions::kChampionPlayerAuras)", self.grimstone_cpp)
        # User ruling 2026-11-17: a wipe in the Encore (or its beat) puts the banner out (the instance's FAIL reads
        # DATA_ENCORE_RUNNING, which Grimstone sets on those steps).
        self.assertIn("if (WipeUnlightsBanner(step))\n            instance->SetData(DATA_ENCORE_RUNNING, 1);",
                      self.grimstone_cpp)
        # D4 request 2: the Encore's kill is reported before the Ring's credit.
        won = self.grimstone_cpp.index("void EncoreWon() override")
        self.assertLess(self.grimstone_cpp.index("instance->SetData(DATA_ENCORE_WON, 1);", won),
                        self.grimstone_cpp.index("instance->SetData(TYPE_RING_OF_LAW, DONE);"))

    def test_screech_is_a_kick_with_a_silence(self):
        screech = self.spells[SCREECH]
        normal, heroic = _header_nh("kScreechPct")
        self.assertEqual(screech["cast_time_ms"], int(_header_value("kScreechCastMs")))
        self.assertEqual(_raw(screech, "InterruptFlags"), 15)
        self.assertEqual(_raw(screech, "PreventionType"), 1)
        self.assertEqual(screech["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertEqual(screech["effect1"]["base_points"] + screech["effect1"]["die_sides"], round(normal * 100))
        self.assertEqual(_raw(screech, "EffectMiscValueB_1"), round(heroic * 100))
        self.assertAlmostEqual(float(screech["effect1"]["radius_yards"]), _header_value("kScreechRadius"))
        self.assertEqual(screech["effect2"]["apply_aura"], AURA_MOD_SILENCE)
        self.assertEqual(screech["duration_ms"], int(_header_value("kScreechSilenceMs")))
        self.assertIn((SCREECH, REFFLAT_DAMAGE), self.scripts)
        self.assertIn("d.interrupts.emplace_back(NPC_DARK_SCREECHER, SPELL_RW_SCREECH, kScreechKickPriority",
                      self.grimstone_cpp)

    def test_the_slow_and_the_swell(self):
        slow = self.spells[CLAP_SLOW]
        self.assertEqual(slow["effect1"]["apply_aura"], AURA_MOD_DECREASE_SPEED)
        self.assertEqual(slow["effect1"]["base_points"], -int(_header_value("kThunderclapSlowPct")))
        self.assertEqual(slow["duration_ms"], int(_header_value("kThunderclapSlowMs")))
        swell = self.spells[ACID_SWELL]
        self.assertEqual(swell["effect1"]["apply_aura"], AURA_MOD_SCALE)
        self.assertEqual(swell["effect1"]["base_points"], int(_header_value("kAcidSwellScalePct")))
        self.assertGreater(swell["duration_ms"], int(_header_value("kAcidBodyHoldMs")))
        self.assertEqual(self.spells[SPIT_POOL]["duration_ms"],
                         int(_header_value("kVenomSpitWarnMs")) + int(_header_value("kVenomSpitLifeMs")))

    def test_the_crowd_throws_are_dest_missiles(self):
        for spell_id in (GIFT_TOSS, JEER_BOTTLE, JEER_APPLE, JEER_BANANA):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], DUMMY_EFFECT, spell_id)
            self.assertEqual(spell["effect1"]["implicit_target_a"], TARGET_DEST_DEST, spell_id)
            self.assertAlmostEqual(float(_raw(spell, "Speed")), _header_value("kThrowMissileSpeed"))

    def test_the_looks_are_v1_ids(self):
        looks = {GIFT: "RL_CROWD_GIFT_ALT", GIFT_TOSS: "RL_CROWD_GIFT", JEER_BOTTLE: "RL_THROW_BOTTLE",
                 JEER_APPLE: "RL_ROTTEN_APPLE", JEER_BANANA: "RL_ROTTEN_BANANA", TRIAL_BURST: "RL_TRIAL_BURST",
                 BURROW_SINK: "RW_BURROW", BURROW_ERUPT: "RW_BURROW_ERUPT", STING_BAR: "RW_TAIL_STING",
                 SCREECH: "RW_SCREECH", CLAP: "RW_THUNDERCLAP", SPIT_POOL: "SHIPPED_GOO_PUDDLE_STATE",
                 ACID_LOOK: "RW_ACID_BURST"}
        for spell_id, name in looks.items():
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), _visual(name), spell_id)
        # Never the spec's WRONG looks (VR): Eruption 5043 for Trial by Fire, Acid Burst 70744's 14985.
        self.assertNotEqual(_raw(self.spells[TRIAL_BURST], "SpellVisualID_1"), 5043)
        self.assertNotEqual(_raw(self.spells[ACID_LOOK], "SpellVisualID_1"), 14985)

    def test_the_sql_rev(self):
        sql = self.sql
        self.assertNotIn("INSERT INTO `creature` ", sql)
        self.assertNotIn("INSERT INTO `smart_scripts`", sql)
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 10096 AND `GroupID` BETWEEN 6 AND 14;", sql)
        for group in (6, 7, 8, 9, 11, 12):
            self.assertRegex(sql, rf"\({GRIMSTONE}, {group}, 0, '[^\n]*', 14,")
        for group in (10, 13, 14):
            self.assertRegex(sql, rf"\({GRIMSTONE}, {group}, 0, '[^\n]*', 41,")
        # The stock groups 0-5 stay (never touched).
        self.assertNotRegex(sql, rf"\({GRIMSTONE}, [0-5], ")


if __name__ == "__main__":
    unittest.main()
