"""
Healing sim stage HS0 data guards (.agents/plans/healing-sim/healing-sim.STAGE-HS0-HANDOFF.md, tasks A and C).

Loads the real `source/npcs/` files and asserts on the declared Sim Raid Boss (900015-900017) and on the BUILT rows of the two
damage spells (202900 Sim Damage Pulse, 202901 Sim Pin Hit): the ids, the attribute bits that make them always-hit, no-crit,
unresisted, unthreatening hits that still honour damage-taken auras, absorbs and the victim's procs, and the one bit
(SPELL_ATTR7_DONT_CAUSE_SPELL_PUSHBACK) that tells them apart. Bits that must stay off are asserted off.

Run directly:

    apps/dbc-tools/.venv/bin/python3 -m pytest apps/dbc-tools/lib/test_healsim_hs0.py -q
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import build, source, spell_tables  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.reuse import ReuseContext  # noqa: E402

NPC_DIR = TOOL_ROOT / "source" / "npcs"

BOSS_IDS = (900015, 900016, 900017)
BOSS_LEVELS = {900015: 60, 900016: 70, 900017: 80}
PULSE, PIN = 202900, 202901

# SharedDefines.h (names verified in the spell file's docstring)
ATTR0_NO_ACTIVE_DEFENSE = 0x00200000
ATTR1_NO_REDIRECTION = 0x00000008
ATTR1_NO_THREAT = 0x00000400
ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004
ATTR2_CANT_CRIT = 0x20000000
ATTR3_NOT_A_PROC = 0x00000200
ATTR3_SUPPRESS_CASTER_PROCS = 0x00010000
ATTR3_ALWAYS_HIT = 0x00040000
ATTR3_TREAT_AS_PERIODIC = 0x02000000
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
ATTR4_NO_CAST_LOG = 0x00000001
ATTR4_IGNORE_DAMAGE_TAKEN_MODIFIERS = 0x00000100
ATTR7_DONT_CAUSE_SPELL_PUSHBACK = 0x00000040

SPELL_EFFECT_SCHOOL_DAMAGE = 2
TARGET_UNIT_TARGET_ENEMY = 6
SCHOOL_ARCANE = 64
DMG_CLASS_MAGIC = 1

CREATURE_TYPE_FLAG_BOSS_MOB = 0x4
FLAGS_EXTRA_DISALLOWED = 0x2 | 0x2000          # CIVILIAN, CANNOT_ENTER_COMBAT
UNIT_FLAG_NON_ATTACKABLE = 0x00000002
UNIT_FLAG_IMMUNE_TO_PC = 0x00000100
UNIT_FLAG_NOT_SELECTABLE = 0x02000000


def _load_npcs() -> registry.Registry:
    return registry.load_class_file(
        NPC_DIR / "training_dummies.py",
        ids_cfg=source.load_ids(TOOL_ROOT / "source" / "ids.yaml"),
        existing_creature_rows={},
        creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
        creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS,
    )


def _load_spells() -> tuple[dict, dict]:
    reg = registry.load_class_file(NPC_DIR / "healsim_spells.py", ids_cfg=source.load_ids(TOOL_ROOT / "source" / "ids.yaml"))
    ids_cfg = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
    reuse = ReuseContext({}, ids_cfg)
    entries = {int(e["id"]): e for e in reg.spells}
    rows = {int(e["id"]): build.build_spell_row(e, reuse) for e in reg.spells}
    return entries, rows


_NPCS = _load_npcs()
_ENTRIES, _ROWS = _load_spells()
_BOSSES = {int(row["entry"]): row for row in _NPCS.creature_templates if int(row["entry"]) in BOSS_IDS}
_MODELS = [m for m in _NPCS.creature_template_models if int(m["CreatureID"]) in BOSS_IDS]


class SimRaidBossTest(unittest.TestCase):
    def test_exactly_the_three_reserved_ids_are_declared(self):
        self.assertEqual(sorted(_BOSSES), list(BOSS_IDS))
        ours = {int(r["entry"]) for r in _NPCS.creature_templates if r["ScriptName"] == "npc_healsim_boss"}
        self.assertEqual(sorted(ours), list(BOSS_IDS))

    def test_levels_name_and_script(self):
        for entry, row in _BOSSES.items():
            self.assertEqual((row["minlevel"], row["maxlevel"]), (BOSS_LEVELS[entry],) * 2, entry)
            self.assertEqual(row["name"], "Sim Raid Boss")
            self.assertEqual(row["ScriptName"], "npc_healsim_boss")

    def test_hostile_and_attackable(self):
        for entry, row in _BOSSES.items():
            self.assertEqual(row["faction"], 14, entry)
            blocked = UNIT_FLAG_NON_ATTACKABLE | UNIT_FLAG_IMMUNE_TO_PC | UNIT_FLAG_NOT_SELECTABLE
            self.assertEqual(row["unit_flags"] & blocked, 0, entry)
            self.assertEqual(row["flags_extra"] & FLAGS_EXTRA_DISALLOWED, 0, entry)
            self.assertEqual(row["npcflag"], 0, entry)

    def test_boss_like(self):
        for entry, row in _BOSSES.items():
            self.assertEqual(row["rank"], 3, entry)
            self.assertTrue(row["type_flags"] & CREATURE_TYPE_FLAG_BOSS_MOB, entry)

    def test_huge_health_that_never_regenerates(self):
        for entry, row in _BOSSES.items():
            self.assertEqual(row["RegenHealth"], 0, entry)
            self.assertGreaterEqual(row["HealthModifier"], 23809.5, entry)

    def test_never_melees_or_aggroes_by_itself(self):
        for entry, row in _BOSSES.items():
            self.assertEqual(row["DamageModifier"], 0, entry)
            self.assertEqual(row["detection_range"], 0, entry)

    def test_creature_type_is_deliberate_not_inherited(self):
        for entry, row in _BOSSES.items():
            self.assertEqual(row["type"], 5, entry)       # Giant, not the dummies' 9 / mechanical

    def test_boss_immunity_set_and_one_model_each(self):
        for entry, row in _BOSSES.items():
            self.assertEqual(row["CreatureImmunitiesId"], -362, entry)
        self.assertEqual(sorted(int(m["CreatureID"]) for m in _MODELS), list(BOSS_IDS))


class SimDamageSpellTest(unittest.TestCase):
    def test_only_the_reserved_ids_are_declared(self):
        self.assertEqual(sorted(_ROWS), [PULSE, PIN])

    def test_single_enemy_school_damage_effect(self):
        for sid, row in _ROWS.items():
            self.assertEqual(row["Effect_1"], SPELL_EFFECT_SCHOOL_DAMAGE, sid)
            self.assertEqual((row["Effect_2"], row["Effect_3"]), (0, 0), sid)
            self.assertEqual(row["ImplicitTargetA_1"], TARGET_UNIT_TARGET_ENEMY, sid)
            self.assertEqual(row["ImplicitTargetB_1"], 0, sid)
            self.assertEqual(row["EffectBasePoints_1"], 0, sid)
            self.assertEqual(row["EffectRealPointsPerLevel_1"], 0, sid)
            self.assertEqual(row["EffectBonusMultiplier_1"], 0, sid)

    def test_magic_class_arcane_school_instant_free_and_unrestricted(self):
        for sid, row in _ROWS.items():
            self.assertEqual(row["SchoolMask"], SCHOOL_ARCANE, sid)
            self.assertEqual(row["DefenseType"], DMG_CLASS_MAGIC, sid)
            self.assertEqual(row["CastingTimeIndex"], 1, sid)
            self.assertEqual((row["RecoveryTime"], row["CategoryRecoveryTime"], row["StartRecoveryTime"]), (0, 0, 0), sid)
            self.assertEqual((row["ManaCost"], row["ManaCostPct"], row["PowerType"]), (0, 0, 0), sid)
            self.assertEqual(row["Speed"], 0, sid)
            self.assertEqual(row["EquippedItemClass"], -1, sid)
            self.assertEqual(row["SpellClassSet"], 0, sid)
            self.assertEqual(row["SpellLevel"], 0, sid)

    def test_never_misses_never_crits_never_resisted_no_threat_no_los(self):
        for sid, row in _ROWS.items():
            self.assertTrue(row["Attributes"] & ATTR0_NO_ACTIVE_DEFENSE, sid)
            self.assertTrue(row["AttributesEx"] & ATTR1_NO_THREAT, sid)
            self.assertTrue(row["AttributesEx"] & ATTR1_NO_REDIRECTION, sid)
            self.assertTrue(row["AttributesEx2"] & ATTR2_CANT_CRIT, sid)
            self.assertTrue(row["AttributesEx2"] & ATTR2_IGNORE_LINE_OF_SIGHT, sid)
            self.assertTrue(row["AttributesEx3"] & ATTR3_ALWAYS_HIT, sid)
            self.assertTrue(row["AttributesEx4"] & ATTR4_NO_CAST_LOG, sid)

    def test_caster_modifiers_ignored_and_triggered_cast_still_procs_the_victim(self):
        for sid, row in _ROWS.items():
            self.assertTrue(row["AttributesEx3"] & ATTR3_IGNORE_CASTER_MODIFIERS, sid)
            self.assertTrue(row["AttributesEx3"] & ATTR3_NOT_A_PROC, sid)

    def test_bits_that_would_break_the_contract_stay_off(self):
        for sid, row in _ROWS.items():
            # SUPPRESS_CASTER_PROCS clears canEffectTrigger, so the victim's taken-damage procs would not fire
            self.assertFalse(row["AttributesEx3"] & ATTR3_SUPPRESS_CASTER_PROCS, sid)
            # TREAT_AS_PERIODIC removes pushback (and changes the proc type) - pushback is the pulse's whole point
            self.assertFalse(row["AttributesEx3"] & ATTR3_TREAT_AS_PERIODIC, sid)
            # "Deals fixed damage": would skip the damage-taken multipliers that must still apply
            self.assertFalse(row["AttributesEx4"] & ATTR4_IGNORE_DAMAGE_TAKEN_MODIFIERS, sid)

    def test_only_the_pin_hit_suppresses_pushback(self):
        self.assertFalse(_ROWS[PULSE]["AttributesEx7"] & ATTR7_DONT_CAUSE_SPELL_PUSHBACK)
        self.assertTrue(_ROWS[PIN]["AttributesEx7"] & ATTR7_DONT_CAUSE_SPELL_PUSHBACK)

    def test_the_two_spells_differ_only_in_name_and_the_pushback_bit(self):
        a, b = dict(_ROWS[PULSE]), dict(_ROWS[PIN])
        diff = {k for k in a if a[k] != b[k]}
        self.assertEqual(diff, {"ID", "Name_Lang_enUS", "AttributesEx7"})

    def test_no_custom_attr_or_script_declared(self):
        reg = registry.load_class_file(NPC_DIR / "healsim_spells.py")
        self.assertEqual(reg.custom_attrs, [])
        self.assertEqual(reg.spell_script_names, [])

    def test_range_is_unlimited(self):
        for sid, entry in _ENTRIES.items():
            self.assertGreaterEqual(entry["range_yards"], 50000, sid)


if __name__ == "__main__":
    unittest.main()
