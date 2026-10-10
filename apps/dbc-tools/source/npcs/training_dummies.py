"""Training dummies and the healing dummy - test/tool NPCs that belong to no class rework.

Declared from `source/ids.yaml`'s `npc_tools` block (900000-900099); loaded by generate.py via
`registry.load_classes_dir(source/npcs/)` next to the class folders. dpssim stage MT0
(.agents/plans/dpssim-multi-target/dpssim-multi-target.STAGE-MT0-HANDOFF.md) moved the first nine
entries here from hand-written migrations; the values below reproduce their live rows, so
generate.py emits nothing for them. 900010 (Quinn Testbury) and 900012 (Ursana) are NPC tools too
but stay hand-written. World spawns (`creature` rows) are not declared by dbc-tools.
"""

from lib.dsl.registry import creature_model, creature_template

# --- Player-facing training dummies (900001-900003) ----------------------------------------------
# Stand in Stormwind for players to hit; ScriptName npc_custom_training_dummy
# (src/server/scripts/Custom/custom_training_dummy.cpp, script name changed by
# data/sql/updates/db_world/2026_09_29_03.sql). Created by 2026_09_01_26.sql (REPLACE INTO).
_TRAINING_DUMMY = dict(
    IconName="", faction=31, rank=3, DamageModifier=35, BaseAttackTime=2000, RangeAttackTime=2000,
    unit_class=1, unit_flags2=2048, type=9, type_flags=4, HealthModifier=23809.5,
    CreatureImmunitiesId=-26, flags_extra=262144, ScriptName="npc_custom_training_dummy",
    VerifiedBuild=None,
)
for _entry, _level in ((900001, 60), (900002, 70), (900003, 80)):
    creature_template(
        _entry, "Training Dummy", subname=f"Level {_level}", minlevel=_level, maxlevel=_level,
        **_TRAINING_DUMMY,
    )
    creature_model(_entry, display_id=3019, verified_build=None)

# --- dpssim sim dummies (900004-900006) ----------------------------------------------------------
# Targets of modules/mod-dpssim (SimTarget picks the entry by level); same stats as the player
# dummies above, but ScriptName npc_dpssim_training_dummy (modules/mod-dpssim/src/SimDummyAI.cpp). Created by
# 2026_09_14_02.sql / 2026_09_14_03.sql (REPLACE INTO).
_SIM_DUMMY = {**_TRAINING_DUMMY, "ScriptName": "npc_dpssim_training_dummy"}
for _entry, _level in ((900004, 60), (900005, 70), (900006, 80)):
    creature_template(
        _entry, "Training Dummy (dpssim)", subname=f"Level {_level}", minlevel=_level,
        maxlevel=_level, **_SIM_DUMMY,
    )
    creature_model(_entry, display_id=3019, verified_build=None)

# --- dpssim elite pack dummies (900007-900009) ---------------------------------------------------
# The multi-target sim's extra pack members (plan §3.4): the sim dummy with rank elite (1) and no
# BOSS_MOB type flag, so they behave like trash next to the boss-rank 900004-900006.
_PACK_DUMMY = {**_SIM_DUMMY, "rank": 1, "type_flags": 0, "VerifiedBuild": 0}  # live rows are 0, not NULL
for _entry, _level in ((900007, 60), (900008, 70), (900009, 80)):
    creature_template(
        _entry, "Training Dummy (dpssim pack)", subname=f"Level {_level}", minlevel=_level,
        maxlevel=_level, **_PACK_DUMMY,
    )
    creature_model(_entry, display_id=3019)

# --- Healing Training Dummy (900011, 900013, 900014) ---------------------------------------------
# For healers: friendly, healable, pinned at 30% HP by npc_healing_dummy (src/server/scripts/
# Custom/custom_healing_dummy.cpp). 900013 is the variant that keeps the healer in combat for 2 min;
# 900014 is the hostile invisible anchor it spawns for that. Created by 2026_09_23_01.sql,
# 2026_09_27_02.sql and 2026_09_27_05.sql.
_HEALING_DUMMY = dict(
    IconName="", faction=35, DamageModifier=35, BaseAttackTime=2000, RangeAttackTime=2000,
    unit_class=1, unit_flags2=2048, type=7, type_flags=4100, HealthModifier=23809.5, RegenHealth=0,
    CreatureImmunitiesId=-26, flags_extra=262144, VerifiedBuild=0,
)
creature_template(
    900011, "Healing Training Dummy", subname="Level 80", minlevel=80, maxlevel=80,
    ScriptName="npc_healing_dummy", **_HEALING_DUMMY,
)
creature_model(900011, display_id=3019)
creature_template(
    900013, "Healing Training Dummy", subname="In Combat (2 min)", minlevel=80, maxlevel=80,
    ScriptName="npc_healing_dummy_combat", **_HEALING_DUMMY,
)
creature_model(900013, display_id=3019)
creature_template(
    900014, "Healing Dummy Combat Anchor", subname="", IconName="", minlevel=80, maxlevel=80,
    faction=14, detection_range=0, DamageModifier=35, BaseAttackTime=2000, RangeAttackTime=2000,
    unit_class=1, unit_flags=33554946, type=10, flags_extra=2,
    ScriptName="npc_healing_dummy_combat_anchor", VerifiedBuild=0,
)
creature_model(900014, display_id=11686)
