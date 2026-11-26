"""
Gnomeregan build WP-D5, Crowd Pummeler 9-60 in the glass window: source/npcs/gnomeregan/crowd_pummeler.py against
its C++ (modules/mod-dungeon-bosses src/Gnomeregan/CrowdPummelerLogic.h, CrowdPummelerMachine.{h,cpp},
boss_crowd_pummeler_rework.cpp), V's looks (source/npcs/gnomeregan/_visuals.py) and its SQL rev.

Checks:
  - the spells sit in the Pummeler's slice (214460-214489) and CrowdPummelerLogic.h names the same ids in order;
  - 6229 is bound (SmartAI off) at the header's normal health, immunity 1972, display 6774 at the window's scale 5
    (the header's kWindowScale, V's PUMMELER_SCALE); the frame stalker 301115 is an inert, invisible helper bound to
    a script the C++ registers, with no heroic template;
  - nothing is kickable (the kick table's row: none); the two pose bars are the header's live markers (1.5 s / 0.8 s),
    no effect, keep his swing timer, carry V's punch pose;
  - the five punches and Trample are resolve copies (ignore caster modifiers, no redirection or reflection, LESSONS
    L7), Physical; the looks are V's (hit flash, Pummel, Uppercut, the stomp ring, the stars); the stars are a short
    undispellable look;
  - the numbers the script plays by id match V's (the bell, the punch emote's anim, the display);
  - the C++ keeps the window's rules (rule 33: gravity off, SetControlled root, DisableRotate, SetDisplayId with the
    scale in one call, the reach fields re-set, no fall at death) and the boss rules (NoAssist first, damage and the
    pull from the pocket only, no loot in JustDied, one cleanup);
  - the SQL rev writes the four emotes (type 41) and the two chest templates (a consumable chest, lock 57, its own
    loot id, V's display) and nothing else;
  - with BM's source on hand (BM_SRC), the drill's row 7 tags are the header's.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_gnomeregan_crowd_pummeler.py
"""

from __future__ import annotations

import math
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
HEADER = MODULE_DIR / "CrowdPummelerLogic.h"
REWORK = MODULE_DIR / "GnomereganRework.h"
SCRIPT = MODULE_DIR / "boss_crowd_pummeler_rework.cpp"
MACHINE = MODULE_DIR / "CrowdPummelerMachine.cpp"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_crowd_pummeler_gnomeregan.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "gnomeregan"

SLICE = range(214460, 214490)
(LEFT, RIGHT, PUMMEL, UPPERCUT, CLINCH, TRAMPLE, TRAMPLE_LOOK, BAR, BAR_H, STARS) = range(214460, 214470)
PUMMELER, STALKER = 6229, 301115
CHESTS = (301380, 301381)
WARRIOR_28_BASE = 853       # creature_classlevelstats level 28 class 1 basehp0

SCHOOL_PHYSICAL = 1
SCHOOL_DAMAGE, APPLY_AURA, DUMMY_EFFECT = 2, 6, 3
AURA_DUMMY = 4
PREVENTION_SILENCE = 1
ATTR1_NO_REDIRECTION, ATTR1_NO_REFLECTION = 0x8, 0x80
ATTR2_DO_NOT_RESET_COMBAT_TIMERS = 0x00020000
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
CHANGE_MAP = 0x00080000
RESOLVE = "spell_boss_mechanics_resolve"
UNIT_FLAG_NON_ATTACKABLE, UNIT_FLAG_NOT_SELECTABLE = 0x2, 0x02000000
EMOTE_ONESHOT_ATTACK_UNARMED = 35   # Emotes.dbc 35 plays AnimationData 16 (AttackUnarmed)
SPELL_NAMES = ("SPELL_LEFT_HOOK", "SPELL_RIGHT_HOOK", "SPELL_CROWD_PUMMEL", "SPELL_UPPERCUT", "SPELL_CLINCH",
               "SPELL_TRAMPLE", "SPELL_TRAMPLE_LOOK", "SPELL_PUNCH_BAR", "SPELL_PUNCH_BAR_H", "SPELL_SEEING_STARS")


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


def _pair(name: str) -> tuple[float, float]:
    match = re.search(rf"\b{name}\{{ (-?[\d.]+)f?, (-?[\d.]+)f? \}};", _tune())
    assert match, name
    return float(match.group(1)), float(match.group(2))


def _code(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.lstrip().startswith(("//", "*", "/*")))


def _body(code: str, signature: str) -> str:
    start = code.index(signature)
    return code[start:code.index("\n    }", start)]


class PummelerDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in reg.creature_template_edits if int(e["entry"]) == PUMMELER}
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == STALKER}
        cls.models = {(int(e["CreatureID"]), int(e["Idx"])): e for e in reg.creature_template_models
                      if int(e["CreatureID"]) in (PUMMELER, STALKER)}
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.machine = MACHINE.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(LEFT, STARS + 1)))
        self.assertEqual(id_blocks.out_of_reservation("gnomeregan", {"spell": mine}), [])
        slice_ = re.search(r"kSpellsPummeler\{\s*(\d+),\s*(\d+)\s*\}", REWORK.read_text(encoding="utf-8"))
        self.assertEqual((int(slice_.group(1)), int(slice_.group(2))), (SLICE.start, SLICE.stop - 1))
        named = re.findall(r"(SPELL_\w+)\s*=\s*kSpellSlice\.first \+ (\d+),", self.header)
        self.assertEqual([n for n, _ in named], list(SPELL_NAMES))
        self.assertEqual([SLICE.start + int(o) for _, o in named], mine)

    def test_the_boss_and_the_stalker(self):
        boss = self.edits[PUMMELER]
        self.assertEqual((boss["ScriptName"], boss["AIName"]), ("boss_crowd_pummeler_rework", ""))
        health = re.search(r"kCrowdPummeler\{ (\d+), (\d+) \}", REWORK.read_text(encoding="utf-8"))
        self.assertEqual(math.ceil(WARRIOR_28_BASE * boss["HealthModifier"]), int(health.group(1)))
        self.assertEqual((boss["DamageModifier"], boss["CreatureImmunitiesId"]), (1.7, 1972))
        model = self.models[(PUMMELER, 0)]
        self.assertEqual(int(model["CreatureDisplayID"]), v.DISPLAY_PUMMELER)
        self.assertEqual(float(model["DisplayScale"]), _value("kWindowScale"))
        self.assertEqual(float(model["DisplayScale"]), v.PUMMELER_SCALE)
        stalker = self.creatures[STALKER]
        self.assertEqual(stalker["ScriptName"], "npc_gnomer_pummeler_frame")
        self.assertEqual(stalker["unit_flags"] & (UNIT_FLAG_NON_ATTACKABLE | UNIT_FLAG_NOT_SELECTABLE),
                         UNIT_FLAG_NON_ATTACKABLE | UNIT_FLAG_NOT_SELECTABLE)
        self.assertEqual(stalker.get("difficulty_entry_1", 0), 0)       # a helper: no heroic template
        self.assertEqual(int(self.models[(STALKER, 0)]["CreatureDisplayID"]), v.DISPLAY_INVISIBLE_STALKER)
        for script in ("boss_crowd_pummeler_rework", "npc_gnomer_pummeler_frame"):
            self.assertIn(f"RegisterDungeonReworkCreatureAI({script},", self.cpp)
        self.assertIn('GnomerTest::RegisterBoss("pummeler"', self.cpp)

    def test_nothing_is_kickable_and_the_bars(self):
        kickable = {i for i, s in self.spells.items() if _raw(s, "PreventionType") == PREVENTION_SILENCE
                    or _raw(s, "InterruptFlags")}
        self.assertEqual(kickable, set())
        live = _pair("kLiveMs")
        for bar, ms in ((BAR, live[0]), (BAR_H, live[1])):
            spell = self.spells[bar]
            self.assertEqual(spell["school"], SCHOOL_PHYSICAL)
            self.assertEqual(spell["cast_time_ms"], int(ms))
            self.assertEqual(spell["effect1"]["type"], DUMMY_EFFECT)
            self.assertTrue(_raw(spell, "AttributesEx2") & ATTR2_DO_NOT_RESET_COMBAT_TIMERS)
            self.assertEqual(_raw(spell, "SpellVisualID_1"), v.CP_PUNCH_POSE)
        self.assertEqual({i for i, s in self.spells.items() if s.get("cast_time_ms")}, {BAR, BAR_H})

    def test_the_hits_are_resolve_copies(self):
        damaging = {i for i, s in self.spells.items() if (s.get("effect1") or {}).get("type") == SCHOOL_DAMAGE}
        self.assertEqual(damaging, {LEFT, RIGHT, PUMMEL, UPPERCUT, CLINCH, TRAMPLE})
        for spell_id in damaging:
            spell = self.spells[spell_id]
            self.assertEqual(spell["school"], SCHOOL_PHYSICAL, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
            self.assertTrue(_raw(spell, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
            self.assertTrue(_raw(spell, "AttributesEx") & ATTR1_NO_REDIRECTION)
            self.assertTrue(_raw(spell, "AttributesEx") & ATTR1_NO_REFLECTION)

    def test_the_looks_are_vs(self):
        looks = {LEFT: v.CP_HIT_FLASH, RIGHT: v.CP_HIT_FLASH, PUMMEL: v.CP_PUMMEL, UPPERCUT: v.CP_UPPERCUT,
                 CLINCH: v.CP_PUMMEL, TRAMPLE_LOOK: v.CP_STOMP, BAR: v.CP_PUNCH_POSE, BAR_H: v.CP_PUNCH_POSE,
                 STARS: v.CP_LANDED}
        self.assertEqual({i: _raw(s, "SpellVisualID_1") for i, s in self.spells.items() if i in looks}, looks)
        self.assertEqual(_raw(self.spells[TRAMPLE], "SpellVisualID_1"), 0)     # the ring is the stalker's look
        stars = self.spells[STARS]
        self.assertEqual((stars["dispel"], stars["duration_ms"]), (0, int(_value("kSeeingStarsMs"))))
        self.assertEqual((stars["effect1"]["type"], stars["effect1"]["apply_aura"]), (APPLY_AURA, AURA_DUMMY))
        self.assertTrue(_raw(stars, "AuraInterruptFlags") & CHANGE_MAP)
        # Never wired: the wrong-tone one-shots V lists (1184 Backhand's knockdown, 1187 Knockout, 672's crescent).
        wired = {_raw(s, "SpellVisualID_1") for s in self.spells.values()}
        self.assertFalse(wired & {1184, 1187, 672})

    def test_the_numbers_the_script_plays(self):
        def const(name: str) -> int:
            return int(re.search(rf"\b{name} = (\d+);", self.header).group(1))
        self.assertEqual(const("kBellSound"), v.CP_BELL)
        self.assertEqual(const("kDisplayPummeler"), v.DISPLAY_PUMMELER)
        self.assertEqual(const("kPunchEmote"), EMOTE_ONESHOT_ATTACK_UNARMED)
        self.assertEqual(v.CP_PUNCH_EMOTE_ANIM, 16)
        self.assertEqual(_pair("kPunchPct"), (40, 60))
        self.assertEqual(_pair("kTramplePct"), (8, 12))
        self.assertEqual((_value("kCombatReachYd"), _value("kNearRadiusYd"), _value("kLaneWidthYd")), (10, 12, 8))
        self.assertEqual((_value("kComboFirstMs"), _value("kComboAfterMs")), (10000, 18000))

    def test_the_cpp_keeps_the_window(self):
        code = _code(self.cpp)
        # Rule 33 and section 10.
        hold = _body(code, "void HoldTheWindow(char const* why)")
        for piece in ("me->SetDisableGravity(true);", "me->SetControlled(true, UNIT_STATE_ROOT);",
                      "me->DisableRotate(true);", "WindowReach(me->GetObjectScale())",
                      "me->SetFloatValue(UNIT_FIELD_COMBATREACH, reach);",
                      "me->SetFloatValue(UNIT_FIELD_BOUNDINGRADIUS, reach);", "me->NearTeleportTo("):
            self.assertIn(piece, hold)
        reset = _body(code, "void Reset() override")
        self.assertIn("me->SetDisplayId(kDisplayPummeler, Tune::kWindowScale);", reset)
        self.assertIn("me->SetCombatMovement(false);", reset)
        self.assertIn('HoldTheWindow("reset");', reset)
        self.assertRegex(code, r"GnomereganRework::NoAssist\(me\);[^\n]*\n\s+HoldTheWindow\(nullptr\);[^\n]*\n"
                               r"\s+if \(!UpdateVictim\(\)\)")
        # No root aura (mask 1972 holds root): no aura is put on him at all.
        self.assertNotRegex(code, r"me->(AddAura|CastSpell\(me, SPELL_\w*ROOT)")
        # No fall at death: the killing blow's flag, then the body kept in the glass.
        self.assertIn("me->SetUnitFlag(UNIT_FLAG_DISABLE_MOVE);", _body(code, "void DamageTaken("))
        died = _body(code, "void JustDied(Unit* killer) override")
        self.assertIn("KeepTheBody();", died)
        self.assertIn("me->SetDisableGravity(true);", _body(code, "void KeepTheBody()"))
        # Never a creature_model_info edit (shared display): nothing in the C++ or the rev touches it.
        self.assertNotIn("creature_model_info", SQL.read_text(encoding="utf-8").split("\n-- ")[-1])

    def test_the_cpp_keeps_the_boss_rules(self):
        code = _code(self.cpp)
        # Damage and the pull from the pocket only (row D5).
        self.assertIn("if (attacker && attacker != me && !InThePocket(attacker))", code)
        self.assertIn("damage = 0;", _body(code, "void DamageTaken("))
        engage = _body(code, "void JustEngagedWith(Unit* who) override")
        self.assertLess(engage.index("if (!InThePocket(who))"), engage.index("BossAI::JustEngagedWith(who);"))
        # Rule 1: loot and bits never in JustDied.
        died = re.sub(r"//.*", "", _body(code, "void JustDied(Unit* killer) override"))
        for banned in ("loot", "Loot", "SummonGameObject", "SetData("):
            self.assertNotIn(banned, died)
        # Mechanics include the tank (rule 17): every punch's tank row is its percent, Trample's too.
        self.assertIn("s.tankPct = _spec.pct[k];", _code(self.machine))
        self.assertIn("spec.tankPct = spec.pct;", code)
        self.assertIn("spec.weakened = false;", code)       # Trample: no penalty
        self.assertIn("spec.frame.floor = PocketArena();", code)
        self.assertIn("if (bounds)\n                        ref.Within(*bounds);", self.machine)
        # RB-1: one cleanup on reset, evade, pull and death.
        cleanup = _body(code, "void Cleanup(char const* why)")
        for piece in ("_combo->Clear();", "Mechanic::Cancel(me, handle);", "stalker->DespawnOrUnsummon();",
                      "RemoveAurasDueToSpell(SPELL_SEEING_STARS);", "_arena.Reset();"):
            self.assertIn(piece, cleanup)
        for hook in ("void Reset() override", "void EnterEvadeMode(EvadeReason why) override",
                     "void JustDied(Unit* killer) override", "void JustEngagedWith(Unit* who) override"):
            self.assertIn("Cleanup(", _body(code, hook))
        self.assertNotIn("\t", self.cpp)
        self.assertNotIn("\t", self.machine)
        self.assertNotIn("\t", self.header)

    def test_the_bots_and_pets(self):
        code = _code(self.cpp)
        # R-1-B M1: the ranged band past the hunters' line, described at engage.
        self.assertEqual((_value("kRangedBandMinYd"), _value("kRangedBandMaxYd")), (19, 26))
        self.assertIn("d.rangeBands.emplace_back(Tune::kRangedBandMinYd, Tune::kRangedBandMaxYd);",
                      _body(code, "void Describe()"))
        engage = _body(code, "void JustEngagedWith(Unit* who) override")
        self.assertLess(engage.index("Mechanic::BeginEncounter(me, options);"), engage.index("Describe();"))
        # R-1-B m3: only a player in reach keeps the at-once Trample away.
        reach = _body(code, "void CheckReach(uint32 diff)")
        self.assertIn("CountsAsPlayer(player)", reach)
        self.assertIn("me->IsWithinMeleeRange(player)", reach)
        # R-1-B M2: every tick, before the combination's early return; the chase without the angle.
        update = _body(code, "void UpdateAI(uint32 diff) override")
        self.assertLess(update.index("KeepPetsOffTheGlass();"), update.index("if (_comboRunning)"))
        pets = _body(code, "void KeepPetsOffTheGlass()")
        self.assertIn("motion->MoveChase(me, ChaseRange(0.f, 0.f));", pets)
        self.assertIn("ENTRY_IMP", pets)
        self.assertIn("_petChases.clear();", _body(code, "void Cleanup(char const* why)"))
        # R-1-B n1: the body is put back every time, a fall spline stopped first.
        body = _body(code, "void KeepTheBody()")
        self.assertIn("me->StopMovingOnCurrentPos();", body)
        self.assertNotIn("GetExactDist", body)

    @unittest.skipUnless(os.environ.get("BM_SRC") and (Path(os.environ["BM_SRC"]) / "MechanicDrill.h").is_file(),
                         "BM_SRC (mod-boss-mechanics src) not set")
    def test_the_drill_tags_are_the_headers(self):
        drill = (Path(os.environ["BM_SRC"]) / "MechanicDrill.h").read_text(encoding="utf-8")
        for tag, name in re.findall(r"\{ TAG_(\w+), \"Zone\", \"(kGn\w+)\" \}", self.header):
            ours = int(re.search(rf"\bTAG_{tag}\s*=\s*(\d+),", self.header).group(1))
            theirs = int(re.search(rf"\b{name} = (\d+);", drill).group(1))
            self.assertEqual(ours, theirs, name)


class PummelerSqlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.code = "\n".join(line for line in cls.sql.splitlines() if not line.startswith("--"))

    def test_the_emotes(self):
        lines = re.findall(r"\(6229, (\d), 0, '([^']*)', (\d+), ", self.code)
        self.assertEqual(lines, [
            ("0", "%s winds up a combination!", "41"),
            ("1", "The bell rings. Round two!", "41"),
            ("2", "The bell rings. Final round!", "41"),
            ("3", "%s shudders, sparks, and goes dark behind the glass.", "41"),
        ])
        groups = re.findall(r"EMOTE_\w+\s*=\s*(\d+),", HEADER.read_text(encoding="utf-8"))
        self.assertEqual(sorted(int(g) for g in groups), [0, 1, 2, 3])

    def test_the_chests(self):
        rework = REWORK.read_text(encoding="utf-8")
        self.assertIn("GO_PUMMELER_CHEST           = 301380,", rework)
        self.assertIn("GO_PUMMELER_CHEST_HEROIC    = 301381,", rework)
        for entry in CHESTS:
            row = re.search(rf"\({entry}, 3, (\d+), '[^']+', '', '', '', 1, 57, (\d+), 0, 1, ", self.code)
            self.assertTrue(row, entry)
            self.assertEqual((int(row.group(1)), int(row.group(2))), (v.GODI_CHEST, entry))

    def test_the_rev_touches_only_its_rows(self):
        self.assertEqual(re.findall(r"(?:DELETE FROM|INSERT INTO|(?<!KEY )UPDATE) `(\w+)`", self.code),
                         ["creature_text", "creature_text", "gameobject_template", "gameobject_template_addon",
                          "gameobject_template_addon"])
        self.assertIn("WHERE `CreatureID` = 6229 AND `GroupID` IN (0, 1, 2, 3);", self.code)


if __name__ == "__main__":
    unittest.main()
