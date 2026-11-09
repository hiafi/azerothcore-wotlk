"""
Stratholme's heroic declaration (Stratholme build, WP-H): source/world/dungeons/stratholme.py as generate.py loads it.

Covered: the heroic() arguments (MapDifficulty 1003, dungeon_access 125, DungeonEncounter 1028-1040, spawn masks, no
event spawns), the roles / extra declarations, the heroic overrides against the build spec's numbers (handoff 3.6) and
the predicted heroic loot ids, the wave switch (BIND_WAVE_2: the Main Gate bosses keep their stock heroic copy until
wave 2 binds them), the kit adds' overrides following the creature_template() declarations of
source/npcs/stratholme/, and the expansion against the live replay: no ERROR or WARNING, the thirteen encounters in
the stock file's order (OrderIndex, not id) with their kill credit, the creature set and the predicted
heroic_ids.lock lines (310120 on, normal-entry order), the bosses' INSTANCE_BIND and immunity sets (1972; the Baron
-419), the SmartAI widening of the Rockwing Screecher and the Eye of Naxxramas, the game-event spawns staying
normal-only, and the client MapDifficulty.dbc / DungeonEncounter.dbc rows (the patch-Z merge) beside the stock rows.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_stratholme_heroic.py
"""

from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import generate  # noqa: E402
from lib import dbcfile, dbcfmt, dungeon_checks, dungeon_heroic, heroic_templates, source, spell_tables  # noqa: E402
from lib import sqlcorpus, state  # noqa: E402
from lib.dsl import registry  # noqa: E402

ST_FILE = TOOL_ROOT / "source" / "world" / "dungeons" / "stratholme.py"
KIT_DIR = TOOL_ROOT / "source" / "npcs" / "stratholme"
IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")

# The normal encounters in the stock file's order (OrderIndex: 473 .. 478, then The Unforgiven 472 at 6500, then
# 479 .. 484), paired with the heroic ids 1028-1040 in that order; and the boss each credits.
STOCK_ORDER = (473, 474, 475, 476, 477, 478, 472, 479, 480, 481, 482, 483, 484)
NORMAL_CREDIT = {
    472: 10516, 473: 10558, 474: 10808, 475: 10997, 476: 11032, 477: 10811, 478: 10813, 479: 10436, 480: 10437,
    481: 10438, 482: 10435, 483: 10439, 484: 10440,
}
HEROIC_ENCOUNTERS = {hid: NORMAL_CREDIT[nid] for hid, nid in zip(range(1028, 1041), STOCK_ORDER)}
ENCOUNTER_NAMES = [  # the stock rows' names (Ramstein's carries the stock file's typo; the heroic copy keeps it)
    "Hearthsinger Forresten", "Timmy the Cruel", "Cannon Master Willey", "Malor the Zealous", "Archivist Galford",
    "Balnazzar", "The Unforgiven", "Baroness Anastari", "Nerub'enkan", "Maleki the Pallid", "Magistrate Barthilas",
    "Ramnstein the Gorger", "Baron Rivendare",
]

# Heroic health from the build spec (docs/dungeons/stratholme-rework.md, handoff 3.6) and the wave each boss binds in.
BOSS_HEALTH = {
    10435: 235_000, 10436: 220_000, 10437: 200_000, 10438: 210_000, 10439: 230_000, 10440: 300_000,
    10516: 250_000, 10558: 240_000, 10808: 225_000, 11032: 230_000, 10997: 230_000, 10811: 220_000,
    10812: 340_000, 10813: 300_000,
}
BOSS_WAVE = {entry: "1" for entry in (10435, 10436, 10437, 10438, 10439, 10440)}
BOSS_WAVE.update({entry: "2" for entry in (10516, 10558, 10808, 11032, 10997, 10811, 10812, 10813)})
# The predicted heroic ids (the lock mints in normal-entry order from 310120; the boss lootids are the same numbers).
HEROIC_LOOTID = {
    10435: 310155, 10436: 310156, 10437: 310157, 10438: 310158, 10439: 310159, 10440: 310160, 10516: 310163,
    10558: 310164, 10808: 310166, 10811: 310168, 10813: 310170, 10997: 310173, 11032: 310175,
}
NO_LOOT = {10812}  # Dathrohan: his kill drops nothing (Balnazzar's does)
# Stock-id kit adds and the C++ summons: heroic health, and the wave each binds in
STOCK_ADD_HEALTH = {
    (10394, "1"): None, (11030, "1"): 5_000, (11197, "1"): 7_500, (10876, "1"): 2_500,
    (10387, "2"): 9_000, (11054, "2"): 7_000,
}
KIT_HEALTH = {  # new kit adds (handoff 3.3 ids): heroic health
    300582: 12_000, 300584: 12_000, 300586: 4_000, 300602: 1_500, 300604: 7_000, 300608: 18_000,
}
KIT_HEROIC_ID = {  # minted after the extraction set, in entry order, wave by wave (the mint-order note)
    300582: 310189, 300584: 310190, 300586: 310191, 300602: 310192, 300604: 310193, 300608: 310194,
}
EXTRA = (10394, 11030, *KIT_HEALTH)
HEROIC_ENTRY_COUNT = 69  # the extraction set plus 10394 and 11030, before any kit add lands
NOT_HEROIC = (10441, 10461, 10536, 14646, 16046, 16100,  # critters, triggers
              10917, 15607, 16031,  # friendly NPCs (Ysida Harmon included)
              14684)  # Balzaphon: a game-event creature
SMART_WIDENED = (10409, 10411)
# Game-event spawns (stay normal-only): Elder Farwhisper (event 7) and Balzaphon (event 120)
EVENT_GUIDS = (200848, 248654)
# The 13 boss spawns (Dathrohan's included; Balnazzar and Ramstein have none) and Ysida
BOSS_SPAWN_GUIDS = (247226, 52150, 247227, 52122, 54433, 52148, 52149, 54237, 54238, 54239, 54240, 54241)


def _bound_waves() -> set[str]:
    path = KIT_DIR / "_common.py"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    return {"1"} | {w for w, v in re.findall(r"^BIND_WAVE_(2)\s*=\s*(True|False)\s*$", text, re.M) if v == "True"}


def _own_heroic_loot() -> bool:
    """stratholme.py's `_HEROIC_BOSS_OWN_LOOT` (on since L-1 declared the heroic loot; it was off until then, the
    Scholomance R-A S-2 rule: a lootid with no loot_template rows behind it drops nothing)."""
    m = re.search(r"^_HEROIC_BOSS_OWN_LOOT\s*=\s*(True|False)\s*$", ST_FILE.read_text(encoding="utf-8"), re.M)
    return bool(m) and m.group(1) == "True"


BOUND = _bound_waves()
OWN_LOOT = _own_heroic_loot()
BOUND_BOSSES = {b for b, w in BOSS_WAVE.items() if w in BOUND}


def _kit_declared() -> set[int]:
    pattern = re.compile(r"\bcreature_template\(\s*(\d+)\s*,")
    return {int(m) for path in KIT_DIR.glob("*.py") for m in pattern.findall(path.read_text(encoding="utf-8"))}


def _st_entry() -> tuple[dict, object]:
    reg = registry.load_class_package(TOOL_ROOT / "source" / "world" / "dungeons", ids_cfg=IDS)
    return {e["map_id"]: e for e in reg.dungeons}[329], reg


class DeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entry, cls.reg = _st_entry()
        cls.heroic = cls.entry["heroic"]

    def test_the_ids_are_the_next_of_their_blocks_after_scholomance(self):
        self.assertEqual((self.heroic["map_difficulty_id"], self.heroic["access_id"]), (1003, 125))
        self.assertEqual(self.heroic["encounter_ids"], tuple(range(1028, 1041)))
        self.assertEqual(self.heroic["min_level"], 60)
        md = {r["ID"]: r for r in self.reg.map_difficulties}[1003]
        self.assertEqual((md["MapID"], md["Difficulty"], md["RaidDuration"], md["MaxPlayers"]), (329, 1, 86400, 5))
        self.assertEqual(md["Message_Lang_enUS"], "Heroic Difficulty requires you to be level 60.")
        access = {r["id"]: r for r in self.reg.dungeon_access}[125]
        self.assertEqual((access["map_id"], access["difficulty"], access["min_level"]), (329, 1, 60))

    def test_spawns_go_to_heroic_but_the_event_spawns_stay_normal_only(self):
        self.assertTrue(self.heroic["spawn_mask"])
        self.assertFalse(self.heroic["event_spawns"])

    def test_roles_and_extras(self):
        by_entry = {c["entry"]: c for c in self.entry["creatures"]}
        # the thirteen encounter bosses (Dathrohan has no encounter row of his own; the role correction makes him one)
        self.assertEqual(sorted(e for e, c in by_entry.items() if c["role"] == "boss"), sorted(BOSS_HEALTH))
        self.assertEqual(by_entry[10812]["role"], "boss")
        for extra in EXTRA:
            self.assertEqual(by_entry[extra]["role"], "trash", extra)
            self.assertTrue(by_entry[extra]["summoned_by"], extra)  # a C++ summon: no spawns, free text names who
            self.assertEqual(by_entry[extra]["spawns"], 0, extra)
        self.assertEqual(self.entry["skip"], ())

    def test_boss_overrides_are_the_build_specs_health_the_immunity_set_and_the_loot_flag(self):
        overrides = {entry: dict(pairs) for entry, pairs in self.heroic["overrides"]}
        for entry, health in BOSS_HEALTH.items():
            with self.subTest(entry=entry):
                if entry not in BOUND_BOSSES:
                    self.assertNotIn(entry, overrides)  # a Main Gate boss: stock until wave 2 binds it
                    continue
                self.assertEqual(overrides[entry]["health"], health)
                expected = {"CreatureImmunitiesId": -419 if entry == 10440 else 1972}
                if OWN_LOOT and entry not in NO_LOOT:
                    expected["lootid"] = HEROIC_LOOTID[entry]
                self.assertEqual(dict(overrides[entry]["columns"]), expected)

    def test_the_stock_id_kit_adds_follow_their_wave(self):
        overrides = {entry: dict(pairs) for entry, pairs in self.heroic["overrides"]}
        for (entry, wave), health in STOCK_ADD_HEALTH.items():
            with self.subTest(entry=entry):
                if health is None or wave not in BOUND:
                    self.assertNotIn(entry, overrides)
                else:
                    self.assertEqual(overrides[entry]["health"], health)
                    self.assertNotIn("columns", overrides[entry])

    def test_wave_1_is_bound_and_the_wave_switch_is_read_from_the_npc_package(self):
        self.assertIn("1", BOUND)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "world" / "dungeons").mkdir(parents=True)
            (root / "npcs" / "stratholme").mkdir(parents=True)
            (root / "world" / "dungeons" / "stratholme.py").write_text(ST_FILE.read_text(encoding="utf-8"))
            for value, bound in (("False", False), ("True", True)):
                (root / "npcs" / "stratholme" / "_common.py").write_text(f"BIND_WAVE_2 = {value}\n")
                reg = registry.load_class_package(root / "world" / "dungeons", ids_cfg=IDS)
                overrides = {e: dict(p) for e, p in {x["map_id"]: x for x in reg.dungeons}[329]["heroic"]["overrides"]}
                for entry in (10516, 10558, 10808, 11032, 10997, 10811, 10812, 10813, 10387, 11054):
                    self.assertEqual(entry in overrides, bound, (value, entry))
                for entry in (10435, 10440, 11030, 11197, 10876):  # wave 1: always
                    self.assertIn(entry, overrides, (value, entry))

    def test_kit_add_overrides_follow_the_declared_templates(self):
        overrides = {entry: dict(pairs) for entry, pairs in self.heroic["overrides"]}
        expected = {entry: health for entry, health in KIT_HEALTH.items() if entry in _kit_declared()}
        self.assertEqual({e: o["health"] for e, o in overrides.items() if e >= 300000}, expected)

    def test_kit_add_overrides_appear_when_a_source_file_declares_the_template(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "world" / "dungeons").mkdir(parents=True)
            (root / "npcs" / "stratholme").mkdir(parents=True)
            (root / "world" / "dungeons" / "stratholme.py").write_text(ST_FILE.read_text(encoding="utf-8"))
            (root / "npcs" / "stratholme" / "boss.py").write_text(
                "cocoon = creature_template(\n    300582, 'Web Cocoon', **{})\n"
                "other = creature_template(300590, 'x')\n"
            )
            reg = registry.load_class_package(root / "world" / "dungeons", ids_cfg=IDS)
        overrides = {entry: dict(pairs) for entry, pairs in {e["map_id"]: e for e in reg.dungeons}[329]["heroic"][
            "overrides"]}
        self.assertEqual(sorted(e for e in overrides if e >= 300000), [300582])
        self.assertEqual(overrides[300582]["health"], 12_000)

    def test_every_override_names_a_listed_creature(self):
        listed = {c["entry"] for c in self.entry["creatures"]}
        for entry, _pairs in self.heroic["overrides"]:
            self.assertIn(entry, listed)


class ExpansionTest(unittest.TestCase):
    """The declaration against the live replay (warm cache: seconds; cold: a few minutes)."""

    @classmethod
    def setUpClass(cls):
        sqlcorpus.activate(generate.CACHE_DIR, generate.cache_code_version())
        try:
            creature_index = spell_tables.load_creature_table_index()
            existing = {int(r["entry"]): r for r in creature_index.live_rows("creature_template")}
            cls.dsl = {
                k: list(v) if isinstance(v, list) else v for k, v in registry.load_classes_dir(
                    generate.SOURCE_DIR / "world" / "dungeons", ids_cfg=IDS, existing_creature_rows=existing,
                    creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS, live_data={},
                ).items()
            }
            # The Stratholme boss package declares its kit adds (source/npcs/stratholme/) as they land
            kit_dir = generate.SOURCE_DIR / "npcs" / "stratholme"
            if kit_dir.is_dir():
                kit = registry.load_class_package(
                    kit_dir, ids_cfg=IDS, existing_creature_rows=existing,
                    creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
                    creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS, live_data={},
                )
                for key in ("creature_templates", "creature_template_models", "creature_template_edits"):
                    cls.dsl[key] = cls.dsl.get(key, []) + list(getattr(kit, key))
            # only Stratholme's heroic is expanded here (the other dungeons have their own tests)
            cls.dsl["dungeons"] = [e if e["map_id"] == 329 else dict(e, heroic=None) for e in cls.dsl["dungeons"]]
            cls.index = spell_tables.load_spell_table_index()
            cls.out = dungeon_heroic.expand(
                cls.dsl, lambda: dungeon_heroic.load_live_world(existing, cls.index), ids_cfg=IDS,
            )
            cls.existing = existing
        finally:
            sqlcorpus.deactivate()
        cls.entry = next(e for e in cls.dsl["dungeons"] if e["map_id"] == 329)
        cls.reports = {r.normal: r for r in cls.out.heroic_reports}

    def test_it_is_clean(self):
        self.assertEqual((self.out.errors, self.out.warnings), ([], []))

    def test_thirteen_encounters_in_the_stock_order_with_their_kill_credit(self):
        rows = sorted(self.dsl["dungeon_encounters"], key=lambda r: r["ID"])
        self.assertEqual([r["ID"] for r in rows], list(HEROIC_ENCOUNTERS))
        for row in rows:
            self.assertEqual((row["MapID"], row["Difficulty"]), (329, 1))
        credits = {r["entry"]: r["creditEntry"] for r in self.dsl["instance_encounters"]}
        self.assertEqual(credits, HEROIC_ENCOUNTERS)
        self.assertEqual([r["Name_Lang_enUS"] for r in rows], ENCOUNTER_NAMES)
        # each heroic row keeps its normal row's bit (the completed-encounter mask the dungeon clear reads)
        self.assertEqual([r["Bit"] for r in rows], [1, 2, 3, 4, 5, 6, 0, 7, 8, 9, 10, 11, 12])

    def test_the_creature_set(self):
        mapping = self.entry["heroic_entries"]
        for boss in BOSS_HEALTH:
            self.assertIn(boss, mapping)
        for hostile in (10381, 10418, 10400, 10409, 10411, 10387, 10876, 11054, 11197, 10394, 11030, 16101, 16102):
            self.assertIn(hostile, mapping)
        for out in NOT_HEROIC:
            self.assertNotIn(out, mapping)
        declared = {int(r["entry"]) for r in self.dsl["creature_templates"] if not r.get(dungeon_heroic.DERIVED)}
        for kit in KIT_HEALTH:
            self.assertEqual(kit in mapping, kit in declared, kit)
        block = IDS["creature_heroic"]
        locked = heroic_templates.parse_lock(heroic_templates.LOCK_PATH.read_text()).pairs
        for normal, heroic in mapping.items():
            self.assertTrue(block["start"] <= heroic <= block["end"], (normal, heroic))
        self.assertEqual(len(set(mapping.values())), len(mapping))
        self.assertFalse(set(mapping.values()) & {h for n, h in locked.items() if n not in mapping})

    def test_the_predicted_lock_lines(self):
        """The ids the first scoped write run mints (the boss lootids are the same numbers): normal-entry order from
        310120, 69 lines for the entries that exist today (the extraction set plus 10394 and 11030). The kit adds
        come after, wave by wave in entry order (310189 on, KIT_HEROIC_ID), and each add's creature_template must
        name its id in difficulty_entry_1."""
        mapping = self.entry["heroic_entries"]
        locked = heroic_templates.parse_lock(heroic_templates.LOCK_PATH.read_text()).pairs
        fresh = {n: h for n, h in mapping.items() if n not in locked}
        if set(fresh) != set(mapping):  # after the scoped write run the lines are committed: the same numbers
            fresh = mapping
        existing = {n: h for n, h in fresh.items() if n < 300000}
        self.assertEqual(sorted(existing.values()), list(range(310120, 310120 + len(existing))))
        self.assertEqual(sorted(existing), sorted(existing, key=lambda n: existing[n]))  # ids follow the entry order
        for boss, heroic in HEROIC_LOOTID.items():
            self.assertEqual(existing[boss], heroic, boss)
        self.assertEqual(existing[10812], 310169)
        self.assertEqual(len(existing), HEROIC_ENTRY_COUNT)
        for kit, heroic in KIT_HEROIC_ID.items():
            if kit in fresh:
                self.assertEqual(fresh[kit], heroic, kit)

    def test_bosses(self):
        rows = {int(r["entry"]): r for r in self.dsl["creature_templates"] if r.get(dungeon_heroic.DERIVED)}
        heroic_entry = self.entry["heroic_entries"]
        for boss, health in BOSS_HEALTH.items():
            with self.subTest(boss=boss):
                report = self.reports[boss]
                self.assertEqual(report.role, "boss")
                row = rows[heroic_entry[boss]]
                self.assertEqual((row["minlevel"], row["maxlevel"], row["exp"]), (60, 60, 0))
                self.assertEqual(int(row["flags_extra"]) & 1, 1)  # INSTANCE_BIND
                if boss not in BOUND_BOSSES:
                    continue  # a Main Gate boss: the tier and its stock row until wave 2
                self.assertEqual(report.solved.health, health)
                self.assertEqual(int(row["CreatureImmunitiesId"]), -419 if boss == 10440 else 1972)
                lootid = int(self.existing[boss]["lootid"])
                if OWN_LOOT and boss not in NO_LOOT:
                    lootid = HEROIC_LOOTID[boss]
                self.assertEqual(int(row["lootid"]), lootid)
        for (entry, wave), health in STOCK_ADD_HEALTH.items():
            if health is not None and wave in BOUND:
                self.assertEqual(self.reports[entry].solved.health, health, entry)
        for kit, health in KIT_HEALTH.items():
            if kit in self.reports:
                self.assertEqual(self.reports[kit].solved.health, health, kit)
        self.assertEqual(self.reports[10381].solved.health, 37_000)  # elite trash: the tier

    def test_the_smart_ai_of_the_normal_only_units_is_widened_to_heroic(self):
        sql = "\n".join(self.out.smart_blocks)
        self.assertIn("-- Stratholme (map 329) heroic:", sql)
        for entry in SMART_WIDENED:
            self.assertIn(f"`entryorguid` = {entry} AND `source_type` = 0", sql)
        self.assertEqual(sql.count("UPDATE `smart_scripts`"), 4)  # 10409, 10411 and the two out-of-scope smiths
        self.assertIn("`event_flags` | 4", sql)

    def test_spawn_masks_cover_the_boss_spawns_and_skip_the_game_event_ones(self):
        sql = "\n".join(self.out.spawn_blocks)
        self.assertIn("-- Stratholme (map 329) heroic:", sql)
        self.assertIn(329, self.out.map_spawns)
        creature_block = next(b for b in self.out.spawn_blocks if "UPDATE `creature` " in b)
        guids = {int(g) for g in re.findall(r"\d+", creature_block.split(") AND `guid` IN (")[1])}
        for guid in BOSS_SPAWN_GUIDS:
            self.assertIn(guid, guids)
        for guid in EVENT_GUIDS:  # Elder Farwhisper (event 7) and Balzaphon (event 120)
            self.assertNotIn(guid, guids)

    def test_the_patch_z_rows_merge_beside_the_stock_rows(self):
        md_path = state.BASE_DBC_DIR / dbcfmt.MAPDIFFICULTY.dbc_filename
        base = dbcfile.read_dbc(md_path, dbcfmt.MAPDIFFICULTY)
        merged = {r["ID"]: r for r in base}
        merged.update(dungeon_checks.map_difficulty_client_rows(self.dsl["map_difficulties"]))
        packed = dbcfile.pack_client_dbc(dbcfmt.MAPDIFFICULTY, list(merged.values()), base)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / dbcfmt.MAPDIFFICULTY.dbc_filename
            path.write_bytes(packed)
            back = dbcfile.read_dbc(path, dbcfmt.MAPDIFFICULTY)
        by_id = {r["ID"]: r for r in back}
        self.assertEqual((by_id[1003]["MapID"], by_id[1003]["Difficulty"]), (329, 1))
        self.assertEqual({k: v for k, v in by_id.items() if k < 1000}, {r["ID"]: r for r in base})
        order = [(r["MapID"], r["Difficulty"]) for r in back]
        self.assertEqual(order, sorted(order))
        self.assertEqual(sum(1 for r in back if r["MapID"] == 329 and r["Difficulty"] == 1), 1)

        de_path = state.BASE_DBC_DIR / dbcfmt.DUNGEONENCOUNTER.dbc_filename
        base_de = dbcfile.read_dbc(de_path, dbcfmt.DUNGEONENCOUNTER)
        merged_de = {r["ID"]: r for r in base_de}
        merged_de.update(dungeon_heroic.client_encounter_rows(self.dsl["dungeon_encounters"]))
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / dbcfmt.DUNGEONENCOUNTER.dbc_filename
            path.write_bytes(dbcfile.pack_client_dbc(dbcfmt.DUNGEONENCOUNTER, list(merged_de.values()), base_de))
            back_de = dbcfile.read_dbc(path, dbcfmt.DUNGEONENCOUNTER)
        self.assertEqual(len(back_de), len(base_de) + 13)
        self.assertEqual(sorted(r["ID"] for r in back_de if r["MapID"] == 329 and r["Difficulty"] == 1),
                         list(range(1028, 1041)))


if __name__ == "__main__":
    unittest.main()
