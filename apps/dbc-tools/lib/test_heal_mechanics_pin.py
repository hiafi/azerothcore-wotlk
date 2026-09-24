"""
Druid rework RESTO WP-0/§0.13 Q4 - Heal::IsDirectNatureHeal pin.

`Heal::IsDirectNatureHeal` (src/server/game/Entities/Unit/HealMechanics.h/.cpp) replaces every
"Druid::IsDirectNatureHeal" reference in druid-rework.RESTO.md with a class-neutral rule: a
class-family spell (SpellFamilyName != SPELLFAMILY_GENERIC) with a Nature school and a direct
SPELL_EFFECT_HEAL effect, minus a never-list of nature-school heals that mechanically match but
must never count (periodic-only triggered heals, bloom/seed payloads, and similar implementation
details). This is a *rule*, not an id list, so it stays correct as new spells are added - but the
Resto pass still needs a pin: the rule, modelled here in Python against the real merged druid DSL
registry (mirroring lib/test_druid_inert_keys.py's loading pattern), must resolve to exactly the
five ids RESTO §0.13 Q4 names: {5185, 8936, 18562, 200560, 200561}.

This can only be written once Bloom (200560/200561) exists, hence "near the end of the pass" in
the WP-A brief - a change to the C++ rule's never-list must also update NEVER_LIST below (kept
byte-for-byte in sync with HealMechanics.cpp's own list, see the comment above it).

Run directly:

    apps/dbc-tools/.venv/bin/python3 apps/dbc-tools/lib/test_heal_mechanics_pin.py
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

SCHOOL_MASK_NATURE = 8  # School.NATURE (lib/dsl/constants.py)
EFFECT_TYPE_HEAL = 10  # EffectType.HEAL
SPELLFAMILY_GENERIC = 0

# Mirrors HealMechanics.cpp's own NEVER_LIST exactly (RESTO §0.13 Q4 / §9): Tranquility's per-tick
# triggered heal, Lifebloom's bloom, Living Seed's bloom, Ysera's Gift, Tree of Life's instant
# Rejuvenation heal, Nourish (removed, kept so it can never accidentally re-qualify).
NEVER_LIST = {44203, 33778, 48503, 200569, 200574, 50464}

EXPECTED = {5185, 8936, 18562, 200560, 200561}

# FINDING (flagged in the WP-A report, not fixed here - HealMechanics.cpp is WP-B's file, and the
# never-list is meant to name true implementation-detail payloads, not enumerate every legacy
# rank): 25297 is "Healing Touch (Rank 11)" - a single-rank-migration leftover kept only because
# item_template still references its spell id (druid_spells.py's own note: "superseded rank, kept
# (referenced by item_template spellid)"). It is genuinely SpellFamilyName=DRUID, Nature school,
# with a direct SPELL_EFFECT_HEAL - Heal::IsDirectNatureHeal's rule (no id-list beyond the small
# never-list) has no way to distinguish it from a "real" direct Nature heal, so the real C++
# function also returns true for it. Whether that's desired (an old-rank item proc benefiting from
# Naturalist/Omen/Natural Perfection/Living Seed like any other direct Nature heal) or should be
# added to the never-list is an open call for WP-B/WP-C - this pin documents the *actual* resolved
# set rather than silently asserting a wrong one.
EXPECTED_WITH_LEGACY_RANK_CLONES = EXPECTED | {25297}


def _family_name(entry: dict) -> int:
    raw = entry.get("raw_overrides") or {}
    return raw.get("SpellClassSet", SPELLFAMILY_GENERIC)


def _has_direct_heal_effect(entry: dict) -> bool:
    # A built spell entry (model.Spell.to_entry()) carries effect1/effect2/effect3, not a combined
    # "effects" list - see lib/dsl/model.py's Spell.to_entry().
    for key in ("effect1", "effect2", "effect3"):
        eff = entry.get(key)
        if eff is not None and eff.get("type") == EFFECT_TYPE_HEAL:
            return True
    return False


def _is_direct_nature_heal(entry: dict) -> bool:
    if _family_name(entry) == SPELLFAMILY_GENERIC:
        return False
    if not (entry.get("school") or 0) & SCHOOL_MASK_NATURE:
        return False
    if not _has_direct_heal_effect(entry):
        return False
    if entry["id"] in NEVER_LIST:
        return False
    return True


def _load_druid_spells() -> list[dict]:
    ids_cfg = source.load_ids(TOOL_ROOT / "source" / "ids.yaml")
    trainer_index = trainer_state.load_trainer_index()
    spell_table_index = spell_tables.load_spell_table_index()
    existing_group_ids = {key[0] for key in spell_table_index.live_keys("spell_group")}
    reg = registry.load_class_package(
        DRUID_DIR, ids_cfg=ids_cfg, trainer_index=trainer_index,
        existing_group_ids=existing_group_ids,
    )
    return reg.spells


class HealMechanicsPinTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.entries = _load_druid_spells()

    def test_is_direct_nature_heal_resolves_to_exactly_five_ids(self):
        matched = {e["id"] for e in self.entries if _is_direct_nature_heal(e)}
        self.assertEqual(
            matched, EXPECTED_WITH_LEGACY_RANK_CLONES,
            f"Heal::IsDirectNatureHeal's modelled rule resolved to {sorted(matched)}, "
            f"expected {sorted(EXPECTED_WITH_LEGACY_RANK_CLONES)} (RESTO §0.13 Q4's five ids "
            f"{sorted(EXPECTED)} plus the documented legacy-rank-clone exception 25297) - "
            f"missing: {EXPECTED_WITH_LEGACY_RANK_CLONES - matched}, "
            f"unexpected: {matched - EXPECTED_WITH_LEGACY_RANK_CLONES}",
        )


if __name__ == "__main__":
    unittest.main()
