"""
Deadmines Pilot WP-B9: VanCleef's hard mode, Burn It Down (.agents/plans/deadmines-pilot/deadmines-pilot.HANDOFF.md
s3.5, s3.7; build spec docs/dungeons/deadmines-rework.md "Hard mode: Burn It Down", VC10-VC13). WP-B9 owns this file
(its spells: 205380-205389 only; modules/mod-dungeon-bosses HardModeLogic.h `HardModeSpells`).

- 300429 powder blast stalker: an invisible helper for the hard mode's looks (the mod-boss-mechanics stalker display
  11686; a trigger, flags_extra 0x80, so players never see it). Level 60: hard mode is heroic only. No script: the
  hard mode summons it unowned (never in combat) and casts the looks on it.
- The powder keg (gameobject 301000, display 436) and the mainmast (301002, display 90020) are gameobject_template
  rows in core pending SQL (WP-K's rev); the keg's heroic-only spawn is WP-B9's SQL rev.

Spells (every damage number is the registry's: the hits are copies of the mod-boss-mechanics resolve spell):

  205380  Fire Front         VC10 a stripe lands: resolve copy, Fire (30% + 1 Weakened)
  205381  Burning Deck       VC10 / VC11 / VC12 every burn (the deck behind the front, the planks, the mast's wall):
                             resolve copy, Fire (10% per second; rider "Standing in It")
  205382  Powder Blast       VC11 the blast: resolve copy, Fire (40% + 1 Weakened)
  205383  Mainmast           VC12 the fall: resolve copy, Physical (60%, no Weakened)
  205384  Sparking Powder    VC11 the 2 s sparking marker: a hidden aura on the stalker (SV 6944, Shredder Sparks 48457)
  205385  Powder Blast       VC11 the blast look: self (SV 148, Detonation 4043)
  205386  Burning Deck       VC10-VC12 the burning look: a hidden aura on the stalkers (SV 4101, On Fire 36301)
  205387  Mainmast           VC12 the landing look: self (SV 9548, Cosmetic - Cannon Impact 46401)
  205388  Ship Explosion     VC13 the explosion look: self (SV 13122, Big Bang 64443); the kill is the script's
  205389  spare
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.registry import creature_model, creature_template, scripted_by, spell

from ._common import ATTR0_NO_IMMUNITIES, ATTR4_NO_CAST_LOG, KIT_HELPER, TARGET_UNIT_CASTER, TEXT_MASKS

powder_stalker_300429 = creature_template(
    300429, 'Powder Blast Stalker', **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1,
                                       'type': 10, 'flags_extra': 0x40 | 0x80, 'ScriptName': ''},
)
creature_model(300429, display_id=11686)

_TARGET_SRC_CASTER = 22
_TARGET_UNIT_SRC_AREA_ENEMY = 15

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

# The mod-boss-mechanics resolve spell's attribute set (as edwin_vancleef.py's copies), so a copy deals exactly the
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

# Stock looks (DM "Visual sources"; none checked in game yet).
_SV_SPARKS = 6944               # Shredder Sparks 48457 (a state kit: shows while the aura is up)
_SV_DETONATION = 148            # Detonation 4043
_SV_ON_FIRE = 4101              # On Fire 36301 (state kit)
_SV_CANNON_IMPACT = 9548        # Cosmetic - Cannon Impact 46401 (the WP-V report's dust pick for the mast)
_SV_BIG_BANG = 13122            # Big Bang 64443
_ICON_FIRE = 37                 # stock Flamestrike
_ICON_EXPLOSION = 11            # stock Detonation
_ICON_SPARK = 141               # stock Shredder Sparks
_ICON_BIG_BANG = 2176


def _raw(desc: str = '', aura_desc: str = '', **more) -> dict:
    return {'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': 0, 'CastingTimeIndex': 1,
            'Description_Lang_enUS': desc, 'AuraDescription_Lang_enUS': aura_desc, **TEXT_MASKS, **more}


def _resolve_copy(spell_id: int, name: str, school: int, desc: str, icon: int, note: str):
    s = spell(
        id=spell_id, name=name, school=school, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
        mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=_TARGET_SRC_CASTER,
                        implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=100.0,
                        potency_excluded=_RESOLVE_EXCLUDED)],
        spell_icon_id=icon, notes=f'Deadmines Pilot WP-B9: {note}',
        raw_overrides=_raw(desc, **_RESOLVE_RAW, SpellVisualID_1=0),
    )
    scripted_by(s, 'spell_boss_mechanics_resolve')
    return s


def _self_visual(spell_id: int, name: str, visual: int, icon: int, note: str):
    return spell(
        id=spell_id, name=name, school=School.FIRE, attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon,
        notes=f'Deadmines Pilot WP-B9: visual only. {note} The stalker 300429 casts it on itself, triggered; DUMMY '
              'with no handler, DO_NOT_DISPLAY | DO_NOT_LOG. Copies the stock visual, never the stock spell (DM '
              'implementation notes).',
        raw_overrides=_raw(SpellVisualID_1=visual, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


def _state_visual(spell_id: int, name: str, visual: int, icon: int, duration_ms: int, note: str):
    # Not passive: a passive aura is never sent to the client, so its state visual would not show (custom-spells.md).
    return spell(
        id=spell_id, name=name, school=School.FIRE, dispel=0, mechanic=0,
        attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon,
        notes=f'Deadmines Pilot WP-B9: visual only. {note} A hidden DUMMY aura the stalker 300429 puts on itself (not '
              'passive, so the client gets it and plays the state visual). Copies the stock visual, never the stock '
              'spell.',
        raw_overrides=_raw(SpellVisualID_1=visual, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- the hits (registry resolve copies) -------------------------------------------------------------------------------

fire_front_hit_205380 = _resolve_copy(
    205380, 'Fire Front', School.FIRE, 'The deck catches fire.', _ICON_FIRE,
    'VC10 (hard mode): a 2.73 yd stripe across the deck lands. Copy of the mod-boss-mechanics resolve spell (Fire); '
    'the registry sets 30% of the reference row and 1 Weakened.',
)

burning_deck_tick_205381 = _resolve_copy(
    205381, 'Burning Deck', School.FIRE, 'Burning.', _ICON_FIRE,
    'VC10 / VC11 / VC12 (hard mode): every burn, one tick per second: the merged burning deck behind the front, the '
    'planks a powder blast leaves (15 s) and the mainmast\'s wall. Copy of the resolve spell (Fire); the registry '
    'sets 10% of the reference row per tick, rider 205201 Standing in It, no Weakened.',
)

powder_blast_hit_205382 = _resolve_copy(
    205382, 'Powder Blast', School.FIRE, 'A powder keg blows through the planks.', _ICON_EXPLOSION,
    'VC11 (hard mode): the 6 yd blast. Copy of the resolve spell (Fire); the registry sets 40% of the reference row '
    'and 1 Weakened.',
)

mainmast_hit_205383 = _resolve_copy(
    205383, 'Mainmast', School.NORMAL, 'The burning mainmast crashes onto the deck.', _ICON_EXPLOSION,
    'VC12 (hard mode): the 6 yd line where the mast falls, after a 4 s creak. Copy of the resolve spell (Physical); '
    'the registry sets 60% of the reference row, no Weakened (ruling 15: over 50%).',
)

# --- the looks (stalker 300429) --------------------------------------------------------------------------------------

powder_sparks_205384 = _state_visual(
    205384, 'Sparking Powder', _SV_SPARKS, _ICON_SPARK, 3000,
    'VC11: the 2 s sparking marker over a powder keg below deck (stock Shredder Sparks 48457 SV 6944); the script '
    'removes it as the blast goes off.',
)

powder_blast_visual_205385 = _self_visual(
    205385, 'Powder Blast', _SV_DETONATION, _ICON_EXPLOSION,
    'VC11: the blast (stock Detonation 4043 SV 148), as the registry circle resolves.',
)

burning_look_205386 = _state_visual(
    205386, 'Burning Deck', _SV_ON_FIRE, _ICON_FIRE, -1,
    'VC10-VC12: the burning look on each landed stripe, each burning plank and the mast (stock On Fire 36301 SV '
    '4101), until the stalker despawns (3:00, a reset or the kill).',
)

mainmast_crash_205387 = _self_visual(
    205387, 'Mainmast', _SV_CANNON_IMPACT, _ICON_EXPLOSION,
    'VC12: the dust and splinters where the mast lands (stock Cosmetic - Cannon Impact 46401 SV 9548).',
)

ship_explosion_205388 = _self_visual(
    205388, 'Ship Explosion', _SV_BIG_BANG, _ICON_BIG_BANG,
    'VC13: the ship blows at 3:00 (stock Big Bang 64443 SV 13122) at three points along the deck; the script kills '
    'every player on board (no spell damage).',
)
