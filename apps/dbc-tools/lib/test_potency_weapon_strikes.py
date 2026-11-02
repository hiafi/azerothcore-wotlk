"""
Potency audit S3 / F14 / F6 / F5 (2026-11-01, stage P5): a weapon strike's percent and flat part must sit on potency, and
the strikes and helpers the audit named were migrated with their level-60 values kept.

  * `lint.check_weapon_potency` (fixtures): a weapon effect with no weapon_potency on the spell, or a hand-set flat part,
    is an error unless the id is in `lint.WEAPON_POTENCY_DEFERRED`; a deferral that stops being a finding is a report
    line, never an error.
  * The migrated spells, from the real class packages: no finding, the weapon percents, and the level-60 flat / tick
    values the old hand-set numbers gave (Multi-Shot 275, Felguard Cleave 62, Plague Strike 151, Blood Plague 23, Frost
    Fever 19).

The whole-tree run is `generate.py --check`.

Run: cd apps/dbc-tools && .venv/bin/python3 -m pytest lib/test_potency_weapon_strikes.py -q -p no:cacheprovider
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import dbcfmt, lint, source, spell_tables, state, trainer_state  # noqa: E402
from lib import potency as P  # noqa: E402
from lib.dsl import registry  # noqa: E402

_WEAPON = {"kind": "weapon", "total_potency": 100.0}
_FLAT = {"kind": "direct", "total_potency": 10.0}


def _entry(spell_id: int, **effects: dict) -> dict:
    entry = {"id": spell_id, "name": "Test"}
    entry.update(effects)
    return entry


class WeaponPotencyLintTest(unittest.TestCase):
    def test_percent_on_weapon_potency_is_clean(self):
        entry = _entry(900001, effect1={"type": 31, "base_points": 149, "die_sides": 1, "_potency": _WEAPON})
        self.assertEqual(lint.check_weapon_potency([entry], {}), [])

    def test_hand_typed_percent_is_an_error(self):
        entry = _entry(900002, effect1={"type": 31, "base_points": 149, "die_sides": 1})
        errors = lint.check_weapon_potency([entry], {})
        self.assertEqual(len(errors), 1)
        self.assertIn("spell 900002 (Test): no weapon_potency on the spell (effect 0 type 31)", errors[0])

    def test_zero_flat_beside_a_weapon_percent_is_clean(self):
        # The Aimed Shot / Unfair Advantage shape: NORMALIZED_WEAPON_DMG base -1 (value 0) then the percent.
        entry = _entry(
            900003, effect1={"type": 121, "base_points": -1, "die_sides": 1},
            effect2={"type": 31, "base_points": 49, "die_sides": 1, "_potency": _WEAPON},
        )
        self.assertEqual(lint.check_weapon_potency([entry], {}), [])

    def test_hand_set_flat_is_an_error_even_with_a_percent_on_potency(self):
        entry = _entry(
            900004, effect1={"type": 121, "base_points": 9, "die_sides": 1, "points_per_level": 2.39},
            effect2={"type": 31, "base_points": 48, "die_sides": 1, "_potency": _WEAPON},
        )
        errors = lint.check_weapon_potency([entry], {})
        self.assertEqual(len(errors), 1)
        self.assertIn("hand-set flat part", errors[0])
        self.assertNotIn("no weapon_potency", errors[0])

    def test_flat_on_sp_potency_is_clean(self):
        entry = _entry(
            900005, effect1={"type": 121, "base_points": 14, "die_sides": 1, "points_per_level": 5.9, "_potency": _FLAT},
            effect2={"type": 31, "base_points": 99, "die_sides": 1, "_potency": _WEAPON},
        )
        self.assertEqual(lint.check_weapon_potency([entry], {}), [])

    def test_flat_with_no_die_sides_counts_its_base_only(self):
        zero = _entry(900006, effect1={"type": 58, "base_points": 0, "die_sides": 0, "_potency": _WEAPON})
        flat = _entry(900007, effect1={"type": 58, "base_points": 31, "die_sides": 0})
        self.assertEqual(lint.check_weapon_potency([zero], {}), [])
        self.assertEqual(len(lint.check_weapon_potency([flat], {})), 1)

    def test_excluded_effect_is_not_flagged(self):
        entry = _entry(900008, effect1={"type": 58, "base_points": 77, "die_sides": 1, "_potency_excluded": "why"},
                       effect2={"type": 31, "base_points": 99, "die_sides": 1, "_potency": _WEAPON})
        self.assertEqual(lint.check_weapon_potency([entry], {}), [])

    def test_spell_without_weapon_effects_is_ignored(self):
        entry = _entry(900009, effect1={"type": 2, "base_points": 100, "die_sides": 1})
        self.assertEqual(lint.check_weapon_potency([entry], {}), [])

    def test_deferred_id_is_not_an_error_and_the_report_names_it(self):
        entry = _entry(900010, effect1={"type": 31, "base_points": 149, "die_sides": 1})
        self.assertEqual(lint.check_weapon_potency([entry], {900010: "later"}), [])
        report = lint.weapon_potency_report([entry], {900010: "later"})
        self.assertEqual(len(report), 1)
        self.assertTrue(report[0].startswith("deferred 900010"))
        self.assertIn("[later]", report[0])

    def test_stale_deferral_is_a_report_line_not_an_error(self):
        fixed = _entry(900011, effect1={"type": 31, "base_points": 149, "die_sides": 1, "_potency": _WEAPON})
        self.assertEqual(lint.check_weapon_potency([fixed], {900011: "later"}), [])
        report = lint.weapon_potency_report([fixed], {900011: "later"})
        self.assertEqual(len(report), 1)
        self.assertTrue(report[0].startswith("stale deferral 900011"))

    def test_deferred_ids_are_real_spell_ids(self):
        self.assertTrue(all(isinstance(k, int) and v for k, v in lint.WEAPON_POTENCY_DEFERRED.items()))


_PACKAGES: dict[str, object] = {}
_SPELLS: dict[str, dict[int, dict]] = {}


def _registry(class_name: str):
    if not _PACKAGES:
        _PACKAGES["ctx"] = dict(
            ids_cfg=source.load_ids(TOOL_ROOT / "source" / "ids.yaml"),
            trainer_index=trainer_state.load_trainer_index(),
            group_ids={key[0] for key in spell_tables.load_spell_table_index().live_keys("spell_group")},
            shapeshift=state.load_stock_rows(dbcfmt.SPELLSHAPESHIFTFORM),
            creature_rows={int(r["entry"]): r for r in spell_tables.load_creature_table_index().live_rows("creature_template")},
            live_data=spell_tables.load_dsl_live_data(),
        )
    if class_name not in _PACKAGES:
        ctx = _PACKAGES["ctx"]
        _PACKAGES[class_name] = registry.load_class_package(
            TOOL_ROOT / "source" / "classes" / class_name, ids_cfg=ctx["ids_cfg"], trainer_index=ctx["trainer_index"],
            existing_group_ids=ctx["group_ids"], shapeshift_index=ctx["shapeshift"],
            existing_creature_rows=ctx["creature_rows"], creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
            creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS, live_data=ctx["live_data"],
        )
    return _PACKAGES[class_name]


def _package(class_name: str) -> dict[int, dict]:
    if class_name not in _SPELLS:
        _SPELLS[class_name] = {int(e["id"]): e for e in _registry(class_name).spells}
    return _SPELLS[class_name]


def _level60(effect: dict) -> float:
    """The effect's value for a level-60 caster (a direct effect at its average roll)."""
    stash = {k: v for k, v in effect["_potency"].items() if k not in ("spell_level", "ticks")}
    resolved = P.ResolvedPotency(**stash)
    spell_level = int(effect["_potency"]["spell_level"])
    return P.simulate_value(resolved, 60, spell_level, roll=1.0 + resolved.variance_pct / 200.0)


def _weapon_percent(effect: dict) -> int:
    return int(effect["base_points"]) + 1  # the +1 is the DieSides 1 roll


# class -> (spell id, expected (effect index, weapon percent) list); every one must also be free of S3 findings.
PERCENTS = {
    "hunter": {2643: [(1, 100)]},
    "shaman": {60103: [(0, 110)], 32175: [(0, 100)], 32176: [(0, 100)], 202413: [(0, 100)], 202415: [(0, 100)]},
    "druid": {200429: [(0, 310)]},
    "warlock": {30213: [(0, 100)]},
    "warrior": {20240: [(0, 100)]},
    "rogue": {14251: [(0, 150)], 51675: [(1, 50)], 51677: [(1, 100)], 51723: [(0, 100)], 52874: [(0, 100)]},
    "deathknight": {45462: [(1, 49)]},
}


class MigratedStrikesTest(unittest.TestCase):
    def test_weapon_percents_and_no_findings(self):
        for class_name, spells in PERCENTS.items():
            package = _package(class_name)
            for spell_id, percents in spells.items():
                entry = package[spell_id]
                self.assertEqual(lint.check_weapon_potency([entry], {}), [], spell_id)
                for index, percent in percents:
                    effect = entry[f"effect{index + 1}"]
                    self.assertEqual(effect["_potency"]["kind"], "weapon", spell_id)
                    self.assertEqual(_weapon_percent(effect), percent, spell_id)

    def test_fan_of_knives_copies_share_one_percent(self):
        rogue = _package("rogue")
        percents = {sid: _weapon_percent(rogue[sid]["effect1"]) for sid in (51723, 52874, 204166, 204167)}
        self.assertEqual(len(set(percents.values())), 1, percents)

    def test_flat_parts_keep_their_level_60_values(self):
        # (class, spell, effect index, the old hand-set level-60 value, tolerance)
        for class_name, spell_id, index, old, tolerance in (
            ("hunter", 2643, 0, 275, 1.5),          # bp 0 + int(42 x 6.5645); a direct sp_potency 103
            ("warlock", 30213, 1, 62, 1.5),         # bp 31 + int(10 x 3.0667) + 1; sp_potency 23.2
            ("deathknight", 45462, 0, 151, 1.5),    # bp 9 + int(59 x 2.3899) + 1; sp_potency 56.4
        ):
            effect = _package(class_name)[spell_id][f"effect{index + 1}"]
            self.assertAlmostEqual(_level60(effect), old, delta=tolerance, msg=spell_id)

    def test_flat_parts_come_after_nothing_they_should_precede(self):
        hunter = _package("hunter")[2643]
        self.assertEqual((hunter["effect1"]["type"], hunter["effect2"]["type"]), (121, 31))  # flat first, percent second
        warlock = _package("warlock")[30213]
        self.assertEqual((warlock["effect1"]["type"], warlock["effect2"]["type"]), (31, 58))  # percent first, flat second

    def test_diseases_keep_their_tick_and_coefficient(self):
        dk = _package("deathknight")
        for spell_id, old_tick in ((55078, 23), (55095, 19)):
            effect = dk[spell_id]["effect1"]
            self.assertEqual(effect["apply_aura"], 3, spell_id)
            self.assertAlmostEqual(_level60(effect), old_tick, delta=0.5, msg=spell_id)
            self.assertAlmostEqual(effect["_potency"]["ap_coefficient"], 0.06325, places=4, msg=spell_id)
            self.assertEqual(effect["_potency"]["sp_coefficient"], 0.0, spell_id)
            self.assertEqual(effect["_potency"]["kind"], "periodic", spell_id)

    def test_stray_bonus_rows_are_unbound(self):
        # Multi-Shot's stray ap 0.2 and the Felguard Cleave ranks' ap 0.1429 (both inert on a weapon effect). Blood Plague /
        # Frost Fever are not unbound: the generator replaces their stock rows with its own (a removal would conflict).
        removed = {int(r["entry"]) for c in ("hunter", "warlock") for r in _registry(c).bonus_removals}
        self.assertTrue({2643, 30213, 30223} <= removed)
        declared = {int(r["entry"]) for c in ("deathknight",) for r in _registry(c).spell_bonus_data}
        self.assertTrue({55078, 55095} <= declared)
        self.assertFalse({55078, 55095} & {int(r["entry"]) for r in _registry("deathknight").bonus_removals})


if __name__ == "__main__":
    unittest.main()
