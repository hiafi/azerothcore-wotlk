"""
Death Knight S1 (Blood) data gate (death-knight-rework S1a-HANDOFF row A5, S1a-WP-BRIEF).

Same shape as lib/test_deathknight_dk0a.py / test_deathknight_dk0b.py: the real deathknight DSL package is loaded once
(shared `_data()` cache) and every check runs on the BUILT rows (stock base + DSL + raw_overrides), so a stale pulled
raw_overrides key that wins over the DSL fails here too. Each check is a pure function that returns problem strings,
with a negative fixture below. An id no agent has declared yet is reported by `test_required_ids_declared` and
skipped by the other checks.

  1. Grid: tab 398 holds the 33 talents of S1-HANDOFF section 3 at the right cells, 76 points, the new talents' rank
     spells, no depends_on, 11 empty cells.
  2. The five new castables' SkillLineAbility rows (30740-30744, skill 770, class 32, acquire 0).
  3. Marrowrend 203123: percent effect first, flat second, nothing third, d2 b8 only, rune cost 2601 = blood 0 /
     unholy 1 / frost 1 / RP 20 (stored x10), SpellLevel 20.
  4. No S1 row (new or edited) carries a `_masks.FORBIDDEN_*` bit in its own SpellClassMask (new rows: effect masks too).
  5. d2 b13 / d2 b15 carriers are exactly the brief's lists (own masks and effect-mask readers).
  6. Subversion / Bloody Strikes / Might of Mograine effect masks never hold d0 b22 and read d2 b8.
  7. Sudden Doom spell_proc mask 0x1040000. 8. Runic Focus mask holds d2 b13. 9. Mark of Blood ProcCharges 10.
 10. Dancing Rune Weapon has no Runic Power cost. 11. Bloodworms aura 231 stored 1 (value 2), 18 s summon, no proc cd.
 12. Bonestorm USE_ALL_MANA + HASTE_AFFECTS_PERIODIC. 13. Shroud aura 301 + 88 + NO_AURA_CANCEL; lockout
     NO_IMMUNITIES + ALLOW_AURA_WHILE_DEAD. 14. Blood Gorged ARP misc physical, damage passives bp 2/5/8 with no
     points_per_level. 15. Veteran of the Third War without aura 240.
 16. Every S1 DONE spell-class / DONE_PERIODIC spell_proc row has SpellPhaseMask 2.
 17. No S1 tooltip ends in "cooldown.". 18. SpellDescriptionVariables names <= 12 chars (1250-1252 declared).
 19. Vendetta 50154 explicitly unbound from spell_dk_vendetta. 20. 52212 not declared / edited, 43265 stock fields kept.

Run: cd apps/dbc-tools && .venv/bin/python3 -m pytest lib/test_deathknight_s1.py -q -p no:cacheprovider
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import dbcfmt, state  # noqa: E402
from lib.test_deathknight_dk0a import _data, _hex, _u32, m, spell_mask  # noqa: E402

BLOOD_TAB = 398
SKILL_BLOOD = 770
CLASS_MASK_DK = 32

# talent id -> (tier, column, rank count)
GRID = {
    1939: (0, 0, 2), 1945: (0, 1, 3), 2017: (0, 2, 3), 60330: (0, 3, 3),
    1938: (1, 0, 3), 1948: (1, 1, 3), 2217: (1, 2, 2),
    60331: (2, 1, 1), 1943: (2, 2, 3),
    60332: (3, 0, 3), 2018: (3, 2, 3), 1953: (3, 3, 3),
    2015: (4, 0, 3), 60333: (4, 1, 1), 1950: (4, 2, 3), 1949: (4, 3, 1),
    60334: (5, 0, 3), 1944: (5, 1, 3), 2105: (5, 2, 2), 60335: (5, 3, 3),
    1960: (6, 0, 3), 1961: (6, 1, 1), 60336: (6, 2, 2), 60337: (6, 3, 1),
    2259: (7, 0, 2), 1955: (7, 1, 3), 60338: (7, 2, 1),
    1959: (8, 0, 3), 2019: (8, 1, 1), 1958: (8, 2, 3),
    2034: (9, 1, 3), 60339: (9, 2, 1),
    60340: (10, 1, 1),
}
GRID_POINTS = 76
GRID_TIERS, GRID_COLUMNS = 11, 4
NEW_TALENT_RANKS = {
    60330: [203120, 203121, 203122], 60331: [203123], 60332: [203124, 203125, 203126], 60333: [203127],
    60334: [203129, 203130, 203131], 60335: [203134, 203135, 203136], 60336: [203138, 203139], 60337: [203141],
    60338: [203143], 60339: [203145], 60340: [203148],
}
# castable spell -> SkillLineAbility id
SLA = {203123: 30740, 203127: 30741, 203141: 30742, 203143: 30743, 203148: 30744}

MARROWREND, MARROWREND_RUNE_COST, MARROWREND_LEVEL = 203123, 2601, 20
RUNIC_FOCUS = 61455
RUNIC_FOCUS_STOCK_MASK = (0x80040202, 0x10022, 0x9)
MARK_OF_BLOOD, DRW = 49005, 49028
BLOODWORM_RANKS, BLOODWORM_SUMMON = (49027, 49542, 49543), 50452
BONESTORM, SHROUD, LOCKOUT = 203148, 203146, 203147
ARP_PASSIVES = {61274: 2, 61275: 5, 61276: 9}
DAMAGE_PASSIVES = {50096: 2, 50108: 5, 50109: 8}
VETERAN_RANKS = (49006, 49526, 50029)
SUBVERSION_RANKS, BLOODY_STRIKES_RANKS, MIGHT_RANKS = (48997, 49490, 49491), (48977, 49394, 49395), (49023, 49533, 49534)
SUDDEN_DOOM = -49018
VENDETTA_RANK2 = 50154
D_AND_D, D_AND_D_TICK = 43265, 52212
SDV_IDS = (1250, 1251, 1252)

B13_OWN = {203144, 203149}
B13_READERS = {RUNIC_FOCUS}
B15_OWN = {45470, 203041, 50181, 50454, 203133, 203140, 203142, 203150, 203154}
B15_READERS: set[int] = set()

S1_NEW = tuple(range(203120, 203157))
S1_EDITED = (
    49998, 45470, 55050, 48721, RUNIC_FOCUS, 203041, 49222, DRW, MARK_OF_BLOOD, 61607,
    *SUBVERSION_RANKS, 49182, 49500, 49501, 51789, 64855, 64856, 49004, 49508, 49509, 50421, 50422,
    *VETERAN_RANKS, 48988, 49503, 49504, 50447, 50448, 50449, 53137, 53138, *BLOODWORM_RANKS, BLOODWORM_SUMMON,
    50453, 50454, 62905, 62908, 49018, 49529, 49530, *MIGHT_RANKS, 61154, 61155, 61156, *DAMAGE_PASSIVES, *ARP_PASSIVES,
    49015, 50154, 55136, 50181, *BLOODY_STRIKES_RANKS, 48987, 49477, 49478, 48978, 49390, 49391, 55107, 55108,
)
S1_IDS = frozenset(S1_NEW) | frozenset(S1_EDITED)
REQUIRED_IDS = (*S1_NEW, MARROWREND, RUNIC_FOCUS, MARK_OF_BLOOD, DRW, *BLOODWORM_RANKS, BLOODWORM_SUMMON,
                *SUBVERSION_RANKS, *BLOODY_STRIKES_RANKS, *MIGHT_RANKS, *DAMAGE_PASSIVES, *ARP_PASSIVES,
                *VETERAN_RANKS, D_AND_D)
# Stock-kept forbidden bits per S1 row (own SpellClassMask); none today.
FORBIDDEN_EXEMPT: dict[int, tuple[int, int, int]] = {}

ATTR0_NO_IMMUNITIES = 0x20000000
ATTR0_NO_AURA_CANCEL = 0x80000000
ATTR1_USE_ALL_MANA = 0x2
ATTR3_ALLOW_AURA_WHILE_DEAD = 0x100000
ATTR5_HASTE_AFFECTS_PERIODIC = 0x2000
PHASE_HIT = 2
PROC_ATTR_REQ_SPELLMOD = 0x8  # a cast-phase spellmod charge consumer (Crimson Scourge buff), not a damage roll
# PROC_FLAG_DONE_SPELL_{MELEE,RANGED,NONE_POS,NONE_NEG,MAGIC_POS,MAGIC_NEG}_DMG_CLASS | DONE_PERIODIC
PROC_DONE_SPELL_CLASS_AND_PERIODIC = 0x10 | 0x100 | 0x400 | 0x1000 | 0x4000 | 0x10000 | 0x40000
EFFECT_WEAPON_PERCENT_DAMAGE = 31
EFFECT_NORMALIZED_WEAPON_DMG = 121
POWER_RUNE = 5
AURA_HEAL_ABSORB, AURA_HEALTH_REGEN_PCT, AURA_BLOODWORM_PROC, AURA_EXPERTISE = 301, 88, 231, 240
SCHOOL_PHYSICAL = 1
COOLDOWN_SENTENCE = re.compile(r"\d+(\.\d+)? ?(min|sec|s|m)\w* cooldown\.$")  # "1.5 min cooldown."; "has no cooldown." is fine
SDV_NAME = re.compile(r"^\$(\w+)=", re.MULTILINE)
MAX_SDV_NAME = 12
D_AND_D_PINNED = {"Attributes": 67108864, "AttributesEx": 136, "AttributesEx3": 0, "AttributesEx5": 512,
                  "RuneCostID": 101, "PowerType": POWER_RUNE, "CategoryRecoveryTime": 30000, "Effect_1": 27,
                  "EffectAura_1": 226, "EffectBasePoints_1": 8}  # RETUNE 2026-10-25 re-anchor: was 25
D_AND_D_MASK = (m.DEATH_AND_DECAY, 0, 0)
STOCK_COMPARE_COLUMNS = ("Attributes", "AttributesEx", "AttributesEx2", "AttributesEx3", "AttributesEx4",
                         "AttributesEx5", "AttributesEx6", "AttributesEx7", "Effect_1", "Effect_2", "Effect_3",
                         "EffectAura_1", "EffectAura_2", "EffectAura_3", "EffectBasePoints_1", "EffectBasePoints_2",
                         "EffectBasePoints_3", "SpellClassMask_1", "SpellClassMask_2", "SpellClassMask_3",
                         "ProcTypeMask", "ProcCharges", "RecoveryTime", "CategoryRecoveryTime", "SchoolMask")


def _fmt(value) -> str:
    return f"{value:#x}" if isinstance(value, int) and not isinstance(value, bool) else repr(value)


def _i(row: dict, col: str) -> int:
    return int(row.get(col) or 0)


def _effects(row: dict) -> list[dict]:
    """Used effect slots: {n, type, aura, bp, die, misc, ppl}."""
    out = []
    for n in (1, 2, 3):
        if _i(row, f"Effect_{n}"):
            out.append({"n": n, "type": _i(row, f"Effect_{n}"), "aura": _i(row, f"EffectAura_{n}"),
                        "bp": _i(row, f"EffectBasePoints_{n}"), "die": _i(row, f"EffectDieSides_{n}"),
                        "misc": _i(row, f"EffectMiscValue_{n}"), "ppl": float(row.get(f"EffectRealPointsPerLevel_{n}") or 0)})
    return out


def _effect_mask(row: dict, n: int = 1) -> tuple[int, int, int]:
    letter = "ABC"[n - 1]
    return tuple(_u32(row.get(f"EffectSpellClassMask{letter}_{d}")) for d in (1, 2, 3))


def _all_effect_masks(row: dict) -> list[tuple[int, int, int]]:
    return [_effect_mask(row, n) for n in (1, 2, 3)]


def _present(rows_by_id: dict[int, dict], *ids: int):
    return [(i, rows_by_id[i]) for i in ids if i in rows_by_id]


# ---- checks (pure: take built rows / declared tables, return problem strings) ----------------------------------

def check_required_ids(rows_by_id: dict[int, dict]) -> list[str]:
    return [f"{i}: not declared by any deathknight DSL file" for i in REQUIRED_IDS if i not in rows_by_id]


def check_grid(talents: list[dict]) -> list[str]:
    bad = []
    tab = [t for t in talents if int(t["tab_id"]) == BLOOD_TAB]
    by_id = {int(t["id"]): t for t in tab}
    if len(tab) != len(by_id):
        bad.append("tab 398: duplicate talent ids")
    if len(by_id) != len(GRID):
        bad.append(f"tab 398 holds {len(by_id)} talents, expected {len(GRID)}")
    for tid in sorted(set(GRID) - set(by_id)):
        bad.append(f"talent {tid}: not on tab 398")
    for tid in sorted(set(by_id) - set(GRID)):
        bad.append(f"talent {tid}: unexpected on tab 398")
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
        got_ranks = len([r for r in t.get("rank_spell_ids") or [] if int(r)])
        points += got_ranks
        if got_ranks != ranks:
            bad.append(f"talent {tid}: {got_ranks} ranks, expected {ranks}")
        if t.get("depends_on"):
            bad.append(f"talent {tid}: depends_on {t['depends_on']!r}, expected none")
    for tid, ranks in NEW_TALENT_RANKS.items():
        t = by_id.get(tid)
        if t is not None and [int(r) for r in t.get("rank_spell_ids") or [] if int(r)] != ranks:
            bad.append(f"talent {tid}: rank spells {t.get('rank_spell_ids')!r}, expected {ranks}")
    for cell, n in cells.items():
        if n > 1:
            bad.append(f"cell {cell}: {n} talents")
    if points != GRID_POINTS:
        bad.append(f"tab 398: {points} points, expected {GRID_POINTS}")
    empty = GRID_TIERS * GRID_COLUMNS - len(cells)
    if empty != 11:
        bad.append(f"tab 398: {empty} empty cells, expected 11")
    return bad


def check_skill_lines(slas: list[dict]) -> list[str]:
    bad = []
    for spell, sla_id in SLA.items():
        rows = [s for s in slas if int(s["spell_id"]) == spell]
        if len(rows) != 1:
            bad.append(f"{spell}: {len(rows)} SkillLineAbility rows, expected 1")
            continue
        s = rows[0]
        for label, got, want in (("id", int(s["id"]), sla_id), ("skill_line", int(s["skill_line"]), SKILL_BLOOD),
                                 ("class_mask", int(s.get("class_mask") or 0), CLASS_MASK_DK),
                                 ("acquire_method", int(s.get("acquire_method") or 0), 0)):
            if got != want:
                bad.append(f"{spell}: SLA {label} {got}, expected {want}")
    return bad


def check_marrowrend(rows_by_id: dict[int, dict], rune_costs: list[dict]) -> list[str]:
    row = rows_by_id.get(MARROWREND)
    if row is None:
        return []
    bad = []
    if _i(row, "Effect_1") != EFFECT_WEAPON_PERCENT_DAMAGE:
        bad.append(f"{MARROWREND}: effect 0 is {row.get('Effect_1')!r}, expected WEAPON_PERCENT_DAMAGE (31) first")
    if _i(row, "Effect_2") != EFFECT_NORMALIZED_WEAPON_DMG:
        bad.append(f"{MARROWREND}: effect 1 is {row.get('Effect_2')!r}, expected NORMALIZED_WEAPON_DMG (121) second")
    if _i(row, "Effect_3"):
        bad.append(f"{MARROWREND}: effect 2 is {row.get('Effect_3')!r}, expected nothing in the third slot")
    if _i(row, "PowerType") != POWER_RUNE:
        bad.append(f"{MARROWREND}: PowerType {row.get('PowerType')!r}, expected 5 (rune)")
    if _i(row, "RuneCostID") != MARROWREND_RUNE_COST:
        bad.append(f"{MARROWREND}: RuneCostID {row.get('RuneCostID')!r}, expected {MARROWREND_RUNE_COST}")
    cost = [c for c in rune_costs if int(c["ID"]) == MARROWREND_RUNE_COST]
    if not cost:
        bad.append(f"rune cost {MARROWREND_RUNE_COST}: not declared")
    else:
        got = tuple(int(cost[0][k]) for k in ("Blood", "Unholy", "Frost", "RunicPower"))
        if got != (0, 1, 1, 200):
            bad.append(f"rune cost {MARROWREND_RUNE_COST}: blood/unholy/frost/RP {got}, expected (0, 1, 1, 200) "
                       f"(RP stored x10)")
    mask = spell_mask(row)
    if mask != (0, 0, m.MARROWREND):
        bad.append(f"{MARROWREND}: SpellClassMask {_hex(mask)}, expected (0x0, 0x0, 0x{m.MARROWREND:X}) - d2 b8 only")
    if _i(row, "SpellLevel") != MARROWREND_LEVEL:
        bad.append(f"{MARROWREND}: SpellLevel {row.get('SpellLevel')!r}, expected {MARROWREND_LEVEL}")
    return bad


def check_forbidden_bits(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for sid, row in _present(rows_by_id, *sorted(S1_IDS)):
        exempt = FORBIDDEN_EXEMPT.get(sid, (0, 0, 0))
        masks = [("SpellClassMask", spell_mask(row))]
        if sid in S1_NEW:
            masks += [(f"EffectSpellClassMask{'ABC'[n]}", em) for n, em in enumerate(_all_effect_masks(row))]
        for label, mask in masks:
            hit = (mask[0] & m.FORBIDDEN_D0 & ~exempt[0], mask[1] & m.FORBIDDEN_D1 & ~exempt[1],
                   mask[2] & m.FORBIDDEN_D2 & ~exempt[2])
            if any(hit):
                bad.append(f"{sid}: {label} {_hex(mask)} holds forbidden bits {_hex(hit)}")
    return bad


def check_d2_carriers(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for label, bit, own_want, read_want in (("b13", m.BLOOD_OTHER_MAGIC, B13_OWN, B13_READERS),
                                            ("b15", m.DK_SELF_HEAL, B15_OWN, B15_READERS)):
        own = {sid for sid, row in rows_by_id.items() if spell_mask(row)[2] & bit}
        readers = {sid for sid, row in rows_by_id.items() if any(em[2] & bit for em in _all_effect_masks(row))}
        for sid in sorted(own_want - own):
            bad.append(f"{sid}: SpellClassMask lacks d2 {label}")
        for sid in sorted(own - own_want):
            bad.append(f"{sid}: unexpected d2 {label} carrier in SpellClassMask")
        for sid in sorted(read_want - readers):
            bad.append(f"{sid}: effect mask lacks d2 {label} (reader)")
        for sid in sorted(readers - read_want):
            bad.append(f"{sid}: unexpected d2 {label} in an effect mask (reader)")
    return bad


def check_reader_masks(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    groups = (("Subversion", SUBVERSION_RANKS), ("Bloody Strikes", BLOODY_STRIKES_RANKS),
              ("Might of Mograine", MIGHT_RANKS))
    for name, ids in groups:
        for sid, row in _present(rows_by_id, *ids):
            masks = [spell_mask(row), *_all_effect_masks(row)]
            if any(mk[0] & m.FORBIDDEN_D0_B22 for mk in masks):
                bad.append(f"{sid} ({name}): a mask still holds d0 b22 (Blood Strike)")
            if not any(em[2] & m.MARROWREND for em in _all_effect_masks(row)):
                bad.append(f"{sid} ({name}): no effect mask reads d2 b8 (Marrowrend)")
    for sid, row in _present(rows_by_id, *SUBVERSION_RANKS):
        if _effect_mask(row, 1) != tuple(m.SUBVERSION_READ):
            bad.append(f"{sid} (Subversion): effect 0 mask {_hex(_effect_mask(row, 1))}, expected "
                       f"{_hex(m.SUBVERSION_READ)}")
    return bad


def check_sudden_doom_proc(procs: list[dict]) -> list[str]:
    rows = [p for p in procs if int(p["SpellId"]) == SUDDEN_DOOM]
    if len(rows) != 1:
        return [f"{SUDDEN_DOOM}: {len(rows)} spell_proc rows, expected 1"]
    got = (int(rows[0]["SpellFamilyMask0"]), int(rows[0]["SpellFamilyMask1"]), int(rows[0]["SpellFamilyMask2"]))
    if got != (0x1040000, 0, 0):
        return [f"{SUDDEN_DOOM}: spell_proc family mask {_hex(got)}, expected (0x1040000, 0x0, 0x0)"]
    return []


def check_runic_focus(rows_by_id: dict[int, dict]) -> list[str]:
    row = rows_by_id.get(RUNIC_FOCUS)
    if row is None:
        return []
    mask = _effect_mask(row)
    want = tuple(a | b | c for a, b, c in zip(RUNIC_FOCUS_STOCK_MASK, m.RUNIC_FOCUS_READ_ADD,
                                              (0, 0, m.BLOOD_OTHER_MAGIC)))
    missing = tuple(w & ~g for w, g in zip(want, mask))
    if any(missing):
        return [f"{RUNIC_FOCUS}: effect mask {_hex(mask)} lacks bits {_hex(missing)} (incl. d2 b13)"]
    return []


def check_mark_of_blood(rows_by_id: dict[int, dict], procs: list[dict]) -> list[str]:
    row = rows_by_id.get(MARK_OF_BLOOD)
    if row is None:
        return []
    bad = []
    if _i(row, "ProcCharges") != 10:
        bad.append(f"{MARK_OF_BLOOD}: ProcCharges {row.get('ProcCharges')!r}, expected 10")
    for p in procs:
        if int(p["SpellId"]) == MARK_OF_BLOOD and int(p.get("Charges") or 0) not in (0, 10):
            bad.append(f"{MARK_OF_BLOOD}: spell_proc Charges {p.get('Charges')!r}, expected 0 (use the spell's) or 10")
    return bad


def check_drw(rows_by_id: dict[int, dict]) -> list[str]:
    row = rows_by_id.get(DRW)
    if row is None:
        return []
    bad = []
    for col in ("ManaCost", "RuneCostID", "ManaCostPct"):
        if _i(row, col):
            bad.append(f"{DRW}: {col} {row.get(col)!r}, expected 0 (no Runic Power / rune cost)")
    return bad


def check_bloodworms(rows_by_id: dict[int, dict], procs: list[dict], entries: dict[int, dict]) -> list[str]:
    bad = []
    for sid, row in _present(rows_by_id, *BLOODWORM_RANKS):
        auras = [e for e in _effects(row) if e["aura"] == AURA_BLOODWORM_PROC]
        if len(auras) != 1:
            bad.append(f"{sid}: {len(auras)} aura-231 effects, expected 1")
        elif auras[0]["bp"] != 1 or auras[0]["die"] != 1:
            bad.append(f"{sid}: aura 231 stored bp {auras[0]['bp']} die_sides {auras[0]['die']}, expected 1 / 1 "
                       f"(fixed value 2)")
    for p in procs:
        if int(p["SpellId"]) == -BLOODWORM_RANKS[0] and int(p.get("Cooldown") or 0) != 0:
            bad.append(f"{p['SpellId']}: spell_proc Cooldown {p.get('Cooldown')!r}, expected 0")
    summon = entries.get(BLOODWORM_SUMMON)  # DSL entry: the built DurationIndex of a fresh ReuseContext is arbitrary
    if summon is not None:
        if _i(summon, "duration_ms") != 18000:
            bad.append(f"{BLOODWORM_SUMMON}: duration_ms {summon.get('duration_ms')!r}, expected 18000")
        if "DurationIndex" in (summon.get("raw_overrides") or {}):
            bad.append(f"{BLOODWORM_SUMMON}: raw_overrides DurationIndex would win over duration_ms")
    return bad


def check_bonestorm(rows_by_id: dict[int, dict]) -> list[str]:
    row = rows_by_id.get(BONESTORM)
    if row is None:
        return []
    bad = []
    if not _u32(row.get("AttributesEx")) & ATTR1_USE_ALL_MANA:
        bad.append(f"{BONESTORM}: AttributesEx {_u32(row.get('AttributesEx')):#x} lacks USE_ALL_MANA 0x2")
    if not _u32(row.get("AttributesEx5")) & ATTR5_HASTE_AFFECTS_PERIODIC:
        bad.append(f"{BONESTORM}: AttributesEx5 {_u32(row.get('AttributesEx5')):#x} lacks HASTE_AFFECTS_PERIODIC 0x2000")
    return bad


def check_shroud_and_lockout(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    row = rows_by_id.get(SHROUD)
    if row is not None:
        auras = {e["aura"] for e in _effects(row)}
        for want in (AURA_HEAL_ABSORB, AURA_HEALTH_REGEN_PCT):
            if want not in auras:
                bad.append(f"{SHROUD}: no aura {want} effect")
        if not _u32(row.get("Attributes")) & ATTR0_NO_AURA_CANCEL:
            bad.append(f"{SHROUD}: Attributes {_u32(row.get('Attributes')):#x} lacks NO_AURA_CANCEL 0x80000000")
    row = rows_by_id.get(LOCKOUT)
    if row is not None:
        if not _u32(row.get("Attributes")) & ATTR0_NO_IMMUNITIES:
            bad.append(f"{LOCKOUT}: Attributes {_u32(row.get('Attributes')):#x} lacks NO_IMMUNITIES 0x20000000")
        if not _u32(row.get("AttributesEx3")) & ATTR3_ALLOW_AURA_WHILE_DEAD:
            bad.append(f"{LOCKOUT}: AttributesEx3 {_u32(row.get('AttributesEx3')):#x} lacks ALLOW_AURA_WHILE_DEAD 0x100000")
    return bad


def check_blood_gorged(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for sid, want in ARP_PASSIVES.items():
        row = rows_by_id.get(sid)
        if row is None:
            continue
        if _i(row, "EffectMiscValue_1") != SCHOOL_PHYSICAL:
            bad.append(f"{sid}: EffectMiscValue_1 {row.get('EffectMiscValue_1')!r}, expected 1 (physical)")
        if _i(row, "EffectBasePoints_1") != want:
            bad.append(f"{sid}: EffectBasePoints_1 {row.get('EffectBasePoints_1')!r}, expected {want}")
    for sid, want in DAMAGE_PASSIVES.items():
        row = rows_by_id.get(sid)
        if row is None:
            continue
        if _i(row, "EffectBasePoints_1") != want:
            bad.append(f"{sid}: EffectBasePoints_1 {row.get('EffectBasePoints_1')!r}, expected {want}")
        for e in _effects(row):
            if e["ppl"]:
                bad.append(f"{sid}: effect {e['n'] - 1} has points_per_level {e['ppl']}, expected none")
        if _i(row, "MaxLevel"):
            bad.append(f"{sid}: MaxLevel {row.get('MaxLevel')!r}, expected 0 (no raw level cap)")
    return bad


def check_veteran(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for sid, row in _present(rows_by_id, *VETERAN_RANKS):
        if any(e["aura"] == AURA_EXPERTISE for e in _effects(row)):
            bad.append(f"{sid}: still has an aura-240 (expertise) effect")
        if _i(row, "Effect_3"):
            bad.append(f"{sid}: effect 2 {row.get('Effect_3')!r} not dropped")
    return bad


def check_proc_phases(procs: list[dict]) -> list[str]:
    bad = []
    for p in procs:
        sid = abs(int(p["SpellId"]))
        if sid in S1_IDS and int(p["ProcFlags"]) & PROC_DONE_SPELL_CLASS_AND_PERIODIC \
                and not int(p.get("AttributesMask") or 0) & PROC_ATTR_REQ_SPELLMOD \
                and int(p["SpellPhaseMask"]) != PHASE_HIT:
            bad.append(f"{p['SpellId']}: DONE spell-class / periodic proc row has SpellPhaseMask "
                       f"{p['SpellPhaseMask']!r}, expected 2")
    return bad


def check_no_cooldown_tooltips(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for sid, row in _present(rows_by_id, *sorted(S1_IDS)):
        for col in ("Description_Lang_enUS", "AuraDescription_Lang_enUS"):
            if COOLDOWN_SENTENCE.search(str(row.get(col) or "").strip()):
                bad.append(f"{sid}: {col} ends in a 'N min cooldown.' sentence")
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


def check_vendetta_unbound(removals: list[dict]) -> list[str]:
    if any(int(r["spell_id"]) == VENDETTA_RANK2 and r["ScriptName"] == "spell_dk_vendetta" for r in removals):
        return []
    return [f"{VENDETTA_RANK2}: no unbind_script(spell_dk_vendetta) - rank 2 would double-heal"]


def check_d_and_d_tick_untouched(rows_by_id: dict[int, dict], stock: dict[int, dict]) -> list[str]:
    """52212 is not an S1 edit: it is either absent from the DSL or still equal to the stock row on every gameplay column."""
    row = rows_by_id.get(D_AND_D_TICK)
    if row is None:
        return []
    base = stock.get(D_AND_D_TICK)
    if base is None:
        return [f"{D_AND_D_TICK}: declared by the DSL but has no stock row to compare"]
    return [f"{D_AND_D_TICK}: {col} {_fmt(_i(row, col))}, stock {_fmt(_i(base, col))}"
            for col in STOCK_COMPARE_COLUMNS if _i(row, col) != _i(base, col)]


def check_d_and_d_stock(rows_by_id: dict[int, dict]) -> list[str]:
    row = rows_by_id.get(D_AND_D)
    if row is None:
        return []
    bad = [f"{D_AND_D}: {col} {_fmt(_i(row, col))}, expected {_fmt(want)}"
           for col, want in D_AND_D_PINNED.items() if _i(row, col) != want]
    if spell_mask(row) != D_AND_D_MASK:
        bad.append(f"{D_AND_D}: SpellClassMask {_hex(spell_mask(row))}, expected {_hex(D_AND_D_MASK)}")
    return bad


# ---- real data ------------------------------------------------------------------------------------------------

class DeathKnightS1DataTest(unittest.TestCase):
    def assertClean(self, problems: list[str]):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def _rows(self):
        return _data()["rows_by_id"]

    def _pkg(self):
        return _data()["package"]

    def test_required_ids_declared(self):
        self.assertClean(check_required_ids(self._rows()))

    def test_grid(self):
        self.assertClean(check_grid(self._pkg().talents))

    def test_castable_skill_lines(self):
        self.assertClean(check_skill_lines(self._pkg().skill_line_abilities))

    def test_marrowrend(self):
        self.assertClean(check_marrowrend(self._rows(), self._pkg().spell_rune_costs))

    def test_no_forbidden_bits(self):
        self.assertClean(check_forbidden_bits(self._rows()))

    def test_d2_b13_b15_carriers(self):
        self.assertClean(check_d2_carriers(self._rows()))

    def test_reader_masks(self):
        self.assertClean(check_reader_masks(self._rows()))

    def test_sudden_doom_proc(self):
        self.assertClean(check_sudden_doom_proc(self._pkg().spell_procs))

    def test_runic_focus(self):
        self.assertClean(check_runic_focus(self._rows()))

    def test_mark_of_blood(self):
        self.assertClean(check_mark_of_blood(self._rows(), self._pkg().spell_procs))

    def test_drw(self):
        self.assertClean(check_drw(self._rows()))

    def test_bloodworms(self):
        entries = {int(e["id"]): e for e in self._pkg().spells}
        self.assertClean(check_bloodworms(self._rows(), self._pkg().spell_procs, entries))

    def test_bonestorm(self):
        self.assertClean(check_bonestorm(self._rows()))

    def test_shroud_and_lockout(self):
        self.assertClean(check_shroud_and_lockout(self._rows()))

    def test_blood_gorged(self):
        self.assertClean(check_blood_gorged(self._rows()))

    def test_veteran(self):
        self.assertClean(check_veteran(self._rows()))

    def test_proc_phases(self):
        self.assertClean(check_proc_phases(self._pkg().spell_procs))

    def test_no_cooldown_tooltips(self):
        self.assertClean(check_no_cooldown_tooltips(self._rows()))

    def test_sdv_names(self):
        self.assertClean(check_sdv(self._pkg().tooltip_vars))

    def test_vendetta_unbound(self):
        self.assertClean(check_vendetta_unbound(self._pkg().script_removals))

    def test_52212_untouched(self):
        self.assertClean(check_d_and_d_tick_untouched(self._rows(), state.load_stock_rows(dbcfmt.SPELL)))

    def test_43265_stock_fields(self):
        self.assertClean(check_d_and_d_stock(self._rows()))


# ---- negative fixtures: every check must fire on a minimal bad input --------------------------------------------

def _row(spell_id=1, **cols) -> dict:
    return {"ID": spell_id, **cols}


def _good_grid() -> list[dict]:
    out = []
    for tid, (tier, col, ranks) in GRID.items():
        spells = NEW_TALENT_RANKS.get(tid) or list(range(tid * 10, tid * 10 + ranks))
        out.append({"id": tid, "tab_id": BLOOD_TAB, "tier": tier, "column": col, "rank_spell_ids": spells,
                    "depends_on": None})
    return out


def _proc(sid, flags=0x10, phase=PHASE_HIT, **cols) -> dict:
    return {"SpellId": sid, "ProcFlags": flags, "SpellPhaseMask": phase, "SpellFamilyMask0": 0, "SpellFamilyMask1": 0,
            "SpellFamilyMask2": 0, "Cooldown": 0, "Charges": 0, **cols}


class DeathKnightS1NegativeTest(unittest.TestCase):
    def test_required_ids(self):
        self.assertEqual(check_required_ids({i: {} for i in REQUIRED_IDS}), [])
        self.assertEqual(len(check_required_ids({i: {} for i in REQUIRED_IDS if i != 203148})), 1)

    def test_grid(self):
        good = _good_grid()
        self.assertEqual(check_grid(good), [])
        moved = [dict(t) for t in good]
        moved[0]["tier"] = 1
        moved[0]["column"] = 1  # lands on 1945's neighbour cell (1,1) = Scent of Blood
        self.assertGreaterEqual(len(check_grid(moved)), 1)
        self.assertEqual(len(check_grid(good[1:])), 4)  # count, absent talent, points, 12 empty cells
        dep = [dict(t) for t in good]
        dep[3]["depends_on"] = {"talent_id": 1, "rank": 1}
        self.assertEqual(len(check_grid(dep)), 1)
        short = [dict(t) for t in good]
        short[1]["rank_spell_ids"] = short[1]["rank_spell_ids"][:2]
        self.assertGreaterEqual(len(check_grid(short)), 2)  # ranks + points
        extra = good + [{"id": 9999, "tab_id": BLOOD_TAB, "tier": 10, "column": 3, "rank_spell_ids": [1],
                         "depends_on": None}]
        self.assertGreaterEqual(len(check_grid(extra)), 1)
        wrong = [dict(t) for t in good]
        wrong[good.index(next(t for t in good if t["id"] == 60330))]["rank_spell_ids"] = [1, 2, 3]
        self.assertEqual(len(check_grid(wrong)), 1)
        retired = [dict(t) for t in good]
        retired[0]["tab_id"] = 60800
        self.assertGreaterEqual(len(check_grid(retired)), 1)

    def test_skill_lines(self):
        good = [{"id": i, "skill_line": 770, "spell_id": s, "class_mask": 32, "acquire_method": 0}
                for s, i in SLA.items()]
        self.assertEqual(check_skill_lines(good), [])
        for col, value in (("skill_line", 202), ("class_mask", 1), ("acquire_method", 1), ("id", 1)):
            bad = [dict(good[0], **{col: value}), *good[1:]]
            self.assertEqual(len(check_skill_lines(bad)), 1, col)
        self.assertEqual(len(check_skill_lines(good[1:])), 1)

    def test_marrowrend(self):
        def mr(**cols):
            row = _row(MARROWREND, Effect_1=31, Effect_2=121, PowerType=5, RuneCostID=2601,
                       SpellClassMask_3=0x100, SpellLevel=20)
            row.update(cols)
            return {MARROWREND: row}

        cost = [{"ID": 2601, "Blood": 0, "Unholy": 1, "Frost": 1, "RunicPower": 200}]
        self.assertEqual(check_marrowrend(mr(), cost), [])
        for cols in ({"Effect_1": 121, "Effect_2": 31}, {"Effect_3": 2}, {"PowerType": 0}, {"RuneCostID": 2600},
                     {"SpellClassMask_1": 0x400000}, {"SpellClassMask_3": 0x100 | 0x2}, {"SpellLevel": 19}):
            self.assertGreaterEqual(len(check_marrowrend(mr(**cols), cost)), 1, cols)
        for field, value in (("Blood", 1), ("Unholy", 0), ("Frost", 0), ("RunicPower", 20)):
            self.assertEqual(len(check_marrowrend(mr(), [{**cost[0], field: value}])), 1, field)
        self.assertEqual(len(check_marrowrend(mr(), [])), 1)
        self.assertEqual(check_marrowrend({}, []), [])

    def test_forbidden_bits(self):
        for col, bit in (("SpellClassMask_1", m.FORBIDDEN_D0_B6), ("SpellClassMask_1", m.FORBIDDEN_D0_B17),
                         ("SpellClassMask_1", m.FORBIDDEN_D0_B22), ("SpellClassMask_2", m.FORBIDDEN_D1_B10),
                         ("SpellClassMask_2", m.FORBIDDEN_D1_B11), ("SpellClassMask_2", m.FORBIDDEN_D1_B23),
                         ("SpellClassMask_2", m.FORBIDDEN_D1_B24), ("SpellClassMask_3", m.FORBIDDEN_D2_B1),
                         ("SpellClassMask_3", m.FORBIDDEN_D2_B31)):
            self.assertEqual(len(check_forbidden_bits({MARROWREND: _row(MARROWREND, **{col: bit})})), 1, (col, bit))
        self.assertEqual(check_forbidden_bits({MARROWREND: _row(MARROWREND, SpellClassMask_3=0x100)}), [])
        self.assertEqual(check_forbidden_bits({1: _row(1, SpellClassMask_3=0x80000000)}), [])  # not an S1 id
        # new rows: effect masks count too; edited stock rows only their own mask
        self.assertEqual(len(check_forbidden_bits({203140: _row(203140, EffectSpellClassMaskB_1=0x400000)})), 1)
        self.assertEqual(check_forbidden_bits({49998: _row(49998, EffectSpellClassMaskB_1=0x400000)}), [])

    def test_d2_carriers(self):
        rows = {sid: _row(sid, SpellClassMask_3=m.BLOOD_OTHER_MAGIC) for sid in B13_OWN}
        rows.update({sid: _row(sid, SpellClassMask_3=m.DK_SELF_HEAL) for sid in B15_OWN})
        rows[RUNIC_FOCUS] = _row(RUNIC_FOCUS, EffectSpellClassMaskA_3=m.BLOOD_OTHER_MAGIC)
        self.assertEqual(check_d2_carriers(rows), [])
        self.assertEqual(len(check_d2_carriers({k: v for k, v in rows.items() if k != 203149})), 1)  # missing b13
        self.assertEqual(len(check_d2_carriers({k: v for k, v in rows.items() if k != 203154})), 1)  # missing b15
        self.assertEqual(len(check_d2_carriers({**rows, 777: _row(777, SpellClassMask_3=m.DK_SELF_HEAL)})), 1)
        self.assertEqual(len(check_d2_carriers({**rows, 778: _row(778, SpellClassMask_3=m.BLOOD_OTHER_MAGIC)})), 1)
        self.assertEqual(len(check_d2_carriers({**rows, 779: _row(779, EffectSpellClassMaskC_3=m.DK_SELF_HEAL)})), 1)
        self.assertEqual(len(check_d2_carriers({k: v for k, v in rows.items() if k != RUNIC_FOCUS})), 1)

    def test_reader_masks(self):
        sub = tuple(m.SUBVERSION_READ)

        def reader(sid, mask=sub, **cols):
            return _row(sid, EffectSpellClassMaskA_1=mask[0], EffectSpellClassMaskA_2=mask[1],
                        EffectSpellClassMaskA_3=mask[2], **cols)

        good = {sid: reader(sid) for sid in SUBVERSION_RANKS}
        good.update({sid: _row(sid, EffectSpellClassMaskB_1=m.HEART_STRIKE, EffectSpellClassMaskB_3=m.MARROWREND)
                     for sid in (*BLOODY_STRIKES_RANKS, *MIGHT_RANKS)})
        self.assertEqual(check_reader_masks(good), [])
        old = {**good, 48997: reader(48997, (sub[0] | 0x400000, sub[1], sub[2]))}
        self.assertEqual(len(check_reader_masks(old)), 2)  # d0 b22 + not the exact Subversion mask
        no_marrow = {**good, 49023: _row(49023, EffectSpellClassMaskA_1=m.DEATH_STRIKE)}
        self.assertEqual(len(check_reader_masks(no_marrow)), 1)
        bad_effect = {**good, 49490: reader(49490, (m.HEART_STRIKE, 0, m.MARROWREND))}
        self.assertEqual(len(check_reader_masks(bad_effect)), 1)
        b22_other_effect = {**good, 48977: _row(48977, EffectSpellClassMaskB_1=0x400000, EffectSpellClassMaskB_3=0x100)}
        self.assertEqual(len(check_reader_masks(b22_other_effect)), 1)

    def test_sudden_doom_proc(self):
        self.assertEqual(check_sudden_doom_proc([_proc(SUDDEN_DOOM, SpellFamilyMask0=0x1040000)]), [])
        self.assertEqual(len(check_sudden_doom_proc([_proc(SUDDEN_DOOM, SpellFamilyMask0=0x1400000)])), 1)
        self.assertEqual(len(check_sudden_doom_proc([_proc(SUDDEN_DOOM, SpellFamilyMask0=0x1040000,
                                                           SpellFamilyMask2=1)])), 1)
        self.assertEqual(len(check_sudden_doom_proc([])), 1)

    def test_runic_focus(self):
        want = tuple(a | b | c for a, b, c in zip(RUNIC_FOCUS_STOCK_MASK, m.RUNIC_FOCUS_READ_ADD,
                                                  (0, 0, m.BLOOD_OTHER_MAGIC)))
        good = {RUNIC_FOCUS: _row(RUNIC_FOCUS, EffectSpellClassMaskA_1=want[0], EffectSpellClassMaskA_2=want[1],
                                  EffectSpellClassMaskA_3=want[2])}
        self.assertEqual(check_runic_focus(good), [])
        no_b13 = {RUNIC_FOCUS: dict(good[RUNIC_FOCUS], EffectSpellClassMaskA_3=want[2] & ~m.BLOOD_OTHER_MAGIC)}
        self.assertEqual(len(check_runic_focus(no_b13)), 1)
        no_stock = {RUNIC_FOCUS: dict(good[RUNIC_FOCUS], EffectSpellClassMaskA_1=0)}
        self.assertEqual(len(check_runic_focus(no_stock)), 1)

    def test_mark_of_blood(self):
        self.assertEqual(check_mark_of_blood({MARK_OF_BLOOD: _row(MARK_OF_BLOOD, ProcCharges=10)}, []), [])
        self.assertEqual(len(check_mark_of_blood({MARK_OF_BLOOD: _row(MARK_OF_BLOOD, ProcCharges=20)}, [])), 1)
        self.assertEqual(len(check_mark_of_blood({MARK_OF_BLOOD: _row(MARK_OF_BLOOD, ProcCharges=10)},
                                                 [_proc(MARK_OF_BLOOD, Charges=20)])), 1)

    def test_drw(self):
        self.assertEqual(check_drw({DRW: _row(DRW, ManaCost=0, RuneCostID=0)}), [])
        self.assertEqual(len(check_drw({DRW: _row(DRW, ManaCost=600)})), 1)
        self.assertEqual(len(check_drw({DRW: _row(DRW, RuneCostID=5)})), 1)

    def test_bloodworms(self):
        good = {sid: _row(sid, Effect_1=6, EffectAura_1=231, EffectBasePoints_1=1, EffectDieSides_1=1)
                for sid in BLOODWORM_RANKS}
        ents = {BLOODWORM_SUMMON: {"id": BLOODWORM_SUMMON, "duration_ms": 18000, "raw_overrides": {"Foo": 1}}}
        procs = [_proc(-49027, Cooldown=0)]
        self.assertEqual(check_bloodworms(good, procs, ents), [])
        self.assertEqual(len(check_bloodworms({**good, 49542: _row(49542, Effect_1=6, EffectAura_1=231,
                                                                 EffectBasePoints_1=5, EffectDieSides_1=1)}, procs, ents)), 1)
        self.assertEqual(len(check_bloodworms({**good, 49543: _row(49543, Effect_1=6, EffectAura_1=4)}, procs, ents)), 1)
        self.assertEqual(len(check_bloodworms(good, [_proc(-49027, Cooldown=20000)], ents)), 1)
        slow = {BLOODWORM_SUMMON: dict(ents[BLOODWORM_SUMMON], duration_ms=15000)}
        self.assertEqual(len(check_bloodworms(good, procs, slow)), 1)
        raw = {BLOODWORM_SUMMON: dict(ents[BLOODWORM_SUMMON], raw_overrides={"DurationIndex": 85})}
        self.assertEqual(len(check_bloodworms(good, procs, raw)), 1)

    def test_bonestorm(self):
        good = {BONESTORM: _row(BONESTORM, AttributesEx=0x2, AttributesEx5=0x2000)}
        self.assertEqual(check_bonestorm(good), [])
        self.assertEqual(len(check_bonestorm({BONESTORM: _row(BONESTORM, AttributesEx=0, AttributesEx5=0x2000)})), 1)
        self.assertEqual(len(check_bonestorm({BONESTORM: _row(BONESTORM, AttributesEx=0x2, AttributesEx5=0)})), 1)

    def test_shroud_and_lockout(self):
        good = {SHROUD: _row(SHROUD, Effect_1=6, EffectAura_1=301, Effect_2=6, EffectAura_2=88,
                             Attributes=0x80000000),
                LOCKOUT: _row(LOCKOUT, Attributes=0x20000000 | 0x04000000, AttributesEx3=0x100000)}
        self.assertEqual(check_shroud_and_lockout(good), [])
        self.assertEqual(len(check_shroud_and_lockout({**good, SHROUD: dict(good[SHROUD], EffectAura_1=69)})), 1)
        self.assertEqual(len(check_shroud_and_lockout({**good, SHROUD: dict(good[SHROUD], EffectAura_2=0)})), 1)
        self.assertEqual(len(check_shroud_and_lockout({**good, SHROUD: dict(good[SHROUD], Attributes=0)})), 1)
        self.assertEqual(len(check_shroud_and_lockout({**good, LOCKOUT: dict(good[LOCKOUT], Attributes=0x04000000)})), 1)
        self.assertEqual(len(check_shroud_and_lockout({**good, LOCKOUT: dict(good[LOCKOUT], AttributesEx3=0)})), 1)

    def test_blood_gorged(self):
        good = {sid: _row(sid, Effect_1=6, EffectMiscValue_1=1, EffectBasePoints_1=bp) for sid, bp in ARP_PASSIVES.items()}
        good.update({sid: _row(sid, Effect_1=6, EffectBasePoints_1=bp) for sid, bp in DAMAGE_PASSIVES.items()})
        self.assertEqual(check_blood_gorged(good), [])
        self.assertEqual(len(check_blood_gorged({**good, 61274: dict(good[61274], EffectMiscValue_1=127)})), 1)
        self.assertEqual(len(check_blood_gorged({**good, 61276: dict(good[61276], EffectBasePoints_1=10)})), 1)
        self.assertEqual(len(check_blood_gorged({**good, 50109: dict(good[50109], EffectBasePoints_1=9)})), 1)
        self.assertEqual(len(check_blood_gorged({**good, 50096: dict(good[50096], EffectRealPointsPerLevel_1=0.5)})), 1)
        self.assertEqual(len(check_blood_gorged({**good, 50108: dict(good[50108], MaxLevel=80)})), 1)

    def test_veteran(self):
        good = {sid: _row(sid, Effect_1=6, EffectAura_1=137, Effect_2=6, EffectAura_2=137) for sid in VETERAN_RANKS}
        self.assertEqual(check_veteran(good), [])
        with_expertise = {**good, 49526: dict(good[49526], Effect_3=6, EffectAura_3=240)}
        self.assertEqual(len(check_veteran(with_expertise)), 2)  # aura 240 and an occupied third slot
        self.assertEqual(len(check_veteran({**good, 50029: dict(good[50029], Effect_3=6, EffectAura_3=4)})), 1)

    def test_proc_phases(self):
        self.assertEqual(check_proc_phases([_proc(203153, 0x10 | 0x4, 2), _proc(-203134, 0x4, 0),
                                            _proc(1, 0x40000, 0), _proc(-49004, 0x8, 0)]), [])
        self.assertEqual(len(check_proc_phases([_proc(203153, 0x10 | 0x4, 0)])), 1)
        self.assertEqual(len(check_proc_phases([_proc(-48988, 0x40000 | 0x10, 1)])), 1)
        self.assertEqual(len(check_proc_phases([_proc(-48988, 0x4000, 4)])), 1)
        # a spellmod charge consumer rolls on cast (phase 1) by design; only that attribute exempts it
        self.assertEqual(check_proc_phases([_proc(203137, 0x4000, 1, AttributesMask=0x8)]), [])
        self.assertEqual(len(check_proc_phases([_proc(203137, 0x4000, 1, AttributesMask=0x1)])), 1)

    def test_no_cooldown_tooltips(self):
        self.assertEqual(check_no_cooldown_tooltips({203123: _row(203123, Description_Lang_enUS="Smash the target.")}), [])
        self.assertEqual(len(check_no_cooldown_tooltips(
            {203143: _row(203143, Description_Lang_enUS="Erupt. 1 min cooldown.")})), 1)
        self.assertEqual(len(check_no_cooldown_tooltips(
            {49028: _row(49028, AuraDescription_Lang_enUS="Parry. 1.5 min cooldown. ")})), 1)
        self.assertEqual(check_no_cooldown_tooltips(
            {203137: _row(203137, Description_Lang_enUS="Your next Death and Decay has no cooldown.")}), [])
        self.assertEqual(check_no_cooldown_tooltips({1: _row(1, Description_Lang_enUS="x cooldown.")}), [])

    def test_sdv(self):
        good = [{"id": i, "Variables": "$bloody1=${1}\r\n$potency=${2}"} for i in SDV_IDS]
        self.assertEqual(check_sdv(good), [])
        long_name = [dict(good[0], Variables="$bloody_strikes1=${1}"), *good[1:]]
        self.assertEqual(len(check_sdv(long_name)), 1)
        self.assertEqual(len(check_sdv(good[:2])), 1)

    def test_vendetta_unbound(self):
        good = [{"spell_id": 50154, "ScriptName": "spell_dk_vendetta"}]
        self.assertEqual(check_vendetta_unbound(good), [])
        self.assertEqual(len(check_vendetta_unbound([])), 1)
        self.assertEqual(len(check_vendetta_unbound([{"spell_id": 49015, "ScriptName": "spell_dk_vendetta"}])), 1)
        self.assertEqual(len(check_vendetta_unbound([{"spell_id": 50154, "ScriptName": "other"}])), 1)

    def test_52212(self):
        stock = {D_AND_D_TICK: _row(D_AND_D_TICK, Attributes=0x4, AttributesEx3=0, SpellClassMask_3=0x8)}
        self.assertEqual(check_d_and_d_tick_untouched({}, stock), [])  # not in the DSL: untouched
        self.assertEqual(check_d_and_d_tick_untouched({D_AND_D_TICK: dict(stock[D_AND_D_TICK])}, stock), [])
        suppress = {D_AND_D_TICK: dict(stock[D_AND_D_TICK], AttributesEx3=0x10000)}
        self.assertEqual(len(check_d_and_d_tick_untouched(suppress, stock)), 1)
        self.assertEqual(len(check_d_and_d_tick_untouched({D_AND_D_TICK: dict(stock[D_AND_D_TICK], SpellClassMask_3=0x2008)},
                                                          stock)), 1)
        self.assertEqual(len(check_d_and_d_tick_untouched({D_AND_D_TICK: stock[D_AND_D_TICK]}, {})), 1)

    def test_43265(self):
        good = _row(D_AND_D, **{k: v for k, v in D_AND_D_PINNED.items()}, SpellClassMask_1=0x20)
        self.assertEqual(check_d_and_d_stock({D_AND_D: good}), [])
        for col, value in (("AttributesEx3", 0x10000), ("RuneCostID", 0), ("CategoryRecoveryTime", 0),
                           ("EffectBasePoints_1", 99), ("SpellClassMask_3", 0x8)):
            self.assertGreaterEqual(len(check_d_and_d_stock({D_AND_D: dict(good, **{col: value})})), 1, col)
        self.assertEqual(check_d_and_d_stock({}), [])


if __name__ == "__main__":
    unittest.main()
