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
