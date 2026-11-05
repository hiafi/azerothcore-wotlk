"""
Frozen replay inputs: SQL that ran on the live world DB once, from outside `data/sql/`, and that the replay must still
see at the position it ran.

The only one is mod-progression's phase 0 (`replay/frozen/2026_09_02_mod_progression_phase_00/`): the module applied
`src/phase_00/sql/` on 2026-09-02 19:54 (42 `phase_00-*` rows in `acore_world.updates`) and never applied a later
phase. The module is retired; the copies are byte-identical to the files that ran (`MANIFEST` holds their SHA1 = the
`updates` hashes) and are never edited. Each frozen directory has a `SLOT` file naming its neighbours in
`data/sql/updates/db_world/`:

    after = 2026_08_21_01.sql
    before = 2026_08_22_00.sql

`splice()` puts the directory's `*.sql` files (byte order, which is the order they were applied) right after `after`
(or, if only `before` is present, right before it) in a sorted list of promoted files. A list that holds neither
(a test's temporary directory) is returned unchanged. A promoted file that sorts between the two names is an error:
whether it ran before or after the frozen SQL cannot be told from its name.

Readers: `trainer_state._migration_files_mentioning` (every table replay, and through it `stale_overlay` and
`spell_tables`) and `state.load_existing_rows` (the DBC tables).

**Normalised on read.** The files stay byte-identical on disk, but `sqlcorpus.read_text` hands the replay
`normalise(text)`: three shapes phase 0 uses that the replay's parsers cannot read, rewritten to equivalent SQL
(`-- comments` inside `IN (...)` lists and between INSERT tuples, `SET @a := 1, @b := 2;`, and column names in
another letter case than the schema's). Without it the shared replay skipped or misapplied about 1,000
`creature_template` cells and 200 `disables` rows of phase 0 (`replay_diff.py` found them).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

FROZEN_ROOT = Path(__file__).resolve().parents[1] / "replay" / "frozen"


class FrozenSlotError(ValueError):
    """A frozen directory whose SLOT is malformed, or a promoted file inside its slot."""


@dataclass(frozen=True)
class FrozenSlot:
    directory: Path
    after: str
    before: str
    files: tuple[Path, ...]


def _read_slot(directory: Path) -> FrozenSlot:
    fields: dict[str, str] = {}
    for line in (directory / "SLOT").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep:
            raise FrozenSlotError(f"{directory / 'SLOT'}: not a `key = value` line: {line!r}")
        fields[key.strip()] = value.strip()
    missing = {"after", "before"} - fields.keys()
    if missing:
        raise FrozenSlotError(f"{directory / 'SLOT'}: missing {', '.join(sorted(missing))}")
    if not fields["after"] < fields["before"]:
        raise FrozenSlotError(f"{directory / 'SLOT'}: `after` must sort before `before`")
    files = tuple(sorted(directory.glob("*.sql"), key=lambda p: p.name))
    return FrozenSlot(directory, fields["after"], fields["before"], files)


def slots() -> list[FrozenSlot]:
    """Every directory under `FROZEN_ROOT` that has a `SLOT` file, by directory name."""
    if not FROZEN_ROOT.is_dir():
        return []
    return [_read_slot(d) for d in sorted(FROZEN_ROOT.iterdir()) if (d / "SLOT").is_file()]


def splice(promoted: list[Path]) -> list[Path]:
    """`promoted` (sorted `db_world` files) with each frozen slot's files inserted at its position."""
    result = list(promoted)
    for slot in slots():
        names = [p.name for p in result]
        if slot.after in names:
            at = names.index(slot.after) + 1
        elif slot.before in names:
            at = names.index(slot.before)
        else:
            continue
        inside = [n for n in names if slot.after < n < slot.before]
        if inside:
            raise FrozenSlotError(
                f"{slot.directory.name}: promoted file(s) {', '.join(inside)} sort between {slot.after} and "
                f"{slot.before}, inside the frozen slot; move the slot or rename the file"
            )
        result[at:at] = slot.files
    return result


def is_frozen(path: Path) -> bool:
    """Whether `path` is a frozen replay input (immutable, so a replay of it can be cached like promoted SQL)."""
    return FROZEN_ROOT in Path(path).parents


def strip_line_comments(text: str) -> str:
    """`text` without `-- ...` comments outside quoted strings. The replay's WHERE and VALUES parsers do not skip
    them, and phase 0 annotates every id of an `IN (...)` list and every INSERT tuple that way."""
    if "--" not in text:
        return text
    return _COMMENT_OR_STRING_RE.sub(lambda m: m.group(0) if m.group(0)[0] in "'\"" else "", text)


_COMMENT_OR_STRING_RE = re.compile(r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"|--[^\n]*")


def split_multi_set(text: str) -> str:
    """`SET @a := 1, @b := 2;` as one `SET` per variable: the replay reads only the single-variable form, and phase 0
    sets its Onyxia loot ids with the multi-variable one."""
    def split(m: re.Match) -> str:
        return " ".join(f"SET {part.strip()};" for part in m.group(1).split(","))
    return _MULTI_SET_RE.sub(split, text)


_MULTI_SET_RE = re.compile(r"\bSET\s+(@\w+\s*:?=\s*-?\d+(?:\s*,\s*@\w+\s*:?=\s*-?\d+)+)\s*;", re.IGNORECASE)


def canonical_columns(text: str, columns) -> str:
    """`text` with every backticked name that is one of `columns` in another letter case spelled as the schema spells
    it. MySQL column names are case-insensitive, the replay's WHERE parser is not: phase 0 writes `` `entry` `` for
    `creature_loot_template.Entry`, and an UPDATE guard on a column the row does not hold counts as satisfied, so the
    emblem swap would hit every Emblem of Triumph row instead of the listed bosses."""
    canon = {c.lower(): c for c in columns}
    return re.sub(r"`(\w+)`", lambda m: f"`{canon.get(m.group(1).lower(), m.group(1))}`", text)


_HEAD_TABLE_RE = re.compile(r"\b(?:INTO|FROM|UPDATE)\s+`(\w+)`", re.IGNORECASE)


def normalise(text: str) -> str:
    """A frozen file's text as the replay should read it (see the module docstring). Column names are canonicalised
    against the base dump `CREATE TABLE` of every table the file writes."""
    from . import sql_dump, trainer_state  # trainer_state imports this module

    text = split_multi_set(strip_line_comments(text))
    columns: list[str] = []
    for table in sorted(set(_HEAD_TABLE_RE.findall(text))):
        base = trainer_state.BASE_SQL_DIR / f"{table}.sql"
        if base.is_file():
            try:
                columns.extend(sql_dump.parse_create_table_columns(base, table))
            except ValueError:
                continue
    return canonical_columns(text, columns) if columns else text
