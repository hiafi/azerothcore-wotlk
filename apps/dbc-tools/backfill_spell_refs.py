#!/usr/bin/env python3
"""
Backfills self-referencing `trigger_spell=<id>` kwargs into `<var>.id` when
`<var>` is that exact spell's own `spell(...)` call - e.g. Arcane Blast's
`trigger_spell=36032` becomes `trigger_spell=arcane_blast_debuff.id` once
`arcane_blast_debuff = spell(id=36032, ...)` exists as a variable. Readability
only: `<var>.id` evaluates to the exact same int at runtime (`Spell.id` is a
plain int field), so this changes nothing about what gets built - **always
re-run verify_dsl_migration.py <class> afterward anyway**, same "don't trust
it, diff it" rule `backfill_constants.py` follows.

Works on both class layouts (see `split_class_file.py`):
  - a single `source/classes/<class>.py` file
  - a `source/classes/<class>/` directory of several files (loaded as a real
    package by `lib/dsl/registry.py`'s `load_class_package`)

A reference to a spell declared in a *different file* of the same class
directory is always safe to backfill - it becomes `<var>.id` plus a
`from .other_file import var` import, and Python resolves it via normal
package-import machinery regardless of which file loads first (this is
`split_class_file.py`'s whole point - see its docstring). A reference to a
spell declared *earlier in the same file* is also safe (already-executed by
the time the reference runs). A reference to a spell declared *later in the
same file* can't be fixed without reordering statements, which this script
deliberately does not attempt - it's reported instead. Splitting the target
spell into a different file (`split_class_file.py`, or by hand) turns a
same-file forward reference into an always-fixable cross-file one - that's
the intended way to clear a report line this script prints, not the other
way around.

Uses `ast` (not regex, unlike `backfill_constants.py`) since matching "this
literal int is the argument to *this* keyword, inside *this* enclosing
spell's call" reliably needs real parsing.

Usage: python3 apps/dbc-tools/backfill_spell_refs.py <class>
Rewrites the class's file(s) in place (same-file forward references excepted).
"""

from __future__ import annotations

import ast
import bisect
import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent
SOURCE_DIR = TOOL_ROOT / "source"

# kwarg names whose value is a plain spell ID that might match a sibling
# `spell()` call - only `trigger_spell` today (what this was built for), kept
# as a set (like backfill_constants.py's FIELDS) since `misc_value`-as-
# spell-id and similar could join later.
SPELL_ID_KWARGS = {"trigger_spell"}


def _class_files(class_name: str) -> list[Path]:
    flat = SOURCE_DIR / "classes" / f"{class_name}.py"
    if flat.is_file():
        return [flat]
    dir_path = SOURCE_DIR / "classes" / class_name
    if dir_path.is_dir():
        return sorted(p for p in dir_path.glob("*.py") if not p.name.startswith("_"))
    raise FileNotFoundError(f"no source/classes/{class_name}.py or source/classes/{class_name}/ directory")


def _spell_id_assignments(tree: ast.Module) -> dict[int, tuple[int, str]]:
    """spell_id -> (top-level statement index in this file, variable name),
    for every `<var> = spell(id=<int literal>, ...)` at module level."""
    result: dict[int, tuple[int, str]] = {}
    for i, stmt in enumerate(tree.body):
        if not isinstance(stmt, ast.Assign):
            continue
        if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
            continue
        call = stmt.value
        if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == "spell"):
            continue
        for kw in call.keywords:
            if kw.arg == "id" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, int):
                result[kw.value.value] = (i, stmt.targets[0].id)
                break
    return result


def _enclosing_stmt_index(tree: ast.Module, lineno: int) -> int:
    starts = [stmt.lineno for stmt in tree.body]
    idx = bisect.bisect_right(starts, lineno) - 1
    return max(idx, 0)


def _offsets(text: str):
    line_starts = [0]
    for line in text.splitlines(keepends=True):
        line_starts.append(line_starts[-1] + len(line))

    def offset(lineno: int, col: int) -> int:
        return line_starts[lineno - 1] + col

    return offset


def analyze_class(files: list[Path]):
    """Returns (fixes_by_path, imports_needed_by_path, reports).
    `fixes_by_path[path]` is a list of (start_offset, end_offset, replacement).
    `imports_needed_by_path[path]` maps target-file-stem -> {varnames} for a
    `from .<stem> import <varnames>` line that path needs added.
    `reports` is human-readable lines for same-file forward references left
    untouched."""
    parsed = {path: (path.read_text(encoding="utf-8"), None) for path in files}
    for path in files:
        text = parsed[path][0]
        parsed[path] = (text, ast.parse(text))

    # spell_id -> (defining path, statement index in that file, variable name)
    id_to_def: dict[int, tuple[Path, int, str]] = {}
    for path, (_, tree) in parsed.items():
        for spell_id, (idx, varname) in _spell_id_assignments(tree).items():
            id_to_def[spell_id] = (path, idx, varname)

    fixes_by_path: dict[Path, list[tuple[int, int, str]]] = {p: [] for p in files}
    imports_needed_by_path: dict[Path, dict[str, set[str]]] = {p: {} for p in files}
    reports: list[str] = []

    for path, (text, tree) in parsed.items():
        offset = _offsets(text)
        for node in ast.walk(tree):
            if not isinstance(node, ast.keyword) or node.arg not in SPELL_ID_KWARGS:
                continue
            value = node.value
            if not (isinstance(value, ast.Constant) and isinstance(value.value, int)):
                continue
            spell_id = value.value
            if spell_id not in id_to_def:
                continue
            target_path, target_idx, varname = id_to_def[spell_id]
            containing_idx = _enclosing_stmt_index(tree, node.lineno)

            if target_path != path:
                start = offset(value.lineno, value.col_offset)
                end = offset(value.end_lineno, value.end_col_offset)
                fixes_by_path[path].append((start, end, f"{varname}.id"))
                imports_needed_by_path[path].setdefault(target_path.stem, set()).add(varname)
                continue

            if target_idx < containing_idx:
                start = offset(value.lineno, value.col_offset)
                end = offset(value.end_lineno, value.end_col_offset)
                fixes_by_path[path].append((start, end, f"{varname}.id"))
            elif target_idx > containing_idx:
                containing_stmt = tree.body[containing_idx]
                referrer = (
                    containing_stmt.targets[0].id
                    if isinstance(containing_stmt, ast.Assign) and isinstance(containing_stmt.targets[0], ast.Name)
                    else f"<stmt at line {containing_stmt.lineno}>"
                )
                reports.append(
                    f"  {path.name} line {node.lineno}: {referrer}'s {node.arg}={spell_id} matches "
                    f"{varname}, declared LATER in the same file (line {tree.body[target_idx].lineno}) - "
                    f"not auto-fixed; splitting {varname} into a different file would make this "
                    f"fixable (see split_class_file.py)"
                )
            # target_idx == containing_idx: a spell whose own id is its own trigger_spell - see
            # backfill_spell_refs.py's module docstring for why that's left as a plain int.

    return fixes_by_path, imports_needed_by_path, reports


def _apply_fixes(text: str, fixes: list[tuple[int, int, str]]) -> str:
    for start, end, replacement in sorted(fixes, key=lambda f: f[0], reverse=True):
        text = text[:start] + replacement + text[end:]
    return text


_RELATIVE_IMPORT_RE_TEMPLATE = r"^from \.{stem} import (.+)$"


def _add_relative_imports(text: str, needed: dict[str, set[str]]) -> str:
    """Merges `from .<stem> import <names>` for each stem in `needed` into
    the file - into an existing line for that stem if one's already there,
    otherwise a new line appended right after the last top-of-file
    `from `/`import ` line (mirrors backfill_constants.py's `_add_imports`,
    generalized to possibly-several target stems instead of one fixed
    line)."""
    import re

    for stem in sorted(needed):
        pattern = re.compile(_RELATIVE_IMPORT_RE_TEMPLATE.format(stem=re.escape(stem)), re.MULTILINE)
        m = pattern.search(text)
        if m:
            existing = {n.strip() for n in m.group(1).split(",")}
            merged = sorted(existing | needed[stem])
            text = text[: m.start()] + f"from .{stem} import {', '.join(merged)}" + text[m.end():]
            continue
        lines = text.splitlines(keepends=True)
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith("from ") or line.startswith("import "):
                insert_at = i + 1
            elif insert_at and line.strip() == "":
                continue
            elif insert_at:
                break
        new_line = f"from .{stem} import {', '.join(sorted(needed[stem]))}\n"
        lines.insert(insert_at, new_line)
        text = "".join(lines)
    return text


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0]} <class>", file=sys.stderr)
        return 2
    class_name = argv[1]
    files = _class_files(class_name)
    fixes_by_path, imports_needed_by_path, reports = analyze_class(files)

    total_fixes = 0
    for path in files:
        fixes = fixes_by_path[path]
        if not fixes and not imports_needed_by_path[path]:
            continue
        text = path.read_text(encoding="utf-8")
        text = _apply_fixes(text, fixes)
        text = _add_relative_imports(text, imports_needed_by_path[path])
        path.write_text(text, encoding="utf-8")
        total_fixes += len(fixes)
        print(f"{class_name}: backfilled {len(fixes)} self-reference(s) into {path}")

    if total_fixes == 0:
        print(f"{class_name}: backfilled 0 self-reference(s)")
    if reports:
        print(f"{class_name}: {len(reports)} same-file forward reference(s) NOT auto-fixed:")
        for line in reports:
            print(line)
    if total_fixes:
        print("Now run: python3 apps/dbc-tools/verify_dsl_migration.py " + class_name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
