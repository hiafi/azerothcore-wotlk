"""
The Haunted set vendors (user rulings 2026-11-06): four per armor type, split by tier, each trading the Haunted tokens
for its armor type's archetype pieces of its tiers only (source/items/haunted_set.py `set_vendor(..., tiers=)`, the
npc_vendor rows with the token as ExtendedCost). The `haunted_set` creature reservation 300480-300499
(source/ids.yaml); 300496-300499 spare.

    Normal & Heroic (the user's spots)   Molten Empowered     Draconic Empowered    Chthonic Empowered
    cloth    300480 Dawnwatcher Ilyssa    300484 Thessa        300485 Lirael         300486 Vaena
    leather  300481 Dawnwatcher Faelan    300487 Aldren        300488 Taerith        300489 Kaelith
    mail     300482 Quartermaster Brannoc 300490 Garreth       300491 Dunstan        300492 Merrow
    plate    300483 Quartermaster Hollis  300493 Corwin        300494 Baylor         300495 Edric

Subname "Haunted <Armor> - <Tiers>" ("Haunted Cloth - Normal & Heroic", "Haunted Cloth - Molten Empowered", ...).
Names and subnames are proposals (designer question). Spawned in Darnassus for the Alliance by hand SQL (the creature
table, guids from the hand-SQL block above 5300000), the three empowered vendors of an armor type in a tight cluster
next to its "Normal & Heroic" vendor; a Horde spot later is a new spawn of the same entries, so the faction is 35,
friendly to everyone. Vendor only (npcflag 128): a right click opens the list. The columns are Quartermaster Miranda
Breechlock's (11536, the Argent Dawn quartermaster the design first named), without her gossip, quests and SmartAI;
civilian (flags_extra 2), level 60. Models: an armor type's four vendors share one look: the Argent Dawn's Darnassus
watchers (Dawnwatcher Shaedlass 4786 and Selgorm 4783) for cloth and leather, Argent Quartermaster Lightspark (10857)
and Argent Officer Pureheart (10840) for mail and plate.
"""

from lib.dsl.registry import creature_model, creature_template

_VENDOR = dict(
    IconName='', exp=0, faction=35, npcflag=128, minlevel=60, maxlevel=60, rank=0, unit_class=1, speed_walk=1.0,
    speed_run=1.14286, speed_swim=1.0, speed_flight=1.0, detection_range=18.0, dmgschool=0, DamageModifier=1.0,
    BaseAttackTime=2000, RangeAttackTime=2000, BaseVariance=1.0, RangeVariance=1.0, unit_flags=0, unit_flags2=2048,
    dynamicflags=0, family=0, type=7, type_flags=0, lootid=0, pickpocketloot=0, skinloot=0, PetSpellDataId=0,
    VehicleId=0, mingold=0, maxgold=0, AIName='', MovementType=0, HoverHeight=1.0, HealthModifier=1.35,
    ManaModifier=1.0, ArmorModifier=1.0, ExperienceModifier=1.0, RacialLeader=0, movementId=0, RegenHealth=1,
    CreatureImmunitiesId=0, flags_extra=2, ScriptName='', VerifiedBuild=0, gossip_menu_id=0,
)

TIER_NAMES = ("Normal & Heroic", "Molten Empowered", "Draconic Empowered", "Chthonic Empowered")

# armor type: (look, (Normal & Heroic entry, name), [(empowered entry, name) x 3 in tier order])
VENDORS = {
    "Cloth": (5225, (300480, "Dawnwatcher Ilyssa"),
              [(300484, "Dawnwatcher Thessa"), (300485, "Dawnwatcher Lirael"), (300486, "Dawnwatcher Vaena")]),
    "Leather": (5226, (300481, "Dawnwatcher Faelan"),
                [(300487, "Dawnwatcher Aldren"), (300488, "Dawnwatcher Taerith"), (300489, "Dawnwatcher Kaelith")]),
    "Mail": (10213, (300482, "Quartermaster Brannoc"),
             [(300490, "Quartermaster Garreth"), (300491, "Quartermaster Dunstan"), (300492, "Quartermaster Merrow")]),
    "Plate": (10211, (300483, "Quartermaster Hollis"),
              [(300493, "Quartermaster Corwin"), (300494, "Quartermaster Baylor"), (300495, "Quartermaster Edric")]),
}

for _armor, (_display, _first, _empowered) in VENDORS.items():
    for _tier_name, (_entry, _name) in zip(TIER_NAMES, [_first, *_empowered]):
        creature_template(_entry, _name, subname=f'Haunted {_armor} - {_tier_name}', **_VENDOR)
        creature_model(_entry, display_id=_display, idx=0)
