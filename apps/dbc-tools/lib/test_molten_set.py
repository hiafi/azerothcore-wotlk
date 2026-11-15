"""
The Molten dungeon set family: source/items/molten_set.py, source/items/molten_set_bonuses.py,
source/npcs/molten_set/vendors.py and the scripts in modules/mod-dungeon-bosses (src/DungeonSets/
molten_set_bonuses.cpp, MoltenSetLogic.h).

Checks:
  - the pieces: 10 sets of 8 on the dungeon ladder, the stock Tier 0.5 entries of the 8 kept sets as base= under their
    item_ids.lock key (qr_<entry>), Deathmist (518) left out, the two new tank sets minted with their own itemset; the
    Normal tier at Haunted's Tier 0 level of the slot, Rare, required level 5 below; the stats per slot and archetype
    (primary, the family's secondaries, the tank swaps, Leather Tank's extra Stamina); sockets (1, the head meta plus
    1; red, blue on tanks) and the socket bonus of the first secondary; Bind on Pickup;
  - the sets: one item_set() per set, 8 pieces, a 3 and a 5 piece bonus from the `molten_set` reservation;
  - the tokens: 8 slots, entries 70540 + 5 * slot + tier and costs 3040 + 5 * slot + tier on the dungeon ladder, every
    armor slot bought by exactly one token;
  - the vendors: 16 creatures in the `molten_set` creature slice (vendor flag, friendly to all), every set and tier
    sold by exactly one vendor of its own armor type;
  - the bonus spells: ids in the reservation and mirrored by MoltenSetLogic.h, every scripted_by() name registered by
    molten_set_bonuses.cpp, the tooltip literals and Heat counts equal to the C++ numbers, the Cooldown Haste list
    equal to Player.cpp's, the Heat buffs (count, 30 s, leave combat, number-free), the proc rows (Heat at 100%, never
    a chance), damage and heals on potency, payouts suppress caster procs.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_molten_set.py
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import test_id_blocks as id_blocks  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.dsl.items import Quality, Socket  # noqa: E402
from lib.dsl.sets import ItemSetDecl, SetTokenDecl, SetVendorDecl  # noqa: E402
from lib.test_hard_mode_item_effects import _load_items_registry  # noqa: E402

SOURCE = TOOL_ROOT / "source" / "items" / "molten_set.py"
BONUS_SOURCE = TOOL_ROOT / "source" / "items" / "molten_set_bonuses.py"
NPC_DIR = TOOL_ROOT / "source" / "npcs" / "molten_set"
MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "DungeonSets"
HEADER = MODULE_DIR / "MoltenSetLogic.h"
SCRIPT = MODULE_DIR / "molten_set_bonuses.cpp"
PLAYER_CPP = REPO_ROOT / "src" / "server" / "game" / "Entities" / "Player" / "Player.cpp"
RESERVATION = range(206900, 207000)
CREATURES = range(300670, 300700)

SLOTS = ("head", "shoulders", "chest", "hands", "waist", "legs", "feet", "wrist")
INVENTORY = {"head": {1}, "shoulders": {3}, "chest": {5, 20}, "hands": {10}, "waist": {6}, "legs": {7}, "feet": {8},
             "wrist": {9}}
TIER0_ILVL = {"head": 62, "shoulders": 60, "chest": 63, "hands": 59, "waist": 58, "legs": 61, "feet": 59, "wrist": 57}
# set id: (primary, kind, stock entries in slot order)
STOCK_SETS = {
    517: ("Intellect (Solo)", "dps", (22065, 22068, 22069, 22066, 22062, 22067, 22064, 22063)),
    514: ("Spirit (Solo)", "dps", (22080, 22082, 22083, 22081, 22078, 22085, 22084, 22079)),
    512: ("Agility (Solo)", "dps", (22005, 22008, 22009, 22006, 22002, 22007, 22003, 22004)),
    513: ("Spirit (Solo)", "dps", (22109, 22112, 22113, 22110, 22106, 22111, 22107, 22108)),
    515: ("Agility (Solo)", "dps", (22013, 22016, 22060, 22015, 22010, 22017, 22061, 22011)),
    519: ("Intellect (Solo)", "dps", (22097, 22101, 22102, 22099, 22098, 22100, 22096, 22095)),
    516: ("Intellect (Solo)", "dps", (22091, 22093, 22089, 22090, 22086, 22092, 22087, 22088)),
    511: ("Strength (Solo)", "dps", (21999, 22001, 21997, 21998, 21994, 22000, 21995, 21996)),
}
NEW_SETS = {1002: ("guardians", "Agility (Solo)", "leather_tank"), 1003: ("impenetrable", "Strength (Solo)",
                                                                          "plate_tank")}
DEATHMIST = range(22070, 22078)
ARMOR_SETS = {"Cloth": {517, 514}, "Leather": {512, 513, 1002}, "Mail": {515, 519}, "Plate": {511, 516, 1003}}
TIER_SPLIT = (("normal", "heroic"), ("empowered_1",), ("empowered_2",), ("empowered_3",))
TIER_NAMES = ("Normal & Heroic", "Molten Empowered", "Draconic Empowered", "Chthonic Empowered")
VENDOR_ENTRIES = {}
for _n, _armor in enumerate(ARMOR_SETS):
    VENDOR_ENTRIES[(_armor, TIER_SPLIT[0])] = 300670 + _n
    for _k, _tiers in enumerate(TIER_SPLIT[1:]):
        VENDOR_ENTRIES[(_armor, _tiers)] = 300674 + 3 * _n + _k
# The ten sets in MoltenSetLogic.h's Archetype order (set k owns 206900 + 10k).
ARCHETYPE_ORDER = (517, 514, 513, 519, 516, 511, 515, 512, 1002, 1003)
COOLDOWN_HOOKS = {206901, 206931, 206951, 206991}

SCHOOL_DAMAGE, APPLY_AURA, HEAL, HEAL_PCT = 2, 6, 10, 136
SUPPRESS_CASTER_PROCS = 0x00010000
LEAVE_COMBAT = 0x80000000
PROC_SPELL_PHASE_CAST = 0x1
PROC_SPELL_PHASE_HIT = 0x2


def secondary(kind: str, slot: str) -> str:
    big = slot in ("head", "shoulders", "chest", "legs")
    if kind == "plate_tank":
        return "Block/Versatility" if big else "Block/CDH"
    if kind == "leather_tank":
        return "Dodge/Versatility" if big else "Dodge/CDH"
    return "Crit/Versatility" if big else ("Crit/CDH" if slot in ("hands", "wrist") else "CDH/Versatility")


def piece_keys(set_id: int) -> tuple[str, ...]:
    if set_id in STOCK_SETS:
        return tuple(f"qr_{entry}" for entry in STOCK_SETS[set_id][2])
    return tuple(f"molten_{NEW_SETS[set_id][0]}_{slot}" for slot in SLOTS)


@unittest.skipUnless(SOURCE.is_file() and BONUS_SOURCE.is_file() and NPC_DIR.is_dir(),
                     "the Molten source files (source/items/molten_set*.py, source/npcs/molten_set/) are missing")
class MoltenSetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load_items_registry()
        keys = {k for s in (*STOCK_SETS, *NEW_SETS) for k in piece_keys(s)}
        cls.items = {e["id"]: e["_decl"] for e in cls.reg.item_declarations if e["id"] in keys}
        decls = [e["_decl"] for e in cls.reg.item_set_declarations]
        set_ids = set(STOCK_SETS) | set(NEW_SETS)
        cls.sets = {d.set_id: d for d in decls if isinstance(d, ItemSetDecl) and d.set_id in set_ids}
        cls.tokens = {d.key: d for d in decls if isinstance(d, SetTokenDecl) and d.key.startswith("molten_")}
        cls.vendors = {d.entry: d for d in decls if isinstance(d, SetVendorDecl) and d.entry in CREATURES}
        cls.spells = {int(e["id"]): e for e in cls.reg.spells if int(e["id"]) in RESERVATION}
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.bonus_source = BONUS_SOURCE.read_text(encoding="utf-8")
        t = id_blocks
        cls.npcs = registry.load_class_package(
            NPC_DIR, ids_cfg=t.IDS, trainer_index=t._AnyTrainer(), existing_group_ids=t._AnySet(),
            shapeshift_index={}, existing_creature_rows=t._AnyRows(),
            creature_columns=t.spell_tables.CREATURE_TEMPLATE_COLUMNS,
            creature_defaults=t.spell_tables.CREATURE_TEMPLATE_DEFAULTS,
        )

    # --- the pieces --------------------------------------------------------------------------------------------------

    def test_pieces(self):
        self.assertEqual(len(self.items), 80)
        for set_id, (primary, kind, bases) in STOCK_SETS.items():
            for slot, base in zip(SLOTS, bases):
                decl = self.items[f"qr_{base}"]
                ilvl = TIER0_ILVL[slot]
                self.assertEqual((decl.base, decl.primary, decl.secondary), (base, primary, secondary(kind, slot)))
                self.assertEqual((decl.ilvl, decl.quality, decl.required_level), (ilvl, Quality.RARE, ilvl - 5))
                self.assertEqual(dict(decl.columns), {"bonding": 1}, decl.key)  # the stock row's itemset stays
                self.assertEqual(decl.extra_stamina, 0.0)
        for set_id, (prefix, primary, kind) in NEW_SETS.items():
            for slot in SLOTS:
                decl = self.items[f"molten_{prefix}_{slot}"]
                ilvl = TIER0_ILVL[slot]
                self.assertIsNone(decl.base)
                self.assertEqual((decl.primary, decl.secondary), (primary, secondary(kind, slot)))
                self.assertEqual((decl.ilvl, decl.quality, decl.required_level), (ilvl, Quality.RARE, ilvl - 5))
                self.assertEqual(dict(decl.columns), {"bonding": 1, "itemset": set_id})
                self.assertEqual(decl.extra_stamina, 0.25 if kind == "leather_tank" else 0.0)
        self.assertFalse({d.base for d in self.items.values()} & set(DEATHMIST))  # Deathmist retires
        for decl in self.items.values():
            self.assertEqual(decl.ladder.name, "vanilla_dungeon")
            self.assertEqual([t.name for t in decl.ladder.tiers if not t.deferred],
                             ["normal", "heroic", "empowered_1", "empowered_2", "empowered_3"])

    def test_normal_below_heroic(self):
        # The Normal tier sits under Heroic 66 (two families at the same item level as Haunted's Tier 0).
        for decl in self.items.values():
            self.assertLess(decl.ilvl, 66, decl.key)

    def test_sockets(self):
        bonus = {"Crit": 2874, "CDH": 2874, "Block": 2972, "Dodge": 2871}
        heads = {piece_keys(s)[0] for s in (*STOCK_SETS, *NEW_SETS)}
        for key, decl in self.items.items():
            tank = decl.secondary.startswith(("Block", "Dodge"))
            first = Socket.BLUE if tank else Socket.RED
            expected = (Socket.META, first) if key in heads else (first,)
            self.assertEqual(decl.sockets, expected, key)
            self.assertEqual(decl.socket_bonus, bonus[decl.secondary.split("/")[0]], key)
            self.assertFalse(decl.ladder.tiers[0].sockets)  # Normal: none (user 2026-11-06)

    # --- the sets ----------------------------------------------------------------------------------------------------

    def test_sets(self):
        self.assertEqual(set(self.sets), set(STOCK_SETS) | set(NEW_SETS))
        for set_id, decl in self.sets.items():
            self.assertEqual(decl.items, piece_keys(set_id))
            self.assertEqual([t for t, _ in decl.bonuses], [3, 5])
            index = ARCHETYPE_ORDER.index(set_id)
            self.assertEqual([s for _, s in decl.bonuses], [206900 + 10 * index, 206901 + 10 * index])
            for _, spell_id in decl.bonuses:
                self.assertIn(spell_id, self.spells)
            self.assertEqual(decl.name is None, set_id in STOCK_SETS)
        self.assertEqual(self.sets[1002].name, "Guardian's Armor")
        self.assertEqual(self.sets[1003].name, "Impenetrable Battlegear")

    # --- the tokens --------------------------------------------------------------------------------------------------

    def test_tokens(self):
        self.assertEqual(len(self.tokens), 8)
        covered = set()
        for index, slot in enumerate(SLOTS):
            token = self.tokens[f"molten_token_{slot}"]
            self.assertEqual(set(token.slots), INVENTORY[slot])
            covered |= set(token.slots)
            self.assertTrue(token.name.startswith("Molten "))
            self.assertIn(token.like, range(22349, 22373))  # the Desecrated tokens' looks
            self.assertEqual((token.ilvl, token.quality, token.required_level), (60, Quality.RARE, 0))
            self.assertEqual(token.ladder.name, "vanilla_dungeon")
            for tier_index, (tier, entry) in enumerate(token.entries):
                self.assertEqual(entry, 70540 + 5 * index + tier_index)
                self.assertEqual(token.cost(tier), 3040 + 5 * index + tier_index)
            self.assertNotIn('"', token.description)
        self.assertEqual(covered, {1, 3, 5, 20, 6, 7, 8, 9, 10})
        # Molten's token looks differ from Haunted's.
        haunted = {d.like for e in self.reg.item_set_declarations for d in [e["_decl"]]
                   if isinstance(d, SetTokenDecl) and d.key.startswith("haunted_")}
        self.assertFalse(haunted & {t.like for t in self.tokens.values()})

    # --- the vendors -------------------------------------------------------------------------------------------------

    def test_vendors(self):
        self.assertEqual(set(self.vendors), set(VENDOR_ENTRIES.values()))
        sold = {}
        creatures = {int(r["entry"]): r for r in self.npcs.creature_templates}
        for (armor, tiers), entry in VENDOR_ENTRIES.items():
            vendor = self.vendors[entry]
            self.assertEqual((set(vendor.sets), vendor.tiers), (ARMOR_SETS[armor], tiers), entry)
            self.assertEqual(set(vendor.tokens), set(self.tokens))
            for set_id in vendor.sets:
                for tier in tiers:
                    self.assertNotIn((set_id, tier), sold)  # one vendor per set and tier
                    sold[(set_id, tier)] = entry
            self.assertEqual(creatures[entry]["subname"], f"Molten {armor} - {TIER_NAMES[TIER_SPLIT.index(tiers)]}")
        tiers = ("normal", "heroic", "empowered_1", "empowered_2", "empowered_3")
        self.assertEqual(set(sold), {(s, t) for s in self.sets for t in tiers})  # every set and tier is sold
        self.assertEqual(set(creatures), set(VENDOR_ENTRIES.values()))
        for entry, row in creatures.items():
            self.assertIn(entry, CREATURES)
            # Faction 35: friendly to the Alliance (Ironforge) and the Horde (Orgrimmar) alike.
            self.assertEqual((int(row["npcflag"]), int(row["faction"]), row["AIName"], row["ScriptName"]),
                             (128, 35, "", ""))
        self.assertEqual({int(r["CreatureID"]) for r in self.npcs.creature_template_models}, set(creatures))

    # --- the bonus spells --------------------------------------------------------------------------------------------

    def header_ids(self) -> dict[str, int]:
        return {m.group(1): int(m.group(2)) for m in re.finditer(r"(SPELL_[A-Z_]+)\s*=\s*(\d+),", self.header)}

    def header_list(self, name: str) -> list[int]:
        match = re.search(rf"{name}\[\w*\]\s*=\s*\{{([^}}]*)\}}", self.header)
        self.assertIsNotNone(match, name)
        return [int(v) for v in re.findall(r"\d+", match.group(1))]

    def test_ids_mirrored_by_the_header(self):
        ids = self.header_ids()
        self.assertEqual(set(ids.values()), set(self.spells))
        self.assertEqual(len(ids), len(self.spells))

    def test_script_bindings(self):
        registered = set(re.findall(r"RegisterSpellScript\((\w+)\)", self.script))
        bound = {r["ScriptName"] for r in self.reg.spell_script_names if int(r["spell_id"]) in RESERVATION}
        self.assertEqual(bound, registered)
        heat = {int(r["spell_id"]) for r in self.reg.spell_script_names if r["ScriptName"] == "spell_molten_heat"}
        self.assertEqual(heat, {206900 + 10 * k for k in range(10)})
        hooks = {int(r["spell_id"]) for r in self.reg.spell_script_names
                 if r["ScriptName"] == "spell_molten_cooldown_heat"}
        self.assertEqual(hooks, COOLDOWN_HOOKS)

    def test_script_numbers_match_the_tooltips(self):
        B = type("Bonuses", (), {m.group(1): int(m.group(2)) for m in re.finditer(r"^([A-Z_]+) = (\d+)$",
                                                                                  self.bonus_source, re.MULTILINE)})

        def const(name: str) -> float:
            match = re.search(rf"{name}\s*=\s*([\d.]+)f?;", self.header)
            self.assertIsNotNone(match, name)
            return float(match.group(1))

        pairs = {
            "kCritHeat": B.CRIT_HEAT, "kCauterizeExtraAllies": B.CAUTERIZE_EXTRA_ALLIES,
            "kCauterizeRadius": B.CAUTERIZE_RADIUS, "kMendingFlameHealthPct": B.MENDING_FLAME_HEALTH_PCT,
            "kMendingFlameBonusPct": B.MENDING_FLAME_BONUS_PCT, "kEmberBloomTicks": B.EMBER_BLOOM_TICKS,
            "kMoltenThunderRadius": B.MOLTEN_THUNDER_RADIUS,
            "kMoltenThunderExtraAllies": B.MOLTEN_THUNDER_EXTRA_ALLIES, "kThunderheadHeat": B.THUNDERHEAD_HEAT,
            "kStokeTheForgeHeat": B.STOKE_THE_FORGE_HEAT, "kBankedCoalsHeat": B.BANKED_COALS_HEAT,
            "kObsidianShardBounceRadius": B.OBSIDIAN_SHARD_BOUNCE_RADIUS,
            "kRekindleComboPoints": B.REKINDLE_COMBO_POINTS, "kCooldownHookMinMs": B.COOLDOWN_HOOK_MIN_S * 1000,
        }
        for name, value in pairs.items():
            self.assertEqual(const(name), float(value), name)
        counts = (B.STOKED_FLAME_HEAT, B.CAUTERIZE_HEAT, B.EMBER_BLOOM_HEAT, B.MOLTEN_THUNDER_HEAT,
                  B.HALLOWED_FLAME_HEAT, B.MOLTEN_EDGE_HEAT, B.OBSIDIAN_SHARD_HEAT, B.SLAG_BURST_HEAT,
                  B.SCORCHING_HIDE_HEAT, B.MOLTEN_PLATE_HEAT)
        self.assertEqual(tuple(self.header_list("kHeatCount")), counts)
        # The doc's counts: 10, 8, 8, 10, 8, 10, 8, 10, 10, 10.
        self.assertEqual(counts, (10, 8, 8, 10, 8, 10, 8, 10, 10, 10))
        # Every 3 piece tooltip names its count and defines Heat.
        for k, count in enumerate(counts):
            desc = self.spells[206900 + 10 * k]["raw_overrides"]["Description_Lang_enUS"]
            self.assertIn(f"At {count} Heat", desc, 206900 + 10 * k)
            self.assertIn("Heat lasts 30 sec", desc)
            self.assertIn("2 when they critically" if k != 7 else "1 more when they critically", desc)

    def test_cooldown_haste_list_matches_player_cpp(self):
        source = PLAYER_CPP.read_text(encoding="utf-8")

        def array(name: str) -> list[int]:
            match = re.search(rf"{name}\s*=\s*\{{([^}}]*)\}}", source)
            self.assertIsNotNone(match, name)
            return [int(v) for v in re.findall(r"\d+", match.group(1))]

        self.assertEqual(self.header_list("kCooldownHasteAllowList"), array("CUSTOM_COOLDOWN_HASTE_ALLOW_LIST"))
        self.assertEqual(self.header_list("kCooldownHasteDenyList"), array("CUSTOM_COOLDOWN_HASTE_DENY_LIST"))
        minimum = re.search(r"CUSTOM_COOLDOWN_HASTE_MIN_BASE_COOLDOWN_MS\s*=\s*(\d+)\s*\*\s*IN_MILLISECONDS", source)
        self.assertIsNotNone(minimum)
        self.assertEqual(int(minimum.group(1)) * 1000, 30000)

    def test_heat_buffs(self):
        counts = self.header_list("kHeatCount")
        for k in range(10):
            heat = self.spells[206902 + 10 * k]
            raw = heat["raw_overrides"]
            self.assertEqual(heat["name"], "Heat")
            self.assertEqual(int(raw["CumulativeAura"]), counts[k])
            self.assertEqual(int(heat["duration_ms"]), 30000)
            self.assertEqual(int(raw["AuraInterruptFlags"]) & LEAVE_COMBAT, LEAVE_COMBAT)
            self.assertFalse(int(heat["attributes"]) & 0x40)  # visible: not passive
            self.assertEqual(raw["Description_Lang_enUS"], "Heat: building toward an eruption.")
            self.assertNotRegex(raw["AuraDescription_Lang_enUS"], r"[\d$]")  # number-free

    def test_proc_rows(self):
        procs = {int(r["SpellId"]): r for r in self.reg.spell_procs if int(r["SpellId"]) in RESERVATION}
        threes = {206900 + 10 * k for k in range(10)}
        self.assertEqual(set(procs), threes | COOLDOWN_HOOKS | {206923, 206924, 206974})
        for spell_id, row in procs.items():
            # Heat is a count: every row is 100% with no internal cooldown, so Proc Chance never changes it.
            self.assertEqual((row["Chance"], row["Cooldown"], row["ProcsPerMinute"]), (100.0, 0, 0.0), spell_id)
            if row["SpellPhaseMask"] == PROC_SPELL_PHASE_CAST:
                self.assertEqual(row["HitMask"], 0, spell_id)  # a cast phase has no outcome yet
        for spell_id in threes:
            self.assertEqual(procs[spell_id]["SpellPhaseMask"], PROC_SPELL_PHASE_HIT)  # the crit is known there
        for spell_id in COOLDOWN_HOOKS:
            self.assertEqual(procs[spell_id]["SpellPhaseMask"], PROC_SPELL_PHASE_CAST)
        for spell_id in (206923, 206924, 206974):
            self.assertEqual(procs[spell_id]["Charges"], 1)
        self.assertTrue(procs[206900]["ProcFlags"] & 0x40000)  # Stoked Flame counts periodic crits

    def test_damage_and_heals_on_potency(self):
        for spell_id, spell in self.spells.items():
            raw = spell["raw_overrides"]
            self.assertEqual(raw["EquippedItemClass"], -1, spell_id)
            self.assertNotIn("{pot", raw["Description_Lang_enUS"], spell_id)
            self.assertNotRegex(raw.get("AuraDescription_Lang_enUS", ""), r"\$", spell_id)
            for n in (1, 2, 3):
                effect = spell.get(f"effect{n}")
                if not effect:
                    continue
                damage_or_heal = effect["type"] in (SCHOOL_DAMAGE, HEAL, HEAL_PCT) or (
                    effect["type"] == APPLY_AURA and effect["apply_aura"] in (3, 8, 20, 69))
                if not damage_or_heal:
                    continue
                self.assertTrue(effect.get("_potency"), spell_id)
                self.assertNotEqual(int(raw["DefenseType"]), 0, spell_id)

    def test_payouts_suppress_caster_procs(self):
        bonuses = {s for d in self.sets.values() for _, s in d.bonuses}
        for spell_id, spell in self.spells.items():
            raw = spell["raw_overrides"]
            if spell_id in bonuses:
                self.assertTrue(int(spell["attributes"]) & 0x40, spell_id)  # passive
                continue
            self.assertTrue(int(raw.get("AttributesEx3", 0)) & SUPPRESS_CASTER_PROCS, spell_id)

    def test_shapes(self):
        # The ranged payouts scale with ranged attack power.
        for spell_id in (206964, 206966):
            self.assertEqual(self.spells[spell_id]["raw_overrides"]["DefenseType"], 3)
        self.assertEqual(self.spells[206963]["raw_overrides"]["DefenseType"], 2)
        # Area eruptions: at the target (dest + area), Scorching Hide around the wearer.
        for spell_id, radius in ((206903, 8.0), (206933, 8.0), (206973, 5.0)):
            effect = self.spells[spell_id]["effect1"]
            self.assertEqual((effect["implicit_target_a"], effect["implicit_target_b"]), (53, 16), spell_id)
            self.assertEqual(effect["radius_yards"], radius)
        self.assertEqual((self.spells[206983]["effect1"]["implicit_target_a"],
                          self.spells[206983]["effect1"]["implicit_target_b"]), (22, 15))
        threat = {int(r["entry"]): r for r in self.reg.spell_threats if int(r["entry"]) in RESERVATION}
        self.assertEqual(set(threat), {206983})
        self.assertGreater(threat[206983]["pctMod"], 1.0)  # "with high threat"
        # Buffs: Fanned Embers +30%, Tempered Hide -5%, Molten Plate +10% armor.
        self.assertEqual(self.spells[206924]["effect1"]["base_points"] + 1, 30)
        self.assertEqual(self.spells[206984]["effect1"]["base_points"] + 1, -5)
        self.assertEqual((self.spells[206993]["effect1"]["apply_aura"], self.spells[206993]["effect1"]["misc_value"],
                          self.spells[206993]["effect1"]["base_points"] + 1), (101, 1, 10))
        for spell_id in (206943, 206944, 206953, 206965, 206966):
            spell = self.spells[spell_id]
            self.assertEqual((spell["duration_ms"], spell["effect1"]["amplitude"]), (6000, 2000), spell_id)

    def test_haunting_mark_ignores_the_molten_payouts(self):
        # HauntedSetUnitHooks::ModifySpellDamageTaken skips the Haunted slice by id; a Molten payout (Obsidian Shard is
        # melee or ranged class) must be skipped too, or it would consume a Beaststalker's Haunting Mark.
        haunted = (MODULE_DIR / "haunted_set_bonuses.cpp").read_text(encoding="utf-8")
        self.assertIn('#include "MoltenSetLogic.h"', haunted)
        hook = haunted.split("void ModifySpellDamageTaken(", 1)[1].split("void OnSpellDamageTakenFinal(", 1)[0]
        self.assertIn("kSpellsHauntedSet.Contains(spellInfo->Id)", hook)
        self.assertIn("MoltenSet::kSpellsMoltenSet.Contains(spellInfo->Id)", hook)


if __name__ == "__main__":
    unittest.main()
