"""
Warlock - "SB units" scaling helper (DEMONOLOGY.md §3.3, §4.0; PLAN B3 / SYSTEMS §16).

Leading underscore = not loaded as a class file by lib/dsl/registry.py's load_class_package (see
source/classes/README.md), just an importable module - `from ._scaling import sb_units`.

Created by Demonology's WP-0. Every new Demonology damage value is expressed as a multiple `k` of
Shadow Bolt 686's own live scaling (`warlock_spells.py`'s `shadow_bolt_686`), so it is exact at
level 60 by construction (PLAN B3's anchor) and follows Shadow Bolt's own curve to 80 - a later
Shadow Bolt retune rescales every row derived from this file on the next `generate.py`, with no
per-row edit. Destruction/Affliction may import this file too if they need SB units (DEMONOLOGY.md
§10).
"""

# Shadow Bolt 686's own base_points / points_per_level / die_sides / EffectBonusMultiplier_1
# (warlock_spells.py:129-146, re-verified against the live DSL row 2026-09-28).
SB_BASE_POINTS = 11
SB_PPL = 7.966101694915254
SB_DIE = 5
SB_COEF = 0.857


def sb_units(k: float, learn_level: int, lo60: int, hi60: int) -> tuple[int, float, int]:
    """B3 + SYSTEMS §16: returns (base_points, points_per_level, die_sides) so the value is k x
    Shadow Bolt at every level, anchored to the spec's level-60 range [lo60, hi60]. The engine adds
    int((level - learn_level) x ppl) to base_points and rolls 1..die_sides (SpellInfo.cpp:410-449).
    """
    ppl = k * SB_PPL
    base_points = lo60 - 1 - int((60 - learn_level) * ppl)
    die_sides = hi60 - lo60 + 1
    return base_points, ppl, die_sides
