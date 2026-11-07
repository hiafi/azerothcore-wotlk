"""
Item variants IV6 (.agents/plans/item-variants/item-variants.PLAN.md section 7.2): the creature of the Edwin VanCleef
hard mode item effects. The spells are source/items/deadmines_hard_mode_effects.py (the `items` spell reservation); the
creature takes the first id of the `deadmines` creature spare (300430-300449).

- 300430 Defias Blackguard: the Blackguard's Signet look. spell_dm_blackguards_signet (modules/mod-dungeon-bosses
  hard_mode_items.cpp) summons it behind the wearer's target for 2.5 s, at the wearer's level, passive; it casts the
  ambush look on itself and the wearer's own triggered Blackguard Strike (205404) deals the damage, so the number
  scales with the wearer (potency). Never targetable or attackable (KIT_HELPER), friendly to all (faction 35), no
  loot, no XP, no melee; it is not a trigger (flags_extra 0x80 would hide it). Models: the stock Blackguard's (636).
"""

from lib.dsl.registry import creature_model, creature_template

from ._common import KIT_HELPER

signet_blackguard_300430 = creature_template(
    300430, 'Defias Blackguard', **{**KIT_HELPER, 'faction': 35, 'minlevel': 60, 'maxlevel': 60, 'rank': 0,
                                    'unit_class': 1, 'ScriptName': ''},
)
creature_model(300430, display_id=2314, idx=0)
creature_model(300430, display_id=2315, idx=1)
