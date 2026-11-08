"""
Shadowfang Keep build WP-S7: Fenrus the Devourer (.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md
s3.5 rows FN1-FN8, s3.6 row S7; build spec docs/dungeons/shadowfang-keep-rework.md SK 1183-1234 (build spec), SK
1087-1182 (design)). WP-S7 owns this file (its spells: kSpellsFenrus 206020-206039 in modules/mod-dungeon-bosses
src/ShadowfangKeep/ShadowfangKeepRework.h only; FenrusLogic.h names the same ids).

- 4274 Fenrus the Devourer: bound to boss_fenrus_the_devourer_rework (SmartAI off; WP-S7's SQL rev drops the stock
  rows), normal health HealthModifier 22 = 11,462 (handoff s3.7), stun immune (IMMUNITY_BOSS_STUN 1972, s7 #8). Stock
  melee (DamageModifier 3.3) and Toxic Saliva 7125. Heroic 259,420 is WP-H's override in
  source/world/dungeons/shadowfang_keep.py; phase two's 40% is the script's.
- 4627 Arugal's Voidwalker (stock, rebound, handoff s3.4: only this fight summons it): npc_sfk_voidwalker, SmartAI off
  (the rev drops its 3 rows), normal health 800 (warrior base 484 at level 20 x 1.6529), standing still until the
  script moves it (MovementType 0). Stunnable on purpose (no immunity set). Heroic 12,000 is WP-H's override.

Spells (FN ids are the build spec's). The registry resolve copies (206020, 206025, 206027) carry the attribute set of
mod-boss-mechanics' 205001 (lib/dsl/dungeon_kit.py resolve_copy) and are bound to its resolve script, so they rename the
hit in the combat log and carry its look; shape, damage and Weakened stay the registry's.

  206020  Arugal's Lightning   FN1 the 3 yd strike at a room-edge point (resolve copy, Nature), the sky bolt SV 986
                               (Lightning Cloud 6535, CallLightning_Impact) on every player it hits.
  206021  Arugal's Lightning   FN1 / FN2 the bolt on the voidwalker as it steps out of the strike (self look, SV 986),
                               so the strike shows at the point whoever stands there.
  206022  Void Pulse           FN3 the voidwalker's 1.5 s cast, interruptible (InterruptFlags 15, PreventionType
                               silence), then Shadow to every player within 100 yd (players only): 4% of the reference
                               row, heroic +1% per landed pulse up to 10% (spell_sfk_fenrus_void_pulse sets RefFlat at
                               launch). Ignores caster modifiers and LoS, cannot crit. Shadow Burst 28447's SV 45.
  206023  Shadow Fenrus        FN5 (heroic) the shadow wolf: a shown DUMMY aura on Fenrus for the rest of the fight
                               with Shadowform 22917's SV 3619 (dark purple, translucent); the script turns his melee
                               Shadow. Not dispellable.
  206024  Shadow Leap          FN6 (heroic) the 2 s crouch (cast bar, not interruptible: the Bait owns the hit).
  206025  Shadow Leap          FN6 (heroic) the landing (resolve copy, Shadow): 25% in 6 yd of the farthest player;
                               also bound to spell_sfk_fenrus_shadow_leap, which multiplies the hit by (1 + 2 x the
                               target's Shadow Scars). Shadow Pounce 52327's SV 8262 (the shadow puff).
  206026  Shadow Scar          FN7 (heroic) the Bait's rider and rule aura: a stacking DUMMY debuff (CumulativeAura 99)
                               for the rest of the fight; the script reads its stacks (+200% Shadow Leap damage taken
                               per stack) and removes it on a wipe or his death. Dispel none.
  206027  Shadow Lightning     FN8 (heroic) the 3 yd strike under a random player (resolve copy, Shadow), WP-V's purple
                               bolt (SV 90400, patch-M) on every player it hits. No Weakened (Dungeon ruling 10).
  206028  Shadow Lightning     FN8 (heroic) the same bolt at the point, on the strike / visual stalker 300516 when that
                               creature is declared (self look).
  206029-206039 spare.

Stock spell kept (handoff s3.7, DD scales it on heroic): Toxic Saliva 7125.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    TARGET_SRC_CASTER,
    TARGET_UNIT_SRC_AREA_ENEMY,
    self_visual,
)
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
from ._visuals import FN_LIGHTNING, FN_SHADOW_LEAP_DEPARTURE, FN_SHADOW_LIGHTNING, FN_SHADOWFORM, FN_VOID_PULSE

creature_template_columns(4274, **boss_columns('boss_fenrus_the_devourer_rework', 22))

# Arugal's Voidwalker: 484 (warrior base at 20) x 1.6529 = 800 (SK tuning).
creature_template_columns(4627, ScriptName='npc_sfk_voidwalker', AIName='', HealthModifier=1.6529, MovementType=0)

# --- spells (206020-206039) ----------------------------------------------------------------------------------------

_ICON_LIGHTNING = 141           # Lightning Cloud 6535
_ICON_SHADOW_BURST = 207        # Shadow Burst 28447
_ICON_SHADOWFORM = 217          # Shadowform 22917
_ICON_SHADOW_POUNCE = 164       # Shadow Pounce 52327
_ICON_SHADOWFURY = 1988         # Shadowfury 30283

_FN = 'Shadowfang Keep build WP-S7'
_REF_FLAT_NOTE = ('Shadowfang Keep build: the damage is set per target by spell_sfk_fenrus_void_pulse '
                  '(OnEffectLaunchTarget SetEffectValue = DungeonKit::RefFlat, a percent of the reference health row)')

arugals_lightning_206020 = resolve_copy(
    206020, "Arugal's Lightning", School.NATURE, 'Lightning from Arugal\'s Focus.',
    f'{_FN}, FN1: Arugal\'s strike at a room-edge point, 3 yd, 2 s warning, 20% Nature + Weakened (the registry). '
    'Lightning Cloud 6535\'s SV 986 (an 11 yd sky bolt) on every player hit (handoff s3.10 correction 2).',
    icon=_ICON_LIGHTNING, visual=FN_LIGHTNING)

lightning_arrival_206021 = self_visual(
    206021, "Arugal's Lightning", FN_LIGHTNING,
    f'{_FN}, FN1 / FN2: the sky bolt (SV 986) on Arugal\'s Voidwalker as it steps out of the strike, cast by the '
    'voidwalker on itself (triggered), so the strike shows at the point whoever stands there.',
    icon=_ICON_LIGHTNING, school=School.NATURE)

void_pulse_206022 = spell(
    id=206022, name='Void Pulse', school=School.SHADOW, cast_time_ms=1500, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=TARGET_SRC_CASTER,
                    implicit_target_b=TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=100.0,
                    potency_excluded=_REF_FLAT_NOTE)],
    spell_icon_id=_ICON_SHADOW_BURST,
    notes=f'{_FN}, FN3: Arugal\'s Voidwalker\'s pulse, a 1.5 s cast every 3 s, then Shadow to every player within '
          '100 yd (players only): 4% of the reference row, heroic Rising Pulse +1% per landed pulse up to 10% '
          '(spell_sfk_fenrus_void_pulse; ignores caster modifiers and cannot crit, so it is exactly the reference '
          'number before the target\'s own mitigation). InterruptFlags 15 and PreventionType silence (the M5 '
          'interruptible pair): interrupt, stun or kill. Ignores LoS: "every player". Shadow Burst 28447\'s SV 45 '
          '(handoff s3.10 correction 7).',
    raw_overrides=kit_raw('Pulses void energy at every enemy.', InterruptFlags=15, PreventionType=1, DefenseType=1,
                          SpellVisualID_1=FN_VOID_PULSE, AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS),
)
scripted_by(void_pulse_206022, 'spell_sfk_fenrus_void_pulse')

shadow_fenrus_206023 = spell(
    id=206023, name='Shadow Fenrus', school=School.SHADOW, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_SHADOWFORM,
    notes=f'{_FN}, FN5 (heroic): Arugal raises Fenrus as a shadow wolf (phase two). A shown DUMMY aura on him for the '
          'rest of the fight carrying Shadowform 22917\'s SV 3619 (dark purple, translucent); cast on himself, '
          'triggered, as he rises; the script turns his melee Shadow and removes it on a reset. Dispel none.',
    raw_overrides=kit_raw('Raised by Arugal as a shadow wolf.', 'Raised by Arugal: melee attacks deal Shadow damage.',
                          instant=True, SpellVisualID_1=FN_SHADOWFORM, AttributesEx4=ATTR4_NO_CAST_LOG),
)

shadow_leap_cast_206024 = cast_bar(
    206024, 'Shadow Leap', 2000, 'Crouches, eyes fixed on the farthest prey.',
    f'{_FN}, FN6 (heroic): Fenrus\'s 2 s crouch before the leap (the emote names it). No effect, not interruptible: '
    'the registry Bait registered beside it owns the hit.',
    icon=_ICON_SHADOW_POUNCE, school=School.SHADOW)

shadow_leap_206025 = resolve_copy(
    206025, 'Shadow Leap', School.SHADOW, 'Fenrus lands on his prey.',
    f'{_FN}, FN6 (heroic): the leap\'s landing, 25% Shadow in 6 yd of the farthest player (registry Bait: the target '
    'takes no Weakened, everyone else caught does), plus the Shadow Scar rider. Also bound to '
    'spell_sfk_fenrus_shadow_leap: the hit is multiplied by (1 + 2 x the target\'s Shadow Scar stacks) before the '
    'rider adds this landing\'s stack. Shadow Pounce 52327\'s SV 8262 (the shadow puff, at the landing marker).',
    icon=_ICON_SHADOW_POUNCE, visual=FN_SHADOW_LEAP_DEPARTURE, scripts=('spell_sfk_fenrus_shadow_leap',))

shadow_scar_206026 = spell(
    id=206026, name='Shadow Scar', school=School.SHADOW, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_SHADOW_POUNCE,
    notes=f'{_FN}, FN7 (heroic): one stack on everyone a Shadow Leap lands on (the Bait\'s rider, cast by the resolve '
          'marker with Fenrus as original caster, so the stacks share one aura), for the rest of the fight. A DUMMY '
          'debuff: spell_sfk_fenrus_shadow_leap reads the stacks (+200% Shadow Leap damage taken per stack, revised '
          '2026-11-04 from a DoT) and the Bait rule baits the player with the fewest. CumulativeAura 99; the script '
          'removes it on a wipe and on his death. AURA_IS_DEBUFF + NO_IMMUNITIES, Dispel none. Aura text number-free.',
    raw_overrides=kit_raw('Shadow Leap damage taken increased by 200% per stack, stacking up to $u times.',
                          'Shadow Leap damage taken increased.', instant=True, CumulativeAura=99,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

shadow_lightning_206027 = resolve_copy(
    206027, 'Shadow Lightning', School.SHADOW, 'Lightning from Arugal\'s Focus.',
    f'{_FN}, FN8 (heroic): Arugal\'s strike under a random player in phase two, 3 yd, 1 s warning, 15% Shadow, no '
    'Weakened (Dungeon ruling 10). WP-V\'s purple sky bolt (SV 90400, patch-M; no-patch fallback Shadowfury SV 7732) '
    'on every player hit.',
    icon=_ICON_SHADOWFURY, visual=FN_SHADOW_LIGHTNING)

shadow_lightning_look_206028 = self_visual(
    206028, 'Shadow Lightning', FN_SHADOW_LIGHTNING,
    f'{_FN}, FN8 (heroic): the purple bolt at the strike point, hit or miss, cast by the strike / visual stalker '
    '300516 on itself (triggered) when that creature is declared.',
    icon=_ICON_SHADOWFURY, school=School.SHADOW)
