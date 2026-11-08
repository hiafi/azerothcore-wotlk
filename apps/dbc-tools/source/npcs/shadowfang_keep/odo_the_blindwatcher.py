"""
Shadowfang Keep build WP-S5: Odo the Blindwatcher (.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md
s3.5 rows OD1-OD6, s3.6 row S5; build spec docs/dungeons/shadowfang-keep-rework.md SK 904-952 (build spec), SK 816-903
(design)). WP-S5 owns this file (its spells: kSpellsOdo 205990-206009 in modules/mod-dungeon-bosses
src/ShadowfangKeep/ShadowfangKeepRework.h only; OdoLogic.h names the same ids).

- 4279 Odo the Blindwatcher: boss_odo_the_blindwatcher_rework (SmartAI off; WP-S5's SQL rev drops the stock rows: Call
  for Help gone, Howling Rage 7481 / 7483 / 7484 kept in C++), normal HealthModifier 28 (14,588 at level 21, warrior;
  handoff s3.7), stun immune (IMMUNITY_BOSS_STUN 1972, s7 #8). Stock melee (DamageModifier 1.7, 2.0 s) and stock run
  rate 1.14 out of the Hunt; the script sets MOVE_RUN 0.8 / 0.95 while hunting (handoff s8 #11). Heroic health 320,460
  is WP-H's override in source/world/dungeons/shadowfang_keep.py. No kit adds; the three Alarm Bells are gameobjects
  (301101, WP-K's template, WP-S5's spawns).

Spells. The Hunt's catch circle and the bell landing deal their damage through the registry (dungeon copies of the
mod-boss-mechanics resolve spell: the registry's percent of the reference row, the combat log names the mechanic). The
Maul's bleed is a script number (spell_sfk_hunt_maul: RefFlat ticks). The rest are a cast bar, looks and auras:

  205990  The Hunt           OD1 the 2 s howl, a cast bar on Odo (Howling Rage's SpellVisual 754, the roar)
  205991  Hunted             OD1 the debuff on the hunted player, 12 s (the howl + the chase; the script removes it)
  205992  Maul               OD2 the catch: the hunt circle's resolve copy, Physical, no damage of its own (the circle
                             has none: the hit is the ledger's catch); Maul 54459's SpellVisual 577 (claw swipe and
                             blood) is the catch's impact. Its rider is 205993.
  205993  Maul               OD2 the stun and bleed: 3 s stun + 35% of the non-tank row over 3 s (1 s ticks, each
                             RefFlat(35 / 3 %)); spell_sfk_hunt_maul (the Hunt's generic Maul script: the bleed's
                             value is the total percent). The Echo of Odo's lighter Maul (WP-S3) is its own copy on
                             the same script.
  205994  Bound              OD4 the bound to the bell: Pounce 55077's SpellVisual 12083 (dust at takeoff), on Odo
  205995  Bell Landing       OD4 the landing's hit: resolve copy, Physical, 35% + 1 Weakened (registry); SV 12083's dust
  205996  Ring the Bell      OD3 the ring flash on the ringer: Sonic Boom 33666's SpellVisual 8124 (a shockwave)
  205997  Deafened           OD5 Odo after landing: damage taken +25% for 5 s (Sonic Burst 8281's SpellVisual 875)
  205998  Blood Frenzy       OD6 heroic: damage dealt +20% per stack, no cap (255 stacks), for the fight (Frenzy 23537's
                             SpellVisual 870)
  205999  Cracked Bell       a cracked bell's smoke: a hidden aura on the visual stalker 300516 at the bell (Small White
                             Smoke Flare 43452's SpellVisual 9774)
  206000-206009 spare

The bell toll is SoundEntries 9154 (BellTollKharazhan), played by the script on the bell (PlayDirectSound).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import self_visual
from lib.dsl.registry import creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import OD_BELL_RING_FLASH, OD_CRACKED_BELL_SMOKE, OD_DEAFENED, OD_FRENZY, OD_HOWLING_RAGE, OD_MAUL

creature_template_columns(4279, **boss_columns('boss_odo_the_blindwatcher_rework', 28))

_ATTR0_DO_NOT_DISPLAY = 0x00000080
_ATTR0_NO_ACTIVE_DEFENSE = 0x00200000
_ATTR1_NO_REDIRECTION = 0x00000008
_ATTR1_NO_REFLECTION = 0x00000080
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_ALWAYS_HIT = 0x00040000

_MECHANIC_STUN = 12
_MECHANIC_BLEED = 15
_DEFENSE_MAGIC = 1
_SCHOOL_MASK_ALL = 127
_STACKS_NO_CAP = 255

_SV_POUNCE = 12083              # Pounce 55077: DustCloud_Land at takeoff and landing (VISUALS-REPORT s16, "OD4 bound")

_ICON_GENERIC = 1
_ICON_REND = 245                # Rend 772 (a bleed)
_ICON_FRENZY = 169              # Frenzy 32964

_SCRIPT_DAMAGE = ('boss spell: spell_sfk_hunt_maul sets each tick (DungeonKit::RefFlat, a percent of reference '
                  'health); the base points are the total percent')
_MAUL_SCRIPT = 'spell_sfk_hunt_maul'

# --- OD1 The Hunt ----------------------------------------------------------------------------------------------------
hunt_howl_205990 = cast_bar(
    205990, 'The Hunt', 2000, 'Sniffs the air for a heartbeat to hunt.',
    'Shadowfang Keep WP-S5 (Odo) OD1 The Hunt: the 2 s howl, cast by Odo on himself (not triggered, so the bar shows) '
    'while he stands and faces the hunted player; the registry circle on him (3 yd, the hunted player only) warns '
    'the same 2 s. Howling Rage 7481\'s SpellVisual 754 (the roar, VISUALS-REPORT s16). Not interruptible (the kit '
    'cast bar rule: a kick must not look as if it stopped the Hunt).',
    visual=OD_HOWLING_RAGE,
)

hunted_205991 = spell(
    id=205991, name='Hunted', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=12000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_GENERIC,
    notes='Shadowfang Keep WP-S5 (Odo) OD1: the Hunted debuff (SK aura text "Odo is hunting you."). Odo casts it '
          '(triggered) on the hunted player as the howl starts; 12 s = the howl (2 s) + the chase (10 s); the script '
          'removes it when the Hunt ends (caught, escaped, a bell). DUMMY, Dispel none, lands through immunities.',
    raw_overrides=kit_raw('Odo is hunting you.', 'Odo is hunting you.', instant=True, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- OD2 Maul ---------------------------------------------------------------------------------------------------------
maul_hit_205992 = resolve_copy(
    205992, 'Maul', School.NORMAL, 'Caught by Odo.',
    'Shadowfang Keep WP-S5 (Odo) OD2 Maul: the catch, the hunt circle\'s resolve copy (205001 Physical). The circle '
    'has no damage of its own: its hit (0) is the catch in the registry ledger (tag 1 normal, 5 heroic, as the '
    'sfk-hunt drill) and its impact, Maul 54459\'s SpellVisual 577 (claw swipe and blood). Its rider, 205993, is the '
    'stun and the bleed.',
    visual=OD_MAUL,
)

maul_205993 = spell(
    id=205993, name='Maul', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | _ATTR0_NO_ACTIVE_DEFENSE, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=3000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, mechanic=_MECHANIC_STUN,
               implicit_target_a=TARGET_UNIT_TARGET_ANY),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=35, die_sides=0,
               amplitude=1000, mechanic=_MECHANIC_BLEED, implicit_target_a=TARGET_UNIT_TARGET_ANY,
               potency_excluded=_SCRIPT_DAMAGE),
    ],
    spell_icon_id=_ICON_REND,
    notes='Shadowfang Keep WP-S5 (Odo) OD2 Maul: the catch\'s rider (the registry casts it from the resolve marker '
          'with Odo as original caster). A 3 s stun (Dungeon ruling 6, the one 3 s stun of the dungeon) and a bleed of '
          '35% of the non-tank row over 3 s: 3 ticks of RefFlat(35 / 3 %) (455 normal, 1,442 heroic), set by '
          'spell_sfk_hunt_maul from the bleed\'s base points (the total percent, die 0). Damage over time: no Weakened '
          '(ruling 17). Bleed mechanic on the DoT (armor does not apply), not dispellable. No active defense, no '
          'redirection or reflection, ignores LoS, cannot crit, always hits, ignores caster modifiers (R1 S-1: Blood '
          'Frenzy and Howling Rage stay out of it). No visual of its own: the catch (205992) shows the claw.',
    raw_overrides=kit_raw('Pinned and mauled: stunned, and bleeding for 35% of your health over $d.',
                          'Stunned. Bleeding.', instant=True, DefenseType=_DEFENSE_MAGIC, InterruptFlags=0,
                          PreventionType=0, AttributesEx=_ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION,
                          AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
                          AttributesEx3=_ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(maul_205993, _MAUL_SCRIPT)

# --- OD3 / OD4 the bells ----------------------------------------------------------------------------------------------
bound_205994 = self_visual(
    205994, 'Bound', _SV_POUNCE,
    'Shadowfang Keep WP-S5 (Odo) OD4: the bound to the rung bell, cast (triggered) by Odo on himself as he jumps '
    '(the jump lands 2 s later on the bell). Pounce 55077\'s SpellVisual 12083 (dust at takeoff).',
)

bell_landing_205995 = resolve_copy(
    205995, 'Bell Landing', School.NORMAL, 'Odo crashes into the bell.',
    'Shadowfang Keep WP-S5 (Odo) OD4 Bell landing: the 6 yd circle on the rung bell as Odo lands, 35% of the non-tank '
    'row (455 normal, 1,442 heroic) + 1 Weakened (ruling 17), through the registry (tag 3). Copy of the resolve spell '
    '205001 (Physical); Pounce 55077\'s SpellVisual 12083 (the landing dust) is the hit\'s impact.',
    visual=_SV_POUNCE,
)

bell_ring_205996 = self_visual(
    205996, 'Ring the Bell', OD_BELL_RING_FLASH,
    'Shadowfang Keep WP-S5 (Odo) OD3: the ring, cast (triggered) by the ringer on himself as the bell rings (1 s '
    'under it, or a click). Sonic Boom 33666\'s SpellVisual 8124 (a shockwave at the ringer, under the bell); the '
    'toll is SoundEntries 9154, played by the script.',
)

# --- OD5 Deafened / OD6 Blood Frenzy ----------------------------------------------------------------------------------
deafened_205997 = spell(
    id=205997, name='Deafened', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=5000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=24,
                    misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Deafened: a flat +25% damage taken debuff on the boss, not a damage value')],
    spell_icon_id=_ICON_GENERIC,
    notes='Shadowfang Keep WP-S5 (Odo) OD5 Deafened: Odo smashes into the bell and takes 25% more damage (BasePoints '
          '24 + DieSides 1, all schools) for 5 s: the group\'s damage window. Cast (triggered) by Odo on himself as he '
          'lands. Shown on his target frame (debuff). Sonic Burst 8281\'s SpellVisual 875.',
    raw_overrides=kit_raw('Damage taken increased by $s1%. Lasts $d.', 'Taking more damage.', instant=True,
                          AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=OD_DEAFENED),
)

blood_frenzy_205998 = spell(
    id=205998, name='Blood Frenzy', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=19,
                    misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Blood Frenzy: a flat +20% damage done per stack, a boss enrage')],
    spell_icon_id=_ICON_FRENZY,
    notes='Shadowfang Keep WP-S5 (Odo) OD6 Blood Frenzy (heroic): every Maul gives Odo a stack, damage dealt +20% per '
          'stack (BasePoints 19 + DieSides 1, all schools), for the rest of the fight (permanent; a reset clears it). '
          'No cap: Dungeon ruling 7, the fight\'s failure-driven enrage (CumulativeAura 255, DungeonKit::AddStacks). '
          'Frenzy 23537\'s SpellVisual 870; stock Frenzy icon 169.',
    raw_overrides=kit_raw('Damage dealt increased by $s1%.', 'Damage dealt increased.', instant=True,
                          CumulativeAura=_STACKS_NO_CAP, SpellVisualID_1=OD_FRENZY),
)

cracked_bell_205999 = spell(
    id=205999, name='Cracked Bell', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=_ATTR0_DO_NOT_DISPLAY | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_GENERIC,
    notes='Shadowfang Keep WP-S5 (Odo) OD3: a cracked bell\'s look (handoff s3.10 gap 16, VISUALS-REPORT s16 option '
          '1). The visual stalker 300516, summoned by the bell gameobject at its foot while the bell is cracked (40 s '
          'on normal, the fight on heroic), casts it on itself: a hidden permanent DUMMY aura carrying Small White '
          'Smoke Flare 43452\'s SpellVisual 9774 (the bell smokes). The stalker despawns when the bell is ready again.',
    raw_overrides=kit_raw('', instant=True, AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=OD_CRACKED_BELL_SMOKE),
)
