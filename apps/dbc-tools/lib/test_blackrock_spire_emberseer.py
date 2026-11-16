"""
Blackrock Spire build WP-B10, Pyroguard Emberseer: source/npcs/blackrock_spire/emberseer.py against its C++
(modules/mod-dungeon-bosses src/BlackrockSpire/EmberseerLogic.h, boss_pyroguard_emberseer_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in Emberseer's slice (210350-210389) and EmberseerLogic.h names the same ids;
  - Emberseer 9816 is bound (SmartAI off) at 175k on the level 60 warrior base, the stock DamageModifier, immunity set
    1973, INSTANCE_BIND; the Incarcerators 10316 are rebound to the C++ AI; the Binding Post 300730 sits in the
    reservation, is a helper with no heroic template;
  - the growth auras are +3% / +4% damage done a stack up to 20; the hits are resolve copies or the stacked-hit /
    percent spells of the right school and percent; Pyroblast is a 6 s interruptible Fire cast with the stock missile
    and a 12 s burn; Seared lasts 40 s; the beam is a 2 s channel; the looks are V-2's EM_* ids;
  - the SQL rev writes the four new lines (4-7) and the immunity set 1973 (the 1972 mechanics set plus the Fire
    school), and touches nothing else; every immunity set a Blackrock Spire row names (the boss package and the heroic
    overrides) exists in the base dump or an update (R-2-A M-1: 1973 was named but shipped nowhere).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_spire_emberseer.py
"""

from __future__ import annotations

import math
import re
import subprocess
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import test_id_blocks as id_blocks  # noqa: E402
from lib.dsl import registry  # noqa: E402
from source.npcs.blackrock_spire import _visuals as V  # noqa: E402

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockSpire"
HEADER = MODULE_DIR / "EmberseerLogic.h"
REWORK = MODULE_DIR / "BlackrockSpireRework.h"
SCRIPT = MODULE_DIR / "boss_pyroguard_emberseer_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_pyroguard_emberseer_blackrock_spire.sql"
SQL_DIRS = [REPO_ROOT / "data" / "sql" / "base" / "db_world", REPO_ROOT / "data" / "sql" / "updates" / "db_world",
            REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world"]
HEROIC = TOOL_ROOT / "source" / "world" / "dungeons" / "blackrock_spire.py"
IMMUNITY_1972_MECHANICS = 1217821862    # rev_1793964948691162910.sql's "-229 + STUN"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_spire"

SLICE = range(210350, 210390)
(GROWTH, GROWTH_H, HEAT, NOVA, RING, BODY_FLARE, RING_LAUNCH, FIRE_NOVA, FULL_STRENGTH, SUPERNOVA, PYROBLAST, SMOLDER,
 COLUMN, BEAM, SEARING_BOND, SEARED, UNSTABLE, SEARING_STATE) = range(210350, 210368)
EMBERSEER = 9816
INCARCERATOR = 10316
POST = 300730

SCHOOL_FIRE, SCHOOL_PHYSICAL = 4, 1
SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT = 2, 6, 3
AURA_DUMMY, AURA_PERIODIC_DAMAGE, AURA_MOD_DAMAGE_PERCENT_DONE = 4, 3, 79
AURA_INTERRUPT_CHANGE_MAP = 0x00080000
RESOLVE = "spell_boss_mechanics_resolve"
REFLAT_DAMAGE = "spell_dungeon_refflat_damage"
REFLAT_PERIODIC = "spell_dungeon_refflat_periodic"
STACKED = "spell_brs_emberseer_stacked_hit"
WARRIOR_60_BASE = 3052      # creature_classlevelstats level 60 class 1 basehp0
ATTR0_PASSIVE = 0x00000040
ATTR0_DO_NOT_DISPLAY = 0x00000080
ATTR1_IS_CHANNELED = 0x00000004
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000


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


def _header_nh(name: str) -> tuple[float, float]:
    match = re.search(rf"\b{name}\{{\s*(-?[\d.]+)f?,\s*(-?[\d.]+)f?\s*\}};", _header())
    assert match, name
    return float(match.group(1)), float(match.group(2))


class EmberseerDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits
                     if int(e["entry"]) in (EMBERSEER, INCARCERATOR)}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == POST}
        cls.models = [e for e in reg.creature_template_models if int(e["CreatureID"]) == POST]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(GROWTH, SEARING_STATE + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_spire", {"spell": mine}), [])
        found = re.search(r"kSpellsEmberseer\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertIsNotNone(found)
        self.assertEqual((int(found.group(1)), int(found.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_EM_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual({SLICE.start + int(o) for o in offsets}, set(mine))

    def test_emberseer_and_the_incarcerators_are_bound(self):
        boss = self.edits[EMBERSEER]
        self.assertEqual(boss["ScriptName"], "boss_pyroguard_emberseer_rework")
        self.assertEqual(boss["AIName"], "")
        self.assertLessEqual(abs(math.ceil(WARRIOR_60_BASE * boss["HealthModifier"]) - 175000), 2)
        self.assertAlmostEqual(float(boss["DamageModifier"]), 3.5)     # stock, not the live 6
        self.assertEqual(boss["CreatureImmunitiesId"], 1973)
        self.assertEqual(boss["flags_extra"], 1)
        incarcerator = self.edits[INCARCERATOR]
        self.assertEqual(incarcerator["ScriptName"], "npc_blackhand_incarcerator_rework")
        self.assertEqual(incarcerator["AIName"], "")
        self.assertNotIn("HealthModifier", incarcerator)        # stock 7,500 (heroic 9,500 is WP-H's)
        for name in ("boss_pyroguard_emberseer_rework", "npc_blackhand_incarcerator_rework", "npc_brs_binding_post"):
            self.assertIn(f"RegisterDungeonReworkCreatureAI({name},", self.cpp)
        # The boss and the Incarcerators bind with wave 2 only.
        for name in ("boss_pyroguard_emberseer_rework", "npc_blackhand_incarcerator_rework"):
            self.assertRegex(self.cpp, rf"if \(kWave2Bound\)\s*RegisterDungeonReworkCreatureAI\({name},")
        self.assertIn("RegisterSpellScript(spell_brs_emberseer_stacked_hit)", self.cpp)
        self.assertIn('BrsTest::RegisterBoss("emberseer"', self.cpp)

    def test_the_r2_fixes_in_the_cpp(self):
        # m-3: a landed Pyroblast feeds him (the script's hit), not the completed cast (n-3: no OnSpellCast override).
        self.assertIn("OnEffectHitTarget += SpellEffectFn(spell_brs_emberseer_stacked_hit::Feed", self.cpp)
        self.assertNotIn("void OnSpellCast(", self.cpp)
        # m-2: the altar respawns the dead Incarcerators itself (the pending recage is dropped by Cleanup).
        start_cage = self.cpp[self.cpp.index("void StartCage()"):self.cpp.index("void UpdateCage(")]
        self.assertIn("RespawnIncarcerators()", start_cage)
        # m-1: the search covers the hall's corners (42 yd from him).
        self.assertGreaterEqual(_header_value("kIncarceratorFindYd"), 42.0)
        # n-2: the post eligibility is never "everyone" when nobody but his target is in the fight.
        self.assertIn("who.carriers.insert(me->GetGUID());", self.cpp)

    def test_the_binding_post(self):
        self.assertEqual(id_blocks.out_of_reservation("blackrock_spire", {"creature": [POST]}), [])
        post = self.creatures[POST]
        self.assertEqual(post["ScriptName"], "npc_brs_binding_post")
        self.assertEqual(post["AIName"], "")
        # A prop: untargetable, unattackable, no loot, no XP, no melee, and no heroic template (handoff s7 #23).
        self.assertEqual(post["unit_flags"], 0x2 | 0x02000000)
        self.assertEqual(post["DamageModifier"], 0.0)
        self.assertEqual(post["lootid"], 0)
        self.assertEqual(post["flags_extra"], 0x40)
        self.assertEqual(post["difficulty_entry_1"], 0)
        self.assertEqual([m["CreatureDisplayID"] for m in self.models], [V.DISPLAY_INVISIBLE_STALKER])
        self.assertRegex(REWORK.read_text(encoding="utf-8"), rf"NPC_BRS_BINDING_POST\s*=\s*{POST},")

    def test_the_growth(self):
        normal, heroic = _header_nh("kStackDamagePct")
        for spell_id, pct in ((GROWTH, normal), (GROWTH_H, heroic)):
            spell = self.spells[spell_id]
            effect = spell["effect1"]
            self.assertEqual(effect["apply_aura"], AURA_MOD_DAMAGE_PERCENT_DONE, spell_id)
            self.assertEqual(effect["base_points"], int(pct), spell_id)
            self.assertEqual(effect["misc_value"], 127, spell_id)
            self.assertEqual(spell["duration_ms"], -1, spell_id)
            self.assertEqual(_raw(spell, "CumulativeAura"), int(_header_value("kFullStrengthStacks")), spell_id)
            self.assertFalse(spell["attributes"] & ATTR0_PASSIVE, spell_id)
        self.assertEqual((normal, heroic), (3.0, 4.0))

    def test_the_hits(self):
        # The registry hits: resolve copies, Fire.
        for spell_id, visual in ((NOVA, V.VG_FIRE_BLAST_IMPACT), (RING, V.VG_FIRE_BLAST_IMPACT),
                                 (SUPERNOVA, V.EM_FIRE_NOVA), (UNSTABLE, V.VG_FIRE_BLAST_IMPACT)):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertEqual(spell["school"], SCHOOL_FIRE, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
            self.assertEqual(_raw(spell, "SpellVisualID_1"), visual, spell_id)
        # Furnace Heat: the stacked hit (the script reads his stacks), ignores caster modifiers.
        heat = self.spells[HEAT]
        self.assertEqual(heat["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertIn((HEAT, STACKED), self.scripts)
        self.assertTrue(_raw(heat, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        # Searing Bond: the kit's percent spell, 4% in hundredths (shown and heroic).
        bond = self.spells[SEARING_BOND]
        hundredths = int(_header_value("kSearingBondPct") * 100)
        self.assertEqual(bond["effect1"]["base_points"] + bond["effect1"]["die_sides"], hundredths)
        self.assertEqual(_raw(bond, "EffectMiscValueB_1"), hundredths)
        self.assertIn((SEARING_BOND, REFLAT_DAMAGE), self.scripts)
        self.assertEqual(_raw(bond, "SpellVisualID_1"), V.EM_SEARING_BOND_ALT)
        # The cpp passes the header's percents through HitPct, never a literal.
        self.assertIn("HitPct(SPELL_EM_RING, _stacks, _heroic)", self.cpp)
        self.assertIn("HitPct(SPELL_EM_NOVA, _stacks, _heroic)", self.cpp)
        self.assertIn("HitPct(SPELL_EM_SUPERNOVA, _stacks, _heroic)", self.cpp)

    def test_pyroblast(self):
        spell = self.spells[PYROBLAST]
        self.assertEqual(spell["cast_time_ms"], int(_header_value("kPyroblastCastMs")))
        self.assertEqual(spell["cast_time_ms"], 6000)
        self.assertEqual(spell["school"], SCHOOL_FIRE)
        # Interruptible and silence-preventable: the expected interrupt.
        self.assertEqual(_raw(spell, "InterruptFlags"), 15)
        self.assertEqual(_raw(spell, "PreventionType"), 1)
        self.assertEqual(_raw(spell, "SpellVisualID_1"), V.EM_PYROBLAST)
        self.assertEqual(_raw(spell, "Speed"), 24.0)
        self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertEqual(spell["effect2"]["apply_aura"], AURA_PERIODIC_DAMAGE)
        self.assertEqual(spell["effect2"]["amplitude"], 3000)
        burn = int(_header_value("kPyroblastBurnPct") * 100)
        self.assertEqual(spell["effect2"]["base_points"], burn)
        self.assertEqual(_raw(spell, "EffectMiscValueB_2"), burn)
        self.assertEqual(spell["duration_ms"], int(_header_value("kPyroblastBurnMs")))
        self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertEqual(_raw(spell, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)
        self.assertIn((PYROBLAST, STACKED), self.scripts)
        self.assertIn((PYROBLAST, REFLAT_PERIODIC), self.scripts)
        self.assertRegex(_header(), r"kPyroblastPct\{\s*40\.f,\s*50\.f\s*\}")

    def test_the_post_spells(self):
        seared = self.spells[SEARED]
        self.assertEqual(seared["duration_ms"], int(_header_value("kSearedMs")))
        self.assertEqual(seared["duration_ms"], 40000)
        self.assertEqual(seared["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(_raw(seared, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)
        self.assertEqual(_raw(seared, "SpellVisualID_1"), V.EM_SEARED)
        beam = self.spells[BEAM]
        self.assertEqual(beam["duration_ms"], int(_header_value("kPostBeamMs")))
        self.assertTrue(_raw(beam, "AttributesEx") & ATTR1_IS_CHANNELED)
        self.assertEqual(beam["school"], SCHOOL_PHYSICAL)       # his Fire immunity must not refuse it
        self.assertEqual(_raw(beam, "SpellVisualID_1"), V.EM_ENCAGE)
        smolder = self.spells[SMOLDER]
        self.assertEqual(smolder["duration_ms"], -1)
        self.assertFalse(smolder["attributes"] & ATTR0_PASSIVE)
        self.assertTrue(smolder["attributes"] & ATTR0_DO_NOT_DISPLAY)
        self.assertEqual(_raw(smolder, "SpellVisualID_1"), V.EM_SMOLDER)
        state = self.spells[SEARING_STATE]
        self.assertEqual(_raw(state, "SpellVisualID_1"), V.EM_SEARING_BOND)
        self.assertEqual(_raw(state, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)

    def test_the_looks(self):
        for spell_id, visual in ((BODY_FLARE, V.EM_GROWING), (RING_LAUNCH, V.EM_RING_LAUNCH),
                                 (FIRE_NOVA, V.EM_FIRE_NOVA), (FULL_STRENGTH, V.EM_SUPERNOVA),
                                 (COLUMN, V.EM_FLARE_COLUMN)):
            spell = self.spells[spell_id]
            self.assertEqual(spell["effect1"]["type"], DUMMY_EFFECT, spell_id)
            self.assertEqual(_raw(spell, "SpellVisualID_1"), visual, spell_id)

    def test_the_cpp_uses_the_declared_names(self):
        for name in re.findall(r"(SPELL_EM_\w+)\s*=\s*kSpellSlice", _header()):
            self.assertIn(name, self.cpp, name)
        self.assertNotIn("\t", self.cpp)


def _shipped_immunity_ids() -> set[int]:
    """Every creature_immunities ID an INSERT in the base dump, the applied updates or a pending rev writes."""
    found = subprocess.run(["grep", "-rl", "--include=*.sql", "creature_immunities", *map(str, SQL_DIRS)],
                           capture_output=True, text=True, check=False).stdout.split()
    ids: set[int] = set()
    for path in found:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
        for block in re.findall(r"INSERT INTO `creature_immunities`[^;]*;", text):
            ids.update(int(i) for i in re.findall(r"(?:VALUES|\),)\s*\(\s*(-?\d+)\s*,", block))
    return ids


class EmberseerImmunityTest(unittest.TestCase):
    def test_every_immunity_set_the_rows_name_is_shipped(self):
        reg = _load()
        named = {int(e["CreatureImmunitiesId"]) for e in [*reg.creature_template_edits, *reg.creature_templates]
                 if e.get("CreatureImmunitiesId")}
        named |= {int(i) for i in re.findall(r'"CreatureImmunitiesId":\s*(\d+)', HEROIC.read_text(encoding="utf-8"))}
        self.assertIn(1973, named)
        shipped = _shipped_immunity_ids()
        self.assertIn(1971, shipped)        # the parse finds the base dump's rows
        self.assertEqual(sorted(named - shipped), [])


class EmberseerSqlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8")

    def test_the_immunity_set(self):
        # The 1972 mechanics plus the Fire school; deleted first (re-runnable), the one 1973 row anywhere.
        self.assertIn("DELETE FROM `creature_immunities` WHERE `ID` = 1973;", self.sql)
        self.assertRegex(self.sql, rf"\(1973, 4, 0, {IMMUNITY_1972_MECHANICS}, '', '', 0, 0, '[^']+'\);")
        self.assertIn(1972, _shipped_immunity_ids())

    def test_the_texts(self):
        for group, kind in ((4, 41), (5, 16), (6, 41), (7, 41)):
            self.assertRegex(self.sql, rf"\({EMBERSEER}, {group}, 0, '[^\n]*', {kind}, 0, 100, ", group)
        self.assertRegex(self.sql, rf"\({EMBERSEER}, 4, 0, 'The binding posts begin to smolder!'")
        self.assertRegex(self.sql, rf"\({EMBERSEER}, 5, 0, '%s draws the flames into itself!'")
        self.assertRegex(self.sql, rf"\({EMBERSEER}, 6, 0, '%s burns at full strength!'")
        self.assertRegex(self.sql, rf"\({EMBERSEER}, 7, 0, 'Unstable posts crackle with fire!'")
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 9816 AND `GroupID` BETWEEN 4 AND 7;", self.sql)
        groups = dict(re.findall(r"TEXT_(\w+)\s*=\s*(\d+),", _header()))
        self.assertEqual(sorted(int(v) for v in groups.values()), list(range(8)))

    def test_the_rev_leaves_the_stock_rows_alone(self):
        # Stock lines 0-3 and the Incarcerators' line stay; no SmartAI, loot or spawn rows.
        self.assertNotRegex(self.sql, r"GroupID` (BETWEEN 0|= [0-3]\b)")
        self.assertNotIn("10316", self.sql.split("-- His new lines")[1])
        self.assertNotIn("smart_scripts", self.sql)
        self.assertNotIn("creature_loot_template", self.sql)
        self.assertNotIn("UPDATE `creature`", self.sql)


if __name__ == "__main__":
    unittest.main()
