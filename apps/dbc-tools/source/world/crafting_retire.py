"""
Crafting rework C7, recipe retirement (`.agents/plans/crafting-rework/crafting-rework.C7-RESEARCH.md` decision 1, ruled
2026-11-12). The data is `lib/crafting_retire_data.py` (882 stock recipes: crafted gear the C7 sets replace, the drop
and vendor stat enchants and enchant items C6 replaced, glyphs, ammo). This file holds the spell-side half:

- **Trainers** (1a): every retired recipe comes off every trainer that taught it (`untrain`, the live trainer ids of
  2026-11-12).
- **Starter recipes** (1a): the 14 retired recipes a profession taught on learning (SkillLineAbility AcquireMethod
  1/2: Handstitched Leather Boots, Linen Cloak, Rough Copper Vest and so on) stop being taught (AcquireMethod 0).
- **Recipe items** (1b A): the 529 retired recipe items stop teaching (no use spell) and turn Poor quality, so copies
  in bags, banks, mail and the auction house become vendor trash. The rows stay (item_template is never deleted).

The rest is hand-written SQL from `write_crafting_retire.py` (the recipe items' loot, vendor and condition rows, the
`disables` rows that refuse the spells and quests, the learned-recipe cleanup in the characters DB) and the learn
guard in `src/server/scripts/Custom/custom_professions.cpp`.
"""

from lib import crafting_retire_data as R
from lib.dsl.registry import item_template, override_skill_line_ability, untrain

RETIRED_RECIPE_DESCRIPTION = 'This recipe has been retired. It no longer teaches anything.'
QUALITY_POOR = 0

for _spell_id, _trainers in R.TRAINERS.items():
    untrain(_spell_id, list(_trainers))

for _sla_id in R.STARTER_SLA:
    override_skill_line_ability(_sla_id, acquire_method=0)

for _item in R.RECIPE_ITEMS:
    item_template(_item, spellid_1=0, spellid_2=0, Quality=QUALITY_POOR, description=RETIRED_RECIPE_DESCRIPTION)
