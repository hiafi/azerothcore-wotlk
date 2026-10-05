"""SpellDescriptionVariables.dbc rendering (potency-system.PLAN.md P9, D10).

An entry is a list of `$name=<expr>` lines that a spell's tooltip reads as `$<name>`. Stock example
(entry 167, Frostbolt): `$piercing1=$?s11151[${1.02}][${1}]` ... `$mult=${$<arctic5>*$<piercing3>}`.
The builders here render those lines so a class file never hand-writes a chain. Client rules found
by the P9.0 spike (docs/potency-system.md, "Showing talent bonuses on the tooltip"):

- read another spell's value as `$<id>m<n>`; `$<id>s<n>` inside an entry stops the variable resolving
- `$?s<id>` checks the character knows the spell (a talent rank), so an active aura doesn't matter
- a bare `$<var>` in tooltip text shows as a whole number; put fractions inside `${...}` math

No model import (registry.py and model.py both import this): a spell is anything with an `.id`, a
talent anything with `.rank_spell_ids`, or a bare int.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

LINE_SEPARATOR = "\r\n"  # stock entries use CRLF (P9.0: LF works too)
# No known client limit. The longest stock entry is 368 chars; 1024 is room for a few rank chains.
MAX_ENTRY_LENGTH = 1024
# Entry 1102 with 17-19 char names (`strength_of_faith1`) made the whole chain read 0 in game, where the
# same chain under 3-char names works. The exact client cap is unknown; the longest stock name is 12
# (`opportunity1`), so that is the cap. It counts talent_mult()'s helper suffix.
MAX_NAME_LENGTH = 12

VAR_REF = re.compile(r"\$<(\w+)>")
SPELL_CONDITION_REF = re.compile(r"\$\?[sa](\d+)")
SPELL_VALUE_REF = re.compile(r"\$(\d+)([a-zA-Z])\d?")
DEFINED_NAME = re.compile(r"^\$(\w+)=", re.MULTILINE)
NAME = re.compile(r"^[a-z][a-z0-9_]*$")


def _num(value: float) -> str:
    return f"{value:g}"


def _spell_id(spell) -> int:
    return int(spell) if isinstance(spell, int) else int(spell.id)


def _expr(value) -> str:
    """A `[then]`/`[else]` branch or product factor: a number, or an expression string written as
    it would appear inside `${...}` (e.g. `"$<base>*1.2"`)."""
    return _num(value) if isinstance(value, (int, float)) else str(value)


class TooltipExpr:
    """A builder result. `render(name)` returns the `(variable, right-hand side)` lines it needs,
    the last one defining `name` itself."""

    def render(self, name: str) -> list[tuple[str, str]]:
        raise NotImplementedError


@dataclass(frozen=True)
class _Condition(TooltipExpr):
    kind: str  # "s" (knows spell) or "a" (has aura)
    spell_id: int
    then: object
    else_: object

    def render(self, name):
        return [(name, f"$?{self.kind}{self.spell_id}[${{{_expr(self.then)}}}][${{{_expr(self.else_)}}}]")]


def knows(spell, then, else_=1) -> TooltipExpr:
    """`then` when the caster knows `spell` (e.g. a talent rank), else `else_`."""
    return _Condition("s", _spell_id(spell), then, else_)


def has_aura(spell, then, else_=1) -> TooltipExpr:
    """`then` while the caster has `spell`'s aura (e.g. a glyph or a buff), else `else_`."""
    return _Condition("a", _spell_id(spell), then, else_)


@dataclass(frozen=True)
class _TalentMult(TooltipExpr):
    rank_ids: tuple[int, ...]
    effect: int

    def render(self, name):
        lines = []
        fallback = "1"
        for i, rank_id in enumerate(self.rank_ids, start=1):
            var = name if i == len(self.rank_ids) else f"{name}{i}"
            lines.append((var, f"$?s{rank_id}[${{${rank_id}m{self.effect}*0.01+1}}][${{{fallback}}}]"))
            fallback = f"$<{var}>"
        return lines


def talent_mult(talent, effect: int = 1) -> TooltipExpr:
    """1 + (the highest known rank's effect `effect` value) / 100, so a "+X% damage" talent becomes
    a multiplier. `talent` is a `talent(...)` object or its rank spells in rank order. Each rank's
    value is read from the rank spell itself (`$<id>m<n>`), so retuning the talent updates the
    tooltip. Rank 1..n-1 helper lines are named `<name>1`..`<name><n-1>`."""
    ranks = getattr(talent, "rank_spell_ids", talent)
    if isinstance(ranks, (int, str)) or not isinstance(ranks, Sequence) or not ranks:
        raise ValueError("talent_mult(): pass a talent(...) object or a non-empty list of rank spells")
    if effect not in (1, 2, 3):
        raise ValueError(f"talent_mult(): effect must be 1, 2 or 3, got {effect!r}")
    return _TalentMult(tuple(_spell_id(r) for r in ranks), effect)


@dataclass(frozen=True)
class _Product(TooltipExpr):
    factors: tuple

    def render(self, name):
        return [(name, "${" + "*".join(_factor(f) for f in self.factors) + "}")]


def _factor(value) -> str:
    if isinstance(value, str) and NAME.match(value):
        return f"$<{value}>"  # a variable declared earlier in the same entry
    return _expr(value)


def product(*factors) -> TooltipExpr:
    """Multiply variables (by name) and/or numbers: `product("piercing", "arctic")`."""
    if len(factors) < 2:
        raise ValueError("product(): pass at least two factors")
    return _Product(tuple(factors))


@dataclass(frozen=True)
class TooltipVars:
    """What `tooltip_vars()` returns; pass it to `spell(tooltip_vars=...)`."""

    id: int
    names: frozenset[str]
    text: str


def render_entry(entry_id: int, variables: dict) -> TooltipVars:
    """Renders `variables` (name -> builder result, or a raw right-hand-side string such as
    `"${$m1*2}"`) into one entry, in declaration order. Raises on a bad name, a duplicate name, a
    reference to a variable not defined earlier, an `$<id>s<n>` read, an over-long name or an over-long
    entry."""
    if not variables:
        raise ValueError(f"tooltip_vars({entry_id}): declare at least one variable")
    lines: list[tuple[str, str]] = []
    for name, value in variables.items():
        if not NAME.match(name):
            raise ValueError(f"tooltip_vars({entry_id}): variable name {name!r} must be lowercase "
                             "letters, digits and underscores, starting with a letter")
        lines += value.render(name) if isinstance(value, TooltipExpr) else [(name, str(value))]

    defined: set[str] = set()
    for var, rhs in lines:
        if len(var) > MAX_NAME_LENGTH:
            raise ValueError(f"tooltip_vars({entry_id}): variable ${var} is {len(var)} chars, over the "
                             f"{MAX_NAME_LENGTH} limit (a longer name reads 0 in the client) - shorten it")
        if var in defined:
            raise ValueError(f"tooltip_vars({entry_id}): variable ${var} is defined twice "
                             "(a talent_mult() chain also defines <name>1, <name>2, ...)")
        for ref in VAR_REF.findall(rhs):
            if ref not in defined:
                raise ValueError(f"tooltip_vars({entry_id}): ${var} uses $<{ref}>, which isn't "
                                 "defined earlier in the entry")
        for spell_id, letter in SPELL_VALUE_REF.findall(rhs):
            if letter in "sS":
                raise ValueError(f"tooltip_vars({entry_id}): ${var} reads ${spell_id}{letter}...; inside an "
                                 f"entry use ${spell_id}m<n> instead (an s read stops the variable resolving, "
                                 "P9.0 spike)")
        defined.add(var)

    text = LINE_SEPARATOR.join(f"${var}={rhs}" for var, rhs in lines)
    if len(text) > MAX_ENTRY_LENGTH:
        raise ValueError(f"tooltip_vars({entry_id}): rendered entry is {len(text)} chars, over the "
                         f"{MAX_ENTRY_LENGTH} limit - split it or simplify the chains")
    return TooltipVars(entry_id, frozenset(defined), text)


def defined_names(text: str) -> set[str]:
    """Variable names an entry's text defines (stock or declared)."""
    return set(DEFINED_NAME.findall(text.replace("\r\n", "\n")))
