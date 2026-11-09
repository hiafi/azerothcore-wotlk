"""
Stratholme build WP-S3: Timmy the Cruel (10808), normal and heroic
(.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.4 rows TC, s3.5 row S3, s3.6; build spec
docs/dungeons/stratholme-rework.md ST 1035-1090, design ST 886-1034). WP-S3 owns this file (its spells: kSpellsTimmy
206460-206479 of modules/mod-dungeon-bosses src/Stratholme/StratholmeRework.h only; TimmyLogic.h names the same ids;
its creature: the Playmate 300604).

- 10808 Timmy the Cruel: boss_timmy_the_cruel_rework (SmartAI off; WP-S3's SQL rev drops the seven stock rows, the
  emerge actionlist 1080800 and the gate's four `conditions`: the C++ keeps the gate, the emerge and patrol path
  2472270), the build spec's normal health (170k: HealthModifier 59.213 on the level 58 warrior class base 2,871),
  DamageModifier 13 (the stock value, base SQL: "the hardest raw melee on the Scarlet side"), stun immunity 1972 (the
  build spec's "own set, stun immune, interruptible": handoff s7 #3 rules 1972, which holds no SILENCE or INTERRUPT, so
  Patty Cake can be kicked), INSTANCE_BIND. Heroic health 225k and the tier's melee are WP-H's
  (source/world/dungeons/stratholme.py). Thrash 12787 (his creature_addon aura), Ravenous Claw 17470 and Enrage 8599
  stay stock (DD scales them on heroic).
- 300604 Playmate (TC7): his look (the white ghoul, display 571) a little smaller (model scale 0.8), level 58 undead,
  faction 21 (his), HealthModifier 1.74155: ceil(2,871 x 1.74155) = 5,000 (heroic 7,000 is WP-H's `_KIT_ADD_HEROIC`,
  applied because this file declares it; the heroic row is 310193, the lock's id after the Gutter Rat 310192 and before
  S7's Infernal 310194). DamageModifier 2 (a third of a Gutter Rat volley's bite rate on the frozen: three playmates on
  one frozen player are about 350 a second). npc_st_playmate: emerge emote 449, yells "TIMMY!", goes for frozen
  players first.

Spells. The shatter and the trip are dungeon copies of the mod-boss-mechanics resolve spell (the registry's percent of
the reference row; the combat log names the mechanic); Frozen's tick is the kit's generic percent DoT; the clap sets its
damage at launch (DungeonKit::RefFlatOn, spell_st_timmy_clap, which also keeps it to the square):

  206460  Tag!              TC2 the 2 s debuff on the tagged player (the registry's 6 yd marker is the telegraph)
  206461  Frozen            TC3 -70% speed and 2% Frost a second; a touch thaws it (the script), the round's end too
  206462  Shatter           TC5 resolve copy (Frost), 30%, Weakened: everyone still frozen at the round's end
  206463  Patty Cake        TC6 the 4 s self channel: a clap a second (PERIODIC_TRIGGER_SPELL 206464); a kick ends it
  206464  Patty Cake        TC6 a clap: Physical on everyone on the square, 10% (heroic 20%) of the reference row
  206465  Jump Rope         TC8 a 2 s skip's cast bar (not interruptible); the registry Jump owns the sweep
  206466  Jump Rope         TC8 a 1.5 s skip (the heroic fallback Double Dutch)
  206467  Trip              TC9 resolve copy (Physical), 25%, Weakened: whoever is on the ground when a skip ends
  206468  Tripped           TC9 the 1 s knockdown (the trip's rider)
  206469-206479 spare

Visual ids are WP-V-2's (._visuals; every look is unconfirmed until seen in game).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_NO_ACTIVE_DEFENSE,
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    ATTR3_NOT_A_PROC,
    TARGET_SRC_CASTER,
    TARGET_UNIT_SRC_AREA_ENEMY,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_2,
    KIT_CREATURE,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_TIMMY_PLAYMATE,
    MK_SHATTER,
    TM_FREEZE,
    TM_SWEEP_BURST,
    TM_THUNDER_CLAP,
    TM_TRIP,
)

_TC = 'Stratholme build WP-S3 (Timmy the Cruel)'

_PLAYMATE_HEROIC = 310193                   # source/world/heroic_ids.lock: after the Gutter Rat 310192
_PLAYMATE_MODEL_SCALE = 0.8                 # "a little smaller" than him (display 571, display scale 1.5)

_MECHANIC_STUN = 12
_DEFENSE_MAGIC = 1
_ATTR1_IS_SELF_CHANNELED = 0x00000040
_CHANNEL_INTERRUPT_KICK = 0x08              # CHANNEL_INTERRUPT_FLAG_INTERRUPT: a kick stops the channel
_PREVENTION_SILENCE = 1
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000     # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map

# The stock icons of the looks they borrow.
_ICON_FREEZE = 35                           # Freeze 5276
_ICON_FROST_NOVA = 193                      # Frost Nova 122
_ICON_THUNDER_CLAP = 199                    # Thunder Clap 6343
_ICON_TRIP = 517                            # Trip 101
_ICON_ROPE = 2452                           # Wrangling Rope 40856

# The percents ride in the effects in hundredths (the kit's convention, DungeonKitFlow.h EffectPercent); TimmyLogic.h
# holds the same numbers (kFrozenTickPct, kClapPct), which the scripts read.
_FROZEN_TICK_HUNDREDTHS = 200               # 2% a second
_CLAP_NORMAL_HUNDREDTHS = 1000              # kClapPct.normal (10%)
_CLAP_HEROIC_HUNDREDTHS = 2000              # kClapPct.heroic (20%)
_FROZEN_SLOW_PCT = 70

_SCRIPT_DAMAGE = ('a percent of the reference row (hundredths in the value), set by the script '
                  '(DungeonKit::RefFlatOn)')

# Held back until wave 2 binds this boss (_common.py BIND_WAVE_2): stock until then.
if BIND_WAVE_2:
    creature_template_columns(10808, **boss_columns(
        'boss_timmy_the_cruel_rework', 59.213, damage_modifier=13,
    ))

    # --- 300604 Playmate (TC7) ----------------------------------------------------------------------------------------

    # Level 58 warrior class: ceil(2,871 x 1.74155) = 5,000 (heroic 7,000: stratholme.py `_KIT_ADD_HEROIC`).
    playmate_300604 = creature_template(
        300604, 'Playmate', **{
            **KIT_CREATURE, 'minlevel': 58, 'maxlevel': 58, 'rank': 0, 'unit_class': 1, 'unit_flags': 0,
            'HealthModifier': 1.74155, 'DamageModifier': 2.0, 'BaseAttackTime': 2000, 'speed_walk': 1.0,
            'speed_run': 1.14286, 'ExperienceModifier': 1.0, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0,
            'mingold': 0, 'maxgold': 0, 'ScriptName': 'npc_st_playmate', 'difficulty_entry_1': _PLAYMATE_HEROIC,
        },
    )
    creature_model(300604, display_id=DISPLAY_TIMMY_PLAYMATE, scale=_PLAYMATE_MODEL_SCALE)

    # --- TC2-TC5 Freeze Tag -------------------------------------------------------------------------------------------

    tagged_206460 = spell(
        id=206460, name='Tag!', school=School.FROST, dispel=0, mechanic=0,
        attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=2000,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=_ICON_FREEZE,
        notes=f'{_TC}, TC2: the tag. Every 3 s of a Freeze Tag round he tags a random player who is not frozen, the '
              'tank too (the script, Unit::AddAura): this 2 s debuff says who, while the registry\'s 6 yd marker on '
              'them (a telegraph-only RunOut, Teal) tells everyone else to keep out. When it ends the burst freezes '
              'the tagged player and everyone inside (206461). Dispel none, NO_IMMUNITIES. AuraInterruptFlags '
              'CHANGE_MAP.',
        raw_overrides=kit_raw('Tagged! You are about to freeze everyone near you.',
                              'Tagged! Everyone within 6 yards freezes with you.', CastingTimeIndex=1,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                              AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )

    frozen_206461 = spell(
        id=206461, name='Frozen', school=School.FROST, dispel=0, mechanic=0,
        attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=16000,
        effects=[
            Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DECREASE_SPEED,
                   base_points=-(_FROZEN_SLOW_PCT + 1), implicit_target_a=TARGET_UNIT_TARGET_ANY),
            Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=_FROZEN_TICK_HUNDREDTHS,
                   die_sides=0, amplitude=1000, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                   potency_excluded=_SCRIPT_DAMAGE),
        ],
        spell_icon_id=_ICON_FREEZE,
        notes=f'{_TC}, TC3: the burst\'s freeze on the tagged player and everyone within 6 yd of them (the script, '
              'Unit::AddAura with him as the caster): -70% speed and 2% of the reference row a second as Frost (the '
              'kit\'s spell_dungeon_refflat_periodic, base point 200 = 2.00% in hundredths, heroic the same), the '
              'tank row on the tank. Not a loss of control: they still attack and cast. 16 s, longer than a round: '
              'the script removes it when an unfrozen player touches them (TC4, a registry Soak of 3 yd anchored on '
              'them, for players without this aura) or when the round ends (TC5, the frozen shatter first). Mechanic '
              '0 and NO_IMMUNITIES, so no snare break or freedom effect undoes it (only a thaw does); Dispel none. '
              'The playmates go for the frozen first. Freeze 5276\'s SV 2335 (ice hands and an ice barrier state, '
              'V-2 TM_FREEZE; ST: never Frost Nova, which is The Unforgiven\'s). AuraInterruptFlags CHANGE_MAP.',
        raw_overrides=kit_raw('Frozen. Movement slowed and Frost damage every second until an ally touches you.',
                              'Frozen: $s1% movement speed, Frost damage every $t2 sec. An ally\'s touch thaws you.',
                              CastingTimeIndex=1, DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=TM_FREEZE,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                              AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG,
                              AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )
    scripted_by(frozen_206461, 'spell_dungeon_refflat_periodic')

    shatter_206462 = resolve_copy(
        206462, 'Shatter', School.FROST, 'The ice shatters.',
        f'{_TC}, TC5: Gotcha. When a Freeze Tag round ends (its 15 s, or everyone frozen at once) everyone still '
        'frozen shatters: 30% of the reference row, the tank too (its own row), 1 Weakened, through the registry '
        '(DungeonKit::RegistryHit on the frozen set). Copy of the resolve spell 205005 (Frost). Frost Nova 122\'s SV '
        '17 (V-1 MK_SHATTER, a frost burst) on every unit hit: the visible impact.',
        icon=_ICON_FROST_NOVA, visual=MK_SHATTER,
    )

    # --- TC6 Patty Cake ---------------------------------------------------------------------------------------------

    patty_cake_206463 = spell(
        id=206463, name='Patty Cake', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=4000,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, amplitude=1000,
                        trigger_spell=206464, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_THUNDER_CLAP,
        notes=f'{_TC}, TC6: "%s starts clapping his hands together." (emote line 2, type 41). A 4 s self channel '
              '(SPELL_ATTR1_IS_SELF_CHANNELED, like Evocation 12051) whose aura claps every second (the clap '
              '206464, four of them). Kickable: ChannelInterruptFlags 0x08 (a kick) and PreventionType 1 (a '
              'silence); his immunity set 1972 holds no INTERRUPT or SILENCE. Any interrupt stops the claps that are '
              'left. The descriptor\'s interrupt list, priority 3 (top; expected on heroic).',
        raw_overrides=kit_raw('Claps his hands together, hurting everyone on the square every second.',
                              'Clapping.', CastingTimeIndex=1, AttributesEx=_ATTR1_IS_SELF_CHANNELED | ATTR1_NO_THREAT,
                              ChannelInterruptFlags=_CHANNEL_INTERRUPT_KICK, InterruptFlags=0,
                              PreventionType=_PREVENTION_SILENCE, AttributesEx4=ATTR4_NO_CAST_LOG),
    )

    clap_206464 = spell(
        id=206464, name='Patty Cake', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=_CLAP_NORMAL_HUNDREDTHS - 1, die_sides=1,
                        implicit_target_a=TARGET_SRC_CASTER, implicit_target_b=TARGET_UNIT_SRC_AREA_ENEMY,
                        radius_yards=100.0, potency_excluded=_SCRIPT_DAMAGE)],
        spell_icon_id=_ICON_THUNDER_CLAP,
        notes=f'{_TC}, TC6: one clap of Patty Cake (the channel 206463 triggers it every second): Physical on every '
              'enemy on the square (100 yd from him; spell_st_timmy_clap keeps the targets inside his arena, the '
              'square, and sets the damage at launch: 10% normal / 20% heroic of the reference row, RefFlatOn, so the '
              'tank takes the tank row; the effect carries the same hundredths, heroic in EffectMiscValueB). Not '
              'avoidable, healable between claps: the resolve spell\'s attribute set (always hits, ignores line of '
              'sight and caster modifiers, cannot crit, no threat). Thunder Clap 6343\'s SV 145 (a ground crack '
              'round him, V-2 TM_THUNDER_CLAP).',
        raw_overrides=kit_raw('Claps his hands together.', instant=True, SpellVisualID_1=TM_THUNDER_CLAP,
                              DefenseType=_DEFENSE_MAGIC, EffectMiscValueB_1=_CLAP_HEROIC_HUNDREDTHS,
                              Attributes=ATTR0_NO_ACTIVE_DEFENSE,
                              AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION | ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                              AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )
    scripted_by(clap_206464, 'spell_st_timmy_clap')

    # --- TC8 / TC9 Jump Rope ----------------------------------------------------------------------------------------

    def _skip(spell_id: int, cast_ms: int, label: str):
        return cast_bar(
            spell_id, 'Jump Rope', cast_ms, 'Swings the Grimgore Noose like a jump rope. Jump as the cast ends.',
            f'{_TC}, TC8: {label}. Three skips back to back (yell line 4 "JUMP TIM TIM", emote line 5), each its own '
            'cast bar; not interruptible (cast_bar: InterruptFlags 0, PreventionType 0). The registry Jump (the '
            'Stratholme X3 kind, a 52 yd circle over the square, warning = this cast) owns the sweep: at the cast\'s '
            'end it trips everyone on the ground (206467 + 206468) and spares whoever is in the air (a jump, or a '
            'bot\'s hop). Smash 42669\'s SV 9612 (a dust ring burst at his feet as the rope comes round, V-2 '
            'TM_SWEEP_BURST). The rope beam (V-2 TM_JUMP_ROPE, a channel chain) is not wired: it needs a stalker to '
            'draw to and a second cast slot.',
            icon=_ICON_ROPE, visual=TM_SWEEP_BURST,
        )

    jump_rope_206465 = _skip(206465, 2000, 'a 2 s skip')
    jump_rope_fast_206466 = _skip(206466, 1500, 'a 1.5 s skip of the heroic fallback Double Dutch (2, 2, 1.5, 1.5, 1.5 '
                                  's; off until the designer calls it, `.dbtest strat timmy rope 1` plays it)')

    trip_206467 = resolve_copy(
        206467, 'Trip', School.NORMAL, 'The rope sweeps your feet from under you.',
        f'{_TC}, TC9: the rope\'s sweep at the end of each skip: every player inside the square who is on the ground '
        '(the registry\'s Jump kind; a pet cannot jump and is never hit): 25% of the reference row, the tank too (its '
        'own row), 1 Weakened, with the knockdown rider 206468. Copy of the resolve spell 205001 (Physical). The '
        'rider carries the look.',
        icon=_ICON_TRIP,
    )

    tripped_206468 = spell(
        id=206468, name='Tripped', school=School.NORMAL, dispel=0, mechanic=_MECHANIC_STUN,
        attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
        mana_cost_pct=0, range_yards=100.0, duration_ms=1000,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, base_points=0,
                        mechanic=_MECHANIC_STUN, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=_ICON_TRIP,
        notes=f'{_TC}, TC9: the 1 s knockdown of a trip (the registry rider, cast by him on every player the sweep '
              'hits). MOD_STUN with the stun mechanic (stun immunities and trinkets work; 1 s is under the shared 2 s '
              'limit on loss of control). Dispel none. Trip 101\'s SV 413 (the knockdown animation, a thud and stun '
              'stars, V-2 TM_TRIP): the visible impact of the trip. AuraInterruptFlags CHANGE_MAP.',
        raw_overrides=kit_raw('Knocked down for $d.', 'Knocked down.', CastingTimeIndex=1, SpellVisualID_1=TM_TRIP,
                              AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )
