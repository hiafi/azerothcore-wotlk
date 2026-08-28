# dbc-tools (`apps/dbc-tools/`)

Generates `spell_dbc`/`Talent.dbc`/etc. content from `apps/dbc-tools/source/{spells,talents}/*`
via `apps/dbc-tools/generate.py`, producing a pending SQL migration plus a client patch MPQ. Full
design and workflow: `apps/dbc-tools/README.md`. Bugs found and fixed via live-client/live-engine
verification are logged in `docs/dbc-build-pipeline.md` — read that log before assuming a
surprising-looking column or value is intentional.

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
