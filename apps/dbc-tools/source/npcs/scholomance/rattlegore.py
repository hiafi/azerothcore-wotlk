"""
Scholomance build WP-S2: Rattlegore (11622)
(.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row S2; build spec
docs/dungeons/scholomance-rework.md SC 733-778). WP-S2 owns this file; WP-KS wrote the skeleton.

Skeleton (WP-KS, handoff s4 row KS): the boss is bound to its C++ script (modules/mod-dungeon-bosses
src/Scholomance/boss_rattlegore_rework.cpp), SmartAI off, the build spec's normal health
(185k: HealthModifier 73.559 on the level 61 class base 2,515), stun immunity 1972 and
flags_extra 1 (INSTANCE_BIND). Heroic health and its
overrides are WP-H's (source/world/dungeons/scholomance.py).

TODO(WP-S2): spells in its slice (kSpellsRattlegore of ScholomanceRework.h), the boss-kit creatures named in the
header's ScholomanceCreatures enum, DamageModifier, the visual ids from ._visuals (WP-V). The SQL rev
(data/sql/updates/pending_db_world/) drops the SmartAI rows and adds the texts.
"""

from lib.dsl.registry import creature_template_columns

from ._common import boss_columns

creature_template_columns(11622, **boss_columns('boss_rattlegore_rework', 73.559))
