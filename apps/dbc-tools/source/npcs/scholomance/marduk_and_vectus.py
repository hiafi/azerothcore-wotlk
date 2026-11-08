"""
Scholomance build WP-S3: Marduk Blackpool (10433) and Vectus (10432), one encounter with one shared health pool
(.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row S3; build spec
docs/dungeons/scholomance-rework.md SC 934-991). WP-S3 owns this file; WP-KS wrote the skeleton.

Skeleton (WP-KS, handoff s4 row KS): both are bound to their C++ scripts (modules/mod-dungeon-bosses
src/Scholomance/boss_marduk_vectus_rework.cpp), SmartAI off, stun immunity 1972 and flags_extra 1 (INSTANCE_BIND).
Both rows carry the pool's normal health (300k, handoff s3.6): HealthModifier 130.605 on Marduk's level 58 class base
2,297 and 122.85 on Vectus's level 60 class base 2,442. Heroic health and its overrides are WP-H's
(source/world/dungeons/scholomance.py).

TODO(WP-S3): spells in its slice (kSpellsMardukVectus of ScholomanceRework.h), the Graduate 300533, the students
10475 as props (creature_template_columns: unselectable, 8k / 12k), DamageModifier, the visual ids from ._visuals
(WP-V). The SQL rev (data/sql/updates/pending_db_world/) drops the SmartAI rows (10433, 10432, 10475) and fixes
Vectus's stray group 0 emote row.
"""

from lib.dsl.registry import creature_template_columns

from ._common import boss_columns

creature_template_columns(10433, **boss_columns('boss_marduk_blackpool_rework', 130.605))
creature_template_columns(10432, **boss_columns('boss_vectus_rework', 122.85))
