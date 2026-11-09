"""
Stratholme build WP-S7: Grand Crusader Dathrohan and Balnazzar (10812 and 10813)
(.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.5 row S7; build spec
docs/dungeons/stratholme-rework.md ST 2077-2166). WP-S7 owns this file; WP-S0 wrote the skeleton.

Skeleton (WP-S0, handoff s3.2 item 3): the boss is bound to its C++ script (modules/mod-dungeon-bosses
src/Stratholme/boss_dathrohan_balnazzar_rework.cpp), SmartAI off, the build spec's normal health (250k / 220k:
HealthModifier 96.525 on the level 62 paladin class base 2,590), stun immunity 1972, INSTANCE_BIND (flags_extra 1),
Balnazzar 10813 gets the same script, HealthModifier 84.942 (220k) and DamageModifier 9 (live), DamageModifier 8.5
(the live value; the boss WP states its own). Heroic health and its overrides are WP-H's
(source/world/dungeons/stratholme.py). Wave 2: nothing is declared until BIND_WAVE_2 flips (_common.py).

TODO(WP-S7): spells in its slice (kSpellsDathrohan of StratholmeRework.h, 206545-206574), the boss-kit creatures named
in the header's StratholmeCreatures enum, the visual ids from ._visuals (WP-V-2). The SQL rev
(data/sql/updates/pending_db_world/) drops the SmartAI rows and adds the texts.
"""

from lib.dsl.registry import creature_template_columns

from ._common import BIND_WAVE_2, boss_columns

# Held back until wave 2 binds this boss (_common.py BIND_WAVE_2): stock until then.
if BIND_WAVE_2:
    creature_template_columns(10812, **boss_columns(
        'boss_dathrohan_balnazzar_rework', 96.525, damage_modifier=8.5,
    ))
    creature_template_columns(10813, **boss_columns(
        'boss_dathrohan_balnazzar_rework', 84.942, damage_modifier=9,
    ))
