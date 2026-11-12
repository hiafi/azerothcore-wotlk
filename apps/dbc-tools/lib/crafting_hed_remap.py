"""
Crafting rework C6, decision 4 (`.agents/plans/crafting-rework/crafting-rework.C6-RESEARCH.md`, user 2026-11-11): the
rule that remaps every stock `SpellItemEnchantment` row carrying Hit, Expertise or Defense (pure function, no
declarations; `source/world/crafting_hed_remap.py` applies it with `override_enchant()`).

Hit and Expertise are gone and Defense is retired (docs/Systems.md section 2), so a stock enchant, gem enchant, socket
bonus or random-property part that carries one gives the nearest live stat instead, point for point (every target stat
costs 1.0 in item_stat_cost): Hit (melee, ranged, spell, rating) -> Crit, Expertise -> Haste, Defense -> Dodge. Only
STAT effects (type 5) are remapped; when the remap leaves two effects on one stat they merge into the first.

The rows are logged in `.agents/plans/crafting-rework/crafting-rework.C6-HED-REMAP.md` (`log_lines()`), the list to
retire eventually (user 2026-11-11).
"""

from __future__ import annotations

import re

ENCHANT_TYPE_STAT = 5
CRIT, HASTE, DODGE = 32, 36, 13
REMAP = {
    16: CRIT, 17: CRIT, 18: CRIT, 31: CRIT,  # Hit Melee / Ranged / Spell / Hit Rating
    37: HASTE,  # Expertise Rating
    12: DODGE,  # Defense Skill Rating
}
OLD_NAMES = {12: "Defense", 16: "Melee Hit", 17: "Ranged Hit", 18: "Spell Hit", 31: "Hit", 37: "Expertise"}
NEW_NAMES = {CRIT: "Critical Strike Rating", HASTE: "Haste Rating", DODGE: "Dodge Rating"}
# Applied in order to the tooltip text when no merge rewrites it.
_TEXT_RULES = (
    (re.compile(r"\b(?:Melee |Ranged |Spell )?Hit Rating\b"), "Critical Strike Rating"),
    (re.compile(r"\bExpertise Rating\b"), "Haste Rating"),
    (re.compile(r"\bDefense Rating\b"), "Dodge Rating"),
    (re.compile(r"\bDefense\b"), "Dodge Rating"),
)
_STAT_WORDS = {
    3: "Agility", 4: "Strength", 5: "Intellect", 6: "Spirit", 7: "Stamina", 13: "Dodge Rating", 14: "Parry Rating",
    15: "Block Rating", 32: "Critical Strike Rating", 35: "Resilience Rating", 36: "Haste Rating",
    38: "Attack Power", 39: "Ranged Attack Power", 43: "mana every 5 sec.", 44: "Armor Penetration Rating",
    45: "Spell Power", 47: "Spell Penetration", 48: "Block Value",
}
_EFFECTS = (1, 2, 3)


def carries_hed(row: dict) -> bool:
    return any(row[f"Effect_{i}"] == ENCHANT_TYPE_STAT and row[f"EffectArg_{i}"] in REMAP for i in _EFFECTS)


def remap_row(row: dict) -> dict | None:
    """The changed columns for one stock row, or None when it carries none of the three stats."""
    if not carries_hed(row):
        return None
    new = {k: row[k] for k in row}
    for i in _EFFECTS:
        if new[f"Effect_{i}"] == ENCHANT_TYPE_STAT and new[f"EffectArg_{i}"] in REMAP:
            new[f"EffectArg_{i}"] = REMAP[new[f"EffectArg_{i}"]]
    merged = False
    for i in _EFFECTS:
        for j in _EFFECTS:
            if j <= i or new[f"Effect_{i}"] != ENCHANT_TYPE_STAT or new[f"Effect_{j}"] != ENCHANT_TYPE_STAT:
                continue
            if new[f"EffectArg_{i}"] != new[f"EffectArg_{j}"]:
                continue
            for column in ("EffectPointsMin", "EffectPointsMax"):
                new[f"{column}_{i}"] += new[f"{column}_{j}"]
                new[f"{column}_{j}"] = 0
            new[f"Effect_{j}"], new[f"EffectArg_{j}"] = 0, 0
            merged = True
    name = row["Name_Lang_enUS"]
    if merged and _all_stat(new):
        name = " and ".join(f"+{new[f'EffectPointsMin_{i}']} {_STAT_WORDS.get(new[f'EffectArg_{i}'], '?')}"
                            for i in _EFFECTS if new[f"Effect_{i}"] == ENCHANT_TYPE_STAT)
    else:
        for pattern, replacement in _TEXT_RULES:
            name = pattern.sub(replacement, name)
    new["Name_Lang_enUS"] = name
    return {k: v for k, v in new.items() if v != row[k]}


def _all_stat(row: dict) -> bool:
    return all(row[f"Effect_{i}"] in (0, ENCHANT_TYPE_STAT) for i in _EFFECTS)


def remapped(stock_rows: dict[int, dict]) -> dict[int, dict]:
    """{enchant id: changed columns} for every stock row the rule touches, in id order."""
    out = {}
    for row_id in sorted(stock_rows):
        changes = remap_row(stock_rows[row_id])
        if changes:
            out[row_id] = changes
    return out


def _stat_key(row: dict) -> tuple:
    return tuple(sorted((row[f"Effect_{i}"], row[f"EffectArg_{i}"], row[f"EffectPointsMin_{i}"])
                        for i in _EFFECTS if row[f"Effect_{i}"]))


def log_lines(stock_rows: dict[int, dict]) -> list[str]:
    """A Markdown table of every remapped row: id, old and new tooltip text, and a stock row the new row now duplicates
    (same effects; a candidate to retire)."""
    changes = remapped(stock_rows)
    after = {row_id: {**stock_rows[row_id], **changes.get(row_id, {})} for row_id in stock_rows}
    by_key: dict[tuple, list[int]] = {}
    for row_id, row in after.items():
        if row_id not in changes and _stat_key(row):
            by_key.setdefault(_stat_key(row), []).append(row_id)
    lines = ["| Enchant | Old text | New text | Duplicates |", "| --- | --- | --- | --- |"]
    for row_id, change in changes.items():
        old = stock_rows[row_id]["Name_Lang_enUS"].replace("|", "/")
        new = after[row_id]["Name_Lang_enUS"].replace("|", "/")
        dupes = ", ".join(str(d) for d in by_key.get(_stat_key(after[row_id]), [])[:3])
        lines.append(f"| {row_id} | {old} | {new} | {dupes} |")
    return lines
