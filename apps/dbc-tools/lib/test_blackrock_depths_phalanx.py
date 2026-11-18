"""
Blackrock Depths build WP-D19, Phalanx and the Rowdy Patron: source/npcs/blackrock_depths/phalanx.py against its C++
(modules/mod-dungeon-bosses src/BlackrockDepths/PhalanxLogic.h, npc_phalanx_rework.cpp) and its SQL rev
(data/sql/updates/pending_db_world/rev_phalanx_blackrock_depths.sql).

Wave 2: the boss's own columns and the patron's ScriptName sit behind BIND_WAVE_2 (_common.py), so this test checks the
declarations directly: the columns through the file's PHALANX_COLUMNS, the gate in both positions through a copy of the
package with the switch written True. Nothing here needs the switch on.

Checks:
  - the spells sit in his slice (211460-211489) and PhalanxLogic.h names the same ids;
  - he is bound once wave 2 is (SmartAI off, immunity 1972, INSTANCE_BIND), 160k at 5 players, DamageModifier 3.5, and
    declares nothing while the switch is off;
  - the Rowdy Patron: its entry, model, level, health, script and WP-H's heroic lock line;
  - Mighty Blow, Thunderclap and Fireball Volley (rule 15 copies on the kit's refflat script, the header's percents),
    the hold, the four resolve copies, Last Call's bar, Outrage, the looks on V-1's ids (never Smash's SV 3948);
  - the SQL rev: his four texts, the gossip option on his stock menu and its condition, no spawn, no SmartAI.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_phalanx.py
"""

from __future__ import annotations

import math
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import test_id_blocks as id_blocks  # noqa: E402
from lib.dsl import registry  # noqa: E402
from source.npcs.blackrock_depths import _common as common  # noqa: E402

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockDepths"
HEADER = MODULE_DIR / "PhalanxLogic.h"
REWORK = MODULE_DIR / "BlackrockDepthsRework.h"
SCRIPT = MODULE_DIR / "npc_phalanx_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_phalanx_blackrock_depths.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_depths"
VISUALS = PACKAGE / "_visuals.py"

SLICE = range(211460, 211490)
(MIGHTY_BLOW, THUNDERCLAP, VOLLEY, GRAB, THROW_LOOK, THROW_OUT, THROWN, SLAM_LOOK, LAST_CALL_CAST, LAST_CALL, OUTRAGE,
 TABLE_SMASH, TABLE_SPLINTERS) = range(211460, 211473)
NAMES = ("SPELL_PH_MIGHTY_BLOW", "SPELL_PH_THUNDERCLAP", "SPELL_PH_FIREBALL_VOLLEY", "SPELL_PH_GRAB",
         "SPELL_PH_THROW_LOOK", "SPELL_PH_THROW_OUT", "SPELL_PH_THROWN", "SPELL_PH_SLAM_LOOK",
         "SPELL_PH_LAST_CALL_CAST", "SPELL_PH_LAST_CALL", "SPELL_PH_OUTRAGE", "SPELL_PH_TABLE_SMASH",
         "SPELL_PH_TABLE_SPLINTERS")
PHALANX = 9502
PATRON = 300841
PATRON_HEROIC = 310415
WARRIOR_55_BASE = 2614
HEALTH_AT_5 = 160_000
STALKER_WAVE_2 = 300845
GOSSIP_MENU = 2283
DATA_PHALANX_ACTIVATED = 44

SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT, KNOCK_BACK = 2, 6, 3, 98
AURA_MOD_STUN, AURA_MOD_DECREASE_SPEED, AURA_MOD_DAMAGE_PERCENT_DONE, AURA_MOD_MELEE_HASTE = 12, 33, 79, 138
SCHOOL_PHYSICAL, SCHOOL_FIRE, SCHOOL_NATURE = 1, 4, 8
TARGET_UNIT_CASTER, TARGET_UNIT_TARGET_ENEMY, TARGET_UNIT_SRC_AREA_ENEMY, TARGET_SRC_CASTER, TARGET_DEST_DEST = (
    1, 6, 15, 22, 87)
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT = "spell_dungeon_refflat_damage"
IMMUNITY_BOSS_STUN = 1972
INSTANCE_BIND = 0x1
# The stock looks (read from the client Spell.dbc 2026-11-17): Thunderclap 15588, Fireball Volley 15285, Grabbed 55424,
# Throw 55425, Ground Slam 33525, Ring Bessy's Bell 35209, Bellowing Roar 18431; the shipped wood chips.
SV_THUNDERCLAP, SV_VOLLEY, SV_GRAB, SV_THROW, SV_SLAM, SV_BELL, SV_ROAR, SV_SPLINTERS = (
    145, 2437, 12139, 12140, 8083, 215, 4939, 90344)
SV_SMASH_WRONG = 3948       # Smash 54458: blood and a stun swirl (VISUALS report: WRONG)


def _load(package: Path = PACKAGE):
    t = id_blocks
    return registry.load_class_package(
        package, ids_cfg=t.IDS, trainer_index=t._AnyTrainer(), existing_group_ids=t._AnySet(),
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


def _raw(spell: dict, column: str) -> float:
    return (spell.get("raw_overrides") or {}).get(column, 0) or 0


def _header() -> str:
    return HEADER.read_text(encoding="utf-8")


def _header_value(name: str) -> float:
    match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f?;", _header())
    assert match, name
    return float(match.group(1))


def _header_nh(name: str) -> tuple[float, float]:
    match = re.search(rf"\b{name}\{{\s*(-?[\d.]+)f?,\s*(-?[\d.]+)f?\s*\}};", _header())
    assert match, name
    return float(match.group(1)), float(match.group(2))


def _visual(name: str) -> int:
    text = VISUALS.read_text(encoding="utf-8")
    match = re.search(rf"^{name}\s*=\s*(\w+)", text, re.MULTILINE)
    assert match, name
    value = match.group(1)
    return int(value) if value.isdigit() else _visual(value)


def _bound_package() -> tempfile.TemporaryDirectory:
    """A copy of this boss's file with the wave switch written True (the shared _common.py and _visuals.py beside
    it)."""
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name) / "blackrock_depths"
    root.mkdir()
    for name in ("_visuals.py", "phalanx.py"):
        shutil.copy(PACKAGE / name, root / name)
    common = (PACKAGE / "_common.py").read_text(encoding="utf-8")
    common = re.sub(r"^BIND_WAVE_2 = (True|False)$", "BIND_WAVE_2 = True", common, flags=re.M)
    (root / "_common.py").write_text(common, encoding="utf-8")
    return tmp


class PhalanxDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) == PHALANX}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == PATRON}
        cls.models = {int(m["CreatureID"]): m for m in reg.creature_template_models if int(m["CreatureID"]) == PATRON}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.declaration = (PACKAGE / "phalanx.py").read_text(encoding="utf-8")

    # --- ids ---------------------------------------------------------------------------------------------------------

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(MIGHTY_BLOW, TABLE_SPLINTERS + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"spell": mine}), [])
        first = re.search(r"kSpellsPhalanx\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(first)
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        for offset, name in enumerate(NAMES):
            self.assertRegex(_header(), rf"{name}\s*=\s*kSpellSlice\.first \+ {offset},", name)
        self.assertRegex(_header(), r"kLastSpell = SPELL_PH_TABLE_SPLINTERS;")
        # rule 15: no stock id declared (the copies replace them)
        for stock in (14099, 15588, 15285):
            self.assertNotIn(stock, self.spells)

    def test_the_patron_id_is_the_headers(self):
        text = REWORK.read_text(encoding="utf-8")
        self.assertRegex(text, rf"\bNPC_BRD_ROWDY_PATRON\s*=\s*{PATRON},")
        self.assertRegex(text, rf"\bNPC_BRD_STALKER_WAVE_2\s*=\s*{STALKER_WAVE_2},")
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"creature": [PATRON]}), [])

    # --- the boss -----------------------------------------------------------------------------------------------------

    def test_his_columns(self):
        self.assertRegex(self.declaration,
                         r"PHALANX_COLUMNS = boss_columns\('npc_phalanx_rework', 61\.209, damage_modifier=3\.5\)")
        self.assertRegex(self.declaration, r"creature_template_columns\(9502, \*\*PHALANX_COLUMNS\)")
        c = common.boss_columns("npc_phalanx_rework", 61.209, damage_modifier=3.5)
        self.assertEqual(c["ScriptName"], "npc_phalanx_rework")
        self.assertEqual(c["AIName"], "")
        self.assertEqual(c["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)      # stock -248 let stuns land
        self.assertEqual(c["flags_extra"], INSTANCE_BIND)
        self.assertEqual(c["DamageModifier"], 3.5)
        self.assertAlmostEqual(c["HealthModifier"] * WARRIOR_55_BASE, HEALTH_AT_5, delta=10)
        # the dormant state and the gossip start need his stock faction, npcflag and menu: none is overridden
        for column in ("faction", "npcflag", "gossip_menu_id"):
            self.assertNotIn(column, c)

    def test_he_is_bound_only_with_the_gate_on(self):
        with _bound_package() as tmp:
            bound = {int(e["entry"]): e for e in _load(Path(tmp) / "blackrock_depths").creature_template_edits
                     if int(e["entry"]) == PHALANX}
        self.assertEqual(bound[PHALANX]["ScriptName"], "npc_phalanx_rework")
        self.assertEqual(bound[PHALANX]["AIName"], "")
        if not common.BIND_WAVE_2:
            self.assertNotIn(PHALANX, self.edits)
        self.assertRegex(self.cpp, r"RegisterDungeonReworkCreatureAI\(npc_phalanx_rework,")
        self.assertRegex(self.cpp, r"struct npc_phalanx_rework : public BossAI")
        self.assertRegex(self.cpp, r'BrdTest::RegisterBoss\("phalanx",')

    # --- the Rowdy Patron ---------------------------------------------------------------------------------------------

    def test_the_patron(self):
        row = self.creatures[PATRON]
        self.assertEqual(row["name"], "Rowdy Patron")
        self.assertEqual((int(row["minlevel"]), int(row["maxlevel"])), (55, 55))
        self.assertEqual(int(row["unit_class"]), 1)
        self.assertEqual(int(row["faction"]), 54)
        self.assertEqual(int(row["lootid"]), 0)
        self.assertEqual(row["AIName"], "")
        # 8,000 at 5 players (normal row; it spawns on heroic only, where WP-H's heroic copy holds 8k too)
        self.assertEqual(math.ceil(WARRIOR_55_BASE * float(row["HealthModifier"])), 8000)
        self.assertEqual(_header_nh("kPatronHealth"), (8000.0, 8000.0))
        # WP-H's heroic lock line (STAGE-H-REPORT s3)
        self.assertEqual(int(row["difficulty_entry_1"]), PATRON_HEROIC)
        # the Hammered Patron look at 1.2 (V-1)
        self.assertEqual(int(self.models[PATRON]["CreatureDisplayID"]), _visual("DISPLAY_ROWDY_PATRON"))
        self.assertEqual(_visual("DISPLAY_ROWDY_PATRON"), 8681)
        self.assertAlmostEqual(float(self.models[PATRON]["DisplayScale"]), 1.2)

    def test_the_patrons_script_waits_for_the_gate(self):
        with _bound_package() as tmp:
            bound = {int(e["entry"]): e for e in _load(Path(tmp) / "blackrock_depths").creature_templates
                     if int(e["entry"]) == PATRON}
        self.assertEqual(bound[PATRON]["ScriptName"], "npc_brd_rowdy_patron")
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_brd_rowdy_patron,", self.cpp)
        if not common.BIND_WAVE_2:
            self.assertEqual(self.creatures[PATRON]["ScriptName"], "")

    # --- PH1-PH3 the kept stock spells --------------------------------------------------------------------------------

    def _assert_refflat(self, spell_id: int, header_name: str, effect: dict):
        spell = self.spells[spell_id]
        normal, heroic = _header_nh(header_name)
        self.assertEqual(effect["type"], SCHOOL_DAMAGE)
        self.assertEqual(effect["base_points"] + effect["die_sides"], round(normal * 100))
        self.assertEqual(_raw(spell, "EffectMiscValueB_1"), round(heroic * 100))
        self.assertIn((spell_id, REFFLAT), self.scripts)
        self.assertTrue(int(_raw(spell, "AttributesEx3")) & ATTR3_IGNORE_CASTER_MODIFIERS)

    def test_mighty_blow_is_a_refflat_copy_with_the_stock_knockback(self):
        spell = self.spells[MIGHTY_BLOW]
        hit, knock = spell["effect1"], spell["effect2"]
        self._assert_refflat(MIGHTY_BLOW, "kMightyBlowPct", hit)
        self.assertEqual(spell["school"], SCHOOL_PHYSICAL)
        self.assertEqual(hit["implicit_target_a"], TARGET_UNIT_TARGET_ENEMY)
        # the stock 14099 knockback: base 74, 51 sides, MiscValue 100
        self.assertEqual((knock["type"], knock["base_points"], knock["die_sides"], knock["misc_value"]),
                         (KNOCK_BACK, 74, 51, 100))
        self.assertEqual(_header_nh("kMightyBlowPct"), (25.0, 30.0))

    def test_thunderclap_is_a_refflat_copy_with_the_magic_slow(self):
        spell = self.spells[THUNDERCLAP]
        hit, slow, haste = spell["effect1"], spell["effect2"], spell["effect3"]
        self._assert_refflat(THUNDERCLAP, "kThunderclapPct", hit)
        self.assertEqual(spell["school"], SCHOOL_NATURE)
        self.assertEqual(spell["dispel"], 1)                    # Magic: the dispel list
        self.assertEqual(spell["duration_ms"], int(_header_value("kThunderclapMs")))
        for effect in (hit, slow, haste):
            self.assertEqual((effect["implicit_target_a"], effect["implicit_target_b"]),
                             (TARGET_SRC_CASTER, TARGET_UNIT_SRC_AREA_ENEMY))
            self.assertEqual(effect["radius_yards"], _header_value("kThunderclapRadiusYd"))
        self.assertEqual((slow["apply_aura"], slow["base_points"] + slow["die_sides"]),
                         (AURA_MOD_DECREASE_SPEED, int(_header_value("kThunderclapSlowPct"))))
        self.assertEqual((haste["apply_aura"], haste["base_points"] + haste["die_sides"]),
                         (AURA_MOD_MELEE_HASTE, int(_header_value("kThunderclapAttackSpeedPct"))))
        self.assertEqual(_raw(spell, "SpellVisualID_1"), SV_THUNDERCLAP)
        self.assertEqual(_visual("PH_THUNDERCLAP"), SV_THUNDERCLAP)
        # the bots' dispel list names the copy
        self.assertIn("d.dispels.emplace_back(SPELL_PH_THUNDERCLAP,", self.cpp)

    def test_fireball_volley_is_a_refflat_copy(self):
        spell = self.spells[VOLLEY]
        hit = spell["effect1"]
        self._assert_refflat(VOLLEY, "kVolleyPct", hit)
        self.assertEqual(spell["school"], SCHOOL_FIRE)
        self.assertEqual(hit["radius_yards"], _header_value("kVolleyRadiusYd"))
        self.assertEqual(_raw(spell, "SpellVisualID_1"), SV_VOLLEY)
        self.assertEqual(_raw(spell, "Speed"), 24.0)

    # --- PH4 Throw Out ------------------------------------------------------------------------------------------------

    def test_the_hold(self):
        spell = self.spells[GRAB]
        effect = spell["effect1"]
        self.assertEqual((effect["type"], effect["apply_aura"]), (APPLY_AURA, AURA_MOD_STUN))
        self.assertEqual(effect["implicit_target_a"], TARGET_UNIT_TARGET_ENEMY)
        self.assertEqual(spell["duration_ms"], int(_header_value("kGrabAuraMs")))
        self.assertGreater(spell["duration_ms"], int(_header_value("kGrabMs")))
        self.assertEqual((spell["dispel"], spell["mechanic"]), (0, 0))      # nothing breaks the 1 s hold
        self.assertEqual(_raw(spell, "SpellVisualID_1"), SV_GRAB)
        self.assertEqual(_visual("PH_THROW_OUT_GRAB"), SV_GRAB)
        self.assertTrue(int(_raw(spell, "AuraInterruptFlags")) & 0x00080000)       # rule 3: CHANGE_MAP

    def test_the_looks(self):
        throw = self.spells[THROW_LOOK]
        self.assertEqual((throw["effect1"]["type"], throw["effect1"]["implicit_target_a"]),
                         (DUMMY_EFFECT, TARGET_UNIT_TARGET_ENEMY))
        self.assertEqual(_raw(throw, "SpellVisualID_1"), SV_THROW)
        slam = self.spells[SLAM_LOOK]
        self.assertEqual((slam["effect1"]["type"], slam["effect1"]["implicit_target_a"]),
                         (DUMMY_EFFECT, TARGET_DEST_DEST))
        self.assertEqual(_raw(slam, "Targets"), 0x40)
        self.assertEqual(_raw(slam, "SpellVisualID_1"), SV_SLAM)
        splinters = self.spells[TABLE_SPLINTERS]
        self.assertEqual((splinters["effect1"]["type"], splinters["effect1"]["implicit_target_a"]),
                         (DUMMY_EFFECT, TARGET_UNIT_CASTER))
        self.assertEqual(_raw(splinters, "SpellVisualID_1"), SV_SPLINTERS)
        self.assertEqual(_visual("PH_TABLE_SPLINTERS"), SV_SPLINTERS)
        # the chips at the table: a stalker casts them on itself
        self.assertIn("stalker->CastSpell(stalker, SPELL_PH_TABLE_SPLINTERS, true)", self.cpp)
        self.assertIn("NPC_BRD_STALKER_WAVE_2", self.cpp)

    def test_no_wrong_listed_look_is_wired(self):
        for spell in self.spells.values():
            self.assertNotEqual(_raw(spell, "SpellVisualID_1"), SV_SMASH_WRONG, spell["id"])

    def test_the_hits_are_physical_resolve_copies(self):
        for spell_id in (THROW_OUT, THROWN, LAST_CALL, TABLE_SMASH):
            spell = self.spells[spell_id]
            self.assertEqual(spell["school"], SCHOOL_PHYSICAL, spell_id)
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts, spell_id)
            self.assertTrue(int(_raw(spell, "AttributesEx3")) & ATTR3_IGNORE_CASTER_MODIFIERS, spell_id)
        # the script registers them on the header's numbers
        for name in ("kLandingPct", "kThrownPct", "kLastCallPct"):
            self.assertIn(name, self.cpp)
        self.assertEqual(_header_nh("kLandingPct"), (30.0, 45.0))
        self.assertEqual(_header_nh("kThrownPct"), (15.0, 25.0))
        self.assertEqual(_header_nh("kLastCallPct"), (25.0, 40.0))
        self.assertEqual(_header_value("kSmashPct"), 25.0)
        self.assertIn("spec.weakened = false;      // not a failure (S4)", self.cpp)

    # --- PH5 Last Call, PH6 Outrage -----------------------------------------------------------------------------------

    def test_last_calls_bar(self):
        spell = self.spells[LAST_CALL_CAST]
        self.assertEqual(spell["cast_time_ms"], int(_header_value("kLastCallCastMs")))
        self.assertEqual(spell["cast_time_ms"], 3000)
        self.assertEqual((_raw(spell, "InterruptFlags"), _raw(spell, "PreventionType")), (0, 0))
        self.assertEqual(_raw(spell, "SpellVisualID_1"), SV_BELL)
        self.assertEqual(_visual("PH_LAST_CALL"), SV_BELL)
        self.assertIn("DungeonKit::CastBar(me, SPELL_PH_LAST_CALL_CAST)", self.cpp)

    def test_outrage(self):
        spell = self.spells[OUTRAGE]
        effect = spell["effect1"]
        self.assertEqual((effect["type"], effect["apply_aura"]), (APPLY_AURA, AURA_MOD_DAMAGE_PERCENT_DONE))
        self.assertEqual((effect["base_points"], effect["die_sides"]),
                         (int(_header_value("kOutragePctPerStack")), 0))
        self.assertEqual(effect["implicit_target_a"], TARGET_UNIT_CASTER)
        self.assertEqual(_raw(spell, "CumulativeAura"), int(_header_value("kOutrageCap")))
        self.assertEqual(spell["duration_ms"], -1)
        self.assertEqual(_raw(spell, "SpellVisualID_1"), SV_ROAR)
        self.assertEqual(_visual("PH_OUTRAGE"), SV_ROAR)

    # --- the SQL ------------------------------------------------------------------------------------------------------

    def test_the_four_texts(self):
        rows = re.findall(r"^\(9502, (\d+), (\d+), '((?:[^']|'')*)', (\d+), 0, 100, 0, 0, 0, 0, (\d+),", self.sql, re.M)
        self.assertEqual([(int(g), int(i), int(t)) for g, i, _, t, _ in rows],
                         [(1, 0, 41), (2, 0, 14), (3, 0, 14), (4, 0, 14)])
        texts = [t.replace("''", "'") for _, _, t, _, _ in rows]
        self.assertEqual(texts, ["%s grabs $n by the collar!", "Last call! Everybody out!", "PROPERTY DAMAGE!",
                                 "Closing... time..."])
        # group 0 (the stock wake-up yell) is untouched
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 9502 AND `GroupID` BETWEEN 1 AND 4;", self.sql)
        for name, group in (("SAY_PH_DOOR", 0), ("EMOTE_PH_GRAB", 1), ("YELL_PH_LAST_CALL", 2),
                            ("YELL_PH_PROPERTY_DAMAGE", 3), ("YELL_PH_DEATH", 4)):
            self.assertRegex(_header(), rf"{name}\s*=\s*{group},", name)
        self.assertRegex(re.sub(r"\s+", " ", REWORK.read_text(encoding="utf-8")), r"\{ NPC_PHALANX, 0, 4, 1 \}")
        for name in ("SAY_PH_DOOR", "YELL_PH_LAST_CALL", "YELL_PH_PROPERTY_DAMAGE", "YELL_PH_DEATH"):
            self.assertIn(f"Talk({name})", self.cpp)
        self.assertIn("Talk(EMOTE_PH_GRAB, target)", self.cpp)

    def test_the_gossip_start(self):
        # rule 9: the option hangs on his stock menu 2283 (gossip_menu_id on the template: not overridden above), the
        # condition reads the instance's saved flag, the C++ answers that menu and option
        self.assertRegex(self.sql, r"\(2283, 0, 0, '[^\n]+', 0, 1, 1, 0, 0, 0, 0, '', 0, 0\);")
        self.assertIn("DELETE FROM `gossip_menu_option` WHERE `MenuID` = 2283 AND `OptionID` = 0;", self.sql)
        self.assertRegex(self.sql,
                         rf"\(15, {GOSSIP_MENU}, 0, 0, 0, 13, 0, {DATA_PHALANX_ACTIVATED}, 0, 0, 0, 0, 0, '',")
        self.assertRegex(_header(), rf"kGossipMenu = {GOSSIP_MENU};")
        self.assertRegex(_header(), r"kGossipOption = 0;")
        self.assertRegex(REWORK.read_text(encoding="utf-8"), rf"DATA_PHALANX_ACTIVATED\s*=\s*{DATA_PHALANX_ACTIVATED},")
        self.assertIn("void sGossipSelect(Player* player, uint32 menuId, uint32 gossipListId) override", self.cpp)
        self.assertIn("StartActivation(PhalanxRequest::Gossip)", self.cpp)

    def test_the_rev_adds_no_spawn_and_no_smartai(self):
        # rule 14: a rev that inserted spawns or SmartAI rows would have to set the heroic spawn mask / event flags
        self.assertNotIn("INSERT INTO `creature` ", self.sql)
        self.assertNotIn("INSERT INTO `smart_scripts`", self.sql)
        self.assertNotIn("DELETE FROM `smart_scripts`", self.sql)


if __name__ == "__main__":
    unittest.main()
