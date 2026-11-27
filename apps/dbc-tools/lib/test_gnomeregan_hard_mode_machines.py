"""
Gnomeregan build WP-D6Hb, the Whole Workshop part b (Mekgineer Thermaplugg's heroic hard mode: the Electrocutioner,
Alert System and Pummeler schematics): source/npcs/gnomeregan/thermaplugg_hard_mode_machines.py against its C++
(modules/mod-dungeon-bosses src/Gnomeregan/ThermapluggHardModeMachinesLogic.h, thermaplugg_hard_mode_machines.cpp),
V's looks (source/npcs/gnomeregan/_visuals.py), WP-H's heroic id table and its SQL rev.

Checks:
  - the spells sit in the package's slice (214580-214619) and the header names the same ids in order;
  - the Pummeler's Fist 301136 is an inert helper (not attackable, not selectable, no XP) on V's fist display at the
    Pummeler's scale, bound to the script the C++ registers, no heroic template (INT reconcile);
  - nothing is kickable; the Justice bar and the fist's wind-up are the header's lengths, Physical, InterruptFlags 0,
    and keep his swing timer; the Voltage aura is +3% damage done a stack (the header's percent), the client's 255
    counter, not dispellable, NO_IMMUNITIES;
  - the two hits are resolve copies (Spotted Arcane, the fist Physical) that ignore caster modifiers and cannot be
    redirected or reflected (rule 2, LESSONS L7); every look is V's;
  - the numbers the C++ plays by id are V's (the numerals and their scale, the punch emote);
  - the C++ keeps the package's rules (the three machines called, never re-built; cleared in OnEnd; one registration);
  - the SQL rev writes lines 10 and 11 (type 41) and nothing else;
  - with BM's source on hand (BM_SRC), the drill's row 10 tags are the header's.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_gnomeregan_hard_mode_machines.py
"""

from __future__ import annotations

import os
import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import test_id_blocks as id_blocks  # noqa: E402
from lib.dsl import registry  # noqa: E402
from source.npcs.gnomeregan import _visuals as v  # noqa: E402

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Gnomeregan"
HEADER = MODULE_DIR / "ThermapluggHardModeMachinesLogic.h"
REWORK = MODULE_DIR / "GnomereganRework.h"
SCRIPT = MODULE_DIR / "thermaplugg_hard_mode_machines.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_thermaplugg_hard_mode_machines_gnomeregan.sql"
HEROIC = TOOL_ROOT / "source" / "world" / "dungeons" / "gnomeregan.py"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "gnomeregan"

SLICE = range(214580, 214620)
(VOLTAGE, JUSTICE_BAR, SPOTTED, SPOTTED_BEAM, FIST_HIT, WIND_UP, FACE_LIGHT) = range(214580, 214587)
FIST = 301136
SPELL_NAMES = ("SPELL_HMB_VOLTAGE", "SPELL_HMB_JUSTICE_BAR", "SPELL_HMB_SPOTTED", "SPELL_HMB_SPOTTED_BEAM",
               "SPELL_HMB_FIST_HIT", "SPELL_HMB_FIST_WIND_UP", "SPELL_HMB_FACE_LIGHT")

SCHOOL_PHYSICAL, SCHOOL_NATURE, SCHOOL_ARCANE = 1, 8, 64
SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT = 2, 6, 3
AURA_DUMMY, AURA_MOD_DAMAGE_PERCENT_DONE = 4, 79
PREVENTION_SILENCE = 1
ATTR0_NO_IMMUNITIES = 0x20000000
ATTR1_NO_REDIRECTION, ATTR1_NO_REFLECTION = 0x8, 0x80
ATTR2_DO_NOT_RESET_COMBAT_TIMERS = 0x00020000
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
CHANGE_MAP = 0x00080000
RESOLVE = "spell_boss_mechanics_resolve"
UNIT_FLAG_NON_ATTACKABLE, UNIT_FLAG_NOT_SELECTABLE = 0x2, 0x02000000
FLAGS_EXTRA_NO_XP, FLAGS_EXTRA_TRIGGER = 0x40, 0x80
EMOTE_ONESHOT_ATTACK_UNARMED = 35   # Emotes.dbc 35 plays AnimationData 16 (AttackUnarmed)


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


def _raw(spell: dict, column: str) -> int | float:
    return (spell.get("raw_overrides") or {}).get(column, 0) or 0


def _tune() -> str:
    text = HEADER.read_text(encoding="utf-8")
    return text[text.index("namespace Tune"):]


def _value(name: str) -> float:
    match = re.search(rf"\b{name} = (-?[\d.]+)f?;", _tune())
    assert match, name
    return float(match.group(1))


def _code(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith(("//", "*", "/*")))


def _body(code: str, signature: str) -> str:
    start = code.index(signature)
    return code[start:code.index("\n    }", start)]


class SchematicsDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == FIST}
        cls.models = {(int(e["CreatureID"]), int(e["Idx"])): e for e in reg.creature_template_models
                      if int(e["CreatureID"]) == FIST}
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(VOLTAGE, FACE_LIGHT + 1)))
        self.assertEqual(id_blocks.out_of_reservation("gnomeregan", {"spell": mine}), [])
        slice_ = re.search(r"kSpellsHardModeB\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertEqual((int(slice_.group(1)), int(slice_.group(2))), (SLICE.start, SLICE.stop - 1))
        named = re.findall(r"(SPELL_HMB_\w+)\s*=\s*kSpellSlice\.first \+ (\d+),", self.header)
        self.assertEqual([n for n, _ in named], list(SPELL_NAMES))
        self.assertEqual([SLICE.start + int(o) for _, o in named], mine)
        self.assertIn(f"kSpellCount = {len(mine)};", self.header)

    def test_the_fist(self):
        fist = self.creatures[FIST]
        self.assertEqual(fist["ScriptName"], "npc_gnomer_pummelers_fist")
        self.assertIn("NPC_PUMMELERS_FIST          = 301136,", REWORK.read_text(encoding="utf-8"))
        self.assertEqual(fist["unit_flags"] & (UNIT_FLAG_NON_ATTACKABLE | UNIT_FLAG_NOT_SELECTABLE),
                         UNIT_FLAG_NON_ATTACKABLE | UNIT_FLAG_NOT_SELECTABLE)
        self.assertEqual(fist["flags_extra"] & FLAGS_EXTRA_NO_XP, FLAGS_EXTRA_NO_XP)
        self.assertFalse(fist["flags_extra"] & FLAGS_EXTRA_TRIGGER)     # seen by the players
        self.assertEqual((fist["lootid"], fist["DamageModifier"]), (0, 0.0))
        model = self.models[(FIST, 0)]
        self.assertEqual(int(model["CreatureDisplayID"]), v.MT_FIST_DISPLAY)
        self.assertEqual(v.MT_FIST_DISPLAY, v.DISPLAY_PUMMELER)
        self.assertEqual(float(model["DisplayScale"]), v.PUMMELER_SCALE)     # SP: at his fight's scale
        # INT reconcile: a helper runs on its normal entry on heroic (not in WP-H's `extra=` / `_HEROIC_ID`).
        self.assertIsNone(re.search(r"\b301136: \d+", HEROIC.read_text(encoding="utf-8")))
        self.assertEqual(fist.get("difficulty_entry_1", 0), 0)
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_gnomer_pummelers_fist,", self.cpp)
        self.assertIn('GnomerTest::RegisterBoss("schematics"', self.cpp)

    def test_nothing_is_kickable_and_the_bars(self):
        kickable = {i for i, s in self.spells.items() if _raw(s, "PreventionType") == PREVENTION_SILENCE
                    or _raw(s, "InterruptFlags")}
        self.assertEqual(kickable, set())
        self.assertEqual({i for i, s in self.spells.items() if s.get("cast_time_ms")}, {JUSTICE_BAR, WIND_UP})
        for bar, ms in ((JUSTICE_BAR, _value("kJusticeCastMs")), (WIND_UP, _value("kFistWarnMs"))):
            spell = self.spells[bar]
            self.assertEqual(spell["school"], SCHOOL_PHYSICAL)      # the Detonator's kick locks Fire only
            self.assertEqual(spell["cast_time_ms"], int(ms))
            self.assertEqual(spell["effect1"]["type"], DUMMY_EFFECT)
            self.assertTrue(_raw(spell, "AttributesEx2") & ATTR2_DO_NOT_RESET_COMBAT_TIMERS)

    def test_the_voltage_aura(self):
        aura = self.spells[VOLTAGE]
        effect = aura["effect1"]
        self.assertEqual((effect["type"], effect["apply_aura"]), (APPLY_AURA, AURA_MOD_DAMAGE_PERCENT_DONE))
        self.assertEqual(effect["base_points"] + effect.get("die_sides", 1), int(_value("kVoltagePctPerStack")))
        self.assertEqual(effect["misc_value"], 127)          # every school: his melee and Knock Away
        self.assertEqual(_raw(aura, "CumulativeAura"), 255)
        self.assertEqual((aura["dispel"], aura["duration_ms"]), (0, -1))
        self.assertTrue(aura["attributes"] & ATTR0_NO_IMMUNITIES)
        self.assertTrue(_raw(aura, "AuraInterruptFlags") & CHANGE_MAP)
        light = self.spells[FACE_LIGHT]
        self.assertEqual((light["effect1"]["apply_aura"], light["duration_ms"]),
                         (AURA_DUMMY, int(_value("kFaceLightMs"))))

    def test_the_hits_are_resolve_copies(self):
        damaging = {i for i, s in self.spells.items() if (s.get("effect1") or {}).get("type") == SCHOOL_DAMAGE}
        self.assertEqual(damaging, {SPOTTED, FIST_HIT})
        self.assertEqual(self.spells[SPOTTED]["school"], SCHOOL_ARCANE)
        self.assertEqual(self.spells[FIST_HIT]["school"], SCHOOL_PHYSICAL)
        for spell_id in damaging:
            spell = self.spells[spell_id]
            self.assertIn((spell_id, RESOLVE), self.scripts)
            self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
            self.assertTrue(_raw(spell, "AttributesEx") & ATTR1_NO_REDIRECTION)
            self.assertTrue(_raw(spell, "AttributesEx") & ATTR1_NO_REFLECTION)

    def test_the_looks_are_vs(self):
        looks = {VOLTAGE: v.EL_VOLTAGE, JUSTICE_BAR: v.EL_JUSTICE_CAST, SPOTTED_BEAM: v.MA_SPOTTED,
                 FIST_HIT: v.CP_PUMMEL, WIND_UP: v.CP_PUNCH_POSE, FACE_LIGHT: v.MT_FIST_FACE_GLOW}
        self.assertEqual({i: _raw(s, "SpellVisualID_1") for i, s in self.spells.items() if i in looks}, looks)
        self.assertEqual(_raw(self.spells[SPOTTED], "SpellVisualID_1"), 0)
        # Never wired: V's WRONG looks (Supercharge's 2048, Overload's 7678, the crafting hammer 395).
        wired = {_raw(s, "SpellVisualID_1") for s in self.spells.values()}
        self.assertFalse(wired & {2048, 7678, 395})

    def test_the_numbers_the_script_plays(self):
        displays = re.search(r"kNumeralDisplays\{ \{ (\d+), (\d+), (\d+) \} \};", self.header)
        self.assertEqual(tuple(int(d) for d in displays.groups()), tuple(v.MT_NUMERALS))
        self.assertEqual(tuple(v.MT_NUMERALS), (v.DISPLAY_NUMERAL_1, v.DISPLAY_NUMERAL_2, v.DISPLAY_NUMERAL_3))
        self.assertAlmostEqual(_value("kNumeralScale"), v.numeral_scale(4.0), places=3)
        emote = re.search(r"kFistEmote = (\d+);", self.header)
        self.assertEqual(int(emote.group(1)), EMOTE_ONESHOT_ATTACK_UNARMED)
        self.assertEqual(v.CP_PUNCH_EMOTE_ANIM, 16)
        # SP's MT21-MT24 rows.
        self.assertEqual((_value("kVoltageTickMs"), _value("kJusticeEvery"), _value("kJusticePct")), (5000, 6, 75))
        self.assertEqual((_value("kJusticeSafeYd"), _value("kSpottedPct"), _value("kFistPct")), (8, 50, 60))
        self.assertEqual((_value("kLightsConeDeg"), _value("kLightsDegPerSec")), (30, 12))
        self.assertEqual((_value("kFistWarnMs"), _value("kFistApartMs"), _value("kFistEveryMs")), (4000, 2500, 18000))
        self.assertEqual(_value("kFistNearYd"), 50)          # section 7 #33 A

    def test_the_cpp_calls_the_machines(self):
        code = _code(self.cpp)
        # Never re-implemented: the machines' factories (D3, D4, D5), the 3-argument combination one.
        for factory in ("GnomereganMachines::MakeElectroVoltageMeter(", "GnomereganMachines::MakeAlertLightsMachine(",
                        "GnomereganMachines::MakeComboMachine(Owner(boss), FistSpec(face), FistExtras())"):
            self.assertIn(factory, code)
        self.assertNotIn("DungeonKit::TurningLights", code)
        self.assertNotIn("DungeonKit::CalledCombination", code)
        self.assertIn("GnomerThermaplugg::HardModePackage::SchematicsB", code)
        # RB-1: everything undone in OnEnd.
        end = _body(code, "void OnEnd(ThermapluggFight& fight, bool won) override")
        for piece in ("_combo->Clear();", "_lights->Clear();", "_voltage->Clear();", "EndCombinationUnits(boss);",
                      "Unlist();"):
            self.assertIn(piece, end)
        # Rule 17 and the Penalty columns: Spotted takes the tank row too, never Weakened; the fist is Weakened.
        spotted = _body(code, "void OnSpotted(Player* who, GnomereganMachines::SpotSource source)")
        self.assertIn("hit.tankPct = hit.pct;", spotted)
        self.assertIn("hit.weakened = Tune::kSpottedWeakened;", spotted)
        self.assertIn("_fight->OpenFace(std::nullopt, \"spotted\")", spotted)
        self.assertIn("spec.weakened = Tune::kFistWeakened;", code)
        self.assertIn("spec.justice.alternate = false;", code)
        # MT21: the mines' and bombs' hits charge him; his factor reaches D6's percents.
        self.assertIn("_voltage->Add(volts,", code)
        self.assertIn("float DamageFactor(ThermapluggFight const& /*fight*/) const override", code)
        for text in ("\t",):
            self.assertNotIn(text, self.cpp)
            self.assertNotIn(text, self.header)

    @unittest.skipUnless(os.environ.get("BM_SRC") and (Path(os.environ["BM_SRC"]) / "MechanicDrill.h").is_file(),
                         "BM_SRC (mod-boss-mechanics src) not set")
    def test_the_drill_tags_are_the_headers(self):
        drill = (Path(os.environ["BM_SRC"]) / "MechanicDrill.h").read_text(encoding="utf-8")
        pairs = re.findall(r"\{ TAG_(HMB_\w+), \"(kGn\w+)\" \}", self.header)
        self.assertEqual(len(pairs), 5)
        for tag, name in pairs:
            ours = int(re.search(rf"\bTAG_{tag}\s*=\s*(\d+),", self.header).group(1))
            theirs = int(re.search(rf"\b{name} = (\d+);", drill).group(1))
            self.assertEqual(ours, theirs, name)
        floor = int(re.search(r"\bTAG_HMB_LIGHTS_FLOOR\s*=\s*(\d+),", self.header).group(1))
        lights = int(re.search(r"\bkGnTagHmLights = (\d+);", drill).group(1))
        self.assertEqual(floor, lights + 1)     # MechanicDrill.h LightsFloorTag
        reported = re.search(r"kGnReportedTags\[\] = \{([^}]*)\}", drill).group(1)
        self.assertTrue({80, 81, 82, 83, 84, 85} <= {int(t) for t in re.findall(r"\d+", reported)})


class SchematicsSqlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.code = "\n".join(line for line in cls.sql.splitlines() if not line.startswith("--"))

    def test_the_emotes(self):
        lines = re.findall(r"\(7800, (\d+), 0, '([^']*)', (\d+), ", self.code)
        self.assertEqual(lines, [
            ("10", "%s overloads the room. Get to him!", "41"),
            ("11", "A giant fist winds up inside a Gnome Face!", "41"),
        ])
        groups = re.findall(r"EMOTE_HMB_\w+\s*=\s*(\d+),", HEADER.read_text(encoding="utf-8"))
        self.assertEqual(sorted(int(g) for g in groups), [10, 11])

    def test_the_rev_touches_only_its_rows(self):
        self.assertEqual(re.findall(r"(?:DELETE FROM|INSERT INTO|(?<!KEY )UPDATE) `(\w+)`", self.code),
                         ["creature_text", "creature_text"])
        self.assertIn("WHERE `CreatureID` = 7800 AND `GroupID` IN (10, 11);", self.code)


if __name__ == "__main__":
    unittest.main()
