#!/usr/bin/env python3
"""
Seeds and checks `source/items/quest_rewards.lock` (quest reward itemization, lib/quest_rewards.py).

    python3 apps/dbc-tools/quest_rewards_lock.py                        # dry run: counts, what a seed would append
    python3 apps/dbc-tools/quest_rewards_lock.py --seed-quest-rewards   # append the missing lines to the lock
    python3 apps/dbc-tools/quest_rewards_lock.py --json out.json        # every decision and skip, for a report

Read-only on everything but the lock (and the `--json` file). The lock is append-only: a seed run appends a line for
every in-scope item without one and never rewrites or removes a line, so hand edits stay. A locked entry that has left
the scope is listed, not removed.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_ROOT))

from lib import quest_rewards as qr  # noqa: E402


def _summary(scoped: qr.Scope, decisions: list[qr.Decision]) -> list[str]:
    out = [f"in scope: {len(decisions)} item(s); skipped: {len(scoped.skipped)}"]
    by_quality = collections.Counter(f"{qr.QUALITY_NAMES[d.stock_quality]}->{qr.QUALITY_NAMES[d.quality]}"
                                     for d in decisions)
    out.append("by quality: " + ", ".join(f"{k} {v}" for k, v in sorted(by_quality.items())))
    skips = collections.Counter(reason.split(" (")[0] if not reason.startswith("owned") else "owned elsewhere"
                                for reason in scoped.skipped.values())
    out.append("skipped: " + ", ".join(f"{k} {v}" for k, v in sorted(skips.items())))
    fallbacks = collections.Counter(f for d in decisions for f in d.fallbacks)
    for text, count in sorted(fallbacks.items(), key=lambda kv: -kv[1]):
        out.append(f"fallback x{count}: {text}")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seed-quest-rewards", action="store_true", help="append the missing lines to the lock")
    parser.add_argument("--json", type=Path, help="write every decision and skip to this JSON file")
    args = parser.parse_args(argv)

    inputs = qr.load_inputs()
    owned = qr.owned_elsewhere()
    scoped, decisions = qr.run(inputs, owned)
    current = qr.LOCK_PATH.read_text(encoding="utf-8") if qr.LOCK_PATH.is_file() else ""
    text, appended, stale = qr.seed(current, decisions, inputs.catalog)
    for line in _summary(scoped, decisions):
        print(line)
    for entry in stale:
        print(f"NOTE: locked entry {entry} is no longer in scope ({scoped.skipped.get(entry, 'not a quest reward')})"
              f"; its line stays (delete it by hand to hand the entry back)")
    if args.json:
        payload = {
            "decisions": [{
                "entry": d.entry, "name": d.name, "quest_level": d.quest_level,
                "quests": [[q.id, q.level, q.title, q.kind] for q in d.quests],
                "stock_quality": d.stock_quality, "stock_ilvl": d.stock_ilvl, "quality": d.quality, "ilvl": d.ilvl,
                "primary": d.primary, "secondary": d.secondary, "share": d.share, "kept": list(d.kept),
                "absorbed": list(d.absorbed), "stock": {str(k): v for k, v in d.stock.items()},
                "stock_line": qr.format_stats(d.stock), "paths": d.paths, "fallbacks": d.fallbacks,
                "class": inputs.rows[d.entry]["class"], "subclass": inputs.rows[d.entry]["subclass"],
                "inv_type": inputs.rows[d.entry]["InventoryType"],
            } for d in decisions],
            "skipped": {str(k): v for k, v in sorted(scoped.skipped.items())},
            "skipped_names": {str(k): inputs.rows[k]["name"] for k in scoped.skipped},
        }
        args.json.write_text(json.dumps(payload, indent=1), encoding="utf-8")
        print(f"wrote {args.json}")
    if args.seed_quest_rewards:
        if appended:
            qr.LOCK_PATH.write_text(text, encoding="utf-8")
        print(f"{qr.LOCK_PATH.name}: appended {len(appended)} line(s)")
    else:
        print(f"{qr.LOCK_PATH.name}: a seed run would append {len(appended)} line(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
