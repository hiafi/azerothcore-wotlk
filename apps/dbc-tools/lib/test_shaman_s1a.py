"""
Shaman S1a data gate (shaman-rework S1a-HANDOFF row A5, S1a-WP-BRIEF, S1-NOTES section 3).

Loads the real shaman DSL package and asserts on the BUILT rows (stock base + DSL + raw_overrides via
`build.build_spell_row`; the same recipe as test_shaman_sh0b), plus the declared talent / spell_group / tooltip-variable
tables and the generated ShamanData.h against the C++ that reads it. Each check is a pure function over rows or declared
entries so the negative fixtures can prove it fails on a minimal bad input.

Known exceptions that are NOT asserted (deliberate):
  - The three Overload copies 202591-93 carry the parent family bits (LB d0 b0, CL d0 b1, Lava Burst d1 b12) on purpose.
  - Only the OWN SpellClassMask is held to the FORBIDDEN_* bits. The EFFECT masks of a SpellMod / proc row are selectors
    (they name which spells the mod reaches), so rows such as Storm Empowerment legitimately select Lightning Bolt.
  - Thunderstorm rank 2 (202594) is stock-shaped on purpose: it is the same row as 51490 plus AttributesEx5 0x8.
  - The haste-group member rows of other classes (Rapid Fire, Dark Soul: Misery, Icy Veins) come from their own class
    packages, loaded here only to read the aura type they build to.

Run: apps/dbc-tools/.venv/bin/python3 -m pytest apps/dbc-tools/lib/test_shaman_s1a.py -q
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import build, dbcfmt, source, spell_tables, state, trainer_state  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.reuse import ReuseContext  # noqa: E402
from lib.test_shaman_sh0a import m, spell_mask, _hex, _u32  # noqa: E402
from lib.test_shaman_sh0b import _data as _shaman_data  # noqa: E402

TOOL_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = TOOL_ROOT.parents[1]
CLASSES_DIR = TOOL_ROOT / "source" / "classes"
HEADER = REPO_ROOT / "src" / "server" / "game" / "Entities" / "Unit" / "Generated" / "ShamanData.h"
CPP_FILES = (
    REPO_ROOT / "src/server/scripts/Spells/spell_shaman_elemental.cpp",
    REPO_ROOT / "src/server/scripts/Spells/spell_shaman_totems.cpp",
    REPO_ROOT / "src/server/scripts/Spells/shaman_hooks.cpp",
    REPO_ROOT / "src/server/scripts/Pet/pet_shaman_rework.cpp",
    REPO_ROOT / "src/server/game/Entities/Unit/ShamanMechanics.h",
    REPO_ROOT / "src/server/game/Entities/Unit/ShamanMechanics.cpp",
)

ELEMENTAL_TAB = 261
S1A_IDS = tuple(range(202520, 202596))
OVERLOAD_COPIES = {202591: (1, 0, 0), 202592: (2, 0, 0), 202593: (0, 0x1000, 0)}  # id -> parent own mask (LB, CL, LvB)
CLASS_SET = 11
ATTR3_NOT_A_PROC = 0x200
ATTR5_USABLE_WHILE_STUNNED = 0x8
ATTR6_IGNORE_CASTER_DAMAGE_MODIFIERS = 0x20000000
ATTR0_PASSIVE = 0x40
ATTR0_DO_NOT_DISPLAY = 0x80
FLAME_SHOCK_D0 = 0x10000000  # d0 b28
CALL_OF_FLAME_FORBIDDEN = (0x20000000, 0x00800000, 0)  # d0 b29, d1 b23
CALL_OF_FLAME_RANKS = (16038, 16160, 16161)
OATH_RANKS = (51466, 51470, 202536)
OATH_CLAUSE_D0 = 0x200800
THUNDERSTORM, THUNDERSTORM_RANK2 = 51490, 202594
EM_HASTE = 64701
CHAIN_LIGHTNING = 421
FROSTBRAND = 8033
STORM_EMPOWERMENT = 202563
CL_JUMP_CAP = 8
ICEFURY_CHARGES, LIGHTNING_MASTERY_BUFF = 202566, 202568
SPELLMOD_DOT = 22
APPLY_AURA_EFFECTS = (6, 27, 35)  # APPLY_AURA, APPLY_AREA_AURA_PARTY (27), APPLY_AREA_AURA_PARTY (35 here): aura carriers
AURA_ADD_FLAT_MODIFIER, AURA_ADD_PCT_MODIFIER = 107, 108
AURA_MOD_CASTING_SPEED_NOT_STACK, AURA_HASTE_ALL = 65, 193  # group 1122 / group 1258 aura types

# The 12 stock rank spells that fell off the 5->3 / 5->2 talent chains (S1a-0VERIFY).
DROPPED_RANKS = (16111, 16112, 16107, 16108, 16115, 16116, 60187, 60188, 16581, 16582, 62100, 62101)

# docs/reworks/shaman-elemental-rework.md section 4: (row, col) -> (talent name, ranks).
GRID = {
    (0, 0): ("Raze", 3), (0, 1): ("Convection", 3), (0, 2): ("Concussion", 3), (0, 3): ("Wind Rush", 3),
    (1, 0): ("Call of Flame", 3), (1, 1): ("Elemental Warding", 3), (1, 2): ("Elemental Devastation", 3),
    (2, 0): ("Reverberation", 3), (2, 1): ("Thunderstorm", 1), (2, 2): ("Elemental Fury", 3),
    (2, 3): ("Elemental Focus", 2),
    (3, 0): ("Rising Flames", 2), (3, 3): ("Eye of the Storm", 3),
    (4, 0): ("Elemental Reach", 2), (4, 1): ("Power of the Elements", 1), (4, 2): ("Call of Thunder", 3),
    (4, 3): ("Unrelenting Storm", 3),
    (5, 0): ("Elemental Precision", 3), (5, 2): ("Lightning Mastery", 3),
    (6, 1): ("Elemental Mastery", 1), (6, 2): ("Storm, Earth and Fire", 3),
    (7, 0): ("Booming Echoes", 3), (7, 1): ("Conduit of the Elements", 1), (7, 2): ("Lightning Overload", 3),
    (7, 3): ("Elemental Oath", 3),
    (8, 0): ("Astral Shift", 3), (8, 1): ("Icefury", 1), (8, 2): ("Lava Flows", 3), (8, 3): ("Fusion of Elements", 2),
    (9, 1): ("Shamanism", 3),
    (10, 1): ("Call of the Elements", 1),
}
EMPTY_CELLS = ((1, 3), (3, 1), (3, 2), (5, 1), (5, 3), (6, 0), (6, 3), (9, 0), (9, 2), (9, 3), (10, 0), (10, 2), (10, 3))

# Stock / stock-rewritten rows S1a edits besides the 202520-202595 block (present ones are checked).
REWRITTEN_STOCK = (403, 421, 1535, 8349, 8042, 8050, 8056, 16166, 16246, 51490, 51505, 57994, 64694, 64701, 65263, 65264,
                   29177, 29178)

# Group membership as the live DB holds it before the DSL: spell_group 1122 (stock "spell casting speed" group).
STOCK_GROUPS = {1122: {2825, 10060, 32182}, 1258: set()}
HASTE_GROUPS = {
    1122: ({10060, 12472, 64701}, AURA_MOD_CASTING_SPEED_NOT_STACK),
    1258: ({26297, 3045, 200732}, AURA_HASTE_ALL),
}
RULE_EXCLUSIVE_SAME_EFFECT = 3
SDV_IDS = tuple(range(1210, 1217))
SDV_NAME_MAX = 12
SDV_TEXT_MAX = 1024


# ---- checks (pure: take built rows / declared entries, return problem strings) -----------------------------

def check_grid(talents: list[dict], names: dict[int, str], expected=GRID, empty=EMPTY_CELLS) -> list[str]:
    """Every tab-261 talent sits in a documented cell with the documented name and rank count, and nothing else."""
    bad = []
    seen = {}
    for t in talents:
        if int(t["tab_id"]) != ELEMENTAL_TAB:
            continue
        cell = (int(t["tier"]), int(t["column"]))
        if cell in seen:
            bad.append(f"talent {t['id']}: cell {cell} also holds talent {seen[cell]}")
        seen[cell] = t["id"]
        want = expected.get(cell)
        ranks = list(t["rank_spell_ids"])
        if want is None:
            bad.append(f"talent {t['id']}: undocumented cell {cell}")
            continue
        got = names.get(ranks[0])
        if got != want[0]:
            bad.append(f"talent {t['id']} at {cell}: name {got!r}, expected {want[0]!r}")
        if len(ranks) != want[1]:
            bad.append(f"talent {t['id']} {want[0]}: {len(ranks)} ranks, expected {want[1]}")
    bad += [f"cell {cell}: {want[0]} missing" for cell, want in expected.items() if cell not in seen]
    bad += [f"cell {cell}: should be empty, holds talent {seen[cell]}" for cell in empty if cell in seen]
    total = sum(int(len(t["rank_spell_ids"])) for t in talents if int(t["tab_id"]) == ELEMENTAL_TAB)
    want_pts = sum(r for _n, r in expected.values())
    if len(seen) != len(expected) or total != want_pts:
        bad.append(f"tab 261 holds {len(seen)} talents / {total} points, expected {len(expected)} / {want_pts}")
    return bad


def check_rank_levels(talents: list[dict], levels: dict[int, int]) -> list[str]:
    """Rank SpellLevels never decrease along a chain and stay within the level cap."""
    bad = []
    for t in talents:
        if int(t["tab_id"]) != ELEMENTAL_TAB:
            continue
        chain = [levels.get(r, 0) for r in t["rank_spell_ids"]]
        if chain != sorted(chain) or any(lv > 80 for lv in chain):
            bad.append(f"talent {t['id']}: rank levels {chain} are not ascending within 1..80")
    return bad


def check_no_depends_on(talents: list[dict]) -> list[str]:
    return [f"talent {t['id']}: depends_on {t['depends_on']!r} on tab 261" for t in talents
            if int(t["tab_id"]) == ELEMENTAL_TAB and t.get("depends_on")]


def check_dropped_ranks(talents: list[dict], dropped=DROPPED_RANKS) -> list[str]:
    ranks = {r: t["id"] for t in talents for r in t["rank_spell_ids"]}
    return [f"dropped rank {r} still in talent {ranks[r]}" for r in dropped if r in ranks]


def check_equipped_item_class(rows: dict[int, dict], ids) -> list[str]:
    return [f"{i}: EquippedItemClass {rows[i].get('EquippedItemClass')!r}, expected -1"
            for i in ids if i in rows and _u32(rows[i].get("EquippedItemClass")) != 0xFFFFFFFF]


def check_forbidden_bits(rows: dict[int, dict], ids=S1A_IDS, allow=tuple(OVERLOAD_COPIES)) -> list[str]:
    bad = []
    for i in ids:
        if i not in rows or i in allow:
            continue
        mask = spell_mask(rows[i])
        hit = (mask[0] & m.FORBIDDEN_D0, mask[1] & m.FORBIDDEN_D1, mask[2] & m.FORBIDDEN_D2)
        if any(hit):
            bad.append(f"{i}: SpellClassMask {_hex(mask)} holds forbidden bits {_hex(hit)}")
    return bad


def check_overload_copies(rows: dict[int, dict], parents=OVERLOAD_COPIES) -> list[str]:
    bad = []
    for i, parent_mask in parents.items():
        row = rows.get(i)
        if row is None:
            bad.append(f"{i}: copy not built")
            continue
        if spell_mask(row) != parent_mask:
            bad.append(f"{i}: SpellClassMask {_hex(spell_mask(row))}, expected the parent bits {_hex(parent_mask)}")
        if int(row.get("SpellClassSet") or 0) != CLASS_SET:
            bad.append(f"{i}: SpellClassSet {row.get('SpellClassSet')}, expected {CLASS_SET}")
        if _u32(row.get("AttributesEx3")) & ATTR3_NOT_A_PROC:
            bad.append(f"{i}: carries NOT_A_PROC (AttributesEx3 0x200)")
        if _u32(row.get("AttributesEx6")) & ATTR6_IGNORE_CASTER_DAMAGE_MODIFIERS:
            bad.append(f"{i}: carries ATTR6_IGNORE_CASTER_DAMAGE_MODIFIERS (copies keep the caster's damage mods)")
    return bad


def check_em_haste(rows: dict[int, dict]) -> list[str]:
    row = rows.get(EM_HASTE)
    if row is None:
        return [f"{EM_HASTE}: not built"]
    bad = []
    mask = spell_mask(row)
    if int(row.get("SpellClassSet") or 0) != CLASS_SET:
        bad.append(f"{EM_HASTE}: SpellClassSet {row.get('SpellClassSet')}, expected {CLASS_SET}")
    if mask[2] != m.EM_HASTE:
        bad.append(f"{EM_HASTE}: SpellClassMask_3 {mask[2]:#x}, expected EM_HASTE {m.EM_HASTE:#x}")
    if mask[0] or mask[1]:
        bad.append(f"{EM_HASTE}: SpellClassMask d0/d1 {_hex(mask)} must be 0")
    return bad


def check_thunderstorm(rows: dict[int, dict]) -> list[str]:
    bad = []
    r1, r2 = rows.get(THUNDERSTORM), rows.get(THUNDERSTORM_RANK2)
    if r1 is not None and _u32(r1.get("AttributesEx5")) & ATTR5_USABLE_WHILE_STUNNED:
        bad.append(f"{THUNDERSTORM}: carries AttributesEx5 0x8 (usable while stunned belongs to rank 2 only)")
    if r2 is None:
        bad.append(f"{THUNDERSTORM_RANK2}: not built")
    elif not _u32(r2.get("AttributesEx5")) & ATTR5_USABLE_WHILE_STUNNED:
        bad.append(f"{THUNDERSTORM_RANK2}: lacks AttributesEx5 0x8")
    return bad


def _effect_masks(row: dict):
    for e in (1, 2, 3):
        yield f"effect {e}", tuple(_u32(row.get(f"EffectSpellClassMask{'ABC'[e - 1]}_{n}")) for n in (1, 2, 3))


def check_call_of_flame_masks(rows: dict[int, dict], ids=CALL_OF_FLAME_RANKS, forbid=CALL_OF_FLAME_FORBIDDEN) -> list[str]:
    bad = []
    for i in ids:
        row = rows.get(i)
        if row is None:
            continue
        for label, mask in [("SpellClassMask", spell_mask(row))] + list(_effect_masks(row)):
            hit = tuple(mask[n] & forbid[n] for n in range(3))
            if any(hit):
                bad.append(f"{i}: {label} {_hex(mask)} holds Call of Flame forbidden bits {_hex(hit)} (d0 b29 / d1 b23)")
    return bad


def _effect_value(row: dict, effect: int) -> int:
    """Level-1 flat value of an effect with DieSides <= 1: BasePoints + 1."""
    return int(row.get(f"EffectBasePoints_{effect}") or 0) + 1


def check_chain_lightning_jumps(rows: dict[int, dict], cap=CL_JUMP_CAP) -> list[str]:
    cl, fb, storm = rows.get(CHAIN_LIGHTNING), rows.get(FROSTBRAND), rows.get(STORM_EMPOWERMENT)
    if None in (cl, fb, storm):
        return [f"jump inputs not built: CL {cl is not None}, Frostbrand {fb is not None}, Storm {storm is not None}"]
    bad = []
    stock_jumps = int(cl.get("EffectChainTargets_1") or 0)
    # Frostbrand: its SPELLMOD_JUMP_TARGETS effect; Storm Empowerment: effect 2 (ADD_FLAT_MODIFIER misc 17).
    fb_jumps = sum(_effect_value(fb, e) for e in (1, 2, 3)
                   if int(fb.get(f"EffectAura_{e}") or 0) == AURA_ADD_FLAT_MODIFIER
                   and int(fb.get(f"EffectMiscValue_{e}") or 0) == 17)
    storm_jumps = sum(_effect_value(storm, e) for e in (1, 2, 3)
                      if int(storm.get(f"EffectAura_{e}") or 0) == AURA_ADD_FLAT_MODIFIER
                      and int(storm.get(f"EffectMiscValue_{e}") or 0) == 17)
    if not fb_jumps:
        bad.append(f"{FROSTBRAND}: no SPELLMOD_JUMP_TARGETS effect found")
    if not storm_jumps:
        bad.append(f"{STORM_EMPOWERMENT}: no SPELLMOD_JUMP_TARGETS effect found")
    total = stock_jumps + fb_jumps + storm_jumps
    if total > cap:
        bad.append(f"Chain Lightning jumps {stock_jumps} + Frostbrand {fb_jumps} + Storm {storm_jumps} = {total} > {cap}")
    return bad


def check_icefury_charges(rows: dict[int, dict], consts: list[dict]) -> list[str]:
    row = rows.get(ICEFURY_CHARGES)
    bad = []
    if row is None:
        return [f"{ICEFURY_CHARGES}: not built"]
    if int(row.get("ProcCharges") or 0) != 3:
        bad.append(f"{ICEFURY_CHARGES}: ProcCharges {row.get('ProcCharges')}, expected 3")
    have = {c["name"]: c["value"] for c in consts}
    if have.get("ICEFURY_MAX_CHARGES") != 3:
        bad.append(f"const ICEFURY_MAX_CHARGES {have.get('ICEFURY_MAX_CHARGES')!r}, expected 3")
    return bad


def check_lightning_mastery_duration(entries: dict[int, dict]) -> list[str]:
    e = entries.get(LIGHTNING_MASTERY_BUFF)
    if e is None:
        return [f"{LIGHTNING_MASTERY_BUFF}: not declared"]
    return [] if int(e.get("duration_ms") or 0) == 8000 else [
        f"{LIGHTNING_MASTERY_BUFF}: duration_ms {e.get('duration_ms')}, expected 8000"]


# 2026-10-20 smoke-test fix pass: summon cost 8%, Lightning Mastery 7% per stack, Icefury refund 5% in every window,
# and the rough damage cut (S1-FIX-REPORT table). (spell id, effect index in `entries_by_id`'s effectN, total potency)
FIX_PASS_SUMMONS = (2062, 2894, 202272, 202273)
FIX_PASS_POTENCY = (
    (51505, 1, 57.6), (403, 1, 126.0), (421, 1, 79.6), (8042, 2, 60.0), (8050, 1, 32.3), (8050, 2, 10.8),
    (8056, 2, 32.3), (202281, 1, 21.5), (202282, 1, 43.0), (202276, 1, 43.0), (202278, 1, 51.6),
    (202270, 1, 10.8), (8349, 1, 104.1),
)


def check_fix_pass(rows: dict[int, dict], entries: dict[int, dict], consts: list[dict]) -> list[str]:
    bad = []
    for sid in FIX_PASS_SUMMONS:
        row = rows.get(sid)
        if row is None or int(row.get("ManaCostPct") or 0) != 8:
            bad.append(f"{sid}: ManaCostPct {row.get('ManaCostPct') if row else None!r}, expected 8")
    have = {c["name"]: c["value"] for c in consts}
    for name, want in (("LM_CHANCE_PER_STACK", 7), ("ICEFURY_MANA_PCT", 5)):
        if have.get(name) != want:
            bad.append(f"const {name} {have.get(name)!r}, expected {want}")
    if "ICEFURY_WATER_MANA_PCT" in have:
        bad.append("const ICEFURY_WATER_MANA_PCT still declared (renamed ICEFURY_MANA_PCT)")
    for sid, effect, want in FIX_PASS_POTENCY:
        pot = ((entries.get(sid) or {}).get(f"effect{effect}") or {}).get("_potency") or {}
        if pot.get("total_potency") != want:
            bad.append(f"{sid}: effect {effect} total potency {pot.get('total_potency')!r}, expected {want}")
    return bad


# 2026-10-20 Earth Shock burst (user): Echo lasts 30 s and adds +30% Earth Shock damage per stack (stored 29; the +10%
# crit damage bonus stays stored 9), the Earth Elemental summon grants 5 Echo, Earth Shock potency 32.3 -> 45.
ECHO_BUFF = 202565
EARTH_SHOCK = 8042


def check_earth_shock_burst(rows: dict[int, dict], entries: dict[int, dict], consts: list[dict]) -> list[str]:
    bad = []
    row = rows.get(ECHO_BUFF)
    if row is None:
        bad.append(f"{ECHO_BUFF}: not built")
    else:
        for col, want in (("EffectBasePoints_1", 29), ("EffectBasePoints_2", 9)):
            if int(row.get(col) or 0) != want:
                bad.append(f"{ECHO_BUFF}: {col} {row.get(col)!r}, expected {want}")
    entry = entries.get(ECHO_BUFF)
    if entry is None or int(entry.get("duration_ms") or 0) != 30000:
        bad.append(f"{ECHO_BUFF}: duration_ms {(entry or {}).get('duration_ms')!r}, expected 30000")
    have = {c["name"]: c["value"] for c in consts}
    for name, want in (("ECHO_DURATION_MS", 30000), ("ECHO_EARTH_ELEMENTAL_GRANT", 5), ("ECHO_MAX", 10)):
        if have.get(name) != want:
            bad.append(f"const {name} {have.get(name)!r}, expected {want}")
    pot = ((entries.get(EARTH_SHOCK) or {}).get("effect2") or {}).get("_potency") or {}
    if pot.get("total_potency") != 60.0:
        bad.append(f"{EARTH_SHOCK}: effect 2 total potency {pot.get('total_potency')!r}, expected 60.0")
    return bad


def effective_group(group_id: int, adds: list[dict], removals: list[dict], stock=STOCK_GROUPS) -> set[int]:
    members = set(stock.get(group_id, set()))
    members -= {int(r["spell_id"]) for r in removals if int(r["id"]) == group_id}
    members |= {int(a["spell_id"]) for a in adds if int(a["id"]) == group_id}
    return members


def check_haste_groups(adds: list[dict], removals: list[dict], rules: list[dict], member_rows: dict[int, dict],
                       groups=HASTE_GROUPS) -> list[str]:
    bad = []
    for gid, (want, aura) in groups.items():
        got = effective_group(gid, adds, removals)
        if got != want:
            bad.append(f"group {gid}: members {sorted(got)}, expected {sorted(want)}")
        declared = [r for r in rules if int(r["group_id"]) == gid]
        if gid == 1258 and not any(int(r["stack_rule"]) == RULE_EXCLUSIVE_SAME_EFFECT for r in declared):
            bad.append(f"group {gid}: no stack rule 3 declared")
        for r in declared:
            if int(r["stack_rule"]) != RULE_EXCLUSIVE_SAME_EFFECT:
                bad.append(f"group {gid}: stack rule {r['stack_rule']}, expected 3")
        for member in sorted(got):
            row = member_rows.get(member)
            if row is None:
                bad.append(f"group {gid}: member {member} has no row to read its aura type from")
            elif aura not in {int(row.get(f"EffectAura_{n}") or 0) for n in (1, 2, 3)}:
                auras = [int(row.get(f"EffectAura_{n}") or 0) for n in (1, 2, 3)]
                bad.append(f"group {gid}: member {member} carries auras {auras}, none is {aura}")
    for gone in (2825, 32182):
        if gone in effective_group(1122, adds, removals):
            bad.append(f"group 1122: still holds {gone} (Bloodlust / Heroism must leave)")
    return bad


def check_visible_buffs(rows: dict[int, dict], ids=S1A_IDS) -> list[str]:
    """Visible (non-passive, non-hidden) aura buffs need a non-empty aura description with no digit."""
    bad = []
    for i in ids:
        row = rows.get(i)
        if row is None:
            continue
        attrs = _u32(row.get("Attributes"))
        if attrs & (ATTR0_PASSIVE | ATTR0_DO_NOT_DISPLAY):
            continue
        if not any(int(row.get(f"Effect_{n}") or 0) in APPLY_AURA_EFFECTS for n in (1, 2, 3)):
            continue
        text = (row.get("AuraDescription_Lang_enUS") or "").strip()
        if not text:
            bad.append(f"{i} ({row.get('Name_Lang_enUS')}): visible buff has no aura description")
        elif re.search(r"\d", text):
            bad.append(f"{i} ({row.get('Name_Lang_enUS')}): aura description {text!r} contains a digit")
    return bad


def check_tooltip_vars(tooltip_vars: list[dict], ids=SDV_IDS, name_max=SDV_NAME_MAX, text_max=SDV_TEXT_MAX) -> list[str]:
    by_id = {int(v["id"]): v for v in tooltip_vars}
    bad = []
    for i in ids:
        v = by_id.get(i)
        if v is None:
            bad.append(f"SpellDescriptionVariables {i}: not declared")
            continue
        text = v["Variables"]
        if len(text) > text_max:
            bad.append(f"SDV {i}: {len(text)} chars, over {text_max}")
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            name = line.split("=", 1)[0].strip()
            if "=" not in line or not name.startswith("$"):
                bad.append(f"SDV {i}: malformed entry {line[:40]!r}")
            elif len(name.lstrip("$")) > name_max:
                bad.append(f"SDV {i}: variable name {name!r} is longer than {name_max} characters")
    return bad


def check_oath_clause_gone(rows: dict[int, dict], scripts_removed: list[dict]) -> list[str]:
    bad = []
    for i in OATH_RANKS:
        row = rows.get(i)
        if row is None:
            bad.append(f"{i}: Oath rank not built")
            continue
        if int(row.get("EffectBasePoints_2") or 0) or int(row.get("EffectDieSides_2") or 0) > 1:
            bad.append(f"{i}: effect idx 1 carries damage values (bp {row.get('EffectBasePoints_2')}, "
                       f"die {row.get('EffectDieSides_2')}): the Clearcasting clause is back")
        for label, mask in _effect_masks(row):
            if label == "effect 2" and mask[0] & OATH_CLAUSE_D0:
                bad.append(f"{i}: {label} mask {_hex(mask)} holds the Clearcasting clause bits {OATH_CLAUSE_D0:#x}")
    clear = rows.get(16246)
    if clear is None:
        bad.append("16246: Clearcasting not built")
    else:
        if int(clear.get("Effect_2") or 0):
            bad.append(f"16246: Clearcasting still has effect idx 1 (Effect_2 {clear.get('Effect_2')})")
        if int(clear.get("Effect_3") or 0):
            bad.append(f"16246: Clearcasting has effect idx 2 (Effect_3 {clear.get('Effect_3')})")
    if not any(int(r["spell_id"]) == 16246 and r["ScriptName"] == "spell_sha_clearcasting" for r in scripts_removed):
        bad.append("16246: spell_sha_clearcasting is not unbound")
    return bad


DOT_TALENTS = {"Concussion": (16035, 16105, 16106), "Convection": (16039, 16109, 16110),
               "Booming Echoes": (63370, 63372, 202535), "Storm, Earth and Fire": (51483, 51485, 51486)}


def check_flame_shock_dots(rows: dict[int, dict], talents=DOT_TALENTS) -> list[str]:
    bad = []
    for name, ranks in talents.items():
        for i in ranks:
            row = rows.get(i)
            if row is None:
                bad.append(f"{name} {i}: not built")
                continue
            hit = any(int(row.get(f"EffectAura_{e}") or 0) in (AURA_ADD_FLAT_MODIFIER, AURA_ADD_PCT_MODIFIER)
                      and int(row.get(f"EffectMiscValue_{e}") or 0) == SPELLMOD_DOT
                      and mask[0] & FLAME_SHOCK_D0
                      for e, (_label, mask) in zip((1, 2, 3), _effect_masks(row)))
            if not hit:
                bad.append(f"{name} {i}: no SPELLMOD_DOT effect reaching Flame Shock (d0 {FLAME_SHOCK_D0:#x})")
    return bad


def parse_cpp_names(texts: dict[str, str]) -> dict[str, set[str]]:
    """ShamanData::NAME references per file."""
    return {f: set(re.findall(r"\bShamanData::([A-Za-z_][A-Za-z0-9_]*)", t)) for f, t in texts.items()}


def check_header_names(used: dict[str, set[str]], header: str) -> list[str]:
    defined = set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\b\s*(?:=|\[[^\]]*\]\s*=|\{)", header))
    bad = []
    for f, names in sorted(used.items()):
        bad += [f"{f}: ShamanData::{n} is not defined in ShamanData.h" for n in sorted(names - defined)]
    return bad


# ---- real data ----------------------------------------------------------------------------------------------

_S1A: dict = {}


def _class_member_rows(class_dirs=("hunter", "warlock", "mage"), wanted=(3045, 200732, 12472)) -> dict[int, dict]:
    """Built rows of the non-shaman haste-group members, from their own class packages (stock when undeclared)."""
    ids_cfg = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
    sti = spell_tables.load_spell_table_index()
    cti = spell_tables.load_creature_table_index()
    out = {}
    stock = state.load_stock_rows(dbcfmt.SPELL)
    for name in class_dirs:
        package = registry.load_class_package(
            CLASSES_DIR / name, ids_cfg=ids_cfg, trainer_index=trainer_state.load_trainer_index(),
            existing_group_ids={key[0] for key in sti.live_keys("spell_group")},
            shapeshift_index=state.load_stock_rows(dbcfmt.SPELLSHAPESHIFTFORM),
            existing_creature_rows={int(r["entry"]): r for r in cti.live_rows("creature_template")},
            creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
            creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS,
            live_data=spell_tables.load_dsl_live_data(),
        )
        reuse = ReuseContext({}, ids_cfg)
        for e in package.spells:
            if int(e["id"]) in wanted:
                out[int(e["id"])] = build.build_spell_row(e, reuse)
    for i in wanted:
        if i not in out and i in stock:
            out[i] = stock[i]
    return out


def _data():
    d = _shaman_data()
    if not _S1A:
        stock = d["stock"]
        names = {}
        levels = {}
        for t in d["package"].talents:
            for r in t["rank_spell_ids"]:
                row = d["rows_by_id"].get(r) or stock.get(r) or {}
                names[r] = row.get("Name_Lang_enUS")
                levels[r] = int(row.get("SpellLevel") or 0)
        members = _class_member_rows()
        for i in (10060, 64701, 26297):
            members[i] = d["rows_by_id"].get(i) or stock[i]
        _S1A.update(names=names, levels=levels, members=members)
    return {**d, **_S1A}


def _s1a_equipped_ids(d) -> list[int]:
    talent_ranks = [r for t in d["package"].talents if int(t["tab_id"]) == ELEMENTAL_TAB for r in t["rank_spell_ids"]]
    return sorted(set(S1A_IDS) | set(talent_ranks) | set(REWRITTEN_STOCK))


class ShamanS1aDataTest(unittest.TestCase):
    def assertClean(self, problems: list[str]):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_s1a_block_is_declared(self):
        # Id map of the WP brief: 202520-202536 (rank spells, castables, markers), 202560-202595 (buffs, copies, ranks);
        # 202537-202559 and 202596+ are unused spares.
        want = set(range(202520, 202537)) | set(range(202560, 202596))
        have = {i for i in _data()["rows_by_id"] if 202520 <= i <= 202639}
        self.assertEqual(sorted(want - have), [], "S1a ids not declared")
        self.assertEqual(sorted(have - want), [], "ids declared outside the S1a id map")

    def test_grid(self):
        d = _data()
        self.assertClean(check_grid(d["package"].talents, d["names"]))

    def test_rank_levels(self):
        d = _data()
        self.assertClean(check_rank_levels(d["package"].talents, d["levels"]))

    def test_no_depends_on_on_elemental_tab(self):
        self.assertClean(check_no_depends_on(_data()["package"].talents))

    def test_dropped_ranks_gone(self):
        self.assertClean(check_dropped_ranks(_data()["package"].talents))

    def test_equipped_item_class(self):
        d = _data()
        self.assertClean(check_equipped_item_class(d["rows_by_id"], _s1a_equipped_ids(d)))

    def test_no_forbidden_bits_on_new_rows(self):
        self.assertClean(check_forbidden_bits(_data()["rows_by_id"]))

    def test_overload_copies(self):
        self.assertClean(check_overload_copies(_data()["rows_by_id"]))

    def test_elemental_mastery_haste(self):
        self.assertClean(check_em_haste(_data()["rows_by_id"]))

    def test_thunderstorm_ranks(self):
        self.assertClean(check_thunderstorm(_data()["rows_by_id"]))

    def test_call_of_flame_masks(self):
        d = _data()
        self.assertClean(check_call_of_flame_masks(d["rows_by_id"]))
        # No S1a-minted Call of Flame row either.
        named = [i for i in S1A_IDS if i in d["rows_by_id"] and d["rows_by_id"][i].get("Name_Lang_enUS") == "Call of Flame"]
        self.assertClean(check_call_of_flame_masks(d["rows_by_id"], ids=named))

    def test_chain_lightning_jump_sum(self):
        self.assertClean(check_chain_lightning_jumps(_data()["rows_by_id"]))

    def test_icefury_charges(self):
        d = _data()
        self.assertClean(check_icefury_charges(d["rows_by_id"], d["package"].consts))

    def test_lightning_mastery_duration(self):
        self.assertClean(check_lightning_mastery_duration(_data()["entries_by_id"]))

    def test_smoke_test_fix_pass_values(self):
        d = _data()
        self.assertClean(check_fix_pass(d["rows_by_id"], d["entries_by_id"], d["package"].consts))

    def test_earth_shock_burst(self):
        d = _data()
        self.assertClean(check_earth_shock_burst(d["rows_by_id"], d["entries_by_id"], d["package"].consts))

    def test_haste_groups(self):
        d = _data()
        p = d["package"]
        self.assertClean(check_haste_groups(p.spell_groups, p.spell_group_removals, p.spell_group_rules, d["members"]))

    def test_visible_buffs_have_number_free_aura_text(self):
        self.assertClean(check_visible_buffs(_data()["rows_by_id"]))

    def test_tooltip_variables(self):
        self.assertClean(check_tooltip_vars(_data()["package"].tooltip_vars))

    def test_oath_has_no_clearcasting_clause(self):
        d = _data()
        self.assertClean(check_oath_clause_gone(d["rows_by_id"], d["package"].script_removals))

    def test_flame_shock_dot_effects(self):
        self.assertClean(check_flame_shock_dots(_data()["rows_by_id"]))

    def test_cpp_shaman_data_names_exist(self):
        texts = {p.name: p.read_text() for p in CPP_FILES}
        used = parse_cpp_names(texts)
        self.assertGreater(sum(len(v) for v in used.values()), 50, "suspiciously few ShamanData:: references parsed")
        self.assertClean(check_header_names(used, HEADER.read_text()))


# ---- negative fixtures: every check must fire on a minimal bad input ---------------------------------------

def _row(spell_id=1, **cols) -> dict:
    return {"ID": spell_id, **cols}


def _talent(tid, tier, col, ranks, tab=ELEMENTAL_TAB, depends_on=None):
    return {"id": tid, "tab_id": tab, "tier": tier, "column": col, "rank_spell_ids": list(ranks), "depends_on": depends_on}


def _good_grid():
    talents, names = [], {}
    for n, ((tier, col), (name, ranks)) in enumerate(GRID.items()):
        ids = [1000 + n * 10 + k for k in range(ranks)]
        talents.append(_talent(n + 1, tier, col, ids))
        names[ids[0]] = name
    return talents, names


class ShamanS1aNegativeTest(unittest.TestCase):
    def test_grid(self):
        talents, names = _good_grid()
        self.assertEqual(check_grid(talents, names), [])
        self.assertEqual(sum(len(t["rank_spell_ids"]) for t in talents), 77)
        self.assertEqual(len(talents), 31)
        # a talent in an empty cell, plus the point total no longer matching
        self.assertTrue(check_grid(talents + [_talent(99, 1, 3, [5000])], {**names, 5000: "X"}))
        # a missing talent
        self.assertTrue(any("missing" in p for p in check_grid(talents[1:], names)))
        # wrong rank count
        wrong = [dict(talents[0], rank_spell_ids=[1000, 1001])] + talents[1:]
        self.assertTrue(any("ranks, expected" in p for p in check_grid(wrong, names)))
        # wrong name
        self.assertTrue(any("name" in p for p in check_grid(talents, {**names, 1000: "Nope"})))
        # moved cell
        moved = [dict(talents[0], column=1)] + talents[1:]
        self.assertTrue(check_grid(moved, names))
        # other tabs are ignored
        self.assertEqual(check_grid(talents + [_talent(98, 0, 0, [1], tab=262)], names), [])

    def test_rank_levels(self):
        talents = [_talent(1, 0, 0, [1, 2, 3])]
        self.assertEqual(check_rank_levels(talents, {1: 0, 2: 30, 3: 30}), [])
        self.assertEqual(len(check_rank_levels(talents, {1: 30, 2: 10, 3: 30})), 1)
        self.assertEqual(len(check_rank_levels(talents, {1: 0, 2: 0, 3: 81})), 1)

    def test_no_depends_on(self):
        self.assertEqual(check_no_depends_on([_talent(1, 0, 0, [1])]), [])
        self.assertEqual(len(check_no_depends_on([_talent(1, 0, 0, [1], depends_on=5)])), 1)
        self.assertEqual(check_no_depends_on([_talent(1, 0, 0, [1], tab=262, depends_on=5)]), [])

    def test_dropped_ranks(self):
        self.assertEqual(check_dropped_ranks([_talent(1, 0, 0, [16110, 16109])]), [])
        self.assertEqual(len(check_dropped_ranks([_talent(1, 0, 0, [16110, 16111])])), 1)
        self.assertEqual(len(check_dropped_ranks([_talent(1, 0, 0, [62100]), _talent(2, 1, 1, [60187], tab=263)])), 2)

    def test_equipped_item_class(self):
        self.assertEqual(len(check_equipped_item_class({202520: _row(202520, EquippedItemClass=0)}, [202520])), 1)
        self.assertEqual(len(check_equipped_item_class({202520: _row(202520)}, [202520])), 1)
        self.assertEqual(check_equipped_item_class({202520: _row(202520, EquippedItemClass=-1)}, [202520]), [])
        self.assertEqual(check_equipped_item_class({}, [202520]), [])

    def test_forbidden_bits(self):
        for col, bit in (("SpellClassMask_1", m.FORBIDDEN_D0_B0), ("SpellClassMask_1", m.FORBIDDEN_D0_B28),
                         ("SpellClassMask_2", m.FORBIDDEN_D1_B12), ("SpellClassMask_3", m.FORBIDDEN_D2_B11)):
            self.assertEqual(len(check_forbidden_bits({202560: _row(202560, **{col: bit})})), 1, col)
        # the three copies are the allowlist
        self.assertEqual(check_forbidden_bits({202591: _row(202591, SpellClassMask_1=m.FORBIDDEN_D0_B0)}), [])
        self.assertEqual(check_forbidden_bits({202593: _row(202593, SpellClassMask_2=m.FORBIDDEN_D1_B12)}), [])
        # but a copy-adjacent id is not
        self.assertEqual(len(check_forbidden_bits({202594: _row(202594, SpellClassMask_1=m.FORBIDDEN_D0_B1)})), 1)
        self.assertEqual(check_forbidden_bits({202560: _row(202560, SpellClassMask_3=m.EM_HASTE)}), [])

    def test_overload_copies(self):
        good = {202591: _row(202591, SpellClassMask_1=1, SpellClassSet=11),
                202592: _row(202592, SpellClassMask_1=2, SpellClassSet=11),
                202593: _row(202593, SpellClassMask_2=0x1000, SpellClassSet=11)}
        self.assertEqual(check_overload_copies(good), [])
        self.assertEqual(len(check_overload_copies({**good, 202591: dict(good[202591], SpellClassMask_1=0)})), 1)
        self.assertEqual(len(check_overload_copies({**good, 202592: dict(good[202592], SpellClassSet=0)})), 1)
        self.assertEqual(len(check_overload_copies({**good, 202593: dict(good[202593], AttributesEx3=0x200)})), 1)
        self.assertEqual(len(check_overload_copies({**good, 202593: dict(good[202593], AttributesEx6=0x20000000)})), 1)
        self.assertEqual(len(check_overload_copies({k: v for k, v in good.items() if k != 202592})), 1)

    def test_em_haste(self):
        good = _row(EM_HASTE, SpellClassSet=11, SpellClassMask_3=m.EM_HASTE)
        self.assertEqual(check_em_haste({EM_HASTE: good}), [])
        self.assertEqual(len(check_em_haste({EM_HASTE: dict(good, SpellClassSet=0)})), 1)
        self.assertEqual(len(check_em_haste({EM_HASTE: dict(good, SpellClassMask_3=0x2)})), 1)
        self.assertEqual(len(check_em_haste({EM_HASTE: dict(good, SpellClassMask_2=m.EM_HASTE)})), 1)
        self.assertEqual(len(check_em_haste({})), 1)

    def test_thunderstorm(self):
        good = {51490: _row(51490, AttributesEx5=0), 202594: _row(202594, AttributesEx5=8)}
        self.assertEqual(check_thunderstorm(good), [])
        self.assertEqual(len(check_thunderstorm({**good, 51490: _row(51490, AttributesEx5=8)})), 1)
        self.assertEqual(len(check_thunderstorm({**good, 202594: _row(202594, AttributesEx5=0)})), 1)
        self.assertEqual(len(check_thunderstorm({51490: good[51490]})), 1)

    def test_call_of_flame_masks(self):
        good = _row(16038, EffectSpellClassMaskA_1=0x40000000, EffectSpellClassMaskA_2=0x40000)
        self.assertEqual(check_call_of_flame_masks({16038: good}), [])
        self.assertEqual(len(check_call_of_flame_masks({16038: dict(good, EffectSpellClassMaskA_1=0x60000000)})), 1)
        self.assertEqual(len(check_call_of_flame_masks({16038: dict(good, EffectSpellClassMaskB_2=0x800000)})), 1)
        self.assertEqual(len(check_call_of_flame_masks({16038: dict(good, SpellClassMask_1=0x20000000)})), 1)

    def test_chain_lightning_jumps(self):
        rows = {421: _row(421, EffectChainTargets_1=3),
                8033: _row(8033, EffectAura_3=107, EffectMiscValue_3=17, EffectBasePoints_3=1),
                202563: _row(202563, EffectAura_2=107, EffectMiscValue_2=17, EffectBasePoints_2=1)}
        self.assertEqual(check_chain_lightning_jumps(rows), [])
        over = {**rows, 421: _row(421, EffectChainTargets_1=5)}
        self.assertEqual(len(check_chain_lightning_jumps(over)), 1)
        self.assertEqual(check_chain_lightning_jumps(over, cap=9), [])
        bigger = {**rows, 202563: _row(202563, EffectAura_2=107, EffectMiscValue_2=17, EffectBasePoints_2=3)}
        self.assertEqual(len(check_chain_lightning_jumps(bigger)), 1)
        # the storm effect lost its misc 17: nothing found
        nomod = {**rows, 202563: _row(202563, EffectAura_2=107, EffectMiscValue_2=0, EffectBasePoints_2=1)}
        self.assertEqual(len(check_chain_lightning_jumps(nomod)), 1)
        self.assertEqual(len(check_chain_lightning_jumps({421: rows[421]})), 1)

    def test_icefury_charges(self):
        consts = [{"name": "ICEFURY_MAX_CHARGES", "value": 3}]
        self.assertEqual(check_icefury_charges({202566: _row(202566, ProcCharges=3)}, consts), [])
        self.assertEqual(len(check_icefury_charges({202566: _row(202566, ProcCharges=5)}, consts)), 1)
        self.assertEqual(len(check_icefury_charges({202566: _row(202566, ProcCharges=3)}, [])), 1)
        self.assertEqual(len(check_icefury_charges({}, consts)), 1)

    def test_smoke_test_fix_pass_values(self):
        rows = {sid: _row(sid, ManaCostPct=8) for sid in FIX_PASS_SUMMONS}
        entries = {sid: {f"effect{e}": {"_potency": {"total_potency": p}}} for sid, e, p in FIX_PASS_POTENCY
                   if sid not in (8050,)}
        entries[8050] = {"effect1": {"_potency": {"total_potency": 32.3}}, "effect2": {"_potency": {"total_potency": 10.8}}}
        consts = [{"name": "LM_CHANCE_PER_STACK", "value": 7}, {"name": "ICEFURY_MANA_PCT", "value": 5}]
        self.assertEqual(check_fix_pass(rows, entries, consts), [])
        self.assertEqual(len(check_fix_pass({**rows, 2062: _row(2062, ManaCostPct=24)}, entries, consts)), 1)
        self.assertEqual(len(check_fix_pass(rows, entries, [consts[0]])), 1)
        self.assertEqual(len(check_fix_pass(rows, entries, [*consts, {"name": "ICEFURY_WATER_MANA_PCT", "value": 5}])), 1)
        stale = {**entries, 51505: {"effect1": {"_potency": {"total_potency": 322.7}}}}
        self.assertEqual(len(check_fix_pass(rows, stale, consts)), 1)

    def test_earth_shock_burst(self):
        rows = {ECHO_BUFF: _row(ECHO_BUFF, EffectBasePoints_1=29, EffectBasePoints_2=9)}
        entries = {ECHO_BUFF: {"duration_ms": 30000}, EARTH_SHOCK: {"effect2": {"_potency": {"total_potency": 60.0}}}}
        consts = [{"name": "ECHO_DURATION_MS", "value": 30000}, {"name": "ECHO_EARTH_ELEMENTAL_GRANT", "value": 5},
                  {"name": "ECHO_MAX", "value": 10}]
        self.assertEqual(check_earth_shock_burst(rows, entries, consts), [])
        # +10% damage per stack (an old value), the crit bonus changed, 20 s, no grant, the old potency
        self.assertEqual(len(check_earth_shock_burst({ECHO_BUFF: _row(ECHO_BUFF, EffectBasePoints_1=9, EffectBasePoints_2=9)},
                                                     entries, consts)), 1)
        self.assertEqual(len(check_earth_shock_burst({ECHO_BUFF: _row(ECHO_BUFF, EffectBasePoints_1=29, EffectBasePoints_2=19)},
                                                     entries, consts)), 1)
        self.assertEqual(len(check_earth_shock_burst(rows, {**entries, ECHO_BUFF: {"duration_ms": 20000}}, consts)), 1)
        self.assertEqual(len(check_earth_shock_burst(rows, entries, consts[:1] + consts[2:])), 1)
        self.assertEqual(len(check_earth_shock_burst(rows, entries, [dict(consts[0], value=20000), *consts[1:]])), 1)
        old = {**entries, EARTH_SHOCK: {"effect2": {"_potency": {"total_potency": 32.3}}}}
        self.assertEqual(len(check_earth_shock_burst(rows, old, consts)), 1)
        self.assertEqual(len(check_earth_shock_burst({}, entries, consts)), 1)

    def test_lightning_mastery_duration(self):
        self.assertEqual(check_lightning_mastery_duration({202568: {"duration_ms": 8000}}), [])
        self.assertEqual(len(check_lightning_mastery_duration({202568: {"duration_ms": 15000}})), 1)
        self.assertEqual(len(check_lightning_mastery_duration({})), 1)

    def test_haste_groups(self):
        adds = [{"id": 1122, "spell_id": 12472}, {"id": 1122, "spell_id": 64701},
                {"id": 1258, "spell_id": 26297}, {"id": 1258, "spell_id": 3045}, {"id": 1258, "spell_id": 200732}]
        removals = [{"id": 1122, "spell_id": 2825}, {"id": 1122, "spell_id": 32182}]
        rules = [{"group_id": 1258, "stack_rule": 3}]
        aura = {10060: 65, 12472: 65, 64701: 65, 26297: 193, 3045: 193, 200732: 193}
        rows = {i: _row(i, EffectAura_1=a) for i, a in aura.items()}
        self.assertEqual(check_haste_groups(adds, removals, rules, rows), [])
        # Bloodlust / Heroism not removed
        self.assertTrue(check_haste_groups(adds, removals[:1], rules, rows))
        self.assertTrue(check_haste_groups(adds, [], rules, rows))
        # a member missing
        self.assertTrue(check_haste_groups(adds[1:], removals, rules, rows))
        # an extra member
        self.assertTrue(check_haste_groups(adds + [{"id": 1258, "spell_id": 9999}], removals, rules, {**rows, 9999: _row(9999, EffectAura_1=193)}))
        # a member with the wrong aura type (the Rapid Fire 140 case)
        self.assertEqual(len(check_haste_groups(adds, removals, rules, {**rows, 3045: _row(3045, EffectAura_1=140)})), 1)
        self.assertEqual(len(check_haste_groups(adds, removals, rules, {**rows, 64701: _row(64701, EffectAura_1=193)})), 1)
        # no row at all
        self.assertEqual(len(check_haste_groups(adds, removals, rules, {k: v for k, v in rows.items() if k != 200732})), 1)
        # missing / wrong rule
        self.assertEqual(len(check_haste_groups(adds, removals, [], rows)), 1)
        self.assertEqual(len(check_haste_groups(adds, removals, [{"group_id": 1258, "stack_rule": 1}], rows)), 2)

    def test_visible_buffs(self):
        good = _row(202570, Attributes=0, Effect_1=6, AuraDescription_Lang_enUS="Haste increased.", Name_Lang_enUS="x")
        self.assertEqual(check_visible_buffs({202570: good}), [])
        self.assertEqual(len(check_visible_buffs({202570: dict(good, AuraDescription_Lang_enUS="Haste up by 5%.")})), 1)
        self.assertEqual(len(check_visible_buffs({202570: dict(good, AuraDescription_Lang_enUS="")})), 1)
        self.assertEqual(len(check_visible_buffs({202570: dict(good, AuraDescription_Lang_enUS=None)})), 1)
        # passive / hidden / non-aura rows are exempt
        self.assertEqual(check_visible_buffs({202570: dict(good, Attributes=0x40, AuraDescription_Lang_enUS="")}), [])
        self.assertEqual(check_visible_buffs({202570: dict(good, Attributes=0x80, AuraDescription_Lang_enUS="")}), [])
        self.assertEqual(check_visible_buffs({202570: dict(good, Effect_1=2, AuraDescription_Lang_enUS="")}), [])

    def test_tooltip_vars(self):
        def sdv(i, text):
            return {"id": i, "Variables": text}
        good = [sdv(i, "$ab=$?s1[${1}][${2}]\r\n$mult=${$<ab>}") for i in SDV_IDS]
        self.assertEqual(check_tooltip_vars(good), [])
        self.assertEqual(len(check_tooltip_vars(good[1:])), 1)
        long_name = [sdv(1210, "$abcdefghijklm=${1}")] + good[1:]
        self.assertEqual(len(check_tooltip_vars(long_name)), 1)
        ok_name = [sdv(1210, "$abcdefghijkl=${1}")] + good[1:]
        self.assertEqual(check_tooltip_vars(ok_name), [])
        huge = [sdv(1210, "\r\n".join(f"$v{n}=${{1}}" for n in range(200)))] + good[1:]
        self.assertTrue(any("over" in p for p in check_tooltip_vars(huge)))
        self.assertEqual(len(check_tooltip_vars([sdv(1210, "garbage")] + good[1:])), 1)

    def test_oath_clause(self):
        removal = [{"spell_id": 16246, "ScriptName": "spell_sha_clearcasting"}]
        rows = {i: _row(i, Effect_2=6, EffectAura_2=107, EffectMiscValue_2=12, EffectSpellClassMaskB_3=0x4000)
                for i in OATH_RANKS}
        rows[202536] = _row(202536)
        rows[16246] = _row(16246, Effect_1=6)
        self.assertEqual(check_oath_clause_gone(rows, removal), [])
        dirty = {**rows, 51466: dict(rows[51466], EffectBasePoints_2=20, EffectDieSides_2=5)}
        self.assertEqual(len(check_oath_clause_gone(dirty, removal)), 1)
        clause = {**rows, 51470: dict(rows[51470], EffectSpellClassMaskB_1=0x200800)}
        self.assertEqual(len(check_oath_clause_gone(clause, removal)), 1)
        self.assertEqual(len(check_oath_clause_gone({**rows, 16246: _row(16246, Effect_1=6, Effect_2=6)}, removal)), 1)
        self.assertEqual(len(check_oath_clause_gone(rows, [])), 1)
        self.assertEqual(len(check_oath_clause_gone({k: v for k, v in rows.items() if k != 202536}, removal)), 1)

    def test_flame_shock_dots(self):
        row = _row(1, EffectAura_3=108, EffectMiscValue_3=22, EffectSpellClassMaskC_1=0x10000000)
        good = {i: dict(row, ID=i) for ranks in DOT_TALENTS.values() for i in ranks}
        self.assertEqual(check_flame_shock_dots(good), [])
        no_mask = {**good, 16035: dict(row, ID=16035, EffectSpellClassMaskC_1=0)}
        self.assertEqual(len(check_flame_shock_dots(no_mask)), 1)
        wrong_op = {**good, 63370: dict(row, ID=63370, EffectMiscValue_3=0)}
        self.assertEqual(len(check_flame_shock_dots(wrong_op)), 1)
        wrong_aura = {**good, 51486: dict(row, ID=51486, EffectAura_3=3)}
        self.assertEqual(len(check_flame_shock_dots(wrong_aura)), 1)
        self.assertEqual(len(check_flame_shock_dots({k: v for k, v in good.items() if k != 16110})), 1)

    def test_header_names(self):
        header = "constexpr uint32 SPELL_A = 1;\nconstexpr int32 TUNE_B = 2;\nconstexpr std::array<uint32, 2> LIST_C = {1, 2};"
        used = parse_cpp_names({"x.cpp": "auto a = ShamanData::SPELL_A + ShamanData::TUNE_B; ShamanData::LIST_C[0];",
                                "y.h": "ShamanData::SPELL_A"})
        self.assertEqual(used["x.cpp"], {"SPELL_A", "TUNE_B", "LIST_C"})
        self.assertEqual(check_header_names(used, header), [])
        bad = parse_cpp_names({"x.cpp": "ShamanData::SPELL_A; ShamanData::SPELL_MISSING; ShamanData::ALSO_MISSING"})
        self.assertEqual(len(check_header_names(bad, header)), 2)
        # a name that only appears as a comment or a prefix does not count
        self.assertEqual(len(check_header_names(parse_cpp_names({"x.cpp": "ShamanData::SPELL"}), header)), 1)


if __name__ == "__main__":
    unittest.main()
