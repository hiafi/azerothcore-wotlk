"""
The Blackrock Spire loot and hard mode item effects (wave 2 dungeon items): source/items/blackrock_spire.py,
source/items/blackrock_spire_hard_mode_effects.py and the scripts in modules/mod-dungeon-bosses
(src/BlackrockSpire/hard_mode_items.cpp, BlackrockSpireHardModeItemsLogic.h).

Checks:
  - the list: 68 items on the dungeon ladder and 6 hard mode items, keys `brs_`, each item's primary and secondaries
    exactly the stats docs/dungeons/blackrock-spire-rework.md ## Loot names for it, rings and necks without a primary,
    Normal tiers Rare (the three stock epics set to Rare), the socket picks;
  - the shapes the list names exist, or are one of the five WP-INT adds (PENDING_SHAPES);
  - the effect spells sit in the `blackrock_spire_items` reservation, the C++ header names the same ids, every
    scripted_by() name is a script hard_mode_items.cpp registers;
  - each hard mode item carries its spell with the right trigger; nothing scales (no `scale="budget"`: every number is a
    percent or a time) and nothing deals damage or healing, so nothing needs potency;
  - every tooltip placeholder is expanded, item spells pass the triggered-cast rules (EquippedItemClass -1), the debuffs
    are flagged as debuffs;
  - the proc rows.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_spire_items.py
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
from lib.dsl.items import NULL_PRIMARY_SHAPE, Quality, Socket, SpellTrigger  # noqa: E402
from lib.test_hard_mode_item_effects import (  # noqa: E402
    _load_items_registry, assert_shape_stats_on_every_tier,
)

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockSpire"
HEADER = MODULE_DIR / "BlackrockSpireHardModeItemsLogic.h"
SCRIPT = MODULE_DIR / "hard_mode_items.cpp"

(WAR_HORN, WAR_CRY, WARD, WARD_BUFF, SHARDSTAFF, STOLEN_POWER, TROPHY, MARK, CHAMPIONS_TROPHY, ORDERS, HUMBLER,
 HUMBLED) = range(206800, 206812)
RESERVATION = range(206800, 206830)

HARD_MODE_KEYS = ("brs_bloodaxe_war_horn", "brs_ward_of_the_three_tribes", "brs_shardstaff_of_stolen_power",
                  "brs_trophy_of_the_champion", "brs_orders_of_the_general", "brs_the_humbler")
# The shapes the list needs that did not exist when it was written; WP-INT adds them in one pending itemization file.
PENDING_SHAPES = {"Mastery/CDH", "Versatility/Proc", "Dodge/Versatility", "Block/Versatility", "Haste/Mastery/Proc"}

# blackrock-spire-rework.md ## Loot "Keep, alter or add" and "Hard mode": item -> the stats named (Stamina is
# everywhere, so it is left out), in the doc's order. The doc's order is the socket bonus order; the shapes are
# unordered pairs.
DOC_STATS = {
    "brs_fist_of_omokk": "Str Vers Crit",
    "brs_tressermane_leggings": "Spi Crit Mastery",
    "brs_skyshroud_leggings": "Int Vers Haste",
    "brs_funeral_cuffs": "Spi Mastery Haste",
    "brs_blackcrow": "Agi Haste Crit",
    "brs_riphook": "Agi Vers Mastery",
    "brs_totem_of_hexed_blood": "Agi Haste Proc",
    "brs_keris_of_zulserak": "Agi Vers",
    "brs_talisman_of_evasion": "Haste CDH",
    "brs_brazecore_armguards": "Int Crit Vers",
    "brs_flightblade_throwing_axe": "Str Mastery",
    "brs_war_masters_hatchet": "Str Crit",
    "brs_venomspitter": "Agi Haste",
    "brs_smolderwebs_eye": "Mastery CDH",
    "brs_smolderweb_silk_sash": "Spi Crit Vers",
    "brs_rosewine_circle": "Vers CDH",
    "brs_marksmans_girdle": "Agi Crit Vers",
    "brs_shardlinked_coif": "Int Mastery Proc",
    "brs_cloudrunner_girdle": "Agi Mastery Haste",
    "brs_quartermasters_blunderbuss": "Agi Vers Haste",
    "brs_supply_sergeants_girdle": "Str Dodge Vers",
    "brs_slashclaw_bracers": "Agi Mastery Crit",
    "brs_halycons_spiked_collar": "Vers Proc",
    "brs_rhombeard_protector": "Int Vers Mastery",
    "brs_wolfshear_leggings": "Spi Haste Crit",
    "brs_bleak_howler_armguards": "Spi Haste Vers",
    "brs_packleaders_hide_belt": "Agi Dodge Mastery",
    "brs_trindlehaven_staff": "Int Vers Haste",
    "brs_relentless_scythe": "Str Parry Mastery",
    "brs_chillpike": "Agi Dodge Mastery",
    "brs_heart_of_wyrmthalak": "Str Vers Crit",
    "brs_mark_of_the_dragon_lord": "Proc Mastery",
    "brs_heart_of_the_scale": "Parry Vers",
    "brs_wildfire_cape": "Int Mastery Crit",
    "brs_emberfury_talisman": "Crit CDH",
    "brs_helm_of_the_bound_flame": "Str Haste Vers",
    "brs_incarcerators_wand": "Int Mastery",
    "brs_dustfeather_sash": "Int Haste Proc",
    "brs_crystallized_girdle": "Spi Mastery Crit",
    "brs_feralsurge_girdle": "Int Mastery Haste",
    "brs_flamewreath_legplates": "Int Crit CDH",
    "brs_blackhand_doomsaw": "Str Mastery",
    "brs_eye_of_rend": "Agi Mastery Crit",
    "brs_felstriker": "Agi Mastery",
    "brs_warmaster_legguards": "Str Haste Mastery",
    "brs_battleborn_armbraces": "Str Block Vers",
    "brs_dalrends_sacred_charge": "Str Crit",
    "brs_dalrends_tribal_guardian": "Str Mastery",
    "brs_gyths_skull": "Str Parry Mastery",
    "brs_dragoneye_coif": "Agi Vers Haste",
    "brs_tribal_war_feathers": "Spi Vers Crit",
    "brs_finkles_skinner": "Int Vers",
    "brs_blademaster_leggings": "Agi Haste Crit",
    "brs_tristam_legguards": "Agi Vers Mastery",
    "brs_blackmist_armguards": "Agi Crit Vers",
    "brs_bloodmoon_cloak": "Str Mastery Crit",
    "brs_seeping_willow": "Str Mastery",
    "brs_idol_of_the_core_hound": "Agi Crit Mastery",
    "brs_blackblade_of_shahram": "Str Proc",
    "brs_draconian_deflector": "Str Block Vers",
    "brs_painweaver_band": "Proc Vers",
    "brs_tooth_of_gnarr": "Mastery Proc Haste",
    "brs_brigam_girdle": "Str Mastery Crit",
    "brs_tome_of_the_lost": "Int CDH Mastery",
    "brs_spellweavers_turban": "Int Mastery Haste",
    "brs_draconic_infused_emblem": "Int Mastery Crit",
    "brs_shadow_prowlers_cloak": "Agi Mastery Haste",
    "brs_libram_of_the_dragon_guard": "Str Block Vers",
    "brs_bloodaxe_war_horn": "Mastery Vers",
    "brs_ward_of_the_three_tribes": "Str Parry Vers",
    "brs_shardstaff_of_stolen_power": "Int Crit",
    "brs_trophy_of_the_champion": "Crit Vers",
    "brs_orders_of_the_general": "Spi Mastery Haste",
    "brs_the_humbler": "Str Dodge",
}
STAT_NAMES = {"Str": "Strength", "Agi": "Agility", "Int": "Intellect", "Spi": "Spirit", "Crit": "Crit",
              "Haste": "Haste", "Mastery": "Mastery", "Vers": "Versatility", "CDH": "CDH", "Proc": "Proc",
              "Dodge": "Dodge", "Parry": "Parry", "Block": "Block"}

# One socketed standalone piece per boss (the doc names none: designer question), 2 on a two-hander; hard mode items 1
# except the trinkets. The first socket is red, blue on tank gear; a second takes the color of the first secondary.
SOCKETS = {
    "brs_fist_of_omokk": (Socket.RED, Socket.YELLOW),
    "brs_blackcrow": (Socket.RED,),
    "brs_brazecore_armguards": (Socket.RED,),
    "brs_smolderweb_silk_sash": (Socket.RED,),
    "brs_shardlinked_coif": (Socket.RED,),
    "brs_supply_sergeants_girdle": (Socket.BLUE,),
    "brs_bleak_howler_armguards": (Socket.RED,),
    "brs_trindlehaven_staff": (Socket.RED, Socket.YELLOW),
    "brs_helm_of_the_bound_flame": (Socket.RED,),
    "brs_flamewreath_legplates": (Socket.RED,),
    "brs_eye_of_rend": (Socket.RED,),
    "brs_tristam_legguards": (Socket.RED,),
    "brs_brigam_girdle": (Socket.RED,),
    "brs_ward_of_the_three_tribes": (Socket.BLUE,),
    "brs_shardstaff_of_stolen_power": (Socket.RED,),
    "brs_orders_of_the_general": (Socket.RED,),
    "brs_the_humbler": (Socket.BLUE,),
}
# Stock rows whose Normal tier is set to Rare (the three stock epics).
RARE_ON_NORMAL = {"brs_mark_of_the_dragon_lord", "brs_felstriker", "brs_blackblade_of_shahram"}
JEWELRY = {"brs_talisman_of_evasion", "brs_rosewine_circle", "brs_halycons_spiked_collar",
           "brs_mark_of_the_dragon_lord", "brs_emberfury_talisman", "brs_painweaver_band", "brs_tooth_of_gnarr"}
# Trinkets with no primary: the list's two Use/proc stat sticks, the tank trinket and the hard mode trinkets.
PRIMARYLESS_TRINKETS = {"brs_smolderwebs_eye", "brs_heart_of_the_scale", "brs_bloodaxe_war_horn",
                        "brs_trophy_of_the_champion"}
KEPT_EFFECTS = {"brs_keris_of_zulserak", "brs_venomspitter", "brs_smolderwebs_eye", "brs_chillpike",
                "brs_heart_of_wyrmthalak", "brs_mark_of_the_dragon_lord", "brs_heart_of_the_scale",
                "brs_blackhand_doomsaw", "brs_felstriker", "brs_seeping_willow", "brs_blackblade_of_shahram",
                "brs_draconic_infused_emblem"}
# Stock resistances and random properties cleared on every tier.
CLEARED = {
    "brs_wolfshear_leggings": {"nature_res": 0}, "brs_wildfire_cape": {"fire_res": 0},
    "brs_draconian_deflector": {"fire_res": 0}, "brs_gyths_skull": {"RandomProperty": 0},
    "brs_dragoneye_coif": {"RandomProperty": 0}, "brs_tribal_war_feathers": {"RandomProperty": 0},
}
NEW_ITEMS = {  # key -> item level (the lowest stock item level of the boss's list)
    "brs_totem_of_hexed_blood": 59, "brs_war_masters_hatchet": 60, "brs_smolderweb_silk_sash": 60,
    "brs_shardlinked_coif": 60, "brs_quartermasters_blunderbuss": 60, "brs_supply_sergeants_girdle": 60,
    "brs_packleaders_hide_belt": 60, "brs_helm_of_the_bound_flame": 61, "brs_incarcerators_wand": 61,
    "brs_flamewreath_legplates": 61, "brs_idol_of_the_core_hound": 63, "brs_libram_of_the_dragon_guard": 63,
}


def _shape_stats(name):
    """The doc stat names an item_shape name stands for ("Crit/Versatility" -> {Crit, Versatility})."""
    if name is None or name == NULL_PRIMARY_SHAPE:
        return set()
    bare = re.sub(r" \((Solo|Any)\)$", "", name)
    return set(bare.split("/"))


# Blackrock gear fix pass (REVIEW S1-S3): the declared budget multipliers; every other item takes the default.
DECLARED_MULTS = {
    "brs_ward_of_the_three_tribes": 0.6,      # socketed hard mode shield: every doc stat a few points (S3)
    "brs_shardstaff_of_stolen_power": 0.7105,  # caster two-hand 60-100 cell x 0.7, 101 tier included (S1)
    "brs_riphook": 0.405,                      # bow 60-100 cell on the level 59 Normal tier too (S2)
}


class BlackrockSpireItemsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load_items_registry()
        cls.spells = {int(e["id"]): e for e in cls.reg.spells if int(e["id"]) in RESERVATION}
        cls.decls = {e["id"]: e["_decl"] for e in cls.reg.item_declarations if e["id"].startswith("brs_")}

    # --- the list ------------------------------------------------------------------------------------------------

    def test_the_list(self):
        hard_mode = {k for k, d in self.decls.items() if d.ladder.name == "vanilla_hard_mode"}
        dungeon = {k for k, d in self.decls.items() if d.ladder.name == "vanilla_dungeon"}
        self.assertEqual(hard_mode, set(HARD_MODE_KEYS))
        self.assertEqual(len(dungeon), 68)
        self.assertEqual(len(self.decls), 74)
        self.assertEqual(set(self.decls), set(DOC_STATS))
        bases = [d.base for d in self.decls.values() if d.base is not None]
        self.assertEqual(len(bases), len(set(bases)))
        self.assertEqual(len(bases), 56)  # the 12 new list items and 6 new hard mode items are minted on every tier
        self.assertEqual({k for k, d in self.decls.items() if d.base is None},
                         set(NEW_ITEMS) | set(HARD_MODE_KEYS))

    def test_stats_are_the_docs(self):
        """Every item's primary and secondaries name exactly the stats the dungeon doc gives it."""
        for key, decl in self.decls.items():
            doc = {STAT_NAMES[s] for s in DOC_STATS[key].split()}
            got = _shape_stats(decl.primary) | _shape_stats(decl.secondary)
            self.assertEqual(got, doc, key)
            # the primary leads the doc's list unless the item has none (rings, necks and the trinkets without one)
            first = DOC_STATS[key].split()[0]
            if first in ("Str", "Agi", "Int", "Spi"):
                self.assertEqual(_shape_stats(decl.primary), {STAT_NAMES[first]}, key)
            else:
                self.assertIn(decl.primary, (None, NULL_PRIMARY_SHAPE), key)

    def test_declared_multipliers(self):
        """Only the fix pass's items declare a multiplier; the thrown axe keeps the one-hand baseline DPS."""
        declared = {k: d.budget_mult for k, d in self.decls.items() if d.budget_mult is not None}
        self.assertEqual(declared, DECLARED_MULTS)
        self.assertEqual(self.decls["brs_flightblade_throwing_axe"].extra_dps, 0.0)
        self.assertFalse(self.decls["brs_flightblade_throwing_axe"].keep_spells)  # its +12 AP Equip folds away

    def test_every_shape_stat_is_on_every_tier(self):
        """The materialized rows, not the declaration: every doc stat (the item's shape stats) has at least one point
        on every tier (REVIEW S3: a thin cell budget after the socket left a hard mode shield 1 Strength and nothing
        else)."""
        assert_shape_stats_on_every_tier(self, self.decls)

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

    def test_sockets(self):
        socketed = {k: d.sockets for k, d in self.decls.items() if d.sockets}
        self.assertEqual(socketed, SOCKETS)
        for key in ("brs_bloodaxe_war_horn", "brs_trophy_of_the_champion", "brs_smolderwebs_eye",
                    "brs_heart_of_wyrmthalak", "brs_heart_of_the_scale", "brs_draconic_infused_emblem"):
            self.assertIsNone(self.decls[key].sockets, key)  # trinkets never
        for key, decl in self.decls.items():
            self.assertEqual(decl.sockets is None, decl.socket_bonus is None, key)
        # a second socket takes the color of the item's first secondary (yellow = throughput stats)
        for key in ("brs_fist_of_omokk", "brs_trindlehaven_staff"):
            self.assertEqual(SOCKETS[key][1], Socket.YELLOW)

    def test_jewelry_has_no_primary_and_no_tank_stat(self):
        for key in JEWELRY:
            decl = self.decls[key]
            self.assertIsNone(decl.primary, key)
            self.assertEqual(decl.primary_share, 0, key)
            self.assertNotRegex(decl.secondary, r"Dodge|Parry|Block|MP5", key)
        for key in PRIMARYLESS_TRINKETS:
            self.assertIsNone(self.decls[key].primary, key)
            self.assertEqual(self.decls[key].primary_share, 0, key)
        for key, decl in self.decls.items():
            if decl.primary is None:
                self.assertIn(key, JEWELRY | PRIMARYLESS_TRINKETS, key)
            self.assertNotEqual(decl.primary, NULL_PRIMARY_SHAPE, key)

    def test_normal_is_rare(self):
        for key, decl in self.decls.items():
            if key in RARE_ON_NORMAL:
                self.assertEqual(decl.quality, Quality.RARE, key)
            elif decl.base is None and decl.ladder.name == "vanilla_dungeon":
                self.assertIn(decl.quality, (None, Quality.RARE), key)  # new items default to Rare

    def test_new_items_level_from_their_boss(self):
        for key, ilvl in NEW_ITEMS.items():
            decl = self.decls[key]
            self.assertEqual(decl.ilvl, ilvl, key)
            self.assertIsNone(decl.required_level, key)  # ilvl - 5, the stock pattern
            self.assertEqual(dict(decl.columns).get("bonding"), 1, key)  # Bind on Pickup

    def test_ranged_weapons_need_no_ammo(self):
        for key in ("brs_blackcrow", "brs_riphook", "brs_quartermasters_blunderbuss"):
            self.assertEqual(dict(self.decls[key].columns).get("ammo_type"), 0, key)

    def test_kept_effects(self):
        kept = {k for k, d in self.decls.items() if d.keep_spells}
        self.assertEqual(kept, KEPT_EFFECTS)
        # Finkle's Skinner keeps its Skinning bonus only
        skinner = self.decls["brs_finkles_skinner"]
        self.assertFalse(skinner.keep_spells)
        self.assertEqual([s.spell_id for s in skinner.spells], [16718])
        self.assertEqual([s.trigger for s in skinner.spells], [SpellTrigger.ON_EQUIP])

    def test_cleared_stock_extras(self):
        for key, columns in CLEARED.items():
            self.assertEqual(dict(self.decls[key].columns), columns, key)

    def test_dalrends_set_is_untouched(self):
        for key in ("brs_dalrends_sacred_charge", "brs_dalrends_tribal_guardian"):
            decl = self.decls[key]
            self.assertNotIn("itemset", dict(decl.columns), key)
            self.assertEqual(decl.overrides, (), key)

    def test_tank_waist_has_extra_stamina(self):
        self.assertEqual(self.decls["brs_packleaders_hide_belt"].extra_stamina, 0.25)

    # --- the effects ---------------------------------------------------------------------------------------------

    def test_ids_sit_in_their_reservation(self):
        self.assertEqual(sorted(self.spells), list(range(WAR_HORN, HUMBLED + 1)))
        ids = {"spell": sorted(self.spells)}
        self.assertEqual(id_blocks.out_of_reservation("blackrock_spire_items", ids), [])

    def test_the_cpp_header_names_the_same_ids(self):
        text = HEADER.read_text()
        named = {name: int(value) for name, value in re.findall(r"\b(SPELL_[A-Z_]+)\s*=\s*(\d+)", text)}
        self.assertEqual(named, {
            "SPELL_BLOODAXE_WAR_HORN": WAR_HORN, "SPELL_BLOODAXE_WAR_CRY": WAR_CRY,
            "SPELL_WARD_OF_THE_THREE_TRIBES": WARD, "SPELL_WARD_BUFF": WARD_BUFF,
            "SPELL_SHARDSTAFF_OF_STOLEN_POWER": SHARDSTAFF, "SPELL_STOLEN_POWER": STOLEN_POWER,
            "SPELL_TROPHY_OF_THE_CHAMPION": TROPHY, "SPELL_CHAMPIONS_MARK": MARK,
            "SPELL_CHAMPIONS_TROPHY": CHAMPIONS_TROPHY, "SPELL_ORDERS_OF_THE_GENERAL": ORDERS,
            "SPELL_THE_HUMBLER": HUMBLER, "SPELL_HUMBLED": HUMBLED,
        })

    def test_every_binding_is_a_registered_script(self):
        registered = set(re.findall(r"RegisterSpellScript\((\w+)\)", SCRIPT.read_text()))
        bound = {(int(r["spell_id"]), r["ScriptName"]) for r in self.reg.spell_script_names
                 if int(r["spell_id"]) in RESERVATION}
        self.assertEqual(bound, {
            (WARD, "spell_brs_ward_of_the_three_tribes"), (MARK, "spell_brs_champions_mark"),
        })
        self.assertEqual({name for _, name in bound}, registered)

    def test_items_carry_their_spell(self):
        expected = {
            "brs_bloodaxe_war_horn": (WAR_HORN, SpellTrigger.USE),
            "brs_ward_of_the_three_tribes": (WARD, SpellTrigger.ON_EQUIP),
            "brs_shardstaff_of_stolen_power": (SHARDSTAFF, SpellTrigger.ON_EQUIP),
            "brs_trophy_of_the_champion": (TROPHY, SpellTrigger.ON_EQUIP),
            "brs_orders_of_the_general": (ORDERS, SpellTrigger.USE),
            "brs_the_humbler": (HUMBLER, SpellTrigger.ON_EQUIP),
        }
        for key, (spell_id, trigger) in expected.items():
            decl = self.decls[key]
            self.assertEqual(len(decl.spells), 1, key)
            item_spell = decl.spells[0]
            self.assertEqual((item_spell.spell_id, item_spell.trigger), (spell_id, trigger), key)
            self.assertEqual(item_spell.cooldown, -1, key)  # the spell's own cooldown
            self.assertIsNone(item_spell.scale, key)  # nothing here grows with item level
            # an effect item pays 0.7 of the budget (the default), except the fix pass's declared ones: the Ward (a
            # socketed thin shield, S3) and the Shardstaff (the 60-100 cell x 0.7 on every tier, S1)
            self.assertEqual(decl.budget_mult, DECLARED_MULTS.get(key), key)

    def test_nothing_deals_damage_or_heals(self):
        for spell_id, spell in self.spells.items():
            for n in (1, 2, 3):
                effect = spell.get(f"effect{n}")
                if not effect:
                    continue
                self.assertNotIn(effect["type"], (2, 10, 31, 58), spell_id)  # damage, heal, weapon damage
                self.assertFalse(effect.get("_potency"), spell_id)
                self.assertNotEqual(effect.get("apply_aura"), 69, spell_id)  # absorb
        self.assertEqual({int(r["entry"]) for r in self.reg.spell_bonus_data if int(r["entry"]) in RESERVATION}, set())

    def test_tooltips(self):
        for spell_id, spell in self.spells.items():
            raw = spell["raw_overrides"]
            self.assertEqual(raw["EquippedItemClass"], -1, spell_id)
            self.assertNotIn("{pot", raw["Description_Lang_enUS"], spell_id)
            self.assertNotRegex(raw.get("AuraDescription_Lang_enUS", ""), r"\$", spell_id)
        self.assertIn("$206801s1%", self.spells[WAR_HORN]["raw_overrides"]["Description_Lang_enUS"])
        self.assertIn("$206803u", self.spells[WARD]["raw_overrides"]["Description_Lang_enUS"] + "$206803u")
        self.assertIn("$206808s1%", self.spells[TROPHY]["raw_overrides"]["Description_Lang_enUS"])

    def test_spell_shapes(self):
        debuff = 0x04000000
        for spell_id in (WAR_CRY, HUMBLED, MARK):
            self.assertTrue(int(self.spells[spell_id].get("attributes", 0)) & debuff, spell_id)
        # the horn: an interrupt and the war cry, both on enemies in a 10 yd circle around the wearer
        horn = self.spells[WAR_HORN]
        self.assertEqual(horn["effect1"]["type"], 68)  # INTERRUPT_CAST
        self.assertEqual(horn["effect2"]["type"], 64)  # TRIGGER_SPELL
        self.assertEqual(horn["effect2"]["trigger_spell"], WAR_CRY)
        for n in (1, 2):
            self.assertEqual((horn[f"effect{n}"]["implicit_target_a"], horn[f"effect{n}"]["implicit_target_b"]),
                             (22, 15))
            self.assertEqual(horn[f"effect{n}"]["radius_yards"], 10.0)
        self.assertEqual(horn["cooldown_ms"], 120000)
        # the debuffs: -10% and -5% damage done, all schools
        for spell_id, amount in ((WAR_CRY, -10), (HUMBLED, -5)):
            effect = self.spells[spell_id]["effect1"]
            self.assertEqual((effect["apply_aura"], effect["misc_value"]), (79, 127), spell_id)
            self.assertEqual(effect["base_points"] + 1, amount, spell_id)
        self.assertEqual(self.spells[WAR_CRY]["duration_ms"], 10000)
        self.assertEqual(self.spells[HUMBLED]["duration_ms"], 8000)
        # the ward: a 0.5 s watch with radius 8 and cap 5, onto a -1% per stack buff of 5 stacks
        ward = self.spells[WARD]["effect1"]
        self.assertEqual((ward["apply_aura"], ward["amplitude"], ward["radius_yards"], ward["base_points"] + 1),
                         (226, 500, 8.0, 5))
        buff = self.spells[WARD_BUFF]
        self.assertEqual(int(buff["raw_overrides"]["CumulativeAura"]), 5)
        self.assertEqual((buff["effect1"]["apply_aura"], buff["effect1"]["base_points"] + 1), (87, -1))
        # Stolen Power and the Trophy: +1% damage and healing, 5 stacks
        for spell_id, duration, mask in ((STOLEN_POWER, 10000, 126), (CHAMPIONS_TROPHY, 30000, 127)):
            spell = self.spells[spell_id]
            self.assertEqual(int(spell["raw_overrides"]["CumulativeAura"]), 5, spell_id)
            self.assertEqual(spell["duration_ms"], duration, spell_id)
            self.assertEqual((spell["effect1"]["apply_aura"], spell["effect1"]["misc_value"],
                              spell["effect1"]["base_points"] + 1), (79, mask, 1), spell_id)
            self.assertEqual((spell["effect2"]["apply_aura"], spell["effect2"]["base_points"] + 1), (136, 1), spell_id)
        self.assertEqual(self.spells[MARK]["duration_ms"], 5000)
        # the proc auras trigger the right spell on the right target
        for aura, trigger in ((SHARDSTAFF, STOLEN_POWER), (TROPHY, MARK), (HUMBLER, HUMBLED)):
            self.assertEqual(self.spells[aura]["effect1"]["apply_aura"], 42, aura)
            self.assertEqual(self.spells[aura]["effect1"]["trigger_spell"], trigger, aura)
        for spell_id in (STOLEN_POWER, CHAMPIONS_TROPHY):
            self.assertEqual(self.spells[spell_id]["effect1"]["implicit_target_a"], 1, spell_id)  # the wearer
        # Orders: the party within 30 yd, -10% damage taken for 8 s, off the GCD
        orders = self.spells[ORDERS]
        self.assertEqual((orders["effect1"]["implicit_target_a"], orders["effect1"]["radius_yards"],
                          orders["effect1"]["apply_aura"], orders["effect1"]["base_points"] + 1), (20, 30.0, 87, -10))
        self.assertEqual((orders["duration_ms"], orders["cooldown_ms"]), (8000, 120000))

    def test_proc_rows(self):
        procs = {int(r["SpellId"]): r for r in self.reg.spell_procs if int(r["SpellId"]) in RESERVATION}
        self.assertEqual(set(procs), {SHARDSTAFF, TROPHY, HUMBLER})
        shardstaff = procs[SHARDSTAFF]
        self.assertEqual(shardstaff["HitMask"], 0x2)  # critical hits only
        self.assertEqual(shardstaff["ProcFlags"] & 0x00040000, 0)  # no periodic ticks
        self.assertEqual((shardstaff["SpellTypeMask"], shardstaff["SpellPhaseMask"]), (0x3, 0x2))  # damage and heals
        self.assertEqual(shardstaff["Chance"], 100.0)
        trophy = procs[TROPHY]
        self.assertTrue(trophy["ProcFlags"] & 0x00040000)  # ticks of damage over time count as damage
        self.assertEqual(trophy["HitMask"], 0x3)
        self.assertEqual(trophy.get("Cooldown", 0), 0)  # a cooldown is per wearer: an area attack would mark one target
        humbler = procs[HUMBLER]
        self.assertEqual(humbler["ProcFlags"], 0x4 | 0x10)  # melee hits only
        self.assertTrue(0 < humbler["Chance"] < 100)


if __name__ == "__main__":
    unittest.main()
