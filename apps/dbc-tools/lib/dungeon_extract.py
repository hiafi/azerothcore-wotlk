"""
The vanilla dungeon creature extraction (dungeon difficulties E2, WP-G): which creatures a dungeon holds, spawned and
summoned, as the `CREATURES` block of its `source/world/dungeons/<name>.py` reference declaration. The CLI is
`extract_dungeon_creatures.py` (it reads the live world DB read-only through a mysql client command); everything here
is pure, so the tests run it on fixtures.

A dungeon's creatures are, per map:

- every entry spawned on the map (`creature.id`, plus the alternate entries of `creature_multispawn`); an entry whose
  every spawn there belongs to a game event is marked `event=True` (holiday bosses, Scourge Invasion);
- every kill credit entry of the map's encounters (`instance_encounters` creditType 0 of a DungeonEncounter row on the
  map): the bosses;
- everything those creatures and the map's gameobjects summon, to a fixed point: SmartAI `SUMMON_CREATURE` (12) and
  `SUMMON_RADIAL` (228), `SUMMON_CREATURE_GROUP` (107) and every `creature_summon_groups` row of the summoner (C++
  scripts summon groups too) or of the map, `UPDATE_TEMPLATE` (36) targets (`Creature::UpdateEntry` swaps to the
  difficulty entry as well), and the creatures a cast spell summons (effects 28 SUMMON and 56 SUMMON_PET, following
  trigger spells and periodic / proc trigger auras) - spells from SmartAI casts (11, 75, 85, 86, 134) and
  `creature_template_spell`. Guid-keyed scripts (negative `entryorguid`) of the map's spawns and the timed action
  lists (source_type 9) a script calls (80, 87, 88) count for their owner.

C++ summons are invisible here; the declaration's hand-written `extra=` names them.

Roles: `boss` (an encounter's kill credit), `critter` (type 8), `trigger` (`flags_extra` 0x80, or a "[DND]" style
developer helper name), `npc` (any `npcflag`:
quest givers, vendors, gossip; a heroic copy must keep `npcflag` or the engine drops the link, and a friendly NPC
needs no level 60 copy), `trash` for the rest. The declaration's `roles=` corrects any of them by hand.
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass, field

# map id -> (name, file stem under source/world/dungeons/). The 19 vanilla 5-man (and 10-man UBRS) dungeon maps.
VANILLA_DUNGEONS: dict[int, tuple[str, str]] = {
    33: ("Shadowfang Keep", "shadowfang_keep"),
    34: ("Stormwind Stockade", "stormwind_stockade"),
    36: ("Deadmines", "deadmines"),
    43: ("Wailing Caverns", "wailing_caverns"),
    47: ("Razorfen Kraul", "razorfen_kraul"),
    48: ("Blackfathom Deeps", "blackfathom_deeps"),
    70: ("Uldaman", "uldaman"),
    90: ("Gnomeregan", "gnomeregan"),
    109: ("Sunken Temple", "sunken_temple"),
    129: ("Razorfen Downs", "razorfen_downs"),
    189: ("Scarlet Monastery", "scarlet_monastery"),
    209: ("Zul'Farrak", "zul_farrak"),
    229: ("Blackrock Spire", "blackrock_spire"),
    230: ("Blackrock Depths", "blackrock_depths"),
    289: ("Scholomance", "scholomance"),
    329: ("Stratholme", "stratholme"),
    349: ("Maraudon", "maraudon"),
    389: ("Ragefire Chasm", "ragefire_chasm"),
    429: ("Dire Maul", "dire_maul"),
}

ROLES = ("boss", "trash", "npc", "critter", "trigger")
CREATURE_TYPE_CRITTER = 8  # SharedDefines.h CREATURE_TYPE_CRITTER
CREATURE_FLAG_EXTRA_TRIGGER = 0x80  # CreatureData.h
DEVELOPER_PREFIXES = ("[DND]", "[DNT]", "[PH]")  # Blizzard's "do not display" helpers (bunnies, generators)
RANK_NAMES = {0: "normal", 1: "elite", 2: "rare elite", 3: "boss", 4: "rare"}
CLASS_NAMES = {1: "warrior", 2: "paladin", 4: "rogue", 8: "mage"}

# SmartScriptMgr.h SMART_ACTION_*
ACTION_CAST, ACTION_SUMMON_CREATURE, ACTION_UPDATE_TEMPLATE = 11, 12, 36
ACTION_ADD_AURA, ACTION_CALL_TIMED_ACTIONLIST, ACTION_SELF_CAST, ACTION_CROSS_CAST = 75, 80, 85, 86
ACTION_CALL_RANDOM_TIMED_ACTIONLIST, ACTION_CALL_RANDOM_RANGE_TIMED_ACTIONLIST = 87, 88
ACTION_SUMMON_CREATURE_GROUP, ACTION_INVOKER_CAST, ACTION_SUMMON_RADIAL = 107, 134, 228
CAST_ACTIONS = (ACTION_CAST, ACTION_ADD_AURA, ACTION_SELF_CAST, ACTION_CROSS_CAST, ACTION_INVOKER_CAST)
SOURCE_CREATURE, SOURCE_GAMEOBJECT, SOURCE_ACTIONLIST = 0, 1, 9  # SmartScriptType
# creature_summon_groups.summonerType (SummonerType)
SUMMONER_CREATURE, SUMMONER_GAMEOBJECT, SUMMONER_MAP = 0, 1, 2
# SharedDefines.h SpellEffects: summons read MiscValue as the creature entry; triggers read EffectTriggerSpell.
SUMMON_EFFECTS = (28, 56)
TRIGGER_EFFECTS = (32, 64, 140, 141, 142, 148)
APPLY_AURA_EFFECTS = (6, 35, 65, 119, 128, 129, 143)  # APPLY_AURA, the area auras and APPLY_AREA_AURA_OWNER
TRIGGER_AURAS = (23, 42, 227)  # PERIODIC_TRIGGER_SPELL, PROC_TRIGGER_SPELL, PERIODIC_TRIGGER_SPELL_WITH_VALUE

BLOCK_BEGIN = "# BEGIN GENERATED CREATURES (extract_dungeon_creatures.py) - do not edit inside this block by hand"
BLOCK_END = "# END GENERATED CREATURES"
WIDTH = 120


def _int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return 0


@dataclass
class World:
    """The world tables the extraction reads (`extract_dungeon_creatures.load_world` from the DB; tests by hand).
    Rows are dicts keyed by the real column names; values may be strings (mysql batch output) or ints."""

    creature_spawns: list[dict]  # guid, id, map
    gameobject_spawns: list[dict]  # guid, id, map
    templates: dict[int, dict]  # entry -> creature_template row
    multispawn: dict[int, set[int]] = field(default_factory=dict)  # creature guid -> alternate entries
    event_guids: set[int] = field(default_factory=set)  # creature guids a game event owns
    encounters: list[dict] = field(default_factory=list)  # DungeonEncounter rows: ID, MapID, Difficulty
    instance_encounters: dict[int, dict] = field(default_factory=dict)  # entry -> creditType, creditEntry
    smart_scripts: list[dict] = field(default_factory=list)  # entryorguid, source_type, action_type, action_param1-6
    template_spells: dict[int, set[int]] = field(default_factory=dict)  # creature entry -> spells
    summon_groups: list[dict] = field(default_factory=list)  # summonerId, summonerType, groupId, entry
    spells: dict[int, dict] = field(default_factory=dict)  # spell id -> Effect_n, EffectAura_n, EffectMiscValue_n, ...


@dataclass
class Extracted:
    """One creature of a dungeon, as its `creature(...)` line will say."""

    entry: int
    name: str
    role: str
    spawns: int = 0
    summoned_by: tuple[str, ...] = ()
    event: bool = False
    comment: str = ""


@dataclass
class DungeonExtract:
    map_id: int
    name: str
    creatures: list[Extracted]
    missing_templates: list[int] = field(default_factory=list)  # referenced entries with no creature_template row

    def counts(self) -> dict[str, int]:
        out = {"entries": len(self.creatures), "spawned": sum(1 for c in self.creatures if c.spawns),
               "summoned only": sum(1 for c in self.creatures if not c.spawns and c.summoned_by),
               "event": sum(1 for c in self.creatures if c.event)}
        for role in ROLES:
            out[role] = sum(1 for c in self.creatures if c.role == role)
        return out


class _Index:
    """The World's smart scripts, summon groups and spells indexed for the fixed point."""

    def __init__(self, world: World):
        self.world = world
        self.smart: dict[tuple[int, int], list[dict]] = {}
        for row in world.smart_scripts:
            key = (_int(row.get("source_type")), _int(row.get("entryorguid")))
            self.smart.setdefault(key, []).append(row)
        self.groups: dict[tuple[int, int], list[dict]] = {}
        for row in world.summon_groups:
            key = (_int(row.get("summonerType")), _int(row.get("summonerId")))
            self.groups.setdefault(key, []).append(row)

    def spell_summons(self, spell_id: int, seen: set[int] | None = None) -> list[int]:
        """Creature entries `spell_id` summons, following trigger spells and trigger auras."""
        seen = set() if seen is None else seen
        if spell_id in seen or spell_id <= 0:
            return []
        seen.add(spell_id)
        row = self.world.spells.get(spell_id)
        if row is None:
            return []
        out = []
        for i in (1, 2, 3):
            effect = _int(row.get(f"Effect_{i}"))
            if effect in SUMMON_EFFECTS and _int(row.get(f"EffectMiscValue_{i}")) > 0:
                out.append(_int(row.get(f"EffectMiscValue_{i}")))
            trigger = _int(row.get(f"EffectTriggerSpell_{i}"))
            if trigger and (effect in TRIGGER_EFFECTS or (
                effect in APPLY_AURA_EFFECTS and _int(row.get(f"EffectAura_{i}")) in TRIGGER_AURAS
            )):
                out += self.spell_summons(trigger, seen)
        return out

    def script_rows(self, source_type: int, keys: list[int]) -> list[tuple[dict, str]]:
        """Every SmartAI row of the scripts `keys` (entry and negative guids) of `source_type`, plus the timed action
        lists they call (recursively), each with a short provenance tag."""
        out, todo, seen_lists = [], [], set()
        for key in keys:
            for row in self.smart.get((source_type, key), []):
                todo.append((row, "smart" if key > 0 else f"guid {-key} smart"))
        while todo:
            row, tag = todo.pop(0)
            out.append((row, tag))
            action = _int(row.get("action_type"))
            params = [_int(row.get(f"action_param{i}")) for i in range(1, 7)]
            lists: list[int] = []
            if action == ACTION_CALL_TIMED_ACTIONLIST:
                lists = [params[0]]
            elif action == ACTION_CALL_RANDOM_TIMED_ACTIONLIST:
                lists = [p for p in params if p]
            elif action == ACTION_CALL_RANDOM_RANGE_TIMED_ACTIONLIST and 0 < params[0] <= params[1]:
                lists = list(range(params[0], params[1] + 1))
            for list_id in lists:
                if list_id in seen_lists or not list_id:
                    continue
                seen_lists.add(list_id)
                for list_row in self.smart.get((SOURCE_ACTIONLIST, list_id), []):
                    todo.append((list_row, f"actionlist {list_id}"))
        return out


def _summons_of(index: _Index, kind: str, entry: int, guids: list[int]) -> list[tuple[int, str]]:
    """(creature entry, provenance) for everything a creature or gameobject `entry` summons; `guids` are its spawns
    on the map (their guid-keyed scripts count too)."""
    source_type = SOURCE_CREATURE if kind == "creature" else SOURCE_GAMEOBJECT
    summoner_type = SUMMONER_CREATURE if kind == "creature" else SUMMONER_GAMEOBJECT
    who = f"{kind} {entry}"
    out: list[tuple[int, str]] = []
    group_ids_called: set[int] = set()
    for row, tag in index.script_rows(source_type, [entry, *(-g for g in sorted(guids))]):
        action = _int(row.get("action_type"))
        param1 = _int(row.get("action_param1"))
        if action in (ACTION_SUMMON_CREATURE, ACTION_SUMMON_RADIAL) and param1:
            out.append((param1, f"{who} {tag}"))
        elif action == ACTION_UPDATE_TEMPLATE and param1:
            out.append((param1, f"{who} {tag} update_template"))
        elif action in CAST_ACTIONS and param1:
            out += [(e, f"{who} {tag} cast {param1}") for e in index.spell_summons(param1)]
        elif action == ACTION_SUMMON_CREATURE_GROUP:
            group_ids_called.add(param1)
    for group in index.groups.get((summoner_type, entry), []):
        group_id = _int(group.get("groupId"))
        how = "smart" if group_id in group_ids_called else "script"
        out.append((_int(group.get("entry")), f"{who} summon group {group_id} ({how})"))
    if kind == "creature":
        for spell in sorted(index.world.template_spells.get(entry, ())):
            out += [(e, f"{who} spell {spell}") for e in index.spell_summons(spell)]
    return out


def auto_role(template: dict | None, is_boss: bool) -> str:
    if is_boss:
        return "boss"
    if template is None:
        return "trash"
    if _int(template.get("type")) == CREATURE_TYPE_CRITTER:
        return "critter"
    if _int(template.get("flags_extra")) & CREATURE_FLAG_EXTRA_TRIGGER or str(template.get("name") or "").startswith(
        DEVELOPER_PREFIXES
    ):
        return "trigger"
    if _int(template.get("npcflag")):
        return "npc"
    return "trash"


def describe(template: dict | None) -> str:
    """The trailing reference comment of a creature line: level range, rank and class."""
    if template is None:
        return "no creature_template row"
    low, high = sorted((_int(template.get("minlevel")), _int(template.get("maxlevel"))))
    level = f"L{low}" if low == high else f"L{low}-{high}"
    rank = RANK_NAMES.get(_int(template.get("rank")), f"rank {template.get('rank')}")
    unit_class = CLASS_NAMES.get(_int(template.get("unit_class")), f"class {template.get('unit_class')}")
    return f"{level} {rank} {unit_class}"


def encounter_credits(world: World, map_id: int) -> list[int]:
    """The map's normal (Difficulty 0) encounters' creature kill credits (creditType 0), in encounter order."""
    out = []
    for row in sorted(world.encounters, key=lambda r: _int(r.get("ID"))):
        if _int(row.get("MapID")) != map_id or _int(row.get("Difficulty")) != 0:
            continue
        credit = world.instance_encounters.get(_int(row.get("ID")))
        if credit and _int(credit.get("creditType")) == 0 and _int(credit.get("creditEntry")):
            out.append(_int(credit.get("creditEntry")))
    return out


_SUMMONER = re.compile(r"^(creature|gameobject|map) (\d+)")


def event_only(
    members: set[int], guids_by_entry: dict[int, list[int]], event_guids: set[int], credits: set[int],
    provenance: dict[int, set[str]],
) -> set[int]:
    """The creatures that only appear during a game event: every spawn on the map is a game event's, or (not spawned)
    every summoner is such a creature (a holiday boss's adds). Encounter credits without a spawn are never event-only.
    A fixed point over the summon graph."""
    out = {e for e in members if guids_by_entry.get(e) and all(g in event_guids for g in guids_by_entry[e])}
    changed = True
    while changed:
        changed = False
        for entry in sorted(members - out):
            if guids_by_entry.get(entry) or entry in credits or not provenance.get(entry):
                continue
            summoners = [_SUMMONER.match(how) for how in provenance[entry]]
            if all(m and m.group(1) == "creature" and int(m.group(2)) in out for m in summoners):
                out.add(entry)
                changed = True
    return out


def extract(world: World, map_id: int, name: str | None = None) -> DungeonExtract:
    """Every creature of `map_id`: spawned, encounter credit, summoned (fixed point)."""
    index = _Index(world)
    name = name or VANILLA_DUNGEONS.get(map_id, (f"map {map_id}", ""))[0]
    guids_by_entry: dict[int, list[int]] = {}
    for row in world.creature_spawns:
        if _int(row.get("map")) != map_id:
            continue
        guid = _int(row.get("guid"))
        for entry in {_int(row.get("id")), *world.multispawn.get(guid, set())}:
            guids_by_entry.setdefault(entry, []).append(guid)
    go_guids: dict[int, list[int]] = {}
    for row in world.gameobject_spawns:
        if _int(row.get("map")) == map_id:
            go_guids.setdefault(_int(row.get("id")), []).append(_int(row.get("guid")))
    credits = encounter_credits(world, map_id)
    provenance: dict[int, set[str]] = {}
    found: list[tuple[int, str]] = []
    for go_entry in sorted(go_guids):
        found += _summons_of(index, "gameobject", go_entry, go_guids[go_entry])
    for group in index.groups.get((SUMMONER_MAP, map_id), []):
        found.append((_int(group.get("entry")), f"map {map_id} summon group {_int(group.get('groupId'))}"))
    members = set(guids_by_entry) | set(credits)
    todo = sorted(members)
    done: set[int] = set()
    while True:
        while todo:
            entry = todo.pop(0)
            if entry in done:
                continue
            done.add(entry)
            found += _summons_of(index, "creature", entry, guids_by_entry.get(entry, []))
        new = []
        for entry, how in found:
            if entry <= 0:
                continue
            provenance.setdefault(entry, set()).add(how)
            if entry not in members:
                members.add(entry)
                new.append(entry)
        found = []
        if not new:
            break
        todo = sorted(new)
    creatures, missing = [], []
    credit_set = set(credits)
    events = event_only(members, guids_by_entry, world.event_guids, credit_set, provenance)
    for entry in sorted(members):
        template = world.templates.get(entry)
        if template is None:
            missing.append(entry)
            continue
        guids = guids_by_entry.get(entry, [])
        event = entry in events
        creatures.append(Extracted(
            entry=entry, name=str(template.get("name") or ""), role=auto_role(template, entry in credit_set),
            spawns=len(guids), summoned_by=tuple(sorted(provenance.get(entry, ()))), event=event,
            comment=describe(template),
        ))
    order = {role: i for i, role in enumerate(ROLES)}
    creatures.sort(key=lambda c: (order[c.role], c.entry))
    return DungeonExtract(map_id=map_id, name=name, creatures=creatures, missing_templates=missing)


# ---------------------------------------------------------------------------------------------------------------------
# Rendering the declaration file


def py_string(text: str) -> str:
    """A double-quoted Python string literal."""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render_creature(c: Extracted, indent: str = "    ") -> str:
    """One `creature(...)` line (wrapped inside `WIDTH` columns when `summoned_by` is long)."""
    args = [str(c.entry), py_string(c.name), py_string(c.role)]
    if c.spawns:
        args.append(f"spawns={c.spawns}")
    if c.event:
        args.append("event=True")
    comment = f"  # {c.comment}" if c.comment else ""
    if c.summoned_by:
        summoned = "(" + ", ".join(py_string(s) for s in c.summoned_by) + ("," if len(c.summoned_by) == 1 else "") + ")"
        line = f"{indent}creature({', '.join(args)}, summoned_by={summoned}),{comment}"
        if len(line) <= WIDTH:
            return line
        head = f"{indent}creature({', '.join(args)}, summoned_by=(" + comment
        if len(head) > WIDTH:
            head = f"{indent}creature({', '.join(args)}, summoned_by=("
        lines = [head]
        lines += [f"{indent}    {py_string(s)}," for s in c.summoned_by]
        lines.append(f"{indent})),")
        return "\n".join(lines)
    line = f"{indent}creature({', '.join(args)}),{comment}"
    if len(line) > WIDTH:
        line = f"{indent}creature({', '.join(args)}),"
    return line


def render_block(extract_: DungeonExtract) -> str:
    """The generated `CREATURES = (...)` block, markers included."""
    lines = [BLOCK_BEGIN, "CREATURES = ("]
    lines += [render_creature(c) for c in extract_.creatures]
    lines += [")", BLOCK_END]
    return "\n".join(lines)


def variable_name(stem: str) -> str:
    return re.sub(r"[^a-z0-9_]", "_", stem.lower())


def render_new_file(extract_: DungeonExtract, stem: str) -> str:
    """A new declaration file: docstring, imports, the generated block and a heroic-off `dungeon(...)` call."""
    body = (
        f"{extract_.name} (map {extract_.map_id}): every creature of the dungeon as a reference declaration (dungeon "
        f"difficulties E2, WP-G). The `CREATURES` block is generated by apps/dbc-tools/extract_dungeon_creatures.py "
        f"from the live world DB; rerun it to refresh the block and never edit inside the markers. Hand edits go in "
        f"the `dungeon(...)` call: `extra=` (creatures the extraction cannot see, e.g. C++ summons), `roles=` (role "
        f"corrections), `skip=` (entries that never get a heroic template) and `heroic=heroic(...)` (none yet: normal "
        f"only, so this file emits nothing)."
    )
    doc = '"""\n' + textwrap.fill(body, WIDTH) + '\n"""\n'
    return (
        f"{doc}\nfrom lib.dsl.dungeon import creature, dungeon\n\n{render_block(extract_)}\n\n"
        f"{variable_name(stem)} = dungeon({extract_.map_id}, {py_string(extract_.name)}, creatures=CREATURES)\n"
    )


class BlockError(ValueError):
    pass


def replace_block(text: str, block: str) -> str:
    """`text` with its generated block replaced by `block`; everything outside the markers is kept byte for byte."""
    begin, end = text.find(BLOCK_BEGIN), text.find(BLOCK_END)
    if begin < 0 or end < 0 or end < begin or text.count(BLOCK_BEGIN) != 1 or text.count(BLOCK_END) != 1:
        raise BlockError("expected exactly one generated block (BEGIN / END markers) - fix the file by hand first")
    return text[:begin] + block + text[end + len(BLOCK_END):]
