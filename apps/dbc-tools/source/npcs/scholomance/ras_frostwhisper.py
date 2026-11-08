"""
Scholomance build WP-S4: Ras Frostwhisper (10508), normal and heroic
(.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.4 rows RF, s3.5 row S4, s3.6; build spec
docs/dungeons/scholomance-rework.md SC 1171-1230, design SC 1000-1170). WP-S4 owns this file (its spells: kSpellsRas
206170-206189 of modules/mod-dungeon-bosses src/Scholomance/ScholomanceRework.h only; RasLogic.h names the same ids).
The hard mode (S12, ras_hard_mode.py) adds its own ids 206190-206204 and fights on the same C++ AI (RasFight.h).

- 10508 Ras Frostwhisper: boss_ras_frostwhisper_rework (SmartAI off; WP-S4's SQL rev drops the five stock rows), the
  build spec's normal health (195k: HealthModifier 75.29 on the level 62 class base 2,590), DamageModifier 3.5 (the
  stock value, set explicitly: SC "Sets its own DamageModifier"), stun immunity 1972, INSTANCE_BIND. Heroic 270k is
  WP-H's override (source/world/dungeons/scholomance.py).
- 300534 Blizzard anchor: an invisible, unselectable trigger (KIT_HELPER, the SFK ward stalker's shape) that carries
  a Blizzard: the registry circle follows it, and it casts the storm's look. Fixed on normal; on heroic the AI walks it
  18 yd at 1.5 yd/s (MovePoint with its own speed). No heroic template (not a combat add).

Spells. The thaw, the Chill Nova and the Blizzard ticks deal their damage through dungeon copies of the
mod-boss-mechanics resolve spell (the registry's percent of the reference row; the combat log names the mechanic). The
Volley is a real cast whose SpellScript sets the damage at launch (DungeonKit::RefFlatOn). The rest are auras the AI
applies (Unit::AddAura), a rider, a cast bar and two looks:

  206170  Chill                 RF1 the 20-stack meter (CumulativeAura 20), a DUMMY debuff for the fight; never
                                dispellable, through immunities
  206171  Deep Chill            RF1 the look from 12 stacks: hidden (Aura of Frost 23186's SV 6778, icebarrier_state)
  206172  Warmth of the Living  RF2 the buff while warm (Glowy (Orange) 22579's SV 6591, the body glow)
  206173  Entombed              RF3 the 2 s freeze at 20 stacks: MOD_STUN, no mechanic (no trinket), through immunities
                                (Ice Tomb 16869's SV 4340)
  206174  Thaw                  RF4 the tomb's 6 yd burst: resolve copy (Frost), Ice Tomb 69675's SV 14726
  206175  Frost Mark            RF5 the 5 s mark (Frost Beacon 70126's SV 15254, the blue mark over the head)
  206176  Chill Nova            RF5 the mark's 10 yd Nova on allies: resolve copy (Frost), Chill Nova 18099's SV 4823
  206177  Chill Nova            RF5 the Nova's rider: a knockback (MiscValue 120, BasePoints 60: about 7 yd)
  206178  Blizzard              RF6 the 1.5 s cast bar
  206179  Blizzard              RF6 the 1 s tick: resolve copy (Frost), no visual (the storm is the look)
  206180  Blizzard              RF6 the storm on a fixed anchor, 12 s (Blizzard 64642's SV 13698, a dynamic object)
  206181  Blizzard              RF6 heroic: the 3 s storm a drifting anchor re-casts every 2 s
  206182  Frostbolt Volley      RF7 the 3 s interruptible cast: Frost at everyone within 40 yd (RefFlat at launch,
                                spell_scholo_ras_frostbolt_volley; heroic +3 Chill) and the stock 50% slow for 8 s
  206183-206189 spare (206190-206204 are S12's).
"""

from lib.dsl import AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import ATTR0_DO_NOT_DISPLAY, ATTR0_DO_NOT_LOG, ATTR2_CANT_CRIT, ATTR2_IGNORE_LINE_OF_SIGHT
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_INVISIBLE_STALKER,
    RF_BLIZZARD,
    RF_CHILL,
    RF_CHILL_12_STACKS,
    RF_ENTOMBED,
    RF_FROST_MARK,
    RF_FROST_NOVA,
    RF_TOMB_THAW,
    RF_WARMTH,
)

creature_template_columns(10508, **boss_columns('boss_ras_frostwhisper_rework', 75.29, DamageModifier=3.5))

_RF = 'Scholomance build WP-S4 (Ras Frostwhisper)'
_SCRIPT_EXCLUDED = 'Scholomance: a percent of reference health, set by the script (DungeonKit::RefFlat)'

_TARGET_DEST_CASTER = 18
_TARGET_SRC_CASTER = 22
_TARGET_UNIT_SRC_AREA_ENEMY = 15
_TARGET_DEST_DYNOBJ_ALLY = 29
_ATTR0_NO_AURA_CANCEL = 0x80000000
_ATTR1_NO_THREAT = 0x00000400
_ATTR3_ALWAYS_HIT = 0x00040000
_INTERRUPT_FLAGS_STANDARD = 15     # movement, pushback, interrupt, auto-attack: a kickable cast
_PREVENTION_SILENCE = 1
_DEFENSE_MAGIC = 1

_ICON_CHILLED = 181                # Chilled 6136
_ICON_AURA_OF_FROST = 182          # Aura of Frost 23186
_ICON_GLOWY_ORANGE = 1479          # Glowy (Orange) 22579
_ICON_ICE_TOMB = 35                # Ice Tomb 16869
_ICON_CHILL_NOVA = 193             # Chill Nova 18099
_ICON_FROST_BEACON = 3410          # Frost Beacon 70126
_ICON_BLIZZARD = 285               # Blizzard 64642
_ICON_FROSTBOLT_VOLLEY = 188       # Frostbolt Volley 8398
_SV_FROSTBOLT_VOLLEY = 13          # Frostbolt Volley 8398 (his own, the bolt missile)

# The Nova's knockback (RasLogic.h kNovaKnockMisc / kNovaKnockBasePoints).
_NOVA_KNOCK_MISC = 120
_NOVA_KNOCK_BASE_POINTS = 60

# --- 300534 Blizzard anchor ------------------------------------------------------------------------------------------
blizzard_anchor_300534 = creature_template(
    300534, 'Blizzard', **{**KIT_HELPER, 'minlevel': 62, 'maxlevel': 62, 'rank': 0, 'unit_class': 1, 'type': 10,
                           'flags_extra': 0x40 | 0x80, 'ScriptName': ''},
)
creature_model(300534, display_id=DISPLAY_INVISIBLE_STALKER)

# --- RF1 Chill / RF2 Warmth -----------------------------------------------------------------------------------------

chill_206170 = spell(
    id=206170, name='Chill', school=School.FROST, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_CHILLED,
    notes=f'{_RF}, RF1: the fight\'s meter on every player, a DUMMY debuff stacking to 20 (CumulativeAura), for the '
          'fight (removed on his death, evade and reset, and on the player\'s death). Ras applies and changes it '
          '(DungeonKit::AddStacks, caster Ras): +1 a second while cold; warm, nothing on normal and +1 every 3 s on '
          'heroic; +2 a Blizzard tick, +5 a Chill Nova, heroic +3 a Volley or a thaw. It never melts: at 20 the '
          'player freezes (206173) and wakes with none. Dispel none and NO_IMMUNITIES. The bots\' self-keyed RunOut '
          '(17+) and the warm Stack\'s eligibility (below 17) read its stacks. Chilled 6136\'s SV 675 (the head mist).',
    raw_overrides=kit_raw('Stacks up to $u times. At $u stacks you freeze solid.', 'Freezing. Stay near your allies.',
                          CastingTimeIndex=1, CumulativeAura=20, SpellVisualID_1=RF_CHILL,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

deep_chill_206171 = spell(
    id=206171, name='Deep Chill', school=School.FROST, dispel=0, mechanic=0,
    attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_AURA_OF_FROST,
    notes=f'{_RF}, RF1: the look from 12 Chill stacks (VISUALS-REPORT, Ras: the two-step swap is the cheapest tell): '
          'a hidden DUMMY aura the AI adds (the player on itself) and removes with the meter. Aura of Frost 23186\'s '
          'SV 6778 (icebarrier_state).',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=RF_CHILL_12_STACKS, AttributesEx4=ATTR4_NO_CAST_LOG),
)

warmth_206172 = spell(
    id=206172, name='Warmth of the Living', school=School.FIRE, dispel=0, mechanic=0,
    attributes=_ATTR0_NO_AURA_CANCEL | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_GLOWY_ORANGE,
    notes=f'{_RF}, RF2: the buff while two or more living, not entombed allies stand within 8 yd (the AI checks it '
          'every second and adds or removes it, the player on itself). Normal: no Chill builds while it is up; '
          'heroic: a third of the cold rate. Not cancellable (the next second would put it back). Glowy (Orange) '
          '22579\'s SV 6591 (the body glow).',
    raw_overrides=kit_raw('Two or more allies close by keep you warm.', 'Warm. Chill builds slowly or not at all.',
                          instant=True, SpellVisualID_1=RF_WARMTH, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- RF3 Entombed / RF4 Thaw -----------------------------------------------------------------------------------------

entombed_206173 = spell(
    id=206173, name='Entombed', school=School.FROST, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=2000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_ICE_TOMB,
    notes=f'{_RF}, RF3: the freeze at 20 Chill: a 2 s stun (the shared 2 s limit), applied by the AI with Ras as the '
          'caster, after the meter empties. No mechanic (no trinket or Freedom breaks it), Dispel none, '
          'NO_IMMUNITIES. As it ends the tomb bursts (the registry thaw, 206174). Ice Tomb 16869\'s SV 4340 '
          '(icebarrier_state). S12\'s permanent tomb (the hard mode\'s OnFreeze) holds the player with this aura '
          'made permanent (RasFight.h).',
    raw_overrides=kit_raw('Frozen solid.', 'Frozen solid.', CastingTimeIndex=1, SpellVisualID_1=RF_ENTOMBED,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

thaw_206174 = resolve_copy(
    206174, 'Thaw', School.FROST, 'The tomb bursts.',
    f'{_RF}, RF4: the tomb\'s burst as it breaks, 6 yd around the frozen player (spared: a shape anchored on a player '
    'never hits it): 30% normal / 45% heroic of the non-tank row + 1 Weakened (ruling 21); heroic +3 Chill on everyone '
    'hit (the registry OnHit). Copy of the resolve spell 205001 (Frost). Ice Tomb 69675\'s SV 14726 (a frost nova and '
    'Xplosion_Frost_Impact at the tomb, the impact on every player hit).',
    icon=_ICON_ICE_TOMB, visual=RF_TOMB_THAW,
)

# --- RF5 Frost Mark --------------------------------------------------------------------------------------------------

frost_mark_206175 = spell(
    id=206175, name='Frost Mark', school=School.FROST, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=5000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_FROST_BEACON,
    notes=f'{_RF}, RF5: the 5 s mark on a random non-tank (never a tank), cast by Ras (triggered) with emote line 1; '
          'the registry RunOut (10 yd) registered beside it owns the Nova (206176). Dispel none. Frost Beacon 70126\'s '
          'SV 15254 (catmark_blue over the head).',
    raw_overrides=kit_raw('Marked by the frost of the grave.', 'A Chill Nova bursts on you. Run out of the group.',
                          CastingTimeIndex=1, SpellVisualID_1=RF_FROST_MARK, AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

chill_nova_206176 = resolve_copy(
    206176, 'Chill Nova', School.FROST, 'Frost bursts from the marked player.',
    f'{_RF}, RF5: the Nova on the marked player as the mark ends: allies within 10 yd take 40% normal / 55% heroic '
    'of the non-tank row, +5 Chill (the registry OnHit) and the knockback rider 206177; the marked player is not hit '
    '(a RunOut never hits its carrier); no Weakened (SC: the Chill is the cost). Copy of the resolve spell 205001 '
    '(Frost). Chill Nova 18099\'s SV 4823 (Frost_Nova_area at the mark, the head state on every player hit).',
    icon=_ICON_CHILL_NOVA, visual=RF_FROST_NOVA,
)

chill_nova_knockback_206177 = spell(
    id=206177, name='Chill Nova', school=School.FROST, attributes=ATTR0_DO_NOT_DISPLAY, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.KNOCK_BACK, base_points=_NOVA_KNOCK_BASE_POINTS, die_sides=0,
                    misc_value=_NOVA_KNOCK_MISC, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_CHILL_NOVA,
    notes=f'{_RF}, RF5: the Nova\'s rider on every ally it hits, cast by the registry marker on the mark (Ras the '
          'original caster), so the push is away from the marked player. Stock Chill Nova 18099\'s knockback '
          '(MiscValue 400, BasePoints 99: 40 yd/s) would throw a player out of the study; MiscValue 120 and BasePoints '
          '60 (12 yd/s out, 6 yd/s up) carry about 7 yd. No damage (206176 has it).',
    raw_overrides=kit_raw('Knocks back.', instant=True, InterruptFlags=0, PreventionType=0,
                          AttributesEx=_ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=_ATTR3_ALWAYS_HIT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- RF6 Blizzard ----------------------------------------------------------------------------------------------------

blizzard_cast_206178 = cast_bar(
    206178, 'Blizzard', 1500, 'Calls down a blizzard.',
    f'{_RF}, RF6: the 1.5 s cast bar while the registry circles (6 yd, on a Blizzard anchor 300534 under each picked '
    'player) warn; then each storm is live for 12 s. No visual on the bar (the storm\'s own look starts when it goes '
    'live).',
    icon=_ICON_BLIZZARD, school=School.FROST)

blizzard_tick_206179 = resolve_copy(
    206179, 'Blizzard', School.FROST, 'Ice and wind.',
    f'{_RF}, RF6: the storm\'s 1 s tick, 8% normal / 12% heroic of the non-tank row and +2 Chill (the registry OnHit) '
    'on everyone inside the 6 yd circle; a persistent zone, so no Weakened. Copy of the resolve spell 205001 (Frost). '
    'No visual (a tick every second; the falling ice of 206180 / 206181 is the look).',
    icon=_ICON_BLIZZARD,
)


def _blizzard_look(spell_id: int, duration_ms: int, label: str):
    return spell(
        id=spell_id, name='Blizzard', school=School.FROST, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=duration_ms,
        effects=[Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=0, implicit_target_a=_TARGET_DEST_CASTER,
                        implicit_target_b=_TARGET_DEST_DYNOBJ_ALLY, apply_aura=AuraType.DUMMY, radius_yards=6.0)],
        spell_icon_id=_ICON_BLIZZARD,
        notes=f'{_RF}, RF6 {label}: visual only, the storm at the Blizzard anchor\'s feet (TARGET_DEST_CASTER / '
              'TARGET_DEST_DYNOBJ_ALLY, the Deadmines Fish Stew puddle\'s shape: its DUMMY aura reaches nobody). '
              'Blizzard 64642\'s SV 13698 (the persistent SummonGround_Blizzard, scaled by the 6 yd radius). The '
              'registry circle on the anchor (206179) owns the ticks.',
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=RF_BLIZZARD, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


blizzard_look_206180 = _blizzard_look(206180, 12000, 'normal (a fixed storm, 12 s)')
blizzard_drift_206181 = _blizzard_look(
    206181, 3000, 'heroic (the drifting anchor re-casts it every 2 s, so the storm follows it in 3 s pieces)')

# --- RF7 Frostbolt Volley --------------------------------------------------------------------------------------------

frostbolt_volley_206182 = spell(
    id=206182, name='Frostbolt Volley', school=School.FROST, dispel=0, mechanic=0, cast_time_ms=3000, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=8000,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=_TARGET_SRC_CASTER,
                    implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=40.0,
                    potency_excluded=_SCRIPT_EXCLUDED),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DECREASE_SPEED, base_points=-51,
                    implicit_target_a=_TARGET_SRC_CASTER, implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY,
                    radius_yards=40.0)],
    spell_icon_id=_ICON_FROSTBOLT_VOLLEY,
    notes=f'{_RF}, RF7: the stock Frostbolt Volley 8398 reworked (never the stock id): a 3 s cast (stock 2 s) at '
          'everyone within 40 yd (the study and the Kormok hall; stock 20 yd), interruptible (InterruptFlags 15, '
          'PreventionType silence; the descriptor\'s interrupt list, every 20 s). Frost: 15% normal / 40% heroic of '
          'the reference row, set at launch by spell_scholo_ras_frostbolt_volley (RefFlatOn, so the target\'s '
          'defensives count), which also adds +3 Chill on heroic when it lands. The stock slow: -50% movement for 8 s '
          '(BasePoints -51 + DieSides 1). Ignores caster modifiers and cannot crit (the number is the reference). '
          'Stock SV 13 and missile speed 28.',
    raw_overrides=kit_raw('Hurls frostbolts at every enemy nearby, slowing them.', 'Movement slowed by $s2%.',
                          InterruptFlags=_INTERRUPT_FLAGS_STANDARD, PreventionType=_PREVENTION_SILENCE,
                          DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=_SV_FROSTBOLT_VOLLEY, Speed=28.0,
                          AttributesEx2=ATTR2_CANT_CRIT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS),
)
scripted_by(frostbolt_volley_206182, 'spell_scholo_ras_frostbolt_volley')
