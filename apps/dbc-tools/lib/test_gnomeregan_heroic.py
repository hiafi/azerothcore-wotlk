"""
Gnomeregan's heroic declaration (Gnomeregan build, WP-H): source/world/dungeons/gnomeregan.py as generate.py loads it,
the two Finder sections of source/world/lfg_classic_sections.py (14 re-ended, 320 new) and the heroic entries 321 and
322 of source/world/lfg_classic_heroic.py, the Dark Iron Ambassador's row (source/npcs/gnomeregan/dark_iron_ambassador.
py) and the three conf lines (the content gate's `90:N,H`, BM's `MapLevels` pins `90:28 90h:60`, DD's `Heroic.Maps`
+= 90).

Covered: the heroic() arguments (MapDifficulty 1009 with MaxPlayers 5, dungeon_access 131, DungeonEncounter 1108-1113,
spawn masks, no event spawns, the exile normal-only), the two declared encounters (379 re-pointed from Grubbis to
Techbot, 1107 the Alert System; both credit by kill), the roles / skip / extra declarations, the boss overrides against
the build spec's numbers (handoff 3.6, pinned to the header's `Health` table) with the stun immunity set, flags_extra
and detection range pinned to the normal rows' `boss_columns()`, the Ambassador's numbers (normal 42,017, heroic
260,000), the unscaled adds, the kit units' overrides following their `creature_template()` declarations (a docstring
or comment naming the entry does not count; the text scan agrees with the real npc package), the predicted heroic ids
(`_HEROIC_ID`), and the expansion against the live replay: no ERROR or WARNING (bar the two that only the boss WPs'
`difficulty_entry_1` clears), the six heroic encounters paired with the normal rows in OrderIndex order and their
credits (all by creature), the Finder (14 ends at 380, 320 at 382, the heroic 321 and 322 complete on 1110 and 1113),
the creature set and the predicted heroic_ids.lock lines (310543 on, normal-entry order, the table the boss WPs read),
the bosses' INSTANCE_BIND, immunity, assist flags and detection range, the tier's trash and melee, the spawn masks, and
the client MapDifficulty.dbc / DungeonEncounter.dbc / LFGDungeons.dbc rows (the patch-Z merge).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_gnomeregan_heroic.py
"""

from __future__ import annotations

import ast
import importlib.util
import math
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import generate  # noqa: E402
from lib import dbcfile, dbcfmt, dungeon_checks, dungeon_encounters, dungeon_heroic, heroic_templates  # noqa: E402
from lib import lfg_dungeons, source, spawn_state, spell_tables, sqlcorpus, state  # noqa: E402
from lib.dsl import registry  # noqa: E402

GN_FILE = TOOL_ROOT / "source" / "world" / "dungeons" / "gnomeregan.py"
LFG_HEROIC_FILE = TOOL_ROOT / "source" / "world" / "lfg_classic_heroic.py"
LFG_SECTIONS_FILE = TOOL_ROOT / "source" / "world" / "lfg_classic_sections.py"
KIT_DIR = TOOL_ROOT / "source" / "npcs" / "gnomeregan"
COMMON_FILE = KIT_DIR / "_common.py"
HEADER = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Gnomeregan" / "GnomereganRework.h"
CONTENT_GATE_DIST = REPO_ROOT / "modules" / "mod-content-gate" / "conf" / "content_gate.conf.dist"
WORKTREES = REPO_ROOT.parent
BM_CONF_DIST = WORKTREES / "boss-mechanics-gnomer" / "conf" / "mod_boss_mechanics.conf.dist"
DD_CONF_DIST = WORKTREES / "mod-dungeon-difficulties-gnomer" / "conf" / "mod_dungeon_difficulties.conf.dist"
IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")

MAP_ID = 90

# The six encounters in kill order and the heroic copies in (OrderIndex, Bit, ID) order of the declared normal rows:
# normal id -> (heroic id, OrderIndex, Bit, name, credit (type, entry)). 379 is Grubbis's row re-pointed to Techbot,
# 1107 is new; 378, 380, 381 and 382 are stock and keep their name and credit.
ENCOUNTERS = {
    379: (1108, 2000, 2, "Techbot", (0, 301105)),
    378: (1109, 2500, 1, "Viscous Fallout", (0, 7079)),
    380: (1110, 3000, 3, "Electrocutioner 6000", (0, 6235)),
    1107: (1111, 3500, 0, "The Mobile Alert System", (0, 301110)),
    381: (1112, 4000, 4, "Crowd Pummeler 9-60", (0, 6229)),
    382: (1113, 5000, 5, "Mekgineer Thermaplugg", (0, 7800)),
}
HEROIC_ENCOUNTER_IDS = tuple(range(1108, 1114))
DECLARED_ENCOUNTERS = (379, 1107)
# The Finder: stock 14 ends at Electrocutioner (380), the new 320 at Thermaplugg (382); the heroic entries 321 and 322
# follow the links to the heroic copies.
FINDER_14, FINDER_320, FINDER_HEROIC_14, FINDER_HEROIC_320 = 14, 320, 321, 322
FINDER_LINKS = {380: FINDER_14, 382: FINDER_320}
HEROIC_LINKS = {1110: FINDER_HEROIC_14, 1113: FINDER_HEROIC_320}
SECTION_START = (-736.51, 2.71, -249.99, 3.14)

# Heroic boss health: the header's `Health` table, heroic column (x4/3 of the spec). entry -> (header name, class base
# basehp0 at level 60: warrior 3,052, paladin 2,442; the engine's health is ceil(base x HealthModifier))
BOSSES = {
    301105: ("kTechbot", 3_052), 7079: ("kViscousFallout", 3_052), 6235: ("kElectrocutioner", 3_052),
    301110: ("kAlertSystem", 3_052), 6229: ("kCrowdPummeler", 3_052), 7800: ("kThermaplugg", 3_052),
}
AMBASSADOR = 6228  # the rare of ruling 5: a level 28 paladin (class base 732), rare tier at level 60 (paladin 2,442)
AMBASSADOR_BASE_28 = 732
TIER_MELEE = 2_500
RARE_MELEE = 900
# the kit units with their own heroic numbers (handoff 3.6 "Unscaled"): entry -> header name, applied once a source file
# declares the template
KIT_HEADER = {
    301106: "kDupeBug", 301111: "kSecurityAssistant", 301112: "kSecurityDefender", 301120: "kWalkingBomb",
    301121: "kWalkingBomb", 301122: "kWalkingBomb", 301123: "kWalkingBomb",
}
KIT_HEALTH = {301106: 4_000, 301111: 6_000, 301112: 12_000, 301120: 5_000, 301121: 5_000, 301122: 5_000,
              301123: 5_000}
# the kit units that get a heroic template (the extra= creatures bar the exile), in entry order
# (INT reconcile: the hard mode's puddle 301135 and fist 301136 are unselectable helpers and run on their normal entry)
KIT_EXTRA = (301105, 301106, 301110, 301111, 301112, 301120, 301121, 301122, 301123, 301124)
NORMAL_ONLY = 301190
# Chomper, Grubbis (Emi's event is cut) and the stock Walking Bomb (the faces' SmartAI that summoned it is gone)
SKIPPED = (6215, 7361, 7915)
NPC_ENTRIES = (7850, 7998, 9676)
HEADER_NAMES = {name for name, _base in BOSSES.values()} | {"kDarkIronAmbassador"} | set(KIT_HEADER.values())

# The predicted heroic ids: the write run mints in normal-entry order from 310543: the stock set (32 lines: the
# extraction's 36 creatures bar the npcs, the trigger and the three skips) and the declared kit units after it, in
# entry order.
FIRST_HEROIC_ID = 310543
STOCK_SET_COUNT = 32
HEROIC_LOOT_BOSSES = (301105, 7079, 6235, 301110, 7800, 6228)
# stock trash ranks and the tier's heroic rows (health, melee per 2.0 s swing)
TIER_BY_RANK = {0: ("normal", 12_000, 200), 1: ("elite", 37_000, 550), 2: ("rare", 74_000, 900),
                4: ("rare", 74_000, 900)}


def _load_common():
    """source/npcs/gnomeregan/_common.py as a module (the dungeon files never import the npc packages)."""
    spec = importlib.util.spec_from_file_location("gn_common_for_heroic_test", COMMON_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _own_heroic_loot() -> bool:
    """gnomeregan.py's `_HEROIC_BOSS_OWN_LOOT` (turned on by the loot WP when it declares the heroic groups)."""
    m = re.search(r"^_HEROIC_BOSS_OWN_LOOT\s*=\s*(True|False)\s*$", GN_FILE.read_text(encoding="utf-8"), re.M)
    return bool(m) and m.group(1) == "True"


OWN_LOOT = _own_heroic_loot()


def _source_table(name: str) -> dict:
    """A module-level literal dict of gnomeregan.py (`_HEROIC_ID`)."""
    text = GN_FILE.read_text(encoding="utf-8")
    found = re.search(rf"^{name} = (\{{.*?^\}}|\{{[^\n]*\}})", text, re.M | re.S)
    assert found, name
    return ast.literal_eval(found[1])


def _kit_declared() -> set[int]:
    """The entries source/npcs/gnomeregan/*.py declares with creature_template(<entry>, ...) or a private helper taking
    the entry first (a literal or a module constant), outside docstrings and comments."""
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
    return found & set(range(301105, 301200))  # spell helpers take a 6-digit id first too


def _gn_entry(root: Path | None = None) -> tuple[dict, object]:
    reg = registry.load_class_package((root or TOOL_ROOT / "source") / "world" / "dungeons", ids_cfg=IDS)
    return {e["map_id"]: e for e in reg.dungeons}[MAP_ID], reg


def _fixture(root: Path, *, kit_text: dict[str, str] | None = None) -> Path:
    """A copy of the dungeon file beside a fake npc package (so `_KIT_NPCS` points into `root`)."""
    (root / "world" / "dungeons").mkdir(parents=True)
    (root / "npcs" / "gnomeregan").mkdir(parents=True)
    (root / "world" / "dungeons" / "gnomeregan.py").write_text(GN_FILE.read_text())
    for name, text in (kit_text or {}).items():
        (root / "npcs" / "gnomeregan" / name).write_text(text)
    return root


def _header_health() -> dict[str, tuple[int, int]]:
    """Each `NH<std::uint32_t> constexpr kName{ normal, heroic };` of the header's Health namespace."""
    text = HEADER.read_text(encoding="utf-8")
    block = re.search(r"namespace Health\b(.*?)\n    \}", text, re.S)
    assert block, "namespace Health"
    return {m[1]: (int(m[2]), int(m[3]))
            for m in re.finditer(r"NH<std::uint32_t> constexpr (k\w+)\{\s*(\d+),\s*(\d+)\s*\}", block[1])}


def _header_constant(name: str) -> int:
    m = re.search(rf"std::uint32_t constexpr {name}\s*=\s*(\d+);", HEADER.read_text(encoding="utf-8"))
    assert m, name
    return int(m[1])


def _swing(solved) -> float:
    """The average melee hit at a 2.0 s swing (the tier's unit)."""
    return (solved.min_damage + solved.max_damage) / 2 * 2000 / solved.swing_ms


class DeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # taken right before the declaration loads: a boss WP may land its files at any time (the other WPs run in
        # this worktree), and both must see the same set
        cls.declared = _kit_declared()
        cls.entry, cls.reg = _gn_entry()
        cls.heroic = cls.entry["heroic"]

    def test_the_ids_are_the_next_of_their_blocks_after_zul_farrak(self):
        self.assertEqual((self.heroic["map_difficulty_id"], self.heroic["access_id"]), (1009, 131))
        self.assertEqual(self.heroic["encounter_ids"], HEROIC_ENCOUNTER_IDS)
        self.assertEqual(self.heroic["min_level"], 60)

    def test_the_heroic_row_is_a_five_player_row_not_flex(self):
        self.assertEqual(self.heroic["max_players"], 5)
        md = {r["ID"]: r for r in self.reg.map_difficulties}[1009]
        self.assertEqual((md["MapID"], md["Difficulty"], md["RaidDuration"], md["MaxPlayers"]), (MAP_ID, 1, 86400, 5))
        self.assertEqual(md["Message_Lang_enUS"], "Heroic Difficulty requires you to be level 60.")
        self.assertEqual(md["Difficultystring"], "DUNGEON_DIFFICULTY_5PLAYER_HEROIC")
        access = {r["id"]: r for r in self.reg.dungeon_access}[131]
        self.assertEqual((access["map_id"], access["difficulty"], access["min_level"]), (MAP_ID, 1, 60))

    def test_spawns_go_to_heroic_and_only_the_exile_stays_normal_only(self):
        self.assertTrue(self.heroic["spawn_mask"])
        self.assertFalse(self.heroic["event_spawns"])
        self.assertEqual(self.heroic["normal_only_creatures"], (NORMAL_ONLY,))

    def test_two_encounters_are_declared_in_kill_order(self):
        decls = {d["id"]: d for d in self.reg.encounter_declarations if d["id"] in ENCOUNTERS}
        self.assertEqual(sorted(decls), sorted(DECLARED_ENCOUNTERS))
        # Grubbis's row 379 becomes Techbot's: the bit (2) and the OrderIndex (2000) stay stock
        self.assertEqual((decls[379]["kind"], decls[379]["name"], decls[379]["credit"]), ("repoint", "Techbot",
                                                                                           (0, 301105)))
        self.assertIsNone(decls[379]["bit"])
        self.assertIsNone(decls[379]["order_index"])
        # the Alert System: bit 0 (free on map 90), OrderIndex 3500 between Electrocutioner and Pummeler
        self.assertEqual(
            {k: decls[1107][k] for k in ("kind", "map_id", "difficulty", "order_index", "bit", "name", "credit")},
            {"kind": "new", "map_id": MAP_ID, "difficulty": 0, "order_index": 3500, "bit": 0,
             "name": "The Mobile Alert System", "credit": (0, 301110)})
        self.assertEqual({d["id"] for d in self.reg.encounter_declarations if d.get("map_id") == MAP_ID}, {1107})

    def test_roles_extras_and_skips(self):
        by_entry = {c["entry"]: c for c in self.entry["creatures"]}
        for entry in (6229, 6235, 7079, 7800, 301105, 301110):
            self.assertEqual(by_entry[entry]["role"], "boss", entry)
        self.assertEqual(self.entry["skip"], SKIPPED)
        for entry in NPC_ENTRIES:
            self.assertEqual(by_entry[entry]["role"], "npc", entry)
        for extra in KIT_EXTRA:
            self.assertEqual(by_entry[extra]["source"], "extra", extra)
            self.assertEqual(by_entry[extra]["role"], "boss" if extra in (301105, 301110) else "trash", extra)
        for extra in set(KIT_EXTRA) - {301105, 301110}:
            self.assertTrue(by_entry[extra]["summoned_by"], extra)  # a summon: no spawns, free text names who
            self.assertEqual(by_entry[extra]["spawns"], 0, extra)
        # the two new bosses spawn from the S0 rev (guids 3011050 and 3011100)
        self.assertEqual((by_entry[301105]["spawns"], by_entry[301110]["spawns"]), (1, 1))
        # the quests WP's exile: an extra npc line (the End NPCs and its hand spawns), normal only
        self.assertEqual((by_entry[NORMAL_ONLY]["role"], by_entry[NORMAL_ONLY]["source"]), ("npc", "extra"))
        # the Ambassador and the stock adds stay generated trash
        self.assertEqual((by_entry[AMBASSADOR]["role"], by_entry[AMBASSADOR]["source"]), ("trash", "extracted"))

    def test_the_boss_overrides_are_the_headers_heroic_health_and_the_normal_rows_columns(self):
        common = _load_common()
        overrides = {entry: dict(pairs) for entry, pairs in self.heroic["overrides"]}
        expected_columns = {"CreatureImmunitiesId": common.IMMUNITY_BOSS_STUN, "flags_extra": common.BOSS_FLAGS_EXTRA,
                            "detection_range": common.BOSS_DETECTION_RANGE}
        self.assertEqual((common.IMMUNITY_BOSS_STUN, common.BOSS_FLAGS_EXTRA, common.BOSS_DETECTION_RANGE),
                         (1972, 0x06000001, 12.0))
        header = _header_health()
        for entry, (name, _base) in BOSSES.items():
            with self.subTest(entry=entry):
                self.assertEqual(overrides[entry]["health"], header[name][1])
                expected = dict(expected_columns)
                if OWN_LOOT and entry in HEROIC_LOOT_BOSSES:
                    expected["lootid"] = _source_table("_HEROIC_ID")[entry]
                self.assertEqual(dict(overrides[entry]["columns"]), expected)
                self.assertNotIn("melee", overrides[entry])  # the tier's 2,500 a swing
                self.assertNotIn("tier", overrides[entry])

    def test_the_header_health_table_has_no_unpinned_unit(self):
        header = _header_health()
        self.assertEqual(set(header), HEADER_NAMES)
        self.assertEqual(_header_constant("kWholeWorkshop"), 800_000)  # the hard mode: by script, not a template

    def test_the_ambassador_is_the_headers_row_on_both_difficulties(self):
        header = _header_health()["kDarkIronAmbassador"]
        overrides = {entry: dict(pairs) for entry, pairs in self.heroic["overrides"]}
        expected = {"health": header[1]}
        if OWN_LOOT:
            expected["columns"] = {"lootid": _source_table("_HEROIC_ID")[AMBASSADOR]}
        got = {k: (dict(v) if k == "columns" else v) for k, v in overrides[AMBASSADOR].items()}
        self.assertEqual(got, expected)
        self.assertEqual(header, (42_017, 260_000))
        # normal: HealthModifier 57.4 on the level 28 paladin base 732, DamageModifier 3.0 (stock 7.5)
        text = (KIT_DIR / "dark_iron_ambassador.py").read_text(encoding="utf-8")
        self.assertIn("creature_template_columns(6228, HealthModifier=57.4, DamageModifier=3.0)", text)
        self.assertEqual(math.ceil(AMBASSADOR_BASE_28 * heroic_templates.f32(57.4)), header[0])

    def test_the_predicted_ids_in_the_source_are_the_lock_mint_order(self):
        ids = _source_table("_HEROIC_ID")
        self.assertEqual(sorted(ids), sorted(ids, key=ids.get))  # ids follow the entry order
        self.assertEqual(min(ids.values()), FIRST_HEROIC_ID)
        self.assertEqual(sorted(ids.values()), list(range(FIRST_HEROIC_ID, FIRST_HEROIC_ID + len(ids))))
        self.assertEqual(sum(1 for e in ids if e < 300000), STOCK_SET_COUNT)
        self.assertEqual(sorted(e for e in ids if e >= 300000), sorted(KIT_EXTRA))
        # the npc package's copy (source/npcs/gnomeregan/_common.py, read by every full row's difficulty_entry_1)
        self.assertEqual(_load_common().HEROIC_PREDICTED, {e: ids[e] for e in KIT_EXTRA})

    def test_the_kit_overrides_follow_their_declared_templates(self):
        overrides = {entry: dict(pairs) for entry, pairs in self.heroic["overrides"]}
        header = _header_health()
        for entry, name in KIT_HEADER.items():
            self.assertEqual(KIT_HEALTH[entry], header[name][1], entry)  # the table pins the header
            self.assertEqual(entry in overrides, entry in self.declared, entry)
            if entry in overrides:
                self.assertEqual(overrides[entry], {"health": KIT_HEALTH[entry]})
        new_bosses = {301105, 301110}  # S0 declared both: their override (the boss health) is unconditional
        self.assertEqual(sorted(e for e in overrides if e >= 300000),
                         sorted(new_bosses | {e for e in KIT_HEALTH if e in self.declared}))

    def test_the_text_scan_agrees_with_the_real_npc_package(self):
        """Whatever creature_template() rows the real package declares, the scan sees (a miss would leave a declared
        unit on the tier: R1-KIT M-4 of the Scarlet Monastery build)."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "world" / "dungeons").mkdir(parents=True)
            shutil.copytree(KIT_DIR, root / "npcs" / "gnomeregan", ignore=shutil.ignore_patterns("__pycache__"))
            (root / "world" / "dungeons" / "gnomeregan.py").write_text(GN_FILE.read_text(encoding="utf-8"))
            entry, _reg = _gn_entry(root)
        overrides = {e: dict(p) for e, p in entry["heroic"]["overrides"]}
        for unit in KIT_HEALTH:
            self.assertEqual(unit in overrides, unit in self.declared, unit)

    def test_a_kit_override_appears_when_a_source_file_declares_the_template(self):
        cases = {
            "literal": ("g = creature_template(301106, 'Dupe Bug', **{})\n", True),
            "constant": ("BUG = 301106\ng = creature_template(BUG, 'Dupe Bug')\n", True),
            "helper": ("def _unit(entry, name):\n    return creature_template(entry, name)\n"
                       "g = _unit(301106, 'Dupe Bug')\n", True),
            "docstring": ('"""creature_template(301106, ...) is named here and is not a declaration."""\n', False),
            "comment": ("# creature_template(301106, 'Dupe Bug')\n", False),
            "columns edit": ("creature_template_columns(301106, x=1)\n", False),
            "other unit": ("w = creature_template(301107, 'Lag Echo')\n", False),
        }
        for label, (text, expected) in cases.items():
            with self.subTest(label), tempfile.TemporaryDirectory() as d:
                root = _fixture(Path(d), kit_text={"adds.py": text})
                entry, _reg = _gn_entry(root)
            overrides = {e: dict(p) for e, p in entry["heroic"]["overrides"]}
            self.assertEqual(301106 in overrides, expected)
            if expected:
                self.assertEqual(overrides[301106]["health"], KIT_HEALTH[301106])

    def test_every_override_names_a_listed_creature(self):
        with tempfile.TemporaryDirectory() as d:
            kit = "\n".join(f"u{entry} = creature_template({entry}, 'x')" for entry in KIT_HEALTH) + "\n"
            root = _fixture(Path(d), kit_text={"all.py": kit})
            entry, _reg = _gn_entry(root)
        listed = {c["entry"] for c in entry["creatures"]}
        overrides = {e for e, _p in entry["heroic"]["overrides"]}
        for unit in overrides:
            self.assertIn(unit, listed)
        self.assertTrue(set(KIT_HEALTH) <= overrides)

    def test_the_finder_entries_and_the_conf_lines(self):
        heroic_text = LFG_HEROIC_FILE.read_text(encoding="utf-8")
        for heroic_id, normal in ((FINDER_HEROIC_14, FINDER_14), (FINDER_HEROIC_320, FINDER_320)):
            self.assertIn(f"lfg_heroic({heroic_id}, normal={normal}, group=CLASSIC_HEROIC)", heroic_text)
        sections = LFG_SECTIONS_FILE.read_text(encoding="utf-8")
        self.assertIn("lfg_override(14, last_encounter=380)", sections)
        self.assertIn('320, "Gnomeregan - The Workshop", map_id=90, like=14, min_level=23, max_level=33, '
                      "target_level=27,\n    last_encounter=382, position=(-736.51, 2.71, -249.99, 3.14),", sections)
        gate = re.search(r'^ContentGate\.Open\.Instances\.EasternKingdoms\s*=\s*"([^"]*)"',
                         CONTENT_GATE_DIST.read_text(), re.M)
        self.assertIsNotNone(gate)
        self.assertIn("90:N,H", gate[1].split())
        self.assertNotIn("90:N", gate[1].split())  # the old, normal-only token is gone
        self.assertIn("189:N,H", gate[1].split())  # Scarlet Monastery's stays
        bm = re.search(r'^BossMechanics\.ReferenceHealth\.MapLevels\s*=\s*"([^"]*)"', BM_CONF_DIST.read_text(), re.M)
        self.assertIsNotNone(bm)
        self.assertTrue({"90:28", "90h:60", "209:46", "209h:60"} <= set(bm[1].split()))
        dd = re.search(r'^DungeonDifficulties\.Heroic\.Maps\s*=\s*"([^"]*)"', DD_CONF_DIST.read_text(), re.M)
        self.assertIsNotNone(dd)
        self.assertIn("90", dd[1].split())
        self.assertIn("209", dd[1].split())

    def test_the_header_names_the_same_encounters_and_finder_entries(self):
        """GnomereganRework.h (slot = DungeonEncounter bit): the slots' normal and heroic encounter ids and the Finder
        table (14 / 321 and 320 / 322)."""
        text = HEADER.read_text(encoding="utf-8")

        def table(name: str) -> list[int]:
            body = re.search(rf"{name}\{{ \{{\s*([\d,\s]+?)\s*\}} \}};", text)
            assert body, name
            return [int(v) for v in body[1].replace("\n", " ").split(",") if v.strip()]

        by_bit = {bit: normal for normal, (_h, _o, bit, _n, _c) in ENCOUNTERS.items()}
        heroic_by_bit = {bit: heroic for _n, (heroic, _o, bit, _name, _c) in ENCOUNTERS.items()}
        self.assertEqual(table("kEncounterNormal"), [by_bit[bit] for bit in range(6)])
        self.assertEqual(table("kEncounterHeroic"), [heroic_by_bit[bit] for bit in range(6)])
        sections = re.findall(r"\{ ([12]), \"[^\"]+\", (\d+), (\d+), kSection", text)
        self.assertEqual(sections, [("1", "14", "321"), ("2", "320", "322")])

    def test_the_bm_pins_are_the_interpolated_reference_rows(self):
        """90:28 reads rows 20 and 35 of ReferenceHealth.Rows (1,694 / 1,707); 90h:60 the heroic row (4,120 / 4,110)."""
        text = BM_CONF_DIST.read_text()
        rows = re.search(r'^BossMechanics\.ReferenceHealth\.Rows\s*=\s*"([^"]*)"', text, re.M)[1].split()
        table = {r.split(":")[0]: tuple(int(v) for v in r.split(":")[1:]) for r in rows}
        (lo_n, lo_t), (hi_n, hi_t) = table["20"], table["35"]
        t = (28 - 20) / (35 - 20)
        self.assertEqual((round(lo_n + (hi_n - lo_n) * t), round(lo_t + (hi_t - lo_t) * t)),
                         (_header_constant_ref("kReferenceNormal")))
        self.assertEqual(table["60h"], _header_constant_ref("kReferenceHeroic"))


def _header_constant_ref(name: str) -> tuple[int, int]:
    m = re.search(rf"ReferenceRow constexpr {name}\{{\s*(\d+),\s*(\d+)\s*\}};", HEADER.read_text(encoding="utf-8"))
    assert m, name
    return int(m[1]), int(m[2])


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
            # The Gnomeregan boss package declares its kit units (source/npcs/gnomeregan/) as they land
            kit = registry.load_class_package(
                KIT_DIR, ids_cfg=IDS, existing_creature_rows=existing,
                creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
                creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS, live_data={},
            )
            for key in ("creature_templates", "creature_template_models", "creature_template_edits"):
                cls.dsl[key] = cls.dsl.get(key, []) + list(getattr(kit, key))
            # only Gnomeregan's heroic and encounters are expanded here (the other dungeons have their own tests)
            cls.dsl["dungeons"] = [e if e["map_id"] == MAP_ID else dict(e, heroic=None) for e in cls.dsl["dungeons"]]
            cls.dsl["encounter_declarations"] = [d for d in cls.dsl["encounter_declarations"]
                                                 if d["id"] in DECLARED_ENCOUNTERS]
            cls.index = spell_tables.load_spell_table_index()
            cls.encounters = dungeon_encounters.expand(cls.dsl, lambda: dungeon_encounters.load_inputs(
                cls.index, {*existing, *(int(r["entry"]) for r in cls.dsl.get("creature_templates", []))},
                spell_ids=set(), ids_cfg=IDS))
            cls.live = dungeon_heroic.load_live_world(existing, cls.index)
            cls.out = dungeon_heroic.expand(cls.dsl, lambda: cls.live, ids_cfg=IDS)
            cls.out_live_spawns = {
                table: {int(guid): row for guid, row in cls.live.spawns.get(table, {}).items()
                        if int(row.get("map") or 0) == MAP_ID} for table in spawn_state.SPAWN_TABLES
            }
            cls.existing = existing
            # generate.py's next step: the finder (source/world/lfg_classic_*.py) with only this map's entries
            heroic = registry.load_class_file(LFG_HEROIC_FILE, ids_cfg=IDS)
            sections = registry.load_class_file(LFG_SECTIONS_FILE, ids_cfg=IDS)
            cls.dsl["lfg_group_declarations"] = list(heroic.lfg_group_declarations)
            mine = {FINDER_14, FINDER_320, FINDER_HEROIC_14, FINDER_HEROIC_320}
            cls.dsl["lfg_dungeon_declarations"] = [
                d for d in (*heroic.lfg_dungeon_declarations, *sections.lfg_dungeon_declarations)
                if d["kind"] == "random" or d["id"] in mine
            ]
            cls.lfg_inputs = lfg_dungeons.load_inputs(cls.index)
            cls.lfg_out = lfg_dungeons.expand(cls.dsl, lambda: cls.lfg_inputs)
        finally:
            sqlcorpus.deactivate()
        cls.entry = next(e for e in cls.dsl["dungeons"] if e["map_id"] == MAP_ID)
        cls.reports = {r.normal: r for r in cls.out.heroic_reports}
        cls.declared = _kit_declared()

    def _heroic_link_errors(self) -> list[str]:
        """The ERRORs that ask a declared kit unit to name its heroic entry in difficulty_entry_1
        (lib/dungeon_heroic.py: 'declares the full row - set difficulty_entry_1 there'). A boss WP declares its units
        before the others have landed and the minted id shifts until they have: `test_declared_kit_units_carry_their_
        heroic_entry` checks them, not this."""
        return [e for e in self.out.errors if "declares the full row - set difficulty_entry_1 there" in e]

    def test_it_is_clean(self):
        self.assertEqual((self.encounters.errors, self.encounters.warnings), ([], []))
        self.assertEqual([e for e in self.out.errors if e not in self._heroic_link_errors()], [])
        self.assertEqual(self.out.warnings, [])
        self.assertEqual((self.lfg_out.errors, self.lfg_out.warnings), ([], []))

    def test_declared_kit_units_carry_their_heroic_entry(self):
        """A kit unit that names its heroic id in its own `creature_template()` row names the one of the predicted
        table once every lower-numbered unit is declared too (a missing lower unit shifts the later ones down). A row
        that names none yet is the run's own ERROR, which the boss WP clears with the table in the report."""
        predicted = _source_table("_HEROIC_ID")
        rows = {int(r["entry"]): r for r in self.dsl["creature_templates"] if not r.get(dungeon_heroic.DERIVED)}
        for entry in KIT_EXTRA:
            if entry not in rows or not int(rows[entry].get("difficulty_entry_1") or 0):
                continue
            with self.subTest(entry=entry):
                if all(lower in rows for lower in KIT_EXTRA if lower < entry):
                    self.assertEqual(int(rows[entry]["difficulty_entry_1"]), predicted[entry])
                else:
                    self.assertLessEqual(int(rows[entry]["difficulty_entry_1"]), predicted[entry])
        if set(KIT_EXTRA) <= set(rows):
            self.assertEqual(self._heroic_link_errors(), [])

    def test_six_heroic_encounters_in_the_kill_order_with_their_credit(self):
        rows = {r["ID"]: r for r in self.dsl["dungeon_encounters"] if r["Difficulty"] == 1}
        self.assertEqual(sorted(rows), list(HEROIC_ENCOUNTER_IDS))
        normal = {r["ID"]: r for r in self.dsl["dungeon_encounters"] if r["Difficulty"] == 0}
        self.assertEqual(sorted(normal), sorted(DECLARED_ENCOUNTERS))  # the declared rows only (stock is not here)
        for normal_id, (heroic_id, order, bit, name, _credit) in ENCOUNTERS.items():
            with self.subTest(encounter=normal_id):
                row = rows[heroic_id]
                self.assertEqual((row["MapID"], row["Difficulty"]), (MAP_ID, 1))
                self.assertEqual((row["Bit"], row["OrderIndex"], row["Name_Lang_enUS"]), (bit, order, name))
                if normal_id in normal:
                    source_row = normal[normal_id]
                    self.assertEqual((row["Bit"], row["OrderIndex"], row["Name_Lang_enUS"]),
                                     (source_row["Bit"], source_row["OrderIndex"], source_row["Name_Lang_enUS"]))
        self.assertEqual([r["OrderIndex"] for _i, r in sorted(rows.items())],
                         sorted(r["OrderIndex"] for r in rows.values()))  # ids in OrderIndex order
        self.assertEqual(sorted(r["Bit"] for r in rows.values()), list(range(6)))  # bit 0 is free on map 90: the Alert

    def test_the_credits_all_by_creature(self):
        by_entry = {r["entry"]: r for r in self.dsl["instance_encounters"]}
        for normal_id, (heroic_id, _order, _bit, _name, credit) in ENCOUNTERS.items():
            for entry in (normal_id, heroic_id):
                if entry in by_entry:  # the stock rows 378, 380-382 come from the replay (generate.py's full run)
                    self.assertEqual((int(by_entry[entry]["creditType"]), int(by_entry[entry]["creditEntry"])),
                                     credit, entry)  # a heroic body credits the NORMAL entry
        for entry in (379, 1107, 1108, 1111):
            self.assertIn(entry, by_entry)
        self.assertEqual({int(by_entry[e]["creditEntry"]) for e in (379, 1107)}, {301105, 301110})

    def test_the_finder_ends_14_at_electrocutioner_and_320_at_thermaplugg(self):
        by_entry = {r["entry"]: r for r in self.dsl["instance_encounters"]}
        edits = {r["entry"]: int(r["lastEncounterDungeon"]) for r in self.dsl["instance_encounters"]
                 if r.get(lfg_dungeons.LINK)}
        self.assertEqual(edits, FINDER_LINKS)  # 380 takes 14, 382 (stock: 14) takes 320: nothing else is edited
        self.assertEqual({e: int(by_entry[e]["lastEncounterDungeon"]) for e in HEROIC_LINKS | {}}, HEROIC_LINKS)
        self.assertEqual({e: int(by_entry[e]["lastEncounterDungeon"]) for e in HEROIC_ENCOUNTER_IDS},
                         {e: HEROIC_LINKS.get(e, 0) for e in HEROIC_ENCOUNTER_IDS})
        self.assertEqual({e: int(by_entry[e]["lastEncounterDungeon"]) for e in (379, 1107)}, {379: 0, 1107: 0})

    def test_the_creature_set(self):
        mapping = self.entry["heroic_entries"]
        ids = _source_table("_HEROIC_ID")
        self.assertEqual({e for e in mapping if e < 300000}, {e for e in ids if e < 300000})
        for out in (*SKIPPED, *NPC_ENTRIES, 13876, NORMAL_ONLY):
            self.assertNotIn(out, mapping)
        for boss in (*BOSSES, AMBASSADOR):
            if boss < 300000 or boss in self.declared:
                self.assertIn(boss, mapping)
        declared_rows = {int(r["entry"]) for r in self.dsl["creature_templates"] if not r.get(dungeon_heroic.DERIVED)}
        for unit in KIT_EXTRA:
            self.assertEqual(unit in mapping, unit in declared_rows, unit)
        for no_heroic in (301107, 301108, 301113, 301115, 301125, 301126, 301127, 301130, 301132, 301135, 301136,
                          301137, 301138):
            self.assertNotIn(no_heroic, mapping)
        block = IDS["creature_heroic"]
        locked = heroic_templates.parse_lock(heroic_templates.LOCK_PATH.read_text()).pairs
        for normal, heroic in mapping.items():
            self.assertTrue(block["start"] <= heroic <= block["end"], (normal, heroic))
        self.assertEqual(len(set(mapping.values())), len(mapping))
        self.assertFalse(set(mapping.values()) & {h for n, h in locked.items() if n not in mapping})

    def test_the_predicted_lock_lines(self):
        """The ids the first write run mints: normal-entry order from 310543 (32 lines for the stock set), the kit
        units after them in entry order, each unit's creature_template naming its id in difficulty_entry_1."""
        mapping = self.entry["heroic_entries"]
        ids = _source_table("_HEROIC_ID")
        locked = heroic_templates.parse_lock(heroic_templates.LOCK_PATH.read_text()).pairs
        fresh = {n: h for n, h in mapping.items() if n not in locked}
        if set(fresh) != set(mapping):  # after the write run the lines are committed: the same numbers
            fresh = mapping
        stock = {n: h for n, h in fresh.items() if n < 300000}
        self.assertEqual(stock, {n: h for n, h in ids.items() if n < 300000})
        self.assertEqual(len(stock), STOCK_SET_COUNT)
        if OWN_LOOT:
            for boss in HEROIC_LOOT_BOSSES:
                if boss in fresh:
                    self.assertEqual(fresh[boss], ids[boss], boss)
        kit = sorted(e for e in fresh if e >= 300000)
        for rank, entry in enumerate(kit):  # consecutive after the stock set; a missing lower unit shifts down only
            self.assertEqual(fresh[entry], FIRST_HEROIC_ID + STOCK_SET_COUNT + rank, entry)
            self.assertLessEqual(fresh[entry], ids[entry], entry)
        if set(KIT_EXTRA) <= set(fresh):
            for entry in KIT_EXTRA:
                self.assertEqual(fresh[entry], ids[entry], entry)
        # nothing of this map is committed yet: the run appends one line per template (or none, after the write run)
        self.assertIn(len(self.out.lock_appended), (0, len(mapping)))

    def test_bosses(self):
        common = _load_common()
        rows = {int(r["entry"]): r for r in self.dsl["creature_templates"] if r.get(dungeon_heroic.DERIVED)}
        heroic_entry = self.entry["heroic_entries"]
        header = _header_health()
        for boss, (name, base) in BOSSES.items():
            if boss not in heroic_entry:  # a boss file that has not landed its row yet
                continue
            with self.subTest(boss=boss):
                report = self.reports[boss]
                self.assertEqual(report.role, "boss")
                self.assertAlmostEqual(report.solved.health, header[name][1], delta=1)
                self.assertEqual(report.solved.tier_row, "boss")
                row = rows[heroic_entry[boss]]
                self.assertEqual((row["minlevel"], row["maxlevel"], row["exp"]), (60, 60, 0))
                self.assertAlmostEqual(float(row["HealthModifier"]) * base, header[name][1], delta=1.0, msg=boss)
                self.assertEqual(int(row["CreatureImmunitiesId"]), common.IMMUNITY_BOSS_STUN)
                self.assertEqual(int(row["flags_extra"]), common.BOSS_FLAGS_EXTRA)  # bind + both assist flags
                self.assertEqual(int(row["flags_extra"]) & 1, 1)  # INSTANCE_BIND
                self.assertEqual(float(row["detection_range"]), common.BOSS_DETECTION_RANGE)
                self.assertEqual((row["AIName"], row["ScriptName"]), ("", ""))  # the normal entry's script runs
                self.assertEqual(int(row["KillCredit1"]), 0)
                if OWN_LOOT and boss in HEROIC_LOOT_BOSSES:
                    self.assertEqual(int(row["lootid"]), _source_table("_HEROIC_ID")[boss])

    def test_the_heroic_fallout_keeps_only_the_frost_immunity_aura(self):
        """D2's rev sets 7079's addon auras to 7940 (9460 dropped); the heroic copy's addon row is this run's copy of
        that replayed row, the only source (INT dedupe: D2's rev no longer joins on difficulty_entry_1)."""
        heroic = self.entry["heroic_entries"][7079]
        addons = {int(r["entry"]): r for r in self.dsl["heroic_template_addons"]}
        self.assertEqual(str(addons[heroic]["auras"]), "7940")

    def test_the_four_stock_bosses_and_both_new_ones_are_in_the_set(self):
        # S0 declared 301105 and 301110 (and spawns them): they are in the set from the start
        for boss in (6229, 6235, 7079, 7800, 301105, 301110):
            self.assertIn(boss, self.entry["heroic_entries"], boss)

    def test_the_boss_melee_is_the_tiers_2500_a_swing(self):
        for boss in BOSSES:
            if boss not in self.reports:
                continue
            self.assertAlmostEqual(_swing(self.reports[boss].solved), TIER_MELEE, delta=10, msg=boss)

    def test_the_ambassador(self):
        report = self.reports[AMBASSADOR]
        header = _header_health()["kDarkIronAmbassador"]
        self.assertEqual((report.role, report.solved.tier_row, report.rank, report.unit_class),
                         ("trash", "rare", 2, 2))
        self.assertAlmostEqual(report.solved.health, header[1], delta=1)
        self.assertAlmostEqual(_swing(report.solved), RARE_MELEE, delta=9)
        row = {int(r["entry"]): r for r in self.dsl["creature_templates"]
               if r.get(dungeon_heroic.DERIVED)}[self.entry["heroic_entries"][AMBASSADOR]]
        self.assertEqual((row["minlevel"], row["maxlevel"]), (60, 60))
        self.assertEqual(int(row["flags_extra"]) & 1, 0)  # a rare is no boss: no bind
        # the normal edit: only the two columns, from the stock 5 and 7.5
        edit = {int(r["entry"]): r for r in self.dsl["creature_template_edits"]}[AMBASSADOR]
        # (the heroic expansion adds `difficulty_entry_1` to the same edit)
        self.assertEqual(tuple(edit["_update_columns"])[:2], ("HealthModifier", "DamageModifier"))
        self.assertLessEqual(set(edit["_update_columns"]), {"HealthModifier", "DamageModifier", "difficulty_entry_1"})
        self.assertEqual((edit["HealthModifier"], edit["DamageModifier"]), (57.4, 3.0))
        # the stock 5 / 7.5 before the write run; once its rev is pending the replay already reads the new values
        self.assertIn((float(self.existing[AMBASSADOR]["HealthModifier"]),
                       float(self.existing[AMBASSADOR]["DamageModifier"])), {(5.0, 7.5), (57.4, 3.0)})

    def test_the_unscaled_adds(self):
        heroic_entry = self.entry["heroic_entries"]
        rows = {int(r["entry"]): r for r in self.dsl["creature_templates"] if r.get(dungeon_heroic.DERIVED)}
        for entry, health in KIT_HEALTH.items():
            if entry in heroic_entry:
                with self.subTest(entry=entry):
                    self.assertEqual(self.reports[entry].solved.health, health)
                    self.assertEqual((rows[heroic_entry[entry]]["minlevel"], rows[heroic_entry[entry]]["maxlevel"]),
                                     (60, 60))
        self.assertEqual(sorted(e for e in KIT_HEALTH if e in heroic_entry), sorted(e for e in KIT_HEALTH
                                                                                     if e in self.declared))

    def test_the_trash_takes_the_tier_as_it_is(self):
        rows = {int(r["entry"]): r for r in self.dsl["creature_templates"] if r.get(dungeon_heroic.DERIVED)}
        heroic_entry = self.entry["heroic_entries"]
        checked = 0
        for entry, report in self.reports.items():
            if report.override or report.role != "trash":
                continue
            with self.subTest(entry=entry):
                row_name, health, melee = TIER_BY_RANK[report.rank]
                self.assertEqual((report.solved.tier_row, report.solved.health), (row_name, health))
                self.assertAlmostEqual(_swing(report.solved), melee, delta=melee * 0.01)
                row = rows[heroic_entry[entry]]
                self.assertEqual((row["minlevel"], row["maxlevel"]), (60, 60))
                self.assertEqual(int(row["flags_extra"]) & 1, 0)  # no bind on trash
                checked += 1
        self.assertGreaterEqual(checked, 25)  # the 27 stock trash kinds (the Ambassador has its own number)
        for skipped in SKIPPED:
            self.assertNotIn(skipped, self.reports)

    def test_the_stock_normal_rows_only_gain_difficulty_entry_1(self):
        """The bosses' normal rows are edited by creature_template_columns() of the boss files, not here: this
        expansion adds only `difficulty_entry_1` (the engine link) to the stock rows."""
        mapping = self.entry["heroic_entries"]
        stock = {e: h for e, h in mapping.items() if e < 300000}
        edits = [r for r in self.dsl.get("creature_template_edits", [])
                 if int(r["entry"]) in stock and "difficulty_entry_1" in r]
        self.assertEqual({int(r["entry"]): int(r["difficulty_entry_1"]) for r in edits}, stock)

    def test_the_smart_ai_widening_touches_no_script_the_rework_replaces(self):
        """S0's rev drops the SmartAI of the units the rework scripts and of the twelve Faces and Buttons; whatever is
        widened is SmartAI that stays."""
        replaced = {7079, 6235, 6229, 7800, *range(142208, 142220)}
        blocks = [b for b in self.out.smart_blocks if "UPDATE `smart_scripts` " in b]
        widened = {int(g) for b in blocks for g in re.findall(r"`entryorguid` = (\d+)", b)}
        self.assertFalse(widened & replaced, sorted(widened & replaced))

    def test_every_spawn_goes_to_heroic_except_the_event_and_the_exile(self):
        """By guid, not by a note's count: a later hand spawn (the exile, normal only) changes the counts, and after
        the write run there is nothing left to set."""
        events = self.live.event_guids.get("creature", set())
        for table in ("creature", "gameobject"):
            blocks = [b for b in self.out.spawn_blocks if f"UPDATE `{table}` " in b]
            guids = {int(g) for block in blocks for g in re.findall(r"\d+", block.split("`guid` IN (")[1])} \
                if blocks else set()
            for guid, row in self.out_live_spawns[table].items():
                if guid in events or spawn_state.spawn_entry(row) == NORMAL_ONLY:
                    self.assertNotIn(guid, guids, (table, guid))
                    continue
                # set by these blocks or carrying the bit already (the hand spawns of the boss WPs' revs)
                self.assertTrue(guid in guids or spawn_state.spawn_mask(row) & dungeon_heroic.HEROIC_SPAWN_BIT,
                                (table, guid))
        self.assertTrue(self.out_live_spawns["creature"], "no live creature spawn of map 90: the replay is empty")

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
        self.assertEqual((by_id[1009]["MapID"], by_id[1009]["Difficulty"], by_id[1009]["MaxPlayers"]), (MAP_ID, 1, 5))
        self.assertEqual({k: v for k, v in by_id.items() if k < 1000}, {r["ID"]: r for r in base})
        order = [(r["MapID"], r["Difficulty"]) for r in back]
        self.assertEqual(order, sorted(order))
        self.assertEqual(sum(1 for r in back if r["MapID"] == MAP_ID and r["Difficulty"] == 1), 1)

        de_path = state.BASE_DBC_DIR / dbcfmt.DUNGEONENCOUNTER.dbc_filename
        base_de = dbcfile.read_dbc(de_path, dbcfmt.DUNGEONENCOUNTER)
        merged_de = {r["ID"]: r for r in base_de}
        merged_de.update(dungeon_heroic.client_encounter_rows(self.dsl["dungeon_encounters"]))
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / dbcfmt.DUNGEONENCOUNTER.dbc_filename
            path.write_bytes(dbcfile.pack_client_dbc(dbcfmt.DUNGEONENCOUNTER, list(merged_de.values()), base_de))
            back_de = dbcfile.read_dbc(path, dbcfmt.DUNGEONENCOUNTER)
        self.assertEqual(len(back_de), len(base_de) + 6 + 1)  # six heroic copies and the new normal row 1107
        self.assertEqual(sorted(r["ID"] for r in back_de if r["MapID"] == MAP_ID and r["Difficulty"] == 1),
                         list(HEROIC_ENCOUNTER_IDS))
        normal = {r["ID"]: r for r in back_de if r["MapID"] == MAP_ID and r["Difficulty"] == 0}
        self.assertEqual(sorted(normal), sorted(ENCOUNTERS))
        # the client's normal list shows the re-pointed row and the new one, in kill order
        self.assertEqual((normal[379]["Name_Lang_enUS"], normal[1107]["Name_Lang_enUS"]),
                         ("Techbot", "The Mobile Alert System"))
        self.assertEqual([i for i, _r in sorted(normal.items(), key=lambda kv: kv[1]["OrderIndex"])],
                         [379, 378, 380, 1107, 381, 382])
        self.assertEqual({i: normal[i]["Bit"] for i in normal}, {i: ENCOUNTERS[i][2] for i in ENCOUNTERS})

    # --- the Finder -------------------------------------------------------------------------------------------

    def _rows(self):
        return {r["ID"]: r for r in self.dsl["lfg_dungeons"]}

    def _stock(self):
        return {r["ID"]: r for r in dbcfile.read_dbc(state.BASE_DBC_DIR / dbcfmt.LFGDUNGEONS.dbc_filename,
                                                     dbcfmt.LFGDUNGEONS)}

    def test_the_new_section_320(self):
        row, stock = self._rows()[FINDER_320], self._stock()[FINDER_14]
        self.assertEqual(row["Name_Lang_enUS"], "Gnomeregan - The Workshop")
        self.assertEqual((row["TypeID"], row["Difficulty"], row["Group_Id"], row["MapID"], row["Flags"]),
                         (1, 0, 1, MAP_ID, 3))
        self.assertEqual((row["MinLevel"], row["MaxLevel"], row["Target_Level"]), (23, 33, 27))
        self.assertEqual((row["MinLevel"], row["MaxLevel"], row["Target_Level"]),
                         (stock["MinLevel"], stock["MaxLevel"], stock["Target_Level"]))  # the stock row's window
        self.assertEqual(row["TextureFilename"], stock["TextureFilename"])
        self.assertNotIn(FINDER_14, self._rows())  # the stock row stays as it is: only its final boss moves
        position = self.lfg_inputs.positions[FINDER_14]
        self.assertEqual((position["position_x"], position["position_y"], position["position_z"],
                          position["orientation"]), (-332.22, -2.28, -150.86, 2.77))  # the stock start stays
        template = {t["dungeonId"]: t for t in self.dsl["lfg_dungeon_templates"]}[FINDER_320]
        self.assertEqual((template["position_x"], template["position_y"], template["position_z"],
                          template["orientation"]), SECTION_START)

    def test_the_heroic_entries(self):
        stock = self._stock()
        for heroic_id, normal, name in ((FINDER_HEROIC_14, FINDER_14, "Gnomeregan"),
                                        (FINDER_HEROIC_320, FINDER_320, "Gnomeregan - The Workshop")):
            with self.subTest(entry=heroic_id):
                row = self._rows()[heroic_id]
                self.assertEqual(row["Name_Lang_enUS"], name)
                self.assertEqual((row["TypeID"], row["Difficulty"], row["Group_Id"], row["MapID"], row["Flags"]),
                                 (5, 1, 12, MAP_ID, 3))
                self.assertEqual((row["MinLevel"], row["MaxLevel"]), (60, 62))
                self.assertEqual(row["TextureFilename"], stock[FINDER_14]["TextureFilename"])
        # each heroic entry copies its normal row's start
        templates = {t["dungeonId"]: t for t in self.dsl["lfg_dungeon_templates"]}
        for heroic_id, normal in ((FINDER_HEROIC_14, FINDER_14), (FINDER_HEROIC_320, FINDER_320)):
            source_position = templates.get(normal) or self.lfg_inputs.positions[normal]
            self.assertEqual(
                tuple(templates[heroic_id][c] for c in ("position_x", "position_y", "position_z", "orientation")),
                tuple(source_position[c] for c in ("position_x", "position_y", "position_z", "orientation")))

    def test_the_client_lfg_file_gains_the_new_rows_and_random_classic_heroic_draws_them(self):
        base = dbcfile.read_dbc(state.BASE_DBC_DIR / dbcfmt.LFGDUNGEONS.dbc_filename, dbcfmt.LFGDUNGEONS)
        merged = {r["ID"]: r for r in base}
        merged.update(lfg_dungeons.client_dungeon_rows(self.dsl["lfg_dungeons"]))
        new = set(merged) - {r["ID"] for r in base}
        self.assertTrue({FINDER_320, FINDER_HEROIC_14, FINDER_HEROIC_320} <= new)
        pool = {i for i, r in merged.items() if r["Group_Id"] == 12 and r["TypeID"] == 5}
        self.assertTrue({FINDER_HEROIC_14, FINDER_HEROIC_320} <= pool)
        # Random Classic Dungeon (258) draws the new normal row from group 1, with the stock entry 14
        self.assertEqual(merged[FINDER_320]["Group_Id"], merged[FINDER_14]["Group_Id"])


if __name__ == "__main__":
    unittest.main()
