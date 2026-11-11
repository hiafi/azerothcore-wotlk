"""
Scoped write runs: `generate.py --scope <name>[,<name>...]` (dbc-tools-scoped-generate plan, section 1).

A full write run regenerates every reserved block (`DELETE FROM spell_dbc WHERE ID BETWEEN 200101 AND 209999` plus a
full re-insert) and builds patch-Z from every source row, so a run from a branch that lacks another branch's rows wipes
them. A scoped run computes exactly what a full run computes (same loaders, same DSL, same lints, same derived rows),
then narrows the output to the rows its scope owns:

- **SQL.** The reserved-block DELETEs narrow to the scope's reservation ranges, minus every id another scope owns;
  the scope's rows outside those ranges are written with an explicit `DELETE ... IN` + INSERT. Every other statement
  (the keyed tables, the item, loot, creature and dungeon blocks, the prune and removal passes) is filtered row by row:
  a row the scope owns stays, a row another scope (or no scope) owns is left out and counted in the summary.
  A statement this module cannot split (an unknown shape) stops the run.
- **Client.** The deployed patch-Z (or `--deployed-patch`) is repacked like `--only items` does: each DBC the full
  run would ship keeps every deployed row except the ids the scope owns, which take the full build's rows (or go,
  when the build no longer has them). Shared secondary rows (cast times, durations, ranges, radii) are added when a
  scope row needs one the base lacks; a different row at the same id stops the run.
- **Files.** Lock files, `ItemSpellCopies.h`, `ItemTierLabels.lua` and `ItemSetMembers.lua` are one file for every
  scope: they are written only when everything that changes in them belongs to the scope, else the run stops.
  Generated class headers are written for the scope's classes only.

**Scopes** (`source/scopes.yaml`): a scope is a name with reservations (ids.yaml `reservations:` keys) and source
files. By convention scope N owns the reservation N and the sources `classes/N`, `npcs/N`, `npcs/N_*.py`, `world/N`,
`world/dungeons/N.py`, `items/N.py` and `items/N_*.py`; the YAML adds more of either. `pools:` names reservations no
scope owns (a mint pool such as `items`, whose ids belong to whoever's declaration minted them).

**Ownership** of an id (per id space, the ids.yaml block name: `spell`, `creature`, `item`, ...):

1. declared: a source file of the scope declared it (`registry.declared_in`), or it derives from such a declaration
   (an item's tier entries, effect spell copies and limit category, a set's tokens and costs, a dungeon's creatures
   and heroic copies, a class's GCD-haste aura);
2. else reserved: it lies inside one of the scope's reservation ranges;
3. else nobody's: only a full run writes it.

A keyed row (a `spell_script_names` binding, a loot group, ...) is owned by the scope that declared that exact key,
else by the owner of its id column (e.g. `spell_proc.SpellId`). An id owned by two scopes is a conflict: a scoped run
that touches it stops.

`items` is not a scope: `--scope items` is `--only items` (every item table, all owners).
"""

from __future__ import annotations

import re
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from . import dbcfile, resolve, sql_out
from .dsl import registry as _registry
from .source import foreign_ids

TOOL_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = TOOL_ROOT / "source"
SCOPES_PATH = SOURCE_DIR / "scopes.yaml"
ITEMS_ALIAS = "items"  # `--scope items` = `--only items`


class ScopeError(ValueError):
    """A scoped run cannot go on (bad scope file, an unsplittable statement, an ownership conflict)."""


# ---------------------------------------------------------------------------------------------------------------------
# Scope definitions
# ---------------------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class ScopeDef:
    name: str
    reservations: tuple[str, ...]
    sources: tuple[str, ...]  # explicit extra sources (paths under source/); the conventional ones are implicit


@dataclass
class Scopes:
    defs: dict[str, ScopeDef]
    pools: tuple[str, ...]

    def names(self) -> list[str]:
        return sorted(self.defs)

    def source_scope(self, rel_path: str) -> str | None:
        """The scope whose sources include `rel_path` (a path under source/, `/`-separated), or None."""
        found = [name for name, scope in self.defs.items() if _source_matches(scope, rel_path)]
        if len(found) > 1:
            raise ScopeError(f"source/{rel_path} belongs to more than one scope: {', '.join(sorted(found))}")
        return found[0] if found else None


def _conventional_sources(name: str) -> tuple[str, ...]:
    return (f"classes/{name}", f"npcs/{name}", f"world/{name}", f"world/dungeons/{name}.py", f"items/{name}.py")


def _source_matches(scope: ScopeDef, rel_path: str) -> bool:
    rel_path = rel_path.replace("\\", "/")
    name = scope.name
    parts = rel_path.split("/")
    for source in (*_conventional_sources(name), *scope.sources):
        source = source.rstrip("/")
        if rel_path == source or rel_path.startswith(source + "/") or rel_path == source + ".py":
            return True
    # npcs/N_*.py and items/N_*.py (one file per concern: items/deadmines_loot.py, npcs/warrior_npcs.py)
    if len(parts) == 2 and parts[0] in ("npcs", "items") and parts[1].startswith(name + "_") and \
            parts[1].endswith(".py"):
        return True
    return False


def load_scopes(path: Path = SCOPES_PATH, ids_cfg: dict | None = None) -> Scopes:
    """Reads `source/scopes.yaml`. With `ids_cfg`, checks every named reservation exists."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    defs: dict[str, ScopeDef] = {}
    for name, body in (data.get("scopes") or {}).items():
        body = body or {}
        if name == ITEMS_ALIAS:
            raise ScopeError(f"{path}: `{ITEMS_ALIAS}` cannot be a scope (--scope items is --only items)")
        if not re.fullmatch(r"[a-z][a-z0-9_]*", str(name)):
            raise ScopeError(f"{path}: scope name {name!r} must be lower_snake_case")
        unknown = set(body) - {"reservations", "sources"}
        if unknown:
            raise ScopeError(f"{path}: scope {name}: unknown key(s) {sorted(unknown)}")
        defs[name] = ScopeDef(name, tuple(body.get("reservations") or ()), tuple(body.get("sources") or ()))
    pools = tuple(data.get("pools") or ())
    scopes = Scopes(defs, pools)
    if ids_cfg is not None:
        reservations = ids_cfg.get("reservations") or {}
        for scope in defs.values():
            for res in scope.reservations:
                if res not in reservations:
                    raise ScopeError(f"{path}: scope {scope.name}: no reservation {res!r} in ids.yaml")
        for pool in pools:
            if pool not in reservations:
                raise ScopeError(f"{path}: pool {pool!r} is not a reservation in ids.yaml")
    return scopes


def scope_reservations(scopes: Scopes, ids_cfg: dict) -> dict[str, tuple[str, ...]]:
    """`{scope: reservation names}`: the conventional one (same name, when ids.yaml has it) plus the listed ones."""
    reservations = ids_cfg.get("reservations") or {}
    out = {}
    for name, scope in scopes.defs.items():
        names = ([name] if name in reservations else []) + [r for r in scope.reservations if r != name]
        out[name] = tuple(names)
    return out


def parse_names(text: str) -> list[str]:
    return [part.strip() for part in text.split(",") if part.strip()]


# ---------------------------------------------------------------------------------------------------------------------
# Ownership
# ---------------------------------------------------------------------------------------------------------------------

def _norm(value):
    """A key value on one footing whether it came from a declaration (int / str) or from SQL text (float / str)."""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if re.fullmatch(r"-?\d+", stripped):
            return int(stripped)
    return value


# Table -> (id column, id space): the fallback owner of a row nobody declared by its exact key. The id spaces are the
# ids.yaml block names (reservations use the same names).
TABLE_IDS: dict[str, tuple[str, str]] = {
    "spell_dbc": ("ID", "spell"),
    "talent_dbc": ("ID", "talent"),
    "talenttab_dbc": ("ID", "talenttab"),
    "skilllineability_dbc": ("ID", "skilllineability"),
    "item_dbc": ("ID", "item"),
    "spell_script_names": ("spell_id", "spell"),
    "spell_bonus_data": ("entry", "spell"),
    "spell_proc": ("SpellId", "spell"),
    "spell_linked_spell": ("spell_trigger", "spell"),
    "spell_group": ("spell_id", "spell"),
    "spell_group_stack_rules": ("group_id", "spell_group"),
    "spell_custom_attr": ("spell_id", "spell"),
    "spellcategory_dbc": ("ID", "spellcategory"),
    "spell_potency_correction": ("spell_id", "spell"),
    "creature_template_spell": ("CreatureID", "creature"),
    "spellrunecost_dbc": ("ID", "spellrunecost"),
    "spell_threat": ("entry", "spell"),
    "playercreateinfo_cast_spell": ("spell", "spell"),
    "mapdifficulty_dbc": ("ID", "mapdifficulty"),
    "dungeon_access_template": ("id", "dungeon_access"),
    "dungeonencounter_dbc": ("ID", "dungeonencounter"),
    "itemlimitcategory_dbc": ("ID", "item_limit_category"),
    "spellitemenchantment_dbc": ("ID", "spellitemenchantment"),
    "itemrandomsuffix_dbc": ("ID", "itemrandomsuffix"),
    "gemproperties_dbc": ("ID", "gemproperties"),
    "spellitemenchantmentcondition_dbc": ("ID", "spellitemenchantmentcondition"),
    "item_enchantment_template": ("entry", "item_enchantment_pool"),
    "instance_encounters": ("entry", "dungeonencounter"),
    # Dungeon finder entries (lfg-classic-heroic): declared in a shared world file, so no scope owns them (a full run
    # writes them); listed so a scope's heroic final boss that names one not yet live stops the run (reference_errors).
    "lfgdungeons_dbc": ("ID", "lfgdungeons"),
    "lfg_dungeon_template": ("dungeonId", "lfgdungeons"),
    "creature_template_addon": ("entry", "creature"),
    "creature_template_resistance": ("CreatureID", "creature"),
    "creature_template_movement": ("CreatureId", "creature"),
    "creature_onkill_reputation": ("creature_id", "creature"),
    "creature_template": ("entry", "creature"),
    "creature_template_model": ("CreatureID", "creature"),
    "item_template": ("entry", "item"),
    "item_itemization": ("entry", "item"),
    "item_budget_variant": ("entry", "item"),
    "creature_loot_template": ("Entry", "creature"),  # Entry is the lootid: a boss's own entry, or its heroic copy's
    "reference_loot_template": ("Entry", "loot_reference"),
    "itemset_dbc": ("ID", "item_set"),
    "itemextendedcost_dbc": ("ID", "item_extended_cost"),
    "npc_vendor": ("entry", "creature"),
    "trainer_spell": ("SpellId", "spell"),
    # Spawn rows by guid (the heroic spawnMask UPDATEs): a dungeon scope owns the spawns on its map (map_spawns).
    "creature": ("guid", "creature_guid"),
    "gameobject": ("guid", "gameobject_guid"),
    # smart_scripts: by its (entryorguid, source_type) key, see Ownership.row_owners.
}
# smart_scripts.source_type -> the id space of a positive (template entry) / negative (spawn guid) entryorguid.
SMART_SOURCE_SPACES = {0: ("creature", "creature_guid"), 1: ("gameobject", "gameobject_guid")}


@dataclass
class Ownership:
    """Who owns which id and which declared key. `selected`: the scopes of this run."""

    selected: frozenset[str]
    ranges: dict[str, list[tuple[int, int, str]]] = field(default_factory=dict)  # space -> (start, end, scope)
    declared: dict[str, dict[int, set[str]]] = field(default_factory=dict)  # space -> id -> scopes
    keys: dict[str, dict[tuple, set[str]]] = field(default_factory=dict)  # table -> key tuple -> scopes
    key_columns: dict[str, tuple[str, ...]] = field(default_factory=dict)  # table -> its declared key columns
    blocks: dict[str, dict] = field(default_factory=dict)  # space -> ids.yaml block (foreign holes)

    def declare(self, space: str, entry_id, scope: str | None) -> None:
        if scope is None or entry_id is None:
            return
        entry_id = _norm(entry_id)
        if not isinstance(entry_id, int):
            return
        self.declared.setdefault(space, {}).setdefault(entry_id, set()).add(scope)

    def declare_key(self, table: str, key: tuple, scope: str | None) -> None:
        if scope is None:
            return
        self.keys.setdefault(table, {}).setdefault(tuple(_norm(v) for v in key), set()).add(scope)

    def owners(self, space: str, entry_id) -> frozenset[str]:
        entry_id = _norm(entry_id)
        if not isinstance(entry_id, int):
            return frozenset()
        declared = self.declared.get(space, {}).get(entry_id)
        if declared:
            return frozenset(declared)
        return frozenset(scope for start, end, scope in self.ranges.get(space, ()) if start <= entry_id <= end)

    def row_owners(self, table: str, row: dict) -> frozenset[str]:
        """The owner(s) of one row of `table` (`row`: at least the columns the statement names)."""
        columns = self.key_columns.get(table)
        if columns and all(c in row for c in columns):
            scopes = self.keys.get(table, {}).get(tuple(_norm(row[c]) for c in columns))
            if scopes:
                return frozenset(scopes)
        if table == "smart_scripts":
            spaces = SMART_SOURCE_SPACES.get(_norm(row.get("source_type")))
            value = _norm(row.get("entryorguid"))
            if spaces is None or not isinstance(value, int) or value == 0:
                return frozenset()
            return self.owners(spaces[0], value) if value > 0 else self.owners(spaces[1], -value)
        if table == "conditions":
            space = CONDITION_SOURCE_SPACES.get(_norm(row.get("SourceTypeOrReferenceId")))
            value = _norm(row.get("SourceGroup"))
            if space is None or not isinstance(value, int) or value <= 0:
                return frozenset()
            return self.owners(space, value)
        id_column = TABLE_IDS.get(table)
        if id_column and id_column[0] in row:
            return self.owners(id_column[1], row[id_column[0]])
        return frozenset()

    def mine(self, owners: frozenset[str]) -> bool:
        """True when the run's scopes own this (one owner or several, all selected)."""
        return bool(owners) and owners <= self.selected

    def conflict(self, owners: frozenset[str]) -> bool:
        """Owned by a selected scope and by another one: the run cannot tell whose row it is."""
        return bool(owners & self.selected) and not owners <= self.selected

    def label(self, owners: frozenset[str]) -> str:
        return "+".join(sorted(owners)) if owners else "no scope"

    def scope_ranges(self, space: str, block: dict) -> list[tuple[int, int]]:
        """The `(start, end)` ranges a scoped reserved-block DELETE may clear: the selected scopes' reservation ranges
        of `space` inside `block`, less every id declared by another scope and the block's `foreign` ids."""
        holes = set(foreign_ids(block))
        for entry_id, scopes in self.declared.get(space, {}).items():
            if not scopes <= self.selected:
                holes.add(entry_id)
        out: list[tuple[int, int]] = []
        for start, end, scope in sorted(self.ranges.get(space, ())):
            if scope not in self.selected:
                continue
            start, end = max(start, int(block["start"])), min(end, int(block["end"]))
            cursor = start
            for hole in sorted(h for h in holes if start <= h <= end):
                if cursor < hole:
                    out.append((cursor, hole - 1))
                cursor = hole + 1
            if cursor <= end:
                out.append((cursor, end))
        return _merge_ranges(out)

    def owned_ids(self, space: str) -> set[int]:
        """Every declared id the selected scopes own (reservation ranges not expanded)."""
        return {i for i, scopes in self.declared.get(space, {}).items() if scopes <= self.selected}


def _merge_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for start, end in sorted(ranges):
        if out and start <= out[-1][1] + 1:
            out[-1] = (out[-1][0], max(out[-1][1], end))
        else:
            out.append((start, end))
    return out


def in_ranges(entry_id: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start <= entry_id <= end for start, end in ranges)


def entry_scope(entry: dict, scopes: Scopes) -> str | None:
    """The scope of a declared entry, from the file that declared it (`registry.declared_in`, or a CSV row's
    `_source_file`)."""
    path = _registry.declared_in(entry)
    if path:
        try:
            rel = Path(path).resolve().relative_to(SOURCE_DIR.resolve()).as_posix()
        except ValueError:
            return None
        return scopes.source_scope(rel)
    csv = entry.get("_source_file")
    if csv:
        return scopes.source_scope(f"spells/{csv}")
    return None


# The registry lists whose entries are rows of one id space, keyed by one column (besides the TableSpec keys below).
_DECLARED_ID_LISTS = (
    ("creature_templates", "entry", "creature"),
    ("creature_template_edits", "entry", "creature"),
    ("creature_template_models", "CreatureID", "creature"),
    ("item_templates", "entry", "item"),
    ("spell_categories", "ID", "spellcategory"),
    ("spell_rune_costs", "ID", "spellrunecost"),
    ("tooltip_vars", "id", "spelldescriptionvariables"),
    ("map_difficulties", "ID", "mapdifficulty"),
    ("dungeon_access", "id", "dungeon_access"),
    ("dungeon_encounters", "ID", "dungeonencounter"),
    # Crafting rework C1: a declaration (or an override of a stock id) belongs to the scope of its file in both halves.
    ("spell_item_enchantments", "ID", "spellitemenchantment"),
    ("item_random_suffixes", "ID", "itemrandomsuffix"),
    ("gem_properties", "ID", "gemproperties"),
    ("enchant_conditions", "ID", "spellitemenchantmentcondition"),
    ("item_enchantment_pools", "entry", "item_enchantment_pool"),
)

# conditions.SourceTypeOrReferenceId -> the id space of its SourceGroup, for the loot conditions lib/loot_tables.py
# writes (creature loot: the lootid; reference loot: the pool's Entry).
CONDITION_SOURCE_SPACES = {1: "creature", 10: "loot_reference"}

# SpellFamilyName -> class scope, for the generated GCD-haste auras (lib/gcd_haste.py, source/gcd_haste.py).
FAMILY_CLASSES = {
    3: "mage", 4: "warrior", 5: "warlock", 6: "priest", 7: "druid", 8: "rogue", 9: "hunter", 10: "paladin",
    11: "shaman", 15: "deathknight",
}


def build_ownership(
    scopes: Scopes, ids_cfg: dict, selected, *, dsl_classes: dict, spell_entries: list[dict], talents: dict,
    table_specs, item_expansion=None, item_spell_expansion=None, item_limit_expansion=None, heroic_lock=None,
    gcd_aura_ids: dict[int, int] | None = None, map_spawns: dict | None = None,
) -> Ownership:
    """Every declared and derived id of every scope (not only the selected ones: the holes in a scope's ranges are
    the other scopes' ids). `table_specs`: the TableSpecs whose declared rows are owned by their exact key."""
    own = Ownership(frozenset(selected))
    reservations = ids_cfg.get("reservations") or {}
    for name, res_names in scope_reservations(scopes, ids_cfg).items():
        for res in res_names:
            for space, block in (reservations.get(res) or {}).items():
                if isinstance(block, dict) and "start" in block:
                    own.ranges.setdefault(space, []).append((int(block["start"]), int(block["end"]), name))
    for space, block in ids_cfg.items():
        if isinstance(block, dict) and "start" in block:
            own.blocks[space] = block

    def scope_of(entry: dict) -> str | None:
        return entry_scope(entry, scopes)

    for entry in spell_entries:
        own.declare("spell", entry.get("id"), scope_of(entry))
    for key, space in (("talents", "talent"), ("tabs", "talenttab"), ("skill_line_abilities", "skilllineability")):
        for entry in talents.get(key, ()):
            own.declare(space, entry.get("id"), scope_of(entry))
    for list_key, column, space in _DECLARED_ID_LISTS:
        for entry in dsl_classes.get(list_key, ()):
            own.declare(space, entry.get(column), scope_of(entry))
    for spec in table_specs:
        own.key_columns.setdefault(spec.name, tuple(spec.key_columns))
        for entry in dsl_classes.get(spec.registry_key, ()):
            scope = scope_of(entry)
            if scope is not None and all(c in entry for c in spec.key_columns):
                own.declare_key(spec.name, tuple(entry[c] for c in spec.key_columns), scope)
    own.key_columns.setdefault("trainer_spell", ("TrainerId", "SpellId"))
    for entry in dsl_classes.get("trainer_spells", ()):
        own.declare_key("trainer_spell", (entry.get("TrainerId"), entry.get("SpellId")), scope_of(entry))

    # Dungeons: the map, its creatures (normal entries) and their heroic copies (heroic_ids.lock) belong to the scope
    # of the file that declared dungeon(); the derived encounter rows follow the map.
    map_scope: dict[int, str] = {}
    for entry in dsl_classes.get("dungeons", ()):
        scope = scope_of(entry)
        if scope is None:
            continue
        map_scope[int(entry["map_id"])] = scope
        for creature in entry.get("creatures") or ():
            own.declare("creature", creature.get("entry"), scope)
    if heroic_lock is not None:
        for normal, heroic in heroic_lock.pairs.items():
            scope = map_scope.get(heroic_lock.maps.get(normal))
            own.declare("creature", normal, scope)
            own.declare("creature", heroic, scope)
    # The spawns on a scope's dungeon map and the SmartAI scripts that run there (their entries and spawn guids, by
    # source_type) belong to it too (`map_spawns`: map -> spawn table -> guid -> template entry, from the dungeon
    # expansion's live world).
    own.key_columns.setdefault("smart_scripts", ("entryorguid", "source_type"))
    creatures_of_map = {
        int(entry["map_id"]): {int(c["entry"]) for c in entry.get("creatures") or () if c.get("entry")}
        for entry in dsl_classes.get("dungeons", ())
    }
    for map_id, tables in (map_spawns or {}).items():
        scope = map_scope.get(int(map_id))
        if scope is None:
            continue
        creature_guids = set(tables.get("creature", {}))
        gameobject_guids = set(tables.get("gameobject", {}))
        for guid in creature_guids:
            own.declare("creature_guid", guid, scope)
        for guid in gameobject_guids:
            own.declare("gameobject_guid", guid, scope)
        entries = creatures_of_map.get(int(map_id), set()) | set(tables.get("creature", {}).values())
        gameobject_ids = set(tables.get("gameobject", {}).values())
        keys = ({(e, 0) for e in entries} | {(-g, 0) for g in creature_guids}
                | {(e, 1) for e in gameobject_ids} | {(-g, 1) for g in gameobject_guids})
        for key in keys:
            own.declare_key("smart_scripts", key, scope)
    for key in ("dungeon_encounters", "map_difficulties"):
        for row in dsl_classes.get(key, ()):
            own.declare({"dungeon_encounters": "dungeonencounter", "map_difficulties": "mapdifficulty"}[key],
                        row.get("ID"), map_scope.get(_norm(row.get("MapID"))))
    for row in dsl_classes.get("dungeon_access", ()):
        own.declare("dungeon_access", row.get("id"), map_scope.get(_norm(row.get("map_id"))))
    encounter_scope = {i: s for i, s in own.declared.get("dungeonencounter", {}).items()}
    for row in dsl_classes.get("instance_encounters", ()):
        for scope in encounter_scope.get(_norm(row.get("entry")), ()):
            own.declare("dungeonencounter", row.get("entry"), scope)

    # Items: a key's tiers, its effect spell copies and its limit category follow the item() declaration.
    key_scope: dict[str, str] = {}
    for entry in dsl_classes.get("item_declarations", ()):
        scope = scope_of(entry)
        if scope is not None:
            key_scope[str(entry["id"])] = scope
    if item_expansion is not None:
        for item in item_expansion.items:
            scope = key_scope.get(item.decl.key)
            for tier in item.tiers:
                own.declare("item", tier.entry, scope)
    if item_spell_expansion is not None:
        for tier in item_spell_expansion.tiers:
            for copy_id in tier.remap.values():
                own.declare("spell", copy_id, key_scope.get(tier.key))
    if item_limit_expansion is not None:
        for key, category in item_limit_expansion.categories.items():
            own.declare("item_limit_category", category, key_scope.get(key))
    for entry in dsl_classes.get("loot_declarations", ()):
        scope, decl = scope_of(entry), entry["_decl"]
        if getattr(decl, "pool_removal", False):
            own.declare("loot_reference", decl.reference, scope)  # a stock pool the scope deletes
            continue
        own.declare("creature", decl.lootid, scope)
        own.declare_key("creature_loot_template", (decl.lootid, decl.group), scope)
        if decl.reference:
            own.declare("loot_reference", decl.reference, scope)
    own.key_columns.setdefault("creature_loot_template", ("Entry", "GroupId"))
    for entry in dsl_classes.get("item_set_declarations", ()):
        scope, decl = scope_of(entry), entry["_decl"]
        if hasattr(decl, "set_id"):
            own.declare("item_set", decl.set_id, scope)
        for _tier, item_entry in getattr(decl, "entries", ()):
            own.declare("item", item_entry, scope)
        for _tier, cost in getattr(decl, "costs", ()):
            own.declare("item_extended_cost", cost, scope)
        if hasattr(decl, "sets") and hasattr(decl, "entry"):
            own.declare("creature", decl.entry, scope)
    for family, aura_id in (gcd_aura_ids or {}).items():
        scope = FAMILY_CLASSES.get(family)
        if scope in scopes.defs:
            own.declare("spell", aura_id, scope)
    return own


# ---------------------------------------------------------------------------------------------------------------------
# SQL statements: a small reader for what the renderers emit
# ---------------------------------------------------------------------------------------------------------------------

def split_statements(text: str) -> list[str]:
    """`text` as a list of statements (each ending with `;`) and `--` comment lines, in order. Quotes are honoured,
    so a `;` inside a tooltip string does not end a statement."""
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        while i < n and text[i] in " \t\r\n":
            i += 1
        if i >= n:
            break
        if text.startswith("--", i):
            end = text.find("\n", i)
            end = n if end < 0 else end
            out.append(text[i:end])
            i = end + 1
            continue
        start = i
        quote = None
        while i < n:
            ch = text[i]
            if quote:
                if ch == "\\":
                    i += 2
                    continue
                if ch == quote:
                    if i + 1 < n and text[i + 1] == quote:
                        i += 2
                        continue
                    quote = None
            elif ch in "'\"":
                quote = ch
            elif ch == ";":
                i += 1
                break
            i += 1
        out.append(text[start:i].strip())
    return out


_LITERAL_RE = re.compile(r"\s*(NULL|-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?|'(?:[^'\\]|\\.|'')*')\s*", re.IGNORECASE)


def _literal(token: str):
    token = token.strip()
    if token.upper() == "NULL":
        return None
    if token.startswith("'"):
        body = token[1:-1].replace("''", "'")
        return re.sub(r"\\(.)", lambda m: {"n": "\n", "r": "\r", "0": "\0"}.get(m.group(1), m.group(1)), body)
    try:
        return int(token)
    except ValueError:
        return float(token)


def _split_top(text: str, sep: str = ",") -> list[str]:
    """`text` split on `sep` outside parentheses and quotes."""
    parts, depth, quote, cur, i = [], 0, None, [], 0
    while i < len(text):
        ch = text[i]
        if quote:
            cur.append(ch)
            if ch == "\\" and i + 1 < len(text):
                cur.append(text[i + 1])
                i += 2
                continue
            if ch == quote:
                if i + 1 < len(text) and text[i + 1] == quote:
                    cur.append(text[i + 1])
                    i += 2
                    continue
                quote = None
        elif ch in "'\"":
            quote = ch
            cur.append(ch)
        elif ch == "(":
            depth += 1
            cur.append(ch)
        elif ch == ")":
            depth -= 1
            cur.append(ch)
        elif ch == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
        i += 1
    parts.append("".join(cur))
    return parts


def _tuples(text: str) -> list[tuple[str, str]]:
    """The `( ... )` groups of a VALUES list (or an IN list of tuples) as `(group text, separator after it)`."""
    out, i, n = [], 0, len(text)
    while i < n:
        while i < n and text[i] in " \t\r\n,":
            i += 1
        if i >= n:
            break
        if text[i] != "(":
            raise ScopeError(f"expected '(' at {text[i:i + 40]!r}")
        start, depth, quote = i, 0, None
        while i < n:
            ch = text[i]
            if quote:
                if ch == "\\":
                    i += 2
                    continue
                if ch == quote:
                    if i + 1 < n and text[i + 1] == quote:
                        i += 2
                        continue
                    quote = None
            elif ch == "'":
                quote = ch
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    i += 1
                    break
            i += 1
        out.append((text[start:i], ""))
    return out


def first_group(text: str) -> str | None:
    """The balanced `( ... )` group `text` starts with (quotes honoured), or None."""
    if not text.startswith("("):
        return None
    depth, quote, i, n = 0, None, 0, len(text)
    while i < n:
        ch = text[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                if i + 1 < n and text[i + 1] == quote:
                    i += 2
                    continue
                quote = None
        elif ch == "'":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[:i + 1]
        i += 1
    return None


def _values(group: str) -> list:
    inner = group.strip()[1:-1]
    return [_literal(token) for token in _split_top(inner)]


def _columns(text: str) -> list[str]:
    return [c.strip().strip("`") for c in text.split(",")]


_INSERT_RE = re.compile(r"^INSERT\s+INTO\s+`?(\w+)`?\s*\(([^)]*)\)\s*VALUES\s*", re.IGNORECASE | re.DOTALL)
_DELETE_RE = re.compile(r"^DELETE\s+FROM\s+`?(\w+)`?\s+WHERE\s+(.*);$", re.IGNORECASE | re.DOTALL)
_UPDATE_RE = re.compile(r"^UPDATE\s+`?(\w+)`?\s+SET\s+(.*?)\s+WHERE\s*(.*);$", re.IGNORECASE | re.DOTALL)
_ON_DUP_RE = re.compile(r"\)\s*(ON\s+DUPLICATE\s+KEY\s+UPDATE\b.*);$", re.IGNORECASE | re.DOTALL)
_COL = r"`?(\w+)`?"
_EQ_RE = re.compile(rf"^\s*{_COL}\s*=\s*(.+?)\s*$", re.DOTALL)
_IN_RE = re.compile(rf"^\s*{_COL}\s+IN\s*\((.*)\)\s*$", re.IGNORECASE | re.DOTALL)
_TUPLE_IN_RE = re.compile(r"^\s*\(([^()]*)\)\s+IN\s*\((.*)\)\s*$", re.IGNORECASE | re.DOTALL)
_BETWEEN_RE = re.compile(rf"^\s*{_COL}\s+BETWEEN\s+(-?\d+)\s+AND\s+(-?\d+)\s*$", re.IGNORECASE)


def _split_and(text: str) -> list[str]:
    """Top-level `AND` conjuncts, keeping `BETWEEN a AND b` whole."""
    parts = [p for p in re.split(r"\s+AND\s+", text, flags=re.IGNORECASE)]
    # re-join pieces split inside parentheses or a BETWEEN
    out: list[str] = []
    for part in parts:
        if out and (out[-1].count("(") > out[-1].count(")") or re.search(r"\bBETWEEN\s+-?\d+\s*$", out[-1], re.I)):
            out[-1] = f"{out[-1]} AND {part}"
        else:
            out.append(part)
    return out


def _split_or(text: str) -> list[str]:
    parts, depth, quote, cur, i = [], 0, None, [], 0
    upper = text.upper()
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == quote:
                quote = None
        elif ch == "'":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif depth == 0 and upper.startswith("OR", i) and (i == 0 or not text[i - 1].isalnum()) and \
                (i + 2 >= len(text) or not text[i + 2].isalnum()) and text[i - 1:i].isspace():
            parts.append("".join(cur))
            cur = []
            i += 2
            continue
        cur.append(ch)
        i += 1
    parts.append("".join(cur))
    return parts


@dataclass
class Conjunct:
    text: str
    kind: str  # "eq", "in", "tuple_in", "between", "other"
    columns: tuple[str, ...] = ()
    values: list = field(default_factory=list)  # eq: [v]; in: [v, ...]; tuple_in: [(v, ...), ...]; between: [a, b]
    groups: list[str] = field(default_factory=list)  # tuple_in / in: the original item texts


def parse_conjunct(text: str) -> Conjunct:
    stripped = _strip_parens(text)
    m = _TUPLE_IN_RE.match(stripped)
    if m:
        cols = tuple(_columns(m.group(1)))
        groups = [g for g, _ in _tuples(m.group(2))]
        return Conjunct(text, "tuple_in", cols, [tuple(_values(g)) for g in groups], groups)
    m = _BETWEEN_RE.match(stripped)
    if m:
        return Conjunct(text, "between", (m.group(1),), [int(m.group(2)), int(m.group(3))])
    m = _IN_RE.match(stripped)
    if m and "(" not in m.group(2):
        items = [t for t in _split_top(m.group(2))]
        return Conjunct(text, "in", (m.group(1),), [_literal(t) for t in items], [t.strip() for t in items])
    m = _EQ_RE.match(stripped)
    if m and _LITERAL_RE.fullmatch(m.group(2)):
        return Conjunct(text, "eq", (m.group(1),), [_literal(m.group(2))])
    return Conjunct(text, "other")


def _strip_parens(text: str) -> str:
    """`text` without parentheses that wrap all of it (`(a = 1 AND b = 2)` -> `a = 1 AND b = 2`)."""
    text = text.strip()
    while text.startswith("(") and text.endswith(")") and _balanced(text[1:-1]) and not _TUPLE_IN_RE.match(text):
        text = text[1:-1].strip()
    return text


def _balanced(text: str) -> bool:
    depth = 0
    for ch in text:
        depth += ch == "("
        depth -= ch == ")"
        if depth < 0:
            return False
    return depth == 0


@dataclass
class Statement:
    kind: str  # "comment", "insert", "delete", "update"
    table: str = ""
    text: str = ""
    columns: list[str] = field(default_factory=list)  # insert
    rows: list[tuple[str, dict]] = field(default_factory=list)  # insert: (tuple text, row)
    suffix: str = ""  # insert: " ON DUPLICATE KEY UPDATE ..."
    head: str = ""  # delete / update: everything up to and including WHERE
    disjuncts: list[list[Conjunct]] = field(default_factory=list)  # delete / update: OR of ANDs
    or_separator: str = " OR "


def parse_statement(text: str) -> Statement:
    if text.startswith("--"):
        return Statement("comment", text=text)
    m = _INSERT_RE.match(text)
    if m:
        table, columns = m.group(1), _columns(m.group(2))
        body = text[m.end():]
        suffix = ""
        dup = _ON_DUP_RE.search(body)
        if dup:
            suffix = " " + dup.group(1)
            body = body[:dup.start() + 1]
        else:
            if not body.rstrip().endswith(";"):
                raise ScopeError(f"cannot read the end of: {text[:120]!r}")
            body = body.rstrip()[:-1]
        rows = []
        for group, _sep in _tuples(body):
            values = _values(group)
            if len(values) != len(columns):
                raise ScopeError(f"{table}: a row has {len(values)} value(s) for {len(columns)} column(s)")
            rows.append((group, dict(zip(columns, values))))
        return Statement("insert", table, text, columns=columns, rows=rows, suffix=suffix)
    m = _DELETE_RE.match(text) or _UPDATE_RE.match(text)
    if m:
        kind = "delete" if text.upper().startswith("DELETE") else "update"
        where = m.group(2) if kind == "delete" else m.group(3)
        head = text[:len(text) - len(where) - 1]
        disjunct_texts = _split_or(where)
        separator = " OR\n" if "\n" in where and len(disjunct_texts) > 1 else " OR "
        disjuncts = [[parse_conjunct(c) for c in _split_and(_strip_parens(d))] for d in disjunct_texts]
        return Statement(kind, m.group(1), text, head=head, disjuncts=disjuncts, or_separator=separator)
    raise ScopeError(f"cannot scope this statement: {text[:120]!r}")


# ---------------------------------------------------------------------------------------------------------------------
# Filtering the rendered SQL
# ---------------------------------------------------------------------------------------------------------------------

@dataclass
class FilterReport:
    kept: Counter = field(default_factory=Counter)  # table -> rows kept
    left_out: Counter = field(default_factory=Counter)  # (table, owner label) -> rows left out
    errors: list[str] = field(default_factory=list)

    def merge(self, other: "FilterReport") -> None:
        self.kept.update(other.kept)
        self.left_out.update(other.left_out)
        self.errors += other.errors


def _disjunct_rows(conjuncts: list[Conjunct]) -> tuple[list[dict], Conjunct | None]:
    """The rows one AND-group names, and the single list conjunct they vary over (None when it names one row)."""
    base: dict = {}
    varying: Conjunct | None = None
    for c in conjuncts:
        if c.kind == "eq":
            base[c.columns[0]] = c.values[0]
        elif c.kind in ("in", "tuple_in"):
            if varying is not None:
                varying = Conjunct("", "many")  # two lists: rows exist but cannot be split
                continue
            varying = c
        elif c.kind == "between":
            raise ScopeError("a BETWEEN outside a reserved block cannot be scoped")
    if varying is None:
        return [base], None
    if varying.kind == "many":
        rows = [base]
        for c in conjuncts:
            if c.kind == "in":
                rows = [{**r, c.columns[0]: v} for r in rows for v in c.values]
            elif c.kind == "tuple_in":
                rows = [{**r, **dict(zip(c.columns, t))} for r in rows for t in c.values]
        return rows, varying
    if varying.kind == "in":
        return [{**base, varying.columns[0]: v} for v in varying.values], varying
    return [{**base, **dict(zip(varying.columns, t))} for t in varying.values], varying


def _owner_list(table: str, conjuncts: list[Conjunct], own: Ownership) -> Conjunct | None:
    """The one `IN` list that decides a row's owner when an AND-group has several lists (else None): the table's id
    column (TABLE_IDS), when no declared key of the table is named in full."""
    lists = [c for c in conjuncts if c.kind in ("in", "tuple_in")]
    if len(lists) < 2 or table not in TABLE_IDS:
        return None
    named = {c.columns[0] for c in conjuncts if c.kind in ("eq", "in")}
    key = own.key_columns.get(table)
    if key and set(key) <= named:
        return None
    column = TABLE_IDS[table][0]
    owner_lists = [c for c in lists if c.kind == "in" and c.columns[0] == column]
    return owner_lists[0] if len(owner_lists) == 1 else None


def _rewrite_list(conjunct: Conjunct, keep: list[bool]) -> str:
    """`conjunct`'s text with only the kept items of its list."""
    if conjunct.kind == "in":
        items = [g for g, k in zip(conjunct.groups, keep) if k]
        return f"`{conjunct.columns[0]}` IN ({', '.join(items)})"
    cols = ", ".join(f"`{c}`" for c in conjunct.columns)
    items = [g for g, k in zip(conjunct.groups, keep) if k]
    return f"({cols}) IN ({', '.join(items)})"


def filter_statement(stmt: Statement, own: Ownership, report: FilterReport) -> str | None:
    """The statement's text narrowed to the rows `own` gives the run, or None when none is left."""
    table = stmt.table
    if stmt.kind == "insert":
        kept = []
        for group, row in stmt.rows:
            owners = own.row_owners(table, row)
            if own.conflict(owners):
                report.errors.append(f"{table}: a row is owned by {own.label(owners)}: {group[:80]}")
            elif own.mine(owners):
                kept.append(group)
                report.kept[table] += 1
            else:
                report.left_out[(table, own.label(owners))] += 1
        if not kept:
            return None
        if len(kept) == len(stmt.rows):
            return stmt.text
        head = stmt.text[:stmt.text.upper().index("VALUES") + len("VALUES")]
        return f"{head}\n" + ",\n".join(kept) + (stmt.suffix or "") + ";"
    kept_disjuncts: list[str] = []
    changed = False
    for conjuncts in stmt.disjuncts:
        id_list = _owner_list(table, conjuncts, own)
        if id_list is not None:
            # Several lists, ownership decided by one of them (a spawnMask UPDATE: `id IN (...) AND guid IN (...)`,
            # owned by guid): keep that list's own items; the other lists only narrow it further.
            space = TABLE_IDS[table][1]
            decisions = []
            for value in id_list.values:
                owners = own.owners(space, value)
                if own.conflict(owners):
                    report.errors.append(f"{table}: {id_list.columns[0]} {value} is owned by {own.label(owners)}")
                decisions.append(own.mine(owners) and not own.conflict(owners))
                if decisions[-1]:
                    report.kept[table] += 1
                else:
                    report.left_out[(table, own.label(owners))] += 1
            if all(decisions):
                kept_disjuncts.append(" AND ".join(c.text.strip() for c in conjuncts))
            else:
                changed = True
                if any(decisions):
                    kept_disjuncts.append(" AND ".join(
                        _rewrite_list(c, decisions) if c is id_list else c.text.strip() for c in conjuncts
                    ))
            continue
        rows, varying = _disjunct_rows(conjuncts)
        decisions = []
        for row in rows:
            owners = own.row_owners(table, row)
            if own.conflict(owners):
                report.errors.append(f"{table}: {row} is owned by {own.label(owners)}")
                decisions.append(False)
                continue
            mine = own.mine(owners)
            decisions.append(mine)
            if mine:
                report.kept[table] += 1
            else:
                report.left_out[(table, own.label(owners))] += 1
        text = " AND ".join(c.text.strip() for c in conjuncts)
        if all(decisions):
            kept_disjuncts.append(text)
        elif any(decisions):
            if varying is None or varying.kind == "many":
                report.errors.append(f"cannot split {stmt.kind.upper()} on {table} between scopes: {stmt.text[:120]!r}")
                continue
            changed = True
            kept_disjuncts.append(" AND ".join(
                _rewrite_list(c, decisions) if c is varying else c.text.strip() for c in conjuncts
            ))
        else:
            changed = True
    if not kept_disjuncts:
        return None
    if not changed:
        return stmt.text
    return f"{stmt.head}{' ' if not stmt.head.endswith((' ', chr(10))) else ''}" \
        f"{stmt.or_separator.join(kept_disjuncts)};"


def filter_sql(text: str, own: Ownership, report: FilterReport) -> str:
    """One rendered block (`text`) narrowed to the run's rows; "" when nothing is left. Comment lines go with the
    statement that follows them."""
    out: list[str] = []
    pending_comments: list[str] = []
    for raw in split_statements(text):
        try:
            stmt = parse_statement(raw)
        except ScopeError as error:
            report.errors.append(str(error))
            continue
        if stmt.kind == "comment":
            pending_comments.append(raw)
            continue
        try:
            kept = filter_statement(stmt, own, report)
        except ScopeError as error:
            report.errors.append(f"{stmt.table}: {error}")
            kept = None
        if kept is not None:
            out.extend(pending_comments)
            if pending_comments and kept != raw:
                out.append("-- (--scope: narrowed to the rows this scope owns; the counts above are the full run's)")
            out.append(kept)
        pending_comments = []
    return "\n".join(out)


def deleted_and_inserted(text: str, tables: dict[str, str]) -> dict[str, tuple[list[tuple[int, int]], set, set]]:
    """For the drop guard: per table of `tables` (`{table: id column}`), `(deleted ranges, deleted ids, inserted ids)`
    in `text`. A DELETE whose WHERE names neither a range nor a list of the id column (an unscoped DELETE) counts as
    the whole id space (`(-2**63, 2**63)`)."""
    out = {t: ([], set(), set()) for t in tables}
    for raw in split_statements(text):
        if raw.startswith("--"):
            continue
        m = re.match(r"^(INSERT\s+INTO|DELETE\s+FROM|UPDATE)\s+`?(\w+)`?", raw, re.IGNORECASE)
        if not m or m.group(2) not in tables:
            continue
        table, column = m.group(2), tables[m.group(2)]
        stmt = parse_statement(raw)
        ranges, deleted, inserted = out[table]
        if stmt.kind == "insert":
            inserted.update(_norm(row.get(column)) for _g, row in stmt.rows)
            continue
        if stmt.kind != "delete":
            continue
        for conjuncts in stmt.disjuncts:
            named = False
            for c in conjuncts:
                if c.kind == "between" and c.columns[0] == column:
                    ranges.append((c.values[0], c.values[1]))
                    named = True
                elif c.kind == "in" and c.columns[0] == column:
                    deleted.update(_norm(v) for v in c.values)
                    named = True
                elif c.kind == "eq" and c.columns[0] == column:
                    deleted.add(_norm(c.values[0]))
                    named = True
                elif c.kind == "tuple_in" and column in c.columns:
                    index = c.columns.index(column)
                    deleted.update(_norm(t[index]) for t in c.values)
                    named = True
            if not named:
                ranges.append((-(2 ** 63), 2 ** 63))
    return out


# ---------------------------------------------------------------------------------------------------------------------
# Reserved DBC blocks
# ---------------------------------------------------------------------------------------------------------------------

# DbcTable.name -> id space, for the reserved DBC blocks and the client tables.
DBC_SPACES = {
    "Spell": "spell", "Talent": "talent", "TalentTab": "talenttab", "SkillLineAbility": "skilllineability",
    "Item": "item", "SpellDescriptionVariables": "spelldescriptionvariables", "SpellCategory": "spellcategory",
    "SpellRuneCost": "spellrunecost", "MapDifficulty": "mapdifficulty", "DungeonEncounter": "dungeonencounter",
    "ItemLimitCategory": "item_limit_category", "ItemSet": "item_set", "ItemExtendedCost": "item_extended_cost",
    "LFGDungeons": "lfgdungeons", "LFGDungeonGroup": "lfgdungeongroup",
    "SpellItemEnchantment": "spellitemenchantment", "ItemRandomSuffix": "itemrandomsuffix",
    "GemProperties": "gemproperties", "SpellItemEnchantmentCondition": "spellitemenchantmentcondition",
}
# The shared secondary tables: no owner, added when a scope's spell needs one the base lacks. Spell column(s) -> table.
SECONDARY_COLUMNS = {
    "spellcasttimes": ("CastingTimeIndex",),
    "spellduration": ("DurationIndex",),
    "spellrange": ("RangeIndex",),
    "spellradius": ("EffectRadiusIndex_1", "EffectRadiusIndex_2", "EffectRadiusIndex_3"),
}


@dataclass
class BlockResult:
    blocks: list[tuple] = field(default_factory=list)  # (table, id_range, rows, explicit ids) for sql_out
    notes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    changed: dict[str, set[int]] = field(default_factory=dict)  # space -> ids whose built row differs from applied
    left_out: Counter = field(default_factory=Counter)  # (table, owner label) -> changed rows left out
    spell_rows: list[dict] = field(default_factory=list)  # the built spell_dbc rows the run owns
    # Shared secondary rows a scope spell needs, as plain INSERTs (no DELETE): if another branch's rev has meanwhile
    # put a different row at the same id, db-import fails loudly instead of one branch overwriting the other.
    insert_blocks: list[str] = field(default_factory=list)


def _changed_ids(built: dict[int, dict], applied: dict[int, dict], ids) -> set[int]:
    out = set()
    for entry_id in ids:
        want, have = built.get(entry_id), applied.get(entry_id)
        if (want is None) != (have is None) or (want is not None and not resolve._rows_equal(want, have)):
            out.add(entry_id)
    return out


def scoped_dbc_blocks(blocks: list[tuple], own: Ownership, applied, secondary_names: dict) -> BlockResult:
    """Narrows the full run's reserved DBC blocks (`(table, id_range, rows, edited_ids, existing)`, before
    `_drop_unchanged_blocks`) to the selected scopes. `applied(table, watch)`: the table as db-import leaves it.
    `secondary_names`: `{DbcTable.name: ids.yaml name}` of the shared secondary tables (handled additively)."""
    result = BlockResult()
    spell_rows_mine: list[dict] = []
    primary = [b for b in blocks if b[0].name not in secondary_names]
    secondary = [b for b in blocks if b[0].name in secondary_names]
    for table, id_range, rows, edited_ids, _existing in primary:
        space = DBC_SPACES[table.name]
        built = {int(r[table.index_column]): r for r in rows}
        ranges = own.scope_ranges(space, id_range)
        block_ids = set(range(int(id_range["start"]), int(id_range["end"]) + 1)) - set(foreign_ids(id_range))
        considered = block_ids | set(built) | set(edited_ids)
        applied_rows = applied(table, considered)
        changed = _changed_ids(built, applied_rows, considered)
        result.changed[space] = changed
        mine_ids = set()
        for entry_id in considered:
            owners = own.owners(space, entry_id)
            if own.conflict(owners) and entry_id in changed:
                result.errors.append(f"{table.sql_table} {entry_id} is owned by {own.label(owners)}")
            if own.mine(owners):
                mine_ids.add(entry_id)
            elif entry_id in changed:
                result.left_out[(table.sql_table, own.label(owners))] += 1
        # Ids the narrowed range DELETE covers are re-inserted from `built`; the scope's ids outside those ranges are
        # explicit (DELETE ... IN + INSERT).
        in_scope_range = {i for i in considered if in_ranges(i, ranges)}
        explicit = sorted(i for i in (mine_ids - in_scope_range) if i in changed)
        scope_rows = [built[i] for i in sorted(built) if i in in_scope_range or i in explicit]
        if table.name == "Spell":
            spell_rows_mine = [built[i] for i in sorted(built) if i in mine_ids]
        if not (changed & (in_scope_range | set(explicit))):
            continue
        scoped_range = {
            "start": id_range["start"], "end": id_range["end"], "ranges": ranges,
            "foreign": id_range.get("foreign") or {},
        }
        result.blocks.append((table, scoped_range, scope_rows, explicit))
        result.notes.append(
            f"{table.sql_table}: ranges {_ranges_text(ranges) or 'none'}, {len(explicit)} explicit id(s), "
            f"{len(changed & (in_scope_range | set(explicit)))} changed row(s)"
        )
    result.spell_rows = spell_rows_mine
    # Shared secondary rows: only the ones a scope spell needs, only when db-import would not already have them.
    for table, id_range, rows, _edited, _existing in secondary:
        name = secondary_names[table.name]
        wanted = set()
        for row in spell_rows_mine:
            for column in SECONDARY_COLUMNS[name]:
                value = _norm(row.get(column))
                if isinstance(value, int) and id_range["start"] <= value <= id_range["end"]:
                    wanted.add(value)
        if not wanted:
            continue
        built = {int(r[table.index_column]): r for r in rows}
        applied_rows = applied(table, wanted)
        add = []
        for entry_id in sorted(wanted):
            want, have = built.get(entry_id), applied_rows.get(entry_id)
            if want is None:
                result.errors.append(f"{table.sql_table} {entry_id}: a scope spell names it but this run builds no row")
            elif have is None:
                add.append(entry_id)
            elif not resolve._rows_equal(want, have):
                result.errors.append(
                    f"{table.sql_table} {entry_id}: this run's row differs from the live / pending one (another "
                    f"checkout minted this id): merge that work first, or run a full generate.py"
                )
        if add:
            result.insert_blocks.append(sql_out.render_insert_block(table, [built[i] for i in add]))
            result.notes.append(f"{table.sql_table}: adding shared row(s) {add} a scope spell needs (plain INSERT)")
    return result


def _ranges_text(ranges: list[tuple[int, int]]) -> str:
    return ", ".join(f"{a}-{b}" if a != b else str(a) for a, b in ranges)


# ---------------------------------------------------------------------------------------------------------------------
# References: a scope row must not need another owner's row that is not live yet
# ---------------------------------------------------------------------------------------------------------------------

SPELL_EFFECT_SUMMON = 28


def reference_errors(scope_spell_rows: list[dict], own: Ownership, changed: dict[str, set[int]],
                     scoped_sql: str, full_sql_changed: dict[str, set[int]]) -> list[str]:
    """A scope's spell triggers (EffectTriggerSpell_N) or summons (SPELL_EFFECT_SUMMON's MiscValue) an id it does not
    own, whose row this run would write as new or changed (`changed` for the DBC spaces, `full_sql_changed` for the
    keyed tables of the full run): shipping the scope alone would point at a row that is not live. The same check
    covers the scope's `spell_linked_spell.spell_effect`, `creature_template_spell.Spell` and
    `instance_encounters.lastEncounterDungeon` rows (in `scoped_sql`)."""
    errors = []

    def check(where: str, space: str, entry_id) -> None:
        entry_id = _norm(entry_id)
        if not isinstance(entry_id, int) or entry_id <= 0:
            return
        owners = own.owners(space, entry_id)
        if own.mine(owners):
            return
        if entry_id in changed.get(space, set()) or entry_id in full_sql_changed.get(space, set()):
            errors.append(
                f"{where} needs {space} {entry_id} (owned by {own.label(owners)}), which is not live or pending yet: "
                f"ship it first (its own --scope, or a full run)"
            )

    for row in scope_spell_rows:
        for n in (1, 2, 3):
            check(f"spell {row['ID']}", "spell", row.get(f"EffectTriggerSpell_{n}"))
            if _norm(row.get(f"Effect_{n}")) == SPELL_EFFECT_SUMMON:
                check(f"spell {row['ID']}", "creature", row.get(f"EffectMiscValue_{n}"))
    for raw in split_statements(scoped_sql):
        if raw.startswith("--") or not raw.upper().startswith("INSERT"):
            continue
        stmt = parse_statement(raw)
        for _group, row in stmt.rows:
            if stmt.table == "spell_linked_spell":
                effect = _norm(row.get("spell_effect"))
                check(f"spell_linked_spell {row.get('spell_trigger')}", "spell",
                      abs(effect) if isinstance(effect, int) else effect)
            elif stmt.table == "creature_template_spell":
                check(f"creature_template_spell {row.get('CreatureID')}", "spell", row.get("Spell"))
            elif stmt.table == "instance_encounters":
                # A heroic final boss names its dungeon finder entry (lib/lfg_dungeons.py); ObjectMgr skips the whole
                # encounter row when that entry is not loaded, so it must be live first.
                check(f"instance_encounters {row.get('entry')}", "lfgdungeons", row.get("lastEncounterDungeon"))
    return list(dict.fromkeys(errors))


def inserted_ids(text: str) -> dict[str, set[int]]:
    """`{space: ids}` of every row `text` INSERTs, per TABLE_IDS: what a full run would write as new or changed."""
    out: dict[str, set[int]] = {}
    for raw in split_statements(text):
        if raw.startswith("--") or not raw.upper().startswith("INSERT"):
            continue
        try:
            stmt = parse_statement(raw)
        except ScopeError:
            continue
        mapping = TABLE_IDS.get(stmt.table)
        if not mapping:
            continue
        for _group, row in stmt.rows:
            value = _norm(row.get(mapping[0]))
            if isinstance(value, int):
                out.setdefault(mapping[1], set()).add(value)
    return out


# ---------------------------------------------------------------------------------------------------------------------
# Whole-file outputs: lock files, ItemSpellCopies.h, the client Lua tables
# ---------------------------------------------------------------------------------------------------------------------

def foreign_lock_lines(lines: list[str], line_owner) -> list[str]:
    """The appended lock lines (`lines`) whose owner (`line_owner(line) -> frozenset`) is not the run's."""
    return [line for line in lines if not line_owner(line)]


_COPY_LINE_RE = re.compile(r"^\s*\{ (\d+), (\d+), (\d+) \},")
_LABEL_LINE_RE = re.compile(r'^\s*\[(\d+)\] = "')
_SET_START_RE = re.compile(r"^    \[(\d+)\] = \{$")


def _entries(text: str, kind: str) -> tuple[dict[int, str], str]:
    """`({key: entry text}, the rest)` of a generated file: kind "copies" (ItemSpellCopies.h, keyed by copy spell id;
    the derived `kCopyCount` line is left out of the rest), "labels" (ItemTierLabels.lua, by item entry) or "sets"
    (ItemSetMembers.lua, by set id, one block per set)."""
    entries: dict[int, str] = {}
    rest: list[str] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if kind == "copies":
            m = _COPY_LINE_RE.match(line)
            if m:
                entries[int(m.group(1))] = line
            elif "kCopyCount" not in line:
                rest.append(line)
        elif kind == "labels":
            m = _LABEL_LINE_RE.match(line)
            if m:
                entries[int(m.group(1))] = line
            else:
                rest.append(line)
        else:
            m = _SET_START_RE.match(line)
            if m:
                block = [line]
                i += 1
                while i < len(lines) and lines[i] != "    },":
                    block.append(lines[i])
                    i += 1
                if i < len(lines):
                    block.append(lines[i])
                entries[int(m.group(1))] = "\n".join(block)
            else:
                rest.append(line)
        i += 1
    return entries, "\n".join(rest)


FILE_SPACES = {"copies": "spell", "labels": "item", "sets": "item_set"}


def foreign_file_changes(old_text: str | None, new_text: str, kind: str, own: Ownership) -> list[str]:
    """Why a scoped run may not write a whole-file output: the entries whose text changes but the run does not own,
    or a change outside the entries. Empty: every change is the run's (writing the full text is writing its part)."""
    if old_text is None:
        old_text = ""
    if old_text == new_text:
        return []
    old_entries, old_rest = _entries(old_text, kind)
    new_entries, new_rest = _entries(new_text, kind)
    problems = []
    if old_text and old_rest != new_rest:
        problems.append("its fixed text (not one entry) changes")
    space = FILE_SPACES[kind]
    foreign = []
    for key in sorted(old_entries.keys() | new_entries.keys()):
        if old_entries.get(key) == new_entries.get(key):
            continue
        owners = own.owners(space, key)
        if not own.mine(owners):
            foreign.append(f"{key} ({own.label(owners)})")
    if foreign:
        shown = ", ".join(foreign[:12]) + (" ..." if len(foreign) > 12 else "")
        problems.append(f"{len(foreign)} entr(ies) of other owners change: {shown}")
    return problems


# ---------------------------------------------------------------------------------------------------------------------
# Client: repack the deployed patch-Z with the scope's rows
# ---------------------------------------------------------------------------------------------------------------------

def read_dbc_bytes(blob: bytes, table) -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="dbc-scope-") as tmp:
        path = Path(tmp) / table.dbc_filename
        path.write_bytes(blob)
        return dbcfile.read_dbc(path, table)


@dataclass
class ClientResult:
    replacements: dict[str, bytes] = field(default_factory=dict)  # archive member name -> new bytes
    loose: dict[str, bytes] = field(default_factory=dict)  # DBC file name -> new bytes
    notes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def scoped_client_files(
    base_members: dict[str, bytes], full_files: dict[str, bytes], tables: dict, own: Ownership, stock_rows: dict,
    secondary_names: dict, ids_cfg: dict,
) -> ClientResult:
    """The patch-Z members a scoped run replaces. `full_files`: `{DBC file name: bytes}` the full run would ship;
    `tables`: `{DBC file name: DbcTable}`; `stock_rows`: `{DBC file name: stock rows}` (the base when the deployed
    archive lacks the file, and the physical order `pack_client_dbc` keeps). Every row the run does not own stays as
    deployed; the run's ids take the full build's row or go."""
    out = ClientResult()
    by_name = {name.replace("\\", "/").split("/")[-1].lower(): name for name in base_members}
    full_rows: dict[str, dict[int, dict]] = {}
    for filename, blob in full_files.items():
        table = tables[filename]
        full_rows[filename] = {int(r[table.index_column]): r for r in read_dbc_bytes(blob, table)}
    spell_ids_mine: list[dict] = []
    order = sorted(full_files, key=lambda f: tables[f].name in secondary_names)  # secondaries last (need the spells)
    for filename in order:
        table = tables[filename]
        member = by_name.get(filename.lower())
        base_blob = base_members.get(member) if member else None
        base_list = read_dbc_bytes(base_blob, table) if base_blob is not None else list(stock_rows.get(filename, []))
        base = {int(r[table.index_column]): r for r in base_list}
        full = full_rows[filename]
        merged = dict(base)
        if table.name in secondary_names:
            name = secondary_names[table.name]
            block = ids_cfg[name]
            wanted = set()
            for row in spell_ids_mine:
                for column in SECONDARY_COLUMNS[name]:
                    value = _norm(row.get(column))
                    if isinstance(value, int) and block["start"] <= value <= block["end"]:
                        wanted.add(value)
            for entry_id in sorted(wanted):
                want, have = full.get(entry_id), base.get(entry_id)
                if want is None:
                    continue
                if have is None:
                    merged[entry_id] = want
                elif have != want:
                    out.errors.append(
                        f"{filename} {entry_id}: the base archive holds a different row at this id (another checkout "
                        f"minted it): merge that work first, or run a full generate.py"
                    )
        else:
            space = DBC_SPACES.get(table.name)
            if space is None:
                if base_blob is None or base_list != list(full.values()):
                    out.notes.append(f"{filename}: no owner map for this table, left as deployed")
                continue
            for entry_id in set(base) | set(full):
                owners = own.owners(space, entry_id)
                if not own.mine(owners):
                    continue
                if entry_id in full:
                    merged[entry_id] = full[entry_id]
                else:
                    merged.pop(entry_id, None)
            if table.name == "Spell":
                spell_ids_mine = [merged[i] for i in merged if own.mine(own.owners("spell", i))]
        changed = sorted(i for i in set(merged) | set(base) if merged.get(i) != base.get(i))
        if not changed:
            continue
        blob = dbcfile.pack_client_dbc(table, list(merged.values()), list(stock_rows.get(filename, base_list)))
        out.replacements[member or f"DBFilesClient\\{filename}"] = blob
        out.loose[filename] = blob
        out.notes.append(f"{filename}: {len(changed)} row(s) of this scope replaced, every other row as in the base")
    return out
