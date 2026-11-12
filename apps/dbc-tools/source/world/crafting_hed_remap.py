"""
Crafting rework C6, decision 4 (`.agents/plans/crafting-rework/crafting-rework.C6-RESEARCH.md`, user 2026-11-11): Hit,
Expertise and Defense are remapped wherever a stock row carries them.

- **Enchant rows**: every stock `SpellItemEnchantment` row with a Hit, Expertise or Defense stat (enchants, gem
  enchants, socket bonuses, random-property parts; 215 rows, Outland and Northrend ones included so they are right
  when those gates open) gets the rule in `lib/crafting_hed_remap.py`: Hit -> Crit, Expertise -> Haste, Defense ->
  Dodge, point for point. `override_enchant()` keeps the stock row and changes only those columns, so dropping this
  file reverts every row, and a rerun is harmless. The rows are logged in
  `.agents/plans/crafting-rework/crafting-rework.C6-HED-REMAP.md` (to retire eventually).
- **Elixir of Minor Accuracy** (spell 63729, item 45621, Alchemy trainers): the one Hit consumable a level-60 player
  can reach today. +10 Hit Rating -> +10 Critical Strike Rating, and the item is renamed Elixir of Minor Precision
  (the client reads item names from the server). The holiday candy stays; Outland and Northrend food and elixirs wait
  for their gate (docs/phase-change-checklist.md).
"""

from lib.dsl import Effect
from lib.dsl.enchants import override_enchant, stock_enchant_rows
from lib.dsl.registry import item_template, spell

from lib import crafting_hed_remap as R

for _enchant_id, _changes in R.remapped(stock_enchant_rows()).items():
    override_enchant(_enchant_id, **_changes)

_CR_CRIT = (1 << 8) | (1 << 9) | (1 << 10)  # was 224 = the three hit ratings (5, 6, 7)

spell(
    id=63729,
    name='Elixir of Minor Accuracy',
    school=1,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    power_type=3,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=3600000,
    effects=[
        Effect(type=6, base_points=9, implicit_target_a=1, apply_aura=189, misc_value=_CR_CRIT, trigger_spell=63732),
    ],
    spell_icon_id=2426,
    notes='Crafting rework C6 remap: +10 Hit Rating (EffectMiscValue_1 224) -> +10 Critical Strike Rating, tooltips to '
          'match. Otherwise the stock row (pulled).',
    raw_overrides={
        'CastingTimeIndex': 1, 'ProcChance': 101, 'BaseLevel': 18, 'RangeIndex': 1, 'EquippedItemClass': -1,
        'ImplicitTargetA_2': 1, 'SpellVisualID_1': 633, 'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172,
        'Description_Lang_enUS': 'Increases your critical strike rating by $s1 for $d.  Battle Elixir.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_enUS': 'Critical strike rating increased by $s1.  Battle Elixir.',
        'AuraDescription_Lang_Mask': 16712190, 'SpellClassSet': 13, 'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0,
    },
)

item_template(45621, name='Elixir of Minor Precision')  # was Elixir of Minor Accuracy
