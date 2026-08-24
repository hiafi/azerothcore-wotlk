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

## Pulling existing data in — and editing it

```
python3 apps/dbc-tools/pull.py --spell 116,133          # explicit IDs
python3 apps/dbc-tools/pull.py --spell 100-200           # inclusive range
python3 apps/dbc-tools/pull.py --spell 100 --dest npc    # force a destination file
python3 apps/dbc-tools/pull.py --class mage              # every spell whose
                                                          # SpellClassSet is
                                                          # that class
python3 apps/dbc-tools/pull.py --all                     # every existing
                                                          # spell_dbc row —
                                                          # also the tool's
                                                          # own round-trip
                                                          # self-test

python3 apps/dbc-tools/pull_talents.py --class mage       # every talent tab
                                                           # (by ClassMask)
                                                           # and talent in it
python3 apps/dbc-tools/pull_talents.py --tab 8,9 --dest mage
python3 apps/dbc-tools/pull_talents.py --talent 23,24 --dest mage
```

Appends rows to the matching file under `source/spells/` (or
`source/talents/` for tabs/talents) for IDs not already present anywhere in
that directory. `pull.py`'s destination file is auto-detected from the
spell's `SpellClassSet` (`SPELLFAMILY_*` in
`src/server/shared/SharedDefines.h` — see `SPELLFAMILY_TO_FILE`) unless
`--dest` overrides it; anything with no player class falls back to
`generic.csv`. A class-family match gets one more check before landing in
that class's file: is the ID taught by a trainer (`trainer_spell`), a
member of a rank chain (`spell_ranks`, which carries a row for every real
player ability, single-rank ones included), or granted by spending a talent
point (`Talent.dbc`'s `SpellRank_1..9` columns)? If none of the three, it's
a boss/creature clone that merely shares the class's `SpellClassSet` —
routed to `npc.csv` instead, automatically. Talent-granted spells land in
`<class>_talents.csv` rather than `<class>.csv` — see "Source files" below —
so a class's plain file only ever holds spells learned outright. Override
with `--dest` for anything auto-detect still gets wrong.

**Pulling a row doesn't make `generate.py` touch it.** `generate.py`
reconciles every source entry against what's actually live (base client DBC
⊕ current SQL overlay — see `lib/resolve.py`) and only ever does one of
three things with it:

1. **New content** — `id` is inside `source/ids.yaml`'s reserved block:
   always built and emitted (the normal "minting a new spell" case).
2. **Editing an existing spell/talent** — `id` is outside the reserved
   block, but you changed something after pulling it in: emitted, with an
   explicit `DELETE ... WHERE ID IN (...)` (not a range delete, since edited
   existing IDs are scattered) so the migration only ever touches the exact
   rows you actually changed. This is the answer to "I pulled Frostbolt, now
   I want to retune its damage" — edit the row in `mage.csv`, run
   `generate.py`, done. `generate.py` prints exactly which IDs it's editing.
3. **Untouched reference copy** — `id` is outside the block *and* identical
   to what's live: silently skipped, no SQL, no patch. This is what lets you
   pull an entire class's worth of spells (or `--all`, ~54k rows) in for
   reading/context without every regen trying to rewrite all of them.

Also useful for validating the pipeline itself: `pull.py --all` reverses
every existing row, and (1) is exactly what runs the "unchanged → skip"
path at scale, and (2) — if you add the check back in, see
`lib/reverse.py`'s docstring — rebuilding and diffing against the original
was run once over all ~54k merged base+overlay spell rows during
development with zero mismatches.

## Source files

- `source/ids.yaml` — reserved ID blocks. Draw new IDs from here, don't
  pick numbers ad hoc.
- `source/spells/*.csv` — one row per spell, two files per class
  (`mage.csv` / `mage_talents.csv`, `warrior.csv` / `warrior_talents.csv`,
  ...) plus `npc.csv` (creature-only abilities) and `generic.csv` (no player
  class — trinket procs, test content, etc.). `<class>.csv` holds spells
  learned outright (trainer-taught or a `spell_ranks` chain member);
  `<class>_talents.csv` holds spells granted by spending a talent point
  (`Talent.dbc`'s `SpellRank_1..9`) — `pull.py`'s `detect_dest` sorts new
  pulls between the two automatically (see "Pulling existing data in"
  above). This mirrors `source/talents/*.yaml` holding the talent tree
  *shape* (tabs, tiers, rank chains) while `<class>_talents.csv` holds the
  actual `Spell.dbc` row each rank grants — different tables, same class
  split. A row is either new content, an active edit to something existing,
  or a pulled-in-for-reference copy nothing has touched yet — see "Pulling
  existing data in" above for how `generate.py` tells those apart. Split
  purely so no single file grows huge; every file shares the same header
  and they're all merged into one list before `build.py`/`reuse.py` ever
  sees them (`lib/source.py::load_spells_csv`), so it makes no functional
  difference which file a row lives in beyond human organization. Duplicate
  IDs across files are a load-time error, naming both files.

  A friendly subset of `Spell.dbc`'s 234 columns (id, name, school, cast
  time, cooldown, mana cost, mana cost %, range, radius, duration, up to 3
  effects, icon). Two JSON columns: `effectN`
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
- `source/talents/*.yaml` — `Talent.dbc` + `TalentTab.dbc` rows, one file
  per class (same merge-by-directory mechanism, same duplicate-ID check,
  new/edit/reference-copy distinction, as `source/spells/`). UI-agnostic per
  `docs/talent-ui-decision.md`. `mage.yaml` carries the full schema/example
  comment (and, as of the Frost Mage rework starting, the real pulled-in
  Fire/Frost/Arcane trees); the other class files are still empty
  placeholders that just point back to it.

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
