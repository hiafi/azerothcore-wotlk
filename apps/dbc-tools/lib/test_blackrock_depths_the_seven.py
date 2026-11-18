"""
Blackrock Depths build WP-D21, The Seven: source/npcs/blackrock_depths/the_seven.py (the spells 211520-211557 and the
seven bindings), data/sql/updates/pending_db_world/rev_the_seven_blackrock_depths.sql (the SmartAI drop and their
texts), and the C++ side they must agree with (modules/mod-dungeon-bosses src/BlackrockDepths/TheSevenLogic.h,
TheSevenFight.h and boss_the_seven_rework.cpp).

Checks:
  - the 38 spells sit in the D21 slice and the C++ names the same ids; the shade aura is -90% damage taken; Gather Doom
    is a 3 s (heroic 2 s) kickable Shadow cast with no effect; the energy stacks to 3; the mood bars are 3 s Physical
    casts nobody can kick (rule 5); Vile Communion is a kickable 6 s self channel (Holy); the registry hits are resolve
    copies; the script hits carry their percents in the effect (normal) and EffectMiscValueB (heroic) on the kit's
    refflat scripts; the TS10 copies are 2 s; no stock id is declared, nothing on DD's double-use list is cast;
  - the bindings (held back until BIND_WAVE_2 flips): one script on all seven, SmartAI off, the stun set, INSTANCE_BIND,
    DamageModifier 3.5, and a HealthModifier that gives every ghost the whole 320k pool on its class base; WP-H's
    heroic override is the 450k pool on every ghost;
  - the SQL: the five SmartAI blocks dropped, 14 new yells (a rise and a mood line each), Doom'rel's stock group 0 kept,
    no spawn and no SmartAI insert (rule 14);
  - the numbers the dbc-tools file pins are the header's, Seething Cold is G2's `loner` row (Cluster(2), tag 22), and
    the script registers what the spec names (the descriptor, the pool host, the gate).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_the_seven.py
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import test_blackrock_depths_event_items as event_items_test  # noqa: E402
from lib import test_id_blocks as id_blocks  # noqa: E402
from source.npcs.blackrock_depths import _common as common  # noqa: E402
from source.npcs.blackrock_depths import _visuals as visuals  # noqa: E402

MDB = REPO_ROOT / "modules" / "mod-dungeon-bosses"
LOGIC = MDB / "src" / "BlackrockDepths" / "TheSevenLogic.h"
FIGHT = MDB / "src" / "BlackrockDepths" / "TheSevenFight.h"
SCRIPT = MDB / "src" / "BlackrockDepths" / "boss_the_seven_rework.cpp"
HEADER = MDB / "src" / "BlackrockDepths" / "BlackrockDepthsRework.h"
SQL = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_the_seven_blackrock_depths.sql"
DECLARATION = TOOL_ROOT / "source" / "npcs" / "blackrock_depths" / "the_seven.py"
HEROIC = TOOL_ROOT / "source" / "world" / "dungeons" / "blackrock_depths.py"
# The BM drill (G2): present in the orchestrator's layout, absent elsewhere (the cross-check then skips).
BM_DRILL = Path("/home/plex/wow_server/worktrees/boss-mechanics-brd/src/MechanicDrill.h")

SLICE = range(211520, 211580)
DECLARED = range(211520, 211558)
NAMES = (
    "SPELL_TS_INCORPOREAL", "SPELL_TS_FADE_LOOK", "SPELL_TS_GATHER_DOOM", "SPELL_TS_GATHER_DOOM_HEROIC",
    "SPELL_TS_GATHERED_DOOM", "SPELL_TS_FURIOUS_CHARGE_CAST", "SPELL_TS_FURIOUS_CHARGE_LOOK",
    "SPELL_TS_FURIOUS_CHARGE", "SPELL_TS_FURIOUS_STOMP", "SPELL_TS_SEETHING_COLD_CAST", "SPELL_TS_SEETHING_COLD",
    "SPELL_TS_DOPEY_HAZE_CAST", "SPELL_TS_DOPEY_HAZE", "SPELL_TS_STUMBLE", "SPELL_TS_GLOOM_CAST", "SPELL_TS_GLOOM",
    "SPELL_TS_RECKLESSNESS", "SPELL_TS_VILE_COMMUNION_CAST", "SPELL_TS_VILE_COMMUNION", "SPELL_TS_VILE_COMMUNION_LOOK",
    "SPELL_TS_HATRED_CAST", "SPELL_TS_HATRED_MARK", "SPELL_TS_HATRED", "SPELL_TS_DOOM_CAST", "SPELL_TS_DOOM",
    "SPELL_TS_DOOM_RING", "SPELL_TS_DOOM_BLAST", "SPELL_TS_DOOM_BLAST_SELF", "SPELL_TS_FROSTBOLT",
    "SPELL_TS_CONE_OF_COLD", "SPELL_TS_FROST_NOVA", "SPELL_TS_BACKSTAB", "SPELL_TS_RUPTURE", "SPELL_TS_GOUGE",
    "SPELL_TS_MIND_BLAST", "SPELL_TS_SHADOW_BOLT", "SPELL_TS_SHADOW_BOLT_VOLLEY", "SPELL_TS_IMMOLATE",
)
ID = {name: 211520 + i for i, name in enumerate(NAMES)}
MOOD_BARS = ("SPELL_TS_FURIOUS_CHARGE_CAST", "SPELL_TS_SEETHING_COLD_CAST", "SPELL_TS_DOPEY_HAZE_CAST",
             "SPELL_TS_GLOOM_CAST", "SPELL_TS_VILE_COMMUNION_CAST", "SPELL_TS_HATRED_CAST", "SPELL_TS_DOOM_CAST")
RESOLVE_COPIES = {"SPELL_TS_FURIOUS_CHARGE": 1, "SPELL_TS_HATRED": 32, "SPELL_TS_DOOM_BLAST": 32}
# hundredths (normal, heroic) of the script hits on spell_dungeon_refflat_damage
REFFLAT = {
    "SPELL_TS_SEETHING_COLD": (600, 1000), "SPELL_TS_STUMBLE": (1500, 2500), "SPELL_TS_DOOM_BLAST_SELF": (2000, 3000),
    "SPELL_TS_FROSTBOLT": (600, 800), "SPELL_TS_CONE_OF_COLD": (800, 1000), "SPELL_TS_FROST_NOVA": (600, 800),
    "SPELL_TS_BACKSTAB": (1200, 1500), "SPELL_TS_GOUGE": (300, 400), "SPELL_TS_MIND_BLAST": (800, 1000),
    "SPELL_TS_SHADOW_BOLT": (1200, 1500), "SPELL_TS_SHADOW_BOLT_VOLLEY": (800, 1000),
}
EFFECT_SCHOOL_DAMAGE, EFFECT_DUMMY, EFFECT_APPLY_AURA = 2, 3, 6
AURA_PERIODIC_DAMAGE, AURA_DUMMY, AURA_MOD_STUN, AURA_MOD_ROOT = 3, 4, 12, 26
AURA_MOD_DECREASE_SPEED, AURA_MOD_DAMAGE_PERCENT_DONE = 33, 79
AURA_MOD_DAMAGE_PERCENT_TAKEN, AURA_MOD_HEALING_PCT = 87, 118
SCHOOL_PHYSICAL, SCHOOL_HOLY, SCHOOL_FIRE, SCHOOL_FROST, SCHOOL_SHADOW = 1, 2, 4, 16, 32
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
SEVEN = (9035, 9038, 9040, 9037, 9036, 9034, 9039)
# entry: (level, unit_class, class base): creature_template and creature_classlevelstats basehp0, live 2026-11-17
GHOSTS = {9035: (55, 1, 2614), 9038: (56, 2, 2159), 9040: (56, 1, 2699), 9037: (56, 1, 2699), 9036: (56, 2, 2159),
          9034: (55, 2, 2091), 9039: (56, 2, 2159)}
SMART_AI = (9034, 9035, 9036, 9038, 9040)
# the stock ids the kits retire or copy (never declared, never cast): DD's double-use ones among them
RETIRED = (15044, 15585, 15586, 12493, 15092, 15093, 15094, 12540, 12674, 15232, 15582, 12675, 15244, 15583, 15587,
           15245, 12742)
DOUBLE_USE = (15232, 15305, 15472, 15530, 15582, 15616)


def _shown(effect: dict) -> int:
    return effect["base_points"] + effect["die_sides"]


class TheSevenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        npcs = event_items_test._load_npcs()
        cls.spells = {int(e["id"]): e for e in npcs.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in npcs.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {int(e["entry"]): e for e in npcs.creature_template_edits}
        cls.creatures = {int(e["entry"]) for e in npcs.creature_templates}
        cls.all_spell_ids = {int(e["id"]) for e in npcs.spells}
        cls.sql = SQL.read_text(encoding="utf-8")
        cls.logic = LOGIC.read_text(encoding="utf-8")
        cls.fight = FIGHT.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")
        cls.heroic = HEROIC.read_text(encoding="utf-8")
        cls.declaration = DECLARATION.read_text(encoding="utf-8")

    def _const(self, name: str) -> str:
        match = re.search(rf"{name}\s*(?:=|\{{)\s*([^;}}]+?)\s*(?:;|\}};)", self.logic)
        self.assertIsNotNone(match, name)
        return match.group(1).replace(" ", "")

    def _spell(self, name: str) -> dict:
        return self.spells[ID[name]]

    # --- the spells ---------------------------------------------------------------------------------------------------

    def test_the_spells_sit_in_the_d21_slice(self):
        self.assertEqual(sorted(self.spells), list(DECLARED))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"spell": list(self.spells)}), [])
        self.assertIn("kSpellsTheSeven{ 211520, 211579 }", re.sub(r"\s+", " ", self.header))

    def test_the_cpp_names_the_same_ids(self):
        for offset, name in enumerate(NAMES):
            self.assertRegex(self.logic, rf"{name}\s*=\s*kSpellSlice\.first \+ {offset},", name)
        self.assertRegex(self.logic, r"kLastSpell = SPELL_TS_IMMOLATE;")

    def test_the_shade(self):
        spell = self._spell("SPELL_TS_INCORPOREAL")
        effect = spell["effect1"]
        self.assertEqual((effect["type"], effect["apply_aura"]), (EFFECT_APPLY_AURA, AURA_MOD_DAMAGE_PERCENT_TAKEN))
        self.assertEqual(_shown(effect), -90)
        self.assertEqual(effect["misc_value"], 127)             # every school
        self.assertEqual(spell["duration_ms"], -1)
        self.assertEqual(spell["dispel"], 0)
        self.assertEqual(spell["raw_overrides"]["SpellVisualID_1"], visuals.TS_SHADE)
        self.assertEqual(self._const("kShadeDamageTakenPct"), "-90")
        self.assertEqual(self._spell("SPELL_TS_FADE_LOOK")["raw_overrides"]["SpellVisualID_1"], visuals.TS_SHADE_FADE)

    def test_gather_doom_is_kickable_and_has_no_effect(self):
        for name, cast in (("SPELL_TS_GATHER_DOOM", 3000), ("SPELL_TS_GATHER_DOOM_HEROIC", 2000)):
            spell = self._spell(name)
            self.assertEqual(spell["cast_time_ms"], cast, name)
            self.assertEqual(spell["school"], SCHOOL_SHADOW, name)
            self.assertEqual(spell["effect1"]["type"], EFFECT_DUMMY, name)
            raw = spell["raw_overrides"]
            self.assertEqual((raw["InterruptFlags"], raw["PreventionType"]), (15, 1), name)
            self.assertEqual(raw["SpellVisualID_1"], visuals.TS_GATHER_DOOM_CAST, name)
            self.assertFalse([s for s in self.scripts if s[0] == ID[name]], name)
        self.assertEqual(self._const("kGatherCastMs"), "3000,2000")
        self.assertEqual(self._const("kGatherEveryMs"), "8000,6000")
        self.assertEqual(self._const("kGatherFirstMs"), "3000")
        energy = self._spell("SPELL_TS_GATHERED_DOOM")
        self.assertEqual(energy["raw_overrides"]["CumulativeAura"], 3)
        self.assertEqual(self._const("kEnergyFull"), "3")
        self.assertEqual(energy["raw_overrides"]["SpellVisualID_1"], visuals.TS_GATHER_DOOM_LANDING)
        # the shades' look and Gather Doom's are not the same (VR: one purple state per role)
        self.assertNotEqual(visuals.TS_SHADE, visuals.TS_GATHER_DOOM_CAST)

    def test_the_mood_bars_are_physical_and_cannot_be_kicked(self):
        for name in MOOD_BARS:
            spell = self._spell(name)
            self.assertEqual(spell["cast_time_ms"], 3000, name)
            self.assertEqual(spell["school"], SCHOOL_PHYSICAL, name)     # rule 5: no lockout stops it
            raw = spell["raw_overrides"]
            self.assertEqual((raw["InterruptFlags"], raw["PreventionType"]), (0, 0), name)
            self.assertEqual(spell["effect1"]["type"], EFFECT_DUMMY, name)
        self.assertEqual(self._const("kMoodCastMs"), "3000")
        # the interruptible casts use other schools than the bars
        kickable = [s for s in self.spells.values() if s["raw_overrides"].get("InterruptFlags") == 15
                    or s["raw_overrides"].get("ChannelInterruptFlags") == 8]
        self.assertTrue(kickable)
        self.assertFalse([s["id"] for s in kickable if s["school"] == SCHOOL_PHYSICAL])

    def test_vile_communion_is_a_kickable_holy_channel(self):
        spell = self._spell("SPELL_TS_VILE_COMMUNION")
        raw = spell["raw_overrides"]
        self.assertEqual(spell["school"], SCHOOL_HOLY)
        self.assertEqual(spell["duration_ms"], 6000)
        self.assertTrue(raw["AttributesEx"] & 0x40)             # a self channel
        self.assertEqual((raw["ChannelInterruptFlags"], raw["PreventionType"]), (0x08, 1))
        self.assertEqual(raw["SpellVisualID_1"], visuals.TS_VILE_COMMUNION)
        self.assertEqual(self._const("kVileHealPct"), "5.f,8.f")
        self.assertEqual(self._const("kVileChannelMs"), "6000")
        self.assertEqual(self._spell("SPELL_TS_VILE_COMMUNION_LOOK")["raw_overrides"]["SpellVisualID_1"],
                         visuals.TS_VILE_COMMUNION)
        # first on the interrupt list
        self.assertRegex(self.script, r"d\.interrupts\.emplace_back\(NPC_VILEREL, SPELL_TS_VILE_COMMUNION, "
                                      r"kVileCommunionKick\);")

    def test_the_registry_hits_are_resolve_copies(self):
        for name, school in RESOLVE_COPIES.items():
            spell = self._spell(name)
            self.assertEqual(spell["school"], school, name)
            self.assertEqual(spell["effect1"]["type"], EFFECT_SCHOOL_DAMAGE, name)
            self.assertIn((ID[name], "spell_boss_mechanics_resolve"), self.scripts, name)
            self.assertTrue(spell["raw_overrides"]["AttributesEx3"] & ATTR3_IGNORE_CASTER_MODIFIERS, name)

    def test_the_script_hits_carry_their_percents(self):
        for name, (normal, heroic) in REFFLAT.items():
            spell = self._spell(name)
            raw = spell["raw_overrides"]
            hit = spell["effect1"]
            self.assertEqual(hit["type"], EFFECT_SCHOOL_DAMAGE, name)
            self.assertEqual(_shown(hit), normal, name)
            self.assertEqual(raw["EffectMiscValueB_1"], heroic, name)
            self.assertIn((ID[name], "spell_dungeon_refflat_damage"), self.scripts, name)
            self.assertTrue(raw["AttributesEx3"] & ATTR3_IGNORE_CASTER_MODIFIERS, name)
        rupture = self._spell("SPELL_TS_RUPTURE")
        self.assertEqual((rupture["effect1"]["apply_aura"], rupture["effect1"]["amplitude"]), (AURA_PERIODIC_DAMAGE,
                                                                                              2000))
        self.assertEqual((_shown(rupture["effect1"]), rupture["raw_overrides"]["EffectMiscValueB_1"]), (200, 300))
        self.assertEqual(rupture["duration_ms"], 10_000)
        self.assertIn((ID["SPELL_TS_RUPTURE"], "spell_dungeon_refflat_periodic"), self.scripts)
        immolate = self._spell("SPELL_TS_IMMOLATE")
        self.assertEqual((immolate["effect1"]["apply_aura"], immolate["effect1"]["amplitude"]),
                         (AURA_PERIODIC_DAMAGE, 3000))
        self.assertEqual((_shown(immolate["effect1"]), immolate["raw_overrides"]["EffectMiscValueB_1"]), (200, 300))
        self.assertEqual((_shown(immolate["effect2"]), immolate["raw_overrides"]["EffectMiscValueB_2"]), (800, 1000))
        self.assertEqual(immolate["cast_time_ms"], 2000)
        self.assertEqual(immolate["school"], SCHOOL_FIRE)
        for script in ("spell_dungeon_refflat_damage", "spell_dungeon_refflat_periodic"):
            self.assertIn((ID["SPELL_TS_IMMOLATE"], script), self.scripts)
        # the header holds the same numbers
        for const, value in (("kColdPct", "6.f,10.f"), ("kStumblePct", "15.f,25.f"), ("kDoomSelfPct", "20.f,30.f"),
                             ("kFrostboltPct", "6.f,8.f"), ("kConeOfColdPct", "8.f,10.f"),
                             ("kFrostNovaPct", "6.f,8.f"), ("kBackstabPct", "12.f,15.f"), ("kRupturePct", "2.f,3.f"),
                             ("kGougePct", "3.f,4.f"), ("kMindBlastPct", "8.f,10.f"),
                             ("kShadowBoltPct", "12.f,15.f"), ("kVolleyPct", "8.f,10.f"),
                             ("kImmolatePct", "8.f,10.f"), ("kImmolateTickPct", "2.f,3.f")):
            self.assertEqual(self._const(const), value, const)

    def test_the_ts10_copies_are_two_seconds(self):
        nova = self._spell("SPELL_TS_FROST_NOVA")
        self.assertEqual(nova["duration_ms"], 2000)
        self.assertEqual(nova["effect2"]["apply_aura"], AURA_MOD_ROOT)
        self.assertEqual(nova["effect2"]["radius_yards"], 10.0)
        self.assertEqual(nova["dispel"], 1)                     # Magic: the dispel list's reward
        gouge = self._spell("SPELL_TS_GOUGE")
        self.assertEqual(gouge["duration_ms"], 2000)
        self.assertEqual(gouge["effect2"]["apply_aura"], AURA_MOD_STUN)
        self.assertEqual(gouge["raw_overrides"]["AuraInterruptFlags"], 0x2)     # breaks on damage (stock)
        self.assertEqual(self._const("kFrostNovaRootMs"), "2000")
        self.assertEqual(self._const("kGougeMs"), "2000")
        self.assertRegex(self.script, r"d\.dispels\.emplace_back\(SPELL_TS_FROST_NOVA, kDispelFrostNova\);")

    def test_the_mood_auras(self):
        gloom = self._spell("SPELL_TS_GLOOM")
        self.assertEqual(gloom["effect1"]["apply_aura"], AURA_MOD_HEALING_PCT)
        self.assertEqual(_shown(gloom["effect1"]), -50)
        self.assertEqual(gloom["duration_ms"], 12_000)
        self.assertEqual(gloom["raw_overrides"]["SpellVisualID_1"], visuals.TS_GLOOM_HEALING_MARK)
        reckless = self._spell("SPELL_TS_RECKLESSNESS")
        self.assertEqual(reckless["effect1"]["apply_aura"], AURA_MOD_DAMAGE_PERCENT_DONE)
        self.assertEqual(_shown(reckless["effect1"]), 50)
        self.assertEqual(reckless["raw_overrides"]["SpellVisualID_1"], visuals.TS_GLOOM_RELS_RECKLESSNESS)
        cold = self._spell("SPELL_TS_SEETHING_COLD")
        self.assertEqual(cold["effect2"]["apply_aura"], AURA_MOD_DECREASE_SPEED)
        self.assertEqual(_shown(cold["effect2"]), -30)
        self.assertEqual(cold["duration_ms"], 1500)
        self.assertEqual(cold["raw_overrides"]["SpellVisualID_1"], visuals.TS_SEETHING_COLD)
        for name, ms, visual in (("SPELL_TS_DOPEY_HAZE", 6000, visuals.TS_DOPEY_HAZE),
                                 ("SPELL_TS_HATRED_MARK", 8000, visuals.TS_HATRED),
                                 ("SPELL_TS_DOOM", 6000, visuals.TS_DOOM_MARK),
                                 ("SPELL_TS_DOOM_RING", 6000, visuals.TS_DOOM_MARK_RING)):
            spell = self._spell(name)
            self.assertEqual(spell["duration_ms"], ms, name)
            self.assertEqual(spell["raw_overrides"]["SpellVisualID_1"], visual, name)
            self.assertEqual(spell["dispel"], 0, name)
        self.assertEqual(self._spell("SPELL_TS_FURIOUS_CHARGE_LOOK")["raw_overrides"]["SpellVisualID_1"],
                         visuals.TS_FURIOUS_CHARGE)
        # VR's WRONG look for Hatred (Shadow Mark's dust whirl, SV 223) is never wired
        for spell in self.spells.values():
            self.assertNotEqual(spell["raw_overrides"].get("SpellVisualID_1"), 223, spell["id"])

    def test_no_stock_id_is_declared_or_cast(self):
        for spell_id in RETIRED:
            self.assertNotIn(spell_id, self.spells)
        kit = self.logic[self.logic.index("kKit{"):self.logic.index("} };", self.logic.index("kKit{"))]
        for spell_id in DOUBLE_USE:
            self.assertNotIn(str(spell_id), kit)
            self.assertNotIn(str(spell_id), self.script)

    def test_the_stock_looks_follow_visuals(self):
        # a copy keeps its stock look through a _visuals.py name (rule 4); until V-2 names it, the declared fallback
        for name, fallback in (("SPELL_TS_FROST_NOVA", ("TS_FROST_NOVA", visuals.VL_FROST_NOVA)),
                               ("SPELL_TS_FROSTBOLT", ("TS_FROSTBOLT", visuals.ST_FROSTBOLT)),
                               ("SPELL_TS_SHADOW_BOLT", ("TS_SHADOW_BOLT", visuals.TS_GATHER_DOOM_CAST)),
                               ("SPELL_TS_FURIOUS_STOMP", ("TS_FURIOUS_STOMP", visuals.GZ_EARTHSHAKER_STOMP))):
            self.assertEqual(self._spell(name)["raw_overrides"].get("SpellVisualID_1"),
                             getattr(visuals, fallback[0], fallback[1]), name)
        for name, look in (("SPELL_TS_CONE_OF_COLD", "TS_CONE_OF_COLD"), ("SPELL_TS_BACKSTAB", "TS_BACKSTAB"),
                           ("SPELL_TS_RUPTURE", "TS_RUPTURE"), ("SPELL_TS_GOUGE", "TS_GOUGE"),
                           ("SPELL_TS_MIND_BLAST", "TS_MIND_BLAST"),
                           ("SPELL_TS_SHADOW_BOLT_VOLLEY", "TS_SHADOW_BOLT_VOLLEY"),
                           ("SPELL_TS_IMMOLATE", "TS_IMMOLATE"), ("SPELL_TS_DOOM_BLAST_SELF", "TS_DOOM_BLAST")):
            self.assertEqual(self._spell(name)["raw_overrides"].get("SpellVisualID_1", 0), getattr(visuals, look, 0),
                             name)
        # no raw visual id in the declaration (rule 4): every SpellVisualID_1 is a name or _look(...)
        self.assertFalse(re.findall(r"SpellVisualID_1=\d", self.declaration))

    # --- the creatures ------------------------------------------------------------------------------------------------

    def test_the_columns(self):
        self.assertIn("ROTATION = (9035, 9038, 9040, 9037, 9036, 9034, 9039)", self.declaration)
        self.assertIn("DAMAGE_MODIFIER = 3.5", self.declaration)
        self.assertIn("POOL_HEALTH = (320_000, 450_000)", self.declaration)
        self.assertRegex(self.declaration, r"GHOST_COLUMNS = \{entry: boss_columns\('boss_the_seven_rework', "
                                           r"pool_health_modifier\(base\),")
        self.assertIn("damage_modifier=DAMAGE_MODIFIER, instance_bind=entry == CREDIT_GHOST)", self.declaration)
        self.assertIn("CREDIT_GHOST = 9035", self.declaration)
        self.assertIn("return round(POOL_HEALTH[0] / base, 3)", self.declaration)
        for entry, (level, cls, base) in GHOSTS.items():
            self.assertRegex(self.declaration, rf"{entry}: \(\"[^\"]+\", {level}, {cls}, {base}\),", entry)
            c = common.boss_columns("boss_the_seven_rework", round(320_000 / base, 3), damage_modifier=3.5,
                                    instance_bind=entry == 9035)
            self.assertEqual(c["ScriptName"], "boss_the_seven_rework", entry)
            self.assertEqual(c["AIName"], "", entry)
            self.assertEqual(c["CreatureImmunitiesId"], 1972, entry)     # s7 #10 (the spec says -251: question)
            self.assertEqual(c["flags_extra"], 1 if entry == 9035 else 0, entry)  # bind on the credit ghost only
            self.assertEqual(entry in common.NO_INSTANCE_BIND, entry != 9035, entry)
            self.assertEqual(c["DamageModifier"], 3.5, entry)
            # the whole 320k pool on every frame
            self.assertAlmostEqual(c["HealthModifier"] * base, 320_000, delta=2)
        self.assertEqual(self._const("kPoolHealth"), "320000,450000")
        self.assertRegex(self.declaration, r"if BIND_WAVE_2:\n    for _entry in ROTATION:\n"
                                           r"        creature_template_columns\(_entry, \*\*GHOST_COLUMNS\[_entry\]\)")

    def test_the_heroic_pool_is_whp_override(self):
        compact = re.sub(r"\s+", " ", self.heroic)
        for entry in SEVEN:
            self.assertIn(f"{entry}: _boss(450_000)", compact, entry)

    @unittest.skipUnless(common.BIND_WAVE_2, "the bindings register only while BIND_WAVE_2 is on")
    def test_the_bindings_register_with_the_gate_on(self):
        for entry in SEVEN:
            self.assertEqual(self.edits[entry]["ScriptName"], "boss_the_seven_rework", entry)
            self.assertEqual(self.edits[entry]["AIName"], "", entry)

    @unittest.skipIf(common.BIND_WAVE_2, "with the gate on the bindings are registered (the test above)")
    def test_nothing_is_bound_with_the_gate_off(self):
        for entry in SEVEN:
            self.assertNotIn(entry, self.edits, entry)

    def test_no_boss_kit_creature_is_declared(self):
        self.assertFalse([e for e in self.creatures if e in SEVEN])
        self.assertFalse([e for e in self.creatures if 300780 <= e <= 300879 and e not in (300796, 300845)
                          and "seven" in str(e)])

    def test_the_script_registers_one_ai_behind_the_gate(self):
        self.assertRegex(self.script, r"if \(kWave2Bound\)\s+RegisterDungeonReworkCreatureAI\(boss_the_seven_rework,")
        self.assertRegex(self.script, r'BrdTest::RegisterBoss\("seven",')
        self.assertRegex(self.script, r"struct boss_the_seven_rework : public ScriptedAI")
        # the pool lives in the instance through TheSevenFight.h's PoolHost
        self.assertIn("class PoolHost", self.fight)
        self.assertIn("virtual DungeonKit::SharedHealthPool& TheSevenPool() = 0;", self.fight)
        self.assertIn("PoolOf(me->GetInstanceScript())", self.script)
        # kill order skips shades; shades are never attacked
        self.assertIn("Condition::LacksAura(SPELL_TS_INCORPOREAL)", self.script)
        self.assertIn("HoldEntry::Attacks(0, SPELL_TS_INCORPOREAL)", self.script)
        # the stock gossip menus
        for menu in (1950, 1952, 1953):
            self.assertIn(f"= {menu};", self.script)

    # --- the SQL ------------------------------------------------------------------------------------------------------

    def test_the_smartai_drop(self):
        self.assertIn("DELETE FROM `smart_scripts` WHERE `source_type` = 0 AND `entryorguid` IN "
                      "(9034, 9035, 9036, 9038, 9040);", self.sql)
        self.assertNotIn("INSERT INTO `smart_scripts`", self.sql)
        self.assertNotIn("INSERT INTO `creature` ", self.sql)

    def test_the_texts(self):
        rows = re.findall(r"^\((\d+), (\d+), (\d+), '((?:[^']|'')*)', (\d+), 0, 100, 0, 0, 0, 0, (\d+),", self.sql,
                          re.M)
        got = {(int(e), int(g)): (t.replace("''", "'"), int(ty), int(r)) for e, g, _i, t, ty, r in rows}
        self.assertEqual(len(got), 14)
        for entry in SEVEN:
            rise, mood = (1, 2) if entry == 9039 else (0, 1)
            self.assertIn((entry, rise), got, entry)
            self.assertIn((entry, mood), got, entry)
            for key in ((entry, rise), (entry, mood)):
                self.assertEqual(got[key][1], 14, key)          # yells
        self.assertNotIn((9039, 0), got)                        # Doom'rel's stock challenge stays
        self.assertEqual(got[(9035, 0)][0], "Anger'rel stands sentry no longer!")
        self.assertEqual(got[(9039, 2)][0], "Your doom is sealed!")
        self.assertIn("DELETE FROM `creature_text` WHERE `CreatureID` = 9039 AND `GroupID` BETWEEN 1 AND 2;", self.sql)
        compact = re.sub(r"\s+", " ", self.header)
        self.assertIn("{ NPC_DOOMREL, 0, 2, 1 }", compact)
        for npc in ("NPC_ANGERREL", "NPC_SEETHREL", "NPC_DOPEREL", "NPC_GLOOMREL", "NPC_VILEREL", "NPC_HATEREL"):
            self.assertIn(f"{{ {npc}, 0, 1, 0 }}", compact)
        self.assertIn("Talk(RiseText(_ghost));", self.script)
        self.assertIn("Talk(MoodText(_ghost));", self.script)
        self.assertIn("Talk(SAY_DOOMREL_CHALLENGE);", self.script)

    # --- the numbers and the drill -----------------------------------------------------------------------------------

    def test_the_numbers_the_spec_names(self):
        for name, expected in (("kChargePct", "30.f,45.f"), ("kHatredPct", "5.f,8.f"), ("kDoomOthersPct", "30.f,45.f"),
                               ("kDoomMarks", "1,2")):
            self.assertEqual(self._const(name), expected, name)
        for name, expected in (("kStepMs", "20000"), ("kChargeSafeYd", "10.f"), ("kChargeWidthYd", "3.f"),
                               ("kChargeLifeMs", "9000"), ("kChargeEveryMs", "3000"), ("kHazeLifeMs", "6000"),
                               ("kGloomMs", "12000"), ("kGloomHealingPct", "-50"), ("kRecklessnessPct", "50"),
                               ("kHatredRadiusYd", "6.f"), ("kHatredLifeMs", "8000"), ("kDoomRadiusYd", "10.f"),
                               ("kDoomMarkMs", "6000")):
            self.assertEqual(self._const(name), expected, name)

    def test_seething_cold_is_g2s_loner_row(self):
        self.assertRegex(self.logic, r"TAG_TS_SEETHING_COLD\s*=\s*22,")
        self.assertEqual(self._const("kColdRadiusYd"), "6.f")
        self.assertEqual(self._const("kColdMinOthers"), "2")
        self.assertEqual(self._const("kColdLifeMs"), "10000")
        self.assertEqual(self._const("kColdTickMs"), "1000")
        self.assertIn("ref.Cluster(static_cast<uint8>(kColdMinOthers)).Persistent(Ms(kColdLifeMs), Ms(kColdTickMs))",
                      self.script)
        if not BM_DRILL.exists():
            self.skipTest("the BM drill source is not in this layout")
        drill = BM_DRILL.read_text(encoding="utf-8")
        self.assertRegex(drill, r"kBrd2TagLoner\s*=\s*22;")
        self.assertRegex(drill, r"kLonerYd\s*=\s*6\.f;")
        self.assertRegex(drill, r"kLonerOthers\s*=\s*2;")
        self.assertRegex(drill, r"kLonerCastMs\s*=\s*3000;")
        self.assertRegex(drill, r"kLonerMs\s*=\s*10000;")


if __name__ == "__main__":
    unittest.main()
