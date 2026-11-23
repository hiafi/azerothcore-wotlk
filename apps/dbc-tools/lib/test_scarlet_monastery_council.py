"""
Scarlet Monastery build WP-D3, the council (Azshir the Sleepless and the Fallen Champion):
source/npcs/scarlet_monastery/council.py against its C++ (modules/mod-dungeon-bosses src/ScarletMonastery/
CouncilLogic.h, boss_azshir_fallen_champion_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in the slice (212390-212439) and CouncilLogic.h names the same ids; the credit spell stays the
    instance's (never cast here);
  - 6488 and 6490 are bound (SmartAI off, immunity 1972, no INSTANCE_BIND), the Champion a paladin, 24k and 18k at
    5 players;
  - Holy Light is the slice's one interruptible cast (Holy, 2.5 s); the bars Azshir must play are Physical and not
    interruptible; the registry's hits are resolve copies of the right school;
  - Execution Sentence is a heal absorb (aura 301) on every school (MiscValue 127, WP-HEAL), 8 s, not dispellable,
    bound to its AuraScript; the Holy Wrath burn is a DUMMY plus a 2 s pacify, never a stun; Grief is +20% damage
    done and attack speed a stack; the shield silences 2 s through its effect only; the Vigil is an 8 s channel
    nothing interrupts;
  - the SQL rev writes Azshir's texts 0-2 and the Champion's 0-3 and moves both spawns to the header's lawn spots.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scarlet_monastery_council.py
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
HEADER = MODULE_DIR / "CouncilLogic.h"
REWORK_HEADER = MODULE_DIR / "ScarletMonasteryRework.h"
SCRIPT = MODULE_DIR / "boss_azshir_fallen_champion_rework.cpp"
SQL_REV = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_council_scarlet_monastery.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "scarlet_monastery"

SLICE = range(212390, 212440)
CREDIT = 212300
(HOLY_SHOCK, HOLY_LIGHT, WRATH_CAST, WRATH, WRATH_BURN, EXORCISM_CAST, EXORCISM, JUDGEMENT, SEAL_COMMAND,
 COMMAND_CLEAVE, SEAL_RIGHTEOUSNESS, BRAND, BURST, SEAL_JUSTICE, MARK, HAMMER, SHIELD_CAST, SHIELD, SHIELD_BOUNCE,
 VIGIL, VIGIL_RING, VIGIL_RISE, GRIEF, EXECUTION, EXECUTION_BURST, EXECUTION_WAVE) = range(212390, 212416)
CHAMPION, AZSHIR = 6488, 6490
PALADIN_32_BASE = 888
CHAMPION_HEALTH_AT_5 = 24_000
AZSHIR_HEALTH_AT_5 = 18_000

SCHOOL_NORMAL, SCHOOL_HOLY = 1, 2
SCHOOL_DAMAGE, DUMMY, APPLY_AURA, HEAL_PCT = 2, 3, 6, 136
AURA_DUMMY, AURA_MOD_PACIFY, AURA_MOD_SILENCE = 4, 25, 27
AURA_MOD_DAMAGE_PERCENT_DONE, AURA_MOD_MELEE_HASTE, AURA_SCHOOL_HEAL_ABSORB = 79, 138, 301
MECHANIC_STUN, MECHANIC_SILENCE = 12, 9
ATTR0_NO_IMMUNITIES = 0x20000000
ATTR1_CHANNELED = 0x4
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
RESOLVE = "spell_boss_mechanics_resolve"
IMMUNITY_BOSS_STUN = 1972
INSTANCE_BIND = 0x1


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


def _raw(spell: dict, column: str) -> int:
    return int((spell.get("raw_overrides") or {}).get(column, 0) or 0)


def _header_int(name: str) -> int:
    match = re.search(rf"\b{name}\s*=\s*(-?\d+)", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return int(match.group(1))


def _header_pair(name: str) -> tuple[float, float]:
    match = re.search(rf"\b{name}\{{\s*(-?[\d.]+)f?,\s*(-?[\d.]+)f?\s*\}}", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return float(match.group(1)), float(match.group(2))


def _header_float(name: str) -> float:
    match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f?;", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return float(match.group(1))


class CouncilDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {}
        for e in reg.creature_template_edits:
            if int(e["entry"]) in (CHAMPION, AZSHIR):
                cls.edits.setdefault(int(e["entry"]), {}).update(e)
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.sql = SQL_REV.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(HOLY_SHOCK, EXECUTION_WAVE + 1)))
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery", {"spell": mine}), [])
        offsets = {int(v) for v in re.findall(r"SPELL_CV_\w+\s*=\s*kSpellSlice\.first \+ (\d+)", self.header)}
        self.assertEqual({HOLY_SHOCK + n for n in offsets}, set(mine))
        self.assertRegex(REWORK_HEADER.read_text(encoding="utf-8"), r"kSpellsCouncil\{ 212390, 212439 \}")
        # The credit is the instance's (OnUnitDeath, both dead): never declared or cast here.
        self.assertNotIn(CREDIT, self.spells)
        self.assertNotIn("kSpellCouncilCredit", self.cpp)
        self.assertNotIn("CreditEncounterBySpell", self.cpp)
        # The retired stock spells are never re-declared.
        for stock in (19642, 19644, 21949, 7399, 9373, 5137):
            self.assertNotIn(stock, self.spells)

    def test_the_two_units_are_bound_with_the_build_specs_health(self):
        for entry, script, health in ((CHAMPION, "boss_fallen_champion_rework", CHAMPION_HEALTH_AT_5),
                                      (AZSHIR, "boss_azshir_the_sleepless_rework", AZSHIR_HEALTH_AT_5)):
            edit = self.edits[entry]
            self.assertEqual(edit["ScriptName"], script)
            self.assertEqual(edit["AIName"], "")
            self.assertEqual(edit["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
            self.assertEqual(edit["flags_extra"] & INSTANCE_BIND, 0)     # the credit spell binds
            self.assertLessEqual(abs(math.ceil(PALADIN_32_BASE * edit["HealthModifier"]) - health), 30)
            self.assertIn(f"RegisterDungeonReworkCreatureAI({script}", self.cpp)
        self.assertEqual(self.edits[CHAMPION]["unit_class"], 2)         # warrior -> paladin (designer)

    def test_holy_light_is_the_one_interruptible_cast(self):
        light = self.spells[HOLY_LIGHT]
        self.assertEqual(light["school"], SCHOOL_HOLY)
        self.assertEqual(light["cast_time_ms"], _header_int("kHolyLightCastMs"))
        self.assertEqual(_raw(light, "InterruptFlags"), 15)
        self.assertEqual(_raw(light, "PreventionType"), 1)
        self.assertEqual(light["range_yards"], 40.0)
        effect = light["effect1"]
        self.assertEqual(effect["type"], HEAL_PCT)
        normal, heroic = _header_pair("kHolyLightHealPct")
        self.assertEqual(effect["base_points"] + 1, int(normal))
        self.assertEqual((normal, heroic), (10.0, 25.0))
        # Cast for real (the bar shows) with the difficulty's percent as the base point; on the interrupt list.
        self.assertIn("me->CastSpell(target, SPELL_CV_HOLY_LIGHT, args)", self.cpp)
        self.assertIn("d.interrupts.emplace_back(NPC_AZSHIR, SPELL_CV_HOLY_LIGHT, kHolyLightKickPriority(heroic),",
                      self.cpp)
        for spell_id, spell in self.spells.items():
            if spell_id != HOLY_LIGHT:
                self.assertEqual(_raw(spell, "InterruptFlags"), 0, spell_id)

    def test_the_bars_are_physical_and_not_interruptible(self):
        for spell_id, ms in ((WRATH_CAST, "kHolyWrathCastMs"), (EXORCISM_CAST, "kExorcismCastMs"),
                             (SHIELD_CAST, "kShieldCastMs")):
            bar = self.spells[spell_id]
            self.assertEqual(bar["cast_time_ms"], _header_int(ms), spell_id)
            self.assertEqual(_raw(bar, "PreventionType"), 0)
            # Rule 5: a kick on Holy Light (Holy) never locks a must-play bar.
            self.assertEqual(bar["school"], SCHOOL_NORMAL)
        self.assertIn("DungeonKit::CastBar(me, SPELL_CV_HOLY_WRATH_CAST)", self.cpp)
        self.assertIn("DungeonKit::CastBar(me, SPELL_CV_EXORCISM_CAST)", self.cpp)
        self.assertIn("DungeonKit::CastBar(me, SPELL_CV_AVENGERS_SHIELD_CAST)", self.cpp)

    def test_the_registry_hits_are_resolve_copies_of_the_right_school(self):
        expected = {WRATH: SCHOOL_HOLY, EXORCISM: SCHOOL_HOLY, COMMAND_CLEAVE: SCHOOL_NORMAL, BURST: SCHOOL_HOLY}
        for spell_id, school in expected.items():
            spell = self.spells[spell_id]
            self.assertEqual(spell["school"], school, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE)
        for name in ("SPELL_CV_HOLY_WRATH)", "SPELL_CV_EXORCISM)", "SPELL_CV_COMMAND_CLEAVE)",
                     "SPELL_CV_RIGHTEOUS_BURST)"):
            self.assertIn(f".Spell({name}", self.cpp)

    def test_the_script_hits_take_the_scripts_base_point(self):
        for spell_id in (HOLY_SHOCK, JUDGEMENT, HAMMER, SHIELD, SHIELD_BOUNCE, EXECUTION_BURST):
            spell = self.spells[spell_id]
            self.assertEqual(spell["school"], SCHOOL_HOLY, spell_id)
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE)
            self.assertTrue(spell["effect1"].get("_potency_excluded"), spell_id)
            self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS, spell_id)
            # No kit percent script would overwrite the base point.
            self.assertFalse([s for s in self.scripts if s[0] == spell_id], spell_id)

    def test_execution_sentence_absorbs_every_school(self):
        es = self.spells[EXECUTION]
        effect = es["effect1"]
        self.assertEqual(effect["type"], APPLY_AURA)
        self.assertEqual(effect["apply_aura"], AURA_SCHOOL_HEAL_ABSORB)
        self.assertEqual(effect["misc_value"], 127)        # WP-HEAL: or Nature heals pass through
        self.assertEqual(es["duration_ms"], _header_int("kExecutionMs"))
        self.assertEqual(es["dispel"], 0)
        self.assertTrue(es["attributes"] & ATTR0_NO_IMMUNITIES)
        self.assertIn((EXECUTION, "spell_sm_council_execution_sentence"), self.scripts)
        self.assertIn("RegisterSpellScript(spell_sm_council_execution_sentence)", self.cpp)
        self.assertIn("AURA_REMOVE_BY_ENEMY_SPELL", self.cpp)
        self.assertEqual(_header_float("kExecutionAbsorbPct"), 75.0)

    def test_the_holy_wrath_burn_pacifies_and_never_stuns(self):
        burn = self.spells[WRATH_BURN]
        self.assertEqual(burn["effect1"]["type"], DUMMY)
        self.assertEqual(burn["effect2"]["apply_aura"], AURA_MOD_PACIFY)
        self.assertEqual(burn["duration_ms"], _header_int("kPacifyMs"))
        self.assertEqual(burn["mechanic"], 0)
        for index in (1, 2):
            self.assertNotEqual(burn[f"effect{index}"].get("mechanic", 0), MECHANIC_STUN)
            self.assertNotEqual(burn[f"effect{index}"].get("apply_aura", 0), 12)     # MOD_STUN
        self.assertIn((WRATH_BURN, "spell_sm_council_holy_wrath_burn"), self.scripts)
        self.assertIn("RegisterSpellScript(spell_sm_council_holy_wrath_burn)", self.cpp)

    def test_grief_is_twenty_percent_damage_and_attack_speed_a_stack(self):
        grief = self.spells[GRIEF]
        pct = int(_header_float("kGriefPctPerStack"))
        self.assertEqual(grief["effect1"]["apply_aura"], AURA_MOD_DAMAGE_PERCENT_DONE)
        self.assertEqual(grief["effect1"]["misc_value"], 127)
        self.assertEqual(grief["effect1"]["base_points"], pct)
        self.assertEqual(grief["effect2"]["apply_aura"], AURA_MOD_MELEE_HASTE)
        self.assertEqual(grief["effect2"]["base_points"], pct)
        self.assertEqual(_raw(grief, "CumulativeAura"), 255)
        self.assertEqual(_header_pair("kGriefMaxStacks"), (5.0, 255.0))

    def test_the_shield_silences_through_its_effect_only(self):
        shield = self.spells[SHIELD]
        self.assertEqual(shield["mechanic"], 0)     # a silence-immune target still takes the hit
        self.assertEqual(shield["effect2"]["apply_aura"], AURA_MOD_SILENCE)
        self.assertEqual(shield["effect2"]["mechanic"], MECHANIC_SILENCE)
        self.assertEqual(shield["duration_ms"], _header_int("kShieldSilenceMs"))
        self.assertIsNone(self.spells[SHIELD_BOUNCE]["effect2"])

    def test_the_vigil_is_an_eight_second_channel_nothing_interrupts(self):
        vigil = self.spells[VIGIL]
        self.assertTrue(_raw(vigil, "AttributesEx") & ATTR1_CHANNELED)
        self.assertEqual(vigil["duration_ms"], _header_int("kVigilChannelMs"))
        self.assertEqual(vigil["duration_ms"], 8000)
        self.assertEqual(_raw(vigil, "ChannelInterruptFlags"), 0)
        self.assertEqual(_raw(vigil, "PreventionType"), 0)
        self.assertEqual(self.spells[VIGIL_RING]["duration_ms"], _header_int("kVigilChannelMs") + 1000)
        # Cast triggered (R-1-GY MN-5): a kicked Holy Light locks his Holy school, which refuses an untriggered cast;
        # a triggered channel with a duration still sets the channel bar (Spell::prepare).
        self.assertIn("me->CastSpell(me, SPELL_CV_LAST_VIGIL, true)", self.cpp)
        self.assertNotIn("me->CastSpell(me, SPELL_CV_LAST_VIGIL, false)", self.cpp)
        self.assertGreater(vigil["duration_ms"], 0)

    def test_the_markers_last_five_seconds(self):
        self.assertEqual(self.spells[BRAND]["duration_ms"], _header_int("kBrandMs"))
        self.assertEqual(self.spells[MARK]["duration_ms"], _header_int("kJusticeMarkMs"))
        for spell_id in (BRAND, MARK):
            self.assertEqual(self.spells[spell_id]["dispel"], 0)
            self.assertTrue(self.spells[spell_id]["attributes"] & ATTR0_NO_IMMUNITIES)

    def test_the_sql_rev_writes_the_texts_and_moves_both_spawns_to_the_lawn(self):
        for entry, groups in ((AZSHIR, {0: 14, 1: 14, 2: 41}), (CHAMPION, {0: 41, 1: 41, 2: 41, 3: 41})):
            for group, kind in groups.items():
                self.assertRegex(self.sql, rf"\({entry}, {group}, 0, '[^']+', {kind}, ")
        self.assertIn("'A hammer of light hangs over $n!'", self.sql)
        # The spots are the header's: the lawn disc (section 7 #18 A), Azshir 3 yd north (behind the Champion).
        lawn = re.search(r"kCouncilLawn\{ ([\d.]+)f, ([\d.]+)f, ([\d.]+)f \}",
                         REWORK_HEADER.read_text(encoding="utf-8"))
        self.assertTrue(lawn)
        x, y, z = (float(v) for v in lawn.groups())
        behind = _header_float("kAzshirBehindYd")
        for guid, entry, px in ((39894, CHAMPION, x), (1975841, AZSHIR, x + behind)):
            match = re.search(rf"`position_x` = ([\d.]+), `position_y` = ([\d.]+), `position_z` = ([\d.]+), "
                              rf"`orientation` = ([\d.]+),\s*`wander_distance` = 0, `MovementType` = 0 WHERE "
                              rf"`guid` = {guid} AND `id` = {entry};", self.sql)
            self.assertTrue(match, guid)
            self.assertAlmostEqual(float(match.group(1)), px, places=2)
            self.assertAlmostEqual(float(match.group(2)), y, places=2)
            self.assertAlmostEqual(float(match.group(3)), z, places=2)
            self.assertAlmostEqual(float(match.group(4)), math.pi, places=3)


if __name__ == "__main__":
    unittest.main()
