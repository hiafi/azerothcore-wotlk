"""
Zul'Farrak build WP-D4a, the Sandfury Executioner and the Block: source/npcs/zul_farrak/sandfury_executioner.py
against its C++ (modules/mod-dungeon-bosses src/ZulFarrak/BlockLogic.h, PyramidFight.h,
boss_sandfury_executioner_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in the Block's slice (213960-213989) and BlockLogic.h names the same ids;
  - the Executioner 7274 is bound (SmartAI off) at 136,058 on the level 46 warrior base, immunity 1972; the Pyramid
    stalker 301019 is an inert, invisible helper bound to its script;
  - nothing he casts is kickable (s3.5 kick table: Behead is a Physical bar, not interruptible) and the bar keeps his
    swing timer (LESSONS L2, L3);
  - the axe is a resolve copy (ignores caster modifiers, no redirection or reflection: LESSONS L7);
  - Grievous Wound: a Physical bleed of 3% a second (the kit's refflat periodic) with its 95% end script, no dispel,
    no mechanic, ignores caster modifiers, CHANGE_MAP; Offerings: +10% x 4; Blood Price: 0 per stack (the script sets
    the amount), 255 stacks shown; the header's numbers;
  - the looks are V's; the rope is a channel field (never cast);
  - the C++ keeps the rules: NoAssist first, the tank in the hit, no Weakened on the soak, the wound rider on heroic,
    the wound-free soak eligibility, the healer rule, the stage director, the cleanup;
  - the SQL rev writes the one new yell (group 2, type 14) and touches nothing else.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_zul_farrak_block.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "ZulFarrak"
HEADER = MODULE_DIR / "BlockLogic.h"
FIGHT = MODULE_DIR / "PyramidFight.h"
REWORK = MODULE_DIR / "ZulFarrakRework.h"
SCRIPT = MODULE_DIR / "boss_sandfury_executioner_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_sandfury_executioner_zul_farrak.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "zul_farrak"

SLICE = range(213960, 213990)
(BAR, BEHEAD, BEHEAD_LOOK, WOUND, WOUND_LOOK, OFFERINGS, BLOOD_PRICE, CHAIN) = range(213960, 213968)
EXECUTIONER, STALKER = 7274, 301019
WARRIOR_46_BASE = 1919      # creature_classlevelstats level 46 class 1 basehp0

SCHOOL_PHYSICAL = 1
SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT = 2, 6, 3
AURA_PERIODIC_DAMAGE, AURA_MOD_DAMAGE_PERCENT_DONE = 3, 79
PREVENTION_SILENCE = 1
ATTR1_NO_REDIRECTION, ATTR1_IS_CHANNELED, ATTR1_NO_REFLECTION = 0x8, 0x4, 0x80
ATTR2_DO_NOT_RESET_COMBAT_TIMERS = 0x00020000
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
CHANGE_MAP = 0x00080000
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT_PERIODIC = "spell_dungeon_refflat_periodic"
WOUND_SCRIPT = "spell_zf_pyramid_grievous_wound"
# V's picks (_visuals.py).
SV_BEHEAD, SV_CHAIN, SV_GRIEVOUS, SV_GRIEVOUS_STATE, SV_OFFERING = 39, 9275, 121, 15286, 47
INVISIBLE_STALKER = 11686
UNIT_FLAG_NON_ATTACKABLE, UNIT_FLAG_NOT_SELECTABLE = 0x2, 0x02000000


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


def _tune() -> str:
    text = HEADER.read_text(encoding="utf-8")
    return text[text.index("namespace Tune"):]


def _value(name: str) -> float:
    match = re.search(rf"\b{name} = (-?[\d.]+)f?;", _tune())
    assert match, name
    return float(match.group(1))


def _pair(name: str) -> tuple[float, float]:
    match = re.search(rf"\b{name}\{{ (-?[\d.]+)f?, (-?[\d.]+)f? \}};", _tune())
    assert match, name
    return float(match.group(1)), float(match.group(2))


def _code(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith(("//", "*", "/*")))


class BlockDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) == EXECUTIONER}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == STALKER}
        cls.models = [e for e in reg.creature_template_models if int(e["CreatureID"]) == STALKER]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.fight = FIGHT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(BAR, CHAIN + 1)))
        self.assertEqual(id_blocks.out_of_reservation("zul_farrak", {"spell": mine}), [])
        first = re.search(r"kSpellsBlock\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_PY_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", HEADER.read_text(encoding="utf-8"))
        self.assertEqual([SLICE.start + int(o) for o in offsets], mine)

    def test_the_executioner_and_the_stalker_are_bound(self):
        boss = self.edits[EXECUTIONER]
        self.assertEqual((boss["ScriptName"], boss["AIName"]), ("boss_sandfury_executioner_rework", ""))
        health = re.search(r"kExecutioner\{ (\d+), (\d+) \}", REWORK.read_text(encoding="utf-8"))
        self.assertEqual(math.ceil(WARRIOR_46_BASE * boss["HealthModifier"]), int(health.group(1)))
        self.assertEqual((boss["DamageModifier"], boss["CreatureImmunitiesId"]), (2.4, 1972))
        stalker = self.creatures[STALKER]
        self.assertEqual(stalker["ScriptName"], "npc_zf_pyramid_stalker")
        self.assertEqual(stalker["unit_flags"] & (UNIT_FLAG_NON_ATTACKABLE | UNIT_FLAG_NOT_SELECTABLE),
                         UNIT_FLAG_NON_ATTACKABLE | UNIT_FLAG_NOT_SELECTABLE)
        self.assertEqual(stalker.get("difficulty_entry_1", 0), 0)       # a helper: no heroic template
        self.assertEqual([int(m["CreatureDisplayID"]) for m in self.models],
                         [INVISIBLE_STALKER])
        for script in ("boss_sandfury_executioner_rework", "npc_zf_pyramid_stalker"):
            self.assertIn(f"RegisterDungeonReworkCreatureAI({script},", self.cpp)
        self.assertIn('ZfTest::RegisterBoss("block"', self.cpp)

    def test_nothing_is_kickable_and_the_bar(self):
        kickable = {i for i, s in self.spells.items() if _raw(s, "PreventionType") == PREVENTION_SILENCE
                    or _raw(s, "InterruptFlags")}
        self.assertEqual(kickable, set())
        bar = self.spells[BAR]
        self.assertEqual(bar["school"], SCHOOL_PHYSICAL)
        self.assertEqual(bar["cast_time_ms"], int(_value("kBeheadCastMs")))
        self.assertEqual(bar["effect1"]["type"], DUMMY_EFFECT)
        self.assertTrue(_raw(bar, "AttributesEx2") & ATTR2_DO_NOT_RESET_COMBAT_TIMERS)
        cast_times = {i for i, s in self.spells.items() if s.get("cast_time_ms")}
        self.assertEqual(cast_times, {BAR})

    def test_the_axe_is_a_resolve_copy(self):
        spell = self.spells[BEHEAD]
        self.assertEqual(spell["school"], SCHOOL_PHYSICAL)
        self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertIn((BEHEAD, RESOLVE), self.scripts)
        self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertTrue(_raw(spell, "AttributesEx") & ATTR1_NO_REDIRECTION)
        self.assertTrue(_raw(spell, "AttributesEx") & ATTR1_NO_REFLECTION)
        damaging = {i for i, s in self.spells.items() if (s.get("effect1") or {}).get("type") == SCHOOL_DAMAGE}
        self.assertEqual(damaging, {BEHEAD})

    def test_grievous_wound(self):
        spell = self.spells[WOUND]
        effect = spell["effect1"]
        self.assertEqual((spell["school"], spell["dispel"], spell["mechanic"], spell["duration_ms"]),
                         (SCHOOL_PHYSICAL, 0, 0, -1))
        self.assertEqual((effect["apply_aura"], int(effect["base_points"]), effect["die_sides"],
                          effect["amplitude"]),
                         (AURA_PERIODIC_DAMAGE, int(_value("kWoundTickHundredths")), 0, int(_value("kWoundTickMs"))))
        self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertTrue(_raw(spell, "AuraInterruptFlags") & CHANGE_MAP)
        self.assertIn((WOUND, REFFLAT_PERIODIC), self.scripts)
        self.assertIn((WOUND, WOUND_SCRIPT), self.scripts)
        self.assertIn(f"RegisterSpellScript({WOUND_SCRIPT});", self.cpp)
        self.assertEqual(_value("kWoundClearPct"), 95)

    def test_offerings_and_blood_price(self):
        offerings, price = self.spells[OFFERINGS], self.spells[BLOOD_PRICE]
        for spell in (offerings, price):
            effect = spell["effect1"]
            self.assertEqual((effect["apply_aura"], effect["die_sides"], effect["misc_value"]),
                             (AURA_MOD_DAMAGE_PERCENT_DONE, 0, 127))
            self.assertEqual((spell["dispel"], spell["duration_ms"]), (0, -1))
        self.assertEqual(int(offerings["effect1"]["base_points"]), int(_value("kOfferingsPctPerStack")))
        cap = re.search(r"kOfferingsCap = (\d+);", REWORK.read_text(encoding="utf-8"))
        self.assertEqual(_raw(offerings, "CumulativeAura"), int(cap.group(1)))
        # Blood Price: the script sets the amount (half the total); the counter shows up to 255.
        self.assertEqual(int(price["effect1"]["base_points"]), 0)
        self.assertEqual(_raw(price, "CumulativeAura"), int(_value("kAuraStackLimit")))
        self.assertEqual(_value("kBloodPricePctPerStack"), 0.5)
        self.assertIn("effect->ChangeAmount(want);", self.fight)

    def test_the_looks_are_vs(self):
        looks = {BEHEAD_LOOK: SV_BEHEAD, WOUND: SV_GRIEVOUS_STATE, WOUND_LOOK: SV_GRIEVOUS, OFFERINGS: SV_OFFERING,
                 BLOOD_PRICE: SV_OFFERING, CHAIN: SV_CHAIN}
        self.assertEqual({i: _raw(s, "SpellVisualID_1") for i, s in self.spells.items() if i in looks}, looks)
        for spell_id in set(self.spells) - set(looks):
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), 0, spell_id)
        self.assertTrue(_raw(self.spells[CHAIN], "AttributesEx") & ATTR1_IS_CHANNELED)
        self.assertIn("SetUInt32Value(UNIT_CHANNEL_SPELL, SPELL_PY_CHAIN)", self.cpp)

    def test_the_numbers(self):
        self.assertEqual(_pair("kBeheadPct"), (40, 60))
        self.assertEqual(_value("kBeheadWoundedPctH"), 150)
        self.assertEqual((_value("kBlockFirstMs"), _value("kBlockEveryMs"), _value("kBlockGapFirstMsH"),
                          _value("kBlockGapStepMsH")), (10000, 20000, 18000, 2000))
        self.assertEqual((_value("kSoakRadiusYd"), _value("kChainDistYd")), (2, 2.5))

    def test_the_cpp_keeps_the_rules(self):
        code = _code(self.cpp)
        # No assist calls, every tick before UpdateVictim (rule 27).
        self.assertRegex(code, r"ZulFarrak::NoAssist\(me\);[^\n]*\n\s+if \(!UpdateVictim\(\)\)")
        # The stage machine is the instance's: start and fail by message, never a slot write.
        self.assertIn("SetData(DATA_PYRAMID_START, PYRAMID_STAGE_BLOCK)", code)
        self.assertIn("SetData(DATA_PYRAMID_FAIL, PYRAMID_STAGE_BLOCK)", code)
        self.assertNotIn("SetBossState", code)
        self.assertIn("RegisterPyramidStage(PYRAMID_STAGE_BLOCK", code)
        # The crew only through BlyCrew.h (rule 28).
        for call in ("ZfCrew::TakePrisoner(", "ZfCrew::SparePrisoner(", "ZfCrew::ExecutePrisoner(",
                     "ZfCrew::PrisonerCandidates("):
            self.assertIn(call, code)
        self.assertNotIn("setFaction", code)
        self.assertNotIn("SetFaction", code)
        # Mechanics include the tank (rule 17); a soak carries no Weakened; the heroic rider is the wound.
        self.assertIn("spec.tankPct = pct;", code)
        self.assertIn("spec.weakened = false;", code)
        self.assertIn("spec.rider = _heroic ? uint32(SPELL_PY_GRIEVOUS_WOUND) : 0u;", code)
        # Bots: the Soak on the prisoner inside the top, wound-free on heroic; the healer rule.
        self.assertIn(".Within(BlockFloorBounds())", code)
        self.assertIn("_heroic ? ZfPyramid::WoundFree() : BossMechanics::Eligibility{};", code)
        self.assertIn("who.playersOnly = true;", code)
        self.assertIn("ZfPyramid::AddWoundHealRule(d, _heroic);", code)
        # RB-1: everything goes on reset, evade and death.
        cleanup = code[code.index("void Cleanup(char const* why)"):]
        for piece in ("AbortBlock(why)", "DespawnRope()", "Mechanic::Cancel(me, handle)", "_clock = BlockClock{}",
                      "ZfPyramid::RemoveSandfuryBuff(me)", "_arena.Reset()"):
            self.assertIn(piece, cleanup)
        for hook in ("void Reset() override", "void EnterEvadeMode(EvadeReason why) override",
                     "void JustDied(Unit* /*killer*/) override"):
            body = code[code.index(hook):]
            self.assertIn("Cleanup(", body[:body.index("\n    }")])
        self.assertNotIn("\t", self.cpp)
        self.assertNotIn("\t", self.fight)


class BlockSqlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8")

    def test_the_yell(self):
        self.assertIn("(7274, 2, 0, 'To the block, $n!', 14, 0, 100, ", self.sql)
        groups = re.findall(r"(?:SAY|YELL)_\w+\s*=\s*(\d+),", HEADER.read_text(encoding="utf-8"))
        self.assertEqual(sorted(int(g) for g in groups), [0, 1, 2])

    def test_the_rev_touches_only_the_new_text(self):
        code = "\n".join(line for line in self.sql.splitlines() if not line.startswith("--"))
        self.assertEqual(re.findall(r"(?:DELETE FROM|INSERT INTO|UPDATE) `(\w+)`", code),
                         ["creature_text", "creature_text"])
        self.assertIn("WHERE `CreatureID` = 7274 AND `GroupID` = 2;", code)


if __name__ == "__main__":
    unittest.main()
