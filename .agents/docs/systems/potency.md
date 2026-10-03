# Potency system (`apps/dbc-tools`'s `sp_potency=`/`ap_potency=`)

How a damage, heal or absorb effect's numbers should be authored from the Warlock pilot (P4,
2026-10-01) onward: as a **potency** value the generator turns into `EffectBasePoints`/
`EffectRealPointsPerLevel`/`EffectDieSides`/`EffectBonusMultiplier_N`, not as hand-typed
`base_points=`/`points_per_level=`. One number (plus a handful of others) stands in for the whole
level curve, the spell-power/attack-power coefficient, and the ±10% damage roll, derived from the
same formula every other potency spell uses — so two abilities with the same potency actually hit
the same, instead of accumulating hand-tuning drift the way `base_points=`/`points_per_level=`
pairs always eventually do (see `docs/bugs-and-fixes.md`'s `spell_bonus_data` staleness entry,
found exactly this way).

The full design rationale — why potency is `F × C(L)`, the measured `R` constant, the healing/DoT/
hybrid/weapon formulas, every reference table — lives in `docs/potency-system.md`. That file is
gitignored (`docs/*`), so it may not exist on a fresh checkout; this doc is the one thing guaranteed
to be there. If `docs/potency-system.md` is present, read it before retuning any constant in
`apps/dbc-tools/lib/potency.py` — this doc is the practitioner's quick reference, not the spec.

## When to use it

Any `Effect` whose type deals damage, heals, or absorbs (`SCHOOL_DAMAGE`, a `PERIODIC_DAMAGE`/
`PERIODIC_HEAL` aura, `HEAL`, an absorb aura) gets a potency value instead of hand-set
`base_points`/`points_per_level`/`die_sides`. Everything else (buffs, procs, stat mods, thresholds,
flat percentages) keeps using `base_points=` as before — potency only replaces the "this effect's
damage/healing number scales with level and gear" case. A few categories deliberately stay off
potency entirely (see "What doesn't get a potency value" below).

## The DSL fields (`lib/dsl/model.py`'s `Effect`)

```python
Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=140.0, potency_kind='direct', implicit_target_a=6)
```

- **`sp_potency`** / **`ap_potency`** (float, default 0) — the potency value(s). A pure spell-power
  effect sets only `sp_potency`; a pure attack-power effect only `ap_potency`; a hybrid (rare — see
  "Hybrid spells" in the design doc) sets both, and the base damage line is driven by their *sum*.
- **`potency_kind`** (str) — one of `'direct'`, `'periodic'`, `'heal'`, `'heal_periodic'`,
  `'absorb'`. Defaults to `'direct'` if omitted. `'direct'` is the only kind that gets the ±10%
  variance roll (`DIRECT_VARIANCE_PCT` in `lib/potency.py`) — periodic/heal/absorb effects roll
  once and every subsequent tick/instance repeats that value, same as stock DieSides-1 auras.
- **`weapon_potency`** (float, mutually exclusive with `sp_potency`/`ap_potency`) — a weapon-percent
  effect's own, simpler path: no level scaling, no correction row, the value is the percent itself
  (must be a whole number). Can't currently be combined with a flat SP/AP bonus riding the same
  effect (raises) — that's P6/P7 scope, not wired up yet.
- **`time_basis_ms`** (int, optional) — overrides what the generator uses as "T" in the formula.
  Defaults to the effect's own `amplitude` for periodic-like kinds, or the spell's `cast_time_ms`
  (or 1500 if that's 0) for direct/heal/absorb. Set this explicitly when the natural default is
  wrong — e.g. an off-GCD proc payout, or (Rain of Fire's real precedent) an effect that carries the
  potency but has no `amplitude` of its own because a *different* effect on the same spell drives
  the actual tick cadence.
- **`base_potency`** (float, optional) — overrides what drives the **base damage line** (`F` in the
  formula) without changing the SP/AP coefficients, which still come from `sp_potency`/`ap_potency`
  directly. Rare: only needed when a spell's base damage shouldn't equal what its coefficients alone
  imply. Not used by any warlock effect as of P4 — a generalization for later classes.
- **`potency_excluded`** (str, mutually exclusive with everything above) — marks an effect that
  looks like a damage/heal/absorb effect but will never get a potency value, with the string
  explaining why. Required reading for `potency_report.py` (below) so it stops flagging the same
  effect every run. Always required for the categories in the next section.

**Required alongside potency on the spell itself:** `raw_overrides={'SpellLevel': <n>, ...}`. The
generator derives `BaseLevel = SpellLevel` and forces `MaxLevel = 0` from it — these are not
optional, and a potency effect without `SpellLevel` set raises immediately. Don't set `BaseLevel`/
`MaxLevel` by hand on a potency spell; the generator owns them.

**Don't hand-set `base_points`/`points_per_level`/`die_sides`** on a potency effect — the generator
raises a hard `ValueError` if any of the three is already nonzero/non-default, since mixing a hand
value with a generated one is unambiguous misuse, not a style choice.

## What doesn't get a potency value

Four categories, found and categorized during the Warlock pilot — mark every one with
`potency_excluded=` explaining which:

1. **Script-driven effects whose base points a `CastCustomSpell`/`SetSpellValue` call computes at
   runtime** (D2: a script-supplied base point always wins over whatever `CalcValue`/the potency
   correction hook would compute, so giving the DBC row a potency value would be dead data the hook
   never reaches). Audit every `CastCustomSpell`/`SetSpellValue`/`SPELLVALUE_BASE_POINTn` call site
   in the class's own scripts before converting a class (the Warlock pilot called this the "F8
   audit") — a spell can *look* like a static damage effect in the DBC while its real value is
   entirely script-driven.
2. **Percent-of-other-damage or percent-of-max-health effects** (e.g. Conflagrate, Rain of Fire's
   old `0.1716`-coefficient placeholder effect, Phantom Singularity's heal) — these don't have an
   independent level/gear curve of their own at all; potency has nothing to represent.
3. **Legacy rank-capped spells kept only because an `item_template` row casts that exact spell id**
   (a superseded rank with its own historical `MaxLevel`). Potency forces `MaxLevel=0` spell-wide,
   which would silently uncap one of these and buff whatever rare item casts it — exclude and leave
   exactly as-is unless the user explicitly says to convert and accept the uncap.
4. **Pet/guardian/demon-cast effects** — left on the old hand-tuned path until their own stage (P8
   for Warlock); not something to convert opportunistically mid-pass on another class.

## Finding what a class's existing effects should be converted to

`apps/dbc-tools/potency_report.py <class>` (or no argument for all ten) compares every damage/heal/
absorb effect's *current* base value against what its *current* spell-power coefficient implies,
flags a >10% disagreement (this is almost always real tuning drift from reworks done before
potency existed, not a report bug), and writes
`.agents/plans/potency-system/<class>-potency-report.md` plus a
`<class>-potency-proposals.txt` the user can fill in with approved values (never overwritten once
hand-edited — see `write_proposal_file()`). Read a flagged row as "these two numbers imply two
different potencies — pick one," not as an automatic answer; which one is right needs a judgment
call the report can't make (usually: did this spell's cast time change in a rework after its
coefficient was last tuned?).

## Tooltips: `{pot1}`/`{pot2}`/`{pot1.total}` placeholders

A potency effect's `Description_Lang_enUS`/`AuraDescription_Lang_enUS` should use `{potN}` (1-based,
matching `Effect_1`/`Effect_2`/`Effect_3`) instead of the native `$s1`/`$o1`/`$m1`-style tokens:

- `{potN}` → a single `${...}` value for most kinds, or `${X} to ${1.1*X}` for a `'direct'` effect
  (the ±10% range) — matching whichever `$sN`/range the native text showed.
- `{potN.total}` → the periodic sum over the effect's own tick count, matching a native `$oN`.
- `{potN.avg}` → the average as one `${...}` value (rarely needed).

**This is not optional cosmetic polish — skipping it produces a materially wrong tooltip.** The
generated `${...}` expression is the *only* way a potency spell's tooltip shows the caster's live
spell power/attack power at all (found during the Warlock pilot's own tooltip migration,
2026-10-01): the plain `$s1`/`$m1` tokens this replaces do **not** auto-include a live stat bonus on
this fork's client — confirmed empirically (a scratch spell's bare `$s1` showed exactly
`EffectBasePoints+1`, zero stat contribution) — so a spell left on `$s1` after conversion will show
a tooltip number far below real combat damage, not just a "slightly simplified" one.

**Cross-spell references stay as native tokens.** `{potN}` only resolves within the spell being
declared — it can't reach another spell's effect. Where native text references another spell by id
(`$42223s1`, two spells sharing one description like Seed of Corruption's DoT/detonation pair),
leave that token as-is; it keeps working once *that* spell's own DBC data is correct, and each
side's own self-reference is what gets the `{potN}` treatment.

**`$SP`/`$AP` are real, confirmed-live tokens** for "caster's current effective spell power/attack
power," usable inside a raw `${...}` math expression — this is what `{potN}`'s generated formula
uses internally (`lib/potency.py`'s `tooltip_expression()`/`_stat_bonus_term()`); you shouldn't need
to hand-write one, but if some future case needs a custom `${...}` expression, these are confirmed
to work (unlike `$SPH`/`$FAP`, which are not real tokens — `$SPH` wasn't conclusively tested, `$FAP`
printed a literal `$`). **Never use `|` in a description string you're live-testing** — WoW's
tooltip engine treats it as a color/texture escape character and silently corrupts the display; this
cost a wasted round-trip finding it out.

**A top-level `+` inside one `${...}` block is silently dropped** on this fork's client (everything
after the first `+` vanishes) — P0's original finding, confirmed again when adding the SP/AP bonus
term. `$max()`/`$min()` nest fine and their *arguments* can freely use `+`/`-`/`*`; the fix for
needing to add a constant to an already-`$max()`-wrapped expression is the identity
`max(a, b) + c == max(a + c, b + c)` — distribute the addition into every branch of the outer
`$max()` rather than appending it after the call closes. If you ever hand-write a `${...}`
expression for a potency effect, keep the entire thing inside one top-level `$max()`/`$min()` call.

## Showing a talent's bonus on a tooltip: `tooltip_vars` (P9)

SpellMods and `MOD_DAMAGE_PERCENT_DONE` auras never move a tooltip. Combat damage includes them, the
preview doesn't. The only way to show a "+X% damage" talent on the spells it affects is a
`SpellDescriptionVariables.dbc` entry, the stock mechanism behind Frostbolt's Piercing Ice chain
(entry 167). Declare one with `tooltip_vars()` and multiply the potency placeholder by it:

```python
frost_talent_tooltip = tooltip_vars(
    1000, "Frost-tree talent multiplier for Frost spell tooltips",
    piercing=talent_mult([11151, 12952, 12953]),               # +2/4/6% Frost, effect 1
    arctic_all=talent_mult([31674, 31675, 31676], effect=1),   # +1/2/3% all damage
    arctic_frost=talent_mult([31674, 31675, 31676], effect=2),  # +1/2/3% Frost
    mult=product("piercing", "arctic_all", "arctic_frost"),
)
frostbolt_116 = spell(..., tooltip_vars=frost_talent_tooltip,
                      raw_overrides={..., 'Description_Lang_enUS': '... causing {pot2*mult} Frost damage ...'})
```

The live precedent is `mage_trigger_spells.py`; the API is in `apps/dbc-tools/README.md`'s
"Declaring tooltip variables (P9)" section.

- **One entry per spell, shared freely.** A spell has one `SpellDescriptionVariableID`, so every
  variable it uses lives in that one entry. Declare it once per group of spells that share the
  same talents (all Frost spells, say) and pass the handle to each one.
- **`talent_mult` reads the talent's own value** (`$<rank>m<effect>`), so retuning a talent rank
  updates every tooltip that shows it. Count every effect of a talent that applies: Arctic Winds
  needs both its all-damage and its Frost effect. Which talents count is a design call. The Frost
  pilot took Frost-tree talents only, and left out cross-tree ones (Playing with Fire, Arcane
  Empowerment) by the user's choice; ask, don't assume.
- **`{potN*var}`** (also `.avg` / `.total`) multiplies the whole potency range by `$<var>`.
- **Ids** come from `ids.yaml`'s `spelldescriptionvariables` block (1000–1999), never a stock id:
  stock entries are shared by dozens of stock spells. When a reworked spell still carries a stock
  id (`SpellDescriptionVariableID: 167` in `raw_overrides`), its chain probably checks talent
  ranks or values the rework changed. Move the spell to its own entry.

Client rules (P9.0 spike, `docs/potency-system.md`'s "Tooltip" section). Builders and
`tooltip_vars()` enforce the first two:

- Inside an entry, read another spell as `$<id>m<n>`. **`$<id>s<n>` stops the variable resolving**:
  it shows as a literal `$<name>`, or as 0 inside math.
- Variables may only reference variables defined earlier in the entry.
- A bare `$<var>` in tooltip text displays as a whole number (1.06 shows "1"). Use it inside math.
- `$<var>` in AuraDescription (buff text) is untested, and no stock spell does it. The pilot kept
  Frostfire Bolt's buff text unmultiplied.

`generate.py` errors before writing any SQL when a tooltip uses a `$<var>` its entry doesn't
define (stock entries included), and when an entry names a spell that doesn't exist.

## Deploying a change

Pure data (no C++): `generate.py` → `docker compose up ac-db-import` → restart `ac-worldserver`
(no image rebuild) → see `docs/bugs-and-fixes.md`'s `manifest_gen.py` entry and the `dbc-deploy`
skill's Step 5 before trying to force an immediate client-patch refresh by hand — the obvious
`python3 apps/patch-service/manifest_gen.py` invocation silently operates on the wrong directory and
writes nothing useful; it has to run inside the `patch-manifest-gen` container.

A tooltip-only change (description text, `tooltip_vars`, `{potN}` placeholders) is client-only:
the server never reads tooltip text or `SpellDescriptionVariableID`, so the regenerated
`patch-Z.mpq` alone takes effect, with no DB import or restart. Testers have to re-run
`patch-client.bat` **after** `manifest.txt` has picked up the new hash. A client patched before
that still runs the previous build, and the P9.4 check first read "the talents do nothing" this
way. Read `generate.py`'s `WARNING: patch:` lines before deploying, too: they flag a
`TalentTab.dbc` or another table that unexpectedly entered or left the patch.

## Generated header (`WarlockData.h`-style, PLAN P2b)

Once a class has `CLASSES_WITH_GENERATED_HEADERS` entry in `generate.py`, every `spell()`/
`creature_template()` call **assigned to a module-level variable** gets a `constexpr` in
`src/server/game/Entities/Unit/Generated/<Class>Data.h` (`shadow_bolt_686` → `SPELL_SHADOW_BOLT`,
collision-fallback keeps the full `_<id>` suffix for a second same-named rank). A
`creature_template()`/`spell()` call that isn't assigned to a variable is invisible to this — the
Warlock pilot's own 6 missing `NPC_*` constants (Wild Imp, Dreadstalker, etc.) were real
`creature_template()` calls that simply had no `name = creature_template(...)` binding for the
header generator's identity-based lookup to find a name from. A hand-maintained `<Class>Mechanics.h`
should alias its ids to this generated header (`constexpr uint32 SPELL_X = ClassData::SPELL_X;`)
rather than hand-typing the same literal twice — see `WarlockMechanics.h`'s own top-of-file comment
for the categories that genuinely can't be generated (`TALENT_*` real `Talent.dbc` row ids;
external/stock spell ids the class's own DSL source never declares) and stay hand literals forever,
not leftover work. `generate.py --check` fails fast (skips the ~130s full pipeline) if the committed
header is stale — run it as a gate alongside pytest once a class has adopted this.
