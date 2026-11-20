"""
Blackrock Depths build WP-D6, the Ring of Law's Encore: source/npcs/blackrock_depths/ring_encore.py against its C++
(modules/mod-dungeon-bosses src/BlackrockDepths/RingEncoreLogic.h, ring_encore_hard_mode.cpp) and its SQL rev.

Checks:
  - the spells sit in the Encore's slice (210960-210999 of 210960-211019) and RingEncoreLogic.h names the same ids;
  - the five members bound to their AIs (Theldren stun immune with INSTANCE_BIND, the others no immunity), the totems'
    rows (their AI, the team's faction, no loot, the heroic lock lines of STAGE-H-REPORT s3, V-1's displays);
  - every registry hit is a resolve copy and the C++ names its tag; the kickable casts are kickable and the bars are
    not; the script-valued hits ignore caster modifiers; the dispel types (Earth Shield, Ice Barrier, the root, the
    freeze: Magic; Vicious Wound: none); Earth Shield's 6 charges; the header's numbers on the auras;
  - every look is one of V-1's ids;
  - the rev: the five members' SmartAI dropped, Theldren's death line, the banner 301280 a goober with its script and
    the stock banner's display.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_ring_encore.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockDepths"
HEADER = MODULE_DIR / "RingEncoreLogic.h"
REWORK = MODULE_DIR / "BlackrockDepthsRework.h"
CPP = MODULE_DIR / "ring_encore_hard_mode.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_ring_encore_blackrock_depths.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_depths"
VISUALS = PACKAGE / "_visuals.py"

SLICE = range(210960, 211020)
FIRST, LAST = 210960, 210999
MEMBERS = {
    16059: "npc_brd_encore_theldren",
    16053: "npc_brd_encore_korv",
    16049: "npc_brd_encore_lefty",
    16058: "npc_brd_encore_volida",
    16052: "npc_brd_encore_malgen",
}
# totem -> (display constant in _visuals.py, heroic lock line [H s3])
TOTEMS = {
    300789: ("DISPLAY_KORV_TOTEM_HEALING", 310400),
    300790: ("DISPLAY_KORV_TOTEM_SEARING", 310401),
    300791: ("DISPLAY_KORV_TOTEM_EARTHBIND", 310402),
}

SCHOOL_DAMAGE, APPLY_AURA, HEAL, DUMMY = 2, 6, 10, 3
AURA_DUMMY, AURA_MOD_FEAR, AURA_MOD_STUN, AURA_MOD_ROOT = 4, 7, 12, 26
AURA_MOD_DECREASE_SPEED, AURA_MOD_DODGE, AURA_SCHOOL_ABSORB = 33, 49, 69
AURA_MOD_HEALING_PCT, AURA_MOD_MELEE_HASTE = 118, 138
SCHOOL_PHYSICAL, SCHOOL_FIRE, SCHOOL_NATURE, SCHOOL_FROST = 1, 4, 8, 16
DISPEL_NONE, DISPEL_MAGIC = 0, 1
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
RESOLVE = "spell_boss_mechanics_resolve"


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


def _header() -> str:
    return HEADER.read_text(encoding="utf-8")


def _header_value(name: str) -> float:
    match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f?;", _header())
    assert match, name
    return float(match.group(1))


def _visual(name: str) -> int:
    text = VISUALS.read_text(encoding="utf-8")
    match = re.search(rf"^{name}\s*=\s*(\w+)", text, re.MULTILINE)
    assert match, name
    value = match.group(1)
    return int(value) if value.isdigit() else _visual(value)


def _effect(spell: dict, index: int) -> dict:
    return spell[f"effect{index}"]


def _duration(spell: dict) -> int:
    return int(spell.get("duration_ms") or 0)


class RingEncoreDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) in MEMBERS}
        cls.templates = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) in TOTEMS}
        cls.models = {int(e["CreatureID"]): e for e in reg.creature_template_models if int(e["CreatureID"]) in TOTEMS}
        cls.cpp = CPP.read_text(encoding="utf-8")
        cls.sql = SQL.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(FIRST, LAST + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"spell": mine}), [])
        found = re.search(r"kSpellsEncore\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(found)
        self.assertEqual((int(found.group(1)), int(found.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_(?:TH|KO|LE|VL|MA|EN)_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual(sorted(SLICE.start + int(o) for o in offsets), mine)

    def test_the_members_are_bound(self):
        for entry, script in MEMBERS.items():
            with self.subTest(entry=entry):
                self.assertIn(f"RegisterDungeonReworkCreatureAI({script},", self.cpp)
                edit = self.edits[entry]
                self.assertEqual(edit["ScriptName"], script)
                self.assertEqual(edit["AIName"], "")
        theldren = self.edits[16059]
        self.assertEqual(int(theldren["CreatureImmunitiesId"]), 1972)       # S1: stun immune
        self.assertEqual(int(theldren["flags_extra"]) & 1, 0)          # no credit of his own: no INSTANCE_BIND
        # The other four own only their script (S1: no immunities; their health is WP-H's heroic override).
        for entry in (16053, 16049, 16058, 16052):
            self.assertEqual(tuple(self.edits[entry]["_update_columns"]), ("ScriptName", "AIName"))

    def test_the_totems(self):
        for entry, (display, heroic) in TOTEMS.items():
            with self.subTest(entry=entry):
                row = self.templates[entry]
                self.assertEqual(row["ScriptName"], "npc_brd_encore_totem")
                self.assertEqual(int(row["difficulty_entry_1"]), heroic)
                self.assertEqual(int(row["faction"]), 54)
                self.assertEqual(int(row["type"]), 11)
                self.assertEqual(int(row["lootid"]), 0)
                self.assertEqual(int(row["minlevel"]), 60)
                self.assertEqual(int(self.models[entry]["CreatureDisplayID"]), _visual(display))
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_brd_encore_totem,", self.cpp)
        rework = REWORK.read_text(encoding="utf-8")
        for i, entry in enumerate(TOTEMS, start=1):
            self.assertRegex(rework, rf"NPC_BRD_KORV_TOTEM_{i}\s*=\s*{entry}")

    def test_the_registry_hits_are_resolve_copies(self):
        schools = {210966: SCHOOL_PHYSICAL, 210983: SCHOOL_FROST, 210987: SCHOOL_FROST, 210992: SCHOOL_PHYSICAL,
                   210993: SCHOOL_PHYSICAL, 210997: SCHOOL_PHYSICAL}
        for spell_id, school in schools.items():
            with self.subTest(spell=spell_id):
                spell = self.spells[spell_id]
                self.assertEqual(_effect(spell, 1)["type"], SCHOOL_DAMAGE)
                self.assertEqual(int(spell["school"]), school)
                self.assertIn((spell_id, RESOLVE), self.scripts)
        # The C++ tags each registry mechanic (RingEncoreLogic.h 29-34) and sends each hit spell.
        for tag in ("TAG_TH_ROAR", "TAG_VL_BLIZZARD", "TAG_VL_FROST_NOVA", "TAG_MA_PIERCING_SHOT", "TAG_MA_SNAP_TRAP",
                    "TAG_MA_MULTI_SHOT"):
            self.assertIn(f".Tag({tag})", self.cpp)
        for name in ("SPELL_TH_ROAR", "SPELL_VL_BLIZZARD", "SPELL_VL_FROST_NOVA", "SPELL_MA_PIERCING_SHOT",
                     "SPELL_MA_SNAP_TRAP", "SPELL_MA_MULTI_SHOT"):
            self.assertIn(f".Spell({name})", self.cpp)

    def test_kicks_and_bars(self):
        # Kickable: Chain Heal, Ancestral Spirit, Frost Nova, Piercing Shot (the interrupt list).
        for spell_id, cast_ms in ((210969, "kChainHealCastMs"), (210971, "kSpiritCastMs"), (210986, "kNovaCastMs"),
                                  (210991, "kPiercingCastMs")):
            with self.subTest(spell=spell_id):
                spell = self.spells[spell_id]
                self.assertEqual(_raw(spell, "InterruptFlags"), 15)
                self.assertEqual(_raw(spell, "PreventionType"), 1)
                self.assertEqual(int(spell["cast_time_ms"]), int(_header_value(cast_ms)))
        # Not interruptible: the bars the registry owns the hit of.
        for spell_id, cast_ms in ((210960, "kChargeWarnMs"), (210965, "kRoarWarnMs"), (210996, "kMultiShotWarnMs")):
            with self.subTest(spell=spell_id):
                spell = self.spells[spell_id]
                self.assertEqual(_raw(spell, "InterruptFlags"), 0)
                self.assertEqual(int(spell["cast_time_ms"]), int(_header_value(cast_ms)))
        # The descriptor lists the kicks.
        for name in ("SPELL_KO_ANCESTRAL_SPIRIT, 3", "SPELL_KO_CHAIN_HEAL, 2", "SPELL_VL_FROST_NOVA_CAST, 2",
                     "SPELL_MA_PIERCING_SHOT_CAST, 1"):
            self.assertIn(name, self.cpp)

    def test_script_values(self):
        for spell_id in (210962, 210964, 210975, 210981, 210998):
            with self.subTest(spell=spell_id):
                spell = self.spells[spell_id]
                self.assertEqual(_effect(spell, 1)["type"], SCHOOL_DAMAGE)
                self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        for spell_id in (210970, 210974, 210976):
            with self.subTest(spell=spell_id):
                spell = self.spells[spell_id]
                self.assertEqual(_effect(spell, 1)["type"], HEAL)
                self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertEqual(int(self.spells[210975]["school"]), SCHOOL_FIRE)
        self.assertEqual(int(self.spells[210970]["school"]), SCHOOL_NATURE)

    def test_auras(self):
        s = self.spells
        self.assertEqual(_effect(s[210963], 1)["apply_aura"], AURA_MOD_HEALING_PCT)
        self.assertEqual(int(_effect(s[210963], 1)["base_points"]), -int(_header_value("kWoundedHealingPct")))
        self.assertEqual(_duration(s[210963]), int(_header_value("kWoundedMs")))
        self.assertEqual(_effect(s[210967], 1)["apply_aura"], AURA_MOD_FEAR)
        self.assertEqual(_duration(s[210967]), int(_header_value("kRoarFearMs")))
        self.assertEqual(_effect(s[210968], 1)["apply_aura"], AURA_MOD_MELEE_HASTE)
        self.assertEqual(int(_effect(s[210968], 1)["base_points"]), int(_header_value("kPrideHastePct")))
        # EN7: Magic, 6 charges.
        self.assertEqual(int(s[210973]["dispel"]), DISPEL_MAGIC)
        self.assertEqual(_raw(s[210973], "ProcCharges"), int(_header_value("kEarthShieldCharges")))
        self.assertEqual(_effect(s[210977], 1)["apply_aura"], AURA_MOD_DECREASE_SPEED)
        self.assertEqual(_duration(s[210977]), int(_header_value("kEarthbindSlowMs")))
        self.assertEqual(_effect(s[210979], 1)["apply_aura"], AURA_MOD_STUN)
        self.assertEqual(_duration(s[210979]), int(_header_value("kKidneyShotMs")))
        # EN9: no dispel, the cap.
        self.assertEqual(int(s[210980]["dispel"]), DISPEL_NONE)
        self.assertEqual(_raw(s[210980], "CumulativeAura"), int(_header_value("kWoundCap")))
        self.assertEqual(_effect(s[210982], 1)["apply_aura"], AURA_MOD_DODGE)
        self.assertEqual(int(_effect(s[210982], 1)["base_points"]), int(_header_value("kEvasionDodgePct")))
        self.assertEqual(_duration(s[210982]), int(_header_value("kEvasionMs")))
        self.assertEqual(_duration(s[210984]), int(_header_value("kBlizzardSlowMs")))
        self.assertEqual(_effect(s[210988], 1)["apply_aura"], AURA_MOD_ROOT)
        self.assertEqual(int(s[210988]["dispel"]), DISPEL_MAGIC)
        self.assertEqual(_duration(s[210988]), int(_header_value("kNovaRootMs")))
        self.assertEqual(_effect(s[210990], 1)["apply_aura"], AURA_SCHOOL_ABSORB)
        self.assertEqual(int(s[210990]["dispel"]), DISPEL_MAGIC)
        self.assertEqual(_effect(s[210994], 1)["apply_aura"], AURA_MOD_STUN)
        self.assertEqual(int(s[210994]["dispel"]), DISPEL_MAGIC)
        self.assertEqual(_duration(s[210994]), int(_header_value("kTrapFreezeMs")))
        self.assertEqual(_duration(s[210985]), int(_header_value("kBlizzardMs")))

    def test_looks_are_v1s(self):
        looks = {
            210962: "TH_EXECUTIONERS_CHARGE", 210964: "TH_EXECUTE", 210966: "TH_INTIMIDATING_ROAR",
            210968: "TH_CHAMPIONS_PRIDE", 210970: "KO_CHAIN_HEAL", 210972: "KO_ANCESTRAL_SPIRIT",
            210973: "KO_EARTH_SHIELD", 210975: "KO_SEARING_BOLT",
            210978: "LE_SHADOWSTEP", 210980: "LE_VICIOUS_WOUND", 210982: "LE_EVASION", 210985: "VL_BLIZZARD",
            210987: "VL_FROST_NOVA", 210989: "VL_BLINK", 210990: "VL_ICE_BARRIER", 210992: "MA_PIERCING_SHOT",
            210994: "MA_SNAP_TRAP_FREEZE", 210995: "MA_DISENGAGE", 210997: "MA_MULTI_SHOT",
            210999: "RL_BANNER_BURN",
        }
        for spell_id, name in looks.items():
            with self.subTest(spell=spell_id):
                self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), _visual(name))
        # Never the one-puff Garrote (V-1: the lasting Bite state) or the stock Evasion's one-shot as the lasting one.
        self.assertNotEqual(_raw(self.spells[210980], "SpellVisualID_1"), 757)
        self.assertNotEqual(_raw(self.spells[210982], "SpellVisualID_1"), 72)

    def test_the_fix_pass_rules(self):
        # R-1-RING MN-2: a member starts in the air; Grimstone's engage at the summon starts no fight before the leap.
        self.assertIn("Phase _phase = Phase::Leaping;", self.cpp)
        self.assertNotIn("Phase _phase = Phase::Fighting;", self.cpp)
        self.assertIn('Land("no leap");', self.cpp)
        # R-1-RING N-1: the credit takes a thrown, unburned banner with it.
        self.assertIn("if (GameObject* banner = grimstone->FindNearestGameObject(GO_BRD_ENCORE_BANNER, "
                      "kBannerSearchYd))", self.cpp)

    def test_the_rev(self):
        self.assertRegex(self.sql, r"DELETE FROM `smart_scripts` WHERE `entryorguid` IN \(16049, 16052, 16053, 16058, "
                                   r"16059\) AND `source_type` = 0;")
        self.assertIn("(16059, 1, 0, 'The title... is yours...', 14,", self.sql)
        self.assertRegex(self.sql, r"\(301280, 10, 6663, 'Banner of Provocation',")
        self.assertIn("'go_brd_encore_banner'", self.sql)
        self.assertIn("RegisterDungeonReworkGameObjectAI(go_brd_encore_banner,", self.cpp)
        self.assertEqual(_visual("GODI_ARENA_BANNER"), 6663)
        # No SmartAI inserted (rule 14 would ask for event_flags), no spawn rows.
        self.assertNotIn("INSERT INTO `smart_scripts`", self.sql)
        self.assertNotIn("INSERT INTO `creature`", self.sql)
        self.assertNotIn("INSERT INTO `gameobject` ", self.sql)

    def test_the_hooks(self):
        # D4's surface: the Encore registers its factory, never describes, credits through EncoreWon, and the hard
        # mode loot bit rides Theldren from his summon (rule 1).
        self.assertIn("BrdRingOfLaw::RegisterEncore(", self.cpp)
        self.assertNotIn("Mechanic::Describe(", self.cpp)
        self.assertIn("frame.EncoreWon()", self.cpp)
        self.assertIn("DungeonKit::SetHardModeLoot(c, true)", self.cpp)
        self.assertIn("TEMPSUMMON_CORPSE_TIMED_DESPAWN", self.cpp)
        self.assertNotIn("TEMPSUMMON_DEAD_DESPAWN, kCorpseMs", self.cpp)


if __name__ == "__main__":
    unittest.main()
