"""
Scholomance build WP-S4: Ras Frostwhisper (10508)
(.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row S4; build spec
docs/dungeons/scholomance-rework.md SC 1171-1230). WP-S4 owns this file; WP-KS wrote the skeleton.

Skeleton (WP-KS, handoff s4 row KS): the boss is bound to its C++ script (modules/mod-dungeon-bosses
src/Scholomance/boss_ras_frostwhisper_rework.cpp), SmartAI off, the build spec's normal health
(195k: HealthModifier 75.29 on the level 62 class base 2,590), stun immunity 1972 and
flags_extra 1 (INSTANCE_BIND). Heroic health and its
overrides are WP-H's (source/world/dungeons/scholomance.py).

TODO(WP-S4): spells in its slice (kSpellsRas of ScholomanceRework.h), the boss-kit creatures named in the
header's ScholomanceCreatures enum, DamageModifier, the visual ids from ._visuals (WP-V). The SQL rev
(data/sql/updates/pending_db_world/) drops the SmartAI rows and adds the texts.
"""

from lib.dsl.registry import creature_template_columns

from ._common import boss_columns

creature_template_columns(10508, **boss_columns('boss_ras_frostwhisper_rework', 75.29))
