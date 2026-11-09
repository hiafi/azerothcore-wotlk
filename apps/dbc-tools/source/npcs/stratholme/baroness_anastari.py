"""
Stratholme build WP-S10: Baroness Anastari (10436)
(.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.5 row S10; build spec
docs/dungeons/stratholme-rework.md ST 2630-2677). WP-S10 owns this file; WP-S0 wrote the skeleton.

Skeleton (WP-S0, handoff s3.2 item 3): the boss is bound to its C++ script (modules/mod-dungeon-bosses
src/Stratholme/boss_baroness_anastari_rework.cpp), SmartAI off, the build spec's normal health (170k: HealthModifier
71.76 on the level 59 paladin class base 2,369), stun immunity 1972, INSTANCE_BIND (flags_extra 1), DamageModifier 3.5
(the stock value: base SQL and the 2026_09_27_06 sniff update; the live value differed only where mod-progression left
one). Heroic health and its overrides are WP-H's (source/world/dungeons/stratholme.py).

TODO(WP-S10): spells in its slice (kSpellsBaroness of StratholmeRework.h, 206625-206644), the boss-kit creatures named
in the header's StratholmeCreatures enum, the visual ids from ._visuals (WP-V-1). The SQL rev
(data/sql/updates/pending_db_world/) drops the SmartAI rows and adds the texts.
"""

from lib.dsl.registry import creature_template_columns

from ._common import boss_columns

creature_template_columns(10436, **boss_columns(
    'boss_baroness_anastari_rework', 71.76, damage_modifier=3.5,
))
