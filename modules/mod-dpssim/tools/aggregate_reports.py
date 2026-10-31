#!/usr/bin/env python3
"""
Aggregates N mod-dpssim report JSON files (SimReport::WriteJson()'s schema) from repeated runs of
the same profile/duration/level into one merged report - see docs/bugs-and-fixes.md's
SimDaemon::RunPlayerbot() non-determinism entry for why this exists: even an identical
seed/profile/duration produces a different DPS number every run, so any single run's numbers are
one noisy sample, not a measurement.

Averages what can be meaningfully averaged across iterations - summary totals (dps, totalDamage,
castCount, critCount, critRatePct) and the per-spell breakdown - and takes everything else (hits,
auraEvents, manaSamples, powerSamples, minionSamples, casts, and auraSamples when the profile sets AuraSampleIds)
from a single representative iteration, verbatim:
those are per-run timelines (when did this specific hit land, when did that specific buff go up), and there
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

The representative iteration (whose hits/auraEvents/manaSamples/powerSamples/minionSamples/casts/auraSamples appear
verbatim; each cast keeps its powerCost) is
whichever *kept* run's own DPS sits at or just below the *kept* set's median - not simply "iteration 1" (an
unusually quiet or lucky run could land there by pure chance - see
docs/.master-todo-list.md's cast-count-swing entry) and not a trimmed-away outlier either, since
this report is already declaring that run non-representative by excluding it from every other
figure.

Multi-target reports (config.targetCount > 1) are aggregated the same way, plus the per-target breakdown
(averaged element-wise over the kept runs) and the per-spell castCount (averaged) / targetsHit (max over the kept
runs). Reports whose targetCount or targetRank differ are refused: averaging a 1-target run with a 5-target run
would be meaningless. A report from before multi-target support counts as targetCount 1, rank "boss".

Heal reports ("kind": "heal", SimReport::WriteHealJson()) are aggregated by the same recipe in main_heal() below:
trimmed by hps instead of dps, an iteration with a death (healer or ally) is never trimmed, the representative run is
the median-hps kept one, and reports of a different group, HealTargets or infiniteMana are refused. The DPS path above
is untouched.

Tank reports ("kind": "tank", SimReport::WriteTankJson()) are a DPS report plus a "tank" section and are merged by
main_tank() below: the DPS part with the DPS helpers above, the tank section with its own (every numeric field of
tank.summary averaged over the kept runs, per-dummy, absorb and self-heal rows averaged, timelines from the
representative run). The scenario decides the trim: "dps" trims on DPS exactly as a DPS batch does (a run where the
actor died is never trimmed), "survive" trims on time to death (TTD; a run that lived counts the full duration as its
TTD, plan T11) and trims dead runs like any other, since in that scenario every run is expected to end in death. The
representative run is the median-DPS (dps) or median-TTD (survive) kept one. Reports of a different kind, scenario,
target setup, hit settings, swing speed, crit switch or pull auras are refused (and of a different duration in
"survive", where the duration is what a survived run's TTD means).

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
    all_ids: set[tuple[int, bool, int]] = set()
    for i, r in enumerate(reports):
        if i not in kept_idx:
            continue
        # keyed by (spellId, isPet, sourceEntry) so a pet's row never merges into the bot's, nor one minion's into
        # another's (isPet and sourceEntry are absent in older reports: False and 0, the actor)
        by_id = {(s["spellId"], s.get("isPet", False), s.get("sourceEntry", 0)): s for s in r.get("spells", [])}
        per_report_by_id.append(by_id)
        all_ids.update(by_id.keys())

    has_multi_target_fields = all(
        "castCount" in s for i, r in enumerate(reports) if i in kept_idx for s in r.get("spells", []))
    merged = []
    for spell_id, is_pet, source_entry in all_ids:
        hit_counts, crit_counts, total_damages, pcts, cast_counts, targets_hit = [], [], [], [], [], []
        for by_id in per_report_by_id:
            s = by_id.get((spell_id, is_pet, source_entry))
            hit_counts.append(s["hitCount"] if s else 0)
            crit_counts.append(s["critCount"] if s else 0)
            total_damages.append(s["totalDamage"] if s else 0)
            pcts.append(s["pctOfTotal"] if s else 0)
            cast_counts.append(s.get("castCount", 0) if s else 0)
            targets_hit.append(s.get("targetsHit", 0) if s else 0)
        row = {
            "spellId": spell_id,
            "isPet": is_pet,
            "sourceEntry": source_entry,
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


# ---------------------------------------------------------------------------------------------------------------------
# Heal reports (SimReport::WriteHealJson()'s schema, "kind": "heal")
# ---------------------------------------------------------------------------------------------------------------------

# Summary fields that are always numbers; averaged over the kept runs.
HEAL_SUMMARY_KEYS = [
    "elapsedMs", "effectiveHealing", "rawHealing", "overhealing", "overhealPct", "healAbsorbed", "absorbHealing",
    "hps", "rawHps", "hpsBeforeOom", "castCount", "triggeredCasts", "critRatePct", "manaSpent", "healingPerMana",
    "deaths", "resurrections", "damageDone", "dps", "wallClockMs", "pinHits", "pinRaises", "drainHits",
    "driverCastFailures",
]
# Summary fields that are null when the event never happened in a run: averaged over the kept runs where it did, with
# the number of such runs next to it ("<key>Runs" in the aggregate summary).
HEAL_NULLABLE_SUMMARY_KEYS = ["oomAtMs", "firstDeathAtMs", "actorDiedAtMs"]
# Per-spell fields averaged (a spell missing from a kept run counts as 0 for that run)
HEAL_SPELL_SUM_KEYS = ["casts", "hits", "ticks", "crits", "effective", "overheal", "healAbsorbed", "absorbed", "events",
                       "total", "manaSpent"]
# Per-target fields averaged over the kept runs
HEAL_TARGET_MEAN_KEYS = ["maxHealth", "healingReceived", "effectiveReceived", "absorbReceived", "overheal",
                         "damageRequested", "damageMitigated", "damageAbsorbed", "damageTaken", "damagePrevented",
                         "deaths", "minHealthPct", "avgHealthPct", "msBelow35Pct", "pinHits", "pinRaises"]
# Per-run timelines taken verbatim from the representative run
HEAL_TIMELINE_KEYS = ["heals", "absorbs", "damageTaken", "healthSamples", "deaths", "resurrections",
                      "groupAuraEvents", "casts", "manaSamples"]


def heal_setup(r: dict) -> tuple:
    c = r.get("config", {})
    return c.get("group"), c.get("healTargets"), bool(c.get("infiniteMana", False))


# Like trim_by_dps(), on hps. An iteration with a death (a healer or ally dying) is never trimmed, from either end: a
# run that lost someone must stay in the headline means.
def trim_by_hps(reports: list[dict]) -> tuple[set[int], list[float], list[float]]:
    n = len(reports)
    k = int(n * TRIM_FRACTION)
    order = sorted(range(n), key=lambda i: reports[i]["summary"]["hps"])
    died = {i for i, r in enumerate(reports) if r["summary"].get("deaths", 0) > 0}
    dropped_low_idx = [i for i in order[:k] if i not in died]
    dropped_high_idx = [i for i in (order[n - k:] if k > 0 else []) if i not in died]
    kept_idx = set(range(n)) - set(dropped_low_idx) - set(dropped_high_idx)
    dropped_low = sorted(reports[i]["summary"]["hps"] for i in dropped_low_idx)
    dropped_high = sorted(reports[i]["summary"]["hps"] for i in dropped_high_idx)
    return kept_idx, dropped_low, dropped_high


# The kept run whose hps sits at or just below the kept set's median (an actual run, see median_report())
def median_heal_report(reports: list[dict], kept_idx: set[int]) -> dict:
    kept = [reports[i] for i in sorted(kept_idx)]
    by_hps = sorted(kept, key=lambda r: r["summary"]["hps"])
    median_hps = statistics.median_low(r["summary"]["hps"] for r in kept)
    return next(r for r in by_hps if r["summary"]["hps"] == median_hps)


def aggregate_heal_summary(reports: list[dict], kept_idx: set[int]) -> tuple[dict, dict, dict]:
    trimmed: dict = {}
    raw: dict = {}
    per_iteration: dict = {}
    for key in HEAL_SUMMARY_KEYS:
        values = [r["summary"].get(key, 0) for r in reports]
        per_iteration[key] = values
        raw[key] = mean(values)
        trimmed[key] = mean([v for i, v in enumerate(values) if i in kept_idx])
    for key in HEAL_NULLABLE_SUMMARY_KEYS:
        values = [r["summary"].get(key) for r in reports]
        per_iteration[key] = values
        for target, picked in ((raw, [v for v in values if v is not None]),
                               (trimmed, [v for i, v in enumerate(values) if i in kept_idx and v is not None])):
            target[key] = mean(picked) if picked else None
            target[key + "Runs"] = len(picked)
    return trimmed, raw, per_iteration


def aggregate_heal_spells(reports: list[dict], kept_idx: set[int]) -> list[dict]:
    kept = [r for i, r in enumerate(reports) if i in kept_idx]
    per_report = [{(s["spellId"], s.get("isPet", False)): s for s in r.get("spells", [])} for r in kept]
    all_ids = set().union(*[set(d) for d in per_report]) if per_report else set()
    merged = []
    for spell_id, is_pet in all_ids:
        row = {"spellId": spell_id, "isPet": is_pet}
        for key in HEAL_SPELL_SUM_KEYS:
            row[key] = mean([d[(spell_id, is_pet)][key] if (spell_id, is_pet) in d else 0 for d in per_report])
        # Max, not mean: a property of the spell, like targetsHit in the DPS aggregate
        row["targetsHit"] = max((d[(spell_id, is_pet)]["targetsHit"] for d in per_report if (spell_id, is_pet) in d),
                                default=0)
        raw = row["effective"] + row["overheal"] + row["healAbsorbed"]
        row["overhealPct"] = 100.0 * row["overheal"] / raw if raw > 0 else 0.0
        row["avgHit"] = row["total"] / row["events"] if row["events"] > 0 else 0.0
        row["hpm"] = row["total"] / row["manaSpent"] if row["manaSpent"] > 0 else None
        merged.append(row)
    grand = sum(row["total"] for row in merged)
    for row in merged:
        row["pctOfTotal"] = 100.0 * row["total"] / grand if grand > 0 else 0.0
    merged.sort(key=lambda s: (s["total"], s["manaSpent"]), reverse=True)
    return merged


def aggregate_heal_targets(reports: list[dict], kept_idx: set[int], representative: dict) -> list[dict]:
    kept = [r.get("targets", []) for i, r in enumerate(reports) if i in kept_idx]
    merged = []
    for idx, base in enumerate(representative.get("targets", [])):
        rows = [t[idx] for t in kept if idx < len(t)]
        row = {k: base[k] for k in ("index", "role", "mode", "value", "percent", "subgroup")}
        for key in HEAL_TARGET_MEAN_KEYS:
            row[key] = mean([x[key] for x in rows])
        died = [x["diedAtMs"] for x in rows if x.get("diedAtMs") is not None]
        row["diedAtMs"] = mean(died) if died else None
        row["diedRuns"] = len(died)
        row["worstMinHealthPct"] = min((x["minHealthPct"] for x in rows), default=0.0)
        merged.append(row)
    return merged


def main_heal(out_path: Path, report_paths: list[Path], reports: list[dict]) -> int:
    for path, r in zip(report_paths, reports):
        if heal_setup(r) != heal_setup(reports[0]):
            g0, t0, m0 = heal_setup(reports[0])
            g1, t1, m1 = heal_setup(r)
            print(f"error: refusing to aggregate heal reports of different scenarios: {report_paths[0].name} has "
                  f"group {g0!r} / HealTargets {t0!r} / infiniteMana {m0}, {path.name} has group {g1!r} / "
                  f"HealTargets {t1!r} / infiniteMana {m1}", file=sys.stderr)
            return 1

    kept_idx, dropped_low, dropped_high = trim_by_hps(reports)
    summary, raw_mean, per_iteration = aggregate_heal_summary(reports, kept_idx)
    representative = median_heal_report(reports, kept_idx)
    death_lists = [r.get("deaths", []) for r in reports]
    death_counts = [r["summary"].get("deaths", 0) for r in reports]
    actor_deaths = [r["summary"]["actorDiedAtMs"] for r in reports if r["summary"].get("actorDiedAtMs") is not None]
    merged = {
        "kind": "heal",
        "config": representative["config"],
        "summary": summary,
        "spells": aggregate_heal_spells(reports, kept_idx),
        "targets": aggregate_heal_targets(reports, kept_idx, representative),
    }
    for key in HEAL_TIMELINE_KEYS:
        merged[key] = representative.get(key, [])
    merged["aggregate"] = {
        "iterations": len(reports),
        # Over ALL iterations (the headline deaths tile): death runs are never trimmed, but the trimmed means above
        # still leave out the few non-death runs that were
        "meanDeaths": mean(death_counts),
        "deathIterations": sum(1 for c in death_counts if c > 0),
        "deathCounts": death_counts,
        "deathLists": death_lists,
        "actorDeathCount": len(actor_deaths),
        "actorDiedAtMs": actor_deaths,
        "sourceReports": [p.name for p in report_paths],
        "representativeHps": representative["summary"]["hps"],
        "trim": {
            "fraction": TRIM_FRACTION,
            "droppedLowCount": len(dropped_low),
            "droppedHighCount": len(dropped_high),
            "keptCount": len(kept_idx),
            "droppedLowHps": dropped_low,
            "droppedHighHps": dropped_high,
            "rawMean": raw_mean,
        },
        "perIteration": per_iteration,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(merged))
    print(f"wrote {out_path} (heal: trimmed mean over {len(kept_idx)}/{len(reports)} iterations, "
          f"dropped {len(dropped_low)} low + {len(dropped_high)} high)")
    if any(death_counts):
        print(f"NOTE: {merged['aggregate']['deathIterations']}/{len(reports)} iterations had a death "
              f"(mean {merged['aggregate']['meanDeaths']:.2f} per iteration); those iterations are never trimmed.")
    if actor_deaths:
        print(f"WARNING: the healer DIED in {len(actor_deaths)}/{len(reports)} iterations (at sim ms {actor_deaths}); "
              f"those iterations are scored on the full duration.")
    return 0


# ---------------------------------------------------------------------------------------------------------------------
# Tank reports (SimReport::WriteTankJson()'s schema, "kind": "tank")
# ---------------------------------------------------------------------------------------------------------------------

# Per-run timelines of the tank section, taken verbatim from the representative run
TANK_TIMELINE_KEYS = ["swings", "samples", "threat"]
# tank.summary leaves that are labels or picks, not quantities: taken from the representative run instead of averaged
# (the survived / died flags are left out of the merge: the survived and died counts are in aggregate.tank)
TANK_SUMMARY_PICK_KEYS = {"scenario", "powerType", "lowestThreatDummy", "critBugAtMs"}


def tank_section(r: dict) -> dict:
    return r.get("tank") or {}


def tank_summary_of(r: dict) -> dict:
    return tank_section(r).get("summary") or {}


def tank_setup(r: dict) -> dict:
    """The settings two tank reports must share to be merged (field name -> value)."""
    t = tank_section(r).get("config") or {}
    scenario = t.get("scenario")
    pack = t.get("dummyKind") == "pack"
    return {
        "scenario": scenario,
        "targetCount": target_count(r),
        "targetRank": target_rank(r),
        # Only the hit range the run used: the other one is a profile default that no dummy swung with
        "hitDamage": t.get("packHitDamage") if pack else t.get("hitDamage"),
        "swingMs": t.get("swingMs"),
        "dummyCrit": t.get("dummyCrit"),
        "pullAuras": t.get("pullAuras", []),
        # A survived run's TTD is the duration, so runs of different lengths don't mix in "survive"
        "durationMs": r.get("config", {}).get("durationMs") if scenario == "survive" else None,
    }


def tank_ttd(r: dict) -> float:
    return tank_summary_of(r)["ttdMs"]


# Like trim_by_dps(), on the time to death (a survived run counts the duration). Dead runs are trimmed like any other:
# in the survive scenario every run is expected to die, so the DPS rule that keeps them does not apply.
def trim_by_ttd(reports: list[dict]) -> tuple[set[int], list[int], list[int]]:
    n = len(reports)
    k = int(n * TRIM_FRACTION)
    order = sorted(range(n), key=lambda i: tank_ttd(reports[i]))
    dropped_low_idx = order[:k]
    dropped_high_idx = order[n - k:] if k > 0 else []
    kept_idx = set(range(n)) - set(dropped_low_idx) - set(dropped_high_idx)
    return kept_idx, dropped_low_idx, dropped_high_idx


def median_tank_report(reports: list[dict], kept_idx: set[int], survive: bool) -> dict:
    kept = [reports[i] for i in sorted(kept_idx)]
    key = tank_ttd if survive else (lambda r: r["summary"]["dps"])
    by_key = sorted(kept, key=key)
    median = statistics.median_low(key(r) for r in kept)
    return next(r for r in by_key if key(r) == median)


def is_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def numeric_paths(d: dict, prefix: str = "") -> list[str]:
    """Dotted paths of every numeric leaf of a nested dict, in first-seen order."""
    out: list[str] = []
    for k, v in d.items():
        path = prefix + k
        if isinstance(v, dict):
            out.extend(numeric_paths(v, path + "."))
        elif is_number(v) and k not in TANK_SUMMARY_PICK_KEYS:
            out.append(path)
    return out


def get_path(d: dict, path: str):
    for part in path.split("."):
        if not isinstance(d, dict) or part not in d:
            return None
        d = d[part]
    return d


def set_path(d: dict, path: str, value) -> None:
    parts = path.split(".")
    for part in parts[:-1]:
        d = d.setdefault(part, {})
    d[parts[-1]] = value


# Returns (trimmed, raw, perIteration): trimmed / raw are nested like tank.summary (means over the kept runs and over
# all runs), perIteration is flat, dotted path -> the value of every run. A leaf that is null in some runs (ttdMs in
# the dps scenario) is averaged over the runs that have it and stays null when none does. Labels come from the
# representative.
def aggregate_tank_summary(reports: list[dict], kept_idx: set[int], representative: dict) -> tuple[dict, dict, dict]:
    summaries = [tank_summary_of(r) for r in reports]
    paths: list[str] = []
    for s in summaries:
        for path in numeric_paths(s):
            if path not in paths:
                paths.append(path)
    # Keys that are numeric in some runs and null in others still need a path
    for s in summaries:
        for k, v in s.items():
            if v is None and k not in paths and k not in TANK_SUMMARY_PICK_KEYS:
                paths.append(k)

    trimmed: dict = {}
    raw: dict = {}
    per_iteration: dict = {}
    for path in paths:
        values = [get_path(s, path) for s in summaries]
        per_iteration[path] = values
        for target, picked in ((raw, [v for v in values if is_number(v)]),
                               (trimmed, [v for i, v in enumerate(values) if i in kept_idx and is_number(v)])):
            set_path(target, path, mean(picked) if picked else None)
    rep = tank_summary_of(representative)
    for key in TANK_SUMMARY_PICK_KEYS:
        if key in rep:
            trimmed[key] = rep[key]
            raw[key] = rep[key]
    return trimmed, raw, per_iteration


def aggregate_tank_per_dummy(reports: list[dict], kept_idx: set[int], representative: dict) -> list[dict]:
    kept = [tank_section(r).get("perDummy", []) for i, r in enumerate(reports) if i in kept_idx]
    merged = []
    for idx, base in enumerate(tank_section(representative).get("perDummy", [])):
        rows = [t[idx] for t in kept if idx < len(t)]
        row: dict = {"index": base["index"]}
        for key in ("swings", "preArmorDamage", "damageTaken", "swingsOutsideFrontArc", "threat"):
            row[key] = mean([x[key] for x in rows])
        row["outcomes"] = {k: mean([x["outcomes"][k] for x in rows]) for k in base["outcomes"]}
        row["outcomePct"] = {k: mean([x["outcomePct"][k] for x in rows]) for k in base.get("outcomePct", {})}
        merged.append(row)
    return merged


def aggregate_tank_absorbs(reports: list[dict], kept_idx: set[int]) -> list[dict]:
    per_report = [{a["spellId"]: a for a in tank_section(r).get("absorbsBySpell", [])}
                  for i, r in enumerate(reports) if i in kept_idx]
    ids = set().union(*[set(d) for d in per_report]) if per_report else set()
    merged = [{"spellId": spell_id,
               "amount": mean([d[spell_id]["amount"] if spell_id in d else 0 for d in per_report]),
               "events": mean([d[spell_id]["events"] if spell_id in d else 0 for d in per_report])}
              for spell_id in ids]
    total = sum(row["amount"] for row in merged)
    for row in merged:
        row["pctOfAbsorbed"] = 100.0 * row["amount"] / total if total > 0 else 0.0
    merged.sort(key=lambda row: row["amount"], reverse=True)
    return merged


TANK_HEAL_SUM_KEYS = ["casts", "hits", "ticks", "crits", "effective", "overheal", "healAbsorbed"]


def aggregate_tank_heals(reports: list[dict], kept_idx: set[int]) -> list[dict]:
    per_report = [{(h["spellId"], h.get("isPet", False)): h for h in tank_section(r).get("selfHeals", [])}
                  for i, r in enumerate(reports) if i in kept_idx]
    keys = set().union(*[set(d) for d in per_report]) if per_report else set()
    merged = []
    for key in keys:
        row = {"spellId": key[0], "isPet": key[1]}
        for name in TANK_HEAL_SUM_KEYS:
            row[name] = mean([d[key][name] if key in d else 0 for d in per_report])
        raw_heal = row["effective"] + row["overheal"] + row["healAbsorbed"]
        row["overhealPct"] = 100.0 * row["overheal"] / raw_heal if raw_heal > 0 else 0.0
        merged.append(row)
    merged.sort(key=lambda row: row["effective"], reverse=True)
    return merged


def main_tank(out_path: Path, report_paths: list[Path], reports: list[dict]) -> int:
    for path, r in zip(report_paths, reports):
        if not tank_section(r).get("summary"):
            print(f"error: {path.name} is a tank report without a tank section", file=sys.stderr)
            return 1
    first = tank_setup(reports[0])
    for path, r in zip(report_paths, reports):
        setup = tank_setup(r)
        if setup != first:
            diff = ", ".join(f"{k} {first[k]!r} vs {setup[k]!r}" for k in first if first[k] != setup[k])
            print(f"error: refusing to aggregate tank reports of different setups: {report_paths[0].name} vs "
                  f"{path.name}: {diff}", file=sys.stderr)
            return 1

    survive = first["scenario"] == "survive"
    if survive:
        kept_idx, dropped_low_idx, dropped_high_idx = trim_by_ttd(reports)
        dropped_low = [tank_ttd(reports[i]) for i in dropped_low_idx]
        dropped_high = [tank_ttd(reports[i]) for i in dropped_high_idx]
        dropped_low_dps = sorted(reports[i]["summary"]["dps"] for i in dropped_low_idx)
        dropped_high_dps = sorted(reports[i]["summary"]["dps"] for i in dropped_high_idx)
    else:
        kept_idx, dropped_low_dps, dropped_high_dps = trim_by_dps(reports)
        dropped_low = dropped_high = []

    summary, raw_mean, per_iteration = aggregate_summary(reports, kept_idx)
    death_times = [r["summary"]["actorDiedAtMs"] for r in reports if r["summary"].get("actorDiedAtMs") is not None]
    representative = median_tank_report(reports, kept_idx, survive)
    rep_tank = tank_section(representative)
    tank_trimmed, tank_raw, tank_per_iteration = aggregate_tank_summary(reports, kept_idx, representative)
    survived_flags = [bool(tank_summary_of(r).get("survived")) for r in reports]
    crit_bug_runs = sum(1 for r in reports if tank_summary_of(r).get("critBugCount", 0) > 0)

    merged = {
        "kind": "tank",
        "config": representative["config"],
        "summary": summary,
        "spells": aggregate_spells(reports, kept_idx),
        "hits": representative.get("hits", []),
        "auraEvents": representative.get("auraEvents", []),
        "manaSamples": representative.get("manaSamples", []),
        "powerSamples": representative.get("powerSamples", []),
        "minionSamples": representative.get("minionSamples", []),
        "casts": representative.get("casts", []),
        # Only a profile with AuraSampleIds has the key; carried verbatim from the representative iteration
        **({"auraSamples": representative["auraSamples"]} if "auraSamples" in representative else {}),
        "targets": aggregate_targets(reports, kept_idx),
        "tank": {
            "config": rep_tank.get("config", {}),
            "actor": rep_tank.get("actor", {}),
            "summary": tank_trimmed,
            "perDummy": aggregate_tank_per_dummy(reports, kept_idx, representative),
            "absorbsBySpell": aggregate_tank_absorbs(reports, kept_idx),
            "selfHeals": aggregate_tank_heals(reports, kept_idx),
        },
        "aggregate": {
            "iterations": len(reports),
            "actorDeathCount": len(death_times),
            "actorDiedAtMs": death_times,
            "sourceReports": [p.name for p in report_paths],
            "representativeDps": representative["summary"]["dps"],
            "trimMetric": "ttd" if survive else "dps",
            "trim": {
                "fraction": TRIM_FRACTION,
                "droppedLowCount": len(dropped_low_dps),
                "droppedHighCount": len(dropped_high_dps),
                "keptCount": len(kept_idx),
                # The DPS of the runs that were dropped (whatever the trim metric was), for the DPS summary's note
                "droppedLowDps": dropped_low_dps,
                "droppedHighDps": dropped_high_dps,
                "rawMean": raw_mean,
            },
            "perIteration": per_iteration,
            "tank": {
                "scenario": first["scenario"],
                "survivedCount": sum(survived_flags),
                "survivedKept": sum(1 for i, f in enumerate(survived_flags) if f and i in kept_idx),
                "diedCount": sum(1 for r in reports if tank_summary_of(r).get("died")),
                "critBugRuns": crit_bug_runs,
                "rawMean": tank_raw,
                "perIteration": tank_per_iteration,
            },
        },
    }
    for key in TANK_TIMELINE_KEYS:
        merged["tank"][key] = rep_tank.get(key, [])
    if survive:
        merged["aggregate"]["representativeTtd"] = tank_ttd(representative)
        merged["aggregate"]["trim"]["droppedLowTtd"] = dropped_low
        merged["aggregate"]["trim"]["droppedHighTtd"] = dropped_high

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(merged))
    metric = "TTD" if survive else "DPS"
    print(f"wrote {out_path} (tank {first['scenario']}: trimmed mean by {metric} over {len(kept_idx)}/{len(reports)} "
          f"iterations, dropped {len(dropped_low_dps)} low + {len(dropped_high_dps)} high)")
    ts = tank_trimmed
    if survive:
        ttd = ts.get("ttdMs")
        print(f"mean TTD {ttd / 1000:.1f} s" if ttd is not None else "mean TTD n/a",
              f"| survived {sum(survived_flags)}/{len(reports)} runs | mean net DTPS {ts.get('netDtps', 0):.1f} "
              f"| mean DTPS {ts.get('dtps', 0):.1f} | mean DPS while alive {ts.get('dpsAlive', 0):.1f} "
              f"(whole-fight DPS {summary['dps']:.1f})")
    if crit_bug_runs:
        print(f"WARNING: {crit_bug_runs}/{len(reports)} iterations took a crit on a swing whose crit chance was 0 "
              f"(the tank should be crit immune)")
    if death_times and not survive:
        print(f"WARNING: the actor DIED in {len(death_times)}/{len(reports)} iterations (at sim ms {death_times}); "
              f"those iterations are scored on the full duration and are never trimmed from the means.")
    return 0


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        return 1

    out_path = Path(sys.argv[1])
    report_paths = [Path(p) for p in sys.argv[2:]]
    reports = [json.loads(p.read_text()) for p in report_paths]

    # A heal report carries "kind": "heal", a tank report "kind": "tank"; a DPS report has no kind. They never merge.
    kinds = {r.get("kind", "dps") for r in reports}
    if len(kinds) > 1:
        print(f"error: refusing to aggregate reports of different kinds: {sorted(kinds)}", file=sys.stderr)
        return 1
    if kinds == {"heal"}:
        return main_heal(out_path, report_paths, reports)
    if kinds == {"tank"}:
        return main_tank(out_path, report_paths, reports)

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
        "powerSamples": representative.get("powerSamples", []),
        "minionSamples": representative.get("minionSamples", []),
        "casts": representative.get("casts", []),
        # Only a profile with AuraSampleIds has the key; carried verbatim from the representative iteration
        **({"auraSamples": representative["auraSamples"]} if "auraSamples" in representative else {}),
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
