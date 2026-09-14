"""
Module-import collection for `source/classes/*.py` DSL files - Phase 1 of
`.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md`.

A class file just calls `spell(...)`/`talent(...)`/`tab(...)`/
`skill_line_ability(...)` at module scope - each one both builds the
dataclass (`model.py`) *and* registers its `to_entry()` dict into whichever
`Registry` is currently being loaded, so there's no separate `SPELLS = [...]`
list a file has to remember to append to. That's deliberate: "declared a
spell but forgot to also add it to a second, separate list" is the exact
bug shape this whole effort exists to prevent (see the plan's "Problem this
solves" - the SkillLineAbility bugs are that shape one table over).

Example `source/classes/mage.py` (once one exists - none do yet, this is
infrastructure only) - see `source/classes/README.md` for a fuller one that
also shows `granted_by_talent()`, Phase 2's bundling helper:

    from lib.dsl import School, Effect, EffectType
    from lib.dsl.registry import spell

    frostbolt = spell(
        id=116, name="Frostbolt", school=School.FROST, cast_time_ms=2000,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=17)],
    )
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field
from pathlib import Path

from . import model


class DuplicateIdError(ValueError):
    """Same shape/name as `lib.source.DuplicateIdError` - kept as a
    separate class (not imported from there) so this package has no
    dependency on `lib.source`; `generate.py` catches both alike."""


class MissingSkillLineAbilityError(ValueError):
    """Raised by `granted_by_talent()` when a talent grants a brand-new
    custom spell ID that looks player-castable (see `_looks_player_castable`)
    but the declaration never said whether it needs a `SkillLineAbility`
    row. This is Phase 2's actual point - see
    `docs/bugs-and-fixes.md`'s "New custom spell IDs granted by a talent
    show up in the Spellbook's General tab instead of the class's own tab"
    entry, which is exactly the live bug an unnoticed gap here caused,
    twice, before this check existed. Fix by passing `player_castable=True`
    (needs the row - also pass a matching `skill_line_ability_ids` entry) or
    `player_castable=False` (this rank is only ever granted as a hidden
    triggered effect, e.g. Icicles) explicitly - see `granted_by_talent`'s
    docstring."""


class DeadTrainerError(ValueError):
    """Raised by `trained_by()` when the `TrainerId` it's given doesn't
    resolve to a real, placed, correctly-flagged NPC - see
    `lib.trainer_state.TrainerIndex.trainer_problems`. This is Phase 3's
    actual point - see `docs/bugs-and-fixes.md`'s "The Death Knight class
    trainer (TrainerId 13) never taught anything, anywhere" and "Trainer
    content fixes landing on the wrong TrainerId" entries, both this exact
    failure mode: a `trainer_spell` row authored against a `TrainerId`
    nothing in the world actually serves."""


@dataclass
class Registry:
    """Everything one `source/classes/*.py` file declared, already in the
    dict shape `lib/source.py`'s CSV/YAML loaders produce - see
    `model.py`'s `to_entry()` docstrings for why that's exactly enough for
    `lib/build.py` to need no changes. `trainer_spells` is the one exception
    - `trainer_spell` has no DBC/CSV/YAML counterpart at all (see
    `trained_by`'s docstring), so its entries are shaped to match that
    table's own columns directly, with a synthetic string `id`
    (`"<TrainerId>:<SpellId>"`) added purely so the generic duplicate-ID
    merge logic below (which is keyed on `entry["id"]`) works for it exactly
    the same way as everything else, with no special-casing."""

    spells: list[dict] = field(default_factory=list)
    talents: list[dict] = field(default_factory=list)
    tabs: list[dict] = field(default_factory=list)
    skill_line_abilities: list[dict] = field(default_factory=list)
    trainer_spells: list[dict] = field(default_factory=list)


MERGE_KEYS = ("spells", "talents", "tabs", "skill_line_abilities", "trainer_spells")

# The registry a class file's spell()/talent()/tab()/skill_line_ability()
# calls register into while it's being imported, and (separately) the
# reserved-ID-block config granted_by_talent() needs to tell a brand-new
# custom spell ID apart from a reused stock one (see its docstring). Plain
# module-level variables (not e.g. contextvars) are enough: load_class_file
# is the only way anything ever becomes "active", it loads one file at a
# time, synchronously, single-threaded (generate.py never imports class
# files concurrently) - there is never more than one active registry (or
# ids_cfg) at once.
_active: Registry | None = None
_active_ids_cfg: dict | None = None
_active_trainer_index = None  # lib.trainer_state.TrainerIndex | None - see trained_by()


def _require_active() -> Registry:
    if _active is None:
        raise RuntimeError(
            "spell()/talent()/tab()/skill_line_ability()/granted_by_talent() only register "
            "anything while a source/classes/*.py file is being loaded via "
            "registry.load_class_file()/load_classes_dir() - importing this module some other "
            "way (e.g. a bare `import` for its constants) registers nothing."
        )
    return _active


def spell(**kwargs) -> model.Spell:
    """Builds a `model.Spell` and registers it. Returns the `Spell` object
    itself (not the entry dict) so a talent declaration can reference its
    `.id` (`ranks=[frostbolt.id]`)."""
    s = model.Spell(**kwargs)
    _require_active().spells.append(s.to_entry())
    return s


def talent(**kwargs) -> model.Talent:
    t = model.Talent(**kwargs)
    _require_active().talents.append(t.to_entry())
    return t


def tab(**kwargs) -> model.TalentTab:
    t = model.TalentTab(**kwargs)
    _require_active().tabs.append(t.to_entry())
    return t


def skill_line_ability(**kwargs) -> model.SkillLineAbility:
    s = model.SkillLineAbility(**kwargs)
    _require_active().skill_line_abilities.append(s.to_entry())
    return s


def _require_trainer_index():
    if _active_trainer_index is None:
        raise RuntimeError(
            "trained_by() needs a lib.trainer_state.TrainerIndex to validate its TrainerId - "
            "pass one through registry.load_class_file(path, trainer_index=...) / "
            "load_classes_dir(dir_path, trainer_index=...) (generate.py already does)."
        )
    return _active_trainer_index


def trained_by(
    spell: model.Spell,
    trainer_id: int,
    req_level: int,
    money_cost: int = 0,
    req_skill_line: int = 0,
    req_skill_rank: int = 0,
    req_ability: list[int] | None = None,
) -> dict:
    """Declares a `trainer_spell` row for `spell`, granted by class trainer
    `trainer_id` - Phase 3 of `.agents/plans/spell-source-dsl/
    spell-source-dsl.PLAN.md`. `trainer_spell` has no DBC/CSV/YAML
    counterpart (see `Registry`'s docstring) - it's a plain world-DB table,
    emitted via a small generic-table SQL path in `lib/sql_out.py` rather
    than anything `lib/build.py` touches.

    The actual point: **validates `trainer_id` first**, via the
    `TrainerIndex` `generate.py` builds from `lib.trainer_state` (a static
    scan of `creature_default_trainer`/`creature_template`/`creature` - no
    live DB needed). Raises `DeadTrainerError` if `trainer_id` has no
    `creature_default_trainer` row, or every `CreatureId` it does have
    either has no `creature_template` row, isn't flagged
    `UNIT_NPC_FLAG_TRAINER`, or has no spawn in `creature` - i.e. a
    `trainer_spell` row that would go exactly nowhere, the failure mode
    behind two real bugs (see `DeadTrainerError`'s docstring). This can't
    catch "picked a *plausible but wrong* TrainerId" (a TrainerId that
    resolves to a real trainer, just not the one you meant) - only "picked
    one nothing resolves to at all"."""
    problems = _require_trainer_index().trainer_problems(trainer_id)
    if problems:
        raise DeadTrainerError(
            f"trained_by({spell.name!r}, trainer_id={trainer_id}): this TrainerId doesn't "
            f"resolve to a usable trainer NPC:\n  - " + "\n  - ".join(problems)
        )
    req_ability = (req_ability or [])[:3] + [0, 0, 0]
    row = {
        "id": f"{trainer_id}:{spell.id}",
        "TrainerId": trainer_id,
        "SpellId": spell.id,
        "MoneyCost": money_cost,
        "ReqSkillLine": req_skill_line,
        "ReqSkillRank": req_skill_rank,
        "ReqAbility1": req_ability[0],
        "ReqAbility2": req_ability[1],
        "ReqAbility3": req_ability[2],
        "ReqLevel": req_level,
        "VerifiedBuild": 0,
    }
    _require_active().trainer_spells.append(row)
    return row


# SPELL_ATTR0_PASSIVE (src/server/shared/SharedDefines.h) - "Spell is
# automatically cast on self by core", never player-cast from a Spellbook.
_SPELL_ATTR0_PASSIVE = 0x00000040


def _looks_player_castable(rank: model.Spell) -> bool:
    """Heuristic for "would a player ever see this in their Spellbook":
    a real cast time or cooldown, and not marked passive. Matches
    `apps/dbc-tools/README.md`'s own manual check ("has real cast_time/
    cooldown, Attributes isn't the passive bit")."""
    if (rank.attributes or 0) & _SPELL_ATTR0_PASSIVE:
        return False
    return bool(rank.cast_time_ms) or bool(rank.cooldown_ms)


def _is_custom_spell_id(spell_id: int) -> int:
    if _active_ids_cfg is None:
        raise RuntimeError(
            "granted_by_talent() needs ids_cfg to tell a brand-new custom spell ID apart from a "
            "reused stock one - pass it through registry.load_class_file(path, ids_cfg=...) / "
            "load_classes_dir(dir_path, ids_cfg=...) (generate.py already does)."
        )
    r = _active_ids_cfg["spell"]
    return r["start"] <= spell_id <= r["end"]


def _bundle_skill_line_ability(
    rank: model.Spell,
    tab: model.TalentTab,
    player_castable: bool | None,
    skill_line_ability_id: int | None,
) -> None:
    if not _is_custom_spell_id(rank.id):
        # Reused stock ID - already has a real SkillLineAbility row shipped in Blizzard's own
        # data, see apps/dbc-tools/README.md's "Pulling existing data in" section. Nothing to do
        # regardless of player_castable's value.
        return
    if player_castable is None:
        if _looks_player_castable(rank):
            raise MissingSkillLineAbilityError(
                f"talent rank {rank.id} ({rank.name!r}) has a real cast_time_ms/cooldown_ms and "
                f"isn't marked passive, but the granted_by_talent() call that grants it never "
                f"said player_castable=True or False."
            )
        return  # doesn't look player-castable and wasn't marked either way - fine (e.g. Icicles)
    if not player_castable:
        return
    if tab.skill_line is None:
        raise ValueError(
            f"granted_by_talent for spell {rank.id} ({rank.name!r}): tab {tab.name!r} "
            f"(id {tab.id}) has no skill_line set, but player_castable=True needs one to derive "
            f"a SkillLineAbility row - see TalentTab.skill_line's docstring."
        )
    if skill_line_ability_id is None:
        raise ValueError(
            f"granted_by_talent for spell {rank.id} ({rank.name!r}): player_castable=True needs "
            f"a matching entry in skill_line_ability_ids (mint the next ID from "
            f"source/ids.yaml's skilllineability block, 30400-30499 - see "
            f"docs/skilllineability-handoff.md)."
        )
    skill_line_ability(
        id=skill_line_ability_id,
        skill_line=tab.skill_line,
        spell_id=rank.id,
        class_mask=tab.class_mask,
    )


def granted_by_talent(
    id: int,
    tab: model.TalentTab,
    tier: int,
    column: int,
    ranks: list[model.Spell],
    player_castable: bool | None = None,
    skill_line_ability_ids: list[int | None] | None = None,
    depends_on: dict | None = None,
    flags: int = 0,
    raw_overrides: dict | None = None,
) -> model.Talent:
    """The bundling helper from spell-source-dsl.PLAN.md's Phase 2: declares
    a `Talent` row AND (for a brand-new custom spell ID) its
    `SkillLineAbility` row from one call, instead of the two independently-
    maintained lists `source/talents/*.yaml` has today - see the plan's
    "Problem this solves" for the exact bug shape this replaces (a talent
    granting a new spell ID with no matching SkillLineAbility entry, which
    silently defaults that spell to the Spellbook's "General" tab instead of
    the class's own).

    `ranks` is the real `Spell` objects returned by `spell(...)` (not bare
    IDs) - one per rank, low to high - so this can inspect each rank's own
    `cast_time_ms`/`cooldown_ms`/`attributes` to tell "hidden triggered
    effect" (e.g. Icicles) from "a player casts this from their Spellbook"
    apart.

    `player_castable`: `True` derives a `SkillLineAbility` row for every
    rank that's a brand-new custom ID (a reused stock ID already has a real
    one from Blizzard's own data - see `apps/dbc-tools/README.md`). `False`
    means "never player-cast, no row needed" (a hidden triggered buff).
    Leaving it `None` is only allowed when every rank's own `cast_time_ms`/
    `cooldown_ms`/passive-`Attributes` bit makes the answer unambiguous -
    otherwise this raises `MissingSkillLineAbilityError` rather than
    guessing, which is the whole point (see the plan).

    `skill_line_ability_ids`: one entry per rank (`None` for ranks that
    don't need one), required wherever `player_castable=True` derives a row
    for a custom ID - IDs aren't auto-minted (see the plan's "Open
    questions"), so pick the next one from `source/ids.yaml`'s
    `skilllineability` block same as today.
    """
    t = talent(
        id=id,
        tab_id=tab.id,
        tier=tier,
        column=column,
        rank_spell_ids=[r.id for r in ranks],
        depends_on=depends_on,
        flags=flags,
        raw_overrides=raw_overrides,
    )
    sla_ids = skill_line_ability_ids or [None] * len(ranks)
    if len(sla_ids) != len(ranks):
        raise ValueError(
            f"granted_by_talent for talent {id}: skill_line_ability_ids has "
            f"{len(sla_ids)} entries but ranks has {len(ranks)} - pass one per rank "
            f"(None for a rank that doesn't need one)."
        )
    for rank, sla_id in zip(ranks, sla_ids):
        _bundle_skill_line_ability(rank, tab, player_castable, sla_id)
    return t


def load_class_file(path: Path, ids_cfg: dict | None = None, trainer_index=None) -> Registry:
    """Imports one `source/classes/<class>.py` file fresh and returns
    everything it registered via `spell()`/`talent()`/`tab()`/
    `skill_line_ability()`/`granted_by_talent()`/`trained_by()`. Each call
    gets a distinct module name (`dsl_class_<stem>`) so loading two files
    with the same basename in different directories can't collide in
    `sys.modules`.

    `ids_cfg` (the parsed `source/ids.yaml`) is only needed if the file
    calls `granted_by_talent()` - see `_is_custom_spell_id`. `trainer_index`
    (a `lib.trainer_state.TrainerIndex` - accepted duck-typed here, not
    imported, so this package stays dependency-free of the rest of `lib/`)
    is only needed if the file calls `trained_by()` - see
    `_require_trainer_index`."""
    global _active, _active_ids_cfg, _active_trainer_index
    registry = Registry()
    _active = registry
    _active_ids_cfg = ids_cfg
    _active_trainer_index = trainer_index
    try:
        spec = importlib.util.spec_from_file_location(f"dsl_class_{path.stem}", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"could not load DSL class file: {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        _active = None
        _active_ids_cfg = None
        _active_trainer_index = None
    return registry


def load_classes_dir(
    dir_path: Path, ids_cfg: dict | None = None, trainer_index=None
) -> dict[str, list[dict]]:
    """Merge every `source/classes/*.py` file's registered spells/talents/
    tabs/skill_line_abilities/trainer_spells into one dict, in sorted
    filename order - same shape and merge-order convention as
    `lib.source.load_spells_csv`/`load_talents_yaml`, so `generate.py` can
    concatenate this output with theirs. A missing directory (no class has
    been migrated to the DSL yet) returns all-empty lists rather than
    erroring - this is a dual-support transition, not a hard requirement
    that the directory exist. Files whose name starts with `_` are skipped
    (reserved for future shared helpers/examples, not class declarations -
    `Registry.spells` etc. would otherwise pick them up as a fifth
    "class")."""
    merged: dict[str, list[dict]] = {key: [] for key in MERGE_KEYS}
    if not dir_path.is_dir():
        return merged
    seen: dict[str, dict[int, str]] = {key: {} for key in MERGE_KEYS}
    for path in sorted(dir_path.glob("*.py")):
        if path.name.startswith("_"):
            continue
        registry = load_class_file(path, ids_cfg=ids_cfg, trainer_index=trainer_index)
        for key in MERGE_KEYS:
            for entry in getattr(registry, key):
                if entry["id"] in seen[key]:
                    raise DuplicateIdError(
                        f"{key} entry ID {entry['id']} appears in both "
                        f"{seen[key][entry['id']]!r} and {path.name!r}"
                    )
                seen[key][entry["id"]] = path.name
                merged[key].append(entry)
    return merged
