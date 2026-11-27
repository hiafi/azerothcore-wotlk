"""
Scarlet Monastery's heroic declaration (Scarlet Monastery build, WP-H): source/world/dungeons/scarlet_monastery.py as
generate.py loads it, the four Finder sections' heroic entries of source/world/lfg_classic_heroic.py (314-317), the
checkpoint module's "reached only" rows (u_dungeon_checkpoint_2026_11_20_00.sql) and the three-way check of the Finder
starts.

Covered: the heroic() arguments (MapDifficulty 1006 with MaxPlayers 5, dungeon_access 128, DungeonEncounter 1081-1094,
spawn masks, no event spawns), the declared normal encounter rows (FD-SM) and the credit that follows a boss creature's
declaration (`_credit` / `_NO_CREDIT_YET`), the roles / extra / skip declarations, the heroic overrides against the
build spec's numbers (handoff 3.6) and the predicted heroic lootids, the wave switch (BIND_WAVE_2: the Armory's and the
Cathedral's stock units keep their stock heroic copy until wave 2 binds them), the kit units' overrides following the
creature_template() declarations of source/npcs/scarlet_monastery/ (a docstring or comment naming an entry does not
count), and the expansion against the live replay: no ERROR or WARNING, the 14 heroic encounters paired with the
declared normal ones in OrderIndex order (FD-SM's table), the creature set and the predicted heroic_ids.lock lines
(310419 on, normal-entry order), the bosses' INSTANCE_BIND and immunity sets, no SmartAI to widen, the game-event
spawns staying normal-only, the client MapDifficulty.dbc / DungeonEncounter.dbc rows (the patch-Z merge) and the Finder
(four heroic entries completing on the heroic copies of Thalnos, Doan, Herod and Whitemane). The three-way test: S0's
`kSections` starts (ScarletMonasteryRework.h), the lfg_dungeon_template rows the Finder expansion reads and writes, and
the checkpoint SQL (the four entrance rows and the four new spots, with every later UPDATE) agree.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scarlet_monastery_heroic.py
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
from lib import dbcfile, dbcfmt, dungeon_checks, dungeon_encounters, dungeon_heroic, heroic_templates  # noqa: E402
from lib import lfg_dungeons, source, spell_tables, sqlcorpus, state  # noqa: E402
from lib.dsl import registry  # noqa: E402

_MARKER = "-- Scarlet Monastery (map 189) heroic:"
_PENDING = TOOL_ROOT.parents[1] / "data" / "sql" / "updates" / "pending_db_world"
MDB = TOOL_ROOT.parents[1] / "modules" / "mod-dungeon-bosses"
CP_SQL_DIR = TOOL_ROOT.parents[1] / "modules" / "mod-dungeon-checkpoint" / "data" / "sql" / "db-world"


def _rendered_or_committed(blocks: list[str]) -> tuple[str, bool]:
    """The rendered blocks, or (after the write run made them live) the committed rev that carries them."""
    sql = "\n".join(blocks)
    if _MARKER in sql:
        return sql, False
    texts = [f.read_text() for f in sorted(_PENDING.glob("rev_*.sql"))]
    return "\n".join(t for t in texts if _MARKER in t), True


SM_FILE = TOOL_ROOT / "source" / "world" / "dungeons" / "scarlet_monastery.py"
LFG_HEROIC_FILE = TOOL_ROOT / "source" / "world" / "lfg_classic_heroic.py"
KIT_DIR = TOOL_ROOT / "source" / "npcs" / "scarlet_monastery"
HEADER = MDB / "src" / "ScarletMonastery" / "ScarletMonasteryRework.h"
CHECKPOINT_NEW = CP_SQL_DIR / "u_dungeon_checkpoint_2026_11_20_00.sql"
CHECKPOINT_ENTRANCES = CP_SQL_DIR / "u_dungeon_checkpoint_2026_10_11_01.sql"
IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")

# FD-SM's pairing (STAGE-FD-SM-REPORT): the 14 heroic ids in OrderIndex order and the normal encounter each copies.
HEROIC_TO_NORMAL = {
    1081: 444, 1082: 1074, 1083: 1075, 1084: 445, 1085: 446, 1086: 1076, 1087: 1077, 1088: 447, 1089: 1078,
    1090: 1079, 1091: 448, 1092: 1080, 1093: 449, 1094: 450,
}
# The credit of each heroic encounter once every boss creature is declared: (creditType, creditEntry)
CREDITS = {
    1081: (0, 3983), 1082: (0, 6489), 1083: (1, 212300), 1084: (0, 4543), 1085: (0, 3974), 1086: (0, 300910),
    1087: (0, 300913), 1088: (0, 6487), 1089: (0, 300940), 1090: (0, 300942), 1091: (0, 3975), 1092: (0, 300946),
    1093: (1, 212301), 1094: (0, 3977),
}
# The five new bosses (their normal encounter id, their heroic copy's id, their creature): the credit exists once the
# creature_template is declared
KIT_BOSS_CREDIT = {1076: (1086, 300910), 1077: (1087, 300913), 1078: (1089, 300940), 1079: (1090, 300942),
                   1080: (1092, 300946)}
SECTION_END = {1084: 314, 1088: 315, 1091: 316, 1094: 317}  # heroic encounter -> heroic Finder entry
NORMAL_LFG = {314: 18, 315: 165, 316: 163, 317: 164}

# Heroic health at 5 players from the build spec (handoff 3.6) and the wave each stock unit binds in. Wave 1 is the
# Graveyard and the Library (always bound), wave 2 the Armory and the Cathedral (behind BIND_WAVE_2).
WAVE_1_HEALTH = {3983: 280_000, 6489: 240_000, 6488: 170_000, 6490: 130_000, 4543: 300_000, 3974: 210_000,
                 6487: 230_000}
WAVE_2_HEALTH = {3975: 320_000, 6575: 2_500, 3976: 250_000, 3977: 220_000}
WAVE_2_COLUMNS_ONLY = (4542,)  # Fairbanks: the tier's health, flags_extra 0 (no credit of his own)
KIT_HEALTH = {
    300900: 20_000, 300901: 20_000, 300902: 20_000, 300903: 20_000, 300904: 20_000, 300905: 20_000, 300906: 20_000,
    300908: 15_000, 300909: 4_000, 300910: 240_000, 300912: 6_000, 300913: 220_000, 300914: 15_000, 300915: 20_000,
    300916: 2_500, 300919: 5_000, 300920: 15_625, 300921: 6_000,
    300940: 270_000, 300942: 300_000, 300944: 5_000, 300946: 300_000, 300949: 8_000, 300950: 15_000, 300951: 15_000,
    300952: 12_000, 300953: 15_000, 300954: 12_000, 300955: 15_000, 300956: 130_000,
}
KIT_BOSSES = (300910, 300913, 300940, 300942, 300946, 300956)
# Units that run on their normal entry and get no heroic template (handoff 3.3)
KIT_NO_HEROIC = (300907, 300911, 300917, 300918, 300922, 300941, 300943, 300945, 300947, 300948, 300957, 300958)
# Boss units that state flags_extra 0 on their heroic row: no encounter credit of their own (the council's pair credit
# by spell, Mograine by spell, the vigil Fairbanks has no encounter, the stock Fairbanks lost his to the Last Stand)
NO_BIND = (6488, 6490, 3976, 4542, 300956)
# The predicted heroic ids: the lock mints in normal-entry order from 310419 (the extraction set first, 39 lines), then
# the wave 1 kit units, then wave 2's, in entry order. The boss lootids are the same numbers.
FIRST_HEROIC_ID = 310419
HEROIC_ENTRY_COUNT = 39
HEROIC_LOOTID = {3974: 310420, 3975: 310421, 3977: 310423, 3983: 310424, 4543: 310448, 6487: 310451, 6488: 310452,
                 6489: 310453, 6490: 310454}
KIT_HEROIC_ID = {entry: FIRST_HEROIC_ID + HEROIC_ENTRY_COUNT + i for i, entry in enumerate(sorted(KIT_HEALTH))}
KIT_LOOTID = {entry: KIT_HEROIC_ID[entry] for entry in (300910, 300913, 300940, 300942, 300946)}
SKIPPED = (3981, 14693, 16062)
ROLE_CORRECTIONS = {6489: "boss", 6488: "boss", 6490: "boss", 3976: "boss", 4542: "boss"}
# Not heroic: the friendly NPC, the critters, Scorn and the cameo (skip), plus nothing else of the generated block
NOT_HEROIC = (3981, 721, 4075, 14693, 16062)
# Boss spawns (spawnMask 1 live: all get the heroic bit): Loksey, Herod, Mograine, Whitemane, Vishas, Fairbanks,
# Thalnos, Doan, the Fallen Champion, Ironspine, Azshir
BOSS_SPAWN_GUIDS = (40088, 89097, 40029, 39946, 27443, 40039, 39934, 40124, 39894, 12164, 1975841)


def _bound_waves() -> set[str]:
    path = KIT_DIR / "_common.py"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    return {"1"} | {w for w, v in re.findall(r"^BIND_WAVE_(2)\s*=\s*(True|False)\s*$", text, re.M) if v == "True"}


def _own_heroic_loot() -> bool:
    """scarlet_monastery.py's `_HEROIC_BOSS_OWN_LOOT` (off until L-1 declares the heroic loot groups)."""
    m = re.search(r"^_HEROIC_BOSS_OWN_LOOT\s*=\s*(True|False)\s*$", SM_FILE.read_text(encoding="utf-8"), re.M)
    return bool(m) and m.group(1) == "True"


BOUND = _bound_waves()
OWN_LOOT = _own_heroic_loot()


def _kit_declared() -> set[int]:
    """The entries source/npcs/scarlet_monastery/*.py declares with creature_template(<entry>, ...) or a private
    helper taking the entry first (`_part(300900, ...)`, or a module constant: `_risen(GALVAR, ...)`), outside the
    docstrings and comments."""
    pattern = re.compile(r"\b(?:creature_template|_\w+)\(\s*(\d{6}|[A-Z][A-Z0-9_]*)\s*,")
    constant = re.compile(r"^([A-Z][A-Z0-9_]*)\s*=\s*(\d{6})\s*$", re.M)
    docstring = re.compile(r'"""(?:.|\n)*?"""|\'\'\'(?:.|\n)*?\'\'\'')
    found: set[int] = set()
    for path in KIT_DIR.glob("*.py"):
        text = docstring.sub("", path.read_text(encoding="utf-8"))
        text = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith("#"))
        names = {name: int(value) for name, value in constant.findall(text)}
        for arg in pattern.findall(text):
            if arg.isdigit():
                found.add(int(arg))
            elif arg in names:
                found.add(names[arg])
    return found


# Zul'Farrak's rows in the same dungeons package (source/world/dungeons/zul_farrak.py): its repoints of the stock rows
# 593-600 and the two credit spells of 598 / 599 (source/npcs/zul_farrak/instance.py, not loaded here).
ZF_STOCK_ENCOUNTERS = frozenset(range(593, 601))
# Gnomeregan's two declared rows (source/world/dungeons/gnomeregan.py: 379 re-pointed to Techbot, 1107 the Alert System;
# their credit creatures 301105 and 301110 are declared by source/npcs/gnomeregan/, not loaded here)
GN_ENCOUNTERS = frozenset({379, 1107})
ZF_CREDIT_SPELLS = frozenset({213840, 213841})


def _sm_entry(root: Path | None = None) -> tuple[dict, object]:
    reg = registry.load_class_package(
        (root or TOOL_ROOT / "source") / "world" / "dungeons", ids_cfg=IDS)
    return {e["map_id"]: e for e in reg.dungeons}[189], reg


def _fixture(root: Path, *, kit_text: dict[str, str] | None = None, common: str | None = None) -> Path:
    """A copy of the dungeon file beside a fake npc package (so `_KIT_NPCS` points into `root`)."""
    (root / "world" / "dungeons").mkdir(parents=True)
    (root / "npcs" / "scarlet_monastery").mkdir(parents=True)
    (root / "world" / "dungeons" / "scarlet_monastery.py").write_text(SM_FILE.read_text(encoding="utf-8"))
    if common is not None:
        (root / "npcs" / "scarlet_monastery" / "_common.py").write_text(common)
    for name, text in (kit_text or {}).items():
        (root / "npcs" / "scarlet_monastery" / name).write_text(text)
    return root


def _all_kit_declared_text() -> str:
    return "".join(f"x{entry} = creature_template({entry}, 'X')\n" for entry in sorted({*KIT_HEALTH, *KIT_NO_HEROIC}))


class DeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # taken right before the declaration loads: a boss WP may land its files at any time (the other WPs run
        # in this worktree), and both must see the same set
        cls.declared = _kit_declared()
        cls.entry, cls.reg = _sm_entry()
        cls.heroic = cls.entry["heroic"]

    def test_the_ids_are_the_next_of_their_blocks_after_blackrock_depths(self):
        self.assertEqual((self.heroic["map_difficulty_id"], self.heroic["access_id"]), (1006, 128))
        self.assertEqual(self.heroic["encounter_ids"], tuple(range(1081, 1095)))
        self.assertEqual(self.heroic["min_level"], 60)

    def test_the_heroic_row_is_a_five_player_row(self):
        self.assertEqual(self.heroic["max_players"], 5)
        md = {r["ID"]: r for r in self.reg.map_difficulties}[1006]
        self.assertEqual((md["MapID"], md["Difficulty"], md["RaidDuration"], md["MaxPlayers"]), (189, 1, 86400, 5))
        self.assertEqual(md["Message_Lang_enUS"], "Heroic Difficulty requires you to be level 60.")
        self.assertEqual(md["Difficultystring"], "DUNGEON_DIFFICULTY_5PLAYER_HEROIC")
        access = {r["id"]: r for r in self.reg.dungeon_access}[128]
        self.assertEqual((access["map_id"], access["difficulty"], access["min_level"]), (189, 1, 60))

    def test_spawns_go_to_heroic_but_the_event_spawns_stay_normal_only(self):
        self.assertTrue(self.heroic["spawn_mask"])
        self.assertFalse(self.heroic["event_spawns"])

    def test_the_declared_encounters_are_fd_sms_seven_rows_and_the_repoint(self):
        # the dungeons package also holds Zul'Farrak's repoints of its stock rows 593-600 (no map on a repoint)
        decls = {d["id"]: d for d in self.reg.encounter_declarations
                 if d["id"] not in ZF_STOCK_ENCOUNTERS | GN_ENCOUNTERS}
        self.assertEqual(sorted(decls), [449, *range(1074, 1081)])
        self.assertEqual({i: (decls[i]["order_index"], decls[i]["bit"], decls[i]["name"]) for i in range(1074, 1081)}, {
            1074: (250, 7, "Ironspine"), 1075: (500, 8, "Azshir the Sleepless and the Fallen Champion"),
            1076: (2250, 9, "Ambrose Kell"), 1077: (2500, 10, "Lector Hollis Grey"),
            1078: (3250, 11, "Forgemaster Gideon Crell"), 1079: (3500, 12, "Drillmaster Corin Halden"),
            1080: (4500, 13, "Brother Aldous Thorne"),
        })
        self.assertEqual(decls[449]["name"], "The Last Stand")
        self.assertEqual(decls[449]["credit"], (1, 212301))
        self.assertEqual(decls[1074]["credit"], (0, 6489))
        self.assertEqual(decls[1075]["credit"], (1, 212300))

    def test_a_new_boss_credit_follows_its_declared_template(self):
        declared = self.declared
        decls = {d["id"]: d for d in self.reg.encounter_declarations}
        for encounter, (_heroic, boss) in KIT_BOSS_CREDIT.items():
            with self.subTest(encounter=encounter):
                self.assertEqual(decls[encounter]["credit"], (0, boss) if boss in declared else None)
        self.assertEqual(self.heroic["no_credit"],
                         tuple(sorted(e for e, (_h, boss) in KIT_BOSS_CREDIT.items() if boss not in declared)))

    def test_the_credit_appears_when_the_boss_is_declared_and_a_docstring_does_not_count(self):
        with tempfile.TemporaryDirectory() as d:
            root = _fixture(Path(d), kit_text={
                "kell.py": '"""Kell: creature_template(300910, ...) is named here and is not a declaration."""\n'
                           "# creature_template(300913, 'Hollis')\n"
                           "creature_template_columns(6489, x=1)\n",
                "crell.py": "crell = creature_template(300940, 'Crell')\n",
                "halden.py": "def _unit(entry, name):\n    return creature_template(entry, name)\n"
                             "halden = _unit(300942, 'Halden')\n",  # a private helper taking the entry first
            })
            entry, reg = _sm_entry(root)
        decls = {d["id"]: d for d in reg.encounter_declarations}
        self.assertIsNone(decls[1076]["credit"])  # Kell: only named in a docstring
        self.assertIsNone(decls[1077]["credit"])  # Hollis Grey: only in a comment
        self.assertEqual(decls[1078]["credit"], (0, 300940))  # Crell: declared
        self.assertEqual(decls[1079]["credit"], (0, 300942))  # Halden: declared through a private helper
        self.assertEqual(entry["heroic"]["no_credit"], (1076, 1077, 1080))

    def test_roles_extras_and_skips(self):
        by_entry = {c["entry"]: c for c in self.entry["creatures"]}
        for entry, role in ROLE_CORRECTIONS.items():
            self.assertEqual(by_entry[entry]["role"], role, entry)
        self.assertEqual(self.entry["skip"], SKIPPED)
        for extra in KIT_HEALTH:
            self.assertEqual(by_entry[extra]["source"], "extra", extra)
            self.assertTrue(by_entry[extra]["summoned_by"], extra)  # a C++ summon: no spawns, free text names who
            self.assertEqual(by_entry[extra]["spawns"], 0, extra)
            self.assertEqual(by_entry[extra]["role"], "boss" if extra in KIT_BOSSES else "trash", extra)
        for no_heroic in KIT_NO_HEROIC:
            self.assertNotIn(no_heroic, by_entry)  # no template: not in the creature set at all

    def test_stock_overrides_are_the_build_specs_health_the_immunity_set_and_the_loot_flag(self):
        overrides = {entry: dict(pairs) for entry, pairs in self.heroic["overrides"]}
        for entry, health in {**WAVE_1_HEALTH, **WAVE_2_HEALTH}.items():
            with self.subTest(entry=entry):
                wave = "1" if entry in WAVE_1_HEALTH else "2"
                if wave not in BOUND:
                    self.assertNotIn(entry, overrides)  # an Armory or Cathedral unit: stock until wave 2 binds it
                    continue
                self.assertEqual(overrides[entry]["health"], health)
                if entry == 6575:  # the Scarlet Trainee: health and a melee sized for 20 (rule 19), no columns
                    self.assertNotIn("columns", overrides[entry])
                    self.assertEqual(overrides[entry]["melee"], 100)
                    continue
                expected = {"CreatureImmunitiesId": 1972}
                if OWN_LOOT and entry in HEROIC_LOOTID:
                    expected["lootid"] = HEROIC_LOOTID[entry]
                if entry in NO_BIND:
                    expected["flags_extra"] = 0
                self.assertEqual(dict(overrides[entry]["columns"]), expected)
        for entry in WAVE_2_COLUMNS_ONLY:
            self.assertEqual(entry in overrides, "2" in BOUND, entry)
            if "2" in BOUND:
                self.assertEqual(sorted(overrides[entry]), ["columns"])
                self.assertEqual(dict(overrides[entry]["columns"]), {"flags_extra": 0})

    def test_the_predicted_ids_in_the_source_are_the_lock_mint_order(self):
        """The `_boss(health, heroic id)` second arguments of the source are the ids the first write run mints."""
        text = SM_FILE.read_text(encoding="utf-8")
        found = {int(e): int(h) for e, h in re.findall(r"^\s*(\d+): _boss\([\d_]+, (\d+)\)", text, re.M)}
        self.assertEqual(found, {**{e: i for e, i in HEROIC_LOOTID.items()}, **KIT_LOOTID})

    def test_the_wave_one_units_are_the_graveyard_and_the_library(self):
        self.assertEqual(set(WAVE_1_HEALTH), {3983, 6489, 6488, 6490, 4543, 3974, 6487})
        self.assertIn("1", BOUND)

    def test_wave_1_is_bound_and_the_wave_switch_is_read_from_the_npc_package(self):
        for value, bound in (("False", False), ("True", True)):
            with tempfile.TemporaryDirectory() as d:
                root = _fixture(Path(d), common=f"BIND_WAVE_2 = {value}\n")
                entry, _reg = _sm_entry(root)
            overrides = {e: dict(p) for e, p in entry["heroic"]["overrides"]}
            for stock in WAVE_2_HEALTH:
                self.assertEqual(stock in overrides, bound, (value, stock))
            self.assertEqual(4542 in overrides, bound, value)
            for stock in WAVE_1_HEALTH:  # wave 1: always
                self.assertIn(stock, overrides, (value, stock))

    def test_a_missing_common_file_reads_as_wave_2_off(self):
        with tempfile.TemporaryDirectory() as d:
            root = _fixture(Path(d))
            entry, _reg = _sm_entry(root)
        overrides = {e: dict(p) for e, p in entry["heroic"]["overrides"]}
        self.assertEqual(sorted(overrides), sorted(WAVE_1_HEALTH))

    def test_kit_overrides_follow_the_declared_templates(self):
        overrides = {entry: dict(pairs) for entry, pairs in self.heroic["overrides"]}
        declared = self.declared
        self.assertEqual({e: o["health"] for e, o in overrides.items() if e >= 300000},
                         {e: h for e, h in KIT_HEALTH.items() if e in declared})
        for boss in KIT_BOSSES:
            if boss in overrides:
                expected = {"CreatureImmunitiesId": 1972}
                if OWN_LOOT and boss in KIT_LOOTID:
                    expected["lootid"] = KIT_LOOTID[boss]
                if boss in NO_BIND:
                    expected["flags_extra"] = 0
                self.assertEqual(dict(overrides[boss]["columns"]), expected, boss)

    def test_every_kit_unit_gets_its_override_once_declared(self):
        with tempfile.TemporaryDirectory() as d:
            root = _fixture(Path(d), kit_text={"all.py": _all_kit_declared_text()})
            entry, _reg = _sm_entry(root)
        overrides = {e: dict(p) for e, p in entry["heroic"]["overrides"]}
        self.assertEqual({e: o["health"] for e, o in overrides.items() if e >= 300000}, KIT_HEALTH)
        for no_heroic in KIT_NO_HEROIC:
            self.assertNotIn(no_heroic, overrides)  # declared, but no heroic template (handoff 3.3)
        self.assertEqual(entry["heroic"]["no_credit"], ())  # every new boss is declared: all five credits exist

    def test_named_constant_declarations_count_and_the_risen_swing_600(self):
        # D4H declares the risen with `_risen(GALVAR, ...)` (a module constant, not a literal: R-1-KIT M-4)
        text = "GALVAR = 300903\nVOSS = 300905\nx = _risen(GALVAR, 'G')\n# _risen(VOSS, 'V')\n"
        with tempfile.TemporaryDirectory() as d:
            root = _fixture(Path(d), kit_text={"risen.py": text})
            entry, _reg = _sm_entry(root)
        overrides = {e: dict(p) for e, p in entry["heroic"]["overrides"]}
        self.assertEqual(overrides[300903]["health"], 20_000)
        self.assertEqual(overrides[300903]["melee"], 600)
        self.assertNotIn(300905, overrides)  # a comment does not declare
        # the real package: the risen and the generic stalkers are declared (the stalkers get no heroic template)
        self.assertTrue({300903, 300904, 300905, 300906, 300922, 300958} <= self.declared)

    def test_every_override_names_a_listed_creature(self):
        with tempfile.TemporaryDirectory() as d:
            root = _fixture(Path(d), kit_text={"all.py": _all_kit_declared_text()}, common="BIND_WAVE_2 = True\n")
            entry, _reg = _sm_entry(root)
        listed = {c["entry"] for c in entry["creatures"]}
        for unit, _pairs in entry["heroic"]["overrides"]:
            self.assertIn(unit, listed)

    def test_the_mint_order_puts_every_wave_1_unit_below_every_wave_2_unit(self):
        wave_1 = [e for e in KIT_HEALTH if e < 300940]
        wave_2 = [e for e in KIT_HEALTH if e >= 300940]
        self.assertLess(max(wave_1), min(wave_2))
        self.assertEqual(sorted(KIT_HEROIC_ID.values()),
                         list(range(FIRST_HEROIC_ID + HEROIC_ENTRY_COUNT,
                                    FIRST_HEROIC_ID + HEROIC_ENTRY_COUNT + len(KIT_HEROIC_ID))))
        self.assertEqual(sorted(KIT_HEROIC_ID), sorted(KIT_HEROIC_ID, key=KIT_HEROIC_ID.get))
        self.assertEqual(KIT_HEROIC_ID[300910], 310467)  # Kell: the 10th wave 1 unit
        self.assertEqual(KIT_HEROIC_ID[300956], 310487)  # the last one: 12 units of wave 2 after the 18 of wave 1

    def test_no_unit_is_both_heroic_and_unheroic(self):
        self.assertFalse(set(KIT_HEALTH) & set(KIT_NO_HEROIC))


def _parse_header_sections() -> list[dict]:
    text = HEADER.read_text(encoding="utf-8")
    pattern = re.compile(
        r'\{\s*(\d),\s*"(\w+)",\s*(\d+),\s*(\d+),\s*\{\s*([-\d.]+)f,\s*([-\d.]+)f,\s*([-\d.]+)f,\s*([-\d.]+)f\s*\},\s*'
        r'\w+,\s*\{\s*([-\d.]+)f,\s*([-\d.]+)f,\s*([-\d.]+)f,\s*([-\d.]+)f\s*\},\s*'
        r'\{\s*([-\d.]+)f,\s*([-\d.]+)f,\s*([-\d.]+)f\s*\}')
    out = []
    for m in pattern.finditer(text):
        n, name, normal, heroic = int(m[1]), m[2], int(m[3]), int(m[4])
        out.append({"number": n, "name": name, "normal": normal, "heroic": heroic,
                    "start": tuple(float(m[i]) for i in range(5, 9)),
                    "wing": tuple(float(m[i]) for i in range(9, 13)),
                    "exit": tuple(float(m[i]) for i in range(13, 16))})
    return out


def _parse_points() -> dict[str, tuple[float, float, float]]:
    text = HEADER.read_text(encoding="utf-8")
    return {m[1]: (float(m[2]), float(m[3]), float(m[4])) for m in re.finditer(
        r"Point3 constexpr (k\w+)\{\s*([-\d.]+)f,\s*([-\d.]+)f,\s*([-\d.]+)f\s*\}", text)}


def _cp_rows() -> dict[int, dict]:
    """The map 189 entrance-type rows of the checkpoint module, with every later UPDATE of the module's files."""
    rows: dict[int, dict] = {}
    for line in CHECKPOINT_ENTRANCES.read_text().splitlines():
        m = re.match(r"\(189, 0, (\d+), (\d+), ([-\d.]+), ([-\d.]+), ([-\d.]+), ([-\d.]+),\s*'", line)
        if m:
            rows[int(m[1])] = {"order": int(m[2]), "pos": tuple(float(m[i]) for i in range(3, 7)), "reach": 0.0}
    text = CHECKPOINT_NEW.read_text()
    for m in re.finditer(r"^\(189, 0, (\d+), (\d+), ([-\d.]+), ([-\d.]+), ([-\d.]+), ([-\d.]+), ([-\d.]+),\s*$", text,
                         re.M):
        rows[int(m[1])] = {"order": int(m[2]), "pos": tuple(float(m[i]) for i in range(3, 7)),
                           "reach": float(m[7])}
    return rows


class CheckpointSqlTest(unittest.TestCase):
    """The checkpoint rows of this WP and the three-way check of the Finder starts (S0's kSections, the checkpoint
    SQL, and the lfg_dungeon_template rows the Finder expansion reads: ExpansionTest below)."""

    @classmethod
    def setUpClass(cls):
        cls.sections = _parse_header_sections()
        cls.rows = _cp_rows()
        cls.points = _parse_points()

    def test_the_header_has_four_sections_with_their_finder_ids(self):
        self.assertEqual([(s["number"], s["normal"], s["heroic"]) for s in self.sections],
                         [(1, 18, 314), (2, 165, 315), (3, 163, 316), (4, 164, 317)])
        self.assertEqual({s["heroic"]: s["normal"] for s in self.sections}, NORMAL_LFG)

    def test_the_four_entrance_rows_are_the_headers_starts(self):
        entrance = [self.rows[i] for i in (0, 1, 2, 3)]
        for section in self.sections:
            near = [r for r in entrance if all(abs(a - b) < 1e-3 for a, b in zip(r["pos"], section["start"]))]
            self.assertEqual(len(near), 1, section["name"])
            self.assertEqual((near[0]["order"], near[0]["reach"]), (0, 0.0))  # always a candidate

    def test_the_new_rows_are_reached_only_order_0_one_per_wing(self):
        new = {i: self.rows[i] for i in (4, 5, 6, 7)}
        self.assertEqual(sorted(self.rows), [0, 1, 2, 3, 4, 5, 6, 7])
        for index, row in new.items():
            self.assertEqual((row["order"], row["reach"]), (0, 15.0), index)
        def wing_of(x: float, y: float) -> int:
            return next(s["number"] for s in self.sections
                        if s["wing"][0] <= x <= s["wing"][1] and s["wing"][2] <= y <= s["wing"][3])

        wings = [wing_of(row["pos"][0], row["pos"][1]) for row in new.values()]
        self.assertEqual(wings, [1, 2, 3, 4])  # Graveyard, Library, Armory, Cathedral: one each, in the wing box

    def test_the_new_spots_are_short_of_the_end_boss_and_clear_of_every_fight_spot(self):
        p = self.points
        ends = {4: p["kThalnosSpawn"], 5: p["kDoanSpawn"], 6: p["kHerodSpawn"], 7: p["kMograineSpawn"]}
        fights = {
            4: [p["kCouncilLawn"], p["kThalnosSpawn"], p["kIronspineHome"], p["kVishasSpawn"]],
            5: [p["kLokseySpawn"], p["kKellSpot"], p["kHollisGreySpot"], p["kDoanSpawn"]],
            6: [p["kCrellAnvil"], p["kHaldenSpot"], p["kHerodSpawn"]],
            7: [p["kThorneSpot"], p["kMograineSpawn"], p["kWhitemaneVigil"]],
        }
        for index, spots in fights.items():
            x, y, _z, _o = self.rows[index]["pos"]
            for spot in spots:
                self.assertGreaterEqual(math.hypot(x - spot[0], y - spot[1]), 35 if index != 7 else 35,
                                        (index, spot))
            # nearer to its own end boss than any other wing's start (the wings are 600+ yd apart)
            own = math.hypot(x - ends[index][0], y - ends[index][1])
            for section in self.sections:
                self.assertLess(own, math.hypot(x - section["start"][0], y - section["start"][1]) + 800)

    def test_the_new_spots_are_clear_of_the_exit_triggers_and_the_portal_spots(self):
        text = HEADER.read_text(encoding="utf-8")
        portals = [tuple(float(v) for v in m.groups()) for m in re.finditer(
            r'\{\s*\d,\s*"P\d\w*",\s*\{\s*([-\d.]+)f,\s*([-\d.]+)f,\s*([-\d.]+)f', text)]
        self.assertEqual(len(portals), 4)
        for index in (4, 5, 6, 7):
            x, y, _z, _o = self.rows[index]["pos"]
            for section in self.sections:
                self.assertGreater(math.hypot(x - section["exit"][0], y - section["exit"][1]), 8 + 15)
            for portal in portals:
                self.assertGreater(math.hypot(x - portal[0], y - portal[1]), 8, (index, portal))

    def test_the_sql_is_rerunnable_and_names_the_column_it_sets(self):
        text = CHECKPOINT_NEW.read_text()
        self.assertIn("DELETE FROM `dungeon_checkpoint_location`", text)
        self.assertIn("`location_index` IN (4, 5, 6, 7)", text)
        self.assertIn("`reach_radius`", text)
        self.assertGreater(CHECKPOINT_NEW.name, "u_dungeon_checkpoint_2026_11_18_00.sql")  # applied last
        self.assertEqual(sorted(p.name for p in CP_SQL_DIR.glob("u_dungeon_checkpoint_2026_11_20*")),
                         [CHECKPOINT_NEW.name])
        for line in text.splitlines():
            self.assertLessEqual(len(line), 120, line)


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
            # The Scarlet Monastery boss package declares its kit units (source/npcs/scarlet_monastery/) as they land
            if KIT_DIR.is_dir():
                kit = registry.load_class_package(
                    KIT_DIR, ids_cfg=IDS, existing_creature_rows=existing,
                    creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
                    creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS, live_data={},
                )
                for key in ("creature_templates", "creature_template_models", "creature_template_edits"):
                    cls.dsl[key] = cls.dsl.get(key, []) + list(getattr(kit, key))
            # only Scarlet Monastery's heroic is expanded here (the other dungeons have their own tests)
            cls.dsl["dungeons"] = [e if e["map_id"] == 189 else dict(e, heroic=None) for e in cls.dsl["dungeons"]]
            # Gnomeregan's rows (credit creatures not loaded here) belong to test_gnomeregan_heroic.py
            cls.dsl["encounter_declarations"] = [d for d in cls.dsl["encounter_declarations"]
                                                 if d["id"] not in GN_ENCOUNTERS]
            cls.index = spell_tables.load_spell_table_index()
            cls.encounters = dungeon_encounters.expand(cls.dsl, lambda: dungeon_encounters.load_inputs(
                cls.index, {*existing, *(int(r["entry"]) for r in cls.dsl.get("creature_templates", []))},
                spell_ids={212300, 212301, *ZF_CREDIT_SPELLS}, ids_cfg=IDS))
            cls.out = dungeon_heroic.expand(
                cls.dsl, lambda: dungeon_heroic.load_live_world(existing, cls.index), ids_cfg=IDS,
            )
            cls.existing = existing
            # generate.py's next step: the finder (source/world/lfg_classic_*.py) with only this map's entries
            heroic = registry.load_class_file(LFG_HEROIC_FILE, ids_cfg=IDS)
            cls.dsl["lfg_group_declarations"] = list(heroic.lfg_group_declarations)
            cls.dsl["lfg_dungeon_declarations"] = [
                d for d in heroic.lfg_dungeon_declarations
                if d["kind"] == "random" or d.get("normal") in NORMAL_LFG.values()
            ]
            cls.lfg_inputs = lfg_dungeons.load_inputs(cls.index)
            cls.lfg_out = lfg_dungeons.expand(cls.dsl, lambda: cls.lfg_inputs)
        finally:
            sqlcorpus.deactivate()
        cls.entry = next(e for e in cls.dsl["dungeons"] if e["map_id"] == 189)
        cls.reports = {r.normal: r for r in cls.out.heroic_reports}

    def _heroic_link_errors(self) -> list[str]:
        """The ERRORs that ask a declared kit unit to name its heroic entry in difficulty_entry_1
        (lib/dungeon_heroic.py: 'declares the full row - set difficulty_entry_1 there'). A boss WP declares its units
        before the last of the lower-numbered ones has landed, and the minted id shifts until it has (the mint-order
        note in scarlet_monastery.py): they are checked by `test_declared_kit_units_carry_their_heroic_entry`, not
        here."""
        return [e for e in self.out.errors if "declares the full row - set difficulty_entry_1" in e]

    def test_it_is_clean(self):
        self.assertEqual((self.encounters.errors, self.encounters.warnings), ([], []))
        self.assertEqual([e for e in self.out.errors if e not in self._heroic_link_errors()], [])
        self.assertEqual(self.out.warnings, [])
        self.assertEqual((self.lfg_out.errors, self.lfg_out.warnings), ([], []))

    def test_declared_kit_units_carry_their_heroic_entry(self):
        """A kit unit that names its heroic id in its own `creature_template()` row names the one of the predicted
        table (KIT_HEROIC_ID) once every lower-numbered unit is declared too. A row that names none yet is the run's
        own ERROR (`_heroic_link_errors`, the number it prints), which the boss WP clears with the table; nothing may
        be left in that list once all 30 units have landed."""
        rows = {int(r["entry"]): r for r in self.dsl["creature_templates"] if not r.get(dungeon_heroic.DERIVED)}
        for entry in sorted(KIT_HEALTH):
            if entry not in rows or not int(rows[entry].get("difficulty_entry_1") or 0):
                continue
            with self.subTest(entry=entry):
                if all(lower in rows for lower in KIT_HEALTH if lower < entry):
                    self.assertEqual(int(rows[entry]["difficulty_entry_1"]), KIT_HEROIC_ID[entry])
                else:
                    self.assertLessEqual(int(rows[entry]["difficulty_entry_1"]), KIT_HEROIC_ID[entry])
        if set(KIT_HEALTH) <= set(rows):
            self.assertEqual(self._heroic_link_errors(), [])

    def test_fourteen_heroic_encounters_in_the_kill_order(self):
        rows = {r["ID"]: r for r in self.dsl["dungeon_encounters"] if r["Difficulty"] == 1}
        self.assertEqual(sorted(rows), list(range(1081, 1095)))  # 14 rows: the client's lockout list
        normal = {r["ID"]: r for r in self.dsl["dungeon_encounters"]
                  if r["Difficulty"] == 0 and r["ID"] not in ZF_STOCK_ENCOUNTERS | GN_ENCOUNTERS}
        self.assertEqual(sorted(normal), [449, *range(1074, 1081)])  # the declared rows (the stock ones are not here)
        stock = {r["ID"]: r for r in dbcfile.read_dbc(state.BASE_DBC_DIR / dbcfmt.DUNGEONENCOUNTER.dbc_filename,
                                                      dbcfmt.DUNGEONENCOUNTER)}
        for heroic_id, normal_id in HEROIC_TO_NORMAL.items():
            source_row = normal.get(normal_id) or stock[normal_id]
            row = rows[heroic_id]
            self.assertEqual((row["MapID"], row["Difficulty"]), (189, 1))
            self.assertEqual((row["Bit"], row["OrderIndex"], row["Name_Lang_enUS"]),
                             (source_row["Bit"], source_row["OrderIndex"], source_row["Name_Lang_enUS"]), heroic_id)
        self.assertEqual([r["OrderIndex"] for _i, r in sorted(rows.items())],
                         sorted(r["OrderIndex"] for r in rows.values()))  # ids in OrderIndex order
        self.assertEqual(sorted(r["Bit"] for r in rows.values()), list(range(14)))

    def test_the_credits_follow_the_declared_boss_creatures(self):
        credits = {r["entry"]: (int(r["creditType"]), int(r["creditEntry"]))
                   for r in self.dsl["instance_encounters"] if r["entry"] >= 1000}
        # the file's own view (`no_credit`): a new boss's copy has no credit until its creature is declared
        dropped = set(self.entry["heroic"]["no_credit"])
        expected = {h: c for h, c in CREDITS.items() if HEROIC_TO_NORMAL[h] not in dropped}
        self.assertEqual({h: c for h, c in credits.items() if h >= 1081}, expected)
        # the normal rows: Ironspine, the council by spell, the Last Stand repointed to its spell (449)
        normal = {r["entry"]: (int(r["creditType"]), int(r["creditEntry"]))
                  for r in self.dsl["instance_encounters"] if r["entry"] < 1081}
        self.assertEqual(normal[1074], (0, 6489))
        self.assertEqual(normal[1075], (1, 212300))
        self.assertEqual(normal[449], (1, 212301))

    def test_the_creature_set(self):
        mapping = self.entry["heroic_entries"]
        for boss in (3983, 6489, 6488, 6490, 4543, 3974, 6487, 3975, 3976, 3977, 4542, 6575):
            self.assertIn(boss, mapping)
        for hostile in (4283, 4295, 4301, 4308, 6426, 6427, 6493, 575):
            self.assertIn(hostile, mapping)
        for out in NOT_HEROIC:
            self.assertNotIn(out, mapping)
        declared_rows = {int(r["entry"]) for r in self.dsl["creature_templates"] if not r.get(dungeon_heroic.DERIVED)}
        for kit in KIT_HEALTH:
            self.assertEqual(kit in mapping, kit in declared_rows, kit)
        for no_heroic in KIT_NO_HEROIC:
            self.assertNotIn(no_heroic, mapping)
        block = IDS["creature_heroic"]
        locked = heroic_templates.parse_lock(heroic_templates.LOCK_PATH.read_text()).pairs
        for normal, heroic in mapping.items():
            self.assertTrue(block["start"] <= heroic <= block["end"], (normal, heroic))
        self.assertEqual(len(set(mapping.values())), len(mapping))
        self.assertFalse(set(mapping.values()) & {h for n, h in locked.items() if n not in mapping})

    def test_the_predicted_lock_lines(self):
        """The ids the first write run mints: normal-entry order from 310419 (39 lines for the extraction set), the
        boss lootids are the same numbers. The kit units come after, wave by wave in entry order, and each unit's
        creature_template must name its id in difficulty_entry_1."""
        mapping = self.entry["heroic_entries"]
        locked = heroic_templates.parse_lock(heroic_templates.LOCK_PATH.read_text()).pairs
        fresh = {n: h for n, h in mapping.items() if n not in locked}
        if set(fresh) != set(mapping):  # after the write run the lines are committed: the same numbers
            fresh = mapping
        existing = {n: h for n, h in fresh.items() if n < 300000}
        self.assertEqual(sorted(existing.values()), list(range(FIRST_HEROIC_ID, FIRST_HEROIC_ID + len(existing))))
        self.assertEqual(sorted(existing), sorted(existing, key=lambda n: existing[n]))  # ids follow the entry order
        self.assertEqual(len(existing), HEROIC_ENTRY_COUNT)
        for boss, heroic in HEROIC_LOOTID.items():
            self.assertEqual(existing[boss], heroic, boss)
        # the declared kit units mint consecutively after them, in entry order; the full table holds once every unit
        # is declared (a missing lower unit shifts the later ones down, never up)
        kit = sorted(e for e in fresh if e >= 300000)
        for rank, entry in enumerate(kit):
            self.assertEqual(fresh[entry], FIRST_HEROIC_ID + HEROIC_ENTRY_COUNT + rank, entry)
            self.assertLessEqual(fresh[entry], KIT_HEROIC_ID[entry], entry)
        if set(KIT_HEALTH) <= set(fresh):
            for entry, heroic in KIT_HEROIC_ID.items():
                self.assertEqual(fresh[entry], heroic, entry)

    def test_bosses(self):
        rows = {int(r["entry"]): r for r in self.dsl["creature_templates"] if r.get(dungeon_heroic.DERIVED)}
        heroic_entry = self.entry["heroic_entries"]
        for boss, health in {**WAVE_1_HEALTH, **WAVE_2_HEALTH}.items():
            with self.subTest(boss=boss):
                wave = "1" if boss in WAVE_1_HEALTH else "2"
                row = rows[heroic_entry[boss]]
                self.assertEqual((row["minlevel"], row["maxlevel"], row["exp"]), (60, 60, 0))
                if wave not in BOUND:
                    continue  # an Armory or Cathedral unit: the tier and its stock row until wave 2
                self.assertEqual(self.reports[boss].solved.health, health)
                if boss == 6575:
                    # twenty at once: 100 a 2.0 s swing each, 1,000 DPS in all (24% of the 4,110 tank row a second)
                    solved = self.reports[boss].solved
                    swing = (solved.min_damage + solved.max_damage) / 2 * 2000 / solved.swing_ms
                    self.assertAlmostEqual(swing, 100, delta=5)
                    self.assertLessEqual(20 * swing / 2.0, 0.25 * 4_110)
                    continue
                self.assertEqual(int(row["CreatureImmunitiesId"]), 1972)
                self.assertEqual(int(row["flags_extra"]) & 1, 0 if boss in NO_BIND else 1)  # INSTANCE_BIND
                lootid = int(self.existing[boss]["lootid"])
                if OWN_LOOT and boss in HEROIC_LOOTID:
                    lootid = HEROIC_LOOTID[boss]
                self.assertEqual(int(row["lootid"]), lootid)
        for kit, health in KIT_HEALTH.items():
            if kit in self.reports:
                self.assertEqual(self.reports[kit].solved.health, health, kit)
        # a boss role without a credit of its own does not bind (the council's pair, Mograine, the vigil Fairbanks)
        for boss in NO_BIND:
            if boss in (3976, 4542) and "2" not in BOUND:
                continue  # their wave 2 override is not applied: the stock heroic copy
            if boss == 300956 and boss not in heroic_entry:
                continue
            self.assertEqual(int(rows[heroic_entry[boss]]["flags_extra"]) & 1, 0, boss)
        self.assertEqual(self.reports[4283].solved.health, 37_000)  # elite trash: the tier

    def test_the_credit_carrying_bosses_bind(self):
        rows = {int(r["entry"]): r for r in self.dsl["creature_templates"] if r.get(dungeon_heroic.DERIVED)}
        heroic_entry = self.entry["heroic_entries"]
        for boss in (3983, 6489, 4543, 3974, 6487, 3975, 3977):
            if boss in WAVE_2_HEALTH and "2" not in BOUND:
                continue
            self.assertEqual(int(rows[heroic_entry[boss]]["flags_extra"]) & 1, 1, boss)

    def test_the_boss_melee_tier_is_2500_a_swing(self):
        for boss in (3983, 6489, 4543, 3974, 6487, 6488, 6490):
            solved = self.reports[boss].solved
            self.assertEqual(solved.tier_row, "boss", boss)
            swing = (solved.min_damage + solved.max_damage) / 2 * 2000 / solved.swing_ms
            self.assertAlmostEqual(swing, 2_500, delta=10)

    def test_there_is_no_normal_only_smart_ai_to_widen(self):
        """The stock SmartAI rows of the map carry event_flags 0 or 1 (every difficulty), none the normal-only bit
        (SMART_EVENT_FLAG_DIFFICULTY_0), so the heroic expansion writes no widening block (unlike Blackrock Depths).
        Boss revs that insert SmartAI rows set `event_flags | 4` on them themselves."""
        self.assertEqual(self.out.smart_blocks, [])
        self.assertFalse([n for n in self.out.notes if "SmartAI" in n])

    def test_spawn_masks_cover_the_boss_spawns_and_skip_the_game_event_ones(self):
        sql, committed = _rendered_or_committed(self.out.spawn_blocks)
        self.assertIn(_MARKER, sql)
        if not committed:
            self.assertIn(189, self.out.map_spawns)
        blocks = sql.split(_MARKER)[1:] if committed else self.out.spawn_blocks
        creature_block = next(b for b in blocks if "UPDATE `creature` " in b)
        guids = {int(g) for g in re.findall(r"\d+", creature_block.split(") AND `guid` IN (")[1])}
        for guid in BOSS_SPAWN_GUIDS:
            self.assertIn(guid, guids)

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
        self.assertEqual((by_id[1006]["MapID"], by_id[1006]["Difficulty"], by_id[1006]["MaxPlayers"]), (189, 1, 5))
        self.assertEqual({k: v for k, v in by_id.items() if k < 1000}, {r["ID"]: r for r in base})
        order = [(r["MapID"], r["Difficulty"]) for r in back]
        self.assertEqual(order, sorted(order))
        self.assertEqual(sum(1 for r in back if r["MapID"] == 189 and r["Difficulty"] == 1), 1)

        de_path = state.BASE_DBC_DIR / dbcfmt.DUNGEONENCOUNTER.dbc_filename
        base_de = dbcfile.read_dbc(de_path, dbcfmt.DUNGEONENCOUNTER)
        merged_de = {r["ID"]: r for r in base_de}
        merged_de.update(dungeon_heroic.client_encounter_rows(self.dsl["dungeon_encounters"]))
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / dbcfmt.DUNGEONENCOUNTER.dbc_filename
            path.write_bytes(dbcfile.pack_client_dbc(dbcfmt.DUNGEONENCOUNTER, list(merged_de.values()), base_de))
            back_de = dbcfile.read_dbc(path, dbcfmt.DUNGEONENCOUNTER)
        self.assertEqual(len(back_de), len(base_de) + 7 + 14)  # 7 new normal rows (449 is replaced) + 14 heroic
        self.assertEqual(sorted(r["ID"] for r in back_de if r["MapID"] == 189 and r["Difficulty"] == 1),
                         list(range(1081, 1095)))
        self.assertEqual(sorted(r["ID"] for r in back_de if r["MapID"] == 189 and r["Difficulty"] == 0),
                         [444, 445, 446, 447, 448, 449, 450, *range(1074, 1081)])

    # --- the Finder -------------------------------------------------------------------------------------------

    def _rows(self):
        return {r["ID"]: r for r in self.dsl["lfg_dungeons"]}

    def test_the_heroic_entries(self):
        rows = self._rows()
        stock = {r["ID"]: r for r in dbcfile.read_dbc(state.BASE_DBC_DIR / dbcfmt.LFGDUNGEONS.dbc_filename,
                                                      dbcfmt.LFGDUNGEONS)}
        for entry, name in ((314, "Scarlet Monastery - Graveyard"), (315, "Scarlet Monastery - Library"),
                            (316, "Scarlet Monastery - Armory"), (317, "Scarlet Monastery - Cathedral")):
            row = rows[entry]
            self.assertEqual(row["Name_Lang_enUS"], name)
            self.assertEqual((row["TypeID"], row["Difficulty"], row["Group_Id"], row["MapID"], row["Flags"]),
                             (5, 1, 12, 189, 3))
            self.assertEqual((row["MinLevel"], row["MaxLevel"]), (60, 62))
            self.assertEqual(row["TextureFilename"], stock[NORMAL_LFG[entry]]["TextureFilename"])
        # the four normal rows stay the stock rows: nothing written for 18, 165, 163, 164
        for normal in NORMAL_LFG.values():
            self.assertNotIn(normal, rows)

    def test_each_section_completes_on_its_own_last_boss_normal_and_heroic(self):
        credits = {r["entry"]: r for r in self.dsl["instance_encounters"] if r["entry"] >= 1081}
        for heroic_id, lfg in SECTION_END.items():
            self.assertEqual(credits[heroic_id]["lastEncounterDungeon"], lfg, heroic_id)
        self.assertEqual({e: r["lastEncounterDungeon"] for e, r in credits.items() if e not in SECTION_END},
                         {e: 0 for e in credits if e not in SECTION_END})
        # the normal rows are stock: no edit of a normal link (the four sections already end on the right bosses)
        self.assertEqual({r["entry"] for r in self.dsl["instance_encounters"] if r.get(lfg_dungeons.LINK)}, set())

    def test_the_start_points_are_the_stock_ones_and_the_three_way_agrees(self):
        """S0's kSections starts == the lfg_dungeon_template rows (normal, as the Finder expansion reads them) == the
        heroic entries' copies == the checkpoint SQL's four entrance rows."""
        sections = _parse_header_sections()
        cp = _cp_rows()
        written = {t["dungeonId"]: (t["position_x"], t["position_y"], t["position_z"], t["orientation"])
                   for t in self.dsl["lfg_dungeon_templates"]}
        live = {i: tuple(float(self.lfg_inputs.positions[i][c]) for c in
                         ("position_x", "position_y", "position_z", "orientation")) for i in NORMAL_LFG.values()}
        for section in sections:
            start = section["start"]
            normal, heroic = section["normal"], section["heroic"]
            for label, position in (("lfg_dungeon_template (normal)", live[normal]),
                                    ("lfg_dungeon_template (heroic copy)", written[heroic])):
                for got, want in zip(position, start):
                    self.assertAlmostEqual(float(got), want, delta=1e-3, msg=(section["name"], label))
            self.assertEqual(written[heroic], live[normal], section["name"])  # the heroic entry copies it exactly
            self.assertTrue(any(all(abs(a - b) < 1e-3 for a, b in zip(row["pos"], start)) for index, row in
                                cp.items() if index < 4), section["name"])

    def test_the_client_lfg_file_gains_the_four_new_rows(self):
        base = dbcfile.read_dbc(state.BASE_DBC_DIR / dbcfmt.LFGDUNGEONS.dbc_filename, dbcfmt.LFGDUNGEONS)
        merged = {r["ID"]: r for r in base}
        merged.update(lfg_dungeons.client_dungeon_rows(self.dsl["lfg_dungeons"]))
        new = set(merged) - {r["ID"] for r in base}
        self.assertEqual(sorted(i for i in new if 300 <= i <= 399), [300, 314, 315, 316, 317])

    def test_random_classic_heroic_draws_the_four_sections(self):
        stock = {r["ID"]: r for r in dbcfile.read_dbc(state.BASE_DBC_DIR / dbcfmt.LFGDUNGEONS.dbc_filename,
                                                      dbcfmt.LFGDUNGEONS)}
        pool = {i for i, r in {**stock, **self._rows()}.items() if r["Group_Id"] == 12 and r["TypeID"] == 5}
        self.assertTrue({314, 315, 316, 317} <= pool)


if __name__ == "__main__":
    unittest.main()
