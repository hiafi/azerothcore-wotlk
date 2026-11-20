"""
The Scarlet Monastery boss list items (wave 3 dungeon items): source/items/scarlet_monastery.py.

Checks:
  - the list: 64 items on the dungeon ladder, keys `sm_`, one declaration per stock entry (24 `base=` items), the 14
    bosses' counts and the new items' levels (the boss's table level, required level = level - 5);
  - the doc's stats: each item's primary and secondaries are exactly the stats docs/dungeons/scarlet-monastery-rework.md
    ## Loot "Boss lists" names for it (Stamina is everywhere, so it is left out);
  - the shapes the list names exist, or are one of the three the integration adds (PENDING_SHAPES);
  - jewelry and the primary-less trinket carry secondaries only, the socket picks (trinkets and Normal tiers never,
    a two-hander two, the second socket yellow), Normal tiers Rare (the one stock epic set to Rare), new items Bind on
    Pickup with a look, the type and slot edits (Gauntlets of Divinity plate, the Dog Whistle and Deadman's Hand
    trinkets), the moved items' levels, the kept effects (Ravager, Deadman's Hand, the Dog Whistle's rewritten Use),
    ranged ammo, the declared multipliers;
  - the materialized rows: every doc stat has a point on every tier (the Blackrock gear review's S3).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scarlet_monastery_items.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib.dsl.items import NULL_PRIMARY_SHAPE, Quality, Socket, SpellTrigger  # noqa: E402
from lib.test_hard_mode_item_effects import (  # noqa: E402
    _load_items_registry, materialized_tier_stats,
)

R, Y, B = Socket.RED, Socket.YELLOW, Socket.BLUE

# The shapes the list names that did not exist when it was written; the integration adds them in one pending
# itemization file (the STAGE-SM-LIST report, "New item shapes needed").
PENDING_SHAPES = {"Block/Parry/Versatility", "Block/Mastery/Versatility", "Dodge/Versatility (Any)"}

# Handoff section 1.3: the boss's item level for new items and moved stock items; required level = level - 5.
BOSS_LEVEL = {
    "Vishas": 34, "Ironspine": 35, "Azshir": 35, "Thalnos": 38, "Loksey": 34, "Kell": 37, "Hollis": 37, "Doan": 38,
    "Crell": 41, "Halden": 41, "Herod": 42, "Thorne": 43, "LastStand": 44, "Whitemane": 44,
}

# key -> (boss, stock entry or None for a new item, the doc's stats). The doc's order is kept; the shapes are
# unordered pairs.
LIST = {
    "sm_bloody_brass_knuckles": ("Vishas", 7683, "Agi Crit"),
    "sm_torturing_poker": ("Vishas", 7682, "Agi Haste"),
    "sm_branded_leather_bracers": ("Vishas", 19508, "Agi Haste Vers"),
    "sm_confessors_gloves": ("Vishas", None, "Spi Crit Vers"),
    "sm_interrogators_thumbscrews": ("Vishas", None, "Crit Proc"),
    "sm_ironspines_eye": ("Ironspine", 7686, "Haste Mastery"),
    "sm_ironspines_fist": ("Ironspine", 7687, "Str Parry"),
    "sm_bonecrawler_boots": ("Ironspine", None, "Str Crit Mastery"),
    "sm_bone_link_legguards": ("Ironspine", None, "Agi Crit Vers"),
    "sm_cloak_of_knitted_bone": ("Ironspine", None, "Agi Haste Mastery"),
    "sm_necrotic_wand": ("Azshir", 7708, "Int Mastery"),
    "sm_blighted_leggings": ("Azshir", 7709, "Int Haste Mastery Vers"),
    "sm_ghostshard_talisman": ("Azshir", 7731, "Haste Vers"),
    "sm_morbid_dawn": ("Azshir", 7689, "Str Crit Mastery"),
    "sm_ebon_vise": ("Azshir", 7690, "Agi Crit Mastery"),
    "sm_vigil_keepers_gauntlets": ("Azshir", None, "Str Parry Vers"),
    "sm_orb_of_the_forgotten_seer": ("Thalnos", 7685, "Int Crit Proc"),
    "sm_bloodmages_handwraps": ("Thalnos", None, "Int Haste Proc"),
    "sm_bloodstained_cloak": ("Thalnos", None, "Int Crit Vers"),
    "sm_bloodletting_kris": ("Thalnos", None, "Spi Haste"),
    "sm_sanguine_signet": ("Thalnos", None, "Vers Proc"),
    "sm_dog_training_gloves": ("Loksey", 7756, "Agi Dodge"),
    "sm_loksey_training_stick": ("Loksey", 7710, "Agi Mastery Vers"),
    "sm_dog_whistle": ("Loksey", 3456, "Agi Crit Haste"),
    "sm_kennelmasters_crossbow": ("Loksey", None, "Agi Crit"),
    "sm_leash_scarred_gauntlets": ("Loksey", None, "Agi Haste Vers"),
    "sm_dusty_mail_boots": ("Kell", 19509, "Int Crit Vers"),
    "sm_antiquarians_signet": ("Kell", None, "Mastery Vers"),
    "sm_kirin_tor_spellblade": ("Kell", None, "Int Mastery"),
    "sm_necromancers_skull": ("Kell", None, "Int Haste Mastery Proc"),
    "sm_index_keepers_bindings": ("Hollis", None, "Int Crit Mastery"),
    "sm_lectors_sash": ("Hollis", None, "Spi Mastery Vers"),
    "sm_forbidden_tome": ("Hollis", None, "Spi Haste Vers"),
    "sm_burning_page": ("Hollis", None, "Int Crit Haste"),
    "sm_illusionary_rod": ("Doan", 7713, "Int Crit"),
    "sm_hypnotic_blade": ("Doan", 7714, "Int Haste"),
    "sm_deadmans_hand": ("Doan", 34227, "Dodge Vers"),
    "sm_arcanists_cord": ("Doan", None, "Int Haste Vers"),
    "sm_totem_of_righteous_fire": ("Doan", None, "Int Crit Haste"),
    "sm_proving_blade": ("Crell", None, "Str Mastery"),
    "sm_red_hot_gauntlets": ("Crell", None, "Str Crit Haste"),
    "sm_tempered_girdle": ("Crell", None, "Str Block Vers"),
    "sm_forge_tempered_buckler": ("Crell", None, "Int Haste Mastery"),
    "sm_drillmasters_girdle": ("Halden", None, "Str Haste Vers"),
    "sm_drillmasters_longbow": ("Halden", None, "Agi Haste"),
    "sm_drillfield_cape": ("Halden", None, "Str Crit Mastery"),
    "sm_medal_of_the_proving_ground": ("Halden", None, "Str Crit Vers"),
    "sm_ravager": ("Herod", 7717, "Str Crit"),
    "sm_whirlwind_legplates": ("Herod", None, "Str Haste Mastery"),
    "sm_blade_dancers_treads": ("Herod", None, "Agi Haste Proc"),
    "sm_pendant_of_the_scarlet_champion": ("Herod", None, "Crit Mastery"),
    "sm_furrowed_boots": ("Thorne", None, "Spi Haste Vers"),
    "sm_waterbearers_girdle": ("Thorne", None, "Int Haste Mastery"),
    "sm_idol_of_the_harvest": ("Thorne", None, "Spi Haste Mastery"),
    "sm_pruning_scythe": ("Thorne", None, "Agi Crit Haste"),
    "sm_aegis_of_the_scarlet_commander": ("LastStand", 7726, "Str Block Parry Vers"),
    "sm_mograines_might": ("LastStand", 7723, "Str Haste Vers"),
    "sm_gauntlets_of_divinity": ("LastStand", 7724, "Int Crit Haste Vers"),
    "sm_captains_legguards": ("LastStand", None, "Str Block Mastery Vers"),
    "sm_libram_of_the_last_stand": ("LastStand", None, "Str Parry Vers"),
    "sm_triune_amulet": ("Whitemane", 7722, "Crit Haste"),
    "sm_hand_of_righteousness": ("Whitemane", 7721, "Spi Crit"),
    "sm_cinch_of_the_faithful": ("Whitemane", None, "Spi Haste Mastery"),
    "sm_whitemanes_vigil_candle": ("Whitemane", None, "Spi Haste Mastery Vers"),
}
BOSS_COUNT = {"Vishas": 5, "Ironspine": 5, "Azshir": 6, "Thalnos": 5, "Loksey": 5, "Kell": 4, "Hollis": 4, "Doan": 5,
              "Crell": 4, "Halden": 4, "Herod": 4, "Thorne": 4, "LastStand": 5, "Whitemane": 4}
STAT_NAMES = {"Str": "Strength", "Agi": "Agility", "Int": "Intellect", "Spi": "Spirit", "Crit": "Crit",
              "Haste": "Haste", "Mastery": "Mastery", "Vers": "Versatility", "CDH": "CDH", "Proc": "Proc",
              "Dodge": "Dodge", "Parry": "Parry", "Block": "Block"}
# The pending shapes as the integration adds them (stat types: Dodge 13, Parry 14, Block 15, Mastery 22, Versatility
# 23; rule: a Strength primary): (name, dist_id, stats in name order, primary rule stats). Dist 4 is "Even trio", 2 an
# Even pair.
PENDING_SHAPE_ROWS = {
    96: ("Block/Parry/Versatility", 4, (15, 14, 23), (4,)),
    97: ("Block/Mastery/Versatility", 4, (15, 22, 23), (4,)),
    98: ("Dodge/Versatility (Any)", 2, (13, 23), ()),
}
PRIMARIES = {"Strength", "Agility", "Intellect", "Spirit"}

# Moved stock items (handoff section 1.3): keep their entry as the Normal tier, re-leveled to the boss's table level.
MOVED = {"sm_branded_leather_bracers": (34, 29), "sm_dusty_mail_boots": (37, 32)}

# One socketed standalone piece per boss (the doc names none: designer question), 2 on a two-hander; trinkets never.
# The first socket is red, blue on tank gear; a second takes the color of the first secondary (Crit: yellow).
SOCKETS = {
    "sm_confessors_gloves": (R,), "sm_bonecrawler_boots": (R,), "sm_morbid_dawn": (R, Y),
    "sm_bloodmages_handwraps": (R,), "sm_leash_scarred_gauntlets": (R,), "sm_dusty_mail_boots": (R,),
    "sm_lectors_sash": (R,), "sm_illusionary_rod": (R, Y), "sm_tempered_girdle": (B,),
    "sm_drillmasters_girdle": (R,), "sm_whirlwind_legplates": (R,), "sm_waterbearers_girdle": (R,),
    "sm_captains_legguards": (B,), "sm_cinch_of_the_faithful": (R,),
}
BONUS = {  # stock +4 ratings: 2874 Crit, 3267 Haste, 2972 Block (Mastery, Versatility, Proc, CDH have none)
    "sm_confessors_gloves": 2874, "sm_bonecrawler_boots": 2874, "sm_morbid_dawn": 2874, "sm_bloodmages_handwraps": 3267,
    "sm_leash_scarred_gauntlets": 3267, "sm_dusty_mail_boots": 2874, "sm_lectors_sash": 3267,
    "sm_illusionary_rod": 2874, "sm_tempered_girdle": 2972, "sm_drillmasters_girdle": 3267,
    "sm_whirlwind_legplates": 3267, "sm_waterbearers_girdle": 3267, "sm_captains_legguards": 2972,
    "sm_cinch_of_the_faithful": 3267,
}
TRINKETS = {"sm_dog_whistle", "sm_burning_page", "sm_deadmans_hand", "sm_medal_of_the_proving_ground",
            "sm_whitemanes_vigil_candle"}
# Rings, necks and the primary-less trinket: secondaries only.
JEWELRY = {"sm_interrogators_thumbscrews", "sm_ironspines_eye", "sm_ghostshard_talisman", "sm_sanguine_signet",
           "sm_antiquarians_signet", "sm_pendant_of_the_scarlet_champion", "sm_triune_amulet"}
PRIMARY_LESS_TRINKETS = {"sm_deadmans_hand"}
KEPT_EFFECTS = {"sm_ravager", "sm_deadmans_hand"}
# Declared multipliers: the Blackrock gear review's S2 (a caster main-hand or bow below level 60 takes the 60-100 role
# cell on every tier so the ladder step is the budget curve's alone).
DECLARED_MULTS = {
    "sm_bloodletting_kris": 1.931, "sm_kirin_tor_spellblade": 1.931, "sm_hypnotic_blade": 1.931,
    "sm_hand_of_righteousness": 1.931, "sm_drillmasters_longbow": 0.405,
}


def stat_names(decl) -> set[str]:
    """The stats a declaration's shapes name, as the doc spells them (Stamina left out)."""
    names = set()
    for shape in (decl.primary, decl.secondary):
        if shape is None or shape == NULL_PRIMARY_SHAPE:
            continue
        for part in shape.replace(" (Solo)", "").replace(" (Any)", "").split("/"):
            names.add(part.strip())
    return names


class ScarletMonasteryItemsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load_items_registry()
        cls.decls = {e["id"]: e["_decl"] for e in cls.reg.item_declarations
                     if e["id"].startswith("sm_") and e["_decl"].ladder.name == "vanilla_dungeon"}

    # --- the list ------------------------------------------------------------------------------------------------

    def test_the_list(self):
        self.assertEqual(set(self.decls), set(LIST))
        self.assertEqual(len(self.decls), 64)
        counts = {}
        for boss, _, _ in LIST.values():
            counts[boss] = counts.get(boss, 0) + 1
        self.assertEqual(counts, BOSS_COUNT)
        bases = [d.base for d in self.decls.values() if d.base is not None]
        self.assertEqual(len(bases), len(set(bases)))  # one declaration per stock entry
        self.assertEqual(set(bases), {stock for _, stock, _ in LIST.values() if stock is not None})
        self.assertEqual(len(bases), 24)
        for key, decl in self.decls.items():
            self.assertEqual(decl.ladder.name, "vanilla_dungeon", key)
            self.assertEqual(decl.base, LIST[key][1], key)

    def test_the_doc_stats(self):
        for key, (_, _, stats) in LIST.items():
            wanted = {STAT_NAMES[s] for s in stats.split()}
            self.assertEqual(stat_names(self.decls[key]), wanted, key)
            decl = self.decls[key]
            # a primary shape names exactly one primary; a secondary shape only secondaries
            if decl.primary is not None:
                self.assertEqual(len(stat_names(decl) & PRIMARIES), 1, key)
            self.assertFalse(
                set(decl.secondary.replace(" (Solo)", "").replace(" (Any)", "").split("/")) & {
                    "Strength", "Agility", "Intellect", "Spirit"}, key)

    def test_new_items(self):
        for key, decl in self.decls.items():
            if decl.base is not None:
                continue
            self.assertEqual(dict(decl.columns).get("bonding"), 1, key)  # a new boss item binds on pickup
            self.assertIsNotNone(decl.like, key)
            self.assertIsNotNone(decl.name, key)
            self.assertEqual(decl.ilvl, BOSS_LEVEL[LIST[key][0]], key)  # the boss's table level
            self.assertIsNone(decl.required_level, key)  # defaults to the item level - 5
            self.assertIn(decl.quality, (None, Quality.RARE), key)

    def test_stock_levels(self):
        """A stock item keeps its stock level and required level; the moved ones take their new boss's."""
        for key, decl in self.decls.items():
            if decl.base is None:
                continue
            if key in MOVED:
                level, required = MOVED[key]
                self.assertEqual((decl.ilvl, decl.required_level), (level, required), key)
                self.assertEqual(level, BOSS_LEVEL[LIST[key][0]], key)
                self.assertEqual(required, level - 5, key)
            else:
                self.assertIsNone(decl.ilvl, key)
                self.assertIsNone(decl.required_level, key)

    def test_normal_is_rare(self):
        self.assertEqual(self.decls["sm_deadmans_hand"].quality, Quality.RARE)  # the one stock epic
        for key, decl in self.decls.items():
            if key != "sm_deadmans_hand":
                self.assertIn(decl.quality, (None, Quality.RARE), key)

    def test_shapes_exist(self):
        from lib import item_variants  # noqa: PLC0415

        _, catalog = item_variants.load_itemization_tables()
        known = {shape["name"] for shape in catalog.values()}
        for key, decl in self.decls.items():
            for name in (decl.primary, decl.secondary):
                if name is not None:
                    self.assertTrue(name in known or name in PENDING_SHAPES, f"{key}: {name}")
        used = {decl.secondary for decl in self.decls.values()}
        self.assertEqual(PENDING_SHAPES & used, PENDING_SHAPES)  # every pending shape is used, none is stale

    def test_jewelry_and_primary_less_trinkets(self):
        for key in JEWELRY | PRIMARY_LESS_TRINKETS:
            decl = self.decls[key]
            self.assertIsNone(decl.primary, key)
            self.assertEqual(decl.primary_share, 0, key)
        for key in JEWELRY:
            self.assertNotRegex(self.decls[key].secondary, r"Dodge|Parry|Block|MP5", key)
        for key, decl in self.decls.items():
            if decl.primary is None:
                self.assertIn(key, JEWELRY | PRIMARY_LESS_TRINKETS, key)
            self.assertNotEqual(decl.primary, NULL_PRIMARY_SHAPE, key)

    def test_sockets(self):
        socketed = {k: d.sockets for k, d in self.decls.items() if d.sockets}
        self.assertEqual(socketed, SOCKETS)
        self.assertEqual({k: d.socket_bonus for k, d in self.decls.items() if d.sockets}, BONUS)
        for key in TRINKETS | JEWELRY:
            self.assertIsNone(self.decls[key].sockets, key)  # trinkets never
        for key, decl in self.decls.items():
            self.assertEqual(decl.sockets is None, decl.socket_bonus is None, key)
        # exactly one socketed piece per boss
        per_boss = {}
        for key in SOCKETS:
            per_boss[LIST[key][0]] = per_boss.get(LIST[key][0], 0) + 1
        self.assertEqual(per_boss, {boss: 1 for boss in BOSS_COUNT})
        for key in ("sm_morbid_dawn", "sm_illusionary_rod"):  # the two-handers: red, then yellow (Crit)
            self.assertEqual(SOCKETS[key], (R, Y), key)
        for key in ("sm_tempered_girdle", "sm_captains_legguards"):  # tank gear: blue
            self.assertEqual(SOCKETS[key], (B,), key)

    def test_stock_edits(self):
        columns = {k: dict(d.columns) for k, d in self.decls.items()}
        self.assertEqual((columns["sm_gauntlets_of_divinity"]["subclass"],
                          columns["sm_gauntlets_of_divinity"]["Material"]), (4, 6))  # mail -> plate
        whistle = columns["sm_dog_whistle"]
        self.assertEqual((whistle["class"], whistle["subclass"], whistle["InventoryType"], whistle["Material"]),
                         (4, 0, 12, -1))  # a consumable becomes a trinket
        # Deadman's Hand: a stock ring, the doc's trinket (review M1); the minted tiers copy the column.
        self.assertEqual(columns["sm_deadmans_hand"]["InventoryType"], 12)
        self.assertEqual(columns["sm_kennelmasters_crossbow"]["ammo_type"], 0)
        self.assertEqual(columns["sm_drillmasters_longbow"]["ammo_type"], 0)
        self.assertEqual(self.decls["sm_dog_training_gloves"].extra_stamina, 0.25)  # the Leather Tank piece
        for key, decl in self.decls.items():
            if key != "sm_dog_training_gloves":
                self.assertEqual(decl.extra_stamina, 0.0, key)

    def test_kept_effects(self):
        self.assertEqual({k for k, d in self.decls.items() if d.keep_spells}, KEPT_EFFECTS)
        whistle = self.decls["sm_dog_whistle"].spells
        self.assertEqual(len(whistle), 1)
        # The stock row carries spellcharges -3; the trinket's Use has none and keeps the stock cooldowns.
        self.assertEqual((whistle[0].spell_id, whistle[0].trigger, whistle[0].scale, whistle[0].charges),
                         (9515, SpellTrigger.USE, None, 0))
        self.assertEqual((whistle[0].cooldown, whistle[0].category, whistle[0].category_cooldown),
                         (120000, 24, 60000))  # 2 minutes (designer ruling A3, 2026-11-20)
        for key, decl in self.decls.items():
            if key != "sm_dog_whistle":
                self.assertIsNone(decl.spells, key)  # no other item declares an effect

    def test_declared_multipliers(self):
        declared = {k: d.budget_mult for k, d in self.decls.items() if d.budget_mult is not None}
        self.assertEqual(declared, DECLARED_MULTS)

    def test_every_shape_stat_is_on_every_tier(self):
        """The materialized rows, not the declaration: every stat of the item's shapes has at least one point on every
        tier (blackrock gear REVIEW S3). The pending shapes are injected into the replayed tables while the
        integration has not added them yet (ids past the largest, never written anywhere)."""
        from unittest import mock  # noqa: PLC0415

        from lib import item_variants  # noqa: PLC0415

        real_loader = item_variants.load_itemization_tables

        def with_pending_shapes():
            tables, catalog = real_loader()
            known = {shape["name"] for shape in catalog.values()}
            missing = {sid: spec for sid, spec in PENDING_SHAPE_ROWS.items() if spec[0] not in known}
            if not missing:
                return tables, catalog
            _, shapes = item_variants._item_lib()
            next_id = max(shape_id for (shape_id,) in tables["item_shape"]) + 1
            for offset, (name, dist_id, stat_types, rules) in enumerate(missing.values()):
                shape_id = next_id + offset
                tables["item_shape"][(shape_id,)] = {"shape_id": shape_id, "name": name, "kind": 1, "dist_id": dist_id}
                for rank, stat_type in enumerate(stat_types, 1):
                    tables["item_shape_stat"][(shape_id, rank)] = {"stat_type": stat_type}
                for stat_type in rules:
                    tables["item_shape_rule"][(shape_id, 1, stat_type)] = {}
            return tables, shapes.catalog(tables)

        with mock.patch.object(item_variants, "load_itemization_tables", with_pending_shapes):
            _, catalog = item_variants.load_itemization_tables()
            by_name = {shape["name"]: shape for shape in catalog.values()}
            stats = materialized_tier_stats(self.decls)
        for key, decl in self.decls.items():
            wanted = set()
            for name in (decl.primary, decl.secondary):
                if name is not None:
                    wanted |= set(by_name[name]["stats"])
            for tier, got in stats[key].items():
                self.assertFalse(sorted(wanted - set(got)), f"{key} {tier}: a shape stat rounds to 0 ({got})")


if __name__ == "__main__":
    unittest.main()
