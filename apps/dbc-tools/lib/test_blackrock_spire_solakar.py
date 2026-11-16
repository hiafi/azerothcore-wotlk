"""
Blackrock Spire build WP-B11, Solakar Flamewreath: source/npcs/blackrock_spire/solakar.py against its C++
(modules/mod-dungeon-bosses src/BlackrockSpire/SolakarLogic.h, boss_solakar_flamewreath_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in Solakar's slice (210390-210429) and SolakarLogic.h names the same ids;
  - Solakar 10264 is bound at 175k on the level 60 warrior base, the stock DamageModifier, stun immune,
    INSTANCE_BIND; the Rookery Guardian and Hatcher are bound to C++ at 30,000 / 25,000; the flame whelp 300731 sits
    in the reservation with its predicted heroic entry and the stock whelp's display;
  - the flame is the custom bag item 70610 (R-2 ruling 2026-11-15; source/world/blackrock_spire_father_flame.py
    FATHER_FLAME): its items.csv Item.dbc row and its SQL item_template row agree with the table and with
    kItemFatherFlame, it is never equippable (InventoryType 0: usable from the bags), and the stock 13371 is untouched
    (no edit anywhere); its on-use is the toss: a friendly player within 30 yd, only for the holder, usable while
    stunned, a missile, bound to its script; the holder aura cannot be cancelled or dispelled and lasts until moved;
  - full bags (R-2 ruling): the toss refuses a catcher without room, the pickups and the pass's catchers skip them;
  - Flamewreath is the header's percent a stack (normal and heroic) with the header's cap; the bars last the header's
    seconds and cannot be interrupted; the stun rider is 2 s; the percent hits carry the script that reads hundredths;
    the spear's bleed is a 12 s, 1 s bleed bound to its script;
  - the SQL rev writes the texts, drops the pair's SmartAI rows, rebinds Father Flame and adds item 70610, and nothing
    else.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_spire_solakar.py
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
from source.npcs.blackrock_spire import _visuals as V  # noqa: E402
from source.world import blackrock_spire_father_flame as FF  # noqa: E402

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockSpire"
HEADER = MODULE_DIR / "SolakarLogic.h"
REWORK = MODULE_DIR / "BlackrockSpireRework.h"
SCRIPT = MODULE_DIR / "boss_solakar_flamewreath_rework.cpp"
INSTANCE = MODULE_DIR / "instance_blackrock_spire_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_solakar_flamewreath_blackrock_spire.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_spire"
ITEM_FILE = TOOL_ROOT / "source" / "world" / "blackrock_spire_father_flame.py"

SLICE = range(210390, 210430)
(FLAME, TOSS, SEARING, SCORCHED, CATCH_FLARE, HATCH_BURST, HATCHER_HATCH, STOLEN, WREATH, WREATH_H, WREATHED,
 WREATHED_TICK, HUNT_ROAR, HUNT, HUNTED, STOMP_BAR, STOMP, STOMP_LOOK, STOMP_STUN, GROUND_BAR, GROUND, SPEAR_THROW,
 SPEAR_WOUND, SPEAR_TEAR, CAUTERIZE) = range(210390, 210415)
SOLAKAR, GUARDIAN, HATCHER, WHELP = 10264, 10258, 10683, 300731
ITEM = 70610
KEEPSAKE = 13371
ITEMS_CSV = TOOL_ROOT / "source" / "items.csv"

SCHOOL_FIRE, SCHOOL_PHYSICAL = 4, 1
SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT = 2, 6, 3
AURA_DUMMY, AURA_PERIODIC_DAMAGE, AURA_MOD_STUN, AURA_MOD_DAMAGE_PERCENT_DONE = 4, 3, 12, 79
TARGET_UNIT_TARGET_ALLY = 21
MECHANIC_STUN, MECHANIC_BLEED = 12, 15
ATTR0_PASSIVE = 0x00000040
ATTR0_NO_AURA_CANCEL = 0x80000000
ATTR5_ALLOW_WHILE_STUNNED = 0x00000008
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
AURA_INTERRUPT_CHANGE_MAP = 0x00080000
RESOLVE = "spell_boss_mechanics_resolve"
REF_PCT = "spell_brs_solakar_ref_pct"
WARRIOR_60_BASE = 3052      # creature_classlevelstats level 60 class 1 basehp0


def _live():
    t = id_blocks
    return t.spell_tables.dsl_live_data(
        {}, t.spell_tables.load_live_item_template_rows,
        lambda: t.state.load_existing_rows(t.dbcfmt.SKILLLINEABILITY),
        lambda: t.state.load_stock_rows(t.dbcfmt.CHRCLASSES),
        lambda: t.state.load_stock_rows(t.dbcfmt.SKILLLINEABILITY),
    )


def _load():
    t = id_blocks
    # Like the heroic and kit tests: no live data, so the boss package must not need any.
    return registry.load_class_package(
        PACKAGE, ids_cfg=t.IDS, trainer_index=t._AnyTrainer(), existing_group_ids=t._AnySet(),
        shapeshift_index={}, existing_creature_rows=t._AnyRows(),
        creature_columns=t.spell_tables.CREATURE_TEMPLATE_COLUMNS,
        creature_defaults=t.spell_tables.CREATURE_TEMPLATE_DEFAULTS, live_data={},
    )


def _raw(spell: dict, column: str) -> int | float:
    return (spell.get("raw_overrides") or {}).get(column, 0) or 0


def _header() -> str:
    return HEADER.read_text(encoding="utf-8")


def _header_value(name: str) -> float:
    match = re.search(rf"{name}\s*=\s*(-?[\d.]+)f?;", _header())
    assert match, name
    return float(match.group(1))


def _header_nh(name: str) -> tuple[float, float]:
    match = re.search(rf"{name}\{{\s*(-?[\d.]+)f?,\s*(-?[\d.]+)f?\s*\}}", _header())
    assert match, name
    return float(match.group(1)), float(match.group(2))


class SolakarDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits
                     if int(e["entry"]) in (SOLAKAR, GUARDIAN, HATCHER)}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == WHELP}
        cls.models = [e for e in reg.creature_template_models if int(e["CreatureID"]) == WHELP]
        cls.items = list(registry.load_class_file(ITEM_FILE, live_data=_live()).item_templates)
        cls.package_items = list(reg.item_templates)
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(FLAME, CAUTERIZE + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_spire", {"spell": mine}), [])
        first = re.search(r"kSpellsSolakar\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(first)
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_SK_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))

    def test_the_bindings(self):
        boss = self.edits[SOLAKAR]
        self.assertEqual(boss["ScriptName"], "boss_solakar_flamewreath_rework")
        self.assertEqual(boss["AIName"], "")
        self.assertLessEqual(abs(math.ceil(WARRIOR_60_BASE * boss["HealthModifier"]) - 175000), 2)
        self.assertAlmostEqual(float(boss["DamageModifier"]), 3.5)
        self.assertEqual(boss["CreatureImmunitiesId"], 1972)
        self.assertEqual(boss["flags_extra"], 1)
        for entry, script, health in ((GUARDIAN, "npc_brs_rookery_guardian", 30000),
                                      (HATCHER, "npc_brs_rookery_hatcher", 25000)):
            add = self.edits[entry]
            self.assertEqual(add["ScriptName"], script)
            self.assertEqual(add["AIName"], "")
            self.assertEqual((add["minlevel"], add["maxlevel"]), (60, 60))
            self.assertLessEqual(abs(WARRIOR_60_BASE * add["HealthModifier"] - health), 1.0, entry)
            self.assertAlmostEqual(float(add["DamageModifier"]), 7.5)
        for name in ("boss_solakar_flamewreath_rework", "npc_brs_rookery_hatcher", "npc_brs_rookery_guardian",
                     "npc_brs_flame_whelp"):
            self.assertIn(f"RegisterDungeonReworkCreatureAI({name},", self.cpp)
        self.assertIn("RegisterDungeonReworkGameObjectAI(go_brs_father_flame,", self.cpp)
        for name in ("spell_brs_solakar_flame_toss", "spell_brs_solakar_ref_pct", "spell_brs_solakar_spear_throw",
                     "spell_brs_solakar_spear_wound"):
            self.assertIn(f"RegisterSpellScript({name})", self.cpp)
        self.assertIn('BrsTest::RegisterBoss("solakar"', self.cpp)

    def test_the_flame_whelp(self):
        self.assertEqual(id_blocks.out_of_reservation("blackrock_spire", {"creature": [WHELP]}), [])
        whelp = self.creatures[WHELP]
        self.assertEqual(whelp["ScriptName"], "npc_brs_flame_whelp")
        self.assertEqual(whelp["AIName"], "")
        self.assertEqual(whelp["faction"], 16)
        self.assertEqual(whelp["type"], 2)      # dragonkin
        self.assertLessEqual(abs(WARRIOR_60_BASE * whelp["HealthModifier"] - 3000), 1.0)
        self.assertEqual(whelp["lootid"], 0)
        # The predicted heroic id (test_blackrock_spire_heroic KIT_HEROIC_ID) and the stock whelp's look.
        self.assertEqual(whelp["difficulty_entry_1"], 310295)
        self.assertEqual([m["CreatureDisplayID"] for m in self.models], [V.DISPLAY_FLAME_WHELP])
        self.assertRegex(REWORK.read_text(encoding="utf-8"), rf"NPC_BRS_FLAME_WHELP\s*=\s*{WHELP},")

    def test_the_item_and_the_toss(self):
        # The stock 13371 is untouched: no item_template edit anywhere (the keepsake); the flame is the custom 70610.
        self.assertEqual(self.items, [])
        self.assertEqual(self.package_items, [])
        item = FF.FATHER_FLAME
        self.assertEqual((item["entry"], FF.ITEM_FATHER_FLAME, FF.ITEM_FATHER_FLAME_KEEPSAKE), (ITEM, ITEM, KEEPSAKE))
        self.assertEqual(item["inventory_type"], 0)         # INVTYPE_NON_EQUIP: used from the bags (R-2-A B-1)
        self.assertEqual(item["spell"], TOSS)
        self.assertEqual(item["map"], 229)
        self.assertGreater(ITEM, 56806)                     # a custom item: it needs its Item.dbc row
        self.assertTrue(70000 <= ITEM <= 70999)             # the hand-picked items.csv part of the item block
        rework = REWORK.read_text(encoding="utf-8")
        self.assertRegex(rework, rf"kItemFatherFlame = {ITEM};")
        self.assertRegex(rework, rf"kItemFatherFlameKeepsake = {KEEPSAKE};")
        # The client Item.dbc / server item_dbc row (items.csv): class, subclass, sound, material, display, slot,
        # sheath.
        rows = [line.split(",", 8) for line in ITEMS_CSV.read_text(encoding="utf-8").splitlines()
                if line.startswith(f"{ITEM},")]
        self.assertEqual(len(rows), 1)
        self.assertEqual([int(v) for v in rows[0][1:8]], [item["class"], item["subclass"], -1, item["material"],
                                                          item["display"], item["inventory_type"], item["sheath"]])
        # The SQL item_template row carries the same values.
        sql = SQL.read_text(encoding="utf-8")
        row = re.search(rf"\({ITEM}, (\d+), (\d+), -1, '([^']*)', (\d+), \d+, 0, 1, 0, 0, (\d+), -1, -1, \d+, 0, 1, 1, "
                        rf"(\d+), 0, 0, 0, -1, 0, -1, 1,\s*'([^']*)', (-?\d+), (\d+), (\d+), 0\)", sql)
        self.assertIsNotNone(row)
        cls_, sub, name, display, invtype, spell, desc, material, sheath, map_ = row.groups()
        self.assertEqual((int(cls_), int(sub), name, int(display), int(invtype), int(spell), desc, int(material),
                          int(sheath), int(map_)),
                         (item["class"], item["subclass"], item["name"], item["display"], item["inventory_type"],
                          item["spell"], item["description"], item["material"], item["sheath"], item["map"]))
        toss = self.spells[TOSS]
        self.assertEqual(toss["effect1"]["type"], DUMMY_EFFECT)
        self.assertEqual(toss["effect1"]["implicit_target_a"], TARGET_UNIT_TARGET_ALLY)
        self.assertEqual(toss["range_yards"], _header_value("kTossRangeYd"))
        self.assertEqual(_raw(toss, "Speed"), _header_value("kTossSpeed"))
        self.assertEqual(_raw(toss, "CasterAuraSpell"), FLAME)      # only the holder
        self.assertTrue(_raw(toss, "AttributesEx5") & ATTR5_ALLOW_WHILE_STUNNED)
        self.assertEqual(_raw(toss, "SpellVisualID_1"), V.SK_TORCH_TOSS)
        self.assertIn((TOSS, "spell_brs_solakar_flame_toss"), self.scripts)
        # The flight (30 yd) is shorter than the pass's Flight.
        self.assertLess(_header_value("kTossRangeYd") / _header_value("kTossSpeed") * 1000,
                        _header_value("kTossFlightMs"))

    def test_the_holder_aura_and_the_burn(self):
        flame = self.spells[FLAME]
        self.assertEqual(flame["duration_ms"], -1)
        self.assertEqual(flame["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(flame["dispel"], 0)
        self.assertTrue(flame["attributes"] & ATTR0_NO_AURA_CANCEL)
        self.assertFalse(flame["attributes"] & ATTR0_PASSIVE)
        self.assertEqual(_raw(flame, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)
        self.assertEqual(_raw(flame, "SpellVisualID_1"), V.SV_TORCH_HELD)
        self.assertEqual(_raw(self.spells[STOLEN], "SpellVisualID_1"), V.SV_TORCH_HELD)
        burn = self.spells[SEARING]
        self.assertEqual(burn["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertEqual(burn["school"], SCHOOL_FIRE)
        self.assertEqual(burn["effect1"]["implicit_target_a"], 1)     # the holder on themself
        self.assertTrue(_raw(burn, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        scorched = self.spells[SCORCHED]
        self.assertEqual(scorched["duration_ms"], 25000)      # the longest; the script shortens it at 5 players
        self.assertEqual(scorched["dispel"], 0)
        for spell_id, visual in ((CATCH_FLARE, V.SK_TORCH_CATCH), (HATCH_BURST, V.SK_EGG_HATCH_BURST),
                                 (HATCHER_HATCH, V.SK_EGG_HATCH_CAST), (STOMP_LOOK, V.SK_WAR_STOMP),
                                 (CAUTERIZE, V.SK_SPEAR_CLEANSE)):
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), visual, spell_id)

    def test_flamewreath_and_the_enrage(self):
        normal, heroic = _header_nh("kFlamewreathPctPerStack")
        for spell_id, pct in ((WREATH, normal), (WREATH_H, heroic)):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["apply_aura"], AURA_MOD_DAMAGE_PERCENT_DONE, spell_id)
            self.assertEqual(spell["effect1"]["base_points"], int(pct), spell_id)
            self.assertEqual(spell["effect1"]["misc_value"], 127, spell_id)
            self.assertEqual(_raw(spell, "CumulativeAura"), int(_header_value("kFlamewreathCap")), spell_id)
            self.assertEqual(spell["duration_ms"], -1, spell_id)
            self.assertEqual(_raw(spell, "SpellVisualID_1"), V.SK_FLAME_WREATH, spell_id)
        self.assertEqual((normal, heroic), (20.0, 25.0))
        self.assertEqual(self.spells[WREATHED]["duration_ms"], -1)

    def test_the_bars_and_the_stomps(self):
        for spell_id, ms_name in ((HUNT_ROAR, "kHuntRoarMs"), (STOMP_BAR, "kStompCastMs"),
                                  (GROUND_BAR, "kStompCastMs")):
            bar = self.spells[spell_id]
            self.assertEqual(bar["cast_time_ms"], int(_header_value(ms_name)), spell_id)
            self.assertEqual(_raw(bar, "InterruptFlags"), 0, spell_id)
            self.assertEqual(_raw(bar, "PreventionType"), 0, spell_id)
        self.assertEqual(_raw(self.spells[HUNT_ROAR], "SpellVisualID_1"), V.SK_HUNT_ROAR)
        self.assertEqual(self.spells[HUNT]["duration_ms"], int(_header_value("kHuntChaseMs")))
        self.assertEqual(self.spells[HUNTED]["duration_ms"], int(_header_value("kHuntChaseMs")))
        for spell_id in (STOMP, GROUND):
            self.assertIn((spell_id, RESOLVE), self.scripts)
            self.assertEqual(self.spells[spell_id]["school"], SCHOOL_PHYSICAL)
        stun = self.spells[STOMP_STUN]
        self.assertEqual(stun["effect1"]["apply_aura"], AURA_MOD_STUN)
        self.assertEqual(stun["mechanic"], MECHANIC_STUN)
        self.assertEqual(stun["duration_ms"], int(_header_value("kWarStompStunMs")))
        self.assertEqual(stun["duration_ms"], 2000)     # the shared limit on loss of control

    def test_the_percent_hits_and_the_spear(self):
        for spell_id, school in ((WREATHED_TICK, SCHOOL_FIRE), (SPEAR_TEAR, SCHOOL_PHYSICAL)):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertEqual(spell["school"], school, spell_id)
            self.assertIn((spell_id, REF_PCT), self.scripts)
            self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS, spell_id)
        throw = self.spells[SPEAR_THROW]
        self.assertEqual(_raw(throw, "SpellVisualID_1"), V.SK_SPEAR_THROW)
        self.assertGreater(_raw(throw, "Speed"), 0)
        self.assertIn((SPEAR_THROW, "spell_brs_solakar_spear_throw"), self.scripts)
        wound = self.spells[SPEAR_WOUND]
        self.assertEqual(wound["effect1"]["apply_aura"], AURA_PERIODIC_DAMAGE)
        self.assertEqual(wound["effect1"]["amplitude"], 1000)
        self.assertEqual(wound["duration_ms"], int(_header_value("kSpearWoundMs")))
        self.assertEqual(wound["mechanic"], MECHANIC_BLEED)
        self.assertEqual(wound["dispel"], 0)            # only the flame cleans it
        self.assertEqual(_raw(wound, "SpellVisualID_1"), V.SK_SPEAR_WOUND)
        self.assertIn((SPEAR_WOUND, "spell_brs_solakar_spear_wound"), self.scripts)

    def test_no_wrong_or_local_looks(self):
        # V-2's wrong picks never wired (12075 Torch, 8855 / 10724 the old spears); no local display or visual ids.
        looks = {_raw(s, "SpellVisualID_1") for s in self.spells.values()}
        for wrong in (12075, 8855, 10724):
            self.assertNotIn(wrong, looks)
        source = (PACKAGE / "solakar.py").read_text(encoding="utf-8")
        self.assertNotRegex(source, r"SpellVisualID_1=\d")
        self.assertNotIn("\t", self.cpp)

    def test_the_cpp_uses_the_declared_names_and_the_pass(self):
        for name in ("SPELL_SK_FATHER_FLAME", "SPELL_SK_SEARING_HEAT", "SPELL_SK_SCORCHED_HANDS", "SPELL_SK_HUNT_ROAR",
                     "SPELL_SK_HUNT", "SPELL_SK_WAR_STOMP", "SPELL_SK_WAR_STOMP_STUN", "SPELL_SK_GROUND_STOMP",
                     "SPELL_SK_SPEAR_THROW", "SPELL_SK_SPEAR_WOUND", "SPELL_SK_SPEAR_TEAR", "SPELL_SK_WREATHED_TICK"):
            self.assertIn(name, self.cpp, name)
        # The pass (WP-PS): by the item, the holder aura, not Scorched (heroic: or wounded), off the eggs.
        self.assertIn("PassEntry::WithItem(SPELL_SK_FATHER_FLAME, kItemFatherFlame", self.cpp)
        self.assertIn("FewestZones(TAG_EGG_CLUTCH", self.cpp)
        # Full bags (R-2 ruling): the toss refuses, the landing refuses, the pickups and the bots' catchers skip them.
        self.assertGreaterEqual(self.cpp.count("!FlameRoom(catcher)"), 2)
        self.assertIn("spec.who.carriers = RoomCarriers();", self.cpp)
        self.assertRegex(self.cpp, r"BossCondition::Custom\(\[\]\(Unit const\* u\)\s*\{\s*return FlameRoom\(")
        self.assertIn("bags are full", self.cpp)
        self.assertIn("d.passes.push_back", self.cpp)
        # The registry carries the header's percents, never a literal.
        self.assertIn("kWarStompPct * WreathMult(", self.cpp)
        self.assertIn("Damage(kGroundStompPct)", self.cpp)
        # The instance's event: one pair, Solakar hidden at once, the arrival at 30 s, a reset that brings Father
        # Flame back.
        instance = INSTANCE.read_text(encoding="utf-8")
        self.assertIn("ACTION_SOLAKAR_ARRIVE", instance)
        self.assertIn("ACTION_SOLAKAR_RESET", instance)
        self.assertIn("kSolakarArriveMs", instance)
        self.assertNotIn("kSolakarWaveCount", instance)
        # R-2 M-2: a loaded Father Flame or egg comes back while the event is not running (a restart mid-event);
        # n-1: tosses and drops do not save the instance.
        self.assertRegex(instance, r"case GO_FATHER_FLAME:\s*case GO_ROOKERY_EGG:\s*RespawnSolakarObject\(go\);")
        self.assertIn("if (_solakarEvent != NOT_STARTED || GetBossState(BOSS_SOLAKAR) == DONE)", instance)
        self.assertIn("if (!SolakarFlameSaved(data))", instance)
        self.assertRegex(REWORK.read_text(encoding="utf-8"), r"kSolakarArriveMs = 30000;")


class SolakarSqlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8")

    def test_the_texts(self):
        groups = dict(re.findall(r"TEXT_(?!HATCHER)(\w+)\s*=\s*(\d+),", _header()))
        self.assertEqual(sorted(int(v) for v in groups.values()), [0, 1, 2, 3, 4])
        self.assertRegex(self.sql, rf"\({SOLAKAR}, 0, 0, '[^\n]*', 14, 0, 100, ")      # the arrival yell
        for group in (1, 2, 3, 4):
            self.assertRegex(self.sql, rf"\({SOLAKAR}, {group}, 0, '[^\n]*', 41, 0, 100, ", group)
        self.assertRegex(self.sql, rf"\({HATCHER}, 1, 0, '%s snatches Father Flame!', 41, ")
        self.assertIn(f"DELETE FROM `creature_text` WHERE `CreatureID` = {SOLAKAR} AND `GroupID` BETWEEN 0 AND 4;",
                      self.sql)
        self.assertIn(f"DELETE FROM `creature_text` WHERE `CreatureID` = {HATCHER} AND `GroupID` = 1;", self.sql)
        # The Hatcher's stock line 0 stays.
        self.assertNotRegex(self.sql, rf"`CreatureID` = {HATCHER} AND `GroupID` (= 0|BETWEEN 0)")

    def test_the_pair_and_father_flame(self):
        for entry in (GUARDIAN, HATCHER):
            self.assertIn(f"DELETE FROM `smart_scripts` WHERE `entryorguid` = {entry} AND `source_type` = 0;",
                          self.sql)
        self.assertRegex(self.sql, r"UPDATE `gameobject_template` SET `ScriptName` = 'go_brs_father_flame' WHERE "
                                   r"`entry` = 175245;")
        # Nothing else: no loot, no spawn; the one item row is the new 70610 (an upsert), never the stock 13371.
        self.assertNotIn("loot_template", self.sql)
        self.assertNotIn("UPDATE `creature`", self.sql)
        self.assertEqual(re.findall(r"(?m)^(?!--).*`item_template`", self.sql), ["INSERT INTO `item_template`"])
        self.assertIn(f"\n({ITEM}, ", self.sql)
        self.assertNotRegex(self.sql, rf"(?m)^(?!--).*\b{KEEPSAKE}\b")      # only comments name it
        self.assertNotIn("DELETE FROM `item_template`", self.sql)


if __name__ == "__main__":
    unittest.main()
