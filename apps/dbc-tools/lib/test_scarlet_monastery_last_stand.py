"""
Scarlet Monastery build WP-D13, the Last Stand: source/npcs/scarlet_monastery/last_stand.py against its C++
(modules/mod-dungeon-bosses src/ScarletMonastery/LastStandLogic.h, boss_mograine_rework.cpp, MograineFight.h) and its
SQL rev.

Checks:
  - the spells sit in the slice (213100-213149) and LastStandLogic.h names the same ids;
  - Mograine 3976 is bound only behind BIND_WAVE_2 (55k on the level 40 paladin base, stun immune, no INSTANCE_BIND,
    the stock 2.6), his AI registers only behind kWave2Bound, the companies' script on every wave;
  - the six companies: level 40 elites, their classes and the build spec's 4k / 3k, V's displays, one script, no loot,
    their heroic entries from WP-H's mint table;
  - the numbers the build spec sets (the hits, the casts, the fire, the stun, Devotion, the heals) match the header;
  - every interruptible cast is Fire or Holy and every bar Mograine must play is Physical (rule 5); every damage spell
    ignores caster modifiers (rule 2) and the refflat ones carry their heroic hundredths;
  - the looks are V's ids and never a WRONG-listed one (Hammer of Justice's SV 322 only as the stun swirl);
  - the C++ registers what the build spec names (the tank in every hit, TankExempt + the tank's own storm hit, the
    Spread for the Hammer, the persistent zones, the detonate / cancel of Purifying Flame, the 1% floor, the chest);
  - the SQL rev deletes exactly the 42 nave spawns, their addons and the four nave path scripts, writes the five yells,
    the two chest templates (their loot is L-2's rev), and touches nothing else (no spawn, no SmartAI insert).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scarlet_monastery_last_stand.py
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
HEADER = MODULE_DIR / "LastStandLogic.h"
REWORK = MODULE_DIR / "ScarletMonasteryRework.h"
SCRIPT = MODULE_DIR / "boss_mograine_rework.cpp"
FIGHT = MODULE_DIR / "MograineFight.h"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_last_stand_scarlet_monastery.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "scarlet_monastery"
VISUALS = PACKAGE / "_visuals.py"
COMMON = PACKAGE / "_common.py"

SLICE = range(213100, 213150)
(HAMMER_THROW, HAMMER_HIT, HAMMER_STRIKE, HAMMER_STUN, STORM_CAST, STORM_HIT, STORM_TANK, DEVOTION, DEVOTION_PULSE,
 CONSECRATION_HIT, CONSECRATION_GROUND, FIREBALL, FLAME_CAST, FLAME_HIT, FLAME_FIRE, FLAME_POOL, FLAME_POOL_H,
 GREATER_HEAL, GREATER_HEAL_H, GREATER_HEAL_PULSE, CHARGE_HIT, CHARGE_LOOK) = range(213100, 213122)
MOGRAINE = 3976
CHAMPION, CAPTAIN, CHAPLAIN, MONK, WIZARD, ABBOT = range(300950, 300956)
COMPANIES = (CHAMPION, CAPTAIN, CHAPLAIN, MONK, WIZARD, ABBOT)
# creature_classlevelstats basehp0 at level 40 (live 2026-11-20)
BASE_40 = {1: 1524, 2: 1226, 8: 1077}
# WP-H's mint table (STAGE-H-REPORT section 3)
HEROIC = {CHAMPION: 310481, CAPTAIN: 310482, CHAPLAIN: 310483, MONK: 310484, WIZARD: 310485, ABBOT: 310486}

SCHOOL_PHYSICAL, SCHOOL_HOLY, SCHOOL_FIRE = 1, 2, 4
SCHOOL_DAMAGE, DUMMY_EFFECT, APPLY_AURA, PERSISTENT_AREA_AURA, HEAL_PCT = 2, 3, 6, 27, 136
AURA_MOD_STUN, AURA_MOD_DAMAGE_PERCENT_TAKEN = 12, 87
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT_DAMAGE = "spell_dungeon_refflat_damage"
NAVE_GUIDS = (
    40000, 40001, 40003, 40004, 40005, 40006, 40007, 40008, 40009, 40010, 40011, 40012, 40013, 40014,
    40015, 40016, 40017, 40018, 40019, 40020, 40021, 40022, 40023, 40024, 40025, 40026, 40027, 40028,
    40030, 40031, 40032, 40033, 40034, 40035, 40036, 40037, 40038, 40040, 40041, 40042, 40043, 40044,
)
KEPT_GUIDS = (40029, 40039)                                     # Mograine, Fairbanks
GARDEN_PATH_GUIDS = (39959, 39967, 39978, 39980, 39998)         # the five guid path scripts that stay
# Looks V marks WRONG for this fight: Hammer of Justice's SV 322 as a thrown hammer (it is only the stun swirl here).
WRONG_THROWN_HAMMER = 322


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
    match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f?;", _header())
    assert match, name
    return float(match.group(1))


def _nh_values(name: str) -> tuple[float, float]:
    match = re.search(rf"\b{name}\{{\s*(-?[\d.]+)f?,\s*(-?[\d.]+)f?\s*\}}", _header())
    assert match, name
    return float(match.group(1)), float(match.group(2))


def _visual(name: str) -> int:
    text = VISUALS.read_text(encoding="utf-8")
    match = re.search(rf"^{name}\s*=\s*(\w+)(\[(\d+)\])?", text, re.MULTILINE)
    assert match, name
    value = match.group(1)
    if match.group(2):
        rungs = re.search(rf"^{value}\s*=\s*\{{([^}}]*)\}}", text, re.MULTILINE)
        assert rungs, value
        table = {int(k): int(v) for k, v in re.findall(r"(\d+):\s*(\d+)", rungs.group(1))}
        return table[int(match.group(3))]
    return int(value) if value.isdigit() else _visual(value)


def _code(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith(("//", "*", "/*")))


def _wave2_bound() -> bool:
    found = re.findall(r"^BIND_WAVE_2\s*=\s*(True|False)\s*$", COMMON.read_text(encoding="utf-8"), re.M)
    assert len(found) == 1
    return found[0] == "True"


class LastStandDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) == MOGRAINE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) in COMPANIES}
        cls.models = {}
        for e in reg.creature_template_models:
            if int(e["CreatureID"]) in COMPANIES:
                cls.models.setdefault(int(e["CreatureID"]), []).append(e)
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.code = _code(cls.cpp)

    # ---- ids --------------------------------------------------------------------------------------------------------

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(HAMMER_THROW, CHARGE_LOOK + 1)))
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery", {"spell": mine}), [])
        first = re.search(r"kSpellsLastStand\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(first)
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_LS_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))
        # The retired stock Hammer of Justice (a live player override) is never cast here.
        self.assertNotIn("5589", self.code)

    # ---- Mograine ---------------------------------------------------------------------------------------------------

    def test_mograine_is_bound_only_with_wave_2(self):
        self.assertIn("if (kWave2Bound)\n        RegisterDungeonReworkCreatureAI(boss_mograine_rework,", self.cpp)
        if not _wave2_bound():
            self.assertNotIn(MOGRAINE, self.edits, "a wave 2 boss stays stock until W2-SETUP")
            return
        boss = self.edits[MOGRAINE]
        self.assertEqual(boss["ScriptName"], "boss_mograine_rework")
        self.assertEqual(boss["AIName"], "")
        self.assertLessEqual(abs(math.ceil(BASE_40[2] * boss["HealthModifier"]) - 55000), 2)
        self.assertEqual(boss["DamageModifier"], 2.6)
        self.assertEqual(boss["CreatureImmunitiesId"], 1972)
        self.assertEqual(boss["flags_extra"], 0)        # no INSTANCE_BIND: the Last Stand credits by spell 212301

    def test_the_mograine_column_line_is_the_s0_one(self):
        text = (PACKAGE / "last_stand.py").read_text(encoding="utf-8")
        self.assertIn("if BIND_WAVE_2:\n    creature_template_columns(3976, **boss_columns(\n"
                      "        'boss_mograine_rework', 44.861, damage_modifier=2.6, instance_bind=False,", text)
        self.assertEqual(int(_nh_values("kMograineHealth")[0]), 55000)
        self.assertLessEqual(abs(math.ceil(BASE_40[2] * 44.861) - 55000), 2)

    # ---- the companies ----------------------------------------------------------------------------------------------

    def test_the_companies(self):
        self.assertEqual(sorted(self.creatures), list(COMPANIES))
        expected = {
            CHAMPION: ("Chapel Guard Champion", 2, 4000),
            CAPTAIN: ("Captain of the Guard", 2, 4000),
            CHAPLAIN: ("Company Chaplain", 2, 3000),
            MONK: ("Company Monk", 1, 4000),
            WIZARD: ("Company Wizard", 8, 3000),
            ABBOT: ("Company Abbot", 2, 4000),
        }
        for entry, (name, unit_class, health) in expected.items():
            with self.subTest(entry=entry):
                row = self.creatures[entry]
                self.assertEqual(row["name"], name)
                self.assertEqual(row["ScriptName"], "npc_sm_last_stand_company")
                self.assertEqual(row["AIName"], "")
                self.assertEqual((int(row["minlevel"]), int(row["maxlevel"])), (40, 40))
                self.assertEqual(int(row["rank"]), 1)                      # elite
                self.assertEqual(int(row["unit_class"]), unit_class)
                self.assertEqual(math.ceil(BASE_40[unit_class] * float(row["HealthModifier"])), health)
                self.assertEqual(int(row["faction"]), 67)                  # the Scarlet Crusade
                self.assertEqual(int(row["type"]), 7)                      # humanoid
                self.assertEqual(int(row["lootid"]), 0)                    # the chest is the reward
                self.assertEqual(int(row["CreatureImmunitiesId"]), 0)      # the trash: stuns and kicks work
                self.assertFalse(int(row["flags_extra"]) & 0x1)            # never INSTANCE_BIND
                # WP-H's mint table once F-1a wires it (unset until every lower-numbered kit unit has landed).
                self.assertIn(int(row.get("difficulty_entry_1") or 0), (0, HEROIC[entry]))
                self.assertLessEqual(float(row["DamageModifier"]), 2.0)    # rule 19: sized against the tank row
                self.assertIn(entry, self.models)
        # The build spec's health table (normal) is the header's.
        self.assertEqual(_nh_values("kBigMemberHealth"), (4000.0, 15000.0))
        self.assertEqual(_nh_values("kSmallMemberHealth"), (3000.0, 12000.0))
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery", {"creature": list(COMPANIES)}), [])
        # One script for the six, registered on every wave (the templates name it on every wave).
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_sm_last_stand_company,", self.cpp)
        self.assertNotIn("if (kWave2Bound)\n        RegisterDungeonReworkCreatureAI(npc_sm_last_stand_company",
                         self.cpp)
        self.assertIn('SmTest::RegisterBoss("laststand"', self.cpp)

    def test_the_company_looks_are_vs(self):
        displays = {e: sorted(int(m["CreatureDisplayID"]) for m in rows) for e, rows in self.models.items()}
        self.assertEqual(displays[CHAMPION], sorted([_visual("DISPLAY_CAPTAIN"), _visual("DISPLAY_CAPTAIN_ALT")]))
        self.assertEqual(displays[CAPTAIN], sorted([_visual("DISPLAY_CAPTAIN"), _visual("DISPLAY_CAPTAIN_ALT")]))
        self.assertEqual(displays[CHAPLAIN], sorted([_visual("DISPLAY_COMPANY_CHAPLAIN"),
                                                     _visual("DISPLAY_COMPANY_CHAPLAIN_ALT")]))
        self.assertEqual(displays[MONK], sorted([_visual("DISPLAY_COMPANY_MONK"), _visual("DISPLAY_COMPANY_MONK_ALT")]))
        self.assertEqual(displays[WIZARD], sorted([_visual("DISPLAY_COMPANY_WIZARD"),
                                                   _visual("DISPLAY_COMPANY_WIZARD_ALT")]))
        self.assertEqual(displays[ABBOT], [_visual("DISPLAY_COMPANY_ABBOT")])
        # The Captain's sword and shield are V's items (the script equips them).
        self.assertIn(f"kItemCaptainSword = {_visual('ITEM_CAPTAIN_SWORD')};", _header())
        self.assertIn(f"kItemCaptainShield = {_visual('ITEM_CAPTAIN_SHIELD')};", _header())
        self.assertIn("me->SetVirtualItem(0, e.mainHand);", self.code)

    # ---- the spells -------------------------------------------------------------------------------------------------

    def _refflat(self, spell_id: int, nh_name: str, school: int):
        spell = self.spells[spell_id]
        normal, heroic = _nh_values(nh_name)
        effect = spell["effect1"]
        self.assertEqual(effect["type"], SCHOOL_DAMAGE)
        self.assertEqual(effect["base_points"] + effect["die_sides"], round(normal * 100))
        self.assertEqual(_raw(spell, "EffectMiscValueB_1"), round(heroic * 100))
        self.assertTrue(int(_raw(spell, "AttributesEx3")) & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertIn((spell_id, REFFLAT_DAMAGE), self.scripts)
        self.assertEqual(spell["school"], school)

    def test_refflat_hits(self):
        self._refflat(HAMMER_STRIKE, "kHammerPct", SCHOOL_HOLY)
        self._refflat(STORM_TANK, "kStormTankPct", SCHOOL_PHYSICAL)
        self._refflat(FIREBALL, "kFireballPct", SCHOOL_FIRE)

    def test_resolve_copies(self):
        for spell_id, school in ((HAMMER_HIT, SCHOOL_HOLY), (STORM_HIT, SCHOOL_PHYSICAL),
                                 (CONSECRATION_HIT, SCHOOL_HOLY), (FLAME_HIT, SCHOOL_FIRE), (FLAME_FIRE, SCHOOL_FIRE),
                                 (CHARGE_HIT, SCHOOL_PHYSICAL)):
            with self.subTest(spell=spell_id):
                spell = self.spells[spell_id]
                self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE)
                self.assertIn((spell_id, RESOLVE), self.scripts)
                self.assertEqual(spell["school"], school)
                self.assertTrue(int(_raw(spell, "AttributesEx3")) & ATTR3_IGNORE_CASTER_MODIFIERS)

    def test_rule_5_the_schools_of_the_bars(self):
        # Every interruptible cast is Fire or Holy; Mograine's must-play bar is Physical, which none of them uses.
        kicks = (FIREBALL, FLAME_CAST, GREATER_HEAL, GREATER_HEAL_H)
        for spell_id in kicks:
            with self.subTest(spell=spell_id):
                spell = self.spells[spell_id]
                self.assertEqual(_raw(spell, "InterruptFlags"), 15)
                self.assertEqual(_raw(spell, "PreventionType"), 1)
                self.assertIn(spell["school"], (SCHOOL_FIRE, SCHOOL_HOLY))
        bar = self.spells[STORM_CAST]
        self.assertEqual(_raw(bar, "InterruptFlags"), 0)
        self.assertEqual(bar["school"], SCHOOL_PHYSICAL)
        self.assertNotIn(bar["school"], {self.spells[s]["school"] for s in kicks})
        self.assertEqual(bar["cast_time_ms"], int(_header_value("kStormCastMs")))
        self.assertEqual(self.spells[FIREBALL]["cast_time_ms"], int(_header_value("kFireballCastMs")))
        self.assertEqual(self.spells[FLAME_CAST]["cast_time_ms"], int(_header_value("kFlameCastMs")))
        self.assertEqual(self.spells[GREATER_HEAL]["cast_time_ms"], int(_header_value("kGreaterHealCastMs")))
        self.assertEqual(self.spells[GREATER_HEAL_H]["cast_time_ms"], int(_header_value("kGreaterHealCastMs")))

    def test_the_hammer(self):
        stun = self.spells[HAMMER_STUN]
        self.assertEqual(stun["duration_ms"], int(_header_value("kHammerStunMs")))
        self.assertLessEqual(stun["duration_ms"], 2000)            # the loss-of-control limit
        self.assertEqual(stun["effect1"]["apply_aura"], AURA_MOD_STUN)
        self.assertEqual(stun["mechanic"], 12)
        self.assertEqual(_raw(stun, "SpellVisualID_1"), _visual("LS_HAMMER_STUN"))
        throw = self.spells[HAMMER_THROW]
        self.assertEqual(_raw(throw, "SpellVisualID_1"), _visual("LS_HAMMER"))
        self.assertNotEqual(_raw(throw, "SpellVisualID_1"), WRONG_THROWN_HAMMER)
        self.assertEqual(float(_raw(throw, "Speed")), _header_value("kHammerMissileSpeed"))
        self.assertEqual(throw["effect1"]["type"], DUMMY_EFFECT)
        # The Spread on the marked players: the others caught take the hit, Weakened and the stun; the marked player
        # its own hit and the stun (the registry skips a Spread's carrier).
        self.assertIn("Mechanic::Spread(me, kHammerRadiusYd, Ms(kHammerWarnMs))", self.code)
        self.assertIn("spread.Targets(carriers).Damage(pct).TankDamage(pct).Weakened().Spell(SPELL_LS_HAMMER_HIT)\n"
                      "            .Rider(SPELL_LS_HAMMER_STUN)", self.code)
        self.assertIn("me->CastSpell(t, SPELL_LS_HAMMER_STRIKE, true);", self.code)
        self.assertIn("me->CastSpell(t, SPELL_LS_HAMMER_STUN, true);", self.code)
        self.assertEqual(_nh_values("kHammerTargets"), (1.0, 2.0))
        self.assertIn("rule.nonTank = false;", self.code)                  # the tank too

    def test_divine_storm(self):
        self.assertEqual(_raw(self.spells[STORM_CAST], "SpellVisualID_1"), _visual("LS_DIVINE_STORM"))
        self.assertIn("storm.TankExempt().Damage(pct).Weakened().Spell(SPELL_LS_DIVINE_STORM_HIT)", self.code)
        self.assertIn("me->CastSpell(tank, SPELL_LS_DIVINE_STORM_TANK, true);", self.code)
        self.assertEqual(_nh_values("kStormRadiusYd"), (8.0, 10.0))
        self.assertEqual(_nh_values("kStormPct"), (30.0, 45.0))
        self.assertEqual(_nh_values("kStormTankPct"), (15.0, 25.0))

    def test_devotion_aura(self):
        aura = self.spells[DEVOTION]
        effect = aura["effect1"]
        self.assertEqual(effect["apply_aura"], AURA_MOD_DAMAGE_PERCENT_TAKEN)
        normal, heroic = _nh_values("kDevotionPct")
        self.assertEqual(effect["base_points"], -int(normal))
        self.assertEqual(effect["die_sides"], 0)
        self.assertEqual(aura["duration_ms"], int(_header_value("kDevotionAuraMs")))
        self.assertGreater(aura["duration_ms"], int(_header_value("kDevotionPulseMs")))
        self.assertEqual(aura["dispel"], 0)                                # not purgeable: kill the Captain
        self.assertEqual(_raw(aura, "SpellVisualID_1"), _visual("LS_DEVOTION"))
        self.assertEqual(_raw(self.spells[DEVOTION_PULSE], "SpellVisualID_1"), _visual("LS_DEVOTION_APPLY"))
        self.assertEqual(heroic, 40.0)
        self.assertIn("args.AddSpellBP0(-kDevotionPct(_heroic));", self.code)
        self.assertIn("me->IsWithinDistInMap(unit, kDevotionRadiusYd)", self.code)

    def test_the_ground(self):
        consecration = self.spells[CONSECRATION_GROUND]
        self.assertEqual(consecration["effect1"]["type"], PERSISTENT_AREA_AURA)
        self.assertEqual(consecration["duration_ms"], int(_header_value("kConsecrationMs")))
        self.assertEqual(float(consecration["effect1"]["radius_yards"]), _header_value("kConsecrationRadiusYd"))
        self.assertEqual(_raw(consecration, "SpellVisualID_1"), _visual("LS_CONSECRATION"))
        normal, heroic = _nh_values("kFlameFireMs")
        for spell_id, duration in ((FLAME_POOL, normal), (FLAME_POOL_H, heroic)):
            with self.subTest(spell=spell_id):
                pool = self.spells[spell_id]
                self.assertEqual(pool["effect1"]["type"], PERSISTENT_AREA_AURA)
                self.assertEqual(pool["duration_ms"], int(duration))
                self.assertEqual(float(pool["effect1"]["radius_yards"]), _header_value("kFlameRadiusYd"))
                self.assertEqual(_raw(pool, "SpellVisualID_1"), _visual("LS_FLAME_POOL"))
        # The zones: persistent, the tank's row on the tank, no Weakened on lingering ground.
        self.assertIn("zone.Persistent(Ms(kConsecrationMs), Ms(kConsecrationTickMs)).Damage(pct).TankDamage(pct)",
                      self.code)
        self.assertIn("fire.Persistent(Ms(kFlameFireMs(heroic)), Ms(kFlameFireTickMs)).Damage(tick).TankDamage(tick)",
                      self.code)

    def test_purifying_flame(self):
        cast = self.spells[FLAME_CAST]
        self.assertEqual(cast["effect1"]["type"], DUMMY_EFFECT)
        self.assertEqual(_raw(cast, "SpellVisualID_1"), _visual("LS_FLAME"))
        # The circle lands with the cast; a kick takes it away; a dead Wizard draws none.
        self.assertIn("circle.Damage(pct).TankDamage(pct).Weakened().Spell(SPELL_LS_PURIFYING_FLAME_HIT)", self.code)
        self.assertIn("Mechanic::Detonate(owner, _flame);", self.code)
        self.assertIn('CancelFlame("kicked");', self.code)
        self.assertIn('CancelFlame("died");', self.code)
        self.assertEqual(_nh_values("kFlamePct"), (30.0, 45.0))
        self.assertEqual(_nh_values("kFlameFirePct"), (10.0, 15.0))

    def test_greater_heal(self):
        normal = self.spells[GREATER_HEAL]
        self.assertEqual(normal["effect1"]["type"], HEAL_PCT)
        self.assertEqual(normal["effect1"]["base_points"], int(_header_value("kGreaterHealPct")))
        heroic = self.spells[GREATER_HEAL_H]
        self.assertEqual(heroic["effect1"]["type"], DUMMY_EFFECT)
        pulse = self.spells[GREATER_HEAL_PULSE]
        self.assertEqual(pulse["effect1"]["type"], HEAL_PCT)
        self.assertEqual(pulse["effect1"]["base_points"], int(_header_value("kMissedHealPct")))
        for spell_id in (GREATER_HEAL, GREATER_HEAL_H, GREATER_HEAL_PULSE):
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), _visual("LS_GREATER_HEAL"))
        # Heroic: a cast that lands heals the company; the interrupt list names both forms.
        self.assertIn("case SPELL_LS_GREATER_HEAL_H:\n                HealCompany();", self.code)
        self.assertIn("d.interrupts.emplace_back(NPC_SM_COMPANY_CHAPLAIN, heal, healKick,", self.code)
        self.assertIn("d.interrupts.emplace_back(NPC_SM_COMPANY_ABBOT, heal, healKick,", self.code)

    def test_the_charge(self):
        self.assertEqual(_raw(self.spells[CHARGE_LOOK], "SpellVisualID_1"), _visual("LS_CHARGE"))
        self.assertIn("spec.pct = kChargePct;\n        spec.tankPct = kChargePct;", self.code)
        self.assertIn("spec.weakened = true;", self.code)
        self.assertIn("champion->IsWithinLOSInMap(p)", self.code)          # handoff 7 #33 A: clipped to LOS

    def test_the_fall_and_the_chest(self):
        # The stock fake death at 1%: the floor in DamageTaken, the fall only once no company is left.
        self.assertIn("ClampToFloor(me->GetHealth(), me->GetMaxHealth(), damage, kFallPct)", self.code)
        self.assertIn("FallAllowed(atFloor, _called, AnyMemberAlive(), _heroic && !_reserveCalled)", self.code)
        self.assertIn("instance->SetData(DATA_LAST_STAND, DONE);", self.code)
        self.assertIn("instance->SetData(DATA_LAST_STAND, FAIL);", self.code)
        # The credit is the instance's (never sent from Mograine).
        self.assertNotIn("CreditEncounterBySpell", self.code)
        self.assertNotIn("kSpellLastStandCredit", self.code)
        # The chest of the difficulty, summoned by the map.
        self.assertIn("IsHeroicMap(me) ? GO_SM_LAST_STAND_CHEST_H : GO_SM_LAST_STAND_CHEST", self.code)
        self.assertIn("me->GetMap()->SummonGameObject(entry,", self.code)

    def test_no_wrong_look_is_wired(self):
        # The thrown hammer is Hammer of Wrath's (V: Hammer of Justice's SV 322 throws nothing); SV 322 is the stun
        # only.
        for spell_id, spell in self.spells.items():
            visual = int(_raw(spell, "SpellVisualID_1"))
            if visual == WRONG_THROWN_HAMMER:
                self.assertEqual(spell_id, HAMMER_STUN)
        # Every look-only spell carries a look.
        for spell_id in (HAMMER_THROW, STORM_CAST, DEVOTION, DEVOTION_PULSE, CONSECRATION_GROUND, FIREBALL, FLAME_CAST,
                         FLAME_POOL, FLAME_POOL_H, GREATER_HEAL, CHARGE_LOOK):
            self.assertNotEqual(int(_raw(self.spells[spell_id], "SpellVisualID_1")), 0, spell_id)

    def test_the_finale_hooks(self):
        fight = FIGHT.read_text(encoding="utf-8")
        for name in ("class MograineFight", "class MograineRisen", "void RegisterMograineRisen",
                     "MograineFight* MograineFightOf", "virtual bool Rise(uint32 maxHealth, float healthPct",
                     "virtual void KillForGood(Unit* killer)", "virtual void BackToBody(char const* why)"):
            self.assertIn(name, fight)
        self.assertIn("struct boss_mograine_rework : public ScriptedAI, public LastStandHost, public MograineFight",
                      self.code)

    # ---- the SQL rev ------------------------------------------------------------------------------------------------

    def test_the_sql_rev(self):
        sql = SQL.read_text(encoding="utf-8")
        body = "\n".join(line for line in sql.splitlines() if not line.startswith("--"))
        deleted = re.search(r"DELETE FROM `creature` WHERE `id` IN \(([^)]*)\) AND `guid` IN \(([^)]*)\);", body)
        self.assertIsNotNone(deleted)
        self.assertEqual({int(v) for v in deleted.group(1).split(",")}, {4299, 4300, 4301, 4302, 4303, 4540})
        self.assertEqual(sorted(int(v) for v in re.findall(r"\d+", deleted.group(2))), sorted(NAVE_GUIDS))
        for guid in KEPT_GUIDS + GARDEN_PATH_GUIDS:
            self.assertNotIn(str(guid), body)
        addon = re.search(r"DELETE FROM `creature_addon` WHERE `guid` IN \(([^)]*)\);", body)
        self.assertEqual(sorted(int(v) for v in re.findall(r"\d+", addon.group(1))), sorted(NAVE_GUIDS))
        self.assertIn("DELETE FROM `smart_scripts` WHERE `source_type` = 0 AND `entryorguid` IN "
                      "(-40008, -40015, -40019, -40034);", body)
        self.assertIn("DELETE FROM `waypoints` WHERE `entry` IN (4000800, 4001500, 4001900, 4003400);", body)
        self.assertIn("DELETE FROM `waypoint_data` WHERE `id` IN (400150, 400340);", body)
        # The five yells (type 14), groups 7-11; nothing stock rewritten.
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 3976 AND `GroupID` BETWEEN 7 AND 11;", body)
        for group in range(7, 12):
            self.assertRegex(body, rf"\(3976, {group}, 0, '[^']+', 14, 0, 100,")
        for group in range(0, 7):
            self.assertNotIn(f"(3976, {group}, 0,", body)
        self.assertIn("'The heretics are at the door! Brothers, sisters, the Crusade stands here!'", body)
        self.assertIn("'To me! The Crusade stands here!'", body)
        # The two chests: CHEST templates whose loot entry is their own id; the loot is L-2's rev alone (the placeholder
        # rows are gone, R-2-LOOT nit), and that rev sorts after this one and fills both entries.
        loot = (SQL.parent / "rev_loot_wave_2_scarlet_monastery.sql").read_text(encoding="utf-8")
        self.assertLess(SQL.name, "rev_loot_wave_2_scarlet_monastery.sql")
        self.assertNotIn("gameobject_loot_template", body)
        for entry in (301330, 301331):
            self.assertRegex(body, rf"\({entry}, 3, 1387, 'Chest of the Last Stand', '', '', '', 1, 57, {entry},")
            self.assertRegex(loot, rf"\n\({entry}, \d+, ")
        # Rule 14: no spawn, no SmartAI insert (the companies and the chest are summoned).
        self.assertNotIn("INSERT INTO `creature` ", body)
        self.assertNotIn("INSERT INTO `gameobject` ", body)
        self.assertNotIn("INSERT INTO `smart_scripts`", body)
        self.assertNotIn("UPDATE `creature`", body)


if __name__ == "__main__":
    unittest.main()
