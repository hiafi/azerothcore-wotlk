"""
Shaman SH0b data gate (shaman-rework SH0b-HANDOFF row A6, SH0b-WP-BRIEF id map).

Loads the real shaman DSL package and asserts on the BUILT rows (stock base + DSL + raw_overrides via
`build.build_spell_row`), plus the declared creature / script / SLA / trainer / const tables and the generated header.
Each lint-style check is a pure function over rows so the negative fixtures can prove it fails.

Known exceptions that are NOT asserted (deliberate, see the brief):
  - Capacitor passive 202266 has no AttributesEx5 0x200 (first tick at 2 s).
  - The elemental summon passives 202274/202275 are SUMMON effects; Windwalk aura 202264 is a party area aura.
  - 6474 and 8145 get 0x200 from core (SpellInfoCorrections.cpp), not from the DSL.

Run: apps/dbc-tools/.venv/bin/python3 -m pytest apps/dbc-tools/lib/test_shaman_sh0b.py -q
"""

from __future__ import annotations

import csv
import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import build, dbcfmt, lint, source, spell_tables, state, trainer_state  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.reuse import ReuseContext  # noqa: E402
from lib.test_shaman_sh0a import m, spell_mask, _hex, _u32  # noqa: E402

TOOL_ROOT = Path(__file__).resolve().parents[1]
SHAMAN_DIR = TOOL_ROOT / "source" / "classes" / "shaman"
HEADER = TOOL_ROOT.parents[1] / "src" / "server" / "game" / "Entities" / "Unit" / "Generated" / "ShamanData.h"

NEW_SPELLS = tuple(range(202260, 202285))
# id -> (variable name, header name, built row name)
SPELL_MAP = {
    202260: ("earthbind_root_202260", "SPELL_EARTHBIND_ROOT", "Earthbind"),
    202261: ("earthen_wall_totem_202261", "SPELL_EARTHEN_WALL_TOTEM", "Earthen Wall Totem"),
    202262: ("earthen_wall_shield_202262", "SPELL_EARTHEN_WALL_SHIELD", "Earthen Wall"),
    202263: ("windwalk_totem_202263", "SPELL_WINDWALK_TOTEM", "Windwalk Totem"),
    202264: ("windwalk_202264", "SPELL_WINDWALK", "Windwalk"),
    202265: ("capacitor_totem_202265", "SPELL_CAPACITOR_TOTEM", "Capacitor Totem"),
    202266: ("capacitor_totem_passive_202266", "SPELL_CAPACITOR_TOTEM_PASSIVE", "Capacitor Totem Passive"),
    202267: ("capacitor_stun_202267", "SPELL_CAPACITOR_STUN", "Capacitor Totem"),
    202268: ("magma_totem_ground_202268", "SPELL_MAGMA_TOTEM_GROUND", "Magma Totem"),
    202269: ("magma_totem_passive_202269", "SPELL_MAGMA_TOTEM_PASSIVE", "Magma Totem Passive"),
    202270: ("searing_bolt_202270", "SPELL_SEARING_BOLT", "Searing Bolt"),
    202271: ("healing_stream_heal_202271", "SPELL_HEALING_STREAM_HEAL", "Healing Stream Totem"),
    202272: ("water_elemental_totem_202272", "SPELL_WATER_ELEMENTAL_TOTEM", "Water Elemental Totem"),
    202273: ("storm_elemental_totem_202273", "SPELL_STORM_ELEMENTAL_TOTEM", "Storm Elemental Totem"),
    202274: ("water_elemental_passive_202274", "SPELL_WATER_ELEMENTAL_PASSIVE", "Water Elemental Totem Passive"),
    202275: ("storm_elemental_passive_202275", "SPELL_STORM_ELEMENTAL_PASSIVE", "Storm Elemental Totem Passive"),
    202276: ("water_bolt_202276", "SPELL_WATER_BOLT", "Water Bolt"),
    202277: ("water_bolt_heal_202277", "SPELL_WATER_BOLT_HEAL", "Water Bolt"),
    202278: ("storm_bolt_202278", "SPELL_STORM_BOLT", "Storm Bolt"),
    202279: ("elemental_owner_stats_202279", "SPELL_ELEMENTAL_OWNER_STATS", "Elemental Spell Power"),
    202280: ("earthquake_202280", "SPELL_EARTHQUAKE", "Earthquake"),
    202281: ("earthquake_tick_202281", "SPELL_EARTHQUAKE_TICK", "Earthquake"),
    202282: ("elemental_blast_202282", "SPELL_ELEMENTAL_BLAST", "Elemental Blast"),
    202283: ("healing_rain_202283", "SPELL_HEALING_RAIN", "Healing Rain"),
    202284: ("healing_rain_heal_202284", "SPELL_HEALING_RAIN_HEAL", "Healing Rain"),
}
CREATURE_MAP = {
    300260: ("water_elemental_guardian_300260", "NPC_WATER_ELEMENTAL_GUARDIAN"),
    300261: ("storm_elemental_guardian_300261", "NPC_STORM_ELEMENTAL_GUARDIAN"),
    300270: ("earth_elemental_totem_300270", "NPC_EARTH_ELEMENTAL_TOTEM"),
    300271: ("fire_elemental_totem_300271", "NPC_FIRE_ELEMENTAL_TOTEM"),
    300272: ("water_elemental_totem_300272", "NPC_WATER_ELEMENTAL_TOTEM"),
    300273: ("storm_elemental_totem_300273", "NPC_STORM_ELEMENTAL_TOTEM"),
    300274: ("earthen_wall_totem_300274", "NPC_EARTHEN_WALL_TOTEM"),
    300275: ("windwalk_totem_300275", "NPC_WINDWALK_TOTEM"),
    300276: ("capacitor_totem_300276", "NPC_CAPACITOR_TOTEM"),
    300277: ("magma_totem_300277", "NPC_MAGMA_TOTEM"),
    300278: ("searing_totem_300278", "NPC_SEARING_TOTEM"),
}
CLASS_SET = 11
# Every id the stage touches that must carry EquippedItemClass -1 (new ids plus the edited stock rows).
STOCK_EDITED = (2062, 2894, 2484, 8143, 3599, 5394, 8170, 8177, 8187, 8172, 5672, 6474, 52041)
EQUIPPED_IDS = NEW_SPELLS + STOCK_EDITED
# Totem passives that must carry AttributesEx5 0x200 in the DSL (202266 first tick at 2 s; 6474/8145 get it from core).
PASSIVES_WITH_0X200 = (202269, 8172, 5672)
GROUND_PERIODIC_DUMMY = (202280, 202283)
GROUND_HELPERS = (202281, 202284)
ELEMENTAL_SUMMONS = (2062, 2894, 202272, 202273)
SUMMON_SPELLS = (2062, 2894, 2484, 8143, 3599, 8170, 8177, 202261, 202263, 202265, 202268, 202272, 202273)
TOOL_COLUMNS = ("Totem_1", "Totem_2", "RequiredTotemCategoryID_1", "RequiredTotemCategoryID_2")
PERIODIC_DAMAGE_HEAL_AURAS = {3, 8, 20, 53, 89}  # PERIODIC_DAMAGE, PERIODIC_HEAL, OBS_MOD_HEALTH, LEECH, DAMAGE_PERCENT
ATTR0_COOLDOWN_ON_EVENT = 0x02000000
ATTR0_NOT_SHAPESHIFT_SUMMON_BIT = 0x10000  # the totem "cast bar" bit Windwalk must not carry
ATTR5_EX5_PERIODIC_FIRST_TICK = 0x200
ATTR5_EX5_FORBID_PERIODIC_DMG = 0x2000
ATTR5_EX5_GROUND_AREA = 0x08000000
ATTR2_EX2_TRIGGERED = 0x4
EFFECT_DUMMY = 3
SCRIPTS = {
    2062: "spell_sha_elemental_lockout", 2894: "spell_sha_elemental_lockout",
    202272: "spell_sha_elemental_lockout", 202273: "spell_sha_elemental_lockout",
    6474: "spell_sha_earthbind_pulse", 5672: "spell_sha_healing_stream_passive", 52041: "spell_sha_healing_stream_pulse",
    202261: "spell_sha_earthen_wall", 202262: "spell_sha_earthen_wall_shield", 202276: "spell_sha_water_bolt",
    202279: "spell_sha_elemental_owner_stats", 202280: "spell_sha_earthquake", 202283: "spell_sha_healing_rain",
    12470: "spell_sha_elemental_engaged_aoe", 13376: "spell_sha_elemental_engaged_aoe",
    36213: "spell_sha_angered_earth_engaged",
}
SCRIPT_REMOVALS = {(6474, "spell_sha_earthbind_totem"), (52041, "spell_sha_healing_stream_totem")}
CONSTS = {
    "SEARING_BOLT_PERIOD_MS": 1000, "SEARING_BOLT_COUNT": 10, "SEARING_RANGE_YD": 20.0,
    "EARTHEN_WALL_PERIOD_MS": 2000, "EARTHEN_WALL_PULSES": 8, "EARTHEN_WALL_RANGE_YD": 40.0,
    "HEALING_STREAM_TARGETS": 5, "HEALING_STREAM_RANGE_YD": 40.0,
    "ELEMENTAL_LOCKOUT_MS": 120000, "WATER_BOLT_HEAL_TARGETS": 3, "WATER_BOLT_HEAL_RANGE_YD": 40.0,
    "ELEMENTAL_CHASE_RANGE_YD": 30.0, "ELEMENTAL_TARGET_RANGE_YD": 40.0, "ELEMENTAL_STAT_REFRESH_MS": 2000,
    "ELEMENTAL_TOTEM_DISPLAY_INVISIBLE": 11686, "HEALING_RAIN_TARGETS": 5,
}
# SkillLineAbility id -> (skill line, spell)
SLAS = {
    30660: (375, 202261), 30661: (373, 202263), 30662: (373, 202265), 30663: (375, 202268), 30664: (374, 202272),
    30665: (375, 202273), 30666: (375, 202280), 30667: (375, 202282), 30668: (374, 202283),
}
SHAMAN_CLASS_MASK = 64
# trainer 210 spell -> learn level (also the row's SpellLevel)
TRAINED = {202261: 20, 202263: 30, 202265: 42, 202268: 26, 2062: 26, 2894: 36, 202272: 46, 202273: 56,
           202280: 38, 202282: 50, 202283: 30}
UNTRAINED = {(210, 5730), (210, 8190)}
# creature -> index-0 creature_spell (None: no creature_spell row at all, a passive totem driven by its own AI)
CREATURE_SPELL0 = {300270: 33663, 300271: 32982, 300272: 202274, 300273: 202275, 300274: None, 300275: 202264,
                   300276: 202266, 300277: 202269, 300278: None, 300260: 202276, 300261: 202278}
NEW_TOTEM_PASSIVES = {300275: 202264, 300276: 202266, 300277: 202269, 300272: 202274, 300273: 202275}
SCRIPT_NAMES = {300270: "npc_sha_elemental_totem", 300271: "npc_sha_elemental_totem",
                300272: "npc_sha_elemental_totem", 300273: "npc_sha_elemental_totem",
                300274: "npc_sha_earthen_wall_totem", 300278: "npc_sha_searing_totem",
                300260: "npc_sha_water_elemental", 300261: "npc_sha_storm_elemental",
                15438: "npc_sha_fire_elemental_rework", 15352: "npc_sha_earth_elemental_rework"}


def _entry_duration(entry: dict) -> int:
    return int(entry.get("duration_ms") or 0)


# ---- checks (pure: take built rows / declared entries, return problem strings) -----------------------------

def check_equipped_item_class(rows: dict[int, dict]) -> list[str]:
    return [f"{i}: EquippedItemClass {rows[i].get('EquippedItemClass')!r}, expected -1"
            for i in EQUIPPED_IDS if i in rows and _u32(rows[i].get("EquippedItemClass")) != 0xFFFFFFFF]


def check_forbidden_bits(rows: dict[int, dict], ids=NEW_SPELLS) -> list[str]:
    bad = []
    for i in ids:
        if i not in rows:
            continue
        mask = spell_mask(rows[i])
        hit = (mask[0] & m.FORBIDDEN_D0, mask[1] & m.FORBIDDEN_D1, mask[2] & m.FORBIDDEN_D2)
        if any(hit):
            bad.append(f"{i}: SpellClassMask {_hex(mask)} holds forbidden bits {_hex(hit)}")
    return bad


def check_passive_0x200(rows: dict[int, dict]) -> list[str]:
    bad = [f"{i}: totem passive lacks AttributesEx5 0x200" for i in PASSIVES_WITH_0X200
           if i in rows and not _u32(rows[i].get("AttributesEx5")) & ATTR5_EX5_PERIODIC_FIRST_TICK]
    bad += [f"{i}: PERIODIC_DUMMY ground spell carries AttributesEx5 0x200" for i in GROUND_PERIODIC_DUMMY
            if i in rows and _u32(rows[i].get("AttributesEx5")) & ATTR5_EX5_PERIODIC_FIRST_TICK]
    return bad


def check_ground_spells(rows: dict[int, dict]) -> list[str]:
    bad = []
    for i in GROUND_PERIODIC_DUMMY:
        row = rows.get(i)
        if row is None:
            continue
        ex5 = _u32(row.get("AttributesEx5"))
        if ex5 & ATTR5_EX5_FORBID_PERIODIC_DMG:
            bad.append(f"{i}: AttributesEx5 {ex5:#x} carries 0x2000")
        if not ex5 & ATTR5_EX5_GROUND_AREA:
            bad.append(f"{i}: AttributesEx5 {ex5:#x} lacks 0x08000000")
        for n in (1, 2, 3):
            if int(row.get(f"EffectAura_{n}") or 0) in PERIODIC_DAMAGE_HEAL_AURAS:
                bad.append(f"{i}: effect {n} is a periodic damage/heal aura {row.get(f'EffectAura_{n}')}")
    for i in GROUND_HELPERS:
        if i in rows and not _u32(rows[i].get("AttributesEx2")) & ATTR2_EX2_TRIGGERED:
            bad.append(f"{i}: AttributesEx2 lacks 0x4")
    return bad


def check_healing_rain_carrier(rows: dict[int, dict]) -> list[str]:
    row = rows.get(202283)
    if row is None:
        return []
    if int(row.get("Effect_3") or 0) != EFFECT_DUMMY:
        return [f"202283: effect 3 is {row.get('Effect_3')}, expected the DUMMY torrent carrier ({EFFECT_DUMMY})"]
    return []


def check_summon_duration_below_cooldown(entries: dict[int, dict]) -> list[str]:
    bad = []
    for i in SUMMON_SPELLS:
        e = entries.get(i)
        if e is None:
            continue
        dur, cd = _entry_duration(e), int(e.get("cooldown_ms") or 0)
        if dur and cd and dur >= cd:
            bad.append(f"{i}: duration {dur} ms is not below cooldown {cd} ms")
    return bad


def check_tool_columns(rows: list[dict]) -> list[str]:
    return [f"{r['ID']}: family-11 row holds {c}={r[c]}" for r in rows
            if int(r.get("SpellClassSet") or 0) == CLASS_SET for c in TOOL_COLUMNS if int(r.get(c) or 0)]


def check_elemental_summons(rows: dict[int, dict]) -> list[str]:
    bad = []
    for i in ELEMENTAL_SUMMONS:
        row = rows.get(i)
        if row is None:
            continue
        for col, want in (("Category", 0), ("RecoveryTime", 120000), ("CategoryRecoveryTime", 0)):
            if int(row.get(col) or 0) != want:
                bad.append(f"{i}: {col} {row.get(col)}, expected {want}")
        if _u32(row.get("Attributes")) & ATTR0_COOLDOWN_ON_EVENT:
            bad.append(f"{i}: carries COOLDOWN_ON_EVENT (Attributes 0x02000000)")
    return bad


def check_windwalk(rows: dict[int, dict]) -> list[str]:
    return [f"{i}: Attributes {_u32(rows[i].get('Attributes')):#x} carries 0x10000" for i in (202263, 202264)
            if i in rows and _u32(rows[i].get("Attributes")) & ATTR0_NOT_SHAPESHIFT_SUMMON_BIT]


EFFECT_APPLY_AREA_AURA_PARTY = 35
CAST_TIMES_MS = {202280: 1500, 202283: 2000}


def check_wp_r_fixes(rows: dict[int, dict], entries: dict[int, dict], cast_index) -> list[str]:
    """WP-R fixes: Windwalk party area aura effect, ground-cast cast times (no raw twin), shield / heal flags."""
    bad = []
    wind = rows.get(202264)
    if wind is not None:
        for n in (1, 2):
            if int(wind.get(f"Effect_{n}") or 0) != EFFECT_APPLY_AREA_AURA_PARTY:
                bad.append(f"202264: Effect_{n} {wind.get(f'Effect_{n}')}, expected APPLY_AREA_AURA_PARTY (35)")
    for i, ms in CAST_TIMES_MS.items():
        e, row = entries.get(i), rows.get(i)
        if e is None or row is None:
            continue
        if int(e.get("cast_time_ms") or 0) != ms:
            bad.append(f"{i}: cast_time_ms {e.get('cast_time_ms')}, expected {ms}")
        if "CastingTimeIndex" in (e.get("raw_overrides") or {}):
            bad.append(f"{i}: raw_overrides holds a CastingTimeIndex twin")
        if cast_index is not None and int(row.get("CastingTimeIndex") or 0) != cast_index(ms):
            bad.append(f"{i}: built CastingTimeIndex {row.get('CastingTimeIndex')} is not the {ms} ms index")
    shield = rows.get(202262)
    if shield is not None and not _u32(shield.get("AttributesEx3")) & 0x80:
        bad.append("202262: AttributesEx3 lacks 0x80")
    heal = rows.get(202277)
    if heal is not None and not _u32(heal.get("AttributesEx2")) & ATTR2_EX2_TRIGGERED:
        bad.append("202277: AttributesEx2 lacks 0x4")
    return bad


def check_elemental_blast(rows: dict[int, dict]) -> list[str]:
    row = rows.get(202282)
    if row is None:
        return []
    bad = []
    if int(row.get("SchoolMask") or 0) != 0x1C:
        bad.append(f"202282: SchoolMask {row.get('SchoolMask')}, expected 0x1C")
    mask = spell_mask(row)
    if mask[0] & (m.FORBIDDEN_D0_B0 | m.FORBIDDEN_D0_B1):
        bad.append(f"202282: SpellClassMask d0 {mask[0]:#x} carries b0/b1")
    if mask[1] & m.FORBIDDEN_D1_B12:
        bad.append(f"202282: SpellClassMask d1 {mask[1]:#x} carries b12 (Lava Burst)")
    return bad


def check_shield_bits(rows: dict[int, dict]) -> list[str]:
    row = rows.get(202262)
    if row is None:
        return []
    mask = spell_mask(row)
    bad = []
    if mask[1] & (m.FORBIDDEN_D1_B5 | m.FORBIDDEN_D1_B10):
        bad.append(f"202262: d1 {mask[1]:#x} carries b5/b10")
    if mask[0] & m.FORBIDDEN_D0_B10:
        bad.append(f"202262: d0 {mask[0]:#x} carries b10")
    return bad


def check_magma_ground_mask(rows: dict[int, dict]) -> list[str]:
    row = rows.get(202268)
    if row is None:
        return []
    d0 = spell_mask(row)[0]
    bad = []
    if not d0 & m.MAGMA_SUMMON_D0_B12:
        bad.append(f"202268: d0 {d0:#x} lacks MAGMA_SUMMON_D0_B12 (0x1000)")
    if d0 & m.SUMMON_D0_B29:
        bad.append(f"202268: d0 {d0:#x} carries b29 (the Magma summon uses b12)")
    return bad


def check_magma_potency(entries: dict[int, dict]) -> list[str]:
    e = entries.get(8187)
    if e is None:
        return []
    pot = (e.get("effect1") or {}).get("_potency") or {}
    got = pot.get("total_potency")
    return [] if got == 20.0 else [f"8187: effect 1 total potency {got!r}, expected 20"]


def check_npc_csv_strip(npc: dict[int, dict], stock: dict[int, dict], ids) -> list[str]:
    """npc.csv rows of family 11 that hold a stock tool column must zero all four columns in raw_overrides."""
    return [f"npc.csv {i}: raw_overrides {c}={npc[i].get(c)!r}, expected 0" for i in sorted(ids) if i in npc
            for c in TOOL_COLUMNS if int(stock[i].get(c) or 0) and npc[i].get(c) != 0]


def check_creature_spell_index0(creature_spells: list[dict]) -> list[str]:
    index0 = {int(r["CreatureID"]): int(r["Spell"]) for r in creature_spells if int(r["Index"]) == 0}
    bad = []
    for cid, want in CREATURE_SPELL0.items():
        got = index0.get(cid)
        if got != want:
            bad.append(f"{cid}: creature_spell index 0 is {got}, expected {want}")
    for r in creature_spells:
        if int(r["CreatureID"]) in (300274, 300278):
            bad.append(f"{r['CreatureID']}: passive totem has a creature_spell row (index {r['Index']})")
    return sorted(set(bad))


def check_scripts(bindings: list[dict], removals: list[dict]) -> list[str]:
    have = {(int(b["spell_id"]), b["ScriptName"]) for b in bindings}
    bad = [f"{sid}: script {name!r} not bound" for sid, name in SCRIPTS.items() if (sid, name) not in have]
    gone = {(int(r["spell_id"]), r["ScriptName"]) for r in removals}
    bad += [f"{sid}: stock script {name!r} not unbound" for sid, name in SCRIPT_REMOVALS if (sid, name) not in gone]
    return bad


def check_consts(consts: list[dict]) -> list[str]:
    have = {c["name"]: c["value"] for c in consts}
    return [f"const {n}: {have.get(n)!r}, expected {v!r}" for n, v in CONSTS.items() if have.get(n) != v]


def check_var_names(spell_vars: dict[int, str], creature_vars: dict[int, str]) -> list[str]:
    bad = [f"{i}: variable {spell_vars.get(i)!r}, expected {v[0]!r}" for i, v in SPELL_MAP.items()
           if spell_vars.get(i) != v[0]]
    bad += [f"{i}: variable {creature_vars.get(i)!r}, expected {v[0]!r}" for i, v in CREATURE_MAP.items()
            if creature_vars.get(i) != v[0]]
    return bad


def check_header(text: str) -> list[str]:
    bad = []
    for i, (_var, name, _row) in SPELL_MAP.items():
        if not re.search(rf"\b{name} = {i};", text):
            bad.append(f"header: {name} = {i} missing")
    for i, (_var, name) in CREATURE_MAP.items():
        if not re.search(rf"\b{name} = {i};", text):
            bad.append(f"header: {name} = {i} missing")
    for n, v in CONSTS.items():
        if not re.search(rf"\b{n} = ", text):
            bad.append(f"header: const {n} missing")
    return bad


def check_names_levels(rows: dict[int, dict]) -> list[str]:
    bad = []
    for i, (_v, _h, name) in SPELL_MAP.items():
        row = rows.get(i)
        if row is None:
            bad.append(f"{i}: not built")
            continue
        if row.get("Name_Lang_enUS") != name:
            bad.append(f"{i}: name {row.get('Name_Lang_enUS')!r}, expected {name!r}")
        if int(row.get("SpellClassSet") or 0) not in (CLASS_SET, 0):
            bad.append(f"{i}: SpellClassSet {row.get('SpellClassSet')}")
    for i, lvl in TRAINED.items():
        row = rows.get(i)
        if row is not None and int(row.get("SpellLevel") or 0) != lvl:
            bad.append(f"{i}: SpellLevel {row.get('SpellLevel')}, expected {lvl}")
    return bad


def check_sla_and_trainers(slas: list[dict], trainers: list[dict], removals: list[dict]) -> list[str]:
    bad = []
    by_id = {int(s["id"]): s for s in slas}
    for sid, (line, spell) in SLAS.items():
        s = by_id.get(sid)
        if s is None:
            bad.append(f"SLA {sid}: missing")
            continue
        if (int(s["skill_line"]), int(s["spell_id"])) != (line, spell):
            bad.append(f"SLA {sid}: ({s['skill_line']}, {s['spell_id']}), expected ({line}, {spell})")
        if int(s["class_mask"]) != SHAMAN_CLASS_MASK or int(s["race_mask"]) != 0 or int(s["acquire_method"]) != 0:
            bad.append(f"SLA {sid}: class_mask {s['class_mask']} race {s['race_mask']} acquire {s['acquire_method']}")
    levels = {(int(t["TrainerId"]), int(t["SpellId"])): int(t["ReqLevel"]) for t in trainers}
    for spell, lvl in TRAINED.items():
        if levels.get((210, spell)) != lvl:
            bad.append(f"trainer 210 spell {spell}: ReqLevel {levels.get((210, spell))}, expected {lvl}")
    gone = {(int(r["TrainerId"]), int(r["SpellId"])) for r in removals}
    bad += [f"untrain {k} missing" for k in sorted(UNTRAINED - gone)]
    return bad


def check_creatures(creatures: dict[int, dict]) -> list[str]:
    bad = []
    for cid, name in SCRIPT_NAMES.items():
        c = creatures.get(cid)
        if c is None:
            bad.append(f"{cid}: creature not declared")
        elif c["ScriptName"] != name:
            bad.append(f"{cid}: ScriptName {c['ScriptName']!r}, expected {name!r}")
    for cid in (300275, 300276, 300277):
        c = creatures.get(cid)
        if c is not None and c["ScriptName"]:
            bad.append(f"{cid}: unexpected ScriptName {c['ScriptName']!r}")
    for cid in (300270, 300271, 300272, 300273):
        c = creatures.get(cid)
        if c is not None and int(c["unit_flags"]) != 0x02000002:
            bad.append(f"{cid}: unit_flags {int(c['unit_flags']):#x}, expected 0x02000002")
    for cid in (300274, 300275, 300276, 300277, 300278):
        c = creatures.get(cid)
        if c is not None and (int(c["faction"]) != 58 or (int(c["minlevel"]), int(c["maxlevel"])) != (1, 80)):
            bad.append(f"{cid}: faction {c['faction']} level {c['minlevel']}-{c['maxlevel']}, expected 58 / 1-80")
    return bad


def check_new_totem_passive_pairing(creature_spells: list[dict], rows: dict[int, dict]) -> list[str]:
    """Each new totem's index-0 spell must be its declared passive."""
    index0 = {int(r["CreatureID"]): int(r["Spell"]) for r in creature_spells if int(r["Index"]) == 0}
    bad = []
    for cid, want in NEW_TOTEM_PASSIVES.items():
        if index0.get(cid) != want:
            bad.append(f"{cid}: index 0 is {index0.get(cid)}, expected passive {want}")
        elif want not in rows:
            bad.append(f"{want}: index-0 passive of {cid} is not a declared spell")
    return bad


# ---- real data ----------------------------------------------------------------------------------------------

_CACHE: dict = {}


def _data():
    if not _CACHE:
        ids_cfg = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
        sti = spell_tables.load_spell_table_index()
        cti = spell_tables.load_creature_table_index()
        package = registry.load_class_package(
            SHAMAN_DIR, ids_cfg=ids_cfg, trainer_index=trainer_state.load_trainer_index(),
            existing_group_ids={key[0] for key in sti.live_keys("spell_group")},
            shapeshift_index=state.load_stock_rows(dbcfmt.SPELLSHAPESHIFTFORM),
            existing_creature_rows={int(r["entry"]): r for r in cti.live_rows("creature_template")},
            creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
            creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS,
            live_data=spell_tables.load_dsl_live_data(),
        )
        reuse = ReuseContext({}, ids_cfg)
        rows = [build.build_spell_row(e, reuse) for e in package.spells]
        strip_ids = [int(x) for x in re.findall(r"^\s+id=(\d+),", (SHAMAN_DIR / "shaman_stock_tool_strip.py")
                                                 .read_text(), re.M)]
        _CACHE.update(
            package=package, rows=rows, rows_by_id={int(r["ID"]): r for r in rows},
            entries_by_id={int(e["id"]): e for e in package.spells}, reuse=reuse,
            creatures={int(c["entry"]): c for c in package.creature_templates},
            stock=state.load_stock_rows(dbcfmt.SPELL), strip_ids=strip_ids,
        )
    return _CACHE


class ShamanSH0bDataTest(unittest.TestCase):
    def assertClean(self, problems: list[str]):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_every_new_id_is_declared(self):
        d = _data()
        self.assertClean([f"{i}: not declared" for i in NEW_SPELLS if i not in d["rows_by_id"]])
        self.assertClean([f"{i}: not declared" for i in CREATURE_MAP if i not in d["creatures"]])

    def test_names_and_levels(self):
        self.assertClean(check_names_levels(_data()["rows_by_id"]))

    def test_variable_names(self):
        p = _data()["package"]
        self.assertClean(check_var_names(p.spell_var_names, p.creature_var_names))

    def test_generated_header_names(self):
        self.assertClean(check_header(HEADER.read_text()))

    def test_equipped_item_class(self):
        self.assertClean(check_equipped_item_class(_data()["rows_by_id"]))

    def test_no_forbidden_bits_on_new_rows(self):
        self.assertClean(check_forbidden_bits(_data()["rows_by_id"]))

    def test_totem_passive_0x200(self):
        self.assertClean(check_passive_0x200(_data()["rows_by_id"]))

    def test_ground_spells(self):
        self.assertClean(check_ground_spells(_data()["rows_by_id"]))

    def test_healing_rain_dummy_carrier(self):
        self.assertClean(check_healing_rain_carrier(_data()["rows_by_id"]))

    def test_summon_duration_below_cooldown(self):
        self.assertClean(check_summon_duration_below_cooldown(_data()["entries_by_id"]))

    def test_no_family_11_tool_column(self):
        self.assertClean(check_tool_columns(_data()["rows"]))

    def test_stock_tool_strip_declares_75_rows_all_stripped(self):
        d = _data()
        self.assertEqual(len(d["strip_ids"]), 75)
        for i in d["strip_ids"]:
            row = d["rows_by_id"][i]
            self.assertEqual(int(row["SpellClassSet"]), CLASS_SET, i)
            self.assertFalse(any(int(row.get(c) or 0) for c in TOOL_COLUMNS), i)
            # the stock client row held a tool column, so the strip is a real change
            self.assertTrue(any(int(d["stock"][i].get(c) or 0) for c in TOOL_COLUMNS), i)

    def test_widened_lint_is_silent_over_stock_and_declared(self):
        # The class-file package alone leaves the npc.csv-declared stock rows (A2 strips those in their raw_overrides
        # JSON); every warning must be one of those, and each must hold all four columns at 0 in that JSON.
        d = _data()
        self.assertEqual(lint.TOOL_FREE_CLASS_SETS, frozenset({11}))
        warned = {int(w.split()[1]) for w in lint.check_totem_tools(d["package"].spells, d["rows"], {11}, d["stock"])}
        with (TOOL_ROOT / "source" / "spells" / "npc.csv").open(newline="") as f:
            npc = {int(r["id"]): json.loads(r["raw_overrides"] or "{}") for r in csv.DictReader(f)}
        self.assertEqual(sorted(warned - set(npc)), [], "undeclared stock family-11 rows still holding a tool column")
        self.assertEqual(check_npc_csv_strip(npc, d["stock"], warned), [])

    def test_elemental_summons(self):
        self.assertClean(check_elemental_summons(_data()["rows_by_id"]))

    def test_windwalk(self):
        self.assertClean(check_windwalk(_data()["rows_by_id"]))

    def test_elemental_blast(self):
        self.assertClean(check_elemental_blast(_data()["rows_by_id"]))

    def test_wp_r_fixes(self):
        d = _data()
        self.assertClean(check_wp_r_fixes(d["rows_by_id"], d["entries_by_id"], d["reuse"].cast_time_index))

    def test_shield_bits(self):
        self.assertClean(check_shield_bits(_data()["rows_by_id"]))

    def test_magma_ground_mask(self):
        self.assertClean(check_magma_ground_mask(_data()["rows_by_id"]))

    def test_magma_pulse_potency(self):
        self.assertClean(check_magma_potency(_data()["entries_by_id"]))

    def test_creature_spell_index0(self):
        self.assertClean(check_creature_spell_index0(_data()["package"].creature_template_spells))

    def test_new_totem_passive_pairing(self):
        d = _data()
        self.assertClean(check_new_totem_passive_pairing(d["package"].creature_template_spells, d["rows_by_id"]))

    def test_script_bindings(self):
        p = _data()["package"]
        self.assertClean(check_scripts(p.spell_script_names, p.script_removals))

    def test_consts(self):
        self.assertClean(check_consts(_data()["package"].consts))

    def test_sla_and_trainers(self):
        p = _data()["package"]
        self.assertClean(check_sla_and_trainers(p.skill_line_abilities, p.trainer_spells, p.trainer_removals))

    def test_creatures(self):
        self.assertClean(check_creatures(_data()["creatures"]))


# ---- negative fixtures: every check must fire on a minimal bad input ---------------------------------------

def _row(spell_id=1, **cols) -> dict:
    return {"ID": spell_id, **cols}


class ShamanSH0bNegativeTest(unittest.TestCase):
    def test_equipped_item_class(self):
        self.assertEqual(len(check_equipped_item_class({202261: _row(202261, EquippedItemClass=0)})), 1)
        self.assertEqual(len(check_equipped_item_class({202261: _row(202261)})), 1)
        self.assertEqual(check_equipped_item_class({202261: _row(202261, EquippedItemClass=-1)}), [])

    def test_forbidden_bits(self):
        for col, bit in (("SpellClassMask_1", m.FORBIDDEN_D0_B0), ("SpellClassMask_1", m.FORBIDDEN_D0_B28),
                         ("SpellClassMask_2", m.FORBIDDEN_D1_B12), ("SpellClassMask_2", m.FORBIDDEN_D1_B5),
                         ("SpellClassMask_3", m.FORBIDDEN_D2_B11)):
            self.assertEqual(len(check_forbidden_bits({202261: _row(202261, **{col: bit})})), 1, col)
        self.assertEqual(check_forbidden_bits({202261: _row(202261, SpellClassMask_1=m.EARTHEN_WALL_SUMMON)}), [])
        self.assertEqual(check_forbidden_bits({8017: _row(8017, SpellClassMask_1=1)}), [])  # not a new id

    def test_passive_0x200(self):
        self.assertEqual(len(check_passive_0x200({202269: _row(202269)})), 1)
        self.assertEqual(check_passive_0x200({202269: _row(202269, AttributesEx5=0x200)}), [])
        self.assertEqual(len(check_passive_0x200({202280: _row(202280, AttributesEx5=0x200)})), 1)
        self.assertEqual(check_passive_0x200({202266: _row(202266)}), [])  # Capacitor passive is exempt

    def test_ground_spells(self):
        good = _row(202280, AttributesEx5=0x08000000, EffectAura_1=4, EffectAura_2=226)
        self.assertEqual(check_ground_spells({202280: good}), [])
        self.assertEqual(len(check_ground_spells({202280: {**good, "AttributesEx5": 0x08002000}})), 1)
        self.assertEqual(len(check_ground_spells({202280: {**good, "AttributesEx5": 0}})), 1)
        self.assertEqual(len(check_ground_spells({202283: {**good, "ID": 202283, "EffectAura_3": 3}})), 1)
        self.assertEqual(len(check_ground_spells({202283: {**good, "ID": 202283, "EffectAura_2": 8}})), 1)
        self.assertEqual(len(check_ground_spells({202281: _row(202281)})), 1)
        self.assertEqual(check_ground_spells({202281: _row(202281, AttributesEx2=0x4)}), [])

    def test_healing_rain_carrier(self):
        self.assertEqual(len(check_healing_rain_carrier({202283: _row(202283, Effect_3=0)})), 1)
        self.assertEqual(check_healing_rain_carrier({202283: _row(202283, Effect_3=3)}), [])

    def test_summon_duration_below_cooldown(self):
        self.assertEqual(len(check_summon_duration_below_cooldown(
            {202261: {"duration_ms": 60000, "cooldown_ms": 60000}})), 1)
        self.assertEqual(check_summon_duration_below_cooldown(
            {202261: {"duration_ms": 15000, "cooldown_ms": 60000}}), [])

    def test_tool_columns(self):
        for col in TOOL_COLUMNS:
            self.assertEqual(len(check_tool_columns([_row(2484, SpellClassSet=11, **{col: 2})])), 1, col)
        self.assertEqual(check_tool_columns([_row(2484, SpellClassSet=11, Totem_1=0)]), [])
        self.assertEqual(check_tool_columns([_row(100, SpellClassSet=7, Totem_1=5)]), [])
        # the widened lint fires on the stock case the constant now guards
        self.assertEqual(len(lint.check_totem_tools([{"name": "x"}], [_row(2484, SpellClassSet=11,
                                                                         Totem_1=5175)], {11})), 1)

    def test_elemental_summons(self):
        good = _row(202272, Category=0, RecoveryTime=120000, CategoryRecoveryTime=0)
        self.assertEqual(check_elemental_summons({202272: good}), [])
        self.assertEqual(len(check_elemental_summons({202272: {**good, "Category": 23}})), 1)
        self.assertEqual(len(check_elemental_summons({202272: {**good, "RecoveryTime": 600000}})), 1)
        self.assertEqual(len(check_elemental_summons({202272: {**good, "CategoryRecoveryTime": 1}})), 1)
        self.assertEqual(len(check_elemental_summons({202272: {**good, "Attributes": 0x02000000}})), 1)

    def test_windwalk(self):
        self.assertEqual(len(check_windwalk({202263: _row(202263, Attributes=0x10000)})), 1)
        self.assertEqual(check_windwalk({202263: _row(202263, Attributes=0)}), [])

    def test_elemental_blast(self):
        good = _row(202282, SchoolMask=0x1C, SpellClassMask_3=m.ELEMENTAL_BLAST)
        self.assertEqual(check_elemental_blast({202282: good}), [])
        self.assertEqual(len(check_elemental_blast({202282: {**good, "SchoolMask": 4}})), 1)
        self.assertEqual(len(check_elemental_blast({202282: {**good, "SpellClassMask_1": 1}})), 1)
        self.assertEqual(len(check_elemental_blast({202282: {**good, "SpellClassMask_1": 2}})), 1)
        self.assertEqual(len(check_elemental_blast({202282: {**good, "SpellClassMask_2": 0x1000}})), 1)

    def test_wp_r_fixes_negative(self):
        rows = {202264: _row(202264, Effect_1=35, Effect_2=35),
                202280: _row(202280, CastingTimeIndex=5), 202283: _row(202283, CastingTimeIndex=7),
                202262: _row(202262, AttributesEx3=0x80), 202277: _row(202277, AttributesEx2=0x4)}
        entries = {202280: {"cast_time_ms": 1500, "raw_overrides": {}}, 202283: {"cast_time_ms": 2000}}
        idx = {1500: 5, 2000: 7}.get
        self.assertEqual(check_wp_r_fixes(rows, entries, idx), [])
        self.assertEqual(len(check_wp_r_fixes({**rows, 202264: _row(202264, Effect_1=61, Effect_2=35)}, entries, idx)), 1)
        self.assertEqual(len(check_wp_r_fixes({**rows, 202264: _row(202264, Effect_1=61, Effect_2=61)}, entries, idx)), 2)
        self.assertEqual(len(check_wp_r_fixes(rows, {**entries, 202280: {"cast_time_ms": 0}}, idx)), 1)
        self.assertEqual(len(check_wp_r_fixes(rows, {**entries, 202283: {"cast_time_ms": 2000,
                                              "raw_overrides": {"CastingTimeIndex": 1}}}, idx)), 1)
        self.assertEqual(len(check_wp_r_fixes({**rows, 202283: _row(202283, CastingTimeIndex=1)}, entries, idx)), 1)
        self.assertEqual(len(check_wp_r_fixes({**rows, 202262: _row(202262)}, entries, idx)), 1)
        self.assertEqual(len(check_wp_r_fixes({**rows, 202277: _row(202277)}, entries, idx)), 1)

    def test_shield_bits(self):
        self.assertEqual(check_shield_bits({202262: _row(202262, SpellClassMask_3=m.EARTHEN_WALL_SHIELD)}), [])
        for col, bit in (("SpellClassMask_2", 0x20), ("SpellClassMask_2", 0x400), ("SpellClassMask_1", 0x400)):
            self.assertEqual(len(check_shield_bits({202262: _row(202262, **{col: bit})})), 1, (col, bit))

    def test_magma_ground_mask(self):
        self.assertEqual(check_magma_ground_mask({202268: _row(202268, SpellClassMask_1=0x1000)}), [])
        self.assertEqual(len(check_magma_ground_mask({202268: _row(202268, SpellClassMask_1=0x20000000)})), 2)
        self.assertEqual(len(check_magma_ground_mask({202268: _row(202268, SpellClassMask_1=0x20001000)})), 1)

    def test_magma_potency(self):
        self.assertEqual(check_magma_potency({8187: {"effect1": {"_potency": {"total_potency": 20.0}}}}), [])
        self.assertEqual(len(check_magma_potency({8187: {"effect1": {"_potency": {"total_potency": 92.3}}}})), 1)
        self.assertEqual(len(check_magma_potency({8187: {"effect1": {}}})), 1)

    def test_npc_csv_strip(self):
        stock = {1: {"Totem_1": 5175, "RequiredTotemCategoryID_1": 2}}
        zeros = {c: 0 for c in TOOL_COLUMNS}
        self.assertEqual(check_npc_csv_strip({1: zeros}, stock, {1}), [])
        self.assertEqual(len(check_npc_csv_strip({1: {}}, stock, {1})), 2)
        self.assertEqual(len(check_npc_csv_strip({1: {**zeros, "Totem_1": 5175}}, stock, {1})), 1)

    def test_creature_spell_index0(self):
        good = [{"CreatureID": c, "Index": 0, "Spell": s} for c, s in CREATURE_SPELL0.items() if s]
        self.assertEqual(check_creature_spell_index0(good), [])
        wrong = [dict(r, Spell=1) if r["CreatureID"] == 300276 else r for r in good]
        self.assertEqual(len(check_creature_spell_index0(wrong)), 1)
        self.assertEqual(len(check_creature_spell_index0([r for r in good if r["CreatureID"] != 300277])), 1)
        self.assertEqual(len(check_creature_spell_index0(good + [{"CreatureID": 300274, "Index": 0, "Spell": 5}])), 2)
        self.assertEqual(len(check_creature_spell_index0(good + [{"CreatureID": 300278, "Index": 1, "Spell": 5}])), 1)

    def test_passive_pairing(self):
        good = [{"CreatureID": c, "Index": 0, "Spell": s} for c, s in NEW_TOTEM_PASSIVES.items()]
        rows = {s: _row(s, Attributes=0x40) for s in NEW_TOTEM_PASSIVES.values()}
        self.assertEqual(check_new_totem_passive_pairing(good, rows), [])
        self.assertEqual(len(check_new_totem_passive_pairing(good[1:], rows)), 1)
        self.assertEqual(len(check_new_totem_passive_pairing(good, {k: v for k, v in rows.items() if k != 202266})), 1)

    def test_scripts(self):
        bindings = [{"spell_id": s, "ScriptName": n} for s, n in SCRIPTS.items()]
        removals = [{"spell_id": s, "ScriptName": n} for s, n in SCRIPT_REMOVALS]
        self.assertEqual(check_scripts(bindings, removals), [])
        self.assertEqual(len(check_scripts(bindings[1:], removals)), 1)
        self.assertEqual(len(check_scripts([dict(bindings[0], ScriptName="spell_sha_wrong")] + bindings[1:],
                                           removals)), 1)
        self.assertEqual(len(check_scripts(bindings, removals[1:])), 1)

    def test_consts(self):
        consts = [{"name": n, "value": v} for n, v in CONSTS.items()]
        self.assertEqual(check_consts(consts), [])
        self.assertEqual(len(check_consts(consts[1:])), 1)
        self.assertEqual(len(check_consts([dict(consts[0], value=-1)] + consts[1:])), 1)

    def test_var_names_and_header(self):
        spell_vars = {i: v[0] for i, v in SPELL_MAP.items()}
        creature_vars = {i: v[0] for i, v in CREATURE_MAP.items()}
        self.assertEqual(check_var_names(spell_vars, creature_vars), [])
        self.assertEqual(len(check_var_names({**spell_vars, 202260: "x"}, creature_vars)), 1)
        self.assertEqual(len(check_var_names(spell_vars, {})), len(CREATURE_MAP))
        text = "\n".join([f"constexpr uint32 {v[1]} = {i};" for i, v in SPELL_MAP.items()]
                         + [f"constexpr uint32 {v[1]} = {i};" for i, v in CREATURE_MAP.items()]
                         + [f"constexpr int32 {n} = 1;" for n in CONSTS])
        self.assertEqual(check_header(text), [])
        self.assertEqual(len(check_header(text.replace("SPELL_WINDWALK = 202264", "SPELL_WINDWALK = 1"))), 1)
        self.assertEqual(len(check_header("")), len(SPELL_MAP) + len(CREATURE_MAP) + len(CONSTS))

    def test_names_levels(self):
        rows = {i: _row(i, Name_Lang_enUS=v[2], SpellClassSet=11) for i, v in SPELL_MAP.items()}
        rows.update({i: _row(i, SpellLevel=lvl) for i, lvl in TRAINED.items() if i not in rows})
        for i, lvl in TRAINED.items():
            rows[i] = {**rows[i], "SpellLevel": lvl}
        self.assertEqual(check_names_levels(rows), [])
        self.assertEqual(len(check_names_levels({**rows, 202260: dict(rows[202260], Name_Lang_enUS="Nope")})), 1)
        self.assertEqual(len(check_names_levels({**rows, 202261: dict(rows[202261], SpellLevel=21)})), 1)
        self.assertEqual(len(check_names_levels({k: v for k, v in rows.items() if k != 202260})), 1)

    def test_sla_and_trainers(self):
        slas = [{"id": i, "skill_line": a, "spell_id": b, "class_mask": 64, "race_mask": 0, "acquire_method": 0}
                for i, (a, b) in SLAS.items()]
        trainers = [{"TrainerId": 210, "SpellId": s, "ReqLevel": lvl} for s, lvl in TRAINED.items()]
        removals = [{"TrainerId": t, "SpellId": s} for t, s in UNTRAINED]
        self.assertEqual(check_sla_and_trainers(slas, trainers, removals), [])
        self.assertEqual(len(check_sla_and_trainers(slas[1:], trainers, removals)), 1)
        self.assertEqual(len(check_sla_and_trainers([dict(slas[0], class_mask=1)] + slas[1:], trainers, removals)), 1)
        self.assertEqual(len(check_sla_and_trainers([dict(slas[0], skill_line=1)] + slas[1:], trainers, removals)), 1)
        self.assertEqual(len(check_sla_and_trainers(slas, trainers[1:], removals)), 1)
        self.assertEqual(len(check_sla_and_trainers(slas, [dict(trainers[0], ReqLevel=1)] + trainers[1:], removals)), 1)
        self.assertEqual(len(check_sla_and_trainers(slas, trainers, removals[1:])), 1)

    def test_creatures(self):
        creatures = {cid: {"ScriptName": n, "unit_flags": 0x02000002, "faction": 58, "minlevel": 1, "maxlevel": 80}
                     for cid, n in SCRIPT_NAMES.items()}
        for cid in (300275, 300276, 300277):
            creatures[cid] = {"ScriptName": "", "unit_flags": 0, "faction": 58, "minlevel": 1, "maxlevel": 80}
        for cid in (300274, 300278):
            creatures[cid] = {**creatures[cid], "faction": 58}
        self.assertEqual(check_creatures(creatures), [])
        self.assertEqual(len(check_creatures({**creatures, 300274: dict(creatures[300274], ScriptName="x")})), 1)
        self.assertEqual(len(check_creatures({**creatures, 300275: dict(creatures[300275], ScriptName="x")})), 1)
        self.assertEqual(len(check_creatures({**creatures, 300270: dict(creatures[300270], unit_flags=2)})), 1)
        self.assertEqual(len(check_creatures({**creatures, 300277: dict(creatures[300277], faction=14)})), 1)
        self.assertEqual(len(check_creatures({k: v for k, v in creatures.items() if k != 15438})), 1)


if __name__ == "__main__":
    unittest.main()
