"""
lib/dungeon_heroic.py (dungeon difficulties E2, WP-T2): a declared heroic's derived rows - the heroic DungeonEncounter
and `instance_encounters` rows, the spawnMask UPDATEs, `difficulty_entry_1` on normal rows and the side-table copies -
plus the DungeonEncounter.dbc client table and `heroic()`'s new arguments.

Covered: the layouts against DBCfmt.h and the base dump; the stock file's Deadmines rows and order; an empty merge is
byte-identical and the merged file round-trips with each heroic row beside its normal row; every validation raise;
the encounter copy (bit, order, names, normal credit entry, no dungeon finder link) and its ERRORs / WARNING; the
spawnMask emitter (only spawns without the bit, game event spawns left out, nothing for a map already at 3) and its
linked-respawn and pool lints; every difficulty_entry ERROR; the side-table copies (declared rows win, schema
defaults fill, a second expand() replaces rather than doubles); render, the real codestyle-sql.py, convergence (a
second build over the read-back state emits nothing) and prune for the SPELL_TABLES entries; the generate.py wiring;
and the real Deadmines declaration against the live replay (warm cache: seconds; cold: a few minutes).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_dungeon_heroic.py
"""

from __future__ import annotations

import inspect
import re
import sys
import tempfile
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import generate  # noqa: E402
from lib import dbcfile, dbcfmt, dungeon_checks, dungeon_heroic, spell_tables, sql_dump, sql_out, state  # noqa: E402
from lib import sqlcorpus, trainer_state  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.table_testkit import (  # noqa: E402
    REPO_ROOT, codestyle_sql, generated_file, index_for, load_dsl, read_back, render, spec_for,
)

DE = dbcfmt.DUNGEONENCOUNTER
STOCK_FILE = state.BASE_DBC_DIR / DE.dbc_filename
IDS_CFG = {
    "mapdifficulty": {"start": 1000, "end": 1099}, "dungeon_access": {"start": 122, "end": 199},
    "dungeonencounter": {"start": 1000, "end": 1199},
}
DEADMINES_CREDITS = {
    161: (644, "Rhahk'zor"), 162: (643, "Sneed"), 163: (1763, "Gilnid"), 164: (646, "Mr. Smite"),
    165: (645, "Cookie"), 166: (647, "Captain Greenskin"), 167: (639, "Edwin VanCleef"),
}
DERIVED_TABLES = (
    "dungeonencounter_dbc", "instance_encounters", "creature_template_addon", "creature_template_resistance",
    "creature_template_movement", "creature_onkill_reputation",
)


def _stock() -> dict[int, dict]:
    if not STOCK_FILE.is_file():
        raise unittest.SkipTest(f"{STOCK_FILE} not extracted")
    return {r["ID"]: r for r in dbcfile.read_dbc(STOCK_FILE, DE)}


def _heroic(map_id=36, name="Deadmines", encounter_ids=(), spawn_mask=True, event_spawns=False, entries=None):
    return {
        "id": map_id, "map_id": map_id, "name": name, "heroic_entries": dict(entries or {}),
        "heroic": {"encounter_ids": tuple(encounter_ids), "spawn_mask": spawn_mask, "event_spawns": event_spawns},
    }


def _dsl(*dungeons, **lists) -> dict:
    out = {key: [] for key in registry.MERGE_KEYS}
    out["dungeons"] = list(dungeons)
    out.update({k: list(v) for k, v in lists.items()})
    return out


def _creature(entry: int, **columns) -> dict:
    row = {"entry": entry, "difficulty_entry_1": 0, "difficulty_entry_2": 0, "difficulty_entry_3": 0}
    row.update(columns)
    return row


def _live(**kw) -> dungeon_heroic.LiveWorld:
    kw.setdefault("creature_templates", {})
    kw.setdefault("stock_encounters", {})
    kw.setdefault("instance_encounters", {
        e: {"entry": e, "creditType": 0, "creditEntry": c, "lastEncounterDungeon": 6 if e == 167 else 0, "comment": n}
        for e, (c, n) in DEADMINES_CREDITS.items()
    })
    return dungeon_heroic.LiveWorld(**kw)


def _spawns(*rows) -> dict[int, dict]:
    return {r[0]: {"guid": r[0], "id": r[1], "map": r[2], "spawnMask": r[3]} for r in rows}


class LayoutTest(unittest.TestCase):
    def test_fmt_is_dbcfmt_h(self):
        text = (REPO_ROOT / "src/server/shared/DataStores/DBCfmt.h").read_text()
        self.assertEqual(DE.fmt, re.search(r'DungeonEncounterfmt\[\] = "([a-z]+)"', text).group(1))
        self.assertEqual(DE.index_column, "ID")
        self.assertNotIn(DE, dbcfmt.ALL_TABLES)

    def test_columns_are_the_base_dump_create_tables(self):
        for table, columns in (
            ("dungeonencounter_dbc", DE.columns),
            ("instance_encounters", spell_tables.INSTANCE_ENCOUNTERS_COLUMNS),
            ("creature_template_addon", spell_tables.CREATURE_TEMPLATE_ADDON_COLUMNS),
            ("creature_template_resistance", spell_tables.CREATURE_TEMPLATE_RESISTANCE_COLUMNS),
            ("creature_template_movement", spell_tables.CREATURE_TEMPLATE_MOVEMENT_COLUMNS),
            ("creature_onkill_reputation", spell_tables.CREATURE_ONKILL_REPUTATION_COLUMNS),
        ):
            with self.subTest(table=table):
                path = trainer_state.BASE_SQL_DIR / f"{table}.sql"
                self.assertEqual(tuple(sql_dump.parse_create_table_columns(path, table)), tuple(columns))

    def test_the_derived_tables_are_keyed_and_prune_when_empty(self):
        keys = {
            "dungeonencounter_dbc": ("ID",), "instance_encounters": ("entry",), "creature_template_addon": ("entry",),
            "creature_template_resistance": ("CreatureID", "School"), "creature_template_movement": ("CreatureId",),
            "creature_onkill_reputation": ("creature_id",),
        }
        for table, key in keys.items():
            with self.subTest(table=table):
                self.assertEqual(spec_for(table).key_columns, key)
                self.assertTrue(spec_for(table).prune_when_empty)
                self.assertIn(spec_for(table).registry_key, registry.MERGE_KEYS)

    def test_side_tables_name_the_engine_read_tables_and_existing_lists(self):
        self.assertEqual(
            [s.name for s in dungeon_heroic.SIDE_TABLES],
            ["creature_template_addon", "creature_template_spell", "creature_template_model",
             "creature_template_resistance", "creature_template_movement", "creature_onkill_reputation"],
        )
        for side in dungeon_heroic.SIDE_TABLES:
            with self.subTest(table=side.name):
                self.assertIn(side.registry_key, registry.MERGE_KEYS)
                self.assertIn(side.entry_column, side.columns)
                self.assertEqual(side.key_columns[0], side.entry_column)
        by_name = {s.name: s for s in dungeon_heroic.SIDE_TABLES}
        self.assertEqual(by_name["creature_template_spell"].registry_key, "creature_template_spells")
        self.assertEqual(by_name["creature_template_model"].registry_key, "creature_template_models")


class StockFileTest(unittest.TestCase):
    def setUp(self):
        self.stock = _stock()

    def test_deadmines_has_seven_normal_encounters_and_no_heroic(self):
        rows = sorted((r for r in self.stock.values() if r["MapID"] == 36), key=lambda r: r["ID"])
        self.assertEqual([r["ID"] for r in rows], list(range(161, 168)))
        self.assertEqual([r["Bit"] for r in rows], list(range(7)))
        self.assertEqual({r["Difficulty"] for r in rows}, {0})
        self.assertEqual(rows[0]["Name_Lang_enUS"], "Rhahk'zor")
        self.assertEqual((len(self.stock), max(self.stock)), (612, 894))

    def test_the_stock_file_is_ordered_by_map_order_index_and_id(self):
        rows = dbcfile.read_dbc(STOCK_FILE, DE)
        self.assertNotEqual([r["ID"] for r in rows], sorted(r["ID"] for r in rows))
        keys = [(r["MapID"], r["OrderIndex"], r["ID"]) for r in rows]
        self.assertEqual(keys, sorted(keys))
        self.assertIn(-1000, {r["OrderIndex"] for r in rows})  # read signed

    def test_an_empty_merge_is_the_stock_file_byte_for_byte(self):
        rows = dbcfile.read_dbc(STOCK_FILE, DE)
        self.assertEqual(dbcfile.pack_client_dbc(DE, rows, rows), STOCK_FILE.read_bytes())


class DeclarationTest(unittest.TestCase):
    def _load(self, args: str) -> dict:
        return load_dsl(
            "from lib.dsl.dungeon import dungeon, heroic\n"
            f"dungeon(36, 'Deadmines', heroic=heroic(map_difficulty_id=1000, access_id=122, min_level=60{args}))\n",
            ids_cfg=IDS_CFG,
        )

    def test_the_new_arguments_reach_the_bookkeeping_entry(self):
        entry = self._load(", encounter_ids=range(1000, 1007)")["dungeons"][0]
        self.assertEqual(entry["heroic"]["encounter_ids"], tuple(range(1000, 1007)))
        self.assertIs(entry["heroic"]["spawn_mask"], True)
        self.assertIs(entry["heroic"]["event_spawns"], False)
        self.assertEqual(entry["heroic_entries"], {})

    def test_bad_values_raise(self):
        for args, pattern in (
            (", encounter_ids=[1000, 1000]", "distinct"),
            (", encounter_ids=['1000']", "distinct positive ints"),
            (", encounter_ids=5", "sequence"),
            (", spawn_mask=1", "spawn_mask must be True or False"),
            (", spawn_mask=False, event_spawns=True", "needs spawn_mask"),
            (", encounter_ids=[999]", "dungeonencounter reserved block"),
        ):
            with self.subTest(args=args), self.assertRaisesRegex(ValueError, pattern):
                self._load(args)

    def test_a_missing_block_raises(self):
        with self.assertRaisesRegex(ValueError, "dungeonencounter"):
            load_dsl(
                "from lib.dsl.dungeon import dungeon, heroic\n"
                "dungeon(36, 'D', heroic=heroic(map_difficulty_id=1000, access_id=122, min_level=60, "
                "encounter_ids=[1000]))\n",
                ids_cfg={k: v for k, v in IDS_CFG.items() if k != "dungeonencounter"},
            )


class EncounterTest(unittest.TestCase):
    def setUp(self):
        self.stock = _stock()

    def _expand(self, *dungeons, **live):
        dsl = _dsl(*dungeons)
        out = dungeon_heroic.expand(dsl, lambda: _live(stock_encounters=self.stock, **live))
        return dsl, out

    def test_each_normal_encounter_is_copied_to_heroic(self):
        dsl, out = self._expand(_heroic(encounter_ids=range(1000, 1007), spawn_mask=False))
        self.assertEqual(out.errors, [])
        self.assertEqual(out.warnings, [])
        rows = dsl["dungeon_encounters"]
        self.assertEqual([r["ID"] for r in rows], list(range(1000, 1007)))
        for row, normal_id in zip(rows, range(161, 168)):
            normal = self.stock[normal_id]
            for column in DE.columns:
                expected = {"ID": row["ID"], "Difficulty": 1}.get(column, normal[column])
                self.assertEqual(row[column], expected, column)
        credits = dsl["instance_encounters"]
        self.assertEqual(
            [(r["entry"], r["creditType"], r["creditEntry"], r["lastEncounterDungeon"]) for r in credits],
            [(1000 + i, 0, c, 0) for i, (c, _) in enumerate(DEADMINES_CREDITS.values())],
        )
        self.assertEqual(credits[0]["comment"], "Rhahk'zor - Heroic")
        self.assertIn("7 DungeonEncounter row(s) 1000-1006, 7 instance_encounters row(s)", "\n".join(out.notes))

    def test_no_encounter_ids_no_rows(self):
        dsl, out = self._expand(_heroic(spawn_mask=False))
        self.assertEqual((dsl["dungeon_encounters"], dsl["instance_encounters"], out.errors), ([], [], []))

    def test_a_count_mismatch_is_an_error(self):
        dsl, out = self._expand(_heroic(encounter_ids=range(1000, 1006), spawn_mask=False))
        self.assertTrue(any("6 id(s) for 7 normal encounter(s)" in e for e in out.errors), out.errors)
        self.assertEqual(dsl["dungeon_encounters"], [])

    def test_a_stock_id_is_an_error(self):
        _, out = self._expand(_heroic(encounter_ids=[161, *range(1001, 1007)], spawn_mask=False))
        self.assertTrue(any("161 is a stock DungeonEncounter id" in e for e in out.errors), out.errors)

    def test_a_live_heroic_row_for_the_map_is_an_error_but_our_own_output_is_not(self):
        own = [dict(self.stock[161 + i], ID=1000 + i, Difficulty=1) for i in range(7)]
        _, out = self._expand(_heroic(encounter_ids=range(1000, 1007), spawn_mask=False), live_encounters=own)
        self.assertEqual(out.errors, [])
        other = [dict(self.stock[161], ID=999, Difficulty=1)]
        _, out = self._expand(_heroic(encounter_ids=range(1000, 1007), spawn_mask=False), live_encounters=other)
        self.assertTrue(any("already has heroic encounter rows [999]" in e for e in out.errors), out.errors)

    def test_a_live_row_of_another_map_under_a_declared_id_is_an_error(self):
        clash = [dict(self.stock[161], ID=1003, MapID=33)]
        _, out = self._expand(_heroic(encounter_ids=range(1000, 1007), spawn_mask=False), live_encounters=clash)
        self.assertTrue(any("1003 belongs to map 33" in e for e in out.errors), out.errors)

    def test_one_id_in_two_dungeons_is_an_error(self):
        _, out = self._expand(
            _heroic(encounter_ids=range(1000, 1007), spawn_mask=False),
            _heroic(map_id=33, name="Shadowfang Keep", encounter_ids=[1006], spawn_mask=False),
        )
        self.assertTrue(any("1006: declared by dungeons 33 and 36" in e for e in out.errors), out.errors)

    def test_a_normal_encounter_without_credit_warns_and_gets_none(self):
        credits = _live().instance_encounters
        del credits[163]
        dsl, out = self._expand(
            _heroic(encounter_ids=range(1000, 1007), spawn_mask=False), instance_encounters=credits,
        )
        self.assertEqual(out.errors, [])
        self.assertTrue(any("163 ('Gilnid') has no instance_encounters row" in w for w in out.warnings))
        self.assertEqual(len(dsl["dungeon_encounters"]), 7)
        self.assertNotIn(1002, [r["entry"] for r in dsl["instance_encounters"]])

    def test_a_missing_stock_file_is_an_error(self):
        dsl = _dsl(_heroic(encounter_ids=range(1000, 1007), spawn_mask=False))
        out = dungeon_heroic.expand(dsl, lambda: _live(stock_encounters=None))
        self.assertTrue(any("no stock DungeonEncounter.dbc" in e for e in out.errors), out.errors)

    def test_the_merged_client_file_round_trips_with_each_heroic_row_beside_its_normal_row(self):
        dsl, _ = self._expand(_heroic(encounter_ids=range(1000, 1007), spawn_mask=False))
        base = dbcfile.read_dbc(STOCK_FILE, DE)
        merged = {r["ID"]: r for r in base}
        merged.update(dungeon_heroic.client_encounter_rows(dsl["dungeon_encounters"]))
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / DE.dbc_filename
            path.write_bytes(dbcfile.pack_client_dbc(DE, list(merged.values()), base))
            back = dbcfile.read_dbc(path, DE)
        self.assertEqual(len(back), len(base) + 7)
        ids = [r["ID"] for r in back]
        start = ids.index(161)
        self.assertEqual(ids[start:start + 14], [161, 1000, 162, 1001, 163, 1002, 164, 1003, 165, 1004, 166, 1005,
                                                  167, 1006])
        by_id = {r["ID"]: r for r in back}
        self.assertEqual(by_id[1003]["Name_Lang_enUS"], "Mr. Smite")
        self.assertEqual(by_id[1003]["Difficulty"], 1)
        self.assertEqual({k: v for k, v in by_id.items() if k < 1000}, {r["ID"]: r for r in base})


class SpawnMaskTest(unittest.TestCase):
    CREATURES = _spawns((10, 644, 36, 1), (11, 1729, 36, 1), (12, 1729, 36, 3), (13, 15000, 36, 1), (20, 1, 0, 1))
    OBJECTS = _spawns((50, 16399, 36, 1), (51, 13965, 36, 3), (60, 1, 1, 1))

    def _expand(self, heroic=None, **live):
        live.setdefault("spawns", {"creature": dict(self.CREATURES), "gameobject": dict(self.OBJECTS)})
        live.setdefault("event_guids", {"creature": {13}, "gameobject": set()})
        dsl = _dsl(heroic or _heroic())
        return dungeon_heroic.expand(dsl, lambda: _live(**live))

    def test_only_spawns_without_the_heroic_bit_are_updated_and_events_are_left_out(self):
        out = self._expand()
        self.assertEqual(out.errors, [])
        self.assertEqual(len(out.spawn_blocks), 2)
        creature, gameobject = out.spawn_blocks
        self.assertIn(
            "UPDATE `creature` SET `spawnMask` = `spawnMask` | 2 WHERE `id` IN (\n    644, 1729\n) AND `guid` IN (\n"
            "    10, 11\n);", creature,
        )
        self.assertIn("WHERE `id` IN (\n    16399\n) AND `guid` IN (\n    50\n);", gameobject)
        self.assertIn("2 of 4 creature spawn(s) to set, 1 game event spawn(s) left normal-only", "\n".join(out.notes))

    def test_event_spawns_opt_in(self):
        out = self._expand(_heroic(event_spawns=True))
        self.assertIn("644, 1729, 15000", out.spawn_blocks[0])

    def test_a_map_already_on_heroic_emits_nothing(self):
        spawns = {"creature": _spawns((10, 644, 36, 3)), "gameobject": _spawns((50, 16399, 36, 3))}
        out = self._expand(spawns=spawns)
        self.assertEqual((out.spawn_blocks, out.errors), ([], []))
        self.assertIn("0 of 1 creature spawn(s) to set; 0 of 1 gameobject spawn(s) to set", "\n".join(out.notes))

    def test_spawn_mask_off_emits_nothing(self):
        self.assertEqual(self._expand(_heroic(spawn_mask=False)).spawn_blocks, [])

    def test_a_map_without_spawns_is_an_error(self):
        out = self._expand(_heroic(map_id=48, name="Blackfathom Deeps"))
        self.assertTrue(any("no creature or gameobject spawn" in e for e in out.errors), out.errors)

    def test_a_link_to_an_event_spawn_left_normal_warns(self):
        link = {"guid": 10, "linkedGuid": 13, "linkType": 0}
        out = self._expand(linked_respawn=[link])
        self.assertTrue(any("linked_respawn creature 10 -> creature 13" in w and "only one" in w
                            for w in out.warnings), out.warnings)
        self.assertEqual(out.errors, [])

    def test_a_link_whose_masks_stop_overlapping_is_an_error(self):
        spawns = {"creature": _spawns((10, 644, 36, 2), (13, 15000, 36, 1)), "gameobject": {}}
        out = self._expand(spawns=spawns, linked_respawn=[{"guid": 10, "linkedGuid": 13, "linkType": 0}])
        self.assertTrue(any("no longer overlap" in e for e in out.errors), out.errors)

    def test_a_creature_to_gameobject_link_reads_both_tables(self):
        out = self._expand(linked_respawn=[{"guid": 11, "linkedGuid": 50, "linkType": 1}])
        self.assertEqual((out.errors, out.warnings), ([], []))

    def test_a_pool_split_across_difficulties_warns(self):
        out = self._expand(pools={"creature": {10: 7, 13: 7}, "gameobject": {50: 8}})
        self.assertTrue(any("pool 7 has creature spawns both on and off heroic" in w for w in out.warnings))
        self.assertFalse(any("pool 8" in w for w in out.warnings))
        self.assertIn("1 gameobject pool(s) on the map", "\n".join(out.notes))

    def test_the_block_passes_the_real_sql_codestyle_check(self):
        out = self._expand()
        done = codestyle_sql("\n\n".join(out.spawn_blocks))
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertNotIn("❌", done.stdout)

    def test_long_lists_wrap_inside_120_columns(self):
        rows = [{"guid": 100000 + i, "id": 200000 + i} for i in range(300)]
        block = dungeon_heroic.render_spawn_mask_update("creature", "X (map 1) heroic", rows)
        self.assertLessEqual(max(len(line) for line in block.splitlines()), 120)
        self.assertEqual(len(re.findall(r"\b1\d{5}\b", block)), 300)


class CreatureTest(unittest.TestCase):
    """The per-creature emitters over a WP-G style entry map (normal -> heroic)."""

    LIVE_TEMPLATES = {644: _creature(644), 646: _creature(646), 4075: _creature(4075), 310000: _creature(310000)}
    SIDE_ROWS = {
        "creature_template_addon": [{"entry": 646, "path_id": 0, "mount": 0, "bytes1": 0, "bytes2": 1, "emote": 0,
                                     "visibilityDistanceType": 0, "auras": "3417 6433"}],
        "creature_template_spell": [{"CreatureID": 646, "Index": 0, "Spell": 6432, "VerifiedBuild": 12340},
                                    {"CreatureID": 646, "Index": 1, "Spell": 3391, "VerifiedBuild": None}],
        "creature_template_model": [{"CreatureID": 646, "Idx": 0, "CreatureDisplayID": 2026, "DisplayScale": 1,
                                     "Probability": 1, "VerifiedBuild": 51831},
                                    {"CreatureID": 644, "Idx": 0, "CreatureDisplayID": 5694, "DisplayScale": 1,
                                     "Probability": 1, "VerifiedBuild": 51831}],
        "creature_template_resistance": [{"CreatureID": 644, "School": 2, "Resistance": 15}],  # VerifiedBuild left out
        "creature_template_movement": [{"CreatureId": 646, "Ground": 1, "Swim": 1, "Flight": 0, "Rooted": 0,
                                        "Chase": None, "Random": None, "InteractionPauseTimer": None}],
        "creature_onkill_reputation": [{"creature_id": 644, "RewOnKillRepFaction1": 72, "RewOnKillRepFaction2": 0,
                                        "MaxStanding1": 4, "IsTeamAward1": 0, "RewOnKillRepValue1": 5.0,
                                        "MaxStanding2": 0, "IsTeamAward2": 0, "RewOnKillRepValue2": 0.0,
                                        "TeamDependent": 0}],
    }
    MAP = {644: 310000, 646: 310001}

    def _expand(self, entries=None, templates=None, declared=(), dungeons=None, **lists):
        templates = dict(self.LIVE_TEMPLATES if templates is None else templates)
        spawns = {"creature": _spawns((1, 644, 36, 3), (2, 646, 36, 3)), "gameobject": {}}
        extra = dict(lists.pop("live", {}))
        live = _live(creature_templates=templates, side_rows=extra.pop("side_rows", self.SIDE_ROWS), spawns=spawns,
                     heroic_maps={36, 574}, **extra)
        dsl = _dsl(*(dungeons or [_heroic(entries=self.MAP if entries is None else entries)]),
                   creature_templates=[_creature(310001, **{"id": 310001})] + list(declared), **lists)
        return dsl, dungeon_heroic.expand(dsl, lambda: live)

    def test_difficulty_entry_1_is_a_one_column_edit_of_each_normal_row(self):
        dsl, out = self._expand()
        self.assertEqual(out.errors, [])
        edits = {r["entry"]: r for r in dsl["creature_template_edits"]}
        self.assertEqual(set(edits), {644, 646})
        self.assertEqual(edits[644]["_update_columns"], ("difficulty_entry_1",))
        self.assertEqual(edits[646]["difficulty_entry_1"], 310001)
        spec = spell_tables.CREATURE_TABLES[0]
        block = sql_out.render_update_block(spec.name, spec.columns, "entry", list(edits.values()))
        self.assertEqual(
            block,
            "UPDATE `creature_template` SET `difficulty_entry_1` = 310000 WHERE `entry` IN (644);\n"
            "UPDATE `creature_template` SET `difficulty_entry_1` = 310001 WHERE `entry` IN (646);",
        )

    def test_the_edit_converges_against_the_live_row(self):
        dsl, _ = self._expand()
        spec = spell_tables.CREATURE_TABLES[0]
        live = [_creature(644, difficulty_entry_1=310000, name="Rhahk'Zor"), _creature(646)]
        index = spell_tables.SpellTableIndex({spec.name: live}, tables=(spec,))
        self.assertEqual([r["entry"] for r in index.rows_to_emit(spec, dsl["creature_template_edits"])], [646])

    def test_side_tables_are_copied_to_the_heroic_entry(self):
        dsl, out = self._expand()
        self.assertEqual(out.errors, [])
        self.assertEqual(dsl["heroic_template_addons"][0]["entry"], 310001)
        self.assertEqual(dsl["heroic_template_addons"][0]["auras"], "3417 6433")
        self.assertEqual(
            [(r["CreatureID"], r["Index"], r["Spell"], r["VerifiedBuild"]) for r in dsl["creature_template_spells"]],
            [(310001, 0, 6432, 12340), (310001, 1, 3391, None)],
        )
        models = {r["id"]: r["CreatureDisplayID"] for r in dsl["creature_template_models"]}
        self.assertEqual(models, {"310000:0": 5694, "310001:0": 2026})
        resistance = dsl["heroic_template_resistances"][0]
        self.assertEqual((resistance["CreatureID"], resistance["School"], resistance["Resistance"]), (310000, 2, 15))
        self.assertIsNone(resistance["VerifiedBuild"])  # the schema DEFAULT fills a column the live row lacks
        self.assertEqual(dsl["heroic_template_movements"][0]["CreatureId"], 310001)
        self.assertEqual(dsl["heroic_onkill_reputations"][0]["creature_id"], 310000)

    def test_a_declared_row_for_the_heroic_entry_wins(self):
        mine = {"id": "310001:0", "CreatureID": 310001, "Idx": 0, "CreatureDisplayID": 999, "DisplayScale": 1.0,
                "Probability": 1.0, "VerifiedBuild": 0}
        dsl, _ = self._expand(creature_template_models=[mine])
        self.assertEqual([r for r in dsl["creature_template_models"] if r["CreatureID"] == 310001], [mine])

    def test_a_heroic_entry_without_a_model_row_is_an_error(self):
        side_rows = {**self.SIDE_ROWS, "creature_template_model": [
            r for r in self.SIDE_ROWS["creature_template_model"] if r["CreatureID"] != 646]}
        _, out = self._expand(live={"side_rows": side_rows})
        self.assertEqual(out.errors, [
            "dungeon(36) creature 646 -> heroic 310001: no creature_template_model row for the heroic entry (the "
            "normal entry has none to copy) - Creature::InitEntry refuses to load it, so its heroic spawns are empty"
        ])
        mine = {"id": "310001:0", "CreatureID": 310001, "Idx": 0, "CreatureDisplayID": 999, "DisplayScale": 1.0,
                "Probability": 1.0, "VerifiedBuild": 0}
        _, out = self._expand(creature_template_models=[mine], live={"side_rows": side_rows})
        self.assertEqual(out.errors, [])  # a declared model row is enough

    def test_a_second_expand_replaces_its_rows(self):
        dsl, _ = self._expand()
        counts = {k: len(dsl[k]) for k in ("creature_template_spells", "creature_template_edits",
                                           "heroic_template_addons")}
        dungeon_heroic.expand(dsl, lambda: _live(
            creature_templates=dict(self.LIVE_TEMPLATES), side_rows=self.SIDE_ROWS,
            spawns={"creature": _spawns((1, 644, 36, 3)), "gameobject": {}},
        ))
        self.assertEqual({k: len(dsl[k]) for k in counts}, counts)

    def test_a_creature_template_columns_edit_takes_the_column_and_gives_it_back(self):
        edit = {"entry": 644, "id": 644, "HealthModifier": 2.0, "_update_columns": ("HealthModifier",)}
        dsl, out = self._expand(creature_template_edits=[edit])
        self.assertEqual(out.errors, [])
        merged = next(r for r in dsl["creature_template_edits"] if r["entry"] == 644)
        self.assertEqual(merged["_update_columns"], ("HealthModifier", "difficulty_entry_1"))
        dsl["dungeons"][0]["heroic_entries"] = {}
        dungeon_heroic.expand(dsl, lambda: _live(creature_templates=dict(self.LIVE_TEMPLATES)))
        restored = [r for r in dsl["creature_template_edits"] if r["entry"] == 644]
        self.assertEqual(len(restored), 1)
        self.assertEqual(restored[0]["_update_columns"], ("HealthModifier",))
        self.assertNotIn("difficulty_entry_1", restored[0])

    def test_a_creature_template_columns_edit_of_the_same_column_must_agree(self):
        edit = {"entry": 644, "id": 644, "difficulty_entry_1": 5, "_update_columns": ("difficulty_entry_1",)}
        _, out = self._expand(creature_template_edits=[edit])
        self.assertTrue(any("declares difficulty_entry_1 = 5" in e for e in out.errors), out.errors)

    def test_engine_refusals_are_errors(self):
        cases = (
            ({999: 310002}, None, (), "no live creature_template row 999"),
            ({644: 644}, None, (), "cannot be its own difficulty entry"),
            ({644: 310009}, None, (), "neither declared this run nor live"),
            ({644: 310000}, {**self.LIVE_TEMPLATES, 644: _creature(644, difficulty_entry_1=31)}, (),
             "already has difficulty_entry_1 = 31"),
            ({644: 310000}, {**self.LIVE_TEMPLATES, 7: _creature(7, difficulty_entry_2=644)}, (),
             "644 is itself the difficulty_entry_2 of creature 7"),
            ({644: 310000}, {**self.LIVE_TEMPLATES, 8: _creature(8, difficulty_entry_1=310000)}, (),
             "310000 is already the difficulty_entry_1 of creature 8"),
            ({644: 310000}, {**self.LIVE_TEMPLATES, 310000: _creature(310000, difficulty_entry_1=4)}, (),
             "has difficulty entries of its own"),
            ({644: 310000, 646: 310000}, None, (), "heroic entry of both 644 and 646"),
            ({644: 310000}, None, [_creature(644, id=644)], "declares the full row"),
        )
        for entries, templates, declared, pattern in cases:
            with self.subTest(pattern=pattern):
                _, out = self._expand(entries=entries, templates=templates, declared=declared)
                self.assertTrue(any(pattern in e for e in out.errors), out.errors)

    def test_one_normal_mapped_twice_is_an_error(self):
        _, out = self._expand(dungeons=[_heroic(entries={644: 310000}),
                                        _heroic(map_id=33, name="Shadowfang Keep", entries={644: 310001})])
        wanted = "dungeons 33 and 36 map it to heroic 310001 and 310000"
        self.assertTrue(any(wanted in e for e in out.errors), out.errors)
        self.assertFalse(any("creature_template_columns()" in e for e in out.errors), out.errors)

    def test_a_creature_also_spawned_on_another_heroic_map(self):
        spawns = {"creature": _spawns((1, 4075, 36, 3), (2, 4075, 574, 3), (3, 4075, 33, 1)), "gameobject": {}}
        live = _live(creature_templates=dict(self.LIVE_TEMPLATES), heroic_maps={36, 574}, spawns=spawns)
        dsl = _dsl(_heroic(entries={4075: 310000}), _heroic(map_id=33, name="Shadowfang Keep", spawn_mask=False))
        out = dungeon_heroic.expand(dsl, lambda: live)
        self.assertTrue(any("also spawns on map 574" in e for e in out.errors), out.errors)
        self.assertFalse(any("map 36" in e for e in out.errors))
        self.assertTrue(any("also spawns on map 33, whose declared heroic" in w for w in out.warnings), out.warnings)

    def test_heroic_entries_without_a_heroic_is_an_error(self):
        entry = dict(_heroic(entries={644: 310000}), heroic=None)
        out = dungeon_heroic.expand(_dsl(entry), lambda: self.fail("no heroic: nothing to load"))
        self.assertTrue(any("heroic_entries without a heroic" in e for e in out.errors))

    def test_no_entry_map_no_creature_rows(self):
        dsl, out = self._expand(entries={})
        self.assertEqual(dsl["creature_template_edits"], [])
        self.assertEqual(dsl["creature_template_spells"], [])
        self.assertFalse(any("heroic creatures" in n for n in out.notes))


class RenderTest(unittest.TestCase):
    """The SPELL_TABLES half: render, codestyle, convergence and prune for every derived table."""

    def setUp(self):
        stock = _stock()
        self.dsl = _dsl(_heroic(encounter_ids=range(1000, 1007), spawn_mask=False, entries=CreatureTest.MAP),
                        creature_templates=[_creature(310001, id=310001)])
        out = dungeon_heroic.expand(self.dsl, lambda: _live(
            stock_encounters=stock, creature_templates=dict(CreatureTest.LIVE_TEMPLATES),
            side_rows=CreatureTest.SIDE_ROWS, spawns={"creature": _spawns((1, 644, 36, 3)), "gameobject": {}},
        ))
        self.assertEqual(out.errors, [])
        self.blocks = {t: render(t, index_for(t, []), self.dsl[spec_for(t).registry_key]) for t in DERIVED_TABLES}

    def test_every_derived_table_renders(self):
        for table, block in self.blocks.items():
            with self.subTest(table=table):
                self.assertTrue(block.startswith(f"DELETE FROM `{table}` WHERE ("), block[:80])
        self.assertIn("(1003, 36, 1, 875, 3, 'Mr. Smite', '', ", self.blocks["dungeonencounter_dbc"])
        self.assertIn("(1006, 0, 639, 0, 'Edwin VanCleef - Heroic');", self.blocks["instance_encounters"])

    def test_the_blocks_pass_the_real_sql_codestyle_check(self):
        done = codestyle_sql("\n\n".join(self.blocks.values()))
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertNotIn("❌", done.stdout)

    def test_a_second_build_over_the_read_back_state_emits_nothing(self):
        for table, rendered in self.blocks.items():
            with self.subTest(table=table):
                spec = spec_for(table)
                live = read_back(rendered, table, spec.columns)
                self.assertEqual(len(live), len(self.dsl[spec.registry_key]))
                self.assertEqual(render(table, index_for(table, live), self.dsl[spec.registry_key]), "")

    def test_dropping_the_heroic_prunes_every_derived_row(self):
        for table, rendered in self.blocks.items():
            with self.subTest(table=table), generated_file(rendered):
                spec = spec_for(table)
                emitted = spell_tables.load_generated_table_rows(table, spec.key_columns)
                result = index_for(table, emitted, emitted=emitted).rows_to_prune(spec, [])
                self.assertEqual(len(result.keys), len(self.dsl[spec.registry_key]))
                self.assertFalse(result.breaker_tripped)


class WiringTest(unittest.TestCase):
    def test_generate_passes_the_expansion_to_both_paths(self):
        self.assertIn("dungeon_expansion", inspect.signature(generate._check_report).parameters)
        text = (TOOL_ROOT / "generate.py").read_text()
        self.assertEqual(text.count("expansion=dungeon_expansion)"), 2)
        self.assertIn("*dungeon_expansion.spawn_blocks", text)
        self.assertIn("*dungeon_expansion.retire_blocks", text)
        self.assertIn("dbcfmt.DUNGEONENCOUNTER: dungeon_heroic.client_encounter_rows(", text)
        self.assertIn("spawn_state.py", generate.CACHE_CODE_FILES)

    def test_errors_and_notes_reach_the_dungeon_checks(self):
        expansion = dungeon_heroic.Expansion(errors=["boom"], notes=["dungeons: hello"])

        class _Index:
            def live_rows(self, table):
                return []

        dsl = _dsl()
        self.assertEqual(dungeon_checks.errors_for_run(dsl, _Index(), expansion=expansion), ["boom"])
        self.assertEqual(dungeon_checks.summary_notes([], expansion), ["dungeons: hello"])


class DeadminesTest(unittest.TestCase):
    """The real declaration against the live replay (E1's WP-1D spawnMask SQL already in pending_db_world)."""

    @classmethod
    def setUpClass(cls):
        sqlcorpus.activate(generate.CACHE_DIR, generate.cache_code_version())
        try:
            from lib import source  # noqa: PLC0415 - needs ruamel (the venv)

            ids_cfg = source.load_ids(generate.SOURCE_DIR / "ids.yaml")
            creature_index = spell_tables.load_creature_table_index()
            existing = {int(r["entry"]): r for r in creature_index.live_rows("creature_template")}
            cls.dsl = {
                k: list(v) for k, v in registry.load_classes_dir(
                    generate.SOURCE_DIR / "world" / "dungeons", ids_cfg=ids_cfg, existing_creature_rows=existing,
                    creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS, live_data={},
                ).items()
            }
            cls.index = spell_tables.load_spell_table_index()
            cls.out = dungeon_heroic.expand(cls.dsl, lambda: dungeon_heroic.load_live_world(existing, cls.index))
        finally:
            sqlcorpus.deactivate()

    def test_the_declaration(self):
        heroic = next(e for e in self.dsl["dungeons"] if e["map_id"] == 36)["heroic"]
        self.assertEqual(heroic["encounter_ids"], tuple(range(1000, 1007)))
        self.assertTrue(heroic["spawn_mask"])

    def test_it_is_clean_and_emits_the_encounter_and_heroic_creature_rows(self):
        self.assertEqual((self.out.errors, self.out.warnings), ([], []))
        self.assertEqual(self.out.spawn_blocks, [])  # WP-1D's spawnMask 3 is live
        for table in ("dungeonencounter_dbc", "instance_encounters"):
            spec = spec_for(table)
            self.assertEqual(len(self.dsl[spec.registry_key]), 7, table)
            # E2's generated rev (pending_db_world) already holds them, so a run has nothing left to emit
            self.assertEqual(self.index.rows_to_emit(spec, self.dsl[spec.registry_key]), [], table)
        # WP-G's heroic templates: difficulty_entry_1 on each normal row of the entry map, from the lock file
        from lib import heroic_templates  # noqa: PLC0415

        lock = heroic_templates.parse_lock(heroic_templates.LOCK_PATH.read_text())
        self.assertEqual(
            {r["entry"]: r["difficulty_entry_1"] for r in self.dsl["creature_template_edits"]},
            {n: h for n, h in lock.pairs.items() if n in next(
                e for e in self.dsl["dungeons"] if e["map_id"] == 36)["heroic_entries"]},
        )
        self.assertEqual(len(self.dsl["creature_template_edits"]), 25)
        self.assertEqual(
            [(r["entry"], r["creditEntry"]) for r in self.dsl["instance_encounters"]],
            [(1000 + i, c) for i, (c, _) in enumerate(DEADMINES_CREDITS.values())],
        )


if __name__ == "__main__":
    unittest.main()
