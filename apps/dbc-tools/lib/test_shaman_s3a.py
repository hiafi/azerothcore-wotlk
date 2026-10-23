"""
Shaman S3a data gate (shaman-rework S3a-HANDOFF row A5, S3a-WP-BRIEF id map, docs/reworks/shaman-enhancement-rework.md).

Loads the real shaman DSL package and asserts on the BUILT rows (stock base + DSL + raw_overrides via
`build.build_spell_row`; same recipe as test_shaman_sh0b / test_shaman_s1a / test_shaman_s2a), plus the declared talent /
group / tooltip-variable tables. Each check is a pure function over rows or declared entries so the negative fixtures can
prove it fails on a minimal bad input.

Conventions (as in test_shaman_s2a): a built EffectBasePoints is the live value minus one (DieSides <= 1), so "-5000 ms"
flat is stored -5001 or -5000 (lenient). Only the OWN SpellClassMask is held to the FORBIDDEN_* bits; EFFECT masks are
selectors and may name any spell, except where a talent is explicitly told never to select a bit (Molten Fury d0 b30,
Guardian Totems d0 b29).

Run: apps/dbc-tools/.venv/bin/python3 -m pytest apps/dbc-tools/lib/test_shaman_s3a.py -q
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.test_shaman_s1a import check_tooltip_vars, check_visible_buffs  # noqa: E402,F401
from lib.test_shaman_s2a import (  # noqa: E402
    _bits, _cooldown, _duration, _effect_mask, _find_mod, _has_bits, _missing, _mod, _mod_effects, _potencies,
    _talent, _row, check_equipped_item_class, check_forbidden_bits, check_no_cancel, check_no_depends_on,
    check_rank_levels, ATTR0_NO_AURA_CANCEL, ATTR0_PASSIVE, AURA_ADD_FLAT_MODIFIER, AURA_ADD_PCT_MODIFIER,
    SPELLMOD_COOLDOWN, SPELLMOD_DAMAGE,
)
from lib.test_shaman_sh0a import m, spell_mask, _hex, _u32  # noqa: E402
from lib.test_shaman_sh0b import _data as _shaman_data  # noqa: E402

TOOL_ROOT = Path(__file__).resolve().parents[1]
SHAMAN_DIR = TOOL_ROOT / "source" / "classes" / "shaman"
ROGUE_TRIGGERS = TOOL_ROOT / "source" / "classes" / "rogue" / "rogue_trigger_spells.py"
SHAMAN_TRIGGERS = SHAMAN_DIR / "shaman_trigger_spells.py"

ENH_TAB = 263
EFFECT_LEARN_SPELL = 36
AURA_SCHOOL_ABSORB = 69
AURA_MOD_EXPERTISE = 240
SDV_IDS = (1217, 1218, 1219)
# stock rows that legitimately own the magic-GCD haste bits (Stormstrike d1 b4/b24, Shamanistic Rage d1 b17, Lava Lash d2 b2)
# and the stock shields (Lightning Shield 324 d0 b10 / d1 b5)
GCD_HASTE_ROWS = (17364, 30823, 60103, 974, 379, 324)

# family bits (raw dwords; the S3a aliases come from _masks, fallbacks are the brief's values)
D0_B2_MAGMA_PULSE = 0x4
D0_B3_EARTHEN_WALL = 0x8
D0_B15_TREMOR = 0x8000
D0_B28_FLAME_SHOCK = 0x10000000
D0_B29_SUMMON = 0x20000000
D0_B30_SEARING = 0x40000000
D2_B5_EARTHBIND = 0x20
D2_LIVING_EARTH = getattr(m, "LIVING_EARTH", 0x10000)   # d2 b16
D2_GUST = getattr(m, "GUST", 0x40000)                   # d2 b18
D2_ENH_SPELL_HIT = getattr(m, "ENH_SPELL_HIT", 0x20000000)  # d2 b29

# docs/reworks/shaman-enhancement-rework.md section 4 + S3-NOTES section 2: (tier, col) -> (talent id, rank spell ids).
GRID = {
    (0, 0): (610, (16259, 16295, 52456)),         # Enhanced Elements
    (0, 1): (2101, (16043, 16130)),                # Earth's Grasp
    (0, 2): (614, (17485, 17486, 17487)),          # Ancestral Knowledge
    (1, 0): (609, (16258, 16293)),                 # Guardian Totems
    (1, 1): (60295, (202360,)),                    # Elemental Charge
    (1, 2): (605, (16262, 16287)),                 # Improved Ghost Wolf
    (1, 3): (607, (16261, 16290, 51881)),          # Improved Lightning Shield
    (2, 0): (611, (16266, 29079, 29080)),          # Elemental Weapons
    (2, 1): (613, (16255, 16302, 16303)),          # Thundering Strikes
    (2, 2): (617, (43338, 202371, 202372)),        # Shamanistic Focus
    (2, 3): (601, (16254, 16271, 16272)),          # Anticipation
    (3, 0): (1643, (29082, 29084, 29086)),         # Weapon Mastery
    (3, 1): (602, (16256, 16281, 16282)),          # Flurry
    (3, 2): (615, (16252, 16306, 16307)),          # Toughness
    (4, 0): (1647, (29192, 29193)),                # Improved Windfury
    (4, 1): (2249, (60103,)),                      # Lava Lash
    (4, 2): (2083, (51883, 51884, 51885)),         # Mental Dexterity
    (4, 3): (60296, (202361,)),                    # Living Earth
    (5, 0): (1689, (30802, 30808, 30809)),         # Unleashed Rage
    (5, 1): (616, (16268, 202373, 202374)),        # Spirit Weapons
    (5, 2): (60297, (202362, 202363)),             # Volcanic Eruption
    (5, 3): (2263, (63373, 63374, 202375)),        # Frozen Power
    (6, 0): (1692, (30816, 30818, 30819)),         # Dual Wield Specialization
    (6, 1): (60298, (202364,)),                    # Ascendance
    (6, 2): (901, (17364,)),                       # Stormstrike
    (6, 3): (60299, (202365, 202366, 202367)),     # Molten Fury
    (7, 0): (2055, (51525, 51526, 51527)),         # Static Shock
    (7, 1): (60300, (202368, 202369, 202370)),     # Spirit Guard
    (7, 2): (2054, (51521, 51522)),                # Improved Stormstrike
    (8, 0): (1691, (30812, 30813, 30814)),         # Mental Quickness
    (8, 1): (1693, (30823,)),                      # Shamanistic Rage
    (8, 2): (2056, (51523, 51524)),                # Earthen Power
    (9, 1): (2057, (51528, 51529, 51530)),         # Maelstrom Weapon
    (10, 1): (2058, (51533,)),                     # Elemental Spirits
}
EMPTY_CELLS = tuple(sorted({(t, c) for t in range(11) for c in range(4)} - set(GRID)))
GRID_TALENTS, GRID_POINTS = 34, 81

# ids: the brief's id map (spells 202360-202419) and the stock rows S3a rewrites.
S3A_IDS = tuple(range(202360, 202420))
S3A_UNMAPPED = tuple(range(202420, 202440))     # 202413 / 202415 are the cleave strikes, 202414 the Elemental Ascendance speed helper, 202416-202419 the ascend bursts (P2); 202420-202439 unassigned
S3A_SPARE = range(202440, 202520)
REWRITTEN_STOCK = (
    16257, 53817, 8017, 324, 8042, 8349, 8187, 2484, 59566, 63685, 3600, 32175, 32176, 421, 60103, 17364, 30823, 51533,
    2645, 26364, 16256, 16281, 16282, 30802, 30808, 30809, 16268, 30816, 30818, 30819,
)

CHARGE_BUFFS = {202380: 10, 202381: 10, 202382: 10, 202383: 60}   # Fire, Frost, Wind, Earth: stack caps
NO_CANCEL_IDS = (*CHARGE_BUFFS, 202387, 202388, 202389, 202407)   # charge buffs, the three singles, timer (EA is cancellable)
# visible buffs the player sees: never passive
VISIBLE_BUFFS = (*CHARGE_BUFFS, 202387, 202388, 202389, 202390, 202393, 202395, 202396, 202397, 202398, 202399, 202400,
                 202401, 202402, 202407, 53817, 16257)
BURSTS = (202384, 202385, 202386)
NO_FLAME_SHOCK_BIT = (*BURSTS, 202408)         # Bursts + Spirit Flame Shock
MOLTEN_FURY = (202365, 202366, 202367)
GUARDIAN_TOTEMS = (16258, 16293)
MW_BUFF = 53817
MW_CONSUME = (0x1 | 0x2 | 0x80, 0x1000, 0)      # Lightning Bolt d0 b0, Chain Lightning d0 b1, LHW d0 b7, Lava Burst d1 b12
ELEMENTAL_SPIRITS = 51533
LIVING_EARTH = 202361
GUST, GUST_SPLASH = 202391, 202392
SPIRIT_WEAPONS = (16268, 202373, 202374)
UNLEASHED_RAGE = (30802, 30808, 30809)
DWS_RANKS = (30816, 30818, 30819)
MQ_BUFFS = (202399, 202400)
MQ_SPELL_BUFF = 202399
# the direct damaging spells the spell buff boosts (S3a code review m3): d0 LB b0 | CL b1 | Earth b20 | Flame b28 | Frost b31,
# d1 Lava Burst b12, d2 Elemental Blast b20
MQ_SPELL_MASK = (0x90100003, 0x1000, 0x100000)
MQ_GROUP = 1259
CLEAVE_STRIKES = (202413, 202415)               # proc-free clones of the stock strikes 32175 / 32176 (S3a code review M1a)
PRIMARY_STRIKES = (32175, 32176)
ATTR3_NOT_A_PROC = 0x200
ATTR3_SUPPRESS_CASTER_PROCS = 0x10000
ATTR4_SUPPRESS_WEAPON_PROCS = 0x00800000
D2_SS_STRIKES = 0x1400                          # d2 b10 | b12
SPELL_CASTER_DOC_RULE = 1


# ---- row helpers ------------------------------------------------------------------------------------------

def _all_effect_masks(row: dict) -> list[tuple[int, int, int]]:
    return [_effect_mask(row, e) for e in (1, 2, 3)]


def _mod_with_bit(row: dict, misc: int, dword: int, bit: int, aura=None):
    for fx in _mod_effects(row):
        if fx["misc"] == misc and fx["mask"][dword] & bit == bit and (aura is None or fx["aura"] == aura):
            return fx
    return None


def _amount_ok(stored: int, live: int, lenient=True) -> bool:
    return stored + 1 == live or (lenient and stored == live)


# ---- checks (pure) ----------------------------------------------------------------------------------------

def check_grid(talents: list[dict], expected=GRID, empty=EMPTY_CELLS) -> list[str]:
    """Tab 263 holds exactly the documented talents: cell, talent id, rank id list; 34 talents / 81 points."""
    bad, seen = [], {}
    for t in talents:
        if int(t["tab_id"]) != ENH_TAB:
            continue
        cell = (int(t["tier"]), int(t["column"]))
        if cell in seen:
            bad.append(f"talent {t['id']}: cell {cell} also holds talent {seen[cell]}")
        seen[cell] = t["id"]
        want = expected.get(cell)
        if want is None:
            bad.append(f"talent {t['id']}: undocumented cell {cell}")
            continue
        ranks = [int(r) for r in t["rank_spell_ids"]]
        if int(t["id"]) != want[0]:
            bad.append(f"cell {cell}: talent {t['id']}, expected {want[0]}")
        if ranks != list(want[1]):
            bad.append(f"talent {t['id']} at {cell}: ranks {ranks}, expected {list(want[1])}")
    bad += [f"cell {cell}: talent {want[0]} missing" for cell, want in expected.items() if cell not in seen]
    bad += [f"cell {cell}: should be empty, holds talent {seen[cell]}" for cell in empty if cell in seen]
    total = sum(len(t["rank_spell_ids"]) for t in talents if int(t["tab_id"]) == ENH_TAB)
    if (len(seen), total) != (GRID_TALENTS, GRID_POINTS):
        bad.append(f"tab {ENH_TAB} holds {len(seen)} talents / {total} points, expected {GRID_TALENTS} / {GRID_POINTS}")
    return bad


def check_s3a_no_depends_on(talents: list[dict]) -> list[str]:
    """Q19: every row on tab 263 has DependsOn 0."""
    return [f"talent {t['id']}: depends_on {t['depends_on']!r} on tab {ENH_TAB}" for t in talents
            if int(t["tab_id"]) == ENH_TAB and t.get("depends_on")]


def check_s3a_rank_levels(talents: list[dict], levels: dict[int, int]) -> list[str]:
    bad = []
    for t in talents:
        if int(t["tab_id"]) != ENH_TAB:
            continue
        chain = [levels.get(int(r), 0) for r in t["rank_spell_ids"]]
        if chain != sorted(chain) or any(lv > 80 for lv in chain):
            bad.append(f"talent {t['id']}: rank levels {chain} are not ascending within 1..80")
    return bad


def check_id_map(declared, unmapped=S3A_UNMAPPED) -> list[str]:
    return [f"{i}: declared but not in the brief's S3a id map" for i in unmapped if i in declared]


def check_molten_fury(rows: dict, ids=MOLTEN_FURY) -> list[str]:
    """Searing Totem shares d0 b30: no Molten Fury effect mask (nor own mask) may hold it; Magma pulse d0 b2 is reached."""
    bad = _missing(rows, *ids)
    for i in ids:
        row = rows.get(i)
        if row is None:
            continue
        for label, mask in (("own", spell_mask(row)), *((f"effect {e}", _effect_mask(row, e)) for e in (1, 2, 3))):
            if mask[0] & D0_B30_SEARING:
                bad.append(f"{i}: {label} mask {_hex(mask)} holds d0 b30 (Searing Totem's bolt)")
        if not _mod_with_bit(row, SPELLMOD_DAMAGE, 0, D0_B2_MAGMA_PULSE):
            bad.append(f"{i}: no SPELLMOD_DAMAGE effect selecting the Magma pulse (d0 b2)")
    return bad


def check_guardian_totems(rows: dict, ids=GUARDIAN_TOTEMS) -> list[str]:
    """Never d0 b29 (the summon-family bit reaches the Earth Elemental); cooldown cuts on Earth Wall / Earthbind / Tremor."""
    bad = _missing(rows, *ids)
    for i, wall, other in zip(ids, (2500, 5000), (5000, 10000)):
        row = rows.get(i)
        if row is None:
            continue
        for label, mask in (("own", spell_mask(row)), *((f"effect {e}", _effect_mask(row, e)) for e in (1, 2, 3))):
            if mask[0] & D0_B29_SUMMON:
                bad.append(f"{i}: {label} mask {_hex(mask)} holds d0 b29 (reaches the Earth Elemental)")
        for label, dword, bit, want in (("Earth Wall d0 b3", 0, D0_B3_EARTHEN_WALL, wall),
                                        ("Earthbind d2 b5", 2, D2_B5_EARTHBIND, other),
                                        ("Tremor d0 b15", 0, D0_B15_TREMOR, other)):
            fx = _mod_with_bit(row, SPELLMOD_COOLDOWN, dword, bit, aura=AURA_ADD_FLAT_MODIFIER)
            if fx is None:
                bad.append(f"{i}: no flat SPELLMOD_COOLDOWN on {label}")
            elif not (_amount_ok(fx["bp"], -want) or abs(fx["bp"]) in (want, want - 1, want + 1)):
                bad.append(f"{i}: cooldown cut on {label} is {fx['bp']}, expected -{want}")
        if not _mod_with_bit(row, SPELLMOD_DAMAGE, 2, D2_LIVING_EARTH) and not any(
                fx["mask"][2] & D2_LIVING_EARTH for fx in _mod_effects(row)):
            bad.append(f"{i}: no SpellMod on Living Earth (d2 b16)")
    return bad


def check_maelstrom_consume(rows: dict) -> list[str]:
    """53817 consume mask = Lightning Bolt, Chain Lightning, Lesser Healing Wave, Lava Burst only."""
    row = rows.get(MW_BUFF)
    if row is None:
        return [f"{MW_BUFF}: not built"]
    union = [0, 0, 0]
    for fx in _mod_effects(row):
        for n in range(3):
            union[n] |= fx["mask"][n]
    if tuple(union) != MW_CONSUME:
        return [f"{MW_BUFF}: spell-mod mask union {_hex(tuple(union))}, expected {_hex(MW_CONSUME)} (LB/CL/LHW/Lava Burst)"]
    return []


def check_elemental_spirits(rows: dict, entries: dict) -> list[str]:
    row, entry = rows.get(ELEMENTAL_SPIRITS), entries.get(ELEMENTAL_SPIRITS)
    if row is None:
        return [f"{ELEMENTAL_SPIRITS}: not built"]
    bad = []
    if _duration(entry) != 20000:
        bad.append(f"{ELEMENTAL_SPIRITS}: duration_ms {_duration(entry)}, expected 20000")
    if max(int(row.get("RecoveryTime") or 0), int((entry or {}).get("cooldown_ms") or 0)) != 120000:
        bad.append(f"{ELEMENTAL_SPIRITS}: RecoveryTime {row.get('RecoveryTime')}, expected 120000")
    return bad


def check_living_earth(rows: dict, entries: dict) -> list[str]:
    row, entry = rows.get(LIVING_EARTH), entries.get(LIVING_EARTH)
    if row is None:
        return [f"{LIVING_EARTH}: not built"]
    bad = []
    if int(row.get("CasterAuraSpell") or 0) != 8017:
        bad.append(f"{LIVING_EARTH}: CasterAuraSpell {row.get('CasterAuraSpell')}, expected 8017 (Rockbiter)")
    if not spell_mask(row)[2] & D2_LIVING_EARTH:
        bad.append(f"{LIVING_EARTH}: own mask {_hex(spell_mask(row))} lacks d2 b16")
    if _cooldown(row, entry) != 10000:
        bad.append(f"{LIVING_EARTH}: cooldown {_cooldown(row, entry)}, expected 10000")
    if AURA_SCHOOL_ABSORB not in {int(row.get(f"EffectAura_{e}") or 0) for e in (1, 2, 3)}:
        bad.append(f"{LIVING_EARTH}: no absorb effect (aura 69)")
    return bad


def check_gust(rows: dict, ids=(GUST, GUST_SPLASH)) -> list[str]:
    bad = _missing(rows, GUST)
    for i in ids:
        row = rows.get(i)
        if row is not None and not spell_mask(row)[2] & D2_GUST:
            bad.append(f"{i}: own mask {_hex(spell_mask(row))} lacks Gust d2 b18")
    return bad


def check_cleave_strikes(rows: dict, ids=CLEAVE_STRIKES, primaries=PRIMARY_STRIKES) -> list[str]:
    """M1a: the cleave strikes roll nothing (no NOT_A_PROC, SUPPRESS_CASTER_PROCS, SUPPRESS_WEAPON_PROCS) but keep the Stormstrike
    strike family bits d2 b10 / b12; the primary strikes keep NOT_A_PROC (that is how they feed Flametongue and Windfury)."""
    bad = _missing(rows, *ids)
    for i in ids:
        row = rows.get(i)
        if row is None:
            continue
        ex3, ex4 = _u32(row.get("AttributesEx3")), _u32(row.get("AttributesEx4"))
        if ex3 & ATTR3_NOT_A_PROC:
            bad.append(f"{i}: AttributesEx3 {ex3:#x} still has NOT_A_PROC (0x200): the cleave hit would roll every proc")
        if not ex3 & ATTR3_SUPPRESS_CASTER_PROCS:
            bad.append(f"{i}: AttributesEx3 {ex3:#x} lacks SUPPRESS_CASTER_PROCS (0x10000)")
        if not ex4 & ATTR4_SUPPRESS_WEAPON_PROCS:
            bad.append(f"{i}: AttributesEx4 {ex4:#x} lacks SUPPRESS_WEAPON_PROCS (0x00800000)")
        if spell_mask(row)[2] & D2_SS_STRIKES != D2_SS_STRIKES:
            bad.append(f"{i}: own mask {_hex(spell_mask(row))} lacks the Stormstrike strike bits d2 b10 | b12")
        if int(row.get("SpellClassSet") or 0) != 11:
            bad.append(f"{i}: SpellClassSet {row.get('SpellClassSet')}, expected 11")
    for i in primaries:
        row = rows.get(i)
        if row is not None and not _u32(row.get("AttributesEx3")) & ATTR3_NOT_A_PROC:
            bad.append(f"{i}: the primary strike lost NOT_A_PROC (Flametongue / Windfury would stop reaching Stormstrike)")
    return bad


def check_gust_no_weapon_procs(rows: dict, gust=GUST, splash=GUST_SPLASH) -> list[str]:
    """M1b: both Gust rows suppress weapon-enchant / item procs; only the splash also suppresses the caster's procs (the Gust must
    keep reaching Maelstrom Weapon)."""
    bad = _missing(rows, gust, splash)
    for i in (gust, splash):
        row = rows.get(i)
        if row is not None and not _u32(row.get("AttributesEx4")) & ATTR4_SUPPRESS_WEAPON_PROCS:
            bad.append(f"{i}: AttributesEx4 {_u32(row.get('AttributesEx4')):#x} lacks SUPPRESS_WEAPON_PROCS (0x00800000)")
    if gust in rows and _u32(rows[gust].get("AttributesEx3")) & ATTR3_SUPPRESS_CASTER_PROCS:
        bad.append(f"{gust}: the Gust has SUPPRESS_CASTER_PROCS (it could never reach Maelstrom Weapon)")
    if splash in rows and not _u32(rows[splash].get("AttributesEx3")) & ATTR3_SUPPRESS_CASTER_PROCS:
        bad.append(f"{splash}: the Gust splash lacks SUPPRESS_CASTER_PROCS (0x10000)")
    return bad


def check_mq_spell_buff(rows: dict, spell_id=MQ_SPELL_BUFF, mask=MQ_SPELL_MASK) -> list[str]:
    """m3: the spell buff is a +10% SPELLMOD_DAMAGE (direct damage only) on exactly the shocks, Lightning Bolt, Chain Lightning,
    Lava Burst and Elemental Blast; no all-schools aura 79 (it lifted Lava Lash, orbs, imbue attacks, Bursts and totems)."""
    row = rows.get(spell_id)
    if row is None:
        return [f"{spell_id}: not built"]
    bad = []
    if int(row.get("SpellClassSet") or 0) != 11:
        bad.append(f"{spell_id}: SpellClassSet {row.get('SpellClassSet')}, expected 11 (a SpellMod of another family never matches)")
    for e in (1, 2, 3):
        if int(row.get(f"EffectAura_{e}") or 0) == 79:
            bad.append(f"{spell_id}: effect {e} is aura 79 (MOD_DAMAGE_PERCENT_DONE): it raises every spell of the school")
    mods = [fx for fx in _mod_effects(row) if fx["aura"] == AURA_ADD_PCT_MODIFIER and fx["misc"] == SPELLMOD_DAMAGE]
    if len(mods) != 1:
        return bad + [f"{spell_id}: {len(mods)} pct SPELLMOD_DAMAGE effects, expected 1"]
    fx = mods[0]
    if fx["mask"] != tuple(mask):
        bad.append(f"{spell_id}: spell mod mask {_hex(fx['mask'])}, expected {_hex(tuple(mask))}")
    if not _amount_ok(fx["bp"], 10, lenient=False):
        bad.append(f"{spell_id}: spell mod base points {fx['bp']}, expected 9 (live +10%)")
    lava_lash = (0, 0, 0x4)
    if any(fx["mask"][n] & lava_lash[n] for n in range(3)):
        bad.append(f"{spell_id}: spell mod reaches Lava Lash (d2 b2), which grants it")
    return bad


def check_no_flame_shock_bit(rows: dict, ids=NO_FLAME_SHOCK_BIT) -> list[str]:
    """Bursts and Spirit Flame Shock must not carry d0 b28: Lava Burst auto-crit reads the own Flame Shock periodic."""
    bad = []
    for i in ids:
        row = rows.get(i)
        if row is not None and spell_mask(row)[0] & D0_B28_FLAME_SHOCK:
            bad.append(f"{i}: own mask {_hex(spell_mask(row))} holds d0 b28 (Flame Shock)")
    return bad


def check_burst_bits(rows: dict) -> list[str]:
    """Flame / Storm Burst carry d2 b29 (Improved Stormstrike aura 271 mask); Wind Burst does not need it."""
    return [f"{i}: own mask {_hex(spell_mask(rows[i]))} lacks d2 b29 (ENH_SPELL_HIT)" for i in (202384, 202385)
            if i in rows and not spell_mask(rows[i])[2] & D2_ENH_SPELL_HIT]


def check_charge_buffs(rows: dict, caps=CHARGE_BUFFS) -> list[str]:
    bad = _missing(rows, *caps)
    for i, cap in caps.items():
        row = rows.get(i)
        if row is None:
            continue
        stacks = int(row.get("CumulativeAura") or 0)
        if stacks != cap:
            bad.append(f"{i}: CumulativeAura {stacks}, expected {cap}")
        if not _u32(row.get("Attributes")) & ATTR0_NO_AURA_CANCEL:
            bad.append(f"{i}: lacks SPELL_ATTR0_NO_AURA_CANCEL")
    return bad


def check_visible_not_passive(rows: dict, ids=VISIBLE_BUFFS) -> list[str]:
    return [f"{i}: visible buff is passive (Attributes {_u32(rows[i].get('Attributes')):#x})" for i in ids
            if i in rows and _u32(rows[i].get("Attributes")) & ATTR0_PASSIVE]


def check_group_1259(groups: list[dict], rules: list[dict], members=MQ_BUFFS, gid=MQ_GROUP) -> list[str]:
    bad = []
    got = {int(g["spell_id"]) for g in groups if int(g["id"]) == gid}
    if got != set(members):
        bad.append(f"group {gid}: members {sorted(got)}, expected {sorted(members)}")
    declared = [r for r in rules if int(r["group_id"]) == gid]
    if [int(r["stack_rule"]) for r in declared] != [SPELL_CASTER_DOC_RULE]:
        bad.append(f"group {gid}: stack rules {[r['stack_rule'] for r in declared]}, expected [1]")
    return bad


def check_dws_home(rogue_text: str, shaman_text: str, ids=DWS_RANKS) -> list[str]:
    bad = []
    for i in ids:
        pat = rf"^\s+id={i},"
        if re.search(pat, rogue_text, re.M):
            bad.append(f"{i}: still declared in the rogue file")
        if not re.search(pat, shaman_text, re.M):
            bad.append(f"{i}: not declared in shaman_trigger_spells.py")
    return bad


def check_spirit_weapons(entries: dict, rows: dict, ids=SPIRIT_WEAPONS) -> list[str]:
    """No LEARN_SPELL effect (Parry 18848 / threat 36591 gone)."""
    bad = []
    for i in ids:
        row = rows.get(i)
        if row is None:
            continue
        for e in (1, 2, 3):
            if int(row.get(f"Effect_{e}") or 0) == EFFECT_LEARN_SPELL:
                bad.append(f"{i}: effect {e} is LEARN_SPELL (trigger {row.get(f'EffectTriggerSpell_{e}')})")
    return bad


def check_unleashed_rage(rows: dict, ids=UNLEASHED_RAGE) -> list[str]:
    """The stock expertise effect (aura 240) is gone."""
    bad = []
    for i in ids:
        row = rows.get(i)
        if row is None:
            continue
        for e in (1, 2, 3):
            if int(row.get(f"EffectAura_{e}") or 0) == AURA_MOD_EXPERTISE:
                bad.append(f"{i}: effect {e} is still MOD_EXPERTISE (aura 240)")
    return bad


LAVA_LASH = 60103
LAVA_LASH_WEAPON_PERCENT = 110   # off-hand weapon damage % [tune], stock 100, 250 on 2026-10-22 then trimmed to 110 (S3-ENH-TRIM-DIAG option 3)
EFFECT_WEAPON_PERCENT_DAMAGE = 31


def check_lava_lash(rows: dict, spell_id=LAVA_LASH, percent=LAVA_LASH_WEAPON_PERCENT) -> list[str]:
    """Lava Lash eff0 is WEAPON_PERCENT_DAMAGE of `percent`% (built base points = percent - 1, die sides <= 1), and the spell text
    names the same number, so the tooltip and the data cannot drift apart."""
    row = rows.get(spell_id)
    if row is None:
        return [f"{spell_id}: not built"]
    bad = []
    if int(row.get("Effect_1") or 0) != EFFECT_WEAPON_PERCENT_DAMAGE:
        bad.append(f"{spell_id}: effect 1 is {row.get('Effect_1')}, expected WEAPON_PERCENT_DAMAGE (31)")
    if int(row.get("EffectBasePoints_1") or 0) not in (percent - 1, percent) or int(row.get("EffectDieSides_1") or 0) > 1:
        bad.append(f"{spell_id}: EffectBasePoints_1 {row.get('EffectBasePoints_1')} (die sides {row.get('EffectDieSides_1')}), "
                   f"expected {percent}% off-hand weapon damage (stored {percent - 1})")
    text = str(row.get("Description_Lang_enUS") or "")
    if f"{percent}% off-hand weapon damage" not in text:
        bad.append(f"{spell_id}: tooltip does not say '{percent}% off-hand weapon damage': {text!r}")
    return bad


MAELSTROM_RANKS = {51528: 7, 51529: 14, 51530: 21}   # chance per rank [tune], trimmed from 10/20/30 on 2026-10-22


def check_maelstrom_chance(rows: dict, ranks=None) -> list[str]:
    """Each Maelstrom Weapon rank's ProcChance (spell_proc -51528 has Chance 0, so the rank row is the chance) and its tooltip
    name the trimmed 7 / 14 / 21%."""
    bad = []
    for sid, pct in (ranks or MAELSTROM_RANKS).items():
        row = rows.get(sid)
        if row is None:
            bad.append(f"{sid}: not built")
            continue
        if int(row.get("ProcChance") or 0) != pct:
            bad.append(f"{sid}: ProcChance {row.get('ProcChance')}, expected {pct}")
        if f"a {pct}% chance" not in str(row.get("Description_Lang_enUS") or ""):
            bad.append(f"{sid}: tooltip does not say 'a {pct}% chance'")
    return bad


def check_dws_proc(procs: list[dict]) -> list[str]:
    """spell_proc -30816: off-hand autos, Chance 20, no family, no phase / type masks (0-verify settled shape)."""
    rows = [p for p in procs if int(p["SpellId"]) == -30816]
    if not rows:
        return []  # not declared yet: the rank-key row is optional until A2 lands it
    p = rows[0]
    bad = []
    if int(p["ProcFlags"]) != 0x00800000:
        bad.append(f"-30816: ProcFlags {int(p['ProcFlags']):#x}, expected 0x800000")
    if float(p["Chance"]) != 20:
        bad.append(f"-30816: Chance {p['Chance']}, expected 20")
    if int(p["SpellFamilyName"]) or any(int(p[f"SpellFamilyMask{n}"]) for n in range(3)):
        bad.append("-30816: carries a family filter")
    if int(p["SpellPhaseMask"]) or int(p["SpellTypeMask"]):
        bad.append("-30816: SpellPhaseMask / SpellTypeMask must be 0")
    return bad


# ---- playtest fix pass P2 (2026-10-22): no Ascendance transform, a cosmetic burst at the shaman's feet ------------

AURA_TRANSFORM = 56
EFFECT_DUMMY = 3
ASCENDANCES = (202387, 202388, 202389, 202390, 202393)
ASCEND_BURSTS = {202416: 963, 202417: 17, 202418: 11302, 202419: 5719}   # Fire Nova, Frost Nova, Thunderstorm, War Stomp


def check_no_ascendance_transform(rows: dict, ids=ASCENDANCES) -> list[str]:
    """The Ascendances keep their gameplay effects but never change the model; every buff still has an effect (Earthen's DUMMY)."""
    bad = _missing(rows, *ids)
    for i in ids:
        row = rows.get(i)
        if row is None:
            continue
        if not any(int(row.get(f"Effect_{n}") or 0) for n in (1, 2, 3)):
            bad.append(f"{i}: no effect at all")
        for n in (1, 2, 3):
            if int(row.get(f"EffectApplyAuraName_{n}") or 0) == AURA_TRANSFORM:
                bad.append(f"{i}: effect {n} is still SPELL_AURA_TRANSFORM")
    return bad


def check_ascend_bursts(rows: dict, script_ids=(), bursts=ASCEND_BURSTS) -> list[str]:
    """Cosmetic only: one self-targeted DUMMY, the stock visual, no aura, no damage, no family, procs suppressed, no script."""
    bad = _missing(rows, *bursts)
    for i, visual in bursts.items():
        row = rows.get(i)
        if row is None:
            continue
        effects = [int(row.get(f"Effect_{n}") or 0) for n in (1, 2, 3)]
        if effects != [EFFECT_DUMMY, 0, 0]:
            bad.append(f"{i}: effects {effects}, expected a single DUMMY")
        if int(row.get("EffectApplyAuraName_1") or 0):
            bad.append(f"{i}: applies an aura")
        if int(row.get("ImplicitTargetA_1") or 0) != 1:
            bad.append(f"{i}: effect 1 target {row.get('ImplicitTargetA_1')}, expected 1 (the caster)")
        if int(row.get("SpellVisualID_1") or 0) != visual:
            bad.append(f"{i}: SpellVisualID_1 {row.get('SpellVisualID_1')}, expected the stock {visual}")
        if int(row.get("SpellClassSet") or 0):
            bad.append(f"{i}: SpellClassSet {row.get('SpellClassSet')}, expected 0 (no shaman SpellMod reaches it)")
        if not int(row.get("AttributesEx3") or 0) & ATTR3_SUPPRESS_CASTER_PROCS:
            bad.append(f"{i}: AttributesEx3 lacks SUPPRESS_CASTER_PROCS")
        if int(row.get("Effect_1") or 0) and int(row.get("EffectBasePoints_1") or 0) > 0:
            bad.append(f"{i}: carries a positive base value")
        if i in script_ids:
            bad.append(f"{i}: has a spell_script_names binding (a cosmetic burst runs no script)")
    return bad


# ---- real data --------------------------------------------------------------------------------------------

_S3A: dict = {}
_LOAD_ERROR: list = []


def _data():
    if _LOAD_ERROR:
        raise _LOAD_ERROR[0]
    try:
        d = _shaman_data()
    except Exception as exc:  # noqa: BLE001
        _LOAD_ERROR.append(exc)
        raise
    if not _S3A:
        levels = {}
        for t in d["package"].talents:
            for r in t["rank_spell_ids"]:
                row = d["rows_by_id"].get(r) or d["stock"].get(r) or {}
                levels[int(r)] = int(row.get("SpellLevel") or 0)
        _S3A.update(levels=levels)
    return {**d, **_S3A}


def _enh_ranks(d) -> list[int]:
    return [int(r) for t in d["package"].talents if int(t["tab_id"]) == ENH_TAB for r in t["rank_spell_ids"]]


class ShamanS3aDataTest(unittest.TestCase):
    def assertClean(self, problems: list[str]):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_maelstrom_chance(self):
        good = {sid: _row(sid, ProcChance=p, Description_Lang_enUS=f"you have a {p}% chance to reduce")
                for sid, p in MAELSTROM_RANKS.items()}
        self.assertEqual(check_maelstrom_chance(good), [])
        self.assertEqual(len(check_maelstrom_chance({**good, 51528: {**good[51528], "ProcChance": 10}})), 1)
        self.assertEqual(len(check_maelstrom_chance({**good, 51530: {**good[51530], "Description_Lang_enUS": "30% chance"}})), 1)
        self.assertEqual(len(check_maelstrom_chance({})), 3)

    def test_id_map(self):
        self.assertClean(check_id_map(set(_data()["rows_by_id"])))

    def test_grid(self):
        self.assertClean(check_grid(_data()["package"].talents))

    def test_rank_levels(self):
        d = _data()
        self.assertClean(check_s3a_rank_levels(d["package"].talents, d["levels"]))

    def test_no_depends_on(self):
        self.assertClean(check_s3a_no_depends_on(_data()["package"].talents))

    def test_equipped_item_class(self):
        d = _data()
        # Stormstrike / Lava Lash keep the stock weapon requirement (class 2 + subclass masks), not the unset-0 hazard.
        ids = sorted((set(S3A_IDS) | set(_enh_ranks(d)) | set(REWRITTEN_STOCK) | set(S3A_SPARE)) - {17364, 60103})
        self.assertClean(check_equipped_item_class(d["rows_by_id"], ids))

    def test_no_forbidden_bits(self):
        d = _data()
        ids = sorted(set(S3A_IDS) | set(_enh_ranks(d)))
        self.assertClean(check_forbidden_bits(d["rows_by_id"], ids, allow=GCD_HASTE_ROWS))

    def test_molten_fury(self):
        self.assertClean(check_molten_fury(_data()["rows_by_id"]))

    def test_guardian_totems(self):
        self.assertClean(check_guardian_totems(_data()["rows_by_id"]))

    def test_maelstrom_consume_mask(self):
        self.assertClean(check_maelstrom_consume(_data()["rows_by_id"]))

    def test_elemental_spirits(self):
        d = _data()
        self.assertClean(check_elemental_spirits(d["rows_by_id"], d["entries_by_id"]))

    def test_living_earth(self):
        d = _data()
        self.assertClean(check_living_earth(d["rows_by_id"], d["entries_by_id"]))

    def test_gust(self):
        self.assertClean(check_gust(_data()["rows_by_id"]))

    def test_cleave_strikes_proc_nothing(self):
        self.assertClean(check_cleave_strikes(_data()["rows_by_id"]))

    def test_gust_weapon_procs_suppressed(self):
        self.assertClean(check_gust_no_weapon_procs(_data()["rows_by_id"]))

    def test_mental_quickness_spell_buff_scope(self):
        self.assertClean(check_mq_spell_buff(_data()["rows_by_id"]))

    def test_thundering_strikes_script_bound(self):
        names = {(int(r["spell_id"]), r["ScriptName"]) for r in _data()["package"].spell_script_names}
        self.assertIn((16303, "spell_sha_enh_thundering_strikes"), names)

    def test_bursts_and_spirit_flame_shock_have_no_flame_shock_bit(self):
        self.assertClean(check_no_flame_shock_bit(_data()["rows_by_id"]))

    def test_burst_bits(self):
        self.assertClean(check_burst_bits(_data()["rows_by_id"]))

    def test_charge_buffs(self):
        self.assertClean(check_charge_buffs(_data()["rows_by_id"]))

    def test_no_cancel(self):
        self.assertClean(check_no_cancel(_data()["rows_by_id"], NO_CANCEL_IDS))

    def test_visible_buffs_not_passive(self):
        self.assertClean(check_visible_not_passive(_data()["rows_by_id"]))

    def test_visible_buffs_have_number_free_aura_text(self):
        d = _data()
        self.assertClean(check_visible_buffs(d["rows_by_id"], sorted(set(S3A_IDS) | {MW_BUFF, 16257})))

    def test_tooltip_variable_names(self):
        self.assertClean(check_tooltip_vars(_data()["package"].tooltip_vars, ids=SDV_IDS))

    def test_group_1259(self):
        p = _data()["package"]
        self.assertClean(check_group_1259(p.spell_groups, p.spell_group_rules))

    def test_dws_rows_live_in_the_shaman_file_only(self):
        self.assertClean(check_dws_home(ROGUE_TRIGGERS.read_text(), SHAMAN_TRIGGERS.read_text()))

    def test_dws_proc(self):
        self.assertClean(check_dws_proc(_data()["package"].spell_procs))

    def test_spirit_weapons_no_learn_spell(self):
        d = _data()
        self.assertClean(check_spirit_weapons(d["entries_by_id"], d["rows_by_id"]))

    def test_unleashed_rage_no_expertise(self):
        self.assertClean(check_unleashed_rage(_data()["rows_by_id"]))

    def test_lava_lash_110_percent(self):
        self.assertClean(check_lava_lash(_data()["rows_by_id"]))

    def test_maelstrom_chance_7_14_21(self):
        self.assertClean(check_maelstrom_chance(_data()["rows_by_id"]))

    def test_ascendances_have_no_transform(self):
        self.assertClean(check_no_ascendance_transform(_data()["rows_by_id"]))

    def test_ascend_bursts_are_cosmetic(self):
        d = _data()
        scripted = {int(r["spell_id"]) for r in d["package"].spell_script_names}
        self.assertClean(check_ascend_bursts(d["rows_by_id"], script_ids=scripted))


# ---- negative fixtures ------------------------------------------------------------------------------------

def _good_grid():
    return [_talent(tid, t, c, ranks, tab=ENH_TAB) for (t, c), (tid, ranks) in GRID.items()]


class ShamanS3aNegativeTest(unittest.TestCase):
    def test_grid_counts(self):
        self.assertEqual((len(GRID), sum(len(r) for _t, r in GRID.values()), len(EMPTY_CELLS)), (34, 81, 10))

    def test_grid(self):
        good = _good_grid()
        self.assertEqual(check_grid(good), [])
        self.assertTrue(check_grid(good[1:]))                                               # talent missing
        moved = [dict(t) for t in good]
        moved[0]["tier"], moved[0]["column"] = EMPTY_CELLS[0]
        self.assertTrue(check_grid(moved))                                                  # empty cell filled
        wrong = [dict(t) for t in good]
        wrong[1]["rank_spell_ids"] = [16043]
        self.assertTrue(check_grid(wrong))                                                  # rank list / points
        other_tab = [dict(t) for t in good]
        other_tab[0]["tab_id"] = 261
        self.assertTrue(check_grid(other_tab))
        self.assertTrue(check_grid(good + [_talent(9999, *EMPTY_CELLS[1], (1,), tab=ENH_TAB)]))
        self.assertTrue(check_grid(good + [_talent(9998, 0, 0, (1,), tab=ENH_TAB)]))         # duplicate cell

    def test_no_depends_on(self):
        good = _good_grid()
        self.assertEqual(check_s3a_no_depends_on(good), [])
        bad = [dict(t) for t in good]
        bad[3]["depends_on"] = 602
        self.assertEqual(len(check_s3a_no_depends_on(bad)), 1)
        bad[3]["tab_id"] = 262
        self.assertEqual(check_s3a_no_depends_on(bad), [])

    def test_rank_levels(self):
        good = _good_grid()
        self.assertEqual(check_s3a_rank_levels(good, {16259: 10, 16295: 20, 52456: 30}), [])
        self.assertTrue(check_s3a_rank_levels(good, {16259: 30, 16295: 20, 52456: 10}))
        self.assertTrue(check_s3a_rank_levels(good, {16259: 10, 16295: 20, 52456: 81}))

    def test_equipped_item_class(self):
        self.assertEqual(check_equipped_item_class({1: _row(1, EquippedItemClass=-1)}, [1]), [])
        self.assertEqual(len(check_equipped_item_class({1: _row(1, EquippedItemClass=2)}, [1])), 1)
        self.assertEqual(len(check_equipped_item_class({1: _row(1)}, [1])), 1)

    def test_forbidden_bits(self):
        self.assertEqual(check_forbidden_bits({202384: _row(202384, SpellClassMask_3=D2_ENH_SPELL_HIT)}, [202384]), [])
        self.assertEqual(len(check_forbidden_bits({202384: _row(202384, SpellClassMask_1=D0_B28_FLAME_SHOCK)}, [202384])), 1)
        self.assertEqual(len(check_forbidden_bits({202384: _row(202384, SpellClassMask_2=m.FORBIDDEN_D1_B12)}, [202384])), 1)

    def test_molten_fury(self):
        good = {i: _row(i, **_mod(1, 108, 0, 9, (D0_B2_MAGMA_PULSE, 0, 0))) for i in MOLTEN_FURY}
        self.assertEqual(check_molten_fury(good), [])
        for mask in ((D0_B2_MAGMA_PULSE | D0_B30_SEARING, 0, 0),):
            bad = dict(good)
            bad[202366] = _row(202366, **_mod(1, 108, 0, 9, mask))
            self.assertEqual(len(check_molten_fury(bad)), 1)
        bad = dict(good)
        bad[202365] = _row(202365, SpellClassMask_1=D0_B30_SEARING, **_mod(1, 108, 0, 9, (D0_B2_MAGMA_PULSE, 0, 0)))
        self.assertEqual(len(check_molten_fury(bad)), 1)
        bad = dict(good)
        bad[202367] = _row(202367, **_mod(1, 108, 0, 9, (D0_B30_SEARING >> 1, 0, 0)))   # misses d0 b2 entirely
        self.assertTrue(check_molten_fury(bad))
        self.assertTrue(check_molten_fury({k: v for k, v in good.items() if k != 202365}))

    def test_guardian_totems(self):
        def rank(i, wall, other, extra=(0, 0, 0)):
            cols = {}
            cols.update(_mod(1, 107, 11, -wall, (D0_B3_EARTHEN_WALL, 0, 0)))
            cols.update(_mod(2, 107, 11, -other, (D0_B15_TREMOR | extra[0], 0, D2_B5_EARTHBIND)))
            cols.update(_mod(3, 108, 0, 9, (0, 0, D2_LIVING_EARTH)))
            return _row(i, **cols)
        good = {16258: rank(16258, 2500, 5000), 16293: rank(16293, 5000, 10000)}
        self.assertEqual(check_guardian_totems(good), [])
        bad = {**good, 16293: rank(16293, 5000, 10000, (D0_B29_SUMMON, 0, 0))}
        self.assertEqual(len(check_guardian_totems(bad)), 1)
        self.assertTrue(check_guardian_totems({16258: good[16258]}))                         # missing rank
        wrong = {**good, 16258: rank(16258, 2500, 7000)}
        self.assertTrue(check_guardian_totems(wrong))
        no_le = {**good, 16258: _row(16258, **_mod(1, 107, 11, -2500, (D0_B3_EARTHEN_WALL, 0, 0)))}
        self.assertTrue(check_guardian_totems(no_le))

    def test_maelstrom_consume(self):
        good = {MW_BUFF: _row(MW_BUFF, **_mod(1, 108, 10, -100, (0x83, 0x1000, 0)))}
        self.assertEqual(check_maelstrom_consume(good), [])
        for mask in ((0x83 | 0x40, 0x1000, 0), (0x83, 0, 0), (0x83 | 0x100, 0x1000, 0), (0x83, 0x1000, 0x1)):
            self.assertEqual(len(check_maelstrom_consume({MW_BUFF: _row(MW_BUFF, **_mod(1, 108, 10, -100, mask))})), 1)
        split = {MW_BUFF: _row(MW_BUFF, **_mod(1, 108, 10, -100, (0x3, 0, 0)), **_mod(2, 108, 10, -100, (0x80, 0x1000, 0)))}
        self.assertEqual(check_maelstrom_consume(split), [])
        self.assertTrue(check_maelstrom_consume({}))

    def test_elemental_spirits(self):
        ok = {ELEMENTAL_SPIRITS: _row(ELEMENTAL_SPIRITS, RecoveryTime=120000)}
        self.assertEqual(check_elemental_spirits(ok, {ELEMENTAL_SPIRITS: {"duration_ms": 20000}}), [])
        self.assertEqual(len(check_elemental_spirits(ok, {ELEMENTAL_SPIRITS: {"duration_ms": 30000}})), 1)
        slow = {ELEMENTAL_SPIRITS: _row(ELEMENTAL_SPIRITS, RecoveryTime=180000)}
        self.assertEqual(len(check_elemental_spirits(slow, {ELEMENTAL_SPIRITS: {"duration_ms": 20000}})), 1)
        self.assertTrue(check_elemental_spirits({}, {}))

    def test_living_earth(self):
        good = {LIVING_EARTH: _row(LIVING_EARTH, CasterAuraSpell=8017, SpellClassMask_3=D2_LIVING_EARTH, RecoveryTime=10000,
                                   EffectAura_1=AURA_SCHOOL_ABSORB)}
        self.assertEqual(check_living_earth(good, {}), [])
        for col, val in (("CasterAuraSpell", 0), ("SpellClassMask_3", 0), ("RecoveryTime", 6000), ("EffectAura_1", 6)):
            bad = {LIVING_EARTH: _row(LIVING_EARTH, **{**good[LIVING_EARTH], col: val})}
            self.assertEqual(len(check_living_earth(bad, {})), 1, col)
        self.assertTrue(check_living_earth({}, {}))

    def test_gust(self):
        good = {GUST: _row(GUST, SpellClassMask_3=D2_GUST), GUST_SPLASH: _row(GUST_SPLASH, SpellClassMask_3=D2_GUST)}
        self.assertEqual(check_gust(good), [])
        self.assertEqual(len(check_gust({**good, GUST_SPLASH: _row(GUST_SPLASH)})), 1)
        self.assertEqual(len(check_gust({GUST: _row(GUST, SpellClassMask_3=D2_LIVING_EARTH)})), 1)
        self.assertTrue(check_gust({}))

    def test_cleave_strikes(self):
        def strike(i, **cols):
            base = {"AttributesEx3": 0x40400 | ATTR3_SUPPRESS_CASTER_PROCS, "AttributesEx4": 0x1 | ATTR4_SUPPRESS_WEAPON_PROCS,
                    "SpellClassSet": 11, "SpellClassMask_3": D2_SS_STRIKES}
            return _row(i, **{**base, **cols})
        primaries = {32175: _row(32175, AttributesEx3=0x40600), 32176: _row(32176, AttributesEx3=0x1040200)}
        good = {202413: strike(202413), 202415: strike(202415, AttributesEx3=0x1040000 | ATTR3_SUPPRESS_CASTER_PROCS), **primaries}
        self.assertEqual(check_cleave_strikes(good), [])
        for col, val in (("AttributesEx3", 0x40600 | ATTR3_SUPPRESS_CASTER_PROCS),     # NOT_A_PROC kept
                         ("AttributesEx3", 0x40400),                                    # no SUPPRESS_CASTER_PROCS
                         ("AttributesEx4", 0x1),                                        # no SUPPRESS_WEAPON_PROCS
                         ("SpellClassMask_3", 0x400),                                   # lost d2 b12
                         ("SpellClassSet", 0)):
            self.assertEqual(len(check_cleave_strikes({**good, 202413: strike(202413, **{col: val})})), 1, (col, val))
        self.assertTrue(check_cleave_strikes({k: v for k, v in good.items() if k != 202415}))              # missing row
        self.assertEqual(len(check_cleave_strikes({**good, 32175: _row(32175, AttributesEx3=0x40400)})), 1)  # primary lost NOT_A_PROC

    def test_gust_weapon_procs(self):
        good = {GUST: _row(GUST, AttributesEx4=ATTR4_SUPPRESS_WEAPON_PROCS),
                GUST_SPLASH: _row(GUST_SPLASH, AttributesEx4=ATTR4_SUPPRESS_WEAPON_PROCS, AttributesEx3=ATTR3_SUPPRESS_CASTER_PROCS)}
        self.assertEqual(check_gust_no_weapon_procs(good), [])
        self.assertEqual(len(check_gust_no_weapon_procs({**good, GUST: _row(GUST)})), 1)
        self.assertEqual(len(check_gust_no_weapon_procs({**good, GUST_SPLASH: _row(GUST_SPLASH, AttributesEx4=ATTR4_SUPPRESS_WEAPON_PROCS)})), 1)
        # the Gust itself must keep reaching Maelstrom Weapon
        self.assertEqual(len(check_gust_no_weapon_procs({**good, GUST: _row(GUST, AttributesEx4=ATTR4_SUPPRESS_WEAPON_PROCS,
                                                                           AttributesEx3=ATTR3_SUPPRESS_CASTER_PROCS)})), 1)
        self.assertTrue(check_gust_no_weapon_procs({}))

    def test_mq_spell_buff(self):
        good = {MQ_SPELL_BUFF: _row(MQ_SPELL_BUFF, SpellClassSet=11, **_mod(1, AURA_ADD_PCT_MODIFIER, SPELLMOD_DAMAGE, 9, MQ_SPELL_MASK))}
        self.assertEqual(check_mq_spell_buff(good), [])
        old_shape = {MQ_SPELL_BUFF: _row(MQ_SPELL_BUFF, Effect_1=6, EffectAura_1=79, EffectBasePoints_1=9, EffectMiscValue_1=126)}
        self.assertTrue(check_mq_spell_buff(old_shape))                                              # aura 79, all magic schools
        for mask in ((0x90100003 | 0x4000000, 0x1000, 0x100000), (0x90100003, 0, 0x100000),         # extra bit / missing Lava Burst
                     (0x90100003, 0x1000, 0x100000 | 0x4), (0x90100003 | 0x400, 0x1000, 0x100000)):  # Lava Lash, orb
            bad = {MQ_SPELL_BUFF: _row(MQ_SPELL_BUFF, SpellClassSet=11, **_mod(1, AURA_ADD_PCT_MODIFIER, SPELLMOD_DAMAGE, 9, mask))}
            self.assertTrue(check_mq_spell_buff(bad), mask)
        for col, val in (("EffectBasePoints_1", 10), ("SpellClassSet", 0), ("EffectMiscValue_1", 8)):
            bad = {MQ_SPELL_BUFF: _row(MQ_SPELL_BUFF, **{**good[MQ_SPELL_BUFF], col: val})}
            self.assertTrue(check_mq_spell_buff(bad), col)
        self.assertTrue(check_mq_spell_buff({}))

    def test_no_flame_shock_bit(self):
        self.assertEqual(check_no_flame_shock_bit({202384: _row(202384, SpellClassMask_1=0x1000)}), [])
        for i in NO_FLAME_SHOCK_BIT:
            self.assertEqual(len(check_no_flame_shock_bit({i: _row(i, SpellClassMask_1=D0_B28_FLAME_SHOCK)})), 1)

    def test_burst_bits(self):
        self.assertEqual(check_burst_bits({202384: _row(202384, SpellClassMask_3=D2_ENH_SPELL_HIT),
                                           202385: _row(202385, SpellClassMask_3=D2_ENH_SPELL_HIT)}), [])
        self.assertEqual(len(check_burst_bits({202385: _row(202385)})), 1)

    def test_charge_buffs(self):
        good = {i: _row(i, CumulativeAura=cap, Attributes=ATTR0_NO_AURA_CANCEL) for i, cap in CHARGE_BUFFS.items()}
        self.assertEqual(check_charge_buffs(good), [])
        for i, val in ((202380, 9), (202383, 50)):
            bad = {**good, i: _row(i, CumulativeAura=val, Attributes=ATTR0_NO_AURA_CANCEL)}
            self.assertEqual(len(check_charge_buffs(bad)), 1)
        self.assertEqual(len(check_charge_buffs({**good, 202381: _row(202381, CumulativeAura=10)})), 1)
        self.assertTrue(check_charge_buffs({}))

    def test_no_cancel(self):
        self.assertTrue(check_no_cancel({202407: _row(202407)}, (202407,)))
        self.assertEqual(check_no_cancel({202407: _row(202407, Attributes=ATTR0_NO_AURA_CANCEL)}, (202407,)), [])

    def test_visible_not_passive(self):
        self.assertEqual(check_visible_not_passive({202380: _row(202380, Attributes=0)}), [])
        self.assertEqual(len(check_visible_not_passive({202380: _row(202380, Attributes=ATTR0_PASSIVE)})), 1)

    def test_visible_buff_aura_text(self):
        base = {"Effect_1": 6, "EffectAura_1": 4}
        self.assertEqual(check_visible_buffs({202380: _row(202380, AuraDescription_Lang_enUS="Fire charges.", **base)}, [202380]), [])
        self.assertEqual(len(check_visible_buffs({202380: _row(202380, AuraDescription_Lang_enUS="Gains 10%.", **base)}, [202380])), 1)
        self.assertEqual(len(check_visible_buffs({202380: _row(202380, **base)}, [202380])), 1)
        self.assertEqual(check_visible_buffs({202380: _row(202380, Attributes=ATTR0_PASSIVE, **base)}, [202380]), [])

    def test_tooltip_vars(self):
        good = [{"id": i, "Variables": "$sf=1"} for i in SDV_IDS]
        self.assertEqual(check_tooltip_vars(good, ids=SDV_IDS), [])
        self.assertEqual(len(check_tooltip_vars(good[:2], ids=SDV_IDS)), 1)
        bad = [good[0], good[1], {"id": 1219, "Variables": "$averyverylongname=1"}]
        self.assertEqual(len(check_tooltip_vars(bad, ids=SDV_IDS)), 1)
        self.assertEqual(check_tooltip_vars([{"id": 1219, "Variables": "$exactly12chr=1"}] + good[:2], ids=SDV_IDS), [])

    def test_group_1259(self):
        groups = [{"id": 1259, "spell_id": 202399}, {"id": 1259, "spell_id": 202400}]
        rules = [{"group_id": 1259, "stack_rule": 1}]
        self.assertEqual(check_group_1259(groups, rules), [])
        self.assertEqual(len(check_group_1259(groups, [{"group_id": 1259, "stack_rule": 3}])), 1)
        self.assertEqual(len(check_group_1259(groups, [])), 1)
        self.assertEqual(len(check_group_1259(groups[:1], rules)), 1)
        self.assertEqual(len(check_group_1259(groups + [{"id": 1259, "spell_id": 9}], rules)), 1)
        self.assertEqual(len(check_group_1259(groups, rules + rules)), 1)

    def test_dws_home(self):
        text = "x = spell(\n    id=30816,\n)\ny = spell(\n    id=30818,\n)\nz = spell(\n    id=30819,\n)\n"
        self.assertEqual(check_dws_home("", text), [])
        self.assertEqual(len(check_dws_home(text, text)), 3)
        self.assertEqual(len(check_dws_home("", text.replace("30818", "30817"))), 1)

    def test_dws_proc(self):
        good = {"SpellId": -30816, "ProcFlags": 0x800000, "Chance": 20.0, "SpellFamilyName": 0, "SpellFamilyMask0": 0,
                "SpellFamilyMask1": 0, "SpellFamilyMask2": 0, "SpellPhaseMask": 0, "SpellTypeMask": 0}
        self.assertEqual(check_dws_proc([good]), [])
        for col, val in (("ProcFlags", 0x4), ("Chance", 30.0), ("SpellFamilyName", 11),
                         ("SpellPhaseMask", 1), ("SpellTypeMask", 1), ("SpellFamilyMask0", 1)):
            self.assertEqual(len(check_dws_proc([{**good, col: val}])), 1, col)

    def test_spirit_weapons(self):
        self.assertEqual(check_spirit_weapons({}, {16268: _row(16268, Effect_1=6, Effect_2=6)}), [])
        self.assertEqual(len(check_spirit_weapons({}, {16268: _row(16268, Effect_1=6, Effect_2=36, EffectTriggerSpell_2=18848)})), 1)

    def test_unleashed_rage(self):
        self.assertEqual(check_unleashed_rage({30802: _row(30802, EffectAura_1=137, EffectAura_2=35)}), [])
        self.assertEqual(len(check_unleashed_rage({30802: _row(30802, EffectAura_1=137, EffectAura_2=240)})), 1)

    def test_lava_lash(self):
        good = _row(60103, Effect_1=31, EffectBasePoints_1=109, EffectDieSides_1=1,
                    Description_Lang_enUS="Strike for 110% off-hand weapon damage as Fire damage.")
        self.assertEqual(check_lava_lash({60103: good}), [])
        self.assertEqual(len(check_lava_lash({60103: {**good, "EffectBasePoints_1": 99}})), 1)
        self.assertEqual(len(check_lava_lash({60103: {**good, "Description_Lang_enUS": "100% off-hand weapon damage"}})), 1)
        self.assertEqual(len(check_lava_lash({60103: {**good, "Effect_1": 2}})), 1)
        self.assertEqual(len(check_lava_lash({})), 1)

    def test_ascendance_transform_gate(self):
        good = {i: _row(i, Effect_1=6, EffectApplyAuraName_1=108) for i in ASCENDANCES}
        self.assertEqual(check_no_ascendance_transform(good), [])
        self.assertEqual(len(check_no_ascendance_transform({**good, 202393: _row(202393, Effect_1=6, EffectApplyAuraName_1=56)})), 1)
        self.assertEqual(len(check_no_ascendance_transform({**good, 202388: _row(202388, EffectApplyAuraName_2=56, Effect_1=6)})), 1)
        self.assertEqual(len(check_no_ascendance_transform({**good, 202393: _row(202393)})), 1)

    def test_ascend_burst_gate(self):
        good = {i: _row(i, Effect_1=3, ImplicitTargetA_1=1, SpellVisualID_1=v, AttributesEx3=ATTR3_SUPPRESS_CASTER_PROCS)
                for i, v in ASCEND_BURSTS.items()}
        self.assertEqual(check_ascend_bursts(good), [])
        self.assertEqual(len(check_ascend_bursts({**good, 202416: {**good[202416], "SpellVisualID_1": 0}})), 1)
        self.assertEqual(len(check_ascend_bursts({**good, 202417: {**good[202417], "Effect_2": 2}})), 1)
        self.assertEqual(len(check_ascend_bursts({**good, 202418: {**good[202418], "SpellClassSet": 11}})), 1)
        self.assertEqual(len(check_ascend_bursts({**good, 202419: {**good[202419], "AttributesEx3": 0}})), 1)
        self.assertEqual(len(check_ascend_bursts(good, script_ids={202416})), 1)
        self.assertEqual(len(check_ascend_bursts({k: v for k, v in good.items() if k != 202416})), 1)

    def test_id_map(self):
        self.assertEqual(check_id_map({202413, 202415, 202440}), [])
        self.assertEqual(len(check_id_map({202420})), 1)


if __name__ == "__main__":
    unittest.main()
