"""
lib/dungeon_encounters.py and lib/dsl/dungeon.py's encounter declarations (Scarlet Monastery build FD-SM):
`dungeon_encounter()` (a new DungeonEncounter row and its credit), `repoint_encounter()` (an edit of a stock row),
and how a declared heroic counts and copies them (lib/dungeon_heroic.py `with_declared_encounters()`).

Covered: every DSL validation raise and the bookkeeping entry; the built rows (new row columns and mask, a repoint's
kept and replaced columns, cleared locales) and credit rows (creature, spell, kept live credit, last_encounter); every
expand() ERROR and WARNING; a second expand() replaces its rows; the Scarlet Monastery layout (7 new rows, 449
repointed, 14 heroic ids paired in OrderIndex order with the declared credits, the guard when the encounter expansion
did not run); the patch-Z merge (449 replaced in place, the new rows between the stock ones, each heroic copy beside its
normal row, every other stock row byte-identical); render, the real codestyle-sql.py and convergence; the generate.py
wiring.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_dungeon_encounters.py
"""

from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import dbcfile, dbcfmt, dungeon_encounters, dungeon_heroic, state  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.table_testkit import codestyle_sql, index_for, load_dsl, read_back, render, spec_for  # noqa: E402

DE = dbcfmt.DUNGEONENCOUNTER
STOCK_FILE = state.BASE_DBC_DIR / DE.dbc_filename
IDS_CFG = {
    "mapdifficulty": {"start": 1000, "end": 1099}, "dungeon_access": {"start": 122, "end": 199},
    "dungeonencounter": {"start": 1000, "end": 1199},
}
# Live instance_encounters of map 189 (FACTS-STOCK §6.1): entry -> (creditEntry, lastEncounterDungeon, comment)
SM_CREDITS = {
    444: (3983, 0, "Interrogator Vishas"), 445: (4543, 18, "Bloodmage Thalnos"), 446: (3974, 0, "Houndmaster Loksey"),
    447: (6487, 165, "Arcanist Doan"), 448: (3975, 163, "Herod"), 449: (4542, 0, "High Inquisitor Fairbanks"),
    450: (3977, 164, "High Inquisitor Whitemane"),
}
COUNCIL_CREDIT, LAST_STAND_CREDIT = 212300, 212301
# The lines handed to WP-H for source/world/dungeons/scarlet_monastery.py (the report's "Shared-file requests").
SM_DECLARATION = f"""
from lib.dsl.dungeon import credit_creature, credit_spell, dungeon_encounter, repoint_encounter

dungeon_encounter(1074, map_id=189, order_index=250, bit=7, name="Ironspine", credit=credit_creature(6489))
dungeon_encounter(1075, map_id=189, order_index=500, bit=8, name="Azshir the Sleepless and the Fallen Champion",
                  credit=credit_spell({COUNCIL_CREDIT}))
dungeon_encounter(1076, map_id=189, order_index=2250, bit=9, name="Ambrose Kell", credit=credit_creature(300910))
dungeon_encounter(1077, map_id=189, order_index=2500, bit=10, name="Lector Hollis Grey",
                  credit=credit_creature(300913))
dungeon_encounter(1078, map_id=189, order_index=3250, bit=11, name="Forgemaster Gideon Crell",
                  credit=credit_creature(300940))
dungeon_encounter(1079, map_id=189, order_index=3500, bit=12, name="Drillmaster Corin Halden",
                  credit=credit_creature(300942))
dungeon_encounter(1080, map_id=189, order_index=4500, bit=13, name="Brother Aldous Thorne",
                  credit=credit_creature(300946))
repoint_encounter(449, name="The Last Stand", credit=credit_spell({LAST_STAND_CREDIT}))
"""
SM_KILL_ORDER = [444, 1074, 1075, 445, 446, 1076, 1077, 447, 1078, 1079, 448, 1080, 449, 450]
SM_CREATURES = {6489, 300910, 300913, 300940, 300942, 300946, *(c for c, _, _ in SM_CREDITS.values())}


def _stock() -> dict[int, dict]:
    if not STOCK_FILE.is_file():
        raise unittest.SkipTest(f"{STOCK_FILE} not extracted")
    return {r["ID"]: r for r in dbcfile.read_dbc(STOCK_FILE, DE)}


def _credits() -> dict[int, dict]:
    return {e: {"entry": e, "creditType": 0, "creditEntry": c, "lastEncounterDungeon": l, "comment": n}
            for e, (c, l, n) in SM_CREDITS.items()}


def _lfg() -> dict[int, dict]:
    return {i: {"ID": i, "MapID": 189, "Difficulty": 0} for i in (18, 163, 164, 165)} | {
        6: {"ID": 6, "MapID": 36, "Difficulty": 0}}


def _inputs(stock, **kw) -> dungeon_encounters.EncounterInputs:
    kw.setdefault("credits", _credits())
    kw.setdefault("map_difficulties", {(189, 0), (36, 0), (36, 1)})
    kw.setdefault("creature_entries", set(SM_CREATURES))
    kw.setdefault("spell_ids", {COUNCIL_CREDIT, LAST_STAND_CREDIT})
    kw.setdefault("lfg_dungeons", _lfg())
    kw.setdefault("block", (1000, 1199))
    return dungeon_encounters.EncounterInputs(stock_encounters=stock, **kw)


def _load(source: str) -> dict:
    return load_dsl(source, ids_cfg=IDS_CFG)


def _expand(dsl: dict, stock, **kw):
    out = dungeon_encounters.expand(dsl, lambda: _inputs(stock, **kw))
    return out


def _sm_dsl(heroic_ids=None) -> dict:
    dsl = _load(SM_DECLARATION)
    if heroic_ids is not None:
        dsl["dungeons"] = [{
            "id": 189, "map_id": 189, "name": "Scarlet Monastery", "heroic_entries": {},
            "heroic": {"encounter_ids": tuple(heroic_ids), "spawn_mask": False, "event_spawns": False,
                       "no_credit": ()},
        }]
    return dsl


class DeclarationTest(unittest.TestCase):
    def test_the_bookkeeping_entries(self):
        decls = {d["id"]: d for d in _load(SM_DECLARATION)["encounter_declarations"]}
        self.assertEqual(sorted(decls), [449, *range(1074, 1081)])
        self.assertEqual(decls[1074], {
            "id": 1074, "kind": "new", "map_id": 189, "difficulty": 0, "order_index": 250, "bit": 7,
            "name": "Ironspine", "credit": (0, 6489), "last_encounter": 0, "icon": 0,
        })
        self.assertEqual(decls[1075]["credit"], (1, COUNCIL_CREDIT))
        self.assertEqual(decls[449], {
            "id": 449, "kind": "repoint", "name": "The Last Stand", "order_index": None, "bit": None,
            "credit": (1, LAST_STAND_CREDIT), "last_encounter": None, "icon": None,
        })

    def test_bad_values_raise(self):
        head = "from lib.dsl.dungeon import credit_creature, credit_spell, dungeon_encounter, repoint_encounter\n"
        new = "dungeon_encounter(1074, map_id=189, order_index=250, bit=7, name='X', credit=credit_creature(1){})\n"
        base = new.format("")
        for line, pattern in (
            (new.format(", difficulty=4"), "difficulty must be an int in 0..3"),
            (base.replace("bit=7", "bit=32"), "bit must be an int in 0..31"),
            (base.replace("bit=7", "bit=-1"), "bit must be an int in 0..31"),
            (base.replace("name='X'", "name=''"), "name must be a non-empty string"),
            (base.replace("name='X'", "name='" + "x" * 101 + "'"), "at most 100"),
            (base.replace("order_index=250", "order_index=2**31"), "signed 32-bit"),
            (base.replace("credit_creature(1)", "6489"), "credit must come from credit_creature"),
            (new.format(", last_encounter=70000"), "last_encounter must be 0 or an LFGDungeons id"),
            (new.replace("credit_creature(1)", "None").format(", last_encounter=18"), "last_encounter needs a credit"),
            (new.format(", icon=-1"), "icon must be a SpellIcon id"),
            (base.replace("1074", "999"), "dungeonencounter reserved block"),
            (base.replace("map_id=189", "map_id=0"), "map_id must be a Map.dbc id"),
            (base.replace("credit_creature(1)", "credit_creature(0)"), r"credit_creature\(0\)"),
            ("credit_spell('1')\n", r"credit_spell\('1'\)"),
            ("dungeon_encounter(1074, map_id=189, order_index=1, name='X', bit=None, credit=None)\n",
             "bit is required"),
            ("repoint_encounter(449)\n", "nothing to change"),
            ("repoint_encounter(449, bit=40)\n", "bit must be an int in 0..31"),
            (new.format("") + new.format(""), "declared twice"),
            ("repoint_encounter(449, name='A')\nrepoint_encounter(449, bit=3)\n", "declared twice"),
        ):
            with self.subTest(line=line), self.assertRaisesRegex(ValueError, pattern):
                _load(head + line)

    def test_a_missing_block_raises(self):
        with self.assertRaisesRegex(ValueError, "dungeonencounter"):
            load_dsl(
                "from lib.dsl.dungeon import credit_creature, dungeon_encounter\n"
                "dungeon_encounter(1074, map_id=189, order_index=250, bit=7, name='X', credit=credit_creature(1))\n",
                ids_cfg={k: v for k, v in IDS_CFG.items() if k != "dungeonencounter"},
            )

    def test_the_declarations_are_a_merge_key(self):
        self.assertIn("encounter_declarations", registry.MERGE_KEYS)


class ExpandTest(unittest.TestCase):
    def setUp(self):
        self.stock = _stock()

    def test_the_rows(self):
        dsl = _sm_dsl()
        out = _expand(dsl, self.stock)
        self.assertEqual((out.errors, out.warnings), ([], []))
        rows = {r["ID"]: r for r in dsl["dungeon_encounters"]}
        self.assertEqual(sorted(rows), [449, *range(1074, 1081)])
        ironspine = rows[1074]
        self.assertEqual({c: ironspine[c] for c in DE.columns if not c.startswith("Name_Lang_")} | {
            "Name_Lang_enUS": ironspine["Name_Lang_enUS"], "Name_Lang_Mask": ironspine["Name_Lang_Mask"]},
            {"ID": 1074, "MapID": 189, "Difficulty": 0, "OrderIndex": 250, "Bit": 7, "SpellIconID": 0,
             "Name_Lang_enUS": "Ironspine", "Name_Lang_Mask": self.stock[444]["Name_Lang_Mask"]})
        self.assertTrue(all(ironspine[c] == "" for c in dungeon_encounters.LOCALE_NAMES if c != "Name_Lang_enUS"))
        last_stand = rows[449]
        for column in DE.columns:
            expected = {"Name_Lang_enUS": "The Last Stand"}.get(column, self.stock[449][column])
            self.assertEqual(last_stand[column], expected, column)
        self.assertEqual((last_stand["Bit"], last_stand["OrderIndex"]), (5, 5000))
        credits = {r["entry"]: r for r in dsl["instance_encounters"]}
        self.assertEqual(sorted(credits), [449, *range(1074, 1081)])
        keys = ("creditType", "creditEntry", "lastEncounterDungeon", "comment")
        self.assertEqual({k: credits[1074][k] for k in keys},
                         {"creditType": 0, "creditEntry": 6489, "lastEncounterDungeon": 0, "comment": "Ironspine"})
        self.assertEqual((credits[1075]["creditType"], credits[1075]["creditEntry"]), (1, COUNCIL_CREDIT))
        self.assertEqual({k: credits[449][k] for k in keys},
                         {"creditType": 1, "creditEntry": LAST_STAND_CREDIT, "lastEncounterDungeon": 0,
                          "comment": "The Last Stand"})
        self.assertTrue(all(r[dungeon_encounters.MARK] for r in [*rows.values(), *credits.values()]))
        notes = "\n".join(out.notes)
        self.assertIn("new 1074 'Ironspine' (map 189 difficulty 0, bit 7, order 250), credit creature 6489", notes)
        self.assertIn("repointed stock 449 'The Last Stand' (map 189 difficulty 0, bit 5, order 5000), credit spell "
                      f"{LAST_STAND_CREDIT}", notes)

    def test_a_repoint_keeps_what_it_does_not_name(self):
        dsl = _load("from lib.dsl.dungeon import repoint_encounter\nrepoint_encounter(448, order_index=4100)\n")
        out = _expand(dsl, self.stock)
        self.assertEqual(out.errors, [])
        row = dsl["dungeon_encounters"][0]
        self.assertEqual((row["Name_Lang_enUS"], row["Bit"], row["OrderIndex"]), ("Herod", 4, 4100))
        credit = dsl["instance_encounters"][0]
        self.assertEqual((credit["creditType"], credit["creditEntry"], credit["lastEncounterDungeon"],
                          credit["comment"]), (0, 3975, 163, "Herod"))

    def test_a_repoint_moves_the_final_boss_link(self):
        dsl = _load("from lib.dsl.dungeon import repoint_encounter\nrepoint_encounter(448, last_encounter=0)\n")
        self.assertEqual(_expand(dsl, self.stock).errors, [])
        self.assertEqual(dsl["instance_encounters"][0]["lastEncounterDungeon"], 0)

    def test_a_repoint_of_a_row_without_credit_writes_none(self):
        credits = _credits()
        del credits[449]
        dsl = _load("from lib.dsl.dungeon import repoint_encounter\nrepoint_encounter(449, name='X')\n")
        self.assertEqual(_expand(dsl, self.stock, credits=credits).errors, [])
        self.assertEqual((len(dsl["dungeon_encounters"]), dsl["instance_encounters"]), (1, []))
        dsl = _load("from lib.dsl.dungeon import repoint_encounter\nrepoint_encounter(449, last_encounter=163)\n")
        out = _expand(dsl, self.stock, credits=credits)
        self.assertTrue(any("needs a credit" in e for e in out.errors), out.errors)

    def test_a_second_expand_replaces_its_rows(self):
        dsl = _sm_dsl()
        _expand(dsl, self.stock)
        _expand(dsl, self.stock)
        self.assertEqual((len(dsl["dungeon_encounters"]), len(dsl["instance_encounters"])), (8, 8))

    def test_nothing_declared_loads_nothing(self):
        dsl = {key: [] for key in registry.MERGE_KEYS}

        def boom():
            raise AssertionError("loaded")

        self.assertEqual(dungeon_encounters.expand(dsl, boom).errors, [])

    def _errors(self, line: str, **kw):
        dsl = _load("from lib.dsl.dungeon import credit_creature, credit_spell, dungeon_encounter, repoint_encounter\n"
                    + line)
        out = _expand(dsl, self.stock, **kw)
        return dsl, out

    def test_errors(self):
        new = "dungeon_encounter({}, map_id={}, order_index=250, bit={}, name='X', credit=credit_creature(6489){})\n"
        for line, kw, pattern in (
            (new.format(1074, 189, 3, ""), {}, r"rows \[447, 1074\] share Bit 3"),
            (new.format(1074, 189, 7, "") + new.format(1075, 189, 7, "").replace("250", "300"), {},
             r"rows \[1074, 1075\] share Bit 7"),
            (new.format(1074, 189, 7, "").replace("6489", "999999"), {}, "credit creature 999999 has no"),
            (new.format(1074, 189, 7, ""), {"live_encounters": [dict(_stock()[161], ID=1074)]},
             "live dungeonencounter_dbc row 1074 belongs to map 36"),
            (new.format(1074, 33, 7, ""), {}, "map 33 has no MapDifficulty row for difficulty 0"),
            ("repoint_encounter(1074, name='X')\n", {}, "1074 is not a stock DungeonEncounter row"),
            (new.format(1074, 189, 7, ", last_encounter=18"), {}, r"finder entry 18 already ends at encounter\(s\) "
                                                                  r"\[445\]"),
            (new.format(1074, 189, 7, ", last_encounter=6"), {}, "last_encounter 6 is a finder entry of map 36"),
            (new.format(1074, 189, 7, ", last_encounter=999"), {}, "last_encounter 999 is no LFGDungeons row"),
            (new.format(1074, 189, 7, ", difficulty=1"), {}, "map 189 has no MapDifficulty row for difficulty 1"),
        ):
            with self.subTest(line=line):
                dsl, out = self._errors(line, **kw)
                self.assertTrue(any(re.search(pattern, e) for e in out.errors), out.errors)
                self.assertEqual((dsl["dungeon_encounters"], dsl["instance_encounters"]), ([], []))

    def test_a_stock_id_for_a_new_row_is_an_error(self):
        # the block check stops a stock id at load time; generate.py's check backs it for a wide block
        dsl = {key: [] for key in registry.MERGE_KEYS}
        dsl["encounter_declarations"] = [{
            "id": 449, "kind": "new", "map_id": 189, "difficulty": 0, "order_index": 1, "bit": 9, "name": "X",
            "credit": None, "last_encounter": 0, "icon": 0,
        }]
        out = _expand(dsl, self.stock)
        self.assertTrue(any("449 is a stock DungeonEncounter id" in e for e in out.errors), out.errors)

    def test_our_own_earlier_output_is_not_a_clash(self):
        dsl = _sm_dsl()
        _expand(dsl, self.stock)
        live = [{c: r[c] for c in DE.columns} for r in dsl["dungeon_encounters"]]
        dsl = _sm_dsl()
        out = _expand(dsl, self.stock, live_encounters=live)
        self.assertEqual(out.errors, [])

    def test_a_module_row_outside_the_block_holds_its_bit(self):
        module = [dict(_stock()[444], ID=5000, Bit=7, OrderIndex=9000)]
        _, out = self._errors("dungeon_encounter(1074, map_id=189, order_index=250, bit=7, name='X', credit=None)\n",
                              live_encounters=module)
        self.assertTrue(any("rows [1074, 5000] share Bit 7" in e for e in out.errors), out.errors)

    def test_a_shared_order_index_warns(self):
        _, out = self._errors("dungeon_encounter(1074, map_id=189, order_index=1000, bit=7, name='X', credit=None)\n")
        self.assertEqual(out.errors, [])
        self.assertTrue(any("rows [445, 1074] share OrderIndex 1000" in w for w in out.warnings), out.warnings)

    def test_an_undeclared_credit_spell_warns(self):
        _, out = self._errors(
            "dungeon_encounter(1074, map_id=189, order_index=250, bit=7, name='X', credit=credit_spell(5))\n")
        self.assertEqual(out.errors, [])
        self.assertTrue(any("credit spell 5 is not declared" in w for w in out.warnings), out.warnings)

    def test_a_declared_finder_entry_and_final_boss(self):
        dsl = _load("from lib.dsl.dungeon import credit_creature, dungeon_encounter\n"
                    "dungeon_encounter(1074, map_id=189, order_index=250, bit=7, name='X', "
                    "credit=credit_creature(6489), last_encounter=320)\n")
        dsl["lfg_dungeon_declarations"] = [{"id": 320, "kind": "dungeon", "map_id": 189}]
        self.assertEqual(_expand(dsl, self.stock).errors, [])
        self.assertEqual(dsl["instance_encounters"][0]["lastEncounterDungeon"], 320)

    def test_an_lfg_last_encounter_on_a_declared_encounter_is_an_error(self):
        dsl = _sm_dsl()
        dsl["lfg_dungeon_declarations"] = [{"id": 18, "kind": "override", "last_encounter": 1074}]
        out = _expand(dsl, self.stock)
        self.assertTrue(any("lfg_override(18, last_encounter=1074)" in e for e in out.errors), out.errors)

    def test_a_heroic_id_is_an_error(self):
        dsl = _sm_dsl(heroic_ids=[1074])
        out = _expand(dsl, self.stock)
        self.assertTrue(any("1074 is also a heroic encounter id of dungeon 189" in e for e in out.errors), out.errors)

    def test_a_missing_stock_file_is_an_error(self):
        out = _expand(_sm_dsl(), None)
        self.assertTrue(any("no stock DungeonEncounter.dbc" in e for e in out.errors), out.errors)


class HeroicTest(unittest.TestCase):
    """dungeon_heroic.expand() after dungeon_encounters.expand(): the declared rows count as normal encounters."""

    def setUp(self):
        self.stock = _stock()

    def _run(self, heroic_ids, **live):
        dsl = _sm_dsl(heroic_ids)
        out = _expand(dsl, self.stock)
        self.assertEqual(out.errors, [])
        live.setdefault("instance_encounters", _credits())
        heroic = dungeon_heroic.expand(dsl, lambda: dungeon_heroic.LiveWorld(
            creature_templates={}, stock_encounters=self.stock, **live))
        return dsl, heroic

    def test_fourteen_heroic_copies_in_order_index_order(self):
        dsl, out = self._run(range(1081, 1095))
        self.assertEqual((out.errors, out.warnings), ([], []))
        heroic = [r for r in dsl["dungeon_encounters"] if r.get(dungeon_heroic.DERIVED)]
        normals = {r["ID"]: r for r in [*self.stock.values(), *dsl["dungeon_encounters"]] if r["Difficulty"] == 0}
        self.assertEqual([r["ID"] for r in heroic], list(range(1081, 1095)))
        for row, normal_id in zip(heroic, SM_KILL_ORDER):
            normal = normals[normal_id]
            for column in DE.columns:
                self.assertEqual(row[column], {"ID": row["ID"], "Difficulty": 1}.get(column, normal[column]),
                                 (row["ID"], column))
        self.assertEqual([r["Bit"] for r in heroic], [0, 7, 8, 1, 2, 9, 10, 3, 11, 12, 4, 13, 5, 6])
        credits = {r["entry"]: r for r in dsl["instance_encounters"] if r.get(dungeon_heroic.DERIVED)}
        self.assertEqual(sorted(credits), list(range(1081, 1095)))
        self.assertEqual((credits[1082]["creditType"], credits[1082]["creditEntry"]), (0, 6489))  # Ironspine
        self.assertEqual((credits[1083]["creditType"], credits[1083]["creditEntry"]), (1, COUNCIL_CREDIT))
        self.assertEqual((credits[1093]["creditType"], credits[1093]["creditEntry"]), (1, LAST_STAND_CREDIT))
        self.assertEqual(credits[1093]["comment"], "The Last Stand - Heroic")
        self.assertEqual(credits[1094]["creditEntry"], 3977)  # Whitemane
        self.assertEqual({e: credits[e]["_normal_lfg"] for e in credits if credits[e]["_normal_lfg"]},
                         {1084: 18, 1088: 165, 1091: 163, 1094: 164})
        # the declared normal rows are untouched by the heroic expansion
        self.assertEqual(len([r for r in dsl["dungeon_encounters"] if r.get(dungeon_encounters.MARK)]), 8)

    def test_seven_ids_no_longer_fit(self):
        dsl, out = self._run(range(1081, 1088))
        self.assertTrue(any("7 id(s) for 14 normal encounter(s)" in e for e in out.errors), out.errors)

    def test_a_stale_live_credit_of_a_declared_id_gives_way(self):
        credits = _credits()
        credits[1074] = {"entry": 1074, "creditType": 0, "creditEntry": 1, "lastEncounterDungeon": 0, "comment": ""}
        dsl, out = self._run(range(1081, 1095), instance_encounters=credits)
        self.assertEqual(out.errors, [])
        heroic = {r["entry"]: r for r in dsl["instance_encounters"] if r.get(dungeon_heroic.DERIVED)}
        self.assertEqual(heroic[1082]["creditEntry"], 6489)

    def test_the_heroic_expansion_stops_when_the_encounter_expansion_did_not_run(self):
        dsl = _sm_dsl(range(1081, 1095))
        out = dungeon_heroic.expand(dsl, lambda: dungeon_heroic.LiveWorld(
            creature_templates={}, stock_encounters=self.stock, instance_encounters=_credits()))
        self.assertTrue(any("lib/dungeon_encounters.expand() must run before" in e for e in out.errors), out.errors)


class PatchZTest(unittest.TestCase):
    def test_the_merged_client_file(self):
        stock = _stock()
        dsl = _sm_dsl(range(1081, 1095))
        self.assertEqual(_expand(dsl, stock).errors, [])
        self.assertEqual(dungeon_heroic.expand(dsl, lambda: dungeon_heroic.LiveWorld(
            creature_templates={}, stock_encounters=stock, instance_encounters=_credits())).errors, [])
        base = dbcfile.read_dbc(STOCK_FILE, DE)
        merged = {r["ID"]: r for r in base}
        merged.update(dungeon_heroic.client_encounter_rows(dsl["dungeon_encounters"]))
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / DE.dbc_filename
            path.write_bytes(dbcfile.pack_client_dbc(DE, list(merged.values()), base))
            back = dbcfile.read_dbc(path, DE)
        self.assertEqual(len(back), len(base) + 7 + 14)
        ids = [r["ID"] for r in back]
        start = ids.index(444)
        expected = []
        for normal, heroic in zip(SM_KILL_ORDER, range(1081, 1095)):
            expected += [normal, heroic]
        self.assertEqual(ids[start:start + 28], expected)
        by_id = {r["ID"]: r for r in back}
        self.assertEqual((by_id[449]["Name_Lang_enUS"], by_id[449]["Bit"], by_id[449]["OrderIndex"]),
                         ("The Last Stand", 5, 5000))
        self.assertEqual((by_id[1093]["Name_Lang_enUS"], by_id[1093]["Difficulty"]), ("The Last Stand", 1))
        self.assertEqual((by_id[1080]["Name_Lang_enUS"], by_id[1080]["Bit"]), ("Brother Aldous Thorne", 13))
        self.assertEqual({k: v for k, v in by_id.items() if k < 1000 and k != 449},
                         {r["ID"]: r for r in base if r["ID"] != 449})


class RenderTest(unittest.TestCase):
    def setUp(self):
        stock = _stock()
        self.dsl = _sm_dsl()
        self.assertEqual(_expand(self.dsl, stock).errors, [])
        self.blocks = {
            t: render(t, index_for(t, []), self.dsl[spec_for(t).registry_key])
            for t in ("dungeonencounter_dbc", "instance_encounters")
        }

    def test_the_blocks(self):
        self.assertIn("(449, 189, 0, 5000, 5, 'The Last Stand', '', ", self.blocks["dungeonencounter_dbc"])
        self.assertIn("(1074, 189, 0, 250, 7, 'Ironspine', '', ", self.blocks["dungeonencounter_dbc"])
        self.assertIn(f"(449, 1, {LAST_STAND_CREDIT}, 0, 'The Last Stand')", self.blocks["instance_encounters"])
        self.assertIn("(1074, 0, 6489, 0, 'Ironspine')", self.blocks["instance_encounters"])

    def test_the_blocks_pass_the_real_sql_codestyle_check(self):
        done = codestyle_sql("\n\n".join(self.blocks.values()))
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

    def test_a_second_build_over_the_read_back_state_emits_nothing(self):
        for table, rendered in self.blocks.items():
            with self.subTest(table=table):
                spec = spec_for(table)
                live = read_back(rendered, table, spec.columns)
                self.assertEqual(len(live), 8)
                self.assertEqual(render(table, index_for(table, live), self.dsl[spec.registry_key]), "")


class WiringTest(unittest.TestCase):
    def test_generate_expands_the_encounters_before_the_heroics(self):
        text = (TOOL_ROOT / "generate.py").read_text()
        encounters = text.index("dungeon_encounters.expand(dsl_classes")
        self.assertLess(encounters, text.index("dungeon_heroic.expand(\n"))
        self.assertIn("dungeon_expansion.errors[:0] = encounter_expansion.errors", text)


if __name__ == "__main__":
    unittest.main()
