#!/usr/bin/env python3
"""
Bakes one mod-dpssim report JSON file (SimReport::WriteJson()'s schema) directly into a copy of
report-template.html - no file picker, no "load report" click needed, the page just shows the
data the moment it's opened. Used by run-sim.sh; not usually invoked by hand.

Usage:
    build_report_html.py <output.html> <label> <report.json>
"""

from __future__ import annotations

import datetime
import json
import subprocess
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = TOOLS_DIR / "report-template.html"


def safe_json(obj) -> str:
    # Guard against a "</script>" sequence inside the data breaking out of the embedding
    # <script type="application/json"> tag early - can't happen with this schema today (no
    # free-text fields), but cheap insurance if that ever changes.
    return json.dumps(obj).replace("</", "<\\/")


def collect_spell_ids(data: dict) -> list[int]:
    ids: set[int] = set()
    for s in data.get("spells", []):
        ids.add(s["spellId"])
    for h in data.get("hits", []):
        ids.add(h["spellId"])
    for e in data.get("auraEvents", []):
        ids.add(e["spellId"])
    for c in data.get("casts", []):
        ids.add(c["spellId"])
    return sorted(ids)


# Looks up real spell names from the live deployment's own world DB, per SimReport.h's design note
# that name resolution belongs here (report-build time) rather than inside the sim process itself.
# report-template.html still carries a small hand-curated SPELL_NAMES override table (for cosmetic
# relabeling like "Arcane Blast (stack)" vs the DBC's plain "Arcane Blast") - this is the fallback
# underneath it, so any id the curated table doesn't cover (e.g. new talents/procs as the rework
# grows) still gets its real name instead of a bare "Spell #id".
#
# Shells out to `docker exec` rather than a MySQL client library (none vendored here, and this is a
# one-shot lookup, not worth the dependency) - discovers the live worldserver container the same
# way run-sim.sh does (AC_WORLD_DATABASE_INFO env var, for db name/user/pass) and finds the actual
# DB container via its compose service label rather than assuming a container name, since a
# `docker compose up` recreate can leave it running under a temporary hash-prefixed name (observed
# on this deployment - see docs/bugs-and-fixes.md if this ever needs re-explaining).
# Best-effort: any failure (docker unavailable, containers not running, query error) logs a warning
# to stderr and returns an empty map rather than failing the whole report build - name lookup is an
# enrichment, not a hard requirement for a usable report.
def fetch_spell_names(spell_ids: list[int]) -> dict[int, str]:
    if not spell_ids:
        return {}

    try:
        env_lines = subprocess.run(
            ["docker", "inspect", "ac-worldserver", "--format", "{{range .Config.Env}}{{println .}}{{end}}"],
            capture_output=True, text=True, check=True, timeout=10,
        ).stdout.splitlines()
        db_info = next(line.split("=", 1)[1] for line in env_lines if line.startswith("AC_WORLD_DATABASE_INFO="))
        _host, _port, user, password, dbname = db_info.split(";")

        db_container = subprocess.run(
            ["docker", "ps", "--filter", "label=com.docker.compose.service=ac-database", "--format", "{{.Names}}"],
            capture_output=True, text=True, check=True, timeout=10,
        ).stdout.strip().splitlines()
        if not db_container:
            print("build_report_html.py: no running ac-database container found - spell names will "
                  "fall back to \"Spell #id\".", file=sys.stderr)
            return {}

        id_list = ",".join(str(i) for i in spell_ids)
        query = f"SELECT ID, Name_Lang_enUS FROM {dbname}.spell_dbc WHERE ID IN ({id_list});"
        rows = subprocess.run(
            ["docker", "exec", db_container[0], "mysql", f"-u{user}", f"-p{password}", "-N", "-B", "-e", query],
            capture_output=True, text=True, check=True, timeout=20,
        ).stdout

        names: dict[int, str] = {}
        for line in rows.splitlines():
            spell_id_str, _, name = line.partition("\t")
            if name and name != "NULL":
                names[int(spell_id_str)] = name
        return names
    except Exception as exc:  # noqa: BLE001 - best-effort enrichment, see doc comment above
        print(f"build_report_html.py: spell-name lookup failed ({exc}) - falling back to \"Spell #id\".",
              file=sys.stderr)
        return {}


# The actual templating step, factored out of main() so apps/sim-reports/webui/app.py can render a
# report on the fly (viewing a past run's JSON) without shelling out to this script or duplicating
# its DB-lookup/placeholder-substitution logic - this is the one place that logic lives.
def render_report_html(data: dict, label: str) -> str:
    spell_names = fetch_spell_names(collect_spell_ids(data))
    html = TEMPLATE_PATH.read_text()
    return (
        html.replace("__PAGE_TITLE__", label)
        .replace("__LABEL__", label)
        .replace("__DATA_JSON__", safe_json(data))
        .replace("__SPELL_NAMES_JSON__", safe_json(spell_names))
        .replace("__GENERATED_AT__", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__, file=sys.stderr)
        return 1

    out_path = Path(sys.argv[1])
    label = sys.argv[2]
    report_path = Path(sys.argv[3])

    data = json.loads(report_path.read_text())
    html = render_report_html(data, label)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
