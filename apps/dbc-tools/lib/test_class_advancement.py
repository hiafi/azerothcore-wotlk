"""
Class Advancement UI, stage U1: the class talent / ability table (write_class_advancement.py). The rule and rendering
tests use fixtures; the data tests build the real table from the source tree (the whole DSL, 30 to 80 s, once per run;
they need the stock DBCs in var/extractors/dbc and are skipped without them), render it, read the Lua back with a small
parser and check it.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_class_advancement.py

An optional check loads the generated file in a real Lua 5.1 when the `lupa` package is importable
(`pip install lupa` into a venv); it is skipped otherwise.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

import write_class_advancement as W  # noqa: E402
from lib import state  # noqa: E402

try:
    from lupa import lua51 as _lua51  # noqa: E402
except ImportError:  # optional, see the module docstring
    _lua51 = None

# TalentTab ids in the order the stock talent frame shows them (OrderIndex), per class.
TAB_ORDER = {
    "WARRIOR": [161, 164, 163], "PALADIN": [382, 383, 381], "HUNTER": [361, 363, 362], "ROGUE": [182, 181, 183],
    "PRIEST": [201, 202, 203], "DEATHKNIGHT": [398, 399, 400], "SHAMAN": [261, 263, 262], "MAGE": [81, 41, 61],
    "WARLOCK": [302, 303, 301], "DRUID": [283, 281, 282],
}
ALLIANCE_RACES = 0x44D  # human, dwarf, night elf, gnome, draenei
HORDE_RACES = 0x2B2  # orc, undead, tauren, troll, blood elf

_TOKEN = re.compile(r'\s*(?:(?P<num>-?\d+)|(?P<name>[A-Za-z_]\w*)|"(?P<str>(?:[^"\\]|\\.)*)"|(?P<sym>[{}\[\]=,]))')
_ESCAPE = re.compile(r"\\(\d{3}|.)")
_SIMPLE = {"n": "\n", "r": "\r", "t": "\t", "\\": "\\", '"': '"'}


def _unescape(text: str) -> str:
    return _ESCAPE.sub(lambda m: chr(int(m[1])) if m[1].isdigit() else _SIMPLE[m[1]], text)


def parse_lua(text: str) -> dict:
    """The assignments of a generated file (`NAME = { ... }`, nested tables, integers and strings only) as a dict.
    Raises ValueError on anything else, which is what keeps the generator to that subset."""
    text = "\n".join(line for line in text.split("\n") if not line.lstrip().startswith("--"))
    tokens: list[tuple[str, object]] = []
    pos = 0
    while text[pos:].strip():
        m = _TOKEN.match(text, pos)
        if m is None:
            raise ValueError(f"cannot read Lua at {text[pos:pos + 40]!r}")
        pos = m.end()
        kind = m.lastgroup
        tokens.append((kind, int(m[kind]) if kind == "num" else _unescape(m[kind]) if kind == "str" else m[kind]))
    index = 0

    def take(kind: str | None = None, value: object = None):
        nonlocal index
        token = tokens[index]
        if (kind and token[0] != kind) or (value is not None and token[1] != value):
            raise ValueError(f"expected {kind} {value!r}, got {token!r} at token {index}")
        index += 1
        return token[1]

    def value():
        kind, tok = tokens[index]
        if kind in ("num", "str"):
            return take()
        return table()

    def table():
        take("sym", "{")
        keyed: dict = {}
        listed: list = []
        while tokens[index] != ("sym", "}"):
            if tokens[index][0] == "name" and tokens[index + 1] == ("sym", "="):
                key = take("name")
                take("sym", "=")
                keyed[key] = value()
            elif tokens[index] == ("sym", "["):
                take("sym", "[")
                key = value()
                take("sym", "]")
                take("sym", "=")
                keyed[key] = value()
            else:
                listed.append(value())
            if tokens[index] == ("sym", ","):
                take()
        take("sym", "}")
        if keyed and listed:
            raise ValueError("a table mixing keys and list items")
        return keyed if keyed or not listed else listed

    out = {}
    while index < len(tokens):
        name = take("name")
        take("sym", "=")
        out[name] = table()
    return out


class RulesTest(unittest.TestCase):
    """Fixtures only."""

    def test_lua_string_escapes(self):
        self.assertEqual(W.lua_string('a"b\\c\n\x01é'), '"a\\"b\\\\c\\n\\001é"')
        self.assertEqual(_unescape(W.lua_string('a"b\\c\n\x01é')[1:-1]), 'a"b\\c\n\x01é')

    def test_render_and_parse_round_trip(self):
        table = {}
        for token, class_id in W.CLASSES:
            table[token] = {"classId": class_id, "tabs": [
                {"id": 1, "name": 'Arc"ane', "art": "MageArcane", "skillLine": 237,
                 "icon": "Interface\\Icons\\Spell_Holy_MagicalSentry", "talents": [
                    {"id": 74, "row": 0, "col": 1, "ranks": [11210, 12592]},
                    {"id": 75, "row": 2, "col": 0, "ranks": [11213], "req": 74, "reqRank": 1},
                ]},
            ], "abilities": [
                {"spell": 133, "section": 2, "level": 1, "how": "start"},
                {"spell": 11366, "section": 2, "how": "talent", "talent": 36},
                {"spell": 2825, "section": 1, "level": 60, "how": "trainer", "races": 178},
            ]}
        text = W.render_lua(table)
        self.assertNotIn("\r", text)
        self.assertTrue(text.endswith("}\n"))
        self.assertTrue(all(len(line) <= 120 for line in text.split("\n")))
        parsed = parse_lua(text)
        self.assertEqual(parsed["CLASS_ADVANCEMENT_ORDER"][0], "WARRIOR")
        self.assertEqual(list(parsed["CLASS_ADVANCEMENT"]), [token for token, _ in W.CLASSES])
        mage = parsed["CLASS_ADVANCEMENT"]["MAGE"]
        self.assertEqual(mage["tabs"][0]["name"], 'Arc"ane')
        self.assertEqual(mage["tabs"][0]["talents"][1], {"id": 75, "row": 2, "col": 0, "ranks": [11213],
                                                         "req": 74, "reqRank": 1})
        self.assertEqual(mage["abilities"][1], {"spell": 11366, "section": 2, "how": "talent", "talent": 36})
        self.assertEqual(mage["abilities"][2]["races"], 178)
        self.assertEqual(mage["tabs"][0]["icon"], "Interface\\Icons\\Spell_Holy_MagicalSentry")
        self.assertIn('icon = "Interface\\\\Icons\\\\Spell_Holy_MagicalSentry"', text)

    def test_parse_rejects_what_the_generator_must_not_write(self):
        with self.assertRaises(ValueError):
            parse_lua("X = { 1.5 }")
        with self.assertRaises(ValueError):
            parse_lua("X = { a = 1, 2 }")

    @staticmethod
    def _spell(attributes: int = 0, effects: tuple = ((2, 0, 0),)) -> dict:
        row = {"Attributes": attributes}
        for n in (1, 2, 3):
            kind, aura, trigger = effects[n - 1] if n <= len(effects) else (0, 0, 0)
            row.update({f"Effect_{n}": kind, f"EffectAura_{n}": aura, f"EffectTriggerSpell_{n}": trigger})
        return row

    def test_ability_exclusion(self):
        self.assertIsNone(W.ability_exclusion(self._spell()))
        self.assertIsNone(W.ability_exclusion(self._spell(0x40, ((6, 4, 0),))))            # a passive stays
        self.assertEqual(W.ability_exclusion(self._spell(0x80)), "hidden")
        self.assertIn("proficiency", W.ability_exclusion(self._spell(0x40, ((W.SPELL_EFFECT_PROFICIENCY, 0, 0),))))
        self.assertIn("proficiency", W.ability_exclusion(self._spell(0, ((25, 0, 0),))))  # weapon skill
        self.assertEqual(W.ability_exclusion(self._spell(0, ((W.SPELL_EFFECT_APPLY_AURA, W.SPELL_AURA_MOUNTED, 0),))),
                         "mount")
        self.assertIsNone(W.ability_exclusion(self._spell(0, ((40, 0, 0),))))              # Dual Wield stays

    def test_sort_key_orders_section_level_talents_last_name(self):
        inp = W.Inputs({}, {}, {1: {"Name_Lang_enUS": "Zap"}, 2: {"Name_Lang_enUS": "alpha"},
                              3: {"Name_Lang_enUS": "Mid"}, 4: {"Name_Lang_enUS": "Beta"}}, {}, {}, {}, {}, {})
        entries = [
            {"spell": 4, "section": 1, "how": "talent", "talent": 9},
            {"spell": 1, "section": 1, "how": "trainer", "level": 20},
            {"spell": 2, "section": 1, "how": "trainer", "level": 4},
            {"spell": 3, "section": 0, "how": "trainer", "level": 60},
        ]
        entries.sort(key=lambda entry: W.sort_key(inp, entry))
        self.assertEqual([e["spell"] for e in entries], [3, 2, 1, 4])

    def test_chains_name_the_highest_rank_that_exists(self):
        chains = W._Chains({100: [(100, 1), (101, 2), (102, 3)]}, {100: {}, 101: {}})
        self.assertEqual((chains.top_of(100), chains.top_of(101), chains.top_of(7)), (101, 101, 7))
        self.assertEqual(chains.family(100), [100, 101])


@unittest.skipUnless((state.BASE_DBC_DIR / "Spell.dbc").is_file(), "no stock Spell.dbc in var/extractors/dbc")
class TableTest(unittest.TestCase):
    """The real table, built once."""

    @classmethod
    def setUpClass(cls):
        cls.result, cls.inp = W.compute()
        cls.table = cls.result.table
        cls.text = W.render_lua(cls.table)
        cls.parsed = parse_lua(cls.text)

    def test_rendered_file_reads_back_to_the_table(self):
        self.assertEqual(self.parsed["CLASS_ADVANCEMENT"], self.table)
        self.assertEqual(self.parsed["CLASS_ADVANCEMENT_ORDER"], [token for token, _ in W.CLASSES])
        self.assertNotIn("\r", self.text)
        self.assertTrue(self.text.endswith("}\n"))
        self.assertTrue(all(len(line) <= 120 for line in self.text.split("\n")))
        self.assertEqual(self.text, W.render_lua(self.table))  # deterministic

    def test_ten_classes_three_tabs(self):
        self.assertEqual(list(self.table), [token for token, _ in W.CLASSES])
        for token, class_id in W.CLASSES:
            entry = self.table[token]
            self.assertEqual(entry["classId"], class_id)
            self.assertEqual(len(entry["tabs"]), 3, token)
            self.assertNotIn(W.RETIRED_TAB_ID, [tab["id"] for tab in entry["tabs"]])
            for tab in entry["tabs"]:
                self.assertTrue(tab["name"] and tab["art"], tab)
                self.assertIn(tab["skillLine"], self.inp.skill_lines)
            self.assertEqual([tab["id"] for tab in entry["tabs"]], TAB_ORDER[token], token)
            for tab in entry["tabs"]:
                self.assertTrue(tab["icon"].startswith("Interface\\Icons\\"), tab)
            self.assertEqual(len({tab["skillLine"] for tab in entry["tabs"]}), 3, token)

    def test_talents(self):
        seen: set[int] = set()
        for token, entry in self.table.items():
            for tab in entry["tabs"]:
                cells = [(t["row"], t["col"]) for t in tab["talents"]]
                self.assertEqual(cells, sorted(cells), f"{token} {tab['name']}: talents not in row, col order")
                self.assertEqual(len(cells), len(set(cells)), f"{token} {tab['name']}: two talents in one cell")
                by_id = {t["id"]: t for t in tab["talents"]}
                for t in tab["talents"]:
                    self.assertNotIn(t["id"], seen, f"talent {t['id']} twice")
                    seen.add(t["id"])
                    self.assertTrue(0 <= t["row"] <= 10 and 0 <= t["col"] <= 3, t)
                    self.assertTrue(t["ranks"] and all(r > 0 for r in t["ranks"]), t)
                    for rank_spell in t["ranks"]:
                        self.assertIn(rank_spell, self.inp.spells, f"talent {t['id']} rank spell {rank_spell}")
                    self.assertEqual("req" in t, "reqRank" in t, t)
                    if "req" in t:
                        self.assertIn(t["req"], by_id, f"{token} talent {t['id']}: prerequisite is in another tab")
                        # stock Mage trees keep three horizontal arrows (same row), so "lower" means "not higher"
                        self.assertLessEqual(by_id[t["req"]]["row"], t["row"], t)
                        self.assertNotEqual(t["req"], t["id"])
                        self.assertTrue(1 <= t["reqRank"] <= len(by_id[t["req"]]["ranks"]), t)

    def test_abilities(self):
        for token, entry in self.table.items():
            talents = {t["id"] for tab in entry["tabs"] for t in tab["talents"]}
            spells = [a["spell"] for a in entry["abilities"]]
            self.assertEqual(len(spells), len(set(spells)), f"{token}: an ability twice")
            for a in entry["abilities"]:
                self.assertIn(a["spell"], self.inp.spells, a)
                self.assertIn(a["section"], (0, 1, 2, 3), a)
                self.assertIn(a["how"], ("trainer", "start", "talent"), a)
                if a["how"] == "talent":
                    self.assertIn(a["talent"], talents, f"{token}: {a}")
                    self.assertNotIn("level", a)
                    tab_of = next(i for i, tab in enumerate(entry["tabs"], 1)
                                  if any(t["id"] == a["talent"] for t in tab["talents"]))
                    self.assertEqual(a["section"], tab_of, a)
                else:
                    self.assertNotIn("talent", a)
                    self.assertTrue(1 <= a["level"] <= 80, a)
            for section in (1, 2, 3):
                self.assertTrue(any(a["section"] == section for a in entry["abilities"]), f"{token}: section {section}")
            keys = [W.sort_key(self.inp, a) for a in entry["abilities"]]
            self.assertEqual(keys, sorted(keys), f"{token}: abilities not sorted")

    def test_nothing_excluded_got_in(self):
        for token, entry in self.table.items():
            for a in entry["abilities"]:
                self.assertIsNone(W.ability_exclusion(self.inp.spells[a["spell"]]), f"{token}: {a}")
                if a["how"] == "talent":
                    self.assertFalse(W.is_passive(self.inp.spells[a["spell"]]), f"{token}: {a}")

    def test_spot_checks(self):
        def ability(token: str, spell: int) -> dict:
            return next(a for a in self.table[token]["abilities"] if a["spell"] == spell)

        self.assertEqual(ability("DRUID", 200333), {"spell": 200333, "section": 1, "level": 22, "how": "trainer"})
        self.assertEqual(ability("DEATHKNIGHT", 203001), {"spell": 203001, "section": 3, "level": 12, "how": "trainer"})
        self.assertEqual(ability("MAGE", 133), {"spell": 133, "section": 2, "level": 1, "how": "start"})
        self.assertEqual(ability("MAGE", 11366), {"spell": 11366, "section": 2, "how": "talent", "talent": 29})
        # a retired stock talent's spell that became baseline stays (SkillLineAbility 19182, AcquireMethod 2)
        self.assertEqual(ability("DEATHKNIGHT", 55050), {"spell": 55050, "section": 1, "level": 1, "how": "start"})
        self.assertEqual([tab["name"] for tab in self.table["MAGE"]["tabs"]], ["Arcane", "Fire", "Frost"])
        self.assertEqual([tab["skillLine"] for tab in self.table["MAGE"]["tabs"]], [237, 8, 6])
        self.assertEqual(self.table["MAGE"]["tabs"][0]["art"], "MageArcane")
        talents = {t["id"]: t for tab in self.table["MAGE"]["tabs"] for t in tab["talents"]}
        self.assertEqual(talents[1849]["req"], 1735)  # a stock DependsOn: Fire row 8 needs Dragon's Breath
        self.assertEqual(talents[1849]["reqRank"], 1)

    def test_faction_abilities_carry_race_masks(self):
        raced = [(token, a) for token, entry in self.table.items() for a in entry["abilities"] if "races" in a]
        self.assertEqual(len(raced), 26)  # 24 Mage teleports and portals, Bloodlust, Heroism
        self.assertEqual({token for token, _a in raced}, {"MAGE", "SHAMAN"})
        for token, a in raced:
            self.assertTrue(a["races"] & W.PLAYABLE_RACES != W.PLAYABLE_RACES, a)
            self.assertTrue(a["races"] & ~ALLIANCE_RACES == 0 or a["races"] & ~HORDE_RACES == 0, f"{token}: {a}")
        by_name: dict[tuple[str, str], list[int]] = {}
        for token, a in raced:
            by_name.setdefault((token, W._spell_name(self.inp, a["spell"])), []).append(a["races"])
        pairs = {key: masks for key, masks in by_name.items() if len(masks) > 1}
        self.assertIn(("MAGE", "Teleport: Shattrath"), pairs)
        self.assertIn(("MAGE", "Portal: Shattrath"), pairs)
        for key, masks in pairs.items():
            for i, first in enumerate(masks):
                for second in masks[i + 1:]:
                    self.assertEqual(first & second, 0, f"{key}: masks {first} and {second} overlap")
        mage = {a["spell"]: a.get("races") for a in self.table["MAGE"]["abilities"]}
        self.assertTrue(mage[3561] & ALLIANCE_RACES and not mage[3561] & HORDE_RACES)  # Teleport: Stormwind
        self.assertTrue(mage[3567] & HORDE_RACES and not mage[3567] & ALLIANCE_RACES)  # Teleport: Orgrimmar
        self.assertIsNone(mage[116])  # Frostbolt is for everyone

    @unittest.skipIf(_lua51 is None, "lupa (Lua 5.1) is not installed")
    def test_file_loads_in_lua_51(self):
        lua = _lua51.LuaRuntime()
        lua.execute(self.text)
        advancement = lua.globals().CLASS_ADVANCEMENT
        self.assertEqual(advancement.MAGE.classId, 8)
        self.assertEqual(len(advancement.MAGE.abilities), len(self.table["MAGE"]["abilities"]))
        self.assertEqual(lua.globals().CLASS_ADVANCEMENT_ORDER[10], "DRUID")


if __name__ == "__main__":
    unittest.main()
