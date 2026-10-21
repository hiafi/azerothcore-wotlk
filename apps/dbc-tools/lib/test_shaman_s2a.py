"""
Shaman S2a data gate (shaman-rework S2a-HANDOFF row A5, S2a-WP-BRIEF id map, docs/reworks/shaman-restoration-rework.md).

Loads the real shaman DSL package and asserts on the BUILT rows (stock base + DSL + raw_overrides via
`build.build_spell_row`; same recipe as test_shaman_sh0b / test_shaman_s1a), plus the declared talent / trainer /
creature / tooltip-variable tables. Each check is a pure function over rows or declared entries so the negative fixtures
can prove it fails on a minimal bad input.

Conventions (as in test_shaman_s1a): a built EffectBasePoints is the live value minus one (DieSides <= 1), so "+10%" is
stored 9. Only the OWN SpellClassMask is held to the FORBIDDEN_* bits; EFFECT masks are selectors and may name any spell.
Flat millisecond values accept stored or stored+1 (the DSL may write either).

Run: apps/dbc-tools/.venv/bin/python3 -m pytest apps/dbc-tools/lib/test_shaman_s2a.py -q
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.test_shaman_s1a import check_tooltip_vars, check_visible_buffs  # noqa: E402,F401
from lib.test_shaman_sh0a import m, spell_mask, _hex, _u32  # noqa: E402
from lib.test_shaman_sh0b import _data as _shaman_data  # noqa: E402

RESTO_TAB = 262
CLASS_SET = 11
S2A_IDS = tuple(range(202640, 202655)) + tuple(range(202660, 202682))
S2A_FIX_SPARE = range(202720, 202760)  # fix-pass spare block: allowed to be declared
S2A_UNMAPPED = tuple(range(202655, 202660)) + tuple(range(202682, 202720))

ATTR0_PASSIVE = 0x40
ATTR0_DO_NOT_DISPLAY = 0x80
ATTR0_NO_AURA_CANCEL = 0x80000000
ATTR3_SUPPRESS_CASTER_PROCS = 0x00010000
ATTR3_DEATH_PERSISTENT = 0x00100000
ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
AURA_ADD_FLAT_MODIFIER, AURA_ADD_PCT_MODIFIER = 107, 108
AURA_MOD_HEALING_RECEIVED = 283
AURA_MOD_SPELL_CRIT_CHANCE, AURA_MOD_CRIT_PCT = 57, 290
SPELLMOD_DAMAGE, SPELLMOD_DURATION, SPELLMOD_CRIT, SPELLMOD_CAST_TIME = 0, 1, 7, 10
SPELLMOD_COOLDOWN, SPELLMOD_DAMAGE_MULTIPLIER, SPELLMOD_DOT = 11, 20, 22
MOD_AURAS = (AURA_ADD_FLAT_MODIFIER, AURA_ADD_PCT_MODIFIER)

# family bits (raw dwords). The first block comes from _masks; the two A3 appends fall back to the brief's values.
D0_LHW, D0_HW, D0_CH = 0x80, 0x40, 0x100               # d0 b7, b6, b8
D0_LB, D0_CL = 0x1, 0x2
D2_RIPTIDE = 0x10                                        # d2 b4
D1_EARTH_SHIELD = 0x400                                  # d1 b10
D1_EARTHLIVING = 0x80000                                 # d1 b19
D2_HEALING_RAIN = getattr(m, "HEALING_RAIN", 0x200000)   # d2 b21
D2_TORRENT = getattr(m, "TORRENT", 0x400000)             # d2 b22
D2_UNDULATING = getattr(m, "UNDULATING_HEAL", 0x800000)  # d2 b23
D0_MANA_TIDE_SUMMON = getattr(m, "MANA_TIDE_SUMMON", 0x2000000)  # d0 b25
D0_SUMMON_B29 = 0x20000000
D0_HEALING_STREAM = getattr(m, "HEALING_STREAM_HEAL", 0x2000)    # d0 b13
D2_MINOR_HEAL = getattr(m, "MINOR_HEAL", 0x8000000)       # d2 b27
D2_TIDAL_FORCE_CAST = getattr(m, "TIDAL_FORCE_CAST", 0x10000000)  # d2 b28
# bits a HoT lives behind: a DAMAGE SpellMod reaching one needs its DOT twin
HOT_BITS = (0, D1_EARTH_SHIELD | D1_EARTHLIVING | getattr(m, "EARTHLIVING_AURA", 0x100000),
            D2_RIPTIDE | D2_HEALING_RAIN | D2_TORRENT)
# stock shields legitimately carry d1 b10 in their own mask
STOCK_SHIELD_ALLOW = (974, 379)

# docs/reworks/shaman-restoration-rework.md section 4 + brief "Rank-id lists": (tier, col) -> (name, rank ids).
GRID = {
    (0, 0): ("Flowing Tides", (202640, 202641, 202642)),
    (0, 1): ("Improved Healing Wave", (16182, 16226, 16227)),
    (0, 2): ("Totemic Focus", (16173, 16222, 16223)),
    (1, 0): ("Improved Reincarnation", (16184, 16209)),
    (1, 1): ("Improved Healing Stream", (29187, 29189, 29191)),
    (1, 2): ("Tidal Focus", (16179, 16214, 16215)),
    (2, 0): ("Improved Water Shield", (16180, 16196, 16198)),
    (2, 1): ("Earthen Bulwark", (16181,)),
    (2, 2): ("Tidal Force", (202654,)),
    (2, 3): ("Ancestral Healing", (16176, 16235, 16240)),
    (3, 2): ("Tidal Mastery", (16194, 16218, 16219)),
    (4, 0): ("Healing Way", (29206, 29205, 29202)),
    (4, 1): ("Riptide", (61295,)),
    (4, 3): ("Torrent", (30864, 30865)),
    (5, 0): ("Rainfall", (202643, 202644)),
    (5, 2): ("Purification", (16178, 16210, 16211)),
    (6, 0): ("Nature's Guardian", (30881, 30883)),
    (6, 1): ("Mana Tide Totem", (16190,)),
    (6, 2): ("Spirit Link Totem", (202645,)),
    (6, 3): ("Restorative Totems", (16187, 16205, 16206)),
    (7, 0): ("Blessing of the Eternals", (51554, 51555)),
    (7, 1): ("Totemic Resonance", (202646,)),
    (7, 2): ("Nature's Blessing", (30867, 30868, 30869)),
    (7, 3): ("Improved Chain Heal", (30872, 30873)),
    (8, 0): ("Ancestral Awakening", (51556, 51557, 51558)),
    (8, 1): ("Undulating Currents Totem", (202647,)),
    (8, 2): ("Improved Earth Shield", (51560, 51561, 202653)),
    (8, 3): ("Tidecaller", (202648, 202649)),
    (9, 1): ("Tidal Waves", (51562, 51563, 51564)),
    (9, 2): ("Kindling", (202650, 202651)),
    (10, 1): ("Cloudburst Totem", (202652,)),
}
EMPTY_CELLS = ((0, 3), (1, 3), (3, 0), (3, 1), (3, 3), (4, 2), (5, 1), (5, 3), (9, 0), (9, 3), (10, 0), (10, 2), (10, 3))
RETIRED_TALENT = 591
OLD_TIDAL_FORCE_SPELL = 55198

# stock rows S2a rewrites besides the 202640-202681 block (present ones are checked)
REWRITTEN_STOCK = (61295, 16190, 16191, 39610, 20608, 202283, 16177, 16236, 16237, 974, 331, 8004, 1064)
ANCESTRAL_FORTITUDE = (16177, 16236, 16237)

RIPTIDE = 61295
TIDAL_FORCE_CAST, TIDAL_FORCE_AURA, TIDAL_FORCE_STACK, TIDAL_FORCE_ECHO = 202654, 202672, 202673, 202674
TIDAL_MASTERY = (16194, 16218, 16219)
TW_BUFF, TW_RANKS, UNDULATION_COUNTER, IHS_COUNTER = 202669, (51562, 51563, 51564), 202670, 202660
MANA_TIDE, RESTORATIVE = 16190, (16187, 16205, 16206)
HEALING_RAIN_HEAL = 202283
TORRENT_HEAL, UCT_HEAL, TIDE_HEAL, NG_HEAL, PLACEMENT_HEAL = 202667, 202663, 202661, 202675, 202677
CLOUDBURST_RELEASE, BULWARK_SHIELD = 202666, 202678
REINCARNATION = 20608
SDV_IDS = tuple(range(1220, 1225))
HOT_TWIN_TALENTS = {"Healing Way": (29206, 29205, 29202), "Torrent": (30864, 30865), "Purification": (16178, 16210, 16211)}

# id -> (total potency, T seconds or None, wanted own-mask bit as (dword index, bit value) or None)
HEAL_POTENCY = {
    TIDE_HEAL: (30.0, 2.0, (0, D0_HEALING_STREAM)),
    UCT_HEAL: (30.0, 2.0, (2, D2_UNDULATING)),
    TORRENT_HEAL: (10.0, 1.5, (2, D2_TORRENT)),
    PLACEMENT_HEAL: (5.0, None, (2, D2_MINOR_HEAL)),
    NG_HEAL: (100.0, None, (2, D2_MINOR_HEAL)),
}
POTENCY_EXCLUDED = (TIDAL_FORCE_ECHO, BULWARK_SHIELD, CLOUDBURST_RELEASE)

CREATURE_SCRIPTS = {300279: "npc_sha_undulating_currents_totem", 300281: "npc_sha_spirit_link_totem"}
CREATURE_NO_SCRIPT = (300280, 300282)


# ---- row helpers ------------------------------------------------------------------------------------------

def _effect_mask(row: dict, e: int) -> tuple[int, int, int]:
    return tuple(_u32(row.get(f"EffectSpellClassMask{'ABC'[e - 1]}_{n}")) for n in (1, 2, 3))


def _mod_effects(row: dict) -> list[dict]:
    """The SpellMod (flat / pct) effects of a built row: idx, aura, misc, stored bp, mask."""
    out = []
    for e in (1, 2, 3):
        aura = int(row.get(f"EffectAura_{e}") or 0)
        if aura in MOD_AURAS:
            out.append({"idx": e, "aura": aura, "misc": int(row.get(f"EffectMiscValue_{e}") or 0),
                        "bp": int(row.get(f"EffectBasePoints_{e}") or 0), "mask": _effect_mask(row, e)})
    return out


def _live(bp: int) -> int:
    return bp + 1


def _has_bits(mask, bits) -> bool:
    return all(mask[i] & bits[i] == bits[i] for i in range(3))


def _bits(d0=0, d1=0, d2=0):
    return (d0, d1, d2)


def _find_mod(row: dict, misc: int, bits, aura=None, live=None, lenient=False):
    for fx in _mod_effects(row):
        if fx["misc"] != misc or not _has_bits(fx["mask"], bits):
            continue
        if aura is not None and fx["aura"] != aura:
            continue
        if live is not None:
            ok = _live(fx["bp"]) == live or (lenient and fx["bp"] == live)
            if not ok:
                continue
        return fx
    return None


def _potencies(entry: dict | None) -> list[tuple[int, dict]]:
    """(effect index, potency dict) for every effect with a resolved potency, in effect order."""
    out = []
    for e in (1, 2, 3):
        pot = ((entry or {}).get(f"effect{e}") or {}).get("_potency")
        if pot:
            out.append((e, pot))
    return out


def _duration(entry: dict | None) -> int:
    return int((entry or {}).get("duration_ms") or 0)


def _cooldown(row: dict, entry: dict | None) -> int:
    return max(int(row.get("RecoveryTime") or 0), int(row.get("CategoryRecoveryTime") or 0),
               int((entry or {}).get("cooldown_ms") or 0), int((entry or {}).get("category_cooldown_ms") or 0))


def _missing(rows: dict, *ids) -> list[str]:
    return [f"{i}: not built" for i in ids if i not in rows]


# ---- checks (pure) ----------------------------------------------------------------------------------------

def check_grid(talents: list[dict], names: dict[int, str], expected=GRID, empty=EMPTY_CELLS) -> list[str]:
    """Tab 262 holds exactly the documented talents: cell, name, rank id list."""
    bad, seen = [], {}
    for t in talents:
        if int(t["tab_id"]) != RESTO_TAB:
            continue
        cell = (int(t["tier"]), int(t["column"]))
        if cell in seen:
            bad.append(f"talent {t['id']}: cell {cell} also holds talent {seen[cell]}")
        seen[cell] = t["id"]
        want = expected.get(cell)
        ranks = [int(r) for r in t["rank_spell_ids"]]
        if want is None:
            bad.append(f"talent {t['id']}: undocumented cell {cell}")
            continue
        if names.get(ranks[0]) != want[0]:
            bad.append(f"talent {t['id']} at {cell}: name {names.get(ranks[0])!r}, expected {want[0]!r}")
        if ranks != list(want[1]):
            bad.append(f"talent {t['id']} {want[0]}: ranks {ranks}, expected {list(want[1])}")
    bad += [f"cell {cell}: {want[0]} missing" for cell, want in expected.items() if cell not in seen]
    bad += [f"cell {cell}: should be empty, holds talent {seen[cell]}" for cell in empty if cell in seen]
    total = sum(len(t["rank_spell_ids"]) for t in talents if int(t["tab_id"]) == RESTO_TAB)
    want_pts = sum(len(r) for _n, r in expected.values())
    if len(seen) != len(expected) or total != want_pts:
        bad.append(f"tab {RESTO_TAB} holds {len(seen)} talents / {total} points, expected {len(expected)} / {want_pts}")
    return bad


def check_counts(talents: list[dict]) -> list[str]:
    mine = [t for t in talents if int(t["tab_id"]) == RESTO_TAB]
    pts = sum(len(t["rank_spell_ids"]) for t in mine)
    return [] if (len(mine), pts) == (31, 69) else [f"tab {RESTO_TAB}: {len(mine)} talents / {pts} points, expected 31 / 69"]


def check_rank_levels(talents: list[dict], levels: dict[int, int]) -> list[str]:
    bad = []
    for t in talents:
        if int(t["tab_id"]) != RESTO_TAB:
            continue
        chain = [levels.get(r, 0) for r in t["rank_spell_ids"]]
        if chain != sorted(chain) or any(lv > 80 for lv in chain):
            bad.append(f"talent {t['id']}: rank levels {chain} are not ascending within 1..80")
    return bad


def check_no_depends_on(talents: list[dict]) -> list[str]:
    return [f"talent {t['id']}: depends_on {t['depends_on']!r} on tab {RESTO_TAB}" for t in talents
            if int(t["tab_id"]) == RESTO_TAB and t.get("depends_on")]


def check_retired_and_old_tidal_force(talents: list[dict]) -> list[str]:
    bad = [f"talent {RETIRED_TALENT} still on tab {RESTO_TAB}" for t in talents
           if int(t["id"]) == RETIRED_TALENT and int(t["tab_id"]) == RESTO_TAB]
    for t in talents:
        if OLD_TIDAL_FORCE_SPELL in [int(r) for r in t["rank_spell_ids"]]:
            bad.append(f"talent {t['id']}: still ranks {OLD_TIDAL_FORCE_SPELL} (old Tidal Force)")
    return bad


def check_equipped_item_class(rows: dict[int, dict], ids) -> list[str]:
    return [f"{i}: EquippedItemClass {rows[i].get('EquippedItemClass')!r}, expected -1"
            for i in ids if i in rows and _u32(rows[i].get("EquippedItemClass")) != 0xFFFFFFFF]


def check_forbidden_bits(rows: dict[int, dict], ids, allow=STOCK_SHIELD_ALLOW) -> list[str]:
    bad = []
    for i in ids:
        if i not in rows or i in allow:
            continue
        mask = spell_mask(rows[i])
        hit = (mask[0] & m.FORBIDDEN_D0, mask[1] & m.FORBIDDEN_D1, mask[2] & m.FORBIDDEN_D2)
        if any(hit):
            bad.append(f"{i}: SpellClassMask {_hex(mask)} holds forbidden bits {_hex(hit)}")
    return bad


def check_riptide(rows: dict, entries: dict) -> list[str]:
    row, entry = rows.get(RIPTIDE), entries.get(RIPTIDE)
    if row is None or entry is None:
        return [f"{RIPTIDE}: not declared"]
    bad = []
    if int(row.get("SpellLevel") or 0) != 30:
        bad.append(f"{RIPTIDE}: SpellLevel {row.get('SpellLevel')}, expected 30")
    pots = _potencies(entry)
    if len(pots) != 2:
        return bad + [f"{RIPTIDE}: {len(pots)} potency effects, expected direct 43 + periodic 5"]
    (_, direct), (_, periodic) = pots
    for label, pot, want, t in (("direct", direct, 43.0, 1.5), ("periodic", periodic, 5.0, 3.0)):
        if pot.get("total_potency") != want:
            bad.append(f"{RIPTIDE}: {label} potency {pot.get('total_potency')!r}, expected {want}")
        if pot.get("t_seconds") != t:
            bad.append(f"{RIPTIDE}: {label} T {pot.get('t_seconds')!r}, expected {t}")
        if int(pot.get("spell_level") or 0) != 30:
            bad.append(f"{RIPTIDE}: {label} potency spell_level {pot.get('spell_level')!r}, expected 30")
    if _duration(entry) not in (0, 15000):
        bad.append(f"{RIPTIDE}: duration_ms {_duration(entry)}, expected 15000")
    return bad


def check_tidal_force(rows: dict, entries: dict) -> list[str]:
    bad = _missing(rows, TIDAL_FORCE_CAST, TIDAL_FORCE_AURA, TIDAL_FORCE_STACK, TIDAL_FORCE_ECHO)
    cast = rows.get(TIDAL_FORCE_CAST)
    if cast is not None:
        cd = _cooldown(cast, entries.get(TIDAL_FORCE_CAST))
        if cd != 120000:
            bad.append(f"{TIDAL_FORCE_CAST}: cooldown {cd}, expected 120000")
        if int(cast.get("StartRecoveryTime") or 0) or int(cast.get("StartRecoveryCategory") or 0):
            bad.append(f"{TIDAL_FORCE_CAST}: on the GCD (StartRecoveryTime {cast.get('StartRecoveryTime')}, "
                       f"category {cast.get('StartRecoveryCategory')}), expected off GCD")
        if not spell_mask(cast)[2] & D2_TIDAL_FORCE_CAST:
            bad.append(f"{TIDAL_FORCE_CAST}: SpellClassMask {_hex(spell_mask(cast))} lacks TIDAL_FORCE_CAST d2 b28")
        if int(cast.get("ManaCost") or 0) or int(cast.get("ManaCostPct") or 0):
            bad.append(f"{TIDAL_FORCE_CAST}: has a mana cost")
    if TIDAL_FORCE_AURA in rows:
        if _duration(entries.get(TIDAL_FORCE_AURA)) != 10000:
            bad.append(f"{TIDAL_FORCE_AURA}: duration_ms {_duration(entries.get(TIDAL_FORCE_AURA))}, expected 10000")
        aura = rows[TIDAL_FORCE_AURA]
        if not _find_mod(aura, SPELLMOD_DURATION, _bits(d2=D2_HEALING_RAIN), aura=AURA_ADD_PCT_MODIFIER, live=50):
            bad.append(f"{TIDAL_FORCE_AURA}: no SPELLMOD_DURATION pct +50 on Healing Rain (d2 b21)")
        if not _find_mod(aura, SPELLMOD_DAMAGE_MULTIPLIER, _bits(d0=D0_CH), aura=AURA_ADD_PCT_MODIFIER, live=67):
            bad.append(f"{TIDAL_FORCE_AURA}: no SPELLMOD_DAMAGE_MULTIPLIER pct +67 on Chain Heal (d0 b8)")
    stack = rows.get(TIDAL_FORCE_STACK)
    if stack is not None:
        auras = [int(stack.get(f"EffectAura_{e}") or 0) for e in (1, 2, 3)]
        if AURA_MOD_HEALING_RECEIVED not in auras:
            bad.append(f"{TIDAL_FORCE_STACK}: auras {auras}, none is MOD_HEALING_RECEIVED (283)")
        else:
            e = auras.index(AURA_MOD_HEALING_RECEIVED) + 1
            if _live(int(stack.get(f"EffectBasePoints_{e}") or 0)) != 5:
                bad.append(f"{TIDAL_FORCE_STACK}: heal-received bonus {_live(int(stack.get(f'EffectBasePoints_{e}') or 0))}, expected 5")
            if any(_effect_mask(stack, e)):
                bad.append(f"{TIDAL_FORCE_STACK}: effect {e} carries a family mask {_hex(_effect_mask(stack, e))}")
        if int(stack.get("CumulativeAura") or 0) != 3:
            bad.append(f"{TIDAL_FORCE_STACK}: CumulativeAura {stack.get('CumulativeAura')}, expected 3")
        if _duration(entries.get(TIDAL_FORCE_STACK)) != 8000:
            bad.append(f"{TIDAL_FORCE_STACK}: duration_ms {_duration(entries.get(TIDAL_FORCE_STACK))}, expected 8000")
    echo = rows.get(TIDAL_FORCE_ECHO)
    if echo is not None and not _u32(echo.get("AttributesEx3")) & ATTR3_IGNORE_CASTER_MODIFIERS:
        bad.append(f"{TIDAL_FORCE_ECHO}: lacks ATTR3_IGNORE_CASTER_MODIFIERS (echo is script-sized)")
    for rank, want in zip(TIDAL_MASTERY, (3000, 6000, 9000)):
        row = rows.get(rank)
        if row is not None and not _find_mod(row, SPELLMOD_COOLDOWN, _bits(d2=D2_TIDAL_FORCE_CAST), aura=AURA_ADD_FLAT_MODIFIER,
                                             live=-want, lenient=True):
            bad.append(f"{rank}: Tidal Mastery lacks SPELLMOD_COOLDOWN flat -{want} on the Tidal Force cast (d2 b28)")
    return bad


def check_tidal_waves(rows: dict, entries: dict) -> list[str]:
    bad = []
    for rank in TW_RANKS:
        row = rows.get(rank)
        if row is not None and (int(row.get("ProcTypeMask") or 0) or int(row.get("ProcChance") or 0)):
            bad.append(f"{rank}: Tidal Waves rank keeps DBC proc flags (ProcTypeMask {row.get('ProcTypeMask')}, "
                       f"ProcChance {row.get('ProcChance')}); the C++ grants it")
    row = rows.get(TW_BUFF)
    if row is None:
        return bad + [f"{TW_BUFF}: not built"]
    if int(row.get("CumulativeAura") or 0) != 3:
        bad.append(f"{TW_BUFF}: CumulativeAura {row.get('CumulativeAura')}, expected 3")
    if _duration(entries.get(TW_BUFF)) != 15000:
        bad.append(f"{TW_BUFF}: duration_ms {_duration(entries.get(TW_BUFF))}, expected 15000")
    if any(spell_mask(row)):
        bad.append(f"{TW_BUFF}: SpellClassMask {_hex(spell_mask(row))} must carry no family bits")
    if _u32(row.get("AttributesEx3")) & ATTR3_DEATH_PERSISTENT:
        bad.append(f"{TW_BUFF}: survives death (AttributesEx3 0x100000); Tidal Waves must not")
    if not _find_mod(row, SPELLMOD_CAST_TIME, _bits(d0=D0_HW), aura=AURA_ADD_PCT_MODIFIER, live=-10):
        bad.append(f"{TW_BUFF}: no SPELLMOD_CASTING_TIME pct -10 on Healing Wave (d0 b6)")
    if not _find_mod(row, SPELLMOD_CRIT, _bits(d0=D0_LHW), live=10):
        bad.append(f"{TW_BUFF}: no SPELLMOD_CRITICAL_CHANCE +10 on Lesser Healing Wave (d0 b7)")
    return bad


def check_counters(rows: dict, entries: dict) -> list[str]:
    bad = []
    undulation = rows.get(UNDULATION_COUNTER)
    if undulation is None:
        bad.append(f"{UNDULATION_COUNTER}: not built")
    elif int(undulation.get("CumulativeAura") or 0) != 3:
        bad.append(f"{UNDULATION_COUNTER}: CumulativeAura {undulation.get('CumulativeAura')}, expected 3")
    for i in (UNDULATION_COUNTER, IHS_COUNTER):
        row = rows.get(i)
        if row is not None and not (_u32(row.get("AttributesEx3")) & ATTR3_DEATH_PERSISTENT
                                    and _u32(row.get("AttributesEx2")) & 0x1):
            bad.append(f"{i}: counter must persist through death (AttributesEx3 0x100000 + AttributesEx2 0x1)")
    return bad


def check_mana_tide(rows: dict, entries: dict) -> list[str]:
    row, entry = rows.get(MANA_TIDE), entries.get(MANA_TIDE)
    if row is None:
        return [f"{MANA_TIDE}: not declared"]
    bad = []
    if _duration(entry) != 10000:
        bad.append(f"{MANA_TIDE}: duration_ms {_duration(entry)}, expected 10000")
    if _cooldown(row, entry) != 180000:
        bad.append(f"{MANA_TIDE}: cooldown {_cooldown(row, entry)}, expected 180000")
    mask = spell_mask(row)
    if not mask[0] & D0_MANA_TIDE_SUMMON:
        bad.append(f"{MANA_TIDE}: SpellClassMask d0 {mask[0]:#x} lacks MANA_TIDE_SUMMON d0 b25")
    if not mask[0] & D0_SUMMON_B29:
        bad.append(f"{MANA_TIDE}: SpellClassMask d0 {mask[0]:#x} lacks the summon-family bit d0 b29")
    if mask[1] or mask[2]:
        bad.append(f"{MANA_TIDE}: SpellClassMask d1/d2 {_hex(mask)} must be 0")
    if int(row.get("ManaCost") or 0) or int(row.get("ManaCostPct") or 0):
        bad.append(f"{MANA_TIDE}: has a mana cost")
    for rank, want in zip(RESTORATIVE, (10000, 20000, 30000)):
        r = rows.get(rank)
        if r is not None and not _find_mod(r, SPELLMOD_COOLDOWN, _bits(d0=D0_MANA_TIDE_SUMMON), aura=AURA_ADD_FLAT_MODIFIER,
                                           live=-want, lenient=True):
            bad.append(f"{rank}: Restorative Totems lacks SPELLMOD_COOLDOWN flat -{want} on Mana Tide (d0 b25)")
    return bad


def check_heal_rows(rows: dict, entries: dict, table=HEAL_POTENCY) -> list[str]:
    """Totem / helper heals: own family bit, potency, T, SpellLevel; the torrent also suppresses caster procs."""
    bad = []
    for sid, (total, t, bit) in table.items():
        row, entry = rows.get(sid), entries.get(sid)
        if row is None or entry is None:
            bad.append(f"{sid}: not declared")
            continue
        pots = _potencies(entry)
        if not pots:
            bad.append(f"{sid}: no potency effect")
        else:
            pot = pots[0][1]
            if pot.get("total_potency") != total:
                bad.append(f"{sid}: potency {pot.get('total_potency')!r}, expected {total}")
            if t is not None and pot.get("t_seconds") != t:
                bad.append(f"{sid}: T {pot.get('t_seconds')!r}, expected {t}")
        if not int(row.get("SpellLevel") or 0):
            bad.append(f"{sid}: potency row has no SpellLevel")
        if bit is not None and not spell_mask(row)[bit[0]] & bit[1]:
            bad.append(f"{sid}: SpellClassMask {_hex(spell_mask(row))} lacks d{bit[0]} {bit[1]:#x}")
    torrent = rows.get(TORRENT_HEAL)
    if torrent is not None:
        if spell_mask(torrent)[2] & ~D2_TORRENT:
            bad.append(f"{TORRENT_HEAL}: SpellClassMask d2 {spell_mask(torrent)[2]:#x} holds more than the torrent bit")
        if not _u32(torrent.get("AttributesEx3")) & ATTR3_SUPPRESS_CASTER_PROCS:
            bad.append(f"{TORRENT_HEAL}: lacks ATTR3_SUPPRESS_CASTER_PROCS (0x10000)")
    return bad


def check_uct_heal(rows: dict) -> list[str]:
    row = rows.get(UCT_HEAL)
    if row is None:
        return [f"{UCT_HEAL}: not built"]
    bad = []
    chain = [int(row.get(f"EffectChainTargets_{e}") or 0) for e in (1, 2, 3)]
    if 3 not in chain and int(row.get("MaxTargets") or 0) != 3:
        bad.append(f"{UCT_HEAL}: chain targets {chain} / MaxTargets {row.get('MaxTargets')}, none is 3")
    amps = [float(row.get(f"EffectChainAmplitude_{e}") or 0) for e in (1, 2, 3)]
    if not any(abs(a - 0.6) < 1e-4 for a in amps):
        bad.append(f"{UCT_HEAL}: chain amplitudes {amps}, none is 0.6")
    return bad


def check_healing_rain(rows: dict) -> list[str]:
    row = rows.get(HEALING_RAIN_HEAL)
    if row is None:
        return [f"{HEALING_RAIN_HEAL}: not declared"]
    if int(row.get("Effect_3") or 0) or int(row.get("EffectAura_3") or 0):
        return [f"{HEALING_RAIN_HEAL}: still has an effect 2 (Effect_3 {row.get('Effect_3')}, aura {row.get('EffectAura_3')})"]
    return []


def check_script_sized_heals(rows: dict, entries: dict) -> list[str]:
    bad = []
    release = rows.get(CLOUDBURST_RELEASE)
    if release is None:
        bad.append(f"{CLOUDBURST_RELEASE}: not built")
    else:
        if any(spell_mask(release)):
            bad.append(f"{CLOUDBURST_RELEASE}: SpellClassMask {_hex(spell_mask(release))} must carry no bits")
        if not _u32(release.get("AttributesEx3")) & ATTR3_IGNORE_CASTER_MODIFIERS:
            bad.append(f"{CLOUDBURST_RELEASE}: lacks ATTR3_IGNORE_CASTER_MODIFIERS")
    for sid in POTENCY_EXCLUDED:
        entry = entries.get(sid)
        if entry is not None and _potencies(entry):
            bad.append(f"{sid}: script-sized row carries a resolved potency")
        if entry is not None and not any(((entry.get(f"effect{e}") or {}).get("_potency_excluded")) for e in (1, 2, 3)):
            bad.append(f"{sid}: effects are not marked potency_excluded")
    return bad


def check_potency_levels(rows: dict, entries: dict, ids) -> list[str]:
    bad = []
    for i in ids:
        pots = _potencies(entries.get(i))
        if pots and i in rows and int(rows[i].get("SpellLevel") or 0) <= 0:
            bad.append(f"{i}: potency row without SpellLevel")
    return bad


def check_hot_twins(rows: dict, talents=HOT_TWIN_TALENTS) -> list[str]:
    """A DAMAGE SpellMod that reaches a HoT bit needs a DOT SpellMod covering the same bits with the same value."""
    bad = []
    for name, ranks in talents.items():
        for i in ranks:
            row = rows.get(i)
            if row is None:
                bad.append(f"{name} {i}: not built")
                continue
            for dmg in (fx for fx in _mod_effects(row) if fx["misc"] == SPELLMOD_DAMAGE):
                hot = tuple(dmg["mask"][n] & HOT_BITS[n] for n in range(3))
                if not any(hot):
                    continue
                twin = [fx for fx in _mod_effects(row) if fx["misc"] == SPELLMOD_DOT and fx["aura"] == dmg["aura"]
                        and fx["bp"] == dmg["bp"] and _has_bits(fx["mask"], hot)]
                if not twin:
                    bad.append(f"{name} {i}: effect {dmg['idx']} DAMAGE mod reaches HoT bits {_hex(hot)} with no "
                               f"matching SPELLMOD_DOT twin")
    return bad


def check_no_duplicate_effects(rows: dict, ids) -> list[str]:
    """Stale raw twins show up as two identical effects on one row."""
    bad = []
    for i in ids:
        row = rows.get(i)
        if row is None:
            continue
        seen = {}
        for e in (1, 2, 3):
            if not int(row.get(f"Effect_{e}") or 0):
                continue
            key = (int(row.get(f"Effect_{e}")), int(row.get(f"EffectAura_{e}") or 0), int(row.get(f"EffectMiscValue_{e}") or 0),
                   int(row.get(f"EffectBasePoints_{e}") or 0), _effect_mask(row, e), int(row.get(f"EffectTriggerSpell_{e}") or 0))
            if key in seen:
                bad.append(f"{i}: effects {seen[key]} and {e} are identical (stale twin)")
            seen[key] = e
    return bad


RAW_EFFECT_KEY = re.compile(r"^(Effect|EffectAura|EffectMiscValue|EffectBasePoints|EffectDieSides|EffectSpellClassMask[ABC])(?:_(\d))$")


def check_raw_twins(entries: dict, ids) -> list[str]:
    """raw_overrides must not re-state a column of an effect the typed DSL already declares (the latent twin of L12)."""
    bad = []
    for i in ids:
        entry = entries.get(i)
        if entry is None:
            continue
        for key in (entry.get("raw_overrides") or {}):
            hit = RAW_EFFECT_KEY.match(key)
            if hit and f"effect{hit.group(2)}" in entry and not hit.group(1).startswith("EffectSpellClassMask"):
                bad.append(f"{i}: raw_overrides {key} duplicates typed effect {hit.group(2)}")
    return bad


def check_reincarnation(rows: dict, trainers: list[dict]) -> list[str]:
    bad = []
    levels = [int(t["ReqLevel"]) for t in trainers if int(t["TrainerId"]) == 210 and int(t["SpellId"]) == REINCARNATION]
    if levels != [15]:
        bad.append(f"trainer 210 spell {REINCARNATION}: ReqLevel {levels}, expected [15]")
    row = rows.get(REINCARNATION)
    if row is None:
        bad.append(f"{REINCARNATION}: not declared")
    else:
        for col in ("SpellLevel", "BaseLevel"):
            if int(row.get(col) or 0) != 15:
                bad.append(f"{REINCARNATION}: {col} {row.get(col)}, expected 15")
    if any(int(t["TrainerId"]) == 14 and int(t["SpellId"]) == REINCARNATION for t in trainers):
        bad.append(f"trainer 14 spell {REINCARNATION}: declared (trainer 14 stays untouched)")
    return bad


def check_creatures(creatures: dict, creature_spells: list[dict]) -> list[str]:
    bad = []
    for cid, name in CREATURE_SCRIPTS.items():
        c = creatures.get(cid)
        if c is None:
            bad.append(f"{cid}: creature not declared")
        elif c["ScriptName"] != name:
            bad.append(f"{cid}: ScriptName {c['ScriptName']!r}, expected {name!r}")
    for cid in CREATURE_NO_SCRIPT:
        c = creatures.get(cid)
        if c is None:
            bad.append(f"{cid}: creature not declared")
        elif c["ScriptName"]:
            bad.append(f"{cid}: unexpected ScriptName {c['ScriptName']!r}")
    index0 = {int(r["CreatureID"]): int(r["Spell"]) for r in creature_spells if int(r["Index"]) == 0}
    if index0.get(300282) != 5672:
        bad.append(f"300282: creature_spell index 0 is {index0.get(300282)}, expected 5672")
    return bad


def check_id_map(declared, unmapped=S2A_UNMAPPED) -> list[str]:
    bad = [f"{i}: not declared" for i in S2A_IDS if i not in declared]
    bad += [f"{i}: declared outside the S2a id map" for i in sorted(declared) if i in unmapped]
    return bad


# S2a review m3: state indicators the player must not click off (the proc store, the Totemic Resonance refresh).
NO_CANCEL_IDS = (202662, 202665)
# S2a review (user ruling): Blessing of the Eternals raises melee, ranged and spell crit (aura 290, one effect).
BOTE_RANKS = {51554: 1, 51555: 3}   # stored base points (live 2% / 4%)


def check_no_cancel(rows: dict, ids=NO_CANCEL_IDS) -> list[str]:
    bad = []
    for i in ids:
        row = rows.get(i)
        if row is None:
            bad.append(f"{i}: not declared")
        elif not _u32(row.get("Attributes")) & ATTR0_NO_AURA_CANCEL:
            bad.append(f"{i}: Attributes {_u32(row.get('Attributes')):#x} lacks SPELL_ATTR0_NO_AURA_CANCEL 0x80000000")
    return bad


def check_blessing_of_the_eternals(rows: dict, ranks=BOTE_RANKS) -> list[str]:
    bad = []
    for sid, stored in ranks.items():
        row = rows.get(sid)
        if row is None:
            bad.append(f"{sid}: not declared")
            continue
        crit = [e for e in (1, 2, 3)
                if int(row.get(f"EffectAura_{e}") or 0) in (AURA_MOD_SPELL_CRIT_CHANCE, AURA_MOD_CRIT_PCT)]
        if crit != [1] or int(row.get("EffectAura_1") or 0) != AURA_MOD_CRIT_PCT:
            bad.append(f"{sid}: needs exactly one crit effect (eff1 aura {AURA_MOD_CRIT_PCT}), found effects {crit} "
                       f"auras {[row.get(f'EffectAura_{e}') for e in crit]}")
        elif int(row.get("EffectBasePoints_1") or 0) != stored:
            bad.append(f"{sid}: eff1 stored base points {row.get('EffectBasePoints_1')}, expected {stored}")
        if int(row.get("EffectAura_2") or 0) != 4:
            bad.append(f"{sid}: eff2 (Earthliving chance dummy) must stay aura 4, is {row.get('EffectAura_2')}")
    return bad


# ---- real data --------------------------------------------------------------------------------------------

_S2A: dict = {}


_LOAD_ERROR: list = []


def _data():
    if _LOAD_ERROR:  # a broken package would otherwise re-load (minutes) for every test
        raise _LOAD_ERROR[0]
    try:
        d = _shaman_data()
    except Exception as exc:  # noqa: BLE001
        _LOAD_ERROR.append(exc)
        raise
    if not _S2A:
        names, levels = {}, {}
        for t in d["package"].talents:
            for r in t["rank_spell_ids"]:
                row = d["rows_by_id"].get(r) or d["stock"].get(r) or {}
                names[r] = row.get("Name_Lang_enUS")
                levels[r] = int(row.get("SpellLevel") or 0)
        _S2A.update(names=names, levels=levels)
    return {**d, **_S2A}


def _resto_ranks(d) -> list[int]:
    return [int(r) for t in d["package"].talents if int(t["tab_id"]) == RESTO_TAB for r in t["rank_spell_ids"]]


class ShamanS2aDataTest(unittest.TestCase):
    def assertClean(self, problems: list[str]):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_id_map(self):
        self.assertClean(check_id_map(set(_data()["rows_by_id"])))

    def test_grid(self):
        d = _data()
        self.assertClean(check_grid(d["package"].talents, d["names"]))

    def test_counts(self):
        self.assertClean(check_counts(_data()["package"].talents))

    def test_rank_levels(self):
        d = _data()
        self.assertClean(check_rank_levels(d["package"].talents, d["levels"]))

    def test_no_depends_on(self):
        self.assertClean(check_no_depends_on(_data()["package"].talents))

    def test_retired_591_and_old_tidal_force(self):
        self.assertClean(check_retired_and_old_tidal_force(_data()["package"].talents))

    def test_equipped_item_class(self):
        d = _data()
        ids = sorted(set(S2A_IDS) | set(_resto_ranks(d)) | set(REWRITTEN_STOCK) | set(S2A_FIX_SPARE))
        self.assertClean(check_equipped_item_class(d["rows_by_id"], ids))

    def test_no_forbidden_bits(self):
        d = _data()
        self.assertClean(check_forbidden_bits(d["rows_by_id"], sorted(set(S2A_IDS) | set(_resto_ranks(d)) | set(REWRITTEN_STOCK))))

    def test_riptide(self):
        d = _data()
        self.assertClean(check_riptide(d["rows_by_id"], d["entries_by_id"]))

    def test_tidal_force(self):
        d = _data()
        self.assertClean(check_tidal_force(d["rows_by_id"], d["entries_by_id"]))

    def test_tidal_force_old_spell_in_no_talent(self):
        # 55198 stays declared (stock row, untouched) but leaves every talent (check_retired_and_old_tidal_force).
        for t in _data()["talents"] if "talents" in _data() else []:
            self.assertNotIn(OLD_TIDAL_FORCE_SPELL, [int(r) for r in t["rank_spell_ids"]])

    def test_tidal_waves(self):
        d = _data()
        self.assertClean(check_tidal_waves(d["rows_by_id"], d["entries_by_id"]))

    def test_counters(self):
        d = _data()
        self.assertClean(check_counters(d["rows_by_id"], d["entries_by_id"]))

    def test_mana_tide(self):
        d = _data()
        self.assertClean(check_mana_tide(d["rows_by_id"], d["entries_by_id"]))

    def test_heal_rows(self):
        d = _data()
        self.assertClean(check_heal_rows(d["rows_by_id"], d["entries_by_id"]))

    def test_uct_heal(self):
        self.assertClean(check_uct_heal(_data()["rows_by_id"]))

    def test_healing_rain_has_no_effect_2(self):
        self.assertClean(check_healing_rain(_data()["rows_by_id"]))

    def test_script_sized_heals(self):
        d = _data()
        self.assertClean(check_script_sized_heals(d["rows_by_id"], d["entries_by_id"]))

    def test_potency_rows_have_spell_level(self):
        d = _data()
        ids = sorted(set(S2A_IDS) | set(REWRITTEN_STOCK))
        self.assertClean(check_potency_levels(d["rows_by_id"], d["entries_by_id"], ids))

    def test_hot_dot_twins(self):
        self.assertClean(check_hot_twins(_data()["rows_by_id"]))

    def test_no_stale_twins(self):
        d = _data()
        ids = sorted(set(_resto_ranks(d)) | set(S2A_IDS) | {61295, 16190, 16191})
        self.assertClean(check_no_duplicate_effects(d["rows_by_id"], ids))
        self.assertClean(check_raw_twins(d["entries_by_id"], ids))

    def test_reincarnation(self):
        d = _data()
        self.assertClean(check_reincarnation(d["rows_by_id"], d["package"].trainer_spells))

    def test_creatures(self):
        d = _data()
        self.assertClean(check_creatures(d["creatures"], d["package"].creature_template_spells))

    def test_no_cancel(self):
        self.assertClean(check_no_cancel(_data()["rows_by_id"]))

    def test_blessing_of_the_eternals(self):
        self.assertClean(check_blessing_of_the_eternals(_data()["rows_by_id"]))

    def test_visible_buffs_have_number_free_aura_text(self):
        d = _data()
        ids = sorted(set(S2A_IDS) | {RIPTIDE, *ANCESTRAL_FORTITUDE})
        self.assertClean(check_visible_buffs(d["rows_by_id"], ids))

    def test_tooltip_variable_names(self):
        self.assertClean(check_tooltip_vars(_data()["package"].tooltip_vars, ids=SDV_IDS))


# ---- negative fixtures ------------------------------------------------------------------------------------

def _row(spell_id=1, **cols) -> dict:
    return {"ID": spell_id, **cols}


def _talent(tid, tier, col, ranks, tab=RESTO_TAB, depends_on=None):
    return {"id": tid, "tab_id": tab, "tier": tier, "column": col, "rank_spell_ids": list(ranks), "depends_on": depends_on}


def _good_grid():
    talents, names = [], {}
    for n, ((tier, col), (name, ranks)) in enumerate(GRID.items()):
        talents.append(_talent(n + 1, tier, col, ranks))
        names[ranks[0]] = name
    return talents, names


def _mod(e, aura, misc, bp, mask_letter_dwords=(0, 0, 0)):
    """Columns of one SpellMod effect e (1..3) with an effect mask."""
    cols = {f"Effect_{e}": 6, f"EffectAura_{e}": aura, f"EffectMiscValue_{e}": misc, f"EffectBasePoints_{e}": bp}
    for n, v in enumerate(mask_letter_dwords, 1):
        cols[f"EffectSpellClassMask{'ABC'[e - 1]}_{n}"] = v
    return cols


class ShamanS2aNegativeTest(unittest.TestCase):
    def test_grid(self):
        talents, names = _good_grid()
        self.assertEqual(check_grid(talents, names), [])
        self.assertEqual(check_counts(talents), [])
        self.assertEqual(len(talents), 31)
        self.assertEqual(sum(len(t["rank_spell_ids"]) for t in talents), 69)
        self.assertTrue(check_grid(talents + [_talent(99, 4, 2, [5000])], {**names, 5000: "X"}))  # (4,2) must stay empty
        self.assertTrue(any("missing" in p for p in check_grid(talents[1:], names)))
        wrong = [dict(talents[0], rank_spell_ids=[202640, 202641])] + talents[1:]
        self.assertTrue(any("ranks" in p for p in check_grid(wrong, names)))
        self.assertTrue(any("name" in p for p in check_grid(talents, {**names, 202640: "Nope"})))
        self.assertTrue(check_grid([dict(talents[0], column=3)] + talents[1:], names))
        self.assertEqual(check_grid(talents + [_talent(98, 0, 0, [1], tab=261)], names), [])
        self.assertTrue(check_counts(talents[1:]))

    def test_rank_levels(self):
        talents = [_talent(1, 0, 0, [1, 2, 3])]
        self.assertEqual(check_rank_levels(talents, {1: 0, 2: 30, 3: 30}), [])
        self.assertEqual(len(check_rank_levels(talents, {1: 30, 2: 10, 3: 30})), 1)
        self.assertEqual(len(check_rank_levels(talents, {1: 0, 2: 0, 3: 81})), 1)

    def test_no_depends_on(self):
        self.assertEqual(check_no_depends_on([_talent(1, 0, 0, [1])]), [])
        self.assertEqual(len(check_no_depends_on([_talent(1, 0, 0, [1], depends_on=5)])), 1)
        self.assertEqual(check_no_depends_on([_talent(1, 0, 0, [1], tab=261, depends_on=5)]), [])

    def test_retired(self):
        self.assertEqual(check_retired_and_old_tidal_force([_talent(582, 2, 2, [202654])]), [])
        self.assertEqual(len(check_retired_and_old_tidal_force([_talent(591, 4, 2, [1])])), 1)
        self.assertEqual(check_retired_and_old_tidal_force([_talent(591, 0, 0, [1], tab=999)]), [])
        self.assertEqual(len(check_retired_and_old_tidal_force([_talent(582, 2, 2, [55198])])), 1)

    def test_equipped_item_class(self):
        self.assertEqual(len(check_equipped_item_class({202640: _row(202640, EquippedItemClass=0)}, [202640])), 1)
        self.assertEqual(len(check_equipped_item_class({202640: _row(202640)}, [202640])), 1)
        self.assertEqual(check_equipped_item_class({202640: _row(202640, EquippedItemClass=-1)}, [202640]), [])

    def test_forbidden_bits(self):
        for col, bit in (("SpellClassMask_1", m.FORBIDDEN_D0_B0), ("SpellClassMask_1", m.FORBIDDEN_D0_B28),
                         ("SpellClassMask_2", m.FORBIDDEN_D1_B12), ("SpellClassMask_3", m.FORBIDDEN_D2_B11)):
            self.assertEqual(len(check_forbidden_bits({202660: _row(202660, **{col: bit})}, [202660])), 1, col)
        self.assertEqual(check_forbidden_bits({974: _row(974, SpellClassMask_2=m.FORBIDDEN_D1_B10)}, [974]), [])
        self.assertEqual(len(check_forbidden_bits({202660: _row(202660, SpellClassMask_2=m.FORBIDDEN_D1_B10)}, [202660])), 1)
        self.assertEqual(check_forbidden_bits({202660: _row(202660, SpellClassMask_3=D2_TORRENT)}, [202660]), [])

    def _riptide(self, **over):
        pot = {"total_potency": 43.0, "t_seconds": 1.5, "spell_level": 30}
        per = {"total_potency": 5.0, "t_seconds": 3.0, "spell_level": 30}
        entry = {"effect1": {"_potency": dict(pot, **over.get("d", {}))}, "effect2": {"_potency": dict(per, **over.get("p", {}))},
                 "duration_ms": over.get("dur", 15000)}
        return {RIPTIDE: _row(RIPTIDE, SpellLevel=over.get("lvl", 30))}, {RIPTIDE: entry}

    def test_riptide(self):
        self.assertEqual(check_riptide(*self._riptide()), [])
        self.assertTrue(check_riptide(*self._riptide(lvl=1)))
        self.assertTrue(check_riptide(*self._riptide(d={"total_potency": 62.8})))
        self.assertTrue(check_riptide(*self._riptide(p={"total_potency": 6.3})))
        self.assertTrue(check_riptide(*self._riptide(p={"t_seconds": 1.5})))
        self.assertTrue(check_riptide(*self._riptide(d={"spell_level": 1})))
        self.assertTrue(check_riptide(*self._riptide(dur=12000)))
        self.assertEqual(len(check_riptide({}, {})), 1)

    def _tf(self):
        rows = {
            TIDAL_FORCE_CAST: _row(TIDAL_FORCE_CAST, RecoveryTime=120000, StartRecoveryTime=0, StartRecoveryCategory=0,
                                   SpellClassMask_3=D2_TIDAL_FORCE_CAST),
            TIDAL_FORCE_AURA: _row(TIDAL_FORCE_AURA, **_mod(1, 108, SPELLMOD_DURATION, 49, (0, 0, D2_HEALING_RAIN)),
                                   **_mod(2, 108, SPELLMOD_DAMAGE_MULTIPLIER, 66, (D0_CH, 0, 0))),
            TIDAL_FORCE_STACK: _row(TIDAL_FORCE_STACK, EffectAura_1=283, EffectBasePoints_1=4, CumulativeAura=3),
            TIDAL_FORCE_ECHO: _row(TIDAL_FORCE_ECHO, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS),
        }
        for rank, v in zip(TIDAL_MASTERY, (3000, 6000, 9000)):
            rows[rank] = _row(rank, **_mod(1, 107, SPELLMOD_COOLDOWN, -v - 1, (0, 0, D2_TIDAL_FORCE_CAST)))
        entries = {TIDAL_FORCE_AURA: {"duration_ms": 10000}, TIDAL_FORCE_STACK: {"duration_ms": 8000}}
        return rows, entries

    def test_tidal_force(self):
        rows, entries = self._tf()
        self.assertEqual(check_tidal_force(rows, entries), [])

        def bad(**cast_over):
            r = dict(rows)
            r[TIDAL_FORCE_CAST] = dict(rows[TIDAL_FORCE_CAST], **cast_over)
            return len(check_tidal_force(r, entries))
        self.assertEqual(bad(RecoveryTime=60000), 1)
        self.assertEqual(bad(StartRecoveryTime=1500), 1)
        self.assertEqual(bad(StartRecoveryCategory=133), 1)
        self.assertEqual(bad(SpellClassMask_3=0), 1)
        self.assertEqual(bad(ManaCostPct=5), 1)
        self.assertEqual(len(check_tidal_force(rows, {**entries, TIDAL_FORCE_AURA: {"duration_ms": 15000}})), 1)
        self.assertEqual(len(check_tidal_force(rows, {**entries, TIDAL_FORCE_STACK: {"duration_ms": 15000}})), 1)
        self.assertEqual(len(check_tidal_force({**rows, TIDAL_FORCE_STACK: _row(TIDAL_FORCE_STACK, EffectAura_1=3, CumulativeAura=3)},
                                               entries)), 1)
        self.assertEqual(len(check_tidal_force({**rows, TIDAL_FORCE_STACK: dict(rows[TIDAL_FORCE_STACK], CumulativeAura=1)},
                                               entries)), 1)
        self.assertEqual(len(check_tidal_force({**rows, TIDAL_FORCE_STACK: dict(rows[TIDAL_FORCE_STACK], EffectSpellClassMaskA_1=D0_HW)},
                                               entries)), 1)
        self.assertEqual(len(check_tidal_force({**rows, TIDAL_FORCE_ECHO: _row(TIDAL_FORCE_ECHO)}, entries)), 1)
        self.assertEqual(len(check_tidal_force({**rows, TIDAL_MASTERY[1]: _row(TIDAL_MASTERY[1])}, entries)), 1)
        self.assertEqual(len(check_tidal_force({k: v for k, v in rows.items() if k != TIDAL_FORCE_AURA}, entries)), 1)
        wrong_ch = dict(rows[TIDAL_FORCE_AURA], EffectBasePoints_2=20)
        self.assertEqual(len(check_tidal_force({**rows, TIDAL_FORCE_AURA: wrong_ch}, entries)), 1)

    def _tw(self):
        buff = _row(TW_BUFF, CumulativeAura=3, **_mod(1, 108, SPELLMOD_CAST_TIME, -11, (D0_HW, 0, 0)),
                    **_mod(2, 107, SPELLMOD_CRIT, 9, (D0_LHW, 0, 0)))
        rows = {TW_BUFF: buff, **{r: _row(r, ProcTypeMask=0, ProcChance=0) for r in TW_RANKS}}
        return rows, {TW_BUFF: {"duration_ms": 15000}}

    def test_tidal_waves(self):
        rows, entries = self._tw()
        self.assertEqual(check_tidal_waves(rows, entries), [])
        self.assertEqual(len(check_tidal_waves({**rows, 51562: _row(51562, ProcTypeMask=0x4, ProcChance=33)}, entries)), 1)
        self.assertEqual(len(check_tidal_waves({**rows, TW_BUFF: dict(rows[TW_BUFF], CumulativeAura=5)}, entries)), 1)
        self.assertEqual(len(check_tidal_waves(rows, {TW_BUFF: {"duration_ms": 8000}})), 1)
        self.assertEqual(len(check_tidal_waves({**rows, TW_BUFF: dict(rows[TW_BUFF], SpellClassMask_1=D0_HW)}, entries)), 1)
        self.assertEqual(len(check_tidal_waves({**rows, TW_BUFF: dict(rows[TW_BUFF], AttributesEx3=ATTR3_DEATH_PERSISTENT)}, entries)), 1)
        self.assertEqual(len(check_tidal_waves({**rows, TW_BUFF: dict(rows[TW_BUFF], EffectBasePoints_1=-6)}, entries)), 1)
        self.assertEqual(len(check_tidal_waves({**rows, TW_BUFF: dict(rows[TW_BUFF], EffectSpellClassMaskB_1=0)}, entries)), 1)
        self.assertEqual(len(check_tidal_waves({k: v for k, v in rows.items() if k != TW_BUFF}, entries)), 1)

    def test_counters(self):
        persist = dict(AttributesEx3=ATTR3_DEATH_PERSISTENT, AttributesEx2=1)
        rows = {UNDULATION_COUNTER: _row(UNDULATION_COUNTER, CumulativeAura=3, **persist), IHS_COUNTER: _row(IHS_COUNTER, **persist)}
        self.assertEqual(check_counters(rows, {}), [])
        self.assertEqual(len(check_counters({**rows, UNDULATION_COUNTER: _row(UNDULATION_COUNTER, CumulativeAura=2, **persist)}, {})), 1)
        self.assertEqual(len(check_counters({**rows, IHS_COUNTER: _row(IHS_COUNTER)}, {})), 1)
        self.assertEqual(len(check_counters({IHS_COUNTER: rows[IHS_COUNTER]}, {})), 1)

    def _mt(self):
        rows = {MANA_TIDE: _row(MANA_TIDE, RecoveryTime=180000, SpellClassMask_1=D0_MANA_TIDE_SUMMON | D0_SUMMON_B29)}
        for rank, v in zip(RESTORATIVE, (10000, 20000, 30000)):
            rows[rank] = _row(rank, **_mod(1, 107, SPELLMOD_COOLDOWN, -v, (D0_MANA_TIDE_SUMMON, 0, 0)))
        return rows, {MANA_TIDE: {"duration_ms": 10000}}

    def test_mana_tide(self):
        rows, entries = self._mt()
        self.assertEqual(check_mana_tide(rows, entries), [])
        self.assertEqual(len(check_mana_tide(rows, {MANA_TIDE: {"duration_ms": 12000}})), 1)
        self.assertEqual(len(check_mana_tide({**rows, MANA_TIDE: dict(rows[MANA_TIDE], RecoveryTime=300000)}, entries)), 1)
        self.assertEqual(len(check_mana_tide({**rows, MANA_TIDE: dict(rows[MANA_TIDE], SpellClassMask_1=D0_SUMMON_B29)}, entries)), 1)
        self.assertEqual(len(check_mana_tide({**rows, MANA_TIDE: dict(rows[MANA_TIDE], SpellClassMask_1=D0_MANA_TIDE_SUMMON)}, entries)), 1)
        self.assertEqual(len(check_mana_tide({**rows, MANA_TIDE: dict(rows[MANA_TIDE], SpellClassMask_2=1)}, entries)), 1)
        self.assertEqual(len(check_mana_tide({**rows, MANA_TIDE: dict(rows[MANA_TIDE], ManaCost=100)}, entries)), 1)
        self.assertEqual(len(check_mana_tide({**rows, RESTORATIVE[0]: _row(RESTORATIVE[0])}, entries)), 1)
        self.assertEqual(len(check_mana_tide({}, entries)), 1)

    def _heals(self):
        entries, rows = {}, {}
        for sid, (total, t, bit) in HEAL_POTENCY.items():
            entries[sid] = {"effect1": {"_potency": {"total_potency": total, "t_seconds": t or 0.0, "spell_level": 30}}}
            masks = [0, 0, 0]
            masks[bit[0]] = bit[1]
            rows[sid] = _row(sid, SpellLevel=30, SpellClassMask_1=masks[0], SpellClassMask_2=masks[1], SpellClassMask_3=masks[2])
        rows[TORRENT_HEAL]["AttributesEx3"] = ATTR3_SUPPRESS_CASTER_PROCS
        return rows, entries

    def test_heal_rows(self):
        rows, entries = self._heals()
        self.assertEqual(check_heal_rows(rows, entries), [])
        self.assertEqual(len(check_heal_rows({**rows, TORRENT_HEAL: dict(rows[TORRENT_HEAL], AttributesEx3=0)}, entries)), 1)
        self.assertEqual(len(check_heal_rows({**rows, TORRENT_HEAL: dict(rows[TORRENT_HEAL], SpellClassMask_3=D2_TORRENT | 1)}, entries)), 1)
        self.assertEqual(len(check_heal_rows({**rows, UCT_HEAL: dict(rows[UCT_HEAL], SpellClassMask_3=D2_TORRENT)}, entries)), 1)
        self.assertEqual(len(check_heal_rows({**rows, UCT_HEAL: dict(rows[UCT_HEAL], SpellLevel=0)}, entries)), 1)
        self.assertEqual(len(check_heal_rows({**rows, NG_HEAL: dict(rows[NG_HEAL], SpellClassMask_3=0)}, entries)), 1)
        bad = {**entries, TIDE_HEAL: {"effect1": {"_potency": {"total_potency": 20.0, "t_seconds": 2.0}}}}
        self.assertEqual(len(check_heal_rows(rows, bad)), 1)
        bad_t = {**entries, UCT_HEAL: {"effect1": {"_potency": {"total_potency": 30.0, "t_seconds": 1.5}}}}
        self.assertEqual(len(check_heal_rows(rows, bad_t)), 1)
        self.assertEqual(len(check_heal_rows(rows, {**entries, UCT_HEAL: {}})), 1)
        self.assertEqual(len(check_heal_rows({k: v for k, v in rows.items() if k != PLACEMENT_HEAL}, entries)), 1)

    def test_uct_heal(self):
        good = _row(UCT_HEAL, EffectChainTargets_1=3, EffectChainAmplitude_1=0.6)
        self.assertEqual(check_uct_heal({UCT_HEAL: good}), [])
        self.assertEqual(check_uct_heal({UCT_HEAL: _row(UCT_HEAL, MaxTargets=3, EffectChainAmplitude_1=0.6)}), [])
        self.assertEqual(len(check_uct_heal({UCT_HEAL: dict(good, EffectChainTargets_1=2)})), 1)
        self.assertEqual(len(check_uct_heal({UCT_HEAL: dict(good, EffectChainAmplitude_1=0.5)})), 1)
        self.assertEqual(len(check_uct_heal({})), 1)

    def test_healing_rain(self):
        self.assertEqual(check_healing_rain({HEALING_RAIN_HEAL: _row(HEALING_RAIN_HEAL, Effect_1=10, Effect_2=6)}), [])
        self.assertEqual(len(check_healing_rain({HEALING_RAIN_HEAL: _row(HEALING_RAIN_HEAL, Effect_3=3)})), 1)
        self.assertEqual(len(check_healing_rain({HEALING_RAIN_HEAL: _row(HEALING_RAIN_HEAL, EffectAura_3=4)})), 1)
        self.assertEqual(len(check_healing_rain({})), 1)

    def test_script_sized_heals(self):
        rows = {CLOUDBURST_RELEASE: _row(CLOUDBURST_RELEASE, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS)}
        entries = {sid: {"effect1": {"_potency_excluded": "script-sized"}} for sid in POTENCY_EXCLUDED}
        self.assertEqual(check_script_sized_heals(rows, entries), [])
        self.assertEqual(len(check_script_sized_heals({CLOUDBURST_RELEASE: dict(rows[CLOUDBURST_RELEASE], SpellClassMask_3=D2_TORRENT)}, entries)), 1)
        self.assertEqual(len(check_script_sized_heals({CLOUDBURST_RELEASE: _row(CLOUDBURST_RELEASE)}, entries)), 1)
        self.assertEqual(len(check_script_sized_heals(rows, {**entries, TIDAL_FORCE_ECHO: {"effect1": {}}})), 1)
        self.assertEqual(len(check_script_sized_heals(rows, {**entries, BULWARK_SHIELD: {"effect1": {"_potency": {"total_potency": 5}}}})), 2)
        self.assertEqual(len(check_script_sized_heals({}, entries)), 1)

    def test_potency_levels(self):
        entries = {1: {"effect1": {"_potency": {"total_potency": 5}}}}
        self.assertEqual(check_potency_levels({1: _row(1, SpellLevel=30)}, entries, [1]), [])
        self.assertEqual(len(check_potency_levels({1: _row(1, SpellLevel=0)}, entries, [1])), 1)
        self.assertEqual(check_potency_levels({1: _row(1)}, {}, [1]), [])

    def test_hot_twins(self):
        def rank(i, dmg_mask, dot_mask, dot_bp=7):
            return _row(i, **_mod(1, 108, SPELLMOD_DAMAGE, 7, dmg_mask), **_mod(2, 108, SPELLMOD_DOT, dot_bp, dot_mask))
        riptide = (0, 0, D2_RIPTIDE)
        talents = {"T": (1, 2)}
        good = {1: rank(1, riptide, riptide), 2: rank(2, riptide, riptide)}
        self.assertEqual(check_hot_twins(good, talents), [])
        self.assertEqual(len(check_hot_twins({**good, 2: _row(2, **_mod(1, 108, SPELLMOD_DAMAGE, 7, riptide))}, talents)), 1)  # no twin
        self.assertEqual(len(check_hot_twins({**good, 2: rank(2, riptide, riptide, dot_bp=9)}, talents)), 1)  # value drift
        self.assertEqual(len(check_hot_twins({**good, 2: rank(2, riptide, (0, 0, D2_HEALING_RAIN))}, talents)), 1)  # other bits
        # a DAMAGE effect that only reaches direct heals needs no twin
        self.assertEqual(check_hot_twins({1: _row(1, **_mod(1, 108, SPELLMOD_DAMAGE, 7, (D0_CH, 0, 0)))}, {"T": (1,)}), [])
        self.assertEqual(len(check_hot_twins({1: good[1]}, talents)), 1)  # rank 2 not built

    def test_duplicate_effects(self):
        twin = _row(1, **_mod(1, 108, SPELLMOD_DAMAGE, 7, (D0_CH, 0, 0)), **_mod(2, 108, SPELLMOD_DAMAGE, 7, (D0_CH, 0, 0)))
        self.assertEqual(len(check_no_duplicate_effects({1: twin}, [1])), 1)
        fine = _row(1, **_mod(1, 108, SPELLMOD_DAMAGE, 7, (D0_CH, 0, 0)), **_mod(2, 108, SPELLMOD_DOT, 7, (D0_CH, 0, 0)))
        self.assertEqual(check_no_duplicate_effects({1: fine}, [1]), [])
        self.assertEqual(check_no_duplicate_effects({}, [1]), [])

    def test_raw_twins(self):
        entries = {1: {"effect3": {}, "raw_overrides": {"Effect_3": 6, "EffectAura_3": 8}}}
        self.assertEqual(len(check_raw_twins(entries, [1])), 2)
        self.assertEqual(check_raw_twins({1: {"effect1": {}, "raw_overrides": {"Effect_3": 6}}}, [1]), [])
        self.assertEqual(check_raw_twins({1: {"effect3": {}, "raw_overrides": {"EffectSpellClassMaskC_1": 4, "AttributesEx3": 1}}}, [1]), [])
        self.assertEqual(check_raw_twins({1: {"effect2": {}}}, [1]), [])

    def test_reincarnation(self):
        trainers = [{"TrainerId": 210, "SpellId": REINCARNATION, "ReqLevel": 15}]
        rows = {REINCARNATION: _row(REINCARNATION, SpellLevel=15, BaseLevel=15)}
        self.assertEqual(check_reincarnation(rows, trainers), [])
        self.assertEqual(len(check_reincarnation(rows, [dict(trainers[0], ReqLevel=30)])), 1)
        self.assertEqual(len(check_reincarnation(rows, [])), 1)
        self.assertEqual(len(check_reincarnation(rows, trainers + trainers)), 1)
        self.assertEqual(len(check_reincarnation(rows, trainers + [dict(trainers[0], TrainerId=14)])), 1)
        self.assertEqual(len(check_reincarnation({REINCARNATION: _row(REINCARNATION, SpellLevel=30, BaseLevel=15)}, trainers)), 1)
        self.assertEqual(len(check_reincarnation({}, trainers)), 1)

    def test_creatures(self):
        creatures = {300279: {"ScriptName": "npc_sha_undulating_currents_totem"}, 300280: {"ScriptName": ""},
                     300281: {"ScriptName": "npc_sha_spirit_link_totem"}, 300282: {"ScriptName": ""}}
        spells = [{"CreatureID": 300282, "Index": 0, "Spell": 5672}]
        self.assertEqual(check_creatures(creatures, spells), [])
        self.assertEqual(len(check_creatures(creatures, [])), 1)
        self.assertEqual(len(check_creatures(creatures, [dict(spells[0], Spell=1)])), 1)
        self.assertEqual(len(check_creatures({**creatures, 300280: {"ScriptName": "x"}}, spells)), 1)
        self.assertEqual(len(check_creatures({**creatures, 300281: {"ScriptName": ""}}, spells)), 1)
        self.assertEqual(len(check_creatures({k: v for k, v in creatures.items() if k != 300279}, spells)), 1)

    def test_no_cancel(self):
        good = {i: _row(i, Attributes=ATTR0_NO_AURA_CANCEL) for i in NO_CANCEL_IDS}
        self.assertEqual(check_no_cancel(good), [])
        self.assertEqual(len(check_no_cancel({**good, 202665: _row(202665, Attributes=0)})), 1)
        self.assertEqual(len(check_no_cancel({**good, 202662: _row(202662, Attributes=ATTR0_DO_NOT_DISPLAY)})), 1)
        self.assertEqual(len(check_no_cancel({202662: good[202662]})), 1)

    def test_blessing_of_the_eternals(self):
        good = {sid: _row(sid, EffectAura_1=AURA_MOD_CRIT_PCT, EffectBasePoints_1=bp, EffectAura_2=4)
                for sid, bp in BOTE_RANKS.items()}
        self.assertEqual(check_blessing_of_the_eternals(good), [])
        old = dict(good[51554], EffectAura_1=AURA_MOD_SPELL_CRIT_CHANCE)   # the stock spell-crit-only effect
        self.assertEqual(len(check_blessing_of_the_eternals({**good, 51554: old})), 1)
        double = dict(good[51554], EffectAura_3=AURA_MOD_SPELL_CRIT_CHANCE)   # a second crit effect double-counts
        self.assertEqual(len(check_blessing_of_the_eternals({**good, 51554: double})), 1)
        self.assertEqual(len(check_blessing_of_the_eternals({**good, 51555: dict(good[51555], EffectBasePoints_1=1)})), 1)
        self.assertEqual(len(check_blessing_of_the_eternals({**good, 51555: dict(good[51555], EffectAura_2=0)})), 1)
        self.assertEqual(len(check_blessing_of_the_eternals({51554: good[51554]})), 1)

    def test_id_map(self):
        self.assertEqual(check_id_map(set(S2A_IDS)), [])
        self.assertEqual(len(check_id_map(set(S2A_IDS) - {202660})), 1)
        self.assertEqual(len(check_id_map(set(S2A_IDS) | {202656})), 1)
        self.assertEqual(len(check_id_map(set(S2A_IDS) | {202683, 202700})), 2)
        self.assertEqual(check_id_map(set(S2A_IDS) | {202720}), [])

    def test_visible_buffs_reused(self):
        good = _row(202662, Attributes=0, Effect_1=6, AuraDescription_Lang_enUS="Healing increased.", Name_Lang_enUS="x")
        self.assertEqual(check_visible_buffs({202662: good}, [202662]), [])
        self.assertEqual(len(check_visible_buffs({202662: dict(good, AuraDescription_Lang_enUS="5% more")}, [202662])), 1)
        self.assertEqual(len(check_visible_buffs({202662: dict(good, AuraDescription_Lang_enUS="")}, [202662])), 1)

    def test_tooltip_vars_reused(self):
        good = [{"id": i, "Variables": "$ab=${1}"} for i in SDV_IDS]
        self.assertEqual(check_tooltip_vars(good, ids=SDV_IDS), [])
        self.assertEqual(len(check_tooltip_vars(good[1:], ids=SDV_IDS)), 1)
        self.assertEqual(len(check_tooltip_vars([{"id": 1220, "Variables": "$abcdefghijklm=${1}"}] + good[1:], ids=SDV_IDS)), 1)


if __name__ == "__main__":
    unittest.main()
