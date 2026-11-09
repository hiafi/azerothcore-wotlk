"""
Scholomance's heroic declaration (Scholomance build, WP-H): source/world/dungeons/scholomance.py as generate.py loads
it.

Covered: the heroic() arguments (MapDifficulty 1002, dungeon_access 124, DungeonEncounter 1015-1027, spawn masks, no
event spawns), the roles / extra declarations, the heroic overrides against the build spec's numbers (handoff 3.6) and
the heroic loot ids (each boss drops its own heroic entry), the kit adds' overrides following the creature_template()
declarations of source/npcs/scholomance/, and the expansion against the live replay: no ERROR or WARNING, the thirteen
encounters in the stock file's order with their kill credit, the creature set and the predicted heroic_ids.lock lines
(310068 on, normal-entry order), the bosses' health, INSTANCE_BIND and stun immunity, the quiz student's and the other
adds' health, the game-event spawn staying normal-only, and the client MapDifficulty.dbc / DungeonEncounter.dbc rows
(the patch-Z merge) beside the stock rows.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scholomance_heroic.py
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

SC_FILE = TOOL_ROOT / "source" / "world" / "dungeons" / "scholomance.py"
KIT_DIR = TOOL_ROOT / "source" / "npcs" / "scholomance"
IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")

# Normal encounter id -> boss entry, in the stock file's order (Kirtonos .. Gandling), and the heroic copies.
NORMAL_ENCOUNTERS = {
    451: 10506, 452: 10503, 453: 11622, 454: 10433, 455: 10432, 456: 10508, 457: 10505, 458: 11261, 459: 10901,
    460: 10507, 461: 10504, 462: 10502, 463: 1853,
}
HEROIC_ENCOUNTERS = dict(zip(range(1015, 1028), NORMAL_ENCOUNTERS.values()))
# Heroic health from the build spec (docs/dungeons/scholomance-rework.md, handoff 3.6).
BOSS_HEALTH = {
    10503: 265_000, 11622: 280_000, 10433: 425_000, 10432: 425_000, 10508: 270_000, 10505: 250_000, 11261: 240_000,
    10901: 360_000, 10507: 210_000, 10504: 250_000, 10502: 250_000, 1853: 400_000,
}
# The predicted heroic ids: the lock mints in normal-entry order from 310068 (45 entries today, the kit adds after).
HEROIC_LOOTID = {
    1853: 310068, 10432: 310069, 10433: 310070, 10502: 310092, 10503: 310093, 10504: 310094, 10505: 310095,
    10507: 310097, 10508: 310098, 10901: 310100, 11261: 310103, 11622: 310110,
}
# WP-L: Marduk has no loot table and no gold (lootid 0); Vectus carries the encounter's list and the sum of the two
# stock purses (1,073-1,406 + 1,162-1,522 copper). The normal rows say the same (marduk_and_vectus.py).
MARDUK, VECTUS = 10433, 10432
HEROIC_COLUMNS = {
    MARDUK: {"lootid": 0, "mingold": 0, "maxgold": 0},
    VECTUS: {"mingold": 2235, "maxgold": 2928},
}
KIT_HEALTH = {
    300533: 22_000, 300536: 18_000, 300539: 9_000, 300540: 9_000, 300541: 9_000, 300542: 65_000, 300544: 25_000,
}
KIT_HEROIC_ID = {
    300533: 310113, 300536: 310114, 300539: 310115, 300540: 310116, 300541: 310117, 300542: 310118, 300544: 310119,
}
EXTRA = (11598, 11284, *KIT_HEALTH)
LORD_BLACKWOOD = 14695  # a game-event creature: normal-only
LORD_BLACKWOOD_GUID = 153321

# The wave each reworked boss is bound in (R-A S-11): a later wave's boss keeps its stock heroic copy until its wave
# flips BIND_WAVE_B / BIND_WAVE_C in source/npcs/scholomance/_common.py.
BOSS_WAVE = {
    10503: "A", 11622: "A", 10433: "A", 10432: "A", 10508: "A",
    10505: "B", 11261: "B", 10901: "B", 10507: "B", 10504: "B", 10502: "B",
    1853: "C",
}
SHELL_GAME_COPY = 11439
QUIZ_STUDENT = 10475


def _bound_waves() -> set[str]:
    text = (KIT_DIR / "_common.py").read_text(encoding="utf-8")
    return {"A"} | {w for w, v in re.findall(r"^BIND_WAVE_([BC])\s*=\s*(True|False)\s*$", text, re.M) if v == "True"}


def _own_heroic_loot() -> bool:
    """scholomance.py's `_HEROIC_BOSS_OWN_LOOT` (R-A S-2: off until WP-L declares the heroic loot)."""
    m = re.search(r"^_HEROIC_BOSS_OWN_LOOT\s*=\s*(True|False)\s*$", SC_FILE.read_text(encoding="utf-8"), re.M)
    return bool(m) and m.group(1) == "True"


BOUND = _bound_waves()
OWN_LOOT = _own_heroic_loot()
BOUND_BOSSES = {b for b, w in BOSS_WAVE.items() if w in BOUND}


def _kit_declared() -> set[int]:
    pattern = re.compile(r"\bcreature_template\(\s*(\d+)\s*,")
    return {int(m) for path in KIT_DIR.glob("*.py") for m in pattern.findall(path.read_text(encoding="utf-8"))}


def _sc_entry() -> dict:
    reg = registry.load_class_package(TOOL_ROOT / "source" / "world" / "dungeons", ids_cfg=IDS)
    return {e["map_id"]: e for e in reg.dungeons}[289], reg


class DeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entry, cls.reg = _sc_entry()
        cls.heroic = cls.entry["heroic"]

    def test_the_ids_are_the_next_of_their_blocks_after_shadowfang_keep(self):
        self.assertEqual((self.heroic["map_difficulty_id"], self.heroic["access_id"]), (1002, 124))
        self.assertEqual(self.heroic["encounter_ids"], tuple(range(1015, 1028)))
        self.assertEqual(self.heroic["min_level"], 60)
        md = {r["ID"]: r for r in self.reg.map_difficulties}[1002]
        self.assertEqual((md["MapID"], md["Difficulty"], md["RaidDuration"], md["MaxPlayers"]), (289, 1, 86400, 5))
        self.assertEqual(md["Message_Lang_enUS"], "Heroic Difficulty requires you to be level 60.")
        access = {r["id"]: r for r in self.reg.dungeon_access}[124]
        self.assertEqual((access["map_id"], access["difficulty"], access["min_level"]), (289, 1, 60))

    def test_spawns_go_to_heroic_but_the_event_spawns_stay_normal_only(self):
        self.assertTrue(self.heroic["spawn_mask"])
        self.assertFalse(self.heroic["event_spawns"])

    def test_roles_and_extras(self):
        by_entry = {c["entry"]: c for c in self.entry["creatures"]}
        # Kirtonos (an instance summon with an encounter row) and the eleven reworked bosses are the bosses
        self.assertEqual(sorted(e for e, c in by_entry.items() if c["role"] == "boss"),
                         sorted({*BOSS_HEALTH, 10506}))
        self.assertEqual(by_entry[10475]["role"], "trash")  # the quiz student takes a heroic template
        for extra in EXTRA:
            self.assertEqual(by_entry[extra]["role"], "trash", extra)
            self.assertTrue(by_entry[extra]["summoned_by"], extra)  # a C++ summon: no spawns, free text names who
            self.assertEqual(by_entry[extra]["spawns"], 0, extra)
        self.assertEqual(self.entry["skip"], ())

    def test_boss_overrides_are_the_build_specs_health_the_stun_immunity_set_and_the_own_heroic_loot(self):
        overrides = {entry: dict(pairs) for entry, pairs in self.heroic["overrides"]}
        self.assertEqual(BOSS_WAVE.keys(), BOSS_HEALTH.keys())
        for entry, health in BOSS_HEALTH.items():
            with self.subTest(entry=entry):
                if entry not in BOUND_BOSSES:
                    self.assertNotIn(entry, overrides)  # a later wave's boss: stock until its wave
                    continue
                self.assertEqual(overrides[entry]["health"], health)
                expected = {"CreatureImmunitiesId": 1972}
                if OWN_LOOT:
                    expected["lootid"] = HEROIC_LOOTID[entry]
                expected.update(HEROIC_COLUMNS.get(entry, {}))
                self.assertEqual(dict(overrides[entry]["columns"]), expected)
        self.assertNotIn(10506, overrides)  # Kirtonos stays stock, loot included
        self.assertEqual(overrides[QUIZ_STUDENT]["health"], 12_000)  # the quiz student
        self.assertEqual(dict(overrides[QUIZ_STUDENT]["columns"]), {"unit_flags": 0x2000042})  # a prop (R-A S-1)
        copy = overrides[SHELL_GAME_COPY]
        self.assertEqual(copy["health"], BOSS_HEALTH[10503])  # her health
        self.assertEqual(dict(copy["columns"])["unit_class"], 2)

    def test_all_waves_bound(self):
        # R-A S-11: wave C flips BIND_WAVE_C with the C++ kWaveCBound; every reworked boss is bound.
        self.assertEqual(BOUND, {"A", "B", "C"})
        self.assertTrue(OWN_LOOT)  # WP-L: every heroic boss drops its own loot (source/items/scholomance_loot.py)

    def test_kit_add_overrides_follow_the_declared_templates(self):
        overrides = {entry: dict(pairs) for entry, pairs in self.heroic["overrides"]}
        expected = {entry: health for entry, health in KIT_HEALTH.items() if entry in _kit_declared()}
        self.assertEqual({e: o["health"] for e, o in overrides.items() if e >= 300000}, expected)

    def test_kit_add_overrides_appear_when_a_source_file_declares_the_template(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "world" / "dungeons").mkdir(parents=True)
            (root / "npcs" / "scholomance").mkdir(parents=True)
            (root / "world" / "dungeons" / "scholomance.py").write_text(SC_FILE.read_text(encoding="utf-8"))
            (root / "npcs" / "scholomance" / "boss.py").write_text(
                "corvane = creature_template(\n    300542, 'Master Corvane', **{})\n"
                "other = creature_template(300560, 'x')\n"
            )
            reg = registry.load_class_package(root / "world" / "dungeons", ids_cfg=IDS)
        overrides = {entry: dict(pairs) for entry, pairs in {e["map_id"]: e for e in reg.dungeons}[289]["heroic"][
            "overrides"]}
        self.assertEqual(sorted(e for e in overrides if e >= 300000), [300542])
        self.assertEqual(overrides[300542]["health"], 65_000)
        # Master Corvane is stun immune like the bosses (handoff s7 #9) and has no loot
        self.assertEqual(dict(overrides[300542]["columns"]), {"CreatureImmunitiesId": 1972})

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
            # The Scholomance boss package declares its kit adds (source/npcs/scholomance/) as they land
            kit = registry.load_class_package(
                generate.SOURCE_DIR / "npcs" / "scholomance", ids_cfg=IDS, existing_creature_rows=existing,
                creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
                creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS, live_data={},
            )
            for key in ("creature_templates", "creature_template_models", "creature_template_edits"):
                cls.dsl[key] = cls.dsl.get(key, []) + list(getattr(kit, key))
            # only Scholomance's heroic is expanded here (the Deadmines' and Shadowfang Keep's have their own tests)
            cls.dsl["dungeons"] = [e if e["map_id"] == 289 else dict(e, heroic=None) for e in cls.dsl["dungeons"]]
            cls.index = spell_tables.load_spell_table_index()
            cls.out = dungeon_heroic.expand(
                cls.dsl, lambda: dungeon_heroic.load_live_world(existing, cls.index), ids_cfg=IDS,
            )
            cls.existing = existing
        finally:
            sqlcorpus.deactivate()
        cls.entry = next(e for e in cls.dsl["dungeons"] if e["map_id"] == 289)
        cls.reports = {r.normal: r for r in cls.out.heroic_reports}

    def test_it_is_clean(self):
        self.assertEqual((self.out.errors, self.out.warnings), ([], []))

    def test_thirteen_encounters_in_the_stock_order_with_their_kill_credit(self):
        rows = sorted(self.dsl["dungeon_encounters"], key=lambda r: r["ID"])
        self.assertEqual([r["ID"] for r in rows], list(HEROIC_ENCOUNTERS))
        for row in rows:
            self.assertEqual((row["MapID"], row["Difficulty"]), (289, 1))
        credits = {r["entry"]: r["creditEntry"] for r in self.dsl["instance_encounters"]}
        self.assertEqual(credits, HEROIC_ENCOUNTERS)
        self.assertEqual([r["Name_Lang_enUS"] for r in rows], [
            "Kirtonos the Herald", "Jandice Barov", "Rattlegore", "Marduk Blackpool", "Vectus", "Ras Frostwhisper",
            "Instructor Malicia", "Doctor Theolen Krastinov", "Lorekeeper Polkelt", "The Ravenian",
            "Lord Alexei Barov", "Lady Illucia Barov", "Darkmaster Gandling",
        ])

    def test_the_creature_set(self):
        mapping = self.entry["heroic_entries"]
        for boss in (*BOSS_HEALTH, 10506):
            self.assertIn(boss, mapping)
        for hostile in (10469, 10472, 10475, 10480, 10678, 11439, 11598, 11284, 16118, 14861):
            self.assertIn(hostile, mapping)
        # the rats, the Kormok trigger and the event creature (Lord Blackwood) run on normal
        for out in (2110, 4075, 16047, LORD_BLACKWOOD):
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
        """The ids the first scoped write run mints (the boss lootids above are the same numbers): normal-entry order
        from 310068, 45 lines for the entries that exist today. The kit adds come after, in entry order (310113 on,
        KIT_HEROIC_ID), and each add's creature_template must name its id in difficulty_entry_1."""
        mapping = self.entry["heroic_entries"]
        locked = heroic_templates.parse_lock(heroic_templates.LOCK_PATH.read_text()).pairs
        fresh = {n: h for n, h in mapping.items() if n not in locked}
        if set(fresh) != set(mapping):  # after the scoped write run the lines are committed: the same numbers
            fresh = mapping
        existing = {n: h for n, h in fresh.items() if n < 300000}
        self.assertEqual(sorted(existing.values()), list(range(310068, 310068 + len(existing))))
        self.assertEqual(sorted(existing), sorted(existing, key=lambda n: existing[n]))  # ids follow the entry order
        for boss, heroic in HEROIC_LOOTID.items():
            self.assertEqual(existing[boss], heroic, boss)
        self.assertEqual(len(existing), 45)
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
                    continue  # a later wave's boss: the tier and its stock row (R-A S-11)
                self.assertEqual(report.solved.health, health)
                self.assertEqual(int(row["CreatureImmunitiesId"]), 1972)
                # Its own heroic loot (WP-L); Marduk has none (lootid 0, no gold), Vectus carries the encounter's purse
                lootid = HEROIC_LOOTID[boss] if OWN_LOOT else int(self.existing[boss]["lootid"])
                lootid = HEROIC_COLUMNS.get(boss, {}).get("lootid", lootid)
                self.assertEqual(int(row["lootid"]), lootid)
                for column in ("mingold", "maxgold"):
                    if column in HEROIC_COLUMNS.get(boss, {}):
                        self.assertEqual(int(row[column]), HEROIC_COLUMNS[boss][column], (boss, column))
        kirtonos = rows[heroic_entry[10506]]
        self.assertEqual(self.reports[10506].role, "boss")
        self.assertEqual(int(kirtonos["flags_extra"]) & 1, 1)
        self.assertNotEqual(int(kirtonos["CreatureImmunitiesId"]), 1972)  # stock: the override leaves him alone
        self.assertEqual(self.reports[10475].solved.health, 12_000)  # the quiz student
        self.assertEqual(self.reports[10469].solved.health, 37_000)  # elite trash: the tier
        for kit, health in KIT_HEALTH.items():
            if kit in self.reports:
                self.assertEqual(self.reports[kit].solved.health, health, kit)

    def test_the_shell_game_copy_matches_jandice(self):
        """R-A S-1: the heroic copy of 11439 carries her class, mana, immunity set, flags and stillness (not the stock
        row's warrior class and -273 set, which the engine would refuse to link and the players would see)."""
        rows = {int(r["entry"]): r for r in self.dsl["creature_templates"] if r.get(dungeon_heroic.DERIVED)}
        heroic_entry = self.entry["heroic_entries"]
        copy = rows[heroic_entry[SHELL_GAME_COPY]]
        jandice = rows[heroic_entry[10503]]
        for column, value in (("unit_class", 2), ("unit_flags", 32832), ("CreatureImmunitiesId", 1972),
                              ("speed_walk", 1.0), ("MovementType", 0), ("RegenHealth", 0), ("flags_extra", 0x40),
                              ("ManaModifier", 3.0)):
            with self.subTest(column=column):
                self.assertEqual(float(copy[column]), float(value))
        for column in ("unit_class", "unit_flags", "CreatureImmunitiesId", "ManaModifier", "speed_walk"):
            with self.subTest(her=column):
                self.assertEqual(float(copy[column]), float(jandice[column]))
        self.assertEqual(self.reports[SHELL_GAME_COPY].solved.health, BOSS_HEALTH[10503])
        student = rows[heroic_entry[QUIZ_STUDENT]]
        self.assertEqual(int(student["unit_flags"]), 0x2000042)  # a prop until its quiz

    def test_spawn_masks_cover_the_boss_spawns(self):
        sql = "\n".join(self.out.spawn_blocks)
        if "-- Scholomance (map 289) heroic:" not in sql:
            self.skipTest("the map 289 spawn masks are already live (wave A), so no spawn block is emitted")
        self.assertIn(289, self.out.map_spawns)
        creature_block = next(b for b in self.out.spawn_blocks if "UPDATE `creature` " in b)
        guids = {int(g) for g in re.findall(r"\d+", creature_block.split(") AND `guid` IN (")[1])}
        for guid in (48807, 48910, 48806, 48805, 48850, 48867, 48925, 48946, 48854, 48863, 48857, 247104):
            self.assertIn(guid, guids)  # the twelve boss spawns
        self.assertNotIn(LORD_BLACKWOOD_GUID, guids)  # Lord Blackwood belongs to game event 120 (Scourge Invasion)

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
        self.assertEqual((by_id[1002]["MapID"], by_id[1002]["Difficulty"]), (289, 1))
        self.assertEqual({k: v for k, v in by_id.items() if k < 1000}, {r["ID"]: r for r in base})
        order = [(r["MapID"], r["Difficulty"]) for r in back]
        self.assertEqual(order, sorted(order))
        self.assertEqual(sum(1 for r in back if r["MapID"] == 289 and r["Difficulty"] == 1), 1)

        de_path = state.BASE_DBC_DIR / dbcfmt.DUNGEONENCOUNTER.dbc_filename
        base_de = dbcfile.read_dbc(de_path, dbcfmt.DUNGEONENCOUNTER)
        merged_de = {r["ID"]: r for r in base_de}
        merged_de.update(dungeon_heroic.client_encounter_rows(self.dsl["dungeon_encounters"]))
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / dbcfmt.DUNGEONENCOUNTER.dbc_filename
            path.write_bytes(dbcfile.pack_client_dbc(dbcfmt.DUNGEONENCOUNTER, list(merged_de.values()), base_de))
            back_de = dbcfile.read_dbc(path, dbcfmt.DUNGEONENCOUNTER)
        self.assertEqual(len(back_de), len(base_de) + 13)
        ids = [r["ID"] for r in back_de]
        start = ids.index(451)
        want = [i for pair in zip(range(451, 464), range(1015, 1028)) for i in pair]
        self.assertEqual(ids[start:start + 26], want)


if __name__ == "__main__":
    unittest.main()
