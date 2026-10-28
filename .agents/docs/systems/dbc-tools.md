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

## Trainer pricing

A trainer spell's price is a function of its learn level (`ReqLevel`) alone. `source/trainer_pricing.py`
holds three things and `lib/trainer_pricing.py` applies them on every `generate.py` run:

- **`PRICE_CURVE`**: `(ReqLevel, copper)` anchors (10c at levels 1-3, 20c at 4, 1s at 10, 12s at 25,
  60s at 40, 2g 20s at 60, 14g 40s at 80). Between anchors the price is interpolated linearly in
  integer math and rounded half up to 1c below 100c, 10c up to 9999c, and 1s from 1g. Outside the
  anchors it is clamped (below level 1 is 10c, above 80 is the last anchor). The curve is validated on
  load: levels strictly increasing, prices non-decreasing, > 0 and on their own rounding step (a multiple of
  10 from 100c, of 100 from 10000c), else `PricingPolicyError`.
- **`PRICED_TRAINER_IDS`**: an explicit allow-list (13 Death Knight, 18-30 mage portals, 200-217 class
  trainers). A stock trainer that later gets an NPC wired to it is *not* repriced silently. A listed
  trainer with no live spawned NPC (`TrainerIndex.trainer_problems()`) gets a `WARNING` and is skipped.
- **`PRICE_OVERRIDES`**: `{SpellId: copper}`, a fixed price on every priced trainer that beats the curve.
  Empty.

**Rows in scope** are the true live `trainer_spell` rows of the priced trainers (a replay over every
file, generated ones included) plus `trained_by()` declarations. A declaration supplies every column
except `MoneyCost`: **`money_cost` is ignored on a listed and live trainer** (it is still honoured on a trainer
outside the allow-list, and on a listed one with no live NPC, which is skipped with a WARNING). Keys retired by `untrain()` are excluded. Only rows that differ from live are
emitted, so a rerun emits no `trainer_spell` rows. Nothing is read from the old price, so nothing can
compound; retune by editing the curve and regenerating.

**The replay must be faithful**, because its output drives writes. `sql_dump.apply_composite_key_statements`
applies `(TrainerId, SpellId) IN (...)`, single-column `=`/`IN`, AND-ed point, `BETWEEN` and OR-of-AND
DELETEs and UPDATEs (`parse_where_predicate`), honours every UPDATE condition (key or not), evaluates
`SET col = col | n` style expressions, and for `trainer_spell` fills omitted INSERT columns with 0 at INSERT
time. A statement it cannot apply prints `WARNING: trainer_state.py: <file>: cannot replay ...`, including
`TRUNCATE`, `INSERT IGNORE`, `UPDATE ... AS alias` and an unquoted table name (the statement scanner
cannot see those, so a separate scan reports them). Treat any such WARNING as a bug in the replay or the
SQL: the pass may re-insert a row that SQL removed. Not detected: a statement that merely mentions the
table inside a larger construct (a subquery, `INSERT ... SELECT`).

The same replay serves `creature_template`/`creature_template_model` (`lib/spell_tables.py`), where the
widened WHERE/expression support corrects stock values to live; those callers do not warn.

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

## Dungeon finder exclusions: `lfg_exclude()`

`lfg_exclude(map_id, name)` (`source/world/lfg.py`; usage in `apps/dbc-tools/README.md`) declares a
`disables` row of sourceType 8, a `SPELL_TABLES` entry keyed on `(sourceType, entry)`. Things that are
not obvious:

- **`flags` must be 1.** `LFGMgr::IsDungeonDisabled` calls `DisableMgr::IsDisabledFor(DISABLE_TYPE_LFG_MAP,
  map, nullptr)`: no unit and flags 0, so the difficulty checked is always normal and a row without
  `DUNGEON_STATUSFLAG_NORMAL` never matches. The same call means heroic cannot be excluded separately.
- **No collision with mod-progression.** Its phase SQL owns `disables` sourceTypes 1-5, 9 and 10 (maps
  are sourceType 2, which closes the instance itself), and the base dump has no sourceType 8 rows.
- **The prune circuit breaker is off for this table** (`TableSpec.prune_when_empty`): an empty
  `lfg.py` is a normal state, and with the breaker on, removing the last exclusion would never DELETE it.
- **`lint.check_lfg_exclusions` reads stock `LFGDungeons.dbc`** (`dbcfmt.LFGDUNGEONS`, read-only, not in
  `ALL_TABLES`). It errors on a map without a TypeID 1/2/5 entry, which includes continent maps (random
  entries have MapID 0), and DisableMgr rejects a continent map with flags anyway. With the file missing
  it errors only when something is declared.

## Superseded ranks: generated `SkillLineAbility` and `CreatureSpellData` overrides

Pets learn from `SkillLineAbility`, not trainers: `SpellMgr::LoadPetLevelupSpellMap` takes every row on a
creature family's skill lines with `AcquireMethod` 2 (`SKILL_LINE_ABILITY_LEARNED_ON_SKILL_LEARN`; 1 is
`..._ON_SKILL_VALUE`). The single-rank conversion removed the chains from `spell_ranks`, so a pet learned
every superseded rank as its own spell (an Imp with Firebolt 3110 and 7799..47964). `generate.py` now
overrides each stock row whose `Spell` is a superseded rank (a base `spell_ranks` chain member other
than the DSL spell tagged "single-rank bootstrap") and whose `AcquireMethod` is 2: the stock row with
`AcquireMethod` 0 (`lib/superseded_ranks.py`). A declared `skill_line_ability` with the same ID wins and
prints a `WARNING`. When added (2026-10-11) the rule covered 553 rows, all on pet-family skill lines
(warlock demons and hunter pets).

That alone is not enough, because pets have a second source: **default spells**. `LoadPetDefaultSpells`
reads the `CreatureSpellData` record named by `creature_template.PetSpellDataId` (a tamed beast keeps
the wild beast's entry), and `LoadPetDefaultSpells_helper` drops only the spells in the family's level-up
set. Stock records name ranked family spells (Ghost Saber: Claw 16829), so once the overrides above
removed those ranks from the level-up set they came back as defaults. The boot log showed it as
`Loaded Addition Spells For 803 Pet Spell Data Entries` (112 in stock). So the same rule also writes
`creaturespelldata_dbc`: each stock record that names a superseded rank, with that `Spells_N` replaced
by the survivor (`Availability_N` stays stock). The survivor is in the level-up set, so the helper drops
it again and the default lists are exactly stock's. That covers 714 of 802 records and 42 ranks. Things
that are not obvious:

- **Server-only.** The rows never go into patch-Z. The server never sends `PetSpellDataId` to the client,
  and it alone sends a pet's spells (`Player::PetSpellInitialize`).
- **The stock file is `var/extractors/dbc/CreatureSpellData.dbc`.** Only `patch-enUS.MPQ` carries it. If
  it is missing, the run prints a `WARNING` and emits nothing for the table.
- **The block is a delta.** Only records that `state.load_existing_rows` (stock plus promoted `db_world/`)
  doesn't already hold are emitted, through `render_generic_table_block`. The `SkillLineAbility` rows
  still go through resolve, because the client patch needs them.
- **Before promotion:** every run lists the 553 IDs in its "editing N existing ... skill line
  abilitie(s)" line and re-emits both blocks. That is expected; strip them if an earlier pending file
  already carries them byte-identically.
- **After promotion:** a run is silent. The overrides read back as live, `generate.py` counts them in a
  separate `note: superseded ranks: N SkillLineAbility override(s) already live` line (not as "unchanged
  copies"), and the `creaturespelldata_dbc` block is empty.
- **When a WARNING appears.** It appears only if a promoted migration left an overridden row as neither
  stock nor the override. Read it; the override is built from stock and replaces that change.

Existing pets keep whatever they already learned, so a rank-chain collapse also needs a characters-DB
cleanup. For this one, that is `pending_db_characters/rev_1791713091186211987.sql`. See
`docs/bugs-and-fixes.md` ("Pets learn every superseded rank..."). Plan:
`.agents/plans/pet-stale-ranks/pet-stale-ranks.PLAN.md`.

## Hunter T1: editing stock talents, pet spells and items

Added for the hunter rework (`.agents/plans/hunter-rework/`, SHARED Part C7). The README's "Editing stock
talents, pet spells and items" section has the call syntax; this is what to know when something misbehaves.

- **`acquire_method` / `superseded_by` on `skill_line_ability()`.** Typed, emitted only when not `None`, so a
  row without them is built byte-for-byte as before. `raw_overrides` is applied last and still wins.
  `lib.dsl.AcquireMethod` is the enum.
- **`retire_talent(id)`** appends a talent entry on holding tab **60800** (`RETIRED_TAB_ID`) and a
  `retired_talents` bookkeeping row (so retiring twice is a `DuplicateIdError`). It needs the live Talent rows,
  which `generate.py` passes to every `load_classes_dir` call as `live_data` (`spell_tables.dsl_live_data`). The
  tool scripts that load `source/classes/` themselves (`pull_dsl.py`, `potency_report.py`, `pull_talents.py
  --dsl`) pass `spell_tables.load_dsl_live_data()`; a new one has to as well, or a class file calling
  `retire_talent()`/`item_template()` raises `RuntimeError`. The holding tab is checked after all sources merge
  (`check_retired_talent_tab`), because a call cannot see a sibling file's `tab()` at import time.
- **Talent.dbc order.** `order_talent_rows` keys each row on its *final* TabID now. A moved or retired row leaves
  its stock block (which stays where it was) and joins the new one; a tab absent from the stock file gets a block
  after every stock block. Rows the stock file had keep their stock relative order inside a block, then new
  rows in the order given. `lib/test_client_dbc_roundtrip.py` still proves an untouched stock file repacks
  byte-identically.
- **`check_talent_tab_refs`** is an ERROR (the run stops before anything is written) on both populations: the
  server's live-plus-built rows and the client's stock-plus-built rows.
- **`retire_pet_spell`** is resolved in `lib/superseded_ranks.py` (`retired_skilllineability_overrides`,
  `spell_data_strips`, and the `strips=` argument of `creaturespelldata_overrides`) and wired in `generate.py`
  next to the superseded-rank pass, whose rows it shares (`rank_override_ids`). The `CreatureSpellData` strip
  zeroes the slot and its `Availability_N`; a record some other family's creature also names is left alone and
  reported, since a record cannot be split. Needs `var/extractors/dbc/CreatureFamily.dbc` (not in any client
  MPQ - the server's DBC dir has it, like `CreatureSpellData.dbc` above; `dbcfmt.CREATUREFAMILY` reads it,
  byte-identical round trip): a declared retirement without it is an ERROR, the family lint's rule (d) a WARNING.
  A superseded rank counts as the spell for the strip (a record naming only Bite rank 4 is stripped when the
  survivor is retired). `shared_lines=True` retires a shared-line (270) row for every family while the strip
  stays scoped to `families`; a retirement that matches nothing is a WARNING.
- **`item_template()`** uses `spell_tables.ITEM_TABLES` (a sibling of `CREATURE_TABLES`): upsert only, never
  pruned (`render_item_retirement_report` lists a dropped declaration), unchanged rows emit nothing. Two
  differences from `creature_template`: the live rows come from `apps/item-tools`' overlay (it recurses into
  `itemization_templates_v2/`; `trainer_state` does not), and the statement is a column-limited
  `UPDATE ... SET <declared columns> WHERE entry IN (...)` (`sql_out.render_update_block` reads each row's
  `_update_columns`; rows with the same assignments share one statement). Reason: mod-progression and other
  runtime SQL rewrite price and level columns of these same rows, and a full-row update from a replayed copy
  would revert them. An UPDATE, not a multi-row `INSERT ... ON DUPLICATE KEY UPDATE`, because the overlay
  reads only the first tuple of an INSERT (T-FIX T1-1). A rerun after the migration applied emits nothing
  (`test_item_template.RoundTripTest`).
- **Item lints.** `check_item_dbc_consistency` (WARNING) and `check_ranged_ammo_type` (WARNING) run in the full
  run, not under `--check`. The 33 quiver `items.csv` rows are stock-id edits: they appear in the "editing N
  existing ... item(s)" line, in an `item_dbc` `DELETE ... WHERE ID IN (...)` plus INSERT, and in patch-Z's
  `Item.dbc`. The ranged-weapon edit has no DBC half: `AmmoType` lives only in `item_template`, the client reads
  it from the item query, so the client's `Cache` folder must be wiped once after rollout.
- **Family-bit lint** (`check_hunter_family_rules`) takes the built custom spell rows, the declared `spell_proc`
  rows, the SkillLineAbility rows (stock plus built) and the pet skill lines (270 plus `CreatureFamily.dbc`'s).
  Rule (c) inspects every effect mask whatever its aura (an effect mask only exists to be read), which is
  broader than the SpellMod-only scoping lint, and every declared `spell_proc` row whatever its spell id
  (SpellFamilyName 9 or 0; 0 matches any family). Rule (a) exempts an "Aspect of ..." name only for a spell
  with a SkillLineAbility row, so a same-named triggered aura still warns; the rule set's `exempt_ids` is the
  explicit escape hatch. Since shaman T1 the function is `check_family_bit_rules` (the old name is an alias) and
  runs under `--check` too, on the declared population; the full run still judges only the new or edited spells.
  Without `CreatureFamily.dbc` the full run prints a WARNING when custom class-set-9 spells exist.
- **TalentTab.dbc in patch-Z.** The retired tab 60800 (`order_index` 3, ClassMask 0, PetTalentMask 0) makes
  `TalentTab.dbc` ship for the first time. The first full run prints two WARNINGs (`TalentTab.dbc ships in the
  client patch ...  60800 (new)` and `TalentTab.dbc is new in the client patch ...`): accept them once and check
  every class's talent frame and the three pet tabs in game. Later runs, once the previous build already carried
  the file, print a `note:` instead when the only TalentTab rows are new inert ones (`lint.check_client_patch`'s
  `notes`); any edited stock row or a tab with a class or pet mask still warns. `CharacterDatabaseCleaner` keeps
  `character_talent` rows on a valid tab, so the characters SQL that retires a talent deletes them itself.
- **Cost.** Loading the item overlay and the Talent rows adds about 30 s to `generate.py` and to `--check`.

## Shaman T1: creature spell slots, spell lints and id blocks

Added for the shaman rework (`.agents/plans/shaman-rework/`, T1). The README's "Shaman T1" section has the syntax and
the lint table; this is what to know when something misbehaves.

- **`creature_spell()` / `remove_creature_spell()`** are `SPELL_TABLES` / `REMOVAL_TABLES` entries for
  `creature_template_spell` (key `(CreatureID, Index)`), so the whole prune / removal / provenance machinery applies
  unchanged. A totem's guardian summon must be on Index 0 (`Totem::GetSpell()` reads `m_spells[0]` when the totem is
  removed). The `TableSpec` defaults (`Index` 0, `Spell` and `VerifiedBuild` NULL) matter only for a hand-written
  INSERT that omitted a column; such a row reads back with NULL and re-emits once. `lib/test_creature_spell.py`
  renders, reads the output back through the readers the diff uses (`sql_dump.read_table_rows`,
  `load_generated_table_rows`, `load_removed_keys`) and checks that the rerun is empty (hunter T1-1).
- **Lint wiring.** `generate._t1_content_warnings` is the one function both the `--check` block and the full run
  call, so a `--check` session sees what the full run prints (hunter T1-10). It takes the built rows of every declared
  entry (`--check` builds them already for the family-zero lint) and a base spell dict: stock rows under `--check`,
  the promoted-aware live rows in the full run. `--check` only knows the declared SkillLineAbility rows. A new lint
  goes into that function and into `test_shaman_t1_lints.RealPopulationTest`, which fails when a lint fires on the
  declared population and no allow set covers it.
- **Allow sets** (`HIDDEN_LEARNED_ALLOW`, `GROUND_HASTE_ALLOW`, `SPELL_PROC_ALLOW`, `SHADOWED_PROC_ALLOW`,
  `TRAINER_SPELL_LEVEL_ALLOW`) hold the existing hits with a reason each; a new hit is fixed in the source, not added.
  `SHADOWED_PROC_ALLOW` is the priest rework's known live bug (12 per-rank rows dropped as `duplicate entry` by stock
  chain rows); its input is the *replayed* `spell_proc` table (`_proc_shadow_inputs`), because the union reader would
  keep a chain row a later migration deleted (-47580) and report false shadows.
- **`check_totem_tools` widening** also walks the base Spell rows (stock under `--check`, live in the full run), so the
  opt-in covers the 117 stock family-11 tool spells, not only the 42 the source declares.
- **LEARN carriers.** `check_hidden_learned_spells` follows LEARN_SPELL (effect 36) targets of learned spells and
  treats a spell whose every effect is effect 36 as a deliberate hidden carrier, so the warlock 59672-pattern talent
  ranks need no allow entry.
- **`lint.TOOL_FREE_CLASS_SETS`** is the SH0 hook for `check_totem_tools`. The 42 stock family-11 spells with a
  non-zero tool column all carry only `RequiredTotemCategoryID_1` (TotemCategory 2 Earth, 3 Air, 4 Fire, 5 Water).
- **Family-bit rules** are data (`FamilyBitRules`); a zero mask turns its rule into a no-op, and the message wording
  (`protected_label`, `reader_label`, ...) comes from the rule row.
- **`ids.yaml` reservations.** The `reservations:` key is a mapping of owner -> table -> `{start, end}` (an owner is a
  class, or a non-class project such as `healsim`; see "Death Knight T1"). Every reader
  of `ids.yaml` indexes it by table name and none iterates it, so it is invisible to them; do not add a reader that
  iterates the file's top level without skipping `reservations`.
- **`--check` count line.** `note: ... (DSL) contributed ...` leaves out tables with nothing declared, so adding a
  table to `SPELL_TABLES` does not change the line until something declares into it.

## Death Knight T1: rune costs, creation data, the class row and `--check` additions

Added for the Death Knight rework (`.agents/plans/death-knight-rework/`, T1). The README's "Death Knight T1" section
has the syntax; this is what to know when something misbehaves.

- **`DBCStructure.h:1843` is wrong.** The comment `0=blood, 1=frost, 2=unholy` on `SpellRuneCostEntry::RuneCost[3]`
  describes the wrong order: the array is indexed by `RuneType` (`RUNE_BLOOD` 0, `RUNE_UNHOLY` 1, `RUNE_FROST` 2,
  Player.h), so the DBC columns are `ID, Blood, Unholy, Frost, RunicPower`. Core files stay stock (merge-guard), so
  the trap is documented in `lib/dbcfmt.py`'s `SPELLRUNECOST` comment and in `spell_rune_cost()`'s docstring, not
  fixed. `RunicPower` is stored x10, and rune cost and RP gain only apply to a `PowerType` 5 spell.
- **`SpellRuneCost.dbc` is a client table too.** `SPELLRUNECOST` is deliberately not in `ALL_TABLES` /
  `SECONDARY_TABLES` (the SQL would go out twice, as for `SPELLCATEGORY`): the server half is the
  `spellrunecost_dbc` entry of `SPELL_TABLES`, the client half is `generate._spell_rune_cost_rows`, merged over
  `var/extractors/dbc/SpellRuneCost.dbc` into patch-Z. Both stock files (`SpellRuneCost.dbc`, `ChrClasses.dbc`) are
  copied from the worldserver's DBC directory (read-only `docker cp`); `var/` is gitignored.
- **The creation tables use the union reader.** `playercreateinfo_action` / `_cast_spell` / `_skills` are ordinary
  `SPELL_TABLES` entries read with `trainer_state.load_table_rows` (union of INSERTs). The three cases that looked
  like traps converge with it, so no `load_replayed_table_rows` switch was needed: a DK override of a stock key
  (later file wins in `SpellTableIndex`), a removal of a row a hand file already deleted (`load_removed_keys` only
  counts generated files, so the extra DELETE is emitted once and then recorded), and an undeclared key a hand
  `UPDATE` changed (never in `rows_to_emit` or the prune orphans). **Gotcha:** the reader does not replay a
  hand-written DELETE or UPDATE, so a declaration equal to a hand-deleted row's original INSERT reads as unchanged
  and is not re-emitted (`creation_cast(48266, 32, ...)`, `spell_threat(8056, ...)` render nothing while the DB has
  no row); change a value or re-add it by hand (`ReaderTrapTest.test_iv`). Not fixed: switching these tables to
  `load_replayed_table_rows` would also have to change `render_removal_blocks`' live keys, or removing a
  hand-deleted row (DK0a's 48266) prints a spurious "doesn't exist anywhere" WARNING.
  `playercreateinfo_cast_spell` has no primary key,
  so its key-exact DELETE removes every duplicate of (raceMask, classMask, spell). All three load once at boot and
  only affect new characters. `creation_skill` rejects `rank >= 16` (`MAX_SKILL_STEP`, the loader skips those rows).
- **`chrclasses_dbc` and `spellrunecost_dbc` have `prune_when_empty=True`**, like `disables`: with the breaker on,
  retiring the last `chr_class()` / `spell_rune_cost()` would leave the overlay row for good.
- **`override_skill_line_ability()` edits the stock row** (`dsl_live_data(skilllineability_stock_rows=...)`), so a
  dropped keyword restores the stock value; a row only a migration added falls back to the live row.
- **`chr_class()` replaces the whole row.** `chrclasses_dbc` has `ChrClassesEntryfmt` read for only four columns, but
  the overlay row carries all 60; the female / male / neutral names and `Filename` are `x` in the fmt yet are string
  offsets in the file, so they are in `read_as_string` (the `SPELLSHAPESHIFTFORM` lesson). The stock file's repacked
  string table is 10 bytes shorter than the original (shared strings): the server never reads this file back, and
  `lib/test_chr_class.py` checks the row-level round trip instead of the bytes.
- **`dsl_live_data` keywords.** `skilllineability_rows` and `chrclasses_rows` are keyword arguments defaulting to
  `None`, and either may be a zero-argument callable that `registry._require_live` calls on first use and caches in
  the bundle. Every older caller (`pull_dsl.py`, `potency_report.py`, `pull_talents.py --dsl`, the tests) is
  untouched; do not turn them into eager loads, the SkillLineAbility replay is about 13 s.
- **`--check` has an ERROR path for rune costs and a dry run for GCD haste.** `generate._rune_cost_errors` feeds
  both the full run's error list and `--check`'s `check_errors` (so it exits 1 for them).
  `_gcd_haste_check_warnings` runs the full run's computation over stock Spell / Talent / TalentTab /
  SkillLineAbility rows with the declared rows laid over them and prints WARNINGs only (promoted migrations are not
  replayed, so it cannot flip the exit code). It must pass the superseded-rank map the full run computes: with
  `superseded={}` the stock rows still list the collapsed ranks as learnable and the tree printed six Paladin /
  Hunter lines (a promoted-aware variant printed the same six). If it ever prints a line on the committed tree, fix
  the data or the policy; do not add an allow list.
- **`reservations:` holds non-class owners.** `healsim` reserves 202900-202909 so the overlap test catches a class
  slice that swallows the healing sim's spells (the T0 collision: DK's first block was 202900-203599). Reserve a new
  project's ids under its own name the same way.
- **`override_skill_line_ability()`** appends the entry `skill_line_ability()` would build (typed columns plus
  `raw_overrides` for the rest). `lib/superseded_ranks.py` treats it as a declared row (a "declared row wins"
  collision), and `resolve.resolve_rows` classifies it like any row outside the reserved block: edited when it
  differs from the live row, unchanged copy when it does not.

## Rogue T1: a SpellDuration with a minimum and a maximum, the rogue id slices and family-bit rules

Added for the Rogue rework (`.agents/plans/rogue-rework/`, T1; tooling only, no rogue content). The README's "Rogue T1"
section has the syntax.

- **`spell(duration_ms=4000, max_duration_ms=24000)`** mints or reuses a `SpellDuration` row whose `Duration` and
  `MaxDuration` differ (`ReuseContext.duration_index(duration_ms, max_duration_ms=None)`; the one-argument call is
  unchanged and still only finds `Duration == MaxDuration` rows). The core scales the aura between the two by the
  caster's combo points (`WorldObject::CalcSpellDuration`, Object.cpp:3377-3394: `min + (max - min) * cp / 5`, only
  for a caster with combo points, `min != -1` and `min != max`). The model raises for a max with no positive
  `duration_ms`, a max equal to (a no-op) or below the minimum, and a negative max. A stock row with the pair is
  reused (185 is 6000/21000), never duplicated.
- **Who reads `duration_ms` as the minimum.** The client's `$d` tooltip token shows `Duration` only, and the periodic
  tick count behind a potency `.total` tooltip (`lib/dsl/model.py`, `round(duration_ms / amplitude)`) uses it too. A
  spell with a range therefore shows its minimum-duration total; the stage that declares one (Rupture) owns the
  per-tick number and the tooltip wording. `lint.check_raw_override_typed_mismatch` compares `duration_ms` with the raw
  row's `Duration` column, which is the minimum, so it stays consistent. A declared max together with a raw
  `DurationIndex` override raises (the raw index is applied last and would win).
- **Combo points at aura creation.** `CalcSpellDuration` scales by whatever combo points the caster holds when the
  aura is created, finisher or not (it never checks `NeedsComboPoints`), and the finisher's points are only cleared
  in the finish phase (`Spell.cpp:4414`). A non-finisher with a ranged row scales by the points it finds and spends
  none; a helper triggered after the finisher consumed its points (an `AfterHit` script cast, a stored-bleed tick
  spell) sees 0 points and always gets the minimum. Put the range on the aura the finisher's own cast creates.
- **Pull stays lossless.** `reverse.py` diffs the rebuilt row against the real one and keeps any difference (a ranged
  `DurationIndex`) in `raw_overrides`.
- **`ROGUE_FAMILY_RULES`** (`SpellClassSet` 8) is in `FAMILY_BIT_RULES`, so both `--check` and the full run judge it:
  no custom (>= 200000) rogue-family spell may carry d0 b11 (Stealth's removal strips every family-8 aura on it), d0 b22
  (the Stealth hardcode drives the Master of Subtlety / Overkill tails) or d0 b25 (Hemorrhage's combo point and dagger
  bonus). The bits that depend on a spell's role are not expressible in the table; RG0 and the spec stages pin them with
  targeted tests: d0 b16 only on Deadly Poison, d0 b20 only on Rupture, d0 b17 only on a spell that should take the
  Eviscerate AP term, d0 b26 / d1 b18 on a new weapon strike, d1 b1 / b2 / b3, the DR bits d0 b3 / b10 / b24, the
  Preparation lists, d0 b0 while Throw shares it, and d1 b19 as the poison group.
- **Ids.** `reservations: rogue` has the PLAN s4 slices (spell 203700-204399 and so on; the P0 spike's 204370-204399,
  1295, 30838-30839 and 300368-300369 are never reused). `spellicon` is widened to 90499 and `spell_group` to 1399.
  `gameobjectdisplayinfo`, `summonproperties` and `spellcategory` are not reserved (not needed); the first stage that
  needs one adds its slice. `lib/test_id_blocks.py::scanned_used_ids` skips the `*_STOCK` constants in
  `patch_rogue_vfx_models.py` (they are stock ids below 90000) and a test pins every other rogue VFX constant to the
  rogue slices (spellvisual 90250-90299, soundentries 90121-90140). The spellvisual block is full after the rogue:
  the next class widens it.

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

## GCD-haste auras (melee-haste-gcd T1)

`source/gcd_haste.py` (policy) + `lib/gcd_haste.py` (applied on every `generate.py` run, call site next to the
superseded-ranks pass) emit one hidden passive per class family, `Haste: Global Cooldown`, whose FLAT
`SPELLMOD_GLOBAL_COOLDOWN` (aura 107, ms; the server ignores pct GCD mods) classmasks cover the 1.5s GCD spells the core's haste branch skips (DmgClass
MELEE/RANGED, `USES_RANGED_SLOT`, `IS_ABILITY`). Plan: `.agents/plans/melee-haste-gcd/`.

- Masks are computed from the merged spell data, never typed. Effect 0 = melee-haste mask (`EffectSpellClassMaskA_n`),
  effect 1 = ranged-haste mask (`..B_n`), effect 2 = PERIODIC_DUMMY. An empty mask is left as *no effect*: an
  all-zero classmask matches every spell in the family.
- A bit shared with a spell the core already hastes stops the run (`ERROR: gcd haste: ...`). Resolve it in
  `source/gcd_haste.py` with a reason: `EXCLUDE` (leave a live ability unhasted) or `NOT_CASTABLE` (a retired
  spell the data still lists as learnable; dropped from both sides).
- "Learnable" = SkillLineAbility row off the pet skill lines, rank of a non-pet-tab talent, or a DSL spell that
  `looks_player_castable` accepts *and* is not a pet spell; minus superseded ranks. The DSL carries stock pet
  spells as reference copies, so the heuristic alone would pull Hunter pet abilities in.
- The server rewrites some `SpellFamilyFlags` at load (`SpellInfoCorrections.cpp`); `SERVER_FLAG_FIXES`/
  `SERVER_FLAG_RULES` mirror them by hand and the check runs under both views. Re-check when that file changes.
  Only flag rewrites are mirrored: other corrections were checked and do not change candidacy (e.g. Shattering
  Throw 64382 loses `IS_ABILITY` at load but stays a candidate, its DmgClass being MELEE).
- `NOT_CASTABLE` ids are left out of the check on the premise that no player can learn them. `generate.py`
  enforces it: a live `trainer_spell` row of a reachable trainer, or a `trained_by()` declaration, stops the run
  (`ERROR: gcd haste: ...`). A superseded rank that a reachable trainer still teaches (Swift Flight Form 40120)
  stays learnable, so it is covered like any other candidate. A stale `EXCLUDE` id prints a
  `WARNING: gcd haste: ...`.
- A new family aura ID comes from `FAMILY_AURA_IDS` (201560-201566 in use); a family with bits and no ID errors.
- A new aura is a *new* spell in the reserved block, so it does not appear in the "editing N existing spell(s)" line.
