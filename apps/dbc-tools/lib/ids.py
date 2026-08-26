"""Reserved-ID-block allocation for source/ids.yaml.

The forward pipeline (generate.py) never needs this — it just builds whatever
IDs source/ already contains. This exists purely for editing convenience (the
webui's "new spell"/"new talent"/... forms): given the set of IDs already in
use anywhere in source/, suggest the next free one from the right reserved
block instead of the human eyeballing source/ids.yaml by hand.
"""

from __future__ import annotations


class NoFreeIdError(ValueError):
    pass


def next_free_id(ids_cfg: dict, kind: str, used_ids: set[int]) -> int:
    """First integer in ids_cfg[kind]'s [start, end] range not already in
    used_ids. `used_ids` should be the merged set of IDs already present
    across every source file for this kind (e.g. every source/spells/*.csv
    row's "id", for kind="spell") — not just one class's file — so the
    suggestion can never collide with another class's already-claimed ID."""
    id_range = ids_cfg[kind]
    for candidate in range(id_range["start"], id_range["end"] + 1):
        if candidate not in used_ids:
            return candidate
    raise NoFreeIdError(
        f"no free ID left in the '{kind}' reserved block "
        f"({id_range['start']}-{id_range['end']}) — widen it in source/ids.yaml"
    )
