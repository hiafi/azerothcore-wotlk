"""
Binary read/patch support for "Gt" ("game table") DBCs - GtCombatRatings.dbc and
GtOCTClassCombatRatingScalar.dbc specifically, though the format is shared by every GtXxx.dbc.

These are a completely different shape from the record DBCs lib/dbcfmt.py models (Spell.dbc,
Talent.dbc, ...): no strings, just a flat table of floats read positionally by a computed index
(`cr * GT_MAX_LEVEL + level - 1` for GtCombatRatings, `(class-1) * GT_MAX_RATING + cr + 1` for
GtOCTClassCombatRatingScalar - see Unit.h/Player::GetRatingMultiplier) - not by any field a human
would recognize as an ID, so there's nothing here to regenerate from source data the way
spells/talents are.

Two different on-disk shapes exist among real Gt-tables, confirmed by extracting both from a real
3.3.5a client and comparing headers against this fork's own server-side copies byte for byte:
  - GtCombatRatings.dbc:                  field_count=1 - just a float per record, no index field
                                           on disk at all (a record's index is its position).
  - GtOCTClassCombatRatingScalar.dbc:     field_count=2 - a stored index field (row position + a
                                           per-table starting offset, e.g. +1 here) then the float.
`DBCfmt.h`'s `"df"` format string (shared by every GtXxx.dbc name in that file) describes the
*parsed* C++ struct shape (`{float ratio;}` either way - the 'd'/FT_SORT field, when present on
disk, is never copied into it) - not the raw file layout, which is genuinely 1-field for some
Gt-tables and 2-field for others. Trusting the format string's letter count over the file's own
header (as an earlier version of this module did) breaks on the 1-field ones.

The *value* side of a patch comes from the live server database, not another binary DBC: AzerothCore
overlays a same-named SQL table (`gtcombatratings_dbc`, `gtoctclasscombatratingscalar_dbc`) on top
of whatever the binary file parses to (DBCDatabaseLoader), and for GtCombatRatings.dbc specifically
the binary file's own field_count (1) doesn't match what `DBCfmt.h` expects (2) - so
`AutoProduceData` silently produces zero rows from the binary in AzerothCore's own C++ loader, and
the SQL table ends up being *100% of the effective data*, confirmed by querying a live server and
finding its values match the ones this was written to reproduce exactly. See patch_gt_tables.py for
how those values get in (a plain id->float mapping, however it was obtained) and why only the
*client's* copy of these two files needs patching.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

WDBC_MAGIC = b"WDBC"
HEADER_FORMAT = "<4sIIII"  # magic, record_count, field_count, record_size, string_size
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

# Matches Unit.h/DBCStructure.h exactly - see src/server/shared/DataStores/DBCStructure.h.
GT_MAX_LEVEL = 100
GT_MAX_RATING = 32

# The 4 combat-rating slots this fork repurposes onto stock/legacy meanings (see Unit.h's
# CombatRating enum and client/CustomStatStrings/CustomStatStrings.lua for the C++/item-mod side
# of the same mapping).
CUSTOM_COMBAT_RATINGS = {
    "Mastery": 20,             # was CR_WEAPON_SKILL_MAINHAND
    "Versatility": 21,         # was CR_WEAPON_SKILL_OFFHAND
    "Cooldown Haste": 22,      # was CR_WEAPON_SKILL_RANGED
    "Proc Rate": 11,           # was CR_HIT_TAKEN_MELEE
}

# Playable class IDs in 3.3.5a (ChrClasses.dbc) - 10 is unused (reserved/Monk in later
# expansions), so there's no row worth touching for it.
WOTLK_CLASS_IDS = (1, 2, 3, 4, 5, 6, 7, 8, 9, 11)


@dataclass(frozen=True)
class GtHeader:
    record_count: int
    field_count: int  # 1 (bare float, index = position) or 2 (stored index field + float)
    record_size: int
    string_size: int


def read_header(data: bytes) -> GtHeader:
    magic, record_count, field_count, record_size, string_size = struct.unpack_from(HEADER_FORMAT, data, 0)
    if magic != WDBC_MAGIC:
        raise ValueError(f"not a WDBC file (magic was {magic!r})")
    if field_count not in (1, 2):
        raise ValueError(
            f"expected a 1-field (bare float) or 2-field (index+float) Gt-table, got "
            f"field_count={field_count} - wrong file, or a Gt-table shape this tool doesn't know about"
        )
    return GtHeader(record_count, field_count, record_size, string_size)


def build_index_map(data: bytes, header: GtHeader) -> dict[int, int]:
    """Index -> that record's byte offset. For a field_count==1 table there's no stored index at
    all, so a record's index is simply its position. For field_count==2, the index is whatever
    raw value is actually stored in the first 4 bytes of the record - in every real Gt-table this
    just equals the row's position too, but look it up rather than assume it, matching
    DBCFileLoader::AutoProduceData's own approach (it keys off the field's value, not the record's
    position in the file)."""
    index_map: dict[int, int] = {}
    for row in range(header.record_count):
        offset = HEADER_SIZE + row * header.record_size
        if header.field_count == 1:
            index_map[row] = offset
        else:
            (idx,) = struct.unpack_from("<I", data, offset)
            index_map[idx] = offset
    return index_map


def get_float(data: bytes, header: GtHeader, record_offset: int) -> float:
    field_offset = 0 if header.field_count == 1 else 4  # skip the stored index field, if any
    (value,) = struct.unpack_from("<f", data, record_offset + field_offset)
    return value


def set_float(data: bytearray, header: GtHeader, record_offset: int, value: float) -> None:
    field_offset = 0 if header.field_count == 1 else 4
    struct.pack_into("<f", data, record_offset + field_offset, value)


@dataclass(frozen=True)
class Change:
    index: int
    old_value: float
    new_value: float


def patch_values(client_bytes: bytes, values: dict[int, float], indices: list[int]) -> tuple[bytes, list[Change]]:
    """Set each of `indices` in a copy of `client_bytes` to the matching value from `values`
    (keyed by the same index scheme as combat_ratings_index/class_scalar_index). Every other row
    in `client_bytes` - including the record_count/header - is returned untouched."""
    header = read_header(client_bytes)
    index_map = build_index_map(client_bytes, header)

    out = bytearray(client_bytes)
    changes: list[Change] = []
    for idx in indices:
        if idx not in values:
            raise KeyError(f"no server value provided for index {idx}")
        if idx not in index_map:
            raise KeyError(f"index {idx} not present in client DBC (record_count={header.record_count})")
        new_value = values[idx]
        old_value = get_float(out, header, index_map[idx])
        if old_value != new_value:
            set_float(out, header, index_map[idx], new_value)
        changes.append(Change(idx, old_value, new_value))
    return bytes(out), changes


def combat_ratings_index(cr: int, level: int) -> int:
    """Matches Player::GetRatingMultiplier's GtCombatRatings.dbc lookup exactly."""
    return cr * GT_MAX_LEVEL + (level - 1)


def class_scalar_index(class_id: int, cr: int) -> int:
    """Matches Player::GetRatingMultiplier's GtOCTClassCombatRatingScalar.dbc lookup exactly."""
    return (class_id - 1) * GT_MAX_RATING + cr + 1
