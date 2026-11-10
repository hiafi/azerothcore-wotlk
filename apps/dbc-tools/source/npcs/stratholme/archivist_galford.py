"""
Stratholme build WP-S6: Archivist Galford (10811), normal and heroic
(.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.4 rows GF, s3.5 row S6, s3.6, s3.8; build spec
docs/dungeons/stratholme-rework.md ST 1707-1765, design ST 1506-1706). WP-S6 owns this file (its spells: kSpellsGalford
206520-206544 of modules/mod-dungeon-bosses src/Stratholme/StratholmeRework.h only; GalfordLogic.h names the same ids;
its creatures: 300606-300607). The engine side is src/Stratholme/boss_archivist_galford_rework.cpp.

- 10811 Archivist Galford: boss_archivist_galford_rework (SmartAI off; WP-S6's SQL rev
  rev_archivist_galford_stratholme.sql drops the three stock rows and adds his texts), the build spec's normal health
  (170k: HealthModifier 69.615 on the level 60 paladin class base 2,442), stun immunity 1972 (the build spec's "own
  immunity set, stun immune"; Pyroblast stays kickable), INSTANCE_BIND (flags_extra 1), DamageModifier 3.5 (the stock
  value: base SQL; the live 6.5 is a mod-progression leftover; WP-T tunes it). Heroic 220k is WP-H's override
  (source/world/dungeons/stratholme.py). He keeps his book (creature_equip_template 12742). Retired: Burning Winds
  17293 (the 8 s stun), Pyroblast 17274 (6 s) and Fire Nova 17366 (instant); his own spells below replace them.
- 300606 Holy Fire (the build spec's holy fire puddle stalker): an invisible, unselectable prop (KIT_HELPER) the script
  summons on each puddle; it carries the puddle's look (206531-206534 by radius). npc_st_holy_fire_puddle (a
  NullCreatureAI). No heroic template (handoff s7 #15).
- 300607 The Pyre (the build spec's Pyre and north wall stalker): an invisible prop, a row of them along each wall (one
  every 6 yd or less) at the pull; each carries the wall's fire (206535) and delivers the lethal strike for the look
  (the kit's DungeonKit::LethalWall strikers). npc_st_pyre_wall (a NullCreatureAI). No heroic template.

Spells. The registry hits (Holy Fire's landing, Fire Nova) deal their damage through dungeon copies of the
mod-boss-mechanics resolve spell; Holy Fire's burn is the kit's generic percent periodic
(spell_dungeon_refflat_periodic); Pyroblast and the holy fire tick have their own SpellScripts in the boss file
(Kindled raises Pyroblast; Scorched raises the tick), each a percent of the reference row set at launch
(DungeonKit::RefFlatOn). The walls' strike is the shared 206400 (shared.py). The rest are auras, cast bars and looks:

  206520  Holy Fire          GF1 the 6 s burn on a non-tank, 10% over 6 s (no dispel type); the circle follows them
  206521  Holy Fire          GF2 the landing on others inside the 4 yd circle: resolve copy, Holy, 30% + Weakened
  206522  Pyroblast          GF3 the 4 s kickable cast at the tank: 35% / 45% Fire (Kindled: x 1.25), then a puddle
  206523  Fire Nova          GF5 the 2 s cast bar (emote line 1; not kickable)
  206524  Fire Nova          GF5 the burst: resolve copy, Fire, 30% + Weakened in 10 yd, the tank too
  206525  Fire Nova          GF5 the burst's look on him (self visual)
  206526  Holy Fire          GF7 the holy fire tick: 8% a second x (1 + 0.25 per Scorched stack), once however many
  206527  Scorched           GF8 a stack a second in holy fire; all fall off 4 s after leaving it
  206528  Kindled            GF9 on him while he stands in holy fire: +25% damage done, -50% damage taken
  206529  Burning Winds      GF11 heroic: the 2 s cast bar (yell line 5; not kickable)
  206530  Burning Winds      GF11 the gust's look on each player thrown (1 s, the fire twister)
  206531  Holy Fire          GF7 a puddle stalker's look, 4 yd (Holy Fire's landing)
  206532  Holy Fire          GF7 5 yd (Fire Nova's)
  206533  Holy Fire          GF7 6 yd (Pyroblast's, normal)
  206534  Holy Fire          GF7 8 yd (Pyroblast's, heroic)
  206535  The Pyre           GF10 a wall stalker's fire
  206536-206544 spare

Visual ids are V-2's (._visuals GF_*, SV_HOLYZONE_*); every look is unconfirmed until seen in game.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_2,
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
    GF_BURNING_WINDS,
    GF_COMBUSTION_FLASH,
    GF_FIRE_NOVA,
    GF_FIRE_WALL,
    GF_HOLY_FIRE,
    GF_KINDLED,
    GF_PYROBLAST,
    SV_HOLYZONE_4_STATE,
    SV_HOLYZONE_5_STATE,
    SV_HOLYZONE_6_STATE,
    SV_HOLYZONE_8_STATE,
)

# Held back until wave 2 binds this boss (_common.py BIND_WAVE_2): stock until then.
if BIND_WAVE_2:
    creature_template_columns(10811, **boss_columns(
        'boss_archivist_galford_rework', 69.615, damage_modifier=3.5,
    ))

_GF = 'Stratholme build WP-S6 (Archivist Galford)'
_SCRIPT_REFFLAT = ('Stratholme: a percent of reference health in hundredths, set at launch by the kit\'s '
                   'spell_dungeon_refflat_periodic (DungeonKit::RefFlatOn)')
_SCRIPT_OWN = ('Stratholme: a percent of reference health set at launch by the boss file\'s own SpellScript '
               '(DungeonKit::RefFlatOn)')

_TARGET_UNIT_TARGET_ENEMY = 6

_ATTR0_DO_NOT_DISPLAY = 0x00000080
_ATTR0_DO_NOT_LOG = 0x00000100
_ATTR0_NO_ACTIVE_DEFENSE = 0x00200000
_ATTR1_NO_REDIRECTION = 0x00000008
_ATTR1_NO_REFLECTION = 0x00000080
_ATTR1_NO_THREAT = 0x00000400
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_NOT_A_PROC = 0x00000200
_ATTR3_ALWAYS_HIT = 0x00040000

_INTERRUPT_FLAGS_STANDARD = 15      # movement, pushback, interrupt, auto-attack: a kickable cast
_PREVENTION_SILENCE = 1
# AURA_INTERRUPT_FLAG_CHANGE_MAP (SpellDefines.h): a map change or a logout drops it, so nothing outlives the instance.
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_SCHOOL_MASK_ALL = 127
_DEFENSE_MAGIC = 1

# Icons (the working-copy Spell.dbc).
_ICON_HOLY_FIRE = 156               # Holy Fire 14914
_ICON_PYROBLAST = 184               # Pyroblast 17274
_ICON_FIRE_NOVA = 33                # Fire Nova 17366 (shared with Combustion 11129)
_ICON_BURNING_WINDS = 220           # Burning Winds 17293
_ICON_IMMOLATE = 31                 # Immolate 348
_ICON_CONSECRATION = 51             # Consecration 20116
_ICON_FIRE_WALL = 2129              # Fire Wall 43113

# Numbers (GalfordLogic.h).
_HOLY_FIRE_MS = 6000                # kHolyFireBurnMs
_HOLY_FIRE_TICK = 167               # kHolyFireTickHundredths: 6 ticks = 10.02%
_PYRO_CAST_MS = 4000                # kPyroCastMs
_PYRO_SPEED = 24.0                  # stock Pyroblast 17274's missile speed
_NOVA_CAST_MS = 2000                # kNovaCastMs
_WINDS_CAST_MS = 2000               # kWindsCastMs
_GUST_MS = 1000                     # kGustLookMs
_SCORCHED_MS = 4000                 # kScorchedFadeMs
_SCORCHED_MAX = 20                  # kScorchedMaxStacks
_KINDLED_MS = 1000                  # kKindledAuraMs
_KINDLED_DONE = 25                  # kKindledDamageDonePct
_KINDLED_TAKEN = -50                # kKindledDamageTakenPct

# --- 300606 Holy Fire puddle, 300607 the Pyre -------------------------------------------------------------------------

holy_fire_puddle_300606 = creature_template(
    300606, 'Holy Fire', **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1,
                            'ScriptName': 'npc_st_holy_fire_puddle'},
)
creature_model(300606, display_id=DISPLAY_INVISIBLE_STALKER)

pyre_wall_300607 = creature_template(
    300607, 'The Pyre', **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1,
                           'ScriptName': 'npc_st_pyre_wall'},
)
creature_model(300607, display_id=DISPLAY_INVISIBLE_STALKER)

# --- GF1 / GF2 Holy Fire ----------------------------------------------------------------------------------------------

holy_fire_206520 = spell(
    id=206520, name='Holy Fire', school=School.HOLY, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=_HOLY_FIRE_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE,
                    base_points=_HOLY_FIRE_TICK - 1, die_sides=1, amplitude=1000,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_HOLY_FIRE,
    notes=f'{_GF}, GF1: Holy Fire, every 8 s from 5 s on a random non-tank (heroic: three different non-tanks every '
          '12 s), cast by Galford (triggered): a 6 s burn, 10% of the reference row over the 6 s (6 ticks of 167 '
          'hundredths, heroic the same in MiscValueB; spell_dungeon_refflat_periodic; the tank row on a tank), not '
          'avoidable. He fights on while the target moves. A 4 yd circle follows the target for the burn and lands '
          'where they stand when it ends (DungeonKit::FollowThenLand, with the drop spot rule for a bot carrier): 30% '
          '+ Weakened to anyone else inside (206521), then a 4 yd puddle. No dispel type (ST: a dispel that dropped '
          'the fire early would land it on the group). Dropped on a logout or a map change. Holy Fire 14914\'s SV '
          '3400.',
    raw_overrides=kit_raw('Holy fire burns the target. When it ends, the fire falls where they stand.',
                          'Burning. When it ends, holy fire falls where you stand: take it behind the group.',
                          CastingTimeIndex=1, EffectMiscValueB_1=_HOLY_FIRE_TICK, SpellVisualID_1=GF_HOLY_FIRE,
                          AttributesEx=_ATTR1_NO_THREAT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(holy_fire_206520, 'spell_dungeon_refflat_periodic')

holy_fire_landing_206521 = resolve_copy(
    206521, 'Holy Fire', School.HOLY, 'Holy fire falls to the floor.',
    f'{_GF}, GF2: the Holy Fire circle lands (4 yd where the target stands when the burn ends): 30% of the row + '
    'Weakened to anyone else inside, through the registry (the circle never hits the player it follows). Copy of the '
    'resolve spell 205002 (Holy). Holy Fire 14914\'s SV 3400 on every unit hit (the visible impact); the puddle look '
    'is the stalker\'s.',
    icon=_ICON_HOLY_FIRE, visual=GF_HOLY_FIRE,
)

# --- GF3 Pyroblast ----------------------------------------------------------------------------------------------------

pyroblast_206522 = spell(
    id=206522, name='Pyroblast', school=School.FIRE, dispel=0, mechanic=0, attributes=_ATTR0_NO_ACTIVE_DEFENSE,
    cast_time_ms=_PYRO_CAST_MS, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=40.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
                    potency_excluded=_SCRIPT_OWN)],
    spell_icon_id=_ICON_PYROBLAST,
    notes=f'{_GF}, GF3: Pyroblast, every 20 s from 15 s, a 4 s cast at the tank (stock 17274: 6 s). Kickable: '
          'InterruptFlags 15 and PreventionType 1 (the descriptor\'s interrupt list, priority 3: a reward on normal, '
          'expected on heroic). Lands for 35% (heroic 45%) of the tank row on the tank, not avoidable, x 1.25 while he '
          'is Kindled (his custom hits ignore caster modifiers, so the script adds it): spell_st_galford_pyroblast '
          'sets the value at launch (DungeonKit::RefFlatOn). The hit leaves a 6 yd (heroic 8 yd) puddle where the '
          'tank stands. Always hits, cannot crit, no reflection or redirection. Stock Pyroblast\'s SV 2253 (fire '
          'hands, the PyroBlast missile at 24 yd/s, a molten impact).',
    raw_overrides=kit_raw('Hurls a fiery boulder at the enemy. Where it lands, holy fire stays on the floor.',
                          InterruptFlags=_INTERRUPT_FLAGS_STANDARD, PreventionType=_PREVENTION_SILENCE,
                          DefenseType=_DEFENSE_MAGIC, Speed=_PYRO_SPEED, SpellVisualID_1=GF_PYROBLAST,
                          AttributesEx=_ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION,
                          AttributesEx2=_ATTR2_CANT_CRIT,
                          AttributesEx3=_ATTR3_NOT_A_PROC | _ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS),
)
scripted_by(pyroblast_206522, 'spell_st_galford_pyroblast')

# --- GF5 Fire Nova ----------------------------------------------------------------------------------------------------

fire_nova_cast_206523 = cast_bar(
    206523, 'Fire Nova', _NOVA_CAST_MS, 'His robes kindle with holy flame.',
    f'{_GF}, GF5: the 2 s windup, every 15 s from 12 s (emote line 1, a 10 yd ring marker on him); he stands still '
    'while he casts. Not kickable (cast_bar): the registry circle on him owns the hit (206524). Stock Fire Nova '
    '17366 was instant. No look of its own: the burst has the ring (206525).',
    icon=_ICON_FIRE_NOVA, school=School.FIRE,
)

fire_nova_206524 = resolve_copy(
    206524, 'Fire Nova', School.FIRE, 'A ring of fire bursts from him.',
    f'{_GF}, GF5: the burst: 30% of the row + Weakened in 10 yd around him, the tank too (its own row), through the '
    'registry. Copy of the resolve spell 205003 (Fire). Stock Fire Nova\'s SV 963 on every unit hit (fire hands, the '
    'FireNova ring, its state). Then a 5 yd puddle under his feet.',
    icon=_ICON_FIRE_NOVA, visual=GF_FIRE_NOVA,
)

fire_nova_look_206525 = spell(
    id=206525, name='Fire Nova', school=School.FIRE, attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_FIRE_NOVA,
    notes=f'{_GF}, GF5: the burst\'s look on Galford, cast by him on himself (triggered) when the ring resolves, '
          'whether it hit anyone or not. Stock Fire Nova 17366\'s SV 963 (the FireNova_Area ring). Look only.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=GF_FIRE_NOVA, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- GF7 / GF8 holy fire and Scorched ---------------------------------------------------------------------------------

holy_fire_tick_206526 = spell(
    id=206526, name='Holy Fire', school=School.HOLY, dispel=0, mechanic=0, attributes=_ATTR0_NO_ACTIVE_DEFENSE,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded=_SCRIPT_OWN)],
    spell_icon_id=_ICON_CONSECRATION,
    notes=f'{_GF}, GF7: the holy fire on the floor. Once a second, each player standing in any armed puddle (the '
          'PuddleField union: overlapping puddles burn once) takes 8% of the reference row x (1 + 0.25 x their '
          'Scorched stacks before this tick), cast by Galford (triggered); then the tick adds a stack (206527). '
          'spell_st_galford_holy_fire_tick sets the value at launch (DungeonKit::RefFlatOn): 8, 10, 12, ... so '
          'crossing one puddle costs about 18% and eight seconds in it kill. Combustion 11129\'s SV 7634 (fire ribbons '
          'on the chest) on the player burned: the visible impact.',
    raw_overrides=kit_raw('Holy fire burns everything that stands in it.', instant=True, DefenseType=_DEFENSE_MAGIC,
                          InterruptFlags=0, PreventionType=0, SpellVisualID_1=GF_COMBUSTION_FLASH,
                          AttributesEx=_ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION | _ATTR1_NO_THREAT,
                          AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
                          AttributesEx3=_ATTR3_NOT_A_PROC | _ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(holy_fire_tick_206526, 'spell_st_galford_holy_fire_tick')

scorched_206527 = spell(
    id=206527, name='Scorched', school=School.HOLY, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_SCORCHED_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_IMMOLATE,
    notes=f'{_GF}, GF8: Scorched. Each holy fire tick a player takes adds a stack (DungeonKit::AddStacks, caster '
          'Galford, CumulativeAura 20; every new stack refreshes the 4 s), so all of them fall off 4 s after the '
          'player leaves the fire. Each stack raises the holy fire tick by 25% (the tick\'s script reads the count). '
          'A DUMMY debuff: the count is the tell. Dispel none, lands through immunities; dropped on a logout or a map '
          'change, removed with the fight. No look of its own (the tick carries the flash).',
    raw_overrides=kit_raw('Scorched by holy fire. Holy fire burns you harder for every stack.',
                          'Holy fire burns you harder for every stack.', CastingTimeIndex=1,
                          CumulativeAura=_SCORCHED_MAX, AttributesEx=_ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- GF9 Kindled ------------------------------------------------------------------------------------------------------

kindled_206528 = spell(
    id=206528, name='Kindled', school=School.HOLY, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=_KINDLED_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE,
                    base_points=_KINDLED_DONE, die_sides=0, misc_value=_SCHOOL_MASK_ALL,
                    implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Kindled: a flat +25% damage done, not a damage or heal value'),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN,
                    base_points=_KINDLED_TAKEN, die_sides=0, misc_value=_SCHOOL_MASK_ALL,
                    implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Kindled: a flat -50% damage taken, not a damage or heal value')],
    spell_icon_id=_ICON_IMMOLATE,
    notes=f'{_GF}, GF9: Kindled. While Galford stands in armed holy fire the AI puts it on him (cast on himself, '
          'triggered, every 250 ms while he is in it), so it ends about 1 s after he leaves: +25% damage done (his '
          'melee; '
          'his custom hits ignore caster modifiers, so Pyroblast\'s script adds the 25% itself) and -50% damage '
          'taken, every school. The first one each pull: yell line 2. Not dispellable or stealable (a boss buff the '
          'tank answers by moving him). Immolate 348\'s SV 46 (the Immolate state flame on him).',
    raw_overrides=kit_raw('The Light\'s fire feeds him.', 'Damage dealt increased by $s1%. Damage taken reduced.',
                          instant=True, SpellVisualID_1=GF_KINDLED, AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- GF11 Burning Winds (heroic) --------------------------------------------------------------------------------------

burning_winds_206529 = cast_bar(
    206529, 'Burning Winds', _WINDS_CAST_MS, 'A burning gust blows down the hall toward the Pyre.',
    f'{_GF}, GF11 heroic: Burning Winds (the stock name, a new job), every 25 s from 20 s: the 2 s cast (yell line 5). '
    'While he casts, every puddle reaches 8 yd north as a telegraph-only zone (the bots stand where the throw lands '
    'on clean floor); when it ends everyone, the tank too, is thrown 8 yd south (no damage; about a 1 s flight). A '
    'throw stops 2 yd short of the Pyre\'s strip (the lethal wall strikes any crossing). Not kickable (cast_bar). '
    'Stock Burning Winds 17293 (the 8 s stun) is retired.',
    icon=_ICON_BURNING_WINDS, school=School.FIRE,
)

gust_206530 = spell(
    id=206530, name='Burning Winds', school=School.FIRE, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_GUST_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_BURNING_WINDS,
    notes=f'{_GF}, GF11 heroic: the gust\'s look on each player it throws, cast by Galford (triggered) with the '
          'throw (Unit::KnockbackFrom, from the script: 8 yd south, cut short of the Pyre). A 1 s DUMMY debuff whose '
          'StateKit is stock Burning Winds\' SV 4486 (a fire twister; a state kit needs an aura to carry it). Dispel '
          'none; dropped on a map change.',
    raw_overrides=kit_raw('Thrown by a burning gust.', 'Thrown toward the Pyre.', CastingTimeIndex=1,
                          SpellVisualID_1=GF_BURNING_WINDS, AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)


# --- GF7 / GF10 the stalkers' looks -----------------------------------------------------------------------------------

def _state_look(spell_id: int, name: str, visual: int, icon: int, notes: str):
    # Not passive: a passive aura is never sent to the client, so its state visual would not show (custom-spells.md).
    return spell(
        id=spell_id, name=name, school=School.HOLY, dispel=0, mechanic=0,
        attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(SpellVisualID_1=visual, AttributesEx4=ATTR4_NO_CAST_LOG, CastingTimeIndex=1),
    )


def _puddle_look(spell_id: int, visual: int, size: str):
    return _state_look(
        spell_id, 'Holy Fire', visual, _ICON_CONSECRATION,
        f'{_GF}, GF7: the look of a {size} holy fire puddle. The puddle stalker 300606 casts it on itself (triggered) '
        'when it is summoned and keeps it until it despawns (his death or a wipe): a hidden DUMMY aura whose StateKit '
        f'is V-2\'s HolyZone gold disc ({visual}) sized to the radius. The registry\'s persistent zone (PuddleField) '
        'draws the marker; the AI deals the tick.',
    )


puddle_look_4_206531 = _puddle_look(206531, SV_HOLYZONE_4_STATE, '4 yd (Holy Fire\'s landing)')
puddle_look_5_206532 = _puddle_look(206532, SV_HOLYZONE_5_STATE, '5 yd (Fire Nova\'s)')
puddle_look_6_206533 = _puddle_look(206533, SV_HOLYZONE_6_STATE, '6 yd (Pyroblast\'s, normal)')
puddle_look_8_206534 = _puddle_look(206534, SV_HOLYZONE_8_STATE, '8 yd (Pyroblast\'s, heroic)')

wall_look_206535 = _state_look(
    206535, 'The Pyre', GF_FIRE_WALL, _ICON_FIRE_WALL,
    f'{_GF}, GF10: the walls\' fire. At the pull a row of Pyre stalkers 300607 (one every 6 yd or less) stands along '
    'the Pyre (x 3444, the hall\'s south end) and the north wall (x 3500); each casts it on itself (triggered) and '
    'keeps it until the fight ends. Fire Wall 43113\'s SV 9701 (Missile_Wave_Fire, about 6 yd, as a state). The '
    'lethal wall itself (marker, strike) is the kit\'s DungeonKit::LethalWall with the shared 206400.',
)
