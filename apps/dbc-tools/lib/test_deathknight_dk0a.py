"""
Death Knight DK0a data gate (death-knight-rework DK0a-HANDOFF row A6, DK0a-WP-BRIEF).

Loads the real deathknight DSL package (source/classes/deathknight/) and asserts on the BUILT rows (stock base + DSL +
raw_overrides via `build.build_spell_row`, the way generate.py pairs them), so a stale raw twin that wins fails here
too. The shape follows lib/test_shaman_sh0a.py; the checks are pure functions over built rows with a negative fixture
each. An id that no agent has declared yet is reported by `test_required_ids_declared` (and skipped by the other
checks), so the file can run at any point of the stage.

  1. Heart Strike 55050 / Frost Strike 49143: EFFECT_2 builds all-zero (the core multiplies it by the disease count);
     effect 1 is the percent weapon effect, effect 2 the flat normalized one (percent before flat).
  2. Death Strike 49998: PowerType 6, ManaCost 400, RuneCostID 0, AttributesEx 0x08000200, EFFECT_2 DUMMY base 24.
  3. Blood Presence 48266: no Attributes 0x80000000, no AttributesEx CAST_WHEN_LEARNED, AttributesEx2 0x10 kept, GCD 0,
     RuneCostID 0, spell_custom_attr 0x06000000, spell_linked_spell type-2 to 203000 and the U1 links to 57340.
  4. Crit child 203000: auras 187/188 at -1001, AttributesEx3 0x100000.
  5. Rune Tap 48982: eff0 ENERGIZE misc 6 value 500. ERW 47568: RecoveryTime 180000.
  6. Every DK0a row a trainer teaches: SpellLevel == the trainer's ReqLevel.
  7. No DK0a row's own SpellClassMask carries a `_masks.FORBIDDEN_*` bit (stock-kept bits exempt per row).
  8. Death's Caress 203001 sits on d2 b12 only.
  9. No spell a player learns has Attributes 0x80 (DO_NOT_DISPLAY).
 10. The 16 cut talents sit on the retired tab 60800.

Run: apps/dbc-tools/.venv/bin/python3 -m pytest apps/dbc-tools/lib/test_deathknight_dk0a.py -q
"""

from __future__ import annotations

import importlib.util
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import build, dbcfmt, lint, source, spell_tables, state, trainer_state  # noqa: E402
from lib.dsl import registry  # noqa: E402
from lib.reuse import ReuseContext  # noqa: E402

TOOL_ROOT = Path(__file__).resolve().parents[1]
DK_DIR = TOOL_ROOT / "source" / "classes" / "deathknight"
_masks_spec = importlib.util.spec_from_file_location("_dk_masks", DK_DIR / "_masks.py")
m = importlib.util.module_from_spec(_masks_spec)
_masks_spec.loader.exec_module(m)

HEART_STRIKE = 55050
FROST_STRIKE = 49143
DEATH_STRIKE = 49998
BLOOD_PRESENCE = 48266
CRIT_CHILD = 203000
DEATHS_CARESS = 203001
RUNE_TAP = 48982
ERW = 47568
TAG_CLASS_TANK_THREAT = 57340
WEAPON_STRIKES = (HEART_STRIKE, FROST_STRIKE)
# Every spell DK0a edits or adds (HANDOFF Known-hard items); the stock-kept helper rows are listed in DK0A_IDS too so
# the SpellLevel / forbidden-bit checks reach them when a DSL file declares them.
DK0A_IDS = (BLOOD_PRESENCE, CRIT_CHILD, DEATHS_CARESS, DEATH_STRIKE, HEART_STRIKE, RUNE_TAP, 51052, 50461, 49222,
            FROST_STRIKE, 49039, ERW, 49576, 50977, 3714, 50842, 48707, 55095, 55078)
REQUIRED_IDS = (BLOOD_PRESENCE, CRIT_CHILD, DEATHS_CARESS, DEATH_STRIKE, HEART_STRIKE, RUNE_TAP, 51052, 50461, 49222,
                FROST_STRIKE, 49039, ERW)
# Stock-kept forbidden bits (own SpellClassMask), per row: the two disease DoTs are the "real disease DoT" d2 b1.
# Anti-Magic Shell 48707 keeps its stock d0 b17.
# DK0b pulled the two diseases into the DSL (they were npc.csv-only), so their stock d1 b11 (0x800) shows up here too.
FORBIDDEN_EXEMPT = {55078: (0, m.FORBIDDEN_D1_B11, m.FORBIDDEN_D2_B1), 55095: (0, m.FORBIDDEN_D1_B11, m.FORBIDDEN_D2_B1),
                    48707: (m.FORBIDDEN_D0_B17, 0, 0)}
RETIRED_TALENTS = (1941, 2086, 1942, 1954, 1936, 1957, 2035, 2215, 1990, 2029, 1979, 1975, 2221, 2013, 2085, 2007)
RETIRED_TAB = 60800
DEATH_KNIGHT_TRAINER = 13

EFFECT_DUMMY = 3
EFFECT_ENERGIZE = 30
EFFECT_WEAPON_PERCENT_DAMAGE = 31
EFFECT_NORMALIZED_WEAPON_DMG = 121
AURA_MOD_ATTACKER_MELEE_CRIT = 187
AURA_MOD_ATTACKER_RANGED_CRIT = 188
POWER_RUNIC_POWER = 6
ATTR0_NO_AURA_CANCEL = 0x80000000
ATTR0_DO_NOT_DISPLAY = 0x80
ATTR1_CAST_WHEN_LEARNED = 0x80000000
ATTR2_USE_SHAPESHIFT_BAR = 0x10
ATTR3_DEATH_PERSISTENT = 0x100000
DEATH_STRIKE_ATTR_EX = 0x08000200
CUSTOM_ATTR_POSITIVE_EFF0_EFF1 = 0x06000000
LINK_AURA = 2
PET_SKILL_LINE = 270
THIRD_SLOT_COLUMNS = ("Effect_3", "EffectBasePoints_3", "EffectDieSides_3", "ImplicitTargetA_3",
                      "ImplicitTargetB_3", "EffectChainAmplitude_3", "EffectAura_3", "EffectMiscValue_3")


def _u32(value) -> int:
    return int(value or 0) & 0xFFFFFFFF


def _f32(value) -> float:
    return struct.unpack("f", struct.pack("f", float(value or 0)))[0]


def spell_mask(row: dict) -> tuple[int, int, int]:
    return tuple(_u32(row.get(f"SpellClassMask_{n}")) for n in (1, 2, 3))


def _hex(mask) -> str:
    return "(" + ", ".join(f"0x{w:X}" for w in mask) + ")"


def _present(rows_by_id: dict[int, dict], *ids: int):
    return [rows_by_id[i] for i in ids if i in rows_by_id]


# ---- checks (pure: take built rows, return problem strings) ------------------------------------------------

def check_required_ids(rows_by_id: dict[int, dict]) -> list[str]:
    return [f"{i}: not declared by any deathknight DSL file (A1-A3 row missing)" for i in REQUIRED_IDS
            if i not in rows_by_id]


def check_weapon_strike_effects(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for row in _present(rows_by_id, *WEAPON_STRIKES):
        sid = row["ID"]
        for col in THIRD_SLOT_COLUMNS:
            default = 1.0 if col == "EffectChainAmplitude_3" else 0  # an unused effect's chain amplitude is 1.0
            if float(row.get(col) or 0) not in (0, default):
                bad.append(f"{sid}: EFFECT_2 column {col} = {row.get(col)!r}, expected 0 (the core reads "
                           f"Effects[EFFECT_2].CalcValue() x diseases)")
        effect1, effect2 = int(row.get("Effect_1") or 0), int(row.get("Effect_2") or 0)
        if effect1 != EFFECT_WEAPON_PERCENT_DAMAGE:
            bad.append(f"{sid}: effect 1 is {effect1}, expected WEAPON_PERCENT_DAMAGE (31) - percent effect first")
        if effect2 != EFFECT_NORMALIZED_WEAPON_DMG:
            bad.append(f"{sid}: effect 2 is {effect2}, expected NORMALIZED_WEAPON_DMG (121) - flat effect second")
    return bad


def check_death_strike(rows_by_id: dict[int, dict]) -> list[str]:
    row = rows_by_id.get(DEATH_STRIKE)
    if row is None:
        return []
    bad = []
    for col, want in (("PowerType", POWER_RUNIC_POWER), ("ManaCost", 400), ("RuneCostID", 0)):
        if int(row.get(col) or 0) != want:
            bad.append(f"{DEATH_STRIKE}: {col} {row.get(col)!r}, expected {want}")
    if _u32(row.get("AttributesEx")) != DEATH_STRIKE_ATTR_EX:
        bad.append(f"{DEATH_STRIKE}: AttributesEx {_u32(row.get('AttributesEx')):#x}, "
                   f"expected {DEATH_STRIKE_ATTR_EX:#x}")
    if int(row.get("Effect_3") or 0) != EFFECT_DUMMY:
        bad.append(f"{DEATH_STRIKE}: effect 3 is {row.get('Effect_3')!r}, expected DUMMY (3, the heal %)")
    if int(row.get("EffectBasePoints_3") or 0) != 24:
        bad.append(f"{DEATH_STRIKE}: effect 3 EffectBasePoints {row.get('EffectBasePoints_3')!r}, "
                   f"expected 24 (heal 25%)")
    if _f32(row.get("EffectRealPointsPerLevel_3")) != 0:
        bad.append(f"{DEATH_STRIKE}: effect 3 points per level {row.get('EffectRealPointsPerLevel_3')!r}, expected 0")
    return bad


EXPECTED_TRAINER_LEVELS = {49576: 16, 50977: 10, 3714: 40, DEATH_STRIKE: 10, 50842: 20, ERW: 54}
DEATH_STRIKE_HEAL = 45470


def check_expected_trainer_levels(rows_by_id: dict[int, dict], trainer_spells: list[dict]) -> list[str]:
    """Each listed spell must be taught by a trainer row at the level and its SpellLevel must match.
    `trainer_spells` is the effective set: the live rows with the DSL's rows laid over them."""
    bad = []
    by_spell = {int(t["SpellId"]): int(t["ReqLevel"]) for t in trainer_spells}
    for spell_id, level in EXPECTED_TRAINER_LEVELS.items():
        if spell_id not in by_spell:
            bad.append(f"{spell_id}: no DK0a trainer row (expected ReqLevel {level})")
        elif by_spell[spell_id] != level:
            bad.append(f"{spell_id}: trainer ReqLevel {by_spell[spell_id]}, expected {level}")
        row = rows_by_id.get(spell_id)
        if row is not None and int(row.get("SpellLevel") or 0) != level:
            bad.append(f"{spell_id}: SpellLevel {row.get('SpellLevel')!r}, expected {level}")
    return bad


def check_death_strike_effect_order(rows_by_id: dict[int, dict]) -> list[str]:
    row = rows_by_id.get(DEATH_STRIKE)
    if row is None:
        return []
    bad = []
    if int(row.get("Effect_1") or 0) != EFFECT_WEAPON_PERCENT_DAMAGE:
        bad.append(f"{DEATH_STRIKE}: effect 1 is {row.get('Effect_1')!r}, expected WEAPON_PERCENT_DAMAGE (31) first")
    if int(row.get("Effect_2") or 0) != EFFECT_NORMALIZED_WEAPON_DMG:
        bad.append(f"{DEATH_STRIKE}: effect 2 is {row.get('Effect_2')!r}, expected NORMALIZED_WEAPON_DMG (121) second")
    return bad


def check_death_strike_heal(rows_by_id: dict[int, dict], bonus_rows: list[dict]) -> list[str]:
    row = rows_by_id.get(DEATH_STRIKE_HEAL)
    if row is None:
        return []
    bad = []
    if int(row.get("DefenseType") or 0) != 1:
        bad.append(f"{DEATH_STRIKE_HEAL}: DefenseType {row.get('DefenseType')!r}, expected 1 (magic)")
    bonus = [b for b in bonus_rows if int(b.get("entry", b.get("spell_id", 0))) == DEATH_STRIKE_HEAL]
    if not bonus:
        bad.append(f"{DEATH_STRIKE_HEAL}: no spell_bonus_data row (expected zeros)")
    for b in bonus:
        for col in ("direct_bonus", "dot_bonus", "ap_bonus", "ap_dot_bonus"):
            if float(b.get(col) or 0) != 0:
                bad.append(f"{DEATH_STRIKE_HEAL}: spell_bonus_data {col} = {b.get(col)!r}, expected 0")
    return bad


def check_blood_presence(rows_by_id: dict[int, dict], links: list[dict], custom_attrs: list[dict]) -> list[str]:
    row = rows_by_id.get(BLOOD_PRESENCE)
    if row is None:
        return []
    bad = []
    if _u32(row.get("Attributes")) & ATTR0_NO_AURA_CANCEL:
        bad.append(f"{BLOOD_PRESENCE}: Attributes carries NO_AURA_CANCEL 0x80000000")
    if _u32(row.get("AttributesEx")) & ATTR1_CAST_WHEN_LEARNED:
        bad.append(f"{BLOOD_PRESENCE}: AttributesEx carries CAST_WHEN_LEARNED 0x80000000")
    if not _u32(row.get("AttributesEx2")) & ATTR2_USE_SHAPESHIFT_BAR:
        bad.append(f"{BLOOD_PRESENCE}: AttributesEx2 lost 0x10 (USE_SHAPESHIFT_BAR)")
    for col in ("StartRecoveryCategory", "StartRecoveryTime", "RuneCostID"):
        if int(row.get(col) or 0) != 0:
            bad.append(f"{BLOOD_PRESENCE}: {col} {row.get(col)!r}, expected 0")
    attrs = [int(c["attributes"]) for c in custom_attrs if int(c["spell_id"]) == BLOOD_PRESENCE]
    if not attrs or not all(a & CUSTOM_ATTR_POSITIVE_EFF0_EFF1 == CUSTOM_ATTR_POSITIVE_EFF0_EFF1 for a in attrs):
        bad.append(f"{BLOOD_PRESENCE}: no spell_custom_attr row with 0x06000000 (got {attrs})")
    wanted = {(BLOOD_PRESENCE, CRIT_CHILD, LINK_AURA): "type-2 link to the crit child 203000",
              (BLOOD_PRESENCE, TAG_CLASS_TANK_THREAT, LINK_AURA): "U1 type-2 link to 57340",
              (-BLOOD_PRESENCE, -TAG_CLASS_TANK_THREAT, 0): "U1 removal link -48266 -> -57340"}
    have = {(int(link["spell_trigger"]), int(link["spell_effect"]), int(link["type"])) for link in links}
    bad += [f"{BLOOD_PRESENCE}: missing {why} {key}" for key, why in wanted.items() if key not in have]
    return bad


def check_crit_child(rows_by_id: dict[int, dict]) -> list[str]:
    row = rows_by_id.get(CRIT_CHILD)
    if row is None:
        return []
    bad = []
    auras = {}
    for i in (1, 2, 3):
        aura = int(row.get(f"EffectAura_{i}") or 0)
        if aura:
            auras[aura] = int(row.get(f"EffectBasePoints_{i}") or 0)
    for aura in (AURA_MOD_ATTACKER_MELEE_CRIT, AURA_MOD_ATTACKER_RANGED_CRIT):
        if aura not in auras:
            bad.append(f"{CRIT_CHILD}: no aura {aura} effect")
        elif auras[aura] != -1001:
            bad.append(f"{CRIT_CHILD}: aura {aura} stored {auras[aura]}, expected -1001")
    if not _u32(row.get("AttributesEx3")) & ATTR3_DEATH_PERSISTENT:
        bad.append(f"{CRIT_CHILD}: AttributesEx3 lacks 0x100000")
    return bad


def check_rune_tap_and_erw(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    row = rows_by_id.get(RUNE_TAP)
    if row is not None:
        if int(row.get("Effect_1") or 0) != EFFECT_ENERGIZE:
            bad.append(f"{RUNE_TAP}: effect 1 is {row.get('Effect_1')!r}, expected ENERGIZE (30)")
        if int(row.get("EffectMiscValue_1") or 0) != POWER_RUNIC_POWER:
            bad.append(f"{RUNE_TAP}: effect 1 misc {row.get('EffectMiscValue_1')!r}, expected 6 (Runic Power)")
        value = int(row.get("EffectBasePoints_1") or 0) + 1
        if value != 500:
            bad.append(f"{RUNE_TAP}: effect 1 value {value}, expected 500 (50 RP x10)")
    row = rows_by_id.get(ERW)
    if row is not None and int(row.get("RecoveryTime") or 0) != 180000:
        bad.append(f"{ERW}: RecoveryTime {row.get('RecoveryTime')!r}, expected 180000")
    return bad


def check_trainer_levels(rows_by_id: dict[int, dict], trainer_spells: list[dict]) -> list[str]:
    bad = []
    for t in trainer_spells:
        row = rows_by_id.get(int(t["SpellId"]))
        if row is None:
            continue
        if int(row.get("SpellLevel") or 0) != int(t["ReqLevel"]):
            bad.append(f"{t['SpellId']}: SpellLevel {row.get('SpellLevel')!r} != trainer {t['TrainerId']} "
                       f"ReqLevel {t['ReqLevel']}")
    return bad


def check_forbidden_bits(rows_by_id: dict[int, dict]) -> list[str]:
    bad = []
    for row in _present(rows_by_id, *DK0A_IDS):
        mask = spell_mask(row)
        exempt = FORBIDDEN_EXEMPT.get(int(row["ID"]), (0, 0, 0))
        hit = (mask[0] & m.FORBIDDEN_D0 & ~exempt[0], mask[1] & m.FORBIDDEN_D1 & ~exempt[1],
               mask[2] & m.FORBIDDEN_D2 & ~exempt[2])
        if any(hit):
            bad.append(f"{row['ID']}: SpellClassMask {_hex(mask)} holds forbidden bits {_hex(hit)}")
    return bad


def check_deaths_caress(rows_by_id: dict[int, dict]) -> list[str]:
    row = rows_by_id.get(DEATHS_CARESS)
    if row is None:
        return []
    mask = spell_mask(row)
    if mask != (0, 0, m.DEATHS_CARESS):
        return [f"{DEATHS_CARESS}: SpellClassMask {_hex(mask)}, expected (0x0, 0x0, 0x{m.DEATHS_CARESS:X}) "
                f"- d2 b12 only"]
    return []


def check_learned_not_hidden(rows_by_id: dict[int, dict], learned: set[int]) -> list[str]:
    return [f"{i}: learned by a player but Attributes {_u32(rows_by_id[i].get('Attributes')):#x} has 0x80"
            for i in sorted(learned) if i in rows_by_id and i in DK0A_IDS
            and _u32(rows_by_id[i].get("Attributes")) & ATTR0_DO_NOT_DISPLAY]


def check_retired_talents(talents: list[dict], retired: list[dict]) -> list[str]:
    bad = []
    by_id = {int(t["id"]): t for t in talents}
    declared = {int(r["id"]) for r in retired}
    for tid in RETIRED_TALENTS:
        if tid not in declared:
            bad.append(f"talent {tid}: not retire_talent()'d")
        talent = by_id.get(tid)
        if talent is None:
            bad.append(f"talent {tid}: no talent entry")
        elif int(talent["tab_id"]) != RETIRED_TAB:
            bad.append(f"talent {tid}: tab {talent['tab_id']}, expected {RETIRED_TAB}")
    return bad


# ---- real data ----------------------------------------------------------------------------------------------

_CACHE: dict = {}


def _data():
    if not _CACHE:
        ids_cfg = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
        spell_table_index = spell_tables.load_spell_table_index()
        creature_table_index = spell_tables.load_creature_table_index()
        trainer_index = trainer_state.load_trainer_index()
        package = registry.load_class_package(
            DK_DIR, ids_cfg=ids_cfg, trainer_index=trainer_index,
            existing_group_ids={key[0] for key in spell_table_index.live_keys("spell_group")},
            shapeshift_index=state.load_stock_rows(dbcfmt.SPELLSHAPESHIFTFORM),
            existing_creature_rows={int(r["entry"]): r for r in creature_table_index.live_rows("creature_template")},
            creature_columns=spell_tables.CREATURE_TEMPLATE_COLUMNS,
            creature_defaults=spell_tables.CREATURE_TEMPLATE_DEFAULTS,
            live_data=spell_tables.load_dsl_live_data(),
        )
        reuse = ReuseContext({}, ids_cfg)
        rows = [build.build_spell_row(e, reuse) for e in package.spells]
        learned = {int(t["SpellId"]) for t in package.trainer_spells}
        learned |= {int(s["spell_id"]) for s in package.skill_line_abilities if int(s["skill_line"]) != PET_SKILL_LINE}
        _CACHE.update(rows_by_id={int(r["ID"]): r for r in rows}, learned=learned, package=package,
                       live_trainer=trainer_index.existing_trainer_spells)
    return _CACHE


class DeathKnightDK0aDataTest(unittest.TestCase):
    def assertClean(self, problems: list[str]):
        self.assertEqual(problems, [], "\n" + "\n".join(problems))

    def test_required_ids_declared(self):
        self.assertClean(check_required_ids(_data()["rows_by_id"]))

    def test_weapon_strike_effects(self):
        self.assertClean(check_weapon_strike_effects(_data()["rows_by_id"]))

    def test_death_strike(self):
        self.assertClean(check_death_strike(_data()["rows_by_id"]))

    def test_blood_presence(self):
        package = _data()["package"]
        self.assertClean(check_blood_presence(_data()["rows_by_id"], package.linked_spells, package.custom_attrs))

    def test_crit_child(self):
        self.assertClean(check_crit_child(_data()["rows_by_id"]))

    def test_rune_tap_and_erw(self):
        self.assertClean(check_rune_tap_and_erw(_data()["rows_by_id"]))

    def test_trainer_levels(self):
        self.assertClean(check_trainer_levels(_data()["rows_by_id"], _data()["package"].trainer_spells))

    def test_expected_trainer_levels(self):
        effective = {sid: row for (tid, sid), row in _data()["live_trainer"].items() if tid == DEATH_KNIGHT_TRAINER}
        effective.update({int(t["SpellId"]): t for t in _data()["package"].trainer_spells
                          if int(t["TrainerId"]) == DEATH_KNIGHT_TRAINER})
        self.assertClean(check_expected_trainer_levels(_data()["rows_by_id"], list(effective.values())))

    def test_death_strike_effect_order(self):
        self.assertClean(check_death_strike_effect_order(_data()["rows_by_id"]))

    def test_death_strike_heal(self):
        package = _data()["package"]
        self.assertClean(check_death_strike_heal(_data()["rows_by_id"], package.spell_bonus_data))

    def test_no_forbidden_bits(self):
        self.assertClean(check_forbidden_bits(_data()["rows_by_id"]))

    def test_deaths_caress_mask(self):
        self.assertClean(check_deaths_caress(_data()["rows_by_id"]))

    def test_learned_spells_not_hidden(self):
        self.assertClean(check_learned_not_hidden(_data()["rows_by_id"], _data()["learned"]))

    def test_retired_talents(self):
        package = _data()["package"]
        self.assertClean(check_retired_talents(package.talents, package.retired_talents))


# ---- negative fixtures: every check must fire on a minimal bad input ---------------------------------------

def _row(spell_id=1, **cols) -> dict:
    return {"ID": spell_id, **cols}


def _strike(spell_id=HEART_STRIKE, **cols) -> dict:
    return _row(spell_id, Effect_1=EFFECT_WEAPON_PERCENT_DAMAGE, Effect_2=EFFECT_NORMALIZED_WEAPON_DMG, **cols)


class DeathKnightDK0aNegativeTest(unittest.TestCase):
    def test_required_ids(self):
        self.assertEqual(len(check_required_ids({})), len(REQUIRED_IDS))
        self.assertEqual(check_required_ids({i: _row(i) for i in REQUIRED_IDS}), [])

    def test_weapon_strike_effects(self):
        self.assertEqual(check_weapon_strike_effects({HEART_STRIKE: _strike()}), [])
        self.assertEqual(check_weapon_strike_effects({FROST_STRIKE: _strike(FROST_STRIKE)}), [])
        default_chain = _strike(FROST_STRIKE, EffectChainAmplitude_3=1.0)
        self.assertEqual(check_weapon_strike_effects({FROST_STRIKE: default_chain}), [])
        for col, value in (("EffectBasePoints_3", 9), ("EffectDieSides_3", 1), ("ImplicitTargetA_3", 1),
                           ("EffectChainAmplitude_3", 0.5), ("EffectChainAmplitude_3", 5.0), ("Effect_3", 2)):
            self.assertEqual(len(check_weapon_strike_effects({HEART_STRIKE: _strike(**{col: value})})), 1, col)
        flat_first = _row(HEART_STRIKE, Effect_1=EFFECT_NORMALIZED_WEAPON_DMG, Effect_2=EFFECT_WEAPON_PERCENT_DAMAGE)
        self.assertEqual(len(check_weapon_strike_effects({HEART_STRIKE: flat_first})), 2)

    def test_death_strike(self):
        good = _row(DEATH_STRIKE, PowerType=6, ManaCost=400, RuneCostID=0, AttributesEx=DEATH_STRIKE_ATTR_EX,
                    Effect_3=EFFECT_DUMMY, EffectBasePoints_3=24, EffectRealPointsPerLevel_3=0.0)
        self.assertEqual(check_death_strike({DEATH_STRIKE: good}), [])
        for col, value in (("PowerType", 0), ("ManaCost", 0), ("RuneCostID", 1142), ("AttributesEx", 0x400),
                           ("Effect_3", 2), ("EffectBasePoints_3", 404), ("EffectRealPointsPerLevel_3", 37.667)):
            self.assertEqual(len(check_death_strike({DEATH_STRIKE: {**good, col: value}})), 1, col)

    def test_blood_presence(self):
        good = _row(BLOOD_PRESENCE, Attributes=0x29050010, AttributesEx=0x400, AttributesEx2=0x11)
        links = [{"spell_trigger": 48266, "spell_effect": 203000, "type": 2},
                 {"spell_trigger": 48266, "spell_effect": 57340, "type": 2},
                 {"spell_trigger": -48266, "spell_effect": -57340, "type": 0}]
        attrs = [{"spell_id": 48266, "attributes": 0x06000000}]
        self.assertEqual(check_blood_presence({BLOOD_PRESENCE: good}, links, attrs), [])
        cases = (
            ({**good, "Attributes": 0xA9050010}, links, attrs),
            ({**good, "AttributesEx": 0x80000400}, links, attrs),
            ({**good, "AttributesEx2": 0x1}, links, attrs),
            ({**good, "StartRecoveryTime": 1500}, links, attrs),
            ({**good, "StartRecoveryCategory": 133}, links, attrs),
            ({**good, "RuneCostID": 484}, links, attrs),
            (good, links, []),
            (good, links, [{"spell_id": 48266, "attributes": 0x02000000}]),
            (good, links[1:], attrs),
            (good, [links[0], links[2]], attrs),
            (good, links[:2], attrs),
            (good, [{**links[0], "type": 0}, *links[1:]], attrs),
        )
        for i, (row, ls, ca) in enumerate(cases):
            self.assertEqual(len(check_blood_presence({BLOOD_PRESENCE: row}, ls, ca)), 1, i)

    def test_crit_child(self):
        good = _row(CRIT_CHILD, EffectAura_1=187, EffectBasePoints_1=-1001, EffectAura_2=188, EffectBasePoints_2=-1001,
                    AttributesEx3=0x100000)
        self.assertEqual(check_crit_child({CRIT_CHILD: good}), [])
        self.assertEqual(len(check_crit_child({CRIT_CHILD: {**good, "EffectBasePoints_2": -1000}})), 1)
        self.assertEqual(len(check_crit_child({CRIT_CHILD: {**good, "EffectAura_1": 0}})), 1)
        self.assertEqual(len(check_crit_child({CRIT_CHILD: {**good, "AttributesEx3": 0}})), 1)

    def test_rune_tap_and_erw(self):
        tap = _row(RUNE_TAP, Effect_1=30, EffectMiscValue_1=6, EffectBasePoints_1=499)
        erw = _row(ERW, RecoveryTime=180000)
        self.assertEqual(check_rune_tap_and_erw({RUNE_TAP: tap, ERW: erw}), [])
        for col, value in (("Effect_1", 136), ("EffectMiscValue_1", 0), ("EffectBasePoints_1", 49)):
            self.assertEqual(len(check_rune_tap_and_erw({RUNE_TAP: {**tap, col: value}})), 1, col)
        self.assertEqual(len(check_rune_tap_and_erw({ERW: {**erw, "RecoveryTime": 300000}})), 1)

    def test_trainer_levels(self):
        trainers = [{"SpellId": 49143, "ReqLevel": 10, "TrainerId": 13}]
        self.assertEqual(check_trainer_levels({49143: _row(49143, SpellLevel=10)}, trainers), [])
        self.assertEqual(len(check_trainer_levels({49143: _row(49143, SpellLevel=75)}, trainers)), 1)
        self.assertEqual(check_trainer_levels({}, trainers), [])

    def test_expected_trainer_levels(self):
        trainers = [{"SpellId": i, "ReqLevel": lv} for i, lv in EXPECTED_TRAINER_LEVELS.items()]
        rows = {i: _row(i, SpellLevel=lv) for i, lv in EXPECTED_TRAINER_LEVELS.items()}
        self.assertEqual(check_expected_trainer_levels(rows, trainers), [])
        self.assertEqual(len(check_expected_trainer_levels(rows, trainers[1:])), 1)  # missing trainer row
        self.assertEqual(len(check_expected_trainer_levels(rows, [{**trainers[0], "ReqLevel": 15}, *trainers[1:]])), 1)
        self.assertEqual(len(check_expected_trainer_levels({**rows, ERW: _row(ERW, SpellLevel=75)}, trainers)), 1)

    def test_death_strike_effect_order(self):
        good = _row(DEATH_STRIKE, Effect_1=31, Effect_2=121)
        self.assertEqual(check_death_strike_effect_order({DEATH_STRIKE: good}), [])
        flipped = _row(DEATH_STRIKE, Effect_1=121, Effect_2=31)
        self.assertEqual(len(check_death_strike_effect_order({DEATH_STRIKE: flipped})), 2)

    def test_death_strike_heal(self):
        zeros = [{"entry": 45470, "direct_bonus": 0, "dot_bonus": 0, "ap_bonus": 0, "ap_dot_bonus": 0}]
        good = _row(45470, DefenseType=1)
        self.assertEqual(check_death_strike_heal({45470: good}, zeros), [])
        self.assertEqual(len(check_death_strike_heal({45470: _row(45470, DefenseType=0)}, zeros)), 1)
        self.assertEqual(len(check_death_strike_heal({45470: good}, [])), 1)
        self.assertEqual(len(check_death_strike_heal({45470: good}, [{**zeros[0], "direct_bonus": 1.0}])), 1)

    def test_forbidden_bits(self):
        for col, bit in (("SpellClassMask_1", m.FORBIDDEN_D0_B6), ("SpellClassMask_1", m.FORBIDDEN_D0_B22),
                         ("SpellClassMask_2", m.FORBIDDEN_D1_B11), ("SpellClassMask_2", m.FORBIDDEN_D1_B23),
                         ("SpellClassMask_3", m.FORBIDDEN_D2_B31), ("SpellClassMask_3", m.FORBIDDEN_D2_B1)):
            self.assertEqual(len(check_forbidden_bits({DEATHS_CARESS: _row(DEATHS_CARESS, **{col: bit})})), 1, col)
        clean = _row(DEATHS_CARESS, SpellClassMask_3=m.DEATHS_CARESS)
        self.assertEqual(check_forbidden_bits({DEATHS_CARESS: clean}), [])
        # stock-kept: the disease DoTs keep d2 b1; the same bit on a strike is wrong
        self.assertEqual(check_forbidden_bits({55095: _row(55095, SpellClassMask_3=m.FORBIDDEN_D2_B1)}), [])
        self.assertEqual(len(check_forbidden_bits({HEART_STRIKE: _row(HEART_STRIKE, SpellClassMask_3=0x2)})), 1)
        # an id outside DK0a is not judged
        self.assertEqual(check_forbidden_bits({48707: _row(48707, SpellClassMask_1=0x20000)}), [])
        self.assertEqual(len(check_forbidden_bits({HEART_STRIKE: _row(HEART_STRIKE, SpellClassMask_1=0x20000)})), 1)
        self.assertEqual(check_forbidden_bits({1: _row(1, SpellClassMask_3=m.FORBIDDEN_D2_B31)}), [])

    def test_deaths_caress(self):
        self.assertEqual(check_deaths_caress({DEATHS_CARESS: _row(DEATHS_CARESS, SpellClassMask_3=0x1000)}), [])
        for cols in ({"SpellClassMask_3": 0x1004}, {"SpellClassMask_3": 0x800}, {"SpellClassMask_3": 0x1000,
                                                                                  "SpellClassMask_1": 0x10}, {}):
            self.assertEqual(len(check_deaths_caress({DEATHS_CARESS: _row(DEATHS_CARESS, **cols)})), 1, cols)

    def test_learned_hidden(self):
        rows = {DEATHS_CARESS: _row(DEATHS_CARESS, Attributes=0x80)}
        self.assertEqual(len(check_learned_not_hidden(rows, {DEATHS_CARESS})), 1)
        self.assertEqual(check_learned_not_hidden(rows, set()), [])  # hidden helper nobody learns
        self.assertEqual(check_learned_not_hidden({CRIT_CHILD: _row(CRIT_CHILD, Attributes=0xC0)}, set()), [])
        self.assertEqual(check_learned_not_hidden({DEATHS_CARESS: _row(DEATHS_CARESS, Attributes=0x40)},
                                                  {DEATHS_CARESS}), [])

    def test_retired_talents(self):
        talents = [{"id": t, "tab_id": RETIRED_TAB} for t in RETIRED_TALENTS]
        retired = [{"id": t} for t in RETIRED_TALENTS]
        self.assertEqual(check_retired_talents(talents, retired), [])
        self.assertEqual(len(check_retired_talents([{**talents[0], "tab_id": 398}, *talents[1:]], retired)), 1)
        self.assertEqual(len(check_retired_talents(talents[1:], retired)), 1)
        self.assertEqual(len(check_retired_talents(talents, retired[1:])), 1)


# ---- lint row: DEATHKNIGHT_FAMILY_RULES (FAMILY-BITS s10.7) ------------------------------------------------

def _lint_row(spell_id=203001, **cols) -> dict:
    row = {"ID": spell_id, "SpellClassSet": 15}
    row.update(cols)
    return row


def _family(row, procs=None, rules=(lint.DEATHKNIGHT_FAMILY_RULES,)):
    return lint.check_family_bit_rules([{"name": "Test Spell"}], [row], procs, None, frozenset(), rules=rules)


class DeathKnightFamilyRulesTest(unittest.TestCase):
    def test_the_row_is_registered(self):
        rules = lint.DEATHKNIGHT_FAMILY_RULES
        self.assertIn(rules, lint.FAMILY_BIT_RULES)
        self.assertIn(lint.HUNTER_FAMILY_RULES, lint.FAMILY_BIT_RULES)
        self.assertIn(lint.SHAMAN_FAMILY_RULES, lint.FAMILY_BIT_RULES)
        self.assertEqual(rules.spell_class_set, 15)
        self.assertEqual(rules.forbidden_carrier_bits, (0x40, 0x800000, 0x80000000))
        self.assertEqual(rules.forbidden_reader_bits, (0, 0x400 | 0x800000 | 0x1000000, 0x80000000))
        self.assertEqual(rules.protected_bits, (0, 0, 0))
        self.assertEqual(rules.pet_required_bits, (0, 0, 0))

    def test_a_carrier_of_a_forbidden_bit_warns(self):
        for col, bit in (("SpellClassMask_3", 0x80000000), ("SpellClassMask_2", 0x800000), ("SpellClassMask_1", 0x40)):
            with self.subTest(col=col):
                warnings = _family(_lint_row(**{col: bit}))
                self.assertEqual(len(warnings), 1)
                self.assertIn("deathknight family-bit rule (b)", warnings[0])

    def test_allowed_bits_are_silent(self):
        for col, bit in (("SpellClassMask_3", m.DEATHS_CARESS), ("SpellClassMask_1", m.HEART_STRIKE),
                         ("SpellClassMask_2", 0x400), ("SpellClassMask_2", 0x1000000)):  # readers-only bits
            self.assertEqual(_family(_lint_row(**{col: bit})), [], col)

    def test_a_reader_of_a_forbidden_bit_warns(self):
        for col, bit in (("EffectSpellClassMaskA_3", 0x80000000), ("EffectSpellClassMaskB_2", 0x400),
                         ("EffectSpellClassMaskA_2", 0x800000), ("EffectSpellClassMaskC_2", 0x1000000)):
            with self.subTest(col=col):
                warnings = _family(_lint_row(**{col: bit}))
                self.assertEqual(len(warnings), 1)
                self.assertIn("deathknight family-bit rule (c)", warnings[0])

    def test_a_clean_reader_is_silent(self):
        self.assertEqual(_family(_lint_row(EffectSpellClassMaskA_1=m.HEART_STRIKE, EffectSpellClassMaskA_3=0x1000)), [])

    def test_custom_ids_and_the_class_set_only(self):
        self.assertEqual(_family(_lint_row(spell_id=48266, SpellClassMask_3=0x80000000)), [])  # stock id
        self.assertEqual(_family(_lint_row(SpellClassSet=11, SpellClassMask_3=0x80000000)), [])  # shaman spell
        self.assertEqual(len(_family(_lint_row(spell_id=200000, SpellClassMask_3=0x80000000))), 1)

    def test_a_declared_proc_reader_warns(self):
        procs = [{"SpellId": 203001, "SpellFamilyName": 15, "SpellFamilyMask0": 0, "SpellFamilyMask1": 0x1000000,
                  "SpellFamilyMask2": 0}]
        self.assertEqual(len(_family(_lint_row(), procs)), 1)
        self.assertEqual(_family(_lint_row(), [{**procs[0], "SpellFamilyMask1": 0x4}]), [])


if __name__ == "__main__":
    unittest.main()
