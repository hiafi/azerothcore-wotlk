"""
Blackrock Depths build WP-D17, the Grim Guzzler room: source/npcs/blackrock_depths/guzzler.py against its C++ numbers
(modules/mod-dungeon-bosses src/BlackrockDepths/GuzzlerLogic.h) and its SQL rev
(data/sql/updates/pending_db_world/rev_guzzler_blackrock_depths.sql).

Checks:
  - the two spell copies sit in the slice (211410-211429), GuzzlerLogic.h names the same ids, and they are copies of the
    stock Gouge 12540 (2 s incapacitate, stun aura, knockout mechanic) and Kick 15610 (3 s lockout, interrupt), never
    the stock ids;
  - the creature columns (read from the declaration, whatever BIND_WAVE_2 says; with the gate on the registry carries
    them, with it off nothing of the room): Ribbly -251 / Plugger 1972, no INSTANCE_BIND, health at 5 players, the
    patrons DamageModifier 1.5 and HealthModifier 0.6 / 0.6 / 1.5, SmartAI untouched (no AIName / ScriptName column);
  - the SQL rev rewrites the five SmartAI blocks whole (DELETE then INSERT), changes exactly five rows to the header's
    numbers, and every other column of every row is the stock row (a digest of the live 2026-11-17 rows);
  - the heroic health WP-H writes (source/world/dungeons/blackrock_depths.py) is the header's heroic numbers.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_guzzler.py
"""

from __future__ import annotations

import hashlib
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

from lib import test_id_blocks as id_blocks  # noqa: E402
from lib.dsl import registry  # noqa: E402

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockDepths"
HEADER = MODULE_DIR / "GuzzlerLogic.h"
SQL_REV = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_guzzler_blackrock_depths.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_depths"
HEROIC_FILE = TOOL_ROOT / "source" / "world" / "dungeons" / "blackrock_depths.py"

SLICE = range(211410, 211430)
GOUGE, KICK = 211410, 211411
RIBBLY, CRONY, PLUGGER, GRIM, GUZZLING, HAMMERED = 9543, 10043, 9499, 9545, 9547, 9554
ROOM = (RIBBLY, CRONY, PLUGGER, GRIM, GUZZLING, HAMMERED)

SCHOOL_NORMAL = 1
SCHOOL_DAMAGE, APPLY_AURA, INTERRUPT_CAST = 2, 6, 68
AURA_MOD_STUN = 12
MECHANIC_KNOCKOUT, MECHANIC_INTERRUPT = 14, 26
IMMUNITY_BOSS_STUN = 1972
INSTANCE_BIND = 0x1

# The columns of a smart_scripts row, in the order the rev writes them.
COLUMNS = ("entryorguid", "source_type", "id", "link", "event_type", "event_phase_mask", "event_chance", "event_flags",
           "event_param1", "event_param2", "event_param3", "event_param4", "event_param5", "event_param6",
           "action_type", "action_param1", "action_param2", "action_param3", "action_param4", "action_param5",
           "action_param6", "target_type", "target_param1", "target_param2", "target_param3", "target_param4",
           "target_x", "target_y", "target_z", "target_o", "comment")
# The stock blocks (live 2026-11-17 = base + updates): the row ids and a digest of every numeric column. 10043 (the
# Cronies) is never rewritten.
STOCK_IDS = {
    RIBBLY: [0, 1, 2, 3, 4, 5],
    PLUGGER: list(range(15)),
    GRIM: [0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14],
    GUZZLING: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15],
    HAMMERED: [0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13],
}
STOCK_DIGEST = {
    RIBBLY: "2302a7cfc8f47bc1", PLUGGER: "907c737a10b18951", GRIM: "8d9c92a6b5640346",
    GUZZLING: "89493cba33771568", HAMMERED: "a7f1eff7893b2ec1",
}
# (entry, id) -> {column: (stock value, new value)}: the five edited rows.
EDITS = {
    (RIBBLY, 4): {"action_param1": (12540, GOUGE)},
    (PLUGGER, 3): {"event_param3": (3000, 8000), "event_param4": (4000, 10000)},
    (GRIM, 0): {"action_param1": (15610, KICK)},
    (GUZZLING, 1): {"event_param3": (3000, 8000), "event_param4": (4000, 10000)},
    (HAMMERED, 0): {"event_param3": (5000, 10000), "event_param4": (8000, 12000)},
}


def _load(package: Path):
    t = id_blocks
    return registry.load_class_package(
        package, ids_cfg=t.IDS, trainer_index=t._AnyTrainer(), existing_group_ids=t._AnySet(),
        shapeshift_index={}, existing_creature_rows=t._AnyRows(),
        creature_columns=t.spell_tables.CREATURE_TEMPLATE_COLUMNS,
        creature_defaults=t.spell_tables.CREATURE_TEMPLATE_DEFAULTS,
        live_data=t.spell_tables.dsl_live_data(
            {}, t.spell_tables.load_live_item_template_rows,
            lambda: t.state.load_existing_rows(t.dbcfmt.SKILLLINEABILITY),
            lambda: t.state.load_stock_rows(t.dbcfmt.CHRCLASSES),
            lambda: t.state.load_stock_rows(t.dbcfmt.SKILLLINEABILITY),
        ),
    )


def _gate_on_package(tmp: Path) -> Path:
    """A package of two files: the real guzzler.py and a copy of _common.py with BIND_WAVE_2 = True (the room alone,
    so a sibling WP's half-written wave 2 file cannot break this test)."""
    text = (PACKAGE / "_common.py").read_text(encoding="utf-8")
    patched, count = re.subn(r"^BIND_WAVE_2\s*=\s*(True|False)\s*$", "BIND_WAVE_2 = True", text, flags=re.MULTILINE)
    assert count == 1
    (tmp / "_common.py").write_text(patched, encoding="utf-8")
    shutil.copy(PACKAGE / "guzzler.py", tmp / "guzzler.py")
    return tmp


def _header_text() -> str:
    return HEADER.read_text(encoding="utf-8")


def _header_int(name: str) -> int:
    match = re.search(rf"\b{name}\s*=\s*(-?\d+)u?;", _header_text())
    assert match, name
    return int(match.group(1))


def _header_float(name: str) -> float:
    match = re.search(rf"\b{name}\s*=\s*(-?[\d.]+)f;", _header_text())
    assert match, name
    return float(match.group(1))


def _header_nh(name: str) -> tuple[int, int]:
    match = re.search(rf"\b{name}\{{\s*(\d+),\s*(\d+)\s*\}}", _header_text())
    assert match, name
    return int(match.group(1)), int(match.group(2))


def _header_window(name: str) -> tuple[int, int]:
    match = re.search(rf"\b{name}\{{\s*(\d+),\s*(\d+)\s*\}}", _header_text())
    assert match, name
    return int(match.group(1)), int(match.group(2))


def _raw(spell: dict, column: str) -> int:
    return int((spell.get("raw_overrides") or {}).get(column, 0) or 0)


def parse_rows(sql: str) -> dict[int, list[list]]:
    """The INSERT ... VALUES tuples of the rev, by entryorguid: numbers as numbers, the comment as a string."""
    out: dict[int, list[list]] = {}
    for statement in re.split(r";\s*\n", sql):
        head = re.search(r"INSERT INTO `smart_scripts`.*?\bVALUES\b", statement, flags=re.S)
        if not head:
            continue
        body = statement[head.end():]
        i, n = 0, len(body)
        while i < n:
            if body[i] != "(":
                i += 1
                continue
            i += 1
            row, token = [], ""
            while body[i] != ")" or token.startswith("'") and not (len(token) > 1 and token.endswith("'")):
                ch = body[i]
                if token.startswith("'"):
                    if ch == "'" and body[i + 1] == "'":
                        token += "''"
                        i += 2
                        continue
                    token += ch
                    i += 1
                    continue
                if ch == "'":
                    token = "'"
                    i += 1
                    continue
                if ch == ",":
                    row.append(token.strip())
                    token = ""
                    i += 1
                    continue
                token += ch
                i += 1
            row.append(token.strip())
            i += 1
            values: list = []
            for item in row:
                if item.startswith("'"):
                    values.append(item[1:-1].replace("''", "'"))
                else:
                    values.append(float(item) if "." in item else int(item))
            out.setdefault(int(values[0]), []).append(values)
    return out


def digest(rows: list[list]) -> str:
    ordered = sorted(rows, key=lambda r: r[2])
    canon = "\n".join(",".join(str(int(float(v))) for v in row[:-1]) for row in ordered)
    return hashlib.sha256(canon.encode()).hexdigest()[:16]


class GuzzlerDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load(PACKAGE)
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits_gate_off = {int(e["entry"]) for e in reg.creature_template_edits if int(e["entry"]) in ROOM}
        with tempfile.TemporaryDirectory() as tmp:
            gate_on = _load(_gate_on_package(Path(tmp)))
        cls.edits = {}
        for e in gate_on.creature_template_edits:
            if int(e["entry"]) in ROOM:
                cls.edits.setdefault(int(e["entry"]), {}).update(e)
        cls.gate_on_spells = {int(e["id"]) for e in gate_on.spells}

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, [GOUGE, KICK])
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"spell": mine}), [])
        header = _header_text()
        offsets = {name: int(n) for name, n in re.findall(r"(SPELL_GZ_\w+)\s*=\s*kSpellSlice\.first \+ (\d+)", header)}
        self.assertEqual(offsets, {"SPELL_GZ_GOUGE": 0, "SPELL_GZ_KICK": 1})
        self.assertEqual(GOUGE + offsets["SPELL_GZ_KICK"], KICK)
        # The stock Gouge and Kick are never re-declared (rule 15); the copies are the cast ids of the SQL rev.
        for stock in (12540, 15610, 12739, 20825, 6253):
            self.assertNotIn(stock, self.spells)
        # The spells do not depend on the gate (the SQL rev casts them whatever it says).
        self.assertEqual({GOUGE, KICK} & self.gate_on_spells, {GOUGE, KICK})
        for sid in (GOUGE, KICK):
            self.assertNotIn(sid, {s for s, _ in self.scripts}, "a plain copy: no script")

    def test_gouge_is_the_stock_spell_with_a_two_second_incapacitate(self):
        gouge = self.spells[GOUGE]
        self.assertEqual(gouge["name"], "Gouge")
        self.assertEqual(gouge["school"], SCHOOL_NORMAL)
        self.assertEqual(gouge["mechanic"], MECHANIC_KNOCKOUT)
        self.assertEqual(gouge["duration_ms"], _header_int("kGougeIncapacitateMs"))
        self.assertEqual(gouge["duration_ms"], 2000)
        self.assertEqual(gouge["cast_time_ms"], 0)
        self.assertEqual(gouge["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertEqual(gouge["effect1"]["base_points"] + 1, 20)
        self.assertEqual(gouge["effect2"]["type"], APPLY_AURA)
        self.assertEqual(gouge["effect2"]["apply_aura"], AURA_MOD_STUN)
        self.assertEqual(_raw(gouge, "AuraInterruptFlags"), 2)             # damage breaks it, as stock
        self.assertEqual(_raw(gouge, "RangeIndex"), 2)                     # combat range
        self.assertEqual(_raw(gouge, "SpellVisualID_1"), 256)
        self.assertEqual(gouge["spell_icon_id"], 245)
        self.assertEqual(gouge["attributes"] & 0x10, 0x10)                 # IS_ABILITY, like stock
        self.assertEqual(gouge["attributes"] & 0x100000, 0x100000)         # stops his auto attack, like stock
        self.assertEqual(_header_int("kStockGougeIncapacitateMs"), 4000)

    def test_kick_is_the_stock_spell_with_a_three_second_lockout(self):
        kick = self.spells[KICK]
        self.assertEqual(kick["name"], "Kick")
        self.assertEqual(kick["school"], SCHOOL_NORMAL)
        self.assertEqual(kick["duration_ms"], _header_int("kKickLockoutMs"))
        self.assertEqual(kick["duration_ms"], 3000)
        self.assertEqual(kick["cast_time_ms"], 0)
        self.assertEqual(kick["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertEqual(kick["effect1"]["base_points"] + 1, 3)
        self.assertEqual(kick["effect1"]["points_per_level"], 1.5)
        self.assertEqual(kick["effect2"]["type"], INTERRUPT_CAST)
        self.assertEqual(kick["effect2"]["mechanic"], MECHANIC_INTERRUPT)
        self.assertEqual(_raw(kick, "BaseLevel"), 20)
        self.assertEqual(_raw(kick, "SpellLevel"), 20)
        self.assertEqual(_raw(kick, "RangeIndex"), 2)
        self.assertEqual(_raw(kick, "SpellVisualID_1"), 90)
        self.assertEqual(kick["spell_icon_id"], 246)
        self.assertEqual(_header_int("kStockKickLockoutMs"), 6000)

    def test_gate_off_declares_nothing_of_the_room(self):
        # BIND_WAVE_2 is read from _common.py: while it is False no creature column of the room is written.
        text = (PACKAGE / "_common.py").read_text(encoding="utf-8")
        gate = re.search(r"^BIND_WAVE_2\s*=\s*(True|False)\s*$", text, flags=re.MULTILINE).group(1) == "True"
        self.assertEqual(self.edits_gate_off, set(ROOM) if gate else set())

    def test_creature_columns_follow_the_build_spec(self):
        self.assertEqual(set(self.edits), set(ROOM))
        base = {RIBBLY: 2453, PLUGGER: 2091, CRONY: 2215}
        health = {RIBBLY: _header_nh("kRibblyHealth")[0], PLUGGER: _header_nh("kPluggerHealth")[0],
                  CRONY: _header_nh("kRibblyCronyHealth")[0]}
        for entry in (RIBBLY, PLUGGER, CRONY):
            edit = self.edits[entry]
            self.assertLessEqual(abs(math.ceil(base[entry] * edit["HealthModifier"]) - health[entry]), 2, entry)
            self.assertEqual(edit["DamageModifier"], 3.5)
        self.assertEqual(self.edits[RIBBLY]["HealthModifier"], _header_float("kRibblyHealthModifier"))
        self.assertEqual(self.edits[PLUGGER]["HealthModifier"], _header_float("kPluggerHealthModifier"))
        self.assertEqual(self.edits[CRONY]["HealthModifier"], _header_float("kRibblyCronyHealthModifier"))
        # Handoff section 10: no encounter credit (240, 241 dropped), so no INSTANCE_BIND (no flags_extra column: the
        # stock 0); Plugger 1972, Ribbly keeps his stock -251 (no immunity column; the heroic copy states -251).
        for entry in (RIBBLY, PLUGGER):
            self.assertNotIn("flags_extra", self.edits[entry])
        self.assertEqual(self.edits[PLUGGER]["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
        self.assertNotIn("CreatureImmunitiesId", self.edits[RIBBLY])
        self.assertEqual(_header_int("kBossImmunity"), IMMUNITY_BOSS_STUN)
        self.assertNotIn("CreatureImmunitiesId", self.edits[CRONY])
        # The patrons (ruling 65): 1.5 damage, 0.6 / 0.6 / 1.5 health, nothing else, normal rows on heroic.
        expected = {GRIM: "kGrimPatronHealthModifier", GUZZLING: "kGuzzlingPatronHealthModifier",
                    HAMMERED: "kHammeredPatronHealthModifier"}
        for entry, name in expected.items():
            edit = self.edits[entry]
            self.assertEqual(edit["HealthModifier"], _header_float(name))
            self.assertEqual(edit["DamageModifier"], _header_float("kPatronDamageModifier"))
            self.assertEqual(edit["DamageModifier"], 1.5)
            for column in ("CreatureImmunitiesId", "flags_extra"):
                self.assertNotIn(column, edit)
        self.assertEqual([self.edits[e]["HealthModifier"] for e in (GRIM, GUZZLING, HAMMERED)], [0.6, 0.6, 1.5])
        # SmartAI stays: no column of the room turns it off or binds a C++ script.
        for entry, edit in self.edits.items():
            for column in ("AIName", "ScriptName"):
                self.assertNotIn(column, edit, entry)

    def test_heroic_health_is_the_headers(self):
        text = HEROIC_FILE.read_text(encoding="utf-8")
        ribbly = re.search(r"9543: _boss\(([\d_]+)", text)
        plugger = re.search(r"9499: _boss\(([\d_]+)", text)
        crony = re.search(r"10043: dict\(health=([\d_]+)", text)
        self.assertTrue(ribbly and plugger and crony)
        self.assertEqual(int(ribbly.group(1).replace("_", "")), _header_nh("kRibblyHealth")[1])
        self.assertEqual(int(plugger.group(1).replace("_", "")), _header_nh("kPluggerHealth")[1])
        self.assertEqual(int(crony.group(1).replace("_", "")), _header_nh("kRibblyCronyHealth")[1])
        # The patrons have no heroic template (they run their normal rows): H does not mint them.
        self.assertNotIn("9545: dict(", text)


class GuzzlerSqlRevTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL_REV.read_text(encoding="utf-8")
        cls.rows = parse_rows(cls.sql)

    def test_five_blocks_each_deleted_then_inserted_whole(self):
        self.assertEqual(sorted(self.rows), sorted(STOCK_IDS))
        for entry, ids in STOCK_IDS.items():
            self.assertEqual(sorted(r[2] for r in self.rows[entry]), ids, entry)
            delete = f"DELETE FROM `smart_scripts` WHERE `entryorguid` = {entry} AND `source_type` = 0;"
            self.assertIn(delete, self.sql)
            self.assertLess(self.sql.index(delete), self.sql.index(f"({entry}, 0, {ids[0]},"))
        # Ribbly's Cronies and Plugger's actionlist are not touched.
        self.assertNotIn("`entryorguid` = 10043", self.sql)
        self.assertNotIn("source_type` = 9", self.sql)
        for row in (r for rows in self.rows.values() for r in rows):
            self.assertEqual(row[1], 0)
            self.assertEqual(len(row), len(COLUMNS))

    def test_exactly_five_rows_differ_from_stock_and_event_flags_are_kept(self):
        flags_col = COLUMNS.index("event_flags")
        for entry, rows in self.rows.items():
            reverted = []
            for row in rows:
                row = list(row)
                for column, (old, new) in EDITS.get((entry, row[2]), {}).items():
                    index = COLUMNS.index(column)
                    self.assertEqual(row[index], new, (entry, row[2], column))
                    row[index] = old
                reverted.append(row)
            self.assertEqual(digest(reverted), STOCK_DIGEST[entry], f"{entry}: a row besides the five edits differs")
            self.assertEqual(len(rows), len(STOCK_IDS[entry]))
        # The five edits keep their event_flags (stock 0 on all five): no row is new, so no `| 4`.
        for (entry, row_id) in EDITS:
            row = next(r for r in self.rows[entry] if r[2] == row_id)
            self.assertEqual(row[flags_col], 0)

    def test_the_numbers_are_the_headers(self):
        def row(entry, row_id):
            return next(r for r in self.rows[entry] if r[2] == row_id)
        col = COLUMNS.index
        self.assertEqual(row(RIBBLY, 4)[col("action_param1")], GOUGE)
        self.assertEqual(row(GRIM, 0)[col("action_param1")], KICK)
        shadow = _header_window("kShadowBoltRepeat")
        backhand = _header_window("kBackhandRepeat")
        for entry, row_id in ((PLUGGER, 3), (GUZZLING, 1)):
            r = row(entry, row_id)
            self.assertEqual((r[col("event_param3")], r[col("event_param4")]), shadow)
        r = row(HAMMERED, 0)
        self.assertEqual((r[col("event_param3")], r[col("event_param4")]), backhand)
        # What the edited rows still cast: the stock Shadow Bolt 12739 / 20825 and Backhand 6253, one cast each.
        self.assertEqual(row(PLUGGER, 3)[col("action_param1")], _header_int("SPELL_STOCK_PLUGGER_SHADOW_BOLT"))
        self.assertEqual(row(GUZZLING, 1)[col("action_param1")], _header_int("SPELL_STOCK_PATRON_SHADOW_BOLT"))
        self.assertEqual(row(HAMMERED, 0)[col("action_param1")], _header_int("SPELL_STOCK_BACKHAND"))
        # The first-cast windows are untouched (Plugger 1-2 s, Guzzling 3-4 s, Hammered 3-5 s).
        self.assertEqual((row(PLUGGER, 3)[col("event_param1")], row(PLUGGER, 3)[col("event_param2")]), (1000, 2000))
        self.assertEqual((row(HAMMERED, 0)[col("event_param1")], row(HAMMERED, 0)[col("event_param2")]), (3000, 5000))
        # The trigger rows the bar depends on are still there: Plugger's counter (ids 6-8), death (9-12), the Ribbly
        # gossip (0-3), the patrons' ale rows.
        self.assertEqual(row(PLUGGER, 8)[col("action_param1")], 949900)
        for row_id in (9, 10, 11, 12):
            self.assertEqual(row(PLUGGER, row_id)[col("action_param1")], _header_int("kFactionAllHostile"))
            self.assertEqual(row(PLUGGER, row_id)[col("target_param2")], 100)
        self.assertEqual(row(RIBBLY, 0)[col("event_param1")], _header_int("kRibblyGossipMenu"))
        self.assertEqual(row(RIBBLY, 1)[col("target_param2")], 30)

    def test_style(self):
        for number, line in enumerate(self.sql.splitlines(), start=1):
            self.assertLessEqual(len(line), 120, f"line {number}")
            self.assertEqual(line, line.rstrip(), f"line {number}")
            self.assertNotIn("\t", line)
        self.assertTrue(self.sql.endswith(";\n"))
        self.assertNotIn("\n\n\n", self.sql)


if __name__ == "__main__":
    unittest.main()
