"""
Scholomance build WP-S7: Lorekeeper Polkelt (10901)
(.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row S7; build spec
docs/dungeons/scholomance-rework.md SC 1979-2036). WP-S7 owns this file; WP-KS wrote the skeleton.

Skeleton (WP-KS, handoff s4 row KS): the boss is bound to its C++ script (modules/mod-dungeon-bosses
src/Scholomance/boss_lorekeeper_polkelt_rework.cpp), SmartAI off, the build spec's normal health
(175k: HealthModifier 57.339 on the level 60 class base 3,052), stun immunity 1972 and
flags_extra 1 (INSTANCE_BIND). Heroic health and its
overrides are WP-H's (source/world/dungeons/scholomance.py). Its solo lesson (detention) and examiner mode are
C++; the Graduate Examiner entry (300548-300554) is declared by WP-S13.

TODO(WP-S7): spells in its slice (kSpellsPolkelt of ScholomanceRework.h), the boss-kit creatures named in the
header's ScholomanceCreatures enum, DamageModifier, the visual ids from ._visuals (WP-V). The SQL rev
(data/sql/updates/pending_db_world/) drops the SmartAI rows and adds the texts.
"""

from lib.dsl.registry import creature_template_columns

from ._common import BIND_WAVE_B, boss_columns

# Held back until wave B binds this boss (_common.py BIND_WAVE_B; R-A S-11): stock until then.
if BIND_WAVE_B:
    creature_template_columns(10901, **boss_columns('boss_lorekeeper_polkelt_rework', 57.339))
