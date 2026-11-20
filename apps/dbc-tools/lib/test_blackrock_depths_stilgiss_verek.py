"""
Blackrock Depths build WP-D8, Warder Stilgiss and Verek: source/npcs/blackrock_depths/stilgiss_verek.py against its
C++ (modules/mod-dungeon-bosses src/BlackrockDepths/StilgissVerekLogic.h, boss_warder_stilgiss_rework.cpp) and its SQL
rev.

Checks:
  - the spells sit in the slice (211050-211089) and StilgissVerekLogic.h names the same ids;
  - Stilgiss 9041 and Verek 9042 are bound (SmartAI off, immunity 1972 for both, INSTANCE_BIND, the stock
    DamageModifier), at 110k and 50k health at 5 players;
  - the cast bars are not interruptible, Frostbolt is (Frost, his only Frost bar: the Nova bar is Arcane, the Magma
    bar Fire), each hit is a resolve copy of the right school or a kit percent spell at the header's percents;
  - Curse of Blood is a Curse for +10% physical damage taken, 30 s; Frost Nova roots 2 s; the Bindings tick and the
    chain are what the script casts; Black Blood's heal is 2% and never on anyone but Verek (the script says so);
  - the SQL rev writes texts 0-6 (the draws as boss emotes 41) and makes Verek's stock emote a boss emote.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_stilgiss_verek.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockDepths"
HEADER = MODULE_DIR / "StilgissVerekLogic.h"
REWORK_HEADER = MODULE_DIR / "BlackrockDepthsRework.h"
SCRIPT = MODULE_DIR / "boss_warder_stilgiss_rework.cpp"
SQL_REV = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_stilgiss_verek_blackrock_depths.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_depths"

SLICE = range(211050, 211090)
CREDIT = 211066         # BlackrockDepthsRework.h kSpellStilgissVerekCredit (F-1a)
(OPEN_COFFER, EYE_HIT, BINDINGS, BINDINGS_TICK, BINDINGS_CHAIN, MAGMA_CAST, MAGMA_HIT, WAND_HIT, BLOOD_HIT,
 BLOOD_HEAL, NOVA_CAST, NOVA_HIT, NOVA_ROOT, FROSTBOLT, CURSE, BLOOD_LOOK) = range(211050, 211066)
STILGISS, VEREK = 9041, 9042
PALADIN_54_BASE = 2026
WARRIOR_53_BASE = 2453
STILGISS_HEALTH_AT_5 = 110_000
VEREK_HEALTH_AT_5 = 50_000

SCHOOL_NORMAL, SCHOOL_HOLY, SCHOOL_FIRE, SCHOOL_FROST, SCHOOL_SHADOW, SCHOOL_ARCANE = 1, 2, 4, 16, 32, 64
SCHOOL_DAMAGE, APPLY_AURA, HEAL_PCT = 2, 6, 136
AURA_DUMMY, AURA_MOD_ROOT, AURA_MOD_DECREASE_SPEED, AURA_MOD_DAMAGE_PERCENT_TAKEN = 4, 26, 33, 87
DISPEL_CURSE = 2
MECHANIC_ROOT = 7
ATTR1_CHANNELED = 0x4
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
AURA_INTERRUPT_CHANGE_MAP = 0x00080000
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT = "spell_dungeon_refflat_damage"
IMMUNITY_BOSS_STUN = 1972
INSTANCE_BIND = 0x1


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


def _raw(spell: dict, column: str) -> int:
    return int((spell.get("raw_overrides") or {}).get(column, 0) or 0)


def _header_int(name: str) -> int:
    match = re.search(rf"\b{name}\s*=\s*(-?\d+)", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return int(match.group(1))


def _header_pair(name: str) -> tuple[float, float]:
    match = re.search(rf"\b{name}\{{\s*(-?[\d.]+)f?,\s*(-?[\d.]+)f?\s*\}}", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return float(match.group(1)), float(match.group(2))


def _header_float(name: str) -> float:
    match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f?;", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return float(match.group(1))


class StilgissVerekDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {}
        for e in reg.creature_template_edits:
            if int(e["entry"]) in (STILGISS, VEREK):
                cls.edits.setdefault(int(e["entry"]), {}).update(e)
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(OPEN_COFFER, BLOOD_LOOK + 1)) + [CREDIT])
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"spell": mine}), [])
        offsets = {int(v) for v in re.findall(r"SPELL_SV_\w+\s*=\s*kSpellSlice\.first \+ (\d+)", self.header)}
        self.assertEqual({OPEN_COFFER + n for n in offsets}, set(mine) - {CREDIT})
        # The encounter's credit (F-1a): the shared header names it; a DUMMY that is never cast.
        self.assertRegex(REWORK_HEADER.read_text(encoding="utf-8"),
                         rf"kSpellStilgissVerekCredit = {CREDIT};")
        credit = self.spells[CREDIT]
        self.assertEqual(credit["effect1"]["type"], 3)       # SPELL_EFFECT_DUMMY
        self.assertIsNone(credit["effect2"])
        self.assertNotIn("kSpellStilgissVerekCredit", self.cpp)     # the instance credits it, the AIs never cast it
        # The stock Frost Ward and Curse of Blood are never re-declared: the retired and the changed one are copies.
        for stock in (15044, 15042, 12675, 12674):
            self.assertNotIn(stock, self.spells)

    def test_the_two_units_are_bound_with_the_build_specs_health(self):
        for entry, script, base, health in ((STILGISS, "boss_warder_stilgiss_rework", PALADIN_54_BASE,
                                             STILGISS_HEALTH_AT_5),
                                            (VEREK, "npc_verek_rework", WARRIOR_53_BASE, VEREK_HEALTH_AT_5)):
            edit = self.edits[entry]
            self.assertEqual(edit["ScriptName"], script)
            self.assertEqual(edit["AIName"], "")
            # H item 3: D8 sets Verek's normal row too (stock -251: stun immune, no silence, no interrupt immunity).
            self.assertEqual(edit["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
            # INSTANCE_BIND on Stilgiss only (row 233 credits the pair by spell 211066; handoff section 10)
            self.assertEqual(edit["flags_extra"] & INSTANCE_BIND, INSTANCE_BIND if entry == STILGISS else 0)
            self.assertEqual(edit["DamageModifier"], 3.5)
            self.assertLessEqual(abs(math.ceil(base * edit["HealthModifier"]) - health), 2)
        self.assertIn('RegisterDungeonReworkCreatureAI(boss_warder_stilgiss_rework', self.cpp)
        self.assertIn('RegisterDungeonReworkCreatureAI(npc_verek_rework', self.cpp)

    def test_the_hits_are_resolve_copies_of_the_right_school(self):
        expected = {EYE_HIT: SCHOOL_SHADOW, MAGMA_HIT: SCHOOL_FIRE, WAND_HIT: SCHOOL_HOLY, BLOOD_HIT: SCHOOL_SHADOW,
                    NOVA_HIT: SCHOOL_FROST}
        for spell_id, school in expected.items():
            spell = self.spells[spell_id]
            self.assertEqual(spell["school"], school, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE)

    def test_the_cast_bars_are_not_interruptible_and_their_schools_stay_clear_of_frost(self):
        for spell_id, ms, school in ((OPEN_COFFER, "kOpenMs", SCHOOL_NORMAL), (MAGMA_CAST, "kMagmaCastMs", SCHOOL_FIRE),
                                     (NOVA_CAST, "kNovaCastMs", SCHOOL_ARCANE)):
            bar = self.spells[spell_id]
            self.assertEqual(bar["cast_time_ms"], _header_int(ms), spell_id)
            self.assertEqual(_raw(bar, "InterruptFlags"), 0)
            self.assertEqual(_raw(bar, "PreventionType"), 0)
            self.assertEqual(bar["school"], school)
            # Rule 5: a kick on Frostbolt (Frost) never locks a must-play bar.
            self.assertNotEqual(bar["school"], SCHOOL_FROST)
        self.assertIn("DungeonKit::CastBar(me, SPELL_SV_MAGMA_CAST)", self.cpp)
        self.assertIn("DungeonKit::CastBar(me, SPELL_SV_NOVA_CAST)", self.cpp)
        self.assertIn("DungeonKit::CastBar(me, SPELL_SV_OPEN_COFFER)", self.cpp)

    def test_frostbolt_is_the_one_interruptible_frost_cast(self):
        bolt = self.spells[FROSTBOLT]
        self.assertEqual(bolt["school"], SCHOOL_FROST)
        self.assertEqual(bolt["cast_time_ms"], _header_int("kFrostboltCastMs"))
        self.assertEqual(bolt["cast_time_ms"], 3000)
        self.assertEqual(_raw(bolt, "InterruptFlags"), 15)
        self.assertEqual(_raw(bolt, "PreventionType"), 1)
        self.assertEqual(bolt["range_yards"], 40.0)
        normal, heroic = _header_pair("kFrostboltPct")
        self.assertEqual(bolt["effect1"]["base_points"] + 1, int(normal * 100))
        self.assertEqual(_raw(bolt, "EffectMiscValueB_1"), int(heroic * 100))
        self.assertIn((FROSTBOLT, REFFLAT), self.scripts)
        self.assertTrue(_raw(bolt, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        slow = bolt["effect2"]
        self.assertEqual(slow["apply_aura"], AURA_MOD_DECREASE_SPEED)
        self.assertEqual(slow["base_points"] + 1, -50)
        self.assertEqual(bolt["duration_ms"], _header_int("kFrostboltSlowMs"))
        # The script casts it for real (the bar shows) and lists it as a reward to kick.
        self.assertIn("me->CastSpell(target, SPELL_SV_FROSTBOLT, false)", self.cpp)
        self.assertIn("d.interrupts.emplace_back(NPC_STILGISS, SPELL_SV_FROSTBOLT, 1,", self.cpp)
        # No other interruptible spell of the slice.
        for spell_id, spell in self.spells.items():
            if spell_id != FROSTBOLT:
                self.assertEqual(_raw(spell, "InterruptFlags"), 0, spell_id)

    def test_the_percent_spells_carry_the_headers_percents(self):
        tick = self.spells[BINDINGS_TICK]
        normal, heroic = _header_pair("kBindingsPct")
        self.assertEqual(tick["effect1"]["base_points"] + 1, int(normal * 100))
        self.assertEqual(_raw(tick, "EffectMiscValueB_1"), int(heroic * 100))
        self.assertIn((BINDINGS_TICK, REFFLAT), self.scripts)
        self.assertTrue(_raw(tick, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertEqual(tick["school"], SCHOOL_NORMAL)

    def test_the_bindings_debuff_and_the_chain(self):
        debuff = self.spells[BINDINGS]
        self.assertEqual(debuff["duration_ms"], _header_int("kBindingsMs"))
        self.assertEqual(debuff["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(debuff["dispel"], 0)
        self.assertEqual(_raw(debuff, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)
        chain = self.spells[BINDINGS_CHAIN]
        self.assertTrue(_raw(chain, "AttributesEx") & ATTR1_CHANNELED)
        self.assertEqual(chain["duration_ms"], _header_int("kBindingsMs"))
        self.assertEqual(chain["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(_raw(chain, "ChannelInterruptFlags"), 0)
        # The chain look is Harpoon Chain's (never Chains of Kel'Thuzad SV 7597) and comes from _visuals.py.
        self.assertEqual(_raw(chain, "SpellVisualID_1"), 10920)
        self.assertIn("SpellVisualID_1", self.spells[BLOOD_LOOK]["raw_overrides"])
        self.assertEqual(_raw(self.spells[BLOOD_LOOK], "SpellVisualID_1"), 90601)

    def test_curse_of_blood_is_a_curse_for_ten_percent_physical(self):
        curse = self.spells[CURSE]
        self.assertEqual(curse["dispel"], DISPEL_CURSE)
        self.assertEqual(curse["duration_ms"], _header_int("kCurseMs"))
        self.assertEqual(curse["duration_ms"], 30000)
        effect = curse["effect1"]
        self.assertEqual(effect["apply_aura"], AURA_MOD_DAMAGE_PERCENT_TAKEN)
        self.assertEqual(effect["misc_value"], 1)
        self.assertEqual(effect["base_points"] + 1, int(_header_float("kCursePhysicalPct")))
        self.assertEqual(curse["range_yards"], 20.0)
        self.assertEqual(curse["school"], SCHOOL_SHADOW)
        self.assertEqual(_raw(curse, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)
        # The descriptor lists it as a dispel (a reward) and Verek's Enrage as the purge.
        self.assertIn("d.dispels.emplace_back(SPELL_SV_CURSE_OF_BLOOD, 1)", self.cpp)
        self.assertIn("d.purges.emplace_back(NPC_VEREK, SPELL_STOCK_ENRAGE, 1)", self.cpp)

    def test_frost_nova_roots_two_seconds(self):
        root = self.spells[NOVA_ROOT]
        self.assertEqual(root["duration_ms"], _header_int("kNovaRootMs"))
        self.assertEqual(root["duration_ms"], 2000)
        self.assertEqual(root["effect1"]["apply_aura"], AURA_MOD_ROOT)
        self.assertEqual(root["mechanic"], MECHANIC_ROOT)
        self.assertEqual(root["dispel"], 0)
        self.assertEqual(_raw(root, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)
        self.assertIn(".Rider(SPELL_SV_NOVA_ROOT)", self.cpp)

    def test_black_blood_heals_two_percent_and_only_verek(self):
        heal = self.spells[BLOOD_HEAL]
        effect = heal["effect1"]
        self.assertEqual(effect["type"], HEAL_PCT)
        self.assertEqual(effect["base_points"] + 1, int(_header_float("kBloodHealPct")))
        self.assertEqual(effect["base_points"] + 1, 2)
        # The only caller casts it at Verek (never at himself).
        casts = re.findall(r"CastSpell\(([^,]+), SPELL_SV_BLOOD_HEAL", self.cpp)
        self.assertEqual(len(casts), 1)
        self.assertIn("verek", casts[0].lower())

    def test_the_spec_wiring_names_exist_in_the_script(self):
        for needle in ("DungeonKit::LineStrike(me, me, target, spec)", "Mechanic::Stack(me, ",
                       "Mechanic::Donut(me, me, kMagmaInnerYd, kMagmaOuterYd,",
                       "Mechanic::Circle(me, me, kNovaRadiusYd",
                       "BossMechanics::Who::MainTank", "SPELL_STOCK_FROST_ARMOR", "OnBossPull(me,"):
            self.assertIn(needle, self.cpp, needle)


class StilgissVerekSqlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL_REV.read_text(encoding="utf-8")

    def test_the_texts_are_groups_zero_to_six_and_the_draws_are_boss_emotes(self):
        rows = re.findall(r"\(9041, (\d), 0, '((?:[^']|'')*)', (\d+), ", self.sql)
        self.assertEqual([int(group) for group, _text, _type in rows], list(range(7)))
        types = {int(group): int(kind) for group, _text, kind in rows}
        self.assertEqual(types[0], 14)
        self.assertEqual(types[6], 14)
        for group in range(1, 6):
            self.assertEqual(types[group], 41, group)
        texts = {int(group): text for group, text, _kind in rows}
        self.assertIn("Thieves, in my Vault?", texts[0])
        self.assertIn("%s draws the Eye of Kajal from a coffer!", texts[1])
        self.assertIn("%s draws the Black Blood of the Tormented from a coffer!", texts[5])
        self.assertIn("My... collection...", texts[6])

    def test_verek_keeps_his_stock_emote_as_a_boss_emote(self):
        self.assertRegex(self.sql, r"UPDATE `creature_text` SET `Type` = 41 WHERE `CreatureID` = 9042 AND "
                                   r"`GroupID` = 0")

    def test_the_smartai_rows_are_not_dropped_twice(self):
        # WP-S0's rev drops the SmartAI of 9041 and 9042.
        self.assertNotIn("DELETE FROM `smart_scripts`", self.sql)


if __name__ == "__main__":
    unittest.main()
