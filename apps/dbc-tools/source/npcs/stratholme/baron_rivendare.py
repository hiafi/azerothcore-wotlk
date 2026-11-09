"""
Stratholme build WP-S14: Baron Rivendare (10440)
(.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.5 row S14; build spec
docs/dungeons/stratholme-rework.md ST 3842-3906). WP-S14 owns this file; WP-S0 wrote the skeleton.

Skeleton (WP-S0, handoff s3.2 item 3): the boss is bound to its C++ script (modules/mod-dungeon-bosses
src/Stratholme/boss_baron_rivendare_rework.cpp), SmartAI off, the build spec's normal health (250k: HealthModifier
96.525 on the level 62 paladin class base 2,590), his stock immunity set -419 (handoff s7 #3), INSTANCE_BIND
(flags_extra 1), DamageModifier 8 (the stock value: base SQL and the 2026_09_27_06 sniff update; the live value
differed only where mod-progression left one). Heroic health and its overrides are WP-H's
(source/world/dungeons/stratholme.py).

TODO(WP-S14): spells in its slice (kSpellsBaron of StratholmeRework.h, 206705-206719), the boss-kit creatures named in
the header's StratholmeCreatures enum, the visual ids from ._visuals (WP-V-1). The SQL rev
(data/sql/updates/pending_db_world/) drops the SmartAI rows and adds the texts.
"""

from lib.dsl.registry import creature_template_columns

from ._common import IMMUNITY_BARON_STOCK, boss_columns

creature_template_columns(10440, **boss_columns(
    'boss_baron_rivendare_rework', 96.525, damage_modifier=8, CreatureImmunitiesId=IMMUNITY_BARON_STOCK,
))
