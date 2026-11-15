"""
Blackrock Spire build WP-B2, Shadow Hunter Vosh'gajin: source/npcs/blackrock_spire/voshgajin.py against its C++
(modules/mod-dungeon-bosses src/BlackrockSpire/VoshgajinLogic.h, boss_shadow_hunter_voshgajin_rework.cpp) and its SQL
rev.

Checks:
  - the spells sit in her slice (210060-210089), VoshgajinLogic.h names the same ids, and the Voodoo Doll 300703 is
    inside the creature reservation;
  - Puppet Strings is a 20 s channel (the script cuts it), not interruptible, not a cure target;
  - Bound is a Curse DoT of 5% every 2 s through the kit's generic percent spell, CHANGE_MAP, the same on heroic;
  - Hex of Agony is a Magic DoT of 4% a second for 8 s through the same spell, CHANGE_MAP;
  - the Hexed rider is the stock Hex's transform and confusion, 2 s, mechanic Polymorph, not dispellable;
  - the Doll Swell is +100% size for a tell's 3 s, and the three tells are 3 s auras wearing the ruling 28 looks;
  - every hit is a resolve copy bound to spell_boss_mechanics_resolve in the right school, and the C++ gives each
    torment its settled shape: hidden (NoTelegraph), Weakened on Flames and Squeeze only, the Needle's zero-stack
    eligibility on Bound, the patch's one Weakened per player, the Hexed rider on Squeeze and the Hex of Agony burst;
  - the doll is a not-selectable, not-attackable helper on display 25017 with no heroic template, bound to the script
    the C++ registers;
  - 9236 is bound to boss_shadow_hunter_voshgajin_rework with SmartAI off, HealthModifier 75.751, DamageModifier 3.5
    and immunity set 1972;
  - the SQL rev removes the two Shadow Priests and gives her the four build spec lines (yells 14, the bind emote 41).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_spire_voshgajin.py
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import test_id_blocks as id_blocks  # noqa: E402
from lib.dsl import registry  # noqa: E402

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockSpire"
HEADER = MODULE_DIR / "VoshgajinLogic.h"
SCRIPT = MODULE_DIR / "boss_shadow_hunter_voshgajin_rework.cpp"
SQL_REV = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_voshgajin_blackrock_spire.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_spire"

SLICE = range(210060, 210090)
(BIND, BOUND, SWELL, FLAMES_TELL, NEEDLE_TELL, SQUEEZE_TELL, FLAMES_HIT, PATCH_HIT, NEEDLE_HIT, SQUEEZE_HIT, HEXED,
 HEX_OF_AGONY, HEX_BURST_HIT, PIN, NEEDLE_FLIGHT, HEX_SKULL) = range(210060, 210076)
VOSHGAJIN = 9236
DOLL = 300703

SCHOOL_NORMAL, SCHOOL_FIRE, SCHOOL_SHADOW = 1, 4, 32
SCHOOL_DAMAGE, APPLY_AURA = 2, 6
AURA_DUMMY, AURA_PERIODIC_DAMAGE, AURA_MOD_CONFUSE, AURA_TRANSFORM, AURA_MOD_SCALE = 4, 3, 5, 56, 61
DISPEL_MAGIC, DISPEL_CURSE = 1, 2
MECHANIC_POLYMORPH = 17
ATTR1_CHANNELED = 0x4
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
AURA_INTERRUPT_CHANGE_MAP = 0x00080000
UNIT_FLAG_NOT_ATTACKABLE = 0x2
UNIT_FLAG_NOT_SELECTABLE = 0x02000000
RESOLVE = "spell_boss_mechanics_resolve"
REFFLAT_PERIODIC = "spell_dungeon_refflat_periodic"

# The looks (ruling 28 for the tells; the stock picks of SP's Build spec "Visuals" for the rest).
LOOKS = {
    BIND: 13152,            # Puppet Strings 62377
    BOUND: 876,             # Curse of Blood 16098
    FLAMES_TELL: 11668,     # Voodoo Flames 54795 (ruling 28)
    NEEDLE_TELL: 11078,     # Crystal Spike Pre-visual 50442 (ruling 28)
    SQUEEZE_TELL: 8025,     # Shadow Prison 33071 (ruling 28)
    FLAMES_HIT: 143,        # Fire Blast: the burst's chest flash
    PATCH_HIT: 143,
    NEEDLE_HIT: 39,         # Gore
    SQUEEZE_HIT: 45,        # Shadow Burst
    HEXED: 2295,            # Hex 16097
    HEX_OF_AGONY: 10061,    # Hex of Agony 52647
    HEX_BURST_HIT: 45,
    PIN: 5287,              # Pin 50245
    NEEDLE_FLIGHT: 9061,    # Needle Spine 39835
    HEX_SKULL: 10061,
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


def _header_int(name: str) -> int:
    match = re.search(rf"\b{name}\s*=\s*(-?\d+)", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return int(match.group(1))


def _header_float(name: str) -> float:
    match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f?;", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return float(match.group(1))


def _header_pair(name: str) -> tuple[float, float]:
    match = re.search(rf"\b{name}\{{\s*(-?[\d.]+)f?,\s*(-?[\d.]+)f?\s*\}}", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return float(match.group(1)), float(match.group(2))


class VoshgajinDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = [e for e in reg.creature_template_edits if int(e["entry"]) == VOSHGAJIN]
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == DOLL}
        cls.models = [m for m in reg.creature_template_models if int(m["CreatureID"]) == DOLL]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(BIND, HEX_SKULL + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_spire", {"spell": mine, "creature": [DOLL]}), [])
        header_ids = {int(v) for v in re.findall(r"SPELL_VG_\w+\s*=\s*kSpellSlice\.first \+ (\d+)", self.header)}
        self.assertEqual({BIND + n for n in header_ids}, set(mine))
        # The stock Hex and Curse of Blood are retired from her kit, never re-declared.
        for retired in (16097, 16098):
            self.assertNotIn(retired, self.spells)

    def test_puppet_strings_is_a_channel_the_script_cuts(self):
        strings = self.spells[BIND]
        self.assertTrue(_raw(strings, "AttributesEx") & ATTR1_CHANNELED)
        self.assertEqual(strings["duration_ms"], 20000)
        self.assertGreater(strings["duration_ms"], _header_int("kBoundMs"))
        self.assertEqual(_raw(strings, "InterruptFlags"), 0)
        self.assertEqual(_raw(strings, "ChannelInterruptFlags"), 0)
        self.assertEqual(strings["dispel"], 0)
        self.assertEqual(strings["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertIn("doll->CastSpell(player, SPELL_VG_BIND, true)", self.cpp)
        self.assertIn("InterruptNonMeleeSpells(false, SPELL_VG_BIND)", self.cpp)

    def test_the_needle_skips_the_strings_not_the_curse(self):
        # R-1-A M2: a dispelled Bound player still stands at the Needle's far end; the skip keys on Puppet Strings
        # (not dispellable, the whole binding), never on the Curse.
        header = HEADER.read_text(encoding="utf-8")
        self.assertRegex(header, r"kNeedleSkipAura\s*=\s*SPELL_VG_BIND;")
        self.assertIn("e.auraSpell = kNeedleSkipAura;", self.cpp)
        self.assertNotIn("e.auraSpell = SPELL_VG_BOUND;", self.cpp)
        self.assertEqual(self.spells[BIND]["dispel"], 0)
        self.assertGreater(self.spells[BIND]["duration_ms"], _header_int("kBoundMs"))

    def test_the_impacts_come_from_the_shared_visuals(self):
        source = (PACKAGE / "voshgajin.py").read_text(encoding="utf-8")
        self.assertNotIn("_SV_", source)
        self.assertEqual(self.spells[BOUND]["raw_overrides"]["SpellVisualID_1"], 876)

    def test_bound_is_the_curse_of_pins(self):
        bound = self.spells[BOUND]
        self.assertEqual(bound["dispel"], DISPEL_CURSE)
        effect = bound["effect1"]
        self.assertEqual(effect["apply_aura"], AURA_PERIODIC_DAMAGE)
        self.assertEqual(effect["amplitude"], _header_int("kPinEveryMs"))
        self.assertEqual(effect["amplitude"], 2000)
        # 5% in hundredths, normal and heroic (EffectMiscValueB).
        self.assertEqual(effect["base_points"], int(_header_float("kPinPct") * 100))
        self.assertEqual(_raw(bound, "EffectMiscValueB_1"), 500)
        self.assertIn((BOUND, REFFLAT_PERIODIC), self.scripts)
        self.assertTrue(_raw(bound, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS)
        self.assertEqual(_raw(bound, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)
        self.assertEqual(bound["school"], SCHOOL_SHADOW)
        # 18 s unless the last torment lands later: the script sets the aura's length from the hold.
        self.assertEqual(_header_int("kBoundMs"), 18000)
        self.assertIn("aura->SetMaxDuration(static_cast<int32>(holdMs))", self.cpp)
        # Needle's eligibility reads its stacks: it is a cure target, and the descriptor lists it.
        self.assertIn("d.dispels.emplace_back(SPELL_VG_BOUND, 1)", self.cpp)

    def test_hex_of_agony_is_a_magic_dot(self):
        hex_ = self.spells[HEX_OF_AGONY]
        self.assertEqual(hex_["dispel"], DISPEL_MAGIC)
        self.assertEqual(hex_["duration_ms"], _header_int("kHexOfAgonyMs"))
        self.assertEqual(hex_["duration_ms"], 8000)
        effect = hex_["effect1"]
        self.assertEqual(effect["apply_aura"], AURA_PERIODIC_DAMAGE)
        self.assertEqual(effect["amplitude"], 1000)
        self.assertEqual(effect["base_points"], int(_header_float("kHexOfAgonyPct") * 100))
        self.assertEqual(_raw(hex_, "EffectMiscValueB_1"), 400)
        self.assertIn((HEX_OF_AGONY, REFFLAT_PERIODIC), self.scripts)
        self.assertEqual(_raw(hex_, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)
        # The descriptor: Magic dispel, priority 3, urgent 4 s before it ends, heroic only.
        self.assertRegex(self.cpp, r"if \(heroic\)\s*d\.dispels\.emplace_back\(SPELL_VG_HEX_OF_AGONY, 3, false, "
                                   r"Ms\(4000\)\)")

    def test_hexed_is_the_stock_hex_for_two_seconds(self):
        hexed = self.spells[HEXED]
        self.assertEqual(hexed["duration_ms"], _header_int("kHexedMs"))
        self.assertEqual(hexed["duration_ms"], 2000)
        self.assertEqual(hexed["mechanic"], MECHANIC_POLYMORPH)
        self.assertEqual(hexed["dispel"], 0)
        self.assertEqual(hexed["effect1"]["apply_aura"], AURA_TRANSFORM)
        self.assertEqual(hexed["effect1"]["misc_value"], 7552)
        self.assertEqual(hexed["effect2"]["apply_aura"], AURA_MOD_CONFUSE)
        self.assertFalse(hexed.get("attributes", 0) & 0x20000000)       # a break is a reward: not NO_IMMUNITIES
        self.assertEqual(_raw(hexed, "AuraInterruptFlags"), AURA_INTERRUPT_CHANGE_MAP)

    def test_the_swell_and_the_tells(self):
        swell = self.spells[SWELL]
        self.assertEqual(swell["effect1"]["apply_aura"], AURA_MOD_SCALE)
        self.assertEqual(swell["effect1"]["base_points"], 100)          # scale 2
        for spell_id in (SWELL, FLAMES_TELL, NEEDLE_TELL, SQUEEZE_TELL):
            self.assertEqual(self.spells[spell_id]["duration_ms"], _header_int("kTellMs"))
            self.assertEqual(self.spells[spell_id]["duration_ms"], 3000)
        for spell_id in (FLAMES_TELL, NEEDLE_TELL, SQUEEZE_TELL):
            self.assertEqual(self.spells[spell_id]["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertIn("doll->CastSpell(doll, SPELL_VG_DOLL_SWELL, true)", self.cpp)

    def test_hits_are_resolve_copies_in_their_schools(self):
        schools = {FLAMES_HIT: SCHOOL_FIRE, PATCH_HIT: SCHOOL_FIRE, NEEDLE_HIT: SCHOOL_NORMAL,
                   SQUEEZE_HIT: SCHOOL_SHADOW, HEX_BURST_HIT: SCHOOL_SHADOW}
        for spell_id, school in schools.items():
            hit = self.spells[spell_id]
            self.assertEqual(hit["effect1"]["type"], SCHOOL_DAMAGE, spell_id)
            self.assertEqual(hit["school"], school, spell_id)
            self.assertTrue(_raw(hit, "AttributesEx3") & ATTR3_IGNORE_CASTER_MODIFIERS, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts, spell_id)

    def test_the_torments_have_their_settled_shapes(self):
        cpp = self.cpp
        # No torment draws a marker (ruling 25): all three registrations are hidden.
        flames = re.search(r"Mechanic::RunOut\(me, player, kFlamesRadius, Ms\(kTellMs\)\);\s*ref\.([^;]*);", cpp)
        needle = re.search(r"Mechanic::Line\(me, BossMechanics::Anchor\(doll\), BossMechanics::Anchor\(player\), "
                           r"kNeedleWidth,\s*Ms\(kTellMs\)\);\s*ref\.([^;]*);", cpp)
        squeeze = re.search(r"Mechanic::Donut\(me, player, kSqueezeInner, kSqueezeOuter, Ms\(kTellMs\)\);\s*"
                            r"ref\.([^;]*);", cpp)
        self.assertIsNotNone(flames)
        self.assertIsNotNone(needle)
        self.assertIsNotNone(squeeze)
        for chain in (flames.group(1), needle.group(1), squeeze.group(1)):
            self.assertIn(".NoTelegraph()", chain)
        # Weakened on Flames and Squeeze, never on the Needle (its own penalty).
        self.assertIn(".Weakened()", flames.group(1))
        self.assertIn(".Weakened()", squeeze.group(1))
        self.assertNotIn("Weakened", needle.group(1))
        self.assertIn("Spell(SPELL_VG_FLAMES_HIT)", flames.group(1))
        self.assertIn("Spell(SPELL_VG_NEEDLE_HIT)", needle.group(1))
        self.assertIn("Spell(SPELL_VG_SQUEEZE_HIT)", squeeze.group(1))
        self.assertIn("Rider(SPELL_VG_HEXED)", squeeze.group(1))
        # The Needle never hits the bound player (the zero-stack eligibility on Puppet Strings, R-1-A M2).
        self.assertIn("Eligible(WithoutBound())", needle.group(1))
        self.assertRegex(cpp, r"e\.auraSpell = kNeedleSkipAura;\s*e\.minStacks = 0;\s*e\.maxStacks = 0;")
        # The patch: persistent 5 yd / 20 s / 1 s, one Weakened per player, marker kept.
        patch = re.search(r"Mechanic::Zone\(me, BossMechanics::Shapes::Circle\(at, kPatchRadius\), "
                          r"Ms\(kPatchTickMs\)\);\s*ref\.([^;]*);", cpp)
        self.assertIsNotNone(patch)
        self.assertIn("Persistent(Ms(kPatchMs), Ms(kPatchTickMs))", patch.group(1))
        self.assertIn("WeakenedOncePerPlayer()", patch.group(1))
        self.assertNotIn("NoTelegraph", patch.group(1))
        # The Bound player's own 10% (Flames and Needle), no Weakened, through RegistryHit.
        self.assertIn("HitBound(player, kFlamesBoundPct, SPELL_SCHOOL_FIRE, SPELL_VG_FLAMES_HIT)", cpp)
        self.assertIn("HitBound(player, kNeedleBoundPct, SPELL_SCHOOL_NORMAL, SPELL_VG_NEEDLE_HIT)", cpp)
        self.assertIn("spec.weakened = false;", cpp)
        self.assertEqual((_header_float("kFlamesBoundPct"), _header_float("kNeedleBoundPct")), (10.0, 10.0))
        # Numbers of the build spec.
        self.assertEqual(_header_pair("kFlamesPct"), (30.0, 35.0))
        self.assertEqual(_header_pair("kNeedlePct"), (40.0, 50.0))
        self.assertEqual(_header_pair("kSqueezePct"), (25.0, 30.0))
        self.assertEqual((_header_float("kFlamesRadius"), _header_float("kNeedleWidth")), (8.0, 4.0))
        self.assertEqual((_header_float("kSqueezeInner"), _header_float("kSqueezeOuter")), (5.0, 25.0))
        self.assertEqual((_header_float("kPatchRadius"), _header_float("kPatchPct")), (5.0, 10.0))
        self.assertEqual(_header_int("kPatchMs"), 20000)
        # Hex of Agony's burst: a registry RunOut on the carrier with the Hexed rider, cancelled when dispelled.
        self.assertRegex(cpp, r"Mechanic::RunOut\(me, player, kHexBurstRadius, Ms\(kHexOfAgonyMs\)\);\s*"
                              r"ref\.Damage\(kHexBurstPct\)[^;]*Rider\(SPELL_VG_HEXED\)")
        self.assertIn('"why=dispelled', cpp)

    def test_looks_are_the_visual_picks(self):
        for spell_id, visual in LOOKS.items():
            self.assertEqual(_raw(self.spells[spell_id], "SpellVisualID_1"), visual, spell_id)

    def test_the_doll_is_a_helper_on_the_ragdoll(self):
        self.assertIn(DOLL, self.creatures)
        doll = self.creatures[DOLL]
        self.assertEqual(doll["ScriptName"], "npc_brs_voodoo_doll")
        self.assertEqual(doll["faction"], 14)
        self.assertEqual(doll["unit_flags"] & (UNIT_FLAG_NOT_ATTACKABLE | UNIT_FLAG_NOT_SELECTABLE),
                         UNIT_FLAG_NOT_ATTACKABLE | UNIT_FLAG_NOT_SELECTABLE)
        self.assertEqual(doll["lootid"], 0)
        self.assertEqual(doll["DamageModifier"], 0.0)
        self.assertEqual(len(self.models), 1)
        self.assertEqual(self.models[0]["CreatureDisplayID"], 25017)
        self.assertEqual(self.models[0]["DisplayScale"], 1.0)
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_brs_voodoo_doll", self.cpp)
        self.assertRegex(self.header, r"kDollSpots[^;]*-124\.30f, -483\.93f, 25\.55f[^;]*-124\.50f, -480\.05f, 25\.62f")

    def test_vosh_gajin_is_bound(self):
        self.assertEqual(len(self.edits), 1)
        edit = self.edits[0]
        self.assertEqual(edit["ScriptName"], "boss_shadow_hunter_voshgajin_rework")
        self.assertEqual(edit["AIName"], "")
        self.assertEqual(edit["HealthModifier"], 75.751)
        self.assertEqual(edit["DamageModifier"], 3.5)
        self.assertEqual(edit["CreatureImmunitiesId"], 1972)
        self.assertEqual(edit["flags_extra"] & 0x1, 0x1)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_shadow_hunter_voshgajin_rework", self.cpp)
        # 174k on the level 58 paladin base 2,297.
        self.assertAlmostEqual(75.751 * 2297, 174_000, delta=100)

    def test_her_texts_and_the_removed_priests(self):
        text = SQL_REV.read_text(encoding="utf-8")
        rows = re.findall(r"^\(9236, (\d+), 0, '((?:[^']|'')*)', (\d+),", text, re.M)
        self.assertEqual([int(r[0]) for r in rows], [0, 1, 2, 3])
        types = {int(r[0]): int(r[2]) for r in rows}
        self.assertEqual(types, {0: 14, 1: 41, 2: 14, 3: 14})
        by_group = {int(r[0]): r[1] for r in rows}
        self.assertEqual(by_group[1], "%s binds the doll to $n!")
        self.assertIn("More pretty dolls for Vosh''gajin", by_group[0])
        self.assertIn("You break so slow", by_group[2])
        self.assertIn("who will play with them now", by_group[3])
        for name, group in (("YELL_VG_PULL", 0), ("EMOTE_VG_BIND", 1), ("YELL_VG_TWIN", 2), ("YELL_VG_DEATH", 3)):
            match = re.search(rf"{name}\s*=\s*(\d+)", self.header)
            self.assertIsNotNone(match, name)
            self.assertEqual(int(match.group(1)), group, name)
        # The two Shadow Priests (spawn guids 43550 / 43551, entry 9240) leave; the SmartAI rows are the S0 rev's.
        self.assertIn("DELETE FROM `creature` WHERE `id` = 9240 AND `guid` IN (43550, 43551);", text)
        self.assertNotIn("DELETE FROM `smart_scripts`", text)


if __name__ == "__main__":
    unittest.main()
