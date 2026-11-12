"""
Crafting rework C7: the crafted sets' recipes (`.agents/plans/crafting-rework/crafting-rework.C7-RESEARCH.md`
decisions 2e and 3e, ruled 2026-11-12). The data is `lib/crafting_sets_data.py`; the items are
`source/items/crafting_sets.py`.

- One recipe per item (207600 + n) on its profession's skill line, with its SkillLineAbility row (31200 + n). A
  recipe names the minted item it creates by its item() key (`lib/item_key_refs.py`).
- Leveling and level-60 recipes are taught by the profession's Azeroth trainer (Blacksmithing 60, Leatherworking 61,
  Tailoring 74, Engineering 92, Enchanting 96, Jewelcrafting 113, Inscription 121): 10 copper for a level-15
  recipe, 1 silver at 30, 10 silver at 45, 1 gold at 60.
- Raid recipes have no trainer: a recipe item (`write_crafting_set_items.py`, 78000 + n) teaches them through its
  learn spell (208600 + n), one learn effect per recipe it teaches (up to three). The recipe items drop from the
  tier's raid bosses (`rev_crafting_c7_set_loot.sql`).

Recipe row shape: the C6 recipes (`source/world/crafting_enchants.py`); the learn spell copies stock 483 Learning.
"""

from lib import crafting_sets_data as T
from lib import item_key_refs
from lib.dsl import RANGE_SELF, Effect, School
from lib.dsl.registry import scripted_by, skill_line_ability, spell, trained_by

_TEXT_MASKS = {
    'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '',
    'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712190,
}
_TARGET_UNIT_CASTER = 1
_EFFECT_CREATE_ITEM = 24
_EFFECT_LEARN_SPELL = 36
_ATTR0_IS_TRADESKILL_NOT_SHAPESHIFTED = 0x00010020
_ATTR1_NO_THREAT = 0x00000400
_INTERRUPT_FLAGS = 15

# Per profession: the stock recipe shape (CastingTimeIndex, SpellVisualID_1, SpellIconID, extra raw columns), as C6.
_CRAFT_SHAPE = {
    T.ENCHANTING: (33, 3182, 241, {}),
    T.TAILORING: (38, 1168, 69, {}),
    T.LEATHERWORKING: (34, 4439, 1, {}),
    T.ENGINEERING: (38, 395, 1, {'RequiredTotemCategoryID_1': 14}),
    T.INSCRIPTION: (5, 10130, 2557, {'RequiredTotemCategoryID_1': 121}),
    T.BLACKSMITHING: (37, 395, 335, {'RequiresSpellFocus': 1, 'RequiredTotemCategoryID_1': 162}),
    T.JEWELCRAFTING: (35, 7373, 1, {}),
}
# Stock 483 Learning: 3 s cast, its visual and icon.
_LEARN_CAST_INDEX, _LEARN_VISUAL, _LEARN_ICON, _LEARN_ATTR0 = 14, 222, 2121, 0x100


def _reagent_columns(reagents) -> dict:
    out = {}
    for index, (item, count) in enumerate(reagents, start=1):
        out[f'Reagent_{index}'] = item
        out[f'ReagentCount_{index}'] = count
    return out


for _row in T.recipes():
    _item = _row.item
    _cast, _visual, _icon, _extra = _CRAFT_SHAPE[_item.profession]
    spell(
        id=_row.spell, name=_item.name, school=School.NORMAL, attributes=_ATTR0_IS_TRADESKILL_NOT_SHAPESHIFTED,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=0, effects=[Effect(type=_EFFECT_CREATE_ITEM, implicit_target_a=_TARGET_UNIT_CASTER)],
        spell_icon_id=_icon,
        notes=f'Crafting rework C7: the recipe of {_item.name} ({_item.set.label} set, item {_item.key}).',
        raw_overrides={
            'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': 0, 'AttributesEx': _ATTR1_NO_THREAT,
            'CastingTimeIndex': _cast, 'InterruptFlags': _INTERRUPT_FLAGS, 'ProcChance': 101,
            'EffectItemType_1': item_key_refs.ref(_item.key), 'SpellVisualID_1': _visual, 'Description_Lang_enUS': '',
            'AuraDescription_Lang_enUS': '', **_reagent_columns(T.reagents(_item)), **_extra, **_TEXT_MASKS,
        },
    )
    skill_line_ability(id=_row.sla, skill_line=_item.profession, spell_id=_row.spell, min_skill_line_rank=1,
                       acquire_method=0, raw_overrides={'TrivialSkillLineRankHigh': 1, 'TrivialSkillLineRankLow': 1})
    if not _item.set.raid:
        trained_by(_row.spell, T.TRAINER[_item.profession], req_level=0, money_cost=T.TRAIN_COST[_item.set.key],
                   req_skill_line=_item.profession, req_skill_rank=1)


for _recipe_item in T.raid_recipe_items():
    spell(
        id=_recipe_item.learn_spell, name=_recipe_item.name, school=School.NORMAL, attributes=_LEARN_ATTR0,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=0,
        effects=[Effect(type=_EFFECT_LEARN_SPELL, implicit_target_a=_TARGET_UNIT_CASTER, trigger_spell=row.spell)
                 for row in _recipe_item.teaches],
        spell_icon_id=_LEARN_ICON,
        notes=f'Crafting rework C7: the learn spell of recipe item {_recipe_item.entry} ({_recipe_item.name}).',
        raw_overrides={
            'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': 0, 'AttributesEx': _ATTR1_NO_THREAT,
            'CastingTimeIndex': _LEARN_CAST_INDEX, 'ProcChance': 101, 'SpellVisualID_1': _LEARN_VISUAL,
            'Description_Lang_enUS': _recipe_item.description,
            'AuraDescription_Lang_enUS': '', **_TEXT_MASKS,
        },
    )
    scripted_by(_recipe_item.learn_spell, "spell_crafting_recipe_learn")  # refused when already known (review S6)
