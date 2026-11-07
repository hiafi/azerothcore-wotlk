"""
Shadowfang Keep build WP-S8: Wolf Master Nandos (.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md
s3.5 rows NA1-NA8, s3.6 row S8; build spec docs/dungeons/shadowfang-keep-rework.md SK 1338-1390 (build spec), SK
1238-1337 (design)). WP-S8 owns this file (its spells: kSpellsNandos in modules/mod-dungeon-bosses
src/ShadowfangKeep/ShadowfangKeepRework.h only; NandosLogic.h names the same ids).

STUB from WP-K (the SFK layer): binds 3927 to boss_wolf_master_nandos_rework (SmartAI off; the stock rows are dropped by
WP-S8's SQL rev), normal health HealthModifier 18 (handoff s3.7), stun immune (IMMUNITY_BOSS_STUN 1972, s7 #8). Heroic
health is WP-H's override in source/world/dungeons/shadowfang_keep.py.

TODO(WP-S8): the boss-kit spells and creatures of handoff s3.5 / s3.6 row S8, and any other normal column (add it to the
creature_template_columns call below: one call per entry).
"""

from lib.dsl.registry import creature_template_columns

from ._common import boss_columns

creature_template_columns(3927, **boss_columns('boss_wolf_master_nandos_rework', 18))
