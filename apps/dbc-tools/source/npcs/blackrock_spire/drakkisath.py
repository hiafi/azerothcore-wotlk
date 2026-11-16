"""
Blackrock Spire build WP-B14: General Drakkisath (10363), "Only the Branded May Pass", normal and heroic
(.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.4 rows DR, s3.5 row B14, s3.6, s3.8 NM 13;
build spec docs/dungeons/blackrock-spire-rework.md SP 3990-4082, design SP 3699-3989, rulings 63, 68-71, 73). WP-B14
owns this file (its spells: kSpellsDrakkisath 210520-210559 of modules/mod-dungeon-bosses
src/BlackrockSpire/BlackrockSpireRework.h; DrakkisathLogic.h names the same ids; no creature of its own). The engine
side is src/BlackrockSpire/boss_drakkisath_rework.cpp; his texts 0-8 and the Elite Guards' dropped SmartAI rows are the
core SQL rev rev_drakkisath_blackrock_spire.sql (line 9 is the hard mode's, WP-B15). The hard mode (the General's
Army) is WP-B15's drakkisath_hard_mode.py.

- 10363 General Drakkisath: bound to boss_drakkisath_rework (SmartAI off; the stock C++ script boss_drakkisath stays
  registered, unbound by this data: Conflagration, Pierce Armor and the plain Cleave are retired), normal 260k at 5
  players (HealthModifier 80.321 on the level 62 warrior class base 3,237; the flex scaler multiplies it at the pull),
  stun immune (1972), INSTANCE_BIND, DamageModifier 3.5 (the stock value; the live 10 is a mod-progression leftover).
  Heroic 310k is WP-H's; the hard mode's 240k is B15's script. His loot rows are L-2's.
- 10814 Chromatic Elite Guard (DR1, DR8; boss-kit only, his two formation spawns): bound to
  npc_brs_chromatic_elite_guard (SmartAI off; the rev drops its three rows, Knockdown 16790 retired, Mortal Strike 15708
  and Strike 15580 kept in C++), level 60 (stock 59-60), 25,000 at 5 players (HealthModifier 8.191349 on the level 60
  warrior base 3,052; heroic 32,000 is WP-H's, the hard mode's 30,000 B15's), DamageModifier 3.5 (the base SQL value;
  the live 9.1 is a leftover). Its stock immunity row stays (stunnable: stops are an add tool).

Spells (looks from ._visuals, WP-V-2's DR_* and SV_BRAND_* picks; every look unconfirmed until seen in game):

  210520  Searing Brand        DR2 the 12 s DUMMY debuff on the bearer (V-2's orange Odyn rune, SV 90613)
  210521  Collapsing Brand     DR3 the 12 s DUMMY debuff on the bearer (the yellow rune, SV 90614)
  210522  Searing Brand        DR2 the bearer's tick: 2% (the kit's percent spell, Fire)
  210523  Searing Flare        DR2 each other player within 4 yd of a bearer: 6% a tick (Fire)
  210524  Collapsing Brand     DR3 the bearer alone: 8% a tick (Fire)
  210525  Collapsing Brand     DR3 the bearer with someone within 4 yd: 1.6% a tick (Fire)
  210526  Thunderclap          DR5 the 2 s wind-up bar (Physical, not interruptible)
  210527  Thunderclap          DR5 the ring's hit (resolve copy, Physical): 25%, Weakened, the tank too
  210528  Thunderclap          DR5 the 3 s slow rider (-50% movement)
  210529  Thunderclap          DR5 the clap on him (Thunderclap 15548's SV 145)
  210530  Flamestrike          DR6 normal: the 2.5 s bar (Fire, not interruptible)
  210531  Flamestrike          DR6 heroic: the 2.5 s bar (Fire, interruptible: the expected kick)
  210532  Flamestrike          DR6 a circle's hit (resolve copy, Fire): 30%, Weakened
  210533  Flamestrike          DR6 the burning patch's tick (resolve copy, Fire): 5% a second, the tank too
  210534  Flamestrike          DR6 the patch's look: a 5 yd dynamic object for 15 s (Flamestrike 16419's SV 10383)
  210535  Blackblade Sweep     DR7 the 1.5 s bar, the sword drawn back (Physical)
  210536  Blackblade Sweep     DR7 the sweep's hit (resolve copy, Physical): 35%, Weakened, the tank too
  210537  Blackblade Sweep     DR7 his swing (Wide Swipe 6749's SV 399, a self DUMMY: no aura, no StunSwirl)
  210538  Seared Flesh         DR9 10 players: a stack on his target, +10% damage taken from him (DUMMY + script)
  210539-210559 spare.

Tooltips are number-free where the number is a reference percent (Systems.md s10).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    self_visual,
    standing_in_it,
)
from lib.dsl.registry import creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_2,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DR_FLAMESTRIKE,
    DR_SEARED_FLESH,
    DR_SWEEP,
    DR_THUNDERCLAP,
    SV_BRAND_COLLAPSING,
    SV_BRAND_SEARING,
)

_B14 = 'Blackrock Spire build WP-B14 (General Drakkisath)'
_SCRIPT_REFFLAT = ('Blackrock Spire: a percent of reference health in hundredths, set at launch by the kit\'s '
                   'spell_dungeon_refflat_damage (DungeonKit::RefFlatOn)')
_REFFLAT = 'spell_dungeon_refflat_damage'

# --- shared bits -----------------------------------------------------------------------------------------------------

_TARGET_DEST_DYNOBJ_ENEMY = 28
_TARGET_FLAG_DEST_LOCATION = 0x40
# AURA_INTERRUPT_FLAG_CHANGE_MAP (SpellDefines.h): a debuff never outlives the instance on the character.
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_DEFENSE_MAGIC = 1
_PREVENTION_SILENCE = 1
_INTERRUPT_FLAGS_KICKABLE = 15

# Icons of the stock spells the looks come from (Spell.dbc, the working copy).
_ICON_BURNING_BRAND = 12            # Burning Brand 29618 (and Mark of Flames 15128)
_ICON_THUNDERCLAP = 199             # Thunderclap 15548
_ICON_FLAMESTRIKE = 37              # Flamestrike 16419
_ICON_WIDE_SWIPE = 371              # Wide Swipe 6749
_ICON_IMMOLATION = 937              # Immolation 40148

# DrakkisathLogic.h: kBrandMs, kSearing*/kCollapsing* (hundredths), kThunderclap*, kFlamestrike*, kSweepCastMs,
# kSearedFlesh*.
_BRAND_MS = 12000
_SEARING_BEARER = 200               # kSearingBearerPct 2
_SEARING_OTHERS = 600               # kSearingOthersPct 6
_COLLAPSING_ALONE = 800             # kCollapsingAlonePct 8
_COLLAPSING_PAIRED = 160            # kCollapsingPairedPct 1.6
_THUNDERCLAP_CAST_MS = 2000
_THUNDERCLAP_SLOW_MS = 3000
_THUNDERCLAP_SLOW_PCT = 50
_FLAMESTRIKE_CAST_MS = 2500
_FLAMESTRIKE_RADIUS = 5.0
_FLAMESTRIKE_PATCH_MS = 15000
_SWEEP_CAST_MS = 1500
_SEARED_FLESH_MS = 15000
_SEARED_FLESH_MAX = 255             # "no cap" (the aura's own limit)

# --- the bindings (wave 2) -------------------------------------------------------------------------------------------

_GUARD_HEALTH_MODIFIER = 8.191349   # ceil(3,052 x 8.191349) = 25,000 at level 60

if BIND_WAVE_2:
    creature_template_columns(10363, **boss_columns(
        'boss_drakkisath_rework', 80.321, damage_modifier=3.5,
    ))
    creature_template_columns(
        10814, ScriptName='npc_brs_chromatic_elite_guard', AIName='', minlevel=60, maxlevel=60,
        HealthModifier=_GUARD_HEALTH_MODIFIER, DamageModifier=3.5,
    )

# --- DR2 / DR3 the brands --------------------------------------------------------------------------------------------


def _brand(spell_id: int, name: str, visual: int, desc: str, aura_desc: str, notes: str):
    """A brand on its bearer: a 12 s DUMMY debuff (the look and the bots' tell; the script ticks)."""
    return spell(
        id=spell_id, name=name, school=School.FIRE, dispel=0, mechanic=0,
        attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_BRAND_MS,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=_ICON_BURNING_BRAND, notes=notes,
        raw_overrides=kit_raw(desc, aura_desc, CastingTimeIndex=1, SpellVisualID_1=visual,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                              AttributesEx3=ATTR3_ALWAYS_HIT, AttributesEx4=ATTR4_NO_CAST_LOG,
                              AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )


def _tick(spell_id: int, name: str, hundredths: int, desc: str, notes: str):
    """A brand's tick: the kit's percent spell (Fire), `hundredths` of the reference row (the tank its own row)."""
    s = spell(
        id=spell_id, name=name, school=School.FIRE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=hundredths - 1, die_sides=1,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_REFFLAT)],
        spell_icon_id=_ICON_BURNING_BRAND, notes=notes,
        raw_overrides=kit_raw(desc, instant=True, InterruptFlags=0, PreventionType=0, DefenseType=_DEFENSE_MAGIC,
                              EffectMiscValueB_1=hundredths, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                              AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )
    scripted_by(s, _REFFLAT)
    return s


searing_brand_210520 = _brand(
    210520, 'Searing Brand', SV_BRAND_SEARING, 'Drakkisath burns his mark into you. It flares on everyone near you.',
    'Burning. Allies within 4 yards are seared too: stand alone.',
    f'{_B14}, DR2: one of his two brands, cast by him (triggered) on a non-tank every 20 s from 15 s (emote line 1; '
    'normal: one kind at random, 1 bearer at 5 players, 2 at 6 or more; heroic: one of each kind per cast). 12 s; '
    'nothing for its first 2 s (the mercy window), then every second the script casts 210522 on the bearer and 210523 '
    'on every other player within 4 yd (a held registry RunOut from the bearer tells the bots to keep away). DUMMY: '
    'the look and the tell. Not dispellable, dropped on a map change, removed with the fight. V-2\'s orange Odyn runic '
    'brand (SV 90613, a rune ring under the bearer; stock runner-up DR_SEARING_BRAND_ALT 1946).',
)

collapsing_brand_210521 = _brand(
    210521, 'Collapsing Brand', SV_BRAND_COLLAPSING, 'Drakkisath burns his mark into you. It burns far less with '
    'someone at your side.', 'Burning. Much less while an ally stands within 4 yards: find a partner.',
    f'{_B14}, DR3: the other brand, on the same cast (emote line 2). 12 s; nothing for 2 s, then every second the '
    'script casts 210524 (nobody within 4 yd) or 210525 (someone within 4 yd, 80% less) on the bearer. The script '
    'picks a partner (another Collapsing bearer first, else the nearest player with no brand, a non-tank before the '
    'tank) and registers a held Stack on that partner that only the bearer must reach (the bots\' pair-up). Not '
    'dispellable, dropped on a map change, removed with the fight. V-2\'s yellow Odyn runic brand (SV 90614; stock '
    'runner-up DR_COLLAPSING_BRAND_ALT 6764).',
)

searing_burn_210522 = _tick(
    210522, 'Searing Brand', _SEARING_BEARER, 'The brand burns.',
    f'{_B14}, DR2: the bearer\'s tick, every second from 3 s to 12 s (10 ticks): 2% of the reference row (200 '
    'hundredths). Cast by him (triggered) on the bearer.',
)

searing_flare_210523 = _tick(
    210523, 'Searing Flare', _SEARING_OTHERS, 'A brand nearby flares.',
    f'{_B14}, DR2: the flare on each other player within 4 yd of a Searing bearer at a tick: 6% of the reference row '
    '(600 hundredths; the tank its own row). Cast by him (triggered) on each of them.',
)

collapsing_burn_210524 = _tick(
    210524, 'Collapsing Brand', _COLLAPSING_ALONE, 'The brand collapses inward.',
    f'{_B14}, DR3: the bearer\'s tick with nobody within 4 yd: 8% of the reference row (800 hundredths).',
)

collapsing_shared_210525 = _tick(
    210525, 'Collapsing Brand', _COLLAPSING_PAIRED, 'The brand smolders, shared.',
    f'{_B14}, DR3: the bearer\'s tick with another player within 4 yd: 80% less, 1.6% of the reference row (160 '
    'hundredths).',
)

# --- DR5 Thunderclap -------------------------------------------------------------------------------------------------

thunderclap_bar_210526 = cast_bar(
    210526, 'Thunderclap', _THUNDERCLAP_CAST_MS, 'Drakkisath raises his blade to strike the ground.',
    f'{_B14}, DR5: the 2 s wind-up, 8 s after the pull, then every 15 s (his cast queue). DUMMY on the caster, not '
    'interruptible, Physical: a kick on the heroic Flamestrike (Fire) never locks it. The registry\'s 10 yd ring on '
    'him owns the hit.',
    icon=_ICON_THUNDERCLAP,
)

thunderclap_210527 = resolve_copy(
    210527, 'Thunderclap', School.NORMAL, 'Drakkisath strikes the ground, hurting and slowing everyone near him.',
    f'{_B14}, DR5: the ring\'s hit, a 10 yd circle on him: 25% of the reference row to everyone inside, the tank too '
    '(its own row, ruling 51), 1 Weakened and 210528. Copy of the mod-boss-mechanics resolve spell 205001 (Physical), '
    'no look (his clap is 210529).',
    icon=_ICON_THUNDERCLAP,
)

thunderclap_slow_210528 = standing_in_it(
    210528, f'{_B14}, DR5: the clap\'s rider on every player it hits: movement -50% for 3 s (SP: "a 3 s slow"; the '
    'amount is the build\'s). Removed with the fight.',
    name='Thunderclap', slow_pct=_THUNDERCLAP_SLOW_PCT, duration_ms=_THUNDERCLAP_SLOW_MS,
    desc='Movement slowed. Lasts $d.', aura_desc='Movement slowed.', icon=_ICON_THUNDERCLAP,
)

thunderclap_look_210529 = self_visual(
    210529, 'Thunderclap', DR_THUNDERCLAP,
    f'{_B14}, DR5: his clap, cast on himself (triggered) as the ring resolves. Thunderclap 15548\'s SV 145 (a 6.9 yd '
    'ground crack and blue hands; the ring marker shows the 10 yd).',
    icon=_ICON_THUNDERCLAP,
)

# --- DR6 Flamestrike -------------------------------------------------------------------------------------------------

flamestrike_bar_210530 = cast_bar(
    210530, 'Flamestrike', _FLAMESTRIKE_CAST_MS, 'Drakkisath calls down pillars of flame.',
    f'{_B14}, DR6 (normal): the 2.5 s bar, 6 s after the pull, then every 15 s (his cast queue). DUMMY on the caster, '
    'not interruptible (a kick must not look as if it stopped the circles the registry lands), Fire. Flamestrike '
    '16419\'s SV 10383 (its flame state on the caster through the bar).',
    icon=_ICON_FLAMESTRIKE, visual=DR_FLAMESTRIKE, school=School.FIRE,
)

flamestrike_bar_heroic_210531 = spell(
    id=210531, name='Flamestrike', school=School.FIRE, cast_time_ms=_FLAMESTRIKE_CAST_MS, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_FLAMESTRIKE,
    notes=f'{_B14}, DR6 (heroic): the expected interrupt (the descriptor\'s list, priority 3). DUMMY on the caster, '
          '2.5 s, interruptible and silence-preventable (InterruptFlags 15, PreventionType silence; his immunity set '
          '1972 holds no interrupt or silence). Fire, a school his other bars do not use (Thunderclap and the Sweep '
          'are Physical), so a kick locks nothing else. Uninterrupted, a 5 yd circle lands under every player (the '
          'registry); kicked, the script cancels them all (OnSpellFailed). Flamestrike 16419\'s SV 10383.',
    raw_overrides=kit_raw('Drakkisath calls down pillars of flame under everyone. Interrupt him!',
                          InterruptFlags=_INTERRUPT_FLAGS_KICKABLE, PreventionType=_PREVENTION_SILENCE,
                          DefenseType=_DEFENSE_MAGIC, AttributesEx4=ATTR4_NO_CAST_LOG,
                          SpellVisualID_1=DR_FLAMESTRIKE),
)

flamestrike_210532 = resolve_copy(
    210532, 'Flamestrike', School.FIRE, 'A pillar of flame erupts.',
    f'{_B14}, DR6: a circle\'s hit, 5 yd at a player\'s spot taken at the bar\'s start (normal: 2 random non-tanks, '
    '4 at 6 or more; heroic: every player, uninterrupted): 30% of the reference row (the tank its own row) and 1 '
    'Weakened. Copy of the resolve spell 205001 (Fire), no look (the patch 210534 shows the landing).',
    icon=_ICON_FLAMESTRIKE,
)

flamestrike_burn_210533 = resolve_copy(
    210533, 'Flamestrike', School.FIRE, 'The ground burns.',
    f'{_B14}, DR6: the burning patch a circle leaves, 5 yd for 15 s: 5% of the reference row a second to everyone '
    'inside, the tank too, no Weakened (DungeonKit::Linger, no slow rider). Copy of the resolve spell 205001 (Fire), '
    'no look of its own (210534).',
    icon=_ICON_FLAMESTRIKE,
)

flamestrike_patch_210534 = spell(
    id=210534, name='Flamestrike', school=School.FIRE, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=_FLAMESTRIKE_PATCH_MS,
    effects=[Effect(type=EffectType.PERSISTENT_AREA_AURA, apply_aura=AuraType.DUMMY,
                    implicit_target_a=_TARGET_DEST_DYNOBJ_ENEMY, radius_yards=_FLAMESTRIKE_RADIUS)],
    spell_icon_id=_ICON_FLAMESTRIKE,
    notes=f'{_B14}, DR6: the burning patch\'s look, visual only. He casts it (triggered) at each circle\'s spot as it '
          'lands (CastSpell(x, y, z)): a dynamic object of 5 yd for 15 s with Flamestrike 16419\'s PersistentArea '
          'fire spiral (SV 10383; whether the client scales it to 5 yd is untested, V-2). Its DUMMY aura reaches '
          'nobody harmful: the registry\'s persistent circle (210533) owns the ticks. The script removes them when '
          'the attempt ends (Unit::RemoveDynObject).',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=DR_FLAMESTRIKE, Targets=_TARGET_FLAG_DEST_LOCATION,
                          InterruptFlags=0, PreventionType=0, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- DR7 Blackblade Sweep --------------------------------------------------------------------------------------------

sweep_bar_210535 = cast_bar(
    210535, 'Blackblade Sweep', _SWEEP_CAST_MS, 'Drakkisath draws back the Blackblade.',
    f'{_B14}, DR7: the 1.5 s wind-up, the sword drawn back, 5 s after the pull, then every 12 s (his cast queue). '
    'His facing locks at its start toward his target (the cone is a point-anchored registry Zone). DUMMY on the '
    'caster, not interruptible, Physical.',
    icon=_ICON_WIDE_SWIPE,
)

blackblade_sweep_210536 = resolve_copy(
    210536, 'Blackblade Sweep', School.NORMAL, 'Drakkisath sweeps the Blackblade before him.',
    f'{_B14}, DR7: the sweep\'s hit, 180 degrees and 10 yd in front of him (no tank exemption: the tank steps to his '
    'flank, ruling 51): 35% of the reference row (the tank its own row) and 1 Weakened. Copy of the resolve spell '
    '205001 (Physical), no look (his swing is 210537).',
    icon=_ICON_WIDE_SWIPE,
)

sweep_look_210537 = self_visual(
    210537, 'Blackblade Sweep', DR_SWEEP,
    f'{_B14}, DR7: his swing, cast on himself (triggered) as the sweep resolves. Wide Swipe 6749\'s SV 399 (anim, '
    'sound and a shake; a self DUMMY applies no aura, so its StunSwirl state never shows).',
    icon=_ICON_WIDE_SWIPE,
)

# --- DR9 Seared Flesh (10 players) -----------------------------------------------------------------------------------

seared_flesh_210538 = spell(
    id=210538, name='Seared Flesh', school=School.FIRE, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_SEARED_FLESH_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_IMMOLATION,
    notes=f'{_B14}, DR9 (10 players only, rulings 63, 70, 71): his blade adds a stack to his target 8 s after the '
          'pull, then every 8 s (DungeonKit::AddStacks with him as caster: the bots\' taunt swap counts his stacks), '
          'no cap (CumulativeAura 255). +10% damage taken from him per stack: his DamageDealt (the aura is a DUMMY; '
          'every school of his, see the B14 report\'s designer question). 15 s, each stack refreshing it: the user\'s '
          'taunt rule (2026-11-15) lets a tank taunt only once its own stacks are gone, so it ends before the other '
          'tank reaches the swap count (3 strikes: 24 s) and outlasts one strike (8 s). It holds (does not run down) '
          'on his current target while he cannot strike it (a wind-up, a hard mode hold, out of reach), so the gap '
          'between strikes is 8 s whatever the downtime. The bots swap at 3. Not dispellable, dropped on a map '
          'change, removed with the fight. Immolation 40148\'s charred embers state (SV 9112).',
    raw_overrides=kit_raw('Damage taken from General Drakkisath increased.', 'Damage taken from General Drakkisath '
                          'increased by 10% per stack.', CastingTimeIndex=1, CumulativeAura=_SEARED_FLESH_MAX,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=ATTR3_ALWAYS_HIT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP, SpellVisualID_1=DR_SEARED_FLESH),
)
