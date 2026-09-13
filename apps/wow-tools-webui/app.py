#!/usr/bin/env python3
"""
wow-tools web editor — combines apps/dbc-tools/webui, apps/item-tools/webui, and
apps/sim-reports/webui into a single Flask process, mounted as Blueprints under
/dbc/, /items/, and /reports/. Each tool's own app.py still defines everything
about that tool (routes, templates, static files); this module only loads the
three as Blueprints and serves them side by side, so there's one
process/port/systemd unit instead of three. See each tool's own README
(apps/dbc-tools/README.md, apps/item-tools/README.md, apps/sim-reports/README.md)
for what the tools themselves do.

Single-user LAN tool, same as both of its parts: no auth, no JS build step.
Run with:
  python3 apps/wow-tools-webui/app.py
and reach it from any machine on the same network at
http://<this machine's LAN IP>:8600/ — it binds 0.0.0.0 on purpose. There's
no login, so anyone who can reach the port can edit dbc-tools' source files
and write item-tools' pending SQL migrations; keep it on a trusted home
network, not port-forwarded to the internet.

Why importlib instead of a plain `import`: all three tools' directories
(apps/dbc-tools, apps/item-tools, apps/sim-reports) have hyphens in their
names, which aren't valid in a dotted Python import path. Loading each app.py
by file path sidesteps that without renaming any tool's directory.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
APPS_DIR = REPO_ROOT / "apps"


def _load_module(name: str, file_path: Path) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, file_path)
    module = importlib.util.module_from_spec(spec)
    # Register in sys.modules *before* exec_module: Flask's Blueprint(name,
    # __name__, ...) call inside the loaded file looks itself up there
    # (via flask.helpers.get_root_path) to find its own directory for
    # template_folder/static_folder - it has to already be findable under
    # this name while the module body is still running.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# dbc-tools/webui/app.py does bare `import gamedata` / `import view_models`,
# relying on being run as __main__ (which makes Python auto-add the script's
# own directory to sys.path). We're importing it as a regular module instead,
# so add that directory explicitly before loading it. Its own
# `sys.path.insert(0, TOOL_ROOT)` line (for `from lib import ...`) runs as
# part of the module body below and needs no help.
sys.path.insert(0, str(APPS_DIR / "dbc-tools" / "webui"))
dbc_app = _load_module("dbc_webui_app", APPS_DIR / "dbc-tools" / "webui" / "app.py")

# item-tools/webui/app.py only imports its own item_lib package, and its own
# `sys.path.insert(0, TOOL_ROOT)` line already makes that resolvable once the
# module executes - nothing extra needed here.
item_app = _load_module("item_webui_app", APPS_DIR / "item-tools" / "webui" / "app.py")

# sim-reports/webui/app.py only imports modules/mod-dpssim/tools/build_report_html.py, which it
# loads by file path itself (mirroring this file's own trick) - nothing extra needed here either.
reports_app = _load_module("reports_webui_app", APPS_DIR / "sim-reports" / "webui" / "app.py")

from flask import Flask, render_template  # noqa: E402

app = Flask(__name__)
app.secret_key = "wow-tools-webui"  # local single-user tool, not internet-facing
app.register_blueprint(dbc_app.bp, url_prefix="/dbc")
app.register_blueprint(item_app.bp, url_prefix="/items")
app.register_blueprint(reports_app.bp, url_prefix="/reports")


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8600, debug=False)
