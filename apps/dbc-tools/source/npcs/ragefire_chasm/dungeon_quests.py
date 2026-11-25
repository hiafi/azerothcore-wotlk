"""
Ragefire Chasm build, the quests WP (Q; handoff 4.Q, section 7 #40 A;
.agents/plans/dungeon-quests/dungeon-quests.PLAN.md section 1): the entrance quest giver, in the `ragefire_chasm`
creature reservation (300989, source/ids.yaml).

    300989  Grunt Dranok  starts 5725 The Power to Destroy..., 5761 Slaying the Beast, 5722 Searching for the Lost
                          Satchel and 5723 Testing an Enemy's Strength; ends 5725, 5761, 5724 Returning the Lost
                          Satchel and 5723. He does not end 5722 (Maur Grimtotem's corpse, 11834, stays its ender and
                          starts 5724) and does not start 5724 (the corpse does).

A quest giver (npcflag 2) only, friendly to both factions (faction 35 is hostile to nobody, so no one attacks him), a
civilian (flags_extra 2: he never aggroes), level 18, no AI, no gossip, no loot, no subname (section 7 #40 A). The look
is the Orgrimmar Grunt's (3296): creature display 4259, a male orc in the grunt's plate. The row follows the Deadmines
and Shadowfang Keep quest givers' column set (source/npcs/deadmines/dungeon_quests.py). The spawn (normal difficulty
only, `spawnMask` 1: named in `normal_only_creatures` of source/world/dungeons/ragefire_chasm.py, WP-H), his weapon
(creature_equip_template), the quest starter and ender rows and the quests themselves are the hand-written
data/sql/updates/pending_db_world/rev_dungeon_quests_ragefire_chasm.sql; the row values (position, why) are in that
file's header.
"""

from lib.dsl.registry import creature_model, creature_template

_GIVER = dict(
    IconName='', exp=0, faction=35, npcflag=2, minlevel=18, maxlevel=18, rank=0, unit_class=1, speed_walk=1.0,
    speed_run=1.14286, speed_swim=1.0, speed_flight=1.0, detection_range=18.0, dmgschool=0, DamageModifier=1.0,
    BaseAttackTime=2000, RangeAttackTime=2000, BaseVariance=1.0, RangeVariance=1.0, unit_flags=0, unit_flags2=2048,
    dynamicflags=0, family=0, type=7, type_flags=0, lootid=0, pickpocketloot=0, skinloot=0, PetSpellDataId=0,
    VehicleId=0, mingold=0, maxgold=0, AIName='', MovementType=0, HoverHeight=1.0, HealthModifier=1.0,
    ManaModifier=1.0, ArmorModifier=1.0, ExperienceModifier=1.0, RacialLeader=0, movementId=0, RegenHealth=1,
    CreatureImmunitiesId=0, flags_extra=2, ScriptName='', VerifiedBuild=0, gossip_menu_id=0,
)

entrance_giver_300989 = creature_template(300989, 'Grunt Dranok', **_GIVER)
creature_model(300989, display_id=4259, idx=0)
