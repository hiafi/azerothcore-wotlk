"""
Zul'Farrak build WP-D4b (.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.5 row D4b; build spec
docs/dungeons/zul-farrak-rework.md SP 1101-1432 (Build spec 1346; PY4-PY16)). WP-D4b owns this file; WP-S0 wrote the
skeleton.

TODO(WP-D4b): spells in its slice (kSpellsStair of modules/mod-dungeon-bosses src/ZulFarrak/ZulFarrakRework.h,
213990-214029), the build creatures of the header's ZfCreatures enum (npc_zf_sandfury_berserker (301015),
npc_zf_sandfury_hexmaster (301016), npc_zf_sandfury_witch_doctor (301017), npc_zf_weegli_barrel (301018), the lane
stalker 301019), the visual ids from ._visuals (WP-V). The SQL rev
(data/sql/updates/pending_db_world/rev_pyramid_stair_zul_farrak.sql) adds the texts and the rows dbc-tools cannot
declare. Heroic health and its overrides are WP-H's (source/world/dungeons/zul_farrak.py).

Skeleton (WP-S0, handoff s3.2 item 8): bound to its C++ script, SmartAI off (rev_skeleton_zul_farrak.sql drops the
rows), the normal health of s3.6 (s7 #1 A: x1.6), the stock DamageModifier until T unless a ruling says otherwise,
immunity 1972, INSTANCE_BIND with both assist flags, detection range 12:

- 7275 boss_sezzziz_rework: normal health 95,938 = 62.5 on the level 46 paladin base 1,535; DamageModifier 2.4
  from 7.5 (s7 #44 A).
- 7796 boss_nekrum_rework: normal health 48,048 = 26.0 on the level 45 warrior base 1,848; DamageModifier 3.0 from
  7.5 (s7 #44 A).
"""

from lib.dsl.registry import creature_template_columns

from ._common import boss_columns

creature_template_columns(7275, **boss_columns(
    'boss_sezzziz_rework', 62.5, damage_modifier=2.4,
))

creature_template_columns(7796, **boss_columns(
    'boss_nekrum_rework', 26.0, damage_modifier=3.0,
))
