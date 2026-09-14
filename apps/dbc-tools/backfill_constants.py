#!/usr/bin/env python3
"""
Backfills `lib.dsl.constants` enum names over raw ints in an already-
migrated `source/classes/<class>.py` file - the readability cleanup
`csv_to_dsl.py`'s own docstring deliberately deferred ("a worthwhile
follow-up a human can do incrementally once real code exists to look at").

Covers exactly the fields `lib/dsl/constants.py` has named values for today:
`Spell(school=..., dispel=..., power_type=...)`, and `mechanic=`/`type=`/
`apply_aura=` wherever they appear (both `Spell.mechanic` and
`Effect.mechanic` use the same `Mechanics` enum, so one substitution rule
covers both contexts). A value with no exact match in `constants.py` is left
as a plain int untouched - per the plan's "grow it as needed" philosophy,
not guessed at. Purely a rename: every substituted value round-trips to the
exact same int (`IntEnum`/`IntFlag` members compare and coerce to `int`
identically), so this changes nothing about what gets built - **always
re-run `verify_dsl_migration.py <class>` afterward anyway**, the same "don't
trust it, diff it" rule Phase 4 established, since a plain text-level
substitution can't itself prove it didn't corrupt something (e.g. a
raw_overrides string literal that happens to contain a matching substring -
unlikely, but that's exactly the kind of thing the row-level diff would
catch and a visual read of the diff might not).

Usage: python3 apps/dbc-tools/backfill_constants.py <class>
Rewrites source/classes/<class>.py in place.
"""

from __future__ import annotations

import enum
import re
import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_ROOT))

from lib.dsl import constants as C  # noqa: E402

SOURCE_DIR = TOOL_ROOT / "source"


def _reverse_map(enum_cls) -> dict[int, str]:
    """value -> member name. Every value in these particular enums is
    unique (curated from grep results against real C++ definitions, no
    duplicates introduced) so this is a safe 1:1 map, not a "first wins"
    approximation."""
    return {int(member.value): member.name for member in enum_cls}


def _render(enum_cls, enum_name: str, value: int) -> str | None:
    """A single `EnumName.MEMBER` for an exact match; for an `IntFlag`
    (bitmask) enum whose value doesn't exactly match one member but *does*
    decompose completely into named members' bits (e.g. Frostfire Bolt's
    `school=20` = `School.FIRE(4) | School.FROST(16)`), an `EnumName.A |
    EnumName.B` expression instead. Returns `None` (leave the raw int alone)
    if nothing accounts for every bit - never guess at an unnamed bit."""
    reverse = _reverse_map(enum_cls)
    name = reverse.get(value)
    if name is not None:
        return f"{enum_name}.{name}"
    if not (isinstance(enum_cls, type) and issubclass(enum_cls, enum.IntFlag)):
        return None
    remaining = value
    parts = []
    for member in enum_cls:
        if member.value and (remaining & member.value) == member.value:
            parts.append(member.name)
            remaining &= ~member.value
    if remaining != 0 or not parts:
        return None  # leftover bits nothing here names - don't guess
    return " | ".join(f"{enum_name}.{p}" for p in parts)


# (kwarg name, enum class, enum class name as it appears in lib.dsl's public
# API). `mechanic` covers both Spell.mechanic and Effect.mechanic - both are
# the real Mechanics enum, so one rule is correct for both.
FIELDS = [
    ("school", C.School, "School"),
    ("dispel", C.DispelType, "DispelType"),
    ("power_type", C.PowerType, "PowerType"),
    ("mechanic", C.Mechanic, "Mechanic"),
    ("type", C.EffectType, "EffectType"),
    ("apply_aura", C.AuraType, "AuraType"),
]


def backfill(text: str) -> tuple[str, set[str]]:
    used: set[str] = set()
    for kwarg, enum_cls, enum_name in FIELDS:
        pattern = re.compile(rf"\b{kwarg}=(-?\d+)\b")

        def _sub(m: re.Match, enum_cls=enum_cls, enum_name=enum_name, kwarg=kwarg) -> str:
            rendered = _render(enum_cls, enum_name, int(m.group(1)))
            if rendered is None:
                return m.group(0)
            used.add(enum_name)
            return f"{kwarg}={rendered}"

        text = pattern.sub(_sub, text)
    return text, used


_IMPORT_RE = re.compile(r"^from lib\.dsl import (.+)$", re.MULTILINE)


def _add_imports(text: str, used: set[str]) -> str:
    if not used:
        return text
    m = _IMPORT_RE.search(text)
    if not m:
        # No existing "from lib.dsl import ..." line (shouldn't happen -
        # csv_to_dsl.py always emits one for Effect) - add a fresh one right
        # after the module docstring.
        insert_at = text.index('"""', text.index('"""') + 3) + 3
        line = f"\nfrom lib.dsl import {', '.join(sorted(used))}\n"
        return text[:insert_at] + line + text[insert_at:]
    existing = {name.strip() for name in m.group(1).split(",")}
    merged = sorted(existing | used)
    return text[: m.start()] + f"from lib.dsl import {', '.join(merged)}" + text[m.end():]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0]} <class>", file=sys.stderr)
        return 2
    path = SOURCE_DIR / "classes" / f"{argv[1]}.py"
    text = path.read_text(encoding="utf-8")
    new_text, used = backfill(text)
    new_text = _add_imports(new_text, used)
    path.write_text(new_text, encoding="utf-8")
    print(f"backfilled {', '.join(sorted(used)) or '(nothing matched)'} into {path}")
    print("Now run: python3 apps/dbc-tools/verify_dsl_migration.py " + argv[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
