"""
Scarlet Monastery build WP-D14, High Inquisitor Whitemane with Mograine risen:
source/npcs/scarlet_monastery/whitemane.py against its C++ (modules/mod-dungeon-bosses src/ScarletMonastery/
WhitemaneLogic.h, boss_whitemane_rework.cpp, WhitemaneFight.h) and its SQL rev.

Checks:
  - the spells sit in the slice (213150-213189) and WhitemaneLogic.h names the same ids;
  - Whitemane 3977 is bound only behind BIND_WAVE_2 (S0's line: 50k on the level 40 paladin base, stun immune,
    INSTANCE_BIND, the stock 2.2), her AI registers only behind kWave2Bound, Mograine's rising hook on every wave;
  - the numbers the build spec sets (the sleep, the raise, the channels, the shield, the casts, the flame) match the
    header;
  - the only interruptible casts (Heal, Holy Smite) are Holy, every bar she or he must play is Physical (rule 5);
    every damage spell ignores caster modifiers (rule 2) and the script-amount ones carry DieSides 0;
  - the looks are V's WM_ ids and never a WRONG-listed one (Beam of Light SV 12479);
  - the C++ registers what the build spec names (the tank in the lane and the pillars, the Spread for Penance, the
    flame's Soak with the tank last and the Seared kept off, the interrupt and purge lists, no Dominate Mind);
  - the SQL rev writes her lines 3, 4, 5, 7 and his 12, 13, the flame's line as a raid emote, and touches nothing
    else (no spawn, no SmartAI row).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scarlet_monastery_whitemane.py
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
HEADER = MODULE_DIR / "WhitemaneLogic.h"
REWORK = MODULE_DIR / "ScarletMonasteryRework.h"
SCRIPT = MODULE_DIR / "boss_whitemane_rework.cpp"
FIGHT = MODULE_DIR / "WhitemaneFight.h"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_whitemane_scarlet_monastery.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "scarlet_monastery"
VISUALS = PACKAGE / "_visuals.py"
COMMON = PACKAGE / "_common.py"

SLICE = range(213150, 213190)
(DEEP_SLEEP, RAISE, RESURRECTION, RISE_LOOK, LAY_ON_HANDS, LAY_ON_HANDS_LOOK, LANE_HIT, CHARGE_LOOK, BODY_SHIELD,
 PENANCE_MARK, PENANCE_HIT, PENANCE_STRIKE, PENANCE_PILLAR, PENANCE_HANDS, HEAL, SHIELD, SMITE, VIGIL_FLAME,
 VIGIL_FLARE, SEARED, FLAME_PASS) = range(213150, 213171)
WHITEMANE = 3977
BASE_40_PALADIN = 1226

SCHOOL_PHYSICAL, SCHOOL_HOLY, SCHOOL_FIRE = 1, 2, 4
SCHOOL_DAMAGE, DUMMY_EFFECT, APPLY_AURA, HEAL_PCT = 2, 3, 6, 136
AURA_DUMMY, AURA_MOD_STUN, AURA_SCHOOL_ABSORB = 4, 12, 69
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
ATTR1_IS_CHANNELED = 0x00000004
RESOLVE = "spell_boss_mechanics_resolve"
BEAM_OF_LIGHT_SV = 12479            # VR: a 135 x 135 x 315 yd model, never wired


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


def _effect(spell: dict) -> dict:
    return spell["effect1"]


class WhitemaneDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) == WHITEMANE}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.code = _code(cls.cpp)

    # ---- ids --------------------------------------------------------------------------------------------------------

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(DEEP_SLEEP, FLAME_PASS + 1)))
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery", {"spell": mine}), [])
        first = re.search(r"kSpellsWhitemane\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(first)
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_WM_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))
        # The retired stock casts are never cast here: Dominate Mind, the stock Heal, Shield and Smite.
        for stock in ("14515", "12039", "22187", "9481"):
            self.assertNotIn(stock, self.code)

    # ---- Whitemane --------------------------------------------------------------------------------------------------

    def test_whitemane_is_bound_only_with_wave_2(self):
        self.assertIn("if (kWave2Bound)\n        RegisterDungeonReworkCreatureAI(boss_whitemane_rework,", self.cpp)
        # Mograine's rising hook registers on every wave (D13's AI asks for it only when it runs).
        self.assertIn("SmLastStand::RegisterMograineRisen(", self.code)
        if not _wave2_bound():
            self.assertNotIn(WHITEMANE, self.edits, "a wave 2 boss stays stock until W2-SETUP")
            return
        boss = self.edits[WHITEMANE]
        self.assertEqual(boss["ScriptName"], "boss_whitemane_rework")
        self.assertEqual(boss["AIName"], "")
        self.assertLessEqual(abs(math.ceil(BASE_40_PALADIN * boss["HealthModifier"]) - 50000), 2)
        self.assertEqual(boss["DamageModifier"], 2.2)
        self.assertEqual(boss["CreatureImmunitiesId"], 1972)
        self.assertEqual(boss["flags_extra"], 1)        # INSTANCE_BIND: her kill is the encounter's credit (row 450)

    def test_the_whitemane_column_line_is_the_s0_one(self):
        text = (PACKAGE / "whitemane.py").read_text(encoding="utf-8")
        self.assertIn("if BIND_WAVE_2:\n    creature_template_columns(3977, **boss_columns(\n"
                      "        'boss_whitemane_rework', 40.783, damage_modifier=2.2,", text)
        self.assertEqual(int(_nh_values("kWhitemaneHealth")[0]), 50000)
        self.assertLessEqual(abs(math.ceil(BASE_40_PALADIN * 40.783) - 50000), 2)

    # ---- numbers ----------------------------------------------------------------------------------------------------

    def test_numbers_match_the_header(self):
        s = self.spells
        self.assertEqual(s[DEEP_SLEEP]["duration_ms"], _header_value("kDeepSleepMs"))
        self.assertEqual(_effect(s[DEEP_SLEEP])["radius_yards"], _header_value("kDeepSleepRadiusYd"))
        self.assertEqual(s[RAISE]["cast_time_ms"], _header_value("kRaiseCastMs"))
        self.assertEqual(s[RESURRECTION]["duration_ms"], _nh_values("kHerSaveMs")[0])
        self.assertEqual(s[LAY_ON_HANDS]["duration_ms"], _nh_values("kHisSaveMs")[0])
        self.assertGreaterEqual(s[RESURRECTION]["duration_ms"], _nh_values("kHerSaveMs")[1])
        self.assertGreaterEqual(s[LAY_ON_HANDS]["duration_ms"], _nh_values("kHisSaveMs")[1])
        self.assertEqual(s[BODY_SHIELD]["duration_ms"], _header_value("kBodyShieldMs"))
        self.assertEqual(s[PENANCE_MARK]["duration_ms"], _header_value("kPenanceWarnMs"))
        self.assertEqual(s[HEAL]["cast_time_ms"], _header_value("kHealCastMs"))
        self.assertEqual(_effect(s[HEAL])["base_points"], _nh_values("kHealPct")[0])
        self.assertEqual(s[SHIELD]["duration_ms"], _header_value("kShieldAuraMs"))
        self.assertEqual(s[SMITE]["cast_time_ms"], _header_value("kSmiteCastMs"))
        self.assertEqual(s[SMITE]["range_yards"], _header_value("kCastRangeYd"))
        self.assertEqual(s[HEAL]["range_yards"], _header_value("kCastRangeYd"))
        self.assertEqual(s[VIGIL_FLAME]["duration_ms"], _header_value("kFlameAuraMs"))
        self.assertEqual(s[SEARED]["duration_ms"], _header_value("kSearedMs"))
        # The build spec's numbers (CATH WM rows): heal 6 / 20 (hub ruling 54), windows 10 / 8 and 6 / 5 s, Seared 19 s.
        self.assertEqual(_nh_values("kHealPct"), (6, 20))
        self.assertEqual(_nh_values("kHerSaveMs"), (10000, 8000))
        self.assertEqual(_nh_values("kHisSaveMs"), (6000, 5000))
        self.assertEqual(_nh_values("kLanePct"), (30, 45))
        self.assertEqual(_nh_values("kPenanceMarkedPct"), (20, 30))
        self.assertEqual(_nh_values("kPenanceOthersPct"), (30, 45))
        self.assertEqual(_nh_values("kPenanceCount"), (2, 3))
        self.assertEqual(_nh_values("kSmitePct"), (10, 15))
        self.assertEqual(_nh_values("kMograineRisenHealth"), (45000, 200000))
        self.assertEqual(_header_value("kSearedMs"), 19000)
        self.assertEqual(_header_value("kFlareTotalPct"), 110)

    # ---- rule 5 and rule 2 ------------------------------------------------------------------------------------------

    def test_schools_interrupts_and_caster_modifiers(self):
        s = self.spells
        kickable = {i for i, e in s.items() if _raw(e, "InterruptFlags") == 15}
        self.assertEqual(kickable, {HEAL, SMITE})
        for i in kickable:
            self.assertEqual(s[i]["school"], SCHOOL_HOLY, i)
            self.assertEqual(_raw(s[i], "PreventionType"), 1, i)
        # The bars she or he must play are Physical (a Holy kick's lockout never stops them), never interruptible.
        for i in (RAISE, RESURRECTION, LAY_ON_HANDS):
            self.assertEqual(s[i]["school"], SCHOOL_PHYSICAL, i)
            self.assertEqual(_raw(s[i], "InterruptFlags"), 0, i)
        for i in (RESURRECTION, LAY_ON_HANDS):
            self.assertTrue(_raw(s[i], "AttributesEx") & ATTR1_IS_CHANNELED, i)
            self.assertEqual(_raw(s[i], "ChannelInterruptFlags"), 0, i)
        # Every damage spell ignores the caster's modifiers; the script-amount ones carry DieSides 0 (exact amount).
        for i, e in s.items():
            if _effect(e)["type"] != SCHOOL_DAMAGE:
                continue
            self.assertTrue(_raw(e, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS, i)
            if (i, RESOLVE) not in self.scripts:
                self.assertEqual(_effect(e)["die_sides"], 0, i)
                self.assertEqual(_effect(e)["base_points"], 0, i)
        self.assertEqual({i for i, _ in self.scripts}, {LANE_HIT, PENANCE_HIT})
        self.assertEqual(s[LANE_HIT]["school"], SCHOOL_PHYSICAL)
        self.assertEqual(s[PENANCE_HIT]["school"], SCHOOL_HOLY)
        self.assertEqual(_effect(s[HEAL])["type"], HEAL_PCT)
        self.assertEqual(_effect(s[HEAL])["die_sides"], 0)
        self.assertEqual(_effect(s[SHIELD])["apply_aura"], AURA_SCHOOL_ABSORB)
        self.assertEqual(s[SHIELD]["dispel"], 1)        # Magic: purgeable
        self.assertEqual(_effect(s[DEEP_SLEEP])["apply_aura"], AURA_MOD_STUN)
        self.assertEqual(s[DEEP_SLEEP]["mechanic"], 10)  # sleep
        self.assertTrue(_raw(s[DEEP_SLEEP], "AuraInterruptFlags") & 0x2)    # damage wakes

    # ---- looks ------------------------------------------------------------------------------------------------------

    def test_visuals_are_vs(self):
        s = self.spells
        expected = {
            DEEP_SLEEP: "WM_DEEP_SLEEP", RAISE: "WM_RESURRECTION", RESURRECTION: "WM_RESURRECTION",
            RISE_LOOK: "WM_RESURRECTION", LAY_ON_HANDS: "WM_LAY_ON_HANDS", LAY_ON_HANDS_LOOK: "WM_LAY_ON_HANDS",
            CHARGE_LOOK: "WM_CHARGE", BODY_SHIELD: "WM_BODY_SHIELD", PENANCE_MARK: "WM_PENANCE_RING",
            PENANCE_PILLAR: "WM_PENANCE_PILLAR", PENANCE_HANDS: "WM_PENANCE_CHANNEL", HEAL: "WM_HEAL",
            SHIELD: "WM_PWS", SMITE: "WM_SMITE", VIGIL_FLAME: "WM_VIGIL_FLAME", SEARED: "WM_SEARED",
            FLAME_PASS: "WM_VIGIL_FLAME_PASS",
        }
        for spell_id, name in expected.items():
            self.assertEqual(_raw(s[spell_id], "SpellVisualID_1"), _visual(name), (spell_id, name))
        for e in s.values():
            self.assertNotEqual(_raw(e, "SpellVisualID_1"), BEAM_OF_LIGHT_SV)
        self.assertEqual(_visual("WM_PENANCE_PILLAR"), 90564)

    # ---- the C++ ----------------------------------------------------------------------------------------------------

    def test_the_script_registers_what_the_build_spec_names(self):
        code = self.code
        # WM2: the lane hits the tank too, owned by Mograine (his victim is the tank), Physical, Weakened.
        self.assertRegex(code, r"Mechanic::Line\(m, ")
        self.assertRegex(code, r"\.Damage\(pct\)\.TankDamage\(pct\)\.Weakened\(\)\.School\(SPELL_SCHOOL_NORMAL\)"
                               r"\.Spell\(SPELL_WM_LANE_HIT\)")
        # WM3: a Spread on the marked players, the tank too in the others' pillars.
        self.assertIn("Mechanic::Spread(owner, kPenanceRadiusYd, Ms(kPenanceWarnMs))", code)
        self.assertRegex(code, r"\.Targets\(targets\)\.Damage\(others\)\.TankDamage\(others\)\.Weakened\(\)")
        # WM5: the soak on the carrier, count 1, the tank last, never a missed-soak penalty; the Seared kept off.
        self.assertIn("Mechanic::Soak(owner, BossMechanics::Anchor(carrier), kFlameRadiusYd, 1, Ms(warn))", code)
        self.assertIn("tankLast.roleLast = BossMechanics::Role::Tank;", code)
        self.assertIn("MissedSoak(BossMechanics::MissedSoakMode::Never)", code)
        self.assertIn("flame.auraSpell = SPELL_WM_SEARED;", code)
        self.assertIn("seared.minStacks = 1;", code)
        # Boss data: Heal and Smite kicks, the shield's purge, kill together by percent of health, the tank on him.
        self.assertIn("d.interrupts.emplace_back(NPC_WHITEMANE, SPELL_WM_HEAL, kHealKickPriority(_heroic)", code)
        self.assertIn("d.interrupts.emplace_back(NPC_WHITEMANE, SPELL_WM_HOLY_SMITE, kSmiteKickPriority)", code)
        self.assertIn("d.purges.emplace_back(NPC_MOGRAINE, SPELL_WM_POWER_WORD_SHIELD, kShieldPurgePriority)", code)
        self.assertIn("KillTogether(NPC_MOGRAINE,", code)
        self.assertIn("BossMechanics::Who::Tank", code)
        # The saves go through D13's hooks, never his file.
        for call in ("f.Down(", "f->GetUp(", "f->KillForGood(", "->BackToBody(", "HoldControl("):
            self.assertIn(call, code, call)
        # The heroic body shield redirects damage in script (F43).
        self.assertIn("kBodyShieldShare", code)
        # The rising sets his finale health through MograineFight::Rise.
        self.assertIn("f->Rise(maxHealth, 100.f, why)", code)
        # Loot and hard mode bits are the instance's: never set in JustDied (rule 1).
        self.assertNotIn("SetHardModeLoot", code)
        self.assertNotIn("SetLootMode", code)

    def test_the_hooks_header_names_the_truth(self):
        text = FIGHT.read_text(encoding="utf-8")
        for name in ("class WhitemaneFight", "class WhitemaneHardMode", "RegisterWhitemaneHardMode",
                     "RegisterWhitemaneIdleHook", "SaveWindowMs", "ToHerSideAllowed", "FlameEveryMs", "SearedMs",
                     "RisenMaxHealth", "BreakCast", "OnDamageTaken", "ConfigureDescriptor"):
            self.assertIn(name, text, name)

    # ---- texts and the SQL rev --------------------------------------------------------------------------------------

    def test_the_sql_rev(self):
        sql = SQL.read_text(encoding="utf-8")
        rows = re.findall(r"^\((\d+), (\d+), 0, '((?:[^']|'')*)', (\d+),", sql, re.M)
        texts = {(int(c), int(g)): (t, int(kind)) for c, g, t, kind in rows}
        self.assertEqual(set(texts), {(3977, 3), (3977, 4), (3977, 5), (3977, 7), (3976, 12), (3976, 13)})
        self.assertEqual(texts[(3977, 7)], ("The Vigil Flame passes to $n!", 41))
        # The flame's raid emote reaches the whole floor (TextRange 3, map), as D12's emotes; her says keep 0.
        ranges = {(int(c), int(g)): int(r) for c, g, r in
                  re.findall(r"^\((\d+), (\d+), 0, '(?:[^']|'')*', \d+, 0, 100, \d+, 0, 0, 0, (\d+),", sql, re.M)}
        self.assertEqual(ranges.pop((3977, 7)), 3)
        self.assertTrue(all(r == 0 for r in ranges.values()), ranges)
        self.assertEqual(texts[(3977, 3)][0], "Mograine has fallen! You shall pay for this treachery!")
        self.assertEqual(texts[(3977, 5)][1], 12)
        self.assertEqual(texts[(3976, 13)][0], "Milady!")
        self.assertEqual(texts[(3976, 12)][0], "Not while I stand, milady!")
        header = _header()
        for name, group in (("SAY_WHITEMANE_FALLEN", 3), ("SAY_WHITEMANE_NOT_YET", 4), ("SAY_WHITEMANE_TOGETHER", 5),
                            ("EMOTE_WHITEMANE_FLAME", 7), ("SAY_MOGRAINE_NOT_WHILE", 12), ("SAY_MOGRAINE_MILADY", 13)):
            self.assertRegex(header, rf"\b{name}\s*=\s*{group},")
        lowered = sql.lower()
        for forbidden in ("insert into `creature` ", "insert into `smart_scripts`", "delete from `creature` ",
                          "update `creature_template`"):
            self.assertNotIn(forbidden, lowered)
        self.assertNotIn("\t", sql)
        for line in sql.splitlines():
            self.assertLessEqual(len(line), 120, line)


if __name__ == "__main__":
    unittest.main()
