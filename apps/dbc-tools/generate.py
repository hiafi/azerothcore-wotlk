#!/usr/bin/env python3
"""
DBC build pipeline — forward generator.

Reads source/ids.yaml, every file under source/spells/*.csv and
source/talents/*.yaml (legacy per-table format, still used by classes not
yet migrated), and source/classes/* (the DSL from .agents/plans/
spell-source-dsl/spell-source-dsl.PLAN.md — one file or a directory of a few
per class; all 9 classes have migrated and split as of that plan's Phase 5 —
see apps/dbc-tools/source/classes/README.md), builds full-width DBC rows,
and produces:
  1. A pending world-DB SQL migration (data/sql/updates/pending_db_world/) —
     load-bearing: this alone is enough for the server (see
     docs/dbc-build-pipeline.md's "Key finding"). Only written if at least
     one table's reserved-block content, or an explicit existing-row edit,
     actually differs from what's already live — see
     lib/resolve.py's `reserved_range_changed` — so a run touching nothing
     of substance (a pure source reorganization, e.g.) prints "nothing to
     emit" instead of a fresh no-op migration every time.
  2. A client patch: loose files under var/dbc-patch/DBFilesClient/ *and* an
     MPQ at var/dbc-patch/patch-Z.mpq — cosmetic-but-necessary, what the
     client actually renders (name, icon, tooltip, talent frame).
  3. The same bytes copied into env/dist/data/dbc/ if that directory exists.

Usage: python3 apps/dbc-tools/generate.py [--no-prune] [--check] [--no-cache] [--rebuild-cache]

  --no-prune       skip the prune pass (rows an earlier run emitted that source/classes/*
                   no longer declares are left live instead of being deleted)
  --check          read-only gate: lints and the generated-header staleness check, no SQL or patch
  --no-cache       do not read or write the on-disk cache of replayed SQL state (var/dbc-tools-cache/)
  --rebuild-cache  ignore what the cache holds, replay everything, and write the cache afresh
  -h, --help       print this message and exit
"""

from __future__ import annotations

import hashlib
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_ROOT))

from lib import build, dbcfile, dbcfmt, lint, mpq_writer, patch_out, resolve, source, sql_out, state  # noqa: E402
from lib import gcd_haste, header_gen, potency_sheet, spell_tables, superseded_ranks  # noqa: E402
from lib import sqlcorpus, trainer_pricing, trainer_state  # noqa: E402
from bootstrap import load_spell_ranks_chains  # noqa: E402
from lib.dsl import registry as dsl_registry  # noqa: E402

KNOWN_FLAGS = {"--no-prune", "--check", "--no-cache", "--rebuild-cache"}

# PLAN P2b step 4: adopted class by class, inside each class's own pass - not a side effect of
# every generate.py run. Extend this tuple when a pass is ready to start generating/relying on its
# own Generated/<Class>Data.h (warlock first, in P4).
CLASSES_WITH_GENERATED_HEADERS = ("warlock", "paladin", "hunter", "shaman", "deathknight", "rogue")
GENERATED_HEADER_DIR = REPO_ROOT / "src" / "server" / "game" / "Entities" / "Unit" / "Generated"
from lib.reuse import ReuseContext  # noqa: E402

SOURCE_DIR = TOOL_ROOT / "source"
BASE_DBC_DIR = state.BASE_DBC_DIR
PENDING_SQL_DIR = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world"

SECONDARY_TABLES = {
    "spellcasttimes": dbcfmt.SPELLCASTTIMES,
    "spellduration": dbcfmt.SPELLDURATION,
    "spellrange": dbcfmt.SPELLRANGE,
    "spellradius": dbcfmt.SPELLRADIUS,
}

# trainer_spell's real columns (data/sql/base/db_world/trainer_spell.sql),
# minus the synthetic "id" lib.dsl.registry.trained_by() adds only for its
# own duplicate-declaration bookkeeping - see Registry's docstring.
TRAINER_SPELL_COLUMNS = (
    "TrainerId", "SpellId", "MoneyCost", "ReqSkillLine", "ReqSkillRank",
    "ReqAbility1", "ReqAbility2", "ReqAbility3", "ReqLevel", "VerifiedBuild",
)


def _tooltip_var_rows(dsl_rows: list[dict]) -> dict[int, dict]:
    """Declared tooltip_vars() entries as SpellDescriptionVariables.dbc rows, keyed by ID. Client-only
    (potency-system.PLAN.md P9): no SQL state to diff against, so every declared row goes into every
    patch build, merged over the stock file like the other client tables."""
    return {e["id"]: {"ID": e["id"], "Variables": e["Variables"]} for e in dsl_rows}


def _spell_category_rows(dsl_rows: list[dict]) -> dict[int, dict]:
    """Declared spell_category() entries as SpellCategory.dbc rows, keyed by ID. The server half is
    the SPELL_TABLES `spellcategory_dbc` delta (spell_tables.py); this is the client half, merged over
    the stock file into the patch on every build like tooltip_vars (Paladin T1, plan defect P1)."""
    return {int(r["ID"]): {"ID": int(r["ID"]), "Flags": int(r["Flags"])} for r in dsl_rows}


def _spell_category_base_error(rows: dict[int, dict], base_dir: Path) -> str | None:
    """Declared categories need the stock SpellCategory.dbc as the patch's base layer; without it
    the client would not know the category (sibling spells stay clickable). None when fine."""
    path = base_dir / dbcfmt.SPELLCATEGORY.dbc_filename
    if rows and not path.is_file():
        return (
            f"spell_category() declared ({', '.join(str(i) for i in sorted(rows))}) but no stock "
            f"{dbcfmt.SPELLCATEGORY.dbc_filename} at {path} - extract DBFilesClient/"
            f"{dbcfmt.SPELLCATEGORY.dbc_filename} from the highest-numbered client patch-enUS MPQ that "
            f"holds it into that directory (see .agents/docs/systems/dbc-tools.md)"
        )
    return None


def _spell_rune_cost_rows(dsl_rows: list[dict]) -> dict[int, dict]:
    """Declared spell_rune_cost() entries as SpellRuneCost.dbc rows, keyed by ID. The server half is the SPELL_TABLES
    `spellrunecost_dbc` delta (spell_tables.py); this is the client half, merged over the stock file into the patch on
    every build like spell_category (Death Knight T1). Column order is Blood, Unholy, Frost (dbcfmt.SPELLRUNECOST)."""
    return {
        int(r["ID"]): {
            "ID": int(r["ID"]), "Blood": int(r["Blood"]), "Unholy": int(r["Unholy"]), "Frost": int(r["Frost"]),
            "RunicPower": int(r["RunicPower"]),
        }
        for r in dsl_rows
    }


def _spell_rune_cost_base_error(rows: dict[int, dict], base_dir: Path) -> str | None:
    """Declared rune costs need the stock SpellRuneCost.dbc as the patch's base layer: without it the client would not
    know the cost and the patch could not carry the row. None when fine."""
    path = base_dir / dbcfmt.SPELLRUNECOST.dbc_filename
    if rows and not path.is_file():
        return (
            f"spell_rune_cost() declared ({', '.join(str(i) for i in sorted(rows))}) but no stock "
            f"{dbcfmt.SPELLRUNECOST.dbc_filename} at {path} - copy it from the worldserver's DBC directory "
            f"(ac-worldserver:/azerothcore/env/dist/data/dbc/{dbcfmt.SPELLRUNECOST.dbc_filename}) into that "
            f"directory (see .agents/docs/systems/dbc-tools.md)"
        )
    return None


def _rune_cost_errors(spell_entries: list[dict], dsl_classes: dict, ids_cfg: dict) -> list[str]:
    """The spell_rune_cost() ERRORs, for `--check` and the full run alike: a spell whose RuneCostID is in the
    spellrunecost block with no declaration, and a declaration with no stock file to merge into."""
    errors = lint.check_undeclared_spell_rune_costs(
        spell_entries, {int(r["ID"]) for r in dsl_classes["spell_rune_costs"]}, ids_cfg.get("spellrunecost"),
    )
    base_error = _spell_rune_cost_base_error(_spell_rune_cost_rows(dsl_classes["spell_rune_costs"]), BASE_DBC_DIR)
    if base_error:
        errors.append(base_error)
    return errors


def _gcd_haste_check_warnings(
    spell_entries: list[dict], talents: dict, dsl_classes: dict, stock_spells: dict[int, dict], ids_cfg: dict,
) -> list[str]:
    """`--check` dry run of the full run's GCD-haste computation (Death Knight T1, step 6): the first P0 deploy
    stopped at `ERROR: gcd haste: ... all-zero SpellClassMask`, which `--check` could not show (the hunter T1-10
    shape). Runs `_gcd_haste_entries` over the *stock* Spell / Talent / TalentTab / SkillLineAbility rows with the
    declared rows laid over them, the superseded-rank map the full run uses, and `trainer_taught` = the declared
    `trained_by()` spells. Everything it finds is a WARNING (it is an approximation: promoted migrations are not
    replayed, so it cannot flip `--check`'s exit code); the full run keeps the authoritative ERRORs. Returns the
    message texts.

    **The superseded-rank map is required, not optional.** The handoff said `superseded={}`; with it the stock
    inputs print six lines on the tree of 2026-10-23 (three Paladin aura bit conflicts, two Hunter melee / ranged bit
    overlaps, Hunter Black Arrow bit 7), because the stock rows still list the ranks the single-rank conversion
    collapsed (Retribution Aura 10298, Mongoose Bite 14269, ...) as learnable. The map (`superseded_ranks`, 2148
    ranks from `spell_ranks` plus the DSL survivors) is cheap and is what the full run passes; with it the committed
    tree prints nothing. Promoted rows were not the cause (a promoted-aware variant printed the same six lines)."""
    stock_secondary = {name: list(state.load_stock_rows(table).values()) for name, table in SECONDARY_TABLES.items()}
    superseded = superseded_ranks.superseded_ranks(
        load_spell_ranks_chains(), superseded_ranks.survivor_ids(dsl_classes["spells"]),
    )
    prefix = "gcd haste (--check, stock approximation): "
    try:
        _entries, result = _gcd_haste_entries(
            spell_entries, talents, dsl_classes["spells"], superseded,
            {int(r["SpellId"]) for r in dsl_classes["trainer_spells"]}, stock_spells,
            state.load_stock_rows(dbcfmt.TALENT), state.load_stock_rows(dbcfmt.TALENTTAB),
            state.load_stock_rows(dbcfmt.SKILLLINEABILITY), stock_secondary, ids_cfg,
        )
    except gcd_haste.GcdHasteError as error:
        return [prefix + str(error)]
    return [prefix + message for message in (*result.errors, *result.warnings)]


def _trainer_spells_to_emit(rows: list[dict], live: dict[tuple[int, int], dict]) -> list[dict]:
    """Drops any priced trainer_spell row that's already live with
    identical values — same "no-op rerun stays a no-op" property the DBC
    tables get from lib/resolve.py's new/edited/unchanged split, just
    reimplemented here since trainer_spell has no reserved-ID-range concept
    for resolve.resolve_rows to key off.

    `live` must be a *replay* (trainer_pricing.replay_trainer_spells), not
    TrainerIndex.existing_trainer_spells's INSERT union: the union ignores
    UPDATE and DELETE, so a row a later file updated or removed still reads
    as its last INSERT."""
    to_emit = []
    for row in rows:
        existing = live.get((row["TrainerId"], row["SpellId"]))
        if existing and all(existing.get(c) == row.get(c) for c in TRAINER_SPELL_COLUMNS):
            continue
        to_emit.append(row)
    return to_emit


def _priced_trainer_spells(dsl_classes: dict, trainer_index: trainer_state.TrainerIndex) -> list[dict]:
    """The trainer_spell rows to emit after applying source/trainer_pricing.py: the live rows of every
    priced trainer plus every trained_by() declaration, priced from the learn-level curve, minus what
    is already live (a replay over all files). Warns about a listed trainer with no live NPC."""
    policy = trainer_pricing.load_policy()
    live = trainer_pricing.replay_trainer_spells()
    removed = {(int(r["TrainerId"]), int(r["SpellId"])) for r in dsl_classes["trainer_removals"]}
    priced_ids, skipped = trainer_pricing.live_priced_trainer_ids(policy, trainer_index)
    for trainer_id, problems in skipped:
        print(f"WARNING: trainer pricing: TrainerId {trainer_id} is in PRICED_TRAINER_IDS but has no live NPC, "
              f"skipped ({'; '.join(problems)})")
    priced = trainer_pricing.priced_trainer_spells(
        dsl_classes["trainer_spells"], live, priced_ids, removed, policy,
    )
    return _trainer_spells_to_emit(priced, live)


def _drop_unchanged_blocks(
    blocks: list[tuple],
) -> tuple[list[tuple[object, dict, list[dict], list[int]]], int]:
    """Filters a `(table, id_range, rows, edited_ids, existing_rows)` list
    (the 5-tuple shape - one extra element, `existing_rows`, over what
    `sql_out.emit_pending_sql` itself wants) down to the 4-tuple shape it
    does want, dropping any table whose block would be a pure no-op -
    re-deleting and re-reinserting exactly what's already live - per
    `lib.resolve.reserved_range_changed`. Returns `(filtered_blocks,
    n_dropped)`.

    Without this, `generate.py` used to emit a fresh, differently-timestamped
    migration touching every table with *any* reserved-block content on
    every single run, regardless of whether that run's source data changed
    it at all - real content is always non-empty for these tables (there's
    always some custom spell/talent/etc.), so in practice a run was close to
    never a true no-op even when nothing had actually changed, making it
    hard to tell "this run has real content changes" apart from "this run
    only reorganized/relabeled source with zero build-output effect" (see
    .agents/plans/spell-source-dsl/spell-source-dsl.PLAN.md's readability
    work, which hit exactly this while confirming a pure file-split changed
    nothing)."""
    filtered = []
    n_dropped = 0
    for table, id_range, rows, edited_ids, existing_rows in blocks:
        if resolve.reserved_range_changed(rows, table.index_column, id_range, edited_ids, existing_rows):
            filtered.append((table, id_range, rows, edited_ids))
        else:
            n_dropped += 1
    return filtered, n_dropped


def _gcd_haste_entries(
    spell_entries: list[dict], talents: dict, dsl_spells: list[dict], superseded: dict[int, int],
    trainer_taught: set[int], existing_spells: dict[int, dict], existing_talents: dict[int, dict],
    existing_talenttabs: dict[int, dict], existing_skilllineabilities: dict[int, dict],
    existing_secondary: dict[str, list[dict]], ids_cfg: dict,
) -> tuple[list[dict], gcd_haste.Result]:
    """melee-haste-gcd T1: the per-class GCD-haste aura entries, computed from the merged spell data (base
    DBC + promoted migrations, with this run's source rows laid over them). See lib/gcd_haste.py. Built with
    a throwaway ReuseContext so no secondary-table row is minted for the comparison alone."""
    policy = gcd_haste.load_policy()
    scratch = ReuseContext(existing_secondary, ids_cfg)
    spells = gcd_haste.merged_spell_rows(
        existing_spells, (build.build_spell_row(e, scratch) for e in spell_entries),
    )
    abilities = {**existing_skilllineabilities}
    abilities.update({int(r["ID"]): r for r in map(build.build_skilllineability_row, talents["skill_line_abilities"])})
    talent_rows = {**existing_talents}
    talent_rows.update({int(r["ID"]): r for r in map(build.build_talent_row, talents["talents"])})
    tab_rows = {**existing_talenttabs}
    tab_rows.update({int(r["ID"]): r for r in map(build.build_talenttab_row, talents["tabs"])})
    learnable = gcd_haste.learnable_spell_ids(
        abilities.values(), talent_rows.values(), gcd_haste.dsl_player_castable_ids(dsl_spells), policy,
        gcd_haste.pet_talent_tab_ids(tab_rows.values()), set(superseded) - trainer_taught,
    )
    result = gcd_haste.compute(spells, learnable, policy, set(superseded) - trainer_taught)
    if result.errors:
        return [], result
    return gcd_haste.aura_entries(result, policy), result


def _pet_skill_lines() -> set[int]:
    """Every skill line a hunter pet family teaches on (CreatureFamily.dbc), or an empty set without the stock
    file (callers add the shared line 270 themselves)."""
    lines: set[int] = set()
    if (BASE_DBC_DIR / dbcfmt.CREATUREFAMILY.dbc_filename).is_file():
        for family_lines in superseded_ranks.family_skill_lines(state.load_stock_rows(dbcfmt.CREATUREFAMILY)).values():
            lines.update(family_lines)
    return lines


def _creature_family_missing_warning(rows: list[dict]) -> str | None:
    """The hunter family lint's rule (d) needs the stock CreatureFamily.dbc to know the pet skill lines; without it
    only line 270 is known. A WARNING line when custom class-set-9 spells exist and the file is missing, else None."""
    if (BASE_DBC_DIR / dbcfmt.CREATUREFAMILY.dbc_filename).is_file():
        return None
    if not any(
        int(row["ID"]) >= lint._CUSTOM_SPELL_ID_START and int(row.get("SpellClassSet") or 0) == 9 for row in rows
    ):
        return None
    return (
        f"WARNING: hunter family lint: no stock {dbcfmt.CREATUREFAMILY.dbc_filename} in "
        f"{BASE_DBC_DIR.relative_to(REPO_ROOT)}, so rule (d) only knows skill line 270 and misses a spell "
        f"taught on a family's own line - copy it from the worldserver's DBC directory "
        f"(ac-worldserver:/azerothcore/env/dist/data/dbc/)"
    )


def _class_trainer_ids() -> set[int]:
    """TrainerIds that teach a class: the priced allow-list (source/trainer_pricing.py) plus every `trainer` row
    of Type 0 (class) in the base dump."""
    ids = set(trainer_pricing.load_policy().priced_ids)
    ids.update(int(r["Id"]) for r in spell_tables.load_base_table_rows("trainer") if int(r["Type"]) == 0)
    return ids


def _proc_shadow_inputs(
    spell_table_index, dsl_classes: dict, talents: dict, existing_talents: dict,
) -> tuple[list[dict], set[int], dict[int, list[int]]]:
    """`(live spell_proc rows, SpellIds deleted this run, rank chains)` for `lint.check_shadowed_spell_procs`. The
    chains are `spell_ranks` (base dump, minus the `unrank_spells()` removals, whose spells are their own first rank)
    overlaid by the talent rank chains (Talent.dbc and the declared talents)."""
    removed_ranks = {int(r["spell_id"]) for r in dsl_classes["spell_rank_removals"]}
    chains: dict[int, list[int]] = {}
    for first, members in load_spell_ranks_chains().items():
        ordered = [spell for spell, _rank in sorted(members, key=lambda m: m[1]) if spell not in removed_ranks]
        for spell in ordered:
            chains[spell] = ordered
    chains.update(lint.build_talent_rank_chains(existing_talents, talents["talents"]))
    removed = {int(r["SpellId"]) for r in dsl_classes["proc_removals"]}
    removed |= {int(key[0]) for key in spell_tables.pruned_keys(spell_table_index, dsl_classes, "spell_proc")}
    # A replay (DELETEs applied), not live_rows(): a union of INSERTs keeps a chain row a later migration deleted
    # (-47580) and would report its per-rank rows as shadowed.
    live = trainer_state.load_replayed_table_rows("spell_proc", spell_tables.SPELL_PROC_COLUMNS, ("SpellId",))
    return live, removed, chains


def _t1_content_warnings(
    dsl_classes: dict, talents: dict, spell_entries: list[dict], built_rows: list[dict], base_spells: dict[int, dict],
    live_skilllineabilities: list[dict], proc_shadow_inputs: tuple | None = None,
) -> list[str]:
    """The shaman-T1 spell-content lints (lib/lint.py), over the full declared population. One function for the
    `--check` block and the full run, so a `--check` session sees what the full run would print (hunter T1-10).
    `built_rows` is every declared entry built (aligned with `spell_entries`); `base_spells` the rows behind them
    (the promoted-aware live Spell.dbc in the full run, the stock client file in `--check`);
    `live_skilllineabilities` the live SkillLineAbility rows (empty in `--check`, which only sees the declared
    ones). `proc_shadow_inputs` is `_proc_shadow_inputs(...)`; without it the shadowed-proc check is skipped."""
    spell_lookup = {**base_spells, **{int(r["ID"]): r for r in built_rows}}
    sla_rows = [
        {"Spell": int(e["spell_id"]), "SkillLine": int(e["skill_line"])} for e in talents["skill_line_abilities"]
    ] + [{"Spell": int(r["Spell"]), "SkillLine": int(r["SkillLine"])} for r in live_skilllineabilities]
    talent_rank_ids = {
        int(rank) for entry in talents["talents"] for rank in (entry.get("rank_spell_ids") or []) if rank
    }
    trainer_spells = dsl_classes["trainer_spells"]
    warnings: list[str] = []
    warnings += lint.check_creature_spell_rows(dsl_classes["creature_template_spells"], set(spell_lookup))
    warnings += lint.check_totem_tools(spell_entries, built_rows, base_spells=base_spells)
    warnings += lint.check_hidden_learned_spells(
        spell_entries, built_rows, sla_rows, {int(r["SpellId"]) for r in trainer_spells}, talent_rank_ids,
        _pet_skill_lines(),
    )
    warnings += lint.check_ground_effect_haste(spell_entries, built_rows)
    warnings += lint.check_spell_proc_rows(dsl_classes["spell_procs"], spell_lookup)
    if proc_shadow_inputs is not None:
        warnings += lint.check_shadowed_spell_procs(dsl_classes["spell_procs"], *proc_shadow_inputs)
    warnings += lint.check_trainer_spell_level(trainer_spells, spell_lookup, _class_trainer_ids())
    # Death Knight T1: spell_threat() / creation_*() reference spells the loader never validates, and the rune-cost
    # lints (RuneCostID without PowerType 5, a free cast, a duplicate of a stock row).
    # (.get: callers that hand-build a partial `dsl_classes`, like the shaman wiring test, declare none of these.)
    warnings += lint.check_spell_threat_rows(dsl_classes.get("spell_threats", []), set(spell_lookup))
    warnings += lint.check_creation_rows(
        dsl_classes.get("creation_actions", []), dsl_classes.get("creation_casts", []), set(spell_lookup),
    )
    rune_costs = dsl_classes.get("spell_rune_costs", [])
    rune_cost_file = BASE_DBC_DIR / dbcfmt.SPELLRUNECOST.dbc_filename
    warnings += lint.check_spell_rune_costs(
        spell_entries, built_rows, state.load_stock_rows(dbcfmt.SPELLRUNECOST) if rune_cost_file.is_file() else None,
        rune_costs,
    )
    return warnings


def _merge_npc_declarations(dsl_classes: dict, dsl_npcs: dict, source_dir: str = "source/npcs/") -> None:
    """Fold a non-class source directory's declarations (`source/npcs/*.py`, `source/world/*.py` -
    loaded by the same `load_classes_dir`) into the class registry's merged dict, in place. Lists
    concatenate; the two var-name dicts update. An entry declared in both places (any merged key) is
    an error, like a duplicate within one directory."""
    for key in dsl_registry.MERGE_KEYS:
        declared = {entry.get("_dedup_id", entry.get("id")) for entry in dsl_classes[key]}
        for entry in dsl_npcs[key]:
            dedup_id = entry.get("_dedup_id", entry.get("id"))
            if dedup_id in declared:
                raise dsl_registry.DuplicateIdError(
                    f"{key} entry {dedup_id!r} appears in both {source_dir} and an earlier source directory"
                )
    for key, value in dsl_npcs.items():
        if isinstance(value, dict):
            dsl_classes[key].update(value)
        else:
            dsl_classes[key].extend(value)


def _merge_dsl_sources(spell_entries: list[dict], talents: dict, dsl_classes: dict) -> None:
    """Append source/classes/*.py's DSL-declared spells/talents/tabs/
    skill_line_abilities into the CSV/YAML-loaded lists, in place — the
    dual-support transition period from spell-source-dsl.PLAN.md's Phase 1.
    Each source format already checked for duplicate IDs *within* itself
    (load_spells_csv, load_talents_yaml, load_classes_dir all raise their
    own DuplicateIdError for that); this only needs to catch an ID declared
    in *both* formats, which none of those individually-scoped checks can
    see."""
    seen_spell_ids = {e["id"]: e.get("_source_file", "<csv>") for e in spell_entries}
    for entry in dsl_classes["spells"]:
        if entry["id"] in seen_spell_ids:
            raise source.DuplicateIdError(
                f"spell ID {entry['id']} appears in both {seen_spell_ids[entry['id']]!r} "
                f"(source/spells/*.csv) and a source/classes/*.py DSL file"
            )
        spell_entries.append(entry)
    for key in ("tabs", "talents", "skill_line_abilities"):
        seen_ids = {e["id"] for e in talents[key]}
        for entry in dsl_classes[key]:
            if entry["id"] in seen_ids:
                raise source.DuplicateIdError(
                    f"{key} entry ID {entry['id']} appears in both source/talents/*.yaml "
                    f"and a source/classes/*.py DSL file"
                )
            talents[key].append(entry)


def main() -> int:
    # No argparse - hand-checked so an unknown flag (e.g. --help before this existed) can't
    # silently fall through into a full multi-minute run that writes a pending SQL migration.
    args = sys.argv[1:]
    if "-h" in args or "--help" in args:
        print(__doc__.strip())
        return 0
    unknown = [a for a in args if a not in KNOWN_FLAGS]
    if unknown:
        print(f"generate.py: unknown argument(s): {' '.join(unknown)} (see --help)", file=sys.stderr)
        return 2

    corpus = sqlcorpus.activate(
        None if "--no-cache" in args else CACHE_DIR, cache_code_version(), rebuild="--rebuild-cache" in args,
    )
    try:
        return _run(corpus)
    finally:
        sqlcorpus.deactivate()


# The files whose code decides what a cached replay holds: the SQL parser, the corpus, the table loaders and the DBC
# reader. A change to any of them (or to the item overlay's own parser) is a cache miss; an edit to a lint or to the
# DSL is not, since neither feeds a snapshot. `--rebuild-cache` is the escape hatch for anything missed here.
CACHE_DIR = REPO_ROOT / "var" / "dbc-tools-cache"
CACHE_CODE_FILES = (
    "sqlcorpus.py", "sql_dump.py", "dbcfile.py", "dbcfmt.py", "state.py", "trainer_state.py", "spell_tables.py",
    "trainer_pricing.py",
)


def cache_code_version() -> str:
    h = hashlib.sha256()
    h.update(sqlcorpus.code_version([REPO_ROOT / "apps" / "item-tools" / "item_lib"]).encode())
    for name in CACHE_CODE_FILES:
        h.update(name.encode())
        h.update((TOOL_ROOT / "lib" / name).read_bytes())
    return h.hexdigest()[:24]


def _cache_summary(corpus: sqlcorpus.Corpus) -> str:
    stats = corpus.stats
    return f"{stats['hit']} hit, {stats['extend']} extended, {stats['miss']} miss, {stats['corrupt']} corrupt"


def _run(corpus: sqlcorpus.Corpus) -> int:
    start = time.monotonic()

    def progress(label: str) -> None:
        # Several of the steps below have no output of their own and can run for minutes on a
        # full-size source tree (a bare CLI run can otherwise look identical to a hang) - see
        # docs/bugs-and-fixes.md's "generate.py looks hung but is CPU-bound" entry. flush=True since
        # this print is the only signal something is happening, and a piped/redirected run
        # (`generate.py > log.txt`) would otherwise buffer it invisibly until exit.
        print(f"[{time.monotonic() - start:6.1f}s] {label}", flush=True)

    ids_cfg = source.load_ids(SOURCE_DIR / "ids.yaml")
    spell_entries = source.load_spells_csv(SOURCE_DIR / "spells")
    talents = source.load_talents_yaml(SOURCE_DIR / "talents")
    item_entries = source.load_items_csv(SOURCE_DIR / "items.csv")
    progress("loaded source/ (ids.yaml, spells/*.csv, talents/*.yaml, items.csv)")

    # Static scan of creature_default_trainer/creature_template/creature (base +
    # updates/pending_db_world) - lib/dsl/registry.py's trained_by() validates
    # every TrainerId against this before registering a trainer_spell row. See
    # lib/trainer_state.py's docstring for why this needs no live DB connection
    # and for its "union of INSERTs, no DELETE/UPDATE replay" limitation.
    trainer_index = trainer_state.load_trainer_index()
    progress("loaded trainer index")
    # spell_script_names / spell_bonus_data / spell_proc / spell_linked_spell / spell_group / ... -
    # built *before* load_classes_dir below (it needs no dsl_classes input, only what's already
    # on disk) so its already-loaded live data can be reused instead of rescanned - both for
    # existing_group_ids right below, and later for render_removal_blocks's typo guard and the
    # linked_spell collision check (review, 2026-09-23 - see lib/spell_tables.py's SpellTableIndex.
    # live_keys()/live_rows()).
    spell_table_index = spell_tables.load_spell_table_index()
    progress("loaded spell table index (spell_script_names/spell_bonus_data/spell_proc/...)")
    # existing spell_group ids (base dump + migrations) - lib/dsl/registry.py's spell_group()/
    # spell_group_rule() accept a member/rule for one of these even when it's outside
    # ids.yaml's own spell_group block (adding to a stock group like 1054/1016 is legitimate).
    existing_group_ids = {key[0] for key in spell_table_index.live_keys("spell_group")}
    # stock SpellShapeshiftForm rows (base DBC + base SQL) - shapeshift_form() builds a full
    # override row starting from whichever of these form_id names.
    shapeshift_index = state.load_stock_rows(dbcfmt.SPELLSHAPESHIFTFORM)
    # T1 (.agents/plans/warlock-rework/warlock-rework.T1-HANDOFF.md): creature_template/
    # creature_template_model - live creature_template entries (for creature_template()'s "fresh
    # id from the reserved block, or override an entry that already exists" check) plus the
    # column/default data creature_template() needs to build a full row - see
    # lib/spell_tables.py's CREATURE_TABLES module docstring for why this table is loaded via its
    # own SpellTableIndex rather than folded into spell_table_index above (never pruned, upsert-only).
    creature_table_index = spell_tables.load_creature_table_index()
    # Full rows, not just entries - creature_template() needs an overridden entry's *current*
    # values to preserve every column the override doesn't mention (see its own docstring; found
    # missing via code review, 2026-09-28 - a bare id set can't tell "override" from "wipe").
    existing_creature_rows = {int(r["entry"]): r for r in creature_table_index.live_rows("creature_template")}
    progress("loaded creature table index (creature_template/creature_template_model)")
    # Hunter T1: the live data retire_talent() (Talent.dbc rows, base client file + promoted migrations)
    # and item_template() (item_template rows, base dump + every migration incl. itemization_templates_v2/)
    # edit an existing row against - see lib/spell_tables.py's ITEM_TABLES for why items use the item-tools
    # overlay. Like creature_template, item_template is never pruned (upsert-only).
    existing_talents = state.load_existing_rows(dbcfmt.TALENT)
    item_live_rows = spell_tables.load_live_item_template_rows()
    item_table_index = spell_tables.load_item_table_index(item_live_rows)
    # Death Knight T1: override_skill_line_ability() edits a live SkillLineAbility row and chr_class() a stock
    # ChrClasses one. The SkillLineAbility replay is ~13 s, so it is loaded on first use and the full run reuses it
    # below (live_skilllineabilities()); an empty ChrClasses index (file missing) makes chr_class() stop with an ERROR.
    live_sla_cache: dict[str, dict[int, dict]] = {}

    def live_skilllineabilities() -> dict[int, dict]:
        if "rows" not in live_sla_cache:
            live_sla_cache["rows"] = state.load_existing_rows(dbcfmt.SKILLLINEABILITY)
        return live_sla_cache["rows"]

    live_data = spell_tables.dsl_live_data(
        existing_talents, item_live_rows, live_skilllineabilities, lambda: state.load_stock_rows(dbcfmt.CHRCLASSES),
        lambda: state.load_stock_rows(dbcfmt.SKILLLINEABILITY),
    )
    progress("loaded live Talent.dbc rows and item_template rows")

    try:
        dsl_classes = dsl_registry.load_classes_dir(
            SOURCE_DIR / "classes", ids_cfg=ids_cfg, trainer_index=trainer_index,
            existing_group_ids=existing_group_ids, shapeshift_index=shapeshift_index,
            existing_creature_rows=existing_creature_rows,
            creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
            creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS, live_data=live_data,
        )
        # source/npcs/*.py: class-less test/tool NPCs (training dummies) - same loader, merged in.
        dsl_npcs = dsl_registry.load_classes_dir(
            SOURCE_DIR / "npcs", ids_cfg=ids_cfg, trainer_index=trainer_index,
            existing_group_ids=existing_group_ids, shapeshift_index=shapeshift_index,
            existing_creature_rows=existing_creature_rows,
            creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
            creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS, live_data=live_data,
        )
        _merge_npc_declarations(dsl_classes, dsl_npcs)
        # source/world/*.py: world content tied to no class or NPC (lfg_exclude(), item_template() edits of
        # stock items) - same loader, merged in.
        dsl_world = dsl_registry.load_classes_dir(SOURCE_DIR / "world", ids_cfg=ids_cfg, live_data=live_data)
        _merge_npc_declarations(dsl_classes, dsl_world, "source/world/")
    except dsl_registry.MissingStockFileError as error:
        print(f"ERROR: {error}")
        return 1
    try:
        dsl_registry.check_retired_talent_tab(dsl_classes)
    except dsl_registry.MissingRetiredTabError as error:
        print(f"ERROR: {error}")
        return 1
    n_dsl = sum(len(v) for v in dsl_classes.values())
    progress(f"loaded source/classes/*.py + source/npcs/*.py + source/world/*.py DSL ({n_dsl} entries)")
    _merge_dsl_sources(spell_entries, talents, dsl_classes)
    if n_dsl:
        creature_counts = {
            **spell_tables.count_declared(dsl_classes),
            **spell_tables.count_declared(dsl_classes, tables=spell_tables.CREATURE_TABLES),
            **spell_tables.count_declared(dsl_classes, tables=spell_tables.ITEM_TABLES),
        }
        print(
            f"note: source/classes/*.py + source/npcs/*.py (DSL) contributed {len(dsl_classes['spells'])} "
            f"spell(s), {len(dsl_classes['talents'])} talent(s), {len(dsl_classes['tabs'])} "
            f"talent tab(s), {len(dsl_classes['skill_line_abilities'])} skill line "
            f"abilitie(s), {len(dsl_classes['trainer_spells'])} trainer spell grant(s), "
            + ", ".join(f"{n} {name}" for name, n in creature_counts.items() if n)
        )
    # Potency system (docs/potency-system.md "Potency sheet", PLAN P2 step 6): one docs/potency/
    # <class>.md per class with at least one potency effect - local and not committed, like the
    # rest of docs/ (rewritten every run, same as the DSL's own `_potency` stash this reads).
    potency_sheets = potency_sheet.write_sheets(dsl_classes, REPO_ROOT / "docs" / "potency")
    if potency_sheets:
        print(f"note: wrote {len(potency_sheets)} potency sheet(s) to docs/potency/")
    # Generated per-class C++ constants header (docs/potency-system.md "Script numbers" tier 3,
    # PLAN P2b) - unlike the potency sheet above, this file IS committed (the CMake build doesn't
    # run Python), so it's only written for classes that have opted in
    # (CLASSES_WITH_GENERATED_HEADERS) rather than for every class with any spell at all.
    if "--check" in sys.argv:
        # A fast, read-only staleness gate (PLAN P2b step 3) - everything below this point (SQL
        # diffing, DBC state, the client patch) is irrelevant to "is the committed header stale",
        # so --check returns here instead of running the rest of the ~130s pipeline.
        for warning in header_gen.collect_warnings(dsl_classes, CLASSES_WITH_GENERATED_HEADERS):
            print(f"WARNING: {warning}")
        for warning in lint.check_range_on_nonself_helpers(dsl_classes["spells"]):
            print(f"WARNING: {warning}")
        for warning in lint.check_custom_equipped_item_class(dsl_classes["spells"]):
            print(f"WARNING: {warning}")
        # Family-0 SpellMods need the built SpellClassSet. --check skips the live secondary tables; seeding the
        # stock lookup rows keeps the throwaway context from minting (and exhausting) reserved index blocks.
        check_reuse = ReuseContext(
            {name: list(state.load_stock_rows(table).values()) for name, table in SECONDARY_TABLES.items()}, ids_cfg,
        )
        check_rows = [build.build_spell_row(e, check_reuse) for e in spell_entries]
        check_stock_spells = state.load_stock_rows(dbcfmt.SPELL)
        for warning in lint.check_family_zero_spellmods(spell_entries, check_rows, check_stock_spells):
            print(f"WARNING: {warning}")
        # Shaman T1 lints and the family-bit rules, over the declared population. --check has no promoted-aware
        # spell/SLA state: the base rows are the stock client file and only declared SkillLineAbility rows count.
        for warning in _t1_content_warnings(
            dsl_classes, talents, spell_entries, check_rows, check_stock_spells, [],
            _proc_shadow_inputs(spell_table_index, dsl_classes, talents, existing_talents),
        ):
            print(f"WARNING: {warning}")
        missing_family_file = _creature_family_missing_warning(check_rows)
        if missing_family_file:
            print(missing_family_file)
        for warning in lint.check_family_bit_rules(
            spell_entries, check_rows, dsl_classes["spell_procs"],
            [{"Spell": int(e["spell_id"]), "SkillLine": int(e["skill_line"])} for e in talents["skill_line_abilities"]],
            _pet_skill_lines(),
        ):
            print(f"WARNING: {warning}")
        # The full run's GCD-haste computation over stock inputs (Death Knight T1 step 6): its errors are WARNINGs
        # here (an approximation), printed so a new family-15 spell with an all-zero class mask shows up in --check.
        for warning in _gcd_haste_check_warnings(spell_entries, talents, dsl_classes, check_stock_spells, ids_cfg):
            print(f"WARNING: {warning}")
        header_problems = header_gen.check_headers(
            dsl_classes, GENERATED_HEADER_DIR, CLASSES_WITH_GENERATED_HEADERS
        )
        # Errors the full run stops on, so --check exits 1 for them too (hunter T1-10).
        check_errors = _rune_cost_errors(spell_entries, dsl_classes, ids_cfg) + header_problems
        if check_errors:
            for problem in check_errors:
                print(f"ERROR: {problem}")
            return 1
        print(f"note: generated header(s) up to date for {', '.join(CLASSES_WITH_GENERATED_HEADERS)}")
        progress(f"--check done (cache: {_cache_summary(corpus)})")
        return 0
    else:
        for warning in header_gen.collect_warnings(dsl_classes, CLASSES_WITH_GENERATED_HEADERS):
            print(f"WARNING: {warning}")
        written_headers = header_gen.write_headers(
            dsl_classes, GENERATED_HEADER_DIR, CLASSES_WITH_GENERATED_HEADERS
        )
        if written_headers:
            print(f"note: wrote {len(written_headers)} generated header(s): {', '.join(written_headers)}")
    for warning in lint.check_linked_spell_key_collisions(
        spell_table_index.live_rows("spell_linked_spell") + dsl_classes["linked_spells"]
    ):
        print(f"WARNING: {warning}")
    # T1: creature_template/creature_template_model - never pruned (creature_template can't be
    # DELETEd, and pruning only the model row would leave a creature without one), so this is
    # entirely separate from the spell_table_index prune/render pass below - see
    # lib/spell_tables.py's CREATURE_TABLES module docstring.
    creature_blocks = spell_tables.render_creature_blocks(creature_table_index, dsl_classes)
    for line in spell_tables.render_creature_retirement_report(creature_table_index, dsl_classes):
        print(line)
    item_blocks = spell_tables.render_item_blocks(item_table_index, dsl_classes)
    for line in spell_tables.render_item_retirement_report(item_table_index, dsl_classes):
        print(line)
    known_model_display_ids = {
        int(r["DisplayID"]) for r in trainer_state.load_table_rows("creature_model_info")
    }
    has_model = (
        {int(r["CreatureID"]) for r in dsl_classes["creature_template_models"]}
        | {int(k[0]) for k in creature_table_index.live_keys("creature_template_model")}
    )
    for warning in lint.check_creature_trigger_flag_with_model(dsl_classes["creature_templates"], has_model):
        print(f"WARNING: {warning}")
    for warning in lint.check_creature_model_display_id(
        dsl_classes["creature_template_models"], known_model_display_ids
    ):
        print(f"WARNING: {warning}")
    for warning in lint.check_creature_without_model(dsl_classes["creature_templates"], has_model):
        print(f"WARNING: {warning}")
    trainer_spell_rows = _priced_trainer_spells(dsl_classes, trainer_index)
    # Declared removals (unbind_script/unlink_spell/leave_spell_group/untrain/remove_spell_proc/
    # unbind_bonus_coefficients) - a row this tool
    # never emitted itself (stock data, or an older hand-written migration), so the prune pass
    # above can't reach it. See lib/spell_tables.py's "Declared removals" section. Reuses
    # spell_table_index's/trainer_index's already-loaded live data for the three REMOVAL_TABLES
    # entries that overlap SPELL_TABLES, instead of a fresh rescan per table (review, 2026-09-23).
    removal_live_keys = {
        spec.name: spell_table_index.live_keys(spec.name) for spec in spell_tables.SPELL_TABLES
    }
    removal_live_keys["trainer_spell"] = set(trainer_index.existing_trainer_spells.keys())
    removal_blocks, removal_report = spell_tables.render_removal_blocks(dsl_classes, removal_live_keys)
    for line in removal_report:
        print(line)
    progress("rendered spell-table blocks (prune + removal passes done)")

    existing_spells = state.load_existing_rows(dbcfmt.SPELL)
    existing_talenttabs = state.load_existing_rows(dbcfmt.TALENTTAB)
    existing_skilllineabilities = dict(live_skilllineabilities())
    existing_items = state.load_existing_rows(dbcfmt.ITEM)
    existing_secondary_by_id = {
        name: state.load_existing_rows(table) for name, table in SECONDARY_TABLES.items()
    }
    existing_secondary = {name: list(rows.values()) for name, rows in existing_secondary_by_id.items()}
    progress("loaded existing (db_world-promoted-aware) DBC state")

    # pet-stale-ranks: stock SkillLineAbility rows still teach pets every superseded rank of a
    # collapsed chain (SpellMgr::LoadPetLevelupSpellMap). Override each with AcquireMethod 0 - see
    # lib/superseded_ranks.py. Appended before both resolve passes, so the rows reach the SQL and
    # the client patch like declared ones; a declared row with the same ID wins.
    stock_skilllineabilities = state.load_stock_rows(dbcfmt.SKILLLINEABILITY)
    rank_overrides = superseded_ranks.skilllineability_overrides(
        load_spell_ranks_chains(), dsl_classes["spells"], stock_skilllineabilities,
        talents["skill_line_abilities"], existing_skilllineabilities,
    )
    declared_sla_entries = list(talents["skill_line_abilities"])  # before any generated override joins the list
    talents["skill_line_abilities"].extend(rank_overrides.entries)
    rank_override_ids = {e["id"] for e in rank_overrides.entries}
    # Hunter T1: retire_pet_spell() declarations ride the same two paths - AcquireMethod 0 on the stock
    # SkillLineAbility rows that teach the spell to pets, and a strip from the CreatureSpellData records
    # applied below with the superseded-rank mapping (one row per record).
    pet_retirements = dsl_classes["pet_spell_retirements"]
    retire_overrides = superseded_ranks.Overrides()
    spell_data_strips: dict[int, frozenset[int]] = {}
    retire_warnings: list[str] = []
    if pet_retirements:
        if not (BASE_DBC_DIR / dbcfmt.CREATUREFAMILY.dbc_filename).is_file():
            print(
                f"ERROR: retire_pet_spell() was declared but there is no stock {dbcfmt.CREATUREFAMILY.dbc_filename} "
                f"in {BASE_DBC_DIR.relative_to(REPO_ROOT)} - copy it from the worldserver's DBC directory "
                f"(ac-worldserver:/azerothcore/env/dist/data/dbc/) into that directory"
            )
            return 1
        retire_overrides = superseded_ranks.retired_skilllineability_overrides(
            pet_retirements, stock_skilllineabilities,
            superseded_ranks.family_skill_lines(state.load_stock_rows(dbcfmt.CREATUREFAMILY)),
            declared_sla_entries, rank_override_ids, existing_skilllineabilities,
        )
        spell_data_strips, retire_warnings = superseded_ranks.spell_data_strips(
            pet_retirements, existing_creature_rows, state.load_stock_rows(dbcfmt.CREATURESPELLDATA),
            rank_overrides.superseded,
            superseded_ranks.family_skill_lines(state.load_stock_rows(dbcfmt.CREATUREFAMILY)),
            {
                **stock_skilllineabilities,
                **{e["id"]: build.build_skilllineability_row(e) for e in talents["skill_line_abilities"]},
                **{e["id"]: build.build_skilllineability_row(e) for e in retire_overrides.entries},
            },
        )
        for retirement in pet_retirements:
            if retirement["spell_id"] not in retire_overrides.matched and not any(
                retirement["spell_id"] in spells for spells in spell_data_strips.values()
            ):
                scope = "every family" if retirement["families"] is None else f"families {list(retirement['families'])}"
                retire_warnings.append(
                    f"retire_pet_spell({retirement['spell_id']}) matches nothing for {scope}: no stock pet "
                    f"SkillLineAbility row on their skill lines and no CreatureSpellData record to strip - "
                    f"wrong spell id or family?"
                )
        talents["skill_line_abilities"].extend(retire_overrides.entries)
        rank_override_ids |= {e["id"] for e in retire_overrides.entries}
    # Default pet spells (CreatureSpellData via creature_template.PetSpellDataId) name the same ranks,
    # and SpellMgr's LoadPetDefaultSpells_helper only drops those in the family's level-up set, which
    # the overrides above just shrank. Server-only rows, emitted as their own block below.
    spell_data_overrides = superseded_ranks.creaturespelldata_overrides(
        rank_overrides.superseded, state.load_stock_rows(dbcfmt.CREATURESPELLDATA),
        state.load_existing_rows(dbcfmt.CREATURESPELLDATA), spell_data_strips,
    )
    for warning in rank_overrides.collisions + rank_overrides.warnings + spell_data_overrides.warnings:
        print(f"WARNING: superseded ranks: {warning}")
    for warning in retire_overrides.collisions + retire_overrides.warnings + retire_warnings:
        print(f"WARNING: retire_pet_spell: {warning}")
    if pet_retirements:
        print(
            f"note: retire_pet_spell: {len(pet_retirements)} retirement(s), {len(retire_overrides.entries)} "
            f"SkillLineAbility row(s) overridden to AcquireMethod 0, {len(spell_data_strips)} CreatureSpellData "
            f"record(s) stripped"
        )
    print(
        f"note: superseded ranks: {len(rank_overrides.superseded)} superseded rank(s) of collapsed chains, "
        f"{len(rank_overrides.entries)} SkillLineAbility row(s) overridden to AcquireMethod 0 on skill "
        f"line(s) {sorted({e['skill_line'] for e in rank_overrides.entries})}; "
        f"{len(spell_data_overrides.rows)} CreatureSpellData record(s) with the survivor in place of a "
        f"superseded rank, {len(spell_data_overrides.to_emit)} not yet live"
    )
    if not (BASE_DBC_DIR / dbcfmt.CREATURESPELLDATA.dbc_filename).is_file():
        print(
            f"WARNING: superseded ranks: no stock {dbcfmt.CREATURESPELLDATA.dbc_filename} in "
            f"{BASE_DBC_DIR.relative_to(REPO_ROOT)}, so pets' default spells keep their superseded ranks - "
            f"extract DBFilesClient/{dbcfmt.CREATURESPELLDATA.dbc_filename} from the client's patch-enUS.MPQ "
            f"into that directory (see .agents/docs/systems/dbc-tools.md)"
        )

    # melee-haste-gcd T1: one hidden GCD-haste aura per class family, its classmasks computed from the merged
    # spell data (lib/gcd_haste.py, policy in source/gcd_haste.py). Appended before both resolve passes, so
    # the rows reach the SQL and the client patch like declared ones. A bit shared with a spell the core
    # already hastes stops the run.
    # What a player can still be taught: replayed trainer_spell rows of a reachable trainer (minus untrain()
    # removals) plus trained_by() declarations. A superseded rank in here is still learnable, so it is not
    # left out of the masks.
    removed_grants = {(int(r["TrainerId"]), int(r["SpellId"])) for r in dsl_classes["trainer_removals"]}
    live_grants = [key for key in trainer_pricing.replay_trainer_spells() if key not in removed_grants]
    declared_grants = {int(r["SpellId"]) for r in dsl_classes["trainer_spells"]}
    trainer_reachable = lambda trainer_id: not trainer_index.trainer_problems(trainer_id)  # noqa: E731
    trainer_taught = declared_grants | {spell for trainer, spell in live_grants if trainer_reachable(trainer)}
    try:
        gcd_entries, gcd_result = _gcd_haste_entries(
            spell_entries, talents, dsl_classes["spells"], rank_overrides.superseded, trainer_taught, existing_spells,
            existing_talents, existing_talenttabs, existing_skilllineabilities, existing_secondary, ids_cfg,
        )
    except gcd_haste.GcdHasteError as error:
        print(f"ERROR: gcd haste: {error}")
        return 1
    for line in gcd_haste.report_lines(gcd_result):
        print(line)
    for warning in gcd_result.warnings:
        print(f"WARNING: gcd haste: {warning}")
    # The masks leave out NOT_CASTABLE spells (and superseded ranks nobody teaches) on the premise that no
    # player can learn them: check that against the replayed trainer_spell rows and trained_by() declarations.
    gcd_result.errors.extend(gcd_haste.untrainable_errors(
        gcd_result.assumed_untrainable, live_grants, trainer_reachable, declared_grants,
    ))
    if gcd_result.errors:
        for error in gcd_result.errors:
            print(f"ERROR: gcd haste: {error}")
        return 1
    taken = {e["id"] for e in spell_entries}
    for entry in gcd_entries:
        if entry["id"] in taken:
            print(f"ERROR: gcd haste: aura spell ID {entry['id']} is already declared in source/")
            return 1
    spell_entries.extend(gcd_entries)
    # Bind the runtime AuraScript to every generated aura like any scripted_by() binding, then render the
    # spell-table blocks once, so the new rows are diffed and pruned with the rest.
    dsl_classes["spell_script_names"].extend(gcd_haste.script_rows(gcd_entries))
    spell_table_blocks = spell_tables.render_blocks(spell_table_index, dsl_classes)
    # Prune: rows an *earlier* run of this script emitted that source/classes/*
    # no longer declares (a removed scripted_by()/procs_on()/bonus_coefficients()).
    # render_blocks above only ever speaks about rows still declared, so without
    # this an orphan stays live in the world DB forever - see
    # .agents/plans/dbc-tools-prune-pass/dbc-tools-prune-pass.PLAN.md for why
    # provenance is "did a generated file emit it", not "is it one of our spell ids".
    if "--no-prune" in sys.argv:
        prune_blocks, prune_report = [], ["prune: skipped (--no-prune)"]
    else:
        prune_blocks, prune_report = spell_tables.render_prune_blocks(spell_table_index, dsl_classes)
    for line in prune_report:
        print(line)
    progress("computed GCD-haste auras")

    # Reconcile source/ against what's actually live: an entry is either new
    # (id inside the reserved block), a deliberate edit to something that
    # already exists (id outside the block, but changed), or an untouched
    # reference copy pulled in for reading only (id outside the block,
    # unchanged) — the last case is silently skipped. See lib/resolve.py.
    # Spell comparisons use a throwaway ReuseContext so an unchanged
    # reference spell's build attempt can't leave an orphan minted
    # secondary-table row behind (see resolve.py's build_one note).
    scratch_reuse = ReuseContext(existing_secondary, ids_cfg)
    spell_resolved = resolve.resolve_rows(
        spell_entries, ids_cfg["spell"], existing_spells,
        lambda e: build.build_spell_row(e, scratch_reuse),
    )
    talent_resolved = resolve.resolve_rows(
        talents["talents"], ids_cfg["talent"], existing_talents, build.build_talent_row,
    )
    talenttab_resolved = resolve.resolve_rows(
        talents["tabs"], ids_cfg["talenttab"], existing_talenttabs, build.build_talenttab_row,
    )
    skilllineability_resolved = resolve.resolve_rows(
        talents["skill_line_abilities"], ids_cfg["skilllineability"],
        existing_skilllineabilities, build.build_skilllineability_row,
    )
    item_resolved = resolve.resolve_rows(
        item_entries, ids_cfg["item"], existing_items, build.build_item_row,
    )
    # Superseded-rank overrides are generated, not pulled-in copies: once promoted they resolve as
    # unchanged, so count them apart. They sit outside the reserved block, so each is edited or unchanged.
    n_live_rank_overrides = len(rank_override_ids - set(skilllineability_resolved.edited_ids))
    n_unchanged_sla = skilllineability_resolved.unchanged - n_live_rank_overrides
    n_unchanged = (
        spell_resolved.unchanged + talent_resolved.unchanged + talenttab_resolved.unchanged
        + n_unchanged_sla + item_resolved.unchanged
    )
    if n_unchanged:
        print(
            f"note: {n_unchanged} row(s) in source/ are unchanged copies of existing data "
            f"(pulled in for reference — see apps/dbc-tools/README.md) and were not "
            f"generated: {spell_resolved.unchanged} spell(s), {talent_resolved.unchanged} "
            f"talent(s), {talenttab_resolved.unchanged} talent tab(s), "
            f"{n_unchanged_sla} skill line abilitie(s), "
            f"{item_resolved.unchanged} item(s)"
        )
    if n_live_rank_overrides:
        print(f"note: superseded ranks: {n_live_rank_overrides} SkillLineAbility override(s) already live")
    n_edited = (
        len(spell_resolved.edited_ids) + len(talent_resolved.edited_ids)
        + len(talenttab_resolved.edited_ids) + len(skilllineability_resolved.edited_ids)
        + len(item_resolved.edited_ids)
    )
    if n_edited:
        print(
            f"editing {len(spell_resolved.edited_ids)} existing spell(s) "
            f"{spell_resolved.edited_ids}, {len(talent_resolved.edited_ids)} talent(s) "
            f"{talent_resolved.edited_ids}, {len(talenttab_resolved.edited_ids)} talent "
            f"tab(s) {talenttab_resolved.edited_ids}, "
            f"{len(skilllineability_resolved.edited_ids)} skill line abilitie(s) "
            f"{skilllineability_resolved.edited_ids}, {len(item_resolved.edited_ids)} "
            f"item(s) {item_resolved.edited_ids}"
        )
    progress("resolved source/ against existing rows (new/edited/unchanged split)")

    # Real build pass (real ReuseContext this time) over just what survived
    # reconciliation — this is what actually gets emitted to SQL.
    reuse = ReuseContext(existing_secondary, ids_cfg)
    spell_rows = [build.build_spell_row(e, reuse) for e in spell_resolved.entries]
    # Pure stock client rows: the classmask lint exempts an effect only if it matches stock exactly.
    stock_spells = state.load_stock_rows(dbcfmt.SPELL)
    for warning in lint.check_classmask_scoping(spell_resolved.entries, spell_rows, stock_spells):
        print(f"WARNING: {warning}")
    for warning in lint.check_missing_skill_line_ability(
        spell_resolved.entries, skilllineability_resolved.entries, existing_skilllineabilities, ids_cfg,
    ):
        print(f"WARNING: {warning}")
    # PLAN A9: raw_overrides silently beating a typed field build_spell_row also sets (lib/build.py
    # applies raw_overrides last) - see lib/lint.py's own docstring for the bug this already
    # shipped (nine spells kept their rank-1 cast time instead of the DSL's cast_time_ms).
    # Scans the *full* spell_entries, not spell_resolved.entries - resolve_rows silently drops any
    # entry whose built row is unchanged from what's already live (an "unchanged reference copy"),
    # which is exactly where a still-live A9-shaped bug hides: a spell nobody edited this run
    # never gets built or compared, so the mismatch stays invisible to a resolved-only scan (found
    # via review, 2026-09-23 - a first version of this check scanned spell_resolved.entries and
    # wrongly concluded all nine PLAN A9 spells were already fixed).
    for warning in lint.check_raw_override_typed_mismatch(spell_entries, existing_secondary_by_id):
        print(f"WARNING: {warning}")
    # Paladin T1: remove_spell_proc() on a spell whose DBC ProcTypeMask is still non-zero doesn't
    # disable the proc (SpellMgr builds a default row from it). Stock spells outside source come
    # from existing_spells (base Spell.dbc + promoted SQL); this run's built rows overlay them.
    # Talent rank chains (Talent.dbc, not spell_ranks); DSL/YAML ranks override existing rows.
    rank_chains = lint.build_talent_rank_chains(existing_talents, talents["talents"])
    for warning in lint.check_removed_proc_flags(
        [int(r["SpellId"]) for r in dsl_classes["proc_removals"]],
        {**existing_spells, **{int(r["ID"]): r for r in spell_rows}},
        rank_chains,
    ):
        print(f"WARNING: {warning}")
    # Same full-population scan: RangeIndex 0 on a spell aimed at another unit fails CheckRange
    # silently (Fury of Elune's beam did no damage - docs/bugs-and-fixes.md).
    zero_range_warnings = lint.check_zero_range_unit_target(spell_entries)
    for warning in zero_range_warnings:
        print(f"WARNING: {warning}")
    # X1 (paladin-rework SHARED B6 item 7): the broader custom-id (>= 200000) variant - non-self
    # means anything but the caster, dest/area targets included. Ids the check above already
    # reported are skipped so a spell never prints twice.
    already_reported = {
        int(w.split()[1]) for w in zero_range_warnings
    }
    for warning in lint.check_range_on_nonself_helpers(spell_entries, skip_ids=already_reported):
        print(f"WARNING: {warning}")
    # Custom spells default to EquippedItemClass 0, which fails every cast (silently when triggered).
    for warning in lint.check_custom_equipped_item_class(spell_entries):
        print(f"WARNING: {warning}")
    # Full declared population (like the scans above): a family-0 SpellMod already live is not "edited",
    # so a resolved-only scan would hide it.
    all_spell_rows = [build.build_spell_row(e, scratch_reuse) for e in spell_entries]
    for warning in lint.check_family_zero_spellmods(spell_entries, all_spell_rows, stock_spells):
        print(f"WARNING: {warning}")
    # Shaman T1 lints (same population and function as --check, with the promoted-aware spell and SLA state).
    for warning in _t1_content_warnings(
        dsl_classes, talents, spell_entries, all_spell_rows, existing_spells,
        list(existing_skilllineabilities.values()),
        _proc_shadow_inputs(spell_table_index, dsl_classes, talents, existing_talents),
    ):
        print(f"WARNING: {warning}")
    talent_rows = [build.build_talent_row(e) for e in talent_resolved.entries]
    talenttab_rows = [build.build_talenttab_row(e) for e in talenttab_resolved.entries]
    skilllineability_rows = [
        build.build_skilllineability_row(e) for e in skilllineability_resolved.entries
    ]
    item_rows = [build.build_item_row(e) for e in item_resolved.entries]
    # Hunter T1 (SHARED C7.6): the PLAN section 2 family-bit rules. Pet skill lines = the shared 270 plus
    # every CreatureFamily.dbc line (the lint adds 270 itself); without the stock file only 270 is known.
    pet_skill_lines: set[int] = set()
    if (BASE_DBC_DIR / dbcfmt.CREATUREFAMILY.dbc_filename).is_file():
        for lines in superseded_ranks.family_skill_lines(state.load_stock_rows(dbcfmt.CREATUREFAMILY)).values():
            pet_skill_lines.update(lines)
    else:
        missing = _creature_family_missing_warning(all_spell_rows)
        if missing:
            print(missing)
    # The whole declared population, like --check and the other full-population scans: a live, unedited spell is
    # not "resolved", so a resolved-only scan would hide a rule break that --check shows.
    for warning in lint.check_family_bit_rules(
        spell_entries, all_spell_rows, dsl_classes["spell_procs"],
        list({**existing_skilllineabilities, **{int(r["ID"]): r for r in skilllineability_rows}}.values()),
        pet_skill_lines,
    ):
        print(f"WARNING: {warning}")
    # Hunter T1: a declared item_template() class/subclass must match the Item.dbc the server will have
    # (stock plus item_dbc overlay plus this run's rows), and no bow/gun/crossbow may still need ammo.
    for warning in lint.check_item_dbc_consistency(
        dsl_classes["item_templates"], {**existing_items, **{int(r["ID"]): r for r in item_rows}},
    ):
        print(f"WARNING: {warning}")
    for warning in lint.check_ranged_ammo_type(dsl_classes["item_templates"], item_entries, item_live_rows):
        print(f"WARNING: {warning}")
    progress("built rows for SQL emission and ran lint checks")

    # Second reconciliation pass, against pure-vanilla state instead of
    # state.load_existing_rows's db_world-promoted-aware state, purely to
    # decide what the *client patch* needs to carry — see state.py's "Two
    # baselines, two purposes" note. Reuses the same `reuse` (idempotent
    # find_or_mint, see reuse.py) so this can't mint a duplicate secondary row
    # for something the SQL-emission pass above already minted one for.
    stock_talents = state.load_stock_rows(dbcfmt.TALENT)
    stock_talenttabs = state.load_stock_rows(dbcfmt.TALENTTAB)
    stock_items = state.load_stock_rows(dbcfmt.ITEM)
    # P9 (potency-system.PLAN.md, D12): SpellDescriptionVariables references - a tooltip variable
    # the spell's entry doesn't define renders as a literal `$<var>` in the client. Errors stop the
    # run here, before any SQL or patch is written.
    stock_tooltip_vars = None
    if (BASE_DBC_DIR / dbcfmt.SPELLDESCRIPTIONVARIABLES.dbc_filename).is_file():
        stock_tooltip_vars = {
            entry_id: row["Variables"]
            for entry_id, row in state.load_stock_rows(dbcfmt.SPELLDESCRIPTIONVARIABLES).items()
        }
    tooltip_errors, tooltip_notes = lint.check_tooltip_vars(
        spell_entries, dsl_classes["tooltip_vars"], stock_tooltip_vars,
        set(stock_spells) | set(existing_spells) | {e["id"] for e in spell_entries},
    )
    for note in tooltip_notes:
        print(f"note: {note}")
    # D1: a live spell_bonus_data row silently overrides an SP-only potency spell's coefficient
    # (lint.check_potency_bonus_overrides). Same stop-before-SQL treatment as the tooltip errors.
    spell_names = {e["id"]: e["name"] for e in spell_entries}
    # Rows this run's own prune pass deletes are not live in the output (squashing the earlier
    # generated files would otherwise trip D1 on every previously-pruned row).
    pruned_bonus_ids = (
        set() if "--no-prune" in sys.argv
        else {int(k[0]) for k in spell_tables.pruned_keys(spell_table_index, dsl_classes, "spell_bonus_data")}
    )
    bonus_errors = lint.check_potency_bonus_overrides(
        {r["spell_id"]: spell_names.get(r["spell_id"], "?") for r in dsl_classes["potency_corrections"]},
        {int(r["entry"]) for r in dsl_classes["spell_bonus_data"]},
        {int(r["entry"]) for r in dsl_classes["bonus_removals"]},
        trainer_state.load_keyed_table_rows(
            "spell_bonus_data", ("entry", "direct_bonus", "dot_bonus", "ap_bonus", "ap_dot_bonus", "comments"),
        ),
        pruned_bonus_ids,
    )
    # Paladin T1: a spell using a custom (spellcategory-block) Category with no spell_category()
    # declaration silently loses its category cooldown on the server.
    category_errors = lint.check_undeclared_spell_categories(
        spell_entries, {int(r["ID"]) for r in dsl_classes["spell_categories"]}, ids_cfg.get("spellcategory"),
    )
    category_base_error = _spell_category_base_error(
        _spell_category_rows(dsl_classes["spell_categories"]), BASE_DBC_DIR,
    )
    if category_base_error:
        category_errors.append(category_base_error)
    # Death Knight T1: the same for a RuneCostID in the spellrunecost block with no spell_rune_cost() declaration, and
    # for declared rune costs with no stock SpellRuneCost.dbc to merge into (shared with --check).
    category_errors.extend(_rune_cost_errors(spell_entries, dsl_classes, ids_cfg))
    lfg_dungeons = (
        state.load_stock_rows(dbcfmt.LFGDUNGEONS)
        if (BASE_DBC_DIR / dbcfmt.LFGDUNGEONS.dbc_filename).is_file() else None
    )
    lfg_errors, lfg_notes = lint.check_lfg_exclusions(dsl_classes["lfg_disables"], lfg_dungeons)
    for note in lfg_notes:
        print(f"note: {note}")
    if tooltip_errors or bonus_errors or category_errors or lfg_errors:
        for error in tooltip_errors + bonus_errors + category_errors + lfg_errors:
            print(f"ERROR: {error}")
        return 1
    client_spell_resolved = resolve.resolve_rows(
        spell_entries, ids_cfg["spell"], stock_spells,
        lambda e: build.build_spell_row(e, scratch_reuse),
    )
    client_talent_resolved = resolve.resolve_rows(
        talents["talents"], ids_cfg["talent"], stock_talents, build.build_talent_row,
    )
    client_talenttab_resolved = resolve.resolve_rows(
        talents["tabs"], ids_cfg["talenttab"], stock_talenttabs, build.build_talenttab_row,
    )
    client_skilllineability_resolved = resolve.resolve_rows(
        talents["skill_line_abilities"], ids_cfg["skilllineability"],
        stock_skilllineabilities, build.build_skilllineability_row,
    )
    client_item_resolved = resolve.resolve_rows(
        item_entries, ids_cfg["item"], stock_items, build.build_item_row,
    )
    client_spell_rows = [build.build_spell_row(e, reuse) for e in client_spell_resolved.entries]
    client_talent_rows = [build.build_talent_row(e) for e in client_talent_resolved.entries]
    client_talenttab_rows = [
        build.build_talenttab_row(e) for e in client_talenttab_resolved.entries
    ]
    client_skilllineability_rows = [
        build.build_skilllineability_row(e) for e in client_skilllineability_resolved.entries
    ]
    client_item_rows = [build.build_item_row(e) for e in client_item_resolved.entries]
    progress("built client-patch rows (resolved against pure-vanilla stock baseline)")

    # Hunter T1 (SHARED §C7.10): a Talent row on a TalentTab nobody declared crashes mod-playerbots and
    # reads a null tab in the core. Checked on both populations - the server's live-plus-built rows (what
    # the SQL overlay leaves in the DB) and the client's stock-plus-built rows (what patch-Z ships).
    tab_ref_errors = lint.check_talent_tab_refs(
        [*{**existing_talents, **{int(r["ID"]): r for r in talent_rows}}.values()],
        [*{**existing_talenttabs, **{int(r["ID"]): r for r in talenttab_rows}}.values()],
    ) + lint.check_talent_tab_refs(
        [*{**stock_talents, **{int(r["ID"]): r for r in client_talent_rows}}.values()],
        [*{**stock_talenttabs, **{int(r["ID"]): r for r in client_talenttab_rows}}.values()],
    )
    if tab_ref_errors:
        for error in dict.fromkeys(tab_ref_errors):
            print(f"ERROR: {error}")
        return 1

    # -- pending SQL: reserved range + explicit edited IDs, per table --
    blocks = [
        (dbcfmt.SPELL, ids_cfg["spell"], spell_rows, spell_resolved.edited_ids, existing_spells),
        (dbcfmt.TALENT, ids_cfg["talent"], talent_rows, talent_resolved.edited_ids, existing_talents),
        (
            dbcfmt.TALENTTAB, ids_cfg["talenttab"], talenttab_rows, talenttab_resolved.edited_ids,
            existing_talenttabs,
        ),
        (
            dbcfmt.SKILLLINEABILITY, ids_cfg["skilllineability"], skilllineability_rows,
            skilllineability_resolved.edited_ids, existing_skilllineabilities,
        ),
        (dbcfmt.ITEM, ids_cfg["item"], item_rows, item_resolved.edited_ids, existing_items),
    ]
    for name, table in SECONDARY_TABLES.items():
        # reserved_rows (reused ∪ minted), not .minted alone - see ReuseContext.reserved_rows's
        # own docstring for the "wiped a range it wasn't fully reinserting" bug this avoids.
        blocks.append(
            (table, ids_cfg[name], reuse.reserved_rows.get(name, []), [], existing_secondary_by_id[name])
        )

    blocks, n_skipped_unchanged_tables = _drop_unchanged_blocks(blocks)
    if n_skipped_unchanged_tables:
        print(
            f"note: {n_skipped_unchanged_tables} table(s) reserved-block content is already "
            f"live and unchanged - not re-emitted"
        )

    header = (
        "-- Generated by apps/dbc-tools/generate.py — DO NOT hand-edit.\n"
        "-- Source of truth: apps/dbc-tools/source/{spells,talents}/*.\n"
        "-- Regenerate with: python3 apps/dbc-tools/generate.py"
    )
    trainer_spell_block = sql_out.render_generic_table_block(
        "trainer_spell", TRAINER_SPELL_COLUMNS, ("TrainerId", "SpellId"), trainer_spell_rows,
    )
    spell_data_block = sql_out.render_generic_table_block(
        dbcfmt.CREATURESPELLDATA.sql_table, dbcfmt.CREATURESPELLDATA.columns, ("ID",),
        spell_data_overrides.to_emit,
    )

    rev = int(time.time() * 1_000_000_000)
    out_path = PENDING_SQL_DIR / f"rev_{rev}.sql"
    wrote_sql = sql_out.emit_pending_sql(
        out_path, blocks, header,
        extra_blocks=[
            *prune_blocks, *removal_blocks, trainer_spell_block, *spell_table_blocks,
            *creature_blocks, *item_blocks, spell_data_block,
        ],
    )
    print(f"SQL: wrote {out_path.relative_to(REPO_ROOT)}" if wrote_sql else "SQL: nothing to emit")
    progress("SQL emission done")

    # -- client patch: needs a complete file (base + new), so any table with
    # new/changed rows but no extracted base file gets skipped, not
    # half-written. Uses the *_client_rows sets (diffed against pure vanilla)
    # so already-promoted content keeps getting baked into every patch build,
    # not just the first one after it was promoted — see state.py.
    new_rows_by_table = {
        dbcfmt.SPELL: {r["ID"]: r for r in client_spell_rows},
        dbcfmt.TALENT: {r["ID"]: r for r in client_talent_rows},
        dbcfmt.TALENTTAB: {r["ID"]: r for r in client_talenttab_rows},
        dbcfmt.SKILLLINEABILITY: {r["ID"]: r for r in client_skilllineability_rows},
        dbcfmt.ITEM: {r["ID"]: r for r in client_item_rows},
        dbcfmt.SPELLDESCRIPTIONVARIABLES: _tooltip_var_rows(dsl_classes["tooltip_vars"]),
        dbcfmt.SPELLCATEGORY: _spell_category_rows(dsl_classes["spell_categories"]),
        dbcfmt.SPELLRUNECOST: _spell_rune_cost_rows(dsl_classes["spell_rune_costs"]),
    }
    for name, table in SECONDARY_TABLES.items():
        # Same reserved_rows switch as the SQL block above - the client patch must carry every
        # reused row too, not just this run's fresh mints, or it silently regresses previously-
        # shipped custom cast times/durations/ranges/radii out of the patch.
        rows_needed = reuse.reserved_rows.get(name, [])
        if rows_needed:
            new_rows_by_table[table] = {r["ID"]: r for r in rows_needed}

    dbc_files: dict[str, bytes] = {}
    for table, new_rows in new_rows_by_table.items():
        if not new_rows:
            continue
        dbc_path = BASE_DBC_DIR / table.dbc_filename
        if not dbc_path.is_file():
            print(
                f"patch: SKIPPING {table.dbc_filename} — no base client DBC at "
                f"{dbc_path.relative_to(REPO_ROOT)}; server SQL overlay is still "
                f"complete, but a client patch needs the full stock file as a base "
                f"layer (see docs/dbc-build-pipeline.md)."
            )
            continue
        base_rows = state.read_dbc_cached(dbc_path, table)  # read-only: shared with the stock-row loaders
        merged = {row[table.index_column]: row for row in base_rows}
        merged.update(new_rows)
        # Talent.dbc's and TalentTab.dbc's physical row order is load-bearing to the client - see
        # dbcfile.pack_client_dbc.
        dbc_files[table.dbc_filename] = dbcfile.pack_client_dbc(table, list(merged.values()), base_rows)

    # Flag client tables that need an in-game look, and tables that appeared in or dropped out of
    # the patch since the last build (lint.check_client_patch).
    previous_patch = mpq_writer.list_mpq(patch_out.MPQ_PATH) if patch_out.MPQ_PATH.is_file() else None
    shipping = {
        table.name: rows for table, rows in new_rows_by_table.items() if table.dbc_filename in dbc_files
    }
    patch_notes: list[str] = []
    for warning in lint.check_client_patch(shipping, {"TalentTab": stock_talenttabs}, previous_patch, patch_notes):
        print(f"WARNING: patch: {warning}")
    for note in patch_notes:
        print(f"note: patch: {note}")
    if dbc_files:
        report = patch_out.write_patch(dbc_files)
        print(f"patch: loose files -> {patch_out.LOOSE_DIR}")
        print(f"patch: mpq -> {report['mpq']}")
        if report["env_dbc"]:
            print(f"patch: also copied into {patch_out.ENV_DBC_DIR}")
        if report["deploy_mpq"]:
            print(f"patch: deployed -> {report['deploy_mpq']} (patch-service's manifest-gen "
                  f"picks this up on its next timer tick; run apps/patch-service/manifest_gen.py "
                  f"by hand for an immediate manifest.txt refresh)")
    else:
        print("patch: nothing to write (no base DBCs available yet)")
    progress(f"done (cache: {_cache_summary(corpus)})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
