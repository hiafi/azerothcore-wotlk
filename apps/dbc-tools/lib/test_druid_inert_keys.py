"""
Druid rework - inert-key guard (druid-rework.CORE-AUDIT.md §4 "Inert-key list").

The core audit neutralizes ~20 stock druid hardcodes by making the data they key on permanently
absent from druid data, rather than deleting the hardcode itself (a deletion is invisible to
apps/merge-guard/merge_guard.py and would silently return if upstream moved the function - see
CORE-AUDIT's own top summary and .agents/docs/upstream-merge.md). This test loads the real druid
DSL (source/classes/druid/) and asserts none of those keys have been reintroduced.

Created by the Balance pass's WP-0 (druid-rework.PLAN.md §3.2/§5.1). Each stock hardcode is owned
by one spec's pass (CORE-AUDIT's "Spec" column: B/R/F) - its own marker stays live, legitimate
stock data until that spec's WP-A/WP-B actually neutralizes it, so a check for a Resto- or
Feral-owned row would wrongly fail during the Balance pass (this file lives under lib/, which PLAN
§5.3's pytest gate runs unscoped). Rows Balance itself owns (3, 4) are asserted for real right now;
rows owned by a later pass are `@unittest.skip`-guarded with the owning pass named in the reason -
that pass removes its own skip (not the whole test) once its WP-B lands, per CORE-AUDIT row X's
"Recommended" column. The two checks that hold regardless of pass order (nothing this rework mints
may reuse a retired icon/bit; the Improved Barkskin ids may never be *reassigned* to something else)
run unconditionally.

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_druid_inert_keys.py
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib import source, spell_tables, trainer_state  # noqa: E402
from lib.dsl import registry  # noqa: E402

TOOL_ROOT = Path(__file__).resolve().parents[1]
DRUID_DIR = TOOL_ROOT / "source" / "classes" / "druid"

APPLY_AURA_EFFECT_TYPE = 6  # EffectType.APPLY_AURA
DUMMY_AURA = 4  # AuraType.DUMMY
MOD_TOTAL_STAT_PERCENTAGE = 137  # AuraType.MOD_TOTAL_STAT_PERCENTAGE
MOD_SPELL_HEALING_OF_STAT_PERCENT = 175  # AuraType.MOD_SPELL_HEALING_OF_STAT_PERCENT
STAT_INTELLECT = 3
NOURISH_BIT = 0x2000000  # dword 2 - retired permanently, see _masks.py's NOURISH
AURA_STATE_SWIFTMEND = 15  # SharedDefines.h TargetAuraState raw column value

# This rework's own reserved id blocks (PLAN §4) - the only ranges a "never reassign" check needs
# to scan, since a legitimate *stock* row (untouched until its owning pass lands) is never in these
# ranges and must not trip a check meant to catch this rework's own mistakes.
CUSTOM_SPELL_ID_MIN = 200000  # PLAN §4.1 spell block 200000-209999
MINTED_TALENT_IDS = set(range(60026, 60070))  # PLAN §4.2 60026-60069 (Balance/Feral/Resto minted)


def _is_this_rework(entry_id: int) -> bool:
    return entry_id >= CUSTOM_SPELL_ID_MIN or entry_id in MINTED_TALENT_IDS


# DUMMY-aura icons whose stock hardcode is neutralized by moving the row's real effect off DUMMY
# entirely. Balance owns icons 109/1771 (CORE-AUDIT rows 3, 4 - Improved Faerie Fire, Improved
# Insect Swarm's Starfire crit); Feral owns 2859/1563 (rows 24, 35 - Rend and Tear, Predatory
# Strikes).
BALANCE_RETIRED_DUMMY_ICONS = {109, 1771}
FERAL_RETIRED_DUMMY_ICONS = {2859, 1563}

# Master Shapeshifter's stock GENERIC-family DUMMY hardcode (CORE-AUDIT row 16, icon 2851) - Resto.
RESTO_RETIRED_GENERIC_DUMMY_ICON = 2851

# Heart of the Wild / Survival of the Fittest / Nurturing Instinct form-boost hardcodes
# (CORE-AUDIT row 32, Feral): aura 137 keyed on icon 961 (any misc) or icon 240 with misc ==
# Intellect; aura 175 keyed on icon 2254.
FERAL_RETIRED_AURA_137_ICON_961 = 961
FERAL_RETIRED_AURA_137_ICON_240_MISC_INT = (240, STAT_INTELLECT)
FERAL_RETIRED_AURA_175_ICON_2254 = 2254

# Improved Barkskin's talent ranks (CORE-AUDIT row 18, Resto repurposes talent 2264 onto new ids
# 200598/200599) - "can never be true again" once Resto lands; until then these are still the live,
# legitimate stock Improved Barkskin ranks, so only "no *new* id ever reuses them" is checkable now.
IMPROVED_BARKSKIN_RANK_IDS = {63410, 63411}


def _has_dummy_aura(entry: dict) -> bool:
    for eff in entry.get("effects") or []:
        if eff is None:
            continue
        if eff.get("type") == APPLY_AURA_EFFECT_TYPE and eff.get("apply_aura") == DUMMY_AURA:
            return True
    return False


def _load_druid_entries():
    ids_cfg = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
    # Balance WP-A adds this package's first trained_by() calls (Starsurge/Mass Entanglement/Solar
    # Beam/Typhoon), which need a real TrainerIndex to validate their TrainerId - same loader
    # generate.py uses (a static scan of creature_default_trainer/creature_template/creature, no
    # live DB needed) - and its first spell_group()/spell_group_rule() calls (A7, PLAN §3 item 18),
    # which need the existing spell_group ids the same way.
    trainer_index = trainer_state.load_trainer_index()
    spell_table_index = spell_tables.load_spell_table_index()
    existing_group_ids = {key[0] for key in spell_table_index.live_keys("spell_group")}
    reg = registry.load_class_package(
        DRUID_DIR, ids_cfg=ids_cfg, trainer_index=trainer_index,
        existing_group_ids=existing_group_ids,
    )
    return reg.spells


class InertKeyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = _load_druid_entries()

    def test_balance_retired_dummy_icons_are_clear(self):
        # CORE-AUDIT rows 3/4 - Balance's own pass; must be true by Balance's WP-C.
        for entry in self.entries:
            if entry.get("spell_icon_id") in BALANCE_RETIRED_DUMMY_ICONS and _has_dummy_aura(entry):
                self.fail(f"spell {entry['id']} ({entry.get('name')}) still carries a DUMMY aura on Balance-retired icon {entry.get('spell_icon_id')} - CORE-AUDIT rows 3/4")

    @unittest.skip("Feral pass (CORE-AUDIT rows 24, 35) hasn't landed - Feral's own WP-B removes this skip")
    def test_feral_retired_dummy_icons_are_clear(self):
        for entry in self.entries:
            if entry.get("spell_icon_id") in FERAL_RETIRED_DUMMY_ICONS and _has_dummy_aura(entry):
                self.fail(f"spell {entry['id']} ({entry.get('name')}) still carries a DUMMY aura on Feral-retired icon {entry.get('spell_icon_id')} - CORE-AUDIT rows 24/35")

    @unittest.skip("Resto pass (CORE-AUDIT row 16) hasn't landed - Resto's own WP-B removes this skip")
    def test_resto_retired_generic_dummy_icon_is_clear(self):
        for entry in self.entries:
            if entry.get("spell_icon_id") == RESTO_RETIRED_GENERIC_DUMMY_ICON and _has_dummy_aura(entry):
                self.fail(f"spell {entry['id']} ({entry.get('name')}) reuses retired GENERIC DUMMY icon {RESTO_RETIRED_GENERIC_DUMMY_ICON} - CORE-AUDIT row 16")

    @unittest.skip("Feral pass (CORE-AUDIT row 32) hasn't landed - Feral's own WP-B removes this skip")
    def test_feral_retired_aura_137_or_175_markers_are_clear(self):
        for entry in self.entries:
            icon = entry.get("spell_icon_id")
            for eff in entry.get("effects") or []:
                if eff is None or eff.get("type") != APPLY_AURA_EFFECT_TYPE:
                    continue
                aura = eff.get("apply_aura")
                misc = eff.get("misc_value")
                if aura == MOD_TOTAL_STAT_PERCENTAGE and icon == FERAL_RETIRED_AURA_137_ICON_961:
                    self.fail(f"spell {entry['id']} reuses retired aura-137/icon-961 marker (Survival of the Fittest) - CORE-AUDIT row 32")
                if aura == MOD_TOTAL_STAT_PERCENTAGE and (icon, misc) == FERAL_RETIRED_AURA_137_ICON_240_MISC_INT:
                    self.fail(f"spell {entry['id']} reuses retired aura-137/icon-240/misc-INT marker (Heart of the Wild) - CORE-AUDIT row 32")
                if aura == MOD_SPELL_HEALING_OF_STAT_PERCENT and icon == FERAL_RETIRED_AURA_175_ICON_2254:
                    self.fail(f"spell {entry['id']} reuses retired aura-175/icon-2254 marker (Nurturing Instinct) - CORE-AUDIT row 32")

    def test_no_new_id_reuses_improved_barkskin_ranks(self):
        # Doesn't (yet) assert 63410/63411 are unreferenced - that's true only once Resto's WP-B
        # moves talent 2264 onto 200598/200599 (CORE-AUDIT row 18). What's checkable now, and
        # forever: nothing this rework mints collides with these ids.
        minted = MINTED_TALENT_IDS | {e["id"] for e in self.entries if e["id"] >= CUSTOM_SPELL_ID_MIN}
        reused = minted & IMPROVED_BARKSKIN_RANK_IDS
        self.assertFalse(reused, f"a newly-minted druid-rework id collides with Improved Barkskin's ranks: {reused} - CORE-AUDIT row 18")

    def test_nourish_bit_never_assigned_to_new_content(self):
        # The bit itself stays on stock rows (e.g. Spark of Nature 48435) until Resto's WP-A drops
        # Nourish - not a violation. What must never happen, from any pass, at any time: a *new*
        # druid-rework spell/talent carrying it.
        for entry in self.entries:
            if not _is_this_rework(entry["id"]):
                continue
            raw = entry.get("raw_overrides") or {}
            if raw.get("SpellClassMask_2", 0) & NOURISH_BIT:
                self.fail(f"new spell {entry['id']} sets the retired Nourish dword-2 bit on SpellClassMask_2 - CORE-AUDIT §4 / _masks.py NOURISH")
            for letter in ("A", "B", "C"):
                if raw.get(f"EffectSpellClassMask{letter}_2", 0) & NOURISH_BIT:
                    self.fail(f"new spell {entry['id']} sets the retired Nourish dword-2 bit on EffectSpellClassMask{letter}_2 - CORE-AUDIT §4 / _masks.py NOURISH")

    @unittest.skip("Resto pass (CORE-AUDIT row 19) hasn't landed - Resto's own WP-B removes this skip once it clears 18562's TargetAuraState to 0")
    def test_swiftmend_target_aura_state_cleared(self):
        for entry in self.entries:
            if entry["id"] != 18562:
                continue
            raw = entry.get("raw_overrides") or {}
            state = raw.get("TargetAuraStateID", raw.get("TargetAuraState"))
            if state == AURA_STATE_SWIFTMEND:
                self.fail("spell 18562 (Swiftmend) still has TargetAuraState=AURA_STATE_SWIFTMEND - CORE-AUDIT row 19 (Resto must clear this to 0)")


if __name__ == "__main__":
    unittest.main()
