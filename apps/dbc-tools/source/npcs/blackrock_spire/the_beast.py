"""
Blackrock Spire build WP-B13: The Beast (10430), "a monster so bad its keepers kill themselves"
(.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.4 rows BE, s3.5 row B13, s3.6; build spec
docs/dungeons/blackrock-spire-rework.md SP 3465-3698, BE1-BE10, rulings 65-67). WP-B13 owns this file (its spells:
kSpellsBeast 210490-210519 in modules/mod-dungeon-bosses src/BlackrockSpire/BlackrockSpireRework.h only;
BeastLogic.h names the same ids). The engine side is src/BlackrockSpire/boss_the_beast_rework.cpp.

- 10430 The Beast: boss_the_beast_rework (no SmartAI: the stock boss is C++ only), the build spec's normal health (220k
  = HealthModifier 67.964 on the level 62 warrior class base 3,237), stun immunity 1972, INSTANCE_BIND, the stock
  DamageModifier 3.5 (the live 10 is a mod-progression leftover; WP-T tunes it). Heroic 235k is WP-H's override. The
  stock Flamebreak 16785, Terrifying Roar 14100, Berserker Charge 16636 and Fireball 16788 are no longer cast (the
  script is new); Immolate 15570 and Fire Blast 16144 stay. His loot is L-2's.
- 300735 Molten Blood: an invisible, unselectable prop (KIT_HELPER, no heroic template) the script summons on each pool
  of lava; it carries the pool's look (210502-210508 by radius). npc_brs_molten_blood (a NullCreatureAI).
- His three boss emotes (creature_text 10430 groups 0-2) are the core SQL rev rev_the_beast_blackrock_spire.sql.

Spells. The registry hits (Magma Split) deal their damage through dungeon copies of the mod-boss-mechanics resolve
spell; the lava, the Eruption and Immolate's burn are the kit's generic percent spells (spell_dungeon_refflat_damage /
_periodic), each a percent of the reference row in hundredths in the effect; the rest are auras, cast bars and looks:

  210490  Heat             BE2 +10% damage done a stack, no cap, on him for the fight
  210491  Molten Fury      BE4 +10% damage done a stack while he stands in lava, no cap, on him for the fight
  210492  Terrifying Roar  BE5 the 2 s roar (a cast bar, not interruptible; emote line 0)
  210493  Dread            BE5 a stack for standing alone in the roar, 30 s after the last, up to 3
  210494  Panic            BE5 the 2 s flee at 3 stacks (heroic 2)
  210495  Magma Split      BE6 the 2 s cast bar (not interruptible)
  210496  Magma Split      BE6 the others' hit: resolve copy, Fire, 30% + Weakened (the script raises it with Heat)
  210497  Magma Split      BE6 the target's own hit: resolve copy, Fire, 15%
  210498  Molten Blood     BE3 a second in lava: 10% Fire (once, however many pools overlap)
  210499  Eruption         BE7 a second on the erupted floor: 10% Fire to everyone
  210500  Immolate         BE8 heroic: 3% Fire a second for 21 s, a Magic dispel; a pool where it runs out
  210501  Heat             BE2 the chest flash at each new stack (look only)
  210502-210508  Molten Blood  BE3 the pool's look on its stalker, 4 to 10 yd rungs (V-2's SV_MAGMA_POOL_STATE)
  210509-210519 spare

Visual ids are V-2's (._visuals BE_*, SV_MAGMA_POOL_STATE); every look is unconfirmed until seen in game. Tooltips are
number-free (SP checklist item 8).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_THREAT,
    RESOLVE_RAW,
    self_visual,
)
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
    BE_HEAT,
    BE_HEAT_ALT,
    BE_HEAT_STACK_FLASH,
    BE_MAGMA_SPLIT,
    BE_ROAR,
    DISPLAY_INVISIBLE_STALKER,
    MAGMA_POOL_RADII,
    SV_MAGMA_POOL_STATE,
    VG_FIRE_BLAST_IMPACT,
)

_B13 = 'Blackrock Spire build WP-B13 (The Beast)'

_TARGET_UNIT_TARGET_ENEMY = 6
_MECHANIC_FEAR = 5
_DISPEL_MAGIC = 1
_DEFENSE_MAGIC = 1
_SCHOOL_MASK_ALL = 127
# AURA_INTERRUPT_FLAG_CHANGE_MAP (SpellDefines.h): a map change or a logout drops it, so nothing outlives the instance.
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000

# Icons (the working-copy Spell.dbc).
_ICON_FIRE_SHIELD = 31              # Fire Shield 35265 / Immolate
_ICON_FEAR = 148                    # Intimidating Roar 16508
_ICON_FIRE_NOVA = 33                # Fire Nova 17366

# Numbers (BeastLogic.h).
_HEAT_DAMAGE_PCT = 10               # kHeatDamagePct
_FURY_DAMAGE_PCT = 10               # kFuryDamagePct
_STACK_MAX = 255                    # the aura counter's limit: no cap
_ROAR_CAST_MS = 2000                # kRoarCastMs
_DREAD_MS = 30000                   # kDreadMs
_DREAD_MAX_STACKS = 3               # kDreadMaxStacks (the script panics at 3, heroic 2)
_PANIC_MS = 2000                    # kPanicMs
_SPLIT_CAST_MS = 2000               # kSplitCastMs
_LAVA_TICK_HUNDREDTHS = 1000        # kPoolTickPct: 10% of the reference row
_ERUPTION_TICK_HUNDREDTHS = 1000    # kEruptionPct: 10%
_IMMOLATE_TICK_HUNDREDTHS = 300     # kImmolateTickPct: 3% a second
_IMMOLATE_MS = 21000                # kImmolateMs (the stock Immolate's duration)

_PERCENT_EXCLUDED = ('Blackrock Spire: a percent of reference health in hundredths, set at launch by the kit\'s '
                     'spell_dungeon_refflat_* (DungeonKit::RefFlatOn)')

# The hits whose damage the script sets carry the resolve attribute set (no active defense, redirection, reflection or
# threat; ignore line of sight; cannot crit; not a proc; always hit; ignore caster modifiers).
_SCRIPT_HIT_RAW = {k: v for k, v in RESOLVE_RAW.items() if k != 'CastingTimeIndex'}

# Held back until wave 2 binds this boss (_common.py BIND_WAVE_2): stock until then.
if BIND_WAVE_2:
    creature_template_columns(10430, **boss_columns(
        'boss_the_beast_rework', 67.964, damage_modifier=3.5,
    ))

# --- 300735 Molten Blood (the pool's stalker) ------------------------------------------------------------------------

molten_blood_300735 = creature_template(
    300735, 'Molten Blood', **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1,
                               'ScriptName': 'npc_brs_molten_blood'},
)
creature_model(300735, display_id=DISPLAY_INVISIBLE_STALKER)

# --- BE2 Heat, BE4 Molten Fury ---------------------------------------------------------------------------------------


def _damage_aura(spell_id: int, name: str, pct: int, visual: int, notes: str, desc: str, aura_desc: str):
    return spell(
        id=spell_id, name=name, school=School.FIRE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=pct,
                        die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                        potency_excluded=f'{name}: a flat +10% damage done per stack, not a damage or heal value')],
        spell_icon_id=_ICON_FIRE_SHIELD, notes=notes,
        raw_overrides=kit_raw(desc, aura_desc, instant=True, CumulativeAura=_STACK_MAX, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=visual),
    )


heat_210490 = _damage_aura(
    210490, 'Heat', _HEAT_DAMAGE_PCT, BE_HEAT,
    f'{_B13}, BE2 Heat: a stack on him every 20 s (heroic 15 s) from the pull, no cap (CumulativeAura 255, '
    'DungeonKit::AddStacks, the boss as caster): +10% damage done per stack, every school, so it raises his melee, '
    'Fire Blast and Immolate; the custom percent hits ignore caster modifiers, so the script adds the 10% a stack to '
    'Magma Split itself (DamageMult). The script also reads the count for the pools\' size (half a yard a stack) and '
    'for the roar\'s cadence (3 stacks) and Magma Split\'s (5). Not dispellable; removed on his death, evade and '
    'reset. '
    'Fire Shield 35265\'s whirl (SV 8581, V-2\'s BE_HEAT: the lasting look).',
    'The blood boils: damage done grows with every stack.', 'Damage done increased.',
)

molten_fury_210491 = _damage_aura(
    210491, 'Molten Fury', _FURY_DAMAGE_PCT, BE_HEAT_ALT,
    f'{_B13}, BE4 Molten Fury: a stack on him for every 2 s of unbroken time he stands in his own lava (the puddle '
    'field\'s Contains, polled every 250 ms), no cap, kept to the end of the fight: +10% damage done per stack, as '
    'Heat (the same ignore-caster-modifiers rule). Not dispellable; removed on his death, evade and reset. Emberseer '
    'Growing 16048\'s SV 3946 (V-2\'s BE_HEAT_ALT: the stock growth state).',
    'Standing in his own lava feeds him: damage done grows with every stack.', 'Damage done increased.',
)

heat_flash_210501 = self_visual(
    210501, 'Heat', BE_HEAT_STACK_FLASH,
    f"{_B13}, BE2: the chest flash at each new Heat stack, cast by him on himself (triggered). Lava Shield 21858's SV "
    '1465 (V-2\'s BE_HEAT_STACK_FLASH: a 1.5 s flash, only as the flash). Look only.',
    icon=_ICON_FIRE_SHIELD, school=School.FIRE,
)

# --- BE5 Dread and Panic ---------------------------------------------------------------------------------------------

roar_210492 = cast_bar(
    210492, 'Terrifying Roar', _ROAR_CAST_MS, 'The Beast rears back to roar.',
    f"{_B13}, BE5: the 2 s roar every 20 s (15 s from Heat 3) from 10 s, on him (emote line 0), NOT interruptible (a "
    'set piece: the registry\'s cluster Stack owns the rule, at its end everyone with fewer than 2 other players '
    "within 6 yd gains a Dread stack). Terrifying Roar 14100's SV 247 (V-2's BE_ROAR: a small ring and fear skulls).",
    icon=_ICON_FEAR, visual=BE_ROAR,
)

dread_210493 = spell(
    id=210493, name='Dread', school=School.SHADOW, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_DREAD_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_FEAR,
    notes=f'{_B13}, BE5 Dread: a stack for every roar a player stands alone in (fewer than 2 other players within 6 '
          'yd; the tank counts like anyone), the boss as caster (DungeonKit::AddStacks, CumulativeAura 3), every new '
          'stack refreshing the 30 s, so it fades 30 s after the last. At 3 stacks (heroic 2: the script caps the '
          'count) the stacks clear and the player panics (210494). A DUMMY debuff: the count is the tell. Dispel '
          'none, lands through immunities; dropped on a logout or a map change, removed with the fight. Terrifying '
          "Roar 14100's SV 247 (V-2's BE_ROAR: the fear skulls on the aura target).",
    raw_overrides=kit_raw('Terror of standing alone: stand near your allies when he roars. Too many stacks and you '
                          'panic.', 'Terror of standing alone.', CastingTimeIndex=1, CumulativeAura=_DREAD_MAX_STACKS,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=BE_ROAR,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

panic_210494 = spell(
    id=210494, name='Panic', school=School.SHADOW, dispel=0, mechanic=_MECHANIC_FEAR,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=_PANIC_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_FEAR, base_points=0,
                    mechanic=_MECHANIC_FEAR, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_FEAR,
    notes=f'{_B13}, BE5 Panic: the flee of a player who panics like the Elites did (the script, at the Dread '
          'threshold): 2 s, the shared limit on loss of control. Mechanic Fear and not NO_IMMUNITIES, so a fear break '
          '(Fear Ward, Berserker Rage, Will of the Forsaken, Tremor Totem) is a reward. Dispel none: 2 s is not worth '
          'a cure. The danger is where they run: lava. No look of its own (the stock fear state). AuraInterruptFlags '
          'CHANGE_MAP.',
    raw_overrides=kit_raw('Panics and runs in fear for $d.', 'Running in panic.', CastingTimeIndex=1,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- BE6 Magma Split -------------------------------------------------------------------------------------------------

split_bar_210495 = cast_bar(
    210495, 'Magma Split', _SPLIT_CAST_MS, 'The Beast splits the floor with magma.',
    f"{_B13}, BE6: the 2 s cast every 20 s (15 s from Heat 5) from 20 s, on him, NOT interruptible (a set piece: the "
    'registry\'s circle on each picked non-tank owns the hit). Flamebreak 16785\'s SV 4321 (V-2\'s BE_MAGMA_SPLIT: '
    'fire hands, a nova ring and a fire spiral; the spiral\'s width is unconfirmed).',
    icon=_ICON_FIRE_NOVA, visual=BE_MAGMA_SPLIT, school=School.FIRE,
)

split_others_210496 = resolve_copy(
    210496, 'Magma Split', School.FIRE, 'Magma splits the floor.',
    f'{_B13}, BE6: the others\' hit when a Magma Split circle lands: 30% of the reference row (raised 10% for each '
    'Heat and Molten Fury stack by the script) + Weakened to every player inside 6 yd of the target but the target, '
    'the script then throws them 5 yd away. Copy of the resolve spell 205003 (Fire). Fire Blast 2136\'s SV 143 (V-2\'s '
    'VG_FIRE_BLAST_IMPACT: hands and a chest flash) on each player hit.',
    icon=_ICON_FIRE_NOVA, visual=VG_FIRE_BLAST_IMPACT,
)

split_target_210497 = resolve_copy(
    210497, 'Magma Split', School.FIRE, 'Magma splits the floor.',
    f'{_B13}, BE6: the target\'s own hit as the circle lands: 15% of the reference row (raised 10% for each Heat and '
    'Molten Fury stack by the script), no Weakened (not avoidable), through the registry (a script-picked hit). Copy '
    'of the resolve spell 205003 (Fire). The same impact as the others\' hit.',
    icon=_ICON_FIRE_NOVA, visual=VG_FIRE_BLAST_IMPACT,
)

# --- BE3 Molten Blood, BE7 Eruption ----------------------------------------------------------------------------------


def _percent_hit(spell_id: int, name: str, hundredths: int, notes: str, desc: str):
    s = spell(
        id=spell_id, name=name, school=School.FIRE, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=hundredths - 1, die_sides=1,
                        implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_PERCENT_EXCLUDED)],
        spell_icon_id=_ICON_FIRE_NOVA, notes=notes,
        raw_overrides=kit_raw(desc, **{**_SCRIPT_HIT_RAW, 'SpellVisualID_1': VG_FIRE_BLAST_IMPACT,
                                       'EffectMiscValueB_1': hundredths}),
    )
    scripted_by(s, 'spell_dungeon_refflat_damage')
    return s


lava_tick_210498 = _percent_hit(
    210498, 'Molten Blood', _LAVA_TICK_HUNDREDTHS,
    f'{_B13}, BE3: the lava on the floor. Once a second, each player standing in any armed pool (the PuddleField '
    'union: overlapping pools burn once) takes 10% of the reference row (the tank row on the tank) on both '
    'difficulties, cast by him (triggered), Fire, for the whole fight; the kit\'s spell_dungeon_refflat_damage reads '
    'the percent from the effect (shown value 1000 hundredths, EffectMiscValueB the same). Not avoidable once '
    'inside, so no Weakened; it does not rise with Heat (the lava is the floor, not a blow of his). Fire Blast 2136\'s '
    'SV 143 on the player burned: the visible impact.',
    'The floor burns.',
)

eruption_210499 = _percent_hit(
    210499, 'Eruption', _ERUPTION_TICK_HUNDREDTHS,
    f'{_B13}, BE7: the enrage. From 2:00 (heroic 1:40) the whole floor is lava: once a second the script casts it on '
    'every player in the fight (triggered), 10% of the reference row (the tank row on the tank), Fire, until the '
    'wipe; the kit\'s spell_dungeon_refflat_damage reads the percent. Fire Blast 2136\'s SV 143 on each tick.',
    'The whole floor burns.',
)

# --- BE8 Immolate (heroic) -------------------------------------------------------------------------------------------

immolate_210500 = spell(
    id=210500, name='Immolate', school=School.FIRE, dispel=_DISPEL_MAGIC, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=_IMMOLATE_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE,
                    base_points=_IMMOLATE_TICK_HUNDREDTHS, die_sides=0, amplitude=1000,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_PERCENT_EXCLUDED)],
    spell_icon_id=_ICON_FIRE_SHIELD,
    notes=f'{_B13}, BE8 (heroic only; normal casts the stock Immolate 15570): his Immolate on a random player (any '
          'role) at 3 s and every 8 s, 3% of the reference row a second (the tank row on the tank; the kit\'s '
          'spell_dungeon_refflat_periodic: 300 hundredths) for the stock 21 s, Fire, Magic: an expected dispel (the '
          'descriptor\'s dispel list, priority 3). If it runs out on a living player (not dispelled, not by death) '
          'spell_brs_beast_immolate has the boss lay a 4 yd pool under them. Ignores caster modifiers (a percent of '
          'the reference row), so Heat does not raise it. AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('Burning: taking Fire damage every $t1 sec. When it runs out a pool of lava is left under '
                          'you.', 'Burning with fire.', CastingTimeIndex=1, DefenseType=_DEFENSE_MAGIC,
                          EffectMiscValueB_1=_IMMOLATE_TICK_HUNDREDTHS, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(immolate_210500, 'spell_dungeon_refflat_periodic', 'spell_brs_beast_immolate')

# --- BE3 the pools' looks (one per 1 yd rung of V-2's ladder) --------------------------------------------------------


def _pool_look(rung: int):
    # Not passive: a passive aura is never sent to the client, so its state visual would not show (custom-spells.md).
    return spell(
        id=210502 + rung - MAGMA_POOL_RADII[0], name='Molten Blood', school=School.FIRE, dispel=0, mechanic=0,
        attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_FIRE_NOVA,
        notes=f'{_B13}, BE3: the look of a pool with a visible radius of {rung} yd. The pool stalker 300735 casts the '
              'rung nearest above the pool\'s real radius on itself (triggered) as the marker arms and keeps it until '
              'it despawns (his death, an evade or a wipe): a hidden DUMMY aura whose StateKit is V-2\'s Ascension '
              f'magmazone lava quad (SV {SV_MAGMA_POOL_STATE[rung]}), minted at this size. The registry\'s puddle '
              'field draws the exact marker and deals the tick; the glow is the look.',
        raw_overrides=kit_raw(SpellVisualID_1=SV_MAGMA_POOL_STATE[rung], AttributesEx4=ATTR4_NO_CAST_LOG,
                              CastingTimeIndex=1),
    )


pool_looks = [_pool_look(rung) for rung in MAGMA_POOL_RADII]
