"""Per-class "GCD haste" aura spells (`.agents/plans/melee-haste-gcd/melee-haste-gcd.PLAN.md`, stage T1).

`Spell::TriggerGlobalCooldown` hastes a 1.5s GCD (`StartRecoveryCategory` 133, `StartRecoveryTime` 1500) only
for spells that are not `DmgClass` MELEE/RANGED and carry neither `USES_RANGED_SLOT` (0x2) nor `IS_ABILITY`
(0x10). Melee strikes, ranged shots and "ability"-flagged utility keep the full 1.5s however much haste the
player has. Both the server and the client apply `SPELLMOD_GLOBAL_COOLDOWN` (SpellModOp 21) spell mods to those
spells, so one hidden passive aura per class family, whose classmasks cover exactly the unhasted abilities,
can shorten them. T2 (C++) keeps the pct mod's amount in sync with the player's haste; this module only
produces the data the mod lives on.

Everything here is computed on every `generate.py` run from the merged spell data (base DBC, promoted
migrations, this run's DSL rows), so a later rework ability is covered automatically and a bit shared with an
ability the core already hastes (which would double-dip) stops the run instead of shipping. The human decisions
live in `source/gcd_haste.py`: the aura IDs, `EXCLUDE`, the tick and the placeholder amount.

The mask is one value used by two readers that disagree about a few spells' `SpellFamilyFlags`: the client
reads Spell.dbc as shipped, the server rewrites about 15 spells at load (`SpellInfoCorrections.cpp`, mirrored
in the policy's `SERVER_FLAG_FIXES`). A candidate contributes its bits under both views, and a conflict under
either view is an error.

Mask columns: the **letter** of `EffectSpellClassMask{A,B,C}_{1,2,3}` is the effect index (A=Effect_1,
B=Effect_2), the number is the dword. Effect 0 (melee mask) therefore goes in `..A_n`, effect 1 (ranged mask)
in `..B_n`. An all-zero classmask matches every spell of the family, so an empty mask is never emitted as a
mod at all: that effect is left empty.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, Iterable

from .dsl import model, registry
from .dsl.constants import RANGE_SELF

POLICY_FILE = Path(__file__).resolve().parents[1] / "source" / "gcd_haste.py"

FAMILY_NAMES = {
    4: "Warrior", 10: "Paladin", 9: "Hunter", 7: "Druid", 11: "Shaman",
    15: "Death Knight", 6: "Priest", 5: "Warlock", 8: "Rogue", 3: "Mage",
}
HUNTER = 9

GCD_CATEGORY = 133
GCD_TIME = 1500
DMG_CLASS_MELEE = 2
DMG_CLASS_RANGED = 3
ATTR0_USES_RANGED_SLOT = 0x2
ATTR0_IS_ABILITY = 0x10
ATTR0_PASSIVE = 0x40
ATTR0_DO_NOT_DISPLAY = 0x80
ATTR0_DO_NOT_LOG = 0x100

SPELL_EFFECT_APPLY_AURA = 6
SPELL_AURA_ADD_PCT_MODIFIER = 108
SPELL_AURA_PERIODIC_DUMMY = 226
SPELLMOD_GLOBAL_COOLDOWN = 21
TARGET_UNIT_CASTER = 1

MELEE = "melee"
RANGED = "ranged"

Mask = tuple[int, int, int]
EMPTY_MASK: Mask = (0, 0, 0)

# The aura's own row. 464 = IS_ABILITY | PASSIVE | DO_NOT_DISPLAY | DO_NOT_LOG, copied from Heart of the
# Crusader 20337 (the stock hidden passive that also carries a GCD spell mod) and Biting Cold 200010, the
# DSL's hidden-passive precedent. CastingTimeIndex 1 = instant and EquippedItemClass -1 = none, as 20337.
AURA_ATTRIBUTES = ATTR0_PASSIVE | ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG | ATTR0_IS_ABILITY
SPELL_CAST_TIME_INSTANT = 1
SCHOOL_PHYSICAL = 1  # SchoolMask, as Heart of the Crusader 20337 has it


class GcdHasteError(ValueError):
    """The merged data and the policy cannot produce a safe set of masks, or the policy is malformed."""


class Policy:
    def __init__(
        self,
        aura_ids: dict[int, int],
        exclude: dict[int, str],
        tick_ms: int,
        placeholder_pct: int,
        pet_skill_lines: Iterable[int],
        not_castable: dict[int, str] | None = None,
        server_flag_fixes: dict[int, Mask] | None = None,
        server_flag_rules: Iterable[Callable[[dict], Mask | None]] = (),
    ):
        unknown = sorted(set(aura_ids) - set(FAMILY_NAMES))
        if unknown:
            raise GcdHasteError(f"FAMILY_AURA_IDS names unknown SpellFamilyName(s) {unknown}")
        if len(set(aura_ids.values())) != len(aura_ids):
            raise GcdHasteError("FAMILY_AURA_IDS gives two families the same aura spell ID")
        for table, label in ((exclude, "EXCLUDE"), (not_castable or {}, "NOT_CASTABLE")):
            for spell_id, reason in table.items():
                if not str(reason).strip():
                    raise GcdHasteError(f"{label}[{spell_id}] needs a reason")
        if tick_ms <= 0:
            raise GcdHasteError(f"TICK_MS must be > 0, got {tick_ms}")
        if not -99 <= placeholder_pct <= 0:
            raise GcdHasteError(f"PLACEHOLDER_PCT must be in -99..0, got {placeholder_pct}")
        self.aura_ids = {int(k): int(v) for k, v in aura_ids.items()}
        self.exclude = {int(k): str(v) for k, v in exclude.items()}
        self.tick_ms = int(tick_ms)
        self.placeholder_pct = int(placeholder_pct)
        self.pet_skill_lines = frozenset(int(s) for s in pet_skill_lines)
        self.not_castable = {int(k): str(v) for k, v in (not_castable or {}).items()}
        self.server_flag_fixes = {int(k): _partial_mask(v) for k, v in (server_flag_fixes or {}).items()}
        self.server_flag_rules = tuple(server_flag_rules)


def load_policy(path: Path = POLICY_FILE) -> Policy:
    """The policy from the data file, loaded by path since `source/` is data, not a package."""
    spec = importlib.util.spec_from_file_location("_gcd_haste_policy", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return Policy(
        module.FAMILY_AURA_IDS, module.EXCLUDE, module.TICK_MS, module.PLACEHOLDER_PCT,
        module.PET_SKILL_LINES, getattr(module, "NOT_CASTABLE", {}), getattr(module, "SERVER_FLAG_FIXES", {}),
        getattr(module, "SERVER_FLAG_RULES", ()),
    )


def _u32(value) -> int:
    return int(value or 0) & 0xFFFFFFFF


def _mask(words) -> Mask:
    words = tuple(_u32(w) for w in words)
    if len(words) != 3:
        raise GcdHasteError(f"a SpellFamilyFlags mask has 3 dwords, got {words!r}")
    return words  # type: ignore[return-value]


def _partial_mask(words) -> tuple:
    words = tuple(None if w is None else _u32(w) for w in words)
    if len(words) != 3:
        raise GcdHasteError(f"a SpellFamilyFlags fix has 3 dwords (None = unchanged), got {words!r}")
    return words


def client_flags(row: dict) -> Mask:
    """`SpellFamilyFlags` as Spell.dbc ships them, which is what the client matches spell mods against."""
    return _mask(row.get(f"SpellClassMask_{n}", 0) for n in (1, 2, 3))


def server_flags(row: dict, policy: Policy) -> Mask:
    """`SpellFamilyFlags` after the server's load-time rewrites (`policy.server_flag_fixes`, a dword of None
    meaning "left as in the DBC", then `policy.server_flag_rules`, each applied to the row as the fixes so far
    left it)."""
    words = client_flags(row)
    fixed = policy.server_flag_fixes.get(int(row["ID"]))
    if fixed is not None:
        words = _mask(w if f is None else f for w, f in zip(words, fixed))
    for rule in policy.server_flag_rules:
        # a rule sees the row as the table fixes left it, as SpellInfoCorrections.cpp applies them in order
        result = rule({**row, **{f"SpellClassMask_{n}": w for n, w in enumerate(words, 1)}})
        if result is not None:
            words = _mask(result)
    return words


def _or(a: Mask, b: Mask) -> Mask:
    return (a[0] | b[0], a[1] | b[1], a[2] | b[2])


def _and(a: Mask, b: Mask) -> Mask:
    return (a[0] & b[0], a[1] & b[1], a[2] & b[2])


def _bits(mask: Mask) -> list[int]:
    return [d * 32 + b for d in range(3) for b in range(32) if mask[d] >> b & 1]


def is_empty(mask: Mask) -> bool:
    return not any(mask)


def _on_gcd(row: dict) -> bool:
    return (
        int(row.get("StartRecoveryCategory", 0)) == GCD_CATEGORY
        and not int(row.get("Attributes", 0)) & ATTR0_PASSIVE
    )


def skipped_by_core_haste(row: dict) -> bool:
    """A 1.5s GCD spell the core's haste branch leaves alone: DmgClass MELEE/RANGED, or USES_RANGED_SLOT /
    IS_ABILITY. These are the candidates (when player-learnable)."""
    return (
        _on_gcd(row)
        and int(row.get("StartRecoveryTime", 0)) == GCD_TIME
        and (
            int(row.get("DefenseType", 0)) in (DMG_CLASS_MELEE, DMG_CLASS_RANGED)
            or bool(int(row.get("Attributes", 0)) & (ATTR0_USES_RANGED_SLOT | ATTR0_IS_ABILITY))
        )
    )


def hasted_by_core(row: dict) -> bool:
    """A GCD spell the core already hastes (or, at 1.0-1.4s, clamps): category 133, StartRecoveryTime
    1000-1500, non-passive, and passing the DmgClass/attribute conditions. A bit shared with one of these
    would haste it twice."""
    return (
        _on_gcd(row)
        and 1000 <= int(row.get("StartRecoveryTime", 0)) <= GCD_TIME
        and int(row.get("DefenseType", 0)) not in (DMG_CLASS_MELEE, DMG_CLASS_RANGED)
        and not int(row.get("Attributes", 0)) & (ATTR0_USES_RANGED_SLOT | ATTR0_IS_ABILITY)
    )


def haste_source(row: dict, family: int) -> str:
    """Plan D3: MELEE-class spells use melee haste, RANGED-class or USES_RANGED_SLOT spells ranged haste, and
    utility "abilities" (shouts, seals, forms) ranged for a Hunter and melee for everyone else."""
    if int(row.get("DefenseType", 0)) == DMG_CLASS_MELEE:
        return MELEE
    if int(row.get("DefenseType", 0)) == DMG_CLASS_RANGED or int(row.get("Attributes", 0)) & ATTR0_USES_RANGED_SLOT:
        return RANGED
    return RANGED if family == HUNTER else MELEE


def pet_talent_tab_ids(talent_tabs: Iterable[dict]) -> set[int]:
    """Talent tabs that belong to pets (Tenacity, Ferocity, Cunning): a nonzero `PetTalentMask`."""
    return {int(t["ID"]) for t in talent_tabs if int(t.get("PetTalentMask", 0))}


def learnable_spell_ids(
    skill_line_abilities: Iterable[dict],
    talents: Iterable[dict],
    dsl_player_castable: Iterable[int],
    policy: Policy,
    pet_tabs: Iterable[int] = (),
    superseded: Iterable[int] = (),
) -> set[int]:
    """Spells a player can learn: on a SkillLineAbility row outside the pet skill lines, a rank of a talent
    outside the pet tabs, or a DSL spell `registry.looks_player_castable` accepts.

    Pet abilities are cast by the pet, so the player's spell mods never touch them: a DSL spell that is on a
    pet skill line or is a pet-talent rank is NOT rescued by the heuristic (the DSL carries stock pet spells
    as reference copies). `superseded` are the ranks the single-rank conversion collapsed into a survivor
    (`superseded_ranks.superseded`): stock still lists them but nothing teaches them any more.
    `policy.not_castable` are spells no player can cast although the data says otherwise."""
    pet_lines = policy.pet_skill_lines
    pet_tabs = set(pet_tabs)
    pet_spells: set[int] = set()
    ids: set[int] = set()
    for row in skill_line_abilities:
        (pet_spells if int(row["SkillLine"]) in pet_lines else ids).add(int(row["Spell"]))
    for talent in talents:
        ranks = {int(talent[f"SpellRank_{n}"]) for n in range(1, 10) if talent.get(f"SpellRank_{n}")}
        (pet_spells if int(talent["TabID"]) in pet_tabs else ids).update(ranks)
    ids.update(int(i) for i in dsl_player_castable if int(i) not in pet_spells)
    return ids - {int(i) for i in superseded} - set(policy.not_castable)


def dsl_player_castable_ids(spell_entries: Iterable[dict]) -> set[int]:
    """IDs of DSL entries that look like something a player casts (`registry.looks_player_castable`, via the
    same `SimpleNamespace` shim `lint.check_missing_skill_line_ability` uses)."""
    ids = set()
    for entry in spell_entries:
        shim = SimpleNamespace(
            attributes=entry.get("attributes") or 0,
            cast_time_ms=entry.get("cast_time_ms"),
            cooldown_ms=entry.get("cooldown_ms"),
            category_cooldown_ms=entry.get("category_cooldown_ms"),
            mana_cost=entry.get("mana_cost"),
            mana_cost_pct=entry.get("mana_cost_pct"),
        )
        if registry.looks_player_castable(shim):
            ids.add(int(entry["id"]))
    return ids


@dataclass
class Candidate:
    spell_id: int
    name: str
    source: str  # MELEE or RANGED
    client: Mask
    server: Mask

    @property
    def mask(self) -> Mask:
        return _or(self.client, self.server)


@dataclass
class FamilyPlan:
    family: int
    aura_id: int | None = None
    candidates: list[Candidate] = field(default_factory=list)
    excluded: list[tuple[int, str, str]] = field(default_factory=list)  # (spell_id, name, reason)
    melee: Mask = EMPTY_MASK
    ranged: Mask = EMPTY_MASK
    view_differences: list[str] = field(default_factory=list)

    @property
    def has_bits(self) -> bool:
        return not (is_empty(self.melee) and is_empty(self.ranged))

    def summary(self) -> str:
        aura = self.aura_id
        return (
            f"note: gcd haste: {FAMILY_NAMES.get(self.family, self.family)} (family {self.family}): "
            f"aura {aura if self.has_bits else 'none'}, "
            f"{len(_bits(self.melee))} melee bit(s), {len(_bits(self.ranged))} ranged bit(s), "
            f"{len(self.candidates)} candidate(s) covered, {len(self.excluded)} excluded"
        )


@dataclass
class Result:
    families: dict[int, FamilyPlan] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    # {spell_id: why}: spells the masks were computed WITHOUT, on the assumption that no player can learn them
    # (`NOT_CASTABLE`, and superseded ranks that would otherwise be a candidate or share a mask bit with a
    # hasted spell). `untrainable_errors` turns that assumption into a check against the trainer data.
    assumed_untrainable: dict[int, str] = field(default_factory=dict)

    def with_bits(self) -> list[FamilyPlan]:
        return [self.families[f] for f in sorted(self.families) if self.families[f].has_bits]


def _name(row: dict) -> str:
    return str(row.get("Name_Lang_enUS", "") or "")


def _fmt_mask(mask: Mask) -> str:
    return "(" + ", ".join(f"0x{w:x}" for w in mask) + ")"


def compute(
    spells: dict[int, dict], learnable: set[int], policy: Policy, superseded: Iterable[int] = (),
) -> Result:
    """The per-family plans from the merged spell rows (`ID` -> full Spell.dbc row). `superseded` is the set
    `learnable` already had removed; it is only used to record which of them the result leans on."""
    result = Result(families={f: FamilyPlan(f, policy.aura_ids.get(f)) for f in FAMILY_NAMES})
    by_family: dict[int, list[dict]] = {f: [] for f in FAMILY_NAMES}
    for row in spells.values():
        family = int(row.get("SpellClassSet", 0))
        if family in by_family:
            by_family[family].append(row)

    for family, rows in by_family.items():
        plan = result.families[family]
        rows.sort(key=lambda r: int(r["ID"]))
        for row in rows:
            spell_id = int(row["ID"])
            if not skipped_by_core_haste(row) or spell_id not in learnable:
                continue
            client, server = client_flags(row), server_flags(row, policy)
            if spell_id in policy.exclude:
                plan.excluded.append((spell_id, _name(row), policy.exclude[spell_id]))
                continue
            if is_empty(_or(client, server)):
                result.errors.append(
                    f"{FAMILY_NAMES[family]}: {spell_id} ({_name(row)}) is a candidate but has an all-zero "
                    f"SpellClassMask, so no spell mod can target it; add it to EXCLUDE with a reason"
                )
                continue
            plan.candidates.append(Candidate(spell_id, _name(row), haste_source(row, family), client, server))

    for family, plan in result.families.items():
        _resolve_masks(plan, by_family[family], learnable, policy, result)
    _check_excluded_ids(policy, spells, result)
    _warn_stale_excludes(policy, spells, result)
    _record_assumed_untrainable(result, by_family, spells, policy, {int(i) for i in superseded})
    return result


def _record_assumed_untrainable(
    result: Result, by_family: dict[int, list[dict]], spells: dict[int, dict], policy: Policy, superseded: set[int],
) -> None:
    for spell_id, reason in policy.not_castable.items():
        if spell_id in spells:
            result.assumed_untrainable[spell_id] = f"NOT_CASTABLE ({reason})"
    for family, rows in by_family.items():
        plan = result.families[family]
        masks = _or(plan.melee, plan.ranged)
        for row in rows:
            spell_id = int(row["ID"])
            if spell_id not in superseded or spell_id in result.assumed_untrainable:
                continue
            flags = _or(client_flags(row), server_flags(row, policy))
            if skipped_by_core_haste(row) or (hasted_by_core(row) and not is_empty(_and(masks, flags))):
                result.assumed_untrainable[spell_id] = "superseded rank"


def untrainable_errors(
    assumed: dict[int, str],
    live_trainer_rows: Iterable[tuple[int, int]],
    trainer_reachable: Callable[[int], bool],
    declared_trained: Iterable[int],
) -> list[str]:
    """The ids in `assumed` (`Result.assumed_untrainable`) a player could in fact still learn: on a live
    `trainer_spell` row (`live_trainer_rows`, (TrainerId, SpellId), after removals) of a reachable trainer, or
    named by a `trained_by()` declaration. Either makes the exclusion from the check wrong."""
    errors = []
    declared = {int(i) for i in declared_trained}
    reachable: dict[int, bool] = {}
    for trainer_id, spell_id in sorted(live_trainer_rows):
        if spell_id not in assumed:
            continue
        if trainer_id not in reachable:
            reachable[trainer_id] = bool(trainer_reachable(trainer_id))
        if reachable[trainer_id]:
            errors.append(
                f"spell {spell_id} is treated as untrainable ({assumed[spell_id]}) but trainer {trainer_id} still "
                f"teaches it and that trainer is reachable; untrain it, or drop it from NOT_CASTABLE"
            )
    for spell_id in sorted(declared & set(assumed)):
        errors.append(
            f"spell {spell_id} is treated as untrainable ({assumed[spell_id]}) but a trained_by() declaration "
            f"teaches it; drop the declaration, or drop it from NOT_CASTABLE"
        )
    return errors


def _resolve_masks(plan: FamilyPlan, rows: list[dict], learnable: set[int], policy: Policy, result: Result) -> None:
    for source in (MELEE, RANGED):
        mask = EMPTY_MASK
        for cand in plan.candidates:
            if cand.source == source:
                mask = _or(mask, cand.mask)
        if source == MELEE:
            plan.melee = mask
        else:
            plan.ranged = mask
    name = FAMILY_NAMES[plan.family]
    both = _and(plan.melee, plan.ranged)
    for bit in _bits(both):
        owners = sorted(
            (c.source, c.spell_id, c.name) for c in plan.candidates if not is_empty(_and(c.mask, _bit_mask(bit)))
        )
        result.errors.append(
            f"{name}: bit {bit} is in both the melee and the ranged mask, so those spells would be hasted by "
            f"the wrong source: {owners}"
        )
    # One error per (haste source, bit): the candidates carrying it and the core-hasted spells it would
    # double-dip, under whichever view (client Spell.dbc / server after load-time rewrites) shows the overlap.
    candidate_ids = {c.spell_id for c in plan.candidates}
    conflicts: dict[tuple[str, int], dict] = {}
    for row in rows:
        spell_id = int(row["ID"])
        if spell_id in candidate_ids or spell_id not in learnable or not hasted_by_core(row):
            continue
        for view, flags in (("client", client_flags(row)), ("server", server_flags(row, policy))):
            for source, mask in ((MELEE, plan.melee), (RANGED, plan.ranged)):
                for bit in _bits(_and(mask, flags)):
                    entry = conflicts.setdefault((source, bit), {"hasted": {}, "views": set()})
                    entry["hasted"][spell_id] = _name(row)
                    entry["views"].add(view)
    for (source, bit), entry in sorted(conflicts.items()):
        carriers = sorted(
            (c.spell_id, c.name) for c in plan.candidates
            if c.source == source and not is_empty(_and(c.mask, _bit_mask(bit)))
        )
        result.errors.append(
            f"{name}: {source} bit {bit} ({'+'.join(sorted(entry['views']))} flags) is carried by candidate(s) "
            f"{carriers} and by spell(s) the core already hastes {sorted(entry['hasted'].items())}; EXCLUDE the "
            f"candidate(s) with a reason, or move a spell to a free bit"
        )
    plan.view_differences = [
        f"{c.spell_id} ({c.name}): client {_fmt_mask(c.client)} vs server {_fmt_mask(c.server)}"
        for c in plan.candidates if c.client != c.server
    ]


def _bit_mask(bit: int) -> Mask:
    words = [0, 0, 0]
    words[bit // 32] = 1 << (bit % 32)
    return (words[0], words[1], words[2])


def _check_excluded_ids(policy: Policy, spells: dict[int, dict], result: Result) -> None:
    for label, table in (("EXCLUDE", policy.exclude), ("NOT_CASTABLE", policy.not_castable)):
        for spell_id in sorted(table):
            if spell_id not in spells:
                result.errors.append(f"{label} names spell {spell_id}, which does not exist in the merged spell data")


def _warn_stale_excludes(policy: Policy, spells: dict[int, dict], result: Result) -> None:
    """An EXCLUDE id that exists but is no longer a candidate (a rework changed its DmgClass, GCD or
    learnability) is dead policy."""
    excluded = {sid for plan in result.families.values() for sid, _, _ in plan.excluded}
    for spell_id in sorted(s for s in policy.exclude if s in spells and s not in excluded):
        result.warnings.append(
            f"EXCLUDE[{spell_id}] is no longer a candidate (not a learnable 1.5s GCD spell the core's haste "
            f"skips); remove it from source/gcd_haste.py"
        )


def aura_entries(result: Result, policy: Policy) -> list[dict]:
    """Source-shaped spell entries (the same dicts the DSL produces) for every family with bits, in family
    order. A family with bits but no `FAMILY_AURA_IDS` entry is an error, not skipped."""
    entries = []
    for plan in result.with_bits():
        if plan.aura_id is None:
            raise GcdHasteError(
                f"{FAMILY_NAMES[plan.family]} (family {plan.family}) has GCD-haste bits "
                f"{_fmt_mask(plan.melee)}/{_fmt_mask(plan.ranged)} but no aura ID in source/gcd_haste.py "
                f"FAMILY_AURA_IDS"
            )
        entries.append(aura_entry(plan, policy))
    return entries


def aura_entry(plan: FamilyPlan, policy: Policy) -> dict:
    """The hidden passive for one family. Effect 0 (melee mask, letter A) and effect 1 (ranged mask, letter B)
    are PCT SPELLMOD_GLOBAL_COOLDOWN mods; an effect with an empty mask is left out entirely, because an
    all-zero classmask would match every spell of the family. Effect 2 is the PERIODIC_DUMMY that drives T2's
    recompute. Built through the DSL model so it is exactly the dict a `spell()` declaration would give."""
    raw = {
        "SpellClassSet": plan.family,
        "SpellLevel": 1,
        "BaseLevel": 1,
        "EquippedItemClass": -1,
        "ProcChance": 101,
        "CastingTimeIndex": SPELL_CAST_TIME_INSTANT,
    }
    effects: list[model.Effect | None] = [None, None, None]
    for index, mask in ((0, plan.melee), (1, plan.ranged)):
        if is_empty(mask):
            continue
        effects[index] = _mod_effect(policy)
        for n in range(3):
            raw[mask_column(index, n)] = mask[n]
    effects[2] = model.Effect(
        type=SPELL_EFFECT_APPLY_AURA, apply_aura=SPELL_AURA_PERIODIC_DUMMY, amplitude=policy.tick_ms,
        implicit_target_a=TARGET_UNIT_CASTER,
    )
    melee_note = "" if not is_empty(plan.melee) else " (empty, so no effect)"
    ranged_note = "" if not is_empty(plan.ranged) else " (empty, so no effect)"
    return model.Spell(
        id=plan.aura_id,
        name="Haste: Global Cooldown",
        school=SCHOOL_PHYSICAL,
        attributes=AURA_ATTRIBUTES,
        range_yards=RANGE_SELF,
        effects=effects,
        notes=(
            f"melee-haste-gcd T1 (.agents/plans/melee-haste-gcd/melee-haste-gcd.PLAN.md): "
            f"{FAMILY_NAMES[plan.family]} GCD-haste aura, generated by lib/gcd_haste.py from "
            f"source/gcd_haste.py on every run. Effect 1 = melee-haste PCT SPELLMOD_GLOBAL_COOLDOWN{melee_note}, "
            f"effect 2 = ranged-haste mod{ranged_note}, effect 3 = PERIODIC_DUMMY {policy.tick_ms}ms for T2's "
            f"AuraScript. Amount {policy.placeholder_pct}% is a T1 test value that T2 overrides at runtime "
            f"and resets to 0."
        ),
        raw_overrides=raw,
    ).to_entry()


def mask_column(effect_index: int, dword: int) -> str:
    """`EffectSpellClassMask{A,B,C}_{1,2,3}` for 0-based `effect_index` and `dword`: the LETTER is the
    effect, the NUMBER is the dword (see this module's docstring)."""
    return f"EffectSpellClassMask{'ABC'[effect_index]}_{dword + 1}"


def _mod_effect(policy: Policy) -> model.Effect:
    # DBC EffectBasePoints stores amount - 1 for a 1-sided die, so -33% is -34.
    return model.Effect(
        type=SPELL_EFFECT_APPLY_AURA, apply_aura=SPELL_AURA_ADD_PCT_MODIFIER, misc_value=SPELLMOD_GLOBAL_COOLDOWN,
        base_points=policy.placeholder_pct - 1, implicit_target_a=TARGET_UNIT_CASTER,
    )


def merged_spell_rows(existing: dict[int, dict], built_dsl_rows: Iterable[dict]) -> dict[int, dict]:
    """Base DBC + promoted migrations, with this run's built DSL rows laid over them."""
    merged = dict(existing)
    merged.update({int(r["ID"]): r for r in built_dsl_rows})
    return merged


def report_lines(result: Result) -> list[str]:
    """One summary line per family, plus a line for every candidate whose client and server flags differ."""
    lines = [plan.summary() for plan in result.families.values()]
    for plan in result.families.values():
        for diff in plan.view_differences:
            lines.append(
                f"note: gcd haste: {FAMILY_NAMES[plan.family]}: client and server SpellFamilyFlags differ for "
                f"{diff}; the aura mask covers both"
            )
    return lines
