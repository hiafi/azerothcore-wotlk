"""
Scarlet Monastery build WP-D4H, the Desecration (Thalnos's hard mode):
source/npcs/scarlet_monastery/thalnos_hard_mode.py against its C++ (modules/mod-dungeon-bosses
src/ScarletMonastery/ThalnosHardModeLogic.h, thalnos_hard_mode.cpp) and its SQL rev.

Checks:
  - the spells sit in the slice (212480-212539) and ThalnosHardModeLogic.h names the same ids;
  - the risen 300903-300906 are level 60 undead elites of Thalnos's faction at 20k, the spectre displays, the hard
    mode's AI, no loot and no XP, their heroic entries from the STAGE-H table; the banner is untargetable scenery;
  - the bars: the teleport is a must-play Arcane bar (no kick), Repent and Greater Heal kick only (Holy), the
    wind-up is not interruptible; the tether is a channel that allows actions with no interrupt flags;
  - the auras: Blood Pact stacks to 4 (not dispellable), Repent a 2 s Magic incapacitate, the shield a 5k Magic
    absorb for 20 s, the hits are resolve copies (Physical);
  - the looks are V's and never a WRONG pick; the numbers equal the header's;
  - the C++ registers what the build spec names (the kill order, the interrupts, the purge, the ward, the drag zone,
    the stones' scripts, the hooks) and the SQL rev writes the texts, the objects, their gossip texts, their heroic
    spawns at the section 7 #18 A spots, and moves the Anguished Dead off the rite.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scarlet_monastery_thalnos_hard_mode.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "ScarletMonastery"
HEADER = MODULE_DIR / "ThalnosHardModeLogic.h"
REWORK = MODULE_DIR / "ScarletMonasteryRework.h"
SCRIPT = MODULE_DIR / "thalnos_hard_mode.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_thalnos_hard_mode_scarlet_monastery.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "scarlet_monastery"

SLICE = range(212480, 212540)
(HARD_MODE_AURA, NO_REST, BLOOD_PACT, TETHER, RISE, STONE_STIR, STONE_BLOOD, DISTURB, RALLIED, CHARGE_LOOK,
 CHARGE_HIT, REPENT, GREATER_HEAL, PWS, WINDUP, WHIRLWIND, WHIRLWIND_HIT) = range(212480, 212497)
GALVAR, FAIRBELL, VOSS, GOODCHILDE, BANNER = range(300903, 300908)
RISEN = (GALVAR, FAIRBELL, VOSS, GOODCHILDE)
HEROIC = {GALVAR: 310461, FAIRBELL: 310462, VOSS: 310463, GOODCHILDE: 310464}
BASE_HP_60 = {1: 3052, 2: 2442}     # creature_classlevelstats level 60 basehp0 (warrior, paladin)
FACTION_UNDEAD = 21

SCHOOL_NORMAL, SCHOOL_HOLY, SCHOOL_SHADOW, SCHOOL_ARCANE = 1, 2, 32, 64
SCHOOL_DAMAGE, DUMMY_EFFECT, APPLY_AURA, HEAL = 2, 3, 6, 10
AURA_DUMMY, AURA_MOD_STUN, AURA_SCHOOL_ABSORB = 4, 12, 69
DISPEL_MAGIC = 1
INTERRUPT_KICK = 0x4
ATTR1_IS_CHANNELED = 0x4
ATTR5_ALLOW_ACTION_DURING_CHANNEL = 0x1
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
RESOLVE = "spell_boss_mechanics_resolve"
# V's picks (_visuals.py) and the WRONG list for Thalnos's hard mode (VR: Summon Spirits, Blood Link, Battle Standard,
# Whirlwind 8989).
SV_RED, SV_TELEPORT, SV_TETHER, SV_RAISE = 90554, 7934, 7270, 4582
SV_CHARGE, SV_REPENT, SV_HEAL, SV_PWS, SV_WHIRLWIND = 867, 5539, 57, 784, 7428
SV_WRONG = (8116, 15256, 6801, 6664)
SPECTRES = {GALVAR: 90800, FAIRBELL: 90801, VOSS: 90802, GOODCHILDE: 90803}


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


def _code(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith(("//", "*", "/*")))


class DesecrationDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates
                         if int(e["entry"]) in (*RISEN, BANNER)}
        cls.models = {int(e["CreatureID"]): e for e in reg.creature_template_models
                      if int(e["CreatureID"]) in (*RISEN, BANNER)}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(HARD_MODE_AURA, WHIRLWIND_HIT + 1)))
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery", {"spell": mine}), [])
        first = re.search(r"kSpellsDesecration\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(first)
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_DS_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))

    def test_the_risen(self):
        for entry in RISEN:
            row = self.creatures[entry]
            self.assertEqual(row["ScriptName"], "npc_sm_risen_hero", entry)
            self.assertEqual(row["AIName"], "", entry)
            self.assertEqual((row["minlevel"], row["maxlevel"]), (60, 60), entry)
            self.assertEqual(row["rank"], 1, entry)
            self.assertEqual(row["faction"], FACTION_UNDEAD, entry)
            self.assertEqual(row["type"], 6, entry)
            self.assertEqual(row["lootid"], 0, entry)
            self.assertEqual(row["flags_extra"] & 0x40, 0x40, entry)
            self.assertEqual(row["CreatureImmunitiesId"], 0, entry)
            self.assertEqual(row["difficulty_entry_1"], HEROIC[entry], entry)
            # 20k (section 3.6), within 2 HP.
            health = math.ceil(BASE_HP_60[row["unit_class"]] * row["HealthModifier"])
            self.assertLessEqual(abs(health - int(_header_value("kRisenHealth"))), 2, entry)
            self.assertEqual(self.models[entry]["CreatureDisplayID"], SPECTRES[entry], entry)
        self.assertEqual(self.creatures[VOSS]["unit_class"], 2)         # mana for his casts
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_sm_risen_hero,", self.cpp)

    def test_the_banner(self):
        row = self.creatures[BANNER]
        self.assertEqual(row["ScriptName"], "")
        self.assertEqual(row["faction"], FACTION_UNDEAD)
        self.assertTrue(row["unit_flags"] & 0x02000000)        # not selectable
        self.assertTrue(row["unit_flags"] & 0x2)               # not attackable
        self.assertEqual(row["DamageModifier"], 0.0)
        self.assertNotIn("difficulty_entry_1", {k for k, v in row.items() if v})
        self.assertEqual(self.models[BANNER]["CreatureDisplayID"], 14541)

    def test_the_bars(self):
        no_rest = self.spells[NO_REST]
        self.assertEqual(no_rest["school"], SCHOOL_ARCANE)      # his kickable bars are Shadow and Physical
        self.assertEqual(no_rest["cast_time_ms"], int(_header_value("kNoRestCastMs")))
        self.assertEqual(_raw(no_rest, "InterruptFlags"), 0)
        self.assertEqual(_raw(no_rest, "PreventionType"), 0)
        self.assertEqual(_raw(no_rest, "SpellVisualID_1"), SV_TELEPORT)
        for spell_id, cast in ((REPENT, "kRepentCastMs"), (GREATER_HEAL, "kHealCastMs")):
            bar = self.spells[spell_id]
            self.assertEqual(bar["school"], SCHOOL_HOLY, spell_id)
            self.assertEqual(_raw(bar, "InterruptFlags"), INTERRUPT_KICK, spell_id)
            self.assertEqual(_raw(bar, "PreventionType"), 1, spell_id)
            self.assertEqual(bar["cast_time_ms"], int(_header_value(cast)), spell_id)
        windup = self.spells[WINDUP]
        self.assertEqual(windup["cast_time_ms"], int(_header_value("kWhirlwindWindupMs")))
        self.assertEqual(_raw(windup, "InterruptFlags"), 0)
        disturb = self.spells[DISTURB]
        self.assertEqual(disturb["cast_time_ms"], int(_header_value("kDisturbCastMs")))
        self.assertEqual(disturb["effect1"]["type"], DUMMY_EFFECT)
        self.assertEqual(disturb["effect1"]["implicit_target_a"], 23)     # TARGET_GAMEOBJECT_TARGET

    def test_the_tether(self):
        tether = self.spells[TETHER]
        self.assertTrue(_raw(tether, "AttributesEx") & ATTR1_IS_CHANNELED)
        self.assertTrue(_raw(tether, "AttributesEx5") & ATTR5_ALLOW_ACTION_DURING_CHANNEL)
        for column in ("InterruptFlags", "ChannelInterruptFlags", "AuraInterruptFlags"):
            self.assertEqual(_raw(tether, column), 0, column)
        self.assertEqual(_raw(tether, "SpellVisualID_1"), SV_TETHER)
        self.assertGreaterEqual(tether["range_yards"], 60)

    def test_the_auras(self):
        pact = self.spells[BLOOD_PACT]
        self.assertEqual(pact["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(_raw(pact, "CumulativeAura"),
                         int(_header_value("kPactCapPct") / _header_value("kPactPctPerRisen")))
        self.assertEqual(pact["dispel"], 0)
        repent = self.spells[REPENT]
        self.assertEqual(repent["effect1"]["apply_aura"], AURA_MOD_STUN)
        self.assertEqual(repent["duration_ms"], int(_header_value("kRepentMs")))
        self.assertEqual(repent["dispel"], DISPEL_MAGIC)
        self.assertEqual(repent["mechanic"], 14)
        shield = self.spells[PWS]
        self.assertEqual(shield["effect1"]["apply_aura"], AURA_SCHOOL_ABSORB)
        self.assertEqual(int(shield["effect1"]["base_points"]), int(_header_value("kShieldAbsorb")))
        self.assertEqual(int(shield["effect1"]["die_sides"]), 0)
        self.assertEqual(shield["duration_ms"], int(_header_value("kShieldMs")))
        self.assertEqual(shield["dispel"], DISPEL_MAGIC)
        heal = self.spells[GREATER_HEAL]
        self.assertEqual(heal["effect1"]["type"], HEAL)
        self.assertEqual(int(heal["effect1"]["die_sides"]), 0)      # the script's BP0 is exact
        self.assertTrue(_raw(heal, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertEqual(self.spells[RALLIED]["duration_ms"], int(_header_value("kRalliedMs")))
        self.assertEqual(int(self.spells[RALLIED]["effect1"]["base_points"]), int(_header_value("kBannerBoostPct")))
        self.assertEqual(self.spells[WHIRLWIND]["duration_ms"], int(_header_value("kWhirlwindSpinMs")))
        self.assertEqual(self.spells[HARD_MODE_AURA]["duration_ms"], -1)

    def test_the_hits_are_resolve_copies(self):
        for spell_id in (CHARGE_HIT, WHIRLWIND_HIT):
            spell = self.spells[spell_id]
            self.assertEqual(spell["school"], SCHOOL_NORMAL, spell_id)
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
        self.assertEqual({name for _, name in self.scripts}, {RESOLVE})

    def test_the_looks(self):
        looks = {HARD_MODE_AURA: SV_RED, STONE_BLOOD: SV_RED, TETHER: SV_TETHER, RISE: SV_RAISE,
                 CHARGE_LOOK: SV_CHARGE, REPENT: SV_REPENT, GREATER_HEAL: SV_HEAL, PWS: SV_PWS,
                 WHIRLWIND: SV_WHIRLWIND, NO_REST: SV_TELEPORT}
        for spell_id, look in looks.items():
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), look, spell_id)
        for spell in self.spells.values():
            self.assertNotIn(_raw(spell, "SpellVisualID_1"), SV_WRONG, spell["id"])

    def test_the_cpp_registers_the_spec(self):
        code = _code(self.cpp)
        # The hooks of ThalnosFight.h and the stones' and rite's scripts.
        for text in ("SmThalnos::RegisterThalnosHardMode(", "SmThalnos::RegisterThalnosIdleHook(",
                     "RegisterDungeonReworkGameObjectAI(go_sm_desecration_stone,",
                     "RegisterDungeonReworkGameObjectAI(go_sm_blood_rite,", 'SmTest::RegisterBoss("desecration"',
                     "fight.SetGround(Ground::Lawn, \"no-rest\");", "fight.Say(SmThalnos::SAY_NO_REST);",
                     "thalnos->AI()->Talk(SmThalnos::SAY_WAKE_THEM_ALL);",
                     "DungeonKit::Flex::SetHealth(boss, kThalnosHardModeHealth, true);",
                     "DungeonKit::SetHardModeLoot(boss, true);", "_ward.Mitigate(damage);",
                     "instance->SetData(DATA_DESECRATION_TOUCH,", "NPC_HAUNTING_PHANTASM"):
            self.assertIn(text, code)
        # The kill order, the interrupts (the tether never), the purge.
        self.assertIn("TargetEntry(EntryOf(h), KillPriority(h), BossMechanics::Who::Dps)", code)
        self.assertRegex(code, r"InterruptEntry\(NPC_SM_FAIRBELL, SPELL_DS_REPENT, 1,")
        self.assertRegex(code, r"InterruptEntry\(NPC_SM_VOSS, SPELL_DS_GREATER_HEAL, 3,")
        self.assertIn("InterruptEntry(0, SPELL_DS_PACT_TETHER, 0)", code)
        self.assertIn("PurgeEntry(0, SPELL_DS_POWER_WORD_SHIELD, 1)", code)
        # The drag zone: tank only, no damage; the charge and the spin include the tank, Weakened.
        self.assertIn("tankOnly.roles = BossMechanics::Role::Tank;", code)
        self.assertIn(".Damage(0.f).Eligible(tankOnly)", code)
        self.assertIn("ref.Damage(pct).TankDamage(pct).Weakened().Spell(SPELL_DS_CHARGE_HIT)", code)
        self.assertIn(".Damage(pct).TankDamage(pct).Weakened()\n            .Spell(SPELL_DS_WHIRLWIND_HIT)", code)
        # Every bot shape bounded by the lawn (RB-8).
        self.assertEqual(code.count(".Within(LawnBounds())"), 3)
        self.assertNotIn("\t", self.cpp)


class DesecrationSqlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.code = "\n".join(line for line in cls.sql.splitlines() if not line.startswith("--"))
        cls.header = _header()

    def test_the_texts(self):
        self.assertRegex(self.sql, r"\(4543, 4, 0, 'Yes\.\.\. wake them all!', 14, ")
        self.assertRegex(self.sql, r"\(300903, 0, 0, '%s plants the banner of the Crusade!', 41, ")
        self.assertRegex(self.sql, r"\(300906, 0, 0, '%s begins to spin!', 41, ")
        # Thalnos's stock lines and D4's group 3 are never deleted.
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 4543 AND `GroupID` = 4;", self.code)
        self.assertNotIn("`GroupID` = 3", self.code)

    def test_the_objects(self):
        for entry, script, display in ((301310, "go_sm_desecration_stone", 499),
                                       (301311, "go_sm_desecration_stone", 499),
                                       (301312, "go_sm_desecration_stone", 499),
                                       (301313, "go_sm_desecration_stone", 499),
                                       (301314, "go_sm_blood_rite", 15)):
            self.assertRegex(self.code, rf"\({entry}, 10, {display}, '[^']+'[^\n]*\n[^\n]*'{script}', 0\)")
        self.assertNotIn("DELETE FROM `gameobject_template` ", self.code)
        # The gossip texts: ids = entries, the four epitaphs and the rite's order (adjacent literals joined).
        joined = re.sub(r"'\n\s+'", "", self.code)
        for text in ("He marched the armies of the Crusade from Tirisfal to Hearthglen.",
                     "He put the question to Gilneas, and the city answered in fire.",
                     "Shepherd of the Crusade''s souls. Slain by his own blood.",
                     "Last to lead the Crusade, last to stand.",
                     "Wake first the general of the long march. Wake second the questioner of the burning city. "
                     "Wake third the father slain by his daughter. Wake last the last of their captains."):
            self.assertIn(text, joined)
        self.assertIn("DELETE FROM `npc_text` WHERE `ID` BETWEEN 301310 AND 301314;", self.code)

    def test_the_spawns(self):
        # Heroic only, at the header's spots (section 7 #18 A), facing the disc's center.
        spots = re.findall(r"\{ (\d+\.\d+)f, (\d+\.\d+)f, (\d+\.\d+)f \},\s*// (\w+)", self.header)
        self.assertEqual([s[3] for s in spots], ["Galvar", "Fairbell", "Voss", "Goodchilde"])
        rows = re.findall(r"\((30131\d0), (3013\d\d), 189, 0, 0, (\d), 1, ([\d.]+), ([\d.]+), ([\d.]+), "
                          r"([\d.]+), 0, 0, ([-\d.]+), ([-\d.]+),", self.code)
        self.assertEqual(len(rows), 5)
        for guid, entry, mask, x, y, z, o, r2, r3 in rows:
            self.assertEqual(int(guid), int(entry) * 10)
            self.assertEqual(mask, "2")
            self.assertAlmostEqual(float(r2), math.sin(float(o) / 2), places=4)
            self.assertAlmostEqual(float(r3), math.cos(float(o) / 2), places=4)
        for (x, y, z, _), row in zip(spots, rows[:4]):
            self.assertEqual((float(x), float(y), float(z)), (float(row[3]), float(row[4]), float(row[5])))
            facing = math.atan2(1369.5 - float(y), 1796.5 - float(x)) % (2 * math.pi)
            self.assertAlmostEqual(float(row[6]), facing, places=3)
        self.assertEqual(rows[4][1], "301314")
        self.assertEqual((float(rows[4][3]), float(rows[4][4])), (1788.5, 1417.0))

    def test_the_anguished_dead_moves(self):
        match = re.search(r"UPDATE `creature` SET `position_x` = ([\d.]+), `position_y` = ([\d.]+) "
                          r"WHERE `guid` = 39906 AND `id` = 6426;", self.code)
        self.assertIsNotNone(match)
        moved = math.hypot(float(match.group(1)) - 1788.5, float(match.group(2)) - 1417.0)
        self.assertGreaterEqual(moved, 10.0)
        self.assertLessEqual(moved, 11.0)
        for table in ("smart_scripts", "creature_loot_template", "conditions", "DELETE FROM `creature` "):
            self.assertNotIn(table, self.code)


if __name__ == "__main__":
    unittest.main()
