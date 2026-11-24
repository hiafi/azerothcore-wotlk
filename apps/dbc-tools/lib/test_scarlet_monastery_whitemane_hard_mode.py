"""
Scarlet Monastery build WP-D14H, Whitemane's hard mode (The Truth):
source/npcs/scarlet_monastery/whitemane_hard_mode.py (the vigil Fairbanks, the spirit of Alexandros and the spells
213190-213207), data/sql/updates/pending_db_world/rev_whitemane_hard_mode_scarlet_monastery.sql (the texts, the Torch's
binding), and the C++ they must agree with (modules/mod-dungeon-bosses src/ScarletMonastery/WhitemaneHardModeLogic.h
and whitemane_hard_mode.cpp).

Checks:
  - the eighteen spells sit in the D14H slice and the C++ names the same ids in the same order; the fear is a 5 s
    no-threat fear; the curse a 2 s Curse DoT ticking every second for 12 s that ignores his modifiers; the shield a
    purgeable absorb on an ally; the Heal a 3 s interruptible HEAL_PCT 15 on an ally; the two hits Holy resolve copies;
    the swing a missile at a point; every look a V constant, none WRONG (never the empty wielder aura 7582);
  - the vigil Fairbanks (level 60 elite paladin, 130k, display 2605, stun immune, no loot, no bind, the wave-gated
    script, H's heroic entry 310487) and the spirit (not selectable, not attackable, friendly, the specter
    display, no heroic template, the wave-gated script);
  - the SQL: the five lines (the spec's texts, types and broadcast ids) and the Torch bound to go_sm_torch with its
    SmartAI rows dropped; the C++ registers the Torch on every wave and the two creature AIs only once wave 2 binds;
  - the numbers the dbc-tools file pins are the header's.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scarlet_monastery_whitemane_hard_mode.py
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
from lib import test_scarlet_monastery_kit as kit_test  # noqa: E402
from lib import test_scarlet_monastery_vfx as vfx_test  # noqa: E402
from source.npcs.scarlet_monastery import _common as common  # noqa: E402
from source.npcs.scarlet_monastery import _visuals as visuals  # noqa: E402

MDB = REPO_ROOT / "modules" / "mod-dungeon-bosses"
LOGIC = MDB / "src" / "ScarletMonastery" / "WhitemaneHardModeLogic.h"
SCRIPT = MDB / "src" / "ScarletMonastery" / "whitemane_hard_mode.cpp"
HEADER = MDB / "src" / "ScarletMonastery" / "ScarletMonasteryRework.h"
WM_LOGIC = MDB / "src" / "ScarletMonastery" / "WhitemaneLogic.h"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_whitemane_hard_mode_scarlet_monastery.sql"
DT_FILE = TOOL_ROOT / "source" / "npcs" / "scarlet_monastery" / "whitemane_hard_mode.py"

SLICE = range(213190, 213240)
FIRST = 213190
NAMES = ("SPELL_TT_TORCH_FEAR", "SPELL_TT_TELEPORT_OUT", "SPELL_TT_TELEPORT_IN", "SPELL_TT_WARD", "SPELL_TT_CURSE",
         "SPELL_TT_CURSE_MARK", "SPELL_TT_SHIELD", "SPELL_TT_HEAL", "SPELL_TT_SPIRIT_GLOW", "SPELL_TT_LIGHT_CAST",
         "SPELL_TT_LIGHT_HIT", "SPELL_TT_LIGHT_PILLAR", "SPELL_TT_VERDICT_RAISE", "SPELL_TT_VERDICT_SWING",
         "SPELL_TT_VERDICT_HIT", "SPELL_TT_VERDICT_IMPACT", "SPELL_TT_SHAME", "SPELL_TT_SPIRIT_FADE")
EFFECT_SCHOOL_DAMAGE, EFFECT_DUMMY, EFFECT_APPLY_AURA, EFFECT_HEAL_PCT = 2, 3, 6, 136
AURA_PERIODIC_DAMAGE, AURA_DUMMY, AURA_MOD_FEAR, AURA_SCHOOL_ABSORB = 3, 4, 7, 69
SCHOOL_NORMAL, SCHOOL_HOLY = 1, 2
DISPEL_MAGIC, DISPEL_CURSE = 1, 2
TARGET_UNIT_TARGET_ENEMY, TARGET_UNIT_TARGET_ALLY, TARGET_DEST_DEST = 6, 21, 87
ATTR1_NO_THREAT = 0x00000400
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
FAIRBANKS, SPIRIT, WHITEMANE, TORCH = 300956, 300957, 3977, 97701

# CATH "Text (hard mode)": (entry, group, text, type, broadcast).
LINES = (
    (300956, 0, "Ask him... how his father died.", 12, 0),
    (300957, 0, "Renault...", 12, 12469),
    (300957, 1, "You are forgiven...", 12, 12473),
    (300957, 2, "%s raises the Ashbringer!", 41, 0),
    (3977, 6, "Lies! He is the Crusade's champion!", 14, 0),
)


class WhitemaneHardModeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = kit_test._load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates}
        cls.models = {}
        for e in reg.creature_template_models:
            cls.models.setdefault(int(e["CreatureID"]), []).append(e)
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.logic = LOGIC.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.wm_logic = WM_LOGIC.read_text(encoding="utf-8")
        cls.dt = DT_FILE.read_text(encoding="utf-8")

    def _const(self, name: str, text: str | None = None) -> str:
        match = re.search(rf"{name}\s*(?:=|\{{)\s*([^;}}]+?)\s*(?:;|\}};)", text or self.logic)
        self.assertIsNotNone(match, name)
        return match.group(1)

    def _dt_num(self, name: str) -> float:
        match = re.search(rf"^{name} = ([\d.]+)", self.dt, re.M)
        self.assertIsNotNone(match, name)
        return float(match.group(1))

    def _visual(self, spell_id: int) -> int:
        return self.spells[spell_id]["raw_overrides"].get("SpellVisualID_1", 0)

    # --- the spells ---------------------------------------------------------------------------------------------------

    def test_the_spells_sit_in_the_d14h_slice(self):
        self.assertEqual(sorted(self.spells), list(range(FIRST, FIRST + len(NAMES))))
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery", {"spell": list(self.spells)}), [])
        self.assertIn("kSpellsTheTruth{ 213190, 213239 }", re.sub(r"\s+", " ", self.header))

    def test_the_cpp_names_the_same_ids(self):
        for offset, name in enumerate(NAMES):
            self.assertRegex(self.logic, rf"{name}\s*=\s*kSpellSlice\.first \+ {offset},", name)
        self.assertIn("kLastSpell = SPELL_TT_SPIRIT_FADE;", self.logic)

    def test_the_trigger(self):
        fear = self.spells[FIRST]
        eff = fear["effect1"]
        self.assertEqual((eff["type"], eff["apply_aura"]), (EFFECT_APPLY_AURA, AURA_MOD_FEAR))
        self.assertEqual(fear["duration_ms"], int(self._const("kFearMs")))
        self.assertEqual(fear["duration_ms"], 5000)
        self.assertTrue(fear["raw_overrides"]["AttributesEx"] & ATTR1_NO_THREAT)     # out of combat: engages no one
        self.assertEqual(self._visual(FIRST), visuals.HM_FEAR)
        leave = self.spells[FIRST + 1]
        self.assertEqual(leave["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(leave["duration_ms"], int(self._const("kLeaveLookMs")))
        self.assertGreater(leave["duration_ms"], int(self._const("kLeaveMs")))
        self.assertEqual(self._visual(FIRST + 1), visuals.HM_TELEPORT)
        self.assertEqual(self._visual(FIRST + 2), visuals.HM_TELEPORT)
        self.assertEqual(self._const("kTorchRefusedText"), '"The Torch will not move."')

    def test_fairbanks_kit(self):
        ward = self.spells[FIRST + 3]
        self.assertEqual((ward["effect1"]["apply_aura"], ward["dispel"]), (AURA_DUMMY, 0))   # the script halves
        self.assertEqual(self._visual(FIRST + 3), visuals.HM_WARD)
        curse = self.spells[FIRST + 4]
        eff = curse["effect1"]
        self.assertEqual((eff["type"], eff["apply_aura"]), (EFFECT_APPLY_AURA, AURA_PERIODIC_DAMAGE))
        self.assertEqual(eff["amplitude"], int(self._const("kCurseTickMs")))
        self.assertEqual(curse["duration_ms"], int(self._const("kCurseMs")))
        self.assertEqual(curse["cast_time_ms"], int(self._const("kCurseCastMs")))
        self.assertEqual((eff["base_points"], eff["die_sides"]), (0, 0))                 # the script's base point
        self.assertEqual(curse["dispel"], DISPEL_CURSE)
        self.assertEqual(curse["school"], SCHOOL_NORMAL)
        self.assertEqual(eff["implicit_target_a"], TARGET_UNIT_TARGET_ENEMY)
        self.assertTrue(curse["raw_overrides"]["AttributesEx3"] & ATTR3_IGNORE_CASTER_MODIFIERS)   # rule 2
        self.assertEqual(self._visual(FIRST + 4), visuals.HM_CURSE)
        mark = self.spells[FIRST + 5]
        self.assertEqual((mark["effect1"]["apply_aura"], mark["dispel"]), (AURA_DUMMY, 0))
        self.assertEqual(self._visual(FIRST + 5), visuals.HM_CURSE_MARK)
        shield = self.spells[FIRST + 6]
        eff = shield["effect1"]
        self.assertEqual((eff["apply_aura"], eff["implicit_target_a"]), (AURA_SCHOOL_ABSORB, TARGET_UNIT_TARGET_ALLY))
        self.assertEqual(shield["dispel"], DISPEL_MAGIC)                                 # purgeable
        self.assertEqual(shield["duration_ms"], int(self._const("kShieldAuraMs")))
        self.assertEqual(self._visual(FIRST + 6), visuals.WM_PWS)
        heal = self.spells[FIRST + 7]
        eff = heal["effect1"]
        self.assertEqual((eff["type"], eff["implicit_target_a"]), (EFFECT_HEAL_PCT, TARGET_UNIT_TARGET_ALLY))
        self.assertEqual(eff["base_points"], int(self._const("kHealPct")))
        self.assertEqual(heal["cast_time_ms"], int(self._const("kHealCastMs")))
        self.assertEqual(heal["raw_overrides"]["InterruptFlags"], 15)                    # interruptible
        self.assertEqual(heal["school"], SCHOOL_HOLY)
        self.assertEqual(self._visual(FIRST + 7), visuals.WM_HEAL)
        # the descriptor lists them
        for text in ("d.targets.emplace_back(NPC_SM_VIGIL_FAIRBANKS, kFairbanksTargetPriority);",
                     "d.interrupts.emplace_back(NPC_SM_VIGIL_FAIRBANKS, SPELL_TT_HEAL, kFairbanksHealKickPriority,",
                     "d.dispels.emplace_back(SPELL_TT_CURSE, kCurseDispelPriority);",
                     "d.purges.emplace_back(0u, SPELL_TT_SHIELD, kShieldPurgePriority);",
                     "d.ignores.emplace_back(NPC_SM_ALEXANDROS_SPIRIT);"):
            self.assertIn(text, self.script)

    def test_the_father(self):
        for hit in (FIRST + 10, FIRST + 14):
            spell = self.spells[hit]
            self.assertEqual(spell["school"], SCHOOL_HOLY)
            self.assertEqual(spell["effect1"]["type"], EFFECT_SCHOOL_DAMAGE)
            self.assertIn((hit, "spell_boss_mechanics_resolve"), self.scripts)
        self.assertIn(".Spell(SPELL_TT_LIGHT_HIT)", self.script)
        self.assertIn(".Spell(SPELL_TT_VERDICT_HIT)", self.script)
        # the light: Weakened for the non-tanks, the tank its own circle without (rule 16: TankDamage on both)
        self.assertRegex(self.script, r"light\.Damage\(kLightPct\)\.TankDamage\(kLightTankPct\)\.Weakened\(\)")
        self.assertRegex(self.script, r"tankLight\.Damage\(kLightTankPct\)\.TankDamage\(kLightTankPct\)\.School")
        self.assertNotRegex(self.script, r"tankLight\.[^;]*Weakened")
        self.assertIn("tankLight.Park(m->Mograine());", self.script)
        # the Verdict: no Weakened (50% or more), the tank included
        self.assertRegex(self.script, r"verdict\.Damage\(kVerdictPct\)\.TankDamage\(kVerdictPct\)\.School")
        self.assertNotRegex(self.script, r"verdict\.[^;]*Weakened")
        swing = self.spells[FIRST + 13]
        self.assertEqual(swing["effect1"]["implicit_target_a"], TARGET_DEST_DEST)
        self.assertEqual(swing["raw_overrides"]["Speed"], float(self._const("kSwingSpeedYd").rstrip("f")))
        self.assertEqual(self._dt_num("SWING_SPEED"), swing["raw_overrides"]["Speed"])
        self.assertEqual(self._visual(FIRST + 12), visuals.HM_VERDICT)
        self.assertEqual(self._visual(FIRST + 13), visuals.HM_VERDICT)
        self.assertEqual(visuals.HM_VERDICT, 8618)                                        # never SV 7582
        self.assertEqual(self._visual(FIRST + 15), visuals.HM_VERDICT_IMPACT)
        self.assertEqual(self._visual(FIRST + 9), visuals.HM_LIGHT)
        self.assertEqual(self._visual(FIRST + 11), visuals.HM_LIGHT_PILLAR)
        self.assertEqual(visuals.HM_LIGHT_PILLAR, visuals.SV_PILLAR_6)                    # never SV 12479
        self.assertEqual(self._visual(FIRST + 8), visuals.HM_SPIRIT_GLOW)
        shame = self.spells[FIRST + 16]
        self.assertEqual(shame["duration_ms"], int(self._const("kVerdictKneelMs")))
        self.assertEqual(self._visual(FIRST + 16), visuals.WM_KNEEL)
        self.assertEqual(self._visual(FIRST + 17), visuals.HM_TELEPORT)

    def test_the_looks_use_the_v_constants_and_none_is_wrong(self):
        for spell_id, spell in self.spells.items():
            self.assertNotIn(spell["raw_overrides"].get("SpellVisualID_1", 0), vfx_test.WRONG_SPELL_VISUALS,
                             spell_id)
        self.assertEqual(int(self._const("kItemAlexandrosBlade")), visuals.ITEM_ALEXANDROS_BLADE)

    def test_the_numbers_the_dt_file_pins(self):
        for dt_name, cpp in (("FEAR_MS", "kFearMs"), ("LEAVE_LOOK_MS", "kLeaveLookMs"),
                             ("CURSE_CAST_MS", "kCurseCastMs"), ("CURSE_TICK_MS", "kCurseTickMs"),
                             ("CURSE_MS", "kCurseMs"),
                             ("SHIELD_AURA_MS", "kShieldAuraMs"), ("HEAL_CAST_MS", "kHealCastMs"),
                             ("HEAL_PCT", "kHealPct"), ("SHAME_MAX_MS", "kVerdictKneelMs")):
            self.assertEqual(self._dt_num(dt_name), float(self._const(cpp)), dt_name)
        self.assertEqual(self._dt_num("CAST_RANGE"), float(self._const("kCastRangeYd").rstrip("f")))
        self.assertEqual(int(self._dt_num("FAIRBANKS_HEALTH")), int(self._const("kFairbanksHealth")))

    # --- the creatures ------------------------------------------------------------------------------------------------

    def test_the_vigil_fairbanks(self):
        c = self.creatures[FAIRBANKS]
        self.assertEqual(c["name"], "High Inquisitor Fairbanks")
        self.assertEqual(c["ScriptName"], "npc_sm_vigil_fairbanks" if common.BIND_WAVE_2 else "")
        self.assertEqual(c["AIName"], "")
        self.assertEqual((c["minlevel"], c["maxlevel"], c["rank"], c["unit_class"], c["faction"]), (60, 60, 1, 2, 67))
        self.assertAlmostEqual(c["HealthModifier"] * 2442, 130000, delta=10)
        self.assertEqual(c["CreatureImmunitiesId"], 1972)                               # stun immune
        self.assertEqual((c["lootid"], c["flags_extra"] & 1), (0, 0))                   # no loot, no bind
        self.assertEqual(c["unit_flags"], 0)                                            # attackable (rule 10)
        self.assertEqual(c["detection_range"], 0.0)                                     # never pulls himself
        self.assertEqual(c.get("difficulty_entry_1", 0), 310487)                      # H's table (all 30 declared)
        self.assertEqual(int(self._dt_num("FAIRBANKS_HEROIC_PLANNED")), 310487)
        self.assertEqual([m["CreatureDisplayID"] for m in self.models[FAIRBANKS]], [visuals.DISPLAY_FAIRBANKS])
        self.assertEqual(visuals.DISPLAY_FAIRBANKS, 2605)
        self.assertIn("creature_template(300956, ", self.dt)        # H finds the kit units by this literal pattern

    def test_the_spirit(self):
        c = self.creatures[SPIRIT]
        self.assertEqual((c["name"], c["subname"]), ("Highlord Mograine", "The Ashbringer"))
        self.assertEqual(c["ScriptName"], "npc_sm_alexandros_spirit" if common.BIND_WAVE_2 else "")
        self.assertTrue(c["unit_flags"] & 0x02000000)                                   # not selectable
        self.assertTrue(c["unit_flags"] & 0x2)                                          # not attackable
        self.assertEqual(c["faction"], 35)                                              # friendly
        self.assertEqual(c["DamageModifier"], 0.0)
        self.assertNotIn("difficulty_entry_1", {k for k, v in c.items() if v})          # no heroic template
        self.assertEqual([m["CreatureDisplayID"] for m in self.models[SPIRIT]], [visuals.DISPLAY_SPECTRE_ALEXANDROS])
        self.assertEqual(visuals.DISPLAY_SPECTRE_ALEXANDROS, 90804)
        self.assertIn("creature_template(300957, ", self.dt)

    def test_ids_sit_in_the_reservation_and_match_the_header(self):
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery", {"creature": [FAIRBANKS, SPIRIT]}), [])
        self.assertRegex(self.header, r"NPC_SM_VIGIL_FAIRBANKS\s*=\s*300956,")
        self.assertRegex(self.header, r"NPC_SM_ALEXANDROS_SPIRIT\s*=\s*300957,")
        self.assertRegex(self.header, r"GO_TORCH\s*=\s*97701,")
        self.assertRegex(self.header, r"GO_SECRET_DOOR\s*=\s*97700,")

    def test_the_registrations(self):
        # the Torch on every wave (its rev binds it now); the two creature AIs once wave 2 binds (as their ScriptNames)
        self.assertIn("RegisterDungeonReworkGameObjectAI(go_sm_torch, ScarletMonasteryRework::kInstanceScriptName);",
                      self.script)
        self.assertRegex(self.script, r"if \(kWave2Bound\)\n\s+\{\n\s+RegisterDungeonReworkCreatureAI\("
                                      r"npc_sm_vigil_fairbanks, ScarletMonasteryRework::kInstanceScriptName\);\n\s+"
                                      r"RegisterDungeonReworkCreatureAI\(npc_sm_alexandros_spirit, ")
        self.assertIn("SmWhitemane::RegisterWhitemaneHardMode(", self.script)
        self.assertIn("SmWhitemane::RegisterWhitemaneIdleHook(", self.script)

    # --- the SQL ------------------------------------------------------------------------------------------------------

    def test_the_five_lines(self):
        rows = re.findall(r"^\((\d+), (\d+), (\d+), '((?:[^']|'')*)', (\d+), 0, 100, (\d+), 0, 0, (\d+), (\d+),",
                          self.sql, re.M)
        got = tuple((int(e), int(g), t.replace("''", "'"), int(ty), int(b)) for e, g, i, t, ty, em, b, _ in rows)
        self.assertEqual(got, LINES)
        self.assertTrue(all(int(i) == 0 for _, _, i, _, _, _, _, _ in rows))
        # The Verdict's warning reaches the whole floor (the spirit over the altar, the nave 94 yd long): TextRange 3
        # (map), as D12's emotes; the rest keep the default range.
        ranges = {(int(e), int(g)): int(r) for e, g, _, _, _, _, _, r in rows}
        self.assertEqual(ranges.pop((300957, 2)), 3)
        self.assertTrue(all(r == 0 for r in ranges.values()), ranges)
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` IN (300956, 300957);", self.sql)
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 3977 AND `GroupID` = 6;", self.sql)
        for name, group in (("SAY_FAIRBANKS_TRUTH", 0), ("SAY_SPIRIT_RENAULT", 0), ("SAY_SPIRIT_FORGIVEN", 1),
                            ("EMOTE_SPIRIT_RAISES", 2), ("SAY_MOGRAINE_FATHER", 4), ("SAY_MOGRAINE_FORGIVE", 5)):
            self.assertRegex(self.logic, rf"{name}\s*=\s*{group},")
        self.assertRegex(self.wm_logic, r"SAY_WHITEMANE_LIES\s*=\s*6,")
        for call in ("Talk(SAY_FAIRBANKS_TRUTH)", "UnitTalk(spirit, SAY_SPIRIT_RENAULT)",
                     "UnitTalk(spirit, SAY_SPIRIT_FORGIVEN)", "UnitTalk(spirit, EMOTE_SPIRIT_RAISES)",
                     "m->Say(SAY_MOGRAINE_FATHER)", "m->Say(SAY_MOGRAINE_FORGIVE)",
                     "fight.Say(SmWhitemane::SAY_WHITEMANE_LIES)"):
            self.assertIn(call, self.script)
        # S0's text ranges: the vigil Fairbanks 0, Whitemane 0-7; the spirit's 2 waits on the shared-file request.
        self.assertIn("{ NPC_SM_VIGIL_FAIRBANKS, 0, 0, 0 },", self.header)
        self.assertIn("{ NPC_WHITEMANE, 0, 7, 3 },", self.header)
        self.assertRegex(self.header, r"\{ NPC_SM_ALEXANDROS_SPIRIT, 0, [12], 0 \},")

    def test_the_torch_is_bound(self):
        self.assertIn("DELETE FROM `smart_scripts` WHERE `entryorguid` = 97701 AND `source_type` = 1;", self.sql)
        self.assertIn("UPDATE `gameobject_template` SET `AIName` = '', `ScriptName` = 'go_sm_torch' WHERE "
                      "`entry` = 97701;", self.sql)
        self.assertNotRegex(self.sql, r"INSERT INTO `(creature|gameobject|smart_scripts)` ")     # rule 14: no spawn

    def test_no_line_over_120_columns(self):
        for path in (SQL, DT_FILE, LOGIC, SCRIPT, MDB / "tests" / "sm_whitemane_hard_mode_test.cpp", Path(__file__)):
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                self.assertLessEqual(len(line), 120, f"{path.name}:{n}")


if __name__ == "__main__":
    unittest.main()
