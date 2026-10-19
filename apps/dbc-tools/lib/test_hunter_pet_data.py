"""
Hunter H0-P1 pet data gates (hunter-rework PET.md 4.4, 4.6, 4.8, 7.1; H0-P1-HANDOFF WP-A4 (2)).

Loads the real hunter DSL package (source/classes/hunter/, `regen_hunter_header.py`'s kwargs, the loader of
`test_hunter_spellmod_family.py`) and asserts on the BUILT rows (stock base + DSL + raw_overrides, via
`build.build_spell_row`), so a stale raw twin that wins fails here too:

  (a) retirement resolution (lesson L8, which generate.py only does on a full run): every `retire_pet_spell`
      matched a stock pet row or a CreatureSpellData record; the AcquireMethod-0 SkillLineAbility ids equal PET 4.6's
      46 rows; every "record also named by another family" warning is printed (reported, not failed);
  (b) `EquippedItemClass == -1` on every P1 id (8 new, 12 pulled, 19596, 8 in-place);
  (c) no `sp_potency` effect on a d1 b28 spell, except 59881 / 50518 / 50271 (PET 4.8);
  (d) Furious Howl 24604: one effect, no points_per_level, MaxLevel 0, aura 52, bp 4;
  (e) d2 b23 (0x800000) is carried by exactly {17253, 16827, 49966, 201710, 201711}; no reader mask holds d1 b28;
  (f) every new pet-cast spell carries d1 b28; the 46 SkillLineAbility rows 30560-30605 are the PET 4.4 table, have
      AcquireMethod 2, and teach spells with SpellLevel >= 1;
  (g) `lint.check_hunter_family_rules` and `lint.check_talent_tab_refs` emit nothing on the loaded package.

Every check is a pure function; the negative-fixture class feeds each one a minimal bad input.

Run directly:

    apps/dbc-tools/.venv/bin/python3 -m pytest apps/dbc-tools/lib/test_hunter_pet_data.py -q -s
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import build, dbcfmt, lint, source, spell_tables, state, superseded_ranks, trainer_state  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.reuse import ReuseContext  # noqa: E402

TOOL_ROOT = Path(__file__).resolve().parents[1]
HUNTER_DIR = TOOL_ROOT / "source" / "classes" / "hunter"

PET_BIT_D1 = 0x10000000          # SpellClassMask_2 (dword 1) bit 28
PET_BASIC_D2 = 0x800000          # SpellClassMask_3 (dword 2) bit 23
SPELLMOD_AURAS = {107, 108}
LETTERS = ("A", "B", "C")

NEW_SPELLS = (201710, 201711, 201715, 201716, 201717, 201718, 201750, 201751)
PET_CAST_NEW = (201710, 201711, 201715, 201716, 201717, 201718)
PULLED_SPELLS = (61689, 61690, 53203, 53204, 53205, 53175, 53176, 53450, 53451, 53186, 53187, 54131)
IN_PLACE_SPELLS = (17253, 16827, 49966, 2649, 61684, 53478, 53490, 24604)
BOARS_SPEED = 19596
P1_SPELLS = NEW_SPELLS + PULLED_SPELLS + (BOARS_SPEED,) + IN_PLACE_SPELLS

SP_POTENCY_KEEP = frozenset({59881, 50518, 50271})     # NPC-used rows keep their stock potency (PET 4.8)
FURIOUS_HOWL = 24604
D2_B23_CARRIERS = frozenset({17253, 16827, 49966, 201710, 201711})

# Readers of d1 b28 that are allowed to stay. Empty: stock Longevity 53262-53264 and Cobra Strikes 53257 were re-masked
# off the pet bit in H0-P1 (Longevity -> Bestial Wrath + Intimidation, Cobra Strikes -> d2 b22, the commanded pet spells
# S1 adds). Keep it empty; a new entry needs a PET/BM decision.
KNOWN_STOCK_PET_BIT_READERS: frozenset[int] = frozenset()

# PET 4.6: the specials' spells (33 spells, 34 SkillLineAbility rows), the 11 Cunning basics, Cower's 270 row.
SPECIAL_SPELLS = frozenset({
    35290, 50519, 50256, 24423, 24450, 59881, 50245, 50433, 26090, 50271, 50541, 50498, 50871, 24640, 4167,
    50285, 26064, 24844, 34889, 50479, 35346, 50518, 35387, 50274, 50318, 54644, 54680, 54706, 55749, 56626,
    57386, 58604, 61193,
})
BASIC_RETIREMENT_SPELLS = frozenset({17253, 16827, 49966})
COWER = 1742
EXPECTED_RETIRED_SPELLS = SPECIAL_SPELLS | BASIC_RETIREMENT_SPELLS | {COWER}
EXPECTED_ZEROED_SLA_IDS = frozenset({
    # specials (34)
    15477, 17469, 17424, 12988, 12916, 20220, 17423, 17454, 13401, 17425, 17485, 17460, 17548, 13041, 17428,
    17427, 13392, 13060, 15283, 17459, 15405, 17468, 15490, 17426, 17447, 19117, 19131, 19224, 19405, 19603,
    19704, 20042, 20466, 20483,
    # Cunning basics replaced by Spit / Venom Spit (11)
    9712, 9640, 9785, 9732, 15426, 15450, 17232, 15438, 15592, 18961, 19225,
    # Cower off skill 270
    13012,
})

# PET 4.4's new SkillLineAbility rows: id range -> (skill lines, spell)
SLA_FIRST, SLA_LAST = 30560, 30605
FEROCITY_LINES = (208, 209, 217, 213, 654, 781, 787, 218, 788, 775, 785)
TENACITY_LINES = (211, 212, 251, 766, 784, 214, 236, 215, 786)
CUNNING_LINES = (653, 655, 656, 763, 767, 765, 764, 768, 780, 783)
SLA_TABLE = (
    ((30560, 30560), (270,), 61684),
    ((30561, 30571), FEROCITY_LINES, COWER),
    ((30572, 30580), TENACITY_LINES, 53478),
    ((30581, 30590), CUNNING_LINES, 53490),
    ((30591, 30600), CUNNING_LINES, 201711),
    ((30601, 30601), (203,), 201710),
    ((30602, 30602), (209,), 201715),
    ((30603, 30603), (217,), 201716),
    ((30604, 30604), (210,), 201717),
    ((30605, 30605), (203,), 201718),
)


def _u32(value) -> int:
    return int(value or 0) & 0xFFFFFFFF


def _effect_mask(row: dict, effect: int) -> tuple[int, int, int]:
    letter = LETTERS[effect - 1]
    return tuple(_u32(row.get(f"EffectSpellClassMask{letter}_{n}")) for n in (1, 2, 3))


# ---- checks (pure: take built rows / entries, return problem strings) ------------------------------------------

def check_retirement_resolution(
    retirements: list[dict], overrides: superseded_ranks.Overrides, strips: dict[int, frozenset[int]],
    strip_warnings: list[str],
) -> list[str]:
    """(a) every retire_pet_spell matched a stock pet SkillLineAbility row or a CreatureSpellData record, and
    nothing the retirement helpers warned about is a defect ('also named by another family' is only reported)."""
    bad = []
    for retirement in retirements:
        spell_id = retirement["spell_id"]
        if spell_id not in overrides.matched and not any(spell_id in spells for spells in strips.values()):
            scope = "every family" if retirement["families"] is None else f"families {list(retirement['families'])}"
            bad.append(f"retire_pet_spell({spell_id}) matches nothing for {scope}: no stock pet SkillLineAbility row "
                       f"and no CreatureSpellData record to strip (wrong spell id or family?)")
    for text in overrides.warnings + overrides.collisions:
        bad.append(f"retired_skilllineability_overrides: {text}")
    for text in strip_warnings:
        if "is also named by creatures of families" not in text:
            bad.append(f"spell_data_strips: {text}")
    return bad


def check_zeroed_sla_ids(entries: list[dict], expected: frozenset[int]) -> list[str]:
    """(a) the AcquireMethod-0 SkillLineAbility ids the retirements produce equal PET 4.6's rows."""
    got = {int(e["id"]) for e in entries if int(build.build_skilllineability_row(e)["AcquireMethod"]) == 0}
    bad = []
    if got - expected:
        bad.append(f"AcquireMethod-0 rows not in PET 4.6: {sorted(got - expected)}")
    if expected - got:
        bad.append(f"PET 4.6 rows no retirement zeroes: {sorted(expected - got)}")
    return bad


def check_retired_spell_set(retirements: list[dict], expected: frozenset[int]) -> list[str]:
    got = {int(r["spell_id"]) for r in retirements}
    bad = []
    if got - expected:
        bad.append(f"retire_pet_spell on spells PET 4.6 does not list: {sorted(got - expected)}")
    if expected - got:
        bad.append(f"PET 4.6 spells with no retire_pet_spell call: {sorted(expected - got)}")
    return bad


def check_equipped_item_class(rows_by_id: dict[int, dict], ids) -> list[str]:
    """(b) EquippedItemClass == -1 on the built row of every id (a missing row is a failure too)."""
    bad = []
    for spell_id in ids:
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared in the hunter package")
        elif int(row.get("EquippedItemClass", 0)) != -1:
            bad.append(f"{spell_id}: built EquippedItemClass {row.get('EquippedItemClass')}, expected -1")
    return bad


def check_no_sp_potency_on_pet_bit(entries: list[dict], rows_by_id: dict[int, dict], bonus_rows: list[dict],
                                   keep: frozenset[int] = SP_POTENCY_KEEP) -> list[str]:
    """(c) no effect with an SP coefficient (sp_potency) on a d1 b28 spell, except the NPC-used ids."""
    bonus_by_id = {int(b["entry"]): b for b in bonus_rows}
    bad = []
    for entry in entries:
        spell_id = entry["id"]
        row = rows_by_id.get(spell_id)
        if row is None or spell_id in keep or not _u32(row.get("SpellClassMask_2")) & PET_BIT_D1:
            continue
        for index in (1, 2, 3):
            potency = (entry.get(f"effect{index}") or {}).get("_potency") or {}
            if potency.get("sp_coefficient"):
                bad.append(f"{spell_id} ({entry.get('name')}): effect {index} still has sp_potency "
                           f"(sp_coefficient {potency['sp_coefficient']}) on a d1 b28 spell")
        bonus = bonus_by_id.get(spell_id)
        if bonus and (bonus.get("direct_bonus") or bonus.get("dot_bonus")):
            bad.append(f"{spell_id} ({entry.get('name')}): spell_bonus_data carries an SP coefficient on a d1 b28 spell")
    return bad


def check_furious_howl(row: dict | None) -> list[str]:
    """(d) 24604: one effect, no points_per_level, MaxLevel 0, aura 52, bp 4."""
    if row is None:
        return [f"{FURIOUS_HOWL}: not declared"]
    bad = []
    if not int(row.get("Effect_1") or 0):
        bad.append("effect 1 is empty")
    for i in (2, 3):
        if int(row.get(f"Effect_{i}") or 0):
            bad.append(f"effect {i} still present (type {row.get(f'Effect_{i}')})")
    if float(row.get("EffectRealPointsPerLevel_1") or 0):
        bad.append(f"EffectRealPointsPerLevel_1 {row.get('EffectRealPointsPerLevel_1')} (CalcValue adds crit per level)")
    if int(row.get("MaxLevel") or 0) != 0:
        bad.append(f"MaxLevel {row.get('MaxLevel')}, expected 0")
    if int(row.get("EffectAura_1") or 0) != 52:
        bad.append(f"EffectAura_1 {row.get('EffectAura_1')}, expected 52 (MOD_WEAPON_CRIT_PERCENT)")
    if int(row.get("EffectBasePoints_1") or 0) != 4:
        bad.append(f"EffectBasePoints_1 {row.get('EffectBasePoints_1')}, expected 4")
    return [f"{FURIOUS_HOWL}: {b}" for b in bad]


def check_d2_b23_carriers(rows: list[dict], expected: frozenset[int] = D2_B23_CARRIERS) -> list[str]:
    """(e) d2 b23 on SpellClassMask is carried by exactly `expected`."""
    got = {int(r["ID"]) for r in rows if _u32(r.get("SpellClassMask_3")) & PET_BASIC_D2}
    bad = []
    if got - expected:
        bad.append(f"d2 b23 carried by unexpected spells: {sorted(got - expected)}")
    if expected - got:
        bad.append(f"d2 b23 missing on: {sorted(expected - got)}")
    return bad


def check_no_pet_bit_in_readers(rows: list[dict], procs: list[dict],
                                known: frozenset[int] = KNOWN_STOCK_PET_BIT_READERS) -> list[str]:
    """(e) no SpellMod aura's EffectSpellClassMask (any id, bar `known`) and no declared spell_proc family mask
    holds d1 b28."""
    bad = []
    for row in rows:
        if int(row["ID"]) in known:
            continue
        for i in (1, 2, 3):
            if int(row.get(f"EffectAura_{i}") or 0) in SPELLMOD_AURAS and _effect_mask(row, i)[1] & PET_BIT_D1:
                bad.append(f"{row['ID']}: SpellMod effect {i} reader mask holds d1 b28")
    for proc in procs:
        if _u32(proc.get("SpellFamilyMask1")) & PET_BIT_D1:
            bad.append(f"spell_proc {proc['SpellId']}: family mask holds d1 b28")
    return bad


def check_pet_cast_carry_pet_bit(rows_by_id: dict[int, dict], ids=PET_CAST_NEW) -> list[str]:
    """(f) every new pet-cast spell carries d1 b28 on its built SpellClassMask."""
    bad = []
    for spell_id in ids:
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
        elif not _u32(row.get("SpellClassMask_2")) & PET_BIT_D1:
            bad.append(f"{spell_id}: SpellClassMask d1 lacks b28 (0x10000000)")
    return bad


def check_sla_rows(sla_rows: list[dict], spell_rows_by_id: dict[int, dict], table=SLA_TABLE) -> list[str]:
    """(f) rows 30560-30605: the PET 4.4 (skill line, spell) table, AcquireMethod 2, taught spell SpellLevel >= 1."""
    bad = []
    in_range = [r for r in sla_rows if SLA_FIRST <= int(r["ID"]) <= SLA_LAST]
    for (first, last), lines, spell in table:
        rows = [r for r in in_range if first <= int(r["ID"]) <= last]
        want = sorted((line, spell) for line in lines)
        got = sorted((int(r["SkillLine"]), int(r["Spell"])) for r in rows)
        if got != want:
            bad.append(f"SkillLineAbility {first}-{last}: (skill line, spell) is {got}, PET 4.4 says {want}")
    declared = {int(r["ID"]) for r in in_range}
    if declared != set(range(SLA_FIRST, SLA_LAST + 1)):
        bad.append(f"SkillLineAbility ids declared in {SLA_FIRST}-{SLA_LAST}: missing "
                   f"{sorted(set(range(SLA_FIRST, SLA_LAST + 1)) - declared)}")
    for row in in_range:
        if int(row.get("AcquireMethod") or 0) != 2:
            bad.append(f"SkillLineAbility {row['ID']}: AcquireMethod {row.get('AcquireMethod')}, expected 2")
        if int(row.get("ClassMask") or 0) != 0:
            bad.append(f"SkillLineAbility {row['ID']}: ClassMask {row.get('ClassMask')}, expected 0")
        spell = spell_rows_by_id.get(int(row["Spell"]))
        if spell is None:
            bad.append(f"SkillLineAbility {row['ID']}: taught spell {row['Spell']} has no spell row")
        elif int(spell.get("SpellLevel") or 0) < 1:
            bad.append(f"SkillLineAbility {row['ID']}: taught spell {row['Spell']} has SpellLevel "
                       f"{spell.get('SpellLevel')} (<1 is never level-up learned, SpellMgr.cpp:2666)")
    return bad


ALSO_NAMED = "is also named by creatures of families"
EXPECTED_SHARED_RECORD_WARNINGS: list[str] = []   # A3-gen: 5953 and 9071 now strip; nothing is left alone

NO_ITEM_CLASS_P2 = (201700, 201703, 201752, 201701, 201702, 201704, 201705, 201706, 201707, 201708, 34026)
MIRRORS = (201700, 201701, 201702)
KITS = (201706, 201707, 201708)
MARKERS = (201703, 201752)
MARKER = 201703    # Hunter Pet Autocast Marker: hidden passive DUMMY, family 0, no script
PASSIVE = 0x40
PET_BASIC_READER = (0, 0, PET_BASIC_D2)


def check_shared_record_warnings(strip_warnings: list[str], expected: list[str]) -> list[str]:
    got = [w for w in strip_warnings if ALSO_NAMED in w]
    if got == expected:
        return []
    return [f"'record also named by another family' warnings differ: unexpected {[w for w in got if w not in expected]}, "
            f"missing {[w for w in expected if w not in got]}"]


def check_passive_permanent(rows_by_id: dict[int, dict], permanent_index: int, ids=MIRRORS + MARKERS + KITS) -> list[str]:
    """Mirrors and kits, on the BUILT row: passive (Attributes & 0x40) and the permanent SpellDuration index
    (`reuse.duration_index(None)`), so a stray raw DurationIndex fails."""
    bad = []
    for spell_id in ids:
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
            continue
        if not int(row.get("Attributes") or 0) & PASSIVE:
            bad.append(f"{spell_id}: Attributes {row.get('Attributes')} lacks passive 0x40")
        if int(row.get("DurationIndex") or 0) != permanent_index:
            bad.append(f"{spell_id}: built DurationIndex {row.get('DurationIndex')}, expected the permanent "
                       f"index {permanent_index}")
    return bad


def check_helpers(rows_by_id: dict[int, dict], strike_range_index: int) -> list[str]:
    """Kill Command helpers, on the BUILT rows: family 0; 201704 RangeIndex 13 with AttributesEx2 IGNORE_LINE_OF_SIGHT
    (0x4) and AttributesEx3 SUPPRESS_CASTER_PROCS (0x10000); 201705 RangeIndex == the index for 50000 yd."""
    bad = []
    for spell_id in (201704, 201705):
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
        elif int(row.get("SpellClassSet") or 0) != 0:
            bad.append(f"{spell_id}: SpellClassSet {row.get('SpellClassSet')}, expected 0 (family 0)")
    tele, strike = rows_by_id.get(201704), rows_by_id.get(201705)
    if tele is not None:
        if int(tele.get("RangeIndex") or 0) != 13:
            bad.append(f"201704: RangeIndex {tele.get('RangeIndex')}, expected 13")
        if not int(tele.get("AttributesEx2") or 0) & 0x4:
            bad.append(f"201704: AttributesEx2 {tele.get('AttributesEx2')} lacks IGNORE_LINE_OF_SIGHT 0x4")
        if not int(tele.get("AttributesEx3") or 0) & 0x10000:
            bad.append(f"201704: AttributesEx3 {tele.get('AttributesEx3')} lacks SUPPRESS_CASTER_PROCS 0x10000")
    if strike is not None and int(strike.get("RangeIndex") or 0) != strike_range_index:
        bad.append(f"201705: built RangeIndex {strike.get('RangeIndex')}, expected {strike_range_index} (50000 yd)")
    return bad


def check_autocast_marker(rows_by_id: dict[int, dict], bound: list[dict], marker: int = MARKER) -> list[str]:
    """201703 / 201752 (`marker`): declared, family 0 with no SpellClassSet and no mask at spell or effect level,
    and no script binding."""
    row = rows_by_id.get(marker)
    if row is None:
        return [f"{marker}: not declared"]
    bad = []
    if int(row.get("SpellClassSet") or 0) != 0:
        bad.append(f"{marker}: SpellClassSet {row.get('SpellClassSet')}, expected 0")
    for n in (1, 2, 3):
        if _u32(row.get(f"SpellClassMask_{n}")):
            bad.append(f"{marker}: SpellClassMask_{n} is not empty")
        for effect in (1, 2, 3):
            if _effect_mask(row, effect)[n - 1]:
                bad.append(f"{marker}: effect {effect} mask dword {n} is not empty")
    if int(row.get("Effect_1") or 0) != 6 or int(row.get("EffectAura_1") or 0) != 4:
        bad.append(f"{marker}: eff0 is not APPLY_AURA DUMMY (Effect_1 {row.get('Effect_1')}, "
                   f"EffectAura_1 {row.get('EffectAura_1')})")
    if int(row.get("EffectBasePoints_1") or 0) != 0:
        bad.append(f"{marker}: eff0 amount {row.get('EffectBasePoints_1')}, expected 0")
    names = sorted(r["ScriptName"] for r in bound if int(r["spell_id"]) == marker)
    if names:
        bad.append(f"{marker}: bound to script(s) {names}, expected none")
    return bad


def check_kit_masks(rows_by_id: dict[int, dict], ids=KITS) -> list[str]:
    """SpellClassSet 9, eff1 and eff2 masks exactly (0, 0, 0x800000), and no SpellClassMask dword 0/1 (spell-level)."""
    bad = []
    for spell_id in ids:
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
            continue
        if int(row.get("SpellClassSet") or 0) != 9:
            bad.append(f"{spell_id}: SpellClassSet {row.get('SpellClassSet')}, expected 9")
        for effect in (1, 2):
            if _effect_mask(row, effect) != PET_BASIC_READER:
                bad.append(f"{spell_id}: effect {effect} mask {_effect_mask(row, effect)}, expected {PET_BASIC_READER}")
        for dword in (1, 2):
            if _u32(row.get(f"SpellClassMask_{dword}")):
                bad.append(f"{spell_id}: spell-level SpellClassMask_{dword} is not empty")
    return bad


def check_kit_values(rows_by_id: dict[int, dict]) -> list[str]:
    want = {201706: (-1, -1), 201707: (5999, 193), 201708: (-1, -1)}
    bad = []
    for spell_id, (cooldown, damage) in want.items():
        row = rows_by_id.get(spell_id)
        if row is None:
            bad.append(f"{spell_id}: not declared")
            continue
        got = (int(row.get("EffectBasePoints_1") or 0), int(row.get("EffectBasePoints_2") or 0))
        if got != (cooldown, damage):
            bad.append(f"{spell_id}: stored base points {got}, expected {(cooldown, damage)}")
    return bad


def check_kill_command_row(row: dict | None) -> list[str]:
    """PET 6.2's built 34026 row."""
    if row is None:
        return ["34026: not declared"]
    want = {"Category": 0, "RecoveryTime": 6000, "StartRecoveryTime": 1500, "StartRecoveryCategory": 133,
            "DefenseType": 3, "AttributesEx": 0, "AttributesEx2": 0, "SpellLevel": 10, "Effect_1": 2, "Effect_2": 3}
    bad = [f"34026: {k} {row.get(k)}, expected {v}" for k, v in want.items() if int(row.get(k) or 0) != v]
    mask = tuple(_u32(row.get(f"SpellClassMask_{n}")) for n in (1, 2, 3))
    if mask != (0, 0x800, 0):
        bad.append(f"34026: SpellClassMask {mask}, expected (0, 0x800, 0)")
    return bad


def check_trainer_rows(trainer_spells: list[dict], spell_id=34026, trainers=(204, 205), req_level=10) -> list[str]:
    got = {int(t["TrainerId"]): int(t["ReqLevel"]) for t in trainer_spells if int(t["SpellId"]) == spell_id}
    want = {t: req_level for t in trainers}
    return [] if got == want else [f"trainer_spell rows for {spell_id}: {got}, expected {want}"]


def check_bindings(bound: list[dict], unbound: list[dict], expected_bound: dict[int, set[str]],
                   expected_unbound: dict[int, set[str]]) -> list[str]:
    """`bound`: spell_script_names rows, `unbound`: script_removals rows. Each expected pair must be present, and
    nothing else is declared for the spells the expectation names (34903/34904 stay untouched)."""
    def group(rows):
        out: dict[int, set[str]] = {}
        for r in rows:
            out.setdefault(int(r["spell_id"]), set()).add(r["ScriptName"])
        return out

    got_bound, got_unbound = group(bound), group(unbound)
    bad = []
    for spell_id, names in expected_bound.items():
        if got_bound.get(spell_id, set()) != names:
            bad.append(f"{spell_id}: bound scripts {sorted(got_bound.get(spell_id, ()))}, expected {sorted(names)}")
    for spell_id, names in expected_unbound.items():
        if got_unbound.get(spell_id, set()) != names:
            bad.append(f"{spell_id}: unbound scripts {sorted(got_unbound.get(spell_id, ()))}, expected {sorted(names)}")
    for spell_id in (34903, 34904):
        if spell_id in got_bound or spell_id in got_unbound:
            bad.append(f"{spell_id}: must stay untouched, but the package binds/unbinds it")
    return bad


EXPECTED_BOUND = {34902: {"spell_hun_pet_scaling_rework"}, 201700: {"spell_hun_pet_passthrough"},
                  201701: {"spell_hun_pet_passthrough"}, 201702: {"spell_hun_pet_passthrough"},
                  34026: {"spell_hun_kill_command_rework", "spell_hun_kill_command_bm"}}
EXPECTED_UNBOUND = {34902: {"spell_hun_generic_scaling"}, 34026: {"spell_hun_kill_command"}}


# ---- real data ------------------------------------------------------------------------------------------------

_CACHE: dict = {}


def package_data() -> dict:
    """Loaded once per process (about two minutes). Shared with test_hunter_inert_keys.py."""
    if not _CACHE:
        ids_cfg = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
        spell_table_index = spell_tables.load_spell_table_index()
        creature_table_index = spell_tables.load_creature_table_index()
        creature_rows = {int(r["entry"]): r for r in creature_table_index.live_rows("creature_template")}
        package = registry.load_class_package(
            HUNTER_DIR, ids_cfg=ids_cfg, trainer_index=trainer_state.load_trainer_index(),
            existing_group_ids={key[0] for key in spell_table_index.live_keys("spell_group")},
            shapeshift_index=state.load_stock_rows(dbcfmt.SPELLSHAPESHIFTFORM),
            existing_creature_rows=creature_rows,
            creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
            creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS,
            live_data=spell_tables.load_dsl_live_data(),
        )
        reuse = ReuseContext({}, ids_cfg)
        rows = [build.build_spell_row(e, reuse) for e in package.spells]
        _CACHE.update(
            reuse=reuse, package=package, ids_cfg=ids_cfg, creature_rows=creature_rows, rows=rows,
            rows_by_id={int(r["ID"]): r for r in rows},
            sla_rows=[build.build_skilllineability_row(e) for e in package.skill_line_abilities],
            stock_spells=state.load_stock_rows(dbcfmt.SPELL),
        )
    return _CACHE


def retirement_resolution() -> dict:
    """Runs the retirement helpers exactly as generate.py (lines ~460-503) does, on the hunter package's retirements:
    the real superseded-rank map, the declared + rank-override + retire-override SkillLineAbility overlay, and the
    family skill lines (P1-4: a `{}` superseded map hid the Bite records 5953 and 9071)."""
    if "resolution" not in _CACHE:
        from bootstrap import load_spell_ranks_chains  # noqa: PLC0415

        data = package_data()
        package = data["package"]
        stock_sla = state.load_stock_rows(dbcfmt.SKILLLINEABILITY)
        existing_sla = state.load_existing_rows(dbcfmt.SKILLLINEABILITY)
        lines_by_family = superseded_ranks.family_skill_lines(state.load_stock_rows(dbcfmt.CREATUREFAMILY))
        declared = list(package.skill_line_abilities)
        rank_overrides = superseded_ranks.skilllineability_overrides(
            load_spell_ranks_chains(), package.spells, stock_sla, declared, existing_sla,
        )
        retirements = package.pet_spell_retirements
        overrides = superseded_ranks.retired_skilllineability_overrides(
            retirements, stock_sla, lines_by_family, declared, {e["id"] for e in rank_overrides.entries}, existing_sla,
        )
        built_declared = [*declared, *rank_overrides.entries]
        strips, strip_warnings = superseded_ranks.spell_data_strips(
            retirements, data["creature_rows"], state.load_stock_rows(dbcfmt.CREATURESPELLDATA),
            rank_overrides.superseded, lines_by_family,
            {
                **stock_sla,
                **{e["id"]: build.build_skilllineability_row(e) for e in built_declared},
                **{e["id"]: build.build_skilllineability_row(e) for e in overrides.entries},
            },
        )
        _CACHE["resolution"] = (retirements, overrides, strips, strip_warnings)
    return _CACHE["resolution"]


class HunterPetDataTest(unittest.TestCase):
    def assertClean(self, problems: list[str]):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    # (a)
    def test_retire_pet_spell_calls_are_the_pet_4_6_list(self):
        retirements, *_ = retirement_resolution()
        self.assertClean(check_retired_spell_set(retirements, EXPECTED_RETIRED_SPELLS))

    def test_every_retirement_resolves(self):
        retirements, overrides, strips, strip_warnings = retirement_resolution()
        print(f"\nretire_pet_spell: {len(retirements)} call(s), {len(overrides.entries)} SkillLineAbility row(s) "
              f"overridden, {len(strips)} CreatureSpellData record(s) stripped")
        for text in overrides.warnings + overrides.collisions + strip_warnings:
            print(f"WARNING: retire_pet_spell: {text}")
        self.assertClean(check_retirement_resolution(retirements, overrides, strips, strip_warnings))

    def test_zeroed_skilllineability_ids_are_the_46_rows(self):
        _, overrides, *_ = retirement_resolution()
        self.assertEqual(len(EXPECTED_ZEROED_SLA_IDS), 46)
        self.assertClean(check_zeroed_sla_ids(overrides.entries, EXPECTED_ZEROED_SLA_IDS))

    # (b)
    def test_p1_rows_have_equipped_item_class_minus_one(self):
        self.assertClean(check_equipped_item_class(package_data()["rows_by_id"], P1_SPELLS))

    # (c)
    def test_no_sp_potency_on_pet_bit_spells(self):
        data = package_data()
        self.assertClean(check_no_sp_potency_on_pet_bit(
            data["package"].spells, data["rows_by_id"], data["package"].spell_bonus_data))

    # (d)
    def test_furious_howl_shape(self):
        self.assertClean(check_furious_howl(package_data()["rows_by_id"].get(FURIOUS_HOWL)))

    # H0-P2 built-row guards
    def test_h0_p2_rows_have_equipped_item_class_minus_one(self):
        self.assertClean(check_equipped_item_class(package_data()["rows_by_id"], NO_ITEM_CLASS_P2))

    def test_mirrors_and_kits_are_passive_and_permanent(self):
        data = package_data()
        self.assertClean(check_passive_permanent(data["rows_by_id"], data["reuse"].duration_index(None)))

    def test_kill_command_helpers(self):
        data = package_data()
        self.assertClean(check_helpers(data["rows_by_id"], data["reuse"].range_index(50000.0)))

    def test_kit_masks_and_values(self):
        rows = package_data()["rows_by_id"]
        self.assertClean(check_kit_masks(rows))
        self.assertClean(check_kit_values(rows))

    def test_autocast_marker(self):
        package = package_data()["package"]
        for marker in MARKERS:
            self.assertClean(check_autocast_marker(package_data()["rows_by_id"], package.spell_script_names, marker))

    def test_versatility_mirror_custom_attr(self):
        attrs = {int(c["spell_id"]): int(c["attributes"]) for c in package_data()["package"].custom_attrs}
        self.assertEqual(attrs.get(201700), 0x0E000000)

    def test_kill_command_row_trainers_and_bindings(self):
        data = package_data()
        package = data["package"]
        self.assertClean(check_kill_command_row(data["rows_by_id"].get(34026)))
        self.assertClean(check_trainer_rows(package.trainer_spells))
        self.assertClean(check_bindings(package.spell_script_names, package.script_removals,
                                        EXPECTED_BOUND, EXPECTED_UNBOUND))

    # P1-4: the real superseded map and family data, so the Bite records strip and nothing is left alone
    def test_no_record_is_left_alone_because_another_family_names_it(self):
        _, _, _, strip_warnings = retirement_resolution()
        self.assertClean(check_shared_record_warnings(strip_warnings, EXPECTED_SHARED_RECORD_WARNINGS))

    # (e)
    def test_d2_b23_carriers(self):
        self.assertClean(check_d2_b23_carriers(package_data()["rows"]))

    def test_no_reader_holds_the_pet_bit(self):
        data = package_data()
        self.assertClean(check_no_pet_bit_in_readers(data["rows"], data["package"].spell_procs))

    def test_longevity_and_cobra_strikes_are_re_masked(self):
        rows = package_data()["rows_by_id"]
        for spell_id in (53262, 53263, 53264):
            # S1a (BM 5): Bestial Wrath + the Command presses (d2 b21), no longer every pet ability
            self.assertEqual(_effect_mask(rows[spell_id], 1), (0, 0x02000000, 0x200000), spell_id)
        self.assertEqual(_effect_mask(rows[53257], 1), (0, 0, 0x400000))

    # (f)
    def test_new_pet_cast_spells_carry_the_pet_bit(self):
        self.assertClean(check_pet_cast_carry_pet_bit(package_data()["rows_by_id"]))

    def test_new_skilllineability_rows(self):
        data = package_data()
        spells = {**data["stock_spells"], **data["rows_by_id"]}
        self.assertClean(check_sla_rows(data["sla_rows"], spells))

    # (g)
    def test_hunter_family_rules_lint_is_silent(self):
        data = package_data()
        package = data["package"]
        pet_lines: set[int] = set()
        for lines in superseded_ranks.family_skill_lines(state.load_stock_rows(dbcfmt.CREATUREFAMILY)).values():
            pet_lines.update(lines)
        sla = list({**state.load_stock_rows(dbcfmt.SKILLLINEABILITY),
                    **{int(r["ID"]): r for r in data["sla_rows"]}}.values())
        warnings = lint.check_hunter_family_rules(package.spells, data["rows"], package.spell_procs, sla, pet_lines)
        self.assertClean(warnings)

    def test_talent_tab_refs_lint_is_silent(self):
        data = package_data()
        package = data["package"]
        talents = {**state.load_stock_rows(dbcfmt.TALENT),
                   **{int(r["ID"]): r for r in map(build.build_talent_row, package.talents)}}
        tabs = {**state.load_stock_rows(dbcfmt.TALENTTAB),
                **{int(r["ID"]): r for r in map(build.build_talenttab_row, package.tabs)}}
        self.assertClean(lint.check_talent_tab_refs([*talents.values()], [*tabs.values()]))


# ---- negative fixtures: every check must fire on a minimal bad input -------------------------------------------

def _row(spell_id=1, **cols) -> dict:
    return {"ID": spell_id, **cols}


class HunterPetDataNegativeTest(unittest.TestCase):
    def test_unmatched_retirement_is_caught(self):
        # the real helper on a one-row stock table: spell 999 teaches nothing, spell 100 matches row 1
        stock = {1: {"ID": 1, "SkillLine": 270, "Spell": 100, "AcquireMethod": 2, "RaceMask": 0, "ClassMask": 0,
                     "ExcludeRace": 0, "ExcludeClass": 0, "MinSkillLineRank": 0, "SupercededBySpell": 0,
                     "TrivialSkillLineRankHigh": 0, "TrivialSkillLineRankLow": 0, "CharacterPoints_1": 0,
                     "CharacterPoints_2": 0}}
        retirements = [{"spell_id": 100, "families": None}, {"spell_id": 999, "families": None}]
        overrides = superseded_ranks.retired_skilllineability_overrides(retirements, stock, {}, [], set(), {})
        problems = check_retirement_resolution(retirements, overrides, {}, [])
        self.assertEqual(len(problems), 1)
        self.assertIn("retire_pet_spell(999)", problems[0])
        self.assertEqual(check_retirement_resolution(retirements[:1], overrides, {}, []), [])

    def test_strip_match_counts_as_resolved(self):
        retirements = [{"spell_id": 5, "families": None}]
        self.assertEqual(
            check_retirement_resolution(retirements, superseded_ranks.Overrides(), {77: frozenset({5})}, []), [])

    def test_helper_warning_is_a_defect_but_shared_record_warning_is_not(self):
        retirements = [{"spell_id": 5, "families": None}]
        strips = {1: frozenset({5})}
        bad = check_retirement_resolution(retirements, superseded_ranks.Overrides(), strips, ["something odd"])
        self.assertEqual(len(bad), 1)
        quiet = check_retirement_resolution(
            retirements, superseded_ranks.Overrides(), strips,
            ["retire_pet_spell(5, families=[1]): CreatureSpellData 12 holds it and is also named by creatures of families [2], so it is left alone"])
        self.assertEqual(quiet, [])
        ov = superseded_ranks.Overrides(warnings=["row 5 stays"])
        self.assertEqual(len(check_retirement_resolution(retirements, ov, strips, [])), 1)

    def test_sla_id_set_mismatch_is_caught(self):
        entries = [{"id": i, "skill_line": 1, "spell_id": 1, "acquire_method": 0} for i in (1, 2, 3)]
        self.assertEqual(len(check_zeroed_sla_ids(entries, frozenset({1, 2}))), 1)   # extra
        self.assertEqual(len(check_zeroed_sla_ids(entries, frozenset({1, 2, 3, 4}))), 1)   # missing
        self.assertEqual(check_zeroed_sla_ids(entries, frozenset({1, 2, 3})), [])
        two = [{"id": 4, "skill_line": 1, "spell_id": 1, "acquire_method": 2}]
        self.assertEqual(len(check_zeroed_sla_ids(two, frozenset({4}))), 1)
        raw = [{"id": 4, "skill_line": 1, "spell_id": 1, "raw_overrides": {"AcquireMethod": 0}}]
        self.assertEqual(check_zeroed_sla_ids(raw, frozenset({4})), [])

    def test_retired_spell_set_mismatch_is_caught(self):
        self.assertEqual(len(check_retired_spell_set([{"spell_id": 1}, {"spell_id": 9}], frozenset({1}))), 1)
        self.assertEqual(len(check_retired_spell_set([{"spell_id": 1}], frozenset({1, 2}))), 1)
        self.assertEqual(check_retired_spell_set([{"spell_id": 1}], frozenset({1})), [])

    def test_wrong_or_missing_equipped_item_class_is_caught(self):
        rows = {1: _row(1, EquippedItemClass=0), 2: _row(2, EquippedItemClass=-1), 3: _row(3)}
        self.assertEqual(len(check_equipped_item_class(rows, (1, 3, 4))), 3)
        self.assertEqual(check_equipped_item_class(rows, (2,)), [])

    def test_sp_potency_on_pet_bit_spell_is_caught(self):
        entry = {"id": 5, "name": "Gore", "effect1": {"_potency": {"sp_coefficient": 0.1}}}
        rows = {5: _row(5, SpellClassMask_2=PET_BIT_D1)}
        self.assertEqual(len(check_no_sp_potency_on_pet_bit([entry], rows, [])), 1)
        # the three NPC-used ids keep their potency; a spell without the pet bit is out of scope
        self.assertEqual(check_no_sp_potency_on_pet_bit([entry], rows, [], keep=frozenset({5})), [])
        self.assertEqual(check_no_sp_potency_on_pet_bit([entry], {5: _row(5)}, []), [])
        ap_only = {"id": 5, "name": "x", "effect1": {"_potency": {"sp_coefficient": 0.0, "ap_coefficient": 0.1}}}
        self.assertEqual(check_no_sp_potency_on_pet_bit([ap_only], rows, []), [])
        # a surviving spell_bonus_data SP coefficient is caught too
        self.assertEqual(len(check_no_sp_potency_on_pet_bit(
            [ap_only], rows, [{"entry": 5, "direct_bonus": 0.2, "dot_bonus": 0.0}])), 1)

    def test_furious_howl_stale_fields_are_caught(self):
        good = _row(FURIOUS_HOWL, Effect_1=6, EffectAura_1=52, EffectBasePoints_1=4, MaxLevel=0,
                    EffectRealPointsPerLevel_1=0.0)
        self.assertEqual(check_furious_howl(good), [])
        self.assertEqual(len(check_furious_howl({**good, "Effect_2": 6})), 1)                       # eff1 not deleted
        self.assertEqual(len(check_furious_howl({**good, "EffectRealPointsPerLevel_1": 3.8227848})), 1)
        self.assertEqual(len(check_furious_howl({**good, "MaxLevel": 80})), 1)
        self.assertEqual(len(check_furious_howl({**good, "EffectAura_1": 99})), 1)
        self.assertEqual(len(check_furious_howl({**good, "EffectBasePoints_1": 17})), 1)
        self.assertEqual(len(check_furious_howl(None)), 1)

    def test_d2_b23_carrier_set_is_exact(self):
        rows = [_row(i, SpellClassMask_3=PET_BASIC_D2) for i in (17253, 16827, 49966, 201710, 201711)]
        self.assertEqual(check_d2_b23_carriers(rows), [])
        self.assertEqual(len(check_d2_b23_carriers(rows + [_row(2649, SpellClassMask_3=PET_BASIC_D2)])), 1)
        self.assertEqual(len(check_d2_b23_carriers(rows[:-1])), 1)

    def test_pet_bit_in_reader_is_caught(self):
        reader = _row(7, EffectAura_2=108, EffectSpellClassMaskB_2=PET_BIT_D1)
        self.assertEqual(len(check_no_pet_bit_in_readers([reader], [])), 1)
        stock_id_too = _row(53, EffectAura_1=107, EffectSpellClassMaskA_2=PET_BIT_D1 | 1)
        self.assertEqual(len(check_no_pet_bit_in_readers([stock_id_too], [])), 1)
        self.assertEqual(check_no_pet_bit_in_readers([_row(7, EffectAura_1=107, EffectSpellClassMaskA_3=PET_BASIC_D2)], []), [])
        self.assertEqual(len(check_no_pet_bit_in_readers([], [{"SpellId": 9, "SpellFamilyMask1": PET_BIT_D1}])), 1)
        longevity = _row(53262, EffectAura_1=108, EffectSpellClassMaskA_2=0x12000000)
        self.assertEqual(len(check_no_pet_bit_in_readers([longevity], [])), 1)
        self.assertEqual(check_no_pet_bit_in_readers([longevity], [], known=frozenset({53262})), [])

    def test_pet_cast_without_pet_bit_is_caught(self):
        rows = {i: _row(i, SpellClassMask_2=PET_BIT_D1) for i in PET_CAST_NEW}
        self.assertEqual(check_pet_cast_carry_pet_bit(rows), [])
        rows[201716] = _row(201716, SpellClassMask_2=0x1)
        self.assertEqual(len(check_pet_cast_carry_pet_bit(rows)), 1)
        del rows[201717]
        self.assertEqual(len(check_pet_cast_carry_pet_bit(rows)), 2)

    def _good_sla(self):
        rows = []
        for (first, last), lines, spell in SLA_TABLE:
            for row_id, line in zip(range(first, last + 1), lines):
                rows.append({"ID": row_id, "SkillLine": line, "Spell": spell, "AcquireMethod": 2, "ClassMask": 0})
        spells = {spell: _row(spell, SpellLevel=1) for _, _, spell in SLA_TABLE}
        return rows, spells

    def test_sla_rows_check_fires_on_each_defect(self):
        rows, spells = self._good_sla()
        self.assertEqual(len(rows), 46)
        self.assertEqual(check_sla_rows(rows, spells), [])
        self.assertTrue(check_sla_rows(rows[:-1], spells))                                       # a missing row
        wrong_method = [dict(r) for r in rows]
        wrong_method[3]["AcquireMethod"] = 0
        self.assertTrue(any("AcquireMethod" in p for p in check_sla_rows(wrong_method, spells)))
        wrong_spell = [dict(r) for r in rows]
        wrong_spell[0]["Spell"] = 53478
        self.assertTrue(any("PET 4.4 says" in p for p in check_sla_rows(wrong_spell, spells)))
        self.assertTrue(any("SpellLevel" in p for p in check_sla_rows(rows, {**spells, 61684: _row(61684, SpellLevel=0)})))
        self.assertTrue(any("no spell row" in p for p in check_sla_rows(rows, {})))
        with_class = [dict(r) for r in rows]
        with_class[5]["ClassMask"] = 4
        self.assertTrue(any("ClassMask" in p for p in check_sla_rows(with_class, spells)))

    def test_shared_record_warning_list_is_exact(self):
        warning = "retire_pet_spell(17253, families=[1]): CreatureSpellData 5953 holds it and " \
                  "is also named by creatures of families [2], so it is left alone"
        self.assertEqual(len(check_shared_record_warnings([warning, "unrelated"], [])), 1)
        self.assertEqual(len(check_shared_record_warnings([warning], [])), 1)
        self.assertEqual(len(check_shared_record_warnings([], [warning])), 1)
        self.assertEqual(check_shared_record_warnings([warning, "other"], [warning]), [])

    def test_passive_and_duration_are_caught(self):
        rows = {1: _row(1, Attributes=464, DurationIndex=7), 2: _row(2, Attributes=16, DurationIndex=7),
                3: _row(3, Attributes=464, DurationIndex=9)}
        bad = check_passive_permanent(rows, 7, ids=(1, 2, 3, 4))
        self.assertEqual(len(bad), 3)    # 2 not passive, 3 wrong built duration index, 4 missing
        self.assertEqual(check_passive_permanent(rows, 7, ids=(1,)), [])

    def test_helper_defects_are_caught(self):
        good = {201704: _row(201704, SpellClassSet=0, RangeIndex=13, AttributesEx2=0x4, AttributesEx3=0x10000),
                201705: _row(201705, SpellClassSet=0, RangeIndex=30202)}
        self.assertEqual(check_helpers(good, 30202), [])
        self.assertEqual(len(check_helpers({**good, 201704: {**good[201704], "SpellClassSet": 9}}, 30202)), 1)
        self.assertEqual(len(check_helpers({**good, 201704: {**good[201704], "RangeIndex": 2}}, 30202)), 1)
        self.assertEqual(len(check_helpers({**good, 201704: {**good[201704], "AttributesEx2": 0}}, 30202)), 1)
        self.assertEqual(len(check_helpers({**good, 201704: {**good[201704], "AttributesEx3": 0}}, 30202)), 1)
        self.assertEqual(len(check_helpers({**good, 201705: {**good[201705], "RangeIndex": 36}}, 30202)), 1)
        self.assertEqual(len(check_helpers({}, 30202)), 2)

    def test_autocast_marker_defects_are_caught(self):
        good = _row(MARKER, SpellClassSet=0, Effect_1=6, EffectAura_1=4, EffectBasePoints_1=0)
        self.assertEqual(check_autocast_marker({MARKER: good}, []), [])
        self.assertEqual(len(check_autocast_marker({}, [])), 1)
        self.assertEqual(len(check_autocast_marker({MARKER: {**good, "SpellClassSet": 9}}, [])), 1)
        self.assertEqual(len(check_autocast_marker({MARKER: {**good, "SpellClassMask_3": PET_BASIC_D2}}, [])), 1)
        self.assertEqual(len(check_autocast_marker({MARKER: {**good, "EffectSpellClassMaskA_3": PET_BASIC_D2}}, [])), 1)
        self.assertEqual(len(check_autocast_marker({MARKER: {**good, "EffectAura_1": 79}}, [])), 1)
        self.assertEqual(len(check_autocast_marker({MARKER: {**good, "EffectBasePoints_1": 5}}, [])), 1)
        self.assertEqual(len(check_autocast_marker({MARKER: good}, [{"spell_id": MARKER, "ScriptName": "x"}])), 1)
        self.assertEqual(check_autocast_marker({MARKER: good}, [{"spell_id": 34902, "ScriptName": "x"}]), [])
        utility = {**good, "ID": 201752}
        self.assertEqual(check_autocast_marker({201752: utility}, [], 201752), [])
        self.assertEqual(len(check_autocast_marker({201752: {**utility, "SpellClassSet": 9}}, [], 201752)), 1)
        self.assertEqual(len(check_autocast_marker({}, [], 201752)), 1)
        self.assertEqual(len(check_autocast_marker({201752: utility}, [{"spell_id": 201752, "ScriptName": "x"}], 201752)), 1)

    def _good_kit(self, spell_id=201707):
        return _row(spell_id, SpellClassSet=9, EffectSpellClassMaskA_3=PET_BASIC_D2, EffectSpellClassMaskB_3=PET_BASIC_D2)

    def test_kit_mask_defects_are_caught(self):
        good = {i: self._good_kit(i) for i in KITS}
        self.assertEqual(check_kit_masks(good), [])
        self.assertEqual(len(check_kit_masks({**good, 201706: {**good[201706], "SpellClassSet": 0}})), 1)
        self.assertEqual(len(check_kit_masks({**good, 201706: {**good[201706], "EffectSpellClassMaskB_2": PET_BIT_D1}})), 1)
        self.assertEqual(len(check_kit_masks({**good, 201706: {**good[201706], "EffectSpellClassMaskA_3": 0}})), 1)
        self.assertEqual(len(check_kit_masks({**good, 201706: {**good[201706], "SpellClassMask_2": PET_BIT_D1}})), 1)
        self.assertEqual(len(check_kit_masks({k: v for k, v in good.items() if k != 201708})), 1)

    def test_kit_value_defects_are_caught(self):
        good = {201706: _row(201706, EffectBasePoints_1=-1, EffectBasePoints_2=-1),
                201707: _row(201707, EffectBasePoints_1=5999, EffectBasePoints_2=193),
                201708: _row(201708, EffectBasePoints_1=-1, EffectBasePoints_2=-1)}
        self.assertEqual(check_kit_values(good), [])
        self.assertEqual(len(check_kit_values({**good, 201707: _row(201707, EffectBasePoints_1=6000,
                                                                    EffectBasePoints_2=193)})), 1)
        self.assertEqual(len(check_kit_values({**good, 201706: _row(201706, EffectBasePoints_1=0,
                                                                    EffectBasePoints_2=-1)})), 1)

    def test_kill_command_row_defects_are_caught(self):
        good = _row(34026, Category=0, RecoveryTime=6000, StartRecoveryTime=1500, StartRecoveryCategory=133,
                    DefenseType=3, AttributesEx=0, AttributesEx2=0, SpellLevel=10, Effect_1=2, Effect_2=3,
                    SpellClassMask_2=0x800)
        self.assertEqual(check_kill_command_row(good), [])
        for key, value in (("Category", 1171), ("RecoveryTime", 60000), ("AttributesEx", 0x10000400),
                           ("AttributesEx2", 4), ("SpellLevel", 66), ("Effect_1", 6), ("Effect_2", 0),
                           ("DefenseType", 0), ("StartRecoveryCategory", 0), ("SpellClassMask_1", 1),
                           ("SpellClassMask_3", 1), ("SpellClassMask_2", 0x801)):
            self.assertEqual(len(check_kill_command_row({**good, key: value})), 1, key)
        self.assertEqual(len(check_kill_command_row(None)), 1)

    def test_trainer_row_defects_are_caught(self):
        good = [{"TrainerId": 204, "SpellId": 34026, "ReqLevel": 10}, {"TrainerId": 205, "SpellId": 34026, "ReqLevel": 10}]
        self.assertEqual(check_trainer_rows(good), [])
        self.assertEqual(len(check_trainer_rows(good[:1])), 1)
        self.assertEqual(len(check_trainer_rows([{**good[0], "ReqLevel": 66}, good[1]])), 1)
        self.assertEqual(len(check_trainer_rows([*good, {"TrainerId": 7, "SpellId": 34026, "ReqLevel": 66}])), 1)

    def test_binding_defects_are_caught(self):
        def rows(pairs):
            return [{"spell_id": i, "ScriptName": n} for i, n in pairs]
        bound = rows([(34902, "spell_hun_pet_scaling_rework")])
        unbound = rows([(34902, "spell_hun_generic_scaling")])
        eb, eu = {34902: {"spell_hun_pet_scaling_rework"}}, {34902: {"spell_hun_generic_scaling"}}
        self.assertEqual(check_bindings(bound, unbound, eb, eu), [])
        self.assertEqual(len(check_bindings([], unbound, eb, eu)), 1)                    # not rebound
        self.assertEqual(len(check_bindings(bound, [], eb, eu)), 1)                      # stock class still bound
        self.assertEqual(len(check_bindings(bound + rows([(34903, "x")]), unbound, eb, eu)), 1)    # 34903 touched
        self.assertEqual(len(check_bindings(bound, unbound + rows([(34904, "y")]), eb, eu)), 1)

    def test_family_rules_lint_fires_on_a_pet_group_carrier_without_the_pet_bit(self):
        row = {"ID": 200100, "SpellClassSet": 9, "SpellClassMask_1": 0, "SpellClassMask_2": 0,
               "SpellClassMask_3": PET_BASIC_D2}
        self.assertEqual(len(lint.check_hunter_family_rules([{"name": "X"}], [row])), 1)

    def test_tab_refs_lint_fires_on_a_missing_tab(self):
        self.assertEqual(len(lint.check_talent_tab_refs([{"ID": 1, "TabID": 60800}], [{"ID": 361}])), 1)


if __name__ == "__main__":
    unittest.main()
