"""
Quest reward itemization (docs/plans/quest-reward-itemization/, stage QR0): which stock quest rewards move onto the
item stat system, and the per-item decisions (item level, quality, shapes, primary share, kept spells), frozen in
`source/items/quest_rewards.lock` and declared by `source/items/quest_rewards.py` as `item(base=<entry>, ...)` on the
one-tier `quest_reward` ladder (QR1).

Everything below `load_inputs()` is a pure function of plain dicts (the replayed world tables, the stock Spell.dbc
rows, the shape catalog and `item_stat_cost`), so the host tests (`lib/test_quest_rewards.py`) build them by hand.
The rules are PLAN section 3 (rulings 1-20 of the REQUIREMENTS):

1. **Scope.** Equippable rewards (`class` 2 weapon or 4 armor, not InventoryType 0, shirts 4 or tabards 19) of
   quests at `QuestLevel` 1-60 that are not repeatable (`SpecialFlags & 1`), daily (`Flags & 0x1000`) or weekly
   (`Flags & 0x8000`) and not raid (`QuestInfoID` 62) or PvP (41) quests. Rewards are `RewardItem1-4` and
   `RewardChoiceItemID1-6`. An item that any out-of-scope quest also rewards is out (a scaled `QuestLevel` -1 quest
   counts as out of scope: it has no quest level). Legendary and Poor items are skipped (rulings 16, 17). An entry
   another declaration owns (`source/items/*.py` `item(base=...)`, `item_ids.lock`, `items.csv`, a literal
   `item_template(<entry>, ...)`) is skipped and reported (`owned_elsewhere()`): one owner per entry.
2. **Quest level**: the lowest `QuestLevel` of the quests that reward it.
3. **Item level and quality.** White becomes green at min(quest level + 2, 55); green min(quest level + 5, 55); blue
   min(quest level + 5, 60); epic keeps its level; then max(current item level, target) (never lower). Required level
   0 (set by the declaration).
4. **Stock stat read** (`stock_read()`): the base dump's stat columns plus the stat effects of its Equip spells
   (`spelltrigger` 1) through `spell_stat_effects()`, the itemization-changes.md s4.5 (revision 3) classifier:
   `MOD_STAT` (29), `MOD_ATTACK_POWER` (99, `MOD_RANGED_ATTACK_POWER` 124 when alone), `MOD_RATING` (189, every
   priced bit), `MOD_DAMAGE_DONE` (13) on a magic school, `MOD_HEALING_DONE` (135) skipped as 13's companion, plus
   `MOD_POWER_REGEN` (85) on mana as MP5 (requirements: vanilla MP5 is mostly an Equip spell) and
   `MOD_TARGET_RESISTANCE` (123) as Spell Penetration. Values are `EffectBasePoints + 1`. Never the live row (a
   converted item's live row has Defense dropped and its spells cleared).
5. **Primary shape.** The nearest primary shape (least squares over the cost-weighted, renormalized primary stats,
   itemization-phase-2.md s9.1 step 3). Whites: by item type (ruling 18, `type_main_stat()`; "alternating by entry"
   = even entry the first stat, odd the second). A non-white item with no primary stat in its stock read takes the
   type main stat too (a reported fallback). Cloaks, rings and necks: no primary shape (Null, share 0).
6. **Secondary shape.** Generic shapes over Crit, Haste, Mastery, Versatility, Cooldown Haste and Proc Chance: green
   one stat (Solo), blue two (pairs), epic two or three (pairs and trios), picked by `entry MOD pool size` over the
   eligible pool sorted by shape id. Tank stats (ruling 12): Dodge, Parry, Block or Defense in the stock read keep
   their stat (Defense becomes Block on a shield, Parry on other plate, Dodge on everything else; the heaviest tank
   stat wins); green takes that stat's Solo shape, blue and epic a pair of that stat and a generic companion. Parry
   and Block shapes need a Strength primary: else Dodge. Dodge shapes need Strength or Agility: else "Dodge (Solo,
   Any)", even on a blue or epic (one secondary stat; reported). MP5 (ruling 13): a blue whose stock read has MP5
   takes an MP5 pair; a Spirit primary forbids MP5, so that item keeps Spirit and loses the MP5 (reported). Greens
   and epics lose MP5 (the ruling keeps it on blues only; reported).
7. **Primary share**: green 8000, blue 6000, epic 6000 with a pair secondary and 4000 with a trio; Null primary 0.
8. **Spells** (`spell_slots()`): on the current row, an Equip spell whose every effect is a stat
   (`spell_stat_effects()` returns its stats) is absorbed (`absorbed_spell_slots`, the item() default); Use, Chance
   on hit and every other Equip spell (procs, slaying, resistances, skills, ...) is kept. A kept effect gives the
   DSL's `budget_mult` 0.7 default.
9. **Resistances** are never written by the materializer: untouched, free (ruling 14).

**The lock.** `source/items/quest_rewards.lock`, one line per item:

    <entry> <quest level> <quality> <ilvl> <primary shape id> <secondary shape id> <share> <spells>  # <name> -- <why>

A comment longer than the 120 columns of .editorconfig continues on `#   ` comment lines under its entry.

`<spells>` is `-` (every stock spell slot absorbed, or none), `all` (`keep_spells=True`) or the kept slot numbers
(`2` or `1,3`; the other slots are absorbed). Shape ids are `item_shape.shape_id` (0 = Null). The file is seeded by
`python3 apps/dbc-tools/quest_rewards_lock.py --seed-quest-rewards` and is append-only afterwards: a seed run only
appends entries that have no line, and never rewrites one, so a hand edit stays (the `item_role_cells.lock`
precedent). A line whose item has left the scope is reported, never removed. The comment is for the reader; the
fields are what the declaration reads.
"""

from __future__ import annotations

import ast
import re
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
ITEMS_DIR = TOOL_ROOT / "source" / "items"
LOCK_PATH = ITEMS_DIR / "quest_rewards.lock"
SOURCE_FILE = "quest_rewards.py"  # the declaration file the lock feeds (skipped by owned_elsewhere)
KEY_PREFIX = "qr_"  # the item() key of a lock line: qr_<entry>

# Qualities
POOR, COMMON, UNCOMMON, RARE, EPIC, LEGENDARY = 0, 1, 2, 3, 4, 5
QUALITY_NAMES = {0: "poor", 1: "white", 2: "green", 3: "blue", 4: "epic", 5: "legendary", 6: "artifact",
                 7: "heirloom"}
GREEN_CAP, BLUE_CAP = 55, 60
WHITE_STEP, GREEN_STEP, BLUE_STEP = 2, 5, 5

# Scope
MIN_QUEST_LEVEL, MAX_QUEST_LEVEL = 1, 60
QUEST_SPECIAL_REPEATABLE = 0x1  # quest_template_addon.SpecialFlags
QUEST_FLAGS_DAILY = 0x1000
QUEST_FLAGS_WEEKLY = 0x8000
QUEST_INFO_RAID, QUEST_INFO_PVP, QUEST_INFO_DUNGEON = 62, 41, 81
REWARD_COLUMNS = tuple(f"RewardItem{n}" for n in range(1, 5)) + tuple(f"RewardChoiceItemID{n}" for n in range(1, 7))
ITEM_CLASS_WEAPON, ITEM_CLASS_ARMOR = 2, 4
EXCLUDED_INV_TYPES = (0, 4, 19)  # not equippable, shirt, tabard
INV_NECK, INV_FINGER, INV_TRINKET, INV_SHIELD, INV_CLOAK, INV_HOLDABLE = 2, 11, 12, 14, 16, 23
NO_MAIN_STAT_INV_TYPES = (INV_NECK, INV_FINGER, INV_CLOAK)  # ruling 18: all secondary
ARMOR_CLOTH, ARMOR_LEATHER, ARMOR_MAIL, ARMOR_PLATE, ARMOR_SHIELD = 1, 2, 3, 4, 6

# Stats (ItemModType)
AGI, STR, INT, SPI, STA = 3, 4, 5, 6, 7
DEFENSE, DODGE, PARRY, BLOCK = 12, 13, 14, 15
MASTERY, VERSATILITY, CDH = 22, 23, 24
HIT, CRIT, PROC, HASTE, EXPERTISE = 31, 32, 33, 36, 37
AP, MP5, ARPEN, SP, SPELL_PEN = 38, 43, 44, 45, 47
PRIMARY_STATS = (AGI, STR, INT, SPI, AP, SP)  # item_stat_cost shape_side 1
TANK_STATS = (DEFENSE, DODGE, PARRY, BLOCK)
GENERIC_SECONDARY_STATS = frozenset((CRIT, HASTE, MASTERY, VERSATILITY, CDH, PROC))
STAT_NAMES = {
    AGI: "Agi", STR: "Str", INT: "Int", SPI: "Spi", STA: "Sta", DEFENSE: "Def", DODGE: "Dodge", PARRY: "Parry",
    BLOCK: "Block", MASTERY: "Mastery", VERSATILITY: "Vers", CDH: "CDH", HIT: "Hit", CRIT: "Crit", PROC: "Proc",
    HASTE: "Haste", EXPERTISE: "Exp", AP: "AP", MP5: "MP5", ARPEN: "ArP", SP: "SP", SPELL_PEN: "SpPen",
    35: "Resil", 46: "HP5", 48: "BlockValue",
}

# Spell effects (Spell.dbc, SharedDefines.h / SpellAuraDefines.h)
EFFECT_APPLY_AURA = 6
SPELL_TRIGGER_USE, SPELL_TRIGGER_EQUIP, SPELL_TRIGGER_HIT = 0, 1, 2
AURA_MOD_DAMAGE_DONE, AURA_MOD_STAT, AURA_MOD_POWER_REGEN = 13, 29, 85
AURA_MOD_ATTACK_POWER, AURA_MOD_TARGET_RESISTANCE, AURA_MOD_RANGED_ATTACK_POWER = 99, 123, 124
AURA_MOD_HEALING_DONE, AURA_MOD_RATING = 135, 189
MAGIC_SCHOOLS = 0x7E
POWER_MANA = 0
MOD_STAT_MISC = {0: (STR,), 1: (AGI,), 2: (STA,), 3: (INT,), 4: (SPI,), -1: (STR, AGI, STA, INT, SPI)}
# CombatRating bit -> ItemModType (itemization-changes.md s4.5 revision 3). Bits that map to the same stat count once.
RATING_BITS = {
    1: DEFENSE, 2: DODGE, 3: PARRY, 4: BLOCK, 5: HIT, 6: HIT, 7: HIT, 8: CRIT, 9: CRIT, 10: CRIT,
    17: HASTE, 18: HASTE, 19: HASTE, 23: EXPERTISE, 24: ARPEN,
}

SPELL_SLOTS = 5
# item_weapon_dps_curve has Rare and Epic rows only (2026-11-09): a green weapon's budget cannot resolve, so its lock
# line is kept but source/items/quest_rewards.py declares no item() for it until a Quality 2 curve exists.
UNCOMMON_WEAPONS_WAIT = True
SHARE_GREEN, SHARE_BLUE, SHARE_EPIC_PAIR, SHARE_EPIC_TRIO = 8000, 6000, 6000, 4000

PRIMARY_SOLO = {STR: "Strength (Solo)", AGI: "Agility (Solo)", INT: "Intellect (Solo)"}
DODGE_ANY = "Dodge (Solo, Any)"


def _int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default


# ---------------------------------------------------------------------------------------------------------------------
# Scope (rules 1-2)


@dataclass(frozen=True)
class Quest:
    id: int
    level: int
    title: str
    kind: str  # "zone", "dungeon" or "class" (QuestSortID < 0 or AllowableClasses set)


def reward_map(quests: dict[int, dict]) -> dict[int, set[int]]:
    """{item entry: {quest ids that reward it}} over `RewardItem1-4` and `RewardChoiceItemID1-6`."""
    out: dict[int, set[int]] = {}
    for qid, row in quests.items():
        for column in REWARD_COLUMNS:
            item = _int(row.get(column))
            if item > 0:
                out.setdefault(item, set()).add(int(qid))
    return out


def quest_out_of_scope(quest: dict, addon: dict | None) -> str | None:
    """Why a quest is out of scope (None: in scope)."""
    level = _int(quest.get("QuestLevel"))
    if not MIN_QUEST_LEVEL <= level <= MAX_QUEST_LEVEL:
        return f"quest level {level}"
    if _int((addon or {}).get("SpecialFlags")) & QUEST_SPECIAL_REPEATABLE:
        return "repeatable"
    flags = _int(quest.get("Flags"))
    if flags & QUEST_FLAGS_DAILY:
        return "daily"
    if flags & QUEST_FLAGS_WEEKLY:
        return "weekly"
    info = _int(quest.get("QuestInfoID"))
    if info == QUEST_INFO_RAID:
        return "raid quest"
    if info == QUEST_INFO_PVP:
        return "PvP quest"
    return None


def quest_kind(quest: dict, addon: dict | None) -> str:
    if _int(quest.get("QuestSortID")) < 0 or _int((addon or {}).get("AllowableClasses")):
        return "class"
    if _int(quest.get("QuestInfoID")) == QUEST_INFO_DUNGEON:
        return "dungeon"
    return "zone"


def equippable(row: dict) -> bool:
    return (_int(row.get("class")) in (ITEM_CLASS_WEAPON, ITEM_CLASS_ARMOR)
            and _int(row.get("InventoryType")) not in EXCLUDED_INV_TYPES)


@dataclass
class Scope:
    items: dict[int, list[Quest]] = field(default_factory=dict)  # entry -> its quests, lowest level first
    skipped: dict[int, str] = field(default_factory=dict)  # equippable quest rewards left out, entry -> why


def scope(quests: dict[int, dict], addons: dict[int, dict], rows: dict[int, dict],
          owned: dict[int, str] | None = None) -> Scope:
    """Rule 1. `rows` are the current (replayed) item rows; `owned` is {entry: owner} of the entries another
    declaration owns (`owned_elsewhere()`)."""
    owned = owned or {}
    out = Scope()
    for entry, qids in sorted(reward_map(quests).items()):
        row = rows.get(entry)
        if row is None or not equippable(row):
            continue
        reasons = sorted({r for q in qids if (r := quest_out_of_scope(quests[q], addons.get(q))) is not None})
        if reasons:
            out.skipped[entry] = "also rewarded by an out-of-scope quest (" + ", ".join(reasons) + ")"
            continue
        quality = _int(row.get("Quality"))
        if quality == POOR:
            out.skipped[entry] = "Poor (ruling 17)"
            continue
        if quality >= LEGENDARY:
            out.skipped[entry] = f"{QUALITY_NAMES.get(quality, quality)} (ruling 16)"
            continue
        if entry in owned:
            out.skipped[entry] = f"owned by {owned[entry]}"
            continue
        out.items[entry] = sorted(
            (Quest(q, _int(quests[q].get("QuestLevel")), str(quests[q].get("LogTitle") or ""),
                   quest_kind(quests[q], addons.get(q))) for q in qids),
            key=lambda quest: (quest.level, quest.id),
        )
    return out


# ---------------------------------------------------------------------------------------------------------------------
# Stock stat read (rule 4) and spells (rule 8)


def spell_stat_effects(spell: dict | None) -> dict[int, int] | None:
    """{stat: value} when every effect of `spell` grants a plain stat (the classifier of itemization-changes.md s4.5
    revision 3, plus MP5 and Spell Penetration), else None (a proc, a conditional bonus, anything else: a real
    effect). A spell with no effect is not a stat spell."""
    if spell is None:
        return None
    effects = [n for n in (1, 2, 3) if _int(spell.get(f"Effect_{n}"))]
    if not effects:
        return None
    stats: dict[int, int] = {}
    auras = {_int(spell.get(f"EffectAura_{n}")) for n in effects}
    for n in effects:
        if _int(spell.get(f"Effect_{n}")) != EFFECT_APPLY_AURA:
            return None
        aura = _int(spell.get(f"EffectAura_{n}"))
        misc = _int(spell.get(f"EffectMiscValue_{n}"))
        value = _int(spell.get(f"EffectBasePoints_{n}")) + 1
        if aura == AURA_MOD_STAT:
            if misc not in MOD_STAT_MISC:
                return None
            for stat in MOD_STAT_MISC[misc]:
                stats[stat] = stats.get(stat, 0) + value
        elif aura == AURA_MOD_ATTACK_POWER:
            stats[AP] = stats.get(AP, 0) + value
        elif aura == AURA_MOD_RANGED_ATTACK_POWER:
            if AURA_MOD_ATTACK_POWER not in auras:  # else 99's companion, counted once
                stats[AP] = stats.get(AP, 0) + value
        elif aura == AURA_MOD_RATING:
            bits = [b for b in range(32) if misc & (1 << b)]
            if not bits or any(b not in RATING_BITS for b in bits):
                return None
            for stat in {RATING_BITS[b] for b in bits}:
                stats[stat] = stats.get(stat, 0) + value
        elif aura == AURA_MOD_DAMAGE_DONE:
            if not misc & MAGIC_SCHOOLS:
                return None  # physical damage done: a weapon damage bonus, not spell power
            stats[SP] = stats.get(SP, 0) + value
        elif aura == AURA_MOD_HEALING_DONE:
            if AURA_MOD_DAMAGE_DONE not in auras:
                stats[SP] = stats.get(SP, 0) + value  # a healing-only spell (none on stock quest rewards)
        elif aura == AURA_MOD_POWER_REGEN:
            if misc != POWER_MANA:
                return None
            stats[MP5] = stats.get(MP5, 0) + value
        elif aura == AURA_MOD_TARGET_RESISTANCE:
            stats[SPELL_PEN] = stats.get(SPELL_PEN, 0) + abs(value)  # stored negative: -21 is +20
        else:
            return None
    return stats


def stock_read(base_row: dict, spells: dict[int, dict]) -> dict[int, int]:
    """Rule 4: {stat: value} of the base dump row's stat columns plus its Equip spells' plain stat effects."""
    stats: dict[int, int] = {}
    for n in range(1, 11):
        stat, value = _int(base_row.get(f"stat_type{n}")), _int(base_row.get(f"stat_value{n}"))
        if stat and value > 0:
            stats[stat] = stats.get(stat, 0) + value
    for n in range(1, SPELL_SLOTS + 1):
        spell_id = _int(base_row.get(f"spellid_{n}"))
        if spell_id and _int(base_row.get(f"spelltrigger_{n}")) == SPELL_TRIGGER_EQUIP:
            for stat, value in (spell_stat_effects(spells.get(spell_id)) or {}).items():
                if value > 0:
                    stats[stat] = stats.get(stat, 0) + value
    return stats


def spell_slots(row: dict, spells: dict[int, dict]) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Rule 8 on the current row: (kept slots, absorbed slots), 1-based. A plain-stat Equip spell is absorbed; every
    other spell (Use, Chance on hit, a proc or other real Equip effect, a spell missing from Spell.dbc) is kept."""
    kept, absorbed = [], []
    for n in range(1, SPELL_SLOTS + 1):
        spell_id = _int(row.get(f"spellid_{n}"))
        if not spell_id:
            continue
        stat_spell = (_int(row.get(f"spelltrigger_{n}")) == SPELL_TRIGGER_EQUIP
                      and spell_stat_effects(spells.get(spell_id)) is not None)
        (absorbed if stat_spell else kept).append(n)
    return tuple(kept), tuple(absorbed)


def format_stats(stats: dict[int, int]) -> str:
    order = (STR, AGI, INT, SPI, STA, AP, SP, *TANK_STATS, CRIT, HASTE, MASTERY, VERSATILITY, CDH, PROC, MP5, HIT,
             EXPERTISE, ARPEN, SPELL_PEN)
    keys = [k for k in order if k in stats] + sorted(k for k in stats if k not in order)
    return ", ".join(f"{stats[k]} {STAT_NAMES.get(k, f'stat{k}')}" for k in keys if stats[k]) or "no stats"


# ---------------------------------------------------------------------------------------------------------------------
# Item level and quality (rule 3)


def target(quality: int, stock_ilvl: int, quest_level: int) -> tuple[int, int, str]:
    """(new quality, new item level, rule path)."""
    if quality == COMMON:
        want, new_quality = min(quest_level + WHITE_STEP, GREEN_CAP), UNCOMMON
    elif quality == UNCOMMON:
        want, new_quality = min(quest_level + GREEN_STEP, GREEN_CAP), UNCOMMON
    elif quality == RARE:
        want, new_quality = min(quest_level + BLUE_STEP, BLUE_CAP), RARE
    elif quality == EPIC:
        return EPIC, stock_ilvl, f"ilvl {stock_ilvl} kept (epic)"
    else:
        raise ValueError(f"quality {quality} has no quest reward target")
    if stock_ilvl >= want:
        return new_quality, stock_ilvl, f"ilvl {stock_ilvl} kept (target {want})"
    return new_quality, want, f"ilvl {stock_ilvl}->{want}"


# ---------------------------------------------------------------------------------------------------------------------
# Shapes (rules 5-7)


@dataclass(frozen=True)
class Catalog:
    """The shape catalog (`item_lib.shapes.catalog()`) and the stat costs, with the lookups the rules need."""

    shapes: dict[int, dict]
    costs: dict[int, float]

    @classmethod
    def from_tables(cls, catalog: dict[int, dict], tables: dict) -> Catalog:
        costs = {int(k[0]): float(v["cost"]) for k, v in tables["item_stat_cost"].items()}
        return cls(catalog, costs)

    def by_name(self, name: str) -> int:
        for shape_id, shape in self.shapes.items():
            if shape["name"] == name:
                return shape_id
        raise KeyError(f"no item_shape named {name!r}")

    def primaries(self) -> list[dict]:
        return [s for sid, s in sorted(self.shapes.items()) if s["kind"] == 0 and s["stats"]]

    def secondaries(self) -> list[dict]:
        return [s for _, s in sorted(self.shapes.items()) if s["kind"] == 1]

    def stats(self, shape_id: int) -> list[int]:
        return list(self.shapes[shape_id]["stats"]) if shape_id in self.shapes else []


def rules_ok(shape: dict, primary_stats: set[int]) -> bool:
    """`item_lib.shapes.rules_satisfied`, inlined so the rules stay importable without item-tools."""
    requires = [stat for rule, stat in shape["rules"] if rule == 1]
    forbids = [stat for rule, stat in shape["rules"] if rule == 2]
    if any(stat in primary_stats for stat in forbids):
        return False
    return not requires or any(stat in primary_stats for stat in requires)


def allowed_primary_stats(stats: dict[int, int]) -> set[int]:
    """The main stats a primary shape may carry for an item with these stock stats: its own primary stats, plus Spell
    Power next to Intellect or Spirit and Attack Power next to Strength or Agility (the companions the catalog pairs
    them with). A shape outside this set would add a main stat of the other role (ruling 6: keep the main stat)."""
    have = {s for s in PRIMARY_STATS if stats.get(s, 0) > 0}
    allowed = set(have)
    if have & {INT, SPI, SP}:
        allowed.add(SP)
    if have & {STR, AGI, AP}:
        allowed.add(AP)
    return allowed


def nearest_primary(stats: dict[int, int], catalog: Catalog, keep_role: bool = True) -> int | None:
    """Rule 5: the primary shape nearest the cost-weighted, renormalized primary stats (None: no primary stat), by
    the stock conversion's least squares (itemization-phase-2.md s9.1 step 3). `keep_role` (the default) only
    considers shapes within `allowed_primary_stats` (else every shape): plain least squares prefers a spread-out trio,
    so a Strength / Agility item would otherwise land on Str/Int/SpellPower."""
    weights = {s: stats[s] * catalog.costs.get(s, 1.0) for s in PRIMARY_STATS if stats.get(s, 0) > 0}
    total = sum(weights.values())
    if total <= 0:
        return None
    vector = {s: w / total for s, w in weights.items()}
    candidates = catalog.primaries()
    if keep_role:
        allowed = allowed_primary_stats(stats)
        candidates = [s for s in candidates if set(s["stats"]) <= allowed] or candidates
    best = None
    for shape in candidates:
        alloc = {s: a / 10000 for s, a in zip(shape["stats"], shape["alloc"])}
        distance = sum((vector.get(s, 0.0) - alloc.get(s, 0.0)) ** 2 for s in set(vector) | set(alloc))
        if best is None or distance < best[0] - 1e-12:
            best = (distance, shape["shape_id"])
    return best[1] if best else None


def type_main_stat(row: dict) -> tuple[int | None, str]:
    """Ruling 18: (main stat, how) by item type; None with "no main stat" for cloaks, rings and necks, and None with
    "uncovered ..." for a type the ruling does not name. Alternating = even entry the first stat, odd the second."""
    entry, item_class = _int(row.get("entry")), _int(row.get("class"))
    subclass, inv_type = _int(row.get("subclass")), _int(row.get("InventoryType"))
    even = entry % 2 == 0
    if inv_type in NO_MAIN_STAT_INV_TYPES:
        return None, "cloak, ring or neck"
    if item_class == ITEM_CLASS_ARMOR:
        if subclass == ARMOR_CLOTH:
            return INT, "cloth"
        if subclass == ARMOR_LEATHER:
            return AGI, "leather"
        if subclass == ARMOR_MAIL:
            return (AGI, "mail, even entry") if even else (INT, "mail, odd entry")
        if subclass in (ARMOR_PLATE, ARMOR_SHIELD):
            return STR, "plate" if subclass == ARMOR_PLATE else "shield"
        return None, f"uncovered armor {subclass}/{inv_type}"
    if item_class == ITEM_CLASS_WEAPON:
        weapon = {
            0: (STR, "one-handed axe"), 1: (STR, "two-handed axe"), 2: (AGI, "bow"), 3: (AGI, "gun"),
            5: (STR, "two-handed mace"), 6: (AGI, "polearm"), 8: (STR, "two-handed sword"), 10: (INT, "staff"),
            13: (AGI, "fist weapon"), 15: (AGI, "dagger"), 16: (AGI, "thrown"), 18: (AGI, "crossbow"),
            19: (INT, "wand"),
        }
        if subclass in weapon:
            return weapon[subclass]
        if subclass == 4:
            return (STR, "one-handed mace, even entry") if even else (INT, "one-handed mace, odd entry")
        if subclass == 7:
            return (STR, "one-handed sword, even entry") if even else (AGI, "one-handed sword, odd entry")
        return None, f"uncovered weapon {subclass}"
    return None, f"uncovered class {item_class}"


@dataclass
class Decision:
    entry: int
    name: str
    quest_level: int
    quests: list[Quest]
    stock_quality: int
    stock_ilvl: int
    quality: int
    ilvl: int
    primary: int  # shape id, 0 = Null
    secondary: int
    share: int
    kept: tuple[int, ...]
    absorbed: tuple[int, ...]
    stock: dict[int, int]  # rule 4's stat read
    paths: list[str] = field(default_factory=list)  # rule paths taken, for the report
    fallbacks: list[str] = field(default_factory=list)  # every fallback, for the report

    @property
    def spells_field(self) -> str:
        if not self.kept:
            return "-"
        if not self.absorbed:
            return "all"
        return ",".join(map(str, self.kept))


def _shape_ids(catalog: Catalog, pred) -> list[int]:
    return [s["shape_id"] for s in catalog.secondaries() if pred(s)]


def _pick(pool: list[int], entry: int) -> int:
    return sorted(pool)[entry % len(pool)]


def tank_stat(stock: dict[int, int], row: dict) -> tuple[int | None, str]:
    """Ruling 12: the tank stat an item keeps (Defense converted), the heaviest one, and how it was found."""
    item_class, subclass = _int(row.get("class")), _int(row.get("subclass"))
    weights: dict[int, int] = {}
    how = []
    for stat in (DODGE, PARRY, BLOCK):
        if stock.get(stat, 0) > 0:
            weights[stat] = weights.get(stat, 0) + stock[stat]
    if stock.get(DEFENSE, 0) > 0:
        if item_class == ITEM_CLASS_ARMOR and subclass == ARMOR_SHIELD:
            converted = BLOCK
        elif item_class == ITEM_CLASS_ARMOR and subclass == ARMOR_PLATE:
            converted = PARRY
        else:
            converted = DODGE
        weights[converted] = weights.get(converted, 0) + stock[DEFENSE]
        how.append(f"Defense->{STAT_NAMES[converted]}")
    if not weights:
        return None, ""
    stat = max(sorted(weights), key=lambda s: weights[s])
    return stat, ", ".join(how)


def decide(entry: int, quests: list[Quest], row: dict, base_row: dict, spells: dict[int, dict],
           catalog: Catalog) -> Decision:
    """Rules 3-8 for one in-scope item. `row` is the current (replayed) row, `base_row` the base dump's."""
    quest_level = quests[0].level
    stock_quality, stock_ilvl = _int(row.get("Quality")), _int(row.get("ItemLevel"))
    quality, ilvl, level_path = target(stock_quality, stock_ilvl, quest_level)
    stock = stock_read(base_row, spells)
    kept, absorbed = spell_slots(row, spells)
    d = Decision(entry, str(row.get("name") or ""), quest_level, quests, stock_quality, stock_ilvl, quality, ilvl,
                 0, 0, 0, kept, absorbed, stock)
    d.paths.append(f"{QUALITY_NAMES[stock_quality]}->{QUALITY_NAMES[quality]}" if quality != stock_quality
                   else QUALITY_NAMES[quality])
    d.paths.append(level_path)

    # Rule 5: the primary shape.
    inv_type = _int(row.get("InventoryType"))
    if inv_type in NO_MAIN_STAT_INV_TYPES:
        primary = 0
        d.paths.append("no primary (jewelry/cloak)")
    elif stock_quality == COMMON:
        stat, how = type_main_stat(row)
        if stat is None:
            primary = 0
            d.fallbacks.append(f"white, {how}: Null primary")
        else:
            primary = catalog.by_name(PRIMARY_SOLO[stat])
            d.paths.append(f"type {STAT_NAMES[stat]} ({how})")
    else:
        nearest = nearest_primary(stock, catalog)
        if nearest is not None:
            primary = nearest
        else:
            stat, how = type_main_stat(row)
            if stat not in (None, STR, AGI) and tank_stat(stock, row)[0] is not None:
                stat, how = AGI, f"{how}, a tank item: Agi"  # a tank stat needs a Strength or Agility primary
            if stat is None:
                primary = 0
                d.fallbacks.append(f"no stock primary, {how}: Null primary")
            else:
                primary = catalog.by_name(PRIMARY_SOLO[stat])
                d.fallbacks.append(f"no stock primary: type {STAT_NAMES[stat]} ({how})")
    d.primary = primary
    primary_stats = set(catalog.stats(primary))

    # Rule 6: the secondary shape.
    count = {UNCOMMON: (1,), RARE: (2,), EPIC: (2, 3)}[quality]
    generic = _shape_ids(catalog, lambda s: not s["rules"] and len(s["stats"]) in count
                         and set(s["stats"]) <= GENERIC_SECONDARY_STATS)
    tank, converted = tank_stat(stock, row)
    secondary = None
    if tank is not None:
        if converted:
            d.paths.append(converted)
        wanted = tank
        if wanted in (PARRY, BLOCK) and STR not in primary_stats:
            d.fallbacks.append(f"{STAT_NAMES[wanted]} needs Str: Dodge")
            wanted = DODGE
        if quality == UNCOMMON:
            pool = _shape_ids(catalog, lambda s: s["stats"] == [wanted] and rules_ok(s, primary_stats)
                              and s["name"] != DODGE_ANY)
        else:
            pool = _shape_ids(catalog, lambda s: len(s["stats"]) == 2 and s["stats"][0] == wanted
                              and set(s["stats"][1:]) <= GENERIC_SECONDARY_STATS and rules_ok(s, primary_stats))
        if pool:
            secondary = _pick(pool, entry)
        else:
            secondary = catalog.by_name(DODGE_ANY)
            if wanted != DODGE:
                d.fallbacks.append(f"no {STAT_NAMES[wanted]} shape fits: Dodge")
            d.fallbacks.append(f"Dodge needs Str/Agi: {DODGE_ANY}"
                               + ("" if quality == UNCOMMON else ", one stat not two"))
        d.paths.append(f"tank {STAT_NAMES[catalog.stats(secondary)[0]]}")
        if stock.get(MP5, 0) > 0:
            d.fallbacks.append("MP5 lost to the tank stat")
    elif stock.get(MP5, 0) > 0:
        if quality == RARE:
            pool = _shape_ids(catalog, lambda s: len(s["stats"]) == 2 and s["stats"][0] == MP5
                              and set(s["stats"][1:]) <= GENERIC_SECONDARY_STATS and rules_ok(s, primary_stats))
            if pool:
                secondary = _pick(pool, entry)
                d.paths.append("MP5 kept")
            else:
                d.fallbacks.append("MP5 lost: Spirit primary kept (MP5 forbids Spirit)")
        else:
            d.fallbacks.append(f"MP5 lost: blues only ({QUALITY_NAMES[quality]})")
    if secondary is None:
        secondary = _pick(generic, entry)
    d.secondary = secondary

    # Rule 7: the primary share.
    if primary == 0:
        d.share = 0
    elif quality == UNCOMMON:
        d.share = SHARE_GREEN
    elif quality == RARE:
        d.share = SHARE_BLUE
    else:
        d.share = SHARE_EPIC_TRIO if len(catalog.stats(secondary)) == 3 else SHARE_EPIC_PAIR
    if kept:
        d.paths.append("keeps spell " + ",".join(map(str, kept)))
    return d


def decide_all(scoped: Scope, rows: dict[int, dict], base_rows: dict[int, dict], spells: dict[int, dict],
               catalog: Catalog) -> list[Decision]:
    """Every in-scope item's decision. An item missing from the base dump (a custom row) reads its current row."""
    return [decide(entry, quests, rows[entry], base_rows.get(entry, rows[entry]), spells, catalog)
            for entry, quests in sorted(scoped.items.items())]


# ---------------------------------------------------------------------------------------------------------------------
# Ownership (rule 1)


def _literal_int_calls(path: Path, func_name: str, keyword: str | None) -> set[int]:
    """Literal int arguments of every `func_name(...)` call in `path`: the `keyword=` value, or (keyword None) the
    first positional argument."""
    found: set[int] = set()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
        if name != func_name:
            continue
        values = ([k.value for k in node.keywords if k.arg == keyword] if keyword is not None
                  else node.args[:1])
        for value in values:
            if isinstance(value, ast.Constant) and isinstance(value.value, int) and not isinstance(value.value, bool):
                found.add(value.value)
    return found


def owned_elsewhere(tool_root: Path = TOOL_ROOT) -> dict[int, str]:
    """{entry: owner} of the item entries another dbc-tools declaration owns: `item(base=<entry>)` in
    `source/items/*.py` (not quest_rewards.py), a non-quest-reward line of `item_ids.lock`, an `items.csv` row, or a
    literal `item_template(<entry>, ...)` anywhere under `source/` (source/world/ranged_weapons.py yields to
    source/items itself, so it is not an owner)."""
    source = tool_root / "source"
    items_dir = source / "items"
    owned: dict[int, str] = {}
    for path in sorted(items_dir.glob("*.py")):
        if path.name.startswith("_") or path.name == SOURCE_FILE:
            continue
        for entry in _literal_int_calls(path, "item", "base"):
            owned.setdefault(entry, f"source/items/{path.name}")
    lock = items_dir / "item_ids.lock"
    if lock.is_file():
        for raw in lock.read_text(encoding="utf-8").splitlines():
            fields = raw.split("#", 1)[0].split()
            if len(fields) >= 2 and fields[0].isdigit() and not fields[1].startswith(KEY_PREFIX):
                owned.setdefault(int(fields[0]), f"item_ids.lock ({fields[1]})")
    csv_path = source / "items.csv"
    if csv_path.is_file():
        for raw in csv_path.read_text(encoding="utf-8").splitlines()[1:]:
            head = raw.split(",", 1)[0].strip()
            if head.isdigit():
                owned.setdefault(int(head), "source/items.csv")
    for path in sorted(source.rglob("*.py")):
        if path.name.startswith("_") or path.relative_to(source).as_posix() == "world/ranged_weapons.py":
            continue
        for entry in _literal_int_calls(path, "item_template", None):
            owned.setdefault(entry, f"source/{path.relative_to(source).as_posix()} item_template()")
    return owned


# ---------------------------------------------------------------------------------------------------------------------
# The lock


LOCK_HEADER = """\
# Quest reward itemization (docs/plans/quest-reward-itemization/, lib/quest_rewards.py): one stock quest reward per
# line, declared by source/items/quest_rewards.py as item(base=<entry>) on the one-tier quest_reward ladder.
#   <entry> <quest level> <quality> <ilvl> <primary shape id> <secondary shape id> <share> <spells>  # <name> -- <why>
# <quality> and <ilvl> are the new ones; shape ids are item_shape.shape_id (0 = Null, no primary); <share> is
# primary_share (0/4000/6000/8000/10000); <spells> is - (stock spell slots absorbed), all (keep_spells=True) or the
# kept slot numbers (1,3: the other slots are absorbed). The comment (shapes as stats, the rule path, FB = a
# fallback; a long one continues on the `#   ` lines below) is for the reader; only the fields are read.
# Seeded by `python3 apps/dbc-tools/quest_rewards_lock.py --seed-quest-rewards`; append-only afterwards: a seed run
# appends new entries and never rewrites a line, so hand edits stay. To hand an entry to another declaration (a
# dungeon item file), delete its line first: one owner per entry.
"""
MAX_LINE = 120  # .editorconfig: a longer comment continues on `#   ` lines under its entry
CONTINUATION = "#   "
_SPELLS_RE = re.compile(r"^(-|all|[1-5](,[1-5])*)$")
LINE_FIELDS = 8


class LockError(ValueError):
    pass


@dataclass(frozen=True)
class LockLine:
    entry: int
    quest_level: int
    quality: int
    ilvl: int
    primary: int
    secondary: int
    share: int
    spells: str  # "-", "all" or "1,3"
    comment: str = ""

    @property
    def key(self) -> str:
        return f"{KEY_PREFIX}{self.entry}"

    @property
    def kept_slots(self) -> tuple[int, ...] | None:
        """None: keep every stock spell (`all`); () none kept; else the kept slots."""
        if self.spells == "all":
            return None
        if self.spells == "-":
            return ()
        return tuple(int(s) for s in self.spells.split(","))


def waits_for_weapon_curve(line: LockLine, row: dict) -> bool:
    """True when the declaration must skip `line` for now: a green weapon while `UNCOMMON_WEAPONS_WAIT`."""
    return UNCOMMON_WEAPONS_WAIT and _int(row.get("class")) == ITEM_CLASS_WEAPON and line.quality == UNCOMMON


def parse_lock(text: str, where: str = "quest_rewards.lock") -> dict[int, LockLine]:
    """{entry: LockLine}; raises LockError on a malformed or repeated line."""
    out: dict[int, LockLine] = {}
    for number, raw in enumerate(text.splitlines(), 1):
        body, _, comment = raw.partition("#")
        fields = body.split()
        if not fields:
            continue
        try:
            if len(fields) != LINE_FIELDS or not _SPELLS_RE.match(fields[7]):
                raise ValueError
            line = LockLine(*(int(f) for f in fields[:7]), fields[7], comment.strip())
        except ValueError:
            raise LockError(f"{where} line {number}: malformed line {raw.strip()!r}") from None
        if line.entry in out:
            raise LockError(f"{where} line {number}: entry {line.entry} is already on an earlier line")
        out[line.entry] = line
    return out


def shape_text(catalog: Catalog, shape_id: int) -> str:
    """A shape as its stats, `Str` / `Dodge+Crit` (`-` for Null): the lock comment's short form."""
    stats = catalog.stats(shape_id)
    return "+".join(STAT_NAMES.get(s, str(s)) for s in stats) if stats else "-"


def render_line(d: Decision, catalog: Catalog) -> str:
    """The lock line of `d`; the comment says the shapes as stats, the rule path and every fallback (`FB`)."""
    why = "; ".join([p for p in d.paths if p] + [f"FB {f}" for f in d.fallbacks])
    head = (f"{d.entry} {d.quest_level} {d.quality} {d.ilvl} {d.primary} {d.secondary} {d.share} "
            f"{d.spells_field}")
    comment = f"{d.name} -- {shape_text(catalog, d.primary)} / {shape_text(catalog, d.secondary)}; {why}"
    first = textwrap.wrap(comment, width=MAX_LINE - len(head) - 4, break_long_words=False)
    rest = textwrap.wrap(comment[len(first[0]):].strip(), width=MAX_LINE - len(CONTINUATION),
                         break_long_words=False) if len(first) > 1 else []
    return "\n".join([f"{head}  # {first[0]}"] + [f"{CONTINUATION}{part}" for part in rest])


def seed(current: str, decisions: list[Decision], catalog: Catalog) -> tuple[str, list[str], list[int]]:
    """(new lock text, appended lines, locked entries no longer decided): appends a line for every decision whose
    entry has none; never rewrites or removes a line."""
    locked = parse_lock(current)
    text = current if current.strip() else LOCK_HEADER
    appended = [render_line(d, catalog) for d in decisions if d.entry not in locked]
    if appended:
        text = text + ("" if text.endswith("\n") else "\n") + "".join(f"{line}\n" for line in appended)
    decided = {d.entry for d in decisions}
    return text, appended, sorted(e for e in locked if e not in decided)


# ---------------------------------------------------------------------------------------------------------------------
# Inputs (impure)


@dataclass
class Inputs:
    quests: dict[int, dict]
    addons: dict[int, dict]
    rows: dict[int, dict]  # current item_template (base dump + every migration, pending and module SQL)
    base_rows: dict[int, dict]  # the base dump's item_template only
    spells: dict[int, dict]  # stock Spell.dbc by id
    catalog: Catalog
    tables: dict


def load_inputs() -> Inputs:
    """The replayed world tables (item-tools' replay: base dump plus migrations, pending and module SQL), the stock
    client Spell.dbc (`var/extractors/dbc`) and the itemization catalog."""
    from . import dbcfile, dbcfmt, item_variants, state  # noqa: PLC0415

    item_variants._item_lib()
    from item_lib import overlay, replay  # noqa: PLC0415

    with replay.session(cache=True):
        quests = {k[0]: v for k, v in replay.load_table("quest_template", ("ID",)).items()}
        addons = {k[0]: v for k, v in replay.load_table("quest_template_addon", ("ID",)).items()}
        base_rows = {k[0]: v for k, v in replay.load_table("item_template", ("entry",), files=[]).items()}
    rows = overlay.resolve_current_rows(cache=True)
    spell_path = state.BASE_DBC_DIR / dbcfmt.SPELL.dbc_filename
    if not spell_path.is_file():
        raise FileNotFoundError(f"{spell_path} is missing (copy var/extractors/dbc from the main checkout)")
    spells = {r["ID"]: r for r in dbcfile.read_dbc(spell_path, dbcfmt.SPELL)}
    tables, shape_catalog = item_variants.load_itemization_tables()
    return Inputs(quests, addons, rows, base_rows, spells, Catalog.from_tables(shape_catalog, tables), tables)


def run(inputs: Inputs, owned: dict[int, str] | None = None) -> tuple[Scope, list[Decision]]:
    scoped = scope(inputs.quests, inputs.addons, inputs.rows, owned_elsewhere() if owned is None else owned)
    return scoped, decide_all(scoped, inputs.rows, inputs.base_rows, inputs.spells, inputs.catalog)
