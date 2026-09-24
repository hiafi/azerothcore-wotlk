"""
Sanity checks run over freshly-built spell rows before they're written out.

It's its own module (rather than living in generate.py or build.py) because
these are *content* sanity checks on the fully built/resolved rows, not part
of building a row or deciding whether to emit it.
"""

from __future__ import annotations

from types import SimpleNamespace

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
# `typed field -> SQL column` for every field `build_spell_row` (lib/build.py) maps directly onto
# the row - two shapes: "direct" columns hold the same unit as the typed field (compare as-is);
# the three "indexed" columns are a lookup-DBC id, so the raw override's *index id* has to be
# resolved to its own value (via `index_tables`, the same base+overlay rows generate.py already
# loads for SpellCastTimes/SpellDuration/SpellRange) before it can be compared to the typed
# field's plain ms/yards value.
_DIRECT_FIELDS = {
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

# Mismatches this check already knows about and hasn't fixed yet. Recomputed by actually running
# this check against the real repo source (WP-T-HANDOFF.md item 4 - "recompute the full list
# yourself"), not hand-copied from the plan text: PLAN A9's own nine cast-time mismatches (the
# bug this check exists for) are *already fixed* as of this computation (2026-09-23, druid-rework
# branch) - the Balance pass's cast-time edits (PLAN §6 item 11) landed before this check did, so
# there is nothing A9-shaped left to allow-list. What's here instead are four pre-existing
# RangeIndex mismatches this check's first real run turned up - same bug shape (a raw_overrides
# column silently beating a typed field), but on `range_yards`/`RangeIndex`, not `cast_time_ms`/
# `CastingTimeIndex`, and in the Mage Arcane/Fire rework, not this one. Out of scope for WP-T/the
# druid rework to fix (PLAN §5.0 item 4: "the other classes' mismatches are flagged, not fixed, by
# this rework") - allow-listed so `generate.py` stays clean today; a future Mage pass removes
# these as it fixes them. {(spell_id, column): reason}.
RAW_OVERRIDE_MISMATCH_ALLOWLIST: dict[tuple[int, str], str] = {
    (200079, "RangeIndex"): "Arcane Overload shell - raw_overrides RangeIndex=6 (100yd) vs range_yards=30.0; Mage Arcane rework leftover, found 2026-09-23",
    (200092, "RangeIndex"): "Arcane Overload's own damage sub-spell (200079's trigger target) - same mismatch as 200079",
    (200116, "RangeIndex"): "Burnout explosion (Fire Mage capstone) - raw_overrides RangeIndex=1 (0yd) vs range_yards=50000.0; leftover, found 2026-09-23",
    (200119, "RangeIndex"): "Flashpoint detonation (Fire Mage capstone, a separate spell from 200116 with the same copy-pasted raw_overrides template) - same mismatch shape as 200116",
}


def check_raw_override_typed_mismatch(
    entries: list[dict], index_tables: dict[str, dict[int, dict]],
) -> list[str]:
    """Flags a spell whose `raw_overrides` sets a column that one of its own typed fields also
    sets, where the two *values* disagree (never the index ids themselves - `CastingTimeIndex`
    16 and 30004 are both 1500 ms, and that's not a bug). `index_tables` is
    `{"spellcasttimes": {ID: row}, "spellduration": {...}, "spellrange": {...}}` - generate.py's
    own `existing_secondary_by_id`, reused rather than re-loaded so this sees the same base+
    overlay state everything else in a run does.

    A typed field left at its default (falsy) is exempt - it isn't really asking for anything, so
    a raw override alongside it isn't a disagreement, just an unmodeled column. Same "pulled from
    existing data" exemption as `check_classmask_scoping`/`check_missing_skill_line_ability`
    (those bytes are copied verbatim from the real client DBC, not hand-typed)."""
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
        for field, column in _DIRECT_FIELDS.items():
            if column not in overrides or (spell_id, column) in RAW_OVERRIDE_MISMATCH_ALLOWLIST:
                continue
            typed_value = entry.get(field) or 0
            if not typed_value or typed_value == overrides[column]:
                continue
            warnings.append(
                f"spell {spell_id} ({name}): raw_overrides sets {column}={overrides[column]!r}, "
                f"but the typed field {field}={typed_value!r} also sets it and lib/build.py "
                f"applies raw_overrides last, so {overrides[column]!r} silently wins - see PLAN "
                f"A9. Drop the raw_overrides entry, or change {field} to match."
            )
        for field, (column, table_name, value_col) in _INDEXED_FIELDS.items():
            if column not in overrides or (spell_id, column) in RAW_OVERRIDE_MISMATCH_ALLOWLIST:
                continue
            typed_value = entry.get(field) or 0
            if not typed_value:
                continue
            index_row = index_tables.get(table_name, {}).get(overrides[column])
            if index_row is None:
                continue  # raw index doesn't resolve to anything live - not this check's job
            resolved_value = index_row.get(value_col)
            if resolved_value == typed_value:
                continue
            warnings.append(
                f"spell {spell_id} ({name}): raw_overrides sets {column}={overrides[column]} "
                f"(resolves to {value_col}={resolved_value!r}), but the typed field "
                f"{field}={typed_value!r} also sets it and lib/build.py applies raw_overrides "
                f"last, so {resolved_value!r} silently wins - see PLAN A9. Drop the "
                f"raw_overrides entry, or change {field} to match."
            )
    return warnings
