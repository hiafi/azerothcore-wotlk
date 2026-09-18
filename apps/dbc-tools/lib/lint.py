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
