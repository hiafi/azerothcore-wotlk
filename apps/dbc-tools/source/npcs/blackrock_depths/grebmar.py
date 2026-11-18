"""
Blackrock Depths build WP-D3: Houndmaster Grebmar (9319) and his Kennel Hounds (300781)
(.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D3; build spec
docs/dungeons/blackrock-depths-1-detention-block.md S1 "Houndmaster Grebmar", GR1-GR8). WP-D3 owns this file (its
spells: kSpellsGrebmar 210780-210809 of modules/mod-dungeon-bosses src/BlackrockDepths/BlackrockDepthsRework.h;
GrebmarLogic.h names the same ids; the texts and the Bloodhound spawn deletes are the core SQL rev
rev_grebmar_blackrock_depths.sql).

- 9319 Houndmaster Grebmar: bound to boss_houndmaster_grebmar_rework (SmartAI off: WP-S0's rev drops his three stock
  rows; Demoralizing Shout retired), normal 95k (HealthModifier 40.067 on the level 52 warrior class base 2,371),
  stun immune (1972: silence and kicks work, the whistle is a kick), INSTANCE_BIND, DamageModifier the stock 3.5. His
  loot is kept. Heroic 150k and the tier's melee are WP-H's (source/world/dungeons/blackrock_depths.py).
- 300781 Kennel Hound: the boss-kit add (S1 "The Pack"), its own entry on the stock Bloodhound's DarkHound display
  (CDI 8180), a demon like the stock Bloodhound 8921 (type 3: Soothe Animal does not work, Tranquilizing Shot does),
  level 52, rank 0, 5,000 health (HealthModifier 2.108814 on 2,371), no stun immunity (an AoE stun stops Lick Wounds),
  DamageModifier 1.5 (this WP's default: about 90 a 2 s swing on a level 52 tank, 3% of the reference tank row; the
  stock Bloodhound's 3.5 at four hounds on the tank is too much), no loot, no XP (the horn brings more for ever).
  Summoned only (npc_brd_kennel_hound): four at his feet, two / three a horn. Heroic 9k: `difficulty_entry_1` 310392
  (WP-H's predicted lock line).

Spells (looks from ._visuals, WP-V-1's GR_* picks; every look unconfirmed until seen in game):

  210780  Sic 'em!           GR2 the whistle: 2 s, interruptible (kick, silence), Physical
  210781  Fetch!             GR2 the whistle: 2 s, interruptible, Nature
  210782  Heel!              GR2 the whistle: 2 s, interruptible, Arcane. Three schools: a kick locks the kicked
                             command's school only, so the heroic double's second whistle (always another command,
                             2.5 s later) is never refused by the first one's lockout
  210783  Sic 'em            GR3 the mark on the player during the whistle and the leap (3.5 s), the purple rune ring
                             under them (SV 90657, V-1's runner alternate; the spec names no look for the mark)
  210784  Sic 'em            GR3 the landing circle's hit: 5 yd, 30% / 45% + Weakened (resolve copy, Physical)
  210785  Leap               GR4 a leap line's hit: 3 yd from a hound to the spot, 15% / 25% + Weakened, heroic + the
                             hounds' Rend (rider 210795) (resolve copy, Physical)
  210786  Leap               look: Leap 47482's charge trail and dust (SV 29), a hound taking off
  210787  Snatched           GR5 -30% damage and healing done, 30 s (refreshed to 30 s when the runner escapes,
                             removed when it dies in time); Snatch 50541's red hands (SV 398)
  210788  Fetch!             GR5 the runner's mark: the orange rune ring under it (SV 90613) and the kill order's key
  210789  Lick Wounds        GR6 the hound's 5 s self channel: 5% of its health a second, +30% damage taken; a kick,
                             a silence, a stun or a knockback stops it; Mend Pet 136's green glow (SV 652)
  210790  Frenzy             GR6 a finished lick: +30% attack speed, 15 s, an Enrage (Tranquilizing Shot), not
                             stacking; Berserking 23505's lasting red hands (SV 6943)
  210791  Frenzy             look: Frenzy 19516's head flash (SV 5319) on the application
  210792  Kennel Horn        look: Horn of Elemental Fury 56893's sound and horn animation (SV 4079) on him
  210793  Kennel Horn        look: the shipped horn burst (SV 90602) on each hound at its kennel door
  210794  Release the Hounds look: Release the Hounds 12851's summoning bark (SV 1523), the 30% finale
  210795  Rend               the hounds' bleed (stock Rend 13445 rescaled): 1% / 1.5% of the reference row every
                             3 s for 15 s (5 ticks), Physical, bleed mechanic
  210796  Pummel             GR7 the stock Pummel 15615 rescaled: 10% / 15% of the reference row and a 5 s school
                             lockout on a player casting within 5 yd
  210797-210809 spare

Bloodlust 21049 (GR8) is the stock spell, unchanged (no damage to rescale; not a DD double-use id).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    KIT_CREATURE,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_KENNEL_HOUND,
    GR_FETCH_RUNNER_RING,
    GR_FRENZY,
    GR_FRENZY_FLASH,
    GR_KENNEL_HORN,
    GR_KENNEL_HORN_BURST,
    GR_LICK_WOUNDS,
    GR_RELEASE_THE_HOUNDS,
    GR_SIC_LEAP,
    GR_SNATCHED,
    SV_PURPLE_RING,
)

_D3 = 'Blackrock Depths build WP-D3 (Houndmaster Grebmar)'
_SCRIPT_REFFLAT = ('Blackrock Depths: a percent of reference health in hundredths, set by the kit\'s '
                   'spell_dungeon_refflat_damage / _periodic (DungeonKit::RefFlatOn)')

creature_template_columns(9319, **boss_columns(
    'boss_houndmaster_grebmar_rework', 40.067, damage_modifier=3.5,
))

# --- constants (GrebmarLogic.h; lib/test_blackrock_depths_grebmar.py pins each against the header) -------------------

WHISTLE_CAST_MS = 2000          # kWhistleCastMs
SIC_EM_MARK_MS = 3500           # kSicEmMarkMs (the whistle + the 1.5 s leap)
SNATCHED_MS = 30000             # kSnatchedMs
SNATCHED_PCT = 30               # kSnatchedPct
FETCH_RUNNER_MS = 16000         # kFetchWindowMs + 1 s (the script despawns the runner at 15 s)
LICK_MS = 5000                  # kLickMs
LICK_TICK_MS = 1000             # kLickTickMs
LICK_HEAL_PCT = 5               # kLickHealPctPerSec
LICK_TAKEN_PCT = 30             # kLickDamageTakenPct
FRENZY_MS = 15000               # kFrenzyMs
FRENZY_HASTE_PCT = 30           # kFrenzyHastePct
REND = (100, 150)               # kRendPctPerTick 1 / 1.5 (hundredths)
REND_MS = 15000                 # kRendMs
REND_TICK_MS = 3000             # kRendTickMs
PUMMEL = (1000, 1500)           # kPummelPct 10 / 15 (hundredths)
PUMMEL_LOCKOUT_MS = 5000        # kPummelLockoutMs

KENNEL_HOUND = 300781
KENNEL_HOUND_HEROIC = 310392    # WP-H's lock line (STAGE-H-REPORT s3)
KENNEL_HOUND_LEVEL = 52
KENNEL_HOUND_HEALTH_MODIFIER = 2.108814     # ceil(2,371 x 2.108814) = 5,000 (kHoundHealth normal)
KENNEL_HOUND_DAMAGE_MODIFIER = 1.5

_FLAGS_EXTRA_NO_XP = 0x40
_CREATURE_TYPE_DEMON = 3
_ATTR1_IS_SELF_CHANNELED = 0x00000040
_CHANNEL_INTERRUPT_FLAG_INTERRUPT = 0x08
_SPELL_INTERRUPT_FLAGS_KICK = 15
_PREVENTION_SILENCE = 1
_PREVENTION_PACIFY = 2
_DEFENSE_MAGIC = 1
_DEFENSE_MELEE = 2
_DISPEL_ENRAGE = 9
_MECHANIC_BLEED = 15
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_SCHOOL_MASK_ALL = 127
_AURA_OBS_MOD_HEALTH = 20                   # SPELL_AURA_OBS_MOD_HEALTH: a percent of max health a tick
_TARGET_UNIT_TARGET_ENEMY = 6

# Stock icons (Spell.dbc SpellIconID of the named spell)
_ICON_CALL_PET = 455            # Call Pet 883 (the whistles)
_ICON_LEAP = 3139               # Leap 47482
_ICON_SNATCH = 168              # Snatch 50541
_ICON_MEND_PET = 267            # Mend Pet 136
_ICON_FRENZY = 456              # Frenzy 19516
_ICON_HORN = 1550               # Horn of Elemental Fury 56893
_ICON_REND = 245                # Rend 13445
_ICON_PUMMEL = 756              # Pummel 15615
_ICON_GENERIC = 1

# --- 300781 Kennel Hound ----------------------------------------------------------------------------------------------

# The entry is written as a number: source/world/dungeons/blackrock_depths.py finds the declared kit adds by the
# pattern `creature_template(<entry>, ...)` (WP-H) and gives them their heroic health.
kennel_hound_300781 = creature_template(300781, 'Kennel Hound', **{
    **KIT_CREATURE, 'type': _CREATURE_TYPE_DEMON, 'minlevel': KENNEL_HOUND_LEVEL,
    'maxlevel': KENNEL_HOUND_LEVEL, 'rank': 0, 'unit_class': 1, 'unit_flags': 0,
    'HealthModifier': KENNEL_HOUND_HEALTH_MODIFIER, 'DamageModifier': KENNEL_HOUND_DAMAGE_MODIFIER,
    'BaseAttackTime': 2000, 'speed_run': 1.42857, 'detection_range': 18.0, 'CreatureImmunitiesId': 0,
    'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'flags_extra': _FLAGS_EXTRA_NO_XP,
    'ScriptName': 'npc_brd_kennel_hound', 'difficulty_entry_1': KENNEL_HOUND_HEROIC,
})
creature_model(KENNEL_HOUND, display_id=DISPLAY_KENNEL_HOUND)


# --- GR2 the whistles -------------------------------------------------------------------------------------------------

def _whistle(spell_id: int, name: str, school: School, command: str, notes: str):
    """A 2 s whistle naming a command: DUMMY on the caster, interruptible (InterruptFlags 15) and silence-preventable;
    a finished one gives the command (the script's OnSpellCast), a kicked one nothing."""
    return spell(
        id=spell_id, name=name, school=school, cast_time_ms=WHISTLE_CAST_MS, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_CALL_PET,
        notes=f'{_D3}, GR2: the whistle "{command}" (yell), 8 s after the pull, then every 12 s (heroic 10 s; below '
              '30% on heroic two back to back, the second 2.5 s after the first); the three commands rotate, never the '
              f'same one twice in a row. DUMMY on the caster, 2 s (GrebmarLogic.h kWhistleCastMs). {notes} '
              'Interruptible (InterruptFlags 15) and silence-preventable (PreventionType 1): his immunity set 1972 '
              'lets both work. The interrupt list names all three (priority 2 normal, a reward; 3 heroic, expected).',
        raw_overrides=kit_raw(f'Grebmar whistles: "{command}"', InterruptFlags=_SPELL_INTERRUPT_FLAGS_KICK,
                              PreventionType=_PREVENTION_SILENCE, DefenseType=_DEFENSE_MAGIC,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


whistle_sic_em_210780 = _whistle(
    210780, "Sic 'em!", School.NORMAL, "Sic 'em!",
    'Finished: the marked player\'s spot locks as the 5 yd landing (210784) and every free hound draws its 3 yd line '
    '(210785), 1.5 s. Physical: each command has its own school, so a kick locks only that command\'s whistle.',
)

whistle_fetch_210781 = _whistle(
    210781, 'Fetch!', School.NATURE, 'Fetch!',
    'Finished: a free hound snatches a random player\'s weapon (Snatched 210787) and runs for the exit (210788). '
    'Nature (its own school, see 210780).',
)

whistle_heel_210782 = _whistle(
    210782, 'Heel!', School.ARCANE, 'Heel!',
    'Finished: every hound but a runner runs back to his feet and channels Lick Wounds (210789). Arcane (its own '
    'school, see 210780).',
)

# --- GR3 / GR4 Sic 'em ------------------------------------------------------------------------------------------------

sic_em_mark_210783 = spell(
    id=210783, name="Sic 'em", school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=SIC_EM_MARK_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_LEAP,
    notes=f'{_D3}, GR3: the mark. Cast by Grebmar (triggered) on a random player, the tank included (ruling 88), as '
          'the Sic \'em whistle starts; 3.5 s (the 2 s whistle and the 1.5 s leap), removed at once when the whistle '
          'is kicked. A DUMMY debuff: the read is the purple rune ring under the player (SV 90657, V-1\'s Fetch-runner '
          'alternate; the spec names no look for the mark). Not dispellable; NO_IMMUNITIES (the hounds still come). '
          'AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw("Grebmar's hounds are coming for you. Move away from the others.",
                          "Marked: the hounds leap here.", CastingTimeIndex=1, SpellVisualID_1=SV_PURPLE_RING,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=ATTR3_ALWAYS_HIT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

sic_em_landing_210784 = resolve_copy(
    210784, "Sic 'em", School.NORMAL, 'The pack lands on its quarry.',
    f'{_D3}, GR3: the landing circle\'s hit, 5 yd at the marked player\'s spot as it was when the whistle ended, 1.5 s '
    'later: 30% (heroic 45%) of the reference row and 1 Weakened (registry tag 5, the G1 drill\'s `leap` landing). '
    'Copy of the mod-boss-mechanics resolve spell 205001 (Physical).',
    icon=_ICON_LEAP,
)

sic_em_leap_210785 = resolve_copy(
    210785, 'Leap', School.NORMAL, 'A hound tears along its line.',
    f'{_D3}, GR4: a leap line\'s hit, 3 yd wide from a hound (where it stood when the whistle ended) to the landing '
    'spot, 1.5 s: 15% (heroic 25%) of the reference row and 1 Weakened; heroic, the hounds\' Rend too (the registry\'s '
    'rider 210795). One line per free hound, so more hounds mean more lines (registry tag 4, the G1 drill\'s `leap` '
    'lines). Copy of the resolve spell 205001 (Physical).',
    icon=_ICON_LEAP,
)

leap_look_210786 = self_visual(
    210786, 'Leap', GR_SIC_LEAP,
    f'{_D3}, GR4: a hound taking off along its line (DungeonKit::JumpTo lookSpell, 0.5 s before the landing); Leap '
    '47482\'s charge trail and dust (SV 29).',
    icon=_ICON_LEAP,
)

# --- GR5 Fetch --------------------------------------------------------------------------------------------------------

snatched_210787 = spell(
    id=210787, name='Snatched', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=SNATCHED_MS,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=-SNATCHED_PCT,
               die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_TARGET_ANY,
               potency_excluded='Snatched: a flat -30% damage done, not a damage or heal value'),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_HEALING_DONE_PERCENT, base_points=-SNATCHED_PCT,
               die_sides=0, implicit_target_a=TARGET_UNIT_TARGET_ANY,
               potency_excluded='Snatched: a flat -30% healing done, not a damage or heal value'),
    ],
    spell_icon_id=_ICON_SNATCH,
    notes=f'{_D3}, GR5: a hound ran off with the player\'s weapon (the tank too, ruling 88): -30% damage and healing '
          'done, 30 s. Cast by the runner (triggered) on the player when the Fetch whistle ends. Killing the runner '
          'within 15 s removes it (the weapon comes back); a runner that gets away (15 s) despawns and Snatched runs '
          'a fresh 30 s (DungeonKit::ShortenAura). Not dispellable (it is a missing weapon), NO_IMMUNITIES, no '
          'disarm (the spec\'s numbers, not a real disarm: casters and healers lose as much as melee). Snatch '
          '50541\'s red hands (SV 398). AuraInterruptFlags CHANGE_MAP; removed when the fight ends.',
    raw_overrides=kit_raw('A hound has run off with your weapon.', 'Damage and healing done reduced by $s1%.',
                          CastingTimeIndex=1, SpellVisualID_1=GR_SNATCHED, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

fetch_runner_210788 = spell(
    id=210788, name='Fetch!', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=FETCH_RUNNER_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_SNATCH,
    notes=f'{_D3}, GR5: the runner\'s mark, cast by the hound on itself (triggered) as it snatches: the orange rune '
          'ring under it (SV 90613, V-1\'s "kill this one" read) and the key of the kill order (TargetEntry when '
          'HasAura, priority 3: the runner before the pack and the boss). 16 s: the script despawns the runner at '
          '15 s (it got away). Not purgeable.',
    raw_overrides=kit_raw('Running off with a weapon.', 'Running off with a weapon. Kill it to get the weapon back.',
                          instant=True, SpellVisualID_1=GR_FETCH_RUNNER_RING, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- GR6 Heel: Lick Wounds, Frenzy ------------------------------------------------------------------------------------

lick_wounds_210789 = spell(
    id=210789, name='Lick Wounds', school=School.NATURE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=LICK_MS,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_OBS_MOD_HEALTH, base_points=LICK_HEAL_PCT, die_sides=0,
               amplitude=LICK_TICK_MS, implicit_target_a=TARGET_UNIT_CASTER,
               potency_excluded='Lick Wounds: a percent of the hound\'s own maximum health (OBS_MOD_HEALTH), not a '
                                'scaled heal'),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=LICK_TAKEN_PCT,
               die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
               potency_excluded='Lick Wounds: a flat +30% damage taken, not a damage or heal value'),
    ],
    spell_icon_id=_ICON_MEND_PET,
    notes=f'{_D3}, GR6: Heel! Every hound but a runner runs back to his feet and channels this on itself: 5 s (a self '
          'channel, SPELL_ATTR1_IS_SELF_CHANNELED, Rattlegore\'s Salvage precedent), 5% of its maximum health a '
          'second (SPELL_AURA_OBS_MOD_HEALTH, amplitude 1 s; healing-taken reductions such as Mortal Strike cut it), '
          '+30% damage taken (every school) while it lasts. A finished channel (OnChannelFinished) gives Frenzy '
          '(210790); a kick (ChannelInterruptFlags 0x08), a silence (PreventionType 1), a stun, or a knockback or grip '
          'that moves the hound 2 yd (npc_brd_kennel_hound interrupts it) stops it: no heal left, no Frenzy. The '
          'descriptor\'s interrupt list (the stop list), priority 2 (a reward). Nature: none of Grebmar\'s whistles '
          'is cast by a hound, so a kick here locks nothing else. Mend Pet 136\'s green glow (SV 652).',
    raw_overrides=kit_raw('Licks its wounds: heals quickly, but takes more damage. Stop it.',
                          'Healing $s1% of its health every second. Damage taken increased by $s2%.',
                          CastingTimeIndex=1, AttributesEx=_ATTR1_IS_SELF_CHANNELED | ATTR1_NO_THREAT,
                          ChannelInterruptFlags=_CHANNEL_INTERRUPT_FLAG_INTERRUPT, InterruptFlags=0,
                          PreventionType=_PREVENTION_SILENCE, DefenseType=_DEFENSE_MAGIC,
                          SpellVisualID_1=GR_LICK_WOUNDS, AttributesEx4=ATTR4_NO_CAST_LOG),
)

frenzy_210790 = spell(
    id=210790, name='Frenzy', school=School.NORMAL, dispel=_DISPEL_ENRAGE, mechanic=0, attributes=0, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=FRENZY_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_MELEE_HASTE, base_points=FRENZY_HASTE_PCT,
                    die_sides=0, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Frenzy: a flat +30% attack speed, not a damage or heal value')],
    spell_icon_id=_ICON_FRENZY,
    notes=f'{_D3}, GR6: a Lick Wounds nobody stopped: +30% attack speed, 15 s, cast by the hound on itself '
          '(triggered). An Enrage (Dispel 9): Tranquilizing Shot removes it (the hounds are demons, so Soothe Animal '
          'does not), on the purge list (a reward). It does not stack (CumulativeAura 0: a second lick refreshes '
          'it). Berserking 23505\'s lasting red hands (SV 6943, V-1: Frenzy\'s SV 5319 is a one-shot flash, 210791).',
    raw_overrides=kit_raw('Frenzied.', 'Attack speed increased by $s1%.', instant=True, SpellVisualID_1=GR_FRENZY,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

frenzy_flash_210791 = self_visual(
    210791, 'Frenzy', GR_FRENZY_FLASH,
    f'{_D3}, GR6: the head flash as Frenzy lands (Frenzy 19516\'s SV 5319, a one-shot; the lasting look is 210790\'s).',
    icon=_ICON_FRENZY,
)

# --- GR1 Kennel Horn, GR8 the finale ----------------------------------------------------------------------------------

kennel_horn_210792 = self_visual(
    210792, 'Kennel Horn', GR_KENNEL_HORN,
    f'{_D3}, GR1: Grebmar blows his horn (emote line 5), 30 s after the pull and every 40 s, and once more at the 30% '
    'finale: Horn of Elemental Fury 56893\'s sound and horn animation (SV 4079; never Horn of Winter\'s icy SV 12396). '
    'Not a cast bar and not interruptible: the refill always comes.',
    icon=_ICON_HORN,
)

kennel_horn_burst_210793 = self_visual(
    210793, 'Kennel Horn', GR_KENNEL_HORN_BURST,
    f'{_D3}, GR1: the horn burst at a kennel door, cast by each new hound on itself as it comes out (the shipped SV '
    '90602: the horn cast plus the Ascension orange shock-ray burst; the hound stands in for the stalker V-1 names).',
    icon=_ICON_HORN,
)

release_the_hounds_210794 = self_visual(
    210794, 'Release the Hounds', GR_RELEASE_THE_HOUNDS,
    f'{_D3}, GR8: the 30% finale (yell 4), with the extra horn and Bloodlust 21049: Release the Hounds 12851\'s '
    'summoning bark (SV 1523).',
    icon=_ICON_GENERIC,
)

# --- the hounds' Rend, GR7 Pummel -------------------------------------------------------------------------------------

rend_210795 = spell(
    id=210795, name='Rend', school=School.NORMAL, dispel=0, mechanic=_MECHANIC_BLEED,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=REND_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=REND[0],
                    die_sides=0, amplitude=REND_TICK_MS, mechanic=_MECHANIC_BLEED,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_REND,
    notes=f'{_D3}: the hounds\' bleed, the stock Bloodhound\'s Rend 13445 (13 every 3 s) rescaled (rule 15: a copy in '
          'the slice). A hound casts it (triggered) on its victim within 5 yd every 7-11 s (the stock 8921 timer); '
          'heroic, every leap line also applies it (the registry\'s rider: Leap Rend). 1% (heroic 1.5%: '
          'EffectMiscValueB) of the reference row every 3 s for 15 s through spell_dungeon_refflat_periodic (the '
          'tank\'s row on the tank), Physical, a bleed; ignores caster modifiers. Not dispellable. Each hound\'s is '
          'its own aura (per caster). No look (the stock Rend\'s kit is not one of V-1\'s picks). Removed when the '
          'fight ends.',
    raw_overrides=kit_raw('Bleeding.', 'Bleeding for Physical damage every 3 sec.', CastingTimeIndex=1,
                          EffectMiscValueB_1=REND[1], DefenseType=_DEFENSE_MELEE, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(rend_210795, 'spell_dungeon_refflat_periodic')

pummel_210796 = spell(
    id=210796, name='Pummel', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=PUMMEL_LOCKOUT_MS,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=PUMMEL[0] - 1, die_sides=1,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT),
        Effect(type=EffectType.INTERRUPT_CAST, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_PUMMEL,
    notes=f'{_D3}, GR7: the stock Pummel 15615 (45 damage and a 5 s school lockout) rescaled (rule 15: a copy in the '
          'slice). 5-7 s after the pull, then every 12-14 s, on a player casting within 5 yd (the stock event 105; '
          'the script looks again every 0.5 s while nobody is): 10% (heroic 15%: EffectMiscValueB) of the reference '
          'row through spell_dungeon_refflat_damage (RefFlatOn), Physical, plus the interrupt (the lockout is the '
          'spell\'s 5 s duration). Always hits, cannot crit, ignores his modifiers (Bloodlust never raises it). '
          'Ranged who keep out of 5 yd are never pummeled. Pummel 15615\'s icon; its SV 1023 is not one of V-1\'s '
          'picks, so no look of its own.',
    raw_overrides=kit_raw('Pummels a spellcaster, interrupting the spell.', instant=True, InterruptFlags=0,
                          PreventionType=_PREVENTION_PACIFY, DefenseType=_DEFENSE_MELEE,
                          EffectMiscValueB_1=PUMMEL[1], AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(pummel_210796, 'spell_dungeon_refflat_damage')
