"""
Blackrock Depths' heroic declaration (Blackrock Depths build, WP-H): source/world/dungeons/blackrock_depths.py as
generate.py loads it, and the four Finder sections of source/world/lfg_classic_sections.py (the normal side) and
source/world/lfg_classic_heroic.py (310-313) for map 230.

Covered: the heroic() arguments (MapDifficulty 1005 with MaxPlayers 5, dungeon_access 127, DungeonEncounter 1055-1073,
`no_credit=(234, 240, 241)`, spawn masks, no event spawns), the roles / extra / skip declarations, the heroic overrides
against the build spec's numbers (handoff 3.6) and the predicted heroic loot ids, the wave switch (BIND_WAVE_2: the
bosses of sections 3 and 4 keep their stock heroic copy until wave 2 binds them), the kit adds' overrides following the
creature_template() declarations of source/npcs/blackrock_depths/, and the expansion against the live replay: no ERROR
or WARNING, the nineteen encounters in the stock file's order (OrderIndex) with kill credit on sixteen of them
(Fineous, Ribbly and Plugger keep their DungeonEncounter row but get no credit row, and still role `boss`), the creature
set and the predicted heroic_ids.lock lines (310301 on, normal-entry order), the bosses' INSTANCE_BIND and immunity sets
(1972; 1973 for Incendius and Bael'Gar), the SmartAI widening, the game-event spawns staying normal-only, the client
MapDifficulty.dbc / DungeonEncounter.dbc rows (the patch-Z merge) beside the stock rows, and the Finder: the two new
normal sections (308, 309), the moved starts, the final-boss links (normal and heroic) and the four heroic entries
(310-313).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_heroic.py
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

_MARKER = "-- Blackrock Depths (map 230) heroic:"
_PENDING = TOOL_ROOT.parents[1] / "data" / "sql" / "updates" / "pending_db_world"


def _rendered_or_committed(blocks: list[str]) -> tuple[str, bool]:
    """The rendered blocks, or (after the write run made them live) the committed rev that carries them."""
    sql = "\n".join(blocks)
    if _MARKER in sql:
        return sql, False
    texts = [f.read_text() for f in sorted(_PENDING.glob("rev_*.sql"))]
    return "\n".join(t for t in texts if _MARKER in t), True


BRD_FILE = TOOL_ROOT / "source" / "world" / "dungeons" / "blackrock_depths.py"
LFG_HEROIC_FILE = TOOL_ROOT / "source" / "world" / "lfg_classic_heroic.py"
LFG_SECTIONS_FILE = TOOL_ROOT / "source" / "world" / "lfg_classic_sections.py"
KIT_DIR = TOOL_ROOT / "source" / "npcs" / "blackrock_depths"
CREDIT_DROP_SQL = _PENDING / "rev_credit_drops_blackrock_depths.sql"
CHECKPOINT_SQL = (TOOL_ROOT.parents[1] / "modules" / "mod-dungeon-checkpoint" / "data" / "sql" / "db-world"
                  / "u_dungeon_checkpoint_2026_11_17_00.sql")
IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")

# The nineteen normal encounters in the stock file's order (OrderIndex 0 ... 18000: the same as the id order here),
# paired with the heroic ids 1055-1073; the boss each credits; the three that lose their credit.
STOCK_ORDER = tuple(range(227, 246))
NORMAL_CREDIT = {
    227: 9018, 228: 9025, 229: 9319, 230: 10096, 231: 9024, 232: 9017, 233: 9041, 234: 9056, 235: 9016, 236: 9033,
    237: 8983, 238: 9537, 239: 9502, 240: 9543, 241: 9499, 242: 9156, 243: 9035, 244: 9938, 245: 9019,
}
NO_CREDIT = (234, 240, 241)
HEROIC_ENCOUNTERS = {hid: NORMAL_CREDIT[nid] for hid, nid in zip(range(1055, 1074), STOCK_ORDER)
                     if nid not in NO_CREDIT}
# 233 (Stilgiss and Verek) credits on the spell the instance casts when both die (rev_credit_drops...sql): the heroic
# copy (1061) follows the replayed normal row. creditType 1 = ENCOUNTER_CREDIT_CAST_SPELL.
SPELL_CREDITS = {1061: 211066}
HEROIC_ENCOUNTERS.update(SPELL_CREDITS)
ENCOUNTER_NAMES = [
    "High Interrogator Gerstahn", "Lord Roccor", "Houndmaster Grebmar", "Ring of Law", "Pyromancer Loregrain",
    "Lord Incendius", "Warder Stilgiss", "Fineous Darkvire", "Bael'Gar", "General Angerforge",
    "Golem Lord Argelmach", "Hurley Blackbreath", "Phalanx", "Ribbly Screwspigot", "Plugger Spazzring",
    "Ambassador Flamelash", "The Seven", "Magmus", "Emperor Dagran Thaurissan",
]
ENCOUNTER_BITS = list(range(19))
SECTION_END = {1058: 310, 1063: 311, 1065: 312, 1073: 313}  # heroic encounter -> heroic Finder entry

# Heroic health at 5 players from the build spec (handoff 3.6) and the wave each unit binds in. Wave 1 is sections 1 and
# 2 (always bound), wave 2 is sections 3 and 4 (behind BIND_WAVE_2).
WAVE_1_HEALTH = {
    9018: 230_000, 9025: 190_000, 9319: 150_000, 9024: 220_000, 9041: 180_000, 9042: 85_000, 9476: 170_000,
    9056: 80_000, 9017: 160_000, 9016: 320_000,
    9027: 150_000, 9028: 150_000, 9029: 150_000, 9030: 150_000, 9031: 150_000, 9032: 150_000,  # the six champions
    8925: 28_000, 8926: 28_000, 8927: 28_000, 8933: 28_000, 8928: 42_000, 8932: 14_000,  # the Ring's wave mobs
    16059: 160_000, 16053: 80_000, 16049: 100_000, 16058: 100_000, 16052: 100_000,  # the Encore
}
WAVE_2_HEALTH = {
    9033: 210_000, 8983: 220_000, 9537: 200_000, 9541: 12_000, 9543: 60_000, 10043: 9_000, 9502: 230_000,
    9499: 60_000, 9156: 210_000, 9178: 4_500, 9034: 450_000, 9035: 450_000, 9036: 450_000, 9037: 450_000,
    9038: 450_000, 9039: 450_000, 9040: 450_000, 9938: 240_000, 9019: 220_000, 8929: 70_000, 10076: 70_000,
}
BOSS_HEALTH = {**WAVE_1_HEALTH, **WAVE_2_HEALTH}
FIRE_IMMUNE = (9017, 9016)  # Incendius and Bael'Gar: 1972 + Fire (1973)
# The units whose override has no `columns` (a plain health override: not a `_boss`)
PLAIN_HEALTH = {8925, 8926, 8927, 8928, 8932, 8933, 9541, 10043}
# Boss-less units whose override carries a column but no `_boss` set (the Burning Spirit: no immunities; the Encore's
# other four: boss role by `extra=`, no credit, so no INSTANCE_BIND, R-2-FW MIN-2)
ENCORE_FOUR = (16053, 16049, 16058, 16052)
PLAIN_WITH_COLUMNS = {9178: {"CreatureImmunitiesId": 0}, **{entry: {"flags_extra": 0} for entry in ENCORE_FOUR}}
# Columns an override states beyond the immunity set and the lootid (blackrock_depths.py). INSTANCE_BIND (flags_extra 1)
# rides only on the units that carry an encounter credit (handoff section 10, the orchestrator rulings of
# 2026-11-17): Ribbly, Plugger, Moira, the High Priestess, the Seven's six non-credit ghosts, Verek, Fineous,
# Doomgrip, the six Ring champions, Theldren and the Encore's other four state flags_extra 0.
EXTRA_COLUMNS = {
    9025: {"speed_walk": 0.6},  # Roccor's Restless March, kept alike on the heroic row (STAGE-D2)
    9543: {"CreatureImmunitiesId": -251, "flags_extra": 0},  # Ribbly keeps his stock set
    9499: {"flags_extra": 0},
    9502: {"faction": 35, "npcflag": 1, "gossip_menu_id": 2283},  # Phalanx starts friendly (STAGE-D19, DC-2)
    9034: {"flags_extra": 0}, 9036: {"flags_extra": 0}, 9037: {"flags_extra": 0}, 9038: {"flags_extra": 0},
    9039: {"flags_extra": 0}, 9040: {"flags_extra": 0}, 8929: {"flags_extra": 0}, 10076: {"flags_extra": 0},
    **{entry: {"flags_extra": 0} for entry in (9042, 9056, 9476, 9027, 9028, 9029, 9030, 9031, 9032, 16059)},
}
NO_BIND = {9543, 9499, 8929, 10076, 9034, 9036, 9037, 9038, 9039, 9040,
           9042, 9056, 9476, 9027, 9028, 9029, 9030, 9031, 9032, 16059, *ENCORE_FOUR}
# R-2-B MJ-1 (orchestrator default 2026-11-17): all seven ghosts of the Seven swing at the boss melee tier on heroic
THE_SEVEN = (9034, 9035, 9036, 9037, 9038, 9039, 9040)
# Kit adds whose heroic melee is stated (the spec's 8% of the reference row, not the elite tier's)
KIT_MELEE = {300780: 330}
# The predicted heroic ids: the lock mints in normal-entry order from 310301, the boss lootids are the same numbers.
HEROIC_LOOTID = {
    9016: 310341, 9017: 310342, 9018: 310343, 9019: 310344, 9024: 310345, 9025: 310346, 9027: 310347, 9028: 310348,
    9029: 310349, 9030: 310350, 9031: 310351, 9032: 310352, 9033: 310353, 8983: 310340, 9041: 310361, 9056: 310363,
    9156: 310364, 9319: 310366, 9476: 310375, 9499: 310376, 9502: 310377, 9537: 310378, 9543: 310380, 9938: 310382,
    16059: 310390,
}
NO_OWN_LOOT = (9042, 9034, 9035, 9036, 9037, 9038, 9039, 9040, 8929, 10076)  # Verek, the Seven, Moira, the Priestess
BOSS_WAVE = {entry: "1" for entry in WAVE_1_HEALTH if entry not in PLAIN_HEALTH}
BOSS_WAVE.update({entry: "2" for entry in WAVE_2_HEALTH if entry not in PLAIN_HEALTH})
PLAIN_WAVE = {entry: "1" for entry in WAVE_1_HEALTH if entry in PLAIN_HEALTH}
PLAIN_WAVE.update({entry: "2" for entry in WAVE_2_HEALTH if entry in PLAIN_HEALTH})
KIT_HEALTH = {  # new kit adds (handoff 3.3 ids): heroic health; None = the tier's template (Korv's totems)
    300780: 12_000, 300781: 9_000, **{e: 10_000 for e in range(300782, 300788)}, 300788: 40_000,
    300789: None, 300790: None, 300791: None, 300792: 7_000, 300793: 28_000, 300794: 9_000, 300795: 6_000,
    300830: 15_000, 300831: 4_500, 300832: 7_500, 300833: 37_000, 300834: 37_000, 300835: 37_000, 300836: 100_000,
    300839: 9_000, 300841: 8_000, 300842: 12_000, 300843: 12_000, 300844: 10_000,
}
# minted after the extraction set, in entry order, wave by wave (the mint-order note in blackrock_depths.py)
KIT_HEROIC_ID = {entry: 310391 + i for i, entry in enumerate(sorted(KIT_HEALTH))}
EXTRA_SUMMONS = (8925, 8926, 8927, 8928, 8932, 8933, 9027, 9028, 9029, 9030, 9031, 9032, 9178, 9476, 10076, 16049,
                 16052, 16053, 16058, 16059)  # the stock summon-only units the extraction cannot see
SKIPPED = (8923, 9022, 9677, 9679, 9680, 9681, 10116, 10117, 23619, 23623, 23624, 23625, 23626)
ROLE_CORRECTIONS = {8929: "trash", 9034: "trash", 9036: "trash", 9037: "trash", 9038: "trash", 9039: "trash",
                    9040: "trash", 9042: "boss", 10043: "trash"}
HEROIC_ENTRY_COUNT = 90  # the extraction set plus the summon-only extras, before any kit add lands
FIRST_HEROIC_ID = 310301
# Not heroic: friendly NPCs (the patrons, the Seven's gossip units besides the corrected ones, Moira's quest givers),
# the Brewfest and Encore triggers, and the units that live on their normal entry
NOT_HEROIC = (8923, 9020, 9021, 9023, 9500, 9503, 9545, 9547, 9554, 9956, 12944, 23872, 28067, 28209, 28210, 16079,
              23830, 28206, 23850)
# The SmartAI rows still widened to heroic after the boss revs: the units whose rows the S0 / D4 / D13 / D18 / D21 revs
# drop (Bael'Gar 9016, Incendius 9017, Loregrain 9024, Roccor 9025, the Seven 9034, Stilgiss 9041, Fineous 9056, the
# Ring and Guzzler units) are gone from the UPDATE: it matches nothing once the row is deleted.
SMART_WIDENED = (8901, 8911, 8921, 9437, 9438, 9439, 9441, 9442, 9443, 9445)
SMART_DROPPED = (9016, 9017, 9024, 9025, 9034, 9041, 9056)
# Boss spawns (all spawnMask 1 live, so they all get the heroic bit) and the two game event spawns
BOSS_SPAWN_GUIDS = (45931, 45885, 47733, 47250, 47613, 47771, 47304, 45954, 47774, 47775, 47631, 47778, 46284, 47703,
                    46615, 46619, 47477, 72000, 91025)
EVENT_CREATURE_GUIDS = (78375, 240000)  # Elder Morndeep and Coren Direbrew
STILGISS_VEREK_CREDIT = 211066  # the credit spell the instance fires when both die (stilgiss_verek.py)
ENTRANCE = (458.32, 26.52, -70.67)  # LFGDungeons 30 / 276: areatrigger_teleport 1466
START_S2 = (595.0, -92.0, -45.0, 1.89)
START_S3 = (607.2, -47.8, -59.8, 6.05)
START_S4 = (843.8, -167.8, -49.7, 4.64)
RING_TRIGGER = (595.29, -186.56, -54.0)  # the Ring of Law's centre; areatrigger 1526 is the arena
LEVER = (615.6, -49.8, -60.1)  # the Shadowforge Lock lever 161460


def _bound_waves() -> set[str]:
    path = KIT_DIR / "_common.py"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    return {"1"} | {w for w, v in re.findall(r"^BIND_WAVE_(2)\s*=\s*(True|False)\s*$", text, re.M) if v == "True"}


def _own_heroic_loot() -> bool:
    """blackrock_depths.py's `_HEROIC_BOSS_OWN_LOOT` (off until L-1 / L-2 declare the heroic loot groups: the
    Scholomance R-A S-2 rule, a lootid with no loot_template rows behind it drops nothing)."""
    m = re.search(r"^_HEROIC_BOSS_OWN_LOOT\s*=\s*(True|False)\s*$", BRD_FILE.read_text(encoding="utf-8"), re.M)
    return bool(m) and m.group(1) == "True"


BOUND = _bound_waves()
OWN_LOOT = _own_heroic_loot()
BOUND_BOSSES = {b for b, w in BOSS_WAVE.items() if w in BOUND}
BOUND_PLAIN = {b for b, w in PLAIN_WAVE.items() if w in BOUND}


def _kit_declared() -> set[int]:
    pattern = re.compile(r"\b(?:creature_template|_golem)\(\s*(\d+)\s*,")  # _golem: argelmach.py's helper
    return {int(m) for path in KIT_DIR.glob("*.py") for m in pattern.findall(path.read_text(encoding="utf-8"))}


def _brd_entry() -> tuple[dict, object]:
    reg = registry.load_class_package(TOOL_ROOT / "source" / "world" / "dungeons", ids_cfg=IDS)
    return {e["map_id"]: e for e in reg.dungeons}[230], reg


class DeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entry, cls.reg = _brd_entry()
        cls.heroic = cls.entry["heroic"]

    def test_the_ids_are_the_next_of_their_blocks_after_blackrock_spire(self):
        self.assertEqual((self.heroic["map_difficulty_id"], self.heroic["access_id"]), (1005, 127))
        self.assertEqual(self.heroic["encounter_ids"], tuple(range(1055, 1074)))
        self.assertEqual(self.heroic["min_level"], 60)

    def test_the_heroic_row_is_a_five_player_row(self):
        self.assertEqual(self.heroic["max_players"], 5)
        md = {r["ID"]: r for r in self.reg.map_difficulties}[1005]
        self.assertEqual((md["MapID"], md["Difficulty"], md["RaidDuration"], md["MaxPlayers"]), (230, 1, 86400, 5))
        self.assertEqual(md["Message_Lang_enUS"], "Heroic Difficulty requires you to be level 60.")
        self.assertEqual(md["Difficultystring"], "DUNGEON_DIFFICULTY_5PLAYER_HEROIC")
        access = {r["id"]: r for r in self.reg.dungeon_access}[127]
        self.assertEqual((access["map_id"], access["difficulty"], access["min_level"]), (230, 1, 60))

    def test_three_encounters_lose_their_credit(self):
        self.assertEqual(self.heroic["no_credit"], NO_CREDIT)

    def test_spawns_go_to_heroic_but_the_event_spawns_stay_normal_only(self):
        self.assertTrue(self.heroic["spawn_mask"])
        self.assertFalse(self.heroic["event_spawns"])

    def test_roles_extras_and_skips(self):
        by_entry = {c["entry"]: c for c in self.entry["creatures"]}
        for entry, role in ROLE_CORRECTIONS.items():
            self.assertEqual(by_entry[entry]["role"], role, entry)
        for extra in EXTRA_SUMMONS:
            self.assertTrue(by_entry[extra]["summoned_by"], extra)  # a C++ summon: no spawns, free text names who
            self.assertEqual(by_entry[extra]["spawns"], 0, extra)
        for extra in KIT_HEALTH:
            self.assertEqual(by_entry[extra]["role"], "trash", extra)
            self.assertEqual(by_entry[extra]["source"], "extra", extra)
        self.assertEqual(self.entry["skip"], SKIPPED)
        # Fineous, Ribbly and Plugger keep role boss after their normal credit is deleted (FD note): the role comes
        # from the declaration, not from the encounter credits
        for entry in (9056, 9543, 9499):
            self.assertEqual(by_entry[entry]["role"], "boss", entry)

    def test_boss_overrides_are_the_build_specs_health_the_immunity_set_and_the_loot_flag(self):
        overrides = {entry: dict(pairs) for entry, pairs in self.heroic["overrides"]}
        for entry, health in BOSS_HEALTH.items():
            with self.subTest(entry=entry):
                wave = BOSS_WAVE.get(entry) or PLAIN_WAVE[entry]
                if wave not in BOUND:
                    self.assertNotIn(entry, overrides)  # a section 3 or 4 unit: stock until wave 2 binds it
                    continue
                self.assertEqual(overrides[entry]["health"], health)
                if entry in PLAIN_HEALTH:
                    self.assertNotIn("columns", overrides[entry])
                    continue
                if entry in PLAIN_WITH_COLUMNS:
                    self.assertEqual(dict(overrides[entry]["columns"]), PLAIN_WITH_COLUMNS[entry])
                    continue
                expected = {"CreatureImmunitiesId": 1973 if entry in FIRE_IMMUNE else 1972}
                if OWN_LOOT and entry not in NO_OWN_LOOT:
                    expected["lootid"] = HEROIC_LOOTID[entry]
                expected.update(EXTRA_COLUMNS.get(entry, {}))
                self.assertEqual(dict(overrides[entry]["columns"]), expected)

    def test_the_wave_one_bosses_are_the_first_two_sections(self):
        # sections 1 and 2: Gerstahn ... Bael'Gar; sections 3 and 4: Angerforge ... the Emperor, plus the Guzzler room
        wave_1 = {9018, 9025, 9319, 9024, 9041, 9042, 9056, 9017, 9016, 9476, 9027, 9031, 16059}
        wave_2 = {9033, 8983, 9537, 9543, 9502, 9499, 9156, 9034, 9035, 9938, 9019, 8929, 10076}
        self.assertLessEqual(wave_1, {e for e, w in {**BOSS_WAVE, **PLAIN_WAVE}.items() if w == "1"})
        self.assertLessEqual(wave_2, {e for e, w in {**BOSS_WAVE, **PLAIN_WAVE}.items() if w == "2"})

    def test_wave_1_is_bound_and_the_wave_switch_is_read_from_the_npc_package(self):
        self.assertIn("1", BOUND)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "world" / "dungeons").mkdir(parents=True)
            (root / "npcs" / "blackrock_depths").mkdir(parents=True)
            (root / "world" / "dungeons" / "blackrock_depths.py").write_text(BRD_FILE.read_text(encoding="utf-8"))
            for value, bound in (("False", False), ("True", True)):
                (root / "npcs" / "blackrock_depths" / "_common.py").write_text(f"BIND_WAVE_2 = {value}\n")
                reg = registry.load_class_package(root / "world" / "dungeons", ids_cfg=IDS)
                overrides = {e: dict(p) for e, p in {x["map_id"]: x for x in reg.dungeons}[230]["heroic"]["overrides"]}
                for entry in WAVE_2_HEALTH:
                    self.assertEqual(entry in overrides, bound, (value, entry))
                for entry in WAVE_1_HEALTH:  # wave 1: always
                    self.assertIn(entry, overrides, (value, entry))

    def test_a_missing_common_file_reads_as_wave_2_off(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "world" / "dungeons").mkdir(parents=True)
            (root / "world" / "dungeons" / "blackrock_depths.py").write_text(BRD_FILE.read_text(encoding="utf-8"))
            reg = registry.load_class_package(root / "world" / "dungeons", ids_cfg=IDS)
        overrides = {e: dict(p) for e, p in {x["map_id"]: x for x in reg.dungeons}[230]["heroic"]["overrides"]}
        self.assertEqual(sorted(overrides), sorted(WAVE_1_HEALTH))

    def test_kit_add_overrides_follow_the_declared_templates(self):
        overrides = {entry: dict(pairs) for entry, pairs in self.heroic["overrides"]}
        declared = _kit_declared()
        # applied to every declared template regardless of the wave switch (like Stratholme's `_KIT_ADD_HEROIC`): the
        # wave only gates the stock-id and boss overrides; Korv's totems have no designer health, so no override
        expected = {e: h for e, h in KIT_HEALTH.items() if e in declared and h is not None}
        self.assertEqual({e: o["health"] for e, o in overrides.items() if e >= 300000}, expected)
        for entry, melee in KIT_MELEE.items():
            if entry in overrides:
                self.assertEqual(overrides[entry].get("melee"), melee, entry)

    def test_kit_add_overrides_appear_when_a_source_file_declares_the_template(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "world" / "dungeons").mkdir(parents=True)
            (root / "npcs" / "blackrock_depths").mkdir(parents=True)
            (root / "world" / "dungeons" / "blackrock_depths.py").write_text(BRD_FILE.read_text(encoding="utf-8"))
            (root / "npcs" / "blackrock_depths" / "boss.py").write_text(
                "earth = creature_template(\n    300780, 'Loosed Earth', **{})\n"
                "stalker = creature_template(300796, 'Generic Stalker')\n"
            )
            reg = registry.load_class_package(root / "world" / "dungeons", ids_cfg=IDS)
        overrides = {entry: dict(pairs) for entry, pairs in {e["map_id"]: e for e in reg.dungeons}[230]["heroic"][
            "overrides"]}
        self.assertEqual(sorted(e for e in overrides if e >= 300000), [300780])  # the stalker gets no heroic template
        self.assertEqual(overrides[300780]["health"], 12_000)

    def test_every_override_names_a_listed_creature(self):
        listed = {c["entry"] for c in self.entry["creatures"]}
        for entry, _pairs in self.heroic["overrides"]:
            self.assertIn(entry, listed)

    def test_the_mint_order_puts_every_wave_1_add_below_every_wave_2_add(self):
        wave_1 = [e for e in KIT_HEALTH if e < 300800]
        wave_2 = [e for e in KIT_HEALTH if e >= 300800]
        self.assertLess(max(wave_1), min(wave_2))
        self.assertEqual(sorted(KIT_HEROIC_ID.values()),
                         list(range(FIRST_HEROIC_ID + HEROIC_ENTRY_COUNT, FIRST_HEROIC_ID + HEROIC_ENTRY_COUNT
                                    + len(KIT_HEROIC_ID))))
        self.assertEqual(sorted(KIT_HEROIC_ID), sorted(KIT_HEROIC_ID, key=KIT_HEROIC_ID.get))


class HandSqlTest(unittest.TestCase):
    """The hand SQL of this WP: the normal credit drops and the three checkpoint rows."""

    def test_the_credit_drop_deletes_exactly_the_three_rows(self):
        text = CREDIT_DROP_SQL.read_text()
        statements = [line for line in text.splitlines() if not line.startswith("--")]
        sql = " ".join(statements)
        self.assertEqual(re.findall(r"DELETE FROM `(\w+)`", sql), ["instance_encounters"])
        delete = sql.split("UPDATE")[0]
        self.assertEqual(sorted(int(n) for n in re.findall(r"\d+", delete.split("`entry` IN (")[1].split(")")[0])),
                         list(NO_CREDIT))
        self.assertEqual(
            sorted(int(n) for n in re.findall(r"\d+", delete.split("`creditEntry` IN (")[1].split(")")[0])),
            [9056, 9499, 9543])
        self.assertNotIn("INSERT", sql)
        self.assertEqual(sql.count("UPDATE"), 1)  # the Stilgiss and Verek spell credit (below)

    def test_row_233_credits_on_the_spell_the_instance_casts_when_both_die(self):
        sql = " ".join(line for line in CREDIT_DROP_SQL.read_text().splitlines() if not line.startswith("--"))
        update = re.search(r"UPDATE `instance_encounters` SET `creditType` = (\d+), `creditEntry` = (\d+)\s+"
                           r"WHERE `entry` = 233 AND `creditType` = 0 AND `creditEntry` = 9041;", sql)
        self.assertIsNotNone(update)
        self.assertEqual(int(update.group(1)), 1)  # ENCOUNTER_CREDIT_CAST_SPELL
        spell_id = int(update.group(2))
        self.assertEqual(spell_id, STILGISS_VEREK_CREDIT)
        # declared in DT (stilgiss_verek.py, D8's slice 211050-211089) and named by the instance header
        source_text = (KIT_DIR / "stilgiss_verek.py").read_text(encoding="utf-8")
        self.assertIn(f"id={spell_id}, name='Warder Stilgiss and Verek'", source_text)
        header = (TOOL_ROOT.parents[1] / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockDepths"
                  / "BlackrockDepthsRework.h").read_text(encoding="utf-8")
        self.assertRegex(header, rf"kSpellStilgissVerekCredit\s*=\s*{spell_id}")

    def test_the_credit_drop_sorts_after_a_generated_rev(self):
        self.assertGreater(CREDIT_DROP_SQL.name, "rev_1794817526058459648.sql")

    def test_the_checkpoint_rows_equal_the_finder_starts(self):
        text = CHECKPOINT_SQL.read_text()
        rows = re.findall(r"^\((230), (\d+), (\d+), (\d+), ([-\d.]+), ([-\d.]+), ([-\d.]+), ([-\d.]+),\s+'", text, re.M)
        self.assertEqual([(int(r[1]), int(r[2]), int(r[3])) for r in rows], [(0, 1, 0), (0, 2, 0), (0, 3, 0)])
        self.assertEqual([tuple(float(v) for v in r[4:8]) for r in rows], [START_S2, START_S3, START_S4])
        self.assertIn("`location_index` IN (1, 2, 3)", text)

    def test_the_finder_starts_are_clear_of_the_arena_trigger_and_near_their_landmarks(self):
        # S2a is outside the Ring's arena (the BRS K-m3 lesson: arriving must not start the event), S3 faces the lever
        self.assertGreater(math.dist(START_S2[:3], RING_TRIGGER), 60)
        self.assertLess(math.dist(START_S3[:3], LEVER), 9)
        bearing = math.atan2(LEVER[1] - START_S3[1], LEVER[0] - START_S3[0]) % (2 * math.pi)
        self.assertAlmostEqual(START_S3[3], bearing, delta=0.25)


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
            # The Blackrock Depths boss package declares its kit adds (source/npcs/blackrock_depths/) as they land
            if KIT_DIR.is_dir():
                kit = registry.load_class_package(
                    KIT_DIR, ids_cfg=IDS, existing_creature_rows=existing,
                    creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
                    creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS, live_data={},
                )
                for key in ("creature_templates", "creature_template_models", "creature_template_edits"):
                    cls.dsl[key] = cls.dsl.get(key, []) + list(getattr(kit, key))
            # only Blackrock Depths' heroic is expanded here (the other dungeons have their own tests)
            cls.dsl["dungeons"] = [e if e["map_id"] == 230 else dict(e, heroic=None) for e in cls.dsl["dungeons"]]
            cls.index = spell_tables.load_spell_table_index()
            cls.out = dungeon_heroic.expand(
                cls.dsl, lambda: dungeon_heroic.load_live_world(existing, cls.index), ids_cfg=IDS,
            )
            cls.existing = existing
            # generate.py's next step: the finder (source/world/lfg_classic_*.py) with only this map's entries
            heroic = registry.load_class_file(LFG_HEROIC_FILE, ids_cfg=IDS)
            sections = registry.load_class_file(LFG_SECTIONS_FILE, ids_cfg=IDS)
            cls.dsl["lfg_group_declarations"] = list(heroic.lfg_group_declarations)
            cls.dsl["lfg_dungeon_declarations"] = [
                d for d in (*heroic.lfg_dungeon_declarations, *sections.lfg_dungeon_declarations)
                if d["kind"] in ("random", "dungeon") or d["id"] in (30, 276) or d.get("normal") in (30, 308, 309, 276)
            ]
            cls.lfg_out = lfg_dungeons.expand(cls.dsl, lambda: lfg_dungeons.load_inputs(cls.index))
        finally:
            sqlcorpus.deactivate()
        cls.entry = next(e for e in cls.dsl["dungeons"] if e["map_id"] == 230)
        cls.reports = {r.normal: r for r in cls.out.heroic_reports}

    def test_it_is_clean(self):
        self.assertEqual((self.out.errors, self.out.warnings), ([], []))
        self.assertEqual((self.lfg_out.errors, self.lfg_out.warnings), ([], []))

    def test_nineteen_encounters_in_the_stock_order_and_sixteen_credits(self):
        rows = sorted(self.dsl["dungeon_encounters"], key=lambda r: r["ID"])
        self.assertEqual([r["ID"] for r in rows], list(range(1055, 1074)))  # 19 rows: the client's lockout list
        for row in rows:
            self.assertEqual((row["MapID"], row["Difficulty"]), (230, 1))
        self.assertEqual([r["Name_Lang_enUS"] for r in rows], ENCOUNTER_NAMES)
        self.assertEqual([r["Bit"] for r in rows], ENCOUNTER_BITS)
        credits = {r["entry"]: r["creditEntry"] for r in self.dsl["instance_encounters"] if r["entry"] >= 1000}
        self.assertEqual(credits, HEROIC_ENCOUNTERS)
        for row in self.dsl["instance_encounters"]:
            if row["entry"] >= 1000:
                want = 1 if row["entry"] in SPELL_CREDITS else 0
                self.assertEqual(int(row["creditType"]), want, row["entry"])
        self.assertEqual(len(credits), 16)  # 16 rows: no 1062 (Fineous), 1068 (Ribbly), 1069 (Plugger)
        for dropped in (1062, 1068, 1069):
            self.assertNotIn(dropped, credits)

    def test_the_three_dropped_credits_keep_role_boss_and_a_bound_heroic_template(self):
        rows = {int(r["entry"]): r for r in self.dsl["creature_templates"] if r.get(dungeon_heroic.DERIVED)}
        heroic_entry = self.entry["heroic_entries"]
        for boss in (9056, 9543, 9499):
            with self.subTest(boss=boss):
                self.assertEqual(self.reports[boss].role, "boss")
                # INSTANCE_BIND: none of the three carries a credit; each states flags_extra 0 once its wave binds
                # it (until then the stock heroic copy is a plain boss-role row)
                bound_no_bind = boss in NO_BIND and (boss == 9056 or "2" in BOUND)
                self.assertEqual(int(rows[heroic_entry[boss]]["flags_extra"]) & 1, 0 if bound_no_bind else 1)

    def test_the_creature_set(self):
        mapping = self.entry["heroic_entries"]
        for boss in (9018, 9025, 9319, 9024, 9017, 9041, 9042, 9056, 9016, 9033, 8983, 9537, 9502, 9543, 9499, 9156,
                     9035, 9938, 9019, 10096, *EXTRA_SUMMONS):
            self.assertIn(boss, mapping)
        for hostile in (8889, 8901, 8905, 8908, 8911, 8982, 9436, 9445, 9541, 9637, 10043, 8929):
            self.assertIn(hostile, mapping)
        for out in NOT_HEROIC + SKIPPED:
            self.assertNotIn(out, mapping)
        declared = {int(r["entry"]) for r in self.dsl["creature_templates"] if not r.get(dungeon_heroic.DERIVED)}
        for kit in KIT_HEALTH:
            self.assertEqual(kit in mapping, kit in declared, kit)
        # D12's Hand of Incendius (300828, summoned on the heroic hard mode only) has no heroic template by design,
        # like the generic stalkers: declared, but in neither the creature list nor the mint order
        self.assertIn(300828, declared)
        self.assertNotIn(300828, mapping)
        self.assertNotIn(300828, KIT_HEROIC_ID)
        block = IDS["creature_heroic"]
        locked = heroic_templates.parse_lock(heroic_templates.LOCK_PATH.read_text()).pairs
        for normal, heroic in mapping.items():
            self.assertTrue(block["start"] <= heroic <= block["end"], (normal, heroic))
        self.assertEqual(len(set(mapping.values())), len(mapping))
        self.assertFalse(set(mapping.values()) & {h for n, h in locked.items() if n not in mapping})

    def test_the_predicted_lock_lines(self):
        """The ids the first write run mints (the boss lootids are the same numbers): normal-entry order from 310301,
        90 lines for the entries that exist today (the extraction set plus the summon-only extras). The kit adds come
        after, wave by wave in entry order (310391 on, KIT_HEROIC_ID), and each add's creature_template must name its
        id in difficulty_entry_1."""
        mapping = self.entry["heroic_entries"]
        locked = heroic_templates.parse_lock(heroic_templates.LOCK_PATH.read_text()).pairs
        fresh = {n: h for n, h in mapping.items() if n not in locked}
        if set(fresh) != set(mapping):  # after the write run the lines are committed: the same numbers
            fresh = mapping
        existing = {n: h for n, h in fresh.items() if n < 300000}
        self.assertEqual(sorted(existing.values()), list(range(FIRST_HEROIC_ID, FIRST_HEROIC_ID + len(existing))))
        self.assertEqual(sorted(existing), sorted(existing, key=lambda n: existing[n]))  # ids follow the entry order
        for boss, heroic in HEROIC_LOOTID.items():
            self.assertEqual(existing[boss], heroic, boss)
        self.assertEqual(len(existing), HEROIC_ENTRY_COUNT)
        # every wave 1 and wave 2 add is declared now (all 24 encounter WPs built): none is left unpinned, and the
        # first write run mints exactly 310391-310418 in this order
        self.assertEqual(sorted(set(KIT_HEROIC_ID) - set(fresh)), [], "a kit add is not declared yet")
        for kit, heroic in KIT_HEROIC_ID.items():
            self.assertEqual(fresh[kit], heroic, kit)
        self.assertEqual(sorted(KIT_HEROIC_ID.values()), list(range(310391, 310419)))

    def test_bosses(self):
        rows = {int(r["entry"]): r for r in self.dsl["creature_templates"] if r.get(dungeon_heroic.DERIVED)}
        heroic_entry = self.entry["heroic_entries"]
        for boss, health in BOSS_HEALTH.items():
            with self.subTest(boss=boss):
                report = self.reports[boss]
                row = rows[heroic_entry[boss]]
                self.assertEqual((row["minlevel"], row["maxlevel"], row["exp"]), (60, 60, 0))
                if boss in PLAIN_HEALTH or boss in PLAIN_WITH_COLUMNS:
                    if boss in BOUND_PLAIN or boss in BOUND_BOSSES:
                        self.assertEqual(report.solved.health, health)
                    continue
                if boss in (9034, 9036, 9037, 9038, 9039, 9040, 8929, 10076):
                    self.assertEqual(int(row["flags_extra"]) & 1, 0)  # fighting trash by role: no INSTANCE_BIND
                elif boss in NO_BIND:  # boss role, no credit: no bind once their wave binds them
                    self.assertEqual(int(row["flags_extra"]) & 1, 0 if boss in BOUND_BOSSES else 1)
                else:
                    self.assertEqual(report.role, "boss")
                    self.assertEqual(int(row["flags_extra"]) & 1, 1)  # INSTANCE_BIND
                if boss == 9502:  # Phalanx starts friendly and dormant: the copy keeps faction, npcflag and gossip
                    self.assertEqual((int(row["faction"]), int(row["npcflag"]), int(row["gossip_menu_id"])),
                                     (35, 1, 2283))
                if boss not in BOUND_BOSSES:
                    continue  # a section 3 or 4 boss: the tier and its stock row until wave 2
                for column, value in EXTRA_COLUMNS.get(boss, {}).items():
                    self.assertEqual(row[column], value, (boss, column))
                self.assertEqual(report.solved.health, health)
                want = EXTRA_COLUMNS.get(boss, {}).get("CreatureImmunitiesId", 1973 if boss in FIRE_IMMUNE else 1972)
                self.assertEqual(int(row["CreatureImmunitiesId"]), want)  # Ribbly keeps the stock -251
                lootid = int(self.existing[boss]["lootid"])
                if OWN_LOOT and boss not in NO_OWN_LOOT:
                    lootid = HEROIC_LOOTID[boss]
                self.assertEqual(int(row["lootid"]), lootid)
        for kit, health in KIT_HEALTH.items():
            if kit in self.reports and health is not None:
                self.assertEqual(self.reports[kit].solved.health, health, kit)
        # Roccor's Loosed Earth hits for 8% of the reference row a swing (the spec), not the elite tier's melee
        if 300780 in self.reports:
            solved = self.reports[300780].solved
            self.assertEqual(solved.swing_ms, 2000)
            self.assertAlmostEqual((solved.min_damage + solved.max_damage) / 2, KIT_MELEE[300780], delta=3)
        if "2" in BOUND and 9178 in rows:
            self.assertEqual(int(rows[heroic_entry[9178]]["CreatureImmunitiesId"]), 0)  # no stock -62
        self.assertEqual(self.reports[8889].solved.health, 37_000)  # elite trash: the tier
        # R-2-FW MIN-2: the Encore's other four (boss role by `extra=`, no credit) do not bind on heroic
        for entry in ENCORE_FOUR:
            self.assertEqual(int(rows[heroic_entry[entry]]["flags_extra"]) & 1, 0, entry)

    def test_the_seven_share_the_boss_melee_tier(self):
        if "2" not in BOUND:
            self.skipTest("wave 2 is not bound: the Seven keep their stock heroic copies")
        melee = set()
        for entry in THE_SEVEN:
            with self.subTest(entry=entry):
                solved = self.reports[entry].solved
                self.assertEqual(solved.tier_row, "boss")
                melee.add(round((solved.min_damage + solved.max_damage) / 2 * 2000 / solved.swing_ms, -1))
        self.assertEqual(len(melee), 1, "one melee value for all seven")
        self.assertAlmostEqual(melee.pop(), 2_500, delta=10)

    def test_the_smart_ai_of_the_normal_only_units_is_widened_to_heroic(self):
        sql, _ = _rendered_or_committed(self.out.smart_blocks)
        self.assertIn(_MARKER, sql)
        self.assertIn("`event_flags` | 4", sql)
        for entry in SMART_WIDENED:
            self.assertIn(f"`entryorguid` = {entry} AND `source_type` = 0", sql)
        for entry in SMART_DROPPED:  # a boss rev deletes every row: nothing left to widen
            self.assertNotIn(f"`entryorguid` = {entry} AND `source_type` = 0", sql)

    def test_spawn_masks_cover_the_boss_spawns_and_skip_the_game_event_ones(self):
        sql, committed = _rendered_or_committed(self.out.spawn_blocks)
        self.assertIn(_MARKER, sql)
        if not committed:
            self.assertIn(230, self.out.map_spawns)
        blocks = sql.split(_MARKER)[1:] if committed else self.out.spawn_blocks
        creature_block = next(b for b in blocks if "UPDATE `creature` " in b)
        guids = {int(g) for g in re.findall(r"\d+", creature_block.split(") AND `guid` IN (")[1])}
        for guid in BOSS_SPAWN_GUIDS:
            self.assertIn(guid, guids)
        for guid in EVENT_CREATURE_GUIDS:  # Elder Morndeep and Coren Direbrew (game events)
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
        self.assertEqual((by_id[1005]["MapID"], by_id[1005]["Difficulty"], by_id[1005]["MaxPlayers"]), (230, 1, 5))
        self.assertEqual({k: v for k, v in by_id.items() if k < 1000}, {r["ID"]: r for r in base})
        order = [(r["MapID"], r["Difficulty"]) for r in back]
        self.assertEqual(order, sorted(order))
        self.assertEqual(sum(1 for r in back if r["MapID"] == 230 and r["Difficulty"] == 1), 1)

        de_path = state.BASE_DBC_DIR / dbcfmt.DUNGEONENCOUNTER.dbc_filename
        base_de = dbcfile.read_dbc(de_path, dbcfmt.DUNGEONENCOUNTER)
        merged_de = {r["ID"]: r for r in base_de}
        merged_de.update(dungeon_heroic.client_encounter_rows(self.dsl["dungeon_encounters"]))
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / dbcfmt.DUNGEONENCOUNTER.dbc_filename
            path.write_bytes(dbcfile.pack_client_dbc(dbcfmt.DUNGEONENCOUNTER, list(merged_de.values()), base_de))
            back_de = dbcfile.read_dbc(path, dbcfmt.DUNGEONENCOUNTER)
        self.assertEqual(len(back_de), len(base_de) + 19)  # all 19, incl. the three that lose their server credit
        self.assertEqual(sorted(r["ID"] for r in back_de if r["MapID"] == 230 and r["Difficulty"] == 1),
                         list(range(1055, 1074)))

    # --- the Finder -------------------------------------------------------------------------------------------

    def _rows(self):
        return {r["ID"]: r for r in self.dsl["lfg_dungeons"]}

    def test_the_two_new_normal_sections(self):
        rows = self._rows()
        stock = {r["ID"]: r for r in dbcfile.read_dbc(state.BASE_DBC_DIR / dbcfmt.LFGDUNGEONS.dbc_filename,
                                                      dbcfmt.LFGDUNGEONS)}
        for entry, name, window, target in ((308, "Blackrock Depths - Shadowforge City", (48, 58), 53),
                                            (309, "Blackrock Depths - Manufactory", (50, 60), 55)):
            row = rows[entry]
            self.assertEqual(row["Name_Lang_enUS"], name)
            self.assertEqual((row["TypeID"], row["Difficulty"], row["Group_Id"], row["MapID"], row["Flags"]),
                             (1, 0, 1, 230, 3))  # Classic Dungeons: Random Classic draws them
            self.assertEqual((row["MinLevel"], row["MaxLevel"], row["Target_Level"]), (*window, target))
            for column in ("TextureFilename", "ExpansionLevel", "Faction"):
                self.assertEqual(row[column], stock[30][column], column)
        # 30 and 276 stay the stock rows (only their final boss / start move)
        self.assertNotIn(30, rows)
        self.assertNotIn(276, rows)

    def test_the_heroic_entries(self):
        rows = self._rows()
        for entry, name in ((310, "Blackrock Depths - Prison"), (311, "Blackrock Depths - Shadowforge City"),
                            (312, "Blackrock Depths - Manufactory"), (313, "Blackrock Depths - Upper City")):
            row = rows[entry]
            self.assertEqual(row["Name_Lang_enUS"], name)
            self.assertEqual((row["TypeID"], row["Difficulty"], row["Group_Id"], row["MapID"], row["Flags"]),
                             (5, 1, 12, 230, 3))
            self.assertEqual((row["MinLevel"], row["MaxLevel"]), (60, 62))

    def test_each_section_completes_on_its_own_last_boss_normal_and_heroic(self):
        heroic = {r["creditEntry"]: r["lastEncounterDungeon"] for r in self.dsl["instance_encounters"]
                  if r["entry"] >= 1000}
        last = {HEROIC_ENCOUNTERS[hid]: lfg for hid, lfg in SECTION_END.items()}
        self.assertEqual(heroic[10096], 310)  # the Ring of Law completes section 1
        self.assertEqual(heroic[9016], 311)  # Bael'Gar completes section 2
        self.assertEqual(heroic[8983], 312)  # Argelmach completes section 3
        self.assertEqual(heroic[9019], 313)  # the Emperor completes section 4
        self.assertEqual({c: v for c, v in heroic.items() if c not in last}, {c: 0 for c in heroic if c not in last})
        # the normal rows (the stock instance_encounters, edited by the Finder DSL): Gerstahn 227 loses 30, the Ring
        # takes it, Bael'Gar and Argelmach end the two new entries, the Emperor stays 276
        normal = {r["entry"]: r["lastEncounterDungeon"] for r in self.dsl["instance_encounters"]
                  if r.get(lfg_dungeons.LINK)}
        self.assertEqual(normal, {227: 0, 230: 30, 235: 308, 237: 309})

    def test_the_start_points(self):
        positions = {t["dungeonId"]: (t["position_x"], t["position_y"], t["position_z"], t["orientation"])
                     for t in self.dsl["lfg_dungeon_templates"]}
        self.assertEqual(positions[308], START_S2)
        self.assertEqual(positions[309], START_S3)
        self.assertEqual(positions[276], START_S4)
        self.assertEqual((positions[311], positions[312], positions[313]), (START_S2, START_S3, START_S4))
        self.assertEqual(positions[310][:3], ENTRANCE)  # section 1 keeps the dungeon entrance

    def test_the_client_lfg_file_gains_the_six_new_rows(self):
        base = dbcfile.read_dbc(state.BASE_DBC_DIR / dbcfmt.LFGDUNGEONS.dbc_filename, dbcfmt.LFGDUNGEONS)
        merged = {r["ID"]: r for r in base}
        merged.update(lfg_dungeons.client_dungeon_rows(self.dsl["lfg_dungeons"]))
        new = set(merged) - {r["ID"] for r in base}
        self.assertEqual(sorted(i for i in new if 308 <= i <= 313), [308, 309, 310, 311, 312, 313])

    def test_random_classic_normal_draws_all_four_sections(self):
        stock = {r["ID"]: r for r in dbcfile.read_dbc(state.BASE_DBC_DIR / dbcfmt.LFGDUNGEONS.dbc_filename,
                                                      dbcfmt.LFGDUNGEONS)}
        pool = {i for i, r in {**stock, **self._rows()}.items() if r["Group_Id"] == 1 and r["TypeID"] == 1}
        self.assertTrue({30, 276, 308, 309} <= pool)


if __name__ == "__main__":
    unittest.main()
