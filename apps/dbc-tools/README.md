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
sudo apt-get install smpq
```

`smpq` (StormLib's CLI archiving tool) packs the client-patch MPQ — see `lib/mpq_writer.py`'s
module docstring for why this is a real system dependency now rather than a pure-Python writer,
and for a no-root fallback if `sudo` isn't available.

Optional but needed for real client-patch output: extract `Spell.dbc`,
`Talent.dbc`, `TalentTab.dbc`, `SpellCastTimes.dbc`, `SpellDuration.dbc`,
`SpellRange.dbc`, `SpellRadius.dbc`, `Item.dbc` from your client's
`DBFilesClient\` (inside the locale MPQs — specifically the highest-numbered
patch, e.g. `Data/enUS/patch-enUS-3.MPQ`; earlier patches in the same
directory also contain these files but are shadowed/stale) into
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
- the same bytes into `env/dist/data/dbc/` if that directory exists;
- a copy of `patch-Z.mpq` deployed to this box's patch-distribution root
  (see `apps/patch-service/README.md`), if one is configured. That root is
  operator-specific, so it isn't hardcoded here — copy
  `lib/local_config.py.example` to `lib/local_config.py` (gitignored) and
  set `DEPLOY_ROOT` to your own path. `build_patch_m.py` and
  `patch_gt_tables.py` read the same `DEPLOY_ROOT` for their own
  patch-M.mpq/patch-Y.mpq (overridable per-run with `--deploy-root`/
  `--deploy`); without a `local_config.py`, all three just skip deployment.

Running it twice with unchanged source produces byte-identical output
(diff the pending SQL / patch files to confirm) — that's what makes this a
generator rather than a one-off script.

Generated pending files accumulate — don't delete an earlier `rev_*.sql`
after a run. The DBC tables are re-emitted in full each time, but
`trainer_spell`/`spell_script_names`/`spell_bonus_data`/`spell_proc` are
emitted as a *delta* against everything already in `pending_db_world/`, so
an older file's rows are skipped as "already live" and exist nowhere else.
To consolidate into one file, delete the old one *before* running, not after.

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

**Gotcha: `EffectSpellClassMaskA/B/C_1/2/3` in `raw_overrides`.** Every other
per-effect column in `spell_dbc` uses `_1/_2/_3` as the effect index
(`EffectBasePoints_2` is Effect_2's base points, etc.) — this is the one
exception. Here the **letter** is the effect index (A=Effect_1, B=Effect_2,
C=Effect_3) and the **number** is which of that effect's 3
`SpellFamilyFlags` dwords holds the bit (see `lib/dbcfmt.py`'s comment on
the `SPELL` table for the full mechanics). If you're adding a classmask
override to scope a `SPELLMOD_EFFECT2`/duration/etc. modifier that lives on
Effect_2, the key is `EffectSpellClassMaskB_1` (or `_2`/`_3`), **not**
`EffectSpellClassMaskA_2` — the latter silently scopes Effect_1 instead and
leaves Effect_2's real classmask all-zero, which the engine
(`SpellInfo::IsAffected`) reads as "matches every spell in the family," not
"matches nothing." This exact mistake shipped for two frost-mage talents
(Permafrost, Chilled to the Bone — see `docs/dbc-build-pipeline.md`'s "Bug
3") and made their movement-slow modifiers apply to every mage spell
instead of just Frostbolt/Cone of Cold. When adding any hand-authored
`EffectSpellClassMask*` override, double check which effect index you
actually mean before picking the letter. This mistake shipped twice in one day even with this
callout already written (see `docs/dbc-build-pipeline.md`'s "Bug 3" for the second one, Empowered
Frostbolt) — so don't rely on reading this. `generate.py` also runs an automated check
(`lib/lint.py`) after every spell build and prints a `WARNING:` line if a SpellMod effect that
needs a classmask ends up with an all-zero one. Take that warning seriously; it's almost always
this exact mistake.

## Web UI

`source/spells/*.csv`'s two JSON-blob columns (`effectN`, `raw_overrides`) and
`source/ids.yaml`'s reserved-ID bookkeeping get old fast by hand. `webui/` is
a small local Flask app that edits the exact same CSV/YAML files as a form
instead — CSV/YAML stay the source of truth (same as everything else in this
tool), it just makes hand-editing them less tedious. No database, no build
step, no auth.

`webui/app.py` defines this as the `dbc` Flask Blueprint; in production it's
served alongside item-tools' webui by **apps/wow-tools-webui**
(`../wow-tools-webui/README.md`), at `/dbc/` on that combined app's port. For
quick dev/debugging it can still run standalone, unprefixed, on its own port:

```
pip install -r apps/dbc-tools/requirements.txt   # adds Flask, ruamel.yaml
python3 apps/dbc-tools/webui/app.py
```

Open `http://localhost:8600/`, or `http://<this machine's LAN IP>:8600/` from
any other device on the same network — it binds `0.0.0.0` on purpose. There's
no login, so anyone who can reach that port can edit these files; keep it on
a trusted home network, not port-forwarded to the internet.

What it does: browse/add/edit/delete rows in any `source/spells/*.csv` or
`source/talents/*.yaml` file, with a structured form for each `effectN` slot
and a key/value editor for `raw_overrides` instead of hand-typed JSON, an
"allocate ID" suggestion drawn from `source/ids.yaml`'s reserved blocks for
new rows, and a "Run generate.py" button on the dashboard. Saving a spell row
rewrites only that row's line in its CSV file — every other row's exact text
is preserved byte-for-byte, deliberately, so an edit doesn't turn into a
whole-file diff. Saving a talent tab/talent/ability does the same for its
YAML file via `ruamel.yaml`'s round-trip mode, which also means an untouched
entry's inline comments survive; a comment sitting on the specific line you
just edited is the one thing that doesn't survive that edit.

What it doesn't do: no enum-name dropdowns for raw DBC integer columns
(school/mechanic/dispel/`SpellClassSet`/...) — plain numeric inputs, same as
the CSV itself; no in-browser diff preview before running `generate.py` (its
own stdout already lists exactly what it's about to touch); no reclassifying
a row into a different class file from the edit form (delete + re-add
instead); no concurrent-edit locking (single-user tool — git is still the
safety net if two edits collide).

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

## Declaring more world-DB tables (WP-T)

A `source/classes/*.py` file (see `source/classes/README.md` for the full DSL - `spell()`,
`talent()`, `scripted_by()`/`bonus_coefficients()`/`procs_on()`, ...) can also declare five more
world-DB tables right next to the spell they belong to, instead of a hand-written migration —
same "diff against live, DELETE-then-INSERT the rest, silent on an unchanged rerun" emission as
every other declared table (`lib/spell_tables.py`):

```python
from lib.dsl.registry import (
    linked_spell, spell_group, spell_group_rule, custom_attr, shapeshift_form,
)

# spell_linked_spell - SpellMgr::LoadSpellLinked. type: 0=cast, 1=hit, 2=aura. Each type reads a
# negative trigger/effect differently - type=0's negative *trigger* means "on removal of the aura
# |trigger|"; type=2's negative *effect* means "grant/revoke immunity to spell |effect|", not
# "remove that aura" - see lib/dsl/registry.py's comment above _SPELL_LINKED_MAX_SPELLS for the
# full, source-verified semantics of every case. A *positive*, type=0 trigger in ids.yaml's custom
# spell block (200000-209999) risks colliding with a type=1/2 row on (trigger-200000) - see
# lib/lint.py's check_linked_spell_key_collisions, which generate.py runs automatically.
linked_spell(200326, 57865, type=2)  # positive trigger/effect, type=2: apply/remove 57865 with 200326's aura

# spell_group + spell_group_stack_rules - SpellMgr::LoadSpellGroups/LoadSpellGroupStackRules.
# group_id must be a fresh id from ids.yaml's `spell_group` block, or one that already exists in
# stock/migration data (adding a member to a stock group like 1054 or 1016 is legitimate). A
# negative member id is a nested-group reference, not a rank chain - the loader expands those
# itself.
spell_group(1200, 200001, 200002)
spell_group_rule(1200, stack_rule=1, description="my new debuff group")

# spell_custom_attr - SpellCustomAttributes (SpellInfo.h). Declaring a stock spell_id replaces
# that row, same as every table here. Double check the exact bit against SpellInfo.h before
# using one - there is no single SPELL_ATTR0_CU_POSITIVE bit, only POSITIVE_EFF0/1/2 (one per
# effect slot) and NEGATIVE_EFF0/1/2, dense neighbors that are easy to transpose.
custom_attr(200001, attributes=0x02000000)  # SPELL_ATTR0_CU_POSITIVE_EFF0 - effect 1 is beneficial

# spellshapeshiftform_dbc - a FULL override row: every column starts at the real stock value
# (var/extractors/dbc/SpellShapeshiftForm.dbc) and only the ones named here change. Accepts
# either the real SQL column name (CombatRoundTime) or DBCStructure.h's own field name
# (attackSpeed) - see lib/dsl/registry.py's _SHAPESHIFT_FRIENDLY_COLUMNS for the rest. Server-
# side only, no client patch (nothing the client renders depends on this table).
shapeshift_form(5, attackSpeed=3500)  # Bear Form's melee swing timer
```

**Declared removals** retract a row this tool never emitted itself - stock Blizzard data, or an
older hand-written migration - which the normal "no longer declared" prune pass can't reach (that
one only ever deletes what a *past `generate.py` run* itself emitted). Each is a key-exact
`DELETE`, emitted once (a rerun with the same removal declared stays silent), with a `WARNING:`
if the key doesn't exist anywhere (base dump, migrations, module SQL - almost always a typo; the
`DELETE` is still emitted, since it's a harmless no-op either way), and an error if the same run
both declares and removes the same key:

```python
from lib.dsl.registry import unbind_script, unlink_spell, leave_spell_group, untrain

unbind_script(69366, "spell_dru_moonkin_form_passive")  # spell_script_names
unlink_spell(200326, 57865, type=2)                      # spell_linked_spell
leave_spell_group(1054, 200001)                          # spell_group (no id-range check - removing never mints)
untrain(50464, trainer_ids=[212, 213])                    # trainer_spell, one DELETE per trainer id
```

**Removing a row mod-progression's phase SQL inserts** (most `untrain` targets - phase_00 is where
this server's class trainers get their spells) only partly sticks. Core `db_world` SQL, the
removal's `DELETE` included, is applied before mod-progression's `OnAfterDatabasesLoaded` applies
`src/phase_NN/sql/`, so any phase that inserts the row puts it back afterwards:

- a phase this realm has already applied (`<= Progression.Phase`): only a fresh world DB (a new
  realm) gets the row back; a realm already past that phase keeps the removal. `generate.py` adds a
  `note:` line naming the phase.
- a phase this realm hasn't reached yet: the `DELETE` matches nothing today, and the row appears
  when the realm reaches that phase. `generate.py` prints a `WARNING:` naming the phase instead of
  the typo warning.

Either way the removal counts as done and is never emitted again. dbc-tools can't change that
apply order - the hand-written `data/sql/updates/db_world/2026_09_23_02.sql` this helper replaces
had the same limit - so a removal that has to hold on every realm and every phase means editing the
phase file itself.

### Declaring a creature (T1)

A `source/classes/*.py` file can also declare a rework's own NPC - `creature_template` +
`creature_template_model` - instead of a hand-written migration (the previous precedent, Tentacle
of Madness, is `data/sql/updates/db_world/2026_09_23_12.sql`):

```python
from lib.dsl.registry import creature_template, creature_model

# creature_template - ObjectMgr::LoadCreatureTemplates. `entry` must be a fresh id from
# source/ids.yaml's `creature` block (300000-300999), or an id that already exists (overriding a
# live custom entry, e.g. re-declaring 300102, is legitimate). Builds a FULL row: every real
# creature_template column gets a value - whatever you pass here, then a small set of defaults
# that differ from the schema's own DEFAULT because the engine rejects/rewrites the schema default
# at boot (unit_class 0 -> 1, BaseAttackTime/RangeAttackTime 0 -> 2000 - see
# lib/dsl/registry.py's _CREATURE_TEMPLATE_DEFAULT_OVERRIDES for the reasons), then the table's
# real schema DEFAULT for everything else. An unknown column name raises.
creature_template(
    300170, "Chaos Rift",
    faction=35, unit_flags=33554434, unit_flags2=2048, flags_extra=66,
    ScriptName="npc_warl_chaos_rift",
)

# creature_template_model - ObjectMgr::LoadCreatureTemplateModels. `probability` defaults to 1.0,
# not the schema's 0 (a lone model at 0 total probability gets reset to 1.0 anyway by
# ObjectMgr::CheckCreatureTemplate, but that's a footgun once a second model is added later).
creature_model(300170, display_id=11686)
```

Emission differs from every other declared table here: `creature_template` is on the SQL linter's
do-not-delete list (`apps/codestyle/codestyle-sql.py`'s `not_delete`), so it's **never**
DELETE-then-INSERT'd - a changed or new row is emitted as an upsert instead (`INSERT ... ON
DUPLICATE KEY UPDATE <every non-key column> = VALUES(<column>);`, never a `DELETE`).
`creature_template_model` (keyed on `CreatureID, Idx`) still gets the normal DELETE-then-INSERT
every other table here does - only `creature_template` itself needs the upsert.

**Neither table is ever pruned.** Dropping a `creature_template`/`creature_model` declaration from
source does not delete anything - `creature_template` can't be (the do-not-delete list), and
pruning only the model row would leave a creature with no visible model. `generate.py` prints one
`creature: ... is no longer declared - left in place` line per retired entry instead, for a human
to remove by hand if they actually want it gone.

Three `WARNING:` lints run automatically: a declared `creature_template` with `flags_extra`
including `CREATURE_FLAG_EXTRA_TRIGGER` (0x80) that also has a model (forces the model invisible
for every non-GM observer - `docs/bugs-and-fixes.md`'s `CREATURE_FLAG_EXTRA_TRIGGER` entry); a
declared `creature_template_model` whose `CreatureDisplayID` has no `creature_model_info` row
anywhere; and a declared `creature_template` with no `creature_template_model` row anywhere
(declared or live).

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
