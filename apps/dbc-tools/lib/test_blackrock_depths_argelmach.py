"""
Blackrock Depths build WP-D15, Golem Lord Argelmach: source/npcs/blackrock_depths/argelmach.py against its C++
(modules/mod-dungeon-bosses src/BlackrockDepths/ArgelmachLogic.h, boss_golem_lord_argelmach_rework.cpp), its SQL rev
and G2's Livewire drill row (mod-boss-mechanics src/MechanicDrill.h, when that source is on hand).

Checks (the declarations directly: none of them waits for BIND_WAVE_2; only 8983's binding does, read from the source):
  - the spells sit in Argelmach's slice (211330-211369) and ArgelmachLogic.h names the same ids;
  - 8983's binding (behind BIND_WAVE_2): his script, 150k at 5 players, DamageModifier 3.5;
  - the golems 300833-300835: 25,000 health at level 55, elite mechanical of his faction, stun immunity, no loot or XP,
    their heroic entries, their displays, bound to the golem AI; the Arcane Orb 300837: a helper with its display;
  - his copies (Chain Lightning, Shock, Lightning Shield) carry the header's percents and the right scripts; Chain
    Lightning is kickable; the registry hits are resolve copies the C++ names; Poison Mist rides the refflat scripts,
    is a Poison; Livewire is Magic and bound to its dispel script; the buffs stack as the header says;
  - no look is one VISUALS calls WRONG; the SQL rev: texts 0-3 and 5-7, the SmartAI drop, the pedestals, the hall;
  - the header's Livewire tags match G2's drill.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_argelmach.py
"""

from __future__ import annotations

import math
import os
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
HEADER = MODULE_DIR / "ArgelmachLogic.h"
REWORK = MODULE_DIR / "BlackrockDepthsRework.h"
SCRIPT = MODULE_DIR / "boss_golem_lord_argelmach_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_argelmach_blackrock_depths.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_depths"
SOURCE = PACKAGE / "argelmach.py"
BM_DRILL = Path(os.environ.get("BOSS_MECHANICS_SRC", str(REPO_ROOT.parent / "boss-mechanics-brd" / "src"))) \
    / "MechanicDrill.h"

SLICE = range(211330, 211370)
(CHAIN, SHOCK, SHIELD, WAKES, BOMB, CLOUD, CLOUD_LOOK, MIST, TETHER, JOLT, LIVEWIRE, PULSE, BURST, SURGE, OVERCHARGED,
 EMPOWERED, OVERCHARGE_BOMB, CATCH, BLAST, STATUE) = range(211330, 211350)
ARGELMACH = 8983
GOLEMS = {300833: ("Toxitron", 8177, 310410), 300834: ("Electron", 8178, 310411), 300835: ("Arcanoton", 8289, 310412)}
ORB = 300837
PALADIN_55_BASE = 2091
WARRIOR_55_BASE = 2614

SCHOOL_DAMAGE, DUMMY_EFFECT, APPLY_AURA = 2, 3, 6
AURA_PERIODIC_DAMAGE, AURA_DUMMY, AURA_PROC_TRIGGER_DAMAGE, AURA_MOD_DAMAGE_PERCENT_DONE = 3, 4, 43, 79
SCHOOL_NATURE, SCHOOL_ARCANE = 8, 64          # School enum (a mask)
DISPEL_MAGIC, DISPEL_POISON = 1, 4
RESOLVE = "spell_boss_mechanics_resolve"
HIT_SCRIPT = "spell_brd_argelmach_hit"
LIVEWIRE_SCRIPT = "spell_brd_argelmach_livewire"
REFFLAT = "spell_dungeon_refflat_damage"
REFFLAT_PERIODIC = "spell_dungeon_refflat_periodic"
IMMUNITY_BOSS_STUN = 1972
FACTION_DARK_IRON = 54
IGNORE_CASTER_MODIFIERS = 0x20000000
NOT_SELECTABLE = 0x02000000
ATTR0_NO_IMMUNITIES = 0x20000000
SV_STOCK_STONED = 1845                  # Stoned 10255's SpellVisualID_1 (client Spell.dbc)
STOCK_STONED = 10255
# VISUALS-REPORT's WRONG looks this fight must never wire (lib/test_blackrock_depths_vfx.py holds the full list).
WRONG = {13174: "Activate Construct (a fire strike)", 11840: "Living Bomb (a fire whirl)",
         10407: "Chemical Flames (fel green)"}


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


def _raw(spell: dict, column: str) -> float:
    return (spell.get("raw_overrides") or {}).get(column, 0) or 0


def _header() -> str:
    return HEADER.read_text(encoding="utf-8")


def _header_value(name: str) -> float:
    match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f?;", _header())
    assert match, name
    return float(match.group(1))


def _header_enum(name: str) -> int:
    match = re.search(rf"\b{name}\s*=\s*(\d+),", _header())
    assert match, name
    return int(match.group(1))


def _header_nh(name: str) -> tuple[float, float]:
    match = re.search(rf"\b{name}\{{\s*(-?[\d.]+)f?,\s*(-?[\d.]+)f?\s*\}};", _header())
    assert match, name
    return float(match.group(1)), float(match.group(2))


class ArgelmachDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) == ARGELMACH}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) in (*GOLEMS, ORB)}
        cls.models = {int(e["CreatureID"]): int(e["CreatureDisplayID"]) for e in reg.creature_template_models
                      if int(e["CreatureID"]) in (*GOLEMS, ORB)}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.source = SOURCE.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(CHAIN, STATUE + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"spell": mine}), [])
        found = re.search(r"kSpellsArgelmach\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(found)
        self.assertEqual((int(found.group(1)), int(found.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_AR_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))

    def test_argelmach_binding(self):
        # Behind the wave switch: read from the source (the gate's on/off state is S0's test).
        match = re.search(r"creature_template_columns\(8983, \*\*boss_columns\(\s*'([a-z_]+)', ([\d.]+), "
                          r"damage_modifier=([\d.]+),", self.source)
        self.assertIsNotNone(match)
        self.assertIn("if BIND_WAVE_2:", self.source[:match.start()])
        self.assertEqual(match.group(1), "boss_golem_lord_argelmach_rework")
        normal, heroic = _header_nh("kBossHealth")
        self.assertLessEqual(abs(math.ceil(PALADIN_55_BASE * float(match.group(2))) - int(normal)), 2)
        self.assertEqual(int(heroic), 220_000)
        self.assertEqual(float(match.group(3)), 3.5)
        if ARGELMACH in self.edits:     # wave 2 bound
            row = self.edits[ARGELMACH]
            self.assertEqual(row["ScriptName"], "boss_golem_lord_argelmach_rework")
            self.assertEqual(row["AIName"], "")
            self.assertEqual(row["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
        # The boss registers only once wave 2 binds; his golems, the orb and the spell scripts always.
        self.assertIn("if (kWave2Bound)\n        RegisterDungeonReworkCreatureAI(boss_golem_lord_argelmach_rework,",
                      self.cpp)
        for name in ("npc_brd_argelmach_golem", "npc_brd_argelmach_arcane_orb"):
            self.assertIn(f"RegisterDungeonReworkCreatureAI({name},", self.cpp)
        for name in (HIT_SCRIPT, LIVEWIRE_SCRIPT):
            self.assertIn(f"RegisterSpellScript({name});", self.cpp)

    def test_the_statue_look_lands_through_immunity_1972(self):
        # R-2-A MA-1: stock Stoned 10255 carries EffectMechanic FREEZE (13), which the golems' set 1972 drops, so
        # AddAura was a no-op. The copy has no mechanic and NO_IMMUNITIES and keeps 10255's visual; the C++ puts and
        # takes the copy (the stock id stays only for the hall golems' SQL), and the kill-order condition reads it.
        spell = self.spells[STATUE]
        self.assertEqual(spell["name"], "Stoned")
        self.assertEqual(spell["mechanic"], 0)
        self.assertEqual(spell["effect1"]["type"], APPLY_AURA)
        self.assertEqual(spell["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(int(spell["effect1"].get("mechanic", 0) or 0), 0)
        self.assertTrue(spell["attributes"] & ATTR0_NO_IMMUNITIES)
        self.assertEqual(_raw(spell, "SpellVisualID_1"), SV_STOCK_STONED)
        self.assertEqual(int(spell["duration_ms"]), -1)
        self.assertEqual(STATUE, 211349)
        self.assertRegex(_header(), r"SPELL_AR_STATUE\s*=\s*kSpellSlice\.first \+ 19,")
        self.assertNotIn("AddAura(kSpellStoned", self.cpp)
        self.assertIn("golem->AddAura(SPELL_AR_STATUE, golem);", self.cpp)
        self.assertIn("golem->RemoveAurasDueToSpell(SPELL_AR_STATUE);", self.cpp)
        self.assertIn("Condition::LacksAura(SPELL_AR_STATUE)", self.cpp)
        self.assertNotIn(STOCK_STONED, self.spells)

    def test_livewire_never_marks_the_tank(self):
        # Orchestrator default 2026-11-17 (R-2-A designer question 1): the RunOut would push the melee off the boss.
        self.assertRegex(_header(), r"kLivewireMarksTank = false;")
        self.assertIn("DungeonKit::PickRule rule = LivewirePickRule();", self.cpp)

    def test_golems(self):
        normal, heroic = _header_nh("kGolemHealth")
        self.assertEqual(int(heroic), 37_000)
        for entry, (name, display, heroic_entry) in GOLEMS.items():
            golem = self.creatures[entry]
            self.assertEqual(golem["name"], name)
            self.assertEqual(golem["ScriptName"], "npc_brd_argelmach_golem")
            self.assertEqual(golem["AIName"], "")
            self.assertEqual((golem["minlevel"], golem["maxlevel"]), (55, 55))
            self.assertEqual((golem["rank"], golem["unit_class"]), (1, 1))
            self.assertEqual(golem["type"], 9)                     # mechanical
            self.assertEqual(golem["faction"], FACTION_DARK_IRON)
            self.assertEqual(golem["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
            self.assertEqual(golem["unit_flags"], 0)                # the script makes the statues unselectable
            self.assertEqual(golem["lootid"], 0)
            self.assertEqual(float(golem["ExperienceModifier"]), 0.0)
            self.assertEqual(math.ceil(WARRIOR_55_BASE * float(golem["HealthModifier"])), int(normal))
            self.assertEqual(golem["difficulty_entry_1"], heroic_entry)
            self.assertEqual(self.models[entry], display)
            self.assertIn(f"NPC_BRD_{name.upper()}", self.cpp + REWORK.read_text(encoding="utf-8"))

    def test_the_orb(self):
        orb = self.creatures[ORB]
        self.assertEqual(orb["name"], "Arcane Orb")
        self.assertEqual(orb["ScriptName"], "npc_brd_argelmach_arcane_orb")
        self.assertTrue(int(orb["unit_flags"]) & NOT_SELECTABLE)
        self.assertEqual(orb["difficulty_entry_1"] if "difficulty_entry_1" in orb else 0, 0)    # no heroic template
        self.assertEqual(self.models[ORB], 26753)
        self.assertIn("spec.entry = NPC_BRD_ARCANE_ORB;", self.cpp)

    def test_his_copies(self):
        chain = self.spells[CHAIN]
        normal, heroic = _header_nh("kChainPct")
        self.assertEqual(chain["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertEqual(chain["effect1"]["base_points"] + 1, round(normal * 100))
        self.assertEqual(_raw(chain, "EffectMiscValueB_1"), round(heroic * 100))
        self.assertEqual(chain["effect1"]["chain_targets"], int(_header_value("kChainTargets")))
        self.assertEqual(_raw(chain, "EffectChainAmplitude_1"), 1.0)
        self.assertEqual(chain["cast_time_ms"], int(_header_value("kChainCastMs")))
        self.assertEqual(_raw(chain, "InterruptFlags"), 15)          # kickable
        self.assertEqual(chain["school"], SCHOOL_NATURE)
        self.assertIn((CHAIN, HIT_SCRIPT), self.scripts)
        self.assertTrue(int(_raw(chain, "AttributesEx3")) & IGNORE_CASTER_MODIFIERS)
        self.assertIn("d.interrupts.emplace_back(NPC_ARGELMACH, SPELL_AR_CHAIN_LIGHTNING", self.cpp)

        shock = self.spells[SHOCK]
        normal, heroic = _header_nh("kShockPct")
        self.assertEqual(shock["effect1"]["base_points"] + 1, round(normal * 100))
        self.assertEqual(_raw(shock, "EffectMiscValueB_1"), round(heroic * 100))
        self.assertIn((SHOCK, HIT_SCRIPT), self.scripts)
        self.assertTrue(int(_raw(shock, "AttributesEx3")) & IGNORE_CASTER_MODIFIERS)

        shield = self.spells[SHIELD]
        self.assertEqual(shield["effect1"]["apply_aura"], AURA_PROC_TRIGGER_DAMAGE)
        self.assertEqual(shield["dispel"], DISPEL_MAGIC)
        self.assertEqual((_raw(shield, "ProcChance"), _raw(shield, "ProcCharges")), (50, 3))
        self.assertEqual(_raw(shield, "ProcTypeMask"), 139944)
        self.assertIn("d.purges.emplace_back(NPC_ARGELMACH, SPELL_AR_LIGHTNING_SHIELD", self.cpp)
        self.assertIn("CastCustomSpell(me, SPELL_AR_LIGHTNING_SHIELD", self.cpp)
        # None of them is the stock id (rule 15).
        for stock in (15305, 15605, 15507):
            self.assertNotIn(stock, self.spells)

    def test_the_registry_hits_are_resolve_copies(self):
        for spell_id, school, name in ((CLOUD, SCHOOL_NATURE, "SPELL_AR_CHEMICAL_CLOUD"),
                                       (JOLT, SCHOOL_NATURE, "SPELL_AR_LETHAL_JOLT"),
                                       (PULSE, SCHOOL_NATURE, "SPELL_AR_LIVEWIRE_PULSE"),
                                       (BURST, SCHOOL_NATURE, "SPELL_AR_LIVEWIRE_BURST"),
                                       (SURGE, SCHOOL_ARCANE, "SPELL_AR_POWER_SURGE"),
                                       (CATCH, SCHOOL_ARCANE, "SPELL_AR_OVERCHARGE_CATCH"),
                                       (BLAST, SCHOOL_ARCANE, "SPELL_AR_OVERCHARGE_BLAST")):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertEqual(spell["school"], school, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
            self.assertRegex(self.cpp, rf"(spellId = |\.Spell\(){name}\b")

    def test_poison_mist(self):
        mist = self.spells[MIST]
        self.assertEqual(mist["dispel"], DISPEL_POISON)
        self.assertEqual(mist["cast_time_ms"], int(_header_value("kMistCastMs")))
        self.assertEqual(mist["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertEqual(mist["effect1"]["base_points"] + 1, round(_header_value("kMistPct") * 100))
        self.assertEqual(mist["effect2"]["apply_aura"], AURA_PERIODIC_DAMAGE)
        self.assertEqual(mist["effect2"]["base_points"], round(_header_value("kMistTickPct") * 100))
        self.assertEqual(mist["effect2"]["amplitude"], int(_header_value("kMistTickMs")))
        self.assertEqual(mist["duration_ms"], int(_header_value("kMistDotMs")))
        self.assertEqual(_raw(mist, "InterruptFlags"), 0)            # a must-play bar
        self.assertIn((MIST, REFFLAT), self.scripts)
        self.assertIn((MIST, REFFLAT_PERIODIC), self.scripts)
        self.assertIn("d.dispels.emplace_back(SPELL_AR_POISON_MIST", self.cpp)

    def test_livewire_and_the_marks(self):
        livewire = self.spells[LIVEWIRE]
        self.assertEqual(livewire["dispel"], DISPEL_MAGIC)
        self.assertEqual(livewire["duration_ms"], int(_header_value("kLivewireMs")))
        self.assertIn((LIVEWIRE, LIVEWIRE_SCRIPT), self.scripts)
        self.assertIn("NearPlayer(kLivewireRadiusYd)", self.cpp)
        self.assertEqual(self.spells[TETHER]["duration_ms"], int(_header_value("kTetherMs")))
        self.assertEqual(self.spells[TETHER]["dispel"], 0)
        self.assertEqual(self.spells[BOMB]["duration_ms"], int(_header_value("kBombWarnMs")))
        self.assertEqual(self.spells[BOMB]["dispel"], 0)
        self.assertEqual(self.spells[CLOUD_LOOK]["duration_ms"], int(_header_value("kCloudLifeMs")))
        # Rule 6: every aura the fight puts on players comes off at the end.
        for name in ("SPELL_AR_CHEMICAL_BOMB", "SPELL_AR_POISON_MIST", "SPELL_AR_LETHAL_ATTRACTION",
                     "SPELL_AR_LIVEWIRE", "SPELL_AR_OVERCHARGED"):
            self.assertRegex(self.cpp, rf"for \(uint32 spell : \{{[^}}]*\b{name}\b")

    def test_the_buffs(self):
        for spell_id, pct, stacks, ms in ((OVERCHARGED, "kOverchargedPct", "kOverchargedMaxStacks", "kOverchargedMs"),
                                          (EMPOWERED, "kEmpoweredPctPerStack", "kEmpoweredMaxStacks",
                                           "kEmpoweredMs")):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["apply_aura"], AURA_MOD_DAMAGE_PERCENT_DONE)
            self.assertEqual(spell["effect1"]["base_points"], int(_header_value(pct)))
            self.assertEqual(_raw(spell, "CumulativeAura"), int(_header_value(stacks)))
            self.assertEqual(spell["duration_ms"], int(_header_value(ms)))

    def test_the_looks(self):
        for spell_id, spell in self.spells.items():
            visual = int(_raw(spell, "SpellVisualID_1"))
            self.assertNotIn(visual, WRONG, f"{spell_id}: {WRONG.get(visual)}")
        for spell_id in (WAKES, BOMB, CLOUD_LOOK, TETHER, LIVEWIRE, OVERCHARGE_BOMB, CHAIN, SHOCK, SHIELD, MIST):
            self.assertNotEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), 0, spell_id)

    def test_the_sql_rev(self):
        sql = SQL.read_text(encoding="utf-8")
        types = {0: 14, 1: 14, 2: 14, 3: 14, 5: 41, 6: 41, 7: 14}
        for group, kind in types.items():
            self.assertRegex(sql, rf"\(8983, {group}, 0, '[^\n]*', {kind},")
        self.assertEqual(len(re.findall(r"^\(8983, \d+,", sql, re.M)), 7)
        self.assertNotRegex(sql, r"^\(8983, 4,")                              # D16's console line
        self.assertIn("`GroupID` IN (0, 1, 2, 3, 5, 6, 7)", sql)
        self.assertIn("Intruders in the Manufactory? My constructs will destroy you!', 14, 0, 100, 0, 0, 0, 5297,",
                      sql)
        self.assertIn("DELETE FROM `smart_scripts` WHERE `entryorguid` = 8983 AND `source_type` = 0;", sql)
        for name, group in (("YELL_AR_AGGRO", 0), ("YELL_AR_TOXITRON", 1), ("YELL_AR_ELECTRON", 2),
                            ("YELL_AR_ARCANOTON", 3), ("YELL_AR_CONSOLE", 4), ("EMOTE_AR_INCINERATE", 5),
                            ("EMOTE_AR_CORE", 6), ("YELL_AR_DEATH", 7)):
            self.assertEqual(_header_enum(name), group)
        # The pedestals: three templates and three spawns (spawnMask 3) at the header's spots.
        for entry, pedestal in ((301285, "kPedestal1"), (301286, "kPedestal2"), (301287, "kPedestal3")):
            self.assertRegex(sql, rf"\({entry}, 5, 3311, 'Golem Pedestal',")
            spot = re.search(rf"\b{pedestal}\{{\s*([\d.-]+)f,\s*([\d.-]+)f,\s*([\d.-]+)f\s*\}};", _header())
            self.assertIsNotNone(spot)
            x, y, z = (float(v) for v in spot.groups())
            self.assertRegex(sql, rf"\({entry}0, {entry}, 230, 0, 0, 3, 1, {x:g}, {y:g}, {z:g},")
        # The hall: no Stoned left on the Ragereavers (both difficulties) or the Wrath Hammer; the chamber's two moved.
        self.assertIn("UPDATE `creature_template_addon` SET `auras` = '' WHERE `entry` = 8906;", sql)
        # the heroic copy's addon row follows the replayed normal row (lib/dungeon_heroic.py): no unreplayable subquery
        self.assertNotIn("SELECT `difficulty_entry_1` FROM", sql)
        self.assertIn("UPDATE `creature_addon` SET `auras` = '' WHERE `guid` = 45933;", sql)
        self.assertIn("WHERE `guid` = 45932 AND `id` = 8906;", sql)
        self.assertIn("WHERE `guid` = 45933 AND `id` = 8907;", sql)


@unittest.skipUnless(BM_DRILL.is_file(), "no mod-boss-mechanics source (set BOSS_MECHANICS_SRC)")
class ArgelmachMatchesTheLivewireDrillTest(unittest.TestCase):
    """G2's Livewire row (reported, not gated): the fight's tags and numbers read the same as the drill's."""

    @classmethod
    def setUpClass(cls):
        cls.drill = BM_DRILL.read_text(encoding="utf-8")

    def _drill(self, name: str) -> float:
        match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f?;", self.drill)
        self.assertIsNotNone(match, name)
        return float(match.group(1))

    def test_tags_and_numbers(self):
        self.assertEqual(self._drill("kBrd2TagLivewire"), _header_enum("TAG_AR_LIVEWIRE"))
        self.assertEqual(self._drill("kBrd2TagLivewireBurst"), _header_enum("TAG_AR_LIVEWIRE_BURST"))
        self.assertEqual(self._drill("kLivewireYd"), _header_value("kLivewireRadiusYd"))
        self.assertEqual(self._drill("kLivewireMs"), _header_value("kLivewireMs"))
        self.assertEqual(self._drill("kLivewireTickMs"), _header_value("kLivewirePulseMs"))


if __name__ == "__main__":
    unittest.main()
