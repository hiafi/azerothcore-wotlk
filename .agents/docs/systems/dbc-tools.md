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

## Watch out: one client DBC, one patch archive

Four scripts each own a patch letter: `generate.py` → `patch-Z.mpq` (Spell/Talent/Item/…),
`build_patch_m.py` → `patch-M.mpq` (SpellVisual*/CreatureDisplayInfo/CreatureModelData/
GameObjectDisplayInfo + `SPELLS/` models), `build_patch_i.py` → `patch-I.mpq` (`SpellIcon.dbc` +
`Interface/Icons/*.blp`), `patch_gt_tables.py` → `patch-Y.mpq` (GT tables). The client loads
lettered patches alphabetically and the **highest letter wins per file**, so a DBC packed into two
archives is silently served from whichever has the later letter — usually a stale copy. That's
exactly what blanked every custom `SpellIcon` row minted after patch-M's last rebuild (patch-M was
sweeping the shared `var/model-visual-dbc/DBFilesClient/` dir wholesale; `docs/bugs-and-fixes.md`).
`build_patch_m.py` now has a `NOT_OURS` skip-set — extend it, don't remove it, if another script
starts keeping its working copy in that directory. Diagnostic when a client ignores a DBC row the
plumbing says is right: `for p in <patch-root>/Data/patch-*.mpq; do smpq -l $p | grep -i
<table>.dbc; done`.

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
`SPELL` table before trusting it. Untouched "pulled from existing data" rows are exempt from both
the manual check and the lint — those bytes are copied verbatim from the real client DBC, not
hand-typed, so they're correct regardless of what a human's own comment on the row claims.
