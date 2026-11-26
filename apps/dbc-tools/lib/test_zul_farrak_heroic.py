"""
Zul'Farrak's heroic declaration (Zul'Farrak build, WP-H): source/world/dungeons/zul_farrak.py as generate.py loads it,
the heroic Finder entry 319 of source/world/lfg_classic_heroic.py, and the three conf lines (the content gate's
`209:N,H`, BM's `MapLevels` pins `209:46 209h:60`, DD's `Heroic.Maps` += 209).

Covered: the heroic() arguments (MapDifficulty 1008 with MaxPlayers 5, dungeon_access 130, DungeonEncounter 1099-1106,
spawn masks, no event spawns, the entrance goblin normal-only), the eight re-pointed stock encounters 593-600 (kill
order, bits kept, 598 and 599 re-named and re-pointed to the credit spells 213840 / 213841 of source/npcs/zul_farrak/
instance.py), the roles / skip / extra declarations, the boss overrides against the build spec's numbers (handoff 3.6,
pinned to the header's `Health` table) with the stun immunity set, flags_extra and detection range pinned to the normal
rows' `boss_columns()`, the crew's and the unscaled adds' numbers, the kit units' overrides following their
`creature_template()` declarations (a docstring or comment naming the entry does not count; the text scan agrees with
the real npc package), the predicted heroic ids (`_HEROIC_ID`), and the expansion against the live replay: no ERROR or
WARNING, the eight heroic encounters paired with the stock rows in OrderIndex order and their credits (six by creature,
two by spell, the heroic Ukorz ending Finder entry 319), the creature set and the predicted heroic_ids.lock lines
(310501 on, normal-entry order, the table the boss WPs read), the bosses' INSTANCE_BIND, immunity, assist flags and
detection range, the tier's trash and melee, the spawn masks, the client MapDifficulty.dbc / DungeonEncounter.dbc rows
(the patch-Z merge) and the Finder (one heroic entry).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_zul_farrak_heroic.py
"""

from __future__ import annotations

import ast
import importlib.util
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

ZF_FILE = TOOL_ROOT / "source" / "world" / "dungeons" / "zul_farrak.py"
LFG_HEROIC_FILE = TOOL_ROOT / "source" / "world" / "lfg_classic_heroic.py"
KIT_DIR = TOOL_ROOT / "source" / "npcs" / "zul_farrak"
COMMON_FILE = KIT_DIR / "_common.py"
HEADER = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "ZulFarrak" / "ZulFarrakRework.h"
CONTENT_GATE_DIST = REPO_ROOT / "modules" / "mod-content-gate" / "conf" / "content_gate.conf.dist"
WORKTREES = REPO_ROOT.parent
BM_CONF_DIST = WORKTREES / "boss-mechanics-zf" / "conf" / "mod_boss_mechanics.conf.dist"
DD_CONF_DIST = WORKTREES / "mod-dungeon-difficulties-zf" / "conf" / "mod_dungeon_difficulties.conf.dist"
IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")

# The eight stock encounters in kill order, and the heroic copies in (OrderIndex, Bit, ID) order of the re-pointed
# rows: normal id -> (heroic id, OrderIndex, Bit, name, credit (type, entry)).
ENCOUNTERS = {
    596: (1099, 0, 3, "Theka the Martyr", (0, 7272)),
    595: (1100, 1000, 2, "Antu'sul", (0, 8127)),
    597: (1101, 2000, 4, "Witch Doctor Zum'rah", (0, 7271)),
    598: (1102, 3000, 5, "The Pyramid", (1, 213840)),
    599: (1103, 4000, 6, "Sergeant Bly's Crew", (1, 213841)),
    600: (1104, 5000, 7, "Chief Ukorz Sandscalp", (0, 7267)),
    593: (1105, 6000, 0, "Hydromancer Velratha", (0, 7795)),
    594: (1106, 7000, 1, "Ghaz'rilla", (0, 7273)),
}
HEROIC_ENCOUNTER_IDS = tuple(range(1099, 1107))
CREDIT_SPELLS = (213840, 213841)
FINDER_HEROIC, FINDER_NORMAL = 319, 24
HEROIC_UKORZ = 1104

# Heroic boss health: the header's `Health` table, heroic column (x4/3 of the spec). entry -> (header name, class base
# basehp0 at level 60: warrior 3,052, paladin 2,442, mage 2,136; the engine's health is ceil(base x HealthModifier))
BOSSES = {
    7272: ("kTheka", 3_052), 8127: ("kAntusul", 2_442), 7271: ("kZumrah", 2_442), 7274: ("kExecutioner", 3_052),
    7275: ("kSezzziz", 2_442), 7796: ("kNekrum", 3_052), 7267: ("kUkorz", 3_052), 7797: ("kRuuzlu", 3_052),
    7795: ("kVelratha", 2_136), 7273: ("kGahzrilla", 3_052),
}
# _crew()'s columns on every heroic crew copy: CAN_ASSIST (7 #17 A; R-1-LOOT m-3 moved it from rev_crew) and no loot or
# money on the bodies (7 #19 A, R-1-LOOT M-1).
CREW_COLUMNS = {"type_flags": 4096, "lootid": 0, "mingold": 0, "maxgold": 0}
CREW = {7604: ("kBly", 1_250), 7605: ("kRaven", 800), 7606: ("kOro", 400), 7607: (None, 400), 7608: ("kMurta", 400)}
WEEGLI_HEALTH = 55_000  # kWeegliPoolAlly
TIER_MELEE = 2_500
BOSS_MELEE = {7275: 1_250, 7796: 1_250, 7267: 1_250, 7797: 1_250}  # the pairs: half of the tier's swing
# stock adds with their own heroic numbers (handoff 3.6 "Unscaled", 7 #44 A)
ADD_HEALTH = {8156: 15_000, 7786: 1_526, 7787: 4_000, 7788: 4_000, 7785: 305}
ADD_COLUMNS = {8156: {"type": 1}}  # the Servant is a beast (D2)
# the kit units that fight on heroic: entry -> heroic health, applied once a source file declares the template
KIT_HEALTH = {301015: 9_000, 301016: 9_000, 301017: 9_000, 301031: 40_000}
KIT_EXTRA = (7276, 7286, 7787, 7788, 301015, 301016, 301017, 301031)
NORMAL_ONLY_GOBLIN = 301090
SKIPPED = (15578,)  # Elder Wildmane: event only
CREW_ENTRIES = tuple(CREW)
ROLE_BOSS = (*BOSSES, *CREW_ENTRIES)

# The predicted heroic ids: the write run mints in normal-entry order from 310501: the stock set (38 lines: the
# extraction's 35 creatures bar Elder Wildmane, plus 7276, 7286, 7787 and 7788) and the declared kit units after it, in
# entry order.
FIRST_HEROIC_ID = 310501
STOCK_SET_COUNT = 38
HEROIC_LOOT_BOSSES = (7267, 7271, 7272, 7273, 7275, 8127)
TRASH = (5648, 5649, 5650, 6017, 6066, 7246, 7247, 7268, 7269, 7276, 7286, 8095, 8120, 8130, 8179, 10080, 10081,
         10082)



def _load_common():
    """source/npcs/zul_farrak/_common.py as a module (the dungeon files never import the npc packages)."""
    spec = importlib.util.spec_from_file_location("zf_common_for_heroic_test", COMMON_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _own_heroic_loot() -> bool:
    """zul_farrak.py's `_HEROIC_BOSS_OWN_LOOT` (turned on by the loot WP when it declares the heroic groups)."""
    m = re.search(r"^_HEROIC_BOSS_OWN_LOOT\s*=\s*(True|False)\s*$", ZF_FILE.read_text(encoding="utf-8"), re.M)
    return bool(m) and m.group(1) == "True"


OWN_LOOT = _own_heroic_loot()


def _source_table(name: str) -> dict:
    """A module-level literal dict of zul_farrak.py (`_HEROIC_ID`)."""
    text = ZF_FILE.read_text(encoding="utf-8")
    found = re.search(rf"^{name} = (\{{.*?^\}}|\{{[^\n]*\}})", text, re.M | re.S)
    assert found, name
    return ast.literal_eval(found[1])


def _kit_declared() -> set[int]:
    """The entries source/npcs/zul_farrak/*.py declares with creature_template(<entry>, ...) or a private helper taking
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
    return found & set(range(301005, 301100))  # spell helpers take a 6-digit id first too


def _zf_entry(root: Path | None = None) -> tuple[dict, object]:
    reg = registry.load_class_package((root or TOOL_ROOT / "source") / "world" / "dungeons", ids_cfg=IDS)
    return {e["map_id"]: e for e in reg.dungeons}[209], reg


def _fixture(root: Path, *, kit_text: dict[str, str] | None = None) -> Path:
    """A copy of the dungeon file beside a fake npc package (so `_KIT_NPCS` points into `root`)."""
    (root / "world" / "dungeons").mkdir(parents=True)
    (root / "npcs" / "zul_farrak").mkdir(parents=True)
    (root / "world" / "dungeons" / "zul_farrak.py").write_text(ZF_FILE.read_text(encoding="utf-8"))
    for name, text in (kit_text or {}).items():
        (root / "npcs" / "zul_farrak" / name).write_text(text)
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


class DeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # taken right before the declaration loads: a boss WP may land its files at any time (the other WPs run in
        # this worktree), and both must see the same set
        cls.declared = _kit_declared()
        cls.entry, cls.reg = _zf_entry()
        cls.heroic = cls.entry["heroic"]

    def test_the_ids_are_the_next_of_their_blocks_after_ragefire_chasm(self):
        self.assertEqual((self.heroic["map_difficulty_id"], self.heroic["access_id"]), (1008, 130))
        self.assertEqual(self.heroic["encounter_ids"], HEROIC_ENCOUNTER_IDS)
        self.assertEqual(self.heroic["min_level"], 60)

    def test_the_heroic_row_is_a_five_player_row_not_flex(self):
        self.assertEqual(self.heroic["max_players"], 5)
        md = {r["ID"]: r for r in self.reg.map_difficulties}[1008]
        self.assertEqual((md["MapID"], md["Difficulty"], md["RaidDuration"], md["MaxPlayers"]), (209, 1, 86400, 5))
        self.assertEqual(md["Message_Lang_enUS"], "Heroic Difficulty requires you to be level 60.")
        self.assertEqual(md["Difficultystring"], "DUNGEON_DIFFICULTY_5PLAYER_HEROIC")
        access = {r["id"]: r for r in self.reg.dungeon_access}[130]
        self.assertEqual((access["map_id"], access["difficulty"], access["min_level"]), (209, 1, 60))

    def test_spawns_go_to_heroic_and_only_the_entrance_goblin_stays_normal_only(self):
        self.assertTrue(self.heroic["spawn_mask"])
        self.assertFalse(self.heroic["event_spawns"])
        self.assertEqual(self.heroic["normal_only_creatures"], (NORMAL_ONLY_GOBLIN,))

    def test_the_stock_encounters_are_re_pointed_in_kill_order(self):
        decls = {d["id"]: d for d in self.reg.encounter_declarations if 593 <= d["id"] <= 600}
        self.assertEqual(sorted(decls), sorted(ENCOUNTERS))
        for normal, (_heroic_id, order, _bit, name, credit) in ENCOUNTERS.items():
            with self.subTest(encounter=normal):
                decl = decls[normal]
                self.assertEqual(decl["kind"], "repoint")
                self.assertEqual(decl["order_index"], order)
                self.assertIsNone(decl["bit"])  # the bits are the instance's boss slots: never moved
                self.assertEqual(decl["credit"], credit if credit[0] == 1 else None)  # creature credits stay stock
                if credit[0] == 1:
                    self.assertEqual(decl["name"], name)
                else:
                    self.assertIsNone(decl["name"])
        self.assertEqual({d["id"] for d in self.reg.encounter_declarations if d.get("map_id") == 209}, set())

    def test_the_credit_spells_are_the_ones_the_instance_declares(self):
        text = (KIT_DIR / "instance.py").read_text(encoding="utf-8")
        for name, spell_id in (("SPELL_PYRAMID_CREDIT", 213840), ("SPELL_CREW_CREDIT", 213841)):
            self.assertRegex(text, re.compile(rf"^{name} = {spell_id}$", re.M))

    def test_roles_extras_and_skips(self):
        by_entry = {c["entry"]: c for c in self.entry["creatures"]}
        for entry in ROLE_BOSS:
            self.assertEqual(by_entry[entry]["role"], "boss", entry)
        self.assertEqual(self.entry["skip"], SKIPPED)
        for extra in KIT_EXTRA:
            self.assertEqual(by_entry[extra]["source"], "extra", extra)
            self.assertEqual(by_entry[extra]["role"], "trash", extra)
            self.assertTrue(by_entry[extra]["summoned_by"], extra)  # a summon: no spawns, free text names who
            self.assertEqual(by_entry[extra]["spawns"], 0, extra)
        self.assertEqual(by_entry[15578]["event"], True)
        for entry in TRASH:
            self.assertEqual(by_entry[entry]["role"], "trash", entry)
        for not_declared in (7789, 8876, 8877, 301005, 301010, 301018, 301030):
            self.assertNotIn(not_declared, by_entry)  # left out of the event / run on their normal entry
        # the quests WP's entrance goblin: an extra npc line (its hand spawn), normal only (normal_only_creatures)
        goblin = by_entry[NORMAL_ONLY_GOBLIN]
        self.assertEqual((goblin["role"], goblin["source"]), ("npc", "extra"))

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
                self.assertEqual(overrides[entry].get("melee"), BOSS_MELEE.get(entry))  # None: the tier's
                self.assertNotIn("tier", overrides[entry])

    def test_the_crew_is_the_headers_heroic_health_with_small_hits_and_no_boss_columns(self):
        overrides = {entry: dict(pairs) for entry, pairs in self.heroic["overrides"]}
        header = _header_health()
        for entry, (name, melee) in CREW.items():
            with self.subTest(entry=entry):
                health = header[name][1] if name else _header_constant("kWeegliPoolAlly")
                got = {k: (dict(v) if k == "columns" else v) for k, v in overrides[entry].items()}
                self.assertEqual(got, {"health": health, "melee": melee, "columns": CREW_COLUMNS})
        self.assertEqual(_header_constant("kWeegliPoolAlly"), WEEGLI_HEALTH)

    def test_every_boss_of_the_header_table_is_overridden(self):
        header = _header_health()
        names = {name for name, _base in BOSSES.values()} | {name for name, _m in CREW.values() if name}
        self.assertEqual(set(header), names)

    def test_the_unscaled_adds(self):
        overrides = {entry: dict(pairs) for entry, pairs in self.heroic["overrides"]}
        for entry, health in ADD_HEALTH.items():
            expected = {"health": health, **({"columns": ADD_COLUMNS[entry]} if entry in ADD_COLUMNS else {})}
            got = {k: (dict(v) if k == "columns" else v) for k, v in overrides[entry].items()}
            self.assertEqual(got, expected, entry)

    def test_the_predicted_ids_in_the_source_are_the_lock_mint_order(self):
        ids = _source_table("_HEROIC_ID")
        self.assertEqual(sorted(ids), sorted(ids, key=ids.get))  # ids follow the entry order
        self.assertEqual(min(ids.values()), FIRST_HEROIC_ID)
        self.assertEqual(sorted(ids.values()), list(range(FIRST_HEROIC_ID, FIRST_HEROIC_ID + len(ids))))
        self.assertEqual(sum(1 for e in ids if e < 300000), STOCK_SET_COUNT)
        self.assertEqual(sorted(e for e in ids if e >= 300000), sorted(KIT_HEALTH))

    def test_the_kit_overrides_follow_their_declared_templates(self):
        overrides = {entry: dict(pairs) for entry, pairs in self.heroic["overrides"]}
        for entry, health in KIT_HEALTH.items():
            self.assertEqual(entry in overrides, entry in self.declared, entry)
            if entry in overrides:
                self.assertEqual(overrides[entry], {"health": health})
        self.assertEqual(sorted(e for e in overrides if e >= 300000), sorted(e for e in KIT_HEALTH if e in
                                                                              self.declared))

    def test_the_text_scan_agrees_with_the_real_npc_package(self):
        """Whatever creature_template() rows the real package declares, the scan sees (a miss would leave a declared
        unit on the tier's 37k: R1-KIT M-4 of the Scarlet Monastery build)."""
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "world" / "dungeons").mkdir(parents=True)
            shutil.copytree(KIT_DIR, root / "npcs" / "zul_farrak", ignore=shutil.ignore_patterns("__pycache__"))
            (root / "world" / "dungeons" / "zul_farrak.py").write_text(ZF_FILE.read_text(encoding="utf-8"))
            entry, _reg = _zf_entry(root)
        overrides = {e: dict(p) for e, p in entry["heroic"]["overrides"]}
        for unit in KIT_HEALTH:
            self.assertEqual(unit in overrides, unit in self.declared, unit)

    def test_a_kit_override_appears_when_a_source_file_declares_the_template(self):
        cases = {
            "literal": ("g = creature_template(301031, 'Wellspring', **{})\n", True),
            "constant": ("WELL = 301031\ng = creature_template(WELL, 'Wellspring')\n", True),
            "helper": ("def _unit(entry, name):\n    return creature_template(entry, name)\n"
                       "g = _unit(301031, 'Wellspring')\n", True),
            "docstring": ('"""creature_template(301031, ...) is named here and is not a declaration."""\n', False),
            "comment": ("# creature_template(301031, 'Wellspring')\n", False),
            "columns edit": ("creature_template_columns(301031, x=1)\n", False),
            "other unit": ("w = creature_template(301030, 'Puddle')\n", False),
        }
        for label, (text, expected) in cases.items():
            with self.subTest(label), tempfile.TemporaryDirectory() as d:
                root = _fixture(Path(d), kit_text={"hard_mode.py": text})
                entry, _reg = _zf_entry(root)
            overrides = {e: dict(p) for e, p in entry["heroic"]["overrides"]}
            self.assertEqual(301031 in overrides, expected)
            if expected:
                self.assertEqual(overrides[301031]["health"], KIT_HEALTH[301031])

    def test_every_override_names_a_listed_creature(self):
        with tempfile.TemporaryDirectory() as d:
            kit = "\n".join(f"u{entry} = creature_template({entry}, 'x')" for entry in KIT_HEALTH) + "\n"
            root = _fixture(Path(d), kit_text={"all.py": kit})
            entry, _reg = _zf_entry(root)
        listed = {c["entry"] for c in entry["creatures"]}
        overrides = {e for e, _p in entry["heroic"]["overrides"]}
        for unit in overrides:
            self.assertIn(unit, listed)
        self.assertTrue(set(KIT_HEALTH) <= overrides)

    def test_the_finder_entry_and_the_conf_lines(self):
        text = LFG_HEROIC_FILE.read_text(encoding="utf-8")
        self.assertIn(f"lfg_heroic({FINDER_HEROIC}, normal={FINDER_NORMAL}, group=CLASSIC_HEROIC)", text)
        gate = re.search(r'^ContentGate\.Open\.Instances\.Kalimdor\s*=\s*"([^"]*)"', CONTENT_GATE_DIST.read_text(),
                         re.M)
        self.assertIsNotNone(gate)
        self.assertIn("209:N,H", gate[1].split())
        self.assertNotIn("209:N", gate[1].split())  # the old, normal-only token is gone
        self.assertIn("389:N,H", gate[1].split())  # Ragefire Chasm's stays
        bm = re.search(r'^BossMechanics\.ReferenceHealth\.MapLevels\s*=\s*"([^"]*)"', BM_CONF_DIST.read_text(), re.M)
        self.assertIsNotNone(bm)
        self.assertTrue({"209:46", "209h:60"} <= set(bm[1].split()))
        dd = re.search(r'^DungeonDifficulties\.Heroic\.Maps\s*=\s*"([^"]*)"', DD_CONF_DIST.read_text(), re.M)
        self.assertIsNotNone(dd)
        self.assertIn("209", dd[1].split())
        self.assertIn("389", dd[1].split())


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
            # The Zul'Farrak boss package declares its kit units (source/npcs/zul_farrak/) as they land
            kit = registry.load_class_package(
                KIT_DIR, ids_cfg=IDS, existing_creature_rows=existing,
                creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
                creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS, live_data={},
            )
            for key in ("creature_templates", "creature_template_models", "creature_template_edits"):
                cls.dsl[key] = cls.dsl.get(key, []) + list(getattr(kit, key))
            # only Zul'Farrak's heroic and encounters are expanded here (the other dungeons have their own tests)
            cls.dsl["dungeons"] = [e if e["map_id"] == 209 else dict(e, heroic=None) for e in cls.dsl["dungeons"]]
            cls.dsl["encounter_declarations"] = [d for d in cls.dsl["encounter_declarations"]
                                                 if 593 <= d["id"] <= 600]
            cls.index = spell_tables.load_spell_table_index()
            cls.encounters = dungeon_encounters.expand(cls.dsl, lambda: dungeon_encounters.load_inputs(
                cls.index, {*existing, *(int(r["entry"]) for r in cls.dsl.get("creature_templates", []))},
                spell_ids=set(CREDIT_SPELLS), ids_cfg=IDS))
            cls.live = dungeon_heroic.load_live_world(existing, cls.index)
            cls.out = dungeon_heroic.expand(cls.dsl, lambda: cls.live, ids_cfg=IDS)
            cls.out_live_spawns = {
                table: {int(guid): row for guid, row in cls.live.spawns.get(table, {}).items()
                        if int(row.get("map") or 0) == 209} for table in spawn_state.SPAWN_TABLES
            }
            cls.existing = existing
            # generate.py's next step: the finder (source/world/lfg_classic_*.py) with only this map's entry
            heroic = registry.load_class_file(LFG_HEROIC_FILE, ids_cfg=IDS)
            cls.dsl["lfg_group_declarations"] = list(heroic.lfg_group_declarations)
            cls.dsl["lfg_dungeon_declarations"] = [
                d for d in heroic.lfg_dungeon_declarations
                if d["kind"] == "random" or d.get("normal") == FINDER_NORMAL
            ]
            cls.lfg_inputs = lfg_dungeons.load_inputs(cls.index)
            cls.lfg_out = lfg_dungeons.expand(cls.dsl, lambda: cls.lfg_inputs)
        finally:
            sqlcorpus.deactivate()
        cls.entry = next(e for e in cls.dsl["dungeons"] if e["map_id"] == 209)
        cls.reports = {r.normal: r for r in cls.out.heroic_reports}
        cls.declared = _kit_declared()

    def _heroic_link_errors(self) -> list[str]:
        """The ERRORs that ask a declared kit unit to name its heroic entry in difficulty_entry_1
        (lib/dungeon_heroic.py: 'declares the full row - set difficulty_entry_1 there'). A boss WP declares its units
        before the others have landed and the minted id shifts until they have: `test_declared_kit_units_carry_their_
        heroic_entry` checks them, not this."""
        return [e for e in self.out.errors if "declares the full row - set difficulty_entry_1" in e]

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
        for entry in sorted(KIT_HEALTH):
            if entry not in rows or not int(rows[entry].get("difficulty_entry_1") or 0):
                continue
            with self.subTest(entry=entry):
                if all(lower in rows for lower in KIT_HEALTH if lower < entry):
                    self.assertEqual(int(rows[entry]["difficulty_entry_1"]), predicted[entry])
                else:
                    self.assertLessEqual(int(rows[entry]["difficulty_entry_1"]), predicted[entry])
        if set(KIT_HEALTH) <= set(rows):
            self.assertEqual(self._heroic_link_errors(), [])

    def test_eight_heroic_encounters_in_the_kill_order_with_their_credit(self):
        rows = {r["ID"]: r for r in self.dsl["dungeon_encounters"] if r["Difficulty"] == 1}
        self.assertEqual(sorted(rows), list(HEROIC_ENCOUNTER_IDS))
        normal = {r["ID"]: r for r in self.dsl["dungeon_encounters"] if r["Difficulty"] == 0}
        self.assertEqual(sorted(normal), sorted(ENCOUNTERS))  # the eight re-pointed stock rows
        for normal_id, (heroic_id, order, bit, name, _credit) in ENCOUNTERS.items():
            with self.subTest(encounter=normal_id):
                row, source_row = rows[heroic_id], normal[normal_id]
                self.assertEqual((row["MapID"], row["Difficulty"]), (209, 1))
                self.assertEqual((row["Bit"], row["OrderIndex"], row["Name_Lang_enUS"]),
                                 (source_row["Bit"], source_row["OrderIndex"], source_row["Name_Lang_enUS"]))
                self.assertEqual((row["Bit"], row["OrderIndex"]), (bit, order))
                self.assertEqual(source_row["Name_Lang_enUS"], name)
        self.assertEqual([r["OrderIndex"] for _i, r in sorted(rows.items())],
                         sorted(r["OrderIndex"] for r in rows.values()))  # ids in OrderIndex order
        self.assertEqual(sorted(r["Bit"] for r in rows.values()), list(range(8)))

    def test_the_credits_six_by_creature_two_by_spell(self):
        by_entry = {r["entry"]: r for r in self.dsl["instance_encounters"]}
        for normal_id, (heroic_id, _order, _bit, _name, credit) in ENCOUNTERS.items():
            for entry in (normal_id, heroic_id):
                self.assertEqual((int(by_entry[entry]["creditType"]), int(by_entry[entry]["creditEntry"])), credit,
                                 entry)  # a heroic body credits the NORMAL entry; the spell credits name the same
        self.assertEqual({int(by_entry[e]["creditEntry"]) for e in (598, 599)}, set(CREDIT_SPELLS))

    def test_the_heroic_ukorz_completes_the_heroic_entry(self):
        by_entry = {r["entry"]: r for r in self.dsl["instance_encounters"]}
        self.assertEqual(int(by_entry[600]["lastEncounterDungeon"]), FINDER_NORMAL)  # stock: ends Finder entry 24
        self.assertEqual({e: int(by_entry[e]["lastEncounterDungeon"]) for e in HEROIC_ENCOUNTER_IDS},
                         {e: (FINDER_HEROIC if e == HEROIC_UKORZ else 0) for e in HEROIC_ENCOUNTER_IDS})
        # the normal rows are stock: no edit of a normal link
        self.assertEqual({r["entry"] for r in self.dsl["instance_encounters"] if r.get(lfg_dungeons.LINK)}, set())

    def test_the_creature_set(self):
        mapping = self.entry["heroic_entries"]
        ids = _source_table("_HEROIC_ID")
        self.assertEqual({e for e in mapping if e < 300000}, {e for e in ids if e < 300000})
        for out in (*SKIPPED, 7789, 8876, 8877, NORMAL_ONLY_GOBLIN):
            self.assertNotIn(out, mapping)
        for boss in ROLE_BOSS:
            self.assertIn(boss, mapping)  # Bly and Weegli too: a role `npc` would have left them out
        declared_rows = {int(r["entry"]) for r in self.dsl["creature_templates"] if not r.get(dungeon_heroic.DERIVED)}
        for unit in KIT_HEALTH:
            self.assertEqual(unit in mapping, unit in declared_rows, unit)
        for no_heroic in (301005, 301006, 301007, 301010, 301011, 301012, 301013, 301018, 301019, 301025, 301026,
                          301030, 301032, 301033):
            self.assertNotIn(no_heroic, mapping)
        block = IDS["creature_heroic"]
        locked = heroic_templates.parse_lock(heroic_templates.LOCK_PATH.read_text()).pairs
        for normal, heroic in mapping.items():
            self.assertTrue(block["start"] <= heroic <= block["end"], (normal, heroic))
        self.assertEqual(len(set(mapping.values())), len(mapping))
        self.assertFalse(set(mapping.values()) & {h for n, h in locked.items() if n not in mapping})

    def test_the_predicted_lock_lines(self):
        """The ids the first write run mints: normal-entry order from 310501 (38 lines for the stock set), the kit
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
                self.assertEqual(stock[boss], ids[boss], boss)
        kit = sorted(e for e in fresh if e >= 300000)
        for rank, entry in enumerate(kit):  # consecutive after the stock set; a missing lower unit shifts down only
            self.assertEqual(fresh[entry], FIRST_HEROIC_ID + STOCK_SET_COUNT + rank, entry)
            self.assertLessEqual(fresh[entry], ids[entry], entry)
        if set(KIT_HEALTH) <= set(fresh):
            for entry in KIT_HEALTH:
                self.assertEqual(fresh[entry], ids[entry], entry)
        # nothing of this map is committed yet: the run appends one line per template (or none, after the write run)
        self.assertIn(len(self.out.lock_appended), (0, len(mapping)))

    def test_bosses(self):
        common = _load_common()
        rows = {int(r["entry"]): r for r in self.dsl["creature_templates"] if r.get(dungeon_heroic.DERIVED)}
        heroic_entry = self.entry["heroic_entries"]
        header = _header_health()
        for boss, (name, base) in BOSSES.items():
            with self.subTest(boss=boss):
                report = self.reports[boss]
                self.assertEqual(report.role, "boss")
                self.assertEqual(report.solved.health, header[name][1])
                self.assertEqual(report.solved.tier_row, "boss")
                row = rows[heroic_entry[boss]]
                self.assertEqual((row["minlevel"], row["maxlevel"], row["exp"]), (60, 60, 0))
                self.assertAlmostEqual(float(row["HealthModifier"]) * base, header[name][1], delta=1.0, msg=boss)
                self.assertEqual(int(row["CreatureImmunitiesId"]), common.IMMUNITY_BOSS_STUN)
                self.assertEqual(int(row["flags_extra"]), common.BOSS_FLAGS_EXTRA)  # bind + both assist flags
                self.assertEqual(int(row["flags_extra"]) & 1, 1)  # INSTANCE_BIND
                self.assertEqual(float(row["detection_range"]), common.BOSS_DETECTION_RANGE)
                self.assertEqual((row["AIName"], row["ScriptName"]), ("", ""))  # the normal entry's script runs
                lootid = ids_loot(boss) if OWN_LOOT and boss in HEROIC_LOOT_BOSSES else boss
                self.assertEqual(int(row["lootid"]), lootid)
                self.assertEqual(int(row["KillCredit1"]), 0)

    def test_the_boss_melee_is_the_tiers_2500_a_swing_and_the_pairs_half_of_it(self):
        for boss in BOSSES:
            solved = self.reports[boss].solved
            swing = (solved.min_damage + solved.max_damage) / 2 * 2000 / solved.swing_ms
            self.assertAlmostEqual(swing, BOSS_MELEE.get(boss, TIER_MELEE), delta=10, msg=boss)

    def test_the_crew_is_five_boss_bodies_with_small_hits_on_the_live_rows(self):
        rows = {int(r["entry"]): r for r in self.dsl["creature_templates"] if r.get(dungeon_heroic.DERIVED)}
        heroic_entry = self.entry["heroic_entries"]
        header = _header_health()
        for entry, (name, melee) in CREW.items():
            with self.subTest(entry=entry):
                report = self.reports[entry]
                self.assertEqual((report.role, report.solved.tier_row), ("boss", "boss"))
                self.assertEqual(report.solved.health, header[name][1] if name else WEEGLI_HEALTH)
                swing = (report.solved.min_damage + report.solved.max_damage) / 2 * 2000 / report.solved.swing_ms
                self.assertAlmostEqual(swing, melee, delta=10)
                row = rows[heroic_entry[entry]]
                self.assertEqual((row["minlevel"], row["maxlevel"]), (60, 60))
                normal = self.existing[entry]
                # no boss columns: the live normal row's faction, immunity set and detection range carry over
                self.assertEqual(int(row["faction"]), int(normal["faction"]))
                # Bly's declared normal row (D5) carries 1972 to the copy; the others keep the live set
                self.assertEqual(int(row["CreatureImmunitiesId"]),
                                 1972 if entry == 7604 else int(normal["CreatureImmunitiesId"]))
                self.assertEqual(float(row["detection_range"]), float(normal["detection_range"]))
                self.assertEqual(int(row["npcflag"]), int(normal["npcflag"]))  # Bly's and Weegli's gossip carries over
                self.assertEqual(int(row["flags_extra"]) & 0x06000000, 0)  # no assist flags: they help each other
                for column, value in CREW_COLUMNS.items():
                    self.assertEqual(int(row[column]), value, column)

    def test_the_unscaled_adds(self):
        rows = {int(r["entry"]): r for r in self.dsl["creature_templates"] if r.get(dungeon_heroic.DERIVED)}
        heroic_entry = self.entry["heroic_entries"]
        for entry, health in ADD_HEALTH.items():
            with self.subTest(entry=entry):
                self.assertEqual(self.reports[entry].solved.health, health)
                self.assertEqual((rows[heroic_entry[entry]]["minlevel"], rows[heroic_entry[entry]]["maxlevel"]),
                                 (60, 60))
        for entry, health in KIT_HEALTH.items():
            if entry in heroic_entry:
                self.assertEqual(self.reports[entry].solved.health, health, entry)

    def test_the_trash_takes_the_tier_as_it_is(self):
        rows = {int(r["entry"]): r for r in self.dsl["creature_templates"] if r.get(dungeon_heroic.DERIVED)}
        heroic_entry = self.entry["heroic_entries"]
        # the Dead Hero and the Zombie (the graves) and the tier of every stock rank (a rank 0 unit: normal row)
        tier = {0: ("normal", 12_000, 200), 1: ("elite", 37_000, 550), 2: ("rare", 74_000, 900),
                4: ("rare", 74_000, 900)}
        for entry in TRASH:
            with self.subTest(entry=entry):
                report = self.reports[entry]
                row_name, health, melee = tier[report.rank]
                self.assertEqual((report.role, report.solved.tier_row, report.solved.health),
                                 ("trash", row_name, health))
                swing = (report.solved.min_damage + report.solved.max_damage) / 2 * 2000 / report.solved.swing_ms
                self.assertAlmostEqual(swing, melee, delta=melee * 0.01)
                row = rows[heroic_entry[entry]]
                self.assertEqual((row["minlevel"], row["maxlevel"]), (60, 60))
                self.assertEqual(int(row["flags_extra"]) & 1, 0)  # no bind on trash
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
        """S0's rev drops the SmartAI of the units the rework scripts; whatever is widened is SmartAI that stays."""
        replaced = {7267, 7271, 7272, 7273, 7274, 7275, 7795, 7796, 7797, 8127, 7604, 7605, 7606, 7607, 7608}
        blocks = [b for b in self.out.smart_blocks if "UPDATE `smart_scripts` " in b]
        widened = {int(g) for b in blocks for g in re.findall(r"`entryorguid` = (\d+)", b)}
        self.assertFalse(widened & replaced, sorted(widened & replaced))

    def test_every_spawn_goes_to_heroic_except_the_event_and_the_goblin(self):
        """By guid, not by a note's count: a later hand spawn (the entrance goblin, normal only) changes the counts, and
        after the write run there is nothing left to set."""
        events = self.live.event_guids.get("creature", set())
        for table in ("creature", "gameobject"):
            blocks = [b for b in self.out.spawn_blocks if f"UPDATE `{table}` " in b]
            guids = {int(g) for block in blocks for g in re.findall(r"\d+", block.split("`guid` IN (")[1])} \
                if blocks else set()
            for guid, row in self.out_live_spawns[table].items():
                if guid in events or spawn_state.spawn_entry(row) == NORMAL_ONLY_GOBLIN:
                    self.assertNotIn(guid, guids, (table, guid))
                    continue
                # set by these blocks or carrying the bit already (the hand spawns of the boss WPs' revs)
                self.assertTrue(guid in guids or spawn_state.spawn_mask(row) & dungeon_heroic.HEROIC_SPAWN_BIT,
                                (table, guid))
        self.assertTrue(self.out_live_spawns["creature"], "no live creature spawn of map 209: the replay is empty")

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
        self.assertEqual((by_id[1008]["MapID"], by_id[1008]["Difficulty"], by_id[1008]["MaxPlayers"]), (209, 1, 5))
        self.assertEqual({k: v for k, v in by_id.items() if k < 1000}, {r["ID"]: r for r in base})
        order = [(r["MapID"], r["Difficulty"]) for r in back]
        self.assertEqual(order, sorted(order))
        self.assertEqual(sum(1 for r in back if r["MapID"] == 209 and r["Difficulty"] == 1), 1)

        de_path = state.BASE_DBC_DIR / dbcfmt.DUNGEONENCOUNTER.dbc_filename
        base_de = dbcfile.read_dbc(de_path, dbcfmt.DUNGEONENCOUNTER)
        merged_de = {r["ID"]: r for r in base_de}
        merged_de.update(dungeon_heroic.client_encounter_rows(self.dsl["dungeon_encounters"]))
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / dbcfmt.DUNGEONENCOUNTER.dbc_filename
            path.write_bytes(dbcfile.pack_client_dbc(dbcfmt.DUNGEONENCOUNTER, list(merged_de.values()), base_de))
            back_de = dbcfile.read_dbc(path, dbcfmt.DUNGEONENCOUNTER)
        self.assertEqual(len(back_de), len(base_de) + 8)
        self.assertEqual(sorted(r["ID"] for r in back_de if r["MapID"] == 209 and r["Difficulty"] == 1),
                         list(HEROIC_ENCOUNTER_IDS))
        normal = {r["ID"]: r for r in back_de if r["MapID"] == 209 and r["Difficulty"] == 0}
        self.assertEqual(sorted(normal), sorted(ENCOUNTERS))
        # the client's normal list shows the re-pointed rows: names of 598 / 599 and the kill order
        self.assertEqual((normal[598]["Name_Lang_enUS"], normal[599]["Name_Lang_enUS"]),
                         ("The Pyramid", "Sergeant Bly's Crew"))
        self.assertEqual([i for i, _r in sorted(normal.items(), key=lambda kv: kv[1]["OrderIndex"])],
                         [596, 595, 597, 598, 599, 600, 593, 594])
        self.assertEqual({i: normal[i]["Bit"] for i in normal}, {i: ENCOUNTERS[i][2] for i in ENCOUNTERS})

    # --- the Finder -------------------------------------------------------------------------------------------

    def _rows(self):
        return {r["ID"]: r for r in self.dsl["lfg_dungeons"]}

    def test_the_heroic_entry(self):
        row = self._rows()[FINDER_HEROIC]
        stock = {r["ID"]: r for r in dbcfile.read_dbc(state.BASE_DBC_DIR / dbcfmt.LFGDUNGEONS.dbc_filename,
                                                      dbcfmt.LFGDUNGEONS)}
        self.assertEqual(row["Name_Lang_enUS"], stock[FINDER_NORMAL]["Name_Lang_enUS"])
        self.assertEqual((row["TypeID"], row["Difficulty"], row["Group_Id"], row["MapID"], row["Flags"]),
                         (5, 1, 12, 209, 3))
        self.assertEqual((row["MinLevel"], row["MaxLevel"]), (60, 62))
        self.assertEqual(row["TextureFilename"], stock[FINDER_NORMAL]["TextureFilename"])
        self.assertNotIn(FINDER_NORMAL, self._rows())  # the stock normal row stays as it is
        # stock entry 24 has no lfg_dungeon_template row (the Finder falls back to the areatrigger): the copy has none
        self.assertNotIn(FINDER_NORMAL, self.lfg_inputs.positions)
        self.assertNotIn(FINDER_HEROIC, {t["dungeonId"] for t in self.dsl["lfg_dungeon_templates"]})

    def test_the_client_lfg_file_gains_the_new_row_and_random_classic_heroic_draws_it(self):
        base = dbcfile.read_dbc(state.BASE_DBC_DIR / dbcfmt.LFGDUNGEONS.dbc_filename, dbcfmt.LFGDUNGEONS)
        merged = {r["ID"]: r for r in base}
        merged.update(lfg_dungeons.client_dungeon_rows(self.dsl["lfg_dungeons"]))
        new = set(merged) - {r["ID"] for r in base}
        self.assertIn(FINDER_HEROIC, new)
        pool = {i for i, r in merged.items() if r["Group_Id"] == 12 and r["TypeID"] == 5}
        self.assertIn(FINDER_HEROIC, pool)


def ids_loot(boss: int) -> int:
    """The predicted heroic lootid of a boss (its own heroic entry, `_HEROIC_ID`)."""
    return _source_table("_HEROIC_ID")[boss]


if __name__ == "__main__":
    unittest.main()
