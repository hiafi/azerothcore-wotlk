"""
Scarlet Monastery build WP-D4, Bloodmage Thalnos: source/npcs/scarlet_monastery/thalnos.py against its C++
(modules/mod-dungeon-bosses src/ScarletMonastery/ThalnosLogic.h, boss_bloodmage_thalnos_rework.cpp, ThalnosFight.h) and
its SQL rev.

Checks:
  - the spells sit in his slice (212440-212479) and ThalnosLogic.h names the same ids;
  - Thalnos 4543 is bound (SmartAI off) at 48k on the level 32 paladin base, stun immune, INSTANCE_BIND;
  - the kickable casts (Bolt, Lance, the three nova bars) kick only (InterruptFlags 4, PreventionType 1), the restart
    is a Physical bar (a kick's Shadow lockout must not stop it), Flame Spike's bar is not interruptible;
  - the percent hits carry the header's percents (hundredths, heroic in EffectMiscValueB) and the kit's refflat script;
    the registry hits are resolve copies of the right schools;
  - Blood Ritual stacks to 255, Blood Brand is Magic, the debuffs are not dispellable; the looks are V's;
  - the retired stock spells are never cast; the C++ registers the mechanics the build spec names and the hooks D4H
    builds on;
  - the SQL rev writes the one new emote (type 41) and touches nothing else.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scarlet_monastery_thalnos.py
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
HEADER = MODULE_DIR / "ThalnosLogic.h"
FIGHT = MODULE_DIR / "ThalnosFight.h"
REWORK = MODULE_DIR / "ScarletMonasteryRework.h"
SCRIPT = MODULE_DIR / "boss_bloodmage_thalnos_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_thalnos_scarlet_monastery.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "scarlet_monastery"

SLICE = range(212440, 212480)
(RITUAL, HANDS, BOLT, LANCE, LANCE_LINE, SPIKE_CAST, SPIKE, PILLAR, POOL, POOL_LOOK, BOIL, BOIL_SPLASH, BOIL_BURST,
 NOVA_CAST, EMPOWERED_NOVA_CAST, NOVA_RESTART, NOVA, EMPOWERED_NOVA, BRAND, SPIKE_ERUPT) = range(212440, 212460)
THALNOS = 4543
PALADIN_32_BASE = 888       # creature_classlevelstats level 32 class 2 basehp0

SCHOOL_NORMAL, SCHOOL_FIRE, SCHOOL_SHADOW = 1, 4, 32
SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT = 2, 6, 3
AURA_DUMMY = 4
DISPEL_MAGIC = 1
INTERRUPT_KICK = 0x4
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT_DAMAGE = "spell_dungeon_refflat_damage"
# V's picks (_visuals.py): Uzo's Ritual of Blood's hands, Bloodbolt, Bloodbolt Splash's ground impact, the stock Flame
# Spike, the 4 yd lava rung, Boiling Blood, the BloodyExplosion, Blood Nova's red hands, Vampiric Curse.
SV_RITUAL, SV_BOLT, SV_LANCE, SV_SPIKE, SV_POOL = 9585, 9308, 15253, 10383, 90606
SV_BOIL, SV_ERUPTION, SV_NOVA, SV_BRAND = 15286, 9312, 15283, 14871
# VR WRONG list for Thalnos: the doc's Summon Spirits SV 8116 and Blood Link SV 15256 (both D4H's, never here).
SV_WRONG = (8116, 15256)
STOCK = (9613, 8814, 8053, 12470)


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


def _code(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith(("//", "*", "/*")))


class ThalnosDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) == THALNOS}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(RITUAL, SPIKE_ERUPT + 1)))
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery", {"spell": mine}), [])
        first = re.search(r"kSpellsThalnos\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(first)
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_TH_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))

    def test_thalnos_is_bound(self):
        boss = self.edits[THALNOS]
        self.assertEqual(boss["ScriptName"], "boss_bloodmage_thalnos_rework")
        self.assertEqual(boss["AIName"], "")
        # 48k at 5 players (the build spec), within 2 HP.
        self.assertLessEqual(abs(math.ceil(PALADIN_32_BASE * boss["HealthModifier"]) - 48000), 2)
        self.assertEqual(boss["DamageModifier"], 1.7)
        self.assertEqual(boss["CreatureImmunitiesId"], 1972)
        self.assertEqual(boss["flags_extra"], 1)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_bloodmage_thalnos_rework,", self.cpp)
        self.assertIn('SmTest::RegisterBoss("thalnos"', self.cpp)

    def test_the_kickable_casts(self):
        for spell_id, school, cast in ((BOLT, SCHOOL_SHADOW, "kBoltCastMs"), (LANCE, SCHOOL_SHADOW, "kBoltCastMs"),
                                       (NOVA_CAST, SCHOOL_SHADOW, "kNovaCastMs"),
                                       (EMPOWERED_NOVA_CAST, SCHOOL_SHADOW, "kNovaCastMs"),
                                       (NOVA_RESTART, SCHOOL_NORMAL, "kNovaRestartCastMs")):
            bar = self.spells[spell_id]
            self.assertEqual(_raw(bar, "InterruptFlags"), INTERRUPT_KICK, spell_id)
            self.assertEqual(_raw(bar, "PreventionType"), 1, spell_id)
            self.assertEqual(bar["school"], school, spell_id)
            self.assertEqual(bar["cast_time_ms"], int(_header_value(cast)), spell_id)
        # The restart must not share the school a kick of the empowered nova locks.
        self.assertNotEqual(self.spells[NOVA_RESTART]["school"], self.spells[EMPOWERED_NOVA_CAST]["school"])
        self.assertEqual(self.spells[EMPOWERED_NOVA_CAST]["name"], "Empowered Blood Nova")
        self.assertEqual(self.spells[LANCE]["name"], "Blood Lance")
        for spell_id in (NOVA_CAST, EMPOWERED_NOVA_CAST, NOVA_RESTART):
            self.assertEqual(self.spells[spell_id]["effect1"]["type"], DUMMY_EFFECT, spell_id)
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), SV_NOVA, spell_id)
        # Flame Spike's bar is a must-play bar: not interruptible, a school no kickable cast uses.
        spike = self.spells[SPIKE_CAST]
        self.assertEqual(_raw(spike, "InterruptFlags"), 0)
        self.assertEqual(_raw(spike, "PreventionType"), 0)
        self.assertEqual(spike["school"], SCHOOL_FIRE)
        self.assertEqual(spike["cast_time_ms"], int(_header_value("kSpikeCastMs")))
        self.assertEqual(_raw(spike, "SpellVisualID_1"), SV_SPIKE)

    def test_the_percent_hits(self):
        cases = ((BOLT, "kBoltTankPct", SV_BOLT), (LANCE, "kLanceTankPct", SV_BOLT),
                 (BOIL_BURST, "kBoilCarrierPct", SV_ERUPTION), (NOVA, "kNovaPct", SV_ERUPTION),
                 (EMPOWERED_NOVA, "kEmpoweredNovaPct", SV_ERUPTION))
        for spell_id, pct, look in cases:
            spell = self.spells[spell_id]
            effect = spell["effect1"]
            self.assertEqual(effect["type"], SCHOOL_DAMAGE, spell_id)
            self.assertEqual(spell["school"], SCHOOL_SHADOW, spell_id)
            normal, heroic = _nh_values(pct)
            self.assertEqual(int(effect["base_points"]), int(normal * 100), spell_id)
            self.assertEqual(int(effect["die_sides"]), 0, spell_id)
            self.assertEqual(_raw(spell, "EffectMiscValueB_1"), int(heroic * 100), spell_id)
            self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS, spell_id)
            self.assertEqual(_raw(spell, "SpellVisualID_1"), look, spell_id)
            self.assertIn((spell_id, REFFLAT_DAMAGE), self.scripts)
        self.assertEqual(_nh_values("kBoltTankPct"), (20, 30))
        self.assertEqual(_nh_values("kLanceTankPct"), (30, 40))
        self.assertEqual(_nh_values("kBoilCarrierPct"), (25, 35))
        self.assertEqual(_nh_values("kNovaPct"), (15, 20))
        self.assertEqual(_nh_values("kEmpoweredNovaPct"), (25, 35))

    def test_the_resolve_copies(self):
        for spell_id, school, look in ((LANCE_LINE, SCHOOL_SHADOW, SV_LANCE), (PILLAR, SCHOOL_FIRE, 0),
                                       (POOL, SCHOOL_FIRE, 0), (BOIL_SPLASH, SCHOOL_SHADOW, SV_ERUPTION)):
            spell = self.spells[spell_id]
            self.assertEqual(spell["school"], school, spell_id)
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
            self.assertEqual(_raw(spell, "SpellVisualID_1"), look, spell_id)
        self.assertEqual(_nh_values("kLanceLinePct"), (35, 45))
        self.assertEqual(_nh_values("kSpikePillarPct"), (35, 45))
        self.assertEqual(_nh_values("kSpikePoolPct"), (5, 8))
        self.assertEqual(_nh_values("kBoilSplashPct"), (35, 45))

    def test_the_auras(self):
        ritual = self.spells[RITUAL]
        self.assertEqual(ritual["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(_raw(ritual, "CumulativeAura"), int(_header_value("kAuraStackLimit")))
        self.assertEqual(ritual["dispel"], 0)
        self.assertEqual(ritual["duration_ms"], -1)
        spike = self.spells[SPIKE]
        self.assertEqual(spike["duration_ms"], int(_header_value("kSpikeCastMs")))
        self.assertEqual(spike["dispel"], 0)
        boil = self.spells[BOIL]
        self.assertEqual(boil["duration_ms"], int(_header_value("kBoilMs")))
        self.assertEqual(boil["dispel"], 0)
        self.assertEqual(_raw(boil, "SpellVisualID_1"), SV_BOIL)
        brand = self.spells[BRAND]
        self.assertEqual(brand["duration_ms"], int(_header_value("kBrandMs")))
        self.assertEqual(brand["dispel"], DISPEL_MAGIC)
        self.assertEqual(_raw(brand, "SpellVisualID_1"), SV_BRAND)
        self.assertEqual(_raw(self.spells[HANDS], "SpellVisualID_1"), SV_RITUAL)
        self.assertEqual(_raw(self.spells[POOL_LOOK], "SpellVisualID_1"), SV_POOL)
        self.assertEqual(_raw(self.spells[SPIKE_ERUPT], "SpellVisualID_1"), SV_SPIKE)

    def test_the_looks_are_vs(self):
        for spell in self.spells.values():
            self.assertNotIn(_raw(spell, "SpellVisualID_1"), SV_WRONG, spell["id"])

    def test_scripts_are_the_kits(self):
        self.assertEqual({name for _, name in self.scripts}, {RESOLVE, REFFLAT_DAMAGE})

    def test_the_stock_spells_are_retired(self):
        code = _code(self.cpp)
        for stock in STOCK:
            self.assertNotIn(str(stock), code)
        self.assertNotIn("SPELL_STOCK_", code)
        self.assertNotIn("\t", self.cpp)

    def test_the_cpp_registers_the_spec(self):
        code = _code(self.cpp)
        # TH2e: a line fixed at the bar's start through the tank, the tank exempt, Weakened.
        self.assertIn("Shapes::LineFacing(BossMechanics::Anchor(apex), facing,", code)
        self.assertIn("ref.Damage(pct).TankDamage(pct).Weakened().TankExempt().Spell(SPELL_TH_BLOOD_LANCE_LINE)", code)
        # TH3: the carry to the edge, then the pillar with Weakened, then the pool.
        self.assertIn("DungeonKit::FollowThenLand(me, target, kSpikeRadius, Ms(kSpikeCastMs), impact,", code)
        self.assertIn("rule.Edge().Away().Within(BoundsFor(_ground));", code)
        self.assertIn("ref.Damage(pct).TankDamage(pct).Weakened().Spell(SPELL_TH_FLAME_SPIKE_PILLAR)", code)
        self.assertIn("DungeonKit::Linger(me,", code)
        self.assertIn("rule.nonTank = false;       // the tank included", code)
        # TH4: a RunOut on non-tanks (the large-spread exemption), the tank still hit by the splash.
        self.assertIn("Mechanic::RunOut(me, targets.front(), radius, Ms(kBoilMs));", code)
        self.assertIn("ref.Targets(carriers).Damage(pct).TankDamage(pct).Weakened()"
                      ".Spell(SPELL_TH_BOILING_BLOOD_SPLASH)", code)
        self.assertIn("rule.nonTank = true;        // the tank is left out", code)
        # Boss data: the novas, the Lance and the Bolt on the interrupt list, Blood Brand on the dispel list.
        for spell in ("SPELL_TH_BLOOD_NOVA_CAST", "SPELL_TH_EMPOWERED_NOVA_CAST", "SPELL_TH_BLOOD_NOVA_RESTART",
                      "SPELL_TH_BLOOD_LANCE", "SPELL_TH_BLOOD_BOLT"):
            self.assertRegex(code, rf"InterruptEntry\(NPC_THALNOS, {spell},")
        self.assertIn("d.dispels.push_back(BossMechanics::DispelEntry(SPELL_TH_BLOOD_BRAND, 2))", code)
        # Scorn under game event 120, normal only (section 7 #35).
        self.assertIn("if (!IsHeroicMap(me) && sGameEventMgr->IsActiveEvent(kGameEventScourgeBossInInstance))", code)
        # The hard mode's hooks are called (ThalnosFight.h).
        for hook in ("CreateThalnosHardMode(me)", "_hardMode->OnEngage(*this)", "_hardMode->OnThreshold(*this)",
                     "_hardMode->OnUpdate(*this, diff)", "_hardMode->OnDamageTaken(*this, attacker, damage)",
                     "_hardMode->ConfigureDescriptor(*this, d)", "hardMode->OnEnd(*this, died)",
                     "OnBossPull(me, kBossLogName, hardMode)", "instance->GetData(DATA_HARD_MODE_THALNOS)"):
            self.assertIn(hook, code)

    def test_the_hooks_header(self):
        fight = FIGHT.read_text(encoding="utf-8")
        for name in ("class ThalnosFight", "class ThalnosHardMode", "void RegisterThalnosHardMode(",
                     "void RegisterThalnosIdleHook(", "virtual void SetGround(Ground ground, char const* why) = 0;",
                     "virtual void OnThreshold(ThalnosFight& /*fight*/)",
                     "virtual uint32 AddRitualStacks(uint32 n, char const* why) = 0;"):
            self.assertIn(name, fight)
        self.assertEqual(_header_value("kNoRestPct"), 75)


class ThalnosSqlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.header = _header()

    def test_the_text(self):
        self.assertRegex(self.sql, r"\(4543, 3, 0, '[^\n]*', 41, 0, 100, ")
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 4543 AND `GroupID` = 3;", self.sql)
        self.assertIn("%s''s hands run red with blood!", self.sql)
        groups = dict(re.findall(r"(?:SAY|EMOTE)_(\w+)\s*=\s*(\d+),", self.header))
        self.assertEqual(sorted(int(v) for v in groups.values()), [0, 1, 2, 3, 4])

    def test_the_rev_touches_only_the_new_text(self):
        code = "\n".join(line for line in self.sql.splitlines() if not line.startswith("--"))
        for table in ("smart_scripts", "creature_loot_template", "UPDATE `creature`", "creature_template",
                      "conditions"):
            self.assertNotIn(table, code)
        # The stock lines 0-2 (and their sounds) and D4H's line 4 are never deleted.
        self.assertNotIn("BETWEEN", code)
        self.assertNotIn("`GroupID` = 4", code)


if __name__ == "__main__":
    unittest.main()
