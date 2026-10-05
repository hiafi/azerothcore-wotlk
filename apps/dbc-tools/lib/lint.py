"""
Sanity checks run over freshly-built spell rows before they're written out.

It's its own module (rather than living in generate.py or build.py) because
these are *content* sanity checks on the fully built/resolved rows, not part
of building a row or deciding whether to emit it.
"""

from __future__ import annotations

from types import SimpleNamespace

from lib.dsl.constants import RANGE_SELF, RANGE_SELF_INDEX
from lib.dsl import tooltip
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

# X1 (paladin-rework SHARED B6 item 7 / CR1): custom helper spells (id >= this) that aim at anything
# but the caster must carry a real range. Ids below it are stock/pulled rows whose RangeIndex is
# whatever Blizzard shipped.
RANGE_LINT_MIN_ID = 200000

# Spell ids exempt from the X1 range lint (reviewed by hand: the spell is only ever applied through a
# path that never runs Spell::CheckRange, e.g. a hit link on the target itself). Keep a comment per id.
RANGE_LINT_ALLOW: frozenset[int] = frozenset({
    200603,  # druid Flourish helper, pre-existing and deployed, not paladin scope
})

# Targets.h: NONE and UNIT_CASTER - the only implicit targets that are "the caster and nothing else".
# Everything else counts as non-self, including the area-aura-on-caster shapes (TARGET_UNIT_CASTER_AREA_*,
# SRC_CASTER, DEST_CASTER, ...): they hit other units, and a helper declared that way is expected to
# carry the range its siblings do (SHARED CR1 gives the Aura bursts an explicit range).
_CASTER_ONLY_TARGETS = {0, 1}


def check_range_on_nonself_helpers(
    entries: list[dict], allow: frozenset[int] | set[int] | None = None,
    skip_ids: set[int] | None = None,
) -> list[str]:
    """X1: flags a custom spell (id >= RANGE_LINT_MIN_ID, not in `allow`/`skip_ids`) that builds with
    RangeIndex 0 - no `range_yards` and no non-zero raw `RangeIndex` - while any effect's implicit
    target A/B is not caster-only. Same silent failure as check_zero_range_unit_target (Spell::
    CheckRange fails OUT_OF_RANGE beyond melee, triggered casts included) but broader: it also
    covers dest and area targets, and is scoped to ids this rework mints so stock rows never nag.

    `skip_ids` lets generate.py drop ids check_zero_range_unit_target already reported, so one
    spell never prints two near-identical warnings. Give the spell `range_yards=50000.0` ("Anywhere",
    for a script-cast helper), a real range, `range_yards=RANGE_SELF`, or add it to RANGE_LINT_ALLOW."""
    allowed = RANGE_LINT_ALLOW if allow is None else allow
    skipped = skip_ids or set()
    warnings: list[str] = []
    for entry in entries:
        spell_id = entry["id"]
        if spell_id < RANGE_LINT_MIN_ID or spell_id in allowed or spell_id in skipped:
            continue
        if (entry.get("notes") or "").strip() == "pulled from existing data":
            continue
        raw_index = (entry.get("raw_overrides") or {}).get("RangeIndex")
        if entry.get("range_yards") or raw_index:
            continue
        hits = sorted({
            effect[key]
            for i in (1, 2, 3)
            if (effect := entry.get(f"effect{i}")) and effect.get("type")
            for key in ("implicit_target_a", "implicit_target_b")
            if effect.get(key) not in _CASTER_ONLY_TARGETS and effect.get(key) is not None
        })
        if not hits:
            continue
        warnings.append(
            f"spell {spell_id} ({entry.get('name', '?')}): RangeIndex 0 but an effect targets something "
            f"other than the caster (implicit target {hits}) - Spell::CheckRange fails it OUT_OF_RANGE "
            f"beyond melee, triggered casts included. Set range_yards (50000.0 = Anywhere for a "
            f"script-cast helper), range_yards=RANGE_SELF, or add the id to lint.RANGE_LINT_ALLOW."
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


_NO_TOOLTIP_VARS = (0, 4294967295, -1)  # stock uses both 0 and -1 for "no entry"
_TOOLTIP_TEXT_KEYS = ("Description_Lang_enUS", "AuraDescription_Lang_enUS")


def check_tooltip_vars(
    spell_entries: list[dict], declared: list[dict], stock_entries: dict[int, str] | None,
    known_spell_ids: set[int],
) -> tuple[list[str], list[str]]:
    """potency-system.PLAN.md P9, D12 - SpellDescriptionVariables.dbc references. Returns
    `(errors, notes)`:

    - error: tooltip text uses `$<var>` but the spell has no entry, its entry doesn't exist, or the
      entry doesn't define that variable (the client shows the literal `$<var>`)
    - error: a declared entry names a spell (`$?s<id>`, `$?a<id>`, `$<id>m1`) that is neither stock
      nor declared anywhere
    - note: spells that carry an entry their text never uses (harmless; one summary line)

    `stock_entries` is None when var/extractors/dbc/SpellDescriptionVariables.dbc isn't extracted;
    then spells pointing at stock entries are skipped rather than reported. Duplicate ids, bad
    names and `$<id>s<n>` reads are rejected earlier, at declaration (registry/tooltip.py)."""
    entries: dict[int, str] = dict(stock_entries or {})
    entries.update({e["id"]: e["Variables"] for e in declared})
    declared_ids = {e["id"] for e in declared}
    errors: list[str] = []
    unused: list[int] = []

    for entry in spell_entries:
        raw = entry.get("raw_overrides") or {}
        entry_id = int(raw.get("SpellDescriptionVariableID") or 0)
        uses = set()
        for key in _TOOLTIP_TEXT_KEYS:
            uses |= set(tooltip.VAR_REF.findall(raw.get(key) or ""))
        label = f"spell {entry['id']} ({entry.get('name', '?')})"
        if entry_id in _NO_TOOLTIP_VARS:
            if uses:
                errors.append(f"{label}: tooltip uses {_vars(uses)} but the spell has no "
                              f"SpellDescriptionVariableID - add tooltip_vars=")
            continue
        if entry_id not in entries:
            if uses and (stock_entries is not None or entry_id in declared_ids):
                errors.append(f"{label}: SpellDescriptionVariableID {entry_id} doesn't exist, but the "
                              f"tooltip uses {_vars(uses)}")
            continue
        missing = uses - tooltip.defined_names(entries[entry_id])
        if missing:
            errors.append(f"{label}: tooltip uses {_vars(missing)}, which SpellDescriptionVariables "
                          f"entry {entry_id} doesn't define")
        if not uses:
            unused.append(entry["id"])

    for e in declared:
        refs = {int(i) for i in tooltip.SPELL_CONDITION_REF.findall(e["Variables"])}
        refs |= {int(i) for i, _ in tooltip.SPELL_VALUE_REF.findall(e["Variables"])}
        for spell_id in sorted(refs - known_spell_ids):
            errors.append(f"tooltip_vars({e['id']}): references spell {spell_id}, which is neither a "
                          f"stock spell nor declared anywhere")

    notes = []
    if unused:
        notes.append(f"{len(unused)} spell(s) carry a SpellDescriptionVariableID their tooltip never "
                     f"uses (harmless): {', '.join(map(str, sorted(unused)))}")
    return errors, notes


def _vars(names: set[str]) -> str:
    return ", ".join(f"$<{n}>" for n in sorted(names))


# Client tables whose every change needs an in-game look: the client draws something global from
# them, so a bad row breaks every class, not just the spell being worked on.
_REVIEW_WHEN_SHIPPED = {
    "TalentTab": "every class's talent frame (tab order, tab backgrounds)",
}


def check_client_patch(
    shipping: dict[str, dict[int, dict]], stock: dict[str, dict[int, dict]], previous_files: set[str] | None,
) -> list[str]:
    """Warnings about what the client patch is about to carry (docs/bugs-and-fixes.md, 2026-10-02:
    one run shipped a TalentTab.dbc nobody meant to change, and it broke every talent frame).

    `shipping`: table name -> {id: row} for the custom/changed rows going into patch-Z.mpq.
    `stock`: table name -> stock rows, for the tables in _REVIEW_WHEN_SHIPPED.
    `previous_files`: file names in the last build's patch-Z.mpq, or None on a first build.

    - a table in _REVIEW_WHEN_SHIPPED is shipping: list each row and the columns it changes, so a
      spurious diff (a signedness or string-offset artifact) is obvious
    - a table is new to the patch, or has dropped out of it, compared with the last build"""
    warnings = []
    for name, rows in sorted(shipping.items()):
        if name not in _REVIEW_WHEN_SHIPPED:
            continue
        base = stock.get(name, {})
        changes = []
        for row_id, row in sorted(rows.items()):
            if row_id not in base:
                changes.append(f"{row_id} (new)")
                continue
            cols = [c for c, v in row.items() if base[row_id].get(c) != v]
            changes.append(f"{row_id} ({', '.join(f'{c}: {base[row_id].get(c)!r} -> {row[c]!r}' for c in cols)})")
        warnings.append(f"{name}.dbc ships in the client patch, which changes {_REVIEW_WHEN_SHIPPED[name]} - "
                        f"check it in-game after deploying. Rows differing from stock: {'; '.join(changes)}")
    if previous_files is not None:
        now = {f"{name}.dbc" for name in shipping}
        for added in sorted(now - previous_files):
            warnings.append(f"{added} is new in the client patch (not in the last build) - "
                            f"{len(shipping[added[:-4]])} custom/changed row(s); make sure that's intended")
        for dropped in sorted(f for f in previous_files - now if f.endswith(".dbc")):
            warnings.append(f"{dropped} was in the last client patch build and isn't in this one - clients "
                            f"fall back to stock for it")
    return warnings


def check_potency_bonus_overrides(
    potency_spells: dict[int, str], generated_bonus_ids: set[int], removed_bonus_ids: set[int],
    live_bonus_rows: dict[int, dict], pruned_bonus_ids: set[int] = frozenset(),
) -> list[str]:
    """Errors for potency spells whose coefficient never takes effect (D1, docs/bugs-and-fixes.md
    2026-10-02). A `spell_bonus_data` row always beats the DBC's `EffectBonusMultiplier_N`, and the
    generator only writes its own row when a spell has AP potency. An SP-only potency spell with a
    stock or hand-written row left live keeps scaling with that old coefficient: 28 P5-P8
    conversions shipped like this.

    `potency_spells`: id -> name for every spell with a potency effect. `generated_bonus_ids`: ids
    whose row the DSL declares (the generator's own D1 rows). `removed_bonus_ids`: ids with an
    `unbind_bonus_coefficients()`. `live_bonus_rows`: `spell_bonus_data` with every migration's
    INSERT/UPDATE/DELETE replayed (`trainer_state.load_keyed_table_rows`), so a row a later
    migration deleted doesn't count. `pruned_bonus_ids`: ids whose live row this same run's prune
    pass DELETEs (no longer declared), so the row is gone once the output is applied; rows that
    stay live are still errors."""
    errors = []
    exempt = generated_bonus_ids | removed_bonus_ids | set(pruned_bonus_ids)
    for spell_id in sorted(set(potency_spells) & set(live_bonus_rows) - exempt):
        row = live_bonus_rows[spell_id]
        errors.append(
            f"spell {spell_id} ({potency_spells[spell_id]}): a live spell_bonus_data row (direct "
            f"{row.get('direct_bonus')}, dot {row.get('dot_bonus')}) overrides its generated potency "
            f"coefficient - add unbind_bonus_coefficients(...) next to its declaration (D1)"
        )
    return errors


def check_undeclared_spell_categories(
    entries: list[dict], declared_ids: set[int], block: dict | None,
) -> list[str]:
    """Errors for a spell whose `Category` is inside `source/ids.yaml`'s `spellcategory` block but
    has no `spell_category()` declaration. Without the `spellcategory_dbc` row the server's
    `SpellInfo::GetCategory()` is 0 and the category cooldown silently never exists (Paladin T1).

    The effective Category is what `lib/build.py` writes: a raw `Category` override wins over the
    typed `category` field. Pass the *full* declared spell population (a spell the resolve pass
    drops as unchanged still needs its row). Stock categories (outside the block) are never
    checked. `block` None (no `spellcategory` block configured) checks nothing."""
    if not block:
        return []
    errors = []
    for entry in entries:
        raw = entry.get("raw_overrides") or {}
        category = int(raw.get("Category", entry.get("category", 0)) or 0)
        if block["start"] <= category <= block["end"] and category not in declared_ids:
            errors.append(
                f"spell {entry['id']} ({entry.get('name', '?')}): Category {category} is in the "
                f"spellcategory reserved block but no spell_category({category}) is declared - the "
                f"server would ignore its category cooldown (SpellInfo::GetCategory() 0)"
            )
    return errors


def build_talent_rank_chains(
    existing_talents: dict, talent_entries: list[dict]
) -> dict[int, list[int]]:
    """Spell id -> its talent rank chain (low to high), for `check_removed_proc_flags`. Existing
    Talent.dbc rows (`SpellRank_1..9`) first; DSL/YAML talent entries (`rank_spell_ids`) override,
    so post-rework ranks win."""
    chains: dict[int, list[int]] = {}
    for row in existing_talents.values():
        chain = [int(row.get(f"SpellRank_{i}") or 0) for i in range(1, 10)]
        chain = [r for r in chain if r]
        for rank_id in chain:
            chains[rank_id] = chain
    for entry in talent_entries:
        chain = [int(r) for r in (entry.get("rank_spell_ids") or [])[:9] if r]
        for rank_id in chain:
            chains[rank_id] = chain
    return chains


def check_removed_proc_flags(
    removal_ids: list[int],
    spell_rows: dict[int, dict],
    rank_chains: dict[int, list[int]] | None = None,
) -> list[str]:
    """Warnings for a `remove_spell_proc()` whose spell still has non-zero DBC `ProcTypeMask`
    (the spell_dbc column holding `ProcFlags`). Removing the `spell_proc` row alone does not
    necessarily stop the proc: `SpellMgr` builds a default row per spell id from the DBC flags
    (and an explicit row with ProcFlags 0 inherits them) - but only when the spell has a trigger
    aura AND non-zero flags. This check is conservative: it ignores the trigger-aura condition, so
    it can warn on a spell the removal alone already disables. Silent once the flags are zeroed.

    `removal_ids`: the declared ids. A negative id means the whole rank chain, so every rank is
    checked and the warning names the offending rank id. `rank_chains`: spell id -> the talent rank
    chain containing it (low to high); chains come from Talent.dbc (`SpellMgr::LoadSpellTalentRanks`),
    not spell_ranks - generate.py builds it from the DSL talent entries (post-rework ranks win),
    falling back to the existing talent rows' SpellRank_1..9. A negative id absent from it checks
    only `abs(id)`. `spell_rows`: spell_dbc rows by ID, already overlaid with this run's built
    rows. An id with no row anywhere is skipped."""
    rank_chains = rank_chains or {}
    warnings = []
    for removal_id in removal_ids:
        base = abs(int(removal_id))
        ids = list(rank_chains.get(base) or [base]) if int(removal_id) < 0 else [base]
        if base not in ids:
            ids.insert(0, base)
        for spell_id in ids:
            row = spell_rows.get(spell_id)
            if row is None:
                continue
            flags = int(row.get("ProcTypeMask", 0) or 0)
            if flags:
                warnings.append(
                    f"remove_spell_proc({removal_id}): spell {spell_id} still has DBC "
                    f"ProcTypeMask {flags} - SpellMgr will build a default spell_proc row from it "
                    f"(if the spell has a trigger aura), so the proc is NOT disabled. Zero "
                    f"ProcTypeMask (raw_overrides={{'ProcTypeMask': 0}}) on this spell "
                    f"(and every rank) if the intent is no proc."
                )
    return warnings