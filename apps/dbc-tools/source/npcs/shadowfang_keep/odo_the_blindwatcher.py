"""
Shadowfang Keep build WP-S5: Odo the Blindwatcher (.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md
s3.5 rows OD1-OD6, s3.6 row S5; build spec docs/dungeons/shadowfang-keep-rework.md SK 904-952 (build spec), SK 816-903
(design)). WP-S5 owns this file (its spells: kSpellsOdo in modules/mod-dungeon-bosses
src/ShadowfangKeep/ShadowfangKeepRework.h only; OdoLogic.h names the same ids).

STUB from WP-K (the SFK layer): binds 4279 to boss_odo_the_blindwatcher_rework (SmartAI off; the stock rows are dropped
by WP-S5's SQL rev), normal health HealthModifier 28 (handoff s3.7), stun immune (IMMUNITY_BOSS_STUN 1972, s7 #8).
Heroic health is WP-H's override in source/world/dungeons/shadowfang_keep.py.

TODO(WP-S5): the boss-kit spells and creatures of handoff s3.5 / s3.6 row S5, and any other normal column (add it to the
creature_template_columns call below: one call per entry).
"""

from lib.dsl.registry import creature_template_columns

from ._common import boss_columns

creature_template_columns(4279, **boss_columns('boss_odo_the_blindwatcher_rework', 28))
