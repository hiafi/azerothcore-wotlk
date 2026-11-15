"""
The Blackrock Depths loot and hard mode item effects (wave 2 dungeon items): source/items/blackrock_depths.py,
source/items/blackrock_depths_hard_mode_effects.py, source/npcs/blackrock_depths/hard_mode_items.py and the scripts
in modules/mod-dungeon-bosses (src/BlackrockDepths/hard_mode_items.cpp, BlackrockDepthsHardModeItemsLogic.h).

Checks:
  - the list: 75 items on the dungeon ladder and 12 hard mode items, keys `brd_`, every stock entry of the dungeon
    doc once, the socket picks, jewelry without a primary, Normal tiers Rare, new items' levels and binding, the type
    and slot changes, the dissolved Savage Gladiator set, the cleared resistances, the bow's ammo;
  - the kept stock effects (whole stock rows, or the named effect slot where the stock stat Equip folds away);
  - the effect spells and the two looks sit in the `blackrock_depths_items` reservation, the C++ header names the same
    ids, every scripted_by() name is a script hard_mode_items.cpp registers;
  - each hard mode item carries its spell with the right trigger, scaled ("budget") exactly where the designer scales
    by item level;
  - damage and healing come from potency (the chained heal is the one declared exception), every tooltip placeholder
    is expanded, item spells pass the triggered-cast rules (EquippedItemClass -1, a damage or heal spell is never
    DmgClass NONE unless it is a share of another heal);
  - the proc rows.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_items.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockDepths"
HEADER = MODULE_DIR / "BlackrockDepthsHardModeItemsLogic.h"
SCRIPT = MODULE_DIR / "hard_mode_items.cpp"

(EXECUTIONER, SHIV, WOUND, FETISH, CHAIN, BULWARK, ERUPTION, FIST, SLAM, SCEPTER, LAVA_SPAWN, HURL, CORE, ORB_STRIKE,
 ROD, SERVO, MEND, COIL, ATTRACTION, ARC, HEARTSTONE, HEARTSTONE_ERUPTION, ORB, BEAM) = range(206830, 206854)
RESERVATION = range(206830, 206900)
LAVA_SPAWN_NPC, SERVO_NPC = 300655, 300656

SCHOOL_DAMAGE = 2
HEAL = 10
APPLY_AURA = 6
PERIODIC_DAMAGE = 3

# blackrock-depths-rework.md ## Loot, sections 1 to 4 and the Vault (rulings 44, 45, 85-87): every stock entry.
STOCK_LIST = {
    11624, 22240, 11626, 11631, 11632, 22397, 11628, 11627, 11623, 11726, 22257, 22270, 11702, 11730, 11824, 11665,
    11678, 11677, 11635, 11633,                                         # section 1 (20 stock + 1 new)
    11750, 11747, 11722, 11782, 11784, 22241, 11755, 22205, 22254, 22255, 22256, 11805, 11803,  # section 2 + Vault
    11816, 11817, 11820, 11819, 11669, 11822,                           # section 3
    11744, 11745, 22212, 11809, 11832, 11814, 11935, 22395, 22400, 11920, 11922, 11923, 11926, 12557, 12553, 11815,
    11924, 11928, 11930, 11933, 12554, 12556, 18044, 18043, 22275, 12793, 12791, 11785, 11786, 11787,  # section 4
}
NEW_LIST = {
    "brd_spell_eaters_choker": 57, "brd_undying_ember": 60, "brd_anvilfire_grips": 60,
    "brd_robe_of_the_elemental_lord": 60, "brd_magmaheart_mantle": 56, "brd_idol_of_the_wayward_princess": 58,
}
HARD_MODE_KEYS = {
    "brd_theldrens_executioner", "brd_leftys_shiv", "brd_korvs_spirit_fetish", "brd_black_anvil_bulwark",
    "brd_fist_of_the_lake_lord", "brd_scepter_of_the_molten_lake", "brd_prototype_power_core",
    "brd_golemwrights_mending_rod", "brd_electrons_lethal_coil", "brd_ironfoe", "brd_volcanic_heartstone",
    "brd_orb_of_the_sorcerer_thane",
}
R, Y, B = Socket.RED, Socket.YELLOW, Socket.BLUE
# The doc's one pick (Mana Shaping Handwraps) plus the shared rule's picks (STAGE-BRD report, designer questions).
SOCKETS = {
    "brd_kentic_amice": (R,), "brd_earthslag_shoulders": (R,), "brd_fleetfoot_greaves": (R,),
    "brd_savage_gladiator_chain": (R, Y), "brd_entrenching_boots": (R,), "brd_savage_gladiator_grips": (R,),
    "brd_ogreseer_fists": (R,), "brd_carapace_of_anubshiah": (B, B), "brd_spiderfang_carapace": (R,),
    "brd_flamestrider_robes": (R, Y), "brd_boreal_mantle": (R,), "brd_mana_shaping_handwraps": (R,),
    "brd_robe_of_the_elemental_lord": (R,), "brd_magmaheart_mantle": (R,), "brd_royal_decorated_armor": (R, Y),
    "brd_omnicast_boots": (R,), "brd_fists_of_phalanx": (R,), "brd_molten_fists": (R,), "brd_magmus_stone": (R,),
    "brd_deathdealer_breastplate": (R, Y), "brd_robes_of_the_royal_crown": (R, Y), "brd_mixologists_tunic": (R,),
    "brd_theldrens_executioner": (R,), "brd_leftys_shiv": (R,), "brd_korvs_spirit_fetish": (R,),
    "brd_black_anvil_bulwark": (B,), "brd_fist_of_the_lake_lord": (R,), "brd_scepter_of_the_molten_lake": (R,),
    "brd_golemwrights_mending_rod": (R,), "brd_electrons_lethal_coil": (R,), "brd_ironfoe": (R,),
    "brd_orb_of_the_sorcerer_thane": (R,),
}
TRINKETS = {"brd_undying_ember", "brd_second_wind", "brd_burst_of_knowledge", "brd_hand_of_justice",
            "brd_prototype_power_core", "brd_volcanic_heartstone"}
JEWELRY = {"brd_bloodclot_band", "brd_spell_eaters_choker", "brd_cyclopean_band", "brd_vereks_collar",
           "brd_magma_forged_band", "brd_naglering", "brd_imperial_jewel", "brd_electrons_lethal_coil"}
PRIMARY_LESS_TRINKETS = {"brd_hand_of_justice", "brd_prototype_power_core", "brd_volcanic_heartstone"}
KEPT_EFFECTS = {"brd_hookfang_shanker", "brd_force_of_magma", "brd_lord_generals_sword", "brd_naglering",
                "brd_bloodfist", "brd_flame_wrath", "brd_totem_of_rage", "brd_libram_of_truth", "brd_wraith_scythe",
                "brd_barman_shanker"}
# Stock items whose stat Equip folds away while the effect slot stays: (spell, trigger).
KEPT_SLOT = {"brd_second_wind": (15604, SpellTrigger.USE), "brd_burst_of_knowledge": (15646, SpellTrigger.USE),
             "brd_hand_of_justice": (15600, SpellTrigger.ON_EQUIP)}


class BlackrockDepthsItemsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load_items_registry()
        cls.spells = {int(e["id"]): e for e in cls.reg.spells if int(e["id"]) in RESERVATION}
        cls.decls = {e["id"]: e["_decl"] for e in cls.reg.item_declarations if e["id"].startswith("brd_")}
        cls.procs = {int(r["SpellId"]): r for r in cls.reg.spell_procs if int(r["SpellId"]) in RESERVATION}

    # --- the list ------------------------------------------------------------------------------------------------

    def test_the_list(self):
        hard_mode = {k for k, d in self.decls.items() if d.ladder.name == "vanilla_hard_mode"}
        dungeon = {k for k, d in self.decls.items() if d.ladder.name == "vanilla_dungeon"}
        self.assertEqual(hard_mode, HARD_MODE_KEYS)
        self.assertEqual(len(dungeon), 75)
        self.assertEqual(len(self.decls), 87)
        bases = [d.base for d in self.decls.values() if d.base is not None]
        self.assertEqual(len(bases), len(set(bases)))
        self.assertEqual(set(bases), STOCK_LIST)
        self.assertEqual({k for k, d in self.decls.items() if d.base is None and k in dungeon}, set(NEW_LIST))

    def test_new_items(self):
        for key, decl in self.decls.items():
            if decl.base is not None:
                continue
            self.assertEqual(dict(decl.columns).get("bonding"), 1, key)  # a new boss item binds on pickup
            self.assertIsNotNone(decl.like, key)
            if key in NEW_LIST:
                self.assertEqual(decl.ilvl, NEW_LIST[key], key)  # the boss's lowest stock item level, else 60
        self.assertEqual(self.decls["brd_ironfoe"].like, 11684)  # Ironfoe's look, on the hard mode ladder

    def test_sockets(self):
        socketed = {k: d.sockets for k, d in self.decls.items() if d.sockets}
        self.assertEqual(socketed, SOCKETS)
        for key in TRINKETS:
            self.assertIsNone(self.decls[key].sockets, key)  # trinkets never
        for key, decl in self.decls.items():
            self.assertEqual(decl.sockets is None, decl.socket_bonus is None, key)
        for key in HARD_MODE_KEYS - TRINKETS:
            self.assertEqual(len(self.decls[key].sockets), 1, key)  # hard mode items carry 1

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

    def test_normal_is_rare(self):
        self.assertEqual(self.decls["brd_savage_gladiator_chain"].quality, Quality.RARE)  # the one stock epic
        for key, decl in self.decls.items():
            if decl.ladder.name == "vanilla_dungeon" and key != "brd_savage_gladiator_chain":
                self.assertIn(decl.quality, (None, Quality.RARE), key)

    def test_stock_edits(self):
        columns = {k: dict(d.columns) for k, d in self.decls.items()}
        self.assertEqual((columns["brd_deathdealer_breastplate"]["subclass"],
                          columns["brd_deathdealer_breastplate"]["Material"]), (4, 6))  # mail -> plate
        self.assertEqual(columns["brd_black_steel_bindings"]["InventoryType"], 10)  # wrist -> hands
        self.assertEqual(columns["brd_savage_gladiator_chain"]["itemset"], 0)  # the dissolved set
        self.assertEqual(columns["brd_savage_gladiator_grips"]["itemset"], 0)
        self.assertEqual((columns["brd_rock_golem_bulwark"]["nature_res"],
                          columns["brd_rock_golem_bulwark"]["arcane_res"]), (0, 0))
        self.assertEqual(columns["brd_houndmasters_bow"]["ammo_type"], 0)
        self.assertEqual(self.decls["brd_coal_miner_boots"].extra_stamina, 0.25)  # the Leather Tank piece

    def test_kept_effects(self):
        self.assertEqual({k for k, d in self.decls.items() if d.keep_spells}, KEPT_EFFECTS)
        for key, (spell_id, trigger) in KEPT_SLOT.items():
            spells = self.decls[key].spells
            self.assertEqual(len(spells), 1, key)
            self.assertEqual((spells[0].spell_id, spells[0].trigger, spells[0].scale), (spell_id, trigger, None), key)
        ironfoe = self.decls["brd_ironfoe"].spells
        self.assertEqual((ironfoe[0].spell_id, ironfoe[0].trigger, ironfoe[0].ppm),
                         (15494, SpellTrigger.CHANCE_ON_HIT, 1.5))

    # --- the effects ---------------------------------------------------------------------------------------------

    def test_ids_sit_in_their_reservation(self):
        self.assertEqual(sorted(self.spells), list(range(EXECUTIONER, BEAM + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths_items", {"spell": set(self.spells)}), [])
        npcs = id_blocks.declared_ids(TOOL_ROOT / "source" / "npcs" / "blackrock_depths")
        items = [c for c in sorted(set(npcs["creature"]))
                 if not id_blocks.out_of_reservation("blackrock_depths_items", {"creature": [c]})]
        self.assertEqual(items, [LAVA_SPAWN_NPC, SERVO_NPC])

    def test_the_cpp_header_names_the_same_ids(self):
        text = HEADER.read_text()
        named = {name: int(value) for name, value in re.findall(r"\b(SPELL_[A-Z_]+)\s*=\s*(\d+)", text)}
        self.assertEqual(sorted(named.values()), list(range(EXECUTIONER, BEAM + 1)))
        self.assertEqual(named["SPELL_THELDRENS_EXECUTIONER"], EXECUTIONER)
        self.assertEqual(named["SPELL_LAVA_SPAWN"], LAVA_SPAWN)
        self.assertEqual(named["SPELL_LETHAL_ATTRACTION"], ATTRACTION)
        self.assertEqual(named["SPELL_SHADOW_BEAM"], BEAM)
        for spell_id, spell in self.spells.items():
            constant = "SPELL_" + re.sub(r"[^A-Z]+", "_", spell["name"].upper().replace("'", "")).strip("_")
            self.assertEqual(named.get(constant), spell_id, constant)
        self.assertRegex(text, rf"\bNPC_LAVA_SPAWN\s*=\s*{LAVA_SPAWN_NPC}\b")
        self.assertRegex(text, rf"\bNPC_MENDING_SERVO\s*=\s*{SERVO_NPC}\b")

    def test_every_binding_is_a_registered_script(self):
        registered = set(re.findall(r"RegisterSpellScript\((\w+)\)", SCRIPT.read_text()))
        bound = {(int(r["spell_id"]), r["ScriptName"]) for r in self.reg.spell_script_names
                 if int(r["spell_id"]) in RESERVATION}
        self.assertEqual(bound, {
            (FETISH, "spell_brd_korvs_spirit_fetish"), (SCEPTER, "spell_brd_scepter_of_the_molten_lake"),
            (LAVA_SPAWN, "spell_brd_lava_spawn"), (CORE, "spell_brd_prototype_power_core"),
            (ROD, "spell_brd_golemwrights_mending_rod"), (SERVO, "spell_brd_mending_servo"),
            (COIL, "spell_brd_electrons_lethal_coil"), (HEARTSTONE, "spell_brd_volcanic_heartstone"),
            (ORB, "spell_brd_orb_of_the_sorcerer_thane"),
        })
        self.assertEqual({name for _, name in bound}, registered)
        self.assertIn('UnitScript("BrdExecutionerDamage"', SCRIPT.read_text())

    def test_items_carry_their_spell(self):
        expected = {
            "brd_theldrens_executioner": (EXECUTIONER, SpellTrigger.ON_EQUIP, None),
            "brd_leftys_shiv": (SHIV, SpellTrigger.ON_EQUIP, "budget"),
            "brd_korvs_spirit_fetish": (FETISH, SpellTrigger.ON_EQUIP, None),
            "brd_black_anvil_bulwark": (BULWARK, SpellTrigger.ON_EQUIP, "budget"),
            "brd_fist_of_the_lake_lord": (FIST, SpellTrigger.ON_EQUIP, "budget"),
            "brd_scepter_of_the_molten_lake": (SCEPTER, SpellTrigger.ON_EQUIP, "budget"),
            "brd_prototype_power_core": (CORE, SpellTrigger.USE, "budget"),
            "brd_golemwrights_mending_rod": (ROD, SpellTrigger.ON_EQUIP, "budget"),
            "brd_electrons_lethal_coil": (COIL, SpellTrigger.ON_EQUIP, "budget"),
            "brd_volcanic_heartstone": (HEARTSTONE, SpellTrigger.USE, "budget"),
            "brd_orb_of_the_sorcerer_thane": (ORB, SpellTrigger.ON_EQUIP, "budget"),
        }
        for key, (spell_id, trigger, scale) in expected.items():
            decl = self.decls[key]
            self.assertEqual(len(decl.spells), 1, key)
            item_spell = decl.spells[0]
            self.assertEqual((item_spell.spell_id, item_spell.trigger, item_spell.scale), (spell_id, trigger, scale),
                             key)
            self.assertEqual(item_spell.cooldown, -1, key)  # the spell's own cooldown

    def test_numbers_come_from_potency(self):
        for spell_id in (WOUND, ERUPTION, SLAM, HURL, ORB_STRIKE, MEND, ARC, HEARTSTONE_ERUPTION, BEAM):
            effect = self.spells[spell_id]["effect1"]
            self.assertIn(effect["type"], (SCHOOL_DAMAGE, HEAL, APPLY_AURA), spell_id)
            self.assertTrue(effect.get("_potency"), spell_id)
            self.assertNotEqual(int(self.spells[spell_id]["raw_overrides"]["DefenseType"]), 0, spell_id)
        self.assertEqual(self.spells[WOUND]["effect1"]["apply_aura"], PERIODIC_DAMAGE)
        chain = self.spells[CHAIN]
        self.assertEqual(chain["effect1"]["type"], HEAL)
        self.assertFalse(chain["effect1"].get("_potency"))  # half the heal (potency_excluded)
        # every potency is distinct, so no two tooltips join one copy family
        potencies = [repr(self.spells[s]["effect1"]["_potency"])
                     for s in (WOUND, ERUPTION, SLAM, HURL, ORB_STRIKE, MEND, ARC, HEARTSTONE_ERUPTION, BEAM)]
        self.assertEqual(len(potencies), len(set(potencies)))

    def test_tooltips(self):
        for spell_id, spell in self.spells.items():
            raw = spell["raw_overrides"]
            self.assertEqual(raw["EquippedItemClass"], -1, spell_id)
            self.assertNotIn("{pot", raw["Description_Lang_enUS"], spell_id)
            self.assertNotRegex(raw.get("AuraDescription_Lang_enUS", ""), r"\$", spell_id)
        # the scaled families reach their buffs and debuffs through a token
        self.assertIn("$206840d", self.spells[SCEPTER]["raw_overrides"]["Description_Lang_enUS"])
        self.assertIn("$206845d", self.spells[ROD]["raw_overrides"]["Description_Lang_enUS"])
        self.assertIn("$206848d", self.spells[COIL]["raw_overrides"]["Description_Lang_enUS"])

    def test_spell_shapes(self):
        self.assertEqual(self.spells[SHIV]["effect1"]["trigger_spell"], WOUND)
        self.assertEqual(int(self.spells[WOUND]["raw_overrides"]["CumulativeAura"]), 5)
        self.assertEqual(self.spells[BULWARK]["effect1"]["trigger_spell"], ERUPTION)
        self.assertEqual(self.spells[FIST]["effect1"]["trigger_spell"], SLAM)
        self.assertEqual(self.spells[EXECUTIONER]["effect1"]["base_points"] + 1, 10)  # +10% damage
        self.assertEqual(self.spells[EXECUTIONER]["effect2"]["base_points"] + 1, 30)  # below 30% health
        self.assertEqual(self.spells[FETISH]["effect1"]["base_points"] + 1, 50)       # half the heal
        self.assertEqual(self.spells[CORE]["effect1"]["base_points"] + 1, 3)          # three orbs
        self.assertEqual(self.spells[CORE]["cooldown_ms"], 120000)
        self.assertEqual(self.spells[CORE]["duration_ms"], 12000)
        self.assertEqual(self.spells[HEARTSTONE]["effect1"]["base_points"] + 1, -20)  # 20% less damage taken
        self.assertEqual(self.spells[HEARTSTONE]["cooldown_ms"], 120000)
        self.assertEqual(self.spells[HEARTSTONE]["duration_ms"], 8000)
        for spell_id in (LAVA_SPAWN, SERVO):
            self.assertEqual(self.spells[spell_id]["duration_ms"], 10000, spell_id)
            self.assertEqual(self.spells[spell_id]["effect1"]["amplitude"], 2000, spell_id)
        self.assertEqual(self.spells[ATTRACTION]["duration_ms"], 8000)

    def test_proc_rows(self):
        self.assertEqual(set(self.procs), {SHIV, FETISH, BULWARK, FIST, SCEPTER, ROD, COIL, ORB})
        for spell_id, row in self.procs.items():
            self.assertEqual(row["ProcFlags"] & 0x00040000, 0, spell_id)  # never periodic ticks
            self.assertGreater(row["Chance"], 0, spell_id)
        self.assertEqual(self.procs[BULWARK]["HitMask"], 0x40)  # blocks
        self.assertEqual(self.procs[BULWARK]["ProcFlags"], 0x8 | 0x20)  # taken melee
        for spell_id in (FETISH, ROD):
            self.assertEqual((self.procs[spell_id]["SpellTypeMask"], self.procs[spell_id]["SpellPhaseMask"]),
                             (0x2, 0x2), spell_id)  # landed heals
        self.assertEqual(self.procs[COIL]["Chance"], 100.0)  # the script rolls the charge itself
        for spell_id in (SCEPTER, ROD):
            self.assertGreater(self.procs[spell_id]["Cooldown"], 10000, spell_id)  # outlasts the 10 sec look

    def test_totem_of_rage_shock_equip_is_on_potency(self):
        # "moved onto potency": the stock Equip 27859 is declared by source/items (not source/spells/npc.csv), the
        # same OVERRIDE_CLASS_SCRIPTS 4418 aura, its amount a potency line that is the stock +30 at level 60.
        entries = [e for e in self.reg.spells if int(e["id"]) == 27859]
        self.assertEqual(len(entries), 1)
        effect = entries[0]["effect1"]
        self.assertEqual((effect["type"], effect["apply_aura"], effect["misc_value"]), (APPLY_AURA, 112, 4418))
        self.assertAlmostEqual(effect["_potency"]["level60_value"], 30.0, delta=0.5)
        self.assertEqual(entries[0]["raw_overrides"]["EffectSpellClassMaskA_1"], 2416967680)  # Earth, Flame, Frost
        csv_text = (TOOL_ROOT / "source" / "spells" / "npc.csv").read_text(encoding="utf-8")
        self.assertNotIn("\n27859,", csv_text)
        self.assertTrue(self.decls["brd_totem_of_rage"].keep_spells)  # slot 1 stays the stock 27859


if __name__ == "__main__":
    unittest.main()
