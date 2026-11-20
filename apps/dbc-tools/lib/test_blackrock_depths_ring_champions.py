"""
Blackrock Depths build WP-D5, the Ring of Law's champions: source/npcs/blackrock_depths/ring_champions.py against its
C++ (modules/mod-dungeon-bosses src/BlackrockDepths/RingChampionsLogic.h, boss_ring_champions_rework.cpp) and its SQL
rev.

Checks:
  - the spells sit in the champions' slice (210870-210923 of 210870-210959) and RingChampionsLogic.h names the same
    ids;
  - the binding goes together: kBound true, the six champions bound to their AIs (registered behind the switch), 90k
    on their class bases, the stun immunity set, the stock DamageModifier;
  - the Risen beasts and the Risen Champion: one per wave type in the header's order, the wave mob's display, their
    heroic lock lines (STAGE-H-REPORT s3), the build spec's health;
  - every registry hit is a resolve copy and the C++ names its tag; G1's drill tags (6-10) on the axe and the rupture;
  - the refflat DoTs and the Volley carry the header's numbers; the curses, the Slow, the Enrage and the shell carry
    their dispel types; the Title Holder buff its +10%;
  - every look is one of V-1's ids;
  - the rev: Grizzle's stock emote as a boss emote, Hedrum's Hate to Zero off his template addon, nothing else.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_ring_champions.py
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
HEADER = MODULE_DIR / "RingChampionsLogic.h"
REWORK = MODULE_DIR / "BlackrockDepthsRework.h"
CPP = MODULE_DIR / "boss_ring_champions_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_ring_champions_blackrock_depths.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_depths"
VISUALS = PACKAGE / "_visuals.py"

SLICE = range(210870, 210960)
FIRST, LAST = 210870, 210923
CHAMPIONS = {
    9027: ("boss_gorosh_the_dervish_rework", 2371),
    9028: ("boss_grizzle_rework", 2371),
    9029: ("boss_eviscerator_rework", 1897),
    9030: ("boss_okthor_rework", 1897),
    9031: ("boss_anubshiah_rework", 1897),
    9032: ("boss_hedrum_rework", 2371),
}
# Risen entry -> (the wave mob it mirrors, its stock display [db], heroic lock line [H s3])
RISEN = {
    300782: (8925, 8182, 310393),
    300783: (8926, 7347, 310394),
    300784: (8927, 1955, 310395),
    300785: (8928, 8184, 310396),
    300786: (8933, 8014, 310397),
    300787: (8932, 7470, 310398),
}
RISEN_CHAMPION, RISEN_CHAMPION_HEROIC = 300788, 310399

SCHOOL_DAMAGE, APPLY_AURA = 2, 6
AURA_DUMMY, AURA_PERIODIC_DAMAGE, AURA_MOD_STUN, AURA_MOD_ROOT = 4, 3, 12, 26
AURA_MOD_DAMAGE_PERCENT_DONE, AURA_MOD_DAMAGE_PERCENT_TAKEN, AURA_MOD_MELEE_HASTE = 79, 87, 138
AURA_MOD_CONFUSE, AURA_TRANSFORM, AURA_MOD_CASTING_SPEED = 5, 56, 65
SCHOOL_PHYSICAL, SCHOOL_NATURE, SCHOOL_SHADOW, SCHOOL_ARCANE = 1, 8, 32, 64
DISPEL_MAGIC, DISPEL_CURSE, DISPEL_POISON, DISPEL_ENRAGE = 1, 2, 4, 9
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


def _effect(spell: dict, index: int) -> dict:
    return spell[f"effect{index}"]


class RingChampionsDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) in CHAMPIONS}
        cls.templates = {int(e["entry"]): e for e in reg.creature_templates
                         if int(e["entry"]) in (*RISEN, RISEN_CHAMPION)}
        cls.models = {int(e["CreatureID"]): e for e in reg.creature_template_models
                      if int(e["CreatureID"]) in (*RISEN, RISEN_CHAMPION)}
        cls.cpp = CPP.read_text(encoding="utf-8")
        cls.sql = SQL.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(FIRST, LAST + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"spell": mine}), [])
        found = re.search(r"kSpellsRingChampions\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(found)
        self.assertEqual((int(found.group(1)), int(found.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_(?:CH|GO|GZ|EV|OK|AN|HE)_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual(sorted(SLICE.start + int(o) for o in offsets), mine)

    def test_the_binding_goes_together(self):
        self.assertIn("inline constexpr bool kBound = true;", _header())
        for entry, (script, base) in CHAMPIONS.items():
            with self.subTest(entry=entry):
                self.assertRegex(self.cpp, rf"if \(BrdRingChampions::kBound\)\s*RegisterDungeonReworkCreatureAI\("
                                 rf"{script},")
                edit = self.edits[entry]
                self.assertEqual(edit["ScriptName"], script)
                self.assertEqual(edit["AIName"], "")
                self.assertEqual(int(edit["CreatureImmunitiesId"]), 1972)
                self.assertAlmostEqual(float(edit["DamageModifier"]), _header_value("kChampionDamageModifier"))
                health = math.ceil(base * float(edit["HealthModifier"]))
                self.assertLessEqual(abs(health - int(_header_value("kChampionNormalHealth"))), 10)
        # The champions have no SmartAI: nothing to drop, nothing inserted.
        self.assertNotIn("`smart_scripts`", self.sql)

    def test_the_risen(self):
        for entry, (wave, display, heroic) in RISEN.items():
            with self.subTest(entry=entry):
                row = self.templates[entry]
                self.assertEqual(row["ScriptName"], "npc_brd_risen_beast")
                self.assertEqual(int(row["difficulty_entry_1"]), heroic)
                self.assertEqual(math.ceil(2292 * float(row["HealthModifier"])),
                                 int(_header_value("kRisenNormalHealth")))
                self.assertEqual(int(row["faction"]), 14)
                self.assertEqual(int(row["lootid"]), 0)
                self.assertEqual(int(self.models[entry]["CreatureDisplayID"]), display)
        # The header's order (RisenEntry) is the stock RingMobs order: 300786 the Cave Creeper, 300787 the Beetle.
        rework = REWORK.read_text(encoding="utf-8")
        self.assertRegex(rework, r"NPC_BRD_RISEN_CREEPER\s*=\s*300786")
        self.assertRegex(rework, r"NPC_BRD_RISEN_BEETLE\s*=\s*300787")
        self.assertEqual(self.templates[300786]["name"], "Risen Cave Creeper")
        self.assertEqual(self.templates[300787]["name"], "Risen Borer Beetle")
        champion = self.templates[RISEN_CHAMPION]
        self.assertEqual(champion["ScriptName"], "npc_brd_risen_champion")
        self.assertEqual(int(champion["difficulty_entry_1"]), RISEN_CHAMPION_HEROIC)
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_brd_risen_beast,", self.cpp)
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_brd_risen_champion,", self.cpp)

    def test_the_registry_hits_are_resolve_copies(self):
        schools = {210874: SCHOOL_PHYSICAL, 210875: SCHOOL_PHYSICAL, 210877: SCHOOL_PHYSICAL, 210878: SCHOOL_PHYSICAL,
                   210883: SCHOOL_PHYSICAL, 210888: SCHOOL_PHYSICAL, 210897: SCHOOL_PHYSICAL, 210900: SCHOOL_ARCANE,
                   210901: SCHOOL_ARCANE, 210906: SCHOOL_NATURE, 210913: SCHOOL_NATURE, 210915: SCHOOL_NATURE,
                   210920: SCHOOL_NATURE, 210923: SCHOOL_NATURE}
        for spell_id, school in schools.items():
            with self.subTest(spell=spell_id):
                spell = self.spells[spell_id]
                self.assertEqual(_effect(spell, 1)["type"], SCHOOL_DAMAGE)
                self.assertIn((spell_id, RESOLVE), self.scripts)
                self.assertEqual(spell["school"], school)
        for needle in (".Spell(SPELL_GO_DANCE_LINE)", ".Tag(TAG_GO_DANCE_LINE)", ".Spell(SPELL_GO_DANCE_END)",
                       ".Spell(SPELL_GO_AXE_LAND).Tag(TAG_GO_AXE)", ".Tag(TAG_GO_AXE_SHOWN)",
                       ".Spell(SPELL_GO_AXE_RETURN).Tag(TAG_GO_AXE_RETURN)",
                       ".Spell(SPELL_GZ_RUSH).Tag(TAG_GZ_BULL_RUSH)",
                       ".Rider(SPELL_GZ_STOMP_STUN).Tag(TAG_GZ_STOMP)", ".Spell(SPELL_OK_RUPTURE).Tag(RuptureTag(",
                       ".Rider(SPELL_OK_SHEEP)", ".Rider(SPELL_AN_WEB_ROOT)", ".Rider(SPELL_HE_STRANDS_ROOT)",
                       ".Rider(SPELL_HE_BANEFUL_POISON)", ".Spell(SPELL_EV_OPEN_WOUNDS_JUMP).Tag(TAG_EV_OPEN_WOUNDS)"):
            self.assertIn(needle, self.cpp)
        # G1's drill tags (MechanicDrill.h kBrdTagAxe..kBrdTagRuptureHeroic).
        for name, tag in (("TAG_GO_AXE", 6), ("TAG_GO_AXE_SHOWN", 7), ("TAG_GO_AXE_RETURN", 8), ("TAG_OK_RUPTURE", 9),
                          ("TAG_OK_RUPTURE_HEROIC", 10)):
            self.assertRegex(_header(), rf"\b{name}\s*=\s*{tag},")

    def test_the_refflat_casts_and_dots(self):
        for spell_id, header_name, tick, duration, dispel in (
                (210896, "kOpenWoundsPct", "kOpenWoundsTickMs", "kOpenWoundsMs", 0),
                (210921, "kBurstPoisonPct", "kBurstPoisonTickMs", "kBurstPoisonMs", DISPEL_POISON)):
            with self.subTest(spell=spell_id):
                spell = self.spells[spell_id]
                pct = _header_value(header_name)
                self.assertEqual(_effect(spell, 1)["apply_aura"], AURA_PERIODIC_DAMAGE)
                self.assertEqual(_effect(spell, 1)["base_points"], round(pct * 100))
                self.assertEqual(_raw(spell, "EffectMiscValueB_1"), round(pct * 100))
                self.assertEqual(_effect(spell, 1)["amplitude"], int(_header_value(tick)))
                self.assertEqual(spell["duration_ms"], int(_header_value(duration)))
                self.assertEqual(spell["dispel"], dispel)
                self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
                self.assertIn((spell_id, REFFLAT_PERIODIC), self.scripts)
        volley = self.spells[210898]
        normal, heroic = _header_nh("kVolleyPct")
        self.assertEqual(_effect(volley, 1)["base_points"] + _effect(volley, 1)["die_sides"], round(normal * 100))
        self.assertEqual(_raw(volley, "EffectMiscValueB_1"), round(heroic * 100))
        self.assertEqual(volley["cast_time_ms"], int(_header_value("kVolleyCastMs")))
        self.assertEqual(_raw(volley, "InterruptFlags"), 15)
        self.assertEqual(volley["school"], SCHOOL_SHADOW)
        self.assertAlmostEqual(float(_effect(volley, 1)["radius_yards"]), _header_value("kVolleyRadius"))
        self.assertIn((210898, REFFLAT_DAMAGE), self.scripts)
        devoured = self.spells[210894]
        self.assertEqual(_effect(devoured, 1)["type"], SCHOOL_DAMAGE)
        self.assertTrue(_raw(devoured, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertIn("CastCustomSpell(SPELL_EV_DEVOURED_MAGIC, SPELLVALUE_BASE_POINT0", self.cpp)

    def test_the_auras(self):
        title = self.spells[210870]
        self.assertEqual(_effect(title, 1)["apply_aura"], AURA_MOD_DAMAGE_PERCENT_DONE)
        self.assertEqual(_effect(title, 1)["base_points"], int(_header_value("kTitleHolderDamagePct")))
        self.assertEqual(title["duration_ms"], -1)
        dazed = self.spells[210885]
        self.assertEqual(_effect(dazed, 1)["apply_aura"], AURA_MOD_DAMAGE_PERCENT_TAKEN)
        self.assertEqual(_effect(dazed, 1)["base_points"], int(_header_value("kDazedDamageTakenPct")))
        self.assertEqual(dazed["duration_ms"], int(_header_value("kDazedMs")))
        self.assertEqual(dazed["mechanic"], 0)          # 1972 holds DAZE
        stun = self.spells[210889]
        self.assertEqual(_effect(stun, 1)["apply_aura"], AURA_MOD_STUN)
        self.assertEqual(stun["duration_ms"], int(_header_value("kStompStunMs")))
        frenzy = self.spells[210890]
        self.assertEqual(frenzy["dispel"], DISPEL_ENRAGE)
        self.assertEqual(_effect(frenzy, 1)["apply_aura"], AURA_MOD_MELEE_HASTE)
        self.assertEqual(_effect(frenzy, 2)["apply_aura"], AURA_MOD_DAMAGE_PERCENT_DONE)
        self.assertEqual(_effect(frenzy, 1)["base_points"], int(_header_value("kFrenzyPctPerStack")))
        self.assertEqual(_raw(frenzy, "CumulativeAura"), int(_header_value("kFrenzyCapHeroic")))
        eater = self.spells[210892]
        self.assertEqual(eater["dispel"], DISPEL_MAGIC)
        self.assertEqual(eater["duration_ms"], int(_header_value("kSpellEaterMs")))
        self.assertEqual(_raw(self.spells[210893], "CumulativeAura"), int(_header_value("kDevouredCap")))
        sheep = self.spells[210902]
        self.assertEqual(_effect(sheep, 1)["apply_aura"], AURA_MOD_CONFUSE)
        self.assertEqual(_effect(sheep, 2)["apply_aura"], AURA_TRANSFORM)
        self.assertEqual(sheep["duration_ms"], int(_header_value("kSheepPolyMs")))
        slow = self.spells[210903]
        self.assertEqual(slow["dispel"], DISPEL_MAGIC)
        self.assertEqual(_effect(slow, 1)["base_points"], -int(_header_value("kSlowMovePct")))
        self.assertEqual(slow["duration_ms"], int(_header_value("kSlowMs")))
        for spell_id, aura, value in ((210911, AURA_MOD_CASTING_SPEED, "kTonguesCastPct"),
                                      (210912, AURA_MOD_DAMAGE_PERCENT_DONE, "kWeaknessPhysicalPct")):
            curse = self.spells[spell_id]
            self.assertEqual(curse["dispel"], DISPEL_CURSE)
            self.assertEqual(_effect(curse, 1)["apply_aura"], aura)
            self.assertEqual(_effect(curse, 1)["base_points"], -int(_header_value(value)))
            self.assertEqual(curse["duration_ms"], int(_header_value("kCurseMs")))
        for spell_id, ms in ((210907, "kWebRootMs"), (210916, "kStrandsRootMs")):
            root = self.spells[spell_id]
            self.assertEqual(_effect(root, 1)["apply_aura"], AURA_MOD_ROOT)
            self.assertEqual(root["duration_ms"], int(_header_value(ms)))
        # The linger riders' slows: the web -50%, the strands -30% (standing_in_it: -(pct + 1) + 1).
        self.assertEqual(_effect(self.spells[210908], 1)["base_points"], -(int(_header_value("kWebPatchSlowPct")) + 1))
        self.assertEqual(_effect(self.spells[210917], 1)["base_points"], -(int(_header_value("kStrandsSlowPct")) + 1))

    def test_the_bars_are_not_kickable_and_dodge_the_kick_schools(self):
        for spell_id in (210873, 210882, 210887, 210899, 210904, 210914):
            with self.subTest(spell=spell_id):
                self.assertEqual(_raw(self.spells[spell_id], "InterruptFlags"), 0)
        # Rule 5: Ok'thor's and Anub'shiah's bars avoid the school of their kickable stock casts (Arcane, Shadow).
        self.assertEqual(self.spells[210899]["school"], SCHOOL_PHYSICAL)
        self.assertEqual(self.spells[210904]["school"], SCHOOL_PHYSICAL)

    def test_the_descriptor_goes_to_grimstone(self):
        # D4's rule: a champion never calls Mechanic::Describe; it hands its entries to SetUnitDescriptor.
        self.assertNotIn("Mechanic::Describe(", self.cpp)
        self.assertIn("frame->SetUnitDescriptor(me->GetGUID(), DescriptorFill())", self.cpp)
        self.assertIn("HoldEntry::Damage(NPC_EVISCERATOR, SPELL_EV_SPELL_EATER", self.cpp)
        self.assertIn("d.purges.emplace_back(NPC_GRIZZLE, SPELL_GZ_KILLING_FRENZY", self.cpp)
        self.assertIn("d.dispels.emplace_back(SPELL_HE_BANEFUL_POISON", self.cpp)

    def test_the_looks_are_v1_ids(self):
        looks = {210870: "CH_TITLE_HOLDER", 210871: "CH_TITLE_HOLDER_FLASH", 210872: "RL_RAISED",
                 210876: "GO_DERVISH_DANCE", 210879: "GO_RETURNING_AXE", 210880: "GO_RETURNING_AXE",
                 210881: "GO_RETURNING_AXE_LINE", 210884: "GZ_BULL_RUSH", 210885: "GZ_DAZED",
                 210886: "GZ_WALL_IMPACT", 210888: "GZ_EARTHSHAKER_STOMP", 210891: "GZ_KILLING_FRENZY_FLASH",
                 210892: "EV_SPELL_EATER", 210895: "EV_DEVOURED_MAGIC", 210896: "EV_OPEN_WOUNDS",
                 210900: "OK_ARCANE_RUPTURE", 210902: "OK_SHEEP_BOLT", 210905: "AN_RAISE_DEAD",
                 210909: "AN_WEB_PATCH", 210910: "AN_WEB_SPIT", 210914: "HE_WEB_STRANDS",
                 210918: "HE_WEB_STRAND_PATCH", 210919: "HE_REEL_IN", 210922: "HE_BANEFUL_BURST"}
        for spell_id, name in looks.items():
            with self.subTest(spell=spell_id):
                self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), _visual(name))
        # Never the spec's WRONG looks (VR): Whirlwind 15589's SV 227, Hurl Axe's 14843, Vicious Rend's 372.
        used = {_raw(s, "SpellVisualID_1") for s in self.spells.values()}
        self.assertTrue(used.isdisjoint({227, 14843, 372}))

    def test_the_sql_rev(self):
        sql = self.sql
        self.assertNotIn("INSERT INTO `creature` ", sql)
        self.assertIn("UPDATE `creature_text` SET `Type` = 41 WHERE `CreatureID` = 9028 AND `GroupID` = 0;", sql)
        self.assertIn("UPDATE `creature_template_addon` SET `auras` = NULL WHERE `entry` = 9032;", sql)


if __name__ == "__main__":
    unittest.main()
