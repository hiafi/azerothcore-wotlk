"""
The Zul'Farrak hard mode items and their effects (the Zul'Farrak gear stage, ZG-HM): source/items/
zul_farrak_hard_mode.py, source/items/zul_farrak_hard_mode_effects.py, the Whistle's crew in source/npcs/zul_farrak/
hard_mode_items.py and the scripts in modules/mod-dungeon-bosses (src/ZulFarrak/hard_mode_items.cpp,
ZulFarrakHardModeItemsLogic.h).

Checks:
  - the list: the three items of the dungeon doc's hard mode list (docs/dungeons/zul-farrak-rework.md ## Loot, ruling
    47; the table is copied below because docs/ is not in every checkout), all new on the hard mode ladder, Bind on
    Pickup, a stock look, the doc's type, slot, primary and secondaries, the socket pick (one, trinkets none), the
    declared multiplier, and every shape stat on every materialized tier;
  - the effect spells and the crew sit in the `zul_farrak_items` reservation, the C++ header names the same ids, every
    scripted_by() name is a script hard_mode_items.cpp registers;
  - each item carries its spell with the right trigger, all three scaled ("budget");
  - the discharge's and the arc's damage come from potency, the copied heal is a script-sized share, every tooltip
    placeholder is expanded, item spells pass the triggered-cast rules (EquippedItemClass -1, a potency damage spell is
    never DmgClass NONE, payouts never proc);
  - the doc's numbers (10 stacks, 8 yd, 5 charges, 2 enemies, 12 sec, 2 allies, 10 yd, 2 min), the in-combat filters,
    the once-per-cast guard and the proc rows;
  - the tier copies: the discharge, the arc and the share grow with the tier, the charges and the copied heal stay one
    spell.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_zul_farrak_hard_mode_items.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "ZulFarrak"
HEADER = MODULE_DIR / "ZulFarrakHardModeItemsLogic.h"
SCRIPT = MODULE_DIR / "hard_mode_items.cpp"
PRIEST = REPO_ROOT / "src" / "server" / "scripts" / "Spells" / "spell_priest.cpp"
NPCS = TOOL_ROOT / "source" / "npcs" / "zul_farrak"

SCALE, CHARGE, DISCHARGE, FANG, STORMCHARGED, ARC, WHISTLE, AID = range(213800, 213808)
DECLARED = range(SCALE, AID + 1)  # the hard mode effects; 213808 is the list's join (test_zul_farrak_items.py)
RESERVATION = range(213800, 213840)
CREW = range(301000, 301005)

SCHOOL_DAMAGE = 2
HEAL = 10
DUMMY_AURA = 4
NO_REFLECTION = 0x00000080
IGNORE_LINE_OF_SIGHT = 0x00000004
CANT_CRIT = 0x20000000
SUPPRESS_CASTER_PROCS = 0x00010000
IGNORE_CASTER_MODIFIERS = 0x20000000

# zul-farrak-rework.md ## Loot, "Hard mode: Gahz'rilla, The Crew at the Pool" (approved 2026-11-24, ruling 47), copied:
# key -> (name, item_template class, subclass, InventoryType, the doc's stats in order).
DOC_LIST = {
    "zf_scale_of_the_storm_god": ("Scale of the Storm God", 4, 0, 12, ("Strength", "Mastery")),
    "zf_stormcharged_fang": ("Stormcharged Fang", 2, 15, 13, ("Intellect", "Crit", "Haste")),
    "zf_sergeants_whistle": ("Sergeant's Whistle", 4, 0, 12, ("Spirit", "Haste")),
}
TRINKETS = {"zf_scale_of_the_storm_god", "zf_sergeants_whistle"}
# key -> (spell, trigger)
ITEM_SPELLS = {
    "zf_scale_of_the_storm_god": (SCALE, SpellTrigger.ON_EQUIP),
    "zf_stormcharged_fang": (FANG, SpellTrigger.ON_EQUIP),
    "zf_sergeants_whistle": (WHISTLE, SpellTrigger.USE),
}


def _shape_words(name: str) -> tuple:
    return tuple(name.replace(" (Solo)", "").split("/"))


class ZulFarrakHardModeItemsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load_items_registry()
        cls.spells = {int(e["id"]): e for e in cls.reg.spells if int(e["id"]) in DECLARED}
        cls.decls = {e["id"]: e["_decl"] for e in cls.reg.item_declarations if e["id"] in DOC_LIST}
        cls.procs = {int(r["SpellId"]): r for r in cls.reg.spell_procs if int(r["SpellId"]) in RESERVATION}
        cls.source = SCRIPT.read_text()

    def _raw(self, spell_id: int) -> dict:
        return self.spells[spell_id]["raw_overrides"]

    def _description(self, spell_id: int) -> str:
        return self._raw(spell_id)["Description_Lang_enUS"]

    def _script(self, name: str) -> str:
        return self.source.split(f"class {name} ", 1)[1].split("\n};\n", 1)[0]

    def _dummy_amounts(self, spell_id: int) -> list:
        effects = [self.spells[spell_id][f"effect{i}"] for i in (1, 2)]
        for effect in effects:
            self.assertEqual(effect["apply_aura"], DUMMY_AURA, spell_id)
        return [effect["base_points"] + 1 for effect in effects]

    # --- the list ------------------------------------------------------------------------------------------------

    def test_the_list(self):
        self.assertEqual(set(self.decls), set(DOC_LIST))
        for key, decl in self.decls.items():
            self.assertEqual(decl.name, DOC_LIST[key][0], key)
            self.assertEqual(decl.ladder.name, "vanilla_hard_mode", key)
            self.assertIsNone(decl.base, key)                       # all new
            self.assertIsNotNone(decl.like, key)                    # a stock look
            self.assertIsNot(decl.unique_equip, False, key)         # unique-equipped (automatic for an effect item)
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
        self.assertEqual(declared, {"zf_stormcharged_fang": (0.6, None)})
        socketed = {k: (d.sockets, d.socket_bonus) for k, d in self.decls.items() if d.sockets}
        self.assertEqual(socketed, {"zf_stormcharged_fang": ((Socket.RED,), 2874)})
        for key in TRINKETS:
            self.assertIsNone(self.decls[key].sockets, key)  # trinkets never
            self.assertIsNone(self.decls[key].socket_bonus, key)

    def test_every_shape_stat_is_on_every_tier(self):
        """The materialized rows: every doc stat has at least one point on every tier (REVIEW S3)."""
        assert_shape_stats_on_every_tier(self, self.decls)

    # --- the effects ---------------------------------------------------------------------------------------------

    def test_ids_sit_in_their_reservation(self):
        self.assertEqual(sorted(self.spells), list(DECLARED))
        self.assertEqual(sorted(int(e["id"]) for e in self.reg.spells if int(e["id"]) in RESERVATION),
                         [*DECLARED, 213808])  # and the list's join
        self.assertEqual(id_blocks.out_of_reservation("zul_farrak_items", {"spell": set(self.spells)}), [])

    def test_the_cpp_header_names_the_same_ids(self):
        text = HEADER.read_text()
        named = {name: int(value) for name, value in re.findall(r"\b((?:SPELL|NPC)_[A-Z_]+)\s*=\s*(\d+)", text)}
        self.assertEqual(named, {
            "SPELL_SCALE_OF_THE_STORM_GOD": SCALE, "SPELL_STATIC_CHARGE": CHARGE, "SPELL_STATIC_DISCHARGE": DISCHARGE,
            "SPELL_STORMCHARGED_FANG": FANG, "SPELL_STORMCHARGED": STORMCHARGED, "SPELL_STORM_ARC": ARC,
            "SPELL_SERGEANTS_WHISTLE": WHISTLE, "SPELL_THE_CREWS_AID": AID,
            "NPC_CREW_BLY": 301000, "NPC_CREW_RAVEN": 301001, "NPC_CREW_ORO": 301002, "NPC_CREW_WEEGLI": 301003,
            "NPC_CREW_MURTA": 301004,
        })
        self.assertIn(f"kSpellsZulFarrakItems{{ {RESERVATION.start}, {RESERVATION.stop - 1} }}", text)
        self.assertIn(f"kCreaturesZulFarrakItems{{ {CREW.start}, {CREW.stop - 1} }}", text)
        self.assertEqual({i: s["name"] for i, s in self.spells.items()}, {
            SCALE: "Scale of the Storm God", CHARGE: "Static Charge", DISCHARGE: "Static Discharge",
            FANG: "Stormcharged Fang", STORMCHARGED: "Stormcharged", ARC: "Storm Arc",
            WHISTLE: "Sergeant's Whistle", AID: "The Crew's Aid",
        })

    def test_the_crew(self):
        """Five looks, one per crew member, in the reservation; untargetable, friendly, and not the stock crew."""
        declared = id_blocks.declared_ids(NPCS)
        self.assertTrue(set(CREW) <= set(declared["creature"]))
        self.assertEqual(id_blocks.out_of_reservation("zul_farrak_items", {"creature": set(CREW)}), [])
        text = (NPCS / "hard_mode_items.py").read_text()
        names = dict((int(i), n) for i, n in re.findall(r"creature_template\((\d+), '([^']+)'", text))
        self.assertEqual(names, {301000: "Sergeant Bly", 301001: "Raven", 301002: "Oro Eyegouge",
                                 301003: "Weegli Blastfuse", 301004: "Murta Grimgut"})
        # the stock crew's models (creature_template_model 7604-7608)
        models = dict((int(i), int(d)) for i, d in re.findall(r"creature_model\((\d+), display_id=(\d+)", text))
        self.assertEqual(models, {301000: 6433, 301001: 6435, 301002: 6432, 301003: 7222, 301004: 6438})
        self.assertIn("unit_flags=0x2 | 0x02000000", text)
        self.assertIn("faction=35", text)
        # the Use outlasts nothing: the script dismisses the crew, its own timer is the Use plus a tail
        stay = int(re.search(r"kCrewStayMs = (\d+)", HEADER.read_text()).group(1))
        self.assertGreater(stay, self.spells[WHISTLE]["duration_ms"])

    def test_every_binding_is_a_registered_script(self):
        registered = set(re.findall(r"RegisterSpellScript\((\w+)\)", self.source))
        bound = {(int(r["spell_id"]), r["ScriptName"]) for r in self.reg.spell_script_names
                 if int(r["spell_id"]) in DECLARED}
        self.assertEqual(bound, {
            (SCALE, "spell_zf_scale_of_the_storm_god"), (DISCHARGE, "spell_zf_static_discharge"),
            (FANG, "spell_zf_stormcharged_fang"), (WHISTLE, "spell_zf_sergeants_whistle"),
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
        for spell_id in (DISCHARGE, ARC):
            effect = self.spells[spell_id]["effect1"]
            self.assertEqual(effect["type"], SCHOOL_DAMAGE, spell_id)
            self.assertTrue(effect.get("_potency"), spell_id)
            self.assertEqual(int(self._raw(spell_id)["DefenseType"]), 1, spell_id)  # magic
            self.assertEqual(int(self.spells[spell_id]["school"]), int(School.NATURE), spell_id)
        self.assertEqual(self.spells[DISCHARGE]["_spell"].effects[0].ap_potency, 90.0)   # a Strength trinket
        self.assertFalse(self.spells[DISCHARGE]["_spell"].effects[0].sp_potency)
        self.assertEqual(self.spells[ARC]["_spell"].effects[0].sp_potency, 150.0)        # an Intellect dagger
        self.assertFalse(self.spells[ARC]["_spell"].effects[0].ap_potency)
        # the share of another heal: sized by a script, no potency, no base points, no second bonus or crit
        effect = self.spells[AID]["effect1"]
        self.assertEqual(effect["type"], HEAL)
        self.assertFalse(effect.get("_potency"))
        self.assertTrue(self.spells[AID]["_spell"].effects[0].potency_excluded)
        self.assertEqual(effect["base_points"], 0)
        self.assertNotIn("DefenseType", self._raw(AID))
        self.assertTrue(self._raw(AID)["AttributesEx2"] & CANT_CRIT)
        self.assertTrue(self._raw(AID)["AttributesEx3"] & IGNORE_CASTER_MODIFIERS)

    def test_payouts_never_proc(self):
        for spell_id in (CHARGE, DISCHARGE, STORMCHARGED, ARC, WHISTLE, AID):
            self.assertTrue(int(self._raw(spell_id)["AttributesEx3"]) & SUPPRESS_CASTER_PROCS, spell_id)
        # a reflected payout would hit the wearer and charge the Scale
        for spell_id in (DISCHARGE, ARC):
            self.assertTrue(int(self._raw(spell_id)["AttributesEx"]) & NO_REFLECTION, spell_id)

    def test_tooltips(self):
        for spell_id, spell in self.spells.items():
            raw = spell["raw_overrides"]
            self.assertEqual(raw["EquippedItemClass"], -1, spell_id)
            self.assertNotIn("{pot", raw["Description_Lang_enUS"], spell_id)
            self.assertNotRegex(raw.get("AuraDescription_Lang_enUS", ""), r"[$0-9]", spell_id)
        self.assertIn("in combat within $213802a1 yd", self._description(SCALE))
        self.assertIn("$s2 more enemies in combat within $a1 yd", self._description(FANG))
        self.assertIn("the $s2 allies lowest on health within $a1 yd of the target for $s1%",
                      self._description(WHISTLE))

    def test_spell_shapes(self):
        s = self.spells
        # Scale: 10 stacks (the buff's cap), a 6 sec cooldown, 8 yd around the wearer
        self.assertEqual(self._dummy_amounts(SCALE), [10, 6])
        self.assertEqual((s[CHARGE]["duration_ms"], self._raw(CHARGE)["CumulativeAura"]), (30000, 10))
        self.assertEqual((s[DISCHARGE]["effect1"]["implicit_target_a"], s[DISCHARGE]["effect1"]["implicit_target_b"],
                          s[DISCHARGE]["effect1"]["radius_yards"]), (22, 15, 8.0))
        # Fang: 5 charges (the buff's cap), 2 more enemies within 10 yd
        self.assertEqual(self._dummy_amounts(FANG), [5, 2])
        self.assertEqual(s[FANG]["effect1"]["radius_yards"], 10.0)
        self.assertEqual((s[STORMCHARGED]["duration_ms"], self._raw(STORMCHARGED)["CumulativeAura"]), (30000, 5))
        # Whistle: 12 sec, 2 min, off the GCD, a share to 2 allies within 10 yd
        self.assertEqual(self._dummy_amounts(WHISTLE), [40, 2])
        self.assertEqual((s[WHISTLE]["duration_ms"], s[WHISTLE]["cooldown_ms"], s[WHISTLE]["effect1"]["radius_yards"],
                          self._raw(WHISTLE)["StartRecoveryTime"]), (12000, 120000, 10.0, 0))
        # the buffs are shown, the Equips are passive
        for spell_id in (CHARGE, STORMCHARGED, WHISTLE):
            self.assertFalse(int(s[spell_id].get("attributes") or 0) & 0x40, spell_id)
        for spell_id in (SCALE, FANG):
            self.assertTrue(int(s[spell_id]["attributes"]) & 0x40, spell_id)
        # an arc and a copied heal start at the target, so the script checks the line of sight from there
        for spell_id in (ARC, AID):
            self.assertTrue(int(self._raw(spell_id)["AttributesEx2"]) & IGNORE_LINE_OF_SIGHT, spell_id)

    def test_damage_reaches_only_enemies_in_combat(self):
        self.assertIn("!unit->IsInCombat()", self._script("spell_zf_static_discharge"))
        self.assertRegex(self._script("spell_zf_static_discharge"),
                         r"FilterTargets, EFFECT_0,\s+TARGET_UNIT_SRC_AREA_ENEMY")
        arcs = self.source.split("std::vector<Unit*> ArcTargets(", 1)[1].split("\n    }\n", 1)[0]
        self.assertIn("unit->IsInCombat()", arcs)
        self.assertIn("victim->IsWithinLOSInMap(unit)", arcs)

    def test_the_scripts_follow_the_rules(self):
        scale = self._script("spell_zf_scale_of_the_storm_god")
        self.assertIn("eventInfo.GetActor() == GetTarget()", scale)     # the wearer's own damage never charges
        self.assertIn("SPELL_ATTR3_NOT_A_PROC", scale)                  # a triggered strike rolls nothing
        fang = self._script("spell_zf_stormcharged_fang")
        self.assertIn("SameCast(_acted", fang.split("bool CheckProc", 1)[1].split("void HandleProc", 1)[0])
        self.assertIn("_acted = StampOf", fang)
        whistle = self._script("spell_zf_sergeants_whistle")
        check = whistle.split("bool CheckProc", 1)[1].split("void HandleProc", 1)[0]
        for rule in ("healSpell->Id == SPELL_THE_CREWS_AID", "SPELL_ATTR3_IGNORE_CASTER_MODIFIERS", "m_CastItem",
                     "HealsOneTarget(healSpell)"):
            self.assertIn(rule, check)
        # a script casts its tier's copy of a scaled spell and the shared base of the others
        for base in ("SPELL_STATIC_DISCHARGE", "SPELL_STORM_ARC"):
            self.assertIn(f"TierSpell(GetSpellInfo(), {base})", self.source)
        for shared in ("SPELL_STATIC_CHARGE", "SPELL_STORMCHARGED", "SPELL_THE_CREWS_AID"):
            self.assertNotRegex(self.source, rf"TierSpell\([^)]*\b{shared}\)")

    def test_bloom_is_not_a_single_target_heal(self):
        """Bloom and its jump (Druid::StartBloomJumps) are a chain heal by script; the ids are the druid's."""
        self.assertIn("Druid::SPELL_BLOOM ", self.source)
        self.assertIn("Druid::SPELL_BLOOM_JUMP", self.source)

    def test_script_spread_heals_are_refused(self):
        """Empowered Penance's extra bolts and Glyph of Prayer of Healing's heal over time are cast on several targets
        by script (single target in the data): refused by id, and the ids are the priest's."""
        shape = self.source.split("bool HealsOneTarget(", 1)[1].split("std::array<HealShape", 1)[0]
        self.assertIn("IsScriptSpreadHeal(spellInfo->Id)", shape)
        header = dict(re.findall(r"\b(k(?:EmpoweredPenanceBolt|PrayerOfHealingGlyph)) = (\d+);", HEADER.read_text()))
        priest = dict(re.findall(r"\b(SPELL_PRIEST_\w+)\s*=\s*(\d+)", PRIEST.read_text()))
        self.assertEqual(header, {
            "kEmpoweredPenanceBolt": priest["SPELL_PRIEST_EMPOWERED_PENANCE_HEAL"],
            "kPrayerOfHealingGlyph": priest["SPELL_PRIEST_GLYPH_OF_PRAYER_OF_HEALING_HEAL"],
        })

    def test_the_copy_is_sized_before_the_targets_healing_taken(self):
        """The share is of the heal before the healed target's healing taken modifiers (undone with a probe on that
        target, as a tick or a direct heal) and heal absorbs; the copied heal takes its own target's."""
        whistle = self._script("spell_zf_sergeants_whistle")
        self.assertRegex(whistle, r"HealBeforeTaken\(heal->GetHeal\(\), heal->GetAbsorb\(\),\s+healed->"
                                  r"SpellHealingBonusTaken\(healer, heal->GetSpellInfo\(\), kTakenProbe, "
                                  r"tick \? DOT : HEAL\)\)")
        self.assertIn("tick = (eventInfo.GetTypeMask() & PROC_FLAG_DONE_PERIODIC) != 0", whistle)
        self.assertIn("ShareOfHeal(whole, aurEff->GetAmount())", whistle)
        self.assertNotIn("ShareOfHeal(heal->GetHeal()", whistle)

    def test_scaled_tiers(self):
        """The copy families (the discharge, the arc and the share grow with the tier; the charges and the copied heal
        stay shared)."""
        from lib import item_spell_copies  # noqa: PLC0415

        spells = [{**entry, "_source_class": item_spell_copies.SOURCE_CLASS} for entry in self.reg.spells]
        index = item_spell_copies.SpellIndex.build({"spells": spells, "linked_spells": self.reg.linked_spells})
        self.assertEqual(index.family(SCALE), [SCALE, DISCHARGE])
        self.assertEqual(index.family(FANG), [FANG, ARC])
        self.assertEqual(index.family(WHISTLE), [WHISTLE])
        # The hard mode ladder's ratios 1.0545 / 1.1091 / 1.2545 (dbc-tools.md, IV10).
        remap = {SCALE: 1, DISCHARGE: 2, FANG: 3, ARC: 4, WHISTLE: 5}
        for ratio, share in ((1.0545, 42), (1.1091, 44), (1.2545, 50)):
            copies = {}
            for root in (SCALE, FANG, WHISTLE):
                copies.update(item_spell_copies.build_copies(index, index.family(root), remap, ratio, "test"))
            self.assertAlmostEqual(copies[DISCHARGE].effects[0].ap_potency, 90.0 * ratio)
            self.assertAlmostEqual(copies[ARC].effects[0].sp_potency, 150.0 * ratio)
            self.assertEqual([e.base_points + 1 for e in copies[SCALE].effects if e], [10, 6])  # the counts stay
            self.assertEqual([e.base_points + 1 for e in copies[FANG].effects if e], [5, 2])
            self.assertEqual([e.base_points + 1 for e in copies[WHISTLE].effects if e], [share, 2], ratio)

    def test_proc_rows(self):
        self.assertEqual(set(self.procs), {SCALE, FANG, WHISTLE})
        for row in self.procs.values():
            self.assertEqual((row["Chance"], row["Cooldown"], row["SpellPhaseMask"], row["HitMask"], row["Charges"]),
                             (100.0, 0, 0x2, 0x3, 0))
            self.assertEqual(row["SpellFamilyName"], 0)
        # hits taken (the header's flags, no periodic tick) and melee-class abilities done (no auto attack); boss hits
        # are often triggered casts, so triggered spells pass and the script sorts them
        scale = self.procs[SCALE]
        self.assertEqual((scale["ProcFlags"], scale["SpellTypeMask"], scale["AttributesMask"]),
                         (0x222A8 | 0x10, 0x1, 0x2))
        taken = re.search(r"kTakenHitFlags = ([^;]+);", HEADER.read_text()).group(1)
        self.assertEqual(sum(int(f.strip().rstrip("u"), 16) for f in taken.split("|")) | 0x10, scale["ProcFlags"])
        fang = self.procs[FANG]
        self.assertEqual((fang["ProcFlags"], fang["SpellTypeMask"], fang["AttributesMask"]), (0x11000, 0x1, 0))
        # direct heals and heal over time ticks
        whistle = self.procs[WHISTLE]
        self.assertEqual((whistle["ProcFlags"], whistle["SpellTypeMask"], whistle["AttributesMask"]), (0x44400, 0x2, 0))


if __name__ == "__main__":
    unittest.main()
