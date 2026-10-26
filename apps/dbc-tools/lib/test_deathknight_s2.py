"""
Death Knight S2 (Frost) data gate (death-knight-rework S2a-HANDOFF row A5, S2a-WP-BRIEF).

Same shape as lib/test_deathknight_s1.py: the real deathknight DSL package is loaded once (shared `_data()` cache) and
every check runs on the BUILT rows (stock base + DSL + raw_overrides), so a stale `raw_overrides` twin that wins over
the DSL fails here too. Each check is a pure function that returns problem strings, with a negative fixture below.
The tests are written from the SPEC (S2a-HANDOFF, S2a-WP-BRIEF D1-D17, S2-HANDOFF sections 3-5), not from the data, so
they fail until the DSL rows land. An id no agent has declared yet is reported by `test_required_ids_declared` and
skipped by the other checks.

  1. Grid: tab 399 holds the 36 talents of S2-HANDOFF section 3 at the right cells and rank lists, 85 points, no
     prerequisite (Improved Icy Talons 2223 is retired, user ruling 2026-10-25; cell (5,0) stays empty; its party haste
     55610 is the Icy Talons rank 3 capstone, check 18). 2. The three new castables' SkillLineAbility rows (30750-30752,
     skill 771, class 32, acquire 0).
  3. Howling Blast 49184: potency 62 (S2 TUNE; was 90) / SL 20, RuneCostID 647, effect 2 TRIGGER_SPELL 55095 with no stale twin.
  4. Potency rows (Glacial Eruption, Breath tick, Hungering Cold tick, Avalanche, Howling Blast): total potency,
     time_basis (1.5 / 1 / 2 / 1.5 s) and SpellLevel (9 + 5 * tier + rank).
  5. Glacial Advance / Breath: magic-class (no IS_ABILITY), Breath 2 min cooldown, Glacial Advance costs RP.
  6. d2 b9 / b10 / b16 carriers exactly per S2-HANDOFF section 5 (readers: Runic Focus + Razorice at least).
  7. No S2 row on a FORBIDDEN bit (stock-kept bits exempt) or on d2 b13 (Runic Focus keeps its S1 reader).
  8. Runic Focus effect mask holds d2 0x10600.
  9. Killing Machine buff 203320 (CumulativeAura 2, no charges, no spell_proc, +100 crit on Obliterate) and the ranks'
     positive spell_proc rows (6/12/20 %, no PPM) + the D8 removals / rebinds.
 10. Neutralised hardcodes: no Merciless / Tundra rank with misc 7277 or a TargetAuraState, Glacier Rot ranks not on
     icon 196, Annihilation without an icon-2710 DUMMY, Blood of the North without PERIODIC_DUMMY (and its D9 removals).
 11. Spell_proc phases: the CAST-phase talents are phase 1, every other DONE spell-class / periodic row is phase 2.
 12. Off-hand copies 66198 / 66188 / 66216 / 203322 / 66196: percent first, flat second, EFFECT_2 empty, numbers mirror
     the main hand, physical copies store half the flat (D1), Frost Strike OH the full flat.
 13. Guile of Gorefiend: E0 mask exactly GUILE_READ, E2 = a108 misc 15 on GUILE_HB_READ at twice E0, no stale twin.
 14. Rime ranks: EffectAura_2 == 42 -> 59052 (EFFECT_1 stays the trigger), ProcChance 12 / 24 / 35, E0 a DUMMY.
 15. No S2 tooltip ends in a cost or cooldown sentence. 16. SpellDescriptionVariables 1253-1255 declared, names <= 12.
 17. DK ids only in the reserved sub-blocks (spells 203270-203325, talents 60345-60358, SLA 30750-30752, SDV 1253-1255,
     no new rune cost, group, creature).

Run: cd apps/dbc-tools && .venv/bin/python3 -m pytest lib/test_deathknight_s2.py -q -p no:cacheprovider
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import dbcfmt, state  # noqa: E402
from lib.test_deathknight_dk0a import LINK_AURA, RETIRED_TAB, _data, _hex, _u32, m, spell_mask  # noqa: E402
from lib.test_deathknight_s1 import (  # noqa: E402
    SDV_NAME, MAX_SDV_NAME, _all_effect_masks, _effect_mask, _effects, _i, _present,
)

FROST_TAB = 399
SKILL_FROST = 771
CLASS_MASK_DK = 32

# talent id -> (tier, column, rank spell ids). Section 3 of S2-HANDOFF (cells / rank cuts / moves).
GRID: dict[int, tuple[int, int, list[int]]] = {
    2031: (0, 1, [49175, 50031, 51456]), 1968: (0, 2, [49042, 49786, 49787]), 2020: (0, 3, [49455, 50147]),
    2260: (1, 1, [50040, 50041, 50043]), 1973: (1, 2, [49140, 49661, 49662]), 60345: (1, 3, [203270, 203271]),
    2042: (2, 0, [50880, 50884, 50885]), 1989: (2, 1, [49184]), 2048: (2, 2, [51468, 51472, 51473]),
    2044: (3, 0, [51123, 51127, 51128]), 1992: (3, 1, [49188, 56822, 59057]), 1971: (3, 2, [49137, 49657]),
    1981: (3, 3, [49149, 50115]),
    1980: (4, 0, [203308, 203309, 203310]), 60346: (4, 1, [203273]), 60347: (4, 2, [203275, 203276, 203277]),
    2030: (4, 3, [49471, 49790, 49791]),
    60348: (5, 1, [203278, 203279]), 1993: (5, 2, [49024, 49538]),
    2022: (6, 0, [49226, 50137, 50138]), 60349: (6, 1, [203280]), 1999: (6, 2, [203314]),
    60350: (6, 3, [203281, 203282]),
    2284: (7, 0, [65661, 66191, 66192]), 2210: (7, 1, [54639, 54638, 54637]), 60351: (7, 2, [203285, 203286, 203287]),
    60352: (7, 3, [203289, 203290]),
    2040: (8, 0, [50187, 50190, 50191]), 60353: (8, 1, [203292]), 1997: (8, 2, None),  # Acclimation: ranks unchanged
    60354: (8, 3, [203294, 203295]),
    60355: (9, 0, [203297, 203298]), 60356: (9, 1, [203299, 203300, 203301]), 1998: (9, 2, [49202, 50127, 50128]),
    60357: (9, 3, [203302, 203303]),
    60358: (10, 1, [203306]),
}
ACCLIMATION_RANKS = 3
GRID_TALENTS, GRID_POINTS = 36, 85
UNORDERED_RANKS = {2210}  # Blood of the North: the rank order is not pinned by the handoff
PREREQS: dict[int, dict] = {}  # no talent on the tab has a depends_on (2042 and 1993 cleared, 2223 retired)
# castable spell -> SkillLineAbility id
SLA = {203273: 30750, 203280: 30751, 203306: 30752}

S2_NEW = tuple(range(203270, 203326))
S2_NEW_TALENTS = tuple(range(60345, 60359))
KEPT_TALENT_RANKS = tuple(sid for tid, (_, _, ranks) in GRID.items() if tid < 60345 and ranks for sid in ranks)
HELPER_ROWS = (59052, 50434, 50435, 50436, 50882, 58575, 58576, 66188, 66196, 66198, 66216, 55610)
# Mind Freeze 47528, Rune Tap 48982, ERW 47568, Horn 57330 and Frost Fever 55095 get no S2 data edit (brief D5, section 2).
SHARED_EDITS = (49184, 55050, 45462, 45477, 49143, 203054, 203055, 61455, 51714)
S2_EDITED = tuple(dict.fromkeys((*KEPT_TALENT_RANKS, *HELPER_ROWS, *SHARED_EDITS)))
S2_IDS = frozenset(S2_NEW) | frozenset(S2_EDITED)
REQUIRED_IDS = (*S2_NEW, 49184, 55050, 45462, 45477, 49143, 203054, 61455, 51714, 66188, 66196, 66198, 66216,
                *KEPT_TALENT_RANKS)

HOWLING_BLAST, HB_RUNE_COST, FROST_FEVER_ID = 49184, 647, 55095
HB_EFFECT_INDEX = 3  # effect slot (1-based) holding the Frost Fever TRIGGER_SPELL
EFFECT_TRIGGER_SPELL = 64
RUNIC_FOCUS = 61455
RUNIC_FOCUS_S2_D2 = 0x10600
KM_BUFF, KM_RANKS = 203320, {51123: 6, 51127: 12, 51128: 20}
KM_REMOVED_RANKS = (51129, 51130)
MERCILESS_RANKS, TUNDRA_RANKS = (49024, 49538), (49202, 50127, 50128)
GLACIER_ROT_RANKS, ANNIHILATION_RANKS, BOTN_RANKS = (49471, 49790, 49791), (51468, 51472, 51473), (54637, 54638, 54639)
GLACIER_ROT_BAD_ICON, ANNIHILATION_DUMMY_ICON, BOTN_ICON = 196, 2710, 3041
HARDCODED_MISC = 7277
GUILE_RANKS = (50187, 50190, 50191)
RIME_RANKS, RIME_CHANCE, FREEZING_FOG = (49188, 56822, 59057), (12, 24, 35), 59052
AVALANCHE_ID = 203321

# damaging row -> (potency, time basis seconds, SpellLevel); SpellLevel = 9 + 5 * tier + rank (L6)
POTENCY = {
    # S2 TUNE 2026-10-25 (U33): HB 90 -> 62, GA eruption 75 -> 52, Breath tick 60 -> 42, HC tick 15 -> 10, Avalanche 25 -> 17
    HOWLING_BLAST: (62.0, 1.5, 20), 203274: (52.0, 1.5, 30), 203307: (42.0, 1.0, 60), 203316: (10.0, 2.0, 40),
    AVALANCHE_ID: (17.0, 1.5, 27),
}
GLACIAL_ADVANCE, BREATH, BREATH_TICK, HC_TICK, GLACIAL_ERUPTION = 203273, 203306, 203307, 203316, 203274
BREATH_COOLDOWN_MS = 120000
GLACIAL_ADVANCE_POWER = (6, 300)  # PowerType runic power, ManaCost x10

# off-hand copy -> (main-hand spell, copy's flat potency, main's flat potency); D1: physical copies store half
OFFHAND = {
    66198: (203054, 5.0, 10.0), 66188: (49998, 5.0, 10.0), 203322: (55050, 5.0, 10.0),
    66216: (45462, None, None),  # PS: half of PS's own flat (value read from the main-hand entry)
    66196: (49143, 5.0, 5.0),  # Frost Strike OH is always Frost = non-physical: the FULL flat, the helper adds x p
}
FULL_FLAT_COPIES = {66196}

# CAST-phase talents (phase 1); abs(SpellId) of their spell_proc rows
CAST_PHASE = {203278, 203279, 203292, 203281, 203282, 49149, 50115, 203302, 203303}

B9_OWN, B9_READERS = {203273, 203274}, {RUNIC_FOCUS, 51714}
B10_OWN, B10_READERS = {203307}, {RUNIC_FOCUS, 51714}
B16_OWN, B16_READERS = {203321, 203316}, {RUNIC_FOCUS, 51714}
B13_BIT = m.BLOOD_OTHER_MAGIC

PHASE_CAST, PHASE_HIT = 1, 2
PROC_ATTR_REQ_SPELLMOD = 0x8
PROC_DONE_SPELL_CLASS_AND_PERIODIC = 0x10 | 0x100 | 0x400 | 0x1000 | 0x4000 | 0x10000 | 0x40000
PROC_DONE_MELEE_AUTO_ATTACK = 0x4
EFFECT_WEAPON_PERCENT_DAMAGE, EFFECT_NORMALIZED_WEAPON_DMG = 31, 121
AURA_DUMMY, AURA_PERIODIC_DUMMY, AURA_ADD_FLAT, AURA_ADD_PCT, AURA_PROC_TRIGGER_SPELL = 4, 226, 107, 108, 42
SPELLMOD_DAMAGE, SPELLMOD_CRIT_CHANCE, SPELLMOD_CRIT_DAMAGE_BONUS = 0, 7, 15
ATTR0_IS_ABILITY = 0x10
SDV_IDS = (1253, 1254, 1255)
COOLDOWN_SENTENCE = re.compile(r"(\d+(\.\d+)? ?(min|sec|s|m)\w* cooldown\.?|cooldown: ?\d.*)$", re.IGNORECASE)
COST_SENTENCE = re.compile(r"(\bcosts? \d[^.]*\.?|\d+ (runic power|(frost|unholy|blood|death) runes?)\.?)$", re.IGNORECASE)

SPELL_BLOCK = (203270, 203439)
TALENT_BLOCK = (60345, 60364)
SLA_BLOCK = (30750, 30759)
SDV_BLOCK = (1253, 1270)
GROUP_BLOCK = (1273, 1284)
CREATURE_BLOCK = (300300, 300349)
ALLOWED_RUNE_COSTS = {2600, 2601, 2602}
PRE_S2_CREATURES = {300340, 300320, 300321}  # the orc trainer 300340; the S3 Lesser Ghoul and Abomination


def _in(value: int, block: tuple[int, int]) -> bool:
    return block[0] <= value <= block[1]


def _potencies(entry: dict) -> list[dict]:
    """The resolved potency stashes of a DSL entry's damage/heal effects (weapon-percent effects excluded)."""
    out = []
    for slot in ("effect1", "effect2", "effect3"):
        eff = entry.get(slot)
        pot = (eff or {}).get("_potency")
        if pot and pot.get("kind") != "weapon":
            out.append(pot)
    return out


def _flat_potency(entry: dict) -> float | None:
    """The flat (NORMALIZED_WEAPON_DMG) effect's total potency, None if the entry has no such potency effect."""
    for slot in ("effect1", "effect2", "effect3"):
        eff = entry.get(slot) or {}
        if int(eff.get("type") or 0) == EFFECT_NORMALIZED_WEAPON_DMG and eff.get("_potency"):
            return float(eff["_potency"]["total_potency"])
    return None


# ---- checks (pure: take built rows / declared tables, return problem strings) ----------------------------------

def check_required_ids(rows_by_id: dict[int, dict]) -> list[str]:
    return [f"{i}: not declared by any deathknight DSL file" for i in REQUIRED_IDS if i not in rows_by_id]


def check_grid(talents: list[dict]) -> list[str]:
    bad = []
    tab = [t for t in talents if int(t["tab_id"]) == FROST_TAB]
    by_id = {int(t["id"]): t for t in tab}
    if len(tab) != len(by_id):
        bad.append("tab 399: duplicate talent ids")
    if len(by_id) != GRID_TALENTS:
        bad.append(f"tab 399 holds {len(by_id)} talents, expected {GRID_TALENTS}")
    for tid in sorted(set(GRID) - set(by_id)):
        bad.append(f"talent {tid}: not on tab 399")
    for tid in sorted(set(by_id) - set(GRID)):
        bad.append(f"talent {tid}: unexpected on tab 399")
    cells: dict[tuple[int, int], int] = {}
    points = 0
    for tid, (tier, col, ranks) in GRID.items():
        t = by_id.get(tid)
        if t is None:
            continue
        got_cell = (int(t["tier"]), int(t["column"]))
        if got_cell != (tier, col):
            bad.append(f"talent {tid}: cell {got_cell}, expected {(tier, col)}")
        cells[got_cell] = cells.get(got_cell, 0) + 1
        got = [int(r) for r in t.get("rank_spell_ids") or [] if int(r)]
        points += len(got)
        if ranks is None:
            if len(got) != ACCLIMATION_RANKS:
                bad.append(f"talent {tid}: {len(got)} ranks, expected {ACCLIMATION_RANKS}")
        elif (sorted(got) if tid in UNORDERED_RANKS else got) != (sorted(ranks) if tid in UNORDERED_RANKS else ranks):
            bad.append(f"talent {tid}: rank spells {got}, expected {ranks}")
        want_dep = PREREQS.get(tid)
        got_dep = t.get("depends_on")
        got_dep = None if not got_dep else {"talent_id": int(got_dep["talent_id"]), "rank": int(got_dep["rank"])}
        if got_dep != want_dep:
            bad.append(f"talent {tid}: depends_on {got_dep!r}, expected {want_dep!r}")
    for cell, n in cells.items():
        if n > 1:
            bad.append(f"cell {cell}: {n} talents")
    if points != GRID_POINTS:
        bad.append(f"tab 399: {points} points, expected {GRID_POINTS}")
    return bad


def check_skill_lines(slas: list[dict]) -> list[str]:
    bad = []
    for spell, sla_id in SLA.items():
        rows = [s for s in slas if int(s["spell_id"]) == spell]
        if len(rows) != 1:
            bad.append(f"{spell}: {len(rows)} SkillLineAbility rows, expected 1")
            continue
        s = rows[0]
        for label, got, want in (("id", int(s["id"]), sla_id), ("skill_line", int(s["skill_line"]), SKILL_FROST),
                                 ("class_mask", int(s.get("class_mask") or 0), CLASS_MASK_DK),
                                 ("acquire_method", int(s.get("acquire_method") or 0), 0)):
            if got != want:
                bad.append(f"{spell}: SLA {label} {got}, expected {want}")
    return bad


def check_howling_blast(rows_by_id: dict[int, dict], entries: dict[int, dict]) -> list[str]:
    row = rows_by_id.get(HOWLING_BLAST)
    if row is None:
        return []
    bad = []
    n = HB_EFFECT_INDEX
    if _i(row, "RuneCostID") != HB_RUNE_COST:
        bad.append(f"{HOWLING_BLAST}: RuneCostID {row.get('RuneCostID')!r}, expected {HB_RUNE_COST}")
    if _i(row, f"Effect_{n}") != EFFECT_TRIGGER_SPELL:
        bad.append(f"{HOWLING_BLAST}: effect 2 is {row.get(f'Effect_{n}')!r}, expected TRIGGER_SPELL (64)")
    if _i(row, f"EffectTriggerSpell_{n}") != FROST_FEVER_ID:
        bad.append(f"{HOWLING_BLAST}: effect 2 triggers {row.get(f'EffectTriggerSpell_{n}')!r}, expected {FROST_FEVER_ID}")
    # stale twins (L9): the old empty slot's base points / die sides / class-mask C leak into the new effect
    if _i(row, f"EffectBasePoints_{n}"):
        bad.append(f"{HOWLING_BLAST}: stale EffectBasePoints_{n} {row.get(f'EffectBasePoints_{n}')!r} (twin residue)")
    if _i(row, f"EffectDieSides_{n}") not in (0, 1):
        bad.append(f"{HOWLING_BLAST}: stale EffectDieSides_{n} {row.get(f'EffectDieSides_{n}')!r} (twin residue)")
    if any(_u32(row.get(f"EffectSpellClassMaskC_{d}")) for d in (1, 2, 3)):
        bad.append(f"{HOWLING_BLAST}: effect 2 class mask C {_hex(_effect_mask(row, 3))} (twin residue)")
    if _i(row, f"EffectAura_{n}"):
        bad.append(f"{HOWLING_BLAST}: effect 2 has aura {row.get(f'EffectAura_{n}')!r}, expected none")
    if float(row.get(f"EffectBonusMultiplier_{n}") or 0) != 0:
        bad.append(f"{HOWLING_BLAST}: stale EffectBonusMultiplier_{n} {row.get(f'EffectBonusMultiplier_{n}')!r}")
    return bad


def check_potency(rows_by_id: dict[int, dict], entries: dict[int, dict]) -> list[str]:
    bad = []
    for sid, (want_total, want_t, want_level) in POTENCY.items():
        entry = entries.get(sid)
        if entry is None:
            continue
        pots = _potencies(entry)
        if not pots:
            bad.append(f"{sid}: no potency effect declared")
            continue
        if not any(abs(float(p["total_potency"]) - want_total) < 1e-6 for p in pots):
            bad.append(f"{sid}: potency {[p['total_potency'] for p in pots]}, expected {want_total:g}")
        for p in pots:
            if abs(float(p["t_seconds"]) - want_t) > 1e-6:
                bad.append(f"{sid}: time basis {p['t_seconds']}s, expected {want_t:g}s")
        row = rows_by_id.get(sid)
        if row is not None and _i(row, "SpellLevel") != want_level:
            bad.append(f"{sid}: SpellLevel {row.get('SpellLevel')!r}, expected {want_level}")
    return bad


def check_castables(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for sid in (GLACIAL_ADVANCE, BREATH):
        row = rows_by_id.get(sid)
        if row is not None and _u32(row.get("Attributes")) & ATTR0_IS_ABILITY:
            bad.append(f"{sid}: Attributes {_u32(row.get('Attributes')):#x} carries IS_ABILITY 0x10 (must stay magic class)")
    row = rows_by_id.get(GLACIAL_ADVANCE)
    if row is not None and (_i(row, "PowerType"), _i(row, "ManaCost")) != GLACIAL_ADVANCE_POWER:
        bad.append(f"{GLACIAL_ADVANCE}: PowerType/ManaCost {(row.get('PowerType'), row.get('ManaCost'))!r}, "
                   f"expected {GLACIAL_ADVANCE_POWER} (30 Runic Power)")
    row = rows_by_id.get(BREATH)
    if row is not None and _i(row, "RecoveryTime") != BREATH_COOLDOWN_MS:
        bad.append(f"{BREATH}: RecoveryTime {row.get('RecoveryTime')!r}, expected {BREATH_COOLDOWN_MS} (normal 2 min cooldown)")
    return bad


def check_d2_carriers(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for label, bit, own_want, read_want in (("b9", m.GLACIAL_ADVANCE, B9_OWN, B9_READERS),
                                            ("b10", m.BREATH, B10_OWN, B10_READERS),
                                            ("b16", m.FROST_OTHER_MAGIC, B16_OWN, B16_READERS)):
        own = {sid for sid, row in rows_by_id.items() if spell_mask(row)[2] & bit}
        readers = {sid for sid, row in rows_by_id.items() if any(em[2] & bit for em in _all_effect_masks(row))}
        for sid in sorted(own_want - own):
            bad.append(f"{sid}: SpellClassMask lacks d2 {label}")
        for sid in sorted(own - own_want):
            bad.append(f"{sid}: unexpected d2 {label} carrier in SpellClassMask")
        for sid in sorted(read_want - readers):  # readers: at least these two (talent / aura rows may read too)
            if sid in rows_by_id:
                bad.append(f"{sid}: effect mask lacks d2 {label} (reader)")
    return bad


def check_forbidden_bits(rows_by_id: dict[int, dict], stock: dict[int, dict]) -> list[str]:
    """New rows: own + effect masks; edited stock rows: own mask minus the bits the stock row already carried."""
    bad = []
    for sid, row in _present(rows_by_id, *sorted(S2_IDS)):
        base = stock.get(sid)
        exempt = spell_mask(base) if base is not None and sid not in S2_NEW else (0, 0, 0)
        masks = [("SpellClassMask", spell_mask(row), exempt)]
        if sid in S2_NEW:
            masks += [(f"EffectSpellClassMask{'ABC'[n]}", em, (0, 0, 0)) for n, em in enumerate(_all_effect_masks(row))]
        for label, mask, ex in masks:
            hit = (mask[0] & m.FORBIDDEN_D0 & ~ex[0], mask[1] & m.FORBIDDEN_D1 & ~ex[1], mask[2] & m.FORBIDDEN_D2 & ~ex[2])
            if any(hit):
                bad.append(f"{sid}: {label} {_hex(mask)} holds forbidden bits {_hex(hit)}")
    return bad


def check_no_d2_b13(rows_by_id: dict[int, dict]) -> list[str]:
    """Blood Shadow's d2 b13 never lands on a Frost row; Runic Focus (S1's reader) is the one effect-mask exception."""
    bad = []
    for sid, row in _present(rows_by_id, *sorted(S2_IDS)):
        if spell_mask(row)[2] & B13_BIT and sid != 203144 and sid != 203149:
            bad.append(f"{sid}: SpellClassMask holds d2 b13 (Blood Shadow)")
        if sid in S2_NEW and any(em[2] & B13_BIT for em in _all_effect_masks(row)):
            bad.append(f"{sid}: an effect mask reads d2 b13 (Blood Shadow)")
    return bad


def check_runic_focus(rows_by_id: dict[int, dict]) -> list[str]:
    row = rows_by_id.get(RUNIC_FOCUS)
    if row is None:
        return []
    got = _effect_mask(row)[2]
    if got & RUNIC_FOCUS_S2_D2 != RUNIC_FOCUS_S2_D2:
        return [f"{RUNIC_FOCUS}: effect mask d2 {got:#x} lacks {RUNIC_FOCUS_S2_D2 & ~got:#x} (Glacial Advance / Breath / "
                f"other-magic bits)"]
    return []


def check_killing_machine(rows_by_id: dict[int, dict], entries: dict[int, dict], procs: list[dict],
                          proc_removals: list[dict], script_removals: list[dict], scripts: list[dict]) -> list[str]:
    bad = []
    row = rows_by_id.get(KM_BUFF)
    if row is not None:
        if _i(row, "CumulativeAura") != 2:
            bad.append(f"{KM_BUFF}: CumulativeAura {row.get('CumulativeAura')!r}, expected 2")
        if _i(row, "ProcCharges"):
            bad.append(f"{KM_BUFF}: ProcCharges {row.get('ProcCharges')!r}, expected none")
        eff = next(iter(_effects(row)), None)
        if eff is None or eff["aura"] != AURA_ADD_FLAT or eff["misc"] != SPELLMOD_CRIT_CHANCE:
            bad.append(f"{KM_BUFF}: effect 0 {eff!r}, expected ADD_FLAT_MODIFIER (107) misc 7 (crit chance)")
        if _effect_mask(row, 1) != tuple(m.KILLING_MACHINE_READ):
            bad.append(f"{KM_BUFF}: effect 0 mask {_hex(_effect_mask(row, 1))}, expected {_hex(m.KILLING_MACHINE_READ)}")
    entry = entries.get(KM_BUFF)
    if entry is not None and entry.get("duration_ms") != 30000:
        bad.append(f"{KM_BUFF}: duration_ms {entry.get('duration_ms')!r}, expected 30000")
    for p in procs:
        if abs(int(p["SpellId"])) == KM_BUFF:
            bad.append(f"{KM_BUFF}: spell_proc row declared (the buff must not proc)")
    for sid, chance in KM_RANKS.items():
        rows = [p for p in procs if int(p["SpellId"]) == sid]
        if len(rows) != 1:
            bad.append(f"{sid}: {len(rows)} positive spell_proc rows, expected 1")
            continue
        p = rows[0]
        if float(p.get("ProcsPerMinute") or 0) != 0:
            bad.append(f"{sid}: spell_proc ProcsPerMinute {p.get('ProcsPerMinute')!r}, expected 0 (Proc Chance only)")
        if float(p.get("Chance") or 0) != chance:
            bad.append(f"{sid}: spell_proc Chance {p.get('Chance')!r}, expected {chance}")
        if not int(p.get("ProcFlags") or 0) & PROC_DONE_MELEE_AUTO_ATTACK:
            bad.append(f"{sid}: spell_proc ProcFlags {int(p.get('ProcFlags') or 0):#x} lacks DONE_MELEE_AUTO_ATTACK 0x4")
    if any(int(p["SpellId"]) == -51123 for p in procs):
        bad.append("-51123: a negative spell_proc row shadows the positive per-rank rows")
    removed = {int(r["SpellId"]) for r in proc_removals}
    for sid in KM_REMOVED_RANKS:
        if sid not in removed:
            bad.append(f"{sid}: no remove_spell_proc (dropped rank would keep its PPM row)")
    if not any(int(r["spell_id"]) == -51123 and r["ScriptName"] == "spell_gen_no_offhand_proc" for r in script_removals):
        bad.append("-51123: no unbind_script(spell_gen_no_offhand_proc) (it blocks off-hand procs)")
    if not any(int(s.get("spell_id", 0)) == -51123 and s["ScriptName"] == "spell_dk_killing_machine_talent"
               for s in scripts):
        bad.append("-51123: no scripted_by(spell_dk_killing_machine_talent)")
    return bad


def check_neutralised_hardcodes(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for sid, row in _present(rows_by_id, *MERCILESS_RANKS, *TUNDRA_RANKS):
        if any(e["misc"] == HARDCODED_MISC for e in _effects(row)):
            bad.append(f"{sid}: an effect still has misc {HARDCODED_MISC} (stock hardcode)")
        if _i(row, "TargetAuraState"):
            bad.append(f"{sid}: TargetAuraState {row.get('TargetAuraState')!r}, expected 0")
    for sid, row in _present(rows_by_id, *GLACIER_ROT_RANKS):
        if _i(row, "SpellIconID") == GLACIER_ROT_BAD_ICON:
            bad.append(f"{sid}: SpellIconID {GLACIER_ROT_BAD_ICON} (stock Glacier Rot hardcode)")
    for sid, row in _present(rows_by_id, *ANNIHILATION_RANKS):
        if _i(row, "SpellIconID") == ANNIHILATION_DUMMY_ICON and any(e["aura"] == AURA_DUMMY for e in _effects(row)):
            bad.append(f"{sid}: still an icon-{ANNIHILATION_DUMMY_ICON} DUMMY effect (stock hardcode)")
    for sid, row in _present(rows_by_id, *BOTN_RANKS):
        if any(e["aura"] == AURA_PERIODIC_DUMMY for e in _effects(row)):
            bad.append(f"{sid}: still has a PERIODIC_DUMMY effect (icon {BOTN_ICON} hardcode)")
        eff = next(iter(_effects(row)), None)
        if eff is None or eff["aura"] != AURA_ADD_PCT and eff["aura"] != AURA_ADD_FLAT or eff["misc"] != SPELLMOD_DAMAGE:
            bad.append(f"{sid}: effect 0 {eff!r}, expected a SPELLMOD_DAMAGE modifier")
    return bad


def check_botn_removals(rows_by_id: dict[int, dict], proc_removals: list[dict], script_removals: list[dict]) -> list[str]:
    bad = []
    if not any(int(r["SpellId"]) == -54639 for r in proc_removals):
        bad.append("-54639: no remove_spell_proc")
    if not any(int(r["spell_id"]) == -54639 and r["ScriptName"] == "spell_dk_death_rune" for r in script_removals):
        bad.append("-54639: no unbind_script(spell_dk_death_rune)")
    for sid, row in _present(rows_by_id, *BOTN_RANKS):
        if _i(row, "ProcTypeMask"):
            bad.append(f"{sid}: ProcTypeMask {_u32(row.get('ProcTypeMask')):#x}, expected 0 (else a default spell_proc row)")
    return bad


def check_proc_phases(procs: list[dict]) -> list[str]:
    bad = []
    for p in procs:
        sid = abs(int(p["SpellId"]))
        if sid not in S2_IDS:
            continue
        phase = int(p["SpellPhaseMask"])
        if sid in CAST_PHASE:
            if phase != PHASE_CAST:
                bad.append(f"{p['SpellId']}: CAST-phase talent row has SpellPhaseMask {p['SpellPhaseMask']!r}, expected 1")
        elif int(p["ProcFlags"]) & PROC_DONE_SPELL_CLASS_AND_PERIODIC \
                and not int(p.get("AttributesMask") or 0) & PROC_ATTR_REQ_SPELLMOD and phase != PHASE_HIT:
            bad.append(f"{p['SpellId']}: DONE spell-class / periodic proc row has SpellPhaseMask "
                       f"{p['SpellPhaseMask']!r}, expected 2")
    return bad


def check_offhand_copies(rows_by_id: dict[int, dict], entries: dict[int, dict]) -> list[str]:
    bad = []
    for sid, (main, want_flat, main_flat) in OFFHAND.items():
        row = rows_by_id.get(sid)
        if row is None:
            continue
        if _i(row, "Effect_1") != EFFECT_WEAPON_PERCENT_DAMAGE:
            bad.append(f"{sid}: effect 0 is {row.get('Effect_1')!r}, expected WEAPON_PERCENT_DAMAGE (31) first")
        if _i(row, "Effect_2") != EFFECT_NORMALIZED_WEAPON_DMG:
            bad.append(f"{sid}: effect 1 is {row.get('Effect_2')!r}, expected NORMALIZED_WEAPON_DMG (121) second")
        if _i(row, "Effect_3") or _i(row, "EffectAura_3"):
            bad.append(f"{sid}: effect 2 is {row.get('Effect_3')!r}/{row.get('EffectAura_3')!r}, expected empty "
                       f"(no per-disease DUMMY)")
        main_row = rows_by_id.get(main)
        if main_row is not None:
            # like with like: the main hand's WEAPON_PERCENT_DAMAGE effect (Plague Strike lists its flat first)
            main_pct = next((_i(main_row, f"EffectBasePoints_{n}") for n in (1, 2, 3)
                             if _i(main_row, f"Effect_{n}") == EFFECT_WEAPON_PERCENT_DAMAGE), None)
            if main_pct is not None and _i(row, "EffectBasePoints_1") != main_pct:
                bad.append(f"{sid}: weapon percent bp {row.get('EffectBasePoints_1')!r}, main hand {main} has "
                           f"{main_pct!r}")
        flat = _flat_potency(entries[sid]) if sid in entries else None
        main_got = _flat_potency(entries[main]) if main in entries else None
        want, want_main = want_flat, main_flat
        if want is None and main_got is not None:  # PS: half of the main hand's own flat
            want, want_main = main_got / 2, main_got
        if flat is not None and want is not None and abs(flat - want) > 1e-6:
            bad.append(f"{sid}: flat potency {flat:g}, expected {want:g}"
                       + (" (the FULL flat, always Frost)" if sid in FULL_FLAT_COPIES else " (half the main-hand flat, D1)"))
        if main_got is not None and want_main is not None and abs(main_got - want_main) > 1e-6:
            bad.append(f"{main}: main-hand flat potency {main_got:g}, expected {want_main:g}")
    return bad


def check_guile(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for sid, row in _present(rows_by_id, *GUILE_RANKS):
        effs = {e["n"]: e for e in _effects(row)}
        e0, e2 = effs.get(1), effs.get(3)
        if e0 is None or e2 is None:
            bad.append(f"{sid}: effects 0 / 2 missing (E0 {e0 is not None}, E2 {e2 is not None})")
            continue
        if _effect_mask(row, 1) != tuple(m.GUILE_READ):
            bad.append(f"{sid}: effect 0 mask {_hex(_effect_mask(row, 1))}, expected GUILE_READ {_hex(m.GUILE_READ)}")
        if _effect_mask(row, 3) != tuple(m.GUILE_HB_READ):
            bad.append(f"{sid}: effect 2 mask {_hex(_effect_mask(row, 3))}, expected GUILE_HB_READ "
                       f"{_hex(m.GUILE_HB_READ)}")
        if (e2["aura"], e2["misc"]) != (AURA_ADD_PCT, SPELLMOD_CRIT_DAMAGE_BONUS):
            bad.append(f"{sid}: effect 2 is aura {e2['aura']} misc {e2['misc']}, expected 108 / 15")
        if (e0["aura"], e0["misc"]) != (AURA_ADD_PCT, SPELLMOD_CRIT_DAMAGE_BONUS):
            bad.append(f"{sid}: effect 0 is aura {e0['aura']} misc {e0['misc']}, expected 108 / 15")
        if e2["bp"] + 1 != 2 * (e0["bp"] + 1):
            bad.append(f"{sid}: effect 2 value {e2['bp'] + 1}, expected twice effect 0's {e0['bp'] + 1}")
        if float(row.get("EffectBonusMultiplier_3") or 0) != 0:
            bad.append(f"{sid}: stale EffectBonusMultiplier_3 {row.get('EffectBonusMultiplier_3')!r}")
    return bad


def check_rime(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for sid, chance in zip(RIME_RANKS, RIME_CHANCE):
        row = rows_by_id.get(sid)
        if row is None:
            continue
        if _i(row, "EffectAura_2") != AURA_PROC_TRIGGER_SPELL:
            bad.append(f"{sid}: EffectAura_2 {row.get('EffectAura_2')!r}, expected 42 (spell_dk_rime registers on EFFECT_1)")
        if _i(row, "EffectTriggerSpell_2") != FREEZING_FOG:
            bad.append(f"{sid}: EffectTriggerSpell_2 {row.get('EffectTriggerSpell_2')!r}, expected {FREEZING_FOG}")
        if _i(row, "ProcChance") != chance:
            bad.append(f"{sid}: ProcChance {row.get('ProcChance')!r}, expected {chance}")
        if _i(row, "EffectAura_1") != AURA_DUMMY:
            bad.append(f"{sid}: EffectAura_1 {row.get('EffectAura_1')!r}, expected 4 (DUMMY flag carrier)")
    return bad


ICY_TALONS_RANKS = (50880, 50884, 50885)


def check_icy_talons_proc(rows_by_id: dict[int, dict]) -> list[str]:
    # Frost Fever is magic-class (DefenseType 1): its hit only carries DONE_SPELL_MAGIC_DMG_CLASS_NEG 0x10000
    bad = []
    for sid, row in _present(rows_by_id, *ICY_TALONS_RANKS):
        if not _u32(row.get("ProcTypeMask")) & 0x10000:
            bad.append(f"{sid}: ProcTypeMask {_u32(row.get('ProcTypeMask')):#x} lacks 0x10000 (never procs off Frost Fever)")
    return bad


# 18. Icy Talons capstone (user ruling 2026-10-25): Improved Icy Talons 2223 is retired, its party/raid melee haste 55610 is
# a hidden passive linked (type 2) to Icy Talons rank 3 (50885), the self +5% (aura 193) is gone, and the three buffs are
# 3 / 6 / 10% (stored 2 / 5 / 9).
IIT_TALENT, IIT_PASSIVE, ICY_TALONS_R3 = 2223, 55610, 50885
ICY_TALONS_BUFF_BP = {50880: (50882, 2), 50884: (58575, 5), 50885: (58576, 9)}  # rank -> (buff, stored base points)
EFFECT_APPLY_AREA_AURA_RAID, AURA_MOD_MELEE_HASTE, AURA_HASTE_ALL = 65, 138, 193
ATTR0_PASSIVE = 0x40
CAPSTONE_GREY = "|cFF9D9D9DCapstone: "


def check_icy_talons_capstone(rows_by_id: dict[int, dict], talents: list[dict], links: list[dict]) -> list[str]:
    bad = []
    # the talent is gone from every tree and no live talent names the passive as a rank
    for t in talents:
        if int(t["id"]) == IIT_TALENT and int(t["tab_id"]) != RETIRED_TAB:
            bad.append(f"talent {IIT_TALENT}: tab {t['tab_id']}, expected the holding tab {RETIRED_TAB} (retired)")
        if int(t["tab_id"]) != RETIRED_TAB and IIT_PASSIVE in [int(r) for r in t.get("rank_spell_ids") or []]:
            bad.append(f"talent {t['id']}: still lists {IIT_PASSIVE} as a rank")
        if int(t["tab_id"]) == FROST_TAB and (int(t["tier"]), int(t["column"])) == (5, 0):
            bad.append(f"talent {t['id']}: occupies the emptied cell (5, 0)")
    # the hidden passive: the party/raid area aura only, nothing else reads the removed self effect
    row = rows_by_id.get(IIT_PASSIVE)
    if row is not None:
        effects = _effects(row)
        if len(effects) != 1:
            bad.append(f"{IIT_PASSIVE}: {len(effects)} effects, expected only the party aura")
        for eff in effects:
            if eff["aura"] == AURA_HASTE_ALL:
                bad.append(f"{IIT_PASSIVE}: effect {eff['n']} is still the self HASTE_ALL aura 193")
        first = effects[0] if effects else {}
        if (first.get("type"), first.get("aura"), first.get("bp")) != (EFFECT_APPLY_AREA_AURA_RAID, AURA_MOD_MELEE_HASTE, 9):
            bad.append(f"{IIT_PASSIVE}: effect 1 is {first!r}, expected area-aura-raid 65 / aura 138 / stored 9 (+10%)")
        if not _i(row, "EffectRadiusIndex_1"):
            bad.append(f"{IIT_PASSIVE}: effect 1 has no radius")
        if not _u32(row.get("Attributes")) & ATTR0_PASSIVE:
            bad.append(f"{IIT_PASSIVE}: not passive (a talent-less aura must be hidden)")
    # linked to rank 3 only, applied and removed with the aura
    have = [(int(link["spell_trigger"]), int(link["type"])) for link in links if int(link["spell_effect"]) == IIT_PASSIVE]
    if have != [(ICY_TALONS_R3, LINK_AURA)]:
        bad.append(f"{IIT_PASSIVE}: spell_linked_spell rows {have}, expected exactly [({ICY_TALONS_R3}, {LINK_AURA})]")
    # the buffs and the rank tooltips
    for rank, (buff, stored) in ICY_TALONS_BUFF_BP.items():
        brow = rows_by_id.get(buff)
        if brow is not None and (_i(brow, "EffectBasePoints_1"), _i(brow, "EffectAura_1")) != (stored, AURA_MOD_MELEE_HASTE):
            bad.append(f"{buff}: bp/aura {brow.get('EffectBasePoints_1')!r}/{brow.get('EffectAura_1')!r}, "
                       f"expected {stored}/{AURA_MOD_MELEE_HASTE}")
        rrow = rows_by_id.get(rank)
        if rrow is None:
            continue
        if _i(rrow, "EffectBasePoints_1") != stored or _i(rrow, "EffectBasePoints_2") != stored:
            bad.append(f"{rank}: eff0 / eff1 base points {rrow.get('EffectBasePoints_1')!r} / "
                       f"{rrow.get('EffectBasePoints_2')!r}, expected {stored} (buff {buff})")
        text = str(rrow.get("Description_Lang_enUS") or "")
        if text.count("Capstone:") != 1 or f"${IIT_PASSIVE}s1" not in text or f"${IIT_PASSIVE}a1" not in text:
            bad.append(f"{rank}: tooltip needs one 'Capstone:' paragraph quoting ${IIT_PASSIVE}a1 / s1")
        elif rank == ICY_TALONS_R3 and (CAPSTONE_GREY in text or not text.endswith(".")):
            bad.append(f"{rank}: the last rank's capstone must be plain (not grey) and end the tooltip")
        elif rank != ICY_TALONS_R3 and not (CAPSTONE_GREY in text and text.endswith("|r")):
            bad.append(f"{rank}: a lower rank's capstone must be grey (|cFF9D9D9D ... |r)")
    return bad


def check_no_cost_cooldown_tooltips(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    # hidden energize helpers: no client tooltip ever shows their description
    hidden_helpers = {203272, 203296, 203304}
    for sid, row in _present(rows_by_id, *sorted(S2_IDS - hidden_helpers)):
        for col in ("Description_Lang_enUS", "AuraDescription_Lang_enUS"):
            text = str(row.get(col) or "").strip()
            if COOLDOWN_SENTENCE.search(text):
                bad.append(f"{sid}: {col} ends in a cooldown sentence")
            elif COST_SENTENCE.search(text):
                bad.append(f"{sid}: {col} ends in a cost sentence")
    return bad


def check_sdv(entries: list[dict]) -> list[str]:
    bad = []
    by_id = {int(e["id"]): e for e in entries}
    for sid in SDV_IDS:
        if sid not in by_id:
            bad.append(f"SpellDescriptionVariables {sid}: not declared")
    for sid in SDV_IDS:
        for name in SDV_NAME.findall(str(by_id.get(sid, {}).get("Variables") or "")):
            if len(name) > MAX_SDV_NAME:
                bad.append(f"SpellDescriptionVariables {sid}: name {name!r} is {len(name)} chars, max {MAX_SDV_NAME}")
    return bad


def check_id_blocks(spell_ids: set[int], talents: list[dict], slas: list[dict], sdv: list[dict],
                    rune_costs: list[dict], groups: list[dict], creatures: list[dict]) -> list[str]:
    bad = []
    for sid in sorted(spell_ids):
        if _in(sid, SPELL_BLOCK) and sid not in S2_NEW:
            bad.append(f"spell {sid}: inside the Frost block {SPELL_BLOCK} but outside 203270-203325 (spare block)")
    for t in talents:
        tid = int(t["id"])
        if _in(tid, TALENT_BLOCK) and tid not in S2_NEW_TALENTS:
            bad.append(f"talent {tid}: inside the Frost block {TALENT_BLOCK} but outside 60345-60358")
    for s in slas:
        sid = int(s["id"])
        if _in(sid, SLA_BLOCK) and sid not in SLA.values():
            bad.append(f"SkillLineAbility {sid}: inside {SLA_BLOCK} but outside 30750-30752")
    for e in sdv:
        eid = int(e["id"])
        if _in(eid, SDV_BLOCK) and eid not in SDV_IDS:
            bad.append(f"SpellDescriptionVariables {eid}: inside {SDV_BLOCK} but outside 1253-1255")
    for c in rune_costs:
        if int(c["ID"]) not in ALLOWED_RUNE_COSTS:
            bad.append(f"SpellRuneCost {c['ID']}: S2 adds none (2602 is earmarked for S3)")
    for g in groups:
        gid = int(g["id"])
        if _in(gid, GROUP_BLOCK):
            bad.append(f"spell_group {gid}: S2 adds none (55610 joins the existing group 1022)")
    for cr in creatures:
        cid = int(cr.get("entry") or cr.get("id") or 0)
        if _in(cid, CREATURE_BLOCK) and cid not in PRE_S2_CREATURES:
            bad.append(f"creature {cid}: S2 adds none")
    return bad


# ---- real data ------------------------------------------------------------------------------------------------

class DeathKnightS2DataTest(unittest.TestCase):
    def assertClean(self, problems: list[str]):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def _rows(self):
        return _data()["rows_by_id"]

    def _pkg(self):
        return _data()["package"]

    def _entries(self):
        return {int(e["id"]): e for e in self._pkg().spells}

    def test_required_ids_declared(self):
        self.assertClean(check_required_ids(self._rows()))

    def test_grid(self):
        self.assertClean(check_grid(self._pkg().talents))

    def test_castable_skill_lines(self):
        self.assertClean(check_skill_lines(self._pkg().skill_line_abilities))

    def test_howling_blast(self):
        self.assertClean(check_howling_blast(self._rows(), self._entries()))

    def test_potency_rows(self):
        self.assertClean(check_potency(self._rows(), self._entries()))

    def test_castables(self):
        self.assertClean(check_castables(self._rows()))

    def test_d2_carriers(self):
        self.assertClean(check_d2_carriers(self._rows()))

    def test_no_forbidden_bits(self):
        self.assertClean(check_forbidden_bits(self._rows(), state.load_stock_rows(dbcfmt.SPELL)))

    def test_no_d2_b13(self):
        self.assertClean(check_no_d2_b13(self._rows()))

    def test_runic_focus(self):
        self.assertClean(check_runic_focus(self._rows()))

    def test_killing_machine(self):
        pkg = self._pkg()
        self.assertClean(check_killing_machine(self._rows(), self._entries(), pkg.spell_procs, pkg.proc_removals,
                                               pkg.script_removals, pkg.spell_script_names))

    def test_neutralised_hardcodes(self):
        self.assertClean(check_neutralised_hardcodes(self._rows()))

    def test_blood_of_the_north_removals(self):
        pkg = self._pkg()
        self.assertClean(check_botn_removals(self._rows(), pkg.proc_removals, pkg.script_removals))

    def test_proc_phases(self):
        self.assertClean(check_proc_phases(self._pkg().spell_procs))

    def test_offhand_copies(self):
        self.assertClean(check_offhand_copies(self._rows(), self._entries()))

    def test_guile(self):
        self.assertClean(check_guile(self._rows()))

    def test_rime(self):
        self.assertClean(check_rime(self._rows()))

    def test_icy_talons_proc(self):
        self.assertClean(check_icy_talons_proc(self._rows()))

    def test_icy_talons_capstone(self):
        pkg = self._pkg()
        self.assertClean(check_icy_talons_capstone(self._rows(), pkg.talents, pkg.linked_spells))

    def test_no_cost_or_cooldown_tooltips(self):
        self.assertClean(check_no_cost_cooldown_tooltips(self._rows()))

    def test_sdv_names(self):
        self.assertClean(check_sdv(self._pkg().tooltip_vars))

    def test_id_blocks(self):
        pkg = self._pkg()
        self.assertClean(check_id_blocks(set(self._entries()), pkg.talents, pkg.skill_line_abilities, pkg.tooltip_vars,
                                         pkg.spell_rune_costs, pkg.spell_groups, pkg.creature_templates))


# ---- negative fixtures: every check must fire on a minimal bad input --------------------------------------------

def _row(spell_id=1, **cols) -> dict:
    return {"ID": spell_id, **cols}


def _proc(sid, flags=0x10, phase=PHASE_HIT, **cols) -> dict:
    return {"SpellId": sid, "ProcFlags": flags, "SpellPhaseMask": phase, "SpellFamilyMask0": 0, "SpellFamilyMask1": 0,
            "SpellFamilyMask2": 0, "Cooldown": 0, "Charges": 0, "ProcsPerMinute": 0, "Chance": 0, **cols}


def _good_grid() -> list[dict]:
    out = []
    for tid, (tier, col, ranks) in GRID.items():
        spells = ranks if ranks is not None else [tid * 10 + i for i in range(ACCLIMATION_RANKS)]
        out.append({"id": tid, "tab_id": FROST_TAB, "tier": tier, "column": col, "rank_spell_ids": list(spells),
                    "depends_on": dict(PREREQS[tid]) if tid in PREREQS else None})
    return out


def _entry(sid, pots, **cols) -> dict:
    """A DSL entry with one damage effect per potency tuple (total, t_seconds, level)."""
    entry = {"id": sid, **cols}
    for i, (total, t, level) in enumerate(pots, start=1):
        entry[f"effect{i}"] = {"type": 2, "_potency": {"total_potency": total, "t_seconds": t, "spell_level": level,
                                                       "kind": "direct"}}
    return entry


class DeathKnightS2NegativeTest(unittest.TestCase):
    def test_sanity_of_constants(self):
        self.assertEqual(len(GRID), GRID_TALENTS)
        self.assertEqual(sum(len(r) if r is not None else ACCLIMATION_RANKS for _, _, r in GRID.values()), GRID_POINTS)
        self.assertEqual(len({(t, c) for t, c, _ in GRID.values()}), GRID_TALENTS)

    def test_required_ids(self):
        self.assertEqual(check_required_ids({i: {} for i in REQUIRED_IDS}), [])
        self.assertEqual(len(check_required_ids({i: {} for i in REQUIRED_IDS if i != 203306})), 1)

    def test_grid(self):
        good = _good_grid()
        self.assertEqual(check_grid(good), [])
        moved = [dict(t) for t in good]
        moved[0]["tier"] = 9
        self.assertGreaterEqual(len(check_grid(moved)), 1)
        self.assertGreaterEqual(len(check_grid(good[1:])), 3)  # count, absent talent, points
        idx = {t["id"]: i for i, t in enumerate(good)}
        dep = [dict(t) for t in good]
        dep[idx[2042]]["depends_on"] = {"talent_id": 2031, "rank": 2}  # the stock prereq that must be cleared
        self.assertEqual(len(check_grid(dep)), 1)
        back = [dict(t) for t in good] + [{"id": 2223, "tab_id": FROST_TAB, "tier": 5, "column": 0,
                                           "rank_spell_ids": [55610], "depends_on": {"talent_id": 2042, "rank": 2}}]
        self.assertEqual(len(check_grid(back)), 2)  # the talent count and the unexpected talent (2223 is retired)
        stock_rank = [dict(t) for t in good]
        stock_rank[idx[2042]]["depends_on"] = {"talent_id": 2031, "rank": 4}  # any prerequisite on the tab is wrong now
        self.assertEqual(len(check_grid(stock_rank)), 1)
        dangling = [dict(t) for t in good]
        dangling[idx[1993]]["depends_on"] = {"talent_id": 1994, "rank": 0}
        self.assertEqual(len(check_grid(dangling)), 1)
        five = [dict(t) for t in good]
        five[idx[1968]]["rank_spell_ids"] = [49042, 49786, 49787, 49788, 49789]  # the 5 -> 3 cut not applied
        self.assertGreaterEqual(len(check_grid(five)), 2)  # rank list + points
        old_dc = [dict(t) for t in good]
        old_dc[idx[1980]]["rank_spell_ids"] = [49796]
        self.assertGreaterEqual(len(check_grid(old_dc)), 2)
        unordered = [dict(t) for t in good]
        unordered[idx[2210]]["rank_spell_ids"] = [54637, 54638, 54639]
        self.assertEqual(check_grid(unordered), [])
        wrong_tab = [dict(t) for t in good]
        wrong_tab[0]["tab_id"] = 398
        self.assertGreaterEqual(len(check_grid(wrong_tab)), 2)
        extra = good + [{"id": 9999, "tab_id": FROST_TAB, "tier": 10, "column": 3, "rank_spell_ids": [1],
                         "depends_on": None}]
        self.assertGreaterEqual(len(check_grid(extra)), 1)

    def test_skill_lines(self):
        good = [{"id": i, "skill_line": 771, "spell_id": s, "class_mask": 32, "acquire_method": 0}
                for s, i in SLA.items()]
        self.assertEqual(check_skill_lines(good), [])
        for col, value in (("skill_line", 770), ("class_mask", 1), ("acquire_method", 1), ("id", 1)):
            bad = [dict(good[0], **{col: value}), *good[1:]]
            self.assertEqual(len(check_skill_lines(bad)), 1, col)
        self.assertEqual(len(check_skill_lines(good[1:])), 1)

    def test_howling_blast(self):
        def hb(**cols):
            row = _row(HOWLING_BLAST, RuneCostID=647, Effect_3=64, EffectTriggerSpell_3=55095, EffectBasePoints_3=0,
                       EffectDieSides_3=1)
            row.update(cols)
            return {HOWLING_BLAST: row}

        self.assertEqual(check_howling_blast(hb(), {}), [])
        for cols in ({"RuneCostID": 1}, {"Effect_3": 3}, {"EffectTriggerSpell_3": 0}, {"EffectBasePoints_3": 49},
                     {"EffectDieSides_3": 5}, {"EffectSpellClassMaskC_1": 0x2}, {"EffectAura_3": 4},
                     {"EffectBonusMultiplier_3": 0.4}):
            self.assertGreaterEqual(len(check_howling_blast(hb(**cols), {})), 1, cols)
        self.assertEqual(check_howling_blast({}, {}), [])

    def test_potency(self):
        entries = {sid: _entry(sid, [(p, t, lvl)]) for sid, (p, t, lvl) in POTENCY.items()}
        rows = {sid: _row(sid, SpellLevel=lvl) for sid, (_, _, lvl) in POTENCY.items()}
        self.assertEqual(check_potency(rows, entries), [])
        # wrong potency / time basis (the 1500 default on a 1 s or 2 s tick) / missing SpellLevel
        self.assertEqual(len(check_potency(rows, {**entries, 203307: _entry(203307, [(42.0, 1.5, 60)])})), 1)
        self.assertEqual(len(check_potency(rows, {**entries, 203316: _entry(203316, [(10.0, 1.5, 40)])})), 1)
        self.assertEqual(len(check_potency(rows, {**entries, 49184: _entry(49184, [(100.9, 1.5, 20)])})), 1)
        self.assertEqual(len(check_potency({**rows, 203274: _row(203274, SpellLevel=0)}, entries)), 1)
        self.assertEqual(len(check_potency(rows, {**entries, 203321: {"id": 203321}})), 1)  # no potency at all
        self.assertEqual(check_potency({}, {}), [])

    def test_castables(self):
        rows = {GLACIAL_ADVANCE: _row(GLACIAL_ADVANCE, Attributes=0, PowerType=6, ManaCost=300),
                BREATH: _row(BREATH, Attributes=0, RecoveryTime=120000)}
        self.assertEqual(check_castables(rows), [])
        self.assertEqual(len(check_castables({**rows, BREATH: _row(BREATH, Attributes=0x10, RecoveryTime=120000)})), 1)
        self.assertEqual(len(check_castables({**rows, GLACIAL_ADVANCE: _row(GLACIAL_ADVANCE, Attributes=0x10,
                                                                           PowerType=6, ManaCost=300)})), 1)
        self.assertEqual(len(check_castables({**rows, GLACIAL_ADVANCE: _row(GLACIAL_ADVANCE, PowerType=0,
                                                                           ManaCost=300)})), 1)
        self.assertEqual(len(check_castables({**rows, BREATH: _row(BREATH, RecoveryTime=0)})), 1)

    def test_d2_carriers(self):
        rows = {sid: _row(sid, SpellClassMask_3=m.GLACIAL_ADVANCE) for sid in B9_OWN}
        rows.update({sid: _row(sid, SpellClassMask_3=m.BREATH) for sid in B10_OWN})
        rows.update({sid: _row(sid, SpellClassMask_3=m.FROST_OTHER_MAGIC) for sid in B16_OWN})
        rows[RUNIC_FOCUS] = _row(RUNIC_FOCUS, EffectSpellClassMaskA_3=RUNIC_FOCUS_S2_D2)
        rows[51714] = _row(51714, EffectSpellClassMaskA_3=RUNIC_FOCUS_S2_D2)
        self.assertEqual(check_d2_carriers(rows), [])
        self.assertEqual(len(check_d2_carriers({k: v for k, v in rows.items() if k != 203274})), 1)  # eruption lost b9
        self.assertEqual(len(check_d2_carriers({k: v for k, v in rows.items() if k != 203307})), 1)  # tick lost b10
        self.assertEqual(len(check_d2_carriers({k: v for k, v in rows.items() if k != 203321})), 1)  # Avalanche b16
        for bit in (m.GLACIAL_ADVANCE, m.BREATH, m.FROST_OTHER_MAGIC):
            self.assertEqual(len(check_d2_carriers({**rows, 777: _row(777, SpellClassMask_3=bit)})), 1, bit)
            self.assertEqual(check_d2_carriers({**rows, 778: _row(778, EffectSpellClassMaskB_3=bit)}), [])  # extra reader ok
        self.assertEqual(len(check_d2_carriers({**rows, RUNIC_FOCUS: _row(RUNIC_FOCUS, EffectSpellClassMaskA_3=0x200)})), 2)
        self.assertEqual(len(check_d2_carriers({**rows, 51714: _row(51714)})), 3)  # Razorice reads none of the bits

    def test_forbidden_bits(self):
        stock: dict[int, dict] = {}
        for col, bit in (("SpellClassMask_1", m.FORBIDDEN_D0_B6), ("SpellClassMask_1", m.FORBIDDEN_D0_B17),
                         ("SpellClassMask_1", m.FORBIDDEN_D0_B22), ("SpellClassMask_2", m.FORBIDDEN_D1_B10),
                         ("SpellClassMask_2", m.FORBIDDEN_D1_B11), ("SpellClassMask_2", m.FORBIDDEN_D1_B23),
                         ("SpellClassMask_2", m.FORBIDDEN_D1_B24), ("SpellClassMask_3", m.FORBIDDEN_D2_B1),
                         ("SpellClassMask_3", m.FORBIDDEN_D2_B31)):
            self.assertEqual(len(check_forbidden_bits({203273: _row(203273, **{col: bit})}, stock)), 1, (col, bit))
        self.assertEqual(check_forbidden_bits({203273: _row(203273, SpellClassMask_3=m.GLACIAL_ADVANCE)}, stock), [])
        self.assertEqual(check_forbidden_bits({1: _row(1, SpellClassMask_3=0x80000000)}, stock), [])  # not an S2 id
        # new rows: effect masks count; edited stock rows: own mask only, minus what stock already carried
        self.assertEqual(len(check_forbidden_bits({203280: _row(203280, EffectSpellClassMaskB_1=0x400000)}, stock)), 1)
        self.assertEqual(check_forbidden_bits({49143: _row(49143, EffectSpellClassMaskB_1=0x400000)}, stock), [])
        self.assertEqual(len(check_forbidden_bits({49143: _row(49143, SpellClassMask_1=0x400000)}, stock)), 1)
        kept = {49143: _row(49143, SpellClassMask_1=0x400000)}
        self.assertEqual(check_forbidden_bits(kept, kept), [])  # stock already carried it

    def test_no_d2_b13(self):
        self.assertEqual(check_no_d2_b13({203273: _row(203273, SpellClassMask_3=m.GLACIAL_ADVANCE)}), [])
        self.assertEqual(len(check_no_d2_b13({203273: _row(203273, SpellClassMask_3=B13_BIT)})), 1)
        self.assertEqual(len(check_no_d2_b13({49143: _row(49143, SpellClassMask_3=B13_BIT)})), 1)
        self.assertEqual(len(check_no_d2_b13({203280: _row(203280, EffectSpellClassMaskC_3=B13_BIT)})), 1)
        # S1's own d2 b13 carriers are not S2 ids; Runic Focus' S1 reader is allowed
        self.assertEqual(check_no_d2_b13({203144: _row(203144, SpellClassMask_3=B13_BIT)}), [])
        self.assertEqual(check_no_d2_b13({RUNIC_FOCUS: _row(RUNIC_FOCUS, EffectSpellClassMaskA_3=B13_BIT)}), [])

    def test_runic_focus(self):
        self.assertEqual(check_runic_focus({RUNIC_FOCUS: _row(RUNIC_FOCUS, EffectSpellClassMaskA_3=0x12600)}), [])
        for d2 in (0x2000, 0x10200, 0x10400, 0x600, 0):
            self.assertEqual(len(check_runic_focus({RUNIC_FOCUS: _row(RUNIC_FOCUS, EffectSpellClassMaskA_3=d2)})), 1, d2)
        self.assertEqual(check_runic_focus({}), [])

    def test_killing_machine(self):
        mk = m.KILLING_MACHINE_READ

        def run(rows=None, entries=None, procs=None, procs_rm=None, scr_rm=None, scripts=None):
            good_rows = {KM_BUFF: _row(KM_BUFF, CumulativeAura=2, ProcCharges=0, Effect_1=6, EffectAura_1=AURA_ADD_FLAT,
                                       EffectMiscValue_1=7, EffectSpellClassMaskA_1=mk[0], EffectSpellClassMaskA_2=mk[1],
                                       EffectSpellClassMaskA_3=mk[2])}
            good_procs = [_proc(sid, 0x4, 0, Chance=c) for sid, c in KM_RANKS.items()]
            return check_killing_machine(
                rows if rows is not None else good_rows,
                entries if entries is not None else {KM_BUFF: {"duration_ms": 30000}},
                procs if procs is not None else good_procs,
                procs_rm if procs_rm is not None else [{"SpellId": 51129}, {"SpellId": 51130}],
                scr_rm if scr_rm is not None else [{"spell_id": -51123, "ScriptName": "spell_gen_no_offhand_proc"}],
                scripts if scripts is not None else [{"spell_id": -51123, "ScriptName": "spell_dk_killing_machine_talent"}])

        self.assertEqual(run(), [])
        buff = _row(KM_BUFF, CumulativeAura=2, ProcCharges=0, Effect_1=6, EffectAura_1=AURA_ADD_FLAT, EffectMiscValue_1=7,
                    EffectSpellClassMaskA_1=mk[0], EffectSpellClassMaskA_2=mk[1], EffectSpellClassMaskA_3=mk[2])
        for cols in ({"CumulativeAura": 0}, {"ProcCharges": 1}, {"EffectAura_1": AURA_ADD_PCT},
                     {"EffectMiscValue_1": 0}, {"EffectSpellClassMaskA_2": 0x1}):
            self.assertGreaterEqual(len(run(rows={KM_BUFF: {**buff, **cols}})), 1, cols)
        self.assertEqual(len(run(entries={KM_BUFF: {"duration_ms": 15000}})), 1)
        ranks = [_proc(sid, 0x4, 0, Chance=c) for sid, c in KM_RANKS.items()]
        self.assertEqual(len(run(procs=[*ranks, _proc(KM_BUFF)])), 1)  # the buff must not proc
        self.assertEqual(len(run(procs=ranks[1:])), 1)  # a missing positive rank row
        self.assertEqual(len(run(procs=[dict(ranks[0], ProcsPerMinute=1.0), *ranks[1:]])), 1)  # PPM
        self.assertEqual(len(run(procs=[dict(ranks[0], Chance=5), *ranks[1:]])), 1)  # wrong chance
        self.assertEqual(len(run(procs=[dict(ranks[0], ProcFlags=0x10), *ranks[1:]])), 1)  # not auto attack
        self.assertEqual(len(run(procs=[*ranks, _proc(-51123, 0x4, 0)])), 1)  # shadowing negative row
        self.assertEqual(len(run(procs_rm=[{"SpellId": 51129}])), 1)
        self.assertEqual(len(run(scr_rm=[])), 1)
        self.assertEqual(len(run(scripts=[])), 1)
        self.assertEqual(run(rows={}, entries={}), [])  # unbuilt buff row is not this check's business

    def test_neutralised_hardcodes(self):
        good = {sid: _row(sid, Effect_1=6, EffectAura_1=AURA_DUMMY, EffectMiscValue_1=0)
                for sid in (*MERCILESS_RANKS, *TUNDRA_RANKS)}
        good.update({sid: _row(sid, SpellIconID=2965) for sid in GLACIER_ROT_RANKS})
        good.update({sid: _row(sid, SpellIconID=2710, Effect_1=6, EffectAura_1=290) for sid in ANNIHILATION_RANKS})
        good.update({sid: _row(sid, Effect_1=6, EffectAura_1=AURA_ADD_PCT, EffectMiscValue_1=0)
                     for sid in BOTN_RANKS})
        self.assertEqual(check_neutralised_hardcodes(good), [])
        self.assertEqual(len(check_neutralised_hardcodes({**good, 49024: _row(49024, Effect_1=6, EffectAura_1=4,
                                                                             EffectMiscValue_1=7277)})), 1)
        self.assertEqual(len(check_neutralised_hardcodes({**good, 50127: _row(50127, Effect_1=6, EffectAura_1=4,
                                                                             EffectMiscValue_2=7277, Effect_2=6,
                                                                             EffectAura_2=4)})), 1)
        self.assertEqual(len(check_neutralised_hardcodes({**good, 49202: _row(49202, Effect_1=6, EffectAura_1=4,
                                                                             TargetAuraState=2)})), 1)
        self.assertEqual(len(check_neutralised_hardcodes({**good, 49790: _row(49790, SpellIconID=196)})), 1)
        self.assertEqual(len(check_neutralised_hardcodes({**good, 51472: _row(51472, SpellIconID=2710, Effect_1=6,
                                                                             EffectAura_1=AURA_DUMMY)})), 1)
        self.assertEqual(len(check_neutralised_hardcodes({**good, 54638: _row(54638, Effect_1=6,
                                                                             EffectAura_1=AURA_PERIODIC_DUMMY)})), 2)
        self.assertEqual(len(check_neutralised_hardcodes({**good, 54637: _row(54637, Effect_1=6, EffectAura_1=AURA_ADD_PCT,
                                                                             EffectMiscValue_1=5)})), 1)

    def test_botn_removals(self):
        rows = {sid: _row(sid, ProcTypeMask=0) for sid in BOTN_RANKS}
        rm = [{"SpellId": -54639}]
        sr = [{"spell_id": -54639, "ScriptName": "spell_dk_death_rune"}]
        self.assertEqual(check_botn_removals(rows, rm, sr), [])
        self.assertEqual(len(check_botn_removals(rows, [], sr)), 1)
        self.assertEqual(len(check_botn_removals(rows, rm, [])), 1)
        self.assertEqual(len(check_botn_removals({**rows, 54638: _row(54638, ProcTypeMask=0x14)}, rm, sr)), 1)

    def test_proc_phases(self):
        cast = [_proc(sid, 0x10, PHASE_CAST) for sid in (203278, 203292, 203281, 49149, 203302)]
        hit = [_proc(sid, 0x10, PHASE_HIT) for sid in (49143, 203054, 49188)]
        self.assertEqual(check_proc_phases([*cast, *hit]), [])
        self.assertEqual(len(check_proc_phases([_proc(203278, 0x10, PHASE_HIT)])), 1)  # CAST talent in the HIT phase
        self.assertEqual(len(check_proc_phases([_proc(-49149, 0x10, 0)])), 1)  # negative id counts, phase 0
        self.assertEqual(len(check_proc_phases([_proc(49143, 0x10, 4)])), 1)  # a HIT talent left in the FINISH phase
        self.assertEqual(len(check_proc_phases([_proc(203054, 0x40000, 0)])), 1)  # DONE_PERIODIC
        self.assertEqual(check_proc_phases([_proc(203054, 0x2, 4)]), [])  # TAKEN-only flag
        self.assertEqual(check_proc_phases([_proc(51123, 0x4, 0)]), [])  # auto-attack proc: not a spell-class flag
        self.assertEqual(check_proc_phases([_proc(1, 0x10, 4)]), [])  # not an S2 id
        self.assertEqual(check_proc_phases([_proc(203054, 0x10, 0, AttributesMask=PROC_ATTR_REQ_SPELLMOD)]), [])

    def test_offhand_copies(self):
        def copy(sid, pct_bp=59, **cols):
            row = _row(sid, Effect_1=31, Effect_2=121, EffectBasePoints_1=pct_bp)
            row.update(cols)
            return row

        rows = {sid: copy(sid) for sid in OFFHAND}
        rows.update({main: copy(main) for main, _, _ in OFFHAND.values()})
        entries = {sid: _entry(sid, [(0.0, 1.5, 20)]) for sid in OFFHAND}
        for sid, (main, flat, main_flat) in OFFHAND.items():
            entries[sid] = {"id": sid, "effect2": {"type": 121, "_potency": {"total_potency": flat if flat is not None else 3.0,
                                                                            "t_seconds": 1.5, "kind": "direct"}}}
            entries[main] = {"id": main, "effect2": {"type": 121, "_potency": {
                "total_potency": main_flat if main_flat is not None else 6.0, "t_seconds": 1.5, "kind": "direct"}}}
        self.assertEqual(check_offhand_copies(rows, entries), [])
        self.assertEqual(len(check_offhand_copies({**rows, 66198: copy(66198, Effect_1=121, Effect_2=31)}, entries)), 2)
        self.assertEqual(len(check_offhand_copies({**rows, 66188: copy(66188, Effect_3=7)}, entries)), 1)  # per-disease E2
        self.assertEqual(len(check_offhand_copies({**rows, 66216: copy(66216, EffectAura_3=4)}, entries)), 1)
        self.assertEqual(len(check_offhand_copies({**rows, 203322: copy(203322, pct_bp=10)}, entries)), 1)  # not mirrored
        full_obl = {**entries, 66198: {"id": 66198, "effect2": {"type": 121, "_potency": {"total_potency": 10.0,
                                                                                      "t_seconds": 1.5, "kind": "direct"}}}}
        self.assertEqual(len(check_offhand_copies(rows, full_obl)), 1)  # physical copy kept the FULL flat (D1)
        half_fs = {**entries, 66196: {"id": 66196, "effect2": {"type": 121, "_potency": {"total_potency": 2.5,
                                                                                     "t_seconds": 1.5, "kind": "direct"}}}}
        self.assertEqual(len(check_offhand_copies(rows, half_fs)), 1)  # Frost Strike OH must keep the full flat
        ps_full = {**entries, 66216: {"id": 66216, "effect2": {"type": 121, "_potency": {"total_potency": 6.0,
                                                                                     "t_seconds": 1.5, "kind": "direct"}}}}
        self.assertEqual(len(check_offhand_copies(rows, ps_full)), 1)  # PS copy must be half of PS's flat
        self.assertEqual(check_offhand_copies({}, {}), [])

    def test_guile(self):
        def guile(bp0=14, bp2=29, **cols):
            row = _row(50187, Effect_1=6, EffectAura_1=108, EffectMiscValue_1=15, EffectBasePoints_1=bp0,
                       EffectSpellClassMaskA_2=0x20004, Effect_2=6, EffectAura_2=4,
                       Effect_3=6, EffectAura_3=108, EffectMiscValue_3=15, EffectBasePoints_3=bp2,
                       EffectSpellClassMaskC_2=0x2)
            row.update(cols)
            return {50187: row}

        self.assertEqual(check_guile(guile()), [])
        self.assertEqual(len(check_guile(guile(bp2=14))), 1)  # eff2 not twice eff0
        self.assertEqual(len(check_guile(guile(EffectSpellClassMaskA_1=4194304))), 1)  # stale raw mask on eff0
        self.assertEqual(len(check_guile(guile(EffectSpellClassMaskC_2=0x20006))), 1)
        self.assertEqual(len(check_guile(guile(EffectAura_3=107))), 1)
        self.assertEqual(len(check_guile(guile(EffectMiscValue_3=0))), 1)
        self.assertEqual(len(check_guile(guile(Effect_3=0))), 1)  # eff2 missing
        self.assertEqual(len(check_guile(guile(EffectBonusMultiplier_3=1.0))), 1)  # stale twin
        self.assertEqual(check_guile({}), [])

    def test_icy_talons_capstone(self):
        def desc(rank):
            tail = "Increases the melee attack speed of all party and raid members within $55610a1 yards by $55610s1%."
            return ("You leech heat. $s2%." + (f"\n\nCapstone: {tail}" if rank == 50885
                                              else f"\n\n|cFF9D9D9DCapstone: {tail}|r"))

        def rows(over=None):
            out = {IIT_PASSIVE: _row(IIT_PASSIVE, Attributes=0x50, Effect_1=65, EffectAura_1=138, EffectBasePoints_1=9,
                                     EffectRadiusIndex_1=29)}
            for rank, (buff, stored) in ICY_TALONS_BUFF_BP.items():
                out[buff] = _row(buff, EffectBasePoints_1=stored, EffectAura_1=138)
                out[rank] = _row(rank, EffectBasePoints_1=stored, EffectBasePoints_2=stored, Description_Lang_enUS=desc(rank))
            for sid, cols in (over or {}).items():
                out[sid] = {**out[sid], **cols}
            return out

        talents = [{"id": 2223, "tab_id": RETIRED_TAB, "tier": 0, "column": 0, "rank_spell_ids": []},
                   {"id": 2042, "tab_id": FROST_TAB, "tier": 2, "column": 0, "rank_spell_ids": [50880, 50884, 50885]}]
        links = [{"spell_trigger": 50885, "spell_effect": 55610, "type": 2}]
        self.assertEqual(check_icy_talons_capstone(rows(), talents, links), [])
        # the talent comes back on the Frost tab, or into the emptied cell, or another talent names the passive
        back = [{**talents[0], "tab_id": FROST_TAB, "tier": 5, "column": 0, "rank_spell_ids": [55610]}, talents[1]]
        self.assertGreaterEqual(len(check_icy_talons_capstone(rows(), back, links)), 3)
        # the self +5% (aura 193 on a second effect) or a stale value on the party aura
        self.assertEqual(len(check_icy_talons_capstone(rows({55610: {"Effect_2": 6, "EffectAura_2": 193,
                                                                      "EffectBasePoints_2": 4}}), talents, links)), 2)
        self.assertEqual(len(check_icy_talons_capstone(rows({55610: {"EffectBasePoints_1": 4}}), talents, links)), 1)
        self.assertEqual(len(check_icy_talons_capstone(rows({55610: {"EffectAura_1": 192}}), talents, links)), 1)
        # no link, a link on rank 1, a link of the wrong type
        self.assertEqual(len(check_icy_talons_capstone(rows(), talents, [])), 1)
        self.assertEqual(len(check_icy_talons_capstone(rows(), talents, [{**links[0], "spell_trigger": 50880}])), 1)
        self.assertEqual(len(check_icy_talons_capstone(rows(), talents, [{**links[0], "type": 0}])), 1)
        # old buff values 7 / 14 / 20 % (stored 6 / 13 / 19), on the buff or on the rank
        self.assertEqual(len(check_icy_talons_capstone(rows({50882: {"EffectBasePoints_1": 6}}), talents, links)), 1)
        self.assertEqual(len(check_icy_talons_capstone(rows({50885: {"EffectBasePoints_1": 19}}), talents, links)), 1)
        # tooltip: no capstone paragraph, a grey capstone on the last rank, a plain one on a lower rank
        self.assertEqual(len(check_icy_talons_capstone(rows({50880: {"Description_Lang_enUS": "You leech heat."}}),
                                                       talents, links)), 1)
        self.assertEqual(len(check_icy_talons_capstone(rows({50885: {"Description_Lang_enUS": desc(50880)}}),
                                                       talents, links)), 1)
        self.assertEqual(len(check_icy_talons_capstone(rows({50884: {"Description_Lang_enUS": desc(50885)}}),
                                                       talents, links)), 1)
        self.assertEqual(check_icy_talons_capstone({}, [], links), [])

    def test_icy_talons_proc(self):
        good = {sid: _row(sid, ProcTypeMask=0x11010) for sid in ICY_TALONS_RANKS}
        self.assertEqual(check_icy_talons_proc(good), [])
        self.assertEqual(len(check_icy_talons_proc({**good, 50884: _row(50884, ProcTypeMask=0x1010)})), 1)

    def test_rime(self):
        rows = {sid: _row(sid, EffectAura_1=4, EffectAura_2=42, EffectTriggerSpell_2=59052, ProcChance=c)
                for sid, c in zip(RIME_RANKS, RIME_CHANCE)}
        self.assertEqual(check_rime(rows), [])
        for cols in ({"EffectAura_2": 4}, {"EffectAura_2": 0, "EffectAura_3": 42}, {"EffectTriggerSpell_2": 0},
                     {"ProcChance": 5}, {"EffectAura_1": 42}):
            self.assertGreaterEqual(len(check_rime({**rows, 56822: {**rows[56822], **cols}})), 1, cols)

    def test_tooltips(self):
        def tip(text, col="Description_Lang_enUS"):
            return {203273: _row(203273, **{col: text})}

        for ok in ("Deals damage to enemies in a line.", "Capstone: Obliterate has no cooldown.", ""):
            self.assertEqual(check_no_cost_cooldown_tooltips(tip(ok)), [], ok)
        for bad in ("Deals damage. 2 min cooldown.", "Deals damage. 8 sec cooldown", "Deals damage. Cooldown: 2 min",
                    "Deals damage. Costs 30 Runic Power.", "Deals damage. 1 Frost Rune.", "Deals damage. 15 Runic Power."):
            self.assertEqual(len(check_no_cost_cooldown_tooltips(tip(bad))), 1, bad)
        self.assertEqual(len(check_no_cost_cooldown_tooltips(tip("Grants haste. 1 min cooldown.", "AuraDescription_Lang_enUS"))), 1)
        self.assertEqual(check_no_cost_cooldown_tooltips({1: _row(1, Description_Lang_enUS="x. 2 min cooldown.")}), [])

    def test_sdv(self):
        good = [{"id": i, "Variables": "$gravefro=5\n$obl=3"} for i in SDV_IDS]
        self.assertEqual(check_sdv(good), [])
        self.assertEqual(len(check_sdv(good[1:])), 1)
        long = [{"id": 1253, "Variables": "$koltirasfavor=5"}, *good[1:]]
        self.assertEqual(len(check_sdv(long)), 1)
        self.assertEqual(len(check_sdv([{"id": 1253, "Variables": "$abcdefghijklm=5"}, *good[1:]])), 1)  # 13 chars

    def test_id_blocks(self):
        ok_slas = [{"id": i} for i in SLA.values()]
        ok_sdv = [{"id": i} for i in SDV_IDS]
        ok_talents = [{"id": 60345}, {"id": 60358}, {"id": 1968}]
        ok_costs = [{"ID": 2600}, {"ID": 2601}]

        def run(spells=frozenset(S2_NEW), talents=ok_talents, slas=ok_slas, sdv=ok_sdv, costs=ok_costs, groups=(),
                creatures=()):
            return check_id_blocks(set(spells), talents, slas, sdv, costs, list(groups), list(creatures))

        self.assertEqual(run(), [])
        self.assertEqual(run(spells={*S2_NEW, 203157, 203440}), [])  # other stages' ids are not ours
        self.assertEqual(len(run(spells={*S2_NEW, 203326})), 1)  # spare block
        self.assertEqual(len(run(spells={*S2_NEW, 203439})), 1)
        self.assertEqual(len(run(talents=[*ok_talents, {"id": 60359}])), 1)
        self.assertEqual(len(run(slas=[*ok_slas, {"id": 30753}])), 1)
        self.assertEqual(len(run(sdv=[*ok_sdv, {"id": 1256}])), 1)
        self.assertEqual(len(run(costs=[*ok_costs, {"ID": 2603}])), 1)
        self.assertEqual(len(run(groups=[{"id": 1273}])), 1)
        self.assertEqual(len(run(creatures=[{"entry": 300322}])), 1)
        self.assertEqual(run(groups=[{"id": 1022}], creatures=[{"entry": 99999}, {"entry": 300340}]), [])


if __name__ == "__main__":
    unittest.main()
