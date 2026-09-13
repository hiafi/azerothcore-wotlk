# wow-tools-webui

One Flask process that serves [apps/dbc-tools/webui](../dbc-tools/README.md#web-ui),
[apps/item-tools/webui](../item-tools/README.md#setup), and
[apps/sim-reports/webui](../sim-reports/README.md) side by side under one port,
instead of each running as its own process/port:

- `/dbc/` — dbc-tools (source/spells, source/talents, DBC generation)
- `/items/` — item-tools (item_template browser/editor, itemization, loot)
- `/reports/` — sim-reports (mod-dpssim DPS-sim report browser)

Each tool's own `webui/app.py` still owns everything about that tool (routes,
templates, static files, `README.md`) — this app only imports the three as
Flask Blueprints (`apps/dbc-tools/webui/app.py`'s `bp`, `apps/item-tools/webui/app.py`'s
`bp`, `apps/sim-reports/webui/app.py`'s `bp`) and registers them under those
three prefixes. Read the tool's own README for what it does; read `app.py`
here only for how the three are wired together.

Each tool's `webui/app.py` can still be run standalone (unprefixed, on its
original port — 8600 for dbc-tools, 8601 for item-tools, 8602 for
sim-reports) for quick dev/debugging without going through this combined
app; see the "Can still be run standalone" note in each one's module
docstring.

## Running it

```
pip install -r apps/wow-tools-webui/requirements.txt
python3 apps/wow-tools-webui/app.py
```

Open `http://localhost:8600/`, or `http://<this machine's LAN IP>:8600/` from
any other device on the same network — it binds `0.0.0.0` on purpose. Same
caveat as both tools it wraps: there's no login, so anyone who can reach that
port can edit dbc-tools' source files and write item-tools' pending SQL
migrations; keep it on a trusted home network, not port-forwarded to the
internet.

In production this runs as the `wow-tools-webui` systemd service (replaces
the old separate `dbc-webui`/`item-tools-webui` services).

## Why this needed more than "mount two Flask apps"

Both tools were originally standalone `webui/app.py` scripts, each assuming
it was the only Flask app in the process. Combining them into one process
surfaced three collisions that had to be fixed in each tool, not just here:

- **A shared `lib` package name.** Both tools have their own `lib/` package
  (`from lib import ...`). Importing both into the same process would make
  the second import shadow the first. item-tools' was renamed to `item_lib/`
  (the smaller of the two - only `webui/app.py` imported it) to make the two
  unambiguous; dbc-tools' stayed `lib/`.
- **Colliding endpoint names and template names.** Each tool's `app.py` is
  now a `Blueprint` (`dbc`, `items`) instead of its own `Flask` app, mounted
  here under `/dbc` and `/items`. Every `url_for(...)` call inside each
  tool's own code/templates was changed to the relative form
  (`url_for('.spell_list', ...)` instead of `url_for('spell_list', ...)`) so
  it keeps resolving correctly regardless of which prefix it's mounted
  under. Each tool's templates were also moved into a subdirectory matching
  its Blueprint name (`templates/dbc/`, `templates/items/`) - both tools had
  a `base.html` and an `index.html`, and Flask's Jinja loader doesn't
  auto-namespace Blueprint template folders, so two same-named templates in
  one process would silently collide (whichever Blueprint's copy loads
  first wins for *both* tools).
- **A couple of hardcoded absolute-path `fetch()` calls** in dbc-tools'
  inline `<script>` blocks (`/api/icon-url/...`, `/api/spell-info/...`) —
  these assumed the app was mounted at `/`. Fixed by rendering the real,
  prefix-aware URL through Jinja's `url_for(...)` once per page and
  swapping in the actual id at call time, instead of hand-building the path
  in JS.

Hyphens in `dbc-tools`/`item-tools` (invalid in a dotted Python import) meant
this app loads each `webui/app.py` by file path via `importlib.util`, rather
than a plain `from apps.dbc_tools.webui import app` — see `app.py`'s
docstring.
