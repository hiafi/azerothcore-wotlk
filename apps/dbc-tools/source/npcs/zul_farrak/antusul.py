"""
Zul'Farrak build WP-D2 (.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.5 row D2; build spec
docs/dungeons/zul-farrak-rework.md SP 534-807 (Build spec 733)). WP-D2 owns this file; WP-S0 wrote the skeleton.

TODO(WP-D2): spells in its slice (kSpellsAntusul of modules/mod-dungeon-bosses src/ZulFarrak/ZulFarrakRework.h,
213890-213919), the build creatures of the header's ZfCreatures enum (npc_antusul_servant_rework (8156, stub
registered here; the Earthgrab totem 6066's SmartAI is this WP's to drop)), the visual ids from ._visuals (WP-V). The
SQL rev (data/sql/updates/pending_db_world/rev_antusul_zul_farrak.sql) adds the texts and the rows dbc-tools cannot
declare. Heroic health and its overrides are WP-H's (source/world/dungeons/zul_farrak.py).

Skeleton (WP-S0, handoff s3.2 item 8): bound to its C++ script, SmartAI off (rev_skeleton_zul_farrak.sql drops the
rows), the normal health of s3.6 (s7 #1 A: x1.6), the stock DamageModifier until T unless a ruling says otherwise,
immunity 1972, INSTANCE_BIND with both assist flags, detection range 12:

- 8127 boss_antusul_rework: normal health 159,947 = 104.2 on the level 46 paladin base 1,535.
- 8156 Servant of Antu'sul: npc_antusul_servant_rework (stub in boss_antusul_rework.cpp), SmartAI
  off (the S0 rev drops its row); stock health and damage until this WP.
"""

from lib.dsl.registry import creature_template_columns

from ._common import boss_columns

creature_template_columns(8127, **boss_columns(
    'boss_antusul_rework', 104.2, damage_modifier=4.25,
))

# The Servant's script (stock health; its SmartAI row dropped by the S0 rev).
creature_template_columns(8156, ScriptName='npc_antusul_servant_rework', AIName='')
