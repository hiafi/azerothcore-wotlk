"""
Crafting rework C7: the crafted sets' items (`.agents/plans/crafting-rework/crafting-rework.C7-RESEARCH.md` decisions 2
and 3, ruled 2026-11-12). The catalog, names, looks and stats are the data in `lib/crafting_sets_data.py`; the recipes
are `source/world/crafting_sets.py`.

Every item is one tier (ladder `crafted_set`, no tooltip label): its set's item level, quality and required level.
Primary stat + Stamina at `primary_share` 6000 and a random suffix from the C4 pool for the secondaries
(`suffix_pool=`; tank pieces roll the tank pool and take +25% Stamina; rings and necks have no primary). Raid pieces
carry one socket (heads a meta plus one) and a +4 secondary socket bonus. Bind on Equip, like stock crafted gear.
"""

from lib import crafting_sets_data as T
from lib.dsl.items import item, ladder, tier

CRAFTED_SET = ladder("crafted_set", normal=tier(step=0, label=None))
BIND_ON_EQUIP = 2

for _item in T.items():
    item(
        _item.key, ladder=CRAFTED_SET, name=_item.name, like=_item.like, ilvl=_item.set.ilvl,
        quality=_item.set.quality, required_level=_item.set.level, primary=_item.primary,
        suffix_pool=_item.pool, extra_stamina=_item.extra_stamina, weapon_role=_item.weapon_role,
        sockets=_item.sockets or None, socket_bonus=_item.socket_bonus, bonding=BIND_ON_EQUIP,
    )
