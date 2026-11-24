"""
Scarlet Monastery build WP-D12, Brother Aldous Thorne: source/npcs/scarlet_monastery/thorne.py (his template, the
Seedling, the Briar, the Blessed Bramble and the spells 213060-213077), data/sql/updates/pending_db_world/
rev_thorne_scarlet_monastery.sql (his texts, his scythe, his spawn, the moved Centurion), and the C++ they must agree
with (modules/mod-dungeon-bosses src/ScarletMonastery/ThorneLogic.h and boss_gardener_rework.cpp).

Checks:
  - the eighteen spells sit in the D12 slice and the C++ names the same ids; the registry's hits are resolve copies in
    their schools with the caster-modifier attribute; the sweep's tank hit carries 15 / 25 in hundredths and binds the
    kit's percent script; Bless the Harvest is an interruptible 2.5 s Nature cast and the Holy Water bar is not (and
    not Nature); the grain is a 5 s undispellable debuff; the slow is 50%; the pollen and the heal are custom values;
    the looks use the V constants and never the WRONG ones;
  - the four creatures: Thorne level 40 paladin, 60k, immunity 1972, INSTANCE_BIND, display 2502, his heroic entry
    unset or the planned one, his ScriptName only once wave 2 binds; the seedling and the briar unselectable helpers
    with no heroic entry; the bramble attackable, no melee, no immunity set, display 12347;
  - the SQL: seven texts, Soul Harvester, his spawn on both difficulties at the header's spot, the Centurion moved;
  - the wave gate: both AIs register behind kWave2Bound; `.dbtest sm thorne` always.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scarlet_monastery_thorne.py
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
from lib import test_scarlet_monastery_kit as kit_test  # noqa: E402
from source.npcs.scarlet_monastery import _common as common  # noqa: E402
from source.npcs.scarlet_monastery import _visuals as visuals  # noqa: E402

MDB = REPO_ROOT / "modules" / "mod-dungeon-bosses"
LOGIC = MDB / "src" / "ScarletMonastery" / "ThorneLogic.h"
SCRIPT = MDB / "src" / "ScarletMonastery" / "boss_gardener_rework.cpp"
HEADER = MDB / "src" / "ScarletMonastery" / "ScarletMonasteryRework.h"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_thorne_scarlet_monastery.sql"
DT_FILE = TOOL_ROOT / "source" / "npcs" / "scarlet_monastery" / "thorne.py"

SLICE = range(213060, 213100)
FIRST = 213060
NAMES = ("SPELL_GD_BLESSED_GRAIN", "SPELL_GD_PLANT_LOOK", "SPELL_GD_PRUNE", "SPELL_GD_PRUNE_TANK",
         "SPELL_GD_PRUNE_LOOK", "SPELL_GD_BLOOM", "SPELL_GD_BLOOM_LOOK", "SPELL_GD_BRIAR", "SPELL_GD_BRIAR_SLOW",
         "SPELL_GD_BRIAR_LOOK", "SPELL_GD_BRAMBLE_BRIAR", "SPELL_GD_POLLEN", "SPELL_GD_POLLEN_LOOK",
         "SPELL_GD_HOLY_WATER_CAST", "SPELL_GD_HOLY_WATER", "SPELL_GD_BLESSED_GROUND_LOOK",
         "SPELL_GD_BLESSED_GROUND_HEAL", "SPELL_GD_BLESS_THE_HARVEST")
EFFECT_SCHOOL_DAMAGE, EFFECT_DUMMY, EFFECT_APPLY_AURA, EFFECT_HEAL = 2, 3, 6, 10
AURA_DUMMY, AURA_MOD_DECREASE_SPEED = 4, 33
SCHOOL_PHYSICAL, SCHOOL_HOLY, SCHOOL_NATURE = 1, 2, 8
TARGET_DEST_DEST = 87
THORNE, SEEDLING, BRIAR, BRAMBLE = 300946, 300947, 300948, 300949
HELPER_FLAGS = 0x2 | 0x100 | 0x200 | 0x02000000


class ThorneTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = kit_test._load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates}
        cls.models = {int(e["CreatureID"]): e for e in reg.creature_template_models}
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.logic = LOGIC.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.dt = DT_FILE.read_text(encoding="utf-8")

    def _const(self, name: str) -> str:
        match = re.search(rf"{name}\s*(?:=|\{{)\s*([^;}}]+?)\s*(?:;|\}};)", self.logic)
        self.assertIsNotNone(match, name)
        return match.group(1).replace(" ", "")

    # --- the spells ---------------------------------------------------------------------------------------------------

    def test_the_spells_sit_in_the_d12_slice(self):
        self.assertEqual(sorted(self.spells), list(range(FIRST, FIRST + len(NAMES))))
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery", {"spell": list(self.spells)}), [])
        self.assertIn("kSpellsThorne{ 213060, 213099 }", re.sub(r"\s+", " ", self.header))

    def test_the_cpp_names_the_same_ids(self):
        for offset, name in enumerate(NAMES):
            self.assertRegex(self.logic, rf"{name}\s*=\s*kSpellSlice\.first \+ {offset},", name)
        self.assertRegex(self.logic, r"static_assert\(SPELL_GD_BLESS_THE_HARVEST <= kSpellSlice\.last")

    def test_the_registry_hits_are_resolve_copies_in_their_schools(self):
        for offset, school in ((2, SCHOOL_PHYSICAL), (5, SCHOOL_HOLY), (7, SCHOOL_NATURE), (10, SCHOOL_NATURE),
                               (14, SCHOOL_HOLY)):
            spell_id = FIRST + offset
            spell = self.spells[spell_id]
            self.assertEqual(spell["school"], school, spell_id)
            self.assertEqual(spell["effect1"]["type"], EFFECT_SCHOOL_DAMAGE, spell_id)
            self.assertIn((spell_id, "spell_boss_mechanics_resolve"), self.scripts, spell_id)
            self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & 0x20000000, spell_id)    # rule 2

    def test_the_prune_tank_hit_binds_the_kit_script(self):
        spell = self.spells[FIRST + 3]
        effect = spell["effect1"]
        self.assertEqual(effect["type"], EFFECT_SCHOOL_DAMAGE)
        self.assertEqual(effect["base_points"] + effect["die_sides"], 1500)
        self.assertEqual(spell["raw_overrides"]["EffectMiscValueB_1"], 2500)
        self.assertIn((FIRST + 3, "spell_dungeon_refflat_damage"), self.scripts)
        self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & 0x20000000)
        self.assertEqual(self._const("kPruneTankPct"), "15.f,25.f")

    def test_the_header_numbers_are_the_build_spec(self):
        for name, value in (("kPrunePct", "30.f,45.f"), ("kBloomPct", "20.f,30.f"), ("kHolyWaterPct", "30.f,45.f"),
                            ("kHolyWaterRadiusYd", "10.f,12.f"), ("kBloomAfterMs", "15000,10000"),
                            ("kCarriers", "2,3"), ("kBriarPct", "10.f"), ("kBrambleBriarPct", "15.f"),
                            ("kBriarRadiusYd", "4.f"), ("kBrambleBriarRadiusYd", "5.f"), ("kBriarCap", "6"),
                            ("kPruneAngleDeg", "120.f"), ("kPruneLengthYd", "8.f"), ("kFurrowAheadYd", "5.f"),
                            ("kFurrowRadiusYd", "3.f"), ("kBlessedGroundRadiusYd", "8.f"),
                            ("kBlessedGroundMs", "8000"), ("kPollenCapPct", "20.f"), ("kPollenEveryMs", "2000"),
                            ("kSowDebuffMs", "5000"), ("kThorneHealthNormal", "60000"),
                            ("kThorneHealthHeroic", "300000"), ("kBrambleHealthHeroic", "8000")):
            self.assertEqual(self._const(name), value, name)

    def test_bless_is_interruptible_and_the_holy_water_bar_is_not(self):
        bless = self.spells[FIRST + 17]
        self.assertEqual(bless["school"], SCHOOL_NATURE)
        self.assertEqual(bless["cast_time_ms"], 2500)
        self.assertEqual(int(self._const("kBlessCastMs")), 2500)
        self.assertEqual((bless["raw_overrides"]["InterruptFlags"], bless["raw_overrides"]["PreventionType"]),
                         (15, 1))
        bar = self.spells[FIRST + 13]
        self.assertEqual(bar["cast_time_ms"], 2500)
        self.assertEqual(int(self._const("kHolyWaterCastMs")), 2500)
        self.assertEqual((bar["raw_overrides"]["InterruptFlags"], bar["raw_overrides"]["PreventionType"]), (0, 0))
        self.assertNotEqual(bar["school"], bless["school"])        # rule 5
        self.assertRegex(self.script, r"d\.interrupts\.emplace_back\(NPC_SM_THORNE, SPELL_GD_BLESS_THE_HARVEST, 3,")

    def test_the_grain_the_slow_the_pollen_and_the_heal(self):
        grain = self.spells[FIRST]
        self.assertEqual(grain["duration_ms"], 5000)
        self.assertEqual(grain["dispel"], 0)
        self.assertEqual((grain["effect1"]["type"], grain["effect1"]["apply_aura"]), (EFFECT_APPLY_AURA, AURA_DUMMY))
        self.assertEqual(grain["raw_overrides"]["SpellVisualID_1"], visuals.GD_SEED)
        slow = self.spells[FIRST + 8]
        self.assertEqual(slow["effect1"]["apply_aura"], AURA_MOD_DECREASE_SPEED)
        self.assertEqual(slow["effect1"]["base_points"] + 1, -50)
        self.assertEqual(self._const("kBriarSlowPct"), "50")
        pollen = self.spells[FIRST + 11]
        self.assertEqual((pollen["school"], pollen["effect1"]["type"]), (SCHOOL_HOLY, EFFECT_SCHOOL_DAMAGE))
        self.assertEqual(pollen["effect1"]["base_points"], 0)
        self.assertTrue(pollen["raw_overrides"]["AttributesEx3"] & 0x20000000)
        heal = self.spells[FIRST + 16]
        self.assertEqual(heal["effect1"]["type"], EFFECT_HEAL)
        self.assertTrue(heal["raw_overrides"]["AttributesEx3"] & 0x20000000)

    def test_the_looks_use_the_v_constants(self):
        self.assertEqual(self.spells[FIRST + 6]["effect1"]["implicit_target_a"], TARGET_DEST_DEST)
        for offset, visual in ((0, visuals.GD_SEED), (1, visuals.GD_SEED), (3, visuals.GD_SWEEP),
                               (4, visuals.GD_SWEEP), (6, visuals.GD_BLOOM), (9, visuals.GD_BRIAR),
                               (12, visuals.GD_POLLEN_ALT), (13, visuals.GD_HOLY_WATER),
                               (15, visuals.GD_BLESSED_GROUND), (17, visuals.GD_BLESS_CAST)):
            self.assertEqual(self.spells[FIRST + offset]["raw_overrides"]["SpellVisualID_1"], visual, offset)
        # VR: the blessed ground is the Strat 8 yd holy zone, never Consecration's 5600 (the Last Stand's look); the
        # pollen glow is the gold holy zone stand-in, not the violet Pollen 8529.
        self.assertEqual(visuals.GD_BLESSED_GROUND, 90512)
        used = {s["raw_overrides"].get("SpellVisualID_1") for s in self.spells.values()}
        self.assertNotIn(5600, used)
        self.assertNotIn(visuals.GD_POLLEN, used)

    # --- the creatures ------------------------------------------------------------------------------------------------

    def test_his_columns(self):
        c = self.creatures[THORNE]
        self.assertEqual((c["name"], c["subname"]), ("Brother Aldous Thorne", "Keeper of the Blessed Grain"))
        self.assertEqual(c["ScriptName"], "boss_gardener_rework" if common.BIND_WAVE_2 else "")
        self.assertEqual(c["AIName"], "")
        self.assertEqual((c["minlevel"], c["maxlevel"], c["unit_class"], c["faction"], c["rank"]), (40, 40, 2, 67, 1))
        self.assertEqual(c["CreatureImmunitiesId"], 1972)
        self.assertEqual(c["flags_extra"], 1)               # INSTANCE_BIND: FD-SM's credit_creature(300946)
        self.assertEqual(c["lootid"], THORNE)
        # WP-H's mint table: 310479 once every lower kit unit is declared (THORNE_HEROIC; until then unset)
        self.assertIn(c.get("difficulty_entry_1") or 0, (0, 310479))
        self.assertIn("THORNE_HEROIC_PLANNED = 310479", self.dt)
        self.assertAlmostEqual(c["HealthModifier"] * 1226, 60000, delta=5)
        self.assertEqual(self.models[THORNE]["CreatureDisplayID"], visuals.DISPLAY_THORNE)
        self.assertEqual(visuals.DISPLAY_THORNE, 2502)

    def test_the_helpers_never_fight(self):
        for entry, display in ((SEEDLING, visuals.DISPLAY_SEEDLING), (BRIAR, 11686)):
            c = self.creatures[entry]
            self.assertEqual(c["ScriptName"], "", entry)
            self.assertEqual(c["unit_flags"], HELPER_FLAGS, entry)
            self.assertEqual(c["DamageModifier"], 0.0, entry)
            self.assertEqual(c["flags_extra"], 0x40, entry)
            self.assertNotIn("difficulty_entry_1", {k for k, v in c.items() if v}, entry)
            self.assertEqual(self.models[entry]["CreatureDisplayID"], display, entry)
        self.assertEqual(self.models[SEEDLING]["DisplayScale"], visuals.SEEDLING_SCALE_RANGE[0])

    def test_the_bramble_is_a_kill_target(self):
        c = self.creatures[BRAMBLE]
        self.assertEqual(c["name"], "Blessed Bramble")
        self.assertEqual(c["ScriptName"], "npc_sm_blessed_bramble" if common.BIND_WAVE_2 else "")
        self.assertEqual(c["unit_flags"], 0)                # attackable and selectable
        self.assertEqual(c["DamageModifier"], 0.0)          # no melee
        self.assertEqual(c["CreatureImmunitiesId"], 0)      # stuns and crowd control land (s7 #10)
        self.assertEqual(c["faction"], 67)
        self.assertIn(c.get("difficulty_entry_1") or 0, (0, 310480))
        self.assertIn("BRAMBLE_HEROIC_PLANNED = 310480", self.dt)
        self.assertEqual(self.models[BRAMBLE]["CreatureDisplayID"], visuals.DISPLAY_BLESSED_BRAMBLE)
        self.assertEqual(self.models[BRAMBLE]["DisplayScale"], visuals.BRAMBLE_SCALE)
        self.assertRegex(self.script, r"TargetEntry\(NPC_SM_BLESSED_BRAMBLE, 1, Who::Dps\)")
        self.assertRegex(self.script, r"TargetEntry\(NPC_SM_BLESSED_BRAMBLE, -1, Who::Tank\)")

    def test_ids_sit_in_the_reservation_and_match_the_header(self):
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery",
                                                      {"creature": [THORNE, SEEDLING, BRIAR, BRAMBLE]}), [])
        for name, value in (("NPC_SM_THORNE", THORNE), ("NPC_SM_SEEDLING", SEEDLING), ("NPC_SM_BRIAR", BRIAR),
                            ("NPC_SM_BLESSED_BRAMBLE", BRAMBLE)):
            self.assertRegex(self.header, rf"{name}\s*=\s*{value},")

    def test_the_wave_gate(self):
        self.assertRegex(self.script, r"if \(kWave2Bound\)\s*RegisterDungeonReworkCreatureAI\(boss_gardener_rework,")
        self.assertRegex(self.script, r"if \(kWave2Bound\)\s*RegisterDungeonReworkCreatureAI\(npc_sm_blessed_bramble,")
        self.assertRegex(self.script, r'\n    SmTest::RegisterBoss\("thorne",')
        for entry in (THORNE, SEEDLING, BRIAR, BRAMBLE):
            self.assertIn(f"creature_template({entry}, ", self.dt)     # H finds the kit units by this literal pattern

    # --- the SQL ------------------------------------------------------------------------------------------------------

    def test_the_seven_texts(self):
        rows = re.findall(r"^\(300946, (\d+), (\d+), '((?:[^']|'')*)', (\d+), 0, 100, 0, 0, 0, 0, (\d+),", self.sql,
                          re.M)
        self.assertEqual([(int(g), int(t), int(r)) for g, _, _, t, r in rows],
                         [(0, 14, 0), (1, 12, 0), (2, 14, 0), (3, 41, 3), (4, 41, 3), (5, 14, 0), (6, 14, 0)])
        self.assertEqual([t.replace("''", "'") for _, _, t, _, _ in rows],
                         ["Weeds in the Light's garden. I know what to do with weeds.", "The furrow is ready. Sow!",
                          "The Light blesses this harvest!", "%s raises the aspergillum!",
                          "The untended seed blooms into thorns!", "Pulled up by the root.",
                          "Nothing grows... from tainted soil..."])
        for name, group in (("SAY_PULL", 0), ("SAY_SOW", 1), ("SAY_BLESS", 2), ("EMOTE_HOLY_WATER", 3),
                            ("EMOTE_BLOOM", 4), ("SAY_KILL", 5), ("SAY_DEATH", 6)):
            self.assertRegex(self.logic, rf"{name}\s*=\s*{group},", name)
        self.assertRegex(re.sub(r"\s+", " ", self.header), r"\{ NPC_SM_THORNE, 0, 6, 0 \}")

    def test_his_scythe(self):
        self.assertIn("(300946, 1, 20536, 0, 0, 0);", self.sql)
        self.assertEqual(visuals.ITEM_THORNE_SCYTHE, 20536)

    def test_his_spawn_is_the_header_spot_on_both_difficulties(self):
        row = re.search(r"^\(3009460, 300946, 189, 0, 0, (\d+), 1, (\d+), ([-\d.]+), ([-\d.]+), ([-\d.]+), ([\d.]+), "
                        r"(\d+), 0,", self.sql, re.M)
        self.assertIsNotNone(row)
        self.assertEqual(int(row.group(1)), 3)
        self.assertEqual(int(row.group(2)), 1)              # equipment_id: the scythe
        spot = re.search(r"kThorneSpot\{ ([-\d.]+)f, ([-\d.]+)f, ([-\d.]+)f \}", self.header)
        self.assertEqual(tuple(float(row.group(i)) for i in (3, 4, 5)), tuple(float(spot.group(i)) for i in (1, 2, 3)))
        self.assertEqual(float(row.group(6)), float(self._const("kThorneSpawnFacing").rstrip("f")))
        self.assertEqual(int(row.group(7)), 86400)
        self.assertIn("DELETE FROM `creature` WHERE `id` = 300946 AND `guid` = 3009460;", self.sql)

    def test_the_centurion_moves_off_his_spot(self):
        row = re.search(r"UPDATE `creature` SET `position_x` = ([\d.]+), `position_y` = ([\d.]+), `position_z` = "
                        r"([\d.]+)\s+WHERE `guid` = 39953 AND `id` = 4301;", self.sql)
        self.assertIsNotNone(row)
        spot = re.search(r"kMovedCenturionSpot\{ ([-\d.]+)f, ([-\d.]+)f, ([-\d.]+)f \}", self.logic)
        self.assertEqual(tuple(float(row.group(i)) for i in (1, 2, 3)), tuple(float(spot.group(i)) for i in (1, 2, 3)))
        self.assertGreater(((float(row.group(1)) - 908.2) ** 2 + (float(row.group(2)) - 1399.2) ** 2) ** 0.5, 30.0)


if __name__ == "__main__":
    unittest.main()
