"""
Scholomance build WP-S1: Jandice Barov (10503)
(.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row S1; build spec
docs/dungeons/scholomance-rework.md SC 546-601). WP-S1 owns this file; WP-KS wrote the skeleton.

Skeleton (WP-KS, handoff s4 row KS): the boss is bound to its C++ script (modules/mod-dungeon-bosses
src/Scholomance/boss_jandice_barov_rework.cpp), SmartAI off, the build spec's normal health
(175k: HealthModifier 69.583 on the level 61 class base 2,515), stun immunity 1972 and
flags_extra 1 (INSTANCE_BIND). Heroic health and its
overrides are WP-H's (source/world/dungeons/scholomance.py).

TODO(WP-S1): spells in its slice (kSpellsJandice of ScholomanceRework.h), the boss-kit creatures named in the
header's ScholomanceCreatures enum, DamageModifier, the visual ids from ._visuals (WP-V). The SQL rev
(data/sql/updates/pending_db_world/) drops the SmartAI rows and adds the texts.
"""

from lib.dsl.registry import creature_template_columns

from ._common import boss_columns

creature_template_columns(10503, **boss_columns('boss_jandice_barov_rework', 69.583))
