"""
Death Knight S3 (Unholy) data gate (death-knight-rework S3a-HANDOFF row A5, S3a-WP-BRIEF D1-D16, S3-HANDOFF 3-5).

Same shape as lib/test_deathknight_s2.py: the real deathknight DSL package is loaded once (shared `_data()` cache) and
every check runs on the BUILT rows (stock base + DSL + raw_overrides). Each check is a pure function that returns
problem strings, with a negative fixture below. Written from the SPEC (brief + handoffs), not from the data, so a check
fails until the owning DSL file lands the row. An id nobody declared yet is reported by `test_required_ids_declared`
and skipped by the other checks.

  1. Grid: tab 400 holds the 35 talents of S3-HANDOFF section 3 at the right cells / ranks, 80 points, one prerequisite
     (Ebon Plaguebringer -> Crypt Fever rank index 2), skill_line 772. 2. SkillLineAbility 30760 / 30761 (skill 772).
  3. Scourge Strike 55090: percent effect first, normalized 0-value second, rune cost 2602, SpellLevel 15, d1 b27.
  4. Festering Wound debuff 203456: CumulativeAura 10, DOT_STACKING_RULE, no dispel, not periodic / linked, no bits.
  5. Burst / overflow / explosion 203457-9: d2 b11, Mechanic 22, potency 30 / 30 / 9, SpellLevel 20.
  6. On a Pale Horse damage 203477 d2 b17 (potency 40, SL 25). 7. Lesser Ghoul summon 203469 d2 b14, finite duration, props 61.
  8. Carriers of d2 b11 / b14 / b17 exactly per S3-HANDOFF section 5. 9. No S3 row on a FORBIDDEN bit.
 10. Runic Focus holds d2 b17; Razorice's reader mask is unchanged. 11. Rage of Rivendare ranks lose misc 7293 / aura 240.
 12. Crypt Fever / Ebon Plague rank ids kept with misc 7282; 50508 DOT_STACKING_RULE. 13. Impurity ranks (family 15,
     DUMMY, icon 1986, gone from the druid file). 14. Desolation buffs icon 235. 15. Night of the Dead holder / icon.
 16. Gargoyle Strike cast time 130; Summon Gargoyle 0 RP / 120 s / 26 s; Corpse Explosion 300 RP internal / no cooldown.
 17. Harbinger buff = charged SPELLMOD_COST, no spell_proc row. 18. Spell_proc phases (CAST 1, auto-attack 0, other 2).
 19. No tooltip ends in a cost / cooldown sentence. 20. SDV names <= 12 chars. 21. Cloud tick time basis 1000 ms.

Run: cd apps/dbc-tools && .venv/bin/python3 -m pytest -q lib/test_deathknight_s3.py -p no:cacheprovider
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import dbcfmt, state  # noqa: E402
from lib.test_deathknight_dk0a import _data, _hex, _u32, m, spell_mask  # noqa: E402
from lib.test_deathknight_s1 import (  # noqa: E402
    SDV_NAME, MAX_SDV_NAME, _all_effect_masks, _effect_mask, _effects, _i, _present,
)
from lib.test_deathknight_s2 import COOLDOWN_SENTENCE, COST_SENTENCE  # noqa: E402

TOOL_ROOT = Path(__file__).resolve().parents[1]
TALENTS_FILE = TOOL_ROOT / "source" / "classes" / "deathknight" / "deathknight_talents.py"
DRUID_FILE = TOOL_ROOT / "source" / "classes" / "druid" / "druid_trigger_spells.py"

UNHOLY_TAB = 400
SKILL_UNHOLY = 772
CLASS_MASK_DK = 32

# talent id -> (tier, column, rank spell ids). Section 3 of S3-HANDOFF.
GRID: dict[int, tuple[int, int, list[int]]] = {
    2082: (0, 0, [51745, 51746]), 1932: (0, 1, [48962, 49567, 49568]), 2218: (0, 2, [55129, 55130, 55131]),
    1963: (1, 0, [49036, 49562]), 2216: (1, 1, [55090]), 1933: (1, 2, [48963, 49564, 49565]),
    1934: (1, 3, [48965, 49571, 49572]),
    2008: (2, 0, [49013, 55236, 55237]), 60365: (2, 1, [203440]), 2047: (2, 2, [51459, 51462, 51463]),
    60366: (2, 3, [203441, 203442]),
    2039: (3, 0, [49146, 51267]), 1984: (3, 1, [52143]), 2004: (3, 2, [49219, 49627, 49628]),
    2025: (3, 3, [49588, 49589]),
    1996: (4, 0, [49194]), 2005: (4, 1, [49220, 49633, 49635]), 2011: (4, 2, [49223, 49599]), 1985: (4, 3, [49158]),
    2001: (5, 0, [49208, 56834, 56835]), 2009: (5, 1, [49224, 49610, 49611]), 2226: (5, 2, [55666, 55667]),
    2225: (5, 3, [55620, 55623]),
    60367: (6, 0, [203443, 203444]), 2036: (6, 1, [50117, 50118, 50119]), 60368: (6, 2, [203445, 203446, 203447]),
    60369: (6, 3, [203448]),
    60370: (7, 0, [203449, 203450, 203451]), 1962: (7, 1, [49032, 49631, 49632]), 2285: (7, 2, [66799, 66814, 66815]),
    2003: (8, 0, [49217, 49654, 49655]), 60371: (8, 1, [203452]), 60372: (8, 3, [203453, 203454, 203455]),
    2043: (9, 1, [51099, 51160, 51161]),
    2000: (10, 1, [49206]),
}
GRID_TALENTS, GRID_POINTS = 35, 80
PREREQS: dict[int, dict] = {2043: {"talent_id": 1962, "rank": 2}}
SLA = {203448: 30760, 203452: 30761}

# S3 new spells 203440-203478 (brief section 2)
S3_NEW = tuple(range(203440, 203479))
S3_NEW_TALENTS = tuple(range(60365, 60373))
SCOURGE_STRIKE_ID, SS_RUNE_COST, SS_LEVEL = 55090, 2602, 15
WOUND, WOUND_BURST, WOUND_OVERFLOW, WOUND_EXPLOSION = 203456, 203457, 203458, 203459
WOUND_DAMAGE = {WOUND_BURST: 30.0, WOUND_OVERFLOW: 30.0, WOUND_EXPLOSION: 9.0}
WOUND_LEVEL, WOUND_MECHANIC = 20, 22
OPH_DAMAGE, OPH_POTENCY, OPH_LEVEL = 203477, 40.0, 25
LESSER_GHOUL_SUMMON, LESSER_GHOUL_PROPS = 203469, 61
BOILING_BLIGHT_BURST = 203043
RUNIC_FOCUS, RAZORICE = 61455, 51714
NIGHT_OF_THE_DEAD = (55620, 55623)
ROR_RANKS = (50117, 50118, 50119)
CRYPT_FEVER_RANKS, EBON_PLAGUE_RANKS = (49032, 49631, 49632), (51099, 51160, 51161)
CRYPT_FEVER_DEBUFF = 50508
IMPURITY_RANKS = (49220, 49633, 49635)
DESOLATION_BUFFS = (63583, 66800, 66801)
GARGOYLE_STRIKE, SUMMON_GARGOYLE, CORPSE_EXPLOSION = 51963, 49206, 49158
HARBINGER_BUFF = 203463
CLOUD, CLOUD_TICK = 203472, 203473

SS_PERCENT_FIRST = 31  # WEAPON_PERCENT_DAMAGE
EFFECT_NORMALIZED_WEAPON_DMG, EFFECT_SUMMON = 121, 28
AURA_DUMMY, AURA_ADD_FLAT, AURA_ADD_PCT = 4, 107, 108
PERIODIC_AURAS = {3, 8, 20, 23, 24, 53, 62, 64, 89, 226}
SPELLMOD_DURATION, SPELLMOD_COST = 1, 14
ATTR3_DOT_STACKING_RULE = 0x80
MISC_ROR_HARDCODE, AURA_ROR_HARDCODE, MISC_DISEASE_AMOUNT = 7293, 240, 7282
ICON_IMPURITY, ICON_DESOLATION, ICON_NIGHT_OF_THE_DEAD = 1986, 235, 2718
GARGOYLE_STRIKE_CAST_INDEX, GARGOYLE_COOLDOWN_MS, GARGOYLE_DURATION_MS = 130, 120000, 26000
CORPSE_EXPLOSION_COST = (6, 300)  # PowerType runic power, ManaCost internal (x10 of display)
RUNE_COST_ROW = (1, 0, 1, 150)  # blood, unholy, frost, runic power x10

D2_B11, D2_B14, D2_B17 = m.ROT_DAMAGE, m.LESSER_GHOUL, m.UNHOLY_OTHER_MAGIC
# S3-HANDOFF section 5: own-mask carriers (DK0b's Boiling Blight burst joins b11; the Rot group's other DK0b/DK0a
# carriers are listed by the test of those stages and are filtered to the S3 ids + DK0b's burst here)
B11_OWN = {WOUND_BURST, WOUND_OVERFLOW, WOUND_EXPLOSION, BOILING_BLIGHT_BURST}
B14_OWN = {LESSER_GHOUL_SUMMON}
B17_OWN = {OPH_DAMAGE}
B11_READERS, B14_READERS, B17_READERS = {RUNIC_FOCUS}, set(NIGHT_OF_THE_DEAD), {RUNIC_FOCUS}

# CAST-phase (phase 1) talents, auto-attack rows (phase 0), spell_proc SpellId absolute values
CAST_PHASE = {203445, 203446, 203447, 203449, 203450, 203451, 49223, 49599}  # + Dirge (U27: CAST on PS + SS)
AUTO_ATTACK_PHASE = {203453, 203454, 203455}
PHASE_NONE, PHASE_CAST, PHASE_HIT = 0, 1, 2
PROC_ATTR_REQ_SPELLMOD = 0x8
PROC_DONE_SPELL_CLASS_AND_PERIODIC = 0x10 | 0x100 | 0x400 | 0x1000 | 0x4000 | 0x10000 | 0x40000

# edited stock rows (rank spells of the kept talents + shared rows); new rows are S3_NEW
KEPT_TALENT_RANKS = tuple(sid for tid, (_, _, ranks) in GRID.items() if tid < 60365 for sid in ranks)
SHARED_EDITS = (45462, 47541, 47632, 55078, 55095, 203043, RUNIC_FOCUS, 50842, 50508, 51726, 49206, 49158, 51963, 70890,
                50526, 63583, 66800, 66801)
S3_EDITED = tuple(dict.fromkeys((*KEPT_TALENT_RANKS, *SHARED_EDITS)))
S3_IDS = frozenset(S3_NEW) | frozenset(S3_EDITED)
REQUIRED_IDS = (*S3_NEW, *KEPT_TALENT_RANKS, 45462, 47541, CRYPT_FEVER_DEBUFF, 51726, SUMMON_GARGOYLE, GARGOYLE_STRIKE,
                CORPSE_EXPLOSION, *DESOLATION_BUFFS, RUNIC_FOCUS, RAZORICE, BOILING_BLIGHT_BURST)
HIDDEN_HELPERS = {203460, 203465, 203466, 203467, 203468, 203474, 203476}  # no client tooltip ever shown
SDV_IDS = (1254, 1280, 1281)


def _in(value: int, lo: int, hi: int) -> bool:
    return lo <= value <= hi


def _entry_potencies(entry: dict) -> list[float]:
    out = []
    for slot in ("effect1", "effect2", "effect3"):
        pot = (entry.get(slot) or {}).get("_potency")
        if pot and pot.get("kind") != "weapon":
            out.append(float(pot["total_potency"]))
    return out


# ---- checks (pure: take built rows / declared tables, return problem strings) ----------------------------------

def check_required_ids(rows_by_id: dict[int, dict]) -> list[str]:
    return [f"{i}: not declared by any deathknight DSL file" for i in REQUIRED_IDS if i not in rows_by_id]


def check_grid(talents: list[dict]) -> list[str]:
    bad = []
    tab = [t for t in talents if int(t["tab_id"]) == UNHOLY_TAB]
    by_id = {int(t["id"]): t for t in tab}
    if len(tab) != len(by_id):
        bad.append("tab 400: duplicate talent ids")
    if len(by_id) != GRID_TALENTS:
        bad.append(f"tab 400 holds {len(by_id)} talents, expected {GRID_TALENTS}")
    for tid in sorted(set(GRID) - set(by_id)):
        bad.append(f"talent {tid}: not on tab 400")
    for tid in sorted(set(by_id) - set(GRID)):
        bad.append(f"talent {tid}: unexpected on tab 400")
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
        if got != ranks:
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
        bad.append(f"tab 400: {points} points, expected {GRID_POINTS}")
    return bad


def check_tab_skill_line(talents_source: str) -> list[str]:
    """`skill_line` is DSL bookkeeping (not a TalentTab column, not in the package), so read the tab declaration source."""
    block = re.search(r"unholy_400_tab\s*=\s*tab\((.*?)\n\)", talents_source, re.DOTALL)
    if block is None:
        return ["unholy_400_tab: declaration not found in deathknight_talents.py"]
    found = re.search(r"\bskill_line\s*=\s*(\d+)", block.group(1))
    got = int(found.group(1)) if found else 0
    return [] if got == SKILL_UNHOLY else [f"tab 400: skill_line {got}, expected {SKILL_UNHOLY}"]


def check_skill_lines(slas: list[dict]) -> list[str]:
    bad = []
    for spell, sla_id in SLA.items():
        rows = [s for s in slas if int(s["spell_id"]) == spell]
        if len(rows) != 1:
            bad.append(f"{spell}: {len(rows)} SkillLineAbility rows, expected 1")
            continue
        s = rows[0]
        for label, got, want in (("id", int(s["id"]), sla_id), ("skill_line", int(s["skill_line"]), SKILL_UNHOLY),
                                 ("class_mask", int(s.get("class_mask") or 0), CLASS_MASK_DK),
                                 ("acquire_method", int(s.get("acquire_method") or 0), 0)):
            if got != want:
                bad.append(f"{spell}: SLA {label} {got}, expected {want}")
    return bad


def check_scourge_strike(rows_by_id: dict[int, dict], rune_costs: list[dict]) -> list[str]:
    row = rows_by_id.get(SCOURGE_STRIKE_ID)
    if row is None:
        return []
    bad = []
    if _i(row, "Effect_1") != SS_PERCENT_FIRST:
        bad.append(f"{SCOURGE_STRIKE_ID}: effect 0 is {row.get('Effect_1')!r}, expected WEAPON_PERCENT_DAMAGE (31) first")
    if _i(row, "Effect_2") != EFFECT_NORMALIZED_WEAPON_DMG:
        bad.append(f"{SCOURGE_STRIKE_ID}: effect 1 is {row.get('Effect_2')!r}, expected NORMALIZED_WEAPON_DMG (121) second")
    elif _i(row, "EffectBasePoints_2") + 1 + _i(row, "EffectDieSides_2") not in (0, 1):
        bad.append(f"{SCOURGE_STRIKE_ID}: normalized effect value {_i(row, 'EffectBasePoints_2') + 1}, expected 0 "
                   f"(bp -1: the cast stays normalized, no flat damage)")
    if _i(row, "RuneCostID") != SS_RUNE_COST:
        bad.append(f"{SCOURGE_STRIKE_ID}: RuneCostID {row.get('RuneCostID')!r}, expected {SS_RUNE_COST}")
    cost = [c for c in rune_costs if int(c["ID"]) == SS_RUNE_COST]
    if not cost:
        bad.append(f"rune cost {SS_RUNE_COST}: not declared")
    else:
        got = tuple(int(cost[0][k]) for k in ("Blood", "Unholy", "Frost", "RunicPower"))
        if got != RUNE_COST_ROW:
            bad.append(f"rune cost {SS_RUNE_COST}: blood/unholy/frost/RP {got}, expected {RUNE_COST_ROW} (RP stored x10)")
    if _i(row, "SpellLevel") != SS_LEVEL:
        bad.append(f"{SCOURGE_STRIKE_ID}: SpellLevel {row.get('SpellLevel')!r}, expected {SS_LEVEL}")
    if not spell_mask(row)[1] & m.SCOURGE_STRIKE:
        bad.append(f"{SCOURGE_STRIKE_ID}: SpellClassMask {_hex(spell_mask(row))} lacks d1 b27")
    return bad


def check_wound_debuff(rows_by_id: dict[int, dict], linked: list[dict]) -> list[str]:
    row = rows_by_id.get(WOUND)
    if row is None:
        return []
    bad = []
    if _i(row, "CumulativeAura") != 10:
        bad.append(f"{WOUND}: CumulativeAura {row.get('CumulativeAura')!r}, expected 10")
    if not _u32(row.get("AttributesEx3")) & ATTR3_DOT_STACKING_RULE:
        bad.append(f"{WOUND}: AttributesEx3 {_u32(row.get('AttributesEx3')):#x} lacks DOT_STACKING_RULE 0x80")
    if _i(row, "DispelType"):
        bad.append(f"{WOUND}: DispelType {row.get('DispelType')!r}, expected 0 (no dispel)")
    for eff in _effects(row):
        period = _i(row, "EffectAuraPeriod_%d" % eff["n"])
        if eff["aura"] in PERIODIC_AURAS or period:
            bad.append(f"{WOUND}: effect {eff['n'] - 1} is periodic (aura {eff['aura']}, period {period}), "
                       f"expected a plain marker")
    for link in linked:
        if WOUND in (int(link["spell_trigger"]), int(link["spell_effect"])):
            bad.append(f"{WOUND}: spell_linked_spell row {link!r} (the debuff must not be linked)")
    if any(spell_mask(row)) or any(any(em) for em in _all_effect_masks(row)):
        bad.append(f"{WOUND}: carries a family bit {_hex(spell_mask(row))} (wound debuff has no bit)")
    return bad


def check_wound_damage(rows_by_id: dict[int, dict], entries: dict[int, dict]) -> list[str]:
    bad = []
    for sid, want in WOUND_DAMAGE.items():
        row = rows_by_id.get(sid)
        if row is None:
            continue
        if not spell_mask(row)[2] & D2_B11:
            bad.append(f"{sid}: SpellClassMask {_hex(spell_mask(row))} lacks d2 b11")
        if _i(row, "Mechanic") != WOUND_MECHANIC:
            bad.append(f"{sid}: Mechanic {row.get('Mechanic')!r}, expected {WOUND_MECHANIC}")
        if _i(row, "SpellLevel") != WOUND_LEVEL:
            bad.append(f"{sid}: SpellLevel {row.get('SpellLevel')!r}, expected {WOUND_LEVEL}")
        entry = entries.get(sid)
        if entry is not None:
            pots = _entry_potencies(entry)
            if not any(abs(p - want) < 1e-6 for p in pots):
                bad.append(f"{sid}: potency {pots}, expected {want:g}")
    return bad


def check_oph_damage(rows_by_id: dict[int, dict], entries: dict[int, dict]) -> list[str]:
    row = rows_by_id.get(OPH_DAMAGE)
    if row is None:
        return []
    bad = []
    if not spell_mask(row)[2] & D2_B17:
        bad.append(f"{OPH_DAMAGE}: SpellClassMask {_hex(spell_mask(row))} lacks d2 b17")
    if _i(row, "SpellLevel") != OPH_LEVEL:
        bad.append(f"{OPH_DAMAGE}: SpellLevel {row.get('SpellLevel')!r}, expected {OPH_LEVEL}")
    entry = entries.get(OPH_DAMAGE)
    if entry is not None and not any(abs(p - OPH_POTENCY) < 1e-6 for p in _entry_potencies(entry)):
        bad.append(f"{OPH_DAMAGE}: potency {_entry_potencies(entry)}, expected {OPH_POTENCY:g}")
    return bad


def check_lesser_ghoul_summon(rows_by_id: dict[int, dict], entries: dict[int, dict]) -> list[str]:
    row = rows_by_id.get(LESSER_GHOUL_SUMMON)
    if row is None:
        return []
    bad = []
    if not spell_mask(row)[2] & D2_B14:
        bad.append(f"{LESSER_GHOUL_SUMMON}: SpellClassMask {_hex(spell_mask(row))} lacks d2 b14")
    summon = next((e for e in _effects(row) if e["type"] == EFFECT_SUMMON), None)
    if summon is None:
        bad.append(f"{LESSER_GHOUL_SUMMON}: no SUMMON (28) effect")
    elif _i(row, "EffectMiscValueB_%d" % summon["n"]) != LESSER_GHOUL_PROPS:
        bad.append(f"{LESSER_GHOUL_SUMMON}: summon properties {_i(row, 'EffectMiscValueB_%d' % summon['n'])}, "
                   f"expected {LESSER_GHOUL_PROPS}")
    if not _i(row, "DurationIndex"):
        bad.append(f"{LESSER_GHOUL_SUMMON}: DurationIndex 0 (infinite), expected a finite duration")
    entry = entries.get(LESSER_GHOUL_SUMMON)
    if entry is not None and not int(entry.get("duration_ms") or 0) > 0:
        bad.append(f"{LESSER_GHOUL_SUMMON}: duration_ms {entry.get('duration_ms')!r}, expected a finite duration")
    return bad


def check_d2_carriers(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for label, bit, own_want, read_want in (("b11", D2_B11, B11_OWN, B11_READERS), ("b14", D2_B14, B14_OWN, B14_READERS),
                                            ("b17", D2_B17, B17_OWN, B17_READERS)):
        own = {sid for sid, row in rows_by_id.items() if spell_mask(row)[2] & bit}
        readers = {sid for sid, row in rows_by_id.items() if any(em[2] & bit for em in _all_effect_masks(row))}
        for sid in sorted(own_want - own):
            bad.append(f"{sid}: SpellClassMask lacks d2 {label}")
        for sid in sorted(own - own_want):
            if label == "b11" and sid not in S3_IDS and sid != BOILING_BLIGHT_BURST:
                continue  # DK0a / DK0b / S1 Rot-group carriers are those stages' (their tests pin them)
            bad.append(f"{sid}: unexpected d2 {label} carrier in SpellClassMask")
        for sid in sorted(read_want - readers):
            if sid in rows_by_id:
                bad.append(f"{sid}: effect mask lacks d2 {label} (reader)")
    return bad


def check_forbidden_bits(rows_by_id: dict[int, dict], stock: dict[int, dict]) -> list[str]:
    bad = []
    for sid, row in _present(rows_by_id, *sorted(S3_IDS)):
        base = stock.get(sid)
        exempt = spell_mask(base) if base is not None and sid not in S3_NEW else (0, 0, 0)
        masks = [("SpellClassMask", spell_mask(row), exempt)]
        if sid in S3_NEW:
            masks += [(f"EffectSpellClassMask{'ABC'[n]}", em, (0, 0, 0)) for n, em in enumerate(_all_effect_masks(row))]
        for label, mask, ex in masks:
            hit = (mask[0] & m.FORBIDDEN_D0 & ~ex[0], mask[1] & m.FORBIDDEN_D1 & ~ex[1], mask[2] & m.FORBIDDEN_D2 & ~ex[2])
            if any(hit):
                bad.append(f"{sid}: {label} {_hex(mask)} holds forbidden bits {_hex(hit)}")
    return bad


def check_runic_focus_and_razorice(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    rf = rows_by_id.get(RUNIC_FOCUS)
    if rf is not None and not _effect_mask(rf)[2] & D2_B17:
        bad.append(f"{RUNIC_FOCUS}: effect mask d2 {_effect_mask(rf)[2]:#x} lacks b17 (On a Pale Horse damage)")
    rz = rows_by_id.get(RAZORICE)
    if rz is not None:
        want = tuple(m.FROST_VULN_READ_S2)
        if not any(em == want for em in _all_effect_masks(rz)):
            bad.append(f"{RAZORICE}: no effect mask equals FROST_VULN_READ_S2 {_hex(want)} "
                       f"(got {[_hex(em) for em in _all_effect_masks(rz)]})")
    return bad


def check_ror_ranks(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for sid, row in _present(rows_by_id, *ROR_RANKS):
        for eff in _effects(row):
            if eff["misc"] == MISC_ROR_HARDCODE:
                bad.append(f"{sid}: effect {eff['n'] - 1} still has misc {MISC_ROR_HARDCODE} (stock hardcode)")
            if eff["aura"] == AURA_ROR_HARDCODE:
                bad.append(f"{sid}: effect {eff['n'] - 1} still has aura {AURA_ROR_HARDCODE} (stock hardcode)")
    return bad


def check_disease_amount_ranks(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for sid, row in _present(rows_by_id, *CRYPT_FEVER_RANKS, *EBON_PLAGUE_RANKS):
        if not any(e["misc"] == MISC_DISEASE_AMOUNT for e in _effects(row)):
            bad.append(f"{sid}: no effect with misc {MISC_DISEASE_AMOUNT} (core switch SpellAuras.cpp:1534-1592 logs an error)")
    row = rows_by_id.get(CRYPT_FEVER_DEBUFF)
    if row is not None and not _u32(row.get("AttributesEx3")) & ATTR3_DOT_STACKING_RULE:
        bad.append(f"{CRYPT_FEVER_DEBUFF}: AttributesEx3 {_u32(row.get('AttributesEx3')):#x} lacks DOT_STACKING_RULE 0x80")
    return bad


def check_impurity(rows_by_id: dict[int, dict], druid_text: str) -> list[str]:
    bad = []
    for sid, row in _present(rows_by_id, *IMPURITY_RANKS):
        if _i(row, "SpellClassSet") != 15:
            bad.append(f"{sid}: SpellClassSet {row.get('SpellClassSet')!r}, expected 15")
        if not any(e["aura"] == AURA_DUMMY for e in _effects(row)):
            bad.append(f"{sid}: no APPLY_AURA DUMMY (4) effect")
        if _i(row, "SpellIconID") != ICON_IMPURITY:
            bad.append(f"{sid}: SpellIconID {row.get('SpellIconID')!r}, expected {ICON_IMPURITY}")
    for sid in IMPURITY_RANKS:
        if re.search(rf"\b{sid}\b", druid_text):
            bad.append(f"{sid}: still declared in druid_trigger_spells.py")
    return bad


def check_desolation_buffs(rows_by_id: dict[int, dict]) -> list[str]:
    return [f"{sid}: SpellIconID {row.get('SpellIconID')!r}, expected {ICON_DESOLATION}"
            for sid, row in _present(rows_by_id, *DESOLATION_BUFFS) if _i(row, "SpellIconID") != ICON_DESOLATION]


def check_night_of_the_dead(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for sid, (_, holder) in zip(NIGHT_OF_THE_DEAD, ((55620, 44), (55623, 89))):
        row = rows_by_id.get(sid)
        if row is None:
            continue
        if _i(row, "SpellIconID") != ICON_NIGHT_OF_THE_DEAD:
            bad.append(f"{sid}: SpellIconID {row.get('SpellIconID')!r}, expected {ICON_NIGHT_OF_THE_DEAD}")
        if _i(row, "EffectAura_1") != AURA_ADD_FLAT:
            bad.append(f"{sid}: effect 0 aura {row.get('EffectAura_1')!r}, expected ADD_FLAT_MODIFIER (107)")
        if _i(row, "EffectMiscValue_1") != SPELLMOD_DURATION:
            bad.append(f"{sid}: effect 0 misc {row.get('EffectMiscValue_1')!r}, expected SPELLMOD_DURATION (1)")
        if _effect_mask(row, 1)[2] & D2_B14 == 0:
            bad.append(f"{sid}: effect 0 mask {_hex(_effect_mask(row, 1))} lacks d2 b14 (Lesser Ghoul)")
        if _i(row, "EffectBasePoints_3") != holder or _i(row, "EffectDieSides_3") != 1:
            bad.append(f"{sid}: effect 2 holder bp/die {row.get('EffectBasePoints_3')!r}/{row.get('EffectDieSides_3')!r}, "
                       f"expected {holder}/1 (read by Pet.cpp / pet_dk.cpp)")
    return bad


def check_gargoyle_and_corpse_explosion(rows_by_id: dict[int, dict], entries: dict[int, dict]) -> list[str]:
    bad = []
    row = rows_by_id.get(GARGOYLE_STRIKE)
    if row is not None and _i(row, "CastingTimeIndex") != GARGOYLE_STRIKE_CAST_INDEX:
        bad.append(f"{GARGOYLE_STRIKE}: CastingTimeIndex {row.get('CastingTimeIndex')!r}, expected {GARGOYLE_STRIKE_CAST_INDEX}")
    row = rows_by_id.get(SUMMON_GARGOYLE)
    if row is not None:
        if _i(row, "ManaCost") or _i(row, "RuneCostID"):
            bad.append(f"{SUMMON_GARGOYLE}: ManaCost {row.get('ManaCost')!r} / RuneCostID {row.get('RuneCostID')!r}, expected 0")
        if _i(row, "RecoveryTime") != GARGOYLE_COOLDOWN_MS:
            bad.append(f"{SUMMON_GARGOYLE}: RecoveryTime {row.get('RecoveryTime')!r}, expected {GARGOYLE_COOLDOWN_MS}")
        entry = entries.get(SUMMON_GARGOYLE)
        if entry is not None and entry.get("duration_ms") != GARGOYLE_DURATION_MS:
            bad.append(f"{SUMMON_GARGOYLE}: duration_ms {entry.get('duration_ms')!r}, expected {GARGOYLE_DURATION_MS}")
    row = rows_by_id.get(CORPSE_EXPLOSION)
    if row is not None:
        if (_i(row, "PowerType"), _i(row, "ManaCost")) != CORPSE_EXPLOSION_COST:
            bad.append(f"{CORPSE_EXPLOSION}: PowerType/ManaCost {(row.get('PowerType'), row.get('ManaCost'))!r}, "
                       f"expected {CORPSE_EXPLOSION_COST} (30 RP shown, 300 internal)")
        if _i(row, "RecoveryTime") or _i(row, "CategoryRecoveryTime"):
            bad.append(f"{CORPSE_EXPLOSION}: cooldown {row.get('RecoveryTime')!r}/{row.get('CategoryRecoveryTime')!r}, expected 0")
    return bad


def check_harbinger_buff(rows_by_id: dict[int, dict], procs: list[dict]) -> list[str]:
    row = rows_by_id.get(HARBINGER_BUFF)
    bad = []
    if row is not None:
        eff = next(iter(_effects(row)), None)
        if eff is None or eff["aura"] not in (AURA_ADD_FLAT, AURA_ADD_PCT) or eff["misc"] != SPELLMOD_COST:
            bad.append(f"{HARBINGER_BUFF}: effect 0 {eff!r}, expected a SPELLMOD_COST (14) modifier")
        elif eff["bp"] + 1 != -100 and eff["bp"] != -100:
            bad.append(f"{HARBINGER_BUFF}: effect 0 value {eff['bp']}, expected -100%")
        if _i(row, "ProcCharges") != 1:
            bad.append(f"{HARBINGER_BUFF}: ProcCharges {row.get('ProcCharges')!r}, expected 1 (charged)")
        if not _effect_mask(row, 1)[0] & m.DEATH_COIL:
            bad.append(f"{HARBINGER_BUFF}: effect 0 mask {_hex(_effect_mask(row, 1))} lacks d0 b13 (Death Coil)")
    if any(abs(int(p["SpellId"])) == HARBINGER_BUFF for p in procs):
        bad.append(f"{HARBINGER_BUFF}: spell_proc row declared (RemoveSpellMods skips mods with a proc entry)")
    return bad


def check_proc_phases(procs: list[dict]) -> list[str]:
    bad = []
    for p in procs:
        sid = abs(int(p["SpellId"]))
        if sid not in S3_IDS:
            continue
        phase = int(p["SpellPhaseMask"])
        if sid in CAST_PHASE:
            if phase != PHASE_CAST:
                bad.append(f"{p['SpellId']}: CAST-phase talent row has SpellPhaseMask {p['SpellPhaseMask']!r}, expected 1")
        elif sid in AUTO_ATTACK_PHASE:
            if phase != PHASE_NONE:
                bad.append(f"{p['SpellId']}: auto-attack row has SpellPhaseMask {p['SpellPhaseMask']!r}, expected 0")
        elif int(p["ProcFlags"]) & PROC_DONE_SPELL_CLASS_AND_PERIODIC \
                and not int(p.get("AttributesMask") or 0) & PROC_ATTR_REQ_SPELLMOD and phase != PHASE_HIT:
            bad.append(f"{p['SpellId']}: DONE spell-class / periodic proc row has SpellPhaseMask "
                       f"{p['SpellPhaseMask']!r}, expected 2")
    return bad


def check_no_cost_cooldown_tooltips(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for sid, row in _present(rows_by_id, *sorted(S3_IDS - HIDDEN_HELPERS)):
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
    for sid, e in by_id.items():
        if sid < 1254:
            continue
        for name in SDV_NAME.findall(str(e.get("Variables") or "")):
            if len(name) > MAX_SDV_NAME:
                bad.append(f"SpellDescriptionVariables {sid}: name {name!r} is {len(name)} chars, max {MAX_SDV_NAME}")
    return bad


def check_cloud(rows_by_id: dict[int, dict], entries: dict[int, dict]) -> list[str]:
    bad = []
    entry = entries.get(CLOUD_TICK)
    if entry is not None:
        ts = [float(((entry.get(s) or {}).get("_potency") or {}).get("t_seconds", -1)) for s in
              ("effect1", "effect2", "effect3") if (entry.get(s) or {}).get("_potency")]
        if not ts:
            bad.append(f"{CLOUD_TICK}: no potency effect declared")
        elif any(abs(t - 1.0) > 1e-6 for t in ts):
            bad.append(f"{CLOUD_TICK}: time basis {ts}s, expected 1s (time_basis_ms=1000)")
    row = rows_by_id.get(CLOUD)
    if row is not None and not any(_i(row, f"EffectAuraPeriod_{n}") == 1000 for n in (1, 2, 3)):
        bad.append(f"{CLOUD}: no effect with a 1000 ms period")
    return bad


# ---- real data ------------------------------------------------------------------------------------------------

class DeathKnightS3DataTest(unittest.TestCase):
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

    def test_tab_skill_line(self):
        self.assertClean(check_tab_skill_line(TALENTS_FILE.read_text(encoding="utf-8")))

    def test_castable_skill_lines(self):
        self.assertClean(check_skill_lines(self._pkg().skill_line_abilities))

    def test_scourge_strike(self):
        self.assertClean(check_scourge_strike(self._rows(), self._pkg().spell_rune_costs))

    def test_wound_debuff(self):
        self.assertClean(check_wound_debuff(self._rows(), self._pkg().linked_spells))

    def test_wound_damage(self):
        self.assertClean(check_wound_damage(self._rows(), self._entries()))

    def test_oph_damage(self):
        self.assertClean(check_oph_damage(self._rows(), self._entries()))

    def test_lesser_ghoul_summon(self):
        self.assertClean(check_lesser_ghoul_summon(self._rows(), self._entries()))

    def test_d2_carriers(self):
        self.assertClean(check_d2_carriers(self._rows()))

    def test_no_forbidden_bits(self):
        self.assertClean(check_forbidden_bits(self._rows(), state.load_stock_rows(dbcfmt.SPELL)))

    def test_runic_focus_and_razorice(self):
        self.assertClean(check_runic_focus_and_razorice(self._rows()))

    def test_ror_ranks(self):
        self.assertClean(check_ror_ranks(self._rows()))

    def test_disease_amount_ranks(self):
        self.assertClean(check_disease_amount_ranks(self._rows()))

    def test_impurity(self):
        self.assertClean(check_impurity(self._rows(), DRUID_FILE.read_text(encoding="utf-8")))

    def test_desolation_buffs(self):
        self.assertClean(check_desolation_buffs(self._rows()))

    def test_night_of_the_dead(self):
        self.assertClean(check_night_of_the_dead(self._rows()))

    def test_gargoyle_and_corpse_explosion(self):
        self.assertClean(check_gargoyle_and_corpse_explosion(self._rows(), self._entries()))

    def test_harbinger_buff(self):
        self.assertClean(check_harbinger_buff(self._rows(), self._pkg().spell_procs))

    def test_proc_phases(self):
        self.assertClean(check_proc_phases(self._pkg().spell_procs))

    def test_no_cost_or_cooldown_tooltips(self):
        self.assertClean(check_no_cost_cooldown_tooltips(self._rows()))

    def test_sdv_names(self):
        self.assertClean(check_sdv(self._pkg().tooltip_vars))

    def test_cloud(self):
        self.assertClean(check_cloud(self._rows(), self._entries()))


# ---- negative fixtures: every check must fire on a minimal bad input --------------------------------------------

def _row(spell_id=1, **cols) -> dict:
    return {"ID": spell_id, **cols}


def _proc(sid, flags=0x10, phase=PHASE_HIT, **cols) -> dict:
    return {"SpellId": sid, "ProcFlags": flags, "SpellPhaseMask": phase, **cols}


def _good_grid() -> list[dict]:
    return [{"id": tid, "tab_id": UNHOLY_TAB, "tier": tier, "column": col, "rank_spell_ids": list(ranks),
             "depends_on": dict(PREREQS[tid]) if tid in PREREQS else None} for tid, (tier, col, ranks) in GRID.items()]


def _entry(sid, totals, t=1.0, **cols) -> dict:
    entry = {"id": sid, **cols}
    for i, total in enumerate(totals, start=1):
        entry[f"effect{i}"] = {"type": 2, "_potency": {"total_potency": total, "t_seconds": t, "kind": "direct"}}
    return entry


class DeathKnightS3NegativeTest(unittest.TestCase):
    def test_sanity_of_constants(self):
        self.assertEqual(len(GRID), GRID_TALENTS)
        self.assertEqual(sum(len(r) for _, _, r in GRID.values()), GRID_POINTS)
        self.assertEqual(len({(t, c) for t, c, _ in GRID.values()}), GRID_TALENTS)
        self.assertEqual(len({s for _, _, r in GRID.values() for s in r}), GRID_POINTS)

    def test_required_ids(self):
        self.assertEqual(check_required_ids({i: {} for i in REQUIRED_IDS}), [])
        self.assertEqual(len(check_required_ids({i: {} for i in REQUIRED_IDS if i != 203472})), 1)

    def test_grid(self):
        good = _good_grid()
        self.assertEqual(check_grid(good), [])
        moved = [dict(t) for t in good]
        moved[0]["tier"] = 9
        self.assertGreaterEqual(len(check_grid(moved)), 1)
        self.assertGreaterEqual(len(check_grid(good[1:])), 3)
        idx = {t["id"]: i for i, t in enumerate(good)}
        nodep = [dict(t) for t in good]
        nodep[idx[2043]]["depends_on"] = None
        self.assertEqual(len(check_grid(nodep)), 1)
        mog = [dict(t) for t in good]
        mog[idx[1984]]["depends_on"] = {"talent_id": 2225, "rank": 1}  # the stock prereq that must be cleared
        self.assertEqual(len(check_grid(mog)), 1)
        five = [dict(t) for t in good]
        five[idx[2218]]["rank_spell_ids"] = [55129, 55130, 55131, 55132, 55133]
        self.assertGreaterEqual(len(check_grid(five)), 2)
        wrong_tab = [dict(t) for t in good]
        wrong_tab[0]["tab_id"] = 399
        self.assertGreaterEqual(len(check_grid(wrong_tab)), 2)
        extra = good + [{"id": 9999, "tab_id": UNHOLY_TAB, "tier": 8, "column": 2, "rank_spell_ids": [1], "depends_on": None}]
        self.assertGreaterEqual(len(check_grid(extra)), 1)
        clash = [dict(t) for t in good]
        clash[idx[60371]]["column"] = 0
        self.assertGreaterEqual(len(check_grid(clash)), 1)

    def test_tab_skill_line(self):
        good = "unholy_400_tab = tab(\n    id=400,\n    skill_line=772,  # S3a\n    raw_overrides={},\n)\n"
        self.assertEqual(check_tab_skill_line(good), [])
        self.assertEqual(len(check_tab_skill_line(good.replace("772", "770"))), 1)
        self.assertEqual(len(check_tab_skill_line(good.replace("    skill_line=772,  # S3a\n", ""))), 1)
        self.assertEqual(len(check_tab_skill_line("")), 1)

    def test_skill_lines(self):
        good = [{"id": 30760, "spell_id": 203448, "skill_line": 772, "class_mask": 32, "acquire_method": 0},
                {"id": 30761, "spell_id": 203452, "skill_line": 772, "class_mask": 32, "acquire_method": 0}]
        self.assertEqual(check_skill_lines(good), [])
        self.assertEqual(len(check_skill_lines(good[:1])), 1)
        self.assertEqual(len(check_skill_lines([{**good[0], "skill_line": 771}, good[1]])), 1)
        self.assertEqual(len(check_skill_lines([{**good[0], "id": 30762}, good[1]])), 1)

    def test_scourge_strike(self):
        row = _row(SCOURGE_STRIKE_ID, Effect_1=31, Effect_2=121, EffectBasePoints_2=-1, RuneCostID=2602, SpellLevel=15,
                   SpellClassMask_2=m.SCOURGE_STRIKE)
        costs = [{"ID": 2602, "Blood": 1, "Unholy": 0, "Frost": 1, "RunicPower": 150}]
        self.assertEqual(check_scourge_strike({SCOURGE_STRIKE_ID: row}, costs), [])
        self.assertEqual(len(check_scourge_strike({SCOURGE_STRIKE_ID: {**row, "Effect_1": 121, "Effect_2": 31}}, costs)), 2)
        self.assertEqual(len(check_scourge_strike({SCOURGE_STRIKE_ID: {**row, "EffectBasePoints_2": 417}}, costs)), 1)
        self.assertEqual(len(check_scourge_strike({SCOURGE_STRIKE_ID: {**row, "RuneCostID": 1145}}, costs)), 1)
        self.assertEqual(len(check_scourge_strike({SCOURGE_STRIKE_ID: row}, [{**costs[0], "Unholy": 1}])), 1)
        self.assertEqual(len(check_scourge_strike({SCOURGE_STRIKE_ID: row}, [])), 1)
        self.assertEqual(len(check_scourge_strike({SCOURGE_STRIKE_ID: {**row, "SpellLevel": 55}}, costs)), 1)
        self.assertEqual(len(check_scourge_strike({SCOURGE_STRIKE_ID: {**row, "SpellClassMask_2": 0}}, costs)), 1)

    def test_wound_debuff(self):
        row = _row(WOUND, CumulativeAura=10, AttributesEx3=0x80, Effect_1=6, EffectAura_1=4)
        self.assertEqual(check_wound_debuff({WOUND: row}, []), [])
        self.assertEqual(len(check_wound_debuff({WOUND: {**row, "CumulativeAura": 5}}, [])), 1)
        self.assertEqual(len(check_wound_debuff({WOUND: {**row, "AttributesEx3": 0}}, [])), 1)
        self.assertEqual(len(check_wound_debuff({WOUND: {**row, "DispelType": 1}}, [])), 1)
        self.assertEqual(len(check_wound_debuff({WOUND: {**row, "EffectAura_1": 3}}, [])), 1)
        self.assertEqual(len(check_wound_debuff({WOUND: {**row, "EffectAuraPeriod_1": 3000}}, [])), 1)
        self.assertEqual(len(check_wound_debuff({WOUND: row}, [{"spell_trigger": 203448, "spell_effect": WOUND}])), 1)
        self.assertEqual(len(check_wound_debuff({WOUND: {**row, "SpellClassMask_3": D2_B11}}, [])), 1)

    def test_wound_damage(self):
        rows = {sid: _row(sid, SpellClassMask_3=D2_B11, Mechanic=22, SpellLevel=20) for sid in WOUND_DAMAGE}
        entries = {sid: _entry(sid, [p]) for sid, p in WOUND_DAMAGE.items()}
        self.assertEqual(check_wound_damage(rows, entries), [])
        for col, val in (("SpellClassMask_3", 0), ("Mechanic", 0), ("SpellLevel", 25)):
            bad = {**rows, WOUND_BURST: {**rows[WOUND_BURST], col: val}}
            self.assertEqual(len(check_wound_damage(bad, entries)), 1, col)
        self.assertEqual(len(check_wound_damage(rows, {**entries, WOUND_EXPLOSION: _entry(WOUND_EXPLOSION, [30.0])})), 1)

    def test_oph_damage(self):
        row = _row(OPH_DAMAGE, SpellClassMask_3=D2_B17, SpellLevel=25)
        entries = {OPH_DAMAGE: _entry(OPH_DAMAGE, [40.0])}
        self.assertEqual(check_oph_damage({OPH_DAMAGE: row}, entries), [])
        self.assertEqual(len(check_oph_damage({OPH_DAMAGE: {**row, "SpellClassMask_3": D2_B11}}, entries)), 1)
        self.assertEqual(len(check_oph_damage({OPH_DAMAGE: {**row, "SpellLevel": 20}}, entries)), 1)
        self.assertEqual(len(check_oph_damage({OPH_DAMAGE: row}, {OPH_DAMAGE: _entry(OPH_DAMAGE, [25.0])})), 1)

    def test_lesser_ghoul_summon(self):
        row = _row(LESSER_GHOUL_SUMMON, SpellClassMask_3=D2_B14, Effect_1=28, EffectMiscValueB_1=61, DurationIndex=5)
        entries = {LESSER_GHOUL_SUMMON: {"id": LESSER_GHOUL_SUMMON, "duration_ms": 15000}}
        self.assertEqual(check_lesser_ghoul_summon({LESSER_GHOUL_SUMMON: row}, entries), [])
        self.assertEqual(len(check_lesser_ghoul_summon({LESSER_GHOUL_SUMMON: {**row, "SpellClassMask_3": 0}}, entries)), 1)
        self.assertEqual(len(check_lesser_ghoul_summon({LESSER_GHOUL_SUMMON: {**row, "EffectMiscValueB_1": 64}}, entries)), 1)
        self.assertEqual(len(check_lesser_ghoul_summon({LESSER_GHOUL_SUMMON: {**row, "Effect_1": 3}}, entries)), 1)
        self.assertEqual(len(check_lesser_ghoul_summon({LESSER_GHOUL_SUMMON: {**row, "DurationIndex": 0}},
                                                       {LESSER_GHOUL_SUMMON: {"duration_ms": 0}})), 2)

    def test_d2_carriers(self):
        def good():
            rows = {sid: _row(sid, SpellClassMask_3=D2_B11) for sid in B11_OWN}
            rows[203469] = _row(203469, SpellClassMask_3=D2_B14)
            rows[203477] = _row(203477, SpellClassMask_3=D2_B17)
            rows[RUNIC_FOCUS] = _row(RUNIC_FOCUS, EffectSpellClassMaskA_3=D2_B11 | D2_B17)
            for sid in NIGHT_OF_THE_DEAD:
                rows[sid] = _row(sid, EffectSpellClassMaskA_3=D2_B14)
            return rows
        self.assertEqual(check_d2_carriers(good()), [])
        rows = good()
        rows[203459]["SpellClassMask_3"] = 0
        self.assertEqual(len(check_d2_carriers(rows)), 1)
        rows = good()
        rows[203470] = _row(203470, SpellClassMask_3=D2_B14)  # a counter on the Lesser Ghoul bit
        self.assertEqual(len(check_d2_carriers(rows)), 1)
        rows = good()
        rows[203460] = _row(203460, SpellClassMask_3=D2_B17)
        self.assertEqual(len(check_d2_carriers(rows)), 1)
        rows = good()
        rows[203471] = _row(203471, SpellClassMask_3=D2_B11)  # the detonation has no bit
        self.assertEqual(len(check_d2_carriers(rows)), 1)
        rows = good()
        rows[RUNIC_FOCUS]["EffectSpellClassMaskA_3"] = D2_B11
        self.assertEqual(len(check_d2_carriers(rows)), 1)
        rows = good()
        del rows[BOILING_BLIGHT_BURST]["SpellClassMask_3"]
        self.assertEqual(len(check_d2_carriers(rows)), 1)

    def test_forbidden_bits(self):
        rows = {203472: _row(203472, SpellClassMask_3=0x4000)}
        self.assertEqual(check_forbidden_bits(rows, {}), [])
        for col, bit in (("SpellClassMask_1", m.FORBIDDEN_D0_B6), ("SpellClassMask_2", m.FORBIDDEN_D1_B11),
                         ("SpellClassMask_3", m.FORBIDDEN_D2_B1), ("SpellClassMask_3", m.FORBIDDEN_D2_B31)):
            self.assertEqual(len(check_forbidden_bits({203472: _row(203472, **{col: bit})}, {})), 1, col)
        self.assertEqual(len(check_forbidden_bits({203472: _row(203472, EffectSpellClassMaskB_2=m.FORBIDDEN_D1_B10)}, {})), 1)
        edited = {55090: _row(55090, SpellClassMask_1=m.FORBIDDEN_D0_B17)}
        self.assertEqual(len(check_forbidden_bits(edited, {55090: _row(55090)})), 1)
        self.assertEqual(check_forbidden_bits(edited, {55090: _row(55090, SpellClassMask_1=m.FORBIDDEN_D0_B17)}), [])

    def test_runic_focus_and_razorice(self):
        rows = {RUNIC_FOCUS: _row(RUNIC_FOCUS, EffectSpellClassMaskA_3=D2_B17),
                RAZORICE: _row(RAZORICE, EffectSpellClassMaskA_1=m.FROST_VULN_READ_S2[0],
                               EffectSpellClassMaskA_2=m.FROST_VULN_READ_S2[1], EffectSpellClassMaskA_3=m.FROST_VULN_READ_S2[2])}
        self.assertEqual(check_runic_focus_and_razorice(rows), [])
        self.assertEqual(len(check_runic_focus_and_razorice({**rows, RUNIC_FOCUS: _row(RUNIC_FOCUS)})), 1)
        widened = {**rows, RAZORICE: {**rows[RAZORICE], "EffectSpellClassMaskA_3": m.FROST_VULN_READ_S2[2] | D2_B17}}
        self.assertEqual(len(check_runic_focus_and_razorice(widened)), 1)

    def test_ror_ranks(self):
        rows = {sid: _row(sid, Effect_1=6, EffectAura_1=4, EffectMiscValue_1=0) for sid in ROR_RANKS}
        self.assertEqual(check_ror_ranks(rows), [])
        self.assertEqual(len(check_ror_ranks({**rows, 50117: {**rows[50117], "EffectMiscValue_1": 7293}})), 1)
        self.assertEqual(len(check_ror_ranks({**rows, 50118: {**rows[50118], "EffectAura_1": 240}})), 1)

    def test_disease_amount_ranks(self):
        rows = {sid: _row(sid, Effect_1=6, EffectAura_1=112, EffectMiscValue_1=7282)
                for sid in (*CRYPT_FEVER_RANKS, *EBON_PLAGUE_RANKS)}
        rows[CRYPT_FEVER_DEBUFF] = _row(CRYPT_FEVER_DEBUFF, AttributesEx3=0x80)
        self.assertEqual(check_disease_amount_ranks(rows), [])
        self.assertEqual(len(check_disease_amount_ranks({**rows, 49631: {**rows[49631], "EffectMiscValue_1": 0}})), 1)
        self.assertEqual(len(check_disease_amount_ranks({**rows, CRYPT_FEVER_DEBUFF: _row(CRYPT_FEVER_DEBUFF)})), 1)

    def test_impurity(self):
        rows = {sid: _row(sid, SpellClassSet=15, Effect_1=6, EffectAura_1=4, SpellIconID=1986) for sid in IMPURITY_RANKS}
        self.assertEqual(check_impurity(rows, "other_spell = 12345"), [])
        self.assertEqual(len(check_impurity({**rows, 49633: {**rows[49633], "SpellClassSet": 7}}, "")), 1)
        self.assertEqual(len(check_impurity({**rows, 49633: {**rows[49633], "EffectAura_1": 226}}, "")), 1)
        self.assertEqual(len(check_impurity({**rows, 49633: {**rows[49633], "SpellIconID": 196}}, "")), 1)
        self.assertEqual(len(check_impurity(rows, "x = spell(id=49220)")), 1)
        self.assertEqual(check_impurity(rows, "x = spell(id=492201)"), [])  # whole-number match only

    def test_desolation_buffs(self):
        rows = {sid: _row(sid, SpellIconID=235) for sid in DESOLATION_BUFFS}
        self.assertEqual(check_desolation_buffs(rows), [])
        self.assertEqual(len(check_desolation_buffs({**rows, 66800: _row(66800, SpellIconID=1)})), 1)

    def test_night_of_the_dead(self):
        def good(sid, holder):
            return _row(sid, SpellIconID=2718, EffectAura_1=107, EffectMiscValue_1=1, EffectSpellClassMaskA_3=D2_B14,
                        EffectBasePoints_3=holder, EffectDieSides_3=1)
        rows = {55620: good(55620, 44), 55623: good(55623, 89)}
        self.assertEqual(check_night_of_the_dead(rows), [])
        for col, val in (("SpellIconID", 22), ("EffectAura_1", 108), ("EffectMiscValue_1", 0),
                         ("EffectSpellClassMaskA_3", 0), ("EffectBasePoints_3", 0), ("EffectDieSides_3", 0)):
            self.assertEqual(len(check_night_of_the_dead({**rows, 55623: {**rows[55623], col: val}})), 1, col)

    def test_gargoyle_and_corpse_explosion(self):
        rows = {GARGOYLE_STRIKE: _row(GARGOYLE_STRIKE, CastingTimeIndex=130),
                SUMMON_GARGOYLE: _row(SUMMON_GARGOYLE, RecoveryTime=120000),
                CORPSE_EXPLOSION: _row(CORPSE_EXPLOSION, PowerType=6, ManaCost=300)}
        entries = {SUMMON_GARGOYLE: {"duration_ms": 26000}}
        self.assertEqual(check_gargoyle_and_corpse_explosion(rows, entries), [])
        bads = (
            {GARGOYLE_STRIKE: _row(GARGOYLE_STRIKE, CastingTimeIndex=1)},
            {SUMMON_GARGOYLE: _row(SUMMON_GARGOYLE, RecoveryTime=180000)},
            {SUMMON_GARGOYLE: _row(SUMMON_GARGOYLE, RecoveryTime=120000, ManaCost=600)},
            {CORPSE_EXPLOSION: _row(CORPSE_EXPLOSION, PowerType=6, ManaCost=400)},
            {CORPSE_EXPLOSION: _row(CORPSE_EXPLOSION, PowerType=6, ManaCost=300, RecoveryTime=5000)},
        )
        for bad in bads:
            self.assertEqual(len(check_gargoyle_and_corpse_explosion({**rows, **bad}, entries)), 1, bad)
        self.assertEqual(len(check_gargoyle_and_corpse_explosion(rows, {SUMMON_GARGOYLE: {"duration_ms": 30000}})), 1)

    def test_harbinger_buff(self):
        row = _row(HARBINGER_BUFF, Effect_1=6, EffectAura_1=108, EffectMiscValue_1=14, EffectBasePoints_1=-101,
                   ProcCharges=1, EffectSpellClassMaskA_1=m.DEATH_COIL)
        self.assertEqual(check_harbinger_buff({HARBINGER_BUFF: row}, []), [])
        for col, val in (("EffectMiscValue_1", 7), ("EffectAura_1", 4), ("EffectBasePoints_1", -51), ("ProcCharges", 0),
                         ("EffectSpellClassMaskA_1", 0)):
            self.assertEqual(len(check_harbinger_buff({HARBINGER_BUFF: {**row, col: val}}, [])), 1, col)
        self.assertEqual(len(check_harbinger_buff({HARBINGER_BUFF: row}, [_proc(HARBINGER_BUFF)])), 1)
        self.assertEqual(len(check_harbinger_buff({HARBINGER_BUFF: row}, [_proc(-HARBINGER_BUFF)])), 1)

    def test_proc_phases(self):
        self.assertEqual(check_proc_phases([_proc(-203445, 0x10, PHASE_CAST), _proc(203453, 0x4, PHASE_NONE),
                                            _proc(203467, 0x10, PHASE_HIT), _proc(1, 0x10, PHASE_NONE)]), [])
        self.assertEqual(len(check_proc_phases([_proc(-203449, 0x10, PHASE_HIT)])), 1)
        self.assertEqual(len(check_proc_phases([_proc(203453, 0x4, PHASE_HIT)])), 1)
        self.assertEqual(len(check_proc_phases([_proc(203467, 0x10, PHASE_NONE)])), 1)
        self.assertEqual(len(check_proc_phases([_proc(203447, 0x10, PHASE_NONE)])), 1)

    def test_no_cost_cooldown_tooltips(self):
        ok = {203448: _row(203448, Description_Lang_enUS="Transforms your ghoul for 15 sec.")}
        self.assertEqual(check_no_cost_cooldown_tooltips(ok), [])
        cool = {203448: _row(203448, Description_Lang_enUS="Transforms your ghoul. 2 min cooldown.")}
        self.assertEqual(len(check_no_cost_cooldown_tooltips(cool)), 1)
        cost = {203452: _row(203452, Description_Lang_enUS="Raises an Abomination. Costs 30 Runic Power.")}
        self.assertEqual(len(check_no_cost_cooldown_tooltips(cost)), 1)
        aura = {203461: _row(203461, AuraDescription_Lang_enUS="Increases damage. 1 sec cooldown.")}
        self.assertEqual(len(check_no_cost_cooldown_tooltips(aura)), 1)
        hidden = {203460: _row(203460, Description_Lang_enUS="Energizes. Costs 10 Runic Power.")}
        self.assertEqual(check_no_cost_cooldown_tooltips(hidden), [])

    def test_sdv(self):
        ok = [{"id": i, "Variables": "$ssdmg=5"} for i in SDV_IDS]
        self.assertEqual(check_sdv(ok), [])
        self.assertEqual(len(check_sdv(ok[:2])), 1)
        self.assertEqual(len(check_sdv([{"id": 1254, "Variables": "$abcdefghijklm=5"}, *ok[1:]])), 1)  # 13 chars
        self.assertEqual(len(check_sdv([*ok, {"id": 1282, "Variables": "$abcdefghijklm=5"}])), 1)
        self.assertEqual(check_sdv([*ok, {"id": 1100, "Variables": "$abcdefghijklmnop=5"}]), [])  # not ours

    def test_cloud(self):
        entries = {CLOUD_TICK: _entry(CLOUD_TICK, [12.0], t=1.0)}
        rows = {CLOUD: _row(CLOUD, EffectAuraPeriod_1=1000)}
        self.assertEqual(check_cloud(rows, entries), [])
        self.assertEqual(len(check_cloud(rows, {CLOUD_TICK: _entry(CLOUD_TICK, [12.0], t=1.5)})), 1)
        self.assertEqual(len(check_cloud(rows, {CLOUD_TICK: {"id": CLOUD_TICK}})), 1)
        self.assertEqual(len(check_cloud({CLOUD: _row(CLOUD, EffectAuraPeriod_1=3000)}, entries)), 1)


if __name__ == "__main__":
    unittest.main()
