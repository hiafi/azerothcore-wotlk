"""
The generate.py side of lib/dsl/enchants.py (crafting rework C1): the client rows of the four enchant / suffix / gem /
condition tables and the checks that need a whole-run view.

`client_rows(table, dsl_rows)` is the patch-Z half: the declared rows as DBC rows keyed by ID, merged over the stock
file by generate.py exactly like SkillLine (the server half is the SPELL_TABLES entry).

`check()` is what only a whole-run view can see. None of these is a load error anywhere (the server skips the part, the
client shows a blank line, a meta gem never counts), so each would ship silently:

- a dangling reference: a suffix part or a gem naming an enchant, or an enchant naming a condition, that nothing
  declares and the stock files do not have;
- a gem whose enchant has `Src_ItemID` 0 (the server finds a socketed gem's color through that item, so the gem would
  never count toward a meta gem requirement), or whose `Src_ItemID` item does not point back at the gem
  (`item_template.GemProperties` != the gem row);
- a suffix part whose enchant carries a flat amount (the core then ignores `AllocationPct` and applies the amount) or an
  effect the suffix factor cannot scale;
- an `item_enchantment_template` row of a SUFFIX pool (an entry some item names in `RandomSuffix`) whose `ench` is not
  an ItemRandomSuffix id: the core's load check samples one random pick of a pool only.

A missing stock file never stops a run that declares nothing of that table: the check that needed it is skipped with one
WARNING naming the file and the `docker cp` command. When something declared (or a reference) needs the file, it is an
ERROR naming the file, not a complaint about the declaration.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from . import dbcfmt
from .dsl.constants import EnchantType

# (table, Registry list) of the four declared tables.
TABLES = (
    (dbcfmt.SPELLITEMENCHANTMENT, "spell_item_enchantments"),
    (dbcfmt.ITEMRANDOMSUFFIX, "item_random_suffixes"),
    (dbcfmt.GEMPROPERTIES, "gem_properties"),
    (dbcfmt.SPELLITEMENCHANTMENTCONDITION, "enchant_conditions"),
)
MAX_SUFFIX_ID = 32767  # item_instance.randomPropertyId is a smallint holding the negated suffix id
# The effect types the core scales by the suffix factor when the enchant's amount is 0 (PlayerStorage.cpp
# ApplyEnchantment): stat and resistance by AllocationPct * factor / 10000, an equip spell's basepoints via the item.
SUFFIX_SCALED = (EnchantType.STAT, EnchantType.RESISTANCE, EnchantType.EQUIP_SPELL)
SUFFIX_FLAT_AMOUNT = (EnchantType.STAT, EnchantType.RESISTANCE)


def copy_command(table: dbcfmt.DbcTable) -> str:
    return (f"docker cp ac-worldserver:/azerothcore/env/dist/data/dbc/{table.dbc_filename} "
            f"var/extractors/dbc/")


class MissingStockFile(Exception):
    """The stock client DBC of `table` is not extracted on this checkout."""

    def __init__(self, table: dbcfmt.DbcTable):
        super().__init__(table.dbc_filename)
        self.table = table


def stock_loader(base_dir: Path | None = None) -> Callable[[dbcfmt.DbcTable], dict[int, dict]]:
    """`table -> {id: stock row}`, raising `MissingStockFile` when the extracted file is absent (state.load_stock_rows
    alone returns {} then, which reads as "no stock row has any id")."""
    from . import state  # noqa: PLC0415

    def load(table: dbcfmt.DbcTable) -> dict[int, dict]:
        directory = Path(base_dir) if base_dir is not None else state.BASE_DBC_DIR
        if not (directory / table.dbc_filename).is_file():
            raise MissingStockFile(table)
        return state.load_stock_rows(table)

    return load


def client_rows(table: dbcfmt.DbcTable, dsl_rows: list[dict]) -> dict[int, dict]:
    """Declared rows as `table`'s DBC rows keyed by ID (no bookkeeping key such as `id` leaks into the client row)."""
    return {int(r["ID"]): {c: r[c] for c in table.columns} for r in dsl_rows}


def declared_any(dsl_classes: dict[str, list[dict]]) -> bool:
    return any(dsl_classes.get(key) for _table, key in TABLES)


def item_columns(live_rows: dict, emission=None, item_templates=()) -> dict[int, tuple[int, int]]:
    """`{item entry: (RandomSuffix, GemProperties)}` as the run will leave `item_template`: the live rows, then the
    declared items (`emission.template_rows` full rows, `emission.template_edits` and the `item_template()` rows
    touching only their `_update_columns`)."""
    out: dict[int, tuple[int, int]] = {}
    for entry, row in live_rows.items():
        suffix, gem = int(row.get("RandomSuffix") or 0), int(row.get("GemProperties") or 0)
        if suffix or gem:
            out[int(entry)] = (suffix, gem)

    def apply(row: dict, columns) -> None:
        entry = int(row["entry"])
        suffix, gem = out.get(entry, (0, 0))
        if "RandomSuffix" in columns and "RandomSuffix" in row:
            suffix = int(row["RandomSuffix"] or 0)
        if "GemProperties" in columns and "GemProperties" in row:
            gem = int(row["GemProperties"] or 0)
        if suffix or gem or entry in out:
            out[entry] = (suffix, gem)

    if emission is not None:
        for row in emission.template_rows:
            apply(row, ("RandomSuffix", "GemProperties"))
        for row in emission.template_edits:
            apply(row, row.get("_update_columns", ()))
    for row in item_templates:
        if "entry" in row:
            apply(row, row.get("_update_columns", ()))
    return out


def check(
    dsl_classes: dict[str, list[dict]], *, pool_rows: list[dict], items: dict[int, tuple[int, int]],
    load_stock: Callable[[dbcfmt.DbcTable], dict[int, dict]],
) -> tuple[list[str], list[str]]:
    """`(errors, warnings)` of the whole-run checks (module docstring). `pool_rows`: `item_enchantment_template` rows
    (`entry`, `ench`). `items`: `item_columns()`. `load_stock(table)`: `stock_loader()`, which raises
    `MissingStockFile`."""
    enchants = {int(r["ID"]): r for r in dsl_classes.get("spell_item_enchantments", [])}
    suffixes = {int(r["ID"]): r for r in dsl_classes.get("item_random_suffixes", [])}
    gems = dsl_classes.get("gem_properties", [])
    conditions = {int(r["ID"]) for r in dsl_classes.get("enchant_conditions", [])}
    errors: list[str] = []
    warnings: list[str] = []
    stock_cache: dict[str, dict[int, dict] | None] = {}

    def stock(table: dbcfmt.DbcTable, why: str) -> dict[int, dict] | None:
        """The stock rows, or None after one ERROR naming the missing file (the first reason that needed it)."""
        if table.name not in stock_cache:
            try:
                stock_cache[table.name] = load_stock(table)
            except MissingStockFile:
                stock_cache[table.name] = None
                errors.append(f"{table.dbc_filename} is missing from var/extractors/dbc/ ({why}); run: "
                              f"{copy_command(table)}")
        return stock_cache[table.name]

    def enchant_row(enchant_id: int, why: str) -> tuple[dict | None, bool]:
        """`(row or None, stock file was missing)`."""
        if enchant_id in enchants:
            return enchants[enchant_id], False
        rows = stock(dbcfmt.SPELLITEMENCHANTMENT, why)
        return (None, True) if rows is None else (rows.get(enchant_id), False)

    for row in suffixes.values():
        for index in range(1, 6):
            enchant_id = int(row[f"Enchantment_{index}"])
            if not enchant_id:
                continue
            found, missing = enchant_row(enchant_id, f"suffix {row['ID']} names enchant {enchant_id}")
            if missing:
                continue
            if found is None:
                errors.append(
                    f"suffix {row['ID']} ({row['Name_Lang_enUS']!r}): part {index} names enchant {enchant_id}, "
                    f"which is neither declared (enchant() / stat_enchant()) nor in the stock SpellItemEnchantment.dbc"
                )
                continue
            for slot in range(1, 4):
                effect, amount = int(found[f"Effect_{slot}"]), int(found[f"EffectPointsMin_{slot}"])
                if not effect:
                    continue
                if effect not in SUFFIX_SCALED:
                    errors.append(
                        f"suffix {row['ID']} ({row['Name_Lang_enUS']!r}): part {index} enchant {enchant_id} has an "
                        f"effect of type {effect} that the suffix factor cannot scale (only stat, resistance and equip "
                        f"spell effects are)"
                    )
                elif effect in SUFFIX_FLAT_AMOUNT and amount != 0:
                    errors.append(
                        f"suffix {row['ID']} ({row['Name_Lang_enUS']!r}): part {index} enchant {enchant_id} carries a "
                        f"flat amount {amount} in effect {slot}; the core then ignores AllocationPct and applies the "
                        f"flat amount (declare the part with amount 0)"
                    )
    for row in gems:
        gem_id, enchant_id = int(row["ID"]), int(row["Enchant_Id"])
        found, missing = enchant_row(enchant_id, f"gem {gem_id} names enchant {enchant_id}")
        if missing:
            continue
        if found is None:
            errors.append(f"gem {gem_id}: names enchant {enchant_id}, which is neither declared nor in the stock "
                          f"SpellItemEnchantment.dbc")
            continue
        src_item = int(found["Src_ItemID"])
        if not src_item:
            errors.append(
                f"gem {gem_id}: enchant {enchant_id} has Src_ItemID 0; the server finds a socketed gem's color through "
                f"that item, so this gem would never count toward a meta gem requirement (give the enchant "
                f"src_item=<the gem item entry>)"
            )
        elif src_item in items and items[src_item][1] != gem_id:
            errors.append(
                f"gem {gem_id}: enchant {enchant_id} has Src_ItemID {src_item}, but item {src_item} has GemProperties "
                f"{items[src_item][1]}, not {gem_id}"
            )
    for row in enchants.values():
        condition_id = int(row["Condition_Id"])
        if condition_id and condition_id not in conditions:
            rows = stock(dbcfmt.SPELLITEMENCHANTMENTCONDITION, f"enchant {row['ID']} names condition {condition_id}")
            if rows is not None and condition_id not in rows:
                errors.append(
                    f"enchant {row['ID']} ({row['Name_Lang_enUS']!r}): names condition {condition_id}, which is "
                    f"neither declared (enchant_condition()) nor in the stock SpellItemEnchantmentCondition.dbc"
                )
    errors.extend(_pool_check(pool_rows, items, suffixes, load_stock, warnings, errors))
    return errors, warnings


def _pool_check(pool_rows, items, suffixes, load_stock, warnings, errors) -> list[str]:
    """The suffix pool half of `check()`: skipped with one WARNING when the ItemRandomSuffix stock file is missing and
    no suffix is declared (the check could only guess), an ERROR naming the file when a suffix is declared."""
    table = dbcfmt.ITEMRANDOMSUFFIX
    try:
        stock_ids = set(load_stock(table))
    except MissingStockFile:
        if suffixes:
            errors.append(f"{table.dbc_filename} is missing from var/extractors/dbc/ (the suffix pool check needs the "
                          f"stock suffix ids next to the {len(suffixes)} declared suffix(es)); run: "
                          f"{copy_command(table)}")
        else:
            warnings.append(f"{table.dbc_filename} is missing from var/extractors/dbc/: the item_enchantment_template "
                            f"suffix pool check was skipped; run: {copy_command(table)}")
        return []
    entries = {suffix for suffix, _gem in items.values() if suffix}
    return suffix_pool_problems(pool_rows, entries, stock_ids | set(suffixes))


def merged_pool_rows(live_rows: list[dict], declared_rows: list[dict]) -> list[dict]:
    """The `item_enchantment_template` rows the server will hold after this run: a pool declared with `suffix_pool()`
    is exactly its declared rows (the prune pass removes a dropped one), every other pool its live rows."""
    declared_entries = {int(row["entry"]) for row in declared_rows}
    return [row for row in live_rows if int(row["entry"]) not in declared_entries] + list(declared_rows)


def suffix_pool_problems(
    pool_rows: list[dict], suffix_entries: set[int], suffix_ids: set[int], limit: int = MAX_SUFFIX_ID,
) -> list[str]:
    """One message per `item_enchantment_template` row of a suffix pool whose `ench` is not an ItemRandomSuffix id.

    `suffix_entries`: the pool entries items roll suffixes from (`item_template.RandomSuffix` values). `suffix_ids`:
    every ItemRandomSuffix id that exists (stock plus declared). The core's load check only samples one random pick of
    a pool (ObjectMgr), so a dangling row would hand some crafted items a suffix the client cannot name and the server
    cannot apply. An id above `limit` cannot be saved either (`item_instance.randomPropertyId` is a smallint holding
    the negated id)."""
    problems = []
    pooled = {int(row["entry"]) for row in pool_rows}
    for entry in sorted(suffix_entries - pooled):
        problems.append(f"item_template.RandomSuffix {entry}: no item_enchantment_template row has that entry, so the "
                        f"item rolls no suffix (GetItemEnchantMod logs an error at every roll)")
    for row in pool_rows:
        entry, ench = int(row["entry"]), int(row["ench"])
        if entry not in suffix_entries:
            continue
        if ench not in suffix_ids:
            problems.append(f"item_enchantment_template pool {entry}: ench {ench} is not an ItemRandomSuffix id "
                            f"(neither stock nor declared with suffix())")
        elif ench > limit:
            problems.append(f"item_enchantment_template pool {entry}: ench {ench} exceeds {limit}, the largest suffix "
                            f"id item_instance.randomPropertyId (smallint) can hold")
    return problems
