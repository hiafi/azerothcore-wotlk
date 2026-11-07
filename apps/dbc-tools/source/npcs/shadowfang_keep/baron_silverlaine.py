"""
Shadowfang Keep build WP-S3: Baron Silverlaine (.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md
s3.5 rows BS1-BS7, s3.6 row S3; build spec docs/dungeons/shadowfang-keep-rework.md SK 578-621 (build spec), SK 483-577
(design)). WP-S3 owns this file (its spells: kSpellsSilverlaine in modules/mod-dungeon-bosses
src/ShadowfangKeep/ShadowfangKeepRework.h only; SilverlaineLogic.h names the same ids).

STUB from WP-K (the SFK layer): binds 3887 to boss_baron_silverlaine_rework (SmartAI off; the stock rows are dropped by
WP-S3's SQL rev), normal health HealthModifier 25 (handoff s3.7), stun immune (IMMUNITY_BOSS_STUN 1972, s7 #8). Heroic
health is WP-H's override in source/world/dungeons/shadowfang_keep.py.

TODO(WP-S3): the boss-kit spells and creatures of handoff s3.5 / s3.6 row S3, and any other normal column (add it to the
creature_template_columns call below: one call per entry).
"""

from lib.dsl.registry import creature_template_columns

from ._common import boss_columns

creature_template_columns(3887, **boss_columns('boss_baron_silverlaine_rework', 25))
