---
name: talent-tooltip-audit
description: Audit one class/spec's talent tree — tooltip text against its design doc, duplicate talent icons within the spec, and the buffs talents apply. Use when the user asks to audit, check, or find bugs in a class/spec's talent tooltips, icons, or the buffs talents grant, or to verify talents match a design doc.
metadata:
  version: "1.2"
---

# Talent tooltip audit

Read-only audit of one talent tab (spec) against `apps/dbc-tools/source/` data: tooltip text vs.
its design doc, duplicate icons within the spec, and the buffs each talent applies. Reports
findings; does not edit files unless the user separately asks for the fixes to be applied (then
follow the pattern in "Applying fixes" below).

`args`: `<class> <spec/tab name> [design doc path]` — e.g. `mage arcane
docs/arcane-mage-rework-design.md`. If the design doc path is omitted, search `docs/*.md` for a
name containing both the class and the spec (e.g. `arcane-mage-rework-design.md`,
`frost-mage-redesign.md`); if more than one plausible match exists, ask.

## Step 1 — Resolve the spec's talent roster

Source of truth is `apps/dbc-tools/source/talents/<class>.yaml` plus `source/spells/*.csv`
(usually `<class>_talents.csv`, but a talent's rank spell can live in `generic.csv` or `<class>.csv`
too — see the class-rework skill's note on reference-only rows).

1. In the class's talent YAML, find the `tabs:` entry whose `name` matches the requested spec
   (case-insensitive) and note its `id` (the `tab_id` talents reference).
2. Collect every entry in `talents:` with that `tab_id`. For each, you have `tier`, `column`,
   `rank_spell_ids` (low rank to high, one spell id per rank), and `depends_on`.
3. For every id in every talent's `rank_spell_ids`, find its row across `source/spells/*.csv` (grep
   by id — don't assume the file). Pull `name`, `spell_icon_id`, and from `raw_overrides`:
   `Name_Lang_enUS`/`NameSubtext_Lang_enUS` (rank label), `Description_Lang_enUS`,
   `AuraDescription_Lang_enUS`.
4. Build one roster entry per talent: `(tier, column, name, [ (rank_n, spell_id, icon,
   description, aura_description) ... ])`. A talent missing a CSV row for one of its
   `rank_spell_ids` is itself a finding (dangling reference).

A small Python script reading the YAML + CSVs with `csv.DictReader`/`json.loads(raw_overrides)` is
the fastest way to build this roster — same approach used to diagnose the mage tooltip bugs this
skill was built from. Print the roster before moving on so mistakes are visible early.

## Step 2 — Buffs applied by talents

Talents often grant a *separate* hidden buff/debuff spell via `CastSpell`/`CastCustomSpell` in
`src/server/scripts/Spells/spell_<class>.cpp` rather than putting all their behavior on the
`rank_spell_ids` themselves — a stacking buff (Netherwind Presence), a capstone proc buff (Spell
Power), an absorb-proc damage buff (Arcane Shielding), a post-cast regen buff (Arcane Overload),
etc. These don't show up in Step 1's roster automatically and are easy to leave un-audited even
though they're exactly what the player sees on their buff bar — resolve them explicitly:

1. In `spell_<class>.cpp`'s anonymous `enum` near the top of the file, build a map from every
   `SPELL_<CLASS>_*` constant to its numeric id.
2. For each talent in the roster, find its script class(es). This codebase's convention is a
   `// <rank spell ids> - <Talent Name>` comment directly above each `class spell_<class>_*` (e.g.
   `// 44400/44402/44403 - Netherwind Presence`, `// -29441 - Magic Absorption`) — match by rank
   spell id, not by guessing the class name from the talent name alone.
3. Inside that class (and any shared helper in the same file that it calls into), collect every
   `CastSpell(...)`/`CastCustomSpell(...)` target that resolves to a `SPELL_<CLASS>_*` constant
   *other than* the talent's own `rank_spell_ids`. Each resolved id is a buff/debuff this talent
   applies. A talent can apply more than one (e.g. a hidden ICD marker plus a player-visible buff)
   — keep all of them, don't collapse to just one.
4. Look up each resolved id the same way as Step 1 (across `source/spells/*.csv`): name, icon,
   `Description_Lang_enUS`, `AuraDescription_Lang_enUS`, and duration. Attach it to its talent's
   roster entry, tagged with which rank(s) apply it if that varies (Netherwind Presence casts a
   different buff spell per rank of the talent, for instance).
5. Flag hidden/marker auras as such rather than presenting them as player-facing tooltips — signs
   of a marker: no `Description_Lang_enUS`/`AuraDescription_Lang_enUS` at all, or a name that's
   obviously internal (an "ICD" or "Capstone" suffix, zero duration on what should be a timed
   buff).

## Step 3 — Duplicate icon check

Icons are legitimately shared **across ranks of the same talent, and between a talent and its own
buffs** (Spell Power's proc buff reusing Spell Power's own icon is correct, not a bug — it's the
same ability reading as one visual identity). The bug is two *different* talents' icon sets
overlapping.

- Attribute every icon to its **owning talent**: a talent's own `spell_icon_id` plus every buff
  found for it in Step 2, all counted as that one talent's icon set (usually one icon value, but
  don't assume — a talent whose buff intentionally uses a different icon than the talent itself is
  fine too, that's still one owner).
- Any icon value (excluding 0/blank) that appears in **more than one distinct talent's** icon set
  is a finding: name both talents (and which spell — talent or specific buff — carries the icon on
  each side), and the shared icon id. Don't flag a talent sharing an icon with its own buff.
- Note but don't flag: an icon shared with something in a *different* spec/tab, or with the tab's
  own `spell_icon_id` — out of scope per spec.
- Cross-reference `apps/dbc-tools/var/spell_icon_names.csv` to report the icon's actual name
  (`Interface\Icons\...`) alongside the numeric id, so findings are actionable without a lookup
  round-trip.

## Step 4 — Tooltip vs. design doc

Design docs in this repo (see `docs/*rework*.md`, `docs/*redesign*.md`) are prose, not structured
data, and heading punctuation is sometimes markdown-escaped (`\)`/`\-`) — don't depend on an exact
heading regex. Match by **talent name** (exact text search across the doc) instead, then read the
surrounding paragraph(s) for that talent's intended base effect and, if present, a capstone/bonus
clause (commonly introduced as "Capstone Bonus:" in the doc prose). The shipped in-game convention
for a capstone clause is fixed — see Step 5 for the exact format — so a capstone that doesn't match
it is a bug, not a style choice.

Apply the same check to any buff found in Step 2 — a talent's design doc paragraph very often
already describes the buff's own effect inline (e.g. Arcane Overload's talent text is really
describing its buff spell's numbers), so treat the buff's `Description_Lang_enUS`/
`AuraDescription_Lang_enUS` as part of that talent's tooltip surface, not a separate thing to
independently source from the doc.

For each talent (and each buff it applies) found in both the roster and the doc, check:

- **Numbers per rank.** The doc usually gives a `low/mid/high` progression (e.g. "5/10/15%"); the
  CSV should have one distinct value per rank matching that progression (remember the storage
  convention: `base_points` is the displayed value minus 1). A tooltip using a `$sN`/`$s1` token
  is fine as long as effect N actually carries that value — cross-check the referenced effect
  index, not just that a token exists.
- **Capstone text.** If the design doc describes a capstone/bonus effect for the talent, every
  rank's `Description_Lang_enUS` must mention it — not just max rank. Missing entirely at max rank
  is the most common finding (this is exactly what this audit was built to catch — several mage
  capstones had the mechanic shipped in C++ but the tooltip text never added), but a capstone
  present only at max rank and absent from earlier ranks is *also* a finding — see Step 5 for the
  exact expected format and why earlier ranks need it too.
- **Stray/broken tokens.** Watch for tooltip tokens referencing a spell id that doesn't exist in
  this codebase (e.g. a leftover retail spell id from a data pull) — these render as literal
  unresolved text in-game. Grep the referenced id across `apps/dbc-tools/source/spells/*.csv`; if
  it's not there, the token is broken and should self-reference this spell's own effect (`$sN`)
  instead if that's what the doc describes.
- **Missing mechanic content** named in the doc but absent from the tooltip (e.g. a resource-gain
  clause, a proc condition) — flag even if you're not fixing the mechanic itself, since a
  tooltip claiming something untrue is as much a bug as one omitting something true.
- **Icon direction**, if the design doc or a project todo list names a specific icon for this
  talent or buff — cross-check against Step 3's icon pool instead of re-deriving it.

Optionally, for any tooltip claim that reads as a mechanic (a proc, a capstone trigger, a
resource-gain) rather than a plain stat mod, grep `src/server/scripts/Spells/spell_<class>.cpp`
for a script implementing it. A tooltip can be textually correct against the design doc while the
mechanic behind it was never wired (this has happened in this codebase — see
`docs/arcane-mage-rework-design.md`'s own "one real bug found via the boot log" note for the
pattern). Call this out as a separate, lower-confidence finding ("tooltip matches design, but no
implementation found for X") rather than silently assuming it's fine — this needs a human or a
deeper C++-side audit to confirm, so don't spend excessive effort chasing it if it's not quick to
verify.

## Step 5 — Capstone formatting audit

A capstone talent's bonus clause has a fixed, already-established format in this codebase (see
`Frostbite` at 11071/12496/12497 in `mage_talents.csv`, or `Improved Revenge`/`Focused Rage`/
`Incite`/`Shield Cover`/`Thunderstruck` in `warrior_talents.csv` for reference examples). Run this
check for **every** talent Step 4 identified as having a capstone/bonus clause, across **all** of
its ranks — a player reads a talent's tooltip long before they've put the final point in it, and
the capstone clause must already be visible (just visually disabled) at rank 1, not appear out of
nowhere at max rank:

1. **Present at every rank, not just max rank.** The exact same capstone sentence must appear in
   `Description_Lang_enUS` at every rank of the talent, including rank 1. A capstone that only
   shows up on the final-rank row is a finding, even if Step 4 already flagged that the doc's
   capstone text is otherwise correct there.
2. **Two line breaks before it, outside the color wrapper.** The capstone clause is separated from
   the talent's base-effect sentence(s) by exactly two newlines (`\n\n`) — a full blank line, not a
   single `\n` and not a plain space — and the newlines sit *before* the gray color escape (not
   inside it): `\n\n|cFF9D9D9D...`, never `|cFF9D9D9D\n\n...`. Check the raw JSON string, not a
   rendered view (a single `\n` reads the same as `\n\n` once whitespace is collapsed by eye, so
   diff the literal characters, and diff the literal ordering of `\n\n` vs. `|cFF9D9D9D` too).
3. **"Capstone Bonus: " label.** The clause itself must start with the literal text `Capstone
   Bonus: ` (capital C and B, colon-space) followed by the effect text — never a bare sentence with
   no label, and never a different label. On a gray non-final rank the label sits immediately after
   the color code with no space between them (`|cFF9D9D9DCapstone Bonus: ...`).
4. **Gray at every rank except the final one.** On every non-final rank, the capstone clause —
   from the two line breaks through the end of the string — is wrapped in the color escape
   `|cFF9D9D9D` ... `|r` (WoW's standard "unavailable" gray), e.g.:
   `"...breaks on damage. \n\n|cFF9D9D9DCapstone Bonus: Increases the damage...|r"`. On the
   **final** rank the same clause appears with **no** color wrapper at all — plain text, full
   color: `"...breaks on damage. \n\nCapstone Bonus: Increases the damage..."`. Flag either
   direction of mismatch: gray color codes left in on the max-rank row (capstone would render dim
   even once earned), or a non-final rank missing the gray wrapper (capstone would render as if
   already active before it is).
5. **`AuraDescription_Lang_enUS` stays clean.** The capstone clause belongs only in
   `Description_Lang_enUS` (the talent-tree tooltip). Don't expect it in
   `AuraDescription_Lang_enUS` (the buff-bar tooltip, when the talent itself grants a passive aura)
   — its absence there is correct, not a finding.

Report every rank of every capstone talent checked, pass or fail, in the format: talent name, rank,
spell id, and which of the five checks above failed (if any) with the exact string found vs.
expected.

## Step 6 — Report

Two parts. First the findings list, most-actionable first:

1. **Icon conflicts** — talent/buff A / talent/buff B / shared icon id (+ name).
2. **Missing/incorrect tooltip text** — talent or buff, rank(s), current text, what the design doc
   says, suggested corrected text.
3. **Broken tokens** — talent or buff, rank(s), the broken token, suggested replacement.
4. **Capstone formatting** — talent, rank(s), which Step 5 check failed, exact string found vs.
   expected.
5. **Unverified mechanic claims** — talent, the claim, and that it needs a code-side check.
6. **Doc/data talents that don't match up** — a talent in the roster with no matching section in
   the doc (may just mean the doc is out of date, not that the talent is wrong — say so), or a doc
   section naming a talent not found in this spec's roster (wrong tab/spec, or a stale doc name).

For each finding give exact spell id(s) so a fix (by hand or by re-invoking this session) doesn't
need a second investigation pass.

Second, **always** print a plain "Buffs applied by talents" listing — every buff/debuff resolved
in Step 2, one per line, regardless of whether Step 4 flagged an issue with it: talent name, buff
name + spell id, icon, `Description_Lang_enUS`, `AuraDescription_Lang_enUS`. A design doc's prose
is often terse or splits a buff's real behavior across the talent's paragraph and the doc's
"System Rulings"/"Open Items" sections, so automated pass/fail is less reliable here than for a
talent's own tooltip — surface the actual text unconditionally so the user can eyeball it
themselves rather than trusting the audit's verdict alone.

## Applying fixes

Only if asked. Follow the same pattern used to fix the mage tooltip bugs this skill generalizes
from: edit `raw_overrides` JSON fields in `source/spells/*.csv` directly (via a small Python
script using `csv`/`json`, never manual text surgery on the quoted CSV — see
`apps/dbc-tools/lib/dbcfmt.py`'s `EffectSpellClassMaskA/B/C` gotcha comment for why hand-edited
DBC-shaped fields are easy to get subtly wrong), verify every row still parses as valid JSON
afterward, and check `git diff --numstat` only touched the intended rows. This is a data-only
change — it does **not** take effect in-game until `apps/dbc-tools/generate.py` is run and the
result deployed (client patch + DB import/restart). Per `AGENTS.md`, don't build or restart the
server unless explicitly asked; say so explicitly when done rather than assuming the fix is live.
