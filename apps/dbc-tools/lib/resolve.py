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


def resolve_rows(entries: list[dict], id_range: dict, existing_rows: dict[int, dict], build_one) -> Resolved:
    kept, edited_ids = [], []
    unchanged = 0
    for entry in entries:
        if in_range(entry["id"], id_range):
            kept.append(entry)
            continue
        existing = existing_rows.get(entry["id"])
        row = build_one(entry)
        if existing is not None and row == existing:
            unchanged += 1
            continue
        kept.append(entry)
        edited_ids.append(entry["id"])
    return Resolved(entries=kept, edited_ids=edited_ids, unchanged=unchanged)
