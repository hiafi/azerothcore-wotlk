"""
Scarlet Monastery build WP-D7, Lector Hollis Grey: source/npcs/scarlet_monastery/hollis_grey.py (his creature and
the five units of his stories, the spells 212610-212644), data/sql/updates/pending_db_world/
rev_hollis_grey_scarlet_monastery.sql (his spawn and texts), and the C++ side they must agree with (modules/
mod-dungeon-bosses src/ScarletMonastery/HollisGreyLogic.h and boss_lector_hollis_grey_rework.cpp).

Checks:
  - the 35 spells sit in the D7 slice and the C++ names the same ids; the hits are resolve copies in their schools;
    Searing Rebuke and Immolation are refflat percents (normal in the effect, heroic in EffectMiscValueB) that ignore
    the caster's modifiers; the two Open the Index casts: the normal one a 2 s bar nobody can kick, the heroic one a
    3 s kick in a school Searing Rebuke does not use; the stacking auras' caps; Dreaming is Magic and bound to its
    script; the looks carry V's visuals (never the doc's WRONG ones);
  - the creatures: his template (script, SmartAI off, 36k on the level 35 mage base, 1972, INSTANCE_BIND, FD-SM's
    credit creature), every story unit at his level with the build spec's health on the level 35 base, the looks not
    selectable, the displays V's (the book never the Rabbit 21955);
  - the SQL: the spawn in the pocket on both difficulties, texts 0-7 (yells and boss emotes), the C++ text groups;
  - the numbers the dbc-tools file pins are the header's; the switch is on in both places.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scarlet_monastery_hollis_grey.py
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
from source.npcs.scarlet_monastery import _visuals as visuals  # noqa: E402

MDB = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "ScarletMonastery"
LOGIC = MDB / "HollisGreyLogic.h"
SCRIPT = MDB / "boss_lector_hollis_grey_rework.cpp"
HEADER = MDB / "ScarletMonasteryRework.h"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_hollis_grey_scarlet_monastery.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "scarlet_monastery"
ENCOUNTERS = TOOL_ROOT / "lib" / "test_dungeon_encounters.py"

SLICE = range(212610, 212670)
NAMES = (
    "SPELL_LB_OPEN_THE_INDEX", "SPELL_LB_OPEN_THE_INDEX_HEROIC", "SPELL_LB_TURNING_THE_PAGE", "SPELL_LB_READERS_WARD",
    "SPELL_LB_STORY_SPIDER", "SPELL_LB_STORY_ARCHIMONDE", "SPELL_LB_STORY_TROLL_WARS", "SPELL_LB_STORY_TITANS",
    "SPELL_LB_STORY_DREAM", "SPELL_LB_STORY_AFTERMATH", "SPELL_LB_WEB_SPRAY", "SPELL_LB_WEB_SLOW",
    "SPELL_LB_WEB_PATCH", "SPELL_LB_HATCH", "SPELL_LB_METEOR", "SPELL_LB_INFERNO", "SPELL_LB_IMMOLATION",
    "SPELL_LB_THROW_AXE", "SPELL_LB_THROW_AXE_LOOK", "SPELL_LB_TITAN_STOMP", "SPELL_LB_WAR_STOMP",
    "SPELL_LB_GROUND_SLAM", "SPELL_LB_DREAM_MIST_6", "SPELL_LB_DREAM_MIST_9", "SPELL_LB_DREAM_MIST_12",
    "SPELL_LB_DROWSY", "SPELL_LB_DREAM_SLEEP", "SPELL_LB_DREAMING", "SPELL_LB_PHANTOM_CHARGE", "SPELL_LB_CHARGE_LOOK",
    "SPELL_LB_SEARING_REBUKE", "SPELL_LB_BURNING_BOOK", "SPELL_LB_BURNING_BOOK_LOOK", "SPELL_LB_DREAM_MIST",
    "SPELL_LB_WEB",
)
SPELL = {name: 212610 + i for i, name in enumerate(NAMES)}
EFFECT_SCHOOL_DAMAGE, EFFECT_APPLY_AURA, EFFECT_DUMMY = 2, 6, 3
AURA_DUMMY, AURA_MOD_STUN, AURA_MOD_DECREASE_SPEED, AURA_CASTING_SPEED, AURA_DAMAGE_TAKEN = 4, 12, 33, 65, 87
SCHOOL_PHYSICAL, SCHOOL_HOLY, SCHOOL_FIRE, SCHOOL_NATURE, SCHOOL_ARCANE = 1, 2, 4, 8, 64
IGNORE_CASTER_MODIFIERS = 0x20000000
ALWAYS_HIT = 0x00040000
INSTANCE_BIND = 0x1
IMMUNITY_BOSS_STUN = 1972
NOT_SELECTABLE = 0x02000000
BASE_MAGE_35, BASE_WARRIOR_35 = 902, 1220
POCKET = (254.8, -389.2)
HOLLIS_GREY, CURSED_BOOK, INFERNAL, SPIDERLING, SPECTRAL_TROLL, PHANTOM_GRUNT = range(300913, 300919)


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


class HollisGreyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        npcs = _load()
        cls.spells = {int(e["id"]): e for e in npcs.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in npcs.spell_script_names}
        cls.creatures = {int(e["entry"]): e for e in npcs.creature_templates}
        cls.models = {int(e["CreatureID"]): e for e in npcs.creature_template_models}
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.logic = LOGIC.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")

    def _const(self, name: str) -> str:
        match = re.search(rf"{name}\s*(?:=|\{{)\s*([^;}}]+?)\s*(?:;|\}};)", self.logic)
        self.assertIsNotNone(match, name)
        return re.sub(r"\s+", "", match.group(1))

    # --- the spells ---------------------------------------------------------------------------------------------------

    def test_the_spells_sit_in_the_d7_slice(self):
        self.assertEqual(sorted(self.spells), list(range(212610, 212645)))
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery", {"spell": list(self.spells)}), [])
        self.assertIn("kSpellsHollisGrey{ 212610, 212669 }", re.sub(r"\s+", " ", self.header))

    def test_the_cpp_names_the_same_ids(self):
        for offset, name in enumerate(NAMES):
            self.assertRegex(self.logic, rf"{name}\s*=\s*kSpellSlice\.first \+ {offset},", name)
        self.assertRegex(self.logic, r"kLastSpell = SPELL_LB_WEB;")

    def test_the_hits_are_resolve_copies_in_their_schools(self):
        for name, school in (("SPELL_LB_METEOR", SCHOOL_FIRE), ("SPELL_LB_THROW_AXE", SCHOOL_PHYSICAL),
                             ("SPELL_LB_TITAN_STOMP", SCHOOL_PHYSICAL), ("SPELL_LB_PHANTOM_CHARGE", SCHOOL_PHYSICAL),
                             ("SPELL_LB_BURNING_BOOK", SCHOOL_FIRE), ("SPELL_LB_DREAM_MIST", SCHOOL_NATURE),
                             ("SPELL_LB_WEB", SCHOOL_PHYSICAL)):
            with self.subTest(name=name):
                spell = self.spells[SPELL[name]]
                self.assertEqual(spell["school"], school)
                self.assertEqual(spell["effect1"]["type"], EFFECT_SCHOOL_DAMAGE)
                self.assertIn((SPELL[name], "spell_boss_mechanics_resolve"), self.scripts)
                self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & IGNORE_CASTER_MODIFIERS)

    def test_the_percent_spells(self):
        for name, normal, heroic, school, header in (
                ("SPELL_LB_SEARING_REBUKE", 2000, 3000, SCHOOL_HOLY, "kRebukePct"),
                ("SPELL_LB_IMMOLATION", 200, 200, SCHOOL_FIRE, "kImmolationPct")):
            with self.subTest(name=name):
                spell = self.spells[SPELL[name]]
                hit = spell["effect1"]
                raw = spell["raw_overrides"]
                self.assertEqual(spell["school"], school)
                self.assertEqual(hit["type"], EFFECT_SCHOOL_DAMAGE)
                self.assertEqual(hit["base_points"] + hit["die_sides"], normal)
                self.assertEqual(raw["EffectMiscValueB_1"], heroic)
                self.assertIn((SPELL[name], "spell_dungeon_refflat_damage"), self.scripts)
                self.assertTrue(raw["AttributesEx3"] & IGNORE_CASTER_MODIFIERS)
                self.assertTrue(raw["AttributesEx3"] & ALWAYS_HIT)
                pct = self._const(header).replace(".f", "").replace("f", "")
                self.assertEqual(pct, f"{normal // 100},{heroic // 100}")
        rebuke = self.spells[SPELL["SPELL_LB_SEARING_REBUKE"]]
        self.assertEqual(rebuke["cast_time_ms"], 2500)
        self.assertEqual(self._const("kRebukeCastMs"), "2500")
        self.assertEqual(rebuke["raw_overrides"]["InterruptFlags"], 15)
        self.assertEqual(rebuke["raw_overrides"]["SpellVisualID_1"], visuals.LB_REBUKE)
        self.assertAlmostEqual(self.spells[SPELL["SPELL_LB_IMMOLATION"]]["effect1"]["radius_yards"], 5.0)

    def test_open_the_index(self):
        normal = self.spells[SPELL["SPELL_LB_OPEN_THE_INDEX"]]
        heroic = self.spells[SPELL["SPELL_LB_OPEN_THE_INDEX_HEROIC"]]
        self.assertEqual((normal["cast_time_ms"], heroic["cast_time_ms"]), (2000, 3000))
        self.assertEqual(self._const("kOpenCastMs"), "2000,3000")
        # normal: a must-play bar nobody can kick; heroic: a kick (and a silence)
        self.assertEqual(normal["raw_overrides"]["InterruptFlags"], 0)
        self.assertEqual(normal["raw_overrides"]["PreventionType"], 0)
        self.assertEqual(heroic["raw_overrides"]["InterruptFlags"], 15)
        self.assertEqual(heroic["raw_overrides"]["PreventionType"], 1)
        # rule 5: neither shares the kickable Searing Rebuke's school
        rebuke = self.spells[SPELL["SPELL_LB_SEARING_REBUKE"]]
        self.assertNotEqual(normal["school"], rebuke["school"])
        self.assertNotEqual(heroic["school"], rebuke["school"])
        self.assertEqual((normal["school"], heroic["school"]), (SCHOOL_ARCANE, SCHOOL_ARCANE))

    def test_the_stacking_auras(self):
        page = self.spells[SPELL["SPELL_LB_TURNING_THE_PAGE"]]
        self.assertEqual(page["raw_overrides"]["CumulativeAura"], int(self._const("kMaxShownPage")))
        ward = self.spells[SPELL["SPELL_LB_READERS_WARD"]]
        self.assertEqual(ward["effect1"]["apply_aura"], AURA_DAMAGE_TAKEN)
        self.assertEqual(ward["effect1"]["base_points"] + ward["effect1"]["die_sides"], -25)
        self.assertEqual(self._const("kWardPctPerBook"), "25.f")
        self.assertEqual(self._const("kWardCapPct"), "50.f,75.f")
        self.assertEqual(ward["raw_overrides"]["CumulativeAura"], 3, "the heroic cap: 75 / 25")
        self.assertEqual(ward["raw_overrides"]["SpellVisualID_1"], visuals.LB_WARD)
        drowsy = self.spells[SPELL["SPELL_LB_DROWSY"]]
        self.assertEqual(drowsy["raw_overrides"]["CumulativeAura"], int(self._const("kDrowsyMaxStacks")))
        self.assertEqual({drowsy["effect1"]["apply_aura"], drowsy["effect2"]["apply_aura"]},
                         {AURA_MOD_DECREASE_SPEED, AURA_CASTING_SPEED})
        for effect in (drowsy["effect1"], drowsy["effect2"]):
            self.assertEqual(effect["base_points"] + effect["die_sides"], -int(self._const("kDrowsyPct")))
        self.assertEqual(drowsy["dispel"], 0)

    def test_sleep_and_dreaming(self):
        sleep = self.spells[SPELL["SPELL_LB_DREAM_SLEEP"]]
        self.assertEqual(sleep["effect1"]["apply_aura"], AURA_MOD_STUN)
        self.assertEqual(sleep["mechanic"], 10, "the sleep mechanic")
        self.assertEqual(sleep["duration_ms"], int(self._const("kDreamSleepMs")))
        self.assertEqual(sleep["raw_overrides"]["SpellVisualID_1"], visuals.LB_SLEEP)
        dreaming = self.spells[SPELL["SPELL_LB_DREAMING"]]
        self.assertEqual(dreaming["dispel"], 1, "Magic: the expected dispel")
        self.assertEqual(dreaming["duration_ms"], int(self._const("kDreamingMs")))
        self.assertEqual(dreaming["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertIn((SPELL["SPELL_LB_DREAMING"], "spell_sm_hollis_dreaming"), self.scripts)
        self.assertIn("RegisterSpellScript(spell_sm_hollis_dreaming);", self.script)
        self.assertIn("SPELL_AURA_DUMMY", self.script)

    def test_the_web_slow(self):
        slow = self.spells[SPELL["SPELL_LB_WEB_SLOW"]]
        self.assertEqual(slow["effect1"]["apply_aura"], AURA_MOD_DECREASE_SPEED)
        self.assertEqual(slow["effect1"]["base_points"] + slow["effect1"]["die_sides"], -50)
        self.assertEqual(self._const("kWebSlowPct"), "50")

    def test_the_looks_carry_the_visuals(self):
        for name, visual in (("SPELL_LB_WEB_SPRAY", visuals.LB_WEB_SPRAY), ("SPELL_LB_WEB_PATCH", visuals.LB_WEB),
                             ("SPELL_LB_HATCH", visuals.LB_WEB_HATCH), ("SPELL_LB_INFERNO", visuals.LB_METEOR),
                             ("SPELL_LB_THROW_AXE_LOOK", visuals.LB_AXES), ("SPELL_LB_WAR_STOMP", visuals.LB_STOMP),
                             ("SPELL_LB_GROUND_SLAM", visuals.LB_STOMP_RINGS),
                             ("SPELL_LB_DREAM_MIST_6", visuals.SV_DREAM_MIST[6]),
                             ("SPELL_LB_DREAM_MIST_9", visuals.SV_DREAM_MIST[9]),
                             ("SPELL_LB_DREAM_MIST_12", visuals.SV_DREAM_MIST[12]),
                             ("SPELL_LB_CHARGE_LOOK", visuals.LB_GRUNT_CHARGE),
                             ("SPELL_LB_BURNING_BOOK_LOOK", visuals.LB_BURNING_BOOK)):
            with self.subTest(name=name):
                self.assertEqual(self.spells[SPELL[name]]["raw_overrides"]["SpellVisualID_1"], visual)
        for story in range(SPELL["SPELL_LB_STORY_SPIDER"], SPELL["SPELL_LB_STORY_AFTERMATH"] + 1):
            self.assertEqual(self.spells[story]["raw_overrides"]["SpellVisualID_1"], visuals.LB_OPEN_BOOK)
        # the axe flies (a missile), never the doc's Axe Volley look
        self.assertEqual(visuals.LB_AXES, 3962)
        self.assertGreater(self.spells[SPELL["SPELL_LB_THROW_AXE_LOOK"]]["raw_overrides"]["Speed"], 0)

    # --- the creatures ------------------------------------------------------------------------------------------------

    def test_his_template(self):
        row = self.creatures[HOLLIS_GREY]
        self.assertEqual(row["name"], "Lector Hollis Grey")
        self.assertEqual(row["subname"], "Keeper of the Index")
        self.assertEqual(row["ScriptName"], "boss_lector_hollis_grey_rework")
        self.assertEqual(row["AIName"], "")
        self.assertEqual(row["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
        self.assertEqual(row["flags_extra"] & INSTANCE_BIND, INSTANCE_BIND, "FD-SM's credit creature")
        self.assertEqual((row["minlevel"], row["maxlevel"], row["unit_class"]), (35, 35, 8))
        self.assertLessEqual(abs(float(row["HealthModifier"]) * BASE_MAGE_35 - 36000), 2)
        self.assertEqual(self.models[HOLLIS_GREY]["CreatureDisplayID"], visuals.DISPLAY_HOLLIS_GREY)
        # FD-SM's encounter row 1077 credits this creature (its template is this one)
        self.assertIn("credit=credit_creature(300913)", re.sub(r"\s+", "", ENCOUNTERS.read_text()))
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_lector_hollis_grey_rework,", self.script)
        self.assertRegex(self.logic, r"constexpr bool kBound = true;")

    def test_the_story_units(self):
        for entry, health, script in ((CURSED_BOOK, 3500, "npc_sm_cursed_book"),
                                      (INFERNAL, 4000, "npc_sm_hollis_story_add"),
                                      (SPIDERLING, 500, "npc_sm_hollis_story_add")):
            with self.subTest(entry=entry):
                row = self.creatures[entry]
                self.assertEqual((row["minlevel"], row["maxlevel"], row["unit_class"]), (35, 35, 1),
                                 "his level: one reference row for every percent hit")
                self.assertLessEqual(abs(float(row["HealthModifier"]) * BASE_WARRIOR_35 - health), 1)
                self.assertEqual(row["ScriptName"], script)
                self.assertEqual(row["lootid"], 0)
                self.assertIn(f"RegisterDungeonReworkCreatureAI({script},", self.script)
        self.assertEqual(self._const("kBookHealth"), "3500,15000")
        self.assertEqual(self._const("kInfernalHealth"), "4000,20000")
        self.assertEqual(self._const("kSpiderlingHealth"), "500,2500")
        for entry in (SPECTRAL_TROLL, PHANTOM_GRUNT):
            row = self.creatures[entry]
            self.assertTrue(row["unit_flags"] & NOT_SELECTABLE, entry)
            self.assertEqual(row["ScriptName"], "npc_sm_hollis_phantom")
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_sm_hollis_phantom,", self.script)
        # V's displays; the book is never the Rabbit (21955)
        self.assertEqual(self.models[CURSED_BOOK]["CreatureDisplayID"], 28103)
        self.assertNotEqual(self.models[CURSED_BOOK]["CreatureDisplayID"], 21955)
        self.assertEqual(self.models[INFERNAL]["CreatureDisplayID"], visuals.DISPLAY_INFERNAL)
        self.assertEqual(self.models[SPIDERLING]["CreatureDisplayID"], visuals.DISPLAY_SPIDERLING)
        self.assertEqual(self.models[SPECTRAL_TROLL]["CreatureDisplayID"], visuals.DISPLAY_TROLL_AXE_THROWER)
        self.assertEqual(self.models[PHANTOM_GRUNT]["CreatureDisplayID"], visuals.DISPLAY_GHOST_ORC_GRUNT)
        # the ids are the header's
        for name, entry in (("NPC_SM_HOLLIS_GREY", 300913), ("NPC_SM_CURSED_BOOK", 300914),
                            ("NPC_SM_INFERNAL", 300915), ("NPC_SM_SPIDERLING", 300916),
                            ("NPC_SM_SPECTRAL_TROLL", 300917), ("NPC_SM_PHANTOM_GRUNT", 300918)):
            self.assertRegex(self.header, rf"{name}\s*=\s*{entry},")

    # --- the SQL ------------------------------------------------------------------------------------------------------

    def test_the_spawn(self):
        match = re.search(r"\((\d+), 300913, 189, 0, 0, (\d+), 1, 0, ([-\d.]+), ([-\d.]+), ([-\d.]+),", self.sql)
        self.assertIsNotNone(match)
        self.assertEqual(int(match.group(2)), 3, "normal and heroic (rule 14)")
        self.assertAlmostEqual(float(match.group(3)), POCKET[0])
        self.assertAlmostEqual(float(match.group(4)), POCKET[1])
        self.assertIn("kHollisGreyPocket{ 254.8f, -389.2f, 20.49f }", self.logic)
        self.assertAlmostEqual(float(match.group(5)), 20.49)

    def test_the_texts(self):
        rows = re.findall(r"\(300913, (\d), 0, '((?:[^']|'')*)', (\d+),", self.sql)
        self.assertEqual([int(g) for g, _t, _y in rows], list(range(8)))
        types = {int(g): int(y) for g, _t, y in rows}
        self.assertEqual((types[0], types[7]), (14, 14))
        for group in range(1, 7):
            self.assertEqual(types[group], 41, "boss emotes")
        self.assertIn("SAY_LB_AGGRO        = 0", self.logic)
        self.assertIn("EMOTE_LB_BOOK_FIRST = 1", self.logic)
        self.assertIn("SAY_LB_DEATH        = 7", self.logic)


if __name__ == "__main__":
    unittest.main()
