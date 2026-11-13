#!/usr/bin/env python3
"""
The hunter pet family sweep (hunter-pet-families PLAN 6, stage SIM1): the BM hunter profile with every pet family of
pet_families.tsv at 1, 3 and 5 targets under the full_raid buff set (raid buffs on the hunter and its pet, raid
debuffs on the dummies, Bloodlust at the pull; DpsSim.BuffSet in dpssim.conf.dist), so a family's own group buff or
debuff adds nothing to its number (BRAINSTORM ruling 7) and only its kit separates it from the others. The measuring
tool for the TUNE stage: every family within about 50 DPS of the others at 1 target (ruling 8).

Each run is one tools/run-sim.sh call (a throwaway worldserver container), at most 6 at once (about 2.4 GB each once
running), with DPSSIM_PET_FAMILY=<key>, DPSSIM_BUFF_SET, DPSSIM_BATCH_TAG=<sweep>-<key>-t<n> (the report timestamp has
a 1 s resolution, so parallel runs need their own names) and DPSSIM_NO_HTML=1. All 1-target runs are queued first, so
a sweep cut short still has the number that matters.

    run    launches the matrix, writes <out>/manifest.json and one log per run, then the index
    index  reads the reports of a manifest and writes <out>/sweep.csv (one row per family and target count) and
           <out>/summary.md / summary.json: per family the DPS at 1/3/5 targets, the pet's share of the damage, the
           spread from the median of the swept families, and a flag when the 1-target DPS is more than --threshold
           (50) from that median.
    list   prints the family table

Usage:
    pet_family_sweep.py run [--out DIR] [--sweep ID] [--families wolf,cat,...] [--targets 1,3,5]
                            [--profile BmHunterSim] [--race 6] [--duration 120] [--iterations 5] [--step 100]
                            [--level 60] [--jobs 6] [--buff-set full_raid] [--disable-spells IDS] [--threshold 50]
                            [--dry-run]
    pet_family_sweep.py index <out-dir-or-manifest.json> [--threshold 50]
    pet_family_sweep.py list

--families takes keys, names or family numbers (pet_families.tsv), default all 32. The image is run-sim.sh's (the live
one unless DPSSIM_IMAGE is set in the environment).
"""

from __future__ import annotations

import argparse
import concurrent.futures
import csv
import datetime
import json
import os
import statistics
import subprocess
import sys
import threading
import time
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parents[2]
RUN_SIM = TOOLS_DIR / "run-sim.sh"
REPORTS_DIR = TOOLS_DIR.parent / "reports"
FAMILIES_TSV = TOOLS_DIR / "pet_families.tsv"

# Never more parallel sims than this (memory: about 2.4 GB each once running, dpssim-parallel-limit)
MAX_JOBS = 6
# Ruling 8: every family within about 50 DPS at 1 target
DEFAULT_THRESHOLD = 50.0

print_lock = threading.Lock()


def log(message: str) -> None:
    with print_lock:
        print(message, file=sys.stderr, flush=True)


# ---- the family table -----------------------------------------------------------------------------------------------

def load_families(path: Path = FAMILIES_TSV) -> list[dict]:
    """The rows of pet_families.tsv, in file order: family (int), key, name, tree, entry (int), creature."""
    families = []
    header = None
    with open(path, newline="") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            cells = line.split("\t")
            if header is None:
                header = cells
                continue
            row = dict(zip(header, cells))
            row["family"] = int(row["family"])
            row["entry"] = int(row["entry"])
            families.append(row)
    return families


def select_families(families: list[dict], wanted: str | None) -> list[dict]:
    """Families by key, name or number (comma separated), in the order asked; all of them for None or ''."""
    if not wanted:
        return list(families)
    chosen = []
    for item in (w.strip().lower() for w in wanted.split(",")):
        if not item:
            continue
        match = next((f for f in families if item in (f["key"], f["name"].lower(), str(f["family"]))), None)
        if match is None:
            raise ValueError(f"'{item}' is not a family of {FAMILIES_TSV.name} (key, name or number)")
        if match not in chosen:
            chosen.append(match)
    return chosen


def parse_targets(text: str) -> list[int]:
    targets = []
    for item in text.split(","):
        item = item.strip()
        if not item:
            continue
        n = int(item)
        if not 1 <= n <= 10:
            raise ValueError(f"a target count must be 1-10, got {n}")
        if n not in targets:
            targets.append(n)
    if not targets:
        raise ValueError("no target count")
    return targets


# ---- run ------------------------------------------------------------------------------------------------------------

def plan_jobs(args, families: list[dict], targets: list[int], sweep: str) -> list[dict]:
    """One job per family and target count, every family's run at the first count before any at the next."""
    jobs = []
    for n in targets:
        for fam in families:
            env = {
                "DPSSIM_PET_FAMILY": fam["key"],
                "DPSSIM_BUFF_SET": args.buff_set,
                "DPSSIM_BATCH_TAG": f"{sweep}-{fam['key']}-t{n}",
                "DPSSIM_NO_HTML": "1",
            }
            if args.disable_spells:
                env["DPSSIM_DISABLE_SPELLS"] = args.disable_spells
            # run-sim.sh <profile> [durationSeconds] [level] [race] [iterations] [stepMs] [targets]
            cmd = [str(args.run_sim), args.profile, str(args.duration), str(args.level), str(args.race),
                   str(args.iterations), str(args.step), str(n)]
            jobs.append({"family": fam["family"], "key": fam["key"], "name": fam["name"], "tree": fam["tree"],
                         "entry": fam["entry"], "targets": n, "env": env, "cmd": cmd})
    return jobs


def shell_line(env: dict[str, str], cmd: list[str]) -> str:
    def quote(v: str) -> str:
        return v if all(c.isalnum() or c in "-_./:,=" for c in v) else "'" + v.replace("'", "'\\''") + "'"
    shown = list(cmd)
    if Path(shown[0]).is_relative_to(REPO_ROOT):
        shown[0] = str(Path(shown[0]).relative_to(REPO_ROOT))
    return " ".join(f"{k}={quote(v)}" for k, v in env.items()) + " " + " ".join(quote(c) for c in shown)


def run_job(job: dict, out_dir: Path) -> dict:
    log_path = out_dir / f"{job['key']}.t{job['targets']}.log"
    started = time.time()
    env = dict(os.environ)
    env.update(job["env"])
    with open(log_path, "w") as log_file:
        proc = subprocess.run(job["cmd"], env=env, cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=log_file, text=True)
    stdout = proc.stdout or ""
    with open(log_path, "a") as log_file:
        log_file.write("\n--- stdout ---\n" + stdout)
    report = next((line.strip() for line in reversed(stdout.splitlines()) if line.strip().endswith(".report.json")),
                  None)
    result = {k: v for k, v in job.items() if k != "cmd"}
    result.update({
        "shell": shell_line(job["env"], job["cmd"]),
        "exitCode": proc.returncode,
        "report": report,
        "log": str(log_path),
        "wallSeconds": round(time.time() - started, 1),
    })
    log(f"[{result['exitCode']}] {job['key']} t{job['targets']} in {result['wallSeconds']} s -> {report}")
    return result


def cmd_run(args) -> int:
    try:
        families = select_families(load_families(), args.families)
        targets = parse_targets(args.targets)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    args.jobs = max(1, min(args.jobs, MAX_JOBS))
    sweep = args.sweep or datetime.datetime.now().strftime("pf%Y%m%d-%H%M%S")
    out_dir = Path(args.out) if args.out else REPORTS_DIR / f"petsweep-{sweep}"
    jobs = plan_jobs(args, families, targets, sweep)

    if args.dry_run:
        print(f"# sweep {sweep}: {len(jobs)} run(s), at most {args.jobs} at once, from {REPO_ROOT}")
        for job in jobs:
            print(shell_line(job["env"], job["cmd"]))
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "sweep": sweep,
        "started": datetime.datetime.now().isoformat(timespec="seconds"),
        "settings": {"profile": args.profile, "race": args.race, "duration": args.duration,
                     "iterations": args.iterations, "step": args.step, "level": args.level, "jobs": args.jobs,
                     "buffSet": args.buff_set, "disableSpells": args.disable_spells or "", "targets": targets,
                     "image": os.environ.get("DPSSIM_IMAGE", "")},
        "runs": [],
    }
    manifest_path = out_dir / "manifest.json"
    log(f"sweep {sweep}: {len(jobs)} run(s), at most {args.jobs} at once; logs and manifest in {out_dir}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(run_job, job, out_dir) for job in jobs]
        for future in concurrent.futures.as_completed(futures):
            manifest["runs"].append(future.result())
            manifest_path.write_text(json.dumps(manifest, indent=1))
    manifest["finished"] = datetime.datetime.now().isoformat(timespec="seconds")
    manifest_path.write_text(json.dumps(manifest, indent=1))
    return write_index(manifest, out_dir, args.threshold)


# ---- index ----------------------------------------------------------------------------------------------------------

def report_numbers(report: dict) -> dict:
    """DPS (the aggregate's trimmed mean, as every sim page shows), the per-iteration spread, the pet's share of the
    damage and the config the report ran with."""
    summary = report.get("summary", {})
    total = float(summary.get("totalDamage") or 0.0)
    pet = sum(float(s.get("totalDamage") or 0.0) for s in report.get("spells", []) if s.get("isPet"))
    per_iteration = (report.get("aggregate", {}).get("perIteration", {}) or {}).get("dps") or []
    config = report.get("config", {})
    return {
        "dps": float(summary.get("dps") or 0.0),
        "dpsMin": min(per_iteration) if per_iteration else None,
        "dpsMax": max(per_iteration) if per_iteration else None,
        "iterations": report.get("aggregate", {}).get("iterations", 1),
        "petSharePct": 100.0 * pet / total if total > 0 else 0.0,
        "petCreatureEntry": config.get("petCreatureEntry"),
        "buffSet": config.get("buffSet"),
    }


def build_rows(manifest: dict, load=None) -> list[dict]:
    """One row per run of the manifest, with its numbers (or an error), sorted by family order then target count."""
    load = load or (lambda path: json.loads(Path(path).read_text()))
    rows = []
    for run in manifest.get("runs", []):
        row = {k: run.get(k) for k in ("family", "key", "name", "tree", "entry", "targets", "report", "log")}
        row["error"] = None
        if run.get("exitCode") != 0 or not run.get("report"):
            row["error"] = f"run failed (exit {run.get('exitCode')}), see {run.get('log')}"
        else:
            try:
                row.update(report_numbers(load(run["report"])))
            except (OSError, ValueError) as e:
                row["error"] = f"report unreadable: {e}"
        if row["error"] is None and row.get("petCreatureEntry") not in (None, row["entry"]):
            row["error"] = f"the report ran pet {row['petCreatureEntry']}, not {row['entry']}"
        rows.append(row)
    order = {f["key"]: i for i, f in enumerate(load_families())}
    rows.sort(key=lambda r: (order.get(r["key"], 999), r["targets"] or 0))
    return rows


def summarize(rows: list[dict], threshold: float = DEFAULT_THRESHOLD) -> dict:
    """Per family: DPS and pet share by target count, the difference from the median DPS of the swept families at
    each count, and `flagged` when the 1-target difference is above `threshold`."""
    good = [r for r in rows if not r.get("error")]
    counts = sorted({r["targets"] for r in good})
    medians = {n: statistics.median([r["dps"] for r in good if r["targets"] == n]) for n in counts}
    families: dict[str, dict] = {}
    for r in rows:
        fam = families.setdefault(r["key"], {"family": r["family"], "key": r["key"], "name": r["name"],
                                             "tree": r["tree"], "entry": r["entry"], "byTargets": {}, "errors": []})
        if r.get("error"):
            fam["errors"].append(f"t{r['targets']}: {r['error']}")
            continue
        fam["byTargets"][r["targets"]] = {
            "dps": r["dps"], "dpsMin": r.get("dpsMin"), "dpsMax": r.get("dpsMax"), "petSharePct": r["petSharePct"],
            "vsMedian": r["dps"] - medians[r["targets"]],
        }
    for fam in families.values():
        one = fam["byTargets"].get(1)
        fam["flagged"] = bool(one) and abs(one["vsMedian"]) > threshold
    ranked = sorted(families.values(), key=lambda f: -(f["byTargets"].get(1, {}).get("dps") or 0.0))
    single = [f["byTargets"][1]["dps"] for f in ranked if 1 in f["byTargets"]]
    return {
        "threshold": threshold,
        "targetCounts": counts,
        "medians": medians,
        "spread1t": (max(single) - min(single)) if single else None,
        "flagged": [f["key"] for f in ranked if f["flagged"]],
        "families": ranked,
    }


def fmt(v, digits: int = 0) -> str:
    if v is None:
        return "-"
    return f"{v:,.{digits}f}"


def summary_markdown(manifest: dict, summary: dict) -> str:
    s = manifest.get("settings", {})
    counts = summary["targetCounts"]
    lines = [
        f"# Pet family sweep {manifest.get('sweep')}",
        "",
        f"{s.get('profile')}, race {s.get('race')}, level {s.get('level')}, buff set {s.get('buffSet')}, "
        f"{s.get('duration')} s x {s.get('iterations')}, {s.get('step')} ms step"
        + (f", disabled spells {s['disableSpells']}" if s.get("disableSpells") else "")
        + (f", image {s['image']}" if s.get("image") else "") + ".",
        f"Started {manifest.get('started')}, finished {manifest.get('finished', '-')}.",
        "",
        "Median DPS: " + ", ".join(f"{n}t {fmt(summary['medians'][n], 1)}" for n in counts)
        + f". 1-target spread (best - worst): {fmt(summary['spread1t'], 1)}.",
        f"Flagged (1-target DPS more than {fmt(summary['threshold'])} from the median): "
        + (", ".join(summary["flagged"]) if summary["flagged"] else "none") + ".",
        "",
        "| Family | Tree | Entry | " + " | ".join(f"DPS {n}t" for n in counts)
        + " | Pet share 1t | vs median 1t | Flag |",
        "|---|---|---|" + "---|" * len(counts) + "---|---|---|",
    ]
    for fam in summary["families"]:
        bt = fam["byTargets"]
        one = bt.get(1, {})
        lines.append(
            f"| {fam['name']} | {fam['tree']} | {fam['entry']} | "
            + " | ".join(fmt(bt.get(n, {}).get("dps"), 1) for n in counts)
            + f" | {fmt(one.get('petSharePct'), 1)}% | {fmt(one.get('vsMedian'), 1)} | "
            + ("**over**" if fam["flagged"] else "") + " |")
    errors = [f"- {fam['name']} {e}" for fam in summary["families"] for e in fam["errors"]]
    if errors:
        lines += ["", "## Failed runs", ""] + errors
    return "\n".join(lines) + "\n"


CSV_FIELDS = ["family", "key", "name", "tree", "entry", "targets", "dps", "dpsMin", "dpsMax", "iterations",
              "petSharePct", "buffSet", "error", "report"]


def write_index(manifest: dict, out_dir: Path, threshold: float = DEFAULT_THRESHOLD) -> int:
    rows = build_rows(manifest)
    with open(out_dir / "sweep.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow({k: (round(r[k], 2) if isinstance(r.get(k), float) else r.get(k)) for k in CSV_FIELDS})
    summary = summarize(rows, threshold)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1))
    (out_dir / "summary.md").write_text(summary_markdown(manifest, summary))
    log(f"index: {out_dir / 'sweep.csv'}, {out_dir / 'summary.md'}")
    return 1 if any(r.get("error") for r in rows) else 0


def cmd_index(args) -> int:
    path = Path(args.path)
    manifest_path = path / "manifest.json" if path.is_dir() else path
    manifest = json.loads(manifest_path.read_text())
    return write_index(manifest, manifest_path.parent, args.threshold)


def cmd_list(_args) -> int:
    for f in load_families():
        print(f"{f['family']:>3}  {f['key']:<14} {f['name']:<14} {f['tree']:<9} {f['entry']:>6}  {f['creature']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="launch the sweep, then index it")
    run.add_argument("--out", help="output directory (default modules/mod-dpssim/reports/petsweep-<sweep>)")
    run.add_argument("--sweep", help="sweep id, part of every batch tag (default pf<timestamp>)")
    run.add_argument("--families", help="keys, names or numbers, comma separated (default all)")
    run.add_argument("--targets", default="1,3,5")
    run.add_argument("--profile", default="BmHunterSim")
    run.add_argument("--race", type=int, default=6, help="6 (Tauren), as the hunter profiles assume")
    run.add_argument("--duration", type=int, default=120)
    run.add_argument("--iterations", type=int, default=5)
    run.add_argument("--step", type=int, default=100)
    run.add_argument("--level", type=int, default=60)
    run.add_argument("--jobs", type=int, default=MAX_JOBS, help=f"parallel sims, at most {MAX_JOBS}")
    run.add_argument("--buff-set", default="full_raid", choices=["full_raid", "self_only"])
    run.add_argument("--disable-spells", help="DPSSIM_DISABLE_SPELLS for every run, e.g. 24604")
    run.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    run.add_argument("--dry-run", action="store_true", help="print the run-sim.sh lines and stop")
    run.add_argument("--run-sim", type=Path, default=RUN_SIM, help=argparse.SUPPRESS)
    run.set_defaults(func=cmd_run)

    index = sub.add_parser("index", help="(re)write the CSV and summary of a sweep")
    index.add_argument("path", help="the sweep's output directory or its manifest.json")
    index.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    index.set_defaults(func=cmd_index)

    lst = sub.add_parser("list", help="print the family table")
    lst.set_defaults(func=cmd_list)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
