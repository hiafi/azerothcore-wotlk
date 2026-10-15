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
            package=package, ids_cfg=ids_cfg, creature_rows=creature_rows, rows=rows,
            rows_by_id={int(r["ID"]): r for r in rows},
            sla_rows=[build.build_skilllineability_row(e) for e in package.skill_line_abilities],
            stock_spells=state.load_stock_rows(dbcfmt.SPELL),
        )
    return _CACHE


def retirement_resolution() -> dict:
    """Runs the two helpers exactly as generate.py (lines ~473-500) does, on the hunter package's retirements."""
    if "resolution" not in _CACHE:
        data = package_data()
        package = data["package"]
        stock_sla = state.load_stock_rows(dbcfmt.SKILLLINEABILITY)
        retirements = package.pet_spell_retirements
        overrides = superseded_ranks.retired_skilllineability_overrides(
            retirements, stock_sla,
            superseded_ranks.family_skill_lines(state.load_stock_rows(dbcfmt.CREATUREFAMILY)),
            list(package.skill_line_abilities), set(), {},
        )
        strips, strip_warnings = superseded_ranks.spell_data_strips(
            retirements, data["creature_rows"], state.load_stock_rows(dbcfmt.CREATURESPELLDATA), {},
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

    # (e)
    def test_d2_b23_carriers(self):
        self.assertClean(check_d2_b23_carriers(package_data()["rows"]))

    def test_no_reader_holds_the_pet_bit(self):
        data = package_data()
        self.assertClean(check_no_pet_bit_in_readers(data["rows"], data["package"].spell_procs))

    def test_longevity_and_cobra_strikes_are_re_masked(self):
        rows = package_data()["rows_by_id"]
        for spell_id in (53262, 53263, 53264):
            self.assertEqual(_effect_mask(rows[spell_id], 1), (0, 0x02000000, 0x8), spell_id)
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

    def test_family_rules_lint_fires_on_a_pet_group_carrier_without_the_pet_bit(self):
        row = {"ID": 200100, "SpellClassSet": 9, "SpellClassMask_1": 0, "SpellClassMask_2": 0,
               "SpellClassMask_3": PET_BASIC_D2}
        self.assertEqual(len(lint.check_hunter_family_rules([{"name": "X"}], [row])), 1)

    def test_tab_refs_lint_fires_on_a_missing_tab(self):
        self.assertEqual(len(lint.check_talent_tab_refs([{"ID": 1, "TabID": 60800}], [{"ID": 361}])), 1)


if __name__ == "__main__":
    unittest.main()
