"""
Gnomeregan build WP-D2: Viscous Fallout (7079) and his pool stalker (301130), normal and heroic
(.agents/plans/gnomeregan-build/gnomeregan-build.HANDOFF.md s3.5 row D2, s3.6, s3.8 (area C), s7 #19 A, #36-#38 A,
s10; build spec docs/dungeons/gnomeregan-rework.md SP 748-801 (VF1-VF9), design SP 585-747, rulings 14-20). WP-D2 owns
this file (its spells: kSpellsFallout 214340-214379 of modules/mod-dungeon-bosses src/Gnomeregan/GnomereganRework.h
only; ViscousFalloutLogic.h names the same ids and lib/test_gnomeregan_fallout.py diffs them). The engine side is
src/Gnomeregan/boss_viscous_fallout_rework.cpp and the DoseField machine ViscousFalloutMachine.cpp; the texts and his
addon are data/sql/updates/pending_db_world/rev_viscous_fallout_gnomeregan.sql.

- 7079 Viscous Fallout: boss_viscous_fallout_rework (SmartAI off: rev_skeleton_gnomeregan.sql drops his rows), normal
  health 65,997 = 77.37 on the level 28 warrior base 853 (spec 33,000 x2.0, s7 #1 A), stock DamageModifier 1.7,
  immunity -232 -> 1972 (stun immune, SYS 6; his Frost immunity stays as the addon aura 7940), INSTANCE_BIND with both
  assist flags, detection 12 (WP-S0's boss_columns). Heroic 466,667 is WP-H's override. His loot stays stock (L-1's).
- 301130 Fallout Pool: the nature disc under a pool (WP-V's DISPLAY_NATURE_DISC 90850; the script sets the scale,
  radius / 4.8, with the display in one call). A helper nobody targets (npc_gnomer_pool_stalker, inert), map-summoned
  per pool and despawned with it. No heroic template.

Spells (214340-214379). Registry damage is a percent of the reference row through resolve copies (the combat log
names the mechanic; IGNORE_CASTER_MODIFIERS, NO_REDIRECTION, NO_REFLECTION), all Nature (rule 2: never Physical).
Nothing he casts is kickable (the kick and dispel table: Half-Life InterruptFlags 0); the dose, Sickness, Meltdown
and Leaking cannot be dispelled; the Volley Poison can (a reward). Tooltips are number-free.

  214340  Irradiated            VF1 the dose: +3% damage and healing done a stack (CumulativeAura 255), a debuff for
                                the fight, cast by the owner (DungeonKit::AddStacks from the DoseField machine). Dispel
                                none, NO_IMMUNITIES, CHANGE_MAP. Irradiated 9775's SV 1712 (VF_DOSE)
  214341  Irradiated            VF1 the bright glow at 7 (normal) / 10 (heroic) dose: hidden (VF_DOSE_BRIGHT 6594)
  214342  Radiation Sickness    VF2 normal: resolve copy, 40% plus Weakened (VF_SICKNESS 1725)
  214343  Radiation Sickness    VF2 the 8 yd pulse on allies: resolve copy, 20%
  214344  Radiation Sickness    VF2 the rider: a 2 s stun (mechanic stun), the vomit (VF_VOMIT 9446). Dispel none
  214345  Toxic Volley          VF3 resolve copy: 10% (heroic +3% per dose carried)
  214346  Toxic Volley          VF3 the Poison rider: 1.00% of the reference row every 3 s for 15 s (the kit's refflat
                                periodic). Dispel Poison: the reward
  214347  Fallout Pool          VF3-VF7 the pool tick: resolve copy, 8% a second
  214348  Slough                VF4 the swell on him (VF_SLOUGH 1725), look only
  214349  Saturated             VF5 +50% damage done while he stands in an armed pool (VF_DOSE_BRIGHT on him)
  214350  Corrosive Ooze        VF6 the lobbed glob: a missile to the circle's center (VF_GLOB = SV_ARCING_GLOB 90750)
  214351  Corrosive Ooze        VF6 resolve copy: 40% / 60%, Weakened
  214352  Half-Life             VF9 heroic: the 3 s bar (not interruptible), keeps his swing timer
  214353  Half-Life             VF9 his heal (the script's base point: 0.5% of his maximum health per dose shed)
  214354  Meltdown              VF8 heroic: resolve copy, 5% a second (the carrier and everyone within 6 yd)
  214355  Meltdown              VF8 the carrier's debuff (the read). Dispel none, NO_IMMUNITIES, CHANGE_MAP
  214356  Toxic Volley          VF3 the Volley's look on him (VF_VOLLEY 4202), look only
  214357-214379 spare.

Kept as cast (stock): Immunity: Frost 7940 (his addon). Weakened is BM's 205000 (the registry's).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_THREAT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_NATURE_DISC,
    VF_DOSE,
    VF_DOSE_BRIGHT,
    VF_GLOB,
    VF_SICKNESS,
    VF_SLOUGH,
    VF_VOLLEY,
    VF_VOMIT,
)

creature_template_columns(7079, **boss_columns(
    'boss_viscous_fallout_rework', 77.37, damage_modifier=1.7,
))

_VF = 'Gnomeregan build WP-D2 (Viscous Fallout)'
_SCRIPT_DAMAGE = ('Gnomeregan: the kit\'s spell_dungeon_refflat_periodic sets each tick (a percent of the reference '
                  'row, hundredths in the base point), not a potency value')
_SCRIPT_HEAL = 'Gnomeregan: the script sets the heal (0.5% of his maximum health per dose shed), not a potency value'

POOL_STALKER = 301130

# ViscousFalloutLogic.h Tune (the DT test pins each against the header).
_DOSE_PCT = 3                       # kDosePctPerStack
_AURA_STACK_LIMIT = 255             # kAuraStackLimit
_STUN_MS = 2000                     # kSicknessStunMs
_POISON_HUNDREDTHS = 100            # kVolleyPoisonHundredths
_POISON_TICK_MS = 3000              # kVolleyPoisonTickMs
_POISON_MS = 15000                  # kVolleyPoisonMs
_SATURATED_PCT = 50                 # kSaturatedDamagePct
_HALF_LIFE_CAST_MS = 3000           # kHalfLifeCastMs
_GLOB_SPEED = 20.0                  # kGlobMissileSpeed

_SCHOOL_MASK_ALL = 127
_DISPEL_POISON = 4
_MECHANIC_STUN = 12
_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40
_ATTR2_DO_NOT_RESET_COMBAT_TIMERS = 0x00020000      # a finished cast keeps his swing timer (LESSONS L3)
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000             # the aura never leaves the instance on the character

# Stock icons (Spell.dbc, read 2026-11-26).
_ICON_IRRADIATED = 203              # Irradiated 9775
_ICON_TOXIC_VOLLEY = 68             # Toxic Volley 21687
_ICON_CORROSIVE_OOZE = 221          # Corrosive Ooze 9459
_ICON_RADIATION = 160               # Radiation Poisoning 11638, Radiation Cloud 10341, Summon Sludge 3527
_ICON_GLOWY = 1479                  # Glowy (Green) 22577


def _hidden_look(spell_id: int, name: str, visual: int, icon: int, notes: str):
    """A hidden DUMMY aura that carries a StateKit look on its holder (applied with Unit::AddAura by him, no cast)."""
    return spell(
        id=spell_id, name=name, school=School.NATURE, dispel=0, mechanic=0,
        attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )


# --- VF1 the dose ----------------------------------------------------------------------------------------------------

irradiated_214340 = spell(
    id=214340, name='Irradiated', school=School.NATURE, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=_DOSE_PCT,
                    die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded='Irradiated: a flat percent of damage done a stack, not a damage value'),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_HEALING_DONE_PERCENT, base_points=_DOSE_PCT,
                    die_sides=0, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded='Irradiated: a flat percent of healing done a stack, not a heal value')],
    spell_icon_id=_ICON_IRRADIATED,
    notes=f'{_VF}, VF1 the dose on every player: +3% damage and healing done a stack (the aura multiplies the '
          'per-stack '
          'amount). The DoseField machine (ViscousFalloutMachine.cpp) owns the count and mirrors it as the stack '
          'count, cast by Fallout (DungeonKit::AddStacks), on every change and every second (rule 25); the client '
          'counter shows at most 255 (CumulativeAura). Sources: Toxic Volley +2 (Saturated +4), any armed pool +1 a '
          'second, a failed glob +3 / +5, heroic Saturated +1 per 2 s. Normal: drains 1 per 3 s out of every pool; '
          'Radiation Sickness at 10 (dose to 0). Heroic: no drain, no cap, Leaking at 10, Meltdown at 20; Half-Life '
          'halves it (loses half, rounded up). A debuff nobody can remove: Dispel none, NO_IMMUNITIES (a bubble or Ice '
          'Block keeps it, rule 27), CHANGE_MAP; removed on his death, evade and reset, and at the pull. Irradiated '
          '9775\'s SV 1712 (VF_DOSE, a lasting green ghost glow).',
    raw_overrides=kit_raw('Irradiated by fallout. Damage and healing done increased, until it is too much.',
                          'Damage and healing done increased by $s1%.', CastingTimeIndex=1,
                          CumulativeAura=_AURA_STACK_LIMIT, SpellVisualID_1=VF_DOSE, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

dose_glow_214341 = _hidden_look(
    214341, 'Irradiated', VF_DOSE_BRIGHT, _ICON_GLOWY,
    f'{_VF}, VF1: the dose\'s second look, the bright glow at 7 dose and up on normal (near the cliff) and 10 and up '
    'on '
    'heroic (Leaking), added and removed by the script every second (Glowy (Green) 22577\'s SV 6594, VF_DOSE_BRIGHT).')

# --- VF2 Radiation Sickness ------------------------------------------------------------------------------------------

sickness_214342 = resolve_copy(
    214342, 'Radiation Sickness', School.NATURE, 'Overcome by the dose.',
    f'{_VF}, VF2 (normal): the sick player at 10 dose (the machine\'s cap, kit RegistryHit): 40% of the reference row '
    '(the tank row on the tank: the tank can get it), Weakened; rider 214344 (the 2 s stun); then the dose goes to 0. '
    'Emote line 1. Radiation Poisoning 11638\'s SV 1725 (VF_SICKNESS, a green burst).',
    icon=_ICON_RADIATION, visual=VF_SICKNESS,
)

sickness_pulse_214343 = resolve_copy(
    214343, 'Radiation Sickness', School.NATURE, 'Fallout splashes from a sick ally.',
    f'{_VF}, VF2 (normal): the pulse on every other player within 8 yd of the sick one, 20% of the reference row, no '
    'Weakened (kit RegistryHit).',
    icon=_ICON_RADIATION,
)

sickness_stun_214344 = spell(
    id=214344, name='Radiation Sickness', school=School.NATURE, dispel=0, mechanic=_MECHANIC_STUN,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=_STUN_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, mechanic=_MECHANIC_STUN,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_RADIATION,
    notes=f'{_VF}, VF2: the rider of 214342: stunned for 2 s while they vomit (the shared stun limit; mechanic stun, '
          'so '
          'a stun break or immunity answers it as any stun). Dispel none. Vomit 41995\'s SV 9446 (VF_VOMIT, one-shot).',
    raw_overrides=kit_raw('Stunned.', 'Vomiting. Stunned.', CastingTimeIndex=1, SpellVisualID_1=VF_VOMIT,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- VF3 Toxic Volley, VF4 Slough, the pools -------------------------------------------------------------------------

toxic_volley_214345 = resolve_copy(
    214345, 'Toxic Volley', School.NATURE, 'A wave of toxic fallout.',
    f'{_VF}, VF3: every player in the fight within 45 yd, every 15 s (heroic 12 s) with Slough (kit RegistryHit): 10% '
    'of the reference row (heroic 10% plus 3% per dose carried, no cap, ruling 18; x1.5 while Saturated), no '
    'Weakened, the tank row on the tank; rider 214346 (the Poison); +2 dose (+4 Saturated) and a 4 yd pool under each.',
    icon=_ICON_TOXIC_VOLLEY,
)

volley_poison_214346 = spell(
    id=214346, name='Toxic Volley', school=School.NATURE, dispel=_DISPEL_POISON, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=_POISON_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=_POISON_HUNDREDTHS,
                    die_sides=0, amplitude=_POISON_TICK_MS, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded=_SCRIPT_DAMAGE)],
    spell_icon_id=_ICON_TOXIC_VOLLEY,
    notes=f'{_VF}, VF3: the Volley\'s Poison, kept from the stock 21687 as a dispel reward (the kick and dispel '
          'table): '
          '1.00% of the reference row every 3 s for 15 s (the kit\'s spell_dungeon_refflat_periodic, base point 100 = '
          '1.00% in hundredths; the tank row on the tank). Dispel Poison (bots cure it, L4). Ignores caster modifiers.',
    raw_overrides=kit_raw('Poisoned by fallout.', 'Poisoned. Nature damage every $t1 sec.', CastingTimeIndex=1,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(volley_poison_214346, 'spell_dungeon_refflat_periodic')

fallout_pool_214347 = resolve_copy(
    214347, 'Fallout Pool', School.NATURE, 'Standing in fallout.',
    f'{_VF}, VF3-VF7: every player in any armed pool (Volley 4 yd, Slough 7 yd and growing on heroic, the glob\'s 5 '
    'yd, '
    'heroic Leaking 4 yd), once a second however many overlap (kit RegistryHit): 8% of the reference row, no Weakened '
    '(a lingering patch), the tank row on the tank; +1 dose. The pools are the script\'s (telegraph-only lasting rings '
    'for the bots, the nature disc on the pool stalker 301130).',
    icon=_ICON_RADIATION,
)

slough_214348 = self_visual(
    214348, 'Slough', VF_SLOUGH,
    f'{_VF}, VF4: he swells as he sheds a 7 yd pool under himself (emote line 0; the pool arms after the 2 s swell and '
    'lasts the fight, heroic +1 yd per 10 s). Cast on himself (triggered) with each Volley. Radiation Poisoning '
    '11638\'s SV 1725 (VF_SLOUGH, the green cast). Look only.',
    icon=_ICON_RADIATION, school=School.NATURE,
)

saturated_214349 = spell(
    id=214349, name='Saturated', school=School.NATURE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE,
                    base_points=_SATURATED_PCT, die_sides=0, misc_value=_SCHOOL_MASK_ALL,
                    implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Saturated: a flat percent of damage done, not a damage value')],
    spell_icon_id=_ICON_GLOWY,
    notes=f'{_VF}, VF5: on him while he stands in any armed pool (judged every 0.5 s, s7 #38 A (b)): +50% damage done '
          '(his melee; his script hits ignore caster modifiers, so the script multiplies them by 1.5 itself, '
          'Tune::kSaturatedScalesHits), his Volley +2 dose; heroic +1 dose to every player per 2 s. Added and removed '
          'by the script (Unit::AddAura). Dispel none (not purgeable); mechanic none (his immunity set 1972 never '
          'refuses it, rule 8). Glowy (Green) 22577\'s SV 6594 (VF_DOSE_BRIGHT) on him.',
    raw_overrides=kit_raw('Saturated with fallout. Damage done increased.', 'Damage done increased by $s1%.',
                          CastingTimeIndex=1, SpellVisualID_1=VF_DOSE_BRIGHT, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

volley_look_214356 = self_visual(
    214356, 'Toxic Volley', VF_VOLLEY,
    f'{_VF}, VF3: the Volley\'s look on him as it lands (triggered; the hits are 214345). Toxic Volley 21687\'s SV '
    '4202 '
    '(VF_VOLLEY, the nature precast). Look only.',
    icon=_ICON_TOXIC_VOLLEY, school=School.NATURE,
)

# --- VF6 Corrosive Ooze ----------------------------------------------------------------------------------------------

ooze_lob_214350 = spell(
    id=214350, name='Corrosive Ooze', school=School.NATURE, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
    spell_icon_id=_ICON_CORROSIVE_OOZE,
    notes=f'{_VF}, VF6: the glob in flight, cast by him (triggered) at the 5 yd circle\'s center, launched so it lands '
          'as the 2 s warning ends (GlobLaunchDelayMs). WP-V\'s arcing glob SV 90750 (VF_GLOB: Acid Spit 854 with an '
          'arc; the stock 1484 is WRONG, one puff) at 20 yd/s. Look only (the hit is 214351).',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=VF_GLOB, Speed=_GLOB_SPEED,
                          Targets=_TARGET_FLAG_DEST_LOCATION, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

corrosive_ooze_214351 = resolve_copy(
    214351, 'Corrosive Ooze', School.NATURE, 'A glob of corrosive ooze.',
    f'{_VF}, VF6: the 5 yd circle where a random player (tank included; heroic two) stood, 2 s: 40% / 60% of the '
    'reference row (x1.5 while Saturated), Weakened, the tank row on the tank; +3 / +5 dose to each player hit; a 5 yd '
    'pool for 30 s where it lands.',
    icon=_ICON_CORROSIVE_OOZE,
)

# --- VF8 Meltdown, VF9 Half-Life (heroic) ----------------------------------------------------------------------------

half_life_bar_214352 = spell(
    id=214352, name='Half-Life', school=School.NATURE, cast_time_ms=_HALF_LIFE_CAST_MS, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_RADIATION,
    notes=f'{_VF}, VF9 (heroic): the 3 s bar every 30 s from 30 s, emote line 2: everyone within 10 yd of him at its '
          'end loses half the dose (rounded up: ViscousFalloutLogic.h Halve, one rule for Half-Life and the hard '
          'mode\'s plates) and he heals 0.5% of his maximum health per dose shed (214353). Bots: a Stack for 8 dose '
          'and up, a keep-out for the rest. No effect: the AI resolves it on its clock. Not interruptible '
          '(InterruptFlags 0, PreventionType 0: the kick and dispel table); keeps his swing timer.',
    raw_overrides=kit_raw('Decays, shedding the dose of everyone close.', InterruptFlags=0, PreventionType=0,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=_ATTR2_DO_NOT_RESET_COMBAT_TIMERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

half_life_heal_214353 = spell(
    id=214353, name='Half-Life', school=School.NATURE, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL, base_points=0, die_sides=0, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded=_SCRIPT_HEAL)],
    spell_icon_id=_ICON_RADIATION,
    notes=f'{_VF}, VF9: his heal at the bar\'s end, cast triggered on himself with the base point set from the script '
          '(0.5% of his maximum health per dose shed, s7 #38 A (c)). Ignores caster modifiers (the dose aura is on '
          'players, never on him); healing-reduction effects on him still count.',
    raw_overrides=kit_raw('Heals the caster.', instant=True, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG),
)

meltdown_214354 = resolve_copy(
    214354, 'Meltdown', School.NATURE, 'Melting down.',
    f'{_VF}, VF8 (heroic): a carrier at 20 dose and up takes 5% of the reference row a second (kit RegistryHit), and '
    'everyone else within 6 yd of each carrier takes 5% a tick from the lasting 6 yd registry Spread on the carrier '
    '(two carriers side by side tick each other). No Weakened; the tank row on the tank.',
    icon=_ICON_RADIATION,
)

meltdown_aura_214355 = spell(
    id=214355, name='Meltdown', school=School.NATURE, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_RADIATION,
    notes=f'{_VF}, VF8 (heroic): the read on a carrier at 20 dose and up (emote line 4 once a pull): added by the '
          'script with the 6 yd Spread and removed when the dose falls below 20 (Half-Life), at death and at every '
          'cleanup. Dispel none, NO_IMMUNITIES, CHANGE_MAP. No look of its own (the ring and the bright glow carry '
          'it).',
    raw_overrides=kit_raw('Melting down.', 'Melting down: you and everyone within 6 yd take damage every second. '
                          'Shed your dose.', CastingTimeIndex=1, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- 301130 the pool stalker -----------------------------------------------------------------------------------------

pool_stalker_301130 = creature_template(
    POOL_STALKER, 'Fallout Pool', **{**KIT_HELPER, 'minlevel': 28, 'maxlevel': 28, 'rank': 0, 'unit_class': 1,
                                     'flags_extra': 0x40 | 0x80, 'ScriptName': 'npc_gnomer_pool_stalker'},
)
creature_model(POOL_STALKER, display_id=DISPLAY_NATURE_DISC)
