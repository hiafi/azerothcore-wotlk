#!/usr/bin/env python3
"""
Computes per-point DPS stat weights for a mod-dpssim profile (2026-09-13 request).

Runs a full baseline batch (the profile unmodified, using run-sim.sh's own default iteration
count - there is no separate "iterations" config key, that default *is* the config, see
run-sim.sh's own doc comment), then for each stat this profile enables via a "Test<Stat> = true"
flag (SimProfile.h's Profile::StatWeightTests), runs a second batch with that one stat bumped by a
fixed amount - 14/22/46 points at level 60/70/80 respectively, the exact brackets given with this
request; an off-bracket level falls back the same way SimTarget::EntryForLevel() does - at half the
baseline's iteration count (also as requested). weight = (variantAvgDps - baselineAvgDps) / delta:
roughly how much DPS one point of that stat is worth *for this profile as currently built*, not a
universal constant - diminishing/increasing returns are real, so a Haste weight computed on a
low-haste profile doesn't necessarily hold once Haste is stacked much higher. Also still inherits
every run-to-run noise source averaging works around (docs/bugs-and-fixes.md) - the baseline batch
and each variant batch are each their own independent average, not a single shared seed pair, so
some of a small weight's magnitude can be noise rather than a real effect; a weight much smaller
than the spread between baseline runs (see the report's own DPS range) shouldn't be trusted as
precise.

Writes the results into the baseline's own report JSON as a new "statWeights" object and rebakes
SimProfileReport.html (via build_report_html.py), so the weights show up alongside that run's
normal breakdown rather than as a separate, disconnected report.

Usage:
    stat_weights.py <profile> [durationSeconds] [level] [race] [baselineIterations] [statDelta] [targets]

<profile>/[durationSeconds]/[level]/[race] mean exactly what they mean to run-sim.sh (see its own
doc comment) - this script calls that one for every batch (baseline and each variant), it does not
talk to Docker/the DB itself. [baselineIterations] overrides run-sim.sh's own default for the
baseline batch only (each variant is still exactly half of whatever the baseline actually used,
rounded down, minimum 1) - omit it to use "the iterations from the config" as originally asked for;
pass a small number (e.g. 2) for a fast smoke test of this whole pipeline without waiting through a
full-size batch.

[targets] is run-sim.sh's [targets] (number of stacked dummies, default 1); every run in the batch, baseline and
variants alike, uses the same count. Pass "-" for [baselineIterations] or [statDelta] to keep its default while
setting [targets].

[statDelta] overrides the level-bracket delta (14/22/46) with an arbitrary flat amount, applied to
every tested stat identically - added 2026-09-13 for a sign/plausibility sanity check: with the
normal small delta, a real effect's DPS swing can be the same order of magnitude as run-to-run
noise, so a weight's *sign* isn't fully trustworthy on its own. Passing a deliberately huge delta
(e.g. 280, a ~20x bump) should move DPS by roughly 20x as much for a stat with a real, consistent
effect - if a stat instead reads flat or flips sign at this scale, that points at a bug in how this
sim applies that particular stat rather than a real, small, noise-dominated weight. Purely a
diagnostic override - the resulting "weight" (deltaDps / statDelta) is not a valid per-point number
once statDelta stops reflecting the level's real rating-to-percent conversion (this is most visible
for ProcChanceRating/VersatilityRating, which don't scale 1:1 with the other ratings at all - see
SimActor.cpp's own stat-application code for each rating's real conversion).

Environment (bot-stat-weights, 2026-11-10):
    STATWEIGHTS_STATS               comma-separated conf keys to test, replacing the profile's Test<Stat> flags (and its
                                    StatWeightsEnabled = false); HitRating, ExpertiseRating and ArmorPenetrationRating
                                    are accepted too.
    STATWEIGHTS_DELTAS              per-stat delta overrides, "MasteryRating=50,VersatilityRating=50".
    STATWEIGHTS_BASELINE_BATCHES    run the baseline this many times and pool every iteration (default 1).
    STATWEIGHTS_VARIANT_ITERATIONS  iterations per variant batch (default: half the baseline's).
    STATWEIGHTS_OUT                 also write the result object to this JSON file.
Heal reports are weighed by "hps" (effective healing plus absorbs over the whole fight; mana and OOM ride along) and
tank reports by "dps", with "ehSeconds" (max health / net damage taken per second), "netDtps" and "health" per point
beside it. Every weight carries its standard error (pooled iterations, baseline and variant SE combined).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "modules" / "mod-dpssim" / "tools"
# STATWEIGHTS_RUN_SIM points at a wrapper with run-sim.sh's interface instead (e.g. one that waits for a free sim slot)
RUN_SIM_SH = Path(os.environ.get("STATWEIGHTS_RUN_SIM") or TOOLS_DIR / "run-sim.sh")
BUILD_REPORT_HTML = TOOLS_DIR / "build_report_html.py"
PROFILES_DIR = REPO_ROOT / "modules" / "mod-dpssim" / "conf" / "profiles"

# NOT a system tempdir (tempfile's own default, e.g. /tmp) - run-sim.sh only bind-mounts
# $REPO_ROOT/modules into the sim container (and only translates a profile's host path to a
# container path by stripping a "$REPO_ROOT/modules/" prefix - see its own PROFILE_CONTAINER_PATH
# line), so a variant profile living outside modules/ is both unreachable from inside the container
# and silently mistranslated into a broken path on the host side too. Gitignored (see .gitignore).
SCRATCH_PARENT = PROFILES_DIR / ".stat-weights-scratch"

# conf key -> "Test<key>" flag name - the 13 stats named in the request, matching SimProfile.cpp's
# STAT_KEYS/RATING_KEYS/TEST_FLAG_KEYS tables exactly (including the note there about why
# Hit/Expertise/ArmorPen aren't in this list even though they're valid RATING_KEYS).
STAT_TEST_KEYS = [
    ("Strength", "TestStrength"),
    ("Agility", "TestAgility"),
    ("Stamina", "TestStamina"),
    ("Intellect", "TestIntellect"),
    ("Spirit", "TestSpirit"),
    ("SpellPower", "TestSpellPower"),
    ("AttackPower", "TestAttackPower"),
    ("CritRating", "TestCritRating"),
    ("HasteRating", "TestHasteRating"),
    ("MasteryRating", "TestMasteryRating"),
    ("VersatilityRating", "TestVersatilityRating"),
    ("CooldownHasteRating", "TestCooldownHasteRating"),
    ("ProcChanceRating", "TestProcChanceRating"),
]

# Exactly the three brackets given with the request. Off-bracket levels fall back the same way
# SimTarget::EntryForLevel() does (SimTarget.cpp): floor to 60 below it, otherwise round up to the
# next bracket - not "nearest", despite what that function's own doc comment claims; mirrored here
# from its actual `if`-chain, not its comment.
STAT_DELTA_BY_BRACKET = {60: 14, 70: 22, 80: 46}


def resolve_delta(level: int) -> int:
    if level in STAT_DELTA_BY_BRACKET:
        return STAT_DELTA_BY_BRACKET[level]
    bracket = 60 if level < 60 else (70 if level < 70 else 80)
    print(f"stat_weights.py: no stat delta defined for level {level} (only 60/70/80 are) - "
          f"falling back to the level {bracket} delta.", file=sys.stderr)
    return STAT_DELTA_BY_BRACKET[bracket]


def resolve_profile_path(profile_arg: str) -> Path:
    direct = Path(profile_arg)
    if direct.is_file():
        return direct
    named = PROFILES_DIR / f"{profile_arg}.conf"
    if named.is_file():
        return named
    print(f"stat_weights.py: no such profile file '{profile_arg}' and no {named} either.", file=sys.stderr)
    sys.exit(1)


# A line-oriented parse, not a full SimProfile.cpp reimplementation - only needs "what's the
# current value of each of the 13 keys" and "which Test<Stat> flags are true", both trivial
# key=value lookups. Keeps the original lines around too (see bump_profile()) so a scratch variant
# preserves the rest of the file (comments, ordering, every other key) untouched.
def parse_profile(path: Path) -> tuple[list[str], dict[str, str]]:
    lines = path.read_text().splitlines(keepends=True)
    values: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        values[key.strip()] = value.strip()
    return lines, values


def format_number(n: float) -> str:
    return str(int(n)) if float(n).is_integer() else str(n)


# Writes a scratch copy of `lines` with `key`'s value increased by `delta`, or a new "key = delta"
# line appended if `key` wasn't present at all - an absent key means this profile's baseline for it
# is 0, the same "absent = untouched default" convention SimProfile.cpp itself uses for
# CombatRatings/Stats.
def bump_profile(lines: list[str], values: dict[str, str], key: str, delta: int, out_path: Path) -> None:
    current = float(values.get(key, "0") or "0")
    new_value = format_number(current + delta)

    new_lines = []
    replaced = False
    for line in lines:
        stripped = line.strip()
        if not replaced and stripped and not stripped.startswith("#") and "=" in stripped:
            k = stripped.split("=", 1)[0].strip()
            if k == key:
                new_lines.append(f"{key} = {new_value}\n")
                replaced = True
                continue
        new_lines.append(line)
    if not replaced:
        new_lines.append(f"\n{key} = {new_value}\n")

    out_path.write_text("".join(new_lines))


# Stats the STATWEIGHTS_STATS list may name on top of STAT_TEST_KEYS: the ratings SimProfile.cpp's RATING_KEYS accepts
# but that have no "Test<Stat>" flag (Hit and Expertise are gone in PvE on this server, docs/Systems.md section 2, so a
# run of them is a check that they read zero).
EXTRA_STAT_KEYS = ["HitRating", "ExpertiseRating", "ArmorPenetrationRating"]


def env_int(name: str) -> int | None:
    value = os.environ.get(name, "").strip()
    return int(value) if value else None


# Runs one run-sim.sh batch and returns (reportJsonPath, htmlPath or None, parsedReport). `iterations=None` omits the
# argument entirely so run-sim.sh's own default applies - see this module's doc comment for why the baseline call is
# made this way. Lets run-sim.sh's own stderr (progress messages) stream straight through rather than capturing it, so
# a long stat-weight pass still shows live progress; only stdout (the final path lines) is captured. With
# DPSSIM_NO_HTML=1 run-sim.sh prints the report path alone.
def run_sim(profile_path: Path, duration: int, level: int, race: int, iterations: int | None,
            targets: int = 1) -> tuple[Path, Path | None, dict]:
    args = [str(RUN_SIM_SH), str(profile_path), str(duration), str(level), str(race)]
    if iterations is not None:
        args.append(str(iterations))
    elif targets != 1:
        args.append("10")  # run-sim.sh's default iteration count; [targets] is positional after [iterations]/[stepMs]
    if targets != 1:
        args += ["100", str(targets)]  # stepMs at run-sim.sh's default, then targets
    elif iterations is not None:
        args.append("100")
    result = subprocess.run(args, stdout=subprocess.PIPE, text=True, check=True)
    out_lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    report_lines = [line for line in out_lines if line.endswith(".report.json")]
    if not report_lines:
        raise RuntimeError(f"run-sim.sh produced unexpected stdout: {result.stdout!r}")
    report_path = Path(report_lines[-1])
    html_path = Path(out_lines[-1]) if out_lines[-1].endswith(".html") else None
    return report_path, html_path, json.loads(report_path.read_text())


def iterations_used(report: dict) -> int:
    agg = report.get("aggregate")
    return agg["iterations"] if agg else 1


# The metrics read from one iteration's report, by report kind:
#   DPS:  dps
#   heal: hps (effective healing plus absorbs over the whole fight; the weight's metric), hpsBeforeOom, oomAtMs (None =
#         never ran out), manaSpent, overhealPct
#   tank: dps, dtps, netDtps, health (max health, the sheet one second in; the dps scenario refills it every step),
#         ehSeconds = health / netDtps (the defensive metric: seconds the tank lasts on its own at this damage intake),
#         ttdMs (survive scenario only)
def iteration_metrics(report: dict) -> dict:
    kind = report.get("kind", "dps")
    summary = report["summary"]
    if kind == "heal":
        return {
            "hps": summary.get("hps"), "hpsBeforeOom": summary.get("hpsBeforeOom"), "oomAtMs": summary.get("oomAtMs"),
            "manaSpent": summary.get("manaSpent"), "overhealPct": summary.get("overhealPct"),
        }
    out = {"dps": summary.get("dps")}
    if kind == "tank":
        tank = report["tank"]
        tsum = tank["summary"]
        health = tank["actor"]["afterFirstSecond"]["health"]
        net = tsum.get("netDtps") or 0.0
        out.update({
            "dtps": tsum.get("dtps"), "netDtps": net, "health": health,
            "ehSeconds": (health / net) if net > 0 else None, "ttdMs": tsum.get("ttdMs"),
            "dpsAlive": tsum.get("dpsAlive"),
        })
    return out


# Every iteration's metrics of one batch, read from the batch's own iteration files (aggregate.sourceReports) so several
# batches pool into one sample (mean and standard error over every iteration, no trimming).
def batch_iterations(report_path: Path, report: dict) -> list[dict]:
    agg = report.get("aggregate")
    if not agg:
        return [iteration_metrics(report)]
    return [iteration_metrics(json.loads((report_path.parent / name).read_text())) for name in agg["sourceReports"]]


def pooled(samples: list[dict], key: str) -> dict:
    values = [s[key] for s in samples if s.get(key) is not None]
    if not values:
        return {"mean": None, "se": None, "sd": None, "n": 0, "min": None, "max": None}
    n = len(values)
    mean = sum(values) / n
    sd = (sum((v - mean) ** 2 for v in values) / (n - 1)) ** 0.5 if n > 1 else 0.0
    return {"mean": mean, "se": sd / n ** 0.5, "sd": sd, "n": n, "min": min(values), "max": max(values)}


def metric_keys(kind: str) -> list[str]:
    if kind == "heal":
        return ["hps", "hpsBeforeOom", "oomAtMs", "manaSpent", "overhealPct"]
    if kind == "tank":
        return ["dps", "dtps", "netDtps", "health", "ehSeconds", "ttdMs", "dpsAlive"]
    return ["dps"]


def headline_key(kind: str) -> str:
    return "hps" if kind == "heal" else "dps"


def summarize(samples: list[dict], kind: str) -> dict:
    return {key: pooled(samples, key) for key in metric_keys(kind)}


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 1

    profile_arg = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 180
    level = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    race = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    baseline_iterations_override = int(sys.argv[5]) if len(sys.argv) > 5 and sys.argv[5] != "-" else None
    stat_delta_override = int(sys.argv[6]) if len(sys.argv) > 6 and sys.argv[6] != "-" else None
    targets = int(sys.argv[7]) if len(sys.argv) > 7 else 1

    profile_path = resolve_profile_path(profile_arg)
    lines, values = parse_profile(profile_path)
    delta = stat_delta_override if stat_delta_override is not None else resolve_delta(level)
    base_delta = delta
    if stat_delta_override is not None:
        print(f"stat_weights.py: statDelta override in effect - using +{delta} for every tested "
              "stat instead of the level-bracket default. Every stat is still a rating/stat point, so the weight "
              "stays per point of what an item carries; a large delta trades linearity for signal.", file=sys.stderr)

    # Master switch - see SimProfile.h's Profile::StatWeightsEnabled doc comment. Checked before
    # anything else runs (including the baseline batch) since it means "don't run stat weights
    # against this profile at all," not "run the baseline but skip variants."
    # An explicit STATWEIGHTS_STATS list overrides it: most profiles set it to false only because this tool was
    # DPS-only and flag-driven when they were written.
    explicit_stats = os.environ.get("STATWEIGHTS_STATS", "").strip()
    if values.get("StatWeightsEnabled", "true").lower() == "false" and not explicit_stats:
        print(f"stat_weights.py: StatWeightsEnabled = false in {profile_path} - stat weights are "
              "turned off for this profile, not running anything.", file=sys.stderr)
        return 1

    # STATWEIGHTS_STATS (comma-separated conf keys) replaces the profile's Test<Stat> flags, so a profile without them
    # (every heal and tank profile, most melee ones) can be weighed without editing it.
    stats_env = os.environ.get("STATWEIGHTS_STATS", "").strip()
    known = [key for key, _flag in STAT_TEST_KEYS] + EXTRA_STAT_KEYS
    if stats_env:
        tested_stats = [s.strip() for s in stats_env.split(",") if s.strip()]
        unknown = [s for s in tested_stats if s not in known]
        if unknown:
            print(f"stat_weights.py: STATWEIGHTS_STATS names unknown stat(s) {unknown}; known: {known}",
                  file=sys.stderr)
            return 1
    else:
        tested_stats = [key for key, flag in STAT_TEST_KEYS if values.get(flag, "false").lower() == "true"]
    if not tested_stats:
        print(f"stat_weights.py: no 'Test<Stat> = true' flags found in {profile_path} and no STATWEIGHTS_STATS - "
              "nothing to weigh. See SimProfile.h's Profile::StatWeightTests doc comment.", file=sys.stderr)
        return 1

    # STATWEIGHTS_BASELINE_BATCHES runs the baseline that many times and pools every iteration (the baseline is shared
    # by every variant, so its noise lands on every weight). STATWEIGHTS_VARIANT_ITERATIONS overrides the "half the
    # baseline" variant size.
    baseline_batches = env_int("STATWEIGHTS_BASELINE_BATCHES") or 1
    variant_iterations_override = env_int("STATWEIGHTS_VARIANT_ITERATIONS")

    print(f"stat_weights.py: baseline ({baseline_batches} batch(es), {profile_path.name}, {duration}s, "
          f"level {level})...", file=sys.stderr)
    baseline_samples: list[dict] = []
    baseline_paths: list[str] = []
    baseline_report_path = baseline_html_path = None
    baseline_report: dict = {}
    for _ in range(baseline_batches):
        path, html, report = run_sim(profile_path, duration, level, race, baseline_iterations_override, targets)
        if baseline_report_path is None:
            baseline_report_path, baseline_html_path, baseline_report = path, html, report
        baseline_paths.append(str(path))
        baseline_samples += batch_iterations(path, report)
    kind = baseline_report.get("kind", "dps")
    head = headline_key(kind)
    baseline = summarize(baseline_samples, kind)
    baseline_value = baseline[head]["mean"]
    n = iterations_used(baseline_report)
    variant_iterations = variant_iterations_override or max(1, n // 2)
    print(f"stat_weights.py: baseline {head} = {baseline_value:.2f} +- {baseline[head]['se']:.2f} (SE, "
          f"{baseline[head]['n']} run(s)). Testing {len(tested_stats)} stat(s) at +{delta}, {variant_iterations} "
          "run(s) each.", file=sys.stderr)

    # STATWEIGHTS_DELTAS ("MasteryRating=140,VersatilityRating=280") overrides the delta per stat: this server's rated
    # stats convert at different rates (level 60, gtcombatratings_dbc: Crit and Mastery 14 rating per 1%, Versatility
    # 28, Cooldown Haste and Proc Chance 7), so one flat delta is a 10% step for one stat and a 5% or 20% step for
    # another.
    per_stat_delta = {}
    for part in os.environ.get("STATWEIGHTS_DELTAS", "").split(","):
        if "=" in part:
            k, _, v = part.partition("=")
            per_stat_delta[k.strip()] = int(v)

    weights = []
    SCRATCH_PARENT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="run.", dir=SCRATCH_PARENT) as scratch_dir_name:
        scratch_dir = Path(scratch_dir_name)
        for key in tested_stats:
            delta = per_stat_delta.get(key, base_delta)
            variant_path = scratch_dir / f"{profile_path.stem}.{key}.conf"
            bump_profile(lines, values, key, delta, variant_path)
            print(f"stat_weights.py: testing {key} (+{delta})...", file=sys.stderr)
            report_path, _html_path, variant_report = run_sim(
                variant_path, duration, level, race, variant_iterations, targets)
            variant = summarize(batch_iterations(report_path, variant_report), kind)
            variant_value = variant[head]["mean"]
            delta_value = variant_value - baseline_value
            se = (variant[head]["se"] ** 2 + baseline[head]["se"] ** 2) ** 0.5
            entry = {
                "stat": key, "delta": delta, "metric": head, "baselineValue": baseline_value,
                "variantValue": variant_value, "deltaValue": delta_value, "perPoint": delta_value / delta,
                "perPointSe": se / delta, "iterations": variant[head]["n"], "report": str(report_path),
                "variantMetrics": variant,
            }
            # Back-compatible names of the DPS-only version
            entry.update({"baselineDps": baseline_value, "variantDps": variant_value, "deltaDps": delta_value,
                          "dpsPerPoint": entry["perPoint"]})
            if kind == "tank":
                for metric in ("ehSeconds", "netDtps", "health"):
                    b, v = baseline[metric], variant[metric]
                    if b["mean"] is not None and v["mean"] is not None:
                        entry[f"{metric}PerPoint"] = (v["mean"] - b["mean"]) / delta
                        entry[f"{metric}PerPointSe"] = ((v["se"] ** 2 + b["se"] ** 2) ** 0.5) / delta
            weights.append(entry)
            print(f"stat_weights.py:   {key}: {variant_value:.2f} {head} ({delta_value:+.2f}) -> "
                  f"{entry['perPoint']:+.3f} +- {entry['perPointSe']:.3f} {head}/point", file=sys.stderr)

    weights.sort(key=lambda w: w["perPoint"], reverse=True)
    result = {
        "profile": profile_path.stem, "kind": kind, "metric": head, "delta": base_delta,
        "perStatDelta": per_stat_delta, "level": level, "race": race,
        "duration": duration, "baselineBatches": baseline_batches, "baselineIterations": n,
        "variantIterations": variant_iterations, "baselineReports": baseline_paths, "baseline": baseline,
        "weights": weights,
    }
    baseline_report["statWeights"] = result
    baseline_report_path.write_text(json.dumps(baseline_report))

    out_path = os.environ.get("STATWEIGHTS_OUT", "").strip()
    if out_path:
        Path(out_path).write_text(json.dumps(result, indent=1))

    if baseline_html_path is not None:
        subprocess.run(
            ["python3", str(BUILD_REPORT_HTML), str(baseline_html_path), profile_path.stem, str(baseline_report_path)],
            check=True,
        )
        print(f"stat_weights.py: rebaked {baseline_html_path}", file=sys.stderr)

    print(f"\nstat_weights.py: results (highest {head}/point first):", file=sys.stderr)
    for w in weights:
        print(f"  {w['stat']:>22}: {w['perPoint']:+8.3f} +- {w['perPointSe']:.3f} {head}/point", file=sys.stderr)
    print(f"\nstat_weights.py: wrote weights into {baseline_report_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
