"""
Sanity checks run over freshly-built spell rows before they're written out.

It's its own module (rather than living in generate.py or build.py) because
these are *content* sanity checks on the fully built/resolved rows, not part
of building a row or deciding whether to emit it.
"""

from __future__ import annotations

from types import SimpleNamespace

from lib.dsl.constants import RANGE_SELF, RANGE_SELF_INDEX
from lib.dsl.registry import looks_player_castable

# SpellModOp values (SpellDefines.h) that only ever make sense scoped to
# specific spells via a classmask - i.e. finding one of these with an
# all-zero classmask on the effect it lives on is a strong signal of the
# EffectSpellClassMask{A,B,C}_{1,2,3} letter/number mixup (see
# docs/dbc-build-pipeline.md "Bug 3"), not a deliberate "applies broadly"
# design choice the way e.g. SPELLMOD_DAMAGE (0) or SPELLMOD_ALL_EFFECTS (8)
# can legitimately be.
_SCOPE_REQUIRED_OPS = {
    1,   # SPELLMOD_DURATION
    3,   # SPELLMOD_EFFECT1
    5,   # SPELLMOD_RANGE
    6,   # SPELLMOD_RADIUS
    10,  # SPELLMOD_CASTING_TIME
    11,  # SPELLMOD_COOLDOWN
    12,  # SPELLMOD_EFFECT2
    17,  # SPELLMOD_JUMP_TARGETS
    20,  # SPELLMOD_DAMAGE_MULTIPLIER
    22,  # SPELLMOD_DOT
    23,  # SPELLMOD_EFFECT3
    27,  # SPELLMOD_VALUE_MULTIPLIER
}
_SPELLMOD_AURAS = {107, 108}  # SPELL_AURA_ADD_FLAT_MODIFIER, SPELL_AURA_ADD_PCT_MODIFIER
_LETTERS = ("A", "B", "C")


def check_classmask_scoping(entries: list[dict], rows: list[dict]) -> list[str]:
    """Flags any hand-authored (non-"pulled from existing data") row where a
    SpellMod effect that needs a classmask to be meaningfully scoped ends up
    with an all-zero one for the effect it actually lives on - almost always
    caused by writing the override under the wrong letter (see
    apps/dbc-tools/README.md's "Gotcha" callout for the letter/number rule).
    Untouched pulled data is exempt: those bytes are copied verbatim from the
    real client DBC, correct by construction regardless of what a human
    comment on the row claims.
    """
    warnings: list[str] = []
    for entry, row in zip(entries, rows):
        notes = entry.get("notes") or ""
        if notes.strip() == "pulled from existing data":
            continue
        # NOTE (2026-09-09): letter = effect index (A=Effect_1, B=Effect_2, C=Effect_3), number =
        # which of that effect's 3 SpellFamilyFlags dwords - see apps/dbc-tools/README.md's
        # "Gotcha" callout. So `masks[i]` below (i indexed 0/1/2 against _LETTERS "A"/"B"/"C") is
        # already "effect i's 3 dwords" - do NOT transpose this to index by number instead; that
        # was tried and briefly shipped as a "fix" here, but it's actually the same mixup mirrored
        # onto the other axis (checked "is *any* effect's dword N scoped" instead of "is *this*
        # effect scoped at all"), which misdiagnosed several already-correct rows (Arcane
        # Shielding, Magic Attunement, Firestarter, Burning Determination) as bugs. See
        # docs/bugs-and-fixes.md for the incident.
        masks = [
            tuple(row.get(f"EffectSpellClassMask{letter}_{n}", 0) or 0 for n in (1, 2, 3))
            for letter in _LETTERS
        ]
        if not any(any(word) for word in masks):
            continue  # nothing on this row is scoped at all - not this bug
        for i in range(3):
            aura = row.get(f"EffectAura_{i + 1}", 0)
            misc = row.get(f"EffectMiscValue_{i + 1}", 0)
            if aura in _SPELLMOD_AURAS and misc in _SCOPE_REQUIRED_OPS and not any(masks[i]):
                warnings.append(
                    f"spell {row['ID']} ({entry.get('name', '?')}): effect {i + 1}'s "
                    f"SpellMod (EffectAura_{i + 1}={aura}, EffectMiscValue_{i + 1}={misc}) has an "
                    f"all-zero classmask (letter {_LETTERS[i]}: {masks[i]}) even though this row "
                    f"sets a classmask elsewhere ({masks}) - probably "
                    f"EffectSpellClassMask{_LETTERS[i]}_* needs the value that's on a different "
                    f"letter. All-zero here means the engine applies it to every matching spell in "
                    f"the family, not just the intended one."
                )
    return warnings


def check_missing_skill_line_ability(
    entries: list[dict],
    skill_line_ability_entries: list[dict],
    existing_skill_line_ability_rows: dict[int, dict],
    ids_cfg: dict,
) -> list[str]:
    """Flags a fully-custom, player-castable spell ID with no `SkillLineAbility`
    coverage at all - the gap that makes a client silently drop it, rather
    than just misfile it, from any UI that buckets spells by skill line
    (Spellbook *and*, per the Meteor incident below, the Trainer window too).

    `granted_by_talent()` already guards against this for talent ranks (see
    `MissingSkillLineAbilityError`), but that check only ever sees spells
    passed through `ranks=`. A baseline spell declared with a bare `spell()`
    call and taught via `trained_by()` - Meteor being the first real example
    - goes through neither, so nothing caught it until a live playtest report
    (`docs/bugs-and-fixes.md`'s "New custom spell IDs granted by a talent
    show up in the Spellbook's 'General' tab instead of the class's own tab"
    - that entry describes the Spellbook-tab symptom; Meteor showed the same
    root cause can make the Trainer window drop the entry outright, confirmed
    via server-side packet logging: the row was correctly sent as
    `Usable=Available`, the client just never rendered it). This check closes
    that gap at generation time instead of needing another live incident to
    catch the next one.

    Reuses `looks_player_castable` (the exact heuristic `granted_by_talent()`
    already relies on) via a `SimpleNamespace` shim, so there's one
    castable/trigger-only rule for the whole pipeline, not two to keep in
    sync. Already-covered spells (either freshly declared elsewhere in this
    run, or already live from a prior run/Blizzard's own data) are exempt;
    reused stock IDs are exempt outright - Blizzard's own data covers them if
    they need it."""
    covered = {e["spell_id"] for e in skill_line_ability_entries}
    covered |= {row.get("Spell") for row in existing_skill_line_ability_rows.values()}
    spell_range = ids_cfg["spell"]

    warnings: list[str] = []
    for entry in entries:
        notes = entry.get("notes") or ""
        if notes.strip() == "pulled from existing data":
            continue
        spell_id = entry["id"]
        if not (spell_range["start"] <= spell_id <= spell_range["end"]):
            continue  # reused stock ID - Blizzard's own data already covers it if it needs it
        if spell_id in covered:
            continue
        if not looks_player_castable(SimpleNamespace(**entry)):
            continue
        warnings.append(
            f"spell {spell_id} ({entry.get('name', '?')}): looks player-castable (a real "
            f"cast_time_ms/cooldown_ms/category_cooldown_ms/mana_cost and not marked passive) "
            f"but has no SkillLineAbility row anywhere - it'll silently drop out of (or misfile "
            f"in) any client UI that buckets spells by skill line, including the Spellbook and "
            f"the Trainer window. If a player can actually learn/cast this, add a row via "
            f"skill_line_ability(id=<next from ids.yaml's skilllineability block>, "
            f"skill_line=<class's line>, spell_id={spell_id}, class_mask=<class mask>). If it's "
            f"really only ever granted as a hidden triggered effect (never learned or cast "
            f"directly by a player), this is a false positive - `looks_player_castable`'s "
            f"heuristic isn't proof, see its docstring."
        )
    return warnings


# PLAN A9 (.agents/plans/druid-rework/druid-rework.PLAN.md): `lib/build.py` applies a row's
# `raw_overrides` *last*, so a raw column silently beats a typed field that also sets it. This
# already shipped wrong cast times on nine spells (the DSL said `cast_time_ms=2000`, but a raw
# `CastingTimeIndex` copied from an old rank-1 pull won).
#
# `typed field -> SQL column` for every top-level field `build_spell_row` (lib/build.py) maps
# directly onto the row - two shapes: "direct" columns hold the same unit as the typed field
# (compare as-is); the indexed columns (cast time/duration/range) are a lookup-DBC id, so the raw
# override's *index id* has to be resolved to its own value (via `index_tables`, the same
# base+overlay rows generate.py already loads for SpellCastTimes/SpellDuration/SpellRange) before
# it can be compared to the typed field's plain ms/yards value. `Name_Lang_enUS` is direct too -
# `name` is the one non-numeric typed field build_spell_row sets.
_DIRECT_FIELDS = {
    "name": "Name_Lang_enUS",
    "school": "SchoolMask",
    "dispel": "DispelType",
    "mechanic": "Mechanic",
    "attributes": "Attributes",
    "category": "Category",
    "cooldown_ms": "RecoveryTime",
    "category_cooldown_ms": "CategoryRecoveryTime",
    "power_type": "PowerType",
    "mana_cost": "ManaCost",
    "mana_cost_pct": "ManaCostPct",
    "spell_icon_id": "SpellIconID",
}
# typed_field -> (SQL column, index_tables key, the index row's own value column)
_INDEXED_FIELDS = {
    "cast_time_ms": ("CastingTimeIndex", "spellcasttimes", "Base"),
    "duration_ms": ("DurationIndex", "spellduration", "Duration"),
    "range_yards": ("RangeIndex", "spellrange", "RangeMax_1"),
}

# Same two shapes, one per effect slot (1/2/3) - build_spell_row's `for i in range(1, 4)` loop,
# lib/build.py. `die_sides` is the one field whose *unset* default isn't 0 (dbcfile.empty_row
# gives every int column 0, but build_spell_row explicitly does `effect.get("die_sides", 1)`) -
# see `_effect_typed_value`'s handling below.
_EFFECT_DIRECT_FIELDS = {
    "type": "Effect",
    "base_points": "EffectBasePoints",
    "points_per_level": "EffectRealPointsPerLevel",
    "die_sides": "EffectDieSides",
    "mechanic": "EffectMechanic",
    "implicit_target_a": "ImplicitTargetA",
    "implicit_target_b": "ImplicitTargetB",
    "apply_aura": "EffectAura",
    "amplitude": "EffectAuraPeriod",
    "misc_value": "EffectMiscValue",
    "trigger_spell": "EffectTriggerSpell",
    "chain_targets": "EffectChainTargets",
}
_EFFECT_FIELD_DEFAULTS = {"die_sides": 1}

# Mismatches this check already knows about and hasn't fixed yet. Recomputed by actually running
# this check against the real repo source (WP-T-HANDOFF.md item 4 - "recompute the full list
# yourself"), not hand-copied from the plan text, and against the *full* declared-spell population
# (every entry `source.load_spells_csv`/the DSL classes produce), not just what a given run's own
# `resolve.resolve_rows` happens to rebuild - a spell whose raw override already matches what's
# live gets silently excluded from `resolve_rows`'s output (it reads as an "unchanged reference
# copy"), which hid the real, still-live PLAN A9 mismatches from this check's first version (a
# real regression this allow-list's history is worth keeping: it originally, wrongly, claimed
# these nine were "already fixed"). PLAN A9's nine `CastingTimeIndex` entries (Wrath, Healing
# Touch, Smite, Lesser Heal, Healing Wave, Lightning Bolt, Shadow Bolt, Firebolt, Frostfire Bolt)
# are gone from this list as of the druid-rework Balance pass's code review fixes (2026-09-24) -
# every one of those, plus Starfire/Regrowth/Greater Heal (which this allow-list never covered),
# now has cast_time_ms and its raw CastingTimeIndex agreeing, so there's nothing left to hide.
# {(spell_id, column): reason}.
RAW_OVERRIDE_MISMATCH_ALLOWLIST: dict[tuple[int, str], str] = {
    (200079, "RangeIndex"): (
        "Arcane Overload shell - raw_overrides RangeIndex=6 (100yd) vs range_yards=30.0; "
        "Mage Arcane rework leftover, found 2026-09-23"
    ),
    (200092, "RangeIndex"): (
        "Arcane Overload's own damage sub-spell (200079's trigger target) - same mismatch as 200079"
    ),
    (200116, "RangeIndex"): (
        "Burnout explosion (Fire Mage capstone) - raw_overrides RangeIndex=1 (0yd) vs "
        "range_yards=50000.0; leftover, found 2026-09-23"
    ),
    (200119, "RangeIndex"): (
        "Flashpoint detonation (Fire Mage capstone, a separate spell from 200116 with the same "
        "copy-pasted raw_overrides template) - same mismatch shape as 200116"
    ),
    (50227, "EffectBasePoints_2"): (
        "Sword and Board (source/spells/npc.csv, not yet DSL-migrated) - Protection Warrior "
        "rework phase 2 gave effect2 real base_points=9 (\"Effect_2 was vestigial-empty\", per "
        "its own note) but left the old raw_overrides EffectBasePoints_2=-1 from before that "
        "behind; first found by this check's effect-level extension, 2026-09-23 - out of scope "
        "for WP-T/the druid rework to fix"
    ),
}


def _mismatch_warning(spell_id, name, column, raw_repr, field, typed_value) -> str:
    return (
        f"spell {spell_id} ({name}): raw_overrides sets {column}={raw_repr}, but the typed "
        f"field {field}={typed_value!r} also sets it and lib/build.py applies raw_overrides "
        f"last, so {raw_repr} silently wins - see PLAN A9. Drop the raw_overrides entry, or "
        f"change {field} to match."
    )


def check_raw_override_typed_mismatch(
    entries: list[dict], index_tables: dict[str, dict[int, dict]],
) -> list[str]:
    """Flags a spell whose `raw_overrides` sets a column that one of its own typed fields also
    sets (top-level or per-effect), where the two *values* disagree (never the index ids
    themselves - `CastingTimeIndex` 16 and 30004 are both 1500 ms, and that's not a bug).
    `index_tables` is `{"spellcasttimes": {ID: row}, "spellduration": {...}, "spellrange": {...},
    "spellradius": {...}}` - generate.py's own `existing_secondary_by_id`, reused rather than
    re-loaded so this sees the same base+overlay state everything else in a run does.

    `entries` must be the *full* declared population (every spell source declares, not just what
    a particular run's `resolve.resolve_rows` rebuilds this time) - see
    `RAW_OVERRIDE_MISMATCH_ALLOWLIST`'s docstring for why a narrower population silently hides
    real, still-live mismatches.

    A typed field left at its default (falsy - or `die_sides`'s own non-zero unset default, 1) is
    exempt - it isn't really asking for anything, so a raw override alongside it isn't a
    disagreement, just an unmodeled column. Same "pulled from existing data" exemption as
    `check_classmask_scoping`/`check_missing_skill_line_ability` (those bytes are copied verbatim
    from the real client DBC, not hand-typed)."""
    warnings: list[str] = []
    for entry in entries:
        notes = entry.get("notes") or ""
        if notes.strip() == "pulled from existing data":
            continue
        overrides = entry.get("raw_overrides") or {}
        if not overrides:
            continue
        spell_id = entry["id"]
        name = entry.get("name", "?")

        def allowed(column: str) -> bool:
            return (spell_id, column) in RAW_OVERRIDE_MISMATCH_ALLOWLIST

        for field, column in _DIRECT_FIELDS.items():
            if column not in overrides or allowed(column):
                continue
            typed_value = entry.get(field) or (0 if field != "name" else "")
            if not typed_value or typed_value == overrides[column]:
                continue
            warnings.append(_mismatch_warning(spell_id, name, column, repr(overrides[column]), field, typed_value))
        for field, (column, table_name, value_col) in _INDEXED_FIELDS.items():
            if column not in overrides or allowed(column):
                continue
            typed_value = entry.get(field) or 0
            if not typed_value:
                continue
            if typed_value == RANGE_SELF:
                if overrides[column] != RANGE_SELF_INDEX:
                    warnings.append(_mismatch_warning(
                        spell_id, name, column, repr(overrides[column]), field, typed_value,
                    ))
                continue
            index_row = index_tables.get(table_name, {}).get(overrides[column])
            if index_row is None:
                continue  # raw index doesn't resolve to anything live - not this check's job
            resolved_value = index_row.get(value_col)
            if resolved_value == typed_value:
                continue
            warnings.append(_mismatch_warning(
                spell_id, name, column, f"{overrides[column]} (resolves to {value_col}={resolved_value!r})",
                field, typed_value,
            ))

        for i in (1, 2, 3):
            effect = entry.get(f"effect{i}") or {}
            for field, base_column in _EFFECT_DIRECT_FIELDS.items():
                column = f"{base_column}_{i}"
                if column not in overrides or allowed(column):
                    continue
                typed_value = effect.get(field, _EFFECT_FIELD_DEFAULTS.get(field, 0))
                if not typed_value or typed_value == overrides[column]:
                    continue
                warnings.append(_mismatch_warning(
                    spell_id, name, column, repr(overrides[column]), f"effect{i}.{field}", typed_value,
                ))
            radius_column = f"EffectRadiusIndex_{i}"
            if radius_column in overrides and not allowed(radius_column):
                # build_spell_row's own fallback: an effect with no radius_yards of its own uses
                # the entry-level default_radius (entry["radius_yards"]) instead.
                typed_value = effect.get("radius_yards", entry.get("radius_yards")) or 0
                if typed_value:
                    index_row = index_tables.get("spellradius", {}).get(overrides[radius_column])
                    if index_row is not None:
                        resolved_value = index_row.get("Radius")
                        if resolved_value != typed_value:
                            warnings.append(_mismatch_warning(
                                spell_id, name, radius_column,
                                f"{overrides[radius_column]} (resolves to Radius={resolved_value!r})",
                                f"effect{i}.radius_yards", typed_value,
                            ))
    return warnings



# Targets.h/SharedDefines.h `Targets` values that aim at the cast's explicit unit target (or a
# destination taken from it) - i.e. the ones where Spell::CheckRange measures caster -> some
# *other* unit. Channel targets (76/77) are left out: they're whatever the channel already hit.
_EXPLICIT_UNIT_TARGETS = {
    6,   # TARGET_UNIT_TARGET_ENEMY
    21,  # TARGET_UNIT_TARGET_ALLY
    25,  # TARGET_UNIT_TARGET_ANY
    35,  # TARGET_UNIT_TARGET_PARTY
    45,  # TARGET_UNIT_TARGET_CHAINHEAL_ALLY
    53,  # TARGET_DEST_TARGET_ENEMY
    57,  # TARGET_UNIT_TARGET_RAID
    61,  # TARGET_UNIT_TARGET_AREA_RAID_CLASS
    63, 64, 65, 66, 67, 68, 69, 70, 71,  # TARGET_DEST_TARGET_ANY / _FRONT ... _FRONT_LEFT
    74,  # TARGET_DEST_TARGET_RANDOM
    75,  # TARGET_DEST_TARGET_RADIUS
    90,  # TARGET_UNIT_TARGET_MINIPET
    95,  # TARGET_UNIT_TARGET_PASSENGER
}


def check_zero_range_unit_target(entries: list[dict]) -> list[str]:
    """Flags a spell that builds with RangeIndex 0 (`range_yards` 0/unset and no raw
    `RangeIndex` override) while one of its effects targets another unit. RangeIndex 0 means no
    SpellRange row, so `GetSpellMaxRangeForTarget` returns 0 and `Spell::CheckRange` - which runs
    for triggered casts too, `TRIGGERED_FULL_MASK` doesn't skip it - fails OUT_OF_RANGE unless
    the target is in melee contact. No log line, the spell just never lands (Fury of Elune,
    Starfire cleave, Swarming Rot, Brambles silence, Halo healing-taken - docs/bugs-and-fixes.md).

    Give it a real range (`range_yards=50000.0` "Anywhere" for a script-cast trigger), or mark a
    genuine no-range spell with `range_yards=RANGE_SELF` (SpellRange 1, which CheckRange skips) or an
    explicit raw `RangeIndex`. Self-only spells (every effect on the caster) are exempt - the
    range check never runs against the caster itself.

    Like check_raw_override_typed_mismatch, pass the *full* declared population, not
    spell_resolved.entries - an unchanged, still-live broken row would otherwise never be seen."""
    warnings: list[str] = []
    for entry in entries:
        notes = entry.get("notes") or ""
        if notes.strip() == "pulled from existing data":
            continue
        if entry.get("range_yards") or "RangeIndex" in (entry.get("raw_overrides") or {}):
            continue
        targets = {
            effect.get(key)
            for i in (1, 2, 3)
            if (effect := entry.get(f"effect{i}"))
            for key in ("implicit_target_a", "implicit_target_b")
        }
        hits = sorted(targets & _EXPLICIT_UNIT_TARGETS)
        if not hits:
            continue
        warnings.append(
            f"spell {entry['id']} ({entry.get('name', '?')}): range_yards is 0/unset (RangeIndex "
            f"0 = 0 yd max range) but an effect targets another unit (implicit target {hits}), "
            f"so Spell::CheckRange fails it OUT_OF_RANGE beyond melee contact - triggered casts "
            f"included. Set a real range_yards (50000.0 = Anywhere for a script-cast trigger), "
            f"or range_yards=RANGE_SELF if it really has no range."
        )
    return warnings

# SpellMgr.h/.cpp's SpellMgr::LoadSpellLinked, verified against the real source (review,
# 2026-09-23 - see lib/dsl/registry.py's comment above _SPELL_LINKED_MAX_SPELLS for the full
# semantics this mirrors): the map key for a `(spell_trigger, type)` pair is `spell_trigger`
# unshifted for type 0, or `spell_trigger ± SPELL_LINKED_MAX_SPELLS*type` (added if positive,
# subtracted if negative) for type 1/2. `source/ids.yaml`'s whole custom-spell block (200000-
# 209999) sits exactly inside that offset window, so a `type=0` trigger in that range can collide
# with a `type=1`/`type=2` row declared (or already stock) at `trigger - 200000`/`trigger -
# 400000` - two unrelated declarations that the engine reads as the *same* row.
_SPELL_LINKED_MAX_SPELLS = 200000


def _spell_linked_engine_key(trigger: int, type_: int) -> int:
    if type_ == 0:
        return trigger
    offset = _SPELL_LINKED_MAX_SPELLS * type_
    return trigger + offset if trigger > 0 else trigger - offset


# T1 (.agents/plans/warlock-rework/warlock-rework.T1-HANDOFF.md): creature_template/
# creature_template_model lints.

# UnitDefines.h CREATURE_FLAG_EXTRA_TRIGGER - forces UNIT_FIELD_DISPLAYID to the invisible model
# for every non-GM observer (Unit::BuildValuesUpdateForPlayerWithFlag), silently hiding whatever
# creature_template_model actually declares. Shipped once - see docs/bugs-and-fixes.md's
# CREATURE_FLAG_EXTRA_TRIGGER entry (Tentacle of Madness's first draft).
CREATURE_FLAG_EXTRA_TRIGGER = 0x80


def check_creature_trigger_flag_with_model(
    creature_templates: list[dict], has_model: set[int],
) -> list[str]:
    """Flags a declared `creature_template` whose `flags_extra` includes
    `CREATURE_FLAG_EXTRA_TRIGGER` while it also has a model (declared this run or already live) -
    the combination that made Tentacle of Madness's real model invisible to every non-GM observer
    the first time it shipped (see `CREATURE_FLAG_EXTRA_TRIGGER`'s comment). `has_model` is the
    union of declared + live `creature_template_model` `CreatureID`s - see `generate.py`'s wiring."""
    warnings: list[str] = []
    for row in creature_templates:
        entry = row["entry"]
        if entry not in has_model:
            continue
        if int(row.get("flags_extra") or 0) & CREATURE_FLAG_EXTRA_TRIGGER:
            warnings.append(
                f"creature_template {entry} ({row.get('name', '?')}): flags_extra includes "
                f"CREATURE_FLAG_EXTRA_TRIGGER (0x80) and has a creature_template_model row - "
                f"Unit::BuildValuesUpdateForPlayerWithFlag force-overrides UNIT_FIELD_DISPLAYID to "
                f"the invisible model for every non-GM observer whenever TRIGGER is set, bypassing "
                f"creature_template_model entirely (docs/bugs-and-fixes.md's "
                f"CREATURE_FLAG_EXTRA_TRIGGER entry)."
            )
    return warnings


def check_creature_model_display_id(
    creature_models: list[dict], known_display_ids: set[int],
) -> list[str]:
    """Flags a declared `creature_template_model` row whose `CreatureDisplayID` has no
    `creature_model_info` row anywhere (base dump or migrations - `known_display_ids`, see
    `generate.py`'s wiring) - `ObjectMgr::LoadCreatureModelInfo`-derived data (bounding radius,
    combat reach) the engine expects for every display id a creature can wear."""
    warnings: list[str] = []
    for row in creature_models:
        display_id = row["CreatureDisplayID"]
        if display_id not in known_display_ids:
            warnings.append(
                f"creature_template_model: CreatureID {row['CreatureID']} declares "
                f"CreatureDisplayID {display_id}, which has no creature_model_info row in the "
                f"base dump or migrations - the model may render with a wrong bounding "
                f"radius/combat reach, or fail to load."
            )
    return warnings


def check_creature_without_model(
    creature_templates: list[dict], has_model: set[int],
) -> list[str]:
    """Flags a declared `creature_template` entry with no `creature_template_model` row anywhere
    (declared this run or already live - `has_model`, see `generate.py`'s wiring) -
    `ObjectMgr::CheckCreatureTemplate` logs "does not have any existing display id" for exactly
    this and the creature has no visible model at all."""
    warnings: list[str] = []
    for row in creature_templates:
        entry = row["entry"]
        if entry not in has_model:
            warnings.append(
                f"creature_template {entry} ({row.get('name', '?')}): no creature_template_model "
                f"row anywhere (declared or live) - ObjectMgr::CheckCreatureTemplate logs 'does "
                f"not have any existing display id' and the creature has no visible model."
            )
    return warnings


def check_linked_spell_key_collisions(rows: list[dict]) -> list[str]:
    """Flags any two `spell_linked_spell` rows (declared this run, live/stock, or a mix - `rows`
    is whatever the caller wants checked together, see `generate.py`'s wiring for "declared +
    everything already live") whose `(spell_trigger, type)` encode to the *same*
    `SpellMgr::LoadSpellLinked` map key - see `_spell_linked_engine_key`. At runtime, the engine
    only ever sees the last-loaded row for that key; the other row's effects fire in the wrong
    place entirely (e.g. a `type=0` trigger of `785` colliding with the stock `type=1` row for
    `585` - Smite - means Smite's on-hit effects fire whenever spell `200585` is cast, and vice
    versa)."""
    by_key: dict[int, set[tuple[int, int]]] = {}
    for row in rows:
        trigger, type_ = row["spell_trigger"], row["type"]
        key = _spell_linked_engine_key(trigger, type_)
        by_key.setdefault(key, set()).add((trigger, type_))
    warnings: list[str] = []
    for key, pairs in by_key.items():
        if len(pairs) < 2:
            continue
        desc = ", ".join(f"(trigger={t}, type={ty})" for t, ty in sorted(pairs))
        warnings.append(
            f"spell_linked_spell: {desc} all encode to the same SpellMgr::LoadSpellLinked lookup "
            f"key ({key}) - trigger ± {_SPELL_LINKED_MAX_SPELLS}*type - so these rows collide at "
            f"runtime; only one is ever seen for that key. A type=0 trigger inside "
            f"source/ids.yaml's custom spell block (200000-209999) is the usual cause."
        )
    return warnings
