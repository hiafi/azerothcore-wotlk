"""
Gnomeregan build WP-D1, Techbot: source/npcs/gnomeregan/techbot.py against its C++ (modules/mod-dungeon-bosses
src/Gnomeregan/TechbotLogic.h, TechbotMachine.{h,cpp}, boss_techbot_rework.cpp) and its SQL rev.

Checks:
  - the spells sit in Techbot's slice (214300-214339) and TechbotLogic.h names the same ids;
  - Techbot 301105 is bound at the header's health; the Dupe Bug 301106 is a level 28 mechanical copy of 7732 at
    faction 63 (never 494), 300 health, not stun immune, no loot, no XP, its heroic entry from heroic_ids.lock when
    WP-H wrote it; the after-image 301107 is a helper nobody targets;
  - the kick table (rule 26): Duplication (Nature) and Patch (Arcane) are the only kickable casts, each the only cast of
    its school on its caster; the dispel table (rule 27): Battle Net's root is the only dispellable aura (Magic), the
    marks are NO_IMMUNITIES;
  - the resolve copies (rule 2), the cast times, Safe Mode, Version, the shutdown's death persistence, V's looks;
  - the C++ keeps the rules: NoAssist first, the tank in every hit, Weakened where SP says, the bounds, the descriptor
    (kick only while a bug lives, never otherwise; a casting bug first; Battle Net dispelled on heroic), the cleanup;
  - the SQL rev writes Techbot's 13 copied lines and lines 1-6 and the bug's emote, nothing else.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_gnomeregan_techbot.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Gnomeregan"
LOGIC_H = MODULE_DIR / "TechbotLogic.h"
REWORK = MODULE_DIR / "GnomereganRework.h"
BOSS_CPP = MODULE_DIR / "boss_techbot_rework.cpp"
MACHINE_CPP = MODULE_DIR / "TechbotMachine.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_techbot_gnomeregan.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "gnomeregan"
LOCK = TOOL_ROOT / "source" / "world" / "heroic_ids.lock"

SLICE = range(214300, 214340)
(LAG_SPIKE, LAG, DUP, DUP_H, PATCH, PATCH_H, SAFE_MODE, SAFE_START, PATCH_DONE, VERSION, RUBBER_BAND, SAVE_POINT,
 SNAP, RUBBER_SPIKE, SAVE_BURST, BUG_ECHO, NET, NET_ROOT, NET_THROW, BUG_SPAWN, SHUTDOWN, AFTER_IMAGE,
 LANDING) = range(214300, 214323)
TECHBOT, DUPE_BUG, ECHO = 301105, 301106, 301107

SCHOOL_PHYSICAL, SCHOOL_FIRE, SCHOOL_NATURE, SCHOOL_ARCANE = 1, 4, 8, 64
SCHOOL_DAMAGE, APPLY_AURA = 2, 6
AURA_MOD_ROOT, AURA_DUMMY, AURA_MOD_DAMAGE_PERCENT_DONE, AURA_MOD_DAMAGE_PERCENT_TAKEN, AURA_CLONE_CASTER = (
    26, 4, 79, 87, 247)
DISPEL_MAGIC = 1
PREVENTION_SILENCE = 1
ATTR0_NO_IMMUNITIES = 0x20000000
ATTR1_NO_REDIRECTION, ATTR1_NO_REFLECTION = 0x8, 0x80
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
ATTR3_ALLOW_AURA_WHILE_DEAD = 0x00100000
CHANGE_MAP = 0x00080000
RESOLVE = "spell_boss_mechanics_resolve"
UNIT_FLAG_NON_ATTACKABLE, UNIT_FLAG_NOT_SELECTABLE = 0x2, 0x02000000
TYPE_MECHANICAL = 9
FLAGS_EXTRA_NO_XP = 0x40
BASE_HEALTH_28 = 853
# V's picks (_visuals.py).
SV = {LAG_SPIKE: 2917, LAG: 68, DUP: 2073, DUP_H: 2073, SAFE_MODE: 37, SAFE_START: 2956, PATCH_DONE: 2074,
      RUBBER_BAND: 68, SAVE_POINT: 2046, SNAP: 263, RUBBER_SPIKE: 2917, SAVE_BURST: 2917, BUG_ECHO: 2917,
      NET_ROOT: 683, NET_THROW: 683, BUG_SPAWN: 2073, SHUTDOWN: 7867, AFTER_IMAGE: 886, LANDING: 2917}
DISPLAYS = {TECHBOT: 7288, DUPE_BUG: 3233, ECHO: 11686}


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
    text = LOGIC_H.read_text(encoding="utf-8")
    return text[text.index("namespace Tune"):]


def _value(name: str) -> float:
    match = re.search(rf"\b{name} = (-?[\d.]+)f?;", _tune())
    assert match, name
    return float(match.group(1))


def _pair(name: str) -> tuple[float, float]:
    match = re.search(rf"\b{name}\{{ (-?[\d.]+)f?, (-?[\d.]+)f? \}};", _tune())
    assert match, name
    return float(match.group(1)), float(match.group(2))


def _code(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith(("//", "*", "/*")))


class TechbotDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates
                         if int(e["entry"]) in (TECHBOT, DUPE_BUG, ECHO)}
        cls.models = [e for e in reg.creature_template_models if int(e["CreatureID"]) in (TECHBOT, DUPE_BUG, ECHO)]
        cls.cpp = BOSS_CPP.read_text(encoding="utf-8")
        cls.machine = MACHINE_CPP.read_text(encoding="utf-8")
        cls.logic = LOGIC_H.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(LAG_SPIKE, LANDING + 1)))
        self.assertEqual(id_blocks.out_of_reservation("gnomeregan", {"spell": mine}), [])
        bounds = re.search(r"kSpellsTechbot\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertEqual((int(bounds.group(1)), int(bounds.group(2))), (SLICE.start, SLICE.stop - 1))
        named = sorted(int(i) for i in re.findall(r"SPELL_\w+\s*=\s*(2143\d\d),", self.logic))
        self.assertEqual(named, mine)

    def test_techbot_is_bound(self):
        row = self.creatures[TECHBOT]
        self.assertEqual((row["ScriptName"], row["AIName"], row["CreatureImmunitiesId"]),
                         ("boss_techbot_rework", "", 1972))
        normal = re.search(r"kTechbot\{ (\d+), (\d+) \}", REWORK.read_text(encoding="utf-8"))
        self.assertEqual(math.ceil(BASE_HEALTH_28 * row["HealthModifier"]), int(normal.group(1)))
        self.assertEqual((row["minlevel"], row["maxlevel"], row["faction"], row["type"]), (28, 28, 63, TYPE_MECHANICAL))
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_techbot_rework,", self.cpp)

    def test_the_bug_and_the_after_image(self):
        bug = self.creatures[DUPE_BUG]
        self.assertEqual((bug["ScriptName"], bug["AIName"], bug["faction"], bug["type"], bug["rank"]),
                         ("npc_gnomer_dupe_bug", "", 63, TYPE_MECHANICAL, 0))
        self.assertEqual((bug["minlevel"], bug["maxlevel"]), (28, 28))
        dupe = re.search(r"kDupeBug\{ (\d+), (\d+) \}", REWORK.read_text(encoding="utf-8"))
        self.assertEqual(math.ceil(BASE_HEALTH_28 * bug["HealthModifier"]), int(dupe.group(1)))
        self.assertEqual(bug["CreatureImmunitiesId"], 0)                  # a stun stops a Duplication
        self.assertEqual((bug["lootid"], bug["flags_extra"] & FLAGS_EXTRA_NO_XP), (0, FLAGS_EXTRA_NO_XP))
        self.assertEqual(bug["DamageModifier"], 1.7)
        heroic = 310576  # WP-H's predicted id (gnomeregan.py `_HEROIC_ID`), until the lock holds the line
        if LOCK.exists():
            line = re.search(rf"^{DUPE_BUG} (\d+) ", LOCK.read_text(encoding="utf-8"), re.M)
            heroic = int(line.group(1)) if line else heroic
        self.assertEqual(bug.get("difficulty_entry_1"), heroic)
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_gnomer_dupe_bug,", self.cpp)
        echo = self.creatures[ECHO]
        self.assertEqual(echo["ScriptName"], "npc_gnomer_lag_echo")
        self.assertEqual(echo["unit_flags"] & (UNIT_FLAG_NON_ATTACKABLE | UNIT_FLAG_NOT_SELECTABLE),
                         UNIT_FLAG_NON_ATTACKABLE | UNIT_FLAG_NOT_SELECTABLE)
        self.assertEqual(echo.get("difficulty_entry_1", 0), 0)
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_gnomer_lag_echo,", self.cpp)
        for entry, display in DISPLAYS.items():
            self.assertEqual([int(m["CreatureDisplayID"]) for m in self.models if int(m["CreatureID"]) == entry],
                             [display])

    def test_the_kick_table(self):
        kickable = {i for i, s in self.spells.items() if _raw(s, "PreventionType") == PREVENTION_SILENCE
                    or _raw(s, "InterruptFlags")}
        self.assertEqual(kickable, {DUP, DUP_H, PATCH, PATCH_H})
        for spell_id in (DUP, DUP_H):
            self.assertEqual(self.spells[spell_id]["school"], SCHOOL_NATURE)    # the bug's only cast
        for spell_id in (PATCH, PATCH_H):
            self.assertEqual(self.spells[spell_id]["school"], SCHOOL_ARCANE)    # his only Arcane cast
        # Nothing else he casts untriggered: the looks and auras are triggered, his hits the registry's.
        self.assertNotRegex(_code(self.cpp), r"CastSpell\([^;]*SPELL_(?!PATCH)\w+, false\)")
        cast_times = {i: s.get("cast_time_ms") for i, s in self.spells.items() if s.get("cast_time_ms")}
        self.assertEqual(cast_times, {DUP: int(_pair("kDupCastMs")[0]), DUP_H: int(_pair("kDupCastMs")[1]),
                                      PATCH: int(_pair("kPatchCastMs")[0]), PATCH_H: int(_pair("kPatchCastMs")[1])})

    def test_the_dispel_table(self):
        dispel = {i: s.get("dispel", 0) for i, s in self.spells.items() if s.get("dispel")}
        self.assertEqual(dispel, {NET_ROOT: DISPEL_MAGIC})
        root = self.spells[NET_ROOT]
        self.assertEqual((root["effect1"]["apply_aura"], root["duration_ms"]),
                         (AURA_MOD_ROOT, int(_value("kNetRootMs"))))
        for spell_id in (LAG, RUBBER_BAND):
            self.assertTrue(self.spells[spell_id]["attributes"] & ATTR0_NO_IMMUNITIES, spell_id)
            self.assertTrue(_raw(self.spells[spell_id], "AuraInterruptFlags") & CHANGE_MAP, spell_id)
        self.assertTrue(_raw(root, "AuraInterruptFlags") & CHANGE_MAP)

    def test_the_resolve_copies(self):
        damaging = {i for i, s in self.spells.items() if (s.get("effect1") or {}).get("type") == SCHOOL_DAMAGE}
        self.assertEqual(damaging, {LAG_SPIKE, RUBBER_SPIKE, SAVE_BURST, BUG_ECHO, NET})
        schools = {LAG_SPIKE: SCHOOL_FIRE, RUBBER_SPIKE: SCHOOL_ARCANE, SAVE_BURST: SCHOOL_ARCANE,
                   BUG_ECHO: SCHOOL_FIRE, NET: SCHOOL_NATURE}
        for spell_id in damaging:
            spell = self.spells[spell_id]
            self.assertEqual(spell["school"], schools[spell_id])
            self.assertIn((spell_id, RESOLVE), self.scripts)
            self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
            self.assertTrue(_raw(spell, "AttributesEx") & ATTR1_NO_REDIRECTION)
            self.assertTrue(_raw(spell, "AttributesEx") & ATTR1_NO_REFLECTION)

    def test_the_auras(self):
        safe = self.spells[SAFE_MODE]
        self.assertEqual((safe["effect1"]["apply_aura"], int(safe["effect1"]["base_points"]),
                          safe["effect1"]["misc_value"], safe["dispel"], safe["mechanic"]),
                         (AURA_MOD_DAMAGE_PERCENT_TAKEN, int(_value("kSafeModeTakenPct")), 127, 0, 0))
        version = self.spells[VERSION]
        self.assertEqual((version["effect1"]["apply_aura"], int(version["effect1"]["base_points"]),
                          version["duration_ms"], _raw(version, "CumulativeAura")),
                         (AURA_MOD_DAMAGE_PERCENT_DONE, 0, -1, int(_value("kVersionShownCap"))))
        self.assertIn("effect->ChangeAmount(VersionAuraAmount(_version));", self.cpp)
        shutdown = self.spells[SHUTDOWN]
        self.assertTrue(_raw(shutdown, "AttributesEx3") & ATTR3_ALLOW_AURA_WHILE_DEAD)
        self.assertEqual(shutdown["duration_ms"], int(_value("kShutdownSparksMs")))
        clone = self.spells[AFTER_IMAGE]
        self.assertEqual(clone["effect1"]["apply_aura"], AURA_CLONE_CASTER)
        # The Duplication bar leaves an aura of itself on its caster: the machine's "done".
        for spell_id in (DUP, DUP_H):
            effect = self.spells[spell_id]["effect1"]
            self.assertEqual((effect["type"], effect["apply_aura"]), (APPLY_AURA, AURA_DUMMY))
            self.assertGreater(self.spells[spell_id]["duration_ms"], 0)
        self.assertIn("unit->HasAura(_spec.barSpellId)", self.machine)
        self.assertEqual(self.spells[LAG]["duration_ms"], int(_value("kLagWarnMs")))
        self.assertGreaterEqual(self.spells[RUBBER_BAND]["duration_ms"], int(_value("kBandSnapMs")))

    def test_the_looks_are_vs(self):
        self.assertEqual({i: _raw(s, "SpellVisualID_1") for i, s in self.spells.items() if i in SV}, SV)

    def test_the_numbers(self):
        self.assertEqual((_value("kLagFirstMs"), _value("kLagEveryMs"), _value("kLagWarnMs")), (8000, 15000, 2000))
        self.assertEqual((_value("kLagRadiusYd"), _value("kLagPct")), (5, 40))
        self.assertEqual(_pair("kBugEveryMs"), (10000, 8000))
        self.assertEqual(_pair("kBugCap"), (8, 0))
        self.assertEqual((_value("kBugRiseYd"), _value("kBugApartYd")), (3, 3))
        self.assertEqual(_pair("kDupFirstMs"), (9000, 7000))
        self.assertEqual(_pair("kDupRepeatMs"), (0, 7000))
        self.assertEqual(_pair("kPatchEveryMs"), (45000, 35000))
        self.assertEqual(_pair("kPatchHealPctPerBug"), (3, 4))
        self.assertEqual(_value("kVersionDonePctPerStack"), 5)
        self.assertEqual((_value("kBandSaveMs"), _value("kBandSpikeTwoMs"), _value("kBandSpikeWarnMs"),
                          _value("kBandSnapMs")), (2000, 3500, 1500, 5000))
        self.assertEqual((_value("kBandSpikeYd"), _value("kBandSpikePct"), _value("kSavePointYd"),
                          _value("kSavePointPct")), (5, 60, 6, 60))
        self.assertEqual((_value("kEchoRadiusYd"), _value("kEchoWarnMs"), _value("kEchoPct")), (4, 2000, 40))
        self.assertEqual((_value("kNetFirstMs"), _value("kNetEveryMs"), _value("kNetWarnMs"), _value("kNetRadiusYd"),
                          _value("kNetPct")), (20000, 25000, 1500, 8, 20))

    def test_the_cpp_keeps_the_rules(self):
        cpp = _code(self.cpp)
        # No assist calls, every tick before UpdateVictim (rule 29): the boss and the bug.
        self.assertEqual(len(re.findall(r"GnomereganRework::NoAssist\(me\);[^\n]*\n\s+if \(!UpdateVictim\(\)\)", cpp)),
                         2)
        # Mechanics include the tank (rule 17): every damaging circle carries TankDamage; Weakened where SP says.
        circles = re.findall(r"Mechanic::Circle\(me,[^;]*;", cpp, re.S)
        self.assertEqual(len(circles), 5)
        for circle in circles:
            self.assertIn(".TankDamage(", circle)
            self.assertIn(".Within(_bounds)", circle)
            weakened = ".Weakened()" in circle
            self.assertEqual(weakened, "SPELL_SAVE_POINT_BURST" not in circle, circle)
        self.assertIn(".Eligible(others)", cpp)
        self.assertIn(".Rider(SPELL_BATTLE_NET_ROOT)", cpp)
        self.assertIn("rule.nonTank = false;", cpp)
        # The descriptor: a casting bug first, Patch kicked only while a bug lives and never otherwise, Net dispelled.
        self.assertIn("Condition::NearUnit(NPC_DUPE_BUG, Tune::kPatchBugRangeYd)", cpp)
        self.assertIn("d.interrupts.emplace_back(NPC_TECHBOT, patch, kKickPatch, every, bugNear);", cpp)
        self.assertIn("d.interrupts.emplace_back(NPC_TECHBOT, patch, kNeverKick, every, Condition::Not(bugNear));",
                      cpp)
        self.assertIn("d.dispels.push_back(DispelEntry(SPELL_BATTLE_NET_ROOT, kDispelNet));", cpp)
        # Loot and credit are BossAI's at the death (no bit in JustDied, rule 1).
        died = cpp[cpp.index("void JustDied(Unit* killer) override"):]
        died = died[:died.index("\n    }\n")]
        self.assertNotIn("LootMode", died)
        self.assertIn("BossAI::JustDied(killer);", died)
        # RB-1: one cleanup on reset, evade and death.
        cleanup = cpp[cpp.index("void Cleanup(char const* why, bool death = false)"):]
        for piece in ("Mechanic::Cancel(me, handle)", "_dup->Clear()", "summons.DespawnAll()", "_bands.clear()",
                      "kOwnAuras", "kPlayerAuras", "_arena.Reset()"):
            self.assertIn(piece, cleanup)
        for call in ('Cleanup("reset")', 'Cleanup("evade")', 'Cleanup("death", true)'):
            self.assertIn(call, cpp)
        for text in (self.cpp, self.machine, self.logic):
            self.assertNotIn("\t", text)


class TechbotSqlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8")

    def test_the_texts(self):
        chatter = re.findall(r"\(301105, 0, (\d+), '[^\n]*', 12, 0, 9, ", self.sql)
        self.assertEqual([int(i) for i in chatter], list(range(13)))
        logic = LOGIC_H.read_text(encoding="utf-8")
        groups = dict((name, int(g)) for name, g in re.findall(r"(\w+)\s*=\s*(\d+),\s*//", logic[
            logic.index("enum TechbotTexts"):logic.index("EMOTE_DUPLICATE")]))
        types = {"EMOTE_LAG": 41, "YELL_PATCH": 14, "YELL_PATCH_FIXED": 14, "YELL_PATCH_CLEAN": 14,
                 "YELL_SHUTDOWN": 14, "EMOTE_RUBBER_BAND": 41}
        for name, kind in types.items():
            self.assertRegex(self.sql, rf"\(301105, {groups[name]}, 0, '[^\n]*', {kind}, 0, 100, ", name)
        self.assertIn("(301106, 0, 0, '%s begins to duplicate!', 41, 0, 100, ", self.sql)

    def test_the_rev_touches_only_its_rows(self):
        code = "\n".join(line for line in self.sql.splitlines() if not line.startswith("--"))
        self.assertEqual(re.findall(r"(?:DELETE FROM|INSERT INTO|UPDATE) `(\w+)`", code), ["creature_text"] * 4)
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 301105;", code)
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 301106;", code)


if __name__ == "__main__":
    unittest.main()
