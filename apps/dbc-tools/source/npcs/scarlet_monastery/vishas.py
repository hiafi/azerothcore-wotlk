"""
Scarlet Monastery build WP-D1: Interrogator Vishas (3983), "an interrogation you are losing", normal and heroic
(.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.5 row D1, s3.6; build spec
docs/dungeons/scarlet-monastery-1-graveyard.md "Interrogator Vishas", VI1-VI4). WP-D1 owns this file (its spells:
kSpellsVishas 212320-212349 of modules/mod-dungeon-bosses src/ScarletMonastery/ScarletMonasteryRework.h only;
VishasLogic.h names the same ids).

- 3983 Interrogator Vishas: boss_interrogator_vishas_rework (SmartAI off: WP-S0's rev drops rows 0-5; the C++ keeps
  the kill line and Vorrel's death line), the build spec's normal health (40k = HealthModifier 45.045 on the level 32
  paladin class base 888), DamageModifier 2.0 (the stock base value), stun immunity 1972, INSTANCE_BIND. Heroic 280k
  is WP-H's override (source/world/dungeons/scarlet_monastery.py). Shadow Word: Pain 2767 (a live spell_dbc player
  override) is retired as his cast: Pain is a copy in the slice (rule 15). He starts unarmed and takes his stock Hot
  Iron Poker 5532 at 70% (the script; creature_equip_template is untouched).
- No boss-kit adds, no new creatures.

Spells. His damage is a percent of the reference row (the tank row on the tank): the DoTs through the kit's
spell_dungeon_refflat_periodic (hundredths in the value, heroic in EffectMiscValueB), the accomplice pulse and the
Branding Iron through the registry (resolve copies), the Torment shares through the script (SplitShares, the base
point). Every damage spell ignores caster modifiers (rule 2):

  212320  Interrogation        VI1 the 1.5 s bar (not interruptible)
  212321  Interrogation        VI1 the 6 s debuff on the carrier: 4% a second (healer work), not dispellable
  212322  Accomplice           VI1 the pulse on anyone within 8 yd of a carrier: 12% / 20% (resolve copy, Shadow)
  212323  Branding Iron        VI2 the 2 s bar (not interruptible)
  212324  Branding Iron        VI2 the cone's hit: 35% / 45% and Weakened (resolve copy, Fire)
  212325  Pain                 VI3 the copy of Shadow Word: Pain: 2% / 4% a 3 s tick for 18 s, Magic
  212326  Torment              VI4 (heroic) the 9.5 s channeled beam (1.5 s on, then 8 ticks), not interruptible
  212327  Torment              VI4 one share of a second's 20% split (the script's base point)
  212328-212349 spare.

Visual ids are WP-V's (._visuals; every look is unconfirmed until seen in game).
"""

from lib.dsl import AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR1_NO_THREAT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    RESOLVE_RAW,
    TARGET_UNIT_TARGET_ENEMY,
)
from lib.dsl.registry import creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    VI_BRANDING_IRON,
    VI_BRANDING_IRON_ALT,
    VI_CONFESSION_MARK,
    VI_INTERROGATION_CAST,
    VI_PAIN,
    VI_TORMENT,
)

_D1 = 'Scarlet Monastery build WP-D1 (Interrogator Vishas)'

creature_template_columns(3983, **boss_columns(
    'boss_interrogator_vishas_rework', 45.045, damage_modifier=2.0,
))

_AURA_INTERRUPT_CHANGE_MAP = 0x00080000     # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map
_ATTR1_IS_CHANNELED = 0x00000004            # SPELL_ATTR1_IS_CHANNELED (stock Drain Soul 32862)
_DEFENSE_MAGIC = 1
_DISPEL_MAGIC = 1

_REFFLAT_PERIODIC = 'spell_dungeon_refflat_periodic'
_SCRIPT_PCT = ('Scarlet Monastery D1: a percent of reference health (hundredths in the value, heroic in '
               'EffectMiscValueB), set by the kit\'s spell_dungeon_refflat_periodic (DungeonKit::RefFlatOn)')
_SCRIPT_SHARE = ('Scarlet Monastery D1: one share of Torment\'s split, the script\'s base point '
                 '(DungeonKit::SplitShares)')

# Icons of the stock spells each one stands in for (stock Spell.dbc SpellIconID).
_ICON_INTERROGATION = 1986      # Interrogation 52805
_ICON_BURNING_BRAND = 12        # Burning Brand 29618
_ICON_SHADOW_WORD_PAIN = 234    # Shadow Word: Pain 2767
_ICON_DRAIN_SOUL = 113          # Drain Soul 32862

# VishasLogic.h: kInterrogationCastMs, kInterrogationMs, kInterrogationTickMs, kInterrogationPct, kBrandCastMs,
# kPainMs, kPainTickMs, kPainPct, TormentChannelMs(). The percents are hundredths (normal, heroic).
INTERROGATION_CAST_MS = 1500
INTERROGATION_MS = 6000
INTERROGATION_TICK_MS = 1000
INTERROGATION_TICK = (400, 400)
BRAND_CAST_MS = 2000
PAIN_MS = 18000
PAIN_TICK_MS = 3000
PAIN_TICK = (200, 400)
TORMENT_CHANNEL_MS = 9500


def _periodic(spell_id: int, name: str, tick: tuple[int, int], amplitude: int, duration_ms: int, *, dispel: int,
              icon: int, visual: int, desc: str, aura_desc: str, notes: str, target: int, attributes: int):
    """A Shadow DoT of his: `tick` hundredths of the reference row a tick (normal; heroic in EffectMiscValueB), the
    tank row on the tank, through the kit's spell_dungeon_refflat_periodic."""
    s = spell(
        id=spell_id, name=name, school=School.SHADOW, dispel=dispel, mechanic=0, attributes=attributes,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=tick[0],
                        die_sides=0, amplitude=amplitude, implicit_target_a=target, potency_excluded=_SCRIPT_PCT)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, aura_desc, CastingTimeIndex=1, DefenseType=_DEFENSE_MAGIC,
                              EffectMiscValueB_1=tick[1], AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                              AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP,
                              SpellVisualID_1=visual),
    )
    scripted_by(s, _REFFLAT_PERIODIC)
    return s


# --- VI1 Interrogation -----------------------------------------------------------------------------------------------

interrogation_cast_212320 = cast_bar(
    212320, 'Interrogation', INTERROGATION_CAST_MS, 'Tell me everything!',
    f'{_D1}, VI1: the 1.5 s bar at 6 s, then every 18 s (phase 3: 14 s), on him. Not interruptible (InterruptFlags 0, '
    'PreventionType 0: he has nothing that makes sense to stop, GY "No expected interrupt"); the registry RunOut '
    'registered with it owns the pulses (212322). When it ends: emote line 4 and the debuff (212321) on each carrier '
    '(a random non-tank; heroic phase 3: two). Interrogation 52805\'s cast look (V VI_INTERROGATION_CAST, SV 11627; '
    'its impact is a grey ash puff, not used).',
    icon=_ICON_INTERROGATION, visual=VI_INTERROGATION_CAST, school=School.SHADOW,
)

interrogation_212321 = _periodic(
    212321, 'Interrogation', INTERROGATION_TICK, INTERROGATION_TICK_MS, INTERROGATION_MS, dispel=0,
    icon=_ICON_INTERROGATION, visual=VI_CONFESSION_MARK, target=TARGET_UNIT_TARGET_ANY,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES,
    desc='Confess!', aura_desc='Interrogated. Taking Shadow damage every $t1 sec. Anyone within 8 yards is an '
                               'accomplice: walk away from the group.',
    notes=f'{_D1}, VI1: the carrier\'s debuff, cast by him (triggered) when the bar ends: 6 s, 4% of the reference '
          'row a second (400 hundredths, heroic the same), the unavoidable healer work. The carrier is never the '
          'tank (the carried-spread exemption). Not dispellable (the walk is the answer), NO_IMMUNITIES (the marker '
          'lands through Divine Shield; the ticks do not). The lasting keening skull over the head (V '
          'VI_CONFESSION_MARK, the shipped SV 90506) with the registry\'s red 8 yd ring. Leaving the map drops it.',
)

accomplice_212322 = resolve_copy(
    212322, 'Accomplice', School.SHADOW, 'Too close to the interrogated: an accomplice.',
    f'{_D1}, VI1: the pulse every 2 s (three, the first 2 s after the bar) on everyone within 8 yd of a carrier, the '
    'tank included (its own row): 12% (heroic 20%) of the reference row, through the registry RunOut (a lasting '
    'RunOut: Persistent). A repeating splash, so no Weakened (L7). Copy of the resolve spell 205001 (Shadow). No look '
    '(the ring and the skull are the tell).',
    icon=_ICON_INTERROGATION,
)

# --- VI2 Branding Iron -----------------------------------------------------------------------------------------------

branding_iron_cast_212323 = cast_bar(
    212323, 'Branding Iron', BRAND_CAST_MS, 'He swings a red-hot branding iron.',
    f'{_D1}, VI2: the 2 s bar from 70% (3 s after the yell, then every 12 s; phase 3: 10 s), on him while he turns '
    'to a random player (the tank included). Not interruptible. Burning Brand 29618\'s fire hands (V '
    'VI_BRANDING_IRON, SV 1946) while he swings; the 15 yd cone is the registry\'s marker.',
    icon=_ICON_BURNING_BRAND, visual=VI_BRANDING_IRON, school=School.FIRE,
)

branding_iron_212324 = resolve_copy(
    212324, 'Branding Iron', School.FIRE, 'Branded by a red-hot iron.',
    f'{_D1}, VI2: the cone\'s hit, a 90 degree, 15 yd cone fixed toward the picked player\'s spot at the bar\'s start: '
    '35% (heroic 45%) of the reference row (the tank row on the tank) plus Weakened (every difficulty), through the '
    'registry Zone. Copy of the resolve spell 205003 (Fire). High Executor\'s Branding Iron Impact 48614\'s head '
    'impact (V VI_BRANDING_IRON_ALT, SV 10800) on every player hit.',
    icon=_ICON_BURNING_BRAND, visual=VI_BRANDING_IRON_ALT,
)

# --- VI3 Pain --------------------------------------------------------------------------------------------------------

pain_212325 = _periodic(
    212325, 'Pain', PAIN_TICK, PAIN_TICK_MS, PAIN_MS, dispel=_DISPEL_MAGIC, icon=_ICON_SHADOW_WORD_PAIN,
    visual=VI_PAIN, target=TARGET_UNIT_TARGET_ENEMY, attributes=ATTR0_AURA_IS_DEBUFF,
    desc='A word of pain.', aura_desc='Taking Shadow damage every $t1 sec.',
    notes=f'{_D1}, VI3: his own copy of Shadow Word: Pain 2767 (rule 15: 2767 carries the priest rework\'s live '
          'spell_dbc override), cast by him (triggered) on a random player, the tank included, at 3-7 s then every '
          '10-14 s. 18 s, a tick every 3 s of 2% (heroic 4%) of the reference row (200 / 400 hundredths), the tank row '
          'on the tank. Magic: a dispel shortens the healer\'s work (the reward; the bots\' dispel list). The stock '
          'look (V VI_PAIN, SV 71).',
)

# --- VI4 Torment (heroic) --------------------------------------------------------------------------------------------

torment_212326 = spell(
    id=212326, name='Torment', school=School.SHADOW, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=TORMENT_CHANNEL_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_DRAIN_SOUL,
    notes=f'{_D1}, VI4 (heroic): his channeled beam to a random player, the tank included (emote line 6), at 10 s then '
          'every 25 s; he stands still and does not melee while he channels, and his other tools wait. 9.5 s: the '
          'registry line Soak\'s 1.5 s warning, then 8 ticks a second; the script splits 20% of the non-tank row '
          'among everyone on the line each tick (212327). SPELL_ATTR1_IS_CHANNELED (like Drain Soul 32862), not '
          'triggered (the bar shows), not interruptible (ChannelInterruptFlags 0, InterruptFlags 0, PreventionType 0: '
          'no expected interrupt). Range 100, ignores line of sight. A dummy aura on the target (the beam\'s end), '
          'not dispellable; removed with the fight. Drain Soul 32862\'s purple beam (V VI_TORMENT, SV 788; never Soul '
          'Drain\'s SV 9364, which draws no beam).',
    raw_overrides=kit_raw('Torments the target. Everyone standing in the beam shares the pain.',
                          'Tormented. Everyone in the beam between you and the interrogator shares the damage.',
                          CastingTimeIndex=1, InterruptFlags=0, ChannelInterruptFlags=0, PreventionType=0,
                          AttributesEx=_ATTR1_IS_CHANNELED | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP, SpellVisualID_1=VI_TORMENT),
)

torment_share_212327 = spell(
    id=212327, name='Torment', school=School.SHADOW, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_SHARE)],
    spell_icon_id=_ICON_DRAIN_SOUL,
    notes=f'{_D1}, VI4 (heroic): one share of a Torment tick, cast by him (triggered) on the target and every player '
          'on the line (the registry\'s hitbox) each second: 20% of the non-tank row split evenly '
          '(DungeonKit::SplitShares, the base point; DieSides 0: exact). Alone the target takes 160% over the beam '
          '(hub ruling 12); with the tank and one more, about 6.7% a second each. Damage over time, so no Weakened. '
          'The resolve attribute set (no threat, always hits, cannot crit, ignores line of sight and his modifiers). '
          'No look (the beam is the tell).',
    raw_overrides=kit_raw('The torment, shared.', **RESOLVE_RAW),
)
