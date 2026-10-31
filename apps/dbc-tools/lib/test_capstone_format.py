"""
Capstone tooltip format (Warrior T1 WP3; user rule 2026-10-28, it broke in the last few reworks).

A talent with a capstone bonus ends its `Description_Lang_enUS` with a separate paragraph, the same clause on every
rank, rank 1 included:

  - every rank below the last: `<text>\\n\\n|cFF9D9D9DCapstone Bonus: <clause>|r` (grey);
  - the last rank (and a single-rank talent): `<text>\\n\\nCapstone Bonus: <clause>`, no colour codes;
  - the label is exactly `Capstone Bonus: `, and the clause never goes in `AuraDescription_Lang_enUS`.

Three layers, all importable by a later class rework (`from lib import test_capstone_format`):
  - `rank_problems(talent_name, descriptions, aura_descriptions)`: the pure per-talent checker;
  - `load_class_talents(class_name)`: the class package through the real loader and row builder, each talent's rank
    descriptions resolved (declared rank spells, else the stock Spell.dbc row);
  - `capstone_problems(class_name, expected_names)`: the exact-set rule (every talent whose rank text says "capstone"
    is in the list, every listed talent is found and carries a valid clause on every rank) plus `rank_problems`.

`EXPECTED_CAPSTONES` below holds the talents each class's stages promise; the warrior test pins it.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_capstone_format.py
"""

from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from itertools import zip_longest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import build, dbcfmt, spell_tables, state, test_id_blocks  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.reuse import ReuseContext  # noqa: E402

CAPSTONE_LABEL = "Capstone Bonus: "
GREY = "|cFF9D9D9D"
RESET = "|r"
HOLDING_TAB = registry.RETIRED_TAB_ID  # retired talents (no ranks) sit on this tab

# Each class's capstone talents, by rank 1's spell name. Warrior: the 5 Protection talents live in the September build
# plus the two S1 adds (The Wall, Storm's Bulwark), four S2 Arms ones and the nine S3 Fury ones, so 20 now. Each
# spec stage's handoff names its talents (T1-HANDOFF C3, derived from the docs' Tooltip lines because only the Fury doc
# has a "Capstones" line): S1 added Storm's Bulwark and The Wall (S1 D25), S2 Arms' 5 (Improved Charge, Anger
# Management, Taste for Blood, Colossus Smash, Endless Rage), S3 Fury's 9 (Dance of Death, Merciless, Improved Cleave,
# Frenzied Blows, Improved Execute, Quick Execution, Intensify Rage, Unshackled Fury, Unending Fury). User 2026-10-30:
# Colossus Smash's Mastery line moved into its main text ("15% plus your Mastery"), so it is no longer a capstone.
# Other classes join with their own key when their rework next touches talents.
EXPECTED_CAPSTONES = {
    "warrior": frozenset({"Incite", "Improved Revenge", "Focused Rage", "Shield Cover", "Thunderstruck", "The Wall",
                          "Storm's Bulwark", "Improved Charge", "Anger Management", "Taste for Blood",
                          "Endless Rage", "Dance of Death", "Merciless", "Improved Cleave",
                          "Frenzied Blows", "Improved Execute", "Quick Execution", "Intensify Rage",
                          "Unshackled Fury", "Unending Fury"}),
}

_COLOUR_CODE_AT_END = re.compile(r"(\|c[0-9A-Fa-f]{8})([ \t\r\n]*)$")


def _rank_label(talent_name: str, index: int, spell_ids) -> str:
    spell = f" (spell {spell_ids[index]})" if spell_ids and index < len(spell_ids) else ""
    return f"{talent_name} rank {index + 1}{spell}"


def _clause_of(description: str) -> str | None:
    """The clause as the format would carry it, read leniently (for the rank-to-rank comparison only)."""
    at = description.find(CAPSTONE_LABEL)
    if at < 0:
        return None
    clause = description[at + len(CAPSTONE_LABEL):]
    return clause[:-len(RESET)] if clause.endswith(RESET) else clause


def _one_rank_problems(where: str, description: str, last: bool) -> list[str]:
    lowered = description.lower()
    if "capstone" not in lowered:
        return [f"{where}: no Capstone Bonus clause"]
    problems = []
    at = description.find(CAPSTONE_LABEL)
    if at < 0:
        at = lowered.find("capstone")  # a wrong label: the first mention is the best guess for where it starts
    head, tail = description[:at], description[at:]
    label_ok = tail.startswith(CAPSTONE_LABEL)
    if not label_ok:
        problems.append(
            f"{where}: the label must be exactly {CAPSTONE_LABEL!r}, found {tail[:len(CAPSTONE_LABEL) + 1]!r}"
        )
    # what sits between the text and the label: <two newlines>[<colour code>]
    code_match = _COLOUR_CODE_AT_END.search(head)
    code = code_match.group(1) if code_match else None
    before = head[:code_match.start()] if code_match else head
    if "capstone" in before.lower():  # an inline "Capstone: x" copied from a design doc, next to the paragraph
        problems.append(f"{where}: 'capstone' appears in the text before the Capstone Bonus paragraph (an inline "
                        f"doc copy?)")
    if code_match and code_match.group(2):
        problems.append(f"{where}: whitespace or a newline sits between the colour code and the label")
    if last:
        if code is not None:
            problems.append(f"{where}: the last rank must be plain (no colour code) but has {code}")
    elif code is None:
        problems.append(f"{where}: a rank below the last must be grey ({GREY}...{RESET}) but is plain")
    elif code != GREY:
        problems.append(f"{where}: the colour code must be exactly {GREY}, found {code}")
    closed_by_reset = not last and code is not None
    if before.endswith("\n\n\n"):
        problems.append(f"{where}: three or more newlines before the clause, expected exactly two")
    elif before.endswith("\n\n"):
        pass
    elif before.endswith("\n"):
        problems.append(f"{where}: one newline before the clause, expected exactly two")
    else:
        problems.append(f"{where}: the clause must follow two newlines directly, found {before[-6:]!r}")
    if label_ok:
        body = tail[len(CAPSTONE_LABEL):]
        if last:
            if code is not None and body.endswith(RESET):
                body = body[:-len(RESET)]  # the grey code is reported above; do not report its closing |r again
            if "|c" in body or RESET in body:
                problems.append(f"{where}: the last rank's paragraph must not contain a colour code")
            clause = body
        elif body.endswith(RESET):
            clause = body[:-len(RESET)]
            if RESET in clause or "|c" in clause:
                problems.append(f"{where}: the clause contains a colour code")
        else:
            clause = body
            if closed_by_reset:  # a plain lower rank is already reported as not grey
                problems.append(f"{where}: the grey paragraph is not closed by {RESET} at the end of the string")
        if not clause.strip():
            problems.append(f"{where}: the clause is empty")
        if re.search(r"capstone\s*(:|bonus)", clause, re.IGNORECASE):
            problems.append(f"{where}: a second label-like 'capstone:' / 'capstone bonus' inside the clause")
        if "\n" in clause or "\r" in clause:
            problems.append(f"{where}: a newline inside the clause")
    return problems


def rank_problems(talent_name: str, descriptions, aura_descriptions=(), spell_ids=None) -> list[str]:
    """Every way one talent's rank tooltips break the capstone format (empty list = valid). `descriptions` is rank
    1..N's `Description_Lang_enUS`, `aura_descriptions` the matching `AuraDescription_Lang_enUS` (may be shorter or
    empty); `spell_ids` only names the rank spells in the messages. Rules: every rank has the clause; a rank below the
    last is grey and closed by |r; the last (and a single) rank is plain; exactly two newlines before the paragraph and
    none inside it; the label is exactly `Capstone Bonus: ` and the colour code exactly `|cFF9D9D9D`; the clause is the
    same on every rank; no "capstone" in an aura description, none in the text before the paragraph, and no
    label-like `capstone:` inside the clause (the word itself is fine there: "similar capstone effects")."""
    problems = []
    total = len(descriptions)
    for index, (description, aura) in enumerate(zip_longest(descriptions, aura_descriptions, fillvalue="")):
        if index >= total:
            problems.append(f"{talent_name}: AuraDescription list is longer than the rank list")
            break
        where = _rank_label(talent_name, index, spell_ids)
        if "capstone" in (aura or "").lower():
            problems.append(f"{where}: the capstone clause is in AuraDescription_Lang_enUS, it belongs only in the "
                            f"description")
        problems.extend(_one_rank_problems(where, description or "", last=index == total - 1))
    first = _clause_of(descriptions[0]) if descriptions else None
    for index, description in enumerate(descriptions[1:], start=1):
        clause = _clause_of(description)
        if first is not None and clause is not None and clause != first:
            problems.append(f"{_rank_label(talent_name, index, spell_ids)}: the clause differs from rank 1's "
                            f"({clause!r} vs {first!r})")
    return problems


# --- the class package through the real loader ---------------------------------------------------------------------

_stock_spells: dict[int, dict] | None = None


def _stock_spell_rows() -> dict[int, dict]:
    global _stock_spells
    if _stock_spells is None:
        _stock_spells = state.load_stock_rows(dbcfmt.SPELL)
    return _stock_spells


def load_class_talents(class_name: str) -> list[dict]:
    """Every talent the class package declares (the holding tab's retired talents have no ranks and are skipped), as
    `{"name", "id", "tab_id", "spell_ids", "descriptions", "auras"}`. `name` is rank 1's `Name_Lang_enUS`; each rank is
    the declared spell built by `build.build_spell_row`, else the stock Spell.dbc row (an undeclared stock rank).
    Raises whatever the loader raises (druid and warlock need SpellShapeshiftForm.dbc, T0 report s1.2). Same loader
    arguments as `test_id_blocks.declared_ids`."""
    ids = test_id_blocks.IDS
    stock_talents = (
        state.load_stock_rows(dbcfmt.TALENT) if (state.BASE_DBC_DIR / dbcfmt.TALENT.dbc_filename).is_file() else {}
    )
    reg = registry.load_class_package(
        TOOL_ROOT / "source" / "classes" / class_name, ids_cfg=ids, trainer_index=test_id_blocks._AnyTrainer(),
        existing_group_ids=test_id_blocks._AnySet(), shapeshift_index={},
        existing_creature_rows=test_id_blocks._AnyRows(), creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
        creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS,
        live_data=spell_tables.dsl_live_data(
            stock_talents, spell_tables.load_live_item_template_rows,
            lambda: state.load_existing_rows(dbcfmt.SKILLLINEABILITY),
            lambda: state.load_stock_rows(dbcfmt.CHRCLASSES),
            lambda: state.load_stock_rows(dbcfmt.SKILLLINEABILITY),
        ),
    )
    stock = {name: list(state.load_stock_rows(table).values()) for name, table in {
        "spellcasttimes": dbcfmt.SPELLCASTTIMES, "spellduration": dbcfmt.SPELLDURATION,
        "spellrange": dbcfmt.SPELLRANGE, "spellradius": dbcfmt.SPELLRADIUS}.items()}
    reuse = ReuseContext(stock, ids)
    declared = {int(e["id"]): e for e in reg.spells}
    built: dict[int, dict] = {}
    talents = []
    for entry in reg.talents:
        rank_ids = [int(r) for r in (entry.get("rank_spell_ids") or []) if r]
        if int(entry["tab_id"]) == HOLDING_TAB or not rank_ids:
            continue
        rows = []
        for spell_id in rank_ids:
            if spell_id not in built:
                if spell_id in declared:
                    built[spell_id] = build.build_spell_row(declared[spell_id], reuse)
                else:
                    built[spell_id] = _stock_spell_rows().get(spell_id) or {}
            rows.append(built[spell_id])
        talents.append({
            "name": rows[0].get("Name_Lang_enUS") or f"<talent {entry['id']}: no rank 1 row>",
            "id": int(entry["id"]), "tab_id": int(entry["tab_id"]), "spell_ids": rank_ids,
            "descriptions": [r.get("Description_Lang_enUS", "") for r in rows],
            "auras": [r.get("AuraDescription_Lang_enUS", "") for r in rows],
        })
    return talents


def _says_capstone(talent: dict) -> bool:
    return any("capstone" in (text or "").lower() for text in (*talent["descriptions"], *talent["auras"]))


def capstone_problems(class_name: str, expected_names, talents: list[dict] | None = None) -> list[str]:
    """Problems for one class: the exact-set rule plus `rank_problems` for each listed talent. Every talent whose rank
    text mentions "capstone" (case-insensitive, description or aura description, any rank) must be in
    `expected_names`; every expected name must match exactly one talent, with a valid clause on every rank. `talents`
    replaces the loader (a test passes mutated copies of `load_class_talents`)."""
    if talents is None:
        talents = load_class_talents(class_name)
    expected = set(expected_names)
    problems = []
    for talent in talents:
        if _says_capstone(talent) and talent["name"] not in expected:
            problems.append(
                f"{class_name}: talent {talent['id']} ({talent['name']}) has capstone text but is not in the expected "
                f"capstone list"
            )
    for name in sorted(expected):
        matches = [t for t in talents if t["name"] == name]
        if len(matches) != 1:
            ids = [t["id"] for t in matches]
            problems.append(f"{class_name}: expected capstone talent {name!r} matches {len(matches)} talents {ids}")
            continue
        talent = matches[0]
        problems.extend(rank_problems(name, talent["descriptions"], talent["auras"], talent["spell_ids"]))
    return problems


# --- tests ---------------------------------------------------------------------------------------------------------

TEXT = "Increases your damage by $s1%."
CLAUSE = "Your Cleave hits 1 additional target."


def _grey(text=TEXT, clause=CLAUSE):
    return f"{text}\n\n{GREY}{CAPSTONE_LABEL}{clause}{RESET}"


def _plain(text=TEXT, clause=CLAUSE):
    return f"{text}\n\n{CAPSTONE_LABEL}{clause}"


def _problems(descriptions, auras=()):
    return rank_problems("Test Talent", descriptions, auras, [100 + i for i in range(len(descriptions))])


def _load_tooltips():
    spec = importlib.util.spec_from_file_location(
        "warrior_tooltips_under_test", TOOL_ROOT / "source" / "classes" / "warrior" / "_tooltips.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_paladin_desc():
    path = TOOL_ROOT / "source" / "classes" / "paladin" / "paladin_holy_ranks.py"
    source = path.read_text(encoding="utf-8")
    start = source.index("def _desc(")
    end = source.index("def _rank(")
    namespace: dict = {}
    exec(compile(source[start:end], str(path), "exec"), namespace)  # the helper is pure: no imports needed
    return namespace["_desc"]


class RankProblemsTest(unittest.TestCase):
    def assertOne(self, problems, fragment):
        self.assertEqual(len(problems), 1, problems)
        self.assertIn(fragment, problems[0])

    def assertHas(self, problems, fragment):
        self.assertTrue(any(fragment in p for p in problems), problems)

    def test_valid_shapes_pass(self):
        self.assertEqual(_problems([_grey("A 5%."), _grey("A 10%."), _plain("A 15%.")]), [])
        self.assertEqual(_problems([_grey(), _plain()]), [])
        self.assertEqual(_problems([_plain()]), [])  # a single-rank talent is plain
        self.assertEqual(_problems([_grey("Deals $s1% for $d."), _plain("Deals $s1% for $d.")]), [])
        # variables inside the clause, and an aura description that carries no capstone
        clause = "Hits $s2 more targets for $<dmg>."
        self.assertEqual(_problems([_grey(clause=clause), _plain(clause=clause)], ["Aura text.", ""]), [])

    def test_a_rank_without_the_clause_fails(self):
        problems = _problems([TEXT, _grey(), _plain()])
        self.assertOne(problems, "rank 1 (spell 100): no Capstone Bonus clause")
        self.assertOne(_problems([_grey(), TEXT, _plain()]), "rank 2 (spell 101): no Capstone Bonus clause")
        self.assertOne(_problems([_grey(), _grey(), TEXT]), "rank 3 (spell 102): no Capstone Bonus clause")
        self.assertOne(_problems([TEXT]), "rank 1 (spell 100): no Capstone Bonus clause")

    def test_a_grey_last_rank_and_a_plain_lower_rank_fail(self):
        self.assertOne(_problems([_grey(), _grey()]), "rank 2 (spell 101): the last rank must be plain")
        self.assertOne(_problems([_grey()]), "the last rank must be plain")
        self.assertOne(_problems([_plain(), _plain()]), "rank 1 (spell 100): a rank below the last must be grey")

    def test_the_two_newlines_come_before_the_colour_code(self):
        for text, fragment in (
            (f"{TEXT}\n{GREY}{CAPSTONE_LABEL}{CLAUSE}{RESET}", "one newline"),
            (f"{TEXT}\n\n\n{GREY}{CAPSTONE_LABEL}{CLAUSE}{RESET}", "three or more newlines"),
            (f"{TEXT} {GREY}{CAPSTONE_LABEL}{CLAUSE}{RESET}", "must follow two newlines directly"),
            (f"{TEXT}\n\n {GREY}{CAPSTONE_LABEL}{CLAUSE}{RESET}", "must follow two newlines directly"),
            (f"{TEXT}\n{GREY}\n{CAPSTONE_LABEL}{CLAUSE}{RESET}", "between the colour code and the label"),
            (f"{GREY}{TEXT}\n\n{CAPSTONE_LABEL}{CLAUSE}{RESET}", "must be grey"),
            (f"{TEXT}{GREY}\n\n{CAPSTONE_LABEL}{CLAUSE}{RESET}", "between the colour code and the label"),
            (f"{TEXT}\n\n|cFF9D\n9D9D{CAPSTONE_LABEL}{CLAUSE}{RESET}", "must follow two newlines directly"),
        ):
            with self.subTest(fragment=fragment, text=text):
                problems = _problems([text, _plain()])
                self.assertTrue(any(fragment in p and "rank 1" in p for p in problems), problems)

    def test_newline_counts_on_a_plain_last_rank(self):
        self.assertOne(_problems([_grey(), f"{TEXT}\n{CAPSTONE_LABEL}{CLAUSE}"]), "one newline")
        self.assertOne(_problems([_grey(), f"{TEXT}\n\n\n{CAPSTONE_LABEL}{CLAUSE}"]), "three or more newlines")
        self.assertOne(_problems([_grey(), f"{TEXT} {CAPSTONE_LABEL}{CLAUSE}"]), "must follow two newlines directly")
        # text that itself ends in a newline is the same as a third newline
        self.assertOne(_problems([_grey(), f"{TEXT}\n\n\n{CAPSTONE_LABEL}{CLAUSE}"]), "three or more newlines")

    def test_a_newline_inside_the_clause_fails(self):
        bad = "First half.\nSecond half."
        self.assertOne(_problems([_plain(clause=bad)]), "newline inside the clause")
        both = _problems([_grey(clause=bad), _plain(clause=bad)])
        self.assertEqual(len(both), 2, both)  # one per rank
        self.assertTrue(all("newline inside the clause" in p for p in both), both)
        self.assertHas(_problems([_grey(clause=bad), _plain()]), "rank 1 (spell 100): a newline inside the clause")

    def test_the_label_must_be_exact(self):
        for label in ("Capstone: ", "Capstone bonus: ", "Capstone Bonus:", "CAPSTONE BONUS: ", "capstone Bonus: "):
            with self.subTest(label=label):
                problems = _problems([_grey(), f"{TEXT}\n\n{label}{CLAUSE}"])
                self.assertOne(problems, "the label must be exactly 'Capstone Bonus: '")
                self.assertIn("rank 2", problems[0])
                grey_problems = _problems([f"{TEXT}\n\n{GREY}{label}{CLAUSE}{RESET}", _plain()])
                self.assertOne(grey_problems, "the label must be exactly")

    def test_the_colour_code_must_be_exact(self):
        for code in ("|cff9d9d9d", "|cFF9d9d9d", "|cFFFFFFFF", "|cFF808080"):
            with self.subTest(code=code):
                problems = _problems([f"{TEXT}\n\n{code}{CAPSTONE_LABEL}{CLAUSE}{RESET}", _plain()])
                self.assertOne(problems, f"the colour code must be exactly {GREY}, found {code}")

    def test_a_grey_paragraph_must_be_closed_and_end_there(self):
        self.assertOne(_problems([f"{TEXT}\n\n{GREY}{CAPSTONE_LABEL}{CLAUSE}", _plain()]), "not closed by |r")
        self.assertHas(
            _problems([f"{TEXT}\n\n{GREY}{CAPSTONE_LABEL}{CLAUSE}{RESET} More.", _plain()]),
            "rank 1 (spell 100): the grey paragraph is not closed by |r",
        )
        clause = f"A {RESET}B"
        self.assertHas(
            _problems([_grey(clause=clause), _plain(clause=clause)]), "rank 1 (spell 100): the clause contains"
        )
        self.assertHas(
            _problems([_grey(), _plain(clause=f"A {RESET}")]), "rank 2 (spell 101): the last rank's paragraph"
        )
        self.assertHas(_problems([_grey(), _plain(clause="|cFFFF0000Red|r")]), "the last rank's paragraph must not")

    def test_the_clause_must_match_on_every_rank(self):
        problems = _problems([_grey(), _grey(clause="Another clause."), _plain()])
        self.assertOne(problems, "rank 2 (spell 101): the clause differs from rank 1's")
        problems = _problems([_grey(), _plain(clause="Another clause.")])
        self.assertOne(problems, "rank 2 (spell 101): the clause differs")
        # a one-character difference still counts
        self.assertOne(_problems([_grey(), _plain(clause=CLAUSE + ".")]), "the clause differs")

    def test_an_empty_clause_fails(self):
        self.assertOne(_problems([_plain(clause="")]), "the clause is empty")
        self.assertHas(_problems([_grey(clause=""), _plain(clause="")]), "rank 1 (spell 100): the clause is empty")

    def test_capstone_in_an_aura_description_fails(self):
        problems = _problems([_grey(), _plain()], ["", f"{CAPSTONE_LABEL}{CLAUSE}"])
        self.assertOne(problems, "rank 2 (spell 101): the capstone clause is in AuraDescription_Lang_enUS")
        problems = _problems([_grey(), _plain()], ["A capstone effect.", ""])
        self.assertOne(problems, "rank 1 (spell 100): the capstone clause is in AuraDescription_Lang_enUS")

    def test_a_second_capstone_in_a_description_fails(self):
        self.assertOne(_problems([_plain("Capstone: also here.")]), "appears in the text before")
        self.assertHas(_problems([_grey("Capstone: also here."), _plain()]), "rank 1 (spell 100): 'capstone' appears")
        # the word inside a clause is real player information, not a second label (priest Shadow Affinity)
        self.assertEqual(_problems([_grey(clause="The capstone strikes."), _plain(clause="The capstone strikes.")]), [])
        shadow = "Does not stack with similar capstone effects."
        self.assertEqual(_problems([_grey(clause=shadow), _plain(clause=shadow)]), [])
        for bad in ("Capstone: x.", "A capstone bonus: x.", "Capstone Bonus: x."):
            with self.subTest(clause=bad):
                self.assertHas(_problems([_plain(clause=bad)]), "label-like 'capstone:'")

    def test_the_messages_name_the_talent_the_rank_and_the_spell(self):
        message = rank_problems("Shield Cover", [_grey(), TEXT], [], [200041, 200042])[0]
        self.assertTrue(message.startswith("Shield Cover rank 2 (spell 200042): "), message)


class DescHelperTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tooltips = _load_tooltips()
        cls.paladin_desc = staticmethod(_load_paladin_desc())

    def test_the_output_is_byte_identical_to_the_paladin_helper_and_the_literal_format(self):
        desc = self.tooltips._desc
        for text in (TEXT, "Hits $s1 times.", "A", "Two sentences. Both stay."):
            self.assertEqual(desc(text), self.paladin_desc(text))
            self.assertEqual(desc(text), text)
            self.assertEqual(desc(text, CLAUSE), self.paladin_desc(text, CLAUSE))
            self.assertEqual(desc(text, CLAUSE, last=True), self.paladin_desc(text, CLAUSE, last=True))
            self.assertEqual(desc(text, CLAUSE), f"{text}\n\n|cFF9D9D9DCapstone Bonus: {CLAUSE}|r")
            self.assertEqual(desc(text, CLAUSE, last=True), f"{text}\n\nCapstone Bonus: {CLAUSE}")

    def test_helper_output_passes_the_checker_for_one_two_and_three_ranks(self):
        for ranks in (1, 2, 3):
            with self.subTest(ranks=ranks):
                descriptions = [
                    self.tooltips._desc(f"Rank {i + 1} text $s1%.", CLAUSE, last=i == ranks - 1) for i in range(ranks)
                ]
                self.assertEqual(rank_problems("Helper Talent", descriptions, [""] * ranks), [])

    def test_the_guards_raise(self):
        desc = self.tooltips._desc
        for kwargs in (
            {"capstone": ""}, {"capstone": "   "}, {"capstone": "Has |cFF0000FFcolour|r"}, {"capstone": "has |r"},
            {"capstone": "has |c"}, {"capstone": "two\nlines"}, {"capstone": "carriage\rreturn"},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                desc(TEXT, **kwargs)
        for last in (False, True):
            with self.subTest(last=last), self.assertRaises(ValueError):
                desc(TEXT + "\n", CLAUSE, last=last)
        # no clause: nothing to guard, the text passes through even if it ends in a newline
        self.assertEqual(desc(TEXT + "\n"), TEXT + "\n")


class ExpectedCapstonesTest(unittest.TestCase):
    def test_every_class_in_expected_capstones_passes(self):
        # adding a class key to EXPECTED_CAPSTONES is how a rework opts in; "matches 0 talents" keeps it non-vacuous
        for class_name, names in sorted(EXPECTED_CAPSTONES.items()):
            with self.subTest(class_name=class_name):
                self.assertTrue(names, f"{class_name}: empty expected set")
                self.assertEqual(capstone_problems(class_name, names), [])


class LiveWarriorPackageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.talents = load_class_talents("warrior")
        cls.expected = EXPECTED_CAPSTONES["warrior"]

    def _copy(self):
        return [{**t, "descriptions": list(t["descriptions"]), "auras": list(t["auras"])} for t in self.talents]

    def test_the_live_package_passes(self):
        self.assertEqual(capstone_problems("warrior", self.expected, talents=self.talents), [])

    def test_the_check_is_not_vacuous(self):
        found = [t for t in self.talents if _says_capstone(t)]
        self.assertEqual({t["name"] for t in found}, set(self.expected))
        self.assertEqual(len(found), 20)
        # S1: 3 + 2 + 3 + 3 + 3 + 2 + 3 ranks; S2: Improved Charge 2 + Anger Management 3 + Taste for Blood 3 +
        # Endless Rage 2 (Colossus Smash dropped 2026-10-30); S3: Dance of Death 3 + Merciless 3 + Improved Cleave 3 + Frenzied Blows 2 +
        # Improved Execute 2 + Quick Execution 3 + Intensify Rage 3 + Unshackled Fury 3 + Unending Fury 3
        self.assertEqual(sum(len(t["descriptions"]) for t in found), 54)
        # the loader resolved every rank to a row with a description (an unresolved rank would be an empty string)
        self.assertTrue(all(all(d for d in t["descriptions"]) for t in found))

    def test_dropping_the_grey_code_from_one_loaded_rank_fails_exactly_that_rank(self):
        talents = self._copy()
        incite = next(t for t in talents if t["name"] == "Incite")
        self.assertIn(GREY, incite["descriptions"][1])
        incite["descriptions"][1] = incite["descriptions"][1].replace(GREY, "")
        problems = capstone_problems("warrior", self.expected, talents=talents)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn(f"Incite rank 2 (spell {incite['spell_ids'][1]})", problems[0])
        self.assertIn("a rank below the last must be grey", problems[0])

    def test_a_listed_talent_without_a_clause_fails_with_its_missing_ranks(self):
        # Resolve (200046-200048) is a Protection talent with no capstone: listing it must fail
        problems = capstone_problems("warrior", self.expected | {"Resolve"}, talents=self.talents)
        resolve = next(t for t in self.talents if t["name"] == "Resolve")
        self.assertEqual(
            problems,
            [f"Resolve rank {i + 1} (spell {spell_id}): no Capstone Bonus clause"
             for i, spell_id in enumerate(resolve["spell_ids"])],
        )
        self.assertEqual([200046, 200047, 200048], resolve["spell_ids"])

    def test_an_unlisted_talent_with_inline_capstone_text_fails_the_set_rule(self):
        talents = self._copy()
        victim = next(t for t in talents if t["name"] == "Resolve")
        victim["descriptions"][0] += " Capstone: 5% more."
        problems = capstone_problems("warrior", self.expected, talents=talents)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("(Resolve) has capstone text but is not in the expected capstone list", problems[0])

    def test_an_expected_name_that_matches_nothing_or_twice_is_a_problem(self):
        problems = capstone_problems("warrior", self.expected | {"No Such Talent"}, talents=self.talents)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("'No Such Talent' matches 0 talents []", problems[0])
        talents = self._copy()
        talents.append({**next(t for t in talents if t["name"] == "Incite"), "id": 99999})
        problems = capstone_problems("warrior", self.expected, talents=talents)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("'Incite' matches 2 talents", problems[0])

    def test_an_unlisted_talent_with_capstone_only_in_its_aura_description_fails_the_set_rule(self):
        talents = self._copy()
        victim = next(t for t in talents if t["name"] == "Resolve")
        victim["auras"][0] = "Capstone Bonus: x"
        problems = capstone_problems("warrior", self.expected, talents=talents)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("has capstone text but is not in the expected capstone list", problems[0])

    def test_a_clause_in_an_aura_description_of_a_loaded_rank_fails(self):
        talents = self._copy()
        focused = next(t for t in talents if t["name"] == "Focused Rage")
        focused["auras"][0] = "Capstone Bonus: x"
        problems = capstone_problems("warrior", self.expected, talents=talents)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("Focused Rage rank 1", problems[0])
        self.assertIn("AuraDescription_Lang_enUS", problems[0])


if __name__ == "__main__":
    unittest.main()
