"""
Deadmines Pilot WP-B8: Edwin VanCleef, the Blackguards and the shadow image
(.agents/plans/deadmines-pilot/deadmines-pilot.HANDOFF.md s3.5; build spec docs/dungeons/deadmines-rework.md "Edwin
VanCleef"). Skeleton from WP-K; WP-B8 owns this file (its spells: 205360-205379 only).

- 639 Edwin VanCleef: bound to boss_edwin_vancleef_rework (SmartAI off), normal 13.6k (HealthModifier 28.1), the
  new stun immunity set. Heroic 340k is deadmines.py's override (hard mode 500k is set by the script).
- 300426 Blackguard: an elite copy of 636 at level 19, 2.4k on normal (449 x 5.35 = 2,402), heroic 40k. Stock
  loot, gold, models and flags copied (no stealth aura on the template: the script summons it in the open).
- 300427 shadow image: VanCleef's display 2029, a summoned helper (not selectable, not attackable, no loot or XP).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR4_NO_CAST_LOG,
    IMMUNITY_BOSS_STUN,
    KIT_CREATURE,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    TEXT_MASKS,
)

creature_template_columns(
    639, ScriptName='boss_edwin_vancleef_rework', AIName='', HealthModifier=28.1,
    CreatureImmunitiesId=IMMUNITY_BOSS_STUN,
)

blackguard_300426 = creature_template(
    300426, 'Defias Blackguard', **{**KIT_CREATURE, 'minlevel': 19, 'maxlevel': 19, 'rank': 1, 'unit_class': 1,
                                    'unit_flags': 64, 'HealthModifier': 5.35, 'DamageModifier': 1.7,
                                    'ExperienceModifier': 1.25, 'lootid': 636, 'pickpocketloot': 636,
                                    'skinloot': 0, 'mingold': 27, 'maxgold': 191,
                                    'difficulty_entry_1': 310028, 'ScriptName': 'npc_dm_blackguard'},
)
creature_model(300426, display_id=2314, idx=0)
creature_model(300426, display_id=2315, idx=1)

shadow_image_300427 = creature_template(
    300427, 'Shadow of VanCleef', **{**KIT_HELPER, 'minlevel': 20, 'maxlevel': 20, 'rank': 0, 'unit_class': 1,
                                     'ScriptName': 'npc_dm_shadow_image'},
)
creature_model(300427, display_id=2029)

# --- spells (205360-205379; modules/mod-dungeon-bosses VanCleefLogic.h `VanCleefSpells`) ------------------------------
#
#   205360  Ambush from the Rigging  VC1 vanish look: self, no effect (SV 255, Vanish 1856); he casts it as he vanishes
#   205361  Ambush from the Rigging  VC1 / VC2 circle hit: resolve copy, Physical (the registry's 40% + Weakened)
#   205362  Shadow of VanCleef       VC2 the image's look: self, no effect (SV 8262, Vanish 55964)
#   205363  Fire Bomb                VC7 burning patch tick (heroic): resolve copy, Fire (the registry's 5% per second)
#   205364  Fire Bomb                VC7 burning patch look: a 15 s persistent area aura at the dead Blackguard's feet
#                                    (SV 9603, Fire Bomb 42629), DUMMY, cast triggered from the corpse
#   205365  Expose Armor             VC9 (heroic): -6% armor per stack, 5 stacks, 20 s, on his victim per Thrash proc
#                                    (SV 3441 and icon 563 of stock Expose Armor 8647)
#   205366  Ambush                   VC1 / VC2 landing look: self, no effect (SV 155, Ambush 8676)
#
# The guns (VC3) reuse Greenskin's lane spells and cast bars (205340-205344, captain_greenskin.py). Stock spells kept:
# Dual Wield 674, Thrash 3417 / 3391 (creature_template_addon), Cheap Shot 1833 (stun cut to 2 s by the script),
# Rupture 14903; VanCleef's Allies 5200 is replaced by the script's summon of 300426.

_TARGET_DEST_CASTER = 18
_TARGET_SRC_CASTER = 22
_TARGET_UNIT_SRC_AREA_ENEMY = 15
_TARGET_DEST_DYNOBJ_ALLY = 29

_ATTR0_DO_NOT_DISPLAY = 0x00000080
_ATTR0_DO_NOT_LOG = 0x00000100
_ATTR0_NO_ACTIVE_DEFENSE = 0x00200000
_ATTR0_ALLOW_CAST_WHILE_DEAD = 0x00800000
_ATTR1_NO_REDIRECTION = 0x00000008
_ATTR1_NO_REFLECTION = 0x00000080
_ATTR1_NO_THREAT = 0x00000400
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_NOT_A_PROC = 0x00000200
_ATTR3_ALWAYS_HIT = 0x00040000
_ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000

# The mod-boss-mechanics resolve spell's attribute set (as captain_greenskin.py's copies), so a copy deals exactly the
# registry's number (IGNORE_CASTER_MODIFIERS: STAGE-X-REPORT).
_RESOLVE_RAW = {
    'Attributes': _ATTR0_NO_ACTIVE_DEFENSE,
    'AttributesEx': _ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION | _ATTR1_NO_THREAT,
    'AttributesEx2': _ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
    'AttributesEx3': _ATTR3_NOT_A_PROC | _ATTR3_ALWAYS_HIT | _ATTR3_IGNORE_CASTER_MODIFIERS,
    'AttributesEx4': ATTR4_NO_CAST_LOG,
    'CastingTimeIndex': 1,
    'DefenseType': 1,
}
_RESOLVE_EXCLUDED = ('mod-boss-mechanics resolve copy: the damage is set per target by spell_boss_mechanics_resolve '
                     'from the reference-health provider')

_MOD_ARMOR = 1                  # SPELL_SCHOOL_MASK_NORMAL: MOD_RESISTANCE_PCT on armor
_MECHANIC_NONE = 0

# Stock looks (DM "Visual sources"; none checked in game yet).
_SV_VANISH = 255                # Vanish 1856
_SV_AMBUSH = 155                # Ambush 8676
_SV_SHADOW_IMAGE = 8262         # Vanish 55964
_SV_FIRE_BOMB_PATCH = 9603      # Fire Bomb 42629 (the burning patch)
_SV_EXPOSE_ARMOR = 3441         # Expose Armor 8647
_ICON_VANISH = 252
_ICON_AMBUSH = 856
_ICON_SHADOW_IMAGE = 250
_ICON_FIRE_BOMB = 2128
_ICON_EXPOSE_ARMOR = 563


def _raw(desc: str = '', aura_desc: str = '', **more) -> dict:
    return {'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': 0, 'CastingTimeIndex': 1,
            'Description_Lang_enUS': desc, 'AuraDescription_Lang_enUS': aura_desc, **TEXT_MASKS, **more}


def _resolve_copy(spell_id: int, name: str, school: int, desc: str, icon: int, visual: int, note: str):
    s = spell(
        id=spell_id, name=name, school=school, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
        mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=_TARGET_SRC_CASTER,
                        implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=100.0,
                        potency_excluded=_RESOLVE_EXCLUDED)],
        spell_icon_id=icon, notes=note,
        raw_overrides=_raw(desc, **_RESOLVE_RAW, SpellVisualID_1=visual),
    )
    scripted_by(s, 'spell_boss_mechanics_resolve')
    return s


def _self_visual(spell_id: int, name: str, visual: int, icon: int, note: str):
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon,
        notes=f'Deadmines Pilot WP-B8: visual only. {note} Cast on the caster itself, triggered; DUMMY with no '
              'handler, DO_NOT_DISPLAY | DO_NOT_LOG. Copies the stock visual, never the stock spell (DM implementation '
              'notes).',
        raw_overrides=_raw(SpellVisualID_1=visual, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- VC1 / VC2 Ambush from the Rigging -------------------------------------------------------------------------------

ambush_vanish_205360 = _self_visual(
    205360, 'Ambush from the Rigging', _SV_VANISH, _ICON_VANISH,
    'VC1: VanCleef vanishes into the rigging (stock Vanish 1856 SV 255); the script then hides him for the 2 s.',
)

ambush_hit_205361 = _resolve_copy(
    205361, 'Ambush from the Rigging', School.NORMAL, 'VanCleef drops out of the rigging.', _ICON_AMBUSH, _SV_AMBUSH,
    'Deadmines Pilot WP-B8 VC1 / VC2: the 5 yd circle hit (VanCleef and his shadow image). Copy of the '
    'mod-boss-mechanics resolve spell 205001 (Physical); the registry sets 40% of the reference row and 1 Weakened. '
    'SV 155 (Ambush 8676).',
)

shadow_image_visual_205362 = _self_visual(
    205362, 'Shadow of VanCleef', _SV_SHADOW_IMAGE, _ICON_SHADOW_IMAGE,
    'VC2: the shadow image (300427) shows it as it lands (stock Vanish 55964 SV 8262).',
)

ambush_strike_205366 = _self_visual(
    205366, 'Ambush', _SV_AMBUSH, _ICON_AMBUSH,
    'VC1 / VC2: the landing strike, cast by VanCleef and by his image as they drop (stock Ambush 8676 SV 155).',
)

# --- VC7 Fire Bomb (heroic) ------------------------------------------------------------------------------------------

fire_bomb_tick_205363 = _resolve_copy(
    205363, 'Fire Bomb', School.FIRE, 'Burning.', _ICON_FIRE_BOMB, 0,
    'Deadmines Pilot WP-B8 VC7 (heroic): the burning patch tick where a Blackguard died. Copy of the resolve spell, '
    'Fire; the registry sets 5% of the reference row per second for 15 s (no slow, no Weakened).',
)

fire_bomb_ground_205364 = spell(
    id=205364, name='Fire Bomb', school=School.FIRE,
    attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG | _ATTR0_ALLOW_CAST_WHILE_DEAD, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=15000,
    effects=[Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=0, implicit_target_a=_TARGET_DEST_CASTER,
                    implicit_target_b=_TARGET_DEST_DYNOBJ_ALLY, apply_aura=AuraType.DUMMY, radius_yards=6.0)],
    spell_icon_id=_ICON_FIRE_BOMB,
    notes='Deadmines Pilot WP-B8 VC7 (heroic): visual only, the burning patch on the ground. The dying Blackguard '
          'casts it at its feet, triggered (ALLOW_CAST_WHILE_DEAD too); TARGET_DEST_CASTER / TARGET_DEST_DYNOBJ_ALLY '
          '(the shape of cookie.py\'s stew puddle), 15 s, 6 yd; its DUMMY aura does nothing. The registry patch at the '
          'same spot owns the damage. SV 9603 (Fire Bomb 42629), unchecked in game.',
    raw_overrides=_raw(SpellVisualID_1=_SV_FIRE_BOMB_PATCH, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- VC9 Expose Armor (heroic) ---------------------------------------------------------------------------------------

expose_armor_205365 = spell(
    id=205365, name='Expose Armor', school=School.NORMAL, dispel=0, mechanic=_MECHANIC_NONE,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=20000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_RESISTANCE_PCT, base_points=-7,
                    misc_value=_MOD_ARMOR, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_EXPOSE_ARMOR,
    notes='Deadmines Pilot WP-B8 VC9 (heroic): VanCleef puts a stack on his victim at every Thrash proc (3391). Armor '
          '-6% per stack (MOD_RESISTANCE_PCT on armor, BasePoints -7 + DieSides 1; AuraEffect amounts multiply by the '
          'stack count), CumulativeAura 5, 20 s refreshed by every stack. AURA_IS_DEBUFF, Dispel none (DM: no '
          'dispel list). SV 3441 and icon 563 of stock Expose Armor 8647 (never cast: a player spell).',
    raw_overrides=_raw('Armor reduced by $s1% per stack, stacking up to $u times. Lasts $d.', 'Armor reduced.',
                       CumulativeAura=5, SpellVisualID_1=_SV_EXPOSE_ARMOR, AttributesEx4=ATTR4_NO_CAST_LOG),
)
