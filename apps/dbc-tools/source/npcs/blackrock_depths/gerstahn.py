"""
Blackrock Depths build WP-D1: High Interrogator Gerstahn (9018), "Everyone talks eventually", normal and heroic
(.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.4 rows D1, s3.5 row D1, s3.6; build spec
docs/dungeons/blackrock-depths-1-detention-block.md S1 45-228, GE1-GE7, rulings 9-12 and 88). WP-D1 owns this file
(its spells: kSpellsGerstahn 210720-210749 of modules/mod-dungeon-bosses src/BlackrockDepths/BlackrockDepthsRework.h
only; GerstahnLogic.h names the same ids).

- 9018 High Interrogator Gerstahn: boss_high_interrogator_gerstahn_rework (SmartAI off: she had no rows; the stock C++
  boss_high_interrogator_gerstahn stays registered, unbound), the build spec's normal health (140k = HealthModifier
  73.801 on the level 52 paladin class base 1,897), DamageModifier 3.5 (the stock base value), stun immunity 1972,
  INSTANCE_BIND. Heroic 230k is WP-H's override (source/world/dungeons/blackrock_depths.py). Her loot (the Prison Cell
  Key 11140 at 100%, A Crumpled Up Note 11446 at 25%) is untouched; L-1 adds the Dark Keeper Key. Mana Burn 14033 and
  Psychic Scream 13704 are retired; Shadow Word: Pain 14032 (a SpellDifficulty row: 14032 -> 15654) and Shadow Shield
  12040 are copies in the slice (rule 15).
- No boss-kit adds. The heroic pool's look rides on the shared generic stalker 300796 (the orchestrator's template;
  the script skips the look while it is not declared).

Spells. Her damage is a percent of the reference row (the tank row on the tank) times her Knowledge (GerstahnLogic.h
ScaledPct, +10% a stack): the DoTs through spell_brd_gerstahn_periodic, the sear tick through spell_brd_gerstahn_damage,
the Circle through the registry (a resolve copy). Every damage spell ignores caster modifiers (rule 2), so the
Knowledge aura raises only her melee by itself:

  210720  Doubt                GE1 the stacking debuff, no duration, not dispellable; a break at 5
  210721  Breaking Point       GE1 the high-Doubt swirl at 4 stacks (gap 6), Glimpse of Madness's SV 7433
  210722  Broken               GE1 the 2 s fear of a break, Psychic Scream's SV 247
  210723  Dread                GE1 30% / 40% Shadow over 10 s (5 ticks of 6% / 8%) on a break
  210724  Knowledge            GE1 her stack per break: +10% damage done; 5 at most on normal (the script), none heroic
  210725  Shadow Word: Pain    GE2 2% / 3% a 3 s tick for 18 s, Magic; its ticks add Doubt; a dispel clears Doubt
  210726  Mind Flay            GE3 a 3 s channel, 3 ticks of 6% / 8%, a Doubt each; a kick clears the target's Doubt
  210727  Interrogation Circle GE4 the 2.5 s cast bar (Arcane: a kicked Mind Flay locks Shadow, rule 5)
  210728  Interrogation Circle GE4 the ring's hit: resolve copy, Shadow, 15% / 25%, 3 Doubt (the script)
  210729  Mind Sear            GE5 the 5 s look on its target (a lasting aura; the script ticks)
  210730  Mind Sear            GE5 a tick on each other player within 8 yd: 3% / 5% Shadow, 1 Doubt (the script)
  210731  Shadow Shield        GE7 normal: absorbs 4,000 of every school, 50 Shadow to melee attackers; Magic
  210732  Shadow Shield        GE7 heroic: absorbs 6,500, 60 Shadow to melee attackers; Magic
  210733  Lingering Doubt      GE6 (heroic) the 5 yd pool's look on a stalker, 8 s
  210734-210749 spare.

Visual ids are WP-V-1's (._visuals; every look is unconfirmed until seen in game). Shadow Shield keeps the stock
12040's look (SV 2476, ._visuals GE_SHADOW_SHIELD).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    TARGET_UNIT_TARGET_ENEMY,
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
from ._visuals import (
    GE_SHADOW_SHIELD,
    GE_BROKEN,
    GE_DOUBT_SWIRL,
    GE_INTERROGATION_BURST,
    GE_LINGERING_DOUBT,
    GE_MIND_FLAY,
    GE_MIND_SEAR,
    GE_SHADOW_WORD_PAIN,
)

_D1 = 'Blackrock Depths build WP-D1 (High Interrogator Gerstahn)'

creature_template_columns(9018, **boss_columns(
    'boss_high_interrogator_gerstahn_rework', 73.801, damage_modifier=3.5,
))

_AURA_INTERRUPT_CHANGE_MAP = 0x00080000     # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map
_ATTR1_IS_CHANNELED = 0x00000004            # SPELL_ATTR1_IS_CHANNELED (stock Mind Flay 16568)
_CHANNEL_INTERRUPT_KICK = 0x08              # CHANNEL_INTERRUPT_FLAG_INTERRUPT: a kick stops the channel
_PREVENTION_SILENCE = 1
_DEFENSE_MAGIC = 1
_DISPEL_MAGIC = 1
_MECHANIC_FEAR = 5
_AURA_DAMAGE_SHIELD = 15                    # SPELL_AURA_DAMAGE_SHIELD (stock Shadow Shield 12040, effect 2)
_SCHOOL_MASK_ALL = 127

_PERIODIC_SCRIPT = 'spell_brd_gerstahn_periodic'
_PAIN_SCRIPT = 'spell_brd_gerstahn_shadow_word_pain'
_DAMAGE_SCRIPT = 'spell_brd_gerstahn_damage'
_SCRIPT_PCT = ('Blackrock Depths D1: a percent of reference health times her Knowledge, set by '
               'spell_brd_gerstahn_periodic / spell_brd_gerstahn_damage (GerstahnLogic.h ScaledPct, RefFlatOn)')

# Icons of the stock spells each one stands in for (stock Spell.dbc SpellIconID).
_ICON_GLIMPSE_OF_MADNESS = 48       # Glimpse of Madness 26108
_ICON_CONFUSED = 2006               # Cosmetic - Confused State Visual (Big) 47044
_ICON_PSYCHIC_SCREAM = 1488         # Psychic Scream 13704
_ICON_SHADOW_BOLT_VOLLEY = 213      # Shadow Bolt Volley 17228
_ICON_MANA_BURN = 212               # Mana Burn 14033
_ICON_SHADOW_WORD_PAIN = 234        # Shadow Word: Pain 14032
_ICON_MIND_FLAY = 548               # Mind Flay 16568
_ICON_MIND_SEAR = 2895              # Mind Sear 48045
_ICON_SHADOW_SHIELD = 207           # Shadow Shield 12040

# GerstahnLogic.h: kDoubtBreakAt, kBrokenMs, kDread*, kKnowledge*, kPain*, kFlay*, kCircleCastMs, kSear*, kShield*,
# kPoolMs. The percents are hundredths (the shown value on normal, EffectMiscValueB on heroic).
DOUBT_STACKS = 5
BROKEN_MS = 2000
DREAD_MS = 10000
DREAD_TICK_MS = 2000
DREAD_TICK = (600, 800)
KNOWLEDGE_PCT = 10
KNOWLEDGE_STACKS = 255              # the aura counter; the script caps normal at 5
PAIN_MS = 18000
PAIN_TICK_MS = 3000
PAIN_TICK = (200, 300)
FLAY_MS = 3000
FLAY_TICK_MS = 1000
FLAY_TICK = (600, 800)
CIRCLE_CAST_MS = 2500
SEAR_MS = 5000
SEAR_TICK = (300, 500)
SHIELD_MS = 30000
SHIELD_ABSORB = (4000, 6500)
SHIELD_REFLECT = (50, 60)
POOL_MS = 8000


def _aura_raw(desc: str, aura_desc: str, **more) -> dict:
    return kit_raw(desc, aura_desc, CastingTimeIndex=1, AttributesEx=ATTR1_NO_THREAT,
                   AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP, **more)


# --- GE1 Doubt, Broken, Dread, Knowledge -----------------------------------------------------------------------------

doubt_210720 = spell(
    id=210720, name='Doubt', school=School.SHADOW, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_GLIMPSE_OF_MADNESS,
    notes=f'{_D1}, GE1: the meter of the fight. A stack per Shadow Word: Pain tick that counts (every 6 s, heroic 3 '
          's), per Mind Flay tick, per Mind Sear tick on a player near its target, 3 per Interrogation Circle hit and '
          '1 per second in a Lingering Doubt pool (the script, DungeonKit::AddStacks, her as the caster). No duration '
          'and not dispellable: only a clear (a kicked Mind Flay clears its target, a dispelled Shadow Word: Pain its '
          'player) or a break removes it. At 5 the player breaks (Broken, Dread, Doubt back to 0, Knowledge +1). '
          'CumulativeAura 5. NO_IMMUNITIES: a meter, it lands through Divine Shield (the hits do not). The bots\' '
          'dispel walk ranks Shadow Word: Pain by these stacks (DispelEntry::MostStacksFirst). Dropped on a map '
          'change, removed with the fight. No look (the swirl at 4 is 210721).',
    raw_overrides=_aura_raw('Doubt builds. At 5 you break.', 'Doubting. At 5 stacks you break: a short fear and '
                            'Shadow damage, and the interrogator learns.', CumulativeAura=DOUBT_STACKS),
)

breaking_point_210721 = spell(
    id=210721, name='Breaking Point', school=School.SHADOW, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_CONFUSED,
    notes=f'{_D1}, GE1 (gap 6): the high-Doubt marker, on while the player is at 4 Doubt (the script adds it at 4 and '
          'takes it off at a clear, a break or below 4). Glimpse of Madness 26108\'s SV 7433 (V-1 GE_DOUBT_SWIRL: a '
          'lasting State, confused glyphs over the head). The healers\' first dispel, the kickers\' Mind Flay target. '
          'Not dispellable, dropped on a map change, removed with the fight.',
    raw_overrides=_aura_raw('One more and you break.', 'One more Doubt and you break.',
                            SpellVisualID_1=GE_DOUBT_SWIRL),
)

broken_210722 = spell(
    id=210722, name='Broken', school=School.SHADOW, dispel=0, mechanic=_MECHANIC_FEAR,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=BROKEN_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_FEAR, base_points=0, mechanic=_MECHANIC_FEAR,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_PSYCHIC_SCREAM,
    notes=f'{_D1}, GE1: a break, cast by her (triggered) on the player whose Doubt reached 5: a 2 s fear (the shared '
          'doc\'s limit for a penalty), fear mechanic (Fear Ward, Berserker Rage and fear immunity answer it). Dispel '
          'none (2 s). Psychic Scream 13704\'s SV 247 (V-1 GE_BROKEN, the fear skulls). Dread (210723) comes with it.',
    raw_overrides=_aura_raw('Broken by doubt.', 'Broken. Running in fear.', SpellVisualID_1=GE_BROKEN),
)


def _periodic(spell_id: int, name: str, tick: tuple[int, int], amplitude: int, duration_ms: int, *, dispel: int,
              icon: int, desc: str, aura_desc: str, notes: str, visual: int = 0, channel: bool = False,
              target: int = TARGET_UNIT_TARGET_ANY):
    """A Shadow DoT of hers: `tick` hundredths of the reference row a tick (normal, heroic in EffectMiscValueB),
    her Knowledge on top (spell_brd_gerstahn_periodic). `channel`: her interruptible channel (Mind Flay)."""
    attributes_ex = ATTR1_NO_THREAT | (_ATTR1_IS_CHANNELED if channel else 0)
    more = dict(CastingTimeIndex=1, DefenseType=_DEFENSE_MAGIC, EffectMiscValueB_1=tick[1],
                AttributesEx=attributes_ex, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG,
                AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP)
    if visual:
        more['SpellVisualID_1'] = visual
    if channel:
        more.update(ChannelInterruptFlags=_CHANNEL_INTERRUPT_KICK, InterruptFlags=0,
                    PreventionType=_PREVENTION_SILENCE)
    return spell(
        id=spell_id, name=name, school=School.SHADOW, dispel=dispel, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=tick[0],
                        die_sides=0, amplitude=amplitude, implicit_target_a=target,
                        potency_excluded=_SCRIPT_PCT)],
        spell_icon_id=icon, notes=notes, raw_overrides=kit_raw(desc, aura_desc, **more),
    )


dread_210723 = _periodic(
    210723, 'Dread', DREAD_TICK, DREAD_TICK_MS, DREAD_MS, dispel=0, icon=_ICON_SHADOW_BOLT_VOLLEY,
    desc='The dread of a broken mind.', aura_desc='Taking Shadow damage every $t1 sec.',
    notes=f'{_D1}, GE1: a break\'s damage, cast by her (triggered) with Broken: 30% (heroic 40%) of the reference row '
          'over 10 s, 5 ticks of 6% / 8% (600 / 800 hundredths), the tank row on the tank, times her Knowledge at '
          'the break. Not dispellable: the healers heal it. No look (Broken carries the fear skulls).',
)
scripted_by(dread_210723, _PERIODIC_SCRIPT)

knowledge_210724 = spell(
    id=210724, name='Knowledge', school=School.SHADOW, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE,
                    base_points=KNOWLEDGE_PCT, die_sides=0, misc_value=_SCHOOL_MASK_ALL,
                    implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Knowledge: a flat +10% damage done per stack, not a damage or heal value')],
    spell_icon_id=_ICON_MANA_BURN,
    notes=f'{_D1}, GE1: each break gives her a stack (DungeonKit::AddStacks on herself): +10% damage done, every '
          'school. Up to 5 on normal (the script\'s cap: a capped group failure below level 60), no cap on heroic '
          '(the soft enrage; CumulativeAura 255, the counter\'s limit). Her spells ignore caster modifiers, so the '
          'aura raises her melee and the scripts raise the rest by the same 10% a stack (GerstahnLogic.h '
          'KnowledgeScale). Not dispellable or stealable; removed on her death, evade and reset. No look (yell line '
          '1 is the tell).',
    raw_overrides=kit_raw('Every broken prisoner teaches the interrogator.', 'Damage done increased by $s1%.',
                          instant=True, CumulativeAura=KNOWLEDGE_STACKS, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- GE2 Shadow Word: Pain -------------------------------------------------------------------------------------------

shadow_word_pain_210725 = _periodic(
    210725, 'Shadow Word: Pain', PAIN_TICK, PAIN_TICK_MS, PAIN_MS, dispel=_DISPEL_MAGIC,
    icon=_ICON_SHADOW_WORD_PAIN, visual=GE_SHADOW_WORD_PAIN, target=TARGET_UNIT_TARGET_ENEMY,
    desc='A word of pain. Dispelling it clears the target\'s Doubt.',
    aura_desc='Taking Shadow damage every $t1 sec. Doubt builds.',
    notes=f'{_D1}, GE2: the copy of her stock 14032 (rule 15: 14032 has a SpellDifficulty row), cast by her '
          '(triggered) on a random player, the tank included, at 4 s then every 8 s (heroic 6 s). 18 s, a tick every '
          '3 s of 2% (heroic 3%) of the reference row (200 / 300 hundredths), the tank row on the tank, times her '
          'Knowledge. Every other tick adds a Doubt on normal (every 6 s, 3 a cast), every tick on heroic (6 a cast: a '
          'missed dispel breaks the player): spell_brd_gerstahn_periodic tells her AI. Magic: a dispel clears all of '
          'the player\'s Doubt (spell_brd_gerstahn_shadow_word_pain; heroic: a Lingering Doubt pool where they stood). '
          'The bots\' dispel list, the player with the most Doubt first. The stock look (SV 71).',
)
scripted_by(shadow_word_pain_210725, _PERIODIC_SCRIPT, _PAIN_SCRIPT)

# --- GE3 Mind Flay ---------------------------------------------------------------------------------------------------

mind_flay_210726 = _periodic(
    210726, 'Mind Flay', FLAY_TICK, FLAY_TICK_MS, FLAY_MS, dispel=0, icon=_ICON_MIND_FLAY, visual=GE_MIND_FLAY,
    channel=True, target=TARGET_UNIT_TARGET_ENEMY,
    desc='Flays the mind of the target. Interrupting it clears the target\'s Doubt.',
    aura_desc='Taking Shadow damage every $t1 sec. Doubt builds.',
    notes=f'{_D1}, GE3: her interruptible channel (SPELL_ATTR1_IS_CHANNELED, like Mind Flay 16568; not triggered, so '
          'the bar shows and a kick stops it): at 8 s then every 12 s (heroic 10 s) on the player with the most Doubt '
          '(random on a tie), the tank included (ruling 88). 3 s, 3 ticks of 6% (heroic 8%) of the reference row '
          '(600 / 800 hundredths), times her Knowledge, and a Doubt each (anyone at 2 or more breaks unless it is '
          'stopped). Kickable: ChannelInterruptFlags 0x08 (a kick) and PreventionType 1 (a silence); her immunity set '
          '1972 holds no INTERRUPT or SILENCE. A kick or a silence clears all of the target\'s Doubt (the AI\'s '
          'OnSpellFailed). Not dispellable (the kick is the answer). The bots\' interrupt list, priority 3. Shadow: a '
          'kick locks her Shadow school, so her must-play cast bar is Arcane (210727) and her other Shadow spells are '
          'triggered. Range 100, ignores line of sight (a corner never cancels the pick). Mind Flay 16568\'s SV 277.',
)
scripted_by(mind_flay_210726, _PERIODIC_SCRIPT)

# --- GE4 Interrogation Circle ----------------------------------------------------------------------------------------

circle_cast_210727 = cast_bar(
    210727, 'Interrogation Circle', CIRCLE_CAST_MS, 'She interrogates everyone around her.',
    f'{_D1}, GE4: the 2.5 s bar at 15 s then every 25 s (heroic 20 s), on her (emote line 2). A cast bar, not '
    'interruptible (the registry Circle beside it owns the hit, 210728). Arcane, not Shadow: a kicked Mind Flay locks '
    'her Shadow school and a Shadow bar would wait out the lockout (rule 5). It waits for the Mind Flay channel and '
    'Mind Flay waits for it (a new cast would break the channel). No look on the bar (the burst is on the hit).',
    icon=_ICON_PSYCHIC_SCREAM, school=School.ARCANE,
)

circle_hit_210728 = resolve_copy(
    210728, 'Interrogation Circle', School.SHADOW, 'The interrogation breaks the mind.',
    f'{_D1}, GE4: the ring\'s hit (the stock Psychic Scream 13704 reworked): 15% (heroic 25%) of the reference row on '
    'everyone within 10 yd of her when the bar ends, the tank included (ruling 88: the tank steps out too; its own '
    'row), times her Knowledge. No Weakened (ruling 11: Doubt is the penalty): the script adds 3 Doubt to each '
    'player hit (OnHit). Copy of the resolve spell 205006 (Shadow). Psychic Scream\'s SV 247 (V-1 '
    'GE_INTERROGATION_BURST) on every unit hit; the ring marker is the registry\'s.',
    icon=_ICON_PSYCHIC_SCREAM, visual=GE_INTERROGATION_BURST,
)

# --- GE5 Mind Sear ---------------------------------------------------------------------------------------------------

mind_sear_210729 = spell(
    id=210729, name='Mind Sear', school=School.SHADOW, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=SEAR_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_MIND_SEAR,
    notes=f'{_D1}, GE5: the sear on its target, cast by her (triggered) at 20 s then every 20 s (heroic 15 s) on a '
          'random non-tank who is not the Mind Flay target, never during the Circle\'s bar (emote line 3). 5 s; every '
          'second the script casts 210730 on every other player within 8 yd of the target and adds them a Doubt; the '
          'target takes neither (their job is to carry it away). A registry RunOut (8 yd, telegraph only) tells the '
          'bots. DEVIATION: an aura on the target, not her channel, so it never blocks Mind Flay or the kicks (S1 '
          'reads "a 5 s channel, not interruptible"; nothing can stop it either way). Mind Sear 48045\'s SV 12121 '
          '(V-1 GE_MIND_SEAR: a shadow swirl at the target\'s feet). Not dispellable, dropped on a map change.',
    raw_overrides=_aura_raw('Sears the minds of everyone near the target.', 'Your mind is seared. Allies within 8 '
                            'yards take Shadow damage and Doubt: move away from them.',
                            SpellVisualID_1=GE_MIND_SEAR),
)

mind_sear_tick_210730 = spell(
    id=210730, name='Mind Sear', school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=SEAR_TICK[0] - 1, die_sides=1,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_PCT)],
    spell_icon_id=_ICON_MIND_SEAR,
    notes=f'{_D1}, GE5: a tick of the sear on each other player within 8 yd of its target, every second for 5 s (cast '
          'by her, triggered): 3% (heroic 5%) of the reference row (300 / 500 hundredths), the tank row on the tank, '
          'times her Knowledge (spell_brd_gerstahn_damage, at launch), plus a Doubt (the script). Always hits, cannot '
          'crit, ignores line of sight and her modifiers. No look (the swirl is on the target).',
    raw_overrides=kit_raw('Sears the mind.', instant=True, InterruptFlags=0, PreventionType=0,
                          DefenseType=_DEFENSE_MAGIC, EffectMiscValueB_1=SEAR_TICK[1], AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(mind_sear_tick_210730, _DAMAGE_SCRIPT)

# --- GE7 Shadow Shield -----------------------------------------------------------------------------------------------


def _shield(spell_id: int, heroic: bool):
    absorb = SHIELD_ABSORB[1 if heroic else 0]
    reflect = SHIELD_REFLECT[1 if heroic else 0]
    more = dict(CastingTimeIndex=1, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG)
    if GE_SHADOW_SHIELD:
        more['SpellVisualID_1'] = GE_SHADOW_SHIELD
    return spell(
        id=spell_id, name='Shadow Shield', school=School.SHADOW, dispel=_DISPEL_MAGIC, mechanic=0, attributes=0,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=SHIELD_MS,
        effects=[
            Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.SCHOOL_ABSORB, base_points=absorb - 1,
                   die_sides=1, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                   potency_excluded='Shadow Shield: a boss absorb of a fixed size per difficulty (S1 GE7)'),
            Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_DAMAGE_SHIELD, base_points=reflect - 1, die_sides=1,
                   implicit_target_a=TARGET_UNIT_CASTER,
                   potency_excluded='Shadow Shield: a small fixed Shadow hit on melee attackers (S1 GE7, gap 36)'),
        ],
        spell_icon_id=_ICON_SHADOW_SHIELD,
        notes=f'{_D1}, GE7 ({"heroic" if heroic else "normal"}): the copy of her stock 12040 rescaled to the new '
              f'health (rule 15), cast by her (triggered) on herself at 8 s then every 25 s: 30 s, absorbs {absorb:,} '
              f'damage of every school and deals {reflect} Shadow to each melee attacker that hits her (the spec\'s '
              '"small Shadow hit", unset: about 1.5% of the row, a designer question). Magic: a purge or an offensive '
              'dispel is a reward (the bots\' purge list). Not scaled by DD (a custom id).',
        raw_overrides=kit_raw('Absorbs damage and harms melee attackers.', 'Absorbs damage. Melee attackers take '
                              'Shadow damage.', **more),
    )


shadow_shield_210731 = _shield(210731, False)
shadow_shield_heroic_210732 = _shield(210732, True)

# --- GE6 Lingering Doubt (heroic) ------------------------------------------------------------------------------------

lingering_doubt_210733 = spell(
    id=210733, name='Lingering Doubt', school=School.SHADOW, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=POOL_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_GLIMPSE_OF_MADNESS,
    notes=f'{_D1}, GE6 (heroic): the pool\'s look, on the shared generic stalker 300796 the script summons where a '
          'dispelled Shadow Word: Pain\'s player stood (the stalker casts it on itself, 8 s, then despawns). The '
          'shipped 6 yd shadow pool state (V-1 GE_LINGERING_DOUBT, SV 90605) under the registry\'s 5 yd ring (the '
          'exact edge). The pool itself is a telegraph-only persistent registry Zone: each second inside adds a '
          'Doubt (the script). No damage. Look only.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=GE_LINGERING_DOUBT, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
