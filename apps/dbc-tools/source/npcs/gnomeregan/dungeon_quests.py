"""
Gnomeregan build, the quests WP (Q; handoff 4.Q, section 7 #49 A, section 10; the dungeon doc's Dungeon quests
section): the exile quest giver, in the `gnomeregan` creature reservation (301190, source/ids.yaml).

    301190  Tinkmaster Fizzbolt  "Gnomeregan Exiles"  starts and ends 2922 Save Techbot's Brain!, 2924 Essential
                                 Artificials, 2928 Gyrodrillmatic Excavationators, 2930 Data Rescue, 2841 Rig Wars and
                                 2929 The Grand Betrayal (2945 Grime-Encrusted Ring is ended by the Sparklematic 5200)

One entry for all four spots (the entrance and the Workshop as static spawns in rev_quests_gnomeregan.sql, the two End
spots summoned by the instance: instance_gnomeregan_rework.cpp `NPC_EXILE`, restored after a restart), so every spot
gives and ends the same quests. A quest giver (npcflag 2) only, friendly to both factions (faction 35 is hostile to
nobody, so no one attacks him), a civilian (flags_extra 2: he never aggroes), level 28 (the dungeon's top and its
Finder target), no AI, no gossip, no loot, standing still. The look is the stock Gnomeregan Evacuee's: four creature
displays (6973 and 6974 male, 6975 and 6976 female, model info 0.35 / 1.725; the friendly stock entry 39265 wears the
same four), one at random per spawn (`creature_template_model`; `creature` has no per-spawn display column, so "one per
spot" of the handoff is the engine's pick, a playtest line). The name "Tinkmaster Fizzbolt" and the subname are the
handoff's placeholders until the designer says otherwise (#49 A). The row follows the Zul'Farrak, Ragefire Chasm,
Deadmines and Shadowfang Keep quest givers' column set (source/npcs/zul_farrak/dungeon_quests.py). He stays normal
only: `normal_only_creatures=(301190,)` in source/world/dungeons/gnomeregan.py, and the instance summons the End spots
on normal only. The quest starter and ender rows and the spawns are the hand-written
data/sql/updates/pending_db_world/rev_quests_gnomeregan.sql; the row values (positions, why, the measurements) are in
that file's header.
"""

from lib.dsl.registry import creature_model, creature_template

EXILE = 301190

# The stock Gnomeregan Evacuee (7843) displays, two male and two female gnomes. Equal weight.
_EVACUEE_DISPLAYS = (6973, 6974, 6975, 6976)

_GIVER = dict(
    IconName='', exp=0, faction=35, npcflag=2, minlevel=28, maxlevel=28, rank=0, unit_class=1, speed_walk=1.0,
    speed_run=1.14286, speed_swim=1.0, speed_flight=1.0, detection_range=18.0, dmgschool=0, DamageModifier=1.0,
    BaseAttackTime=2000, RangeAttackTime=2000, BaseVariance=1.0, RangeVariance=1.0, unit_flags=0, unit_flags2=2048,
    dynamicflags=0, family=0, type=7, type_flags=0, lootid=0, pickpocketloot=0, skinloot=0, PetSpellDataId=0,
    VehicleId=0, mingold=0, maxgold=0, AIName='', MovementType=0, HoverHeight=1.0, HealthModifier=1.0,
    ManaModifier=1.0, ArmorModifier=1.0, ExperienceModifier=1.0, RacialLeader=0, movementId=0, RegenHealth=1,
    CreatureImmunitiesId=0, flags_extra=2, ScriptName='', VerifiedBuild=0, gossip_menu_id=0,
)

exile_giver_301190 = creature_template(
    EXILE, 'Tinkmaster Fizzbolt', subname='Gnomeregan Exiles', **_GIVER,
)
for _idx, _display in enumerate(_EVACUEE_DISPLAYS):
    creature_model(EXILE, display_id=_display, idx=_idx)
