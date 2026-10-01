#!/usr/bin/env python3
"""
PLAN P3 step 1: a starting-potency table per class, read from the live DSL (`source/classes/*`)
plus the current, already-live `Spell.dbc`/`spell_bonus_data` state - NOT a generator, this script
writes nothing except its own report files under `.agents/plans/potency-system/`.

For every damage, heal or absorb effect that ISN'T already a potency effect (no `sp_potency`/
`ap_potency`/`weapon_potency` declared), prints:

  - the current level-60 value (`V60`), simulated from the spell's real, live `EffectBasePoints`/
    `EffectRealPointsPerLevel`/`EffectDieSides`/`BaseLevel`/`SpellLevel`/`MaxLevel` - the same
    native-line + average-roll math `SpellEffectInfo::CalcValue` does today, before any potency
    hook exists for this spell;
  - its current coefficient (`spell_bonus_data`'s `direct_bonus`/`dot_bonus`/`ap_bonus`/
    `ap_dot_bonus` when a row exists for this spell - D1: that row replaces the DBC value
    entirely - else the effect's own live `EffectBonusMultiplier_N`);
  - T (cast time or tick amplitude);
  - implied potency from the base (`V60 / (C(60) x T/1.5)`, heal / 3.96 - "dbc-tools generator");
  - implied SP potency from the SP coefficient (`100 x coef x 3.5 / T`, heal / 1.88);
  - implied AP potency from the AP coefficient (`100 x coef x 3.5 x R / T`, R = `potency.DEFAULT_R`,
    the P3-measured value);
  - a mismatch flag when the base-derived and coefficient-derived potencies disagree by more than
    10%.

Per potency-system.HANDOFF.md's P3 extra: "Don't set any potency yourself on a mismatched row. The
user does that at the start of each class pass." This script only reports; `docs/potency-system.md`
says the base-damage potency wins by default where a human hasn't overridden it.

Alongside each class's `.md` report, also writes a plain-text `<class>-potency-proposals.txt` -
one editable line per mismatched effect, prefilled with the base-damage potency - so a human can
hand-edit just the numbers they disagree with and hand the file back (`load_proposal_file` reads
it); see `build_proposal_text`'s docstring for the exact format. Once that file exists, rerunning
this script NEVER overwrites it with fresh defaults if its content has changed (a human's edits
look exactly like that) - pass `--force-proposals` to regenerate it anyway (`write_proposal_file`).

Usage: `apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/potency_report.py [class_name] [--force-proposals]`
(omit the class name to report on every class the DSL currently covers).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_ROOT))

from lib import dbcfmt, potency, source, spell_tables, state, trainer_state  # noqa: E402
from lib.dsl import constants as C  # noqa: E402
from lib.dsl import registry as dsl_registry  # noqa: E402

REPO_ROOT = TOOL_ROOT.parents[1]
SOURCE_DIR = TOOL_ROOT / "source"
OUT_DIR = REPO_ROOT / ".agents" / "plans" / "potency-system"

MISMATCH_THRESHOLD = 0.10

# kind -> (is_heal_like, label) - "Periodic effects"/"Healing"/"Damage range" in the design doc.
_KIND_LABELS = {
    "direct": "direct",
    "heal": "heal",
    "periodic": "periodic",
    "heal_periodic": "heal_periodic",
    "absorb": "absorb",
}
_HEAL_LIKE_KINDS = ("heal", "heal_periodic", "absorb")


def classify_effect(effect_type: int, aura_type: int) -> str | None:
    """Mirrors `lib.potency`'s kinds - `None` for anything that isn't a damage/heal/absorb effect
    (dummies, CC, buffs, weapon strikes - weapon_potency's own migration doesn't go through this
    coefficient-based report at all, see docs/potency-system.md's "Weapon attacks")."""
    if effect_type == C.EffectType.SCHOOL_DAMAGE:
        return "direct"
    if effect_type == C.EffectType.HEAL:
        return "heal"
    if effect_type == C.EffectType.APPLY_AURA:
        if aura_type == C.AuraType.PERIODIC_DAMAGE:
            return "periodic"
        if aura_type == C.AuraType.PERIODIC_HEAL:
            return "heal_periodic"
        if aura_type == C.AuraType.SCHOOL_ABSORB:
            return "absorb"
    return None


def native_level60_value(
    base_points: float, points_per_level: float, die_sides: float,
    spell_level: int, base_level: int, max_level: int,
) -> float:
    """Reproduces `SpellEffectInfo::CalcValue`'s native line at level 60, averaged over the
    DieSides roll (`(1 + die_sides) / 2`, same average `irand(1, die_sides)`/`irand(die_sides, 1)`
    both resolve to) - the *current*, pre-potency value, not the potency-hook math in
    `lib.potency.simulate_value` (there is no correction row for a spell this script is reporting
    on - it hasn't been migrated yet)."""
    level = 60
    if max_level and level > max_level:
        level = max_level
    if level < base_level:
        level = base_level
    level -= max(base_level, spell_level)
    value = base_points + int(level * points_per_level)
    if die_sides == 1:
        value += 1
    elif die_sides:
        value += (1 + die_sides) / 2
    return value


def _fmt(x: float | None, digits: int = 1) -> str:
    return "-" if x is None else f"{x:.{digits}f}"


def build_class_report(
    class_name: str, entries: list[dict], existing_spells: dict[int, dict], bonus_rows: dict[int, dict],
) -> tuple[str, int, int, list[dict], int]:
    """Returns (markdown text, row count, mismatch count, mismatched row records, excluded count).
    `mismatched` is for `build_proposal_text` - a record per mismatched effect (spell_id/name/eff/
    proposed_potency), not needed by the markdown table itself."""
    rows: list[str] = []
    mismatched: list[dict] = []
    mismatches = 0
    excluded = 0
    seen_ids: set[int] = set()
    c60 = potency.c_of_level(60)

    for entry in sorted(entries, key=lambda e: e["id"]):
        spell_id = entry["id"]
        if spell_id in seen_ids:
            continue
        seen_ids.add(spell_id)
        live = existing_spells.get(spell_id)
        if live is None:
            continue  # declared in source but not yet resolved into a real live row - skip

        base_level = int(live.get("BaseLevel") or 0)
        spell_level = int(live.get("SpellLevel") or 0)
        max_level = int(live.get("MaxLevel") or 0)
        bonus = bonus_rows.get(spell_id)
        declared_effects = entry.get("effect1"), entry.get("effect2"), entry.get("effect3")

        for idx in (1, 2, 3):
            declared = declared_effects[idx - 1]
            if declared is not None and "_potency" in declared:
                continue  # already a potency effect - nothing to report, it's already migrated
            if declared is not None and declared.get("_potency_excluded"):
                # deliberately out of scope (Effect.potency_excluded, e.g. Conflagrate: a percent-
                # of-other-damage effect whose DBC fields are dead) - not an unreviewed row, so
                # don't print a meaningless implied potency for it or put it in the proposal file.
                excluded += 1
                continue

            effect_type = int(live.get(f"Effect_{idx}") or 0)
            if not effect_type:
                continue
            aura_type = int(live.get(f"EffectAura_{idx}") or 0)
            kind = classify_effect(effect_type, aura_type)
            if kind is None:
                continue

            base_points = float(live.get(f"EffectBasePoints_{idx}") or 0)
            ppl = float(live.get(f"EffectRealPointsPerLevel_{idx}") or 0.0)
            die_sides = float(live.get(f"EffectDieSides_{idx}") or 0)

            is_periodic_like = kind in ("periodic", "heal_periodic")
            if is_periodic_like:
                t_ms = float(live.get(f"EffectAuraPeriod_{idx}") or 0)
            else:
                t_ms = float(entry.get("cast_time_ms") or 1500)
            if not t_ms:
                continue  # can't compute T (e.g. an aura with no real tick) - not reportable

            v60 = native_level60_value(base_points, ppl, die_sides, spell_level, base_level, max_level)
            if v60 <= 0:
                continue  # not a real damage/heal number on this effect (e.g. a pure debuff)

            t = t_ms / 1000.0
            is_heal_like = kind in _HEAL_LIKE_KINDS
            heal_div = potency.HEAL_BASE_MULT if is_heal_like else 1.0
            base_potency = (v60 / (c60 * t / 1.5)) / heal_div

            if bonus is not None:
                coef = float(bonus["dot_bonus" if is_periodic_like else "direct_bonus"] or 0.0)
                ap_coef = float(bonus["ap_dot_bonus" if is_periodic_like else "ap_bonus"] or 0.0)
            else:
                coef = float(live.get(f"EffectBonusMultiplier_{idx}") or 0.0)
                ap_coef = 0.0

            coef_div = potency.HEAL_COEF_MULT if is_heal_like else 1.0
            sp_implied = (100 * coef * 3.5 / t) / coef_div if coef else None
            ap_implied = (100 * ap_coef * 3.5 * potency.DEFAULT_R / t) if ap_coef else None

            mismatch = False
            for implied in (sp_implied, ap_implied):
                if implied is not None and base_potency and abs(implied - base_potency) / abs(base_potency) > MISMATCH_THRESHOLD:
                    mismatch = True
            if mismatch:
                mismatches += 1

            # Proposed potency ("the base-damage potency wins by default", docs/potency-system.md):
            # the base-derived potency is the one this script proposes, since a human hasn't
            # overridden it yet. Re-bake New Base/New Coefficient straight from it so the proposal
            # shows up as a concrete before/after instead of an abstract potency number. Keeps the
            # row's existing SP/AP shape (pure SP, pure AP, or a hybrid split proportional to the
            # current SP:AP implied ratio) rather than guessing a new one.
            proposed_potency = base_potency
            is_ap_only = bool(ap_coef) and not coef
            is_hybrid = bool(coef) and bool(ap_coef)
            if is_ap_only:
                new_sp_potency, new_ap_potency = 0.0, proposed_potency
            elif is_hybrid:
                total_implied = (sp_implied or 0.0) + (ap_implied or 0.0)
                new_sp_potency = proposed_potency * ((sp_implied or 0.0) / total_implied) if total_implied else proposed_potency
                new_ap_potency = proposed_potency - new_sp_potency
            else:
                new_sp_potency, new_ap_potency = proposed_potency, 0.0

            new_resolved = potency.resolve(
                potency.PotencyEffect(
                    sp_potency=new_sp_potency, ap_potency=new_ap_potency, kind=kind, t_ms=t_ms,
                ),
                spell_level=spell_level,
            )
            new_base_cell = f"{new_resolved.level60_value:.0f}"
            new_coef_cell = f"{new_resolved.sp_coefficient:.3f}"
            if new_ap_potency:
                new_coef_cell += f" / {new_resolved.ap_coefficient:.3f}"

            coef_cell = f"{coef:.3f}"
            if ap_coef:
                coef_cell += f" / {ap_coef:.3f}"
            old_potency_cell = f"{base_potency:.1f} / {_fmt(sp_implied)} / {_fmt(ap_implied)}"
            rows.append(
                f"| {spell_id} | {entry.get('name', '')} | {idx} | {kind} | {t:g}s | {v60:.0f} | "
                f"{coef_cell} | {old_potency_cell} | {proposed_potency:.1f} | "
                f"{new_base_cell} | {new_coef_cell} | {'YES' if mismatch else ''} |"
            )
            if mismatch:
                mismatched.append({
                    "spell_id": spell_id, "name": entry.get("name", ""), "eff": idx,
                    "proposed": proposed_potency,
                })

    header = (
        f"# {class_name.capitalize()} starting-potency report\n\n"
        "Generated by `apps/dbc-tools/potency_report.py` (PLAN P3 step 1). Every row is an "
        "existing, not-yet-migrated damage/heal/absorb effect - this is a starting point for "
        "review, not a decision (HANDOFF: \"Don't set any potency yourself on a mismatched row. "
        "The user does that at the start of each class pass\"). `Old Potency` is the potency "
        "implied three ways by the live spell - from its base damage, its SP coefficient, its AP "
        "coefficient (`-` where that coefficient is absent) - and `Mismatch` flags when those "
        "three disagree by more than 10%. `Proposed Potency` is the base-damage potency, since it "
        "wins by default where a human hasn't overridden it (docs/potency-system.md); `New Base`/"
        "`New Coefficient` re-bake the effect from that proposal, so it's visible as a concrete "
        "before/after next to the live `V60 (old)`/`Coefficient (old)` values.\n\n"
        "| Spell | Name | Eff | Kind | T | V60 (old) | Coefficient (old, SP / AP) | "
        "Old Potency (Base / SP Coef / AP Coef) | Proposed Potency | New Base | "
        "New Coefficient (SP / AP) | Mismatch |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|---|\n"
    )
    return header + "\n".join(rows) + "\n", len(rows), mismatches, mismatched, excluded


_PROPOSAL_RE = re.compile(
    r"^(?P<name>.+?)\s*\((?P<id>\d+)\)(?:\s*eff(?P<eff>\d+))?.*?:\s*(?P<value>-?[\d.]+)\s*(?:#.*)?$"
)


def build_proposal_text(mismatched: list[dict]) -> str:
    """Plain-text, hand-editable proposal file: one line per mismatched effect (HANDOFF: "the user
    sets final potencies on warlock's mismatched rows"), prefilled with the base-damage potency
    (`docs/potency-system.md`'s default winner) so editing is "change the numbers you disagree
    with," not "type 40 numbers from scratch." `eff N` is only appended when a spell has more than
    one mismatched effect (e.g. Immolate's periodic tick and direct impact need telling apart;
    single-effect spells don't). No comments - `Name (ID)[ effN]: value` only, nothing else.
    Round-trips through `load_proposal_file` - keep the two in sync."""
    by_spell: dict[int, list[dict]] = {}
    for row in mismatched:
        by_spell.setdefault(row["spell_id"], []).append(row)

    lines = []
    for spell_id in sorted(by_spell):
        spell_rows = sorted(by_spell[spell_id], key=lambda r: r["eff"])
        multi = len(spell_rows) > 1
        for row in spell_rows:
            label = f"{row['name']} ({spell_id})"
            if multi:
                label += f" eff{row['eff']}"
            lines.append(f"{label}: {row['proposed']:.1f}")
    return "\n".join(lines) + "\n"


def load_proposal_file(path: Path) -> dict[tuple[int, int | None], float]:
    """Reads a hand-edited proposal file back - keys are `(spell_id, eff_index_or_None)`, `eff` is
    `None` for a single-effect spell's unlabeled line (matches whichever one mismatched row that
    spell has). Raises on a line that isn't blank, a `#` comment, or a parseable proposal line, so a
    typo is caught here rather than silently dropped."""
    result: dict[tuple[int, int | None], float] = {}
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _PROPOSAL_RE.match(line)
        if not m:
            raise ValueError(f"{path}:{lineno}: can't parse proposal line: {raw!r}")
        spell_id = int(m.group("id"))
        eff = int(m.group("eff")) if m.group("eff") else None
        result[(spell_id, eff)] = float(m.group("value"))
    return result


def write_proposal_file(path: Path, text: str, force: bool = False) -> bool:
    """Writes the proposal file, unless it already exists with content different from `text` and
    `force` isn't set - a human's hand-edited review (exactly what "different from a fresh
    default" looks like) is never silently clobbered by rerunning the report. Returns whether it
    actually wrote."""
    if path.exists() and not force and path.read_text(encoding="utf-8") != text:
        return False
    path.write_text(text, encoding="utf-8")
    return True


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--force-proposals"]
    force_proposals = len(args) != len(sys.argv) - 1
    only_class = args[0] if args else None

    ids_cfg = source.load_ids(SOURCE_DIR / "ids.yaml")
    trainer_index = trainer_state.load_trainer_index()
    spell_table_index = spell_tables.load_spell_table_index()
    existing_group_ids = {key[0] for key in spell_table_index.live_keys("spell_group")}
    shapeshift_index = state.load_stock_rows(dbcfmt.SPELLSHAPESHIFTFORM)
    creature_table_index = spell_tables.load_creature_table_index()
    existing_creature_rows = {int(r["entry"]): r for r in creature_table_index.live_rows("creature_template")}

    dsl_classes = dsl_registry.load_classes_dir(
        SOURCE_DIR / "classes", ids_cfg=ids_cfg, trainer_index=trainer_index,
        existing_group_ids=existing_group_ids, shapeshift_index=shapeshift_index,
        existing_creature_rows=existing_creature_rows,
        creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
        creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS,
    )

    existing_spells = state.load_existing_rows(dbcfmt.SPELL)
    # load_replayed_table_rows, not load_table_rows: plain load_table_rows unions every INSERT
    # ever seen (base dump + migrations) with no DELETE replay, so a spell whose stock
    # spell_bonus_data row was correctly removed by an earlier rework migration would still read
    # as "live" - confirmed hitting this for real (Shadow Bolt 686, Frostbolt 116: both show a
    # stock row via load_table_rows that's long gone from the real live table - verified directly
    # against the dev DB, 0 rows for either). load_replayed_table_rows correctly reproduces the
    # live table's exact row count (1201, confirmed against `SELECT COUNT(*)`).
    bonus_rows = {
        int(r["entry"]): r
        for r in trainer_state.load_replayed_table_rows(
            "spell_bonus_data", spell_tables.SPELL_BONUS_DATA_COLUMNS, ("entry",),
        )
    }

    by_class: dict[str, list[dict]] = {}
    for entry in dsl_classes["spells"]:
        by_class.setdefault(entry.get("_source_class", "unknown"), []).append(entry)

    if only_class and only_class not in by_class:
        print(f"potency_report.py: no class {only_class!r} in source/classes/ (have: {sorted(by_class)})", file=sys.stderr)
        return 2

    classes = [only_class] if only_class else sorted(by_class)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for class_name in classes:
        text, n_rows, n_mismatches, mismatched, n_excluded = build_class_report(
            class_name, by_class.get(class_name, []), existing_spells, bonus_rows
        )
        path = OUT_DIR / f"{class_name}-potency-report.md"
        path.write_text(text, encoding="utf-8")
        proposal_path = OUT_DIR / f"{class_name}-potency-proposals.txt"
        wrote_proposal = write_proposal_file(
            proposal_path, build_proposal_text(mismatched), force=force_proposals
        )
        proposal_note = (
            str(proposal_path) if wrote_proposal
            else f"{proposal_path} KEPT AS-IS (hand-edited; pass --force-proposals to overwrite)"
        )
        print(
            f"{class_name}: {n_rows} effect(s), {n_mismatches} mismatch(es), "
            f"{n_excluded} excluded -> {path}, {proposal_note}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
