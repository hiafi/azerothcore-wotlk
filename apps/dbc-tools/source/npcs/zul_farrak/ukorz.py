"""
Zul'Farrak build WP-D6 (.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.5 row D6; build spec
docs/dungeons/zul-farrak-rework.md SP 1719-1999 (Build spec 1910)). WP-D6 owns this file; WP-S0 wrote the skeleton.

TODO(WP-D6): spells in its slice (kSpellsUkorz of modules/mod-dungeon-bosses src/ZulFarrak/ZulFarrakRework.h,
214070-214109), the build creatures of the header's ZfCreatures enum (npc_zf_quicksand (301025), npc_zf_creeping_sands
(301026)), the visual ids from ._visuals (WP-V). The SQL rev
(data/sql/updates/pending_db_world/rev_ukorz_zul_farrak.sql) adds the texts and the rows dbc-tools cannot declare.
Heroic health and its overrides are WP-H's (source/world/dungeons/zul_farrak.py).

Skeleton (WP-S0, handoff s3.2 item 8): bound to its C++ script, SmartAI off (rev_skeleton_zul_farrak.sql drops the
rows), the normal health of s3.6 (s7 #1 A: x1.6), the stock DamageModifier until T unless a ruling says otherwise,
immunity 1972, INSTANCE_BIND with both assist flags, detection range 12:

- 7267 boss_ukorz_rework: normal health 143,925 = 75.0 on the level 46 warrior base 1,919.
- 7797 boss_ruuzlu_rework: normal health 128,067 = 69.3 on the level 45 warrior base 1,848.
"""

from lib.dsl.registry import creature_template_columns

from ._common import boss_columns

creature_template_columns(7267, **boss_columns(
    'boss_ukorz_rework', 75.0, damage_modifier=2.4,
))

creature_template_columns(7797, **boss_columns(
    'boss_ruuzlu_rework', 69.3, damage_modifier=2.4,
))
