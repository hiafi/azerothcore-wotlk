"""
Potency rebase (level60-stat-curve HANDOFF 1.9, LS5b ruling 7, review S5): a few amounts live outside `resolve()` and
were scaled by hand to the rebase's `a` (`potency.SP_BASE_SCALE`, the flat base) and `b` (`potency.SP_COEF_SCALE`, the
power coefficients), or by R (`potency.DEFAULT_R`, attack power per spell power). A refit of a / b / R (HANDOFF 6.1)
regenerates every potency spell but not these, so each one is recomputed here from its stock value and the current
constants and compared with the number in the C++ source or the DSL (both parsed, not imported). A refit then fails
here with the number to write.

    cd apps/dbc-tools && .venv/bin/python3 -m pytest -q lib/test_potency_hand_scaled.py
"""

from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import potency  # noqa: E402

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
SPELL_MAGE = REPO_ROOT / "src/server/scripts/Spells/spell_mage.cpp"
PET_WARLOCK = REPO_ROOT / "src/server/scripts/Pet/pet_warlock_rework.cpp"
MAGE_SPELLS = TOOL_ROOT / "source/classes/mage/mage_spells.py"
MAGE_TRIGGER_SPELLS = TOOL_ROOT / "source/classes/mage/mage_trigger_spells.py"
DK_MINIONS = TOOL_ROOT / "source/classes/deathknight/deathknight_minions.py"

# Stock (pre-rebase) values: the numbers a = b = R = 1 would give.
MANA_SHIELD_SP = 0.8053        # spell_mage_mana_shield's "+80.53% from sp bonus"
MANA_SHIELD_BASE = 119         # Mana Shield 1463 effect 1 base points
MANA_SHIELD_PER_LEVEL = 11.25  # ... and points per level
INCANTERS_SP = 0.15            # spell_mage_incanters_absorption_shield's placeholder spell power factor
INFERNAL_BASE = 166.0          # Infernal melee: two Immolation ticks at 80 (DEMONOLOGY.md 4.0: 83 + 0.1114 x SP)
INFERNAL_SP = 0.2228
ARCANE_OVERLOAD_SP_SHARE = 60  # Arcane Overload 200092 effect 3: spell power share, percent. Shown in 200079's tooltip
                               # ($200092s3%), so a round literal since the GS3 review fix (was round(34 x 0.975 x 0.926 x b) = 59)
GARGOYLE_SP_SHARE_PCT = 100    # Ebon Gargoyle spell power per owner attack power, percent


def _cpp_float(path: Path, pattern: str) -> float:
    """The float literal (`1.23f`) that `pattern`'s single group captures in `path`; exactly one match."""
    matches = re.findall(pattern, path.read_text())
    if len(matches) != 1:
        raise AssertionError(f"{path.name}: expected one match of {pattern!r}, found {len(matches)}")
    return float(matches[0])


def _class_body(source: str, name: str) -> str:
    """The text of C++ `class <name>` up to the next top-level `class ` line."""
    start = source.index(f"class {name} ")
    end = source.find("\nclass ", start + 1)
    return source[start:end if end != -1 else len(source)]


def _dsl_effect_value(path: Path, variable: str, effect_index: int, field: str):
    """Evaluates `<variable> = spell(..., effects=[...])`'s effect `effect_index` keyword `field` from the DSL source,
    with `_potency` bound to `lib.potency` (a file's own constants are not resolved: keep the expression to literals
    and `_potency.*`)."""
    tree = ast.parse(path.read_text(), str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == variable for t in node.targets):
            effects = next(k.value for k in node.value.keywords if k.arg == "effects")
            effect = effects.elts[effect_index]
            expr = next(k.value for k in effect.keywords if k.arg == field)
            return eval(compile(ast.Expression(expr), str(path), "eval"),  # noqa: S307
                        {"__builtins__": {}, "round": round, "_potency": potency})
    raise AssertionError(f"{path.name}: no `{variable} = spell(...)`")


class HandScaledConstantsTest(unittest.TestCase):
    def assertWritten(self, written: float, stock: float, scale: float, places: int, what: str):
        expected = round(stock * scale, places)
        self.assertAlmostEqual(written, expected, places=places,
                               msg=f"{what}: {written} is not stock {stock} x {scale}; write {expected}")

    def test_mana_shield_spell_power_factor(self):
        body = _class_body(SPELL_MAGE.read_text(), "spell_mage_mana_shield")
        written = float(re.search(r"float bonus = ([0-9.]+)f;", body).group(1))
        self.assertWritten(written, MANA_SHIELD_SP, potency.SP_COEF_SCALE, 4, "spell_mage.cpp Mana Shield bonus")

    def test_incanters_absorption_spell_power_factor(self):
        body = _class_body(SPELL_MAGE.read_text(), "spell_mage_incanters_absorption_shield")
        written = float(re.search(r"SpellBaseDamageBonusDone\(SPELL_SCHOOL_MASK_ARCANE\) \* ([0-9.]+)f", body).group(1))
        self.assertWritten(written, INCANTERS_SP, potency.SP_COEF_SCALE, 4, "spell_mage.cpp Incanter's Absorption")

    def test_infernal_melee(self):
        base = _cpp_float(PET_WARLOCK, r"INFERNAL_MELEE_BASE_DAMAGE = ([0-9.]+)f;")
        coefficient = _cpp_float(PET_WARLOCK, r"INFERNAL_MELEE_SP_COEFFICIENT = ([0-9.]+)f;")
        self.assertWritten(base, INFERNAL_BASE, potency.SP_BASE_SCALE, 2, "pet_warlock_rework.cpp Infernal base")
        self.assertWritten(coefficient, INFERNAL_SP, potency.SP_COEF_SCALE, 4, "pet_warlock_rework.cpp Infernal SP")

    def test_mana_shield_base(self):
        base = _dsl_effect_value(MAGE_SPELLS, "mana_shield_1463", 0, "base_points")
        per_level = _dsl_effect_value(MAGE_SPELLS, "mana_shield_1463", 0, "points_per_level")
        self.assertEqual(base, round(MANA_SHIELD_BASE * potency.SP_BASE_SCALE))
        self.assertWritten(per_level, MANA_SHIELD_PER_LEVEL, potency.SP_BASE_SCALE, 4, "Mana Shield points per level")

    def test_arcane_overload_spell_power_share(self):
        share = _dsl_effect_value(MAGE_TRIGGER_SPELLS, "arcane_overload_200092", 2, "base_points")
        self.assertEqual(share, ARCANE_OVERLOAD_SP_SHARE)

    def test_gargoyle_spell_power_share(self):
        # Attack power turned into spell power for a spell-potency strike: one point of attack power is worth 1 / R.
        tree = ast.parse(DK_MINIONS.read_text(), str(DK_MINIONS))
        call = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "MINION_SP_SHARE_PCT" for t in n.targets))
        value = eval(compile(ast.Expression(call.args[1]), str(DK_MINIONS), "eval"),  # noqa: S307
                     {"__builtins__": {}, "round": round, "_potency": potency})
        self.assertEqual(value, round(GARGOYLE_SP_SHARE_PCT / potency.DEFAULT_R))


if __name__ == "__main__":
    unittest.main()
