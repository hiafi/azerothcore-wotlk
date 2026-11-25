"""
Ragefire Chasm build WP-D2: Jergosh the Invoker (11518)
(.agents/plans/ragefire-chasm-build/ragefire-chasm-build.HANDOFF.md s3.5 row D2, s3.6, s3.8, s3.10, s3.12, s7 #21, #29,
#35; build spec docs/dungeons/ragefire-chasm-rework.md "Jergosh the Invoker", JR1-JR5, ruling 15). WP-D2 owns this file
(its spells: kSpellsJergosh 213580-213609 of modules/mod-dungeon-bosses src/RagefireChasm/RagefireChasmRework.h only;
JergoshLogic.h names the same ids; the texts are the core SQL rev rev_jergosh_ragefire_chasm.sql).

- 11518 Jergosh the Invoker: boss_jergosh_rework (SmartAI off: rev_skeleton_ragefire_chasm.sql drops its rows), the
  build spec's normal health (21,490 = HealthModifier 70 on the level 16 mage base 307), the stock DamageModifier (until
  T), stun immunity 1972, INSTANCE_BIND with both assist flags, detection range 12 (s7 #12 A). Heroic 335,352 is WP-H's
  override (source/world/dungeons/ragefire_chasm.py).
- 300986 Soul Wisp (JR5, heroic): npc_rfc_soul_wisp, the Wisp display 12432 at scale 1.75, not selectable, not
  attackable; the boss's CrawlPickups moves and removes it. No heroic template.
- The offering patch is the S0 stalker 300988 wearing 213588.

Spells. The rings' hit is a dungeon copy of the mod-boss-mechanics resolve spell; every other damage is a plain effect
whose amount is the script's base point (DungeonKit::RefFlatOn, the tank row on the tank, times his Tithe; Immolate's
normal values flat; DieSides 0 so the base point is the amount) and every one ignores caster modifiers (rule 2: the
Tithe aura never counts twice):

  213580  Immolate         JR1 the kickable 2 s cast: effect 1 the hit, effect 2 the Magic DoT (21 s, 3 s ticks; SV 46)
  213581  Conflagrate      JR2 the 2.5 s bar, Arcane, never interruptible (rule 25)
  213582  Conflagrate      JR2 the rings on everyone else (resolve copy, Fire; SV 5199)
  213583  Conflagrate      JR2 the bearer's own burst (script, Fire; SV 5199)
  213584  Drain Soul       JR4 heroic: the kickable 3 s channel, a dummy aura on its owner (SV 12656)
  213585  Soul Tear        JR4 heroic: the completed channel's hit (script, Shadow; SV 7180)
  213586  Soul-sick        JR5 heroic: 25% less healing taken, 30 s (SV 561)
  213587  Tithe            JR5 heroic: +15% damage dealt a stack, for the fight (SV 11821)
  213588  Offering Spot    JR5 heroic: the stalker's shadow patch (shipped SV 90601)
  213589  The Hungerer's Tithe  JR5 heroic: the look on him as a soul arrives (SV 7180)
  213590-213609 spare.

Immolate (Fire) and Drain Soul (Shadow) are the only interruptible casts. A kick locks the cast's school (2 s: the
script shortens the kick's own lockout) and refuses every non-triggered cast of it (rule 25 as corrected), so
Conflagrate's bar is Arcane. Curse of Weakness 18267 stays a stock cast (JR3). Retired as a cast: Immolate 20800 (the
copy above). Looks are copied, never the stock spells.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
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
    DISPLAY_SOUL_WISP,
    JR_CONFLAGRATION_BURST,
    JR_DRAIN_SOUL,
    JR_IMMOLATE,
    JR_OFFERING_SPOT,
    JR_SOUL_SICK,
    JR_SOUL_TEAR,
    JR_TITHE,
    SOUL_WISP_SCALE,
)

creature_template_columns(11518, **boss_columns(
    'boss_jergosh_rework', 70.0, damage_modifier=1.95,
))

wisp_300986 = creature_template(
    300986, 'Soul Wisp', **{**KIT_HELPER, 'minlevel': 16, 'maxlevel': 16, 'rank': 0, 'unit_class': 1, 'type': 10,
                            'ScriptName': 'npc_rfc_soul_wisp'},
)
creature_model(300986, display_id=DISPLAY_SOUL_WISP, scale=SOUL_WISP_SCALE)

_D2 = 'Ragefire Chasm build WP-D2 (Jergosh the Invoker)'
_SCRIPT_BP = ('Ragefire Chasm Jergosh: the script\'s base point (a percent of reference health, DungeonKit::RefFlatOn, '
              'times his Tithe; Immolate on normal: the build spec\'s flat stock value)')

# --- constants (RagefireChasmRework.h namespace Jergosh; lib/test_ragefire_chasm_jergosh.py pins each) ----------------

IMMOLATE_CAST_MS = 2000         # kImmolateCastMs
IMMOLATE_MS = 21000             # kImmolateDurationMs
IMMOLATE_TICK_MS = 3000         # kImmolateTickMs
CONFLAGRATE_CAST_MS = 2500      # kConflagrateCastMs
DRAIN_SOUL_MS = 3000            # kDrainSoulChannelMs
SOUL_SICK_MS = 30000            # kSoulSickMs
SOUL_SICK_PCT = 25              # kSoulSickHealingPct
TITHE_PCT = 15                  # kTithePct
TITHE_MAX_STACKS = 99           # JergoshLogic.h kTitheMaxStacks: out of reach (no cap, ruling 15)

# Stock icons (Spell.dbc SpellIconID of the named spell; read from the stock DBC 2026-11-24).
_ICON_IMMOLATE = 31             # Immolate 20800
_ICON_CONFLAGRATE = 12          # Conflagrate 17962
_ICON_DRAIN_SOUL = 113          # Drain Soul 1120
_ICON_CURSE = 543               # Curse of Weakness 18267

_TARGET_UNIT_TARGET_ENEMY = 6
_DEFENSE_MAGIC = 1
_DISPEL_MAGIC = 1
_PREVENTION_SILENCE = 1
_INTERRUPT_FLAGS_KICKABLE = 15              # the whitemane.py recipe: movement, pushback, interrupt, auto-attack
_CHANNEL_INTERRUPT_KICK = 0x08              # SpellDefines.h CHANNEL_INTERRUPT_FLAG_INTERRUPT
_ATTR1_IS_CHANNELED = 0x00000004
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000     # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map
_SCHOOL_MASK_ALL = 127
_ATTR2_DO_NOT_RESET_COMBAT_TIMERS = 0x00020000  # SharedDefines.h: the cast leaves his swing timer alone


def _script_hit(spell_id: int, name: str, school: School, desc: str, notes: str, *, icon: int, visual: int):
    """A hit whose amount the script sets as the base point (CastSpellExtraArgs::AddSpellBP0; DieSides 0, so the amount
    is exact): triggered, always hits, cannot crit, ignores LoS and the caster's modifiers, DmgClass magic."""
    return spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_BP)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, instant=True, InterruptFlags=0, PreventionType=0, DefenseType=_DEFENSE_MAGIC,
                              SpellVisualID_1=visual,
                              AttributesEx=ATTR1_NO_THREAT | ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                              AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- JR1 Immolate ----------------------------------------------------------------------------------------------------

immolate_213580 = spell(
    id=213580, name='Immolate', school=School.FIRE, dispel=_DISPEL_MAGIC, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=IMMOLATE_CAST_MS, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=100.0, duration_ms=IMMOLATE_MS,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_BP),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=0, die_sides=0,
                    amplitude=IMMOLATE_TICK_MS, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
                    potency_excluded=_SCRIPT_BP)],
    spell_icon_id=_ICON_IMMOLATE,
    notes=f'{_D2}, JR1: 3 s, then every 3 s: a 2 s cast on a random player, the tank included, never one already '
          'burning, none while three burn. Cast for real (the bar shows), interruptible and silence-preventable '
          '(InterruptFlags 15, PreventionType silence; his immunity set 1972 holds neither): the descriptor\'s '
          'interrupt list, a reward. Normal: the stock values of 20800 (56, then 16 a tick: 7 ticks of 3 s); heroic '
          '5% of the reference row and 5% a tick, times his Tithe (both effects are the script\'s base points). '
          'Magic: on heroic the bots\' dispel list. The burn is the fuel of JR2 (its ring is the registry\'s '
          'SelfTrigger on this aura). Heroic: whoever another\'s ring hits catches the same DoT (a triggered cast, '
          'the hit\'s base point 0). Ignores line of sight, is not reflected or redirected. Leaving the map drops '
          'it; removed from everyone on a reset, evade or his death. Does not reset his swing (a cast every 3 s '
          'would cost him about a third of them). Immolate 20800\'s SV 46.',
    raw_overrides=kit_raw('Burns an enemy, then inflicts additional Fire damage every $t2 sec. for $d.',
                          'Burning: Fire damage every $t2 sec. Conflagrate will burst this fire around you.',
                          InterruptFlags=_INTERRUPT_FLAGS_KICKABLE, PreventionType=_PREVENTION_SILENCE,
                          DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=JR_IMMOLATE,
                          AttributesEx=ATTR1_NO_THREAT | ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                          AttributesEx2=(ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT
                                         | _ATTR2_DO_NOT_RESET_COMBAT_TIMERS),
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- JR2 Conflagrate -------------------------------------------------------------------------------------------------

conflagrate_cast_213581 = cast_bar(
    213581, 'Conflagrate', CONFLAGRATE_CAST_MS, 'The flames on his victims flare.',
    f'{_D2}, JR2: the 2.5 s bar on himself, 16 s then every 20 s, with emote line 1; the registry Spread registered '
    'beside it owns the rings (5 yd, heroic 6 yd, one on every burning player, for the whole bar). Not interruptible '
    '(InterruptFlags 0, PreventionType 0) and Arcane: a kicked Immolate (Fire) or Drain Soul (Shadow) locks that '
    'school, never this bar (rule 25). The damage is Fire (213582, 213583). SV 46\'s fire hands.',
    icon=_ICON_CONFLAGRATE, visual=JR_IMMOLATE, school=School.ARCANE,
)

conflagrate_213582 = resolve_copy(
    213582, 'Conflagrate', School.FIRE, 'Caught in the burst of another\'s flames.',
    f'{_D2}, JR2: at the bar\'s end each burn bursts: 35% (heroic 45%) of the reference row (the tank row on the tank) '
    'and Weakened on everyone in its ring but the bearer, tank included, through the registry Spread. A player in two '
    'rings takes both. Copy of the resolve spell 205003 (Fire). Conflagrate 17962\'s SV 5199 on every player hit.',
    icon=_ICON_CONFLAGRATE, visual=JR_CONFLAGRATION_BURST,
)

conflagrate_bearer_213583 = _script_hit(
    213583, 'Conflagrate', School.FIRE, 'The flames burst.',
    f'{_D2}, JR2: the bearer\'s own burst as their burn is consumed (the registry Spread skips its carrier): 15% '
    '(heroic 20%) of the reference row, the tank row on the tank (the script\'s base point). No Weakened: a done job.',
    icon=_ICON_CONFLAGRATE, visual=JR_CONFLAGRATION_BURST,
)

# --- JR4 Drain Soul (heroic) -----------------------------------------------------------------------------------------

drain_soul_213584 = spell(
    id=213584, name='Drain Soul', school=School.SHADOW, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=DRAIN_SOUL_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_DRAIN_SOUL,
    notes=f'{_D2}, JR4 (heroic): 10 s, then every 20 s: a real 3 s channel on a random player, the tank included, '
          'emote line 2. Kickable (ChannelInterruptFlags interrupt, PreventionType silence; first on the interrupt '
          'list): nothing happens then. Only the completed channel (OnChannelFinished) tears the soul out: Soul Tear '
          '213585 and the wisp. A death or an immunity on its owner ends it with nothing. Ignores line of sight, 100 '
          'yd, not reflected or redirected. The dummy aura carries Drain Soul 1120\'s victim state (SV 12656: the '
          'channel beam and the funnel); leaving the map drops it.',
    raw_overrides=kit_raw('Tears at an enemy\'s soul.', 'Your soul is being torn out. Interrupt Jergosh!',
                          instant=True, InterruptFlags=0, ChannelInterruptFlags=_CHANNEL_INTERRUPT_KICK,
                          PreventionType=_PREVENTION_SILENCE, SpellVisualID_1=JR_DRAIN_SOUL,
                          AttributesEx=_ATTR1_IS_CHANNELED | ATTR1_NO_THREAT | ATTR1_NO_REDIRECTION
                          | ATTR1_NO_REFLECTION,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

soul_tear_213585 = _script_hit(
    213585, 'Soul Tear', School.SHADOW, 'Tears a soul out.',
    f'{_D2}, JR4 (heroic): the completed Drain Soul on its owner: 25% of the reference row, the tank row on the tank '
    '(the script\'s base point), as the soul wisp 300986 leaves them. Spirit Burst\'s SV 7180.',
    icon=_ICON_DRAIN_SOUL, visual=JR_SOUL_TEAR,
)

# --- JR5 The Hungerer's Tithe (heroic) -------------------------------------------------------------------------------

soul_sick_213586 = spell(
    id=213586, name='Soul-sick', school=School.SHADOW, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=SOUL_SICK_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_HEALING_PCT, base_points=-SOUL_SICK_PCT,
                    die_sides=0, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded='Soul-sick: a flat -25% healing received, not a damage or heal value')],
    spell_icon_id=_ICON_CURSE,
    notes=f'{_D2}, JR5 (heroic): the owner of an eaten soul, 30 s (triggered): 25% less healing taken. Not '
          'dispellable (the penalty). Removed on his reset, evade or death, and on a map change. Cripple\'s chest '
          'state (SV 561).',
    raw_overrides=kit_raw('The soul is gone.', 'Healing received reduced by 25%.', instant=True,
                          SpellVisualID_1=JR_SOUL_SICK, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

tithe_213587 = spell(
    id=213587, name='Tithe', school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=TITHE_PCT,
                    die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_DRAIN_SOUL,
    notes=f'{_D2}, JR5 (heroic): a stack for every eaten soul (DungeonKit::AddStacks), for the fight, no cap (ruling '
          '15; CumulativeAura 99 is out of reach at a soul every 20 s). +15% damage dealt a stack: the aura raises his '
          'melee (every school); his own percent hits ignore caster modifiers, so the script multiplies them by the '
          'stacks (TitheFactor). Not dispellable; gone on his reset, evade or death. His size grows 4% a stack, at '
          'most five steps (the script). Hunger For Blood\'s state (SV 11821).',
    raw_overrides=kit_raw('Damage dealt increased by $s1% per soul eaten.', 'Damage dealt increased by $s1%.',
                          instant=True, CumulativeAura=TITHE_MAX_STACKS, SpellVisualID_1=JR_TITHE,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

offering_spot_213588 = spell(
    id=213588, name='Offering Spot', school=School.SHADOW, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_DRAIN_SOUL,
    notes=f'{_D2}, JR5 (heroic): the look of the offering spot (-328, 218, -20.5; s7 #21 A) on the S0 stalker 300988, '
          'from the pull to the end of the fight: the shipped 4 yd shadow patch state (SV 90601). Look only.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=JR_OFFERING_SPOT, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

feed_look_213589 = self_visual(
    213589, "The Hungerer's Tithe", JR_SOUL_TEAR,
    f'{_D2}, JR5 (heroic): the look on him as a soul reaches the offering spot (Spirit Burst\'s SV 7180), with emote '
    'line 3.',
    icon=_ICON_DRAIN_SOUL, school=School.SHADOW,
)
