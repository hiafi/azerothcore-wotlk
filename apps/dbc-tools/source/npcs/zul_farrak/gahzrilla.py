"""
Zul'Farrak build WP-D7 (.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.5 row D7; build spec
docs/dungeons/zul-farrak-rework.md SP 2001-2415 (Build spec 2298)). WP-D7 owns this file; WP-S0 wrote the skeleton.

TODO(WP-D7): spells in its slice (kSpellsPool of modules/mod-dungeon-bosses src/ZulFarrak/ZulFarrakRework.h,
214110-214149), the build creatures of the header's ZfCreatures enum (npc_zf_puddle (301030)), the visual ids from
._visuals (WP-V). The SQL rev (data/sql/updates/pending_db_world/rev_gahzrilla_zul_farrak.sql) adds the texts and the
rows dbc-tools cannot declare. Heroic health and its overrides are WP-H's (source/world/dungeons/zul_farrak.py).

Skeleton (WP-S0, handoff s3.2 item 8): bound to its C++ script, SmartAI off (rev_skeleton_zul_farrak.sql drops the
rows), the normal health of s3.6 (s7 #1 A: x1.6), the stock DamageModifier until T unless a ruling says otherwise,
immunity 1972, INSTANCE_BIND with both assist flags, detection range 12:

- 7795 boss_velratha_rework: normal health 112,007 = 83.4 on the level 46 mage base 1,343.
- 7273 boss_gahzrilla_rework: normal health 208,020 = 108.4 on the level 46 warrior base 1,919.
"""

from lib.dsl.registry import creature_template_columns

from ._common import boss_columns

creature_template_columns(7795, **boss_columns(
    'boss_velratha_rework', 83.4, damage_modifier=2.4,
))

creature_template_columns(7273, **boss_columns(
    'boss_gahzrilla_rework', 108.4, damage_modifier=3.5,
))
