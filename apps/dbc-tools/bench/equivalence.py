#!/usr/bin/env python3
"""
Equivalence + timing harness for `generate.py` (dbc-tools-generate-speed plan, stage 1).

Runs `generate.py` from two code versions against the SAME frozen inputs and diffs everything it produces, byte for
byte: the pending SQL, the generated C++ headers, the potency sheets, every loose client-patch `.dbc`, the patch MPQ
and the stdout (minus the `[ x.xs]` progress lines).

How the isolation works. `generate.py` anchors every path at `REPO_ROOT = parents[3]` of its own file, so a run is
confined to whatever tree its code lives in. A *sandbox* is a throwaway tree under `var/dbc-tools-equiv/runs/<label>/
sandbox/`:

  - `apps/dbc-tools` and `apps/item-tools`: a COPY of the code under test (`--code-ref <git ref>`, or `worktree` for the
    current working tree including uncommitted files). Copied, not linked: Python resolves `__file__` through symlinks
    and would walk back out of the sandbox.
  - `data/sql/base`, `data/sql/updates/db_world`, `var/extractors/dbc`, `modules`, `env/dist/etc`: symlinks to the
    frozen inputs (read-only by construction - generate.py never writes there).
  - `data/sql/updates/pending_db_world`, `src/.../Generated`, `docs/`, `var/dbc-patch`: real directories (copies of
    the frozen state), because a full run writes into them.
  - no `lib/local_config.py`, no `env/dist/data/dbc`: nothing is deployed anywhere. `assert_no_deploy` checks it.

No database is read or written (generate.py reads static files only).

Subcommands:
  run      --label L --code-ref REF|worktree [--scenarios a,b,c]   run scenarios in a fresh sandbox
  compare  A B                                                      diff two runs scenario by scenario
  list                                                              known scenarios

Scenario sequence (one sandbox, in order, so later ones see the earlier ones' pending output):
  check          generate.py --check
  full           generate.py                      (cold: first write run)
  full2          generate.py                      (second write run: sees `full`'s pending file)
  mutate-full    edit one pending file (a real statement), then generate.py   (cache invalidation)
  check-class-X  generate.py --check --class X    (new code only; not part of the old/new diff)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FROZEN_REPO = HERE.parents[2]  # the git worktree this harness lives in: source of the frozen inputs
RUNS_DIR = FROZEN_REPO / "var" / "dbc-tools-equiv" / "runs"
DEFAULT_PYTHON = "/home/plex/wow_server/azerothcore-wotlk/apps/dbc-tools/.venv/bin/python"

DEFAULT_SCENARIOS = ("check", "full", "full2", "mutate-full")
MUTATION_SQL = (
    "\n-- equivalence harness mutation\n"
    "UPDATE `spell_dbc` SET `Attributes` = 0 WHERE `ID` = 133;\n"
    "UPDATE `creature_template` SET `minlevel` = 2 WHERE `entry` = 900011;\n"
)

_PROGRESS_RE = re.compile(r"^\[ *\d+\.\ds\] .*\n?", re.MULTILINE)
_REV_RE = re.compile(r"rev_\d+")


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _tree_digest(root: Path, rename=None) -> dict[str, str]:
    """{relative path: sha256} for every file under `root` (empty if it does not exist)."""
    out: dict[str, str] = {}
    if not root.is_dir():
        return out
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            out[rename(rel) if rename else rel] = _sha(path)
    return out


# --------------------------------------------------------------------------------------------------------------
# sandbox
# --------------------------------------------------------------------------------------------------------------

def _code_files(code_ref: str) -> list[str]:
    """Paths (repo-relative) of the code under test."""
    paths = ["apps/dbc-tools", "apps/item-tools"]
    if code_ref == "worktree":
        out = subprocess.run(
            ["git", "ls-files", "-co", "--exclude-standard", "-z", "--", *paths],
            cwd=FROZEN_REPO, capture_output=True, check=True,
        ).stdout.decode()
        return [p for p in out.split("\0") if p and (FROZEN_REPO / p).is_file()]
    out = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", "-z", code_ref, "--", *paths],
        cwd=FROZEN_REPO, capture_output=True, check=True,
    ).stdout.decode()
    return [p for p in out.split("\0") if p]


def build_sandbox(sandbox: Path, code_ref: str) -> None:
    if sandbox.exists():
        shutil.rmtree(sandbox)
    sandbox.mkdir(parents=True)
    if code_ref == "worktree":
        for rel in _code_files(code_ref):
            dest = sandbox / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(FROZEN_REPO / rel, dest)
    else:
        archive = subprocess.run(
            ["git", "archive", code_ref, "apps/dbc-tools", "apps/item-tools"],
            cwd=FROZEN_REPO, capture_output=True, check=True,
        ).stdout
        subprocess.run(["tar", "-x", "-C", str(sandbox)], input=archive, check=True)
    for gitignored in ("bench",):  # the harness itself is not part of what generate.py needs
        shutil.rmtree(sandbox / "apps" / "dbc-tools" / gitignored, ignore_errors=True)

    sql = sandbox / "data" / "sql" / "updates"
    sql.mkdir(parents=True)
    (sandbox / "data" / "sql" / "base").symlink_to(FROZEN_REPO / "data" / "sql" / "base")
    (sql / "db_world").symlink_to(FROZEN_REPO / "data" / "sql" / "updates" / "db_world")
    shutil.copytree(FROZEN_REPO / "data" / "sql" / "updates" / "pending_db_world", sql / "pending_db_world")

    (sandbox / "var" / "extractors").mkdir(parents=True)
    (sandbox / "var" / "extractors" / "dbc").symlink_to(FROZEN_REPO / "var" / "extractors" / "dbc")
    (sandbox / "modules").symlink_to(FROZEN_REPO / "modules")
    (sandbox / "env" / "dist").mkdir(parents=True)
    (sandbox / "env" / "dist" / "etc").symlink_to(FROZEN_REPO / "env" / "dist" / "etc")
    (sandbox / "docs").mkdir()

    generated = Path("src/server/game/Entities/Unit/Generated")
    (sandbox / generated.parent).mkdir(parents=True)
    shutil.copytree(FROZEN_REPO / generated, sandbox / generated)


def assert_no_deploy(sandbox: Path, python: str) -> None:
    """The sandbox's patch_out must have nowhere to deploy and nowhere to copy the DBC files."""
    code = (
        "import sys; sys.path.insert(0, 'apps/dbc-tools'); from lib import patch_out; "
        "print(patch_out.DEPLOY_ROOT, patch_out.REPO_ROOT, patch_out.ENV_DBC_DIR.is_dir())"
    )
    out = subprocess.run([python, "-c", code], cwd=sandbox, capture_output=True, text=True, check=True).stdout.split()
    if out[0] != "None" or Path(out[1]).resolve() != sandbox.resolve() or out[2] != "False":
        raise SystemExit(f"sandbox is not isolated (DEPLOY_ROOT/REPO_ROOT/ENV_DBC_DIR = {out}); refusing to run")


def input_fingerprint() -> dict:
    """Sizes+names of the frozen input listings, recorded so a drifting input shows up in `compare`."""
    def listing(path: Path) -> str:
        h = hashlib.sha256()
        for p in sorted(path.rglob("*")):
            if p.is_file():
                h.update(f"{p.relative_to(path)}:{p.stat().st_size}\n".encode())
        return h.hexdigest()

    return {
        "db_world": listing(FROZEN_REPO / "data" / "sql" / "updates" / "db_world"),
        "base": listing(FROZEN_REPO / "data" / "sql" / "base"),
        "pending": listing(FROZEN_REPO / "data" / "sql" / "updates" / "pending_db_world"),
        "dbc": listing(FROZEN_REPO / "var" / "extractors" / "dbc"),
        "modules": listing(FROZEN_REPO / "modules"),
    }


# --------------------------------------------------------------------------------------------------------------
# scenarios
# --------------------------------------------------------------------------------------------------------------

def scenario_args(name: str) -> tuple[list[str], bool]:
    """(generate.py args, mutate pending first?)"""
    if name == "check":
        return ["--check"], False
    if name in ("full", "full2"):
        return [], False
    if name == "mutate-full":
        return [], True
    if name.startswith("check-class-"):
        return ["--check", "--class", name.removeprefix("check-class-")], False
    raise SystemExit(f"unknown scenario {name!r}")


def mutate_pending(sandbox: Path) -> str:
    frozen = sorted((FROZEN_REPO / "data" / "sql" / "updates" / "pending_db_world").glob("*.sql"))
    target = sandbox / "data" / "sql" / "updates" / "pending_db_world" / frozen[-1].name  # a file git tracks
    with target.open("a", encoding="utf-8") as fh:
        fh.write(MUTATION_SQL)
    return target.name


def capture_outputs(sandbox: Path, dest: Path) -> dict:
    """Digest of every file a run can produce; copies the files themselves into `dest` for later diffing."""
    pending = sandbox / "data" / "sql" / "updates" / "pending_db_world"
    patch = sandbox / "var" / "dbc-patch"
    out = {
        "pending": _tree_digest(pending),
        "headers": _tree_digest(sandbox / "src" / "server" / "game" / "Entities" / "Unit" / "Generated"),
        "docs": _tree_digest(sandbox / "docs"),
        "loose_dbc": _tree_digest(patch / "DBFilesClient"),
        "mpq": {"patch-Z.mpq": _sha(patch / "patch-Z.mpq")} if (patch / "patch-Z.mpq").is_file() else {},
    }
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    # Text outputs are kept whole (they are the ones worth `diff`ing); the binary ones only as digests plus a copy
    # of the MPQ's file list.
    shutil.copytree(pending, dest / "pending_db_world")
    shutil.copytree(sandbox / "src" / "server" / "game" / "Entities" / "Unit" / "Generated", dest / "headers")
    if (sandbox / "docs").is_dir():
        shutil.copytree(sandbox / "docs", dest / "docs")
    return out


def run_scenario(sandbox: Path, run_dir: Path, name: str, python: str) -> dict:
    args, mutate = scenario_args(name)
    record: dict = {"scenario": name, "args": args}
    if mutate:
        record["mutated"] = mutate_pending(sandbox)
    pending_before = {p.name for p in (sandbox / "data/sql/updates/pending_db_world").glob("*.sql")}
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0"}
    start = time.monotonic()
    proc = subprocess.run(
        [python, "apps/dbc-tools/generate.py", *args], cwd=sandbox, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    record["seconds"] = round(time.monotonic() - start, 1)
    record["returncode"] = proc.returncode
    scen_dir = run_dir / "scenarios" / name
    scen_dir.mkdir(parents=True, exist_ok=True)
    (scen_dir / "stdout.raw.txt").write_text(proc.stdout, encoding="utf-8")
    normalized = _REV_RE.sub("rev_N", _PROGRESS_RE.sub("", proc.stdout))
    (scen_dir / "stdout.txt").write_text(normalized, encoding="utf-8")
    new_files = sorted(p.name for p in (sandbox / "data/sql/updates/pending_db_world").glob("*.sql")
                       if p.name not in pending_before)
    record["new_pending"] = len(new_files)

    def rename(rel: str) -> str:
        return "<new-rev>.sql" if rel in new_files else rel

    outputs = capture_outputs(sandbox, scen_dir / "files")
    outputs["pending"] = {rename(k): v for k, v in outputs["pending"].items()}
    if new_files:  # keep the generated SQL under a stable name for text diffs
        shutil.copy2(sandbox / "data/sql/updates/pending_db_world" / new_files[-1], scen_dir / "new_rev.sql")
    record["outputs"] = outputs
    record["stdout_sha"] = hashlib.sha256(normalized.encode()).hexdigest()
    return record


def cmd_run(args: argparse.Namespace) -> int:
    run_dir = RUNS_DIR / args.label
    sandbox = run_dir / "sandbox"
    run_dir.mkdir(parents=True, exist_ok=True)
    build_sandbox(sandbox, args.code_ref)
    assert_no_deploy(sandbox, args.python)
    manifest = {
        "label": args.label, "code_ref": args.code_ref, "inputs": input_fingerprint(), "scenarios": [],
        "code_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=FROZEN_REPO, capture_output=True, text=True,
                                    check=True).stdout.strip(),
    }
    for name in args.scenarios.split(","):
        print(f"[{args.label}] scenario {name} ...", flush=True)
        record = run_scenario(sandbox, run_dir, name, args.python)
        manifest["scenarios"].append(record)
        (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
        print(f"[{args.label}] scenario {name}: rc={record['returncode']} {record['seconds']}s "
              f"new_pending={record['new_pending']}", flush=True)
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    a = json.loads((RUNS_DIR / args.a / "manifest.json").read_text())
    b = json.loads((RUNS_DIR / args.b / "manifest.json").read_text())
    bad = 0
    if a["inputs"] != b["inputs"]:
        print("INPUT DRIFT between runs:", {k: (a["inputs"][k], b["inputs"][k]) for k in a["inputs"]
                                            if a["inputs"][k] != b["inputs"][k]})
        bad += 1
    by_name = {s["scenario"]: s for s in b["scenarios"]}
    for sa in a["scenarios"]:
        name = sa["scenario"]
        sb = by_name.get(name)
        if sb is None or name.startswith("check-class-"):
            continue
        problems = []
        if sa["returncode"] != sb["returncode"]:
            problems.append(f"return code {sa['returncode']} != {sb['returncode']}")
        if sa["stdout_sha"] != sb["stdout_sha"]:
            problems.append("stdout differs (see `diff` of scenarios/%s/stdout.txt)" % name)
        for kind in sa["outputs"]:
            da, db = sa["outputs"][kind], sb["outputs"][kind]
            for key in sorted(set(da) | set(db)):
                if da.get(key) != db.get(key):
                    problems.append(f"{kind}/{key}: {'missing in A' if key not in da else 'missing in B' if key not in db else 'bytes differ'}")
        status = "IDENTICAL" if not problems else "DIFFERENT"
        print(f"{name:14s} {status}  (A {sa['seconds']}s, B {sb['seconds']}s)")
        for p in problems[:30]:
            print(f"    {p}")
        bad += bool(problems)
    return 1 if bad else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run")
    run.add_argument("--label", required=True)
    run.add_argument("--code-ref", required=True, help="git ref of the code under test, or 'worktree'")
    run.add_argument("--scenarios", default=",".join(DEFAULT_SCENARIOS))
    run.add_argument("--python", default=DEFAULT_PYTHON)
    cmp_ = sub.add_parser("compare")
    cmp_.add_argument("a")
    cmp_.add_argument("b")
    sub.add_parser("list")
    args = parser.parse_args()
    if args.cmd == "run":
        return cmd_run(args)
    if args.cmd == "compare":
        return cmd_compare(args)
    print("\n".join([*DEFAULT_SCENARIOS, "check-class-<name>"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
