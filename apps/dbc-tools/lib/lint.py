"""
Sanity checks run over freshly-built spell rows before they're written out.

It's its own module (rather than living in generate.py or build.py) because
these are *content* sanity checks on the fully built/resolved rows, not part
of building a row or deciding whether to emit it.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

from lib.dsl.constants import RANGE_SELF, RANGE_SELF_INDEX
from lib.dsl import tooltip
from lib.dsl.registry import looks_player_castable

# SpellModOp values (SpellDefines.h) that only ever make sense scoped to
# specific spells via a classmask - i.e. finding one of these with an
# all-zero classmask on the effect it lives on is a strong signal of the
# EffectSpellClassMask{A,B,C}_{1,2,3} letter/number mixup (see
# docs/dbc-build-pipeline.md "Bug 3"), not a deliberate "applies broadly"
# design choice the way e.g. SPELLMOD_DAMAGE (0) can legitimately be.
# SPELLMOD_ALL_EFFECTS (8) used to be left out on the same "can be broad"
# reasoning; that is how Magic Absorption's Mana Gem clause shipped as a
# +45% to every effect of every Mage spell (2026-10-06). 7/8/14/15/19/21/24
# were added together then: none of them produced a warning on the source
# of that day once the two real bugs (Magic Absorption, Improved Blizzard)
# were fixed.
_SCOPE_REQUIRED_OPS = {
    1,   # SPELLMOD_DURATION
    3,   # SPELLMOD_EFFECT1
    5,   # SPELLMOD_RANGE
    6,   # SPELLMOD_RADIUS
    7,   # SPELLMOD_CRITICAL_CHANCE
    8,   # SPELLMOD_ALL_EFFECTS
    10,  # SPELLMOD_CASTING_TIME
    11,  # SPELLMOD_COOLDOWN
    12,  # SPELLMOD_EFFECT2
    14,  # SPELLMOD_COST
    15,  # SPELLMOD_CRIT_DAMAGE_BONUS
    17,  # SPELLMOD_JUMP_TARGETS
    19,  # SPELLMOD_ACTIVATION_TIME
    20,  # SPELLMOD_DAMAGE_MULTIPLIER
    21,  # SPELLMOD_GLOBAL_COOLDOWN
    22,  # SPELLMOD_DOT
    23,  # SPELLMOD_EFFECT3
    24,  # SPELLMOD_BONUS_MULTIPLIER
    27,  # SPELLMOD_VALUE_MULTIPLIER
}
# (spell id, 1-based effect) pairs of custom/hand-edited SpellMods that are *deliberately* family-wide
# (all-zero classmask = every spell of the SpellFamilyName). Add an entry, with the reason, only after
# confirming the leak is the intent. See melee-haste-gcd T4-FIX (Predatory Strikes).
_FAMILY_WIDE_ALLOWED: set[tuple[int, int]] = {
    # Empowering Frostbolt 200023/200024 effect 1: the crit damage bonus of ALL your spells is meant to be
    # increased (docs/reworks/frost-mage-rework.md:199, "the critical strike damage bonus of your spells").
    (200023, 1),
    (200024, 1),
    # Chilled to the Bone 44566-44568 effect 1: "all damage you deal" is meant to reach every mage spell
    # (user ruling 2026-10-16, S1c).
    (44566, 1),
    (44567, 1),
    (44568, 1),
}
_SPELLMOD_AURAS = {107, 108}  # SPELL_AURA_ADD_FLAT_MODIFIER, SPELL_AURA_ADD_PCT_MODIFIER
_LETTERS = ("A", "B", "C")
_MASK_COLUMNS = tuple(f"EffectSpellClassMask{letter}_{n}" for letter in _LETTERS for n in (1, 2, 3))


def _u32(value) -> int:
    return int(value or 0) & 0xFFFFFFFF


def check_classmask_scoping(
    entries: list[dict], rows: list[dict], stock_rows: dict[int, dict] | None = None,
) -> list[str]:
    """Flags any row where a SpellMod effect that needs a classmask to be
    meaningfully scoped ends up with an all-zero one for the effect it
    actually lives on - almost always caused by writing the override under
    the wrong letter (see apps/dbc-tools/README.md's "Gotcha" callout for the
    letter/number rule).

    Exemption: an effect whose row has a stock client Spell.dbc counterpart
    (`stock_rows`, i.e. `state.load_stock_rows(dbcfmt.SPELL)`) with the same
    nine EffectSpellClassMask* values *and* the same EffectAura/EffectMiscValue
    on that effect - real Blizzard bytes, correct by construction (a few stock
    SpellMods are deliberately family-wide). A row with no stock counterpart is
    never exempt. This replaced an exemption keyed on the row's
    `notes == "pulled from existing data"`, which hid hand edits made to pulled
    rows without updating the note (Improved Blizzard 11185/12487/12488, Arcane
    Flows 44378/44379 - 2026-10-06). Requiring the effect's aura/misc to match
    too keeps a SpellMod effect *added* to a stock row whose masks were left
    untouched from slipping through.
    """
    stock_rows = stock_rows or {}
    warnings: list[str] = []
    for entry, row in zip(entries, rows):
        stock = stock_rows.get(row.get("ID", entry.get("id")))
        stock_masks_match = stock is not None and all(
            _u32(row.get(col)) == _u32(stock.get(col)) for col in _MASK_COLUMNS
        )
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
        warned_effects: set[int] = set()
        if any(any(word) for word in masks):
            _check_scope_required(entry, row, masks, stock, stock_masks_match, warnings, warned_effects)
        for i in range(3):
            aura = row.get(f"EffectAura_{i + 1}", 0)
            misc = row.get(f"EffectMiscValue_{i + 1}", 0)
            if aura not in _SPELLMOD_AURAS or any(masks[i]) or i in warned_effects:
                continue
            if (row["ID"], i + 1) in _FAMILY_WIDE_ALLOWED:
                continue
            if stock_masks_match and (
                stock.get(f"EffectAura_{i + 1}", 0) == aura and stock.get(f"EffectMiscValue_{i + 1}", 0) == misc
            ):
                continue  # identical to the stock client row - real Blizzard data
            warnings.append(
                f"spell {row['ID']} ({entry.get('name', '?')}): effect {i + 1}'s SpellMod "
                f"(EffectAura_{i + 1}={aura}, EffectMiscValue_{i + 1}={misc}) has an all-zero classmask "
                f"on a custom/hand-edited row, so it applies to EVERY spell of the family "
                f"(SpellInfo::IsAffected). Scope it, use a marker bit nothing matches "
                f"(druid _masks.MARKER_NOTHING) if it is only a data marker, or add it to "
                f"lint._FAMILY_WIDE_ALLOWED if family-wide is intended."
            )
    return warnings


def _check_scope_required(entry, row, masks, stock, stock_masks_match, warnings, warned_effects) -> None:
    for i in range(3):
        aura = row.get(f"EffectAura_{i + 1}", 0)
        misc = row.get(f"EffectMiscValue_{i + 1}", 0)
        if not (aura in _SPELLMOD_AURAS and misc in _SCOPE_REQUIRED_OPS and not any(masks[i])):
            continue
        if stock_masks_match and (
            stock.get(f"EffectAura_{i + 1}", 0) == aura and stock.get(f"EffectMiscValue_{i + 1}", 0) == misc
        ):
            continue  # identical to the stock client row - real Blizzard data
        warned_effects.add(i)
        warnings.append(
            f"spell {row['ID']} ({entry.get('name', '?')}): effect {i + 1}'s "
            f"SpellMod (EffectAura_{i + 1}={aura}, EffectMiscValue_{i + 1}={misc}) has an "
            f"all-zero classmask (letter {_LETTERS[i]}: {masks[i]}) even though this row "
            f"sets a classmask elsewhere ({masks}) - probably "
            f"EffectSpellClassMask{_LETTERS[i]}_* needs the value that's on a different "
            f"letter. All-zero here means the engine applies it to every matching spell in "
            f"the family, not just the intended one."
        )


# Spell ids whose family-0 SpellMod (aura 107 / 108 on a SpellClassSet 0 row) is a *deliberate* effect on every
# spell of every class. Add an entry only with a one-line reason, after confirming the leak is the intent.
FAMILY_ZERO_SPELLMOD_ALLOW: dict[int, str] = {}


def check_family_zero_spellmods(
    entries: list[dict], rows: list[dict], stock_rows: dict[int, dict] | None = None,
    allow: dict[int, str] | None = None,
) -> list[str]:
    """A declared row with an aura 107 / 108 effect whose built `SpellClassSet` is 0. `SpellInfo::IsAffected`
    returns true for family 0 and ignores the mask, so the modifier reaches EVERY spell of every class (and
    the pets' spells through `Unit::GetSpellModOwner`) whatever its EffectSpellClassMask* says - Improved
    Prayer of Mending's -4 s cooldown / +20% on a Freepick hunter's Bite, Claw and Smack. Set the row's
    SpellClassSet to the owning class's family (and scope the mask), or add the id to
    FAMILY_ZERO_SPELLMOD_ALLOW with the reason.

    Exemptions: a row in `allow`; an effect whose aura, misc value and nine EffectSpellClassMask* values equal
    its stock client Spell.dbc row on that effect (real Blizzard data, e.g. the stock family-wide Hunter Giant
    Stalker) - the check_classmask_scoping pattern. Pass the *full* declared population."""
    stock_rows = stock_rows or {}
    allowed = FAMILY_ZERO_SPELLMOD_ALLOW if allow is None else allow
    warnings: list[str] = []
    for entry, row in zip(entries, rows):
        spell_id = row.get("ID", entry.get("id"))
        if spell_id in allowed or _u32(row.get("SpellClassSet")) != 0:
            continue
        stock = stock_rows.get(spell_id)
        # The stock row must itself be family 0: a rebuild of a stock family-N row that lost its
        # SpellClassSet keeps every mask byte and is exactly the leak this lint exists for.
        masks_match = (
            stock is not None and _u32(stock.get("SpellClassSet")) == 0
            and all(_u32(row.get(col)) == _u32(stock.get(col)) for col in _MASK_COLUMNS)
        )
        for i in range(3):
            aura = row.get(f"EffectAura_{i + 1}", 0)
            misc = row.get(f"EffectMiscValue_{i + 1}", 0)
            if aura not in _SPELLMOD_AURAS:
                continue
            if masks_match and (
                stock.get(f"EffectAura_{i + 1}", 0) == aura and stock.get(f"EffectMiscValue_{i + 1}", 0) == misc
            ):
                continue  # identical to the stock client row - real Blizzard data
            warnings.append(
                f"spell {spell_id} ({entry.get('name', '?')}): effect {i + 1}'s SpellMod "
                f"(EffectAura_{i + 1}={aura}, EffectMiscValue_{i + 1}={misc}) is on a SpellClassSet 0 row, "
                f"so SpellInfo::IsAffected applies it to EVERY spell of every class and to pet spells "
                f"whatever its classmask says. Set the row's SpellClassSet to the owning class's family, "
                f"or add the id to lint.FAMILY_ZERO_SPELLMOD_ALLOW with the reason."
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


# Spell ids exempt from the EquippedItemClass lint (reviewed by hand: the spell really requires an
# equipped item of class 0, Consumable). Keep a comment per id; expected to stay empty.
EQUIPPED_ITEM_CLASS_ALLOW: frozenset[int] = frozenset()

_SPELL_ATTR0_PASSIVE = 0x40


def check_custom_equipped_item_class(
    entries: list[dict], allow: frozenset[int] | set[int] | None = None,
) -> list[str]:
    """A custom spell (id >= RANGE_LINT_MIN_ID, not in `allow`) whose `EquippedItemClass` is unset or 0.
    The column defaults to 0 = ITEM_CLASS_CONSUMABLE, which the engine reads as "needs an equipped item of
    class 0": `Spell::CheckItems` -> `Player::HasItemFitToSpellRequirements` logs "Not handled spell
    requirement for item class 0" and fails the cast with SPELL_FAILED_EQUIPPED_ITEM_CLASS, silently for a
    triggered one (Aspect of the Beast/Monkey procs, Fanned Flames - docs/bugs-and-fixes.md). Passive
    spells (SPELL_ATTR0_PASSIVE) are exempt: CheckCast skips CheckItems for them. Set
    `'EquippedItemClass': -1` in `raw_overrides`, or add the id to EQUIPPED_ITEM_CLASS_ALLOW.

    Pass the *full* declared population, like check_zero_range_unit_target."""
    allowed = EQUIPPED_ITEM_CLASS_ALLOW if allow is None else allow
    warnings: list[str] = []
    for entry in entries:
        spell_id = entry["id"]
        if spell_id < RANGE_LINT_MIN_ID or spell_id in allowed:
            continue
        raw = entry.get("raw_overrides") or {}
        if raw.get("EquippedItemClass", 0) != 0:
            continue
        # A passive spell is applied through learn/aura-restore, never a cast that runs CheckItems.
        if int(raw.get("Attributes", entry.get("attributes")) or 0) & _SPELL_ATTR0_PASSIVE:
            continue
        warnings.append(
            f"spell {spell_id} ({entry.get('name', '?')}): EquippedItemClass is 0 (the default), which means "
            f"\"needs an equipped item of class 0\" and fails every cast with "
            f"SPELL_FAILED_EQUIPPED_ITEM_CLASS. Set raw_overrides 'EquippedItemClass': -1, or add the id to "
            f"lint.EQUIPPED_ITEM_CLASS_ALLOW."
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


def _is_inert_talent_tab(row_id: int, row: dict, base: dict[int, dict]) -> bool:
    """A TalentTab row that is new and matches no class and no pet type (`retire_talent()`'s holding tab,
    60800): the client never shows it, so shipping it cannot change any existing talent frame."""
    return row_id not in base and not int(row.get("ClassMask") or 0) and not int(row.get("PetTalentMask") or 0)


def check_client_patch(
    shipping: dict[str, dict[int, dict]], stock: dict[str, dict[int, dict]], previous_files: set[str] | None,
    notes: list[str] | None = None,
) -> list[str]:
    """Warnings about what the client patch is about to carry (docs/bugs-and-fixes.md, 2026-10-02:
    one run shipped a TalentTab.dbc nobody meant to change, and it broke every talent frame).

    `shipping`: table name -> {id: row} for the custom/changed rows going into patch-Z.mpq.
    `stock`: table name -> stock rows, for the tables in _REVIEW_WHEN_SHIPPED.
    `previous_files`: file names in the last build's patch-Z.mpq, or None on a first build.

    - a table in _REVIEW_WHEN_SHIPPED is shipping: list each row and the columns it changes, so a
      spurious diff (a signedness or string-offset artifact) is obvious
    - a table is new to the patch, or has dropped out of it, compared with the last build

    Known inert case (T-FIX T1-3): once the last build already carried TalentTab.dbc (so it was reviewed in
    game), a run whose only TalentTab rows are new ones with ClassMask 0 and PetTalentMask 0 - the retired
    holding tab - is appended to `notes` instead of `warnings`. The first build that ships the file still
    warns, so the in-game look happens once."""
    warnings = []
    for name, rows in sorted(shipping.items()):
        if name not in _REVIEW_WHEN_SHIPPED:
            continue
        base = stock.get(name, {})
        if (
            notes is not None and name == "TalentTab" and previous_files is not None and "TalentTab.dbc" in previous_files
            and all(_is_inert_talent_tab(row_id, row, base) for row_id, row in rows.items())
        ):
            notes.append(f"TalentTab.dbc ships {len(rows)} inert new tab(s) {sorted(rows)} (ClassMask 0, "
                         f"PetTalentMask 0) and no other change - no talent frame is affected")
            continue
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


# LFGDungeons.dbc TypeIDs LFGMgr::LoadLFGDungeons keeps that sit on an instance map (LFGMgr.h:
# LFG_TYPE_DUNGEON/RAID/HEROIC). LFG_TYPE_RANDOM is also kept but its MapID is 0, a continent.
_LFG_INSTANCE_TYPES = {1: "dungeon", 2: "raid", 5: "heroic"}
_LFGDUNGEONS_FILE = "LFGDungeons.dbc"


def check_lfg_exclusions(
    rows: list[dict], lfg_dungeons: dict[int, dict] | None,
) -> tuple[list[str], list[str]]:
    """`(errors, notes)` for lfg_exclude() declarations, checked against stock LFGDungeons.dbc.

    Error: a map with no dungeon/raid/heroic finder entry - a typo, or a continent map, which
    DisableMgr rejects at load anyway ("Disable flags for map ... are invalid" for flags on a common
    map). Note: one line per exclusion naming every finder entry it covers, since a map exclusion
    takes all wings and seasonal entries on that map with it. `lfg_dungeons` None (stock file not
    extracted) is reported as an error when anything is declared: an unchecked map id is exactly
    the silent no-op this check exists to catch."""
    if not rows:
        return [], []
    if lfg_dungeons is None:
        return [
            f"lfg_exclude() declared but no stock {_LFGDUNGEONS_FILE} to check map ids against - extract "
            f"DBFilesClient/{_LFGDUNGEONS_FILE} from the client's patch-enUS-3.MPQ into var/extractors/dbc/ "
            f"(see .agents/docs/systems/dbc-tools.md)"
        ], []
    by_map: dict[int, list[dict]] = {}
    for entry in lfg_dungeons.values():
        if entry["TypeID"] in _LFG_INSTANCE_TYPES:
            by_map.setdefault(entry["MapID"], []).append(entry)
    errors, notes = [], []
    for row in sorted(rows, key=lambda r: r["entry"]):
        map_id = row["entry"]
        entries = sorted(by_map.get(map_id, []), key=lambda e: e["ID"])
        if not entries:
            errors.append(
                f"lfg_exclude({map_id}, {row['comment']!r}): no dungeon finder entry uses map {map_id} "
                f"(LFGDungeons.dbc MapID) - wrong id? lfg_exclude() takes a Map.dbc id, not an LFGDungeons id"
            )
            continue
        covered = ", ".join(
            f"{e['ID']} {e['Name_Lang_enUS']} ({_LFG_INSTANCE_TYPES[e['TypeID']]}, {e['MinLevel']}-{e['MaxLevel']})"
            for e in entries
        )
        notes.append(f"lfg_exclude({map_id}, {row['comment']!r}) removes from the finder: {covered}")
    return errors, notes


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

def check_talent_tab_refs(talent_rows, talenttab_rows) -> list[str]:
    """ERRORs for every built Talent.dbc row whose `TabID` is not a row of the built TalentTab.dbc
    (hunter-rework SHARED §C7.10, review P2). Both arguments are the *whole* table as it will exist
    (stock plus this run's rows), not just this run's rows. A talent on a missing tab is not dropped
    quietly: mod-playerbots' `InitPetTalents` dereferences the tab of every Talent.dbc row without a null
    check and crashes, and the core's talent lookups read `sTalentTabStore.LookupEntry(...)` unguarded in
    places. `retire_talent()` moves a row to the declared holding tab 60800, never to TabID 0; a retired row
    whose tab was never declared lands here."""
    tab_ids = {int(row["ID"]) for row in talenttab_rows}
    missing: dict[int, list[int]] = {}
    for row in talent_rows:
        tab = int(row["TabID"])
        if tab not in tab_ids:
            missing.setdefault(tab, []).append(int(row["ID"]))
    errors = []
    for tab, ids in sorted(missing.items()):
        shown = ", ".join(str(i) for i in sorted(ids)[:10]) + (f", ... ({len(ids)} in all)" if len(ids) > 10 else "")
        errors.append(
            f"talent row(s) {shown} name TabID {tab}, which is not in the built TalentTab.dbc - declare the "
            f"tab() (a retired talent's holding tab is 60800, source/classes/hunter/hunter_retired_tab.py)"
        )
    return errors


# Ranged weapon ItemSubClass ids (ItemSubclassWeapon): Bow, Gun, Crossbow. Thrown (16) and Wand (19) are out.
_AMMO_WEAPON_SUBCLASSES = (2, 3, 18)
_ITEM_CLASS_WEAPON = 2
# source/items.csv rows from this id up are custom; below it they are stock Item.dbc rows being edited.
_FIRST_CUSTOM_ITEM_ID = 56806


def check_item_dbc_consistency(item_templates: list[dict], item_dbc_rows: dict[int, dict]) -> list[str]:
    """Warnings for a declared `item_template()` row whose `class`/`subclass` differs from the item's
    Item.dbc row. `item_dbc_rows` is the Item.dbc the server will have (stock plus `item_dbc` overlay plus
    this run's rows). `DBC.EnforceItemAttributes` defaults to 1 (WorldConfig.cpp) and resets the item_template
    class/subclass from Item.dbc at boot (ObjectMgr.cpp), so a mismatch means the edit is undone at the next
    start - and the client reads class/subclass from its own Item.dbc. An item with no Item.dbc row is not
    judged here (nothing to compare against)."""
    warnings = []
    for row in item_templates:
        dbc = item_dbc_rows.get(int(row["entry"]))
        if dbc is None:
            continue
        declared = (int(row["class"]), int(row["subclass"]))
        actual = (int(dbc["ClassID"]), int(dbc["SubclassID"]))
        if declared != actual:
            warnings.append(
                f"item {row['entry']} ({row.get('name', '?')}): item_template class/subclass {declared[0]}/{declared[1]} "
                f"differs from its Item.dbc row {actual[0]}/{actual[1]} - DBC.EnforceItemAttributes resets "
                f"item_template to the Item.dbc values at boot, so this edit would be undone. Add or edit the "
                f"source/items.csv row for {row['entry']} so both agree."
            )
    return warnings


def check_ranged_ammo_type(
    item_templates: list[dict], item_entries: list[dict], live_rows: dict[int, dict],
) -> list[str]:
    """Warnings for a bow, gun or crossbow that would still need ammo. With the no-ammo rework every ranged
    weapon must have `ammo_type` 0, or the client's paper-doll check refuses to let it fire. Two shapes:
    (a) a declared `item_template()` row of class 2, subclass 2/3/18 with `ammo_type` != 0;
    (b) a custom `source/items.csv` row (id >= 56806) of class 2, subclass 2/3/18 whose item_template row -
    its declaration if there is one, else the live overlay row - has `ammo_type` != 0.
    A custom weapon with no item_template row anywhere is not judged here."""
    warnings = []
    warned: set[int] = set()
    declared = {int(row["entry"]): row for row in item_templates}
    for entry, row in sorted(declared.items()):
        if (
            int(row["class"]) == _ITEM_CLASS_WEAPON and int(row["subclass"]) in _AMMO_WEAPON_SUBCLASSES
            and int(row["ammo_type"] or 0) != 0
        ):
            warnings.append(
                f"item {entry} ({row.get('name', '?')}): declared ranged weapon (subclass {row['subclass']}) has "
                f"ammo_type {row['ammo_type']}, so the client still demands ammo; declare ammo_type=0 "
                f"(source/world/ranged_weapons.py does this for every live bow, gun and crossbow)"
            )
            warned.add(entry)
    for entry in item_entries:
        entry_id = int(entry["id"])
        if (
            entry_id < _FIRST_CUSTOM_ITEM_ID or entry.get("class_id") != _ITEM_CLASS_WEAPON
            or entry.get("subclass_id") not in _AMMO_WEAPON_SUBCLASSES or entry_id in warned
        ):
            continue
        template = declared.get(entry_id, live_rows.get(entry_id))
        if template is not None and int(template.get("ammo_type") or 0) != 0:
            warnings.append(
                f"item {entry_id} ({template.get('name', '?')}): custom ranged weapon (items.csv subclass "
                f"{entry['subclass_id']}) has item_template ammo_type {template['ammo_type']}, so the client "
                f"still demands ammo; set ammo_type 0 in its item_template row or declare it with "
                f"item_template({entry_id}, ammo_type=0)"
            )
    return warnings


# --- Per-family bit rules (hunter-rework SHARED C7.6, PLAN section 2; T1 step 8) -----------------------


@dataclass(frozen=True)
class FamilyBitRules:
    """The family-bit rules of one SpellClassSet, as data so another class can join with its own row of
    `FAMILY_BIT_RULES`. A mask is `(d0, d1, d2)` = `SpellClassMask_1/_2/_3` = `EffectSpellClassMaskX_1/_2/_3`.
    The hunter literals below are PLAN section 2 / SHARED A3 (`_masks.py` does not exist until H0, and a lint
    must not import the thing it checks)."""

    name: str
    spell_class_set: int
    # (a) a spell that is not one of these must not carry any of these bits (SpellInfo::GetSpellSpecific
    # makes any carrier SPELL_SPECIFIC_ASPECT, which knocks the active aspect off). `exempt_name_prefix` is
    # the name prefix that marks the spell as the real thing - but only for a spell that is also learned by a
    # player (it has a SkillLineAbility row), because a helper or triggered aura can be named "Aspect of ..."
    # too and still knocks the real aspect off (T-FIX T1-6); `exempt_ids` is the explicit escape hatch.
    protected_bits: tuple[int, int, int] = (0, 0, 0)
    exempt_name_prefix: str = ""
    exempt_ids: frozenset = frozenset()
    # (b) nobody may carry these bits (a poisoned bit a core hardcode still keys on).
    forbidden_carrier_bits: tuple[int, int, int] = (0, 0, 0)
    # (c) no reader mask (an effect mask or a spell_proc family mask) may share a bit with these
    # (`SpellInfo::IsAffected` matches on ANY shared bit, so a reader containing the pet bit reaches every pet
    # ability).
    forbidden_reader_bits: tuple[int, int, int] = (0, 0, 0)
    # (d) a pet-cast spell (carries one of `pet_group_bits`, or is taught on a pet skill line) must carry all
    # of `pet_required_bits`: without the pet bit SpellInfo::IsRangedWeaponSpell is true for any hunter-family
    # spell and the pet's cast would need a ranged weapon.
    pet_group_bits: tuple[int, int, int] = (0, 0, 0)
    pet_required_bits: tuple[int, int, int] = (0, 0, 0)
    # Message wording, so a rule set that is not the hunter's says its own thing. The defaults are the hunter's.
    # An all-zero mask turns its rule into a no-op: (a) and (c) need a shared bit, (b) needs a carrier bit, (d)
    # needs `pet_required_bits` non-zero. `exempt_name_prefix=""` means "no name exemption".
    protected_label: str = "aspect"
    protected_article: str = "an"
    protected_effect: str = "SPELL_SPECIFIC_ASPECT and it knocks the active aspect off"
    protected_hint: str = (
        "Use another bit (a real aspect needs a SkillLineAbility row, or its id in the rule's exempt_ids)."
    )
    carrier_note: str = "d1 b0, the old Steady Shot bit that old readers and core hardcodes still key on"
    reader_label: str = "the pet bit (d1 b28)"
    reader_reaches: str = "every pet ability"
    reader_hint: str = "Read a pet group through its d2 bit alone."


HUNTER_FAMILY_RULES = FamilyBitRules(
    name="hunter",
    spell_class_set=9,
    protected_bits=(0x380000, 0x440000, 0x1010),                    # ASPECT_SPECIFIC
    exempt_name_prefix="Aspect of",
    forbidden_carrier_bits=(0, 0x1, 0),                              # d1 b0: the old Steady Shot bit
    forbidden_reader_bits=(0, 0x10000000, 0),                        # d1 b28: the pet bit
    pet_group_bits=(0, 0, 0x400000 | 0x800000 | 0x1000000),          # d2 b22 / b23 / b24
    pet_required_bits=(0, 0x10000000, 0),                            # d1 b28
)
# Shaman T1 (.agents/plans/shaman-rework/shaman-rework.FAMILY-BITS.md s3.3, "never take"):
#   d1 b5 | d1 b10 (0x420): SpellInfo::GetSpellSpecific makes any shaman-family spell carrying either bit
#     SPELL_SPECIFIC_ELEMENTAL_SHIELD (SpellInfo.cpp:2241-2248), and IsAuraExclusiveBySpecificWith makes two of
#     those mutually exclusive on a target. SH0 lists a custom real shield's id in `exempt_ids`.
#   d2 b11 | d2 b31 (0x80000800): the Orc racial Command (65223, cast on pets by the core) and the Draenei racial
#     Gift of the Naaru (59547); a reader mask containing either would modify a racial.
# The other shaman "never take" bits (d0 b10 shield with NO_THREAT, d2 b14 root DR) and "imbue auras leave d1 b11"
# depend on attributes or on the spell's role, which this table cannot express: SH0 pins them with targeted tests.
SHAMAN_FAMILY_RULES = FamilyBitRules(
    name="shaman",
    spell_class_set=11,
    protected_bits=(0, 0x420, 0),                                    # d1 b5, b10: ELEMENTAL_SHIELD_SPECIFIC
    exempt_name_prefix="",
    exempt_ids=frozenset(),
    forbidden_reader_bits=(0, 0, 0x80000800),                        # d2 b11 (Orc racial), d2 b31 (Draenei racial)
    protected_label="elemental shield",
    protected_effect=(
        "SPELL_SPECIFIC_ELEMENTAL_SHIELD, which is mutually exclusive with the shaman's real elemental shields"
    ),
    protected_hint="Use another bit, or list the id in the rule's exempt_ids if it really is a shield.",
    reader_label="a racial's bit (d2 b11 Orc Command, d2 b31 Draenei Gift of the Naaru)",
    reader_reaches="the racial",
    reader_hint="Pick another bit for the reader.",
)
# Death Knight DK0a (death-knight-rework.DK0-HANDOFF.md "Family bits", FAMILY-BITS s3.3):
#   carriers: d2 b31 (Draenei racial Gift of the Naaru), d1 b23 (Orc racial pet bit), d0 b6 (server Icy Touch alias).
#   readers: d2 b31, d1 b10 / b23 / b24 (Orc racial pet bits) - a reader containing them would modify a racial.
DEATHKNIGHT_FAMILY_RULES = FamilyBitRules(
    name="deathknight",
    spell_class_set=15,
    forbidden_carrier_bits=(0x40, 0x800000, 0x80000000),             # d0 b6, d1 b23, d2 b31
    forbidden_reader_bits=(0, 0x400 | 0x800000 | 0x1000000, 0x80000000),  # d1 b10 / b23 / b24, d2 b31
    carrier_note="a bit a racial or a core hardcode keys on: d0 b6 Icy Touch alias, d1 b23 Orc pet bit, d2 b31 Gift",
    reader_label="a racial's bit (d1 b10 / b23 / b24 Orc pet bits, d2 b31 Draenei Gift of the Naaru)",
    reader_reaches="the racial",
    reader_hint="Pick another bit for the reader.",
)
# Rogue T1 (.agents/plans/rogue-rework/rogue-rework.FAMILY-BITS.md s3.3 "never take", s6.1 C2; PLAN s1D.11).
# Carrier bits no custom rogue-family spell may carry, each a core hardcode that keys on the bit:
#   d0 b11 (0x800): Stealth 1784's removal runs RemoveAurasWithFamily(ROGUE, 0x800), so a new aura on it is stripped
#     whenever Stealth drops.
#   d0 b22 (0x400000): the Stealth hardcode (SpellAuras.cpp:1831-1854) drives the Master of Subtlety and Overkill
#     apply / tail code, so a new aura on it (Shadowed, Shadow Dance's twin) starts the 8 s / 20 s tails at the wrong
#     time.
#   d0 b25 (0x2000000): the Hemorrhage +1 combo point and dagger +50% hardcode (SpellEffects.cpp:3693-3705): any
#     weapon-damage family-8 spell carrying it gets both.
# The other s3.3 bits depend on the spell's role, which this table cannot express (a carrier list is all-or-nothing and
# a "never take except on X" rule needs a per-spell exemption this dataclass has no field for), so RG0 and the spec
# stages pin them with targeted tests: d0 b16 only on Deadly Poison (AURA_STATE_DEADLY_POISON, Envenom's dose
# consumption, Mutilate's poisoned check), d0 b20 only on Rupture (Glyph of Backstab extends it), d0 b17 only on a
# spell meant to take the Eviscerate AP term, d0 b26 / d1 b18 on a new weapon strike (dagger bonus, Hemorrhage's combo
# point), d1 b1 / b2 / b3 (Mutilate +20%, Cold Blood / Remorseless, Envenom's effect code), d0 b3 / b10 / b24 (the DR
# categories), the Preparation lists (d0 b4 / b5 / b6, d1 b6 / b9 / b11 + d0 b30, d1 b20), d0 b0 while Throw shares it,
# and d1 b19 as the poison group (a role, not a ban).
ROGUE_FAMILY_RULES = FamilyBitRules(
    name="rogue",
    spell_class_set=8,
    forbidden_carrier_bits=(0x800 | 0x400000 | 0x2000000, 0, 0),    # d0 b11, d0 b22, d0 b25
    carrier_note=(
        "d0 b11 Stealth's removal strips every family-8 aura carrying it, d0 b22 the Stealth hardcode drives the "
        "Master of Subtlety / Overkill tails, d0 b25 the Hemorrhage combo point / dagger hardcode"
    ),
)
# Warrior T1 (.agents/plans/warrior-rework/warrior-rework.FAMILY-BITS.md s3.3 "never take", s6.2 hardcodes;
# T1-HANDOFF WP2). Carrier bits no custom warrior-family spell may carry, each keyed in core or a script:
#   d0 b0 (0x1): Charge's own bit, shared with ~95 NPC rows and read by Improved Charge, Glyph of Charge and
#     Juggernaut's proc row (the likeliest slip is copying stock Heroic Leap 53625's mask, which sits on it).
#   d0 b1 (0x2) and d0 b24 (0x1000000): the diminishing-returns categories (SpellMgr.cpp:158-166, Hamstring / Charge
#     Stun).
#   d0 b17 (0x20000) and d1 b5 (0x20): the "Shout" CC marker, SPELL_ATTR0_CU_AURA_CC (SpellMgr.cpp:3474-3477,
#     Unit.cpp:5442).
#   d1 b6 (0x40): Devastate casts Sunder Armor 58567 off this bit (SpellEffects.cpp:3681-3693).
#   d2 b31 (0x80000000): the Draenei racial Gift of the Naaru 28880 carries it, and Shadow Resistance 59221 reads it
#     (the only stock family-4 d2 carrier and reader).
# Reader ban: d2 b31, a reader containing it would modify the racial.
# The bits that depend on a spell's role are not expressible in this table (a carrier list is all-or-nothing and a
# "never take except on X" rule needs a per-spell exemption the dataclass has no field for), so W0b and the spec stages
# pin them with targeted tests: d0 b7 only on Thunder Clap and its echo (Improved Thunder Clap, Thunderstruck);
# d0 b10 only on Revenge (the Incite capstone, spell_warrior.cpp:1382); d1 b8 Victory Rush damage / glyph
# (SpellEffects.cpp:371-383, Unit.cpp:9212); d1 b9 plus category 1209 Shield Slam (SpellEffects.cpp:361-370); d1 b18 the
# Victorious aura state (SpellInfo.cpp:2052); d1 b21 (a carrier counts as Dazed for Heroic Strike's bonus,
# spell_warrior.cpp:1080); d0 b23 the stances (a rage-keep block keys on icon 139 / A112 831, not the bit, so it is a
# role bit, not a ban); d2 b0-b3 only on their FAMILY-BITS s5
# roles; and no new warrior spell on category 132 unless it should get NO_CATEGORY_COOLDOWN_MODS
# (SpellInfoCorrections.cpp:5335). `source/classes/warrior/_masks.py` holds the same literals: the lint does not
# import it (a lint must not import the thing it checks), lib/test_warrior_family_rules.py asserts they agree.
WARRIOR_FAMILY_RULES = FamilyBitRules(
    name="warrior",
    spell_class_set=4,
    forbidden_carrier_bits=(0x01020003, 0x60, 0x80000000),           # d0 b0 / b1 / b17 / b24, d1 b5 / b6, d2 b31
    forbidden_reader_bits=(0, 0, 0x80000000),                        # d2 b31 (Draenei racial)
    carrier_note=(
        "d0 b0 Charge's bit (Improved Charge, Glyph of Charge, Juggernaut read it), d0 b1 / b24 diminishing-returns "
        "categories, d0 b17 / d1 b5 the Shout CC marker, d1 b6 Devastate's Sunder cast, d2 b31 the Draenei racial's bit"
    ),
    reader_label="the Draenei racial's bit (d2 b31 Gift of the Naaru)",
    reader_reaches="the racial",
    reader_hint="Pick another bit for the reader.",
)
FAMILY_BIT_RULES = (
    HUNTER_FAMILY_RULES, SHAMAN_FAMILY_RULES, DEATHKNIGHT_FAMILY_RULES, ROGUE_FAMILY_RULES, WARRIOR_FAMILY_RULES,
)
_CUSTOM_SPELL_ID_START = 200000
PET_SHARED_SKILL_LINE = 270  # "Pet - Hunter": the skill line every hunter pet family shares


def _spell_class_mask(row: dict) -> tuple[int, int, int]:
    return tuple(_u32(row.get(f"SpellClassMask_{n}")) for n in (1, 2, 3))


def _shares_bit(mask: tuple[int, int, int], bits: tuple[int, int, int]) -> bool:
    return any(m & b for m, b in zip(mask, bits))


def _hex_mask(mask: tuple[int, int, int]) -> str:
    return "(" + ", ".join(f"0x{word:X}" for word in mask) + ")"


def check_family_bit_rules(
    entries: list[dict], rows: list[dict], spell_procs: list[dict] | None = None,
    skill_line_abilities: list[dict] | None = None, pet_skill_lines: set[int] | frozenset[int] = frozenset(),
    rules: tuple[FamilyBitRules, ...] = FAMILY_BIT_RULES,
) -> list[str]:
    """WARNINGs for the family-bit rules of every `FamilyBitRules` set (the hunter's PLAN section 2 and, since shaman
    T1, the shaman's FAMILY-BITS s3.3), on custom spell ids (>= 200000) of each rule set's SpellClassSet. A rule set
    with a zero mask is silent for the rules that mask drives. Also exported as `check_hunter_family_rules`.
    `entries`/`rows` are aligned like `check_classmask_scoping`'s (source entry, built row).
    Rules, per `FamilyBitRules`:
      (a) a non-aspect carrying an aspect bit (an "Aspect of ..." name only counts when the spell has a
          SkillLineAbility row; otherwise list its id in `exempt_ids`);
      (b) any carrier of a forbidden carrier bit (d1 b0);
      (c) a reader mask containing the pet bit d1 b28 - on any effect's `EffectSpellClassMask`, or in a
          declared `spell_proc` family mask (`spell_procs`: the registry's rows, whatever their spell id, with
          SpellFamilyName of the rule's class set or 0 - 0 matches any family);
      (d) inverted: a pet-cast spell that lacks the pet bit. Pet-cast = carries a pet group bit, or is taught
          by a SkillLineAbility row (`skill_line_abilities`: dicts with Spell/SkillLine) on a pet skill line
          (`pet_skill_lines`, plus 270). The pet bit with DmgClass RANGED (the pets' ranged spits, the 30 yd
          commands) is intended and never warns - nothing here looks at DmgClass.
    Rule (c) looks at every effect's mask whatever its aura: an effect mask only exists to be read."""
    spell_procs = spell_procs or []
    pet_lines = set(pet_skill_lines) | {PET_SHARED_SKILL_LINE}
    taught_on_pet_line = {
        int(r["Spell"]) for r in (skill_line_abilities or []) if int(r["SkillLine"]) in pet_lines
    }
    learned = {int(r["Spell"]) for r in (skill_line_abilities or [])}
    warnings: list[str] = []
    for rule in rules:
        for entry, row in zip(entries, rows):
            spell_id = int(row["ID"])
            if spell_id < _CUSTOM_SPELL_ID_START or int(row.get("SpellClassSet") or 0) != rule.spell_class_set:
                continue
            label = f"spell {spell_id} ({entry.get('name', '?')})"
            mask = _spell_class_mask(row)
            name = str(entry.get("name") or "")
            # An empty prefix is "no name exemption": str.startswith("") is always True, so test it first.
            name_exempt = bool(
                rule.exempt_name_prefix and name.lower().startswith(rule.exempt_name_prefix.lower())
                and spell_id in learned
            )
            if _shares_bit(mask, rule.protected_bits) and spell_id not in rule.exempt_ids and not name_exempt:
                warnings.append(
                    f"{label}: {rule.name} family-bit rule (a): carries "
                    f"{rule.protected_article} {rule.protected_label} bit {_hex_mask(mask)} "
                    f"({rule.protected_label} bits {_hex_mask(rule.protected_bits)}) but is "
                    f"not {rule.protected_article} {rule.protected_label} - the core makes it "
                    f"{rule.protected_effect}. {rule.protected_hint}"
                )
            if _shares_bit(mask, rule.forbidden_carrier_bits):
                warnings.append(
                    f"{label}: {rule.name} family-bit rule (b): carries a poisoned bit {_hex_mask(mask)} "
                    f"({rule.carrier_note}, {_hex_mask(rule.forbidden_carrier_bits)}). Use another bit."
                )
            for letter in _LETTERS:
                reader = tuple(_u32(row.get(f"EffectSpellClassMask{letter}_{n}")) for n in (1, 2, 3))
                if _shares_bit(reader, rule.forbidden_reader_bits):
                    warnings.append(
                        f"{label}: {rule.name} family-bit rule (c): effect {_LETTERS.index(letter) + 1}'s reader "
                        f"mask {_hex_mask(reader)} contains {rule.reader_label} - SpellInfo::IsAffected matches "
                        f"on any shared bit, so it reaches {rule.reader_reaches}. {rule.reader_hint}"
                    )
            pet_cast = _shares_bit(mask, rule.pet_group_bits) or spell_id in taught_on_pet_line
            lacks_pet_bit = not all(m & b == b for m, b in zip(mask, rule.pet_required_bits))
            if any(rule.pet_required_bits) and pet_cast and lacks_pet_bit:
                warnings.append(
                    f"{label}: {rule.name} family-bit rule (d): a pet-cast spell without the pet bit "
                    f"{_hex_mask(rule.pet_required_bits)} (mask {_hex_mask(mask)}) - without it the core treats "
                    f"it as a ranged weapon spell and the pet's cast needs a ranged weapon."
                )
        for proc in spell_procs:
            # Every declared row, whatever its id (declared rows are ours; hunter procs sit on stock ids too).
            # SpellFamilyName 0 matches the family mask against ANY family, so it is judged like the class set.
            if int(proc.get("SpellFamilyName") or 0) not in (rule.spell_class_set, 0):
                continue
            reader = tuple(_u32(proc.get(f"SpellFamilyMask{n}")) for n in (0, 1, 2))
            if _shares_bit(reader, rule.forbidden_reader_bits):
                warnings.append(
                    f"spell_proc {proc['SpellId']}: {rule.name} family-bit rule (c): family mask "
                    f"{_hex_mask(reader)} contains {rule.reader_label}, so the proc reaches {rule.reader_reaches}. "
                    f"{rule.reader_hint}"
                )
    return warnings


# The hunter T1 name, kept so generate.py and every hunter test keep working.
check_hunter_family_rules = check_family_bit_rules


# --- Shaman T1 lints (.agents/plans/shaman-rework/shaman-rework.T1-HANDOFF.md steps 2-7) -----------------------
#
# Every check below takes already-built spell rows (`rows`, aligned with `entries` where both are passed) and runs
# in generate.py's full run AND in its `--check` block (hunter T1-10: a lint that only runs on the full pipeline is
# invisible to a `--check` session). `--check` has no live (promoted-aware) overlay, so each docstring says which
# input falls back to the stock client rows there.


def check_creature_spell_rows(rows: list[dict], known_spell_ids: set[int] | frozenset[int]) -> list[str]:
    """WARNING for a declared `creature_spell()` row whose spell is in neither the spells this run builds nor the
    stock/live spells (`known_spell_ids`): `ObjectMgr::LoadCreatureTemplateSpells` logs "has non existing spell" at
    boot and leaves the slot empty. Pass the union of the declared spell ids and the existing Spell.dbc rows (the
    `--check` run only has the stock client rows for the second half)."""
    warnings = []
    for row in rows:
        spell_id = int(row["Spell"])
        if spell_id in known_spell_ids:
            continue
        warnings.append(
            f"creature_spell({row['CreatureID']}, {row['Index']}, {spell_id}): spell {spell_id} is neither declared "
            f"in source/ nor a stock spell - ObjectMgr::LoadCreatureTemplateSpells drops the slot at boot. "
            f"Check the id, or declare the spell."
        )
    return warnings


# --- Death Knight T1: rune costs, spell_threat and creation rows ---

POWER_TYPE_RUNE = 5  # Powers (SharedDefines.h) POWER_RUNE


def _effective_column(entry: dict, column: str, typed_key: str | None = None) -> int:
    """The value `lib/build.py` writes for `column`: a `raw_overrides` value wins over the typed field."""
    raw = entry.get("raw_overrides") or {}
    if column in raw:
        return int(raw[column] or 0)
    return int(entry.get(typed_key, 0) or 0) if typed_key else 0


def check_undeclared_spell_rune_costs(
    entries: list[dict], declared_ids: set[int], block: dict | None,
) -> list[str]:
    """Errors for a spell whose `RuneCostID` is inside `source/ids.yaml`'s `spellrunecost` block but has no
    `spell_rune_cost()` declaration: the id names no row, so `Spell::CheckRuneCost` finds no cost and the cast is
    free (Spell.cpp:5621-5624). Mirrors `check_undeclared_spell_categories`: pass the *full* declared spell
    population, stock ids (outside the block) are never checked, `block` None checks nothing."""
    if not block:
        return []
    errors = []
    for entry in entries:
        cost_id = _effective_column(entry, "RuneCostID")
        if block["start"] <= cost_id <= block["end"] and cost_id not in declared_ids:
            errors.append(
                f"spell {entry.get('id', '?')} ({entry.get('name', '?')}): RuneCostID {cost_id} is in the "
                f"spellrunecost reserved block but no spell_rune_cost({cost_id}) is declared - the cast would be free "
                f"(Spell::CheckRuneCost finds no row)"
            )
    return errors


def check_spell_rune_costs(
    entries: list[dict], rows: list[dict], stock_costs: dict[int, dict] | None, declared_costs: list[dict],
) -> list[str]:
    """WARNINGs about custom spells' (id >= 200000) rune costs and about declared `spell_rune_cost()` rows.
    `rows` are the built Spell.dbc rows aligned with `entries`; `stock_costs` the stock `SpellRuneCost.dbc` rows by
    id (None: the file is not extracted); `declared_costs` the declared registry rows.

      (a) `RuneCostID` set and `PowerType` not 5: the cost and its Runic Power gain are ignored
          (`CheckRuneCost` returns OK, Spell.cpp:5605; `TakePower` calls `TakeRunePower` only for `POWER_RUNE`,
          :5531). Stock spells are not checked: 168 carry a `RuneCostID` with another `PowerType` (Death Coil
          47541 = power 6 / cost 422), inert.
      (b) a `RuneCostID` that is neither a stock row nor declared: a free cast (:5621-5624, 5666-5668).
      (c) a declared row whose (Blood, Unholy, Frost, RunicPower) equals a stock row: reference the stock id
          instead (A3: reuse stock rows).

    Without the stock file (b) and (c) cannot be judged: one WARNING says so (only when there is something to
    judge) and nothing is printed per spell, the `CreatureFamily.dbc` pattern."""
    warnings = []
    custom_costs: list[tuple[dict, dict, int]] = []
    for entry, row in zip(entries, rows):
        spell_id = int(row.get("ID", entry.get("id", 0)))
        if spell_id < _CUSTOM_SPELL_ID_START:
            continue
        cost_id = int(row.get("RuneCostID") or 0)
        if not cost_id:
            continue
        custom_costs.append((entry, row, cost_id))
        if int(row.get("PowerType") or 0) != POWER_TYPE_RUNE:
            warnings.append(
                f"spell {spell_id} ({entry.get('name', '?')}): RuneCostID {cost_id} with PowerType "
                f"{int(row.get('PowerType') or 0)} - the rune cost and the Runic Power gain only apply to a "
                f"PowerType 5 (RUNE) spell and are ignored here"
            )
    if stock_costs is None:
        if custom_costs or declared_costs:
            warnings.append(
                "spell rune costs: no stock SpellRuneCost.dbc in var/extractors/dbc, so a RuneCostID with no row "
                "(a free cast) and a declared row that duplicates a stock one cannot be checked - copy it from "
                "the worldserver's DBC directory (ac-worldserver:/azerothcore/env/dist/data/dbc/)"
            )
        return warnings
    known = set(stock_costs) | {int(r["ID"]) for r in declared_costs}
    for entry, row, cost_id in custom_costs:
        if cost_id not in known:
            warnings.append(
                f"spell {row.get('ID', entry.get('id'))} ({entry.get('name', '?')}): RuneCostID {cost_id} is "
                f"neither a stock SpellRuneCost row nor declared with spell_rune_cost() - the cast is free"
            )
    by_cost: dict[tuple, int] = {}
    for stock_id, stock in sorted(stock_costs.items()):
        by_cost.setdefault(
            (int(stock["Blood"]), int(stock["Unholy"]), int(stock["Frost"]), int(stock["RunicPower"])), stock_id,
        )
    for declared in declared_costs:
        cost = (int(declared["Blood"]), int(declared["Unholy"]), int(declared["Frost"]), int(declared["RunicPower"]))
        stock_id = by_cost.get(cost)
        if stock_id is not None and stock_id != int(declared["ID"]):
            warnings.append(
                f"spell_rune_cost({declared['ID']}): the same cost as stock SpellRuneCost row {stock_id} "
                f"(Blood {cost[0]}, Unholy {cost[1]}, Frost {cost[2]}, RunicPower {cost[3]}) - reference "
                f"RuneCostID {stock_id} instead of minting a duplicate"
            )
    return warnings


def check_spell_threat_rows(rows: list[dict], known_spell_ids: set[int] | frozenset[int]) -> list[str]:
    """WARNING for a declared `spell_threat()` row whose spell is in neither the spells this run builds nor the
    stock/live spells: `SpellMgr::LoadSpellThreats` logs "does not exist" and drops the row (SpellMgr.cpp:2358-2362).
    Pass the union of the declared spell ids and the existing Spell.dbc rows, as `check_creature_spell_rows` does."""
    warnings = []
    for row in rows:
        spell_id = int(row["entry"])
        if spell_id not in known_spell_ids:
            warnings.append(
                f"spell_threat({spell_id}): spell {spell_id} is neither declared in source/ nor a stock spell - "
                f"SpellMgr::LoadSpellThreats drops the row at boot. Check the id, or declare the spell."
            )
    return warnings


def check_creation_rows(
    actions: list[dict], casts: list[dict], known_spell_ids: set[int] | frozenset[int],
) -> list[str]:
    """WARNINGs for declared creation rows that name a spell nobody defines: a `creation_action()` of type 0 (spell)
    and every `creation_cast()`. The loader (ObjectMgr::LoadPlayerInfo) does not check the spell, so the button stays
    empty or the creation cast silently fails. Pass the same union as `check_spell_threat_rows`."""
    warnings = []
    for row in actions:
        if int(row["type"]) == 0 and int(row["action"]) not in known_spell_ids:
            warnings.append(
                f"creation_action({row['race']}, {row['class']}, {row['button']}, {row['action']}): spell "
                f"{row['action']} is neither declared in source/ nor a stock spell - the button would hold nothing"
            )
    for row in casts:
        if int(row["spell"]) not in known_spell_ids:
            warnings.append(
                f"creation_cast({row['spell']}, {row['classMask']}, {row['raceMask']}): spell {row['spell']} is "
                f"neither declared in source/ nor a stock spell - the creation cast would fail"
            )
    return warnings


# --- check_totem_tools (ruling 3A.8) ---

# The only SpellClassSet whose custom spells must not need a totem tool item.
TOTEM_TOOL_CLASS_SET = 11
# SpellClassSets whose every declared spell, stock ones included, must be tool-free. 11 since SH0b stripped the stock
# shaman totem columns (the Earth/Fire/Water/Air Totem items 5175/5176/5177/5178) from all 117 stock family-11 rows;
# any stock family-11 spell a later change forgets to strip warns.
TOOL_FREE_CLASS_SETS: frozenset = frozenset({11})
_TOTEM_TOOL_COLUMNS = ("Totem_1", "Totem_2", "RequiredTotemCategoryID_1", "RequiredTotemCategoryID_2")


def check_totem_tools(
    entries: list[dict], rows: list[dict], tool_free_class_sets: frozenset[int] | set[int] | None = None,
    base_spells: dict[int, dict] | None = None,
) -> list[str]:
    """Ruling 3A.8 (P0-RESULTS "Other findings"): the rework drops the totem tool requirement, because a shaman
    without the Earth/Fire/Water/Air Totem item fails the cast with SPELL_FAILED_TOTEMS (`Spell::CheckItems`). WARNING
    for a custom spell (id >= 200000) of SpellClassSet 11 whose built row has a non-zero `Totem_1/2` (the item the
    spell needs) or `RequiredTotemCategoryID_1/2` (the TotemCategory the spell needs). A SpellClassSet listed in
    `TOOL_FREE_CLASS_SETS` widens the check to every declared spell of that set, stock ids included, and, when
    `base_spells` is passed (spell id -> row: the stock client file under `--check`, the promoted-aware live rows in
    the full run), to every UNDECLARED spell of that set in it too: a learnable stock rank SH0 forgot to declare and
    strip is exactly the miss the opt-in exists to catch (117 stock family-11 spells hold a tool column, 42 of them
    declared). `entries`/`rows` are aligned like `check_classmask_scoping`'s. Zero the columns with
    `raw_overrides={'Totem_1': 0, 'Totem_2': 0, 'RequiredTotemCategoryID_1': 0, 'RequiredTotemCategoryID_2': 0}`."""
    wide = TOOL_FREE_CLASS_SETS if tool_free_class_sets is None else frozenset(tool_free_class_sets)
    warnings = []
    for entry, row in zip(entries, rows):
        spell_id = int(row["ID"])
        class_set = int(row.get("SpellClassSet") or 0)
        custom = spell_id >= _CUSTOM_SPELL_ID_START and class_set == TOTEM_TOOL_CLASS_SET
        if not (custom or class_set in wide):
            continue
        held = [(column, int(row.get(column) or 0)) for column in _TOTEM_TOOL_COLUMNS if int(row.get(column) or 0)]
        if not held:
            continue
        warnings.append(
            f"spell {spell_id} ({entry.get('name', '?')}): requires a totem tool "
            f"({', '.join(f'{column}={value}' for column, value in held)}) - Spell::CheckItems fails the cast with "
            f"SPELL_FAILED_TOTEMS for a shaman without the totem item (ruling 3A.8 drops the tools). Zero "
            f"Totem_1/2 and RequiredTotemCategoryID_1/2 in raw_overrides."
        )
    if wide and base_spells:
        declared = {int(r["ID"]) for r in rows}
        for spell_id in sorted(base_spells):
            row = base_spells[spell_id]
            if spell_id in declared or int(row.get("SpellClassSet") or 0) not in wide:
                continue
            held = [(c, int(row.get(c) or 0)) for c in _TOTEM_TOOL_COLUMNS if int(row.get(c) or 0)]
            if not held:
                continue
            warnings.append(
                f"spell {spell_id} ({row.get('Name_Lang_enUS', '?')}): an undeclared stock spell that requires a totem "
                f"tool ({', '.join(f'{column}={value}' for column, value in held)}) - declare it with spell() and zero "
                f"Totem_1/2 and RequiredTotemCategoryID_1/2 in raw_overrides, or the tool requirement stays."
            )
    return warnings


# --- check_hidden_learned_spells (P0 6b-rain: AttributesEx 0x80 hid Healing Rain) ---

_SPELL_ATTR0_DO_NOT_DISPLAY = 0x80

# Hidden, non-passive spells a player learns on purpose. One comment per id. A pure LEARN_SPELL carrier needs no
# entry (see `check_hidden_learned_spells`), so this is empty today.
HIDDEN_LEARNED_ALLOW: frozenset[int] = frozenset()
_EFFECT_LEARN_SPELL = 36


def _learn_targets(row: dict) -> list[int]:
    """The spells a row's LEARN_SPELL (effect 36) effects teach (`EffectTriggerSpell_n`)."""
    return [
        int(row.get(f"EffectTriggerSpell_{i}") or 0) for i in (1, 2, 3)
        if int(row.get(f"Effect_{i}") or 0) == _EFFECT_LEARN_SPELL and int(row.get(f"EffectTriggerSpell_{i}") or 0)
    ]


def _is_learn_carrier(row: dict) -> bool:
    """True when every non-empty effect is LEARN_SPELL: the stock 59672 talent-rank carrier pattern (hidden on
    purpose; the spells it teaches are the visible ones)."""
    effects = [int(row.get(f"Effect_{i}") or 0) for i in (1, 2, 3)]
    effects = [e for e in effects if e]
    return bool(effects) and all(e == _EFFECT_LEARN_SPELL for e in effects)


def check_hidden_learned_spells(
    entries: list[dict], rows: list[dict], skill_line_abilities: list[dict] | None = None,
    trained_spell_ids: set[int] | frozenset[int] = frozenset(),
    talent_rank_ids: set[int] | frozenset[int] = frozenset(),
    pet_skill_lines: set[int] | frozenset[int] = frozenset(), allow: frozenset[int] | set[int] | None = None,
) -> list[str]:
    """WARNING for a custom spell (id >= 200000) with `Attributes & 0x80` (SPELL_ATTR0_DO_NOT_DISPLAY) and without
    `0x40` (passive) that a player learns. The client hides a DO_NOT_DISPLAY spell from the spellbook and the
    trainer window, so a learnable active spell is never shown or castable from a button: P0's Healing Rain was
    invisible this way. "Learned" means a SkillLineAbility row on a non-pet skill line (`skill_line_abilities`: dicts
    with Spell/SkillLine, the declared plus, in the full run, the live rows; `--check` only has the declared ones),
    a `trained_by()` row (`trained_spell_ids`), a talent rank (`talent_rank_ids`), or a LEARN_SPELL (effect 36)
    target of any learned spell in `rows` (followed transitively). Pet lines (270 plus `pet_skill_lines`) do not
    count: a pet spell is shown on the pet bar. Silent: a hidden passive (a talent's aura), a hidden helper nobody
    learns (cast by a script), and a pure LEARN_SPELL carrier (every effect is effect 36, the stock 59672 pattern: the
    carrier is hidden on purpose and the spells it teaches are the visible ones). Clear 0x80, make the spell
    passive, or add a deliberate hidden spell to `HIDDEN_LEARNED_ALLOW`. Note the P0 incident itself used `.learn`,
    which no data lint can see; this catches the production shapes."""
    allowed = HIDDEN_LEARNED_ALLOW if allow is None else allow
    pet_lines = set(pet_skill_lines) | {PET_SHARED_SKILL_LINE}
    learned_via: dict[int, str] = {}
    for sla in skill_line_abilities or []:
        if int(sla["SkillLine"]) not in pet_lines:
            learned_via.setdefault(int(sla["Spell"]), f"SkillLineAbility on skill line {int(sla['SkillLine'])}")
    for spell_id in trained_spell_ids:
        learned_via.setdefault(int(spell_id), "a trained_by() row")
    for spell_id in talent_rank_ids:
        learned_via.setdefault(int(spell_id), "a talent rank")
    by_id = {int(r["ID"]): r for r in rows}
    queue = list(learned_via)
    while queue:
        source_id = queue.pop()
        source_row = by_id.get(source_id)
        if source_row is None:
            continue
        for target in _learn_targets(source_row):
            if target not in learned_via:
                learned_via[target] = f"LEARN_SPELL from spell {source_id}"
                queue.append(target)
    warnings = []
    for entry, row in zip(entries, rows):
        spell_id = int(row["ID"])
        attributes = int(row.get("Attributes") or 0)
        if spell_id < _CUSTOM_SPELL_ID_START or spell_id in allowed or spell_id not in learned_via:
            continue
        if not attributes & _SPELL_ATTR0_DO_NOT_DISPLAY or attributes & _SPELL_ATTR0_PASSIVE:
            continue
        if _is_learn_carrier(row):
            continue
        warnings.append(
            f"spell {spell_id} ({entry.get('name', '?')}): Attributes has SPELL_ATTR0_DO_NOT_DISPLAY (0x80) but a "
            f"player learns it ({learned_via[spell_id]}) and it is not passive - the client hides it from the "
            f"spellbook and the trainer window (P0 Healing Rain was invisible this way). Clear 0x80 (use "
            f"SPELL_ATTR5_NO_CASTER_AURA_ICON to hide only the buff), or make it passive (0x40) if it is an aura."
        )
    return warnings


# --- check_ground_effect_haste (PLAN s3 periodic haste, ruling s7; T0b s4) ---

_EFFECT_PERSISTENT_AREA_AURA = 27
_SPELL_ATTR5_SPELL_HASTE_AFFECTS_PERIODIC = 0x2000
# SpellEffectInfo::IsAura(): APPLY_AURA and the area-aura effects, plus PERSISTENT_AREA_AURA (a dynobj aura).
_AURA_EFFECTS = frozenset({6, 27, 35, 65, 119, 128, 129, 143})
# SpellInfo::HasPeriodicDamageOrHealEffect (SpellInfo.cpp:935-942): PERIODIC_DAMAGE 3, PERIODIC_HEAL 8,
# OBS_MOD_HEALTH 20, PERIODIC_LEECH 53, PERIODIC_DAMAGE_PERCENT 89. PERIODIC_DUMMY (226) and
# PERIODIC_TRIGGER_SPELL (23) are not on it, so they tick at their fixed amplitude.
_PERIODIC_DAMAGE_OR_HEAL_AURAS = frozenset({3, 8, 20, 53, 89})

# Existing custom ground effects that tick hasted today. PLAN s7 keeps their behavior until their owner rules, so
# they are listed, not changed. Keep one comment per id.
# SpellAuraEffects.cpp FIXED_CADENCE_PERIODIC_SPELLS (IsFixedCadencePeriodic): spells whose periodic ticks the core
# never hastes. Priest Echo of Light heal / damage today (PriestMechanics.h). Add an id here when that array grows.
FIXED_CADENCE_PERIODIC_SPELLS: frozenset[int] = frozenset({200218, 200219})
GROUND_HASTE_ALLOW: frozenset[int] = frozenset({
    200096,  # mage Meteor: the ground burn is a persistent area aura carrying PERIODIC_DAMAGE, so it ticks hasted
    201200,  # paladin Light's Hammer: AttributesEx5 0x2000 (cloned from a stock ground effect), so it ticks hasted
})


def check_ground_effect_haste(
    entries: list[dict], rows: list[dict], allow: frozenset[int] | set[int] | None = None,
) -> list[str]:
    """WARNING for a custom spell (id >= 200000) with a PERSISTENT_AREA_AURA effect (27) that will tick hasted,
    because the aura effect amplitude is scaled by cast speed when the spell has `AttributesEx5 & 0x2000`
    (SPELL_HASTE_AFFECTS_PERIODIC: stock Blizzard 10 and Rain of Fire 5740 carry it, the clone trap) or an aura that
    `SpellInfo::HasPeriodicDamageOrHealEffect` matches (SpellAuraEffects.cpp:660-680). Fixed-tick ground effects
    (Healing Rain, Earthquake, Blizzard) use the trigger shape instead: a persistent area aura + a PERIODIC_DUMMY
    aura + a script casting one single-target spell per target, which is not hasted and draws the ground kit.
    Spells in `GROUND_HASTE_ALLOW` are exempt (existing effects whose owner has not ruled yet), and so are the core's
    fixed-cadence ids (`FIXED_CADENCE_PERIODIC_SPELLS`, mirroring `IsFixedCadencePeriodic`)."""
    allowed = GROUND_HASTE_ALLOW if allow is None else allow
    warnings = []
    for entry, row in zip(entries, rows):
        spell_id = int(row["ID"])
        if spell_id < _CUSTOM_SPELL_ID_START or spell_id in allowed or spell_id in FIXED_CADENCE_PERIODIC_SPELLS:
            continue
        effects = [(int(row.get(f"Effect_{i}") or 0), int(row.get(f"EffectAura_{i}") or 0)) for i in (1, 2, 3)]
        if not any(effect == _EFFECT_PERSISTENT_AREA_AURA for effect, _ in effects):
            continue
        reasons = []
        if int(row.get("AttributesEx5") or 0) & _SPELL_ATTR5_SPELL_HASTE_AFFECTS_PERIODIC:
            reasons.append("AttributesEx5 has SPELL_HASTE_AFFECTS_PERIODIC (0x2000)")
        carried = {aura for effect, aura in effects if effect in _AURA_EFFECTS}
        hasted_auras = sorted(carried & _PERIODIC_DAMAGE_OR_HEAL_AURAS)
        if hasted_auras:
            reasons.append(
                f"it carries periodic damage/heal aura(s) {hasted_auras} (SpellInfo::HasPeriodicDamageOrHealEffect)"
            )
        if not reasons:
            continue
        warnings.append(
            f"spell {spell_id} ({entry.get('name', '?')}): a persistent area aura that ticks hasted - "
            f"{' and '.join(reasons)}, so every cast-speed point shortens its period (and adds ticks). For a "
            f"fixed cadence use the trigger shape: PERSISTENT_AREA_AURA (dummy aura) + a PERIODIC_DUMMY aura on the "
            f"caster + a script casting one single-target spell per target, with no 0x2000 and no periodic "
            f"damage/heal aura on this spell. Do not clone Blizzard 10 or Rain of Fire 5740. If the haste is "
            f"intended, add the id to lint.GROUND_HASTE_ALLOW."
        )
    return warnings


# --- check_spell_proc_rows (P0 REPORT s3, the 202766 deviation) ---

# SpellMgr.h ProcFlags (PROC_FLAG_*), copied: a lint must not import the engine header, and the values are fixed.
_PROC_DONE_MELEE_AUTO_ATTACK = 0x00000004
_PROC_TAKEN_MELEE_AUTO_ATTACK = 0x00000008
_PROC_DONE_SPELL_MELEE_DMG_CLASS = 0x00000010
_PROC_TAKEN_SPELL_MELEE_DMG_CLASS = 0x00000020
_PROC_DONE_RANGED_AUTO_ATTACK = 0x00000040
_PROC_TAKEN_RANGED_AUTO_ATTACK = 0x00000080
_PROC_DONE_SPELL_RANGED_DMG_CLASS = 0x00000100
_PROC_TAKEN_SPELL_RANGED_DMG_CLASS = 0x00000200
_PROC_DONE_SPELL_NONE_DMG_CLASS_POS = 0x00000400
_PROC_TAKEN_SPELL_NONE_DMG_CLASS_POS = 0x00000800
_PROC_DONE_SPELL_NONE_DMG_CLASS_NEG = 0x00001000
_PROC_TAKEN_SPELL_NONE_DMG_CLASS_NEG = 0x00002000
_PROC_DONE_SPELL_MAGIC_DMG_CLASS_POS = 0x00004000
_PROC_TAKEN_SPELL_MAGIC_DMG_CLASS_POS = 0x00008000
_PROC_DONE_SPELL_MAGIC_DMG_CLASS_NEG = 0x00010000
_PROC_TAKEN_SPELL_MAGIC_DMG_CLASS_NEG = 0x00020000
_PROC_DONE_PERIODIC = 0x00040000
_PROC_TAKEN_PERIODIC = 0x00080000
_PROC_DONE_TRAP_ACTIVATION = 0x00200000
_PROC_DONE_MAINHAND_ATTACK = 0x00400000
_PROC_DONE_OFFHAND_ATTACK = 0x00800000
SPELL_PROC_FLAG_MASK = (
    _PROC_DONE_SPELL_MELEE_DMG_CLASS | _PROC_TAKEN_SPELL_MELEE_DMG_CLASS
    | _PROC_DONE_RANGED_AUTO_ATTACK | _PROC_TAKEN_RANGED_AUTO_ATTACK
    | _PROC_DONE_SPELL_RANGED_DMG_CLASS | _PROC_TAKEN_SPELL_RANGED_DMG_CLASS
    | _PROC_DONE_SPELL_NONE_DMG_CLASS_POS | _PROC_TAKEN_SPELL_NONE_DMG_CLASS_POS
    | _PROC_DONE_SPELL_NONE_DMG_CLASS_NEG | _PROC_TAKEN_SPELL_NONE_DMG_CLASS_NEG
    | _PROC_DONE_SPELL_MAGIC_DMG_CLASS_POS | _PROC_TAKEN_SPELL_MAGIC_DMG_CLASS_POS
    | _PROC_DONE_SPELL_MAGIC_DMG_CLASS_NEG | _PROC_TAKEN_SPELL_MAGIC_DMG_CLASS_NEG
    | _PROC_DONE_PERIODIC | _PROC_TAKEN_PERIODIC | _PROC_DONE_TRAP_ACTIVATION
)
DONE_HIT_PROC_FLAG_MASK = (
    _PROC_DONE_MELEE_AUTO_ATTACK | _PROC_DONE_RANGED_AUTO_ATTACK
    | _PROC_DONE_SPELL_MELEE_DMG_CLASS | _PROC_DONE_SPELL_RANGED_DMG_CLASS
    | _PROC_DONE_SPELL_NONE_DMG_CLASS_POS | _PROC_DONE_SPELL_NONE_DMG_CLASS_NEG
    | _PROC_DONE_SPELL_MAGIC_DMG_CLASS_POS | _PROC_DONE_SPELL_MAGIC_DMG_CLASS_NEG
    | _PROC_DONE_PERIODIC | _PROC_DONE_TRAP_ACTIVATION | _PROC_DONE_MAINHAND_ATTACK | _PROC_DONE_OFFHAND_ATTACK
)
REQ_SPELL_PHASE_PROC_FLAG_MASK = SPELL_PROC_FLAG_MASK & DONE_HIT_PROC_FLAG_MASK

# Declared spell_proc rows that fail LoadSpellProcs' checks today (SpellId -> why it is accepted), found by the run
# that introduced this lint. Each logs an error at boot; the owner triages whether the row was meant.
_PROC_PHASE_UNUSED = (
    "SpellPhaseMask 2 on taken-only ProcFlags: the phase is ignored (SpellMgr.cpp:917 checks it only for done-hit "
    "flags), the proc still fires, boot logs 'won't be used'"
)
SPELL_PROC_ALLOW: dict[int, str] = {
    -17106: "druid Intensity: ProcFlags 0 on purpose, it neutralises the stock Enrage-rage proc (druid_talents.py)",
    20098: "paladin Anticipation: " + _PROC_PHASE_UNUSED,
    -20127: "paladin Redoubt: " + _PROC_PHASE_UNUSED,
    -53590: "paladin Touched by the Light: " + _PROC_PHASE_UNUSED,
    201347: "paladin Bulwark of Faith: " + _PROC_PHASE_UNUSED,
    201353: "paladin Avenging Light: " + _PROC_PHASE_UNUSED,
    201354: "paladin Avenging Light: " + _PROC_PHASE_UNUSED,
    201355: "paladin Avenging Light: " + _PROC_PHASE_UNUSED,
    201365: "paladin Shroud of Light: " + _PROC_PHASE_UNUSED,
    201367: "paladin Touched by the Light: " + _PROC_PHASE_UNUSED,
    201374: "paladin Shield of the Templar: " + _PROC_PHASE_UNUSED,
    -30299: "warlock Nether Protection: " + _PROC_PHASE_UNUSED,
}


def check_spell_proc_rows(
    spell_procs: list[dict], spell_rows: dict[int, dict], allow: dict[int, str] | set[int] | None = None,
) -> list[str]:
    """Mirrors the "proc will not be triggered" checks of `SpellMgr::LoadSpellProcs` (SpellMgr.cpp:2112-2117) for
    every declared `spell_proc` row (`procs_on()`), whatever its spell id. The effective ProcFlags is the row's
    value, or the spell's DBC `ProcTypeMask` when the row has 0 (`spell_rows`: spell id -> built or stock row; a
    negative SpellId is a rank chain and is judged on its base id; a spell with no row is not judged on the flags).
    WARNING when
      - the effective ProcFlags is 0 ("doesn't have `ProcFlags` value defined, proc will not be triggered");
      - `SpellPhaseMask` is 0 but ProcFlags intersects REQ_SPELL_PHASE_PROC_FLAG_MASK (SPELL_PROC_FLAG_MASK &
        DONE_HIT_PROC_FLAG_MASK: a done-spell or periodic proc must say CAST, HIT or FINISH): the proc never fires -
        the 202766 deviation (a Flametongue melee-spell proc with phase 0);
      - `SpellPhaseMask` is set but ProcFlags is outside that mask ("won't be used"): LoadSpellProcs logs an error.
    A row whose SpellId is in `allow` is exempt (a dict of id -> reason, or a set). A negative row is judged on its base
    rank's DBC flags only, while the engine re-derives the flags per rank. A proc another row shadows is a different
    failure: see `check_shadowed_spell_procs`."""
    allowed = SPELL_PROC_ALLOW if allow is None else allow
    warnings = []
    for proc in spell_procs:
        spell_id = int(proc["SpellId"])
        if spell_id in allowed or abs(spell_id) in allowed:
            continue
        row = spell_rows.get(abs(spell_id))
        flags = int(proc.get("ProcFlags") or 0)
        inherited = False
        if not flags and row is not None:
            flags = int(row.get("ProcTypeMask") or 0)
            inherited = True
        phase = int(proc.get("SpellPhaseMask") or 0)
        where = f"spell_proc {spell_id}"
        source = " (inherited from the spell's DBC ProcTypeMask)" if inherited else ""
        if not flags:
            if row is not None:
                warnings.append(
                    f"{where}: ProcFlags is 0 and the spell's DBC ProcTypeMask is 0 - LoadSpellProcs logs "
                    f"\"doesn't have `ProcFlags` value defined, proc will not be triggered\". "
                    f"Set ProcFlags in procs_on()."
                )
            continue
        if not phase and flags & REQ_SPELL_PHASE_PROC_FLAG_MASK:
            warnings.append(
                f"{where}: ProcFlags 0x{flags:X}{source} intersects REQ_SPELL_PHASE_PROC_FLAG_MASK "
                f"(0x{REQ_SPELL_PHASE_PROC_FLAG_MASK:X}) but SpellPhaseMask is 0 - LoadSpellProcs logs \"doesn't have "
                f"`SpellPhaseMask` value defined, but it's required ... proc will not be triggered\", so the "
                f"done-spell half never procs (melee auto attacks still do). Set spell_phase_mask (1 CAST, 2 HIT, "
                f"4 FINISH) in procs_on(), or add the id to lint.SPELL_PROC_ALLOW."
            )
        if phase and not flags & REQ_SPELL_PHASE_PROC_FLAG_MASK:
            warnings.append(
                f"{where}: SpellPhaseMask {phase} is set but ProcFlags 0x{flags:X}{source} is outside "
                f"REQ_SPELL_PHASE_PROC_FLAG_MASK (0x{REQ_SPELL_PHASE_PROC_FLAG_MASK:X}) - LoadSpellProcs logs \"has "
                f"`SpellPhaseMask` value defined, but it won't be used\". Drop the phase mask."
            )
    return warnings


# Declared per-rank spell_proc rows that a negative rank-chain row shadows today (SpellId -> why it is accepted). Empty:
# the priest rows found when the lint was written were fixed by remove_spell_proc() of the stock chain rows (10-31 fix A).
SHADOWED_PROC_ALLOW: dict[int, str] = {}


def check_shadowed_spell_procs(
    declared_procs: list[dict], live_procs: list[dict], removed_ids: set[int] | frozenset[int],
    rank_chains: dict[int, list[int]], allow: dict[int, str] | set[int] | None = None,
) -> list[str]:
    """WARNING for a declared per-rank `spell_proc` row that a negative rank-chain row in the final set shadows.
    `SpellMgr::LoadSpellProcs` has no ORDER BY, so rows load in primary-key order and a negative `-first_rank` row
    (negative SpellId = every rank) loads before every positive one; it claims all ranks, and the later row for a
    rank of that chain is discarded ("listed in `spell_proc` has duplicate entry", SpellMgr.cpp:2068-2072). The
    declared row never takes effect.

    `declared_procs`: the registry's rows. `live_procs`: the live `spell_proc` rows (base dump + migrations + pending,
    `SpellTableIndex.live_rows`). `removed_ids`: SpellIds a `remove_spell_proc()` or the prune pass deletes this run
    (they leave the final set). `rank_chains`: spell id -> chain, first rank first (`spell_ranks` chains plus the
    talent rank chains; a spell absent from it is its own first rank). The final set is the live rows minus the
    removed ones, with the declared rows over them. Fix: `remove_spell_proc(-first_rank)`, or declare the row on the
    chain key (`-first_rank`) instead."""
    allowed = SHADOWED_PROC_ALLOW if allow is None else allow
    declared_keys = {int(p["SpellId"]) for p in declared_procs}
    negative_firsts = {
        -int(r["SpellId"]) for r in live_procs
        if int(r["SpellId"]) < 0 and int(r["SpellId"]) not in removed_ids and int(r["SpellId"]) not in declared_keys
    } | {-key for key in declared_keys if key < 0}
    warnings = []
    for proc in declared_procs:
        spell_id = int(proc["SpellId"])
        if spell_id <= 0 or spell_id in allowed:
            continue
        chain = rank_chains.get(spell_id)
        first = int(chain[0]) if chain else spell_id
        if first not in negative_firsts:
            continue
        warnings.append(
            f"spell_proc {spell_id}: shadowed by the rank-chain row -{first} (negative SpellId = every rank of "
            f"{first}'s chain). LoadSpellProcs loads the negative row first and drops this one as a duplicate, so it "
            f"never takes effect. remove_spell_proc(-{first}), or declare the proc on -{first} instead."
        )
    return warnings


# --- check_trainer_spell_level (T0a s8 SpellLevel moves) ---

# Class-trainer grants whose ReqLevel is below the spell's SpellLevel and that really need a rank for level (SpellId ->
# why it is accepted). Empty: the two hits the first version printed (Savage Bite, Deep Freeze) were attacks, which the
# rank-selection filter below no longer judges.
TRAINER_SPELL_LEVEL_ALLOW: dict[int, str] = {}

# Implicit targets of a friendly effect: the approximation of SpellInfo::IsPositiveEffect used below (the engine derives
# it from the targets and the aura; an effect aimed at the caster, an ally, the party or the raid is positive).
_FRIENDLY_TARGETS = frozenset({1, 3, 4, 5, 20, 21, 27, 30, 31, 33, 34, 35, 37, 45, 56, 57, 58, 59, 61})
_RANK_SELECT_EFFECTS = frozenset({6, 35, 65})  # APPLY_AURA, APPLY_AREA_AURA_PARTY, APPLY_AREA_AURA_RAID
_SPELL_ATTR0_COOLDOWN_ON_EVENT = 0x02000000
_SPELL_ATTR2_ALLOW_LOW_LEVEL_BUFF = 0x00000008
_SPELL_ATTR3_ONLY_PROC_ON_CASTER = 0x08000000


def _needs_aura_rank_selection(row: dict) -> bool:
    """`SpellInfo::GetAuraRankForLevel` (SpellInfo.cpp:2989-3014) only acts on a spell with a positive APPLY_AURA /
    AREA_AURA_PARTY / AREA_AURA_RAID effect, and returns the spell unchanged for COOLDOWN_ON_EVENT,
    ALLOW_LOW_LEVEL_BUFF and ONLY_PROC_ON_CASTER spells. Positive is approximated from the effect's implicit
    target A."""
    if (
        int(row.get("Attributes") or 0) & _SPELL_ATTR0_COOLDOWN_ON_EVENT
        or int(row.get("AttributesEx2") or 0) & _SPELL_ATTR2_ALLOW_LOW_LEVEL_BUFF
        or int(row.get("AttributesEx3") or 0) & _SPELL_ATTR3_ONLY_PROC_ON_CASTER
    ):
        return False
    return any(
        int(row.get(f"Effect_{i}") or 0) in _RANK_SELECT_EFFECTS
        and int(row.get(f"ImplicitTargetA_{i}") or 0) in _FRIENDLY_TARGETS
        for i in (1, 2, 3)
    )


def check_trainer_spell_level(
    trainer_spells: list[dict], spell_rows: dict[int, dict], class_trainer_ids: set[int] | frozenset[int],
    allow: dict[int, str] | set[int] | None = None,
) -> list[str]:
    """WARNING for a declared `trained_by()` row on a class trainer (`class_trainer_ids`: `PRICED_TRAINER_IDS` plus
    every `trainer` of Type 0) whose `ReqLevel` is below the spell's `SpellLevel` (`spell_rows`: spell id -> built
    row, else the stock/live row; a spell with no row is not judged). `SpellInfo::GetAuraRankForLevel`
    (SpellInfo.cpp:3023-3032) returns no rank when the target's level + 10 is below SpellLevel, so a single-rank buff
    such as Bloodlust at SpellLevel 70 learned at 60 fails on lower-level group members. Only spells that go through
    rank selection are judged (`_needs_aura_rank_selection`: a friendly APPLY_AURA / area-aura effect and none of the
    three exempting attributes): an attack or a stun never reaches it, and SpellLevel's other effect, seeding a cast's
    initial threat (Spell.cpp:5802), is negligible. Move SpellLevel down with the learn level (a `spell()` edit), or
    add the spell to `TRAINER_SPELL_LEVEL_ALLOW`."""
    allowed = TRAINER_SPELL_LEVEL_ALLOW if allow is None else allow
    warnings = []
    for row in trainer_spells:
        trainer_id, spell_id, req_level = int(row["TrainerId"]), int(row["SpellId"]), int(row["ReqLevel"])
        if trainer_id not in class_trainer_ids or spell_id in allowed:
            continue
        spell = spell_rows.get(spell_id)
        spell_level = int(spell.get("SpellLevel") or 0) if spell is not None else 0
        if req_level >= spell_level or not _needs_aura_rank_selection(spell):
            continue
        warnings.append(
            f"trained_by(spell {spell_id}, trainer {trainer_id}, req_level {req_level}): the spell's SpellLevel is "
            f"{spell_level}, above the learn level - SpellInfo::GetAuraRankForLevel returns no rank for a target "
            f"below SpellLevel - 10, so a buff learned this early fails on lower-level group members. Lower "
            f"SpellLevel to {req_level} with a spell() edit, or add the spell to lint.TRAINER_SPELL_LEVEL_ALLOW."
        )
    return warnings
