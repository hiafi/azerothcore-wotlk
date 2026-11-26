"""
Zul'Farrak build WP-D3 (.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.5 row D3; build spec
docs/dungeons/zul-farrak-rework.md SP 809-1099 (Build spec 1009)). WP-D3 owns this file; WP-S0 wrote the skeleton.

TODO(WP-D3): spells in its slice (kSpellsZumrah of modules/mod-dungeon-bosses src/ZulFarrak/ZulFarrakRework.h,
213920-213959), the build creatures of the header's ZfCreatures enum (npc_zf_empty_vessel (301010), npc_zf_lost_soul
(301011), npc_zf_bound_dead (301012), the grave stalker 301013), the visual ids from ._visuals (WP-V). The SQL rev
(data/sql/updates/pending_db_world/rev_zumrah_zul_farrak.sql) adds the texts and the rows dbc-tools cannot declare.
Heroic health and its overrides are WP-H's (source/world/dungeons/zul_farrak.py).

Skeleton (WP-S0, handoff s3.2 item 8): bound to its C++ script, SmartAI off (rev_skeleton_zul_farrak.sql drops the
rows), the normal health of s3.6 (s7 #1 A: x1.6), the stock DamageModifier until T unless a ruling says otherwise,
immunity 1972, INSTANCE_BIND with both assist flags, detection range 12:

- 7271 boss_zumrah_rework: normal health 176,065 = 114.7 on the level 46 paladin base 1,535.
"""

from lib.dsl.registry import creature_template_columns

from ._common import boss_columns

creature_template_columns(7271, **boss_columns(
    'boss_zumrah_rework', 114.7, damage_modifier=2.4,
))
