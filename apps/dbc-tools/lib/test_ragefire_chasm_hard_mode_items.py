"""
The Ragefire Chasm hard mode items and their effects (the Ragefire Chasm gear stage, RF-HM):
source/items/ragefire_chasm_hard_mode.py, source/items/ragefire_chasm_hard_mode_effects.py and the scripts in
modules/mod-dungeon-bosses (src/RagefireChasm/hard_mode_items.cpp, RagefireChasmHardModeItemsLogic.h).

Checks:
  - the list: the three items of the dungeon doc's hard mode list (docs/dungeons/ragefire-chasm-rework.md ## Loot,
    ruling 13; the table is copied below because docs/ is not in every checkout), all new on the hard mode ladder, Bind
    on Pickup, a stock look, the doc's type, slot, primary and secondaries, the socket pick (one, trinkets none), the
    declared multipliers, and every shape stat on every materialized tier;
  - the effect spells sit in the `ragefire_chasm_items` reservation, the C++ header names the same ids, every
    scripted_by() name is a script hard_mode_items.cpp registers;
  - each item carries its spell with the right trigger, all three scaled ("budget");
  - the bite's and the spin's damage come from potency, the heal and the absorb are script-sized shares, every tooltip
    placeholder is expanded, item spells pass the triggered-cast rules (EquippedItemClass -1, a potency damage spell is
    never DmgClass NONE, payouts never proc);
  - the doc's numbers (25 yd, 2 min, below 30%, 6 sec, 20 sec, 3 sec, every second, 8 yd) and the proc rows;
  - the tier copies: the bite, the share and the spin grow with the tier, Feed and Bloodward stay one spell.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_ragefire_chasm_hard_mode_items.py
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
from lib.dsl import School  # noqa: E402
from lib.dsl.items import Socket, SpellTrigger  # noqa: E402
from lib.test_hard_mode_item_effects import (  # noqa: E402
    _load_items_registry, assert_shape_stats_on_every_tier,
)

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "RagefireChasm"
HEADER = MODULE_DIR / "RagefireChasmHardModeItemsLogic.h"
SCRIPT = MODULE_DIR / "hard_mode_items.cpp"

FANG, BITE, FEED, HEART, BLOODWARD, GREATBLADE, FELSTORM, SPIN = range(213500, 213508)
RESERVATION = range(213500, 213540)

SCHOOL_DAMAGE = 2
DUMMY_EFFECT = 3
APPLY_AURA = 6
HEAL = 10
CHARGE = 96
DUMMY_AURA = 4
PERIODIC_TRIGGER_SPELL = 23
PROC_TRIGGER_SPELL = 42
SCHOOL_ABSORB = 69
SUPPRESS_CASTER_PROCS = 0x00010000

# ragefire-chasm-rework.md ## Loot, "Hard mode: Taragaman the Hungerer, Starving" (approved 2026-11-21, ruling 13),
# copied: key -> (name, item_template class, subclass, InventoryType, the doc's stats in order).
DOC_LIST = {
    "rfc_taragamans_fang": ("Taragaman's Fang", 4, 0, 12, ("Agility", "Haste")),
    "rfc_heart_of_the_starving": ("Heart of the Starving", 4, 0, 12, ("Spirit", "Mastery")),
    "rfc_felstorm_greatblade": ("Felstorm Greatblade", 2, 8, 17, ("Strength", "Crit", "Haste")),
}
TRINKETS = {"rfc_taragamans_fang", "rfc_heart_of_the_starving"}
# key -> (spell, trigger)
ITEM_SPELLS = {
    "rfc_taragamans_fang": (FANG, SpellTrigger.USE),
    "rfc_heart_of_the_starving": (HEART, SpellTrigger.ON_EQUIP),
    "rfc_felstorm_greatblade": (GREATBLADE, SpellTrigger.ON_EQUIP),
}


def _shape_words(name: str) -> tuple:
    return tuple(name.replace(" (Solo)", "").split("/"))


class RagefireChasmHardModeItemsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load_items_registry()
        cls.spells = {int(e["id"]): e for e in cls.reg.spells if int(e["id"]) in RESERVATION}
        cls.decls = {e["id"]: e["_decl"] for e in cls.reg.item_declarations if e["id"] in DOC_LIST}
        cls.procs = {int(r["SpellId"]): r for r in cls.reg.spell_procs if int(r["SpellId"]) in RESERVATION}

    def _description(self, spell_id: int) -> str:
        return self.spells[spell_id]["raw_overrides"]["Description_Lang_enUS"]

    # --- the list ------------------------------------------------------------------------------------------------

    def test_the_list(self):
        self.assertEqual(set(self.decls), set(DOC_LIST))
        for key, decl in self.decls.items():
            self.assertEqual(decl.name, DOC_LIST[key][0], key)
            self.assertEqual(decl.ladder.name, "vanilla_hard_mode", key)
            self.assertIsNone(decl.base, key)                       # all new
            self.assertIsNotNone(decl.like, key)                    # a stock look
            self.assertEqual(dict(decl.columns).get("bonding"), 1, key)  # Bind on Pickup

    def test_doc_stats(self):
        for key, (_, _, _, _, stats) in DOC_LIST.items():
            decl = self.decls[key]
            self.assertEqual(_shape_words(decl.primary), stats[:1], key)
            self.assertEqual(set(_shape_words(decl.secondary)), set(stats[1:]), key)

    def test_type_and_slot_follow_the_look(self):
        # like= copies class, subclass and InventoryType: every look donor is of the doc's type and slot.
        rows = id_blocks.spell_tables.load_live_item_template_rows()
        for key, (_, item_class, subclass, inventory_type, _) in DOC_LIST.items():
            donor = rows[self.decls[key].like]
            got = (int(donor["class"]), int(donor["subclass"]), int(donor["InventoryType"]))
            self.assertEqual(got, (item_class, subclass, inventory_type), key)

    def test_declared_multipliers_and_sockets(self):
        declared = {k: (d.budget_mult, d.extra_dps) for k, d in self.decls.items()
                    if d.budget_mult is not None or d.extra_dps is not None}
        self.assertEqual(declared, {"rfc_felstorm_greatblade": (0.5537, 0.0695)})
        socketed = {k: (d.sockets, d.socket_bonus) for k, d in self.decls.items() if d.sockets}
        self.assertEqual(socketed, {"rfc_felstorm_greatblade": ((Socket.RED,), 2874)})
        for key in TRINKETS:
            self.assertIsNone(self.decls[key].sockets, key)  # trinkets never
            self.assertIsNone(self.decls[key].socket_bonus, key)

    def test_every_shape_stat_is_on_every_tier(self):
        """The materialized rows: every doc stat has at least one point on every tier (REVIEW S3)."""
        assert_shape_stats_on_every_tier(self, self.decls)

    # --- the effects ---------------------------------------------------------------------------------------------

    def test_ids_sit_in_their_reservation(self):
        self.assertEqual(sorted(self.spells), list(range(FANG, SPIN + 1)))
        self.assertEqual(id_blocks.out_of_reservation("ragefire_chasm_items", {"spell": set(self.spells)}), [])

    def test_the_cpp_header_names_the_same_ids(self):
        text = HEADER.read_text()
        named = {name: int(value) for name, value in re.findall(r"\b(SPELL_[A-Z_]+)\s*=\s*(\d+)", text)}
        self.assertEqual(named, {
            "SPELL_TARAGAMANS_FANG": FANG, "SPELL_HUNGERING_BITE": BITE, "SPELL_FEED": FEED,
            "SPELL_HEART_OF_THE_STARVING": HEART, "SPELL_BLOODWARD": BLOODWARD,
            "SPELL_FELSTORM_GREATBLADE": GREATBLADE, "SPELL_FELSTORM": FELSTORM, "SPELL_FELSTORM_SPIN": SPIN,
        })
        self.assertIn(f"kSpellsRagefireChasmItems{{ {RESERVATION.start}, {RESERVATION.stop - 1} }}", text)
        self.assertEqual({i: s["name"] for i, s in self.spells.items()}, {
            FANG: "Taragaman's Fang", BITE: "Hungering Bite", FEED: "Feed", HEART: "Heart of the Starving",
            BLOODWARD: "Bloodward", GREATBLADE: "Felstorm Greatblade", FELSTORM: "Felstorm", SPIN: "Felstorm",
        })

    def test_every_binding_is_a_registered_script(self):
        registered = set(re.findall(r"RegisterSpellScript\((\w+)\)", SCRIPT.read_text()))
        bound = {(int(r["spell_id"]), r["ScriptName"]) for r in self.reg.spell_script_names
                 if int(r["spell_id"]) in RESERVATION}
        self.assertEqual(bound, {
            (FANG, "spell_rfc_taragamans_fang"), (BITE, "spell_rfc_hungering_bite"),
            (HEART, "spell_rfc_heart_of_the_starving"), (GREATBLADE, "spell_rfc_one_roll_per_cast"),
        })
        self.assertEqual({name for _, name in bound}, registered)

    def test_items_carry_their_spell(self):
        for key, (spell_id, trigger) in ITEM_SPELLS.items():
            decl = self.decls[key]
            self.assertEqual(len(decl.spells), 1, key)
            item_spell = decl.spells[0]
            self.assertEqual((item_spell.spell_id, item_spell.trigger, item_spell.scale), (spell_id, trigger, "budget"),
                             key)
            self.assertEqual(item_spell.cooldown, -1, key)  # the spell's own cooldown

    def test_numbers_come_from_potency(self):
        for spell_id in (BITE, SPIN):
            effect = self.spells[spell_id]["effect1"]
            self.assertEqual(effect["type"], SCHOOL_DAMAGE, spell_id)
            self.assertTrue(effect.get("_potency"), spell_id)
            self.assertEqual(int(self.spells[spell_id]["raw_overrides"]["DefenseType"]), 2, spell_id)  # melee
            self.assertEqual(int(self.spells[spell_id]["school"]), int(School.NORMAL), spell_id)  # Physical
        # distinct potencies, so no two tooltips join one copy family
        self.assertNotEqual(repr(self.spells[BITE]["effect1"]["_potency"]),
                            repr(self.spells[SPIN]["effect1"]["_potency"]))
        # the shares of another hit or heal: sized by a script, no potency, no base points
        for spell_id in (FEED, BLOODWARD):
            effect = self.spells[spell_id]["effect1"]
            self.assertFalse(effect.get("_potency"), spell_id)
            self.assertTrue(self.spells[spell_id]["_spell"].effects[0].potency_excluded, spell_id)
            self.assertEqual(effect["base_points"], 0, spell_id)
        self.assertEqual(self.spells[FEED]["effect1"]["type"], HEAL)
        self.assertEqual(self.spells[BLOODWARD]["effect1"]["apply_aura"], SCHOOL_ABSORB)

    def test_payouts_never_proc(self):
        for spell_id in (FANG, BITE, FEED, BLOODWARD, FELSTORM, SPIN):
            self.assertTrue(int(self.spells[spell_id]["raw_overrides"]["AttributesEx3"]) & SUPPRESS_CASTER_PROCS,
                            spell_id)

    def test_tooltips(self):
        for spell_id, spell in self.spells.items():
            raw = spell["raw_overrides"]
            self.assertEqual(raw["EquippedItemClass"], -1, spell_id)
            self.assertNotIn("{pot", raw["Description_Lang_enUS"], spell_id)
            self.assertNotRegex(raw.get("AuraDescription_Lang_enUS", ""), r"\$", spell_id)
        # the typed numbers match the data
        self.assertIn("within 25 yd", self._description(FANG))
        self.assertIn("for 6 sec", self._description(HEART))
        self.assertIn("20 sec cooldown", self._description(HEART))

    def test_spell_shapes(self):
        s = self.spells
        # Taragaman's Fang: a charge to an enemy within 25 yd, a hit delayed by distance / 42, 2 min, off the GCD
        self.assertEqual((s[FANG]["range_yards"], s[FANG]["cooldown_ms"]), (25.0, 120000))
        self.assertEqual((s[FANG]["effect1"]["type"], s[FANG]["effect2"]["type"]), (CHARGE, DUMMY_EFFECT))
        raw = s[FANG]["raw_overrides"]
        self.assertEqual((raw["Speed"], raw["StartRecoveryTime"]), (42.0, 0))
        motion = (REPO_ROOT / "src/server/game/Movement/MotionMaster.h").read_text()
        self.assertRegex(motion, r"#define SPEED_CHARGE\s+42\.0f")
        # ... while the leap runs at the ground spline cap, the speed the C++ header's landing watch is sized for
        spline = (REPO_ROOT / "src/server/game/Movement/Spline/MoveSplineInit.cpp").read_text()
        self.assertIn("std::max(28.0f, unit->GetSpeed(MOVE_RUN) * 4.0f)", spline)
        self.assertIn("kLeapSplineSpeed = 28.0f", HEADER.read_text())
        # ... no DefenseType and no damage effect: the leap itself cannot be missed
        self.assertNotIn("DefenseType", raw)
        self.assertTrue(s[BITE]["attributes"] & 0x00200000)  # NO_ACTIVE_DEFENSE
        # Heart of the Starving: below 30%, the share, 6 sec
        self.assertEqual((s[HEART]["effect1"]["apply_aura"], s[HEART]["effect1"]["base_points"] + 1), (DUMMY_AURA, 30))
        self.assertEqual((s[HEART]["effect2"]["apply_aura"], s[HEART]["effect2"]["base_points"] + 1), (DUMMY_AURA, 40))
        self.assertEqual(s[BLOODWARD]["duration_ms"], 6000)
        self.assertEqual(s[BLOODWARD]["effect1"]["misc_value"], 127)
        # Felstorm Greatblade: 3 sec, every second, 8 yd around the wearer
        self.assertEqual((s[GREATBLADE]["effect1"]["apply_aura"], s[GREATBLADE]["effect1"]["trigger_spell"]),
                         (PROC_TRIGGER_SPELL, FELSTORM))
        self.assertEqual((s[FELSTORM]["duration_ms"], s[FELSTORM]["effect1"]["apply_aura"],
                          s[FELSTORM]["effect1"]["amplitude"], s[FELSTORM]["effect1"]["trigger_spell"]),
                         (3000, PERIODIC_TRIGGER_SPELL, 1000, SPIN))
        self.assertEqual((s[SPIN]["effect1"]["implicit_target_a"], s[SPIN]["effect1"]["implicit_target_b"],
                          s[SPIN]["effect1"]["radius_yards"]), (22, 15, 8.0))

    def test_the_fang_is_a_leap_trinket_for_the_bots(self):
        """mod-playerbots recognizes the Fang by this spell data, not by id (src/Ai/Base/Util/LeapTrinketRules.h,
        IsLeapSpell; its host test is tests/leap_trinket_rules_test.cpp there): instant, not passive, not channeled,
        a CHARGE and a DUMMY or SCHOOL_DAMAGE effect, every effect on target A 6 (the enemy target) with no target B.
        A change here that breaks this stops the bots pressing it: change that header too."""
        fang = self.spells[FANG]
        self.assertEqual((fang["cast_time_ms"], fang["duration_ms"]), (0, 0))
        self.assertFalse(int(fang.get("attributes") or 0) & 0x40)  # passive
        self.assertFalse(int(fang["raw_overrides"].get("AttributesEx", 0)) & 0x44)  # channeled
        effects = [fang[f"effect{i}"] for i in (1, 2, 3) if fang.get(f"effect{i}")]
        self.assertEqual([e["type"] for e in effects], [CHARGE, DUMMY_EFFECT])
        for effect in effects:
            self.assertEqual((effect["implicit_target_a"], effect.get("implicit_target_b") or 0), (6, 0))

    def test_the_fang_never_leaps_from_melee_range(self):
        """Review M1: a leap from inside the target's combat reach would carry the wearer to its center."""
        fang = SCRIPT.read_text().split("class spell_rfc_taragamans_fang", 1)[1].split("};\n\n//", 1)[0]
        self.assertRegex(fang, r"OnEffectLaunchTarget \+= SpellEffectFn\([\w:]+HandleLeap, EFFECT_0, "
                               r"SPELL_EFFECT_CHARGE")
        self.assertRegex(fang, r"if \(!LeapMoves\(wearer->IsWithinMeleeRange\(victim\)[^;]+\)\)\s+"
                               r"PreventHitDefaultEffect\(EFFECT_0\);")

    def test_the_scripts_follow_the_doc(self):
        source = SCRIPT.read_text()
        self.assertNotIn("IsInCombat", source)  # designer 2026-11-24: the Felstorm hits every enemy in its 8 yd
        heart = source.split("class spell_rfc_heart_of_the_starving", 1)[1].split("};\n\n//", 1)[0]
        self.assertIn("BelowThresholdBeforeHeal", heart)
        # a larger remaining Bloodward stays (review m3), decided before the cooldown starts
        self.assertIn("BloodwardReplaces", heart.split("bool CheckProc", 1)[1].split("void HandleProc", 1)[0])
        self.assertNotIn("healed == ", heart)  # any target the heal hits counts, the healer included
        self.assertNotIn("IsPlayer()", heart)

    def test_scaled_tiers(self):
        """The copy families (the bite, the share and the spin grow with the tier; Feed and Bloodward stay shared)."""
        from lib import item_spell_copies  # noqa: PLC0415

        spells = [{**entry, "_source_class": item_spell_copies.SOURCE_CLASS} for entry in self.reg.spells]
        index = item_spell_copies.SpellIndex.build({"spells": spells, "linked_spells": self.reg.linked_spells})
        self.assertEqual(index.family(FANG), [FANG, BITE])
        self.assertEqual(index.family(HEART), [HEART])
        self.assertEqual(index.family(GREATBLADE), [GREATBLADE, FELSTORM, SPIN])
        # The hard mode ladder's ratios 1.0545 / 1.1091 / 1.2545 (dbc-tools.md, IV10).
        remap = {FANG: 1, BITE: 2, HEART: 3, GREATBLADE: 4, FELSTORM: 5, SPIN: 6}
        for ratio, share in ((1.0545, 42), (1.1091, 44), (1.2545, 50)):
            copies = {}
            for root in (FANG, HEART, GREATBLADE):
                copies.update(item_spell_copies.build_copies(index, index.family(root), remap, ratio, "test"))
            self.assertAlmostEqual(copies[BITE].effects[0].ap_potency, 250.0 * ratio)
            self.assertAlmostEqual(copies[SPIN].effects[0].ap_potency, 35.0 * ratio)
            self.assertEqual(copies[HEART].effects[0].base_points + 1, 30)  # the threshold stays
            self.assertEqual(copies[HEART].effects[1].base_points + 1, share, ratio)
            self.assertEqual(copies[GREATBLADE].effects[0].trigger_spell, 5)  # the tier's own Felstorm and spin
            self.assertEqual(copies[FELSTORM].effects[0].trigger_spell, 6)

    def test_proc_rows(self):
        self.assertEqual(set(self.procs), {HEART, GREATBLADE})
        heart, blade = self.procs[HEART], self.procs[GREATBLADE]
        # every landed direct heal (the script's check picks the low ones), 20 sec internal cooldown
        self.assertEqual((heart["ProcFlags"], heart["SpellTypeMask"], heart["SpellPhaseMask"]), (0x4400, 0x2, 0x2))
        self.assertEqual((heart["Chance"], heart["Cooldown"]), (100.0, 20000))
        # melee hits, a chance, an internal cooldown longer than the Felstorm
        self.assertEqual((blade["ProcFlags"], blade["SpellTypeMask"], blade["SpellPhaseMask"]), (0x14, 0x1, 0x2))
        self.assertEqual((blade["Chance"], blade["Cooldown"]), (15.0, 6000))
        self.assertGreater(blade["Cooldown"], self.spells[FELSTORM]["duration_ms"])

    def test_haunting_mark_ignores_the_item_spells(self):
        """HauntedSetUnitHooks::ModifySpellDamageTaken skips these item spells and their tier copies (the bite and
        the spin are melee class and would consume a Beaststalker's Haunting Mark). The predicate itself is
        host-tested (tests/ragefire_chasm_hard_mode_items_test.cpp)."""
        haunted = (REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "DungeonSets" /
                   "haunted_set_bonuses.cpp").read_text(encoding="utf-8")
        self.assertIn('#include "RagefireChasmHardModeItemsLogic.h"', haunted)
        hook = haunted.split("void ModifySpellDamageTaken(", 1)[1].split("void OnSpellDamageTakenFinal(", 1)[0]
        self.assertIn("RagefireChasmHardModeItems::IsItemSpell(spellInfo->Id)", hook)


if __name__ == "__main__":
    unittest.main()
