"""
Stratholme build WP-S8, the Grand Lie (Balnazzar's hard mode): source/npcs/stratholme/balnazzar_hard_mode.py and
source/items/stratholme_relics.py against their C++ (modules/mod-dungeon-bosses src/Stratholme/GrandLieLogic.h,
balnazzar_hard_mode.cpp), the relics' Item.dbc rows (source/items.csv) and the SQL rev
(data/sql/updates/pending_db_world/rev_balnazzar_hard_mode_stratholme.sql).

Checks:
  - the spells sit in the Grand Lie's slice (206575-206604, never S7's 206545-206574) and GrandLieLogic.h names the
    same ids; 206575-206584 are the boss file's, 206585-206588 the relics file's;
  - the swarm stalker 300609: unselectable, invisible, no heroic template, bound to npc_st_moving_swarm;
  - the twins and the swarm tick are resolve copies; the share, the mark and the cast bar carry GrandLieLogic.h's
    numbers; the relic use spells' effects and targets match the SpellScript hooks that bind them (a mismatch unbinds
    the hook at boot) and their sizes match the header;
  - every relic has a client Item.dbc row (source/items.csv) and an item_template row (the SQL rev) that agree on the
    class, the look and the use spell (a custom item needs both, memory dbc-tools-item-support);
  - the SQL rev: the texts, the gameobjects bound to go_st_grand_lie_relic and their heroic spawns at the header's
    spots.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_stratholme_grand_lie.py
"""

from __future__ import annotations

import csv
import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import test_id_blocks as id_blocks  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.test_hard_mode_item_effects import _load_items_registry  # noqa: E402

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Stratholme"
HEADER = MODULE_DIR / "GrandLieLogic.h"
SCRIPT = MODULE_DIR / "balnazzar_hard_mode.cpp"
REWORK = MODULE_DIR / "StratholmeRework.h"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_balnazzar_hard_mode_stratholme.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "stratholme"
ITEMS_CSV = TOOL_ROOT / "source" / "items.csv"
RELICS_FILE = TOOL_ROOT / "source" / "items" / "stratholme_relics.py"
VISUALS = PACKAGE / "_visuals.py"

SLICE = range(206575, 206605)
S7_SLICE = range(206545, 206575)
BOSS_SPELLS = range(206575, 206585)
RELIC_SPELLS = range(206585, 206589)
(CLEAVE_LIGHT, CLEAVE_BLADE, RING_LIGHT, RING_DARK, MARK, MARK_SHARE, MARK_BURST, SWARM_CLOUD, SWARM_BITE,
 DREAD_SLUMBER, LETTER, HOLY_WATER, STANDARD, MEDALLION) = range(206575, 206589)
SWARM = 300609
RELIC_ITEMS = (70600, 70601, 70602, 70603)

DUMMY, SCHOOL_DAMAGE, APPLY_AURA, PERSISTENT_AREA_AURA = 3, 2, 6, 27
AURA_DUMMY, AURA_MECHANIC_IMMUNITY = 4, 77
TARGET_UNIT_CASTER, TARGET_DEST_CASTER, TARGET_SRC_CASTER, TARGET_DEST_DYNOBJ_ALLY = 1, 18, 22, 29
TARGET_UNIT_SRC_AREA_ALLY, TARGET_DEST_DEST = 31, 87
MECHANIC_SLEEP = 10
AURA_INTERRUPT_CHANGE_MAP = 0x00080000
DISPLAY_INVISIBLE_STALKER = 11686
RESOLVE = "spell_boss_mechanics_resolve"


def _load_npcs():
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


def _header_number(name: str) -> float:
    match = re.search(rf"{name}\s*=\s*(-?[\d.]+)f?;", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return float(match.group(1))


def _header_spot(name: str) -> tuple[float, float, float, float]:
    match = re.search(rf"{name}\{{\s*([-\d.]+)f,\s*([-\d.]+)f,\s*([-\d.]+)f,\s*([-\d.]+)f\s*\}}",
                      HEADER.read_text(encoding="utf-8"))
    assert match, name
    return tuple(float(g) for g in match.groups())


def _visual(name: str) -> int:
    match = re.search(rf"^{name}\s*=\s*(\d+)", VISUALS.read_text(encoding="utf-8"), re.M)
    assert match, name
    return int(match.group(1))


class GrandLieDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        npcs = _load_npcs()
        items = _load_items_registry()
        cls.spells = {}
        for reg in (npcs, items):
            for e in reg.spells:
                if int(e["id"]) in SLICE or int(e["id"]) in S7_SLICE:
                    cls.spells[int(e["id"])] = e
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for reg in (npcs, items)
                       for e in reg.spell_script_names if int(e["spell_id"]) in SLICE}
        cls.item_spell_ids = {int(e["id"]) for e in items.spells if int(e["id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in npcs.creature_templates if int(e["entry"]) == SWARM}
        cls.models = {int(e["CreatureID"]): e for e in npcs.creature_template_models if int(e["CreatureID"]) == SWARM}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.sql = SQL.read_text(encoding="utf-8")
        with open(ITEMS_CSV, newline="", encoding="utf-8") as f:
            cls.csv_rows = {int(r["id"]): r for r in csv.DictReader(f) if r.get("id", "").strip().isdigit()}
        namespace: dict = {}
        source = RELICS_FILE.read_text(encoding="utf-8")
        relics = re.search(r"^RELICS = \{.*?^\}", source, re.M | re.S)
        assert relics, "RELICS"
        exec(relics.group(0), namespace)  # noqa: S102 - a literal dict from our own source file
        cls.relics = namespace["RELICS"]

    def test_spells_fill_the_slice_and_match_the_header(self):
        mine = sorted(i for i in self.spells if i in SLICE)
        self.assertEqual(mine, list(range(206575, 206589)))
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"spell": mine}), [])
        self.assertEqual(self.item_spell_ids, set())    # source/items spells must sit in an item reservation
        header_ids = {int(v) for v in re.findall(r"SPELL_GL_\w+\s*=\s*(\d+)", self.header)}
        self.assertEqual(header_ids, set(mine))
        self.assertFalse(header_ids & set(S7_SLICE))
        self.assertIn("kSpellsGrandLie{ 206575, 206604 }", REWORK.read_text(encoding="utf-8"))

    def test_swarm_stalker(self):
        self.assertEqual(sorted(self.creatures), [SWARM])
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"creature": [SWARM]}), [])
        swarm = self.creatures[SWARM]
        self.assertEqual(swarm["ScriptName"], "npc_st_moving_swarm")
        self.assertTrue(swarm["unit_flags"] & 0x02000000)       # not selectable
        self.assertTrue(swarm["unit_flags"] & 0x2)              # not attackable
        self.assertEqual(swarm.get("difficulty_entry_1", 0), 0)     # hard mode only: no heroic template (s7 #15)
        self.assertEqual(swarm["lootid"], 0)
        self.assertEqual(self.models[SWARM]["CreatureDisplayID"], DISPLAY_INVISIBLE_STALKER)
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_st_moving_swarm", self.cpp)
        self.assertEqual(_raw(self.spells[SWARM_CLOUD], "SpellVisualID_1"), _visual("BZ_SWARM_CLOUD"))

    def test_resolve_copies_and_scripts(self):
        for spell_id in (CLEAVE_LIGHT, CLEAVE_BLADE, RING_LIGHT, RING_DARK, MARK_BURST, SWARM_BITE):
            self.assertIn((spell_id, RESOLVE), self.scripts, spell_id)
            self.assertEqual(self.spells[spell_id]["effect1"]["type"], SCHOOL_DAMAGE)
            self.assertTrue(_raw(self.spells[spell_id], "SpellVisualID_1"), spell_id)      # a visible impact
        expected = {
            (LETTER, "spell_strat_grand_lie_letter"), (HOLY_WATER, "spell_strat_grand_lie_holy_water"),
            (MEDALLION, "spell_strat_grand_lie_medallion"), (STANDARD, "spell_strat_grand_lie_standard"),
        }
        self.assertTrue(expected <= self.scripts)
        self.assertEqual(len(self.scripts), 6 + len(expected))
        for _, name in expected:
            self.assertIn(f"RegisterSpellScript({name})", self.cpp)
        # The hooks name the effects the spells carry (a mismatch unbinds the hook at boot).
        letter = self.spells[LETTER]["effect1"]
        self.assertEqual((letter["type"], letter["implicit_target_a"]), (DUMMY, TARGET_UNIT_CASTER))
        self.assertIn("OnEffectHit += SpellEffectFn(spell_strat_grand_lie_letter::Read, EFFECT_0, SPELL_EFFECT_DUMMY)",
                      self.cpp)
        water = self.spells[HOLY_WATER]["effect1"]
        self.assertEqual((water["type"], water["implicit_target_a"]), (DUMMY, TARGET_DEST_DEST))
        self.assertIn("OnEffectHit += SpellEffectFn(spell_strat_grand_lie_holy_water::Splash, EFFECT_0, "
                      "SPELL_EFFECT_DUMMY)", self.cpp)
        medallion = self.spells[MEDALLION]["effect1"]
        self.assertEqual((medallion["type"], medallion["apply_aura"], medallion["misc_value"]),
                         (APPLY_AURA, AURA_MECHANIC_IMMUNITY, MECHANIC_SLEEP))
        self.assertEqual((medallion["implicit_target_a"], medallion["implicit_target_b"]),
                         (TARGET_SRC_CASTER, TARGET_UNIT_SRC_AREA_ALLY))
        self.assertIn("SpellEffectFn(spell_strat_grand_lie_medallion::Wake, EFFECT_0, SPELL_EFFECT_APPLY_AURA)",
                      self.cpp)
        # The Standard's bots' Stack (F-2 MIN-1) hooks the cast, not an effect.
        self.assertIn("AfterCast += SpellCastFn(spell_strat_grand_lie_standard::Raised);", self.cpp)
        # The relics' gameobjects and the boss AI's hooks are registered.
        self.assertIn("RegisterDungeonReworkGameObjectAI(go_st_grand_lie_relic", self.cpp)
        self.assertIn("StratDathrohan::RegisterGrandLie(", self.cpp)

    def test_numbers_match_the_header(self):
        self.assertEqual(self.spells[MARK]["duration_ms"], int(_header_number("kCallLandMs")))
        self.assertTrue(_raw(self.spells[MARK], "AuraInterruptFlags") & AURA_INTERRUPT_CHANGE_MAP)
        self.assertEqual(self.spells[MARK]["dispel"], 0)
        self.assertEqual(self.spells[DREAD_SLUMBER]["cast_time_ms"], int(_header_number("kSlumberCastMs")))
        self.assertEqual(_raw(self.spells[DREAD_SLUMBER], "InterruptFlags"), 0)     # cannot be interrupted
        share = self.spells[MARK_SHARE]["effect1"]
        self.assertEqual((share["type"], share["base_points"], share["die_sides"]), (SCHOOL_DAMAGE, 0, 0))
        standard = self.spells[STANDARD]
        effect = standard["effect1"]
        self.assertEqual((effect["type"], effect["apply_aura"]), (PERSISTENT_AREA_AURA, AURA_DUMMY))
        self.assertEqual((effect["implicit_target_a"], effect["implicit_target_b"]),
                         (TARGET_DEST_CASTER, TARGET_DEST_DYNOBJ_ALLY))
        self.assertEqual(effect["radius_yards"], _header_number("kStandardRadiusYd"))
        self.assertEqual(standard["duration_ms"], int(_header_number("kStandardMs")))
        self.assertEqual(self.spells[MEDALLION]["effect1"]["radius_yards"], _header_number("kMedallionRadiusYd"))
        self.assertEqual(self.spells[MEDALLION]["duration_ms"], int(_header_number("kMedallionWardMs")))
        self.assertEqual(self.spells[HOLY_WATER]["range_yards"], _header_number("kHolyWaterRangeYd"))
        self.assertEqual(self.spells[HOLY_WATER]["effect1"]["radius_yards"], _header_number("kHolyWaterSplashYd"))
        # The swarms and the cones read the Standard's own aura as the ward.
        self.assertIn("e.auraSpell = SPELL_GL_STANDARD;", self.cpp)
        self.assertIn("spec.wardAura = SPELL_GL_STANDARD;", self.cpp)
        # V-2's picks on the relics' looks.
        for spell_id, name in ((HOLY_WATER, "DA_HOLY_WATER"), (STANDARD, "DA_TRUE_GROUND"),
                               (MEDALLION, "DA_TRUE_JUDGMENT_ALT")):
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), _visual(name), name)

    def test_relic_items_have_both_rows(self):
        self.assertEqual(sorted(self.relics), list(RELIC_ITEMS))
        rework = REWORK.read_text(encoding="utf-8")
        for entry, (name, display, spell_id, cooldown, go) in self.relics.items():
            # The client Item.dbc and server item_dbc row (source/items.csv).
            row = self.csv_rows.get(entry)
            self.assertIsNotNone(row, entry)
            self.assertEqual((int(row["class_id"]), int(row["subclass_id"]), int(row["display_info_id"])),
                             (15, 4, display), entry)
            self.assertEqual((int(row["inventory_type"]), int(row["sheathe_type"]), int(row["material"])),
                             (0, 0, -1), entry)
            # The item_template row (the SQL rev) agrees and names the use spell and the per-copy cooldown.
            sql_name = name.replace("'", "''")
            pattern = (rf"\({entry}, 15, 4, -1, '{re.escape(sql_name)}', {display}, 1, 0, 1, 0, 0, 0, -1, -1, 60, 0, "
                       rf"1, 1, {spell_id}, 0, 0, 0, {cooldown}, 0,\s*-1,\s*1,\s*'[^']*(?:''[^']*)*', -1,"
                       rf"\s*0, 329, 0\)")
            self.assertRegex(self.sql, pattern, entry)
            self.assertIn(spell_id, RELIC_SPELLS)
            self.assertIn(f"({go}, 10, ", self.sql)
            self.assertRegex(rework, rf"= {entry},")
        # Per-copy cooldowns (ruling 33) match the header.
        self.assertEqual(self.relics[70601][3], int(_header_number("kStandardCooldownMs")))
        self.assertEqual(self.relics[70602][3], int(_header_number("kHolyWaterCooldownMs")))
        self.assertEqual(self.relics[70603][3], int(_header_number("kMedallionCooldownMs")))

    def test_the_sql_rev(self):
        sql = re.sub(r"\s+", " ", self.sql)     # rows wrap at 120 columns
        for group, kind in ((8, 12), (9, 14)):
            self.assertRegex(sql, rf"\(10812, {group}, 0, '[^']+(?:''[^']*)*', {kind},")
        for group in range(10, 17):
            self.assertIn(f"(10813, {group}, 0, '", sql)
        # True lines say "the Light", lies never do (ruling 28).
        for group, is_true in ((10, True), (11, False), (12, True), (13, False), (14, True), (15, False)):
            line = re.search(rf"\(10813, {group}, 0, '((?:[^']|'')*)'", sql).group(1)
            self.assertEqual("Light" in line, is_true, group)
        # Four goobers bound to the relic AI, heroic spawns only, at the header's spots.
        for go in (301203, 301204, 301205, 301206):
            self.assertRegex(sql, rf"\({go}, 10, \d+, '[^']+(?:''[^']*)*', '', '', '', 1, (0, ){{24}}'', "
                                  rf"'go_st_grand_lie_relic', 0\)")
        spots = {301203: "kLetterSpot", 301204: "kStandardSpot", 301205: "kMedallionLightSpot",
                 301206: "kBlessedCrateSpot"}
        for go, name in spots.items():
            x, y, z, o = _header_spot(name)
            self.assertRegex(sql, rf"\(\d+, {go}, 329, 0, 0, 2, 1, {x:g}, {y:g}, {z:g}, {o:g}, ")
        # The swarm is never a heroic copy and no stock row is touched.
        self.assertNotIn("smart_scripts", sql)


if __name__ == "__main__":
    unittest.main()
