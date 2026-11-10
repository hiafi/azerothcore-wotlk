"""
Stratholme build WP-S12, Maleki the Pallid: source/npcs/stratholme/maleki_the_pallid.py against its C++
(modules/mod-dungeon-bosses src/Stratholme/MalekiLogic.h, boss_maleki_the_pallid_rework.cpp). R-1-B B-6 (the
Scholomance Krastinov precedent) and B-3 (the Siphon's marker).

Checks:
  - the spells sit in Maleki's slice (206665-206684) and MalekiLogic.h names the same ids;
  - the Ice Tomb 300584 (8,000 health, its heroic 310190, npc_st_ice_tomb) and the eye stalker 300585 (an invisible
    trigger, no heroic template), both in the `stratholme` creature reservation;
  - Icy Death 206665: Magic, 5 stacks, the per-stack tick and slow of MalekiLogic.h, its two script bindings, and a
    duration of -1 (R-1-BM: the bots' own self-cure never touches it only because its duration is above
    DispelAuraDuration);
  - the Siphon's drain and the tomb's drain carry MalekiLogic.h's percents for the kit's generic percent script
    (hundredths, heroic in MiscValueB);
  - the auras that could outlive the fight drop on a map change; the Siphon's cast, channel and the storm's bar last as
    long as MalekiLogic.h says;
  - the Siphon's marker 206681: a hidden DUMMY aura for kSiphonMarkMs; the Eye's hit leaves its bearer out by it and is
    registered once per Eye (B-3);
  - 10438 is bound to its rework script.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_stratholme_maleki.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Stratholme"
HEADER = MODULE_DIR / "MalekiLogic.h"
SCRIPT = MODULE_DIR / "boss_maleki_the_pallid_rework.cpp"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "stratholme"

SLICE = range(206665, 206685)
(ICY_DEATH, ICY_DEATH_LOOK, SHATTER, SHATTER_ROOT, SIPHON_CAST, SIPHON_CHANNEL, SIPHON_DRAIN, SIPHON_HEAL,
 TOMB_HOLD, TOMB_DRAIN, TOMB_HEAL, EYE_STORM, EYE_CHANNEL, EYE_STORM_LOOK, TOMB_LOOK, FROSTBITE_LOOK,
 SIPHON_MARK) = range(206665, 206682)
ICE_TOMB = 300584
ICE_TOMB_HEROIC = 310190
EYE = 300585
MALEKI = 10438

SCHOOL_DAMAGE, APPLY_AURA, HEAL = 2, 6, 10
AURA_DUMMY, AURA_PERIODIC_DAMAGE, AURA_MOD_DECREASE_SPEED, AURA_MOD_STUN = 4, 3, 33, 12
DISPEL_MAGIC = 1
ATTR0_DO_NOT_DISPLAY = 0x00000080
ATTR0_NO_IMMUNITIES = 0x20000000
ATTR0_AURA_IS_DEBUFF = 0x04000000
ATTR1_IS_CHANNELED = 0x00000004
AURA_INTERRUPT_CHANGE_MAP = 0x00080000
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
UNIT_FLAG_NOT_SELECTABLE = 0x02000000
CREATURE_FLAG_EXTRA_TRIGGER = 0x80
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT = "spell_dungeon_refflat_damage"
REFFLAT_PERIODIC = "spell_dungeon_refflat_periodic"
ICY_DEATH_SCRIPT = "spell_st_maleki_icy_death"
WARRIOR_60_BASE = 3052      # creature_classlevelstats level 60 class 1 basehp0


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


def _header() -> str:
    return HEADER.read_text(encoding="utf-8")


def _header_number(name: str) -> float:
    match = re.search(rf"{name}\s*=\s*(-?[\d.]+)f?;", _header())
    assert match, name
    return float(match.group(1))


def _header_nh(name: str) -> tuple[float, float]:
    match = re.search(rf"{name}\{{\s*(-?[\d.]+)f?,\s*(-?[\d.]+)f?\s*\}}", _header())
    assert match, name
    return float(match.group(1)), float(match.group(2))


class MalekiDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) in (ICE_TOMB, EYE)}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) == MALEKI}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(ICY_DEATH, SIPHON_MARK + 1)))
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"spell": mine}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_MK_\w+\s*=\s*(\d+)", _header())}
        self.assertEqual(header_ids, set(mine))

    def test_the_tomb_and_the_eye_stalker(self):
        self.assertEqual(sorted(self.creatures), [ICE_TOMB, EYE])
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"creature": [ICE_TOMB, EYE]}), [])
        tomb = self.creatures[ICE_TOMB]
        self.assertEqual(tomb["ScriptName"], "npc_st_ice_tomb")
        self.assertEqual(tomb["difficulty_entry_1"], ICE_TOMB_HEROIC)
        normal, _ = _header_nh("kTombHealth")
        self.assertEqual(math.ceil(WARRIOR_60_BASE * tomb["HealthModifier"]), int(normal))
        self.assertEqual(tomb["lootid"], 0)
        eye = self.creatures[EYE]
        self.assertTrue(eye["unit_flags"] & UNIT_FLAG_NOT_SELECTABLE)
        self.assertTrue(eye["flags_extra"] & CREATURE_FLAG_EXTRA_TRIGGER)
        self.assertEqual(eye.get("difficulty_entry_1", 0), 0)
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_st_ice_tomb", self.cpp)

    def test_icy_death(self):
        curse = self.spells[ICY_DEATH]
        # R-1-BM: a bot's own self-cure skips DispelEntry::when; it never touches Icy Death only because its duration
        # (-1, the fight) is above the bots' DispelAuraDuration. A finite duration would let bots shatter themselves.
        self.assertEqual(curse["duration_ms"], -1)
        self.assertEqual(curse["dispel"], DISPEL_MAGIC)
        self.assertEqual(_raw(curse, "CumulativeAura"), int(_header_number("kCurseMaxStacks")))
        tick = curse["effect1"]
        self.assertEqual(tick["apply_aura"], AURA_PERIODIC_DAMAGE)
        self.assertEqual(tick["amplitude"], int(_header_number("kCurseTickMs")))
        self.assertEqual(tick["base_points"] + 1, round(_header_number("kCurseTickPct") * 100))
        slow = curse["effect2"]
        self.assertEqual(slow["apply_aura"], AURA_MOD_DECREASE_SPEED)
        self.assertEqual(-(slow["base_points"] + 1), int(_header_number("kCurseSlowPct")))
        self.assertIn((ICY_DEATH, REFFLAT_PERIODIC), self.scripts)
        self.assertIn((ICY_DEATH, ICY_DEATH_SCRIPT), self.scripts)
        self.assertIn(f"RegisterSpellScript({ICY_DEATH_SCRIPT})", self.cpp)

    def test_the_drains_carry_the_percents(self):
        for spell_id, name in ((SIPHON_DRAIN, "kSiphonDrainPct"), (TOMB_DRAIN, "kTombDrainPct")):
            spell = self.spells[spell_id]
            normal, heroic = _header_nh(name)
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertEqual(spell["effect1"]["base_points"] + 1, round(normal * 100), spell_id)
            self.assertEqual(_raw(spell, "EffectMiscValueB_1"), round(heroic * 100), spell_id)
            self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS, spell_id)
            self.assertIn((spell_id, REFFLAT), self.scripts)
        for spell_id in (SIPHON_HEAL, TOMB_HEAL):
            self.assertEqual(self.spells[spell_id]["effect1"]["type"], HEAL)

    def test_spell_scripts_are_bound(self):
        for spell_id in (SHATTER, EYE_STORM):
            self.assertIn((spell_id, RESOLVE), self.scripts)
        own = {name for _, name in self.scripts if name not in (RESOLVE, REFFLAT, REFFLAT_PERIODIC)}
        self.assertEqual(own, {ICY_DEATH_SCRIPT})

    def test_timings_and_map_changes(self):
        self.assertEqual(self.spells[SIPHON_CAST]["cast_time_ms"], int(_header_number("kSiphonCastMs")))
        channel = self.spells[SIPHON_CHANNEL]
        self.assertEqual(channel["duration_ms"], int(_header_number("kSiphonChannelMs")))
        self.assertTrue(_raw(channel, "AttributesEx") & ATTR1_IS_CHANNELED)
        self.assertEqual(self.spells[EYE_CHANNEL]["duration_ms"], int(_header_number("kEyeStormMs")))
        hold = self.spells[TOMB_HOLD]
        self.assertEqual(hold["effect1"]["apply_aura"], AURA_MOD_STUN)
        self.assertEqual(hold["duration_ms"], int(_header_number("kTombMaxMs")))
        for spell_id in (ICY_DEATH, SIPHON_CHANNEL, TOMB_HOLD, SIPHON_MARK):
            self.assertTrue(_raw(self.spells[spell_id], "AuraInterruptFlags") & AURA_INTERRUPT_CHANGE_MAP, spell_id)

    def test_the_siphon_marker(self):
        mark = self.spells[SIPHON_MARK]
        self.assertEqual(mark["effect1"]["type"], APPLY_AURA)
        self.assertEqual(mark["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertTrue(mark["attributes"] & ATTR0_DO_NOT_DISPLAY)
        self.assertTrue(mark["attributes"] & ATTR0_AURA_IS_DEBUFF)
        self.assertTrue(mark["attributes"] & ATTR0_NO_IMMUNITIES)
        self.assertEqual(mark["dispel"], 0)
        cast, channel = _header_number("kSiphonCastMs"), _header_number("kSiphonChannelMs")
        self.assertEqual(mark["duration_ms"], int(cast + channel + 1000))
        self.assertRegex(_header(), r"kSiphonMarkMs = kSiphonCastMs \+ kSiphonChannelMs \+ 1000;")
        # B-3: the Eye's hit leaves the marker's bearer out by a live aura check and is registered once per Eye (one
        # call site, in StartEye), never again when a Siphon starts or ends mid-storm.
        self.assertRegex(self.cpp, r"notCarrying\.auraSpell = SPELL_MK_SIPHON_MARK;\s*notCarrying\.maxStacks = 0;")
        self.assertEqual(len(re.findall(r"\bRegisterEyeHit\(\);", self.cpp)), 1)
        self.assertIn("CastSpell(carrier, SPELL_MK_SIPHON_MARK, true)", self.cpp)

    def test_maleki_is_bound(self):
        self.assertEqual(self.edits[MALEKI]["ScriptName"], "boss_maleki_the_pallid_rework")
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_maleki_the_pallid_rework", self.cpp)


if __name__ == "__main__":
    unittest.main()
