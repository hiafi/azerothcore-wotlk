# sim-reports

A small local web UI that lists and renders `modules/mod-dpssim`'s DPS-sim report runs -
the JSON files `modules/mod-dpssim/tools/run-sim.sh` writes to `modules/mod-dpssim/reports/`,
one per run. Read-only: this tool doesn't run sims, edit anything, or touch the live
database itself - it exists so a past run is a click away in a browser instead of a
`find`/`ls` through the reports folder.

## Why this isn't its own templating engine

The actual report page (charts, tables, spell-name resolution) is one thing:
`modules/mod-dpssim/tools/report-template.html`, filled in by
`modules/mod-dpssim/tools/build_report_html.py`'s `render_report_html()`. This app imports
that function directly (loaded by file path - `mod-dpssim` has a hyphen, so it can't be a
normal dotted import) rather than re-implementing or shelling out to it, so a report viewed
here always renders identically to the baked `SimProfileReport.html` file `run-sim.sh`
produces. See that script's own doc comment for how spell/buff names get resolved from the
live world DB.

## Routes (mounted at `/reports/` under apps/wow-tools-webui)

- `/` - table of every `<Profile>.<timestamp>.report.json` under
  `modules/mod-dpssim/reports/`, newest first, with each run's DPS/total damage/cast
  count/crit rate read straight from its `summary` block.
- `/view/<filename>` - renders one report through the shared template, on demand (no file
  written to disk - this is a GET, not a rebuild of `SimProfileReport.html`).
- `/raw/<filename>` - the underlying report JSON, unmodified.
- `/latest` - the most recently baked `SimProfileReport.html`, served as-is, if one exists.

## Running it

Normally served as part of `apps/wow-tools-webui` (`python3 apps/wow-tools-webui/app.py`,
then `http://<host>:8600/reports/`). Can also run standalone for quick debugging:

```
pip install -r apps/sim-reports/requirements.txt
python3 apps/sim-reports/webui/app.py
```

reachable at `http://<this machine's LAN IP>:8602/` (unprefixed, since nothing else is
mounted alongside it). Same caveat as the rest of `wow-tools-webui`: no auth, LAN-only.
