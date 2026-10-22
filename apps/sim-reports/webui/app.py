#!/usr/bin/env python3
"""
sim-reports web viewer - lists and renders modules/mod-dpssim's DPS-sim report JSON files
(SimReport::WriteJson()'s schema, one per modules/mod-dpssim/tools/run-sim.sh run) without needing
to hunt through modules/mod-dpssim/reports/ by hand or re-run a sim just to see a past result.

Heal-mode reports ("kind": "heal", SimReport::WriteHealJson()) are listed beside the DPS ones and rendered through the
heal template (build_report_html.render_report_html() picks the template by kind). Tank reports ("kind": "tank",
SimReport::WriteTankJson()) are DPS reports with a tank section: listed with their scenario and headline (DPS and TPS,
or time to death and net DTPS) and rendered through the DPS template plus the "Damage taken" section.

Does no templating of its own for the report page itself - it imports
render_report_html()/fetch_spell_names() straight from
modules/mod-dpssim/tools/build_report_html.py (the same code run-sim.sh uses to bake
SimProfileReport.html) so there is exactly one place that knows how to turn a report JSON into a
page, and viewing a report here always looks identical to opening the baked file directly.

Single-user LAN tool, same as apps/dbc-tools and apps/item-tools: no auth, no JS build step.
Normally served as part of apps/wow-tools-webui (this module only defines the `reports` Blueprint;
see that app's app.py for how it's mounted and run) at /reports/ on whatever host serves that
combined app.

Can still be run standalone for quick dev/debugging:
  python3 apps/sim-reports/webui/app.py
reachable at http://<this machine's LAN IP>:8602/ (unprefixed, since nothing else is mounted
alongside it).
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
import types
from pathlib import Path

from flask import Blueprint, Flask, abort, render_template, send_file

REPO_ROOT = Path(__file__).resolve().parents[3]
REPORTS_DIR = REPO_ROOT / "modules" / "mod-dpssim" / "reports"
BUILD_SCRIPT_PATH = REPO_ROOT / "modules" / "mod-dpssim" / "tools" / "build_report_html.py"
LATEST_HTML_PATH = REPORTS_DIR / "SimProfileReport.html"
LATEST_HEAL_HTML_PATH = REPORTS_DIR / "HealProfileReport.html"
LATEST_TANK_HTML_PATH = REPORTS_DIR / "TankProfileReport.html"

# modules/mod-dpssim has a hyphen, so it can't be a normal dotted import target - load
# build_report_html.py by file path instead, same trick apps/wow-tools-webui/app.py uses for
# dbc-tools/item-tools.
def _load_build_report_html() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("dpssim_build_report_html", BUILD_SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["dpssim_build_report_html"] = module
    spec.loader.exec_module(module)
    return module


build_report_html = _load_build_report_html()

bp = Blueprint("reports", __name__, template_folder="templates", static_folder="static")

# run-sim.sh's reports end up named "<Profile>.<YYYYMMDD-HHMMSS>.report.json", or
# "<Profile>.T<N>.<YYYYMMDD-HHMMSS>.report.json" for an N > 1 target run, or, for a heal run,
# "<Profile>.<group>.<tag>.<YYYYMMDD-HHMMSS>.report.json" (group party|raid10|raid20, tag e.g. pin50, drain150,
# x1a2b3c or pin50-inf), or, for a tank run, "<Profile>.tank-<scenario>.<N>t[.x<hash>].<YYYYMMDD-HHMMSS>.report.json"
# (scenario dps|survive, N dummies, x<hash> when TANKSIM_HIT / TANKSIM_PACK_HIT / TANKSIM_SWING_MS overrode the
# profile) - see its own BATCH_NAME construction.
# Sorting on the timestamp group (a plain string) sorts newest-first
# correctly without parsing it into a real datetime, since the format is fixed-width and zero-padded.
REPORT_FILENAME_RE = re.compile(
    r"^(?P<profile>.+?)"
    r"(?:\.T(?P<targets>\d+)|\.(?P<group>party|raid10|raid20)\.(?P<tag>[A-Za-z0-9_-]+)"
    r"|\.tank-(?P<scenario>dps|survive)\.(?P<tank_targets>\d+)t(?:\.(?P<tank_tag>x[0-9a-f]{6}))?)?"
    r"\.(?P<timestamp>\d{8}-\d{6})\.report\.json$")


def _tank_row(filename: str, m: re.Match, data: dict) -> dict:
    """A listing row of a tank report: the scenario and the headline (dps: DPS and TPS; survive: time to death and net
    DTPS). An aggregated report's numbers are its trimmed means."""
    summary = data.get("summary", {})
    config = data.get("config", {})
    tank = (data.get("tank") or {}).get("summary", {})
    agg = data.get("aggregate") or {}
    scenario = tank.get("scenario") or m["scenario"]
    ttd = tank.get("ttdMs")
    if scenario == "survive" and ttd is not None:
        headline = f"TTD {ttd / 1000:.1f} s"
        if agg:
            headline += f" (survived {agg.get('tank', {}).get('survivedCount', 0)}/{agg.get('iterations', 1)})"
        elif tank.get("survived"):
            headline += " (survived)"
        headline += f" \u00b7 net DTPS {tank.get('netDtps', 0):.0f}"
    else:
        headline = f"DPS {summary.get('dps', 0):.1f} \u00b7 TPS {tank.get('tps', 0):.1f}"
    if agg:
        deaths = agg.get("tank", {}).get("diedCount")
    else:
        deaths = 1 if tank.get("died") else 0
    return {
        "filename": filename, "profile": m["profile"], "timestamp": m["timestamp"], "error": None, "kind": "tank",
        "scenario": scenario, "headline": headline, "rate": summary.get("dps"), "total": summary.get("totalDamage"),
        "cast_count": summary.get("castCount"), "crit_rate_pct": summary.get("critRatePct"), "deaths": deaths,
        "duration_ms": config.get("durationMs"), "iterations": agg.get("iterations", 1),
        "tag": m["tank_tag"], "targets": config.get("targetCount", int(m["tank_targets"] or 1)),
        "target_rank": config.get("targetRank", "boss"),
    }


def _list_reports() -> list[dict]:
    if not REPORTS_DIR.is_dir():
        return []

    runs = []
    for path in REPORTS_DIR.glob("*.report.json"):
        m = REPORT_FILENAME_RE.match(path.name)
        if not m:
            continue
        heal_name = m["group"] is not None
        tank_name = m["scenario"] is not None
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            runs.append({"filename": path.name, "profile": m["profile"], "timestamp": m["timestamp"],
                         "kind": "heal" if heal_name else ("tank" if tank_name else "dps"), "group": m["group"],
                         "tag": m["tag"] or m["tank_tag"], "scenario": m["scenario"],
                         "targets": int(m["targets"] or m["tank_targets"] or 1), "target_rank": "boss",
                         "error": str(exc)})
            continue
        summary = data.get("summary", {})
        config = data.get("config", {})
        if data.get("kind") == "heal":
            agg = data.get("aggregate") or {}
            # An aggregated report's deaths tile is the mean over every run; a single run's is its own count
            deaths = agg.get("meanDeaths", summary.get("deaths"))
            runs.append({
                "filename": path.name, "profile": m["profile"], "timestamp": m["timestamp"], "error": None,
                "kind": "heal", "group": config.get("group") or m["group"], "tag": m["tag"],
                "infinite_mana": bool(config.get("infiniteMana")),
                "rate": summary.get("hps"),
                "total": (summary.get("effectiveHealing", 0) + summary.get("absorbHealing", 0))
                if "effectiveHealing" in summary else None,
                "cast_count": summary.get("castCount"), "crit_rate_pct": summary.get("critRatePct"),
                "deaths": deaths, "duration_ms": config.get("durationMs"), "iterations": agg.get("iterations", 1),
            })
            continue
        if data.get("kind") == "tank":
            runs.append(_tank_row(path.name, m, data))
            continue
        runs.append({
            "filename": path.name, "profile": m["profile"], "timestamp": m["timestamp"],
            "error": None, "kind": "dps", "rate": summary.get("dps"), "total": summary.get("totalDamage"),
            "cast_count": summary.get("castCount"), "crit_rate_pct": summary.get("critRatePct"),
            "duration_ms": config.get("durationMs"), "deaths": None,
            # reports from before multi-target support carry neither field: 1 boss dummy
            "targets": config.get("targetCount", int(m["targets"] or 1)),
            "target_rank": config.get("targetRank", "boss"),
        })
    runs.sort(key=lambda r: r["timestamp"], reverse=True)
    return runs


# Only ever serves a filename this same glob already found on disk - closes off path traversal via
# the URL without needing to sanity-check `..`/absolute-path segments by hand.
def _resolve_report_path(filename: str) -> Path:
    for path in REPORTS_DIR.glob("*.report.json"):
        if path.name == filename:
            return path
    abort(404)


@bp.route("/")
def index():
    return render_template(
        "reports/index.html", runs=_list_reports(), has_latest=LATEST_HTML_PATH.is_file(),
        has_latest_heal=LATEST_HEAL_HTML_PATH.is_file(), has_latest_tank=LATEST_TANK_HTML_PATH.is_file(),
    )


@bp.route("/latest")
def latest():
    if not LATEST_HTML_PATH.is_file():
        abort(404, "No baked report yet - run modules/mod-dpssim/tools/run-sim.sh first.")
    return send_file(LATEST_HTML_PATH)


@bp.route("/latest-heal")
def latest_heal():
    if not LATEST_HEAL_HTML_PATH.is_file():
        abort(404, "No baked heal report yet - run modules/mod-dpssim/tools/run-sim.sh on a heal profile first.")
    return send_file(LATEST_HEAL_HTML_PATH)


@bp.route("/latest-tank")
def latest_tank():
    if not LATEST_TANK_HTML_PATH.is_file():
        abort(404, "No baked tank report yet - run modules/mod-dpssim/tools/run-sim.sh on a tank profile first.")
    return send_file(LATEST_TANK_HTML_PATH)


@bp.route("/view/<path:filename>")
def view(filename: str):
    report_path = _resolve_report_path(filename)
    data = json.loads(report_path.read_text())
    m = REPORT_FILENAME_RE.match(filename)
    label = f"{m['profile']} ({m['timestamp']})" if m else filename
    n = data.get("config", {}).get("targetCount") or (m and m["targets"])
    if m and n and int(n) > 1:
        label = f"{m['profile']} T{n} ({m['timestamp']})"
    if m and m["scenario"]:
        # a tank report (the DPS template plus the Damage taken section, chosen by render_report_html)
        tag = f" {m['tank_tag']}" if m["tank_tag"] else ""
        label = f"{m['profile']} tank {m['scenario']} T{m['tank_targets']}{tag} ({m['timestamp']})"
    if m and m["group"]:
        # a heal report (rendered through the heal template by render_report_html)
        label = f"{m['profile']} {m['group']} {m['tag']} ({m['timestamp']})"
    html = build_report_html.render_report_html(data, label)
    return html


@bp.route("/raw/<path:filename>")
def raw(filename: str):
    return send_file(_resolve_report_path(filename), mimetype="application/json")


if __name__ == "__main__":
    app = Flask(__name__)
    app.register_blueprint(bp)
    app.run(host="0.0.0.0", port=8602, debug=False)
