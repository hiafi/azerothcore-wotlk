#!/usr/bin/env python3
"""
The mechanics sweep (dungeon mechanics STAGE-M4, handoff section 3.4 and decisions 7.3, 7.5, 7.7): every reworked spec
runs as the member under test of a group of real bots (1 tank, 1 healer, 3 DPS; the other slots are the fixed
reference profiles of SimMechanicsConfig.cpp) twice, once with the drill program rotation and once as the paired
baseline (program "none": same profile, group, gear, duration, iterations and seeds, nothing fires). Each run is one
tools/run-sim.sh call (a throwaway worldserver container off the live image), at most 6 at once (about 2.4 GB each once
running), and the two runs of a spec are queued next to each other so they run together.

    run    launches the matrix and writes <out>/manifest.json, one log per run, then the index
    index  pairs the runs of a manifest and writes <out>/index.json and <out>/index.md: per spec the failures of the
           member under test by type and mechanic, DPS with and without mechanics and the loss, the time it spent
           moving, escaping, holding and frozen, the lock leaks, the module's solve and route maxima, and the same
           for the reference members. Specs with a problem (see below), a leak, a missing strategy, a program error
           or a death come first.

Each build drill has its own pass bar (DRILL_BARS): gated tags with a per-spec-run limit, reported tags that are only
listed, a cross-spec limit, and for some drills limits on the reference members and on group failures. When every
drill of --programs has a bar, "Problems" lists only what breaks it; otherwise every failure of the member under test
is a problem. The index also flags a comma program longer than the fight and a program that started on a stale game
clock.

--programs: ';' separates programs and ',' chains entries inside one program. "a;b" alternates, iteration i runs
program i mod n, so a run of 2n iterations runs each program twice. "a,b" runs a and then b (4 s apart) inside every
iteration, so the second entry starts only after the first one's cycles and never runs if the fight ends first (run
warns at launch, the index flags it). For several build drills, sweep each one alone (`--programs sfk-hunt:4`), or
alternate them: `--programs 'deadmines-followups;sfk-hunt:4;scholomance-shapes:3' --iterations 6`.

Every run writes its reports through run-sim.sh with DPSSIM_BATCH_TAG=<sweep>-<spec>-<mech|base> (the report timestamp
has a 1 s resolution, so parallel runs need their own names) and DPSSIM_NO_HTML=1 (parallel runs would overwrite the
page); 5 iterations aggregate without trimming (aggregate_reports.py's mechanics merge).

--descriptor runs the boss descriptor slice (STAGE-M5, DESCRIPTOR_PROGRAMS) instead of the M4 rotation; the index then
adds a "Boss descriptor" table (kicks, dispels, purges, ignore list, target priority, break-out) per spec.

Usage:
    mechanics_sweep.py run [--out DIR] [--sweep ID] [--specs A,B] [--profiles P1,P2] [--duration 120]
                           [--iterations 5] [--step 100] [--level 60] [--group 5] [--jobs 6] [--programs TEXT]
                           [--descriptor] [--fallibility] [--no-baseline] [--dry-run] [--run-sim PATH]
    mechanics_sweep.py index <out-dir-or-manifest.json>
    mechanics_sweep.py list
"""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parents[2]
RUN_SIM = TOOLS_DIR / "run-sim.sh"
REPORTS_DIR = TOOLS_DIR.parent / "reports"

sys.path.insert(0, str(TOOLS_DIR))
from aggregate_reports import aggregate_mechanics  # noqa: E402

# Never more parallel sims than this (memory: about 2.4 GB each once running, dpssim-parallel-limit)
MAX_JOBS = 6

# The descriptor slice (STAGE-M5-HANDOFF section 3.7, `--descriptor`): mod-boss-mechanics' `descriptor` program
# (interrupts, dispels, purges, target priority, the ignore list and a break-out prison; one run is 64 s) twice in a
# row, so a 120 s iteration sees it start twice as the 300403 dummy's loop does. Not in the default rotation.
DESCRIPTOR_PROGRAMS = "descriptor:2"

# The M5 boss descriptor counters (MechanicBotCounters.h blocks "M5 WP-I / WP-P / WP-T"; FlattenCounters() in
# SimBossMechanics.cpp exports each under this name). The index sums them over the group (a name ending in "Max" takes
# the maximum); listedMissed is counted by one bot per group (the observer), so only its group sum means anything.
# A new counter: add its name here.
DESCRIPTOR_COUNTERS = [
    # interrupts (WP-I)
    "kicksLanded", "kicksWasted", "doNotKickKicks", "duplicateKicks", "overloadHolds", "listedMissed",
    "stockKicksDropped", "castStops",
    # dispels and purges (WP-P; dispelWrongAura M5 WP-F)
    "urgentDispels", "urgentLatencyMsMax", "deadlineDispels", "deadlineMisses", "listedDispels", "purges",
    "dispelWrongAura",
    # targets and the ignore list (WP-T)
    "focusSwitches", "msLowerTarget", "breakOutMsMax", "ignoredHits", "ignoredDamage", "petIgnoredHits",
    "petIgnoredDamage", "ignoreBlocks", "ignoreDrops", "petRecalls",
]


# ---- drill pass bars -------------------------------------------------------------------------------------------------
# Each build drill's own pass bar (Stratholme SWEEP-1 D1: the index used to flag every ledger hit, so a by-design
# "reported" tag read as a failure). Mirrored from mod-boss-mechanics src/MechanicDrill.h (kFollowupTags,
# kScholoBarTags, kStratBarTags, kDropBarTags and the tag comments) and the build reports that set each bar:
# deadmines-pilot STAGE-G8, shadowfang-keep-build STAGE-GD (sfk-hunt), scholomance-build STAGE-G, stratholme-build
# STAGE-G (followups), X2 (drops) and X3 (jump). test_mechanics_sweep.py checks the tags and cycle lengths against
# MechanicDrill.h when the module source is next to this repo.
#
# A bar is per spec run (every iteration of the run summed; the bars were set for 5 x 120 s). Keys are the ledger's
# "<Kind>/<tag>"; a bar names tags, which are unique within a drill.
#   gated        tag -> the most hits the member under test may take in a spec run
#   reported     tags listed for information, never a problem
#   cross_specs  no gated tag may hit the member under test on more than this many specs of the sweep (None: no rule)
#   references   tag -> the most hits each reference member may take in a run (they are the same bots in every spec)
#   group        tag -> the most group failures (MissedSoak) of that tag in a run
#   cycle_ms, default_cycles: the drill's Def, for the program length (Drill::RunLengthMs)
DRILL_BARS: dict[str, dict] = {
    "deadmines-followups": {
        "gated": {2: 1, 3: 1, 5: 1, 7: 1, 9: 1, 10: 1, 12: 1}, "reported": {1, 4, 6, 8, 11}, "cross_specs": 3,
        "references": {}, "group": {}, "cycle_ms": 30000, "default_cycles": 2,
    },
    "sfk-hunt": {
        # Zone/1 the 80% catch, Zone/3 the landing on anyone but the ringer; Zone/4 the ringer in the landing and
        # Zone/5 the 95% catch (a rate out of 20) are reported; the bell rung on at least 90% of hunts (MissedSoak 2)
        "gated": {1: 1, 3: 0}, "reported": {4, 5}, "cross_specs": None,
        "references": {1: 1, 3: 0}, "group": {2: 2}, "cycle_ms": 30000, "default_cycles": 2,
    },
    "scholomance-shapes": {
        "gated": {2: 1, 3: 1, 4: 1, 5: 1, 7: 1, 8: 1, 9: 1, 10: 1}, "reported": {1, 6}, "cross_specs": 3,
        "references": {}, "group": {}, "cycle_ms": 40000, "default_cycles": 3,
    },
    "stratholme-followups": {
        "gated": {2: 1, 4: 1, 6: 1, 8: 1, 9: 1}, "reported": {1, 3, 5, 7}, "cross_specs": 3,
        "references": {}, "group": {}, "cycle_ms": 40000, "default_cycles": 3,
    },
    "stratholme-drops": {
        # tag 1, the old webs: a carrier that steps in for the drop takes a tick by design
        "gated": {2: 1, 3: 1, 4: 1, 5: 1}, "reported": {1}, "cross_specs": 3,
        "references": {}, "group": {}, "cycle_ms": 30000, "default_cycles": 4,
    },
    "stratholme-jump": {
        # the bar is no Jump hit at all (1, 3, 4); Freeze Tag's RunOut (2) is reported
        "gated": {1: 0, 3: 0, 4: 0}, "reported": {2}, "cross_specs": None,
        "references": {}, "group": {}, "cycle_ms": 20000, "default_cycles": 6,
    },
}
# Drill::kProgramGapMs: the quiet time after each comma entry of a program
PROGRAM_GAP_MS = 4000


def program_entries(program: str) -> list[tuple[str, int | None]]:
    """The comma entries of one program text (Drill::ParseProgramText): (name, count or None)."""
    out = []
    for item in program.split(","):
        item = item.strip()
        if not item:
            continue
        name, _, count = item.partition(":")
        name = name.split(" ")[0]
        try:
            n = int(count) if count else None
        except ValueError:
            n = None
        out.append((name, n))
    return out


def split_programs(text: str | None) -> list[str]:
    """MECHSIM_PROGRAMS / --programs: ';' separates programs (iteration i runs program i mod n), ',' chains entries
    inside one program (they run one after another in the same iteration)."""
    return [p.strip() for p in (text or "").split(";") if p.strip()]


def program_length_ms(program: str) -> tuple[int, list[tuple[str, int]]] | None:
    """When the program's last entry ends and each entry's start (ms), for a program of barred drills only; None
    when an entry is not a drill this table knows (its length lives in mod-boss-mechanics)."""
    at = 0
    end = 0
    starts = []
    for name, n in program_entries(program):
        bar = DRILL_BARS.get(name)
        if bar is None:
            return None
        cycles = min(max(n or bar["default_cycles"], 1), 20)
        starts.append((name, at))
        end = at + bar["cycle_ms"] * cycles
        at = end + PROGRAM_GAP_MS
    return end, starts


def late_entries(program: str, duration_ms: int) -> list[str] | None:
    """The entries of a program that start at or after the fight's end (they never run), or None when unknown."""
    known = program_length_ms(program)
    if known is None:
        return None
    return [f"{name} at {start / 1000:.0f} s" for name, start in known[1] if start >= duration_ms]


def program_warnings(programs_text: str | None, duration_ms: int, iterations: int | None = None) -> list[str]:
    """Before a launch: each comma program that runs longer than the fight, with the entries that never start, and
    ';' programs that the iterations do not split evenly."""
    out = []
    programs = split_programs(programs_text)
    if iterations and len(programs) > 1 and iterations % len(programs):
        out.append(f"{len(programs)} ';' programs over {iterations} iterations: iteration i runs program i mod "
                   f"{len(programs)}, so they do not run equally often (use a multiple of {len(programs)})")
    for program in split_programs(programs_text):
        known = program_length_ms(program)
        if known is None or known[0] <= duration_ms:
            continue
        late = late_entries(program, duration_ms) or []
        out.append(f"program '{program}' runs {known[0] / 1000:.0f} s, longer than the {duration_ms / 1000:.0f} s "
                   "fight: its comma entries run one after another in each iteration"
                   + (f", so {', '.join(late)} never runs" if late else "")
                   + ". To alternate drills per iteration, separate them with ';' (iteration i runs program i mod n).")
    return out


def program_bar(programs_text: str | None) -> dict | None:
    """The bar of a sweep's programs: every drill of every program must have one, else None (the legacy rule: every
    failure of the member under test is a problem). Several drills: their tags share one ledger key space, so a tag is
    gated if any drill gates it (the strictest limit wins) and reported only if no drill gates it."""
    names = [name for p in split_programs(programs_text) for name, _ in program_entries(p)]
    if not names or any(n not in DRILL_BARS for n in names):
        return None
    out = {"drills": sorted(set(names)), "gated": {}, "reported": set(), "cross_specs": None, "references": {},
           "group": {}}
    for name in names:
        bar = DRILL_BARS[name]
        for field in ("gated", "references", "group"):
            for tag, limit in bar[field].items():
                out[field][tag] = min(limit, out[field].get(tag, limit))
        out["reported"] |= bar["reported"]
        if bar["cross_specs"] is not None:
            out["cross_specs"] = bar["cross_specs"] if out["cross_specs"] is None else min(out["cross_specs"],
                                                                                          bar["cross_specs"])
    out["reported"] -= set(out["gated"])
    return out


def key_tag(key: str) -> int | None:
    """The tag of a ledger key "<Kind>/<tag>"."""
    _, _, tag = key.rpartition("/")
    return int(tag) if tag.isdigit() else None


def counts_by_key(by_type: dict) -> dict[str, int]:
    """A failure map {type: {key: n}} summed per key over the types."""
    out: dict[str, int] = {}
    for by_key in (by_type or {}).values():
        for key, n in by_key.items():
            out[key] = out.get(key, 0) + int(n)
    return out


def judge_against_bar(bar: dict | None, by_type: dict, limits_field: str = "gated") -> tuple[list[str], dict, dict]:
    """(bar failures as text, gated hits {key: n}, reported hits {key: n}) of one failure map. A key the bar does not
    know is gated at 0 (a tag the drill does not use)."""
    counts = counts_by_key(by_type)
    if bar is None:
        return [], counts, {}
    failures, gated, reported = [], {}, {}
    limits = bar[limits_field]
    for key, n in sorted(counts.items()):
        tag = key_tag(key)
        if limits_field == "gated" and tag in bar["reported"]:
            reported[key] = n
            continue
        if tag not in limits:
            if limits_field != "gated":
                continue    # the reference and group bars only name what they gate
            failures.append(f"{key} x{n} (not a tag of {', '.join(bar['drills'])})")
            gated[key] = n
            continue
        gated[key] = n
        if n > limits[tag]:
            failures.append(f"{key} x{n} (bar {limits[tag]})")
    return failures, gated, reported


def merge_descriptor(lines: list[dict]) -> dict:
    """The descriptor counters of several member lines: summed, a name ending in "Max" as the maximum."""
    out = {name: 0 for name in DESCRIPTOR_COUNTERS}
    for line in lines:
        for name, value in (line.get("descriptor") or {}).items():
            out[name] = max(out.get(name, 0), value) if name.endswith("Max") else out.get(name, 0) + value
    return out


# Every reworked spec (all ten classes, Mage included: STAGE-M4-HANDOFF decision 7.1) and the profile that sims it.
# One profile per spec: the variants (pack, cover, breath, minion, ...) are talent or target setups of the same spec.
SPECS: list[tuple[str, str, str]] = [
    ("Warrior", "Arms", "ArmsWarriorSim"),
    ("Warrior", "Fury", "FuryWarriorSim"),
    ("Warrior", "Protection", "ProtWarriorTankSim"),
    ("Paladin", "Holy", "HolyPaladinHealSim"),
    ("Paladin", "Protection", "ProtPaladinTankSim"),
    ("Paladin", "Retribution", "RetPaladinSim"),
    ("Hunter", "Beast Mastery", "BmHunterSim"),
    ("Hunter", "Marksmanship", "MmHunterSim"),
    ("Hunter", "Survival", "SvHunterSim"),
    ("Rogue", "Assassination", "AssassinationRogueSim"),
    ("Rogue", "Combat", "CombatRogueSim"),
    ("Rogue", "Subtlety", "SubtletyRogueSim"),
    ("Priest", "Discipline", "DiscPriestHealSim"),
    ("Priest", "Holy", "HolyPriestHealSim"),
    ("Priest", "Shadow", "ShadowPriestSim"),
    ("Death Knight", "Blood", "BloodDkTankSim"),
    ("Death Knight", "Frost", "FrostDk2hSim"),
    ("Death Knight", "Unholy", "UnholyDkPlagueSim"),
    ("Shaman", "Elemental", "ShamanEleSim"),
    ("Shaman", "Enhancement", "EnhShamanSim"),
    ("Shaman", "Restoration", "RestoShamanHealSim"),
    ("Mage", "Arcane", "ArcaneMageSim"),
    ("Mage", "Fire", "FireMageSim"),
    ("Mage", "Frost", "FrostMageSim"),
    ("Warlock", "Affliction", "AfflictionWarlockSim"),
    ("Warlock", "Demonology", "DemonologyWarlockSim"),
    ("Warlock", "Destruction", "DestructionWarlockSim"),
    ("Druid", "Balance", "BalanceDruidSim"),
    ("Druid", "Feral", "FeralCatSim"),
    ("Druid", "Guardian", "BearTankSim"),
    ("Druid", "Restoration", "RestoDruidHealSim"),
]

print_lock = threading.Lock()


def log(message: str) -> None:
    with print_lock:
        print(message, file=sys.stderr, flush=True)


def select_specs(args) -> list[tuple[str, str, str]]:
    if args.profiles:
        known = {s[2]: s for s in SPECS}
        return [known.get(p.strip(), ("-", "-", p.strip())) for p in args.profiles.split(",") if p.strip()]
    specs = SPECS
    if args.specs:
        wanted = [w.strip().lower() for w in args.specs.split(",") if w.strip()]
        specs = [s for s in SPECS if any(w in f"{s[0]} {s[1]} {s[2]}".lower() for w in wanted)]
    return specs


def job_env(args, sweep: str, profile: str, kind: str) -> dict[str, str]:
    env = {
        "MECHSIM": "1",
        "MECHSIM_GROUP": str(args.group),
        "DPSSIM_BATCH_TAG": f"{sweep}-{profile}-{kind}",
        "DPSSIM_NO_HTML": "1",
    }
    if kind == "base":
        env["MECHSIM_BASELINE"] = "1"
    elif args.programs:
        env["MECHSIM_PROGRAMS"] = args.programs
    elif args.descriptor:
        env["MECHSIM_PROGRAMS"] = DESCRIPTOR_PROGRAMS
    if args.fallibility:
        env["MECHSIM_FALLIBILITY"] = "1"
    return env


def job_command(args, profile: str) -> list[str]:
    # run-sim.sh <profile> [durationSeconds] [level] [race] [iterations] [stepMs] [targets]; [race] is ignored by a
    # mechanics run (every member is Horde), 2 keeps the line readable
    return [str(args.run_sim), profile, str(args.duration), str(args.level), "2", str(args.iterations), str(args.step),
            "1"]


def shell_line(env: dict[str, str], cmd: list[str]) -> str:
    def quote(v: str) -> str:
        return v if all(c.isalnum() or c in "-_./:,=" for c in v) else "'" + v.replace("'", "'\\''") + "'"
    return " ".join(f"{k}={quote(v)}" for k, v in env.items()) + " " + " ".join(quote(c) for c in cmd)


def run_job(job: dict, out_dir: Path) -> dict:
    log_path = out_dir / f"{job['profile']}.{job['kind']}.log"
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
    result = dict(job)
    result.update({
        "exitCode": proc.returncode,
        "report": report,
        "log": str(log_path),
        "wallSeconds": round(time.time() - started, 1),
    })
    log(f"[{result['exitCode']}] {job['profile']} {job['kind']} in {result['wallSeconds']} s -> {report}")
    return result


def programs_label(args) -> str:
    if args.programs:
        return args.programs
    return f"descriptor slice ({DESCRIPTOR_PROGRAMS})" if args.descriptor else "default rotation"


def cmd_run(args) -> int:
    if args.programs and args.descriptor:
        print("error: --programs and --descriptor exclude each other", file=sys.stderr)
        return 1
    args.jobs = max(1, min(args.jobs, MAX_JOBS))
    sweep = args.sweep or datetime.datetime.now().strftime("ms%Y%m%d-%H%M%S")
    out_dir = Path(args.out) if args.out else REPORTS_DIR / f"mechsweep-{sweep}"
    specs = select_specs(args)
    if not specs:
        print("error: no spec matches", file=sys.stderr)
        return 1

    jobs: list[dict] = []
    for cls, spec, profile in specs:
        for kind in (("mech",) if args.no_baseline else ("mech", "base")):
            env = job_env(args, sweep, profile, kind)
            cmd = job_command(args, profile)
            jobs.append({"class": cls, "spec": spec, "profile": profile, "kind": kind, "env": env, "cmd": cmd,
                         "shell": shell_line(env, [str(Path(cmd[0]).relative_to(REPO_ROOT))
                                                   if Path(cmd[0]).is_relative_to(REPO_ROOT) else cmd[0]] + cmd[1:])})

    for warning in program_warnings(args.programs, args.duration * 1000, args.iterations):
        log(f"warning: {warning}")

    if args.dry_run:
        print(f"# sweep {sweep}: {len(jobs)} run(s), at most {args.jobs} at once, from {REPO_ROOT}")
        for job in jobs:
            print(job["shell"])
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "sweep": sweep,
        "started": datetime.datetime.now().isoformat(timespec="seconds"),
        "settings": {"duration": args.duration, "iterations": args.iterations, "step": args.step, "level": args.level,
                     "group": args.group, "jobs": args.jobs, "programs": programs_label(args),
                     "fallibility": args.fallibility},
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
    return cmd_index_path(manifest_path)


# ---- index ----------------------------------------------------------------------------------------------------------

def load_aggregate(path: str) -> dict:
    """The aggregated mechanics report of a run (run-sim.sh writes the aggregate for 2+ iterations, the bare report for
    one; the latter is merged here so both read the same)."""
    data = json.loads(Path(path).read_text())
    if data.get("kind") != "mechanics":
        raise ValueError(f"{path} is not a mechanics report")
    if "aggregate" not in data:
        data = aggregate_mechanics([data], [Path(path).name])
    return data


def mean_of(v) -> float:
    return v.get("mean", 0.0) if isinstance(v, dict) else float(v or 0)


def sum_of(v) -> float:
    if isinstance(v, dict):
        return v.get("sum", v.get("mean", 0.0))
    return float(v or 0)


# Cost targets at 10 bots (STAGE-M4-HANDOFF acceptance 4, decision 7.7): recorded for every group size, a target only
# from 10 bots up
SOLVE_US_TARGET = 2000
ROUTE_US_TARGET = 1000
HISTOGRAM_BUCKETS = 16


def bucket_upper(b: int) -> float:
    """MechanicCost.h's UsHistogram::BucketUpper: bucket 0 is [0, 2) us, bucket b [2^b, 2^(b+1)), the last open."""
    return float("inf") if b + 1 >= HISTOGRAM_BUCKETS else float(2 << b)


def histogram(cost: dict, name: str) -> dict | None:
    """count, mean, p50, p90, p99 and max (us) of a flattened UsHistogram (FlattenHistogram() in
    SimBossMechanics.cpp); quantiles are bucket upper bounds capped at the exact max, as UsHistogram::Quantile."""
    count = cost.get(name + "Count", 0)
    if not count:
        return None
    buckets = [cost.get(f"{name}B{b:02d}", 0) for b in range(HISTOGRAM_BUCKETS)]
    peak = cost.get(name + "Max", 0)

    def quantile(q: float) -> float:
        want = q * count
        seen = 0
        for b, n in enumerate(buckets):
            seen += n
            if seen > 0 and seen >= want:
                return min(bucket_upper(b), peak)
        return peak

    return {"count": count, "mean": cost.get(name + "Total", 0) / count, "p50": quantile(0.5),
            "p90": quantile(0.9), "p99": quantile(0.99), "max": peak}


def member_line(mech: dict, base: dict | None) -> dict:
    stats = mech.get("stats", {})
    counters = stats.get("counters", {})
    leaks = stats.get("leaks", {})
    mode = stats.get("modeMs", {})
    dps = mean_of(mech.get("dps"))
    base_dps = mean_of(base.get("dps")) if base else None
    loss = (1.0 - dps / base_dps) * 100.0 if base_dps else None
    per_iteration_loss = []
    if base:
        for m, b in zip(mech["dps"].get("perIteration", []), base["dps"].get("perIteration", [])):
            if b:
                per_iteration_loss.append((1.0 - m / b) * 100.0)
    # Healing output, same pairing (reports from before the heal recorder have no hps and read as 0)
    hps = mean_of(mech.get("hps"))
    base_hps = mean_of(base.get("hps")) if base else None
    hps_loss = (1.0 - hps / base_hps) * 100.0 if base_hps else None
    per_iteration_hps_loss = []
    if base:
        mech_hps = (mech.get("hps") or {}).get("perIteration", [])
        for m, b in zip(mech_hps, (base.get("hps") or {}).get("perIteration", [])):
            if b:
                per_iteration_hps_loss.append((1.0 - m / b) * 100.0)
    return {
        "index": mech["index"],
        "profile": mech["profile"],
        "role": mech["role"],
        "underTest": mech["underTest"],
        "failures": sum_of(mech.get("failureTotal")),
        "failuresByType": mech.get("failures", {}),
        "hits": sum_of(mech.get("hits")),
        "dps": dps,
        "baselineDps": base_dps,
        "dpsLossPct": loss,
        "dpsLossPctMin": min(per_iteration_loss) if per_iteration_loss else None,
        "dpsLossPctMax": max(per_iteration_loss) if per_iteration_loss else None,
        "hps": hps,
        "baselineHps": base_hps,
        "hpsLossPct": hps_loss,
        "hpsLossPctMin": min(per_iteration_hps_loss) if per_iteration_hps_loss else None,
        "hpsLossPctMax": max(per_iteration_hps_loss) if per_iteration_hps_loss else None,
        "healEffective": mean_of(mech.get("healEffective")),
        "healOverheal": mean_of(mech.get("healOverheal")),
        "healAbsorb": mean_of(mech.get("healAbsorb")),
        "movingMs": mean_of(mech.get("movingMs")),
        "baselineMovingMs": mean_of(base.get("movingMs")) if base else None,
        "escapeMs": mean_of(mode.get("escape")),
        "holdMs": mean_of(mode.get("hold")),
        "freezeMs": mean_of(mode.get("freeze")),
        "leaks": {"moves": leaks.get("moves", 0), "casts": leaks.get("casts", 0), "turns": leaks.get("turns", 0),
                  "spells": leaks.get("spells", [])},
        "solves": counters.get("solves", 0),
        "fallbacks": counters.get("outcomeFallback", 0),
        "solveUsMax": max(counters.get("solveUsMax", 0), stats.get("cost", {}).get("solveUsMax", 0)),
        # M5 C4: the allies' refresh before a solve, timed apart (older reports: solveUsMax included it, no refresh)
        "refreshUsMax": counters.get("refreshUsMax", 0),
        "solveRefreshes": counters.get("solveRefreshes", 0),
        "routeUsMax": max(counters.get("routeUsMax", 0), stats.get("cost", {}).get("routeUsMax", 0)),
        "costSummary": {name: histogram(stats.get("cost", {}), name)
                        for name in ("solveUs", "routeUs", "pathUs", "probeUs", "sightUs", "brainUs")},
        "pathCallsPerMechanic": {
            "mechanics": stats.get("cost", {}).get("mechanicsSeen", 0),
            "max": stats.get("cost", {}).get("mechanicPathCallsMax", 0),
            "mean": (stats.get("cost", {}).get("mechanicPathCallsTotal", 0)
                     / stats.get("cost", {}).get("mechanicsSeen", 1)) if stats.get("cost", {}).get("mechanicsSeen")
            else 0,
        },
        # Stratholme SWEEP-2 D6: Moves only the pocket pass found, and its oracle calls (older reports read as 0)
        "pocketMoves": counters.get("pocketMoves", 0),
        "pocketPathChecks": counters.get("pocketPathChecks", 0),
        "fallbackClear": counters.get("fallbackClear", 0),
        "fallbackHot": counters.get("fallbackHot", 0),
        "fallbackKept": counters.get("fallbackKept", 0),
        "regionRoutes": counters.get("regionRoutes", 0),
        "regionRoutesFound": counters.get("regionRoutesFound", 0),
        "msOutOfBand": counters.get("msOutOfBand", 0),
        "msOutOfBandTask": counters.get("msOutOfBandTask", 0),
        "pullBlocks": counters.get("pullBlocks", 0),
        "moverBreaks": counters.get("moverBreaks", 0),
        "pullsEnded": counters.get("pullsEnded", 0),
        "landingBlocks": counters.get("landingBlocks", 0),
        "motionEndStops": counters.get("motionEndStops", 0),
        "msChaseRefused": counters.get("msChaseRefused", 0),
        "chaseReleases": counters.get("chaseReleases", 0),
        "chaseSolves": counters.get("chaseSolves", 0),
        "msChaseStranded": counters.get("msChaseStranded", 0),
        "strandRoutes": counters.get("strandRoutes", 0),
        "escapeFacingBlocks": counters.get("escapeFacingBlocks", 0),
        "descriptorWakes": counters.get("descriptorWakes", 0),
        "forcedLeaks": [counters.get(k, 0) for k in ("forcedMoves", "forcedCasts", "forcedTurns")],
        # M5 boss descriptor (DESCRIPTOR_COUNTERS; reports from before M5 read as 0)
        "descriptor": {name: counters.get(name, 0) for name in DESCRIPTOR_COUNTERS},
        "strategyInstalled": mech.get("strategyInstalledAll", False),
        "deaths": mech.get("deaths", 0),
        "cost": stats.get("cost", {}),
    }


def spec_entry(run_mech: dict | None, run_base: dict | None, bar: dict | None = None) -> dict:
    """One spec's index entry. `bar` is program_bar() of the sweep (None: every failure of the member under test is a
    problem)."""
    any_run = run_mech or run_base
    entry = {"class": any_run["class"], "spec": any_run["spec"], "profile": any_run["profile"], "problems": []}
    mech = base = None
    for run, name in ((run_mech, "mech"), (run_base, "base")):
        if run is None:
            entry["problems"].append(f"no {name} run")
            continue
        if run.get("exitCode") != 0 or not run.get("report"):
            entry["problems"].append(f"{name} run failed (exit {run.get('exitCode')}, log {run.get('log')})")
            continue
        try:
            data = load_aggregate(run["report"])
        except (OSError, ValueError) as exc:
            entry["problems"].append(f"{name} report unreadable: {exc}")
            continue
        if name == "mech":
            mech = data
        else:
            base = data
    if mech is None:
        return entry

    base_members = {m["index"]: m for m in (base or {}).get("members", [])}
    if base and [m["profile"] for m in base["members"]] != [m["profile"] for m in mech["members"]]:
        entry["problems"].append("the baseline's group differs from the mechanics run's")
        base_members = {}
    lines = [member_line(m, base_members.get(m["index"])) for m in mech["members"]]
    entry["actor"] = next((line for line in lines if line["underTest"]), None)
    entry["references"] = [line for line in lines if not line["underTest"]]
    # The group's descriptor counters (every member, the one under test included); listedMissed is only whole here
    entry["descriptorGroup"] = merge_descriptor(lines)
    summary = mech.get("summary", {})
    entry["groupFailures"] = mech.get("groupFailures", {})
    entry["programErrors"] = summary.get("programErrors", [])
    base_summary = (base or {}).get("summary", {})
    entry["groupHps"] = mean_of(summary.get("groupHps"))
    entry["baselineGroupHps"] = mean_of(base_summary.get("groupHps")) if base else None
    entry["tankSaves"] = sum_of(summary.get("tankSaves"))
    entry["strayFailures"] = sum_of(summary.get("strayFailures"))
    entry["iterations"] = mech.get("aggregate", {}).get("iterations")
    entry["reports"] = {"mech": run_mech.get("report") if run_mech else None,
                        "base": run_base.get("report") if run_base else None}

    actor = entry["actor"] or {}
    bar_failures, entry["gatedHits"], entry["reportedHits"] = judge_against_bar(bar, actor.get("failuresByType", {}))
    entry["barFailures"] = bar_failures
    if bar is None:
        if actor.get("failures"):
            entry["problems"].append(f"{int(actor['failures'])} failure(s) of the member under test")
    else:
        if bar_failures:
            entry["problems"].append("bar: " + ", ".join(bar_failures))
        for ref in entry["references"]:
            ref_failures, _, _ = judge_against_bar(bar, ref.get("failuresByType", {}), "references")
            if ref_failures:
                entry["problems"].append(f"reference {ref['profile']} bar: " + ", ".join(ref_failures))
        group_failures, _, _ = judge_against_bar(bar, entry["groupFailures"], "group")
        if group_failures:
            entry["problems"].append("group bar: " + ", ".join(group_failures))
    # Stratholme SWEEP-1 D2: a comma program longer than the fight (its later entries never run)
    config = mech.get("config", {})
    duration_ms = config.get("durationMs") or 0
    lengths = config.get("programLengthsMs")
    late = config.get("programLateEntries")
    if lengths is None or late is None:     # reports from before the sim wrote them: this table's estimate
        lengths, late = [], []
        for program in config.get("programs", []):
            known = program_length_ms(program)
            lengths.append(known[0] if known else 0)
            late.extend(late_entries(program, duration_ms) or [])
    entry["programLengthsMs"] = lengths
    # A single entry longer than the fight is a choice (alexei, 156 s); a chain that runs past it cuts its last entry
    # short or never starts it
    chained_over = [length for program, length in zip(config.get("programs", []), lengths)
                    if duration_ms and length > duration_ms and len(program_entries(program)) > 1]
    if late or chained_over:
        names = ", ".join(late[:5]) + (f" and {len(late) - 5} more" if len(late) > 5 else "")
        entry["problems"].append(f"program longer than the fight ({max(lengths) / 1000:.0f} s of "
                                 f"{duration_ms / 1000:.0f} s)" + (": never runs " + names if late else
                                                                   ": its last entry is cut short"))
    # Stratholme SWEEP-1 D3: the program started on a stale game clock (its later entries run early)
    lag = summary.get("programStartLagMs")
    lag_values = lag.get("perIteration", []) if isinstance(lag, dict) else ([] if lag is None else [lag])
    if any(lag_values):
        entry["problems"].append(f"program start lag up to {max(lag_values, key=abs)} ms (stale game clock: its "
                                 "later entries run early)")
    if any(actor.get("leaks", {}).get(k) for k in ("moves", "casts", "turns")):
        entry["problems"].append("lock leaks")
    if not all(line["strategyInstalled"] for line in lines):
        entry["problems"].append("a member without the boss mechanics strategy")
    if entry["descriptorGroup"]["doNotKickKicks"]:
        entry["problems"].append(f"{entry['descriptorGroup']['doNotKickKicks']} do-not-kick kick(s)")
    if entry["programErrors"]:
        entry["problems"].append(f"{len(entry['programErrors'])} program error(s): {entry['programErrors'][0]}")
    if any(line["deaths"] for line in lines):
        entry["problems"].append("a death")
    if base is None:
        entry["problems"].append("no baseline: no DPS/HPS loss")
    return entry


def fmt(v, digits: int = 0) -> str:
    if v is None:
        return "-"
    return f"{v:,.{digits}f}"


def failures_text(by_type: dict) -> str:
    parts = []
    for ftype, by_key in sorted(by_type.items()):
        parts.append(ftype + " " + ", ".join(f"{k} x{int(n)}" for k, n in sorted(by_key.items())))
    return "; ".join(parts) if parts else "0"


def descriptor_table(manifest: dict, entries: list[dict]) -> list[str]:
    """index.md's boss descriptor table (M5): the group's counters per spec, the member under test's in brackets where
    they tell specs apart. Left out when no run has a descriptor counter and the sweep did not run the slice."""
    programs = str((manifest.get("settings") or {}).get("programs", ""))
    shown = "descriptor" in programs or any(any((e.get("descriptorGroup") or {}).values()) for e in entries)
    if not shown:
        return []
    lines = [
        "## Boss descriptor",
        "",
        "Group totals over every iteration (the member under test in brackets). Kicks: landed / wasted (an unlisted "
        "cast while a listed one was due) / missed (listed casts that completed). Do-not-kick kicks and duplicates "
        "should stay 0. Urgent dispels with the longest application-to-cure latency; deadline misses are deadline "
        "auras that ran out; ignored damage is the bots' own / their pets'; lower target is the time spent on "
        "something else while the pick lived; break-out max is the longest a prison held its player.",
        "",
        "| Spec | Kicks L / W / M | Do-not-kick | Dup | Holds | Urgent dispels, max latency | Deadline ok / miss | "
        "Listed dispels | Purges | Ignored dmg bot / pet | Focus switches | Lower target s | Break-out max s |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for e in entries:
        g = e.get("descriptorGroup")
        if g is None:
            continue
        a = (e.get("actor") or {}).get("descriptor") or {}

        def both(name: str, scale: float = 1.0, digits: int = 0) -> str:
            return f"{fmt(g.get(name, 0) / scale, digits)} ({fmt(a.get(name, 0) / scale, digits)})"

        lines.append(" | ".join([
            f"| {e['class']} {e['spec']}",
            f"{both('kicksLanded')} / {both('kicksWasted')} / {fmt(g['listedMissed'])}",
            fmt(g["doNotKickKicks"]), fmt(g["duplicateKicks"]), fmt(g["overloadHolds"]),
            f"{both('urgentDispels')}, {fmt(g['urgentLatencyMsMax'])} ms",
            f"{fmt(g['deadlineDispels'])} / {fmt(g['deadlineMisses'])}",
            both("listedDispels"), both("purges"),
            f"{fmt(g['ignoredDamage'])} / {fmt(g['petIgnoredDamage'])}",
            both("focusSwitches"), both("msLowerTarget", 1000.0, 1), fmt(g["breakOutMsMax"] / 1000.0, 1),
        ]) + " |")
    lines.append("")
    return lines


def cross_spec_problems(bar: dict | None, entries: list[dict]) -> list[str]:
    """The bar's sweep-wide rule: no gated tag hits the member under test on more than `cross_specs` specs."""
    if bar is None or bar["cross_specs"] is None:
        return []
    specs_by_key: dict[str, list[str]] = {}
    for e in entries:
        for key, n in (e.get("gatedHits") or {}).items():
            if n:
                specs_by_key.setdefault(key, []).append(f"{e['class']} {e['spec']}")
    return [f"{key} hits the member under test on {len(specs)} specs (bar {bar['cross_specs']}): "
            + ", ".join(specs) for key, specs in sorted(specs_by_key.items()) if len(specs) > bar["cross_specs"]]


def bar_json(bar: dict | None) -> dict | None:
    if bar is None:
        return None
    return {"drills": bar["drills"], "gated": {str(t): n for t, n in sorted(bar["gated"].items())},
            "reported": sorted(bar["reported"]), "crossSpecs": bar["cross_specs"],
            "references": {str(t): n for t, n in sorted(bar["references"].items())},
            "group": {str(t): n for t, n in sorted(bar["group"].items())}}


def bar_text(bar: dict | None, sweep_problems: list[str]) -> list[str]:
    """index.md's lines on the pass bar the problems were judged against."""
    if bar is None:
        return ["Bar: none known for these programs, so every failure of the member under test is a problem.", ""]

    def limits(d: dict) -> str:
        return ", ".join(f"{t} at most {n}" for t, n in sorted(d.items())) or "none"

    lines = [
        f"Bar ({', '.join(bar['drills'])}; per spec run, every iteration summed): gated tags {limits(bar['gated'])}; "
        f"reported only {', '.join(str(t) for t in sorted(bar['reported'])) or 'none'}"
        + (f"; no gated tag on more than {bar['cross_specs']} specs" if bar["cross_specs"] is not None else "")
        + (f"; each reference member: {limits(bar['references'])}" if bar["references"] else "")
        + (f"; group failures: {limits(bar['group'])}" if bar["group"] else "") + ".",
        "",
    ]
    if len(bar["drills"]) > 1:
        lines[0:0] = ["Several drills share the ledger's tags here: a tag is gated if any of them gates it.", ""]
    if sweep_problems:
        lines.extend(["Sweep problems:", ""] + [f"- {p}" for p in sweep_problems] + [""])
    return lines


def write_index(manifest: dict, out_dir: Path) -> tuple[Path, Path]:
    by_profile: dict[str, dict] = {}
    for run in manifest.get("runs", []):
        by_profile.setdefault(run["profile"], {})[run["kind"]] = run
    settings = manifest.get("settings") or {}
    bar = program_bar(settings.get("programs"))
    entries = [spec_entry(runs.get("mech"), runs.get("base"), bar) for runs in by_profile.values()]
    sweep_problems = cross_spec_problems(bar, entries)
    order = {s[2]: i for i, s in enumerate(SPECS)}
    entries.sort(key=lambda e: (0 if e["problems"] else 1, -(e.get("actor") or {}).get("failures", 0),
                                order.get(e["profile"], 999)))

    worst_solve = max((line["solveUsMax"] for e in entries for line in ([e["actor"]] if e.get("actor") else [])
                       + e.get("references", [])), default=0)
    worst_route = max((line["routeUsMax"] for e in entries for line in ([e["actor"]] if e.get("actor") else [])
                       + e.get("references", [])), default=0)
    group = (manifest.get("settings") or {}).get("group", 5)
    index = {
        "sweep": manifest.get("sweep"),
        "settings": manifest.get("settings"),
        "specs": len(entries),
        "specsWithProblems": sum(1 for e in entries if e["problems"]),
        "bar": bar_json(bar),
        "sweepProblems": sweep_problems,
        "solveUsMax": worst_solve,
        "routeUsMax": worst_route,
        "costTargets": {
            "solveUsTarget": SOLVE_US_TARGET,
            "routeUsTarget": ROUTE_US_TARGET,
            "applies": group >= 10,
            "solveOk": worst_solve < SOLVE_US_TARGET,
            "routeOk": worst_route < ROUTE_US_TARGET,
        },
        "entries": entries,
    }
    json_path = out_dir / "index.json"
    json_path.write_text(json.dumps(index, indent=1))

    lines = [
        f"# Mechanics sweep {manifest.get('sweep')}",
        "",
        f"Settings: {json.dumps(manifest.get('settings'))}. {index['specs']} spec(s), "
        f"{index['specsWithProblems']} with problems (listed first). Worst solve {worst_solve} µs (target "
        f"{SOLVE_US_TARGET}), worst route {worst_route} µs (target {ROUTE_US_TARGET}) over every member; the targets "
        f"hold from 10 bots up, this group has {group}.",
        "",
    ]
    lines.extend(bar_text(bar, sweep_problems))
    lines.extend([
        "| Spec | Profile | Problems | Failures (under test) | Reported (not gated) | Output | Mech | Base | "
        "Loss % (min-max) | Group HPS mech / base | Moving s (base) | Escape / hold / freeze s | Leaks m/c/t | "
        "Solve / route max µs | Reference failures |",
        "| --- | --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ])
    for e in entries:
        a = e.get("actor") or {}
        refs = "; ".join(f"{r['profile']} {int(r['failures'])}" for r in e.get("references", []) if r["failures"])
        # A healer under test is judged on healing output (HPS), everyone else on DPS
        pre = "hps" if a.get("role") == "healer" else "dps"
        loss = (f"{fmt(a.get(pre + 'LossPct'), 1)} ({fmt(a.get(pre + 'LossPctMin'), 1)} to "
                f"{fmt(a.get(pre + 'LossPctMax'), 1)})") if a else "-"
        lk = a.get("leaks", {})
        lines.append(" | ".join([
            f"| {e['class']} {e['spec']}", e["profile"], "; ".join(e["problems"]) or "clean",
            failures_text(a.get("failuresByType", {})) if a else "-",
            ", ".join(f"{k} x{n}" for k, n in sorted((e.get("reportedHits") or {}).items())) or "-",
            pre.upper() if a else "-", fmt(a.get(pre)), fmt(a.get("baselineHps" if pre == "hps" else "baselineDps")),
            loss, f"{fmt(e.get('groupHps'))} / {fmt(e.get('baselineGroupHps'))}",
            f"{fmt((a.get('movingMs') or 0) / 1000, 1)} ({fmt((a.get('baselineMovingMs') or 0) / 1000, 1)})"
            if a else "-",
            f"{fmt(a.get('escapeMs', 0) / 1000, 1)} / {fmt(a.get('holdMs', 0) / 1000, 1)} / "
            f"{fmt(a.get('freezeMs', 0) / 1000, 1)}" if a else "-",
            f"{lk.get('moves', 0)}/{lk.get('casts', 0)}/{lk.get('turns', 0)}" if a else "-",
            f"{a.get('solveUsMax', 0)} / {a.get('routeUsMax', 0)}" if a else "-",
            refs or "0",
        ]) + " |")
    lines.append("")
    lines.extend(descriptor_table(manifest, entries))
    md_path = out_dir / "index.md"
    md_path.write_text("\n".join(lines))
    return json_path, md_path


def cmd_index_path(path: Path) -> int:
    manifest_path = path / "manifest.json" if path.is_dir() else path
    manifest = json.loads(manifest_path.read_text())
    json_path, md_path = write_index(manifest, manifest_path.parent)
    print(json_path)
    print(md_path)
    return 0


def cmd_index(args) -> int:
    return cmd_index_path(Path(args.path))


def cmd_list(_args) -> int:
    for cls, spec, profile in SPECS:
        print(f"{cls:13} {spec:14} {profile}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="launch the sweep")
    run.add_argument("--out", help="output directory (default modules/mod-dpssim/reports/mechsweep-<sweep>)")
    run.add_argument("--sweep", help="sweep id used in the batch tags (default ms<timestamp>)")
    run.add_argument("--specs", help="comma-separated filters on '<class> <spec> <profile>' (case-insensitive)")
    run.add_argument("--profiles", help="comma-separated profiles instead of the reworked-spec matrix")
    run.add_argument("--duration", type=int, default=120)
    run.add_argument("--iterations", type=int, default=5)
    run.add_argument("--step", type=int, default=100)
    run.add_argument("--level", type=int, default=60)
    run.add_argument("--group", type=int, default=5)
    run.add_argument("--jobs", type=int, default=MAX_JOBS, help=f"parallel sims, at most {MAX_JOBS}")
    run.add_argument("--programs",
                     help="MECHSIM_PROGRAMS for the mechanics runs (default: the rotation). ';' alternates programs "
                          "per iteration; ',' chains entries one after another inside every iteration (a chain "
                          "longer than --duration never reaches its later entries)")
    run.add_argument("--descriptor", action="store_true",
                     help=f"run the boss descriptor slice ({DESCRIPTOR_PROGRAMS}) instead of the rotation")
    run.add_argument("--fallibility", action="store_true", help="BossMechanics.Bots.Fallibility.Enable = 1")
    run.add_argument("--no-baseline", action="store_true", help="skip the paired baseline runs (no DPS loss)")
    run.add_argument("--dry-run", action="store_true", help="print the run-sim.sh lines and exit")
    run.add_argument("--run-sim", type=Path, default=RUN_SIM, help=argparse.SUPPRESS)
    run.set_defaults(func=cmd_run)

    index = sub.add_parser("index", help="pair the runs of a sweep and write index.json / index.md")
    index.add_argument("path", help="the sweep's output directory or its manifest.json")
    index.set_defaults(func=cmd_index)

    lister = sub.add_parser("list", help="print the reworked-spec matrix")
    lister.set_defaults(func=cmd_list)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
