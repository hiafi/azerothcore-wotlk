# dbc-tools (`apps/dbc-tools/`)

Generates `spell_dbc`/`Talent.dbc`/`item_dbc`/etc. content from
`apps/dbc-tools/source/{spells,talents,items.csv}` via `apps/dbc-tools/generate.py`, producing a
pending SQL migration plus a client patch MPQ. Full design and workflow:
`apps/dbc-tools/README.md`. Bugs found and fixed via live-client/live-engine verification are
logged in `docs/dbc-build-pipeline.md` — read that log before assuming a surprising-looking column
or value is intentional.

## `Item.dbc` — the newest table this pipeline touches

Added to fix a real bug (see `docs/bugs-and-fixes.md`'s "blank bag icon" entry for the full
investigation): a custom `item_template` entry above **56806** (the last real client item) needs a
matching row in `item_dbc` just for the server to load it fully, but that alone does nothing the
*client* can see — the client has its own separate local `Item.dbc`, and only a real client patch
(this pipeline's normal output) teaches it about a new entry. `source/items.csv` is a flat file (no
per-class split like `spells/`, since nothing here is class-specific); the reserved ID block is
`item` in `source/ids.yaml` (70000–79999, chosen to include the one item that pre-dated this
table's use, entry 70001). If you're touching `var/extractors/dbc/Item.dbc`: it must come from
`patch-enUS-3.MPQ` specifically (the highest-numbered, most-patched locale MPQ under
`client/MPQs/enUS/`) — earlier patches (`patch-enUS.MPQ`, `patch-enUS-2.MPQ`) also contain an
`Item.dbc` but it's shadowed/stale, smaller, and not what the client actually ends up using.

## Watch out: `generate.py` has no per-table scope flag

Running it regenerates the pending SQL for *every* table at once — `spell`/`talent`/`item`/etc. If
`source/spells/*.csv` or `source/talents/*.yaml` have in-progress, not-yet-promoted edits sitting
in them (someone else's rework mid-flight), a run made for an unrelated reason (e.g. adding one
`item_dbc` row) will sweep those into the same output file. Check the printed "editing N existing
spell(s) [...]" line before treating the generated SQL as ready to apply — if it names IDs you
didn't touch, hand-extract just the block(s) you actually meant to ship into their own migration
file rather than applying (or discarding) the whole thing.

## Watch out: never delete an earlier generated `pending_db_world/rev_*.sql`

`generate.py` emits **delta** rows for `trainer_spell`, `spell_script_names`, `spell_bonus_data`
and `spell_proc`: `lib/trainer_state.py` scans `base/` + `updates/db_world/` + **`pending_db_world/`**
and anything already present there is "live" and skipped (`lib/spell_tables.py`'s
`rows_to_emit`). The DBC tables (`spell_dbc`, `talent_dbc`, …) deliberately ignore `pending_db_world/`
and are re-emitted in full every run. So generated pending files are meant to **accumulate**: each
new one carries a full DBC rebuild plus only the secondary-table rows the previous files don't
already have.

Deleting an earlier generated file *after* running `generate.py` silently drops every
secondary-table row it alone carried — the new file skipped them as live, and now nothing has them.
Git will often show this as a rename (`R old.sql -> new.sql`) because the DBC blocks are near-
identical, which hides that the small itemised blocks vanished. This shipped once (Priest Holy pass
deleting the Disc pass's file: 10 Disc spells lost their script bindings, procs and trainer rows —
`docs/bugs-and-fixes.md`). If you genuinely want one consolidated file, delete the old one
**before** running `generate.py`, never after; and treat an `R` on a `rev_*.sql` in `git status` as
a red flag to diff the `spell_script_names`/`spell_proc` blocks.

## SQL lint: generated output

`python3 apps/codestyle/codestyle-sql.py` lints every `pending_db_*/*.sql`, so generated files must
pass it. Cause of the old failures (hundreds per file, e.g. 145 backtick hits in each, 759 in the
Item.dbc one): spell `Description`/`AuraDescription` strings with embedded line breaks were written as
literal multi-line strings. The linter works line by line, so every continuation line was read as
SQL ("Missing backticks around (cloth)"), a tooltip line ending in a space tripped the trailing-
whitespace check, and a row whose string continued on the next line was judged the final row
("Missing semicolon"). The linter is right to be line-based; the fix is in the generator.
`sql_out._sql_literal` now writes `\n`/`\r` inside a string as the escape (MySQL decodes it to the
same bytes), so a row is one physical line. `sql_dump._read_value` decodes MySQL escapes, so it reads
both the new files and the older literal-multi-line ones. Rule for any new emitter: never put a raw
line break inside a quoted SQL literal. Already-committed `rev_*.sql` files keep the old form and
still fail the linter (never delete them, see above); only a file generated after this change is clean.

## The prune pass: removing a `scripted_by()` / `procs_on()` from source

Deleting a declaration from `source/classes/*` does **not**, on its own, delete the row. The delta
emitter above only ever speaks about rows it still declares, so before the prune pass existed a
removed binding stayed live in the world DB forever — costing a `Scriptname '<x>' ... not found`
boot error per orphaned `spell_script_names` row, and a proc chance nothing handles per orphaned
`spell_proc` row. Found via Shadow Reach's capstone rework (2026-09-23).

`lib/spell_tables.py`'s `render_prune_blocks()` now closes it: it emits a bare `DELETE` for any key
a **previous generated run** emitted that the source no longer declares, and `generate.py` prints
one line per removal.

Provenance is the whole design. A row is the tool's to delete only if a marker-bearing file
emitted it — `GENERATED_MARKER`, the `-- Generated by apps/dbc-tools/generate.py` first line every
`generate.py` output carries. The base dump, hand-written migrations and module SQL are excluded by
construction. Pruning "every row belonging to a spell id we manage" was considered and **rejected**:
the DSL declares plenty of *stock* spells just to edit a tooltip, and stock AzerothCore ships
`spell_script_names`/`spell_proc` rows for many of them (Penance 47540 → `spell_pri_penance`), so
that model deletes stock bindings and re-creates the "spells go inert" bug in
`docs/bugs-and-fixes.md`.

Two refusals, both of which print rather than act:

- **Stock overlap.** The orphaned key also exists in `data/sql/base/db_world/<table>.sql`, meaning a
  past run *overrode* a stock row instead of adding one — `DELETE` would leave a hole where
  AzerothCore has a row. Reachable only for the single-key tables; three such rows exist today
  (`spell_proc` `-14531`, `-45234`, `-47516`, the negative "this spell and all its ranks" ids).
- **Circuit breaker.** A table with emitted history but zero declarations this run means the source
  failed to load, not that everything was retired; the table's prune is skipped wholesale.

`--no-prune` disables the pass. Design notes:
`.agents/plans/dbc-tools-prune-pass/dbc-tools-prune-pass.PLAN.md`.

The emitted set is a **replay**, not a union: `sql_dump.read_table_statements` walks each generated
file's INSERTs and DELETEs in file order. That matters because the prune writes its own DELETEs into
these same files — a union would re-report every already-pruned row on every later run, and would
write a migration file even when nothing changed.

Note this interacts with the rule above: the prune reads *generated files still on disk*, so
deleting an earlier `rev_*.sql` also erases the tool's memory that those rows were ever emitted.

## WP-T: five more declared tables, and declared removals

`.agents/plans/druid-rework/druid-rework.WP-T-HANDOFF.md` (PLAN B11/§5.0) added five more world-DB
tables a `source/classes/*.py` file can declare - `spell_linked_spell`, `spell_group` +
`spell_group_stack_rules`, `spell_custom_attr`, `spellshapeshiftform_dbc` (`lib/dsl/registry.py`'s
`linked_spell`/`spell_group`/`spell_group_rule`/`custom_attr`/`shapeshift_form`) - so the druid
rework ships with **no hand-written `pending_db_world` file at all**. All five slot into the same
`lib/spell_tables.py` `SPELL_TABLES` machinery the original three (`spell_script_names`/
`spell_bonus_data`/`spell_proc`) already used: diff against live, DELETE-then-INSERT the rest,
silent on an unchanged rerun, and - since they're in `SPELL_TABLES` - automatically covered by the
prune pass above if a class file stops declaring one. Usage: `apps/dbc-tools/README.md`'s
"Declaring more world-DB tables" section.

Two design notes worth knowing before extending this further:

- **`spell_group`'s real SQL column is itself called `id`.** Every other declared table's dedup
  key (`load_classes_dir`'s cross-file duplicate check, keyed on `entry["id"]`) is a synthetic
  string that never collides with a real column name. `spell_group` is keyed on `(id, spell_id)`
  with `id` being the real group id column, so two different members of the *same* group would
  otherwise look like the same declaration twice. `entry["_dedup_id"]` is the escape hatch -
  `load_classes_dir` checks it before falling back to `entry["id"]` - see `spell_group()`'s and
  `load_classes_dir()`'s own docstrings. `leave_spell_group()` needs the same treatment.
- **`shapeshift_form()` needs a real extracted `SpellShapeshiftForm.dbc`.** Unlike the other four
  (plain world-DB tables with no DBC counterpart at all), this one builds a *full override row* -
  every column starts at the stock value and only the named ones change - so it has to read the
  stock row from somewhere. `var/extractors/dbc/SpellShapeshiftForm.dbc` didn't exist before this
  package; it was extracted the same way `Item.dbc` was (`patch-enUS-3.MPQ`, this doc's "Item.dbc"
  section above) - `smpq -x <mpq> DBFilesClient/SpellShapeshiftForm.dbc`, then flattened into
  `var/extractors/dbc/` (not left under a `DBFilesClient/` subdirectory - `state.BASE_DBC_DIR`
  expects the flat layout). 35 fields, 140-byte records, confirmed against `DBCStructure.h`'s
  `SpellShapeshiftFormEntry` and the file's own header. `Name_Lang_*` is `'x'` in `DBCfmt.h` (the
  AC struct never reads a form's name) but is real string-table-offset data in the file - marked
  `read_as_string` in `lib/dbcfmt.py`, same as `TalentTab`'s own name column, or a raw offset like
  `53` gets written straight into the `varchar(100)` SQL column instead of `'Bear Form'`.

**Declared removals** (`unbind_script`/`unlink_spell`/`leave_spell_group`/`untrain`) are a
separate mechanism from the prune pass above, for the case the prune pass explicitly can't cover:
retiring a row this tool never emitted itself (stock Blizzard data, or an older hand-written
migration) - the prune pass's whole notion of provenance is "did a *generated file* emit this",
and a stock row was never one. Provenance for a removal instead means "has a generated file's own
DELETE already covered this exact key" (`spell_tables.load_removed_keys` - a plain accumulation of
every matching-shape DELETE a past run has emitted for the table, not a replay against INSERTs the
way `load_generated_table_rows` is, since a removal never has an INSERT side to net against - the
declare-and-remove conflict check enforces that). A removal whose key doesn't exist anywhere (base
dump, migrations, module SQL) still gets emitted - the DELETE is a harmless no-op either way - but
prints a `WARNING:`, almost always a typo.

## T1: creature_template/creature_template_model

`.agents/plans/warlock-rework/warlock-rework.T1-HANDOFF.md` added two more declared tables -
`creature_template`/`creature_template_model` (`lib/dsl/registry.py`'s `creature_template()`/
`creature_model()`) - for a rework's own NPC (a talent's summoned add), so those also no longer
need a hand-written migration (the precedent this replaces, Tentacle of Madness, is
`data/sql/updates/db_world/2026_09_23_12.sql`). Usage: `apps/dbc-tools/README.md`'s "Declaring a
creature (T1)" section.

Two things make this pair different from every WP-T table above, both stemming from
`creature_template` being on the SQL linter's do-not-delete list (`apps/codestyle/codestyle-sql.py`'s
`not_delete`):

- **Upsert, never DELETE-then-INSERT.** `creature_template` is rendered with a new
  `lib/sql_out.py` function, `render_upsert_block` - `INSERT ... ON DUPLICATE KEY UPDATE <every
  non-key column> = VALUES(<column>);`, no DELETE ever. Reading one back (so a live upsert reads
  as "already declared" and a rerun stays silent) needed `lib/sql_dump.py`'s core tuple reader
  (`_read_tuples`, shared by `read_table_rows` and `read_table_statements`) to stop treating
  `ON DUPLICATE KEY UPDATE ...;` after a VALUES list as unparseable - previously
  `trainer_state.load_table_rows('creature_template')` silently skipped any such file (see that
  function's own docstring, which documented this as a known gap before T1 closed it).
  `creature_template_model` (keyed on `CreatureID, Idx`) is narrow enough to keep the ordinary
  `render_generic_table_block` DELETE-then-INSERT path every other table here uses - only
  `creature_template` itself needs the upsert.
- **Never pruned.** Both tables are deliberately kept out of `SPELL_TABLES`/`render_prune_blocks`
  entirely - a separate `CREATURE_TABLES` tuple plus `load_creature_table_index()`/
  `render_creature_blocks()`/`render_creature_retirement_report()` in `lib/spell_tables.py` handle
  them instead. `creature_template` can't be DELETEd at all, and pruning only the model row would
  leave a creature with no visible model - so a declaration dropped from source is only ever
  reported (`render_creature_retirement_report` reuses `SpellTableIndex.rows_to_prune`'s orphan
  computation, it just never turns the result into SQL), never deleted automatically.

`creature_template`'s column list and per-column schema `DEFAULT`s are parsed from its own
`CREATE TABLE` (`sql_dump.parse_create_table_columns`/`parse_create_table_defaults`) rather than
hand-transcribed - the table is ~55 columns wide, and `parse_create_table_columns`'s own docstring
already explains why hand-transcribing a table that wide is its own source of bugs.
`creature_template()` builds a **full** row from that: an explicit `**columns` value, else (for an
entry that already exists) that column's *current live value* - see "Overriding an existing entry"
below - else a handful of documented overrides for columns where `ObjectMgr::CheckCreatureTemplate`
rejects or silently rewrites the schema's own DEFAULT at boot (`unit_class` 0 is invalid, becomes 1;
`BaseAttackTime`/`RangeAttackTime` 0 becomes `BASE_ATTACK_TIME`), else the real schema default.
`creature_template_model` is narrow (6 columns) and stays a hand-typed column tuple like every
other table above.

The SQL linter needed one narrow exception for the upsert shape to pass at all -
`insert_delete_safety_check` (`apps/codestyle/codestyle-sql.py`) normally demands a `DELETE`
immediately before every `INSERT`, which an upsert into a `not_delete` table can never have. The
exception (marked `# Custom:`) only fires when the `INSERT` targets a `not_delete` table **and**
its own statement carries `ON DUPLICATE KEY UPDATE` before the terminating `;` - a plain `INSERT`
anywhere still needs its `DELETE` exactly as before.

`source/ids.yaml`'s `creature` block is `300000-300999` - four live custom `creature_template`
entries already sat in it before this block existed (300001 Frozen Orb, 300002 Meteor Missile,
300100 Divine Star, 300102 Tentacle of Madness), and the warlock-rework plan (§4.5) pre-reserved
300140-300179 inside it for the Affliction/Demonology/Destruction passes that use this helper next.

### Test and tool NPCs (dpssim MT0)

`source/ids.yaml` has a second creature block, `npc_tools` (900000-900099), accepted by
`_validate_creature_entry` alongside `creature`. The training dummies (900001-900009) and healing
dummy (900011/13/14) are declared in `source/npcs/training_dummies.py`; `generate.py` loads
`source/npcs/` with the same `load_classes_dir` and merges it into the class registry
(`_merge_npc_declarations`). 900010 and 900012 stay hand-written.

`lib/sql_dump.py` now reads `REPLACE INTO` like `INSERT INTO`. It had to: 900001-900006, 900010
(`2026_09_01_00.sql`) and 900012 were created with `REPLACE INTO`, so the reader never saw them and a declaration could not
compare as live. MySQL's semantics (delete the same-key row, then insert; omitted columns are not kept) already
hold at every replay site because each stores `rows[key] = row`, never `.update()`; the plain-union
readers have no old row to drop. The same work fixed column lists wrapped over several lines (the
hand-written REPLACEs do this): the first name on each line kept its newline, so `name`,
`DamageModifier` and `HealthModifier` read as absent. The same fix also corrects
`trainer_spell.ReqAbility2` in `2026_09_27_00.sql`; every value of that column is 0, so it can only
remove false diffs.

Known replay gap: `UPDATE ... WHERE entry IN (...) AND ScriptName = '...'` (the `IN (...)`
list, which `parse_and_equality_conditions` rejects, `2026_09_29_03.sql`) is not replayed, so
900001-900003 read as still on `npc_training_dummy` and re-emit one harmless `ScriptName` upsert.

### Three correctness fixes from code review (2026-09-28)

All three were found by checking T1's first commit against this repo's *actual* migration
history, not just re-reading the code - creature_template/creature_template_model turned out to
have real precedent the original three declared spell tables never did (a hand-written `UPDATE`
after the original `INSERT`, and a partial-column-list `INSERT`), which the design hadn't
accounted for:

- **Live state must replay `UPDATE`/`DELETE`, not just union every `INSERT`.** Frozen Orb 300001's
  `flags_extra` was inserted as `194` and later hand-fixed to `66` via a plain `UPDATE ... WHERE
  entry = 300001 AND flags_extra = 194` (`data/sql/updates/db_world/2026_09_01_01.sql`) - its
  `CreatureDisplayID` went through several such revisions too. `trainer_state.load_table_rows`
  (every other declared table's live-state reader) only unions `INSERT`s, so it kept reporting
  `194` as live forever; a re-declaration matching that stale value would have compared as
  unchanged and silently never applied the real fix. `lib/spell_tables.py`'s `load_creature_table_index`
  uses `trainer_state.load_replayed_table_rows` instead - single or composite key
  (`sql_dump.apply_statements`/`apply_composite_key_statements`), including a new AND-guarded
  `UPDATE` shape (`` `col` = n AND `other` = v ``, the exact idiom this repo's hand-written creature
  fixes use) that `sql_dump.py`'s existing replay machinery didn't recognize before.
- **Overriding an existing entry must not wipe columns it doesn't mention.** `creature_template()`
  originally always built from schema defaults, even for an already-existing `entry` -
  `_validate_creature_entry` explicitly allows overriding any live entry in the block, so
  re-declaring Tentacle of Madness to fix just its `ScriptName` would have silently reset its
  faction, levels, flags and every modifier. Fixed the same way `shapeshift_form()` already
  handles its own full-row override: start from the entry's current live row
  (`existing_creature_rows`, now full rows keyed by entry, not just a bare id set) and only
  overwrite what's explicitly passed.
- **A missing column's implicit value isn't 0 for every table.** `spell_tables._same_row` assumed
  a column absent from a live row defaults to `0`/`NULL` - true for the original spell tables, but
  wrong for `creature_template` (`minlevel`/`speed_run`/`RegenHealth`/... default to 1 or more).
  Real precedent: three module SQL files (`mod-transmog`, `mod-mythic-plus` x2) `INSERT
  creature_template` with a partial column list omitting exactly this kind of column. `TableSpec`
  gained a `defaults` field (`CREATURE_TEMPLATE_DEFAULTS`/`CREATURE_TEMPLATE_MODEL_DEFAULTS`) that
  `_same_row` checks before falling back to the old 0/`None` guess; every other table's `TableSpec`
  leaves it empty and is unaffected.

## Paladin T1: `spell_category()` and `remove_spell_proc()`

`spell_category(id, flags)` declares a `spellcategory_dbc` row (a `SPELL_TABLES` entry, so diff/prune
like `custom_attr`); ids come from `ids.yaml`'s `spellcategory` block (1300-1309, stock max 1253).
The same declared rows also go into the client patch: `generate.py` merges them over the stock
`var/extractors/dbc/SpellCategory.dbc` (`dbcfmt.SPELLCATEGORY`, fmt `ni`, not in `ALL_TABLES`/
`SECONDARY_TABLES` so the SQL is not emitted twice) into patch-Z.mpq, and stops with an error if
categories are declared but that stock file is missing (extract it from the highest-numbered
`patch-enUS*` MPQ that holds it, flattened, like `Item.dbc` above). The server blocks category siblings
(same `SpellFamilyName`) but sends them to the client only for spells with
`SPELL_ATTR0_CU_FORCE_SEND_CATEGORY_COOLDOWNS` (`custom_attr` 0x10000000; core sets it only for Aimed
Shot); the client's sweep comes from its `Spell.dbc` `Category`/`CategoryRecoveryTime` plus the shipped
row. An in-game `.cooldown` plus visual sweep check on a sibling remains advisable.
`lint.check_undeclared_spell_categories` makes `generate.py` error on a spell using a block
category nobody declared (the server would silently drop the cooldown).

`remove_spell_proc(spell)` is a `REMOVAL_TABLES` entry on `spell_proc` (negative ids = whole rank
chain). Trap: `SpellMgr` builds a default row per spell id only when the spell has a trigger aura AND
non-zero DBC `ProcTypeMask`; an explicit row with ProcFlags 0 inherits them too. So -31871 (flags 0)
and Redoubt 20128/20131/20132 are disabled by the removal alone, but a trigger-aura spell with flags
needs `ProcTypeMask` zeroed on every rank. `lint.check_removed_proc_flags` warns per rank (a negative
id expands over the Talent.dbc rank chain: DSL talent ranks first, else existing `SpellRank_1..9`),
conservatively ignoring the trigger-aura condition. Both new checks run on a full `generate.py` run
only, not `--check`.
`lint.check_removed_proc_flags` warns while `abs(id)`'s `ProcTypeMask` is non-zero (other ranks of a
negative id are not checked).

## Watch out: one client DBC, one patch archive

Five scripts each own a patch letter: `generate.py` → `patch-Z.mpq` (Spell/Talent/Item/…),
`build_patch_m.py` → `patch-M.mpq` (SpellVisual*/CreatureDisplayInfo/CreatureModelData/
GameObjectDisplayInfo/SoundEntries + `SPELLS/` models and `SOUND/` sounds), `build_patch_i.py` →
`patch-I.mpq` (`SpellIcon.dbc` + `Interface/Icons/*.blp`), `patch_gt_tables.py` → `patch-Y.mpq` (GT
tables), `build_patch_f.py` → `patch-F.mpq` (Bear/Cat Form model assets only — its
CreatureModelData/CreatureDisplayInfo rows, IDs 90100–90299, are written to the shared working copy
and ship in patch-M; see `docs/shapeshift-appearances.md`). The client loads lettered patches
alphabetically and the **highest letter wins per file**, so a DBC packed into two archives is silently served from
whichever has the later letter — usually a stale copy. That's exactly what blanked every custom
`SpellIcon` row minted after patch-M's last rebuild (patch-M was sweeping the shared
`var/model-visual-dbc/DBFilesClient/` dir wholesale; `docs/bugs-and-fixes.md`). `build_patch_m.py`
now has a `NOT_OURS` skip-set — extend it, don't remove it, if another script starts keeping its
working copy in that directory. Diagnostic when a client ignores a DBC row the plumbing says is
right: `for p in <patch-root>/Data/patch-*.mpq; do smpq -l $p | grep -i <table>.dbc; done`.

## Mined spell visuals and sounds (`patch_{mage,priest,druid}_vfx_models.py`)

These scripts sit outside `generate.py` and write rows straight into the working-copy DBCs in
`var/model-visual-dbc/DBFilesClient/`. `build_patch_m.py` then ships the rows. Each spell's DSL
source only points `SpellVisualID_1` at the minted `SpellVisual` row. The full mining procedure
and the custom ID ranges in use are in `docs/ascension-asset-mining.md` Part 3. Two traps:

- **A kit's `SoundID` must exist in our `SoundEntries.dbc`.** A sound ID copied from Ascension is
  silently ignored. Mint a row with `_sound_row()` (`patch_priest_vfx_models.py`) and put the
  `.wav` in `var/model-visual-dbc/SOUND/`.
- **A model needs all its textures.** Read the `.m2`'s texture table and ship every texture stock
  doesn't have, or the model renders as nothing.

After running one of these scripts, run `build_patch_m.py`. Also apply the `--sql-out` migration if
the script changed `SpellVisual`, which the server loads.

## Load-bearing gotcha: `EffectSpellClassMask{A,B,C}_{1,2,3}`

Every other per-effect `spell_dbc` column uses `_1/_2/_3` as the **effect index**
(`EffectBasePoints_2` = Effect_2's base points). This one is the exception: the **letter** is the
effect index (A=Effect_1, B=Effect_2, C=Effect_3) and the **number** is which of that effect's 3
`SpellFamilyFlags` dwords holds the bit. Writing `EffectSpellClassMaskA_2` when you mean "scope
Effect_2's modifier" silently scopes Effect_1 instead and leaves Effect_2's real classmask
all-zero — which the engine reads as "matches every spell in the family," not "matches nothing."

This shipped for real twice in the Frost Mage rework — first Permafrost and Chilled to the Bone,
then (same day, after only documenting the gotcha) Empowered Frostbolt again, on a different
`SpellModOp` — see `docs/dbc-build-pipeline.md`'s "Bug 3" for both. Docs alone didn't stop the
recurrence, so `generate.py` now runs `lib/lint.py`'s `check_classmask_scoping` automatically after
every spell build and prints a `WARNING:` line for any hand-authored row where a SpellMod effect
that needs a classmask ends up with an all-zero one. **Don't ignore that warning** — it means an
`EffectSpellClassMask*` override is almost certainly on the wrong letter. If you're adding or
auditing one yourself, double-check the letter/number against `lib/dbcfmt.py`'s comment on the
`SPELL` table before trusting it. The lint exempts an effect only when its aura, misc value and the
row's nine `EffectSpellClassMask*` values equal the stock client `Spell.dbc` row (real Blizzard bytes).
A "pulled from existing data" note proves nothing: Improved Blizzard and Arcane Flows kept it after
hand edits, which hid two wildcard SpellMods until 2026-10-06. When you edit a pulled row, replace
the note with what you changed. The lint only sees rows `generate.py` emits (new or edited), not
unchanged reference copies.
