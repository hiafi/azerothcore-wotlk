"""
The Gnomeregan hard mode items and their effects (the Gnomeregan gear stage, GG-HM): source/items/
gnomeregan_hard_mode.py, source/items/gnomeregan_hard_mode_effects.py, the Walking Bomb's look in source/npcs/
gnomeregan/hard_mode_items.py and the scripts in modules/mod-dungeon-bosses (src/Gnomeregan/hard_mode_items.cpp,
GnomereganHardModeItemsLogic.h).

Checks:
  - the list: the three items of the dungeon doc's hard mode list (docs/dungeons/gnomeregan-rework.md ## Loot, rulings
    56 to 58; the table is copied below because docs/ is not in every checkout), all new on the hard mode ladder, Bind
    on Pickup, a stock look, the doc's type, slot, primary and secondaries, the socket pick (one, trinkets none), the
    declared multiplier, no ammo, and every shape stat on every materialized tier;
  - the effect spells and the bomb sit in the `gnomeregan_items` reservation, the C++ header names the same ids, every
    scripted_by() name is a script hard_mode_items.cpp registers;
  - each item carries its spell with the right trigger, all three scaled ("budget");
  - Meltdown's pulse and the blast come from potency, every tooltip placeholder is expanded, item spells pass the
    triggered-cast rules (EquippedItemClass -1, a potency damage spell is never DmgClass NONE, payouts never proc);
  - the numbers (15 sec, 2 min, +15% / +20%, a pulse every 3 sec, 8 yd; 35% on a crit, 10 sec, an 8 sec bomb, a 3 yd
    fuse, 8 yd; 5 punches, a 30 sec lock, 10 sec of +50 haste and +70 crit rating), the in-combat filters, the
    once-per-cast guard, the punch rule and the proc rows;
  - the tier copies: the pulse, Meltdown's damage bonus, the blast and Clearance's ratings grow with the tier, the
    risk, the counts and Punched do not.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_gnomeregan_hard_mode_items.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Gnomeregan"
HEADER = MODULE_DIR / "GnomereganHardModeItemsLogic.h"
SCRIPT = MODULE_DIR / "hard_mode_items.cpp"
NPCS = TOOL_ROOT / "source" / "npcs" / "gnomeregan"

MELTDOWN, PULSE, LAUNCHER, MARK, BLAST, CARD, PUNCHED, CLEARANCE = range(214240, 214248)
DECLARED = range(MELTDOWN, CLEARANCE + 1)
RESERVATION = range(214240, 214280)
BOMB = 301100
CREATURES = range(301100, 301105)

SCHOOL_DAMAGE = 2
APPLY_AURA = 6
DUMMY_AURA = 4
PERIODIC_DUMMY = 226
PERIODIC_TRIGGER_SPELL = 23
MOD_DAMAGE_PERCENT_DONE = 79
MOD_DAMAGE_PERCENT_TAKEN = 87
MOD_RATING = 189
NO_AURA_CANCEL = 0x80000000
PASSIVE = 0x40
NO_REFLECTION = 0x00000080
SUPPRESS_CASTER_PROCS = 0x00010000
ALWAYS_AOE_LINE_OF_SIGHT = 0x04000000
RANGED_WEAPON_SUBCLASS_MASK = (1 << 2) | (1 << 3) | (1 << 18) | (1 << 16)
HASTE_RATING_MASK = 917504
CRIT_RATING_MASK = 1792
BOMB_TAIL_MS = 1000

# gnomeregan-rework.md ## Loot, "Hard mode: Mekgineer Thermaplugg, the Whole Workshop" (approved 2026-11-24), copied:
# key -> (name, item_template class, subclass, InventoryType, the doc's stats in order).
DOC_LIST = {
    "gnomer_leaking_reactor_core": ("Leaking Reactor Core", 4, 0, 12, ("Strength", "Crit", "Mastery")),
    "gnomer_walking_bomb_launcher": ("Walking Bomb Launcher", 2, 3, 26, ("Agility", "Crit", "Proc Chance")),
    "gnomer_master_punch_card": ("Master Punch Card", 4, 0, 12, ("Intellect", "Haste", "Versatility")),
}
TRINKETS = {"gnomer_leaking_reactor_core", "gnomer_master_punch_card"}
# key -> (spell, trigger)
ITEM_SPELLS = {
    "gnomer_leaking_reactor_core": (MELTDOWN, SpellTrigger.USE),
    "gnomer_walking_bomb_launcher": (LAUNCHER, SpellTrigger.ON_EQUIP),
    "gnomer_master_punch_card": (CARD, SpellTrigger.ON_EQUIP),
}
SHAPE_WORDS = {"Proc": "Proc Chance"}


def _shape_words(name: str) -> tuple:
    return tuple(SHAPE_WORDS.get(word, word) for word in name.replace(" (Solo)", "").split("/"))


class GnomereganHardModeItemsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = _load_items_registry()
        cls.spells = {int(e["id"]): e for e in cls.reg.spells if int(e["id"]) in DECLARED}
        cls.decls = {e["id"]: e["_decl"] for e in cls.reg.item_declarations if e["id"] in DOC_LIST}
        cls.procs = {int(r["SpellId"]): r for r in cls.reg.spell_procs if int(r["SpellId"]) in RESERVATION}
        cls.source = SCRIPT.read_text()
        cls.header = HEADER.read_text()

    def _raw(self, spell_id: int) -> dict:
        return self.spells[spell_id]["raw_overrides"]

    def _description(self, spell_id: int) -> str:
        return self._raw(spell_id)["Description_Lang_enUS"]

    def _script(self, name: str) -> str:
        return self.source.split(f"class {name} ", 1)[1].split("\n};\n", 1)[0]

    def _effect(self, spell_id: int, index: int) -> dict:
        return self.spells[spell_id][f"effect{index}"]

    def _amount(self, spell_id: int, index: int) -> int:
        return self._effect(spell_id, index)["base_points"] + 1

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

    def test_declared_multipliers_sockets_and_looks(self):
        declared = {k: (d.budget_mult, d.extra_dps) for k, d in self.decls.items()
                    if d.budget_mult is not None or d.extra_dps is not None}
        self.assertEqual(declared, {"gnomer_walking_bomb_launcher": (0.6, None)})
        socketed = {k: (d.sockets, d.socket_bonus) for k, d in self.decls.items() if d.sockets}
        self.assertEqual(socketed, {"gnomer_walking_bomb_launcher": ((Socket.RED,), 2874)})
        for key in TRINKETS:
            self.assertIsNone(self.decls[key].sockets, key)  # trinkets never
            self.assertIsNone(self.decls[key].socket_bonus, key)
        self.assertEqual(dict(self.decls["gnomer_walking_bomb_launcher"].columns).get("ammo_type"), 0)
        # the Card wears the Prismatic Punch Card's look (item 9316)
        self.assertEqual(dict(self.decls["gnomer_master_punch_card"].columns).get("displayid"), 40633)

    def test_every_shape_stat_is_on_every_tier(self):
        """The materialized rows: every doc stat has at least one point on every tier (REVIEW S3)."""
        assert_shape_stats_on_every_tier(self, self.decls)

    # --- the effects ---------------------------------------------------------------------------------------------

    def test_ids_sit_in_their_reservation(self):
        self.assertEqual(sorted(self.spells), list(DECLARED))
        self.assertEqual(sorted(int(e["id"]) for e in self.reg.spells if int(e["id"]) in RESERVATION), list(DECLARED))
        self.assertEqual(id_blocks.out_of_reservation("gnomeregan_items", {"spell": set(self.spells)}), [])

    def test_the_cpp_header_names_the_same_ids(self):
        named = {name: int(value) for name, value in re.findall(r"\b((?:SPELL|NPC)_[A-Z_]+)\s*=\s*(\d+)", self.header)}
        self.assertEqual(named, {
            "SPELL_REACTOR_CORE_MELTDOWN": MELTDOWN, "SPELL_REACTOR_CORE_PULSE": PULSE,
            "SPELL_BOMB_LAUNCHER": LAUNCHER, "SPELL_BOMB_LAUNCHER_MARK": MARK, "SPELL_BOMB_LAUNCHER_BLAST": BLAST,
            "SPELL_PUNCH_CARD": CARD, "SPELL_PUNCH_CARD_PUNCHED": PUNCHED, "SPELL_PUNCH_CARD_CLEARANCE": CLEARANCE,
            "NPC_LAUNCHER_WALKING_BOMB": BOMB,
        })
        self.assertIn(f"kSpellsGnomereganItems{{ {RESERVATION.start}, {RESERVATION.stop - 1} }}", self.header)
        self.assertIn(f"kSpellsDeclared{{ {DECLARED.start}, {DECLARED.stop - 1} }}", self.header)
        self.assertIn(f"kCreaturesGnomereganItems{{ {CREATURES.start}, {CREATURES.stop - 1} }}", self.header)
        self.assertEqual({i: s["name"] for i, s in self.spells.items()}, {
            MELTDOWN: "Meltdown", PULSE: "Radiation Pulse", LAUNCHER: "Walking Bomb Launcher", MARK: "Walking Bomb",
            BLAST: "Walking Bomb Blast", CARD: "Master Punch Card", PUNCHED: "Punched",
            CLEARANCE: "Clearance: PRISMATIC",
        })

    def test_the_bomb(self):
        """One look in the reservation: untargetable, friendly, passive, the stock bomb's model, no script."""
        declared = id_blocks.declared_ids(NPCS)
        self.assertEqual(set(declared["creature"]), {BOMB})  # the template and its model
        self.assertEqual(id_blocks.out_of_reservation("gnomeregan_items", {"creature": {BOMB}}), [])
        text = (NPCS / "hard_mode_items.py").read_text()
        self.assertEqual(re.findall(r"creature_template\((\d+), '([^']+)'", text),
                         [(str(BOMB), "Launched Walking Bomb")])
        self.assertIn("_DISPLAY_WALKING_BOMB = 6977", text)   # creature_template_model 7915
        # its own name and a smaller look than Thermaplugg's hostile Walking Bomb (same model, scale 1)
        self.assertIn("_BOMB_SCALE = 0.6", text)
        self.assertIn("creature_model(301100, display_id=_DISPLAY_WALKING_BOMB, scale=_BOMB_SCALE, idx=0)", text)
        self.assertIn("unit_flags=0x2 | 0x02000000", text)
        self.assertIn("faction=35", text)
        self.assertIn("ScriptName=''", text)
        self.assertIn("DamageModifier=0.0", text)
        # the script keeps it passive and runs it at the target: a follow (a chase never starts for a unit with no
        # victim, docs/bugs-and-fixes.md), at its own run speed (no inherited walk state or speed)
        launcher = self._script("spell_gnomer_item_walking_bomb_launcher")
        for rule in ("SetReactState(REACT_PASSIVE)", "bomb->SetWalk(false)",
                     "MoveFollow(victim, 0.0f, 0.0f, MOTION_SLOT_ACTIVE, false, false)", "TEMPSUMMON_TIMED_DESPAWN",
                     "NPC_LAUNCHER_WALKING_BOMB"):
            self.assertIn(rule, launcher)
        self.assertNotIn("MoveChase", launcher)
        # a dead wearer's bomb falls apart (its blast would be refused, caster dead)
        self.assertIn("wearer && wearer->IsInWorld() && wearer->IsAlive()",
                      self._script("spell_gnomer_item_walking_bomb"))

    def test_every_binding_is_a_registered_script(self):
        registered = set(re.findall(r"RegisterSpellScript\((\w+)\)", self.source))
        bound = {(int(r["spell_id"]), r["ScriptName"]) for r in self.reg.spell_script_names
                 if int(r["spell_id"]) in DECLARED}
        self.assertEqual(bound, {
            (PULSE, "spell_gnomer_item_meltdown_pulse"), (LAUNCHER, "spell_gnomer_item_walking_bomb_launcher"),
            (MARK, "spell_gnomer_item_walking_bomb"), (BLAST, "spell_gnomer_item_walking_bomb_blast"),
            (CARD, "spell_gnomer_item_master_punch_card"),
        })
        self.assertEqual({name for _, name in bound}, registered)
        # the handoff's prefix: nothing a boss file of the dungeon build would want
        self.assertTrue(all(name.startswith("spell_gnomer_item_") for name in registered))
        self.assertIn("void AddSC_gnomer_hard_mode_items()", self.source)

    def test_items_carry_their_spell(self):
        for key, (spell_id, trigger) in ITEM_SPELLS.items():
            decl = self.decls[key]
            self.assertEqual(len(decl.spells), 1, key)
            item_spell = decl.spells[0]
            self.assertEqual((item_spell.spell_id, item_spell.trigger, item_spell.scale), (spell_id, trigger, "budget"),
                             key)
            self.assertEqual(item_spell.cooldown, -1, key)  # the spell's own cooldown

    def test_numbers_come_from_potency(self):
        for spell_id, school, potency in ((PULSE, School.NATURE, 50.0), (BLAST, School.FIRE, 150.0)):
            effect = self._effect(spell_id, 1)
            self.assertEqual(effect["type"], SCHOOL_DAMAGE, spell_id)
            self.assertTrue(effect.get("_potency"), spell_id)
            self.assertEqual(int(self._raw(spell_id)["DefenseType"]), 1, spell_id)  # magic
            self.assertEqual(int(self.spells[spell_id]["school"]), int(school), spell_id)
            declared = self.spells[spell_id]["_spell"].effects[0]
            self.assertEqual(declared.ap_potency, potency, spell_id)   # a Strength trinket, an Agility gun
            self.assertFalse(declared.sp_potency, spell_id)
        # the blast reads ranged attack power (server and tooltip), with no weapon requirement
        self.assertEqual(self._raw(BLAST)["EquippedItemSubclass"], RANGED_WEAPON_SUBCLASS_MASK)
        self.assertEqual(self._effect(BLAST, 1)["_potency"]["ap_token"], "$RAP")
        self.assertEqual(self._effect(PULSE, 1)["_potency"]["ap_token"], "$AP")

    def test_payouts_never_proc(self):
        for spell_id in (PULSE, MARK, BLAST, PUNCHED, CLEARANCE):
            self.assertTrue(int(self._raw(spell_id)["AttributesEx3"]) & SUPPRESS_CASTER_PROCS, spell_id)
        for spell_id in (PULSE, BLAST):
            self.assertTrue(int(self._raw(spell_id)["AttributesEx"]) & NO_REFLECTION, spell_id)

    def test_tooltips(self):
        for spell_id, spell in self.spells.items():
            raw = spell["raw_overrides"]
            self.assertEqual(raw["EquippedItemClass"], -1, spell_id)
            self.assertNotIn("{pot", raw["Description_Lang_enUS"], spell_id)
            self.assertNotIn("{pot", raw.get("AuraDescription_Lang_enUS", ""), spell_id)
        self.assertIn("enemies in combat within $214241a1 yd every $t2 sec", self._description(MELTDOWN))
        self.assertIn("you take $s3% more damage", self._description(MELTDOWN))
        self.assertIn("enemies in combat within $214244a1 yd of it", self._description(LAUNCHER))
        self.assertIn("within $214243d", self._description(LAUNCHER))
        self.assertIn("haste rating by $214247s1 and your critical strike rating by $214247s2 for $214247d",
                      self._description(CARD))
        self.assertIn("up to $s1 punches", self._description(CARD))
        self.assertIn("for $s2 sec after Clearance", self._description(CARD))

    def test_meltdown(self):
        s = self.spells[MELTDOWN]
        self.assertEqual((s["duration_ms"], s["cooldown_ms"], self._raw(MELTDOWN)["StartRecoveryTime"],
                          self._raw(MELTDOWN)["StartRecoveryCategory"]), (15000, 120000, 0, 0))
        self.assertTrue(int(s["attributes"]) & NO_AURA_CANCEL)   # the risk cannot be dropped
        self.assertFalse(int(s["attributes"]) & PASSIVE)
        done, pulse, taken = (self._effect(MELTDOWN, i) for i in (1, 2, 3))
        self.assertEqual((done["apply_aura"], done["base_points"] + 1, done["misc_value"]),
                         (MOD_DAMAGE_PERCENT_DONE, 15, 127))
        self.assertEqual((taken["apply_aura"], taken["base_points"] + 1, taken["misc_value"]),
                         (MOD_DAMAGE_PERCENT_TAKEN, 20, 127))
        # mod-playerbots' "use trinket" keeps tank bots off a Use with this effect (an aura raising damage taken; ruling
        # G15 A, GenericSpellActions.cpp RaisesDamageTaken), and treats it as a boost, not a defensive Use, for the rest
        self.assertEqual(taken["type"], APPLY_AURA)
        self.assertEqual((pulse["apply_aura"], pulse["amplitude"], pulse["trigger_spell"]),
                         (PERIODIC_TRIGGER_SPELL, 3000, PULSE))
        # the risk is real: more damage taken than dealt, in percent
        self.assertGreater(taken["base_points"], done["base_points"])
        declared = self.spells[MELTDOWN]["_spell"].effects
        self.assertTrue(declared[0].scale_amount)                # the bonus grows with the tier
        self.assertFalse(declared[2].scale_amount)               # the risk does not
        p = self._effect(PULSE, 1)
        self.assertEqual((p["implicit_target_a"], p["implicit_target_b"], p["radius_yards"]), (22, 15, 8.0))

    def test_launcher_and_bomb(self):
        s = self.spells
        self.assertEqual(self._effect(LAUNCHER, 1)["apply_aura"], DUMMY_AURA)
        self.assertTrue(int(s[LAUNCHER]["attributes"]) & PASSIVE)
        mark = self._effect(MARK, 1)
        self.assertEqual((mark["apply_aura"], mark["amplitude"], mark["implicit_target_a"]), (PERIODIC_DUMMY, 500, 6))
        self.assertEqual(s[MARK]["duration_ms"], 8000)
        # the fuse, the same 3 yd on the Equip and on the mark (the mark's is the one the script reads)
        self.assertEqual(self._amount(LAUNCHER, 1), 3)
        self.assertEqual(self._amount(MARK, 1), 3)
        blast = self._effect(BLAST, 1)
        self.assertEqual((blast["implicit_target_a"], blast["implicit_target_b"], blast["radius_yards"]),
                         (87, 16, 8.0))
        self.assertTrue(int(self._raw(BLAST)["AttributesEx5"]) & ALWAYS_AOE_LINE_OF_SIGHT)
        self.assertGreaterEqual(s[BLAST]["range_yards"], 100.0)
        self.assertGreaterEqual(s[MARK]["range_yards"], 100.0)
        # the cooldown outlasts a bomb (its mark plus the despawn tail): one bomb per wearer at most
        tail = int(re.search(r"kBombTailMs = (\d+);", self.header).group(1))
        self.assertEqual(tail, BOMB_TAIL_MS)
        self.assertGreater(self.procs[LAUNCHER]["Cooldown"], s[MARK]["duration_ms"] + tail)

    def test_punch_card(self):
        s = self.spells
        self.assertTrue(int(s[CARD]["attributes"]) & PASSIVE)
        self.assertEqual([self._amount(CARD, i) for i in (1, 2)], [5, 30])
        for i in (1, 2):
            self.assertEqual(self._effect(CARD, i)["apply_aura"], DUMMY_AURA)
        # the punches: shown, up to 5, no duration
        self.assertFalse(int(s[PUNCHED].get("attributes") or 0) & PASSIVE)
        self.assertEqual((s[PUNCHED]["duration_ms"], self._raw(PUNCHED)["CumulativeAura"]), (-1, 5))
        # Clearance: 10 sec, haste and crit rating (stock ratings: MOD_RATING, never aura 306)
        self.assertEqual(s[CLEARANCE]["duration_ms"], 10000)
        haste, crit = self._effect(CLEARANCE, 1), self._effect(CLEARANCE, 2)
        self.assertEqual((haste["apply_aura"], haste["misc_value"], haste["base_points"] + 1),
                         (MOD_RATING, HASTE_RATING_MASK, 50))
        self.assertEqual((crit["apply_aura"], crit["misc_value"], crit["base_points"] + 1),
                         (MOD_RATING, CRIT_RATING_MASK, 70))
        self.assertFalse(int(s[CLEARANCE].get("attributes") or 0) & PASSIVE)

    def test_damage_reaches_only_enemies_in_combat(self):
        helper = self.source.split("void KeepEnemiesInCombat(", 1)[1].split("\n    }\n", 1)[0]
        self.assertIn("!unit->IsInCombat()", helper)
        self.assertRegex(self._script("spell_gnomer_item_meltdown_pulse"),
                         r"FilterTargets,\s+EFFECT_0, TARGET_UNIT_SRC_AREA_ENEMY")
        self.assertRegex(self._script("spell_gnomer_item_walking_bomb_blast"),
                         r"FilterTargets,\s+EFFECT_0, TARGET_UNIT_DEST_AREA_ENEMY")
        for name in ("spell_gnomer_item_meltdown_pulse", "spell_gnomer_item_walking_bomb_blast"):
            self.assertIn("KeepEnemiesInCombat(targets)", self._script(name))

    def test_the_scripts_follow_the_rules(self):
        launcher = self._script("spell_gnomer_item_walking_bomb_launcher")
        check = launcher.split("bool CheckProc", 1)[1].split("void HandleProc", 1)[0]
        self.assertIn("FirstRollOfCast(_rolled, eventInfo)", check)            # one roll per cast
        proc = launcher.split("void HandleProc", 1)[1]
        # the mark first, the bomb only for a mark that landed, the bomb handed to the mark
        self.assertLess(proc.index("CastSpell(victim, markId"), proc.index("SummonCreature("))
        self.assertIn("if (!holder)\n            return;", proc)
        self.assertIn("holder->SetBomb(bomb->GetGUID())", proc)
        mark = self._script("spell_gnomer_item_walking_bomb")
        self.assertIn("StepBomb(target->IsAlive()", mark)
        self.assertIn("bomb->IsWithinDist(target, float(std::max(aurEff->GetAmount(), 0)))", mark)
        self.assertIn("CastSpell(bomb->GetPositionX(), bomb->GetPositionY(), bomb->GetPositionZ(), blastId", mark)
        self.assertIn("bomb->DespawnOrUnsummon()", mark.split("void HandleRemove", 1)[1])
        card = self._script("spell_gnomer_item_master_punch_card")
        card_check = card.split("bool CheckProc", 1)[1].split("void HandleProc", 1)[0]
        for rule in ("PROC_SPELL_PHASE_CAST", "eventInfo.GetActor() != wearer", "spell->IsTriggered()",
                     "spell->m_CastItem != nullptr", "IsAutoRepeatRangedSpell()", "IsPassive()",
                     "SyncCard(_card, StacksOf(wearer, SPELL_PUNCH_CARD_PUNCHED))", "NowMs() >= _readyAtMs",
                     "!IsPunched(_card, FirstRankOf(spellInfo))"):
            self.assertIn(rule, card_check)
        self.assertIn("GetFirstRankSpell()", self.source)
        self.assertIn("_readyAtMs = now + uint64(std::max(lock->GetAmount(), 0)) * uint64(IN_MILLISECONDS)", card)
        for handler in ("void HandleApply", "void HandleRemove"):
            body = card.split(handler, 1)[1].split("}\n", 1)[0]
            self.assertIn("ClearCard(_card)", body)
            self.assertIn("RemoveAurasDueToSpell(SPELL_PUNCH_CARD_PUNCHED)", body)
        # a script casts its tier's copy of a scaled spell and the shared base of Punched
        for base in ("SPELL_BOMB_LAUNCHER_MARK", "SPELL_BOMB_LAUNCHER_BLAST", "SPELL_PUNCH_CARD_CLEARANCE"):
            self.assertIn(f"TierSpell(GetSpellInfo(), {base})", self.source)
        self.assertNotRegex(self.source, r"TierSpell\([^)]*\bSPELL_PUNCH_CARD_PUNCHED\)")

    def test_scaled_tiers(self):
        """The copy families (the pulse, Meltdown's bonus, the blast and Clearance's ratings grow with the tier; the
        risk, the counts and Punched stay)."""
        from lib import item_spell_copies  # noqa: PLC0415

        spells = [{**entry, "_source_class": item_spell_copies.SOURCE_CLASS} for entry in self.reg.spells]
        index = item_spell_copies.SpellIndex.build({"spells": spells, "linked_spells": self.reg.linked_spells})
        self.assertEqual(index.family(MELTDOWN), [MELTDOWN, PULSE])
        self.assertEqual(sorted(index.family(LAUNCHER)), [LAUNCHER, MARK, BLAST])
        self.assertEqual(sorted(index.family(CARD)), [CARD, CLEARANCE])
        # The hard mode ladder's ratios 1.0545 / 1.1091 / 1.2545 (dbc-tools.md, IV10).
        remap = {MELTDOWN: 1, PULSE: 2, LAUNCHER: 3, MARK: 4, BLAST: 5, CARD: 6, CLEARANCE: 7}
        for ratio, bonus, haste, crit in ((1.0545, 16, 53, 74), (1.1091, 17, 55, 78), (1.2545, 19, 63, 88)):
            copies = {}
            for root in (MELTDOWN, LAUNCHER, CARD):
                copies.update(item_spell_copies.build_copies(index, index.family(root), remap, ratio, "test"))
            self.assertAlmostEqual(copies[PULSE].effects[0].ap_potency, 50.0 * ratio)
            self.assertAlmostEqual(copies[BLAST].effects[0].ap_potency, 150.0 * ratio)
            self.assertEqual([e.base_points + 1 for e in copies[MELTDOWN].effects if e][0::2], [bonus, 20], ratio)
            self.assertEqual(copies[MELTDOWN].effects[1].trigger_spell, 2)           # its own tier's pulse
            self.assertEqual([e.base_points + 1 for e in copies[CLEARANCE].effects if e], [haste, crit], ratio)
            self.assertEqual([e.base_points + 1 for e in copies[CARD].effects if e], [5, 30])  # the counts stay
            self.assertEqual([e.base_points + 1 for e in copies[LAUNCHER].effects if e], [3])
            self.assertEqual([e.base_points + 1 for e in copies[MARK].effects if e], [3])

    def test_proc_rows(self):
        self.assertEqual(set(self.procs), {LAUNCHER, CARD})
        launcher = self.procs[LAUNCHER]
        self.assertEqual((launcher["ProcFlags"], launcher["SpellTypeMask"], launcher["SpellPhaseMask"],
                          launcher["HitMask"], launcher["Chance"], launcher["Cooldown"], launcher["AttributesMask"]),
                         (0x140, 0x1, 0x2, 0x2, 35.0, 10000, 0))
        card = self.procs[CARD]
        self.assertEqual((card["ProcFlags"], card["SpellTypeMask"], card["SpellPhaseMask"], card["HitMask"],
                          card["Chance"], card["Cooldown"], card["AttributesMask"]),
                         (0x15510, 0x7, 0x1, 0, 100.0, 0, 0))
        for row in self.procs.values():
            self.assertEqual((row["SpellFamilyName"], row["Charges"]), (0, 0))
        # the header's flags are the rows'
        for name, row in (("kRangedHitFlags", launcher), ("kOwnCastFlags", card)):
            flags = re.search(rf"{name} = ([^;]+);", self.header).group(1)
            self.assertEqual(sum(int(f.strip().rstrip("u"), 16) for f in flags.split("|")), row["ProcFlags"], name)
        # the Spell.dbc columns say the same
        self.assertEqual((self._raw(LAUNCHER)["ProcTypeMask"], self._raw(LAUNCHER)["ProcChance"]), (0x140, 35))
        self.assertEqual((self._raw(CARD)["ProcTypeMask"], self._raw(CARD)["ProcChance"]), (0x15510, 100))


if __name__ == "__main__":
    unittest.main()
