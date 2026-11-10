"""
Stratholme build WP-S7, Grand Crusader Dathrohan and Balnazzar: source/npcs/stratholme/dathrohan_balnazzar.py against
its C++ (modules/mod-dungeon-bosses src/Stratholme/DathrohanLogic.h, boss_dathrohan_balnazzar_rework.cpp).

Checks:
  - the spells sit in the S7 slice (206545-206574, never S8's 206575-206604) and DathrohanLogic.h names the same ids;
  - 10812 and 10813 are bound to the one script, SmartAI off, the build spec's normal health, stun immunity 1972;
  - the Infernal 300608: display 7029, 12,000 health, npc_st_infernal, its heroic entry;
  - every registry hit is a resolve copy; the script-set hits ignore caster modifiers; the percent spells carry the
    header's percents in hundredths (heroic in MiscValueB);
  - Sleep is an interruptible 2 s Magic sleep that damage does not break, bound to its AuraScript on the same aura
    type the script registers; Nightmare is a 6 s, not dispellable DoT bound to the kit's periodic script and its own;
  - the marks and auras that must clear on leaving carry CHANGE_MAP.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_stratholme_dathrohan.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Stratholme"
HEADER = MODULE_DIR / "DathrohanLogic.h"
SCRIPT = MODULE_DIR / "boss_dathrohan_balnazzar_rework.cpp"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "stratholme"

SLICE = range(206545, 206575)
S8_SLICE = range(206575, 206605)
(SG_BAR, TRUE_GROUND, LIE_GROUND, HOLY_WRATH, ERUPTION, MARK, DARK_MARK, SHARE, BURST, J_TARGET, UNMASK_MARK,
 UNMASK_BURST, CARRION_BAR, CARRION_HIT, CARRION_TARGET, INFERNO_BAR, INFERNO_HIT, INFERNO_LOOK, IMMOLATION_LOOK,
 IMMOLATION_TICK, STOKED, SLEEP, NIGHTMARE, NIGHTMARE_PULSE, VAMPIRIC_AURA, VAMPIRIC_HEAL,
 INFERNAL_STRIKE) = range(206545, 206572)
DATHROHAN, BALNAZZAR, INFERNAL = 10812, 10813, 300608

SCHOOL_DAMAGE, APPLY_AURA, HEAL, PERSISTENT_AREA_AURA = 2, 6, 10, 27
AURA_PERIODIC_DAMAGE, AURA_DUMMY, AURA_MOD_STUN = 3, 4, 12
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
AURA_INTERRUPT_CHANGE_MAP = 0x00080000
DISPEL_MAGIC = 1
MECHANIC_SLEEP = 10
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT = "spell_dungeon_refflat_damage"
REFFLAT_PERIODIC = "spell_dungeon_refflat_periodic"
SLEEP_SCRIPT = "spell_strat_balnazzar_sleep"
NIGHTMARE_SCRIPT = "spell_strat_balnazzar_nightmare"
WARRIOR_60_BASE = 3052      # creature_classlevelstats level 60 class 1 basehp0 (live 2026-11-09)
PALADIN_62_BASE = 2590      # level 62 class 2


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


def _header_number(name: str) -> float:
    match = re.search(rf"{name}\s*=\s*(-?[\d.]+)f?;", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return float(match.group(1))


def _header_nh(name: str) -> tuple[float, float]:
    match = re.search(rf"{name}\{{\s*(-?[\d.]+)f?,\s*(-?[\d.]+)f?\s*\}}", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return float(match.group(1)), float(match.group(2))


class DathrohanDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE or int(e["id"]) in S8_SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == INFERNAL}
        cls.models = {int(e["CreatureID"]): e for e in reg.creature_template_models
                      if int(e["CreatureID"]) == INFERNAL}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits
                     if int(e["entry"]) in (DATHROHAN, BALNAZZAR)}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(i for i in self.spells if i in SLICE)
        self.assertEqual(mine, list(range(SG_BAR, INFERNAL_STRIKE + 1)))
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"spell": mine}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_(?:DB|BZ)_\w+\s*=\s*(2\d+)",
                                                 HEADER.read_text(encoding="utf-8"))}
        self.assertEqual(header_ids, set(mine))
        self.assertFalse(header_ids & set(S8_SLICE))

    def test_both_entries_run_the_one_script(self):
        for entry, health in ((DATHROHAN, 250_000), (BALNAZZAR, 220_000)):
            row = self.edits[entry]
            self.assertEqual(row["ScriptName"], "boss_dathrohan_balnazzar_rework")
            self.assertEqual(row["AIName"], "")
            self.assertEqual(row["CreatureImmunitiesId"], 1972)
            self.assertTrue(row["flags_extra"] & 1)
            self.assertAlmostEqual(PALADIN_62_BASE * row["HealthModifier"], health, delta=50)
        self.assertEqual(self.edits[DATHROHAN]["DamageModifier"], 3.5)
        self.assertEqual(self.edits[BALNAZZAR]["DamageModifier"], 9)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_dathrohan_balnazzar_rework", self.cpp)

    def test_the_infernal(self):
        infernal = self.creatures[INFERNAL]
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"creature": [INFERNAL]}), [])
        self.assertEqual(infernal["ScriptName"], "npc_st_infernal")
        self.assertEqual(infernal["AIName"], "")
        normal, _ = _header_nh("kInfernalHealth")
        self.assertAlmostEqual(WARRIOR_60_BASE * infernal["HealthModifier"], normal, delta=5)
        self.assertEqual(infernal["difficulty_entry_1"], 310194)
        self.assertEqual(infernal["lootid"], 0)
        self.assertEqual(self.models[INFERNAL]["CreatureDisplayID"], 7029)
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_st_infernal", self.cpp)

    def test_registry_hits_are_resolve_copies(self):
        for spell_id in (HOLY_WRATH, ERUPTION, BURST, UNMASK_BURST, CARRION_HIT, INFERNO_HIT, NIGHTMARE_PULSE):
            self.assertIn((spell_id, RESOLVE), self.scripts, spell_id)
            self.assertTrue(_raw(self.spells[spell_id], "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)

    def test_script_set_hits(self):
        for spell_id in (SHARE, CARRION_TARGET, IMMOLATION_TICK):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertEqual(spell["effect1"]["die_sides"], 0, spell_id)
            self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS, spell_id)
        heal = self.spells[VAMPIRIC_HEAL]
        self.assertEqual(heal["effect1"]["type"], HEAL)
        self.assertTrue(_raw(heal, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertIn("SPELL_BZ_VAMPIRIC_HEAL", self.cpp)

    def test_percent_spells_carry_the_header_percents(self):
        target = self.spells[J_TARGET]
        self.assertEqual(target["effect1"]["base_points"] + 1, round(_header_number("kJudgmentTargetPct") * 100))
        self.assertEqual(_raw(target, "EffectMiscValueB_1"), round(_header_number("kJudgmentTargetPct") * 100))
        self.assertIn((J_TARGET, REFFLAT), self.scripts)
        strike = self.spells[INFERNAL_STRIKE]
        normal, heroic = _header_nh("kInfernalStrikePct")
        self.assertEqual(strike["effect1"]["base_points"] + 1, round(normal * 100))
        self.assertEqual(_raw(strike, "EffectMiscValueB_1"), round(heroic * 100))
        self.assertIn((INFERNAL_STRIKE, REFFLAT), self.scripts)

    def test_sleep(self):
        sleep = self.spells[SLEEP]
        self.assertEqual(sleep["cast_time_ms"], int(_header_number("kSleepCastMs")))
        self.assertEqual(sleep["duration_ms"], int(_header_number("kSleepMs")))
        self.assertEqual(sleep["dispel"], DISPEL_MAGIC)
        self.assertEqual(sleep["mechanic"], MECHANIC_SLEEP)
        self.assertEqual(sleep["range_yards"], _header_number("kSleepRangeYd"))
        self.assertEqual(sleep["effect1"]["apply_aura"], AURA_MOD_STUN)
        self.assertEqual(_raw(sleep, "InterruptFlags"), 15)
        self.assertEqual(_raw(sleep, "PreventionType"), 1)
        # Damage does not break it: only a map change does.
        self.assertEqual(_raw(sleep, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)
        self.assertIn((SLEEP, SLEEP_SCRIPT), self.scripts)
        self.assertIn(f"RegisterSpellScript({SLEEP_SCRIPT})", self.cpp)
        # The AuraScript's hooks name the aura type the spell carries (a mismatch unbinds them at boot).
        self.assertIn("EFFECT_0, SPELL_AURA_MOD_STUN", self.cpp)

    def test_nightmare(self):
        nightmare = self.spells[NIGHTMARE]
        self.assertEqual(nightmare["dispel"], 0)
        self.assertEqual(nightmare["duration_ms"], int(_header_number("kNightmareMs")))
        effect = nightmare["effect1"]
        self.assertEqual(effect["apply_aura"], AURA_PERIODIC_DAMAGE)
        self.assertEqual(effect["amplitude"], int(_header_number("kNightmareTickMs")))
        ticks = _header_number("kNightmareMs") / _header_number("kNightmareTickMs")
        self.assertEqual(effect["base_points"] + 1, round(_header_number("kNightmarePct") / ticks * 100))
        self.assertIn((NIGHTMARE, REFFLAT_PERIODIC), self.scripts)
        self.assertIn((NIGHTMARE, NIGHTMARE_SCRIPT), self.scripts)
        self.assertIn(f"RegisterSpellScript({NIGHTMARE_SCRIPT})", self.cpp)
        self.assertIn("EFFECT_0,\n            SPELL_AURA_PERIODIC_DAMAGE", self.cpp)

    def test_auras_clear_on_leaving(self):
        for spell_id in (MARK, DARK_MARK, UNMASK_MARK, SLEEP, NIGHTMARE):
            self.assertTrue(_raw(self.spells[spell_id], "AuraInterruptFlags") & AURA_INTERRUPT_CHANGE_MAP, spell_id)

    def test_looks(self):
        for spell_id in (TRUE_GROUND, LIE_GROUND):
            self.assertEqual(self.spells[spell_id]["effect1"]["type"], PERSISTENT_AREA_AURA)
            self.assertEqual(self.spells[spell_id]["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(self.spells[TRUE_GROUND]["effect1"]["radius_yards"], _header_number("kShelterRadius"))
        self.assertEqual(self.spells[LIE_GROUND]["effect1"]["radius_yards"], _header_number("kEruptionRadius"))
        expected = {TRUE_GROUND: 5600, LIE_GROUND: 8506, HOLY_WRATH: 126, MARK: 5651, DARK_MARK: 90514,
                    CARRION_BAR: 90513, INFERNO_HIT: 4859, INFERNO_LOOK: 4859, IMMOLATION_LOOK: 8313, SLEEP: 7320}
        for spell_id, visual in expected.items():
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), visual, spell_id)
        self.assertEqual(self.spells[STOKED]["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(self.spells[VAMPIRIC_AURA]["duration_ms"], -1)
        for spell_id, ms in ((SG_BAR, "kSacredGroundCastMs"), (CARRION_BAR, "kCarrionCastMs"),
                             (INFERNO_BAR, "kInfernoCastMs")):
            self.assertEqual(self.spells[spell_id]["cast_time_ms"], int(_header_number(ms)), spell_id)


if __name__ == "__main__":
    unittest.main()
