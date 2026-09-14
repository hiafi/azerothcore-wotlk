# `source/classes/` — DSL spell/talent source (Phase 1 infra, no classes migrated yet)

One `<class>.py` file per class will land here, replacing that class's
`source/spells/<class>.csv` + `source/spells/<class>_talents.csv` +
`source/talents/<class>.yaml` — talents and abilities declared together, in
real Python instead of CSV rows with embedded JSON blobs. See
`.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md` for the full design
and phased rollout, and `apps/dbc-tools/lib/dsl/registry.py`'s module
docstring for the exact API a class file uses.

**Nothing has migrated yet.** `generate.py` already reads this directory
(empty directory or no files here at all → contributes nothing, no error —
see `lib/dsl/registry.py`'s `load_classes_dir`), so a class can be migrated
here one at a time, whenever it's next touched for a rework (the plan's
Phase 4/5), without a flag-day rewrite of every class at once. Until a class
migrates, its `source/spells/<class>*.csv` / `source/talents/<class>.yaml`
stay authoritative — don't hand-add a `.py` file here speculatively.

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
