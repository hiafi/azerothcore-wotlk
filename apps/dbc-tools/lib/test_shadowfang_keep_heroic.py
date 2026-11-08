"""
Shadowfang Keep's heroic declaration (Shadowfang Keep build, WP-H): source/world/dungeons/shadowfang_keep.py as
generate.py loads it.

Covered: the heroic() arguments (MapDifficulty 1001, dungeon_access 123, DungeonEncounter 1007-1014, spawn masks, no
event spawns), the roles / skip / extra declarations, the heroic overrides against the build spec's numbers (handoff
3.7), the kit adds' overrides following the creature_template() declarations of source/npcs/shadowfang_keep/, and the
expansion against the live replay: no ERROR or WARNING, the eight encounters in the stock file's order with their kill
credit, the creature set (the cutscene Arugal, the NPCs, the event creatures and the unbuilt kit adds get no
template), the bosses' health, INSTANCE_BIND and stun immunity, Hummel's and Sever's spawns staying normal-only, and
the client MapDifficulty.dbc / DungeonEncounter.dbc rows (the patch-Z merge) beside the stock rows.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_shadowfang_keep_heroic.py
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

SFK_FILE = TOOL_ROOT / "source" / "world" / "dungeons" / "shadowfang_keep.py"
KIT_DIR = TOOL_ROOT / "source" / "npcs" / "shadowfang_keep"
IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")

# Normal encounter id -> boss entry, in the stock file's order (Rethilgore .. Arugal), and the heroic copies.
NORMAL_ENCOUNTERS = {464: 3914, 465: 3886, 466: 3887, 467: 4278, 468: 4279, 469: 4274, 470: 3927, 471: 4275}
HEROIC_ENCOUNTERS = dict(zip(range(1007, 1015), NORMAL_ENCOUNTERS.values()))
# Heroic health from the build spec (docs/dungeons/shadowfang-keep-rework.md, handoff 3.7).
BOSS_HEALTH = {
    3914: 265_524, 3886: 350_980, 3887: 305_200, 4278: 305_250, 4279: 320_460, 3872: 244_160, 4274: 259_420,
    3927: 244_160, 4275: 405_840,
}
KIT_HEALTH = {
    300500: 12_000, 300503: 20_000, 300504: 20_000, 300505: 20_000, 300506: 15_000, 300507: 15_000, 300508: 15_000,
    300509: 30_000, 300510: 30_000, 300511: 30_000, 300512: 30_000,
}
HUMMEL_GUID, SEVER_GUID = 146623, 248653  # game event 8 (Love is in the Air) and 120 (Scourge Invasion)


def _kit_declared() -> set[int]:
    pattern = re.compile(r"\bcreature_template\(\s*(\d+)\s*,")
    return {int(m) for path in KIT_DIR.glob("*.py") for m in pattern.findall(path.read_text(encoding="utf-8"))}


def _sfk_entry() -> dict:
    reg = registry.load_class_package(TOOL_ROOT / "source" / "world" / "dungeons", ids_cfg=IDS)
    return {e["map_id"]: e for e in reg.dungeons}[33], reg


# WP-L: each heroic boss drops its own loot (lootid = its own heroic entry, heroic_ids.lock).
HEROIC_LOOTID = {3914: 310048, 3886: 310046, 3887: 310047, 4278: 310052, 4279: 310053, 3872: 310042, 4274: 310050,
                 3927: 310049, 4275: 310051}


class DeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entry, cls.reg = _sfk_entry()
        cls.heroic = cls.entry["heroic"]

    def test_the_ids_are_the_next_of_their_blocks(self):
        self.assertEqual((self.heroic["map_difficulty_id"], self.heroic["access_id"]), (1001, 123))
        self.assertEqual(self.heroic["encounter_ids"], tuple(range(1007, 1015)))
        self.assertEqual(self.heroic["min_level"], 60)
        md = {r["ID"]: r for r in self.reg.map_difficulties}[1001]
        self.assertEqual((md["MapID"], md["Difficulty"], md["RaidDuration"], md["MaxPlayers"]), (33, 1, 86400, 5))
        self.assertEqual(md["Message_Lang_enUS"], "Heroic Difficulty requires you to be level 60.")
        access = {r["id"]: r for r in self.reg.dungeon_access}[123]
        self.assertEqual((access["map_id"], access["difficulty"], access["min_level"]), (33, 1, 60))

    def test_spawns_go_to_heroic_but_the_event_spawns_stay_normal_only(self):
        self.assertTrue(self.heroic["spawn_mask"])
        self.assertFalse(self.heroic["event_spawns"])

    def test_roles_and_skips(self):
        by_entry = {c["entry"]: c for c in self.entry["creatures"]}
        # the rare Captain: boss tier and INSTANCE_BIND (handoff s7 #14)
        self.assertEqual(by_entry[3872]["role"], "boss")
        self.assertEqual(
            sorted(e for e, c in by_entry.items() if c["role"] == "boss"), sorted({*BOSS_HEALTH}),
        )
        self.assertEqual(self.entry["skip"], (10000,))  # the non-combat cutscene Arugal
        # the kit adds that are not hostile combat units never get a heroic template
        for kit in (300501, 300502, 300513, 300514, 300515, 300516):
            self.assertIn(by_entry[kit]["role"], ("npc", "trigger"), kit)
        for kit in KIT_HEALTH:
            self.assertEqual(by_entry[kit]["role"], "trash", kit)

    def test_boss_overrides_are_the_build_specs_health_and_the_stun_immunity_set(self):
        overrides = {entry: dict(pairs) for entry, pairs in self.heroic["overrides"]}
        for entry, health in BOSS_HEALTH.items():
            with self.subTest(entry=entry):
                self.assertEqual(overrides[entry]["health"], health)
                self.assertEqual(dict(overrides[entry]["columns"]),
                                 {"CreatureImmunitiesId": 1972, "lootid": HEROIC_LOOTID[entry]})
        self.assertEqual(overrides[4627]["health"], 12_000)  # Arugal's Voidwalker

    def test_kit_add_overrides_follow_the_declared_templates(self):
        overrides = {entry: dict(pairs) for entry, pairs in self.heroic["overrides"]}
        expected = {entry: health for entry, health in KIT_HEALTH.items() if entry in _kit_declared()}
        self.assertEqual({e: o["health"] for e, o in overrides.items() if e >= 300500}, expected)

    def test_kit_add_overrides_appear_when_a_source_file_declares_the_template(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "world" / "dungeons").mkdir(parents=True)
            (root / "npcs" / "shadowfang_keep").mkdir(parents=True)
            (root / "world" / "dungeons" / "shadowfang_keep.py").write_text(SFK_FILE.read_text(encoding="utf-8"))
            (root / "npcs" / "shadowfang_keep" / "boss.py").write_text(
                "echo = creature_template(\n    300503, 'Echo of Rethilgore', **{})\n"
                "other = creature_template(300460, 'x')\n"
            )
            reg = registry.load_class_package(root / "world" / "dungeons", ids_cfg=IDS)
        overrides = {entry: dict(pairs) for entry, pairs in {e["map_id"]: e for e in reg.dungeons}[33]["heroic"][
            "overrides"]}
        self.assertEqual(sorted(e for e in overrides if e >= 300500), [300503])
        self.assertEqual(overrides[300503]["health"], 20_000)

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
            # The Shadowfang Keep boss package declares its kit adds (source/npcs/shadowfang_keep/) as they land
            kit = registry.load_class_package(
                generate.SOURCE_DIR / "npcs" / "shadowfang_keep", ids_cfg=IDS, existing_creature_rows=existing,
                creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
                creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS, live_data={},
            )
            for key in ("creature_templates", "creature_template_models", "creature_template_edits"):
                cls.dsl[key] = cls.dsl.get(key, []) + list(getattr(kit, key))
            # only Shadowfang Keep's heroic is expanded here (the Deadmines' has its own tests)
            cls.dsl["dungeons"] = [e if e["map_id"] == 33 else dict(e, heroic=None) for e in cls.dsl["dungeons"]]
            cls.index = spell_tables.load_spell_table_index()
            cls.out = dungeon_heroic.expand(
                cls.dsl, lambda: dungeon_heroic.load_live_world(existing, cls.index), ids_cfg=IDS,
            )
        finally:
            sqlcorpus.deactivate()
        cls.entry = next(e for e in cls.dsl["dungeons"] if e["map_id"] == 33)
        cls.reports = {r.normal: r for r in cls.out.heroic_reports}

    def test_it_is_clean(self):
        self.assertEqual((self.out.errors, self.out.warnings), ([], []))

    def test_eight_encounters_in_the_stock_order_with_their_kill_credit(self):
        rows = sorted(self.dsl["dungeon_encounters"], key=lambda r: r["ID"])
        self.assertEqual([r["ID"] for r in rows], list(HEROIC_ENCOUNTERS))
        for row in rows:
            self.assertEqual((row["MapID"], row["Difficulty"]), (33, 1))
        credits = {r["entry"]: r["creditEntry"] for r in self.dsl["instance_encounters"]}
        self.assertEqual(credits, HEROIC_ENCOUNTERS)
        self.assertEqual([r["Name_Lang_enUS"] for r in rows], [
            "Rethilgore", "Razorclaw the Butcher", "Baron Silverlaine", "Commander Springvale",
            "Odo the Blindwatcher", "Fenrus the Devourer", "Wolf Master Nandos", "Archmage Arugal",
        ])

    def test_the_creature_set(self):
        mapping = self.entry["heroic_entries"]
        for boss in BOSS_HEALTH:
            self.assertIn(boss, mapping)
        for hostile in (2529, 3854, 3861, 3862, 3863, 4627, 5058, 5097):
            self.assertIn(hostile, mapping)
        # the cutscene Arugal, the friendly NPCs, the critters, the triggers and the event creatures run on normal
        for out in (10000, 3849, 3850, 4444, 17822, 36296, 38208, 2110, 36212, 23033, 36530, 14682, 36272, 36565,
                    36885):
            self.assertNotIn(out, mapping)
        for kit in (300501, 300502, 300513, 300514, 300515, 300516):
            self.assertNotIn(kit, mapping)
        declared = {int(r["entry"]) for r in self.dsl["creature_templates"] if not r.get(dungeon_heroic.DERIVED)}
        for kit in KIT_HEALTH:
            self.assertEqual(kit in mapping, kit in declared, kit)
        block = IDS["creature_heroic"]
        deadmines = heroic_templates.parse_lock(heroic_templates.LOCK_PATH.read_text()).pairs
        for normal, heroic in mapping.items():
            self.assertTrue(block["start"] <= heroic <= block["end"], (normal, heroic))
        self.assertEqual(len(set(mapping.values())), len(mapping))
        self.assertFalse(set(mapping.values()) & {h for n, h in deadmines.items() if n not in mapping})

    def test_bosses(self):
        rows = {int(r["entry"]): r for r in self.dsl["creature_templates"] if r.get(dungeon_heroic.DERIVED)}
        heroic_entry = self.entry["heroic_entries"]
        for boss, health in BOSS_HEALTH.items():
            with self.subTest(boss=boss):
                report = self.reports[boss]
                self.assertEqual(report.role, "boss")
                self.assertEqual(report.solved.health, health)
                row = rows[heroic_entry[boss]]
                self.assertEqual((row["minlevel"], row["maxlevel"], row["exp"]), (60, 60, 0))
                self.assertEqual(int(row["flags_extra"]) & 1, 1)  # INSTANCE_BIND
                self.assertEqual(int(row["CreatureImmunitiesId"]), 1972)
        self.assertEqual(self.reports[3872].role, "boss")  # the Captain, by role
        self.assertEqual(self.reports[4275].solved.health, 405_840)
        self.assertEqual(self.reports[2529].solved.health, 37_000)  # elite trash: the tier
        self.assertEqual(self.reports[4627].solved.health, 12_000)
        for kit, health in KIT_HEALTH.items():
            if kit in self.reports:
                self.assertEqual(self.reports[kit].solved.health, health, kit)

    def test_spawn_masks_leave_the_event_spawns_alone(self):
        sql = "\n".join(self.out.spawn_blocks)
        self.assertIn("-- Shadowfang Keep (map 33) heroic:", sql)
        planned = self.out.map_spawns[33]
        self.assertIn(HUMMEL_GUID, planned["creature"])
        self.assertIn(SEVER_GUID, planned["creature"])
        creature_block = next(b for b in self.out.spawn_blocks if "UPDATE `creature` " in b)
        guids = {int(g) for g in re.findall(r"\d+", creature_block.split(") AND `guid` IN (")[1])}
        for guid in (16242, 16255, 134517, 18714):  # Rethilgore, Arugal, the Captain, Fenrus
            self.assertIn(guid, guids)
        for guid in (HUMMEL_GUID, SEVER_GUID):
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
        self.assertEqual((by_id[1001]["MapID"], by_id[1001]["Difficulty"]), (33, 1))
        self.assertEqual({k: v for k, v in by_id.items() if k < 1000}, {r["ID"]: r for r in base})
        order = [(r["MapID"], r["Difficulty"]) for r in back]
        self.assertEqual(order, sorted(order))
        self.assertEqual(sum(1 for r in back if r["MapID"] == 33 and r["Difficulty"] == 1), 1)

        de_path = state.BASE_DBC_DIR / dbcfmt.DUNGEONENCOUNTER.dbc_filename
        base_de = dbcfile.read_dbc(de_path, dbcfmt.DUNGEONENCOUNTER)
        merged_de = {r["ID"]: r for r in base_de}
        merged_de.update(dungeon_heroic.client_encounter_rows(self.dsl["dungeon_encounters"]))
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / dbcfmt.DUNGEONENCOUNTER.dbc_filename
            path.write_bytes(dbcfile.pack_client_dbc(dbcfmt.DUNGEONENCOUNTER, list(merged_de.values()), base_de))
            back_de = dbcfile.read_dbc(path, dbcfmt.DUNGEONENCOUNTER)
        self.assertEqual(len(back_de), len(base_de) + 8)
        ids = [r["ID"] for r in back_de]
        start = ids.index(464)
        self.assertEqual(ids[start:start + 16], [464, 1007, 465, 1008, 466, 1009, 467, 1010, 468, 1011, 469, 1012,
                                                  470, 1013, 471, 1014])


if __name__ == "__main__":
    unittest.main()
