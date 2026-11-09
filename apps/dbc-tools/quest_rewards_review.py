#!/usr/bin/env python3
"""
Writes the designer review lists of the quest reward itemization (docs/plans/quest-reward-itemization/, stage QR1b):
every epic from zone and dungeon quests, and every class quest reward (grouped by class, then the profession and
holiday quests), stock stats against the new materialized ones.

    python3 apps/dbc-tools/quest_rewards_review.py --out <path>/quest-reward-itemization.REVIEW-EPICS-AND-CLASS.md

Reads the current `source/items/quest_rewards.lock` (hand edits included) and materializes every line the way
source/items/quest_rewards.py declares it (`lib/quest_rewards.materialize`). Read-only on everything but `--out`.
The designer writes notes after the `//` of a Note cell; a re-run keeps whatever follows the `//` of each entry.
"""

from __future__ import annotations

import argparse
import collections
import re
import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_ROOT))

from lib import quest_rewards as qr  # noqa: E402

I = qr._int
NOTE_MARK = "//"

STAT_WORDS = {
    qr.STR: "Strength", qr.AGI: "Agility", qr.INT: "Intellect", qr.SPI: "Spirit", qr.STA: "Stamina",
    qr.AP: "Attack Power", qr.SP: "Spell Power", qr.DEFENSE: "Defense", qr.DODGE: "Dodge", qr.PARRY: "Parry",
    qr.BLOCK: "Block", qr.CRIT: "Crit", qr.HASTE: "Haste", qr.MASTERY: "Mastery", qr.VERSATILITY: "Versatility",
    qr.CDH: "Cooldown Haste", qr.PROC: "Proc Chance", qr.MP5: "MP5", qr.HIT: "Hit", qr.EXPERTISE: "Expertise",
    qr.ARPEN: "Armor Penetration", qr.SPELL_PEN: "Spell Penetration", 35: "Resilience", 46: "Health per 5",
    48: "Block Value", 39: "Ranged Attack Power", 41: "Healing", 42: "Spell Damage",
}
STAT_ORDER = (qr.STR, qr.AGI, qr.INT, qr.SPI, qr.STA, qr.AP, qr.SP, *qr.TANK_STATS, qr.CRIT, qr.HASTE, qr.MASTERY,
              qr.VERSATILITY, qr.CDH, qr.PROC, qr.MP5, qr.HIT, qr.EXPERTISE, qr.ARPEN, qr.SPELL_PEN)
# Abbreviations of lib/quest_rewards.py's rule paths, spelled out for the Note column.
ABBREVIATIONS = {"Str": "Strength", "Agi": "Agility", "Int": "Intellect", "Spi": "Spirit", "Sta": "Stamina",
                 "Vers": "Versatility", "CDH": "Cooldown Haste", "Proc": "Proc Chance", "SP": "Spell Power",
                 "AP": "Attack Power", "Def": "Defense", "ilvl": "item level", "FB": "Fallback:"}
RESISTS = (("holy_res", "Holy"), ("fire_res", "Fire"), ("nature_res", "Nature"), ("frost_res", "Frost"),
           ("shadow_res", "Shadow"), ("arcane_res", "Arcane"))
QUALITY_WORDS = {1: "white", 2: "green", 3: "blue", 4: "epic"}
TRIGGERS = {0: "Use", 1: "Equip", 2: "Chance on hit", 4: "Soulstone", 5: "Use, no delay", 6: "Learn"}
INV_TYPES = {1: "Head", 2: "Neck", 3: "Shoulder", 5: "Chest", 6: "Waist", 7: "Legs", 8: "Feet", 9: "Wrist",
             10: "Hands", 11: "Finger", 12: "Trinket", 13: "One-Hand", 14: "Off Hand", 15: "Ranged", 16: "Back",
             17: "Two-Hand", 20: "Chest", 21: "Main Hand", 22: "Off Hand", 23: "Held In Off-hand", 25: "Thrown",
             26: "Ranged", 28: "Relic"}
ARMOR_TYPES = {0: "", 1: "Cloth", 2: "Leather", 3: "Mail", 4: "Plate", 6: "Shield", 7: "Libram", 8: "Idol",
               9: "Totem", 10: "Sigil"}
WEAPON_TYPES = {0: "Axe", 1: "Axe", 2: "Bow", 3: "Gun", 4: "Mace", 5: "Mace", 6: "Polearm", 7: "Sword", 8: "Sword",
                10: "Staff", 13: "Fist Weapon", 14: "Miscellaneous", 15: "Dagger", 16: "Thrown", 17: "Spear",
                18: "Crossbow", 19: "Wand", 20: "Fishing Pole"}


def cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def stat_text(stats: dict[int, int]) -> str:
    keys = [k for k in STAT_ORDER if stats.get(k)] + sorted(k for k in stats if k not in STAT_ORDER and stats[k])
    return ", ".join(f"{stats[k]} {STAT_WORDS.get(k, f'stat {k}')}" for k in keys) or "no stats"


def weapon_text(row: dict) -> str:
    lo, hi, delay = float(row.get("dmg_min1") or 0), float(row.get("dmg_max1") or 0), I(row.get("delay"))
    if delay <= 0 or hi <= 0:
        return "no damage"
    return f"{lo:.0f}-{hi:.0f} dmg, speed {delay / 1000:.2f}, {(lo + hi) / 2 / (delay / 1000):.1f} DPS"


def resist_text(row: dict) -> str:
    parts = [f"{I(row.get(col))} {name} Resistance" for col, name in RESISTS if I(row.get(col))]
    return ", ".join(parts)


def item_side(stats: str, row: dict, other: dict) -> str:
    """One Stock or New stats cell: stats; weapon damage; armor and block value where they change; resistances."""
    parts = [stats]
    if I(row.get("class")) == qr.ITEM_CLASS_WEAPON:
        parts.append(weapon_text(row))
    for col, word in (("armor", "Armor"), ("block", "Block Value")):
        if I(row.get(col)) != I(other.get(col)):
            parts.append(f"{word} {I(row.get(col))}")
    if resist := resist_text(row):
        parts.append(resist)
    return "; ".join(parts)


def slot_text(row: dict) -> str:
    inv, cls, sub = I(row.get("InventoryType")), I(row.get("class")), I(row.get("subclass"))
    kind = WEAPON_TYPES.get(sub, f"weapon {sub}") if cls == qr.ITEM_CLASS_WEAPON else ARMOR_TYPES.get(sub, "")
    slot = INV_TYPES.get(inv, f"slot {inv}")
    return f"{slot} {kind}".strip() if kind and kind != slot else slot


def spell_name(spells: dict, spell_id: int) -> str:
    row = spells.get(spell_id)
    return f"{(row or {}).get('Name_Lang_enUS') or 'unknown'} ({spell_id})"


def spells_text(line: qr.LockLine, row: dict, base: dict, spells: dict) -> str:
    kept_slots = line.kept_slots
    kept, absorbed = [], []
    for n in range(1, qr.SPELL_SLOTS + 1):
        spell_id = I(row.get(f"spellid_{n}"))
        if not spell_id:
            continue
        text = f"{TRIGGERS.get(I(row.get(f'spelltrigger_{n}')), 'trigger ?')}: {spell_name(spells, spell_id)}"
        (kept if kept_slots is None or n in kept_slots else absorbed).append(text)
    current = {I(row.get(f"spellid_{n}")) for n in range(1, qr.SPELL_SLOTS + 1)}
    earlier = [f"Equip: {spell_name(spells, I(base.get(f'spellid_{n}')))}" for n in range(1, qr.SPELL_SLOTS + 1)
               if I(base.get(f"spellid_{n}")) and I(base.get(f"spellid_{n}")) not in current
               and I(base.get(f"spelltrigger_{n}")) == qr.SPELL_TRIGGER_EQUIP]
    parts = []
    if kept:
        parts.append("kept: " + "; ".join(kept))
    if absorbed:
        parts.append("absorbed: " + "; ".join(absorbed))
    if earlier:
        parts.append("absorbed earlier (stock): " + "; ".join(earlier))
    return " / ".join(parts) or "-"


def plain(text: str) -> str:
    text = text.replace("->", " → ")
    for short, word in ABBREVIATIONS.items():
        text = re.sub(rf"(?<![A-Za-z]){re.escape(short)}(?![A-Za-z])", word, text)
    return re.sub(r"\s+", " ", text).strip()


ROUND = "round 7"  # the round a re-run marks; earlier rounds' notes stay in the rule path
ROUND_PREFIXES = ("round 7: ", "designer 2026-11-09 (round 7, ruling 36): ", "round 7 step-down (ruling 35): ")


def note_text(d: qr.Decision | None, line: qr.LockLine, comment: str, stats_changed: str = "") -> str:
    """The Note: what this round (`ROUND`) changed first (`**round 7**: ...`: a designer edit or a step-down from
    the lock comment, a ruling 32 or 33 rule path, or `stats_changed` when only the materialized stats moved), then
    the rule path. A lock line whose fields differ from the rules, or that the designer edited (a rule may since have
    caught up with the edit), is a hand edit: its comment is the rule path."""
    hand = d is None or "designer 2026-11-09" in comment or (
        d.quality, d.ilvl, d.primary, d.secondary, d.share, d.spells_field) != (
        line.quality, line.ilvl, line.primary, line.secondary, line.share, line.spells)
    if hand:
        why = comment.split(" -- ", 1)[-1]
        parts = why.split("; ")[1:]  # the first part is the shapes as stats
    else:
        parts = [p for p in d.paths if p] + [f"FB {f}" for f in d.fallbacks]
    changed = [p for p in parts if ROUND in p]
    rest = [p for p in parts if ROUND not in p]
    for prefix in ROUND_PREFIXES:
        changed = [p.replace(prefix, "designer: " if "designer" in prefix else
                             "step-down: " if "step-down" in prefix else "") for p in changed]
    if not changed and stats_changed:
        changed = [stats_changed]
    head = f"**{ROUND}**: " + "; ".join(changed) + ". " if changed else ""
    return head + plain("; ".join((["hand-edited lock line"] if hand else []) + rest))


def quests_text(d: qr.Decision, quests: dict) -> str:
    out = []
    for q in d.quests[:2]:
        scaled = f", scaled: MinLevel {q.level}" if q.scaled else ""
        out.append(f"{quests[q.id].get('LogTitle') or q.title} ({q.id}, {q.level}{scaled})")
    if len(d.quests) > 2:
        out.append(f"+{len(d.quests) - 2} more")
    return "; ".join(out)


def class_names(d: qr.Decision, quests: dict, addons: dict) -> set[str]:
    names = set()
    for q in d.quests:
        quest, addon = quests[q.id], addons.get(q.id) or {}
        mask = I(addon.get("AllowableClasses"))
        if mask:
            names |= {name for cid, name in qr.CLASS_NAMES.items() if mask & (1 << (cid - 1))}
        elif I(quest.get("QuestSortID")) in qr.CLASS_QUEST_SORTS:
            names.add(qr.CLASS_QUEST_SORTS[I(quest.get("QuestSortID"))])
    return names


def old_new_stats(path: Path | None) -> dict[int, str]:
    """{entry: its New stats cell} of an earlier review file (the baseline a re-run marks changes against)."""
    out = {}
    if path is None or not path.is_file():
        return out
    for raw in path.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", raw)[1:-1]]
        if len(cells) >= 10 and cells[0].isdigit():
            out[int(cells[0])] = cells[7]
    return out


def old_notes(path: Path) -> dict[int, str]:
    """{entry: designer text after the `//`} of an earlier review file."""
    notes = {}
    if not path.is_file():
        return notes
    for raw in path.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", raw)[1:-1]]
        if len(cells) >= 10 and cells[0].isdigit() and NOTE_MARK in cells[-1]:
            extra = cells[-1].split(NOTE_MARK, 1)[1].strip()
            if extra:
                notes[int(cells[0])] = extra
    return notes


HEADER = ("| Entry | Name | Quest (id, level) | Quality (stock -> new) | Slot / type | Item level (stock -> new) "
          "| Stock stats | New stats | Spells | Note |\n| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, required=True, help="the review markdown file to (re)write")
    parser.add_argument("--baseline", type=Path,
                        help="an earlier review file: a row whose New stats differ from it is marked as changed by "
                             f"{ROUND} even when its lock line did not change (a curve change)")
    args = parser.parse_args(argv)

    from lib import item_variants  # noqa: PLC0415

    inputs = qr.load_inputs()
    _, decisions = qr.run(inputs)
    by_entry = {d.entry: d for d in decisions}
    lock = qr.parse_lock(qr.LOCK_PATH.read_text(encoding="utf-8"))
    _, shape_catalog = item_variants.load_itemization_tables()
    mat = qr.materialize(lock, inputs.rows, inputs.tables, shape_catalog)
    if mat.errors:
        print("\n".join(mat.errors), file=sys.stderr)
        return 1
    notes = old_notes(args.out)
    baseline = old_new_stats(args.baseline)
    comments = qr.lock_comments(qr.LOCK_PATH.read_text(encoding="utf-8"))

    part1, part2, other = [], collections.defaultdict(list), []
    for entry in sorted(lock):
        d = by_entry.get(entry)
        if d is None:
            print(f"NOTE: locked entry {entry} is no longer in scope; left out", file=sys.stderr)
            continue
        classes = class_names(d, inputs.quests, inputs.addons)
        if classes:
            part2[next(iter(classes)) if len(classes) == 1 else "Several classes"].append(d)
        elif any(I(inputs.quests[q.id].get("QuestSortID")) < 0 for q in d.quests):
            other.append(d)
        elif d.stock_quality == qr.EPIC:
            part1.append(d)

    def table(rows: list[qr.Decision]) -> list[str]:
        out = [HEADER]
        for d in sorted(rows, key=lambda x: (x.quest_level, x.entry)):
            line, new, cur = lock[d.entry], mat.rows[d.entry], inputs.rows[d.entry]
            base = inputs.base_rows.get(d.entry, cur)
            new_stats = {I(new[f"stat_type{n}"]): I(new[f"stat_value{n}"]) for n in range(1, 11)
                         if I(new[f"stat_type{n}"])}
            new_cell = item_side(stat_text(new_stats), new, base)
            moved = ""
            if d.entry in baseline and baseline[d.entry] != cell(new_cell):
                moved = "new stats changed"
            note = note_text(d, line, comments.get(d.entry, line.comment), moved)
            if I(cur.get("RandomProperty")) or I(cur.get("RandomSuffix")):
                note += (f"; keeps its random enchant (RandomProperty {I(cur.get('RandomProperty'))}, RandomSuffix "
                         f"{I(cur.get('RandomSuffix'))}) on top of the budget (ruling 26)")
            note = f"{note} {NOTE_MARK}"
            if d.entry in notes:
                note += f" {notes[d.entry]}"
            out.append("| " + " | ".join(cell(c) for c in (
                d.entry, d.name, quests_text(d, inputs.quests),
                f"{QUALITY_WORDS[d.stock_quality]} -> {QUALITY_WORDS[line.quality]}", slot_text(cur),
                f"{d.stock_ilvl} -> {line.ilvl}", item_side(stat_text(d.stock), base, new),
                new_cell, spells_text(line, cur, base, inputs.spells),
                note)) + " |")
        return out

    class_order = sorted(part2, key=lambda k: (k == "Several classes", k))
    count2 = sum(len(v) for v in part2.values())
    by_quality = collections.Counter(QUALITY_WORDS[d.stock_quality] for v in part2.values() for d in v)
    scaled = sum(1 for v in part2.values() for d in v if any(q.scaled for q in d.quests))
    lines = [
        "# Quest reward itemization: review of epics and class quest rewards",
        "",
        "Generated by `apps/dbc-tools/quest_rewards_review.py` from `apps/dbc-tools/source/items/quest_rewards.lock`"
        " (branch `feat/quest-reward-itemization`). Stage QR1d, rulings 1-36. A row round 7 changed starts its Note"
        " with **round 7**.",
        "",
        "**How to annotate:** write your notes in the Note cell after the `//`. To change an item, edit its lock "
        "line (or tell me), then re-run the script: it keeps whatever follows the `//` of each entry.",
        "",
        "Columns:",
        "",
        "- **Quest (id, level)**: the rewarding quests, lowest level first (the level used). `scaled: MinLevel N`: a"
        " level -1 class quest, counted at its minimum level.",
        "- **Quality / Item level**: stock -> new (rulings 2, 5, 7, 8: whites become green, never lowered, epics keep"
        " their level).",
        "- **Stock stats**: the stock item as the rules read it: the base dump's stat columns plus the stats of its"
        " Equip spells (so vanilla Defense, Dodge, MP5, Spell Power spells show here), weapon damage and DPS,"
        " resistances; armor and block value when they change.",
        "- **New stats**: the materialized result (the server's budget formula), same format.",
        "- **Spells**: kept spells (Use, procs, other real effects; an armor item with a kept effect gets 70% of the"
        " stat budget, a weapon its role cell's share) and"
        " absorbed ones (plain stat Equip spells, folded into the new stats).",
        "- **Note**: the rule path and any fallback, in plain words.",
        "",
        f"Counts: Part 1 {len(part1)} epics. Part 2 {count2} class quest rewards ("
        + ", ".join(f"{k} {v}" for k, v in sorted(by_quality.items())) + f"; {scaled} from scaled class quests), "
        f"{len(other)} profession and holiday quest rewards.",
        "",
        f"## Part 1: epics from zone and dungeon quests ({len(part1)})",
        "",
        *table(part1),
        "",
        f"## Part 2: class quest rewards ({count2})",
        "",
    ]
    for name in class_order:
        lines += [f"### {name} ({len(part2[name])})", "", *table(part2[name]), ""]
    lines += [f"### Profession and holiday quests ({len(other)})", "", *table(other), ""]
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {args.out}: part 1 {len(part1)}, part 2 {count2} in {len(part2)} class group(s), other {len(other)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
