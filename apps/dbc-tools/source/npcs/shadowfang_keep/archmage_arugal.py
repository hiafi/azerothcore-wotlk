"""
Shadowfang Keep build WP-S9: Archmage Arugal (.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md s3.5
rows AR1-AR9, s3.6 row S9; build spec docs/dungeons/shadowfang-keep-rework.md SK 1576-1646 (build spec), SK 1394-1575
(design)). WP-S9 owns this file (its spells: kSpellsArugal in modules/mod-dungeon-bosses
src/ShadowfangKeep/ShadowfangKeepRework.h only; ArugalLogic.h names the same ids).

STUB from WP-K (the SFK layer): binds 4275 to boss_archmage_arugal_rework (SmartAI off; the stock rows are dropped by
WP-S9's SQL rev), normal health HealthModifier 37.25 (handoff s3.7), stun immune (IMMUNITY_BOSS_STUN 1972, s7 #8).
Heroic health is WP-H's override in source/world/dungeons/shadowfang_keep.py.

The lair prisoners 300513 / 300514 at the end of this file are WP-K's skeleton (handoff s7 #9): S9 adds their
gossip menus and anything else they need.

TODO(WP-S9): the boss-kit spells and creatures of handoff s3.5 / s3.6 row S9, and any other normal column (add it to the
creature_template_columns call below: one call per entry).
"""

from lib.dsl.registry import creature_model, creature_template, creature_template_columns

from ._common import KIT_CREATURE, boss_columns

creature_template_columns(4275, **boss_columns('boss_archmage_arugal_rework', 37.25))

# The lair prisoners (handoff s7 #9; declared by WP-K, scripted by WP-S9 / S10): copies of the stock cell prisoners
# 3850 / 3849 (read-only SELECTs 2026-11-07: levels, faction, class, flags, modifiers, models) without their SmartAI,
# loot or gossip menu, so the stock courtyard event never runs again. The instance summons the one who opened the
# Courtyard Door (DATA_PRISONER; else by the players' side) at the lair door once Nandos is dead. Friendly gossip NPCs
# (npcflag 1: S9's menu, S10's heroic option); no heroic template (s3.4).
_LAIR_PRISONER = {
    **KIT_CREATURE, 'minlevel': 18, 'maxlevel': 18, 'rank': 1, 'npcflag': 1, 'gossip_menu_id': 0,
    'HealthModifier': 3.0, 'DamageModifier': 1.7, 'ExperienceModifier': 1.0, 'lootid': 0, 'pickpocketloot': 0,
    'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'ScriptName': 'npc_sfk_lair_prisoner',
}

lair_ashcrombe_300513 = creature_template(
    300513, 'Sorcerer Ashcrombe', **{**_LAIR_PRISONER, 'faction': 12, 'unit_class': 8, 'unit_flags': 32832,
                                    'ManaModifier': 2.0},
)
creature_model(300513, display_id=2005)

lair_adamant_300514 = creature_template(
    300514, 'Deathstalker Adamant', **{**_LAIR_PRISONER, 'faction': 68, 'unit_class': 1, 'unit_flags': 37440},
)
creature_model(300514, display_id=2006)
