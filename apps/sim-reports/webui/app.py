#!/usr/bin/env python3
"""
sim-reports web viewer - lists and renders modules/mod-dpssim's DPS-sim report JSON files
(SimReport::WriteJson()'s schema, one per modules/mod-dpssim/tools/run-sim.sh run) without needing
to hunt through modules/mod-dpssim/reports/ by hand or re-run a sim just to see a past result.

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

# run-sim.sh's reports always end up named "<Profile>.<YYYYMMDD-HHMMSS>.report.json" - see its own
# FINAL_PATH construction. Sorting on the timestamp group (a plain string) sorts newest-first
# correctly without parsing it into a real datetime, since the format is fixed-width and zero-padded.
REPORT_FILENAME_RE = re.compile(r"^(?P<profile>.+)\.(?P<timestamp>\d{8}-\d{6})\.report\.json$")


def _list_reports() -> list[dict]:
    if not REPORTS_DIR.is_dir():
        return []

    runs = []
    for path in REPORTS_DIR.glob("*.report.json"):
        m = REPORT_FILENAME_RE.match(path.name)
        if not m:
            continue
        try:
            data = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            runs.append({"filename": path.name, "profile": m["profile"], "timestamp": m["timestamp"],
                         "error": str(exc)})
            continue
        summary = data.get("summary", {})
        config = data.get("config", {})
        runs.append({
            "filename": path.name, "profile": m["profile"], "timestamp": m["timestamp"],
            "error": None, "dps": summary.get("dps"), "total_damage": summary.get("totalDamage"),
            "cast_count": summary.get("castCount"), "crit_rate_pct": summary.get("critRatePct"),
            "duration_ms": config.get("durationMs"),
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
    )


@bp.route("/latest")
def latest():
    if not LATEST_HTML_PATH.is_file():
        abort(404, "No baked report yet - run modules/mod-dpssim/tools/run-sim.sh first.")
    return send_file(LATEST_HTML_PATH)


@bp.route("/view/<path:filename>")
def view(filename: str):
    report_path = _resolve_report_path(filename)
    data = json.loads(report_path.read_text())
    m = REPORT_FILENAME_RE.match(filename)
    label = f"{m['profile']} ({m['timestamp']})" if m else filename
    html = build_report_html.render_report_html(data, label)
    return html


@bp.route("/raw/<path:filename>")
def raw(filename: str):
    return send_file(_resolve_report_path(filename), mimetype="application/json")


if __name__ == "__main__":
    app = Flask(__name__)
    app.register_blueprint(bp)
    app.run(host="0.0.0.0", port=8602, debug=False)
