"""
The Stratholme loot and hard mode item effects (wave 1 dungeon items): source/items/stratholme.py,
source/items/stratholme_hard_mode_effects.py and the scripts in modules/mod-dungeon-bosses (src/Stratholme/
hard_mode_items.cpp, StratholmeHardModeItemsLogic.h).

Checks:
  - the list: 73 items on the dungeon ladder and 6 hard mode items, keys `strat_`, the socket picks of the dungeon
    doc, rings and necks without a primary, Normal tiers Rare (the stock greens and epics set to Rare);
  - the effect spells sit in the `stratholme_items` reservation, the C++ header names the same ids, every
    scripted_by() name is a script hard_mode_items.cpp registers;
  - each hard mode item carries its spell with the right trigger, scaled ("budget") exactly where the designer scales
    by item level;
  - damage and absorbs come from potency (the lie is the one declared exception), every tooltip placeholder is
    expanded, item spells pass the triggered-cast rules (EquippedItemClass -1, a damage spell is never DmgClass NONE);
  - the proc rows.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_stratholme_hard_mode_items.py
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
from lib.test_hard_mode_item_effects import _load_items_registry  # noqa: E402

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Stratholme"
HEADER = MODULE_DIR / "StratholmeHardModeItemsLogic.h"
SCRIPT = MODULE_DIR / "hard_mode_items.cpp"

(SIGNET, SWARM, DUST, TOME, LIE, LOCKET, WARD, LOCKOUT, BLADE, CONDEMNED, SPUR, TRAMPLE,
 LOOK) = range(205660, 205673)
RESERVATION = range(205660, 205700)

SCHOOL_DAMAGE = 2
APPLY_AURA = 6
SCHOOL_ABSORB = 69

HARD_MODE_KEYS = ("strat_carrion_signet", "strat_dust_of_the_nathrezim", "strat_two_faced_tome",
                  "strat_ysidas_locket", "strat_blade_of_the_condemned", "strat_deathchargers_spur")
# stratholme-rework.md "Sockets" (approved 2026-11-06): item -> socket colors.
SOCKETS = {
    "strat_mask_of_the_unforgiven": (Socket.RED,),
    "strat_rainbow_girdle": (Socket.RED,),
    "strat_grimgore_noose": (Socket.RED,),
    "strat_gauntlets_of_the_zealot": (Socket.RED,),
    "strat_helm_of_the_new_moon": (Socket.RED,),
    "strat_pyrewatch_coif": (Socket.RED,),
    "strat_grand_crusaders_helm": (Socket.BLUE, Socket.BLUE),
    "strat_demonshear": (Socket.RED,),
    "strat_crimson_felt_hat": (Socket.RED,),
    "strat_windshrieker_pauldrons": (Socket.RED,),
    "strat_acid_etched_pauldrons": (Socket.RED,),
    "strat_darkbind_fingers": (Socket.RED,),
    "strat_soulstealer_mantle": (Socket.RED,),
    "strat_helm_of_the_executioner": (Socket.RED, Socket.YELLOW),
    "strat_runeblade_of_baron_rivendare": (Socket.RED, Socket.YELLOW),
    "strat_carrion_signet": (Socket.RED,),
    "strat_two_faced_tome": (Socket.RED,),
    "strat_ysidas_locket": (Socket.RED,),
    "strat_blade_of_the_condemned": (Socket.RED,),
}
# Stock rows whose Normal tier is set to Rare (resist greens and the two epics).
RARE_ON_NORMAL = {"strat_windshrieker_pauldrons", "strat_banshees_touch", "strat_darkspinner_claws",
                  "strat_acid_etched_pauldrons", "strat_darkbind_fingers", "strat_flamescarred_girdle",
                  "strat_book_of_the_dead", "strat_runeblade_of_baron_rivendare"}
JEWELRY = {"strat_dianas_pearl_necklace", "strat_star_of_mystaria", "strat_anastari_heirloom", "strat_band_of_flesh",
           "strat_seal_of_rivendare", "strat_carrion_signet", "strat_ysidas_locket"}
KEPT_EFFECTS = {"strat_soul_breaker", "strat_piccolo_of_the_flaming_fire", "strat_the_cruel_hand_of_timmy",
                "strat_cannonball_runner", "strat_demonshear", "strat_book_of_the_dead", "strat_crest_of_retribution",
                "strat_ramsteins_lightning_bolts", "strat_skullforge_reaver", "strat_runeblade_of_baron_rivendare"}


class StratholmeItemsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load_items_registry()
        cls.spells = {int(e["id"]): e for e in cls.reg.spells if int(e["id"]) in RESERVATION}
        cls.decls = {e["id"]: e["_decl"] for e in cls.reg.item_declarations if e["id"].startswith("strat_")}

    # --- the list ------------------------------------------------------------------------------------------------

    def test_the_list(self):
        hard_mode = {k for k, d in self.decls.items() if d.ladder.name == "vanilla_hard_mode"}
        dungeon = {k for k, d in self.decls.items() if d.ladder.name == "vanilla_dungeon"}
        self.assertEqual(hard_mode, set(HARD_MODE_KEYS))
        self.assertEqual(len(dungeon), 73)
        self.assertEqual(len(self.decls), 79)
        bases = [d.base for d in self.decls.values() if d.base is not None]
        self.assertEqual(len(bases), len(set(bases)))
        self.assertEqual(len(bases), 64)  # 9 new list items and 6 new hard mode items are minted on every tier

    def test_sockets(self):
        socketed = {k: d.sockets for k, d in self.decls.items() if d.sockets}
        self.assertEqual(socketed, SOCKETS)
        for key in ("strat_dust_of_the_nathrezim", "strat_deathchargers_spur", "strat_piccolo_of_the_flaming_fire",
                    "strat_cannonball_runner", "strat_ramsteins_lightning_bolts"):
            self.assertIsNone(self.decls[key].sockets, key)  # trinkets never
        for key, decl in self.decls.items():
            self.assertEqual(decl.sockets is None, decl.socket_bonus is None, key)

    def test_jewelry_has_no_primary_and_no_tank_stat(self):
        for key in JEWELRY:
            decl = self.decls[key]
            self.assertIsNone(decl.primary, key)
            self.assertEqual(decl.primary_share, 0, key)
            self.assertNotRegex(decl.secondary, r"Dodge|Parry|Block|MP5", key)
        for key, decl in self.decls.items():
            if decl.primary is None and key not in JEWELRY:
                self.assertIn(key, {"strat_piccolo_of_the_flaming_fire", "strat_dust_of_the_nathrezim",
                                    "strat_deathchargers_spur"}, key)  # the primary-less trinkets
            self.assertNotEqual(decl.primary, NULL_PRIMARY_SHAPE, key)

    def test_normal_is_rare(self):
        for key, decl in self.decls.items():
            if key in RARE_ON_NORMAL:
                self.assertEqual(decl.quality, Quality.RARE, key)
            elif decl.base is None and decl.ladder.name == "vanilla_dungeon":
                self.assertIn(decl.quality, (None, Quality.RARE), key)  # new items default to Rare

    def test_kept_effects(self):
        kept = {k for k, d in self.decls.items() if d.keep_spells}
        self.assertEqual(kept, KEPT_EFFECTS)
        self.assertEqual(self.decls["strat_piccolo_of_the_flaming_fire"].budget_mult, 1.0)  # full stat budget

    # --- the effects ---------------------------------------------------------------------------------------------

    def test_ids_sit_in_their_reservation(self):
        self.assertEqual(sorted(self.spells), list(range(SIGNET, LOOK + 1)))
        ids = {"spell": sorted(self.spells)}
        self.assertEqual(id_blocks.out_of_reservation("stratholme_items", ids), [])

    def test_the_cpp_header_names_the_same_ids(self):
        text = HEADER.read_text()
        named = {name: int(value) for name, value in re.findall(r"\b(SPELL_[A-Z_]+)\s*=\s*(\d+)", text)}
        self.assertEqual(named, {
            "SPELL_CARRION_SIGNET": SIGNET, "SPELL_CARRION_SWARM": SWARM, "SPELL_DUST_OF_THE_NATHREZIM": DUST,
            "SPELL_TWO_FACED_TOME": TOME, "SPELL_THE_LIE": LIE, "SPELL_YSIDAS_LOCKET": LOCKET,
            "SPELL_YSIDAS_WARD": WARD, "SPELL_YSIDAS_LOCKET_LOCKOUT": LOCKOUT,
            "SPELL_BLADE_OF_THE_CONDEMNED": BLADE, "SPELL_CONDEMNED": CONDEMNED,
            "SPELL_DEATHCHARGERS_SPUR": SPUR, "SPELL_DEATHCHARGER_TRAMPLE": TRAMPLE,
            "SPELL_SPECTRAL_DEATHCHARGER": LOOK,
        })

    def test_every_binding_is_a_registered_script(self):
        registered = set(re.findall(r"RegisterSpellScript\((\w+)\)", SCRIPT.read_text()))
        bound = {(int(r["spell_id"]), r["ScriptName"]) for r in self.reg.spell_script_names
                 if int(r["spell_id"]) in RESERVATION}
        self.assertEqual(bound, {
            (DUST, "spell_strat_dust_of_the_nathrezim"), (TOME, "spell_strat_two_faced_tome"),
            (LOCKET, "spell_strat_ysidas_locket"), (BLADE, "spell_strat_blade_of_the_condemned"),
            (SPUR, "spell_strat_deathchargers_spur"),
        })
        self.assertEqual({name for _, name in bound}, registered)

    def test_items_carry_their_spell(self):
        expected = {
            "strat_carrion_signet": (SIGNET, SpellTrigger.ON_EQUIP, "budget"),
            "strat_dust_of_the_nathrezim": (DUST, SpellTrigger.USE, None),
            "strat_two_faced_tome": (TOME, SpellTrigger.ON_EQUIP, None),
            "strat_ysidas_locket": (LOCKET, SpellTrigger.ON_EQUIP, "budget"),
            "strat_blade_of_the_condemned": (BLADE, SpellTrigger.ON_EQUIP, None),
            "strat_deathchargers_spur": (SPUR, SpellTrigger.USE, "budget"),
        }
        for key, (spell_id, trigger, scale) in expected.items():
            decl = self.decls[key]
            self.assertEqual(len(decl.spells), 1, key)
            item_spell = decl.spells[0]
            self.assertEqual((item_spell.spell_id, item_spell.trigger, item_spell.scale), (spell_id, trigger, scale),
                             key)
            self.assertEqual(item_spell.cooldown, -1, key)  # the spell's own cooldown
        self.assertEqual(self.decls["strat_dust_of_the_nathrezim"].budget_mult, 1.0)  # full stat budget (designer)

    def test_damage_and_absorbs_come_from_potency(self):
        for spell_id in (SWARM, TRAMPLE):
            effect = self.spells[spell_id]["effect1"]
            self.assertEqual(effect["type"], SCHOOL_DAMAGE)
            self.assertTrue(effect.get("_potency"), spell_id)
            self.assertNotEqual(int(self.spells[spell_id]["raw_overrides"]["DefenseType"]), 0, spell_id)
        ward = self.spells[WARD]["effect1"]
        self.assertEqual((ward["type"], ward["apply_aura"]), (APPLY_AURA, SCHOOL_ABSORB))
        self.assertTrue(ward.get("_potency"))
        lie = self.spells[LIE]
        self.assertEqual(lie["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertFalse(lie["effect1"].get("_potency"))  # a share of the heal (potency_excluded)
        self.assertNotEqual(int(lie["raw_overrides"]["DefenseType"]), 0)
        self.assertEqual({int(r["entry"]) for r in self.reg.spell_bonus_data if int(r["entry"]) in RESERVATION},
                         {SWARM, TRAMPLE})
        # the swarm and the trample differ, so their tooltip numbers never join one copy family
        self.assertNotEqual(self.spells[SWARM]["effect1"]["_potency"], self.spells[TRAMPLE]["effect1"]["_potency"])

    def test_tooltips(self):
        for spell_id, spell in self.spells.items():
            raw = spell["raw_overrides"]
            self.assertEqual(raw["EquippedItemClass"], -1, spell_id)
            self.assertNotIn("{pot", raw["Description_Lang_enUS"], spell_id)
            self.assertNotRegex(raw.get("AuraDescription_Lang_enUS", ""), r"\$", spell_id)
        self.assertIn("$205667d", self.spells[LOCKET]["raw_overrides"]["Description_Lang_enUS"])
        self.assertIn("$205669s1%", self.spells[BLADE]["raw_overrides"]["Description_Lang_enUS"])

    def test_spell_shapes(self):
        self.assertEqual(self.spells[SIGNET]["effect1"]["trigger_spell"], SWARM)
        self.assertEqual(self.spells[SWARM]["effect1"]["implicit_target_a"], 24)  # a cone in front of the wearer
        self.assertEqual(int(self.spells[DUST]["raw_overrides"]["Mechanic"]), 10)  # sleep
        self.assertEqual(int(self.spells[DUST]["raw_overrides"]["AuraInterruptFlags"]) & 0x2, 0x2)  # damage wakes
        self.assertEqual(self.spells[DUST]["duration_ms"], 20000)
        self.assertEqual(int(self.spells[CONDEMNED]["raw_overrides"]["CumulativeAura"]), 5)
        self.assertEqual(self.spells[LOCKOUT]["duration_ms"], 60000)
        self.assertEqual(self.spells[SPUR]["duration_ms"], 6000)
        self.assertEqual(self.spells[LOOK]["effect1"]["misc_value"], 30542)  # Rivendare's Deathcharger

    def test_proc_rows(self):
        procs = {int(r["SpellId"]): r for r in self.reg.spell_procs if int(r["SpellId"]) in RESERVATION}
        self.assertEqual(set(procs), {SIGNET, TOME, BLADE})
        signet = procs[SIGNET]
        self.assertEqual(signet["ProcFlags"] & 0x00040000, 0)  # no periodic ticks
        self.assertEqual(signet["HitMask"], 0x3)
        self.assertGreater(signet["Cooldown"], 0)
        self.assertTrue(0 < signet["Chance"] < 100)
        tome = procs[TOME]
        self.assertEqual((tome["SpellTypeMask"], tome["SpellPhaseMask"]), (0x2, 0x2))  # landed heals
        self.assertTrue(0 < tome["Chance"] < 100)
        blade = procs[BLADE]
        self.assertEqual(blade["ProcFlags"], 0x4 | 0x10)  # melee hits only
        self.assertEqual(blade["Chance"], 100.0)


if __name__ == "__main__":
    unittest.main()
