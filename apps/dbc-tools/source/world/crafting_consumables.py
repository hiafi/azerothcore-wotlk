"""
Crafting rework C7: premium enchants, flasks, raid buff scrolls, boss runes and the Darkmoon tarot
(`.agents/plans/crafting-rework/crafting-rework.C7-RESEARCH.md` decisions 4, 5, 6; the data and the rules are in
`lib/crafting_consumables_data.py`). The items are hand-written rows from `write_crafting_consumable_items.py`; the
scripts are `custom_crafting_enchants.cpp` (premium procs, Steelweave) and `custom_crafting_runes.cpp` (boss runes).

Row shapes: the C6 enchant use spells and recipes (`source/world/crafting_enchants.py`), the stock flasks (Flask of the
Titans 17626, its recipe 17635), Gift of the Wild 21849 for the raid-wide scrolls, 483 Learning for the learn spells.
"""

from lib import crafting_consumables_data as T
from lib.dsl import RANGE_SELF, Effect, School
from lib.dsl.enchants import enchant, spell_effect, stat_effect
from lib.dsl.registry import (
    EnchantType, item_template, procs_on, scripted_by, skill_line_ability, spell, spell_category, spell_group,
    spell_group_rule, trained_by,
)

_TEXT_MASKS = {
    'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '',
    'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712190,
}
_TARGET_UNIT_CASTER = 1
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_FLAG_ITEM = 16
_EFFECT_APPLY_AURA = 6
_EFFECT_CREATE_ITEM = 24
_EFFECT_LEARN_SPELL = 36
_EFFECT_ENCHANT_ITEM = 53
_EFFECT_DUMMY = 3
_AURA_PERIODIC_DUMMY = 226
_ATTR0_PASSIVE = 0x40
_ATTR0_HIDDEN = 0x80
_ATTR0_IS_TRADESKILL_NOT_SHAPESHIFTED = 0x00010020
_ATTR1_NO_THREAT = 0x00000400
_ATTR2_ENCHANT_OWN_ITEM_ONLY = 0x00002000
_ATTR3_ALLOW_AURA_WHILE_DEAD = 0x00100000
_ATTR4_AURA_EXPIRES_OFFLINE = 0x00000004
_INTERRUPT_FLAGS = 15
_DURATION_INFINITE = 21
_DISPEL_MAGIC = 1

# Per profession: the stock recipe shape (CastingTimeIndex, SpellVisualID_1, SpellIconID, extra raw columns).
_CRAFT_SHAPE = {
    T.ENCHANTING: (33, 3182, 241, {}),
    T.INSCRIPTION: (5, 10130, 2557, {'RequiredTotemCategoryID_1': 121}),
    T.ALCHEMY: (37, 92, 1, {}),
}


def _reagent_columns(reagents) -> dict:
    out = {}
    for index, (item, count) in enumerate(reagents, start=1):
        out[f'Reagent_{index}'] = item
        out[f'ReagentCount_{index}'] = count
    return out


def _aura(aura: int, misc: int, amount: int, target: int = _TARGET_UNIT_CASTER, **kwargs) -> Effect:
    # base_points is the raw DBC column: the effect's value is base_points + 1 (DieSides 1).
    return Effect(type=_EFFECT_APPLY_AURA, apply_aura=aura, misc_value=misc, base_points=amount - 1,
                  implicit_target_a=target, **kwargs)


def _recipe(spell_id: int, sla_id: int, name: str, item: int, profession: int, reagents, note: str,
            trainer: bool) -> None:
    cast_index, visual, icon, extra = _CRAFT_SHAPE[profession]
    spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=_ATTR0_IS_TRADESKILL_NOT_SHAPESHIFTED, cast_time_ms=0,
        cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=_EFFECT_CREATE_ITEM, implicit_target_a=_TARGET_UNIT_CASTER)], spell_icon_id=icon,
        notes=f'Crafting rework C7: the recipe of {name} (item {item}). {note}',
        raw_overrides={
            'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': 0, 'AttributesEx': _ATTR1_NO_THREAT,
            'CastingTimeIndex': cast_index, 'InterruptFlags': _INTERRUPT_FLAGS, 'ProcChance': 101,
            'EffectItemType_1': item, 'SpellVisualID_1': visual, 'Description_Lang_enUS': '',
            'AuraDescription_Lang_enUS': '', **_reagent_columns(reagents), **extra, **_TEXT_MASKS,
        },
    )
    skill_line_ability(id=sla_id, skill_line=profession, spell_id=spell_id, min_skill_line_rank=1, acquire_method=0,
                       raw_overrides={'TrivialSkillLineRankHigh': 1, 'TrivialSkillLineRankLow': 1})
    if trainer:
        trained_by(spell_id, T.TRAINER[profession], req_level=0, money_cost=T.TRAIN_COST, req_skill_line=profession,
                   req_skill_rank=1)


def _buff(spell_id: int, name: str, effects, duration_ms: int, text: str, note: str, raw=None, **kwargs) -> None:
    spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=duration_ms,
        effects=effects, spell_icon_id=kwargs.pop('icon', 1), notes=f'Crafting rework C7: {note}',
        raw_overrides={'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': 0, 'CastingTimeIndex': 1,
                       'ProcChance': 101, 'Description_Lang_enUS': text,
                       'AuraDescription_Lang_enUS': T.number_free(text),
                       **(raw or {}), **_TEXT_MASKS},
        **kwargs,
    )


# --- Premium enchants (decision 4) -----------------------------------------------------------------------------------
for _key, _b in T.BUFFS.items():
    _buff(_b.spell, _b.name, [_aura(_b.aura, _b.misc, _b.amount)], _b.duration_ms, _b.text,
          f'premium enchant buff ({_key}).')
scripted_by(T.BUFFS["absorb"].spell, "spell_crafting_max_health_absorb")

for _key, _p in T.PROCS.items():
    spell(
        id=_p.aura_spell, name=_p.name, school=School.NORMAL, attributes=_ATTR0_PASSIVE | _ATTR0_HIDDEN,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=-1, effects=[Effect(type=_EFFECT_APPLY_AURA, apply_aura=T.AURA_PROC_TRIGGER_SPELL,
                                        trigger_spell=T.BUFFS[_p.buff].spell, implicit_target_a=_TARGET_UNIT_CASTER)],
        spell_icon_id=1, notes=f'Crafting rework C7: the premium enchant proc aura of {_p.name}.',
        raw_overrides={'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': 0, 'CastingTimeIndex': 1,
                       'DurationIndex': _DURATION_INFINITE, 'ProcChance': 101, 'Description_Lang_enUS': _p.description,
                       'AuraDescription_Lang_enUS': '', **_TEXT_MASKS},
    )
    procs_on(_p.aura_spell, _p.proc_flags, chance=_p.chance, cooldown_ms=_p.cooldown_ms, spell_phase_mask=_p.phase)
    if _p.script:
        scripted_by(_p.aura_spell, _p.script)

_seen_enchants = set()
for _pr in T.PREMIUMS:
    if _pr.enchant not in _seen_enchants:
        _seen_enchants.add(_pr.enchant)
        _parts = [spell_effect(EnchantType.EQUIP_SPELL, T.PROCS[_pr.proc].aura_spell)] if _pr.proc else []
        for _extra in _pr.extra:
            if _extra[0] == "spell":
                _parts.append(spell_effect(EnchantType.EQUIP_SPELL, _extra[1]))
            else:
                _parts.append(stat_effect(_extra[1], _extra[2]))
        enchant(_pr.enchant, _pr.text, *_parts, min_level=T.PREMIUM_ENCHANT_MIN_LEVEL)
    _item_class, _subclass_mask, _inv_mask = _pr.target
    spell(
        id=_pr.use_spell, name=_pr.item_name, school=School.NORMAL, attributes=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=_EFFECT_ENCHANT_ITEM, misc_value=_pr.enchant)], spell_icon_id=241,
        notes=f'Crafting rework C7: the on-use spell of {_pr.item_name} (item {_pr.item}): enchant {_pr.enchant}.',
        raw_overrides={
            'SpellClassSet': 0, 'SpellLevel': 0, 'BaseLevel': 0, 'AttributesEx2': _ATTR2_ENCHANT_OWN_ITEM_ONLY,
            'Targets': _TARGET_FLAG_ITEM, 'CastingTimeIndex': 15, 'InterruptFlags': _INTERRUPT_FLAGS,
            'ProcChance': 101, 'EquippedItemClass': _item_class, 'EquippedItemSubclass': _subclass_mask,
            'EquippedItemInvTypes': _inv_mask, 'SpellVisualID_1': 3182,
            'Description_Lang_enUS': f'Permanently enchants an item with {_pr.text}. Requires level 60 to take effect.',
            'AuraDescription_Lang_enUS': '', **_TEXT_MASKS,
        },
    )
    _recipe(_pr.recipe_spell, _pr.sla, _pr.item_name, _pr.item, T.ENCHANTING, T.PREMIUM_REAGENTS,
            'Premium enchant, learned from a T1 raid recipe.', trainer=False)
    spell(
        id=_pr.learn_spell, name=f'Formula: {_pr.item_name.removeprefix("Scroll of ")}', school=School.NORMAL,
        attributes=0x100, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=_EFFECT_LEARN_SPELL, implicit_target_a=_TARGET_UNIT_CASTER,
                        trigger_spell=_pr.recipe_spell)],
        spell_icon_id=2121, notes=f'Crafting rework C7: the learn spell of premium recipe item {_pr.recipe_item}.',
        raw_overrides={'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': 0, 'AttributesEx': _ATTR1_NO_THREAT,
                       'CastingTimeIndex': 14, 'ProcChance': 101, 'SpellVisualID_1': 222,
                       'Description_Lang_enUS': f'Teaches you how to make a {_pr.item_name}.',
                       'AuraDescription_Lang_enUS': '', **_TEXT_MASKS},
    )
    scripted_by(_pr.learn_spell, "spell_crafting_recipe_learn")  # refused when already known (review S6)

# --- Flasks (decision 5) ----------------------------------------------------------------------------------------------
# (SpellIconID, SpellVisualID_1) of each stock flask; the new ones look like the Titans.
_FLASK_LOOK = {17626: (1639, 147), 17627: (1640, 147), 17628: (1643, 633)}
for _f in T.FLASKS:
    _icon, _visual = _FLASK_LOOK.get(_f.spell, _FLASK_LOOK[17626])
    _stat = T.STAT_NAME[_f.stat]
    spell(
        id=_f.spell, name=_f.name, school=School.NORMAL, attributes=671088640, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, power_type=4, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=3600000, effects=[_aura(T.AURA_MOD_STAT, _f.stat, _f.amount)], spell_icon_id=_icon,
        notes=f'Crafting rework C7 flask: +{_f.amount} {_stat} (decision 5, sizes research 6.4). Otherwise the stock '
              f'flask row shape (Flask of the Titans 17626).',
        raw_overrides={
            'AttributesEx2': 1, 'AttributesEx3': _ATTR3_ALLOW_AURA_WHILE_DEAD, 'CastingTimeIndex': 1,
            'ProcChance': 101, 'SpellLevel': 15, 'DurationIndex': T.FLASK_DURATION_INDEX, 'EquippedItemClass': -1,
            'SpellVisualID_1': _visual, 'SpellClassSet': 13,
            'Description_Lang_enUS': f'Increases {_stat} by $s1 for $d. Counts as both a Battle and Guardian elixir.  '
                                     f'This effect persists through death.',
            'AuraDescription_Lang_enUS': f'{_stat} increased.', **_TEXT_MASKS,
        },
    )
    if _f.sla is not None:
        spell_group(T.FLASK_GROUPS[0], _f.spell)
        spell_group(T.FLASK_GROUPS[1], _f.spell)
        _recipe(_f.recipe_spell, _f.sla, _f.name, _f.item, T.ALCHEMY, _f.reagents, 'Flask, trained.', trainer=True)
    else:
        trained_by(_f.recipe_spell, T.TRAINER[T.ALCHEMY], req_level=0, money_cost=T.TRAIN_COST,
                   req_skill_line=T.ALCHEMY, req_skill_rank=1)

# --- Raid buff scrolls (decision 6a) ----------------------------------------------------------------------------------
for _group, (_nested, _name) in T.WRAPPER_GROUPS.items():
    spell_group(_group, _nested)
    spell_group_rule(_group, T.STACK_RULE_SAME_EFFECT, _name)
for _n, _s in enumerate(T.SCROLLS):
    _spell_id, _recipe_id, _sla_id, _item_id = T.scroll_ids(_n)
    _buff(
        _spell_id, _s.name,
        [_aura(aura, misc, amount, target=T.SCROLL_TARGET) for aura, misc, amount in _s.effects],
        T.SCROLL_DURATION_MS,
        _s.text, f'raid buff scroll copying {_s.source} at its base value, in its spell group(s) {_s.groups}.',
        raw={'Description_Lang_enUS': f'Gives every party and raid member nearby the {_s.source} effect for $d: '
                                      f'{_s.text}',
             'AuraDescription_Lang_enUS': T.number_free(_s.text),
             **{f'EffectRadiusIndex_{k}': T.SCROLL_RADIUS_INDEX for k in range(1, len(_s.effects) + 1)},
             'SpellVisualID_1': 212},
        dispel=_DISPEL_MAGIC, icon=2435,
    )
    for _group in _s.groups:
        spell_group(_group, _spell_id)
    _recipe(_recipe_id, _sla_id, _s.name, _item_id, T.INSCRIPTION, T.SCROLL_REAGENTS, 'Raid buff scroll, trained.',
            trainer=True)

# --- Boss runes (decision 6b) -----------------------------------------------------------------------------------------
spell_category(T.RUNE_CATEGORY, comment='crafting rework C7 Rune of Empowerment: its 24 hour cooldown')
_r = T.RUNE
spell(
    id=_r.spell, name=_r.name, school=School.NORMAL, attributes=0, category=T.RUNE_CATEGORY,
    cast_time_ms=T.RUNE_CAST_MS, cooldown_ms=0, category_cooldown_ms=T.RUNE_COOLDOWN_MS, mana_cost=0, mana_cost_pct=0,
    range_yards=T.RUNE_RANGE_YARDS, duration_ms=T.RUNE_DURATION_MS,
    effects=[Effect(type=_EFFECT_DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, base_points=_r.warding_pct - 1),
             _aura(_AURA_PERIODIC_DUMMY, 0, _r.damage_pct, amplitude=1000),
             _aura(T.AURA_MOD_HEALING_DONE_PERCENT, 0, _r.healing_pct)],  # the tick switches it (review B3)
    spell_icon_id=2557, notes=f'Crafting rework C7: {_r.name}, the boss rune (custom_crafting_runes.cpp).',
    raw_overrides={'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': 0, 'InterruptFlags': _INTERRUPT_FLAGS,
                   'ProcChance': 101, 'AttributesEx': _ATTR1_NO_THREAT,  # no pull (review B2)
                   'AttributesEx3': _ATTR3_ALLOW_AURA_WHILE_DEAD,
                   'AttributesEx4': _ATTR4_AURA_EXPIRES_OFFLINE,  # 24 hours of real time
                   'Description_Lang_enUS': f'Use on a boss to select it: for $d, {_r.text}',
                   'AuraDescription_Lang_enUS': 'Empowered against the selected boss: more damage to it, less damage '
                                                'from it, more healing while fighting it.',
                   'SpellVisualID_1': 10130, **_TEXT_MASKS},
)
scripted_by(_r.spell, "spell_crafting_boss_rune")
_recipe(_r.recipe_spell, _r.sla, _r.name, _r.item, T.INSCRIPTION, T.RUNE_REAGENTS, 'Boss rune, trained.', trainer=True)

# --- Darkmoon (decision 6c) -------------------------------------------------------------------------------------------
_recipe(T.TAROT_RECIPE, T.TAROT_SLA, 'Darkmoon Tarot', T.TAROT_ITEM, T.INSCRIPTION, T.TAROT_REAGENTS,
        'Opens into a random card of the vanilla decks.', trainer=True)
for _deck, (_trinket, _spell_id) in T.DECKS.items():
    spell(
        id=_spell_id, name=f'Shuffle the {T.DECK_NAMES[_deck]}', school=School.NORMAL, attributes=0, cast_time_ms=0,
        cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=_EFFECT_CREATE_ITEM, implicit_target_a=_TARGET_UNIT_CASTER)], spell_icon_id=1,
        notes=f'Crafting rework C7: the {T.DECK_NAMES[_deck]} turns into its trinket (item {_trinket}) on use.',
        raw_overrides={'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': 0, 'CastingTimeIndex': 14,
                       'ProcChance': 101, 'EffectItemType_1': _trinket, 'EffectBasePoints_1': 0,
                       'Description_Lang_enUS': 'Turns the deck into its Darkmoon Card.',
                       'AuraDescription_Lang_enUS': '', **_TEXT_MASKS},
    )
    item_template(_deck, startquest=0, spellid_1=_spell_id, spelltrigger_1=0, spellcharges_1=-1)
