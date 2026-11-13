"""
Crafting rework C7 follow-up (user 2026-11-12): the 27 stock utility enchants become scrolls like the C6 enchants
(data and rationale: `lib/crafting_utility_enchants_data.py`).

- Each stock recipe spell is re-declared as a create-item recipe: same id, rod and cast time, named after its scroll
  like the C6 recipes ("Scroll of Enchant Cloak - Defense"), the squished reagents, and it makes the stock scroll item
  of its enchant (no vellum, no item target). Its trainer row,
  SkillLineAbility and recipe items are untouched. Eleven of them were re-declared by the C6 squish before
  (`crafting_squish.KEPT` and the armor/absorption ranks); those declarations moved here.
- Each scroll's on-use spell is new (209000 + n): SPELL_EFFECT_ENCHANT_ITEM (53) of the stock enchant into the
  permanent slot, the stock item restrictions, the C6 use spell shape (3 s, `Targets` 16 item cursor).
- The stock scroll items (`item_template`) point at the new use spell.
"""

from lib.dsl import RANGE_SELF, Effect, School
from lib.dsl.registry import item_template, spell

from lib import crafting_utility_enchants_data as U

_TEXT_MASKS = {
    'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '',
    'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712190,
}
_TARGET_UNIT_CASTER = 1
_TARGET_FLAG_ITEM = 16
_EFFECT_CREATE_ITEM = 24
_EFFECT_ENCHANT_ITEM = 53
_ATTR0_IS_TRADESKILL_NOT_SHAPESHIFTED = 0x00010020
_ATTR1_NO_THREAT = 0x00000400
_ATTR2_ENCHANT_OWN_ITEM_ONLY = 0x00002000
_INTERRUPT_FLAGS = 15
_CAST_INDEX_STOCK_ENCHANT = 6  # 5 s, the stock enchant recipes
_CAST_INDEX_APPLY = 15  # 3 s, the C6 use spells
_VISUAL_ENCHANT, _ICON_ENCHANT = 3182, 241


def _reagent_columns(reagents) -> dict:
    out = {}
    for index, (item, count) in enumerate(reagents, start=1):
        out[f'Reagent_{index}'] = item
        out[f'ReagentCount_{index}'] = count
    return out


for _n, _u in enumerate(U.UTILITY):
    _use = U.use_spell(_n)
    spell(
        id=_u.recipe, name=_u.scroll_name, school=School.NORMAL, attributes=_ATTR0_IS_TRADESKILL_NOT_SHAPESHIFTED,
        cast_time_ms=5000, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=_EFFECT_CREATE_ITEM, implicit_target_a=_TARGET_UNIT_CASTER)], spell_icon_id=_ICON_ENCHANT,
        notes=f'Crafting rework C7 follow-up: the stock recipe now makes {_u.scroll_name} (item {_u.scroll}), whose '
              f'use spell {_use} applies enchant {_u.enchant}. Stock id, rod and cast time; squished reagents.',
        raw_overrides={
            'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': 0, 'AttributesEx': _ATTR1_NO_THREAT,
            'CastingTimeIndex': _CAST_INDEX_STOCK_ENCHANT, 'InterruptFlags': _INTERRUPT_FLAGS, 'ProcChance': 101,
            'EffectItemType_1': _u.scroll, 'SpellVisualID_1': _VISUAL_ENCHANT, 'RequiredTotemCategoryID_1': _u.rod,
            'Description_Lang_enUS': '', 'AuraDescription_Lang_enUS': '', **_reagent_columns(_u.reagents),
            **_TEXT_MASKS,
        },
    )
    _item_class, _subclass_mask, _inv_mask = _u.target
    spell(
        id=_use, name=_u.name, school=School.NORMAL, attributes=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=_EFFECT_ENCHANT_ITEM, misc_value=_u.enchant)], spell_icon_id=_ICON_ENCHANT,
        notes=f'Crafting rework C7 follow-up: the on-use spell of {_u.scroll_name} (item {_u.scroll}): stock enchant '
              f'{_u.enchant}, the stock recipe {_u.recipe}\'s item restrictions.',
        raw_overrides={
            'SpellClassSet': 0, 'SpellLevel': 0, 'BaseLevel': 0, 'AttributesEx2': _ATTR2_ENCHANT_OWN_ITEM_ONLY,
            'Targets': _TARGET_FLAG_ITEM, 'CastingTimeIndex': _CAST_INDEX_APPLY, 'InterruptFlags': _INTERRUPT_FLAGS,
            'ProcChance': 101, 'EquippedItemClass': _item_class, 'EquippedItemSubclass': _subclass_mask,
            'EquippedItemInvTypes': _inv_mask, 'SpellVisualID_1': _VISUAL_ENCHANT,
            'Description_Lang_enUS': _u.description, 'AuraDescription_Lang_enUS': '', **_TEXT_MASKS,
        },
    )
    item_template(_u.scroll, spellid_1=_use)
