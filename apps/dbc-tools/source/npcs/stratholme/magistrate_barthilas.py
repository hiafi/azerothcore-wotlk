"""
Stratholme build WP-S9: Magistrate Barthilas (10435)
(.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.5 row S9; build spec
docs/dungeons/stratholme-rework.md ST 2355-2407). WP-S9 owns this file; WP-S0 wrote the skeleton.

Skeleton (WP-S0, handoff s3.2 item 3): the boss is bound to its C++ script (modules/mod-dungeon-bosses
src/Stratholme/boss_magistrate_barthilas_rework.cpp), SmartAI off, the build spec's normal health (180k:
HealthModifier 62.696 on the level 58 warrior class base 2,871), stun immunity 1972, INSTANCE_BIND (flags_extra 1),
DamageModifier 3.5 (the stock value: base SQL and the 2026_09_27_06 sniff update; the live value differed only where
mod-progression left one). Heroic health and its overrides are WP-H's (source/world/dungeons/stratholme.py).

TODO(WP-S9): spells in its slice (kSpellsBarthilas of StratholmeRework.h, 206605-206624), the boss-kit creatures named
in the header's StratholmeCreatures enum, the visual ids from ._visuals (WP-V-1). The SQL rev
(data/sql/updates/pending_db_world/) drops the SmartAI rows and adds the texts.
"""

from lib.dsl.registry import creature_template_columns

from ._common import boss_columns

creature_template_columns(10435, **boss_columns(
    'boss_magistrate_barthilas_rework', 62.696, damage_modifier=3.5,
))
