"""
Ragefire Chasm build WP-D4: Taragaman the Hungerer (11520)
(.agents/plans/ragefire-chasm-build/ragefire-chasm-build.HANDOFF.md s3.5 row D4, s3.10, s3.12; build spec
docs/dungeons/ragefire-chasm-rework.md "Taragaman the Hungerer", TG1-TG6, TG10). WP-D4 owns this file.

- 11520: bound to boss_taragaman_rework (modules/mod-dungeon-bosses src/RagefireChasm/boss_taragaman_rework.cpp),
  SmartAI off (rev_skeleton_ragefire_chasm.sql drops its rows), the build spec's normal health (12,816 =
  HealthModifier 36 on the level 16 warrior base 356), the stock DamageModifier (until T), stun immunity 1972,
  INSTANCE_BIND with both assist flags, detection range 12 (s7 #12 A). Heroic health and its overrides are WP-H's
  (source/world/dungeons/ragefire_chasm.py). He has no add of his own.
- GO 301342 (the Searing Spike) and texts 11520 0-6 are hand SQL:
  data/sql/updates/pending_db_world/rev_taragaman_ragefire_chasm.sql.

Spells (kSpellsTaragaman 213650-213689; TaragamanLogic.h names the same ids; looks from ._visuals, unconfirmed until
seen in game). A kick on Devour (Shadow) locks Shadow alone, so it never eats a set piece: Felstorm's and the Nova's
bars are Fire, Uppercut 18072 (stock, Physical) is free (handoff s3.5 rule 25 as corrected by G1):

  213650  Feast              TG1 the mark on the prey, 3 s (the hard mode's 2 s is the script's)
  213651  Feast              a leap's look, on himself, at the start and at the landing
  213652  Feast              TG1 the bite: Physical, the script's base point
  213653  Gorged             +10% damage dealt per stack (the script's cap: 3 normal, none on heroic)
  213654  Gorge              TG1 his heal on a Gorge (and a drunk globule's, D4H), the script's base point
  213655  Devour             TG2 the 5 s kickable channel on the prey (Shadow)
  213656  Devour             TG2 a tick: Physical, the script's base point
  213657  Devour             TG2 his heal per tick, the script's base point
  213658  Felstorm           TG3 the 2 s bar (Fire, not interruptible)
  213659  Felstorm           TG3 the spin's look, an aura on him
  213660  Felstorm           TG3 the ring's tick (resolve copy, Physical)
  213661  Fel Pulse          TG4 a pulse on one player: Fire, the script's base point
  213662  Fel Eruption       TG5 a spot's hit (resolve copy, Fire)
  213663  Fel Eruption       TG5 the eruption's look, the spot's stalker 300988 on itself
  213664  Searing Spike      TG6 a spike rises: the rock burst at its point
  213665  Searing Spike      TG6 and the dirt under it
  213666  Searing Nova       TG6 the 4 s bar (Fire, not interruptible)
  213667  Searing Nova       TG6 the hard mode's 3 s bar
  213668  Searing Nova       TG6 the Nova's hit (resolve copy, Fire)
  213669-213689 spare.

Not wired: TG_NOVA_CAST (the optional lasting look during the Nova's cast).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    self_visual,
)
from lib.dsl.registry import creature_template_columns, spell

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
    TG_BITE,
    TG_DEVOUR_CHANNEL,
    TG_FEAST_MARK,
    TG_FEL_PULSE,
    TG_FEL_SPOT,
    TG_FELSTORM,
    TG_LEAP,
    TG_NOVA,
    TG_SPIKE_RISE,
    TG_SPIKE_RISE_DIRT,
)

_D4 = 'Ragefire Chasm build WP-D4 (Taragaman the Hungerer)'
_SCRIPT_BP = ('Ragefire Chasm Taragaman: a percent of reference health the script sets as the base point '
              '(DungeonKit::RefFlatOn, the tank row on the tank)')
_SCRIPT_HEAL = 'Ragefire Chasm Taragaman: a percent of his own maximum health (the script\'s base point)'

creature_template_columns(11520, **boss_columns(
    'boss_taragaman_rework', 36.0, damage_modifier=2.4,
))

# --- constants (RagefireChasmRework.h namespace Taragaman; lib/test_ragefire_chasm_taragaman.py pins each) ------------

FEAST_MARK_MS = 3000            # kFeastMarkMs.normal / heroic (the script cuts it to the hard mode's 2 s)
GORGED_PCT = 10                 # kGorgedPct
DEVOUR_MS = 5000                # kDevourTicks x kDevourTickMs
DEVOUR_RANGE = 100.0            # kDevourRangeYd
FELSTORM_CAST_MS = 2000         # kFelstormCastMs
FELSTORM_SPIN_MS = 6000         # the longest kFelstormSpinMs (the script ends it: heroic 5 s)
NOVA_CAST_MS = (4000, 3000)     # kNovaCastMs: normal and heroic, hard mode

_ATTR0_DO_NOT_DISPLAY = 0x00000080
_ATTR0_DO_NOT_LOG = 0x00000100
_ATTR1_IS_CHANNELED = 0x00000004
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_CHANNEL_INTERRUPT_KICK = 0x08      # SpellDefines.h CHANNEL_INTERRUPT_FLAG_INTERRUPT
_PREVENTION_SILENCE = 1
_DEFENSE_MAGIC = 1
_SCHOOL_MASK_ALL = 127
_STACKS_UNCAPPED = 255              # the aura's own limit, never reached
_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40

# Stock icons (Spell.dbc SpellIconID of the named spell)
_ICON_FEAST = 538                   # Hunter's Mark 1130
_ICON_LEAP = 1559                   # Feral Charge - Bear 16979
_ICON_DEVOUR = 243                  # Devour 38895
_ICON_GORGED = 169                  # Death Wish 12292
_ICON_FELSTORM = 83                 # Bladestorm 9632
_ICON_FEL = 2299                    # Felfire 35767
_ICON_SPIKE = 66                    # Ground Spike 59750
_ICON_NOVA = 33                     # Fire Nova 11970


def _script_hit(spell_id: int, name: str, school: School, desc: str, notes: str, *, icon: int, visual: int = 0):
    """A hit whose amount the script sets as the base point (CastSpellExtraArgs::AddSpellBP0; DieSides 0, so the amount
    is exact): triggered, always hits, cannot crit, is not reflected or redirected, ignores LoS and the caster's
    modifiers (Gorged is the script's factor), DmgClass magic. Physical ones are reduced by the target's armor, as the
    resolve copies are."""
    return spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_BP)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, instant=True, InterruptFlags=0, PreventionType=0, DefenseType=_DEFENSE_MAGIC,
                              AttributesEx=ATTR1_NO_THREAT | ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                              AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                              AttributesEx4=ATTR4_NO_CAST_LOG, **({'SpellVisualID_1': visual} if visual else {})),
    )


def _script_heal(spell_id: int, name: str, desc: str, notes: str, *, icon: int):
    """His heal, an exact amount from the script (base point 0, triggered, on himself). Ignores his modifiers; a healing
    reduction on him (Mortal Strike) cuts it."""
    return spell(
        id=spell_id, name=name, school=School.SHADOW, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.HEAL, base_points=0, die_sides=0, implicit_target_a=TARGET_UNIT_CASTER,
                        potency_excluded=_SCRIPT_HEAL)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, instant=True, InterruptFlags=0, PreventionType=0, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


def _look_at_point(spell_id: int, name: str, visual: int, notes: str, *, icon: int):
    """A look-only spell cast at a point (a DUMMY aimed at a destination; DO_NOT_DISPLAY | DO_NOT_LOG), the boss's own
    cast, triggered (the Bael'Gar shape). Copies a stock visual, never the stock spell."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, Targets=_TARGET_FLAG_DEST_LOCATION,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- TG1 Feast --------------------------------------------------------------------------------------------------------

feast_mark_213650 = spell(
    id=213650, name='Feast', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=FEAST_MARK_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_FEAST,
    notes=f'{_D4}, TG1: the mark on the prey, the player with the lowest health percent on the plateau (emote line 2): '
          '3 s, cut by the script to 2 s in the hard mode (ruling 12). At its end he leaps to them and bites. DUMMY, '
          'not dispellable, lands through immunities, dropped on a map change. Hunter\'s Mark 1130\'s SV 3239.',
    raw_overrides=kit_raw('Marked as the Hungerer\'s prey.',
                          'The Hungerer smells your blood. Be healed above half before he lands.', instant=True,
                          SpellVisualID_1=TG_FEAST_MARK, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

leap_look_213651 = self_visual(
    213651, 'Feast', TG_LEAP,
    f'{_D4}, TG1 and TG6: a leap\'s look, cast (triggered) on himself as he takes off and again as he lands (the cast '
    'kit plays at the start only): Feral Charge - Bear 16979\'s SV 5162. Look only.',
    icon=_ICON_LEAP,
)

bite_213652 = _script_hit(
    213652, 'Feast', School.NORMAL, 'The Hungerer bites.',
    f'{_D4}, TG1: the bite as the Feast\'s leap lands on the prey: 25% (heroic 40%, hard mode 45%) of the reference '
    'row, the tank row on the tank, times the Gorged factor. Not avoidable, so no Weakened. The prey under half health '
    'at the landing (read before the bite) Gorges him. Devour 38895\'s SV 8923 (a blood burst on the target; the '
    'Felguard has no animation for it).',
    icon=_ICON_DEVOUR, visual=TG_BITE,
)

gorged_213653 = spell(
    id=213653, name='Gorged', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=GORGED_PCT,
                    die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_GORGED,
    notes=f'{_D4}, TG1 Gorged: a stack for every Gorge (and, in the hard mode, every drunk globule): +10% damage '
          'dealt, for the fight; 3 stacks at most on normal, no cap on heroic and in the hard mode (ruling 15; the '
          'script caps it, DungeonKit::AddStacks). The aura raises his melee and Uppercut; his percent hits ignore '
          'caster modifiers and take the same factor from the script. It never changes his size (rule 29: the Nova\'s '
          'eye). Not dispellable; removed on a wipe.',
    raw_overrides=kit_raw('Well fed.', 'Deals more damage with every meal.', instant=True,
                          CumulativeAura=_STACKS_UNCAPPED, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

gorge_heal_213654 = _script_heal(
    213654, 'Gorge', 'Feeds on the wounded.',
    f'{_D4}, TG1: his heal when he Gorges, 3% of his maximum health (a drunk globule, D4H: 2%).',
    icon=_ICON_DEVOUR,
)

# --- TG2 Devour (heroic, hard mode) -----------------------------------------------------------------------------------

devour_213655 = spell(
    id=213655, name='Devour', school=School.SHADOW, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=DEVOUR_RANGE,
    duration_ms=DEVOUR_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_DEVOUR,
    notes=f'{_D4}, TG2 (heroic, hard mode): right after the bite, a 5 s channel on the prey (a DUMMY aura on them, '
          'emote line 5). The ticks run on the AI\'s clock, five, the first at 1 s: 213656 on the prey and 213657 on '
          'him. Cast for real (the bar shows). Kickable: ChannelInterruptFlags 0x08 (a kick) and PreventionType 1 (a '
          'silence); the descriptor\'s interrupt list, priority 4, every 15 s (the hard mode 6 s). SHADOW, though its '
          'damage is Physical (the tick is its own spell): a kick locks the school of what it stopped, and Felstorm\'s '
          'and the Nova\'s bars are Fire and Uppercut is Physical (rule 25). Range 100, ignores LoS: the prey is not '
          'held. Dropped on a map change; Divine Shield or Ice Block end it. Blood Siphon 24322\'s SV 7270 (the beam).',
    raw_overrides=kit_raw('Devours an enemy alive.', 'The Hungerer is devouring you.', instant=True, InterruptFlags=0,
                          ChannelInterruptFlags=_CHANNEL_INTERRUPT_KICK, PreventionType=_PREVENTION_SILENCE,
                          SpellVisualID_1=TG_DEVOUR_CHANNEL, AttributesEx=_ATTR1_IS_CHANNELED | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

devour_tick_213656 = _script_hit(
    213656, 'Devour', School.NORMAL, 'The Hungerer feeds.',
    f'{_D4}, TG2: one tick of Devour on the prey: 14% (hard mode 16%) of the reference row, the tank row on the tank, '
    'times the Gorged factor; Physical; no Weakened.',
    icon=_ICON_DEVOUR,
)

devour_heal_213657 = _script_heal(
    213657, 'Devour', 'Feeds on its prey.',
    f'{_D4}, TG2: his heal per tick of Devour, 1% of his maximum health.',
    icon=_ICON_DEVOUR,
)

# --- TG3 Felstorm, TG4 fel pulses, TG5 fel spots ----------------------------------------------------------------------

felstorm_cast_213658 = cast_bar(
    213658, 'Felstorm', FELSTORM_CAST_MS, 'Raises his blade to spin. Get away from him.',
    f'{_D4}, TG3: the 2 s bar before the spin (emote line 3). Not interruptible (the registry\'s ring, tag 10, lands '
    'whatever happens to the bar). Fire: a kick on Devour (Shadow) never locks it (rule 25).',
    icon=_ICON_FELSTORM, school=School.FIRE,
)

felstorm_spin_213659 = spell(
    id=213659, name='Felstorm', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=FELSTORM_SPIN_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_FELSTORM,
    notes=f'{_D4}, TG3: the spin\'s look, a DUMMY aura he casts (triggered) on himself when the cast ends: 6 s, cut by '
          'the script at the spin\'s end (heroic and hard mode 5 s). The minted SpellVisual 90370 (Ascension '
          'bladestorm ribbons and a fel wreath, anim 126); fallback Bladestorm 6044. The ring marker carries the '
          'radius.',
    raw_overrides=kit_raw('Spins with his blade out.', 'Spinning.', instant=True, SpellVisualID_1=TG_FELSTORM,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

felstorm_213660 = resolve_copy(
    213660, 'Felstorm', School.NORMAL, 'Caught in the Felstorm.',
    f'{_D4}, TG3: the ring\'s tick, once a second for the spin (normal 6 s, heroic and hard mode 5 s) on everyone '
    'within 8 yd (10): 8% (heroic, hard mode 20%) of the reference row, the tank included; lingering, so no Weakened '
    '(registry tag 10). Copy of the resolve spell 205001 (Physical).',
    icon=_ICON_FELSTORM,
)

fel_pulse_213661 = _script_hit(
    213661, 'Fel Pulse', School.FIRE, 'Fel fire pulses across the plateau.',
    f'{_D4}, TG4 (heroic, hard mode): once a second of the spin, on every player of the fight on the plateau: 4% (hard '
    'mode 5%) of the reference row. Unavoidable, no Weakened, never a registry Zone (bots would flee it). Felfire '
    '35767\'s SV 8092 on the player.',
    icon=_ICON_FEL, visual=TG_FEL_PULSE,
)

fel_spot_213662 = resolve_copy(
    213662, 'Fel Eruption', School.FIRE, 'Fel fire erupts from the floor.',
    f'{_D4}, TG5 (heroic, hard mode): a spot\'s hit, ten per spin, one every 0.5 s, 4 yd (hard mode 5) round a floor '
    'point 0 to 4 yd (0 to 3) off the next player of a shuffled rotation, the tank included, 1.5 s (1.25 s) after its '
    'marker: 35% (45%) of the reference row and 1 Weakened (registry tag 11). Copy of the resolve spell 205001 (Fire).',
    icon=_ICON_FEL,
)

fel_spot_look_213663 = self_visual(
    213663, 'Fel Eruption', TG_FEL_SPOT,
    f'{_D4}, TG5: the eruption\'s look, cast (triggered) by the spot\'s stalker 300988 on itself as the spot lands: '
    'the minted SpellVisual 90371 (an impact kit); fallback 9004. Look only.',
    icon=_ICON_FEL, school=School.FIRE,
)

# --- TG6 Searing Nova -------------------------------------------------------------------------------------------------

spike_look_213664 = _look_at_point(
    213664, 'Searing Spike', TG_SPIKE_RISE,
    f'{_D4}, TG6: a Searing Spike rises. He casts it (triggered) at each spike\'s point as the object appears: Ground '
    'Spike 59750\'s SV 12718 (a rock burst over the pop). Look only.',
    icon=_ICON_SPIKE,
)

spike_dirt_213665 = _look_at_point(
    213665, 'Searing Spike', TG_SPIKE_RISE_DIRT,
    f'{_D4}, TG6: the dirt under the rising spike, at the same point: SV 7443 (an area kit). Look only.',
    icon=_ICON_SPIKE,
)

nova_cast_213666 = cast_bar(
    213666, 'Searing Nova', NOVA_CAST_MS[0], 'Draws the fire of the lake. Get out of his sight.',
    f'{_D4}, TG6: the 4 s bar on the hub while the spikes stand. Not interruptible (the registry\'s Hide, tags 12 and '
    '13, lands whatever happens to the bar). Fire: a kick on Devour (Shadow) never locks it (rule 25). Fire Nova '
    '11970\'s SV 963: fire in his hands, the nova at the cast\'s end.',
    icon=_ICON_NOVA, visual=TG_NOVA, school=School.FIRE,
)

nova_cast_hm_213667 = cast_bar(
    213667, 'Searing Nova', NOVA_CAST_MS[1], 'Draws the fire of the lake. Get out of his sight.',
    f'{_D4}, TG6: the hard mode\'s 3 s bar. As 213666.',
    icon=_ICON_NOVA, visual=TG_NOVA, school=School.FIRE,
)

nova_213668 = resolve_copy(
    213668, 'Searing Nova', School.FIRE, 'Only a spike\'s shadow saves you.',
    f'{_D4}, TG6: the Nova\'s hit, at the cast\'s end, on every player within 60 yd whom he can see (the BM Hide kind: '
    'a real IsWithinLOSInMap from 3.05 yd over the hub, so a Searing Spike\'s collision model blocks it): 50% (heroic '
    '75%, hard mode 90%) of the reference row, the tank included, no Weakened. Copy of the resolve spell 205001 '
    '(Fire). Its look is the bar\'s (213666).',
    icon=_ICON_NOVA,
)
