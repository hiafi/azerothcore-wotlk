"""
The Scholomance items (wave 1 dungeon items): source/items/scholomance.py, its effects in
source/items/scholomance_hard_mode_effects.py and the scripts in modules/mod-dungeon-bosses (src/Scholomance/
scholomance_items.cpp, ScholomanceItemsLogic.h).

Checks:
  - the list: 52 items on the dungeon ladder (42 stock, 10 new) and 6 on the hard mode ladder, every key scholo_;
  - the effect spells sit in the `scholomance_items` reservation, the C++ header names the same ids, and every
    scripted_by() name is a script scholomance_items.cpp registers;
  - each effect item carries its spell with the right trigger, scaled per tier exactly when it has a damage, healing,
    absorb or stat aura number (the Phylactery Shard's scripted armor excepted);
  - every damage, healing and absorb number comes from potency (the Phylactery's percent heal is the one declared
    exclusion), never on DmgClass NONE, every tooltip placeholder is expanded, aura texts are number-free and every
    spell passes the triggered-cast rule (EquippedItemClass -1);
  - the proc rows;
  - the item rules the list sets: kept stock effects, former set pieces without a set, the stock Epics on a Rare
    Normal tier, the two look changes, sockets.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scholomance_hard_mode_items.py
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
from lib.dsl.items import Quality, Socket, SpellTrigger  # noqa: E402
from lib.test_hard_mode_item_effects import _load_items_registry  # noqa: E402

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Scholomance"
HEADER = MODULE_DIR / "ScholomanceItemsLogic.h"
SCRIPT = MODULE_DIR / "scholomance_items.cpp"

FIRST, LAST = 205620, 205659
(SPARE_RIB, JAR, TORN_SOUL, RIB_SPREADER, OPEN_WOUND, LAUNCHER, ACID, DEANS_ROD, DEMERIT, SUTURE_KIT, STITCHES,
 PHYLACTERY, MEND, CHILLBAND, CHILL, BONECHILL, FROST_BLAST, PAPERS, RIBBON, HONOR_ROLL, PORTAL_ROD, BARRAGE,
 PORTAL_LOOK) = range(205620, 205643)

SCHOOL_DAMAGE, HEAL, APPLY_AURA, PERSISTENT_AREA_AURA = 2, 10, 6, 27
PERIODIC_DAMAGE, PERIODIC_HEAL, SCHOOL_ABSORB = 3, 8, 69
PORTAL_NPC = 300465  # the Portal Rod's look-alike portal (source/npcs/scholomance/hard_mode_items.py)

HEADER_NAMES = {
    "SPELL_SPARE_RIB": SPARE_RIB, "SPELL_JAR_OF_TORN_SOULS": JAR, "SPELL_TORN_SOUL": TORN_SOUL,
    "SPELL_RIB_SPREADER": RIB_SPREADER, "SPELL_OPEN_WOUND": OPEN_WOUND, "SPELL_SPECIMEN_LAUNCHER": LAUNCHER,
    "SPELL_SPECIMEN_ACID": ACID, "SPELL_THE_DEANS_ROD": DEANS_ROD, "SPELL_DEMERIT": DEMERIT,
    "SPELL_SUTURE_KIT": SUTURE_KIT, "SPELL_STITCHES": STITCHES, "SPELL_PHYLACTERY_SHARD": PHYLACTERY,
    "SPELL_PHYLACTERY_MEND": MEND, "SPELL_FROSTWHISPERS_CHILLBAND": CHILLBAND, "SPELL_CHILL": CHILL,
    "SPELL_BONECHILL_BLADE": BONECHILL, "SPELL_BONECHILL_FROST_BLAST": FROST_BLAST, "SPELL_TRANSFER_PAPERS": PAPERS,
    "SPELL_HONOR_ROLL_RIBBON": RIBBON, "SPELL_HONOR_ROLL": HONOR_ROLL, "SPELL_DARKMASTERS_PORTAL_ROD": PORTAL_ROD,
    "SPELL_PORTAL_BARRAGE": BARRAGE, "SPELL_DARKMASTERS_PORTAL_LOOK": PORTAL_LOOK,
}

# item key -> (effect spell, trigger, scaled per tier)
EFFECT_ITEMS = {
    "scholo_spare_rib": (SPARE_RIB, SpellTrigger.USE, True),  # a stat aura (armor), wave 1 integration
    "scholo_jar_of_torn_souls": (JAR, SpellTrigger.ON_EQUIP, True),  # a stat aura (Intellect)
    "scholo_rib_spreader": (RIB_SPREADER, SpellTrigger.ON_EQUIP, True),
    "scholo_polkelts_specimen_launcher": (LAUNCHER, SpellTrigger.ON_EQUIP, True),
    "scholo_the_deans_rod": (DEANS_ROD, SpellTrigger.ON_EQUIP, False),
    "scholo_krastinovs_suture_kit": (SUTURE_KIT, SpellTrigger.USE, True),
    "scholo_phylactery_shard": (PHYLACTERY, SpellTrigger.USE, False),
    "scholo_frostwhispers_chillband": (CHILLBAND, SpellTrigger.ON_EQUIP, False),
    "scholo_bonechill_blade": (BONECHILL, SpellTrigger.ON_EQUIP, True),
    "scholo_transfer_papers": (PAPERS, SpellTrigger.USE, False),
    "scholo_honor_roll_ribbon": (RIBBON, SpellTrigger.ON_EQUIP, True),
    "scholo_darkmasters_portal_rod": (PORTAL_ROD, SpellTrigger.ON_EQUIP, True),
}
# the spells that carry a number (damage, healing, absorb): all potency, the Mend excluded by declaration
POTENCY_SPELLS = {OPEN_WOUND: PERIODIC_DAMAGE, ACID: PERIODIC_DAMAGE, STITCHES: PERIODIC_HEAL,
                  FROST_BLAST: SCHOOL_DAMAGE, HONOR_ROLL: SCHOOL_ABSORB, BARRAGE: PERIODIC_DAMAGE}
KEPT_STOCK_EFFECTS = {"scholo_barovian_family_sword", "scholo_frightskull_shaft", "scholo_ebon_hilt_of_marduk",
                      "scholo_silent_fang", "scholo_headmasters_charge"}
FORMER_SET_PIECES = {"scholo_necropile_robe", "scholo_necropile_boots", "scholo_necropile_cuffs",
                     "scholo_cadaverous_leggings", "scholo_cadaverous_armor", "scholo_cadaverous_walkers",
                     "scholo_deathbone_sabatons", "scholo_deathbone_chestplate", "scholo_bloodmail_hauberk",
                     "scholo_bloodmail_legguards"}


def _id(spell_entry) -> int:
    return int(spell_entry["id"])


class ScholomanceItemsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load_items_registry()
        cls.spells = {_id(e): e for e in cls.reg.spells if FIRST <= _id(e) <= LAST}
        cls.decls = {e["id"]: e["_decl"] for e in cls.reg.item_declarations if e["id"].startswith("scholo_")}
        cls.procs = {int(r["SpellId"]): r for r in cls.reg.spell_procs if FIRST <= int(r["SpellId"]) <= LAST}

    def test_the_list(self):
        ladders = [d.ladder.name for d in self.decls.values()]
        self.assertEqual(ladders.count("vanilla_dungeon"), 52)
        self.assertEqual(ladders.count("vanilla_hard_mode"), 6)
        normal = [d for d in self.decls.values() if d.ladder.name == "vanilla_dungeon"]
        self.assertEqual(sum(d.base is not None for d in normal), 42)
        self.assertEqual(sum(d.base is None for d in normal), 10)
        for d in self.decls.values():
            if d.base is None:
                self.assertEqual(dict(d.columns).get("bonding"), 1, d.key)  # a new boss item binds on pickup
            if d.base is None and d.ladder.name == "vanilla_dungeon":
                self.assertIn(d.ilvl, (59, 61), d.key)  # the boss's lowest stock item level on the list

    def test_ids_sit_in_their_reservation(self):
        self.assertEqual(sorted(self.spells), list(range(SPARE_RIB, PORTAL_LOOK + 1)))
        ids = {"spell": set(self.spells)}
        self.assertEqual(id_blocks.out_of_reservation("scholomance_items", ids), [])
        npcs = id_blocks.declared_ids(TOOL_ROOT / "source" / "npcs" / "scholomance")
        self.assertEqual(sorted(set(npcs["creature"])), [PORTAL_NPC])
        self.assertEqual(id_blocks.out_of_reservation("scholomance_items", {"creature": npcs["creature"]}), [])

    def test_the_cpp_header_names_the_same_ids(self):
        named = {name: int(value) for name, value in re.findall(r"\b(SPELL_[A-Z_]+)\s*=\s*(\d+)", HEADER.read_text())}
        self.assertEqual(named, HEADER_NAMES)
        self.assertRegex(HEADER.read_text(), rf"\bNPC_DARKMASTERS_PORTAL\s*=\s*{PORTAL_NPC}\b")

    def test_every_binding_is_a_registered_script(self):
        registered = set(re.findall(r"RegisterSpellScript\((\w+)\)", SCRIPT.read_text()))
        bound = {(int(r["spell_id"]), r["ScriptName"]) for r in self.reg.spell_script_names
                 if FIRST <= int(r["spell_id"]) <= LAST}
        self.assertEqual(bound, {(PHYLACTERY, "spell_scholo_phylactery_shard"),
                                 (BONECHILL, "spell_scholo_bonechill_blade"),
                                 (PAPERS, "spell_scholo_transfer_papers"),
                                 (PORTAL_ROD, "spell_scholo_darkmasters_portal_rod")})
        self.assertEqual({name for _, name in bound}, registered)

    def test_items_carry_their_spell(self):
        for key, (spell_id, trigger, scaled) in EFFECT_ITEMS.items():
            decl = self.decls[key]
            self.assertEqual(len(decl.spells), 1, key)
            spell = decl.spells[0]
            self.assertEqual((spell.spell_id, spell.trigger), (spell_id, trigger), key)
            self.assertEqual(spell.cooldown, -1, key)  # the spell's own cooldown
            self.assertEqual(spell.scale, "budget" if scaled else None, key)
        with_spells = {k for k, d in self.decls.items() if d.spells}
        self.assertEqual(with_spells, set(EFFECT_ITEMS))
        self.assertEqual({k for k, d in self.decls.items() if d.keep_spells}, KEPT_STOCK_EFFECTS)
        # hard mode: 0.7 for the effect, the Papers' full budget, the two weapon-slot items on their role cell
        self.assertEqual(self.decls["scholo_transfer_papers"].budget_mult, 1.0)
        for key in ("scholo_phylactery_shard", "scholo_frostwhispers_chillband", "scholo_honor_roll_ribbon"):
            self.assertEqual(self.decls[key].budget_mult, 0.7, key)
        for key in ("scholo_bonechill_blade", "scholo_darkmasters_portal_rod"):
            self.assertIsNone(self.decls[key].budget_mult, key)

    def test_numbers_come_from_potency_only(self):
        for spell_id, aura_or_effect in POTENCY_SPELLS.items():
            effect = self.spells[spell_id]["effect1"]
            kind = effect["type"] if effect["type"] == SCHOOL_DAMAGE else effect["apply_aura"]
            self.assertEqual(kind, aura_or_effect, spell_id)
            self.assertTrue(effect.get("_potency"), spell_id)
            if spell_id != HONOR_ROLL:  # an absorb gets no spell power from the engine; base only
                self.assertNotEqual(int(self.spells[spell_id]["raw_overrides"]["DefenseType"]), 0, spell_id)
        for spell_id, spell in self.spells.items():
            for index in (1, 2, 3):
                effect = spell.get(f"effect{index}") or {}
                numbered = effect.get("type") in (SCHOOL_DAMAGE, HEAL) or (
                    effect.get("type") in (APPLY_AURA, PERSISTENT_AREA_AURA)
                    and effect.get("apply_aura") in (PERIODIC_DAMAGE, PERIODIC_HEAL, SCHOOL_ABSORB))
                if numbered and spell_id not in POTENCY_SPELLS:
                    self.assertEqual(spell_id, MEND)  # the one exclusion, declared
        bonus = {int(r["entry"]) for r in self.reg.spell_bonus_data if FIRST <= int(r["entry"]) <= LAST}
        self.assertTrue(bonus <= set(POTENCY_SPELLS), bonus)
        self.assertNotIn(MEND, bonus)
        # the acid scales with ranged attack power (hunters), the wound with melee attack power
        self.assertIn("$RAP", self.spells[LAUNCHER]["raw_overrides"]["Description_Lang_enUS"])
        self.assertIn("$AP", self.spells[RIB_SPREADER]["raw_overrides"]["Description_Lang_enUS"])
        self.assertIn("$SP", self.spells[PORTAL_ROD]["raw_overrides"]["Description_Lang_enUS"])

    def test_tooltips(self):
        for spell_id, spell in self.spells.items():
            raw = spell["raw_overrides"]
            self.assertEqual(raw["EquippedItemClass"], -1, spell_id)
            self.assertNotIn("{pot", raw["Description_Lang_enUS"], spell_id)
            self.assertNotRegex(raw.get("AuraDescription_Lang_enUS", ""), r"\$|\d", spell_id)  # number-free
        self.assertEqual(self.spells[DEMERIT]["raw_overrides"]["AuraDescription_Lang_enUS"],
                         "Has earned a Demerit. Deals less damage.")  # approved 2026-11-02

    def test_aura_amounts(self):
        def amount(spell_id, index=1):
            effect = self.spells[spell_id][f"effect{index}"]
            return effect["base_points"] + effect["die_sides"]
        self.assertEqual(amount(SPARE_RIB), 1000)
        self.assertEqual(amount(PHYLACTERY), 1500)
        self.assertEqual(amount(PHYLACTERY, 2), 30)  # the percent the script heals
        self.assertEqual(amount(TORN_SOUL), 10)
        self.assertEqual(self.spells[TORN_SOUL]["raw_overrides"]["CumulativeAura"], 5)
        self.assertEqual(amount(DEMERIT), -1)
        self.assertEqual(self.spells[DEMERIT]["raw_overrides"]["CumulativeAura"], 5)
        self.assertEqual(self.spells[DEMERIT]["duration_ms"], 30000)
        self.assertEqual((amount(CHILL), amount(CHILL, 2)), (-10, -10))
        self.assertEqual((amount(HONOR_ROLL, 2), amount(HONOR_ROLL, 3)), (1, 1))
        self.assertEqual(self.spells[RIBBON]["effect1"]["amplitude"], 30000)
        self.assertEqual(self.spells[RIBBON]["effect1"]["trigger_spell"], HONOR_ROLL)
        acid = self.spells[ACID]["effect1"]
        self.assertEqual((acid["implicit_target_a"], acid["implicit_target_b"], acid["radius_yards"]), (53, 28, 6.0))
        self.assertEqual(self.spells[ACID]["duration_ms"], 6000)
        self.assertEqual(self.spells[PAPERS]["effect1"]["implicit_target_a"], 35)  # TARGET_UNIT_TARGET_PARTY

    def test_proc_rows(self):
        self.assertEqual(set(self.procs), {JAR, RIB_SPREADER, LAUNCHER, DEANS_ROD, SUTURE_KIT, PHYLACTERY, CHILLBAND,
                                           BONECHILL, PORTAL_ROD})
        launcher = self.procs[LAUNCHER]
        self.assertEqual(launcher["ProcFlags"], 0x40 | 0x100)  # ranged auto attacks and ranged spells
        self.assertEqual((launcher["Chance"], launcher["Cooldown"]), (10.0, 10000))  # approved 2026-11-02
        rod = self.procs[DEANS_ROD]
        self.assertEqual(rod["ProcFlags"], 0x8 | 0x20)  # taken melee
        self.assertEqual(rod["HitMask"], 0x20)  # parries only
        self.assertEqual(rod["Chance"], 100.0)  # the parry is the gate
        kit = self.procs[SUTURE_KIT]
        self.assertEqual((kit["SpellTypeMask"], kit["SpellPhaseMask"], kit["Charges"]), (0x2, 0x2, 3))
        self.assertEqual(self.procs[PHYLACTERY]["ProcFlags"], 0x00100000)  # any damage taken
        self.assertEqual(self.procs[BONECHILL]["Cooldown"], 10000)
        for spell_id in (JAR, RIB_SPREADER, CHILLBAND, BONECHILL, PORTAL_ROD):
            row = self.procs[spell_id]
            self.assertEqual(row["SpellTypeMask"], 0x1, spell_id)  # damage
            self.assertEqual(row["HitMask"], 0x3, spell_id)  # landed
            self.assertTrue(0 < row["Chance"] < 100, spell_id)
            self.assertEqual(row["ProcFlags"] & 0x00040000, 0, spell_id)  # no periodic ticks

    def test_item_rules(self):
        for key in FORMER_SET_PIECES:
            self.assertEqual(dict(self.decls[key].columns).get("itemset"), 0, key)
        for key in ("scholo_alannas_embrace", "scholo_headmasters_charge"):
            self.assertEqual(self.decls[key].quality, Quality.RARE, key)  # stock Epic, Rare on Normal
        ghostloom = dict(self.decls["scholo_ghostloom_leggings"].columns)
        self.assertEqual((ghostloom["subclass"], ghostloom["Material"]), (1, 7))  # cloth now
        self.assertEqual(dict(self.decls["scholo_detention_strap"].columns)["InventoryType"], 9)  # a wrist strap
        socketed = {k: d.sockets for k, d in self.decls.items() if d.sockets}
        self.assertEqual(len(socketed), 17)
        for key in ("scholo_wraithplate_leggings", "scholo_deathbone_chestplate"):
            self.assertEqual(socketed[key], (Socket.BLUE, Socket.BLUE), key)  # tank pieces
        for key, sockets in socketed.items():
            self.assertLessEqual(len(sockets), 2, key)
        for key in ("scholo_phylactery_shard", "scholo_transfer_papers", "scholo_spare_rib", "scholo_jar_of_torn_souls",
                    "scholo_krastinovs_suture_kit"):
            self.assertNotIn(key, socketed)  # trinkets never


if __name__ == "__main__":
    unittest.main()
