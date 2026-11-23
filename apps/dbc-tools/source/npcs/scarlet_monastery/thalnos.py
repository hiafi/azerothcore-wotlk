"""
Scarlet Monastery build WP-D4: Bloodmage Thalnos (4543), "Blood Ritual", normal and heroic
(.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.5 row D4, s3.6; build spec
docs/dungeons/scarlet-monastery-1-graveyard.md "Bloodmage Thalnos", TH1-TH6). WP-D4 owns this file (its spells:
kSpellsThalnos 212440-212479 of modules/mod-dungeon-bosses src/ScarletMonastery/ScarletMonasteryRework.h only;
ThalnosLogic.h names the same ids). The hard mode (the Desecration: TH7, TH8, the risen) is WP-D4H's
(thalnos_hard_mode.py, on the hooks of ThalnosFight.h).

- 4543 Bloodmage Thalnos: boss_bloodmage_thalnos_rework (SmartAI off: WP-S0's rev drops rows 0-7; the C++ keeps the
  aggro and kill lines and Scorn's summon under game event 120 on normal), the build spec's normal health (48k =
  HealthModifier 54.054 on the level 32 paladin class base 888), DamageModifier 1.7 (the stock base value), stun
  immunity 1972, INSTANCE_BIND. Heroic 300k is WP-H's override (source/world/dungeons/scarlet_monastery.py). Shadow
  Bolt 9613, Flame Spike 8814, Flame Shock 8053 and Fire Nova 12470 are retired as his casts (8053 and 12470 carry
  live spell_dbc player overrides: his versions are copies here, rule 15).
- No boss-kit adds, no new creatures. The pool looks use the shared stalker 300922 (NPC_SM_STALKER, the
  orchestrator's template; the fight plays without it).

Spells. His damage is a percent of the reference row (the tank row on the tank): the casts' own hits through the kit's
spell_dungeon_refflat_damage (hundredths in the value, heroic in EffectMiscValueB), the line, the pillar, the pool and
the eruption's splash through the registry (resolve copies). Every damage spell ignores caster modifiers (rule 2). The
kickable casts (InterruptFlags 4: a kick, never his own movement; PreventionType 1: a silence) are the Bolt, the Lance
and the three nova bars; a kick locks the school, so the empowered nova's restart is a Physical bar:

  212440  Blood Ritual         TH1 his stack buff (the count; normal capped at 10 by the script, heroic 255)
  212441  Blood Ritual         TH1 an empowered cast's look on him (emote line 3)
  212442  Blood Bolt           TH2 2.5 s on the tank: 20% / 30% of the tank row (kickable)
  212443  Blood Lance          TH2e 2.5 s on the tank: 30% / 40% of the tank row (kickable)
  212444  Blood Lance          TH2e the line's hit on the others: 35% / 45% and Weakened (resolve copy, Shadow)
  212445  Flame Spike          TH3 the 2 s bar (not interruptible, Fire)
  212446  Flame Spike          TH3 the carrier's 2 s debuff (the carry)
  212447  Flame Spike          TH3 the pillar: 35% / 45% and Weakened (resolve copy, Fire)
  212448  Flame Spike          TH3 the pool's tick: 5% / 8% a second (resolve copy, Fire)
  212449  Flame Spike          TH3 the pool's look (the stalker's state aura, the shipped 4 yd lava rung)
  212450  Boiling Blood        TH4 the carrier's 5 s debuff
  212451  Boiling Blood        TH4 the eruption on the others: 35% / 45% and Weakened (resolve copy, Shadow)
  212452  Boiling Blood        TH4 the eruption on the carrier: 25% / 35%
  212453  Blood Nova           TH5 the 3 s bar (kickable, Shadow)
  212454  Empowered Blood Nova TH5e the 3 s bar (kickable, Shadow)
  212455  Blood Nova           TH5e the 2 s restart after the first kick (kickable, Physical)
  212456  Blood Nova           TH5 the plain hit on each player: 15% / 20%
  212457  Empowered Blood Nova TH5e the hit on each player: 25% / 35%
  212458  Blood Brand          TH6 (heroic) the 12 s Magic debuff
  212459  Flame Spike          TH3 the pillar's look (the stalker's, as the pool starts)
  212460-212479 spare.

Visual ids are WP-V's (._visuals; every look is unconfirmed until seen in game). Icons: the stock spells each one
stands in for (stock Spell.dbc SpellIconID).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR1_NO_THREAT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    RESOLVE_RAW,
    TARGET_UNIT_TARGET_ENEMY,
    self_visual,
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
    TH_BLOOD_BOLT,
    TH_BLOOD_BRAND,
    TH_BLOOD_LANCE,
    TH_BLOOD_NOVA,
    TH_BLOOD_NOVA_RING,
    TH_BLOOD_RITUAL,
    TH_BOILING_BLOOD,
    TH_BOILING_BLOOD_ERUPTION,
    TH_FLAME_SPIKE,
    TH_FLAME_SPIKE_POOL,
)

_D4 = 'Scarlet Monastery build WP-D4 (Bloodmage Thalnos)'

creature_template_columns(4543, **boss_columns(
    'boss_bloodmage_thalnos_rework', 54.054, damage_modifier=1.7,
))

_AURA_INTERRUPT_CHANGE_MAP = 0x00080000     # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map
_ATTR0_DO_NOT_DISPLAY = 0x00000080
_ATTR0_DO_NOT_LOG = 0x00000100
_INTERRUPT_KICK = 0x4                       # SPELL_INTERRUPT_FLAG_INTERRUPT only: a kick, never his own movement
_PREVENTION_SILENCE = 1
_DEFENSE_MAGIC = 1
_DISPEL_MAGIC = 1

_REFFLAT_DAMAGE = 'spell_dungeon_refflat_damage'
_SCRIPT_PCT = ('Scarlet Monastery D4: a percent of reference health (hundredths in the value, heroic in '
               'EffectMiscValueB), set by the kit\'s spell_dungeon_refflat_damage (DungeonKit::RefFlatOn)')

# Icons of the stock spells each one stands in for (stock Spell.dbc SpellIconID).
_ICON_RITUAL_OF_BLOOD = 2724    # Uzo's Ritual of Blood 10727
_ICON_BLOODBOLT = 153           # Bloodbolt 41072
_ICON_BLOODBOLT_SPLASH = 3222   # Bloodbolt Splash 71447
_ICON_FLAME_SPIKE = 37          # Flame Spike 8814
_ICON_BLOOD = 2725              # Boiling Blood 72385, Blood Nova 72378
_ICON_VAMPIRIC_CURSE = 1876     # Vampiric Curse 70423

# ThalnosLogic.h: the cast times and percents (hundredths: normal, heroic).
BOLT_CAST_MS = 2500
SPIKE_CAST_MS = 2000
BOIL_MS = 5000
NOVA_CAST_MS = 3000
NOVA_RESTART_CAST_MS = 2000
BRAND_MS = 12000
BOLT_PCT = (2000, 3000)
LANCE_PCT = (3000, 4000)
BOIL_CARRIER_PCT = (2500, 3500)
NOVA_PCT = (1500, 2000)
EMPOWERED_NOVA_PCT = (2500, 3500)
RITUAL_STACK_LIMIT = 255


def _hit_raw(desc: str, pct: tuple[int, int], visual: int, **more) -> dict:
    """A percent hit of his on one target: the resolve attribute set (no threat, always hits, cannot crit, ignores
    line of sight and his modifiers), the heroic hundredths in EffectMiscValueB."""
    raw = kit_raw(desc, **RESOLVE_RAW)
    raw.update(EffectMiscValueB_1=pct[1], **more)
    if visual:
        raw['SpellVisualID_1'] = visual
    return raw


def _cast(spell_id: int, name: str, pct: tuple[int, int], desc: str, notes: str):
    """Blood Bolt / Blood Lance: a 2.5 s kickable Shadow cast on the tank whose hit is `pct` of the tank row."""
    s = spell(
        id=spell_id, name=name, school=School.SHADOW, cast_time_ms=BOLT_CAST_MS, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=pct[0], die_sides=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_PCT)],
        spell_icon_id=_ICON_BLOODBOLT, notes=notes,
        raw_overrides=kit_raw(desc, InterruptFlags=_INTERRUPT_KICK, PreventionType=_PREVENTION_SILENCE,
                              DefenseType=_DEFENSE_MAGIC, EffectMiscValueB_1=pct[1],
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                              AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, SpellVisualID_1=TH_BLOOD_BOLT),
    )
    scripted_by(s, _REFFLAT_DAMAGE)
    return s


def _nova_bar(spell_id: int, name: str, cast_ms: int, school: School, desc: str, notes: str):
    """A kickable nova bar: a DUMMY on himself; the script deals the hit when it finishes (OnSpellCast)."""
    return spell(
        id=spell_id, name=name, school=school, cast_time_ms=cast_ms, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_BLOOD, notes=notes,
        raw_overrides=kit_raw(desc, InterruptFlags=_INTERRUPT_KICK, PreventionType=_PREVENTION_SILENCE,
                              AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=TH_BLOOD_NOVA),
    )


def _nova_hit(spell_id: int, name: str, pct: tuple[int, int], desc: str, notes: str):
    s = spell(
        id=spell_id, name=name, school=School.SHADOW, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=pct[0], die_sides=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_PCT)],
        spell_icon_id=_ICON_BLOOD, notes=notes,
        raw_overrides=_hit_raw(desc, pct, TH_BLOOD_NOVA_RING),
    )
    scripted_by(s, _REFFLAT_DAMAGE)
    return s


# --- TH1 Blood Ritual ------------------------------------------------------------------------------------------------

blood_ritual_212440 = spell(
    id=212440, name='Blood Ritual', school=School.SHADOW, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_RITUAL_OF_BLOOD,
    notes=f'{_D4}, TH1: his stack buff, the count the players read. The script holds the count (ThalnosLogic.h '
          'Ritual) and mirrors it here (DungeonKit::AddStacks): +1 for each player a plain spell hits (a bolt, a '
          'spike\'s pillar, a Boiling Blood eruption, a nova; heroic: each Blood Brand hit, at most one a second), '
          'minus the cost of each empowered cast. Normal capped at 10 by the script, heroic uncapped (CumulativeAura '
          '255, the client\'s byte). Not dispellable (Dispel none: a purge must not reset the frame); permanent '
          'while he fights, removed with the fight. No look of its own (the hands are 212441).',
    raw_overrides=kit_raw('Draws power from the blood of the living.',
                          'Blood Ritual. Each stack feeds an empowered spell.', CastingTimeIndex=1,
                          CumulativeAura=RITUAL_STACK_LIMIT, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

hands_run_red_212441 = self_visual(
    212441, 'Blood Ritual', TH_BLOOD_RITUAL,
    f'{_D4}, TH1: an empowered cast\'s look, cast by him on himself (triggered) with emote line 3 ("%s\'s hands run '
    'red with blood!") as the empowered version starts. Uzo\'s Ritual of Blood 10727\'s SV 9585 (V TH_BLOOD_RITUAL, '
    'RISKY: shadow-purple hands; the red alternate is TH_BLOOD_RITUAL_ALT, SV 15283, the Blood Nova bar\'s own look). '
    'Look only.',
    icon=_ICON_RITUAL_OF_BLOOD, school=School.SHADOW,
)

# --- TH2 Blood Bolt / TH2e Blood Lance -------------------------------------------------------------------------------

blood_bolt_212442 = _cast(
    212442, 'Blood Bolt', BOLT_PCT, 'Hurls a bolt of blood at the enemy.',
    f'{_D4}, TH2: the changed Shadow Bolt (9613 retired). A 2.5 s Shadow cast on the tank at 2 s, then every 8 s '
    '(heroic 6 s): 20% (heroic 30%) of the reference row, the tank row on the tank (spell_dungeon_refflat_damage: 2000 '
    '/ 3000 hundredths). Kickable (InterruptFlags 4, PreventionType 1; the interrupt list, priority 1, a reward): no '
    'hit and no stack. A hit gives him a Blood Ritual stack (the AI\'s SpellHitTarget). Bloodbolt 41072\'s SV 9308 (V '
    'TH_BLOOD_BOLT, RISKY: fire hands with a blood missile).',
)

blood_lance_212443 = _cast(
    212443, 'Blood Lance', LANCE_PCT, 'Hurls a lance of blood through the enemy.',
    f'{_D4}, TH2e: Blood Bolt\'s empowered version (needs 3 stacks, spends 1): the same 2.5 s cast on the tank, 30% '
    '(heroic 40%) of the tank row (3000 / 4000 hundredths), plus the registry line 212444 from him through the tank to '
    'the crypt\'s wall. Kickable (the interrupt list, priority 2): a kick cancels the line too. No stack. SV 9308 like '
    'the bolt (the line is the marker).',
)

blood_lance_line_212444 = resolve_copy(
    212444, 'Blood Lance', School.SHADOW, 'Run through by a lance of blood.',
    f'{_D4}, TH2e: the line\'s hit, a 4 yd line from him through the tank to the wall (clipped by the crypt\'s floor, '
    'at most 30 yd; 30 yd on the lawn), fixed at the bar\'s start and resolved 150 ms after it ends: everyone in it '
    'but the tank (TankExempt: the bolt is its hit) takes 35% (heroic 45%) of the reference row and Weakened. Copy of '
    'the resolve spell 205006 (Shadow). Bloodbolt Splash 71447\'s SV 15253 (V TH_BLOOD_LANCE: a blood_rain ground '
    'impact) on every player hit.',
    icon=_ICON_BLOODBOLT_SPLASH, visual=TH_BLOOD_LANCE,
)

# --- TH3 Flame Spike -------------------------------------------------------------------------------------------------

flame_spike_cast_212445 = cast_bar(
    212445, 'Flame Spike', SPIKE_CAST_MS, 'Marks the ground beneath the enemy for a pillar of flame.',
    f'{_D4}, TH3: the changed Flame Spike (8814 retired). The 2 s bar at 6 s, then every 15 s: a random player (the '
    'tank included; empowered, needs 3 spends 2: three) carries the debuff 212446 and a 4 yd circle that follows them '
    '(DungeonKit::FollowThenLand; the bots carry it to the edge, away from the group and the pools). At the bar\'s end '
    'it lands where they stand; 1.5 s later the pillar (212447), then the pool (212448). Not interruptible '
    '(InterruptFlags 0): a must-play bar, Fire (the kickable casts are Shadow and Physical). His stock Flame Spike\'s '
    'SV 10383 (V TH_FLAME_SPIKE: fire hands).',
    icon=_ICON_FLAME_SPIKE, visual=TH_FLAME_SPIKE, school=School.FIRE,
)

flame_spike_212446 = spell(
    id=212446, name='Flame Spike', school=School.FIRE, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=SPIKE_CAST_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_FLAME_SPIKE,
    notes=f'{_D4}, TH3: the carrier\'s debuff for the 2 s bar (the carry): the pillar lands where they stand when it '
          'ends. A DUMMY, not dispellable, NO_IMMUNITIES (it lands through Divine Shield). No look (the registry\'s 4 '
          'yd circle follows them).',
    raw_overrides=kit_raw('Marked for a pillar of flame.',
                          'A pillar of flame will erupt where you stand. Carry it to the edge.', CastingTimeIndex=1,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

flame_spike_pillar_212447 = resolve_copy(
    212447, 'Flame Spike', School.FIRE, 'A pillar of flame erupts.',
    f'{_D4}, TH3: the pillar, 1.5 s after the marker lands: 35% (heroic 45%) of the reference row (the tank row on the '
    'tank) and Weakened to everyone inside the 4 yd circle, the carrier too. A plain spike\'s hits give him a stack '
    'each. Copy of the resolve spell 205003 (Fire). No look of its own (212459 on the pool\'s stalker).',
    icon=_ICON_FLAME_SPIKE,
)

flame_spike_pool_212448 = resolve_copy(
    212448, 'Flame Spike', School.FIRE, 'The ground burns.',
    f'{_D4}, TH3: the pool\'s tick where a pillar stood: 5% (heroic 8%) of the reference row a second for 20 s (heroic '
    '30 s), the tank row on the tank, no Weakened (a lingering patch), the kit\'s Standing in It slow; no stack '
    '(pool ticks give none). DungeonKit::Linger. Copy of the resolve spell 205003 (Fire).',
    icon=_ICON_FLAME_SPIKE,
)

flame_spike_look_212449 = spell(
    id=212449, name='Flame Spike', school=School.FIRE, dispel=0, mechanic=0,
    attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_FLAME_SPIKE,
    # Not passive: a passive aura is never sent to the client, so its state visual would not show (custom-spells.md).
    notes=f'{_D4}, TH3: the look of a 4 yd Flame Spike pool. He summons the generic stalker 300922 on the pool for the '
          'pool\'s life and it casts this on itself (triggered): a hidden DUMMY aura whose StateKit is the shipped '
          '4 yd lava rung (V TH_FLAME_SPIKE_POOL, SV 90606). The registry zone owns the ticks.',
    raw_overrides=kit_raw('A burning pool.', 'A burning pool.', CastingTimeIndex=1, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=TH_FLAME_SPIKE_POOL),
)

flame_spike_erupt_212459 = self_visual(
    212459, 'Flame Spike', TH_FLAME_SPIKE,
    f'{_D4}, TH3: the pillar\'s look, cast once by the pool\'s stalker on itself (triggered) as the pillar erupts: '
    'the stock Flame Spike\'s SV 10383 (V TH_FLAME_SPIKE; its Flamestrike_Impact_Base on the ground; the hands do not '
    'show on the invisible stalker). Look only.',
    icon=_ICON_FLAME_SPIKE, school=School.FIRE,
)

# --- TH4 Boiling Blood -----------------------------------------------------------------------------------------------

boiling_blood_212450 = spell(
    id=212450, name='Boiling Blood', school=School.SHADOW, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=BOIL_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_BLOOD,
    notes=f'{_D4}, TH4: the changed Flame Shock (8053, a live player override, retired). His 5 s debuff on a random '
          'non-tank (the large-spread exemption) at 10 s, then every 15 s (empowered, needs 4 spends 2: two '
          'carriers), cast by him (triggered). The registry RunOut (8 yd, heroic 10 yd) erupts as it ends: 212451 on '
          'the others, 212452 on the carrier. Not dispellable (the walk is the answer), NO_IMMUNITIES. Boiling Blood '
          '72385\'s SV 15286 (V TH_BOILING_BLOOD: a blood boil on the chest, lasting 5 s).',
    raw_overrides=kit_raw('Your blood boils.',
                          'Your blood will erupt. Get away from everyone else.', CastingTimeIndex=1,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP, SpellVisualID_1=TH_BOILING_BLOOD),
)

boiling_blood_splash_212451 = resolve_copy(
    212451, 'Boiling Blood', School.SHADOW, 'Splashed by boiling blood.',
    f'{_D4}, TH4: the eruption on everyone else within 8 yd (heroic 10 yd) of a carrier: 35% (heroic 45%) of the '
    'reference row (the tank row on the tank) and Weakened, through the registry RunOut. Each player hit by a plain '
    'eruption gives him a stack. Copy of the resolve spell 205006 (Shadow). Blood Nova 72379\'s SV 9312 (V '
    'TH_BOILING_BLOOD_ERUPTION: BloodyExplosion) on every player hit.',
    icon=_ICON_BLOOD, visual=TH_BOILING_BLOOD_ERUPTION,
)

boiling_blood_burst_212452 = spell(
    id=212452, name='Boiling Blood', school=School.SHADOW, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=BOIL_CARRIER_PCT[0], die_sides=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_PCT)],
    spell_icon_id=_ICON_BLOOD,
    notes=f'{_D4}, TH4: the eruption on the carrier itself, cast by him (triggered) as the RunOut resolves: 25% '
          '(heroic 35%) of the reference row (2500 / 3500 hundredths, spell_dungeon_refflat_damage). The carrier '
          'cannot avoid it (a plain eruption: always a stack); no Weakened. The resolve attribute set. SV 9312 (V '
          'TH_BOILING_BLOOD_ERUPTION).',
    raw_overrides=_hit_raw('Your blood erupts.', BOIL_CARRIER_PCT, TH_BOILING_BLOOD_ERUPTION),
)
scripted_by(boiling_blood_burst_212452, _REFFLAT_DAMAGE)

# --- TH5 Blood Nova --------------------------------------------------------------------------------------------------

blood_nova_cast_212453 = _nova_bar(
    212453, 'Blood Nova', NOVA_CAST_MS, School.SHADOW, 'Blood bursts from the caster in a nova.',
    f'{_D4}, TH5: the changed Fire Nova (12470, a live player override, retired). The 3 s bar at 15 s, then every '
    '20 s. Kickable (InterruptFlags 4, PreventionType 1; the interrupt list, priority 2 on normal, a reward; 3 on '
    'heroic, expected): kicked, no hits and no stacks. Finished (OnSpellCast): 212456 on every player on his ground. '
    'Blood Nova 72378\'s SV 15283 (V TH_BLOOD_NOVA: red hands).',
)

empowered_nova_cast_212454 = _nova_bar(
    212454, 'Empowered Blood Nova', NOVA_CAST_MS, School.SHADOW, 'A nova of blood, fed by the ritual.',
    f'{_D4}, TH5e: Blood Nova\'s empowered version (needs 5 stacks, spends 3): the 3 s bar, kickable (priority 3). '
    'Finished: 212457 on every player on his ground (no stack). The first kick strips the blood: on the next tick he '
    'starts the plain restart 212455; a kick locks the Shadow school, so the restart is a Physical bar. SV 15283.',
)

blood_nova_restart_212455 = _nova_bar(
    212455, 'Blood Nova', NOVA_RESTART_CAST_MS, School.NORMAL, 'Blood bursts from the caster in a nova.',
    f'{_D4}, TH5e: the plain 2 s nova he restarts at once after the empowered nova\'s first kick (hub ruling 54: the '
    'deliberate two-interrupter moment on heroic). Physical, so the first kick\'s Shadow lockout does not stop it. '
    'Kickable (priority 3): the second kick stops it. Finished: the plain nova\'s hit 212456 (and its stacks). SV '
    '15283.',
)

blood_nova_212456 = _nova_hit(
    212456, 'Blood Nova', NOVA_PCT, 'Struck by a nova of blood.',
    f'{_D4}, TH5: the plain nova\'s hit, cast by him (triggered) on every player of the fight on his ground (the '
    'crypt; the lawn in the hard mode) as a plain nova or its restart finishes: 15% (heroic 20%; designer question '
    '1: the heroic bullet reads 30%) of the reference row, the tank row on the tank (spell_dungeon_refflat_damage). '
    'Each player hit gives him a stack (5 for a full group). Blood Nova 72379\'s SV 9312 (V TH_BLOOD_NOVA_RING) on '
    'each player.',
)

empowered_nova_212457 = _nova_hit(
    212457, 'Empowered Blood Nova', EMPOWERED_NOVA_PCT, 'Struck by a nova of blood.',
    f'{_D4}, TH5e: the empowered nova\'s hit on every player on his ground: 25% (heroic 35%) of the reference row; no '
    'stack (empowered spells give none). SV 9312.',
)

# --- TH6 Blood Brand (heroic) ----------------------------------------------------------------------------------------

blood_brand_212458 = spell(
    id=212458, name='Blood Brand', school=School.SHADOW, dispel=_DISPEL_MAGIC, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=BRAND_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_VAMPIRIC_CURSE,
    notes=f'{_D4}, TH6 (heroic): a 12 s Magic debuff on a random player (the tank included) at 12 s, then every 20 s, '
          'cast by him (triggered). Each time the branded player takes damage from any source he gains a Blood '
          'Ritual stack, at most one a second (the module\'s UnitScript OnDamage hook and the AI\'s gate). Magic: the '
          'dispel list, priority 2 (expected on heroic). Vampiric Curse 70423\'s SV 14871 (V TH_BLOOD_BRAND: '
          'MarkofBlood on the head, a red base state, lasting 12 s).',
    raw_overrides=kit_raw('Branded in blood.',
                          'Each time you take damage, the Bloodmage grows stronger.', CastingTimeIndex=1,
                          DefenseType=_DEFENSE_MAGIC, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP, SpellVisualID_1=TH_BLOOD_BRAND),
)
