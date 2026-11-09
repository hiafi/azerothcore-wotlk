"""
Quest reward itemization (docs/plans/quest-reward-itemization/, stage QR0): which stock quest rewards move onto the
item stat system, and the per-item decisions (item level, quality, shapes, primary share, kept spells), frozen in
`source/items/quest_rewards.lock` and declared by `source/items/quest_rewards.py` as `item(base=<entry>, ...)` on the
one-tier `quest_reward` ladder (QR1).

Everything below `load_inputs()` is a pure function of plain dicts (the replayed world tables, the stock Spell.dbc
rows, the shape catalog and `item_stat_cost`), so the host tests (`lib/test_quest_rewards.py`) build them by hand.
The rules are PLAN section 3 (rulings 1-30 of the REQUIREMENTS; ruling 29's per-item edits are hand edits of the
lock, not rules):

1. **Scope.** Equippable rewards (`class` 2 weapon or 4 armor, not InventoryType 0, shirts 4 or tabards 19) of
   quests at `QuestLevel` 1-60 that are not repeatable (`SpecialFlags & 1`), daily (`Flags & 0x1000`) or weekly
   (`Flags & 0x8000`) and not raid (`QuestInfoID` 62) or PvP (41) quests. Rewards are `RewardItem1-4` and
   `RewardChoiceItemID1-6`. An item that any out-of-scope quest also rewards is out. A scaled (`QuestLevel` -1) class
   quest (`AllowableClasses` set or a class `QuestSortID`) counts at its `MinLevel` (round 5 default; above 60 it is
   out); any other scaled quest is out of scope, except the Argent Dawn gloves' quests (`RULED_SCALED_QUESTS`, round
   6 default: at MinLevel 50, 9094's repeatable flag ignored). Fishing poles and 10515 Torch of Retribution stay
   stock (ruling 25), as do 3567 Dwarven Fishing Pole and 864 Knightly Longsword (round 6 defaults; `STOCK_ENTRIES`).
   Legendary and Poor items are skipped (rulings 16, 17). An entry
   another declaration owns (`source/items/*.py` `item(base=...)`, `item_ids.lock`, `items.csv`, a literal
   `item_template(<entry>, ...)`) is skipped and reported (`owned_elsewhere()`): one owner per entry.
2. **Quest level**: the lowest quest level (`QuestLevel`, or `MinLevel` for a scaled class quest) of the quests
   that reward it.
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
   type main stat too (a reported fallback; ruled for held-in-off-hand items, Intellect, ruling 25). Cloaks, rings,
   necks and relics: no primary shape (Null, share 0; rulings 18 and 25). Trinkets with no main stat: Null (ruling
   22).
6. **Secondary shape.** Generic shapes over Crit, Haste, Mastery, Versatility, Cooldown Haste and Proc Chance: green
   one stat (Solo), blue two (pairs), epic two or three (pairs and trios), picked by `entry MOD pool size` over the
   eligible pool sorted by shape id. Tank stats (ruling 12): Dodge, Parry, Block or Defense in the stock read keep
   their stat (Defense becomes Block on a shield, Parry on other plate, Dodge on everything else; the heaviest tank
   stat wins); green takes that stat's Solo shape, blue and epic a pair of that stat and a generic companion. Parry
   and Block shapes need a Strength primary: else Dodge. Dodge shapes need Strength or Agility: an item that cannot
   take one (rings, necks, cloaks, trinkets, relics, Intellect or Spirit items) drops the tank stat (ruling 24); it
   takes "Versatility (Solo)" on a green, else a generic pair with Versatility (`entry MOD pool size` over the
   Versatility pairs). MP5 (ruling 13): a blue whose stock read has MP5
   takes an MP5 pair; a Spirit primary forbids MP5, so that item keeps Spirit and loses the MP5 (reported). Greens
   and epics lose MP5 (the ruling keeps it on blues only; reported).
7. **Primary share**: green 8000, blue 6000, epic 6000 with a pair secondary and 4000 with a trio; Null primary 0.
8. **Spells** (`spell_slots()`): on the current row, an Equip spell whose every effect is a stat
   (`spell_stat_effects()` returns its stats) is absorbed (`absorbed_spell_slots`, the item() default); Use, Chance
   on hit and every other Equip spell (procs, slaying, resistances, skills, ...) is kept. A kept effect gives the
   DSL's `budget_mult` 0.7 default.
9. **Resistances** are never written by the materializer: untouched, free (ruling 14).
10. **Warrior class quest gear** (ruling 30, the literal reading; `warrior_swap()`): when every class the item's
    quests are for is Warrior, a primary with Agility (Intellect) goes: Null primary, share 0, and a secondary of
    Crit (Proc Chance) plus the current secondary stat.
11. **Same name, same quest** (ruling 28, `apply_same_name()`): items sharing a name and their rewarding quest titles
    take the lowest entry's primary, secondary and share; a role variant (other main stats) keeps its primary.

The round 6 shapes (`HAND_ONLY_PRIMARIES`, `HAND_ONLY_SECONDARIES`) are for hand edits only; the rules never pick
them. `step_down_zero()` (`quest_rewards_lock.py --step-down-zero`) lowers the primary share of a lock line whose
secondary stat materializes to 0 while the primary keeps a point.

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
INV_NECK, INV_FINGER, INV_TRINKET, INV_SHIELD, INV_CLOAK, INV_HOLDABLE, INV_RELIC = 2, 11, 12, 14, 16, 23, 28
NO_MAIN_STAT_INV_TYPES = (INV_NECK, INV_FINGER, INV_CLOAK, INV_RELIC)  # rulings 18 and 25: all secondary
WEAPON_FISHING_POLE = 20
STOCK_ENTRIES = {  # in-scope rewards that stay stock
    10515: "Torch of Retribution (ruling 25)",
    3567: "Dwarven Fishing Pole (a gun by type; round 6 default)",
    864: "Knightly Longsword (test quest only; round 6 default)",
}
# Scaled (QuestLevel -1) quests that are not class quests but are in scope at their MinLevel (round 6 default): the
# Argent Dawn gloves (23078, 23081, 23082, 23084). 9094 is the repeatable copy of 9333; its repeatable flag is ignored.
RULED_SCALED_QUESTS = {9094: "Argent Dawn Gloves", 9333: "Argent Dawn Gloves"}
# QuestSortID of the class quest sorts (QuestSort.dbc): Warlock, Warrior, Shaman, Paladin, Mage, Rogue, Hunter, Priest,
# Druid, Death Knight. The other negative sorts are professions, holidays and other non-zone groups.
CLASS_QUEST_SORTS = {-61: "Warlock", -81: "Warrior", -82: "Shaman", -141: "Paladin", -161: "Mage", -162: "Rogue",
                     -261: "Hunter", -262: "Priest", -263: "Druid", -372: "Death Knight"}
CLASS_NAMES = {1: "Warrior", 2: "Paladin", 3: "Hunter", 4: "Rogue", 5: "Priest", 6: "Death Knight", 7: "Shaman",
               8: "Mage", 9: "Warlock", 11: "Druid"}  # ChrClasses ids (AllowableClasses bit = id - 1)
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
SHARE_GREEN, SHARE_BLUE, SHARE_EPIC_PAIR, SHARE_EPIC_TRIO = 8000, 6000, 6000, 4000

PRIMARY_SOLO = {STR: "Strength (Solo)", AGI: "Agility (Solo)", INT: "Intellect (Solo)"}
# Round 6 shapes for the designer's hand edits (ruling 29), kept out of the nearest-primary search so the rules'
# picks for Spell Power or Attack Power only items stay as they were.
HAND_ONLY_PRIMARIES = frozenset(("Spell Power (Solo)", "Attack Power (Solo)"))
HAND_ONLY_SECONDARIES = frozenset(("Parry/Versatility (Any)",))  # likewise out of the tank pools
DODGE_ANY = "Dodge (Solo, Any)"
VERSATILITY_SOLO = "Versatility (Solo)"


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
    scaled: bool = False  # a QuestLevel -1 class quest (or RULED_SCALED_QUESTS): `level` is its MinLevel
    classes: frozenset[str] = frozenset()  # the classes it is for (`quest_classes()`); empty for any class


def reward_map(quests: dict[int, dict]) -> dict[int, set[int]]:
    """{item entry: {quest ids that reward it}} over `RewardItem1-4` and `RewardChoiceItemID1-6`."""
    out: dict[int, set[int]] = {}
    for qid, row in quests.items():
        for column in REWARD_COLUMNS:
            item = _int(row.get(column))
            if item > 0:
                out.setdefault(item, set()).add(int(qid))
    return out


def is_class_quest(quest: dict, addon: dict | None) -> bool:
    """A real class quest: `AllowableClasses` set, or a class `QuestSortID` (not a profession or holiday sort)."""
    return bool(_int((addon or {}).get("AllowableClasses"))) or _int(quest.get("QuestSortID")) in CLASS_QUEST_SORTS


def quest_classes(quest: dict, addon: dict | None) -> frozenset[str]:
    """The classes a quest is for: the `AllowableClasses` bits, else a class `QuestSortID`'s class; empty for any."""
    mask = _int((addon or {}).get("AllowableClasses"))
    if mask:
        return frozenset(name for cid, name in CLASS_NAMES.items() if mask & (1 << (cid - 1)))
    sort = _int(quest.get("QuestSortID"))
    return frozenset((CLASS_QUEST_SORTS[sort],)) if sort in CLASS_QUEST_SORTS else frozenset()


def quest_level(quest: dict, addon: dict | None) -> tuple[int, bool]:
    """(quest level, scaled): `QuestLevel`, or for a scaled (-1) class quest its `MinLevel` (round 5 default; round 6
    adds the RULED_SCALED_QUESTS)."""
    level = _int(quest.get("QuestLevel"))
    if level == -1 and (is_class_quest(quest, addon) or _int(quest.get("ID")) in RULED_SCALED_QUESTS):
        return _int(quest.get("MinLevel")), True
    return level, False


def quest_out_of_scope(quest: dict, addon: dict | None) -> str | None:
    """Why a quest is out of scope (None: in scope)."""
    level, scaled = quest_level(quest, addon)
    if not MIN_QUEST_LEVEL <= level <= MAX_QUEST_LEVEL:
        return f"scaled class quest, MinLevel {level}" if scaled else f"quest level {level}"
    if (_int((addon or {}).get("SpecialFlags")) & QUEST_SPECIAL_REPEATABLE
            and _int(quest.get("ID")) not in RULED_SCALED_QUESTS):
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


def _level_and(quest: dict, addon: dict | None) -> tuple[int, str, str, bool, frozenset[str]]:
    level, scaled = quest_level(quest, addon)
    return level, str(quest.get("LogTitle") or ""), quest_kind(quest, addon), scaled, quest_classes(quest, addon)


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
        if _int(row.get("class")) == ITEM_CLASS_WEAPON and _int(row.get("subclass")) == WEAPON_FISHING_POLE:
            out.skipped[entry] = "fishing pole (ruling 25)"
            continue
        if entry in STOCK_ENTRIES:
            out.skipped[entry] = STOCK_ENTRIES[entry]
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
            (Quest(q, *_level_and(quests[q], addons.get(q))) for q in qids),
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
    candidates = [s for s in catalog.primaries() if s["name"] not in HAND_ONLY_PRIMARIES]
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
    """Rulings 18, 22 and 25: (main stat, how) by item type; None for cloaks, rings, necks, relics and trinkets (all
    secondary), and None with "uncovered ..." for a type no ruling names. Alternating = even entry the first stat, odd
    the second. `how` names the ruling when one covers every quality (`ruled_type()`)."""
    entry, item_class = _int(row.get("entry")), _int(row.get("class"))
    subclass, inv_type = _int(row.get("subclass")), _int(row.get("InventoryType"))
    even = entry % 2 == 0
    if inv_type == INV_RELIC:
        return None, "relic, ruling 25"
    if inv_type in NO_MAIN_STAT_INV_TYPES:
        return None, "cloak, ring or neck"
    if inv_type == INV_HOLDABLE:
        return INT, "held in off-hand, ruling 25"
    if inv_type == INV_TRINKET:
        return None, "trinket, ruling 22"
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


def ruled_type(how: str) -> bool:
    """True when `type_main_stat()`'s answer is ruled for every quality (rulings 22 and 25), not only for whites."""
    return ", ruling " in how


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
    return [s["shape_id"] for s in catalog.secondaries() if s["name"] not in HAND_ONLY_SECONDARIES and pred(s)]


def generic_pairs(catalog: Catalog) -> set[int]:
    """The generic two-stat secondary shapes (no rules, both stats generic): the blue pool."""
    return set(_shape_ids(catalog, lambda s: not s["rules"] and len(s["stats"]) == 2
                          and set(s["stats"]) <= GENERIC_SECONDARY_STATS))


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
        d.paths.append("no primary (relic)" if inv_type == INV_RELIC else "no primary (jewelry/cloak)")
    elif stock_quality == COMMON:
        stat, how = type_main_stat(row)
        if stat is None:
            primary = 0
            (d.paths.append(f"no primary ({how})") if ruled_type(how)
             else d.fallbacks.append(f"white, {how}: Null primary"))
        else:
            primary = catalog.by_name(PRIMARY_SOLO[stat])
            d.paths.append(f"type {STAT_NAMES[stat]} ({how})")
    else:
        nearest = nearest_primary(stock, catalog)
        if nearest is not None:
            primary = nearest
        else:
            stat, how = type_main_stat(row)
            if (stat not in (None, STR, AGI) and inv_type != INV_HOLDABLE
                    and tank_stat(stock, row)[0] is not None):
                stat, how = AGI, f"{how}, a tank item: Agi"  # a tank stat needs a Strength or Agility primary
            ruled = ruled_type(how)
            if stat is None:
                primary = 0
                (d.paths.append(f"no primary ({how})") if ruled
                 else d.fallbacks.append(f"no stock primary, {how}: Null primary"))
            else:
                primary = catalog.by_name(PRIMARY_SOLO[stat])
                (d.paths.append(f"type {STAT_NAMES[stat]} ({how})") if ruled
                 else d.fallbacks.append(f"no stock primary: type {STAT_NAMES[stat]} ({how})"))
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
            d.paths.append(f"tank {STAT_NAMES[catalog.stats(secondary)[0]]}")
        else:
            # Ruling 24: no Dodge shape fits (no Strength or Agility primary): drop the tank stat for Versatility.
            if quality == UNCOMMON:
                secondary = catalog.by_name(VERSATILITY_SOLO)
            else:
                secondary = _pick(_shape_ids(catalog, lambda s: s["shape_id"] in generic_pairs(catalog)
                                             and VERSATILITY in s["stats"]), entry)
            d.paths.append(f"tank {STAT_NAMES[wanted]} dropped, no Str/Agi (ruling 24): Vers")
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
    if set().union(*(q.classes for q in quests)) == {WARRIOR}:
        warrior_swap(d, catalog)
    if kept:
        d.paths.append("keeps spell " + ",".join(map(str, kept)))
    return d


WARRIOR = "Warrior"
WARRIOR_SWAPS = ((AGI, CRIT), (INT, PROC))  # ruling 30: on Warrior class quest gear


def _secondary_with(catalog: Catalog, stats: list[int]) -> int | None:
    """The rule-free secondary shape whose stats are exactly `stats` (lowest id: the Even shape before a lead one)."""
    found = [s["shape_id"] for s in catalog.secondaries()
             if set(s["stats"]) == set(stats) and len(s["stats"]) == len(set(stats)) and rules_ok(s, set())]
    return min(found) if found else None


def warrior_swap(d: Decision, catalog: Catalog) -> None:
    """Ruling 30, the literal reading: on Warrior class quest gear a primary with Agility (Intellect) gives it up for
    Crit (Proc Chance). The item takes the Null primary (share 0) and a secondary of the new stat plus its current
    secondary stats (a pair from a Solo, Crit Solo when the current one is Crit already); when no shape has them all,
    the new stat plus the first current one, else the new stat alone."""
    primary_stats = catalog.stats(d.primary)
    new = [stat for old, stat in WARRIOR_SWAPS if old in primary_stats]
    if not new:
        return
    current = [s for s in catalog.stats(d.secondary) if s not in new]
    secondary = (_secondary_with(catalog, new + current) or (current and _secondary_with(catalog, new + current[:1]))
                 or _secondary_with(catalog, new))
    if secondary is None:
        d.fallbacks.append("ruling 30: no secondary shape for " + "+".join(STAT_NAMES[s] for s in new))
        return
    swaps = ", ".join(f"{STAT_NAMES[old]}->{STAT_NAMES[stat]}" for old, stat in WARRIOR_SWAPS if stat in new)
    d.paths.append(f"round 6: Warrior gear {swaps} (ruling 30): no primary, "
                   f"{shape_text(catalog, d.secondary)} -> {shape_text(catalog, secondary)}")
    d.primary, d.secondary, d.share = 0, secondary, 0


def same_name_groups(decisions: list[Decision]) -> list[list[Decision]]:
    """Ruling 28's groups: two or more items with the same name and the same rewarding quest titles, lowest entry
    first."""
    groups: dict[tuple, list[Decision]] = {}
    for d in sorted(decisions, key=lambda x: x.entry):
        groups.setdefault((d.name, frozenset(q.title for q in d.quests)), []).append(d)
    return [members for members in groups.values() if len(members) > 1]


def apply_same_name(decisions: list[Decision], catalog: Catalog) -> list[list[Decision]]:
    """Ruling 28: in each `same_name_groups()` group every item takes the lowest entry's primary shape, secondary shape
    and share (item level and quality stay its own). A member whose own primary has other main stats than the lowest
    entry's (a choice of role variants, e.g. Troll Kickers Str / Int+SP / Agi) keeps its primary and share and takes
    only the secondary. Returns the groups."""
    groups = same_name_groups(decisions)
    for lead, *rest in groups:
        lead_stats = set(catalog.stats(lead.primary))
        for d in rest:
            before = (d.primary, d.secondary, d.share)
            if set(catalog.stats(d.primary)) == lead_stats:
                d.primary, d.share = lead.primary, lead.share
                how = ""
            else:
                how = f"; keeps its own primary ({shape_text(catalog, d.primary)} variant)"
            if rules_ok(catalog.shapes[lead.secondary], set(catalog.stats(d.primary))):
                d.secondary = lead.secondary
            if (d.primary, d.secondary, d.share) != before:
                d.paths.append(f"round 6: as {lead.entry}, same name and quest (ruling 28){how}")
    return groups


def decide_all(scoped: Scope, rows: dict[int, dict], base_rows: dict[int, dict], spells: dict[int, dict],
               catalog: Catalog) -> list[Decision]:
    """Every in-scope item's decision, then ruling 28 (`apply_same_name()`). An item missing from the base dump (a
    custom row) reads its current row."""
    decisions = [decide(entry, quests, rows[entry], base_rows.get(entry, rows[entry]), spells, catalog)
                 for entry, quests in sorted(scoped.items.items())]
    apply_same_name(decisions, catalog)
    return decisions


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
    return _wrap(head, comment)


def _wrap(head: str, comment: str) -> str:
    first = textwrap.wrap(comment, width=MAX_LINE - len(head) - 4, break_long_words=False, break_on_hyphens=False)
    rest = textwrap.wrap(comment[len(first[0]):].strip(), width=MAX_LINE - len(CONTINUATION),
                         break_long_words=False, break_on_hyphens=False) if len(first) > 1 else []
    return "\n".join([f"{head}  # {first[0]}"] + [f"{CONTINUATION}{part}" for part in rest])


def render_lock_line(line: LockLine) -> str:
    """A LockLine as lock text (its comment wrapped like `render_line()`)."""
    head = (f"{line.entry} {line.quest_level} {line.quality} {line.ilvl} {line.primary} {line.secondary} "
            f"{line.share} {line.spells}")
    return _wrap(head, line.comment) if line.comment else head


def replace_lines(text: str, lines: dict[int, LockLine]) -> str:
    """`text` with the line of each entry in `lines` (and its `#   ` continuation lines) replaced in place; raises
    LockError for an entry that has no line. The hand-edit path: a seed run never rewrites a line."""
    out: list[str] = []
    done: set[int] = set()
    skipping = False
    for raw in text.splitlines():
        if skipping and raw.startswith(CONTINUATION):
            continue
        skipping = False
        fields = raw.partition("#")[0].split()
        if fields and fields[0].isdigit() and int(fields[0]) in lines:
            entry = int(fields[0])
            out.append(render_lock_line(lines[entry]))
            done.add(entry)
            skipping = True
            continue
        out.append(raw)
    missing = sorted(set(lines) - done)
    if missing:
        raise LockError(f"no lock line for {missing}")
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def lock_comments(text: str) -> dict[int, str]:
    """{entry: the whole comment, continuation lines joined (a line that ends in a word and a hyphen joins the next
    without a space: the wrap broke a hyphenated word there)}."""
    out: dict[int, str] = {}
    current = None
    for raw in text.splitlines():
        if raw.startswith(CONTINUATION) and current is not None:
            part = raw[len(CONTINUATION):].strip()
            # Older lines were wrapped at hyphens ("one-" / "handed"): rejoin those without a space.
            glue = "" if re.search(r"[A-Za-z]-$", out[current]) and part[:1].isalpha() else " "
            out[current] += glue + part
            continue
        body, _, comment = raw.partition("#")
        fields = body.split()
        current = int(fields[0]) if fields and fields[0].isdigit() else None
        if current is not None:
            out[current] = comment.strip()
    return out


SHARE_STEPS = (8000, 6000, 4000, 0)  # PRIMARY_SHARES below a green's 8000, high to low


def zero_secondaries(lock: dict[int, LockLine], mat: Materialized, catalog: Catalog) -> dict[int, list[int]]:
    """{entry: the secondary shape's stats that materialize to 0 points} (a stat at 0 is left off the item)."""
    out: dict[int, list[int]] = {}
    for entry, line in lock.items():
        row = mat.rows.get(entry)
        if row is None:
            continue
        have = _positive_stats(row)
        zero = [s for s in catalog.stats(line.secondary) if s not in have]
        if zero:
            out[entry] = zero
    return out


def step_down_zero(text: str, rows: dict[int, dict], tables: dict, shape_catalog: dict, catalog: Catalog,
                   max_rounds: int = len(SHARE_STEPS)) -> tuple[str, dict[int, tuple[int, int, list[int]]],
                                                               dict[int, list[int]], dict[int, list[int]]]:
    """Round 6 (ruling 29, the Primitive weapons, and every other lock line like them): a line whose secondary shape
    materializes a stat to 0 points steps its primary share down (`step_down()`) until every secondary stat is at
    least 1 or the share is 0. A line whose stat is still 0 at share 0, or whose primary stats all fall to 0 at the
    first share that lifts it, keeps its share. Returns (new lock text, {entry: (old share, new share, the stats that
    were 0)}, {entry: the stats still 0 at share 0, share kept}, {entry: the stats a step-down would only buy with
    the main stat, share kept}). The changed lines' comments say so."""
    first: dict[int, tuple[int, list[int]]] = {}
    stuck: dict[int, list[int]] = {}
    for _ in range(max_rounds):
        lock = parse_lock(text)
        zero = zero_secondaries(lock, materialize(lock, rows, tables, shape_catalog), catalog)
        lower = {e: line for e, stats in zero.items() if (line := step_down(lock[e])) is not None}
        stuck = {e: stats for e, stats in zero.items() if e not in lower}
        if not lower:
            break
        for e in lower:
            first.setdefault(e, (lock[e].share, zero[e]))
        comments = lock_comments(text)
        text = replace_lines(text, {e: LockLine(e, line.quest_level, line.quality, line.ilvl, line.primary,
                                                line.secondary, line.share, line.spells, comments[e])
                                    for e, line in lower.items()})
    # A line still at 0 with share 0 gained nothing from stepping down (its whole budget is too small), and one whose
    # primary stats all fell to 0 only swapped its main stat for the secondary (ruling 6 keeps the main stat; a lower
    # share only lowers the primary further): both keep their share. The others say what changed.
    lock = parse_lock(text)
    comments = lock_comments(text)
    stepped = {e: lock[e] for e in first if e not in stuck}
    mat = materialize(stepped, rows, tables, shape_catalog) if stepped else None
    blocked = {e: first[e][1] for e in stepped if catalog.stats(lock[e].primary)
               and not set(catalog.stats(lock[e].primary)) & _positive_stats(mat.rows[e])}
    keep = set(stuck) | set(blocked)
    changes = {e: (old, lock[e].share, stats) for e, (old, stats) in first.items() if e not in keep}
    lines = {e: LockLine(e, lock[e].quest_level, lock[e].quality, lock[e].ilvl, lock[e].primary, lock[e].secondary,
                         first[e][0], lock[e].spells, comments[e]) for e in keep if e in first}
    lines.update({e: LockLine(
        e, lock[e].quest_level, lock[e].quality, lock[e].ilvl, lock[e].primary, lock[e].secondary, lock[e].share,
        lock[e].spells, f"{comments[e]}; round 6 step-down: share {old}->{new} so "
        + "/".join(STAT_NAMES[s] for s in stats) + " is at least 1") for e, (old, new, stats) in changes.items()})
    return replace_lines(text, lines) if lines else text, changes, stuck, blocked


def _positive_stats(row: dict) -> set[int]:
    return {_int(row.get(f"stat_type{n}")) for n in range(1, 11) if _int(row.get(f"stat_value{n}")) > 0}


def step_down(line: LockLine) -> LockLine | None:
    """The line with its primary share one step lower (`SHARE_STEPS`), None when it is at 0 already."""
    lower = [s for s in SHARE_STEPS if s < line.share]
    if not lower:
        return None
    return LockLine(line.entry, line.quest_level, line.quality, line.ilvl, line.primary, line.secondary, lower[0],
                    line.spells, line.comment)


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


@dataclass
class Materialized:
    rows: dict[int, dict]  # entry -> the emitted item_template row (new stats, item level, damage, armor)
    itemization: dict[int, dict]  # entry -> its item_itemization row
    errors: list[str]  # expansion and emit errors about a quest reward (qr_) item
    labels: dict  # tooltip labels the emit would add (ruling 20: none)


def materialize(lock: dict[int, LockLine], rows: dict[int, dict], tables: dict, shape_catalog: dict) -> Materialized:
    """Expand and emit every lock line as source/items/quest_rewards.py declares it (without the registry): the rows a
    write run would produce, for the real-data test and the designer review lists (quest_rewards_review.py). `rows`
    are the current item rows (`item_lib.overlay.resolve_current_rows()`)."""
    from . import item_emit, item_variants, spell_tables  # noqa: PLC0415
    from .dsl import items as D  # noqa: PLC0415

    ladder = D.ladder("quest_reward", normal=D.tier(step=0, label=None))
    decls = []
    for line in lock.values():
        row = rows[line.entry]
        extra: dict = {"keep_spells": True} if line.kept_slots is None else {}
        if line.kept_slots:
            extra["spells"] = tuple(D.ItemSpell(_int(row[f"spellid_{n}"]), _int(row[f"spelltrigger_{n}"]))
                                    for n in line.kept_slots)
        decls.append({"id": line.key, "_decl": D.item(
            line.key, base=line.entry, ladder=ladder, ilvl=line.ilvl, quality=line.quality, required_level=0,
            primary=line.primary or None, secondary=line.secondary, primary_share=line.share, unique_equip=False,
            **extra)})
    exp = item_variants.expand(
        decls, ids_cfg={"item": {"start": 70000, "end": 79999}, "item_minted": {"start": 71000, "end": 79999}},
        live_rows=rows, columns=tuple(spell_tables.ITEM_TEMPLATE_COLUMNS),
        tables_loader=lambda: (tables, shape_catalog), lock=item_variants.item_ids.Lock(text=""),
        labels_loader=dict, cells_lock_text=item_variants.CELLS_LOCK_PATH.read_text(encoding="utf-8"),
    )
    # Only these items are declared, so errors about other source/items lock lines are not this caller's business.
    errors = [e for e in exp.errors if KEY_PREFIX in e]
    exp.errors = []
    em = item_emit.build(exp)
    return Materialized({t.row["entry"]: t.row for t in em.tiers},
                        {t.row["entry"]: {"entry": t.row["entry"], **t.tier.itemization} for t in em.tiers},
                        errors + list(em.errors), em.labels)


def run(inputs: Inputs, owned: dict[int, str] | None = None) -> tuple[Scope, list[Decision]]:
    scoped = scope(inputs.quests, inputs.addons, inputs.rows, owned_elsewhere() if owned is None else owned)
    return scoped, decide_all(scoped, inputs.rows, inputs.base_rows, inputs.spells, inputs.catalog)
