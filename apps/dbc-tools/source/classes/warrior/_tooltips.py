"""
Warrior - tooltip string helpers shared by the Protection, Arms and Fury stages.

Leading underscore = not loaded as a class file by lib/dsl/registry.py's load_class_package (see
source/classes/README.md), just an importable module - `from . import _tooltips as t` or
`from ._tooltips import _desc`.

Capstone tooltip rule (user rule 2026-10-28, warrior-rework.IMPLEMENTATION-HANDOFF.md "Capstone tooltips"; it broke in
the last few reworks, so lib/test_capstone_format.py enforces it): a talent with a capstone bonus ends its
`Description_Lang_enUS` with a separate paragraph, the same clause on every rank, rank 1 included:

  - every rank below the last: `<text>\\n\\n|cFF9D9D9DCapstone Bonus: <clause>|r` (grey, the two newlines BEFORE the
    colour code, `|r` closes the string);
  - the last rank: `<text>\\n\\nCapstone Bonus: <clause>` with no colour codes, so it renders in normal colour;
  - a single-rank talent has only a last rank: pass `last=True`.

The clause never goes in `AuraDescription_Lang_enUS`. Build every capstone string with `_desc`, never hand-write the
colour codes per row. The design docs write capstones inline ("... by 5/10/15%. Capstone: Your Cleave strikes 1
additional target."): render that as the paragraph above, not as the inline form.

    _desc("Increases your damage by 5%.", "Cleave hits 1 additional target.", last=False)
    _desc("Increases your damage by 15%.", "Cleave hits 1 additional target.", last=True)
    _desc("Rank text with no capstone")  # -> the text unchanged
"""


def _desc(text, capstone=None, last=False):
    """The rank description for a talent with (or without) a capstone clause. Output is byte-identical to
    `paladin_holy_ranks._desc` (HOLY section 5): `capstone=None` -> `text`; `last` -> plain paragraph; else grey.

    Raises ValueError for input the in-game tooltip would mangle: an empty clause, a clause with a colour code
    (`|c`, `|r`) or a newline, or a `text` that already ends in a newline (the paragraph break must be exactly two)."""
    if capstone is None:
        return text
    if not capstone.strip():
        raise ValueError("_desc(): the capstone clause is empty")
    if "|c" in capstone or "|r" in capstone:
        raise ValueError(f"_desc(): the capstone clause must not contain a colour code: {capstone!r}")
    if "\n" in capstone or "\r" in capstone:
        raise ValueError(f"_desc(): the capstone clause must not contain a newline: {capstone!r}")
    if text.endswith("\n"):
        raise ValueError(f"_desc(): the text must not end in a newline (the paragraph break adds two): {text!r}")
    if last:
        return f"{text}\n\nCapstone Bonus: {capstone}"
    return f"{text}\n\n|cFF9D9D9DCapstone Bonus: {capstone}|r"
