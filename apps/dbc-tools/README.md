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
`SpellRange.dbc`, `SpellRadius.dbc`, `Item.dbc`, `SpellDescriptionVariables.dbc` from your client's
`DBFilesClient\` (inside the locale MPQs — specifically the highest-numbered
patch, e.g. `Data/enUS/patch-enUS-3.MPQ`; earlier patches in the same
directory also contain these files but are shadowed/stale) into
`var/extractors/dbc/`. Without these, `generate.py` still produces correct
SQL (the server doesn't need them), it just skips producing a client patch
for whichever files aren't there, and `reuse.py` mints fresh IDs from the
reserved blocks instead of reusing matching stock rows.

One exception feeds the SQL, not the patch: `CreatureSpellData.dbc`, which only `patch-enUS.MPQ`
carries (no later patch has it). Extract it, flattened, into the same directory. The superseded-rank
rule (`lib/superseded_ranks.py`) reads it; without it `generate.py` prints a `WARNING` and emits no
`creaturespelldata_dbc` rows.

`CreatureFamily.dbc` is the same kind of exception (in no client MPQ; copy it from the worldserver's DBC
directory, `ac-worldserver:/azerothcore/env/dist/data/dbc/`, into `var/extractors/dbc/`). `retire_pet_spell()`
reads it to know which skill lines a family uses: with a retirement declared and the file missing the run stops
with an `ERROR`, and the hunter family lint (rule d) prints a `WARNING` that it only knows skill line 270.

`SpellRuneCost.dbc` and `ChrClasses.dbc` are the same kind of exception (copy both from
`ac-worldserver:/azerothcore/env/dist/data/dbc/` into `var/extractors/dbc/`; `SpellRuneCost.dbc` is also in the
client's `patch-enUS-3.MPQ` and is byte-identical). `spell_rune_cost()` merges its rows over `SpellRuneCost.dbc`
into patch-Z and stops the run with an `ERROR` naming the file when it is missing; `chr_class()` builds its row
from `ChrClasses.dbc` and stops with an `ERROR` naming the file too. Neither is needed until a rune cost or a class
row is declared. See "Death Knight T1" below.

## Generating

```
python3 apps/dbc-tools/generate.py
python3 apps/dbc-tools/generate.py --check                  # read-only lints + generated-header gate
python3 apps/dbc-tools/generate.py --check --class warrior  # the same for one class only (seconds)
```

Flags: `--no-prune`, `--check`, `--check --class NAME` (refused without `--check`), `--no-cache`, `--rebuild-cache`.
A run replays the base dumps and every promoted `db_world` file to learn what is live; that replay is cached under
the gitignored `var/dbc-tools-cache/` and reused while the files, the loader code and the parameters are unchanged
(see `.agents/docs/systems/dbc-tools.md`, "generate.py speed"). A run after a change that touches the cache's inputs
is slower once. Timings and the harness that proves the output unchanged: `apps/dbc-tools/bench/equivalence.py`.

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

### Spell categories and `spell_proc` removals (Paladin T1)

```python
from lib.dsl.registry import remove_spell_proc, spell_category

# spellcategory_dbc - id from ids.yaml's `spellcategory` block (1300-1319, widened from
# 1309 by Warrior T1; stock tops out at 1253). A spell then shares the cooldown with
# `category=1300, category_cooldown_ms=15000`.
# generate.py stops with an error for a spell whose Category (typed `category` or a raw
# `Category` override) is in that block but has no spell_category() - without the server row
# SpellInfo::GetCategory() is 0 and the category cooldown silently never exists.
spell_category(1300, comment="paladin auras, 15 s shared cooldown")

# spell_proc removal (negative id = every rank of the chain). Removing the row does not always stop
# the proc: with no row SpellMgr builds a default one only when the spell has a trigger aura AND
# non-zero DBC ProcFlags (spell_dbc column `ProcTypeMask`), and an explicit row with ProcFlags 0
# inherits them too. So -31871 (DBC flags 0) and Redoubt 20128/20131/20132 are fully disabled by the
# removal alone; a trigger-aura spell with flags needs `ProcTypeMask` zeroed on every rank.
# generate.py prints a WARNING for each rank still non-zero (conservative: it ignores the
# trigger-aura condition). Full generate.py run only - not under --check.
remove_spell_proc(-53695)
```

**Client row.** `spell_category()` writes both halves: the server `spellcategory_dbc` SQL (a
`SPELL_TABLES` delta, so diff/prune like `custom_attr`) and a client `SpellCategory.dbc` row merged
over the stock file into patch-Z on every build (like `tooltip_vars`). The stock file must be at
`var/extractors/dbc/SpellCategory.dbc` (extract `DBFilesClient/SpellCategory.dbc` from the
highest-numbered client `patch-enUS*` MPQ holding it, flattened - same as `Item.dbc`); `generate.py`
errors out if categories are declared and it is missing. The server still sends sibling cooldowns to
the client only for spells with `custom_attr` 0x10000000 (FORCE_SEND_CATEGORY_COOLDOWNS), so the
client's sweep relies on `Spell.dbc` `Category`/`CategoryRecoveryTime` plus this row. Still check a
sibling's sweep in-game, not only `.cooldown` (which reads server state).

### Keeping a dungeon out of the dungeon finder

`source/world/lfg.py` declares world content that belongs to no class (`source/world/` is loaded
like `source/npcs/`):

```python
from lib.dsl.registry import lfg_exclude

lfg_exclude(230, "Blackrock Depths")  # Map.dbc id, dungeon name
```

Each becomes a `disables` row `(8, <map>, 1, '', '', <name>)` (`DISABLE_TYPE_LFG_MAP`). The dungeon is then
locked for everyone: it drops out of the random pool and the "Specific Dungeons" list, and stays
enterable on foot. It applies per map, so every finder entry on that map goes with it: all wings,
normal and heroic, and seasonal bosses (BRD takes Coren Direbrew). `generate.py` prints a `note:` per
exclusion listing exactly what it covers, and stops with an error for a map no dungeon/raid/heroic
finder entry uses. Deleting a line re-enables the dungeon (the prune pass DELETEs the row, the last one
included). Live on worldserver start or `.reload disables`. Needs the stock
`var/extractors/dbc/LFGDungeons.dbc` (`DBFilesClient/LFGDungeons.dbc` from `patch-enUS-3.MPQ`, flattened).

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

**Class-less NPCs: `source/npcs/`.** `source/classes/` only holds class folders. Test and tool NPCs
that belong to no class (the training dummies, `source/npcs/training_dummies.py`) live in
`source/npcs/*.py` instead: same DSL, same loader (`generate.py` calls `load_classes_dir` on it a
second time and merges the result), ids from `source/ids.yaml`'s `npc_tools` block (900000-900099)
or the `creature` block. A creature entry declared in both directories is an error. Pass every
column that differs from the schema default explicitly, so the file documents the NPC and rebuilds
the row on a fresh DB; `creature_model(..., verified_build=None)` reproduces a NULL `VerifiedBuild`.

### Editing stock talents, pet spells and items (hunter-rework T1)

Helpers for changing data that already exists (stock rows), so no later stage hand-writes world SQL. All of them
register from a `source/classes/*.py` (or, for items, `source/world/*.py`) file like `spell()` does.

```python
from lib.dsl import AcquireMethod
from lib.dsl.registry import (
    item_template, live_item_templates, retire_pet_spell, retire_talent, skill_line_ability, tab, talent,
)

# retire_talent(talent_id) - moves a stock talent out of its tree without deleting the row: the live row
# re-emitted on TabID 60800 (the "Retired" holding tab, declared once in source/classes/hunter/
# hunter_retired_tab.py - do not declare another), TierID/ColumnIndex 0, every SpellRank_n 0, PrereqTalent_n/
# PrereqRank_n 0, CategoryMask_n 0, Flags 0. Errors if talent_id is not a live row; generate.py stops
# (MissingRetiredTabError) if nothing declares tab 60800. Never TabID 0: mod-playerbots dereferences the tab of
# every Talent.dbc row. A talent that source/classes/hunter/hunter_pet_talents.py carries as a reference copy
# must be deleted from that file first (one declaration per id).
retire_talent(2110)

# retire_pet_spell(spell, families=None) - takes a stock pet ability away from pets. `spell` is an id or a
# declared Spell; `families` are CreatureFamily ids (creature_template.family: 3 Spider, 2 Cat, ...). It
#   1. sets AcquireMethod 0 on every stock SkillLineAbility row teaching the spell on a pet skill line - the
#      shared 270 and every CreatureFamily.dbc line - or, with `families`, only on the lines those families
#      use alone (the shared 270 cannot be retired for one family: that row is reported and left, unless
#      shared_lines=True opts in - see Cower below);
#   2. strips the spell from the CreatureSpellData record of every creature of those families
#      (creature_template.family -> PetSpellDataId), so it does not come back as a default spell;
#   3. rides the pet-stale-ranks override path (one row per record: superseded rank -> survivor first, then the
#      strip). A skill_line_ability() declared with the same id wins, with the existing WARNING.
# A talent whose rank spell is retired here also needs retire_talent(): this never touches Talent.dbc.
retire_pet_spell(61684)                    # Dash, for every family
retire_pet_spell(24604, families=[1])      # Furious Howl: the Wolf's rows only (stock row 13031 is on its own line 208)
# Cower (1742) is taught only by SLA 13012 on the shared line 270. shared_lines=True retires that row for every
# family and keeps the CreatureSpellData strip to `families` (PET 4.6: non-Ferocity families only):
retire_pet_spell(1742, families=[...non-Ferocity family ids...], shared_lines=True)
# A retirement that matches no SkillLineAbility row in scope and no record prints
# "WARNING: retire_pet_spell: retire_pet_spell(N) matches nothing" (wrong spell id or family).

# skill_line_ability(..., acquire_method=, superseded_by=) - the typed AcquireMethod / SupercededBySpell
# columns (None = unset, the row is built exactly as before; raw_overrides still wins). AcquireMethod is a
# lib.dsl IntEnum: NONE 0, LEARNED_ON_SKILL_VALUE 1, LEARNED_ON_SKILL_LEARN 2 (a pet learns it with its
# level - SpellMgr::LoadPetLevelupSpellMap reads exactly this).
skill_line_ability(id=30990, skill_line=270, spell_id=201710, acquire_method=AcquireMethod.LEARNED_ON_SKILL_LEARN)

# item_template(entry, **columns) - edits columns of an EXISTING item_template row (unknown entry raises;
# `class` is a Python keyword, hence the dict). Unmentioned columns keep their live value, an unknown column
# raises KeyError. Emitted as a column-limited
# `UPDATE item_template SET <passed columns> WHERE entry IN (...)` (item_template is on the SQL linter's
# do-not-delete list; rows with the same assignments share one statement), so nothing you left alone is
# rewritten from the replayed row, and apps/item-tools' overlay reads it back. Never pruned: a dropped declaration prints "item: ... no longer declared - left in place".
item_template(2101, **{"class": 1, "subclass": 0, "BagFamily": 0})
# live_item_templates() is the read-only live row dict, for selecting by column instead of listing entries.
# Illustrative selector only (the real ranged-weapon one is source/world/ranged_weapons.py; Thrown is out of scope):
for entry, row in live_item_templates().items():
    if row["class"] == 2 and row["subclass"] == 18:
        item_template(entry, ammo_type=0)
```

Live state for `item_template()` comes from apps/item-tools' overlay (`item_lib.overlay`: base dump plus every
merged and pending migration, recursing into `itemization_templates_v2/`), not from `trainer_state`'s replay,
which only sees top-level `*.sql`.

**`item_template` class/subclass must agree with `Item.dbc`.** The server resets them from the DBC at boot
(`DBC.EnforceItemAttributes`, default 1) and the client reads them from its own `Item.dbc`, so an edit that
changes `class`/`subclass` also needs the matching `source/items.csv` row (a stock id is an *edit*: an `item_dbc`
delta plus the row replaced inside patch-Z). `WARNING: item N ... differs from its Item.dbc row` when they
disagree. Stock content using this: `source/world/quivers.py` (33 quivers and ammo pouches become plain bags,
class 1/subclass 0/`BagFamily` 0) and `source/world/ranged_weapons.py` (every live bow, gun and crossbow gets
`ammo_type` 0, selected by `class` 2 and `subclass` 2/3/18, never by `ammo_type`). `ammo_type` is not in
`Item.dbc`, so there is no client patch for it; the client caches item queries, so **delete the client's `Cache`
folder once at rollout**. `WARNING: item N ... the client still demands ammo` (`lint.check_ranged_ammo_type`) fires on a
declared ranged weapon, or a custom `items.csv` bow/gun/crossbow (id >= 56806), whose `ammo_type` is not 0.

The item lints and `check_talent_tab_refs` run on a **full** `generate.py` run only: `--check` returns before
them, so a session limited to `--check` gets no feedback from them. The family-bit lint also runs under `--check`
since shaman T1 (see "Shaman T1" below).

**Talent rows are ordered by their final tab.** Talent.dbc's physical order is load-bearing (see
`dbcfile.order_talent_rows`): a row goes into the block of the `TabID` it is built with, so a talent moved from
one tab to another leaves the old block and sorts by tier/column in the new one; tabs keep the stock file's
order, and a tab missing from the stock file (60800) is a block after all of them. `ERROR: talent row(s) ...
name TabID N, which is not in the built TalentTab.dbc` (`lint.check_talent_tab_refs`) stops the run when a
talent names a tab nobody declared.

**Family-bit lint.** `WARNING: spell N ...: hunter family-bit rule (a|b|c|d)` (`lint.check_family_bit_rules`, also
exported as `check_hunter_family_rules`; custom ids >= 200000 with `SpellClassSet` 9): (a) a non-aspect (its name
does not start with "Aspect of") carrying an aspect bit; (b) any carrier of d1 b0; (c) any reader mask (an effect's
`EffectSpellClassMask`, or a `spell_proc` family mask) containing the pet bit d1 b28 - read a pet group through its
d2 bit alone; (d) a pet-cast spell (carries d2 b22/b23/b24, or is taught on skill line 270 or a CreatureFamily.dbc
line) that lacks d1 b28. A spell with d1 b28 and DmgClass RANGED never warns. The literals live in
`lint.HUNTER_FAMILY_RULES`; another class joins by adding a `FamilyBitRules` row to `FAMILY_BIT_RULES`.

**Pet reference data.** `source/classes/hunter/hunter_pet_talents.py` holds the three stock pet talent tabs
(409 Tenacity, 410 Ferocity, 411 Cunning) and their 63 talents as untouched copies (66 rows, no SQL, no patch
delta); the hunter pet pass owns every edit. `pull_talents.py --tab 409,410,411 --dsl` prints DSL `tab(...)` /
`talent(...)` declarations to stdout (the DSL counterpart of `pull_dsl.py`; it never writes a file and skips ids
already declared under `source/classes/`). `retire_pet_spell()` needs the stock
`var/extractors/dbc/CreatureFamily.dbc` (from the worldserver's `env/dist/data/dbc/`; generate.py stops with the
path if a retirement is declared without it).

### Shaman T1: creature spell slots, spell lints and id blocks

Added for the shaman rework (`.agents/plans/shaman-rework/`, T1). No shaman content: these are the helpers, lints and
id blocks SH0 and the spec stages call.

**`creature_spell(entry, index, spell, verified_build=0)` / `remove_creature_spell(entry, index)`** declare one
`creature_template_spell` row (`ObjectMgr::LoadCreatureTemplateSpells`: the creature's `m_spells[0..7]`) and its
key-exact removal. `spell` is a stock id or a declared `Spell`; `entry` is a creature this run declares (inside
`ids.yaml`'s `creature` / `npc_tools` block) or one that already exists. A bad index or an unknown entry raises.

```python
# SH0: a totem that summons its guardian. The summon must sit on Index 0 - when the totem is removed
# Unit::SetMinion despawns the guardians it summoned by reading only Totem::GetSpell(), which is m_spells[0]
# (Totem.h:59, Unit.cpp:7745-7759), so a summon on any other slot leaves the guardian standing.
creature_template(300270, "Fire Elemental Totem", ...)
creature_spell(300270, 0, fire_elemental_summon_202xxx)
creature_spell(15439, 0, 202xxx)       # overriding a stock row is ordinary: the declared row replaces it

# SH0 removes the P0 spike's hand-written rows (rev_1792393868936008368.sql): this tool never emitted them, so
# the prune pass cannot reach them and a removal is the only way. One key-exact DELETE, emitted once.
remove_creature_spell(300298, 0)
remove_creature_spell(300299, 0)
```

It rides the `SPELL_TABLES` / `REMOVAL_TABLES` path like `procs_on()` / `untrain()`: a DELETE on the
(CreatureID, Index) keys followed by the INSERT, diffed against the live table (base dump, every migration, pending
files), so an unchanged rerun emits nothing. Dropping a declaration prunes only a row **this tool emitted before**; a
hand-written row is neither pruned nor re-emitted, and a dropped declaration that overrode a stock row is reported
(`prune: NOT removing creature_template_spell (...) - the stock dump owns this key too`) and left as the declaration
wrote it, exactly as `procs_on()` behaves. Declaring and removing one slot in the same run raises. A declared spell
that is neither declared in source nor a stock spell prints `WARNING: creature_spell(...): spell N is neither
declared ...` (`lint.check_creature_spell_rows`). The note line `contributed ...` now omits tables with a zero count.

**New lints** (all in `lib/lint.py`, all `WARNING:`, all run under `--check` *and* the full run through
`generate._t1_content_warnings`; `--check` has no promoted-aware spell or SkillLineAbility state, so it judges the
stock client rows plus the declared SkillLineAbility rows, and the full run adds the live ones):

- `check_totem_tools` fires on a custom (id >= 200000) `SpellClassSet` 11 spell whose built row has non-zero
  `Totem_1/2` or `RequiredTotemCategoryID_1/2` (ruling 3A.8: the rework drops the Earth/Fire/Water/Air Totem item
  requirement). Fix: zero the four columns in `raw_overrides`.
- `check_hidden_learned_spells` fires on a custom spell with `Attributes & 0x80` (DO_NOT_DISPLAY) and not `0x40`
  (passive) that a player learns: a SkillLineAbility row on a non-pet line, a `trained_by()` row, a talent
  rank, or a LEARN_SPELL (effect 36) target of any learned spell (followed transitively). The client hides it from the
  spellbook (P0's Healing Rain; that incident itself used `.learn`, which no data lint sees). Hidden passives, hidden
  helpers nobody learns, pet-line rows and pure LEARN_SPELL carriers (every effect is effect 36, the stock 59672
  talent-rank shape) are silent. Allow: `lint.HIDDEN_LEARNED_ALLOW` (empty).
- `check_ground_effect_haste` fires on a custom spell with a PERSISTENT_AREA_AURA effect that ticks hasted:
  `AttributesEx5 & 0x2000` (the Blizzard 10 / Rain of Fire 5740 clone trap) or a periodic damage/heal aura (3, 8, 20,
  53, 89 = `SpellInfo::HasPeriodicDamageOrHealEffect`). Fixed-tick ground effects use the trigger shape: persistent
  area aura (dummy) + PERIODIC_DUMMY on the caster + a script casting one single-target spell per target. The core's
  own fixed-cadence ids (`IsFixedCadencePeriodic`, Echo of Light today) are exempt via
  `lint.FIXED_CADENCE_PERIODIC_SPELLS`: extend it when `FIXED_CADENCE_PERIODIC_SPELLS` in SpellAuraEffects.cpp grows.
  Allow: `lint.GROUND_HASTE_ALLOW`.
- `check_spell_proc_rows` fires on a declared `spell_proc` row that `SpellMgr::LoadSpellProcs` logs
  (SpellMgr.cpp:2112-2117). The effective ProcFlags is the row's, or the spell's DBC `ProcTypeMask` when the row has
  0. It warns when that is 0; when there is no `SpellPhaseMask` and the flags intersect
  `REQ_SPELL_PHASE_PROC_FLAG_MASK` (a done-spell or periodic proc never matches: the 202766 Flametongue slip); and
  when a phase is set on flags outside the mask. A rank-chain row is judged on its base rank's flags only. Allow:
  `lint.SPELL_PROC_ALLOW` (id -> reason).
- `check_shadowed_spell_procs` fires on a declared per-rank `spell_proc` row that a negative rank-chain row in the
  final set shadows. `LoadSpellProcs` has no ORDER BY, so negative rows load first, claim every rank of the chain, and
  the declared per-rank row is dropped at boot ("listed in `spell_proc` has duplicate entry"). The final set is the
  replayed live table minus `remove_spell_proc()` and prune deletions, with the declared rows over it; chains are
  `spell_ranks` plus the talent rank chains. Fix: `remove_spell_proc(-first_rank)` or declare the proc on the chain
  key. Allow: `lint.SHADOWED_PROC_ALLOW`.
- `check_trainer_spell_level` fires on a `trained_by()` row on a class trainer (`PRICED_TRAINER_IDS` plus every
  `trainer` of Type 0) whose `ReqLevel` is below the spell's `SpellLevel`: `SpellInfo::GetAuraRankForLevel` returns
  no rank for a target below SpellLevel - 10, so a single-rank buff learned early (Bloodlust, SpellLevel 70, learned
  at 60) fails on lower-level group members. Only spells that go through rank selection are judged (a friendly
  APPLY_AURA or party / raid area-aura effect, none of COOLDOWN_ON_EVENT / ALLOW_LOW_LEVEL_BUFF /
  ONLY_PROC_ON_CASTER); an attack or a stun is not. Allow: `lint.TRAINER_SPELL_LEVEL_ALLOW` (empty).

Each allow set holds the hits that existed when the lint was written, one comment per entry. `SPELL_PROC_ALLOW`
holds only druid Intensity's deliberate ProcFlags 0 row (the paladin / warlock taken-only rows that carried a useless
phase were cleaned up 2026-10-31: do not set `spell_phase_mask` on taken-only flags). `SHADOWED_PROC_ALLOW` is empty:
the priest rows it held (Blessed Recovery, Surge of Light, Holy Concentration, Serendipity, Body and Soul, Grace rank
3), shadowed by the stock rank-chain rows -27811, -33150, -34753, -63730, -64127 and -47516, were fixed 2026-10-31 by
`remove_spell_proc()` of the chain rows (plus a HIT phase on the done-spell rows) and by dropping Grace rank 3's
positive row, which the -47516 chain row already covers through the talent rank chain.

**`lint.TOOL_FREE_CLASS_SETS`** (empty frozenset) widens `check_totem_tools` to every spell of the listed
`SpellClassSet`s: the declared ones, stock ids included, and the undeclared stock spells in the base Spell rows (stock
client file under `--check`, the live rows in the full run). 117 stock family-11 spells hold a tool column, 42 of them
declared today, so a learnable stock rank SH0 forgot to declare and strip is flagged. SH0 adds `11` once it has
stripped `RequiredTotemCategoryID_1`; until then stock rows stay quiet.

**Shaman family-bit rules.** `lint.SHAMAN_FAMILY_RULES` (`SpellClassSet` 11) joins `FAMILY_BIT_RULES`: (a) no custom
spell may carry d1 b5 or d1 b10 (`0x420`, `SPELL_SPECIFIC_ELEMENTAL_SHIELD`, SpellInfo.cpp:2241-2248: two such
spells are mutually exclusive) unless its id is in the rule's `exempt_ids` (empty; SH0 adds a custom real shield);
(c) no reader mask (effect mask or `spell_proc` family mask) may contain d2 b11 or d2 b31 (`0x80000800`, the Orc and
Draenei racials). Rules (b) and (d) are no-ops (zero masks), and `exempt_name_prefix=""` means no name exemption.
The other shaman "never take" bits (d0 b10 on a shield with NO_THREAT, d2 b14 root DR) and "imbue auras leave d1
b11" depend on attributes or on the spell's role, which the table cannot express: they are SH0's targeted tests.

**ID blocks.** `source/ids.yaml` now names the client-patch tables' ranges (`spellicon` 90100-90499, `soundentries`
90001-90199, `spellvisual` 90001-90399 shared by SpellVisual/Kit/EffectName, `creaturedisplayinfo` and
`creaturemodeldata` 90001-90499, `gameobjectdisplayinfo` 90001-90099, `summonproperties` 3000-3099; stock tops out
at 2935; `soundentries` and `spellvisual` were widened by Death Knight T1, `spellicon` from 90399 and the `spell_group`
block from 1299 to 1399 by Rogue T1, `spellvisual` to 90399 and `spellcategory` to 1319 by Warrior T1) and a
`reservations:` key holding each class's slice of every table (shaman,
deathknight, rogue and warrior; `healsim` reserves the healing sim's spells). Nothing mints
from the new blocks; `lib/test_id_blocks.py` checks that blocks of one table do not overlap, that a reservation sits
inside its block and overlaps no other class, and that every custom id `source/classes/<class>/` declares inside a
tool-wide block is inside that class's reservation. A new class reserves its slice in `ids.yaml` first (keep to
`.agents/plans/shaman-rework/shaman-rework.PLAN.md` s4's table of who owns what).

### Death Knight T1: rune costs, threat rows, creation data, the class row and SkillLineAbility overrides

Added for the Death Knight rework (`.agents/plans/death-knight-rework/`, T1). No Death Knight content: these are the
helpers, lints and id blocks DK0a / DK0b and the spec stages call. Nothing here needs C++; every table already has a
loader.

**`spell_rune_cost(cost_id, *, blood=0, unholy=0, frost=0, runic_power=0, comment="")`** declares a
`spellrunecost_dbc` row (`SpellRuneCost.dbc`): the runes a rune ability costs and the Runic Power it generates. The
server overlay row and, merged over the stock file, the client row both go out (the first declaration makes patch-Z
carry `SpellRuneCost.dbc`; expect `lint.check_client_patch`'s "new to the patch" WARNING once).

```python
# S1: Marrowrend costs one Frost and one Unholy rune and generates 20 Runic Power.
spell_rune_cost(2600, frost=1, unholy=1, runic_power=20, comment="Marrowrend")
spell(id=203xxx, name="Marrowrend", power_type=5, raw_overrides={'RuneCostID': 2600}, ...)
```

- **Column order is Blood, Unholy, Frost.** `SpellRuneCostEntry::RuneCost[3]` is indexed by `RuneType`
  (`RUNE_BLOOD` 0, `RUNE_UNHOLY` 1, `RUNE_FROST` 2, Player.h; Spell.cpp:5627-5634, 5682-5686). The comment
  `0=blood, 1=frost, 2=unholy` at DBCStructure.h:1843 is wrong (core files stay stock: documented, not fixed). Stock
  proof: 241 Icy Touch = (0, 0, 1, 100), 482 Frost Presence = (0, 0, 1, 0), 797 = (0, 1, 1, 150), 1144 Empower Rune
  Weapon = (0, 0, 0, 250). The arguments are keyword-only so the order cannot be transposed.
- **`runic_power` is whole Runic Power as the player reads it** (10, 15, 20, 25) and is stored x10 (100 = 10 RP;
  `TakeRunePower` adds `runePowerGain * Rate.RunicPower.Income`, Spell.cpp:5716-5718; the maximum is 1000).
- **It applies only to a `PowerType` 5 (RUNE) spell:** `CheckRuneCost` returns OK otherwise (Spell.cpp:5605) and
  `TakePower` calls `TakeRunePower` only for `POWER_RUNE` (:5531). A `RuneCostID` with no row is a free cast
  (:5621-5624, 5666-5668). 168 stock spells carry a `RuneCostID` with another `PowerType` (Death Coil 47541 =
  power 6 / cost 422): inert, so the lints only judge custom spells (id >= 200000).
- **Reuse a stock row first.** Marrowrend needs (0, 1, 1, 200) and Scourge Strike (1, 0, 1, 150) (DATA 1.6); 475
  stock rows already cover most costs.
- `cost_id` must be inside `ids.yaml`'s `spellrunecost` block (2600-2629; stock tops out at 2513, DK reserves
  2600-2609). The helper raises on an id outside it, a rune count outside 0..2 (more than two of one type is payable
  only with Death Runes: widen `registry.RUNE_COUNT_MAX` deliberately), a non-int or bool, `runic_power` outside
  0..100, and an all-zero row.
- Lints: **ERROR** (`--check` exits 1 too) for a spell whose `RuneCostID` is inside the block with no declaration
  or a declaration with no stock file to merge into; **WARNING** for a custom spell with a `RuneCostID` and a
  `PowerType` other than 5, for a `RuneCostID` that is neither stock nor declared (a free cast), and for a declared
  row equal to a stock row (it names the stock id). Without the stock file the last two collapse into one WARNING.

**`spell_threat(spell, flat_mod=None, pct_mod=1.0, ap_pct_mod=0.0)` / `remove_spell_threat(spell)`** declare a
`spell_threat` row (`SpellMgr::LoadSpellThreats`) and its key-exact removal. Stock Death Knight threat lives in
rows keyed by spell id (Chains of Ice 45524 flat 240, Death Grip 49576 110, Strangulate 49916 138, Lichborne 49039
110, Hungering Cold 51209 112, Death and Decay 52212 pctMod 1.9, Scourge Strike 55090 / 55265 / 55270 / 55271 flat
51 / 63 / 98 / 120, Rune Strike 56815 pctMod 1.75, and zero rows on 47568, 48743, 50181, 50422, 63611, 65142): a
rework that mints a new id for one of them loses its threat unless the new id gets a row. Blood Presence's own
threat is a `MOD_THREAT` aura, not this table. A spell that is neither declared nor stock prints a WARNING (the
loader drops the row, SpellMgr.cpp:2358-2362).

**`creation_action(race, class_id, button, action, action_type=0)` / `creation_cast(spell, class_mask, race_mask=0,
note="")` / `creation_skill(skill, class_mask, race_mask=0, rank=0, comment="")`** and their `remove_creation_*`
counterparts declare what a newly created character starts with: `playercreateinfo_action`,
`playercreateinfo_cast_spell` and `playercreateinfo_skills`. All three load once at boot
(`ObjectMgr::LoadPlayerInfo`, not reloadable) and **only affect characters created afterwards**.

```python
# DK0a: the class-6 action bar on each race, the creation Blood Presence cast and First Aid.
for race in (1, 2, 3, 4, 5, 6, 7, 8, 10, 11):
    creation_action(race, 6, 4, 49000)                # a row per race: the action table has no mask
remove_creation_cast(48266, 32)                        # the stock creation cast (0, 32, 48266)
remove_creation_skill(129, 32)                         # (0, 32, 129, 4, 'Death Knight - First Aid') only
```

- `creation_action` takes one playable race (1-8, 10, 11), a class 1-11 except 10, a button 0..143
  (`MAX_ACTION_BUTTONS`) and an `action_type` of 0 (spell), 0x40 (macro) or 0x80 (item). Key (race, class, button).
- `creation_cast` / `creation_skill` take masks, checked like the loader (ObjectMgr.cpp:4680-4690): the race mask is
  0 (every race) or within the playable mask (1791), the class mask is non-zero and within the playable classes
  (1535). `creation_skill`'s `rank` is 0..15 (`MAX_SKILL_STEP`): the server skips a higher-rank row at boot.
  **`playercreateinfo_cast_spell` has no primary key:** the key-exact `DELETE` on (raceMask, classMask,
  spell) removes every duplicate, which is what a declaration or a removal means. The removals are key-exact, so a
  shared-mask row such as `(0, 35, 55)` Two-Handed Swords is never touched by `remove_creation_skill(129, 32)`.
- Ordinary declared tables: DELETE-then-INSERT, diffed against the live rows, pruned when a declaration this tool
  emitted is dropped (a dropped override of a stock key is reported, never deleted). The live-state reader stays the
  union of INSERTs. That reader does not replay an `UPDATE` (`2026_09_06_01.sql` re-points a priest button) or a
  hand-written `DELETE` (the P0 spike's file deletes the `(0, 32, 48266)` cast). A DK override of a stock key
  renders once and converges on the next run, `remove_creation_cast(48266, 32)` emits one extra idempotent `DELETE`
  and converges, and a key nobody declared is never touched (`lib/test_creation_data.py`). **The gotcha:** a
  declaration whose values equal a row a hand-written `DELETE` removed (or that equal the original INSERT of a row a
  hand `UPDATE` changed) reads as unchanged and is never re-emitted, so `creation_cast(48266, 32, note=...)` renders
  nothing while the DB has no row, and the same holds for `spell_threat(8056, ...)`. To bring such a row back, change
  one value or re-add it by hand. It was not fixed here because the replayed reader (`load_replayed_table_rows`)
  would also have to feed `render_removal_blocks`' live keys, or every removal of a hand-deleted row (DK0a's 48266)
  would print a spurious "doesn't exist anywhere" WARNING; that is more than a contained change.
- `chr_class` / `spell_rune_cost` skip the prune circuit breaker (`TableSpec.prune_when_empty`): dropping the last
  declaration still DELETEs the overlay row, so `chr_class(6, ...)` can be undone through the tool.
- A spell action or creation cast that names a spell nobody declares prints a WARNING.

**`chr_class(class_id, **columns)`** is a full-row override of a stock `ChrClasses.dbc` row (`chrclasses_dbc`,
server-side only, no client patch), built like `shapeshift_form()`: every column starts at the stock value and only
the named ones change. An overlay row replaces the whole row (power type, `SpellClassSet`, `Required_Expansion`,
names), so hand SQL is a trap. It accepts the SQL column name or `DBCStructure.h`'s field name for the four it
exposes (`CinematicSequence`, `powerType`, `spellfamily`, `expansion`). The use is the race intro cinematic for new
Death Knights: `WorldSession::HandlePlayerLogin` (CharacterHandler.cpp:887-898) plays `ChrClasses.CinematicSequence`
of the class if it is non-zero, else `ChrRaces.CinematicSequence` of the race, and only the DK class row has a class
cinematic in 3.3.5 (165). `chr_class(6, CinematicSequenceID=0)` therefore gives every new DK its race's intro with
no C++ and no client patch (confirm in the DK0a playtest). Stock row 6 in `ChrClasses.dbc`: DisplayPower 6,
SpellClassSet 15, Required_Expansion 2, CinematicSequenceID 165, names "Death Knight". Without the stock file
`generate.py` stops with an ERROR naming it.

**`override_skill_line_ability(sla_id, **columns)`** re-declares the STOCK `SkillLineAbility.dbc` row (not a
promoted one, so deleting a keyword later restores that column's stock value; a row only a migration added falls
back to its live row) with only the named columns changed, instead of copying every column by hand (the P0
spike's `_stock_sla_unlearned`). It accepts the typed names `skill_line_ability()` uses (`skill_line`, `spell_id`,
`class_mask`, `race_mask`, `min_skill_line_rank`, `acquire_method`, `superseded_by`) and the raw SQL column names; an
unknown name or a non-live id raises. The entry is exactly what `skill_line_ability()` builds, so the
superseded-ranks "a declared row wins" path keeps working.

```python
# DK0a: Icy Touch, Plague Strike, Death Coil, Blood Strike, Blood Presence, Rune Strike's enabler and Journeyman
# Riding stop auto-learning at level 1, and Heart Strike starts to (AcquireMethod 2, class mask 32).
for sla_id in (16231, 16238, 16433, 16616, 17016, 17101, 19641, 19184):
    override_skill_line_ability(sla_id, acquire_method=0)
override_skill_line_ability(19182, acquire_method=2, class_mask=32)
```

The live rows reach the registry through `spell_tables.dsl_live_data(..., skilllineability_rows=None,
chrclasses_rows=None)`: keyword arguments with a default, so every caller that predates them (`pull_dsl.py`,
`potency_report.py`, `pull_talents.py --dsl`, `test_id_blocks.declared_ids`) keeps working and the two helpers raise
a clear error when their rows were not passed. Either value may be a zero-argument callable, loaded on first use
(the SkillLineAbility replay takes about 13 s, so `--check` and `load_dsl_live_data` pay for it only when a file
calls the helper; the full run loads it once and shares it with its own later use).

**`--check` GCD-haste dry run.** The first P0 deploy stopped at `ERROR: gcd haste: Death Knight: 203684 ... all-zero
SpellClassMask`, which `--check` could not show. `--check` now runs the full run's GCD-haste computation
(`generate._gcd_haste_check_warnings`) over the stock Spell / Talent / TalentTab / SkillLineAbility rows with the
declared rows laid over them, `trainer_taught` = the declared `trained_by()` spells and the superseded-rank map the
full run uses (`superseded_ranks.superseded_ranks`, 2148 collapsed ranks), and prints each error or warning as
`WARNING: gcd haste (--check, stock approximation): ...`. It is a WARNING so the approximation (promoted migrations
are not replayed) cannot flip the exit code; the full run keeps the authoritative ERRORs. **The superseded map is
required:** with `superseded={}` (the handoff's first draft) the stock rows still list the collapsed ranks as
learnable and the committed tree printed six unrelated lines (three Paladin aura bit conflicts, two Hunter melee /
ranged overlaps, Hunter Black Arrow bit 7); a promoted-aware variant printed the same six, so promoted rows were not
the cause. With the map, today's tree prints nothing. `lib/test_dk_t1_check.py`: a learnable family-15 GCD melee
spell with an all-zero class mask produces the warning, the same spell with a mask bit does not.

**ID blocks and reservations.** `soundentries` is widened to 90001-90199 and `spellvisual` to 90001-90299 (the shaman
slices filled the old ends), and a `spellrunecost` block 2600-2629 is added. `reservations:` gains `deathknight`
(PLAN s4: spell 203000-203699, talent 60330-60389, SkillLineAbility 30720-30779, spell_group 1271-1285,
SpellDescriptionVariables 1230-1299, creature 300300-300339, plus the client-patch and `spellrunecost` 2600-2609
slices; 203680-203699, 1285, 30779 and 300338 / 300339 held the P0 spike: never reuse) and `healsim` (spells
202900-202909). A non-class owner reserves under its project name, so the overlap test protects it (the T0 collision:
Death Knight's first spell block swallowed the healing sim's spells).

**Rogue T1 (tooling for the rogue rework, no rogue content).**

- *ID blocks.* `reservations:` gains `rogue` (PLAN s4: spell 203700-204399 split shared 203700-203799 / Assassination
  203800-203949 / Combat 203950-204129 / Subtlety 204130-204279 / spare 204280-204399, talent 60390-60449,
  SkillLineAbility 30780-30839, spell_group 1286-1295, SpellDescriptionVariables 1300-1369, creature 300350-300369,
  SpellIcon 90370-90419, SoundEntries 90121-90140, SpellVisual / Kit / EffectName 90250-90299, CreatureDisplayInfo and
  CreatureModelData 90490-90499; 204370-204399, 1295, 30838-30839 and 300368-300369 held the P0 spike: never reuse).
  `spellicon` is widened 90399 -> 90499 and `spell_group` 1299 -> 1399. The rogue reserves no `gameobjectdisplayinfo`,
  `summonproperties` or `spellcategory` (T0: not needed).
- *A duration with a minimum and a maximum.* `spell(duration_ms=4000, max_duration_ms=24000)` builds
  `SpellDuration {Duration 4000, MaxDuration 24000}`; the core scales the aura between the two by the caster's combo
  points (`min + (max - min) * comboPoints / 5`), which is Rupture's "4 s plus 4 s per combo point". Without
  `max_duration_ms` nothing changes (`duration_ms` alone still means `Duration == MaxDuration`). A max needs a positive
  `duration_ms` and must be greater than it, and it cannot be combined with a raw `DurationIndex` override (that wins
  and leaves the ranged row unused). The client's `$d` and the potency `.total` tick count read the minimum. **The core
  scales by whatever combo points the caster holds when the aura is created, finisher or not** (it never checks
  `NeedsComboPoints`; the finisher's points are cleared in the finish phase, `Spell.cpp:4414`): a non-finisher with a
  range scales by the points it finds and spends none, and a helper triggered after the finisher consumed its points
  (an `AfterHit` script cast, a stored-bleed tick spell) always gets the minimum. Put the range on the aura the
  finisher's own cast creates.
- *Rogue family-bit rules.* `lint.ROGUE_FAMILY_RULES` (`SpellClassSet` 8, in `FAMILY_BIT_RULES`, so `--check` and the
  full run both apply it): a custom spell may not carry d0 b11 (`0x800`), d0 b22 (`0x400000`) or d0 b25 (`0x2000000`).
  The role-dependent "never take" bits (d0 b16 / b20 / b17 / b26, d1 b1 / b2 / b3 / b18, the DR and Preparation bits)
  are the rogue stages' targeted tests.

### Warrior T1: id blocks, family bits and the capstone tooltip test (tooling only, no warrior content)

- *ID blocks.* `reservations:` gains `warrior` (PLAN s4: spell 204400-204899 split shared 204400-204489 / Arms
  204490-204629 / Fury 204630-204769 / Protection 204770-204799 / spare 204800-204868; talent 60450-60489,
  SkillLineAbility 30840-30869, spell_group 1296-1305, SpellDescriptionVariables 1370-1429, creature 300370-300389,
  SpellIcon 90420-90449, SoundEntries 90141-90150, SpellVisual / Kit / EffectName 90300-90339, spellcategory 1313-1319).
  The P0 spike's spells 204869-204899, spell_group 1305 and creatures 300388-300389 are never reused; talents
  60488-60489 and SkillLineAbility 30868-30869 were reserved for it but never declared (also never reuse). `spellvisual`
  is widened 90299 -> 90399 and `spellcategory` 1309 -> 1319. The September Protection build's ids (spells
  200028-200066 except the mage's 200037 / 200044, talents 60003-60006) stay outside the reservation, pinned exactly as
  `WARRIOR_LEGACY` in `lib/test_id_blocks.py` (a spec stage that retires one shrinks that set). The helper
  `class_slice_problems(class_name, script_name, scanned)` generalises the rogue VFX-script ownership rule
  (`rogue_slice_problems` is a wrapper) and `WARRIOR_VFX_SCRIPT` names the warrior's, for stage V.
- *Family bits.* `source/classes/warrior/_masks.py` names the FAMILY-BITS s5 allocation (d2 b0 Heroic Leap, b1 Colossus
  Smash, b2 Rampage, b3 the R1 damaging-ability group; b4-b7 reserved; append-only) and `lint.WARRIOR_FAMILY_RULES`
  (`SpellClassSet` 4, in `FAMILY_BIT_RULES`, so `--check` and the full run both apply it): a custom spell may not carry
  d0 b0 / b1 / b17 / b24, d1 b5 / b6 or d2 b31, and no reader mask may contain d2 b31. The role bits (d0 b7 / b10 / b23,
  d1 b8 / b9 / b18 / b21, category 132) are the warrior stages' targeted tests. `lib/test_warrior_family_rules.py`.
- *Capstone tooltips.* `source/classes/warrior/_tooltips.py::_desc(text, capstone, last)` builds the user's capstone
  paragraph (grey `|cFF9D9D9DCapstone Bonus: <clause>|r` below the last rank, plain on the last, the same clause on
  every rank, never in `AuraDescription_Lang_enUS`); `lib/test_capstone_format.py` checks it:
  `capstone_problems(class_name, expected_names)` loads `source/classes/<class>/` and fails any rank that breaks the
  format, any listed talent that is missing or ambiguous, and any unlisted talent whose rank text says "capstone". Add
  the class to `EXPECTED_CAPSTONES` in that file when its talents get capstones, and list every capstone talent by name
  in the stage handoff (a clause without the label cannot be found by a text scan).

### Declaring tooltip variables (P9)

SpellMods never show up in a tooltip, so stock shows a talent's percent bonus through a
`SpellDescriptionVariables.dbc` entry: named variables the spell's text reads as `$<name>`, keyed
by the spell's `SpellDescriptionVariableID` (Frostbolt's stock entry 167 checks which Piercing Ice
rank you know). `tooltip_vars()` declares one; pass the result to `spell(tooltip_vars=...)`, and one
entry can serve many spells:

```python
from lib.dsl.registry import has_aura, knows, product, talent_mult, tooltip_vars

# Explicit id from source/ids.yaml's `spelldescriptionvariables` block (1000-1999), never a stock
# id: stock entries are shared by dozens of stock spells.
frost_talents = tooltip_vars(
    1000, "Frost damage talents shown on Frost spell tooltips",
    piercing=talent_mult(piercing_ice),            # 1 + highest known rank's effect 1 value / 100
    arctic=talent_mult(arctic_winds, effect=2),    # reads effect 2 instead
    mult=product("piercing", "arctic"),
)

frostbolt_116 = spell(
    id=116, ..., tooltip_vars=frost_talents,
    # {potN*var}: the potency range (or .avg/.total) times the variable - see lib/potency.py
    raw_overrides={..., 'Description_Lang_enUS': 'Deals {pot2*mult} Frost damage ...'},
)
```

- `talent_mult(talent, effect=1)` takes a `talent(...)` object or its rank spells in rank order,
  and reads each rank's value from the rank spell (`$<id>m<n>`), so retuning the talent updates
  the tooltip. It also defines helper variables `<name>1` .. `<name><n-1>`.
- `knows(spell, then, else_=1)` / `has_aura(spell, then, else_=1)`: one condition. Branches are a
  number or an expression as written inside `${...}`, e.g. `"$<base>*1.2"`.
- `product("a", "b", 1.1)` multiplies earlier variables and/or numbers.
- A raw right-hand side string also works (`base="${$m1*2}"`).

Client rules (P9.0 spike, `docs/potency-system.md`'s "Tooltip" section), enforced at declaration:
inside an entry, read another spell's value as `$<id>m<n>`, never `$<id>s<n>`, which stops the
variable resolving; reference only variables defined earlier; names are lowercase and at most 12
chars, `talent_mult()` helpers included (longer names read 0 in game). A bare `$<var>`
in tooltip text displays as a whole number, so show a multiplier inside math: `${100*$<mult>}`.

`generate.py` also checks every spell (stock entries included): a `$<var>` in Description or
AuraDescription that the spell's entry doesn't define, or a variable with no entry at all, is an
`ERROR:` and stops the run before any SQL is written. So is a spell id in a declared entry that
exists nowhere. A spell carrying an entry it never uses is only a `note:`. Entries are
client-only (no SQL table): they ship in `patch-Z.mpq`, merged over
`var/extractors/dbc/SpellDescriptionVariables.dbc`, which must be extracted (see Setup).

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
