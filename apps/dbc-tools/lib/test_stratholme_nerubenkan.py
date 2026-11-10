"""
Stratholme build WP-S11, Nerub'enkan: source/npcs/stratholme/nerubenkan.py against its C++
(modules/mod-dungeon-bosses src/Stratholme/NerubenkanLogic.h, boss_nerubenkan_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in his slice (206645-206664) and NerubenkanLogic.h names the same ids;
  - Web Spray is the 3 s mark; the glob missile flies at the header's speed; the carrier's own hit is the kit's
    percent spell at 15% (1500 hundredths), ignoring caster modifiers;
  - the glob splash and the Skitter burst are resolve copies bound to spell_boss_mechanics_resolve, both with
    Weakened in the script;
  - Sticky Web slows 50% for 1 s; Stuck is the 2 s root (mechanic Root) the RegistryHit rides;
  - the Cocoon is a 2 s cast nothing kicks, its hold a stun of the normal hold time, the immunity beside it; the
    Brood Call is a 2.5 s cast nothing kicks; both sit on his interrupt list at priority 0;
  - the looks are WP-V-1's picks, every one from _visuals.py (no visual id of its own in nerubenkan.py);
  - 10437 is bound to boss_nerubenkan_rework with SmartAI off, HealthModifier 55.701, DamageModifier 7.5 and
    immunity set 1972; the scarab 10876 has 2,000 health; the cocoon and the web patch carry their scripts;
  - the SQL rev gives him the six build spec lines and keeps the scarab's Poison Proc reset row.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_stratholme_nerubenkan.py
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
HEADER = MODULE_DIR / "NerubenkanLogic.h"
SCRIPT = MODULE_DIR / "boss_nerubenkan_rework.cpp"
SQL_REV = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_nerubenkan_stratholme.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "stratholme"
SOURCE = PACKAGE / "nerubenkan.py"

SLICE = range(206645, 206665)
(WEB_SPRAY, GLOB_MISSILE, GLOB_HIT, GLOB_SPLASH, STICKY_WEB, STUCK, WEB_LOOK_5, WEB_LOOK_7, COCOON_CAST,
 COCOON_HOLD, COCOONED, SKITTER_BURST, SKITTER_LANDING, BROOD_CALL, COCOON_SPLITS,
 POISON_BURST) = range(206645, 206661)
NERUBENKAN, SCARAB, COCOON, WEB_PATCH = 10437, 10876, 300582, 300583

SCHOOL_NATURE = 8
SCHOOL_DAMAGE, APPLY_AURA = 2, 6
AURA_MOD_STUN, AURA_MOD_ROOT, AURA_MOD_DECREASE_SPEED = 12, 26, 33
MECHANIC_ROOT = 7
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
AURA_INTERRUPT_CHANGE_MAP = 0x00080000
RESOLVE = "spell_boss_mechanics_resolve"
PERCENT = "spell_dungeon_refflat_damage"
DISPLAY_INVISIBLE_STALKER = 11686

# The picks of source/npcs/stratholme/_visuals.py (handoff s3.10, V-1).
LOOKS = {
    GLOB_MISSILE: 4199,     # NE_VENOM_SPIT
    GLOB_SPLASH: 4199,
    STUCK: 684,             # NE_STUCK
    WEB_LOOK_5: 90501,      # SV_WEB_PATCH_5_STATE
    WEB_LOOK_7: 90503,      # SV_WEB_PATCH_7_STATE
    COCOON_HOLD: 7610,      # NE_WEB_WRAP
    COCOON_SPLITS: 7610,
    SKITTER_BURST: 4199,
    SKITTER_LANDING: 11441,  # NE_SKITTER_LEAP
    POISON_BURST: 761,      # NE_PLAGUE_FOG
    BROOD_CALL: 634,        # NE_RAISE_SCARAB
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


def _raw(spell: dict, column: str):
    return (spell.get("raw_overrides") or {}).get(column, 0) or 0


def _header_num(name: str) -> float:
    match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f?;", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return float(match.group(1))


def _header_pair(name: str) -> tuple[float, float]:
    match = re.search(rf"\b{name}\{{\s*([\d.]+)f?,\s*([\d.]+)f?\s*\}}", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return float(match.group(1)), float(match.group(2))


class NerubenkanDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits
                     if int(e["entry"]) in (NERUBENKAN, SCARAB)}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates
                         if int(e["entry"]) in (COCOON, WEB_PATCH)}
        cls.models = {int(e["CreatureID"]): e for e in reg.creature_template_models
                      if int(e["CreatureID"]) in (COCOON, WEB_PATCH)}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(WEB_SPRAY, POISON_BURST + 1)))
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"spell": mine}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_NE_\w+\s*=\s*kSpellSlice\.first \+ (\d+)", self.header)}
        self.assertEqual({WEB_SPRAY + n for n in header_ids}, set(mine))
        # The retired stock kit is never re-declared; Pierce Armor stays stock (StratholmeRework.h's constant).
        for retired in (4962, 31602, 17235, 6016):
            self.assertNotIn(retired, self.spells)
        self.assertIn("SPELL_PIERCE_ARMOR", self.cpp)
        self.assertNotIn("SPELL_PIERCE_ARMOR =", self.header)

    def test_web_spray_and_the_glob(self):
        spray = self.spells[WEB_SPRAY]
        self.assertEqual(spray["duration_ms"], _header_num("kWebSprayWarnMs"))
        self.assertEqual(spray["duration_ms"], 3000)
        missile = self.spells[GLOB_MISSILE]
        self.assertEqual(_raw(missile, "Speed"), _header_num("kGlobMissileSpeed"))
        hit = self.spells[GLOB_HIT]
        self.assertEqual(hit["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertEqual(hit["school"], SCHOOL_NATURE)
        # 15% in hundredths: base 1499 + die 1 shows 1500.
        self.assertEqual(hit["effect1"]["base_points"] + hit["effect1"]["die_sides"],
                         round(_header_num("kGlobTargetPct") * 100))
        self.assertEqual(_header_num("kGlobTargetPct"), 15.0)
        self.assertTrue(_raw(hit, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertIn((GLOB_HIT, PERCENT), self.scripts)

    def test_hits_are_resolve_copies(self):
        for spell_id in (GLOB_SPLASH, SKITTER_BURST):
            hit = self.spells[spell_id]
            self.assertEqual(hit["effect1"]["type"], SCHOOL_DAMAGE)
            self.assertEqual(hit["school"], SCHOOL_NATURE)
            self.assertTrue(_raw(hit, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
            self.assertIn((spell_id, RESOLVE), self.scripts)
        self.assertEqual(_header_pair("kGlobSplashPct"), (25.0, 30.0))
        self.assertEqual(_header_pair("kSkitterPct"), (30.0, 40.0))
        self.assertRegex(self.cpp, r"impact\.spellId = SPELL_NE_GLOB_SPLASH;\s*impact\.weakened = true;")
        self.assertRegex(self.cpp, r"\.Weakened\(\)\.Spell\(SPELL_NE_SKITTER_BURST\)")

    def test_sticky_web_and_stuck(self):
        sticky = self.spells[STICKY_WEB]
        self.assertEqual(sticky["effect1"]["apply_aura"], AURA_MOD_DECREASE_SPEED)
        self.assertEqual(sticky["effect1"]["base_points"] + sticky["effect1"]["die_sides"], -50)
        self.assertEqual(sticky["duration_ms"], 1000)
        stuck = self.spells[STUCK]
        self.assertEqual(stuck["duration_ms"], _header_num("kStuckRootMs"))
        self.assertEqual(stuck["duration_ms"], 2000)
        self.assertEqual(stuck["effect1"]["apply_aura"], AURA_MOD_ROOT)
        self.assertEqual(stuck["mechanic"], MECHANIC_ROOT)
        self.assertEqual(_raw(stuck, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)
        self.assertIn("spec.rider = SPELL_NE_STUCK;", self.cpp)
        self.assertIn("spec.weakened = true;", self.cpp)

    def test_cocoon_and_brood_call(self):
        cast = self.spells[COCOON_CAST]
        self.assertEqual(cast["cast_time_ms"], _header_num("kCocoonCastMs"))
        self.assertEqual(cast["cast_time_ms"], 2000)
        hold = self.spells[COCOON_HOLD]
        self.assertEqual(hold["effect1"]["apply_aura"], AURA_MOD_STUN)
        self.assertEqual(hold["duration_ms"], _header_pair("kCocoonHoldMs")[0])
        self.assertEqual(_raw(hold, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)
        self.assertEqual(self.spells[COCOONED]["duration_ms"], _header_pair("kCocoonHoldMs")[0])
        self.assertEqual(_raw(self.spells[COCOONED], "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)
        self.assertIn("spec.holdSpell = SPELL_NE_COCOON_HOLD;", self.cpp)
        self.assertIn("spec.immuneSpell = SPELL_NE_COCOONED;", self.cpp)
        brood = self.spells[BROOD_CALL]
        self.assertEqual(brood["cast_time_ms"], _header_num("kBroodCastMs"))
        self.assertEqual(brood["cast_time_ms"], 2500)
        for spell_id in (COCOON_CAST, BROOD_CALL):
            self.assertEqual(_raw(self.spells[spell_id], "InterruptFlags"), 0)
            self.assertEqual(_raw(self.spells[spell_id], "PreventionType"), 0)
        self.assertIn("d.interrupts.emplace_back(NPC_NERUBENKAN, SPELL_NE_COCOON_CAST, 0);", self.cpp)
        self.assertIn("d.interrupts.emplace_back(NPC_NERUBENKAN, SPELL_NE_BROOD_CALL, 0);", self.cpp)

    def test_looks_are_the_visual_picks(self):
        for spell_id, visual in LOOKS.items():
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), visual, spell_id)
        # Every visual id comes from _visuals.py: the file names none of its own (R-1-LOOT note on S11).
        source = SOURCE.read_text(encoding="utf-8")
        self.assertNotRegex(source, r"(?m)^_SV_\w+\s*=")

    def test_he_and_his_creatures_are_bound(self):
        edit = self.edits[NERUBENKAN]
        self.assertEqual(edit["ScriptName"], "boss_nerubenkan_rework")
        self.assertEqual(edit["AIName"], "")
        self.assertEqual(edit["HealthModifier"], 55.701)
        self.assertEqual(edit["DamageModifier"], 7.5)
        self.assertEqual(edit["CreatureImmunitiesId"], 1972)
        self.assertEqual(edit["flags_extra"] & 0x1, 0x1)
        # 170k on the level 60 warrior base 3,052; the scarab 2,000 on the mage base 2,136.
        self.assertAlmostEqual(55.701 * 3052, 170_000, delta=100)
        self.assertAlmostEqual(self.edits[SCARAB]["HealthModifier"] * 2136, _header_pair("kScarabHealth")[0],
                               delta=5)
        self.assertEqual(self.creatures[COCOON]["ScriptName"], "npc_st_web_cocoon")
        self.assertAlmostEqual(self.creatures[COCOON]["HealthModifier"] * 3052, _header_pair("kCocoonHealth")[0],
                               delta=5)
        self.assertEqual(self.creatures[WEB_PATCH]["ScriptName"], "npc_st_web_patch")
        self.assertEqual(int(self.models[WEB_PATCH]["CreatureDisplayID"]), DISPLAY_INVISIBLE_STALKER)
        for ai in ("boss_nerubenkan_rework", "npc_st_web_cocoon", "npc_st_web_patch"):
            self.assertIn(f"RegisterDungeonReworkCreatureAI({ai},", self.cpp)

    def test_his_texts(self):
        text = SQL_REV.read_text(encoding="utf-8")
        rows = re.findall(r"^\(10437, (\d+), 0, '((?:[^'\\]|\\.|'')*)', (\d+),", text, re.M)
        self.assertEqual([int(r[0]) for r in rows], [0, 1, 2, 3, 4, 5])
        types = {int(r[0]): int(r[2]) for r in rows}
        self.assertEqual(types, {0: 14, 1: 41, 2: 41, 3: 41, 4: 14, 5: 14})
        for name, group in (("YELL_NERUBENKAN_AGGRO", 0), ("EMOTE_NERUBENKAN_WEB", 1),
                            ("EMOTE_NERUBENKAN_COCOON", 2), ("EMOTE_NERUBENKAN_SKITTER", 3),
                            ("YELL_NERUBENKAN_BROOD_CALL", 4), ("YELL_NERUBENKAN_DEATH", 5)):
            match = re.search(rf"{name}\s*=\s*(\d+)", (MODULE_DIR / "StratholmeRework.h").read_text(encoding="utf-8"))
            self.assertIsNotNone(match, name)
            self.assertEqual(int(match.group(1)), group, name)
        # His SmartAI goes; the scarab loses only its attack row (id 1), its Poison Proc reset row 0 stays.
        self.assertIn("DELETE FROM `smart_scripts` WHERE `entryorguid` = 10437 AND `source_type` = 0;", text)
        self.assertIn("`entryorguid` = 10876 AND `source_type` = 0 AND `id` = 1;", text)


if __name__ == "__main__":
    unittest.main()
