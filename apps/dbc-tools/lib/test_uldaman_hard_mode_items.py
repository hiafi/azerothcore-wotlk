"""
The Uldaman hard mode items and their effects (the Uldaman gear stage, UG-HM): source/items/uldaman_hard_mode.py,
source/items/uldaman_hard_mode_effects.py, the Waking Earthen's look in source/npcs/uldaman/hard_mode_items.py and the
scripts in modules/mod-dungeon-bosses (src/Uldaman/hard_mode_items.cpp, UldamanHardModeItemsLogic.h).

Checks:
  - the list: the three items of the dungeon doc's hard mode list (docs/dungeons/uldaman-rework.md ## Loot, ruling 35;
    the table is copied below because docs/ is not in every checkout), all new on the hard mode ladder, Bind on
    Pickup, a stock look, the doc's type, slot, primary and secondaries, the socket picks (one, trinkets none), no
    declared multiplier, and every shape stat on every materialized tier;
  - the effect spells and the earthen sit in the `uldaman_items` reservation, the C++ header names the same ids, every
    scripted_by() name is a script hard_mode_items.cpp registers, all prefixed `spell_uldaman_item_`;
  - each item carries its spell with the right trigger, all three scaled ("budget");
  - the trample comes from potency (melee class, Physical, no dodge, parry or block), every tooltip placeholder is
    expanded, item spells pass the triggered-cast rules (EquippedItemClass -1, payouts never proc);
  - the numbers (2 min, a 20 yd march, a 3 yd half width, AP potency 400, the War Stomp knockback; 8 sec, 3 stacks,
    +10 haste rating; 6 sec recording, 50%, 6 sec replay in 1 sec ticks), the in-combat filter, the knockback rule, the
    Choker's spell rule, the Disk's record and handover, and the proc rows;
  - the tier copies: the trample, Two Lights' rating and the replay share grow with the tier (Two Lights on the
    secondary-curve ratio, 10 / 14 / 18 / 25 a stack, the others on the primary), the march, the width, the knockback
    and the Disk's replay and heal do not.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_uldaman_hard_mode_items.py
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

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "Uldaman"
HEADER = MODULE_DIR / "UldamanHardModeItemsLogic.h"
SCRIPT = MODULE_DIR / "hard_mode_items.cpp"
NPCS = TOOL_ROOT / "source" / "npcs" / "uldaman"
DOC = REPO_ROOT / "docs" / "dungeons" / "uldaman-rework.md"

STONE, TRAMPLE, CHOKER, LIGHTS, RECORDING, REPLAY, REPLAY_HEAL = range(214680, 214687)
DECLARED = range(STONE, REPLAY_HEAL + 1)
RESERVATION = range(214680, 214720)
EARTHEN = 301200
CREATURES = range(301200, 301205)

SCHOOL_DAMAGE = 2
HEAL = 10
KNOCK_BACK = 98
APPLY_AURA = 6
DUMMY_AURA = 4
PERIODIC_DUMMY = 226
MOD_RATING = 189
PASSIVE = 0x40
NO_ACTIVE_DEFENSE = 0x00200000
NO_AURA_CANCEL = 0x80000000
IGNORE_LINE_OF_SIGHT = 0x00000004
CANT_CRIT = 0x20000000
SUPPRESS_CASTER_PROCS = 0x00010000
IGNORE_CASTER_MODIFIERS = 0x20000000
HASTE_RATING_MASK = 917504

# uldaman-rework.md ## Loot, "Hard mode: Archaedas, The Makers' Lights" (approved 2026-11-21, ruling 35), copied:
# key -> (name, item_template class, subclass, InventoryType, the doc's stats in order).
DOC_LIST = {
    "uldaman_waking_stone": ("Waking Stone", 4, 0, 12, ("Strength", "Mastery")),
    "uldaman_lightbound_choker": ("Lightbound Choker", 4, 0, 2, ("Crit", "Haste")),
    "uldaman_fragment_of_the_disks": ("Fragment of the Disks", 4, 0, 23,
                                      ("Intellect", "Versatility", "Mastery", "Crit")),
}
NECK = "uldaman_lightbound_choker"
TRINKETS = {"uldaman_waking_stone"}
# key -> (spell, trigger)
ITEM_SPELLS = {
    "uldaman_waking_stone": (STONE, SpellTrigger.USE),
    "uldaman_lightbound_choker": (CHOKER, SpellTrigger.ON_EQUIP),
    "uldaman_fragment_of_the_disks": (RECORDING, SpellTrigger.USE),
}


def _shape_words(name: str | None) -> tuple:
    return () if name is None else tuple(name.replace(" (Solo)", "").split("/"))


class UldamanHardModeItemsTest(unittest.TestCase):
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
            if key == NECK:                                         # secondaries only (the Rosary precedent)
                self.assertIsNone(decl.primary, key)
                self.assertEqual(set(_shape_words(decl.secondary)), set(stats), key)
                continue
            self.assertEqual(_shape_words(decl.primary), stats[:1], key)
            self.assertEqual(set(_shape_words(decl.secondary)), set(stats[1:]), key)

    @unittest.skipUnless(DOC.is_file(), "docs/ is not in this checkout")
    def test_the_doc_table(self):
        """The copied table above equals the dungeon doc's hard mode rows (names, slots, stats, in order)."""
        text = DOC.read_text()
        section = text.split("**Hard mode: Archaedas, The Makers' Lights**", 1)[1].split("\n\n", 2)[1]
        rows = {}
        for line in section.splitlines():
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 4 and cells[0].startswith("**"):
                rows[cells[0].strip("*")] = tuple(s.strip() for s in cells[3].split(","))
        self.assertEqual(rows, {name: stats for name, _, _, _, stats in DOC_LIST.values()})

    def test_type_and_slot_follow_the_look(self):
        # like= copies class, subclass and InventoryType: every look donor is of the doc's type and slot.
        rows = id_blocks.spell_tables.load_live_item_template_rows()
        for key, (_, item_class, subclass, inventory_type, _) in DOC_LIST.items():
            donor = rows[self.decls[key].like]
            got = (int(donor["class"]), int(donor["subclass"]), int(donor["InventoryType"]))
            self.assertEqual(got, (item_class, subclass, inventory_type), key)

    def test_declared_multipliers_and_sockets(self):
        declared = {k for k, d in self.decls.items() if d.budget_mult is not None or d.extra_dps is not None}
        self.assertEqual(declared, set())
        socketed = {k: (d.sockets, d.socket_bonus) for k, d in self.decls.items() if d.sockets}
        self.assertEqual(socketed, {
            "uldaman_lightbound_choker": ((Socket.RED,), 2874),
            "uldaman_fragment_of_the_disks": ((Socket.RED,), 2874),
        })
        for key in TRINKETS:
            self.assertIsNone(self.decls[key].sockets, key)         # trinkets never
            self.assertIsNone(self.decls[key].socket_bonus, key)

    def test_every_shape_stat_is_on_every_tier(self):
        """The materialized rows: every doc stat has at least one point on every tier (REVIEW S3)."""
        assert_shape_stats_on_every_tier(self, self.decls)

    # --- the effects ---------------------------------------------------------------------------------------------

    def test_ids_sit_in_their_reservation(self):
        self.assertEqual(sorted(self.spells), list(DECLARED))
        self.assertEqual(sorted(int(e["id"]) for e in self.reg.spells if int(e["id"]) in RESERVATION), list(DECLARED))
        self.assertEqual(id_blocks.out_of_reservation("uldaman_items", {"spell": set(self.spells)}), [])

    def test_the_cpp_header_names_the_same_ids(self):
        named = {name: int(value) for name, value in re.findall(r"\b((?:SPELL|NPC)_[A-Z_]+)\s*=\s*(\d+)", self.header)}
        self.assertEqual(named, {
            "SPELL_WAKING_STONE": STONE, "SPELL_WAKING_STONE_TRAMPLE": TRAMPLE, "SPELL_CHOKER": CHOKER,
            "SPELL_CHOKER_TWO_LIGHTS": LIGHTS, "SPELL_DISK_RECORDING": RECORDING, "SPELL_DISK_REPLAY": REPLAY,
            "SPELL_DISK_REPLAY_HEAL": REPLAY_HEAL, "NPC_WAKING_STONE_EARTHEN": EARTHEN,
        })
        self.assertIn(f"kSpellsUldamanItems{{ {RESERVATION.start}, {RESERVATION.stop - 1} }}", self.header)
        self.assertIn(f"kSpellsDeclared{{ {DECLARED.start}, {DECLARED.stop - 1} }}", self.header)
        self.assertIn(f"kCreaturesUldamanItems{{ {CREATURES.start}, {CREATURES.stop - 1} }}", self.header)
        self.assertEqual({i: s["name"] for i, s in self.spells.items()}, {
            STONE: "Waking Stone", TRAMPLE: "Earthen Trample", CHOKER: "Lightbound Choker", LIGHTS: "Two Lights",
            RECORDING: "Fragment of the Disks", REPLAY: "Disk Replay", REPLAY_HEAL: "Echo of the Disks",
        })

    def test_the_earthen(self):
        """One look in the reservation: untargetable, friendly, passive, the wall earthen's model, small, no script."""
        declared = id_blocks.declared_ids(NPCS)
        # the template and its model; the build's own creatures (301205+) will sit in the package too
        self.assertTrue({EARTHEN} <= set(declared["creature"]))
        self.assertEqual(id_blocks.out_of_reservation("uldaman_items", {"creature": {EARTHEN}}), [])
        text = (NPCS / "hard_mode_items.py").read_text()
        self.assertEqual(re.findall(r"creature_template\((\d+), '([^']+)'", text), [(str(EARTHEN), "Waking Earthen")])
        self.assertIn("_DISPLAY_WALL_EARTHEN = 6025", text)   # creature_template_model 7309 and 7077
        # its own name and a smaller look than Archaedas's marchers (same model, scale 1)
        self.assertIn("_EARTHEN_SCALE = 0.6", text)
        self.assertIn("creature_model(301200, display_id=_DISPLAY_WALL_EARTHEN, scale=_EARTHEN_SCALE, idx=0)", text)
        for column in ("unit_flags=0x2 | 0x02000000", "faction=35", "ScriptName=''", "DamageModifier=0.0",
                       "speed_run=1.14286"):
            self.assertIn(column, text)
        # the script keeps it passive and runs it to its end point
        stone = self._script("spell_uldaman_item_waking_stone")
        for rule in ("SetReactState(REACT_PASSIVE)", "earthen->SetWalk(false)",
                     "MovePoint(kMarchPointId, _end, FORCED_MOVEMENT_RUN)", "TEMPSUMMON_TIMED_DESPAWN",
                     "NPC_WAKING_STONE_EARTHEN", "GetFirstCollisionPosition(kEarthenStartDistance, 0.0f)"):
            self.assertIn(rule, stone)
        self.assertIn("earthen->DespawnOrUnsummon()", stone.split("void HandleRemove", 1)[1])

    def test_every_binding_is_a_registered_script(self):
        registered = set(re.findall(r"RegisterSpellScript\((\w+)\)", self.source))
        bound = {(int(r["spell_id"]), r["ScriptName"]) for r in self.reg.spell_script_names
                 if int(r["spell_id"]) in DECLARED}
        self.assertEqual(bound, {
            (STONE, "spell_uldaman_item_waking_stone"), (TRAMPLE, "spell_uldaman_item_earthen_trample"),
            (CHOKER, "spell_uldaman_item_lightbound_choker"),
            (RECORDING, "spell_uldaman_item_fragment_of_the_disks"), (REPLAY, "spell_uldaman_item_disk_replay"),
        })
        self.assertEqual({name for _, name in bound}, registered)
        # the handoff's prefix: nothing a boss file of the dungeon build would want (stock spell_uldaman_* names exist)
        self.assertTrue(all(name.startswith("spell_uldaman_item_") for name in registered))
        self.assertIn("void AddSC_uldaman_hard_mode_items()", self.source)

    def test_items_carry_their_spell(self):
        for key, (spell_id, trigger) in ITEM_SPELLS.items():
            decl = self.decls[key]
            self.assertEqual(len(decl.spells), 1, key)
            item_spell = decl.spells[0]
            self.assertEqual((item_spell.spell_id, item_spell.trigger, item_spell.scale), (spell_id, trigger, "budget"),
                             key)
            self.assertEqual(item_spell.cooldown, -1, key)  # the spell's own cooldown

    def test_the_trample(self):
        damage, knock = self._effect(TRAMPLE, 1), self._effect(TRAMPLE, 2)
        self.assertEqual(damage["type"], SCHOOL_DAMAGE)
        self.assertTrue(damage.get("_potency"))
        declared = self.spells[TRAMPLE]["_spell"].effects[0]
        self.assertEqual((declared.ap_potency, declared.sp_potency), (400.0, 0))  # a Strength trinket
        self.assertEqual(self._effect(TRAMPLE, 1)["_potency"]["ap_token"], "$AP")
        self.assertEqual(int(self.spells[TRAMPLE]["school"]), int(School.NORMAL))   # Physical
        self.assertEqual(int(self._raw(TRAMPLE)["DefenseType"]), 2)                  # melee: melee crit, armor
        self.assertTrue(int(self.spells[TRAMPLE]["attributes"]) & NO_ACTIVE_DEFENSE)
        self.assertTrue(int(self._raw(TRAMPLE)["AttributesEx2"]) & IGNORE_LINE_OF_SIGHT)
        # the stock War Stomp 45 knockback, from the wearer's spot
        self.assertEqual((knock["type"], knock["misc_value"], knock["base_points"] + 1), (KNOCK_BACK, 75, 57))
        self.assertEqual((damage["implicit_target_a"], knock["implicit_target_a"]), (6, 6))
        self.assertGreaterEqual(self.spells[TRAMPLE]["range_yards"], 100.0)

    def test_payouts_never_proc(self):
        for spell_id in (TRAMPLE, LIGHTS, RECORDING, REPLAY, REPLAY_HEAL):
            self.assertTrue(int(self._raw(spell_id)["AttributesEx3"]) & SUPPRESS_CASTER_PROCS, spell_id)

    def test_tooltips(self):
        for spell_id, spell in self.spells.items():
            raw = spell["raw_overrides"]
            self.assertEqual(raw["EquippedItemClass"], -1, spell_id)
            self.assertNotIn("{pot", raw["Description_Lang_enUS"], spell_id)
            self.assertNotIn("{pot", raw.get("AuraDescription_Lang_enUS", ""), spell_id)
        self.assertIn("marches $s1 yd ahead of you", self._description(STONE))
        self.assertIn("within $s2 yd of its path", self._description(STONE))
        self.assertIn("Bosses are not knocked back", self._description(STONE))
        self.assertIn("haste rating by $214683s1 for $214683d, stacking up to $214683u times",
                      self._description(CHOKER))
        self.assertIn("records your healing for $d", self._description(RECORDING))
        self.assertIn("replays $s1% of it on the same targets", self._description(RECORDING))
        self.assertIn("Overhealing is not recorded", self._description(RECORDING))
        # the replay's spells carry no number and no tooltip names them: they stay one spell for every tier
        for spell_id in DECLARED:
            for text in (self._description(spell_id), self._raw(spell_id).get("AuraDescription_Lang_enUS", "")):
                self.assertNotIn(f"${REPLAY}", text)
                self.assertNotIn(f"${REPLAY_HEAL}", text)

    def test_waking_stone(self):
        s = self.spells[STONE]
        self.assertEqual((s["duration_ms"], s["cooldown_ms"], self._raw(STONE)["StartRecoveryTime"],
                          self._raw(STONE)["StartRecoveryCategory"]), (4000, 120000, 0, 0))
        self.assertFalse(int(s.get("attributes") or 0) & PASSIVE)
        march, width = self._effect(STONE, 1), self._effect(STONE, 2)
        self.assertEqual(
            (march["apply_aura"], march["amplitude"], march["base_points"] + 1, march["implicit_target_a"]),
            (PERIODIC_DUMMY, 250, 20, 1))
        self.assertEqual((width["apply_aura"], width["base_points"] + 1), (DUMMY_AURA, 3))
        # a step at 8 yd/s (speed_run 1.14286 x 7) in one tick stays inside the half width: no gap between steps
        self.assertLess(8.0 * march["amplitude"] / 1000.0, 2 * (width["base_points"] + 1))
        # 19 yd at 8 yd/s fits the march's time limit
        self.assertLess((20 - 1) / 8.0 * 1000, s["duration_ms"])
        tail = int(re.search(r"kEarthenTailMs = (\d+);", self.header).group(1))
        self.assertLess(s["duration_ms"] + tail, s["cooldown_ms"])

    def test_choker_and_two_lights(self):
        self.assertTrue(int(self.spells[CHOKER]["attributes"]) & PASSIVE)
        self.assertEqual(self._effect(CHOKER, 1)["apply_aura"], DUMMY_AURA)
        s = self.spells[LIGHTS]
        self.assertFalse(int(s.get("attributes") or 0) & PASSIVE)
        self.assertEqual((s["duration_ms"], self._raw(LIGHTS)["CumulativeAura"]), (8000, 3))
        haste = self._effect(LIGHTS, 1)
        self.assertEqual((haste["apply_aura"], haste["misc_value"], haste["base_points"] + 1),
                         (MOD_RATING, HASTE_RATING_MASK, 10))

    def test_fragment_and_replay(self):
        rec = self.spells[RECORDING]
        self.assertEqual((rec["duration_ms"], rec["cooldown_ms"], self._raw(RECORDING)["StartRecoveryTime"]),
                         (6000, 120000, 0))
        self.assertTrue(int(rec["attributes"]) & NO_AURA_CANCEL)
        share = self._effect(RECORDING, 1)
        self.assertEqual((share["apply_aura"], share["base_points"] + 1), (DUMMY_AURA, 50))
        self.assertTrue(rec["_spell"].effects[0].scale_amount)     # the share grows with the tier
        rep = self.spells[REPLAY]
        tick = self._effect(REPLAY, 1)
        self.assertEqual((rep["duration_ms"], tick["apply_aura"], tick["amplitude"]), (6000, PERIODIC_DUMMY, 1000))
        self.assertTrue(int(rep["attributes"]) & NO_AURA_CANCEL)
        heal = self._effect(REPLAY_HEAL, 1)
        self.assertEqual((heal["type"], heal["base_points"]), (HEAL, 0))
        self.assertFalse(heal.get("_potency"))                     # sized by the script
        self.assertTrue(int(self._raw(REPLAY_HEAL)["AttributesEx2"]) & CANT_CRIT)
        self.assertTrue(int(self._raw(REPLAY_HEAL)["AttributesEx3"]) & IGNORE_CASTER_MODIFIERS)
        self.assertEqual(int(self._raw(REPLAY_HEAL).get("DefenseType", 0)), 0)

    def test_the_trample_reaches_only_enemies_in_combat(self):
        stone = self._script("spell_uldaman_item_waking_stone")
        sweep = stone.split("void Sweep(", 1)[1].split("void HandleTick", 1)[0]
        for rule in ("!unit->IsInCombat()", "!wearer->IsValidAttackTarget(unit)",
                     "HasBreakableByDamageCrowdControlAura(wearer)",
                     "OnMarchPath(from, to, ToPoint(*unit), unit->GetCombatReach(), halfWidth)",
                     "earthen->IsWithinLOSInMap(unit)", "MarkTrampled(_trampled, unit->GetGUID().GetRawValue())",
                     "TierSpell(GetSpellInfo(), SPELL_WAKING_STONE_TRAMPLE)"):
            self.assertIn(rule, sweep)
        tick = stone.split("void HandleTick", 1)[1].split("void HandleRemove", 1)[0]
        self.assertIn("StepMarch(wearerHere, earthenHere, toEnd)", tick)
        self.assertIn("_last = now;", tick)

    def test_the_knockback_spares_bosses(self):
        trample = self._script("spell_uldaman_item_earthen_trample")
        self.assertIn("!CanKnockBack(KnockbackSignsOf(target))", trample)
        self.assertIn("PreventHitDefaultEffect(effIndex)", trample)
        self.assertRegex(trample, r"HandleKnockBack, EFFECT_1,\s+SPELL_EFFECT_KNOCK_BACK")
        signs = self.source.split("KnockbackTarget KnockbackSignsOf(", 1)[1].split("\n    }\n", 1)[0]
        for sign in ("isWorldBoss()", "IsDungeonBoss()", "IsImmuneToKnockback()",
                     "CREATURE_FLAG_EXTRA_INSTANCE_BIND", "dynamic_cast<BossAI const*>"):
            self.assertIn(sign, signs)

    def test_the_scripts_follow_the_rules(self):
        choker = self._script("spell_uldaman_item_lightbound_choker")
        check = choker.split("bool CheckProc", 1)[1].split("void HandleProc", 1)[0]
        for rule in ("PROC_SPELL_PHASE_CAST", "eventInfo.GetActor() != GetTarget()", "spell->IsTriggered()",
                     "spell->m_CastItem != nullptr", "IsAutoRepeatRangedSpell()", "IsPassive()",
                     "DamagesOrHeals(spellInfo)"):
            self.assertIn(rule, check)
        self.assertIn("NoteSchool(_memory, school) != LightsStep::Different", choker)
        self.assertIn("GetSchoolMask()", choker)
        for handler in ("void HandleApply", "void HandleRemove"):
            self.assertIn("_memory = LightsMemory{};", choker.split(handler, 1)[1].split("}\n", 1)[0])

        disk = self._script("spell_uldaman_item_fragment_of_the_disks")
        check = disk.split("bool CheckProc", 1)[1].split("void HandleProc", 1)[0]
        for rule in ("GetEffectiveHeal()", "SPELL_ATTR3_IGNORE_CASTER_MODIFIERS", "SPELL_DISK_REPLAY_HEAL",
                     "spell->m_CastItem", "eventInfo.GetActor() != GetTarget()"):
            self.assertIn(rule, check)
        proc = disk.split("void HandleProc", 1)[1].split("void HandleRemove", 1)[0]
        self.assertIn("UndoTakenMods(heal->GetEffectiveHeal(), probe)", proc)    # overhealing never recorded
        remove = disk.split("void HandleRemove", 1)[1]
        self.assertIn("AURA_REMOVE_BY_EXPIRE", remove)                           # death or a dispel replays nothing
        self.assertIn('GetScript<spell_uldaman_item_disk_replay>("spell_uldaman_item_disk_replay")', remove)
        self.assertIn("holder->SetRecord(record, share)", remove)
        replay = self._script("spell_uldaman_item_disk_replay")
        self.assertIn("ReplayTickAmount(entry.amount, ticks, aurEff->GetTickNumber())", replay)
        self.assertIn("CastCustomSpell(target, SPELL_DISK_REPLAY_HEAL, &amount", replay)
        # a script casts its tier's copy of a scaled spell and the shared base of the replay
        for base in ("SPELL_WAKING_STONE_TRAMPLE", "SPELL_CHOKER_TWO_LIGHTS"):
            self.assertIn(f"TierSpell(GetSpellInfo(), {base})", self.source)
        self.assertNotRegex(self.source, r"TierSpell\([^)]*\bSPELL_DISK_REPLAY(_HEAL)?\)")

    def test_scaled_tiers(self):
        """The copy families (the trample, Two Lights' rating and the share grow with the tier; the march, the width,
        the knockback and the replay stay)."""
        from lib import item_spell_copies  # noqa: PLC0415

        spells = [{**entry, "_source_class": item_spell_copies.SOURCE_CLASS} for entry in self.reg.spells]
        index = item_spell_copies.SpellIndex.build({"spells": spells, "linked_spells": self.reg.linked_spells})
        self.assertEqual(sorted(index.family(STONE)), [STONE, TRAMPLE])
        self.assertEqual(sorted(index.family(CHOKER)), [CHOKER, LIGHTS])
        self.assertEqual(index.family(RECORDING), [RECORDING])
        # The generator (item_spell_copies.plan, `tier_rating_ratio`) passes every tier two ratios: the hard mode
        # ladder's primary ratios 1.0545 / 1.1091 / 1.2545 (dbc-tools.md, IV10) for potency and plain stat auras, and
        # the secondary-curve ratios 1.3667 / 1.8444 / 2.5111 (item_budget_curve.secondary_budget 90 / 123 / 166 /
        # 226) for a MOD_RATING aura whose ratings all ride the secondary curve: Two Lights' haste (CR 17-19). The
        # recording's share is a DUMMY, so it stays on the primary ratio.
        tiers = ((1.0545, 1.3667, 14, 53), (1.1091, 1.8444, 18, 55), (1.2545, 2.5111, 25, 63))
        self._assert_generator_ratios(item_spell_copies, [(ratio, rating_ratio) for ratio, rating_ratio, *_ in tiers])
        remap = {STONE: 1, TRAMPLE: 2, CHOKER: 3, LIGHTS: 4, RECORDING: 5}
        for ratio, rating_ratio, rating, share in tiers:
            copies = {}
            for root in (STONE, CHOKER, RECORDING):
                copies.update(item_spell_copies.build_copies(index, index.family(root), remap, ratio, "test",
                                                             rating_ratio))
            self.assertAlmostEqual(copies[TRAMPLE].effects[0].ap_potency, 400.0 * ratio)
            knock = copies[TRAMPLE].effects[1]
            self.assertEqual((knock.misc_value, knock.base_points + 1), (75, 57))          # the knockback stays
            self.assertEqual([e.base_points + 1 for e in copies[STONE].effects if e], [20, 3])  # march and width stay
            self.assertEqual([e.base_points + 1 for e in copies[LIGHTS].effects if e], [rating], ratio)
            self.assertEqual([e.base_points + 1 for e in copies[RECORDING].effects if e], [share], ratio)

    def _assert_generator_ratios(self, copies_lib, expected):
        """The ratios above are the generator's own on the replayed itemization tables (skipped on a bare checkout)."""
        from lib import item_variants  # noqa: PLC0415

        try:
            tables, _ = item_variants.load_itemization_tables()
        except Exception:  # noqa: BLE001 - the replay needs the repo's SQL; the literals above still pin the copies
            return
        neck, epic = 2, 4
        first = item_variants.ResolvedTier("k", "a", "a", 1, False, 71, epic, 60, False, None, {}, {})
        got = []
        for ilvl in (81, 91, 101):
            tier = item_variants.ResolvedTier("k", "b", "b", 2, False, ilvl, epic, 60, False, None, {}, {})
            got.append((copies_lib.tier_ratio(tables, first, tier, neck),
                        copies_lib.tier_rating_ratio(tables, first, tier, neck)))
        self.assertEqual(got, expected)

    def test_proc_rows(self):
        self.assertEqual(set(self.procs), {CHOKER, RECORDING})
        choker = self.procs[CHOKER]
        self.assertEqual((choker["ProcFlags"], choker["SpellTypeMask"], choker["SpellPhaseMask"], choker["HitMask"],
                          choker["Chance"], choker["Cooldown"], choker["AttributesMask"]),
                         (0x15510, 0x7, 0x1, 0, 100.0, 0, 0))
        disk = self.procs[RECORDING]
        self.assertEqual((disk["ProcFlags"], disk["SpellTypeMask"], disk["SpellPhaseMask"], disk["HitMask"],
                          disk["Chance"], disk["Cooldown"], disk["AttributesMask"]),
                         (0x44400, 0x2, 0x2, 0x3, 100.0, 0, 0x2))
        for row in self.procs.values():
            self.assertEqual((row["SpellFamilyName"], row["Charges"]), (0, 0))
        # the header's flags are the rows'
        for name, row in (("kOwnCastFlags", choker), ("kHealFlags", disk)):
            flags = re.search(rf"{name} = ([^;]+);", self.header).group(1)
            self.assertEqual(sum(int(f.strip().rstrip("u"), 16) for f in flags.split("|")), row["ProcFlags"], name)
        # the Spell.dbc columns say the same
        self.assertEqual((self._raw(CHOKER)["ProcTypeMask"], self._raw(CHOKER)["ProcChance"]), (0x15510, 100))
        self.assertEqual((self._raw(RECORDING)["ProcTypeMask"], self._raw(RECORDING)["ProcChance"]), (0x44400, 100))


if __name__ == "__main__":
    unittest.main()
