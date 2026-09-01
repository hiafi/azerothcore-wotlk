"""Reserved item-entry ID block from `source/ids.yaml` (see that file's
header for the reasoning), plus a "suggest the next free one" helper for
the webui's new-item form."""

from __future__ import annotations

from pathlib import Path

import yaml

SOURCE_DIR = Path(__file__).resolve().parent.parent / "source"
IDS_FILE = SOURCE_DIR / "ids.yaml"


def item_range() -> dict:
    data = yaml.safe_load(IDS_FILE.read_text(encoding="utf-8"))
    return data["item"]


def suggest_new_id(existing_entries) -> int:
    """Lowest ID in the reserved `item` block not already used by an
    existing row (base, merged, or pending)."""
    bounds = item_range()
    used = set(existing_entries)
    for candidate in range(bounds["start"], bounds["end"] + 1):
        if candidate not in used:
            return candidate
    raise RuntimeError("item ID block in source/ids.yaml is exhausted")


def in_range(entry: int) -> bool:
    bounds = item_range()
    return bounds["start"] <= entry <= bounds["end"]
