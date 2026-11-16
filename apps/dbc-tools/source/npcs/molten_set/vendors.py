"""
The Molten set vendors (user ruling 2026-11-14, blackrock-gear handoff section 1): Haunted's split, four per armor
type by tier, each trading the Molten tokens for its armor type's archetype pieces of its tiers only
(source/items/molten_set.py `set_vendor(..., tiers=)`, the npc_vendor rows with the token as ExtendedCost). The
`molten_set` creature reservation 300670-300699 (source/ids.yaml); 300686-300699 spare.

    Normal & Heroic                  Molten Empowered      Draconic Empowered    Chthonic Empowered
    cloth    300670 Smelter Brunna    300674 Smelter Hela   300675 Smelter Kirra  300676 Smelter Dagna
    leather  300671 Tanner Grimmald   300677 Tanner Orvik   300678 Tanner Kelda   300679 Tanner Bruk
    mail     300672 Linksmith Durgan  300680 Linksmith Hargun 300681 Linksmith Thrain 300682 Linksmith Gorrin
    plate    300673 Platewright Torvald 300683 Platewright Grumm 300684 Platewright Belgar 300685 Platewright Haldor

Subname "Molten <Armor> - <Tiers>" ("Molten Cloth - Normal & Heroic", "Molten Plate - Chthonic Empowered"). Names and
subnames are proposals (designer question). Not Lokhtos Darkbargainer (user 2026-11-14): Ironforge and Orgrimmar,
each creature spawned in both cities (hand SQL), so the faction is 35, friendly to both. Vendor only (npcflag 128):
a right click opens the list. The columns are Haunted's (Quartermaster Miranda Breechlock's without her gossip, quests
and SmartAI); civilian (flags_extra 2), level 60. Models: the Thorium Brotherhood smiths of Searing Gorge, one per
armor type, the four vendors of an armor type sharing it: Evonice Sootsmoker 14656 (cloth), Hansel Heavyhands 14655
(leather), Overseer Oilfist 14653 (mail), Master Smith Burninate 14652 (plate).
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
    "Cloth": (14656, (300670, "Smelter Brunna"),
              [(300674, "Smelter Hela"), (300675, "Smelter Kirra"), (300676, "Smelter Dagna")]),
    "Leather": (14655, (300671, "Tanner Grimmald"),
                [(300677, "Tanner Orvik"), (300678, "Tanner Kelda"), (300679, "Tanner Bruk")]),
    "Mail": (14653, (300672, "Linksmith Durgan"),
             [(300680, "Linksmith Hargun"), (300681, "Linksmith Thrain"), (300682, "Linksmith Gorrin")]),
    "Plate": (14652, (300673, "Platewright Torvald"),
              [(300683, "Platewright Grumm"), (300684, "Platewright Belgar"), (300685, "Platewright Haldor")]),
}

for _armor, (_display, _first, _empowered) in VENDORS.items():
    for _tier_name, (_entry, _name) in zip(TIER_NAMES, [_first, *_empowered]):
        creature_template(_entry, _name, subname=f'Molten {_armor} - {_tier_name}', **_VENDOR)
        creature_model(_entry, display_id=_display, idx=0)
