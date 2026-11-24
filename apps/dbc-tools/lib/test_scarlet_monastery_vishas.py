"""
Scarlet Monastery build WP-D1, Interrogator Vishas: source/npcs/scarlet_monastery/vishas.py against its C++
(modules/mod-dungeon-bosses src/ScarletMonastery/VishasLogic.h, boss_interrogator_vishas_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in his slice (212320-212349) and VishasLogic.h names the same ids;
  - Vishas 3983 is bound (SmartAI off) at 40k on the level 32 paladin base, stun immune, INSTANCE_BIND;
  - the bars are not interruptible and last the header's times; the hits are resolve copies of the right schools;
  - the DoTs (Interrogation, Pain) carry the header's percents (hundredths, heroic in EffectMiscValueB), ticks and
    durations and the kit's refflat script; Pain is Magic, Interrogation not dispellable;
  - Torment is an uninterruptible channel of the warning plus 8 ticks; its share takes the script's base point;
  - the looks are V's (and never Soul Drain's beamless SV 9364); the stock Shadow Word: Pain 2767 is never cast;
  - the C++ registers the mechanics the build spec names (tank included where it says so, Torment as SM-BM's example);
  - the SQL rev writes the three new emotes (type 41) and touches nothing else.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scarlet_monastery_vishas.py
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
HEADER = MODULE_DIR / "VishasLogic.h"
REWORK = MODULE_DIR / "ScarletMonasteryRework.h"
SCRIPT = MODULE_DIR / "boss_interrogator_vishas_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_vishas_scarlet_monastery.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "scarlet_monastery"

SLICE = range(212320, 212350)
(INTERROGATION_CAST, INTERROGATION, ACCOMPLICE, BRAND_CAST, BRAND, PAIN, TORMENT, TORMENT_SHARE) = range(212320, 212328)
VISHAS = 3983
PALADIN_32_BASE = 888       # creature_classlevelstats level 32 class 2 basehp0

SCHOOL_FIRE, SCHOOL_SHADOW = 4, 32
SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT = 2, 6, 3
AURA_DUMMY, AURA_PERIODIC_DAMAGE = 4, 3
DISPEL_MAGIC = 1
ATTR1_IS_CHANNELED = 0x4
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT_PERIODIC = "spell_dungeon_refflat_periodic"
# V's picks (_visuals.py): the Interrogation cast, the keening skull, Burning Brand's hands, the Branding Iron
# impact, Shadow Word: Pain, Drain Soul's beam. Soul Drain's SV 9364 draws no beam (VR WRONG list).
SV_INTERROGATION, SV_SKULL, SV_BRAND_HANDS, SV_BRAND_IMPACT, SV_PAIN, SV_TORMENT = 11627, 90506, 1946, 10800, 71, 788
SV_SOUL_DRAIN = 9364
STOCK_SHADOW_WORD_PAIN = 2767


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


class VishasDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) == VISHAS}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(INTERROGATION_CAST, TORMENT_SHARE + 1)))
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery", {"spell": mine}), [])
        first = re.search(r"kSpellsVishas\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(first)
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_VI_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))

    def test_vishas_is_bound(self):
        boss = self.edits[VISHAS]
        self.assertEqual(boss["ScriptName"], "boss_interrogator_vishas_rework")
        self.assertEqual(boss["AIName"], "")
        # 40k at 5 players (the build spec), within 2 HP.
        self.assertLessEqual(abs(math.ceil(PALADIN_32_BASE * boss["HealthModifier"]) - 40000), 2)
        self.assertEqual(boss["DamageModifier"], 2.0)
        self.assertEqual(boss["CreatureImmunitiesId"], 1972)
        self.assertEqual(boss["flags_extra"], 1)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_interrogator_vishas_rework,", self.cpp)
        self.assertIn('SmTest::RegisterBoss("vishas"', self.cpp)

    def test_the_bars(self):
        for spell_id, name in ((INTERROGATION_CAST, "kInterrogationCastMs"), (BRAND_CAST, "kBrandCastMs")):
            bar = self.spells[spell_id]
            self.assertEqual(bar["effect1"]["type"], DUMMY_EFFECT, spell_id)
            self.assertEqual(_raw(bar, "InterruptFlags"), 0, spell_id)
            self.assertEqual(_raw(bar, "PreventionType"), 0, spell_id)
            self.assertEqual(bar["cast_time_ms"], int(_header_value(name)), spell_id)
        self.assertEqual(self.spells[INTERROGATION_CAST]["cast_time_ms"], 1500)
        self.assertEqual(self.spells[BRAND_CAST]["cast_time_ms"], 2000)
        self.assertEqual(_raw(self.spells[INTERROGATION_CAST], "SpellVisualID_1"), SV_INTERROGATION)
        self.assertEqual(_raw(self.spells[BRAND_CAST], "SpellVisualID_1"), SV_BRAND_HANDS)

    def test_the_resolve_copies(self):
        accomplice = self.spells[ACCOMPLICE]
        brand = self.spells[BRAND]
        self.assertEqual(accomplice["school"], SCHOOL_SHADOW)
        self.assertEqual(brand["school"], SCHOOL_FIRE)
        for spell_id in (ACCOMPLICE, BRAND):
            self.assertEqual(self.spells[spell_id]["effect1"]["type"], SCHOOL_DAMAGE)
            self.assertIn((spell_id, RESOLVE), self.scripts)
        self.assertEqual(_raw(brand, "SpellVisualID_1"), SV_BRAND_IMPACT)
        self.assertEqual(_nh_values("kAccomplicePct"), (12, 20))
        self.assertEqual(_nh_values("kBrandPct"), (35, 45))

    def test_the_dots(self):
        cases = (
            (INTERROGATION, "kInterrogationPct", "kInterrogationTickMs", "kInterrogationMs", 0, SV_SKULL),
            (PAIN, "kPainPct", "kPainTickMs", "kPainMs", DISPEL_MAGIC, SV_PAIN),
        )
        for spell_id, pct, tick, duration, dispel, look in cases:
            spell = self.spells[spell_id]
            effect = spell["effect1"]
            self.assertEqual(spell["school"], SCHOOL_SHADOW, spell_id)
            self.assertEqual(effect["apply_aura"], AURA_PERIODIC_DAMAGE, spell_id)
            normal, heroic = _nh_values(pct)
            self.assertEqual(int(effect["base_points"]), int(normal * 100), spell_id)
            self.assertEqual(_raw(spell, "EffectMiscValueB_1"), int(heroic * 100), spell_id)
            self.assertEqual(effect["amplitude"], int(_header_value(tick)), spell_id)
            self.assertEqual(spell["duration_ms"], int(_header_value(duration)), spell_id)
            self.assertEqual(spell["dispel"], dispel, spell_id)
            self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS, spell_id)
            self.assertEqual(_raw(spell, "SpellVisualID_1"), look, spell_id)
            self.assertIn((spell_id, REFFLAT_PERIODIC), self.scripts)
        self.assertEqual(_nh_values("kInterrogationPct"), (4, 4))
        self.assertEqual(_nh_values("kPainPct"), (2, 4))
        self.assertEqual(self.spells[PAIN]["duration_ms"], 18000)

    def test_torment(self):
        beam = self.spells[TORMENT]
        self.assertTrue(_raw(beam, "AttributesEx") & ATTR1_IS_CHANNELED)
        self.assertEqual(_raw(beam, "ChannelInterruptFlags"), 0)
        self.assertEqual(_raw(beam, "InterruptFlags"), 0)
        self.assertEqual(_raw(beam, "PreventionType"), 0)
        self.assertEqual(beam["dispel"], 0)
        self.assertEqual(beam["effect1"]["apply_aura"], AURA_DUMMY)
        # The channel: the registry's warning plus the 8 ticks (TormentChannelMs).
        self.assertEqual(beam["duration_ms"], int(_header_value("kTormentWarnMs") + _header_value("kTormentMs")))
        self.assertEqual(_raw(beam, "SpellVisualID_1"), SV_TORMENT)
        share = self.spells[TORMENT_SHARE]
        self.assertEqual(share["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertEqual(int(share["effect1"]["base_points"]), 0)
        self.assertEqual(int(share["effect1"]["die_sides"]), 0)
        self.assertTrue(_raw(share, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertNotIn(TORMENT_SHARE, {spell_id for spell_id, _ in self.scripts})
        self.assertEqual(_nh_values("kTormentTickPct"), (20, 20))

    def test_the_looks_are_vs(self):
        for spell in self.spells.values():
            self.assertNotEqual(_raw(spell, "SpellVisualID_1"), SV_SOUL_DRAIN, spell["id"])

    def test_scripts_are_the_kits(self):
        self.assertEqual({name for _, name in self.scripts}, {RESOLVE, REFFLAT_PERIODIC})

    def test_the_stock_pain_is_retired(self):
        code = _code(self.cpp)
        self.assertNotIn(str(STOCK_SHADOW_WORD_PAIN), code)
        self.assertNotIn("SPELL_STOCK_", code)
        self.assertNotIn("\t", self.cpp)

    def test_the_cpp_registers_the_spec(self):
        code = _code(self.cpp)
        # VI1: a RunOut on random non-tanks, the tank exempt from being a carrier but hit as an accomplice.
        self.assertIn("Mechanic::RunOut(me, targets.front(), kAccompliceRadius, Ms(AccompliceWarnMs()))", code)
        self.assertIn(".Targets(carriers).Damage(pct).TankDamage(pct).Spell(SPELL_VI_ACCOMPLICE)", code)
        self.assertIn(".Persistent(Ms(AccomplicePersistMs()), Ms(kAccomplicePulseMs))", code)
        self.assertIn("rule.nonTank = true;        // the tank is never interrogated", code)
        # VI2: a cone fixed at the bar's start, the tank included, Weakened.
        self.assertIn("ref.Damage(pct).TankDamage(pct).Spell(SPELL_VI_BRANDING_IRON).Weakened()", code)
        self.assertNotIn("TankExempt", code)
        # VI4: SM-BM's F2 example (G1's torment drill row reads the same registration).
        self.assertIn(".Eligible(soakers).Persistent(Ms(kTormentMs), Ms(kTormentTickMs))"
                      ".EndBacksOff(kTormentBackOffYd)", code)
        self.assertIn(".TankNearSource(kTormentTankNearYd).MissedSoak(BossMechanics::MissedSoakMode::Never).Tag(VI4)",
                      code)
        self.assertIn("DungeonKit::SplitShares(me, takers, pct)", code)
        # Pain on the dispel list; no interrupt list.
        self.assertIn("d.dispels.push_back(BossMechanics::DispelEntry(SPELL_VI_PAIN, 1))", code)
        self.assertNotIn("d.interrupts", code)
        # The weapon swap and Vorrel's line.
        self.assertIn("me->SetVirtualItem(0, kItemHotIronPoker)", code)
        self.assertIn("vorrel->AI()->Talk(SAY_VORREL_DEATH)", code)


class VishasSqlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.header = _header()

    def test_the_texts(self):
        for group in (4, 5, 6):
            self.assertRegex(self.sql, rf"\(3983, {group}, 0, '[^\n]*', 41, 0, 100, ", group)
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 3983 AND `GroupID` BETWEEN 4 AND 6;", self.sql)
        groups = dict(re.findall(r"(?:SAY|EMOTE)_(\w+)\s*=\s*(\d+),", self.header))
        self.assertEqual(sorted(int(v) for v in groups.values()), [0, 1, 2, 3, 4, 5, 6])
        self.assertIn("%s demands a confession from $n!", self.sql)
        self.assertIn("%s takes a branding iron from the coals.", self.sql)
        self.assertIn("%s turns his torments on $n!", self.sql)

    def test_the_rev_touches_only_the_new_texts(self):
        code = "\n".join(line for line in self.sql.splitlines() if not line.startswith("--"))
        self.assertNotIn("smart_scripts", code)
        self.assertNotIn("creature_loot_template", code)
        self.assertNotIn("UPDATE `creature`", code)
        self.assertNotIn("creature_template", code)
        self.assertNotIn("creature_equip_template", code)
        # The stock lines 0-3 (and their sounds) are never deleted.
        self.assertNotIn("BETWEEN 0 AND", code)


if __name__ == "__main__":
    unittest.main()
