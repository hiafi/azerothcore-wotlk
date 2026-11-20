"""
Blackrock Depths build WP-D15: Golem Lord Argelmach (8983; golems Toxitron 300833, Electron 300834, Arcanoton 300835;
the Arcane Orb 300837), normal and heroic (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.4 /
s3.5 row D15, s3.6, s3.8, s3.10, s7 #20, s8 #20; build spec docs/dungeons/blackrock-depths-3-manufactory.md "Golem Lord
Argelmach" AR1-AR10). WP-D15 owns this file (its spells: kSpellsArgelmach 211330-211369 of modules/mod-dungeon-bosses
src/BlackrockDepths/BlackrockDepthsRework.h only; ArgelmachLogic.h names the same ids). The engine side is
src/BlackrockDepths/boss_golem_lord_argelmach_rework.cpp; his texts, the SmartAI drop, the three pedestal gameobjects
(301285-301287) and the hall mobs' changes are data/sql/updates/pending_db_world/rev_argelmach_blackrock_depths.sql. The
hard mode (the Prototype) is WP-D16's argelmach_hard_mode.py.

- 8983 Golem Lord Argelmach: bound once wave 2 binds (BIND_WAVE_2, _common.py): boss_golem_lord_argelmach_rework
  (SmartAI off: this WP's rev drops his 14 rows), 150k at 5 players (HealthModifier 71.736 on the level 55 paladin base
  2,091), stun immunity 1972, INSTANCE_BIND, DamageModifier 3.5 (the stock base value; the live 6.25 is a leftover).
  Heroic 220k is WP-H's override (source/world/dungeons/blackrock_depths.py).
- 300833 Toxitron, 300834 Electron, 300835 Arcanoton (AR4): boss-kit adds, level 55 elite mechanical golems of his
  faction, 25,000 health (HealthModifier 9.56388 on the warrior base 2,614), no loot or XP, stun immunity 1972 (they
  stand still and cast: a stun would stop Poison Mist), bound to npc_brd_argelmach_golem (they never move or melee; he
  summons them dormant on their pedestals and wakes them at 90 / 65 / 40%). Heroic 37k is WP-H's `extra=`
  (difficulty_entry_1 310410-310412, STAGE-H-REPORT section 3). Displays: Toxitron 8177 (GolemCannonStone, shared with
  Phalanx), Electron 8178, Arcanoton 8289 (GolemStone, shared with the Vault Sentinels): V-1's approved defaults.
- 300837 Arcane Orb (AR9): a helper the players walk into (not selectable, not attackable), the PowerSparkCreature
  display 26753; it runs on its normal entry on heroic too (no heroic template, handoff s7 #2).
  npc_brd_argelmach_arcane_orb.

Spells. The registry hits (the cloud ticks, the tether's jolt, Livewire's pulses and burst, the orb's pop, the
Overcharge's catch and blast) deal their damage through dungeon copies of the mod-boss-mechanics resolve spell. Chain
Lightning and Shock are copies of the stock spells (rule 15; 15305 is on DD's double-use list) whose percent the boss's
own script sets at launch, times his Empowered stacks (spell_brd_argelmach_hit). Lightning Shield is a copy whose strike
the script sets at the cast (CastCustomSpell). Poison Mist carries its percents on the kit's refflat scripts. The rest
are auras or looks:

  211330  Chain Lightning      AR1 3 s, kickable, 5 targets, 12% / 15% each (x Empowered), Nature
  211331  Shock                AR2 instant on the tank, 20% / 25% of the tank row (x Empowered), Nature
  211332  Lightning Shield     AR3 self, 10 min, 3 charges, 50% to strike an attacker for 3% / 4%; Magic (purge)
  211333  Golem Wakes          AR4 the golem's own look as it wakes (Awaken SV 11519)
  211334  Chemical Bomb        AR5 the 4 s mark on a player (debuff, look)
  211335  Chemical Cloud       AR5 a cloud's tick: resolve copy, Nature, 6% / 9% a second
  211336  Chemical Cloud       AR5 the cloud's look on a stalker for its 30 s
  211337  Poison Mist          AR6 (heroic) Toxitron's 2 s cast: 25% to everyone + a Poison DoT 2% every 2 s, 10 s
  211338  Lethal Attraction    AR7 the 8 s tether on the pair (debuff, look)
  211339  Lethal Attraction    AR7 the jolt on a pair more than 5 yd apart: resolve copy, Nature, 40% / 60%
  211340  Livewire             AR8 (heroic) the 12 s Magic debuff; its dispel bursts (spell_brd_argelmach_livewire)
  211341  Livewire             AR8 a 2 s pulse round the carrier: resolve copy, Nature, 4%
  211342  Livewire Burst       AR8 the dispel's burst on everyone else within 8 yd: resolve copy, Nature, 30%
  211343  Power Surge          AR9 the orb's pop on the popper: resolve copy, Arcane, 10% / 15%
  211344  Overcharged          AR9 the popper's buff: +10% damage done, 30 s, stacks 3
  211345  Empowered            AR9 an orb that reached him: +15% damage done, 30 s, stacks 5
  211346  Arcane Overcharge    AR10 (heroic) the bomb's burst on its spot (look; Mana Bomb SV 5441)
  211347  Arcane Overcharge    AR10 the catcher's hit: resolve copy, Arcane, 30%
  211348  Arcane Overcharge    AR10 nobody caught it: resolve copy, Arcane, 40% to everyone
  211349  Stoned               AR4 the dormant statue look (golems and D16's Magmatron; R-2-A MA-1): Stoned 10255's SV
                               1845 without its FREEZE mechanic, NO_IMMUNITIES (immunity set 1972 drops the stock aura)
  211350-211369 spare

Visual ids are V-1's (._visuals AR_*); every look is unconfirmed until seen in game. Never wired: Activate Construct SV
13174, Living Bomb SV 11840, Chemical Flames SV 10407 (lib/test_blackrock_depths_vfx.py).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR0_NO_IMMUNITIES,
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    ATTR3_NOT_A_PROC,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_2,
    FACTION_DARK_IRON,
    IMMUNITY_BOSS_STUN,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    boss_columns,
    kit_creature,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    AR_ARCANE_OVERCHARGE,
    AR_CHAIN_LIGHTNING,
    AR_CHEMICAL_BOMB,
    AR_CHEMICAL_CLOUD,
    AR_GOLEM_WAKES,
    AR_LETHAL_ATTRACTION,
    AR_LIGHTNING_SHIELD,
    AR_LIVEWIRE,
    AR_POISON_MIST,
    AR_SHOCK,
    DISPLAY_ARCANE_ORB,
    DISPLAY_ARCANOTON,
    DISPLAY_ELECTRON,
    DISPLAY_TOXITRON,
)

# Held back until wave 2 binds this boss (_common.py BIND_WAVE_2): stock until then.
if BIND_WAVE_2:
    creature_template_columns(8983, **boss_columns(
        'boss_golem_lord_argelmach_rework', 71.736, damage_modifier=3.5,
    ))

_AR = 'Blackrock Depths build WP-D15 (Golem Lord Argelmach)'
_SCRIPT_HIT = ('Blackrock Depths: a percent of reference health in hundredths times his Empowered stacks, set at '
               'launch by spell_brd_argelmach_hit (ArgelmachLogic.h ScaledPct, DungeonKit::RefFlatOn)')
_SCRIPT_REFFLAT = ('Blackrock Depths: a percent of reference health in hundredths, set at launch by the kit\'s '
                   'spell_dungeon_refflat_damage / _periodic (DungeonKit::RefFlatOn)')

_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_SRC_CASTER = 22
_TARGET_UNIT_SRC_AREA_ENEMY = 15
_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40
_DISPEL_MAGIC = 1
_DISPEL_POISON = 4
_DEFENSE_MAGIC = 1
_PREVENTION_SILENCE = 1
_INTERRUPT_FLAGS_KICKABLE = 15
_SCHOOL_MASK_ALL = 127
# AURA_INTERRUPT_FLAG_CHANGE_MAP (SpellDefines.h): a map change or a logout drops it, so nothing outlives the instance.
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_TYPE_MECHANICAL = 9

# The stock Lightning Shield 15507's proc (the client Spell.dbc, 2026-11-17): melee and ranged hits taken, 50%.
_SHIELD_PROC_MASK = 139944
_SHIELD_PROC_CHANCE = 50
_SHIELD_CHARGES = 3

# Icons (the client Spell.dbc, the stock spells').
_ICON_CHAIN_LIGHTNING = 165         # Chain Lightning 15305
_ICON_SHOCK = 117                   # Shock 15605
_ICON_LIGHTNING_SHIELD = 19         # Lightning Shield 15507
_ICON_GENERIC = 1
_ICON_STONED = 220                  # Stoned 10255
_SV_STONED = 1845                   # Stoned 10255's SpellVisualID_1 (client Spell.dbc, read 2026-11-17)

# Numbers (ArgelmachLogic.h).
_CHAIN = (1200, 1500)               # kChainPct, hundredths (tooltip; the script reads the header)
_CHAIN_CAST_MS = 3000               # kChainCastMs
_CHAIN_TARGETS = 5                  # kChainTargets
_CHAIN_RANGE = 30.0
_SHOCK = (2000, 2500)               # kShockPct
_SHOCK_RANGE = 20.0
_SHIELD_MS = 600000                 # 10 min (stock)
_SHIELD_STRIKE = (300, 400)         # kShieldStrikePct (set by CastCustomSpell; the base point is a placeholder)
_BOMB_MS = 4000                     # kBombWarnMs
_CLOUD_MS = 30000                   # kCloudLifeMs
_MIST_CAST_MS = 2000                # kMistCastMs
_MIST = (2500, 2500)                # kMistPct
_MIST_TICK = (200, 200)             # kMistTickPct
_MIST_TICK_MS = 2000                # kMistTickMs
_MIST_DOT_MS = 10000                # kMistDotMs
_MIST_RADIUS = 60.0                 # kMistRadiusYd
_TETHER_MS = 8000                   # kTetherMs
_LIVEWIRE_MS = 12000                # kLivewireMs
_OVERCHARGED_PCT = 10               # kOverchargedPct
_OVERCHARGED_STACKS = 3             # kOverchargedMaxStacks
_OVERCHARGED_MS = 30000             # kOverchargedMs
_EMPOWERED_PCT = 15                 # kEmpoweredPctPerStack
_EMPOWERED_STACKS = 5               # kEmpoweredMaxStacks
_EMPOWERED_MS = 30000               # kEmpoweredMs

_GOLEM_HEALTH_MODIFIER = 9.56388    # ceil(2,614 x 9.56388) = 25,000 at level 55 (kGolemHealth normal)
GOLEM_HEROIC_ENTRIES = {300833: 310410, 300834: 310411, 300835: 310412}  # heroic_ids.lock (STAGE-H-REPORT s3)

# The scripted hit: no redirection or reflection, no crit, ignores his modifiers (a percent of the reference row).
_HIT_ATTRS = dict(
    AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
    AttributesEx2=ATTR2_CANT_CRIT,
    AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
)


def _state_aura(spell_id: int, name: str, visual: int, duration_ms: int, notes: str):
    """A hidden DUMMY aura a stalker casts on itself for its look (a state kit needs an aura to play; not passive: a
    passive aura is never sent to the client)."""
    return spell(
        id=spell_id, name=name, school=School.NATURE, dispel=0, mechanic=0,
        attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_GENERIC, notes=notes,
        raw_overrides=kit_raw(SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                              CastingTimeIndex=1),
    )


def _debuff(spell_id: int, name: str, visual: int, duration_ms: int, desc: str, aura_desc: str, notes: str, *,
            dispel: int = 0, school: School = School.NATURE, icon: int = _ICON_GENERIC):
    """A DUMMY debuff a golem (or a hard mode core) puts on a player: the mark and its look; the script judges it.
    AURA_IS_DEBUFF, 100 yd, through line of sight, dropped on a map change."""
    return spell(
        id=spell_id, name=name, school=school, dispel=dispel, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, aura_desc, instant=True, DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=visual,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                              AttributesEx3=ATTR3_ALWAYS_HIT, AttributesEx4=ATTR4_NO_CAST_LOG,
                              AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )


def _damage_buff(spell_id: int, name: str, pct: int, stacks: int, duration_ms: int, desc: str, aura_desc: str,
                 notes: str):
    """+pct% damage done (every school) a stack, `stacks` at most (DungeonKit::AddStacks, CumulativeAura), on the unit
    itself. Not dispellable."""
    return spell(
        id=spell_id, name=name, school=School.ARCANE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=pct,
                        die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                        potency_excluded=f'{name}: a flat +{pct}% damage done a stack, not a damage value')],
        spell_icon_id=_ICON_GENERIC, notes=notes,
        raw_overrides=kit_raw(desc, aura_desc, instant=True, CumulativeAura=stacks, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )


# --- 300833-300835 the golems, 300837 the Arcane Orb ----------------------------------------------------------------

def _golem(entry: int, name: str, display: int):
    row = creature_template(
        entry, name, **{
            **kit_creature(faction=FACTION_DARK_IRON, type=_TYPE_MECHANICAL), 'minlevel': 55, 'maxlevel': 55,
            'rank': 1, 'unit_class': 1, 'unit_flags': 0, 'HealthModifier': _GOLEM_HEALTH_MODIFIER,
            'DamageModifier': 1.0, 'BaseAttackTime': 2000, 'ExperienceModifier': 0.0, 'lootid': 0,
            'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'CreatureImmunitiesId': IMMUNITY_BOSS_STUN,
            'ScriptName': 'npc_brd_argelmach_golem', 'difficulty_entry_1': GOLEM_HEROIC_ENTRIES[entry],
        },
    )
    creature_model(entry, display_id=display)
    return row


toxitron_300833 = _golem(300833, 'Toxitron', DISPLAY_TOXITRON)
electron_300834 = _golem(300834, 'Electron', DISPLAY_ELECTRON)
arcanoton_300835 = _golem(300835, 'Arcanoton', DISPLAY_ARCANOTON)

arcane_orb_300837 = creature_template(
    300837, 'Arcane Orb', **{**KIT_HELPER, 'minlevel': 55, 'maxlevel': 55, 'rank': 0, 'unit_class': 1,
                             'ScriptName': 'npc_brd_argelmach_arcane_orb'},
)
creature_model(300837, display_id=DISPLAY_ARCANE_ORB)

# --- AR1 Chain Lightning, AR2 Shock, AR3 Lightning Shield -----------------------------------------------------------

chain_lightning_211330 = spell(
    id=211330, name='Chain Lightning', school=School.NATURE, dispel=0, mechanic=0, cast_time_ms=_CHAIN_CAST_MS,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=_CHAIN_RANGE, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=_CHAIN[0] - 1, die_sides=1,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, chain_targets=_CHAIN_TARGETS,
                    potency_excluded=_SCRIPT_HIT)],
    spell_icon_id=_ICON_CHAIN_LIGHTNING,
    notes=f'{_AR}, AR1: the stock Chain Lightning 15305 (278-322 Nature, on DD\'s double-use list) rescaled (rule 15: '
          'a copy in the slice). A 3 s cast on his victim at 14 s, then every 15 s (the stock timers), jumping to 5 '
          'targets: 12% (heroic 15%) of each target\'s row (the tank row on the tank) times his Empowered stacks '
          '(+15% each), set at launch by spell_brd_argelmach_hit (gap 36 "stock rescaled", designer question 1). No '
          'fall-off per jump (EffectChainAmplitude 1). Interruptible and silence-preventable: the interrupt list '
          '(priority 1 normal, 3 heroic). Cannot crit, always hits, ignores his modifiers. The stock SV 36.',
    raw_overrides=kit_raw('Strikes an enemy with a lightning bolt that arcs to up to $x1 nearby enemies.',
                          InterruptFlags=_INTERRUPT_FLAGS_KICKABLE, PreventionType=_PREVENTION_SILENCE,
                          DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=AR_CHAIN_LIGHTNING,
                          EffectChainAmplitude_1=1.0, EffectMiscValueB_1=_CHAIN[1], **_HIT_ATTRS),
)
scripted_by(chain_lightning_211330, 'spell_brd_argelmach_hit')

shock_211331 = spell(
    id=211331, name='Shock', school=School.NATURE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=_SHOCK_RANGE, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=_SHOCK[0] - 1, die_sides=1,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_HIT)],
    spell_icon_id=_ICON_SHOCK,
    notes=f'{_AR}, AR2: the stock Shock 15605 (273-293 Nature) rescaled (rule 15). Instant on his victim, the tank, at '
          '6 s then every 7 s (the stock timers): 20% (heroic 25%) of the tank row times his Empowered stacks, set at '
          'launch by spell_brd_argelmach_hit (a tank swing-class hit, the BRS convention; designer question 1). Cannot '
          'crit, always hits, ignores his modifiers. The stock SV 97.',
    raw_overrides=kit_raw('Instantly throws a bolt of lightning at an enemy, inflicting Nature damage.', instant=True,
                          DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=AR_SHOCK, EffectMiscValueB_1=_SHOCK[1],
                          **_HIT_ATTRS),
)
scripted_by(shock_211331, 'spell_brd_argelmach_hit')

lightning_shield_211332 = spell(
    id=211332, name='Lightning Shield', school=School.NATURE, dispel=_DISPEL_MAGIC, mechanic=0, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=_SHIELD_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PROC_TRIGGER_DAMAGE,
                    base_points=_SHIELD_STRIKE[0] - 1, die_sides=1, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Lightning Shield: the strike is set at the cast by the script (CastCustomSpell, '
                                     'DungeonKit::RefFlat)')],
    spell_icon_id=_ICON_LIGHTNING_SHIELD,
    notes=f'{_AR}, AR3: the stock Lightning Shield 15507 (3 charges of 4 Nature) rescaled (rule 15). He casts it on '
          'himself (triggered) at the pull and every 45 s; 10 min, 3 charges, a 50% chance to strike a melee or '
          'ranged attacker (the stock proc: ProcTypeMask 139944): each strike 3% (heroic 4%) of the non-tank row, the '
          'amount set at the cast (CastCustomSpell base point 0 = DungeonKit::RefFlat; designer question 1). Magic: '
          'the purge list (a reward). The stock SV 37.',
    raw_overrides=kit_raw('Surrounds the caster with $n balls of lightning that strike attackers.',
                          '$h% chance to strike an attacker for $s1 Nature damage.', instant=True,
                          DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=AR_LIGHTNING_SHIELD,
                          ProcTypeMask=_SHIELD_PROC_MASK, ProcChance=_SHIELD_PROC_CHANCE, ProcCharges=_SHIELD_CHARGES,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- AR4 the golem wakes --------------------------------------------------------------------------------------------

golem_wakes_211333 = self_visual(
    211333, 'Golem Wakes', AR_GOLEM_WAKES,
    f'{_AR}, AR4: a golem casts it on itself (triggered) as it wakes on its pedestal (at 90%, 65% and 40% of his '
    'health; he yells lines 1-3): Awaken 52875\'s SV 11519 (V-1: never Activate Construct\'s SV 13174, a fire '
    'strike). Look only.',
    icon=_ICON_GENERIC, school=School.NATURE,
)

# --- AR5 Chemical Bomb, AR6 Poison Mist ------------------------------------------------------------------------------

chemical_bomb_211334 = _debuff(
    211334, 'Chemical Bomb', AR_CHEMICAL_BOMB, _BOMB_MS, 'Marks the target with a chemical bomb.',
    'A chemical cloud drops where you stand in $d. Carry it to the edge.',
    f'{_AR}, AR5: Toxitron marks 2 players (the tank too, ruling 88) at 5 s after its wake, then every 15 s (heroic '
    '12 s), casting this on each (triggered): the 4 s mark. The registry circle follows the carrier (DungeonKit::'
    'FollowThenLand; the bots carry it to the chamber\'s edge) and the cloud (211335, 211336) drops where they stand. '
    'Noxious Cloud 21070\'s green SV 10395 (V-1: never Living Bomb\'s SV 11840). Not dispellable; removed when the '
    'fight ends.',
)

chemical_cloud_211335 = resolve_copy(
    211335, 'Chemical Cloud', School.NATURE, 'A caustic cloud clings to the ground.',
    f'{_AR}, AR5: a Chemical Bomb cloud\'s tick: a 5 yd cloud where a marked player stood for 30 s, hitting everyone '
    'inside every second for 6% (heroic 9%) of the row plus the kit\'s Standing in It slow, through the registry '
    '(DungeonKit::Linger). Copy of the resolve spell 205001 with the Nature school. The look is 211336. D16\'s '
    'Incineration detonates the clouds (ArgelmachFight.h TakeClouds).',
)

chemical_cloud_look_211336 = _state_aura(
    211336, 'Chemical Cloud', AR_CHEMICAL_CLOUD, _CLOUD_MS,
    f'{_AR}, AR5: the cloud\'s look: a stalker (300796) at the spot casts it on itself as the cloud drops and lives as '
    'long as the cloud (30 s). Noxious Cloud 21070\'s SV 10395 (V-1; alternate the 4 yd goo SV 90343). Look only.',
)

poison_mist_211337 = spell(
    id=211337, name='Poison Mist', school=School.NATURE, dispel=_DISPEL_POISON, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=_MIST_CAST_MS, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=_MIST_DOT_MS,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=_MIST[0] - 1, die_sides=1,
               implicit_target_a=_TARGET_SRC_CASTER, implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY,
               radius_yards=_MIST_RADIUS, potency_excluded=_SCRIPT_REFFLAT),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=_MIST_TICK[0],
               die_sides=0, amplitude=_MIST_TICK_MS, implicit_target_a=_TARGET_SRC_CASTER,
               implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=_MIST_RADIUS,
               potency_excluded=_SCRIPT_REFFLAT),
    ],
    spell_icon_id=_ICON_GENERIC,
    notes=f'{_AR}, AR6 (heroic only): Toxitron\'s second attack, 8 s after its wake, then every 20 s: a 2 s cast (not '
          'interruptible: a must-play bar), then 25% of the row to every enemy within 60 yd (the whole chamber), and '
          'a Poison DoT of 2% every 2 s for 10 s (handoff s7 #21: "Poison Mist 2% per 2 s"). Poison: the dispel list '
          '(priority 1, a reward); D16\'s Flamethrower burns it off. Both percents through the kit\'s refflat scripts '
          '(the tank row on the tank). Cannot crit, always hits, ignores the golem\'s modifiers. Poison Nova 55081\'s '
          'SV 12084.',
    raw_overrides=kit_raw('Sprays a poison mist over every enemy in the chamber.', 'Poisoned. $s2 Nature damage every '
                          '$t2 sec.', InterruptFlags=0, PreventionType=0, DefenseType=_DEFENSE_MAGIC,
                          SpellVisualID_1=AR_POISON_MIST, EffectMiscValueB_1=_MIST[1],
                          EffectMiscValueB_2=_MIST_TICK[1], AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                          AttributesEx2=ATTR2_CANT_CRIT | ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(poison_mist_211337, 'spell_dungeon_refflat_damage', 'spell_dungeon_refflat_periodic')

# --- AR7 Lethal Attraction, AR8 Livewire -----------------------------------------------------------------------------

lethal_attraction_211338 = _debuff(
    211338, 'Lethal Attraction', AR_LETHAL_ATTRACTION, _TETHER_MS, 'Tethers two enemies together.',
    'Tethered. Be within 5 yards of your partner when it ends.',
    f'{_AR}, AR7: Electron tethers two players (the tank too) 5 s after its wake, then every 20 s (heroic 15 s), '
    'casting this on both (triggered): 8 s. At the end the script measures the pair: more than 5 yd apart, both take '
    'the jolt (211339). The registry Stack keeps the second within 5 yd of the first (the bots). Lightning Tether '
    '33628\'s SV 8371. Not dispellable; removed at the end and when the fight ends.',
)

lethal_jolt_211339 = resolve_copy(
    211339, 'Lethal Attraction', School.NATURE, 'The tether snaps.',
    f'{_AR}, AR7: the jolt on a tethered pair more than 5 yd apart after 8 s: 40% (heroic 60%) of the row to both, '
    'through the registry (DungeonKit::RegistryHit). Copy of the resolve spell 205001 with the Nature school.',
)

livewire_211340 = _debuff(
    211340, 'Livewire', AR_LIVEWIRE, _LIVEWIRE_MS, 'Charges the target with a live current.',
    'Shocks everyone within 8 yards every 2 sec. Dispelling it shocks them too.',
    f'{_AR}, AR8 (heroic only): Electron\'s second attack, 8 s after its wake, then every 20 s, on one player (the '
    'tank too): 12 s. Every 2 s everyone within 8 yd of the carrier (the carrier too) takes the pulse (211341); a '
    'dispel bursts on everyone else within 8 yd (211342; spell_brd_argelmach_livewire, AfterDispel). Magic: the '
    'dispel list (priority 3) only once no ally is within 8 yd (NearPlayer, WP-DS). Lightning Shield 15507\'s lasting '
    'SV 37 (V-1: never SV 11840).',
    dispel=_DISPEL_MAGIC,
)
scripted_by(livewire_211340, 'spell_brd_argelmach_livewire')

livewire_pulse_211341 = resolve_copy(
    211341, 'Livewire', School.NATURE, 'A live current arcs from the carrier.',
    f'{_AR}, AR8: a Livewire pulse every 2 s on everyone within 8 yd of the carrier (the carrier too): 4% of the row '
    'through the registry (DungeonKit::RegistryHit). Copy of the resolve spell 205001 with the Nature school.',
)

livewire_burst_211342 = resolve_copy(
    211342, 'Livewire Burst', School.NATURE, 'The current bursts as it is dispelled.',
    f'{_AR}, AR8: the dispel\'s burst: 30% of the row to everyone else within 8 yd of the carrier (a 0 s RunOut on the '
    'carrier). Copy of the resolve spell 205001 with the Nature school.',
)

# --- AR9 Power Generator, AR10 Arcane Overcharge ---------------------------------------------------------------------

power_surge_211343 = resolve_copy(
    211343, 'Power Surge', School.ARCANE, 'The orb discharges into whoever touches it.',
    f'{_AR}, AR9: an Arcane Orb (300837) drifts from Arcanoton to him in 10 s, 5 s after its wake, then every 20 s '
    '(heroic 15 s); walking into it (2.5 yd) pops it: 10% (heroic 15%) of the row to the popper through the registry, '
    'and Overcharged (211344). Copy of the resolve spell 205001 with the Arcane school.',
)

overcharged_211344 = _damage_buff(
    211344, 'Overcharged', _OVERCHARGED_PCT, _OVERCHARGED_STACKS, _OVERCHARGED_MS,
    'Increases damage done by $s1% for $d. Stacks up to 3 times.', 'Damage done increased by $s1%.',
    f'{_AR}, AR9: the popper\'s reward (DungeonKit::AddStacks on the player): +10% damage done, 30 s, stacks 3 (each '
    'pop refreshes it). Removed when the fight ends. No look of its own.',
)

empowered_211345 = _damage_buff(
    211345, 'Empowered', _EMPOWERED_PCT, _EMPOWERED_STACKS, _EMPOWERED_MS,
    'Increases damage done by $s1% for $d. Stacks up to 5 times.', 'Damage done increased by $s1%.',
    f'{_AR}, AR9 (ruling 91): an orb that reaches him gives him a stack (DungeonKit::AddStacks): +15% damage done, '
    '30 s, stacks 5. His melee takes it from the aura; Chain Lightning and Shock (which ignore caster modifiers) by '
    'EmpoweredFactor in spell_brd_argelmach_hit. Removed on his death, evade and reset.',
)

overcharge_bomb_211346 = spell(
    id=211346, name='Arcane Overcharge', school=School.ARCANE, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
    spell_icon_id=_ICON_GENERIC,
    notes=f'{_AR}, AR10 (heroic only): Arcanoton\'s second attack, 8 s after its wake, then every 20 s: a 3 yd spot on '
          'the open floor (8-25 yd from him, off the walls and the pedestals) marked for 4 s (the registry Soak); as '
          'it lands Arcanoton casts this at the spot (triggered): Mana Bomb 36846\'s SV 5441, the arcane explosion. '
          'Look only (the hits are 211347 / 211348).',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=AR_ARCANE_OVERCHARGE, Targets=_TARGET_FLAG_DEST_LOCATION,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

overcharge_catch_211347 = resolve_copy(
    211347, 'Arcane Overcharge', School.ARCANE, 'You catch the overcharged bomb.',
    f'{_AR}, AR10: a caught bomb: 30% of the row to each catcher standing in the 3 yd spot as it lands, through the '
    'registry. Copy of the resolve spell 205001 with the Arcane school.',
)

overcharge_blast_211348 = resolve_copy(
    211348, 'Arcane Overcharge', School.ARCANE, 'The overcharged bomb explodes.',
    f'{_AR}, AR10: nobody caught the bomb: 40% of the row to everyone in the fight, through the registry. Copy of the '
    'resolve spell 205001 with the Arcane school.',
)

# --- AR4 the dormant statue look (R-2-A MA-1) ------------------------------------------------------------------------

statue_211349 = spell(
    id=211349, name='Stoned', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_STONED,
    notes=f'{_AR}, AR4 (R-2-A MA-1): the dormant statue look on the three pedestal golems and D16\'s Magmatron 300836 '
          '(boss_golem_lord_argelmach_rework / argelmach_hard_mode MakeDormant, AddAura; removed by the wake and the '
          'pull). A copy of Stoned 10255 (its SV 1845 and icon) without the stock EffectMechanic FREEZE, which their '
          'immunity set 1972 drops (so the stock aura never lands), and with NO_IMMUNITIES. Look only: the dormant '
          'state is the golem\'s own state (D15 GolemState.awake, D16 StatueDormant: NOT_SELECTABLE, out of combat). '
          'Same pattern as the Vault Sentinels\' 211103 (F-2a).',
    raw_overrides=kit_raw(SpellVisualID_1=_SV_STONED, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          CastingTimeIndex=1, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
