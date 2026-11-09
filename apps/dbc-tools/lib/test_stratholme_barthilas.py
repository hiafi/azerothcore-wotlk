"""
Stratholme build WP-S9, Magistrate Barthilas: source/npcs/stratholme/magistrate_barthilas.py against its C++
(modules/mod-dungeon-bosses src/Stratholme/BarthilasLogic.h, boss_magistrate_barthilas_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in his slice (206605-206624) and BarthilasLogic.h names the same ids;
  - Infection is a 10 s Disease, 4% of the reference row every 2 s through the kit's periodic percent spell, with
    its expiry script (the cough), CHANGE_MAP and IGNORE_CASTER_MODIFIERS; Recovered lasts 10 s;
  - the cough, the grain's landing and the purge are resolve copies bound to spell_boss_mechanics_resolve; the cough
    and the grain carry Weakened, the purge does not;
  - the sack flies at the header's speed; the pile fog lasts the heroic pile life over 5 yd;
  - Fever is +5% damage and +3% attack speed a stack, no cap, with its per-stack script (heroic +6%);
  - Bedlam is a 3 s cast a kick or a silence stops, on his interrupt list;
  - the looks are WP-V-1's picks;
  - 10435 is bound to boss_magistrate_barthilas_rework with SmartAI off, HealthModifier 62.696, DamageModifier 3.5
    and immunity set 1972; the two stalkers are invisible triggers with no script;
  - the SQL rev keeps stock group 0 and adds the five build spec lines (the cough a boss emote, the rest yells).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_stratholme_barthilas.py
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
HEADER = MODULE_DIR / "BarthilasLogic.h"
SCRIPT = MODULE_DIR / "boss_magistrate_barthilas_rework.cpp"
SQL_REV = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_magistrate_barthilas_stratholme.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "stratholme"

SLICE = range(206605, 206625)
(INFECTION, COUGH, COUGHING, RECOVERED, GRAIN_THROW, GRAIN_IMPACT, PLAGUE_FOG, PURGE, FEVER,
 BEDLAM) = range(206605, 206615)
BARTHILAS = 10435
GRAIN_PILE, WARD = 300580, 300581

SCHOOL_NATURE = 8
SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT, PERSISTENT_AREA_AURA = 2, 6, 3, 27
AURA_PERIODIC_DAMAGE, AURA_DUMMY, AURA_MOD_DAMAGE_PERCENT_DONE, AURA_MOD_MELEE_HASTE = 3, 4, 79, 138
DISPEL_DISEASE = 3
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
AURA_INTERRUPT_CHANGE_MAP = 0x00080000
RESOLVE = "spell_boss_mechanics_resolve"
DISPLAY_INVISIBLE_STALKER = 11686

# The picks of source/npcs/stratholme/_visuals.py (handoff s3.10, V-1).
LOOKS = {
    INFECTION: 1712,        # BT_INFECTION
    COUGH: 761,             # BT_CONTAGION
    COUGHING: 761,
    GRAIN_THROW: 12216,     # BT_GRAIN_SACK
    GRAIN_IMPACT: 761,
    PLAGUE_FOG: 10395,      # BT_NOXIOUS_FOG
    PURGE: 761,
    FEVER: 47,              # BT_FEVER
    BEDLAM: 2817,           # BT_FURIOUS_ANGER_FLASH
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


def _raw(spell: dict, column: str) -> int:
    return int((spell.get("raw_overrides") or {}).get(column, 0) or 0)


def _header_num(name: str) -> float:
    match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f?;", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return float(match.group(1))


def _header_pair(name: str) -> tuple[float, float]:
    match = re.search(rf"\b{name}\{{\s*([\d.]+)f?,\s*([\d.]+)f?\s*\}}", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return float(match.group(1)), float(match.group(2))


class BarthilasDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = [e for e in reg.creature_template_edits if int(e["entry"]) == BARTHILAS]
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates
                         if int(e["entry"]) in (GRAIN_PILE, WARD)}
        cls.models = {int(e["CreatureID"]): e for e in reg.creature_template_models
                      if int(e["CreatureID"]) in (GRAIN_PILE, WARD)}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(INFECTION, BEDLAM + 1)))
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"spell": mine}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_BT_\w+\s*=\s*(\d+),", self.header)}
        self.assertEqual(header_ids, set(mine))

    def test_infection_and_recovered(self):
        infection = self.spells[INFECTION]
        self.assertEqual(infection["duration_ms"], _header_num("kInfectionMs"))
        self.assertEqual(infection["duration_ms"], 10000)
        self.assertEqual(infection["dispel"], DISPEL_DISEASE)
        self.assertEqual(infection["school"], SCHOOL_NATURE)
        effect = infection["effect1"]
        self.assertEqual((effect["type"], effect["apply_aura"]), (APPLY_AURA, AURA_PERIODIC_DAMAGE))
        self.assertEqual(effect["amplitude"], _header_num("kInfectionTickMs"))
        self.assertEqual(effect["amplitude"], 2000)
        # 4% of the reference row a tick, in hundredths.
        self.assertEqual(effect["base_points"], round(_header_num("kInfectionTickPct") * 100))
        self.assertEqual(effect["base_points"], 400)
        self.assertTrue(_raw(infection, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertEqual(_raw(infection, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)
        self.assertIn((INFECTION, "spell_dungeon_refflat_periodic"), self.scripts)
        self.assertIn((INFECTION, "spell_st_barthilas_infection"), self.scripts)
        self.assertIn("RegisterSpellScript(spell_st_barthilas_infection);", self.cpp)
        recovered = self.spells[RECOVERED]
        self.assertEqual(recovered["duration_ms"], _header_num("kRecoveredMs"))
        self.assertEqual(recovered["duration_ms"], 10000)
        self.assertEqual(recovered["dispel"], 0)
        self.assertEqual(_raw(recovered, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)

    def test_hits_are_resolve_copies(self):
        for spell_id in (COUGH, GRAIN_IMPACT, PURGE):
            hit = self.spells[spell_id]
            self.assertEqual(hit["effect1"]["type"], SCHOOL_DAMAGE)
            self.assertEqual(hit["school"], SCHOOL_NATURE)
            self.assertTrue(_raw(hit, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
            self.assertIn((spell_id, RESOLVE), self.scripts)
        # The percents: cough 30 / 40 + Weakened on both (handoff s7 #17), grain 30 + Weakened, purge 40 without.
        self.assertEqual(_header_pair("kCoughPct"), (30.0, 40.0))
        self.assertEqual(_header_num("kGrainPct"), 30.0)
        self.assertEqual(_header_num("kPurgePct"), 40.0)
        self.assertRegex(self.cpp, r"Spell\(SPELL_BT_COUGH\)\.Weakened\(\)")
        self.assertRegex(self.cpp, r"Spell\(SPELL_BT_GRAIN_IMPACT\)\.Weakened\(\)")
        self.assertRegex(self.cpp, r"spec\.spellId = SPELL_BT_PURGE;\s*spec\.weakened = false;")

    def test_the_grain_and_the_pile(self):
        throw = self.spells[GRAIN_THROW]
        self.assertEqual(throw["effect1"]["type"], DUMMY_EFFECT)
        self.assertEqual((throw.get("raw_overrides") or {}).get("Speed"), _header_num("kGrainSackSpeed"))
        fog = self.spells[PLAGUE_FOG]
        self.assertEqual(fog["effect1"]["type"], PERSISTENT_AREA_AURA)
        self.assertEqual(fog["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(fog["effect1"]["radius_yards"], _header_num("kPileYd"))
        # The look lasts the longest pile (heroic 45 s); the stalker's despawn ends it sooner.
        self.assertEqual(fog["duration_ms"], max(_header_pair("kPileLifeMs")))

    def test_fever(self):
        fever = self.spells[FEVER]
        self.assertEqual(fever["duration_ms"], -1)
        self.assertEqual(fever["effect1"]["apply_aura"], AURA_MOD_DAMAGE_PERCENT_DONE)
        self.assertEqual(fever["effect1"]["base_points"], _header_pair("kFeverDamagePct")[0])
        self.assertEqual(_header_pair("kFeverDamagePct"), (5.0, 6.0))
        self.assertEqual(fever["effect2"]["apply_aura"], AURA_MOD_MELEE_HASTE)
        self.assertEqual(fever["effect2"]["base_points"], _header_num("kFeverHastePct"))
        self.assertEqual(_raw(fever, "CumulativeAura"), 255)       # no cap
        self.assertEqual(fever["dispel"], 0)
        self.assertIn((FEVER, "spell_st_barthilas_fever"), self.scripts)
        self.assertIn("RegisterSpellScript(spell_st_barthilas_fever);", self.cpp)

    def test_bedlam_is_kickable(self):
        bedlam = self.spells[BEDLAM]
        self.assertEqual(bedlam["cast_time_ms"], _header_num("kBedlamCastMs"))
        self.assertEqual(bedlam["cast_time_ms"], 3000)
        self.assertEqual(_raw(bedlam, "InterruptFlags"), 15)
        self.assertEqual(_raw(bedlam, "PreventionType"), 1)
        self.assertIn("d.interrupts.emplace_back(NPC_BARTHILAS, SPELL_BT_BEDLAM, kBedlamKickPriority", self.cpp)
        self.assertEqual(_header_num("kBedlamKickPriority"), 3)

    def test_looks_are_the_visual_picks(self):
        for spell_id, visual in LOOKS.items():
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), visual, spell_id)

    def test_barthilas_and_his_stalkers_are_bound(self):
        self.assertEqual(len(self.edits), 1)
        edit = self.edits[0]
        self.assertEqual(edit["ScriptName"], "boss_magistrate_barthilas_rework")
        self.assertEqual(edit["AIName"], "")
        self.assertEqual(edit["HealthModifier"], 62.696)
        self.assertEqual(edit["DamageModifier"], 3.5)
        self.assertEqual(edit["CreatureImmunitiesId"], 1972)
        self.assertEqual(edit["flags_extra"] & 0x1, 0x1)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_magistrate_barthilas_rework", self.cpp)
        # 180k on the level 58 warrior base 2,871.
        self.assertAlmostEqual(62.696 * 2871, 180_000, delta=100)
        for entry in (GRAIN_PILE, WARD):
            self.assertEqual(self.creatures[entry]["ScriptName"], "")
            self.assertEqual(int(self.models[entry]["CreatureDisplayID"]), DISPLAY_INVISIBLE_STALKER)

    def test_his_texts(self):
        text = SQL_REV.read_text(encoding="utf-8")
        rows = re.findall(r"^\(10435, (\d+), 0, '((?:[^'\\]|\\.|'')*)', (\d+),", text, re.M)
        self.assertEqual([int(r[0]) for r in rows], [1, 2, 3, 4, 5])
        types = {int(r[0]): int(r[2]) for r in rows}
        self.assertEqual(types, {1: 41, 2: 14, 3: 14, 4: 14, 5: 14})
        # Stock group 0 stays: the rev deletes only 1-5.
        self.assertIn("`CreatureID` = 10435 AND `GroupID` BETWEEN 1 AND 5", text)
        for name, group in (("SAY_BARTHILAS_AGGRO", 0), ("EMOTE_BARTHILAS_COUGH", 1),
                            ("YELL_BARTHILAS_QUARANTINE", 2), ("YELL_BARTHILAS_BEDLAM", 3),
                            ("YELL_BARTHILAS_GRAIN", 4), ("YELL_BARTHILAS_DEATH", 5)):
            match = re.search(rf"{name}\s*=\s*(\d+)", (MODULE_DIR / "StratholmeRework.h").read_text(encoding="utf-8"))
            self.assertIsNotNone(match, name)
            self.assertEqual(int(match.group(1)), group, name)
        # His SmartAI rows and their conditions go.
        self.assertIn("DELETE FROM `smart_scripts` WHERE `entryorguid` = 10435 AND `source_type` = 0;", text)
        self.assertIn("`SourceTypeOrReferenceId` = 22 AND `SourceEntry` = 10435", text)


if __name__ == "__main__":
    unittest.main()
