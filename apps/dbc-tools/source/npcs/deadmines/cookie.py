"""
Deadmines Pilot WP-B6: Cookie (.agents/plans/deadmines-pilot/deadmines-pilot.HANDOFF.md s3.4 rows CK, s3.5 row B6;
build spec docs/dungeons/deadmines-rework.md "Cookie"). WP-B6 owns this file (its spells: 205320-205339 only).

- 645 Cookie: bound to boss_cookie_rework (SmartAI off; his patrol 793440 is creature_addon data and stays), normal
  11.3k (HealthModifier 23.4), the new stun immunity set. Heroic 330k is deadmines.py's override.

Spells (modules/mod-dungeon-bosses/src/Deadmines/CookieLogic.h `CookieSpells` names the same ids):

  205320  Fire Pepper Chowder   the eater's dish debuff (CK3/CK4), 6 s, names the job; feed visual SV 9721 (Feed)
  205321  Fire Pepper Chowder   breath visual: the eater casts it on itself at every breath (SV 3899, the Dragonbreath
                                Chili breath); no effect
  205322  Fire Pepper Chowder   the registry's resolve copy, Fire (a breath hitting someone; named in the log)
  205323  Pepper Burn           heroic: rider of every breath hit, 30% Fire over 6 s (6 x 5% of reference health, set
                                by spell_dm_cookie_pepper_burn), Magic, refreshes, does not stack
  205324  Week-Old Fish Stew    the eater's dish debuff (CK5), 6 s
  205325  Week-Old Fish Stew    vomit visual: the eater casts it on itself at every drop (SV 9749, Vomit)
  205326  Week-Old Fish Stew    the registry's resolve copy, Nature (a puddle tick)
  205327  Week-Old Fish Stew    puddle ground visual, normal (30 s persistent area, DUMMY, hidden)
  205328  Week-Old Fish Stew    puddle ground visual, heroic (60 s)
  205329  Gut Bomb              the eater's dish debuff (CK6), 5 s (the script cuts it to 4 s on heroic)
  205330  Gut Bomb              the registry's resolve copy, Nature (the belch hitting the others)
  205331  Gut Bomb              the eater's own unavoidable 15% (spell_dm_cookie_gut_bomb_eater)
  205332  Gut Bomb              belch visual: the eater casts it on itself (SV 10241, Gas Nova)
  205333  Cookie's Cooking      CK2 normal: 2 s interruptible self-heal, 5% (HEAL_PCT), SV 147 (stock 5174)
  205334  Cookie's Cooking      CK2 heroic: 8%
  205335  Seasoned              +10% damage done per stack for the fight; the script caps it at 3 (normal) or 10
                                (heroic, ruling 31). Dispel none.
  205336-205339 spare.

Registry damage (Damage(pct) through the resolve copies) and the two script spells (205323, 205331) carry
SPELL_ATTR3_IGNORE_CASTER_MODIFIERS: Seasoned reaches them through the script (pct x (1 + 0.1 x stacks)), never twice.
Stock Acid Splash 6306 (CK1) stays; Seasoned's MOD_DAMAGE_PERCENT_DONE scales it and the melee, and DD scales it on
heroic.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.registry import creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR4_NO_CAST_LOG,
    IMMUNITY_BOSS_STUN,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    TEXT_MASKS,
)

creature_template_columns(
    645, ScriptName='boss_cookie_rework', AIName='', HealthModifier=23.4, CreatureImmunitiesId=IMMUNITY_BOSS_STUN,
)

# The Fish Stew puddle's ground look (handoff s3.10 gap 4, s7 #9): WP-V wires the stock green `goo_flow_state.m2` as a
# new SpellVisual in 90340-90369. Until the orchestrator repoints this constant to that id: the stock no-patch
# fallback, Pungent Slime 52938's SpellVisual 11664 (AcidBurn pool; its cast kit is a vomit breath, which plays on the
# eater, who casts the puddle).
STEW_PUDDLE_SPELLVISUAL = 90342  # WP-V: goo_flow_state green pool, area-aura form (fallback: stock 11664)

_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_DEST_CASTER = 18
_TARGET_SRC_CASTER = 22
_TARGET_UNIT_SRC_AREA_ENEMY = 15
_TARGET_DEST_DYNOBJ_ALLY = 29

_ATTR0_DO_NOT_DISPLAY = 0x00000080
_ATTR0_DO_NOT_LOG = 0x00000100
_ATTR0_NO_ACTIVE_DEFENSE = 0x00200000
_ATTR1_NO_REDIRECTION = 0x00000008
_ATTR1_NO_REFLECTION = 0x00000080
_ATTR1_NO_THREAT = 0x00000400
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_NOT_A_PROC = 0x00000200
_ATTR3_ALWAYS_HIT = 0x00040000
_ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000

_DISPEL_MAGIC = 1
_SCHOOL_ALL = 127

# Stock icons and visuals (DM "Visual sources", Spell.dbc 3.3.5).
_ICON_CHILI = 937           # Dragonbreath Chili 15851
_ICON_FIRE = 37             # Flamestrike 2120
_ICON_SLIME = 2025          # Pungent Slime 52938
_ICON_GAS = 2366            # Gas Nova 45855
_ICON_COOKING = 104         # Cookie's Cooking 5174
_ICON_WELL_FED = 59         # Well Fed (the most common stock Well Fed icon)
_SV_FEED = 9721             # Feed 46694
_SV_CHILI_BREATH = 3899     # Dragonbreath Chili 15851
_SV_VOMIT = 9749            # Vomit 43327
_SV_GAS_NOVA = 10241        # Gas Nova 45855
_SV_COOKING = 147           # Cookie's Cooking 5174

_RESOLVE_EXCLUDED = ('mod-boss-mechanics resolve copy: the damage is set per target by spell_boss_mechanics_resolve '
                     'from the reference-health provider')
_SCRIPT_EXCLUDED = 'Deadmines: a percent of reference health, set by the SpellScript (DeadminesKit::RefFlat)'


def _raw(desc: str = '', aura_desc: str = '', **more) -> dict:
    return {'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': 0, 'CastingTimeIndex': 1,
            'Description_Lang_enUS': desc, 'AuraDescription_Lang_enUS': aura_desc, **TEXT_MASKS, **more}


def _dish_debuff(spell_id: int, name: str, school: School, duration_ms: int, icon: int, text: str, note: str):
    return spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0,
        attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=icon,
        notes=f'Deadmines Pilot WP-B6: {note} Cookie casts it on the eater at the feed (Taste Test, CK3); DUMMY, '
              'AURA_IS_DEBUFF + NO_IMMUNITIES, Dispel none (the dish is the job, not a dispel). Feed visual SV 9721 '
              '(Feed 46694). Aura text number-free (custom-spells.md).',
        raw_overrides=_raw(text + ' Lasts $d.', text, SpellVisualID_1=_SV_FEED, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


def _self_visual(spell_id: int, name: str, school: School, visual: int, icon: int, note: str):
    return spell(
        id=spell_id, name=name, school=school, attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon,
        notes=f'Deadmines Pilot WP-B6: visual only. {note} The eater casts it on itself, triggered; DUMMY with no '
              'handler, DO_NOT_DISPLAY | DO_NOT_LOG. Copies the stock visual, never the stock spell (DM implementation '
              'notes).',
        raw_overrides=_raw(SpellVisualID_1=visual, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


def _resolve_copy(spell_id: int, name: str, school: School, note: str):
    s = spell(
        id=spell_id, name=name, school=school, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
        mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=_TARGET_SRC_CASTER,
                        implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=100.0,
                        potency_excluded=_RESOLVE_EXCLUDED)],
        notes=f'Deadmines Pilot WP-B6: {note} A dungeon copy of the mod-boss-mechanics resolve spell (205001-205007, '
              'source/npcs/boss_mechanics.py) with its exact attribute set, so the combat log names the dish: '
              'bound to spell_boss_mechanics_resolve, which filters the targets to the shape and sets the damage.',
        raw_overrides={
            'Attributes': _ATTR0_NO_ACTIVE_DEFENSE,
            'AttributesEx': _ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION | _ATTR1_NO_THREAT,
            'AttributesEx2': _ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
            'AttributesEx3': _ATTR3_NOT_A_PROC | _ATTR3_ALWAYS_HIT | _ATTR3_IGNORE_CASTER_MODIFIERS,
            'AttributesEx4': ATTR4_NO_CAST_LOG,
            'CastingTimeIndex': 1, 'DefenseType': 1, 'EquippedItemClass': -1, 'SpellClassSet': 0, 'SpellLevel': 0,
        },
    )
    scripted_by(s, 'spell_boss_mechanics_resolve')
    return s


def _puddle_visual(spell_id: int, duration_ms: int, label: str):
    return spell(
        id=spell_id, name='Week-Old Fish Stew', school=School.NATURE,
        attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=duration_ms,
        effects=[Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=0, implicit_target_a=_TARGET_DEST_CASTER,
                        implicit_target_b=_TARGET_DEST_DYNOBJ_ALLY, apply_aura=AuraType.DUMMY, radius_yards=4.0)],
        spell_icon_id=_ICON_SLIME,
        notes=f'Deadmines Pilot WP-B6: visual only, the Fish Stew puddle on the ground ({label}). The eater casts it '
              'at their feet at each drop (TARGET_DEST_CASTER / TARGET_DEST_DYNOBJ_ALLY, the shape of '
              'flourish_ground_200603); its DUMMY aura does nothing (DO_NOT_DISPLAY | DO_NOT_LOG). The registry '
              'zone registered at the same spot owns the damage and the slow. SpellVisual = STEW_PUDDLE_SPELLVISUAL '
              '(stock fallback 11664 until WP-V\'s goo_flow_state visual is wired). boss_cookie_rework removes these '
              'dynamic objects when the encounter ends.',
        raw_overrides=_raw(SpellVisualID_1=STEW_PUDDLE_SPELLVISUAL, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- CK4 Fire Pepper Chowder -----------------------------------------------------------------------------------------
chowder_debuff_205320 = _dish_debuff(
    205320, 'Fire Pepper Chowder', School.FIRE, 6000, _ICON_CHILI,
    'You breathe fire in front of you. Face away from your allies.',
    'the Fire Pepper Chowder dish (CK4): 6 s, three breaths 2 s apart from 2 s after the feed.')

chowder_breath_visual_205321 = _self_visual(
    205321, 'Fire Pepper Chowder', School.FIRE, _SV_CHILI_BREATH, _ICON_CHILI,
    'One fire breath (SV 3899, Dragonbreath Chili 15851), cast at every pass of the chowder cone.')

chowder_breath_205322 = _resolve_copy(
    205322, 'Fire Pepper Chowder', School.FIRE,
    'CK4: a breath, 25% Fire (registry Damage) + Weakened on anyone in the 60 degree / 8 yd cone.')

pepper_burn_205323 = spell(
    id=205323, name='Pepper Burn', school=School.FIRE, dispel=_DISPEL_MAGIC, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=6000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=0, amplitude=1000,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_EXCLUDED)],
    spell_icon_id=_ICON_FIRE,
    notes='Deadmines Pilot WP-B6: CK4 heroic, the chowder burn. Rider of every breath hit (cast by the resolve marker '
          'with Cookie as original caster): 30% Fire over 6 s, 6 ticks; spell_dm_cookie_pepper_burn sets each tick '
          'to RefFlat(Cookie, 5% x Seasoned). Magic (an expected dispel, class tool pass), refreshes, does not stack. '
          'ALWAYS_HIT, NO_REFLECTION, IGNORE_CASTER_MODIFIERS (the registry number, Seasoned applied by the script).',
    raw_overrides=_raw('Burns for 30% of reference health as Fire damage over $d.', 'Burning.',
                       AttributesEx=_ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION,
                       AttributesEx3=_ATTR3_ALWAYS_HIT | _ATTR3_IGNORE_CASTER_MODIFIERS, DefenseType=1),
)
scripted_by(pepper_burn_205323, 'spell_dm_cookie_pepper_burn')

# --- CK5 Week-Old Fish Stew -------------------------------------------------------------------------------------------
stew_debuff_205324 = _dish_debuff(
    205324, 'Week-Old Fish Stew', School.NATURE, 6000, _ICON_SLIME,
    'You drop a puddle under you every few seconds. Walk to the edge of the group.',
    'the Week-Old Fish Stew dish (CK5): 6 s, a puddle under the eater every 2 s from 2 s after the feed.')

stew_vomit_visual_205325 = _self_visual(
    205325, 'Week-Old Fish Stew', School.NATURE, _SV_VOMIT, _ICON_SLIME,
    'The vomit at each puddle drop (SV 9749, Vomit 43327).')

stew_puddle_205326 = _resolve_copy(
    205326, 'Week-Old Fish Stew', School.NATURE,
    'CK5: a puddle tick, 10% (normal) / 15% (heroic) Nature per second + the Standing in It slow, no Weakened.')

stew_puddle_visual_205327 = _puddle_visual(205327, 30000, 'normal, 30 s')
stew_puddle_visual_205328 = _puddle_visual(205328, 60000, 'heroic, 60 s')

# --- CK6 Gut Bomb -----------------------------------------------------------------------------------------------------
gut_bomb_debuff_205329 = _dish_debuff(
    205329, 'Gut Bomb', School.NATURE, 5000, _ICON_GAS,
    'You are about to belch. Run away from your allies.',
    'the Gut Bomb dish (CK6): the belch lands when it runs out (5 s; the script cuts the aura to 4 s on heroic).')

gut_bomb_belch_205330 = _resolve_copy(
    205330, 'Gut Bomb', School.NATURE,
    'CK6: the belch, 30% Nature + Weakened on everyone else within 8 yd of the eater (registry RunOut); heroic '
    'knocks them 6 yd away from the eater (OnHit).')

gut_bomb_eater_205331 = spell(
    id=205331, name='Gut Bomb', school=School.NATURE, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
                    potency_excluded=_SCRIPT_EXCLUDED)],
    spell_icon_id=_ICON_GAS,
    notes='Deadmines Pilot WP-B6: CK6, the eater\'s own belch, 15% Nature, unavoidable (no Weakened, ruling 15). '
          'Cookie casts it on the eater, triggered, at the belch; spell_dm_cookie_gut_bomb_eater sets the damage to '
          'RefFlat(Cookie, 15% x Seasoned). The resolve set\'s attributes (no defense, reflect, threat, LoS, crit; '
          'always hit; IGNORE_CASTER_MODIFIERS so Seasoned lands once, through the script).',
    raw_overrides=_raw('Belches for 15% of reference health as Nature damage.',
                       Attributes=_ATTR0_NO_ACTIVE_DEFENSE,
                       AttributesEx=_ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION | _ATTR1_NO_THREAT,
                       AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
                       AttributesEx3=_ATTR3_NOT_A_PROC | _ATTR3_ALWAYS_HIT | _ATTR3_IGNORE_CASTER_MODIFIERS,
                       AttributesEx4=ATTR4_NO_CAST_LOG, DefenseType=1),
)
scripted_by(gut_bomb_eater_205331, 'spell_dm_cookie_gut_bomb_eater')

gut_bomb_visual_205332 = _self_visual(
    205332, 'Gut Bomb', School.NATURE, _SV_GAS_NOVA, _ICON_GAS,
    'The belch (SV 10241, Gas Nova 45855), at the eater when the Gut Bomb lands.')


# --- CK2 Cookie's Cooking and Seasoned --------------------------------------------------------------------------------
def _cooking(spell_id: int, heal_pct: int, label: str):
    return spell(
        id=spell_id, name="Cookie's Cooking", school=School.HOLY, cast_time_ms=2000, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.HEAL_PCT, base_points=heal_pct - 1, implicit_target_a=TARGET_UNIT_CASTER,
                        potency_excluded="Deadmines: a percent of the boss's own health, not a heal value")],
        spell_icon_id=_ICON_COOKING,
        notes=f'Deadmines Pilot WP-B6: CK2 {label}, a copy of stock 5174 (2 s cast, InterruptFlags 13, PreventionType '
              f'1, SV 147) healing {heal_pct}% of his health (HEAL_PCT, BasePoints {heal_pct - 1} + DieSides 1). On a '
              'completed cast boss_cookie_rework adds a Seasoned stack (cap 3 normal / 10 heroic). On the '
              "descriptor's interrupt list.",
        raw_overrides=_raw('Heals the caster for $s1% of maximum health.', CastingTimeIndex=5, InterruptFlags=13,
                           PreventionType=1, DefenseType=1, SpellPriority=50, SpellVisualID_1=_SV_COOKING),
    )


cookies_cooking_normal_205333 = _cooking(205333, 5, 'normal')
cookies_cooking_heroic_205334 = _cooking(205334, 8, 'heroic')

seasoned_205335 = spell(
    id=205335, name='Seasoned', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=9,
                    misc_value=_SCHOOL_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Seasoned: a flat +10% damage done per stack, not a damage or heal value')],
    spell_icon_id=_ICON_WELL_FED,
    notes="Deadmines Pilot WP-B6: CK2's stacking buff. +10% damage done per stack (BasePoints 9 + DieSides 1; "
          'AuraEffect amounts multiply by the stack count) for the rest of the fight, CumulativeAura 10; the script '
          'stops adding stacks at 3 on normal (Tuning) and 10 on heroic (ruling 31). Scales his melee and Acid Splash '
          'through the aura; his dishes (registry and script damage, IGNORE_CASTER_MODIFIERS) get the same factor '
          'from the script. Not passive (shown), Dispel none (not purgeable: the counter is the interrupt).',
    raw_overrides=_raw('Damage done increased by $s1% per stack, stacking up to $u times.',
                       'Damage done increased by $s1% per stack.', CumulativeAura=10),
)
