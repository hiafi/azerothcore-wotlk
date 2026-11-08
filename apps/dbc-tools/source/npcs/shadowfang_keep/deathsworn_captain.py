"""
Shadowfang Keep build WP-S6: Deathsworn Captain (.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md
s3.5 rows DC1-DC3, s3.6 row S6, s7 #14 and #25; build spec docs/dungeons/shadowfang-keep-rework.md SK 1044-1083 (build
spec), SK 956-1043 (design)). WP-S6 owns this file (its spells: 206010-206019 only, kSpellsDeathswornCaptain in
modules/mod-dungeon-bosses src/ShadowfangKeep/ShadowfangKeepRework.h; DeathswornCaptainLogic.h names the same ids).

- 3872 Deathsworn Captain: bound to boss_deathsworn_captain_rework (SmartAI off; WP-S6's SQL rev drops the stock rows:
  the despawn roll, now the instance's, Battle Stance 7165, Cleave 15496, Hamstring 9080), normal 8,857 health
  (HealthModifier 17, s3.7), stun immune (IMMUNITY_BOSS_STUN 1972, s7 #8; stock -114). Heroic 244,160 at boss tier is
  WP-H's override in source/world/dungeons/shadowfang_keep.py (roles={3872: "boss"}, s7 #14). Melee stays stock
  (DamageModifier 1.7, 2.0 s).

Spells. The registry owns the avoidable hits (Deathsworn Charge, Chain Charge, the cleave on non-tanks) through the two
resolve copies below, so the combat log names the mechanic and each hit shows Cleave's impact (SpellVisual 219,
Cleave_Impact_Chest) on the player hit. Cast bars are named no-effect casts, not interruptible (the build spec has no
interrupts). The tank's cleave is the script's own cast, its value set at launch (two of his swings).

  206010  Deathsworn Charge  DC1 cast bar, 2 s; Charge 32323's SpellVisual 3783 (ChargeTrail + DustCloud_Land on its
                             cast kit, so it plays as the bar completes: the moment he charges)
  206011  Deathsworn Charge  DC2 (heroic) the dash look on himself as the chained leg starts (no bar): SV 3783
  206012  Deathsworn Charge  DC1 / DC2 resolve copy, Physical: the registry's 35% + Weakened on the 3 yd line
  206013  Sweeping Cleave    DC3 cast bar, 2 s; Cleave 15496's SpellVisual 219 (Cleave_Cast_Base, the swing, as the
                             bar completes)
  206014  Sweeping Cleave    DC3 resolve copy, Physical: the registry's 40% + Weakened on non-tanks in the cone
  206015  Sweeping Cleave    DC3 the tank's own hit, two of his swings (spell_sfk_captain_cleave_tank)
  206016  Last Stand         DC4 (heroic) below 30%: melee attack speed +30% for the rest of the fight; Enrage 28371's
                             SpellVisual 5440 (BeastRageState + glowing hands)
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import self_visual
from lib.dsl.registry import creature_template_columns, scripted_by, spell

from ._common import (
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    TARGET_UNIT_CASTER,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)

creature_template_columns(3872, **boss_columns('boss_deathsworn_captain_rework', 17))

_SV_CHARGE = 3783           # Charge 32323 (handoff s3.10 / SK visuals: DC1, DC2)
_SV_CLEAVE = 219            # Cleave 15496, his stock ability (DC3)
_SV_ENRAGE = 5440           # Enrage 28371, Gluth's attack-speed enrage (DC4)
_ICON_CHARGE = 457          # Charge
_ICON_CLEAVE = 277          # Cleave
_ICON_ENRAGE = 957          # Enrage 28371

_TARGET_UNIT_TARGET_ENEMY = 6
_DEFENSE_MELEE = 2
_PREVENTION_PACIFY = 2
_ATTR2_CANT_CRIT = 0x20000000

_NOTE = 'Shadowfang Keep build WP-S6 (Deathsworn Captain):'

# --- DC1 / DC2 Deathsworn Charge, Chain Charge -----------------------------------------------------------------------
charge_bar_206010 = cast_bar(
    206010, 'Deathsworn Charge', 2000, 'Charges through everyone in a line.',
    f'{_NOTE} DC1 cast bar, 2 s, beside the registry line (3 yd wide, 5 yd past a random non-tank at least 8 yd away, '
    'the first 4 yd excluded); he charges along it when it resolves. Charge 32323\'s SpellVisual 3783: its cast kit '
    '(ChargeTrail, DustCloud_Land) plays as the bar completes, when he charges. Icon 457.',
    icon=_ICON_CHARGE, visual=_SV_CHARGE)

charge_trail_206011 = self_visual(
    206011, 'Deathsworn Charge', _SV_CHARGE,
    f'{_NOTE} DC2 (heroic) Chain Charge has no cast bar (1.5 s marker from his landing spot): when its line resolves '
    'he casts this on himself (triggered) as he charges, for Charge 32323\'s look (SpellVisual 3783: ChargeTrail + '
    'DustCloud_Land on its cast kit, which an instant plays as stock Charge does).',
    icon=_ICON_CHARGE)

charge_hit_206012 = resolve_copy(
    206012, 'Deathsworn Charge', School.NORMAL, 'Trampled by a charge.',
    f'{_NOTE} DC1 / DC2 resolve copy (Physical): the registry\'s 35% of the reference row (455 normal, 1,442 heroic) '
    '+ Weakened on everyone in the 3 yd line. Impact: Cleave\'s SpellVisual 219 (Cleave_Impact_Chest) on each player '
    'hit.',
    icon=_ICON_CHARGE, visual=_SV_CLEAVE)

# --- DC3 Sweeping Cleave ---------------------------------------------------------------------------------------------
cleave_bar_206013 = cast_bar(
    206013, 'Sweeping Cleave', 2000, 'Cleaves everyone in front of the caster.',
    f'{_NOTE} DC3 cast bar, 2 s, beside the registry cone (90 degrees, 10 yd, tank exempt: a Frontal for the bots). '
    'Cleave 15496\'s SpellVisual 219: its cast kit (Cleave_Cast_Base, a crescent swing) plays as the bar completes, '
    'when the cone lands. Icon 277.',
    icon=_ICON_CLEAVE, visual=_SV_CLEAVE)

cleave_hit_206014 = resolve_copy(
    206014, 'Sweeping Cleave', School.NORMAL, 'Caught in a sweeping cleave.',
    f'{_NOTE} DC3 resolve copy (Physical): the registry\'s 40% of the reference row (520 normal, 1,648 heroic) + '
    'Weakened on every non-tank in the cone. Impact: Cleave\'s SpellVisual 219 (Cleave_Impact_Chest).',
    icon=_ICON_CLEAVE, visual=_SV_CLEAVE)

cleave_tank_206015 = spell(
    id=206015, name='Sweeping Cleave', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=1, die_sides=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
                    potency_excluded='boss spell: the script sets the value at launch (two of the caster\'s melee '
                                     'swings, Unit::CalculateDamage)')],
    spell_icon_id=_ICON_CLEAVE,
    notes=f'{_NOTE} DC3 the tank\'s own hit ("tank two swings"): the cone is TankExempt, so when it resolves the '
          'script casts this (triggered) on his victim if it stands in the arc. spell_sfk_captain_cleave_tank sets '
          'the value in OnEffectLaunchTarget to two rolls of his main-hand damage (template weapon damage and '
          'DamageModifier: stock 1.7 on normal, the heroic template\'s boss tier on heroic), so the tank\'s '
          'damage-taken modifiers apply. Physical (armor applies, as on a swing), melee defense (dodge, parry and '
          'block apply, as on a swing), cannot crit, IGNORE_CASTER_MODIFIERS (the Pilot lesson: the spell path adds '
          'no damage-done bonus; the swings already hold his). Cleave 15496\'s SpellVisual 219 and icon 277. Base '
          'points 1 is a placeholder only.',
    raw_overrides=kit_raw('Strikes twice with the caster\'s weapon.', instant=True, DefenseType=_DEFENSE_MELEE,
                          PreventionType=_PREVENTION_PACIFY, InterruptFlags=0, AttributesEx2=_ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG,
                          SpellVisualID_1=_SV_CLEAVE),
)
scripted_by(cleave_tank_206015, 'spell_sfk_captain_cleave_tank')

# --- DC4 Last Stand (heroic) -----------------------------------------------------------------------------------------
last_stand_206016 = spell(
    id=206016, name='Last Stand', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_MELEE_HASTE, base_points=29,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_ENRAGE,
    notes=f'{_NOTE} DC4 (heroic): below 30% health, melee attack speed +30% (MOD_MELEE_HASTE 138, BasePoints 29 + '
          'DieSides 1; DeathswornCaptainLogic.h kLastStandHastePct) for the rest of the fight (permanent duration; '
          'the reset clears it). Cast by the script on himself, triggered, once. Enrage 28371\'s SpellVisual 5440 and '
          'icon 957. Dispel none (the build spec has no dispels). Miner Johnson\'s Gold Fever 205233 shape.',
    raw_overrides=kit_raw('Attacking faster.', 'Attacking faster.', SpellVisualID_1=_SV_ENRAGE),
)
