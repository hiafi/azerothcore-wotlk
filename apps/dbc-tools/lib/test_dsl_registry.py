"""
Unit tests for `lib/dsl/registry.py` - Phase 1 of `.agents/plans/
spell-source-dsl/spell-source-dsl.PLAN.md`. Uses real temp `.py` files
(not mocks) since the thing under test *is* "import this file from disk and
see what it registered".

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_dsl_registry.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

TOOL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOL_ROOT))

from lib.dsl import model, registry  # noqa: E402

MAGE_FILE = '''
from lib.dsl.registry import spell, tab, talent

frostbolt = spell(id=116, name="Frostbolt", school=16, cast_time_ms=2000)

frost_tab = tab(id=60800, name="Frost", class_mask=128)

t = talent(id=60000, tab_id=frost_tab.id, tier=0, column=0, rank_spell_ids=[frostbolt.id])
'''

WARRIOR_FILE = '''
from lib.dsl.registry import spell

charge = spell(id=100, name="Charge", school=1)
'''

DUPLICATE_FILE = '''
from lib.dsl.registry import spell

impostor = spell(id=116, name="Not Actually Frostbolt", school=1)
'''

SKIPPED_FILE = '''
from lib.dsl.registry import spell

# If this ever gets loaded, it'll collide with mage.py's real Frostbolt (116)
# and the test would fail loudly instead of silently passing - that's the
# point: proves leading-underscore files are actually skipped, not merely
# assumed to be.
spell(id=116, name="Should never be imported", school=1)
'''


IDS_CFG = {"spell": {"start": 200000, "end": 209999}}

# A custom (in-reserved-block) spell ID, real cast_time_ms, correctly marked
# player_castable=True with a matching skill_line_ability id - the "did it
# correctly" case.
GRANTED_CUSTOM_CASTABLE = '''
from lib.dsl.registry import spell, tab, granted_by_talent

frost_tab = tab(id=60800, name="Frost", class_mask=128, skill_line=6)
frostbolt = spell(id=200001, name="Custom Frostbolt", school=16, cast_time_ms=2000)
granted_by_talent(
    id=60000, tab=frost_tab, tier=0, column=0,
    ranks=[frostbolt], player_castable=True, skill_line_ability_ids=[30400],
)
'''

# A reused stock spell ID (outside the reserved block) that "looks castable"
# (real cast_time_ms) but player_castable is left unset - must NOT raise,
# since a stock ID already has its own real SkillLineAbility row for free.
GRANTED_STOCK_ID_NO_DECISION_NEEDED = '''
from lib.dsl.registry import spell, tab, granted_by_talent

frost_tab = tab(id=60800, name="Frost", class_mask=128, skill_line=6)
frostbolt = spell(id=116, name="Frostbolt", school=16, cast_time_ms=2000)
granted_by_talent(id=60000, tab=frost_tab, tier=0, column=0, ranks=[frostbolt])
'''

# A bare-int rank (no Spell() declaration at all) mixed with a real one -
# the Phase 4 real-data case (some old stock talent ranks were never pulled
# into source). Must not crash, and must not need a decision for the bare
# int (only the real Spell still might, depending on its own shape).
GRANTED_BARE_INT_RANK_MIXED_WITH_SPELL = '''
from lib.dsl.registry import spell, tab, granted_by_talent

frost_tab = tab(id=60800, name="Frost", class_mask=128, skill_line=6)
frostbolt = spell(id=116, name="Frostbolt", school=16, cast_time_ms=2000)
granted_by_talent(id=60000, tab=frost_tab, tier=0, column=0, ranks=[29447, frostbolt])
'''

# A custom, castable-looking spell ID with player_castable left unset - the
# exact ambiguity that must hard-fail rather than silently default.
GRANTED_CUSTOM_AMBIGUOUS = '''
from lib.dsl.registry import spell, tab, granted_by_talent

frost_tab = tab(id=60800, name="Frost", class_mask=128, skill_line=6)
frostbolt = spell(id=200002, name="Custom Frostbolt", school=16, cast_time_ms=2000)
granted_by_talent(id=60000, tab=frost_tab, tier=0, column=0, ranks=[frostbolt])
'''

# A custom, castable-looking spell ID explicitly marked player_castable=False
# (a hidden triggered effect that happens to have a cast_time/cooldown for
# some other reason) - must NOT raise and must NOT register a row.
GRANTED_CUSTOM_NOT_CASTABLE = '''
from lib.dsl.registry import spell, tab, granted_by_talent

frost_tab = tab(id=60800, name="Frost", class_mask=128, skill_line=6)
icicles = spell(id=200003, name="Icicles", school=16, cast_time_ms=1500)
granted_by_talent(id=60000, tab=frost_tab, tier=0, column=0,
                   ranks=[icicles], player_castable=False)
'''

# A custom, instant/free/no-cooldown spell (cast_time_ms=cooldown_ms=0) that
# nonetheless has a real mana_cost_pct - the exact shape `looks_player_castable`
# used to miss (see its docstring: Frost Nova/Blink/Arcane Intellect/... all
# have this shape for real). Must still be treated as ambiguous/castable-
# looking, not silently passed through as "doesn't look castable".
GRANTED_CUSTOM_FREE_INSTANT_WITH_MANA_COST = '''
from lib.dsl.registry import spell, tab, granted_by_talent

frost_tab = tab(id=60800, name="Frost", class_mask=128, skill_line=6)
buff = spell(id=200005, name="Custom Armor", school=16, mana_cost_pct=25)
granted_by_talent(id=60000, tab=frost_tab, tier=0, column=0, ranks=[buff])
'''

# player_castable=True but no skill_line_ability_ids entry for the rank.
GRANTED_CUSTOM_MISSING_SLA_ID = '''
from lib.dsl.registry import spell, tab, granted_by_talent

frost_tab = tab(id=60800, name="Frost", class_mask=128, skill_line=6)
frostbolt = spell(id=200004, name="Custom Frostbolt", school=16, cast_time_ms=2000)
granted_by_talent(id=60000, tab=frost_tab, tier=0, column=0,
                   ranks=[frostbolt], player_castable=True)
'''


class GrantedByTalentTest(unittest.TestCase):
    def _load(self, source: str, ids_cfg=IDS_CFG):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "mage.py"
            path.write_text(source)
            return registry.load_class_file(path, ids_cfg=ids_cfg)

    def test_derives_skill_line_ability_for_custom_castable_spell(self):
        reg = self._load(GRANTED_CUSTOM_CASTABLE)
        self.assertEqual(len(reg.skill_line_abilities), 1)
        sla = reg.skill_line_abilities[0]
        self.assertEqual(sla["id"], 30400)
        self.assertEqual(sla["skill_line"], 6)
        self.assertEqual(sla["spell_id"], 200001)
        self.assertEqual(sla["class_mask"], 128)

    def test_stock_id_needs_no_decision(self):
        reg = self._load(GRANTED_STOCK_ID_NO_DECISION_NEEDED)
        self.assertEqual(reg.skill_line_abilities, [])

    def test_bare_int_rank_mixed_with_spell_does_not_crash(self):
        reg = self._load(GRANTED_BARE_INT_RANK_MIXED_WITH_SPELL)
        self.assertEqual(reg.talents[0]["rank_spell_ids"], [29447, 116])
        self.assertEqual(reg.skill_line_abilities, [])

    def test_custom_castable_ambiguous_raises(self):
        with self.assertRaises(registry.MissingSkillLineAbilityError):
            self._load(GRANTED_CUSTOM_AMBIGUOUS)

    def test_custom_free_instant_with_mana_cost_is_ambiguous_raises(self):
        with self.assertRaises(registry.MissingSkillLineAbilityError):
            self._load(GRANTED_CUSTOM_FREE_INSTANT_WITH_MANA_COST)

    def test_custom_marked_not_castable_is_skipped(self):
        reg = self._load(GRANTED_CUSTOM_NOT_CASTABLE)
        self.assertEqual(reg.skill_line_abilities, [])

    def test_missing_skill_line_ability_id_raises(self):
        with self.assertRaises(ValueError):
            self._load(GRANTED_CUSTOM_MISSING_SLA_ID)

    def test_missing_ids_cfg_raises(self):
        with self.assertRaises(RuntimeError):
            self._load(GRANTED_CUSTOM_CASTABLE, ids_cfg=None)


class FakeTrainerIndex:
    """Duck-typed stand-in for lib.trainer_state.TrainerIndex - registry.py
    never imports the real class (see load_class_file's docstring), so a
    fake with the same two-member surface is all trained_by() needs to
    exercise without dragging in a real SQL-file scan."""

    def __init__(self, dead_trainer_ids: set[int] = frozenset(), existing: dict | None = None):
        self._dead = dead_trainer_ids
        self.existing_trainer_spells = existing or {}

    def trainer_problems(self, trainer_id: int) -> list[str]:
        return [f"TrainerId {trainer_id} is dead"] if trainer_id in self._dead else []


TRAINED_BY_FILE = '''
from lib.dsl.registry import spell, trained_by

frostbolt = spell(id=200005, name="Frostbolt", school=16, cast_time_ms=2000)
trained_by(frostbolt, trainer_id=13, req_level=20, money_cost=500)
'''

TRAINED_BY_DEAD_TRAINER_FILE = '''
from lib.dsl.registry import spell, trained_by

frostbolt = spell(id=200006, name="Frostbolt", school=16, cast_time_ms=2000)
trained_by(frostbolt, trainer_id=666, req_level=20)
'''


class TrainedByTest(unittest.TestCase):
    def _load(self, source: str, trainer_index):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "mage.py"
            path.write_text(source)
            return registry.load_class_file(path, trainer_index=trainer_index)

    def test_registers_trainer_spell_row_for_a_live_trainer(self):
        reg = self._load(TRAINED_BY_FILE, FakeTrainerIndex())
        self.assertEqual(len(reg.trainer_spells), 1)
        row = reg.trainer_spells[0]
        self.assertEqual(row["TrainerId"], 13)
        self.assertEqual(row["SpellId"], 200005)
        self.assertEqual(row["MoneyCost"], 500)
        self.assertEqual(row["ReqLevel"], 20)
        self.assertEqual(row["id"], "13:200005")

    def test_dead_trainer_raises(self):
        with self.assertRaises(registry.DeadTrainerError):
            self._load(TRAINED_BY_DEAD_TRAINER_FILE, FakeTrainerIndex(dead_trainer_ids={666}))

    def test_missing_trainer_index_raises(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "mage.py"
            path.write_text(TRAINED_BY_FILE)
            with self.assertRaises(RuntimeError):
                registry.load_class_file(path)  # no trainer_index passed


class LooksPlayerCastableTest(unittest.TestCase):
    """Real shapes found via split_class_file.py misfiling ~40 real Mage
    spells into the trigger-only bucket - see looks_player_castable's
    docstring."""

    def test_real_cast_time_is_castable(self):
        self.assertTrue(registry.looks_player_castable(model.Spell(id=1, name="x", cast_time_ms=2000)))

    def test_plain_cooldown_is_castable(self):
        self.assertTrue(registry.looks_player_castable(model.Spell(id=1, name="x", cooldown_ms=120000)))

    def test_category_cooldown_only_is_castable(self):
        # Frost Nova's real shape: cast_time_ms=cooldown_ms=0, cooldown lives in
        # category_cooldown_ms instead.
        self.assertTrue(
            registry.looks_player_castable(model.Spell(id=122, name="Frost Nova", category_cooldown_ms=25000))
        )

    def test_mana_cost_pct_only_is_castable(self):
        # Arcane Intellect's real shape: instant, no cooldown at all, only a mana cost.
        self.assertTrue(
            registry.looks_player_castable(model.Spell(id=1459, name="Arcane Intellect", mana_cost_pct=31))
        )

    def test_mana_cost_only_is_castable(self):
        self.assertTrue(registry.looks_player_castable(model.Spell(id=1, name="x", mana_cost=15)))

    def test_all_zero_is_not_castable(self):
        # Arcane Blast's own debuff (36032): instant, free, no cooldown of any kind - a real
        # trigger-only spell, not a missed castable one.
        self.assertFalse(registry.looks_player_castable(model.Spell(id=36032, name="Arcane Blast")))

    def test_passive_overrides_everything_else(self):
        self.assertFalse(
            registry.looks_player_castable(
                model.Spell(id=1, name="x", cast_time_ms=2000, mana_cost_pct=10, attributes=0x40)
            )
        )


class RegistryTest(unittest.TestCase):
    def test_spell_call_outside_load_raises(self):
        with self.assertRaises(RuntimeError):
            registry.spell(id=1, name="Nothing")

    def test_load_class_file_collects_declarations(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "mage.py"
            path.write_text(MAGE_FILE)
            reg = registry.load_class_file(path)
        self.assertEqual([e["id"] for e in reg.spells], [116])
        self.assertEqual([e["id"] for e in reg.tabs], [60800])
        self.assertEqual([e["id"] for e in reg.talents], [60000])
        self.assertEqual(reg.talents[0]["tab_id"], 60800)

    def test_active_registry_cleared_after_load(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "mage.py"
            path.write_text(MAGE_FILE)
            registry.load_class_file(path)
        self.assertIsNone(registry._active)

    def test_load_classes_dir_merges_multiple_files(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "mage.py").write_text(MAGE_FILE)
            (Path(d) / "warrior.py").write_text(WARRIOR_FILE)
            merged = registry.load_classes_dir(Path(d))
        self.assertEqual(sorted(e["id"] for e in merged["spells"]), [100, 116])
        self.assertEqual([e["id"] for e in merged["tabs"]], [60800])

    def test_load_classes_dir_skips_underscore_files(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "mage.py").write_text(MAGE_FILE)
            (Path(d) / "_example.py").write_text(SKIPPED_FILE)
            merged = registry.load_classes_dir(Path(d))
        self.assertEqual(len(merged["spells"]), 1)

    def test_load_classes_dir_missing_directory_returns_empty(self):
        merged = registry.load_classes_dir(Path("/nonexistent/does/not/exist"))
        self.assertEqual(merged, {key: [] for key in registry.MERGE_KEYS})

    def test_load_classes_dir_duplicate_id_across_files_raises(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "mage.py").write_text(MAGE_FILE)
            (Path(d) / "zzz_conflict.py").write_text(DUPLICATE_FILE)
            with self.assertRaises(registry.DuplicateIdError):
                registry.load_classes_dir(Path(d))


# Multi-file (directory-per-class) layout fixtures - "backward" reference
# (talents.py imports from spells.py, which is loaded first alphabetically)
# and "forward" (spells.py's own trigger_spell references a spell declared in
# trigger_spells.py, which sorts *after* it) both need to resolve, which is
# the entire point of `load_class_package` using real Python imports instead
# of the single-file loader's "must be defined earlier in this file" rule.
PACKAGE_SPELLS_FILE = '''
from lib.dsl import Effect, EffectType
from lib.dsl.registry import spell
from .mage_trigger_spells import arcane_blast_debuff

arcane_blast = spell(
    id=30451, name="Arcane Blast", school=16, cast_time_ms=2500,
    effects=[Effect(type=EffectType.TRIGGER_SPELL, trigger_spell=arcane_blast_debuff.id)],
)
'''

PACKAGE_TRIGGER_SPELLS_FILE = '''
from lib.dsl.registry import spell

arcane_blast_debuff = spell(id=36032, name="Arcane Blast", school=16)
'''

PACKAGE_TALENTS_FILE = '''
from lib.dsl.registry import tab, talent
from .mage_spells import arcane_blast

arcane_tab = tab(id=81, name="Arcane", class_mask=128)
t = talent(id=60000, tab_id=arcane_tab.id, tier=0, column=0, rank_spell_ids=[arcane_blast.id])
'''


class LoadClassPackageTest(unittest.TestCase):
    def _write_mage_package(self, d: str) -> Path:
        pkg = Path(d) / "mage"
        pkg.mkdir()
        (pkg / "mage_spells.py").write_text(PACKAGE_SPELLS_FILE)
        (pkg / "mage_trigger_spells.py").write_text(PACKAGE_TRIGGER_SPELLS_FILE)
        (pkg / "mage_talents.py").write_text(PACKAGE_TALENTS_FILE)
        return pkg

    def test_cross_file_references_resolve_both_directions(self):
        with tempfile.TemporaryDirectory() as d:
            pkg = self._write_mage_package(d)
            reg = registry.load_class_package(pkg)
        ids = sorted(e["id"] for e in reg.spells)
        self.assertEqual(ids, [30451, 36032])
        arcane_blast = next(e for e in reg.spells if e["id"] == 30451)
        self.assertEqual(arcane_blast["effect1"]["trigger_spell"], 36032)
        self.assertEqual([e["id"] for e in reg.talents], [60000])
        self.assertEqual(reg.talents[0]["rank_spell_ids"], [30451])

    def test_active_registry_cleared_after_load(self):
        with tempfile.TemporaryDirectory() as d:
            pkg = self._write_mage_package(d)
            registry.load_class_package(pkg)
        self.assertIsNone(registry._active)

    def test_sys_modules_has_no_leftover_entries(self):
        with tempfile.TemporaryDirectory() as d:
            pkg = self._write_mage_package(d)
            before = set(sys.modules)
            registry.load_class_package(pkg)
            after = set(sys.modules)
        self.assertEqual(before, after)

    def test_repeated_load_in_same_process_is_fresh(self):
        # Two loads of the same directory in one process must not silently
        # reuse a cached module (a stale `arcane_blast_debuff` object from
        # the first load would still work by accident; a *changed* file
        # between loads must actually take effect).
        with tempfile.TemporaryDirectory() as d:
            pkg = self._write_mage_package(d)
            reg1 = registry.load_class_package(pkg)
            (pkg / "mage_trigger_spells.py").write_text(
                PACKAGE_TRIGGER_SPELLS_FILE.replace("36032", "99999")
            )
            reg2 = registry.load_class_package(pkg)
        self.assertEqual(
            next(e for e in reg1.spells if e["name"] == "Arcane Blast" and e["id"] == 30451)[
                "effect1"
            ]["trigger_spell"],
            36032,
        )
        self.assertEqual(
            next(e for e in reg2.spells if e["name"] == "Arcane Blast" and e["id"] == 30451)[
                "effect1"
            ]["trigger_spell"],
            99999,
        )

    def test_load_classes_dir_supports_directory_and_file_side_by_side(self):
        with tempfile.TemporaryDirectory() as d:
            self._write_mage_package(d)
            (Path(d) / "warrior.py").write_text(WARRIOR_FILE)
            merged = registry.load_classes_dir(Path(d))
        self.assertEqual(sorted(e["id"] for e in merged["spells"]), [100, 30451, 36032])
        self.assertEqual([e["id"] for e in merged["talents"]], [60000])

    def test_duplicate_id_across_package_and_file_raises(self):
        with tempfile.TemporaryDirectory() as d:
            self._write_mage_package(d)
            (Path(d) / "zzz_conflict.py").write_text(
                'from lib.dsl.registry import spell\nspell(id=30451, name="Impostor", school=1)\n'
            )
            with self.assertRaises(registry.DuplicateIdError):
                registry.load_classes_dir(Path(d))


# ---------------------------------------------------------------------------
# WP-T (.agents/plans/druid-rework/druid-rework.WP-T-HANDOFF.md, PLAN B11/§5.0):
# linked_spell/spell_group/spell_group_rule/custom_attr/shapeshift_form and
# their declared-removal counterparts.
# ---------------------------------------------------------------------------

WP_T_IDS_CFG = {"spell_group": {"start": 1200, "end": 1299}}

STOCK_SHAPESHIFT_INDEX = {
    5: {
        "ID": 5, "BonusActionBar": 0, "Name_Lang_enUS": "Bear Form", "Flags": 728,
        "CreatureType": 1, "AttackIconID": 496, "CombatRoundTime": 2500,
        "CreatureDisplayID_1": 2281, "CreatureDisplayID_2": 0,
        "CreatureDisplayID_3": 0, "CreatureDisplayID_4": 0,
        "PresetSpellID_1": 0, "PresetSpellID_2": 0, "PresetSpellID_3": 0, "PresetSpellID_4": 0,
        "PresetSpellID_5": 0, "PresetSpellID_6": 0, "PresetSpellID_7": 0, "PresetSpellID_8": 0,
    },
}


def _load_wp_t(source: str, **kwargs) -> registry.Registry:
    kwargs.setdefault("ids_cfg", WP_T_IDS_CFG)
    kwargs.setdefault("existing_group_ids", {1054, 1016})
    kwargs.setdefault("shapeshift_index", STOCK_SHAPESHIFT_INDEX)
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "druid.py"
        path.write_text(source)
        return registry.load_class_file(path, **kwargs)


class LinkedSpellTest(unittest.TestCase):
    def test_declares_row_with_default_comment(self):
        reg = _load_wp_t('from lib.dsl.registry import linked_spell\nlinked_spell(200326, 57865, 2)\n')
        (row,) = reg.linked_spells
        self.assertEqual((row["spell_trigger"], row["spell_effect"], row["type"]), (200326, 57865, 2))
        self.assertTrue(row["comment"])
        self.assertEqual(row["id"], "200326:57865:2")

    def test_negative_trigger_with_type_zero_is_on_aura_removal(self):
        # type=0's negative trigger is the only place a negative trigger means anything -
        # SpellAuras.cpp looks this up via GetSpellLinked(-GetId()) when the aura is removed.
        reg = _load_wp_t('from lib.dsl.registry import linked_spell\nlinked_spell(-33891, 200500, 0)\n')
        (row,) = reg.linked_spells
        self.assertEqual((row["spell_trigger"], row["spell_effect"], row["type"]), (-33891, 200500, 0))

    def test_negative_effect_with_type_two_means_immunity_not_removal(self):
        # type=2's negative effect grants/revokes immunity (ApplySpellImmune), verified against
        # SpellAuras.cpp's HandleAuraSpecificMods - NOT "remove that aura", which is type=0's
        # negative-trigger behavior above, a different type entirely.
        reg = _load_wp_t('from lib.dsl.registry import linked_spell\nlinked_spell(200326, -57865, 2)\n')
        (row,) = reg.linked_spells
        self.assertEqual((row["spell_trigger"], row["spell_effect"], row["type"]), (200326, -57865, 2))

    def test_negative_trigger_with_type_one_raises(self):
        # A dead row: no engine call site for type 1/2 ever looks up a negative-based key -
        # SpellMgr::LoadSpellLinked only shifts a *positive* trigger for those types.
        with self.assertRaises(ValueError):
            _load_wp_t('from lib.dsl.registry import linked_spell\nlinked_spell(-7943, 1, 1)\n')

    def test_negative_trigger_with_type_two_raises(self):
        with self.assertRaises(ValueError):
            _load_wp_t('from lib.dsl.registry import linked_spell\nlinked_spell(-200326, -57865, 2)\n')

    def test_invalid_type_raises(self):
        with self.assertRaises(ValueError):
            _load_wp_t('from lib.dsl.registry import linked_spell\nlinked_spell(1, 2, 3)\n')

    def test_empty_comment_is_not_written_as_literal_empty_string(self):
        # comment is NOT NULL text; an explicit empty string must fall back to the auto-generated
        # description the same way omitting it entirely does, not render as NULL.
        reg = _load_wp_t('from lib.dsl.registry import linked_spell\nlinked_spell(1, 2, 0, comment="")\n')
        self.assertTrue(reg.linked_spells[0]["comment"])

    def test_unlink_spell_declares_removal(self):
        reg = _load_wp_t('from lib.dsl.registry import unlink_spell\nunlink_spell(200326, 57865, 2)\n')
        (row,) = reg.linked_spell_removals
        self.assertEqual((row["spell_trigger"], row["spell_effect"], row["type"]), (200326, 57865, 2))

    def test_unlink_spell_negative_trigger_with_nonzero_type_raises(self):
        with self.assertRaises(ValueError):
            _load_wp_t('from lib.dsl.registry import unlink_spell\nunlink_spell(-200326, 57865, 1)\n')


class SpellGroupTest(unittest.TestCase):
    def test_fresh_id_from_reserved_block_is_accepted(self):
        reg = _load_wp_t('from lib.dsl.registry import spell_group\nspell_group(1200, 50171, 50172)\n')
        self.assertEqual(
            [(r["id"], r["spell_id"]) for r in reg.spell_groups], [(1200, 50171), (1200, 50172)]
        )

    def test_adding_a_member_to_a_stock_group_is_accepted(self):
        # 1054 is not in the reserved block, but is passed as an existing (stock) group id -
        # "adding members to stock groups like 1054 or 1016 is legitimate" per the handoff.
        reg = _load_wp_t('from lib.dsl.registry import spell_group\nspell_group(1054, 200001)\n')
        self.assertEqual(reg.spell_groups[0]["id"], 1054)

    def test_unknown_group_id_raises(self):
        with self.assertRaises(ValueError):
            _load_wp_t('from lib.dsl.registry import spell_group\nspell_group(999999, 1)\n')

    def test_negative_member_id_is_a_nested_group_reference_not_rejected(self):
        reg = _load_wp_t('from lib.dsl.registry import spell_group\nspell_group(1200, -1016)\n')
        self.assertEqual(reg.spell_groups[0]["spell_id"], -1016)

    def test_accepts_a_spell_object_member_not_just_a_bare_int(self):
        # Regression guard: every other helper here normalizes a Spell|int member through
        # _spell_id_of - spell_group() didn't, so a real Spell object (the normal, idiomatic way
        # the rest of the DSL references a declared spell) rendered as its dataclass repr instead
        # of an int.
        reg = _load_wp_t(
            'from lib.dsl.registry import spell, spell_group\n'
            'moonfire = spell(id=200500, name="Moonfire")\n'
            'spell_group(1200, moonfire)\n'
        )
        self.assertEqual(reg.spell_groups[0]["spell_id"], 200500)

    def test_two_members_of_the_same_group_do_not_collide_across_files(self):
        # Regression guard for the entry["id"] == group_id collision: spell_group's real SQL
        # column IS `id`, so without `_dedup_id` two different files each adding a member to the
        # same group would falsely look like the same declaration twice.
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "a.py").write_text(
                'from lib.dsl.registry import spell_group\nspell_group(1054, 1)\n'
            )
            (Path(d) / "b.py").write_text(
                'from lib.dsl.registry import spell_group\nspell_group(1054, 2)\n'
            )
            merged = registry.load_classes_dir(
                Path(d), ids_cfg=WP_T_IDS_CFG, existing_group_ids={1054},
            )
        self.assertEqual(sorted(r["spell_id"] for r in merged["spell_groups"]), [1, 2])

    def test_missing_existing_group_ids_raises(self):
        with self.assertRaises(RuntimeError):
            _load_wp_t(
                'from lib.dsl.registry import spell_group\nspell_group(1054, 1)\n',
                existing_group_ids=None,
            )

    def test_leave_spell_group_declares_removal_with_no_id_validation(self):
        # Removing never mints - a removal for a group id outside both the reserved block and
        # existing_group_ids must not raise (there's nothing to "mint" here).
        reg = _load_wp_t(
            'from lib.dsl.registry import leave_spell_group\nleave_spell_group(999999, 1)\n',
            existing_group_ids=set(),
        )
        self.assertEqual(reg.spell_group_removals[0], {"id": 999999, "spell_id": 1, "_dedup_id": "999999:1"})


class SpellGroupRuleTest(unittest.TestCase):
    def test_declares_row(self):
        reg = _load_wp_t(
            'from lib.dsl.registry import spell_group_rule\nspell_group_rule(1200, 1, "test")\n'
        )
        (row,) = reg.spell_group_rules
        self.assertEqual((row["group_id"], row["stack_rule"], row["description"]), (1200, 1, "test"))

    def test_invalid_stack_rule_raises(self):
        with self.assertRaises(ValueError):
            _load_wp_t('from lib.dsl.registry import spell_group_rule\nspell_group_rule(1200, 99)\n')

    def test_unknown_group_id_raises(self):
        with self.assertRaises(ValueError):
            _load_wp_t('from lib.dsl.registry import spell_group_rule\nspell_group_rule(999999, 1)\n')

    def test_default_description_is_never_a_literal_empty_string(self):
        # description is `varchar(150) NOT NULL DEFAULT ''`, but sql_out._sql_literal renders ""
        # the same as NULL - a constraint violation under strict SQL mode. The signature's own
        # default (description="") must not reach the row as a literal empty string.
        reg = _load_wp_t('from lib.dsl.registry import spell_group_rule\nspell_group_rule(1200, 1)\n')
        self.assertTrue(reg.spell_group_rules[0]["description"])


class CustomAttrTest(unittest.TestCase):
    def test_declares_row(self):
        reg = _load_wp_t('from lib.dsl.registry import custom_attr\ncustom_attr(200425, 1)\n')
        (row,) = reg.custom_attrs
        self.assertEqual((row["spell_id"], row["attributes"]), (200425, 1))


class ScriptAndTrainerRemovalTest(unittest.TestCase):
    def test_unbind_script_declares_removal(self):
        reg = _load_wp_t(
            'from lib.dsl.registry import unbind_script\n'
            'unbind_script(69366, "spell_dru_moonkin_form_passive")\n'
        )
        (row,) = reg.script_removals
        self.assertEqual((row["spell_id"], row["ScriptName"]), (69366, "spell_dru_moonkin_form_passive"))

    def test_untrain_declares_one_row_per_trainer(self):
        reg = _load_wp_t('from lib.dsl.registry import untrain\nuntrain(50464, [212, 213])\n')
        self.assertEqual(
            sorted((r["TrainerId"], r["SpellId"]) for r in reg.trainer_removals),
            [(212, 50464), (213, 50464)],
        )

    def test_untrain_requires_at_least_one_trainer(self):
        with self.assertRaises(ValueError):
            _load_wp_t('from lib.dsl.registry import untrain\nuntrain(50464, [])\n')


class ShapeshiftFormTest(unittest.TestCase):
    def test_full_row_override_keeps_stock_columns_and_changes_named_ones(self):
        reg = _load_wp_t(
            'from lib.dsl.registry import shapeshift_form\nshapeshift_form(5, attackSpeed=3500)\n'
        )
        (row,) = reg.shapeshift_forms
        self.assertEqual(row["CombatRoundTime"], 3500)  # changed
        self.assertEqual(row["Name_Lang_enUS"], "Bear Form")  # kept from stock
        self.assertEqual(row["CreatureDisplayID_1"], 2281)  # kept from stock
        self.assertEqual(row["ID"], 5)
        self.assertEqual(row["id"], 5)

    def test_real_sql_column_name_also_accepted(self):
        reg = _load_wp_t(
            'from lib.dsl.registry import shapeshift_form\nshapeshift_form(5, CombatRoundTime=3500)\n'
        )
        self.assertEqual(reg.shapeshift_forms[0]["CombatRoundTime"], 3500)

    def test_unknown_form_id_raises(self):
        with self.assertRaises(ValueError):
            _load_wp_t('from lib.dsl.registry import shapeshift_form\nshapeshift_form(999, attackSpeed=1)\n')

    def test_unknown_column_raises(self):
        with self.assertRaises(KeyError):
            _load_wp_t('from lib.dsl.registry import shapeshift_form\nshapeshift_form(5, notAColumn=1)\n')

    def test_missing_shapeshift_index_raises(self):
        with self.assertRaises(RuntimeError):
            _load_wp_t(
                'from lib.dsl.registry import shapeshift_form\nshapeshift_form(5, attackSpeed=1)\n',
                shapeshift_index=None,
            )

    def test_empty_shapeshift_index_raises_runtime_error_not_misleading_value_error(self):
        # An empty (but non-None) index - the real symptom of SpellShapeshiftForm.dbc not being
        # extracted on this checkout - must not be misreported as "not a real shapeshift form id"
        # (a bad form_id), which points the author at the wrong problem entirely.
        with self.assertRaises(RuntimeError):
            _load_wp_t(
                'from lib.dsl.registry import shapeshift_form\nshapeshift_form(5, attackSpeed=1)\n',
                shapeshift_index={},
            )


if __name__ == "__main__":
    unittest.main()
