"""
Shadowfang Keep build WP-S4: Commander Springvale (.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md
s3.5 rows SP1-SP8, s3.6 row S4; build spec docs/dungeons/shadowfang-keep-rework.md SK 754-812 (build spec), SK 625-753
(design)). WP-S4 owns this file (its spells: kSpellsSpringvale in modules/mod-dungeon-bosses
src/ShadowfangKeep/ShadowfangKeepRework.h only; SpringvaleLogic.h names the same ids).

STUB from WP-K (the SFK layer): binds 4278 to boss_commander_springvale_rework (SmartAI off; the stock rows are dropped
by WP-S4's SQL rev), normal health HealthModifier 28 (handoff s3.7), stun immune (IMMUNITY_BOSS_STUN 1972, s7 #8).
Heroic health is WP-H's override in source/world/dungeons/shadowfang_keep.py.

TODO(WP-S4): the boss-kit spells and creatures of handoff s3.5 / s3.6 row S4, and any other normal column (add it to the
creature_template_columns call below: one call per entry).
"""

from lib.dsl.registry import creature_template_columns

from ._common import boss_columns

creature_template_columns(4278, **boss_columns('boss_commander_springvale_rework', 28))
