"""
Ragefire Chasm build WP-D1, Oggleflint: source/npcs/ragefire_chasm/oggleflint.py (his columns, the Borer and the spells
213550-213557), data/sql/updates/pending_db_world/rev_oggleflint_ragefire_chasm.sql (his texts), and the C++ they must
agree with (modules/mod-dungeon-bosses src/RagefireChasm/OggleflintLogic.h, RagefireChasmRework.h namespace Oggleflint
and boss_oggleflint_rework.cpp).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_ragefire_chasm_oggleflint.py
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
from lib import test_ragefire_chasm_npcs as skeleton  # noqa: E402
from source.npcs.ragefire_chasm import _common as common  # noqa: E402
from source.npcs.ragefire_chasm import _visuals as visuals  # noqa: E402

MDB = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "RagefireChasm"
LOGIC = MDB / "OggleflintLogic.h"
SCRIPT = MDB / "boss_oggleflint_rework.cpp"
HEADER = MDB / "RagefireChasmRework.h"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_oggleflint_ragefire_chasm.sql"

FIRST = 213550
SLICE = range(213550, 213580)
NAMES = ("SPELL_OG_ERUPTION", "SPELL_OG_ERUPTION_LOOK", "SPELL_OG_TUNNEL", "SPELL_OG_SWING_BAR", "SPELL_OG_SWING",
         "SPELL_OG_SWING_TANK", "SPELL_OG_SWING_LOOK", "SPELL_OG_BLOW")
ERUPTION, ERUPTION_LOOK, TUNNEL, BAR, SWING, TANK, SWING_LOOK, BLOW = range(FIRST, FIRST + len(NAMES))
EFFECT_SCHOOL_DAMAGE, EFFECT_DUMMY, EFFECT_APPLY_AURA = 2, 3, 6
AURA_DUMMY = 4
SCHOOL_PHYSICAL = 1
TARGET_DEST_DEST = 87
OGGLEFLINT, BORER = 11517, 300985
IGNORE_CASTER_MODIFIERS = 0x20000000


class OggleflintTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = skeleton._load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits}
        cls.models = {int(e["CreatureID"]): e for e in reg.creature_template_models}
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.logic = LOGIC.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        header = HEADER.read_text(encoding="utf-8")
        cls.header = header
        cls.tune = header[header.index("namespace Oggleflint"):header.index("namespace Jergosh")]

    def _tune(self, name: str) -> str:
        match = re.search(rf"\b{name}\s*(?:=\s*|\{{)([^;}}]+?)\s*(?:;|\}};)", self.tune)
        self.assertIsNotNone(match, name)
        return match.group(1).replace(" ", "")

    # --- the spells ---------------------------------------------------------------------------------------------------

    def test_the_spells_sit_in_the_d1_slice(self):
        self.assertEqual(sorted(self.spells), list(range(FIRST, FIRST + len(NAMES))))
        self.assertEqual(id_blocks.out_of_reservation("ragefire_chasm", {"spell": list(self.spells)}), [])
        self.assertIn("kSpellsOggleflint{ 213550, 213579 }", self.header)

    def test_the_cpp_names_the_same_ids(self):
        for offset, name in enumerate(NAMES):
            self.assertRegex(self.logic, rf"{name}\s*=\s*kSpellSlice\.first \+ {offset},", name)

    def test_the_registry_hits_are_resolve_copies(self):
        for spell_id in (ERUPTION, SWING, BLOW):
            spell = self.spells[spell_id]
            self.assertEqual(spell["school"], SCHOOL_PHYSICAL, spell_id)
            self.assertEqual(spell["effect1"]["type"], EFFECT_SCHOOL_DAMAGE, spell_id)
            self.assertIn((spell_id, "spell_boss_mechanics_resolve"), self.scripts, spell_id)
            self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & IGNORE_CASTER_MODIFIERS, spell_id)
        for name in ("ERUPTION", "SWING", "BLOW"):
            self.assertIn(f".Spell(SPELL_OG_{name})", self.script)

    def test_the_tank_hit_carries_the_headers_percent(self):
        spell = self.spells[TANK]
        effect = spell["effect1"]
        self.assertEqual(effect["type"], EFFECT_SCHOOL_DAMAGE)
        self.assertEqual(self._tune("kSwingTankPct"), "10.f")
        self.assertEqual(effect["base_points"] + effect["die_sides"], 1000)
        self.assertEqual(int(spell["raw_overrides"].get("EffectMiscValueB_1", 0)), 0)      # the same on heroic
        self.assertIn((TANK, "spell_dungeon_refflat_damage"), self.scripts)
        self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & IGNORE_CASTER_MODIFIERS)
        # A spell row without a range lands at 0 yd: the triggered cast would fail silently.
        self.assertEqual(float(spell["range_yards"]), 100.0)

    def test_the_bar_is_the_wind_up_and_cannot_be_kicked(self):
        bar = self.spells[BAR]
        self.assertEqual(bar["cast_time_ms"], int(self._tune("kSwingWarnMs")))
        self.assertEqual((bar["raw_overrides"]["InterruptFlags"], bar["raw_overrides"]["PreventionType"]), (0, 0))

    def test_nothing_of_his_can_be_kicked(self):
        for spell_id, spell in self.spells.items():
            self.assertEqual(int(spell["raw_overrides"].get("InterruptFlags", 0)), 0, spell_id)
            self.assertEqual(int(spell["raw_overrides"].get("PreventionType", 0)), 0, spell_id)

    def test_the_looks_are_the_approved_picks(self):
        for spell_id, visual in ((ERUPTION_LOOK, visuals.OG_BORER_ERUPTION), (TUNNEL, visuals.OG_BORER_TRAIL),
                                 (SWING, visuals.OG_CLUB_SWING), (TANK, visuals.OG_CLUB_SWING),
                                 (SWING_LOOK, visuals.OG_CLUB_SWING), (BLOW, visuals.OG_BEATING_BLOW)):
            self.assertEqual(self.spells[spell_id]["raw_overrides"]["SpellVisualID_1"], visual, spell_id)
        for spell_id in (ERUPTION, BAR):
            self.assertNotIn("SpellVisualID_1", self.spells[spell_id]["raw_overrides"], spell_id)
        for spell_id in (ERUPTION_LOOK, SWING_LOOK):
            effect = self.spells[spell_id]["effect1"]
            self.assertEqual((effect["type"], effect["implicit_target_a"]), (EFFECT_DUMMY, TARGET_DEST_DEST))
            self.assertEqual(float(self.spells[spell_id]["range_yards"]), 100.0)
        tunnel = self.spells[TUNNEL]
        self.assertEqual((tunnel["effect1"]["type"], tunnel["effect1"]["apply_aura"]),
                         (EFFECT_APPLY_AURA, AURA_DUMMY))
        self.assertEqual(tunnel["duration_ms"], -1)

    def test_the_worm_is_the_approved_display_and_scale(self):
        self.assertIn(f"kWormDisplay = {visuals.DISPLAY_BORER_ERUPT};", self.logic)
        low, high = visuals.BORER_ERUPT_SCALE_RANGE
        scale = float(re.search(r"kWormScale = ([\d.]+)f;", self.logic).group(1))
        self.assertTrue(low <= scale <= high)

    # --- the numbers --------------------------------------------------------------------------------------------------

    def test_the_worm_keeps_its_scale(self):
        # SetDisplayId puts the native scale back unless it is told another (Unit::RecalculateObjectScale).
        self.assertIn("SetDisplayId(kWormDisplay, kWormScale)", self.script)
        self.assertNotIn("SetObjectScale(kWormScale)", self.script)

    def test_no_assist_calls(self):
        # The flag stops the first call only: every tick, before UpdateVictim.
        self.assertRegex(self.script, r"me->SetAssistanceTimer\(0\);[^\n]*\n\s+if \(!UpdateVictim\(\)\)")

    def test_the_header_is_the_build_spec(self):
        for name, value in (("kHealth", "21360,317408"), ("kHuntFirstMs", "10000,10000"),
                            ("kHuntEveryMs", "15000,12000"), ("kChaseMs", "4000"), ("kChaseSpeed", "4.f,5.f"),
                            ("kChaseRadius", "3.f"), ("kExtraBorerEveryMs", "40000"), ("kEruptionWarnMs", "2000"),
                            ("kEruptionRadius", "4.f"), ("kEruptionPct", "30.f,45.f"), ("kSwingFirstMs", "6000,6000"),
                            ("kSwingEveryMs", "12000,12000"), ("kSwingAngleDeg", "90.f"), ("kSwingLength", "8.f"),
                            ("kSwingPct", "30.f,40.f"), ("kBeatingFirstMs", "15000"), ("kBeatingEveryMs", "20000"),
                            ("kBeatingBlows", "3"), ("kBeatingBlowMs", "1500"), ("kBeatingRadius", "3.f"),
                            ("kBeatingPct", "35.f"), ("kHuntSwingGapMs", "3000")):
            self.assertEqual(self._tune(name), value, name)

    # --- the creatures ------------------------------------------------------------------------------------------------

    def test_the_boss_keeps_the_skeletons_columns(self):
        row = self.edits[OGGLEFLINT]
        self.assertEqual(row["ScriptName"], "boss_oggleflint_rework")
        self.assertEqual(row["CreatureImmunitiesId"], common.IMMUNITY_BOSS_STUN)

    def test_the_borer_is_a_hazard_never_a_target(self):
        row = self.creatures[BORER]
        self.assertEqual(row["name"], "The Borer")
        self.assertEqual(row["ScriptName"], "npc_rfc_borer")
        self.assertEqual(row["AIName"], "")
        self.assertEqual(int(row["unit_flags"]), 0x2 | 0x02000000)
        self.assertFalse(int(row["flags_extra"]) & 0x80, "a trigger's model is invisible: the worm must show")
        self.assertEqual(float(row["DamageModifier"]), 0.0)
        self.assertNotIn("difficulty_entry_1", {k for k, v in row.items() if v})
        self.assertEqual(int(self.models[BORER]["CreatureDisplayID"]), visuals.DISPLAY_BORER_TUNNEL)
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_rfc_borer,", self.script)

    # --- the SQL ------------------------------------------------------------------------------------------------------

    def test_the_texts_are_the_build_spec(self):
        rows = re.findall(r"\(11517, (\d), 0, '([^']*)', (\d+), 0, 100, 0, 0, 0, 0, 0,", self.sql)
        self.assertEqual(rows, [
            ("0", "%s bellows, and the ground churns toward $n!", "41"),
            ("1", "%s raises his club high!", "41"),
            ("2", "%s glares at $n and hefts his club!", "41"),
        ])
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 11517 AND `GroupID` BETWEEN 0 AND 2;", self.sql)
        statements = re.sub(r"^--.*$", "", self.sql, flags=re.M)
        self.assertNotIn("smart_scripts", statements)      # S0's rev owns it


if __name__ == "__main__":
    unittest.main()
