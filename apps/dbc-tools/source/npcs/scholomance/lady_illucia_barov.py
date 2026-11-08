"""
Scholomance build WP-S10: Lady Illucia Barov (10502), normal and heroic
(.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.4 rows IB, s3.5 row S10, s3.6; build spec
docs/dungeons/scholomance-rework.md SC 2695-2741, design SC 2548-2694). WP-S10 owns this file (its spells:
kSpellsIllucia 206315-206329 of modules/mod-dungeon-bosses src/Scholomance/ScholomanceRework.h only; IlluciaLogic.h
names the same ids).

- 10502 Lady Illucia Barov: boss_lady_illucia_barov_rework (SmartAI off; WP-S10's SQL rev drops the five stock rows),
  the build spec's normal health (160k: HealthModifier 65.52 on the level 60 class base 2,442), DamageModifier 3.5 (the
  stock value: SC "Sets its own DamageModifier", the live 6.5 is a mod-progression leftover), stun immunity 1972,
  INSTANCE_BIND. Heroic 250k is WP-H's override (source/world/dungeons/scholomance.py). No boss-kit units (SC: the four
  Risen Bonewarders stay trash).
- Her Graduate Examiner (S13, 300554) runs the same C++ in examiner mode (npc_sc_examiner_illucia, 80k by script);
  WP-S13 declares the entry. The Shadow Vault's solo lesson (detention) is C++ too and uses 206316 / 206317.

Spells. The Foresight markers, the Memory trail and the Fear's end marker deal their damage through dungeon copies of
the mod-boss-mechanics resolve spell (the registry's percent of the reference row; the combat log names the mechanic).
The Fear is a real interruptible cast whose aura script runs the straight flight. The rest is a cast bar and a debuff:

  206315  Foresight          IB1 the 1.5 s cast bar (not interruptible: the registry owns the hit)
  206316  Foresight          IB1 the read debuff on each read player for the chain, cast on them (triggered) so its
                             look plays: Mind Vision 2096's SV 4839 (the eyes over the head)
  206317  Foresight          IB1 a 4 yd marker's hit: resolve copy (Shadow), Shadow Crash 62659's SV 13255; 30% / 40%
                             and Weakened (ruling 20); the solo lesson's markers too (15% / 25% and Weakened)
  206318  Memory             IB2 (heroic) the trail's 1 s tick: resolve copy (Shadow), Mind Sear 48045's SV 12121
  206319  Fear               IB3 the stock Fear 12542 changed (never the stock id): a 1.5 s interruptible cast, a 2 s
                             Magic fear (Fear 4 s before), the run scripted straight away from her
                             (spell_scholo_illucia_fear); Psychic Horror 64044's SV 13757
  206320  Fear               IB3 the end marker's hit: resolve copy (Shadow), Mind Blast 8092's SV 3057; 15% / 50%, no
                             Weakened (ruling 21)
  206321-206329 spare.

Stock Shadow Shock 19460 and Curse of Agony 18266 are cast as they are (DD scales them on heroic); Silence 15487 is
retired from her kit.
"""

from lib.dsl import AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import ATTR2_IGNORE_LINE_OF_SIGHT, TARGET_UNIT_TARGET_ENEMY
from lib.dsl.registry import creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_B,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import IL_FEAR, IL_FORESIGHT_IMPACT, IL_FORESIGHT_IMPACT_ALT, IL_MEMORY_TRAIL, IL_THE_READ

# Held back until wave B binds this boss (_common.py BIND_WAVE_B; R-A S-11): stock until then.
if BIND_WAVE_B:
    creature_template_columns(10502, **boss_columns('boss_lady_illucia_barov_rework', 65.52, DamageModifier=3.5))

_IB = 'Scholomance build WP-S10 (Lady Illucia Barov)'

_DISPEL_MAGIC = 1
_MECHANIC_FEAR = 5
_INTERRUPT_FLAGS_STANDARD = 15     # movement, pushback, interrupt, auto-attack: a kickable cast
_PREVENTION_SILENCE = 1
_DEFENSE_MAGIC = 1
_ATTR1_NO_THREAT = 0x00000400

_ICON_MIND_VISION = 502            # Mind Vision 2096
_ICON_SHADOW_CRASH = 1939          # Shadow Crash 62659
_ICON_MIND_SEAR = 2895             # Mind Sear 48045
_ICON_FEAR = 98                    # Fear 12542 (her stock Fear)

# IlluciaLogic.h ReadAuraMs(5): the cast plus the heroic chain (the AI removes it when the chain ends).
_READ_MS = 9000
_FEAR_CAST_MS = 1500
_FEAR_MS = 2000

# --- IB1 Foresight ---------------------------------------------------------------------------------------------------

foresight_cast_206315 = cast_bar(
    206315, 'Foresight', 1500, 'Reads a mind and strikes where it will go.',
    f'{_IB}, IB1: the 1.5 s cast bar (yell line 1 names the first read player); as it ends the chain\'s first 4 yd '
    'marker lands on each read player 1.5 s later, then one where they will be every 1.5 s (the registry circles, '
    '206317). Not interruptible (cast_bar): the chains are the registry\'s.',
    icon=_ICON_MIND_VISION, school=School.SHADOW)

foresight_read_206316 = spell(
    id=206316, name='Foresight', school=School.SHADOW, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_READ_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_MIND_VISION,
    notes=f'{_IB}, IB1: the read player\'s debuff for the chain: cast (triggered) by Illucia, her examiner or the '
          'Shadow Vault lesson\'s stalker on each read player as the read starts, removed when the chain ends (at most '
          'the cast plus five markers, 9 s). A DUMMY aura: the tell only. Dispel none and NO_IMMUNITIES (a dispel '
          'would hide the tell, not stop the chain). Mind Vision 2096\'s SV 4839 (eyesofbeast_impact_head) plays '
          'as it lands.',
    raw_overrides=kit_raw('She knows where you will go.', 'She knows where you will go. Keep changing direction.',
                          CastingTimeIndex=1, SpellVisualID_1=IL_THE_READ, AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

foresight_206317 = resolve_copy(
    206317, 'Foresight', School.SHADOW, 'She saw you coming.',
    f'{_IB}, IB1: a Foresight marker\'s hit, 4 yd: 30% normal / 40% heroic of the non-tank row and Weakened '
    '(ruling 20, both difficulties); each marker is its own failure. The Shadow Vault\'s solo lesson uses it at '
    '15% / 25% and Weakened. Copy of the resolve spell 205001 (Shadow). Shadow Crash 62659\'s SV 13255 '
    '(Shadow_ImpactDD_Uber_Chest and a shadow nova on whoever is hit).',
    icon=_ICON_SHADOW_CRASH, visual=IL_FORESIGHT_IMPACT,
)

# --- IB2 Memory trail (heroic) ---------------------------------------------------------------------------------------

memory_206318 = resolve_copy(
    206318, 'Memory', School.SHADOW, 'She remembers where you have been.',
    f'{_IB}, IB2 (heroic): the Memory trail\'s 1 s tick: a read player\'s path during their chain lingers in 4 yd '
    'pieces, 3 yd wide, for 4 s (DungeonKit::Linger, no slow): 10% of the non-tank row a second on everyone inside; a '
    'persistent zone, so no Weakened. Copy of the resolve spell 205001 (Shadow). Mind Sear 48045\'s SV 12121 '
    '(priest_mindshear) on whoever is hit (Shadow Trap 73530\'s SV 15489, the doc\'s first pick, draws nothing).',
    icon=_ICON_MIND_SEAR, visual=IL_MEMORY_TRAIL,
)

# --- IB3 Fear --------------------------------------------------------------------------------------------------------

fear_206319 = spell(
    id=206319, name='Fear', school=School.SHADOW, dispel=_DISPEL_MAGIC, mechanic=_MECHANIC_FEAR,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=_FEAR_CAST_MS, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=40.0, duration_ms=_FEAR_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_FEAR, base_points=0,
                    mechanic=_MECHANIC_FEAR, implicit_target_a=TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_FEAR,
    notes=f'{_IB}, IB3: her stock Fear 12542 changed (never the stock id): a 1.5 s cast on a random non-tank who is '
          'not being read (stock: a random player within 20 yd), interruptible (InterruptFlags 15, PreventionType '
          'silence; the descriptor\'s interrupt list, every 20 s); a 2 s fear (the shared loss of control limit; '
          'stock 4 s), mechanic fear and Magic (the dispel list, urgent: Fear Ward, Berserker Rage and fear '
          'immunities still work). spell_scholo_illucia_fear replaces the random flight with a straight run away from '
          'her at the player\'s run speed (at most 20 yd, stopped by walls) and registers a 4 yd marker at the run\'s '
          'end that lands as the fear ends (206320); a dispel stops the run where the player stands. Psychic Horror '
          '64044\'s SV 13757 (Fear_Impact_Chest, then Fear_State_Head while it lasts).',
    raw_overrides=kit_raw('Fills the target with dread: they run straight away for $d.', 'Running in terror.',
                          InterruptFlags=_INTERRUPT_FLAGS_STANDARD, PreventionType=_PREVENTION_SILENCE,
                          DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=IL_FEAR),
)
scripted_by(fear_206319, 'spell_scholo_illucia_fear')

fear_end_206320 = resolve_copy(
    206320, 'Fear', School.SHADOW, 'The end of the run was foreseen.',
    f'{_IB}, IB3: the 4 yd marker at the end of the terrified player\'s straight run, landing as the 2 s fear ends: '
    '15% normal / 50% heroic of the non-tank row (her examiner: 50%); no Weakened (ruling 21: the terrified player '
    'could not dodge; heroic expects the kick or the dispel). Copy of the resolve spell 205001 (Shadow). Mind Blast '
    '8092\'s SV 3057 (MindBlast_Head) on whoever is hit.',
    icon=_ICON_FEAR, visual=IL_FORESIGHT_IMPACT_ALT,
)
