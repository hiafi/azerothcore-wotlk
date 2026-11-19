"""
Blackrock Depths build WP-D18, Hurley Blackbreath: source/npcs/blackrock_depths/hurley.py against its C++
(modules/mod-dungeon-bosses src/BlackrockDepths/HurleyLogic.h, boss_hurley_blackbreath_rework.cpp) and its SQL rev
(data/sql/updates/pending_db_world/rev_hurley_blackrock_depths.sql).

Wave 2: Hurley's and the Cronies' columns and the keg's ScriptName sit behind BIND_WAVE_2 (_common.py), so this test
checks the declarations directly: the columns through the file's HURLEY_COLUMNS / CRONY_COLUMNS, the gate in both
positions through a copy of the package with the switch written True. Nothing here needs the switch on.

Checks:
  - the spells sit in his slice (211430-211459) and HurleyLogic.h names the same ids; the keg and puddle entries are
    the header's;
  - Hurley and the Cronies are bound once wave 2 is (SmartAI off, health at 5 players, the C++ registrations inside
    kWave2Bound), and nothing is declared for them while the switch is off;
  - the keg (not selectable, 6,000, the minted G_Keg display, WP-H's lock line) and the puddle (a helper);
  - Mortal Strike and the tank's breath (refflat copies), the breath's cone and the two heroic hits (resolve copies),
    the drink, Liquid Courage, Lager Buzz and Tipsy against the header's numbers; the looks on V-1's ids, no WRONG one;
  - the SQL rev: the SmartAI drops, the 43,200 s respawn, the four new texts; WP-H's heroic numbers match the header.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_hurley.py
"""

from __future__ import annotations

import math
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import test_id_blocks as id_blocks  # noqa: E402
from lib.dsl import registry  # noqa: E402

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockDepths"
HEADER = MODULE_DIR / "HurleyLogic.h"
REWORK = MODULE_DIR / "BlackrockDepthsRework.h"
SCRIPT = MODULE_DIR / "boss_hurley_blackbreath_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_hurley_blackrock_depths.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_depths"
VISUALS = PACKAGE / "_visuals.py"
HEROIC = TOOL_ROOT / "source" / "world" / "dungeons" / "blackrock_depths.py"

SLICE = range(211430, 211460)
(MORTAL_STRIKE, BREATH_BAR, BREATH, BREATH_TANK, BREATH_LOOK, DRINK, COURAGE, COURAGE_FLASH, KEG_MARK, LAGER_BUZZ,
 TIPSY, PUDDLE_LOOK, BURNING_LAGER, BURNING_LOOK, BOTTLE_TOSS, BOTTLE_LOOK) = range(211430, 211446)
HURLEY, CRONY, KEG, PUDDLE = 9537, 9541, 300839, 300840
KEG_HEROIC = 310414
WARRIOR_55_BASE, WARRIOR_53_BASE = 2614, 2453

SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT = 2, 6, 3
AURA_DUMMY, AURA_MOD_DECREASE_SPEED, AURA_MOD_DAMAGE_PERCENT_DONE = 4, 33, 79
AURA_MOD_HEALING_PCT, AURA_MOD_MELEE_HASTE = 118, 138
SCHOOL_PHYSICAL, SCHOOL_FIRE = 1, 4
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
UNIT_FLAG_NOT_SELECTABLE = 0x02000000
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT = "spell_dungeon_refflat_damage"
IMMUNITY_BOSS_STUN = 1972
INSTANCE_BIND = 0x1
STALKER_DISPLAY_WRONG = 24860       # the spec's keg display: InvisibleStalker.mdx (VISUALS report, WRONG)
DRUNKEN_STUPOR_SV = 2816            # a stun swirl: never Tipsy's look (V-1)
CRONY_GUIDS = (71997, 71998, 71999)


def _load(package: Path = PACKAGE):
    t = id_blocks
    return registry.load_class_package(
        package, ids_cfg=t.IDS, trainer_index=t._AnyTrainer(), existing_group_ids=t._AnySet(),
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
    match = re.search(rf"^{name}\s*=\s*([\w\[\]]+)", text, re.MULTILINE)
    assert match, name
    value = match.group(1)
    if value.isdigit():
        return int(value)
    ladder = re.fullmatch(r"(\w+)\[(\d+)\]", value)
    if ladder:     # SHIPPED_LAVA_POOL[5]: a rung of a dict ladder
        body = re.search(rf"^{ladder.group(1)}\s*=\s*\{{([^}}]*)\}}", text, re.MULTILINE).group(1)
        return int(re.search(rf"\b{ladder.group(2)}:\s*(\d+)", body).group(1))
    return _visual(value)


def _bound_package() -> tempfile.TemporaryDirectory:
    """A copy of this boss's file with the wave switch written True (the shared _common.py and _visuals.py beside
    it)."""
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name) / "blackrock_depths"
    root.mkdir()
    for name in ("_visuals.py", "hurley.py"):
        shutil.copy(PACKAGE / name, root / name)
    common = (PACKAGE / "_common.py").read_text(encoding="utf-8")
    common = re.sub(r"^BIND_WAVE_2 = (True|False)$", "BIND_WAVE_2 = True", common, flags=re.M)
    (root / "_common.py").write_text(common, encoding="utf-8")
    return tmp


class HurleyDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) in (HURLEY, CRONY)}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) in (KEG, PUDDLE)}
        cls.models = {int(m["CreatureID"]): m for m in reg.creature_template_models
                      if int(m["CreatureID"]) in (KEG, PUDDLE)}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        with _bound_package() as tmp:
            bound = _load(Path(tmp) / "blackrock_depths")
        cls.bound_edits = {int(e["entry"]): e for e in bound.creature_template_edits}
        cls.bound_creatures = {int(e["entry"]): e for e in bound.creature_templates
                               if int(e["entry"]) in (KEG, PUDDLE)}

    # --- ids ---------------------------------------------------------------------------------------------------------

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(MORTAL_STRIKE, BOTTLE_LOOK + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"spell": mine}), [])
        first = re.search(r"kSpellsHurley\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(first)
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_HU_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))

    def test_the_keg_and_the_puddle_ids_are_the_headers(self):
        text = REWORK.read_text(encoding="utf-8")
        for name, entry in (("NPC_BRD_LAGER_KEG", KEG), ("NPC_BRD_LAGER_PUDDLE", PUDDLE)):
            self.assertRegex(text, rf"\b{name}\s*=\s*{entry},")
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"creature": [KEG, PUDDLE]}), [])

    # --- the stock units ---------------------------------------------------------------------------------------------

    def test_nothing_is_declared_for_the_stock_units_while_wave_2_is_off(self):
        common = (PACKAGE / "_common.py").read_text(encoding="utf-8")
        gate = re.search(r"^BIND_WAVE_2 = (True|False)$", common, re.M).group(1) == "True"
        self.assertEqual(HURLEY in self.edits, gate)
        self.assertEqual(CRONY in self.edits, gate)

    def test_hurley_is_bound_once_wave_2_is(self):
        boss = self.bound_edits[HURLEY]
        self.assertEqual(boss["ScriptName"], "boss_hurley_blackbreath_rework")
        self.assertEqual(boss["AIName"], "")
        self.assertEqual(boss["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
        self.assertEqual(boss["flags_extra"] & INSTANCE_BIND, INSTANCE_BIND)
        normal, heroic = _header_nh("kHurleyHealth")
        self.assertLessEqual(abs(math.ceil(WARRIOR_55_BASE * boss["HealthModifier"]) - normal), 2)
        self.assertEqual((normal, heroic), (140_000, 200_000))
        self.assertAlmostEqual(float(boss["DamageModifier"]), 7.5)
        for script in ("boss_hurley_blackbreath_rework", "npc_blackbreath_crony_rework", "npc_brd_lager_keg"):
            self.assertRegex(self.cpp, rf"if \(kWave2Bound\)\s*RegisterDungeonReworkCreatureAI\({script},")

    def test_the_cronies_are_bound_once_wave_2_is(self):
        crony = self.bound_edits[CRONY]
        self.assertEqual(crony["ScriptName"], "npc_blackbreath_crony_rework")
        self.assertEqual(crony["AIName"], "")
        normal, heroic = _header_nh("kCronyHealth")
        self.assertEqual(math.ceil(WARRIOR_53_BASE * float(crony["HealthModifier"])), int(normal))
        self.assertEqual((normal, heroic), (8_000, 12_000))
        self.assertAlmostEqual(float(crony["DamageModifier"]), 7.5)
        # the kept stock spells, not copies
        self.assertEqual(int(_header_value("SPELL_STOCK_SINISTER_STRIKE")), 15581)
        self.assertEqual(int(_header_value("SPELL_STOCK_RUPTURE")), 15583)

    def test_wp_h_heroic_numbers_match_the_header(self):
        text = HEROIC.read_text(encoding="utf-8")
        self.assertRegex(text, r"9537: _boss\(200_000, 310378\)")
        self.assertRegex(text, r"9541: dict\(health=12_000\)")
        self.assertRegex(text, r"300839: dict\(health=6_000\)")
        self.assertEqual(_header_nh("kKegHealth"), (4_000.0, 6_000.0))

    # --- the keg and the puddle --------------------------------------------------------------------------------------

    def test_the_keg(self):
        keg = self.creatures[KEG]
        self.assertEqual(keg["name"], "Thunderbrew Lager Keg")
        self.assertEqual((int(keg["minlevel"]), int(keg["maxlevel"])), (55, 55))
        self.assertEqual(math.ceil(WARRIOR_55_BASE * float(keg["HealthModifier"])), 4_000)
        self.assertTrue(int(keg["unit_flags"]) & UNIT_FLAG_NOT_SELECTABLE)    # selectable only once marked
        self.assertEqual(float(keg["DamageModifier"]), 0.0)
        self.assertEqual(int(keg["faction"]), 54)
        self.assertEqual(int(keg["CreatureImmunitiesId"]), IMMUNITY_BOSS_STUN)
        self.assertEqual(int(keg["lootid"]), 0)
        self.assertTrue(int(keg["flags_extra"]) & 0x40)                       # no XP
        self.assertEqual(int(keg["difficulty_entry_1"]), KEG_HEROIC)
        self.assertEqual(keg["AIName"], "")
        gate = re.search(r"^BIND_WAVE_2 = (True|False)$", (PACKAGE / "_common.py").read_text(encoding="utf-8"),
                         re.M).group(1) == "True"
        self.assertEqual(keg["ScriptName"], "npc_brd_lager_keg" if gate else "")   # follows the wave switch
        self.assertEqual(self.bound_creatures[KEG]["ScriptName"], "npc_brd_lager_keg")
        display = int(self.models[KEG]["CreatureDisplayID"])
        self.assertEqual(display, _visual("DISPLAY_LAGER_KEG"))
        self.assertEqual(display, 90770)
        self.assertNotEqual(display, STALKER_DISPLAY_WRONG)

    def test_the_puddle_is_a_helper(self):
        puddle = self.creatures[PUDDLE]
        self.assertEqual(puddle["name"], "Lager Puddle")
        self.assertEqual(int(puddle["unit_flags"]) & 0x02000002, 0x02000002)    # not selectable, not attackable
        self.assertEqual(int(puddle.get("difficulty_entry_1", 0) or 0), 0)       # no heroic template (s7 #2)
        self.assertEqual(puddle["ScriptName"], "")
        self.assertEqual(int(self.models[PUDDLE]["CreatureDisplayID"]), _visual("DISPLAY_INVISIBLE_STALKER"))

    # --- HU1, HU2 ----------------------------------------------------------------------------------------------------

    def _refflat(self, spell_id: int, header: str, school: int):
        spell = self.spells[spell_id]
        normal, heroic = _header_nh(header)
        hit = spell["effect1"]
        self.assertEqual(hit["type"], SCHOOL_DAMAGE)
        self.assertEqual(hit["base_points"] + hit["die_sides"], round(normal * 100))
        self.assertEqual(_raw(spell, "EffectMiscValueB_1"), round(heroic * 100))
        self.assertEqual(spell["school"], school)
        self.assertEqual(spell["cast_time_ms"], 0)
        self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertIn((spell_id, REFFLAT), self.scripts)
        return spell

    def test_mortal_strike_is_a_refflat_copy_with_the_healing_cut(self):
        spell = self._refflat(MORTAL_STRIKE, "kMortalStrikePct", SCHOOL_PHYSICAL)
        cut = spell["effect2"]
        self.assertEqual((cut["type"], cut["apply_aura"]), (APPLY_AURA, AURA_MOD_HEALING_PCT))
        self.assertEqual(cut["base_points"], -int(_header_value("kMortalStrikeHealingPct")))
        self.assertEqual(spell["duration_ms"], int(_header_value("kMortalStrikeMs")))
        self.assertEqual(spell["dispel"], 0)

    def test_flame_breath(self):
        bar = self.spells[BREATH_BAR]
        self.assertEqual(bar["cast_time_ms"], int(_header_value("kBreathCastMs")))
        self.assertEqual(_raw(bar, "InterruptFlags"), 0)          # no longer interruptible
        self.assertEqual(bar["school"], SCHOOL_FIRE)
        cone = self.spells[BREATH]
        self.assertIn((BREATH, RESOLVE), self.scripts)
        self.assertEqual(cone["school"], SCHOOL_FIRE)
        self._refflat(BREATH_TANK, "kBreathTankPct", SCHOOL_FIRE)
        self.assertEqual(_header_nh("kBreathPct"), (30.0, 45.0))
        self.assertEqual(_header_nh("kBreathTankPct"), (10.0, 15.0))
        self.assertIn("BossMechanics::TankExempt::Yes", self.cpp)
        self.assertIn(".Spell(SPELL_HU_FLAME_BREATH).Weakened()", self.cpp)
        self.assertEqual(_raw(self.spells[BREATH_LOOK], "SpellVisualID_1"), _visual("HU_FLAME_BREATH"))
        self.assertEqual(_visual("HU_FLAME_BREATH"), 7651)

    # --- HU3, HU4 ----------------------------------------------------------------------------------------------------

    def test_the_drink_and_liquid_courage(self):
        drink = self.spells[DRINK]
        self.assertEqual(drink["cast_time_ms"], int(_header_value("kDrinkMs")))
        self.assertEqual(_raw(drink, "InterruptFlags"), 0)
        self.assertEqual(_raw(drink, "SpellVisualID_1"), _visual("HU_DRINK"))
        self.assertEqual(_visual("HU_DRINK"), 101)
        courage = self.spells[COURAGE]
        damage, haste = courage["effect1"], courage["effect2"]
        self.assertEqual((damage["apply_aura"], damage["base_points"], damage["misc_value"]),
                         (AURA_MOD_DAMAGE_PERCENT_DONE, int(_header_value("kCourageDamagePct")), 127))
        self.assertEqual((haste["apply_aura"], haste["base_points"]),
                         (AURA_MOD_MELEE_HASTE, int(_header_value("kCourageHastePct"))))
        self.assertEqual(courage["duration_ms"], -1)                # the rest of the fight
        self.assertEqual(_raw(courage, "CumulativeAura"), int(_header_value("kKegCount")))
        self.assertEqual(courage["dispel"], 0)                      # not purgeable
        self.assertEqual(_raw(courage, "SpellVisualID_1"), _visual("HU_LIQUID_COURAGE"))
        self.assertEqual(_raw(self.spells[COURAGE_FLASH], "SpellVisualID_1"), _visual("HU_LAGER_BUZZ_FLASH"))
        self.assertEqual(int(_header_value("kDrinkHealPct")), 10)
        mark = self.spells[KEG_MARK]
        self.assertEqual(mark["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(mark["duration_ms"], -1)
        self.assertEqual(_raw(mark, "SpellVisualID_1"), _visual("HU_KEG_MARK"))
        # the kill order keys on the mark; the Cronies come next, AoE allowed
        self.assertIn("TargetEntry(NPC_BRD_LAGER_KEG, kKegPriority", self.cpp)
        self.assertIn("BossMechanics::Condition::HasAura(SPELL_HU_KEG_MARK)", self.cpp)
        self.assertIn("TargetEntry(NPC_BLACKBREATH_CRONY, kCronyPriority", self.cpp)

    # --- HU5, HU6 ----------------------------------------------------------------------------------------------------

    def test_the_puddle_auras(self):
        buzz = self.spells[LAGER_BUZZ]
        self.assertEqual((buzz["effect1"]["apply_aura"], buzz["effect1"]["base_points"]),
                         (AURA_MOD_DAMAGE_PERCENT_DONE, int(_header_value("kLagerBuzzPct"))))
        self.assertEqual(buzz["duration_ms"], int(_header_value("kLagerBuzzMs")))
        tipsy = self.spells[TIPSY]
        hit = tipsy["effect1"]
        self.assertEqual(hit["apply_aura"], AURA_MOD_DECREASE_SPEED)
        self.assertEqual(hit["base_points"] + hit["die_sides"], -int(_header_value("kTipsyPct")))
        self.assertEqual(tipsy["duration_ms"], int(_header_value("kTipsyMs")))
        self.assertEqual(_raw(tipsy, "SpellVisualID_1"), _visual("HU_TIPSY"))
        self.assertNotEqual(_raw(tipsy, "SpellVisualID_1"), DRUNKEN_STUPOR_SV)
        self.assertEqual(_raw(self.spells[PUDDLE_LOOK], "SpellVisualID_1"), _visual("SV_LAGER_PUDDLE"))
        self.assertEqual(_visual("SV_LAGER_PUDDLE"), 90650)
        burning = self.spells[BURNING_LAGER]
        self.assertIn((BURNING_LAGER, RESOLVE), self.scripts)
        self.assertEqual(burning["school"], SCHOOL_FIRE)
        self.assertEqual(_raw(self.spells[BURNING_LOOK], "SpellVisualID_1"), _visual("HU_BURNING_LAGER"))
        self.assertEqual(_visual("HU_BURNING_LAGER"), 90607)       # the 5 yd lava rung
        self.assertEqual(_header_value("kBurningLagerPct"), 8.0)
        self.assertIn(".Spell(SPELL_HU_BURNING_LAGER)", self.cpp)

    # --- HU8 ---------------------------------------------------------------------------------------------------------

    def test_bottle_toss(self):
        toss = self.spells[BOTTLE_TOSS]
        self.assertIn((BOTTLE_TOSS, RESOLVE), self.scripts)
        self.assertEqual(toss["school"], SCHOOL_PHYSICAL)
        look = self.spells[BOTTLE_LOOK]
        self.assertEqual(look["effect1"]["type"], DUMMY_EFFECT)
        self.assertEqual(look["effect1"]["implicit_target_a"], 87)     # a destination
        self.assertEqual(_raw(look, "Targets"), 0x40)
        self.assertEqual(_raw(look, "SpellVisualID_1"), _visual("HU_BOTTLE_TOSS"))
        self.assertEqual(_header_value("kBottleTossPct"), 25.0)
        self.assertEqual(_header_value("kBottleRadius"), 3.0)
        self.assertIn(".Spell(SPELL_HU_BOTTLE_TOSS)", self.cpp)

    def test_nothing_wires_a_wrong_look(self):
        for spell in self.spells.values():
            self.assertNotEqual(_raw(spell, "SpellVisualID_1"), DRUNKEN_STUPOR_SV, spell["id"])
        for model in self.models.values():
            self.assertNotEqual(int(model["CreatureDisplayID"]), STALKER_DISPLAY_WRONG)

    # --- the SQL rev -------------------------------------------------------------------------------------------------

    def test_the_sql_rev(self):
        sql = SQL.read_text(encoding="utf-8")
        self.assertIn(f"DELETE FROM `smart_scripts` WHERE `entryorguid` = {HURLEY} AND `source_type` = 0;", sql)
        guids = ", ".join(f"-{g}" for g in CRONY_GUIDS)
        self.assertIn(f"DELETE FROM `smart_scripts` WHERE `entryorguid` IN ({guids}) AND `source_type` = 0;", sql)
        self.assertIn("UPDATE `creature` SET `spawntimesecs` = 43200 WHERE `id` = 9537 AND `guid` = 72000;", sql)
        self.assertIn("UPDATE `creature` SET `spawntimesecs` = 43200 WHERE `id` = 9541 AND `guid` IN (71997, 71998, "
                      "71999);", sql)
        # the keg GOs' SmartAI (the wake-up) is kept
        self.assertNotIn("164911", re.sub(r"^--.*$", "", sql, flags=re.M))
        # texts 2-5 (0-1 stock kept): yells, the drink a boss emote
        self.assertIn(f"DELETE FROM `creature_text` WHERE `CreatureID` = {HURLEY} AND `GroupID` BETWEEN 2 AND 5;", sql)
        for group in (2, 4, 5):
            self.assertRegex(sql, rf"\({HURLEY}, {group}, 0, '[^\n]*', 14,")
        self.assertRegex(sql, rf"\({HURLEY}, 3, 0, '%s drains the keg and roars with Liquid Courage!', 41,")
        self.assertIn("'All this fighting''s made me thirsty!'", sql)
        self.assertIn("'That was good ale, you fools!'", sql)
        self.assertIn("'Tell Ragnar... it was... delicious...'", sql)
        # nothing inserts a spawn or a SmartAI row (rule 14), nothing edits a template
        self.assertNotIn("INSERT INTO `creature` ", sql)
        self.assertNotIn("INSERT INTO `smart_scripts`", sql)
        self.assertNotIn("`creature_template`", sql)
        # the texts the C++ says are the header's groups
        for name, group in (("SAY_HURLEY_THIRSTY", 2), ("EMOTE_HURLEY_DRINK", 3), ("SAY_HURLEY_KEG_SMASHED", 4),
                            ("SAY_HURLEY_DEATH", 5)):
            self.assertRegex(_header(), rf"\b{name}\s*=\s*{group},")


if __name__ == "__main__":
    unittest.main()
