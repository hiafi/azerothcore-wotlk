"""
Ragefire Chasm build WP-D2, Jergosh the Invoker: source/npcs/ragefire_chasm/jergosh.py against its C++
(modules/mod-dungeon-bosses src/RagefireChasm/JergoshLogic.h, RagefireChasmRework.h namespace Jergosh,
boss_jergosh_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in his slice (213580-213609) and JergoshLogic.h names the same ids;
  - Jergosh 11518 is bound (SmartAI off) at 21,490 on the level 16 mage base; the Soul Wisp 300986 is declared,
    scripted, untouchable and shown;
  - Immolate and Drain Soul are kickable (rule 25) and no must-play bar shares a school with them: Conflagrate is Arcane
    and uninterruptible;
  - Immolate's ticks and duration, the times, the Soul-sick and Tithe values are the header's; every damage spell
    ignores caster modifiers and takes the script's base point; no stock spell is scaled but cast as stock (rule 15);
  - the looks are V's;
  - the C++ registers the burn Spread and the wisp as G1's drill does, and cleans up;
  - the SQL rev writes the four texts (0 yell, 1-3 emotes type 41) and touches nothing else.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_ragefire_chasm_jergosh.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "RagefireChasm"
HEADER = MODULE_DIR / "JergoshLogic.h"
REWORK = MODULE_DIR / "RagefireChasmRework.h"
SCRIPT = MODULE_DIR / "boss_jergosh_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_jergosh_ragefire_chasm.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "ragefire_chasm"

SLICE = range(213580, 213610)
(IMMOLATE, CONFLAGRATE_CAST, CONFLAGRATE, BEARER, DRAIN_SOUL, SOUL_TEAR, SOUL_SICK, TITHE, OFFERING,
 FEED_LOOK) = range(213580, 213590)
JERGOSH, SOUL_WISP = 11518, 300986
MAGE_16_BASE = 307          # creature_classlevelstats level 16 class 8 basehp0

SCHOOL_FIRE, SCHOOL_SHADOW, SCHOOL_ARCANE = 4, 32, 64
SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT = 2, 6, 3
AURA_PERIODIC_DAMAGE, AURA_DUMMY, AURA_MOD_DAMAGE_PCT, AURA_MOD_HEALING_PCT = 3, 4, 79, 118
DISPEL_MAGIC = 1
PREVENTION_SILENCE = 1
CHANNEL_KICK = 0x08
ATTR1_IS_CHANNELED = 0x4
ATTR2_IGNORE_LOS = 0x4
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
CHANGE_MAP = 0x00080000
RESOLVE = "spell_boss_mechanics_resolve"
# V's picks (_visuals.py).
SV_IMMOLATE, SV_BURST, SV_DRAIN, SV_TEAR, SV_SICK, SV_TITHE, SV_PATCH = 46, 5199, 12656, 7180, 561, 11821, 90601
STOCK_IMMOLATE = 20800


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
    """RagefireChasmRework.h's `namespace Jergosh` block."""
    text = REWORK.read_text(encoding="utf-8")
    start = text.index("namespace Jergosh")
    return text[start:text.index("namespace Bazzalan", start)]


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


class JergoshDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) == JERGOSH}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == SOUL_WISP}
        cls.models = [e for e in reg.creature_template_models if int(e["CreatureID"]) == SOUL_WISP]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(IMMOLATE, FEED_LOOK + 1)))
        self.assertEqual(id_blocks.out_of_reservation("ragefire_chasm", {"spell": mine}), [])
        first = re.search(r"kSpellsJergosh\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_JR_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", HEADER.read_text(encoding="utf-8"))
        self.assertEqual([SLICE.start + int(o) for o in offsets], mine)

    def test_jergosh_is_bound(self):
        boss = self.edits[JERGOSH]
        self.assertEqual(boss["ScriptName"], "boss_jergosh_rework")
        self.assertEqual(boss["AIName"], "")
        self.assertEqual(math.ceil(MAGE_16_BASE * boss["HealthModifier"]), int(_pair("kHealth")[0]))
        self.assertEqual(boss["DamageModifier"], 1.95)
        self.assertEqual(boss["CreatureImmunitiesId"], 1972)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_jergosh_rework,", self.cpp)
        self.assertIn('RfcTest::RegisterBoss("jergosh"', self.cpp)

    def test_the_wisp(self):
        wisp = self.creatures[SOUL_WISP]
        self.assertEqual(wisp["ScriptName"], "npc_rfc_soul_wisp")
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_rfc_soul_wisp,", self.cpp)
        self.assertEqual(wisp["unit_flags"], 0x2 | 0x02000000)       # not attackable, not selectable
        self.assertEqual(wisp["flags_extra"] & 0x80, 0)              # never an invisible trigger
        self.assertEqual(len(self.models), 1)
        self.assertEqual(self.models[0]["CreatureDisplayID"], 12432)
        self.assertEqual(float(self.models[0]["DisplayScale"]), _value("kWispScale"))

    def test_kickable_casts_and_the_bar(self):
        immolate, bar, drain = self.spells[IMMOLATE], self.spells[CONFLAGRATE_CAST], self.spells[DRAIN_SOUL]
        self.assertEqual(_raw(immolate, "InterruptFlags"), 15)
        self.assertEqual(_raw(immolate, "PreventionType"), PREVENTION_SILENCE)
        self.assertEqual(_raw(drain, "ChannelInterruptFlags"), CHANNEL_KICK)
        self.assertEqual(_raw(drain, "PreventionType"), PREVENTION_SILENCE)
        self.assertTrue(_raw(drain, "AttributesEx") & ATTR1_IS_CHANNELED)
        self.assertEqual(_raw(bar, "InterruptFlags"), 0)
        self.assertEqual(_raw(bar, "PreventionType"), 0)
        self.assertEqual(bar["effect1"]["type"], DUMMY_EFFECT)
        kickable = [s for s in self.spells.values() if _raw(s, "PreventionType") == PREVENTION_SILENCE]
        self.assertEqual({int(s["id"]) for s in kickable}, {IMMOLATE, DRAIN_SOUL})
        # Rule 25 as corrected: a kick refuses every non-triggered cast of the school it locked.
        self.assertEqual((immolate["school"], drain["school"], bar["school"]),
                         (SCHOOL_FIRE, SCHOOL_SHADOW, SCHOOL_ARCANE))
        self.assertTrue(all(s["school"] != bar["school"] for s in kickable))
        self.assertEqual(immolate["cast_time_ms"], int(_value("kImmolateCastMs")))
        self.assertEqual(bar["cast_time_ms"], int(_value("kConflagrateCastMs")))
        self.assertEqual(drain["duration_ms"], int(_value("kDrainSoulChannelMs")))

    def test_immolate(self):
        spell = self.spells[IMMOLATE]
        hit, dot = spell["effect1"], spell["effect2"]
        self.assertEqual(hit["type"], SCHOOL_DAMAGE)
        self.assertEqual((dot["type"], dot["apply_aura"]), (APPLY_AURA, AURA_PERIODIC_DAMAGE))
        self.assertEqual(dot["amplitude"], int(_value("kImmolateTickMs")))
        self.assertEqual(spell["duration_ms"], int(_value("kImmolateDurationMs")))
        self.assertEqual(spell["duration_ms"] // dot["amplitude"], 7)
        self.assertEqual(spell["dispel"], DISPEL_MAGIC)
        for effect in (hit, dot):
            self.assertEqual((int(effect["base_points"]), int(effect["die_sides"])), (0, 0))
        self.assertEqual((_value("kImmolateFlatDirect"), _value("kImmolateFlatTick")), (56, 16))
        self.assertTrue(_raw(spell, "AuraInterruptFlags") & CHANGE_MAP)
        self.assertTrue(_raw(spell, "AttributesEx2") & ATTR2_IGNORE_LOS)
        self.assertTrue(_raw(spell, "AttributesEx2") & 0x00020000)   # does not reset his swing timer

    def test_the_hits(self):
        for spell_id, school, visual in ((BEARER, SCHOOL_FIRE, SV_BURST), (SOUL_TEAR, SCHOOL_SHADOW, SV_TEAR)):
            spell = self.spells[spell_id]
            effect = spell["effect1"]
            self.assertEqual(spell["school"], school)
            self.assertEqual((effect["type"], int(effect["base_points"]), int(effect["die_sides"])),
                             (SCHOOL_DAMAGE, 0, 0))
            self.assertEqual(_raw(spell, "SpellVisualID_1"), visual)
        rings = self.spells[CONFLAGRATE]
        self.assertEqual(rings["school"], SCHOOL_FIRE)
        self.assertEqual(self.scripts, {(CONFLAGRATE, RESOLVE)})
        for spell in self.spells.values():
            effects = [spell.get(f"effect{i}") or {} for i in (1, 2, 3)]
            if any(e.get("type") == SCHOOL_DAMAGE or e.get("apply_aura") == AURA_PERIODIC_DAMAGE for e in effects):
                self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS, spell["id"])

    def test_the_auras(self):
        sick, tithe, patch = self.spells[SOUL_SICK], self.spells[TITHE], self.spells[OFFERING]
        self.assertEqual(sick["effect1"]["apply_aura"], AURA_MOD_HEALING_PCT)
        self.assertEqual(int(sick["effect1"]["base_points"]), -int(_value("kSoulSickHealingPct")))
        self.assertEqual(sick["duration_ms"], int(_value("kSoulSickMs")))
        self.assertEqual(sick["dispel"], 0)
        self.assertTrue(_raw(sick, "AuraInterruptFlags") & CHANGE_MAP)
        self.assertEqual(tithe["effect1"]["apply_aura"], AURA_MOD_DAMAGE_PCT)
        self.assertEqual(int(tithe["effect1"]["base_points"]), int(_value("kTithePct")))
        self.assertEqual(tithe["effect1"]["misc_value"], 127)
        cap = re.search(r"kTitheMaxStacks = (\d+);", HEADER.read_text(encoding="utf-8"))
        self.assertEqual(_raw(tithe, "CumulativeAura"), int(cap.group(1)))
        self.assertEqual((sick["effect1"]["die_sides"], tithe["effect1"]["die_sides"]), (0, 0))
        self.assertEqual((tithe["duration_ms"], patch["duration_ms"]), (-1, -1))
        self.assertEqual(self.spells[DRAIN_SOUL]["effect1"]["apply_aura"], AURA_DUMMY)

    def test_the_looks_are_vs(self):
        looks = {IMMOLATE: SV_IMMOLATE, CONFLAGRATE_CAST: SV_IMMOLATE, CONFLAGRATE: SV_BURST, BEARER: SV_BURST,
                 DRAIN_SOUL: SV_DRAIN, SOUL_TEAR: SV_TEAR, SOUL_SICK: SV_SICK, TITHE: SV_TITHE, OFFERING: SV_PATCH,
                 FEED_LOOK: SV_TEAR}
        self.assertEqual({i: _raw(s, "SpellVisualID_1") for i, s in self.spells.items()}, looks)

    def test_the_cpp_registers_the_spec(self):
        code = _code(self.cpp)
        # No assist calls (the flag stops the first only), every tick before UpdateVictim.
        self.assertRegex(code, r"me->SetAssistanceTimer\(0\);[^\n]*\n\s+if \(!UpdateVictim\(\)\)")
        # The random picks stay in the hall, and a wisp has the hall's height whoever its owner is.
        self.assertIn("std::vector<uint64> skip = OffHall();", code)
        self.assertIn("PickPlayer(me, DrainSoulPick(OffHall()))", code)
        self.assertIn("OnFloor(me, start, kJergoshSpawn.z)", code)
        # Lost rings are judged by the clock before the tick's.
        self.assertIn("RingsLost(before, _conflagrate.endsAt)", code)
        self.assertNotIn(str(STOCK_IMMOLATE), code)
        # JR2: G1's burn-spread registration, the tank included, the bearers' hit and the spread by script.
        self.assertIn(".SelfTrigger(SPELL_JR_IMMOLATE, 1).School(SPELL_SCHOOL_FIRE).Damage(pct).TankDamage(pct)", code)
        self.assertIn(".Spell(SPELL_JR_CONFLAGRATE).Weakened().Tag(TAG_JR_CONFLAGRATE)", code)
        self.assertIn("BurningAfter(hits, _heroic)", code)
        self.assertNotIn("TankExempt", code)
        # JR5: the kit's CrawlPickups as G1's wisp-soak row (touch 2 yd, 3 yd/s, healers last), anyone may catch.
        self.assertIn("order.roleLast = BossMechanics::Role::Healer;", code)
        self.assertIn("spec.radius = Tune::kWispTouchYd;", code)
        self.assertNotIn("spec.who", code)
        self.assertIn("void OnChannelFinished(SpellInfo const* spell) override", code)
        # Boss data.
        self.assertIn("d.dispels.emplace_back(SPELL_JR_IMMOLATE, kImmolateDispelPriority)", code)
        self.assertEqual(code.count("d.interrupts.emplace_back(NPC_JERGOSH"), 2)
        # RB-1: everything goes on reset, evade and death.
        cleanup = code[code.index("void Cleanup()"):]
        for piece in ("_wisps.Clear(me)", "summons.DespawnAll()", "SPELL_JR_TITHE", "SPELL_JR_IMMOLATE",
                      "SPELL_JR_SOUL_SICK", "SPELL_JR_DRAIN_SOUL", "_conflagrate.rings", "SetObjectScale"):
            self.assertIn(piece, cleanup)
        self.assertNotIn("\t", self.cpp)

    def test_the_immolate_cadence_and_the_kick_lock(self):
        """User rulings 2026-11-25: every 3 s on both difficulties, none while three burn, a kick's lockout is 2 s."""
        self.assertEqual(_pair("kImmolateFirstMs"), (3000, 3000))
        self.assertEqual(_pair("kImmolateEveryMs"), (3000, 3000))
        self.assertEqual((_value("kImmolateMaxBurning"), _value("kKickLockMs")), (3, 2000))
        code = _code(self.cpp)
        cast = code[code.index("bool CastImmolate(Player* forced)"):]
        self.assertLess(cast.index("ImmolateFull(burning.size())"), cast.index("PickPlayer("))
        # Only an existing lock is cut (a silence makes none), after the engine's own.
        self.assertRegex(code, r"if \(!me->IsSpellProhibited\(school\)\)\s+return false;\s+"
                               r"me->ProhibitSpellSchool\(school, Tune::kKickLockMs\);")
        failed = code[code.index("void OnSpellFailed"):code.index("void OnChannelFinished")]
        self.assertEqual(failed.count("ShortenKickLock(spell)"), 2)
        # The engine locks before it interrupts (the hook sees the lock), and OnSpellFailed is the interrupt's.
        effects = (REPO_ROOT / "src/server/game/Spells/SpellEffects.cpp").read_text(encoding="utf-8")
        effect = effects[effects.index("void Spell::EffectInterruptCast("):]
        self.assertLess(effect.index("ProhibitSpellSchool("), effect.index("InterruptSpell("))
        unit = (REPO_ROOT / "src/server/game/Entities/Unit/Unit.cpp").read_text(encoding="utf-8")
        interrupt = unit[unit.index("void Unit::InterruptSpell("):]
        self.assertIn("OnSpellFailed(", interrupt[:interrupt.index("\n}")])

    def test_drill_tags(self):
        header = HEADER.read_text(encoding="utf-8")
        self.assertRegex(header, r"TAG_JR_CONFLAGRATE\s*=\s*6,")
        self.assertRegex(header, r"TAG_JR_WISP\s*=\s*7,")


class JergoshSqlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8")

    def test_the_texts(self):
        self.assertRegex(self.sql, r"\(11518, 0, 0, 'The Searing Blade will purge you in fire!', 14, 0, 100, ")
        for group, text in ((1, "%s spreads his hands, and the flames on his victims flare!"),
                            (2, "%s begins to tear the soul from $n!"),
                            (3, "The Hungerer feeds, and %s grows stronger!")):
            self.assertIn(f"(11518, {group}, 0, '{text}', 41, 0, 100, ", self.sql)
        groups = re.findall(r"(?:YELL|EMOTE)_JERGOSH_\w+\s*=\s*(\d+),", REWORK.read_text(encoding="utf-8"))
        self.assertEqual(sorted(int(g) for g in groups), [0, 1, 2, 3])

    def test_the_rev_touches_only_the_texts(self):
        code = "\n".join(line for line in self.sql.splitlines() if not line.startswith("--"))
        self.assertEqual(re.findall(r"(?:DELETE FROM|INSERT INTO|UPDATE) `(\w+)`", code),
                         ["creature_text", "creature_text"])


if __name__ == "__main__":
    unittest.main()
