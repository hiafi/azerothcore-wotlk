"""
Zul'Farrak build WP-D1 (.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.5 row D1; build spec
docs/dungeons/zul-farrak-rework.md SP 321-532 (Build spec 463)). WP-D1 owns this file; WP-S0 wrote the skeleton.

TODO(WP-D1): spells in its slice (kSpellsTheka of modules/mod-dungeon-bosses src/ZulFarrak/ZulFarrakRework.h,
213860-213889), the build creatures of the header's ZfCreatures enum (npc_zf_persecutor_swarm (301005),
npc_zf_penitent_swarm (301006), the stalker 301007), the visual ids from ._visuals (WP-V). The SQL rev
(data/sql/updates/pending_db_world/rev_theka_zul_farrak.sql) adds the texts and the rows dbc-tools cannot declare.
Heroic health and its overrides are WP-H's (source/world/dungeons/zul_farrak.py).

Skeleton (WP-S0, handoff s3.2 item 8): bound to its C++ script, SmartAI off (rev_skeleton_zul_farrak.sql drops the
rows), the normal health of s3.6 (s7 #1 A: x1.6), the stock DamageModifier until T unless a ruling says otherwise,
immunity 1972, INSTANCE_BIND with both assist flags, detection range 12:

- 7272 boss_theka_rework: normal health 175,973 = 91.7 on the level 46 warrior base 1,919.
"""

from lib.dsl.registry import creature_template_columns

from ._common import boss_columns

creature_template_columns(7272, **boss_columns(
    'boss_theka_rework', 91.7, damage_modifier=2.4,
))
