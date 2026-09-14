# `source/classes/` — DSL spell/talent source (all 9 classes migrated AND split)

Each class lives here as a `<class>/` directory of several files (see "Two
layouts" below - a single `<class>.py` file is also still fully supported,
just not what any class currently uses) — either way it replaces that
class's old `source/spells/<class>.csv` + `source/spells/<class>_talents.csv`
+ `source/talents/<class>.yaml`, talents and abilities declared together in
real Python instead of CSV rows with embedded JSON blobs. See
`.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md` for the full
design and phased rollout, and `apps/dbc-tools/lib/dsl/registry.py`'s module
docstring for the exact API a class file uses.

**All 9 classes have migrated and all 10 (Mage included) are split**: each
is a `source/classes/<class>/` directory of `<class>_spells.py`/
`<class>_trigger_spells.py`/`<class>_talents.py` (Phase 4/5 migration, then a
later-session readability pass split every one of them). `source/spells/
<class>.csv`, `source/spells/<class>_talents.csv`, and `source/talents/` no
longer exist — `source/spells/` now holds only `generic.csv`/`npc.csv`
(non-class content, out of scope for this DSL). To convert a *new* class
file from scratch (e.g. after a `pull.py` run against a class not yet
touched by this migration) or to redo one: run `csv_to_dsl.py <class>` →
`backfill_constants.py <class>` → `verify_dsl_migration.py <class>`
(re-verify after each step), then delete the old CSV/YAML once
`verify_dsl_migration.py` reports `MATCH`; split it (see below) whenever
convenient afterward.

## Two layouts: one file, or a directory of a few

A class starts as a single `<class>.py` (what `csv_to_dsl.py` produces).
Once that file gets big enough to be annoying to navigate, split it:

```
python3 apps/dbc-tools/split_class_file.py <class>
```

This replaces `source/classes/<class>.py` with a `source/classes/<class>/`
directory of three files, partitioned automatically:

- `<class>_spells.py` — player-castable spells (real `cast_time_ms`/
  `cooldown_ms`, not marked passive — the same heuristic
  `granted_by_talent()` already uses, exposed as
  `lib.dsl.registry.looks_player_castable`).
- `<class>_trigger_spells.py` — everything else: proc/periodic-tick effects,
  `trigger_spell` targets, hidden talent-rank buffs — spells a player never
  casts directly.
- `<class>_talents.py` — talent tabs, talents (`granted_by_talent` bundles a
  rank's `SkillLineAbility` row too), and any standalone
  `skill_line_ability()` row.

This is purely organizational — which file a `spell()` call's source line
lives in has zero effect on what `generate.py` builds (the merged registry
doesn't care which file contributed an entry), so **always run
`verify_dsl_migration.py <class>` afterward anyway** to prove nothing got
dropped or duplicated, same as every other tool here. `lib/dsl/registry.py`'s
`load_class_package` loads the directory as one real Python package, so a
file can `from .other_file import some_var` to reference a spell/tab
declared in a sibling file — that's what makes `<class>_talents.py`'s
`ranks=[...]` (or a `trigger_spell=other.id` in `<class>_spells.py`
targeting something in `<class>_trigger_spells.py`) work regardless of which
file happens to be read first; there's no "must be declared earlier in this
file" rule across files the way there still is *within* one file.

Once a class is split, `backfill_spell_refs.py <class>` (see below) can turn
a plain-int `trigger_spell=<id>` into `trigger_spell=<var>.id` across files,
not just within one — a real example, Arcane Blast's `trigger_spell=36032`
→ `trigger_spell=arcane_blast_debuff.id` (a `mage_spells.py` spell
referencing one in `mage_trigger_spells.py`), only became fixable once the
split put the two ends of that reference in different files with a real
import connecting them; it couldn't be fixed while both lived in one
`mage.py` with the debuff declared *after* the spell that triggers it.
A single-file class stays fully supported — splitting is opportunistic, same
"whenever it's next worth doing" philosophy as the class migration itself,
not a requirement.

Quick shape, once a real one exists:

```python
from lib.dsl import Effect, EffectType, School
from lib.dsl.registry import spell, tab, granted_by_talent

# A talent tab needs `skill_line` set (see docs/skilllineability-handoff.md)
# only if a talent in it ever grants a brand-new, player-castable spell ID —
# see granted_by_talent below.
frost_tab = tab(id=60800, name="Frost", class_mask=128, skill_line=6)

frostbolt = spell(
    id=200001,
    name="Frostbolt",
    school=School.FROST,
    cast_time_ms=2000,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=17, points_per_level=7.5464)],
)

# Declares the Talent row AND (because player_castable=True) the matching
# SkillLineAbility row that keeps Frostbolt in the Frost Spellbook tab
# instead of "General" — see docs/bugs-and-fixes.md's SkillLineAbility entry
# for the bug this exists to make impossible. Leaving player_castable unset
# on a spell that has a real cast_time/cooldown and isn't passive is a hard
# build error, not a silent default — see granted_by_talent's docstring.
granted_by_talent(
    id=60000, tab=frost_tab, tier=0, column=0,
    ranks=[frostbolt], player_castable=True, skill_line_ability_ids=[30400],
)

# A trainer-taught (not talent-granted) spell instead uses trained_by() —
# validates trainer_id resolves to a real, spawned, correctly-flagged NPC
# *before* registering the trainer_spell row, raising DeadTrainerError
# otherwise. See docs/bugs-and-fixes.md's two TrainerId entries for the bug
# this exists to make impossible.
from lib.dsl.registry import trained_by

fireball = spell(id=200002, name="Fireball", school=School.FIRE, cast_time_ms=2500)
trained_by(fireball, trainer_id=212, req_level=20, money_cost=500)
```

A file whose name starts with `_` is skipped by the loader (reserved for a
future shared-helpers module, not a class file).
