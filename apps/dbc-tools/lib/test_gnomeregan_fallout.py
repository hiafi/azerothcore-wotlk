"""
Gnomeregan build WP-D2, Viscous Fallout: source/npcs/gnomeregan/viscous_fallout.py against its C++
(modules/mod-dungeon-bosses src/Gnomeregan/ViscousFalloutLogic.h, ViscousFalloutMachine.{h,cpp},
boss_viscous_fallout_rework.cpp), WP-V's _visuals.py, BM's gnomeregan-shapes drill table (when the BM worktree is on
hand) and its SQL rev.

Checks:
  - the spells sit in Fallout's slice (214340-214379) and ViscousFalloutLogic.h names the same ids;
  - 7079 is bound (SmartAI off) at 65,997 on the level 28 warrior base, immunity 1972, DamageModifier 1.7; the pool
    stalker 301130 is an inert helper wearing WP-V's nature disc, bound to its script, no heroic template;
  - nothing he casts is kickable (the kick and dispel table: Half-Life is a bar with InterruptFlags 0) and the bar
    keeps his swing timer; the only cast time is the bar's;
  - every hit is a Nature resolve copy (ignores caster modifiers, no redirection or reflection: rule 2, LESSONS L7);
  - the dose: +3% damage and healing done a stack, 255 shown, no dispel, NO_IMMUNITIES, CHANGE_MAP; the Poison is the
    only dispellable aura (Poison); the stun is 2 s; Saturated +50%; the glob's speed; the header's numbers;
  - the looks are V's (the stock glob 1484 is WRONG and never wired), the geiger click and the disc are V's;
  - the C++ keeps the rules: NoAssist first, every shape within the cave, the tank row on every hit, the machine
    from the contract, the cleanup;
  - the drill tags equal BM's MechanicDrill.h kGnTag* (Fallout's block);
  - the SQL rev writes the five emotes (type 41) and his addon auras (7940, no 9460) and touches nothing else.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_gnomeregan_fallout.py
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
from source.npcs.gnomeregan import _visuals as visuals  # noqa: E402

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Gnomeregan"
HEADER = MODULE_DIR / "ViscousFalloutLogic.h"
REWORK = MODULE_DIR / "GnomereganRework.h"
SCRIPT = MODULE_DIR / "boss_viscous_fallout_rework.cpp"
MACHINE = MODULE_DIR / "ViscousFalloutMachine.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_viscous_fallout_gnomeregan.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "gnomeregan"
BM_DRILL = Path(os.environ.get("BM_SRC", str(REPO_ROOT.parent / "boss-mechanics-gnomer" / "src"))) / "MechanicDrill.h"

SLICE = range(214340, 214380)
(DOSE, GLOW, SICKNESS, PULSE, STUN, VOLLEY, POISON, POOL, SLOUGH, SATURATED, LOB, OOZE, HALF_LIFE, HEAL, MELTDOWN,
 MELTDOWN_AURA, VOLLEY_LOOK) = range(214340, 214357)
FALLOUT, STALKER = 7079, 301130
WARRIOR_28_BASE = 853

SCHOOL_NATURE = 8
SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT, HEAL_EFFECT = 2, 6, 3, 10
AURA_DUMMY, AURA_PERIODIC_DAMAGE, AURA_MOD_STUN, AURA_MOD_DAMAGE_PERCENT_DONE = 4, 3, 12, 79
AURA_MOD_HEALING_DONE_PERCENT = 136
PREVENTION_SILENCE = 1
ATTR0_AURA_IS_DEBUFF, ATTR0_NO_IMMUNITIES = 0x04000000, 0x20000000
ATTR1_NO_REDIRECTION, ATTR1_NO_REFLECTION = 0x8, 0x80
ATTR2_DO_NOT_RESET_COMBAT_TIMERS = 0x00020000
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
CHANGE_MAP = 0x00080000
DISPEL_POISON = 4
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT_PERIODIC = "spell_dungeon_refflat_periodic"
UNIT_FLAG_NON_ATTACKABLE, UNIT_FLAG_NOT_SELECTABLE = 0x2, 0x02000000
WRONG_GLOB = 1484           # VISUALS-REPORT: Corrosive Ooze's SV, one puff (WRONG)


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


def _header_const(name: str) -> float:
    match = re.search(rf"\b{name} = (-?[\d.]+)f?;", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return float(match.group(1))


def _code(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith(("//", "*", "/*")))


class FalloutDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) == FALLOUT}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == STALKER}
        cls.models = [e for e in reg.creature_template_models if int(e["CreatureID"]) == STALKER]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.machine = MACHINE.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(DOSE, VOLLEY_LOOK + 1)))
        self.assertEqual(id_blocks.out_of_reservation("gnomeregan", {"spell": mine}), [])
        first = re.search(r"kSpellsFallout\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_VF_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", HEADER.read_text(encoding="utf-8"))
        self.assertEqual([SLICE.start + int(o) for o in offsets], mine)

    def test_fallout_and_the_stalker_are_bound(self):
        boss = self.edits[FALLOUT]
        self.assertEqual((boss["ScriptName"], boss["AIName"]), ("boss_viscous_fallout_rework", ""))
        health = re.search(r"kViscousFallout\{ (\d+), (\d+) \}", REWORK.read_text(encoding="utf-8"))
        self.assertEqual(math.ceil(WARRIOR_28_BASE * boss["HealthModifier"]), int(health.group(1)))
        self.assertEqual((boss["DamageModifier"], boss["CreatureImmunitiesId"]), (1.7, 1972))
        stalker = self.creatures[STALKER]
        self.assertEqual(stalker["ScriptName"], "npc_gnomer_pool_stalker")
        self.assertEqual(stalker["unit_flags"] & (UNIT_FLAG_NON_ATTACKABLE | UNIT_FLAG_NOT_SELECTABLE),
                         UNIT_FLAG_NON_ATTACKABLE | UNIT_FLAG_NOT_SELECTABLE)
        self.assertEqual(stalker.get("difficulty_entry_1", 0), 0)       # a helper: no heroic template
        self.assertEqual([int(m["CreatureDisplayID"]) for m in self.models], [visuals.DISPLAY_NATURE_DISC])
        self.assertEqual(int(_header_const("kDisplayPoolDisc")), visuals.DISPLAY_NATURE_DISC)
        self.assertEqual(_header_const("kDiscQuadRadius"), visuals.DISC_QUAD_RADIUS)
        self.assertEqual(int(_header_const("kSoundGeiger")), visuals.VF_CLICK)
        for script in ("boss_viscous_fallout_rework", "npc_gnomer_pool_stalker"):
            self.assertIn(f"RegisterDungeonReworkCreatureAI({script},", self.cpp)
        self.assertIn('GnomerTest::RegisterBoss("fallout"', self.cpp)

    def test_nothing_is_kickable_and_the_bar(self):
        kickable = {i for i, s in self.spells.items() if _raw(s, "PreventionType") == PREVENTION_SILENCE
                    or _raw(s, "InterruptFlags")}
        self.assertEqual(kickable, set())
        bar = self.spells[HALF_LIFE]
        self.assertEqual(bar["cast_time_ms"], int(_value("kHalfLifeCastMs")))
        self.assertEqual(bar["effect1"]["type"], DUMMY_EFFECT)
        self.assertTrue(_raw(bar, "AttributesEx2") & ATTR2_DO_NOT_RESET_COMBAT_TIMERS)
        self.assertEqual({i for i, s in self.spells.items() if s.get("cast_time_ms")}, {HALF_LIFE})

    def test_every_hit_is_a_nature_resolve_copy(self):
        damaging = {i for i, s in self.spells.items() if (s.get("effect1") or {}).get("type") == SCHOOL_DAMAGE}
        self.assertEqual(damaging, {SICKNESS, PULSE, VOLLEY, POOL, OOZE, MELTDOWN})
        for spell_id in damaging:
            spell = self.spells[spell_id]
            self.assertEqual(spell["school"], SCHOOL_NATURE, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
            self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS, spell_id)
            self.assertTrue(_raw(spell, "AttributesEx") & ATTR1_NO_REDIRECTION, spell_id)
            self.assertTrue(_raw(spell, "AttributesEx") & ATTR1_NO_REFLECTION, spell_id)
        heal = self.spells[HEAL]
        self.assertEqual(heal["effect1"]["type"], HEAL_EFFECT)
        self.assertTrue(_raw(heal, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)

    def test_the_dose(self):
        dose = self.spells[DOSE]
        self.assertEqual((dose["dispel"], dose["mechanic"], dose["duration_ms"], dose["school"]),
                         (0, 0, -1, SCHOOL_NATURE))
        self.assertTrue(dose["attributes"] & ATTR0_AURA_IS_DEBUFF and dose["attributes"] & ATTR0_NO_IMMUNITIES)
        auras = [(dose["effect1"]["apply_aura"], int(dose["effect1"]["base_points"]), dose["effect1"]["die_sides"]),
                 (dose["effect2"]["apply_aura"], int(dose["effect2"]["base_points"]), dose["effect2"]["die_sides"])]
        pct = int(_value("kDosePctPerStack"))
        self.assertEqual(auras, [(AURA_MOD_DAMAGE_PERCENT_DONE, pct, 0), (AURA_MOD_HEALING_DONE_PERCENT, pct, 0)])
        self.assertEqual(dose["effect1"]["misc_value"], 127)
        self.assertEqual(_raw(dose, "CumulativeAura"), int(_value("kAuraStackLimit")))
        self.assertTrue(_raw(dose, "AuraInterruptFlags") & CHANGE_MAP)
        for spell_id in (GLOW, MELTDOWN_AURA):
            self.assertEqual(self.spells[spell_id]["dispel"], 0)
            self.assertTrue(self.spells[spell_id]["attributes"] & ATTR0_NO_IMMUNITIES)
            self.assertTrue(_raw(self.spells[spell_id], "AuraInterruptFlags") & CHANGE_MAP)
        # The dose is the machine's: the boss creates it through the contract with Irradiated.
        self.assertIn("GnomereganMachines::MakeDoseField(", self.cpp)
        self.assertIn("spec.auraSpellId = SPELL_VF_IRRADIATED;", self.cpp)
        self.assertIn("std::unique_ptr<DoseField> MakeDoseField(MachineOwner const& owner, DoseSpec spec)",
                      self.machine)

    def test_auras_and_riders(self):
        poison = self.spells[POISON]
        self.assertEqual((poison["dispel"], poison["duration_ms"]), (DISPEL_POISON, int(_value("kVolleyPoisonMs"))))
        effect = poison["effect1"]
        self.assertEqual((effect["apply_aura"], int(effect["base_points"]), effect["die_sides"], effect["amplitude"]),
                         (AURA_PERIODIC_DAMAGE, int(_value("kVolleyPoisonHundredths")), 0,
                          int(_value("kVolleyPoisonTickMs"))))
        self.assertIn((POISON, REFFLAT_PERIODIC), self.scripts)
        self.assertTrue(_raw(poison, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        # The Poison is the only dispellable aura (rule 27: the dose, Sickness, Meltdown are not).
        self.assertEqual({i for i, s in self.spells.items() if s.get("dispel")}, {POISON})
        stun = self.spells[STUN]
        self.assertEqual((stun["effect1"]["apply_aura"], stun["duration_ms"], stun["mechanic"]),
                         (AURA_MOD_STUN, int(_value("kSicknessStunMs")), 12))
        saturated = self.spells[SATURATED]
        self.assertEqual((saturated["effect1"]["apply_aura"], int(saturated["effect1"]["base_points"]),
                          saturated["dispel"], saturated["mechanic"]),
                         (AURA_MOD_DAMAGE_PERCENT_DONE, int(_value("kSaturatedDamagePct")), 0, 0))
        self.assertEqual(_raw(self.spells[LOB], "Speed"), _value("kGlobMissileSpeed"))

    def test_the_looks_are_vs(self):
        looks = {DOSE: visuals.VF_DOSE, GLOW: visuals.VF_DOSE_BRIGHT, SICKNESS: visuals.VF_SICKNESS,
                 STUN: visuals.VF_VOMIT, SLOUGH: visuals.VF_SLOUGH, SATURATED: visuals.VF_DOSE_BRIGHT,
                 LOB: visuals.VF_GLOB, VOLLEY_LOOK: visuals.VF_VOLLEY}
        self.assertEqual({i: _raw(s, "SpellVisualID_1") for i, s in self.spells.items() if i in looks}, looks)
        for spell_id in set(self.spells) - set(looks):
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), 0, spell_id)
        self.assertNotIn(WRONG_GLOB, {_raw(s, "SpellVisualID_1") for s in self.spells.values()})

    def test_the_numbers(self):
        self.assertEqual(_pair("kSicknessAt"), (10, 0))
        self.assertEqual(_pair("kDrainEveryMs"), (3000, 0))
        self.assertEqual((_pair("kLeakAt"), _pair("kMeltdownAt")), ((0, 10), (0, 20)))
        self.assertEqual((_value("kSicknessPct"), _value("kSicknessPulsePct"), _value("kSicknessPulseYd")),
                         (40, 20, 8))
        self.assertEqual((_pair("kBeatFirstMs"), _pair("kBeatEveryMs")), ((15000, 12000), (15000, 12000)))
        self.assertEqual((_value("kVolleyPct"), _value("kVolleyPctPerDoseH"), _value("kVolleyDose")), (10, 3, 2))
        self.assertEqual((_value("kVolleyPoolYd"), _value("kVolleyPoolArmMs")), (4, 1500))
        self.assertEqual(_pair("kVolleyPoolLifeMs"), (20000, 30000))
        self.assertEqual((_value("kSloughYd"), _value("kSloughSwellMs"), _value("kSloughGrowYdH"),
                          _value("kSloughGrowEveryMsH")), (7, 2000, 1, 10000))
        self.assertEqual((_value("kPoolPct"), _value("kPoolDose")), (8, 1))
        self.assertEqual((_value("kSaturatedVolleyDose"), _value("kSaturatedPollMs"),
                          _value("kSaturatedPulseEveryMsH")), (2, 500, 2000))
        self.assertEqual((_value("kOozeFirstMs"), _value("kOozeEveryMs"), _value("kOozeWarnMs"), _value("kOozeYd")),
                         (5000, 10000, 2000, 5))
        self.assertEqual((_pair("kOozeCount"), _pair("kOozePct"), _pair("kOozeDose")), ((1, 2), (40, 60), (3, 5)))
        self.assertEqual((_value("kOozePoolYd"), _value("kOozePoolLifeMs")), (5, 30000))
        self.assertEqual((_value("kLeakEveryMs"), _value("kLeakPoolYd")), (10000, 4))
        self.assertEqual((_value("kMeltdownPct"), _value("kMeltdownYd")), (5, 6))
        self.assertEqual((_value("kHalfLifeFirstMs"), _value("kHalfLifeEveryMs"), _value("kHalfLifeYd"),
                          _value("kHalfLifeHealPctPerDose"), _value("kHalfLifeBotStacks")), (30000, 30000, 10, 0.5, 8))

    def test_the_cpp_keeps_the_rules(self):
        code = _code(self.cpp)
        # No assist calls, every tick before UpdateVictim (rule 29).
        self.assertRegex(code, r"GnomereganRework::NoAssist\(me\);[^\n]*\n\s+if \(!UpdateVictim\(\)\)")
        # Every registry shape keeps the bots on the cave floor (rule 14).
        shapes = len(re.findall(r"Mechanic::(?:Zone|Circle|Spread|Stack)\(", code))
        self.assertGreaterEqual(shapes, 5)
        self.assertEqual(code.count(".Within(FalloutFloorBounds())"), shapes)
        # Mechanics include the tank (rule 17): every hit sets the tank row.
        self.assertEqual(code.count("spec.pct = ") + code.count("hit.pct = ") + code.count("pulse.pct = "),
                         code.count("spec.tankPct = ") + code.count("hit.tankPct = ") + code.count("pulse.tankPct = "))
        self.assertIn(".TankDamage(pct)", code)
        self.assertIn(".TankDamage(Tune::kMeltdownPct)", code)
        # Weakened where the Penalty column says (Sickness, the glob), nowhere else.
        self.assertIn("hit.weakened = true;", code)
        self.assertEqual(code.count(".Weakened()"), 1)
        # No registration inside the registry's resolve: the glob's pool is queued.
        self.assertIn("ai._queued.push_back({ PoolKind::Ooze, at });", code)
        # RB-1: everything goes on reset, evade and death.
        cleanup = code[code.index("void Cleanup(char const* why)"):]
        for piece in ("_dose->Clear()", "EndMeltdown(raw, handle)", "DropLook(look)", "_pools.Clear()",
                      "Mechanic::Cancel(me, handle)", "RemoveAurasDueToSpell(SPELL_VF_SATURATED)", "_arena.Reset()"):
            self.assertIn(piece, cleanup)
        for hook in ("void Reset() override", "void EnterEvadeMode(EvadeReason why) override",
                     "void JustDied(Unit* killer) override"):
            body = code[code.index(hook):]
            self.assertIn("Cleanup(", body[:body.index("\n    }")])
        for text in (self.cpp, self.machine, HEADER.read_text(encoding="utf-8")):
            self.assertNotIn("\t", text)

    @unittest.skipUnless(BM_DRILL.exists(), "BM worktree not on hand (set BM_SRC)")
    def test_drill_tags_match_bm(self):
        drill = BM_DRILL.read_text(encoding="utf-8")
        header = HEADER.read_text(encoding="utf-8")
        pairs = {"kGnTagSlough": "TAG_VF_SLOUGH", "kGnTagSaturated": "TAG_VF_SATURATED",
                 "kGnTagVolleyPool": "TAG_VF_VOLLEY_POOL", "kGnTagOoze": "TAG_VF_OOZE",
                 "kGnTagLeaking": "TAG_VF_LEAKING", "kGnTagMeltdown": "TAG_VF_MELTDOWN",
                 "kGnTagHalfLife": "TAG_VF_HALF_LIFE", "kGnTagHalfLifeOut": "TAG_VF_HALF_LIFE_OUT"}
        for bm, mine in pairs.items():
            theirs = re.search(rf"\b{bm} = (\d+);", drill)
            ours = re.search(rf"\b{mine}\s*= (\d+),", header)
            self.assertTrue(theirs and ours, bm)
            self.assertEqual(int(theirs.group(1)), int(ours.group(1)), bm)
        numbers = {"kGnSloughYd": "kSloughYd", "kGnVolleyPoolYd": "kVolleyPoolYd", "kGnOozeYd": "kOozeYd",
                   "kGnHalfLifeStacks": "kHalfLifeBotStacks", "kGnHalfLifeYd": "kHalfLifeYd",
                   "kGnMeltdownYd": "kMeltdownYd"}
        for bm, mine in numbers.items():
            theirs = re.search(rf"\b{bm} = ([\d.]+)f?;", drill)
            self.assertTrue(theirs, bm)
            self.assertEqual(float(theirs.group(1)), _value(mine), bm)


class FalloutSqlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8")

    def test_the_emotes(self):
        texts = {
            0: "%s sloughs off a pool of fallout!",
            1: "$n is overcome by Radiation Sickness!",
            2: "%s begins to decay. Stand close to shed your dose!",
            3: "$n is leaking fallout!",
            4: "$n is melting down!",
        }
        for group, text in texts.items():
            self.assertIn(f"(7079, {group}, 0, '{text}', 41, 0, 100, ", self.sql)
        groups = re.findall(r"EMOTE_\w+\s*=\s*(\d+),", HEADER.read_text(encoding="utf-8"))
        self.assertEqual(sorted(int(g) for g in groups), [0, 1, 2, 3, 4])

    def test_the_rev_touches_only_its_rows(self):
        code = "\n".join(line for line in self.sql.splitlines() if not line.startswith("--"))
        self.assertEqual(re.findall(r"(?:DELETE FROM|INSERT INTO|UPDATE) `(\w+)`", code),
                         ["creature_template_addon", "creature_addon", "creature_text", "creature_text"])
        self.assertIn("WHERE `CreatureID` = 7079 AND `GroupID` BETWEEN 0 AND 4;", code)
        # template + spawn rows; the heroic copy's addon is the write run's copy (INT dedupe: no join here)
        self.assertEqual(code.count("SET `auras` = '7940'"), 2)
        self.assertNotIn("`cta`", code)
        self.assertNotIn("9460", code)
        self.assertIn("WHERE `guid` = 30137;", code)


if __name__ == "__main__":
    unittest.main()
