# dbc-tools

DBCs as generated build artifacts, not hand-edited files. See
`docs/dbc-build-pipeline.md` for the full design decision and rationale;
this file is just usage.

## Why this works the way it does

AzerothCore already loads `Spell.dbc`, `Talent.dbc`, `TalentTab.dbc`, and
several secondary spell DBCs by reading the client binary file and then
**overlaying a same-named world-DB table on top, row by row, by ID**
(`DBCDatabaseLoader`). That means a new spell or talent is fully live
server-side from SQL alone — the binary `.dbc` only matters for what the
*client* renders (name, icon, tooltip, talent frame). So this tool has two
genuinely separate outputs:

1. **SQL** (`data/sql/updates/pending_db_world/rev_*.sql`) — load-bearing,
   sufficient for the server by itself.
2. **A client patch** — cosmetic-but-necessary, built by patching a
   complete copy of the stock client DBC (base + our rows), since the
   client loads a whole file per archive, not a row-level merge like the
   server does.

New content lives in reserved ID blocks (`source/ids.yaml`) so it never
collides with stock data or with another ticket's IDs.

## Setup

```
pip install -r apps/dbc-tools/requirements.txt
```

Optional but needed for real client-patch output: extract `Spell.dbc`,
`Talent.dbc`, `TalentTab.dbc`, `SpellCastTimes.dbc`, `SpellDuration.dbc`,
`SpellRange.dbc`, `SpellRadius.dbc` from your client's `DBFilesClient\`
(inside the locale MPQs, e.g. `Data/enUS/patch-enUS-3.MPQ`) into
`var/extractors/dbc/`. Without these, `generate.py` still produces correct
SQL (the server doesn't need them), it just skips producing a client patch
for whichever files aren't there, and `reuse.py` mints fresh IDs from the
reserved blocks instead of reusing matching stock rows.

## Generating

```
python3 apps/dbc-tools/generate.py
```

Reads `source/ids.yaml` plus every file under `source/spells/*.csv` and
`source/talents/*.yaml` (merged together — see "Source files" below for why
they're split), and produces:
- a new pending SQL migration (only if something changed — the file is
  skipped entirely otherwise);
- `var/dbc-patch/DBFilesClient/*.dbc` (loose files, for dev iteration) and
  `var/dbc-patch/patch-Z.mpq` (an MPQ, for release-style distribution) —
  both, always, for whichever tables had a base file to patch;
- the same bytes into `env/dist/data/dbc/` if that directory exists.

Running it twice with unchanged source produces byte-identical output
(diff the pending SQL / patch files to confirm) — that's what makes this a
generator rather than a one-off script.

## Pulling existing data in

```
python3 apps/dbc-tools/pull.py --spell 116,133          # explicit IDs
python3 apps/dbc-tools/pull.py --spell 100-200           # inclusive range
python3 apps/dbc-tools/pull.py --spell 100 --dest npc    # force a destination file
python3 apps/dbc-tools/pull.py --all                     # every existing
                                                          # spell_dbc row —
                                                          # also the tool's
                                                          # own round-trip
                                                          # self-test
```

Appends rows to the matching file under `source/spells/` for IDs not
already present anywhere in that directory. The destination file is
auto-detected from the spell's `SpellClassSet` (`SPELLFAMILY_*` in
`src/server/shared/SharedDefines.h` — see `SPELLFAMILY_TO_FILE` in
`pull.py`) unless `--dest` overrides it; anything with no player class
(generic/potion/pet effects, or an unrecognized value) falls back to
`generic.csv`. Override with `--dest` when auto-detect isn't what you want —
e.g. a boss ability that happens to share a player class's `SpellClassSet`
usually belongs in `npc.csv`, not that class's file.

Useful for two things: seeding a real spell (e.g. Frostbolt, which
auto-routes to `mage.csv`) as an editable starting point before reworking
it, and validating the pipeline itself (`--all` reverses every existing
row, rebuilds it, and — if you add that check back in, see
`lib/reverse.py`'s docstring — diffs it against the original; this was run
once over all ~54k merged base+overlay spell rows during development with
zero mismatches).

## Source files

- `source/ids.yaml` — reserved ID blocks. Draw new IDs from here, don't
  pick numbers ad hoc.
- `source/spells/*.csv` — one row per new/changed spell, one file per class
  (`mage.csv`, `warrior.csv`, ...) plus `npc.csv` (creature-only abilities)
  and `generic.csv` (no player class — trinket procs, test content, etc.).
  Split purely so no single file grows huge; every file shares the same
  header and they're all merged into one list before `build.py`/`reuse.py`
  ever sees them (`lib/source.py::load_spells_csv`), so it makes no
  functional difference which file a row lives in beyond human
  organization. Duplicate IDs across files are a load-time error, naming
  both files.

  A friendly subset of `Spell.dbc`'s 234 columns (id, name, school, cast
  time, cooldown, mana cost, range, radius, duration, up to 3 effects,
  icon). Two JSON columns: `effectN`
  (type/base_points/points_per_level/die_sides/mechanic/implicit_target_a/b/
  apply_aura/amplitude/misc_value/trigger_spell/chain_targets/radius_yards)
  and `raw_overrides` (any column name → value, applied last — the escape
  hatch to reach the other ~200 columns, and what makes `pull.py` lossless:
  anything the friendly fields don't model just round-trips through here).

  **Once `docs/single-rank-spell-system.md` lands** and rank chains
  collapse to one entry per ability: the surviving rank stays in its
  class's file under its existing row; superseded lower ranks that nothing
  else references just get deleted from source (they're not emitted
  anymore, and the pending SQL's per-block `DELETE` already retracts them).
  Only keep an old rank around at all if something still casts that exact
  spell ID directly (a specific NPC ability, a set-bonus proc, a
  `spell_ranks`/hardcoded reference) — in that case move *that row* into
  `npc.csv` (or add a `notes` entry explaining what still needs it) rather
  than leaving it in the class file, so the class file only ever holds the
  one live rank per ability.
- `source/talents/*.yaml` — new/changed `Talent.dbc` + `TalentTab.dbc` rows,
  one file per class (same merge-by-directory mechanism, same duplicate-ID
  check, as `source/spells/`). UI-agnostic per `docs/talent-ui-decision.md`.
  Empty until a real ticket (Frost Mage) needs it; `mage.yaml` carries the
  full schema/example comment, the other class files just point back to it.

`spell_weight` / `coeff_weight` columns are captured as passthrough
metadata only — turning them into `BasePoints`/`RealPointsPerLevel` is
`docs/single-rank-spell-system.md`'s job, not this tool's.

## Known limitations

- `spell_icon_id` takes a raw `SpellIconID` integer, not a texture-path
  lookup — the server doesn't load `SpellIcon.dbc` at all (nothing to
  overlay), so resolving one from a friendly name would mean extracting and
  indexing it separately. Pick an ID by browsing an already-extracted
  `SpellIcon.dbc` in any DBC viewer.
- The MPQ writer (`lib/mpq_writer.py`) is store-only (no compression), no
  `(listfile)` (the client finds files by hash, it doesn't need a
  directory listing — only external MPQ browsers would miss one).
- Only the specific columns listed in each `DbcTable.signed` (see
  `lib/dbcfmt.py`) are treated as signed int32 on read; this covers every
  `int32`-typed field in `DBCStructure.h` for the tables this tool touches.
