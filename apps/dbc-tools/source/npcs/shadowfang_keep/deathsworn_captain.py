"""
Shadowfang Keep build WP-S6: Deathsworn Captain (.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md
s3.5 rows DC1-DC3, s3.6 row S6; build spec docs/dungeons/shadowfang-keep-rework.md SK 1044-1083 (build spec), SK
956-1043 (design)). WP-S6 owns this file (its spells: kSpellsDeathswornCaptain in modules/mod-dungeon-bosses
src/ShadowfangKeep/ShadowfangKeepRework.h only; DeathswornCaptainLogic.h names the same ids).

STUB from WP-K (the SFK layer): binds 3872 to boss_deathsworn_captain_rework (SmartAI off; the stock rows are dropped by
WP-S6's SQL rev), normal health HealthModifier 17 (handoff s3.7), stun immune (IMMUNITY_BOSS_STUN 1972, s7 #8). Heroic
health is WP-H's override in source/world/dungeons/shadowfang_keep.py.

TODO(WP-S6): the boss-kit spells and creatures of handoff s3.5 / s3.6 row S6, and any other normal column (add it to the
creature_template_columns call below: one call per entry).
"""

from lib.dsl.registry import creature_template_columns

from ._common import boss_columns

creature_template_columns(3872, **boss_columns('boss_deathsworn_captain_rework', 17))
