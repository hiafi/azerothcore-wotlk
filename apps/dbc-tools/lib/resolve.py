"""
Reconciles source/ entries against what's actually live today (base client
DBC ⊕ current SQL overlay), so the same source file supports two different
things without a flag to tell them apart:

  - **New content**: `id` is inside the reserved block (source/ids.yaml).
    Always built and emitted — this is genuinely new data, minted by the
    generator per docs/dbc-build-pipeline.md's "Corollary" (new spells never
    squat on an existing ID).
  - **Editing an existing spell/talent**: `id` is outside the reserved
    block, but the built row doesn't match what's currently live. This is
    the answer to "what if I want to edit Frostbolt" — pull it in
    (pull.py/pull_talents.py), change a field, and it's now a deliberate
    edit: emitted, with an explicit `DELETE ... WHERE ID IN (...)` (not a
    range delete, since edited existing IDs are scattered, not contiguous)
    so the SQL only ever touches the exact rows this run actually changed.

Anything else — `id` outside the block *and* identical to what's live — is
a pulled-in-for-reference copy nothing has touched yet, and is silently
skipped: pulling a spell in for reading/reference must never by itself
cause a write to the world DB or the client patch.

`build_one` is only used here to *decide* (build once, compare, discard) —
callers should pass a throwaway build (e.g. a scratch `ReuseContext` for
spells) rather than the one whose `.minted` secondary rows they actually
care about, then do the real build pass over just `Resolved.entries`. That
keeps an untouched reference spell whose secondary-table lookup happens to
miss (see `reuse.py`) from leaving an orphan minted row behind even though
the spell itself was never emitted.
"""

from __future__ import annotations

from dataclasses import dataclass

from .source import in_range


@dataclass
class Resolved:
    entries: list[dict]        # source entries to actually build/emit (new + edited)
    edited_ids: list[int]      # subset of the above that are existing-row edits
    unchanged: int              # count of untouched reference rows, skipped


def _normalize_for_compare(value):
    """Collapses two representation-only differences that otherwise make an
    untouched, pulled-in-for-reference row compare unequal to itself forever:

      - `None` vs `''` for an unset locale string. The base client DBC's
        string block has no NULL concept — an unset localized name/
        description reads back as `''` (see `dbcfile.read_dbc`) — while
        `build_spell_row` (and friends) write `None` for the same "no
        override" case. Same field, same real-world value, two Python
        representations depending on which side of the pipeline produced it.
      - `\\r\\n` vs `\\n` inside a multi-line text field. A chunk of
        source/spells/*.csv's `raw_overrides` description/aura-description
        text was pulled in with literal CRLF line breaks baked into the
        JSON string (Windows-authored copy/paste, most likely); the live
        data — extracted straight from the base DBC/SQL — only ever has
        bare `\\n`. Confirmed (2026-09-15, see docs/bugs-and-fixes.md)
        that these two artifacts alone fully explain a 374-spell "needs
        re-editing" block that never actually changed: every single one
        was a pulled-in-for-reference copy whose only "difference" from
        live was one of these two non-differences, not a real edit —
        directly violating this module's own docstring guarantee that
        pulling a spell in for reading must never by itself cause a write.
        Only used for the reconcile-against-live *comparison* — the actual
        built row (what gets emitted for a genuine new/edited entry) is
        untouched, so a real edit still ships whatever source/ actually
        contains."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.replace("\r\n", "\n")
    return value


def _rows_equal(a: dict, b: dict) -> bool:
    return all(
        _normalize_for_compare(a.get(key)) == _normalize_for_compare(b.get(key))
        for key in a.keys() | b.keys()
    )


def resolve_rows(entries: list[dict], id_range: dict, existing_rows: dict[int, dict], build_one) -> Resolved:
    kept, edited_ids = [], []
    unchanged = 0
    for entry in entries:
        if in_range(entry["id"], id_range):
            kept.append(entry)
            continue
        existing = existing_rows.get(entry["id"])
        row = build_one(entry)
        if existing is not None and _rows_equal(row, existing):
            unchanged += 1
            continue
        kept.append(entry)
        edited_ids.append(entry["id"])
    return Resolved(entries=kept, edited_ids=edited_ids, unchanged=unchanged)


def reserved_range_changed(
    rows: list[dict], index_column: str, id_range: dict, edited_ids: list[int],
    existing_rows: dict[int, dict],
) -> bool:
    """True if emitting this table's DELETE+INSERT block (see `sql_out.py`)
    would actually change anything live - either there's a genuine edit
    outside the reserved block (`edited_ids` non-empty - by construction
    from `resolve_rows` above, that can only happen when the built row
    already differs from what's live), or the reserved-block content this
    run would (re)insert differs - a row added, removed, or with a changed
    field - from what's already live in that exact ID range.

    `rows` is *always* built and kept for every in-range ID regardless of
    whether it changed (see this module's own docstring - "new content" is
    unconditionally built/emitted) - this function is what lets a caller
    still tell "genuinely nothing to do here" apart from that, without
    weakening the always-full-reinsert behavior `reuse.py`'s
    `ReuseContext.reserved_rows` itself depends on (see its docstring for
    the wipe-the-whole-range bug that guarantees). False means the block
    would be a pure no-op - re-deleting and re-inserting exactly what's
    already there - so `generate.py` can skip emitting it, instead of every
    run re-emitting a fresh, identically-content'd, differently-timestamped
    migration for every table regardless of whether *this* run touched it."""
    if edited_ids:
        return True
    reserved_new = {
        row[index_column]: row for row in rows
        if id_range["start"] <= row[index_column] <= id_range["end"]
    }
    reserved_existing = {
        id_: row for id_, row in existing_rows.items()
        if id_range["start"] <= id_ <= id_range["end"]
    }
    if reserved_new.keys() != reserved_existing.keys():
        return True
    # Dict `!=` would inherit the same None-vs-'' / CRLF false-positive
    # _normalize_for_compare exists for (see its docstring) - same fix,
    # applied row-by-row since these are keyed by ID, not a single row.
    return any(
        not _rows_equal(reserved_new[id_], reserved_existing[id_])
        for id_ in reserved_new
    )
