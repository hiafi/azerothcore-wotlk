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
import itertools
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from . import model

# Unique-ifies the synthetic package name `load_class_package` registers in
# `sys.modules` per call, so two loads of the same class directory in one
# process (repeated CLI invocations within a test run, `verify_dsl_migration.py`
# comparing before/after, ...) never collide with a stale cached entry.
_package_load_counter = itertools.count()


class DuplicateIdError(ValueError):
    """Same shape/name as `lib.source.DuplicateIdError` - kept as a
    separate class (not imported from there) so this package has no
    dependency on `lib.source`; `generate.py` catches both alike."""


class MissingSkillLineAbilityError(ValueError):
    """Raised by `granted_by_talent()` when a talent grants a brand-new
    custom spell ID that looks player-castable (see `looks_player_castable`)
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
    # Three more plain world-DB tables with no DBC counterpart, same shape/
    # rationale as `trainer_spells` - see `scripted_by`/`bonus_coefficients`/
    # `procs_on` below and `lib/spell_tables.py` for how they're emitted.
    spell_script_names: list[dict] = field(default_factory=list)
    spell_bonus_data: list[dict] = field(default_factory=list)
    spell_procs: list[dict] = field(default_factory=list)
    # WP-T (.agents/plans/druid-rework/druid-rework.WP-T-HANDOFF.md, PLAN B11/§5.0): five more
    # declared tables, same "diff against live, DELETE-then-INSERT the rest" emission as the three
    # above (lib/spell_tables.py's SPELL_TABLES) - see linked_spell()/spell_group()/
    # spell_group_rule()/custom_attr()/shapeshift_form() below.
    linked_spells: list[dict] = field(default_factory=list)
    spell_groups: list[dict] = field(default_factory=list)
    spell_group_rules: list[dict] = field(default_factory=list)
    custom_attrs: list[dict] = field(default_factory=list)
    shapeshift_forms: list[dict] = field(default_factory=list)
    # Declared *removals* - key-exact DELETEs for a row this tool never emitted (stock Blizzard
    # data, or an older hand-written migration) that the normal "no longer declared" prune pass
    # can't reach (it only ever removes what a past `generate.py` run itself emitted - see
    # `lib/spell_tables.py`'s "Relationship to the prune pass" note on `unbind_script`/
    # `unlink_spell`/`leave_spell_group`/`untrain` below). Each entry holds just the target row's
    # key columns - there is no "content" to declare for a removal.
    script_removals: list[dict] = field(default_factory=list)
    linked_spell_removals: list[dict] = field(default_factory=list)
    spell_group_removals: list[dict] = field(default_factory=list)
    trainer_removals: list[dict] = field(default_factory=list)
    # Potency system (docs/potency-system.md, PLAN P4): the counterpart to spell_bonus_data above -
    # see unbind_bonus_coefficients() below.
    bonus_removals: list[dict] = field(default_factory=list)
    # T1 (.agents/plans/warlock-rework/warlock-rework.T1-HANDOFF.md): two world-DB tables outside
    # the spell system entirely - creature_template/creature_template_model, for a rework's own
    # NPCs (e.g. a talent's summoned add). Unlike every table above, creature_template is on the
    # SQL linter's do-not-delete list (apps/codestyle/codestyle-sql.py's `not_delete`), so it's
    # never diffed as DELETE-then-INSERT the way the others are - see creature_template()'s
    # docstring and lib/spell_tables.py's CREATURE_TABLES for the upsert-only emission this implies.
    creature_templates: list[dict] = field(default_factory=list)
    creature_template_models: list[dict] = field(default_factory=list)
    # Potency system (docs/potency-system.md, PLAN P2): auto-emitted by spell() whenever a
    # declared Spell had any effect with sp_potency/ap_potency - see model.Spell._resolve_potency
    # and spell_bonus_data's own entry just above (potency reuses that exact table/mechanism for
    # its half of D1; this is the new spell_potency_correction table P1 added).
    potency_corrections: list[dict] = field(default_factory=list)
    # P2b (D8 tier 3 - docs/potency-system.md's "Script numbers"): const(name, value, doc) entries
    # for hidden script numbers that belong in the generated per-class C++ header, not a potency
    # effect's base points (tier 2) or a plain potency effect (tier 1). See const() below and
    # lib/header_gen.py, which turns these (plus spell/creature ids - see spell_var_names/
    # creature_var_names) into the header text.
    consts: list[dict] = field(default_factory=list)
    # P2b: {id: python_variable_name}, found by introspecting each loaded module's own namespace
    # after it finishes executing - see _collect_var_names(). Not in MERGE_KEYS: these are dicts,
    # not lists, and merged by lib.header_gen's caller with a plain dict.update() (ids are already
    # guaranteed unique by the DuplicateIdError check every other table gets).
    spell_var_names: dict[int, str] = field(default_factory=dict)
    creature_var_names: dict[int, str] = field(default_factory=dict)


MERGE_KEYS = (
    "spells", "talents", "tabs", "skill_line_abilities", "trainer_spells",
    "spell_script_names", "spell_bonus_data", "spell_procs",
    "linked_spells", "spell_groups", "spell_group_rules", "custom_attrs", "shapeshift_forms",
    "script_removals", "linked_spell_removals", "spell_group_removals", "trainer_removals",
    "bonus_removals",
    "creature_templates", "creature_template_models",
    "potency_corrections",
    "consts",
)

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
_active_group_ids: set[int] | None = None  # existing spell_group ids, base dump + migrations - see spell_group()
_active_shapeshift_index: dict[int, dict] | None = None  # stock SpellShapeshiftForm rows by ID - see shapeshift_form()
_active_creature_rows: dict[int, dict] | None = None  # live creature_template rows by entry - see creature_template()
# creature_template's full column list/defaults, from the base dump's own CREATE TABLE (parsed by
# the caller, not here - see creature_template()'s docstring for why this module never imports
# sql_dump/trainer_state itself, the same reasoning as _active_trainer_index/_active_shapeshift_index).
_active_creature_columns: tuple[str, ...] | None = None
_active_creature_defaults: dict[str, object] | None = None


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
    entry = s.to_entry()
    registry = _require_active()
    registry.spells.append(entry)
    # Potency system (docs/potency-system.md, PLAN P2): to_entry() stashes these on `s` when the
    # spell has any potency effect - see model.Spell._resolve_potency. Declared the same automatic
    # way as every other table this module manages, so authoring a potency effect can't forget the
    # row the way a hand-written bonus_coefficients()/migration call could.
    if s.potency_bonus_row is not None:
        registry.spell_bonus_data.append(s.potency_bonus_row)
    registry.potency_corrections.extend(s.potency_correction_rows)
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
    spell: model.Spell | int,
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
    one nothing resolves to at all".

    `spell` may also be a bare stock spell ID (see `_spell_id_of`), for a
    Blizzard spell with no declaration in source that only needs a trainer."""
    spell_id = _spell_id_of(spell)
    label = spell.name if isinstance(spell, model.Spell) else spell_id
    problems = _require_trainer_index().trainer_problems(trainer_id)
    if problems:
        raise DeadTrainerError(
            f"trained_by({label!r}, trainer_id={trainer_id}): this TrainerId doesn't "
            f"resolve to a usable trainer NPC:\n  - " + "\n  - ".join(problems)
        )
    req_ability = (req_ability or [])[:3] + [0, 0, 0]
    row = {
        "id": f"{trainer_id}:{spell_id}",
        "TrainerId": trainer_id,
        "SpellId": spell_id,
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


def _spell_id_of(spell: model.Spell | int) -> int:
    """`scripted_by`/`bonus_coefficients`/`procs_on` accept either the
    `Spell` object a `spell(...)` call returned or a bare stock spell ID -
    the latter for binding to a pre-existing Blizzard spell that has no
    declaration in source at all (e.g. a script on a stock proc aura the
    rework only touches from C++), mirroring `granted_by_talent`'s own
    bare-int rank convention."""
    return spell.id if isinstance(spell, model.Spell) else int(spell)


def scripted_by(spell: model.Spell | int, *script_names: str) -> list[dict]:
    """Declares one `spell_script_names` row per name in `script_names` for
    `spell` - the C++ `SpellScript`/`AuraScript` binding(s) that
    `AddSC_<class>_spell_scripts()` registers under that name. Lives next to
    the spell declaration instead of in a hand-written migration so "wrote
    the script, forgot the row" (which fails silently - the script simply
    never runs, no boot-log line) is one call instead of a separate file.

    Binds the exact positive spell ID only - never the stock table's
    negative "-<id> = this spell and every rank in its spell_ranks chain"
    convention. A multi-rank talent binds each rank individually (the
    `Spell` objects are all right there), which doesn't depend on a
    `spell_ranks` row existing for the chain."""
    if not script_names:
        raise ValueError(f"scripted_by({_spell_id_of(spell)}): pass at least one script name")
    rows = []
    for name in script_names:
        if not name or len(name) > 64:
            raise ValueError(
                f"scripted_by({_spell_id_of(spell)}): script name {name!r} must be 1-64 chars "
                f"(spell_script_names.ScriptName is char(64))"
            )
        row = {
            "id": f"{_spell_id_of(spell)}:{name}",
            "spell_id": _spell_id_of(spell),
            "ScriptName": name,
        }
        _require_active().spell_script_names.append(row)
        rows.append(row)
    return rows


def bonus_coefficients(
    spell: model.Spell | int,
    direct: float = 0.0,
    dot: float = 0.0,
    ap: float = 0.0,
    ap_dot: float = 0.0,
    comment: str | None = None,
) -> dict:
    """Declares `spell`'s `spell_bonus_data` row - the spell-power (`direct`
    / `dot`) and attack-power (`ap` / `ap_dot`) coefficients
    `SpellMgr::GetSpellBonusData` reads, overriding the DBC-derived default
    the engine would otherwise compute from cast time. `comment` fills the
    table's own free-text `comments` column; defaults to the spell's name
    when a `Spell` object was passed."""
    if comment is None and isinstance(spell, model.Spell):
        comment = spell.name
    if isinstance(spell, model.Spell) and (spell.potency_bonus_row is not None or spell.potency_correction_rows):
        raise ValueError(
            f"bonus_coefficients({spell.id}, ...): this spell already has a potency effect, which "
            f"auto-emits its own spell_bonus_data row (docs/potency-system.md, PLAN P2 step 2) - "
            f"a hand-written bonus_coefficients() call would silently race it. Set sp_potency/"
            f"ap_potency on the effect instead."
        )
    row = {
        "id": _spell_id_of(spell),
        "entry": _spell_id_of(spell),
        "direct_bonus": float(direct),
        "dot_bonus": float(dot),
        "ap_bonus": float(ap),
        "ap_dot_bonus": float(ap_dot),
        "comments": comment,
    }
    _require_active().spell_bonus_data.append(row)
    return row


def unbind_bonus_coefficients(spell: model.Spell | int) -> dict:
    """Declares a removal of `spell`'s `spell_bonus_data` row - the counterpart to
    `bonus_coefficients()`, for retiring a stock (or previously hand-written/DSL-declared)
    coefficient row the automatic prune pass can't reach because the base dump also owns that key
    (`lib/spell_tables.py`'s `render_prune_blocks`: "the stock dump owns this key too... Resolve by
    hand" - this is that hand resolution). Needed when a spell switches to a potency effect: the
    DBC's own `EffectBonusMultiplier_N` is freshly generated and correct, but a still-live
    `spell_bonus_data` row would keep overriding it (`Unit.cpp`'s `SpellBonusData` lookup always
    wins over the DBC field - D1), silently keeping the spell on its old, pre-potency coefficient."""
    spell_id = _spell_id_of(spell)
    row = {"id": str(spell_id), "entry": spell_id}
    _require_active().bonus_removals.append(row)
    return row


def procs_on(
    spell: model.Spell | int,
    proc_flags: int,
    school_mask: int = 0,
    family_name: int = 0,
    family_mask: tuple[int, int, int] = (0, 0, 0),
    spell_type_mask: int = 0,
    spell_phase_mask: int = 0,
    hit_mask: int = 0,
    attributes_mask: int = 0,
    disable_effects_mask: int = 0,
    ppm: float = 0.0,
    chance: float = 0.0,
    cooldown_ms: int = 0,
    charges: int = 0,
) -> dict:
    """Declares `spell`'s `spell_proc` row - what the aura procs on
    (`proc_flags` is `PROC_FLAG_*`, `hit_mask` is `PROC_HIT_*`,
    `spell_type_mask`/`spell_phase_mask` are `PROC_SPELL_TYPE_*`/
    `PROC_SPELL_PHASE_*`, all from src/server/game/Spells/SpellMgr.h) and
    how often (`chance` in %, or `ppm`; `cooldown_ms` is the internal
    cooldown). `family_name`/`family_mask` restrict which triggering spells
    count, same three-dword classmask convention as everywhere else.
    Overrides whatever the DBC's own `ProcTypeMask`/`ProcChance` said - the
    row is what the engine actually uses once it exists."""
    m0, m1, m2 = (tuple(family_mask) + (0, 0, 0))[:3]
    row = {
        "id": _spell_id_of(spell),
        "SpellId": _spell_id_of(spell),
        "SchoolMask": int(school_mask),
        "SpellFamilyName": int(family_name),
        "SpellFamilyMask0": int(m0),
        "SpellFamilyMask1": int(m1),
        "SpellFamilyMask2": int(m2),
        "ProcFlags": int(proc_flags),
        "SpellTypeMask": int(spell_type_mask),
        "SpellPhaseMask": int(spell_phase_mask),
        "HitMask": int(hit_mask),
        "AttributesMask": int(attributes_mask),
        "DisableEffectsMask": int(disable_effects_mask),
        "ProcsPerMinute": float(ppm),
        "Chance": float(chance),
        "Cooldown": int(cooldown_ms),
        "Charges": int(charges),
    }
    _require_active().spell_procs.append(row)
    return row


# ---------------------------------------------------------------------------
# WP-T (.agents/plans/druid-rework/druid-rework.WP-T-HANDOFF.md, PLAN B11/§5.0):
# five more declared world-DB tables, plus their "declared removal" counterparts
# for rows this tool never emitted (stock Blizzard data, or an older hand-written
# migration) that the automatic prune pass in lib/spell_tables.py can't reach -
# see that module's "Relationship to the prune pass" note.
#
# Declared removals share four rules, enforced in lib/spell_tables.py (not here -
# a removal helper only ever needs to record *what* to remove; deciding whether
# it's already been done, whether the key is real, and whether it collides with
# something this same run also declares needs the full merged picture across
# every class file, which only exists after load_classes_dir() returns):
#   - key-exact DELETE only, rendered via sql_out.render_delete_only_block;
#   - emitted once - a generated file's DELETE already covering the key means a
#     rerun stays silent (spell_tables.load_removed_keys is the provenance);
#   - a WARNING if the key exists nowhere (base dump, migrations, module SQL) -
#     almost always a typo;
#   - an error if the same run both declares and removes the same key.
# ---------------------------------------------------------------------------

_VALID_LINKED_SPELL_TYPES = (0, 1, 2)  # SpellLinkedType (SpellMgr.h): cast / hit / aura

# SpellMgr.h/.cpp's SpellMgr::LoadSpellLinked, read carefully (verified against the real source,
# not just its header comment - see .agents/docs/systems/dbc-tools.md's WP-T section):
#
#   - `type == 0` (cast): the map key is `trigger`, unshifted - a negative trigger means "on
#     removal of the aura |trigger|" (SpellAuras.cpp reads it via `GetSpellLinked(-GetId())`); a
#     positive trigger means "on cast of trigger" (Spell.cpp's `GetSpellLinked(m_spellInfo->Id)`).
#     `effect`'s sign there: positive casts/applies `effect`, negative removes the aura `|effect|`.
#   - `type == 1` (hit) / `type == 2` (aura): the key is `trigger + SPELL_LINKED_MAX_SPELLS*type`
#     (trigger positive) or `trigger - SPELL_LINKED_MAX_SPELLS*type` (trigger negative) -
#     `SPELL_LINKED_MAX_SPELLS` is 200000. Every engine call site for these two types only ever
#     looks the key up as `GetId() + <offset>` (a real spell's *positive* id, offset added) -
#     never with a negative base - so a **negative trigger with type 1 or 2 is never looked up by
#     anything: a silently dead row**. `effect`'s sign for `type == 2` (aura, SpellAuras.cpp
#     `HandleAuraSpecificMods`): positive applies/removes the aura `effect` in lockstep with the
#     base aura; **negative grants/revokes immunity to spell `|effect|` (`ApplySpellImmune`), not
#     "remove that aura"** - the "remove that aura" behavior belongs to `type == 0`'s negative-
#     trigger branch above, a different type entirely. `type == 1` (hit, Spell.cpp
#     `GetSpellLinked(m_spellInfo->Id + SPELL_LINK_HIT)`) only ever triggers `effect` on a
#     positive-effect entry; no engine call site reads a negative `effect` for `type == 1`.
#
# The `trigger + 200000*type` offset is also why a *positive* `type == 0` trigger in
# `source/ids.yaml`'s custom spell block (200000-209999) is dangerous: it collides with whatever
# `type == 1` row (if any) exists for `trigger - 200000`. `lib/lint.py`'s
# `check_linked_spell_key_collisions` catches that case (needs the full declared+live row set,
# not available at declaration time here).
_SPELL_LINKED_MAX_SPELLS = 200000


def linked_spell(trigger: int, effect: int, type: int = 0, comment: str | None = None) -> dict:
    """Declares one `spell_linked_spell` row - `SpellMgr::LoadSpellLinked`'s trigger/effect/type
    model (`type` 0=cast, 1=hit, 2=aura - see `SpellLinkedType`, SpellMgr.h, and this module's own
    comment above `_SPELL_LINKED_MAX_SPELLS` for the full, verified-against-source semantics of
    each type and of a negative trigger/effect - they are NOT symmetric across types). `comment`
    is `NOT NULL text` in the schema; defaults to a plain description of the link when not given
    (never left empty - see `_sql_literal`'s "" == NULL collapsing, which a `NOT NULL` text column
    can't tolerate)."""
    if type not in _VALID_LINKED_SPELL_TYPES:
        raise ValueError(
            f"linked_spell({trigger}, {effect}, type={type}): type must be 0 (cast), 1 (hit) or "
            f"2 (aura) - see SpellLinkedType (SpellMgr.h)"
        )
    if type != 0 and trigger < 0:
        raise ValueError(
            f"linked_spell({trigger}, {effect}, type={type}): a negative trigger only means "
            f"anything for type=0 ('on removal of the aura |trigger|') - SpellMgr::LoadSpellLinked "
            f"only shifts a *positive* trigger by SPELL_LINKED_MAX_SPELLS*type for type 1/2, and "
            f"every engine call site for those types looks the key up as a real spell's positive "
            f"id plus that offset, never as a negative base - so this row would never be looked "
            f"up by anything. Use type=0 if you meant 'on removal of |trigger|'."
        )
    if not comment:
        comment = f"{trigger} -> {effect} (type {type})"
    row = {
        "id": f"{trigger}:{effect}:{type}",
        "spell_trigger": trigger, "spell_effect": effect, "type": type, "comment": comment,
    }
    _require_active().linked_spells.append(row)
    return row


def unlink_spell(trigger: int, effect: int, type: int = 0) -> dict:
    """Declares a removal of one `spell_linked_spell` row - the counterpart to `linked_spell()`,
    for retiring a stock relationship (or one an earlier pass declared) a rework's replacement no
    longer wants."""
    if type not in _VALID_LINKED_SPELL_TYPES:
        raise ValueError(f"unlink_spell({trigger}, {effect}, type={type}): type must be 0, 1 or 2")
    if type != 0 and trigger < 0:
        raise ValueError(
            f"unlink_spell({trigger}, {effect}, type={type}): a negative trigger only means "
            f"anything for type=0 - see linked_spell()'s docstring; a type 1/2 row is always keyed "
            f"on a positive trigger."
        )
    row = {
        "id": f"{trigger}:{effect}:{type}",
        "spell_trigger": trigger, "spell_effect": effect, "type": type,
    }
    _require_active().linked_spell_removals.append(row)
    return row


def _require_group_ids() -> set[int]:
    if _active_group_ids is None:
        raise RuntimeError(
            "spell_group()/spell_group_rule() need the existing spell_group ids (base dump + "
            "migrations) to tell a legitimate 'add a member to a stock group' apart from a "
            "typo'd id - pass them through registry.load_class_file(path, existing_group_ids=...) "
            "/ load_classes_dir(dir_path, existing_group_ids=...) (generate.py already does)."
        )
    return _active_group_ids


def _validate_group_id(group_id: int, caller: str) -> None:
    """A `spell_group`/`spell_group_stack_rules` id must be a fresh mint from `source/ids.yaml`'s
    `spell_group` block, or already exist in stock/migration data - `SpellMgr.h`'s
    `SPELL_GROUP_DB_RANGE_MIN` (1000) is the engine's own floor for a DB-defined group, but
    "adding members to a stock group like 1054 or 1016" is explicitly legitimate (WP-T handoff),
    so a bare range check against the reserved block alone would wrongly reject that."""
    ids_cfg = _active_ids_cfg
    if ids_cfg is not None:
        r = ids_cfg.get("spell_group")
        if r and r["start"] <= group_id <= r["end"]:
            return
    if group_id in _require_group_ids():
        return
    raise ValueError(
        f"{caller}({group_id}, ...): group id {group_id} is neither inside source/ids.yaml's "
        f"spell_group reserved block nor an id already present in stock/migration data - mint a "
        f"new one from that block, or double check the id if you meant to add a member/rule to "
        f"an existing group."
    )


def spell_group(group_id: int, *spells: model.Spell | int) -> list[dict]:
    """Declares one `spell_group` row per member in `spells` (`SpellMgr::LoadSpellGroups`), each
    either the `Spell` object `spell(...)` returned or a bare stock spell id - same convention as
    every other helper here (`_spell_id_of`). `group_id` must be a fresh id from
    `source/ids.yaml`'s `spell_group` block, or an id that already exists in stock/migration data
    (adding a member to a stock group, e.g. 1054 or 1016, is legitimate - see
    `_validate_group_id`). A negative member id is a *nested-group reference* (the loader expands
    a rank chain itself - this is not that), not a typo - pass a bare negative int for it, since a
    nested group has no `Spell` object of its own."""
    if not spells:
        raise ValueError(f"spell_group({group_id}): pass at least one member spell id")
    _validate_group_id(group_id, "spell_group")
    rows = []
    for member in spells:
        spell_id = _spell_id_of(member)
        # The real SQL column is `id` (the group id) - the same name the generic per-list
        # duplicate-declaration dedup below keys on for every other table, which would otherwise
        # misread "two different members of the same group" as a duplicate declaration. `_dedup_id`
        # is load_classes_dir's escape hatch for exactly this collision - see its docstring.
        row = {"id": group_id, "spell_id": spell_id, "_dedup_id": f"{group_id}:{spell_id}"}
        _require_active().spell_groups.append(row)
        rows.append(row)
    return rows


def leave_spell_group(group_id: int, spell: model.Spell | int) -> dict:
    """Declares a removal of one `(group_id, spell_id)` row from `spell_group` - the counterpart
    to `spell_group()`, for retiring one spell's membership (its own reworked group, or a stock
    one) without touching the rest of the group. No id-range validation - removing never mints."""
    spell_id = _spell_id_of(spell)
    row = {"id": group_id, "spell_id": spell_id, "_dedup_id": f"{group_id}:{spell_id}"}
    _require_active().spell_group_removals.append(row)
    return row


_VALID_STACK_RULES = (0, 1, 2, 3, 4)  # SpellGroupStackRule (SpellMgr.h): DEFAULT..EXCLUSIVE_HIGHEST


def spell_group_rule(group_id: int, stack_rule: int, description: str = "") -> dict:
    """Declares `group_id`'s `spell_group_stack_rules` row - `SpellGroupStackRule` (SpellMgr.h)
    controlling how the engine treats simultaneously-active auras from spells in that group. Same
    id-legitimacy rule as `spell_group()` (fresh mint from the reserved block, or an id that
    already exists). `description` defaults to a plain, never-empty placeholder: the column is
    `varchar(150) NOT NULL DEFAULT ''`, but `sql_out._sql_literal` renders an empty Python string
    the same as `None` (`NULL`) - fine for a nullable column, a constraint violation for this
    one - so an empty/unset `description` is never passed through as `""` literally."""
    if stack_rule not in _VALID_STACK_RULES:
        raise ValueError(
            f"spell_group_rule({group_id}, stack_rule={stack_rule}): not a real "
            f"SpellGroupStackRule (SpellMgr.h) - valid values are {list(_VALID_STACK_RULES)}"
        )
    _validate_group_id(group_id, "spell_group_rule")
    row = {
        "id": group_id, "group_id": group_id, "stack_rule": stack_rule,
        "description": description or f"spell_group {group_id}",
    }
    _require_active().spell_group_rules.append(row)
    return row


def custom_attr(spell: model.Spell | int, attributes: int) -> dict:
    """Declares `spell`'s `spell_custom_attr` row (`SpellCustomAttributes`, `SpellInfo.h`) -
    server-only per-spell behavior flags the engine layers on top of the DBC data (e.g.
    `SPELL_ATTR0_CU_POSITIVE_EFF0/1/2`, individually or OR'd as `SPELL_ATTR0_CU_POSITIVE`, for a
    beneficial spell the engine's own heuristic misclassifies - there is no single
    `SPELL_ATTR0_CU_POSITIVE` bit; double-check the exact flag against `SpellInfo.h` before using
    one, the values are dense and easy to transpose). Stock rows exist for many spells; declaring
    one here replaces that row, same as every other table in this module."""
    spell_id = _spell_id_of(spell)
    row = {"id": spell_id, "spell_id": spell_id, "attributes": int(attributes)}
    _require_active().custom_attrs.append(row)
    return row


_VALID_CONST_CPP_TYPES = ("int32", "uint32", "uint8", "uint16", "float", "Milliseconds")
_CONST_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


def const(name: str, value: int | float, doc: str = "", cpp_type: str | None = None) -> dict:
    """P2b (D8 tier 3 - docs/potency-system.md's "Script numbers"): declares one hidden script
    number for the generated per-class C++ header (`lib/header_gen.py`, `generate.py --check`) -
    "internal timers, ranges, hidden multipliers" that aren't a potency effect (tier 1) or a value
    a tooltip shows / a talent can modify (tier 2, which belongs in an effect's base points
    instead, read with `GetAmount()`/`CalcValue()`). Unlike `spell()`/`talent()`/
    `creature_template()`, the header's constant name is `name` itself, not inferred from the
    Python variable this call is assigned to - there's no DBC id to derive a shorter name from, so
    the author just names it (`"WARLOCK_SOUL_SHARD_CAP"`, not `SPELL_`/`NPC_`-prefixed since it
    isn't one). `cpp_type` defaults from `value`'s own Python type (`int` -> `int32`, `float` ->
    `float`) - pass it explicitly for anything else (`uint32`, `Milliseconds`, ...)."""
    if not _CONST_NAME_RE.match(name):
        raise ValueError(
            f"const({name!r}, ...): name must be SCREAMING_SNAKE_CASE (matches {_CONST_NAME_RE.pattern}) "
            f"- it becomes the generated header's constant name verbatim."
        )
    if cpp_type is None:
        cpp_type = "float" if isinstance(value, float) else "int32"
    elif cpp_type not in _VALID_CONST_CPP_TYPES:
        raise ValueError(f"const({name!r}): cpp_type must be one of {_VALID_CONST_CPP_TYPES}, got {cpp_type!r}")
    row = {"id": name, "name": name, "value": value, "doc": doc, "cpp_type": cpp_type}
    _require_active().consts.append(row)
    return row


def unbind_script(spell: model.Spell | int, script_name: str) -> dict:
    """Declares a removal of one `spell_script_names` row - the counterpart to `scripted_by()`,
    for retiring a stock (or previously hand-written) C++ binding, e.g. when a rework's
    replacement class rebinds the spell under a new `ScriptName`."""
    spell_id = _spell_id_of(spell)
    row = {"id": f"{spell_id}:{script_name}", "spell_id": spell_id, "ScriptName": script_name}
    _require_active().script_removals.append(row)
    return row


def untrain(spell: model.Spell | int, trainer_ids: list[int]) -> list[dict]:
    """Declares a removal of `spell`'s `trainer_spell` row for each id in `trainer_ids` - the
    counterpart to `trained_by()`, for a spell a rework no longer wants any class trainer to
    teach. `trainer_ids` is the *live* list of TrainerIds that actually teach this spell right now
    (a server's real, possibly module-rewired, trainer id - see `lib.trainer_state`'s module
    docstring - not necessarily the stock one), since each becomes its own key-exact DELETE.

    Known limitation, inherent to removing a *module*-granted row this way, not something this
    helper can fix: `DBUpdater` applies core `pending_db_world`/`db_world` SQL (this DELETE)
    before `OnAfterDatabasesLoaded` applies module SQL (mod-progression's phase files). On a
    fresh database, or when `Progression.Phase` later advances past a phase that (re)inserts this
    exact row, the module's own INSERT runs *after* this DELETE and silently brings the grant
    back - the removal only reads as "done" (via provenance) and is never re-emitted. The
    hand-written migration this helper replaces (see the WP-T handoff) had the identical
    limitation; there is no DB-update-ordering fix available from this tool."""
    spell_id = _spell_id_of(spell)
    if not trainer_ids:
        raise ValueError(f"untrain({spell_id}, ...): pass at least one trainer id")
    rows = []
    for trainer_id in trainer_ids:
        row = {"id": f"{trainer_id}:{spell_id}", "TrainerId": trainer_id, "SpellId": spell_id}
        _require_active().trainer_removals.append(row)
        rows.append(row)
    return rows


# DBCStructure.h's SpellShapeshiftFormEntry field names, for the handful that differ from this
# table's SQL column name (see lib.dbcfmt.SPELLSHAPESHIFTFORM's own comment for the full mapping) -
# a human reading a design doc knows "attackSpeed", not "CombatRoundTime".
_SHAPESHIFT_FRIENDLY_COLUMNS = {
    "flags1": "Flags",
    "creatureType": "CreatureType",
    "attackSpeed": "CombatRoundTime",
    "modelID_A": "CreatureDisplayID_1",
    "modelID_H": "CreatureDisplayID_2",
}


def _require_shapeshift_index() -> dict:
    if _active_shapeshift_index is None:
        raise RuntimeError(
            "shapeshift_form() needs the stock SpellShapeshiftForm rows (lib.dbcfmt."
            "SPELLSHAPESHIFTFORM, base DBC + base SQL) to build a full override row from - pass "
            "them through registry.load_class_file(path, shapeshift_index=...) / "
            "load_classes_dir(dir_path, shapeshift_index=...) (generate.py already does)."
        )
    return _active_shapeshift_index


def shapeshift_form(form_id: int, **changed_columns) -> dict:
    """Declares a full-row override of `spellshapeshiftform_dbc`'s stock `form_id` row: every
    column starts at the real client value (`shapeshift_index`, the base DBC + base SQL - see
    `load_class_file`'s docstring) and `changed_columns` overwrites just the named ones - e.g.
    `shapeshift_form(5, attackSpeed=3500)` for Bear Form's melee swing timer. Accepts either the
    real SQL column name (`CombatRoundTime`) or the friendlier `DBCStructure.h` field name a
    design doc is more likely to use (`attackSpeed`) - see `_SHAPESHIFT_FRIENDLY_COLUMNS`.

    Unlike a hand-authored `spell()`/`talent()` row, there is no reserved-ID-block minting here:
    `form_id` always names an existing stock form (CAT=1, TREE=2, TRAVEL=3, AQUA=4, BEAR=5, ...,
    MOONKIN=31 in retail 3.3.5a), so declaring one always means "override this real form", never
    "create a new one" - nothing in the client's UI can address a form id nothing points at.
    Server-side only: no client patch is produced for this table (nothing the client renders
    depends on it - contrast `docs/shapeshift-appearances.md`'s CreatureDisplayInfo/
    CreatureModelData, which does)."""
    index = _require_shapeshift_index()
    if not index:
        # Distinct from "not a real form id" below: an *empty* index almost always means
        # var/extractors/dbc/SpellShapeshiftForm.dbc isn't extracted on this checkout at all
        # (it's gitignored - a fresh clone or another machine won't have it) rather than form_id
        # being wrong - see apps/dbc-tools/README.md's "Setup" section for extraction, and
        # .agents/docs/systems/dbc-tools.md's WP-T section for exactly how this file was pulled.
        raise RuntimeError(
            "shapeshift_form(): the stock SpellShapeshiftForm index is empty - "
            "var/extractors/dbc/SpellShapeshiftForm.dbc is probably missing on this checkout "
            "(extract it from patch-enUS-3.MPQ, same as Item.dbc), not a bad form_id."
        )
    stock = index.get(form_id)
    if stock is None:
        raise ValueError(
            f"shapeshift_form({form_id}, ...): no stock SpellShapeshiftForm row for id {form_id} "
            f"- not a real shapeshift form id ({len(index)} stock rows are loaded, so this isn't "
            f"a missing-extraction problem)"
        )
    row = dict(stock)
    unknown = [
        key for key in changed_columns
        if key not in _SHAPESHIFT_FRIENDLY_COLUMNS and key not in row
    ]
    if unknown:
        raise KeyError(
            f"shapeshift_form({form_id}): no such column(s): {', '.join(sorted(unknown))} - see "
            f"lib.dbcfmt.SPELLSHAPESHIFTFORM.columns for the real names, or "
            f"_SHAPESHIFT_FRIENDLY_COLUMNS for the DBCStructure.h aliases this accepts"
        )
    for key, value in changed_columns.items():
        row[_SHAPESHIFT_FRIENDLY_COLUMNS.get(key, key)] = value
    row["id"] = form_id
    _require_active().shapeshift_forms.append(row)
    return row


# ---------------------------------------------------------------------------
# T1 (.agents/plans/warlock-rework/warlock-rework.T1-HANDOFF.md): creature_template/
# creature_template_model - a rework's own NPCs (e.g. a talent's summoned add), previously always a
# hand-written migration (data/sql/updates/db_world/2026_09_23_12.sql, Tentacle of Madness - the
# shape both helpers below reproduce). creature_template is on the SQL linter's do-not-delete list
# (apps/codestyle/codestyle-sql.py's `not_delete`), so unlike every table above this one is never
# emitted as DELETE-then-INSERT - see lib/spell_tables.py's CREATURE_TABLES/render_creature_blocks
# for the upsert-only path this implies, and lib/sql_out.py's render_upsert_block for the rendering.
# ---------------------------------------------------------------------------

# Columns where the CREATE TABLE's own DEFAULT is what ObjectMgr::CheckCreatureTemplate (ObjectMgr.cpp)
# rejects or silently rewrites at every boot, so a declaration that doesn't mention the column
# would otherwise ship a value the engine never actually uses:
#   - unit_class: schema DEFAULT is 0; CheckCreatureTemplate treats 0 as invalid ("has invalid
#     unit_class") and rewrites it to 1 (CLASS_WARRIOR) every time creature_template loads.
#   - BaseAttackTime / RangeAttackTime: schema DEFAULT is 0; CheckCreatureTemplate silently
#     substitutes BASE_ATTACK_TIME (2000) for either column whenever it's exactly 0.
# VerifiedBuild is always 0 here (T1 handoff) rather than the schema's DEFAULT NULL - every other
# helper in this module writes 0 for it too (see trained_by/scripted_by/bonus_coefficients/...).
_CREATURE_TEMPLATE_DEFAULT_OVERRIDES = {
    "unit_class": 1,
    "BaseAttackTime": 2000,
    "RangeAttackTime": 2000,
    "VerifiedBuild": 0,
}


def _require_creature_columns() -> tuple[str, ...]:
    if _active_creature_columns is None:
        raise RuntimeError(
            "creature_template() needs creature_template's full column list (parsed from "
            "data/sql/base/db_world/creature_template.sql's own CREATE TABLE - too wide, ~54 "
            "columns, to safely hand-transcribe) - pass it through registry.load_class_file(path, "
            "creature_columns=...) / load_classes_dir(dir_path, creature_columns=...) "
            "(generate.py already does)."
        )
    return _active_creature_columns


def _require_creature_defaults() -> dict[str, object]:
    if _active_creature_defaults is None:
        raise RuntimeError(
            "creature_template() needs creature_template's per-column DEFAULT values (parsed from "
            "the same CREATE TABLE as creature_columns) - pass them through "
            "registry.load_class_file(path, creature_defaults=...) / "
            "load_classes_dir(dir_path, creature_defaults=...) (generate.py already does)."
        )
    return _active_creature_defaults


def _require_creature_rows() -> dict[int, dict]:
    if _active_creature_rows is None:
        raise RuntimeError(
            "creature_template() needs the live creature_template rows (base dump + migrations, "
            "keyed by entry) both to tell a legitimate override of an already-existing row apart "
            "from a typo'd entry outside source/ids.yaml's creature block, and to preserve that "
            "row's untouched columns on an override - pass them through "
            "registry.load_class_file(path, existing_creature_rows=...) / "
            "load_classes_dir(dir_path, existing_creature_rows=...) (generate.py already does)."
        )
    return _active_creature_rows


def _validate_creature_entry(entry: int) -> None:
    """A `creature_template` entry must be a fresh mint from `source/ids.yaml`'s `creature` block,
    or an entry that already exists (base dump or migrations) - re-declaring a live custom entry
    (e.g. 300102, Tentacle of Madness) to override it is legitimate, the same "add a member to an
    existing group" exception `spell_group()`'s `_validate_group_id` makes."""
    ids_cfg = _active_ids_cfg
    if ids_cfg is not None:
        r = ids_cfg.get("creature")
        if r and r["start"] <= entry <= r["end"]:
            return
    if entry in _require_creature_rows():
        return
    raise ValueError(
        f"creature_template({entry}, ...): entry {entry} is neither inside source/ids.yaml's "
        f"creature reserved block nor an entry that already exists in the base dump/migrations - "
        f"mint a new one from that block, or double check the id if you meant to override an "
        f"existing creature."
    )


def creature_template(entry: int, name: str, **columns) -> dict:
    """Declares one `creature_template` row (`ObjectMgr::LoadCreatureTemplates`) - a rework's own
    NPC, e.g. a talent's summoned add (Tentacle of Madness, `data/sql/updates/db_world/
    2026_09_23_12.sql`, is the row this helper reproduces). `entry` must be a fresh id from
    `source/ids.yaml`'s `creature` block, or an entry that already exists (see
    `_validate_creature_entry`) - overriding a live custom entry is a legitimate re-declaration.

    Builds a **full** row: every column in creature_template's real column list (parsed from its
    own `CREATE TABLE`, never hand-transcribed - see `_require_creature_columns`) gets a value, so
    the emitted `INSERT` always has every column, matching `sql_out.render_upsert_block`'s
    "declared row replaces whatever's live" upsert semantics. A column's value is, in order:
    `name` (the required parameter) for the `name` column; whatever `columns` passes explicitly;
    **the entry's current live value, if `entry` already exists** (an override that doesn't
    mention a column must not reset it - see the note below); `_CREATURE_TEMPLATE_DEFAULT_OVERRIDES`
    for the handful of columns whose schema DEFAULT the engine rejects or silently rewrites at boot
    (see that dict's own comment, and only reached for genuinely new content, since an existing row
    already has *some* value there); otherwise the column's real schema DEFAULT. An unknown column
    name in `columns` raises `KeyError` naming it - a typo here must not silently produce a
    spurious extra column or get ignored.

    **Overriding an existing entry never wipes a column you didn't mention.** `shapeshift_form()`
    already has to solve this same problem (a full-row override starting from the stock DBC row) -
    this mirrors it: `entry`'s current live row (from `existing_creature_rows`, see
    `_require_creature_rows`) is the starting point for every column you don't pass explicitly,
    not the schema default. Get this wrong (as this helper originally did - found via code review,
    2026-09-28) and re-declaring Tentacle of Madness (300102) to fix just its `ScriptName` would
    have reset its faction, levels, flags and every modifier back to schema defaults, with no
    warning - `_validate_creature_entry` explicitly allows overriding *any* existing entry in the
    block (a real collision with e.g. Frozen Orb 300001, not just an intentional override of your
    own past declaration, is accepted the same way), so this isn't a rare edge case.

    Unlike every other table this module declares, `creature_template` is on the SQL linter's
    do-not-delete list (`apps/codestyle/codestyle-sql.py`'s `not_delete`) - it is never emitted as
    a DELETE-then-INSERT, and a declaration removed from source is never pruned either (see
    `lib/spell_tables.py`'s `CREATURE_TABLES`/`render_creature_retirement_report` - it's reported
    for a human to remove by hand instead)."""
    all_columns = _require_creature_columns()
    schema_defaults = _require_creature_defaults()
    _validate_creature_entry(entry)
    unknown = [c for c in columns if c not in all_columns]
    if unknown:
        raise KeyError(
            f"creature_template({entry}): no such column(s): {', '.join(sorted(unknown))} - see "
            f"data/sql/base/db_world/creature_template.sql's CREATE TABLE for the real names"
        )
    live_row = _require_creature_rows().get(entry)
    row: dict = {}
    for column in all_columns:
        if column == "entry":
            continue
        if column == "name":
            row[column] = name
        elif column in columns:
            row[column] = columns[column]
        elif live_row is not None and column in live_row:
            row[column] = live_row[column]
        elif column in _CREATURE_TEMPLATE_DEFAULT_OVERRIDES:
            row[column] = _CREATURE_TEMPLATE_DEFAULT_OVERRIDES[column]
        else:
            row[column] = schema_defaults.get(column)
    row["entry"] = entry
    row["id"] = entry
    _require_active().creature_templates.append(row)
    return row


def creature_model(
    entry: int, display_id: int, scale: float = 1.0, idx: int = 0, probability: float = 1.0,
) -> dict:
    """Declares one `creature_template_model` row (`ObjectMgr::LoadCreatureTemplateModels`) for
    `entry` (an id `creature_template()` declared, or a bare int for an existing creature). Unlike
    `creature_template()`, this is a plain, narrow table (6 columns, none reused elsewhere) - no
    `**columns` escape hatch, just the columns a design doc actually needs.

    `probability` defaults to `1.0`, not the schema's own `0` - `ObjectMgr::CheckCreatureTemplate`
    resets *every* model's probability to `1.0` when the models on a creature sum to exactly `0`
    (`totalProbability <= 0.0f` branch, harmless for one model but a real footgun once a second
    model is added later with its own nonzero weight and the first one's `0` no longer reads as
    "equal chance"). `VerifiedBuild` is always 0, same convention as every other helper here."""
    row = {
        "id": f"{entry}:{idx}",
        "CreatureID": entry,
        "Idx": idx,
        "CreatureDisplayID": display_id,
        "DisplayScale": float(scale),
        "Probability": float(probability),
        "VerifiedBuild": 0,
    }
    _require_active().creature_template_models.append(row)
    return row


# SPELL_ATTR0_PASSIVE (src/server/shared/SharedDefines.h) - "Spell is
# automatically cast on self by core", never player-cast from a Spellbook.
_SPELL_ATTR0_PASSIVE = 0x00000040


def looks_player_castable(rank: model.Spell) -> bool:
    """Heuristic for "would a player ever see this in their Spellbook": not
    marked passive, and has *some* real sign of being actively cast - a real
    cast time, cooldown (plain or category), or mana cost. Public (not
    `_`-prefixed) because `split_class_file.py` reuses it as the same
    castable/trigger-only split rule `granted_by_talent()` already uses for
    its own player_castable validation - one heuristic, not two
    independently-maintained ones.

    Originally checked only `cast_time_ms`/`cooldown_ms` - wrong for a
    surprisingly large, common class of real player spells: an instant,
    off-GCD-cooldown or free-cast active spell legitimately has both at 0
    (e.g. Frost Nova's actual cooldown lives in `category_cooldown_ms`, not
    `cooldown_ms`; Arcane Intellect/Frost Armor/Mage Armor/... are instant,
    no-cooldown buffs whose only "this is really cast, not a passive/proc"
    signal is a real `mana_cost_pct`). Found via `split_class_file.py`
    misfiling ~40 real Mage spells (Blizzard, Frost Nova, Blink, Counterspell,
    Arcane Missiles, the armor buffs, ...) into `mage_trigger_spells.py` -
    every one had `cast_time_ms=cooldown_ms=0` but a real `mana_cost_pct` or
    `category_cooldown_ms`. Checking all of `cast_time_ms`/`cooldown_ms`/
    `category_cooldown_ms`/`mana_cost`/`mana_cost_pct` fixes every one of
    those with no observed false positive (every genuinely trigger-only
    spell checked - e.g. Arcane Blast's own debuff, 36032 - has all five at
    0), but a truly free *and* off-any-cooldown-category active spell (rare)
    could still slip through undetected as "doesn't look castable" - same
    "heuristic, not proof" caveat this function always had."""
    if (rank.attributes or 0) & _SPELL_ATTR0_PASSIVE:
        return False
    return bool(
        rank.cast_time_ms or rank.cooldown_ms or rank.category_cooldown_ms
        or rank.mana_cost or rank.mana_cost_pct
    )


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
        if looks_player_castable(rank):
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
    ranks: list[model.Spell | int],
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

    `ranks` is normally the real `Spell` objects returned by `spell(...)` -
    one per rank, low to high - so this can inspect each rank's own
    `cast_time_ms`/`cooldown_ms`/`attributes` to tell "hidden triggered
    effect" (e.g. Icicles) from "a player casts this from their Spellbook"
    apart. **A bare `int` is also accepted**, for a rank that's a pre-
    existing stock spell ID with no `Spell()` declaration of its own in this
    file (real example found migrating Mage's talents in Phase 4: a handful
    of low-rank stock IDs used only as an old talent rank, never pulled into
    source at all) - safe by construction, since a *custom* ID can only ever
    exist via a `Spell()` call somewhere in this pipeline (that's the only
    way a `spell_dbc` row gets emitted), so a bare int can never secretly be
    one; bundling is skipped for it entirely, the same as a stock `Spell`
    object would get from `_is_custom_spell_id`.

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
    rank_ids = [r.id if isinstance(r, model.Spell) else r for r in ranks]
    t = talent(
        id=id,
        tab_id=tab.id,
        tier=tier,
        column=column,
        rank_spell_ids=rank_ids,
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
        if isinstance(rank, model.Spell):
            _bundle_skill_line_ability(rank, tab, player_castable, sla_id)
        # else: a bare-int rank is always a pre-existing stock ID - see the docstring above for
        # why that's safe to skip outright, with no _is_custom_spell_id check even needed.
    return t


def _exec_fresh_module(mod_name: str, path: Path, package: str | None = None):
    """Builds and executes a module from `path` under `mod_name`, always
    compiling the current on-disk source - deliberately bypassing
    `spec.loader.exec_module()`'s normal `__pycache__/*.pyc` staleness check
    (mtime+size), which only invalidates the cache when either changed. Two
    loads of the *same path* within one process with an edit that happens to
    keep both identical (same second, same byte length - a real way to hit
    this: a test, or any tool, rewriting a class file and immediately
    reloading it) would otherwise silently serve the previous run's stale
    compiled code. `sys.modules[mod_name]` is set before exec'ing (as
    `importlib` itself always does) so a relative import from within this
    module's own source can find it, and so a *nested* relative import that
    pulls in a sibling module before we get to it in our own loop still ends
    up registered the same way."""
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None:
        raise ImportError(f"could not load DSL class file: {path}")
    module = importlib.util.module_from_spec(spec)
    if package is not None:
        module.__package__ = package
    sys.modules[mod_name] = module
    source = path.read_text(encoding="utf-8")
    code = compile(source, str(path), "exec")
    exec(code, module.__dict__)
    return module


def _collect_var_names(module, registry: Registry) -> None:
    """P2b: fills `registry.spell_var_names`/`creature_var_names` from the already-executed
    `module`'s own top-level namespace - `shadow_bolt_686 = spell(id=686, ...)` binds the real
    `model.Spell` object to that name, so `vars(module)` is the ground truth for "what did the
    author call this", no AST parsing needed. `spell()` returns the `Spell` object itself (matched
    here by `isinstance` + `.id`); `creature_template()` returns the *exact same dict* it already
    appended to `registry.creature_templates` (matched by identity, since a dict has no type to
    `isinstance`-check and no stable field this function should assume - `id(obj)` against that
    list is exact and needs no guessing). `talent()`'s own `Talent.dbc` row id is deliberately not
    collected - see `lib/header_gen.py`'s module docstring for why a script never wants that id at
    all (it wants a specific rank's spell id, already covered by the spell-id case above)."""
    creature_row_ids = {id(row): row["entry"] for row in registry.creature_templates}
    for name, obj in vars(module).items():
        if name.startswith("_"):
            continue
        if isinstance(obj, model.Spell):
            registry.spell_var_names.setdefault(obj.id, name)
        elif isinstance(obj, dict) and id(obj) in creature_row_ids:
            registry.creature_var_names.setdefault(creature_row_ids[id(obj)], name)


def load_class_file(
    path: Path, ids_cfg: dict | None = None, trainer_index=None,
    existing_group_ids: set[int] | None = None, shapeshift_index: dict | None = None,
    existing_creature_rows: dict[int, dict] | None = None, creature_columns: tuple[str, ...] | None = None,
    creature_defaults: dict[str, object] | None = None,
) -> Registry:
    """Imports one `source/classes/<class>.py` file fresh and returns
    everything it registered via `spell()`/`talent()`/`tab()`/
    `skill_line_ability()`/`granted_by_talent()`/`trained_by()`. Each call
    gets a distinct module name (`dsl_class_<stem>`) so loading two files
    with the same basename in different directories can't collide in
    `sys.modules`.

    `ids_cfg` (the parsed `source/ids.yaml`) is only needed if the file
    calls `granted_by_talent()` - see `_is_custom_spell_id` - or
    `spell_group()`/`spell_group_rule()` - see `_validate_group_id`.
    `trainer_index` (a `lib.trainer_state.TrainerIndex` - accepted duck-typed
    here, not imported, so this package stays dependency-free of the rest of
    `lib/`) is only needed if the file calls `trained_by()` - see
    `_require_trainer_index`. `existing_group_ids` (a plain `set[int]`, same
    duck-typed reasoning) is only needed for `spell_group()`/
    `spell_group_rule()` - see `_require_group_ids`. `shapeshift_index` (a
    plain `dict[int, dict]`) is only needed for `shapeshift_form()` - see
    `_require_shapeshift_index`. `existing_creature_rows`/`creature_columns`/
    `creature_defaults` are only needed for `creature_template()` - see
    `_require_creature_ids`/`_require_creature_columns`/`_require_creature_defaults`."""
    global _active, _active_ids_cfg, _active_trainer_index, _active_group_ids, _active_shapeshift_index
    global _active_creature_rows, _active_creature_columns, _active_creature_defaults
    registry = Registry()
    _active = registry
    _active_ids_cfg = ids_cfg
    _active_trainer_index = trainer_index
    _active_group_ids = existing_group_ids
    _active_shapeshift_index = shapeshift_index
    _active_creature_rows = existing_creature_rows
    _active_creature_columns = creature_columns
    _active_creature_defaults = creature_defaults
    mod_name = f"dsl_class_{path.stem}"
    try:
        module = _exec_fresh_module(mod_name, path)
        _collect_var_names(module, registry)
    finally:
        _active = None
        _active_ids_cfg = None
        _active_trainer_index = None
        _active_group_ids = None
        _active_shapeshift_index = None
        _active_creature_rows = None
        _active_creature_columns = None
        _active_creature_defaults = None
        sys.modules.pop(mod_name, None)
    return registry


def load_class_package(
    dir_path: Path, ids_cfg: dict | None = None, trainer_index=None,
    existing_group_ids: set[int] | None = None, shapeshift_index: dict | None = None,
    existing_creature_rows: dict[int, dict] | None = None, creature_columns: tuple[str, ...] | None = None,
    creature_defaults: dict[str, object] | None = None,
) -> Registry:
    """Imports every `*.py` file inside `dir_path` (a `source/classes/<class>/`
    directory - the multi-file layout, one class split across e.g.
    `<class>_spells.py`/`<class>_trigger_spells.py`/`<class>_talents.py`
    instead of one `<class>.py`) as a single real Python package, so a file
    can `from .sibling_module import some_var` to reference a spell/tab
    declared in a different file of the same class - standard Python import
    resolution (not a custom reordering pass) is what lets
    `<class>_talents.py` reference a spell from `<class>_spells.py`
    regardless of which file happens to be read first, and lets a spell in
    `<class>_spells.py` reference a `trigger_spell` target declared in
    `<class>_trigger_spells.py` even though (unlike a same-file reference)
    there's no "must be declared earlier" ordering constraint at all - the
    import statement itself pulls the target module in and runs it first.

    The package is synthetic (its name isn't meaningful, doesn't need to
    match anything on `sys.path`) and always registered under a fresh,
    counter-suffixed name so calling this twice in one process (tests,
    `verify_dsl_migration.py`'s dual load, ...) never hits a stale cached
    module - `sys.modules` entries this call adds are removed again in
    `finally`, same "always fresh" contract `load_class_file` already has for
    the single-file case. Files starting with `_` are skipped, same
    convention as `load_classes_dir`."""
    global _active, _active_ids_cfg, _active_trainer_index, _active_group_ids, _active_shapeshift_index
    global _active_creature_rows, _active_creature_columns, _active_creature_defaults
    pkg_name = f"dsl_classpkg_{dir_path.name}_{next(_package_load_counter)}"
    pkg_spec = importlib.util.spec_from_loader(pkg_name, loader=None, is_package=True)
    pkg_module = importlib.util.module_from_spec(pkg_spec)
    pkg_module.__path__ = [str(dir_path)]
    registry = Registry()
    _active = registry
    _active_ids_cfg = ids_cfg
    _active_trainer_index = trainer_index
    _active_group_ids = existing_group_ids
    _active_shapeshift_index = shapeshift_index
    _active_creature_rows = existing_creature_rows
    _active_creature_columns = creature_columns
    _active_creature_defaults = creature_defaults
    sys.modules[pkg_name] = pkg_module
    # A sibling's own `from .other import x` is resolved by Python's *standard* import
    # machinery (not our `_exec_fresh_module`, which only covers the files this loop reaches
    # directly) - it goes through the normal `.pyc`-caching `SourceFileLoader`, so it needs the
    # same "always fresh" guarantee applied at the interpreter level for this call's duration,
    # not just per-file. See `_exec_fresh_module`'s docstring for the exact staleness scenario
    # this closes (same mtime + same byte length between two loads in one process).
    dont_write_bytecode, sys.dont_write_bytecode = sys.dont_write_bytecode, True
    try:
        for path in sorted(dir_path.glob("*.py")):
            if path.name.startswith("_"):
                continue
            mod_name = f"{pkg_name}.{path.stem}"
            if mod_name in sys.modules:
                # A sibling file's own relative import already pulled this one in - still need
                # its namespace for _collect_var_names (P2b), just not a second exec.
                _collect_var_names(sys.modules[mod_name], registry)
                continue
            module = _exec_fresh_module(mod_name, path, package=pkg_name)
            _collect_var_names(module, registry)
    finally:
        sys.dont_write_bytecode = dont_write_bytecode
        _active = None
        _active_ids_cfg = None
        _active_trainer_index = None
        _active_group_ids = None
        _active_shapeshift_index = None
        _active_creature_rows = None
        _active_creature_columns = None
        _active_creature_defaults = None
        # Remove every module this call put in sys.modules - not just the ones our own loop
        # inserted directly, but also any sibling pulled in by another file's own relative
        # import (that insertion happens inside `exec`, via Python's normal import machinery,
        # not through a line of ours we could have tracked in a list) - a prefix sweep catches
        # both uniformly, and is safe because `pkg_name` is fresh-per-call (see docstring).
        for name in [n for n in sys.modules if n == pkg_name or n.startswith(pkg_name + ".")]:
            sys.modules.pop(name, None)
    return registry


def load_classes_dir(
    dir_path: Path, ids_cfg: dict | None = None, trainer_index=None,
    existing_group_ids: set[int] | None = None, shapeshift_index: dict | None = None,
    existing_creature_rows: dict[int, dict] | None = None, creature_columns: tuple[str, ...] | None = None,
    creature_defaults: dict[str, object] | None = None,
) -> dict[str, list[dict]]:
    """Merge every `source/classes/*` entry's registered spells/talents/
    tabs/skill_line_abilities/trainer_spells into one dict, in sorted-name
    order - same shape and merge-order convention as
    `lib.source.load_spells_csv`/`load_talents_yaml`, so `generate.py` can
    concatenate this output with theirs. A missing directory (no class has
    been migrated to the DSL yet) returns all-empty lists rather than
    erroring - this is a dual-support transition, not a hard requirement
    that the directory exist.

    Each entry is either a single `<class>.py` file (loaded via
    `load_class_file` - the original, one-file-per-class layout) or a
    `<class>/` subdirectory (loaded via `load_class_package` - the
    multi-file layout, one class split across several files). Both are
    supported side by side so a class can be split into a directory whenever
    that's next worth doing, same incremental-migration philosophy as the
    plan's Phase 4/5. Entries whose name starts with `_` are skipped
    (reserved for future shared helpers/examples, not class declarations -
    `Registry.spells` etc. would otherwise pick them up as a fifth
    "class").

    `ids_cfg`/`trainer_index`/`existing_group_ids`/`shapeshift_index`/
    `existing_creature_rows`/`creature_columns`/`creature_defaults` are passed
    straight through to every `load_class_file`/`load_class_package`
    call - see their docstrings."""
    merged: dict[str, list[dict]] = {key: [] for key in MERGE_KEYS}
    # P2b: {id: var_name}, merged across every class - see _collect_var_names(). Not part of
    # MERGE_KEYS (dicts, not lists); ids are already unique by construction (DuplicateIdError
    # would have fired on the matching spells/creature_templates entry first).
    merged["spell_var_names"] = {}
    merged["creature_var_names"] = {}
    if not dir_path.is_dir():
        return merged
    seen: dict[str, dict[object, str]] = {key: {} for key in MERGE_KEYS}
    entries = [p for p in dir_path.iterdir() if not p.name.startswith("_")]
    entries = [p for p in entries if p.is_dir() or p.suffix == ".py"]
    for path in sorted(entries, key=lambda p: p.name):
        kwargs = dict(
            ids_cfg=ids_cfg, trainer_index=trainer_index,
            existing_group_ids=existing_group_ids, shapeshift_index=shapeshift_index,
            existing_creature_rows=existing_creature_rows, creature_columns=creature_columns,
            creature_defaults=creature_defaults,
        )
        if path.is_dir():
            registry = load_class_package(path, **kwargs)
        else:
            registry = load_class_file(path, **kwargs)
        class_name = path.stem  # "warlock" for warlock.py or the warlock/ package directory
        for key in MERGE_KEYS:
            for entry in getattr(registry, key):
                # `_dedup_id` is the escape hatch for a table whose real SQL column is itself
                # called `id` (spell_group/spell_group's own leave_ counterpart) - see
                # spell_group()'s docstring for why entry["id"] can't double as the dedup key
                # there the way it does for every other table.
                dedup_id = entry.get("_dedup_id", entry.get("id"))
                if dedup_id in seen[key]:
                    raise DuplicateIdError(
                        f"{key} entry {dedup_id!r} appears in both "
                        f"{seen[key][dedup_id]!r} and {path.name!r}"
                    )
                seen[key][dedup_id] = path.name
                # Bookkeeping only (never a real column) - lib.potency_sheet groups the generated
                # docs/potency/<class>.md sheet by this. Harmless for every other consumer: SQL
                # emission only ever reads the columns a TableSpec/build_*_row names explicitly.
                entry.setdefault("_source_class", class_name)
                merged[key].append(entry)
        merged["spell_var_names"].update(registry.spell_var_names)
        merged["creature_var_names"].update(registry.creature_var_names)
    return merged
