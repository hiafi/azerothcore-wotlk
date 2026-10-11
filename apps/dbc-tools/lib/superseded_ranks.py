"""
SkillLineAbility and CreatureSpellData overrides that stop pets learning superseded ranks of
collapsed chains (`.agents/plans/pet-stale-ranks/pet-stale-ranks.PLAN.md` Part A, plus the review's
B1 fix for default spells).

The single-rank class conversion collapsed every rank chain into one survivor, the DSL spell whose
`notes` carry `SURVIVOR_TAG` (e.g. Firebolt 3110), and deleted the chain's `spell_ranks` rows. Pets
don't learn from trainers: `SpellMgr::LoadPetLevelupSpellMap` builds each creature family's level-up
list from the `SkillLineAbility` rows on the family's skill lines whose `AcquireMethod` is
`SKILL_LINE_ABILITY_LEARNED_ON_SKILL_LEARN` (2, `DBCEnums.h`). Stock SkillLineAbility still lists
every superseded rank there, and with no rank chain left `Pet::learnSpell` can't see that 7799
replaces 3110, so a pet learns each superseded rank as a separate, unscaled spell.

The fix is data. For every stock SkillLineAbility row whose `Spell` is a superseded rank and whose
`AcquireMethod` is LEARNED_ON_SKILL_LEARN, emit an override: the stock row with `AcquireMethod = 0`.
`DBCDatabaseLoader` replaces a DBC record by ID with a `skilllineability_dbc` row, so the record
drops out of the pet level-up map and nothing in core changes.

The overrides are source-shaped `skill_line_ability` entries, so they go through the same
resolve/build/emit path as declared ones (server SQL and client patch). A declared row with the
same ID wins; the collision is reported.

Stock rows have `AcquireMethod` 0 (no auto-learn) or 2. When this was written every superseded rank
at 2 sat on a pet family's skill line (`CreatureFamily.dbc` skillLine[0/1]): warlock demons and
hunter pet families, none on a player skill line.

Pets have a second, rank-blind source: default spells. `SpellMgr::LoadPetDefaultSpells` takes the
`CreatureSpellData` record a creature's `PetSpellDataId` names (a tamed beast keeps its entry, so
this is the beast's record) and `LoadPetDefaultSpells_helper` drops only the spells that are in the
family's level-up set. Stock records name ranked family spells (Ghost Saber: Claw 16829), and once
the SkillLineAbility overrides take those ranks out of the level-up set they survive as defaults, so
`Pet::InitLevelupSpellsForLevel` teaches them again. `creaturespelldata_overrides` rewrites each
such record with every superseded rank replaced by its survivor. The survivor is in the family's
level-up set, so the helper drops it again: the default list ends up exactly as stock left it, and
a record whose rank was never in that family's set (an off-family default) gets the survivor
instead of the stale rank. These rows are server-only (`creaturespelldata_dbc`).

Both rules read `existing_rows` (stock plus promoted migrations) to report a conflict: a row a
migration changed to something that is neither stock nor this override. The CreatureSpellData rule
also uses it to skip records already live; the SkillLineAbility entries get that from
`resolve.resolve_rows`, since they must still reach the client patch.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from lib import build, dbcfmt

SURVIVOR_TAG = "single-rank bootstrap"
SKILL_LINE_ABILITY_LEARNED_ON_SKILL_LEARN = 2

# build.build_skilllineability_row sets these from typed entry fields; every other column of the
# override goes through raw_overrides so the built row is the full stock row.
_TYPED_COLUMNS = {
    "ID": "id",
    "SkillLine": "skill_line",
    "Spell": "spell_id",
    "ClassMask": "class_mask",
    "RaceMask": "race_mask",
    "MinSkillLineRank": "min_skill_line_rank",
}


@dataclass
class Overrides:
    entries: list[dict] = field(default_factory=list)  # skill_line_ability entries to emit
    superseded: dict[int, int] = field(default_factory=dict)  # superseded rank -> survivor
    collisions: list[str] = field(default_factory=list)  # IDs a declared row already owns
    warnings: list[str] = field(default_factory=list)


@dataclass
class SpellDataOverrides:
    rows: list[dict] = field(default_factory=list)  # every rewritten CreatureSpellData record
    to_emit: list[dict] = field(default_factory=list)  # the subset not already live
    warnings: list[str] = field(default_factory=list)


def survivor_ids(spell_entries: list[dict]) -> set[int]:
    """IDs of spells whose notes mark them as a collapsed chain's single-rank survivor."""
    return {e["id"] for e in spell_entries if SURVIVOR_TAG in (e.get("notes") or "")}


def superseded_ranks(chains: dict[int, list[tuple[int, int]]], survivors: set[int]) -> dict[int, int]:
    """Every rank of a chain that holds a survivor, minus the survivor itself, mapped to the
    survivor. `chains` is `bootstrap.load_spell_ranks_chains()`: first_spell_id -> [(spell_id,
    rank)], from the base `spell_ranks` dump (the conversion deleted those rows later on). A
    chain with two survivors keeps both and maps the rest to the lower-ranked one."""
    superseded: dict[int, int] = {}
    for members in chains.values():
        rank_of = dict(members)
        kept = rank_of.keys() & survivors
        if not kept:
            continue
        survivor = min(kept, key=rank_of.get)  # lowest rank if a chain ever holds two survivors
        for spell_id in rank_of.keys() - kept:
            superseded[spell_id] = survivor
    return superseded


def _override_entry(stock: dict, survivor: int) -> dict:
    table = dbcfmt.SKILLLINEABILITY
    entry = {key: stock[column] for column, key in _TYPED_COLUMNS.items()}
    raw = {column: stock.get(column, 0) for column in table.columns if column not in _TYPED_COLUMNS}
    raw["AcquireMethod"] = 0
    entry["raw_overrides"] = raw
    entry["notes"] = (
        f"superseded rank of collapsed chain (survivor {survivor}): stock row with AcquireMethod "
        f"{stock['AcquireMethod']} -> 0 so pets stop learning it (pet-stale-ranks)"
    )
    return entry


def skilllineability_overrides(
    chains: dict[int, list[tuple[int, int]]],
    spell_entries: list[dict],
    stock_rows: dict[int, dict],
    declared_entries: list[dict],
    existing_rows: dict[int, dict] | None = None,
) -> Overrides:
    """The override entries for every stock row on a superseded rank with AcquireMethod
    LEARNED_ON_SKILL_LEARN, in ID order. `declared_entries` are the source's own
    skill_line_ability entries: an ID among them is left to the declaration and reported in
    `collisions`. With `existing_rows` (stock plus promoted migrations), an ID a migration changed
    to something other than stock or this override is reported in `warnings`, since the override is
    built from the stock row; a promoted copy of the override itself is silent."""
    result = Overrides(superseded=superseded_ranks(chains, survivor_ids(spell_entries)))
    declared_ids = {e["id"] for e in declared_entries}
    for row_id in sorted(stock_rows):
        stock = stock_rows[row_id]
        survivor = result.superseded.get(stock["Spell"])
        if survivor is None or stock["AcquireMethod"] != SKILL_LINE_ABILITY_LEARNED_ON_SKILL_LEARN:
            continue
        if row_id in declared_ids:
            result.collisions.append(
                f"SkillLineAbility {row_id} (spell {stock['Spell']}, superseded by {survivor}) is "
                f"declared in source; the declared row wins over the superseded-rank override"
            )
            continue
        entry = _override_entry(stock, survivor)
        existing = (existing_rows or {}).get(row_id)
        if _changed_elsewhere(existing, stock, build.build_skilllineability_row(entry)):
            result.warnings.append(
                f"SkillLineAbility {row_id} (spell {stock['Spell']}) was changed by a promoted "
                f"migration; the superseded-rank override is built from the stock row and replaces it"
            )
        result.entries.append(entry)
    return result


def _changed_elsewhere(existing: dict | None, stock: dict, override: dict) -> bool:
    """True when a promoted migration left the row as something other than stock or this override.
    The override itself, once promoted, reads back as `existing` and must stay silent."""
    return existing is not None and existing != stock and existing != override


def creaturespelldata_overrides(
    superseded: dict[int, int],
    stock_rows: dict[int, dict],
    existing_rows: dict[int, dict] | None = None,
) -> SpellDataOverrides:
    """Every stock CreatureSpellData record that names a superseded rank, rewritten with each such
    `Spells_N` replaced by the rank's survivor (`Availability_N` and every other slot stay stock), in
    ID order. `superseded` is `Overrides.superseded`. `to_emit` drops the records `existing_rows`
    (stock plus promoted migrations) already carry, so a rerun after promotion emits nothing."""
    table = dbcfmt.CREATURESPELLDATA
    spell_columns = [c for c in table.columns if c.startswith("Spells_")]
    result = SpellDataOverrides()
    existing_rows = existing_rows or {}
    for row_id in sorted(stock_rows):
        stock = stock_rows[row_id]
        if not any(stock[c] in superseded for c in spell_columns):
            continue
        row = {**stock, **{c: superseded.get(stock[c], stock[c]) for c in spell_columns}}
        result.rows.append(row)
        existing = existing_rows.get(row_id)
        if _changed_elsewhere(existing, stock, row):
            result.warnings.append(
                f"CreatureSpellData {row_id} was changed by a promoted migration; the superseded-rank "
                f"override is built from the stock record and replaces it"
            )
        if existing != row:
            result.to_emit.append(row)
    return result
