"""
Scholomance build WP-S5: Instructor Malicia (10505)
(.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row S5; build spec
docs/dungeons/scholomance-rework.md SC 1431-1488). WP-S5 owns this file; WP-KS wrote the skeleton.

Skeleton (WP-KS, handoff s4 row KS): the boss is bound to its C++ script (modules/mod-dungeon-bosses
src/Scholomance/boss_instructor_malicia_rework.cpp), SmartAI off, the build spec's normal health
(160k: HealthModifier 65.52 on the level 60 class base 2,442), stun immunity 1972 and
flags_extra 1 (INSTANCE_BIND). Heroic health and its
overrides are WP-H's (source/world/dungeons/scholomance.py). Its solo lesson (detention) and examiner mode are
C++; the Graduate Examiner entry (300548-300554) is declared by WP-S13.

TODO(WP-S5): spells in its slice (kSpellsMalicia of ScholomanceRework.h), the boss-kit creatures named in the
header's ScholomanceCreatures enum, DamageModifier, the visual ids from ._visuals (WP-V). The SQL rev
(data/sql/updates/pending_db_world/) drops the SmartAI rows and adds the texts.
"""

from lib.dsl.registry import creature_template_columns

from ._common import boss_columns

creature_template_columns(10505, **boss_columns('boss_instructor_malicia_rework', 65.52))
