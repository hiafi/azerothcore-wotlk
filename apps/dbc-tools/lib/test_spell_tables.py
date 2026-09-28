"""
Unit tests for `lib/spell_tables.py` and the three registry helpers it
emits for (`scripted_by`/`bonus_coefficients`/`procs_on` in
`lib/dsl/registry.py`). Same shape as `test_trainer_state.py`: temp
directories stand in for the base dump + migrations so the "already live,
don't re-emit" diff is exercised against real parsed SQL, not mocks.

Run directly:

    python3 apps/dbc-tools/lib/test_spell_tables.py
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import dbcfmt, spell_tables, sql_dump, trainer_state  # noqa: E402
from lib.dsl import registry  # noqa: E402

CLASS_FILE = '''
from lib.dsl.registry import bonus_coefficients, procs_on, scripted_by, spell

meteor = spell(id=200095, name="Meteor", school=4, cooldown_ms=45000)
scripted_by(meteor, "spell_mage_meteor")
scripted_by(12654, "spell_mage_ignite_dot", "spell_mage_ignite_display")
bonus_coefficients(meteor, direct=0.3, dot=0.15)
procs_on(200098, proc_flags=0x10000, family_name=3, family_mask=(0x2, 0, 0), chance=100, cooldown_ms=2500)
'''

BASE_SQL = {
    "spell_script_names": (
        "CREATE TABLE `spell_script_names` (\n"
        "  `spell_id` int NOT NULL,\n"
        "  `ScriptName` char(64) NOT NULL\n"
        ") ENGINE=InnoDB;\n"
    ),
    "spell_bonus_data": (
        "CREATE TABLE `spell_bonus_data` (\n"
        "  `entry` int unsigned NOT NULL DEFAULT '0',\n"
        "  `direct_bonus` float NOT NULL DEFAULT '0',\n"
        "  `dot_bonus` float NOT NULL DEFAULT '0',\n"
        "  `ap_bonus` float NOT NULL DEFAULT '0',\n"
        "  `ap_dot_bonus` float NOT NULL DEFAULT '0',\n"
        "  `comments` varchar(255) DEFAULT NULL,\n"
        "  PRIMARY KEY (`entry`)\n"
        ") ENGINE=InnoDB;\n"
    ),
    "spell_proc": (
        "CREATE TABLE `spell_proc` (\n"
        + "".join(f"  `{c}` int NOT NULL DEFAULT '0',\n" for c in spell_tables.SPELL_PROC_COLUMNS)
        + "  PRIMARY KEY (`SpellId`)\n"
        ") ENGINE=InnoDB;\n"
    ),
    # WP-T (PLAN B11/§5.0): the four plain (non-DBC) new tables - CREATE TABLEs mirror
    # data/sql/base/db_world/*.sql exactly (see spell_tables.py's own column-tuple comment).
    "spell_linked_spell": (
        "CREATE TABLE `spell_linked_spell` (\n"
        "  `spell_trigger` int NOT NULL,\n"
        "  `spell_effect` int NOT NULL DEFAULT '0',\n"
        "  `type` tinyint unsigned NOT NULL DEFAULT '0',\n"
        "  `comment` text NOT NULL,\n"
        "  UNIQUE KEY `trigger_effect_type` (`spell_trigger`,`spell_effect`,`type`)\n"
        ") ENGINE=InnoDB;\n"
    ),
    "spell_group": (
        "CREATE TABLE `spell_group` (\n"
        "  `id` int unsigned NOT NULL DEFAULT '0',\n"
        "  `spell_id` int NOT NULL,\n"
        "  PRIMARY KEY (`id`,`spell_id`)\n"
        ") ENGINE=InnoDB;\n"
    ),
    "spell_group_stack_rules": (
        "CREATE TABLE `spell_group_stack_rules` (\n"
        "  `group_id` int unsigned NOT NULL DEFAULT '0',\n"
        "  `stack_rule` tinyint NOT NULL DEFAULT '0',\n"
        "  `description` varchar(150) NOT NULL DEFAULT '',\n"
        "  PRIMARY KEY (`group_id`)\n"
        ") ENGINE=InnoDB;\n"
    ),
    "spell_custom_attr": (
        "CREATE TABLE `spell_custom_attr` (\n"
        "  `spell_id` int unsigned NOT NULL DEFAULT '0',\n"
        "  `attributes` int unsigned NOT NULL DEFAULT '0',\n"
        "  PRIMARY KEY (`spell_id`)\n"
        ") ENGINE=InnoDB;\n"
    ),
    # Column *names* only matter for parse_create_table_columns (types are never read back out of
    # a CREATE TABLE by this tool) - synthesized from lib.dbcfmt.SPELLSHAPESHIFTFORM rather than
    # transcribing the real 35-column base file a second time.
    "spellshapeshiftform_dbc": (
        "CREATE TABLE `spellshapeshiftform_dbc` (\n"
        + "".join(f"  `{c}` int NOT NULL DEFAULT '0',\n" for c in dbcfmt.SPELLSHAPESHIFTFORM.columns)
        + "  PRIMARY KEY (`ID`)\n"
        ") ENGINE=InnoDB;\n"
    ),
}

WP_T_IDS_CFG = {"spell_group": {"start": 1200, "end": 1299}}

WP_T_CLASS_FILE = '''
from lib.dsl.registry import linked_spell, spell_group, spell_group_rule, custom_attr, unbind_script

linked_spell(200326, 57865, 2)
linked_spell(-200326, -57865, 0)
spell_group(1200, 50171, 50172)
spell_group_rule(1200, 1, "test group")
custom_attr(200425, 1)
unbind_script(69366, "spell_dru_moonkin_form_passive")
'''


def _load_wp_t_class(source: str = WP_T_CLASS_FILE) -> dict:
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "druid.py"
        path.write_text(source)
        reg = registry.load_class_file(
            path, ids_cfg=WP_T_IDS_CFG, existing_group_ids={1054, 1016},
        )
    return {k: getattr(reg, k) for k in registry.MERGE_KEYS}


def _shapeshift_row(form_id: int, **overrides) -> dict:
    """A full spellshapeshiftform_dbc row, the shape `shapeshift_form()` (lib/dsl/registry.py)
    produces - built directly rather than via the real registry helper + a real extracted
    `SpellShapeshiftForm.dbc`, so this stays portable across a checkout that hasn't extracted one
    (see that module's `ShapeshiftFormTest` in test_dsl_registry.py for the registry-level,
    mocked-index coverage of the actual merge logic)."""
    row = {c: 0 for c in dbcfmt.SPELLSHAPESHIFTFORM.columns}
    row["ID"] = form_id
    row["id"] = form_id
    row.update(overrides)
    return row


def _load_class(source: str) -> dict:
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "mage.py"
        path.write_text(source)
        reg = registry.load_class_file(path)
    return {k: getattr(reg, k) for k in registry.MERGE_KEYS}


class RegistryHelpersTest(unittest.TestCase):
    def setUp(self):
        self.dsl = _load_class(CLASS_FILE)

    def test_scripted_by_one_row_per_name_with_composite_id(self):
        rows = self.dsl["spell_script_names"]
        self.assertEqual(
            [(r["spell_id"], r["ScriptName"]) for r in rows],
            [(200095, "spell_mage_meteor"), (12654, "spell_mage_ignite_dot"), (12654, "spell_mage_ignite_display")],
        )
        self.assertEqual(rows[0]["id"], "200095:spell_mage_meteor")

    def test_bonus_coefficients_defaults_comment_to_spell_name(self):
        (row,) = self.dsl["spell_bonus_data"]
        self.assertEqual(row["entry"], 200095)
        self.assertEqual((row["direct_bonus"], row["dot_bonus"], row["ap_bonus"]), (0.3, 0.15, 0.0))
        self.assertEqual(row["comments"], "Meteor")

    def test_procs_on_splits_family_mask_into_three_columns(self):
        (row,) = self.dsl["spell_procs"]
        self.assertEqual(row["SpellId"], 200098)
        self.assertEqual((row["SpellFamilyMask0"], row["SpellFamilyMask1"], row["SpellFamilyMask2"]), (2, 0, 0))
        self.assertEqual((row["Chance"], row["Cooldown"], row["ProcFlags"]), (100.0, 2500, 0x10000))

    def test_helpers_outside_load_raise(self):
        with self.assertRaises(RuntimeError):
            registry.scripted_by(1, "x")
        with self.assertRaises(RuntimeError):
            registry.bonus_coefficients(1, direct=1.0)
        with self.assertRaises(RuntimeError):
            registry.procs_on(1, proc_flags=1)

    def test_scripted_by_rejects_empty_or_overlong_names(self):
        with self.assertRaises(ValueError):
            _load_class('from lib.dsl.registry import scripted_by\nscripted_by(1)\n')
        with self.assertRaises(ValueError):
            _load_class(f'from lib.dsl.registry import scripted_by\nscripted_by(1, "{"x" * 65}")\n')

    def test_duplicate_binding_across_files_raises(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ("a.py", "b.py"):
                (Path(d) / name).write_text('from lib.dsl.registry import scripted_by\nscripted_by(5, "s")\n')
            with self.assertRaises(registry.DuplicateIdError):
                registry.load_classes_dir(Path(d))


class SpellTableIndexTest(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        base = Path(self._tmp.name) / "base"
        promoted = Path(self._tmp.name) / "promoted"
        pending = Path(self._tmp.name) / "pending"
        for d in (base, promoted, pending):
            d.mkdir()
        self._promoted = promoted
        for table, sql in BASE_SQL.items():
            (base / f"{table}.sql").write_text(sql)
        self._orig = (trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR)
        trainer_state.BASE_SQL_DIR = base
        trainer_state.PROMOTED_SQL_DIR = promoted
        trainer_state.PENDING_SQL_DIR = pending
        self.dsl = _load_class(CLASS_FILE)

    def tearDown(self):
        (trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR) = self._orig
        self._tmp.cleanup()

    def _blocks(self) -> list[str]:
        return spell_tables.render_blocks(spell_tables.load_spell_table_index(), self.dsl)

    def test_nothing_live_emits_all_three_tables(self):
        blocks = self._blocks()
        self.assertEqual(len(blocks), 3)
        self.assertIn("DELETE FROM `spell_script_names` WHERE (`spell_id`, `ScriptName`) IN "
                      "((12654, 'spell_mage_ignite_display'), (12654, 'spell_mage_ignite_dot'), "
                      "(200095, 'spell_mage_meteor'));", blocks[0])
        self.assertIn("INSERT INTO `spell_bonus_data`", blocks[1])
        self.assertIn("(200095, 0.3, 0.15, 0.0, 0.0, 'Meteor')", blocks[1])
        self.assertIn("DELETE FROM `spell_proc` WHERE (`SpellId`) IN ((200098));", blocks[2])

    def test_identical_live_rows_are_not_re_emitted(self):
        (self._promoted / "live.sql").write_text(
            "INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES "
            "(200095, 'spell_mage_meteor'), (12654, 'spell_mage_ignite_dot'), (12654, 'spell_mage_ignite_display');\n"
            "INSERT INTO `spell_bonus_data` (`entry`, `direct_bonus`, `dot_bonus`, `ap_bonus`, `ap_dot_bonus`, `comments`) "
            "VALUES (200095, 0.3, 0.15, 0, 0, 'Meteor');\n"
        )
        blocks = self._blocks()
        self.assertEqual(len(blocks), 1)  # only spell_proc still has anything to say
        self.assertIn("spell_proc", blocks[0])

    def test_changed_coefficient_is_re_emitted(self):
        (self._promoted / "live.sql").write_text(
            "INSERT INTO `spell_bonus_data` (`entry`, `direct_bonus`, `dot_bonus`, `ap_bonus`, `ap_dot_bonus`, `comments`) "
            "VALUES (200095, 0.25, 0.15, 0, 0, 'Meteor');\n"
        )
        blocks = self._blocks()
        self.assertTrue(any("spell_bonus_data" in b and "0.3, 0.15" in b for b in blocks))

    def test_partial_column_live_row_compares_on_declared_columns(self):
        # A hand-written migration that omitted the ap_* columns (defaults 0)
        # still counts as identical to a declaration with ap=0.
        (self._promoted / "live.sql").write_text(
            "INSERT INTO `spell_bonus_data` (`entry`, `direct_bonus`, `dot_bonus`, `comments`) "
            "VALUES (200095, 0.3, 0.15, 'Meteor');\n"
        )
        blocks = self._blocks()
        self.assertFalse(any("spell_bonus_data" in b for b in blocks))


GENERATED_HEADER = spell_tables.GENERATED_MARKER + " — DO NOT hand-edit.\n"


class PruneTest(unittest.TestCase):
    """The prune pass: rows an earlier generated run emitted that the source
    no longer declares. See .agents/plans/dbc-tools-prune-pass/."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self._base, self._promoted, self._pending = root / "base", root / "promoted", root / "pending"
        for d in (self._base, self._promoted, self._pending):
            d.mkdir()
        for table, sql in BASE_SQL.items():
            (self._base / f"{table}.sql").write_text(sql)
        self._orig = (trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR)
        trainer_state.BASE_SQL_DIR = self._base
        trainer_state.PROMOTED_SQL_DIR = self._promoted
        trainer_state.PENDING_SQL_DIR = self._pending
        self.dsl = _load_class(CLASS_FILE)

    def tearDown(self):
        (trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR) = self._orig
        self._tmp.cleanup()

    def _write(self, name: str, body: str, generated: bool = True):
        (self._promoted / name).write_text((GENERATED_HEADER if generated else "") + body)

    def _prune(self):
        return spell_tables.render_prune_blocks(spell_tables.load_spell_table_index(), self.dsl)

    # The real case this was built for: a renamed script leaves the old
    # (spell_id, ScriptName) pair behind, plus a retired procs_on row.
    def test_orphaned_rows_are_pruned(self):
        self._write("gen.sql",
            "INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES "
            "(200095, 'spell_mage_meteor'), (200095, 'spell_mage_meteor_old');\n")
        blocks, report = self._prune()
        self.assertEqual(len(blocks), 1)
        self.assertIn("DELETE FROM `spell_script_names` WHERE (`spell_id`, `ScriptName`) IN "
                      "((200095, 'spell_mage_meteor_old'));", blocks[0])
        # still-declared row untouched
        self.assertNotIn("'spell_mage_meteor')", blocks[0].split("IN (")[1])
        self.assertTrue(any("removing spell_script_names" in line for line in report))

    def test_declared_rows_are_never_pruned(self):
        self._write("gen.sql",
            "INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES "
            "(200095, 'spell_mage_meteor'), (12654, 'spell_mage_ignite_dot'), "
            "(12654, 'spell_mage_ignite_display');\n")
        blocks, report = self._prune()
        self.assertEqual(blocks, [])
        self.assertEqual([l for l in report if "removing" in l], [])

    # Provenance: an identical orphan in a hand-written migration is not ours.
    def test_hand_written_migration_rows_are_not_pruned(self):
        self._write("hand.sql",
            "INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES "
            "(200095, 'spell_mage_meteor_old');\n", generated=False)
        blocks, report = self._prune()
        self.assertEqual(blocks, [])
        self.assertEqual([l for l in report if "removing" in l], [])

    # Safety rule 1: a past run overrode a stock row; deleting leaves a hole.
    def test_base_dump_overlap_is_reported_not_deleted(self):
        (self._base / "spell_proc.sql").write_text(
            BASE_SQL["spell_proc"]
            + "INSERT INTO `spell_proc` (`SpellId`) VALUES (12345);\n")
        self._write("gen.sql", "INSERT INTO `spell_proc` (`SpellId`) VALUES (12345);\n")
        blocks, report = self._prune()
        self.assertEqual(blocks, [])
        self.assertTrue(any("NOT removing spell_proc" in line and "12345" in line for line in report))

    # Safety rule 2: zero declarations + a history means the source didn't load.
    def test_circuit_breaker_refuses_to_empty_a_table(self):
        self._write("gen.sql",
            "INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES (200095, 'a'), (7, 'b');\n")
        blocks, report = spell_tables.render_prune_blocks(
            spell_tables.load_spell_table_index(), {})
        self.assertEqual(blocks, [])
        self.assertTrue(any("SKIPPED spell_script_names" in line for line in report))

    def test_delete_block_renders_ints_not_floats(self):
        self._write("gen.sql", "INSERT INTO `spell_proc` (`SpellId`) VALUES (200098), (99999);\n")
        blocks, _ = self._prune()
        self.assertIn("DELETE FROM `spell_proc` WHERE (`SpellId`) IN ((99999));", blocks[0])
        self.assertNotIn(".0", blocks[0])

    # spell_proc's "this spell and every rank in its chain" negative-id rows
    # are the real-world instance of safety rule 1 (three such rows are
    # currently overridden in this repo: -14531, -45234, -47516).
    def test_negative_spell_id_overriding_stock_is_not_pruned(self):
        (self._base / "spell_proc.sql").write_text(
            BASE_SQL["spell_proc"]
            + "INSERT INTO `spell_proc` (`SpellId`) VALUES (-47516);\n")
        self._write("gen.sql", "INSERT INTO `spell_proc` (`SpellId`) VALUES (-47516);\n")
        blocks, report = self._prune()
        self.assertEqual(blocks, [])
        self.assertTrue(any("NOT removing spell_proc" in l and "-47516" in l for l in report))

    def test_key_sort_tolerates_none_and_mixed_types(self):
        from lib import sql_out
        self.assertEqual(
            sql_out.stable_key_sort([(2.0, "b"), (None, "a"), (1.0, "z"), (2.0, "a")]),
            [(None, "a"), (1.0, "z"), (2.0, "a"), (2.0, "b")])

    # The regression this replay exists for: once a prune has emitted its
    # DELETE into a generated file, a later run must see the row as gone
    # rather than re-reporting it forever.
    def test_already_pruned_row_is_not_reported_again(self):
        self._write("01_gen.sql",
            "INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES "
            "(200095, 'spell_mage_meteor'), (200095, 'spell_mage_meteor_old');\n")
        blocks, report = self._prune()
        self.assertEqual(len(blocks), 1)  # first run: prunes the orphan

        # Simulate that prune having been written out as the next generated file.
        self._write("02_gen.sql",
            "DELETE FROM `spell_script_names` WHERE (`spell_id`, `ScriptName`) IN "
            "((200095, 'spell_mage_meteor_old'));\n")
        blocks, report = self._prune()
        self.assertEqual(blocks, [])
        self.assertEqual([l for l in report if "removing" in l], [])

    # A DELETE+INSERT block (render_generic_table_block) must not read as a
    # net removal - the INSERT immediately puts the row back.
    def test_delete_then_insert_in_same_file_keeps_the_row(self):
        self._write("gen.sql",
            "DELETE FROM `spell_script_names` WHERE (`spell_id`, `ScriptName`) IN "
            "((200095, 'spell_mage_meteor_old'));\n"
            "INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES "
            "(200095, 'spell_mage_meteor_old');\n")
        blocks, _ = self._prune()
        self.assertEqual(len(blocks), 1)
        self.assertIn("spell_mage_meteor_old", blocks[0])

    # Single-column DELETE against a two-column-keyed table removes every
    # matching row (the prefix case in _matching_keys).
    def test_single_column_delete_removes_all_matching_keys(self):
        self._write("gen.sql",
            "INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES "
            "(4242, 'a'), (4242, 'b');\n"
            "DELETE FROM `spell_script_names` WHERE `spell_id` IN (4242);\n")
        blocks, report = self._prune()
        self.assertEqual(blocks, [])
        self.assertEqual([l for l in report if "removing" in l], [])

    def test_spell_proc_delete_replay(self):
        self._write("gen.sql",
            "INSERT INTO `spell_proc` (`SpellId`) VALUES (777);\n"
            "DELETE FROM `spell_proc` WHERE (`SpellId`) IN ((777));\n")
        blocks, report = self._prune()
        self.assertEqual(blocks, [])

    # Safety: a shape the replay can't read must shrink the prune, not guess.
    def test_unparsed_delete_shape_disables_prune_for_that_table(self):
        self._write("gen.sql",
            "INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES (200095, 'orphan');\n"
            "DELETE FROM `spell_script_names` WHERE `ScriptName` LIKE 'spell_%';\n")
        blocks, report = self._prune()
        self.assertEqual(blocks, [])


# ---------------------------------------------------------------------------
# WP-T (.agents/plans/druid-rework/druid-rework.WP-T-HANDOFF.md, PLAN B11/§5.0):
# the five new declared tables (emit/rerun/prune, via the same SPELL_TABLES
# machinery as spell_script_names/spell_bonus_data/spell_proc) and the four
# declared-removal helpers (a separate mechanism - see render_removal_blocks).
# ---------------------------------------------------------------------------


class NewDeclaredTablesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        base = Path(self._tmp.name) / "base"
        promoted = Path(self._tmp.name) / "promoted"
        pending = Path(self._tmp.name) / "pending"
        for d in (base, promoted, pending):
            d.mkdir()
        self._promoted = promoted
        for table, sql in BASE_SQL.items():
            (base / f"{table}.sql").write_text(sql)
        self._orig = (trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR)
        trainer_state.BASE_SQL_DIR = base
        trainer_state.PROMOTED_SQL_DIR = promoted
        trainer_state.PENDING_SQL_DIR = pending
        self.dsl = _load_wp_t_class()

    def tearDown(self):
        (trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR) = self._orig
        self._tmp.cleanup()

    def _blocks(self) -> list[str]:
        return spell_tables.render_blocks(spell_tables.load_spell_table_index(), self.dsl)

    def test_nothing_live_emits_all_four_plain_tables(self):
        # shapeshift_form isn't declared by WP_T_CLASS_FILE (needs a real extracted stock DBC,
        # covered separately in test_dsl_registry.py's ShapeshiftFormTest) - the other four are.
        blocks = self._blocks()
        self.assertEqual(len(blocks), 4)
        joined = "\n".join(blocks)
        self.assertIn("INSERT INTO `spell_linked_spell`", joined)
        self.assertIn("(200326, 57865, 2,", joined)
        self.assertIn("(-200326, -57865, 0,", joined)  # negative ids round-trip
        self.assertIn("INSERT INTO `spell_group`", joined)
        self.assertIn("(1200, 50171)", joined)
        self.assertIn("INSERT INTO `spell_group_stack_rules`", joined)
        self.assertIn("(1200, 1, 'test group')", joined)
        self.assertIn("INSERT INTO `spell_custom_attr`", joined)
        self.assertIn("(200425, 1)", joined)

    def test_rerun_with_unchanged_source_emits_nothing(self):
        header = spell_tables.GENERATED_MARKER + " -- DO NOT hand-edit.\n"
        (self._promoted / "gen.sql").write_text(header + "\n\n".join(self._blocks()) + "\n")
        self.assertEqual(self._blocks(), [])

    def test_changed_value_is_re_emitted(self):
        header = spell_tables.GENERATED_MARKER + " -- DO NOT hand-edit.\n"
        (self._promoted / "gen.sql").write_text(header + "\n\n".join(self._blocks()) + "\n")
        self.dsl = _load_wp_t_class(WP_T_CLASS_FILE.replace("custom_attr(200425, 1)", "custom_attr(200425, 2)"))
        blocks = self._blocks()
        self.assertTrue(any("spell_custom_attr" in b and "(200425, 2)" in b for b in blocks))


class RemovalBlocksTest(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        base = Path(self._tmp.name) / "base"
        promoted = Path(self._tmp.name) / "promoted"
        pending = Path(self._tmp.name) / "pending"
        for d in (base, promoted, pending):
            d.mkdir()
        self._promoted = promoted
        for table, sql in BASE_SQL.items():
            (base / f"{table}.sql").write_text(sql)
        # A live row for the removal helpers to actually find (see the typo-guard tests below for
        # the "doesn't exist anywhere" case).
        (base / "spell_script_names.sql").write_text(
            BASE_SQL["spell_script_names"]
            + "INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES "
            "(69366, 'spell_dru_moonkin_form_passive');\n"
        )
        # The removal typo guard reads mod-progression phase SQL too - point it at an empty
        # modules dir so the real repo's phase files can't leak into these tests.
        modules = Path(self._tmp.name) / "modules"
        modules.mkdir()
        self._modules = modules
        self._orig = (
            trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR,
            trainer_state.MODULES_DIR, trainer_state.PROGRESSION_CONF, trainer_state.PROGRESSION_CONF_DIST,
        )
        trainer_state.BASE_SQL_DIR = base
        trainer_state.PROMOTED_SQL_DIR = promoted
        trainer_state.PENDING_SQL_DIR = pending
        trainer_state.MODULES_DIR = modules
        trainer_state.PROGRESSION_CONF = modules / "mod_progression.conf"
        trainer_state.PROGRESSION_CONF_DIST = modules / "mod_progression.conf.dist"
        trainer_state.PROGRESSION_CONF.write_text("Progression.Phase = 2\n")

    def tearDown(self):
        (
            trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR,
            trainer_state.MODULES_DIR, trainer_state.PROGRESSION_CONF, trainer_state.PROGRESSION_CONF_DIST,
        ) = self._orig
        self._tmp.cleanup()

    def _phase_trainer_spell(self, phase: int, trainer_id: int, spell_id: int) -> None:
        # The shape of mod-progression's phase_NN-trainer_spell.sql (@TrainerId-relative rows).
        sql_dir = self._modules / "mod-progression" / "src" / f"phase_{phase:02}" / "sql"
        sql_dir.mkdir(parents=True)
        (sql_dir / f"phase_{phase:02}-trainer_spell.sql").write_text(
            "SET @TrainerId := 200;\n"
            "INSERT INTO `trainer_spell` (`TrainerId`, `SpellId`, `ReqLevel`) VALUES\n"
            f"(@TrainerId+{trainer_id - 200}, {spell_id}, 10);\n"
        )

    def test_live_removal_is_emitted_and_reported(self):
        blocks, report = spell_tables.render_removal_blocks(_load_wp_t_class())
        self.assertEqual(len(blocks), 1)
        self.assertIn(
            "DELETE FROM `spell_script_names` WHERE (`spell_id`, `ScriptName`) IN "
            "((69366, 'spell_dru_moonkin_form_passive'));",
            blocks[0],
        )
        self.assertTrue(any("removal: spell_script_names" in l and "69366" in l for l in report))
        self.assertFalse(any(l.startswith("WARNING:") for l in report))

    def test_removal_emitted_once_then_silent_on_rerun(self):
        blocks, _ = spell_tables.render_removal_blocks(_load_wp_t_class())
        header = spell_tables.GENERATED_MARKER + " -- DO NOT hand-edit.\n"
        (self._promoted / "gen.sql").write_text(header + "\n\n".join(blocks) + "\n")
        blocks2, report2 = spell_tables.render_removal_blocks(_load_wp_t_class())
        self.assertEqual(blocks2, [])
        self.assertEqual(report2, [])

    def test_unknown_key_gets_a_warning_but_is_still_emitted(self):
        dsl = _load_wp_t_class(
            'from lib.dsl.registry import unbind_script\n'
            'unbind_script(999999, "spell_that_never_existed")\n'
        )
        blocks, report = spell_tables.render_removal_blocks(dsl)
        self.assertEqual(len(blocks), 1)  # still emitted - the DELETE is a harmless no-op
        self.assertTrue(any(l.startswith("WARNING:") and "999999" in l for l in report))

    def test_declare_and_remove_conflict_raises(self):
        dsl = _load_wp_t_class(
            'from lib.dsl.registry import scripted_by, unbind_script, spell\n'
            'meteor = spell(id=200095, name="Meteor", school=4)\n'
            'scripted_by(meteor, "spell_mage_meteor")\n'
            'unbind_script(meteor, "spell_mage_meteor")\n'
        )
        with self.assertRaises(spell_tables.DeclareAndRemoveConflictError):
            spell_tables.render_removal_blocks(dsl)

    def test_no_removals_declared_is_a_silent_no_op(self):
        dsl = _load_wp_t_class('from lib.dsl.registry import linked_spell\nlinked_spell(1, 2)\n')
        blocks, report = spell_tables.render_removal_blocks(dsl)
        self.assertEqual((blocks, report), ([], []))

    # Regression test (review, 2026-09-23): load_removed_keys used to treat *any* matching-shape
    # DELETE as proof of a past removal - including the DELETE that always precedes a declared
    # table's own INSERT (render_generic_table_block's normal idempotent-rerun shape). That meant
    # a key first declared (DELETE-then-INSERT) in one run, then later switched to a removal
    # (unbind_script) in a subsequent run, was misread as "already removed" from the very first
    # run's own DELETE half of its declare - so the real removal never got emitted.
    def test_declare_then_later_remove_across_two_runs_still_emits_the_removal(self):
        declare_dsl = _load_wp_t_class(
            'from lib.dsl.registry import scripted_by, spell\n'
            'meteor = spell(id=200095, name="Meteor", school=4)\n'
            'scripted_by(meteor, "spell_mage_meteor")\n'
        )
        declared_blocks = spell_tables.render_blocks(spell_tables.load_spell_table_index(), declare_dsl)
        header = spell_tables.GENERATED_MARKER + " -- DO NOT hand-edit.\n"
        (self._promoted / "01_declare.sql").write_text(header + "\n\n".join(declared_blocks) + "\n")

        # A later run: the design changed, scripted_by() is gone, unbind_script() replaces it.
        remove_dsl = _load_wp_t_class(
            'from lib.dsl.registry import unbind_script\nunbind_script(200095, "spell_mage_meteor")\n'
        )
        blocks, report = spell_tables.render_removal_blocks(remove_dsl)
        self.assertEqual(len(blocks), 1)
        self.assertIn(
            "DELETE FROM `spell_script_names` WHERE (`spell_id`, `ScriptName`) IN "
            "((200095, 'spell_mage_meteor'));",
            blocks[0],
        )
        self.assertTrue(any("removal: spell_script_names" in l and "200095" in l for l in report))

        # Promoting that removal (marker moves to line 2 - see _is_generated) makes a further
        # rerun of the same unbind_script() declaration silent, same as the simpler case above.
        (self._promoted / "01_declare.sql").unlink()
        (self._promoted / "02_removed.sql").write_text(
            "-- DB update 01 -> 02\n" + header + "\n\n".join(blocks) + "\n"
        )
        blocks2, report2 = spell_tables.render_removal_blocks(_load_wp_t_class(
            'from lib.dsl.registry import unbind_script\nunbind_script(200095, "spell_mage_meteor")\n'
        ))
        self.assertEqual((blocks2, report2), ([], []))

    def test_live_keys_by_table_is_used_instead_of_rescanning_when_given(self):
        # An empty override for spell_script_names must be trusted over what's actually on disk -
        # proves the pre-loaded map takes priority instead of always re-scanning.
        dsl = _load_wp_t_class(
            'from lib.dsl.registry import unbind_script\n'
            'unbind_script(69366, "spell_dru_moonkin_form_passive")\n'
        )
        blocks, report = spell_tables.render_removal_blocks(dsl, live_keys_by_table={"spell_script_names": set()})
        self.assertEqual(len(blocks), 1)
        self.assertTrue(any(l.startswith("WARNING:") for l in report))  # "live" set was empty, so it warns

    def test_removal_of_a_later_phase_row_names_the_phase_not_a_typo(self):
        # Progression.Phase is 2 (setUp): phase_07's row isn't live yet, so the plain typo guard
        # would call it nonexistent - it's real, and phase 7 will re-add it after this DELETE.
        self._phase_trainer_spell(7, 200, 469)
        dsl = _load_wp_t_class('from lib.dsl.registry import untrain\nuntrain(469, [200])\n')
        blocks, report = spell_tables.render_removal_blocks(dsl)
        self.assertEqual(len(blocks), 1)  # still emitted
        warnings = [l for l in report if l.startswith("WARNING:")]
        self.assertEqual(len(warnings), 1)
        self.assertIn("phase_07", warnings[0])
        self.assertNotIn("check for a typo", warnings[0])

    def test_removal_of_an_applied_phase_row_gets_a_fresh_db_note(self):
        self._phase_trainer_spell(0, 208, 2060)
        dsl = _load_wp_t_class('from lib.dsl.registry import untrain\nuntrain(2060, [208])\n')
        blocks, report = spell_tables.render_removal_blocks(dsl)
        self.assertEqual(len(blocks), 1)
        self.assertFalse(any(l.startswith("WARNING:") for l in report))
        self.assertTrue(any(l.startswith("note:") and "phase_00" in l and "fresh world DB" in l for l in report))


class ShapeshiftFormEmissionTest(unittest.TestCase):
    """spellshapeshiftform_dbc through the same SpellTableIndex/render_blocks machinery as every
    other declared table - see _shapeshift_row's docstring for why this doesn't need a real
    extracted SpellShapeshiftForm.dbc the way the registry-level merge test does."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        base = Path(self._tmp.name) / "base"
        promoted = Path(self._tmp.name) / "promoted"
        pending = Path(self._tmp.name) / "pending"
        for d in (base, promoted, pending):
            d.mkdir()
        self._promoted = promoted
        (base / "spellshapeshiftform_dbc.sql").write_text(BASE_SQL["spellshapeshiftform_dbc"])
        self._orig = (trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR)
        trainer_state.BASE_SQL_DIR = base
        trainer_state.PROMOTED_SQL_DIR = promoted
        trainer_state.PENDING_SQL_DIR = pending

    def tearDown(self):
        (trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR) = self._orig
        self._tmp.cleanup()

    def _dsl(self, combat_round_time=3500):
        return {"shapeshift_forms": [_shapeshift_row(5, CombatRoundTime=combat_round_time, Name_Lang_enUS="Bear Form")]}

    def _blocks(self, dsl):
        return spell_tables.render_blocks(spell_tables.load_spell_table_index(), dsl)

    def test_full_override_row_is_emitted(self):
        blocks = self._blocks(self._dsl())
        self.assertEqual(len(blocks), 1)
        self.assertIn("DELETE FROM `spellshapeshiftform_dbc` WHERE (`ID`) IN ((5));", blocks[0])
        self.assertIn("3500", blocks[0])

    def test_rerun_with_unchanged_source_emits_nothing(self):
        header = spell_tables.GENERATED_MARKER + " -- DO NOT hand-edit.\n"
        (self._promoted / "gen.sql").write_text(header + "\n\n".join(self._blocks(self._dsl())) + "\n")
        self.assertEqual(self._blocks(self._dsl()), [])

    def test_changed_value_is_re_emitted(self):
        header = spell_tables.GENERATED_MARKER + " -- DO NOT hand-edit.\n"
        (self._promoted / "gen.sql").write_text(header + "\n\n".join(self._blocks(self._dsl())) + "\n")
        blocks = self._blocks(self._dsl(combat_round_time=4000))
        self.assertTrue(any("4000" in b for b in blocks))


class IsGeneratedTest(unittest.TestCase):
    """Regression coverage (review, 2026-09-23): every real promoted file in
    data/sql/updates/db_world/ starts with a `-- DB update X -> Y` header line that
    apps/ci/ci-pending-sql.sh's promotion step always prepends, pushing GENERATED_MARKER from
    line 1 to line 2 - _is_generated used to check only line 1."""

    def test_marker_on_line_one_is_recognized(self):
        with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as f:
            f.write(spell_tables.GENERATED_MARKER + " -- DO NOT hand-edit.\nSELECT 1;\n")
            path = Path(f.name)
        try:
            self.assertTrue(spell_tables._is_generated(path))
        finally:
            path.unlink()

    def test_marker_on_line_two_after_promotion_header_is_recognized(self):
        with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as f:
            f.write(
                "-- DB update 2026_09_23_00 -> 2026_09_23_01\n"
                + spell_tables.GENERATED_MARKER + " -- DO NOT hand-edit.\nSELECT 1;\n"
            )
            path = Path(f.name)
        try:
            self.assertTrue(spell_tables._is_generated(path))
        finally:
            path.unlink()

    def test_marker_on_line_three_is_not_recognized(self):
        with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as f:
            f.write("-- one\n-- two\n" + spell_tables.GENERATED_MARKER + "\n")
            path = Path(f.name)
        try:
            self.assertFalse(spell_tables._is_generated(path))
        finally:
            path.unlink()

    def test_hand_written_file_is_not_recognized(self):
        with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as f:
            f.write("-- DB update 01 -> 02\nDELETE FROM `x` WHERE `id` = 1;\n")
            path = Path(f.name)
        try:
            self.assertFalse(spell_tables._is_generated(path))
        finally:
            path.unlink()


# ---------------------------------------------------------------------------
# T1 (.agents/plans/warlock-rework/warlock-rework.T1-HANDOFF.md): creature_template/
# creature_template_model - deliberately kept out of SPELL_TABLES/render_prune_blocks (see
# lib/spell_tables.py's CREATURE_TABLES module docstring), so this gets its own fixture. Uses the
# *real* base dump files (copied wholesale) rather than a synthetic CREATE TABLE - spell_tables.
# CREATURE_TEMPLATE_COLUMNS/_DEFAULTS are parsed once, at import time, from the real
# data/sql/base/db_world/creature_template.sql, so a synthetic fixture with a different column set
# would silently disagree with them.
# ---------------------------------------------------------------------------

REAL_BASE_SQL_DIR = trainer_state.REPO_ROOT / "data" / "sql" / "base" / "db_world"
TENTACLE_MIGRATION = trainer_state.REPO_ROOT / "data" / "sql" / "updates" / "db_world" / "2026_09_23_12.sql"
CREATURE_IDS_CFG = {"creature": {"start": 300000, "end": 300999}}


def _load_creature_class(source: str, existing_creature_ids=frozenset()) -> dict:
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "warlock.py"
        path.write_text(source)
        reg = registry.load_class_file(
            path,
            ids_cfg=CREATURE_IDS_CFG,
            existing_creature_ids=set(existing_creature_ids),
            creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
            creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS,
        )
    return {k: getattr(reg, k) for k in registry.MERGE_KEYS}


def _rows_from_sql(text: str, table_name: str, columns) -> list[dict]:
    """Round-trips a rendered SQL block back through sql_dump, for comparing *values* against a
    hand-written migration rather than raw text - see CreatureTablesTest's own docstring."""
    with tempfile.NamedTemporaryFile("w", suffix=".sql", delete=False) as f:
        f.write(text)
        path = Path(f.name)
    try:
        return sql_dump.read_table_rows(path, table_name, columns)
    finally:
        path.unlink()


class CreatureTablesTest(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        base = Path(self._tmp.name) / "base"
        promoted = Path(self._tmp.name) / "promoted"
        pending = Path(self._tmp.name) / "pending"
        for d in (base, promoted, pending):
            d.mkdir()
        self._promoted = promoted
        for name in ("creature_template.sql", "creature_template_model.sql", "creature_model_info.sql"):
            shutil.copyfile(REAL_BASE_SQL_DIR / name, base / name)
        # Point MODULES_DIR at an empty dir too - creature_template/creature_template_model are
        # both in trainer_state._TRAINER_TABLES-adjacent scanning (module SQL included), and the
        # real repo's modules/ has hand-written creature SQL using session-variable shapes this
        # parser can't read, which would otherwise leak warnings (and real content) into this test.
        modules = Path(self._tmp.name) / "modules"
        modules.mkdir()
        self._orig = (
            trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR,
            trainer_state.MODULES_DIR,
        )
        trainer_state.BASE_SQL_DIR = base
        trainer_state.PROMOTED_SQL_DIR = promoted
        trainer_state.PENDING_SQL_DIR = pending
        trainer_state.MODULES_DIR = modules

    def tearDown(self):
        (
            trainer_state.BASE_SQL_DIR, trainer_state.PROMOTED_SQL_DIR, trainer_state.PENDING_SQL_DIR,
            trainer_state.MODULES_DIR,
        ) = self._orig
        self._tmp.cleanup()

    def _index(self) -> spell_tables.SpellTableIndex:
        return spell_tables.load_creature_table_index()

    def test_declare_matches_tentacle_hand_written_migration(self):
        # The Tentacle row (300102) declared with only its distinctive fields (everything else
        # comes from creature_template()'s own defaults) must render to the same values the real
        # hand-written migration has - values, not raw text: the rendered upsert legitimately
        # differs from the hand-written file in harmless ways (NULL vs '' for an unset nullable
        # column, 1.0 vs 1 for a float literal - both are the same SQL value).
        dsl = _load_creature_class(
            'from lib.dsl.registry import creature_template, creature_model\n'
            'creature_template(\n'
            '    300102, "Tentacle of Madness",\n'
            '    faction=35, speed_run=1, detection_range=0,\n'
            '    unit_flags=33554434, unit_flags2=2048,\n'
            '    type=10, type_flags=1024,\n'
            '    flags_extra=66, ScriptName="npc_pri_tentacle_of_madness",\n'
            ')\n'
            'creature_model(300102, 15788, scale=0.5)\n',
            existing_creature_ids={300102},
        )
        blocks = spell_tables.render_creature_blocks(self._index(), dsl)
        self.assertEqual(len(blocks), 2)
        self.assertIn("INSERT INTO `creature_template`", blocks[0])
        self.assertIn("ON DUPLICATE KEY UPDATE", blocks[0])
        self.assertNotIn("DELETE", blocks[0])  # creature_template is never DELETEd
        self.assertIn("DELETE FROM `creature_template_model`", blocks[1])

        template_columns = spell_tables.CREATURE_TEMPLATE_COLUMNS
        (want_template,) = [
            r for r in sql_dump.read_table_rows(TENTACLE_MIGRATION, "creature_template", template_columns)
            if int(r["entry"]) == 300102
        ]
        (got_template,) = _rows_from_sql(blocks[0], "creature_template", template_columns)
        for column in template_columns:
            self.assertEqual(
                spell_tables._normalise(got_template.get(column)),
                spell_tables._normalise(want_template.get(column)),
                f"column {column!r} differs: got {got_template.get(column)!r}, want {want_template.get(column)!r}",
            )

        model_columns = spell_tables.CREATURE_TEMPLATE_MODEL_COLUMNS
        (want_model,) = [
            r for r in sql_dump.read_table_rows(TENTACLE_MIGRATION, "creature_template_model", model_columns)
            if int(r["CreatureID"]) == 300102
        ]
        (got_model,) = _rows_from_sql(blocks[1], "creature_template_model", model_columns)
        for column in model_columns:
            self.assertEqual(
                spell_tables._normalise(got_model.get(column)),
                spell_tables._normalise(want_model.get(column)),
                f"column {column!r} differs: got {got_model.get(column)!r}, want {want_model.get(column)!r}",
            )

    def test_rerun_with_unchanged_source_emits_nothing(self):
        dsl = _load_creature_class(
            'from lib.dsl.registry import creature_template\ncreature_template(300170, "Chaos Rift")\n'
        )
        blocks = spell_tables.render_creature_blocks(self._index(), dsl)
        header = spell_tables.GENERATED_MARKER + " -- DO NOT hand-edit.\n"
        (self._promoted / "gen.sql").write_text(header + "\n\n".join(blocks) + "\n")
        self.assertEqual(spell_tables.render_creature_blocks(self._index(), dsl), [])

    def test_changed_column_is_re_emitted_as_a_fresh_upsert(self):
        dsl = _load_creature_class(
            'from lib.dsl.registry import creature_template\n'
            'creature_template(300170, "Chaos Rift", faction=35)\n'
        )
        header = spell_tables.GENERATED_MARKER + " -- DO NOT hand-edit.\n"
        blocks = spell_tables.render_creature_blocks(self._index(), dsl)
        (self._promoted / "gen.sql").write_text(header + "\n\n".join(blocks) + "\n")

        dsl2 = _load_creature_class(
            'from lib.dsl.registry import creature_template\n'
            'creature_template(300170, "Chaos Rift", faction=90)\n'
        )
        blocks2 = spell_tables.render_creature_blocks(self._index(), dsl2)
        self.assertEqual(len(blocks2), 1)
        self.assertIn("ON DUPLICATE KEY UPDATE", blocks2[0])
        self.assertIn(", 90,", blocks2[0])

    def test_retired_declaration_is_reported_but_never_deleted(self):
        dsl = _load_creature_class(
            'from lib.dsl.registry import creature_template, creature_model\n'
            'creature_template(300170, "Chaos Rift")\n'
            'creature_model(300170, 11686)\n'
        )
        header = spell_tables.GENERATED_MARKER + " -- DO NOT hand-edit.\n"
        blocks = spell_tables.render_creature_blocks(self._index(), dsl)
        (self._promoted / "gen.sql").write_text(header + "\n\n".join(blocks) + "\n")

        # A later run drops 300170 but still declares something else - a totally empty run would
        # instead trip the circuit breaker (see the next test), which is a different case.
        dsl2 = _load_creature_class(
            'from lib.dsl.registry import creature_template, creature_model\n'
            'creature_template(300171, "Chaos Rift 2")\n'
            'creature_model(300171, 11686)\n'
        )
        index2 = self._index()
        self.assertEqual(
            [b for b in spell_tables.render_creature_blocks(index2, dsl2) if "300170" in b], []
        )
        report = spell_tables.render_creature_retirement_report(index2, dsl2)
        self.assertTrue(any("creature_template" in l and "300170" in l and "left in place" in l for l in report))
        self.assertTrue(
            any("creature_template_model" in l and "300170" in l and "left in place" in l for l in report)
        )
        self.assertFalse(any("DELETE" in l for l in report))  # report only - never a SQL block

    def test_circuit_breaker_refuses_to_report_an_emptied_source_load(self):
        dsl = _load_creature_class(
            'from lib.dsl.registry import creature_template\ncreature_template(300170, "Chaos Rift")\n'
        )
        header = spell_tables.GENERATED_MARKER + " -- DO NOT hand-edit.\n"
        blocks = spell_tables.render_creature_blocks(self._index(), dsl)
        (self._promoted / "gen.sql").write_text(header + "\n\n".join(blocks) + "\n")

        # Zero declarations at all this run, for a table with emitted history, must be refused as
        # a probable source-load failure rather than read as "everything was retired".
        report = spell_tables.render_creature_retirement_report(self._index(), {})
        self.assertTrue(any("SKIPPED checking creature_template " in l for l in report))


if __name__ == "__main__":
    unittest.main()
