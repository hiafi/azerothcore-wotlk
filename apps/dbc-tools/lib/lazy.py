"""
`Lazy`: a stand-in for a value that is costly to load and that a scoped run may never touch.

`generate.py --check --class X` loads one class's DSL files, which hand a few validators live world state
(`trained_by()` the trainer index, `creature_template()` the live creature rows, `item_template()` the item rows). A
class that never calls those helpers should not pay for loading them, but the DSL loader takes plain objects, not
loaders. A `Lazy` stands in: it loads on first use and then behaves as the loaded value for the operations the
loader's helpers use (attribute access, `in`, indexing, iteration, `len`, truthiness).
"""

from __future__ import annotations

from typing import Callable

_UNSET = object()


class Lazy:
    def __init__(self, loader: Callable[[], object]):
        object.__setattr__(self, "_loader", loader)
        object.__setattr__(self, "_value", _UNSET)

    def _get(self):
        value = object.__getattribute__(self, "_value")
        if value is _UNSET:
            value = object.__getattribute__(self, "_loader")()
            object.__setattr__(self, "_value", value)
        return value

    @property
    def loaded(self) -> bool:
        return object.__getattribute__(self, "_value") is not _UNSET

    def __getattr__(self, name: str):
        return getattr(self._get(), name)

    def __contains__(self, item) -> bool:
        return item in self._get()

    def __getitem__(self, key):
        return self._get()[key]

    def __iter__(self):
        return iter(self._get())

    def __len__(self) -> int:
        return len(self._get())

    def __bool__(self) -> bool:
        return bool(self._get())
