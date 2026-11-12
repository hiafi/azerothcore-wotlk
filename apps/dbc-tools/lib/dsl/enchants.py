"""
Enchants, random suffixes, gems and meta gem conditions (crafting rework C1): the four client+server DBC tables behind
"+8 Mastery" gear enchants, "of the Tiger" random suffixes, gem items and the meta gem requirement line. Declared in
`source/world/` (or anywhere a class file may declare); `generate.py` writes each table's server overlay
(`spellitemenchantment_dbc`, `itemrandomsuffix_dbc`, `gemproperties_dbc`, `spellitemenchantmentcondition_dbc`) and
merges the rows over the stock client file into patch-Z. This module declares no content: C4 (suffixes), C5 (gems) and
C6 (enchants as items) do.

    from lib.dsl.enchants import (
        enchant, stat_enchant, stat_effect, suffix, gem, enchant_condition, gems_at_least, override_enchant,
    )
    from lib.dsl.registry import ItemMod, GemColor

    crit = stat_enchant(5000, ItemMod.CRIT_RATING)                      # a suffix part: amount 0, "+$i ..."
    mastery = stat_enchant(5001, ItemMod.MASTERY_RATING)
    suffix(1000, "of the Tiger", "Tiger", (crit, 6666), (mastery, 10000))
    ruby = stat_enchant(5100, ItemMod.STRENGTH, 12, src_item=71234)    # a gem's bonus: "+12 Strength"
    gem(2000, ruby, GemColor.RED)                                       # item_template.GemProperties = 2000
    purist = enchant_condition(1000, gems_at_least(GemColor.RED, 3))   # "requires 3 red gems"
    enchant(5900, "Hard to Kill", stat_effect(ItemMod.STAMINA, 30), condition=purist)
    override_enchant(2605, ItemVisual=0)                                # a stock row: stock columns + the changes

**Ids.** A declared row's id sits in its `source/ids.yaml` block (`spellitemenchantment`, `itemrandomsuffix`,
`gemproperties`, `spellitemenchantmentcondition`); an id outside it raises, so a stock row is never replaced by
accident. `override_*()` is the opposite: it takes a STOCK id (outside the block), starts from the stock row and changes
only the named columns, like `override_skill_line()`.

**Cross references** (a suffix part's enchant, a gem's enchant, an enchant's condition) are checked after everything is
loaded (lib/enchant_tables.py): an id that is neither declared nor stock stops `generate.py`.

**What the client needs** (all four tables go out as both halves): the enchant `name` is the tooltip line (the client
fills `$i` with the computed amount, which is how a suffix part reads "+$i Haste Rating"), the suffix `name` is the
"of the Tiger" in the item's name, `GemProperties` is how the client colors a gem item and matches sockets, and the
condition is the meta gem's requirement line. A gem's enchant row needs `src_item` (the gem item entry): the server
finds a socketed gem's color through `Src_ItemID` -> item -> `GemProperties`, so a gem enchant with `src_item=0` never
counts toward a meta gem requirement.

**Amounts.** `amount` is the flat value of a stat / resistance / damage effect; 0 on a suffix part, whose value the
item's suffix factor sets (`Player::ApplyEnchantment`: `AllocationPct * suffix factor / 10000`, the branch for
`EffectPointsMin` 0). `min_level` is the SpellItemEnchantment `MinLevel`: the player level below which the enchant
does not apply (`Player::ApplyEnchantment` returns early when `requiredLevel` is above the player's level).
GemProperties itself has no level column, so a "minimum level gem" sets it on the gem's enchant.
"""

from __future__ import annotations

import math
from enum import IntEnum
from typing import NamedTuple

from .. import dbcfile, dbcfmt
from . import registry as _registry
from .constants import EnchantType, GemColor, GemCompare, ItemMod

# Every stock row of the three string tables carries this Name_Lang_Mask (enUS present).
NAME_LANG_MASK = 16712190
NAME_MAX_LENGTH = 100
MAX_ENCHANT_EFFECTS = 3  # MAX_SPELL_ITEM_ENCHANTMENT_EFFECTS
MAX_SUFFIX_PARTS = 5  # MAX_ITEM_ENCHANTMENT_EFFECTS (ItemRandomSuffix)
MAX_CONDITION_CLAUSES = 5
# A suffix part's share of the item's suffix factor, in 1/10000ths. Stock tops out at 10000 (a lone part) with 6666
# on two-part suffixes; double a full share is generous, anything past it is a typo.
MAX_ALLOCATION_PCT = 20000
# item_instance.randomPropertyId is a SMALLINT and a suffix is stored negated, so a suffix id above 32767 cannot be
# saved on an item. The ids.yaml block is well below it; this holds even if the block is ever widened.
MAX_SUFFIX_ID = 32767
INT32_MIN, INT32_MAX = -(2 ** 31), 2 ** 31 - 1

# The text the stat gets in an enchant's name when none is given. Custom stats use the names this fork gives them
# ("Cooldown Haste", "Proc Chance"); the rest are the stock enchant strings.
STAT_NAMES: dict[int, str] = {
    ItemMod.MANA: "Mana", ItemMod.HEALTH: "Health", ItemMod.AGILITY: "Agility", ItemMod.STRENGTH: "Strength",
    ItemMod.INTELLECT: "Intellect", ItemMod.SPIRIT: "Spirit", ItemMod.STAMINA: "Stamina",
    ItemMod.DEFENSE_SKILL_RATING: "Defense Rating", ItemMod.DODGE_RATING: "Dodge Rating",
    ItemMod.PARRY_RATING: "Parry Rating", ItemMod.BLOCK_RATING: "Block Rating",
    ItemMod.HIT_MELEE_RATING: "Melee Hit Rating", ItemMod.HIT_RANGED_RATING: "Ranged Hit Rating",
    ItemMod.HIT_SPELL_RATING: "Spell Hit Rating", ItemMod.CRIT_MELEE_RATING: "Melee Critical Strike Rating",
    ItemMod.CRIT_RANGED_RATING: "Ranged Critical Strike Rating",
    ItemMod.CRIT_SPELL_RATING: "Spell Critical Strike Rating",
    ItemMod.MASTERY_RATING: "Mastery Rating", ItemMod.VERSATILITY_RATING: "Versatility Rating",
    ItemMod.COOLDOWN_RATING: "Cooldown Haste Rating", ItemMod.HASTE_MELEE_RATING: "Melee Haste Rating",
    ItemMod.HASTE_RANGED_RATING: "Ranged Haste Rating", ItemMod.HASTE_SPELL_RATING: "Spell Haste Rating",
    ItemMod.HIT_RATING: "Hit Rating", ItemMod.CRIT_RATING: "Critical Strike Rating",
    ItemMod.PROC_RATING: "Proc Chance Rating", ItemMod.RESILIENCE_RATING: "Resilience Rating",
    ItemMod.HASTE_RATING: "Haste Rating", ItemMod.EXPERTISE_RATING: "Expertise Rating",
    ItemMod.ATTACK_POWER: "Attack Power", ItemMod.RANGED_ATTACK_POWER: "Ranged Attack Power",
    ItemMod.MANA_REGENERATION: "Mana per 5 sec.", ItemMod.ARMOR_PENETRATION_RATING: "Armor Penetration Rating",
    ItemMod.SPELL_POWER: "Spell Power", ItemMod.HEALTH_REGEN: "Health Regeneration",
    ItemMod.SPELL_PENETRATION: "Spell Penetration", ItemMod.BLOCK_VALUE: "Block Value",
}

# Pure gem colors a GemProperties row may carry: the hybrids are ORs, and META stands alone (stock has no other combo).
VALID_GEM_COLORS = frozenset({1, 2, 4, 6, 8, 10, 12, 14})
# Condition clause colors are slots 1..4 = the bit position + 1 of META, RED, YELLOW, BLUE (Condition->Color[i] - 1).
PURE_COLOR_SLOT = {GemColor.META: 1, GemColor.RED: 2, GemColor.YELLOW: 3, GemColor.BLUE: 4}


def _plain_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _check_name(label: str, value) -> str:
    one_line = isinstance(value, str) and "\n" not in value and "\r" not in value
    if not one_line or not value.strip() or len(value) > NAME_MAX_LENGTH:
        raise ValueError(f"{label}: must be a non-empty one-line string of at most {NAME_MAX_LENGTH} characters, "
                         f"got {value!r}")
    return value


def _check_int32(label: str, value, minimum: int = INT32_MIN) -> int:
    if not _plain_int(value) or not minimum <= value <= INT32_MAX:
        raise ValueError(f"{label}: must be an int in {minimum}..{INT32_MAX}, got {value!r}")
    return int(value)  # an IntEnum member becomes a plain int


def _id_of(label: str, ref) -> int:
    """An id given as a number or as the row a declaration returned."""
    value = ref["ID"] if isinstance(ref, dict) and "ID" in ref else ref
    if not _plain_int(value) or value <= 0:
        raise ValueError(f"{label}: {ref!r} is not a positive id or a declared row")
    return int(value)


def _check_block(caller: str, block_name: str, value) -> int:
    _registry._require_active()  # a bare import registers nothing: say so before any other complaint
    block = (_registry._active_ids_cfg or {}).get(block_name)
    if not block:
        raise ValueError(
            f"{caller}: needs source/ids.yaml's `{block_name}` block - pass ids_cfg through "
            f"registry.load_class_file(path, ids_cfg=...) (generate.py already does)"
        )
    if not _plain_int(value) or not block["start"] <= value <= block["end"]:
        raise ValueError(
            f"{caller}: id {value!r} is outside source/ids.yaml's {block_name} reserved block "
            f"({block['start']}-{block['end']}) - use override_*() to edit a stock row, or widen the block deliberately"
        )
    return int(value)


def _empty_row(table: dbcfmt.DbcTable, row_id: int) -> dict:
    row = dbcfile.empty_row(table)
    row["ID"] = row_id
    row["id"] = row_id  # bookkeeping for the registry's duplicate check, never a column
    return row


def _register(attribute: str, caller: str, row: dict) -> dict:
    active = _registry._require_active()
    declared = getattr(active, attribute)
    if any(entry["id"] == row["id"] for entry in declared):
        raise _registry.DuplicateIdError(f"{caller}: id {row['id']} is declared twice")
    declared.append(row)
    return row


# ---------------------------------------------------------------------------------------------------------------------
# SpellItemEnchantment


class EnchantEffect(NamedTuple):
    """One of an enchant's (up to three) effects: `type` is an `EnchantType`, `arg` the stat / school / spell id and
    `amount` the value (see `EnchantType`)."""

    type: int
    arg: int
    amount: int


def stat_effect(stat: int, amount: int = 0) -> EnchantEffect:
    """`+amount` of an `ItemMod` stat. `amount` 0 is a suffix part (the suffix factor sets the value)."""
    if not _plain_int(stat) or stat not in STAT_NAMES:
        raise ValueError(f"stat_effect({stat!r}): not a stat an enchant can carry (see constants.ItemMod)")
    return EnchantEffect(EnchantType.STAT, int(stat), _check_int32("stat_effect amount", amount))


def resistance_effect(school: int, amount: int) -> EnchantEffect:
    """`+amount` resistance of a spell school (0 = armor, 1 holy ... 6 arcane)."""
    if not _plain_int(school) or not 0 <= school <= 6:
        raise ValueError(f"resistance_effect({school!r}): the school must be 0 (armor) to 6 (arcane)")
    return EnchantEffect(EnchantType.RESISTANCE, int(school), _check_int32("resistance_effect amount", amount))


def spell_effect(kind: int, spell, amount: int = 0) -> EnchantEffect:
    """A spell effect: `EnchantType.EQUIP_SPELL` (cast on equip), `COMBAT_SPELL` (proc; `amount` the proc chance) or
    `USE_SPELL`. `spell` is a spell id or a declared `Spell`."""
    if kind not in (EnchantType.EQUIP_SPELL, EnchantType.COMBAT_SPELL, EnchantType.USE_SPELL):
        raise ValueError(f"spell_effect({kind!r}): must be EnchantType.EQUIP_SPELL, COMBAT_SPELL or USE_SPELL")
    spell_id = getattr(spell, "id", spell)
    if not _plain_int(spell_id) or spell_id <= 0:
        raise ValueError(f"spell_effect: {spell!r} is not a spell id or a declared spell")
    return EnchantEffect(int(kind), int(spell_id), _check_int32("spell_effect amount", amount))


def socket_effect() -> EnchantEffect:
    """A prismatic socket (`ITEM_ENCHANTMENT_TYPE_PRISMATIC_SOCKET`): the belt buckle's enchant."""
    return EnchantEffect(EnchantType.PRISMATIC_SOCKET, 0, 1)


def _build_enchant_row(caller: str, enchant_id: int, name: str, effects, *, charges, flags, item_visual, src_item,
                       condition, required_skill, required_skill_rank, min_level) -> dict:
    _check_name(f"{caller}: name", name)
    if not effects or len(effects) > MAX_ENCHANT_EFFECTS:
        raise ValueError(f"{caller}: needs 1 to {MAX_ENCHANT_EFFECTS} effects, got {len(effects)}")
    row = _empty_row(dbcfmt.SPELLITEMENCHANTMENT, enchant_id)
    for index, effect in enumerate(effects, start=1):
        if not isinstance(effect, EnchantEffect):
            raise ValueError(f"{caller}: effect {index} must come from stat_effect() / resistance_effect() / "
                             f"spell_effect() / socket_effect(), got {effect!r}")
        row[f"Effect_{index}"] = int(effect.type)
        row[f"EffectArg_{index}"] = int(effect.arg)
        row[f"EffectPointsMin_{index}"] = row[f"EffectPointsMax_{index}"] = int(effect.amount)
    row["Name_Lang_enUS"] = name
    row["Name_Lang_Mask"] = NAME_LANG_MASK
    row["Charges"] = _check_int32(f"{caller}: charges", charges, 0)
    row["Flags"] = _check_int32(f"{caller}: flags", flags, 0)
    row["ItemVisual"] = _check_int32(f"{caller}: item_visual", item_visual)
    row["Src_ItemID"] = _check_int32(f"{caller}: src_item", src_item, 0)
    row["Condition_Id"] = _id_of(f"{caller}: condition", condition) if condition else 0
    row["RequiredSkillID"] = _check_int32(f"{caller}: required_skill", required_skill, 0)
    row["RequiredSkillRank"] = _check_int32(f"{caller}: required_skill_rank", required_skill_rank, 0)
    row["MinLevel"] = _check_int32(f"{caller}: min_level", min_level, 0)
    return row


def enchant(
    enchant_id: int, name: str, *effects: EnchantEffect, charges: int = 0, flags: int = 0, item_visual: int = 0,
    src_item: int = 0, condition=0, required_skill: int = 0, required_skill_rank: int = 0, min_level: int = 0,
) -> dict:
    """Declares a `SpellItemEnchantment` row: `name` (the tooltip line, `$i` = the computed amount) and one to three
    effects (`stat_effect()`, `resistance_effect()`, `spell_effect()`, `socket_effect()`). `src_item`: the gem item
    entry, for a gem's enchant. `condition`: a `SpellItemEnchantmentCondition` id (or the row `enchant_condition()`
    returned), the meta gem requirement. `flags` is the stock `Flags` column (1 = can be soulbound ...), `item_visual`
    the weapon glow (a `SpellItemEnchantment` visual id). Returns the row, so a suffix or gem can take it as an id."""
    caller = f"enchant({enchant_id!r})"
    enchant_id = _check_block(caller, "spellitemenchantment", enchant_id)
    row = _build_enchant_row(
        caller, enchant_id, name, effects, charges=charges, flags=flags, item_visual=item_visual, src_item=src_item,
        condition=condition, required_skill=required_skill, required_skill_rank=required_skill_rank,
        min_level=min_level,
    )
    return _register("spell_item_enchantments", caller, row)


def stat_enchant(enchant_id: int, stat: int, amount: int = 0, *, name: str | None = None, **kwargs) -> dict:
    """`enchant()` for a single stat: `stat_enchant(5001, ItemMod.MASTERY_RATING, 12)` is "+12 Mastery Rating". With
    `amount` 0 it is a suffix part ("+$i Mastery Rating"). `name` overrides the generated text; the other keywords
    are `enchant()`'s."""
    effect = stat_effect(stat, amount)
    if name is None:
        stat_name = STAT_NAMES[effect.arg]
        name = f"+{effect.amount} {stat_name}" if effect.amount > 0 else \
            (f"+$i {stat_name}" if effect.amount == 0 else f"{effect.amount} {stat_name}")
    return enchant(enchant_id, name, effect, **kwargs)


# ---------------------------------------------------------------------------------------------------------------------
# ItemRandomSuffix


def suffix(suffix_id: int, name: str, internal_name: str, *parts) -> dict:
    """Declares an `ItemRandomSuffix` row: `name` is what the item reads ("of the Tiger"), `internal_name` the client's
    internal label ("Tiger"), and `parts` one to five `(enchant, allocation_pct)` pairs: `enchant` an id or the row an
    `enchant()` returned, `allocation_pct` its share of the item's suffix factor in 1/10000ths (stock: 10000 for a lone
    part, 6666 on two-part suffixes). A part's enchant should have amount 0 (`stat_enchant(id, stat)`).

    The id must also fit a signed 16-bit negative (`item_instance.randomPropertyId` is a smallint holding `-suffix id`),
    which source/ids.yaml's block (1000-1999) does. Items roll a suffix through `item_template.RandomSuffix` and an
    `item_enchantment_template` pool."""
    caller = f"suffix({suffix_id!r})"
    suffix_id = _check_block(caller, "itemrandomsuffix", suffix_id)
    if suffix_id > MAX_SUFFIX_ID:
        raise ValueError(f"{caller}: a suffix id above {MAX_SUFFIX_ID} does not fit item_instance.randomPropertyId "
                         f"(a smallint holding -id)")
    _check_name(f"{caller}: name", name)
    _check_name(f"{caller}: internal_name", internal_name)
    if not parts or len(parts) > MAX_SUFFIX_PARTS:
        raise ValueError(f"{caller}: needs 1 to {MAX_SUFFIX_PARTS} (enchant, allocation_pct) parts, got {len(parts)}")
    row = _empty_row(dbcfmt.ITEMRANDOMSUFFIX, suffix_id)
    row["Name_Lang_enUS"] = name
    row["Name_Lang_Mask"] = NAME_LANG_MASK
    row["InternalName"] = internal_name
    seen = set()
    for index, part in enumerate(parts, start=1):
        if not isinstance(part, (tuple, list)) or len(part) != 2:
            raise ValueError(f"{caller}: part {index} must be an (enchant, allocation_pct) pair, got {part!r}")
        enchant_ref, pct = part
        enchant_id = _id_of(f"{caller}: part {index}", enchant_ref)
        if enchant_id in seen:
            raise ValueError(f"{caller}: enchant {enchant_id} is listed twice")
        seen.add(enchant_id)
        if not _plain_int(pct) or not 1 <= pct <= MAX_ALLOCATION_PCT:
            raise ValueError(f"{caller}: part {index} allocation_pct must be an int in 1..{MAX_ALLOCATION_PCT} "
                             f"(10000 = the whole suffix factor), got {pct!r}")
        row[f"Enchantment_{index}"] = enchant_id
        row[f"AllocationPct_{index}"] = int(pct)
    return _register("item_random_suffixes", caller, row)


def suffix_pool(entry: int, *suffixes) -> list[dict]:
    """Declares a random suffix pool (crafting rework C4): one `item_enchantment_template` row per suffix, `entry` the
    pool id an item names in `item_template.RandomSuffix`, every suffix at an equal chance. `suffixes` are suffix ids
    or the rows `suffix()` returned (declared or stock). The chances are rounded UP to four decimals so they sum to at
    least 100: `GetItemEnchantMod` (ItemEnchantmentMgr.cpp) walks the running total against a 0-100 roll, and a sum
    short of 100 sends the top of the roll to its slower fallback. `entry` sits in source/ids.yaml's
    `item_enchantment_pool` block, clear of the stock pools (61-8675), which share this table with RandomProperty.
    Returns the rows."""
    caller = f"suffix_pool({entry!r})"
    entry = _check_block(caller, "item_enchantment_pool", entry)
    if not suffixes:
        raise ValueError(f"{caller}: needs at least one suffix")
    ids = [_id_of(f"{caller}: suffix {index}", ref) for index, ref in enumerate(suffixes, start=1)]
    if len(set(ids)) != len(ids):
        raise ValueError(f"{caller}: a suffix is listed twice")
    for suffix_id in ids:
        if suffix_id > MAX_SUFFIX_ID:
            raise ValueError(f"{caller}: suffix {suffix_id} is above {MAX_SUFFIX_ID} (item_instance.randomPropertyId)")
    chance = math.ceil(100.0 / len(ids) * 10000) / 10000
    return [
        _register("item_enchantment_pools", caller,
                  {"id": f"{entry}:{suffix_id}", "entry": entry, "ench": suffix_id, "chance": chance})
        for suffix_id in ids
    ]


# ---------------------------------------------------------------------------------------------------------------------
# GemProperties


def gem(gem_id: int, enchant, color: int, *, max_count_inv: int = 0, max_count_item: int = 0) -> dict:
    """Declares a `GemProperties` row: the gem item's `item_template.GemProperties` points here, `enchant` is the
    `SpellItemEnchantment` it applies (an id or the row `enchant()` returned; give that enchant `src_item=<gem item>`)
    and `color` the `GemColor` (a hybrid is the OR of its colors; META stands alone). `max_count_inv` /
    `max_count_item` are the unique-gem limits (0 = none)."""
    caller = f"gem({gem_id!r})"
    gem_id = _check_block(caller, "gemproperties", gem_id)
    if not _plain_int(color) or color not in VALID_GEM_COLORS:
        raise ValueError(f"{caller}: color {color!r} must be a GemColor (1 meta, 2 red, 4 yellow, 8 blue or an OR of "
                         f"the three pure colors)")
    row = _empty_row(dbcfmt.GEMPROPERTIES, gem_id)
    row["Enchant_Id"] = _id_of(f"{caller}: enchant", enchant)
    row["Maxcount_Inv"] = _check_int32(f"{caller}: max_count_inv", max_count_inv, 0)
    row["Maxcount_Item"] = _check_int32(f"{caller}: max_count_item", max_count_item, 0)
    row["Type"] = int(color)
    return _register("gem_properties", caller, row)


# ---------------------------------------------------------------------------------------------------------------------
# SpellItemEnchantmentCondition


class GemClause(NamedTuple):
    """One requirement clause: the count of `color_slot` gems compared with a fixed count or another color's count."""

    color_slot: int
    comparator: int
    rhs_color_slot: int  # 0: compare with `rhs_value`
    rhs_value: int


def _clause(caller: str, comparator: int, color, rhs) -> GemClause:
    if color not in PURE_COLOR_SLOT:
        raise ValueError(f"{caller}: the color must be one of GemColor.META / RED / YELLOW / BLUE, got {color!r}")
    if isinstance(rhs, GemColor):
        if rhs not in PURE_COLOR_SLOT:
            raise ValueError(f"{caller}: compare with a pure color (META / RED / YELLOW / BLUE), got {rhs!r}")
        return GemClause(PURE_COLOR_SLOT[color], int(comparator), PURE_COLOR_SLOT[rhs], 0)
    if not _plain_int(rhs) or not 0 <= rhs <= 255:
        raise ValueError(f"{caller}: compare with a count (0-255) or a pure GemColor, got {rhs!r}")
    return GemClause(PURE_COLOR_SLOT[color], int(comparator), 0, int(rhs))


def gems_at_least(color, count_or_color) -> GemClause:
    """"At least N `color` gems" (Operator 5), or at least as many as another color's count."""
    return _clause("gems_at_least", GemCompare.AT_LEAST, color, count_or_color)


def gems_more_than(color, count_or_color) -> GemClause:
    """"More than N `color` gems" (Operator 3)."""
    return _clause("gems_more_than", GemCompare.MORE_THAN, color, count_or_color)


def gems_fewer_than(color, count_or_color) -> GemClause:
    """"Fewer than N `color` gems" (Operator 2)."""
    return _clause("gems_fewer_than", GemCompare.LESS_THAN, color, count_or_color)


def enchant_condition(condition_id: int, *clauses: GemClause) -> dict:
    """Declares a `SpellItemEnchantmentCondition` row: the meta gem requirement, one to five clauses that must all hold
    (`Player::EnchantmentFitsRequirements` ANDs them). The server counts the four colors META, RED, YELLOW and BLUE
    over the equipped items' sockets, counting a hybrid once for each color bit; anything richer (six colors, "per
    gem" scaling) is a script. Pass the id, or this row, as `enchant(..., condition=)`."""
    caller = f"enchant_condition({condition_id!r})"
    condition_id = _check_block(caller, "spellitemenchantmentcondition", condition_id)
    if not clauses or len(clauses) > MAX_CONDITION_CLAUSES:
        raise ValueError(f"{caller}: needs 1 to {MAX_CONDITION_CLAUSES} clauses, got {len(clauses)}")
    row = _empty_row(dbcfmt.SPELLITEMENCHANTMENTCONDITION, condition_id)
    for index, clause in enumerate(clauses, start=1):
        if not isinstance(clause, GemClause):
            raise ValueError(f"{caller}: clause {index} must come from gems_at_least() / gems_more_than() / "
                             f"gems_fewer_than(), got {clause!r}")
        row[f"Lt_OperandType_{index}"] = clause.color_slot
        row[f"Operator_{index}"] = clause.comparator
        row[f"Rt_OperandType_{index}"] = clause.rhs_color_slot
        row[f"Rt_Operand_{index}"] = clause.rhs_value
        # The stock rows chain every clause but the last with Logic 1 (the client reads it; the server ANDs).
        row[f"Logic_{index}"] = 1 if index < len(clauses) else 0
    return _register("enchant_conditions", caller, row)


# ---------------------------------------------------------------------------------------------------------------------
# Stock row overrides


def _column_range(table: dbcfmt.DbcTable, column: str) -> tuple[int, int]:
    """The values `column` can hold in the SQL overlay (and the client file): a byte column ('b' / 'X') 0..255, a
    `signed` column int32, a locale mask uint32 (`int unsigned`), every other column int32's non-negative half (the
    SQL columns are signed `int`)."""
    fmt = table.fmt[table.columns.index(column)]
    if fmt in ("b", "X"):
        return 0, 255
    if column in table.signed:
        return INT32_MIN, INT32_MAX
    if column.endswith("_Lang_Mask"):
        return 0, 2 ** 32 - 1
    return 0, INT32_MAX


def _override_stock_row(
    helper: str, row_id: int, changed: dict, *, live_key: str, table: dbcfmt.DbcTable, attribute: str,
) -> dict:
    """The shared body of the four `override_*()` helpers: the stock row with `changed` columns applied."""
    caller = f"{helper}({row_id!r})"
    stock_rows = _registry._require_live(live_key, helper)
    if not stock_rows:
        raise _registry.MissingStockFileError(
            f"{caller}: the stock {table.name} index is empty - var/extractors/dbc/{table.dbc_filename} is missing "
            f"on this checkout. Copy it from the worldserver's DBC directory "
            f"(ac-worldserver:/azerothcore/env/dist/data/dbc/{table.dbc_filename}) into var/extractors/dbc/."
        )
    stock = stock_rows.get(row_id)
    if stock is None:
        raise ValueError(
            f"{caller}: no stock {table.name} row for id {row_id!r} ({len(stock_rows)} stock rows are loaded, so "
            f"this isn't a missing-extraction problem) - a new row is declared with its own helper, from the "
            f"reserved block"
        )
    row = dict(stock)
    unknown = [key for key in changed if key not in row]
    if unknown:
        raise KeyError(f"{caller}: no such column(s): {', '.join(sorted(unknown))} - see "
                       f"lib.dbcfmt.{table.name.upper()}.columns")
    for key, value in changed.items():
        if key == "ID":
            raise ValueError(f"{caller}: the ID column is the key and cannot be changed")
        if isinstance(value, IntEnum):
            value = int(value)  # a plain int in the row
        if isinstance(stock[key], str) != isinstance(value, str) or (
            not isinstance(value, str) and not _plain_int(value)
        ):
            raise ValueError(f"{caller}: {key} must be {'a str' if isinstance(stock[key], str) else 'an int'}, "
                             f"got {value!r}")
        if not isinstance(value, str):
            low, high = _column_range(table, key)
            if not low <= value <= high:
                raise ValueError(f"{caller}: {key} must be in {low}..{high} (the SQL column's range), got {value!r}")
        row[key] = value
    row["id"] = row_id
    return _register(attribute, caller, row)


def stock_enchant_rows() -> dict[int, dict]:
    """The stock `SpellItemEnchantment` rows by id (read-only copies), for a source file that selects stock rows by
    their content, as the crafting rework C6 Hit / Expertise / Defense remap does."""
    stock_rows = _registry._require_live("spellitemenchantment_rows", "stock_enchant_rows")
    if not stock_rows:
        raise _registry.MissingStockFileError(
            "stock_enchant_rows(): the stock SpellItemEnchantment index is empty - var/extractors/dbc/"
            "SpellItemEnchantment.dbc is missing on this checkout. Copy it from the worldserver's DBC directory "
            "(ac-worldserver:/azerothcore/env/dist/data/dbc/SpellItemEnchantment.dbc) into var/extractors/dbc/."
        )
    return {row_id: dict(row) for row_id, row in stock_rows.items()}


def override_enchant(enchant_id: int, **changed_columns) -> dict:
    """A full-row override of the stock `SpellItemEnchantment` row `enchant_id`: every column starts at the stock
    value and `changed_columns` (SQL column names, `lib.dbcfmt.SPELLITEMENCHANTMENT.columns`) overwrites just the
    named ones, so dropping a keyword restores the stock value and dropping the call prunes the overlay row. This is
    how a stock gem / enchant that carries Hit, Expertise or Defense is remapped (crafting rework C6)."""
    return _override_stock_row(
        "override_enchant", enchant_id, changed_columns, live_key="spellitemenchantment_rows",
        table=dbcfmt.SPELLITEMENCHANTMENT, attribute="spell_item_enchantments",
    )


def override_suffix(suffix_id: int, **changed_columns) -> dict:
    """`override_enchant()` for a stock `ItemRandomSuffix` row (`lib.dbcfmt.ITEMRANDOMSUFFIX.columns`)."""
    return _override_stock_row(
        "override_suffix", suffix_id, changed_columns, live_key="itemrandomsuffix_rows",
        table=dbcfmt.ITEMRANDOMSUFFIX, attribute="item_random_suffixes",
    )


def override_gem(gem_id: int, **changed_columns) -> dict:
    """`override_enchant()` for a stock `GemProperties` row (`lib.dbcfmt.GEMPROPERTIES.columns`)."""
    return _override_stock_row(
        "override_gem", gem_id, changed_columns, live_key="gemproperties_rows",
        table=dbcfmt.GEMPROPERTIES, attribute="gem_properties",
    )


def override_enchant_condition(condition_id: int, **changed_columns) -> dict:
    """`override_enchant()` for a stock `SpellItemEnchantmentCondition` row
    (`lib.dbcfmt.SPELLITEMENCHANTMENTCONDITION.columns`)."""
    return _override_stock_row(
        "override_enchant_condition", condition_id, changed_columns,
        live_key="spellitemenchantmentcondition_rows", table=dbcfmt.SPELLITEMENCHANTMENTCONDITION,
        attribute="enchant_conditions",
    )
