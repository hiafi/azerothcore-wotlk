"""
Shadowfang Keep build WP-S3: Baron Silverlaine and his three echoes
(.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md s3.5 rows BS1-BS7, s3.6 row S3; build spec
docs/dungeons/shadowfang-keep-rework.md SK 578-621 (build spec), SK 483-577 (design)). WP-S3 owns this file (its
spells: kSpellsSilverlaine 205945-205964 only; modules/mod-dungeon-bosses src/ShadowfangKeep/SilverlaineLogic.h names
the same ids; creatures 300503-300505). User ruling (handoff s10, s7 #21): the echoes come on timers (15 s, then every
25 s), not at 75 / 50 / 25% health.

- 3887 Baron Silverlaine: bound to boss_baron_silverlaine_rework (SmartAI off; WP-S3's core rev drops the stock rows:
  the aggro yell is kept in C++, Veil of Shadow 7068 is replaced by Accursed Veil), normal 12.1k (HealthModifier 25,
  handoff s3.7), stun immune (IMMUNITY_BOSS_STUN 1972, s7 #8). Stock melee (DamageModifier 1.7, 2.0 s). Heroic 305,200
  is WP-H's override in source/world/dungeons/shadowfang_keep.py.
- 300503 Echo of Rethilgore, 300504 Echo of Razorclaw, 300505 Echo of Odo (npc_sfk_echo): boss-kit adds Silverlaine
  summons into his hall. Copies of the stock bosses' looks (displays 524, 524, 522: Rethilgore's, Razorclaw's and Odo's
  own) at level 20, elite warriors like them, made spectral by 205948 (Ghost Visual's SV 886). Normal health 1,200
  (warrior base 484 x HealthModifier 2.4793), heroic 20,000 (WP-H's `_KIT_ADD_HEROIC`); each names its heroic entry
  (STAGE-H: 310058-310060). Plain melee (DamageModifier 1.0, 2.0 s): their threat is their mechanic, and their heroic
  melee is the damage hook's tier swing. No loot, gold or XP (flags_extra NO_XP: heroic summons them again and again),
  stunnable (no immunity set, handoff s6 "kit adds stay stunnable"). unit_flags 64 as the three stock bosses.

The echoes reuse the other bosses' spells, never copies (handoff s3.3 item 3): Rethilgore's Soul Drain channel, tick,
fragment heal, streak and feast (205913-205917, rethilgore.py), Razorclaw's Meat Hook bar, hit and chain (205930-205932,
razorclaw.py), Odo's howl, Hunted and catch (205990-205992, odo_the_blindwatcher.py). Only the Echo of Odo's lighter
Maul needs its own row (205947), on S5's generic script.

  205945  Accursed Veil      BS6: the real 1.5 s cast (interruptible: InterruptFlags 15, PreventionType silence) on a
                             random non-tank, and the curse it applies: Curse (dispellable), 12 s, 3% Shadow of the
                             reference non-tank row every 2 s (spell_sfk_silverlaine_accursed_veil: RefFlat, 39 normal /
                             124 heroic), healing received -50%. A pulse's catch is the same spell cast triggered by
                             Silverlaine (its own 12 s). Veil of Shadow 7068's SpellVisual 561 (shadow hands).
  205946  Accursed Veil      BS6: the 2 s pulse Spread's resolve copy (Shadow, no damage: catching the curse is the
                             penalty, no Weakened), SV 561 on whoever stood within 4 yd.
  205947  Maul               BS5: the Echo of Odo's catch rider: 1.5 s stun + a bleed of 20% over 1.5 s (3 ticks of
                             RefFlat(20 / 3 %): 260 normal, 824 heroic), spell_sfk_hunt_maul (S5's generic Maul script:
                             the bleed's base points are the total percent). Odo's 205993 with his numbers swapped.
  205948  Spectral Echo      BS1: the echoes' look, a shown (not passive) permanent DUMMY aura each echo casts on
                             itself: Ghost Visual 9617's SpellVisual 886 (pale, 50% alpha, ghost particles).
  205949  Echo of the Night  BS1: the burst into the hall, a self visual (Spirit Particles (Spawn) 37119's SV 4490).
  205950-205964 spare.
"""

from lib.dsl import RANGE_SELF, AuraType, DispelType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR0_NO_ACTIVE_DEFENSE,
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    TARGET_UNIT_TARGET_ENEMY,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    KIT_CREATURE,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    kit_raw,
    resolve_copy,
)
from ._visuals import BS_ACCURSED_VEIL, BS_ECHO_ARRIVAL, BS_ECHO_GHOST, DISPLAY_ECHO_ODO, DISPLAY_ECHO_RETHILGORE

creature_template_columns(3887, **boss_columns('boss_baron_silverlaine_rework', 25))

# --- the echoes (300503-300505) --------------------------------------------------------------------------------------

_WARRIOR_BASE_HEALTH_20 = 484       # creature_classlevelstats, level 20 warrior, exp 0 (SK "Tuning model")
_ECHO_HEALTH_NORMAL = 1200          # SilverlaineLogic.h kEchoHealth
_FLAGS_EXTRA_NO_XP = 0x40
_UNIT_FLAGS_STOCK_BOSSES = 64       # 3914 / 3886 / 4279's own unit_flags (read-only SELECT 2026-11-07)

_ECHO = {
    **KIT_CREATURE, 'minlevel': 20, 'maxlevel': 20, 'rank': 1, 'unit_class': 1, 'unit_flags': _UNIT_FLAGS_STOCK_BOSSES,
    'HealthModifier': round(_ECHO_HEALTH_NORMAL / _WARRIOR_BASE_HEALTH_20, 4), 'DamageModifier': 1.0,
    'BaseAttackTime': 2000, 'ExperienceModifier': 0.0, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0,
    'mingold': 0, 'maxgold': 0, 'flags_extra': _FLAGS_EXTRA_NO_XP, 'ScriptName': 'npc_sfk_echo',
}

echo_of_rethilgore_300503 = creature_template(
    300503, 'Echo of Rethilgore', **{**_ECHO, 'difficulty_entry_1': 310058},
)
creature_model(300503, display_id=DISPLAY_ECHO_RETHILGORE)

echo_of_razorclaw_300504 = creature_template(
    300504, 'Echo of Razorclaw', **{**_ECHO, 'difficulty_entry_1': 310059},
)
creature_model(300504, display_id=DISPLAY_ECHO_RETHILGORE)    # 524, Razorclaw's own display too

echo_of_odo_300505 = creature_template(
    300505, 'Echo of Odo', **{**_ECHO, 'difficulty_entry_1': 310060},
)
creature_model(300505, display_id=DISPLAY_ECHO_ODO)

# --- spells (205945-205964) ------------------------------------------------------------------------------------------

_MECHANIC_STUN = 12
_MECHANIC_BLEED = 15
_DEFENSE_MAGIC = 1

_ICON_VEIL_OF_SHADOW = 173      # Veil of Shadow 7068
_ICON_GHOST = 143               # Ghost Visual 9617
_ICON_REND = 245                # Rend 772 (a bleed; Odo's Maul 205993 uses it too)

_VEIL_TICK_NOTE = ('boss spell: spell_sfk_silverlaine_accursed_veil sets each tick (DungeonKit::RefFlat, 3% of the '
                   'reference non-tank row); the base points are a placeholder')
_MAUL_NOTE = ('boss spell: spell_sfk_hunt_maul sets each tick (DungeonKit::RefFlat, a percent of reference health); '
              'the base points are the total percent')

accursed_veil_205945 = spell(
    id=205945, name='Accursed Veil', school=School.SHADOW, dispel=DispelType.CURSE, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=1500, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=45.0, duration_ms=12000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=2, amplitude=2000,
               implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_VEIL_TICK_NOTE),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_HEALING_PCT, base_points=-51,
               implicit_target_a=TARGET_UNIT_TARGET_ENEMY,
               potency_excluded='Accursed Veil: a flat -50% healing received, not a damage or heal value'),
    ],
    spell_icon_id=_ICON_VEIL_OF_SHADOW,
    notes='Shadowfang Keep WP-S3, BS6 Accursed Veil: Silverlaine\'s 1.5 s cast (stock Veil of Shadow\'s) on a random '
          'non-tank, at 6 s then every 20 s; interruptible (InterruptFlags 15, PreventionType silence: a kick is the '
          'reward; on the descriptor\'s interrupt list). The curse: Curse (DispelType 2, removable by a mage\'s Remove '
          'Curse or a shaman\'s Cleanse Spirit at 18; on the dispel list), 12 s, 3% Shadow of the reference non-tank '
          'row every 2 s (spell_sfk_silverlaine_accursed_veil, RefFlat: 39 normal, 124 heroic; 18% over its life), '
          'healing received -50% (BasePoints -51 + DieSides 1). Every 2 s the script pulses a 4 yd Spread around each '
          'cursed player; an uncursed player inside catches this same spell, cast triggered by Silverlaine (its own '
          '12 s), the tank included. IGNORE_CASTER_MODIFIERS and cannot crit, so the ticks are the reference numbers. '
          'Veil of Shadow 7068\'s SpellVisual 561 (shadow hands, cripple state).',
    raw_overrides=kit_raw('Curses the target with Shadow damage over time and halves the healing it receives for $d. '
                          'The curse spreads to anyone within 4 yards.',
                          'Shadow damage over time. Healing received reduced. Keep 4 yards from your allies.',
                          InterruptFlags=15, PreventionType=1, DefenseType=_DEFENSE_MAGIC, SpellPriority=50,
                          AttributesEx2=ATTR2_CANT_CRIT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                          SpellVisualID_1=BS_ACCURSED_VEIL),
)
scripted_by(accursed_veil_205945, 'spell_sfk_silverlaine_accursed_veil')

accursed_veil_spread_205946 = resolve_copy(
    205946, 'Accursed Veil', School.SHADOW, 'The curse leaps to you.',
    'Shadowfang Keep WP-S3, BS6: a copy of the registry resolve spell 205001 under its own name (Shadow), bound to '
    'spell_boss_mechanics_resolve: the 2 s pulse\'s 4 yd Spread around every cursed player (SelfTrigger on 205945; '
    'handoff s7 #18, a fresh Spread each pulse). No damage and no Weakened: the hit is the ledger\'s failure and the '
    'script\'s OnHit casts the curse (205945) on the player who stood close. Veil of Shadow 7068\'s SpellVisual 561 as '
    'the impact.',
    icon=_ICON_VEIL_OF_SHADOW, visual=BS_ACCURSED_VEIL)

echo_maul_205947 = spell(
    id=205947, name='Maul', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_ACTIVE_DEFENSE, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=1500,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, mechanic=_MECHANIC_STUN,
               implicit_target_a=TARGET_UNIT_TARGET_ANY),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=20, die_sides=0,
               amplitude=500, mechanic=_MECHANIC_BLEED, implicit_target_a=TARGET_UNIT_TARGET_ANY,
               potency_excluded=_MAUL_NOTE),
    ],
    spell_icon_id=_ICON_REND,
    notes='Shadowfang Keep WP-S3, BS5 the Echo of Odo\'s Maul: the hunt circle\'s rider on a catch (the registry casts '
          'it from the resolve marker with Silverlaine as original caster; the catch itself is Odo\'s 205992, SV 577). '
          'A 1.5 s stun and a bleed of 20% of the non-tank row over 1.5 s: 3 ticks of RefFlat(20 / 3 %) (260 normal, '
          '824 heroic), set by spell_sfk_hunt_maul (S5\'s generic Maul script, registered once by Odo\'s AddSC) from '
          'the bleed\'s base points (the total percent, die 0). Damage over time: no Weakened (ruling 17). Bleed '
          'mechanic on the DoT, not dispellable. No active defense, no redirection or reflection, ignores LoS, cannot '
          'crit, always hits, ignores caster modifiers. Odo\'s 205993 with the echo\'s numbers (SK BS5).',
    raw_overrides=kit_raw('Pinned and mauled: stunned, and bleeding for 20% of your health over $d.',
                          'Stunned. Bleeding.', instant=True, DefenseType=_DEFENSE_MAGIC, InterruptFlags=0,
                          PreventionType=0, AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(echo_maul_205947, 'spell_sfk_hunt_maul')

spectral_echo_205948 = spell(
    id=205948, name='Spectral Echo', school=School.SHADOW, dispel=0, mechanic=0,
    attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_GHOST,
    notes='Shadowfang Keep WP-S3, BS1: the echoes\' spectral look. Each echo casts it (triggered) on itself as it is '
          'summoned; permanent, hidden from the buff frame, not passive (a passive aura is never sent to the client, '
          'so its look would not play). A DUMMY with no handler: Ghost Visual 9617\'s SpellVisual 886 (pale blue tint, '
          '50% alpha, ghost particles) on the stock worgen displays 524 / 522 (handoff s3.10 gap 9, the top pick). '
          'Dispel none.',
    raw_overrides=kit_raw('A spectral echo of the night of the massacre.', 'Spectral.', instant=True,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          SpellVisualID_1=BS_ECHO_GHOST),
)

echo_arrival_205949 = self_visual(
    205949, 'Echo of the Night', BS_ECHO_ARRIVAL,
    'Shadowfang Keep WP-S3, BS1: an echo bursts into the hall. The echo casts it (triggered) on itself as it is '
    'summoned, beside Silverlaine\'s yell naming it. Spirit Particles (Spawn) 37119\'s SpellVisual 4490.',
    icon=_ICON_GHOST, school=School.SHADOW)
