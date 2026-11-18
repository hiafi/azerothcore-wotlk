"""
Blackrock Depths build WP-D9, the Vault: source/npcs/blackrock_depths/vault.py against its C++
(modules/mod-dungeon-bosses src/BlackrockDepths/VaultLogic.h, boss_watchman_doomgrip_rework.cpp), its SQL rev and the
items the Safe holds.

Checks:
  - the spells sit in the slice (211090-211119) and VaultLogic.h names the same ids;
  - Doomgrip 9476 is bound (SmartAI off, immunity 1972, no INSTANCE_BIND, DamageModifier 7.5) at 110k health at 5
    players;
  - the Vault Sentinel 300793 is the boss-kit add (18,000 health, the construct's look, no loot, its script, the heroic
    entry WP-H minted, WP-H's 28,000 heroic health);
  - the hits are resolve copies of the right school; the sweep's bar is not interruptible and lasts the warning;
  - the field looks are the four minted rungs in order; the link, Sunder Armor and the draught carry the header's
    numbers; the draught is Magic and on the purge list;
  - the Safe's gear ids in VaultLogic.h are Doomgrip's four items in item_ids.lock (Normal and Heroic tiers), the bags
    and the Cinder are WP-IT's items;
  - the SQL rev writes texts 1-5, re-enters the four spawns with the heroic bit, binds the Safe's script.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_blackrock_depths_vault.py
"""

from __future__ import annotations

import math
import re
import sys
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib import test_id_blocks as id_blocks  # noqa: E402
from lib.dsl import registry  # noqa: E402

MODULE_DIR = REPO_ROOT / "modules" / "mod-dungeon-bosses" / "src" / "BlackrockDepths"
HEADER = MODULE_DIR / "VaultLogic.h"
SCRIPT = MODULE_DIR / "boss_watchman_doomgrip_rework.cpp"
SQL_REV = REPO_ROOT / "data" / "sql" / "updates" / "pending_db_world" / "rev_vault_blackrock_depths.sql"
PACKAGE = TOOL_ROOT / "source" / "npcs" / "blackrock_depths"
ITEM_IDS = TOOL_ROOT / "source" / "items" / "item_ids.lock"
EVENT_ITEMS = TOOL_ROOT / "source" / "items" / "blackrock_depths_event_items.py"
HEROIC = TOOL_ROOT / "source" / "world" / "dungeons" / "blackrock_depths.py"

SLICE = range(211090, 211120)
(LOCKDOWN, WAKES, FIELD_6, FIELD_7, FIELD_8, FIELD_9, FIELD_HIT, LINK_BEAM, SECURITY_LINK, SWEEP_CAST, SWEEP_HIT,
 SUNDER, DRAUGHT, STONED) = range(211090, 211104)
DOOMGRIP, SENTINEL = 9476, 300793
SENTINEL_HEROIC = 310404
PALADIN_54_BASE = 2026
WARRIOR_52_BASE = 2371
DOOMGRIP_HEALTH_AT_5 = 110_000
SENTINEL_HEALTH = 18_000

SCHOOL_NORMAL, SCHOOL_ARCANE = 1, 64
SCHOOL_DAMAGE, APPLY_AURA, HEAL_PCT = 2, 6, 136
AURA_DUMMY, AURA_MOD_DAMAGE_PERCENT_DONE, AURA_MOD_DAMAGE_PERCENT_TAKEN, AURA_MOD_RESISTANCE_PCT = 4, 79, 87, 101
DISPEL_MAGIC = 1
ATTR1_CHANNELED = 0x4
RESOLVE = "spell_boss_mechanics_resolve"
IMMUNITY_BOSS_STUN = 1972
INSTANCE_BIND = 0x1
TYPE_MECHANICAL = 9
DISPLAY_VAULT_SENTINEL = 8289
ATTR0_NO_IMMUNITIES = 0x20000000
SV_STOCK_STONED = 1845                  # Stoned 10255's SpellVisualID_1 (client Spell.dbc)


def _load():
    t = id_blocks
    return registry.load_class_package(
        PACKAGE, ids_cfg=t.IDS, trainer_index=t._AnyTrainer(), existing_group_ids=t._AnySet(),
        shapeshift_index={}, existing_creature_rows=t._AnyRows(),
        creature_columns=t.spell_tables.CREATURE_TEMPLATE_COLUMNS,
        creature_defaults=t.spell_tables.CREATURE_TEMPLATE_DEFAULTS,
        live_data=t.spell_tables.dsl_live_data(
            {}, t.spell_tables.load_live_item_template_rows,
            lambda: t.state.load_existing_rows(t.dbcfmt.SKILLLINEABILITY),
            lambda: t.state.load_stock_rows(t.dbcfmt.CHRCLASSES),
            lambda: t.state.load_stock_rows(t.dbcfmt.SKILLLINEABILITY),
        ),
    )


def _raw(spell: dict, column: str) -> int:
    return int((spell.get("raw_overrides") or {}).get(column, 0) or 0)


def _header_int(name: str) -> int:
    match = re.search(rf"\b{name}\s*=\s*(-?\d+)", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return int(match.group(1))


def _header_pair(name: str) -> tuple[float, float]:
    match = re.search(rf"\b{name}\{{\s*(-?[\d.]+)f?,\s*(-?[\d.]+)f?\s*\}}", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return float(match.group(1)), float(match.group(2))


def _header_ids(name: str) -> list[int]:
    match = re.search(rf"\b{name}\{{\s*\{{([\d,\s]+)\}}\s*\}}", HEADER.read_text(encoding="utf-8"))
    assert match, name
    return [int(v) for v in match.group(1).split(",")]


class VaultDeclarationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reg = _load()
        cls.spells = {int(e["id"]): e for e in reg.spells if int(e["id"]) in SLICE}
        cls.scripts = {(int(e["spell_id"]), e["ScriptName"]) for e in reg.spell_script_names
                       if int(e["spell_id"]) in SLICE}
        cls.edits = {}
        for e in reg.creature_template_edits:
            if int(e["entry"]) == DOOMGRIP:
                cls.edits.update(e)
        cls.creatures = {int(e["entry"]): e for e in reg.creature_templates if int(e["entry"]) == SENTINEL}
        cls.models = [e for e in reg.creature_template_models if int(e["CreatureID"]) == SENTINEL]
        cls.cpp = SCRIPT.read_text(encoding="utf-8")
        cls.header = HEADER.read_text(encoding="utf-8")

    def test_spells_sit_in_the_slice_and_match_the_header(self):
        mine = sorted(self.spells)
        self.assertEqual(mine, list(range(LOCKDOWN, STONED + 1)))
        self.assertEqual(id_blocks.out_of_reservation("blackrock_depths", {"spell": mine}), [])
        offsets = {int(v) for v in re.findall(r"SPELL_VA_\w+\s*=\s*kSpellSlice\.first \+ (\d+)", self.header)}
        self.assertEqual({LOCKDOWN + n for n in offsets}, set(mine))
        # The stock Sunder Armor and Drink Healing Potion are never re-declared: the changed one is a copy, the potion
        # retired.
        for stock in (11971, 15504, 10255):
            self.assertNotIn(stock, self.spells)

    def test_the_dormant_look_lands_through_immunity_1972(self):
        # R-2-A MA-2: stock Stoned 10255 carries EffectMechanic FREEZE (13), which set 1972 drops. The copy has no
        # mechanic and NO_IMMUNITIES, keeps 10255's visual, and the dormant state is the flag, not the aura.
        spell = self.spells[STONED]
        self.assertEqual(spell["name"], "Stoned")
        self.assertEqual(spell["mechanic"], 0)
        self.assertEqual(spell["effect1"]["type"], APPLY_AURA)
        self.assertEqual(spell["effect1"]["apply_aura"], AURA_DUMMY)
        self.assertEqual(int(spell["effect1"].get("mechanic", 0) or 0), 0)
        self.assertTrue(spell["attributes"] & ATTR0_NO_IMMUNITIES)
        self.assertEqual(_raw(spell, "SpellVisualID_1"), SV_STOCK_STONED)
        self.assertEqual(int(spell["duration_ms"]), -1)
        self.assertNotIn("SPELL_STOCK_STONED", self.cpp)
        self.assertIn("IsStone(", self.cpp)
        self.assertIn("SentinelReStoned(", self.cpp)
        instance = (MODULE_DIR / "instance_blackrock_depths_rework.cpp").read_text(encoding="utf-8")
        self.assertIn("kSpellVaultStoned", instance)
        rework = (MODULE_DIR / "BlackrockDepthsRework.h").read_text(encoding="utf-8")
        self.assertRegex(rework, rf"kSpellVaultStoned = {STONED};")

    def test_doomgrip_is_bound_with_the_build_specs_health(self):
        self.assertEqual(self.edits["ScriptName"], "boss_watchman_doomgrip_rework")
        self.assertEqual(self.edits["AIName"], "")
        self.assertEqual(self.edits["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
        self.assertEqual(self.edits["flags_extra"] & INSTANCE_BIND, 0)  # no Vault credit row: no INSTANCE_BIND
        self.assertEqual(self.edits["DamageModifier"], 7.5)
        self.assertLessEqual(abs(math.ceil(PALADIN_54_BASE * self.edits["HealthModifier"]) - DOOMGRIP_HEALTH_AT_5), 2)
        self.assertIn("RegisterDungeonReworkCreatureAI(boss_watchman_doomgrip_rework", self.cpp)

    def test_the_vault_sentinel(self):
        add = self.creatures[SENTINEL]
        self.assertEqual(add["name"], "Vault Sentinel")
        self.assertEqual(add["ScriptName"], "npc_brd_vault_sentinel")
        self.assertEqual(add["AIName"], "")
        self.assertEqual((add["minlevel"], add["maxlevel"], add["rank"], add["unit_class"]), (52, 52, 1, 1))
        self.assertEqual(math.ceil(WARRIOR_52_BASE * add["HealthModifier"]), SENTINEL_HEALTH)
        self.assertEqual(add["type"], TYPE_MECHANICAL)
        self.assertEqual(add["lootid"], 0)
        self.assertEqual(add["ExperienceModifier"], 0.0)
        self.assertEqual(add["difficulty_entry_1"], SENTINEL_HEROIC)
        # R-1-B B1: it never moves: fear and the other control mechanics (1972); the script roots it and puts it back
        # on its post after a grip or a knockback.
        self.assertEqual(add["CreatureImmunitiesId"], IMMUNITY_BOSS_STUN)
        self.assertIn("ReturnToPost", self.cpp)
        self.assertIn("UNIT_STATE_ROOT", self.cpp)
        self.assertEqual([m["CreatureDisplayID"] for m in self.models], [DISPLAY_VAULT_SENTINEL])
        self.assertIn("RegisterDungeonReworkCreatureAI(npc_brd_vault_sentinel", self.cpp)
        # WP-H's heroic health for it (28,000; the build spec's "about 28,000").
        self.assertRegex(HEROIC.read_text(encoding="utf-8"), r"300793: dict\(health=28_000\)")

    def test_the_hits_are_resolve_copies_of_the_right_school(self):
        for spell_id, school in ((FIELD_HIT, SCHOOL_ARCANE), (SWEEP_HIT, SCHOOL_NORMAL)):
            spell = self.spells[spell_id]
            self.assertEqual(spell["school"], school, spell_id)
            self.assertIn((spell_id, RESOLVE), self.scripts)
            self.assertEqual(spell["effect1"]["type"], SCHOOL_DAMAGE)
        self.assertIn(".Spell(SPELL_VA_FIELD_HIT)", self.cpp)
        self.assertIn(".Spell(SPELL_VA_SWEEP_HIT).Weakened()", self.cpp)

    def test_the_sweep_bar_lasts_the_warning_and_is_not_interruptible(self):
        bar = self.spells[SWEEP_CAST]
        self.assertEqual(bar["cast_time_ms"], _header_int("kSweepWarnMs"))
        self.assertEqual(_raw(bar, "InterruptFlags"), 0)
        self.assertEqual(_raw(bar, "PreventionType"), 0)
        self.assertEqual(_raw(bar, "SpellVisualID_1"), 2717)
        self.assertIn("DungeonKit::CastBar(me, SPELL_VA_SWEEP_CAST)", self.cpp)
        # No spell of the slice can be kicked (Doomgrip has no kickable cast; the link beam must not look cut).
        for spell_id, spell in self.spells.items():
            self.assertEqual(_raw(spell, "InterruptFlags"), 0, spell_id)

    def test_the_field_looks_are_the_four_rungs(self):
        for spell_id, visual in zip((FIELD_6, FIELD_7, FIELD_8, FIELD_9), (90653, 90654, 90655, 90656)):
            look = self.spells[spell_id]
            self.assertEqual(_raw(look, "SpellVisualID_1"), visual, spell_id)
            self.assertEqual(look["effect1"]["apply_aura"], AURA_DUMMY)
            self.assertEqual(look["duration_ms"], -1)
        self.assertEqual(_raw(self.spells[LOCKDOWN], "SpellVisualID_1"), 8225)
        self.assertEqual(_raw(self.spells[WAKES], "SpellVisualID_1"), 11519)
        self.assertEqual(self.spells[WAKES]["duration_ms"], _header_int("kWakeLookMs"))

    def test_the_link(self):
        beam = self.spells[LINK_BEAM]
        self.assertTrue(_raw(beam, "AttributesEx") & ATTR1_CHANNELED)
        self.assertEqual(_raw(beam, "ChannelInterruptFlags"), 0)
        self.assertEqual(_raw(beam, "SpellVisualID_1"), 13261)
        link = self.spells[SECURITY_LINK]
        effect = link["effect1"]
        self.assertEqual(effect["apply_aura"], AURA_MOD_DAMAGE_PERCENT_TAKEN)
        self.assertEqual(effect["base_points"] + 1, -_header_int("kLinkPctPerSentinel"))
        self.assertEqual(effect["misc_value"], 127)
        self.assertEqual(_raw(link, "CumulativeAura"), _header_int("kLinkMaxStacks"))
        self.assertEqual(link["dispel"], 0)
        self.assertIn("me->SetAuraStack(SPELL_VA_SECURITY_LINK, me, stacks)", self.cpp)

    def test_sunder_armor_is_real(self):
        sunder = self.spells[SUNDER]
        effect = sunder["effect1"]
        self.assertEqual(effect["apply_aura"], AURA_MOD_RESISTANCE_PCT)
        self.assertEqual(effect["base_points"] + 1, -_header_int("kSunderArmorPct"))
        self.assertEqual(effect["misc_value"], 1)
        self.assertEqual(_raw(sunder, "CumulativeAura"), _header_int("kSunderMaxStacks"))
        self.assertEqual(sunder["duration_ms"], _header_int("kSunderMs"))
        self.assertEqual(sunder["dispel"], 0)

    def test_the_draught_heals_five_percent_and_is_purgeable(self):
        draught = self.spells[DRAUGHT]
        self.assertEqual(draught["effect1"]["type"], HEAL_PCT)
        self.assertEqual(draught["effect1"]["base_points"] + 1, _header_int("kDraughtHealPct"))
        self.assertEqual(draught["effect2"]["apply_aura"], AURA_MOD_DAMAGE_PERCENT_DONE)
        self.assertEqual(draught["effect2"]["base_points"] + 1, _header_int("kDraughtDamagePct"))
        self.assertEqual(draught["duration_ms"], _header_int("kDraughtMs"))
        self.assertEqual(draught["dispel"], DISPEL_MAGIC)
        self.assertIn("d.purges.emplace_back(NPC_DOOMGRIP, SPELL_VA_WATCHMANS_DRAUGHT, 1)", self.cpp)

    def test_the_spec_numbers(self):
        self.assertEqual(_header_pair("kFieldPct"), (5.0, 8.0))
        self.assertEqual(_header_pair("kSweepPct"), (25.0, 40.0))
        self.assertEqual(_header_pair("kSweepEveryMs"), (15000.0, 12000.0))
        self.assertEqual(_header_pair("kWakeEveryMs"), (20000.0, 15000.0))

    def test_the_safe_items_are_the_declared_ones(self):
        tiers: dict[str, dict[str, int]] = {}
        for line in ITEM_IDS.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) >= 3 and parts[0].isdigit():
                tiers.setdefault(parts[1], {})[parts[2]] = int(parts[0])
        keys = ("brd_black_steel_bindings", "brd_wand_of_eternal_light", "brd_magma_forged_band",
                "brd_mana_shaping_handwraps")
        self.assertEqual(_header_ids("kGearNormal"), [tiers[k]["normal"] for k in keys])
        self.assertEqual(_header_ids("kGearHeroic"), [tiers[k]["heroic"] for k in keys])
        self.assertEqual(_header_ids("kGearNormal"), [22205, 22254, 22255, 22256])
        items = EVENT_ITEMS.read_text(encoding="utf-8")
        for entry in (70620, 70621, 70623):
            self.assertIn(str(entry), items)
        self.assertEqual(_header_int("kItemBagHeroic"), 70623)

    def test_the_wiring_names_exist_in_the_script(self):
        for needle in ("RegisterDungeonReworkGameObjectAI(go_brd_vault_secret_safe", "new brd_vault_safe_loot()",
                       "MISCHOOK_ON_AFTER_LOOT_TEMPLATE_PROCESS", "&store != &LootTemplates_Gameobject",
                       "instance->SetData(DATA_VAULT_CLOCK, seconds)", "instance->SetData(DATA_VAULT_RESET, 1)",
                       "BossMechanics::Who::Dps", "OnBossPull(me, kBossKey)", "options.bossStateId = BOSS_VAULT",
                       "_lockdown.KeepOut(strip, putOut)", "BrdTest::RegisterBoss(\"vault\""):
            self.assertIn(needle, self.cpp, needle)


class VaultSqlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = SQL_REV.read_text(encoding="utf-8")

    def test_the_texts_are_groups_one_to_five(self):
        rows = re.findall(r"\(9476, (\d), 0, '((?:[^']|'')*)', (\d+), ", self.sql)
        self.assertEqual([int(group) for group, _text, _type in rows], list(range(1, 6)))
        types = {int(group): int(kind) for group, _text, kind in rows}
        for group in range(1, 5):
            self.assertEqual(types[group], 41, group)
        self.assertEqual(types[5], 14)
        texts = {int(group): text for group, text, _kind in rows}
        self.assertEqual(texts[1], "A Vault Sentinel grinds to life!")
        self.assertEqual(texts[3], "The vault seals away a treasure!")
        self.assertEqual(texts[5], "The vault... is breached...")
        # The stock yell (group 0) stays.
        self.assertIn("`GroupID` BETWEEN 1 AND 5", self.sql)

    def test_the_four_constructs_become_sentinels_with_the_heroic_bit(self):
        self.assertIn("UPDATE `creature` SET `id` = 300793, `spawnMask` = 3 WHERE `id` = 8905 AND `guid` IN "
                      "(46608, 46610, 46611, 46612);", self.sql)

    def test_the_safe_runs_the_clock(self):
        self.assertIn("UPDATE `gameobject_template` SET `ScriptName` = 'go_brd_vault_secret_safe' WHERE `entry` = "
                      "161495;", self.sql)
        self.assertIn("WHERE `id` = 161495 AND `guid` = 43137;", self.sql)

    def test_no_smartai_and_no_loot_tables_here(self):
        # WP-S0's rev drops Doomgrip's SmartAI; the loot tables are WP-L-1's.
        self.assertNotIn("smart_scripts", self.sql)
        self.assertNotIn("loot_template", self.sql.replace("gameobject_loot_template 161495", ""))


if __name__ == "__main__":
    unittest.main()
