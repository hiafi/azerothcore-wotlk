#!/usr/bin/env python3
"""
Bootstrap tool for docs/single-rank-class-conversion-playbook.md step 4.

For one class's source/spells/<class>.csv (already populated by pull.py with
every rank of every real player chain), groups spell IDs by spell_ranks'
first_spell_id, and for each multi-rank chain rewrites the survivor
(rank-1) row in place per the playbook's algorithm:

  - BasePoints/BaseLevel/SpellLevel: unchanged from rank 1.
  - RealPointsPerLevel: (anchor value - rank1 value) / (anchor level -
    rank1's own learn level), picking the anchor per the "covers 60" /
    top-rank-fallback rules, per effect index.
  - EffectBonusMultiplier_N / cast_time_ms / mana_cost_pct: max rank's value.
  - mana_cost: zeroed only for mana-costed (power_type == 0) chains.
  - MaxLevel: forced to 80. NameSubtext_Lang_enUS: blanked.

This is the mechanical half of step 4 only. It does NOT do: step 3 (NPC
audit), step 5 (spell_bonus_data), step 7 (world-DB migration for
superseded ranks), or step 8 (mod-playerbots). It also does not silently
resolve the "needs a human call" edge cases from the playbook's Gotchas
section - those are printed as warnings and the affected effect is left
untouched (flat, ppl=0) rather than guessed at:
  - SPELL_EFFECT_CREATE_ITEM(_2) / ENCHANT_ITEM* effects (non-scaling).
  - |base_points| > 5000 in any rank (probable embedded spell-ID reference).
  - A higher rank introducing a whole new effect slot rank 1 never had -
    this one IS auto-handled (copied from the introducing rank, flat),
    per this project's established default (see rogue notes in the
    playbook), but is still printed so it can be spot-checked.

Usage:
  python3 apps/dbc-tools/bootstrap.py <classname> [--dry-run]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_ROOT))

from lib import sql_dump, state  # noqa: E402
from lib.source import SPELL_CSV_FIELDNAMES, SPELL_CSV_JSON_FIELDS  # noqa: E402
from lib.source import SPELL_CSV_INT_FIELDS, SPELL_CSV_FLOAT_FIELDS  # noqa: E402

SPELLS_DIR = TOOL_ROOT / "source" / "spells"
_SPELL_RANKS_COLUMNS = ("first_spell_id", "spell_id", "rank")

CREATE_ITEM_TYPES = {24, 157}
ENCHANT_ITEM_TYPES = {53, 54, 156}
NONSCALING_TYPES = CREATE_ITEM_TYPES | ENCHANT_ITEM_TYPES
EMBEDDED_ID_THRESHOLD = 5000
SPELL_AURA_DUMMY = 4
SYSTEM_MAX_LEVEL = 80


def ov(row: dict, key: str, default=0):
    ro = row.get("raw_overrides") or {}
    if key in ro:
        return ro[key]
    return default


def _blank(v):
    return v is None or (isinstance(v, str) and v.strip() == "")


def load_class_rows(klass: str) -> tuple[list[dict], dict[int, int]]:
    """Returns (ordered list of row dicts with fields type-converted like
    lib.source does, {id: index in list})."""
    path = SPELLS_DIR / f"{klass}.csv"
    rows = []
    index_by_id = {}
    with open(path, newline="", encoding="utf-8") as f:
        for raw in csv.DictReader(f):
            if not raw.get("id") or raw["id"].strip().startswith("#"):
                continue
            entry = dict(raw)
            for field in SPELL_CSV_INT_FIELDS:
                v = entry.get(field)
                entry[field] = None if _blank(v) else int(v)
            for field in SPELL_CSV_FLOAT_FIELDS:
                v = entry.get(field)
                entry[field] = None if _blank(v) else float(v)
            for field in SPELL_CSV_JSON_FIELDS:
                v = entry.get(field)
                entry[field] = None if _blank(v) else json.loads(v)
            index_by_id[entry["id"]] = len(rows)
            rows.append(entry)
    return rows, index_by_id


def load_spell_ranks_chains() -> dict[int, list[tuple[int, int]]]:
    path = state.BASE_SQL_DIR / "spell_ranks.sql"
    raw_rows = sql_dump.read_table_rows(path, "spell_ranks", _SPELL_RANKS_COLUMNS)
    chains: dict[int, list[tuple[int, int]]] = {}
    for r in raw_rows:
        chains.setdefault(r["first_spell_id"], []).append((r["spell_id"], r["rank"]))
    return chains


def learn_level(row: dict) -> int:
    return max(ov(row, "BaseLevel", 0), ov(row, "SpellLevel", 0))


def eff_max(row: dict) -> float:
    ml = ov(row, "MaxLevel", 0)
    return float("inf") if not ml else ml


def effect_value_at(row: dict, i: int, level: int) -> float | None:
    eff = row.get(f"effect{i}")
    if not eff:
        return None
    bp = eff.get("base_points", 0) or 0
    ppl = eff.get("points_per_level", 0.0) or 0.0
    return bp + ppl * (level - learn_level(row))


def pick_anchor(rank_rows: list[dict], rank1: dict) -> tuple[dict, int, str]:
    """Returns (anchor_row, anchor_level, reason_str).

    Extra check beyond the playbook's literal covers-60 rule, needed for the
    first time on Death Knight: DK is the only class whose rank-1 learn
    level already sits inside the 51-60 band (every other class's chains
    start around level 1-20, so by the time a chain's ranks reach level 60
    they've essentially exhausted the chain's real growth already). That
    means a DK chain can have a covers-60 candidate that is NOT the top
    rank, with real per-rank growth continuing well past it (e.g. Blood
    Strike ranks 1/2 sit at level 55/59, but ranks 3-6 keep growing up to
    level 80) - anchoring at the covers-60 candidate alone derives a slope
    from only the shallow 55-59 window and drastically undershoots the real
    level-80 value. Validate the covers-60 anchor against the chain's
    literal top rank's own value before trusting it; fall back to the top
    rank if it would undershoot/overshoot by more than 25%."""
    top = max(rank_rows, key=lambda r: r["_rank"])
    top_max = ov(top, "MaxLevel", 0)
    top_level = top_max if top_max else SYSTEM_MAX_LEVEL
    fallback = (top, top_level, "top-rank-fallback")

    r1_learn = learn_level(rank1)
    if r1_learn >= 60:
        return fallback
    candidates = [r for r in rank_rows if ov(r, "BaseLevel", 0) <= 60 <= eff_max(r)]
    if not candidates:
        return fallback
    candidates.sort(key=lambda r: (ov(r, "BaseLevel", 0), r["_rank"]))
    anchor = candidates[-1]
    if anchor is top:
        return anchor, 60, "covers-60"

    for i in (1, 2, 3):
        r1_eff, top_eff = rank1.get(f"effect{i}"), top.get(f"effect{i}")
        if not r1_eff or not top_eff or top_eff.get("type") in NONSCALING_TYPES:
            continue
        r1v = r1_eff.get("base_points", 0) or 0
        top_actual = effect_value_at(top, i, top_level)
        anchor_v = effect_value_at(anchor, i, 60)
        if top_actual is None or top_actual == r1v:
            continue
        # anchor_v == r1v (e.g. the covers-60 candidate is rank 1 itself,
        # trivially) is NOT skipped here - that's exactly the undershoot
        # case: real growth exists in later ranks but covers-60 would
        # report a flat 0 slope, discarding all of it.
        slope60 = (anchor_v - r1v) / (60 - r1_learn)
        predicted_top = r1v + slope60 * (top_level - r1_learn)
        ratio = predicted_top / top_actual if top_actual else None
        if ratio is None or ratio < 0.75 or ratio > 1.33:
            return top, top_level, "covers-60-overridden(undershoot-vs-top-rank)"

    return anchor, 60, "covers-60"


def bootstrap_chain(chain_id: int, ranks: list[tuple[int, int]], rows_by_id: dict[int, dict],
                     warnings: list[str]) -> dict | None:
    missing = [sid for sid, _ in ranks if sid not in rows_by_id]
    if missing:
        warnings.append(f"chain {chain_id}: rank IDs {missing} not present in this class's CSV "
                         f"(check npc.csv / other files) - SKIPPED, needs manual handling")
        return None
    if len(ranks) < 2:
        return None  # single-rank chain, nothing to do

    rank_rows = []
    for sid, rank_num in ranks:
        r = rows_by_id[sid]
        r["_rank"] = rank_num
        rank_rows.append(r)
    rank1 = min(rank_rows, key=lambda r: r["_rank"])
    name = rank1.get("name", "")

    anchor, anchor_level, reason = pick_anchor(rank_rows, rank1)
    r1_learn = learn_level(rank1)

    changes = {"cast_time_ms": None, "mana_cost_pct": None, "mana_cost": None,
               "effects": {}, "raw_override_updates": {}, "new_effect_slots": []}

    # coefficient / cast_time / mana_cost_pct: max rank's value
    max_rank_row = max(rank_rows, key=lambda r: r["_rank"])
    new_cast_time = max_rank_row.get("cast_time_ms")
    if new_cast_time is not None and new_cast_time != rank1.get("cast_time_ms"):
        changes["cast_time_ms"] = new_cast_time

    new_mcp = max_rank_row.get("mana_cost_pct") or 0
    if new_mcp != (rank1.get("mana_cost_pct") or 0):
        changes["mana_cost_pct"] = new_mcp

    power_type = rank1.get("power_type") or 0
    if power_type == 0:
        if (rank1.get("mana_cost") or 0) != 0:
            changes["mana_cost"] = 0
    else:
        costs = {r.get("mana_cost") or 0 for r in rank_rows}
        if len(costs) > 1:
            warnings.append(f"chain {chain_id} ({name}): power_type={power_type} (non-mana) but "
                             f"flat mana_cost varies across ranks {sorted(costs)} - NOT auto-zeroed, "
                             f"needs manual decision")

    for i in (1, 2, 3):
        for r in rank_rows:
            eff = r.get(f"effect{i}")
            if eff and eff.get("type") in NONSCALING_TYPES:
                warnings.append(f"chain {chain_id} ({name}) effect{i} rank {r['_rank']}: "
                                 f"non-scaling effect type {eff.get('type')} "
                                 f"(CREATE_ITEM/ENCHANT_ITEM family) - left untouched")
        for r in rank_rows:
            eff = r.get(f"effect{i}")
            if eff and abs(eff.get("base_points", 0) or 0) > EMBEDDED_ID_THRESHOLD:
                dummy = eff.get("apply_aura") == SPELL_AURA_DUMMY
                warnings.append(f"chain {chain_id} ({name}) effect{i} rank {r['_rank']}: "
                                 f"base_points={eff.get('base_points')} exceeds "
                                 f"{EMBEDDED_ID_THRESHOLD}{' (SPELL_AURA_DUMMY - SKIPPED, resolve by name)' if dummy else ' (not SPELL_AURA_DUMMY - computed normally, but double-check by name)'}")

        rank1_eff = rank1.get(f"effect{i}")
        anchor_eff = anchor.get(f"effect{i}")

        if not rank1_eff and anchor_eff:
            # new effect slot introduced at a higher rank - find the first
            # rank that has it, copy verbatim (flat, ppl=0), per project default.
            introducer = min((r for r in rank_rows if r.get(f"effect{i}")),
                              key=lambda r: r["_rank"])
            new_eff = dict(introducer[f"effect{i}"])
            new_eff["points_per_level"] = 0.0
            changes["effects"][i] = new_eff
            changes["new_effect_slots"].append(i)
            warnings.append(f"chain {chain_id} ({name}): effect{i} first appears at rank "
                             f"{introducer['_rank']} (spell {introducer['id']}) - copied onto "
                             f"survivor flat; check raw_overrides for stale "
                             f"EffectBasePoints_{i}/EffectDieSides_{i}/etc keys that would shadow it")
            continue

        if not rank1_eff or not anchor_eff:
            continue

        eff_type = rank1_eff.get("type")
        if eff_type in NONSCALING_TYPES:
            continue
        if rank1_eff.get("apply_aura") == SPELL_AURA_DUMMY and (
                abs(rank1_eff.get("base_points", 0) or 0) > EMBEDDED_ID_THRESHOLD
                or abs(anchor_eff.get("base_points", 0) or 0) > EMBEDDED_ID_THRESHOLD):
            continue

        r1_val = rank1_eff.get("base_points", 0) or 0
        anchor_val = effect_value_at(anchor, i, anchor_level)
        if anchor_val is None:
            continue

        if anchor_val == r1_val:
            new_ppl = 0.0
        else:
            denom = anchor_level - r1_learn
            if denom == 0:
                warnings.append(f"chain {chain_id} ({name}) effect{i}: anchor_level == "
                                 f"rank1 learn level ({anchor_level}) but values differ - "
                                 f"zero-width anchor, SKIPPED (needs manual review)")
                continue
            new_ppl = (anchor_val - r1_val) / denom

        cur_ppl = rank1_eff.get("points_per_level", 0.0) or 0.0
        if abs(new_ppl - cur_ppl) > 1e-9:
            changes["effects"][i] = new_ppl

        # self-check from the playbook: anchor differs but slope computed 0
        if anchor_val != r1_val and new_ppl == 0.0:
            warnings.append(f"chain {chain_id} ({name}) effect{i}: anchor value "
                             f"({anchor_val}) != rank1 ({r1_val}) but computed slope is 0 - "
                             f"investigate (zero-width-anchor bug signature)")

    for i in (1, 2, 3):
        cur = ov(rank1, f"EffectBonusMultiplier_{i}", 0.0)
        newv = ov(max_rank_row, f"EffectBonusMultiplier_{i}", 0.0)
        if newv != cur:
            changes["raw_override_updates"][f"EffectBonusMultiplier_{i}"] = newv

    changes["raw_override_updates"]["MaxLevel"] = SYSTEM_MAX_LEVEL
    changes["raw_override_updates"]["NameSubtext_Lang_enUS"] = ""

    return {
        "chain_id": chain_id, "name": name, "rank1_id": rank1["id"],
        "ranks": sorted(r["_rank"] for r in rank_rows),
        "anchor_id": anchor["id"], "anchor_rank": anchor["_rank"],
        "anchor_level": anchor_level, "reason": reason,
        "r1_learn_level": r1_learn, "changes": changes, "rank1_row": rank1,
    }


def apply_changes(row: dict, result: dict) -> None:
    changes = result["changes"]
    if changes["cast_time_ms"] is not None:
        row["cast_time_ms"] = changes["cast_time_ms"]
    if changes["mana_cost_pct"] is not None:
        row["mana_cost_pct"] = changes["mana_cost_pct"]
    if changes["mana_cost"] is not None:
        row["mana_cost"] = changes["mana_cost"]
    for i, val in changes["effects"].items():
        if isinstance(val, dict):
            row[f"effect{i}"] = val
        else:
            row[f"effect{i}"]["points_per_level"] = val
    ro = dict(row.get("raw_overrides") or {})
    for i in changes.get("new_effect_slots", []):
        for key in ("EffectBasePoints", "EffectDieSides", "EffectRealPointsPerLevel",
                     "EffectAura", "EffectAuraPeriod", "EffectMiscValue", "EffectTriggerSpell",
                     "EffectChainTargets", "EffectRadiusIndex", "ImplicitTargetA",
                     "ImplicitTargetB", "EffectMechanic", "Effect"):
            stale_key = f"{key}_{i}"
            if stale_key in ro:
                del ro[stale_key]
    ro.update(changes["raw_override_updates"])
    row["raw_overrides"] = ro
    row.setdefault("notes", "")
    tag = "single-rank bootstrap"
    if tag not in (row.get("notes") or ""):
        note = (f"{tag}: BasePoints/BaseLevel/SpellLevel kept from rank 1 (learn level "
                f"{result['r1_learn_level']}); RealPointsPerLevel from rank1->{result['reason']} "
                f"(anchor rank {result['anchor_rank']} @ level {result['anchor_level']}); "
                f"coefficient/cast_time_ms/mana_cost_pct from max rank; MaxLevel set to 80")
        row["notes"] = (row["notes"] + "; " + note) if row["notes"] else note


def row_to_csv_dict(row: dict) -> dict:
    out = {}
    for field in SPELL_CSV_FIELDNAMES:
        v = row.get(field)
        if field in SPELL_CSV_JSON_FIELDS:
            out[field] = "" if not v else json.dumps(v, sort_keys=True)
        else:
            out[field] = "" if v is None else v
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("klass")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rows, index_by_id = load_class_rows(args.klass)
    rows_by_id = {r["id"]: r for r in rows}
    chains = load_spell_ranks_chains()

    warnings: list[str] = []
    results = []
    for chain_id, ranks in sorted(chains.items()):
        if chain_id not in rows_by_id and not any(sid in rows_by_id for sid, _ in ranks):
            continue  # not this class's chain at all
        res = bootstrap_chain(chain_id, ranks, rows_by_id, warnings)
        if res:
            results.append(res)

    print(f"=== {args.klass}: {len(results)} multi-rank chain(s) to bootstrap ===\n")
    for res in results:
        c = res["changes"]
        print(f"- {res['name']} (survivor {res['rank1_id']}, ranks {res['ranks']}): "
              f"anchor=rank {res['anchor_rank']} (id {res['anchor_id']}) @ level "
              f"{res['anchor_level']} [{res['reason']}], rank1 learn_level={res['r1_learn_level']}")
        for i, val in c["effects"].items():
            if isinstance(val, dict):
                print(f"    effect{i}: NEW SLOT copied -> {val}")
            else:
                print(f"    effect{i}: ppl -> {val:.4f}")
        if c["cast_time_ms"] is not None:
            print(f"    cast_time_ms -> {c['cast_time_ms']}")
        if c["mana_cost_pct"] is not None:
            print(f"    mana_cost_pct -> {c['mana_cost_pct']}")
        if c["mana_cost"] is not None:
            print(f"    mana_cost -> {c['mana_cost']}")
        for k, v in c["raw_override_updates"].items():
            if k in ("MaxLevel", "NameSubtext_Lang_enUS"):
                continue
            print(f"    raw_overrides.{k} -> {v}")

    if warnings:
        print(f"\n=== {len(warnings)} warning(s) - review before trusting the output ===")
        for w in warnings:
            print(f"  ! {w}")

    if args.dry_run:
        print("\n--dry-run: no files written")
        return 0

    for res in results:
        apply_changes(res["rank1_row"], res)

    path = SPELLS_DIR / f"{args.klass}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SPELL_CSV_FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow(row_to_csv_dict(row))
    print(f"\nwrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
