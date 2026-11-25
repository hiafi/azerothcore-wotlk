"""
Ragefire Chasm's heroic declaration (Ragefire Chasm build, WP-H): source/world/dungeons/ragefire_chasm.py as
generate.py loads it, the heroic Finder entry 318 of source/world/lfg_classic_heroic.py and the content gate line.

Covered: the heroic() arguments (MapDifficulty 1007 with MaxPlayers 5, dungeon_access 129, DungeonEncounter 1095-1098,
spawn masks, no event spawns, the entrance orc normal-only), the roles / skip / extra declarations (Zelemar and Maur
Grimtotem skipped, the Blood Globule extra), the boss overrides against the build spec's numbers (handoff 3.6, pinned to
the header's `kHealth` tables) with the stun immunity set, flags_extra and detection range pinned to the normal rows'
`boss_columns()`, the predicted heroic lootids and the `_HEROIC_BOSS_OWN_LOOT` flag (on since L-1), the Blood Globule's
override following its `creature_template()` declaration (a docstring or comment naming the entry does not count; the
text scan agrees with the real npc package), and the expansion against the live replay: no ERROR or WARNING, the four
heroic encounters paired with the stock rows 430 / 432 / 433 / 431 in OrderIndex order, the creature set and the
predicted heroic_ids.lock lines (310488 on, normal-entry order, the table the boss WPs read), the bosses' INSTANCE_BIND,
immunity, assist flags and detection range, the tier's trash and melee, the SmartAI widening, the spawn masks, the
client MapDifficulty.dbc / DungeonEncounter.dbc rows (the patch-Z merge) and the Finder (one heroic entry completing on
the heroic Taragaman).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_ragefire_chasm_heroic.py
"""

from __future__ import annotations

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
from lib import dbcfile, dbcfmt, dungeon_checks, dungeon_heroic, heroic_templates, lfg_dungeons, source  # noqa: E402
from lib import spawn_state, spell_tables, sqlcorpus, state  # noqa: E402
from lib import test_ragefire_chasm_npcs as npcs_test  # noqa: E402
from lib.dsl import registry  # noqa: E402

RFC_FILE = TOOL_ROOT / "source" / "world" / "dungeons" / "ragefire_chasm.py"
LFG_HEROIC_FILE = TOOL_ROOT / "source" / "world" / "lfg_classic_heroic.py"
KIT_DIR = TOOL_ROOT / "source" / "npcs" / "ragefire_chasm"
COMMON_FILE = KIT_DIR / "_common.py"
HEADER = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "RagefireChasm" / "RagefireChasmRework.h"
CONTENT_GATE_DIST = REPO_ROOT / "modules" / "mod-content-gate" / "conf" / "content_gate.conf.dist"
IDS = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")

# Stock normal encounter -> boss, and the heroic copies in (OrderIndex, Bit, ID) order of the stock rows:
# 430 Oggleflint (order 0, bit 0), 432 Jergosh (2000, 2), 433 Bazzalan (3000, 3), 431 Taragaman (4000, 1).
HEROIC_TO_NORMAL = {1095: 430, 1096: 432, 1097: 433, 1098: 431}
CREDITS = {1095: 11517, 1096: 11518, 1097: 11519, 1098: 11520}
ENCOUNTER_NAMES = {1095: "Oggleflint", 1096: "Jergosh the Invoker", 1097: "Bazzalan", 1098: "Taragaman the Hungerer"}
ENCOUNTER_BITS = {1095: (0, 0), 1096: (2, 2000), 1097: (3, 3000), 1098: (1, 4000)}  # heroic id -> (Bit, OrderIndex)

# Heroic health (handoff 3.6): HealthModifier x the level 60 class base (warrior 3,052, mage 2,136).
BOSS_HEALTH = {11517: 238_056, 11518: 252_048, 11519: 250_264, 11520: 314_356}
BOSS_MODIFIER = {11517: 78, 11518: 118, 11519: 82, 11520: 103}
BOSS_CLASS_BASE = {11517: 3_052, 11518: 2_136, 11519: 3_052, 11520: 3_052}
BLOOD_GLOBULE = 300987
GLOBULE_HEALTH = 6_000
NORMAL_ONLY_ORC = 300989
SKIPPED = (17830, 11834)  # Zelemar the Wrathful (ruling 5), Maur Grimtotem (the quest corpse)
# The kit units that run on their normal entry (no heroic template)
NO_HEROIC = (300985, 300986, 300988, NORMAL_ONLY_ORC)

# The predicted heroic ids: the write run mints in normal-entry order from 310488: the extraction set (12 lines) and
# the Blood Globule after it (it needs its template declared). The boss lootids are the same numbers as the heroic ids.
FIRST_HEROIC_ID = 310488
EXTRACTION_SET = (8996, 11318, 11319, 11320, 11321, 11322, 11323, 11324, 11517, 11518, 11519, 11520)
PREDICTED = {entry: FIRST_HEROIC_ID + i for i, entry in enumerate(EXTRACTION_SET)}
GLOBULE_HEROIC_ID = FIRST_HEROIC_ID + len(EXTRACTION_SET)
HEROIC_LOOTID = {11517: 310496, 11518: 310497, 11519: 310498, 11520: 310499}
TRASH = (11318, 11319, 11320, 11321, 11322, 11323, 11324)
FINDER_HEROIC, FINDER_NORMAL = 318, 4
# STAGE-D3 Q2 A: Bazzalan swings for half the tier (his heroic Sinister Strike is one more swing every 2 s)
TIER_MELEE = 2_500
BOSS_MELEE = {11519: 1_250}
BOSS_SPAWN_GUIDS = (48644, 48740, 48750, 48706)  # 11517, 11518, 11519, 11520

PENDING = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world"
HEROIC_MARKER = "-- Ragefire Chasm (map 389) heroic:"


def _rendered_or_committed(blocks: list[str], want: str) -> list[str]:
    """The rendered blocks holding `want`, or (after the write run: the replay already holds those rows, so nothing is
    rendered) the same blocks of the committed rev(s), each from its marker line to the next comment line."""
    rendered = [b for b in blocks if want in b]
    if rendered:
        return rendered
    found = []
    for path in sorted(PENDING.glob("rev_*.sql")):
        text = path.read_text(encoding="utf-8")
        if HEROIC_MARKER in text:
            found += re.findall(re.escape(HEROIC_MARKER) + r"[^\n]*\n(?:(?!-- )[^\n]*\n?)*", text)
    return [block for block in found if want in block]


def _load_common():
    """source/npcs/ragefire_chasm/_common.py as a module (the dungeon files never import the npc packages)."""
    spec = importlib.util.spec_from_file_location("rfc_common_for_heroic_test", COMMON_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _own_heroic_loot() -> bool:
    """ragefire_chasm.py's `_HEROIC_BOSS_OWN_LOOT` (on since L-1 declared the heroic loot groups)."""
    m = re.search(r"^_HEROIC_BOSS_OWN_LOOT\s*=\s*(True|False)\s*$", RFC_FILE.read_text(encoding="utf-8"), re.M)
    return bool(m) and m.group(1) == "True"


OWN_LOOT = _own_heroic_loot()


def _kit_declared() -> set[int]:
    """The entries source/npcs/ragefire_chasm/*.py declares with creature_template(<entry>, ...) or a private helper
    taking the entry first (a literal or a module constant), outside docstrings and comments."""
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
    return found & set(range(300985, 301000))  # spell helpers take a 6-digit id first too


def _rfc_entry(root: Path | None = None) -> tuple[dict, object]:
    reg = registry.load_class_package((root or TOOL_ROOT / "source") / "world" / "dungeons", ids_cfg=IDS)
    return {e["map_id"]: e for e in reg.dungeons}[389], reg


def _fixture(root: Path, *, kit_text: dict[str, str] | None = None) -> Path:
    """A copy of the dungeon file beside a fake npc package (so `_KIT_NPCS` points into `root`)."""
    (root / "world" / "dungeons").mkdir(parents=True)
    (root / "npcs" / "ragefire_chasm").mkdir(parents=True)
    (root / "world" / "dungeons" / "ragefire_chasm.py").write_text(RFC_FILE.read_text(encoding="utf-8"))
    for name, text in (kit_text or {}).items():
        (root / "npcs" / "ragefire_chasm" / name).write_text(text)
    return root


def _header_health() -> dict[str, tuple[int, int]]:
    """Each boss namespace's `kHealth{ normal, heroic[, hard mode] }` of RagefireChasmRework.h."""
    text = HEADER.read_text(encoding="utf-8")
    out: dict[str, tuple[int, int]] = {}
    for m in re.finditer(r"namespace (Oggleflint|Jergosh|Bazzalan|Taragaman)\b.*?constexpr kHealth\{\s*(\d+),\s*(\d+)",
                         text, re.S):
        out[m[1]] = (int(m[2]), int(m[3]))
    return out


class DeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # taken right before the declaration loads: a boss WP may land its files at any time (the other WPs run in
        # this worktree), and both must see the same set
        cls.declared = _kit_declared()
        cls.entry, cls.reg = _rfc_entry()
        cls.heroic = cls.entry["heroic"]

    def test_the_ids_are_the_next_of_their_blocks_after_scarlet_monastery(self):
        self.assertEqual((self.heroic["map_difficulty_id"], self.heroic["access_id"]), (1007, 129))
        self.assertEqual(self.heroic["encounter_ids"], tuple(range(1095, 1099)))
        self.assertEqual(self.heroic["min_level"], 60)

    def test_the_heroic_row_is_a_five_player_row_not_flex(self):
        self.assertEqual(self.heroic["max_players"], 5)
        md = {r["ID"]: r for r in self.reg.map_difficulties}[1007]
        self.assertEqual((md["MapID"], md["Difficulty"], md["RaidDuration"], md["MaxPlayers"]), (389, 1, 86400, 5))
        self.assertEqual(md["Message_Lang_enUS"], "Heroic Difficulty requires you to be level 60.")
        self.assertEqual(md["Difficultystring"], "DUNGEON_DIFFICULTY_5PLAYER_HEROIC")
        access = {r["id"]: r for r in self.reg.dungeon_access}[129]
        self.assertEqual((access["map_id"], access["difficulty"], access["min_level"]), (389, 1, 60))

    def test_spawns_go_to_heroic_and_only_the_entrance_orc_stays_normal_only(self):
        self.assertTrue(self.heroic["spawn_mask"])
        self.assertFalse(self.heroic["event_spawns"])
        self.assertEqual(self.heroic["normal_only_creatures"], (NORMAL_ONLY_ORC,))

    def test_no_encounter_is_declared_or_repointed(self):
        self.assertEqual([d for d in self.reg.encounter_declarations if d.get("map_id") == 389], [])
        self.assertEqual(self.heroic["no_credit"], ())

    def test_roles_extras_and_skips(self):
        by_entry = {c["entry"]: c for c in self.entry["creatures"]}
        self.assertEqual(sorted(e for e, c in by_entry.items() if c["role"] == "boss"), sorted(BOSS_HEALTH))
        self.assertEqual(sorted(self.entry["skip"]), sorted(SKIPPED))
        self.assertEqual(by_entry[11834]["role"], "npc")  # Maur is a friendly NPC either way
        self.assertEqual(by_entry[17830]["role"], "trash")  # Zelemar is only kept out by skip=
        for entry in TRASH:
            self.assertEqual(by_entry[entry]["role"], "trash", entry)
        globule = by_entry[BLOOD_GLOBULE]
        self.assertEqual((globule["source"], globule["role"], globule["spawns"]), ("extra", "trash", 0))
        self.assertTrue(globule["summoned_by"])  # a C++ summon: no spawns, free text names who
        for kit in NO_HEROIC:
            if kit == NORMAL_ONLY_ORC:
                # the quests WP's `extra=` declaration (role npc: listed, but no heroic template and no mapping below)
                self.assertEqual((by_entry[kit]["role"], by_entry[kit]["source"]), ("npc", "extra"))
                continue
            self.assertNotIn(kit, by_entry)  # no heroic template, so not in the creature set at all

    def test_the_boss_overrides_are_the_build_specs_health_and_the_normal_rows_columns(self):
        common = _load_common()
        overrides = {entry: dict(pairs) for entry, pairs in self.heroic["overrides"]}
        expected_columns = {"CreatureImmunitiesId": common.IMMUNITY_BOSS_STUN, "flags_extra": common.BOSS_FLAGS_EXTRA,
                            "detection_range": common.BOSS_DETECTION_RANGE}
        self.assertEqual((common.IMMUNITY_BOSS_STUN, common.BOSS_FLAGS_EXTRA, common.BOSS_DETECTION_RANGE),
                         (1972, 0x06000001, 12.0))
        for entry, health in BOSS_HEALTH.items():
            with self.subTest(entry=entry):
                self.assertEqual(overrides[entry]["health"], health)
                expected = dict(expected_columns)
                if OWN_LOOT:
                    expected["lootid"] = HEROIC_LOOTID[entry]
                self.assertEqual(dict(overrides[entry]["columns"]), expected)
                self.assertEqual(overrides[entry].get("melee"), BOSS_MELEE.get(entry))  # None: the tier's, tuned in T
                self.assertNotIn("tier", overrides[entry])

    def test_the_boss_health_is_the_headers_heroic_table(self):
        header = _header_health()
        self.assertEqual(sorted(header), ["Bazzalan", "Jergosh", "Oggleflint", "Taragaman"])
        for name, entry in (("Oggleflint", 11517), ("Jergosh", 11518), ("Bazzalan", 11519), ("Taragaman", 11520)):
            self.assertEqual(header[name][1], BOSS_HEALTH[entry], name)
            self.assertEqual(BOSS_MODIFIER[entry] * BOSS_CLASS_BASE[entry], BOSS_HEALTH[entry], name)

    def test_the_predicted_ids_in_the_source_are_the_lock_mint_order(self):
        """`_HEROIC_LOOTID` of the source holds the ids the first write run mints for the four bosses."""
        text = RFC_FILE.read_text(encoding="utf-8")
        found = re.search(r"^_HEROIC_LOOTID = (\{[^}]*\})", text, re.M)
        self.assertIsNotNone(found)
        self.assertEqual(eval(found[1]), HEROIC_LOOTID)  # noqa: S307 - a literal dict of the file under test
        for entry, heroic in HEROIC_LOOTID.items():
            self.assertEqual(PREDICTED[entry], heroic)

    def test_the_blood_globule_override_follows_its_declared_template(self):
        overrides = {entry: dict(pairs) for entry, pairs in self.heroic["overrides"]}
        self.assertEqual(BLOOD_GLOBULE in overrides, BLOOD_GLOBULE in self.declared)
        if BLOOD_GLOBULE in overrides:
            self.assertEqual(overrides[BLOOD_GLOBULE], {"health": GLOBULE_HEALTH})
        self.assertEqual(sorted(e for e in overrides if e >= 300000), [BLOOD_GLOBULE] if BLOOD_GLOBULE in
                         self.declared else [])

    def test_the_text_scan_agrees_with_the_real_npc_package(self):
        """Whatever creature_template() rows the real package declares, the scan sees (a miss would leave a declared
        unit on the tier's 37k: R1-KIT M-4 of the Scarlet Monastery build). Only the Blood Globule is read from it."""
        reg = npcs_test._load()
        rows = {int(r["entry"]) for r in reg.creature_templates}
        self.assertEqual(rows, self.declared)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "world" / "dungeons").mkdir(parents=True)
            shutil.copytree(KIT_DIR, root / "npcs" / "ragefire_chasm", ignore=shutil.ignore_patterns("__pycache__"))
            (root / "world" / "dungeons" / "ragefire_chasm.py").write_text(RFC_FILE.read_text(encoding="utf-8"))
            entry, _reg = _rfc_entry(root)
        overrides = {e: dict(p) for e, p in entry["heroic"]["overrides"]}
        self.assertEqual(BLOOD_GLOBULE in overrides, BLOOD_GLOBULE in rows)

    def test_the_globule_override_appears_when_a_source_file_declares_the_template(self):
        cases = {
            "literal": ("g = creature_template(300987, 'Blood Globule', **{})\n", True),
            "constant": ("GLOBULE = 300987\ng = creature_template(GLOBULE, 'Blood Globule')\n", True),
            "helper": ("def _unit(entry, name):\n    return creature_template(entry, name)\n"
                       "g = _unit(300987, 'Blood Globule')\n", True),
            "docstring": ('"""creature_template(300987, ...) is named here and is not a declaration."""\n', False),
            "comment": ("# creature_template(300987, 'Blood Globule')\n", False),
            "columns edit": ("creature_template_columns(300987, x=1)\n", False),
            "other unit": ("w = creature_template(300986, 'Soul Wisp')\n", False),
        }
        for label, (text, expected) in cases.items():
            with self.subTest(label), tempfile.TemporaryDirectory() as d:
                root = _fixture(Path(d), kit_text={"hard_mode.py": text})
                entry, _reg = _rfc_entry(root)
            overrides = {e: dict(p) for e, p in entry["heroic"]["overrides"]}
            self.assertEqual(BLOOD_GLOBULE in overrides, expected)
            if expected:
                self.assertEqual(overrides[BLOOD_GLOBULE]["health"], GLOBULE_HEALTH)

    def test_every_override_names_a_listed_creature(self):
        with tempfile.TemporaryDirectory() as d:
            root = _fixture(Path(d), kit_text={"hard_mode.py": "g = creature_template(300987, 'Blood Globule')\n"})
            entry, _reg = _rfc_entry(root)
        listed = {c["entry"] for c in entry["creatures"]}
        for unit, _pairs in entry["heroic"]["overrides"]:
            self.assertIn(unit, listed)

    def test_the_finder_entry_and_the_content_gate_line(self):
        text = LFG_HEROIC_FILE.read_text(encoding="utf-8")
        self.assertIn(f"lfg_heroic({FINDER_HEROIC}, normal={FINDER_NORMAL}, group=CLASSIC_HEROIC)", text)
        gate = re.search(r'^ContentGate\.Open\.Instances\.Kalimdor\s*=\s*"([^"]*)"', CONTENT_GATE_DIST.read_text(),
                         re.M)
        self.assertIsNotNone(gate)
        self.assertIn("389:N,H", gate[1].split())
        self.assertNotIn("389:N", gate[1].split())  # the old, normal-only token is gone


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
            # The Ragefire Chasm boss package declares its kit units (source/npcs/ragefire_chasm/) as they land
            kit = registry.load_class_package(
                KIT_DIR, ids_cfg=IDS, existing_creature_rows=existing,
                creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
                creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS, live_data={},
            )
            for key in ("creature_templates", "creature_template_models", "creature_template_edits"):
                cls.dsl[key] = cls.dsl.get(key, []) + list(getattr(kit, key))
            # only Ragefire Chasm's heroic is expanded here (the other dungeons have their own tests)
            cls.dsl["dungeons"] = [e if e["map_id"] == 389 else dict(e, heroic=None) for e in cls.dsl["dungeons"]]
            # no normal encounter is declared here; Scarlet Monastery's (FD-SM) belong to its own expansion
            cls.dsl["encounter_declarations"] = []
            cls.index = spell_tables.load_spell_table_index()
            live = dungeon_heroic.load_live_world(existing, cls.index)
            cls.out = dungeon_heroic.expand(cls.dsl, lambda: live, ids_cfg=IDS)
            cls.out_live_spawns = {
                table: {int(guid): row for guid, row in live.spawns.get(table, {}).items()
                        if int(row.get("map") or 0) == 389} for table in spawn_state.SPAWN_TABLES
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
        cls.entry = next(e for e in cls.dsl["dungeons"] if e["map_id"] == 389)
        cls.reports = {r.normal: r for r in cls.out.heroic_reports}
        cls.declared = _kit_declared()

    def _heroic_link_errors(self) -> list[str]:
        """The ERROR that asks the declared Blood Globule to name its heroic entry in difficulty_entry_1
        (lib/dungeon_heroic.py: 'declares the full row - set difficulty_entry_1 there'). D4H declares the unit, then
        names 310500; `test_the_blood_globule_names_its_heroic_entry` checks the id once it does."""
        return [e for e in self.out.errors if "declares the full row - set difficulty_entry_1" in e]

    def test_it_is_clean(self):
        self.assertEqual([e for e in self.out.errors if e not in self._heroic_link_errors()], [])
        self.assertEqual(self.out.warnings, [])
        self.assertEqual((self.lfg_out.errors, self.lfg_out.warnings), ([], []))

    def test_the_blood_globule_names_its_heroic_entry(self):
        rows = {int(r["entry"]): r for r in self.dsl["creature_templates"] if not r.get(dungeon_heroic.DERIVED)}
        if BLOOD_GLOBULE not in rows:
            self.assertEqual(self._heroic_link_errors(), [])
            return
        named = int(rows[BLOOD_GLOBULE].get("difficulty_entry_1") or 0)
        if named:
            self.assertEqual(named, GLOBULE_HEROIC_ID)
            self.assertEqual(self._heroic_link_errors(), [])
        else:
            self.assertEqual(len(self._heroic_link_errors()), 1)  # the run prints 310500 until D4H sets it

    def test_four_heroic_encounters_in_the_stock_order_with_their_kill_credit(self):
        rows = {r["ID"]: r for r in self.dsl["dungeon_encounters"] if r["Difficulty"] == 1}
        self.assertEqual(sorted(rows), list(HEROIC_TO_NORMAL))
        stock = {r["ID"]: r for r in dbcfile.read_dbc(state.BASE_DBC_DIR / dbcfmt.DUNGEONENCOUNTER.dbc_filename,
                                                      dbcfmt.DUNGEONENCOUNTER)}
        for heroic_id, normal_id in HEROIC_TO_NORMAL.items():
            source_row = stock[normal_id]
            row = rows[heroic_id]
            self.assertEqual((row["MapID"], row["Difficulty"]), (389, 1))
            self.assertEqual((row["Bit"], row["OrderIndex"], row["Name_Lang_enUS"]),
                             (source_row["Bit"], source_row["OrderIndex"], source_row["Name_Lang_enUS"]), heroic_id)
            self.assertEqual((row["Bit"], row["OrderIndex"]), ENCOUNTER_BITS[heroic_id])
            self.assertEqual(row["Name_Lang_enUS"], ENCOUNTER_NAMES[heroic_id])
        self.assertEqual([r["OrderIndex"] for _i, r in sorted(rows.items())],
                         sorted(r["OrderIndex"] for r in rows.values()))  # ids in OrderIndex order
        # a heroic body credits the NORMAL entry: the credit names the stock boss, not the heroic copy
        credits = {r["entry"]: int(r["creditEntry"]) for r in self.dsl["instance_encounters"]
                   if 1095 <= r["entry"] <= 1098}
        self.assertEqual(credits, CREDITS)
        self.assertTrue(all(int(r["creditType"]) == 0 for r in self.dsl["instance_encounters"]
                            if 1095 <= r["entry"] <= 1098))

    def test_the_creature_set(self):
        mapping = self.entry["heroic_entries"]
        self.assertEqual(sorted(e for e in mapping if e < 300000), sorted(EXTRACTION_SET))
        for out in SKIPPED:  # Zelemar (skip=) and Maur (a friendly NPC): normal rows only
            self.assertNotIn(out, mapping)
        for kit in NO_HEROIC:
            self.assertNotIn(kit, mapping)
        self.assertEqual(BLOOD_GLOBULE in mapping, BLOOD_GLOBULE in self.declared)
        declared_rows = {int(r["entry"]) for r in self.dsl["creature_templates"] if not r.get(dungeon_heroic.DERIVED)}
        self.assertEqual(BLOOD_GLOBULE in mapping, BLOOD_GLOBULE in declared_rows)
        block = IDS["creature_heroic"]
        locked = heroic_templates.parse_lock(heroic_templates.LOCK_PATH.read_text()).pairs
        for normal, heroic in mapping.items():
            self.assertTrue(block["start"] <= heroic <= block["end"], (normal, heroic))
        self.assertEqual(len(set(mapping.values())), len(mapping))
        self.assertFalse(set(mapping.values()) & {h for n, h in locked.items() if n not in mapping})

    def test_the_predicted_lock_lines(self):
        """The ids the first write run mints: normal-entry order from 310488 (12 lines for the extraction set); the
        boss lootids are the same numbers. The Blood Globule follows at 310500 once its template is declared, and its
        `creature_template()` row must name that id in difficulty_entry_1."""
        mapping = self.entry["heroic_entries"]
        locked = heroic_templates.parse_lock(heroic_templates.LOCK_PATH.read_text()).pairs
        fresh = {n: h for n, h in mapping.items() if n not in locked}
        if set(fresh) != set(mapping):  # after the write run the lines are committed: the same numbers
            fresh = mapping
        self.assertEqual({e: h for e, h in fresh.items() if e < 300000}, PREDICTED)
        self.assertEqual(sorted(PREDICTED), sorted(PREDICTED, key=PREDICTED.get))  # ids follow the entry order
        for boss, heroic in HEROIC_LOOTID.items():
            self.assertEqual(fresh[boss], heroic, boss)
        if BLOOD_GLOBULE in fresh:
            self.assertEqual(fresh[BLOOD_GLOBULE], GLOBULE_HEROIC_ID)
        # nothing of this map is committed yet: the run appends one line per template (or none, after the write run)
        self.assertIn(len(self.out.lock_appended), (0, len(mapping)))

    def test_bosses(self):
        common = _load_common()
        rows = {int(r["entry"]): r for r in self.dsl["creature_templates"] if r.get(dungeon_heroic.DERIVED)}
        heroic_entry = self.entry["heroic_entries"]
        for boss, health in BOSS_HEALTH.items():
            with self.subTest(boss=boss):
                report = self.reports[boss]
                self.assertEqual(report.role, "boss")
                self.assertEqual(report.solved.health, health)
                self.assertEqual(report.solved.tier_row, "boss")
                row = rows[heroic_entry[boss]]
                self.assertEqual((row["minlevel"], row["maxlevel"], row["exp"]), (60, 60, 0))
                # 78 / 118 / 82 / 103: the generator stores the modifier a hair under (it rounds the health up)
                self.assertAlmostEqual(float(row["HealthModifier"]), BOSS_MODIFIER[boss], delta=0.001, msg=boss)
                self.assertEqual(int(row["CreatureImmunitiesId"]), common.IMMUNITY_BOSS_STUN)
                self.assertEqual(int(row["flags_extra"]), common.BOSS_FLAGS_EXTRA)  # bind + both assist flags
                self.assertEqual(int(row["flags_extra"]) & 1, 1)  # INSTANCE_BIND
                self.assertEqual(float(row["detection_range"]), common.BOSS_DETECTION_RANGE)
                self.assertEqual((row["AIName"], row["ScriptName"]), ("", ""))  # the normal entry's script runs
                lootid = boss if not OWN_LOOT else HEROIC_LOOTID[boss]
                self.assertEqual(int(row["lootid"]), lootid)
                self.assertEqual(int(row["KillCredit1"]), 0)

    def test_the_boss_melee_is_the_tiers_2500_a_swing_and_bazzalans_half_of_it(self):
        for boss in BOSS_HEALTH:
            solved = self.reports[boss].solved
            swing = (solved.min_damage + solved.max_damage) / 2 * 2000 / solved.swing_ms
            self.assertAlmostEqual(swing, BOSS_MELEE.get(boss, TIER_MELEE), delta=10, msg=boss)

    def test_the_trash_takes_the_tier_as_it_is(self):
        rows = {int(r["entry"]): r for r in self.dsl["creature_templates"] if r.get(dungeon_heroic.DERIVED)}
        heroic_entry = self.entry["heroic_entries"]
        for entry in TRASH:
            with self.subTest(entry=entry):
                report = self.reports[entry]
                self.assertEqual((report.role, report.solved.tier_row, report.solved.health),
                                 ("trash", "elite", 37_000))
                swing = (report.solved.min_damage + report.solved.max_damage) / 2 * 2000 / report.solved.swing_ms
                self.assertAlmostEqual(swing, 550, delta=5)
                row = rows[heroic_entry[entry]]
                self.assertEqual((row["minlevel"], row["maxlevel"]), (60, 60))
                self.assertEqual(int(row["flags_extra"]) & 1, 0)  # no bind on trash
        # the Warlock's Voidwalker (a level 42-56 stock unit) gets its own level 60 copy: a normal-rank minion
        minion = self.reports[8996]
        self.assertEqual((minion.role, minion.solved.tier_row, minion.solved.health), ("trash", "normal", 12_000))
        # the quest-only and skipped creatures are not on heroic as templates (Zelemar runs as its stock row)
        for entry in SKIPPED:
            self.assertNotIn(entry, self.reports)

    def test_the_stock_normal_rows_only_gain_difficulty_entry_1(self):
        """The four bosses' normal rows are edited by creature_template_columns() of the boss files, not here: this
        expansion adds only `difficulty_entry_1` (the engine link) to the 12 stock rows."""
        edits = [r for r in self.dsl.get("creature_template_edits", [])
                 if int(r["entry"]) in set(PREDICTED) and "difficulty_entry_1" in r]
        self.assertEqual({int(r["entry"]): int(r["difficulty_entry_1"]) for r in edits}, PREDICTED)

    def test_the_smart_ai_widening_is_the_shamans_three_normal_only_rows(self):
        blocks = _rendered_or_committed(self.out.smart_blocks, "UPDATE `smart_scripts` ")
        self.assertEqual(len(blocks), 1)
        block = blocks[0]
        self.assertEqual(set(re.findall(r"`entryorguid` = (\d+)", block)), {"11319"})
        self.assertEqual(block.count("`entryorguid` ="), 3)
        for boss in BOSS_HEALTH:  # the bosses' SmartAI is dropped by S0's rev, so nothing of theirs is widened
            self.assertNotIn(f"`entryorguid` = {boss} ", block)

    def test_every_spawn_goes_to_heroic(self):
        """By guid, not by a note's count: a later hand spawn (the entrance orc, normal only) changes the counts, and
        after the write run there is nothing left to set."""
        for table, names in (("creature", BOSS_SPAWN_GUIDS), ("gameobject", ())):
            blocks = _rendered_or_committed(self.out.spawn_blocks, f"UPDATE `{table}` ")
            self.assertTrue(blocks, table)
            guids = {int(g) for block in blocks for g in re.findall(r"\d+", block.split("`guid` IN (")[1])}
            self.assertTrue(set(names) <= guids, table)
            # every spawn of the map stands on heroic: set by these blocks, or carrying the bit already (D4H's two)
            for guid, row in self.out_live_spawns[table].items():
                if guid in guids or spawn_state.spawn_entry(row) == NORMAL_ONLY_ORC:
                    continue
                self.assertTrue(spawn_state.spawn_mask(row) & dungeon_heroic.HEROIC_SPAWN_BIT, (table, guid))

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
        self.assertEqual((by_id[1007]["MapID"], by_id[1007]["Difficulty"], by_id[1007]["MaxPlayers"]), (389, 1, 5))
        self.assertEqual({k: v for k, v in by_id.items() if k < 1000}, {r["ID"]: r for r in base})
        order = [(r["MapID"], r["Difficulty"]) for r in back]
        self.assertEqual(order, sorted(order))
        self.assertEqual(sum(1 for r in back if r["MapID"] == 389 and r["Difficulty"] == 1), 1)

        de_path = state.BASE_DBC_DIR / dbcfmt.DUNGEONENCOUNTER.dbc_filename
        base_de = dbcfile.read_dbc(de_path, dbcfmt.DUNGEONENCOUNTER)
        merged_de = {r["ID"]: r for r in base_de}
        merged_de.update(dungeon_heroic.client_encounter_rows(self.dsl["dungeon_encounters"]))
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / dbcfmt.DUNGEONENCOUNTER.dbc_filename
            path.write_bytes(dbcfile.pack_client_dbc(dbcfmt.DUNGEONENCOUNTER, list(merged_de.values()), base_de))
            back_de = dbcfile.read_dbc(path, dbcfmt.DUNGEONENCOUNTER)
        self.assertEqual(len(back_de), len(base_de) + 4)
        self.assertEqual(sorted(r["ID"] for r in back_de if r["MapID"] == 389 and r["Difficulty"] == 1),
                         [1095, 1096, 1097, 1098])
        self.assertEqual(sorted(r["ID"] for r in back_de if r["MapID"] == 389 and r["Difficulty"] == 0),
                         [430, 431, 432, 433])

    # --- the Finder -------------------------------------------------------------------------------------------

    def _rows(self):
        return {r["ID"]: r for r in self.dsl["lfg_dungeons"]}

    def test_the_heroic_entry(self):
        row = self._rows()[FINDER_HEROIC]
        stock = {r["ID"]: r for r in dbcfile.read_dbc(state.BASE_DBC_DIR / dbcfmt.LFGDUNGEONS.dbc_filename,
                                                      dbcfmt.LFGDUNGEONS)}
        self.assertEqual(row["Name_Lang_enUS"], "Ragefire Chasm")
        self.assertEqual((row["TypeID"], row["Difficulty"], row["Group_Id"], row["MapID"], row["Flags"]),
                         (5, 1, 12, 389, 3))
        self.assertEqual((row["MinLevel"], row["MaxLevel"]), (60, 62))
        self.assertEqual(row["TextureFilename"], stock[FINDER_NORMAL]["TextureFilename"])
        self.assertNotIn(FINDER_NORMAL, self._rows())  # the stock normal row stays as it is
        # stock entry 4 has no lfg_dungeon_template row (the Finder falls back to the areatrigger): the copy has none
        self.assertNotIn(FINDER_NORMAL, self.lfg_inputs.positions)
        self.assertNotIn(FINDER_HEROIC, {t["dungeonId"] for t in self.dsl["lfg_dungeon_templates"]})

    def test_the_heroic_taragaman_completes_the_heroic_entry(self):
        credits = {r["entry"]: r for r in self.dsl["instance_encounters"] if 1095 <= r["entry"] <= 1098}
        self.assertEqual({e: r["lastEncounterDungeon"] for e, r in credits.items()},
                         {1095: 0, 1096: 0, 1097: 0, 1098: FINDER_HEROIC})
        # the normal rows are stock: no edit of a normal link (431 already ends entry 4)
        self.assertEqual({r["entry"] for r in self.dsl["instance_encounters"] if r.get(lfg_dungeons.LINK)}, set())

    def test_the_client_lfg_file_gains_the_new_row_and_random_classic_heroic_draws_it(self):
        base = dbcfile.read_dbc(state.BASE_DBC_DIR / dbcfmt.LFGDUNGEONS.dbc_filename, dbcfmt.LFGDUNGEONS)
        merged = {r["ID"]: r for r in base}
        merged.update(lfg_dungeons.client_dungeon_rows(self.dsl["lfg_dungeons"]))
        new = set(merged) - {r["ID"] for r in base}
        self.assertIn(FINDER_HEROIC, new)
        pool = {i for i, r in merged.items() if r["Group_Id"] == 12 and r["TypeID"] == 5}
        self.assertIn(FINDER_HEROIC, pool)


if __name__ == "__main__":
    unittest.main()
