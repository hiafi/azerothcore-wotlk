"""
Stratholme build WP-S12: Maleki the Pallid (10438)
(.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.5 row S12; build spec
docs/dungeons/stratholme-rework.md ST 3160-3211). WP-S12 owns this file; WP-S0 wrote the skeleton.

Skeleton (WP-S0, handoff s3.2 item 3): the boss is bound to its C++ script (modules/mod-dungeon-bosses
src/Stratholme/boss_maleki_the_pallid_rework.cpp), SmartAI off, the build spec's normal health (170k: HealthModifier
77.237 on the level 61 mage class base 2,201), stun immunity 1972, flags_extra 0x4000001 (his stock 0x4000000 plus
INSTANCE_BIND), DamageModifier 3.5 (the stock value: base SQL and the 2026_09_27_06 sniff update; the live value
differed only where mod-progression left one). Heroic health and its overrides are WP-H's
(source/world/dungeons/stratholme.py).

TODO(WP-S12): spells in its slice (kSpellsMaleki of StratholmeRework.h, 206665-206684), the boss-kit creatures named
in the header's StratholmeCreatures enum, the visual ids from ._visuals (WP-V-1). The SQL rev
(data/sql/updates/pending_db_world/) drops the SmartAI rows and adds the texts.
"""

from lib.dsl.registry import creature_template_columns

from ._common import FLAGS_EXTRA_INSTANCE_BIND, FLAGS_EXTRA_MALEKI_STOCK, boss_columns

creature_template_columns(10438, **boss_columns(
    'boss_maleki_the_pallid_rework', 77.237, damage_modifier=3.5,
    flags_extra=FLAGS_EXTRA_INSTANCE_BIND | FLAGS_EXTRA_MALEKI_STOCK,
))
