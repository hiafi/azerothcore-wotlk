#!/usr/bin/env python3
"""
Splits an already-migrated `source/classes/<class>.py` (one big file) into
`source/classes/<class>/` (a directory of three files) - a readability
follow-up, not a behavior change: `<class>_spells.py` (player-castable
spells), `<class>_trigger_spells.py` (spells that only ever exist to be a
`trigger_spell`/proc target - never directly cast), and `<class>_talents.py`
(tabs, talents, and any standalone `skill_line_ability()` rows). Cross-file
references (a talent's `ranks=[...]`, a spell's `trigger_spell=other.id`)
become plain `from .sibling import name` imports - `lib/dsl/registry.py`'s
`load_class_package` loads the three files as one real Python package, so
these resolve via normal import machinery regardless of which file happens
to come first alphabetically. This is what removes the single-file layout's
"can only reference a spell declared *earlier* in this file" constraint (see
`backfill_spell_refs.py`, which exists only because that constraint used to
be real).

Castable vs. trigger-only uses the exact same heuristic `granted_by_talent()`
already applies to a talent rank (`lib.dsl.registry.looks_player_castable`:
real `cast_time_ms`/`cooldown_ms`, not marked passive) - applied here to
*every* spell in the file, not just talent ranks. This is purely
organizational: which file a `spell()` call's source line lives in has zero
effect on what `generate.py` builds (the merged `Registry` doesn't care which
file contributed an entry) - so a borderline miscategorization here is a
readability nit to fix later, never a correctness bug. **Still always run
verify_dsl_migration.py <class> afterward anyway**, same standing rule as
every other tool in this pipeline - it's what actually proves the split
didn't drop or duplicate anything.

Uses `ast.get_source_segment()` to lift each top-level statement's *exact*
original source text (so multi-hundred-character `raw_overrides`/`notes`
strings round-trip byte-for-byte) - never re-serializes a statement from its
parsed form. Only rewrites: which file each statement lands in, and each
file's own import block. The five stale `# --- ... ---` section-header
comments (they described the old CSV/YAML origin of each block, which this
split's castable/trigger-only grouping doesn't preserve) are dropped rather
than reattached somewhere now-inaccurate; nothing else about a statement's
own text changes.

Usage: python3 apps/dbc-tools/split_class_file.py <class>
Writes source/classes/<class>/<class>_spells.py, _trigger_spells.py,
_talents.py, then deletes source/classes/<class>.py.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from types import SimpleNamespace

TOOL_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_ROOT))

from lib import source, trainer_state  # noqa: E402
from lib.dsl import registry  # noqa: E402

SOURCE_DIR = TOOL_ROOT / "source"

# lib.dsl / lib.dsl.registry public names a class file might reference -
# split into the two import lines the original files already use.
DSL_CONST_NAMES = {
    "School", "PowerType", "DispelType", "Mechanic", "EffectType", "AuraType",
    "Effect", "ApplyAura", "Damage",
}
DSL_FUNC_NAMES = {"spell", "talent", "tab", "skill_line_ability", "granted_by_talent", "trained_by"}

BUCKET_SUFFIX = {"spells": "spells", "trigger_spells": "trigger_spells", "talents": "talents"}


def _call_func_name(call: ast.Call) -> str | None:
    return call.func.id if isinstance(call.func, ast.Name) else None


def _classify(tree: ast.Module, reg: registry.Registry) -> list[tuple[ast.stmt, str, str | None]]:
    """Returns one (statement, bucket, assigned_varname_or_None) per
    top-level content statement (module docstring and top-of-file
    import statements excluded - those get regenerated per destination file,
    not copied)."""
    classified: list[tuple[ast.stmt, str, str | None]] = []
    spell_idx = 0
    for stmt in tree.body:
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(
            stmt.value.value, str
        ):
            continue  # module docstring
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            continue  # regenerated per destination file below

        call = None
        varname = None
        if isinstance(stmt, ast.Assign):
            if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
                raise ValueError(f"line {stmt.lineno}: unsupported assignment shape - expected `var = f(...)`")
            varname = stmt.targets[0].id
            if isinstance(stmt.value, ast.Call):
                call = stmt.value
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            call = stmt.value
        if call is None:
            raise ValueError(f"line {stmt.lineno}: unrecognized top-level statement shape")

        func_name = _call_func_name(call)
        if func_name == "spell":
            entry = reg.spells[spell_idx]
            spell_idx += 1
            # `**entry` rather than hand-picking fields: looks_player_castable only reads a
            # handful of attributes by name (ignores the rest), and this way a future broadening
            # of its heuristic (see its docstring - already grew once) needs no matching update
            # here, since `entry` already carries every field `Spell.to_entry()` produces.
            bucket = "spells" if registry.looks_player_castable(SimpleNamespace(**entry)) else "trigger_spells"
        elif func_name in ("talent", "tab", "granted_by_talent", "skill_line_ability"):
            bucket = "talents"
        elif func_name == "trained_by":
            # No class uses this yet (Phase 3's trained_by() bundling); a trainer grant reads
            # more like "spells" (it's about how a real castable spell is learned) than
            # "talents" - revisit if a real one ever needs splitting.
            bucket = "spells"
        else:
            raise ValueError(f"line {stmt.lineno}: unrecognized top-level call {func_name!r}")
        classified.append((stmt, bucket, varname))
    if spell_idx != len(reg.spells):
        raise AssertionError(
            f"matched {spell_idx} top-level spell() statements but the loaded Registry has "
            f"{len(reg.spells)} spells - a spell() call outside a simple top-level `var = spell(...)` "
            f"assignment would break the statement<->entry alignment this script relies on."
        )
    return classified


def _referenced_names(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}


def split(text: str, class_name: str, ids_cfg: dict, trainer_index) -> dict[str, str]:
    tree = ast.parse(text)
    tmp_path = Path(f"<{class_name}.py>")
    # Load for real (through the standard loader, ids_cfg/trainer_index wired the same way
    # generate.py does) to get every spell's *actual* resolved attributes/cast_time_ms/
    # cooldown_ms (enum members, `|`-combined School bitmasks, etc. all already collapsed to
    # plain ints by Spell.to_entry()) - classification needs real values, not a re-implementation
    # of Python expression evaluation over the AST.
    real_path = SOURCE_DIR / "classes" / f"{class_name}.py"
    reg = registry.load_class_file(real_path, ids_cfg=ids_cfg, trainer_index=trainer_index)

    classified = _classify(tree, reg)
    var_bucket = {varname: bucket for _, bucket, varname in classified if varname is not None}

    buckets: dict[str, list[ast.stmt]] = {"spells": [], "trigger_spells": [], "talents": []}
    for stmt, bucket, _ in classified:
        buckets[bucket].append(stmt)

    files: dict[str, str] = {}
    for bucket, stmts in buckets.items():
        if not stmts:
            continue
        used_names: set[str] = set()
        cross_imports: dict[str, set[str]] = {}  # source bucket -> {names}
        bodies = []
        for stmt in stmts:
            used_names |= _referenced_names(stmt)
            for name in _referenced_names(stmt):
                src_bucket = var_bucket.get(name)
                if src_bucket is not None and src_bucket != bucket:
                    cross_imports.setdefault(src_bucket, set()).add(name)
            segment = ast.get_source_segment(text, stmt)
            if segment is None:
                raise AssertionError(f"could not recover source for statement at line {stmt.lineno}")
            bodies.append(segment)

        const_names = sorted(used_names & DSL_CONST_NAMES)
        func_names = sorted(used_names & DSL_FUNC_NAMES)
        import_lines = []
        if const_names:
            import_lines.append(f"from lib.dsl import {', '.join(const_names)}")
        if func_names:
            import_lines.append(f"from lib.dsl.registry import {', '.join(func_names)}")
        for src_bucket in sorted(cross_imports):
            names = ", ".join(sorted(cross_imports[src_bucket]))
            import_lines.append(f"from .{class_name}_{BUCKET_SUFFIX[src_bucket]} import {names}")

        role = {
            "spells": "player-castable spells (real cast_time_ms/cooldown_ms, not marked passive)",
            "trigger_spells": "spells that are never directly cast - proc/periodic-tick effects, "
            "trigger_spell targets, hidden talent-rank buffs, etc.",
            "talents": "talent tabs, talents (granted_by_talent bundles a rank's SkillLineAbility "
            "row too - see lib/dsl/registry.py), and any standalone skill_line_ability() row",
        }[bucket]
        docstring = (
            f'"""\n{class_name.capitalize()} - {role}.\n\n'
            f"Split from a single source/classes/{class_name}.py via split_class_file.py "
            f"(.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md) - see "
            f"source/classes/README.md for the multi-file layout and lib/dsl/registry.py's "
            f"load_class_package for how cross-file references (`from .{class_name}_...` below) "
            f'resolve.\n"""'
        )
        files[bucket] = docstring + "\n\n" + "\n".join(import_lines) + "\n\n\n" + "\n\n\n".join(bodies) + "\n"
    return files


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0]} <class>", file=sys.stderr)
        return 2
    class_name = argv[1]
    flat_path = SOURCE_DIR / "classes" / f"{class_name}.py"
    text = flat_path.read_text(encoding="utf-8")

    ids_cfg = source.load_ids(SOURCE_DIR / "ids.yaml")
    trainer_index = trainer_state.load_trainer_index()
    files = split(text, class_name, ids_cfg, trainer_index)

    out_dir = SOURCE_DIR / "classes" / class_name
    out_dir.mkdir(exist_ok=True)
    for bucket, content in files.items():
        out_path = out_dir / f"{class_name}_{BUCKET_SUFFIX[bucket]}.py"
        out_path.write_text(content, encoding="utf-8")
        print(f"wrote {out_path} ({content.count(chr(10))} lines)")
    flat_path.unlink()
    print(f"removed {flat_path}")
    print(f"Now run: python3 apps/dbc-tools/verify_dsl_migration.py {class_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
