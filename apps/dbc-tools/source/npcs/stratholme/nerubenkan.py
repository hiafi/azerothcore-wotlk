"""
Stratholme build WP-S11: Nerub'enkan (10437)
(.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.5 row S11; build spec
docs/dungeons/stratholme-rework.md ST 2859-2911). WP-S11 owns this file; WP-S0 wrote the skeleton.

Skeleton (WP-S0, handoff s3.2 item 3): the boss is bound to its C++ script (modules/mod-dungeon-bosses
src/Stratholme/boss_nerubenkan_rework.cpp), SmartAI off, the build spec's normal health (170k: HealthModifier 55.701
on the level 60 warrior class base 3,052), stun immunity 1972, INSTANCE_BIND (flags_extra 1), DamageModifier 7.5 (the
stock value: base SQL and the 2026_09_27_06 sniff update; the live value differed only where mod-progression left
one). Heroic health and its overrides are WP-H's (source/world/dungeons/stratholme.py).

TODO(WP-S11): spells in its slice (kSpellsNerubenkan of StratholmeRework.h, 206645-206664), the boss-kit creatures
named in the header's StratholmeCreatures enum, the visual ids from ._visuals (WP-V-1). The SQL rev
(data/sql/updates/pending_db_world/) drops the SmartAI rows and adds the texts.
"""

from lib.dsl.registry import creature_template_columns

from ._common import boss_columns

creature_template_columns(10437, **boss_columns(
    'boss_nerubenkan_rework', 55.701, damage_modifier=7.5,
))
