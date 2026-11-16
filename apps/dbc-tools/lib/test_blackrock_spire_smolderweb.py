"""
Blackrock Spire build WP-B4, Mother Smolderweb: source/npcs/blackrock_spire/smolderweb.py against its C++
(modules/mod-dungeon-bosses src/BlackrockSpire/SmolderwebLogic.h, boss_mother_smolderweb_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in her slice (210120-210149) and SmolderwebLogic.h names the same ids;
  - Smolderweb 10596 is bound (SmartAI off) at 165k on the level 59 warrior base, the sniffed DamageModifier, stun
    immune, INSTANCE_BIND;
  - the Broodling 300705 sits in the reservation, is bound, has 2,000 health, names its heroic entry (H's 3,000 override
    exists) and wears the stock spiderling's display;
  - the hits are resolve copies of the right school; the cast bars last the header's seconds and cannot be kicked; the
    stun lasts the header's seconds;
  - Venom and Widow's Bite: Nature periodic damage of the header's percent per stack, the header's duration and stack
    caps, Poison dispel, the kit's percent script, Venom's own dispel script; the bite falls off in time;
  - the looks are V-1's picks and the SP's wrong Poison 744 look is not used;
  - the SQL rev writes the three texts (boss emotes) and the egg gameobject at display 364, not selectable, and leaves
    her loot, her spawn, the cave's quest eggs and the smart_scripts rows (S0's) alone.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_spire_smolderweb.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockSpire"
HEADER = MODULE_DIR / "SmolderwebLogic.h"
REWORK = MODULE_DIR / "BlackrockSpireRework.h"
SCRIPT = MODULE_DIR / "boss_mother_smolderweb_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_mother_smolderweb_blackrock_spire.sql"
HEROIC = TOOL_ROOT / "source" / "world" / "dungeons" / "blackrock_spire.py"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_spire"

SLICE = range(210120, 210150)
(SPRAY_CAST, SPRAY, ENCASED, EGG_HATCH, MILK, MILK_LOOK, VENOM, VENOM_HEROIC, WIDOWS_BITE, BROOD_CALL,
 HATCH_LOOK) = range(210120, 210131)
SMOLDERWEB = 10596
BROODLING = 300705
BROODLING_HEROIC_ENTRY = 310289
EGG_GAMEOBJECT = 301251
EGG_DISPLAY = 364               # SpiderEggSack04 (ruling 36); never 23058, the quest eggs' own model

SCHOOL_NATURE, SCHOOL_FROST = 8, 16
SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT = 2, 6, 3
AURA_MOD_STUN, AURA_PERIODIC_DAMAGE = 12, 3
MECHANIC_STUN = 12
DISPEL_POISON = 4
AURA_INTERRUPT_CHANGE_MAP = 0x00080000
TARGET_FLAG_DEST_LOCATION = 0x40
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT = "spell_dungeon_refflat_periodic"
VENOM_SCRIPT = "spell_brs_smolderweb_venom"
WARRIOR_59_BASE = 2961      # creature_classlevelstats level 59 class 1 basehp0
WARRIOR_60_BASE = 3052      # level 60 class 1 basehp0
SV_VENOM_STING, SV_HATCH_BURST, SV_HATCH_EGGS, SV_MILK, SV_CRYSTALLIZE = 2617, 4339, 11329, 854, 4001
SV_POISON_WRONG = 19        # the SP's Poison 744: a 3 s impact, never wired


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


class SmolderwebDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) == SMOLDERWEB}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == BROODLING}
        cls.models = [e for e in reg.creature_template_models if int(e["CreatureID"]) == BROODLING]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(SPRAY_CAST, HATCH_LOOK + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_spire", {"spell": mine}), [])
        first = re.search(r"kSpellsSmolderweb\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(first)
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_SW_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))

    def test_smolderweb_is_bound(self):
        boss = self.edits[SMOLDERWEB]
        self.assertEqual(boss["ScriptName"], "boss_mother_smolderweb_rework")
        self.assertEqual(boss["AIName"], "")
        # 165k at 5 players (the build spec), within the S0 skeleton's 2 HP.
        self.assertLessEqual(abs(math.ceil(WARRIOR_59_BASE * boss["HealthModifier"]) - 165000), 2)
        self.assertAlmostEqual(float(boss["DamageModifier"]), 5.75)
        self.assertEqual(boss["CreatureImmunitiesId"], 1972)
        self.assertEqual(boss["flags_extra"], 1)
        for name in ("boss_mother_smolderweb_rework", "npc_brs_broodling"):
            self.assertIn(f"RegisterDungeonReworkCreatureAI({name},", self.cpp)
        self.assertIn("RegisterSpellScript(spell_brs_smolderweb_venom)", self.cpp)
        self.assertIn('BrsTest::RegisterBoss("smolderweb"', self.cpp)

    def test_the_broodling(self):
        self.assertEqual(id_blocks.out_of_reservation("blackrock_spire", {"creature": [BROODLING]}), [])
        broodling = self.creatures[BROODLING]
        self.assertEqual(broodling["ScriptName"], "npc_brs_broodling")
        self.assertEqual(broodling["AIName"], "")
        self.assertEqual(broodling["difficulty_entry_1"], BROODLING_HEROIC_ENTRY)
        # 2,000 health at 5 players, the header's; heroic 3,000 is H's override.
        self.assertEqual(math.ceil(WARRIOR_60_BASE * broodling["HealthModifier"]),
                         int(_header_value("kBroodlingHealth")))
        self.assertEqual(int(_header_value("kBroodlingHealth")), 2000)
        self.assertEqual(int(_header_value("kBroodlingHealthHeroic")), 3000)
        self.assertRegex(HEROIC.read_text(encoding="utf-8"), r"300705:\s*dict\(health=3_000\)")
        # A beast of her own faction (16), attackable, no loot, no XP, a weak bite.
        self.assertEqual(broodling["type"], 1)
        self.assertEqual(broodling["faction"], 16)
        self.assertEqual(broodling["unit_flags"], 0)
        self.assertEqual(broodling["lootid"], 0)
        self.assertEqual(broodling["ExperienceModifier"], 0.0)
        self.assertLessEqual(float(broodling["DamageModifier"]), 1.0)
        self.assertEqual([m["CreatureDisplayID"] for m in self.models], [9756])
        self.assertRegex(REWORK.read_text(encoding="utf-8"), rf"NPC_BRS_BROODLING\s*=\s*{BROODLING},")

    def test_hits_are_resolve_copies_of_the_right_school(self):
        for spell_id, school in ((SPRAY, SCHOOL_FROST), (EGG_HATCH, SCHOOL_NATURE), (MILK, SCHOOL_NATURE)):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertEqual(spell["school"], school, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
        # The egg's burst rides its hit (Spawn Bile Slime's SV 4339).
        self.assertEqual(_raw(self.spells[EGG_HATCH], "SpellVisualID_1"), SV_HATCH_BURST)

    def test_the_cast_bars(self):
        for spell_id, ms, name in ((SPRAY_CAST, "kSprayCastMs", "Crystal Spray"),
                                   (BROOD_CALL, "kBroodCallCastMs", "Brood Call")):
            bar = self.spells[spell_id]
            self.assertEqual(bar["name"], name)
            self.assertEqual(bar["effect1"]["type"], DUMMY_EFFECT)
            # Not interruptible: a kick must not look as if it stopped what the registry still lands.
            self.assertEqual(_raw(bar, "InterruptFlags"), 0)
            self.assertEqual(_raw(bar, "PreventionType"), 0)
            self.assertEqual(bar["cast_time_ms"], int(_header_value(ms)))
        self.assertEqual(self.spells[SPRAY_CAST]["cast_time_ms"], 2000)
        self.assertEqual(self.spells[BROOD_CALL]["cast_time_ms"], 3000)
        self.assertEqual(_raw(self.spells[SPRAY_CAST], "SpellVisualID_1"), SV_CRYSTALLIZE)
        self.assertEqual(_raw(self.spells[BROOD_CALL], "SpellVisualID_1"), SV_HATCH_EGGS)
        self.assertEqual(self.spells[SPRAY_CAST]["school"], SCHOOL_FROST)

    def test_the_stun(self):
        stun = self.spells[ENCASED]
        self.assertEqual(stun["effect1"]["apply_aura"], AURA_MOD_STUN)
        self.assertEqual(stun["mechanic"], MECHANIC_STUN)
        self.assertEqual(stun["duration_ms"], int(_header_value("kEncasedMs")))
        self.assertEqual(stun["duration_ms"], 2000)
        self.assertEqual(_raw(stun, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)
        self.assertEqual(_raw(stun, "SpellVisualID_1"), SV_CRYSTALLIZE)

    def test_the_milk_and_hatch_looks(self):
        look = self.spells[MILK_LOOK]
        self.assertEqual(look["effect1"]["type"], DUMMY_EFFECT)
        self.assertAlmostEqual(float(_raw(look, "Speed")), _header_value("kMilkMissileSpeed"))
        self.assertEqual(_raw(look, "SpellVisualID_1"), SV_MILK)
        self.assertTrue(_raw(look, "Targets") & TARGET_FLAG_DEST_LOCATION)
        hatch = self.spells[HATCH_LOOK]
        self.assertEqual(hatch["effect1"]["type"], DUMMY_EFFECT)
        self.assertEqual(_raw(hatch, "SpellVisualID_1"), SV_HATCH_BURST)
        self.assertTrue(_raw(hatch, "Targets") & TARGET_FLAG_DEST_LOCATION)

    def test_venom(self):
        normal, heroic = _nh_values("kVenomMaxStacks")
        for spell_id, stacks in ((VENOM, normal), (VENOM_HEROIC, heroic)):
            venom = self.spells[spell_id]
            self.assertEqual(venom["name"], "Venom")
            self.assertEqual(venom["school"], SCHOOL_NATURE)
            self.assertEqual(venom["dispel"], DISPEL_POISON)
            self.assertEqual(venom["effect1"]["apply_aura"], AURA_PERIODIC_DAMAGE)
            # 1% of the reference row a second a stack (hundredths, heroic the same: EffectMiscValueB).
            self.assertEqual(int(venom["effect1"]["base_points"]), int(_header_value("kVenomPctPerStack") * 100))
            self.assertEqual(_raw(venom, "EffectMiscValueB_1"), 100)
            self.assertEqual(venom["effect1"]["amplitude"], 1000)
            self.assertEqual(venom["duration_ms"], int(_header_value("kVenomMs")))
            self.assertEqual(venom["duration_ms"], 30000)
            self.assertEqual(_raw(venom, "CumulativeAura"), int(stacks))
            self.assertEqual(_raw(venom, "SpellVisualID_1"), SV_VENOM_STING)
            self.assertEqual(_raw(venom, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)
            self.assertIn((spell_id, REFFLAT), self.scripts)
            self.assertIn((spell_id, VENOM_SCRIPT), self.scripts)
        self.assertEqual((normal, heroic), (5, 8))
        # The registry's rider is the one of the map's difficulty.
        self.assertIn("Rider(VenomSpell(_heroic))", self.cpp)
        self.assertRegex(_header(), r"VenomSpell\(bool heroic\)\s*\{\s*return heroic \? SPELL_SW_VENOM_HEROIC")

    def test_widows_bite_and_the_taunt_swap(self):
        bite = self.spells[WIDOWS_BITE]
        self.assertEqual(bite["name"], "Widow's Bite")
        self.assertEqual(bite["school"], SCHOOL_NATURE)
        self.assertEqual(bite["dispel"], DISPEL_POISON)
        self.assertEqual(bite["effect1"]["apply_aura"], AURA_PERIODIC_DAMAGE)
        self.assertEqual(int(bite["effect1"]["base_points"]), int(_header_value("kBitePctPerStack") * 100))
        self.assertEqual(bite["duration_ms"], int(_header_value("kBiteMs")))
        self.assertEqual(bite["duration_ms"], 15000)
        # No cap (the aura counter's limit), the SP: "a tank who keeps her past 5 or 6 stacks dies".
        self.assertEqual(_raw(bite, "CumulativeAura"), int(_header_value("kBiteStackCap")))
        self.assertEqual(_raw(bite, "CumulativeAura"), 255)
        self.assertEqual(_raw(bite, "SpellVisualID_1"), SV_VENOM_STING)
        self.assertNotEqual(_raw(bite, "SpellVisualID_1"), SV_POISON_WRONG)
        self.assertIn((WIDOWS_BITE, REFFLAT), self.scripts)
        # The user ruling of 2026-11-15: the old tank is clear (0 stacks) before the new one reaches the count, so the
        # debuff is shorter than the swap count of bites.
        every = int(_header_value("kBiteEveryMs"))
        swap = int(_header_value("kBiteSwapAtStacks"))
        self.assertLess(bite["duration_ms"], swap * every)
        self.assertEqual(swap, 3)
        # The entry is registered only at 10 players, with the boss as the caster.
        self.assertRegex(self.cpp, r"if \(_tankSwap\)\s*\{\s*d\.dispels\.emplace_back\(SPELL_SW_WIDOWS_BITE")
        self.assertIn("d.tauntSwaps.emplace_back(NPC_SMOLDERWEB, SPELL_SW_WIDOWS_BITE, kBiteSwapAtStacks)", self.cpp)
        self.assertIn("DungeonKit::Flex::TankSwapOn(_players)", self.cpp)
        self.assertIn("DungeonKit::AddStacks(victim, SPELL_SW_WIDOWS_BITE, 1, me)", self.cpp)

    def test_scripts_are_the_kits_and_venoms(self):
        self.assertEqual({name for _, name in self.scripts}, {RESOLVE, REFFLAT, VENOM_SCRIPT})

    def test_the_cpp_uses_the_declared_names(self):
        for name in ("SPELL_SW_SPRAY_CAST", "SPELL_SW_SPRAY", "SPELL_SW_ENCASED", "SPELL_SW_EGG_HATCH", "SPELL_SW_MILK",
                     "SPELL_SW_MILK_LOOK", "SPELL_SW_VENOM", "SPELL_SW_VENOM_HEROIC", "SPELL_SW_WIDOWS_BITE",
                     "SPELL_SW_BROOD_CALL", "SPELL_SW_HATCH_LOOK"):
            self.assertIn(name, self.cpp + _header(), name)
        # The registry carries the header's percents, never a literal.
        self.assertIn("kEggPct(_heroic)", self.cpp)
        self.assertIn("kMilkPct(_heroic)", self.cpp)
        self.assertIn("kSprayPct(_heroic)", self.cpp)
        self.assertNotIn("\t", self.cpp)
        # The tank-exempt cone, the stock quest aura and the death spiderlings.
        self.assertIn("BossMechanics::TankExempt::Yes", self.cpp)
        self.assertIn("SPELL_SW_QUEST_MILK", self.cpp)
        self.assertIn("SPELL_SW_DEATH_SPIDERLINGS", self.cpp)
        # The egg is the gameobject, never a creature (neither model has a creature display).
        self.assertIn("GO_BRS_SMOLDERWEB_EGG", self.cpp)
        self.assertRegex(REWORK.read_text(encoding="utf-8"), rf"GO_BRS_SMOLDERWEB_EGG\s*=\s*{EGG_GAMEOBJECT},")

    def test_the_wrong_poison_look_is_not_used(self):
        source = (PACKAGE / "smolderweb.py").read_text(encoding="utf-8")
        self.assertNotIn("SW_VENOM_WRONG", source)
        self.assertNotRegex(source, r"SpellVisualID_1=19\b")
        for spell in self.spells.values():
            self.assertNotEqual(_raw(spell, "SpellVisualID_1"), SV_POISON_WRONG, spell["id"])


class SmolderwebSqlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.header = _header()

    def test_the_texts(self):
        for group in (0, 1, 2):
            self.assertRegex(self.sql, rf"\(10596, {group}, 0, '%s [^\n]*', 41, 0, 100, ", group)      # boss emotes
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 10596 AND `GroupID` BETWEEN 0 AND 2;", self.sql)
        # The header's group names are those three, the text range the SP's.
        groups = dict(re.findall(r"TEXT_(\w+)\s*=\s*(\d+),", self.header))
        self.assertEqual(sorted(int(v) for v in groups.values()), [0, 1, 2])
        self.assertIn("lays her eggs", self.sql)
        self.assertIn("calls to her brood", self.sql)
        self.assertIn("spits her last milk across the cave", self.sql)

    def test_the_egg(self):
        self.assertRegex(self.sql, rf"\({EGG_GAMEOBJECT}, 5, {EGG_DISPLAY}, 'Smolderweb Egg'")
        self.assertNotRegex(self.sql, r"\(301251, 5, 23058,")       # the quest eggs' own model
        self.assertIn(f"({EGG_GAMEOBJECT}, 0, 16, 0, 0, 0, 0, 0, 0)", self.sql)      # not selectable
        self.assertIn("ON DUPLICATE KEY UPDATE", self.sql)
        # No spawn: the script places every egg.
        self.assertNotIn("INSERT INTO `gameobject` ", self.sql)

    def test_the_rev_leaves_the_stock_rows_alone(self):
        # S0's rev dropped her SmartAI rows; this one never touches them, her loot, her spawn or the quest eggs.
        code = "\n".join(line for line in self.sql.splitlines() if not line.startswith("--"))
        self.assertNotIn("smart_scripts", code)
        self.assertNotIn("creature_loot_template", code)
        self.assertNotIn("UPDATE `creature`", code)
        self.assertNotIn("175606", code)
        self.assertNotIn("DELETE FROM `gameobject_template`", code)


if __name__ == "__main__":
    unittest.main()
