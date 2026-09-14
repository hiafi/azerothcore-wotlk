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
    stat_weights.py <profile> [durationSeconds] [level] [race] [baselineIterations] [statDelta]

<profile>/[durationSeconds]/[level]/[race] mean exactly what they mean to run-sim.sh (see its own
doc comment) - this script calls that one for every batch (baseline and each variant), it does not
talk to Docker/the DB itself. [baselineIterations] overrides run-sim.sh's own default for the
baseline batch only (each variant is still exactly half of whatever the baseline actually used,
rounded down, minimum 1) - omit it to use "the iterations from the config" as originally asked for;
pass a small number (e.g. 2) for a fast smoke test of this whole pipeline without waiting through a
full-size batch.

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
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "modules" / "mod-dpssim" / "tools"
RUN_SIM_SH = TOOLS_DIR / "run-sim.sh"
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


# Runs one run-sim.sh batch and returns (reportJsonPath, htmlPath, parsedReport). `iterations=None`
# omits the argument entirely so run-sim.sh's own default applies - see this module's doc comment
# for why the baseline call is made this way. Lets run-sim.sh's own stderr (progress messages)
# stream straight through rather than capturing it, so a long stat-weight pass still shows live
# progress; only stdout (the two final path lines) is captured.
def run_sim(profile_path: Path, duration: int, level: int, race: int, iterations: int | None) -> tuple[Path, Path, dict]:
    args = [str(RUN_SIM_SH), str(profile_path), str(duration), str(level), str(race)]
    if iterations is not None:
        args.append(str(iterations))
    result = subprocess.run(args, stdout=subprocess.PIPE, text=True, check=True)
    out_lines = [line for line in result.stdout.splitlines() if line.strip()]
    if len(out_lines) < 2:
        raise RuntimeError(f"run-sim.sh produced unexpected stdout: {result.stdout!r}")
    report_path, html_path = Path(out_lines[-2]), Path(out_lines[-1])
    return report_path, html_path, json.loads(report_path.read_text())


def iterations_used(report: dict) -> int:
    agg = report.get("aggregate")
    return agg["iterations"] if agg else 1


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 1

    profile_arg = sys.argv[1]
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 180
    level = int(sys.argv[3]) if len(sys.argv) > 3 else 60
    race = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    baseline_iterations_override = int(sys.argv[5]) if len(sys.argv) > 5 else None
    stat_delta_override = int(sys.argv[6]) if len(sys.argv) > 6 else None

    profile_path = resolve_profile_path(profile_arg)
    lines, values = parse_profile(profile_path)
    delta = stat_delta_override if stat_delta_override is not None else resolve_delta(level)
    if stat_delta_override is not None:
        print(f"stat_weights.py: statDelta override in effect - using +{delta} for every tested "
              "stat instead of the level-bracket default. This is a sign/plausibility sanity check, "
              "not a real per-point weight run - see this script's own doc comment.", file=sys.stderr)

    # Master switch - see SimProfile.h's Profile::StatWeightsEnabled doc comment. Checked before
    # anything else runs (including the baseline batch) since it means "don't run stat weights
    # against this profile at all," not "run the baseline but skip variants."
    if values.get("StatWeightsEnabled", "true").lower() == "false":
        print(f"stat_weights.py: StatWeightsEnabled = false in {profile_path} - stat weights are "
              "turned off for this profile, not running anything.", file=sys.stderr)
        return 1

    tested_stats = [(key, flag) for key, flag in STAT_TEST_KEYS if values.get(flag, "false").lower() == "true"]
    if not tested_stats:
        print(f"stat_weights.py: no 'Test<Stat> = true' flags found in {profile_path} - nothing to "
              "weigh. See SimProfile.h's Profile::StatWeightTests doc comment.", file=sys.stderr)
        return 1

    print(f"stat_weights.py: baseline batch ({profile_path.name}, {duration}s, level {level})...", file=sys.stderr)
    baseline_report_path, baseline_html_path, baseline_report = run_sim(
        profile_path, duration, level, race, baseline_iterations_override)
    baseline_dps = baseline_report["summary"]["dps"]
    n = iterations_used(baseline_report)
    variant_iterations = max(1, n // 2)
    print(f"stat_weights.py: baseline DPS = {baseline_dps:.2f} (avg of {n} run(s)). Testing "
          f"{len(tested_stats)} stat(s) at +{delta}, {variant_iterations} run(s) each.", file=sys.stderr)

    weights = []
    SCRATCH_PARENT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="run.", dir=SCRATCH_PARENT) as scratch_dir_name:
        scratch_dir = Path(scratch_dir_name)
        for key, _flag in tested_stats:
            variant_path = scratch_dir / f"{profile_path.stem}.{key}.conf"
            bump_profile(lines, values, key, delta, variant_path)
            print(f"stat_weights.py: testing {key} (+{delta})...", file=sys.stderr)
            _report_path, _html_path, variant_report = run_sim(variant_path, duration, level, race, variant_iterations)
            variant_dps = variant_report["summary"]["dps"]
            delta_dps = variant_dps - baseline_dps
            weight = delta_dps / delta
            weights.append({
                "stat": key, "delta": delta, "baselineDps": baseline_dps, "variantDps": variant_dps,
                "deltaDps": delta_dps, "dpsPerPoint": weight, "iterations": variant_iterations,
            })
            print(f"stat_weights.py:   {key}: {variant_dps:.2f} DPS ({delta_dps:+.2f}) -> "
                  f"{weight:+.3f} DPS/point", file=sys.stderr)

    weights.sort(key=lambda w: w["dpsPerPoint"], reverse=True)
    baseline_report["statWeights"] = {
        "delta": delta, "level": level, "baselineIterations": n, "variantIterations": variant_iterations,
        "weights": weights,
    }
    baseline_report_path.write_text(json.dumps(baseline_report))

    subprocess.run(
        ["python3", str(BUILD_REPORT_HTML), str(baseline_html_path), profile_path.stem, str(baseline_report_path)],
        check=True,
    )

    print("\nstat_weights.py: results (highest DPS/point first):", file=sys.stderr)
    for w in weights:
        print(f"  {w['stat']:>20}: {w['dpsPerPoint']:+8.3f} DPS/point", file=sys.stderr)
    print(f"\nstat_weights.py: wrote weights into {baseline_report_path}", file=sys.stderr)
    print(f"stat_weights.py: rebaked {baseline_html_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
