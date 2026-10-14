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

`retire_pet_spell()` (hunter-rework T1, SHARED §C7.8) rides the same two paths: `retired_skilllineability_overrides`
adds AcquireMethod 0 overrides for a retired pet ability and `spell_data_strips` plans the CreatureSpellData strip
that `creaturespelldata_overrides` applies after the superseded-rank mapping (one row per record).

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
    matched: set[int] = field(default_factory=set)  # retire_pet_spell spell ids that found a pet row in scope


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


def _zero_acquire_entry(stock: dict, notes: str) -> dict:
    """The stock row as a source-shaped `skill_line_ability` entry with `AcquireMethod` 0."""
    table = dbcfmt.SKILLLINEABILITY
    entry = {key: stock[column] for column, key in _TYPED_COLUMNS.items()}
    raw = {column: stock.get(column, 0) for column in table.columns if column not in _TYPED_COLUMNS}
    raw["AcquireMethod"] = 0
    entry["raw_overrides"] = raw
    entry["notes"] = notes
    return entry


def _override_entry(stock: dict, survivor: int) -> dict:
    return _zero_acquire_entry(
        stock,
        f"superseded rank of collapsed chain (survivor {survivor}): stock row with AcquireMethod "
        f"{stock['AcquireMethod']} -> 0 so pets stop learning it (pet-stale-ranks)",
    )


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


PET_SHARED_SKILL_LINE = 270  # "Pet - Hunter": skillLine[1] of every hunter pet family


def family_skill_lines(families: dict[int, dict]) -> dict[int, tuple[int, ...]]:
    """CreatureFamily id -> its non-zero skill lines (`CreatureFamily.dbc` SkillLine_1/_2), from the
    rows `state.load_stock_rows(dbcfmt.CREATUREFAMILY)` returns. Hunter families carry their own line and
    the shared 270; warlock demons carry only their own."""
    return {
        fid: tuple(line for line in (int(row["SkillLine_1"]), int(row["SkillLine_2"])) if line)
        for fid, row in families.items()
    }


def retired_skilllineability_overrides(
    retirements: list[dict],
    stock_rows: dict[int, dict],
    lines_by_family: dict[int, tuple[int, ...]],
    declared_entries: list[dict],
    taken_ids: set[int] | frozenset[int] = frozenset(),
    existing_rows: dict[int, dict] | None = None,
) -> Overrides:
    """AcquireMethod 0 overrides for `retire_pet_spell()` declarations (`retirements` are the registry's
    `pet_spell_retirements` entries: `spell_id`, `families` = None or a tuple of CreatureFamily ids).

    A retirement for every family hits the stock rows teaching the spell on 270 and on any family's line.
    One scoped to families hits only the lines those families use *alone*: a line another family also
    uses (the shared 270) would take the spell from them too, so that row is left and reported in
    `warnings` - unless the retirement carries `shared_lines` (`retire_pet_spell(..., shared_lines=True)`),
    which retires those rows for every family while the CreatureSpellData strip stays scoped to `families`
    (PET §4.6's Cower 13012: a 270-only row retired for the non-Ferocity families' records). A shared-line row
    that is declared in source is left to the declaration without the warning. A family id with no CreatureFamily row is reported too. A row already at AcquireMethod 0 is
    skipped; so is an id in `taken_ids` (the superseded-rank pass already emits the identical row). An id
    among `declared_entries` is left to the declaration and reported in `collisions`, like the rank pass."""
    result = Overrides()
    users: dict[int, set[int]] = {}
    for family, lines in lines_by_family.items():
        for line in lines:
            users.setdefault(line, set()).add(family)
    every_pet_line = {PET_SHARED_SKILL_LINE, *users}
    declared_ids = {e["id"] for e in declared_entries}
    emitted: set[int] = set()
    for retirement in retirements:
        spell_id, families = retirement["spell_id"], retirement["families"]
        take_shared = bool(retirement.get("shared_lines"))
        shared: set[int] = set()
        if families is None:
            lines = every_pet_line
        else:
            lines = set()
            for family in families:
                if family not in lines_by_family:
                    result.warnings.append(
                        f"retire_pet_spell({spell_id}, families=...): family {family} has no CreatureFamily.dbc row"
                    )
                    continue
                for line in lines_by_family[family]:
                    (lines if take_shared or users[line] <= set(families) else shared).add(line)
        for row_id in sorted(stock_rows):
            stock = stock_rows[row_id]
            if stock["Spell"] != spell_id or stock["AcquireMethod"] == 0:
                continue
            if stock["SkillLine"] in shared:
                result.matched.add(spell_id)
                if row_id in declared_ids:
                    continue
                result.warnings.append(
                    f"retire_pet_spell({spell_id}, families={list(families)}): SkillLineAbility {row_id} teaches "
                    f"it on skill line {stock['SkillLine']}, which other families use too, so it stays; retire "
                    f"the spell for every family (families=None), pass shared_lines=True, or give those families "
                    f"their own row"
                )
                continue
            if stock["SkillLine"] not in lines or row_id in emitted:
                continue
            result.matched.add(spell_id)
            emitted.add(row_id)
            if row_id in declared_ids:
                result.collisions.append(
                    f"SkillLineAbility {row_id} (spell {spell_id}, retired by retire_pet_spell) is declared in "
                    f"source; the declared row wins over the retirement override"
                )
                continue
            if row_id in taken_ids:
                continue
            entry = _zero_acquire_entry(
                stock,
                f"retired pet spell {spell_id}: stock row with AcquireMethod {stock['AcquireMethod']} -> 0 so "
                f"pets stop learning it (retire_pet_spell)",
            )
            existing = (existing_rows or {}).get(row_id)
            if _changed_elsewhere(existing, stock, build.build_skilllineability_row(entry)):
                result.warnings.append(
                    f"SkillLineAbility {row_id} (spell {spell_id}) was changed by a promoted migration; the "
                    f"retire_pet_spell override is built from the stock row and replaces it"
                )
            result.entries.append(entry)
    return result


def spell_data_strips(
    retirements: list[dict], creature_rows: dict[int, dict], spell_data_rows: dict[int, dict],
    superseded: dict[int, int] | None = None,
) -> tuple[dict[int, frozenset[int]], list[str]]:
    """Which spells each CreatureSpellData record must lose: `(record id -> spells, warnings)`.

    A retirement for every family strips the spell from every record some creature names in
    `PetSpellDataId`. One scoped to families strips it from the records their creatures
    (`creature_template.family`) name - unless a creature of another family names the same record and the
    record holds the spell, in which case the record is left alone and reported (a record cannot be split).
    `creature_rows` are the live `creature_template` rows, `spell_data_rows` the stock records.

    A record "holds" the spell when a slot is the spell itself **or a superseded rank that
    `creaturespelldata_overrides` maps onto it** (`superseded`: `Overrides.superseded`, rank -> survivor).
    Without that, a record naming only an older rank of a collapsed chain (Spider Bite: 92 records) came out
    of the mapping holding the retired survivor and was never stripped (T-FIX T1-2)."""
    table = dbcfmt.CREATURESPELLDATA
    spell_columns = [c for c in table.columns if c.startswith("Spells_")]
    named_by: dict[int, set[int]] = {}  # record id -> families of the creatures naming it
    for row in creature_rows.values():
        record = int(row.get("PetSpellDataId") or 0)
        if record:
            named_by.setdefault(record, set()).add(int(row.get("family") or 0))
    superseded = superseded or {}
    strips: dict[int, set[int]] = {}
    warnings: list[str] = []
    for retirement in retirements:
        spell_id, families = retirement["spell_id"], retirement["families"]
        for record in sorted(named_by):
            stock = spell_data_rows.get(record)
            if stock is None or not any(
                stock[c] and (stock[c] == spell_id or superseded.get(stock[c]) == spell_id) for c in spell_columns
            ):
                continue
            if families is None:
                strips.setdefault(record, set()).add(spell_id)
            elif named_by[record] & set(families):
                if named_by[record] - set(families):
                    warnings.append(
                        f"retire_pet_spell({spell_id}, families={list(families)}): CreatureSpellData {record} holds "
                        f"it and is also named by creatures of families {sorted(named_by[record] - set(families))}, "
                        f"so it is left alone; those families' pets keep it as a default spell"
                    )
                else:
                    strips.setdefault(record, set()).add(spell_id)
    return {record: frozenset(spells) for record, spells in strips.items()}, warnings


def creaturespelldata_overrides(
    superseded: dict[int, int],
    stock_rows: dict[int, dict],
    existing_rows: dict[int, dict] | None = None,
    strips: dict[int, frozenset[int]] | None = None,
) -> SpellDataOverrides:
    """Every stock CreatureSpellData record that names a superseded rank, rewritten with each such
    `Spells_N` replaced by the rank's survivor (`Availability_N` and every other slot stay stock), in
    ID order. `superseded` is `Overrides.superseded`. `to_emit` drops the records `existing_rows`
    (stock plus promoted migrations) already carry, so a rerun after promotion emits nothing.

    `strips` (`spell_data_strips`: record id -> spells to remove) adds `retire_pet_spell()`'s second rule:
    a record that holds a stripped spell - by its stock slot or after the survivor mapping above - gets
    that slot (and its `Availability_N`) zeroed. One row per record: a record both rules touch is mapped
    first, then stripped, so retiring a survivor also removes the superseded ranks that mapped onto it."""
    table = dbcfmt.CREATURESPELLDATA
    spell_columns = [c for c in table.columns if c.startswith("Spells_")]
    strips = strips or {}
    result = SpellDataOverrides()
    existing_rows = existing_rows or {}
    for row_id in sorted(stock_rows):
        stock = stock_rows[row_id]
        strip = strips.get(row_id, frozenset())
        mapped = any(stock[c] in superseded for c in spell_columns)
        stripped = any(stock[c] in strip or superseded.get(stock[c]) in strip for c in spell_columns if stock[c])
        if not mapped and not stripped:
            continue
        row = {**stock, **{c: superseded.get(stock[c], stock[c]) for c in spell_columns}}
        for column in spell_columns:
            if row[column] in strip or stock[column] in strip:
                row[column] = 0
                row[column.replace("Spells_", "Availability_")] = 0
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
