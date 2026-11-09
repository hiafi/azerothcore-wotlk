"""
Stratholme build WP-S3: Timmy the Cruel (10808)
(.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.5 row S3; build spec
docs/dungeons/stratholme-rework.md ST 1035-1090). WP-S3 owns this file; WP-S0 wrote the skeleton.

Skeleton (WP-S0, handoff s3.2 item 3): the boss is bound to its C++ script (modules/mod-dungeon-bosses
src/Stratholme/boss_timmy_the_cruel_rework.cpp), SmartAI off, the build spec's normal health (170k: HealthModifier
59.213 on the level 58 warrior class base 2,871), stun immunity 1972, INSTANCE_BIND (flags_extra 1), DamageModifier 13
(the live value; the boss WP states its own). Heroic health and its overrides are WP-H's
(source/world/dungeons/stratholme.py). Wave 2: nothing is declared until BIND_WAVE_2 flips (_common.py).

TODO(WP-S3): spells in its slice (kSpellsTimmy of StratholmeRework.h, 206460-206479), the boss-kit creatures named in
the header's StratholmeCreatures enum, the visual ids from ._visuals (WP-V-2). The SQL rev
(data/sql/updates/pending_db_world/) drops the SmartAI rows and adds the texts.
"""

from lib.dsl.registry import creature_template_columns

from ._common import BIND_WAVE_2, boss_columns

# Held back until wave 2 binds this boss (_common.py BIND_WAVE_2): stock until then.
if BIND_WAVE_2:
    creature_template_columns(10808, **boss_columns(
        'boss_timmy_the_cruel_rework', 59.213, damage_modifier=13,
    ))
