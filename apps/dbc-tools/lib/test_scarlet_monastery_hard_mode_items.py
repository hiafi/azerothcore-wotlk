"""
The Scarlet Monastery hard mode items and their effects (the Scarlet Monastery gear stage, WP-SM-HM):
source/items/scarlet_monastery_hard_mode.py, source/items/scarlet_monastery_hard_mode_effects.py,
source/npcs/scarlet_monastery/hard_mode_items.py and the scripts in modules/mod-dungeon-bosses
(src/ScarletMonastery/hard_mode_items.cpp, ScarletMonasteryHardModeItemsLogic.h).

Checks:
  - the list: the twelve items of the dungeon doc's "Hard mode lists" (docs/dungeons/scarlet-monastery-rework.md ##
    Loot, ruling 59; the table is copied below because docs/ is not in every checkout), keys `sm_`, all new on the hard
    mode ladder, Bind on Pickup, a stock look, the doc's type, slot, primary and secondaries, the ring and the neck
    without a primary, the socket picks (one, trinkets none), the gun's ammo, the declared multipliers, and every shape
    stat on every materialized tier;
  - the effect spells and the banner sit in the `scarlet_monastery_items` reservation, the C++ header names the same
    ids, every scripted_by() name is a script hard_mode_items.cpp registers;
  - each item carries its spell with the right trigger, scaled ("budget") exactly where a number grows with item level;
  - damage, healing and absorbs come from potency, every tooltip placeholder is expanded, item spells pass the
    triggered-cast rules (EquippedItemClass -1, a damage or heal spell is never DmgClass NONE);
  - the doc's numbers (5% for 15 sec, the 2 min lockout, 3 stacks, 8 sec, 30% slower, 6 / 8 yd, 10%, 50%) and the
    proc rows;
  - the fix pass (2026-11-20): the short areas hit every enemy (ruling B8: no in-combat filter on the Fissure, the
    Volley or the Verdict), Recently Rallied survives death and immunities and stays one spell for every tier (review
    m3), the Standard's 5% and Denial's 10% grow with the tier (review m5).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_scarlet_monastery_hard_mode_items.py
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
from lib.dsl.items import Socket, SpellTrigger  # noqa: E402
from lib.test_hard_mode_item_effects import (  # noqa: E402
    _load_items_registry, assert_shape_stats_on_every_tier,
)

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "ScarletMonastery"
HEADER = MODULE_DIR / "ScarletMonasteryHardModeItemsLogic.h"
SCRIPT = MODULE_DIR / "hard_mode_items.cpp"

(STANDARD, RALLIED, RECENTLY_RALLIED, CENSER, PENITENT_FIRE, SIGNET, BLESSING, SHARD, WAND, ICY_DEATH, GRIPS, FISSURE,
 RIFLE, VOLLEY, BULWARK, PILLAR, STAFF, CONSECRATED_PILLAR, FATHERS_VERDICT, VERDICT, TREADS, DENIAL, ROSARY,
 RESOLVE) = range(212000, 212024)
RESERVATION = range(212000, 212100)
BANNER_NPC = 300880

SCHOOL_DAMAGE = 2
HEAL = 10
APPLY_AURA = 6
PERIODIC_DAMAGE = 3
SCHOOL_ABSORB = 69

# scarlet-monastery-rework.md ## Loot, "Hard mode lists (approved 2026-11-19, ruling 59)", copied: key -> (name,
# item_template class, subclass, InventoryType, the doc's stats in order). The doc's "Ranged" slot is a ranged weapon
# (InventoryType 26), "Off-hand" a held-in-off-hand item (23) or a shield (14), "Two-hand" 17.
DOC_LIST = {
    "sm_purebloods_rallying_standard": ("Pureblood's Rallying Standard", 4, 0, 12, ("Strength", "Haste", "Mastery")),
    "sm_fairbells_censer": ("Fairbell's Censer", 4, 0, 23, ("Intellect", "Crit", "Mastery")),
    "sm_voss_blessed_signet": ("Voss's Blessed Signet", 4, 0, 11, ("Crit", "Haste")),
    "sm_shard_of_the_phylactery": ("Shard of the Phylactery", 4, 0, 12, ("Intellect", "Haste", "Versatility")),
    "sm_heretics_wand": ("Heretic's Wand", 2, 19, 26, ("Intellect", "Crit")),
    "sm_fissure_touched_grips": ("Fissure-touched Grips", 4, 2, 10, ("Agility", "Haste", "Versatility")),
    "sm_scarlet_garrison_rifle": ("Scarlet Garrison Rifle", 2, 3, 26, ("Agility", "Crit", "Haste")),
    "sm_garrison_bulwark": ("Garrison Bulwark", 4, 6, 14, ("Strength", "Block", "Mastery")),
    "sm_staff_of_the_consecrated_hall": ("Staff of the Consecrated Hall", 2, 10, 17, ("Spirit", "Crit", "Versatility")),
    "sm_fathers_verdict": ("Father's Verdict", 2, 8, 17, ("Strength", "Haste", "Versatility")),
    "sm_treads_of_denial": ("Treads of Denial", 4, 4, 8, ("Strength", "Parry", "Mastery")),
    "sm_inquisitors_rosary": ("Inquisitor's Rosary", 4, 0, 2, ("Crit", "Versatility")),
}
PRIMARIES = {"Strength", "Agility", "Intellect", "Spirit"}
TRINKETS = {"sm_purebloods_rallying_standard", "sm_shard_of_the_phylactery"}
JEWELRY = {"sm_voss_blessed_signet", "sm_inquisitors_rosary"}
R, B = Socket.RED, Socket.BLUE
# The shared rule's picks (STAGE-SM-HM report, designer question): one socket, red on damage and healing gear, blue on
# tank gear; the bonus is the stock +4 rating of the first secondary (Mastery -> Haste, Versatility -> Crit).
SOCKETS = {
    "sm_fairbells_censer": ((R,), 2874), "sm_voss_blessed_signet": ((R,), 2874), "sm_heretics_wand": ((R,), 2874),
    "sm_fissure_touched_grips": ((R,), 3267), "sm_scarlet_garrison_rifle": ((R,), 2874),
    "sm_garrison_bulwark": ((B,), 2972), "sm_staff_of_the_consecrated_hall": ((R,), 2874),
    "sm_fathers_verdict": ((R,), 3267), "sm_treads_of_denial": ((B,), 3359), "sm_inquisitors_rosary": ((R,), 2874),
}
# key -> (spell, trigger, scale)
ITEM_SPELLS = {
    "sm_purebloods_rallying_standard": (STANDARD, SpellTrigger.USE, "budget"),  # review m5: the 5% grows
    "sm_fairbells_censer": (CENSER, SpellTrigger.ON_EQUIP, "budget"),
    "sm_voss_blessed_signet": (SIGNET, SpellTrigger.ON_EQUIP, "budget"),
    "sm_shard_of_the_phylactery": (SHARD, SpellTrigger.USE, "budget"),
    "sm_heretics_wand": (WAND, SpellTrigger.ON_EQUIP, "budget"),
    "sm_fissure_touched_grips": (GRIPS, SpellTrigger.ON_EQUIP, "budget"),
    "sm_scarlet_garrison_rifle": (RIFLE, SpellTrigger.ON_EQUIP, "budget"),
    "sm_garrison_bulwark": (BULWARK, SpellTrigger.ON_EQUIP, "budget"),
    "sm_staff_of_the_consecrated_hall": (STAFF, SpellTrigger.ON_EQUIP, "budget"),
    "sm_fathers_verdict": (FATHERS_VERDICT, SpellTrigger.ON_EQUIP, "budget"),
    "sm_treads_of_denial": (TREADS, SpellTrigger.ON_EQUIP, "budget"),  # review m5: the 10% grows
    "sm_inquisitors_rosary": (ROSARY, SpellTrigger.ON_EQUIP, None),
}
PAYOUTS = (PENITENT_FIRE, BLESSING, SHARD, ICY_DEATH, FISSURE, VOLLEY, PILLAR, CONSECRATED_PILLAR, VERDICT)


def _shape_words(name: str | None) -> tuple:
    if name is None:
        return ()
    return tuple(name.replace(" (Solo)", "").split("/"))


class ScarletMonasteryHardModeItemsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load_items_registry()
        cls.spells = {int(e["id"]): e for e in cls.reg.spells if int(e["id"]) in RESERVATION}
        cls.decls = {e["id"]: e["_decl"] for e in cls.reg.item_declarations if e["id"] in DOC_LIST}
        cls.procs = {int(r["SpellId"]): r for r in cls.reg.spell_procs if int(r["SpellId"]) in RESERVATION}

    # --- the list ------------------------------------------------------------------------------------------------

    def test_the_list(self):
        self.assertEqual(set(self.decls), set(DOC_LIST))
        for key, decl in self.decls.items():
            name = DOC_LIST[key][0]
            self.assertEqual(decl.name, name, key)
            self.assertEqual(decl.ladder.name, "vanilla_hard_mode", key)
            self.assertIsNone(decl.base, key)                       # all new
            self.assertIsNotNone(decl.like, key)                    # a stock look
            self.assertEqual(dict(decl.columns).get("bonding"), 1, key)  # Bind on Pickup

    def test_doc_stats(self):
        for key, (_, _, _, _, stats) in DOC_LIST.items():
            decl = self.decls[key]
            primary = [s for s in stats if s in PRIMARIES]
            secondary = tuple(s for s in stats if s not in PRIMARIES)
            self.assertEqual(_shape_words(decl.primary), tuple(primary), key)
            self.assertEqual(set(_shape_words(decl.secondary)), set(secondary), key)
            if not primary:
                self.assertIn(key, JEWELRY, key)
                self.assertEqual(decl.primary_share, 0, key)

    def test_type_and_slot_follow_the_look(self):
        # like= copies class, subclass and InventoryType: every look donor is of the doc's type and slot.
        rows = id_blocks.spell_tables.load_live_item_template_rows()
        for key, (_, item_class, subclass, inventory_type, _) in DOC_LIST.items():
            donor = rows[self.decls[key].like]
            got = (int(donor["class"]), int(donor["subclass"]), int(donor["InventoryType"]))
            self.assertEqual(got, (item_class, subclass, inventory_type), key)
        self.assertEqual(dict(self.decls["sm_scarlet_garrison_rifle"].columns)["ammo_type"], 0)

    def test_declared_multipliers(self):
        """The Blackrock gear fix pass (REVIEW S1 and S3): the weapon-tier items whose cell is thin or jumps at 101
        declare a multiplier (and the wand and the sword their DPS fraction); the rest take the cell or the
        plain default."""
        declared = {k: d.budget_mult for k, d in self.decls.items() if d.budget_mult is not None}
        self.assertEqual(declared, {
            "sm_heretics_wand": 0.6, "sm_scarlet_garrison_rifle": 0.6, "sm_garrison_bulwark": 0.6,
            "sm_staff_of_the_consecrated_hall": 0.5537, "sm_fathers_verdict": 0.5537,
        })
        dps = {k: d.extra_dps for k, d in self.decls.items() if d.extra_dps is not None}
        # The gun declares no DPS fraction: bows, guns and crossbows take dps_delta 0 (level60-stat-curve 1.8).
        self.assertEqual(dps, {"sm_heretics_wand": -0.2, "sm_fathers_verdict": 0.0695})

    def test_every_shape_stat_is_on_every_tier(self):
        """The materialized rows: every doc stat has at least one point on every tier (REVIEW S3)."""
        assert_shape_stats_on_every_tier(self, self.decls)

    def test_sockets(self):
        socketed = {k: (d.sockets, d.socket_bonus) for k, d in self.decls.items() if d.sockets}
        self.assertEqual(socketed, SOCKETS)
        for key in TRINKETS:
            self.assertIsNone(self.decls[key].sockets, key)  # trinkets never
            self.assertIsNone(self.decls[key].socket_bonus, key)

    # --- the effects ---------------------------------------------------------------------------------------------

    def test_ids_sit_in_their_reservation(self):
        self.assertEqual(sorted(self.spells), list(range(STANDARD, RESOLVE + 1)))
        self.assertEqual(id_blocks.out_of_reservation("scarlet_monastery_items", {"spell": set(self.spells)}), [])
        npcs = id_blocks.declared_ids(TOOL_ROOT / "source" / "npcs" / "scarlet_monastery")
        items = [c for c in sorted(set(npcs["creature"]))
                 if not id_blocks.out_of_reservation("scarlet_monastery_items", {"creature": [c]})]
        self.assertEqual(items, [BANNER_NPC])

    def test_the_cpp_header_names_the_same_ids(self):
        text = HEADER.read_text()
        named = {name: int(value) for name, value in re.findall(r"\b(SPELL_[A-Z_]+)\s*=\s*(\d+)", text)}
        self.assertEqual(sorted(named.values()), list(range(STANDARD, RESOLVE + 1)))
        for spell_id, spell in self.spells.items():
            constant = "SPELL_" + re.sub(r"[^A-Z]+", "_", spell["name"].upper().replace("'", "")).strip("_")
            self.assertEqual(named.get(constant), spell_id, constant)
        self.assertRegex(text, rf"\bNPC_RALLYING_STANDARD\s*=\s*{BANNER_NPC}\b")

    def test_every_binding_is_a_registered_script(self):
        registered = set(re.findall(r"RegisterSpellScript\((\w+)\)", SCRIPT.read_text()))
        bound = {(int(r["spell_id"]), r["ScriptName"]) for r in self.reg.spell_script_names
                 if int(r["spell_id"]) in RESERVATION}
        once = "spell_sm_one_roll_per_cast"
        self.assertEqual(bound, {
            (STANDARD, "spell_sm_pureblood_rallying_standard"),
            (CENSER, once), (SIGNET, once), (WAND, once), (GRIPS, once), (RIFLE, once), (STAFF, once),
            (FATHERS_VERDICT, "spell_sm_fathers_verdict"), (ROSARY, "spell_sm_inquisitors_rosary"),
        })
        self.assertEqual({name for _, name in bound}, registered)

    def test_items_carry_their_spell(self):
        for key, (spell_id, trigger, scale) in ITEM_SPELLS.items():
            decl = self.decls[key]
            self.assertEqual(len(decl.spells), 1, key)
            item_spell = decl.spells[0]
            self.assertEqual((item_spell.spell_id, item_spell.trigger, item_spell.scale), (spell_id, trigger, scale),
                             key)
            self.assertEqual(item_spell.cooldown, -1, key)  # the spell's own cooldown

    def test_numbers_come_from_potency(self):
        for spell_id in PAYOUTS:
            effect = self.spells[spell_id]["effect1"]
            self.assertIn(effect["type"], (SCHOOL_DAMAGE, HEAL, APPLY_AURA), spell_id)
            self.assertTrue(effect.get("_potency"), spell_id)
            if effect["type"] != APPLY_AURA or effect["apply_aura"] != SCHOOL_ABSORB:
                self.assertNotEqual(int(self.spells[spell_id]["raw_overrides"]["DefenseType"]), 0, spell_id)
        for spell_id in (BLESSING, SHARD):
            self.assertEqual(self.spells[spell_id]["effect1"]["apply_aura"], SCHOOL_ABSORB, spell_id)
        # every damage or heal potency is distinct, so no two tooltips join one copy family
        potencies = [repr(self.spells[s]["effect1"]["_potency"]) for s in PAYOUTS]
        self.assertEqual(len(potencies), len(set(potencies)))
        # the volley adds ranged attack power: ranged class and the ranged weapon subclass mask
        raw = self.spells[VOLLEY]["raw_overrides"]
        self.assertEqual(int(raw["DefenseType"]), 3)
        self.assertTrue(int(raw["EquippedItemSubclass"]) & (1 << 3))  # guns

    def test_tooltips(self):
        for spell_id, spell in self.spells.items():
            raw = spell["raw_overrides"]
            self.assertEqual(raw["EquippedItemClass"], -1, spell_id)
            self.assertNotIn("{pot", raw["Description_Lang_enUS"], spell_id)
            self.assertNotRegex(raw.get("AuraDescription_Lang_enUS", ""), r"\$", spell_id)
        self.assertEqual(self.spells[RECENTLY_RALLIED]["raw_overrides"]["AuraDescription_Lang_enUS"],
                         "Cannot benefit from a Rallying Standard.")  # the doc's debuff text

    def test_spell_shapes(self):
        s = self.spells
        # Pureblood's Rallying Standard: 15 sec, 10 yd, 5% more damage, 2 min cooldown and lockout
        self.assertEqual((s[STANDARD]["duration_ms"], s[STANDARD]["cooldown_ms"]), (15000, 120000))
        self.assertEqual(s[STANDARD]["effect1"]["radius_yards"], 10.0)
        self.assertEqual(s[RALLIED]["effect1"]["base_points"] + 1, 5)
        self.assertEqual(s[RECENTLY_RALLIED]["duration_ms"], 120000)
        # the Censer's fire: 8 sec, stacks 3; the Signet's shield 6 sec
        self.assertEqual(s[CENSER]["effect1"]["trigger_spell"], PENITENT_FIRE)
        self.assertEqual(s[PENITENT_FIRE]["duration_ms"], 8000)
        self.assertEqual(int(s[PENITENT_FIRE]["raw_overrides"]["CumulativeAura"]), 3)
        self.assertEqual(s[SIGNET]["effect1"]["trigger_spell"], BLESSING)
        self.assertEqual(s[BLESSING]["duration_ms"], 6000)
        # the Shard: 15 sec, 10% more spell damage and healing, 2 min cooldown
        self.assertEqual((s[SHARD]["duration_ms"], s[SHARD]["cooldown_ms"]), (15000, 120000))
        self.assertEqual(s[SHARD]["effect2"]["base_points"] + 1, 10)
        self.assertEqual(s[SHARD]["effect3"]["base_points"] + 1, 10)
        # Icy Death: 8 sec, 30% slower
        self.assertEqual(s[WAND]["effect1"]["trigger_spell"], ICY_DEATH)
        self.assertEqual(s[ICY_DEATH]["duration_ms"], 8000)
        self.assertEqual(s[ICY_DEATH]["effect2"]["base_points"] + 1, -30)
        # the fissure 6 yd, the volley 5 yd, the pillar 5 yd, the Verdict 8 yd and 2 more enemies
        self.assertEqual(s[GRIPS]["effect1"]["trigger_spell"], FISSURE)
        self.assertEqual(s[FISSURE]["effect1"]["radius_yards"], 6.0)
        self.assertEqual(s[RIFLE]["effect1"]["trigger_spell"], VOLLEY)
        self.assertEqual(s[VOLLEY]["effect1"]["radius_yards"], 5.0)
        self.assertEqual(s[BULWARK]["effect1"]["trigger_spell"], PILLAR)
        self.assertEqual(s[STAFF]["effect1"]["trigger_spell"], CONSECRATED_PILLAR)
        self.assertEqual(s[CONSECRATED_PILLAR]["effect1"]["radius_yards"], 5.0)
        self.assertEqual(s[FATHERS_VERDICT]["effect1"]["radius_yards"], 8.0)
        self.assertEqual(s[FATHERS_VERDICT]["effect1"]["base_points"] + 1, 2)
        # Denial: 10% less damage taken for 6 sec; the Rosary: below 50%, Versatility for 8 sec
        self.assertEqual(s[TREADS]["effect1"]["trigger_spell"], DENIAL)
        self.assertEqual(s[DENIAL]["effect1"]["base_points"] + 1, -10)
        self.assertEqual(s[DENIAL]["duration_ms"], 6000)
        self.assertEqual(s[ROSARY]["effect1"]["base_points"] + 1, 50)
        self.assertEqual(s[RESOLVE]["duration_ms"], 8000)
        self.assertEqual((s[RESOLVE]["effect1"]["apply_aura"], s[RESOLVE]["effect1"]["misc_value"]), (306, 1 << 21))

    def test_short_areas_hit_every_enemy(self):
        """Designer ruling B8 (2026-11-20): an area of about 10 yd or less hits every enemy in it, in combat or not.
        The Fissure (6 yd), the Volley (5 yd) and the Verdict's extra targets (8 yd) carry no in-combat filter."""
        for spell_id, radius in ((FISSURE, 6.0), (VOLLEY, 5.0), (FATHERS_VERDICT, 8.0)):
            self.assertLessEqual(self.spells[spell_id]["effect1"]["radius_yards"], 10.0, spell_id)
        bound = {int(r["spell_id"]) for r in self.reg.spell_script_names if int(r["spell_id"]) in RESERVATION}
        self.assertNotIn(FISSURE, bound)
        self.assertNotIn(VOLLEY, bound)
        source = SCRIPT.read_text()
        self.assertNotIn("IsInCombat", source)
        self.assertNotIn("spell_sm_engaged_area", source)

    def test_haunting_mark_ignores_the_item_spells(self):
        """Review m2: HauntedSetUnitHooks::ModifySpellDamageTaken skips the Scarlet Monastery item spells and their
        tier copies (Garrison Volley is ranged class and would consume a Beaststalker's Haunting Mark). The predicate
        itself is host-tested (tests/scarlet_monastery_hard_mode_items_test.cpp, TestIsItemSpell)."""
        haunted = (REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "DungeonSets" /
                   "haunted_set_bonuses.cpp").read_text(encoding="utf-8")
        self.assertIn('#include "ScarletMonasteryHardModeItemsLogic.h"', haunted)
        hook = haunted.split("void ModifySpellDamageTaken(", 1)[1].split("void OnSpellDamageTakenFinal(", 1)[0]
        self.assertIn("ScarletMonasteryHardModeItems::IsItemSpell(spellInfo->Id)", hook)

    def test_recently_rallied_survives_death_and_immunities(self):
        """Review m3: Sated's attributes, so neither a school immunity nor death sheds the lockout."""
        spell = self.spells[RECENTLY_RALLIED]
        self.assertTrue(spell["attributes"] & 0x20000000)  # SPELL_ATTR0_NO_IMMUNITIES
        self.assertTrue(spell["attributes"] & 0x04000000)  # still a debuff (cannot be clicked off)
        self.assertTrue(int(spell["raw_overrides"]["AttributesEx3"]) & 0x00100000)  # ALLOW_AURA_WHILE_DEAD

    def test_scaled_percents(self):
        """Review m5: the Standard's family is itself and Rallied (the lockout stays one spell, so any standard's
        lockout blocks every other), Treads' is itself and Denial; both percents grow with the tier's ratio."""
        from lib import item_spell_copies  # noqa: PLC0415

        spells = [{**entry, "_source_class": item_spell_copies.SOURCE_CLASS} for entry in self.reg.spells]
        index = item_spell_copies.SpellIndex.build({"spells": spells, "linked_spells": self.reg.linked_spells})
        self.assertEqual(index.family(STANDARD), [STANDARD, RALLIED])
        self.assertEqual(index.family(TREADS), [TREADS, DENIAL])
        self.assertNotIn(f"${RECENTLY_RALLIED}", self.spells[STANDARD]["raw_overrides"]["Description_Lang_enUS"])
        # The hard mode ladder's ratios 1.0545 / 1.1091 / 1.2545 (dbc-tools.md, IV10).
        for ratio, rallied, denial in ((1.0545, 5, -11), (1.1091, 6, -11), (1.2545, 6, -13)):
            remap = {STANDARD: 1, RALLIED: 2, TREADS: 3, DENIAL: 4}
            copies = item_spell_copies.build_copies(index, [STANDARD, RALLIED], remap, ratio, "test")
            copies.update(item_spell_copies.build_copies(index, [TREADS, DENIAL], remap, ratio, "test"))
            got_rallied = copies[RALLIED].effects[0]
            got_denial = copies[DENIAL].effects[0]
            self.assertEqual(got_rallied.base_points + 1, rallied, ratio)
            self.assertEqual(got_denial.base_points + 1, denial, ratio)
            self.assertEqual(copies[TREADS].effects[0].trigger_spell, 4)  # the tier's own Denial

    def test_proc_rows(self):
        self.assertEqual(set(self.procs), {CENSER, SIGNET, WAND, GRIPS, RIFLE, BULWARK, STAFF, FATHERS_VERDICT, TREADS,
                                           ROSARY})
        for spell_id, row in self.procs.items():
            self.assertEqual(row["ProcFlags"] & 0x00040000, 0, spell_id)  # never periodic ticks
            self.assertGreater(row["Chance"], 0, spell_id)
            self.assertLess(row["Chance"], 100, spell_id)
        self.assertEqual(self.procs[GRIPS]["ProcFlags"], 0x10)  # melee abilities only (no auto attacks)
        self.assertEqual(self.procs[RIFLE]["ProcFlags"], 0x140)  # ranged auto attacks and ranged abilities
        self.assertEqual(self.procs[FATHERS_VERDICT]["ProcFlags"], 0x14)  # melee hits
        self.assertEqual((self.procs[BULWARK]["ProcFlags"], self.procs[BULWARK]["HitMask"]), (0x28, 0x40))  # blocks
        self.assertEqual((self.procs[TREADS]["ProcFlags"], self.procs[TREADS]["HitMask"]), (0x28, 0x20))  # parries
        for spell_id in (SIGNET, STAFF, ROSARY):
            self.assertEqual((self.procs[spell_id]["SpellTypeMask"], self.procs[spell_id]["SpellPhaseMask"]),
                             (0x2, 0x2), spell_id)  # landed heals
        for spell_id in (CENSER, WAND):
            self.assertEqual(self.procs[spell_id]["Cooldown"], 0, spell_id)  # the stack / refresh needs procs
        for spell_id in (GRIPS, RIFLE, STAFF, FATHERS_VERDICT):
            self.assertGreater(self.procs[spell_id]["Cooldown"], 0, spell_id)  # an area payout is throttled


if __name__ == "__main__":
    unittest.main()
