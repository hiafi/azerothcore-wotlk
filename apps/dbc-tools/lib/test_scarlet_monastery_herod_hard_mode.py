"""
Scarlet Monastery build WP-D11H, Herod's hard mode (Call to Arms):
source/npcs/scarlet_monastery/herod_hard_mode.py (the Garrison Trainee, the planted Ravager and the spells
213020-213029), data/sql/updates/pending_db_world/rev_herod_hard_mode_scarlet_monastery.sql (Herod's lines 5-9, the
wall rack and the planted axe's prop, the rack's heroic spawn), and the C++ they must agree with
(modules/mod-dungeon-bosses src/ScarletMonastery/HerodHardModeLogic.h and herod_hard_mode.cpp).

Checks:
  - the ten spells sit in the D11H slice and the C++ names the same ids; the red aura holds a wipe; the prayer is a
    school immunity; Zeal stacks to six (+5% damage, +5% attack speed); the beam's chain is a channel and its hit a
    Holy resolve copy; the hall's tick is 4% through the kit's percent script and ignores his modifiers; every look is
    a V constant, none WRONG;
  - the Garrison Trainee (level 60, 5k, no melee, no immunity, the trainee's displays, the wave-gated script, H's
    heroic entry once it settles) and the planted Ravager (a helper on the invisible stalker model);
  - the SQL: groups 5-8 of 3975 (the spec's lines and types), the two gameobject templates (V's displays), the rack's
    heroic-only spawn on the header's spot;
  - the numbers the dbc-tools file pins are the header's; the trainee's AI registers only once wave 2 binds.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scarlet_monastery_herod_hard_mode.py
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
from lib import test_scarlet_monastery_kit as kit_test  # noqa: E402
from lib import test_scarlet_monastery_vfx as vfx_test  # noqa: E402
from source.npcs.scarlet_monastery import _common as common  # noqa: E402
from source.npcs.scarlet_monastery import _visuals as visuals  # noqa: E402

MDB = REPO_ROOT / "modules" / "mod-dungeon-bosses"
LOGIC = MDB / "src" / "ScarletMonastery" / "HerodHardModeLogic.h"
SCRIPT = MDB / "src" / "ScarletMonastery" / "herod_hard_mode.cpp"
HEROD_LOGIC = MDB / "src" / "ScarletMonastery" / "HerodLogic.h"
HEADER = MDB / "src" / "ScarletMonastery" / "ScarletMonasteryRework.h"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_herod_hard_mode_scarlet_monastery.sql"
DT_FILE = TOOL_ROOT / "source" / "npcs" / "scarlet_monastery" / "herod_hard_mode.py"

SLICE = range(213020, 213060)
FIRST = 213020
NAMES = ("SPELL_CTA_AURA", "SPELL_CTA_PRAYER", "SPELL_CTA_PILLAR", "SPELL_CTA_ZEAL", "SPELL_CTA_FADE",
         "SPELL_CTA_GLOW", "SPELL_CTA_BEAM_LOOK", "SPELL_CTA_BEAM", "SPELL_CTA_HALL", "SPELL_CTA_HALL_LOOK")
EFFECT_SCHOOL_DAMAGE, EFFECT_APPLY_AURA, EFFECT_DUMMY = 2, 6, 3
AURA_DUMMY, AURA_SCHOOL_IMMUNITY, AURA_MOD_DAMAGE_PERCENT_DONE, AURA_MOD_MELEE_HASTE = 4, 39, 79, 138
SCHOOL_HOLY = 2
ATTR1_IS_CHANNELED = 0x00000004
ATTR1_AURA_STAYS_AFTER_COMBAT = 0x02000000
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
TRAINEE, RAVAGER, HEROD = 300944, 300945, 3975
RACK, PROP = 301328, 301329
GENERIC = 5
GO_COLUMN_COUNT = 35

# ARM "Text" (Build spec): Herod's lines 5-8, verbatim, with their types (yell 14, say 12, boss emote 41); 9 the seal.
LINES = (
    (5, "You mock the Champion of the Crusade? Then you will face all of it!", 14),
    (6, "Words. Show me steel.", 12),
    (7, "The Crusade answers!", 14),
    (8, "Herod's Door bursts open! The garrison marches to its champion!", 41),
    (9, "Herod's Door slams shut! None leave until the Champion falls.", 41),     # D11's seal (F-2c)
)


def _split_values(text: str) -> list:
    """A VALUES tuple's fields: quoted strings (with '' escapes), ints and floats."""
    out: list = []
    for match in re.finditer(r"'((?:[^']|'')*)'|(-?\d+\.\d+)|(-?\d+)", text):
        quoted, real, whole = match.groups()
        out.append(quoted.replace("''", "'") if quoted is not None else float(real) if real is not None
                   else int(whole))
    return out


class HerodHardModeTest(unittest.TestCase):
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
        cls.herod_logic = HEROD_LOGIC.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.dt = DT_FILE.read_text(encoding="utf-8")

    def _const(self, name: str, text: str | None = None) -> str:
        match = re.search(rf"{name}\s*(?:=|\{{)\s*([^;}}]+?)\s*(?:;|\}};)", text or self.logic)
        self.assertIsNotNone(match, name)
        return match.group(1)

    def _dt_int(self, name: str) -> int:
        match = re.search(rf"^{name} = (\d+)", self.dt, re.M)
        self.assertIsNotNone(match, name)
        return int(match.group(1))

    # --- the spells ---------------------------------------------------------------------------------------------------

    def test_the_spells_sit_in_the_d11h_slice(self):
        self.assertEqual(sorted(self.spells), list(range(FIRST, FIRST + len(NAMES))))
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery", {"spell": list(self.spells)}), [])
        self.assertIn("kSpellsCallToArms{ 213020, 213059 }", re.sub(r"\s+", " ", self.header))

    def test_the_cpp_names_the_same_ids(self):
        for offset, name in enumerate(NAMES):
            self.assertRegex(self.logic, rf"{name}\s*=\s*kSpellSlice\.first \+ {offset},", name)
        self.assertRegex(self.logic, r"static_assert\(SPELL_CTA_HALL_LOOK <= kSpellSlice\.last")

    def test_the_red_aura_holds_a_wipe(self):
        aura = self.spells[FIRST]
        self.assertEqual((aura["effect1"]["type"], aura["effect1"]["apply_aura"]), (EFFECT_APPLY_AURA, AURA_DUMMY))
        self.assertEqual(aura["duration_ms"], -1)
        self.assertTrue(aura["raw_overrides"]["AttributesEx"] & ATTR1_AURA_STAYS_AFTER_COMBAT)
        self.assertEqual(aura["raw_overrides"]["SpellVisualID_1"], visuals.HM_RED_AURA)
        self.assertEqual(visuals.HM_RED_AURA, 90554)

    def test_the_prayer_is_unharmable_and_the_pillar_a_look(self):
        prayer = self.spells[FIRST + 1]
        eff = prayer["effect1"]
        self.assertEqual((eff["type"], eff["apply_aura"]), (EFFECT_APPLY_AURA, AURA_SCHOOL_IMMUNITY))
        self.assertEqual(eff["misc_value"], 127)                                  # every school
        self.assertEqual(prayer["duration_ms"], -1)                               # the script ends it at 20 s
        self.assertEqual(prayer["dispel"], 0)
        self.assertEqual(prayer["raw_overrides"]["SpellVisualID_1"], visuals.HM_KNEEL)
        pillar = self.spells[FIRST + 2]
        self.assertEqual(pillar["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(pillar["raw_overrides"]["SpellVisualID_1"], visuals.HM_PRAYER_PILLAR)
        self.assertEqual(visuals.HM_PRAYER_PILLAR, 90563)                         # never SV 12479
        self.assertEqual(int(self._const("kPrayerMs")), 20000)
        # the AI zeroes damage while he prays and the bots ignore him then
        self.assertIn("damage = 0;", self.script)
        self.assertIn("d.ignores.emplace_back(NPC_HEROD, Condition::HasAura(SPELL_CTA_PRAYER));", self.script)

    def test_zeal_stacks_to_six(self):
        zeal = self.spells[FIRST + 3]
        dmg, haste = zeal["effect1"], zeal["effect2"]
        self.assertEqual((dmg["type"], dmg["apply_aura"]), (EFFECT_APPLY_AURA, AURA_MOD_DAMAGE_PERCENT_DONE))
        self.assertEqual(dmg["base_points"] + dmg["die_sides"], 5)
        self.assertEqual(dmg["misc_value"], 127)
        self.assertEqual((haste["type"], haste["apply_aura"]), (EFFECT_APPLY_AURA, AURA_MOD_MELEE_HASTE))
        self.assertEqual(haste["base_points"] + haste["die_sides"], 5)
        self.assertEqual(zeal["raw_overrides"]["CumulativeAura"], 6)
        self.assertEqual(zeal["duration_ms"], -1)
        self.assertEqual(zeal["dispel"], 0)
        self.assertEqual(int(self._const("kZealPct")), self._dt_int("ZEAL_PCT"))
        self.assertEqual(int(self._const("kZealMax")), self._dt_int("ZEAL_MAX"))
        self.assertEqual(self._dt_int("ZEAL_MAX"), 6)
        self.assertEqual(zeal["raw_overrides"]["SpellVisualID_1"], visuals.HB_ZEAL)

    def test_the_beacon(self):
        look = self.spells[FIRST + 6]
        self.assertTrue(look["raw_overrides"]["AttributesEx"] & ATTR1_IS_CHANNELED)    # the kit re-casts a channel
        self.assertEqual(look["raw_overrides"]["ChannelInterruptFlags"], 0)            # the end stalker moves
        self.assertEqual(look["raw_overrides"]["SpellVisualID_1"], visuals.HM_BEAM)
        self.assertEqual(visuals.HM_BEAM, 11500)
        hit = self.spells[FIRST + 7]
        self.assertEqual(hit["school"], SCHOOL_HOLY)
        self.assertEqual(hit["effect1"]["type"], EFFECT_SCHOOL_DAMAGE)                  # a resolve copy
        self.assertIn((FIRST + 7, "spell_boss_mechanics_resolve"), self.scripts)
        self.assertEqual(self._const("kBeamPct"), "SmHerod::kHitPct.heroic")           # 45%, heroic's hit
        self.assertIn("spec.spellId = SPELL_CTA_BEAM;", self.script)
        self.assertIn("spec.beamSpell = SPELL_CTA_BEAM_LOOK;", self.script)
        self.assertIn("spec.tankPct = kBeamPct;", self.script)                          # rule 16
        self.assertIn("spec.clip = &_pitArena;", self.script)
        self.assertEqual(self.spells[FIRST + 5]["raw_overrides"]["SpellVisualID_1"], visuals.HB_RAVAGER_GLOW)

    def test_the_hall(self):
        tick = self.spells[FIRST + 8]
        eff = tick["effect1"]
        self.assertEqual(tick["school"], SCHOOL_HOLY)
        self.assertEqual(eff["type"], EFFECT_SCHOOL_DAMAGE)
        self.assertEqual(eff["base_points"] + eff["die_sides"], 400)                   # 4% a tick in hundredths
        self.assertEqual(tick["raw_overrides"]["EffectMiscValueB_1"], 400)             # heroic: the same
        self.assertEqual(int(self._const("kHallTickMs")), self._dt_int("HALL_TICK_MS"))
        self.assertEqual(self._dt_int("HALL_HUNDREDTHS"), 400)
        self.assertIn((FIRST + 8, "spell_dungeon_refflat_damage"), self.scripts)
        self.assertTrue(tick["raw_overrides"]["AttributesEx3"] & ATTR3_IGNORE_CASTER_MODIFIERS)   # rule 2
        look = self.spells[FIRST + 9]
        self.assertEqual(look["raw_overrides"]["SpellVisualID_1"], visuals.HM_HALL)
        self.assertEqual(visuals.HM_HALL, visuals.SV_CONSECRATED_HALL)

    def test_the_looks_use_the_v_constants_and_none_is_wrong(self):
        for spell_id, spell in self.spells.items():
            self.assertNotIn(spell["raw_overrides"].get("SpellVisualID_1", 0), vfx_test.WRONG_SPELL_VISUALS,
                             spell_id)
        self.assertEqual(self.spells[FIRST + 4]["raw_overrides"]["SpellVisualID_1"], visuals.HB_RAVAGER_GLOW)
        # the items and displays the C++ and the SQL use are V's
        self.assertEqual(int(self._const("kItemCrusaderBlade")), visuals.ITEM_HEROD_BLADE)
        self.assertEqual(int(self._const("kItemTraineeMace")), visuals.ITEM_TRAINEE_MACE)

    # --- the creatures ------------------------------------------------------------------------------------------------

    def test_the_garrison_trainee(self):
        c = self.creatures[TRAINEE]
        self.assertEqual(c["name"], "Scarlet Garrison Trainee")
        self.assertEqual(c["ScriptName"], "npc_sm_garrison_trainee" if common.BIND_WAVE_2 else "")
        self.assertEqual(c["AIName"], "")
        self.assertEqual((c["minlevel"], c["maxlevel"], c["unit_class"], c["faction"]), (60, 60, 1, 67))
        self.assertAlmostEqual(c["HealthModifier"] * 3052, 5000, delta=5)
        self.assertEqual(c["DamageModifier"], 0.0)                                 # marches only
        self.assertEqual(c["CreatureImmunitiesId"], 0)                             # stops and roots are rewards
        self.assertEqual(c["unit_flags"], 0)
        self.assertEqual((c["lootid"], c["flags_extra"]), (0, 0x40))
        self.assertIn(c.get("difficulty_entry_1", 0), (0, 310478))                 # H's table, once it settles
        self.assertEqual(self._dt_int("GARRISON_TRAINEE_HEROIC_PLANNED"), 310478)
        self.assertEqual(sorted(m["CreatureDisplayID"] for m in self.models[TRAINEE]),
                         sorted((visuals.DISPLAY_SCARLET_TRAINEE, visuals.DISPLAY_SCARLET_TRAINEE_ALT)))
        self.assertEqual(visuals.DISPLAY_GARRISON_TRAINEE, visuals.DISPLAY_SCARLET_TRAINEE)
        self.assertIn("creature_template(300944, ", self.dt)        # H finds the kit adds by this literal pattern
        # the AI registers only once wave 2 binds (as the ScriptName)
        self.assertRegex(self.script, r"if \(kWave2Bound\)\n\s+RegisterDungeonReworkCreatureAI\("
                                      r"npc_sm_garrison_trainee, ScarletMonasteryRework::kInstanceScriptName\)")

    def test_the_planted_ravager(self):
        c = self.creatures[RAVAGER]
        self.assertEqual(c["name"], "Ravager")
        self.assertEqual(c["ScriptName"], "")
        self.assertTrue(c["unit_flags"] & 0x02000000)                                # not selectable
        self.assertTrue(c["unit_flags"] & 0x2)                                       # not attackable
        self.assertEqual(c["DamageModifier"], 0.0)
        self.assertNotIn("difficulty_entry_1", {k for k, v in c.items() if v})       # runs on its normal entry
        self.assertEqual([m["CreatureDisplayID"] for m in self.models[RAVAGER]], [11686])

    def test_ids_sit_in_the_reservation_and_match_the_header(self):
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery",
                                                      {"creature": [TRAINEE, RAVAGER], "gameobject": [RACK, PROP]}), [])
        self.assertRegex(self.header, r"NPC_SM_GARRISON_TRAINEE\s*=\s*300944,")
        self.assertRegex(self.header, r"NPC_SM_PLANTED_RAVAGER\s*=\s*300945,")
        self.assertRegex(self.header, r"GO_SM_WALL_RACK\s*=\s*301328,")
        self.assertRegex(self.header, r"GO_SM_PLANTED_AXE\s*=\s*301329,")

    # --- the SQL ------------------------------------------------------------------------------------------------------

    def test_the_five_lines(self):
        rows = re.findall(r"^\(3975, (\d+), (\d+), '((?:[^']|'')*)', (\d+), 0, 100, 0, 0, 0, 0, (\d+),", self.sql,
                          re.M)
        self.assertEqual([(int(g), t.replace("''", "'"), int(ty)) for g, i, t, ty, r in rows], list(LINES))
        self.assertTrue(all(int(i) == 0 for _, i, _, _, _ in rows))
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 3975 AND `GroupID` BETWEEN 5 AND 9;", self.sql)
        for group, name in ((5, "SAY_TAUNT_ANSWERED"), (6, "SAY_TAUNT_WORDS"), (7, "SAY_RISING"),
                            (8, "EMOTE_GARRISON")):
            self.assertRegex(self.herod_logic, rf"{name}\s*=\s*{group},")
        for call in ("fight.Say(SmHerod::SAY_TAUNT_ANSWERED, player)", "fight.Say(SmHerod::SAY_TAUNT_WORDS, player)",
                     "fight.Say(SmHerod::SAY_RISING)", "fight.Say(SmHerod::EMOTE_GARRISON)"):
            self.assertIn(call, self.script)
        # S0's text range for Herod covers them
        self.assertIn("{ NPC_HEROD, 0, 9, 5 },", self.header)

    def test_the_gameobject_templates(self):
        block = re.search(r"INSERT INTO `gameobject_template`.*?VALUES\n(.*?)\nON DUPLICATE KEY", self.sql, re.S)
        self.assertIsNotNone(block)
        tuples = re.findall(r"\((\d+, .*?)\)(?:,|$)", block.group(1).replace("\n", " "))
        self.assertEqual(len(tuples), 2)
        displays = {RACK: visuals.GODI_RAVAGER_RACK, PROP: visuals.GODI_PLANTED_RAVAGER}
        for text in tuples:
            fields = _split_values(text)
            self.assertEqual(len(fields), GO_COLUMN_COUNT)
            self.assertIn(fields[0], displays)
            self.assertEqual(fields[1], GENERIC)
            self.assertEqual(fields[2], displays[fields[0]])
            self.assertEqual(fields[-2], "")                                # no script
        self.assertEqual((visuals.GODI_RAVAGER_RACK, visuals.GODI_PLANTED_RAVAGER), (130, 8494))
        self.assertIn("(301328, 0, 16, 0, 0, 0, 0, 0, 0),", self.sql)      # not selectable
        self.assertIn("(301329, 0, 16, 0, 0, 0, 0, 0, 0);", self.sql)
        self.assertIn("SummonGameObject(GO_SM_PLANTED_AXE,", self.script)

    def test_the_rack_is_a_heroic_spawn_on_the_header_spot(self):
        spot = re.search(r"kRackSpot\{ ([-\d.]+)f, ([-\d.]+)f, ([-\d.]+)f \}", self.logic)
        self.assertIsNotNone(spot)
        rows = re.findall(r"^\((\d+), (3013\d\d), 189, 0, 0, (\d), 1, ([-\d.]+), ([-\d.]+), ([-\d.]+), ([-\d.]+), "
                          r"0, 0, ([-\d.]+), ([-\d.]+), ", self.sql, re.M)
        self.assertEqual(len(rows), 1)
        guid, entry, mask, x, y, z, o, r2, r3 = rows[0]
        self.assertEqual((int(guid), int(entry)), (RACK * 10, RACK))
        self.assertEqual(int(mask), 2)                                       # heroic only
        self.assertEqual((float(x), float(y), float(z)), tuple(float(v) for v in spot.groups()))
        self.assertAlmostEqual(float(o), math.pi / 2, places=3)              # kRackFacing
        self.assertAlmostEqual(float(r2), math.sin(float(o) / 2), places=4)
        self.assertAlmostEqual(float(r3), math.cos(float(o) / 2), places=4)

    def test_the_beams_plan_bots_in_the_whole_hall(self):
        # R-2-ARM m-5: the beams' bounds are the hall (the pit, the ledge, the spur), not the pit disc.
        self.assertIn("ref.Within(HallBounds());", self.script)
        self.assertNotIn("PitBounds()", self.script)

    def test_no_line_over_120_columns(self):
        for path in (SQL, DT_FILE, LOGIC, SCRIPT, Path(__file__)):
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                self.assertLessEqual(len(line), 120, f"{path.name}:{n}")


if __name__ == "__main__":
    unittest.main()
