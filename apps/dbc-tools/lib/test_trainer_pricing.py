"""
Unit tests for `lib/trainer_pricing.py` - the class-trainer learn-level price curve
(`.agents/plans/trainer-cost-discount/trainer-cost-discount.PLAN.md`). The curve and row logic are tested directly;
the replay uses temp directories like `test_trainer_state.py`.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_trainer_pricing.py
"""

from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import generate  # noqa: E402
from lib import spell_tables, trainer_pricing, trainer_state  # noqa: E402

TRAINER_SPELL_DDL = (
    "CREATE TABLE `trainer_spell` (\n"
    "  `TrainerId` int unsigned NOT NULL,\n"
    "  `SpellId` int unsigned NOT NULL,\n"
    "  `MoneyCost` int unsigned NOT NULL DEFAULT '0',\n"
    "  `ReqSkillLine` int unsigned NOT NULL DEFAULT '0',\n"
    "  `ReqSkillRank` int unsigned NOT NULL DEFAULT '0',\n"
    "  `ReqAbility1` int unsigned NOT NULL DEFAULT '0',\n"
    "  `ReqAbility2` int unsigned NOT NULL DEFAULT '0',\n"
    "  `ReqAbility3` int unsigned NOT NULL DEFAULT '0',\n"
    "  `ReqLevel` tinyint unsigned NOT NULL DEFAULT '0',\n"
    "  `VerifiedBuild` int DEFAULT '0',\n"
    "  PRIMARY KEY (`TrainerId`,`SpellId`)\n"
    ") ENGINE=InnoDB;\n"
)
COLS = ", ".join(f"`{c}`" for c in trainer_pricing.TRAINER_SPELL_COLUMNS)


def row(trainer: int, spell: int, cost: int, level: int) -> dict:
    return {
        "TrainerId": trainer, "SpellId": spell, "MoneyCost": cost, "ReqSkillLine": 0, "ReqSkillRank": 0,
        "ReqAbility1": 0, "ReqAbility2": 0, "ReqAbility3": 0, "ReqLevel": level, "VerifiedBuild": 0,
    }


def insert_sql(*rows: dict) -> str:
    values = ",\n".join(
        "(" + ", ".join(str(r[c]) for c in trainer_pricing.TRAINER_SPELL_COLUMNS) + ")" for r in rows
    )
    return f"INSERT INTO `trainer_spell` ({COLS}) VALUES\n{values};\n"


CURVE = ((1, 10), (3, 10), (4, 20), (6, 40), (10, 100), (12, 160), (30, 3200), (40, 6000), (80, 144000))


def policy(overrides=None, priced=(212,)):
    return trainer_pricing.Policy(CURVE, overrides or {}, priced)


class CurveTest(unittest.TestCase):
    def test_anchors_are_exact_and_outside_is_clamped(self):
        for level, price in CURVE:
            self.assertEqual(trainer_pricing.curve_price(CURVE, level), price)
        self.assertEqual(trainer_pricing.curve_price(CURVE, 0), 10)
        self.assertEqual(trainer_pricing.curve_price(CURVE, -5), 10)
        self.assertEqual(trainer_pricing.curve_price(CURVE, 81), 144000)
        self.assertEqual(trainer_pricing.curve_price(CURVE, 255), 144000)

    def test_interpolates_with_1c_below_100c(self):
        self.assertEqual(trainer_pricing.curve_price(CURVE, 5), 30)   # 20 -> 40 over 2 levels
        c = ((1, 10), (4, 20), (10, 100))
        self.assertEqual(trainer_pricing.curve_price(c, 2), 13)   # 13.33 -> 13
        self.assertEqual(trainer_pricing.curve_price(c, 3), 17)   # 16.67 -> 17

    def test_step_boundaries_99_100_9999_10000(self):
        c = ((1, 98), (3, 100), (5, 9990), (7, 10010))
        self.assertEqual(trainer_pricing.curve_price(c, 2), 99)       # 99, 1c step, exact
        self.assertEqual(trainer_pricing.curve_price(c, 4), 5050)     # 5045 -> 10c step, half up
        self.assertEqual(trainer_pricing.curve_price(c, 6), 10000)    # 10000 exactly
        c2 = ((1, 100), (4, 103))
        self.assertEqual(trainer_pricing.curve_price(c2, 2), 100)     # 101 is >= 100c so the step is 10c
        c3 = ((1, 95), (3, 104))
        self.assertEqual(trainer_pricing.curve_price(c3, 2), 100)     # 99.5 -> step 1 -> 100
        c4 = ((1, 9990), (3, 10005))
        self.assertEqual(trainer_pricing.curve_price(c4, 2), 10000)   # 9997.5 -> 10c step -> 10000
        c5 = ((1, 10000), (3, 10250))
        self.assertEqual(trainer_pricing.curve_price(c5, 2), 10100)   # 10125 -> 1s step -> 10100
        c6 = ((1, 10000), (3, 10150))
        self.assertEqual(trainer_pricing.curve_price(c6, 2), 10100)   # 10075 -> 10100 (half up)

    def test_shipped_policy_loads_and_matches_the_handoff(self):
        pol = trainer_pricing.load_policy()
        expected = {1: 10, 4: 20, 5: 30, 6: 40, 8: 60, 10: 100, 11: 130, 20: 440, 24: 800, 25: 1200,
                    30: 3200, 40: 6000, 50: 12000, 55: 17000, 58: 20000, 60: 22000, 70: 50000, 80: 144000}
        for level, price in expected.items():
            self.assertEqual(pol.price_for(level, 1), price, level)
        self.assertEqual(pol.overrides, {})
        self.assertTrue({13, 18, 30, 200, 217} <= pol.priced_ids)
        self.assertNotIn(16, pol.priced_ids)

    def test_invalid_curves_raise(self):
        bad = {
            "empty": (),
            "equal levels": ((1, 10), (1, 20)),
            "decreasing levels": ((5, 10), (3, 20)),
            "decreasing prices": ((1, 20), (2, 10)),
            "zero price": ((1, 0), (2, 10)),
            "anchor off its rounding step": ((1, 9994), (3, 9996)),
            "anchor off the 1s step": ((1, 10000), (3, 10050)),
        }
        for name, curve in bad.items():
            with self.assertRaises(trainer_pricing.PricingPolicyError, msg=name):
                trainer_pricing.validate_curve(curve)

    def test_override_wins_over_curve(self):
        pol = policy(overrides={7: 12345})
        self.assertEqual(pol.price_for(10, 7), 12345)
        self.assertEqual(pol.price_for(10, 8), 100)
        with self.assertRaises(trainer_pricing.PricingPolicyError):
            policy(overrides={7: 0})


class PricedTrainerSpellsTest(unittest.TestCase):
    def _priced(self, declared=(), live=(), priced=(212,), removed=(), pol=None):
        as_map = lambda rows: {(r["TrainerId"], r["SpellId"]): r for r in rows}  # noqa: E731
        return trainer_pricing.priced_trainer_spells(
            list(declared), as_map(live), set(priced), set(removed), pol or policy(priced=priced),
        )

    def test_live_rows_of_a_priced_trainer_are_priced_by_level_keeping_other_columns(self):
        live = row(212, 100, 999999, 30)
        live["VerifiedBuild"] = 7
        rows = self._priced(live=[live])
        self.assertEqual(rows[0]["MoneyCost"], 3200)
        self.assertEqual(rows[0]["VerifiedBuild"], 7)

    def test_unlisted_trainer_untouched(self):
        rows = self._priced(live=[row(5, 100, 1000, 30)], declared=[row(5, 101, 777, 30)])
        self.assertEqual([(r["SpellId"], r["MoneyCost"]) for r in rows], [(101, 777)])  # declared honoured, live not

    def test_declared_money_cost_ignored_on_a_listed_trainer(self):
        rows = self._priced(declared=[row(212, 100, 500, 10)], live=[row(212, 100, 150000, 10)])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["MoneyCost"], 100)

    def test_declared_columns_beat_live_except_cost(self):
        declared = row(212, 100, 500, 40)
        rows = self._priced(declared=[declared], live=[row(212, 100, 1, 10)])
        self.assertEqual((rows[0]["ReqLevel"], rows[0]["MoneyCost"]), (40, 6000))

    def test_untrained_keys_are_excluded(self):
        rows = self._priced(
            declared=[row(212, 100, 500, 10)], live=[row(212, 101, 1000, 10)], removed=[(212, 100), (212, 101)],
        )
        self.assertEqual(rows, [])

    def test_override_applies_on_every_priced_trainer(self):
        pol = policy(overrides={100: 555}, priced=(212, 213))
        rows = self._priced(live=[row(212, 100, 1, 10), row(213, 100, 1, 50)], priced=(212, 213), pol=pol)
        self.assertEqual({r["MoneyCost"] for r in rows}, {555})


class LivePricedTrainerIdsTest(unittest.TestCase):
    def test_dead_listed_trainer_is_reported_and_skipped(self):
        class Idx:
            def trainer_problems(self, tid):
                return [] if tid == 212 else ["no spawn"]
        ids, skipped = trainer_pricing.live_priced_trainer_ids(policy(priced=(212, 213)), Idx())
        self.assertEqual(ids, {212})
        self.assertEqual(skipped, [(213, ["no spawn"])])


class ReplayFixture(unittest.TestCase):
    """Temp-dir SQL tree wired into `trainer_state`; holds no tests itself."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self._base, self._promoted, self._pending, self._modules = (
            root / "base", root / "promoted", root / "pending", root / "modules",
        )
        for d in (self._base, self._promoted, self._pending, self._modules):
            d.mkdir()
        (self._base / "trainer_spell.sql").write_text(TRAINER_SPELL_DDL)
        self._orig = (
            trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR,
            trainer_state.MODULES_DIR, trainer_state.PROGRESSION_CONF, trainer_state.PROGRESSION_CONF_DIST,
        )
        trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR = self._base, self._promoted
        trainer_state.PENDING_SQL_DIR, trainer_state.MODULES_DIR = self._pending, self._modules
        trainer_state.PROGRESSION_CONF = self._modules / "absent.conf"
        trainer_state.PROGRESSION_CONF_DIST = self._modules / "absent.conf.dist"

    def tearDown(self):
        (
            trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR,
            trainer_state.MODULES_DIR, trainer_state.PROGRESSION_CONF, trainer_state.PROGRESSION_CONF_DIST,
        ) = self._orig
        self._tmp.cleanup()

    def _seed(self, *keys):
        (self._promoted / "a_seed.sql").write_text(insert_sql(*[row(t, s, 1000, 30) for t, s in keys]))

    def _after(self, delete_sql: str) -> set:
        (self._promoted / "b_delete.sql").write_text(delete_sql)
        return set(trainer_pricing.replay_trainer_spells())


class ReplayTest(ReplayFixture):
    def test_and_ed_point_delete(self):
        self._seed((212, 1), (212, 2), (213, 1))
        self.assertEqual(
            self._after("DELETE FROM `trainer_spell` WHERE `TrainerId` = 212 AND `SpellId` = 1;\n"),
            {(212, 2), (213, 1)},
        )

    def test_between_delete(self):
        self._seed((199, 1), (200, 1), (217, 1), (218, 1))
        self.assertEqual(
            self._after("DELETE FROM `trainer_spell` WHERE `TrainerId` BETWEEN 200 AND 217;\n"), {(199, 1), (218, 1)},
        )

    def test_in_delete_on_one_column(self):
        self._seed((212, 1), (212, 2), (213, 2), (213, 3))
        self.assertEqual(
            self._after("DELETE FROM `trainer_spell` WHERE `SpellId` IN (1, 2);\n"), {(213, 3)},
        )

    def test_or_of_and_delete(self):
        self._seed((1, 71), (1, 72), (2, 71), (202, 71))
        sql = ("DELETE FROM `trainer_spell` WHERE (`TrainerId` = 1 AND `SpellId` = 71) "
               "OR (`TrainerId` = 202 AND `SpellId` = 71);\n")
        self.assertEqual(self._after(sql), {(1, 72), (2, 71)})

    def test_partial_column_insert_gets_schema_defaults(self):
        (self._promoted / "a.sql").write_text(
            "INSERT INTO `trainer_spell` (`TrainerId`, `SpellId`, `MoneyCost`, `ReqLevel`) VALUES (13, 5, 100, 1);\n"
        )
        self.assertEqual(trainer_pricing.replay_trainer_spells()[(13, 5)]["VerifiedBuild"], 0)

    def test_tuple_in_delete_still_works(self):
        self._seed((212, 1), (212, 2))
        self.assertEqual(
            self._after("DELETE FROM `trainer_spell` WHERE (`TrainerId`, `SpellId`) IN ((212, 1));\n"), {(212, 2)},
        )

    def test_update_with_in_filter(self):
        self._seed((212, 1), (212, 2), (212, 3))
        (self._promoted / "b_update.sql").write_text(
            "UPDATE `trainer_spell` SET `ReqAbility1` = 0 WHERE `SpellId` IN (1, 2);\n"
        )
        (self._promoted / "a_seed.sql").write_text(
            insert_sql(*[dict(row(212, s, 1000, 30), ReqAbility1=9) for s in (1, 2, 3)])
        )
        live = trainer_pricing.replay_trainer_spells()
        self.assertEqual({k[1]: v["ReqAbility1"] for k, v in live.items()}, {1: 0, 2: 0, 3: 9})

    def test_unsupported_statement_warns_and_never_silently_skips(self):
        self._seed((212, 1))
        (self._promoted / "b_odd.sql").write_text(
            "DELETE FROM `trainer_spell` WHERE `SpellId` IN (SELECT 1);\n"
            "UPDATE `trainer_spell` SET `MoneyCost` = `MoneyCost` * 2 WHERE `TrainerId` = 212;\n"
        )
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            live = trainer_pricing.replay_trainer_spells()
        self.assertEqual(set(live), {(212, 1)})
        text = out.getvalue()
        self.assertEqual(text.count("WARNING"), 2, text)
        self.assertIn("b_odd.sql", text)
        self.assertIn("SELECT 1", text)

    def test_second_run_emits_nothing(self):
        # Snapshot at arbitrary old prices; first run's generated file reprices by level; a second
        # run over everything (generated file counted as live) must emit nothing.
        (self._promoted / "snapshot.sql").write_text(
            insert_sql(row(212, 100, 999, 30), row(212, 101, 5, 10), row(212, 102, 77, 99))
        )
        pol = policy()
        live = trainer_pricing.replay_trainer_spells()
        priced = trainer_pricing.priced_trainer_spells([], live, {212}, set(), pol)
        first = generate._trainer_spells_to_emit(priced, live)
        self.assertEqual(sorted(r["MoneyCost"] for r in first), [100, 3200, 144000])
        keys = ", ".join(f"({r['TrainerId']}, {r['SpellId']})" for r in first)
        (self._pending / "rev_1.sql").write_text(
            spell_tables.GENERATED_MARKER + " - DO NOT hand-edit.\n"
            f"DELETE FROM `trainer_spell` WHERE (`TrainerId`, `SpellId`) IN ({keys});\n" + insert_sql(*first)
        )
        live2 = trainer_pricing.replay_trainer_spells()
        priced2 = trainer_pricing.priced_trainer_spells([], live2, {212}, set(), pol)
        second = generate._trainer_spells_to_emit(priced2, live2)
        self.assertEqual(second, [])

    def test_declared_row_second_run_is_a_no_op(self):
        declared = row(212, 100, 500, 10)
        pol = policy()
        (self._promoted / "snapshot.sql").write_text(insert_sql(row(212, 100, 100, 10)))
        live = trainer_pricing.replay_trainer_spells()
        priced = trainer_pricing.priced_trainer_spells([declared], live, {212}, set(), pol)
        self.assertEqual(generate._trainer_spells_to_emit(priced, live), [])


class FakeIndex:
    def __init__(self, dead=()):
        self.dead = set(dead)

    def trainer_problems(self, tid):
        return ["no spawn"] if tid in self.dead else []


class PricedWiringTest(ReplayFixture):
    """`generate._priced_trainer_spells` end to end over a temp-dir fixture."""

    def _run(self, declared=(), removed=(), dead=()):
        dsl = {"trainer_spells": list(declared), "trainer_removals": [
            {"TrainerId": t, "SpellId": s} for t, s in removed]}
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rows = generate._priced_trainer_spells(dsl, FakeIndex(dead))
        return rows, out.getvalue()

    def test_prices_live_rows_declared_rows_and_honours_removals(self):
        (self._promoted / "s.sql").write_text(insert_sql(
            row(212, 1, 999, 30), row(212, 2, 999, 10), row(5, 3, 999, 30), row(212, 4, 999, 10)))
        rows, out = self._run(declared=[row(212, 9, 7, 40)], removed=[(212, 4)])
        got = {(r["TrainerId"], r["SpellId"]): r["MoneyCost"] for r in rows}
        self.assertEqual(got, {(212, 1): 3200, (212, 2): 100, (212, 9): 6000})
        self.assertEqual(out, "")

    def test_listed_but_dead_trainer_warns_is_skipped_and_keeps_declared_money_cost(self):
        (self._promoted / "s.sql").write_text(insert_sql(row(212, 1, 999, 30), row(213, 1, 999, 30)))
        rows, out = self._run(declared=[row(213, 9, 777, 40)], dead=[213])
        got = {(r["TrainerId"], r["SpellId"]): r["MoneyCost"] for r in rows}
        self.assertEqual(got, {(212, 1): 3200, (213, 9): 777})
        self.assertIn("WARNING: trainer pricing: TrainerId 213", out)
        self.assertNotIn("TrainerId 212 is in", out)

    def test_wiring_second_run_emits_nothing(self):
        (self._promoted / "s.sql").write_text(insert_sql(row(212, 1, 999, 30), row(212, 2, 5, 10)))
        first, _ = self._run()
        self.assertEqual(len(first), 2)
        keys = ", ".join(f"({r['TrainerId']}, {r['SpellId']})" for r in first)
        (self._pending / "rev_1.sql").write_text(
            spell_tables.GENERATED_MARKER + " - DO NOT hand-edit.\n"
            f"DELETE FROM `trainer_spell` WHERE (`TrainerId`, `SpellId`) IN ({keys});\n" + insert_sql(*first)
        )
        second, out = self._run()
        self.assertEqual((second, out), ([], ""))


class ReplayHardeningTest(ReplayFixture):
    def _warnings(self, sql: str) -> str:
        (self._promoted / "b_odd.sql").write_text(sql)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            trainer_pricing.replay_trainer_spells()
        return out.getvalue()

    def test_invisible_statements_warn(self):
        self._seed((212, 1))
        for sql in (
            "DELETE FROM trainer_spell WHERE `TrainerId` = 212;\n",
            "INSERT IGNORE INTO `trainer_spell` (`TrainerId`, `SpellId`) VALUES (1, 2);\n",
            "UPDATE `trainer_spell` AS ts SET `ReqLevel` = 1 WHERE ts.`TrainerId` = 212;\n",
            "TRUNCATE `trainer_spell`;\n",
            "TRUNCATE TABLE trainer_spell;\n",
        ):
            self.assertEqual(self._warnings(sql).count("WARNING"), 1, sql)

    def test_comments_and_recognised_forms_do_not_warn(self):
        self._seed((212, 1))
        self.assertEqual(self._warnings("-- DELETE FROM trainer_spell WHERE x\nSELECT 1;\n"), "")
        self.assertEqual(
            self._warnings("DELETE FROM `trainer_spell` WHERE `TrainerId` = 212 AND `SpellId` = 1;\n"), ""
        )

    def test_update_guard_on_a_non_key_column_is_honoured_by_both_paths(self):
        (self._promoted / "a.sql").write_text(insert_sql(row(212, 1, 500, 30), row(212, 2, 999, 30)))
        (self._promoted / "b.sql").write_text(
            "UPDATE `trainer_spell` SET `ReqLevel` = 7 WHERE `TrainerId` = 212 AND `MoneyCost` = 999;\n"
            "UPDATE `trainer_spell` SET `ReqAbility1` = 9 WHERE `TrainerId` IN (212) AND `MoneyCost` = 999;\n"
        )
        live = trainer_pricing.replay_trainer_spells()
        self.assertEqual((live[(212, 1)]["ReqLevel"], live[(212, 1)]["ReqAbility1"]), (30, 0))
        self.assertEqual((live[(212, 2)]["ReqLevel"], live[(212, 2)]["ReqAbility1"]), (7, 9))

    def test_where_on_an_omitted_column_matches_its_default(self):
        (self._promoted / "a.sql").write_text(
            "INSERT INTO `trainer_spell` (`TrainerId`, `SpellId`, `MoneyCost`, `ReqLevel`) VALUES (13, 5, 100, 1);\n"
            "DELETE FROM `trainer_spell` WHERE `TrainerId` = 13 AND `VerifiedBuild` = 0;\n"
        )
        self.assertEqual(trainer_pricing.replay_trainer_spells(), {})

    def test_between_update_and_non_key_only_update(self):
        self._seed((199, 1), (200, 1), (217, 1))
        (self._promoted / "b.sql").write_text(
            "UPDATE `trainer_spell` SET `ReqLevel` = 5 WHERE `TrainerId` BETWEEN 200 AND 217;\n"
        )
        live = trainer_pricing.replay_trainer_spells()
        self.assertEqual({k[0]: v["ReqLevel"] for k, v in live.items()}, {199: 30, 200: 5, 217: 5})
        warned = self._warnings("UPDATE `trainer_spell` SET `ReqLevel` = 1 WHERE `ReqLevel` = 5;\n")
        self.assertEqual(warned.count("WARNING"), 1)


class CreatureReplayTest(unittest.TestCase):
    """The widened shared replay, through `load_replayed_table_rows` on a `creature_template` fixture."""

    DDL = (
        "CREATE TABLE `creature_template` (\n  `entry` int unsigned NOT NULL,\n"
        "  `ExperienceModifier` float NOT NULL DEFAULT '1',\n  `flags_extra` int unsigned NOT NULL DEFAULT '0',\n"
        "  `faction` int NOT NULL DEFAULT '0',\n  PRIMARY KEY (`entry`)\n) ENGINE=InnoDB;\n"
    )
    COLS = ("entry", "ExperienceModifier", "flags_extra", "faction")

    def test_in_update_expression_update_and_omitted_columns(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            base, promoted = root / "base", root / "promoted"
            for d in (base, promoted, root / "pending", root / "modules"):
                d.mkdir()
            (base / "creature_template.sql").write_text(self.DDL)
            (promoted / "a.sql").write_text(
                "INSERT INTO `creature_template` (`entry`, `ExperienceModifier`, `flags_extra`) VALUES\n"
                "(1, 1, 0), (2, 1, 0), (3, 1, 0);\n"
                "INSERT INTO `creature_template` (`entry`) VALUES (4);\n"
            )
            (promoted / "b.sql").write_text(
                "UPDATE `creature_template` SET `ExperienceModifier` = 0 WHERE `entry` IN (1, 2);\n"
                "UPDATE `creature_template` SET `ExperienceModifier` = 1, `flags_extra` = `flags_extra` | 64 "
                "WHERE `entry` IN (1, 2);\n"
                "UPDATE `creature_template` SET `flags_extra` = `flags_extra` & ~64 "
                "WHERE `entry` = 2 AND `flags_extra` = 64;\n"
                "DELETE FROM `creature_template` WHERE `entry` BETWEEN 3 AND 3;\n"
            )
            orig = (trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR,
                    trainer_state.MODULES_DIR)
            trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR = base, promoted
            trainer_state.PENDING_SQL_DIR, trainer_state.MODULES_DIR = root / "pending", root / "modules"
            try:
                rows = {
                    r["entry"]: r for r in
                    trainer_state.load_replayed_table_rows("creature_template", self.COLS, ("entry",))
                }
            finally:
                (trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR,
                 trainer_state.MODULES_DIR) = orig
        self.assertEqual((rows[1]["ExperienceModifier"], rows[1]["flags_extra"]), (1, 64))
        self.assertEqual((rows[2]["ExperienceModifier"], rows[2]["flags_extra"]), (1, 0))
        self.assertNotIn(3, rows)
        self.assertNotIn("flags_extra", rows[4])  # omitted columns stay omitted without fill_missing


if __name__ == "__main__":
    unittest.main()
