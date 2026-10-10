#!/usr/bin/env python3
"""
Aggregates N mod-dpssim report JSON files (SimReport::WriteJson()'s schema) from repeated runs of
the same profile/duration/level into one merged report - see docs/bugs-and-fixes.md's
SimDaemon::RunPlayerbot() non-determinism entry for why this exists: even an identical
seed/profile/duration produces a different DPS number every run, so any single run's numbers are
one noisy sample, not a measurement.

Averages what can be meaningfully averaged across iterations - summary totals (dps, totalDamage,
castCount, critCount, critRatePct) and the per-spell breakdown - and takes everything else (hits,
auraEvents, manaSamples, casts) from a single representative iteration, verbatim: those are
per-run timelines (when did this specific hit land, when did that specific buff go up), and there
is no sensible way to "average" N different timelines into one without fabricating events that
never happened in any single run.

**Trimmed mean, added 2026-09-13**: this profile's own kit is randomness-sensitive by nature (a
Missile Barrage/Clearcasting-heavy Arcane build can get proc-starved or proc-showered by pure luck),
on top of the already-noisy RunPlayerbot() non-determinism - so before averaging, the TRIM_FRACTION
(default 10%) most extreme runs on *both* ends of the DPS distribution are dropped, and every
summary/per-spell figure is computed over only the remaining, "typical" runs - not "trim each field
independently by its own extremes" (which could average across a different subset of runs per
field, an internally inconsistent result), but one DPS-sorted trim applied uniformly to every
field, including which run gets picked as "representative" below. The untrimmed mean rides along
under "aggregate.trim.rawMean" and every raw per-iteration value still rides along under
"aggregate.perIteration" (unaffected by trimming) - trimming is meant to reduce the influence of
outliers, not hide that they happened.

The representative iteration (whose hits/auraEvents/manaSamples/casts appear verbatim) is whichever
*kept* run's own DPS sits at or just below the *kept* set's median - not simply "iteration 1" (an
unusually quiet or lucky run could land there by pure chance - see
docs/.master-todo-list.md's cast-count-swing entry) and not a trimmed-away outlier either, since
this report is already declaring that run non-representative by excluding it from every other
figure.

Multi-target reports (config.targetCount > 1) are aggregated the same way, plus the per-target breakdown
(averaged element-wise over the kept runs) and the per-spell castCount (averaged) / targetsHit (max over the kept
runs). Reports whose targetCount or targetRank differ are refused: averaging a 1-target run with a 5-target run
would be meaningless. A report from before multi-target support counts as targetCount 1, rank "boss".

Usage:
    aggregate_reports.py <output.json> <report1.json> [<report2.json> ...]
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

# Fraction trimmed from *each* end of the DPS-sorted distribution before averaging - 0.1 means the
# bottom 10% and top 10% of runs are dropped, and the remaining 80% are averaged. Matches
# scipy.stats.trim_mean's own convention for turning a fraction into a count: floor(n * fraction)
# per side, never more (so a small n never accidentally trims everything away).
TRIM_FRACTION = 0.1


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


# Indices (into `reports`, in their original order) of the runs kept after trimming the top/bottom
# TRIM_FRACTION by DPS (never an iteration where the actor died), plus the (lowest, highest) DPS values actually dropped, for transparency.
def trim_by_dps(reports: list[dict]) -> tuple[set[int], list[float], list[float]]:
    n = len(reports)
    k = int(n * TRIM_FRACTION)
    order = sorted(range(n), key=lambda i: reports[i]["summary"]["dps"])
    # An iteration where the actor died is never trimmed: a self-killing rotation must stay in the headline mean
    died = {i for i, r in enumerate(reports) if r["summary"].get("actorDiedAtMs") is not None}
    dropped_low_idx = [i for i in order[:k] if i not in died]
    dropped_high_idx = order[n - k:] if k > 0 else []
    kept_idx = set(range(n)) - set(dropped_low_idx) - set(dropped_high_idx)
    dropped_low = sorted(reports[i]["summary"]["dps"] for i in dropped_low_idx)
    dropped_high = sorted(reports[i]["summary"]["dps"] for i in dropped_high_idx)
    return kept_idx, dropped_low, dropped_high


# The real iteration (not an interpolated value - statistics.median() would average the two middle
# values for an even N, which isn't any actual run's timeline) among `kept_idx` whose own DPS sits
# at or just below that kept set's median. Ties/even-N break toward the lower of the two middle
# values (statistics.median_low's own convention) purely for a deterministic, reproducible pick -
# there's no principled reason to prefer the higher one.
def median_report(reports: list[dict], kept_idx: set[int]) -> dict:
    kept = [reports[i] for i in kept_idx]
    by_dps = sorted(kept, key=lambda r: r["summary"]["dps"])
    median_dps = statistics.median_low(r["summary"]["dps"] for r in kept)
    return next(r for r in by_dps if r["summary"]["dps"] == median_dps)


# Summary fields worth averaging - every field SimReport::WriteJson() puts in "summary" today.
SUMMARY_KEYS = ["elapsedMs", "totalDamage", "dps", "castCount", "critCount", "critRatePct"]
# Added with multi-target support; only averaged (and only written) when every report carries them, so an aggregate
# of older reports stays free of fields that never existed in its inputs.
MULTI_TARGET_SUMMARY_KEYS = ["dpsPerTarget", "targetSwitches"]


def target_count(r: dict) -> int:
    return r.get("config", {}).get("targetCount", 1)


def target_rank(r: dict) -> str:
    return r.get("config", {}).get("targetRank", "boss")


# Returns (trimmedMean, rawMean, perIteration) - perIteration always holds all N raw values
# (untouched by trimming, for the report's own spread display); trimmedMean/rawMean are each a
# {key: value} dict over SUMMARY_KEYS, computed over `kept_idx` and all indices respectively.
def aggregate_summary(reports: list[dict], kept_idx: set[int]) -> tuple[dict, dict, dict]:
    trimmed: dict = {}
    raw: dict = {}
    per_iteration: dict = {}
    keys = SUMMARY_KEYS + [k for k in MULTI_TARGET_SUMMARY_KEYS if all(k in r["summary"] for r in reports)]
    for key in keys:
        values = [r["summary"][key] for r in reports]
        per_iteration[key] = values
        raw[key] = mean(values)
        trimmed[key] = mean([v for i, v in enumerate(values) if i in kept_idx])
    return trimmed, raw, per_iteration


# Averages each spell's aggregate stats across the kept iterations only (see this module's doc
# comment for why the same trimmed set applies here too, not an independent per-spell trim). A
# spell missing from one kept iteration's "spells" (never cast, or cast but never landed) counts as
# zero for that iteration rather than being excluded from the average - this is "average damage per
# run this spell could have appeared in", not "average damage in runs where it happened to appear",
# which would overstate a proc-gated spell's typical contribution.
def aggregate_spells(reports: list[dict], kept_idx: set[int]) -> list[dict]:
    per_report_by_id = []
    all_ids: set[tuple[int, bool]] = set()
    for i, r in enumerate(reports):
        if i not in kept_idx:
            continue
        # keyed by (spellId, isPet) so a pet's row never merges into the bot's (isPet is absent in older reports)
        by_id = {(s["spellId"], s.get("isPet", False)): s for s in r.get("spells", [])}
        per_report_by_id.append(by_id)
        all_ids.update(by_id.keys())

    has_multi_target_fields = all(
        "castCount" in s for i, r in enumerate(reports) if i in kept_idx for s in r.get("spells", []))
    merged = []
    for spell_id, is_pet in all_ids:
        hit_counts, crit_counts, total_damages, pcts, cast_counts, targets_hit = [], [], [], [], [], []
        for by_id in per_report_by_id:
            s = by_id.get((spell_id, is_pet))
            hit_counts.append(s["hitCount"] if s else 0)
            crit_counts.append(s["critCount"] if s else 0)
            total_damages.append(s["totalDamage"] if s else 0)
            pcts.append(s["pctOfTotal"] if s else 0)
            cast_counts.append(s.get("castCount", 0) if s else 0)
            targets_hit.append(s.get("targetsHit", 0) if s else 0)
        row = {
            "spellId": spell_id,
            "isPet": is_pet,
            "hitCount": mean(hit_counts),
            "critCount": mean(crit_counts),
            "totalDamage": mean(total_damages),
            "pctOfTotal": mean(pcts),
        }
        if has_multi_target_fields:
            row["castCount"] = mean(cast_counts)
            # Max, not mean: "how many distinct dummies can this row reach" is a property of the spell, and a
            # mean of per-run distinct counts would read as a fractional, meaningless number of targets.
            row["targetsHit"] = max(targets_hit)
        merged.append(row)
    merged.sort(key=lambda s: s["totalDamage"], reverse=True)
    return merged


# Element-wise average of "targets" over the kept runs: totalDamage is averaged, pctOfTotal recomputed from the
# averaged damage so the column still sums to 100. Empty for reports without a "targets" block.
def aggregate_targets(reports: list[dict], kept_idx: set[int]) -> list[dict]:
    kept = [r.get("targets", []) for i, r in enumerate(reports) if i in kept_idx]
    count = max((len(t) for t in kept), default=0)
    damages = [mean([t[idx]["totalDamage"] if idx < len(t) else 0 for t in kept]) for idx in range(count)]
    total = sum(damages)
    return [{"index": idx, "totalDamage": dmg, "pctOfTotal": dmg / total * 100 if total > 0 else 0.0}
            for idx, dmg in enumerate(damages)]


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        return 1

    out_path = Path(sys.argv[1])
    report_paths = [Path(p) for p in sys.argv[2:]]
    reports = [json.loads(p.read_text()) for p in report_paths]

    for path, r in zip(report_paths, reports):
        if target_count(r) != target_count(reports[0]) or target_rank(r) != target_rank(reports[0]):
            print(f"error: refusing to aggregate reports with different target setups: {report_paths[0].name} has "
                  f"targetCount {target_count(reports[0])} / targetRank {target_rank(reports[0])!r}, {path.name} has "
                  f"targetCount {target_count(r)} / targetRank {target_rank(r)!r}", file=sys.stderr)
            return 1

    kept_idx, dropped_low, dropped_high = trim_by_dps(reports)
    summary, raw_mean, per_iteration = aggregate_summary(reports, kept_idx)
    # Iterations where the actor died (actorDiedAtMs null/absent when it lived). They are never trimmed, so they stay in the
    # headline means above and a self-killing rotation shows up as low DPS; this only makes the cause visible.
    death_times = [r["summary"]["actorDiedAtMs"] for r in reports if r["summary"].get("actorDiedAtMs") is not None]
    representative = median_report(reports, kept_idx)
    targets = aggregate_targets(reports, kept_idx)
    merged = {
        # targetCount / targetSpreadYards / targetRank ride along inside config (identical across all runs,
        # checked above)
        "config": representative["config"],
        "summary": summary,
        "spells": aggregate_spells(reports, kept_idx),
        # Verbatim from the median-DPS *kept* iteration - see median_report()'s doc comment for why
        # that one, not iteration 1 and not a trimmed-away outlier.
        "hits": representative.get("hits", []),
        "auraEvents": representative.get("auraEvents", []),
        "manaSamples": representative.get("manaSamples", []),
        "casts": representative.get("casts", []),
        "aggregate": {
            "iterations": len(reports),
            "actorDeathCount": len(death_times),
            "actorDiedAtMs": death_times,
            "sourceReports": [p.name for p in report_paths],
            "representativeDps": representative["summary"]["dps"],
            "trim": {
                "fraction": TRIM_FRACTION,
                "droppedLowCount": len(dropped_low),
                "droppedHighCount": len(dropped_high),
                "keptCount": len(kept_idx),
                "droppedLowDps": dropped_low,
                "droppedHighDps": dropped_high,
                "rawMean": raw_mean,
            },
            "perIteration": per_iteration,
        },
    }

    if targets:
        merged["targets"] = targets

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(merged))
    print(f"wrote {out_path} (trimmed mean over {len(kept_idx)}/{len(reports)} iterations, "
          f"dropped {len(dropped_low)} low + {len(dropped_high)} high)")
    if death_times:
        print(f"WARNING: the actor DIED in {len(death_times)}/{len(reports)} iterations (at sim ms {death_times}); "
              f"those iterations are scored on the full duration and are never trimmed from the means.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
