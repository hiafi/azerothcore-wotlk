"""
Blackrock Depths build WP-D24, the Emperor's hard mode (the Avatar of Ragnaros): source/npcs/blackrock_depths/
emperor_hard_mode.py (the spells 211660-211669) and the C++ side it must agree with (modules/mod-dungeon-bosses
src/BlackrockDepths/EmperorHardModeLogic.h, emperor_hard_mode.cpp; D23's EmperorFight.h hooks and texts).

Checks:
  - the 10 spells sit in the D24 slice, inside the dungeon's reservation, and the C++ names the same ids;
  - the Magma Clap bar is a Fire cast bar (not interruptible, the spec's 3 s); the two scripted hits are exact (base
    point 0, no script) and ignore the caster's modifiers; the mark is a 5 s non-dispellable debuff that leaves with the
    map; the stone's tick is a Fire resolve copy; Magma Blast (rule 10) is 20% on the kit's percent script;
  - the looks are V-2's EM_ picks, never a WRONG-listed visual;
  - the numbers the dbc-tools file pins are the header's; the Avatar's display, scale and health are the spec's;
  - the hard mode registers its factory on D23's hooks, says D23's texts 11 and 12, and writes no SQL of its own.

Does not depend on the wave 2 gate: nothing here is bound by data (the Avatar is Dagran's script).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_emperor_hard_mode.py
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import test_blackrock_depths_event_items as event_items_test  # noqa: E402
from lib import test_id_blocks as id_blocks  # noqa: E402
from lib.test_blackrock_depths_vfx import WRONG_SPELL_VISUALS  # noqa: E402
from source.npcs.blackrock_depths import _visuals as visuals  # noqa: E402

MDB = REPO_ROOT / "modules" / "mod-dungeon-bosses"
LOGIC = MDB / "src" / "BlackrockDepths" / "EmperorHardModeLogic.h"
D23_LOGIC = MDB / "src" / "BlackrockDepths" / "EmperorLogic.h"
SCRIPT = MDB / "src" / "BlackrockDepths" / "emperor_hard_mode.cpp"
HEADER = MDB / "src" / "BlackrockDepths" / "BlackrockDepthsRework.h"
D23_SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_emperor_blackrock_depths.sql"
DECLARATION = TOOL_ROOT / "source" / "npcs" / "blackrock_depths" / "emperor_hard_mode.py"
OWN_SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_emperor_hard_mode_blackrock_depths.sql"

SLICE = range(211660, 211710)
NAMES = ("SPELL_AV_MAGMA_CLAP_CAST", "SPELL_AV_MAGMA_CLAP", "SPELL_AV_MAGMA_CLAP_RING", "SPELL_AV_VOLCANIC_MARK",
         "SPELL_AV_VOLCANIC_BLAST", "SPELL_AV_VOLCANIC_STONE", "SPELL_AV_VOLCANIC_STONE_LOOK",
         "SPELL_AV_AWAKENS_PILLAR", "SPELL_AV_AWAKENS_ERUPTION", "SPELL_AV_MAGMA_BLAST")
(CLAP_CAST, CLAP, CLAP_RING, MARK, BLAST, STONE, STONE_LOOK, PILLAR, ERUPTION, MAGMA_BLAST) = range(211660, 211670)
EFFECT_SCHOOL_DAMAGE, EFFECT_APPLY_AURA, EFFECT_DUMMY = 2, 6, 3
AURA_DUMMY = 4
SCHOOL_FIRE = 4
ATTR0_AURA_IS_DEBUFF = 0x04000000
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
AURA_INTERRUPT_CHANGE_MAP = 0x00080000


class EmperorHardModeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        npcs = event_items_test._load_npcs()
        cls.spells = {int(e["id"]): e for e in npcs.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in npcs.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.logic = LOGIC.read_text(encoding="utf-8")
        cls.d23_logic = D23_LOGIC.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.d23_sql = D23_SQL.read_text(encoding="utf-8")
        cls.declaration = DECLARATION.read_text(encoding="utf-8")

    def _const(self, name: str) -> str:
        match = re.search(rf"{name}\s*=\s*([^;]+?)\s*;", self.logic)
        self.assertIsNotNone(match, name)
        return match.group(1)

    def _declared(self, name: str) -> int:
        """An integer constant of the declaration file (it registers spells, so it is read, not imported)."""
        match = re.search(rf"^{name} = (\d+)", self.declaration, re.M)
        self.assertIsNotNone(match, name)
        return int(match.group(1))

    # --- the spells ---------------------------------------------------------------------------------------------------

    def test_the_spells_sit_in_the_d24_slice(self):
        self.assertEqual(sorted(self.spells), list(range(211660, 211670)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"spell": list(self.spells)}), [])
        self.assertIn("kSpellsAvatar{ 211660, 211709 }", re.sub(r"\s+", " ", self.header))

    def test_the_cpp_names_the_same_ids(self):
        for offset, name in enumerate(NAMES):
            self.assertRegex(self.logic, rf"{name}\s*=\s*kSpellSlice\.first \+ {offset},", name)
        self.assertRegex(self.logic, r"kLastSpell = SPELL_AV_MAGMA_BLAST;")

    def test_every_spell_is_fire(self):
        for spell_id, spell in self.spells.items():
            self.assertEqual(spell["school"], SCHOOL_FIRE, spell_id)

    def test_the_magma_clap_bar_is_a_three_second_cast_nobody_can_kick(self):
        spell = self.spells[CLAP_CAST]
        self.assertEqual(spell["cast_time_ms"], self._declared("CLAP_CAST_MS"))
        self.assertEqual(self._const("kClapCastMs"), str(self._declared("CLAP_CAST_MS")))
        self.assertEqual(spell["raw_overrides"]["InterruptFlags"], 0)
        self.assertEqual(spell["raw_overrides"]["PreventionType"], 0)
        self.assertEqual(spell["effect1"]["type"], EFFECT_DUMMY)

    def test_the_scripted_hits_are_exact(self):
        for spell_id in (CLAP, BLAST):
            spell = self.spells[spell_id]
            effect = spell["effect1"]
            self.assertEqual(effect["type"], EFFECT_SCHOOL_DAMAGE, spell_id)
            self.assertEqual((effect["base_points"], effect["die_sides"]), (0, 0), spell_id)
            self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & ATTR3_IGNORE_CASTER_MODIFIERS, spell_id)
            self.assertFalse([s for (i, s) in self.scripts if i == spell_id], spell_id)
        self.assertIn("CastCustomSpell(SPELL_AV_MAGMA_CLAP, SPELLVALUE_BASE_POINT0", self.script)
        self.assertIn("CastCustomSpell(SPELL_AV_VOLCANIC_BLAST, SPELLVALUE_BASE_POINT0", self.script)
        self.assertIn("DungeonKit::RefFlatOn(boss, player, pct)", self.script)
        self.assertIn("DungeonKit::SplitShares(boss, takers", self.script)

    def test_the_mark_is_a_five_second_marker_nobody_can_dispel(self):
        spell = self.spells[MARK]
        self.assertEqual(spell["duration_ms"], self._declared("BLAST_MARK_MS"))
        self.assertEqual(self._const("kBlastMarkMs"), str(self._declared("BLAST_MARK_MS")))
        self.assertEqual(spell["dispel"], 0)
        self.assertTrue(spell["attributes"] & ATTR0_AURA_IS_DEBUFF)
        self.assertEqual((spell["effect1"]["type"], spell["effect1"]["apply_aura"]), (EFFECT_APPLY_AURA, AURA_DUMMY))
        self.assertTrue(spell["raw_overrides"]["AuraInterruptFlags"] & AURA_INTERRUPT_CHANGE_MAP)
        self.assertIn("DoRemoveAurasDueToSpellOnPlayers(SPELL_AV_VOLCANIC_MARK)", self.script)

    def test_the_stone_tick_is_a_fire_resolve_copy(self):
        self.assertIn((STONE, "spell_boss_mechanics_resolve"), self.scripts)
        self.assertEqual(self.spells[STONE_LOOK]["duration_ms"], -1)
        self.assertEqual(self._const("kStoneMs"), str(self._declared("STONE_MS")))

    def test_magma_blast_is_twenty_percent_on_the_percent_script(self):
        spell = self.spells[MAGMA_BLAST]
        effect = spell["effect1"]
        self.assertEqual(effect["base_points"] + effect["die_sides"], 2000)
        self.assertEqual(spell["raw_overrides"]["EffectMiscValueB_1"], 2000)
        self.assertIn((MAGMA_BLAST, "spell_dungeon_refflat_damage"), self.scripts)
        self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertEqual(self._const("kMagmaBlastPct"), "20.f")

    # --- the looks ----------------------------------------------------------------------------------------------------

    def test_the_looks_use_the_v2_visuals(self):
        expected = {
            CLAP: visuals.EM_MAGMA_CLAP_HIT, CLAP_RING: visuals.EM_MAGMA_CLAP_RING,
            MARK: visuals.EM_VOLCANIC_BLAST_MARK, BLAST: visuals.EM_VOLCANIC_BLAST,
            STONE_LOOK: visuals.EM_VOLCANIC_STONE, PILLAR: visuals.EM_RAGNAROS_AWAKENS, ERUPTION: visuals.EM_FIRESTORM,
            MAGMA_BLAST: visuals.EM_MAGMA_CLAP_HIT,
        }
        for spell_id, sv in expected.items():
            self.assertEqual(self.spells[spell_id]["raw_overrides"].get("SpellVisualID_1"), sv, spell_id)
        self.assertEqual(visuals.EM_VOLCANIC_STONE, visuals.SHIPPED_LAVA_POOL[5])     # the 5 yd stone

    def test_no_wrong_listed_look_is_wired(self):
        for spell in self.spells.values():
            self.assertNotIn(spell["raw_overrides"].get("SpellVisualID_1"), WRONG_SPELL_VISUALS, spell["id"])

    # --- the Avatar and the numbers -----------------------------------------------------------------------------------

    def test_the_avatar(self):
        self.assertEqual(self._const("kAvatarDisplay"), str(visuals.DISPLAY_AVATAR_OF_RAGNAROS))
        self.assertEqual(self._const("kAvatarHealth"), "260000")
        low, high = visuals.AVATAR_SCALE_RANGE
        self.assertEqual(float(self._const("kAvatarScaleMin").rstrip("f")), low)
        self.assertEqual(float(self._const("kAvatarScaleMax").rstrip("f")), high)
        self.assertTrue(low <= float(self._const("kAvatarScale").rstrip("f")) <= high)
        self.assertIn("SetDisplayId(kAvatarDisplay, kAvatarScale)", self.script)
        self.assertIn("Flex::SetHealth(boss, kAvatarHealth, true)", self.script)
        self.assertIn("SetControlled(true, UNIT_STATE_ROOT)", self.script)

    def test_the_stone_stays_out_of_the_melee_ring(self):
        # R-2-C m4, orchestrator default: the stone lands at StoneSpot, outside the rooted Avatar's melee ring.
        self.assertIn("Vec2 spot = StoneSpot(avatar, boss->GetOrientation(), mark);", self.script)
        self.assertIn("kStoneClearYd = AvatarMeleeRingYd() + kStoneRadiusYd", self.logic)

    def test_the_spec_numbers(self):
        for name, value in (("kClapFirstMs", "10000"), ("kClapEveryMs", "20000"), ("kClapRunOutYd", "30.f"),
                            ("kClapNearYd", "10.f"), ("kClapFarYd", "40.f"), ("kClapNearPct", "70.f"),
                            ("kClapFarPct", "15.f"), ("kBlastFirstMs", "15000"), ("kBlastEveryMs", "25000"),
                            ("kBlastRadiusYd", "8.f"), ("kBlastTotalPct", "80.f"), ("kStoneRadiusYd", "5.f"),
                            ("kStonePct", "8.f")):
            self.assertEqual(self._const(name), value, name)

    # --- the hooks, the texts, the SQL --------------------------------------------------------------------------------

    def test_the_factory_rides_d23s_hooks(self):
        self.assertIn("BrdEmperor::RegisterEmperorHardMode(", self.script)
        for hook in ("void OnAwaken(EmperorFight& fight) override", "void OnRise(EmperorFight& fight) override",
                     "void OnUpdate(EmperorFight& fight, uint32 /*diff*/) override",
                     "void OnEnd(EmperorFight& fight, bool died) override"):
            self.assertIn(hook, self.script, hook)
        # Rule 1: the loot bit at the trigger, never in a death hook.
        self.assertIn("DungeonKit::SetHardModeLoot(boss, true)", self.script)
        self.assertNotIn("JustDied", re.sub(r"//.*|/\*.*?\*/", "", self.script, flags=re.S))
        self.assertIn('BrdTest::RegisterBoss("avatar"', self.script)

    def test_it_says_d23s_texts_and_writes_no_sql(self):
        self.assertRegex(self.d23_logic, r"EMOTE_EM_MAGMA_CLAP\s*=\s*11,")
        self.assertRegex(self.d23_logic, r"EMOTE_EM_VOLCANIC_BLAST\s*=\s*12,")
        self.assertIn("BrdEmperor::EMOTE_EM_MAGMA_CLAP", self.script)
        self.assertIn("Talk(BrdEmperor::EMOTE_EM_VOLCANIC_BLAST, target)", self.script)
        self.assertRegex(self.d23_sql, r"\(9019, 11, 0, '%s brings his hands together")
        self.assertRegex(self.d23_sql, r"\(9019, 12, 0, '%s marks \$n for a Volcanic Blast")
        self.assertFalse(OWN_SQL.exists(), "D24 has no row of its own to write (texts are D23's)")


if __name__ == "__main__":
    unittest.main()
