"""
Deadmines Pilot WP-B2: Miner Johnson and the Working Miners (.agents/plans/deadmines-pilot/deadmines-pilot.HANDOFF.md
s3.5; build spec docs/dungeons/deadmines-rework.md "Miner Johnson"). Skeleton from WP-K; WP-B2 owns this file (its
spells: 205230-205239 only; modules/mod-dungeon-bosses MinerJohnsonLogic.h names the same ids).

- 3586 Miner Johnson: bound to boss_miner_johnson_rework (SmartAI off), normal 8.5k (HealthModifier 19), the new
  stun immunity set (handoff s7 #5). Heroic 240k is deadmines.py's override. His 40% spawn roll is the instance's.
- 300422 Working Miner: a copy of 598 at level 18, 1.0k when paid (warrior base 417 x 2.4 = 1,001), heroic 30k.
  Unselectable and passive with emote 233 until paid: WP-B2's script sets those (the template stays plain). Stock
  loot, gold, models copied; WP-B2's SQL deletes stock spawns 79194, 79190, 79191 and 79185.

Spells (MJ ids are the build spec's):

  205230  Pay Pouch          MJ1 the pouch lob: a no-effect missile to a point (stock SpellVisual 10269, Summon
                             Ahune's Loot Missile 45941: the loot-bag missile and its landing burst). Speed 8 yd/s;
                             the script launches it late so it lands as the registry Soak resolves
                             (MinerJohnsonLogic.h LaunchDelay; kPouchSpeed must equal Speed here).
  205231  Payday             MJ1 the gold glint (handoff s7 #13: the blue Soak circle plus SV 737, Summon Treasure
                             Horde Visual 12564): the Working Miner whose pouch is in the air casts it on himself, so
                             the glint marks whose pay it is; the registry's get-in circle marks the spot.
  205232  Pocketed           MJ2 the catcher's buff: damage done +15% for 15 s, refreshed by another catch. The
                             catcher casts it on himself (caster = target, like the registry's Weakened), so a second
                             catch refreshes it. Treasure Sparkle SV 12528 (handoff s7 #9 pick 1a). Not passive.
  205233  Gold Fever         MJ5 heroic, below 30%: melee attack speed +30% for the rest of the fight. SV 47 (Unholy
                             Frenzy 8699: enrage flash, glowing hands that persist; s7 #9 pick 1b). Dispel none (the
                             build spec has no dispel list).
  205234  Gold Fever (tint)  the optional gold tint of pick 1b: a hidden cosmetic DUMMY aura with SV 11903 (AuraYellow).

Pierce Armor stays the stock spells (handoff s7 #3): Johnson's 12097 cut to 10 s by the script, the miners' 6016.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, spell

from ._common import (
    ATTR0_NO_IMMUNITIES,
    ATTR4_NO_CAST_LOG,
    IMMUNITY_BOSS_STUN,
    KIT_CREATURE,
    TARGET_UNIT_CASTER,
    TEXT_MASKS,
)

creature_template_columns(
    3586, ScriptName='boss_miner_johnson_rework', AIName='', HealthModifier=19.0,
    CreatureImmunitiesId=IMMUNITY_BOSS_STUN,
)

working_miner_300422 = creature_template(
    300422, 'Working Miner', **{**KIT_CREATURE, 'minlevel': 18, 'maxlevel': 18, 'rank': 0, 'unit_class': 1,
                                'unit_flags': 0, 'speed_walk': 0.666668, 'HealthModifier': 2.4,
                                'DamageModifier': 1.0, 'lootid': 598, 'pickpocketloot': 598, 'skinloot': 0,
                                'mingold': 8, 'maxgold': 54,
                                'difficulty_entry_1': 310027, 'ScriptName': 'npc_dm_working_miner'},
)
creature_model(300422, display_id=308, idx=0)
creature_model(300422, display_id=2444, idx=1)

_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40
_ATTR0_DO_NOT_DISPLAY = 0x00000080      # hidden aura (no buff icon); its state kit still plays
_ATTR0_DO_NOT_LOG = 0x00000100
_ATTR1_NO_THREAT = 0x00000400
_ATTR2_IGNORE_LOS = 0x00000004
_SCHOOL_ALL = 127

_SV_LOOT_MISSILE = 10269        # Summon Ahune's Loot Missile 45941
_SV_TREASURE_HORDE = 737        # Summon Treasure Horde Visual 12564
_SV_TREASURE_SPARKLE = 12528    # Treasure Sparkle 58042 (sparkle_a.mdx)
_SV_FRENZY = 47                 # Unholy Frenzy 8699 / Frenzy 32964 / Enrage 31915
_SV_AURA_YELLOW = 11903         # AuraYellow.mdx

_ICON_GENERIC = 1
_ICON_TREASURE = 202            # stock Find Treasure 2481
_ICON_FRENZY = 169              # stock Frenzy 32964


def _raw(desc: str, aura_desc: str = '', **more) -> dict:
    return {'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': 0, 'CastingTimeIndex': 1,
            'Description_Lang_enUS': desc, 'AuraDescription_Lang_enUS': aura_desc, **TEXT_MASKS, **more}


pay_pouch_205230 = spell(
    id=205230, name='Pay Pouch', school=School.NORMAL, attributes=_ATTR0_DO_NOT_LOG | ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
    spell_icon_id=_ICON_GENERIC,
    notes='Deadmines Pilot WP-B2, MJ1: the pouch lob, a no-effect missile to the Payday spot (cast at a point by '
          'Miner Johnson, triggered). Stock SpellVisual 10269 (Summon Ahune\'s Loot Missile 45941). Speed 8 yd/s = '
          'MinerJohnsonLogic.h kPouchSpeed: the script launches it so it lands when the Soak resolves.',
    raw_overrides=_raw('Tosses the crew\'s pay.', SpellVisualID_1=_SV_LOOT_MISSILE, Speed=8.0,
                       Targets=_TARGET_FLAG_DEST_LOCATION, AttributesEx=_ATTR1_NO_THREAT,
                       AttributesEx2=_ATTR2_IGNORE_LOS, AttributesEx4=ATTR4_NO_CAST_LOG),
)

payday_glint_205231 = spell(
    id=205231, name='Payday', school=School.NORMAL, attributes=_ATTR0_DO_NOT_LOG | ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_GENERIC,
    notes='Deadmines Pilot WP-B2, MJ1: the gold glint (handoff s7 #13). The Working Miner whose pouch is in the air '
          'casts it on himself (triggered): Summon Treasure Horde Visual 12564\'s SpellVisual 737 (a gold impact at '
          'his feet). The registry Soak draws the blue get-in circle on the spot itself.',
    raw_overrides=_raw('The crew\'s pay is on its way.', SpellVisualID_1=_SV_TREASURE_HORDE,
                       AttributesEx=_ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

pocketed_205232 = spell(
    id=205232, name='Pocketed', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=15000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=14,
                    misc_value=_SCHOOL_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Pocketed: a flat +15% damage done reward buff, not a damage or heal value')],
    spell_icon_id=_ICON_TREASURE,
    notes='Deadmines Pilot WP-B2, MJ2: the Payday catcher\'s reward, damage done +15% (BasePoints 14 + DieSides 1) '
          'for 15 s, all schools; cast by the catcher on himself (triggered), so another catch refreshes it. Not '
          'passive (shown); Treasure Sparkle SV 12528 (handoff s7 #9 pick 1a); stock Find Treasure icon 202.',
    raw_overrides=_raw('Damage done increased. Lasts $d.', 'Damage done increased.',
                       SpellVisualID_1=_SV_TREASURE_SPARKLE),
)

gold_fever_205233 = spell(
    id=205233, name='Gold Fever', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_MELEE_HASTE, base_points=29,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_FRENZY,
    notes='Deadmines Pilot WP-B2, MJ5 (heroic): Miner Johnson below 30% health, melee attack speed +30% '
          '(MOD_MELEE_HASTE 138, BasePoints 29 + DieSides 1) for the rest of the fight (permanent duration; the '
          'reset clears it). SV 47 (handoff s7 #9 pick 1b); Dispel none; stock Frenzy icon 169.',
    raw_overrides=_raw('Attacking faster.', 'Attacking faster.', SpellVisualID_1=_SV_FRENZY),
)

gold_fever_tint_205234 = spell(
    id=205234, name='Gold Fever', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_GENERIC,
    notes='Deadmines Pilot WP-B2, MJ5 (heroic): the gold tint that rides Gold Fever (handoff s7 #9 pick 1b, '
          'optional): a hidden (DO_NOT_DISPLAY) cosmetic DUMMY aura carrying SV 11903 (AuraYellow).',
    raw_overrides=_raw('', SpellVisualID_1=_SV_AURA_YELLOW),
)
