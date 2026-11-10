"""
Stratholme build WP-S1, The Unforgiven: source/npcs/stratholme/the_unforgiven.py against its C++
(modules/mod-dungeon-bosses src/Stratholme/UnforgivenLogic.h, boss_the_unforgiven_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in his slice (206420-206439), UnforgivenLogic.h names the same ids; his creatures are the Spectral
    Footman 300600 (not attackable, no heroic template) and the house fire stalker 300601 (an invisible trigger);
  - the March, the fire's landing and the burning patch are resolve copies in the right schools;
  - Grief, the Frost Nova copy and Haunting Memory carry the header's percents through the kit's percent spells;
    Freed is an exact amount; Grudge is +10% damage done per stack; Haunting Memory is an 8 s Magic DoT that also
    binds the expiry script;
  - auras that must not survive a map change carry CHANGE_MAP; the looks are V-2's UF_ picks;
  - 10516 is bound with SmartAI off, 185k, DamageModifier 3.7, immunity 1972; the phantom 10387 is 6,000 at level 57
    on the Spectral Citizen models;
  - the SQL rev gives him the six build spec lines (yells 14, the fire emote 41), drops the SmartAI rows of 10516 and
    10387, and arms the footman.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_stratholme_unforgiven.py
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
HEADER = MODULE_DIR / "UnforgivenLogic.h"
SCRIPT = MODULE_DIR / "boss_the_unforgiven_rework.cpp"
SQL_REV = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_the_unforgiven_stratholme.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "stratholme"

SLICE = range(206420, 206440)
(MARCH, HOUSE_FIRE, BURNING, FIRELIGHT, ACCUSED, ACCUSED_FLASH, GRIEF, GRUDGE, FREED, SOUL_FREED, BOUND, FROST_NOVA,
 HAUNTING, IN_FIRELIGHT) = range(206420, 206434)
FOOTMAN, FIRE_STALKER = 300600, 300601
BOSS, PHANTOM = 10516, 10387

SCHOOL_PHYSICAL, SCHOOL_HOLY, SCHOOL_FIRE, SCHOOL_FROST, SCHOOL_SHADOW = 1, 2, 4, 16, 32
SCHOOL_DAMAGE, APPLY_AURA = 2, 6
AURA_DUMMY, AURA_PERIODIC_DAMAGE, AURA_MOD_ROOT, AURA_MOD_DAMAGE_PERCENT_DONE = 4, 3, 26, 79
DISPEL_MAGIC = 1
ATTR0_AURA_IS_DEBUFF = 0x04000000
ATTR0_NO_IMMUNITIES = 0x20000000
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
AURA_INTERRUPT_CHANGE_MAP = 0x00080000
UNIT_FLAG_NON_ATTACKABLE = 0x2
UNIT_FLAG_NOT_SELECTABLE = 0x02000000
CREATURE_FLAG_EXTRA_TRIGGER = 0x80
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT = "spell_dungeon_refflat_damage"
REFFLAT_PERIODIC = "spell_dungeon_refflat_periodic"
EXPIRY = "spell_st_unforgiven_haunting_memory"

LOOKS = {
    MARCH: 4159,            # Ghostly Strike 14278
    HOUSE_FIRE: 6821,       # UF_BUILDING_FIRE
    BURNING: 6821,
    FIRELIGHT: 90507,       # SV_FLAMEZONE_10_STATE
    ACCUSED: 10201,         # UF_ACCUSED_ARROW
    ACCUSED_FLASH: 11826,   # UF_ACCUSED_FLASH
    GRIEF: 4209,            # Shadow Shock 16583
    SOUL_FREED: 4501,       # UF_SOUL_FREED
    BOUND: 335,             # UF_HAUNTING_PHANTOMS
    FROST_NOVA: 17,         # UF_FROST_NOVA
    HAUNTING: 335,
}


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


def _kickable(spell: dict) -> bool:
    """A kick or a silence stops it: InterruptFlags or ChannelInterruptFlags INTERRUPT (0x08), or PreventionType 1."""
    return bool(_raw(spell, "InterruptFlags") & 0x08 or _raw(spell, "ChannelInterruptFlags") & 0x08
                or _raw(spell, "PreventionType") == 1)


def _school_clash(spells: dict) -> list[tuple[int, int]]:
    """R-2-A A-3 (ORCH F-2 ruling): a kick locks the kicked cast's school, and a creature's untriggered cast in a
    locked school is refused. The (bar, kickable) pairs where a cast bar that must play (a cast time, not kickable)
    shares a school with one of the boss's kickable casts."""
    kickable = [s for s in spells.values() if _kickable(s)]
    bars = [s for s in spells.values() if int(s.get("cast_time_ms") or 0) > 0 and not _kickable(s)]
    return [(int(b["id"]), int(k["id"])) for b in bars for k in kickable if int(b["school"]) & int(k["school"])]


def _header() -> str:
    return HEADER.read_text(encoding="utf-8")


def _header_number(name: str) -> float:
    match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f?;", _header())
    assert match, name
    return float(match.group(1))


def _header_nh(name: str) -> tuple[float, float]:
    match = re.search(rf"\b{name}\{{\s*(-?[\d.]+)f?,\s*(-?[\d.]+)f?\s*\}}", _header())
    assert match, name
    return float(match.group(1)), float(match.group(2))


class UnforgivenDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates
                         if int(e["entry"]) in (FOOTMAN, FIRE_STALKER)}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) in (BOSS, PHANTOM)}
        cls.models = [m for m in reg.creature_template_models
                      if int(m["CreatureID"]) in (PHANTOM, FOOTMAN, FIRE_STALKER)]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_must_play_bars_never_share_a_kickable_school(self):
        self.assertEqual(_school_clash(self.spells), [])

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(MARCH, IN_FIRELIGHT + 1)))
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"spell": mine}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_UF_\w+\s*=\s*kSpellSlice\.first \+ (\d+)", _header())}
        self.assertEqual({MARCH + n for n in header_ids}, set(mine))
        # His stock kit is retired, never re-declared.
        for retired in (14907, 16331, 15089):
            self.assertNotIn(retired, self.spells)

    def test_his_creatures(self):
        self.assertEqual(sorted(self.creatures), [FOOTMAN, FIRE_STALKER])
        self.assertEqual(id_blocks.out_of_reservation("stratholme", {"creature": [FOOTMAN, FIRE_STALKER]}), [])
        footman = self.creatures[FOOTMAN]
        self.assertTrue(footman["unit_flags"] & UNIT_FLAG_NON_ATTACKABLE)
        self.assertFalse(footman["unit_flags"] & UNIT_FLAG_NOT_SELECTABLE)     # its name can be read
        self.assertEqual(footman["ScriptName"], "npc_st_spectral_footman")
        self.assertEqual(footman.get("difficulty_entry_1", 0), 0)       # handoff s7 #15: no heroic template
        self.assertEqual(footman["lootid"], 0)
        stalker = self.creatures[FIRE_STALKER]
        self.assertTrue(stalker["unit_flags"] & UNIT_FLAG_NOT_SELECTABLE)
        self.assertTrue(stalker["flags_extra"] & CREATURE_FLAG_EXTRA_TRIGGER)
        self.assertEqual(stalker.get("difficulty_entry_1", 0), 0)
        self.assertEqual(stalker["ScriptName"], "")
        displays = {(int(m["CreatureID"]), int(m["CreatureDisplayID"])) for m in self.models}
        self.assertIn((FOOTMAN, 30978), displays)
        self.assertEqual({d for e, d in displays if e == PHANTOM}, {10483, 10484, 10485, 10486})
        for script in ("npc_st_spectral_footman", "npc_st_vengeful_phantom", "boss_the_unforgiven_rework"):
            self.assertIn(f"RegisterDungeonReworkCreatureAI({script}", self.cpp)
        self.assertIn("RegisterSpellScript(spell_st_unforgiven_haunting_memory)", self.cpp)

    def test_registry_hits_are_resolve_copies(self):
        for spell_id, school in ((MARCH, SCHOOL_SHADOW), (HOUSE_FIRE, SCHOOL_FIRE), (BURNING, SCHOOL_FIRE)):
            hit = self.spells[spell_id]
            self.assertEqual(hit["school"], school, spell_id)
            self.assertEqual(hit["effect1"]["type"], SCHOOL_DAMAGE)
            self.assertTrue(_raw(hit, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
            self.assertIn((spell_id, RESOLVE), self.scripts)
        self.assertEqual(_header_nh("kMarchPct"), (40.0, 45.0))
        self.assertRegex(self.cpp, r"Spell\(SPELL_UF_MARCH_HIT\)\.Weakened\(\)")
        self.assertIn("Projectile(v).ProjectileUnit(leader)", self.cpp)
        self.assertIn("impact.spellId = SPELL_UF_HOUSE_FIRE;", self.cpp)
        self.assertIn("linger.spellId = SPELL_UF_BURNING_HOUSE;", self.cpp)
        self.assertIn("linger.slow = false;", self.cpp)

    def test_percent_spells_carry_the_header(self):
        grief = self.spells[GRIEF]
        self.assertEqual(grief["school"], SCHOOL_SHADOW)
        self.assertEqual(grief["effect1"]["base_points"] + 1, round(_header_number("kGriefPct") * 100))
        self.assertIn((GRIEF, REFFLAT), self.scripts)
        nova = self.spells[FROST_NOVA]
        self.assertEqual(nova["school"], SCHOOL_FROST)
        self.assertEqual(nova["dispel"], DISPEL_MAGIC)
        self.assertEqual(nova["effect1"]["base_points"] + 1, round(_header_number("kNovaPct") * 100))
        self.assertEqual(nova["effect1"]["radius_yards"], _header_number("kNovaRadius"))
        self.assertEqual(nova["effect2"]["apply_aura"], AURA_MOD_ROOT)
        self.assertEqual(nova["duration_ms"], int(_header_number("kNovaRootMs")))
        self.assertIn((FROST_NOVA, REFFLAT), self.scripts)
        haunting = self.spells[HAUNTING]
        self.assertEqual(haunting["dispel"], DISPEL_MAGIC)
        self.assertEqual(haunting["duration_ms"], int(_header_number("kHauntingMs")))
        self.assertEqual(haunting["effect1"]["apply_aura"], AURA_PERIODIC_DAMAGE)
        self.assertEqual(haunting["effect1"]["amplitude"], 1000)
        self.assertEqual(haunting["effect1"]["base_points"] + 1, round(_header_number("kHauntingPct") * 100))
        self.assertIn((HAUNTING, REFFLAT_PERIODIC), self.scripts)
        self.assertIn((HAUNTING, EXPIRY), self.scripts)
        for spell_id in (GRIEF, FROST_NOVA, HAUNTING, FREED):
            self.assertTrue(_raw(self.spells[spell_id], "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS, spell_id)

    def test_freed_grudge_and_auras(self):
        freed = self.spells[FREED]
        self.assertEqual(freed["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertEqual(freed["effect1"]["base_points"], 0)
        # R-2-A A-4: never cast (his damage-taken debuffs would scale it): the script takes the exact amount and logs
        # it under Freed.
        self.assertNotIn("SPELL_UF_FREED, SPELLVALUE_BASE_POINT0", self.cpp)
        self.assertIn("GetSpellInfo(SPELL_UF_FREED)", self.cpp)
        self.assertIn("me->ModifyHealth(-static_cast<int32>(tear))", self.cpp)
        grudge = self.spells[GRUDGE]
        self.assertEqual(grudge["effect1"]["apply_aura"], AURA_MOD_DAMAGE_PERCENT_DONE)
        self.assertEqual(grudge["effect1"]["base_points"], int(_header_number("kGrudgeDamagePct")))
        self.assertEqual(_raw(grudge, "CumulativeAura"), int(_header_number("kGrudgeMaxStacks")))
        self.assertEqual(grudge["duration_ms"], -1)
        self.assertFalse(grudge["attributes"] & ATTR0_AURA_IS_DEBUFF)
        accused = self.spells[ACCUSED]
        self.assertEqual(accused["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(accused["duration_ms"], -1)      # the AI removes it when its last phantom ends
        self.assertTrue(accused["attributes"] & ATTR0_NO_IMMUNITIES)
        for spell_id in (FIRELIGHT, IN_FIRELIGHT):
            self.assertEqual(self.spells[spell_id]["effect1"]["apply_aura"], AURA_DUMMY)
            self.assertEqual(self.spells[spell_id]["duration_ms"], -1)
        for spell_id in (ACCUSED, FROST_NOVA, HAUNTING):
            self.assertTrue(_raw(self.spells[spell_id], "AuraInterruptFlags") & AURA_INTERRUPT_CHANGE_MAP, spell_id)

    def test_looks_are_the_visual_picks(self):
        for spell_id, visual in LOOKS.items():
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), visual, spell_id)
        visuals = (PACKAGE / "_visuals.py").read_text(encoding="utf-8")
        for name, value in (("SV_FLAMEZONE_10_STATE", 90507), ("UF_ACCUSED_ARROW", 10201),
                            ("UF_ACCUSED_FLASH", 11826), ("UF_SOUL_FREED", 4501), ("UF_HAUNTING_PHANTOMS", 335),
                            ("UF_FROST_NOVA", 17), ("UF_BUILDING_FIRE", 6821), ("DISPLAY_SPECTRAL_FOOTMAN", 30978)):
            self.assertIsNotNone(re.search(rf"^{name}\s*=\s*{value}\b", visuals, re.M), name)

    def test_he_and_his_phantom_are_bound(self):
        boss = self.edits[BOSS]
        self.assertEqual(boss["ScriptName"], "boss_the_unforgiven_rework")
        self.assertEqual(boss["AIName"], "")
        self.assertEqual(boss["HealthModifier"], 66.451)
        self.assertEqual(boss["DamageModifier"], 3.7)
        self.assertEqual(boss["CreatureImmunitiesId"], 1972)
        self.assertEqual(boss["flags_extra"] & 0x1, 0x1)
        self.assertAlmostEqual(66.451 * 2784, 185_000, delta=100)
        phantom = self.edits[PHANTOM]
        self.assertEqual(phantom["ScriptName"], "npc_st_vengeful_phantom")
        self.assertEqual(phantom["AIName"], "")
        self.assertEqual((phantom["minlevel"], phantom["maxlevel"]), (57, 57))
        # ceil(2,784 x modifier) is the header's normal phantom health (the engine rounds up).
        self.assertEqual(math.ceil(2784 * phantom["HealthModifier"]), int(_header_nh("kPhantomHealth")[0]))

    def test_his_texts_and_stock_rows(self):
        text = SQL_REV.read_text(encoding="utf-8")
        rows = re.findall(r"^\(10516, (\d+), 0, '((?:[^'\\]|'')*)', (\d+),", text, re.M)
        self.assertEqual([int(r[0]) for r in rows], [0, 1, 2, 3, 4, 5])
        self.assertEqual({int(r[0]): int(r[2]) for r in rows}, {0: 14, 1: 14, 2: 14, 3: 41, 4: 14, 5: 14})
        header = (MODULE_DIR / "StratholmeRework.h").read_text(encoding="utf-8")
        for name, group in (("YELL_UNFORGIVEN_AGGRO", 0), ("YELL_UNFORGIVEN_MARCH", 1),
                            ("YELL_UNFORGIVEN_ACCUSED", 2), ("EMOTE_UNFORGIVEN_HOUSE_FIRE", 3),
                            ("YELL_UNFORGIVEN_LAST_SOUL", 4), ("YELL_UNFORGIVEN_DEATH", 5)):
            match = re.search(rf"{name}\s*=\s*(\d+)", header)
            self.assertIsNotNone(match, name)
            self.assertEqual(int(match.group(1)), group, name)
        self.assertIn("DELETE FROM `smart_scripts` WHERE `entryorguid` IN (10516, 10387) AND `source_type` = 0;", text)
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 10516;", text)
        self.assertIn("(300600, 1, 1899, 1984, 0, 0)", text)


if __name__ == "__main__":
    unittest.main()
