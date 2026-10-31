"""
Warrior S1 data gate (warrior-rework S1-HANDOFF WP-A row A4, S1-WP-BRIEF rulings 1-11, S1-0VERIFY item 2).

Loads the real warrior DSL package (source/classes/warrior/) and asserts on the BUILT rows (stock base + DSL +
raw_overrides via `build.build_spell_row`, the way generate.py pairs them) for the Protection delta: the eight grid cell
moves, the SpellMod masks per dword, the DUMMY carriers, the new spells 204770 / 204774 / 204775 and the stock override
50227, the holder / echo / tick rows, Devastate / Concussion Blow / Shockwave potency, the spell_proc and script
bindings, the SpellDescriptionVariables rows, the talent tooltips against docs/reworks/warrior-protection-rework.md and
the capstone format. Every check is a pure function over built rows / package tables; the negative tests mutate a copy
of the real rows and prove each check can fail.

Reading rule for the masks (S1-0VERIFY top): EffectSpellClassMask{A,B,C}_{1,2,3}: the LETTER is the effect index
(A = effect 0, B = effect 1, C = effect 2), the NUMBER is the dword (1 = d0, 2 = d1, 3 = d2). Effects in the
comments below are 0-based ("e0"); the DBC columns and the entry keys (`effect1`..`effect3`) are 1-based.

Devastate (brief ruling 1): the flat part is 10 potency per Sunder stack on effect index 2. The engine adds n x V per
cast (n = the stack count after the cast's own Sunder application, V = CalculateSpellDamage(2)), so a 5-stack
Devastate adds 5V = 50 potency (V is 25-27.5 at level 60, about 127-137 damage). The tooltip says it the way the
engine counts.

Run: cd /home/plex/wow_server/azerothcore-wotlk && PYTHONDONTWRITEBYTECODE=1 apps/dbc-tools/.venv/bin/python3 \
     -m pytest apps/dbc-tools/lib/test_warrior_s1.py -q -p no:cacheprovider
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import dbcfile, dbcfmt, state  # noqa: E402
from lib import test_capstone_format as capfmt  # noqa: E402
from lib import test_warrior_w0b as w0b  # noqa: E402
import patch_warrior_vfx_models as warrior_vfx  # noqa: E402

TOOL_ROOT = Path(__file__).resolve().parents[1]

# effect types / auras
EFF_SCHOOL_DAMAGE, EFF_DUMMY, EFF_APPLY_AURA = 2, 3, 6
EFF_WEAPON_PERCENT, EFF_REDIRECT_THREAT, EFF_NORMALIZED = 31, 130, 121
AURA_DUMMY, AURA_SCHOOL_ABSORB, AURA_SPELLMOD_FLAT, AURA_SPELLMOD_PCT = 4, 69, 107, 108
AURA_DMG_DONE_PCT, AURA_DMG_TAKEN_PCT, AURA_MELEE_HASTE, AURA_PERIODIC_DUMMY = 79, 87, 138, 226
AURA_CUSTOM_STAT_PCT = 306
AURA_PERIODIC_TRIGGER = 23
# implicit targets: the echo is cast at an explicit destination and hits the enemies around it
TARGET_DEST_DEST, TARGET_UNIT_DEST_AREA_ENEMY = 87, 16
# spellmod ops (EffectMiscValue of aura 107 / 108)
OP_DAMAGE, OP_RADIUS, OP_CRIT, OP_COOLDOWN, OP_EFFECT2 = 0, 6, 7, 11, 12

ATTR0_DO_NOT_DISPLAY, ATTR0_NOT_SHAPESHIFTED = 0x80, 0x10000
ATTR2_ALLOW_WHILE_NOT_SHAPESHIFTED, ATTR2_CANT_CRIT = 0x80000, 0x20000000
ATTR2_IGNORE_LINE_OF_SIGHT = 0x4      # S2 fix pass m2: a script-cast tick must not die behind a corner
ATTR5_HASTE_PERIODIC = 0x2000
CU_IGNORE_ARMOR = 0x8000

M1, M2, M3 = "SpellClassMask_1", "SpellClassMask_2", "SpellClassMask_3"

# ---- the talents / ranks ---------------------------------------------------------------------------------------
IMPROVED_THUNDER_CLAP = (12287, 12665, 12666)
PUNCTURE = (12308, 12810, 12811)
FOCUSED_RAGE = (29787, 29790, 29792)
CRITICAL_BLOCK = (47294, 47295, 47296)
THE_WALL = (12312, 12803)
SAFEGUARD = (46945, 46949)
SWORD_AND_BOARD = (46951, 46952, 46953)
IRON_TEMPER = (29593, 29594)
UNWAVERING_SENTINEL = (200034, 200035, 200036)
THUNDERSTRUCK = (200051, 200052, 200053)
IMPROVED_BLOODRAGE = (12301, 12818)
SHIELD_COVER = (200041, 200042, 200043)
FIRM_GRIP = (200038, 200039, 200040)
INCITE = (50685, 50686, 50687)
REPRISAL = (200056, 200057)
STORMS_BULWARK = (200058, 200059, 200060)
IMPROVED_REVENGE = (12797, 12799)
SWORD_AND_BOARD_BUFF, TEMPERED, BLOODSTORM = 50227, 200050, 200030
ECHO, SHIELD_DISCIPLINE_BUFF, CONCUSSED = 200065, 200064, 200029
ECHO_HOLDER = 200066
EMPOWERED_REVENGE, IMPROVED_BLOODRAGE_BUFF, BLOODSTORM_TICK = 204770, 204774, 204775
VIGILANCE_THREAT = 59665
DEVASTATE, CONCUSSION_BLOW, SHOCKWAVE, LAST_STAND = 20243, 12809, 46968, 12975
REVENGE, THUNDER_CLAP, SHIELD_SLAM = 6572, 6343, 23922

# D27: talent id -> (tier, column) in the Protection tab (163); the eight moves, in the order of the handoff, plus
# the user's 2026-10-30 playtest moves
GRID_MOVES = {
    60005: (6, 3),   # Storm's Bulwark (5,2) -> (6,3)
    60004: (3, 1),   # Reprisal (3,0) -> (3,1)
    2247: (3, 0),    # Shield Cover (3,2) -> (3,0)
    146: (3, 2),     # Puncture (3,1) -> (3,2)
    151: (9, 0),     # Thunderstruck (9,2) -> (9,0)
    1871: (9, 1),    # Sword and Board (9,0) -> (9,1)
    2246: (9, 2),    # Damage Shield (9,1) -> (9,2)
    1872: (10, 1),   # Shockwave (10,1) -> (10,0); user 2026-10-30 moved it back to (10,1)
    2236: (8, 1),    # Unrelenting (8,0) -> (8,1), user 2026-10-30
    60006: (8, 2),   # Shield Discipline (8,1) -> (8,2), user 2026-10-30
}
PROTECTION_TAB = 163

# the rows A1 / A2 / A3 wrote or rewrote (the "no stray $" and "no empty-mask SpellMod" sweeps)
S1_RANK_IDS = (*IMPROVED_THUNDER_CLAP, *PUNCTURE, *FOCUSED_RAGE, *CRITICAL_BLOCK, *THE_WALL, *SAFEGUARD,
               *SWORD_AND_BOARD, *IRON_TEMPER, *UNWAVERING_SENTINEL, *THUNDERSTRUCK, *IMPROVED_BLOODRAGE,
               *SHIELD_COVER, *FIRM_GRIP, *INCITE, *REPRISAL, *STORMS_BULWARK, *IMPROVED_REVENGE)
S1_AURA_IDS = (*S1_RANK_IDS, SWORD_AND_BOARD_BUFF, TEMPERED, BLOODSTORM, ECHO, SHIELD_DISCIPLINE_BUFF, CONCUSSED,
               EMPOWERED_REVENGE, IMPROVED_BLOODRAGE_BUFF, BLOODSTORM_TICK, VIGILANCE_THREAT, 200028)
S1_NEW_IDS = (EMPOWERED_REVENGE, IMPROVED_BLOODRAGE_BUFF, BLOODSTORM_TICK)
# ids that carry a tooltip variable (`$<name>` / `${$m2*...}`); their text is checked with the variable forms stripped
S1_VARIABLE_TOOLTIP_IDS = (DEVASTATE, CONCUSSION_BLOW, SHOCKWAVE, REVENGE, THUNDER_CLAP)

# SpellDescriptionVariables block (ids.yaml Warrior Protection 1420-1424): id -> talent rank spells it reads
SDV_ROWS = {1420: (12797, 12799), 1421: (12308, 12810, 12811), 1422: (12287, 12665, 12666, 200051, 200052, 200053),
            1424: (200051, 200052, 200053)}
SDV_SKIPPED = 1423     # Shield Slam (Gag Order is an EFFECT2 mod: a {pot2*mult} would overstate it, brief ruling 3)
# spell -> the variable the built description reads
SDV_READERS = {REVENGE: "$<ir>", DEVASTATE: "$<pun>", THUNDER_CLAP: "$<mult>", SHOCKWAVE: "$<ts>"}

# brief "Script names and bindings (frozen)": spell id -> the exact set of S1 script names that id carries
S1_BINDINGS = {
    CONCUSSION_BLOW: {"spell_warr_concussion_blow_rework"},
    50720: {"spell_warr_vigilance_focused_rage"},
    50725: {"spell_warr_vigilance_trigger_growl"},
    BLOODSTORM: {"spell_warr_bloodstorm"},
    ECHO: {"spell_warr_thunder_clap_echo"},
    ECHO_HOLDER: {"spell_warr_thunderstruck_echo_holder"},
}
S1_UNBINDINGS = {(CONCUSSION_BLOW, "spell_warr_concussion_blow"), (-46951, "spell_warr_sword_and_board"),
                 (50687, "spell_warr_incite")}
# ids whose bindings (bound or unbound) the S1 list pins; nothing else may sit on them
S1_BOUND_IDS = (CONCUSSION_BLOW, 50720, 50725, BLOODSTORM, ECHO, ECHO_HOLDER, -46951, 50687)
S1_PROC_REMOVALS = {-29593, -46945, -46951}

SPELL_LEVELS = {DEVASTATE: 10, LAST_STAND: 20, CONCUSSION_BLOW: 30, SHOCKWAVE: 60}

# docs/reworks/warrior-protection-rework.md, "Tooltip" lines: sid -> fragments the built description must contain
TOOLTIP_FRAGMENTS = {
    12287: ("damage of your Thunder Clap by 10%", "radius by 1 yard,", "an additional 4%"),
    12665: ("damage of your Thunder Clap by 20%", "radius by 2 yards", "an additional 7%"),
    12666: ("damage of your Thunder Clap by 30%", "radius by 3 yards", "an additional 10%"),
    12308: ("damage of your Devastate by 5%", "ignore an additional 4% of your target's armor"),
    12810: ("damage of your Devastate by 10%", "ignore an additional 8% of your target's armor"),
    12811: ("damage of your Devastate by 15%", "ignore an additional 12% of your target's armor"),
    29787: ("5% more rage from damage taken", "gain 5 rage every time the target of your Vigilance takes damage",
            "only occur once every second"),
    29790: ("10% more rage from damage taken", "gain 5 rage every time the target of your Vigilance takes damage"),
    29792: ("15% more rage from damage taken", "gain 5 rage every time the target of your Vigilance takes damage"),
    47294: ("reduce the damage you take from the blocked hit by 8%", "Shield Slam ability by 4%",
            "Does not work with Touched by the Light"),
    47295: ("blocked hit by 16%", "Shield Slam ability by 7%"),
    47296: ("blocked hit by 25%", "Shield Slam ability by 10%"),
    12312: ("cooldown of your Shield Wall by 30 sec", "Your Shield Slam reduces the remaining cooldown of Shield Wall "
                                                     "by 3 sec"),
    12803: ("cooldown of your Shield Wall by 60 sec", "Your Shield Slam reduces the remaining cooldown of Shield Wall "
                                                     "by 3 sec"),
    46945: ("Your Intervene reduces the target's damage taken by 20% instead of 10%",),
    46949: ("Your Intervene reduces the target's damage taken by 30% instead of 10%",),
    46951: ("critical strike chance of Devastate by 5%", "10% chance to reset the cooldown of Shield Slam",
            "increase its damage by 10%"),
    46952: ("critical strike chance of Devastate by 10%", "20% chance to reset the cooldown of Shield Slam"),
    46953: ("critical strike chance of Devastate by 15%", "30% chance to reset the cooldown of Shield Slam"),
    29593: ("Tempered for 8 sec", "you take 3% less damage and deal 6% more physical damage"),
    29594: ("Tempered for 8 sec", "you take 6% less damage and deal 6% more physical damage"),
    200034: ("Increases your Cooldown Haste by 1%",), 200035: ("Increases your Cooldown Haste by 2%",),
    200036: ("Increases your Cooldown Haste by 3%",),
    200051: ("damage of Shockwave and Thunder Clap by 10%", "additional 10% damage to targets that cannot be stunned",
             "a second Thunder Clap strikes the same spot at 50% effectiveness"),
    200052: ("damage of Shockwave and Thunder Clap by 20%", "additional 20% damage"),
    200053: ("damage of Shockwave and Thunder Clap by 30%", "additional 30% damage"),
    12301: ("rage generated by your Bloodrage ability by 25%", "Defensive Stance your Bloodrage reduces your damage "
                                                                 "taken by 2%"),
    12818: ("rage generated by your Bloodrage ability by 50%", "reduces your damage taken by 4%"),
    200041: ("Reduces your damage taken by 1%", "block value by 4%", "cooldown of Spell Reflection by 3 sec",
             "reduces all Magic damage taken by 30% for 3 sec"),
    200042: ("damage taken by 2%", "block value by 7%"), 200043: ("damage taken by 3%", "block value by 10%"),
    200038: ("armor value from your equipped Shield by 10%", "Stamina by 1%", "block value by 2%"),
    200039: ("armor value from your equipped Shield by 20%", "Stamina by 2%", "block value by 4%"),
    200040: ("armor value from your equipped Shield by 30%", "Stamina by 3%", "block value by 6%"),
    50685: ("critical strike chance of your Revenge by 10%",
            "1.5% of your maximum health to your Storm's Bulwark shield", "does not extend the shield's duration"),
    50686: ("chance of your Revenge by 20%",), 50687: ("chance of your Revenge by 30%",),
    200056: ("0.5% of your maximum health to your Storm's Bulwark shield", "increased by 20% for each application of "
                                                                          "Sunder Armor"),
    200057: ("1% of your maximum health to your Storm's Bulwark shield", "increased by 20%"),
    200058: ("absorb shield equal to 2% of your maximum health",
             "additional 1% for each target struck, up to 5 targets", "Lasts 15 sec",
             "Mastery increases every amount added to your Storm's Bulwark shield, and raises its maximum"),
    200059: ("equal to 4% of your maximum health", "Lasts 15 sec"),
    200060: ("equal to 6% of your maximum health", "Lasts 15 sec"),
    12797: ("Revenge ability by 15%", "next Devastate within 8 sec will strike an additional target",
            "Your Revenge strikes 2 additional targets"),
    12799: ("Revenge ability by 30%", "next Devastate within 8 sec will strike an additional target"),
    200049: ("reduces the remaining cooldown of your Last Stand by 1 sec", "increasing its damage by 30%",
             "equal to 2% of your maximum health"),
    200062: ("increases the absorb granted by your next Thunder Clap by 25%",),
    200063: ("increases the absorb granted by your next Thunder Clap by 50%",),
    200054: ("bleed for 15% of the damage dealt over 9 sec",),
    200055: ("bleed for 30% of the damage dealt over 9 sec",),
    EMPOWERED_REVENGE: ("Your next Revenge deals 30% more damage and adds to your Storm's Bulwark shield",),
    SWORD_AND_BOARD_BUFF: ("Your next Shield Slam costs no rage and deals 10% more damage",),
    CONCUSSED: ("Dealing 15% less damage",),
    BLOODSTORM: ("Bleeding",),
    SHIELD_DISCIPLINE_BUFF: ("Your next Thunder Clap grants a larger shield",),
}
# the capstone talents (S1 D25): name -> rank spells, the clause every rank carries
CAPSTONE_RANKS = {
    "Incite": INCITE, "Improved Revenge": IMPROVED_REVENGE, "Focused Rage": FOCUSED_RAGE, "Shield Cover": SHIELD_COVER,
    "Thunderstruck": THUNDERSTRUCK, "The Wall": THE_WALL, "Storm's Bulwark": STORMS_BULWARK,
}


def _i(row: dict, col: str) -> int:
    return int(row.get(col) or 0)


def _u32(value) -> int:
    return int(value or 0) & 0xFFFFFFFF


def _eff(row: dict, idx: int) -> tuple[int, int, int, int]:
    """(effect type, aura, misc value, base points) of the 0-based effect `idx`."""
    n = idx + 1
    return (_i(row, f"Effect_{n}"), _i(row, f"EffectAura_{n}"), _i(row, f"EffectMiscValue_{n}"),
            _i(row, f"EffectBasePoints_{n}"))


def _emask(row: dict, idx: int) -> tuple[int, int, int]:
    """The three dwords of the 0-based effect `idx` (letter = effect, number = dword)."""
    letter = "ABC"[idx]
    return tuple(_u32(row.get(f"EffectSpellClassMask{letter}_{n}")) for n in (1, 2, 3))


def _all_masks(row: dict) -> dict[int, tuple[int, int, int]]:
    return {idx: _emask(row, idx) for idx in range(3)}


def _hex3(mask) -> str:
    return "(" + ", ".join(hex(x) for x in mask) + ")"


def _missing(rows: dict, *ids: int) -> list[str]:
    return [f"{sid}: not built" for sid in ids if sid not in rows]


def _aura_effect(row: dict, idx: int, aura: int, misc: int | None, bp: int | None, mask, sid: int,
                 label: str) -> list[str]:
    """One effect must be APPLY_AURA `aura` with misc / bp (None = not pinned) and exactly the `mask` on its letter."""
    bad = []
    typ, got_aura, got_misc, got_bp = _eff(row, idx)
    if (typ, got_aura) != (EFF_APPLY_AURA, aura):
        bad.append(f"{sid}: {label} e{idx} is type/aura {typ}/{got_aura}, expected APPLY_AURA/{aura}")
    if misc is not None and got_misc != misc:
        bad.append(f"{sid}: {label} e{idx} misc {got_misc}, expected {misc}")
    if bp is not None and got_bp != bp:
        bad.append(f"{sid}: {label} e{idx} bp {got_bp}, expected {bp}")
    if mask is not None and _emask(row, idx) != tuple(mask):
        bad.append(f"{sid}: {label} e{idx} mask {_hex3(_emask(row, idx))}, expected {_hex3(mask)}")
    return bad


def _effect_empty(row: dict, idx: int, sid: int, label: str) -> list[str]:
    """The effect slot is gone: no type, no aura, no masks (the stale residue the 0-verify found is cleared)."""
    typ, aura, misc, _bp = _eff(row, idx)
    bad = []
    if typ or aura or misc:
        bad.append(f"{sid}: {label} e{idx} should be empty, got type/aura/misc {typ}/{aura}/{misc}")
    if any(_emask(row, idx)):
        bad.append(f"{sid}: {label} e{idx} is empty but keeps the mask {_hex3(_emask(row, idx))}")
    return bad


# ---- checks (pure: take built rows / package tables, return problem strings) ------------------------------------

def check_grid(talents: list[dict]) -> list[str]:
    bad = []
    prot = {int(t["id"]): t for t in talents if int(t["tab_id"]) == PROTECTION_TAB}
    for tid, cell in sorted(GRID_MOVES.items()):
        t = prot.get(tid)
        if t is None:
            bad.append(f"talent {tid}: not in the Protection tab")
        elif (int(t["tier"]), int(t["column"])) != cell:
            bad.append(f"talent {tid}: cell (tier, column) {(int(t['tier']), int(t['column']))}, expected {cell}")
    seen: dict[tuple[int, int], int] = {}
    for tid, t in sorted(prot.items()):
        cell = (int(t["tier"]), int(t["column"]))
        if cell in seen:
            bad.append(f"talents {seen[cell]} and {tid} share the cell {cell}")
        seen[cell] = tid
        if not (0 <= cell[0] <= 10 and 0 <= cell[1] <= 3):
            bad.append(f"talent {tid}: cell {cell} is off the grid")
        if t.get("depends_on"):
            bad.append(f"talent {tid}: has a prerequisite {t['depends_on']} (D27: none are set)")
    return bad


def check_improved_thunder_clap(rows: dict) -> list[str]:
    bad = _missing(rows, *IMPROVED_THUNDER_CLAP)
    if bad:
        return bad
    for rank, sid in enumerate(IMPROVED_THUNDER_CLAP):
        r = rows[sid]
        # e0 RADIUS flat 0/1/2 on d0 0x80 (+1/2/3 yd); e1 the stock damage mod kept; e2 EFFECT2 -4/-7/-10 on d0 0x80
        bad += _aura_effect(r, 0, AURA_SPELLMOD_FLAT, OP_RADIUS, rank, (0x80, 0, 0), sid, "radius")
        bad += _aura_effect(r, 1, AURA_SPELLMOD_PCT, OP_DAMAGE, 9 + 10 * rank, (0x80, 0, 0), sid, "damage")
        bad += _aura_effect(r, 2, AURA_SPELLMOD_FLAT, OP_EFFECT2, (-5, -8, -11)[rank], (0x80, 0, 0), sid, "slow")
    return bad


def check_puncture(rows: dict) -> list[str]:
    bad = _missing(rows, *PUNCTURE)
    if bad:
        return bad
    for rank, sid in enumerate(PUNCTURE):
        r = rows[sid]
        bad += _aura_effect(r, 0, AURA_SPELLMOD_PCT, OP_DAMAGE, (4, 9, 14)[rank], (0, 0x40, 0), sid, "damage")
        if _eff(r, 1)[1] != 280 or _eff(r, 1)[3] != (3, 7, 11)[rank] or any(_emask(r, 1)):
            bad.append(f"{sid}: e1 (armor penetration, aura 280 bp {(3, 7, 11)[rank]}) changed: {_eff(r, 1)}")
    return bad


def check_focused_rage(rows: dict) -> list[str]:
    bad = _missing(rows, *FOCUSED_RAGE)
    if bad:
        return bad
    for rank, sid in enumerate(FOCUSED_RAGE):
        r = rows[sid]
        bad += _aura_effect(r, 0, AURA_DUMMY, None, (4, 9, 14)[rank], None, sid, "carrier")
        for idx, mask in _all_masks(r).items():
            if any(mask):
                bad.append(f"{sid}: e{idx} keeps the mask {_hex3(mask)} (a DUMMY carrier takes no mask)")
        for idx in (1, 2):
            bad += _effect_empty(r, idx, sid, "carrier")
    return bad


def check_critical_block(rows: dict) -> list[str]:
    bad = _missing(rows, *CRITICAL_BLOCK)
    if bad:
        return bad
    for rank, sid in enumerate(CRITICAL_BLOCK):
        r = rows[sid]
        bad += _aura_effect(r, 0, AURA_SPELLMOD_FLAT, OP_CRIT, (3, 6, 9)[rank], (0, 0x200, 0), sid, "crit")
        # the DUMMY marker the C++ reads (GetAuraEffect(DUMMY, WARRIOR, 2778, EFFECT_1)): icon + e1 kept, mask cleared
        bad += _aura_effect(r, 1, AURA_DUMMY, None, (7, 15, 24)[rank], (0, 0, 0), sid, "marker")
        if _i(r, "SpellIconID") != 2778:
            bad.append(f"{sid}: SpellIconID {r.get('SpellIconID')!r}, expected the marker icon 2778")
        bad += _effect_empty(r, 2, sid, "marker")
    return bad


def check_the_wall(rows: dict) -> list[str]:
    bad = _missing(rows, *THE_WALL)
    if bad:
        return bad
    for rank, sid in enumerate(THE_WALL):
        r = rows[sid]
        if r.get("Name_Lang_enUS") != "The Wall":
            bad.append(f"{sid}: name {r.get('Name_Lang_enUS')!r}, expected 'The Wall'")
        bad += _aura_effect(r, 0, AURA_SPELLMOD_FLAT, OP_COOLDOWN, (-30001, -60001)[rank], (0x2000, 0, 0), sid,
                            "cooldown")
        bad += _effect_empty(r, 1, sid, "residue")   # the stale EffectSpellClassMaskB_1 = 0x2000 on the empty e1
        bad += _effect_empty(r, 2, sid, "residue")
    return bad


def check_safeguard(rows: dict) -> list[str]:
    bad = _missing(rows, *SAFEGUARD)
    if bad:
        return bad
    for rank, sid in enumerate(SAFEGUARD):
        r = rows[sid]
        bad += _aura_effect(r, 0, AURA_SPELLMOD_FLAT, OP_EFFECT2, (-11, -21)[rank], (0, 0x10000, 0), sid, "intervene")
        bad += _effect_empty(r, 1, sid, "cleared")
        bad += _effect_empty(r, 2, sid, "cleared")
        for col in ("ProcTypeMask", "ProcChance"):
            if _i(r, col):
                bad.append(f"{sid}: {col} {r.get(col)!r}, expected 0 (the proc is gone)")
    return bad


def check_empty_mask_spellmods(rows: dict) -> list[str]:
    """No S1 row has a SpellMod (aura 107 / 108) with an empty mask: it would leak onto every spell."""
    bad = []
    for sid in S1_AURA_IDS:
        r = rows.get(sid)
        if r is None:
            continue
        for idx in range(3):
            if _eff(r, idx)[1] in (AURA_SPELLMOD_FLAT, AURA_SPELLMOD_PCT) and not any(_emask(r, idx)):
                bad.append(f"{sid}: e{idx} is a SpellMod (aura {_eff(r, idx)[1]}) with no class mask")
    return bad


def check_sword_and_board(rows: dict) -> list[str]:
    bad = _missing(rows, *SWORD_AND_BOARD, SWORD_AND_BOARD_BUFF)
    if bad:
        return bad
    for rank, sid in enumerate(SWORD_AND_BOARD):
        r = rows[sid]
        bad += _aura_effect(r, 0, AURA_DUMMY, None, (9, 19, 29)[rank], (0, 0, 0), sid, "carrier")
        for col in ("ProcTypeMask", "ProcChance"):
            if _i(r, col):
                bad.append(f"{sid}: {col} {r.get(col)!r}, expected 0 (the roll is the dispatcher's)")
    b = rows[SWORD_AND_BOARD_BUFF]
    bad += _aura_effect(b, 0, AURA_SPELLMOD_PCT, 14, -101, (0, 0x200, 0), SWORD_AND_BOARD_BUFF, "free Shield Slam")
    bad += _aura_effect(b, 1, AURA_SPELLMOD_PCT, OP_DAMAGE, 9, (0, 0x200, 0), SWORD_AND_BOARD_BUFF, "damage")
    if _emask(b, 1)[0] & 0x400:
        bad.append(f"{SWORD_AND_BOARD_BUFF}: e1 still carries the Revenge bit d0 0x400")
    if _i(b, "ProcCharges") != 1:
        bad.append(f"{SWORD_AND_BOARD_BUFF}: ProcCharges {b.get('ProcCharges')!r}, expected 1 (one Shield Slam)")
    if _dur_ms(b) != 5000:
        bad.append(f"{SWORD_AND_BOARD_BUFF}: duration {_dur_ms(b)} ms, expected 5000")
    if b.get("AuraDescription_Lang_enUS") != "Shield Slam is free and deals more damage.":
        bad.append(f"{SWORD_AND_BOARD_BUFF}: aura text {b.get('AuraDescription_Lang_enUS')!r}")
    return bad


def check_iron_temper(rows: dict) -> list[str]:
    bad = _missing(rows, *IRON_TEMPER, TEMPERED)
    if bad:
        return bad
    for rank, sid in enumerate(IRON_TEMPER):
        r = rows[sid]
        bad += _aura_effect(r, 0, AURA_DUMMY, None, (-4, -7)[rank], (0, 0, 0), sid, "carrier")
        if _i(r, "ShapeshiftMask") != 0:
            bad.append(f"{sid}: ShapeshiftMask {r.get('ShapeshiftMask')!r}, expected 0 (no stance gate)")
        for col in ("ProcTypeMask", "ProcChance", "ProcCharges"):
            if _i(r, col):
                bad.append(f"{sid}: {col} {r.get(col)!r}, expected 0")
    t = rows[TEMPERED]
    if t.get("Name_Lang_enUS") != "Tempered":
        bad.append(f"{TEMPERED}: name {t.get('Name_Lang_enUS')!r}, expected 'Tempered'")
    if _dur_ms(t) != 8000:
        bad.append(f"{TEMPERED}: duration {_dur_ms(t)} ms, expected 8000")
    bad += _aura_effect(t, 0, AURA_DMG_TAKEN_PCT, 127, None, None, TEMPERED, "reduction (caster-set amount)")
    if _eff(t, 0)[3] >= 0:
        bad.append(f"{TEMPERED}: e0 stored bp {_eff(t, 0)[3]} is not negative (a damage-taken reduction)")
    bad += _aura_effect(t, 1, AURA_DMG_DONE_PCT, 1, 5, None, TEMPERED, "+6% physical")
    bad += _effect_empty(t, 2, TEMPERED, "tail")
    return bad


def check_unwavering_sentinel(rows: dict) -> list[str]:
    bad = _missing(rows, *UNWAVERING_SENTINEL)
    if bad:
        return bad
    for rank, sid in enumerate(UNWAVERING_SENTINEL):
        r = rows[sid]
        if r.get("Name_Lang_enUS") != "Unwavering Sentinel":
            bad.append(f"{sid}: name {r.get('Name_Lang_enUS')!r}, expected 'Unwavering Sentinel'")
        bad += _aura_effect(r, 0, AURA_CUSTOM_STAT_PCT, 1 << 22, rank, (0, 0, 0), sid, "cooldown haste")
    return bad


def check_thunderstruck(rows: dict) -> list[str]:
    bad = _missing(rows, *THUNDERSTRUCK)
    if bad:
        return bad
    for rank, sid in enumerate(THUNDERSTRUCK):
        r = rows[sid]
        bad += _aura_effect(r, 0, AURA_SPELLMOD_PCT, OP_DAMAGE, (9, 19, 29)[rank], (0x80, 0x8000, 0), sid, "damage")
        bad += _effect_empty(r, 1, sid, "threat (gone)")
        bad += _aura_effect(r, 2, AURA_DUMMY, None, (9, 19, 29)[rank], (0, 0, 0), sid, "stun-immune carrier")
    return bad


def check_improved_bloodrage(rows: dict) -> list[str]:
    bad = _missing(rows, *IMPROVED_BLOODRAGE)
    if bad:
        return bad
    for rank, sid in enumerate(IMPROVED_BLOODRAGE):
        r = rows[sid]
        bad += _aura_effect(r, 0, AURA_SPELLMOD_PCT, 3, (24, 49)[rank], (0x100, 0, 0), sid, "rage")
        bad += _aura_effect(r, 1, AURA_DUMMY, None, (1, 3)[rank], (0, 0, 0), sid, "damage-taken carrier")
        if _i(r, "ShapeshiftMask") != 0:
            bad.append(f"{sid}: ShapeshiftMask {r.get('ShapeshiftMask')!r}, expected 0")
    return bad


def check_shield_cover_and_firm_grip(rows: dict) -> list[str]:
    bad = _missing(rows, *SHIELD_COVER, *FIRM_GRIP)
    if bad:
        return bad
    for rank, sid in enumerate(SHIELD_COVER):
        bad += _aura_effect(rows[sid], 0, AURA_DMG_TAKEN_PCT, 127, (-2, -3, -4)[rank], None, sid, "all schools")
    for rank, sid in enumerate(FIRM_GRIP):
        r = rows[sid]
        # brief ruling 2 (F7): no shield gate on the rank; all three effects kept
        if _i(r, "EquippedItemClass") != -1:
            bad.append(f"{sid}: EquippedItemClass {r.get('EquippedItemClass')!r}, expected -1 (Firm Grip is ungated)")
        if _i(r, "EquippedItemSubclass"):
            bad.append(f"{sid}: EquippedItemSubclass {r.get('EquippedItemSubclass')!r}, expected 0")
        got = [_eff(r, i)[1] for i in range(3)]
        if got != [142, 137, 150]:
            bad.append(f"{sid}: auras {got}, expected [142 armor, 137 stamina, 150 block value]")
    return bad


def check_bloodrage_buff(rows: dict, dur_ms) -> list[str]:
    bad = _missing(rows, IMPROVED_BLOODRAGE_BUFF)
    if bad:
        return bad
    r = rows[IMPROVED_BLOODRAGE_BUFF]
    sid = IMPROVED_BLOODRAGE_BUFF
    if _i(r, "ShapeshiftMask") != 131072:
        bad.append(f"{sid}: ShapeshiftMask {r.get('ShapeshiftMask')!r}, expected 131072 (Defensive Stance)")
    attrs, ex2 = _u32(r.get("Attributes")), _u32(r.get("AttributesEx2"))
    if attrs & ATTR0_NOT_SHAPESHIFTED:
        bad.append(f"{sid}: Attributes {attrs:#x} has NOT_SHAPESHIFTED 0x10000 (the stance removal would not happen)")
    if ex2 & ATTR2_ALLOW_WHILE_NOT_SHAPESHIFTED:
        bad.append(f"{sid}: AttributesEx2 {ex2:#x} has ALLOW_WHILE_NOT_SHAPESHIFTED 0x80000")
    if attrs != ATTR0_DO_NOT_DISPLAY:
        bad.append(f"{sid}: Attributes {attrs:#x}, expected exactly 0x80 (hidden)")
    if dur_ms(r) != 10000:
        bad.append(f"{sid}: duration {dur_ms(r)} ms, expected 10000")
    bad += _aura_effect(r, 0, AURA_DMG_TAKEN_PCT, 127, None, (0, 0, 0), sid, "reduction (caster-set amount)")
    if _eff(r, 0)[3] >= 0:
        bad.append(f"{sid}: stored bp {_eff(r, 0)[3]} is not negative")
    bad += _effect_empty(r, 1, sid, "tail")
    return bad


def check_empowered_revenge(rows: dict, dur_ms) -> list[str]:
    bad = _missing(rows, EMPOWERED_REVENGE)
    if bad:
        return bad
    r = rows[EMPOWERED_REVENGE]
    sid = EMPOWERED_REVENGE
    if dur_ms(r) != 20000:
        bad.append(f"{sid}: duration {dur_ms(r)} ms, expected 20000")
    if _i(r, "ProcCharges") != 1:
        bad.append(f"{sid}: ProcCharges {r.get('ProcCharges')!r}, expected 1")
    bad += _aura_effect(r, 0, AURA_SPELLMOD_PCT, OP_DAMAGE, 29, (0x400, 0, 0), sid, "damage")
    if _u32(r.get("Attributes")) & (0x40 | ATTR0_DO_NOT_DISPLAY):
        bad.append(f"{sid}: Attributes {_u32(r.get('Attributes')):#x} is passive / hidden, expected a visible buff")
    if r.get("AuraDescription_Lang_enUS") != "Your next Revenge is empowered.":
        bad.append(f"{sid}: aura text {r.get('AuraDescription_Lang_enUS')!r}")
    return bad


def check_bloodstorm_tick(rows: dict, entries: dict, custom_attrs: dict, bonus: list, corrections: list,
                          range_ms_of) -> list[str]:
    bad = _missing(rows, BLOODSTORM_TICK)
    if bad:
        return bad
    r = rows[BLOODSTORM_TICK]
    sid = BLOODSTORM_TICK
    if _u32(r.get("Attributes")) != ATTR0_DO_NOT_DISPLAY:
        bad.append(f"{sid}: Attributes {_u32(r.get('Attributes')):#x}, expected 0x80")
    if _u32(r.get("AttributesEx2")) != ATTR2_CANT_CRIT | ATTR2_IGNORE_LINE_OF_SIGHT:
        bad.append(f"{sid}: AttributesEx2 {_u32(r.get('AttributesEx2')):#x}, expected CANT_CRIT 0x20000000 | "
                   "IGNORE_LINE_OF_SIGHT 0x4 (a script-cast tick runs CheckCast's LoS test)")
    if _u32(r.get("AttributesEx3")) != 537198592:
        bad.append(f"{sid}: AttributesEx3 {_u32(r.get('AttributesEx3'))}, expected 537198592 "
                   "(0x20000000 IGNORE_CASTER_MODIFIERS | 0x40000 ALWAYS_HIT | 0x10000 SUPPRESS_CASTER_PROCS)")
    if custom_attrs.get(sid) != CU_IGNORE_ARMOR:
        bad.append(f"{sid}: custom_attr {custom_attrs.get(sid)!r}, expected 0x8000 (ignore armor)")
    if range_ms_of(r) != 50000.0:
        bad.append(f"{sid}: range {range_ms_of(r)} yd, expected 50000")
    typ = _eff(r, 0)[0]
    if typ != EFF_SCHOOL_DAMAGE:
        bad.append(f"{sid}: e0 type {typ}, expected SCHOOL_DAMAGE")
    if _i(r, "SchoolMask") != 1:
        bad.append(f"{sid}: SchoolMask {r.get('SchoolMask')!r}, expected 1 (physical)")
    if _i(r, "Mechanic") != 15 or _i(r, "EffectMechanic_1") != 15:
        bad.append(f"{sid}: Mechanic/EffectMechanic_1 {r.get('Mechanic')}/{r.get('EffectMechanic_1')}, expected 15")
    # potency excluded: no potency row, no bonus row, no correction row
    if any((entries[sid].get(f"effect{n}") or {}).get("_potency") for n in (1, 2, 3)):
        bad.append(f"{sid}: carries a potency row (it is a percent-of-other-damage tick)")
    if any(int(b.get("entry", 0)) == sid for b in bonus):
        bad.append(f"{sid}: has a spell_bonus_data row")
    if any(int(c["spell_id"]) == sid for c in corrections):
        bad.append(f"{sid}: has a potency correction row")
    if any(_emask(r, i) != (0, 0, 0) for i in range(3)) or any(_u32(r.get(c)) for c in (M1, M2, M3)):
        bad.append(f"{sid}: carries family mask bits (nothing modifies the tick by mask)")
    return bad


def check_bloodstorm_holder(rows: dict, dur_ms) -> list[str]:
    bad = _missing(rows, BLOODSTORM)
    if bad:
        return bad
    r = rows[BLOODSTORM]
    sid = BLOODSTORM
    typ, aura, _misc, _bp = _eff(r, 0)
    if (typ, aura) != (EFF_APPLY_AURA, AURA_PERIODIC_DUMMY):
        bad.append(f"{sid}: e0 is {typ}/{aura}, expected APPLY_AURA / 226 PERIODIC_DUMMY")
    if _i(r, "EffectAuraPeriod_1") != 3000:
        bad.append(f"{sid}: period {r.get('EffectAuraPeriod_1')!r}, expected 3000 ms")
    if _u32(r.get("AttributesEx5")) & ATTR5_HASTE_PERIODIC:
        bad.append(f"{sid}: AttributesEx5 {_u32(r.get('AttributesEx5')):#x} has the haste-periodic bit 0x2000")
    if dur_ms(r) != 9000:
        bad.append(f"{sid}: duration {dur_ms(r)} ms, expected 9000")
    if r.get("AuraDescription_Lang_enUS") != "Bleeding.":
        bad.append(f"{sid}: aura text {r.get('AuraDescription_Lang_enUS')!r}, expected 'Bleeding.'")
    if _i(r, "Mechanic") != 15:
        bad.append(f"{sid}: Mechanic {r.get('Mechanic')!r}, expected 15 (bleed)")
    return bad


def check_echo(rows: dict, entries: dict, dur_ms) -> list[str]:
    bad = _missing(rows, ECHO)
    if bad:
        return bad
    r = rows[ECHO]
    sid = ECHO
    pot = (entries[sid].get("effect1") or {}).get("_potency") or {}
    if pot.get("total_potency") != 41.5:
        bad.append(f"{sid}: effect 1 potency {pot.get('total_potency')!r}, expected 41.5 (half of Thunder Clap's 83)")
    if _eff(r, 0)[0] != EFF_SCHOOL_DAMAGE:
        bad.append(f"{sid}: e0 type {_eff(r, 0)[0]}, expected SCHOOL_DAMAGE")
    bad += _aura_effect(r, 1, AURA_MELEE_HASTE, 0, -11, None, sid, "slow")
    if _i(r, "EffectMechanic_2") != 8:
        bad.append(f"{sid}: e1 mechanic {r.get('EffectMechanic_2')!r}, expected 8 (slow)")
    for col in ("ImplicitTargetA", "ImplicitTargetB", "EffectRadiusIndex"):
        if _i(r, f"{col}_2") != _i(r, f"{col}_1"):
            bad.append(f"{sid}: {col} of e1 ({r.get(f'{col}_2')}) differs from e0 ({r.get(f'{col}_1')})")
    if dur_ms(r) != 30000:
        bad.append(f"{sid}: duration {dur_ms(r)} ms, expected 30000 (the slow lasts)")
    if _u32(r.get(M1)) & 0x80 == 0:
        bad.append(f"{sid}: lost its own d0 0x80 (Improved Thunder Clap and Thunderstruck scale it through it)")
    # S1-FIX: the doc's echo "can crit". Unit::SpellDoneCritChance gives SPELL_DAMAGE_CLASS_NONE (0) no crit, so the
    # echo takes Thunder Clap's own DmgClass (DefenseType) and never CANT_CRIT.
    if THUNDER_CLAP in rows and _i(r, "DefenseType") != _i(rows[THUNDER_CLAP], "DefenseType"):
        bad.append(f"{sid}: DefenseType {r.get('DefenseType')!r}, expected Thunder Clap's "
                   f"{rows[THUNDER_CLAP].get('DefenseType')!r} (DmgClass NONE never crits)")
    if _i(r, "DefenseType") == 0:
        bad.append(f"{sid}: DefenseType 0 (SPELL_DAMAGE_CLASS_NONE never crits)")
    if _u32(r.get("AttributesEx2")) & ATTR2_CANT_CRIT:
        bad.append(f"{sid}: carries SPELL_ATTR2_CANT_CRIT")
    # S1 playtest (user 2026-10-30): the echo strikes where the Thunder Clap was cast. The warrior casts it at that
    # explicit destination and both effects take their targets around it (Ball Lightning 52779's 87/16 pair).
    for e in (1, 2):
        pair = (_i(r, f"ImplicitTargetA_{e}"), _i(r, f"ImplicitTargetB_{e}"))
        if pair != (TARGET_DEST_DEST, TARGET_UNIT_DEST_AREA_ENEMY):
            bad.append(f"{sid}: effect {e} targets {pair}, expected (87, 16): TARGET_DEST_DEST + "
                       f"TARGET_UNIT_DEST_AREA_ENEMY, centred on the Thunder Clap's spot")
    # RangeIndex 1 returns early from Spell::CheckRange, so the warrior may have walked any distance from the spot
    if _i(r, "RangeIndex") != 1:
        bad.append(f"{sid}: RangeIndex {r.get('RangeIndex')!r}, expected 1 (no range check against the spot)")
    # the visual plays at that destination: patch_warrior_vfx_models.py's row (145 without the caster's CastKit)
    if _i(r, "SpellVisualID_1") != warrior_vfx.SV_THUNDER_CLAP_ECHO:
        bad.append(f"{sid}: SpellVisualID_1 {r.get('SpellVisualID_1')!r}, expected "
                   f"{warrior_vfx.SV_THUNDER_CLAP_ECHO} (Thunder Clap's visual at the destination)")
    return bad


def check_echo_holder(rows: dict, dur_ms) -> list[str]:
    bad = _missing(rows, ECHO_HOLDER)
    if bad:
        return bad
    r = rows[ECHO_HOLDER]
    sid = ECHO_HOLDER
    typ, aura, _misc, _bp = _eff(r, 0)
    if (typ, aura) != (EFF_APPLY_AURA, AURA_PERIODIC_TRIGGER):
        bad.append(f"{sid}: e0 is {typ}/{aura}, expected APPLY_AURA / 23 PERIODIC_TRIGGER_SPELL")
    if _i(r, "EffectAuraPeriod_1") != 3000 or dur_ms(r) != 3000:
        bad.append(f"{sid}: period {r.get('EffectAuraPeriod_1')!r} / duration {dur_ms(r)}, expected 3000 / 3000 "
                   f"(one tick, 3 s after the Thunder Clap)")
    if _i(r, "EffectTriggerSpell_1") != ECHO:
        bad.append(f"{sid}: e0 trigger {r.get('EffectTriggerSpell_1')!r}, expected {ECHO}")
    if (_i(r, "ImplicitTargetA_1"), _i(r, "ImplicitTargetB_1")) != (1, 0):
        bad.append(f"{sid}: e0 targets ({r.get('ImplicitTargetA_1')}, {r.get('ImplicitTargetB_1')}), expected the "
                   f"caster (1, 0): its position at apply is the Thunder Clap's spot")
    return bad


# SpellVisual 145 (Thunder Clap): CastKit 356 plays on the caster (stomp animation 181, hand lightning, ring, sound,
# shake). The echo's row keeps 145's ImpactKit / StateKit, has no kit that plays on the caster, and plays stock kit
# 7397 (the ring, sound 3090, shake 3, no animation, no hands) as its InstantAreaKit, at the destination.
ECHO_VISUAL_KITS = {"InstantAreaKit": 7397, "ImpactKit": 283, "StateKit": 360}
CASTER_KITS = ("PrecastKit", "CastKit", "ChannelKit", "CasterImpactKit", "StateDoneKit")


def check_echo_visual(row: dict) -> list[str]:
    sid = row.get("ID")
    bad = []
    if sid != warrior_vfx.SV_THUNDER_CLAP_ECHO:
        bad.append(f"SpellVisual {sid}: expected id {warrior_vfx.SV_THUNDER_CLAP_ECHO}")
    for col in CASTER_KITS:
        if _i(row, col):
            bad.append(f"SpellVisual {sid}: {col} {row.get(col)} plays on the warrior (the stomp would play again)")
    for col, want in ECHO_VISUAL_KITS.items():
        if _i(row, col) != want:
            bad.append(f"SpellVisual {sid}: {col} {row.get(col)!r}, expected {want}")
    if _i(row, "HasMissile") or _i(row, "ImpactAreaKit") or _i(row, "PersistentAreaKit"):
        bad.append(f"SpellVisual {sid}: carries a missile / impact-area / persistent-area kit")
    return bad


def check_small_rows(rows: dict, dur_ms) -> list[str]:
    bad = _missing(rows, SHIELD_DISCIPLINE_BUFF, CONCUSSED, VIGILANCE_THREAT)
    if bad:
        return bad
    sd, cz, vg = rows[SHIELD_DISCIPLINE_BUFF], rows[CONCUSSED], rows[VIGILANCE_THREAT]
    if dur_ms(sd) != 20000:
        bad.append(f"{SHIELD_DISCIPLINE_BUFF}: duration {dur_ms(sd)} ms, expected 20000")
    if sd.get("AuraDescription_Lang_enUS") != "Your next Thunder Clap grants a larger shield.":
        bad.append(f"{SHIELD_DISCIPLINE_BUFF}: aura text {sd.get('AuraDescription_Lang_enUS')!r}")
    if _eff(cz, 0)[1:] != (AURA_DMG_DONE_PCT, 127, -16):
        bad.append(f"{CONCUSSED}: e0 aura/misc/bp {_eff(cz, 0)[1:]}, expected (79, 127, -16)")
    if _eff(vg, 0)[0] != EFF_REDIRECT_THREAT or _eff(vg, 0)[3] != 9:
        bad.append(f"{VIGILANCE_THREAT}: e0 type/bp {_eff(vg, 0)[0]}/{_eff(vg, 0)[3]}, expected 130 / 9 (10%)")
    return bad


def check_bindings(names: list[dict], removals: list[dict]) -> list[str]:
    bad = []
    have: dict[int, set[str]] = {}
    for n in names:
        have.setdefault(int(n["spell_id"]), set()).add(n["ScriptName"])
    for sid, expect in sorted(S1_BINDINGS.items()):
        if have.get(sid, set()) != expect:
            bad.append(f"scripted_by on {sid}: {sorted(have.get(sid, set()))}, expected exactly {sorted(expect)}")
    gone = {(int(n["spell_id"]), n["ScriptName"]) for n in removals}
    for b in sorted(S1_UNBINDINGS - gone):
        bad.append(f"unbind_script {b} is not declared")
    # the unbound classes must not be re-bound
    for sid, name in sorted(S1_UNBINDINGS):
        if name in have.get(sid, set()):
            bad.append(f"{name} is both bound and unbound on {sid}")
    for sid in (-46951, 50687):
        if have.get(sid):
            bad.append(f"{sid}: still has scripted_by {sorted(have[sid])}")
    return bad


def check_proc_rows(procs: list[dict], proc_removals: list[dict]) -> list[str]:
    bad = []
    by_id = {int(p["SpellId"]): p for p in procs}
    for sid in IMPROVED_REVENGE:
        row = by_id.get(sid)
        if row is None:
            bad.append(f"{sid}: no spell_proc row")
        elif int(row["SpellPhaseMask"]) != 1:
            bad.append(f"{sid}: spell_phase_mask {row['SpellPhaseMask']!r}, expected 1 (cast, not hit)")
    gone = {int(r["SpellId"]) for r in proc_removals}
    for sid in sorted(S1_PROC_REMOVALS - gone):
        bad.append(f"remove_spell_proc({sid}) is not declared")
    for sid in S1_PROC_REMOVALS:
        if sid in by_id:
            bad.append(f"{sid}: a spell_proc row is still declared")
    return bad


def check_spell_levels(rows: dict) -> list[str]:
    bad = _missing(rows, *SPELL_LEVELS)
    if bad:
        return bad
    for sid, level in sorted(SPELL_LEVELS.items()):
        r = rows[sid]
        got = (_i(r, "SpellLevel"), _i(r, "BaseLevel"))
        if got != (level, level):
            bad.append(f"{sid}: SpellLevel/BaseLevel {got}, expected {(level, level)}")
        if _i(r, "MaxLevel") not in (0,):
            bad.append(f"{sid}: MaxLevel {r.get('MaxLevel')!r}, expected 0 (no slope; the 50 / 80 overrides are gone)")
    return bad


def _potency_of(entries: dict, sid: int, effect_1based: int) -> dict:
    return (entries.get(sid, {}).get(f"effect{effect_1based}") or {}).get("_potency") or {}


def check_devastate(rows: dict, entries: dict, corrections: list[dict]) -> list[str]:
    bad = _missing(rows, DEVASTATE)
    if bad:
        return bad
    r = rows[DEVASTATE]
    sid = DEVASTATE
    if _eff(r, 0)[0] != 0:
        bad.append(f"{sid}: e0 type {_eff(r, 0)[0]}, expected empty")
    if _eff(r, 1)[0] != EFF_WEAPON_PERCENT:
        bad.append(f"{sid}: e1 type {_eff(r, 1)[0]}, expected WEAPON_PERCENT_DAMAGE 31")
    if _eff(r, 2)[0] != EFF_NORMALIZED:
        bad.append(f"{sid}: e2 type {_eff(r, 2)[0]}, expected NORMALIZED_WEAPON_DMG 121")
    weapon = _potency_of(entries, sid, 2)
    if weapon.get("kind") != "weapon" or weapon.get("total_potency") != 120:
        bad.append(f"{sid}: effect 1 (DBC Effect_2) weapon potency {weapon.get('total_potency')!r}/"
                   f"{weapon.get('kind')!r}, expected 120 / weapon")
    flat = _potency_of(entries, sid, 3)
    if flat.get("total_potency") != 10 or flat.get("kind") != "direct":
        bad.append(f"{sid}: effect 2 (DBC Effect_3) potency {flat.get('total_potency')!r}/{flat.get('kind')!r}, "
                   "expected 10 / direct")
    # V = the built correction resolves to 25-27.5 at level 60; the 5-stack hit adds 5V = 50 potency (127-137.5 dmg)
    v = float(flat.get("level60_value") or 0)
    if not 25.0 <= v <= 27.5:
        bad.append(f"{sid}: V (effect 2 at level 60) {v}, expected 25-27.5")
    if not 125.0 <= 5 * v <= 137.5:
        bad.append(f"{sid}: 5 stacks add {5 * v}, expected 125-137.5")
    if not any(int(c["spell_id"]) == sid and int(c["effect_index"]) == 2 for c in corrections):
        bad.append(f"{sid}: no potency correction row (20243, 2)")
    if _i(r, "EquippedItemClass") != 4 or _i(r, "EquippedItemSubclass") != 64:
        bad.append(f"{sid}: the shield requirement changed")
    text = str(r.get("Description_Lang_enUS") or "")
    for frag in ("counting the application from this attack", "for each application of Sunder Armor"):
        if frag not in text:
            bad.append(f"{sid}: tooltip lacks {frag!r} (the engine counts n x V)")
    # S1-CODE-REVIEW N6: e0 is empty and Devastate applies no aura of its own, so no aura text
    if str(r.get("AuraDescription_Lang_enUS") or ""):
        bad.append(f"{sid}: aura text {r.get('AuraDescription_Lang_enUS')!r}, expected empty (no aura of its own)")
    return bad


def check_concussion_and_shockwave(rows: dict, entries: dict, corrections: list[dict]) -> list[str]:
    bad = _missing(rows, CONCUSSION_BLOW, SHOCKWAVE)
    if bad:
        return bad
    cb, sw = rows[CONCUSSION_BLOW], rows[SHOCKWAVE]
    if _eff(cb, 0)[:2] != (EFF_APPLY_AURA, 12):
        bad.append(f"{CONCUSSION_BLOW}: e0 {_eff(cb, 0)}, expected the stun APPLY_AURA 12")
    if _eff(cb, 1)[0] != EFF_SCHOOL_DAMAGE:
        bad.append(f"{CONCUSSION_BLOW}: e1 type {_eff(cb, 1)[0]}, expected SCHOOL_DAMAGE (the potency effect)")
    pot = _potency_of(entries, CONCUSSION_BLOW, 2)
    if pot.get("total_potency") != 54.6 or pot.get("kind") != "direct":
        bad.append(f"{CONCUSSION_BLOW}: effect 1 potency {pot.get('total_potency')!r}, expected 54.6 direct")
    if _potency_of(entries, CONCUSSION_BLOW, 3):
        bad.append(f"{CONCUSSION_BLOW}: effect 2 still carries a potency row")
    bad += _effect_empty(cb, 2, CONCUSSION_BLOW, "old DUMMY 38%")
    if _eff(cb, 2)[3]:
        bad.append(f"{CONCUSSION_BLOW}: e2 keeps bp {_eff(cb, 2)[3]} (the stock DUMMY 38%)")
    if not any(int(c["spell_id"]) == CONCUSSION_BLOW and int(c["effect_index"]) == 1 for c in corrections):
        bad.append(f"{CONCUSSION_BLOW}: no potency correction row (12809, 1)")
    if _eff(sw, 1)[0] != EFF_SCHOOL_DAMAGE:
        bad.append(f"{SHOCKWAVE}: e1 type {_eff(sw, 1)[0]}, expected SCHOOL_DAMAGE")
    pot = _potency_of(entries, SHOCKWAVE, 2)
    if pot.get("total_potency") != 107.7:
        bad.append(f"{SHOCKWAVE}: effect 1 potency {pot.get('total_potency')!r}, expected 107.7")
    if _u32(sw.get(M2)) & 0x8000 == 0:
        bad.append(f"{SHOCKWAVE}: lost its identity bit d1 0x8000 (Thunderstruck reads it)")
    return bad


def check_sdv(tooltip_vars: list[dict], rows: dict) -> list[str]:
    bad = []
    by_id = {int(t["id"]): t for t in tooltip_vars}
    for vid, ranks in sorted(SDV_ROWS.items()):
        t = by_id.get(vid)
        if t is None:
            bad.append(f"SpellDescriptionVariables {vid}: not declared")
            continue
        for rank in ranks:
            if f"${rank}m" not in t["Variables"]:
                bad.append(f"SDV {vid}: Variables do not read rank spell {rank}")
    if SDV_SKIPPED in by_id:
        bad.append(f"SDV {SDV_SKIPPED} exists (Shield Slam is skipped on purpose)")
    for sid, token in sorted(SDV_READERS.items()):
        text = str((rows.get(sid) or {}).get("Description_Lang_enUS") or "")
        if token not in text:
            bad.append(f"{sid}: description does not read {token}")
    if "$<" in str((rows.get(SHIELD_SLAM) or {}).get("Description_Lang_enUS") or ""):
        bad.append(f"{SHIELD_SLAM}: reads a tooltip variable (Shield Slam is skipped)")
    return bad


def check_new_ids(rows: dict) -> list[str]:
    bad = []
    got = sorted(sid for sid in rows if 204770 <= sid <= 204899)
    if got != sorted(S1_NEW_IDS):
        bad.append(f"ids in the S1 block 204770-204899: {got}, expected exactly {sorted(S1_NEW_IDS)}")
    return bad


def check_no_stray_dollar(rows: dict) -> list[str]:
    bad = []
    for sid in S1_AURA_IDS:
        r = rows.get(sid)
        if r is None:
            continue
        for col in ("Description_Lang_enUS", "AuraDescription_Lang_enUS"):
            if "$" in str(r.get(col) or ""):
                bad.append(f"{sid}: {col} has a '$': {r.get(col)!r}")
    for sid in S1_VARIABLE_TOOLTIP_IDS:
        text = str((rows.get(sid) or {}).get("Description_Lang_enUS") or "")
        text = re.sub(r"\$\{[^{}]*\}", "", text)       # ${...} expressions (potency text, SDV products)
        text = re.sub(r"\$[sdu]\d?\b", "", text)       # $s2 / $d / $u
        if "$" in text:
            bad.append(f"{sid}: description has an unrecognised '$' after removing the variable forms: {text!r}")
    return bad


def check_tooltips(rows: dict) -> list[str]:
    bad = []
    for sid, frags in sorted(TOOLTIP_FRAGMENTS.items()):
        r = rows.get(sid)
        if r is None:
            bad.append(f"{sid}: not built")
            continue
        text = str(r.get("Description_Lang_enUS") or "")
        for frag in frags:
            if frag not in text:
                bad.append(f"{sid}: tooltip lacks {frag!r}: {text!r}")
    for sid in (INCITE[0], INCITE[1], INCITE[2], 200056, 200057):
        if "mastery" in str((rows.get(sid) or {}).get("Description_Lang_enUS") or "").lower() and "Capstone" not in \
                str(rows[sid].get("Description_Lang_enUS")):
            bad.append(f"{sid}: still says 'increased by your mastery' (Incite / Reprisal lose it, D25)")
    return bad


def check_capstones(rows: dict) -> list[str]:
    """The 7 capstones in the T1 format: grey below the last rank, plain on it, the same clause on every rank."""
    bad = []
    for name, ranks in CAPSTONE_RANKS.items():
        if any(sid not in rows for sid in ranks):
            bad += _missing(rows, *ranks)
            continue
        if rows[ranks[0]].get("Name_Lang_enUS") != name:
            bad.append(f"{ranks[0]}: rank 1 is named {rows[ranks[0]].get('Name_Lang_enUS')!r}, expected {name!r}")
        descs = [rows[s].get("Description_Lang_enUS", "") for s in ranks]
        auras = [rows[s].get("AuraDescription_Lang_enUS", "") for s in ranks]
        bad += capfmt.rank_problems(name, descs, auras, list(ranks))
    # S2 adds the five Arms capstones to the same list (test_warrior_s2.py pins those), so S1's seven are a subset
    if not set(CAPSTONE_RANKS) <= set(capfmt.EXPECTED_CAPSTONES["warrior"]):
        bad.append(f"EXPECTED_CAPSTONES['warrior'] is {sorted(capfmt.EXPECTED_CAPSTONES['warrior'])}, S1 expects "
                   f"{sorted(CAPSTONE_RANKS)} in it")
    return bad


# ---- real data ----------------------------------------------------------------------------------------------------

_CACHE: dict = {}


def _dur_ms(row: dict) -> int:
    """The row's duration in ms through the stock SpellDuration.dbc (-1 = permanent)."""
    return _DUR.get(_i(row, "DurationIndex"), None) if _DUR else None


def _range_yd(row: dict) -> float | None:
    return _RANGE.get(_i(row, "RangeIndex")) if _RANGE else None


_DUR: dict[int, int] = {}
_RANGE: dict[int, float] = {}


def _data() -> dict:
    if not _CACHE:
        base = w0b._data()
        package = base["package"]
        _DUR.update({int(r["ID"]): int(r["Duration"]) for r in state.load_stock_rows(dbcfmt.SPELLDURATION).values()})
        _RANGE.update({int(r["ID"]): float(r["RangeMax_1"]) for r in state.load_stock_rows(dbcfmt.SPELLRANGE).values()})
        _CACHE.update(
            package=package, rows=base["rows"], entries=base["entries"], custom_attrs=base["custom_attrs"],
            talents=package.talents, procs=package.spell_procs, proc_removals=package.proc_removals,
            names=package.spell_script_names, removals=package.script_removals, bonus=package.spell_bonus_data,
            corrections=package.potency_corrections, tooltip_vars=package.tooltip_vars,
        )
    return _CACHE


class WarriorS1DataTest(unittest.TestCase):
    def assertClean(self, problems: list[str]):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_grid_cell_moves(self):
        self.assertClean(check_grid(_data()["talents"]))

    def test_improved_thunder_clap(self):
        self.assertClean(check_improved_thunder_clap(_data()["rows"]))

    def test_puncture(self):
        self.assertClean(check_puncture(_data()["rows"]))

    def test_focused_rage(self):
        self.assertClean(check_focused_rage(_data()["rows"]))

    def test_critical_block(self):
        self.assertClean(check_critical_block(_data()["rows"]))

    def test_the_wall(self):
        self.assertClean(check_the_wall(_data()["rows"]))

    def test_safeguard(self):
        self.assertClean(check_safeguard(_data()["rows"]))

    def test_no_empty_mask_spellmod(self):
        self.assertClean(check_empty_mask_spellmods(_data()["rows"]))

    def test_sword_and_board(self):
        self.assertClean(check_sword_and_board(_data()["rows"]))

    def test_iron_temper_and_tempered(self):
        self.assertClean(check_iron_temper(_data()["rows"]))

    def test_unwavering_sentinel(self):
        self.assertClean(check_unwavering_sentinel(_data()["rows"]))

    def test_thunderstruck(self):
        self.assertClean(check_thunderstruck(_data()["rows"]))

    def test_improved_bloodrage_ranks(self):
        self.assertClean(check_improved_bloodrage(_data()["rows"]))

    def test_shield_cover_and_firm_grip(self):
        self.assertClean(check_shield_cover_and_firm_grip(_data()["rows"]))

    def test_improved_bloodrage_buff(self):
        _data()
        self.assertClean(check_bloodrage_buff(_data()["rows"], _dur_ms))

    def test_empowered_revenge(self):
        _data()
        self.assertClean(check_empowered_revenge(_data()["rows"], _dur_ms))

    def test_bloodstorm_tick(self):
        d = _data()
        self.assertClean(check_bloodstorm_tick(d["rows"], d["entries"], d["custom_attrs"], d["bonus"],
                                               d["corrections"], _range_yd))

    def test_bloodstorm_holder(self):
        self.assertClean(check_bloodstorm_holder(_data()["rows"], _dur_ms))

    def test_thunder_clap_echo(self):
        d = _data()
        self.assertClean(check_echo(d["rows"], d["entries"], _dur_ms))

    def test_thunder_clap_echo_holder(self):
        _data()
        self.assertClean(check_echo_holder(_data()["rows"], _dur_ms))

    @unittest.skipUnless((warrior_vfx.DBC_DIR / "SpellVisual.dbc").is_file(), "no model-visual working copy")
    def test_thunder_clap_echo_visual(self):
        rows = warrior_vfx.build_spellvisual_rows()
        self.assertEqual(len(rows), 1)
        self.assertClean(check_echo_visual(rows[0]))
        # the area kit is the stock one: Thunder Clap's ring, sound and shake, no animation and no hand effects
        kit = next(k for k in dbcfile.read_dbc(warrior_vfx.DBC_DIR / "SpellVisualKit.dbc", dbcfmt.SPELLVISUALKIT)
                   if k["ID"] == ECHO_VISUAL_KITS["InstantAreaKit"])
        self.assertEqual((kit["WorldEffect"], kit["SoundID"], kit["ShakeID"]), (349, 3090, 3))
        self.assertEqual((_u32(kit["AnimID"]), kit["LeftHandEffect"], kit["RightHandEffect"]), (0xFFFFFFFF, 0, 0))

    def test_shield_discipline_concussed_vigilance(self):
        self.assertClean(check_small_rows(_data()["rows"], _dur_ms))

    def test_bindings(self):
        d = _data()
        self.assertClean(check_bindings(d["names"], d["removals"]))

    def test_proc_rows(self):
        d = _data()
        self.assertClean(check_proc_rows(d["procs"], d["proc_removals"]))

    def test_spell_levels(self):
        self.assertClean(check_spell_levels(_data()["rows"]))

    def test_devastate(self):
        d = _data()
        self.assertClean(check_devastate(d["rows"], d["entries"], d["corrections"]))

    def test_concussion_blow_and_shockwave(self):
        d = _data()
        self.assertClean(check_concussion_and_shockwave(d["rows"], d["entries"], d["corrections"]))

    def test_spell_description_variables(self):
        d = _data()
        self.assertClean(check_sdv(d["tooltip_vars"], d["rows"]))

    def test_new_ids(self):
        self.assertClean(check_new_ids(_data()["rows"]))

    def test_no_stray_dollar(self):
        self.assertClean(check_no_stray_dollar(_data()["rows"]))

    def test_tooltips_match_the_doc(self):
        self.assertClean(check_tooltips(_data()["rows"]))

    def test_capstone_format(self):
        self.assertClean(check_capstones(_data()["rows"]))


# ---- negative fixtures: every check must fire on a minimal bad mutation of the real built rows -------------------

def _mut(rows: dict, sid: int, **cols) -> dict:
    return {**rows, sid: {**rows[sid], **cols}}


class WarriorS1NegativeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = _data()
        cls.rows = cls.d["rows"]

    def fires(self, check, mutations, *extra, missing=True):
        """`check(rows, *extra)` is clean on the real rows and reports on each (sid, column, value) mutation, and (when
        `missing`) on the first mutated row never having been built."""
        self.assertEqual(check(self.rows, *extra), [], check.__name__)
        for sid, col, val in mutations:
            self.assertGreaterEqual(len(check(_mut(self.rows, sid, **{col: val}), *extra)), 1,
                                    (check.__name__, sid, col, val))
        if missing:
            sid = mutations[0][0]
            self.assertGreaterEqual(len(check({k: v for k, v in self.rows.items() if k != sid}, *extra)), 1)

    def test_grid(self):
        talents = self.d["talents"]
        self.assertEqual(check_grid(talents), [])
        for tid, (tier, col) in GRID_MOVES.items():
            for field, val in (("tier", tier + 1), ("column", (col + 1) % 4)):
                mutated = [{**t, field: val} if int(t["id"]) == tid else t for t in talents]
                self.assertGreaterEqual(len(check_grid(mutated)), 1, (tid, field))
        # a collision: Storm's Bulwark onto Reprisal's cell
        collide = [{**t, "tier": 3, "column": 1} if int(t["id"]) == 60005 else t for t in talents]
        self.assertTrue(any("share the cell" in p for p in check_grid(collide)))
        # a prerequisite where none are set
        dep = [{**t, "depends_on": {"talent_id": 140, "rank": 1}} if int(t["id"]) == 60005 else t for t in talents]
        self.assertTrue(any("prerequisite" in p for p in check_grid(dep)))
        self.assertGreaterEqual(len(check_grid([t for t in talents if int(t["id"]) != 60005])), 1)

    def test_improved_thunder_clap(self):
        self.fires(check_improved_thunder_clap, [
            (12287, "EffectMiscValue_1", 14),            # still the COST mod
            (12665, "EffectBasePoints_1", 0),            # radius bp wrong
            (12287, "EffectSpellClassMaskA_1", 0),       # RADIUS mod loses its mask
            (12287, "EffectSpellClassMaskA_1", 0x100),
            (12666, "EffectSpellClassMaskC_1", 0),       # EFFECT2 mod loses its mask (e2.d0)
            (12666, "EffectSpellClassMaskB_1", 0),       # damage mod loses its mask (e1.d0)
            (12287, "EffectSpellClassMaskC_2", 0x80),    # EFFECT2 mod on the wrong dword too
            (12665, "EffectMiscValue_3", 2),             # EFFECT2 -> THREAT
            (12666, "EffectBasePoints_3", -5),           # slow rank value wrong
            (12287, "Effect_3", 0),                      # the new effect is gone
        ])

    def test_puncture(self):
        self.fires(check_puncture, [
            (12308, "EffectSpellClassMaskA_1", 0x40),    # right bit, wrong dword (d0)
            (12308, "EffectSpellClassMaskA_2", 0),
            (12810, "EffectSpellClassMaskA_2", 0x80),
            (12811, "EffectBasePoints_1", 4),
            (12308, "EffectMiscValue_1", 14),            # COST again
            (12810, "EffectAura_2", 108),                # armor effect lost
            (12811, "EffectSpellClassMaskB_2", 0x40),    # stray mask on the armor effect
        ])

    def test_focused_rage(self):
        self.fires(check_focused_rage, [
            (29787, "EffectAura_1", 107),                # a SpellMod again
            (29787, "EffectBasePoints_1", 0),
            (29790, "EffectSpellClassMaskA_1", 0x6E6E4EEE),   # the live leak mask
            (29792, "EffectSpellClassMaskA_2", 0x40E664),
            (29792, "EffectSpellClassMaskB_1", 1),
            (29790, "Effect_2", 6),
        ])

    def test_critical_block(self):
        self.fires(check_critical_block, [
            (47294, "EffectSpellClassMaskA_2", 0x40),     # Devastate's bit
            (47294, "EffectSpellClassMaskA_2", 0),
            (47295, "EffectSpellClassMaskA_1", 0x200),    # right bit, wrong dword
            (47295, "EffectMiscValue_1", 0),
            (47296, "EffectBasePoints_1", 8),
            (47296, "EffectAura_2", 107),                 # the marker became a SpellMod
            (47294, "EffectSpellClassMaskB_2", 0x200),    # stale mask back on the marker
            (47294, "SpellIconID", 2777),
            (47295, "EffectBasePoints_2", 7),
        ])

    def test_the_wall(self):
        self.fires(check_the_wall, [
            (12312, "Name_Lang_enUS", "Improved Disciplines"),
            (12312, "EffectSpellClassMaskA_1", 0x2010),   # Recklessness bit back
            (12803, "EffectSpellClassMaskA_2", 0x8),      # Retaliation bit back
            (12312, "EffectSpellClassMaskB_1", 0x2000),   # the stale residue on e1
            (12803, "EffectSpellClassMaskC_1", 1),
            (12803, "EffectBasePoints_1", -40001),
            (12312, "EffectMiscValue_1", 14),
        ])

    def test_safeguard(self):
        self.fires(check_safeguard, [
            (46945, "EffectSpellClassMaskA_2", 0),
            (46945, "EffectSpellClassMaskA_1", 0x10000),   # wrong dword
            (46949, "EffectBasePoints_1", -11),
            (46945, "EffectMiscValue_1", 14),
            (46945, "EffectAura_2", 42),                   # the proc trigger came back
            (46945, "ProcTypeMask", 1024),
            (46949, "ProcChance", 100),
            (46949, "EffectSpellClassMaskB_1", 0x40000001),
        ])

    def test_empty_mask_spellmod(self):
        self.fires(check_empty_mask_spellmods, [
            (29787, "EffectAura_1", 107),                  # Focused Rage as an empty-mask SpellMod
            (47294, "EffectSpellClassMaskA_2", 0),
            (200041, "EffectSpellClassMaskC_2", 0),
            (204770, "EffectSpellClassMaskA_1", 0),
            (50227, "EffectSpellClassMaskB_2", 0),
        ], missing=False)

    def test_sword_and_board(self):
        self.fires(check_sword_and_board, [
            (46951, "EffectAura_1", 42),
            (46952, "EffectBasePoints_1", 9),
            (46953, "EffectSpellClassMaskA_1", 0x400),
            (46951, "ProcTypeMask", 16),
            (46952, "ProcChance", 20),
            (50227, "EffectSpellClassMaskB_1", 0x400),      # the Revenge bit
            (50227, "EffectSpellClassMaskB_2", 0),
            (50227, "EffectSpellClassMaskB_3", 0x200),      # right bit, wrong dword
            (50227, "EffectBasePoints_2", -1),              # the stale raw bp
            (50227, "EffectBasePoints_1", -1),
            (50227, "EffectSpellClassMaskA_2", 0x400),
            (50227, "ProcCharges", 0),
            (50227, "DurationIndex", 21),
            (50227, "AuraDescription_Lang_enUS", "Devastate or Revenge ability deals damage"),
        ])

    def test_iron_temper(self):
        self.fires(check_iron_temper, [
            (29593, "EffectAura_1", 42),
            (29593, "EffectBasePoints_1", -3),
            (29594, "EffectBasePoints_1", -6),
            (29593, "ShapeshiftMask", 131072),
            (29594, "ProcTypeMask", 174760),
            (29593, "ProcChance", 50),
            (200050, "Name_Lang_enUS", "Enrage (Iron Temper)"),
            (200050, "DurationIndex", 29),
            (200050, "EffectAura_1", 79),                   # effects not swapped
            (200050, "EffectAura_2", 87),
            (200050, "EffectBasePoints_2", 4),
            (200050, "EffectBasePoints_1", 4),              # a reduction stored positive
        ])

    def test_unwavering_sentinel(self):
        self.fires(check_unwavering_sentinel, [
            (200034, "Name_Lang_enUS", "Unbridled Wrath"),
            (200034, "EffectMiscValue_1", 1 << 21),
            (200035, "EffectBasePoints_1", 0),
            (200036, "EffectAura_1", 189),
            (200036, "EffectSpellClassMaskA_1", 1),
        ])

    def test_thunderstruck(self):
        self.fires(check_thunderstruck, [
            (200051, "Effect_2", 6),                         # the threat effect is back
            (200051, "EffectAura_2", 108),
            (200052, "EffectSpellClassMaskB_2", 0x8000),
            (200053, "EffectAura_3", 107),
            (200051, "EffectBasePoints_3", 0),
            (200052, "EffectBasePoints_1", 9),
            (200053, "EffectSpellClassMaskA_2", 0),
            (200053, "EffectSpellClassMaskA_1", 0),
        ])

    def test_improved_bloodrage(self):
        self.fires(check_improved_bloodrage, [
            (12301, "EffectAura_2", 87),
            (12301, "EffectBasePoints_2", 3),
            (12818, "EffectBasePoints_2", 1),
            (12301, "ShapeshiftMask", 131072),
            (12818, "EffectSpellClassMaskA_1", 0),
            (12301, "EffectSpellClassMaskB_1", 0x100),
        ])

    def test_shield_cover_and_firm_grip(self):
        self.fires(check_shield_cover_and_firm_grip, [
            (200041, "EffectMiscValue_1", 1),                # physical only again
            (200042, "EffectBasePoints_1", -2),
            (200038, "EquippedItemClass", 4),
            (200039, "EquippedItemSubclass", 64),
            (200040, "EquippedItemClass", 4),
            (200038, "EffectAura_3", 0),
            (200039, "EffectAura_2", 0),
        ])

    def test_bloodrage_buff(self):
        r = self.rows[IMPROVED_BLOODRAGE_BUFF]
        self.assertEqual(check_bloodrage_buff(self.rows, _dur_ms), [])
        for col, val in (("ShapeshiftMask", 0), ("Attributes", 0x80 | ATTR0_NOT_SHAPESHIFTED),
                         ("AttributesEx2", ATTR2_ALLOW_WHILE_NOT_SHAPESHIFTED), ("Attributes", 0),
                         ("Attributes", 0x40 | 0x80), ("DurationIndex", 21), ("EffectAura_1", 3),
                         ("EffectMiscValue_1", 1), ("EffectBasePoints_1", 1), ("Effect_2", 6),
                         ("EffectSpellClassMaskA_1", 1)):
            self.assertGreaterEqual(len(check_bloodrage_buff(_mut(self.rows, IMPROVED_BLOODRAGE_BUFF, **{col: val}),
                                                             _dur_ms)), 1, (col, val))
        self.assertGreaterEqual(len(check_bloodrage_buff({}, _dur_ms)), 1)
        self.assertEqual(r["ShapeshiftMask"], 131072)

    def test_empowered_revenge(self):
        self.assertEqual(check_empowered_revenge(self.rows, _dur_ms), [])
        for col, val in (("DurationIndex", 21), ("ProcCharges", 0), ("EffectSpellClassMaskA_1", 0),
                         ("EffectSpellClassMaskA_2", 0x400), ("EffectBasePoints_1", 9), ("EffectMiscValue_1", 14),
                         ("EffectAura_1", 107), ("Attributes", 0x80), ("Attributes", 0x40),
                         ("AuraDescription_Lang_enUS", "")):
            self.assertGreaterEqual(len(check_empowered_revenge(_mut(self.rows, EMPOWERED_REVENGE, **{col: val}),
                                                                _dur_ms)), 1, (col, val))

    def test_bloodstorm_tick(self):
        d = self.d
        args = (d["entries"], d["custom_attrs"], d["bonus"], d["corrections"], _range_yd)
        self.assertEqual(check_bloodstorm_tick(self.rows, *args), [])
        for col, val in (("Attributes", 0), ("AttributesEx2", 0), ("AttributesEx2", 0x20000000), ("AttributesEx2", 0x4),
                         ("AttributesEx2", 0x20000000 | 0x4 | 0x80000),
                         ("AttributesEx3", 0x20000000), ("AttributesEx3", 0x50000), ("RangeIndex", 7),
                         ("Effect_1", 6), ("SchoolMask", 4), ("Mechanic", 0), ("EffectMechanic_1", 0),
                         ("SpellClassMask_1", 0x80), ("EffectSpellClassMaskA_1", 1)):
            self.assertGreaterEqual(len(check_bloodstorm_tick(_mut(self.rows, BLOODSTORM_TICK, **{col: val}), *args)),
                                    1, (col, val))
        self.assertGreaterEqual(len(check_bloodstorm_tick(self.rows, d["entries"], {}, d["bonus"], d["corrections"],
                                                          _range_yd)), 1)     # custom_attr missing
        self.assertGreaterEqual(len(check_bloodstorm_tick(self.rows, d["entries"], {BLOODSTORM_TICK: 0x200000},
                                                          d["bonus"], d["corrections"], _range_yd)), 1)
        pot = {**d["entries"], BLOODSTORM_TICK: {**d["entries"][BLOODSTORM_TICK], "effect1": {"_potency": {"x": 1}}}}
        self.assertGreaterEqual(len(check_bloodstorm_tick(self.rows, pot, d["custom_attrs"], d["bonus"],
                                                          d["corrections"], _range_yd)), 1)
        self.assertGreaterEqual(len(check_bloodstorm_tick(self.rows, d["entries"], d["custom_attrs"],
                                                          [*d["bonus"], {"entry": BLOODSTORM_TICK}],
                                                          d["corrections"], _range_yd)), 1)
        self.assertGreaterEqual(len(check_bloodstorm_tick(self.rows, d["entries"], d["custom_attrs"], d["bonus"],
                                                          [*d["corrections"], {"spell_id": BLOODSTORM_TICK}],
                                                          _range_yd)), 1)

    def test_bloodstorm_holder(self):
        self.assertEqual(check_bloodstorm_holder(self.rows, _dur_ms), [])
        for col, val in (("EffectAura_1", 3), ("EffectAuraPeriod_1", 1000), ("AttributesEx5", ATTR5_HASTE_PERIODIC),
                         ("DurationIndex", 21), ("AuraDescription_Lang_enUS", "Bleeding for damage."), ("Mechanic", 0),
                         ("Effect_1", 3)):
            self.assertGreaterEqual(len(check_bloodstorm_holder(_mut(self.rows, BLOODSTORM, **{col: val}),
                                                                _dur_ms)), 1, (col, val))

    def test_echo(self):
        d = self.d
        self.assertEqual(check_echo(self.rows, d["entries"], _dur_ms), [])
        for col, val in (("DurationIndex", 21), ("EffectAura_2", 3), ("EffectBasePoints_2", -9),
                         ("EffectMechanic_2", 0), ("ImplicitTargetA_2", 6), ("ImplicitTargetB_2", 0),
                         ("EffectRadiusIndex_2", 7), ("SpellClassMask_1", 0), ("Effect_1", 3),
                         ("EffectMiscValue_2", 4), ("DefenseType", 0), ("DefenseType", 2),
                         ("AttributesEx2", ATTR2_CANT_CRIT)):
            self.assertGreaterEqual(len(check_echo(_mut(self.rows, ECHO, **{col: val}), d["entries"], _dur_ms)), 1,
                                    (col, val))
        bad_pot = {**d["entries"], ECHO: {**d["entries"][ECHO], "effect1": {"_potency": {"total_potency": 44.9}}}}
        self.assertGreaterEqual(len(check_echo(self.rows, bad_pot, _dur_ms)), 1)
        # caster-centred targets (the old 22/15), a range index, Thunder Clap's own visual 145 (plays on the warrior)
        for col, val in (("ImplicitTargetA_1", 22), ("ImplicitTargetB_1", 15), ("ImplicitTargetA_2", 22),
                         ("ImplicitTargetB_2", 15), ("RangeIndex", 2), ("SpellVisualID_1", 145)):
            self.assertGreaterEqual(len(check_echo(_mut(self.rows, ECHO, **{col: val}), d["entries"], _dur_ms)), 1,
                                    (col, val))

    def test_echo_holder(self):
        self.assertEqual(check_echo_holder(self.rows, _dur_ms), [])
        for col, val in (("EffectAura_1", 226), ("EffectAuraPeriod_1", 2000), ("DurationIndex", 9),
                         ("EffectTriggerSpell_1", 6343), ("ImplicitTargetA_1", 22)):
            self.assertGreaterEqual(len(check_echo_holder(_mut(self.rows, ECHO_HOLDER, **{col: val}), _dur_ms)), 1,
                                    (col, val))

    def test_echo_visual(self):
        good = {"ID": warrior_vfx.SV_THUNDER_CLAP_ECHO, "InstantAreaKit": 7397, "ImpactKit": 283, "StateKit": 360,
                "MissileAttachment": -1, "MissileDestinationAttachment": 1}
        self.assertEqual(check_echo_visual(good), [])
        for col, val in (("CastKit", 356), ("PrecastKit", 1), ("ChannelKit", 1), ("InstantAreaKit", 0),
                         ("InstantAreaKit", 9208), ("ImpactKit", 0), ("StateKit", 0), ("ImpactAreaKit", 9208),
                         ("HasMissile", 1), ("ID", 145)):
            self.assertGreaterEqual(len(check_echo_visual({**good, col: val})), 1, (col, val))

    def test_small_rows(self):
        self.assertEqual(check_small_rows(self.rows, _dur_ms), [])
        for sid, col, val in ((SHIELD_DISCIPLINE_BUFF, "DurationIndex", 9),
                              (SHIELD_DISCIPLINE_BUFF, "AuraDescription_Lang_enUS", ""),
                              (CONCUSSED, "EffectBasePoints_1", -15), (CONCUSSED, "EffectMiscValue_1", 1),
                              (VIGILANCE_THREAT, "EffectBasePoints_1", 14), (VIGILANCE_THREAT, "Effect_1", 2)):
            self.assertGreaterEqual(len(check_small_rows(_mut(self.rows, sid, **{col: val}), _dur_ms)), 1,
                                    (sid, col))

    def test_bindings(self):
        names, rem = self.d["names"], self.d["removals"]
        self.assertEqual(check_bindings(names, rem), [])
        # every S1 binding dropped / extra script added / unbind dropped / unbound class re-bound
        for i, n in enumerate(names):
            if int(n["spell_id"]) in S1_BINDINGS:
                self.assertGreaterEqual(len(check_bindings(names[:i] + names[i + 1:], rem)), 1, n)
        for sid in S1_BOUND_IDS:
            extra = {"spell_id": sid, "ScriptName": "spell_warr_something_else"}
            self.assertGreaterEqual(len(check_bindings([*names, extra], rem)), 1, sid)
        for i in range(len(rem)):
            if (int(rem[i]["spell_id"]), rem[i]["ScriptName"]) in S1_UNBINDINGS:
                self.assertGreaterEqual(len(check_bindings(names, rem[:i] + rem[i + 1:])), 1, rem[i])
        rebound = [*names, {"spell_id": CONCUSSION_BLOW, "ScriptName": "spell_warr_concussion_blow"}]
        self.assertGreaterEqual(len(check_bindings(rebound, rem)), 1)

    def test_proc_rows(self):
        procs, rem = self.d["procs"], self.d["proc_removals"]
        self.assertEqual(check_proc_rows(procs, rem), [])
        for sid in IMPROVED_REVENGE:
            mutated = [{**p, "SpellPhaseMask": 2} if int(p["SpellId"]) == sid else p for p in procs]
            self.assertGreaterEqual(len(check_proc_rows(mutated, rem)), 1, sid)
            self.assertGreaterEqual(len(check_proc_rows([p for p in procs if int(p["SpellId"]) != sid], rem)), 1)
        for i, r in enumerate(rem):
            if int(r["SpellId"]) in S1_PROC_REMOVALS:
                self.assertGreaterEqual(len(check_proc_rows(procs, rem[:i] + rem[i + 1:])), 1, r)
        for sid in (29593, 46945, 46951):
            self.assertGreaterEqual(len(check_proc_rows([*procs, {"SpellId": -sid, "SpellPhaseMask": 1}], rem)), 1)

    def test_spell_levels(self):
        self.fires(check_spell_levels, [
            (DEVASTATE, "SpellLevel", 50), (DEVASTATE, "BaseLevel", 50), (DEVASTATE, "MaxLevel", 80),
            (LAST_STAND, "SpellLevel", 1), (CONCUSSION_BLOW, "BaseLevel", 1), (SHOCKWAVE, "SpellLevel", 50),
        ])

    def test_devastate(self):
        d = self.d
        self.assertEqual(check_devastate(self.rows, d["entries"], d["corrections"]), [])
        for col, val in (("Effect_2", 121), ("Effect_3", 31), ("Effect_1", 6), ("EquippedItemClass", -1),
                         ("EquippedItemSubclass", 0), ("AuraDescription_Lang_enUS", "Armor decreased by $s1."),
                         ("Description_Lang_enUS", "causes 120% weapon damage plus 10 for each application of Sunder "
                                                   "Armor on the target.")):
            self.assertGreaterEqual(len(check_devastate(_mut(self.rows, DEVASTATE, **{col: val}), d["entries"],
                                                        d["corrections"])), 1, (col, val))

        def with_potency(effect, **kw):
            eff = {**d["entries"][DEVASTATE][f"effect{effect}"]}
            eff["_potency"] = {**eff["_potency"], **kw}
            return {**d["entries"], DEVASTATE: {**d["entries"][DEVASTATE], f"effect{effect}": eff}}
        for effect, kw in ((3, {"total_potency": 2.0}), (3, {"total_potency": 50.0}), (3, {"kind": "periodic"}),
                           (3, {"level60_value": 20.0}), (3, {"level60_value": 30.0}),
                           (2, {"total_potency": 100}), (2, {"kind": "direct"})):
            self.assertGreaterEqual(len(check_devastate(self.rows, with_potency(effect, **kw), d["corrections"])), 1,
                                    (effect, kw))
        no_corr = [c for c in d["corrections"] if not (int(c["spell_id"]) == DEVASTATE and int(c["effect_index"]) == 2)]
        self.assertGreaterEqual(len(check_devastate(self.rows, d["entries"], no_corr)), 1)

    def test_concussion_and_shockwave(self):
        d = self.d
        self.assertEqual(check_concussion_and_shockwave(self.rows, d["entries"], d["corrections"]), [])
        for sid, col, val in ((CONCUSSION_BLOW, "Effect_2", 3), (CONCUSSION_BLOW, "Effect_3", 3),
                              (CONCUSSION_BLOW, "EffectBasePoints_3", 37), (CONCUSSION_BLOW, "EffectAura_1", 3),
                              (SHOCKWAVE, "Effect_2", 3), (SHOCKWAVE, "SpellClassMask_2", 0)):
            self.assertGreaterEqual(len(check_concussion_and_shockwave(_mut(self.rows, sid, **{col: val}),
                                                                       d["entries"], d["corrections"])), 1, (sid, col))
        for sid, effect, total in ((CONCUSSION_BLOW, 2, 38.0), (SHOCKWAVE, 2, 100.0)):
            eff = {**d["entries"][sid][f"effect{effect}"]}
            eff["_potency"] = {**eff["_potency"], "total_potency": total}
            entries = {**d["entries"], sid: {**d["entries"][sid], f"effect{effect}": eff}}
            self.assertGreaterEqual(len(check_concussion_and_shockwave(self.rows, entries, d["corrections"])), 1, sid)
        on_dummy = {**d["entries"], CONCUSSION_BLOW: {**d["entries"][CONCUSSION_BLOW],
                                                      "effect3": {"_potency": {"total_potency": 54.6}}}}
        self.assertGreaterEqual(len(check_concussion_and_shockwave(self.rows, on_dummy, d["corrections"])), 1)
        no_corr = [c for c in d["corrections"] if int(c["spell_id"]) != CONCUSSION_BLOW]
        self.assertGreaterEqual(len(check_concussion_and_shockwave(self.rows, d["entries"], no_corr)), 1)

    def test_sdv(self):
        tv = self.d["tooltip_vars"]
        self.assertEqual(check_sdv(tv, self.rows), [])
        self.assertGreaterEqual(len(check_sdv([t for t in tv if int(t["id"]) != 1421], self.rows)), 1)
        self.assertGreaterEqual(len(check_sdv([*tv, {"id": SDV_SKIPPED, "Variables": "$x=1"}], self.rows)), 1)
        broken = [{**t, "Variables": t["Variables"].replace("$12308m", "$99m")} if int(t["id"]) == 1421 else t
                  for t in tv]
        self.assertGreaterEqual(len(check_sdv(broken, self.rows)), 1)
        for sid, token in SDV_READERS.items():
            text = self.rows[sid]["Description_Lang_enUS"].replace(token, "1")
            self.assertGreaterEqual(len(check_sdv(tv, _mut(self.rows, sid, Description_Lang_enUS=text))), 1, sid)
        shield_slam = _mut(self.rows, SHIELD_SLAM, Description_Lang_enUS="x $<mult> y")
        self.assertGreaterEqual(len(check_sdv(tv, shield_slam)), 1)

    def test_new_ids(self):
        self.assertEqual(check_new_ids(self.rows), [])
        for extra in (204771, 204772, 204773, 204776, 204799, 204869):
            self.assertGreaterEqual(len(check_new_ids({**self.rows, extra: {}})), 1, extra)
        for sid in S1_NEW_IDS:
            self.assertGreaterEqual(len(check_new_ids({k: v for k, v in self.rows.items() if k != sid})), 1, sid)

    def test_no_stray_dollar(self):
        self.assertEqual(check_no_stray_dollar(self.rows), [])
        for sid in (12287, 200058, 50227, 200030, 204770, 204774, 200028, 59665):
            for col in ("Description_Lang_enUS", "AuraDescription_Lang_enUS"):
                self.assertGreaterEqual(len(check_no_stray_dollar(_mut(self.rows, sid, **{col: "reduces by $s1%"}))), 1,
                                        (sid, col))
        for sid in S1_VARIABLE_TOOLTIP_IDS:
            text = self.rows[sid]["Description_Lang_enUS"] + " $x"
            mutated = _mut(self.rows, sid, Description_Lang_enUS=text)
            self.assertGreaterEqual(len(check_no_stray_dollar(mutated)), 1, sid)

    def test_tooltips(self):
        self.assertEqual(check_tooltips(self.rows), [])
        for sid, frags in TOOLTIP_FRAGMENTS.items():
            text = self.rows[sid]["Description_Lang_enUS"].replace(frags[0], "X")
            self.assertGreaterEqual(len(check_tooltips(_mut(self.rows, sid, Description_Lang_enUS=text))), 1, sid)
        stale = self.rows[200056]["Description_Lang_enUS"] + " increased by your mastery"
        self.assertGreaterEqual(len(check_tooltips(_mut(self.rows, 200056, Description_Lang_enUS=stale))), 1)

    def test_capstones(self):
        self.assertEqual(check_capstones(self.rows), [])
        for name, ranks in CAPSTONE_RANKS.items():
            grey, last = ranks[0], ranks[-1]
            plain = self.rows[grey]["Description_Lang_enUS"].replace(capfmt.GREY, "")
            self.assertGreaterEqual(len(check_capstones(_mut(self.rows, grey, Description_Lang_enUS=plain))), 1, name)
            coloured = self.rows[last]["Description_Lang_enUS"].replace(
                "\n\nCapstone", f"\n\n{capfmt.GREY}Capstone") + capfmt.RESET
            self.assertGreaterEqual(len(check_capstones(_mut(self.rows, last, Description_Lang_enUS=coloured))), 1,
                                    name)
            clause_gone = self.rows[last]["Description_Lang_enUS"].split("\n\n")[0]
            self.assertGreaterEqual(len(check_capstones(_mut(self.rows, last, Description_Lang_enUS=clause_gone))), 1,
                                    name)
            in_aura = _mut(self.rows, grey, AuraDescription_Lang_enUS="Capstone Bonus: x")
            self.assertGreaterEqual(len(check_capstones(in_aura)), 1, name)
        self.assertGreaterEqual(len(check_capstones({k: v for k, v in self.rows.items() if k != 12803})), 1)
        self.assertGreaterEqual(len(check_capstones(_mut(self.rows, 12312, Name_Lang_enUS="Improved Disciplines"))), 1)


if __name__ == "__main__":
    unittest.main()
