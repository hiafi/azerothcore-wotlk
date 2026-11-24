"""
Scarlet Monastery build WP-D5: Houndmaster Loksey (3974; Loksey's Tracking Hound 300908, Kennel Pup 300909)
(.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.5 row D5; build spec
docs/dungeons/scarlet-monastery-2-library.md "Houndmaster Loksey", LK1-LK6). WP-D5 owns this file (its spells:
kSpellsLoksey 212540-212569 of modules/mod-dungeon-bosses src/ScarletMonastery/ScarletMonasteryRework.h; LokseyLogic.h
names the same ids; the texts and the Tracking Hound spawn deletes are the core SQL rev
rev_loksey_scarlet_monastery.sql).

- 3974 Houndmaster Loksey: boss_houndmaster_loksey_rework (SmartAI off: WP-S0's rev drops his two rows; Bloodlust
  6742 is retired as his cast), the build spec's normal health (38k = HealthModifier 39.297 on the level 34 paladin
  class base 967), stun immunity 1972, INSTANCE_BIND, DamageModifier the stock 2.4 (S0's column, kept). Heroic 210k and
  the tier's melee are WP-H's overrides (source/world/dungeons/scarlet_monastery.py).
- 300908 Loksey's Tracking Hound: the boss-kit add (LIB "Build spec"), its own entry on the stock hound's display (CDI
  2709, the hyena), a beast of the stock hound's family (25), level 33, 3,000 health (HealthModifier 2.7027 on the
  level 33 warrior base 1,110), no stun immunity (a stun holds a dog off its marker), no loot, no XP. DamageModifier
  1.1 (this WP's default: three hounds and six pups on the tank add up to 6.3, under one stock Scarlet pack of four at
  1.7 each (6.8); the spec leaves the dogs' melee unset, rule 19). Three at his feet, summoned by the script (the stock
  guids 40089-40091 are deleted).
- 300909 Kennel Pup: level 32, 800 health (HealthModifier 0.7568 on the level 32 warrior base 1,057), the same
  display at 0.7 scale, DamageModifier 0.5, summoned only (two entries on the hall's rim, 3 a Release).
- Heroic copies (15k / 4k, and their `difficulty_entry_1`) are WP-H's: the lines are in this WP's report.

Spells. His damage is a percent of the reference row (the tank row on the tank): the Mark landings and the Correction
cone through the registry (resolve copies), the tank's Correction through the kit's spell_dungeon_refflat_damage
(hundredths in the value, heroic in EffectMiscValueB). Every damage spell ignores caster modifiers (rule 2):

  212540  Release the Hounds   LK2 heroic: the 2.5 s whistle, interruptible (Nature); a finished one brings 6 pups, a
                               kicked one 3 (the script's OnSpellCast / OnSpellFailed)
  212541  Whistle              LK1 look: the whistle's animation and sound (8839), cast by him on himself each round
  212542  Scent                LK3 the 5 s debuff on the carrier (the orange rune ring under them), not dispellable
  212543  Scent                LK3 look: the scent pouch's flash on the carrier (15364)
  212544  Hound Leap           LK3 a marker's landing: 35% / 45% + Weakened, 5 yd (resolve copy, Physical)
  212545  Whipped Frenzy       LK4 / LK6 +50% attack speed and damage a stack, 30 s (heroic: until the dog dies,
                               stacking without a cap); Magic: a purge removes it
  212546  Frenzy               LK4 his own when no dog lives: +30% attack speed, 15 s, Magic
  212547  Correction           LK5 the 2 s bar (Physical, not interruptible)
  212548  Correction           LK5 the cone's hit: 30% / 40% + Weakened (resolve copy, Physical)
  212549  Correction           LK5 the tank's own hit: 20% / 30% of the tank row
  212550  Fetch                LK6 the thrown stick: a missile at the landing circle, look only
  212551  Cowed                LK6 a caught Fetch: the dogs are pacified and rooted for 6 s and take 25% more damage
  212552-212569 spare.

Visual ids are WP-V's (._visuals; every look is unconfirmed until seen in game).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    self_visual,
)
from lib.dsl.registry import (
    creature_model,
    creature_template,
    creature_template_columns,
    scripted_by,
    spell,
)

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    KIT_CREATURE,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_TRACKING_HOUND,
    LK_CORRECTION,
    LK_FETCH,
    LK_LEAP_LANDING,
    LK_SCENT,
    LK_SCENT_RING,
    LK_WHIPPED_FRENZY,
    LK_WHISTLE,
    PUP_SCALE,
)

_D5 = 'Scarlet Monastery build WP-D5 (Houndmaster Loksey)'
_SCRIPT_REFFLAT = ('Scarlet Monastery: a percent of reference health in hundredths, set by the kit\'s '
                   'spell_dungeon_refflat_damage (DungeonKit::RefFlatOn)')

creature_template_columns(3974, **boss_columns(
    'boss_houndmaster_loksey_rework', 39.297, damage_modifier=2.4,
))

# --- constants (LokseyLogic.h; lib/test_scarlet_monastery_loksey.py pins each against the header) ---------------------

RELEASE_CAST_MS = 2500          # kReleaseCastMs
SCENT_MS = 5000                 # kScentMs
FRENZY_NORMAL_MS = 30000        # kFrenzyNormalMs
FRENZY_PCT = 50                 # kWhippedFrenzyPct: attack speed and damage, a stack
LOKSEY_FRENZY_MS = 15000        # kLokseyFrenzyMs
LOKSEY_FRENZY_PCT = 30          # kLokseyFrenzyHastePct
CORRECTION_CAST_MS = 2000       # kCorrectionCastMs
CORRECTION_TANK = (2000, 3000)  # kCorrectionTankPct 20 / 30 (hundredths)
FETCH_SPEED = 10.0              # kFetchMissileSpeed
COWED_MS = 6000                 # kCowedMs
COWED_TAKEN_PCT = 25            # kFetchCowedTakenPct

HOUND = 300908
PUP = 300909
HOUND_LEVEL = 33
PUP_LEVEL = 32
HOUND_HEALTH_MODIFIER = 2.7027      # ceil(1,110 x 2.7027) = 3,000 (kHoundHealth normal)
PUP_HEALTH_MODIFIER = 0.7568        # ceil(1,057 x 0.7568) = 800 (kPupHealth normal)
HOUND_DAMAGE_MODIFIER = 1.1
PUP_DAMAGE_MODIFIER = 0.5
HOUND_FAMILY = 25                   # the stock Scarlet Tracking Hound's (hyena)

_FLAGS_EXTRA_NO_XP = 0x40
_CREATURE_TYPE_BEAST = 1
_SPELL_INTERRUPT_FLAGS_KICK = 15
_PREVENTION_SILENCE = 1
_DEFENSE_MAGIC = 1
_DEFENSE_MELEE = 2
_DISPEL_MAGIC = 1
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_SCHOOL_MASK_ALL = 127
_STACKS_NO_CAP = 255
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40

# Stock icons (Spell.dbc SpellIconID of the named spell)
_ICON_WHISTLE = 455             # Huffer's Whistle 38362
_ICON_SCENT = 3222              # Scent of Blood 72769
_ICON_LEAP = 3139               # Leap 47482
_ICON_FRENZY = 38               # Whipped Frenzy 34086 / Bloodlust 6742
_ICON_CLEAVE = 277              # Cleave 15496
_ICON_GENERIC = 1               # Pet Toy - Fetch Ball 48650

# --- 300908 Loksey's Tracking Hound, 300909 Kennel Pup ---------------------------------------------------------------

# The entries are written as numbers: source/world/dungeons/scarlet_monastery.py finds the declared kit adds by the
# pattern `creature_template(<entry>, ...)` (WP-H) and gives them their heroic health. Their `difficulty_entry_1` is
# WP-H's lock line (heroic_ids.lock, the wave 1 kit units in entry order: F-1a's reconcile).
HOUND_HEROIC = 310465
PUP_HEROIC = 310466
_DOG = {
    **KIT_CREATURE, 'type': _CREATURE_TYPE_BEAST, 'family': HOUND_FAMILY, 'rank': 0, 'unit_class': 1,
    'unit_flags': 0, 'BaseAttackTime': 2000, 'speed_run': 1.14286, 'detection_range': 20.0,
    'CreatureImmunitiesId': 0, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0,
    'flags_extra': _FLAGS_EXTRA_NO_XP,
}

hound_300908 = creature_template(300908, "Loksey's Tracking Hound", **{
    **_DOG, 'minlevel': HOUND_LEVEL, 'maxlevel': HOUND_LEVEL, 'HealthModifier': HOUND_HEALTH_MODIFIER,
    'DamageModifier': HOUND_DAMAGE_MODIFIER, 'ScriptName': 'npc_sm_loksey_hound', 'difficulty_entry_1': HOUND_HEROIC,
})
creature_model(HOUND, display_id=DISPLAY_TRACKING_HOUND)

pup_300909 = creature_template(300909, 'Kennel Pup', **{
    **_DOG, 'minlevel': PUP_LEVEL, 'maxlevel': PUP_LEVEL, 'HealthModifier': PUP_HEALTH_MODIFIER,
    'DamageModifier': PUP_DAMAGE_MODIFIER, 'ScriptName': 'npc_sm_kennel_pup', 'difficulty_entry_1': PUP_HEROIC,
})
creature_model(PUP, display_id=DISPLAY_TRACKING_HOUND, scale=PUP_SCALE)

# --- LK1 / LK2 the whistle, Release the Hounds -----------------------------------------------------------------------

release_the_hounds_212540 = spell(
    id=212540, name='Release the Hounds', school=School.NATURE, cast_time_ms=RELEASE_CAST_MS, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_WHISTLE,
    notes=f'{_D5}, LK2 (heroic): the 2.5 s whistle that brings the pups (yell 0 as it starts), once a 48 s cycle (the '
          'Release round, 12 s a round). DUMMY on the caster, 2.5 s (LokseyLogic.h kReleaseCastMs). A finished bar '
          '(OnSpellCast) brings 6 Kennel Pups, a kicked one (OnSpellFailed) 3. Interruptible (InterruptFlags 15) '
          'and silence-preventable (PreventionType 1): his immunity set 1972 lets both work. Nature: Correction is '
          'Physical, so a kick here never locks the Correction bar (rule 5). The interrupt list names it (priority '
          '3, expected). The whistle look (SV 8839: the animation and the PetCall sound) plays as the bar starts.',
    raw_overrides=kit_raw('Loksey whistles for the pack. Interrupt it, or more pups come.',
                          InterruptFlags=_SPELL_INTERRUPT_FLAGS_KICK, PreventionType=_PREVENTION_SILENCE,
                          DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=LK_WHISTLE, AttributesEx4=ATTR4_NO_CAST_LOG),
)

whistle_212541 = self_visual(
    212541, 'Whistle', LK_WHISTLE,
    f'{_D5}, LK1: the whistle of every round that is not the heroic Release bar (Mark, Heel, Fetch, and the normal '
    "Release and the pull's): Huffer's Whistle 38362's animation and PetCall sound (SV 8839), cast by him on himself "
    '(triggered). The emote line names the command.',
    icon=_ICON_WHISTLE,
)

# --- LK3 Mark: the Scent, the landings -------------------------------------------------------------------------------

scent_212542 = spell(
    id=212542, name='Scent', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=SCENT_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_SCENT,
    notes=f'{_D5}, LK3: the Scent. Cast by Loksey (triggered) on a random player, never the tank '
          'or the healer (1; heroic 2; STAGE-R-1-LIB Q1, F-4b), 5 s (LokseyLogic.h kScentMs). When it ends the dogs '
          'come: one 5 yd marker every '
          '0.5 s round the carrier, '
          'one per free dog. A DUMMY debuff: the read is the orange rune ring under the carrier (the shipped SV 90613, '
          'V: the lasting mark; the Scent of Blood flash is 212543). Not dispellable (Dispel none) and '
          'NO_IMMUNITIES (the trail still comes). AuraInterruptFlags CHANGE_MAP; the script removes it from everyone '
          'on a reset, evade and death.',
    raw_overrides=kit_raw('Loksey has your scent. Run from the pack: when this ends the dogs come for you.',
                          'The hounds follow this trail. Keep away from the others and keep moving.',
                          CastingTimeIndex=1, SpellVisualID_1=LK_SCENT_RING, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

scent_flash_212543 = spell(
    id=212543, name='Scent', school=School.NORMAL, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_SCENT,
    notes=f'{_D5}, LK3: the scent pouch\'s flash on the carrier, cast by Loksey (triggered) beside the Scent: Scent of '
          'Blood 72769\'s one-shot shadow hands (SV 15364; its State kit is empty, so the ring of 212542 carries '
          'the lasting look). A DUMMY on a target, no effect.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=LK_SCENT, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

hound_leap_212544 = resolve_copy(
    212544, 'Hound Leap', School.NORMAL, 'A hound leaps onto the trail.',
    f'{_D5}, LK3: a marker\'s landing, 5 yd, 1.5 s after the marker drops: 35% (heroic 45%) of the reference row '
    '(the tank row on the tank) and 1 Weakened to everyone inside, the carrier too (registry tag 3). Copy of the '
    'mod-boss-mechanics resolve spell 205001 (Physical). Pounce 39449\'s animation and blood burst on every player '
    'hit (SV 9006).',
    icon=_ICON_LEAP, visual=LK_LEAP_LANDING,
)

# --- LK4 Heel: the frenzies ------------------------------------------------------------------------------------------

whipped_frenzy_212545 = spell(
    id=212545, name='Whipped Frenzy', school=School.NORMAL, dispel=_DISPEL_MAGIC, mechanic=0, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=FRENZY_NORMAL_MS,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_MELEE_HASTE, base_points=FRENZY_PCT, die_sides=0,
               implicit_target_a=TARGET_UNIT_TARGET_ANY,
               potency_excluded='Whipped Frenzy: a flat +50% attack speed a stack, not a damage or heal value'),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=FRENZY_PCT,
               die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_TARGET_ANY,
               potency_excluded='Whipped Frenzy: a flat +50% damage done a stack, not a damage or heal value'),
    ],
    spell_icon_id=_ICON_FRENZY,
    notes=f'{_D5}, LK4 / LK6: the dog the whistle whips: +50% attack speed and +50% damage done a stack, 30 s on '
          'normal (one dog at a time: the 45 s cycle outlasts it). Heroic: the script makes it last until the dog '
          'dies (SetMaxDuration -1) and a second whip, or a missed Fetch, adds a stack (CumulativeAura 255, no cap). '
          'A Magic buff (Dispel 1): a purge removes it, on the purge list (a reward). Cast by Loksey (triggered) on '
          'the dog; the dog grows 30% (the script, a look). Whipped Frenzy 34086\'s lasting hands (SV 8147).',
    raw_overrides=kit_raw('Whipped into a frenzy.', 'Attack speed and damage increased by $s1%.', CastingTimeIndex=1,
                          CumulativeAura=_STACKS_NO_CAP, SpellVisualID_1=LK_WHIPPED_FRENZY,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

loksey_frenzy_212546 = spell(
    id=212546, name='Frenzy', school=School.NORMAL, dispel=_DISPEL_MAGIC, mechanic=0, attributes=0, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=LOKSEY_FRENZY_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_MELEE_HASTE, base_points=LOKSEY_FRENZY_PCT,
                    die_sides=0, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Frenzy: a flat +30% attack speed, not a damage or heal value')],
    spell_icon_id=_ICON_FRENZY,
    notes=f'{_D5}, LK4: the Heel with no dog alive: Loksey whips himself (emote line 3): +30% attack speed, 15 s '
          '(a spike on the tank). A Magic buff (Dispel 1), on the purge list (a reward). Whipped Frenzy 34086\'s '
          'lasting hands (SV 8147). AuraInterruptFlags CHANGE_MAP; the script removes it on a reset.',
    raw_overrides=kit_raw('Works himself into a frenzy.', 'Attack speed increased by $s1%.', CastingTimeIndex=1,
                          SpellVisualID_1=LK_WHIPPED_FRENZY, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- LK5 Correction --------------------------------------------------------------------------------------------------

correction_cast_212547 = cast_bar(
    212547, 'Correction', CORRECTION_CAST_MS, 'Loksey swings his Training Stick.',
    f'{_D5}, LK5: the 2 s cast bar of the cone (a 90 degree, 8 yd cone in front of him), first at 6 s and every 10 s. '
    'Not interruptible (cast_bar): the registry cone owns the hit (212548) and the tank\'s own hit follows it '
    '(212549). Physical, a school the Release whistle (Nature) does not use. Cleave 15496\'s swing (SV 219) plays as '
    'the bar starts.',
    icon=_ICON_CLEAVE, visual=LK_CORRECTION, school=School.NORMAL,
)

correction_hit_212548 = resolve_copy(
    212548, 'Correction', School.NORMAL, 'The Training Stick lands.',
    f'{_D5}, LK5: the cone\'s hit on everyone but the tank (TankExempt): 30% (heroic 40%) of the non-tank row and 1 '
    'Weakened (registry tag 5). Copy of the resolve spell 205001 (Physical).',
    icon=_ICON_CLEAVE,
)

correction_tank_212549 = spell(
    id=212549, name='Correction', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=CORRECTION_TANK[0] - 1, die_sides=1,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_CLEAVE,
    notes=f'{_D5}, LK5: the tank\'s hit. The registry cone skips Loksey\'s victim (TankExempt), so he casts this on '
          'his victim (triggered) when the cone resolves with the victim inside it: 20% (heroic 30%: '
          'EffectMiscValueB) of the tank row through spell_dungeon_refflat_damage (RefFlatOn), Physical, armor '
          'applies, no Weakened (the tank). The resolve set\'s attributes (always hits, cannot crit, ignores caster '
          'modifiers, no threat).',
    raw_overrides=kit_raw('Hits the target with the Training Stick for 20% of the tank reference health.',
                          instant=True, DefenseType=_DEFENSE_MELEE, EffectMiscValueB_1=CORRECTION_TANK[1],
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(correction_tank_212549, 'spell_dungeon_refflat_damage')

# --- LK6 Fetch (heroic) ----------------------------------------------------------------------------------------------

fetch_throw_212550 = spell(
    id=212550, name='Fetch', school=School.NORMAL, attributes=ATTR0_DO_NOT_LOG, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
    spell_icon_id=_ICON_GENERIC,
    notes=f'{_D5}, LK6: the thrown stick, a no-effect missile Loksey casts at the landing circle (triggered). Pet Toy '
          '- Fetch Ball - Throw Ball 48650\'s throw animation and red yarn ball (SV 10809: the stick has no model, '
          'so the ball is the thrown thing). Speed 10 yd/s = LokseyLogic.h kFetchMissileSpeed: the script launches '
          'it so it lands as the 3 s circle resolves (FetchLaunchDelayMs).',
    raw_overrides=kit_raw('Loksey throws his Training Stick.', SpellVisualID_1=LK_FETCH, Speed=FETCH_SPEED,
                          Targets=_TARGET_FLAG_DEST_LOCATION, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          CastingTimeIndex=1),
)

cowed_212551 = spell(
    id=212551, name='Cowed', school=School.NORMAL, dispel=0, mechanic=0, attributes=0, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=COWED_MS,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_PACIFY, base_points=0,
               implicit_target_a=TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_ROOT, base_points=0,
               implicit_target_a=TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN,
               base_points=COWED_TAKEN_PCT, die_sides=0, misc_value=_SCHOOL_MASK_ALL,
               implicit_target_a=TARGET_UNIT_CASTER,
               potency_excluded='Cowed: a flat +25% damage taken, not a damage or heal value'),
    ],
    spell_icon_id=_ICON_GENERIC,
    notes=f'{_D5}, LK6: a caught Fetch: every dog sits and cowers for 6 s, an AoE window. Cast by each dog on itself '
          '(triggered): pacified (no attacks) and rooted, never a stun (pacify and root are not the stun the '
          'boss-stun immunity set 1972 stops; the dogs have no immunity set anyway); +25% damage taken. The dog\'s '
          'sit is the script\'s (a look). Not dispellable. AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('Cowering. Cannot attack or move; takes more damage.',
                          'Cannot attack or move. Damage taken increased by $s3%.', CastingTimeIndex=1,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
