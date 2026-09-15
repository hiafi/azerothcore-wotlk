#!/usr/bin/env python3
"""
One-time CSV/YAML -> DSL converter - Phase 4 of `.agents/plans/spell-source-dsl/
spell-source-dsl.PLAN.md`.

Reads one class's existing `source/spells/<class>.csv` +
`source/spells/<class>_talents.csv` + `source/talents/<class>.yaml` (via the
exact same `lib.source` loaders `generate.py` already uses) and writes an
equivalent `source/classes/<class>.py` DSL file. Purely mechanical and
lossless-by-construction:
  - every scalar field is only emitted when it differs from that DSL
    dataclass's own default (see `*_DEFAULTS` below, transcribed from
    `lib/dsl/model.py`) - so an omitted kwarg and an explicit
    default-valued one produce byte-identical `to_entry()` output;
  - `raw_overrides`/`depends_on` dicts round-trip via `repr()` - Python's
    dict repr is already valid Python literal syntax for the JSON-compatible
    values these ever hold (str/int/float/bool/None/list/dict), so there's
    no hand-rolled literal-rendering logic to get subtly wrong.

**Not** meant to produce hand-authored-quality code on the first pass - long
`raw_overrides`/description-string lines stay on one line rather than being
wrapped, and no attempt is made to translate raw ints back into
`lib.dsl.constants` enum names (e.g. `school=16` stays `school=16`, not
`school=School.FROST`) - that's a worthwhile follow-up a human can do
incrementally once real code exists to look at, not something to get
mechanically right in one pass. **Always run `verify_dsl_migration.py`
before trusting or committing this script's output** - see that script's
docstring for why a row-level rebuild-and-diff is the actual safety net
here, not this script's own logic.

Usage: python3 apps/dbc-tools/csv_to_dsl.py <class>
Writes source/classes/<class>.py. Does NOT touch or delete the old
source/spells/<class>*.csv / source/talents/<class>.yaml files.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_ROOT))

from lib import source  # noqa: E402

SOURCE_DIR = TOOL_ROOT / "source"
CLASSES_DIR = SOURCE_DIR / "classes"

# Transcribed from lib/dsl/model.py's dataclass field defaults - see this
# file's own docstring for why matching these exactly is the correctness
# invariant the whole converter leans on.
EFFECT_DEFAULTS = {
    "base_points": 0, "points_per_level": 0.0, "die_sides": 1, "mechanic": 0,
    "implicit_target_a": 0, "implicit_target_b": 0, "apply_aura": 0, "amplitude": 0,
    "misc_value": 0, "trigger_spell": 0, "chain_targets": 0, "radius_yards": None,
}
SPELL_SCALAR_DEFAULTS = {
    "school": 0, "dispel": 0, "mechanic": 0, "attributes": 0, "category": 0,
    "cast_time_ms": None, "cooldown_ms": None, "category_cooldown_ms": None,
    "power_type": 0, "mana_cost": None, "mana_cost_pct": None,
    "range_yards": None, "radius_yards": None, "duration_ms": None,
}
TAB_DEFAULTS = {"class_mask": 0, "pet_talent_mask": 0, "order_index": 0, "spell_icon_id": 0}
SLA_DEFAULTS = {"class_mask": 0, "race_mask": 0, "min_skill_line_rank": 1}


def _slug(name: str, id_: int) -> str:
    """A unique, valid Python identifier for one spell/tab - `<slugified
    name>_<id>`. The `_<id>` suffix alone already guarantees uniqueness (IDs
    are unique by construction), so no collision-detection is needed even
    though several Mage spells share a name (e.g. "Replenish Mana" at
    5405/10052/10057/10058, "Conjure Water" at 5504/10140)."""
    slug = re.sub(r"[^0-9a-zA-Z]+", "_", name).strip("_").lower()
    if not slug or slug[0].isdigit():
        slug = f"s_{slug}"
    return f"{slug}_{id_}"


def _effect_call(effect: dict) -> str:
    parts = [f"type={effect['type']!r}"]
    for key, default in EFFECT_DEFAULTS.items():
        value = effect.get(key)
        if value != default:
            parts.append(f"{key}={value!r}")
    return f"Effect({', '.join(parts)})"


def _spell_call_lines(entry: dict, var: str) -> list[str]:
    lines = [f"{var} = spell("]
    lines.append(f"    id={entry['id']!r},")
    lines.append(f"    name={entry['name']!r},")
    for key, default in SPELL_SCALAR_DEFAULTS.items():
        value = entry.get(key)
        if value != default:
            lines.append(f"    {key}={value!r},")
    # Trim only *trailing* empty slots - a spell whose real data lives in
    # Effect_2 with Effect_1 genuinely empty (e.g. Invisibility, Chilled)
    # must keep that gap as an explicit `None` placeholder, not have it
    # compacted away: `effects` is positional (index 0 = Effect_1), and
    # EffectSpellClassMask{A,B,C}_{1,2,3}'s letter=effect-index convention
    # (see apps/dbc-tools/README.md's gotcha) means silently shifting which
    # slot a real effect lands in is exactly the kind of change that could
    # break a *different* spell's classmask override that targets it by
    # index. Found via Phase 4's real-data verification.
    effects = [entry.get(f"effect{i}") for i in (1, 2, 3)]
    while effects and effects[-1] is None:
        effects.pop()
    if effects:
        lines.append("    effects=[")
        for effect in effects:
            lines.append(f"        {'None' if effect is None else _effect_call(effect)},")
        lines.append("    ],")
    for key in ("spell_icon_id", "spell_weight", "coeff_weight", "notes"):
        value = entry.get(key)
        if value is not None:
            lines.append(f"    {key}={value!r},")
    if entry.get("raw_overrides"):
        lines.append(f"    raw_overrides={entry['raw_overrides']!r},")
    lines.append(")")
    return lines


def _tab_call_lines(entry: dict, var: str, skill_line: int | None) -> list[str]:
    lines = [f"{var} = tab("]
    lines.append(f"    id={entry['id']!r},")
    lines.append(f"    name={entry['name']!r},")
    for key, default in TAB_DEFAULTS.items():
        # entry.get(key, default), not entry.get(key): a YAML entry only has
        # the keys a human actually wrote (unlike a CSV row, which always
        # has every column) - a genuinely-absent key means "use the
        # default", not "explicitly None".
        value = entry.get(key, default)
        if value != default:
            lines.append(f"    {key}={value!r},")
    if skill_line is not None:
        lines.append(f"    skill_line={skill_line!r},")
    if entry.get("raw_overrides"):
        lines.append(f"    raw_overrides={entry['raw_overrides']!r},")
    lines.append(")")
    return lines


def _sla_call_lines(entry: dict, var: str) -> list[str]:
    lines = [f"{var} = skill_line_ability("]
    lines.append(f"    id={entry['id']!r},")
    lines.append(f"    skill_line={entry['skill_line']!r},")
    lines.append(f"    spell_id={entry['spell_id']!r},")
    for key, default in SLA_DEFAULTS.items():
        value = entry.get(key, default)  # see _tab_call_lines's comment on entry.get(key, default)
        if value != default:
            lines.append(f"    {key}={value!r},")
    if entry.get("raw_overrides"):
        lines.append(f"    raw_overrides={entry['raw_overrides']!r},")
    lines.append(")")
    return lines


def _talent_call_lines(
    entry: dict, tab_var: str, rank_vars: list[str], player_castable: bool, sla_ids: list[int | None],
) -> list[str]:
    lines = [f"granted_by_talent("]
    lines.append(f"    id={entry['id']!r},")
    lines.append(f"    tab={tab_var},")
    lines.append(f"    tier={entry['tier']!r},")
    lines.append(f"    column={entry['column']!r},")
    lines.append(f"    ranks=[{', '.join(rank_vars)}],")
    lines.append(f"    player_castable={player_castable!r},")
    if any(s is not None for s in sla_ids):
        lines.append(f"    skill_line_ability_ids={sla_ids!r},")
    depends_on = entry.get("depends_on")
    if depends_on and (depends_on.get("talent_id") or depends_on.get("rank")):
        lines.append(f"    depends_on={dict(depends_on)!r},")
    if entry.get("flags"):
        lines.append(f"    flags={entry['flags']!r},")
    if entry.get("raw_overrides"):
        lines.append(f"    raw_overrides={entry['raw_overrides']!r},")
    lines.append(")")
    return lines


def convert(class_name: str) -> str:
    spells_csv = source.load_one_spell_file(SOURCE_DIR / "spells" / f"{class_name}.csv")
    spells_talents_csv_path = SOURCE_DIR / "spells" / f"{class_name}_talents.csv"
    spells_talents_csv = (
        source.load_one_spell_file(spells_talents_csv_path) if spells_talents_csv_path.is_file() else []
    )
    yaml_path = SOURCE_DIR / "talents" / f"{class_name}.yaml"
    talents_data = source.load_talents_yaml_file(yaml_path) if yaml_path.is_file() else {
        "tabs": [], "talents": [], "skill_line_abilities": [],
    }

    var_by_spell_id: dict[int, str] = {}
    body: list[str] = []

    body.append("# --- spells trained outright (source/spells/%s.csv) ---" % class_name)
    for entry in spells_csv:
        var = _slug(entry["name"], entry["id"])
        var_by_spell_id[entry["id"]] = var
        body.append("\n".join(_spell_call_lines(entry, var)))

    if spells_talents_csv:
        body.append("\n# --- spells granted by a talent point (source/spells/%s_talents.csv) ---" % class_name)
        for entry in spells_talents_csv:
            var = _slug(entry["name"], entry["id"])
            var_by_spell_id[entry["id"]] = var
            body.append("\n".join(_spell_call_lines(entry, var)))

    sla_by_spell_id: dict[int, dict] = {}
    for e in talents_data["skill_line_abilities"]:
        sla_by_spell_id.setdefault(e["spell_id"], e)

    tab_var_by_id: dict[int, str] = {}
    tab_skill_line_by_id: dict[int, int | None] = {}
    for talent_entry in talents_data["talents"]:
        ranks = talent_entry.get("rank_spell_ids") or []
        for rid in ranks:
            sla = sla_by_spell_id.get(rid)
            if sla is not None:
                tab_skill_line_by_id.setdefault(talent_entry["tab_id"], sla["skill_line"])

    if talents_data["tabs"]:
        body.append("\n# --- talent tabs (source/talents/%s.yaml) ---" % class_name)
        for entry in talents_data["tabs"]:
            var = _slug(entry["name"], entry["id"]) + "_tab"
            tab_var_by_id[entry["id"]] = var
            skill_line = tab_skill_line_by_id.get(entry["id"])
            body.append("\n".join(_tab_call_lines(entry, var, skill_line)))

    used_sla_ids: set[int] = set()
    if talents_data["talents"]:
        body.append("\n# --- talents (source/talents/%s.yaml) ---" % class_name)
        for entry in talents_data["talents"]:
            ranks = entry.get("rank_spell_ids") or []
            rank_vars = []
            player_castable = False
            sla_ids: list[int | None] = []
            for rid in ranks:
                sla = sla_by_spell_id.get(rid)
                if sla is not None:
                    player_castable = True
                    sla_ids.append(sla["id"])
                    used_sla_ids.add(sla["id"])
                else:
                    sla_ids.append(None)
                rank_vars.append(var_by_spell_id.get(rid, repr(rid)))
            tab_var = tab_var_by_id[entry["tab_id"]]
            body.append(
                "\n".join(_talent_call_lines(entry, tab_var, rank_vars, player_castable, sla_ids))
            )

    orphan_slas = [e for e in talents_data["skill_line_abilities"] if e["id"] not in used_sla_ids]
    if orphan_slas:
        body.append(
            "\n# --- SkillLineAbility rows not granted by any talent above "
            "(baseline player-castable spells) ---"
        )
        for entry in orphan_slas:
            var = _slug(f"sla_{entry['spell_id']}", entry["id"])
            body.append("\n".join(_sla_call_lines(entry, var)))

    imports = ["from lib.dsl import Effect", "from lib.dsl.registry import spell"]
    if talents_data["talents"]:
        imports.append("from lib.dsl.registry import granted_by_talent, tab")
    elif talents_data["tabs"]:
        imports.append("from lib.dsl.registry import tab")
    if orphan_slas:
        imports.append("from lib.dsl.registry import skill_line_ability")

    header = (
        f'"""\n'
        f"Auto-converted from source/spells/{class_name}*.csv + "
        f"source/talents/{class_name}.yaml by csv_to_dsl.py\n"
        f"({'.agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md'}'s Phase 4) - not yet "
        f"hand-cleaned. See csv_to_dsl.py's docstring for what \"mechanical, not "
        f'hand-authored-quality" means here.\n"""\n\n'
    )
    return header + "\n".join(imports) + "\n\n" + "\n\n".join(body) + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0]} <class>", file=sys.stderr)
        return 2
    class_name = argv[1]
    text = convert(class_name)
    CLASSES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = CLASSES_DIR / f"{class_name}.py"
    out_path.write_text(text, encoding="utf-8")
    print(f"wrote {out_path.relative_to(TOOL_ROOT.parents[1])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
