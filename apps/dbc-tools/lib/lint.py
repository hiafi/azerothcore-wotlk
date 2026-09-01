"""
Sanity checks run over freshly-built spell rows before they're written out.

Currently just one check, but it's its own module (rather than living in
generate.py or build.py) because it's a *content* sanity check on the fully
built row, not part of building the row or deciding whether to emit it.
"""

from __future__ import annotations

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
                    f"all-zero classmask (letter {_LETTERS[i]}) even though this row sets a "
                    f"classmask elsewhere ({masks}) - probably EffectSpellClassMask{_LETTERS[i]}_* "
                    f"needs the value that's on the wrong letter. All-zero here means the engine "
                    f"applies it to every matching spell in the family, not just the intended one."
                )
    return warnings
