"""
Scholomance build WP-S12, Ras Frostwhisper's hard mode "the Torn Keepsake": source/npcs/scholomance/ras_hard_mode.py
and WP-S12's SQL rev against its C++ (modules/mod-dungeon-bosses src/Scholomance/RasHardModeLogic.h,
ras_hard_mode.cpp).

Checks:
  - the spells sit in S12's slice (206190-206204) and RasHardModeLogic.h names the same ids;
  - the Ice Tomb 300535 is a 12k, attackable, script-bound unit in the `scholomance` creature reservation, heroic only
    with no heroic template (the wave C mint rule) and the visual pick;
  - Mortal Decay is a stacking, undispellable DoT bound to its AuraScript; the Siphon's heal and backfire carry their
    amounts in base point 0 and ignore caster modifiers; the bars and the channel cannot be interrupted;
  - the SQL rev declares the four keepsake gameobjects with the registered scripts and spawns them on heroic only at
    the user's spots (ScholomanceRework.h), with Ras's text group 3.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scholomance_keepsake.py
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
from lib import test_scholomance_ras as ras_test  # noqa: E402

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Scholomance"
HEADER = MODULE_DIR / "RasHardModeLogic.h"
KIT_HEADER = MODULE_DIR / "ScholomanceRework.h"
SCRIPT = MODULE_DIR / "ras_hard_mode.cpp"
SQL_DIR = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world"
HEROIC = TOOL_ROOT / "source" / "world" / "dungeons" / "scholomance.py"

SLICE = range(206190, 206205)
(CLINGING, SIPHON_CAST, SIPHON_CHANNEL, SIPHONED, SIPHON_HEAL, BACKFIRE, DECAY, THAWING) = range(206190, 206198)
TOMB = 300535
GOS = {301150: "go_sc_torn_page", 301151: "go_sc_keepsake_book", 301152: "go_sc_keepsake_book",
       301154: "go_sc_alchemy_table"}

SCHOOL_DAMAGE, APPLY_AURA, HEAL = 2, 6, 10
AURA_DUMMY, AURA_PERIODIC_DAMAGE = 4, 3
ATTR1_IS_SELF_CHANNELED = 0x00000040
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
ATTR3_ALWAYS_HIT = 0x00040000
ATTR4_IGNORE_RESISTANCES = 0x00000001
CREATURE_FLAG_EXTRA_NO_XP = 0x40
AURA_INTERRUPT_FLAG_CHANGE_MAP = 0x00080000
WARRIOR_BASE_60 = 3052


def _raw(spell: dict, column: str) -> int:
    return ras_test._raw(spell, column)


def _header_int(name: str) -> int:
    match = re.search(rf"{name}\s*=\s*(-?\d+)", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return int(match.group(1))


def _rev() -> str:
    for path in sorted(SQL_DIR.glob("rev_*.sql")):
        text = path.read_text(encoding="utf-8")
        if "WP-S12" in text and "gameobject_template" in text:
            return text
    raise AssertionError("WP-S12's SQL rev is missing")


def _kit_points() -> dict[str, tuple[float, float, float, float]]:
    text = KIT_HEADER.read_text(encoding="utf-8")
    floats = r"\{\s*(-?[\d.]+)f,\s*(-?[\d.]+)f,\s*(-?[\d.]+)f,\s*(-?[\d.]+)f\s*\}"
    pages = re.search(r"kKeepsakePages\{\s*\{(.*?)\}\s*\};", text, re.S)
    assert pages
    out = {f"page{i + 1}": tuple(float(v) for v in m) for i, m in enumerate(re.findall(floats, pages.group(1)))}
    for name in ("kKeepsakeBook", "kHardModeTable"):
        m = re.search(rf"{name}{floats}", text)
        assert m, name
        out[name] = tuple(float(v) for v in m.groups())
    return out


class KeepsakeDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = ras_test._load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == TOMB}
        cls.models = {int(e["CreatureID"]): e for e in reg.creature_template_models if int(e["CreatureID"]) == TOMB}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.sql = _rev()

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(CLINGING, THAWING + 1)))
        self.assertEqual(id_blocks.out_of_reservation("scholomance", {"spell": mine}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_RK_\w+\s*=\s*(\d+)", HEADER.read_text(encoding="utf-8"))}
        self.assertEqual(header_ids, set(mine))

    def test_the_ice_tomb(self):
        self.assertEqual(sorted(self.creatures), [TOMB])
        self.assertEqual(id_blocks.out_of_reservation("scholomance", {"creature": [TOMB]}), [])
        tomb = self.creatures[TOMB]
        self.assertEqual(tomb["ScriptName"], "npc_sc_ice_tomb")
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_sc_ice_tomb,", self.cpp)
        self.assertEqual(math.ceil(WARRIOR_BASE_60 * tomb["HealthModifier"]), _header_int("kTombHealth"))
        self.assertEqual((tomb["minlevel"], tomb["maxlevel"], tomb["unit_class"]), (60, 60, 1))
        self.assertEqual(tomb["unit_flags"], 0)             # selectable and attackable
        self.assertEqual(tomb["faction"], 233)              # hostile to players
        self.assertEqual(tomb["RegenHealth"], 0)
        self.assertEqual(tomb["DamageModifier"], 0.0)
        self.assertEqual(tomb["lootid"], 0)
        self.assertTrue(tomb["flags_extra"] & CREATURE_FLAG_EXTRA_NO_XP)
        # Heroic only, summoned at this entry: no heroic template (wave C mint rule).
        self.assertEqual(tomb.get("difficulty_entry_1", 0), 0)
        self.assertNotRegex(HEROIC.read_text(encoding="utf-8"), r"\n\s*300535\s*:")
        self.assertEqual(self.models[TOMB]["CreatureDisplayID"], 30890)
        self.assertAlmostEqual(self.models[TOMB]["DisplayScale"], 0.35)

    def test_the_bars_and_the_channel_cannot_be_interrupted(self):
        for spell_id, ms in ((CLINGING, "kTransitionMs"), (SIPHON_CAST, "kSiphonCastMs"), (THAWING, "kTombCrackMs")):
            self.assertEqual(self.spells[spell_id]["cast_time_ms"], _header_int(ms), spell_id)
            self.assertEqual(_raw(self.spells[spell_id], "InterruptFlags"), 0, spell_id)
        channel = self.spells[SIPHON_CHANNEL]
        self.assertEqual(channel["duration_ms"], _header_int("kSiphonChannelMs"))
        self.assertTrue(_raw(channel, "AttributesEx") & ATTR1_IS_SELF_CHANNELED)
        for column in ("InterruptFlags", "ChannelInterruptFlags", "PreventionType"):
            self.assertEqual(_raw(channel, column), 0, column)

    def test_the_siphon_amounts_come_from_the_script(self):
        heal = self.spells[SIPHON_HEAL]
        self.assertEqual(heal["effect1"]["type"], HEAL)
        backfire = self.spells[BACKFIRE]
        self.assertEqual(backfire["effect1"]["type"], SCHOOL_DAMAGE)
        for spell in (heal, backfire):
            self.assertEqual(spell["effect1"]["base_points"], 0)
            self.assertTrue(spell["effect1"].get("_potency_excluded"))
            self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertTrue(_raw(backfire, "AttributesEx3") & ATTR3_ALWAYS_HIT)
        self.assertTrue(_raw(backfire, "AttributesEx4") & ATTR4_IGNORE_RESISTANCES)
        self.assertIn("SPELL_RK_SIPHON_HEAL, SPELLVALUE_BASE_POINT0", self.cpp)
        self.assertIn("SPELL_RK_SIPHON_BACKFIRE, SPELLVALUE_BASE_POINT0", self.cpp)
        # F-C3 N-3: the backfire's hit is set to base point 0 past Ras's damage-taken modifiers.
        self.assertIn((BACKFIRE, "spell_sc_ras_siphon_backfire"), self.scripts)
        self.assertIn("RegisterSpellScript(spell_sc_ras_siphon_backfire)", self.cpp)
        self.assertEqual(self.spells[SIPHONED]["effect1"]["apply_aura"], AURA_DUMMY)

    def test_mortal_decay(self):
        decay = self.spells[DECAY]
        self.assertEqual(decay["effect1"]["apply_aura"], AURA_PERIODIC_DAMAGE)
        self.assertEqual(decay["effect1"]["amplitude"], 1000)
        self.assertEqual(decay["dispel"], 0)
        # F-C3 S-1: finite (refreshed by each 10 s step) and dropped on a logout or a map change.
        self.assertEqual(decay["duration_ms"], _header_int("kDecayDurationMs"))
        self.assertGreater(decay["duration_ms"], _header_int("kDecayEveryMs"))
        self.assertEqual(_raw(decay, "CumulativeAura"), _header_int("kDecayMaxStacks"))
        self.assertTrue(_raw(decay, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertIn((DECAY, "spell_sc_ras_mortal_decay"), self.scripts)
        self.assertIn("RegisterSpellScript(spell_sc_ras_mortal_decay)", self.cpp)
        self.assertEqual({name for _, name in self.scripts},
                         {"spell_sc_ras_mortal_decay", "spell_sc_ras_siphon_backfire"})

    def test_player_auras_never_leave_the_map(self):
        # R-C KEEPSAKE S-1: Mortal Decay and the drain are dropped before the logout save, after the login load and
        # on a map change, so none outlives the fight on the character.
        for spell_id in (DECAY, SIPHONED):
            self.assertTrue(_raw(self.spells[spell_id], "AuraInterruptFlags") & AURA_INTERRUPT_FLAG_CHANGE_MAP,
                            spell_id)

    def test_looks_are_the_visual_picks(self):
        for spell_id in (SIPHON_CHANNEL, SIPHONED, BACKFIRE):
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), 7607, spell_id)
        self.assertEqual(_raw(self.spells[DECAY], "SpellVisualID_1"), 11624)

    def test_the_gameobjects_and_their_scripts(self):
        for entry, script in GOS.items():
            self.assertRegex(self.sql, rf"\({entry}, 10, \d+, '[^\n]*'{script}', 0\)", entry)
            self.assertIn(f"RegisterDungeonReworkGameObjectAI({script},", self.cpp)
        self.assertNotIn("301153", self.sql)                # the honors paper is S13's

    def test_the_spawns_are_heroic_only_at_the_users_spots(self):
        rows = re.findall(r"\((\d+), (3011\d\d), 289, 0, 0, (\d+), 1, (-?[\d.]+), (-?[\d.]+), (-?[\d.]+), "
                          r"(-?[\d.]+), 0, 0, (-?[\d.]+), (-?[\d.]+),", self.sql)
        self.assertEqual(len(rows), 6)
        spots = _kit_points()
        want = {
            "3011500": (301150, spots["page1"]), "3011501": (301150, spots["page2"]),
            "3011502": (301150, spots["page3"]), "3011510": (301151, spots["kKeepsakeBook"]),
            "3011520": (301152, spots["kKeepsakeBook"]), "3011540": (301154, spots["kHardModeTable"]),
        }
        for guid, entry, mask, x, y, z, o, r2, r3 in rows:
            self.assertIn(guid, want)
            want_entry, point = want.pop(guid)
            self.assertEqual(int(entry), want_entry, guid)
            self.assertEqual(int(mask), 2, guid)            # heroic only
            for got, exp in zip((x, y, z, o), point):
                self.assertAlmostEqual(float(got), exp, places=4, msg=guid)
            self.assertAlmostEqual(float(r2), math.sin(point[3] / 2), places=5, msg=guid)
            self.assertAlmostEqual(float(r3), math.cos(point[3] / 2), places=5, msg=guid)
        self.assertEqual(want, {})

    def test_the_human_form_is_the_visual_pick(self):
        from source.npcs.scholomance import _visuals

        self.assertEqual(_header_int("kHumanDisplay"), _visuals.DISPLAY_RAS_HUMAN)

    def test_the_start_emote(self):
        self.assertEqual(_header_int("EMOTE_RAS_KEEPSAKE_LIT"), 3)
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 10508 AND `GroupID` = 3;", self.sql)
        self.assertRegex(self.sql, r"\(10508, 3, 0, '%s [^']+', 41, 0, 100, 0, 0, 0, 0, 3, ")


if __name__ == "__main__":
    unittest.main()
