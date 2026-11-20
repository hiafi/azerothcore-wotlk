"""
The Zealot's dungeon set family: source/items/zealot_set.py, source/items/zealot_set_bonuses.py, source/items/ladders.py
VANILLA_HEROIC_SET, source/npcs/zealot_set/vendors.py, the scripts in modules/mod-dungeon-bosses (src/DungeonSets/
zealot_set_bonuses.cpp, ZealotSetLogic.h) and the spawn SQL (data/sql/updates/pending_db_world/rev_zealot_set.sql).

Checks:
  - the ladder: VANILLA_DUNGEON's Heroic and empowered tiers (steps 1-4, levels, flag, labels), no Normal tier;
  - the pieces: 10 sets of 3 (head, shoulders, chest) per the hub's Sets table, all new on the heroic-only ladder
    (the seven reused stock pieces as copies: stock name, `like=` the stock entry), the type changes, Bind on Pickup,
    every tier in its set; the stats (primary, Haste / Versatility / Cooldown Haste by slot, the tank swaps, Leather
    Tank's extra Stamina); sockets (1, the head a meta plus 1; red, blue on tanks) and the socket bonus; every shape
    stat materialized on every tier (when the shapes are live);
  - the sets: ItemSet 1004-1013, the doc's names, a 2 piece Fervor of the archetype's role and the 3 piece;
  - the tokens: 3 slots, entries 70580 + 4 * slot + tier and costs 3080 + 4 * slot + tier, every token slot bought;
  - the vendors: 4 creatures, one tier each, every set and tier sold once, faction 35; the hound look;
  - the bonus spells: ids in the reservation and mirrored by ZealotSetLogic.h, every scripted_by() name registered,
    the tooltip literals equal to the C++ numbers, the trigger rows (100%, the 60 s cooldown, the flags of the trigger
    kind), damage on potency, the percent heals excluded, payouts suppress caster procs, the Fervor values, no
    "Martyrdom" in a tooltip;
  - the spawn SQL: the four vendors on map 0, guids in the hand block.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_zealot_set.py
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
from lib.test_hard_mode_item_effects import _load_items_registry, assert_shape_stats_on_every_tier  # noqa: E402

SOURCE = TOOL_ROOT / "source" / "items" / "zealot_set.py"
BONUS_SOURCE = TOOL_ROOT / "source" / "items" / "zealot_set_bonuses.py"
NPC_DIR = TOOL_ROOT / "source" / "npcs" / "zealot_set"
MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "DungeonSets"
HEADER = MODULE_DIR / "ZealotSetLogic.h"
SCRIPT = MODULE_DIR / "zealot_set_bonuses.cpp"
SPAWNS = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_zealot_set.sql"
RESERVATION = range(212100, 212300)
CREATURES = range(300890, 300900)

SLOTS = ("head", "shoulders", "chest")
INVENTORY = {"head": {1}, "shoulders": {3}, "chest": {5, 20}}
TIERS = ("heroic", "empowered_1", "empowered_2", "empowered_3")
# The hub's Sets table (ruling 57), in its order: ItemSet id, key prefix, set name, primary, kind, role, pieces
# ({slot: (name, like)}).
SETS = (
    (1004, "scarlet_champion", "Battlegear of the Scarlet Champion", "Strength (Solo)", "dps", "damage",
     {"head": ("Raging Berserker's Helm", 7719), "shoulders": ("Herod's Shoulder", 7718),
      "chest": ("Herod's Breastplate", None)}),
    (1005, "last_stand", "Bulwark of the Last Stand", "Strength (Solo)", "plate_tank", "tank",
     {"head": ("Last Stand Helm", None), "shoulders": ("Last Stand Pauldrons", None),
      "chest": ("Last Stand Breastplate", None)}),
    (1006, "vigil", "Vigil of the Fallen Champion", "Intellect (Solo)", "dps", "hybrid",
     {"head": ("Vigilant Helm", None), "shoulders": ("Vigilant Pauldrons", None),
      "chest": ("Vigilant Breastplate", None)}),
    (1007, "houndmaster", "Houndmaster's Harness", "Agility (Solo)", "dps", "damage",
     {"head": ("Houndmaster's Coif", None), "shoulders": ("Houndmaster's Mantle", None),
      "chest": ("Houndmaster's Hauberk", None)}),
    (1008, "curator", "Curator's Regalia", "Intellect (Solo)", "dps", "hybrid",
     {"head": ("Curator's Coif", None), "shoulders": ("Curator's Mantle", None), "chest": ("Curator's Hauberk", None)}),
    (1009, "interrogator", "Interrogator's Garb", "Agility (Solo)", "dps", "damage",
     {"head": ("Interrogator's Hood", None), "shoulders": ("Interrogator's Mantle", None),
      "chest": ("Interrogator's Jerkin", None)}),
    (1010, "ironspine", "Ironspine's Bones", "Agility (Solo)", "leather_tank", "tank",
     {"head": ("Ironspine's Skull", None), "shoulders": ("Ironspine's Shoulderblades", None),
      "chest": ("Ironspine's Ribcage", 7688)}),
    (1011, "gardener", "Gardener's Vestments", "Spirit (Solo)", "dps", "hybrid",
     {"head": ("Gardener's Hat", None), "shoulders": ("Gardener's Mantle", None), "chest": ("Gardener's Smock", None)}),
    (1012, "arcanist", "Regalia of the Arcanist", "Intellect (Solo)", "dps", "damage",
     {"head": ("Doan's Cowl", None), "shoulders": ("Mantle of Doan", 7712), "chest": ("Robe of Doan", 7711)}),
    (1013, "high_inquisitor", "Vestments of the High Inquisitor", "Spirit (Solo)", "dps", "healing",
     {"head": ("Whitemane's Chapeau", 7720), "shoulders": ("Inquisitor's Shawl", 19507),
      "chest": ("Whitemane's Vestments", None)}),
)
FERVOR = {"damage": 212100, "healing": 212101, "tank": 212102, "hybrid": 212103}
# Type changes the doc names (subclass, Material): mail to plate, mail to leather.
TYPE_CHANGES = {"zealot_scarlet_champion_head": (4, 6), "zealot_scarlet_champion_shoulders": (4, 6),
                "zealot_ironspine_chest": (2, 8)}
VENDOR_ENTRIES = {"heroic": 300890, "empowered_1": 300891, "empowered_2": 300892, "empowered_3": 300893}
TIER_NAMES = {"heroic": "Heroic", "empowered_1": "Molten Empowered", "empowered_2": "Draconic Empowered",
              "empowered_3": "Chthonic Empowered"}
HOUND = 300894

SCHOOL_DAMAGE, APPLY_AURA, HEAL, HEAL_PCT = 2, 6, 10, 136
PERIODIC_DAMAGE, PERIODIC_HEAL, OBS_MOD_HEALTH, SCHOOL_ABSORB = 3, 8, 20, 69
SUPPRESS_CASTER_PROCS = 0x00010000
PROC_FLAG_TAKEN_DAMAGE = 0x00100000
HEALS_DONE = 0x00004000 | 0x00000400 | 0x00040000


def secondary(kind: str, slot: str) -> str:
    if slot == "chest":
        return "CDH/Versatility"
    if kind == "plate_tank":
        return "Parry/Versatility (Any)" if slot == "head" else "Parry/CDH"
    if kind == "leather_tank":
        return "Dodge/Versatility" if slot == "head" else "Dodge/CDH"
    return "Haste/Versatility" if slot == "head" else "Haste/CDH"


@unittest.skipUnless(SOURCE.is_file() and BONUS_SOURCE.is_file() and NPC_DIR.is_dir(),
                     "the Zealot's source files (source/items/zealot_set*.py, source/npcs/zealot_set/) are missing")
class ZealotSetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load_items_registry()
        keys = {f"zealot_{prefix}_{slot}" for _, prefix, *_ in SETS for slot in SLOTS}
        cls.items = {e["id"]: e["_decl"] for e in cls.reg.item_declarations if e["id"] in keys}
        decls = [e["_decl"] for e in cls.reg.item_set_declarations]
        cls.sets = {d.set_id: d for d in decls if isinstance(d, ItemSetDecl) and d.set_id in range(1004, 1014)}
        cls.tokens = {d.key: d for d in decls if isinstance(d, SetTokenDecl) and d.key.startswith("zealot_")}
        cls.other_tokens = [d for d in decls if isinstance(d, SetTokenDecl) and not d.key.startswith("zealot_")]
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

    # --- the ladder --------------------------------------------------------------------------------------------------

    def test_ladder(self):
        # The ladders as the items carry them (source/ is loaded by the registry, not importable as a package).
        VANILLA_HEROIC_SET = next(iter(self.items.values())).ladder
        VANILLA_DUNGEON = next(e["_decl"].ladder for e in self.reg.item_declarations
                               if e["_decl"].ladder.name == "vanilla_dungeon")
        self.assertEqual([t.name for t in VANILLA_HEROIC_SET.tiers], list(TIERS))
        dungeon = {t.name: t for t in VANILLA_DUNGEON.tiers}
        for spec in VANILLA_HEROIC_SET.tiers:
            ref = dungeon[spec.name]
            self.assertEqual((spec.step, spec.ilvl, spec.quality, spec.required_level, spec.heroic_flag, spec.label,
                              spec.sockets, spec.deferred),
                             (ref.step, ref.ilvl, ref.quality, ref.required_level, ref.heroic_flag, ref.label,
                              ref.sockets, ref.deferred), spec.name)
        first = VANILLA_HEROIC_SET.tiers[0]
        self.assertTrue(first.explicit and first.heroic_flag and first.step == 1 and first.ilvl == 66)
        self.assertEqual(first.quality, Quality.EPIC)
        self.assertEqual(VANILLA_HEROIC_SET.effect_reference, "heroic")
        # A normal lootid finds no tier on it (the tokens drop only on heroic).
        from lib import loot_tables

        self.assertIsNone(loot_tables.own_level_tier(VANILLA_HEROIC_SET))
        self.assertEqual(loot_tables.first_explicit_tier(VANILLA_HEROIC_SET).name, "heroic")

    # --- the pieces --------------------------------------------------------------------------------------------------

    def test_pieces(self):
        self.assertEqual(len(self.items), 30)
        for set_id, prefix, _name, primary, kind, _role, pieces in SETS:
            for slot in SLOTS:
                key = f"zealot_{prefix}_{slot}"
                decl = self.items[key]
                name, stock = pieces[slot]
                self.assertIsNone(decl.base, key)  # every piece is new (the stock entries stay as they are)
                self.assertEqual(decl.name, name, key)
                if stock is not None:
                    self.assertEqual(decl.like, stock, key)  # a reused stock piece: its name and look
                self.assertIsNotNone(decl.like, key)
                self.assertEqual((decl.primary, decl.secondary), (primary, secondary(kind, slot)), key)
                self.assertEqual(decl.extra_stamina, 0.25 if kind == "leather_tank" else 0.0, key)
                self.assertEqual(decl.ladder.name, "vanilla_heroic_set")
                self.assertEqual((decl.ilvl, decl.quality, decl.required_level), (None, None, None))
                columns = dict(decl.columns)
                self.assertEqual((columns["bonding"], columns["itemset"]), (1, set_id), key)
                if key in TYPE_CHANGES:
                    self.assertEqual((columns["subclass"], columns["Material"]), TYPE_CHANGES[key], key)
        stock = {decl.like for decl in self.items.values()} & {7719, 7718, 7688, 7712, 7711, 7720, 19507}
        self.assertEqual(len(stock), 7)

    def test_sockets(self):
        bonus = {"Haste": 3267, "Parry": 3359, "Dodge": 2871, "CDH": 2874}
        for key, decl in self.items.items():
            kind = next(k for _, p, _, _, k, _, _ in SETS if key.startswith(f"zealot_{p}_"))
            first = Socket.RED if kind == "dps" else Socket.BLUE
            expected = (Socket.META, first) if key.endswith("_head") else (first,)
            self.assertEqual(decl.sockets, expected, key)
            self.assertEqual(decl.socket_bonus, bonus[decl.secondary.split("/")[0]], key)
        self.assertTrue(all(t.sockets for t in next(iter(self.items.values())).ladder.tiers))

    def test_shape_stats_on_every_tier(self):
        from lib import item_variants

        _, catalog = item_variants.load_itemization_tables()
        names = {shape["name"] for shape in catalog.values()}
        missing = sorted({d.secondary for d in self.items.values()} - names)
        if missing:
            self.skipTest(f"item_shape {missing} not live or pending yet (the integration's itemization SQL)")
        assert_shape_stats_on_every_tier(self, self.items)

    # --- the sets ----------------------------------------------------------------------------------------------------

    def test_sets(self):
        self.assertEqual(set(self.sets), set(range(1004, 1014)))
        for k, (set_id, prefix, name, _primary, _kind, role, _pieces) in enumerate(SETS):
            decl = self.sets[set_id]
            self.assertEqual(decl.name, name)
            self.assertEqual(decl.items, tuple(f"zealot_{prefix}_{slot}" for slot in SLOTS))
            self.assertEqual(list(decl.bonuses), [(2, FERVOR[role]), (3, 212110 + 10 * k)])

    # --- the tokens --------------------------------------------------------------------------------------------------

    def test_tokens(self):
        self.assertEqual(set(self.tokens), {f"zealot_token_{s}" for s in SLOTS})
        names = {"head": "Zealot's Helm", "shoulders": "Zealot's Mantle", "chest": "Zealot's Chestguard"}
        for index, slot in enumerate(SLOTS):
            token = self.tokens[f"zealot_token_{slot}"]
            self.assertEqual(token.name, names[slot])
            self.assertEqual(set(token.slots), INVENTORY[slot])
            self.assertEqual(token.ladder.name, "vanilla_heroic_set")
            self.assertEqual([t for t, _ in token.entries], list(TIERS))
            for tier_index, (tier, entry) in enumerate(token.entries):
                self.assertEqual(entry, 70580 + 4 * index + tier_index)
                self.assertEqual(token.cost(tier), 3080 + 4 * index + tier_index)
            self.assertIn(token.like, range(22349, 22373))  # a Desecrated token's look
            self.assertNotIn('"', token.description)
        self.assertFalse({t.like for t in self.other_tokens} & {t.like for t in self.tokens.values()})

    # --- the vendors -------------------------------------------------------------------------------------------------

    def test_vendors(self):
        self.assertEqual(set(self.vendors), set(VENDOR_ENTRIES.values()))
        creatures = {int(r["entry"]): r for r in self.npcs.creature_templates}
        sold = set()
        for tier, entry in VENDOR_ENTRIES.items():
            vendor = self.vendors[entry]
            self.assertEqual((vendor.tiers, set(vendor.sets), set(vendor.tokens)),
                             ((tier,), set(range(1004, 1014)), set(self.tokens)))
            sold |= {(s, tier) for s in vendor.sets}
            row = creatures[entry]
            self.assertEqual((int(row["npcflag"]), int(row["faction"]), row["AIName"], row["ScriptName"]),
                             (128, 35, "", ""))
            self.assertEqual(row["subname"], f"Zealot's Armor - {TIER_NAMES[tier]}")
        self.assertEqual(len(sold), 40)
        self.assertEqual(set(creatures), set(VENDOR_ENTRIES.values()) | {HOUND})
        self.assertTrue(all(e in CREATURES for e in creatures))
        hound = creatures[HOUND]
        self.assertEqual((int(hound["npcflag"]), int(hound["faction"]), float(hound["DamageModifier"])), (0, 35, 0.0))
        self.assertEqual(int(hound["unit_flags"]) & 0x02000002, 0x02000002)  # not attackable, not selectable
        models = {int(r["CreatureID"]): int(r["CreatureDisplayID"]) for r in self.npcs.creature_template_models}
        self.assertEqual(set(models), set(creatures))
        self.assertEqual(models[HOUND], 2709)  # the stock Scarlet Tracking Hound's look
        self.assertIn(f"NPC_SCARLET_TRACKING_HOUND      = {HOUND}", self.header)

    # --- the bonus spells --------------------------------------------------------------------------------------------

    def header_ids(self) -> dict[str, int]:
        return {m.group(1): int(m.group(2)) for m in re.finditer(r"(SPELL_[A-Z_]+)\s*=\s*(\d+),", self.header)}

    def martyrs(self) -> dict[int, str]:
        ids = self.header_ids()
        found = re.findall(r"\{ (SPELL_[A-Z_]+), Trigger::(\w+) \}", self.header)
        return {ids[name]: kind for name, kind in found}

    def test_ids_mirrored_by_the_header(self):
        ids = self.header_ids()
        self.assertEqual(set(ids.values()), set(self.spells))
        self.assertEqual(len(ids), len(self.spells))
        bonuses = {s for d in self.sets.values() for _, s in d.bonuses}
        self.assertEqual(set(self.martyrs()), bonuses - set(FERVOR.values()))

    def test_script_bindings(self):
        registered = set(re.findall(r"RegisterSpellScript\((\w+)\)", self.script))
        bound = {r["ScriptName"] for r in self.reg.spell_script_names if int(r["spell_id"]) in RESERVATION}
        self.assertEqual(bound, registered)
        martyr = {int(r["spell_id"]) for r in self.reg.spell_script_names if r["ScriptName"] == "spell_zealot_martyr"}
        self.assertEqual(martyr, {212110 + 10 * k for k in range(10)})
        self.assertIn("new ZealotSetUnitHooks();", self.script)

    def test_script_numbers_match_the_tooltips(self):
        B = type("Bonuses", (), {m.group(1): int(m.group(2)) for m in re.finditer(r"^([A-Z_]+) = (\d+)$",
                                                                                  self.bonus_source, re.MULTILINE)})

        def const(name: str) -> float:
            match = re.search(rf"{name}\s*=\s*([\d.]+)f?;", self.header)
            self.assertIsNotNone(match, name)
            return float(match.group(1))

        pairs = {"kFervorFullAtHealthPct": B.FERVOR_FULL_AT_HEALTH_PCT, "kMartyrHealthPct": B.MARTYR_HEALTH_PCT,
                 "kKennelCallHounds": B.KENNEL_CALL_HOUNDS, "kArcanistsWardHealthPct": B.ARCANISTS_WARD_HEALTH_PCT,
                 "kBloodOfferingCostPct": B.BLOOD_OFFERING_COST_PCT}
        for name, value in pairs.items():
            self.assertEqual(const(name), float(value), name)
        # The doc's numbers: full Fervor at 40%, the 35% line, 60 s, two hounds, 15% ward, 10% blood.
        self.assertEqual((B.FERVOR_FULL_AT_HEALTH_PCT, B.MARTYR_HEALTH_PCT, B.MARTYR_COOLDOWN_S, B.KENNEL_CALL_HOUNDS,
                          B.ARCANISTS_WARD_HEALTH_PCT, B.BLOOD_OFFERING_COST_PCT), (40, 35, 60, 2, 15, 10))
        for k in range(10):
            desc = self.spells[212110 + 10 * k]["raw_overrides"]["Description_Lang_enUS"]
            self.assertIn("35% health", desc, 212110 + 10 * k)
            self.assertIn("once every 60 sec", desc)
        # The doc's percents in the payouts' data.
        amount = {sid: [(self.spells[sid].get(f"effect{n}") or {}).get("base_points", 0) + 1 for n in (1, 2, 3)]
                  for sid in self.spells}
        self.assertEqual(amount[212111][:2], [5, 30])     # Unbroken Zeal: Strength +5%, heal 30%
        self.assertEqual(amount[212121][0], -10)          # Hold the Line
        self.assertEqual(amount[212131][0], 5)            # Kindled Vigil: 5% x 3 ticks = 15%
        self.assertEqual(amount[212141][0], -10)          # Kennel Call
        self.assertEqual(amount[212151][0], 50)           # Last Page
        self.assertEqual(amount[212161], [15, 10, 25])    # Extract Confession
        self.assertEqual(amount[212171][0], -20)          # Bone Cage
        self.assertEqual(amount[212181][0], -10)          # Hallowed Thorns
        self.assertEqual(amount[212201][0], 20)           # Blood Offering
        self.assertEqual((amount[212100][0], amount[212101][0], amount[212102][0], amount[212103][:2]),
                         (6, 8, 6, [6, 8]))               # Zealot's Fervor
        durations = {212111: 10000, 212121: 8000, 212131: 6000, 212141: 12000, 212151: 10000, 212161: 8000,
                     212171: 8000, 212181: 10000, 212191: 8000}
        for sid, ms in durations.items():
            self.assertEqual(int(self.spells[sid]["duration_ms"]), ms, sid)

    def test_trigger_rows(self):
        procs = {int(r["SpellId"]): r for r in self.reg.spell_procs if int(r["SpellId"]) in RESERVATION}
        kinds = self.martyrs()
        self.assertEqual(set(procs), set(kinds) | {212111, 212151, 212171, 212181})
        for spell_id, row in procs.items():
            self.assertEqual((row["Chance"], row["ProcsPerMinute"]), (100.0, 0.0), spell_id)
            flags = int(row["ProcFlags"])
            if spell_id in kinds:
                # The 60 s internal cooldown on a proc row: Cooldown Haste never touches it.
                self.assertEqual(row["Cooldown"], 60000, spell_id)
                kind = kinds[spell_id]
                self.assertEqual(bool(flags & PROC_FLAG_TAKEN_DAMAGE), kind in ("Self", "SelfOrAlly"), spell_id)
                self.assertEqual(flags & HEALS_DONE, HEALS_DONE if kind != "Self" else 0, spell_id)
            else:
                self.assertEqual(row["Cooldown"], 0, spell_id)
        self.assertEqual(procs[212151]["Charges"], 3)
        # The thorns answer melee and ranged hits taken, never a spell.
        for spell_id in (212171, 212181):
            self.assertEqual(int(procs[spell_id]["ProcFlags"]), 0x8 | 0x20 | 0x80 | 0x200)

    def test_damage_on_potency_and_heals_by_percent(self):
        for spell_id, spell in self.spells.items():
            raw = spell["raw_overrides"]
            self.assertEqual(raw["EquippedItemClass"], -1, spell_id)
            self.assertNotIn("{pot", raw.get("AuraDescription_Lang_enUS", ""), spell_id)
            for n in (1, 2, 3):
                effect = spell.get(f"effect{n}")
                if not effect:
                    continue
                damage = effect["type"] == SCHOOL_DAMAGE or (effect["type"] == APPLY_AURA
                                                             and effect["apply_aura"] == PERIODIC_DAMAGE)
                heal = effect["type"] in (HEAL, HEAL_PCT) or (
                    effect["type"] == APPLY_AURA and effect["apply_aura"] in (PERIODIC_HEAL, OBS_MOD_HEALTH,
                                                                              SCHOOL_ABSORB))
                if damage:
                    self.assertTrue(effect.get("_potency"), spell_id)
                    self.assertNotEqual(int(raw["DefenseType"]), 0, spell_id)
                elif heal:
                    # Heals and the ward are percents of health or of a hit (ruling 59: never a flat number).
                    self.assertTrue(effect.get("_potency_excluded"), spell_id)

    def test_payouts_suppress_caster_procs(self):
        bonuses = {s for d in self.sets.values() for _, s in d.bonuses}
        for spell_id, spell in self.spells.items():
            if spell_id in bonuses:
                self.assertTrue(int(spell["attributes"]) & 0x40, spell_id)  # passive
                continue
            self.assertTrue(int(spell["raw_overrides"].get("AttributesEx3", 0)) & SUPPRESS_CASTER_PROCS, spell_id)
            self.assertFalse(int(spell["attributes"]) & 0x40, spell_id)  # a buff the player sees

    def test_names(self):
        for spell_id in FERVOR.values():
            self.assertEqual(self.spells[spell_id]["name"], "Zealot's Fervor")
        for spell_id, spell in self.spells.items():
            raw = spell["raw_overrides"]
            for text in (spell["name"], raw["Description_Lang_enUS"], raw.get("AuraDescription_Lang_enUS", "")):
                self.assertNotIn("Martyrdom", text, spell_id)
                self.assertNotIn("|", text, spell_id)
        self.assertIn(f"{40}% health or below", self.spells[212100]["raw_overrides"]["Description_Lang_enUS"])

    # --- the spawns --------------------------------------------------------------------------------------------------

    def test_spawns(self):
        text = SPAWNS.read_text(encoding="utf-8")
        rows = re.findall(r"^\((\d+), (\d+), (\d+), .*\),?;?$", text, re.MULTILINE)
        self.assertEqual(sorted(int(e) for _, e, _ in rows), sorted(VENDOR_ENTRIES.values()))
        self.assertTrue(all(int(m) == 0 for _, _, m in rows))  # Tirisfal Glades, map 0
        self.assertTrue(all(5300000 < int(g) < 5400000 for g, _, _ in rows))
        self.assertIn("DELETE FROM `creature` WHERE `id` BETWEEN 300890 AND 300893", text)

    def test_fix_pass_rulings(self):
        """The 2026-11-20 rulings and review fixes. B8: the two short areas (Kindled Vigil's burn 5 yd, Arcanist's
        detonation 10 yd) hit every enemy, so no area script binds them. C4: the heal trigger takes any target the
        heal hits, the wearer included (no player or self exclusion in the martyr's heal path), and the four heal
        tooltips say so. m6: the ward detonates only on break, expiry or cancel."""
        for spell_id in (212132, 212192):
            self.assertLessEqual(self.spells[spell_id]["effect1"]["radius_yards"], 10.0, spell_id)
        bound = {int(r["spell_id"]) for r in self.reg.spell_script_names if int(r["spell_id"]) in RESERVATION}
        self.assertFalse({212132, 212192} & bound)
        self.assertNotIn("in_combat_area", self.script)
        subject = self.script.split("Unit* Subject(ProcEventInfo& eventInfo) const", 1)[1]
        subject = subject.split("bool CheckProc(", 1)[0]
        heal_path = subject.split("TriggersOnAlly(trigger)", 1)[1]
        for excluded in ("healed == wearer", "IsPlayer()", "IsFriendlyTo"):
            self.assertNotIn(excluded, heal_path, excluded)
        for spell_id in (212130, 212150, 212180, 212200):
            self.assertIn("(you included)", self.spells[spell_id]["raw_overrides"]["Description_Lang_enUS"], spell_id)
        ward = self.script.split("class spell_zealot_arcanists_ward", 1)[1].split("class ", 1)[0]
        for mode in ("AURA_REMOVE_BY_ENEMY_SPELL", "AURA_REMOVE_BY_EXPIRE", "AURA_REMOVE_BY_CANCEL"):
            self.assertIn(mode, ward, mode)

    def test_haunting_mark_ignores_the_zealot_payouts(self):
        # HauntedSetUnitHooks::ModifySpellDamageTaken skips the Zealot's slice by id: Kennel Call's ranged bite
        # (hunters) is ranged class and would otherwise consume a Beaststalker's Haunting Mark.
        haunted = (REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "DungeonSets" /
                   "haunted_set_bonuses.cpp").read_text(encoding="utf-8")
        self.assertIn('#include "ZealotSetLogic.h"', haunted)
        hook = haunted.split("void ModifySpellDamageTaken(", 1)[1].split("void OnSpellDamageTakenFinal(", 1)[0]
        self.assertIn("ZealotSet::kSpellsZealotSet.Contains(spellInfo->Id)", hook)


if __name__ == "__main__":
    unittest.main()
