"""
Gnomeregan build WP-D5: Crowd Pummeler 9-60 (6229) in the glass window, normal and heroic
(.agents/plans/gnomeregan-build/gnomeregan-build.HANDOFF.md s3.5 row D5 and rule 33, s3.6, s3.8, s3.9 row 7, s7 #27 A,
#28 A, #29 A, s10 the window ruling; build spec docs/dungeons/gnomeregan-rework.md SP 1226-1437 (CP1-CP8, Build spec
1388)). WP-D5 owns this file (its spells: kSpellsPummeler 214460-214489 of modules/mod-dungeon-bosses
src/Gnomeregan/GnomereganRework.h only; CrowdPummelerLogic.h names the same ids). The engine side is
src/Gnomeregan/boss_crowd_pummeler_rework.cpp and the ComboMachine (CrowdPummelerMachine.{h,cpp}); the texts and the
chest's gameobject templates (301380 normal, 301381 heroic: the instance places the chest at his DONE) are
data/sql/updates/pending_db_world/rev_crowd_pummeler_gnomeregan.sql. Heroic health and its overrides are WP-H's
(source/world/dungeons/gnomeregan.py); his loot is L-1's (s7 #42 A: his body carries nothing, the chest does).

- 6229 Crowd Pummeler 9-60: boss_crowd_pummeler_rework (SmartAI off: rev_skeleton_gnomeregan.sql drops his rows),
  normal health 60,001 = 70.34 on the level 28 warrior base 853 (spec 30,000 x2.0, s7 #1 A), stock DamageModifier 1.7,
  immunity 1972, INSTANCE_BIND with both assist flags, detection 12 (WP-S0's boss_columns). His model row: display 6774
  at DisplayScale 5 (the window ruling; the heroic copy inherits the row, lib/dungeon_heroic.py side tables). Display
  6774 is worn by four creatures (6229, 21426, 25752, 25766): its creature_model_info is never edited; the script sets
  his combat reach and bounding radius (10, s7 #27 A). The movement row (Flight 1, Rooted 1) is the S0 rev's.
- 301115 the frame stalker: npc_gnomer_pummeler_frame (inert), KIT_HELPER (not selectable, not attackable, no XP), the
  invisible stalker 11686 (stock creature_model_info row), summoned at the frame origin (-887.0, 364.2) for the pull:
  Trample's ring plays on it (he floats 4.8 yd under the floor, so a ring at his own feet would be under it). No heroic
  template (a helper).

Spells (every punch is a dungeon copy of the mod-boss-mechanics resolve spell, so the combat log names it; nothing is
kickable and nothing is dispellable: the kick and dispel table's row for Crowd Pummeler is "none / none / Weakened,
knockback"):

  214460  Left Hook       CP2: resolve copy, Physical, 40% / 60% of the reference row (the tank row on the tank),
                          Weakened; the east half of the pocket
  214461  Right Hook      CP3: the same, the west half
  214462  Crowd Pummel    CP4: the same within 12 yd of the frame origin; the script knocks the player 7.5 yd south
  214463  Uppercut        CP5 heroic: the same on the 8 yd lane down the center line; the script knocks them up
  214464  Clinch          CP6 heroic: the same past 12 yd (to 40)
  214465  Trample         CP8: resolve copy, Physical, 8% / 12% to everyone on the near side, no penalty
  214466  Trample         CP8: the ground slam ring on the frame stalker (look only)
  214467  Punch           the pose bar over a normal live marker: 1.5 s, no effect (SV 90752's punch precast)
  214468  Punch           the same over a heroic live marker: 0.8 s
  214469  Seeing Stars    a punch that landed: 3 s of stars over the head (look only), the punches' rider
  214470-214489 spare.

The bars are Physical and not interruptible (InterruptFlags 0, PreventionType 0): he has no kickable cast at all, and a
bar that a kick could stop must not look as if it stopped the punch the registry still lands. They keep his swing timer
(LESSONS L3). Tooltips are number-free.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import ATTR1_NO_THREAT, self_visual
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR4_NO_CAST_LOG,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    TYPE_MECHANICAL,
    boss_columns,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    CP_HIT_FLASH,
    CP_LANDED,
    CP_PUMMEL,
    CP_PUNCH_POSE,
    CP_STOMP,
    CP_UPPERCUT,
    DISPLAY_INVISIBLE_STALKER,
    DISPLAY_PUMMELER,
    PUMMELER_SCALE,
)

PUMMELER = 6229
FRAME_STALKER = 301115

creature_template_columns(PUMMELER, **boss_columns(
    'boss_crowd_pummeler_rework', 70.34, damage_modifier=1.7,
))
# The window ruling: scale 5 (the script also sets it with the display, SetDisplayId(6774, 5)).
creature_model(PUMMELER, display_id=DISPLAY_PUMMELER, scale=PUMMELER_SCALE, idx=0)

_CP = 'Gnomeregan build WP-D5 (Crowd Pummeler 9-60)'

_ATTR2_DO_NOT_RESET_COMBAT_TIMERS = 0x00020000      # a finished bar keeps his swing timer (LESSONS L3)
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000             # never leaves the instance on a character

# CrowdPummelerLogic.h Tune (the DT test pins each against the header).
_LIVE_MS_NORMAL = 1500              # kLiveMs.normal
_LIVE_MS_HEROIC = 800               # kLiveMs.heroic
_SEEING_STARS_MS = 3000             # kSeeingStarsMs

# Stock icons (Spell.dbc 2026-11-26).
_ICON_ARCING_SMASH = 277            # Arcing Smash 8374
_ICON_CROWD_PUMMEL = 756            # Crowd Pummel 10887
_ICON_UPPERCUT = 314                # Uppercut 10966
_ICON_TRAMPLE = 168                 # Trample 5568
_ICON_DIZZY = 87                    # Dizzy 9992


def _punch(spell_id: int, name: str, desc: str, notes: str, *, icon: int, visual: int):
    return resolve_copy(
        spell_id, name, School.NORMAL, desc,
        f'{_CP}, {notes} 40% normal / 60% heroic of the reference row (the tank row on the tank, tank included), '
        'Weakened, the Seeing Stars rider (214469). Copy of the resolve spell 205001 (Physical: armor cuts it, the '
        'precedent of the Zul\'Farrak axes).',
        icon=icon, visual=visual,
    )


def _pose_bar(spell_id: int, cast_ms: int, which: str):
    return spell(
        id=spell_id, name='Punch', school=School.NORMAL, cast_time_ms=cast_ms, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_ARCING_SMASH,
        notes=f'{_CP}: the pose over each {which} live marker (the ComboMachine\'s onLive: the bar is as long as the '
              'marker and ends at the strike). No effect: the registry lands the punch. SV 90752 (V: Ground Slam 8083 '
              'with its precast kit\'s anim 118 -> 16, AttackUnarmed, GnomeBot\'s one punch; the ring and shake at '
              'the bar\'s end). Physical and not interruptible (InterruptFlags 0, PreventionType 0): he has no '
              'kickable cast. Keeps his swing timer. The script also plays the AttackUnarmed emote at every strike '
              '(CP_PUNCH_EMOTE_ANIM 16), so the pose shows without the patch.',
        raw_overrides=kit_raw('Winds up a punch.', InterruptFlags=0, PreventionType=0, SpellVisualID_1=CP_PUNCH_POSE,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=_ATTR2_DO_NOT_RESET_COMBAT_TIMERS,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- CP2-CP6 the punches ---------------------------------------------------------------------------------------------

left_hook_214460 = _punch(
    214460, 'Left Hook', 'A hook across the east half of the room.',
    'CP2: the east half of the pocket (left of the frame\'s center line y 364.2, from the glass to 30 yd), every '
    'combination\'s pick.', icon=_ICON_ARCING_SMASH, visual=CP_HIT_FLASH,
)

right_hook_214461 = _punch(
    214461, 'Right Hook', 'A hook across the west half of the room.',
    'CP3: the west half of the pocket (right of the center line).', icon=_ICON_ARCING_SMASH, visual=CP_HIT_FLASH,
)

crowd_pummel_214462 = _punch(
    214462, 'Crowd Pummel', 'Both fists down in front of him.',
    'CP4: within 12 yd of the frame origin (-887.0, 364.2) (s7 #28 A); the script knocks each player hit 7.5 yd due '
    'south (KnockbackFrom, 12 / 6 yd/s).', icon=_ICON_CROWD_PUMMEL, visual=CP_PUMMEL,
)

uppercut_214463 = _punch(
    214463, 'Uppercut', 'A rising blow straight down the middle.',
    'CP5 (heroic): the lane 8 yd wide down the center line, from the glass to the south wall; the script knocks each '
    'player hit straight up (12 yd/s, no fall damage).', icon=_ICON_UPPERCUT, visual=CP_UPPERCUT,
)

clinch_214464 = _punch(
    214464, 'Clinch', 'Both arms sweep the far side of the room.',
    'CP6 (heroic): past 12 yd of the frame origin, to 40 yd (the reverse of Crowd Pummel).', icon=_ICON_CROWD_PUMMEL,
    visual=CP_PUMMEL,
)

# --- CP8 Trample -----------------------------------------------------------------------------------------------------

trample_214465 = resolve_copy(
    214465, 'Trample', School.NORMAL, 'Stamps on everyone close to the glass.',
    f'{_CP}, CP8: 8% normal / 12% heroic of the reference row (the tank row on the tank) to every player on the near '
    'side (within 12 yd of the frame origin), every 10 s from 6 s, never during a combination, and at once when '
    'nobody has been in his melee reach for 1.5 s (the kit\'s RegistryHit). No penalty (a healer pulse). Copy of the '
    'resolve spell 205001 (Physical). The ring is 214466.',
    icon=_ICON_TRAMPLE,
)

trample_look_214466 = self_visual(
    214466, 'Trample', CP_STOMP,
    f'{_CP}, CP8: the ring on the frame stalker 301115 at the frame origin as Trample lands (triggered). V\'s CP_STOMP '
    '8083 (Ground Slam: the ThunderClap ring 6.9 yd, shake 6).', icon=_ICON_TRAMPLE,
)

# --- the pose, the stars ---------------------------------------------------------------------------------------------

punch_bar_214467 = _pose_bar(214467, _LIVE_MS_NORMAL, 'normal (1.5 s)')
punch_bar_214468 = _pose_bar(214468, _LIVE_MS_HEROIC, 'heroic (0.8 s)')

seeing_stars_214469 = spell(
    id=214469, name='Seeing Stars', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=_SEEING_STARS_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_DIZZY,
    notes=f'{_CP}: the rider of every punch (214460-214464): 3 s of stars over the head of whoever it hit, look only '
          '(V\'s CP_LANDED 1763, Dizzy 9992\'s Sap stars). The penalty is the registry\'s Weakened. Dispel none (a '
          'look). AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('Punched.', 'Punched. Seeing stars.', CastingTimeIndex=1, SpellVisualID_1=CP_LANDED,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- 301115 the frame stalker ----------------------------------------------------------------------------------------

frame_stalker_301115 = creature_template(FRAME_STALKER, 'Crowd Pummeler Frame', **{
    **KIT_HELPER, 'minlevel': 28, 'maxlevel': 28, 'rank': 0, 'unit_class': 1, 'type': TYPE_MECHANICAL,
    'flags_extra': 0x40 | 0x80, 'ScriptName': 'npc_gnomer_pummeler_frame',
})
creature_model(FRAME_STALKER, display_id=DISPLAY_INVISIBLE_STALKER, idx=0)
