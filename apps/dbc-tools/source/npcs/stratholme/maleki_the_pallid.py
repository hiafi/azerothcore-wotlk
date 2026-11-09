"""
Stratholme build WP-S12: Maleki the Pallid (10438), normal and heroic
(.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.4 rows MK, s3.5 row S12, s3.6; build spec
docs/dungeons/stratholme-rework.md ST 3160-3211, design ST 2915-3159). WP-S12 owns this file (its spells: kSpellsMaleki
206665-206684 of modules/mod-dungeon-bosses src/Stratholme/StratholmeRework.h only; MalekiLogic.h names the same ids;
its creatures: 300584-300585). The engine side is src/Stratholme/boss_maleki_the_pallid_rework.cpp.

- 10438 Maleki the Pallid: boss_maleki_the_pallid_rework (SmartAI off; WP-S12's SQL rev drops the five stock rows and
  adds his texts), the build spec's normal health (170k: HealthModifier 77.237 on the level 61 mage class base 2,201),
  stun immunity 1972 (handoff s7 #3; the build spec's -273 holds silence too), flags_extra 0x4000001 (his stock
  0x4000000 plus INSTANCE_BIND), DamageModifier 3.5 (the stock value). Heroic 210k is WP-H's override
  (source/world/dungeons/stratholme.py).
- 300584 Ice Tomb (MK4): the tomb a player at 5 Icy Death freezes in, 8,000 health (warrior base 3,052 at level 60 x
  2.6212; the script sets exactly 8,000 / 12,000 too). Hostile (the Scourge's faction 21), not specified (type 10), no
  XP, no loot, no melee, no health regen; npc_st_ice_tomb roots it and keeps it passive. Sindragosa's tomb display 30890
  at scale 0.35 (WP-V: the block is 9.6 x 9.5 x 5.8 yd at scale 1, display scale 1.5). A combat add: its heroic
  template is minted by WP-H's _KIT_ADD_HEROIC (12,000 health), and this row names it, difficulty_entry_1 310190
  (STAGE-H report: the wave 1 kit adds mint 310189 Web Cocoon, 310190 Ice Tomb, 310191 Half-Digested Corpse).
- 300585 Eye of the Blizzard: an invisible, unselectable trigger (KIT_HELPER, the Ras Blizzard anchor's shape). One
  anchors the eye (the registry donuts follow it; on heroic the AI walks it 1.5 yd/s, MovePoint with its own speed),
  six more carry the storm's look in a ring outside the eye (206678). Not a combat add: no heroic template (handoff s7
  #15).

Spells. The Shatter and the storm deal their damage through dungeon copies of the mod-boss-mechanics resolve spell (the
registry's percent of the reference row; the combat log names the mechanic). The Siphon's and the tomb's drains and
Icy Death's ticks are the kit's generic percent spells (spell_dungeon_refflat_damage / _periodic: hundredths in the
effect value, heroic in EffectMiscValueB; KT-1). The heals are exact amounts from the script (base point 0). The rest
are auras the AI applies, casts and looks:

  206665  Icy Death         MK1 Magic, 5 stacks (CumulativeAura), for the fight: 1% Frost every 2 s and a 10% slow per
                            stack; spell_st_maleki_icy_death takes every stack on a dispel and shatters them (MK2)
  206666  Icy Death         MK1 the landing look (Chains of Ice 45524's SV 12328)
  206667  Shatter           MK2 the nova: resolve copy (Frost), Frost Nova 122's SV 17
  206668  Shatter           MK2 the rider: a 2 s root
  206669  The Siphon        MK3 the 2 s cast at the carrier, kickable
  206670  The Siphon        MK3 the 5 s channel tether, kickable (Drain Life 17238's SV 12655)
  206671  The Siphon        MK3 a stack eaten: 6% / 8% Shadow to the carrier
  206672  The Siphon        MK3 a stack eaten: his heal, 2% / 3% of his health (base point 0 = the amount)
  206673  Ice Tomb          MK4 the prisoner's hold: a stun (Ice Block 45438's SV 4325, the shell)
  206674  Ice Tomb          MK4 the drain, a second: 3% / 4% Shadow to the prisoner
  206675  Ice Tomb          MK4 his heal from the tomb, a second: 1% / 1.5% of his health (base point 0 = the amount)
  206676  Eye of the Blizzard  MK5 the storm's 1 s tick: resolve copy (Frost), no visual (the falling ice is the look)
  206677  Eye of the Blizzard  MK5 his 6 s channel bar (not kickable)
  206678  Eye of the Blizzard  MK5 the falling ice on a storm stalker (Blizzard 26607's SV 8787, 6 s)
  206679  Ice Tomb          MK4 the freeze's look on the prisoner (Ice Tomb 16869's SV 4340)
  206680  Frostbite         MK2 heroic: the look on an ally the nova gives a stack (Seed of Corruption 27243's SV 8339)
  206681  The Siphon        MK3 the carrier's hidden marker for the Siphon's life: the Eye's hit leaves them out by it
  206682-206684 spare.

Tooltips are number-free (ST checklist item 8, Systems.md s10).
"""

from lib.dsl import AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    FLAGS_EXTRA_INSTANCE_BIND,
    FLAGS_EXTRA_MALEKI_STOCK,
    KIT_CREATURE,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_ICE_TOMB,
    DISPLAY_INVISIBLE_STALKER,
    ICE_TOMB_SIZE,
    MK_EYE_OF_BLIZZARD,
    MK_FROSTBITE_SEED,
    MK_ICE_TOMB_CAST,
    MK_ICE_TOMB_SHELL,
    MK_ICY_DEATH_CAST,
    MK_ICY_DEATH_STATE,
    MK_SHATTER,
    MK_SIPHON_BEAM,
)

creature_template_columns(10438, **boss_columns(
    'boss_maleki_the_pallid_rework', 77.237, damage_modifier=3.5,
    flags_extra=FLAGS_EXTRA_INSTANCE_BIND | FLAGS_EXTRA_MALEKI_STOCK,
))

_MK = 'Stratholme build WP-S12 (Maleki the Pallid)'
_SCRIPT_REFFLAT = ('Stratholme: a percent of reference health in hundredths, set at launch by the kit\'s '
                   'spell_dungeon_refflat_damage / _periodic (DungeonKit::RefFlatOn)')
_SCRIPT_EXACT = 'Stratholme: an exact amount from the script (CastCustomSpell base point 0)'

_TARGET_DEST_CASTER = 18
_TARGET_DEST_DYNOBJ_ALLY = 29
_ATTR1_IS_CHANNELED = 0x00000004
_ATTR1_IS_SELF_CHANNELED = 0x00000040
_INTERRUPT_FLAGS_STANDARD = 15      # movement, pushback, interrupt, auto-attack: a kickable cast
_CHANNEL_INTERRUPT_KICK = 0x08      # CHANNEL_INTERRUPT_FLAG_INTERRUPT: a kick stops the channel
_PREVENTION_SILENCE = 1
_DISPEL_MAGIC = 1
_MECHANIC_ROOT = 7
# AURA_INTERRUPT_FLAG_CHANGE_MAP (SpellDefines.h): AC drops the aura before the logout save, after the login load and on
# a cross-map teleport, so a curse, a tether or a tomb's hold never outlives the instance on the character.
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000

_ICON_CHAINS_OF_ICE = 180           # Chains of Ice 45524
_ICON_FROST_NOVA = 193              # Frost Nova 122
_ICON_DRAIN_LIFE = 546              # Drain Life 17238
_ICON_ICE_TOMB = 35                 # Ice Tomb 16869
_ICON_BLIZZARD = 285                # Blizzard 26607
_ICON_SEED = 1932                   # Seed of Corruption 27243

# Percents in hundredths (KT-1's generic percent spells): the shown value is EffectBasePoints + 1 as stored.
_ICY_DEATH_TICK = 100               # 1% per stack, both difficulties (MalekiLogic.h kCurseTickPct)
_ICY_DEATH_SLOW = 10                # % per stack (kCurseSlowPct)
_SIPHON_DRAIN = (600, 800)          # kSiphonDrainPct 6 / 8
_TOMB_DRAIN = (300, 400)            # kTombDrainPct 3 / 4
_SIPHON_MARK_MS = 8000              # kSiphonMarkMs: the 2 s cast + the 5 s channel + 1 s


def _look(spell_id: int, name: str, visual: int, icon: int, notes: str):
    """A look Maleki casts (triggered) on a player: an instant DUMMY on the target, no handler, hidden from the log."""
    return spell(
        id=spell_id, name=name, school=School.FROST, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


def _refflat_hit(spell_id: int, name: str, pct: tuple[int, int], icon: int, desc: str, notes: str):
    """A drain hit at a percent of the reference row (the kit's spell_dungeon_refflat_damage), cast by Maleki
    (triggered): Shadow, always hits, cannot crit, ignores his modifiers (the target's own defensives count)."""
    s = spell(
        id=spell_id, name=name, school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=pct[0] - 1, die_sides=1,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_REFFLAT)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, instant=True, InterruptFlags=0, PreventionType=0, EffectMiscValueB_1=pct[1],
                              AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                              AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )
    scripted_by(s, 'spell_dungeon_refflat_damage')
    return s


def _heal(spell_id: int, name: str, icon: int, desc: str, notes: str):
    """His heal, an exact amount from the script (CastCustomSpell base point 0, triggered, on himself). Ignores his
    modifiers; a healing reduction on him (Mortal Strike) cuts it."""
    return spell(
        id=spell_id, name=name, school=School.SHADOW, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.HEAL, base_points=0, die_sides=0, implicit_target_a=TARGET_UNIT_CASTER,
                        potency_excluded=_SCRIPT_EXACT)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, instant=True, InterruptFlags=0, PreventionType=0, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- 300584 Ice Tomb / 300585 Eye of the Blizzard --------------------------------------------------------------------

# Level 60 warrior base 3,052: ceil(3,052 x 2.6212) = 8,000 (the build spec's tomb; the script sets it too).
ice_tomb_300584 = creature_template(
    300584, 'Ice Tomb', **{
        **KIT_CREATURE, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'type': 10, 'unit_class': 1, 'unit_flags': 0,
        'HealthModifier': 2.6212, 'DamageModifier': 0.0, 'RegenHealth': 0, 'detection_range': 0.0, 'lootid': 0,
        'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'flags_extra': 0x40,
        'ScriptName': 'npc_st_ice_tomb', 'difficulty_entry_1': 310190,
    },
)
creature_model(300584, display_id=DISPLAY_ICE_TOMB, scale=ICE_TOMB_SIZE)

eye_300585 = creature_template(
    300585, 'Eye of the Blizzard', **{**KIT_HELPER, 'minlevel': 61, 'maxlevel': 61, 'rank': 0, 'unit_class': 1,
                                      'type': 10, 'flags_extra': 0x40 | 0x80, 'ScriptName': ''},
)
creature_model(300585, display_id=DISPLAY_INVISIBLE_STALKER)

# --- MK1 Icy Death ---------------------------------------------------------------------------------------------------

icy_death_206665 = spell(
    id=206665, name='Icy Death', school=School.FROST, dispel=_DISPEL_MAGIC, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=_ICY_DEATH_TICK - 1,
                    die_sides=1, amplitude=2000, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded=_SCRIPT_REFFLAT),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DECREASE_SPEED,
                    base_points=-_ICY_DEATH_SLOW - 1, die_sides=1, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_CHAINS_OF_ICE,
    notes=f'{_MK}, MK1: the frost corruption on a random non-tank (never the tank), every 12 s from 5 s, emote line 1. '
          'Maleki applies and grows it (DungeonKit::AddStacks, caster Maleki): one stack on landing, +1 every 6 s '
          '(heroic 4 s), +1 when it lands again or (heroic) when a Shatter hits the carrier. Five stacks '
          '(CumulativeAura 5) and the AI freezes the carrier in an Ice Tomb (MK4) and removes it. Each stack: 1% Frost '
          'every 2 s of the reference row (spell_dungeon_refflat_periodic: 100 hundredths, both difficulties; the '
          'engine multiplies the tick by the stacks) and a 10% slow (50% at 5). Magic: a dispel takes every stack at '
          'once and shatters them (spell_st_maleki_icy_death, MK2); the Siphon (MK3) eats it a stack a second. For the '
          'fight (-1), dropped on a logout or a map change, removed on his death, evade and reset. Ignores his '
          'modifiers. Unstable Affliction 30108\'s SV 8141 (the chest rot state).',
    raw_overrides=kit_raw('A frost corruption that deepens over time. Dispelling it shatters it on nearby allies.',
                          'Frozen rot and a growing slow. A dispel shatters it on your allies.',
                          CastingTimeIndex=1, CumulativeAura=5, SpellVisualID_1=MK_ICY_DEATH_STATE,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(icy_death_206665, 'spell_dungeon_refflat_periodic', 'spell_st_maleki_icy_death')

icy_death_look_206666 = _look(
    206666, 'Icy Death', MK_ICY_DEATH_CAST, _ICON_CHAINS_OF_ICE,
    f'{_MK}, MK1: the landing look Maleki casts (triggered) on the cursed player with emote line 1. Chains of Ice '
    '45524\'s SV 12328 (ice hands, the chain mesh, a path of frost).')

# --- MK2 Shatter -----------------------------------------------------------------------------------------------------

shatter_206667 = resolve_copy(
    206667, 'Shatter', School.FROST, 'Icy Death bursts.',
    f'{_MK}, MK2: Icy Death\'s burst when it is dispelled or a Siphon snaps: a registry circle of 8 yd on the carrier '
    '(spared: a shape anchored on a player never hits it), 7% normal / 8% heroic of the non-tank row per stack the '
    'carrier had (at most 28% / 32%) and the 2 s root 206668; no Weakened (ruling 50). Heroic: each non-tank ally hit '
    'gains a stack of Icy Death (Frostbite, the registry OnHit). Copy of the resolve spell 205001 (Frost). Frost Nova '
    '122\'s SV 17 (the nova at the carrier, the frozen feet on every player hit).',
    icon=_ICON_FROST_NOVA, visual=MK_SHATTER,
)

shatter_root_206668 = spell(
    id=206668, name='Shatter', school=School.FROST, dispel=0, mechanic=_MECHANIC_ROOT,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=2000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_ROOT,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_FROST_NOVA,
    notes=f'{_MK}, MK2: the Shatter\'s rider on every ally it hits (cast by the registry marker, Maleki the original '
          'caster): a 2 s root (mechanic root: a freedom effect breaks it). No damage (206667 has it), no visual of '
          'its own (the nova\'s impact is the look).',
    raw_overrides=kit_raw('Frozen in place.', 'Frozen in place.', instant=True, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

frostbite_look_206680 = _look(
    206680, 'Frostbite', MK_FROSTBITE_SEED, _ICON_SEED,
    f'{_MK}, MK2 heroic: the look on an ally a Shatter hits as it gains a stack of Icy Death (the script adds the '
    'stack). Seed of Corruption 27243\'s SV 8339 (shadow hands, a chest state, a blood bolt: the spread).')

# --- MK3 The Siphon --------------------------------------------------------------------------------------------------

siphon_cast_206669 = spell(
    id=206669, name='The Siphon', school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=2000, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_DRAIN_LIFE,
    notes=f'{_MK}, MK3: the 2 s cast at the carrier (the player with the most Icy Death; emote line 2), every 20 s '
          'from 15 s. Kickable (InterruptFlags 15, PreventionType silence; the descriptor\'s interrupt list, priority '
          '1, a reward): a kick ends the Siphon with the stacks kept. No effect: at the cast\'s end the AI starts the '
          'channel 206670. The carrier 12 yd from their spot at the cast\'s start snaps it (the AI, every 250 ms). '
          'Ignores LoS.',
    raw_overrides=kit_raw('Turns his staff on a cursed enemy to drink the frost from them.',
                          InterruptFlags=_INTERRUPT_FLAGS_STANDARD, PreventionType=_PREVENTION_SILENCE,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT),
)

siphon_channel_206670 = spell(
    id=206670, name='The Siphon', school=School.SHADOW, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=5000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_DRAIN_LIFE,
    notes=f'{_MK}, MK3: the 5 s channel on the carrier, the tether (a DUMMY aura on them, Drain Life 17238\'s SV '
          '12655: chain 719 HealBeam_Desaturated, a gray-white wave). The stacks it eats (one a second) run on the '
          'AI\'s clock: 206671 on the carrier, 206672 on him. Kickable (ChannelInterruptFlags interrupt, '
          'PreventionType silence; priority 1): the stacks left stay. The AI stops it when the carrier snaps it (12 '
          'yd), dies, freezes or runs out of stacks. Ignores LoS; dropped on a map change.',
    raw_overrides=kit_raw('Drinks the frost from a cursed enemy.', 'Maleki drinks your frost. Run 12 yards from where '
                          'you stood to snap the tether.', CastingTimeIndex=1, InterruptFlags=0,
                          ChannelInterruptFlags=_CHANNEL_INTERRUPT_KICK, PreventionType=_PREVENTION_SILENCE,
                          SpellVisualID_1=MK_SIPHON_BEAM, AttributesEx=_ATTR1_IS_CHANNELED | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

siphon_mark_206681 = spell(
    id=206681, name='The Siphon', school=School.SHADOW, dispel=0, mechanic=0,
    attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_SIPHON_MARK_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_DRAIN_LIFE,
    notes=f'{_MK}, MK3: the carrier\'s marker for the Siphon\'s whole life (the 2 s cast and the 5 s channel), cast by '
          'Maleki (triggered) as the cast starts and removed when the Siphon ends; 8 s (MalekiLogic.h kSiphonMarkMs) '
          'only bounds a Siphon the script forgot. A hidden DUMMY aura (not shown, not logged): the Eye\'s registry '
          'hit leaves its bearer out by a live aura check (Eligibility auraSpell, at most 0 stacks), so the hit is '
          'registered once per Eye and its once-per-player Weakened holds the whole storm (R-1-B B-3); the carrier\'s '
          'own storm ticks are the script\'s. A debuff (never cancelled), NO_IMMUNITIES (an immunity never strips it '
          'mid-Siphon), dispel none; dropped on a map change.',
    raw_overrides=kit_raw(instant=True, AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=ATTR3_ALWAYS_HIT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

siphon_drain_206671 = _refflat_hit(
    206671, 'The Siphon', _SIPHON_DRAIN, _ICON_DRAIN_LIFE, 'Drinks a stack of Icy Death.',
    f'{_MK}, MK3: a stack eaten, each second of the channel: 6% normal / 8% heroic of the reference row on the carrier '
    '(600 / 800 hundredths: the tank row if the carrier is the tank, never in practice). No visual (the tether is the '
    'look).')

siphon_heal_206672 = _heal(
    206672, 'The Siphon', _ICON_DRAIN_LIFE, 'Drinks a stack of Icy Death.',
    f'{_MK}, MK3: his heal for each stack eaten, 2% normal / 3% heroic of his maximum health (170k: 3,400; 210k: '
    '6,300).')

# --- MK4 Ice Tomb ----------------------------------------------------------------------------------------------------

ice_tomb_hold_206673 = spell(
    id=206673, name='Ice Tomb', school=School.FROST, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=8000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_ICE_TOMB,
    notes=f'{_MK}, MK4: the prisoner\'s hold, applied by the Ice Tomb 300584 through the kit\'s HoldInUnit (its own '
          'spell, handoff s3.11 #23 / KT-1 s4 #2): a stun for at most 8 s, removed when the tomb dies (broken), at 8 s '
          '(it melts), when the prisoner dies or leaves, or at the fight\'s end. Not damage immune (the drain 206674 '
          'lands). No mechanic (no trinket breaks it), Dispel none, NO_IMMUNITIES; dropped on a logout or a map '
          'change. Ice Block 45438\'s SV 4325 (the icebarrier_state shell on the player).',
    raw_overrides=kit_raw('Frozen in an Ice Tomb.', 'Frozen in an Ice Tomb. Your allies must break it.',
                          CastingTimeIndex=1, SpellVisualID_1=MK_ICE_TOMB_SHELL, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

ice_tomb_drain_206674 = _refflat_hit(
    206674, 'Ice Tomb', _TOMB_DRAIN, _ICON_ICE_TOMB, 'Drains the frozen.',
    f'{_MK}, MK4: the tomb\'s drain on its prisoner, each second it stands: 3% normal / 4% heroic of the reference row '
    '(300 / 400 hundredths). No visual of its own (the tomb and the shell are the look).')

ice_tomb_heal_206675 = _heal(
    206675, 'Ice Tomb', _ICON_ICE_TOMB, 'Drains the frozen.',
    f'{_MK}, MK4: his heal from each standing tomb, each second: 1% normal / 1.5% heroic of his maximum health '
    '(170k: 1,700; 210k: 3,150).')

ice_tomb_look_206679 = _look(
    206679, 'Ice Tomb', MK_ICE_TOMB_CAST, _ICON_ICE_TOMB,
    f'{_MK}, MK4: the freeze\'s look Maleki casts (triggered) on the player as the tomb forms. Ice Tomb 16869\'s SV '
    '4340 (ice hands, head and base, the ice barrier state, the missile).')

# --- MK5 The Eye of the Blizzard -------------------------------------------------------------------------------------

eye_storm_206676 = resolve_copy(
    206676, 'Eye of the Blizzard', School.FROST, 'The storm outside the eye.',
    f'{_MK}, MK5: the storm\'s 1 s tick on everyone outside the eye (a hidden registry donut on the eye stalker, 8 yd '
    '/ 6 yd hole, out to 60 yd: the whole plaza) for the 6 s storm: 10% normal / 15% heroic of the non-tank row, '
    'Weakened once per player (registered once per Eye). The Siphon\'s carrier (206681\'s bearer, left out of the '
    'registry hit) takes the same tick through the kit\'s RegistryHit while the Siphon runs, and owes one Weakened at '
    'the storm\'s end unless the registry hit them. Copy of the resolve spell 205001 (Frost). No visual (a tick every '
    'second; the falling ice of 206678 is the look).',
    icon=_ICON_BLIZZARD,
)

eye_channel_206677 = spell(
    id=206677, name='Eye of the Blizzard', school=School.FROST, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=6000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_BLIZZARD,
    notes=f'{_MK}, MK5: his 6 s channel bar for the storm, the bar only (SPELL_ATTR1_IS_SELF_CHANNELED with a DUMMY '
          'aura): the storm runs on the AI\'s clock, so a broken channel changes nothing. He channels it only when he '
          'is free (the 60 s collision: a Siphon\'s channel keeps the storm without the bar). Not interruptible '
          '(InterruptFlags, ChannelInterruptFlags and PreventionType 0). While it runs a due Siphon waits.',
    raw_overrides=kit_raw('Calls a blizzard over the plaza. Only the eye is calm.', 'Calling the blizzard.',
                          AttributesEx=_ATTR1_IS_SELF_CHANNELED, ChannelInterruptFlags=0, InterruptFlags=0,
                          PreventionType=0, AttributesEx4=ATTR4_NO_CAST_LOG),
)

eye_storm_look_206678 = spell(
    id=206678, name='Eye of the Blizzard', school=School.FROST, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=6000,
    effects=[Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=0, implicit_target_a=_TARGET_DEST_CASTER,
                    implicit_target_b=_TARGET_DEST_DYNOBJ_ALLY, apply_aura=AuraType.DUMMY, radius_yards=3.0)],
    spell_icon_id=_ICON_BLIZZARD,
    notes=f'{_MK}, MK5: visual only, the falling ice at a storm stalker\'s feet for the 6 s storm (TARGET_DEST_CASTER '
          '/ TARGET_DEST_DYNOBJ_ALLY, the Ras Blizzard look\'s shape: its DUMMY aura reaches nobody). Six stalkers '
          '300585 in a ring outside every spot the eye can cover (12 yd normal, 18 yd heroic). Blizzard 26607\'s SV '
          '8787 (Blizzard_Impact_Base as a PersistentAreaKit, about 6 yd across). The registry donut (206676) owns the '
          'ticks.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=MK_EYE_OF_BLIZZARD, AttributesEx4=ATTR4_NO_CAST_LOG),
)
