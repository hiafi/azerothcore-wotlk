"""
Stratholme build WP-S5: Cannon Master Willey (10997)
(.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.5 row S5; build spec
docs/dungeons/stratholme-rework.md ST 1444-1502). WP-S5 owns this file; WP-S0 wrote the skeleton.

Skeleton (WP-S0, handoff s3.2 item 3): the boss is bound to its C++ script (modules/mod-dungeon-bosses
src/Stratholme/boss_cannon_master_willey_rework.cpp), SmartAI off, the build spec's normal health (185k:
HealthModifier 60.616 on the level 60 warrior class base 3,052), stun immunity 1972, INSTANCE_BIND (flags_extra 1),
DamageModifier 7 (the live value; the boss WP states its own). Heroic health and its overrides are WP-H's
(source/world/dungeons/stratholme.py). Wave 2: nothing is declared until BIND_WAVE_2 flips (_common.py).

TODO(WP-S5): spells in its slice (kSpellsWilley of StratholmeRework.h, 206500-206519), the boss-kit creatures named in
the header's StratholmeCreatures enum, the visual ids from ._visuals (WP-V-2). The SQL rev
(data/sql/updates/pending_db_world/) drops the SmartAI rows and adds the texts.
"""

from lib.dsl.registry import creature_template_columns

from ._common import BIND_WAVE_2, boss_columns

# Held back until wave 2 binds this boss (_common.py BIND_WAVE_2): stock until then.
if BIND_WAVE_2:
    creature_template_columns(10997, **boss_columns(
        'boss_cannon_master_willey_rework', 60.616, damage_modifier=7,
    ))
