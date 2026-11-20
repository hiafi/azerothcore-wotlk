"""
The Zealot's set vendors and the Kennel Call hound (scarlet-gear handoff section 1, user ruling 2026-11-19). The
`zealot_set` creature reservation 300890-300899 (source/ids.yaml); 300895-300899 spare.

**Vendors**, one per tier, each trading the Zealot's tokens for the 30 pieces of its tier (source/items/zealot_set.py
`set_vendor(..., tiers=)`, the npc_vendor rows with the token as ExtendedCost). Spawned side by side outside the
Monastery's outer gate in Tirisfal Glades (hand SQL, data/sql/updates/pending_db_world/rev_zealot_set.sql), so the
faction is 35, friendly to both sides. Penitents of the Crusade who sell its relics: names, subnames and looks are
proposals (designer question). Vendor only (npcflag 128), civilian (flags_extra 2), level 60; the columns are the
Molten quartermasters'. Looks: Scarlet Crusade models, one per tier.

    300890 Penitent Aldric    Zealot's Armor - Heroic              Scarlet Chaplain 2501
    300891 Penitent Maren     Zealot's Armor - Molten Empowered    Scarlet Defender 2462
    300892 Penitent Corwin    Zealot's Armor - Draconic Empowered  Scarlet Champion 2460
    300893 Penitent Isolde    Zealot's Armor - Chthonic Empowered  Scarlet Abbot 2492

**300894 Scarlet Tracking Hound**: the Kennel Call look (Houndmaster's Harness 3 piece, zealot_set_bonuses.py
212140). spell_zealot_martyr summons two beside the wearer for the buff's 12 sec; spell_zealot_kennel_call has them
chase the wearer's target and play a bite while the wearer's triggered bite (212142 / 212143) deals the damage, so the
number scales with the wearer (potency). A look the players never target (the Blackrock Depths Lava Spawn's columns):
not selectable, not attackable, friendly to all, no loot, no XP, no melee (DamageModifier 0), passive. Model: the stock
Scarlet Tracking Hound's (4304, display 2709), not a spirit wolf (ruling 59). A look-alike entry, never 4304 itself
(a hostile dungeon add with its own loot).
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

TIER_NAMES = ("Heroic", "Molten Empowered", "Draconic Empowered", "Chthonic Empowered")

# entry: (name, display), in tier order
VENDORS = {
    300890: ("Penitent Aldric", 2501),
    300891: ("Penitent Maren", 2462),
    300892: ("Penitent Corwin", 2460),
    300893: ("Penitent Isolde", 2492),
}

for (_entry, (_name, _display)), _tier_name in zip(VENDORS.items(), TIER_NAMES):
    creature_template(_entry, _name, subname=f"Zealot's Armor - {_tier_name}", **_VENDOR)
    creature_model(_entry, display_id=_display, idx=0)

# The Blackrock Depths look creatures' columns (source/npcs/blackrock_depths/hard_mode_items.py _HELPER): not
# selectable and not attackable (UNIT_FLAG_NON_ATTACKABLE 0x2 | UNIT_FLAG_NOT_SELECTABLE 0x02000000), no loot, no XP
# (flags_extra 0x40), no melee (DamageModifier 0).
_HELPER = dict(
    subname='', IconName='', exp=0, npcflag=0, speed_walk=1.0, speed_run=1.14286, speed_swim=1.0, speed_flight=1.0,
    detection_range=0.0, dmgschool=0, BaseAttackTime=2000, RangeAttackTime=2000, BaseVariance=1.0, RangeVariance=1.0,
    unit_flags=0x2 | 0x02000000, unit_flags2=2048, dynamicflags=0, family=0, type_flags=0, PetSpellDataId=0,
    VehicleId=0, MovementType=0, HoverHeight=1.0, HealthModifier=1.0, ManaModifier=1.0, ArmorModifier=1.0,
    DamageModifier=0.0, ExperienceModifier=1.0, RacialLeader=0, movementId=0, RegenHealth=1, CreatureImmunitiesId=0,
    flags_extra=0x40, AIName='', VerifiedBuild=0, lootid=0, pickpocketloot=0, skinloot=0, mingold=0, maxgold=0,
    faction=35, minlevel=60, maxlevel=60, rank=0, unit_class=1, ScriptName='',
)
_TYPE_BEAST = 1

scarlet_tracking_hound_300894 = creature_template(300894, 'Scarlet Tracking Hound', **{**_HELPER, 'type': _TYPE_BEAST})
creature_model(300894, display_id=2709, idx=0)
