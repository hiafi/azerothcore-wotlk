"""
Scarlet Monastery build WP-D5, Houndmaster Loksey: source/npcs/scarlet_monastery/loksey.py against its C++
(modules/mod-dungeon-bosses src/ScarletMonastery/LokseyLogic.h, boss_houndmaster_loksey_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in his slice (212540-212569) and LokseyLogic.h names the same ids;
  - Loksey 3974 is bound (SmartAI off) at 38k on the level 34 paladin base, stun immune, INSTANCE_BIND, the stock 2.4;
  - the two dogs: their own templates (hound level 33 at 3,000 and pup level 32 at 800 on the warrior bases), their
    scripts, no stun immunity, no loot or XP, the stock hound's display (the pup at 0.7);
  - the heroic Release whistle is a 2.5 s kick in a school Correction does not use; Correction is an uninterruptible
    2 s bar; the Mark landing and the cone are resolve copies; the tank's hit is the kit's refflat damage at 20 / 30%;
  - the Scent is a 5 s non-dispellable debuff, Whipped Frenzy a Magic stacking +50% buff, his own frenzy a Magic +30%
    haste, Cowed a pacify + root + 25% damage taken that is not a stun;
  - the looks are V's ids (never a WRONG-listed one);
  - the C++ registers the mechanics the build spec names (tank included where it says so; the F5 trail built from a
    Bait and per-marker Circles; Fetch a 1-body Soak; Correction a TankExempt cone with the tank's own hit);
  - the SQL rev deletes the three stock hounds, writes the four new emotes (type 41) and touches nothing else.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scarlet_monastery_loksey.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "ScarletMonastery"
HEADER = MODULE_DIR / "LokseyLogic.h"
REWORK = MODULE_DIR / "ScarletMonasteryRework.h"
SCRIPT = MODULE_DIR / "boss_houndmaster_loksey_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_loksey_scarlet_monastery.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "scarlet_monastery"
VISUALS = PACKAGE / "_visuals.py"

SLICE = range(212540, 212570)
(RELEASE_CAST, WHISTLE, SCENT, SCENT_FLASH, HOUND_LEAP, WHIPPED_FRENZY, LOKSEY_FRENZY, CORRECTION_CAST,
 CORRECTION_HIT, CORRECTION_TANK, FETCH_THROW, COWED) = range(212540, 212552)
LOKSEY, HOUND, PUP = 3974, 300908, 300909
PALADIN_34_BASE = 967       # creature_classlevelstats level 34 class 2 basehp0
WARRIOR_33_BASE = 1110      # level 33 class 1
WARRIOR_32_BASE = 1057      # level 32 class 1
STOCK_HOUND_DISPLAY = 2709

SCHOOL_PHYSICAL, SCHOOL_NATURE = 1, 8
SCHOOL_DAMAGE, DUMMY_EFFECT = 2, 3
AURA_DUMMY, AURA_MOD_PACIFY, AURA_MOD_ROOT = 4, 25, 26
AURA_MOD_DAMAGE_PERCENT_DONE, AURA_MOD_DAMAGE_PERCENT_TAKEN, AURA_MOD_MELEE_HASTE = 79, 87, 138
DISPEL_MAGIC = 1
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT_DAMAGE = "spell_dungeon_refflat_damage"
TARGET_DEST_DEST = 87
FLAG_DEST_LOCATION = 0x40
STOCK_HOUND_GUIDS = (40089, 40090, 40091)
# V-wrong looks that must never be wired (VR "Looks with no good candidate" and the WRONG lists): none of these is a
# Loksey pick; Horn of Winter's icy breath and Scent of Blood's empty State kit are the nearest traps.
WRONG_SPELL_VISUALS = (12396, 14210)


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


def _header() -> str:
    return HEADER.read_text(encoding="utf-8")


def _header_value(name: str) -> float:
    match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f?;", _header())
    assert match, name
    return float(match.group(1))


def _nh_values(name: str) -> tuple[float, float]:
    match = re.search(rf"\b{name}\{{\s*(-?[\d.]+)f?,\s*(-?[\d.]+)f?\s*\}}", _header())
    assert match, name
    return float(match.group(1)), float(match.group(2))


def _visual(name: str) -> int:
    text = VISUALS.read_text(encoding="utf-8")
    match = re.search(rf"^{name}\s*=\s*(\w+)", text, re.MULTILINE)
    assert match, name
    value = match.group(1)
    return int(value) if value.isdigit() else _visual(value)


def _code(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith(("//", "*", "/*")))


class LokseyDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) == LOKSEY}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) in (HOUND, PUP)}
        cls.models = {int(e["CreatureID"]): e for e in reg.creature_template_models
                      if int(e["CreatureID"]) in (HOUND, PUP)}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.code = _code(cls.cpp)

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(RELEASE_CAST, COWED + 1)))
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery", {"spell": mine}), [])
        first = re.search(r"kSpellsLoksey\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(first)
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_LK_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))

    def test_loksey_is_bound(self):
        boss = self.edits[LOKSEY]
        self.assertEqual(boss["ScriptName"], "boss_houndmaster_loksey_rework")
        self.assertEqual(boss["AIName"], "")
        self.assertLessEqual(abs(math.ceil(PALADIN_34_BASE * boss["HealthModifier"]) - 38000), 2)
        self.assertEqual(38000, int(_nh_values("kBossHealth")[0]))
        self.assertEqual(boss["DamageModifier"], 2.4)
        self.assertEqual(boss["CreatureImmunitiesId"], 1972)
        self.assertEqual(boss["flags_extra"], 1)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_houndmaster_loksey_rework,", self.cpp)
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_sm_loksey_hound,", self.cpp)
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_sm_kennel_pup,", self.cpp)
        self.assertIn('SmTest::RegisterBoss("loksey"', self.cpp)

    def test_the_dogs(self):
        hound, pup = self.creatures[HOUND], self.creatures[PUP]
        self.assertEqual(hound["name"], "Loksey's Tracking Hound")
        self.assertEqual(pup["name"], "Kennel Pup")
        self.assertEqual(hound["ScriptName"], "npc_sm_loksey_hound")
        self.assertEqual(pup["ScriptName"], "npc_sm_kennel_pup")
        for dog in (hound, pup):
            self.assertEqual(dog["AIName"], "")
            self.assertEqual(int(dog["unit_class"]), 1)
            self.assertEqual(int(dog["CreatureImmunitiesId"]), 0)       # a stun holds a dog off its marker
            self.assertEqual(int(dog["type"]), 1)                       # a beast, as the stock hound
            self.assertEqual(int(dog["family"]), 25)
            self.assertEqual(int(dog["faction"]), 67)                   # the Scarlet Crusade, as the stock hound
            self.assertEqual(int(dog["lootid"]), 0)
            self.assertTrue(int(dog["flags_extra"]) & 0x40)             # no XP
            self.assertEqual(int(dog["BaseAttackTime"]), 2000)
        self.assertEqual((int(hound["minlevel"]), int(hound["maxlevel"])), (33, 33))
        self.assertEqual((int(pup["minlevel"]), int(pup["maxlevel"])), (32, 32))
        normal_hound, normal_pup = int(_nh_values("kHoundHealth")[0]), int(_nh_values("kPupHealth")[0])
        self.assertEqual(math.ceil(WARRIOR_33_BASE * float(hound["HealthModifier"])), normal_hound)
        self.assertEqual(math.ceil(WARRIOR_32_BASE * float(pup["HealthModifier"])), normal_pup)
        self.assertEqual((normal_hound, normal_pup), (3000, 800))
        # The melee is this WP's default (rule 19): fewer swings of weight on the tank than a stock pack.
        self.assertEqual(float(hound["DamageModifier"]), 1.1)
        self.assertEqual(float(pup["DamageModifier"]), 0.5)
        self.assertLess(3 * 1.1 + 6 * 0.5, 4 * 1.7)       # the full pack on the tank: under a stock pack of four
        self.assertEqual([int(self.models[e]["CreatureDisplayID"]) for e in (HOUND, PUP)],
                         [STOCK_HOUND_DISPLAY] * 2)
        self.assertEqual(float(self.models[HOUND]["DisplayScale"]), 1.0)
        self.assertEqual(float(self.models[PUP]["DisplayScale"]), _pup_scale())
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery", {"creature": [HOUND, PUP]}), [])
        self.assertEqual((int(hound["entry"]), int(pup["entry"])), (300908, 300909))

    def test_release_is_a_heroic_kick_in_its_own_school(self):
        release = self.spells[RELEASE_CAST]
        self.assertEqual(release["cast_time_ms"], int(_header_value("kReleaseCastMs")))
        self.assertEqual(_raw(release, "InterruptFlags"), 15)
        self.assertEqual(_raw(release, "PreventionType"), 1)
        self.assertEqual(release["effect1"]["type"], DUMMY_EFFECT)
        self.assertEqual(release["school"], SCHOOL_NATURE)
        self.assertEqual(self.spells[CORRECTION_CAST]["school"], SCHOOL_PHYSICAL)
        self.assertNotEqual(release["school"], self.spells[CORRECTION_CAST]["school"])    # rule 5
        self.assertEqual(_raw(release, "SpellVisualID_1"), _visual("LK_WHISTLE"))
        self.assertIn("d.interrupts.emplace_back(NPC_LOKSEY, SPELL_LK_RELEASE_CAST, kReleaseKickPriority", self.cpp)
        # The pups follow the cast: 6 when it ran, 3 when it was cut.
        self.assertIn("if (spell && spell->Id == SPELL_LK_RELEASE_CAST && Active())\n            ReleaseLanded(false);",
                      self.cpp)
        self.assertIn("if (spell && spell->Id == SPELL_LK_RELEASE_CAST && Active() && me->IsAlive())\n"
                      "            ReleaseLanded(true);", self.cpp)

    def test_correction(self):
        bar = self.spells[CORRECTION_CAST]
        self.assertEqual(bar["cast_time_ms"], int(_header_value("kCorrectionCastMs")))
        self.assertEqual(_raw(bar, "InterruptFlags"), 0)
        self.assertEqual(_raw(bar, "PreventionType"), 0)
        self.assertEqual(_raw(bar, "SpellVisualID_1"), _visual("LK_CORRECTION"))
        hit = self.spells[CORRECTION_HIT]
        self.assertEqual(hit["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertIn((CORRECTION_HIT, RESOLVE), self.scripts)
        self.assertEqual(hit["school"], SCHOOL_PHYSICAL)
        tank = self.spells[CORRECTION_TANK]
        normal, heroic = _nh_values("kCorrectionTankPct")
        effect = tank["effect1"]
        self.assertEqual(effect["type"], SCHOOL_DAMAGE)
        self.assertEqual(effect["base_points"] + effect["die_sides"], round(normal * 100))
        self.assertEqual(_raw(tank, "EffectMiscValueB_1"), round(heroic * 100))
        self.assertTrue(int(_raw(tank, "AttributesEx3")) & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertIn((CORRECTION_TANK, REFFLAT_DAMAGE), self.scripts)
        # The registry cone skips the tank (Frontal); the script hits him itself when he stands in it.
        self.assertIn("BossMechanics::TankExempt::Yes", self.code)
        self.assertIn(".Spell(SPELL_LK_CORRECTION_HIT).Tag(TAG_LK_CORRECTION)", self.code)
        self.assertIn("me->CastSpell(tank, SPELL_LK_CORRECTION_TANK, true);", self.code)
        self.assertIn("DungeonKit::CastBar(me, SPELL_LK_CORRECTION_CAST);", self.code)

    def test_the_mark_trail_is_a_bait_and_circles(self):
        # F5 from existing kinds: no new BM option. The carrier's walk is a Bait on the carrier alone; each marker a
        # 5 yd Circle with the Hound Leap landing, the tank's row included.
        self.assertIn("Mechanic::Bait(me, BossMechanics::BaitRule::Farthest(), kScentFarYd, Ms(kScentMs))", self.code)
        self.assertIn("only.carriers.insert(carrier->GetGUID());", self.code)
        self.assertIn("Mechanic::Circle(me, BossMechanics::Anchor(spot), kMarkerRadiusYd, Ms(kMarkerWarnMs))",
                      self.code)
        self.assertIn("marker.Damage(pct).TankDamage(pct).Weakened().Spell(SPELL_LK_HOUND_LEAP)", self.code)
        self.assertIn(".Tag(TAG_LK_MARK_LANDING)", self.code)
        landing = self.spells[HOUND_LEAP]
        self.assertEqual(landing["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertIn((HOUND_LEAP, RESOLVE), self.scripts)
        self.assertEqual(landing["school"], SCHOOL_PHYSICAL)
        self.assertEqual(_raw(landing, "SpellVisualID_1"), _visual("LK_LEAP_LANDING"))
        self.assertEqual(_nh_values("kMarkLandingPct"), (35.0, 45.0))

    def test_the_scent(self):
        scent = self.spells[SCENT]
        self.assertEqual(scent["duration_ms"], int(_header_value("kScentMs")))
        self.assertEqual(scent["dispel"], 0)
        self.assertEqual(scent["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertTrue(int(scent["attributes"]) & 0x20000000)          # NO_IMMUNITIES: the trail still comes
        self.assertEqual(_raw(scent, "SpellVisualID_1"), _visual("LK_SCENT_RING"))
        flash = self.spells[SCENT_FLASH]
        self.assertEqual(_raw(flash, "SpellVisualID_1"), _visual("LK_SCENT"))
        self.assertEqual(flash["effect1"]["type"], DUMMY_EFFECT)
        self.assertEqual(flash["effect1"]["implicit_target_a"], 25)    # on the carrier (a target, not the caster)

    def test_the_frenzies(self):
        whipped = self.spells[WHIPPED_FRENZY]
        pct = int(_header_value("kWhippedFrenzyPct"))
        self.assertEqual(whipped["dispel"], DISPEL_MAGIC)
        self.assertEqual(whipped["duration_ms"], int(_header_value("kFrenzyNormalMs")))
        self.assertEqual(whipped["effect1"]["apply_aura"], AURA_MOD_MELEE_HASTE)
        self.assertEqual(whipped["effect1"]["base_points"], pct)
        self.assertEqual(whipped["effect2"]["apply_aura"], AURA_MOD_DAMAGE_PERCENT_DONE)
        self.assertEqual(whipped["effect2"]["base_points"], pct)
        self.assertEqual(_raw(whipped, "CumulativeAura"), 255)           # heroic: no cap
        self.assertEqual(_raw(whipped, "SpellVisualID_1"), _visual("LK_WHIPPED_FRENZY"))
        own = self.spells[LOKSEY_FRENZY]
        self.assertEqual(own["dispel"], DISPEL_MAGIC)
        self.assertEqual(own["duration_ms"], int(_header_value("kLokseyFrenzyMs")))
        self.assertEqual(own["effect1"]["apply_aura"], AURA_MOD_MELEE_HASTE)
        self.assertEqual(own["effect1"]["base_points"], int(_header_value("kLokseyFrenzyHastePct")))
        # The purge list: both dogs' frenzy and his own (a reward); the frenzied dog first in the kill order.
        self.assertIn("d.purges.emplace_back(NPC_SM_TRACKING_HOUND, SPELL_LK_WHIPPED_FRENZY", self.code)
        self.assertIn("d.purges.emplace_back(NPC_SM_KENNEL_PUP, SPELL_LK_WHIPPED_FRENZY", self.code)
        self.assertIn("d.purges.emplace_back(NPC_LOKSEY, SPELL_LK_LOKSEY_FRENZY", self.code)
        self.assertIn("BossMechanics::Condition::HasAura(SPELL_LK_WHIPPED_FRENZY)", self.code)
        # Heroic: until the dog dies.
        self.assertIn("aura->SetMaxDuration(-1);", self.code)

    def test_fetch_and_cowed(self):
        throw = self.spells[FETCH_THROW]
        self.assertEqual(throw["effect1"]["implicit_target_a"], TARGET_DEST_DEST)
        self.assertEqual(_raw(throw, "Targets"), FLAG_DEST_LOCATION)
        self.assertEqual(float(_raw(throw, "Speed")), _header_value("kFetchMissileSpeed"))
        self.assertEqual(_raw(throw, "SpellVisualID_1"), _visual("LK_FETCH"))
        cowed = self.spells[COWED]
        self.assertEqual(cowed["duration_ms"], int(_header_value("kCowedMs")))
        self.assertEqual(cowed["effect1"]["apply_aura"], AURA_MOD_PACIFY)
        self.assertEqual(cowed["effect2"]["apply_aura"], AURA_MOD_ROOT)
        self.assertEqual(cowed["effect3"]["apply_aura"], AURA_MOD_DAMAGE_PERCENT_TAKEN)
        self.assertEqual(cowed["effect3"]["base_points"], int(_header_value("kFetchCowedTakenPct")))
        for effect in ("effect1", "effect2", "effect3"):
            self.assertNotEqual(cowed[effect]["apply_aura"], 12)         # never MOD_STUN
        # A 1-body Soak; caught = cower, missed = every dog whipped.
        self.assertIn("Mechanic::Soak(me, BossMechanics::Anchor(spot), kFetchRadiusYd, 1,", self.code)
        self.assertIn("ai->FetchLanded(r.count >= 1,", self.code)
        self.assertIn("ai->Cower(kCowedMs);", self.code)
        self.assertIn("Frenzy(dog);", self.code)

    def test_the_whistle_is_one_look(self):
        whistle = self.spells[WHISTLE]
        self.assertEqual(whistle["effect1"]["type"], DUMMY_EFFECT)
        self.assertEqual(_raw(whistle, "SpellVisualID_1"), _visual("LK_WHISTLE"))
        self.assertEqual(_visual("LK_WHISTLE"), 8839)

    def test_no_wrong_look_is_wired(self):
        # The hits that borrow the bar's or the landing's look (the cone's and the tank's Correction, Cowed: a state the
        # dog's sit shows) carry none of their own.
        lookless = {CORRECTION_HIT, CORRECTION_TANK, COWED}
        for spell_id, spell in self.spells.items():
            self.assertNotIn(int(_raw(spell, "SpellVisualID_1")), WRONG_SPELL_VISUALS, spell_id)
            if spell_id not in lookless:
                self.assertNotEqual(int(_raw(spell, "SpellVisualID_1")), 0, f"{spell_id} has no look")
        # The dogs wear the stock hound's display, never the Rabbit-class traps of the other Library bosses.
        self.assertEqual(_visual("DISPLAY_TRACKING_HOUND"), STOCK_HOUND_DISPLAY)

    def test_the_arena_is_the_hall(self):
        # The pups come from the NAVMESH entries, not a guessed archway.
        self.assertIn("200.8f, -243.2f, 19.5f", _header())
        self.assertIn("180.8f, -306.2f, 18.8f", _header())
        for guid in STOCK_HOUND_GUIDS:
            self.assertIn(str(guid), _header() + SQL.read_text(encoding="utf-8"))

    def test_the_sql_rev(self):
        sql = SQL.read_text(encoding="utf-8")
        self.assertIn("DELETE FROM `creature` WHERE `id` = 4304 AND `guid` IN (40089, 40090, 40091);", sql)
        self.assertIn("DELETE FROM `creature_addon` WHERE `guid` IN (40089, 40090, 40091);", sql)
        # the four new emotes (type 41); group 0 is the stock yell and is not rewritten
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 3974 AND `GroupID` BETWEEN 1 AND 4;", sql)
        for group in (1, 2, 4):
            self.assertRegex(sql, rf"\({LOKSEY}, {group}, 0, '%s whistles: \w+!', 41,")
        self.assertRegex(sql, rf"\({LOKSEY}, 3, 0, '%s works himself into a frenzy!', 41,")
        self.assertNotIn(f"({LOKSEY}, 0, 0,", sql)
        # WP-S0's rev owns the SmartAI delete of 3974; nothing here inserts a spawn or SmartAI row (rule 14)
        self.assertNotIn("`smart_scripts`", sql)
        self.assertNotIn("INSERT INTO `creature` ", sql)
        # the other four stock 4304 spawns stay with the Beastmasters
        for guid in (40054, 40060, 40070, 40079):
            self.assertNotIn(str(guid), sql.replace("40054, 40060, 40070, 40079", ""))


def _pup_scale() -> float:
    text = VISUALS.read_text(encoding="utf-8")
    match = re.search(r"^PUP_SCALE\s*=\s*([\d.]+)", text, re.MULTILINE)
    assert match
    return float(match.group(1))


if __name__ == "__main__":
    unittest.main()
