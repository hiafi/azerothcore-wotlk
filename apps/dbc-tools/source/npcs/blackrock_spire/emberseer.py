"""
Blackrock Spire build WP-B10: Pyroguard Emberseer (9816), "The Furnace, with Bind Him Again's escalation"
(.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.4 rows EM, s3.5 row B10, s3.6, s3.8, s10 the
rolling front rulings; build spec docs/dungeons/blackrock-spire-rework.md SP 2523-2790, EM1-EM10, rulings 50-54).
WP-B10 owns this file (its spells: kSpellsEmberseer 210350-210389 in modules/mod-dungeon-bosses
src/BlackrockSpire/BlackrockSpireRework.h only; EmberseerLogic.h names the same ids). The engine side is
src/BlackrockSpire/boss_pyroguard_emberseer_rework.cpp.

- 9816 Pyroguard Emberseer: boss_pyroguard_emberseer_rework (no SmartAI: the stock boss is C++ only), the build spec's
  normal health (175k = HealthModifier 57.339 on the level 60 warrior class base 3,052), the immunity set 1973 (1972 +
  the Fire school, handoff s7 #16), INSTANCE_BIND, the stock DamageModifier 3.5 (the live 6 is a mod-progression
  leftover). Heroic 225k is WP-H's override. The stock Fire Nova 23462, Flame Buffet 23341, Pyroblast 17274 and the
  growth trigger 16048 are no longer cast; the growth is the stock 16049 aura (+5% size a stack) stacked by the
  script, the cage keeps the stock Encaged Emberseer 15282, Freeze Anim 16245 and the Incarcerators' channel 15281.
  His loot is L-2's (the world drop tree 1000260 stays).
- 10316 Blackhand Incarcerator: rebound to npc_blackhand_incarcerator_rework (the stock prelude without the flee at
  30%), stock health 7,500 (HealthModifier 2.5; heroic 9,500 is WP-H's override), Strike 15580 kept.
- 300730 Binding Post: an invisible, unselectable prop (KIT_HELPER, no heroic template), seven of them summoned at the
  Incarcerators' spawn spots when he breaks free; it carries the smolder, the flare column, the Encage beam and the
  eruption. npc_brs_binding_post (a NullCreatureAI).
- His four new lines (creature_text 9816 groups 4-7) are the core SQL rev rev_pyroguard_emberseer_blackrock_spire.sql.

Spells. The registry hits (the nova, the rings, Supernova, the eruptions) deal their damage through dungeon copies of
the mod-boss-mechanics resolve spell; Furnace Heat and Pyroblast's hit read his stacks in
spell_brs_emberseer_stacked_hit (a percent of the reference row, EmberseerLogic.h HitPct); Searing Bond and
Pyroblast's burn are the kit's generic percent spells (spell_dungeon_refflat_damage / _periodic); the rest are auras
and looks:

  210350  The Furnace Grows  EM4 normal: +3% damage done a stack, up to 20, on him (with the stock 16049 size stacks)
  210351  The Furnace Grows  EM4 heroic: +4% a stack
  210352  Furnace Heat       EM4 every 3 s to everyone: 0.5% + 0.1% a stack, Fire
  210353  Furnace Pulse      EM2 the nova's hit: resolve copy, Fire, 30% (raised by his stacks) + Weakened
  210354  Furnace Pulse      EM3 a ring's hit: resolve copy, Fire, 30% (raised) + Weakened
  210355  Furnace Pulse      EM2 his body flares as the nova's warning starts (look)
  210356  Flame Wave         EM3 a ring launches: on the apex stalker (look)
  210357  Fire Nova          EM2 / EM8 the burst at the nova's spot and on an erupting post (look)
  210358  Full Strength      EM5 on him at 20 stacks and at each Supernova (look)
  210359  Supernova          EM5 every 6 s at 20 stacks: resolve copy, Fire, 50% (raised), unavoidable
  210360  Pyroblast          EM9 the 6 s interruptible cast: 40% / 50% (raised) and a 12 s burn
  210361  Smoldering Post    EM6 a picked post smolders (post state)
  210362  Pillar of Fire     EM6 the flare's column (post look, re-cast at 5 s)
  210363  Encage Emberseer   EM6 a held post's 2 s beam onto him (a channel)
  210364  Searing Bond       EM7 heroic: 4% Fire a second on a flared post
  210365  Seared             EM7 heroic: 40 s, cannot fire a post
  210366  Unstable Post      EM8 heroic: an erupting post's hit, resolve copy, Fire, 30% + Weakened
  210367  Searing Bond       EM7 heroic: the holder's flame (look, 1.5 s, refreshed each second)
  210368-210389 spare

Visual ids are V-2's (._visuals EM_*); every look is unconfirmed until seen in game. Tooltips are number-free (SP
checklist item 8).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_THREAT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
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
    IMMUNITY_EMBERSEER,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_INVISIBLE_STALKER,
    EM_ENCAGE,
    EM_FIRE_NOVA,
    EM_FLARE_COLUMN,
    EM_GROWING,
    EM_PYROBLAST,
    EM_RING_LAUNCH,
    EM_SEARED,
    EM_SEARING_BOND,
    EM_SEARING_BOND_ALT,
    EM_SMOLDER,
    EM_SUPERNOVA,
    VG_FIRE_BLAST_IMPACT,
)

_B10 = 'Blackrock Spire build WP-B10 (Pyroguard Emberseer)'

_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_FLAG_UNIT = 0x2
_DEFENSE_MAGIC = 1
_PREVENTION_SILENCE = 1
_INTERRUPT_FLAGS_KICKABLE = 15
_SCHOOL_MASK_ALL = 127
_ATTR1_IS_CHANNELED = 0x00000004
_ATTR5_ALLOW_ACTION_DURING_CHANNEL = 0x00000001
# AURA_INTERRUPT_FLAG_CHANGE_MAP (SpellDefines.h): a map change or a logout drops it, so nothing outlives the instance.
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000

# Icons (the working-copy Spell.dbc).
_ICON_FIRE_NOVA = 33                # Fire Nova 23462
_ICON_GROWING = 148                 # Emberseer Growing 16049
_ICON_PYROBLAST = 184               # Pyroblast 17274
_ICON_ENCAGE = 207                  # Encage Emberseer 15281
_ICON_SEARING_PAIN = 816            # Searing Pain 5676
_ICON_FIRE_SHIELD = 31              # Fire Shield 13376

# Numbers (EmberseerLogic.h).
_STACK_MAX = 20                     # kFullStrengthStacks
_STACK_DAMAGE_PCT = (3, 4)          # kStackDamagePct normal, heroic
_PYROBLAST_CAST_MS = 6000           # kPyroblastCastMs
_PYROBLAST_SPEED = 24.0             # the stock Pyroblast 17274's missile speed
_PYROBLAST_BURN_HUNDREDTHS = 150    # kPyroblastBurnPct 1.5% a tick
_PYROBLAST_BURN_TICK_MS = 3000      # the stock burn: a tick every 3 s for 12 s
_PYROBLAST_BURN_MS = 12000          # kPyroblastBurnMs
_BEAM_MS = 2000                     # kPostBeamMs
_SEARING_BOND_HUNDREDTHS = 400      # kSearingBondPct 4%
_SEARING_STATE_MS = 1500            # re-applied every second while on a flared post
_SEARED_MS = 40000                  # kSearedMs

_PERCENT_EXCLUDED = ('Blackrock Spire: a percent of reference health in hundredths, set at launch by the kit\'s '
                     'spell_dungeon_refflat_* (DungeonKit::RefFlatOn)')
_STACKED_EXCLUDED = ('Blackrock Spire: a percent of reference health set at launch by spell_brs_emberseer_stacked_hit '
                     'from his stacks (EmberseerLogic.h HitPct, DungeonKit::RefFlatOn)')

# The hits whose damage a script sets carry the resolve attribute set (no active defense, redirection, reflection or
# threat; ignore line of sight; cannot crit; not a proc; always hit; ignore caster modifiers).
_SCRIPT_HIT_RAW = {k: v for k, v in RESOLVE_RAW.items() if k != 'CastingTimeIndex'}

# Held back until wave 2 binds this boss (_common.py BIND_WAVE_2): stock until then.
if BIND_WAVE_2:
    creature_template_columns(9816, **boss_columns(
        'boss_pyroguard_emberseer_rework', 57.339, damage_modifier=3.5, CreatureImmunitiesId=IMMUNITY_EMBERSEER,
    ))
    # The Incarcerators: the stock prelude without the flee (stock health, Strike kept).
    creature_template_columns(10316, ScriptName='npc_blackhand_incarcerator_rework', AIName='')

# --- 300730 Binding Post (the seven posts' prop) ---------------------------------------------------------------------

binding_post_300730 = creature_template(
    300730, 'Binding Post', **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1,
                               'ScriptName': 'npc_brs_binding_post'},
)
creature_model(300730, display_id=DISPLAY_INVISIBLE_STALKER)

# --- EM4 The Furnace Grows -------------------------------------------------------------------------------------------


def _growth_aura(spell_id: int, pct: int, mode: str):
    return spell(
        id=spell_id, name='The Furnace Grows', school=School.FIRE, dispel=0, mechanic=0,
        attributes=ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
        mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=pct,
                        die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                        potency_excluded=f'The Furnace Grows: a flat +{pct}% damage done per stack, not a damage or '
                                         'heal value')],
        spell_icon_id=_ICON_GROWING,
        notes=f'{_B10}, EM4 ({mode}): his growth meter, a stack with every stock Emberseer Growing 16049 stack the '
              'script adds (the cage: one every 5 s up to 8; the fight: one every 6 s, heroic 4 s, up to 20; a landed '
              f'Pyroblast +1 / +2; each held post -2, 1 at 6 or more players). +{pct}% damage done per stack, every '
              'school, so it raises his melee; the custom hits ignore caster modifiers, so the script raises the '
              'nova, the rings, Supernova and Pyroblast itself (HitPct). CumulativeAura 20 (DungeonKit::AddStacks, he '
              'is the caster). No look of its own (16049 carries the growth). Removed on his death, evade and reset.',
        raw_overrides=kit_raw('The furnace grows: damage done increases with every stack.', 'Damage done increased.',
                              instant=True, CumulativeAura=_STACK_MAX, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


growth_210350 = _growth_aura(210350, _STACK_DAMAGE_PCT[0], 'normal')
growth_heroic_210351 = _growth_aura(210351, _STACK_DAMAGE_PCT[1], 'heroic')


def _stacked_hit(spell_id: int, name: str, visual: int, notes: str, desc: str):
    s = spell(
        id=spell_id, name=name, school=School.FIRE, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=1,
                        implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_STACKED_EXCLUDED)],
        spell_icon_id=_ICON_FIRE_SHIELD, notes=notes,
        raw_overrides=kit_raw(desc, **{**_SCRIPT_HIT_RAW, 'SpellVisualID_1': visual}),
    )
    scripted_by(s, 'spell_brs_emberseer_stacked_hit')
    return s


furnace_heat_210352 = _stacked_hit(
    210352, 'Furnace Heat', VG_FIRE_BLAST_IMPACT,
    f'{_B10}, EM4: the heat of the furnace (reworked from the stock Fire Shield 13376 pulse, which dealt nothing). '
    'From the engage, every 3 s, cast by him (triggered) on every player of the fight: 0.5% of the reference row '
    'plus 0.1% '
    'per stack (the tank row on the tank), Fire, both difficulties; spell_brs_emberseer_stacked_hit reads his stacks '
    '(EmberseerLogic.h HeatPct; not raised again by the damage aura). Not avoidable, so no Weakened. Fire Blast '
    '2136\'s SV 143 (V-1\'s VG_FIRE_BLAST_IMPACT) on each player: the visible impact.',
    'The furnace\'s heat burns everyone in the hall.',
)

nova_210353 = resolve_copy(
    210353, 'Furnace Pulse', School.FIRE, 'The furnace flares outward.',
    f'{_B10}, EM2: the nova\'s hit, a circle of 7 yd plus 0.3 yd per stack on the spot he stood when the pulse began, '
    '2.5 s warning: 30% of the reference row raised 3% (heroic 4%) per stack (the tank its own row, no tank exemption: '
    'ruling 51) and 1 Weakened. Copy of the resolve spell 205003 (Fire); Fire Blast 2136\'s SV 143 on each player '
    'hit (the Fire Nova burst at the spot is 210357).',
    icon=_ICON_FIRE_NOVA, visual=VG_FIRE_BLAST_IMPACT,
)

ring_210354 = resolve_copy(
    210354, 'Furnace Pulse', School.FIRE, 'A ring of fire rolls across the hall.',
    f'{_B10}, EM3: a ring\'s hit, the rolling cone front\'s band (4 yd, 8 yd/s, 300 degrees, heroic 315) as it passes '
    'a player outside its slice: 30% of the reference row raised 3% (heroic 4%) per stack (the tank its own row) and '
    '1 Weakened. Copy of the resolve spell 205003 (Fire); Fire Blast 2136\'s SV 143 on each player hit.',
    icon=_ICON_FIRE_NOVA, visual=VG_FIRE_BLAST_IMPACT,
)

body_flare_210355 = self_visual(
    210355, 'Furnace Pulse', EM_GROWING,
    f'{_B10}, EM2: his body flares as the nova\'s 2.5 s warning starts (cast by him on himself, triggered). Emberseer '
    'Growing 16049\'s SV 3947 (V-2\'s EM_GROWING: a glow star and a smoke puff at the base). Look only.',
    icon=_ICON_FIRE_NOVA, school=School.FIRE,
)

ring_launch_210356 = self_visual(
    210356, 'Flame Wave', EM_RING_LAUNCH,
    f'{_B10}, EM3: a ring launches. Cast (triggered) by the pulse\'s look stalker (the generic stalker 300713, '
    'summoned on the apex for the pulse) on itself at each ring\'s launch. Flame Wave 75413\'s SV 13372 (V-2\'s '
    'EM_RING_LAUNCH: '
    'rune base and a FireNova x4 shockwave; RISKY, plausible). Look only: the front\'s marker is the telegraph.',
    icon=_ICON_FIRE_NOVA, school=School.FIRE,
)

fire_nova_210357 = self_visual(
    210357, 'Fire Nova', EM_FIRE_NOVA,
    f'{_B10}, EM2 / EM8: the Fire Nova burst, cast (triggered) by the pulse\'s look stalker on the nova\'s spot as it '
    'erupts, and by an Unstable Post (heroic) as it erupts. Fire Nova 23462\'s SV 6899 (V-2\'s EM_FIRE_NOVA). Look '
    'only.',
    icon=_ICON_FIRE_NOVA, school=School.FIRE,
)

full_strength_210358 = self_visual(
    210358, 'Emberseer Full Strength', EM_SUPERNOVA,
    f'{_B10}, EM5: on him as he reaches 20 stacks (line 6) and at each Supernova (cast on himself, triggered). '
    'Emberseer Full Strength 16047\'s SV 3944 (V-2\'s EM_SUPERNOVA: a blue arcane dome and a fire ring; off-tone, '
    'stock). Look '
    'only.',
    icon=_ICON_FIRE_NOVA, school=School.FIRE,
)

supernova_210359 = resolve_copy(
    210359, 'Supernova', School.FIRE, 'The furnace burns at full strength.',
    f'{_B10}, EM5: the enrage. Every 6 s while he holds 20 stacks, through DungeonKit::RegistryHit on every player of '
    'the fight: 50% of the reference row raised 3% (heroic 4%) per stack (the tank its own row), unavoidable, so no '
    'Weakened. Held posts pulling him under 20 end it. Copy of the resolve spell 205003 (Fire); Fire Nova 23462\'s SV '
    '6899 on each player (the dome on him is 210358).',
    icon=_ICON_FIRE_NOVA, visual=EM_FIRE_NOVA,
)

# --- EM9 Pyroblast ---------------------------------------------------------------------------------------------------

pyroblast_210360 = spell(
    id=210360, name='Pyroblast', school=School.FIRE, dispel=0, mechanic=0, cast_time_ms=_PYROBLAST_CAST_MS,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=_PYROBLAST_BURN_MS,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=1,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_STACKED_EXCLUDED),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE,
                    base_points=_PYROBLAST_BURN_HUNDREDTHS, die_sides=0, amplitude=_PYROBLAST_BURN_TICK_MS,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_PERCENT_EXCLUDED)],
    spell_icon_id=_ICON_PYROBLAST,
    notes=f'{_B10}, EM9: the stock 6 s Pyroblast as his own copy, at 12 s after the engage, then every 20 s, at a '
          'random non-tank (the script, not triggered: the bar shows). Interruptible and silence-preventable '
          '(InterruptFlags 15, PreventionType silence; his immunity set 1973 holds no interrupt or silence): the '
          'descriptor\'s interrupt list, priority 2 normal (a reward), 3 heroic (expected). Fire, the only bar he '
          'casts, so a kick locks nothing else. Landed: 40% (heroic 50%) of the reference row raised 3% (heroic 4%) '
          'per stack (spell_brs_emberseer_stacked_hit, the tank row on the tank) and the stock burn as a percent: '
          '1.5% every 3 s for 12 s (spell_dungeon_refflat_periodic, 150 hundredths both difficulties); a landed hit '
          'feeds him +1 (heroic +2) stacks (the stacked-hit script\'s hit, line 5). Ignores caster modifiers. The '
          'stock missile and impact (Pyroblast 17274\'s SV 2253, V-2\'s EM_PYROBLAST) at the stock 24 yd/s. AuraInterruptFlags '
          'CHANGE_MAP.',
    raw_overrides=kit_raw('Hurls an immense fiery boulder: heavy Fire damage and a burn. Landed, the flames feed him.',
                          'Burning.', InterruptFlags=_INTERRUPT_FLAGS_KICKABLE,
                          PreventionType=_PREVENTION_SILENCE, DefenseType=_DEFENSE_MAGIC, Speed=_PYROBLAST_SPEED,
                          Targets=_TARGET_FLAG_UNIT, EffectMiscValueB_2=_PYROBLAST_BURN_HUNDREDTHS,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS | ATTR3_ALWAYS_HIT,
                          SpellVisualID_1=EM_PYROBLAST, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(pyroblast_210360, 'spell_brs_emberseer_stacked_hit', 'spell_dungeon_refflat_periodic')

# --- EM6 Binding Posts: the looks ------------------------------------------------------------------------------------

smolder_210361 = spell(
    id=210361, name='Smoldering Post', school=School.FIRE, dispel=0, mechanic=0,
    attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_FIRE_NOVA,
    notes=f'{_B10}, EM6 step 1 (the smolder): a picked post smolders from the pulse\'s nova warning until it flares '
          '(about 4 to 7 s; the script removes it). Cast by the Binding Post 300730 on itself (triggered): a hidden '
          'DUMMY aura whose StateKit is Smoldering Flames 48454\'s SV 10775 (V-2\'s EM_SMOLDER: a lasting Base state; '
          'RISKY). Not passive (a passive aura is never sent to the client).',
    raw_overrides=kit_raw(SpellVisualID_1=EM_SMOLDER, AttributesEx4=ATTR4_NO_CAST_LOG, CastingTimeIndex=1),
)

flare_column_210362 = self_visual(
    210362, 'Pillar of Fire', EM_FLARE_COLUMN,
    f'{_B10}, EM6 step 2 (the flare): the column of fire on a flared post, seen across the hall, cast by the post on '
    'itself (triggered) as the 8 s window opens and again 5 s later (a 6 s one-shot). Cosmetic - Pillar of Fire '
    '43541\'s SV 9727 (V-2\'s EM_FLARE_COLUMN). Look only: the registry\'s 3 yd get-in circle and its fill are the '
    'telegraph.',
    icon=_ICON_FIRE_NOVA, school=School.FIRE,
)

encage_beam_210363 = spell(
    id=210363, name='Encage Emberseer', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_BEAM_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_ENCAGE,
    notes=f'{_B10}, EM6 step 3 (the fire): a held post locks the stock cage beam onto him for 2 s as he loses its '
          'stacks: channeled by the Binding Post at him (triggered). Encage Emberseer 15281\'s SV 3943 (V-2\'s '
          'EM_ENCAGE: ManaBeam from the caster\'s hand and the state on him; the stalker\'s attach point is '
          'unchecked). IS_CHANNELED + NO_THREAT, ignores LoS, always hits, ALLOW_ACTION_DURING_CHANNEL, no interrupt '
          'flags. Physical, so his Fire immunity does not refuse it. Look only.',
    raw_overrides=kit_raw('The binding post holds the furnace.', 'Bound.', CastingTimeIndex=1, InterruptFlags=0,
                          AuraInterruptFlags=0, ChannelInterruptFlags=0,
                          AttributesEx=_ATTR1_IS_CHANNELED | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AttributesEx5=_ATTR5_ALLOW_ACTION_DURING_CHANNEL,
                          SpellVisualID_1=EM_ENCAGE),
)

# --- EM7 Searing Bond and Seared, EM8 Unstable Posts (heroic) --------------------------------------------------------

searing_bond_210364 = spell(
    id=210364, name='Searing Bond', school=School.FIRE, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=_SEARING_BOND_HUNDREDTHS - 1, die_sides=1,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_PERCENT_EXCLUDED)],
    spell_icon_id=_ICON_SEARING_PAIN,
    notes=f'{_B10}, EM7 (heroic): holding a flared post burns. Once a second through the 8 s window, cast by him '
          '(triggered) on everyone standing in a binding post\'s 3 yd circle: 4% of the reference row (the tank row '
          'on the tank; up to 32% over the window), Fire; the kit\'s spell_dungeon_refflat_damage reads the percent '
          '(shown value 400 hundredths, EffectMiscValueB the same). Not raised by his stacks (the post\'s fire). '
          'Searing Pain 5676\'s SV 945 (V-2\'s EM_SEARING_BOND_ALT: a 1.1 s impact, re-cast every second).',
    raw_overrides=kit_raw('The binding post\'s fire burns its holder.',
                          **{**_SCRIPT_HIT_RAW, 'SpellVisualID_1': EM_SEARING_BOND_ALT,
                             'EffectMiscValueB_1': _SEARING_BOND_HUNDREDTHS}),
)
scripted_by(searing_bond_210364, 'spell_dungeon_refflat_damage')

seared_210365 = spell(
    id=210365, name='Seared', school=School.FIRE, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_SEARED_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_SEARING_PAIN,
    notes=f'{_B10}, EM7 (heroic): a post that fires leaves its eligible holders Seared for 40 s (cast by him, '
          'triggered): they cannot fire a post (the Soak\'s eligibility, maxStacks 0 of this aura, Urok\'s check), '
          'so holders trade in pairs. A DUMMY debuff: the icon and the clock are the tell. Dispel none, lands through '
          'immunities; dropped on a logout or a map change, removed with the fight. Fire Reflector 23097\'s SV 6764 '
          '(V-2\'s EM_SEARED: lasting red ribbons on the chest).',
    raw_overrides=kit_raw('Seared by a binding post: it cannot be held again until this fades.', 'Cannot hold a post.',
                          CastingTimeIndex=1, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          SpellVisualID_1=EM_SEARED, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

unstable_post_210366 = resolve_copy(
    210366, 'Unstable Post', School.FIRE, 'An unstable post erupts.',
    f'{_B10}, EM8 (heroic): an erupting post\'s hit, a 6 yd circle on 2 posts that are not flaring (3 at 6 or more '
    'players), 8 s warning from the flare, erupting as the binding posts fire: 30% of the reference row (the tank its '
    'own row) and 1 Weakened; not raised by his stacks (the post\'s fire). Copy of the resolve spell 205003 (Fire); '
    'Fire Blast 2136\'s SV 143 on each player hit (the post\'s Fire Nova burst is 210357).',
    icon=_ICON_FIRE_NOVA, visual=VG_FIRE_BLAST_IMPACT,
)

searing_state_210367 = spell(
    id=210367, name='Searing Bond', school=School.FIRE, dispel=0, mechanic=0,
    attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_SEARING_STATE_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_SEARING_PAIN,
    notes=f'{_B10}, EM7 (heroic): the holder\'s flame, re-applied with every Searing Bond tick (1.5 s, so it lasts '
          'while they stand on the post and fades a moment after). A hidden DUMMY aura whose StateKit is Burning '
          'Brand 29618\'s SV 1946 (V-2\'s EM_SEARING_BOND: StateKit 235, a lasting flame state). AuraInterruptFlags '
          'CHANGE_MAP. Look only.',
    raw_overrides=kit_raw(CastingTimeIndex=1, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          SpellVisualID_1=EM_SEARING_BOND, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
