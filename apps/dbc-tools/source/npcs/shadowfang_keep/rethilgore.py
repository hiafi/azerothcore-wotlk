"""
Shadowfang Keep build WP-S1: Rethilgore (.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md s3.5 rows
RG1-RG6, s3.6 row S1; build spec docs/dungeons/shadowfang-keep-rework.md SK 310-353 (normal and heroic), SK 191-309
(design)). WP-S1 owns this file (its spells: kSpellsRethilgore in modules/mod-dungeon-bosses
src/ShadowfangKeep/ShadowfangKeepRework.h only; RethilgoreLogic.h names the same ids).

STUB from WP-K (the SFK layer): binds 3914 to boss_rethilgore_rework (SmartAI off; the stock rows are dropped by WP-S1's
SQL rev), normal health HealthModifier 25 (handoff s3.7), stun immune (IMMUNITY_BOSS_STUN 1972, s7 #8). Heroic health is
WP-H's override in source/world/dungeons/shadowfang_keep.py.

TODO(WP-S1): the boss-kit spells and creatures of handoff s3.5 / s3.6 row S1, and any other normal column (add it to the
creature_template_columns call below: one call per entry).
"""

from lib.dsl.registry import creature_template_columns

from ._common import boss_columns

creature_template_columns(3914, **boss_columns('boss_rethilgore_rework', 25))
