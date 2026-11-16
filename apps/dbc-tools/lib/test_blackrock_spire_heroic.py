"""
Blackrock Spire's heroic declaration (Blackrock Spire build, WP-H): source/world/dungeons/blackrock_spire.py as
generate.py loads it, and the Finder entries of source/world/lfg_classic_heroic.py for map 229.

Covered: the heroic() arguments (MapDifficulty 1004 with MaxPlayers 10, dungeon_access 126, DungeonEncounter
1041-1054, spawn masks, no event spawns), the roles / extra declarations, the heroic overrides against the build spec's
numbers (handoff 3.6) and the predicted heroic loot ids, the wave switch (BIND_WAVE_2: the Upper Spire bosses keep their
stock heroic copy until wave 2 binds them), the kit adds' overrides following the creature_template() declarations of
source/npcs/blackrock_spire/, and the expansion against the live replay: no ERROR or WARNING, the fourteen encounters
in the stock file's order (OrderIndex, not id: Halycon before Gizrul) with their kill credit, the creature set and the
predicted heroic_ids.lock lines (310195 on, normal-entry order), the bosses' INSTANCE_BIND and immunity sets (1972),
the SmartAI widening, the game-event spawns staying normal-only, the client MapDifficulty.dbc / DungeonEncounter.dbc
rows (the patch-Z merge) beside the stock rows, and the finder: Upper Blackrock Spire (LFGDungeons 44) made a dungeon
entry, its start point before the Dragonspire Hall trigger, and the two heroic entries (306, 307) each completing on
its own final boss.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_spire_heroic.py
"""

from __future__ import annotations

import math
import re
import sys
import tempfile
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import generate  # noqa: E402
from lib import dbcfile, dbcfmt, dungeon_checks, dungeon_heroic, heroic_templates, lfg_dungeons, source  # noqa: E402
from lib import spell_tables, sqlcorpus, state  # noqa: E402
from lib.dsl import registry  # noqa: E402

_MARKER = "-- Blackrock Spire (map 229) heroic:"
_PENDING = TOOL_ROOT.parents[1] / "data" / "sql" / "updates" / "pending_db_world"


def _rendered_or_committed(blocks: list[str]) -> tuple[str, bool]:
    """The rendered blocks, or (after the scoped write run made them live) the committed rev that carries them."""
    sql = "\n".join(blocks)
    if _MARKER in sql:
        return sql, False
    texts = [f.read_text() for f in sorted(_PENDING.glob("rev_*.sql"))]
    return "\n".join(t for t in texts if _MARKER in t), True


BRS_FILE = TOOL_ROOT / "source" / "world" / "dungeons" / "blackrock_spire.py"
LFG_FILE = TOOL_ROOT / "source" / "world" / "lfg_classic_heroic.py"
KIT_DIR = TOOL_ROOT / "source" / "npcs" / "blackrock_spire"
IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")

# The normal encounters in the stock file's order (OrderIndex: Omokk 0 ... Zigris 5000, Halycon 274 at 5500, Gizrul 273
# at 6000, then 8000 ... 13000), paired with the heroic ids 1041-1054 in that order; and the boss each credits.
STOCK_ORDER = (267, 268, 269, 270, 271, 272, 274, 273, 275, 276, 277, 278, 279, 280)
NORMAL_CREDIT = {
    267: 9196, 268: 9236, 269: 9237, 270: 10596, 271: 10584, 272: 9736, 273: 10268, 274: 10220, 275: 9568, 276: 9816,
    277: 10264, 278: 10429, 279: 10430, 280: 10363,
}
HEROIC_ENCOUNTERS = {hid: NORMAL_CREDIT[nid] for hid, nid in zip(range(1041, 1055), STOCK_ORDER)}
ENCOUNTER_NAMES = [
    "Highlord Omokk", "Shadow Hunter Vosh'gajin", "War Master Voone", "Mother Smolderweb", "Urok Doomhowl",
    "Quartermaster Zigris", "Halycon", "Gizrul the Slavener", "Overlord Wyrmthalak", "Pyroguard Emberseer",
    "Solakar Flamewreath", "Warchief Rend Blackhand", "The Beast", "General Drakkisath",
]
ENCOUNTER_BITS = [0, 1, 2, 3, 4, 5, 7, 6, 8, 9, 10, 11, 12, 13]  # Halycon's bit is 7, Gizrul's 6 (stock)

# Heroic health at 5 players from the build spec (docs/dungeons/blackrock-spire-rework.md, handoff 3.6) and the wave
# each boss binds in. Gyth (10339) has no encounter row of his own: a boss by role.
BOSS_HEALTH = {
    9196: 230_000, 9236: 230_000, 9237: 230_000, 10596: 218_000, 10584: 195_000, 9736: 185_000, 10220: 150_000,
    10268: 150_000, 9568: 260_000, 9816: 225_000, 10264: 220_000, 10339: 200_000, 10429: 210_000, 10430: 235_000,
    10363: 310_000,
}
BOSS_WAVE = {entry: "1" for entry in (9196, 9236, 9237, 10596, 10584, 9736, 10220, 10268, 9568)}
BOSS_WAVE.update({entry: "2" for entry in (9816, 10264, 10339, 10429, 10430, 10363)})
# The predicted heroic ids: the lock mints in normal-entry order from 310195 and the boss lootids are the same numbers.
HEROIC_LOOTID = {
    9196: 310199, 9236: 310209, 9237: 310210, 9568: 310228, 9736: 310240, 9816: 310241, 10220: 310250, 10264: 310255,
    10268: 310256, 10339: 310262, 10363: 310263, 10429: 310270, 10430: 310271, 10584: 310275, 10596: 310276,
}
EMBERSEER = 9816
# Stock-id units with a heroic health override, and the wave each binds in
STOCK_ADD_HEALTH = {
    (10316, "2"): 9_500, (10258, "2"): 38_000, (10683, "2"): 32_000, (10442, "2"): 5_000, (10447, "2"): 19_000,
    (10742, "2"): 11_000, (10814, "2"): 32_000,
}
KIT_HEALTH = {  # new kit adds (handoff 3.3 ids): heroic health
    300702: 12_000, 300705: 3_000, 300707: 3_000, 300708: 32_000, 300709: 32_000, 300710: 32_000, 300711: 6_000,
    300731: 4_000, 300733: 20_000, 300736: 17_000, 300737: 23_000, 300738: 13_000, 300739: 21_000,
}
KIT_HEROIC_ID = {  # minted after the extraction set, in entry order, wave by wave (the mint-order note)
    300702: 310288, 300705: 310289, 300707: 310290, 300708: 310291, 300709: 310292, 300710: 310293, 300711: 310294,
    300731: 310295, 300733: 310296, 300736: 310297, 300737: 310298, 300738: 310299, 300739: 310300,
}
STOCK_EXTRA = (10161, 10258, 10339, 10601, 10602, 10683)  # the stock event units the extraction cannot see
EXTRA = (*STOCK_EXTRA, *KIT_HEALTH)
HEROIC_ENTRY_COUNT = 93  # the 87 hostile extraction creatures plus the six stock extras, before any kit add lands
NOT_HEROIC = (10162, 300732, 10257, 10296, 10740, 10799, 15560,  # friendly NPCs and the event Elder Stonefort
              16044, 16048)  # triggers
SMART_WIDENED = (10442, 10447)
# The 14 boss spawns and Nefarius' (BRS spawn 137967; it keeps the normal entry) are heroic-masked; the Elder Stonefort
# (game event 7) and the one event gameobject (event 203) stay normal-only.
BOSS_SPAWN_GUIDS = (43518, 43522, 45840, 45757, 45749, 137817, 40245, 137971, 137968, 137969, 44342)
EVENT_CREATURE_GUIDS = (78383,)
ENTRANCE = (78.5083, -225.044, 49.839)  # LFGDungeons 32 / areatrigger_teleport 1468 (the Lower Spire)
DRAGONSPIRE_TRIGGER = (102.43, -319.167, 65.4635, 10.0)  # areatrigger 2046: x, y, z, radius


def _bound_waves() -> set[str]:
    path = KIT_DIR / "_common.py"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    return {"1"} | {w for w, v in re.findall(r"^BIND_WAVE_(2)\s*=\s*(True|False)\s*$", text, re.M) if v == "True"}


def _own_heroic_loot() -> bool:
    """blackrock_spire.py's `_HEROIC_BOSS_OWN_LOOT` (off until L-1 declares the heroic loot groups: the Scholomance
    R-A S-2 rule, a lootid with no loot_template rows behind it drops nothing)."""
    m = re.search(r"^_HEROIC_BOSS_OWN_LOOT\s*=\s*(True|False)\s*$", BRS_FILE.read_text(encoding="utf-8"), re.M)
    return bool(m) and m.group(1) == "True"


BOUND = _bound_waves()
OWN_LOOT = _own_heroic_loot()
BOUND_BOSSES = {b for b, w in BOSS_WAVE.items() if w in BOUND}


def _kit_declared() -> set[int]:
    pattern = re.compile(r"\bcreature_template\(\s*(\d+)\s*,")
    return {int(m) for path in KIT_DIR.glob("*.py") for m in pattern.findall(path.read_text(encoding="utf-8"))}


def _brs_entry() -> tuple[dict, object]:
    reg = registry.load_class_package(TOOL_ROOT / "source" / "world" / "dungeons", ids_cfg=IDS)
    return {e["map_id"]: e for e in reg.dungeons}[229], reg


class DeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entry, cls.reg = _brs_entry()
        cls.heroic = cls.entry["heroic"]

    def test_the_ids_are_the_next_of_their_blocks_after_stratholme(self):
        self.assertEqual((self.heroic["map_difficulty_id"], self.heroic["access_id"]), (1004, 126))
        self.assertEqual(self.heroic["encounter_ids"], tuple(range(1041, 1055)))
        self.assertEqual(self.heroic["min_level"], 60)

    def test_the_heroic_row_is_a_ten_player_row(self):
        self.assertEqual(self.heroic["max_players"], 10)
        md = {r["ID"]: r for r in self.reg.map_difficulties}[1004]
        self.assertEqual((md["MapID"], md["Difficulty"], md["RaidDuration"], md["MaxPlayers"]), (229, 1, 86400, 10))
        self.assertEqual(md["Message_Lang_enUS"], "Heroic Difficulty requires you to be level 60.")
        access = {r["id"]: r for r in self.reg.dungeon_access}[126]
        self.assertEqual((access["map_id"], access["difficulty"], access["min_level"]), (229, 1, 60))

    def test_spawns_go_to_heroic_but_the_event_spawns_stay_normal_only(self):
        self.assertTrue(self.heroic["spawn_mask"])
        self.assertFalse(self.heroic["event_spawns"])

    def test_roles_and_extras(self):
        by_entry = {c["entry"]: c for c in self.entry["creatures"]}
        # the thirteen extracted bosses (Omokk ... Drakkisath, Solakar and Gizrul included) plus Gyth, a boss by extra
        self.assertEqual(sorted(e for e, c in by_entry.items() if c["role"] == "boss"), sorted(BOSS_HEALTH))
        for extra in EXTRA:
            self.assertEqual(by_entry[extra]["role"], "boss" if extra == 10339 else "trash", extra)
            self.assertTrue(by_entry[extra]["summoned_by"], extra)  # a C++ summon: no spawns, free text names who
            self.assertEqual(by_entry[extra]["spawns"], 0, extra)
        self.assertEqual(self.entry["skip"], ())  # the out-of-scope rares keep their tier template (handoff 7 #23)

    def test_boss_overrides_are_the_build_specs_health_the_immunity_set_and_the_loot_flag(self):
        overrides = {entry: dict(pairs) for entry, pairs in self.heroic["overrides"]}
        for entry, health in BOSS_HEALTH.items():
            with self.subTest(entry=entry):
                if entry not in BOUND_BOSSES:
                    self.assertNotIn(entry, overrides)  # an Upper Spire boss: stock until wave 2 binds it
                    continue
                self.assertEqual(overrides[entry]["health"], health)
                expected = {"CreatureImmunitiesId": 1973 if entry == EMBERSEER else 1972}
                if OWN_LOOT:
                    expected["lootid"] = HEROIC_LOOTID[entry]
                self.assertEqual(dict(overrides[entry]["columns"]), expected)

    def test_the_stock_id_adds_follow_their_wave(self):
        overrides = {entry: dict(pairs) for entry, pairs in self.heroic["overrides"]}
        for (entry, wave), health in STOCK_ADD_HEALTH.items():
            with self.subTest(entry=entry):
                if wave not in BOUND:
                    self.assertNotIn(entry, overrides)
                else:
                    self.assertEqual(overrides[entry]["health"], health)
                    self.assertNotIn("columns", overrides[entry])

    def test_wave_1_is_bound_and_the_wave_switch_is_read_from_the_npc_package(self):
        self.assertIn("1", BOUND)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "world" / "dungeons").mkdir(parents=True)
            (root / "npcs" / "blackrock_spire").mkdir(parents=True)
            (root / "world" / "dungeons" / "blackrock_spire.py").write_text(BRS_FILE.read_text(encoding="utf-8"))
            for value, bound in (("False", False), ("True", True)):
                (root / "npcs" / "blackrock_spire" / "_common.py").write_text(f"BIND_WAVE_2 = {value}\n")
                reg = registry.load_class_package(root / "world" / "dungeons", ids_cfg=IDS)
                overrides = {e: dict(p) for e, p in {x["map_id"]: x for x in reg.dungeons}[229]["heroic"]["overrides"]}
                for entry in (9816, 10264, 10339, 10429, 10430, 10363, 10316, 10258, 10683, 10442, 10447, 10742,
                              10814):
                    self.assertEqual(entry in overrides, bound, (value, entry))
                for entry in (9196, 9568, 10584, 10268):  # wave 1: always
                    self.assertIn(entry, overrides, (value, entry))

    def test_a_missing_common_file_reads_as_wave_2_off(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "world" / "dungeons").mkdir(parents=True)
            (root / "world" / "dungeons" / "blackrock_spire.py").write_text(BRS_FILE.read_text(encoding="utf-8"))
            reg = registry.load_class_package(root / "world" / "dungeons", ids_cfg=IDS)
        overrides = {e: dict(p) for e, p in {x["map_id"]: x for x in reg.dungeons}[229]["heroic"]["overrides"]}
        self.assertEqual(sorted(overrides), sorted(e for e, w in BOSS_WAVE.items() if w == "1"))

    def test_kit_add_overrides_follow_the_declared_templates(self):
        overrides = {entry: dict(pairs) for entry, pairs in self.heroic["overrides"]}
        declared = _kit_declared()
        # applied to every declared template regardless of the wave switch (like Stratholme's `_KIT_ADD_HEROIC`): the
        # wave only gates the stock-id and boss overrides
        expected = {e: h for e, h in KIT_HEALTH.items() if e in declared}
        self.assertEqual({e: o["health"] for e, o in overrides.items() if e >= 300000}, expected)

    def test_kit_add_overrides_appear_when_a_source_file_declares_the_template(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "world" / "dungeons").mkdir(parents=True)
            (root / "npcs" / "blackrock_spire").mkdir(parents=True)
            (root / "world" / "dungeons" / "blackrock_spire.py").write_text(BRS_FILE.read_text(encoding="utf-8"))
            (root / "npcs" / "blackrock_spire" / "boss.py").write_text(
                "mystic = creature_template(\n    300702, 'Spirestone Mojo Mystic', **{})\n"
                "other = creature_template(300703, 'Voodoo Doll')\n"
            )
            reg = registry.load_class_package(root / "world" / "dungeons", ids_cfg=IDS)
        overrides = {entry: dict(pairs) for entry, pairs in {e["map_id"]: e for e in reg.dungeons}[229]["heroic"][
            "overrides"]}
        self.assertEqual(sorted(e for e in overrides if e >= 300000), [300702])  # the Doll gets no heroic template
        self.assertEqual(overrides[300702]["health"], 12_000)

    def test_every_override_names_a_listed_creature(self):
        listed = {c["entry"] for c in self.entry["creatures"]}
        for entry, _pairs in self.heroic["overrides"]:
            self.assertIn(entry, listed)

    def test_the_mint_order_puts_every_wave_1_add_below_every_wave_2_add(self):
        wave_1 = [e for e in KIT_HEALTH if e < 300730]
        wave_2 = [e for e in KIT_HEALTH if e >= 300730]
        self.assertLess(max(wave_1), min(wave_2))
        self.assertEqual(sorted(KIT_HEROIC_ID.values()), list(range(310288, 310288 + len(KIT_HEROIC_ID))))
        self.assertEqual(sorted(KIT_HEROIC_ID), sorted(KIT_HEROIC_ID, key=KIT_HEROIC_ID.get))


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
            # The Blackrock Spire boss package declares its kit adds (source/npcs/blackrock_spire/) as they land
            if KIT_DIR.is_dir():
                kit = registry.load_class_package(
                    KIT_DIR, ids_cfg=IDS, existing_creature_rows=existing,
                    creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
                    creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS, live_data={},
                )
                for key in ("creature_templates", "creature_template_models", "creature_template_edits"):
                    cls.dsl[key] = cls.dsl.get(key, []) + list(getattr(kit, key))
            # only Blackrock Spire's heroic is expanded here (the other dungeons have their own tests)
            cls.dsl["dungeons"] = [e if e["map_id"] == 229 else dict(e, heroic=None) for e in cls.dsl["dungeons"]]
            cls.index = spell_tables.load_spell_table_index()
            cls.out = dungeon_heroic.expand(
                cls.dsl, lambda: dungeon_heroic.load_live_world(existing, cls.index), ids_cfg=IDS,
            )
            cls.existing = existing
            # generate.py's next step: the finder (source/world/lfg_classic_heroic.py) with only this map's entries
            lfg = registry.load_class_file(LFG_FILE, ids_cfg=IDS)
            cls.dsl["lfg_group_declarations"] = list(lfg.lfg_group_declarations)
            cls.dsl["lfg_dungeon_declarations"] = [
                d for d in lfg.lfg_dungeon_declarations
                if d["kind"] in ("random", "override") or d["normal"] in (32, 44)
            ]
            cls.lfg_out = lfg_dungeons.expand(cls.dsl, lambda: lfg_dungeons.load_inputs(cls.index))
        finally:
            sqlcorpus.deactivate()
        cls.entry = next(e for e in cls.dsl["dungeons"] if e["map_id"] == 229)
        cls.reports = {r.normal: r for r in cls.out.heroic_reports}

    def test_it_is_clean(self):
        self.assertEqual((self.out.errors, self.out.warnings), ([], []))
        self.assertEqual((self.lfg_out.errors, self.lfg_out.warnings), ([], []))

    def test_fourteen_encounters_in_the_stock_order_with_their_kill_credit(self):
        rows = sorted(self.dsl["dungeon_encounters"], key=lambda r: r["ID"])
        self.assertEqual([r["ID"] for r in rows], list(HEROIC_ENCOUNTERS))
        for row in rows:
            self.assertEqual((row["MapID"], row["Difficulty"]), (229, 1))
        credits = {r["entry"]: r["creditEntry"] for r in self.dsl["instance_encounters"]}
        self.assertEqual(credits, HEROIC_ENCOUNTERS)
        self.assertEqual([r["Name_Lang_enUS"] for r in rows], ENCOUNTER_NAMES)
        # each heroic row keeps its normal row's bit (the completed-encounter mask the dungeon clear reads); Halycon
        # (bit 7) and Gizrul (bit 6) stay two rows, in the stock order
        self.assertEqual([r["Bit"] for r in rows], ENCOUNTER_BITS)

    def test_the_creature_set(self):
        mapping = self.entry["heroic_entries"]
        for boss in BOSS_HEALTH:
            self.assertIn(boss, mapping)
        for hostile in (9097, 9096, 9583, 9216, 10442, 10447, 10742, 10814, 10316, 10258, 10683, 10161, 10601, 10602,
                        10339, 16042, 16080, 10899):
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
        310195, 93 lines for the entries that exist today (the extraction set plus the six stock extras). The kit adds
        come after, wave by wave in entry order (310288 on, KIT_HEROIC_ID), and each add's creature_template must
        name its id in difficulty_entry_1."""
        mapping = self.entry["heroic_entries"]
        locked = heroic_templates.parse_lock(heroic_templates.LOCK_PATH.read_text()).pairs
        fresh = {n: h for n, h in mapping.items() if n not in locked}
        if set(fresh) != set(mapping):  # after the scoped write run the lines are committed: the same numbers
            fresh = mapping
        existing = {n: h for n, h in fresh.items() if n < 300000}
        self.assertEqual(sorted(existing.values()), list(range(310195, 310195 + len(existing))))
        self.assertEqual(sorted(existing), sorted(existing, key=lambda n: existing[n]))  # ids follow the entry order
        for boss, heroic in HEROIC_LOOTID.items():
            self.assertEqual(existing[boss], heroic, boss)
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
                    continue  # an Upper Spire boss: the tier and its stock row until wave 2
                self.assertEqual(report.solved.health, health)
                self.assertEqual(int(row["CreatureImmunitiesId"]), 1973 if boss == EMBERSEER else 1972)
                lootid = int(self.existing[boss]["lootid"])
                if OWN_LOOT:
                    lootid = HEROIC_LOOTID[boss]
                self.assertEqual(int(row["lootid"]), lootid)
        for (entry, wave), health in STOCK_ADD_HEALTH.items():
            if wave in BOUND:
                self.assertEqual(self.reports[entry].solved.health, health, entry)
        for kit, health in KIT_HEALTH.items():
            if kit in self.reports:
                self.assertEqual(self.reports[kit].solved.health, health, kit)
        self.assertEqual(self.reports[9097].solved.health, 37_000)  # elite trash: the tier

    def test_the_smart_ai_of_the_normal_only_units_is_widened_to_heroic(self):
        sql, _ = _rendered_or_committed(self.out.smart_blocks)
        self.assertIn(_MARKER, sql)
        self.assertIn("`event_flags` | 4", sql)
        for entry in SMART_WIDENED:
            self.assertIn(f"`entryorguid` = {entry} AND `source_type` = 0", sql)

    def test_spawn_masks_cover_the_boss_spawns_and_skip_the_game_event_ones(self):
        sql, committed = _rendered_or_committed(self.out.spawn_blocks)
        self.assertIn(_MARKER, sql)
        if not committed:
            self.assertIn(229, self.out.map_spawns)
        blocks = sql.split(_MARKER)[1:] if committed else self.out.spawn_blocks
        creature_block = next(b for b in blocks if "UPDATE `creature` " in b)
        guids = {int(g) for g in re.findall(r"\d+", creature_block.split(") AND `guid` IN (")[1])}
        for guid in BOSS_SPAWN_GUIDS:
            self.assertIn(guid, guids)
        for guid in EVENT_CREATURE_GUIDS:  # the Elder Stonefort (game event 7)
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
        self.assertEqual((by_id[1004]["MapID"], by_id[1004]["Difficulty"], by_id[1004]["MaxPlayers"]), (229, 1, 10))
        self.assertEqual({k: v for k, v in by_id.items() if k < 1000}, {r["ID"]: r for r in base})
        self.assertEqual(by_id[24]["MaxPlayers"], 15)  # the stock normal row is not touched (flex clamps 5-10)
        order = [(r["MapID"], r["Difficulty"]) for r in back]
        self.assertEqual(order, sorted(order))
        self.assertEqual(sum(1 for r in back if r["MapID"] == 229 and r["Difficulty"] == 1), 1)

        de_path = state.BASE_DBC_DIR / dbcfmt.DUNGEONENCOUNTER.dbc_filename
        base_de = dbcfile.read_dbc(de_path, dbcfmt.DUNGEONENCOUNTER)
        merged_de = {r["ID"]: r for r in base_de}
        merged_de.update(dungeon_heroic.client_encounter_rows(self.dsl["dungeon_encounters"]))
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / dbcfmt.DUNGEONENCOUNTER.dbc_filename
            path.write_bytes(dbcfile.pack_client_dbc(dbcfmt.DUNGEONENCOUNTER, list(merged_de.values()), base_de))
            back_de = dbcfile.read_dbc(path, dbcfmt.DUNGEONENCOUNTER)
        self.assertEqual(len(back_de), len(base_de) + 14)
        self.assertEqual(sorted(r["ID"] for r in back_de if r["MapID"] == 229 and r["Difficulty"] == 1),
                         list(range(1041, 1055)))

    def _rows(self):
        return {r["ID"]: r for r in self.dsl["lfg_dungeons"]}

    def test_upper_blackrock_spire_is_a_classic_dungeon_entry(self):
        edited = self._rows()[44]
        self.assertEqual(edited["Name_Lang_enUS"], "Upper Blackrock Spire")
        self.assertEqual((edited["TypeID"], edited["Group_Id"], edited["Flags"], edited["Difficulty"]), (1, 1, 3, 0))
        self.assertEqual((edited["MinLevel"], edited["MaxLevel"], edited["MapID"]), (55, 65, 229))
        # the stock row's Target levels, texture and expansion are kept
        stock = next(r for r in dbcfile.read_dbc(state.BASE_DBC_DIR / dbcfmt.LFGDUNGEONS.dbc_filename,
                                                  dbcfmt.LFGDUNGEONS) if r["ID"] == 44)
        self.assertEqual((edited["Target_Level"], edited["Target_Level_Min"], edited["Target_Level_Max"],
                          edited["TextureFilename"], edited["ExpansionLevel"]),
                         (stock["Target_Level"], stock["Target_Level_Min"], stock["Target_Level_Max"],
                          stock["TextureFilename"], stock["ExpansionLevel"]))

    def test_the_heroic_entries(self):
        rows = self._rows()
        for entry, name in ((306, "Lower Blackrock Spire"), (307, "Upper Blackrock Spire")):
            row = rows[entry]
            self.assertEqual(row["Name_Lang_enUS"], name)
            self.assertEqual((row["TypeID"], row["Difficulty"], row["Group_Id"], row["MapID"], row["Flags"]),
                             (5, 1, 12, 229, 3))
            self.assertEqual((row["MinLevel"], row["MaxLevel"]), (60, 62))

    def test_each_heroic_entry_completes_on_its_own_final_boss(self):
        last = {r["creditEntry"]: r["lastEncounterDungeon"] for r in self.dsl["instance_encounters"]}
        self.assertEqual(last[9568], 306)  # Wyrmthalak completes the Lower Spire run
        self.assertEqual(last[10363], 307)  # Drakkisath completes the Upper Spire run
        self.assertEqual({c: v for c, v in last.items() if c not in (9568, 10363)}, {c: 0 for c in last
                                                                                  if c not in (9568, 10363)})

    def test_the_start_points(self):
        positions = {t["dungeonId"]: (t["position_x"], t["position_y"], t["position_z"], t["orientation"])
                     for t in self.dsl["lfg_dungeon_templates"]}
        self.assertEqual(positions[44], (98.25, -300.75, 63.1, 4.94))
        self.assertEqual(positions[307], positions[44])  # the heroic copies its normal entry's start point
        self.assertEqual(positions[306][:3], ENTRANCE)  # the Lower Spire keeps the entrance
        # the Upper Spire start is outside the Dragonspire Hall trigger (areatrigger 2046) with the client's delta
        # (IsInAreaTriggerRadius: the player's 3D distance to the trigger centre against its radius), so the group
        # does not start the stock rune-room check by arriving; the hall's own self-start covers entering it
        x, y, z = positions[44][:3]
        tx, ty, tz, radius = DRAGONSPIRE_TRIGGER
        self.assertGreater(math.dist((x, y, z), (tx, ty, tz)), radius + 5)

    def test_the_stock_row_is_replaced_in_the_client_file(self):
        base = dbcfile.read_dbc(state.BASE_DBC_DIR / dbcfmt.LFGDUNGEONS.dbc_filename, dbcfmt.LFGDUNGEONS)
        merged = {r["ID"]: r for r in base}
        merged.update(lfg_dungeons.client_dungeon_rows(self.dsl["lfg_dungeons"]))
        self.assertEqual(len(merged), len(base) + 3)  # 300 random, 306 and 307; row 44 replaces the stock one
        self.assertEqual((merged[44]["TypeID"], merged[44]["Group_Id"], merged[44]["Flags"]), (1, 1, 3))

    def test_the_random_classic_normal_pool_gains_the_upper_spire(self):
        # Random Classic Dungeon (258) draws from Group 1 / TypeID 1: both Spire entries are in it now
        stock = {r["ID"]: r for r in dbcfile.read_dbc(state.BASE_DBC_DIR / dbcfmt.LFGDUNGEONS.dbc_filename,
                                                      dbcfmt.LFGDUNGEONS)}
        pool = {i for i, r in {**stock, **self._rows()}.items() if r["Group_Id"] == 1 and r["TypeID"] == 1}
        self.assertTrue({32, 44} <= pool)
        self.assertNotIn(44, {i for i, r in stock.items() if r["Group_Id"] == 1 and r["TypeID"] == 1})



if __name__ == "__main__":
    unittest.main()
