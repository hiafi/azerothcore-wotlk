"""
Shadowfang Keep build WP-S7: Fenrus the Devourer (.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md
s3.5 rows FN1-FN8, s3.6 row S7; build spec docs/dungeons/shadowfang-keep-rework.md SK 1183-1234 (build spec), SK
1087-1182 (design)). WP-S7 owns this file (its spells: kSpellsFenrus in modules/mod-dungeon-bosses
src/ShadowfangKeep/ShadowfangKeepRework.h only; FenrusLogic.h names the same ids).

STUB from WP-K (the SFK layer): binds 4274 to boss_fenrus_the_devourer_rework (SmartAI off; the stock rows are dropped
by WP-S7's SQL rev), normal health HealthModifier 22 (handoff s3.7), stun immune (IMMUNITY_BOSS_STUN 1972, s7 #8).
Heroic health is WP-H's override in source/world/dungeons/shadowfang_keep.py.

TODO(WP-S7): the boss-kit spells and creatures of handoff s3.5 / s3.6 row S7, and any other normal column (add it to the
creature_template_columns call below: one call per entry).
"""

from lib.dsl.registry import creature_template_columns

from ._common import boss_columns

creature_template_columns(4274, **boss_columns('boss_fenrus_the_devourer_rework', 22))
