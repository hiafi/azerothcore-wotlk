"""
Deadmines Pilot: shared constants for the per-boss declaration files of this package (not loaded on its own: the
leading underscore keeps the package loader from treating it as a declaration file; siblings import it with
`from ._common import ...`). Owned by WP-K (.agents/plans/deadmines-pilot/deadmines-pilot.HANDOFF.md s3.2); a boss
WP asks the orchestrator for a change here.

A boss-kit combat add listed in source/world/dungeons/deadmines.py's `extra=` gets its heroic template in the same run
(lib/dungeon_heroic.py with_declared_templates), and its full creature_template() row must name that heroic entry
itself: `difficulty_entry_1` = its id in source/world/heroic_ids.lock (generate.py --check prints it when missing).
"""

# creature_immunities: the new positive set "-229 + STUN" (mask 0x244B3E53 in the table's comment notation,
# MechanicsMask 1217821862), inserted by core pending SQL (WP-K's rev). Every reworked boss uses it except Rhahk'Zor,
# who keeps -159 (handoff s7 #5).
IMMUNITY_BOSS_STUN = 1972
IMMUNITY_RHAHKZOR = -159

# Text masks and attributes shared by every Deadmines spell declaration.
TEXT_MASKS = {
    'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '',
    'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712190,
}
ATTR0_AURA_IS_DEBUFF = 0x04000000
ATTR0_NO_IMMUNITIES = 0x20000000
ATTR4_NO_CAST_LOG = 0x00000001

TARGET_UNIT_CASTER = 1
TARGET_UNIT_TARGET_ANY = 25

# The boss-kit creature columns every new Deadmines creature shares (the stock Defias rows' values; read-only
# SELECTs 2026-11-06): faction 17 (Defias), unit_flags2 2048, humanoid, exp 0, standing still (MovementType 0: the
# scripts place and move them), no SmartAI.
KIT_CREATURE = dict(
    subname='', IconName='', exp=0, faction=17, npcflag=0, speed_walk=1.0, speed_run=1.14286, speed_swim=1.0,
    speed_flight=1.0, detection_range=20.0, dmgschool=0, BaseAttackTime=2000, RangeAttackTime=2000, BaseVariance=1.0,
    RangeVariance=1.0, unit_flags2=2048, dynamicflags=0, family=0, type=7, type_flags=0, PetSpellDataId=0,
    VehicleId=0, MovementType=0, HoverHeight=1.0, ManaModifier=1.0, ArmorModifier=1.0, ExperienceModifier=1.0,
    RacialLeader=0, movementId=0, RegenHealth=1, CreatureImmunitiesId=0, flags_extra=0, AIName='', VerifiedBuild=0,
)

# Summoned helpers the players never target (iron shot, land mine, shadow image, the powder stalker): not selectable
# and not attackable (UNIT_FLAG_NON_ATTACKABLE 0x2 | UNIT_FLAG_NOT_SELECTABLE 0x02000000, the mod-boss-mechanics marker
# precedent), hostile faction 14, no loot, no XP (flags_extra 0x40), no melee (DamageModifier 0).
KIT_HELPER = dict(
    KIT_CREATURE, faction=14, unit_flags=0x2 | 0x02000000, DamageModifier=0.0, HealthModifier=1.0, lootid=0,
    pickpocketloot=0, skinloot=0, mingold=0, maxgold=0, flags_extra=0x40, detection_range=0.0,
)
