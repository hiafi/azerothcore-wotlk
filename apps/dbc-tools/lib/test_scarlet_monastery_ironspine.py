"""
Scarlet Monastery build WP-D2, Ironspine: source/npcs/scarlet_monastery/ironspine.py against its C++
(modules/mod-dungeon-bosses src/ScarletMonastery/IronspineLogic.h, boss_ironspine_rework.cpp) and its SQL rev
(data/sql/updates/pending_db_world/rev_ironspine_scarlet_monastery.sql).

Checks:
  - the spells sit in his slice (212350-212389) and IronspineLogic.h names the same ids;
  - he is bound (SmartAI off, immunity 1972, INSTANCE_BIND), 36k at 5 players;
  - the parts: three entries, undead, level 32, 3k each, stun immune, no melee, the script, WP-V's models;
  - the pool (resolve copy, Nature) and its four rung looks on WP-V's SV_GRAVE_ROT; the Fist's resolve copy; the
    Crush (a root with the root mechanic) and its squeeze (ignores armor and caster modifiers); Reassembled; the heal;
    the Glare's bar and stun; no look the VISUALS report marks WRONG (SV 118, SV 7434);
  - the SQL rev: guid 12164 on the lawn at the header's kIronspineHome, his four texts and the Eye's one, all emotes.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scarlet_monastery_ironspine.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "ScarletMonastery"
HEADER = MODULE_DIR / "IronspineLogic.h"
REWORK = MODULE_DIR / "ScarletMonasteryRework.h"
SCRIPT = MODULE_DIR / "boss_ironspine_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_ironspine_scarlet_monastery.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "scarlet_monastery"
VISUALS = PACKAGE / "_visuals.py"

SLICE = range(212350, 212390)
(ROT_CAST, ROT, LOOK_7, LOOK_8, LOOK_9, LOOK_10, SHATTER, REASSEMBLED, HEAL, FIST_SLAM, FIST_LANDING, CRUSH,
 CRUSH_TICK, CLOSED, EYE_SIGHT, GLARE_CAST, GLARE) = range(212350, 212367)
IRONSPINE = 6489
FIST, RIBCAGE, EYE = 300900, 300901, 300902
WARRIOR_32_BASE = 1057

SCHOOL_DAMAGE, APPLY_AURA, HEAL_EFFECT, DUMMY_EFFECT = 2, 6, 10, 3
AURA_DUMMY, AURA_MOD_STUN, AURA_MOD_ROOT, AURA_MOD_DAMAGE_PERCENT_DONE = 4, 12, 26, 79
SCHOOL_PHYSICAL, SCHOOL_NATURE, SCHOOL_SHADOW = 1, 8, 32
MECHANIC_ROOT, MECHANIC_STUN = 7, 12
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
CU_IGNORE_ARMOR = 0x8000
CHANGE_MAP = 0x00080000
RESOLVE = "spell_boss_mechanics_resolve"
IMMUNITY_BOSS_STUN = 1972
INSTANCE_BIND = 0x1
WRONG_VISUALS = {118, 7434}     # VISUALS: Slime Pool's one-shot puff; Eye Beam with no beam


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


def _visual(name: str) -> int:
    text = VISUALS.read_text(encoding="utf-8")
    match = re.search(rf"^{name}\s*=\s*(\w+)", text, re.MULTILINE)
    assert match, name
    value = match.group(1)
    return int(value) if value.isdigit() else _visual(value)


def _grave_rot_rungs() -> dict[int, int]:
    text = VISUALS.read_text(encoding="utf-8")
    match = re.search(r"^SV_GRAVE_ROT = \{([^}]*)\}", text, re.MULTILINE)
    assert match
    return {int(k): int(v) for k, v in re.findall(r"(\d+):\s*(\d+)", match.group(1))}


class IronspineDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.custom = {int(e["spell_id"]): int(e["attributes"]) for e in reg.custom_attrs if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) == IRONSPINE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) in (FIST, RIBCAGE, EYE)}
        cls.models = {int(m["CreatureID"]): m for m in reg.creature_template_models
                      if int(m["CreatureID"]) in (FIST, RIBCAGE, EYE)}
        cls.header = HEADER.read_text(encoding="utf-8")

    def test_spells_in_slice_and_header(self):
        self.assertEqual(sorted(self.spells), list(range(212350, 212367)))
        names = re.findall(r"\b(SPELL_IR_\w+)\s*=\s*kSpellSlice\.first \+ (\d+),", self.header)
        self.assertEqual(len(names), 17)
        for _, offset in names:
            self.assertIn(212350 + int(offset), self.spells)
        self.assertIn("kSpellsIronspine{ 212350, 212389 }", REWORK.read_text(encoding="utf-8"))

    def test_boss_bound(self):
        row = self.edits[IRONSPINE]
        self.assertEqual(row["ScriptName"], "boss_ironspine_rework")
        self.assertEqual(row["AIName"], "")
        self.assertEqual(row["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
        self.assertEqual(row["flags_extra"], INSTANCE_BIND)
        self.assertEqual(round(row["HealthModifier"] * WARRIOR_32_BASE), 36000)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_ironspine_rework", SCRIPT.read_text(encoding="utf-8"))

    def test_parts(self):
        cpp = SCRIPT.read_text(encoding="utf-8")
        displays = {FIST: _visual("DISPLAY_IRONSPINE_FIST"), RIBCAGE: _visual("DISPLAY_IRONSPINE_RIBCAGE"),
                    EYE: _visual("DISPLAY_IRONSPINE_EYE")}
        for entry in (FIST, RIBCAGE, EYE):
            row = self.creatures[entry]
            self.assertEqual(row["ScriptName"], "npc_sm_ironspine_part")
            self.assertIn(f"RegisterDungeonReworkCreatureAI({row['ScriptName']}", cpp)
            self.assertEqual((row["minlevel"], row["maxlevel"], row["unit_class"]), (32, 32, 1))
            self.assertEqual((row["faction"], row["type"]), (21, 6))
            self.assertEqual(round(row["HealthModifier"] * WARRIOR_32_BASE), 3000)
            self.assertEqual(row["DamageModifier"], 0.0)
            self.assertEqual(row["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
            self.assertEqual(row["lootid"], 0)
            self.assertEqual(self.models[entry]["CreatureDisplayID"], displays[entry])
        self.assertIn("Ironspine's Fist", self.creatures[FIST]["name"])
        self.assertIn("Ironspine's Eye", self.creatures[EYE]["name"])

    def test_pool_and_rungs(self):
        rot = self.spells[ROT]
        self.assertEqual(rot["school"], SCHOOL_NATURE)
        self.assertIn((ROT, RESOLVE), self.scripts)
        self.assertEqual(self.spells[ROT_CAST]["cast_time_ms"], 1500)
        self.assertEqual(_raw(self.spells[ROT_CAST], "InterruptFlags"), 0)
        rungs = _grave_rot_rungs()
        for radius, spell_id in ((7, LOOK_7), (8, LOOK_8), (9, LOOK_9), (10, LOOK_10)):
            look = self.spells[spell_id]
            self.assertEqual(_raw(look, "SpellVisualID_1"), rungs[radius])
            self.assertEqual(look["effect1"]["apply_aura"], AURA_DUMMY)
            self.assertEqual(look["duration_ms"], -1)
            # The header's rung table names the same spell for the radius.
            self.assertRegex(self.header, rf"\{{ {radius}\.f, SPELL_IR_GRAVE_ROT_LOOK_{radius} \}}")

    def test_fist(self):
        self.assertEqual(self.spells[FIST_SLAM]["school"], SCHOOL_PHYSICAL)
        self.assertIn((FIST_SLAM, RESOLVE), self.scripts)
        self.assertEqual(_raw(self.spells[FIST_LANDING], "SpellVisualID_1"), _visual("IR_FIST_LANDING"))

    def test_crush(self):
        crush = self.spells[CRUSH]
        self.assertEqual(crush["mechanic"], MECHANIC_ROOT)
        self.assertEqual(crush["effect1"]["apply_aura"], AURA_MOD_ROOT)
        self.assertEqual(crush["effect1"]["mechanic"], MECHANIC_ROOT)
        self.assertEqual(crush["dispel"], 0)
        self.assertEqual(crush["duration_ms"], 12000)
        self.assertEqual(_raw(crush, "AuraInterruptFlags") & CHANGE_MAP, CHANGE_MAP)
        self.assertEqual(_raw(crush, "SpellVisualID_1"), _visual("IR_CRUSH_HELD"))
        tick = self.spells[CRUSH_TICK]
        self.assertEqual(tick["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertEqual(tick["effect1"]["base_points"], 0)
        self.assertEqual(_raw(tick, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS, ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertEqual(self.custom.get(CRUSH_TICK, 0) & CU_IGNORE_ARMOR, CU_IGNORE_ARMOR)
        self.assertEqual(self.spells[CLOSED]["effect1"]["apply_aura"], AURA_DUMMY)

    def test_reassembled_and_heal(self):
        aura = self.spells[REASSEMBLED]
        self.assertEqual(aura["effect1"]["apply_aura"], AURA_MOD_DAMAGE_PERCENT_DONE)
        self.assertEqual(aura["effect1"]["base_points"], 10)
        self.assertEqual(aura["effect1"]["misc_value"], 127)
        # The aura's own cap must hold the header's "no cap" heroic (kReassembledAuraMax) and normal's 3.
        cap = int(re.search(r"kReassembledAuraMax = (\d+);", self.header).group(1))
        self.assertEqual(_raw(aura, "CumulativeAura"), cap)
        self.assertEqual(_raw(aura, "SpellVisualID_1"), _visual("IR_REASSEMBLED"))
        heal = self.spells[HEAL]
        self.assertEqual(heal["effect1"]["type"], HEAL_EFFECT)
        self.assertEqual(_raw(heal, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS, ATTR3_IGNORE_CASTER_MODIFIERS)

    def test_glare(self):
        self.assertEqual(self.spells[GLARE_CAST]["cast_time_ms"], 2000)
        self.assertEqual(_raw(self.spells[GLARE_CAST], "SpellVisualID_1"), _visual("IR_GLARE"))
        stun = self.spells[GLARE]
        self.assertEqual(stun["effect1"]["apply_aura"], AURA_MOD_STUN)
        self.assertEqual(stun["duration_ms"], 2000)
        self.assertEqual(self.spells[EYE_SIGHT]["duration_ms"], 2000)

    def test_no_wrong_visuals(self):
        for spell_id, spell in self.spells.items():
            self.assertNotIn(_raw(spell, "SpellVisualID_1"), WRONG_VISUALS, spell_id)


class IronspineSqlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.rework = REWORK.read_text(encoding="utf-8")

    def test_spawn_on_the_lawn(self):
        home = re.search(r"kIronspineHome\{ ([\d.]+)f, ([\d.]+)f, ([\d.]+)f \}", self.rework)
        self.assertIsNotNone(home)
        x, y, z = (float(v) for v in home.groups())
        move = re.search(r"UPDATE `creature` SET `position_x` = ([\d.]+), `position_y` = ([\d.]+), `position_z` = "
                         r"([\d.]+), `orientation` = [\d.]+\s+WHERE `guid` = 12164 AND `id` = 6489;", self.sql)
        self.assertIsNotNone(move)
        self.assertEqual(tuple(float(v) for v in move.groups()), (x, y, z))

    def test_texts(self):
        rows = re.findall(r"^\((\d+), (\d+), 0, '((?:[^']|'')*)', (\d+),", self.sql, re.MULTILINE)
        texts = {(int(c), int(g)): (t, int(ty)) for c, g, t, ty in rows}
        self.assertEqual(sorted(texts), [(6489, 0), (6489, 1), (6489, 2), (6489, 3), (300902, 0)])
        self.assertTrue(all(ty == 41 for _, ty in texts.values()))
        self.assertIn("$n", texts[(6489, 3)][0])
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 6489 AND `GroupID` BETWEEN 0 AND 3;", self.sql)

    def test_glare_and_ribcage_emote_to_the_map(self):
        # R-1-GY MN-2: a type 41 emote reaches 25 yd; the Glare hits to 40 yd and the cage lands 15-20 yd out, so both
        # go to the map (TextRange 3); the other three stay at the default.
        ranges = {(int(c), int(g)): int(r) for c, g, r in re.findall(
            r"^\((\d+), (\d+), 0, '(?:[^']|'')*', 41, 0, 100, 0, 0, 0, 0, (\d+),", self.sql, re.MULTILINE)}
        self.assertEqual(ranges, {(6489, 0): 0, (6489, 1): 0, (6489, 2): 0, (6489, 3): 3, (300902, 0): 3})


if __name__ == "__main__":
    unittest.main()
