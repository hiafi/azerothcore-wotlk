"""
Deadmines Pilot WP-B7: Captain Greenskin (.agents/plans/deadmines-pilot/deadmines-pilot.HANDOFF.md s3.5; build spec
docs/dungeons/deadmines-rework.md "Captain Greenskin"). WP-B7 owns this file (its spells: 205340-205359 only).

- 647 Captain Greenskin: bound to boss_captain_greenskin_rework (SmartAI off; since playtest 1 he stands still:
  the core pending SQL clears spawn 79333's patrol 793330, his two formation followers stay), normal 14.2k
  (HealthModifier 29.2), the new stun immunity set. Heroic 377k is deadmines.py's override. The harpoon rope is
  gameobject 301001 (core pending SQL, WP-K's rev; script go_dm_harpoon_rope).
- 300425 Harpoon Rope: the invisible unit the rope beam is channeled from (it follows Greenskin while a rope is out;
  the handoff's "harpoon rope unit" slot). The mod-boss-mechanics stalker display 11686 WITHOUT the trigger bit
  (0x80 hides a unit from non-GMs, and a hidden unit draws no beam), like the registry's markers. Not selectable,
  not attackable, no loot or XP (KIT_HELPER). Summoned on both difficulties from the normal entry (no heroic row: a
  helper, not a combat add).

Spells (modules/mod-dungeon-bosses GreenskinLogic.h `GreenskinSpells`):

  205340  Fire on My Mark   GS2 lane hit, rail to rail. A copy of the mod-boss-mechanics resolve spell (Physical; same
                            attributes, effect and radius as 205001), bound to spell_boss_mechanics_resolve plus
                            spell_dm_greenskin_lane_hit (a player at a crossing is hit once per volley, ruling 15).
                            The registry sets the damage per target (40% of the reference row). Shared with
                            VanCleef's guns (VC3).
  205341  Crossfire         GS3 lane hit, bow to stern (heroic): as 205340.
  205342  Burning Deck      GS4 crossing tick (heroic): resolve copy, Fire, spell_boss_mechanics_resolve only.
  205343  Fire on My Mark   GS2 cast bar: 2 s, no effect, not interruptible (the 205200 shape, named).
  205344  Crossfire         GS2 + GS3 heroic cast bar: 2.5 s, as 205343.
  205345  Reel 'Em In       GS5 cast: 2 s, 40 yd (stock Poisoned Harpoon 5208 has 10 yd; the build spec's target is
                            "at least 10 yd away"), interruptible (stock 5208's InterruptFlags 15 and silence
                            prevention), stock 5208's visual 731 and icon 247; a DUMMY on the target (no weapon hit:
                            lint S3). ALWAYS_HIT: the rope is the mechanic, not a hit roll. The script puts stock
                            5208's poison on each target (Unit::AddAura, the stock id: DD scales it).
  205346  Harpooned         GS5 rope: channeled by 300425 at the target; the beam is stock Rope Beam 43368's visual
                            9759. ALLOW_ACTION_DURING_CHANNEL so the anchor can follow him. The target's debuff, aura
                            text "Harpooned. Get away to snap the rope." (DM "Debuff and buff text", approved).
  205347  Reel 'Em In       GS5 reel: resolve copy, Physical: the RunOut's 30% (and Weakened) when he reels a target in.
  205348  Grappling Hook    playtest 1: the grip that keeps the fight on the ship. Greenskin casts it (triggered) on a
                            unit he pulls onto the deck (at the pull, or after 1.5 s off the ship); the script does
                            the jump. DUMMY on the target, no damage; stock Death Grip 49576's SpellVisual 10906 (the
                            grip anim, the chain and the ghoul-hand impact), icon 2723.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR4_NO_CAST_LOG,
    IMMUNITY_BOSS_STUN,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    TEXT_MASKS,
)

creature_template_columns(
    647, ScriptName='boss_captain_greenskin_rework', AIName='', HealthModifier=29.2,
    CreatureImmunitiesId=IMMUNITY_BOSS_STUN,
)

rope_anchor_300425 = creature_template(
    300425, 'Harpoon Rope', **{**KIT_HELPER, 'minlevel': 20, 'maxlevel': 20, 'rank': 0, 'unit_class': 1, 'type': 10,
                               'ScriptName': ''},
)
creature_model(300425, display_id=11686)

# --- shared bits -----------------------------------------------------------------------------------------------------

_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_SRC_CASTER = 22
_TARGET_UNIT_SRC_AREA_ENEMY = 15

# The mod-boss-mechanics resolve spell's attribute set (source/npcs/boss_mechanics.py, 205001-205007), so a copy deals
# exactly the registry's number: no active defense, no redirection or reflection, no threat, ignores LoS, cannot crit,
# not a proc, always hits, ignores caster modifiers (STAGE-X-REPORT), DmgClass magic, instant.
_ATTR0_IS_ABILITY = 0x00000010
_ATTR0_NO_ACTIVE_DEFENSE = 0x00200000
_ATTR0_DO_NOT_SHEATH = 0x00040000
_ATTR1_IS_CHANNELED = 0x00000004
_ATTR1_NO_REDIRECTION = 0x00000008
_ATTR1_NO_REFLECTION = 0x00000080
_ATTR1_NO_THREAT = 0x00000400
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_NOT_A_PROC = 0x00000200
_ATTR3_SUPPRESS_CASTER_PROCS = 0x00010000
_ATTR3_SUPPRESS_TARGET_PROCS = 0x00020000
_ATTR3_ALWAYS_HIT = 0x00040000
_ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
_ATTR5_ALLOW_ACTION_DURING_CHANNEL = 0x00000001

_RESOLVE_RAW = {
    'Attributes': _ATTR0_NO_ACTIVE_DEFENSE,
    'AttributesEx': _ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION | _ATTR1_NO_THREAT,
    'AttributesEx2': _ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
    'AttributesEx3': _ATTR3_NOT_A_PROC | _ATTR3_ALWAYS_HIT | _ATTR3_IGNORE_CASTER_MODIFIERS,
    'AttributesEx4': ATTR4_NO_CAST_LOG,
    'CastingTimeIndex': 1,
    'DefenseType': 1,
}

# Stock look sources (DM "Visual sources"; none checked in game yet).
_VISUAL_CANNON_FIRE = 612       # Southsea Cannon Fire 6252: the gun fires from the lane's rail end (resolve caster)
_VISUAL_ON_FIRE = 4101          # On Fire 36301
_VISUAL_POISONED_HARPOON = 731  # stock Poisoned Harpoon 5208
_VISUAL_ROPE_BEAM = 9759        # stock Rope Beam 43368
_ICON_CANNON_BALL = 965         # stock Cannon Ball 4170
_ICON_FIRE = 37                 # stock Flamestrike 2120
_ICON_HARPOON = 247             # stock Poisoned Harpoon 5208

_RESOLVE_NOTE = ('the damage is set per target by the resolve SpellScript (OnEffectLaunchTarget SetEffectValue) from '
                 'the reference-health provider')


def _raw(desc: str, aura_desc: str = '', **more) -> dict:
    return {'SpellClassSet': 0, 'EquippedItemClass': -1, 'SpellLevel': 0, 'Description_Lang_enUS': desc,
            'AuraDescription_Lang_enUS': aura_desc, **TEXT_MASKS, **more}


def _resolve_copy(spell_id: int, name: str, school: int, desc: str, icon: int, visual: int, note: str, *scripts):
    s = spell(
        id=spell_id, name=name, school=school, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
        mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=_TARGET_SRC_CASTER,
                        implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=100.0,
                        potency_excluded=_RESOLVE_NOTE)],
        spell_icon_id=icon, notes=note,
        raw_overrides=_raw(desc, **_RESOLVE_RAW, SpellVisualID_1=visual),
    )
    scripted_by(s, 'spell_boss_mechanics_resolve', *scripts)
    return s


def _cast_bar(spell_id: int, name: str, cast_ms: int, desc: str, note: str):
    return spell(
        id=spell_id, name=name, school=School.NORMAL, cast_time_ms=cast_ms, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_CANNON_BALL, notes=note,
        raw_overrides=_raw(desc, InterruptFlags=0, PreventionType=0, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- GS2-GS4: the lanes ----------------------------------------------------------------------------------------------

fire_on_my_mark_hit_205340 = _resolve_copy(
    205340, 'Fire on My Mark', School.NORMAL, "The ship's guns fire across the deck.", _ICON_CANNON_BALL,
    _VISUAL_CANNON_FIRE,
    'Deadmines Pilot WP-B7 GS2: the rail-to-rail lane hit (also VanCleef VC3). Copy of the mod-boss-mechanics resolve '
    'spell 205001 (Physical), plus spell_dm_greenskin_lane_hit (once per player per volley). Visual 612 (Southsea '
    'Cannon Fire 6252), unchecked in game.',
    'spell_dm_greenskin_lane_hit',
)

crossfire_hit_205341 = _resolve_copy(
    205341, 'Crossfire', School.NORMAL, "The ship's guns fire along the deck.", _ICON_CANNON_BALL,
    _VISUAL_CANNON_FIRE,
    'Deadmines Pilot WP-B7 GS3 (heroic): the bow-to-stern lane hit (also VanCleef VC3 heroic). As 205340.',
    'spell_dm_greenskin_lane_hit',
)

burning_deck_205342 = _resolve_copy(
    205342, 'Burning Deck', School.FIRE, 'The deck burns where the shots crossed.', _ICON_FIRE, _VISUAL_ON_FIRE,
    'Deadmines Pilot WP-B7 GS4 (heroic): the burning crossing tick (10% Fire per second, 20 s; rider 205201). Copy of '
    'the resolve spell, Fire. Visual 4101 (On Fire 36301), unchecked in game.',
)

fire_on_my_mark_cast_205343 = _cast_bar(
    205343, 'Fire on My Mark', 2000, 'Calls the guns.',
    'Deadmines Pilot WP-B7 GS2: the 2 s cast bar of the volley (the registry lanes land the hit). DUMMY on the '
    'caster; not interruptible (InterruptFlags 0, PreventionType 0), like 205200.',
)

crossfire_cast_205344 = _cast_bar(
    205344, 'Crossfire', 2500, 'Calls the guns on both sides.',
    'Deadmines Pilot WP-B7 GS2 + GS3 (heroic): the 2.5 s cast bar of the crossfire volley. As 205343.',
)

# --- GS5: Reel 'Em In ------------------------------------------------------------------------------------------------

reel_em_in_205345 = spell(
    id=205345, name="Reel 'Em In", school=School.NATURE, cast_time_ms=2000, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=40.0, duration_ms=0,
    attributes=_ATTR0_IS_ABILITY | _ATTR0_DO_NOT_SHEATH,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_HARPOON,
    notes="Deadmines Pilot WP-B7 GS5: Greenskin's harpoon throw. Stock Poisoned Harpoon 5208's cast (2 s, "
          'interruptible: InterruptFlags 15, PreventionType silence, DefenseType magic) at 40 yd: the target is a '
          "random non-tank at least 10 yd away. DUMMY on the target (stock 5208's weapon-damage hit is not kept: a "
          'custom WEAPON_DAMAGE effect needs a potency weapon percent, lint S3). ALWAYS_HIT. On the hit the script '
          "adds the stock poison (5208's aura, so DD scales it on heroic) and the rope.",
    raw_overrides=_raw('Harpoons an enemy, poisoning it and roping it to the captain.',
                       InterruptFlags=15, PreventionType=1, DefenseType=1, AttributesEx3=_ATTR3_ALWAYS_HIT,
                       SpellVisualID_1=_VISUAL_POISONED_HARPOON),
)

harpooned_205346 = spell(
    id=205346, name='Harpooned', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=6000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_HARPOON,
    notes='Deadmines Pilot WP-B7 GS5: the rope. Channeled by the rope anchor 300425 at the harpooned player; the '
          'channel draws the beam (stock Rope Beam 43368 visual 9759) and the aura is the target\'s debuff. '
          'IS_CHANNELED + NO_THREAT, ignores LoS, suppresses procs, always hits (a level 20 anchor on a level 60 '
          'player must not miss), ALLOW_ACTION_DURING_CHANNEL (the anchor follows '
          'Greenskin while it channels); no interrupt flags. The script ends it when the rope snaps, is cut, or reels.',
    raw_overrides=_raw('Roped to Captain Greenskin. Get away to snap the rope.',
                       'Harpooned. Get away to snap the rope.', CastingTimeIndex=1, InterruptFlags=0,
                       AuraInterruptFlags=0, ChannelInterruptFlags=0,
                       AttributesEx=_ATTR1_IS_CHANNELED | _ATTR1_NO_THREAT,
                       AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT,
                       AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS | _ATTR3_SUPPRESS_TARGET_PROCS
                       | _ATTR3_ALWAYS_HIT,
                       AttributesEx5=_ATTR5_ALLOW_ACTION_DURING_CHANNEL,
                       SpellVisualID_1=_VISUAL_ROPE_BEAM),
)

reel_hit_205347 = _resolve_copy(
    205347, "Reel 'Em In", School.NORMAL, 'Reeled in.', _ICON_HARPOON, 0,
    'Deadmines Pilot WP-B7 GS5: the reel. The RunOut (25 yd, measured from Greenskin) resolves with this copy of the '
    'resolve spell (Physical): 30% of the reference row and 1 Weakened on a target still within 25 yd after 4 s; the '
    "script's OnHit then pulls the target to his feet.",
)

# --- Playtest 1: the grip back onto the deck --------------------------------------------------------------------------
_VISUAL_DEATH_GRIP = 10906      # stock Death Grip 49576 / 57602
_ICON_DEATH_GRIP = 2723

grappling_hook_205348 = spell(
    id=205348, name='Grappling Hook', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_DEATH_GRIP,
    notes='Deadmines Pilot playtest 1: Greenskin keeps the fight on his ship. He casts this (triggered) on everyone in '
          'combat with him who is off the ship at the pull, and on anyone off it for 1.5 s during the fight (players, '
          'bots, pets); the script then jumps the unit onto the open stern deck near him (MoveJump, as the reel). '
          'DUMMY on the target, no damage, no threat; ignores LoS, always hits, suppresses procs. Stock Death Grip '
          '49576\'s SpellVisual 10906 and icon 2723 (the grip look the playtest asked for).',
    raw_overrides=_raw('Hooks an enemy and hauls it back aboard.', CastingTimeIndex=1, InterruptFlags=0,
                       PreventionType=0, AttributesEx=_ATTR1_NO_THREAT,
                       AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT,
                       AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS | _ATTR3_SUPPRESS_TARGET_PROCS
                       | _ATTR3_ALWAYS_HIT,
                       AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=_VISUAL_DEATH_GRIP),
)
