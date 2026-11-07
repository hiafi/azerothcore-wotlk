"""
Shadowfang Keep build WP-S2: Razorclaw the Butcher (.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md
s3.5 rows RC1-RC4, s3.6 row S2; build spec docs/dungeons/shadowfang-keep-rework.md SK 444-479 (build spec), SK 357-443
(design)). WP-S2 owns this file (its spells: kSpellsRazorclaw in modules/mod-dungeon-bosses
src/ShadowfangKeep/ShadowfangKeepRework.h only; RazorclawLogic.h names the same ids).

STUB from WP-K (the SFK layer): binds 3886 to boss_razorclaw_rework (SmartAI off; the stock rows are dropped by WP-S2's
SQL rev), normal health HealthModifier 33 (handoff s3.7), stun immune (IMMUNITY_BOSS_STUN 1972, s7 #8). Heroic health is
WP-H's override in source/world/dungeons/shadowfang_keep.py.

TODO(WP-S2): the boss-kit spells and creatures of handoff s3.5 / s3.6 row S2, and any other normal column (add it to the
creature_template_columns call below: one call per entry).
"""

from lib.dsl.registry import creature_template_columns

from ._common import boss_columns

creature_template_columns(3886, **boss_columns('boss_razorclaw_rework', 33))
