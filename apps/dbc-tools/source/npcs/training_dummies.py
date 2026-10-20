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

# --- healsim boss (900015-900017) ---------------------------------------------------------------
# "Sim Raid Boss": the healing sim's damage source and the healer's optional DPS target (healing-sim PLAN
# section 1, D4), at levels 60/70/80. modules/mod-dpssim's npc_healsim_boss (SimHealBossAI.cpp) is its AI: it never
# swings, moves or evades, and the sim's Sim Damage Pulse 202900 / Sim Pin Hit 202901 casts
# (source/npcs/healsim_spells.py) are its only damage. Re-derived for that role, not cloned from the dummies above:
#   faction 14        hostile to every player (the dummies' 31 is not), so the healer can attack it and it holds combat
#                     references with the whole group.
#   rank 3            boss rank; type_flags 4 is CREATURE_TYPE_FLAG_BOSS_MOB, so boss-only branches (world-boss level
#                     difference, knockback immunity, boss triggers) behave as on a raid boss.
#   type 5 (Giant)    deliberately inert: not 9/mechanical (the dummies', which carries mechanical-only immunities and
#                     bonuses), not 7/humanoid (Mind Control, Polymorph and Sap rules apply) and not 10/unspecified
#                     (what trigger-like NPCs use).
#   HealthModifier    the dummies' 23809.5 (a pool the healer's DPS cannot dent) with RegenHealth 0, so it never
#                     regenerates; the AI also clamps damage so it never drops below 1 health.
#   DamageModifier 0  it never melees; a stray swing would deal nothing.
#   detection_range 0 it never aggroes anything by itself; the sim engages the group explicitly.
#   CreatureImmunitiesId -362  the boss set Gruul / Illidan / Lady Sacrolash use: every control mechanic, interrupt and
#                     disarm, knockback / pull, taunt and bind. A healer bot's stun or fear cannot disturb the boss.
#   flags_extra       NO_XP | NO_SKILL_GAINS | DONT_CALL_ASSISTANCE | IGNORE_ALL_ASSISTANCE_CALLS (0x06040040 =
#                     100925504): no XP, no weapon skill gains and no pulling of neighbouring creatures. unit_flags
#                     stays 0, so none of NOT_SELECTABLE / NON_ATTACKABLE / IMMUNE_TO_PC is set.
_HEALSIM_BOSS = dict(
    IconName="", faction=14, rank=3, detection_range=0, DamageModifier=0, BaseAttackTime=2000, RangeAttackTime=2000,
    unit_class=1, unit_flags2=2048, type=5, type_flags=4, HealthModifier=23809.5, RegenHealth=0,
    CreatureImmunitiesId=-362, flags_extra=100925504, ScriptName="npc_healsim_boss", VerifiedBuild=0,
)
for _entry, _level in ((900015, 60), (900016, 70), (900017, 80)):
    creature_template(
        _entry, "Sim Raid Boss", subname=f"Level {_level}", minlevel=_level, maxlevel=_level, **_HEALSIM_BOSS,
    )
    creature_model(_entry, display_id=3019)
