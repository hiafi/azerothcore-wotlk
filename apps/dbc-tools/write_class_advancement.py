#!/usr/bin/env python3
"""
Class Advancement UI, stage U1: writes the class talent / ability table for the client,
`client/ui-overrides/Interface/FrameXML/ClassAdvancementData.lua` (the private repo hiafi/wow-client-ui, shipped in
patch-X by `build_patch_x.py`). The window `ClassAdvancementFrame.lua` (stage U3) reads `CLASS_ADVANCEMENT_ORDER` and
`CLASS_ADVANCEMENT` and draws, per class, the three talent trees and the class's abilities by spec
(`.agents/plans/classless-ui/classless-ui.PLAN.md`, sections 2 to 4).

Inputs, all read-only and the same view `generate.py` builds (the source tree wins over what is live):

- Talent.dbc / TalentTab.dbc: the stock client files (`var/extractors/dbc`) with every `talent()` / `tab()` /
  `retire_talent()` declaration of `source/classes/*` merged over them, rows built by `lib/build.py`. TalentTab 60800
  ("Retired"), tabs with class mask 0 and pet tabs (`PetTalentMask`) are skipped.
- Spell.dbc: the stock file with every declared spell laid over it (names, passive / hidden flags, effects, ranks).
- SkillLineAbility.dbc: the stock file with the declared `skill_line_ability()` rows laid over it.
- `trainer_spell`: the replay of the world SQL (`lib/trainer_pricing.replay_trainer_spells`, base dump, promoted,
  pending and module SQL in apply order) with the declared `trained_by()` rows laid over it and the `untrain()`ed keys
  taken out, the same combination `generate.py` writes. Only trainers that resolve to a spawned NPC count
  (`TrainerIndex.trainer_problems`); the `trainer` table (replayed) says which class a trainer teaches.
- `spell_ranks` (replayed, minus `unrank_spells()`): a chain's highest rank is the one listed, and a stock rank that a
  single-rank survivor replaced (`lib/superseded_ranks.py`) is dropped.

Output: `CLASS_ADVANCEMENT_ORDER` (the ten class file tokens) and `CLASS_ADVANCEMENT[token]` = `{ classId, tabs,
abilities }`; the field contract is in the PLAN (section 4) and the U1 handoff. Per class:

- `tabs`: three, in TalentTab `OrderIndex` order: `{ id, name, art, skillLine, talents }`, talents sorted by row, then
  column, `{ id, row, col, ranks, req?, reqRank? }`. `skillLine` is the spec's SkillLine (no DBC field links the two,
  so `SPEC_SKILL_LINES` below is the hand table; each id is checked against SkillLine.dbc).
- `abilities`: one entry per ability (highest rank id), `{ spell, section, level?, how, talent? }`. `how` is
  "trainer" (lowest ReqLevel on an in-use class trainer), "start" (a class skill line row learned on its own,
  `AcquireMethod` 1 or 2; `level` = ceil(MinSkillLineRank / 5) for method 1, class skills being 5 per level, and 1 for
  method 2) or "talent" (an active spell a talent rank teaches or is; `talent` = the Talent id, no level). `section`
  1..3 = the tab whose skill line the spell's SkillLineAbility is on (the talent's tab for "talent"), 0 = anything
  else (trainer spells with no spec-line row). Sorted by section, then level (talents last), then name, then id.
  Proficiencies, languages, professions, mounts, racials, pet abilities, hidden helpers and retired spells are left
  out (`ability_exclusion`); `--report` prints every spell a rule dropped, and the per-class counts.

The file is deterministic (LF, integers only): a rerun with unchanged data writes nothing.
`lib/test_class_advancement.py` checks the table.

    python3 write_class_advancement.py [--check] [--out PATH] [--report]

It loads the whole DSL (about 30 to 80 s, the replays are cached under `var/dbc-tools-cache/`), so it needs the
stock DBCs in `var/extractors/dbc` like `generate.py` does.
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOL_ROOT))

from bootstrap import load_spell_ranks_chains  # noqa: E402
from lib import build, dbcfmt, source, spell_tables, sqlcorpus, state, superseded_ranks  # noqa: E402
from lib import trainer_pricing, trainer_state  # noqa: E402
from lib.dsl import registry as dsl_registry  # noqa: E402
from lib.lazy import Lazy  # noqa: E402

REPO_ROOT = TOOL_ROOT.parent.parent
SOURCE_DIR = TOOL_ROOT / "source"
CACHE_DIR = REPO_ROOT / "var" / "dbc-tools-cache"
OUT_PATH = REPO_ROOT / "client" / "ui-overrides" / "Interface" / "FrameXML" / "ClassAdvancementData.lua"

RETIRED_TAB_ID = 60800

# (class file token, ChrClasses id) in the order the window lists them.
CLASSES = (
    ("WARRIOR", 1), ("PALADIN", 2), ("HUNTER", 3), ("ROGUE", 4), ("PRIEST", 5),
    ("DEATHKNIGHT", 6), ("SHAMAN", 7), ("MAGE", 8), ("WARLOCK", 9), ("DRUID", 11),
)
CLASS_BY_ID = {class_id: token for token, class_id in CLASSES}

# TalentTab id -> SkillLine id of the spec (SkillLine.dbc category 7). Nothing in the DBCs links the two.
SPEC_SKILL_LINES = {
    161: 26, 164: 256, 163: 257,        # Warrior: Arms, Fury, Protection
    382: 594, 383: 267, 381: 184,       # Paladin: Holy, Protection, Retribution
    361: 50, 363: 163, 362: 51,         # Hunter: Beast Mastery, Marksmanship, Survival
    182: 253, 181: 38, 183: 39,         # Rogue: Assassination, Combat, Subtlety
    201: 613, 202: 56, 203: 78,         # Priest: Discipline, Holy, Shadow
    398: 770, 399: 771, 400: 772,       # Death Knight: Blood, Frost, Unholy
    261: 375, 263: 373, 262: 374,       # Shaman: Elemental, Enhancement, Restoration
    81: 237, 41: 8, 61: 6,              # Mage: Arcane, Fire, Frost
    302: 355, 303: 354, 301: 593,       # Warlock: Affliction, Demonology, Destruction
    283: 574, 281: 134, 282: 573,       # Druid: Balance, Feral Combat, Restoration
}

SPELL_ATTR0_PASSIVE = 0x00000040
SPELL_ATTR0_DO_NOT_DISPLAY = 0x00000080
SPELL_EFFECT_LEARN_SPELL = 36
SPELL_EFFECT_LANGUAGE = 39
SPELL_EFFECT_TRADE_SKILL = 47
SPELL_EFFECT_PROFICIENCY = 60
SPELL_EFFECT_SKILL = 118
SPELL_EFFECT_APPLY_AURA = 6
SPELL_AURA_MOUNTED = 78

LEARNED_ON_SKILL_VALUE = 1
LEARNED_ON_SKILL_LEARN = 2
TRAINER_TYPE_CLASS = 0
TRAINER_COLUMNS = ("Id", "Type", "Requirement", "Greeting", "VerifiedBuild")
SPELL_RANKS_COLUMNS = ("first_spell_id", "spell_id", "rank")


class DataError(ValueError):
    """An input the table cannot be built from (a missing stock file, a class without three tabs, ...)."""


@dataclass
class Inputs:
    """Everything `build_table` reads, as plain dicts (so the tests can hand it fixtures).

    `spells` / `slas` are Spell.dbc / SkillLineAbility.dbc rows by id; `talents` / `tabs` the final rows; `skill_lines`
    SkillLine.dbc rows; `trainer_rows` the `trainer_spell` rows (TrainerId, SpellId) -> row; `class_trainers`
    class id -> in-use trainer ids; `chains` first_spell_id -> [(spell_id, rank)]; `superseded` the stock ranks a
    single-rank survivor replaced; `retired_spells` spells whose declaration retired them."""

    talents: dict[int, dict]
    tabs: dict[int, dict]
    spells: dict[int, dict]
    slas: dict[int, dict]
    skill_lines: dict[int, dict]
    trainer_rows: dict[tuple[int, int], dict]
    class_trainers: dict[int, set[int]]
    chains: dict[int, list[tuple[int, int]]]
    superseded: dict[int, int] = field(default_factory=dict)
    retired_spells: set[int] = field(default_factory=set)
    class_tokens: dict[int, str] = field(default_factory=dict)  # ChrClasses id -> Filename, for the check below


# --- loading -------------------------------------------------------------------------------------------------------


class _NoReuse:
    """`build.build_spell_row` wants a ReuseContext only to turn friendly units into cast time / duration / range /
    radius indices; the table reads none of them."""

    def cast_time_index(self, *_args) -> int:
        return 0

    range_index = duration_index = radius_index = cast_time_index


def _merge_declared(base: dict[int, dict], entries: list[dict], builder) -> dict[int, dict]:
    out = dict(base)
    for entry in entries:
        row = builder(entry)
        out[int(row["ID"])] = row
    return out


def load_inputs(progress=lambda _label: None) -> Inputs:
    """Loads the DSL like `generate.py --check` does (every class, no `only=`) and the replayed world state. Needs an
    active `sqlcorpus` (the caller's `with`)."""
    ids_cfg = source.load_ids(SOURCE_DIR / "ids.yaml")
    spell_entries = source.load_spells_csv(SOURCE_DIR / "spells")
    talents = source.load_talents_yaml(SOURCE_DIR / "talents")
    trainer_index = trainer_state.load_trainer_index()
    spell_table_index = spell_tables.load_spell_table_index()
    existing_talents = state.load_existing_rows(dbcfmt.TALENT)
    sla_cache: dict[str, dict[int, dict]] = {}

    def live_skilllineabilities() -> dict[int, dict]:
        if "rows" not in sla_cache:
            sla_cache["rows"] = state.load_existing_rows(dbcfmt.SKILLLINEABILITY)
        return sla_cache["rows"]

    live_data = spell_tables.dsl_live_data(
        existing_talents, Lazy(spell_tables.load_live_item_template_rows), live_skilllineabilities,
        lambda: state.load_stock_rows(dbcfmt.CHRCLASSES), lambda: state.load_stock_rows(dbcfmt.SKILLLINEABILITY),
        lambda: state.load_stock_rows(dbcfmt.SKILLLINE), **spell_tables.stock_enchant_loaders(),
    )
    progress("loaded the live state the declarations validate against")
    dsl = dsl_registry.load_classes_dir(
        SOURCE_DIR / "classes", ids_cfg=ids_cfg, trainer_index=trainer_index,
        existing_group_ids={key[0] for key in spell_table_index.live_keys("spell_group")},
        shapeshift_index=Lazy(lambda: state.load_stock_rows(dbcfmt.SPELLSHAPESHIFTFORM)),
        existing_creature_rows=Lazy(lambda: {
            int(r["entry"]): r for r in spell_tables.load_creature_table_index().live_rows("creature_template")
        }),
        creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
        creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS, live_data=live_data,
    )
    progress(f"loaded source/classes ({sum(len(v) for v in dsl.values())} entries)")
    for key in ("tabs", "talents", "skill_line_abilities"):  # generate._merge_dsl_sources, minus the CSV overlap check
        seen = {e["id"] for e in talents[key]}
        clash = [e["id"] for e in dsl[key] if e["id"] in seen]
        if clash:
            raise DataError(f"{key} entries {clash} are in source/talents/*.yaml and in source/classes")
        talents[key].extend(dsl[key])
    spell_ids = {e["id"] for e in spell_entries}
    clash = [e["id"] for e in dsl["spells"] if e["id"] in spell_ids]
    if clash:
        raise DataError(f"spells {clash[:5]} are in source/spells/*.csv and in source/classes")
    spell_entries.extend(dsl["spells"])

    stock_spells = state.load_stock_rows(dbcfmt.SPELL)
    if not stock_spells:
        raise DataError(f"no stock Spell.dbc in {state.BASE_DBC_DIR} (copy it from the client, see README.md)")
    reuse = _NoReuse()
    spells = _merge_declared(stock_spells, spell_entries, lambda e: build.build_spell_row(e, reuse))
    final_talents = _merge_declared(state.load_stock_rows(dbcfmt.TALENT), talents["talents"], build.build_talent_row)
    final_tabs = _merge_declared(state.load_stock_rows(dbcfmt.TALENTTAB), talents["tabs"], build.build_talenttab_row)
    slas = _merge_declared(
        state.load_stock_rows(dbcfmt.SKILLLINEABILITY), talents["skill_line_abilities"],
        build.build_skilllineability_row,
    )
    skill_lines = state.load_stock_rows(dbcfmt.SKILLLINE)
    progress("built the talent, spell and skill line views")

    removed = {(int(r["TrainerId"]), int(r["SpellId"])) for r in dsl["trainer_removals"]}
    trainer_rows = trainer_pricing.replay_trainer_spells()
    for row in dsl["trainer_spells"]:
        trainer_rows[(int(row["TrainerId"]), int(row["SpellId"]))] = row
    trainer_rows = {key: row for key, row in trainer_rows.items() if key not in removed}
    class_trainers: dict[int, set[int]] = {}
    for row in trainer_state.load_replayed_table_rows("trainer", TRAINER_COLUMNS, ("Id",), fill_missing=True):
        if int(row["Type"]) == TRAINER_TYPE_CLASS and not trainer_index.trainer_problems(int(row["Id"])):
            class_trainers.setdefault(int(row["Requirement"]), set()).add(int(row["Id"]))

    unranked = {int(r["spell_id"]) for r in dsl["spell_rank_removals"]}
    chains: dict[int, list[tuple[int, int]]] = {}
    for row in trainer_state.load_replayed_table_rows(
        "spell_ranks", SPELL_RANKS_COLUMNS, ("first_spell_id", "spell_id"),
    ):
        if int(row["spell_id"]) not in unranked:
            chains.setdefault(int(row["first_spell_id"]), []).append((int(row["spell_id"]), int(row["rank"])))
    progress("replayed trainer_spell, trainer and spell_ranks")
    stock_talents = state.load_stock_rows(dbcfmt.TALENT)
    retired = {int(r["SpellId"]) for r in dsl["trainer_removals"]}
    for entry in dsl["retired_talents"]:
        row = stock_talents.get(int(entry["id"]))
        retired.update(int(row[f"SpellRank_{n}"]) for n in range(1, 10) if row and row[f"SpellRank_{n}"])
    return Inputs(
        talents=final_talents, tabs=final_tabs, spells=spells, slas=slas, skill_lines=skill_lines,
        trainer_rows=trainer_rows, class_trainers=class_trainers, chains=chains,
        superseded=superseded_ranks.superseded_ranks(
            load_spell_ranks_chains(), superseded_ranks.survivor_ids(spell_entries),
        ),
        retired_spells=retired,
        class_tokens={cid: str(r["Filename"]).upper() for cid, r in state.load_stock_rows(dbcfmt.CHRCLASSES).items()},
    )


# --- the table -----------------------------------------------------------------------------------------------------

_NON_ABILITY_EFFECTS = frozenset({
    25,                          # WEAPON (weapon proficiency)
    26,                          # DEFENSE (the Defense skill)
    SPELL_EFFECT_LANGUAGE,
    44,                          # SKILL_STEP
    SPELL_EFFECT_TRADE_SKILL,
    SPELL_EFFECT_PROFICIENCY,
    SPELL_EFFECT_SKILL,
})


def _effects(row: dict) -> list[tuple[int, int, int]]:
    """(effect type, aura, trigger spell) of the row's used effect slots."""
    return [
        (int(row[f"Effect_{n}"]), int(row[f"EffectAura_{n}"]), int(row[f"EffectTriggerSpell_{n}"]))
        for n in (1, 2, 3) if int(row[f"Effect_{n}"])
    ]


def is_passive(row: dict) -> bool:
    return bool(int(row["Attributes"]) & SPELL_ATTR0_PASSIVE)


def ability_exclusion(row: dict) -> str | None:
    """Why a spell is not a class ability the window lists, or None. Hidden helpers, proficiencies and skills,
    languages, professions and mounts."""
    if int(row["Attributes"]) & SPELL_ATTR0_DO_NOT_DISPLAY:
        return "hidden"
    effects = _effects(row)
    if effects and all(kind in _NON_ABILITY_EFFECTS for kind, _aura, _trigger in effects):
        return "proficiency, skill, language or profession"
    if any(aura == SPELL_AURA_MOUNTED for _kind, aura, _trigger in effects):
        return "mount"
    return None


@dataclass
class Dropped:
    """A candidate a rule left out, for `--report`."""

    cls: str
    spell: int
    name: str
    how: str
    reason: str


@dataclass
class Result:
    table: dict[str, dict]
    dropped: list[Dropped] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class _Chains:
    """Rank chains: any rank id -> the chain's highest-rank spell that exists."""

    def __init__(self, chains: dict[int, list[tuple[int, int]]], spells: dict[int, dict]):
        self.members: dict[int, list[int]] = {}  # any member -> every member, lowest rank first
        self.top: dict[int, int] = {}
        for first, ranks in chains.items():
            ordered = [spell for spell, _rank in sorted(ranks, key=lambda item: (item[1], item[0]))]
            ordered = [spell for spell in ordered if spell in spells]
            if not ordered:
                continue
            for spell in ordered:
                self.members[spell] = ordered
                self.top[spell] = ordered[-1]

    def top_of(self, spell: int) -> int:
        return self.top.get(spell, spell)

    def family(self, spell: int) -> list[int]:
        return self.members.get(spell, [spell])


def spec_tabs(inp: Inputs, class_id: int) -> list[dict]:
    """The class's three player tabs, in TalentTab OrderIndex order."""
    mask = 1 << (class_id - 1)
    tabs = [
        row for row in inp.tabs.values()
        if int(row["ID"]) != RETIRED_TAB_ID and int(row["ClassMask"]) & mask and not int(row["PetTalentMask"])
    ]
    tabs.sort(key=lambda row: (int(row["OrderIndex"]), int(row["ID"])))
    return tabs


def tab_entry(inp: Inputs, row: dict) -> dict:
    tab_id = int(row["ID"])
    if tab_id not in SPEC_SKILL_LINES:
        raise DataError(f"talent tab {tab_id} ({row['Name_Lang_enUS']}) has no entry in SPEC_SKILL_LINES")
    skill_line = SPEC_SKILL_LINES[tab_id]
    if skill_line not in inp.skill_lines:
        raise DataError(f"SPEC_SKILL_LINES: skill line {skill_line} (tab {tab_id}) is not in SkillLine.dbc")
    talents = []
    for talent in inp.talents.values():
        if int(talent["TabID"]) != tab_id:
            continue
        ranks = [int(talent[f"SpellRank_{n}"]) for n in range(1, 10)]
        while ranks and not ranks[-1]:
            ranks.pop()
        if int(talent["PrereqTalent_2"]) or int(talent["PrereqTalent_3"]):
            raise DataError(f"talent {talent['ID']} has more than one prerequisite, which the table cannot hold")
        entry = {"id": int(talent["ID"]), "row": int(talent["TierID"]), "col": int(talent["ColumnIndex"]),
                 "ranks": ranks}
        if int(talent["PrereqTalent_1"]):
            entry["req"] = int(talent["PrereqTalent_1"])
            entry["reqRank"] = int(talent["PrereqRank_1"]) + 1  # the DBC stores the rank 0-based
        talents.append(entry)
    talents.sort(key=lambda t: (t["row"], t["col"], t["id"]))
    return {"id": tab_id, "name": str(row["Name_Lang_enUS"]), "art": str(row["BackgroundFile"]),
            "skillLine": skill_line, "talents": talents}


def _spell_name(inp: Inputs, spell: int) -> str:
    row = inp.spells.get(spell)
    return str(row["Name_Lang_enUS"]) if row else ""


def class_abilities(inp: Inputs, class_id: int, tabs: list[dict], chains: _Chains, result: Result) -> list[dict]:
    """The class's ability entries (unsorted), appending every candidate a rule left out to `result.dropped`."""
    token = CLASS_BY_ID[class_id]
    mask = 1 << (class_id - 1)
    line_section = {tab["skillLine"]: index for index, tab in enumerate(tabs, start=1)}
    found: dict[int, dict] = {}  # ability (top rank id) -> entry
    sla_by_spell: dict[int, list[dict]] = {}
    for row in inp.slas.values():
        sla_by_spell.setdefault(int(row["Spell"]), []).append(row)

    def drop(spell: int, how: str, reason: str) -> None:
        result.dropped.append(Dropped(token, spell, _spell_name(inp, spell), how, reason))

    def section_of(spell: int) -> int:
        """The tab whose skill line carries a SkillLineAbility row of the spell (or of one of its ranks)."""
        lines = sorted(
            (int(row["ID"]), int(row["SkillLine"]))
            for member in chains.family(spell) for row in sla_by_spell.get(member, ())
            if int(row["SkillLine"]) in line_section and int(row["ClassMask"]) in (0, mask)
        )
        return line_section[lines[0][1]] if lines else 0

    def accept(spell: int, how: str, **fields) -> None:
        """Adds `spell` (any rank) as an ability unless a rule drops it or an earlier source already has it."""
        if spell in inp.superseded and how != "trainer":  # a trainer that still teaches a rank is the truth
            drop(spell, how, f"rank replaced by single-rank survivor {inp.superseded[spell]}")
            return
        top = chains.top_of(spell)
        row = inp.spells.get(top)
        if row is None:
            drop(spell, how, "no such spell")
            return
        reason = ability_exclusion(row)
        if reason:
            drop(top, how, reason)
            return
        if top in found:
            known = found[top]
            if known["how"] != how:
                result.notes.append(
                    f"{token} {top} {_spell_name(inp, top)}: also {how} (kept as {known['how']})"
                )
            elif how == "talent" and fields["talent"] != known["talent"]:
                result.notes.append(
                    f"{token} {top} {_spell_name(inp, top)}: also granted by talent {fields['talent']} "
                    f"(kept talent {known['talent']})"
                )
            elif how == "trainer" and fields["level"] < known["level"]:
                known["level"] = fields["level"]
            return
        found[top] = {"spell": top, "how": how, **fields}

    # talents first: they win over a trainer or start row of the same spell
    for tab in tabs:
        section = line_section[tab["skillLine"]]
        for talent in tab["talents"]:
            for rank_spell in talent["ranks"]:
                row = inp.spells.get(rank_spell)
                if row is None:
                    continue
                taught = [trigger for kind, _aura, trigger in _effects(row) if kind == SPELL_EFFECT_LEARN_SPELL]
                if taught:
                    for spell in taught:
                        accept(spell, "talent", section=section, talent=talent["id"])
                elif int(inp.talents[talent["id"]]["Flags"]) and not is_passive(row):
                    accept(rank_spell, "talent", section=section, talent=talent["id"])

    start_levels: dict[int, int] = {}
    start_superseded: dict[int, int] = {}
    for sla in inp.slas.values():
        if (
            int(sla["SkillLine"]) in line_section and int(sla["ClassMask"]) in (0, mask)
            and int(sla["AcquireMethod"]) in (LEARNED_ON_SKILL_VALUE, LEARNED_ON_SKILL_LEARN)
        ):
            spell = int(sla["Spell"])
            rank = int(sla["MinSkillLineRank"])
            level = max(1, -(-rank // 5)) if int(sla["AcquireMethod"]) == LEARNED_ON_SKILL_VALUE else 1
            start_levels[spell] = min(level, start_levels.get(spell, level))
            if int(sla["SupercededBySpell"]) and int(sla["SupercededBySpell"]) != spell:
                start_superseded[chains.top_of(spell)] = int(sla["SupercededBySpell"])
    for spell, level in sorted(start_levels.items()):
        accept(spell, "start", section=section_of(spell), level=level)

    trainers = inp.class_trainers.get(class_id, set())
    levels: dict[int, int] = {}
    for (trainer_id, spell), row in inp.trainer_rows.items():
        if trainer_id in trainers:
            levels[spell] = min(int(row["ReqLevel"]), levels.get(spell, 255))
    by_top: dict[int, int] = {}  # lowest level over the chain, keyed by its top
    for spell, level in levels.items():
        by_top[chains.top_of(spell)] = min(level, by_top.get(chains.top_of(spell), 255))
    for spell, level in sorted(levels.items()):
        top = chains.top_of(spell)
        accept(spell, "trainer", section=section_of(top), level=by_top[top])

    entries = []
    for top, entry in found.items():
        if entry["how"] != "trainer" and top in inp.retired_spells:
            drop(top, entry["how"], "retired")
        elif entry["how"] == "start" and start_superseded.get(top) in found:
            drop(top, "start", f"SkillLineAbility says it is superseded by {start_superseded[top]}")
        else:
            entries.append(entry)
    return entries


def sort_key(inp: Inputs, entry: dict) -> tuple:
    """Section, then level (talent abilities last within a section), then name, then spell id."""
    level = entry.get("level")
    return (entry["section"], 1 if level is None else 0, level or 0, _spell_name(inp, entry["spell"]).lower(),
            entry["spell"])


def build_table(inp: Inputs) -> Result:
    """The whole table from `inp` (pure: no file or SQL access)."""
    for class_id, token in CLASS_BY_ID.items():
        if inp.class_tokens and inp.class_tokens.get(class_id) != token:
            raise DataError(f"ChrClasses {class_id} is {inp.class_tokens.get(class_id)!r}, expected {token!r}")
    chains = _Chains(inp.chains, inp.spells)
    result = Result(table={})
    for token, class_id in CLASSES:
        tab_rows = spec_tabs(inp, class_id)
        if len(tab_rows) != 3:
            raise DataError(f"{token} has {len(tab_rows)} player talent tabs ({[r['ID'] for r in tab_rows]}), not 3")
        tabs = [tab_entry(inp, row) for row in tab_rows]
        abilities = class_abilities(inp, class_id, tabs, chains, result)
        abilities.sort(key=lambda entry: sort_key(inp, entry))
        result.table[token] = {"classId": class_id, "tabs": tabs, "abilities": abilities}
    return result


# --- output --------------------------------------------------------------------------------------------------------

HEADER = (
    "-- Generated by apps/dbc-tools/write_class_advancement.py from the talent and spell declarations in\n"
    "-- apps/dbc-tools/source/classes over the stock DBCs, and the class trainers' trainer_spell rows. Do not edit.\n"
    "-- CLASS_ADVANCEMENT[class file token] = { classId, tabs = { { id, name, art, skillLine, talents } x 3 },\n"
    "-- abilities = { { spell, section, level, how, talent } } } for the class advancement window\n"
    "-- (.agents/plans/classless-ui/classless-ui.PLAN.md, section 4).\n"
)
_LUA_ESCAPES = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r", "\t": "\\t"}


def lua_string(text: str) -> str:
    """`text` as a double-quoted Lua string literal: backslash, quote and control characters escaped, anything else
    (UTF-8 included) as is."""
    out = []
    for ch in text:
        if ch in _LUA_ESCAPES:
            out.append(_LUA_ESCAPES[ch])
        elif ord(ch) < 0x20 or ord(ch) == 0x7F:
            out.append(f"\\{ord(ch):03d}")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def _talent_line(talent: dict) -> str:
    parts = [f"id = {talent['id']}", f"row = {talent['row']}", f"col = {talent['col']}",
             "ranks = { " + ", ".join(str(r) for r in talent["ranks"]) + " }"]
    if "req" in talent:
        parts += [f"req = {talent['req']}", f"reqRank = {talent['reqRank']}"]
    return "{ " + ", ".join(parts) + " }"


def _ability_line(ability: dict) -> str:
    parts = [f"spell = {ability['spell']}", f"section = {ability['section']}"]
    if "level" in ability:
        parts.append(f"level = {ability['level']}")
    parts.append(f"how = {lua_string(ability['how'])}")
    if "talent" in ability:
        parts.append(f"talent = {ability['talent']}")
    return "{ " + ", ".join(parts) + " }"


def render_lua(table: dict[str, dict]) -> str:
    tokens = [lua_string(token) for token, _ in CLASSES]
    lines = [
        HEADER + "CLASS_ADVANCEMENT_ORDER = {", "  " + ", ".join(tokens[:5]) + ",", "  " + ", ".join(tokens[5:]) + ",",
        "}", "CLASS_ADVANCEMENT = {",
    ]
    for token, _class_id in CLASSES:
        entry = table[token]
        lines += [f"  [{lua_string(token)}] = {{", f"    classId = {entry['classId']},", "    tabs = {"]
        for tab in entry["tabs"]:
            lines.append(
                f"      {{ id = {tab['id']}, name = {lua_string(tab['name'])}, art = {lua_string(tab['art'])}, "
                f"skillLine = {tab['skillLine']},"
            )
            lines.append("        talents = {")
            lines += [f"          {_talent_line(t)}," for t in tab["talents"]]
            lines.append("        } },")
        lines += ["    },", "    abilities = {"]
        lines += [f"      {_ability_line(a)}," for a in entry["abilities"]]
        lines += ["    },", "  },"]
    lines.append("}")
    return "\n".join(lines) + "\n"


def report_lines(result: Result) -> list[str]:
    """Per-class counts, the dropped candidates and the notes, for `--report`."""
    lines = ["class        talents/tab      abilities  section0  section1  section2  section3  trainer  start  talent"]
    for token, _class_id in CLASSES:
        entry = result.table[token]
        abilities = entry["abilities"]
        by_section = [sum(1 for a in abilities if a["section"] == s) for s in range(4)]
        by_how = [sum(1 for a in abilities if a["how"] == h) for h in ("trainer", "start", "talent")]
        lines.append(
            f"{token:<12} {'/'.join(str(len(t['talents'])) for t in entry['tabs']):<16} {len(abilities):>9}  "
            + "  ".join(f"{n:>8}" for n in by_section) + "  " + "  ".join(f"{n:>7}" for n in by_how)
        )
    lines.append("")
    lines.append(f"dropped candidates ({len(result.dropped)}):")
    lines += [f"  {d.cls:<11} {d.spell:>7} {d.name!r} ({d.how}): {d.reason}" for d in result.dropped]
    lines.append("")
    lines.append(f"notes ({len(result.notes)}):")
    lines += [f"  {n}" for n in result.notes]
    return lines


# --- entry point ---------------------------------------------------------------------------------------------------


def compute(progress=lambda _label: None) -> tuple[Result, Inputs]:
    """Loads everything and builds the table. Activates (and leaves active) a `sqlcorpus` over the cache directory."""
    import generate  # noqa: PLC0415 - heavy; only the cache version is wanted from it

    sqlcorpus.activate(CACHE_DIR, generate.cache_code_version())
    try:
        inp = load_inputs(progress)
        return build_table(inp), inp
    finally:
        sqlcorpus.deactivate()
        dsl_registry.stop_provenance()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--check", action="store_true", help="exit 1 if the file is stale, write nothing")
    parser.add_argument("--out", type=Path, default=OUT_PATH, help=f"output file (default: {OUT_PATH})")
    parser.add_argument("--report", action="store_true", help="print per-class counts and every dropped candidate")
    args = parser.parse_args()
    start = time.monotonic()
    try:
        result, _inputs = compute(lambda label: print(f"[{time.monotonic() - start:6.1f}s] {label}", flush=True))
    except DataError as error:
        print(f"ERROR: {error}")
        return 1
    if args.report:
        print("\n".join(report_lines(result)))
    text = render_lua(result.table)
    stale = not args.out.is_file() or args.out.read_bytes() != text.encode("utf-8")
    if args.check:
        if stale:
            print(f"stale: {args.out}")
        return 1 if stale else 0
    if stale:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(text.encode("utf-8"))
        print(f"wrote {args.out} ({len(text.encode('utf-8'))} bytes)")
    else:
        print(f"{args.out} is current")
    return 0


if __name__ == "__main__":
    sys.exit(main())
