"""`generate.py --scope` (lib/scope.py): the scope file, ownership, the SQL narrowing, the reserved blocks, the client
repack and the whole-file checks. No generate.py run: every piece is fed small hand-made inputs."""

from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import dbcfile, dbcfmt, scope, source, sql_out  # noqa: E402
from lib.dsl import registry  # noqa: E402

SOURCE_DIR = Path(__file__).resolve().parents[1] / "source"


def _ownership(selected=("deadmines",)) -> scope.Ownership:
    own = scope.Ownership(frozenset(selected))
    own.ranges["spell"] = [(205200, 205399, "deadmines"), (204400, 204899, "warrior")]
    own.ranges["creature"] = [(300420, 300449, "deadmines")]
    return own


class ScopeFileTest(unittest.TestCase):
    """source/scopes.yaml against ids.yaml and the source tree."""

    @classmethod
    def setUpClass(cls):
        cls.ids_cfg = source.load_ids(SOURCE_DIR / "ids.yaml")
        cls.scopes = scope.load_scopes(ids_cfg=cls.ids_cfg)

    def test_every_reservation_belongs_to_one_scope_or_a_pool(self):
        owned = scope.scope_reservations(self.scopes, self.ids_cfg)
        seen: dict[str, str] = {}
        for name, reservations in owned.items():
            for res in reservations:
                self.assertNotIn(res, seen, f"reservation {res} is in scopes {seen.get(res)} and {name}")
                seen[res] = name
        for res in self.ids_cfg["reservations"]:
            with self.subTest(reservation=res):
                self.assertTrue(res in seen or res in self.scopes.pools, f"reservation {res} has no scope or pool")
        self.assertFalse(set(seen) & set(self.scopes.pools))

    def test_every_source_file_belongs_to_one_scope_at_most(self):
        for path in sorted(SOURCE_DIR.rglob("*.py")):
            rel = path.relative_to(SOURCE_DIR).as_posix()
            with self.subTest(path=rel):
                self.scopes.source_scope(rel)  # raises on two scopes

    def test_listed_sources_exist(self):
        for name, scope_def in self.scopes.defs.items():
            for src in scope_def.sources:
                with self.subTest(scope=name, source=src):
                    self.assertTrue((SOURCE_DIR / src).exists())

    def test_conventions(self):
        cases = {
            "npcs/deadmines/rhahk_zor.py": "deadmines",
            "items/deadmines_loot.py": "deadmines",
            "items/deadmines.py": "deadmines",
            "world/dungeons/deadmines.py": "deadmines",
            "items/shadowfang_keep_hard_mode_effects.py": "shadowfang_keep",
            "classes/warrior/warrior_shared.py": "warrior",
            "npcs/warrior_npcs.py": "warrior",
            "npcs/boss_mechanics.py": "bossmechanics",
            "npcs/healsim_spells.py": "healsim",
            "items/haunted_set_bonuses.py": "haunted_set",
            "items/ladders.py": None,
            "world/lfg.py": None,
            "world/dungeons/wailing_caverns.py": None,
        }
        for rel, want in cases.items():
            with self.subTest(path=rel):
                self.assertEqual(self.scopes.source_scope(rel), want)

    def test_items_is_not_a_scope_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scopes.yaml"
            path.write_text("scopes:\n  items:\n")
            with self.assertRaises(scope.ScopeError):
                scope.load_scopes(path)


class DeclaredInTest(unittest.TestCase):
    """registry.declared_in: the source file whose top-level code registered an entry (recorded only on request)."""

    def tearDown(self):
        registry.stop_provenance()

    def test_package_files_helpers_and_relative_imports(self):
        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp) / "thing"
            pkg.mkdir()
            (pkg / "_common.py").write_text(textwrap.dedent("""
                from lib.dsl.registry import scripted_by

                def bind(spell_id, name):
                    scripted_by(spell_id, name)
            """))
            (pkg / "a_uses_b.py").write_text(textwrap.dedent("""
                from ._common import bind
                from .b_target import X
                bind(205001, 'spell_a')
            """))
            (pkg / "b_target.py").write_text(textwrap.dedent("""
                from ._common import bind
                X = 1
                bind(205002, 'spell_b')
            """))
            registry.stop_provenance()
            reg = registry.load_class_package(pkg)
            self.assertIsNone(registry.declared_in(reg.spell_script_names[0]))  # not recording: nothing kept
            registry.record_provenance()
            reg = registry.load_class_package(pkg)
            by_spell = {e["spell_id"]: Path(registry.declared_in(e)).name for e in reg.spell_script_names}
            self.assertNotIn("_declared_in", reg.spell_script_names[0])  # the entry itself is untouched
        # a_uses_b.py imports b_target.py first: b's binding is still b's, and a helper's call is its caller's.
        self.assertEqual(by_spell, {205001: "a_uses_b.py", 205002: "b_target.py"})


class OwnershipTest(unittest.TestCase):
    def test_declared_beats_reserved_and_conflicts(self):
        own = _ownership()
        self.assertEqual(own.owners("spell", 205250), {"deadmines"})
        own.declare("spell", 205250, "warrior")  # a warrior declaration inside the Deadmines range
        self.assertEqual(own.owners("spell", 205250), {"warrior"})
        self.assertFalse(own.mine(own.owners("spell", 205250)))
        own.declare("spell", 205250, "deadmines")
        self.assertTrue(own.conflict(own.owners("spell", 205250)))
        self.assertEqual(own.owners("spell", 999), frozenset())

    def test_scope_ranges_leave_holes_for_other_owners_and_foreign_ids(self):
        own = _ownership()
        own.declare("spell", 205300, "warrior")
        own.declare("spell", 205301, "deadmines")
        block = {"start": 200000, "end": 209999, "foreign": {205350: "mod-x"}}
        self.assertEqual(own.scope_ranges("spell", block), [(205200, 205299), (205301, 205349), (205351, 205399)])

    def test_row_owner_by_declared_key_then_id_column(self):
        own = _ownership()
        own.key_columns["spell_script_names"] = ("spell_id", "ScriptName")
        own.declare_key("spell_script_names", (133, "spell_x"), "deadmines")
        self.assertEqual(own.row_owners("spell_script_names", {"spell_id": 133.0, "ScriptName": "spell_x"}),
                         {"deadmines"})
        self.assertEqual(own.row_owners("spell_script_names", {"spell_id": 205210, "ScriptName": "y"}),
                         {"deadmines"})
        self.assertEqual(own.row_owners("spell_script_names", {"spell_id": 204401, "ScriptName": "y"}), {"warrior"})
        self.assertEqual(own.row_owners("unknown_table", {"id": 1}), frozenset())

    def test_build_ownership_derivations(self):
        scopes = scope.Scopes({n: scope.ScopeDef(n, (), ()) for n in ("deadmines", "warrior")}, ())
        ids_cfg = {"reservations": {"deadmines": {"spell": {"start": 205200, "end": 205399}}}}
        dsl = {
            "item_declarations": [{"id": "dm_axe"}],
            "dungeons": [{"map_id": 36, "creatures": [{"entry": 644}]}],
            "dungeon_encounters": [{"ID": 1000, "MapID": 36}],
            "creature_templates": [{"entry": 300420}],
        }
        registry.record_provenance()
        self.addCleanup(registry.stop_provenance)
        registry.set_declared_in(dsl["item_declarations"][0], SOURCE_DIR / "items" / "deadmines.py")
        registry.set_declared_in(dsl["dungeons"][0], SOURCE_DIR / "world" / "dungeons" / "deadmines.py")
        registry.set_declared_in(dsl["creature_templates"][0], SOURCE_DIR / "npcs" / "deadmines" / "x.py")
        expansion = SimpleNamespace(items=[SimpleNamespace(decl=SimpleNamespace(key="dm_axe"),
                                                           tiers=[SimpleNamespace(entry=71000)])])
        copies = SimpleNamespace(tiers=[SimpleNamespace(key="dm_axe", remap={205400: 205410})])
        limits = SimpleNamespace(categories={"dm_axe": 1000})
        lock = SimpleNamespace(pairs={644: 310001}, maps={644: 36})
        own = scope.build_ownership(
            scopes, ids_cfg, ["deadmines"], dsl_classes=dsl, spell_entries=[], talents={}, table_specs=(),
            item_expansion=expansion, item_spell_expansion=copies, item_limit_expansion=limits, heroic_lock=lock,
            gcd_aura_ids={4: 201560}, map_spawns={36: {"creature": {5000: 644}, "gameobject": {6000: 1234}}},
        )
        self.assertEqual(own.owners("creature_guid", 5000), {"deadmines"})
        self.assertEqual(own.owners("gameobject_guid", 6000), {"deadmines"})
        for key in ((644, 0), (-5000, 0), (1234, 1), (-6000, 1)):
            self.assertEqual(own.row_owners("smart_scripts", {"entryorguid": key[0], "source_type": key[1]}),
                             {"deadmines"})
        for space, entry_id, want in (
            ("item", 71000, "deadmines"), ("spell", 205410, "deadmines"), ("item_limit_category", 1000, "deadmines"),
            ("creature", 644, "deadmines"), ("creature", 310001, "deadmines"), ("creature", 300420, "deadmines"),
            ("dungeonencounter", 1000, "deadmines"), ("spell", 201560, "warrior"), ("spell", 205250, "deadmines"),
        ):
            with self.subTest(space=space, id=entry_id):
                self.assertEqual(own.owners(space, entry_id), {want})


class StatementTest(unittest.TestCase):
    def test_split_honours_quotes_and_comments(self):
        text = "-- a comment; with a semicolon\nINSERT INTO `t` (`a`, `b`) VALUES\n(1, 'x;y'),\n(2, 'it''s');\n" \
               "DELETE FROM `t` WHERE `a` IN (1, 2);"
        parts = scope.split_statements(text)
        self.assertEqual(len(parts), 3)
        stmt = scope.parse_statement(parts[1])
        self.assertEqual([row for _g, row in stmt.rows], [{"a": 1, "b": "x;y"}, {"a": 2, "b": "it's"}])

    def test_unknown_statement_is_an_error(self):
        report = scope.FilterReport()
        scope.filter_sql("SET @x := 1;", _ownership(), report)
        self.assertTrue(report.errors)


class FilterTest(unittest.TestCase):
    def setUp(self):
        self.own = _ownership()
        self.report = scope.FilterReport()

    def run_filter(self, text):
        return scope.filter_sql(text, self.own, self.report)

    def test_insert_keeps_own_rows(self):
        text = "INSERT INTO `spell_proc` (`SpellId`, `ProcsPerMinute`) VALUES\n(205210, 0),\n(204401, 1),\n(205211, 2);"
        out = self.run_filter(text)
        self.assertEqual(
            out, "INSERT INTO `spell_proc` (`SpellId`, `ProcsPerMinute`) VALUES\n(205210, 0),\n(205211, 2);",
        )
        self.assertEqual(self.report.left_out[("spell_proc", "warrior")], 1)

    def test_upsert_keeps_its_suffix(self):
        text = ("INSERT INTO `creature_template` (`entry`, `name`) VALUES\n(300420, 'a'),\n(300370, 'b') "
                "ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);")
        out = self.run_filter(text)
        self.assertEqual(out, "INSERT INTO `creature_template` (`entry`, `name`) VALUES\n(300420, 'a') "
                              "ON DUPLICATE KEY UPDATE `name` = VALUES(`name`);")

    def test_delete_key_tuples_narrow_and_comment_follows(self):
        text = ("-- Prune: 2 rows\nDELETE FROM `spell_script_names` WHERE (`spell_id`, `ScriptName`) IN "
                "((205210, 'a'), (204401, 'b'));")
        out = self.run_filter(text)
        self.assertIn("-- Prune: 2 rows", out)
        self.assertIn("narrowed", out)
        self.assertTrue(out.endswith("DELETE FROM `spell_script_names` WHERE (`spell_id`, `ScriptName`) IN "
                                     "((205210, 'a'));"))

    def test_statement_with_no_own_row_goes_with_its_comment(self):
        out = self.run_filter("-- warrior only\nDELETE FROM `spell_proc` WHERE `SpellId` = 204401;")
        self.assertEqual(out, "")

    def test_update_in_list_narrows(self):
        out = self.run_filter("UPDATE `creature_template` SET `minlevel` = 2 WHERE `entry` IN (300420, 300370);")
        self.assertEqual(out, "UPDATE `creature_template` SET `minlevel` = 2 WHERE `entry` IN (300420);")

    def test_loot_group_and_or_of_ands(self):
        out = self.run_filter("DELETE FROM `creature_loot_template` WHERE `Entry` = 300421 AND `GroupId` = 1;")
        self.assertIn("300421", out)
        text = ("UPDATE `smart_scripts` SET `event_flags` = `event_flags` | 2 WHERE\n"
                "    (`entryorguid` = 300421 AND `source_type` = 0 AND `id` = 1) OR\n"
                "    (`entryorguid` = 300370 AND `source_type` = 0 AND `id` = 1);")
        out = self.run_filter(text)
        self.assertIn("300421", out)
        self.assertNotIn("300370", out)

    def test_spawn_mask_update_splits_by_guid(self):
        self.own.declare("creature_guid", 1, "deadmines")
        self.own.declare("creature_guid", 3, "deadmines")
        self.own.declare("creature_guid", 2, "warrior")
        text = "UPDATE `creature` SET `spawnMask` = 3 WHERE `id` IN (300420, 300370) AND `guid` IN (\n1, 2\n);"
        self.assertEqual(self.run_filter(text),
                         "UPDATE `creature` SET `spawnMask` = 3 WHERE `id` IN (300420, 300370) AND `guid` IN (1);")
        text = "UPDATE `creature` SET `spawnMask` = 3 WHERE `id` IN (300420, 300421) AND `guid` IN (1, 3);"
        self.assertEqual(self.run_filter(text), text)
        self.assertEqual(self.report.errors, [])

    def test_smart_scripts_follow_source_type(self):
        self.own.declare("creature_guid", 77, "deadmines")
        self.own.declare("gameobject", 300421, "warrior")
        text = ("UPDATE `smart_scripts` SET `event_flags` = `event_flags` | 4 WHERE\n"
                "    (`entryorguid` = 300421 AND `source_type` = 1 AND `id` = 0) OR\n"
                "    (`entryorguid` = -77 AND `source_type` = 0 AND `id` = 0);")
        out = self.run_filter(text)
        self.assertNotIn("300421", out)  # source_type 1: the gameobject 300421, not the Deadmines creature
        self.assertIn("-77", out)  # a spawn guid script on the scope's map
        self.own.key_columns["smart_scripts"] = ("entryorguid", "source_type")
        self.own.declare_key("smart_scripts", (300421, 1), "deadmines")
        self.assertIn("300421", self.run_filter(text))


class DeletedInsertedTest(unittest.TestCase):
    def test_ranges_lists_and_inserts(self):
        text = ("DELETE FROM `spell_dbc` WHERE `ID` BETWEEN 200000 AND 200099;\n"
                "DELETE FROM `spell_dbc` WHERE `ID` IN (133, 134);\n"
                "INSERT INTO `spell_dbc` (`ID`, `x`) VALUES\n(200001, 0),\n(133, 1);\n"
                "DELETE FROM `creature_template_model` WHERE (`CreatureID`, `Idx`) IN ((300420, 0));")
        out = scope.deleted_and_inserted(text, {"spell_dbc": "ID", "creature_template_model": "CreatureID"})
        self.assertEqual(out["spell_dbc"], ([(200000, 200099)], {133, 134}, {200001, 133}))
        self.assertEqual(out["creature_template_model"][1], {300420})


class _Table:
    def __init__(self, name, sql_table, columns=("ID", "v")):
        self.name, self.sql_table, self.index_column, self.columns = name, sql_table, "ID", columns


class DbcBlockTest(unittest.TestCase):
    SPELL = _Table("Spell", "spell_dbc")
    DURATION = _Table("SpellDuration", "spellduration_dbc")

    def blocks(self, built, applied, edited=(), secondary_rows=(), secondary_applied=None, spell_extra=None):
        spell_rows = [{"ID": i, "v": v, **(spell_extra or {}).get(i, {})} for i, v in built.items()]
        blocks = [
            (self.SPELL, {"start": 200000, "end": 209999}, spell_rows, list(edited), {}),
            (self.DURATION, {"start": 30100, "end": 30199}, list(secondary_rows), [], {}),
        ]
        applied_rows = {
            "Spell": {i: {"ID": i, "v": v} for i, v in applied.items()},
            "SpellDuration": secondary_applied or {},
        }
        own = _ownership()
        own.declare("spell", 133, "deadmines")  # a stock spell the dungeon edits
        return scope.scoped_dbc_blocks(blocks, own, lambda table, _w: applied_rows[table.name],
                                       {"SpellDuration": "spellduration"})

    def test_narrowed_ranges_explicit_ids_and_left_out(self):
        result = self.blocks(
            built={205214: 2, 205215: 1, 204401: 9, 133: 5}, applied={205214: 1, 205215: 1, 204401: 1, 133: 4},
            edited=[133],
        )
        self.assertEqual(len(result.blocks), 1)
        table, id_range, rows, explicit = result.blocks[0]
        self.assertEqual(id_range["ranges"], [(205200, 205399)])
        self.assertEqual(explicit, [133])
        self.assertEqual(sorted(r["ID"] for r in rows), [133, 205214, 205215])
        self.assertEqual(result.left_out[("spell_dbc", "warrior")], 1)
        sql = sql_out._table_block(table, id_range, rows, explicit)
        self.assertIn("BETWEEN 205200 AND 205399;", sql)
        self.assertIn("IN (133);", sql)
        self.assertNotIn("204401", sql)

    def test_unchanged_scope_writes_nothing(self):
        result = self.blocks(built={205214: 1, 204401: 9}, applied={205214: 1, 204401: 1})
        self.assertEqual(result.blocks, [])

    def test_a_removed_row_in_range_is_deleted_by_the_range(self):
        result = self.blocks(built={205214: 1}, applied={205214: 1, 205215: 1})
        self.assertEqual(len(result.blocks), 1)
        self.assertEqual([r["ID"] for r in result.blocks[0][2]], [205214])

    def test_shared_secondary_rows_are_added_or_refused(self):
        extra = {205214: {"DurationIndex": 30157}}
        rows = [{"ID": 30157, "v": 2345}]
        result = self.blocks(built={205214: 2}, applied={205214: 1}, secondary_rows=rows, spell_extra=extra)
        self.assertFalse([b for b in result.blocks if b[0].name == "SpellDuration"])
        self.assertEqual(result.insert_blocks, ["INSERT INTO `spellduration_dbc` (`ID`, `v`) VALUES\n(30157, 2345);"])
        result = self.blocks(built={205214: 2}, applied={205214: 1}, secondary_rows=rows, spell_extra=extra,
                             secondary_applied={30157: {"ID": 30157, "v": 999}})
        self.assertTrue(any("another checkout minted" in e for e in result.errors))
        result = self.blocks(built={205214: 2}, applied={205214: 1}, secondary_rows=rows, spell_extra=extra,
                             secondary_applied={30157: {"ID": 30157, "v": 2345}})
        self.assertEqual(result.insert_blocks, [])


class ReferenceTest(unittest.TestCase):
    def test_trigger_of_an_unshipped_foreign_spell(self):
        own = _ownership()
        rows = [{"ID": 205214, "EffectTriggerSpell_1": 204401, "Effect_2": 28, "EffectMiscValue_2": 300370}]
        errors = scope.reference_errors(rows, own, {"spell": {204401}}, "", {"creature": {300370}})
        self.assertEqual(len(errors), 2)
        self.assertFalse(scope.reference_errors(rows, own, {}, "", {}))  # both live already: fine


class ClientTest(unittest.TestCase):
    LIMIT = dbcfmt.ITEMLIMITCATEGORY
    DURATION = dbcfmt.SPELLDURATION

    def limit_rows(self, quantities: dict[int, int]) -> list[dict]:
        out = []
        for row_id, quantity in quantities.items():
            row = dbcfile.empty_row(self.LIMIT)
            row.update(ID=row_id, Quantity=quantity, Name_Lang_enUS=f"c{row_id}")
            out.append(row)
        return out

    def pack(self, quantities):
        return dbcfile.pack_dbc_bytes(self.LIMIT, self.limit_rows(quantities))

    def test_only_own_rows_change(self):
        own = scope.Ownership(frozenset({"deadmines"}))
        own.declare("item_limit_category", 1000, "deadmines")
        own.declare("item_limit_category", 1001, "deadmines")
        own.declare("item_limit_category", 1002, "shadowfang_keep")
        base = {"DBFilesClient/ItemLimitCategory.dbc": self.pack({1: 1, 1000: 1, 1001: 1, 1002: 1})}
        # the full build changes 1000, drops 1001 and changes the other scope's 1002 (in-flight work)
        full = {"ItemLimitCategory.dbc": self.pack({1: 1, 1000: 2, 1002: 5})}
        result = scope.scoped_client_files(
            base, full, {"ItemLimitCategory.dbc": self.LIMIT}, own, {"ItemLimitCategory.dbc": self.limit_rows({1: 1})},
            {}, {},
        )
        self.assertEqual(result.errors, [])
        rows = {r["ID"]: r["Quantity"] for r in scope.read_dbc_bytes(result.loose["ItemLimitCategory.dbc"], self.LIMIT)}
        self.assertEqual(rows, {1: 1, 1000: 2, 1002: 1})
        self.assertEqual(list(result.replacements), ["DBFilesClient/ItemLimitCategory.dbc"])

    def test_nothing_of_the_scope_changes(self):
        own = scope.Ownership(frozenset({"deadmines"}))
        base = {"DBFilesClient/ItemLimitCategory.dbc": self.pack({1: 1, 1002: 1})}
        full = {"ItemLimitCategory.dbc": self.pack({1: 1, 1002: 5})}
        result = scope.scoped_client_files(base, full, {"ItemLimitCategory.dbc": self.LIMIT}, own,
                                           {"ItemLimitCategory.dbc": self.limit_rows({1: 1})}, {}, {})
        self.assertEqual(result.replacements, {})


class WholeFileTest(unittest.TestCase):
    def test_labels(self):
        own = scope.Ownership(frozenset({"deadmines"}))
        own.declare("item", 71000, "deadmines")
        own.declare("item", 72000, "shadowfang_keep")
        old = 'HEAD\nITEM_TIER_LABELS = {\n    [71000] = "Normal",\n    [72000] = "Normal",\n}\n'
        mine = old.replace('[71000] = "Normal"', '[71000] = "Heroic"')
        self.assertEqual(scope.foreign_file_changes(old, mine, "labels", own), [])
        theirs = old.replace('[72000] = "Normal"', '[72000] = "Heroic"')
        self.assertTrue(scope.foreign_file_changes(old, theirs, "labels", own))
        header = old.replace("HEAD", "HEAD2")
        self.assertTrue(scope.foreign_file_changes(old, header, "labels", own))

    def test_copies_ignore_the_count_line(self):
        own = scope.Ownership(frozenset({"deadmines"}))
        own.declare("spell", 205410, "deadmines")
        old = "    {\n    };\n    inline constexpr std::size_t kCopyCount = 0;\n"
        new = "    {\n        { 205410, 205400, 205410 },  // dm_x empowered_1\n    };\n" \
              "    inline constexpr std::size_t kCopyCount = 1;\n"
        self.assertEqual(scope.foreign_file_changes(old, new, "copies", own), [])


if __name__ == "__main__":
    unittest.main()
