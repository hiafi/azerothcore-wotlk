"""
The one Zul'Farrak list item effect that is not a stock spell: Call of Sul'thraze, the Use on every tier of Jang'thraze
the Protector (zul_farrak.py). User ruling 2026-11-25, option A: the join is tier matched. A Jang'thraze and a
Sang'thraze of the same tier make the Sul'thraze of that tier, Normal to the last empowered tier; mixed tiers are
refused and nothing is used up.

  213808  Call of Sul'thraze      the stock 11654 (look, icon, 10 sec cast, self, interrupt flags) without its Create
                                  Item effect and its reagent: one DUMMY effect on the caster. The client refuses a
                                  cast over a missing reagent entry by itself, so a reagent can only ever name one tier.
                                  spell_zf_call_of_sulthraze (modules/mod-dungeon-bosses src/ZulFarrak/
                                  sulthraze_join.cpp) finds the tier of the Jang'thraze that is used and of the
                                  Sang'thraze in item_budget_variant, uses up the Sang'thraze and makes the sword; the
                                  engine uses up Jang'thraze (the Use slot's charges -1, as stock). One spell for every
                                  tier: it carries no number.
  213809-213839  spare (the reservation `zul_farrak_items`, 213800-213839; 213800-213807 are
                 zul_farrak_hard_mode_effects.py)

The stock spell 11654 and the items it names stay as they are. Only 9380, a second stock Jang'thraze entry that nothing
hands out, still casts it.
"""

from lib.dsl import RANGE_SELF, Effect, EffectType, School
from lib.dsl.registry import scripted_by, spell

_TARGET_UNIT_CASTER = 1
_ATTR0_DO_NOT_LOG = 0x00000100
_INTERRUPT_FLAGS = 15               # movement, pushback, interrupt, auto attack (11654)
_CAST_MS = 10000                    # cast time index 7 (11654)
_SV_CALL_OF_SULTHRAZE = 76          # 11654
_ICON_CALL_OF_SULTHRAZE = 2667      # 11654

call_of_sulthraze_213808 = spell(
    id=213808, name="Call of Sul'thraze", school=School.NORMAL, attributes=_ATTR0_DO_NOT_LOG, cast_time_ms=_CAST_MS,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_CALL_OF_SULTHRAZE,
    notes='Zul\'Farrak, Jang\'thraze the Protector (every tier), the Use: the tier-matched join (user 2026-11-25, '
          'option A). The stock 11654 with a DUMMY instead of its Create Item and without its reagent (a reagent names '
          'one tier and the client enforces it). spell_zf_call_of_sulthraze joins it with a Sang\'thraze of the same '
          'tier into that tier\'s Sul\'thraze and refuses mixed tiers, a full bag, a second unique Sul\'thraze and a '
          'cast without the sword. The engine uses up Jang\'thraze (charges -1). Look: stock 11654 (SV 76).',
    raw_overrides={
        'SpellClassSet': 0, 'EquippedItemClass': -1, 'InterruptFlags': _INTERRUPT_FLAGS, 'ProcChance': 101,
        'SpellVisualID_1': _SV_CALL_OF_SULTHRAZE, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190,
        'NameSubtext_Lang_enUS': '', 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712190,
        'Description_Lang_enUS': "Combines Jang'thraze with a Sang'thraze of the same tier to form the mighty sword, "
                                 "Sul'thraze. Both halves are used up.",
        'AuraDescription_Lang_enUS': '',
    },
)
scripted_by(call_of_sulthraze_213808, 'spell_zf_call_of_sulthraze')
