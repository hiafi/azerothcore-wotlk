---
name: classmask-scope-audit
description: Audit hand-authored spell/talent data for classmask-scoping bugs on SpellMod-type effects (SPELLMOD_DURATION, SPELLMOD_EFFECT1/2/3, SPELLMOD_COST, etc.) — a modifier with no real spell identifier that leaks into unrelated spells, a modifier that silently matches nothing because its classmask is on the wrong dword, or two individually-correct modifiers that collide on a shared bit. Use when the user asks to audit classmask scoping, find "spell identifier" bugs, check whether a talent's modifier is leaking into unrelated spells, or references the Frost Mage Chill / Devastate:Puncture / Arcane Shielding precedents.
metadata:
  version: "1.0"
---

# Classmask scope audit

Read-only audit of `apps/dbc-tools/source/spells/*.csv` (plus the live `spell_dbc` table when a
dev DB is available) for `EffectSpellClassMask{A,B,C}_{1,2,3}` scoping bugs on hand-authored
`SPELLMOD`-type effects. This bug class has shipped **at least six times** across this fork's
reworks (Permafrost, Chilled to the Bone, Empowered Frostbolt, Puncture/Devastate, and — the
incident this skill was built from — Missile Barrage/Arcane Shielding, where an agent auditing for
*exactly this bug class* misdiagnosed it and "fixed" an already-correct row). It keeps recurring
because the field-naming convention is genuinely counter-intuitive and each incident has been a
*different* failure mode under the same surface symptom ("a percent/flat modifier is affecting the
wrong spell(s)"). Read this whole skill, especially Step 0, before touching any
`EffectSpellClassMask*` field — do not rely on memory of the convention, even if you've audited
this before.

`args`: `<class> [talent/spec name]` — e.g. `mage arcane`. If a spec name is given, scope Step 1's
CSV sweep to that spec's talents (same resolution as `talent-tooltip-audit`'s Step 1) but **always**
run Step 3's collision search against the *whole* family (every CSV pulled for that class, not just
the spec) — a modifier can collide with a pulled-data spell far outside the tree being audited,
which is exactly what happened with Missile Barrage.

## Step 0 — Load the ground truth before doing anything else

**The convention:** in `spell_dbc`'s `EffectSpellClassMask{A,B,C}_{1,2,3}` columns, unlike every
other per-effect column in the schema, **the letter is the effect index** (A = Effect_1, B =
Effect_2, C = Effect_3, i.e. `Effects[0..2]` in the engine) **and the number is which of that
effect's 3 `SpellFamilyFlags` dwords holds the bit**. `EffectSpellClassMaskA_2` scopes *Effect_1*'s
*second* dword — it has nothing to do with Effect_2, despite what `_2` would suggest by analogy
with `EffectBasePoints_2` etc.

Do not take this paragraph's word for it — cross-check it live against the source of truth before
relying on it in this session, every time:

1. `apps/dbc-tools/lib/dbcfmt.py`, the comment directly above `("EffectSpellClassMaskA", 3),
   ("EffectSpellClassMaskB", 3), ("EffectSpellClassMaskC", 3)` in the `spell_dbc` column list — the
   single most authoritative source, since it's the code that actually emits these columns.
2. `apps/dbc-tools/README.md`'s "Gotcha: `EffectSpellClassMaskA/B/C_1/2/3` in `raw_overrides`"
   section.
3. `.agents/docs/systems/dbc-tools.md`'s "Load-bearing gotcha" section.
4. `docs/dbc-build-pipeline.md`'s "Bug 3" writeup — the original incident and its exact symptom
   (Permafrost's slow leaking onto every mage spell's first effect).

All four say the same thing. If any local note, CSV comment, or your own prior turn in this
conversation says something different ("the letter is the dword," "just move the value to match
the effect's own suffix number") — that source is wrong, not the convention above; this exact
wrong belief is what caused the Missile Barrage/Arcane Shielding incident this skill exists to
prevent. When in doubt, write a two-line throwaway Python check against a **known-good, real
"pulled from existing data" row** (e.g. Summon Water Elemental 31687, or Devastate 20243/Heroic
Strike whatever's on hand in the class you're auditing) and confirm your read of the convention
reproduces that row's known-correct classmask/target-match before trusting any conclusion you're
about to write down.

## Step 1 — Automated sweep (catches empty/wildcard classmasks)

`apps/dbc-tools/lib/lint.py`'s `check_classmask_scoping` already runs this check automatically on
every `generate.py` build and is the fastest, most reliable first pass:

```
cd apps/dbc-tools && .venv/bin/python3 generate.py 2>&1 | grep WARNING
```

This flags any hand-authored row (skips rows marked `"pulled from existing data"` — those are
verbatim real client bytes, correct by construction) where a `SPELLMOD`-requiring effect
(`EffectAura` 107/108, `EffectMiscValue` in `lint.py`'s `_SCOPE_REQUIRED_OPS`) has an **all-zero**
classmask on *its own* effect index while some *other* effect on the same row has a nonzero one —
the exact "wrote it under the wrong letter" shape (Permafrost, Chilled to the Bone, Empowered
Frostbolt, and the *first*, wrong "fix" attempted on Arcane Shielding all had this shape — though
Arcane Shielding itself turned out not to actually have this bug; see Step 3).

**Before trusting this check's output, read `check_classmask_scoping`'s current implementation and
verify `masks[i]` (or whatever it's now called) is built as "effect `i`'s 3 dwords," i.e. keyed by
`_LETTERS[i]` with the 3 numbers varying — NOT the transpose (keyed by number with the 3 letters
varying).** The transposed version compiles fine, produces plausible-looking warnings, and is
*wrong* — it checks "does any effect on this row have a nonzero value under dword N" instead of
"is this specific effect scoped at all," which both hides real bugs (a wrong-letter value on
another effect can make it look like this effect is scoped when it isn't) and — as happened in this
skill's own origin incident — invents false positives on rows that are already correct (it flagged
six unrelated, correct rows: Magic Attunement, Firestarter, Burning Determination, Devastate: Extra
Target, Shield Cover, Thunderstruck). If you need to touch `lint.py` at all, write both a
known-broken input (an empty-on-its-own-effect row) and a known-correct input as inline test cases
and confirm the fixed function gives the right answer on *both* before moving on — see
`docs/bugs-and-fixes.md`'s writeup of this exact near-miss for the two test cases already worked
out.

## Step 2 — Manual sweep for "right effect, wrong dword" (matches nothing, not too much)

The Step 1 check only catches an *all-zero* classmask. A classmask that's nonzero but on the wrong
**number** (dword) within the correct **letter** (effect) passes it silently — the modifier just
quietly does nothing, no wildcard, no warning, no error (this is the Puncture/Devastate incident:
`docs/bugs-and-fixes.md`, "A hand-authored `EffectSpellClassMask*` SpellMod silently matches
nothing when the target spell's own flag lives in a different dword"). This failure mode reads as
"the talent's tooltip says X but nothing happens" rather than "the talent affects too much" — worth
checking both directions, not just the leaking-into-everything one.

For every hand-authored `SPELLMOD`-type effect (same filter as Step 1, but this time **including**
rows Step 1 didn't flag, since a nonzero-but-wrong value produces no warning):

1. Identify the spell(s) the modifier is *supposed* to affect, from its own `Description_Lang_enUS`
   / the design doc's prose for that talent.
2. Look up each named target spell's own real `SpellClassMask_1/2/3` (its family-flag identity) —
   `grep` the CSVs for `"SpellClassMask_1"`/`"_2"`/`"_3"` on that spell's row, or query the live
   `spell_dbc` table (`SELECT SpellClassMask_1, SpellClassMask_2, SpellClassMask_3 FROM spell_dbc
   WHERE ID = ...`) if a dev DB is up — the DB is authoritative for spells whose classmask comes
   from stock/pulled data with no `raw_overrides` entry to grep.
3. Confirm the modifier's own classmask (correctly read per Step 0: letter = this effect's index,
   fixed; check all 3 numbers) shares a nonzero bit with the target's classmask **in the same dword
   position** for at least one named target. If it doesn't — nonzero value present, but on a dword
   where every intended target's own flag is zero — that's this failure mode. Note which dword the
   target's *real* bit is actually in (cross-reference a second, independently-verified spell that
   shares the same real family behavior, the way `docs/bugs-and-fixes.md`'s Puncture writeup used
   "Devastate: Extra Target" as a known-good reference) before proposing the fix.

## Step 3 — Collision search (correctly-scoped modifiers that still overlap something unintended)

The failure mode this skill was ultimately built from: a modifier can be **correctly scoped** to
its intended target(s) by every check above, and still unintentionally affect an unrelated spell
because that spell's own real family flags happen to reuse the same bit in the same dword. This is
not a data-entry mistake on either side, and **cannot be fixed by moving a classmask field** — see
`docs/bugs-and-fixes.md`'s "Missile Barrage's -50% still computed to -65%..." entry for the full
worked example (Arcane Shielding's Ward-absorb bonus needs the one dword all three Wards share;
Missile Barrage's own proc buff, real Blizzard data, happens to carry that exact bit for unrelated
reasons).

For every modifier confirmed correctly-scoped in Step 2 (or found in Step 1's clean pass):

1. Take the modifier's real, correctly-attributed classmask — one nonzero dword (or more) at a
   specific letter+number.
2. Search **the entire family** (every `SpellClassSet`-matching row across all CSVs pulled for this
   class — not just the spec/tree being audited) for any *other* spell whose own real
   `SpellClassMask_{1,2,3}` has a nonzero value in that **same dword position**, sharing at least
   one bit. Prefer a live DB query if available — one pass over `spell_dbc` filtered by
   `SpellClassSet` covers everything, including rows with no CSV `raw_overrides` at all:
   ```sql
   SELECT ID, Name_Lang_enUS, SpellClassMask_1, SpellClassMask_2, SpellClassMask_3
   FROM spell_dbc WHERE SpellClassSet = <family>;
   ```
   then compute the bitwise overlap in Python/shell rather than eyeballing — values are often large
   and share bits non-obviously (`8` and `8388612` both have bit 3 set, for instance).
3. Every spell found this way is the modifier's real blast radius — list all of them, not just the
   ones that look suspicious. Then flag, as a likely-unintended collision, any hit that isn't named
   in the talent's own tooltip/design-doc prose as an intended target. A hit that *also* affects the
   modifier's own effect index specifically (not just "this spell exists in the family") is the
   dangerous case — e.g. a `SPELLMOD_DURATION` colliding with another spell's own duration effect,
   the way Arcane Shielding's `SPELLMOD_EFFECT1` collided with Missile Barrage's.
4. Do not propose "move the classmask" as the fix for a genuine collision — there may be no bit
   assignment that both covers every intended target and avoids every real spell in the family.
   Name it as a design problem needing a different mechanism (a C++ `EffectCalcAmount`/`CheckProc`
   hook reading the specific target spell IDs directly, sidestepping classmask matching entirely —
   see `spell_mage_fire_frost_ward`'s existing `EffectCalcAmount` hook in `spell_mage.cpp` for the
   established pattern) rather than a one-line data fix.

## Step 4 — Report

One entry per hand-authored `SPELLMOD`-type effect audited, most-actionable first:

1. **Empty/wildcard classmask** (Step 1) — spell id/name, effect index, op, and (if the row has a
   value on a different letter that's plausibly the misplaced one) the specific one-line fix.
2. **Wrong dword, matches nothing** (Step 2) — spell id/name, effect index, op, current classmask,
   the target's real classmask, and the specific corrected value/slot.
3. **Genuine collision** (Step 3) — spell id/name, effect index, op, the colliding spell(s) found,
   and an explicit note that this needs a design decision, not a data edit — link
   `docs/bugs-and-fixes.md`'s Arcane Shielding entry as the template for how to write this finding
   up.
4. **Clean** — modifiers checked and confirmed correctly scoped with no collisions found. Report
   these too, briefly, so a re-audit later knows what's already been cleared.

For every finding, give the exact spell id(s), the exact `EffectSpellClassMask<letter>_<number>`
field(s) involved, and the exact classmask values (not just "it's wrong") — this audit exists
because eyeballing plausible-looking values is exactly how the bug keeps recurring, so leave
nothing for the next pass to re-derive.

## Applying fixes

Only if asked, and only for Step 1/Step 2 findings (a genuine Step 3 collision needs a design
decision from the user first, not a fix applied on this audit's own initiative). Follow
`talent-tooltip-audit`'s "Applying fixes" pattern: edit `raw_overrides` via a small Python script
using `csv`/`json` — **never** a blind text `str.replace()` across the file, even scoped by spell
id string prefix; a substring match on a numeric value (e.g. searching for `"...": 8` to fix one
row) can silently hit unrelated rows whose value merely *starts with* the same digits (`8192`,
`8388612`) — this is exactly how the Missile Barrage incident's revert briefly corrupted six other
rows before being caught. Match on the full row (`line.startswith(f"{spell_id},")`) or parse with
`csv.DictReader`/`json.loads` and rewrite the specific key, never a raw substring across the whole
file. Verify every row still parses as valid JSON and the file still round-trips through
`csv.reader` with the original column count afterward, then run `generate.py` again and confirm the
warning (if any) clears with no new one appearing elsewhere. This is a data-only change — it does
not take effect in-game until `generate.py` is run and the result deployed (client patch + DB
import/restart); per `AGENTS.md`, don't build or restart the server unless explicitly asked.
