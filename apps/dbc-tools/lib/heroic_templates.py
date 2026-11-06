"""
The heroic creature template generator (dungeon difficulties E2, WP-G): for every declared heroic, one level 60
`creature_template` row per creature of the dungeon's heroic entry set, the normal -> heroic map T2's emitters read
(`entry["heroic_entries"]`), and the dungeon's creature lints. `build()` runs inside `dungeon_heroic.expand()` (so
`--check` and the full run see the same rows), before T2's `difficulty_entry_1` edits and side-table copies.

**Entry set** (`entry_set()`): the declaration's creatures (the generated `CREATURES` block plus `extra=`, roles after
`roles=`) together with every creature live spawns on the map outside game events (unless the heroic takes event
spawns) and every encounter kill credit of the map, minus `skip=`, critters (type 8 or role critter), triggers
(`flags_extra` 0x80 or role trigger), friendly NPCs (role npc: a heroic copy must keep `npcflag`, and they need none)
and event-only creatures. A live spawned entry missing from the declaration is still included, with a WARNING to
rerun extract_dungeon_creatures.py.

**Ids**: `source/world/heroic_ids.lock`, append-only, one `normal heroic map name` line per creature, from
`source/ids.yaml`'s `creature_heroic` block (310000-311999). A new creature takes the next id after the highest one
the file holds (gaps are never reused); a full generate.py run appends its lines, `--check` only reports them. An id
never moves, and a dropped creature keeps its line (its heroic row is never deleted: creature_template is never
pruned).

**Retiring**: a creature with a lock line for a declared heroic's map that is no longer in any heroic entry set (a
later `skip=`, a role change to npc / critter / trigger, `event=True`, gone from the map) stops generate.py with an
ERROR, also under `--check`: its normal row would keep `difficulty_entry_1` on a heroic row whose side rows (spells,
auras, resistances, models) the next run prunes. Put it back, or list it in `dungeon(retired=...)`: the run then emits
a guarded `UPDATE creature_template SET difficulty_entry_1 = 0 WHERE entry = N AND difficulty_entry_1 = H` (while the
replayed normal row still points at H) and no longer copies its side rows. Its lock line stays.

**Row**: every column of the live normal row (the replayed base dump, migrations and frozen phase 0), then the tier's
level (`minlevel` = `maxlevel`), `exp` 0, `HealthModifier` and `DamageModifier` solved for the tier row of the role or
rank (boss role: boss; rank 0 normal, 1 elite, 2 and 4 rare, 3 boss) or the creature's override, `flags_extra` |
INSTANCE_BIND (0x1) on bosses (a kill binds the group only through the current template's flag, Unit::Kill),
`AIName` / `ScriptName` empty (ObjectMgr::CheckCreatureTemplate drops the link otherwise; the normal entry's scripts
run on heroic), `difficulty_entry_*` 0; `KillCredit1/2`, `lootid` (heroic drops the normal loot until E5), `npcflag`,
`unit_class`, faction and the rest copied. `ArmorModifier` and `ManaModifier` are kept, so armor and mana are the
level 60 base values times the normal modifiers. Override `columns` apply last.

Health and damage follow the engine (all creature rates are 1 live):
- health = ceil(basehp0(60, class) x HealthModifier) (`CreatureBaseStats::GenerateHealth`, `Creature::SelectLevel`);
- a melee hit = (weapon + AP / 14 x BaseVariance) x DamageModifier x BaseAttackTime / 1000, weapon from damage_base
  (min) to 1.5 x damage_base (max) (`Creature::SelectLevel`, `Creature::CalculateMinMaxDamage`). The tier's melee is the
  average hit at a 2.0 sec swing and scales with the template's own swing, so the modifier is
  melee / (2 x (1.25 x damage_base + AP / 14 x BaseVariance)) for every swing time (equal damage per second).
"""

from __future__ import annotations

import math
import re
import struct
from dataclasses import dataclass, field
from pathlib import Path

from . import dungeon_extract
from .dsl import dungeon as dungeon_dsl

TOOL_ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = TOOL_ROOT / "source" / "world" / "heroic_ids.lock"
LOCK_BLOCK = "creature_heroic"
LOCK_HEADER = (
    "# Heroic creature template ids (dungeon difficulties E2, WP-G; lib/heroic_templates.py): one line per\n"
    "# creature, `<normal entry> <heroic entry> <map> <name>`, from source/ids.yaml's creature_heroic block.\n"
    "# Append-only: a full generate.py run appends the new creatures of a declared heroic; never edit, reorder or\n"
    "# delete a line (an id must never move or be reused: the heroic creature_template row stays in the database).\n"
)

INSTANCE_BIND = 0x1  # CREATURE_FLAG_EXTRA_INSTANCE_BIND
TRIGGER = 0x80  # CREATURE_FLAG_EXTRA_TRIGGER
CRITTER = 8  # CREATURE_TYPE_CRITTER
SWING_REFERENCE = 2.0  # sec: the tier table's melee is per hit at this swing
AVERAGE_WEAPON = 1.25  # (damage_base + 1.5 x damage_base) / 2
AP_PER_DPS = 14.0
SKIP_ROLES = ("npc", "critter", "trigger")
DIFFICULTY_ENTRY_COLUMNS = ("difficulty_entry_1", "difficulty_entry_2", "difficulty_entry_3")


@dataclass(frozen=True)
class Tier:
    level: int
    rows: dict  # row name -> (health, melee per hit at a 2.0 sec swing)


# Handoff s3.5 / s7 #4 starting values, to tune in the Pilot. Rows: dungeon_dsl.TIER_ROWS.
TIERS = {
    "vanilla": Tier(level=60, rows={
        "normal": (12_000, 200), "elite": (37_000, 550), "rare": (74_000, 900), "boss": (300_000, 2_500),
    }),
}
RANK_ROWS = {0: "normal", 1: "elite", 2: "rare", 3: "boss", 4: "rare"}


def _int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0


def _float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def f32(value: float) -> float:
    """`value` stored in a MySQL FLOAT / a C++ float."""
    return struct.unpack("<f", struct.pack("<f", value))[0]


# ---------------------------------------------------------------------------------------------------------------------
# Stats


@dataclass
class Solved:
    columns: dict  # creature_template columns the solve sets
    health: int
    min_damage: float
    max_damage: float
    armor: int
    mana: int
    tier_row: str
    swing_ms: int


def melee_factor(stats: dict, row: dict) -> float:
    """Average hit per second of swing at DamageModifier 1: 1.25 x damage_base + AP / 14 x BaseVariance."""
    return AVERAGE_WEAPON * _float(stats["damage_base"]) + _float(stats["attackpower"]) / AP_PER_DPS * _float(
        row.get("BaseVariance"), 1.0)


def health_modifier(base_hp: int, health: float) -> float:
    """The 4-decimal HealthModifier whose engine health (ceil(base x float(mod))) is nearest `health`, the lower one on
    a tie (ceil rounds up, so the plain rounded quotient often lands one point high)."""
    center = round(health / base_hp, 4)
    candidates = [round(center + step / 10_000, 4) for step in (-1, 0, 1)]
    return min(candidates, key=lambda mod: (abs(math.ceil(base_hp * f32(mod)) - health), mod))


def solve(row: dict, stats: dict, health: float, melee: float, tier_row: str) -> Solved:
    """The modifiers that give `row` (already at the heroic level, `exp` 0) `health` and an average `melee` hit at a
    2.0 sec swing, against the class's level stats row `stats` (creature_classlevelstats)."""
    base_hp = _int(stats["basehp0"])
    health_mod = health_modifier(base_hp, health)
    factor = melee_factor(stats, row)
    damage_mod = round(melee / (SWING_REFERENCE * factor), 4)
    swing_ms = _int(row.get("BaseAttackTime")) or 2000
    swing = swing_ms / 1000.0
    flat = _float(stats["attackpower"]) / AP_PER_DPS * _float(row.get("BaseVariance"), 1.0)
    weapon = _float(stats["damage_base"])
    mod = f32(damage_mod)
    return Solved(
        columns={"HealthModifier": health_mod, "DamageModifier": damage_mod},
        health=math.ceil(base_hp * f32(health_mod)),
        min_damage=(weapon + flat) * mod * swing, max_damage=(1.5 * weapon + flat) * mod * swing,
        armor=math.ceil(_float(stats["basearmor"]) * f32(_float(row.get("ArmorModifier"), 1.0))),
        mana=math.ceil(_int(stats["basemana"]) * f32(_float(row.get("ManaModifier"), 1.0))) if _int(
            stats["basemana"]) else 0,
        tier_row=tier_row, swing_ms=swing_ms,
    )


def tier_rows(spec: dict) -> tuple[Tier | None, dict]:
    tier = TIERS.get(spec.get("tier") or "vanilla")
    if tier is None:
        return None, {}
    rows = dict(tier.rows)
    for row, health, melee in spec.get("tier_values") or ():
        rows[row] = (health, melee)
    return tier, rows


# ---------------------------------------------------------------------------------------------------------------------
# The lock file


class LockError(ValueError):
    pass


@dataclass
class Lock:
    pairs: dict[int, int] = field(default_factory=dict)  # normal -> heroic
    text: str = ""
    maps: dict[int, int] = field(default_factory=dict)  # normal -> the map of its line


_LOCK_LINE = re.compile(r"^(\d+) (\d+) (\d+) (.*)$")


def parse_lock(text: str, block: dict | None = None) -> Lock:
    """Reads the lock file; raises LockError on a malformed line, a repeated normal or heroic entry, or an id outside
    `block` (`{start, end}`)."""
    lock = Lock(text=text)
    heroic_seen: dict[int, int] = {}
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        m = _LOCK_LINE.match(line)
        if not m:
            raise LockError(f"heroic_ids.lock line {number}: expected `<normal> <heroic> <map> <name>`, got {line!r}")
        normal, heroic_entry = int(m.group(1)), int(m.group(2))
        if normal in lock.pairs:
            raise LockError(f"heroic_ids.lock line {number}: creature {normal} is listed twice")
        if heroic_entry in heroic_seen:
            raise LockError(f"heroic_ids.lock line {number}: heroic entry {heroic_entry} is already creature "
                            f"{heroic_seen[heroic_entry]}'s")
        if block and not block["start"] <= heroic_entry <= block["end"]:
            raise LockError(f"heroic_ids.lock line {number}: {heroic_entry} is outside source/ids.yaml's "
                            f"{LOCK_BLOCK} block ({block['start']}-{block['end']})")
        lock.pairs[normal] = heroic_entry
        lock.maps[normal] = int(m.group(3))
        heroic_seen[heroic_entry] = normal
    return lock


def assign_ids(lock: Lock, wanted: list[tuple[int, int, str]], block: dict) -> tuple[dict[int, int], list[str]]:
    """Heroic ids for `wanted` ((normal, map, name), in order): the lock's id, else the next id after the highest the
    lock holds. Returns the full map and the new lines to append. Raises LockError when the block runs out."""
    pairs = dict(lock.pairs)
    next_id = max([block["start"] - 1, *pairs.values()]) + 1
    appended = []
    for normal, map_id, name in wanted:
        if normal in pairs:
            continue
        if next_id > block["end"]:
            raise LockError(f"source/ids.yaml's {LOCK_BLOCK} block ({block['start']}-{block['end']}) is full")
        pairs[normal] = next_id
        appended.append(f"{normal} {next_id} {map_id} {' '.join(str(name).split())}")
        next_id += 1
    return pairs, appended


def lock_text(lock: Lock, appended: list[str]) -> str:
    """The lock file with `appended` added at the end (the header on a new file); existing lines byte for byte."""
    text = lock.text or LOCK_HEADER
    if appended:
        if not text.endswith("\n"):
            text += "\n"
        text += "".join(f"{line}\n" for line in appended)
    return text


# ---------------------------------------------------------------------------------------------------------------------
# The entry set


@dataclass
class EntrySet:
    included: dict[int, str] = field(default_factory=dict)  # entry -> role
    skipped: dict[int, str] = field(default_factory=dict)  # entry -> why
    undeclared: list[int] = field(default_factory=list)  # live spawned / credit entries the declaration lacks


def entry_set(
    dungeon_entry: dict, spawned: set[int], credits: set[int], templates: dict[int, dict], event_spawns: bool = False,
) -> EntrySet:
    """declared creatures (after roles=) | live non-event spawned entries | encounter credits, minus skip=, critters,
    triggers, friendly NPCs and event-only creatures (`entry_set` in this module's docstring)."""
    out = EntrySet()
    declared = {int(c["entry"]): c for c in dungeon_entry.get("creatures") or ()}
    skip = set(dungeon_entry.get("skip") or ())
    retired = set(dungeon_entry.get("retired") or ())
    candidates = sorted(set(declared) | set(spawned) | set(credits))
    for entry in candidates:
        template = templates.get(entry)
        listed = declared.get(entry)
        if listed is None:
            out.undeclared.append(entry)
            role = "boss" if entry in credits else _auto_role(template)
        else:
            role = listed["role"]
        if entry in retired:
            out.skipped[entry] = "retired="
        elif entry in skip:
            out.skipped[entry] = "skip="
        elif template is None:
            out.skipped[entry] = "no live creature_template row"
        elif role in SKIP_ROLES:
            out.skipped[entry] = role
        elif _int(template.get("type")) == CRITTER:
            out.skipped[entry] = "critter (type 8)"
        elif _int(template.get("flags_extra")) & TRIGGER:
            out.skipped[entry] = "trigger (flags_extra 0x80)"
        elif listed is not None and listed.get("event") and not event_spawns and entry not in spawned:
            out.skipped[entry] = "event only"
        else:
            out.included[entry] = role
    return out


def _auto_role(template: dict | None) -> str:
    return dungeon_extract.auto_role(template, False)


# ---------------------------------------------------------------------------------------------------------------------
# The heroic row


def heroic_row(
    normal: dict, heroic_entry: int, columns: tuple[str, ...], defaults: dict, level: int, solved: Solved,
    boss: bool, override_columns: dict | None = None,
) -> dict:
    row = {c: normal[c] if c in normal else defaults.get(c) for c in columns}
    row.update(entry=heroic_entry, minlevel=level, maxlevel=level, exp=0, AIName="", ScriptName="")
    for column in DIFFICULTY_ENTRY_COLUMNS:
        row[column] = 0
    row.update(solved.columns)
    if boss:
        row["flags_extra"] = _int(row.get("flags_extra")) | INSTANCE_BIND
    row.update(override_columns or {})
    row["id"] = heroic_entry
    return row


def refusal_errors(label: str, normal: dict, heroic: dict) -> tuple[list[str], list[str]]:
    """ERRORs for a heroic row `ObjectMgr::CheckCreatureTemplate` would refuse to link (it then ignores
    difficulty_entry_1); WARNINGs for differences it only logs."""
    errors, warnings = [], []
    for column in ("unit_class", "npcflag"):
        if _int(normal.get(column)) != _int(heroic.get(column)):
            errors.append(f"{label}: {column} {heroic.get(column)} differs from the normal row's "
                          f"{normal.get(column)} - the engine drops the difficulty link")
    for column in ("AIName", "ScriptName"):
        if heroic.get(column):
            errors.append(f"{label}: {column} {heroic.get(column)!r} is set - the engine drops the difficulty link "
                          f"(the normal entry's script runs on heroic anyway)")
    if any(_int(heroic.get(c)) for c in DIFFICULTY_ENTRY_COLUMNS):
        errors.append(f"{label}: the heroic row has difficulty entries of its own")
    if _int(normal.get("exp")) > _int(heroic.get("exp")):
        warnings.append(f"{label}: the normal row's exp {normal.get('exp')} is above the heroic row's "
                        f"{heroic.get('exp')} - ObjectMgr::CheckCreatureTemplate logs it at every boot")
    for column in ("faction", "family", "type", "dmgschool"):
        if str(normal.get(column)) != str(heroic.get(column)) and _int(normal.get(column)) != _int(heroic.get(column)):
            warnings.append(f"{label}: {column} differs from the normal row's (the engine logs it at every boot)")
    return errors, warnings


# ---------------------------------------------------------------------------------------------------------------------
# SmartAI and SpellDifficulty lints

SMART_DIFFICULTY_NORMAL = 0x02  # SMART_EVENT_FLAG_DIFFICULTY_0
SMART_DIFFICULTY_HEROIC = 0x04  # SMART_EVENT_FLAG_DIFFICULTY_1: spawnMode 1 (a 5-man heroic) -> 1 << (1 + 1)
SMART_DIFFICULTY_ALL = 0x1E
CAST_ACTIONS = (11, 75, 85, 86, 134)  # SMART_ACTION_CAST, ADD_AURA, SELF_CAST, CROSS_CAST, INVOKER_CAST


def smart_keys(entries: set[int], creature_guids: set[int], gameobject_ids: set[int],
               gameobject_guids: set[int]) -> set[tuple[int, int]]:
    """The (entryorguid, source_type) scripts that run in the dungeon: its creatures' entries and spawn guids
    (source_type 0) and its gameobjects' entries and spawn guids (1)."""
    return ({(e, 0) for e in entries} | {(-g, 0) for g in creature_guids}
            | {(e, 1) for e in gameobject_ids} | {(-g, 1) for g in gameobject_guids})


def normal_only_rows(rows: list[dict], keys: set[tuple[int, int]]) -> tuple[list[dict], list[tuple[int, int]]]:
    """SmartAI rows of `keys` that run on normal only (`event_flags` has the normal bit and no heroic bit) and can be
    widened, and the scripts left alone because another of their rows already names the heroic bit (a script with
    its own per-difficulty rows)."""
    by_key: dict[tuple[int, int], list[dict]] = {}
    for row in rows:
        key = (_int(row.get("entryorguid")), _int(row.get("source_type")))
        if key in keys:
            by_key.setdefault(key, []).append(row)
    widen, left = [], []
    for key in sorted(by_key):
        script = by_key[key]
        masked = [r for r in script if _int(r.get("event_flags")) & SMART_DIFFICULTY_ALL
                  and _int(r.get("event_flags")) & SMART_DIFFICULTY_NORMAL
                  and not _int(r.get("event_flags")) & SMART_DIFFICULTY_HEROIC]
        if not masked:
            continue
        if any(_int(r.get("event_flags")) & SMART_DIFFICULTY_HEROIC for r in script):
            left.append(key)
        else:
            widen += sorted(masked, key=lambda r: (_int(r.get("id")), _int(r.get("link"))))
    return widen, left


def render_smart_widen(label: str, rows: list[dict]) -> str:
    """One `UPDATE smart_scripts SET event_flags = event_flags | 4` per script, each row pinned by its full key and
    its current flags (so a rerun or a later change of the row never double-applies), behind a comment line."""
    if not rows:
        return ""
    by_key: dict[tuple[int, int], list[dict]] = {}
    for row in rows:
        by_key.setdefault((_int(row["entryorguid"]), _int(row["source_type"])), []).append(row)
    parts = [f"-- {label}: {len(rows)} normal-only SmartAI row(s) also run on heroic (event_flags | "
             f"{SMART_DIFFICULTY_HEROIC}, SMART_EVENT_FLAG_DIFFICULTY_1)"]
    for (entryorguid, source_type), script in sorted(by_key.items()):
        conditions = [
            f"(`entryorguid` = {entryorguid} AND `source_type` = {source_type} AND `id` = {_int(r['id'])} AND "
            f"`link` = {_int(r['link'])} AND `event_flags` = {_int(r['event_flags'])})"
            for r in script
        ]
        parts.append(f"UPDATE `smart_scripts` SET `event_flags` = `event_flags` | {SMART_DIFFICULTY_HEROIC} WHERE\n"
                     + " OR\n".join(f"    {c}" for c in conditions) + ";")
    return "\n".join(parts)


def spell_difficulty_index(rows: dict[int, dict]) -> dict[int, int]:
    """spell -> the SpellDifficulty row id the engine's searcher files it under (DBCStores.cpp: rows with slots 1 and
    2 set, every non-zero slot, later ids win)."""
    out = {}
    for row_id in sorted(rows):
        row = rows[row_id]
        slots = [_int(row.get(f"DifficultySpellID_{i}")) for i in range(1, 5)]
        if slots[0] <= 0 or slots[1] <= 0:
            continue
        for spell in slots:
            if spell > 0:
                out[spell] = row_id
    return out


def heroic_swaps(spells: set[int], rows: dict[int, dict]) -> dict[int, int]:
    """spell -> the spell it becomes in a 5-man heroic (`SpellMgr::GetSpellIdForDifficulty` mode 1), for the spells
    that change."""
    index = spell_difficulty_index(rows)
    out = {}
    for spell in sorted(spells):
        row = rows.get(index.get(spell, 0))
        if row is None:
            continue
        heroic_spell = _int(row.get("DifficultySpellID_2"))
        if heroic_spell > 0 and heroic_spell != spell:
            out[spell] = heroic_spell
    return out


# ---------------------------------------------------------------------------------------------------------------------
# The entry point


@dataclass
class HeroicReport:
    """One generated heroic row, for the summary and the dry run."""

    map_id: int
    normal: int
    heroic: int
    name: str
    role: str
    rank: int
    unit_class: int
    solved: Solved
    override: bool


@dataclass
class BuildResult:
    rows: list[dict] = field(default_factory=list)
    reports: list[HeroicReport] = field(default_factory=list)
    lock_appended: list[str] = field(default_factory=list)
    smart_blocks: list[str] = field(default_factory=list)
    retire_blocks: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def build(
    heroics: list[dict], live, lock: Lock, block: dict | None, columns: tuple[str, ...], defaults: dict,
    derived_mark: str,
) -> BuildResult:
    """Heroic rows, `heroic_entries` (set on each heroic dungeon entry), lock lines and lints for `heroics` (the
    declared `Registry.dungeons` entries with a heroic) over `live` (a dungeon_heroic.LiveWorld)."""
    out = BuildResult()
    if block is None:
        out.errors.append(f"dungeons: source/ids.yaml has no {LOCK_BLOCK} block - the heroic creature ids come from it")
        return out
    spawns_by_map: dict[int, dict[str, list[dict]]] = {}
    for table in ("creature", "gameobject"):
        events = live.event_guids.get(table, set())
        for row in live.spawns.get(table, {}).values():
            spawns_by_map.setdefault(_int(row.get("map")), {}).setdefault(table, []).append(
                {**row, "_event": _int(row.get("guid")) in events})
    wanted: list[tuple[int, int, str]] = []
    plans = []
    owner: dict[int, int] = {}
    for entry in heroics:
        map_id, name, spec = entry["map_id"], entry["name"], entry["heroic"]
        label = f"dungeon({map_id}, {name!r}) heroic"
        tier, rows = tier_rows(spec)
        if tier is None:
            out.errors.append(f"{label}: unknown tier {spec.get('tier')!r} - one of {sorted(TIERS)}")
            continue
        spawns = spawns_by_map.get(map_id, {})
        event_spawns = bool(spec.get("event_spawns"))
        spawned = {_entry_of(r) for r in spawns.get("creature", []) if event_spawns or not r["_event"]}
        credits = _credits(live, map_id)
        chosen = entry_set(entry, spawned, credits, live.creature_templates, event_spawns)
        if chosen.undeclared:
            names = ", ".join(f"{e} {live.creature_templates.get(e, {}).get('name', '?')}" for e in chosen.undeclared)
            out.warnings.append(f"{label}: live creature(s) on the map missing from the declaration: {names} - rerun "
                                f"extract_dungeon_creatures.py")
        overrides = dungeon_dsl.override_dict(spec)
        for e in sorted(set(overrides) - set(chosen.included)):
            why = chosen.skipped.get(e, "not a creature of the dungeon")
            out.errors.append(f"{label}: overrides[{e}] names a creature without a heroic template ({why})")
        if chosen.skipped:
            counts: dict[str, int] = {}
            for why in chosen.skipped.values():
                counts[why] = counts.get(why, 0) + 1
            out.notes.append(f"dungeons: {name} (map {map_id}) heroic: no heroic template for "
                             + ", ".join(f"{n} {why}" for why, n in sorted(counts.items())))
        for e in sorted(chosen.included):
            if e in owner:
                if owner[e] != map_id:
                    out.notes.append(f"dungeons: creature {e} is in the heroic of maps {owner[e]} and {map_id}; one "
                                     f"heroic row, built from map {owner[e]}'s declaration")
                continue
            owner[e] = map_id
            wanted.append((e, map_id, live.creature_templates[e].get("name", "")))
        plans.append((entry, label, tier, rows, chosen, overrides, credits, spawns))
    try:
        pairs, out.lock_appended = assign_ids(lock, wanted, block)
    except LockError as error:
        out.errors.append(f"dungeons: {error}")
        return out
    for entry, label, tier, rows, chosen, overrides, credits, spawns in plans:
        map_id, name = entry["map_id"], entry["name"]
        mapping = {}
        for normal_entry, role in sorted(chosen.included.items()):
            heroic_entry = pairs[normal_entry]
            mapping[normal_entry] = heroic_entry
            if owner.get(normal_entry) != map_id:
                continue
            normal = live.creature_templates[normal_entry]
            stats = live.class_level_stats.get((tier.level, _int(normal.get("unit_class"))))
            what = f"{label} creature {normal_entry} -> {heroic_entry}"
            if stats is None:
                out.errors.append(f"{what}: no creature_classlevelstats row for level {tier.level} class "
                                  f"{normal.get('unit_class')}")
                continue
            override = overrides.get(normal_entry, {})
            row_name = override.get("tier") or ("boss" if role == "boss" else RANK_ROWS.get(_int(normal.get("rank")),
                                                                                           "elite"))
            health, melee = rows[row_name]
            health, melee = override.get("health", health), override.get("melee", melee)
            at_level = {**normal, "minlevel": tier.level, "maxlevel": tier.level, "exp": 0}
            solved = solve(at_level, stats, health, melee, row_name)
            row = heroic_row(normal, heroic_entry, columns, defaults, tier.level, solved, role == "boss",
                             override.get("columns"))
            unknown = sorted(set(override.get("columns", {})) - set(columns))
            if unknown:
                out.errors.append(f"{what}: overrides columns {unknown} are not creature_template columns")
            row[derived_mark] = True
            errors, warnings = refusal_errors(what, normal, row)
            out.errors += errors
            out.warnings += warnings
            out.rows.append(row)
            out.reports.append(HeroicReport(
                map_id=map_id, normal=normal_entry, heroic=heroic_entry, name=str(normal.get("name", "")), role=role,
                rank=_int(normal.get("rank")), unit_class=_int(normal.get("unit_class")), solved=solved,
                override=bool(override),
            ))
        entry["heroic_entries"] = mapping
        bosses = sorted(e for e, r in chosen.included.items() if r == "boss" and e not in credits)
        if bosses:
            out.notes.append(f"dungeons: {name} (map {map_id}) heroic: boss role without an encounter row: "
                             + ", ".join(f"{e} {live.creature_templates[e].get('name')}" for e in bosses)
                             + " (INSTANCE_BIND set; a kill sets no encounter bit)")
        _script_lints(entry, label, chosen, spawns, live, out)
        out.notes.append(f"dungeons: {name} (map {map_id}) heroic: {len(mapping)} heroic creature template(s)")
    _retired(plans, lock, set(owner), live, out)
    return out


def render_retire_revert(label: str, pairs: list[tuple[int, int]]) -> str:
    """One guarded `UPDATE creature_template SET difficulty_entry_1 = 0` per retired (normal, heroic) pair: it only
    clears the link while it still names that heroic row."""
    if not pairs:
        return ""
    lines = [f"-- {label}: {len(pairs)} retired heroic creature(s) lose their difficulty link (dungeon(retired=...))"]
    lines += [f"UPDATE `creature_template` SET `difficulty_entry_1` = 0 WHERE `entry` = {normal} AND "
              f"`difficulty_entry_1` = {heroic_entry};" for normal, heroic_entry in pairs]
    return "\n".join(lines)


def _retired(plans: list, lock: Lock, mapped: set[int], live, out: BuildResult) -> None:
    """The lock lines of each declared heroic's map whose creature left every heroic entry set: an ERROR unless the
    declaration retires it (then a guarded revert of its normal row's difficulty_entry_1)."""
    for entry, label, _tier, _rows, chosen, _overrides, _credits, _spawns in plans:
        map_id, name = entry["map_id"], entry["name"]
        retired = set(entry.get("retired") or ())
        shipped = {n: h for n, h in lock.pairs.items() if lock.maps.get(n) == map_id}
        for normal in sorted(retired):
            if normal not in shipped:
                out.errors.append(f"{label}: retired= names creature {normal}, which has no {LOCK_PATH.name} line for "
                                  f"map {map_id} - it never shipped a heroic template; use skip= instead")
            elif normal in mapped:
                out.errors.append(f"{label}: retired= names creature {normal}, which another declared heroic still "
                                  f"maps to {shipped[normal]} - drop it from retired=")
        reverts = []
        for normal, heroic_entry in sorted(shipped.items()):
            if normal in mapped:
                continue
            template = live.creature_templates.get(normal) or {}
            if normal in retired:
                if _int(template.get("difficulty_entry_1")) == heroic_entry:
                    reverts.append((normal, heroic_entry))
                continue
            why = chosen.skipped.get(normal) or "no longer declared, spawned on the map or an encounter kill credit"
            out.errors.append(
                f"{label}: creature {normal} {template.get('name', '?')} shipped heroic entry {heroic_entry} "
                f"({LOCK_PATH.name}) but left the heroic entry set ({why}) - its normal row would keep "
                f"difficulty_entry_1 = {heroic_entry} while the run prunes that heroic row's spells, auras, "
                f"resistances and models. Put it back in the set, or declare dungeon(..., retired=({normal},)) to "
                f"revert difficulty_entry_1 and stop copying its side rows (its lock line stays)"
            )
        if reverts:
            out.retire_blocks.append(render_retire_revert(f"{name} (map {map_id}) heroic", reverts))
            out.notes.append(f"dungeons: {name} (map {map_id}) heroic: reverting difficulty_entry_1 of retired "
                             f"creature(s) " + ", ".join(str(n) for n, _ in reverts))


def _entry_of(row: dict) -> int:
    return _int(row.get("id", row.get("id1")))


def _credits(live, map_id: int) -> set[int]:
    merged = dict(live.stock_encounters or {})
    for row in live.live_encounters:
        merged[_int(row.get("ID"))] = row
    out = set()
    for encounter_id, row in merged.items():
        if _int(row.get("MapID")) != map_id or _int(row.get("Difficulty")) != 0:
            continue
        credit = live.instance_encounters.get(encounter_id)
        if credit and _int(credit.get("creditType")) == 0 and _int(credit.get("creditEntry")):
            out.add(_int(credit.get("creditEntry")))
    return out


def _script_lints(entry: dict, label: str, chosen: EntrySet, spawns: dict, live, out: BuildResult) -> None:
    map_id, name, spec = entry["map_id"], entry["name"], entry["heroic"]
    creatures = spawns.get("creature", [])
    gameobjects = spawns.get("gameobject", [])
    # Every creature of the dungeon, not only those with a heroic template: a script runs for the normal entry on
    # heroic too (a trigger's or an NPC's included), and its spells are swapped there whatever the caster's template.
    everyone = set(chosen.included) | set(chosen.skipped)
    keys = smart_keys(
        everyone, {_int(r.get("guid")) for r in creatures},
        {_entry_of(r) for r in gameobjects}, {_int(r.get("guid")) for r in gameobjects},
    )
    widen, left = normal_only_rows(live.smart_scripts, keys)
    if widen:
        scripts = sorted({(_int(r["entryorguid"]), _int(r["source_type"])) for r in widen})
        if spec.get("widen_smart_scripts", True):
            out.smart_blocks.append(render_smart_widen(f"{name} (map {map_id}) heroic", widen))
            out.notes.append(f"dungeons: {name} (map {map_id}) heroic: widening {len(widen)} normal-only SmartAI "
                             f"row(s) of {len(scripts)} script(s) to heroic")
        else:
            out.warnings.append(f"{label}: {len(widen)} normal-only SmartAI row(s) (event_flags 0x02) of scripts "
                                f"{scripts} never run on heroic (widen_smart_scripts=False)")
    if left:
        out.notes.append(f"dungeons: {name} (map {map_id}) heroic: normal-only SmartAI rows left alone in scripts "
                         f"with their own heroic rows: {left}")
    if live.spell_difficulty is None:
        out.notes.append(f"dungeons: {name} (map {map_id}) heroic: SpellDifficulty.dbc missing from "
                         f"var/extractors/dbc/ - the spell swap check was skipped")
        return
    spells: set[int] = set()
    for row in live.side_rows.get("creature_template_spell", []):
        if _int(row.get("CreatureID")) in everyone:
            spells.add(_int(row.get("Spell")))
    for row in live.smart_scripts:
        key = (_int(row.get("entryorguid")), _int(row.get("source_type")))
        if key in keys and _int(row.get("action_type")) in CAST_ACTIONS and _int(row.get("action_param1")):
            spells.add(_int(row.get("action_param1")))
    swaps = heroic_swaps(spells, live.spell_difficulty)
    if swaps:
        out.notes.append(f"dungeons: {name} (map {map_id}) heroic: {len(swaps)} creature spell(s) swap to another "
                         f"spell on heroic (SpellDifficulty; mod-dungeon-difficulties rescales them): "
                         + ", ".join(f"{s} -> {h}" for s, h in swaps.items()))
