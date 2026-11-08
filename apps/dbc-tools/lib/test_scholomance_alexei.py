"""
Scholomance build WP-S9, Lord Alexei Barov: source/npcs/scholomance/lord_alexei_barov.py against its C++
(modules/mod-dungeon-bosses src/Scholomance/AlexeiLogic.h, boss_lord_alexei_barov_rework.cpp).

Checks:
  - the spells sit in his slice (206290-206314) and AlexeiLogic.h names the same ids;
  - the six rule icons are DUMMY debuffs nobody dispels; the Demerit stacks to the header's cap for the fight and
    nothing past it (persists through death, leaves with the map, never saved);
  - the two rule hits are resolve copies (no damage: the ledger entry); the Dean's Rod takes its damage from the base
    point (DieSides 0) and ignores caster modifiers; Ill-Gotten Gains is +40% damage and healing for 15 s;
  - Veil of Shadow is the tank-only copy of 17820: 1.5 s, kickable, a Curse, -50% healing taken for 10 s;
  - the fortune 300543 is an invisible, unselectable prop bound to npc_sc_barov_fortune, registered in the C++;
  - the looks are WP-V's picks;
  - 10504 is bound to boss_lord_alexei_barov_rework with SmartAI off, HealthModifier 52.425, DamageModifier 6 and
    immunity set 1972; the examiner has its own script, registered only behind kWaveCBound.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scholomance_alexei.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Scholomance"
HEADER = MODULE_DIR / "AlexeiLogic.h"
SCRIPT = MODULE_DIR / "boss_lord_alexei_barov_rework.cpp"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "scholomance"

SLICE = range(206290, 206315)
RULES = range(206290, 206296)
(ANNOUNCE, OUT_OF_BOUNDS, KEEP_DISTANCE, DEMERIT, DEANS_ROD, ILL_GOTTEN_GAINS, VEIL) = range(206296, 206303)
FORTUNE = 300543
ALEXEI = 10504

SCHOOL_DAMAGE, APPLY_AURA = 2, 6
AURA_DUMMY, AURA_MOD_DAMAGE_PERCENT_DONE, AURA_MOD_HEALING_PCT, AURA_MOD_HEALING_DONE_PERCENT = 4, 79, 118, 136
ATTR0_AURA_IS_DEBUFF = 0x04000000
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
ATTR3_ALLOW_AURA_WHILE_DEAD = 0x00100000
AURA_INTERRUPT_FLAG_CHANGE_MAP = 0x00080000
CU_AURA_CANNOT_BE_SAVED = 0x01000000
UNIT_FLAG_NOT_SELECTABLE = 0x02000000
UNIT_FLAG_NON_ATTACKABLE = 0x2
RESOLVE = "spell_boss_mechanics_resolve"
DISPEL_CURSE = 2


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


class AlexeiDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == FORTUNE}
        cls.models = {int(e["CreatureID"]): e for e in reg.creature_template_models if int(e["CreatureID"]) == FORTUNE}
        cls.edits = [e for e in reg.creature_template_edits if int(e["entry"]) == ALEXEI]
        cls.custom_attrs = {int(e["spell_id"]): int(e["attributes"]) for e in reg.custom_attrs
                            if int(e["spell_id"]) in SLICE}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(RULES.start, VEIL + 1)))
        self.assertEqual(id_blocks.out_of_reservation("scholomance", {"spell": mine}), [])
        text = HEADER.read_text(encoding="utf-8")
        first = int(re.search(r"kSpellsAlexei\{ (\d+),", (MODULE_DIR / "ScholomanceRework.h").read_text()).group(1))
        offsets = [int(v) for v in re.findall(r"SPELL_AX_\w+\s*=\s*kSpellSlice\.first \+ (\d+)", text)]
        self.assertEqual(sorted(first + o for o in offsets), mine)

    def test_rule_icons_and_demerit(self):
        for spell_id in RULES:
            s = self.spells[spell_id]
            self.assertEqual(s["effect1"]["apply_aura"], AURA_DUMMY)
            self.assertEqual(s["dispel"], 0)
            self.assertTrue(s["attributes"] & ATTR0_AURA_IS_DEBUFF)
            self.assertGreaterEqual(s["duration_ms"], 10000)    # the script trims it to the rule's 9-10 s
        demerit = self.spells[DEMERIT]
        self.assertEqual(_raw(demerit, "CumulativeAura"), _header_int("kDemeritCap"))
        self.assertEqual(demerit["duration_ms"], -1)
        self.assertEqual(demerit["dispel"], 0)
        # The fight and nothing past it (R-B N9-1): a battle resurrection keeps the ladder, a player who leaves the
        # instance (or logs out) carries no stale stacks into the world or the next pull.
        self.assertTrue(_raw(demerit, "AttributesEx3") & ATTR3_ALLOW_AURA_WHILE_DEAD)
        self.assertTrue(_raw(demerit, "AuraInterruptFlags") & AURA_INTERRUPT_FLAG_CHANGE_MAP)
        self.assertTrue(self.custom_attrs.get(DEMERIT, 0) & CU_AURA_CANNOT_BE_SAVED)
        self.assertEqual(sorted(self.custom_attrs), [DEMERIT])

    def test_the_rule_hits_and_the_rod(self):
        for spell_id in (OUT_OF_BOUNDS, KEEP_DISTANCE):
            self.assertIn((spell_id, RESOLVE), self.scripts)
        rod = self.spells[DEANS_ROD]
        self.assertEqual(rod["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertEqual(rod["effect1"]["base_points"], 0)
        self.assertEqual(rod["effect1"]["die_sides"], 0)        # CastCustomSpell's base point is the exact damage
        self.assertTrue(_raw(rod, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertEqual(_raw(rod, "SpellVisualID_1"), 792)
        self.assertFalse({s for s, _ in self.scripts} & {DEANS_ROD, DEMERIT, VEIL, ILL_GOTTEN_GAINS})

    def test_ill_gotten_gains(self):
        gains = self.spells[ILL_GOTTEN_GAINS]
        pct = _header_int("kIllGottenGainsPct")
        self.assertEqual(gains["duration_ms"], _header_int("kIllGottenGainsMs"))
        self.assertEqual([gains[f"effect{i}"]["apply_aura"] for i in (1, 2)],
                         [AURA_MOD_DAMAGE_PERCENT_DONE, AURA_MOD_HEALING_DONE_PERCENT])
        for i in (1, 2):
            self.assertEqual(gains[f"effect{i}"]["base_points"] + gains[f"effect{i}"]["die_sides"], pct)
        self.assertFalse(gains["attributes"] & ATTR0_AURA_IS_DEBUFF)
        self.assertEqual(_raw(gains, "SpellVisualID_1"), 12473)

    def test_veil_of_shadow(self):
        veil = self.spells[VEIL]
        self.assertEqual(veil["cast_time_ms"], _header_int("kVeilCastMs"))
        self.assertEqual(veil["duration_ms"], 10000)
        self.assertEqual(veil["dispel"], DISPEL_CURSE)
        self.assertEqual(veil["effect1"]["apply_aura"], AURA_MOD_HEALING_PCT)
        self.assertEqual(veil["effect1"]["base_points"] + veil["effect1"]["die_sides"], -50)
        self.assertEqual(_raw(veil, "InterruptFlags"), 15)
        self.assertEqual(_raw(veil, "PreventionType"), 1)
        self.assertNotEqual(veil["id"], 17820)

    def test_the_fortune(self):
        self.assertEqual(sorted(self.creatures), [FORTUNE])
        fortune = self.creatures[FORTUNE]
        self.assertEqual(fortune["ScriptName"], "npc_sc_barov_fortune")
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_sc_barov_fortune,", self.cpp)
        self.assertTrue(fortune["unit_flags"] & UNIT_FLAG_NOT_SELECTABLE)
        self.assertTrue(fortune["unit_flags"] & UNIT_FLAG_NON_ATTACKABLE)
        self.assertEqual(fortune.get("difficulty_entry_1", 0), 0)
        self.assertEqual(self.models[FORTUNE]["CreatureDisplayID"], 11686)
        # The look is the stock Gold Coins chest on GODI 2614 (VISUALS-REPORT gap 13), never a new entry.
        self.assertEqual(_header_int("GO_GOLD_COINS"), 186634)

    def test_alexei_is_bound(self):
        self.assertEqual(len(self.edits), 1)
        row = self.edits[0]
        self.assertEqual(row["ScriptName"], "boss_lord_alexei_barov_rework")
        self.assertEqual(row["AIName"], "")
        self.assertAlmostEqual(float(row["HealthModifier"]) * 3052, 160000, delta=2)
        self.assertEqual(float(row["DamageModifier"]), 6.0)
        self.assertEqual(row["CreatureImmunitiesId"], 1972)

    def test_the_examiner_has_its_own_script_behind_wave_c(self):
        # R-B S-3 / user ruling 5: npc_sc_examiner_alexei, registered only once wave C binds (no "not assigned").
        name = re.search(r'kExaminerScriptName\[\] = "(\w+)"', HEADER.read_text(encoding="utf-8")).group(1)
        self.assertEqual(name, "npc_sc_examiner_alexei")
        self.assertRegex(self.cpp, r"if \(kWaveCBound\)\s*RegisterDungeonReworkCreatureAI\(npc_sc_examiner_alexei,")
        self.assertNotIn("NPC_SC_EXAMINER_ALEXEI)", self.cpp.split("struct boss_lord_alexei_barov_rework")[1]
                         .split("struct npc_sc_examiner_alexei")[0])


if __name__ == "__main__":
    unittest.main()
