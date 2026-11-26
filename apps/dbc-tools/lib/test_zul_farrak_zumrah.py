"""
Zul'Farrak build WP-D3, Witch Doctor Zum'rah: source/npcs/zul_farrak/zumrah.py against its C++
(modules/mod-dungeon-bosses src/ZulFarrak/ZumrahLogic.h, boss_zumrah_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in his slice (213920-213959) and ZumrahLogic.h names the same ids;
  - Zum'rah 7271 is bound at 176,065 on the level 46 paladin base (the header's Health); the Skeleton 7786 gets its
    script; the four adds 301010-301013 are declared, scripted and shown as the C++ registers them;
  - the Volley and the Bolt are the only kickable casts (Shadow) and Spirit Rend is Arcane and never interruptible
    (rule 24);
  - the walker's aura detects what the souls, the Bound Dead and the grave looks hide (type 11), the times and
    percents are the header's; every damage spell ignores caster modifiers, redirection and reflection (rule 2,
    LESSONS L7) and takes the script's base point or is a resolve copy;
  - the looks are V's (the two stock projectile looks pending V);
  - the C++ registers the spec: NoAssist before UpdateVictim, the walker-only circles seen only with type 11, the
    souls through the kit's walker switch, the Bound Dead's Soaks on two Gathered Souls, cleanup;
  - the SQL rev writes the two emotes (type 41) and touches nothing else.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_zul_farrak_zumrah.py
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
HEADER = MODULE_DIR / "ZumrahLogic.h"
REWORK = MODULE_DIR / "ZulFarrakRework.h"
SCRIPT = MODULE_DIR / "boss_zumrah_rework.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_zumrah_zul_farrak.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "zul_farrak"

SLICE = range(213920, 213960)
(REND, BETWEEN_WORLDS, EMPTY_VESSEL, TETHER, SPIRIT_WORLD, LOST_SOUL, BOUND, FREED, GATHERED, WARD, VOLLEY,
 VOLLEY_HEROIC, VOLLEY_HIT, BOLT, STRIKE, SOUL_BURN, ECHO, WAIL, GRAVES, ERUPTION) = range(213920, 213940)
ZUMRAH, SKELETON = 7271, 7786
VESSEL, SOUL, BOUND_DEAD, STALKER = 301010, 301011, 301012, 301013
PALADIN_46_BASE = 1535      # creature_classlevelstats level 46 class 2 basehp0

SCHOOL_SHADOW, SCHOOL_ARCANE = 32, 64
SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT = 2, 6, 3
AURA_DUMMY, AURA_INVISIBILITY, AURA_INVISIBILITY_DETECT, AURA_SPEED, AURA_DAMAGE_TAKEN, AURA_CLONE = 4, 18, 19, 31, \
    87, 247
PREVENTION_SILENCE = 1
ATTR0_AURA_IS_DEBUFF = 0x04000000
ATTR1_NO_REDIRECTION, ATTR1_NO_REFLECTION, ATTR1_IS_CHANNELED = 0x8, 0x80, 0x4
ATTR2_IGNORE_LOS = 0x4
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
CHANGE_MAP = 0x00080000
RESOLVE = "spell_boss_mechanics_resolve"
# V's picks (_visuals.py) and the two stock projectile looks of the copies.
SV_REND, SV_GHOST, SV_TETHER, SV_SOUL, SV_GATHERED, SV_BIND, SV_FREED, SV_WARD, SV_WAIL, SV_GRAVE = (
    7964, 886, 8283, 7566, 5101, 7181, 7180, 7519, 14508, 634)
SV_BOLT, SV_VOLLEY = 64, 2318
CDI_SOUL, CDI_BOUND, CDI_STALKER = 12432, 29716, 11686
STOCK_CASTS = (12739, 15245, 12491)     # copied or retired: never cast by the script


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


def _value(name: str) -> float:
    match = re.search(rf"\b{name} = (-?[\d.]+)f?;", _header())
    assert match, name
    return float(match.group(1))


def _pair(name: str) -> tuple[float, float]:
    match = re.search(rf"\b{name}\{{ (-?[\d.]+)f?, (-?[\d.]+)f? \}};", _header())
    assert match, name
    return float(match.group(1)), float(match.group(2))


def _code(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith(("//", "*", "/*")))


def _effects(spell: dict) -> list[dict]:
    return [spell.get(f"effect{i}") or {} for i in (1, 2, 3)]


class ZumrahDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) in (ZUMRAH, SKELETON)}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates
                         if int(e["entry"]) in (VESSEL, SOUL, BOUND_DEAD, STALKER)}
        cls.models = {int(e["CreatureID"]): e for e in reg.creature_template_models
                      if int(e["CreatureID"]) in (VESSEL, SOUL, BOUND_DEAD, STALKER)}
        cls.cpp = SCRIPT.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(REND, ERUPTION + 1)))
        self.assertEqual(id_blocks.out_of_reservation("zul_farrak", {"spell": mine}), [])
        first = re.search(r"kSpellsZumrah\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertEqual((int(first.group(1)), int(first.group(2))), (SLICE.start, SLICE.stop - 1))
        offsets = re.findall(r"SPELL_ZR_\w+\s*=\s*kSpellSlice\.first \+ (\d+),", _header())
        self.assertEqual([SLICE.start + int(o) for o in offsets], mine)

    def test_zumrah_and_the_skeleton_are_bound(self):
        boss = self.edits[ZUMRAH]
        self.assertEqual(boss["ScriptName"], "boss_zumrah_rework")
        self.assertEqual(boss["AIName"], "")
        health = re.search(r"kZumrah\{ (\d+), (\d+) \};", REWORK.read_text(encoding="utf-8"))
        self.assertEqual(math.ceil(PALADIN_46_BASE * boss["HealthModifier"]), int(health.group(1)))
        self.assertEqual(boss["CreatureImmunitiesId"], 1972)
        self.assertEqual(self.edits[SKELETON]["ScriptName"], "npc_zf_zumrah_skeleton")
        for script in ("boss_zumrah_rework", "npc_zf_zumrah_skeleton", "npc_zf_empty_vessel", "npc_zf_lost_soul",
                       "npc_zf_bound_dead", "npc_zf_grave_stalker"):
            self.assertIn(f"RegisterDungeonReworkCreatureAI({script},", self.cpp)
        self.assertIn('ZfTest::RegisterBoss("zumrah"', self.cpp)

    def test_the_adds(self):
        scripts = {VESSEL: "npc_zf_empty_vessel", SOUL: "npc_zf_lost_soul", BOUND_DEAD: "npc_zf_bound_dead",
                   STALKER: "npc_zf_grave_stalker"}
        self.assertEqual({e: c["ScriptName"] for e, c in self.creatures.items()}, scripts)
        # The husk: friendly to players (no player attacks it), hostile to the Skeletons, selectable (s8 #11).
        vessel = self.creatures[VESSEL]
        self.assertEqual(vessel["faction"], 495)
        self.assertEqual(vessel["unit_flags"] & (0x2 | 0x02000000), 0)
        self.assertEqual(vessel["DamageModifier"], 0.0)
        # The others: untouchable.
        for entry in (SOUL, BOUND_DEAD, STALKER):
            self.assertEqual(self.creatures[entry]["unit_flags"], 0x2 | 0x02000000)
        self.assertEqual(self.creatures[SOUL]["flags_extra"] & 0x80, 0)         # a wisp is no invisible trigger
        self.assertEqual(self.creatures[BOUND_DEAD]["flags_extra"] & 0x80, 0)
        self.assertEqual({e: m["CreatureDisplayID"] for e, m in self.models.items()},
                         {VESSEL: CDI_STALKER, SOUL: CDI_SOUL, BOUND_DEAD: CDI_BOUND, STALKER: CDI_STALKER})
        self.assertEqual(float(self.models[SOUL]["DisplayScale"]), _value("kSoulScale"))
        self.assertTrue(1.5 <= _value("kSoulScale") <= 2.0)

    def test_kickable_casts_and_the_bar(self):
        bar = self.spells[REND]
        kickable = {i for i, s in self.spells.items() if _raw(s, "PreventionType") == PREVENTION_SILENCE}
        self.assertEqual(kickable, {VOLLEY, VOLLEY_HEROIC, BOLT})
        for spell_id in kickable:
            self.assertEqual(_raw(self.spells[spell_id], "InterruptFlags"), 15)
            self.assertEqual(self.spells[spell_id]["school"], SCHOOL_SHADOW)
            self.assertTrue(_raw(self.spells[spell_id], "AttributesEx2") & 0x00020000)    # keeps his swing timer
        self.assertEqual((_raw(bar, "InterruptFlags"), _raw(bar, "PreventionType")), (0, 0))
        self.assertEqual(bar["school"], SCHOOL_ARCANE)
        self.assertEqual(bar["effect1"]["type"], DUMMY_EFFECT)
        self.assertEqual(bar["cast_time_ms"], int(_value("kRendCastMs")))
        self.assertEqual((self.spells[VOLLEY]["cast_time_ms"], self.spells[VOLLEY_HEROIC]["cast_time_ms"]),
                         tuple(int(v) for v in _pair("kVolleyCastMs")))
        self.assertEqual(self.spells[BOLT]["cast_time_ms"], int(_value("kBoltCastMs")))
        # He never moves: the bolt reaches across the bowl.
        self.assertEqual(self.spells[BOLT]["range_yards"], 100.0)

    def test_the_spirit_world(self):
        walker = self.spells[BETWEEN_WORLDS]
        detect, speed = walker["effect1"], walker["effect2"]
        self.assertEqual((detect["apply_aura"], detect["misc_value"], int(detect["base_points"])),
                         (AURA_INVISIBILITY_DETECT, 11, int(_value("kSpiritSightValue"))))
        self.assertEqual((speed["apply_aura"], int(speed["base_points"])), (AURA_SPEED, int(_value("kWalkSpeedPct"))))
        self.assertGreaterEqual(walker["duration_ms"], int(_value("kWalkMs")))
        self.assertEqual(walker["dispel"], 0)
        self.assertTrue(walker["attributes"] & ATTR0_AURA_IS_DEBUFF)              # cannot be clicked off
        self.assertTrue(_raw(walker, "AuraInterruptFlags") & CHANGE_MAP)
        hidden = self.spells[SPIRIT_WORLD]["effect1"]
        self.assertEqual((hidden["apply_aura"], hidden["misc_value"], int(hidden["base_points"])),
                         (AURA_INVISIBILITY, 11, int(_value("kSpiritWorldValue"))))
        self.assertLessEqual(int(hidden["base_points"]), int(detect["base_points"]))
        self.assertRegex(_header(), r"kSpiritWorldType = 11;")
        self.assertEqual(self.spells[EMPTY_VESSEL]["effect1"]["apply_aura"], AURA_CLONE)
        self.assertTrue(_raw(self.spells[TETHER], "AttributesEx") & ATTR1_IS_CHANNELED)

    def test_the_stacks(self):
        gathered, ward = self.spells[GATHERED], self.spells[WARD]
        self.assertEqual(gathered["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertTrue(gathered["attributes"] & ATTR0_AURA_IS_DEBUFF)
        self.assertEqual(gathered["dispel"], 0)
        self.assertEqual(ward["effect1"]["apply_aura"], AURA_DAMAGE_TAKEN)
        self.assertEqual(int(ward["effect1"]["base_points"]), -int(_pair("kWardPctPerBound")[0]))
        self.assertEqual((ward["effect1"]["misc_value"], ward["effect1"]["die_sides"]), (127, 0))
        self.assertEqual((ward["dispel"], ward["duration_ms"]), (0, -1))
        cap = re.search(r"kGatheredMaxStacks = (\d+);", self.cpp)
        self.assertEqual(_raw(gathered, "CumulativeAura"), int(cap.group(1)))
        cap = re.search(r"kWardMaxStacks = (\d+);", self.cpp)
        self.assertEqual(_raw(ward, "CumulativeAura"), int(cap.group(1)))

    def test_the_hits(self):
        for spell_id in (VOLLEY_HIT, BOLT, STRIKE, SOUL_BURN):
            spell = self.spells[spell_id]
            effect = spell["effect1"]
            self.assertEqual(spell["school"], SCHOOL_SHADOW, spell_id)
            self.assertEqual((effect["type"], int(effect["base_points"]), int(effect["die_sides"])),
                             (SCHOOL_DAMAGE, 0, 0))
        self.assertEqual(self.scripts, {(ECHO, RESOLVE), (WAIL, RESOLVE), (GRAVES, RESOLVE)})
        for spell_id in (ECHO, WAIL, GRAVES):
            self.assertEqual(self.spells[spell_id]["school"], SCHOOL_SHADOW)
        for spell in self.spells.values():
            if any(e.get("type") == SCHOOL_DAMAGE for e in _effects(spell)):
                self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS, spell["id"])
                self.assertEqual(_raw(spell, "AttributesEx") & (ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION),
                                 ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION, spell["id"])
                self.assertTrue(_raw(spell, "AttributesEx2") & ATTR2_IGNORE_LOS, spell["id"])

    def test_the_looks_are_vs(self):
        looks = {REND: SV_REND, BETWEEN_WORLDS: SV_GHOST, EMPTY_VESSEL: 0, TETHER: SV_TETHER, SPIRIT_WORLD: 0,
                 LOST_SOUL: SV_SOUL, BOUND: SV_BIND, FREED: SV_FREED, GATHERED: SV_GATHERED, WARD: SV_WARD,
                 VOLLEY: SV_VOLLEY, VOLLEY_HEROIC: SV_VOLLEY, VOLLEY_HIT: SV_VOLLEY, BOLT: SV_BOLT, STRIKE: 0,
                 SOUL_BURN: 0, ECHO: SV_FREED, WAIL: SV_WAIL, GRAVES: SV_GRAVE, ERUPTION: SV_GRAVE}
        self.assertEqual({i: _raw(s, "SpellVisualID_1") for i, s in self.spells.items()}, looks)

    def test_the_cpp_registers_the_spec(self):
        code = _code(self.cpp)
        # Rule 27: no assist calls, every tick before UpdateVictim.
        self.assertRegex(code, r"ZulFarrak::NoAssist\(me\);[^\n]*\n\s+bool const hasVictim = UpdateVictim\(\);")
        for stock in STOCK_CASTS:
            self.assertNotIn(str(stock), code)
        self.assertIn("SPELL_WARD_OF_ZUMRAH = 11086", _header())
        # Nothing on the living side reaches the walker; the living-only and walker-only sets.
        self.assertEqual(code.count("bool CanAIAttack(Unit const* who) const override"), 2)
        self.assertIn("IsWalker(player) || !me->IsWithinDist(player, Tune::kVolleyRangeYd)", code)
        # The wails, the graves, the Bound Dead and (once the kit lets it) the souls.
        self.assertEqual(code.count(".SeenOnlyWith(kSpiritWorldType)"), 4)
        self.assertIn(".Weakened().Eligible(living).Tag(TAG_ZR_ECHO)", code)
        self.assertEqual(code.count(".Eligible(WalkerOnly(walker))"), 2)
        # ZR4: the kit's walker switch; ZR6: two Gathered Souls.
        self.assertIn("spec.onlyWhileCarriers = true;", code)
        self.assertIn("_souls.SetCarriers(me, GuidSet{ walker->GetGUID() });", code)
        self.assertIn("_souls.SetCarriers(me, GuidSet());", code)
        self.assertIn("spec.who.auraSpell = SPELL_ZR_GATHERED_SOULS;", code)
        self.assertIn("spec.who.minStacks = static_cast<uint8>(Tune::kSoulsToFree);", code)
        self.assertIn("ref.HealerWithinTankReach().SeenOnlyWith(kSpiritWorldType);", code)
        # Boss data.
        self.assertEqual(code.count("d.interrupts.emplace_back("), 1)
        self.assertNotIn("d.dispels", code)
        # RB-1: everything goes on reset, evade and death.
        cleanup = code[code.index("void Cleanup(bool snapBack)"):]
        for piece in ('EndWalk("cleanup", snapBack)', "_souls.Clear(me)", "_frees.Clear(me)", "summons.DespawnAll()",
                      "SPELL_ZR_WARD_OF_THE_DEAD", "SPELL_ZR_BETWEEN_WORLDS", "SPELL_ZR_GATHERED_SOULS",
                      "_skeletons.clear()", "_bound.clear()"):
            self.assertIn(piece, cleanup)
        for hook in ("void Reset() override", "void EnterEvadeMode(EvadeReason why) override",
                     "void JustDied(Unit* killer) override"):
            body = code[code.index(hook):]
            self.assertIn("Cleanup(true);", body[:body.index("\n    }")])
        self.assertNotIn("\t", self.cpp)

    def test_drill_tags(self):
        header = _header()
        for name, tag in (("TAG_ZR_SOUL", 9), ("TAG_ZR_FREE", 10), ("TAG_ZR_WAIL", 13), ("TAG_ZR_GRAVE", 14),
                          ("TAG_ZR_ECHO", 15)):
            self.assertRegex(header, rf"{name}\s*=\s*{tag},")


class ZumrahSqlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8")

    def test_the_texts(self):
        self.assertIn("(7271, 3, 0, '%s tears $n''s spirit from $g his:her; body!', 41, 0, 100, ", self.sql)
        self.assertIn("(7271, 4, 0, 'A lost soul is bound to %s''s ward!', 41, 0, 100, ", self.sql)
        groups = re.findall(r"(?:SAY|EMOTE)_ZUMRAH_\w+\s*=\s*(\d+),", _header())
        self.assertEqual(sorted(int(g) for g in groups), [0, 1, 3, 4])

    def test_the_rev_touches_only_the_new_texts(self):
        code = "\n".join(line for line in self.sql.splitlines() if not line.startswith("--"))
        self.assertEqual(re.findall(r"(?:DELETE FROM|INSERT INTO|UPDATE) `(\w+)`", code),
                         ["creature_text", "creature_text"])
        self.assertIn("WHERE `CreatureID` = 7271 AND `GroupID` IN (3, 4);", code)


if __name__ == "__main__":
    unittest.main()
