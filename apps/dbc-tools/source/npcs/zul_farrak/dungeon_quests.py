"""
Zul'Farrak build, the quests WP (Q; handoff 4.Q, section 7 #53 A, section 10; .agents/plans/dungeon-quests/
dungeon-quests.PLAN.md section 7): the entrance quest giver, in the `zul_farrak` creature reservation (301090,
source/ids.yaml).

    301090  Kizzi Fuseboot  "Steamwheedle Cartel"  starts and ends 2865 Scarab Shells, 3042 Troll Temper, 2846 Tiara of
                            the Deep, 2768 Divino-matic Rod and 2770 Gahz'rilla

A quest giver (npcflag 2) only, friendly to both factions (faction 35 is hostile to nobody, so no one attacks her), a
civilian (flags_extra 2: she never aggroes), level 46 (Theka's level and the Finder target of the dungeon's first
quests), no AI, no gossip, no loot. The look is Tran'rek's (7876): creature display 11379, a Gadgetzan goblin, the
"Steamwheedle look" the designer named (section 7 #53 A: the name is a placeholder until the designer says
otherwise). The row follows the Ragefire Chasm, Deadmines and Shadowfang Keep quest givers' column set
(source/npcs/ragefire_chasm/dungeon_quests.py). The spawn (normal difficulty only, `spawnMask` 1: named in
`normal_only_creatures` of source/world/dungeons/zul_farrak.py), the quest starter and ender rows and the quest edits
are the hand-written data/sql/updates/pending_db_world/rev_quests_zul_farrak.sql; the row values (position, why, the
measurements) are in that file's header.
"""

from lib.dsl.registry import creature_model, creature_template

_GIVER = dict(
    IconName='', exp=0, faction=35, npcflag=2, minlevel=46, maxlevel=46, rank=0, unit_class=1, speed_walk=1.0,
    speed_run=1.14286, speed_swim=1.0, speed_flight=1.0, detection_range=18.0, dmgschool=0, DamageModifier=1.0,
    BaseAttackTime=2000, RangeAttackTime=2000, BaseVariance=1.0, RangeVariance=1.0, unit_flags=0, unit_flags2=2048,
    dynamicflags=0, family=0, type=7, type_flags=0, lootid=0, pickpocketloot=0, skinloot=0, PetSpellDataId=0,
    VehicleId=0, mingold=0, maxgold=0, AIName='', MovementType=0, HoverHeight=1.0, HealthModifier=1.0,
    ManaModifier=1.0, ArmorModifier=1.0, ExperienceModifier=1.0, RacialLeader=0, movementId=0, RegenHealth=1,
    CreatureImmunitiesId=0, flags_extra=2, ScriptName='', VerifiedBuild=0, gossip_menu_id=0,
)

entrance_giver_301090 = creature_template(
    301090, 'Kizzi Fuseboot', subname='Steamwheedle Cartel', **_GIVER,
)
creature_model(301090, display_id=11379, idx=0)
