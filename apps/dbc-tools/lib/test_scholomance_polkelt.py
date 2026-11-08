"""
Scholomance build WP-S7, Lorekeeper Polkelt: source/npcs/scholomance/lorekeeper_polkelt.py against its C++
(modules/mod-dungeon-bosses src/Scholomance/PolkeltLogic.h, boss_lorekeeper_polkelt_rework.cpp).

Checks:
  - the spells sit in Polkelt's slice (206250-206269) and PolkeltLogic.h names the same ids;
  - the ring and pool hits are Nature resolve copies bound to spell_boss_mechanics_resolve, and the C++ registers them;
  - the fuses are 2 s / 1 s / 3 s cast bars (not interruptible) with the swell look; the pool look is the Deadmines
    puddle at 6 yd for 60 s;
  - Corroded is +5% damage taken per stack, 20 s, 10 stacks; Hardened is -90%; Rooted roots; Noxious Catalyst is an
    undispellable stacking Nature dot bound to its aura script, which the C++ registers;
  - the two specimens are full rows (6,000 health, the Unstable Corpse's models and run speed, no XP) bound to
    npc_sc_polkelt_specimen and naming their heroic entries; 10901 is bound with SmartAI off, 175k and
    DamageModifier 3.5;
  - the Hall of Secrets lesson is registered.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scholomance_polkelt.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Scholomance"
HEADER = MODULE_DIR / "PolkeltLogic.h"
SCRIPT = MODULE_DIR / "boss_lorekeeper_polkelt_rework.cpp"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "scholomance"

SLICE = range(206250, 206270)
(BURST, RIPE_BURST, POOL, POOL_LOOK, RAISE, FUSE, CHAINED_FUSE, RIPE, BURST_LOOK, CATALYST, CORRODED, ROOTED,
 HARDENED, NOXIOUS, RIPENING) = range(206250, 206265)
POLKELT, UNSTABLE, ROOTED_SPECIMEN = 10901, 300540, 300541
HEROIC = {UNSTABLE: 310116, ROOTED_SPECIMEN: 310117}     # lib/test_scholomance_heroic.py KIT_HEROIC_ID

SCHOOL_NATURE = 8
SCHOOL_DAMAGE, APPLY_AURA, PERSISTENT_AREA_AURA = 2, 6, 27
AURA_PERIODIC_DAMAGE, AURA_MOD_ROOT, AURA_MOD_DAMAGE_PERCENT_TAKEN = 3, 26, 87
ATTR0_NO_IMMUNITIES = 0x20000000
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
RESOLVE = "spell_boss_mechanics_resolve"
NOXIOUS_SCRIPT = "spell_sc_polkelt_noxious_catalyst"
WARRIOR_BASE_60 = 3052


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


def _effect(spell: dict) -> dict:
    return spell["effect1"]


class PolkeltDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = [e for e in reg.creature_template_edits if int(e["entry"]) == POLKELT]
        cls.rows = {int(r["entry"]): r for r in reg.creature_templates if int(r["entry"]) in HEROIC}
        cls.models = [m for m in reg.creature_template_models if int(m["CreatureID"]) in HEROIC]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(BURST, RIPENING + 1)))
        self.assertEqual(id_blocks.out_of_reservation("scholomance", {"spell": mine}), [])
        offsets = {int(v) for v in re.findall(r"SPELL_PK_\w+\s*=\s*kSpellSlice\.first \+ (\d+)", self.header)}
        self.assertEqual({206250 + o for o in offsets}, set(mine))

    def test_hits_are_nature_resolve_copies(self):
        for spell_id in (BURST, RIPE_BURST, POOL):
            hit = self.spells[spell_id]
            self.assertEqual(_effect(hit)["type"], SCHOOL_DAMAGE)
            self.assertEqual(hit["school"], SCHOOL_NATURE)
            self.assertTrue(_raw(hit, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
            self.assertIn((spell_id, RESOLVE), self.scripts)
        self.assertIn("Spell(SPELL_PK_SPECIMEN_BURST)", self.cpp)
        self.assertIn("Spell(SPELL_PK_RIPE_BURST)", self.cpp)
        self.assertIn("spec.spellId = SPELL_PK_ACID_POOL;", self.cpp)

    def test_fuses_are_cast_bars(self):
        for spell_id, ms in ((FUSE, 2000), (CHAINED_FUSE, 1000), (RIPE, 3000)):
            cast = self.spells[spell_id]
            self.assertEqual(cast["cast_time_ms"], ms, spell_id)
            self.assertEqual(_raw(cast, "InterruptFlags"), 0)
            self.assertEqual(_raw(cast, "SpellVisualID_1"), 11259)
        self.assertEqual(_raw(self.spells[BURST_LOOK], "SpellVisualID_1"), 749)
        self.assertEqual(_raw(self.spells[RAISE], "SpellVisualID_1"), 11305)

    def test_the_pool_look(self):
        look = self.spells[POOL_LOOK]
        self.assertEqual(_effect(look)["type"], PERSISTENT_AREA_AURA)
        self.assertEqual(_effect(look)["radius_yards"], 6.0)
        self.assertEqual(look["duration_ms"], 60000)
        self.assertEqual(_raw(look, "SpellVisualID_1"), 90342)

    def test_auras(self):
        corroded = self.spells[CORRODED]
        self.assertEqual(_effect(corroded)["apply_aura"], AURA_MOD_DAMAGE_PERCENT_TAKEN)
        self.assertEqual(_effect(corroded)["base_points"] + _effect(corroded)["die_sides"], 5)
        self.assertEqual(corroded["duration_ms"], 20000)
        self.assertEqual(_raw(corroded, "CumulativeAura"), 10)
        self.assertEqual(corroded["dispel"], 0)
        hardened = self.spells[HARDENED]
        self.assertEqual(_effect(hardened)["apply_aura"], AURA_MOD_DAMAGE_PERCENT_TAKEN)
        self.assertEqual(_effect(hardened)["base_points"] + _effect(hardened)["die_sides"], -90)
        self.assertEqual(_raw(hardened, "SpellVisualID_1"), 6662)
        rooted = self.spells[ROOTED]
        self.assertEqual(_effect(rooted)["apply_aura"], AURA_MOD_ROOT)
        self.assertEqual(rooted["dispel"], 0)
        self.assertEqual(_raw(rooted, "SpellVisualID_1"), 38)
        self.assertEqual(self.spells[RIPENING]["duration_ms"], 30000)

    def test_noxious_catalyst(self):
        dot = self.spells[NOXIOUS]
        self.assertEqual(_effect(dot)["apply_aura"], AURA_PERIODIC_DAMAGE)
        self.assertEqual(_effect(dot)["amplitude"], 1000)
        self.assertEqual(dot["school"], SCHOOL_NATURE)
        self.assertEqual(dot["dispel"], 0)
        self.assertTrue(dot["attributes"] & ATTR0_NO_IMMUNITIES)
        self.assertTrue(_raw(dot, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertEqual(_raw(dot, "CumulativeAura"), 255)
        self.assertNotEqual(NOXIOUS, 18151)
        self.assertIn((NOXIOUS, NOXIOUS_SCRIPT), self.scripts)
        self.assertIn(f"RegisterSpellScript({NOXIOUS_SCRIPT})", self.cpp)
        own = {name for _, name in self.scripts if name != RESOLVE}
        self.assertEqual(own, {NOXIOUS_SCRIPT})

    def test_specimens(self):
        self.assertEqual(set(self.rows), set(HEROIC))
        for entry, row in self.rows.items():
            with self.subTest(entry=entry):
                self.assertEqual(row["ScriptName"], "npc_sc_polkelt_specimen")
                self.assertEqual(row["AIName"], "")
                self.assertEqual(int(row["difficulty_entry_1"]), HEROIC[entry])
                self.assertEqual(math.ceil(WARRIOR_BASE_60 * float(row["HealthModifier"])), 6000)
                self.assertEqual((int(row["minlevel"]), int(row["maxlevel"])), (60, 60))
                self.assertEqual(float(row["speed_run"]), 0.571429)
                self.assertTrue(int(row["flags_extra"]) & 0x40)
                self.assertEqual(int(row["lootid"]), 0)
        displays = {(int(m["CreatureID"]), int(m["CreatureDisplayID"])) for m in self.models}
        self.assertEqual(displays, {(e, d) for e in HEROIC for d in (10978, 10972)})
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_sc_polkelt_specimen,", self.cpp)

    def test_polkelt_is_bound(self):
        self.assertEqual(len(self.edits), 1)
        edit = self.edits[0]
        self.assertEqual(edit["ScriptName"], "boss_lorekeeper_polkelt_rework")
        self.assertEqual(edit["AIName"], "")
        self.assertLessEqual(abs(float(edit["HealthModifier"]) * WARRIOR_BASE_60 - 175000), 2)
        self.assertEqual(edit["DamageModifier"], 3.5)
        self.assertEqual(edit["CreatureImmunitiesId"], 1972)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_lorekeeper_polkelt_rework,", self.cpp)

    def test_the_lesson_and_the_examiner(self):
        self.assertIn("RegisterSoloLesson(Classroom::HallOfSecrets,", self.cpp)
        # The examiner has its own ScriptName (the user's convention, 2026-11-08), registered only once wave C binds.
        self.assertIn('kExaminerScriptName[] = "npc_sc_examiner_polkelt"', self.header)
        self.assertIn("struct npc_sc_examiner_polkelt : public boss_lorekeeper_polkelt_rework", self.cpp)
        self.assertRegex(self.cpp, r"if \(kWaveCBound\)\s*RegisterDungeonReworkCreatureAI\(npc_sc_examiner_polkelt,")
        self.assertRegex(self.header, r"kExaminerHealth = 80000;")


if __name__ == "__main__":
    unittest.main()
