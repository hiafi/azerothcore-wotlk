"""
Blackrock Depths build WP-D14, General Angerforge: source/npcs/blackrock_depths/angerforge.py against its C++
(modules/mod-dungeon-bosses src/BlackrockDepths/AngerforgeLogic.h, boss_general_angerforge_rework.cpp) and its SQL rev
(data/sql/updates/pending_db_world/rev_angerforge_blackrock_depths.sql).

Wave 2: the boss's own columns and the squad's ScriptNames sit behind BIND_WAVE_2 (_common.py), so this test checks the
declarations directly: the columns through the file's ANGERFORGE_COLUMNS, the gate in both positions through a copy of
the package with the switch written True. Nothing here needs the switch on.

Checks:
  - the spells sit in his slice (211300-211329) and AngerforgeLogic.h names the same ids;
  - he is bound once wave 2 is (SmartAI off, immunity 1972, INSTANCE_BIND), 150k at 5 players, DamageModifier 3.5, and
    declares nothing while the switch is off;
  - the squad: three entries with the models, levels, classes, health, scripts and WP-H's heroic lock lines;
  - Mighty Blow and Cleave (rule 15 copies on the kit's refflat script), the Commanding Aura pair, the Heal, the
    grenade's mark, own hit and resolve copy, the looks (self or point or unit visuals on V-2's ids);
  - the SQL rev: his four texts, the machine's template, the Reservist's rows (and no flee row).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_angerforge.py
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
HEADER = MODULE_DIR / "AngerforgeLogic.h"
REWORK = MODULE_DIR / "BlackrockDepthsRework.h"
SCRIPT = MODULE_DIR / "boss_general_angerforge_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_angerforge_blackrock_depths.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_depths"
VISUALS = PACKAGE / "_visuals.py"

SLICE = range(211300, 211330)
(MIGHTY_BLOW, CLEAVE, COMMANDING_AURA, COMMANDED, COMMANDING_SHOUT, HEAL, GRENADE_MARK, GRENADE_MARKED, GRENADE,
 GRENADE_LOOK, MOLE_DEPLOY_LOOK, MOLE_RETREAT_LOOK) = range(211300, 211312)
ANGERFORGE = 9033
OFFICER, RESERVIST, MEDIC = 300830, 300831, 300832
OFFICER_HEROIC, RESERVIST_HEROIC, MEDIC_HEROIC = 310407, 310408, 310409
WARRIOR_55_BASE, MAGE_55_BASE = 2614, 1830
HEALTH_AT_5 = 150_000
MOLE_MACHINE_GO = 301289

SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT, KNOCK_BACK, HEAL_PCT = 2, 6, 3, 98, 136
AURA_DUMMY, AURA_MOD_DAMAGE_PERCENT_TAKEN, AURA_MECHANIC_IMMUNITY = 4, 87, 77
SCHOOL_PHYSICAL, SCHOOL_HOLY, SCHOOL_FIRE = 1, 2, 4
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT = "spell_dungeon_refflat_damage"
IMMUNITY_BOSS_STUN = 1972
INSTANCE_BIND = 0x1


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
    match = re.search(rf"^{name}\s*=\s*(\w+)", text, re.MULTILINE)
    assert match, name
    value = match.group(1)
    return int(value) if value.isdigit() else _visual(value)


def _bound_package() -> tempfile.TemporaryDirectory:
    """A copy of this boss's file with the wave switch written True (the shared _common.py and _visuals.py beside
    it)."""
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name) / "blackrock_depths"
    root.mkdir()
    for name in ("_visuals.py", "angerforge.py"):
        shutil.copy(PACKAGE / name, root / name)
    common = (PACKAGE / "_common.py").read_text(encoding="utf-8")
    common = re.sub(r"^BIND_WAVE_2 = (True|False)$", "BIND_WAVE_2 = True", common, flags=re.M)
    (root / "_common.py").write_text(common, encoding="utf-8")
    return tmp


class AngerforgeDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) == ANGERFORGE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates
                         if int(e["entry"]) in (OFFICER, RESERVIST, MEDIC)}
        cls.models = {int(m["CreatureID"]): m for m in reg.creature_template_models
                      if int(m["CreatureID"]) in (OFFICER, RESERVIST, MEDIC)}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    # --- ids ---------------------------------------------------------------------------------------------------------

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(MIGHTY_BLOW, MOLE_RETREAT_LOOK + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"spell": mine}), [])
        first = re.search(r"kSpellsAngerforge\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(first)
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_AF_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))

    def test_the_squad_and_the_machine_ids_are_the_headers(self):
        text = REWORK.read_text(encoding="utf-8")
        for name, entry in (("NPC_BRD_SQUAD_OFFICER", OFFICER), ("NPC_BRD_SQUAD_RESERVIST", RESERVIST),
                            ("NPC_BRD_SQUAD_MEDIC", MEDIC), ("GO_BRD_MOLE_MACHINE", MOLE_MACHINE_GO)):
            self.assertRegex(text, rf"\b{name}\s*=\s*{entry},")
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"creature": [OFFICER, RESERVIST, MEDIC]}),
                         [])

    # --- the boss ----------------------------------------------------------------------------------------------------

    def test_he_declares_nothing_while_wave_2_is_off(self):
        common = (PACKAGE / "_common.py").read_text(encoding="utf-8")
        gate = re.search(r"^BIND_WAVE_2 = (True|False)$", common, re.M).group(1) == "True"
        self.assertEqual(ANGERFORGE in self.edits, gate)

    def test_he_is_bound_once_wave_2_is(self):
        with _bound_package() as tmp:
            reg = _load(Path(tmp) / "blackrock_depths")
        boss = {int(e["entry"]): e for e in reg.creature_template_edits}[ANGERFORGE]
        self.assertEqual(boss["ScriptName"], "boss_general_angerforge_rework")
        self.assertEqual(boss["AIName"], "")
        self.assertEqual(boss["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
        self.assertEqual(boss["flags_extra"] & INSTANCE_BIND, INSTANCE_BIND)
        self.assertLessEqual(abs(math.ceil(WARRIOR_55_BASE * boss["HealthModifier"]) - HEALTH_AT_5), 2)
        self.assertAlmostEqual(float(boss["DamageModifier"]), 3.5)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_general_angerforge_rework,", self.cpp)
        # the C++ registers every script the squad's rows name, and only inside the wave switch
        for script in ("boss_general_angerforge_rework", "npc_brd_squad_officer", "npc_brd_squad_medic"):
            self.assertRegex(self.cpp, rf"if \(kWave2Bound\)\s*RegisterDungeonReworkCreatureAI\({script},")

    # --- the squad ---------------------------------------------------------------------------------------------------

    def test_the_squad_entries(self):
        officer, reservist, medic = (self.creatures[e] for e in (OFFICER, RESERVIST, MEDIC))
        for entry, row, name in ((OFFICER, officer, "Anvilrage Squad Officer"),
                                 (RESERVIST, reservist, "Anvilrage Squad Reservist"),
                                 (MEDIC, medic, "Anvilrage Squad Medic")):
            self.assertEqual(row["name"], name)
            self.assertEqual((int(row["minlevel"]), int(row["maxlevel"])), (55, 55), entry)
            self.assertEqual(int(row["faction"]), 54, entry)
            self.assertEqual(int(row["type"]), 7, entry)                    # humanoid
            self.assertEqual(int(row["lootid"]), 0, entry)
            self.assertTrue(int(row["flags_extra"]) & 0x40, entry)           # no XP
            self.assertEqual(int(row["CreatureImmunitiesId"]), 0, entry)
            self.assertEqual(int(row["MovementType"]), 0, entry)
        self.assertEqual([int(r["unit_class"]) for r in (officer, reservist, medic)], [1, 1, 8])
        self.assertEqual([int(r["rank"]) for r in (officer, reservist, medic)], [1, 0, 1])
        # health at 5 players: the build spec's 10,000 / 3,000 / 5,000 (the header's kOfficerHealth ...)
        for row, base, name in ((officer, WARRIOR_55_BASE, "kOfficerHealth"), (reservist, WARRIOR_55_BASE,
                                                                               "kReservistHealth"),
                                (medic, MAGE_55_BASE, "kMedicHealth")):
            normal, heroic = _header_nh(name)
            self.assertEqual(math.ceil(base * float(row["HealthModifier"])), int(normal))
            self.assertGreater(heroic, normal)
        self.assertEqual([int(_header_nh(n)[0]) for n in ("kOfficerHealth", "kReservistHealth", "kMedicHealth")],
                         [10_000, 3_000, 5_000])
        # WP-H's heroic lock lines (STAGE-H-REPORT s3)
        self.assertEqual([int(r["difficulty_entry_1"]) for r in (officer, reservist, medic)],
                         [OFFICER_HEROIC, RESERVIST_HEROIC, MEDIC_HEROIC])
        self.assertEqual([int(_header_nh(n)[1]) for n in ("kOfficerHealth", "kReservistHealth", "kMedicHealth")],
                         [15_000, 4_500, 7_500])

    def test_the_squads_scripts(self):
        # the Officer and the Medic run C++, the Reservist the stock kit's SmartAI (the rev's rows); the ScriptNames are
        # held back by the wave switch (an unbound name logs "not assigned" at boot)
        officer, reservist, medic = (self.creatures[e] for e in (OFFICER, RESERVIST, MEDIC))
        self.assertEqual(reservist["AIName"], "SmartAI")
        self.assertEqual(reservist["ScriptName"], "")
        self.assertEqual(officer["AIName"], "")
        self.assertEqual(medic["AIName"], "")
        with _bound_package() as tmp:
            bound = {int(e["entry"]): e for e in _load(Path(tmp) / "blackrock_depths").creature_templates
                     if int(e["entry"]) in (OFFICER, RESERVIST, MEDIC)}
        self.assertEqual(bound[OFFICER]["ScriptName"], "npc_brd_squad_officer")
        self.assertEqual(bound[MEDIC]["ScriptName"], "npc_brd_squad_medic")
        self.assertEqual(bound[RESERVIST]["ScriptName"], "")
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_brd_squad_officer,", self.cpp)
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_brd_squad_medic,", self.cpp)
        # this tree's own declaration follows the switch: the C++ names once wave 2 binds, nothing before
        gate = re.search(r"^BIND_WAVE_2 = (True|False)$", (PACKAGE / "_common.py").read_text(encoding="utf-8"),
                         re.M).group(1) == "True"
        self.assertEqual([c["ScriptName"] for c in (officer, medic)],
                         ["npc_brd_squad_officer", "npc_brd_squad_medic"] if gate else ["", ""])

    def test_the_squads_looks(self):
        self.assertEqual({e: int(m["CreatureDisplayID"]) for e, m in self.models.items()},
                         {OFFICER: _visual("DISPLAY_SQUAD_OFFICER"), RESERVIST: _visual("DISPLAY_SQUAD_RESERVIST"),
                          MEDIC: _visual("DISPLAY_SQUAD_MEDIC")})
        self.assertAlmostEqual(float(self.models[RESERVIST]["DisplayScale"]), 0.9)

    # --- AF1, AF2 ----------------------------------------------------------------------------------------------------

    def test_mighty_blow_is_a_refflat_copy_with_the_stock_knockback(self):
        spell = self.spells[MIGHTY_BLOW]
        normal, heroic = _header_nh("kMightyBlowPct")
        hit, knock = spell["effect1"], spell["effect2"]
        self.assertEqual(hit["type"], SCHOOL_DAMAGE)
        self.assertEqual(hit["base_points"] + hit["die_sides"], round(normal * 100))
        self.assertEqual(_raw(spell, "EffectMiscValueB_1"), round(heroic * 100))
        self.assertEqual((knock["type"], knock["base_points"], knock["die_sides"], knock["misc_value"]),
                         (KNOCK_BACK, 74, 51, 100))          # the stock 14099 second effect
        self.assertEqual(spell["school"], SCHOOL_PHYSICAL)
        self.assertEqual(spell["cast_time_ms"], 0)
        self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertIn((MIGHTY_BLOW, REFFLAT), self.scripts)
        self.assertIn("SPELL_AF_MIGHTY_BLOW", self.cpp)

    def test_cleave_is_a_frontal_arc_on_five(self):
        spell = self.spells[CLEAVE]
        normal, heroic = _header_nh("kCleavePct")
        hit = spell["effect1"]
        self.assertEqual(hit["type"], SCHOOL_DAMAGE)
        self.assertEqual(hit["implicit_target_a"], 104)             # TARGET_UNIT_CONE_ENEMY_104
        self.assertEqual(hit["base_points"] + hit["die_sides"], round(normal * 100))
        self.assertEqual(_raw(spell, "EffectMiscValueB_1"), round(heroic * 100))
        self.assertEqual(_raw(spell, "MaxTargets"), int(_header_value("kCleaveMaxTargets")))
        self.assertEqual(_raw(spell, "MaxTargets"), 5)
        self.assertIn((CLEAVE, REFFLAT), self.scripts)
        self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)

    # --- AF4 ---------------------------------------------------------------------------------------------------------

    def test_the_commanding_aura_pair(self):
        aura = self.spells[COMMANDING_AURA]
        self.assertEqual(aura["duration_ms"], -1)                    # lasts until the Officer dies
        self.assertEqual(aura["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(aura["dispel"], 0)
        shield = self.spells[COMMANDED]
        self.assertEqual(shield["duration_ms"], int(_header_value("kCommandedMs")))
        damage, interrupt, silence = shield["effect1"], shield["effect2"], shield["effect3"]
        self.assertEqual((damage["apply_aura"], damage["base_points"]),
                         (AURA_MOD_DAMAGE_PERCENT_TAKEN, int(_header_value("kCommandedDamageTakenPct"))))
        self.assertEqual(damage["misc_value"], 127)                  # every school
        # no kick (the interrupt mechanic 26) and no silence (9): "their casts cannot be interrupted"
        self.assertEqual((interrupt["apply_aura"], interrupt["misc_value"]), (AURA_MECHANIC_IMMUNITY, 26))
        self.assertEqual((silence["apply_aura"], silence["misc_value"]), (AURA_MECHANIC_IMMUNITY, 9))
        self.assertEqual(shield["dispel"], 0)                        # a shield, not a dispellable buff
        self.assertGreater(shield["duration_ms"], int(_header_value("kCommandingPulseMs")))
        self.assertEqual(int(_header_value("kCommandingRadiusYd")), 15)
        # the descriptor: no interrupt entry on a shielded Medic, and a hold keeps kicks off any shielded unit
        self.assertIn("BossMechanics::Condition::Not(BossMechanics::Condition::HasAura(SPELL_AF_COMMANDED))", self.cpp)
        self.assertIn("BossMechanics::HoldEntry::Interrupts(0, SPELL_AF_COMMANDED)", self.cpp)

    def test_the_shout_is_a_self_visual_on_v2s_id(self):
        look = self.spells[COMMANDING_SHOUT]
        self.assertEqual(look["effect1"]["type"], DUMMY_EFFECT)
        self.assertEqual(_raw(look, "SpellVisualID_1"), _visual("AF_COMMANDING_SHOUT"))
        self.assertEqual(_visual("AF_COMMANDING_SHOUT"), 6506)

    # --- AF5 ---------------------------------------------------------------------------------------------------------

    def test_the_heal_is_a_three_second_kick(self):
        heal = self.spells[HEAL]
        self.assertEqual(heal["cast_time_ms"], int(_header_value("kHealCastMs")))
        self.assertEqual(_raw(heal, "CastingTimeIndex"), 0)          # the DSL maps 3,000 ms (index 22 is 3.5 s)
        self.assertEqual(heal["school"], SCHOOL_HOLY)
        self.assertEqual(heal["effect1"]["type"], HEAL_PCT)
        self.assertEqual(heal["effect1"]["base_points"], int(_header_value("kHealPctOfBoss")))
        self.assertEqual(heal["effect1"]["implicit_target_a"], 21)   # an ally
        self.assertEqual(_raw(heal, "InterruptFlags"), 15)
        self.assertEqual(_raw(heal, "PreventionType"), 1)
        self.assertEqual(_raw(heal, "SpellVisualID_1"), _visual("AF_MEDIC_HEAL"))
        self.assertEqual(_visual("AF_MEDIC_HEAL"), 135)
        self.assertIn("d.interrupts.emplace_back(NPC_BRD_SQUAD_MEDIC, SPELL_AF_HEAL", self.cpp)
        self.assertIn("SPELL_STOCK_MIND_BLAST", self.cpp)
        self.assertEqual(int(_header_value("SPELL_STOCK_MIND_BLAST")), 15587)
        # R-2-A MI-1: the Medic walks back to him before he leaves the heal's range (the header's leash).
        self.assertEqual(heal["range_yards"], _header_value("kMedicHealRangeYd"))
        self.assertLess(_header_value("kMedicLeashYd"), heal["range_yards"])
        self.assertIn("KeepHealRange();", self.cpp)
        self.assertIn("MoveChase(boss, kMedicRangeYd)", self.cpp)

    def test_the_grenade_never_marks_the_tank(self):
        # Orchestrator default 2026-11-17 (R-2-A designer question 1): an 8 yd Spread on the tank pushes the melee off.
        self.assertRegex(_header(), r"kGrenadeMarksTank = false;")
        self.assertIn("DungeonKit::PickPlayers(me, GrenadePickRule(), kGrenadeCount(_heroic))", self.cpp)
        self.assertNotIn("rule.nonTank = false", self.cpp)

    # --- AF6 ---------------------------------------------------------------------------------------------------------

    def test_the_grenade(self):
        mark = self.spells[GRENADE_MARK]
        self.assertEqual(mark["duration_ms"], int(_header_value("kGrenadeWarnMs")))
        self.assertEqual(mark["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(_raw(mark, "SpellVisualID_1"), _visual("AF_GRENADE_MARK"))
        marked = self.spells[GRENADE_MARKED]
        normal, heroic = _header_nh("kGrenadeMarkedPct")
        self.assertEqual(marked["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertEqual(marked["effect1"]["base_points"] + marked["effect1"]["die_sides"], round(normal * 100))
        self.assertEqual(_raw(marked, "EffectMiscValueB_1"), round(heroic * 100))
        self.assertEqual(marked["school"], SCHOOL_FIRE)
        self.assertIn((GRENADE_MARKED, REFFLAT), self.scripts)
        self.assertTrue(_raw(marked, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        others = self.spells[GRENADE]
        self.assertEqual(others["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertIn((GRENADE, RESOLVE), self.scripts)
        self.assertEqual(others["school"], SCHOOL_FIRE)
        self.assertIn(".Spell(SPELL_AF_GRENADE).Tag(TAG_AF_GRENADE)", self.cpp)
        self.assertIn("Mechanic::Spread(me, kGrenadeRadius, Ms(kGrenadeWarnMs))", self.cpp)
        self.assertIn(".Weakened()", self.cpp)
        self.assertEqual(int(_header_value("kGrenadeRadius")), 8)
        # the others' percent is the registry's: the header's, both rows, normal and heroic
        self.assertEqual(_header_nh("kGrenadeOthersPct"), (25.0, 40.0))
        self.assertEqual(_header_nh("kGrenadeMarkedPct"), (15.0, 25.0))
        # the bomb: a unit-targeted look on V-2's Iron Grenade pick
        look = self.spells[GRENADE_LOOK]
        self.assertEqual(look["effect1"]["type"], DUMMY_EFFECT)
        self.assertEqual(_raw(look, "SpellVisualID_1"), _visual("AF_IRON_GRENADE"))

    def test_the_machines_looks_are_point_visuals(self):
        for spell_id, name in ((MOLE_DEPLOY_LOOK, "AF_MOLE_DEPLOY"), (MOLE_RETREAT_LOOK, "AF_MOLE_RETREAT")):
            look = self.spells[spell_id]
            self.assertEqual(look["effect1"]["type"], DUMMY_EFFECT, spell_id)
            self.assertEqual(look["effect1"]["implicit_target_a"], 87, spell_id)   # a destination
            self.assertEqual(_raw(look, "Targets"), 0x40, spell_id)
            self.assertEqual(_raw(look, "SpellVisualID_1"), _visual(name), spell_id)

    def test_nothing_wires_a_wrong_look(self):
        # Living Bomb 20475 (SV 11840) is a fire whirl: V-1 forbids it for the grenade
        for spell in self.spells.values():
            self.assertNotEqual(_raw(spell, "SpellVisualID_1"), 11840, spell["id"])

    # --- the SQL rev -------------------------------------------------------------------------------------------------

    def test_the_sql_rev(self):
        sql = SQL.read_text(encoding="utf-8")
        # texts 0-3: yells, the grenade a boss emote with the target's name
        for group in (0, 1, 3):
            self.assertRegex(sql, rf"\({ANGERFORGE}, {group}, 0, '[^\n]*', 14,")
        self.assertRegex(sql, rf"\({ANGERFORGE}, 2, 0, '%s lobs a Fireburst Grenade at \$n!', 41,")
        self.assertIn("'Intruders in the Shadowforge! To arms!'", sql)
        self.assertIn("'Reinforcements, up from below!'", sql)
        self.assertIn("'The Emperor... will avenge...'", sql)
        # the machine: a generic (type 5) object on the Dark Iron Mole Machine display at 0.6, not selectable
        size = re.search(r"^MOLE_MACHINE_SIZE\s*=\s*([\d.]+)", VISUALS.read_text(encoding="utf-8"), re.M).group(1)
        self.assertEqual(size, "0.6")
        self.assertRegex(sql, rf"\({MOLE_MACHINE_GO}, 5, {_visual('GODI_MOLE_MACHINE')}, 'Mole Machine', '', '', '', "
                              rf"{re.escape(size)},")
        self.assertRegex(sql, rf"\({MOLE_MACHINE_GO}, 0, 16, 0, 0, 0, 0, 0, 0\)")
        # the Reservist's rows: the stock 8901 kit (rows 0-3), the heroic bit set, no flee row
        rows = re.findall(r"^\(300831, 0, (\d+), 0, (\d+), 0, 100, (\d+), [^\n]*?, 0, 0, 11, (\d+), ", sql, re.M)
        self.assertEqual([int(r[0]) for r in rows], [0, 1, 2, 3])
        self.assertEqual([int(r[3]) for r in rows], [9128, 6660, 9080, 11976])  # Battle Shout, Shoot, Hamstring, Strike
        self.assertEqual([int(r[2]) for r in rows], [7, 6, 6, 6])                # normal (2) + heroic (4), + no repeat
        for flags in (int(r[2]) for r in rows):
            self.assertTrue(flags & 2 and flags & 4)
        self.assertEqual(sql.count("Flee"), 1)                                   # only the comment naming the cut row
        # nothing here drops a stock row, inserts a spawn or touches the stock trash
        self.assertNotIn("DELETE FROM `smart_scripts` WHERE `entryorguid` = 8", sql)
        self.assertNotIn("INSERT INTO `creature` ", sql)
        self.assertNotIn("`creature_template`", sql)


if __name__ == "__main__":
    unittest.main()
