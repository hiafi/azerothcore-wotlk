"""
Ragefire Chasm build WP-D3, Bazzalan: source/npcs/ragefire_chasm/bazzalan.py against its C++ (modules/
mod-dungeon-bosses src/RagefireChasm/BazzalanLogic.h, boss_bazzalan_rework.cpp, RagefireChasmRework.h namespace
Bazzalan) and its SQL rev.

Checks:
  - the spells sit in his slice (213610-213649) and BazzalanLogic.h names the same ids;
  - the interrupt rule (handoff s3.5 rule 25): the kickable casts are Physical and Nature with the kick recipe, every
    must-play bar is Shadow and not interruptible, 2 s; the Sinister Strike copy is cast triggered;
  - the bleed, the poisons and the combo points carry the header's numbers; every damage spell ignores caster modifiers
    and has a range; the scripts bound are registered;
  - the looks are V's;
  - the C++ registers the fans as the drill does (tank included, Weakened, the ridge bounds, the rider on heroic only),
    keeps the boss data of the spec and never casts the stock spells;
  - the SQL rev writes the six texts of the build spec and nothing else.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_ragefire_chasm_bazzalan.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "RagefireChasm"
HEADER = MODULE_DIR / "BazzalanLogic.h"
REWORK = MODULE_DIR / "RagefireChasmRework.h"
SCRIPT = MODULE_DIR / "boss_bazzalan_rework.cpp"
HEROIC = TOOL_ROOT / "source" / "world" / "dungeons" / "ragefire_chasm.py"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_bazzalan_ragefire_chasm.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "ragefire_chasm"

SLICE = range(213610, 213650)
(STRIKE, COMBO, EVISCERATE, RUPTURE_CAST, RUPTURE_LOOK, RUPTURE, RUPTURE_HEROIC, FAN_CAST, FAN, ENVENOM,
 SHADOWSTEP_CAST, SHADOWSTEP_LOOK, DEADLY, WOUND, CRIPPLING) = range(213610, 213625)

SCHOOL_PHYSICAL, SCHOOL_NATURE, SCHOOL_SHADOW = 1, 8, 32
SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT = 2, 6, 3
AURA_PERIODIC_DAMAGE, AURA_DUMMY, AURA_MOD_DECREASE_SPEED, AURA_MOD_HEALING_PCT = 3, 4, 33, 118
DISPEL_POISON = 4
MECHANIC_BLEED, MECHANIC_SNARE = 15, 11
ATTR0_NO_IMMUNITIES = 0x20000000
ATTR1_NO_REDIRECTION = 0x00000008
ATTR1_NO_REFLECTION = 0x00000080
ATTR3_ALWAYS_HIT = 0x00040000
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
AURA_INTERRUPT_CHANGE_MAP = 0x00080000
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT_PERIODIC = "spell_dungeon_refflat_periodic"
HEROIC_BOSS_MELEE = 2_500      # the tier's swing (lib/test_ragefire_chasm_heroic.py pins it)
# V's picks (_visuals.py).
LOOKS = {
    STRIKE: 253, EVISCERATE: 90373, RUPTURE_LOOK: 90374, RUPTURE: 15286, RUPTURE_HEROIC: 15286, FAN_CAST: 90376,
    ENVENOM: 90375, SHADOWSTEP_LOOK: 8262, DEADLY: 14987, WOUND: 5100, CRIPPLING: 5100,
}
TEXTS = {
    0: (14, "Thrall''s pups come sniffing? The Blade cuts both ways!"),
    1: (41, "%s readies an Eviscerate!"),
    2: (41, "%s readies a Rupture on $n!"),
    3: (41, "%s readies a Fan of Knives!"),
    4: (41, "%s readies an Envenom!"),
    5: (41, "%s vanishes and appears behind $n!"),
}


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


def _attributes(spell: dict) -> int:
    return int(spell.get("attributes") or 0) | int(_raw(spell, "Attributes"))


def _tuning() -> str:
    text = REWORK.read_text(encoding="utf-8")
    return re.search(r"namespace Bazzalan\n    \{(.*?)\n    \}\n\n    namespace", text, re.S).group(1)


def _tune(name: str) -> float:
    match = re.search(rf"{name}\s*=\s*(-?[\d.]+)f?;", _tuning())
    assert match, name
    return float(match.group(1))


def _code(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith(("//", "*", "/*")))


class BazzalanDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.cpp = _code(SCRIPT.read_text(encoding="utf-8"))

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(STRIKE, CRIPPLING + 1)))
        self.assertEqual(id_blocks.out_of_reservation("ragefire_chasm", {"spell": mine}), [])
        offsets = re.findall(r"SPELL_BZ_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", HEADER.read_text(encoding="utf-8"))
        self.assertEqual([SLICE.start + int(o) for o in offsets], mine)

    def test_the_must_play_bars(self):
        kickable = {int(self.spells[i]["school"]) for i in (EVISCERATE, ENVENOM)}
        self.assertEqual(kickable, {SCHOOL_PHYSICAL, SCHOOL_NATURE})
        for spell_id in (RUPTURE_CAST, FAN_CAST, SHADOWSTEP_CAST):
            bar = self.spells[spell_id]
            with self.subTest(spell=spell_id):
                self.assertEqual(int(bar["school"]), SCHOOL_SHADOW)
                self.assertNotIn(int(bar["school"]), kickable)      # a kick never locks it (rule 25)
                self.assertEqual(bar["effect1"]["type"], DUMMY_EFFECT)
                self.assertEqual(_raw(bar, "InterruptFlags"), 0)
                self.assertEqual(_raw(bar, "PreventionType"), 0)
                self.assertEqual(bar["cast_time_ms"], _tune("kFinisherCastMs"))
        self.assertEqual(_tune("kFinisherCastMs"), _tune("kFanWarnMs"))
        self.assertEqual(_tune("kFinisherCastMs"), _tune("kShadowstepWarnMs"))

    def test_the_kickable_casts(self):
        for spell_id, script in ((EVISCERATE, "spell_rfc_bazzalan_eviscerate"),
                                 (ENVENOM, "spell_rfc_bazzalan_envenom")):
            spell = self.spells[spell_id]
            with self.subTest(spell=spell_id):
                self.assertEqual(_raw(spell, "InterruptFlags"), 15)
                self.assertEqual(_raw(spell, "PreventionType"), 1)
                self.assertEqual(spell["cast_time_ms"], _tune("kFinisherCastMs"))
                self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE)
                self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_ALWAYS_HIT)
                self.assertIn((spell_id, script), self.scripts)

    def test_the_strike_is_triggered(self):
        strike = self.spells[STRIKE]
        self.assertEqual(int(strike["school"]), SCHOOL_PHYSICAL)
        self.assertIn("me->CastSpell(victim, SPELL_BZ_SINISTER_STRIKE, true);", self.cpp)
        self.assertIn((STRIKE, "spell_rfc_bazzalan_sinister_strike"), self.scripts)

    def test_damage_spells_ignore_caster_modifiers(self):
        for spell_id in (STRIKE, EVISCERATE, RUPTURE, RUPTURE_HEROIC, FAN, ENVENOM, DEADLY):
            self.assertTrue(_raw(self.spells[spell_id], "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS, spell_id)

    def test_every_targeted_spell_has_a_range(self):
        for spell_id in (STRIKE, EVISCERATE, RUPTURE_LOOK, RUPTURE, RUPTURE_HEROIC, ENVENOM, DEADLY, WOUND, CRIPPLING):
            self.assertEqual(self.spells[spell_id]["range_yards"], 100.0, spell_id)

    def test_nothing_on_a_player_is_reflected_or_grounded(self):
        for spell_id in (EVISCERATE, RUPTURE_LOOK, RUPTURE, RUPTURE_HEROIC, FAN, ENVENOM, DEADLY, WOUND, CRIPPLING):
            ex1 = _raw(self.spells[spell_id], "AttributesEx")
            self.assertTrue(ex1 & ATTR1_NO_REDIRECTION, spell_id)
            self.assertTrue(ex1 & ATTR1_NO_REFLECTION, spell_id)

    def test_a_heroic_swing_and_strike_are_one_tier_swing(self):
        # STAGE-D3 Q2 A: a strike stays one of his own swings, every 2 s beside a 2.0 s swing, on half the tier's melee.
        self.assertIn("caster->CalculateDamage(BASE_ATTACK, false, true) + kStrikeBonus", self.cpp)
        heroic = int(re.search(r"kStrikeEveryMs\{ \d+, (\d+) \};", _tuning()).group(1))
        self.assertEqual(heroic, 2000)
        text = HEROIC.read_text(encoding="utf-8")
        self.assertRegex(text, r"11519: _boss\(11519, 250_264, melee=_BAZZALAN_MELEE\)")
        melee = int(re.search(r"^_BAZZALAN_MELEE = ([\d_]+)", text, re.M).group(1))
        self.assertEqual(2 * melee, HEROIC_BOSS_MELEE)

    def test_he_walks_back_onto_his_arena(self):
        # RF-1 RF-M1: the engine's step back is held every tick, bars included; no 2 s bar starts while he is off it.
        update = self.cpp[self.cpp.index("void UpdateAI("):self.cpp.index("void OnSpellFailed(")]
        self.assertLess(update.index("_edge.HoldBackstep(me);"), update.index("UpdateFinisher();"))
        self.assertIn("_edge.Update(me, _arena, _reach);", update)
        self.assertIn("Points() >= Tune::kComboMax && _clockMs >= _retryAtMs && _arena.Contains(me)", update)

    def test_combo_points(self):
        combo = self.spells[COMBO]
        self.assertEqual(combo["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(_raw(combo, "CumulativeAura"), _tune("kComboMax"))
        self.assertEqual(combo["duration_ms"], -1)
        self.assertEqual(combo["dispel"], 0)

    def test_the_rupture(self):
        ticks = _tune("kRuptureNormalMs") / _tune("kRuptureTickMs")
        normal, heroic = self.spells[RUPTURE], self.spells[RUPTURE_HEROIC]
        self.assertEqual(normal["duration_ms"], _tune("kRuptureNormalMs"))
        self.assertEqual(heroic["duration_ms"], -1)
        self.assertEqual(int(normal["effect1"]["base_points"]), round(_tune("kRuptureNormalTotalPct") / ticks * 100))
        self.assertEqual(int(heroic["effect1"]["base_points"]), _tune("kRuptureHeroicTickPct") * 100)
        self.assertTrue(_attributes(heroic) & ATTR0_NO_IMMUNITIES)
        for spell in (normal, heroic):
            spell_id = int(spell["id"])
            self.assertEqual(spell["effect1"]["apply_aura"], AURA_PERIODIC_DAMAGE)
            self.assertEqual(spell["effect1"]["amplitude"], _tune("kRuptureTickMs"))
            self.assertEqual(_raw(spell, "EffectMiscValueB_1"), int(spell["effect1"]["base_points"]))
            self.assertEqual(spell["mechanic"], MECHANIC_BLEED)
            self.assertEqual(spell["dispel"], 0)
            self.assertTrue(_raw(spell, "AuraInterruptFlags") & AURA_INTERRUPT_CHANGE_MAP)
            self.assertIn((spell_id, REFFLAT_PERIODIC), self.scripts)
        self.assertIn("SPELL_BZ_RUPTURE_HEROIC)", self.cpp)

    def test_the_poisons(self):
        deadly, wound, crippling = self.spells[DEADLY], self.spells[WOUND], self.spells[CRIPPLING]
        for spell in (deadly, wound, crippling):
            self.assertEqual(spell["dispel"], DISPEL_POISON, spell["id"])
            self.assertEqual(int(spell["school"]), SCHOOL_NATURE, spell["id"])
            self.assertTrue(_raw(spell, "AuraInterruptFlags") & AURA_INTERRUPT_CHANGE_MAP, spell["id"])
        self.assertEqual(deadly["duration_ms"], _tune("kDeadlyMs"))
        self.assertEqual(deadly["effect1"]["amplitude"], _tune("kDeadlyTickMs"))
        self.assertEqual(_raw(deadly, "CumulativeAura"), _tune("kDeadlyStacks"))
        self.assertIn((DEADLY, "spell_rfc_bazzalan_deadly_poison"), self.scripts)
        self.assertEqual(wound["effect1"]["apply_aura"], AURA_MOD_HEALING_PCT)
        self.assertEqual(int(wound["effect1"]["base_points"]), -(int(_tune("kWoundHealingPctPerStack")) + 1))
        self.assertEqual(_raw(wound, "CumulativeAura"), _tune("kWoundStacks"))
        self.assertEqual(wound["duration_ms"], _tune("kWoundMs"))
        self.assertEqual(crippling["effect1"]["apply_aura"], AURA_MOD_DECREASE_SPEED)
        self.assertEqual(int(crippling["effect1"]["base_points"]), -(int(_tune("kCripplingSlowPct")) + 1))
        self.assertEqual(crippling["mechanic"], MECHANIC_SNARE)
        self.assertEqual(crippling["duration_ms"], _tune("kCripplingMs"))

    def test_the_fan_is_a_resolve_copy(self):
        self.assertEqual(int(self.spells[FAN]["school"]), SCHOOL_PHYSICAL)
        self.assertIn((FAN, RESOLVE), self.scripts)

    def test_the_looks_are_vs(self):
        for spell_id, look in LOOKS.items():
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), look, spell_id)

    def test_every_bound_script_is_registered(self):
        for _spell, name in self.scripts:
            if name in (RESOLVE, REFFLAT_PERIODIC):
                continue
            self.assertIn(f"RegisterSpellScript({name});", self.cpp)
        registered = set(re.findall(r"RegisterSpellScript\((\w+)\);", self.cpp))
        self.assertEqual(registered, {name for _s, name in self.scripts} - {RESOLVE, REFFLAT_PERIODIC})

    def test_the_cpp_registers_the_spec(self):
        cpp = self.cpp
        # BZ5 and BZ7: the drill's shapes (STAGE-G1), the tank included, on the ridge.
        self.assertIn("Mechanic::Circle(me, me, Tune::kFanRadius, Ms(Tune::kFanWarnMs))", cpp)
        self.assertIn("Mechanic::Circle(me, me, Tune::kShadowstepRadius, Ms(Tune::kShadowstepWarnMs))", cpp)
        self.assertIn("ref.Damage(Tune::kFanPct).TankDamage(Tune::kFanPct).Spell(SPELL_BZ_FAN).Weakened()", cpp)
        self.assertIn("ref.Damage(Tune::kShadowstepPct).TankDamage(Tune::kShadowstepPct).Spell(SPELL_BZ_FAN)"
                      ".Weakened()", cpp)
        self.assertEqual(cpp.count(".Within(BazzalanFloorBounds())"), 2)
        self.assertEqual(cpp.count(".Rider(SPELL_BZ_CRIPPLING_POISON)"), 1)
        self.assertNotIn("TankExempt", cpp)
        # Threat unchanged (rule 35), and every pick includes the tank.
        self.assertNotIn("ResetAllThreat", cpp)
        self.assertNotIn("nonTank = true", cpp)
        self.assertIn("rule.nonTank = false;", cpp)
        # Boss data.
        self.assertIn("d.interrupts.emplace_back(NPC_BAZZALAN, SPELL_BZ_EVISCERATE,", cpp)
        self.assertIn("d.interrupts.emplace_back(NPC_BAZZALAN, SPELL_BZ_ENVENOM,", cpp)
        for poison in ("DEADLY", "WOUND", "CRIPPLING"):
            self.assertIn(f"DispelEntry(SPELL_BZ_{poison}_POISON,", cpp)
        # The stock casts are retired.
        self.assertNotIn("SPELL_STOCK_", cpp)
        self.assertNotIn("14873", cpp)
        self.assertNotIn("2818", cpp)
        # No assist calls (the flag stops the first only), every tick before UpdateVictim.
        self.assertRegex(cpp, r"me->SetAssistanceTimer\(0\);[^\n]*\n\s+if \(!UpdateVictim\(\)\)")
        # The rim band never turns him (R-1-BOSS M-1): the leash neither switches nor holds, the reach guard does, and
        # neither runs during the chain.
        self.assertIn("_arena(BazzalanArena(), SelfLeash(kBossLogName))", cpp)
        self.assertIn("_reach(ReachArena(), ReachLeash(kBossLogName))", cpp)
        kit = (MODULE_DIR / "RagefireChasmKit.cpp").read_text(encoding="utf-8")
        for line in ("o.switchWhenVictimOff = false;", "o.holdWhileVictimOff = false;", "o.evadeNoTargetInsideMs = 0;",
                     "o.evadeWhenBossOff = false;"):
            self.assertEqual(kit.count(line), 1, line)
        self.assertIn("if (!_state.passive && (!_arena.Update(me, diff) || (!jump && !_reach.Update(me, diff))))", cpp)
        self.assertIn("_jump.Skip(victim && victim->HasUnitMovementFlag(MOVEMENTFLAG_FALLING), diff)", cpp)  # RF2-m1
        self.assertLess(cpp.index("me->GetThreatMgr().ClearFixate();"), cpp.index("me->SelectVictim()"))
        # Rupture skips whoever is off the ridge.
        self.assertIn("Outsiders(players)", cpp)
        # Every aura of the fight is taken off again.
        for aura in ("RUPTURE)", "RUPTURE_HEROIC)", "DEADLY_POISON)", "WOUND_POISON)", "CRIPPLING_POISON)"):
            self.assertIn(f"uint32(SPELL_BZ_{aura}", cpp)
        self.assertIn("me->RemoveAurasDueToSpell(SPELL_BZ_COMBO_POINTS);", cpp)


class BazzalanSqlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8")

    def test_the_texts(self):
        for group, (kind, text) in TEXTS.items():
            self.assertIn(f"(11519, {group}, 0, '{text}', {kind}, 0, 100, ", self.sql)
        self.assertEqual(len(re.findall(r"^\(11519, ", self.sql, re.M)), len(TEXTS))
        header = REWORK.read_text(encoding="utf-8")
        groups = [int(v) for v in re.findall(r"(?:YELL|EMOTE)_BAZZALAN_\w+\s*=\s*(\d+),", header)]
        self.assertEqual(groups, sorted(TEXTS))

    def test_the_rev_touches_only_his_texts(self):
        code = re.sub(r"^--.*$", "", self.sql, flags=re.M)
        self.assertEqual(re.findall(r"(?:DELETE FROM|INSERT INTO|UPDATE) `(\w+)`", code),
                         ["creature_text", "creature_text"])
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 11519 AND `GroupID` BETWEEN 0 AND 5;", code)


if __name__ == "__main__":
    unittest.main()
