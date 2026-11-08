"""
Scholomance build WP-S10: Lady Illucia Barov (10502)
(.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row S10; build spec
docs/dungeons/scholomance-rework.md SC 2695-2741). WP-S10 owns this file; WP-KS wrote the skeleton.

Skeleton (WP-KS, handoff s4 row KS): the boss is bound to its C++ script (modules/mod-dungeon-bosses
src/Scholomance/boss_lady_illucia_barov_rework.cpp), SmartAI off, the build spec's normal health
(160k: HealthModifier 65.52 on the level 60 class base 2,442), stun immunity 1972 and
flags_extra 1 (INSTANCE_BIND). Heroic health and its
overrides are WP-H's (source/world/dungeons/scholomance.py). Its solo lesson (detention) and examiner mode are
C++; the Graduate Examiner entry (300548-300554) is declared by WP-S13.

TODO(WP-S10): spells in its slice (kSpellsIllucia of ScholomanceRework.h), the boss-kit creatures named in the
header's ScholomanceCreatures enum, DamageModifier, the visual ids from ._visuals (WP-V). The SQL rev
(data/sql/updates/pending_db_world/) drops the SmartAI rows and adds the texts.
"""

from lib.dsl.registry import creature_template_columns

from ._common import boss_columns

creature_template_columns(10502, **boss_columns('boss_lady_illucia_barov_rework', 65.52))
