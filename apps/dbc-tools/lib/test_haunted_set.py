"""
The Haunted dungeon set family: source/items/haunted_set.py, source/items/haunted_set_bonuses.py,
source/npcs/haunted_set/vendors.py and the scripts in modules/mod-dungeon-bosses (src/DungeonSets/
haunted_set_bonuses.cpp, HauntedSetLogic.h).

Checks:
  - the pieces: 10 sets of 8 on the dungeon ladder, the stock Tier 0 entries of the 8 kept sets as base=, Dreadmist
    (183) left out, the two new tank sets minted with their own itemset; the stats per slot and archetype (primary,
    the family's secondaries, the tank swaps, Leather Tank's extra Stamina); sockets (1, the head meta plus 1; red,
    blue on tanks) and the socket bonus of the first secondary; Bind on Pickup;
  - the sets: one item_set() per set, 8 pieces, a 3 and a 5 piece bonus from the `haunted_set` reservation;
  - the tokens: 8 slots, entries 70500 + 5 * slot + tier and costs 3000 + 5 * slot + tier on the dungeon ladder,
    the Desecrated looks, every armor slot bought by exactly one token;
  - the vendors: four creatures in the `haunted_set` creature slice (vendor flag, friendly to all), one per armor
    type, every set sold by exactly one vendor of its own armor type;
  - the bonus spells: ids in the reservation and mirrored by HauntedSetLogic.h, every scripted_by() name registered
    by haunted_set_bonuses.cpp, the tooltip literals equal to the C++ script numbers, damage and heals on potency
    unless declared excluded (and then DefenseType NONE or a percent of health), payouts suppress caster procs,
    triggered-cast rules (EquippedItemClass -1), the proc rows (a cast-phase row has no hit mask).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_haunted_set.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "DungeonSets"
HEADER = MODULE_DIR / "HauntedSetLogic.h"
SCRIPT = MODULE_DIR / "haunted_set_bonuses.cpp"
NPC_DIR = TOOL_ROOT / "source" / "npcs" / "haunted_set"
RESERVATION = range(205700, 205900)
BONUS_RANGE = range(205700, 205800)
CREATURES = range(300480, 300500)

SLOTS = ("head", "shoulders", "chest", "hands", "waist", "legs", "feet", "wrist")
INVENTORY = {"head": {1}, "shoulders": {3}, "chest": {5, 20}, "hands": {10}, "waist": {6}, "legs": {7}, "feet": {8},
             "wrist": {9}}
STOCK_SETS = {
    181: ("magisters", "Intellect (Solo)", "dps", (16686, 16689, 16688, 16684, 16685, 16687, 16682, 16683)),
    182: ("devout", "Spirit (Solo)", "dps", (16693, 16695, 16690, 16692, 16696, 16694, 16691, 16697)),
    184: ("shadowcraft", "Agility (Solo)", "dps", (16707, 16708, 16721, 16712, 16713, 16709, 16711, 16710)),
    185: ("wildheart", "Spirit (Solo)", "dps", (16720, 16718, 16706, 16717, 16716, 16719, 16715, 16714)),
    186: ("beaststalkers", "Agility (Solo)", "dps", (16677, 16679, 16674, 16676, 16680, 16678, 16675, 16681)),
    187: ("elements", "Intellect (Solo)", "dps", (16667, 16669, 16666, 16672, 16673, 16668, 16670, 16671)),
    188: ("lightforge", "Intellect (Solo)", "dps", (16727, 16729, 16726, 16724, 16723, 16728, 16725, 16722)),
    189: ("valor", "Strength (Solo)", "dps", (16731, 16733, 16730, 16737, 16736, 16732, 16734, 16735)),
}
NEW_SETS = {1000: ("protectors", "Agility (Solo)", "leather_tank"), 1001: ("shadowguard", "Strength (Solo)",
                                                                            "plate_tank")}
ARMOR_SETS = {"Cloth": {181, 182}, "Leather": {184, 185, 1000}, "Mail": {186, 187}, "Plate": {188, 189, 1001}}
# (armor type, tiers) -> vendor entry: the "Normal & Heroic" vendor on the user's spot, then the three empowered ones.
TIER_SPLIT = (("normal", "heroic"), ("empowered_1",), ("empowered_2",), ("empowered_3",))
TIER_NAMES = ("Normal & Heroic", "Molten Empowered", "Draconic Empowered", "Chthonic Empowered")
VENDOR_ENTRIES = {}
for _n, _armor in enumerate(ARMOR_SETS):
    VENDOR_ENTRIES[(_armor, TIER_SPLIT[0])] = 300480 + _n
    for _k, _tiers in enumerate(TIER_SPLIT[1:]):
        VENDOR_ENTRIES[(_armor, _tiers)] = 300484 + 3 * _n + _k

SCHOOL_DAMAGE, APPLY_AURA, HEAL, HEAL_PCT = 2, 6, 10, 136
SUPPRESS_CASTER_PROCS = 0x00010000
PROC_SPELL_PHASE_CAST = 0x1


def secondary(kind: str, slot: str) -> str:
    big = slot in ("head", "shoulders", "chest", "legs")
    if kind == "plate_tank":
        return "Parry/Mastery" if big else "Parry/Proc"
    if kind == "leather_tank":
        return "Dodge/Mastery" if big else "Dodge/Proc"
    return "Haste/Mastery" if big else ("Haste/Proc" if slot in ("hands", "wrist") else "Mastery/Proc")


class HauntedSetTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load_items_registry()
        cls.items = {e["id"]: e["_decl"] for e in cls.reg.item_declarations if e["id"].startswith("haunted_")}
        decls = [e["_decl"] for e in cls.reg.item_set_declarations]
        cls.sets = {d.set_id: d for d in decls if isinstance(d, ItemSetDecl)}
        cls.tokens = {d.key: d for d in decls if isinstance(d, SetTokenDecl)}
        cls.vendors = {d.entry: d for d in decls if isinstance(d, SetVendorDecl)}
        cls.spells = {int(e["id"]): e for e in cls.reg.spells if int(e["id"]) in RESERVATION}
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
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
        for set_id, (prefix, primary, kind, bases) in STOCK_SETS.items():
            for slot, base in zip(SLOTS, bases):
                decl = self.items[f"haunted_{prefix}_{slot}"]
                self.assertEqual((decl.base, decl.primary, decl.secondary), (base, primary, secondary(kind, slot)))
                self.assertEqual(dict(decl.columns), {"bonding": 1}, decl.key)  # the stock row's itemset stays
                self.assertEqual(decl.extra_stamina, 0.0)
        for set_id, (prefix, primary, kind) in NEW_SETS.items():
            for slot in SLOTS:
                decl = self.items[f"haunted_{prefix}_{slot}"]
                self.assertIsNone(decl.base)
                self.assertEqual((decl.primary, decl.secondary, decl.quality), (primary, secondary(kind, slot),
                                                                                 Quality.RARE))
                self.assertEqual(dict(decl.columns), {"bonding": 1, "itemset": set_id})
                self.assertEqual(decl.extra_stamina, 0.25 if kind == "leather_tank" else 0.0)
        self.assertFalse([k for k, d in self.items.items() if d.base in range(16698, 16706)])  # Dreadmist retires
        for decl in self.items.values():
            self.assertEqual(decl.ladder.name, "vanilla_dungeon")
            self.assertEqual([t.name for t in decl.ladder.tiers if not t.deferred],
                             ["normal", "heroic", "empowered_1", "empowered_2", "empowered_3"])

    def test_sockets(self):
        bonus = {"Haste": 3267, "Mastery": 3267, "Parry": 3359, "Dodge": 2871}
        for key, decl in self.items.items():
            tank = decl.secondary.startswith(("Parry", "Dodge"))
            first = Socket.BLUE if tank else Socket.RED
            expected = (Socket.META, first) if key.endswith("_head") else (first,)
            self.assertEqual(decl.sockets, expected, key)
            self.assertEqual(decl.socket_bonus, bonus[decl.secondary.split("/")[0]], key)
            self.assertFalse(decl.ladder.tiers[0].sockets)  # Normal: none (user 2026-11-06)

    # --- the sets ----------------------------------------------------------------------------------------------------

    def test_sets(self):
        self.assertEqual(set(self.sets), set(STOCK_SETS) | set(NEW_SETS))
        for set_id, decl in self.sets.items():
            prefix = (STOCK_SETS.get(set_id) or NEW_SETS[set_id])[0]
            self.assertEqual(decl.items, tuple(f"haunted_{prefix}_{slot}" for slot in SLOTS))
            self.assertEqual([t for t, _ in decl.bonuses], [3, 5])
            for _, spell_id in decl.bonuses:
                self.assertIn(spell_id, BONUS_RANGE)
                self.assertIn(spell_id, self.spells)
            self.assertEqual(decl.name is None, set_id in STOCK_SETS)
        self.assertEqual(len({s for d in self.sets.values() for _, s in d.bonuses}), 20)

    # --- the tokens --------------------------------------------------------------------------------------------------

    def test_tokens(self):
        self.assertEqual(len(self.tokens), 8)
        covered = set()
        for index, slot in enumerate(SLOTS):
            token = self.tokens[f"haunted_token_{slot}"]
            self.assertEqual(set(token.slots), INVENTORY[slot])
            covered |= set(token.slots)
            self.assertTrue(token.name.startswith("Haunted "))
            self.assertIn(token.like, range(22349, 22373))  # the Desecrated tokens' looks
            self.assertEqual((token.ilvl, token.quality, token.required_level), (60, Quality.RARE, 0))
            self.assertEqual(token.ladder.name, "vanilla_dungeon")
            for tier_index, (tier, entry) in enumerate(token.entries):
                self.assertEqual(entry, 70500 + 5 * index + tier_index)
                self.assertEqual(token.cost(tier), 3000 + 5 * index + tier_index)
            self.assertNotIn('"', token.description)
        self.assertEqual(covered, {1, 3, 5, 20, 6, 7, 8, 9, 10})

    # --- the vendors -------------------------------------------------------------------------------------------------

    def test_vendors(self):
        self.assertEqual(len(self.vendors), 16)
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
            self.assertEqual(creatures[entry]["subname"], f"Haunted {armor} - {TIER_NAMES[TIER_SPLIT.index(tiers)]}")
        tiers = ("normal", "heroic", "empowered_1", "empowered_2", "empowered_3")
        self.assertEqual(set(sold), {(s, t) for s in self.sets for t in tiers})  # every set and tier is sold
        self.assertEqual(set(creatures), set(VENDOR_ENTRIES.values()))
        for entry, row in creatures.items():
            self.assertIn(entry, CREATURES)
            self.assertEqual((int(row["npcflag"]), int(row["faction"]), row["AIName"], row["ScriptName"]),
                             (128, 35, "", ""))
        self.assertEqual({int(r["CreatureID"]) for r in self.npcs.creature_template_models}, set(creatures))

    # --- the bonus spells --------------------------------------------------------------------------------------------

    def header_ids(self) -> dict[str, int]:
        return {m.group(1): int(m.group(2)) for m in re.finditer(r"(SPELL_[A-Z_]+)\s*=\s*(\d+),", self.header)}

    def test_ids_mirrored_by_the_header(self):
        ids = self.header_ids()
        self.assertEqual(set(ids.values()), set(self.spells))
        self.assertEqual(len(ids), len(self.spells))
        self.assertTrue(all(i in BONUS_RANGE for i in self.spells))

    def test_script_bindings(self):
        registered = set(re.findall(r"RegisterSpellScript\((\w+)\)", self.script))
        bound = {r["ScriptName"] for r in self.reg.spell_script_names if int(r["spell_id"]) in RESERVATION}
        self.assertEqual(bound, registered)
        self.assertIn("new HauntedSetSpellHooks()", self.script)
        self.assertIn("new HauntedSetUnitHooks()", self.script)

    def test_script_numbers_match_the_tooltips(self):
        source = (TOOL_ROOT / "source" / "items" / "haunted_set_bonuses.py").read_text(encoding="utf-8")
        B = type("Bonuses", (), {m.group(1): int(m.group(2)) for m in re.finditer(r"^([A-Z_]+) = (\d+)$", source,
                                                                                  re.MULTILINE)})

        def const(name: str) -> float:
            match = re.search(rf"{name}\s*=\s*([\d.]+)f?;", self.header)
            self.assertIsNotNone(match, name)
            return float(match.group(1))

        pairs = {
            "kWraithVolleyCastPct": B.WRAITH_VOLLEY_CAST_PCT, "kWraithVolleyTickPct": B.WRAITH_VOLLEY_TICK_PCT,
            "kWraithVolleyExtraTargets": B.WRAITH_VOLLEY_EXTRA_TARGETS, "kWraithVolleyRadius": B.WRAITH_VOLLEY_RADIUS,
            "kSolaceRange": B.SOLACE_RANGE, "kLingeringDeathPct": B.LINGERING_DEATH_PCT,
            "kGraveBloomRadius": B.GRAVE_BLOOM_RADIUS, "kUnbrokenFaithManaPct": B.UNBROKEN_FAITH_MANA_PCT,
            "kSoulReleasedHealRange": B.SOUL_RELEASED_HEAL_RANGE,
            "kSoulReleasedEnemyRange": B.SOUL_RELEASED_ENEMY_RANGE, "kWraithVenomPct": B.WRAITH_VENOM_PCT,
            "kWraithVenomCooldownMs": B.WRAITH_VENOM_ICD_S * 1000, "kGraveRotPct": B.GRAVE_ROT_PCT,
            "kGraveRotCooldownMs": B.GRAVE_ROT_ICD_S * 1000, "kGraveRotExtendMs": B.GRAVE_ROT_EXTEND_S * 1000,
            "kGraveRotExtendCapMs": B.GRAVE_ROT_EXTEND_CAP_S * 1000,
            "kBoneWardPctPerStack": B.BONE_WARD_PCT, "kDeathlessHealthPct": B.DEATHLESS_HEALTH_PCT,
            "kGatheringChorusMaxStacks": int(self.spells[205734]["raw_overrides"]["CumulativeAura"]),
        }
        for name, value in pairs.items():
            self.assertEqual(const(name), float(value), name)
        # The chorus stack's amount is the 20% per stack the payout reads; its target count the chain's.
        self.assertEqual(self.spells[205734]["effect1"]["base_points"] + 1, B.CHORUS_STACK_PCT)
        self.assertEqual(self.spells[205731]["effect1"]["chain_targets"], B.CHORUS_TARGETS)
        self.assertEqual(self.spells[205732]["effect1"]["chain_targets"], B.CHORUS_TARGETS)

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
                if effect.get("_potency"):
                    self.assertNotEqual(int(raw["DefenseType"]), 0, spell_id)
                else:
                    self.assertTrue(effect.get("_potency_excluded"), spell_id)
        # The repeated ticks carry the tick's own amount: DmgClass NONE, so no second bonus.
        for spell_id in (205722, 205723):
            self.assertEqual(int(self.spells[spell_id]["raw_overrides"]["DefenseType"]), 0)

    def test_payouts_suppress_caster_procs(self):
        bonuses = {s for d in self.sets.values() for _, s in d.bonuses}
        for spell_id, spell in self.spells.items():
            raw = spell["raw_overrides"]
            if spell_id in bonuses:
                self.assertTrue(int(spell["attributes"]) & 0x40, spell_id)  # passive
                continue
            self.assertTrue(int(raw.get("AttributesEx3", 0)) & SUPPRESS_CASTER_PROCS, spell_id)

    def test_proc_rows(self):
        procs = {int(r["SpellId"]): r for r in self.reg.spell_procs if int(r["SpellId"]) in RESERVATION}
        self.assertEqual(set(procs), {205700, 205710, 205712, 205721, 205730, 205733, 205742, 205750, 205760,
                                      205762, 205781, 205790, 205792})
        for spell_id, row in procs.items():
            if row["SpellPhaseMask"] == PROC_SPELL_PHASE_CAST:
                self.assertEqual(row["HitMask"], 0, spell_id)  # a cast phase has no outcome yet
            self.assertTrue(0 < row["Chance"] <= 100, spell_id)
        self.assertEqual((procs[205700]["Chance"], procs[205700]["Cooldown"]), (100.0, 4000))  # the script rolls
        self.assertEqual((procs[205712]["Chance"], procs[205712]["Cooldown"]), (12.0, 3000))
        self.assertEqual((procs[205721]["Chance"], procs[205721]["Cooldown"]), (5.0, 2000))
        self.assertEqual((procs[205730]["Chance"], procs[205730]["Cooldown"]), (10.0, 6000))
        self.assertEqual(procs[205733]["HitMask"], 0x2)  # crits only
        self.assertEqual((procs[205742]["Chance"], procs[205742]["Cooldown"]), (12.0, 4000))
        self.assertEqual((procs[205750]["Chance"], procs[205750]["Cooldown"]), (10.0, 5000))
        self.assertEqual((procs[205760]["Chance"], procs[205760]["Cooldown"]), (15.0, 4000))
        self.assertEqual((procs[205762]["Chance"], procs[205762]["Cooldown"]), (10.0, 4000))
        self.assertEqual((procs[205781]["HitMask"], procs[205781]["Cooldown"]), (0x10, 1000))  # dodges
        self.assertEqual((procs[205790]["HitMask"], procs[205790]["Cooldown"]), (0x60, 1000))  # parries, blocks
        self.assertEqual(procs[205792]["Cooldown"], 60000)

    def test_shapes(self):
        triggers = {205710: 205711, 205733: 205734, 205760: 205761, 205781: 205782, 205790: 205791}
        for aura, payout in triggers.items():
            self.assertEqual(self.spells[aura]["effect1"]["apply_aura"], 42)  # PROC_TRIGGER_SPELL
            self.assertEqual(self.spells[aura]["effect1"]["trigger_spell"], payout)
        self.assertEqual(self.spells[205703]["effect1"]["apply_aura"], 271)  # MOD_DAMAGE_FROM_CASTER, family 0
        self.assertEqual(int(self.spells[205703]["raw_overrides"]["SpellClassSet"]), 0)
        self.assertEqual(self.spells[205780]["effect1"]["misc_value"], 2)  # Stamina
        self.assertEqual(int(self.spells[205782]["raw_overrides"]["CumulativeAura"]), 3)
        self.assertEqual((self.spells[205793]["duration_ms"], self.spells[205793]["effect1"]["amplitude"]),
                         (6000, 2000))
        self.assertEqual(self.spells[205764]["raw_overrides"]["DefenseType"], 3)  # ranged attack power
        self.assertEqual(self.spells[205763]["raw_overrides"]["DefenseType"], 2)


if __name__ == "__main__":
    unittest.main()
