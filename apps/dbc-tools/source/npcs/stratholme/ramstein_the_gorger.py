"""
Stratholme build WP-S13: Ramstein the Gorger (10439)
(.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.5 row S13; build spec
docs/dungeons/stratholme-rework.md ST 3432-3483). WP-S13 owns this file; WP-S0 wrote the skeleton.

Skeleton (WP-S0, handoff s3.2 item 3): the boss is bound to its C++ script (modules/mod-dungeon-bosses
src/Stratholme/boss_ramstein_the_gorger_rework.cpp), SmartAI off, the build spec's normal health (210k: HealthModifier
66.794 on the level 61 warrior class base 3,144), stun immunity 1972, INSTANCE_BIND (flags_extra 1), DamageModifier 9
(the stock value: base SQL and the 2026_09_27_06 sniff update; the live value differed only where mod-progression left
one). Heroic health and its overrides are WP-H's (source/world/dungeons/stratholme.py).

TODO(WP-S13): spells in its slice (kSpellsRamstein of StratholmeRework.h, 206685-206704), the boss-kit creatures named
in the header's StratholmeCreatures enum, the visual ids from ._visuals (WP-V-1). The SQL rev
(data/sql/updates/pending_db_world/) drops the SmartAI rows and adds the texts.
"""

from lib.dsl.registry import creature_template_columns

from ._common import boss_columns

creature_template_columns(10439, **boss_columns(
    'boss_ramstein_the_gorger_rework', 66.794, damage_modifier=9,
))
