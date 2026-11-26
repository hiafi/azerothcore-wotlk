"""
Zul'Farrak build WP-D4b, the Stair and the Altar of the Pyramid: source/npcs/zul_farrak/pyramid_stair.py against its
C++ (modules/mod-dungeon-bosses src/ZulFarrak/StairLogic.h, SezzzizLogic.h, pyramid_stair_rework.cpp,
boss_sezzziz_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in the Stair's slice (213990-214029) and the two headers name the same ids;
  - Sezz'ziz 7275 and Nekrum 7796 are bound (SmartAI off) at the header's health, DamageModifier 2.4 / 3.0, 1972;
  - the specialists 301015-301017 are bound elite copies at SP's health, each naming WP-H's heroic entry; the barrel
    301018 is a helper nobody targets, the fused keg at scale 2.0;
  - the kick table (rule 24): Blood Offering is the only kickable cast (Fire); the Scream's bar is Physical and not
    interruptible; the totem's bar is not interruptible;
  - the dispel table (rule 25): Curse of Blood and Sandfury Hex are Curses, Hexed and the Scream's fear Magic, the
    bleed and Knockdown not dispellable;
  - the resolve copies (LESSONS L7), the bleed's refflat script, the Hex's script; the header's numbers; V's looks;
  - the C++ keeps the rules: NoAssist first, the stage machine by message only, the crew only through BlyCrew.h, the
    tank in every hit, the healer rule, the directors registered, the cleanup;
  - the SQL rev writes the one emote (group 0, type 41) and the three specialists' weapons, nothing else.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_zul_farrak_stair.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "ZulFarrak"
STAIR_H = MODULE_DIR / "StairLogic.h"
ALTAR_H = MODULE_DIR / "SezzzizLogic.h"
REWORK = MODULE_DIR / "ZulFarrakRework.h"
STAIR_CPP = MODULE_DIR / "pyramid_stair_rework.cpp"
ALTAR_CPP = MODULE_DIR / "boss_sezzziz_rework.cpp"
PYRAMID_H = MODULE_DIR / "PyramidFight.h"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_pyramid_stair_zul_farrak.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "zul_farrak"
HEROIC = TOOL_ROOT / "source" / "world" / "dungeons" / "zul_farrak.py"

SLICE = range(213990, 214030)
(BARREL_HIT, KNOCKDOWN, BARREL_BLAST, BARREL_TROLL, BLEED, BLEED_LOOK, TRAMPLING, CURSE, HEX, HEXED, LAVA_SPOUT,
 TOTEM_BAR, LAVA_GLOW) = range(213990, 214003)
(OFFERING, OFFERING_H, OFFERING_HIT, FRENZY, FRENZY_H, SCREAM_BAR, SCREAM_FEAR, OFFERING_BEAM) = range(214010, 214018)
SEZZZIZ, NEKRUM = 7275, 7796
BERSERKER, HEXMASTER, WITCH_DOCTOR, BARREL = 301015, 301016, 301017, 301018
HEROIC_IDS = {BERSERKER: 310539, HEXMASTER: 310540, WITCH_DOCTOR: 310541}
SP_HEALTH = {BERSERKER: 5346, HEXMASTER: 3603, WITCH_DOCTOR: 4278}
BASES = {BERSERKER: 1782, HEXMASTER: 1201, WITCH_DOCTOR: 1426, SEZZZIZ: 1535, NEKRUM: 1848}

SCHOOL_PHYSICAL, SCHOOL_FIRE, SCHOOL_SHADOW = 1, 4, 32
SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT = 2, 6, 3
AURA_PERIODIC_DAMAGE, AURA_MOD_STUN, AURA_MOD_FEAR, AURA_TRANSFORM = 3, 12, 7, 56
AURA_MOD_DAMAGE_PERCENT_DONE, AURA_MOD_DAMAGE_PERCENT_TAKEN, AURA_PERIODIC_DUMMY = 79, 87, 226
DISPEL_MAGIC, DISPEL_CURSE = 1, 2
PREVENTION_SILENCE = 1
ATTR1_NO_REDIRECTION, ATTR1_IS_CHANNELED, ATTR1_NO_REFLECTION = 0x8, 0x4, 0x80
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
CHANGE_MAP = 0x00080000
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT_PERIODIC = "spell_dungeon_refflat_periodic"
HEX_SCRIPT = "spell_zf_sandfury_hex"
UNIT_FLAG_NON_ATTACKABLE, UNIT_FLAG_NOT_SELECTABLE = 0x2, 0x02000000
# V's picks (_visuals.py).
SV = {BARREL_HIT: 889, KNOCKDOWN: 522, BARREL_BLAST: 889, BLEED: 15286, BLEED_LOOK: 372, CURSE: 876, HEX: 876,
      HEXED: 2295, LAVA_GLOW: 90508, FRENZY: 47, FRENZY_H: 47, SCREAM_FEAR: 247, OFFERING_BEAM: 7270}
BARREL_DISPLAY, BARREL_SCALE, FROG = 26252, 2.0, 7552


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


def _tune(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return text[text.index("namespace Tune"):]


def _value(path: Path, name: str) -> float:
    match = re.search(rf"\b{name} = (-?[\d.]+)f?;", _tune(path))
    assert match, name
    return float(match.group(1))


def _pair(path: Path, name: str) -> tuple[float, float]:
    match = re.search(rf"\b{name}\{{ (-?[\d.]+)f?, (-?[\d.]+)f? \}};", _tune(path))
    assert match, name
    return float(match.group(1)), float(match.group(2))


def _code(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith(("//", "*", "/*")))


class StairDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) in (SEZZZIZ, NEKRUM)}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates
                         if int(e["entry"]) in (BERSERKER, HEXMASTER, WITCH_DOCTOR, BARREL)}
        cls.models = [e for e in reg.creature_template_models
                      if int(e["CreatureID"]) in (BERSERKER, HEXMASTER, WITCH_DOCTOR, BARREL)]
        cls.stair = STAIR_CPP.read_text(encoding="utf-8")
        cls.altar = ALTAR_CPP.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_headers(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(BARREL_HIT, LAVA_GLOW + 1)) + list(range(OFFERING, OFFERING_BEAM + 1)))
        self.assertEqual(id_blocks.out_of_reservation("zul_farrak", {"spell": mine}), [])
        first = re.search(r"kSpellsStair\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        stair = re.findall(r"SPELL_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", STAIR_H.read_text(encoding="utf-8"))
        base = re.search(r"kAltarSpellBase = kSpellSlice\.first \+ (\d+);", STAIR_H.read_text(encoding="utf-8"))
        altar = re.findall(r"SPELL_\w+\s*=\s*ZfStair::kAltarSpellBase \+ (\d+),", ALTAR_H.read_text(encoding="utf-8"))
        ids = [SLICE.start + int(o) for o in stair] + [SLICE.start + int(base.group(1)) + int(o) for o in altar]
        self.assertEqual(sorted(ids), mine)

    def test_sezzziz_and_nekrum_are_bound(self):
        health = REWORK.read_text(encoding="utf-8")
        for entry, script, name, damage in ((SEZZZIZ, "boss_sezzziz_rework", "kSezzziz", 2.4),
                                            (NEKRUM, "boss_nekrum_rework", "kNekrum", 3.0)):
            row = self.edits[entry]
            self.assertEqual((row["ScriptName"], row["AIName"]), (script, ""))
            normal = re.search(rf"{name}\{{ (\d+), (\d+) \}}", health)
            self.assertEqual(math.ceil(BASES[entry] * row["HealthModifier"]), int(normal.group(1)))
            self.assertEqual((row["DamageModifier"], row["CreatureImmunitiesId"]), (damage, 1972))
            self.assertIn(f"RegisterDungeonReworkCreatureAI({script},", self.altar)

    def test_the_specialists_and_the_barrel(self):
        lock = HEROIC.read_text(encoding="utf-8")
        for entry, script in ((BERSERKER, "npc_zf_sandfury_berserker"), (HEXMASTER, "npc_zf_sandfury_hexmaster"),
                              (WITCH_DOCTOR, "npc_zf_sandfury_witch_doctor")):
            row = self.creatures[entry]
            self.assertEqual((row["ScriptName"], row["AIName"], row["rank"], row["faction"]), (script, "", 1, 37))
            self.assertEqual(math.ceil(BASES[entry] * row["HealthModifier"]), SP_HEALTH[entry])
            self.assertEqual(row["difficulty_entry_1"], HEROIC_IDS[entry])
            self.assertIn(f"{entry}: {HEROIC_IDS[entry]}", lock)        # WP-H's prediction
            self.assertIn(f"RegisterDungeonReworkCreatureAI({script},", self.stair)
            self.assertEqual(len([m for m in self.models if int(m["CreatureID"]) == entry]), 2)
        barrel = self.creatures[BARREL]
        self.assertEqual(barrel["ScriptName"], "npc_zf_weegli_barrel")
        self.assertEqual(barrel["unit_flags"] & (UNIT_FLAG_NON_ATTACKABLE | UNIT_FLAG_NOT_SELECTABLE),
                         UNIT_FLAG_NON_ATTACKABLE | UNIT_FLAG_NOT_SELECTABLE)
        self.assertEqual(barrel.get("difficulty_entry_1", 0), 0)
        model = [m for m in self.models if int(m["CreatureID"]) == BARREL]
        self.assertEqual([(int(m["CreatureDisplayID"]), float(m["DisplayScale"])) for m in model],
                         [(BARREL_DISPLAY, BARREL_SCALE)])
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_zf_weegli_barrel,", self.stair)

    def test_the_kick_table(self):
        kickable = {i for i, s in self.spells.items() if _raw(s, "PreventionType") == PREVENTION_SILENCE
                    or _raw(s, "InterruptFlags")}
        self.assertEqual(kickable, {OFFERING, OFFERING_H})
        for spell_id in (OFFERING, OFFERING_H):
            self.assertEqual(self.spells[spell_id]["school"], SCHOOL_FIRE)     # his only Fire cast
        self.assertEqual(self.spells[SCREAM_BAR]["school"], SCHOOL_PHYSICAL)    # his Shadow Bolt locks Shadow
        cast_times = {i: s.get("cast_time_ms") for i, s in self.spells.items() if s.get("cast_time_ms")}
        self.assertEqual(cast_times, {
            OFFERING: int(_pair(ALTAR_H, "kOfferingCastMs")[0]), OFFERING_H: int(_pair(ALTAR_H, "kOfferingCastMs")[1]),
            SCREAM_BAR: int(_value(ALTAR_H, "kScreamCastMs")), TOTEM_BAR: int(_value(STAIR_H, "kTotemBarMs"))})

    def test_the_dispel_table(self):
        dispel = {i: s.get("dispel", 0) for i, s in self.spells.items() if s.get("dispel")}
        self.assertEqual(dispel, {CURSE: DISPEL_CURSE, HEX: DISPEL_CURSE, HEXED: DISPEL_MAGIC,
                                  SCREAM_FEAR: DISPEL_MAGIC})
        self.assertEqual(self.spells[BLEED].get("dispel", 0), 0)
        self.assertEqual(self.spells[KNOCKDOWN].get("dispel", 0), 0)

    def test_the_resolve_copies(self):
        damaging = {i for i, s in self.spells.items() if (s.get("effect1") or {}).get("type") == SCHOOL_DAMAGE}
        self.assertEqual(damaging, {BARREL_HIT, TRAMPLING, LAVA_SPOUT, OFFERING_HIT})
        schools = {BARREL_HIT: SCHOOL_FIRE, TRAMPLING: SCHOOL_PHYSICAL, LAVA_SPOUT: SCHOOL_FIRE,
                   OFFERING_HIT: SCHOOL_SHADOW}
        for spell_id in damaging:
            spell = self.spells[spell_id]
            self.assertEqual(spell["school"], schools[spell_id])
            self.assertIn((spell_id, RESOLVE), self.scripts)
            self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
            self.assertTrue(_raw(spell, "AttributesEx") & ATTR1_NO_REDIRECTION)
            self.assertTrue(_raw(spell, "AttributesEx") & ATTR1_NO_REFLECTION)

    def test_the_auras(self):
        bleed = self.spells[BLEED]
        effect = bleed["effect1"]
        self.assertEqual((bleed["school"], bleed["mechanic"], bleed["duration_ms"]),
                         (SCHOOL_PHYSICAL, 0, int(_value(STAIR_H, "kBleedMs"))))
        self.assertEqual((effect["apply_aura"], int(effect["base_points"]), effect["die_sides"], effect["amplitude"]),
                         (AURA_PERIODIC_DAMAGE, int(_value(STAIR_H, "kBleedTickHundredths")), 0,
                          int(_value(STAIR_H, "kBleedTickMs"))))
        self.assertTrue(_raw(bleed, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertIn((BLEED, REFFLAT_PERIODIC), self.scripts)
        curse = self.spells[CURSE]
        self.assertEqual((curse["effect1"]["apply_aura"], int(curse["effect1"]["base_points"]),
                          curse["effect1"]["misc_value"], curse["duration_ms"]),
                         (AURA_MOD_DAMAGE_PERCENT_TAKEN, int(_value(STAIR_H, "kCursePhysicalTakenPct")), 1,
                          int(_value(STAIR_H, "kCurseMs"))))
        hex_ = self.spells[HEX]
        self.assertEqual((hex_["effect1"]["apply_aura"], hex_["effect1"]["amplitude"], _raw(hex_, "CumulativeAura")),
                         (AURA_PERIODIC_DUMMY, int(_value(STAIR_H, "kHexStackMs")),
                          int(_value(STAIR_H, "kHexMaxStacks"))))
        self.assertIn((HEX, HEX_SCRIPT), self.scripts)
        self.assertIn(f"RegisterSpellScript({HEX_SCRIPT});", self.stair)
        hexed = self.spells[HEXED]
        self.assertEqual((hexed["duration_ms"], hexed["effect1"]["apply_aura"], hexed["effect2"]["apply_aura"],
                          hexed["effect2"]["misc_value"]),
                         (int(_value(STAIR_H, "kHexedMs")), AURA_MOD_STUN, AURA_TRANSFORM, FROG))
        self.assertEqual(self.spells[KNOCKDOWN]["duration_ms"], int(_value(STAIR_H, "kKnockdownMs")))
        self.assertEqual(self.spells[KNOCKDOWN]["effect1"]["apply_aura"], AURA_MOD_STUN)
        self.assertEqual((self.spells[SCREAM_FEAR]["duration_ms"], self.spells[SCREAM_FEAR]["effect1"]["apply_aura"]),
                         (int(_value(ALTAR_H, "kFearMs")), AURA_MOD_FEAR))
        for spell_id in (KNOCKDOWN, BLEED, CURSE, HEX, HEXED, SCREAM_FEAR):
            self.assertTrue(_raw(self.spells[spell_id], "AuraInterruptFlags") & CHANGE_MAP, spell_id)
        frenzy, frenzy_h = self.spells[FRENZY], self.spells[FRENZY_H]
        self.assertEqual((frenzy["effect1"]["apply_aura"], int(frenzy["effect1"]["base_points"]),
                          frenzy["duration_ms"]),
                         (AURA_MOD_DAMAGE_PERCENT_DONE, int(_value(ALTAR_H, "kFrenzyPct")),
                          int(_value(ALTAR_H, "kFrenzyMs"))))
        # heroic: the script sets the amount (50 x stacks), the counter shows up to 255
        self.assertEqual((int(frenzy_h["effect1"]["base_points"]), frenzy_h["duration_ms"],
                          _raw(frenzy_h, "CumulativeAura")), (0, -1, int(_value(ALTAR_H, "kFrenzyStackLimit"))))
        self.assertIn("effect->ChangeAmount(FrenzyDamagePct(_frenzy));", self.altar)

    def test_the_looks_are_vs(self):
        self.assertEqual({i: _raw(s, "SpellVisualID_1") for i, s in self.spells.items() if i in SV}, SV)
        self.assertTrue(_raw(self.spells[OFFERING_BEAM], "AttributesEx") & ATTR1_IS_CHANNELED)
        self.assertIn("SetUInt32Value(UNIT_CHANNEL_SPELL, target ? uint32(SPELL_BLOOD_OFFERING_BEAM) : 0u)",
                      self.altar)

    def test_the_numbers(self):
        self.assertEqual(_pair(STAIR_H, "kBarrelPct"), (40, 50))
        self.assertEqual(_pair(STAIR_H, "kBarrelEveryMs"), (15000, 12000))
        self.assertEqual((_value(STAIR_H, "kBarrelWarnMs"), _value(STAIR_H, "kBarrelTrollPct")), (3000, 50))
        self.assertEqual((_value(STAIR_H, "kSendEveryMs"), _value(STAIR_H, "kWaveGapMs")), (8000, 10000))
        self.assertEqual((_value(STAIR_H, "kChargeMinYd"), _value(STAIR_H, "kChargeMaxYd")), (8, 25))
        self.assertEqual((_value(STAIR_H, "kTramplingPct"), _value(STAIR_H, "kTramplingWarnMs")), (30, 1500))
        self.assertEqual((_value(STAIR_H, "kTotemPct"), _value(STAIR_H, "kTotemRadiusYd")), (6, 8))
        self.assertEqual(_pair(ALTAR_H, "kOfferingHealPct"), (15, 25))
        self.assertEqual((_value(ALTAR_H, "kOfferingPlayerPct"), _value(ALTAR_H, "kAddsCap")), (25, 4))
        self.assertEqual((_value(ALTAR_H, "kScreamRadiusYd"), _value(ALTAR_H, "kGutchewEveryMs")), (8, 15000))

    def test_the_cpp_keeps_the_rules(self):
        stair, altar = _code(self.stair), _code(self.altar)
        # No assist calls, every tick before UpdateVictim (rule 27): the two bosses and the specialists.
        self.assertEqual(len(re.findall(r"ZulFarrak::NoAssist\(me\);[^\n]*\n\s+if \(!UpdateVictim\(\)\)", altar)), 2)
        self.assertEqual(len(re.findall(r"ZulFarrak::NoAssist\(me\);\n\s+if \(!UpdateVictim\(\)\)", stair)), 1)
        # The stage machine is the instance's: start, fail and complete by message, never a slot write.
        self.assertIn("SetData(DATA_PYRAMID_START, PYRAMID_STAGE_ALTAR)", altar)
        self.assertIn("SetData(DATA_PYRAMID_FAIL, PYRAMID_STAGE_ALTAR)", altar)
        self.assertIn("SetData(DATA_PYRAMID_COMPLETE, PYRAMID_STAGE_STAIR)", stair)
        for code in (stair, altar):
            self.assertNotIn("SetBossState", code)
        self.assertIn("RegisterPyramidStage(PYRAMID_STAGE_STAIR", stair)
        self.assertIn("RegisterPyramidStage(PYRAMID_STAGE_ALTAR", stair)
        self.assertIn("ZfPyramid::PyramidStage::OnStart(restart);", stair)
        # The crew only through BlyCrew.h (rule 28): the Offering's kill, the Ally handler, Weegli's own AI.
        self.assertIn("ZfCrew::KillCrew(member, me)", altar)
        self.assertIn("ZfCrew::RegisterCrewModeHandler(CrewMode::Ally", stair)
        self.assertIn("weegli->AI()->Talk(ZfCrew::YELL_WEEGLI_BARRELS);", stair)
        self.assertNotIn("SetFaction", altar)
        # Mechanics include the tank (rule 17); the lane's Weakened and Knockdown; the Offering's player hit.
        self.assertIn("spec.tankPct = pct;", stair)
        self.assertIn("spec.weakened = true;", stair)
        self.assertIn("spec.rider = SPELL_KNOCKDOWN;", stair)
        self.assertIn("spec.tankPct = Tune::kOfferingPlayerPct;", altar)
        self.assertIn(".TankDamage(Tune::kTramplingPct)", stair)
        self.assertIn(".TankDamage(Tune::kTotemPct)", stair)
        # Bots: the healer rule on both descriptors, the landing hold, the Altar's bounds on the Scream. The Altar's
        # descriptor is one copy (PyramidFight.h AltarDescriptor) on Sezz'ziz and on the director's stalker for the
        # whole stage (R-1-B mn-1).
        pyramid = _code(PYRAMID_H.read_text(encoding="utf-8"))
        self.assertIn("ZfPyramid::AddWoundHealRule(d, _heroic);", stair)
        altar_desc = pyramid[pyramid.index("inline BossMechanics::Descriptor AltarDescriptor(bool heroic)"):]
        self.assertIn("AddWoundHealRule(d, heroic);", altar_desc[:altar_desc.index("return d;")])
        self.assertIn("Mechanic::Describe(me, ZfPyramid::AltarDescriptor(_heroic));", altar)
        self.assertIn("Mechanic::Describe(stalker, ZfPyramid::AltarDescriptor(Heroic()));", stair)
        self.assertIn(".NoTelegraph().Within(_hold).Tag(TAG_HOLD)", stair)
        # R-1-B mn-2: the barrel's damage never starts a fight with the barrel.
        self.assertIn("/*skipCombat*/ true);", self.stair)
        self.assertIn(".Within(_bounds).Tag(TAG_SCREAM)", altar)
        # RB-1: Sezz'ziz's cleanup on reset, evade and death.
        cleanup = altar[altar.index("void Cleanup(char const* why, bool adds)"):]
        for piece in ("Mechanic::Cancel(me, handle)", "RemoveAurasDueToSpell(SPELL_BLOOD_FRENZY_H)",
                      "ZfPyramid::RemoveSandfuryBuff(me)", "Beam(nullptr)", "_arena.Reset()"):
            self.assertIn(piece, cleanup)
        for text in (self.stair, self.altar):
            self.assertNotIn("\t", text)


class StairSqlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8")

    def test_the_emote_and_the_weapons(self):
        self.assertIn("(7275, 0, 0, '%s offers $n''s blood to the loa!', 41, 0, 100, ", self.sql)
        groups = re.findall(r"EMOTE_\w+\s*=\s*(\d+),", ALTAR_H.read_text(encoding="utf-8"))
        self.assertEqual([int(g) for g in groups], [0])
        for row in ("(301015, 1, 4991, 0, 0, 0)", "(301016, 1, 6230, 0, 0, 0)", "(301017, 1, 1908, 0, 0, 0)"):
            self.assertIn(row, self.sql)

    def test_the_rev_touches_only_its_rows(self):
        code = "\n".join(line for line in self.sql.splitlines() if not line.startswith("--"))
        self.assertEqual(re.findall(r"(?:DELETE FROM|INSERT INTO|UPDATE) `(\w+)`", code),
                         ["creature_text", "creature_text", "creature_equip_template", "creature_equip_template"])
        self.assertIn("WHERE `CreatureID` = 7275 AND `GroupID` = 0;", code)


if __name__ == "__main__":
    unittest.main()
