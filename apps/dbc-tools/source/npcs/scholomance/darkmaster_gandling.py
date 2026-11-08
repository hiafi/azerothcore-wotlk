"""
Scholomance build WP-S11: Darkmaster Gandling (1853), normal and heroic, and detention
(.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row S11, s3.7; build spec
docs/dungeons/scholomance-rework.md SC 3034-3101). WP-S11 owns this file; WP-KS wrote the skeleton.

Skeleton (WP-KS, handoff s4 row KS): the boss is rebound from the stock boss_darkmaster_gandling (the stock C++ file
stays untouched) to modules/mod-dungeon-bosses src/Scholomance/boss_darkmaster_gandling_rework.cpp, SmartAI off (his
12 dormant rows go in S11's SQL rev), the build spec's normal health (280k: HealthModifier 111.332 on the level 61
class base 2,515), stun immunity 1972 (in place of -346, which also blocked interrupts; s7 #9) and flags_extra 1
(INSTANCE_BIND). He stays rank 1 (stock). Heroic health and its overrides are WP-H's
(source/world/dungeons/scholomance.py).

TODO(WP-S11): spells in its slice (kSpellsGandling of ScholomanceRework.h), the Expelled Student 300544, the
Ravenian's echo 300545, the lesson and portal stalkers 300546-300547 (KIT_HELPER), DamageModifier, the visual ids
from ._visuals (WP-V); the Risen Guardian 11598 is retired.
"""

from lib.dsl.registry import creature_template_columns

from ._common import BIND_WAVE_C, boss_columns

# Held back until wave C binds this boss (_common.py BIND_WAVE_C; R-A S-11): stock until then.
if BIND_WAVE_C:
    creature_template_columns(1853, **boss_columns('boss_darkmaster_gandling_rework', 111.332))
