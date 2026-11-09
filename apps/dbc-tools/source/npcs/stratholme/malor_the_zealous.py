"""
Stratholme build WP-S4: Malor the Zealous (11032), normal and heroic
(.agents/plans/stratholme-build/stratholme-build.HANDOFF.md s3.4 rows MZ, s3.5 row S4, s3.6; build spec
docs/dungeons/stratholme-rework.md ST 1239-1289, design ST 1150-1238). WP-S4 owns this file (its spells: kSpellsMalor
206480-206499 of modules/mod-dungeon-bosses src/Stratholme/StratholmeRework.h only; MalorLogic.h names the same ids;
its creature: 300605). The engine side is src/Stratholme/boss_malor_the_zealous_rework.cpp.

- 11032 Malor the Zealous: boss_malor_the_zealous_rework (SmartAI off; WP-S4's SQL rev drops the four stock rows and
  adds his texts), the build spec's normal health (175k: HealthModifier 71.663 on the level 60 paladin class base
  2,442), stun immunity 1972 (handoff s7 #3; the build spec's own set is "stun immune, interruptible"), INSTANCE_BIND
  (flags_extra 1), DamageModifier 3.5 (the stock value: base SQL; the live 6.75 is a mod-progression leftover). Heroic
  230k is WP-H's override (source/world/dungeons/stratholme.py). Retired: Head Crack 16172, the instant Ground Smash
  12734 and Lay on Hands 10310 as a full heal. His Holy Light is his own interruptible cast (206490).
- 300605 Medallion of Faith (the build spec's Medallion stalker): an invisible, unselectable trigger (KIT_HELPER, the
  Eye of the Blizzard's shape) the script summons on Malor's Strongbox 176112 (3617.53, -3130.55) at the pull. It casts
  the blaze's beam at Malor. The strongbox itself is untouched (Aurius's quest). Not a combat add: no heroic template
  (handoff s7 #15).

Spells. The Ground Smash and its Aftershock deal their damage through dungeon copies of the mod-boss-mechanics resolve
spell (the registry's percent of the reference row; the combat log names the mechanic). Judgment's hit and Searing
Faith's ticks are the kit's generic percent spells (spell_dungeon_refflat_damage / _periodic: hundredths in the effect
value, heroic in EffectMiscValueB; KT-1). The heals are exact amounts from the script (base point 0). The rest are
auras the AI applies, casts and looks:

  206480  The Medallion's Blaze  MZ1 the beam, a 12 s channel by the stalker at Malor (Light Beam 52407's SV 11500)
  206481  Faith                  MZ3 on Malor: +5% damage done per stack, 10 stacks (Zeal 8191's SV 211)
  206482  Searing Faith          MZ4 on a blocker: Holy damage every second per stack (2% / 3% of the row)
  206483  Searing Faith          MZ4 the look each second a blocker burns (Holy Fire 14914's SV 3400)
  206484  Unclean                MZ5 8 s, purified by 2 s in the beam (Tainted Mind 16567's SV 339)
  206485  Judgment               MZ6 the Unclean player's hit when it runs out: Holy 40% / 50% (SV 5651)
  206486  Ground Smash           MZ7 the 2 s windup bar (not kickable)
  206487  Ground Smash           MZ7 the circle's hit: resolve copy (Physical), Smash 42669's SV 9612
  206488  Stunned                MZ7 the rider: a 1 s stun
  206489  Aftershock             MZ8 heroic: the ring's hit: resolve copy (Physical), SV 9612
  206490  Holy Light             MZ9 the 2.5 s cast, kickable; finished, his heal (Holy Light 635's SV 2936)
  206491  Holy Light             MZ9 his heal: 1% of his health per Faith stack (heroic 3% and 1%), exact amount
  206492  Miracle                MZ10 the 3 s cast bar, not kickable (Lay on Hands 10310's SV 132)
  206493  Miracle                MZ10 his heal: 8% of his health per Faith stack, exact amount
  206494-206499 spare.

Tooltips are number-free (ST checklist item 8, Systems.md s10).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
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
    ML_BLAZE_BEAM,
    ML_HOLY_FIRE,
    ML_JUDGMENT,
    ML_LAY_ON_HANDS,
    ML_SMASH_BURST,
    ML_TAINTED_MIND,
    ML_ZEAL,
)

# Held back until wave 2 binds this boss (_common.py BIND_WAVE_2): stock until then.
if BIND_WAVE_2:
    creature_template_columns(11032, **boss_columns(
        'boss_malor_the_zealous_rework', 71.663, damage_modifier=3.5,
    ))

_MZ = 'Stratholme build WP-S4 (Malor the Zealous)'
_SCRIPT_REFFLAT = ('Stratholme: a percent of reference health in hundredths, set at launch by the kit\'s '
                   'spell_dungeon_refflat_damage / _periodic (DungeonKit::RefFlatOn)')
_SCRIPT_EXACT = 'Stratholme: an exact amount from the script (CastCustomSpell base point 0)'

_ATTR1_IS_CHANNELED = 0x00000004
_INTERRUPT_FLAGS_STANDARD = 15      # movement, pushback, interrupt, auto-attack: a kickable cast
_PREVENTION_SILENCE = 1
_MECHANIC_STUN = 12
# AURA_INTERRUPT_FLAG_CHANGE_MAP (SpellDefines.h): AC drops the aura before the logout save, after the login load and on
# a cross-map teleport, so a debuff never outlives the instance on the character.
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_SCHOOL_MASK_ALL = 127

# Looks: V-2's picks (._visuals ML_*); every one is unconfirmed until seen in game. Holy Light 635's SV 2936 has no
# ML_ name (V-2 listed none), so it stays here.
SV_BLAZE_BEAM = ML_BLAZE_BEAM       # WotLK Prologue Light Beam 52407: chain 568 HealBeam, a gold wavy beam
SV_FAITH = ML_ZEAL                  # Zeal 8191 (shared with Inner Fire): hands and a crown rune
SV_SEARING = ML_HOLY_FIRE           # Holy Fire 14914: gold hands, a gold burst and an orange plume (one-shot)
SV_UNCLEAN = ML_TAINTED_MIND        # Tainted Mind 16567: shadow hands, a rune ring and a chest state
SV_JUDGMENT = ML_JUDGMENT           # Judgement of Light 20271: holy hands and the gold judgement flash
SV_SMASH = ML_SMASH_BURST           # Smash 42669: the warrior shockwave dust ring on the caster
SV_HOLY_LIGHT = 2936                # Holy Light 635
SV_MIRACLE = ML_LAY_ON_HANDS        # Lay on Hands 10310: holy hands and a light on the target

_ICON_HOLY_LIGHT = 70               # Holy Light 635
_ICON_ZEAL = 51                     # Zeal 8191
_ICON_HOLY_FIRE = 156               # Holy Fire 14914
_ICON_TAINTED_MIND = 114            # Tainted Mind 16567
_ICON_JUDGMENT = 205                # Judgement of Light 20271
_ICON_SMASH = 277                   # Smash 42669
_ICON_LAY_ON_HANDS = 79             # Lay on Hands 10310

# Percents in hundredths (KT-1's generic percent spells): the shown value is EffectBasePoints + 1 as stored, the heroic
# value EffectMiscValueB.
_SEARING_TICK = (200, 300)          # MalorLogic.h kSearingPct 2 / 3
_JUDGMENT = (4000, 5000)            # kJudgmentPct 40 / 50
_FAITH_DAMAGE_PCT = 5               # kFaithDamagePct, per stack
_FAITH_MAX = 10                     # kFaithMax
_SEARING_MAX = 12                   # kSearingMaxStacks: one per second of a 12 s blaze
_BLAZE_MS = 12000                   # kBlazeMs
_UNCLEAN_MS = 8000                  # kUncleanMs
_SMASH_CAST_MS = 2000               # kSmashCastMs
_STUN_MS = 1000                     # kSmashStunMs
_HOLY_LIGHT_CAST_MS = 2500          # kHolyLightCastMs
_MIRACLE_CAST_MS = 3000             # kMiracleCastMs

# --- 300605 Medallion of Faith ---------------------------------------------------------------------------------------

medallion_stalker_300605 = creature_template(
    300605, 'Medallion of Faith', **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1,
                                     'type': 10, 'flags_extra': 0x40 | 0x80, 'ScriptName': ''},
)
creature_model(300605, display_id=DISPLAY_INVISIBLE_STALKER)


def _refflat_hit(spell_id: int, name: str, school: School, pct: tuple[int, int], icon: int, desc: str, notes: str,
                 *, visual: int = 0):
    """A hit at a percent of the reference row (the kit's spell_dungeon_refflat_damage), cast by Malor (triggered):
    always hits, cannot crit, ignores his modifiers (the target's own defensives count)."""
    s = spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=pct[0] - 1, die_sides=1,
                        implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_REFFLAT)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, instant=True, InterruptFlags=0, PreventionType=0, EffectMiscValueB_1=pct[1],
                              SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                              AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )
    scripted_by(s, 'spell_dungeon_refflat_damage')
    return s


def _heal(spell_id: int, name: str, icon: int, desc: str, notes: str, *, visual: int = 0):
    """His heal, an exact amount from the script (CastCustomSpell base point 0, triggered, on himself). Ignores his
    modifiers; a healing reduction on him (Mortal Strike) cuts it."""
    return spell(
        id=spell_id, name=name, school=School.HOLY, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.HEAL, base_points=0, die_sides=0, implicit_target_a=TARGET_UNIT_CASTER,
                        potency_excluded=_SCRIPT_EXACT)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, instant=True, InterruptFlags=0, PreventionType=0, SpellVisualID_1=visual,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- MZ1 The blaze ---------------------------------------------------------------------------------------------------

blaze_206480 = spell(
    id=206480, name='The Medallion\'s Blaze', school=School.HOLY, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_BLAZE_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_HOLY_LIGHT,
    notes=f'{_MZ}, MZ1: the beam of holy light from the strongbox to Malor, every 30 s from 10 s (emote line 1): a '
          '12 s channel the Medallion stalker 300605 casts (triggered) at Malor on the strongbox, so the beam is drawn '
          'between the two units and follows him. Nothing in the spell does anything: a DUMMY aura on Malor and the '
          'channel\'s look. The hit rules are the AI\'s (boss_malor_the_zealous_rework: every second the beam reaches '
          'him unblocked he gains Faith, or a non-tank standing in the 3 yd lane takes Searing Faith). Not '
          'interruptible, ignores LoS (the beam crosses the dais wall); the AI stops it when the blaze ends early. '
          'WotLK Prologue Light Beam 52407\'s SV 11500 (chain 568 HealBeam, a 0.35 wide gold wave).',
    raw_overrides=kit_raw('A beam of holy light feeds the Zealot.', 'Fed by the Medallion of Faith.',
                          CastingTimeIndex=1, InterruptFlags=0, ChannelInterruptFlags=0, PreventionType=0,
                          SpellVisualID_1=SV_BLAZE_BEAM, AttributesEx=_ATTR1_IS_CHANNELED | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- MZ3 Faith -------------------------------------------------------------------------------------------------------

faith_206481 = spell(
    id=206481, name='Faith', school=School.HOLY, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE,
                    base_points=_FAITH_DAMAGE_PCT, die_sides=0, misc_value=_SCHOOL_MASK_ALL,
                    implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Faith: a flat +5% damage done per stack, not a damage or heal value')],
    spell_icon_id=_ICON_ZEAL,
    notes=f'{_MZ}, MZ3: his stacking buff. Each second of a blaze that the beam reaches him unblocked gives one stack '
          '(heroic two), up to 10 (DungeonKit::AddStacks, CumulativeAura 10); one stack fades every 8 s (the AI\'s '
          'clock, so the aura has no duration). +5% damage done per stack (the engine multiplies the amount by the '
          'stack count), every school: it raises his melee and his stock blows; the reference-sized hits ignore caster '
          'modifiers, so they stay exact. Holy Light and the Miracle read the stack count for their heals. Not '
          'dispellable; removed on his death, evade and reset. Zeal 8191\'s SV 211 (hands and a crown rune).',
    raw_overrides=kit_raw('Faith: damage done increased.', 'Damage dealt increased.', instant=True,
                          CumulativeAura=_FAITH_MAX, SpellVisualID_1=SV_FAITH, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- MZ4 Searing Faith -----------------------------------------------------------------------------------------------

searing_faith_206482 = spell(
    id=206482, name='Searing Faith', school=School.HOLY, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE,
                    base_points=_SEARING_TICK[0] - 1, die_sides=1, amplitude=1000,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_HOLY_FIRE,
    notes=f'{_MZ}, MZ4: the blocker\'s burn. A non-tank standing in the beam gains a stack each second of a blaze '
          '(DungeonKit::AddStacks, caster Malor, CumulativeAura 12: one per second of the blaze); one stack fades '
          'every 2 s once out of the beam (the AI\'s clock, so the aura has no duration). Each stack burns Holy damage '
          'every second: 2% normal / 3% heroic of the reference row per stack (spell_dungeon_refflat_periodic: 200 '
          'hundredths, heroic 300 in MiscValueB; the engine multiplies each tick by the stack count). Holding the beam '
          'for 4 s costs about 20% of a non-tank\'s health, so blockers trade off. Not dispellable, lands through '
          'immunities; dropped on a logout or a map change, removed with the fight. The look is 206483.',
    raw_overrides=kit_raw('Burned by the Medallion\'s light.', 'Taking Holy damage every second for each stack.',
                          CastingTimeIndex=1, CumulativeAura=_SEARING_MAX, EffectMiscValueB_1=_SEARING_TICK[1],
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(searing_faith_206482, 'spell_dungeon_refflat_periodic')

searing_look_206483 = spell(
    id=206483, name='Searing Faith', school=School.HOLY, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_HOLY_FIRE,
    notes=f'{_MZ}, MZ4: the look each second a blocker burns, cast by Malor (triggered) on every blocker: an instant '
          'DUMMY with Holy Fire 14914\'s SV 3400 (gold hands, a gold burst and an orange plume; a one-shot kit, '
          'which is why it is re-cast every second). Does nothing else.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=SV_SEARING, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- MZ5 Unclean and MZ6 Judgment -------------------------------------------------------------------------------------

unclean_206484 = spell(
    id=206484, name='Unclean', school=School.SHADOW, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_UNCLEAN_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_TAINTED_MIND,
    notes=f'{_MZ}, MZ5: "Unclean! I can smell the plague on you!" (yell line 2): at the start of each blaze Malor puts '
          'it on one random non-tank (heroic two), cast by him (triggered), 8 s. Two seconds in the beam purify it '
          '(the AI counts them and removes the aura); if the 8 s run out, Judgment (206485) lands on the bearer. A '
          'DUMMY aura: the tell, and what the bots read (Unclean players claim the beam first). Dispel none and '
          'NO_IMMUNITIES (nothing hides or removes it); dropped on a logout or a map change, removed with the fight. '
          'Tainted Mind 16567\'s SV 339 (shadow hands, a rune ring and a chest state; unconfirmed).',
    raw_overrides=kit_raw('Unclean. Stand in the Medallion\'s light to be purified, or be judged.',
                          'Stand in the Medallion\'s light to be purified, or be judged.',
                          CastingTimeIndex=1, SpellVisualID_1=SV_UNCLEAN, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

judgment_206485 = _refflat_hit(
    206485, 'Judgment', School.HOLY, _JUDGMENT, _ICON_JUDGMENT, 'The warhammer of the Light comes down.',
    f'{_MZ}, MZ6: the Unclean player\'s hit when the 8 s run out: 40% normal / 50% heroic of the reference non-tank '
    'row on that player alone (4000 / 5000 hundredths), Holy, no Weakened (ST). Cast by Malor (triggered). '
    'Judgement of Light 20271\'s SV 5651 (holy hands and the gold judgement flash; 20267\'s SV 5560 is only the '
    'heal sparkle).',
    visual=SV_JUDGMENT,
)

# --- MZ7 Ground Smash and the stun -----------------------------------------------------------------------------------

smash_bar_206486 = cast_bar(
    206486, 'Ground Smash', _SMASH_CAST_MS, 'He raises his warhammer to smash the ground.',
    f'{_MZ}, MZ7: the 2 s windup (emote line 3, an 8 yd ring marker on him); he stands still while he casts. Not '
    'interruptible (cast_bar): the registry circle on him owns the hit (206487). No look of its own: the hit has the '
    'shockwave.',
    icon=_ICON_SMASH, school=School.NORMAL,
)

smash_hit_206487 = resolve_copy(
    206487, 'Ground Smash', School.NORMAL, 'The ground breaks under the warhammer.',
    f'{_MZ}, MZ7: the circle\'s hit: 30% of the row, in 8 yd around him, the tank too (its own row), 1 Weakened, with '
    'the Stunned rider (206488), through the registry. Copy of the resolve spell 205001 (Physical). Smash 42669\'s SV '
    '9612 (the shockwave dust ring on him; Ground Smash 12734\'s SV 2643 is only a camera shake) on every unit '
    'hit: the visible impact.',
    icon=_ICON_SMASH, visual=SV_SMASH,
)

stunned_206488 = spell(
    id=206488, name='Stunned', school=School.NORMAL, dispel=0, mechanic=_MECHANIC_STUN,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=_STUN_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, mechanic=_MECHANIC_STUN,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_SMASH,
    notes=f'{_MZ}, MZ7: the 1 s stun the Ground Smash applies as the registry\'s rider (Weakened and the stun are the '
          'penalty), cast by Malor on every unit hit. Mechanic Stun and not NO_IMMUNITIES, so a stun break or immunity '
          'is a reward. Dispel none: 1 s is not worth a cure. AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('Stunned by the smash.', 'Stunned.', CastingTimeIndex=1, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- MZ8 Aftershock (heroic) -----------------------------------------------------------------------------------------

aftershock_hit_206489 = resolve_copy(
    206489, 'Aftershock', School.NORMAL, 'The ground breaks again, farther out.',
    f'{_MZ}, MZ8 (heroic): 1.5 s after the Ground Smash lands, a ring from 8 to 14 yd around him: 30% of the row, the '
    'tank too (its own row), 1 Weakened, through the registry. Copy of the resolve spell 205001 (Physical). Smash '
    '42669\'s SV 9612 on every unit hit.',
    icon=_ICON_SMASH, visual=SV_SMASH,
)

# --- MZ9 Holy Light --------------------------------------------------------------------------------------------------

holy_light_206490 = spell(
    id=206490, name='Holy Light', school=School.HOLY, cast_time_ms=_HOLY_LIGHT_CAST_MS, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_HOLY_LIGHT,
    notes=f'{_MZ}, MZ9: the 2.5 s cast every 15 s from 20 s. Interruptible: InterruptFlags 15 (movement, pushback, '
          'interrupt, auto-attack) and PreventionType 1 (a silence stops it); the descriptor\'s interrupt list, every '
          '15 s: a reward on normal, expected on heroic. Finished (the boss AI\'s OnSpellCast) it heals him through '
          '206491 by his Faith; a kick leaves the Faith. A DUMMY effect on himself, no damage. Holy Light 635\'s SV '
          '2936.',
    raw_overrides=kit_raw('Heals the Zealot by the Faith he has gathered.', InterruptFlags=_INTERRUPT_FLAGS_STANDARD,
                          PreventionType=_PREVENTION_SILENCE, SpellVisualID_1=SV_HOLY_LIGHT),
)

holy_light_heal_206491 = _heal(
    206491, 'Holy Light', _ICON_HOLY_LIGHT, 'The Light mends the Zealot.',
    f'{_MZ}, MZ9: his heal when the cast finishes, exact from the script: 1% of his maximum health per Faith stack '
    'normal; heroic 3% plus 1% per stack (175k: 1,750 a stack; heroic 230k: 6,900 plus 2,300 a stack).',
    visual=SV_HOLY_LIGHT,
)

# --- MZ10 Miracle ----------------------------------------------------------------------------------------------------

miracle_206492 = cast_bar(
    206492, 'Miracle', _MIRACLE_CAST_MS, 'He kneels toward the medallion and begs for a miracle.',
    f'{_MZ}, MZ10: once per fight at 10% health, the 3 s cast (yell line 4): he kneels toward the strongbox. Not '
    'interruptible (cast_bar). Finished (OnSpellCast) it heals him through 206493 by his Faith. Lay on Hands 10310\'s '
    'SV 132 (holy hands and a light).',
    icon=_ICON_LAY_ON_HANDS, visual=SV_MIRACLE, school=School.HOLY,
)

miracle_heal_206493 = _heal(
    206493, 'Miracle', _ICON_LAY_ON_HANDS, 'The Light answers the Zealot.',
    f'{_MZ}, MZ10: his heal when the Miracle finishes, exact from the script: 8% of his maximum health per Faith stack '
    '(175k: 14,000 a stack; no Faith, no heal; 10 stacks heal 80%).',
    visual=SV_MIRACLE,
)
