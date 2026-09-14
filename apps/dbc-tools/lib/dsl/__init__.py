"""
Python DSL for hand-authored spell/talent source — Phase 0 of
`.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md`.

Replaces `source/spells/<class>*.csv` + `source/talents/<class>.yaml`'s raw
CSV rows / JSON-blob columns with real Python: named constants instead of
magic DBC integers, and dataclasses instead of hand-typed JSON. Talents and
abilities live together in one `source/classes/<class>.py` file per class
once migrated (see the plan's "Source layout").

Phase 0 scope only: `constants.py` (named enums for values already in use)
and `model.py` (`Spell`/`Effect`/`Talent`/`TalentTab`/`SkillLineAbility`
dataclasses, each with a `to_entry()` that produces the exact same dict
shape `lib/source.py`'s CSV/YAML loaders already produce) — verified in
`lib/test_dsl.py` to build byte-identical `spell_dbc` rows to today's
CSV-driven pipeline for real, already-shipped spells (Frostbolt, Polymorph,
Blizzard). `lib/build.py`/`lib/resolve.py`/`lib/dbcfmt.py`/`lib/lint.py`/
`lib/sql_out.py`/`lib/patch_out.py` are unchanged and untouched by this
package on purpose — see the plan's "Key architectural fact" for why that's
possible at all (the pipeline already works on plain `dict` rows
internally; only the source-loading layer is new).

`registry.py` (module-import collection, so a `source/classes/<class>.py`
file can just call `spell(...)`/`talent(...)` and have it register itself
with no separate list to remember to append to — the exact bug shape this
whole effort exists to prevent, see the plan's "Problem this solves") and
wiring into `generate.py` are Phase 1, not yet done.
"""

from __future__ import annotations

from .constants import AuraType, DispelType, EffectType, Mechanic, PowerType, School
from .model import ApplyAura, Damage, Effect, SkillLineAbility, Spell, Talent, TalentTab
from .registry import (
    DeadTrainerError,
    DuplicateIdError,
    MissingSkillLineAbilityError,
    Registry,
    load_class_file,
    load_classes_dir,
)

__all__ = [
    "School",
    "PowerType",
    "DispelType",
    "Mechanic",
    "EffectType",
    "AuraType",
    "Effect",
    "ApplyAura",
    "Damage",
    "Spell",
    "Talent",
    "TalentTab",
    "SkillLineAbility",
    "Registry",
    "DuplicateIdError",
    "MissingSkillLineAbilityError",
    "DeadTrainerError",
    "load_class_file",
    "load_classes_dir",
]
