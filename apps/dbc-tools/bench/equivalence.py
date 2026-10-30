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
  - `data/sql/base`, `var/extractors/dbc`, `modules`, `env/dist/etc`: symlinks to the frozen inputs (read-only by
    construction - generate.py never writes there). `data/sql/updates/db_world` is a directory of hardlinks to the
    frozen files, so a scenario can add a promoted file; it never opens an existing one for writing.
  - `data/sql/updates/pending_db_world`, `src/.../Generated`: copies of the frozen state, `docs/` and `var/dbc-patch`:
    created empty, because a full run writes into them.
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
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FROZEN_REPO = HERE.parents[2]  # the git worktree this harness lives in: source of the frozen inputs
RUNS_DIR = FROZEN_REPO / "var" / "dbc-tools-equiv" / "runs"
DEFAULT_PYTHON = "/home/plex/wow_server/azerothcore-wotlk/apps/dbc-tools/.venv/bin/python"

DEFAULT_SCENARIOS = ("check", "full", "full2", "mutate-full")
# A warrior spell the lints dislike (custom id with EquippedItemClass 0, a unit-target helper with range 0), written
# into the sandbox's copy of the code by the `check-injected` scenario to give the scoped check something to say.
INJECTED_DSL = """from lib.dsl import Effect, EffectType, School
from lib.dsl.registry import spell

inject_bad_209990 = spell(
    id=209990, name='Inject Bad', school=School.NORMAL, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=0.0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=1, implicit_target_a=6)],
    spell_icon_id=1, raw_overrides={'SpellClassSet': 4},
)
"""
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
    # Hardlinks, not a symlink: a scenario may *add* a promoted file (never edits one), and an added file must land in
    # the sandbox, not in the frozen tree.
    shutil.copytree(FROZEN_REPO / "data" / "sql" / "updates" / "db_world", sql / "db_world", copy_function=os.link)
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

def scenario_args(name: str) -> tuple[list[str], str | None]:
    """(generate.py args, what to do to the sandbox first: None, "mutate" a pending file, or "promote" the newest
    generated rev into db_world the way the CI promotion does)"""
    if name in ("check", "check2"):
        return ["--check"], None
    if name in ("full", "full2", "full3"):
        return [], None
    if name == "mutate-full":
        return [], "mutate"
    if name == "promote-full":
        return [], "promote"
    if name == "check-injected":
        return ["--check"], "inject"
    if name.startswith("check-class-"):
        return ["--check", "--class", name.removeprefix("check-class-")], None
    raise SystemExit(f"unknown scenario {name!r}")


def promote_newest(sandbox: Path, generated: dict[str, str]) -> str:
    """Moves the newest generated pending rev into db_world as a new file sorting after every existing one, with the
    `-- DB update` header line CI prepends (apps/ci/ci-pending-sql.sh)."""
    pending = sandbox / "data" / "sql" / "updates" / "pending_db_world"
    newest = sorted(p for p in pending.glob("rev_*.sql") if p.name in generated)[-1]
    db_world = sandbox / "data" / "sql" / "updates" / "db_world"
    # db_world is a hardlink copy of the frozen tree: never open an existing file for writing (that would write through
    # to the tracked original). The new file is named after the last existing one so it sorts after it (an append).
    last = max(p.stem for p in db_world.glob("*.sql") if re.fullmatch(r"\d{4}_\d{2}_\d{2}_\d{2}", p.stem))
    number = int(last.rsplit("_", 1)[1]) + 1
    target = db_world / f"{last.rsplit('_', 1)[0]}_{number:02d}.sql"
    if target.exists() or target.is_symlink():
        raise SystemExit(f"refusing to overwrite {target}")
    header = f"-- DB update {last} -> {target.stem}\n"
    temp = target.with_name(target.name + ".tmp")
    temp.write_text(header + newest.read_text(encoding="utf-8"), encoding="utf-8")
    os.replace(temp, target)
    newest.unlink()
    return newest.name


def mutate_pending(sandbox: Path) -> str:
    frozen = sorted((FROZEN_REPO / "data" / "sql" / "updates" / "pending_db_world").glob("*.sql"))
    target = sandbox / "data" / "sql" / "updates" / "pending_db_world" / frozen[-1].name  # a file git tracks
    with target.open("a", encoding="utf-8") as fh:
        fh.write(MUTATION_SQL)
    return target.name


def mpq_contents(mpq: Path) -> dict[str, str]:
    """{archive path: sha256} of the files inside an MPQ. smpq stamps file times into the archive, so two runs never
    produce the same archive bytes; the files inside are what the client reads."""
    if not mpq.is_file():
        return {}
    with tempfile.TemporaryDirectory(prefix="dbc-equiv-mpq-") as tmp:
        subprocess.run(["smpq", "-x", "-q", str(mpq.resolve())], cwd=tmp, check=True)
        return _tree_digest(Path(tmp))


def capture_outputs(sandbox: Path, dest: Path) -> dict:
    """Digest of every file a run can produce; copies the files themselves into `dest` for later diffing."""
    pending = sandbox / "data" / "sql" / "updates" / "pending_db_world"
    patch = sandbox / "var" / "dbc-patch"
    out = {
        "pending": _tree_digest(pending),
        "headers": _tree_digest(sandbox / "src" / "server" / "game" / "Entities" / "Unit" / "Generated"),
        "docs": _tree_digest(sandbox / "docs"),
        "loose_dbc": _tree_digest(patch / "DBFilesClient"),
        "mpq": mpq_contents(patch / "patch-Z.mpq"),
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


def run_scenario(
    sandbox: Path, run_dir: Path, name: str, python: str, generated: dict[str, str],
    extra_args: list[str] | None = None,
) -> dict:
    args, action = scenario_args(name)
    args = [*args, *(extra_args or [])]
    record: dict = {"scenario": name, "args": args}
    if action == "mutate":
        record["mutated"] = mutate_pending(sandbox)
    elif action == "promote":
        record["promoted"] = promote_newest(sandbox, generated)
    elif action == "inject":
        (sandbox / "apps/dbc-tools/source/classes/warrior/zz_inject.py").write_text(INJECTED_DSL, encoding="utf-8")
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
    new_files = sorted(p.name for p in (sandbox / "data/sql/updates/pending_db_world").glob("*.sql")
                       if p.name not in pending_before)
    record["new_pending"] = len(new_files)

    for file_name in new_files:  # revs are named after the clock: number them in the order they were written
        generated[file_name] = f"<generated #{len(generated)}>.sql"

    def rename(rel: str) -> str:
        return generated.get(rel, rel)

    outputs = capture_outputs(sandbox, scen_dir / "files")
    outputs["pending"] = {rename(k): v for k, v in outputs["pending"].items()}
    if new_files:  # keep the generated SQL under a stable name for text diffs
        shutil.copy2(sandbox / "data/sql/updates/pending_db_world" / new_files[-1], scen_dir / "new_rev.sql")
    record["outputs"] = outputs
    return record


def cmd_run(args: argparse.Namespace) -> int:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", args.label):
        raise SystemExit(f"--label must be a plain name, got {args.label!r}")
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
    generated: dict[str, str] = {}
    for name in args.scenarios.split(","):
        print(f"[{args.label}] scenario {name} ...", flush=True)
        record = run_scenario(sandbox, run_dir, name, args.python, generated, args.gen_args.split())
        manifest["scenarios"].append(record)
        (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
        print(f"[{args.label}] scenario {name}: rc={record['returncode']} {record['seconds']}s "
              f"new_pending={record['new_pending']}", flush=True)
    return 0


def normalized_stdout(label: str, scenario: str) -> str:
    """stdout of a scenario with the `[ x.xs]` progress lines, the sandbox path and the rev name stripped. Done at
    compare time from the raw capture so the normalisation can be refined without re-running anything."""
    raw = (RUNS_DIR / label / "scenarios" / scenario / "stdout.raw.txt").read_text(encoding="utf-8")
    sandbox = RUNS_DIR / label / "sandbox"
    for form in {str(sandbox), str(sandbox.resolve())}:
        raw = raw.replace(form, "<SANDBOX>")
    return _REV_RE.sub("rev_N", _PROGRESS_RE.sub("", raw))


def canonical_pending(digests: dict[str, str]) -> dict[str, str]:
    """Pending files a run wrote are named after the clock; call them `<generated #k>` in name (= time) order, so two
    runs compare by what each scenario wrote, not by when. Files that were already in the frozen tree keep their name.
    (`<new-rev>.sql` is how a manifest from before numbering called the scenario's own file: the newest.)"""
    frozen = {p.name for p in (FROZEN_REPO / "data" / "sql" / "updates" / "pending_db_world").iterdir()}
    written = sorted(name for name in digests if name not in frozen and not name.startswith("<"))
    renames = {name: f"<generated #{i}>.sql" for i, name in enumerate(written)}
    renames["<new-rev>.sql"] = f"<generated #{len(written)}>.sql"
    return {renames.get(name, name): digest for name, digest in digests.items()}


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
        out_a, out_b = normalized_stdout(args.a, name), normalized_stdout(args.b, name)
        if out_a != out_b:
            (RUNS_DIR / "last-compare").mkdir(exist_ok=True)
            (RUNS_DIR / "last-compare" / f"{name}.A.txt").write_text(out_a, encoding="utf-8")
            (RUNS_DIR / "last-compare" / f"{name}.B.txt").write_text(out_b, encoding="utf-8")
            problems.append(f"stdout differs (diff var/dbc-tools-equiv/runs/last-compare/{name}.A.txt .B.txt)")
        for kind in sa["outputs"]:
            da, db = sa["outputs"][kind], sb["outputs"][kind]
            if kind == "pending":
                da, db = canonical_pending(da), canonical_pending(db)
            for key in sorted(set(da) | set(db)):
                if da.get(key) != db.get(key):
                    what = "missing in A" if key not in da else "missing in B" if key not in db else "bytes differ"
                    problems.append(f"{kind}/{key}: {what}")
        status = "IDENTICAL" if not problems else "DIFFERENT"
        print(f"{name:14s} {status}  (A {sa['seconds']}s, B {sb['seconds']}s)")
        for p in problems[:30]:
            print(f"    {p}")
        bad += bool(problems)
    return 1 if bad else 0


def cmd_scoped(args: argparse.Namespace) -> int:
    """For every `check-class-X` scenario of a run: its WARNING/ERROR lines are a subset of the whole-tree `check`
    scenario's (a scoped check may say less than the full one, never something the full one does not say), and report
    what each cost."""
    manifest = json.loads((RUNS_DIR / args.run / "manifest.json").read_text())
    scenarios = {s["scenario"]: s for s in manifest["scenarios"]}
    if "check" not in scenarios:
        raise SystemExit("the run has no whole-tree `check` scenario to compare against")

    def verdicts(scenario: str) -> set[str]:
        text = normalized_stdout(args.run, scenario)
        return {line for line in text.splitlines() if line.startswith(("WARNING:", "ERROR:"))}

    reference = "check-injected" if "check-injected" in scenarios else "check"
    full = verdicts(reference)
    print(f"reference: {reference} ({len(full)} WARNING/ERROR line(s))")
    bad = 0
    for name, record in scenarios.items():
        if not name.startswith("check-class-"):
            continue
        got = verdicts(name)
        extra = got - full
        status = "OK" if not extra and record["returncode"] == scenarios[reference]["returncode"] else "NOT A SUBSET"
        injected = {line for line in full if "209990" in line}  # the check-injected defect belongs to warrior alone
        if status == "OK" and injected and (injected <= got) != (name == "check-class-warrior"):
            status = "MISSES ITS OWN DEFECT" if name == "check-class-warrior" else "SEES ANOTHER CLASS'S DEFECT"
        print(f"{name:26s} {status}  rc={record['returncode']}  {record['seconds']}s")
        for line in sorted(extra)[:10]:
            print(f"    only in the scoped run: {line[:200]}")
        bad += status != "OK"
    return 1 if bad else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run")
    run.add_argument("--label", required=True)
    run.add_argument("--code-ref", required=True, help="git ref of the code under test, or 'worktree'")
    run.add_argument("--scenarios", default=",".join(DEFAULT_SCENARIOS))
    run.add_argument("--python", default=DEFAULT_PYTHON)
    run.add_argument("--gen-args", default="", help="extra generate.py arguments for every scenario, e.g. '--cache'")
    cmp_ = sub.add_parser("compare")
    cmp_.add_argument("a")
    cmp_.add_argument("b")
    scoped = sub.add_parser("scoped")
    scoped.add_argument("run")
    sub.add_parser("list")
    args = parser.parse_args()
    if args.cmd == "run":
        return cmd_run(args)
    if args.cmd == "compare":
        return cmd_compare(args)
    if args.cmd == "scoped":
        return cmd_scoped(args)
    print("\n".join([*DEFAULT_SCENARIOS, "check-class-<name>"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
