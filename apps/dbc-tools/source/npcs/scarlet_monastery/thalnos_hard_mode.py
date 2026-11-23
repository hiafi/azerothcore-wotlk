"""
Scarlet Monastery build WP-D4H: Bloodmage Thalnos's hard mode, the Desecration (heroic only)
(.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.7, s3.5 row D4H, s7 #18 A; build spec
docs/dungeons/scarlet-monastery-1-graveyard.md "Hard mode" and "Build spec": TH7, TH8, RH1-RH6, the Desecration).
WP-D4H owns this file (its spells: kSpellsDesecration 212480-212539 of modules/mod-dungeon-bosses
src/ScarletMonastery/ScarletMonasteryRework.h only; ThalnosHardModeLogic.h names the same ids). The C++ is
thalnos_hard_mode.cpp, on D4's hooks (ThalnosFight.h). The gravestones and the rite (GOs 301310-301314), their
gossip texts, their spawns, Thalnos's line 4, the risen's emotes and the Anguished Dead moved off the rite are
data/sql/updates/pending_db_world/rev_thalnos_hard_mode_scarlet_monastery.sql (rows dbc-tools cannot declare).

- 300903 High Commander Galvar Pureblood, 300904 Inquisitor Fairbell, 300905 Benedictus Voss, 300906 High Commander
  Goodchilde: the risen heroes, Thalnos's summons on the lawn (npc_sm_risen_hero; the hard mode drives their
  abilities). Undead (type 6) of Thalnos's faction 21, level 60 elites, 20k (HealthModifier on the level 60 base; their
  heroic copies 310461-310464 are WP-H's, 20k too), the spectre displays (V's 90800-90803, alpha 128), no loot, no XP,
  no immunity set (players' crowd control works on them). Galvar and Goodchilde warriors, Fairbell and Voss paladins
  (mana: the build spec's "mana for his casts"; their casts cost none). Normal threat: the tank picks them up.
- 300907 the Rallying Banner (RH1): untargetable scenery for 30 s (BattleStandard_Alliance 14541), Thalnos's summon;
  the 25% is the script's (the Rallied buff). No heroic template (WP-H's list).

Spells (kSpellsDesecration; looks from ._visuals, V's TH_* / RH_* picks, every look unconfirmed until seen in game; the
WRONG picks of the build spec are never wired: Summon Spirits SV 8116, Blood Link SV 15256, Battle Standard SV 6801,
Whirlwind 8989's SV 6664). Hits are percents of the reference row (heroic: the tank row on the tank) through the
registry (resolve copies):

  212480  The Desecration      Thalnos's red aura while the flag is lit (SV 90554)
  212481  No Rest for the Angry Dead   TH7 the 3 s teleport bar (Arcane, not interruptible; Mass Teleport's SV 7934)
  212482  Blood Pact           TH8 his buff, one stack per living risen (20% less damage taken each, the script's)
  212483  Blood Pact           TH8 a risen's tether into him (a channel that allows actions; Blood Siphon's SV 7270)
  212484  Rise                 a risen's rising look (Raise Dead's SV 4582)
  212485  Disturbed            a touched stone's faint glow (a stalker's aura: the shipped holy zone, 4 yd)
  212486  Blood of the Fallen  the answered stones' and the rite's red glow (a stalker's aura, SV 90554)
  212487  Disturb the Grave    the player's 2 s use on a stone (DUMMY on the object)
  212488  Rallied              RH1 the banner's buff on Thalnos and the risen within 10 yd (25% more damage)
  212489  Crusader's Charge    RH2 Galvar's charge look (Charge's SV 867)
  212490  Crusader's Charge    RH2 the landing's hit: 30% and Weakened (resolve copy, Physical)
  212491  Repent               RH3 Fairbell's 2 s Holy cast, a 2 s incapacitate (kickable; Repentance's SV 5539)
  212492  Greater Heal         RH4 Voss's 3 s Holy cast, 10% of the ally's health (kickable; SV 57)
  212493  Power Word: Shield   RH5 Voss's 5k absorb, 20 s, Magic (a purge reward; SV 784)
  212494  Whirlwind            RH6 Goodchilde's 2 s wind-up bar (Physical, not interruptible)
  212495  Whirlwind            RH6 the 4 s spin's look on him (Whirlwind 26083's SV 7428)
  212496  Whirlwind            RH6 a spin tick's hit: 30% and Weakened (resolve copy, Physical)
  212497-212539 spare.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR1_NO_THREAT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    cast_bar,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    FACTION_UNDEAD,
    KIT_CREATURE,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_RALLYING_BANNER,
    DISPLAY_RISEN_FAIRBELL,
    DISPLAY_RISEN_GALVAR,
    DISPLAY_RISEN_GOODCHILDE,
    DISPLAY_RISEN_VOSS,
    RH_CHARGE,
    RH_GREATER_HEAL,
    RH_PWS,
    RH_REPENT,
    RH_WHIRLWIND,
    TH_BLOOD_PACT_TETHER,
    TH_HARD_MODE_AURA,
    TH_RAISE,
    TH_STONE_ANSWERED,
    TH_STONE_STIR,
    TH_TELEPORT,
)

_D4H = 'Scarlet Monastery build WP-D4H (the Desecration)'

# --- the creatures ---------------------------------------------------------------------------------------------------

GALVAR = 300903
FAIRBELL = 300904
VOSS = 300905
GOODCHILDE = 300906
RALLYING_BANNER = 300907

# The risen's heroic entries (difficulty_entry_1 = their ids in source/world/heroic_ids.lock, minted by WP-H's write
# run in entry order: the STAGE-H report's table). generate.py --check prints the number a full row must carry until
# every lower kit unit is declared (the STAGE-H note).
RISEN_HEROIC = {GALVAR: 310461, FAIRBELL: 310462, VOSS: 310463, GOODCHILDE: 310464}

# Section 3.6: 20k each (the normal row too: the units only ever stand on heroic; WP-H's heroic copies say 20k).
# creature_classlevelstats level 60 basehp0 (live 2026-11-20): warrior 3,052, paladin 2,442.
RISEN_HEALTH = 20000
_BASE_HP_60 = {1: 3052, 2: 2442}
_CLASS_WARRIOR = 1
_CLASS_PALADIN = 2
_RANK_ELITE = 1
_CREATURE_TYPE_UNDEAD = 6
_FLAGS_EXTRA_NO_XP = 0x40
# The risen's melee: the level 60 elite base, a starting point (WP-H's heroic copies carry the tier's add melee; the
# report asks for a number sized against the tank row, rule 19).
RISEN_DAMAGE_MODIFIER = 1.0


def _risen(entry: int, name: str, subname: str, unit_class: int, display: int) -> dict:
    """A risen hero: level 60 elite undead of Thalnos's faction, the spectre display, the hard mode's AI."""
    row = creature_template(entry, name, **{
        **KIT_CREATURE, 'subname': subname, 'faction': FACTION_UNDEAD, 'type': _CREATURE_TYPE_UNDEAD,
        'minlevel': 60, 'maxlevel': 60, 'rank': _RANK_ELITE, 'unit_class': unit_class, 'unit_flags': 0,
        'HealthModifier': round(RISEN_HEALTH / _BASE_HP_60[unit_class], 4), 'ManaModifier': 1.0,
        'DamageModifier': RISEN_DAMAGE_MODIFIER, 'BaseAttackTime': 2000, 'speed_run': 1.14286,
        'detection_range': 20.0, 'CreatureImmunitiesId': 0, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0,
        'mingold': 0, 'maxgold': 0, 'ExperienceModifier': 0.0, 'flags_extra': _FLAGS_EXTRA_NO_XP,
        'difficulty_entry_1': RISEN_HEROIC[entry], 'ScriptName': 'npc_sm_risen_hero', 'AIName': '',
    })
    creature_model(entry, display_id=display)
    return row


galvar_300903 = _risen(GALVAR, 'High Commander Galvar Pureblood', 'Risen Hero of the Crusade', _CLASS_WARRIOR,
                       DISPLAY_RISEN_GALVAR)
fairbell_300904 = _risen(FAIRBELL, 'Inquisitor Fairbell', 'Risen Hero of the Crusade', _CLASS_PALADIN,
                         DISPLAY_RISEN_FAIRBELL)
voss_300905 = _risen(VOSS, 'Benedictus Voss', 'Risen Hero of the Crusade', _CLASS_PALADIN, DISPLAY_RISEN_VOSS)
goodchilde_300906 = _risen(GOODCHILDE, 'High Commander Goodchilde', 'Risen Hero of the Crusade', _CLASS_WARRIOR,
                           DISPLAY_RISEN_GOODCHILDE)

# The banner: scenery (not selectable, not attackable, no melee, no XP) of Thalnos's faction, a level 60 helper.
rallying_banner_300907 = creature_template(RALLYING_BANNER, 'Rallying Banner', **{
    **KIT_HELPER, 'faction': FACTION_UNDEAD, 'type': _CREATURE_TYPE_UNDEAD, 'minlevel': 60, 'maxlevel': 60,
    'rank': 0, 'unit_class': _CLASS_WARRIOR, 'ScriptName': '', 'AIName': '',
})
creature_model(RALLYING_BANNER, display_id=DISPLAY_RALLYING_BANNER)

# --- constants (ThalnosHardModeLogic.h; lib/test_scarlet_monastery_thalnos_hard_mode.py pins each) -------------------

NO_REST_CAST_MS = 3000          # kNoRestCastMs
DISTURB_CAST_MS = 2000          # kDisturbCastMs
DISTURB_RANGE_YD = 10.0         # the use's reach (kDisturbRangeYd 5 plus the object's own size)
RALLIED_MS = 1500               # kRalliedMs (refreshed every 0.5 s while within 10 yd of a banner)
BANNER_BOOST_PCT = 25           # kBannerBoostPct
REPENT_CAST_MS = 2000           # kRepentCastMs
REPENT_MS = 2000                # kRepentMs
HEAL_CAST_MS = 3000             # kHealCastMs
SHIELD_ABSORB = 5000            # kShieldAbsorb (designer gap 9: a starting guess)
SHIELD_MS = 20000               # kShieldMs
WHIRLWIND_WINDUP_MS = 2000      # kWhirlwindWindupMs
WHIRLWIND_SPIN_MS = 4000        # kWhirlwindSpinMs
PACT_STACKS = 4                 # kPactCapPct / kPactPctPerRisen

_LOOK_ONLY = 'Look only.'
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000     # AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map
_ATTR1_IS_CHANNELED = 0x00000004
_ATTR5_ALLOW_ACTION_DURING_CHANNEL = 0x00000001
_INTERRUPT_KICK = 0x4                       # SPELL_INTERRUPT_FLAG_INTERRUPT only: a kick, never his own movement
_PREVENTION_SILENCE = 1
_DEFENSE_MAGIC = 1
_DISPEL_MAGIC = 1
_MECHANIC_KNOCKOUT = 14                     # incapacitate (Repentance)
_MECHANIC_SHIELD = 19
_SCHOOL_MASK_ALL = 127
_TARGET_GAMEOBJECT_TARGET = 23
_TARGET_UNIT_TARGET_ALLY = 21

# Stock icons (Spell.dbc SpellIconID of the named spell)
_ICON_DEATH_KNIGHT_BLOOD = 2636     # Blood Presence 48266 (the red aura)
_ICON_MASS_TELEPORT = 1873          # Mass Teleport 16807
_ICON_BLOOD_LINK = 3224             # Blood Link 72202
_ICON_RAISE_DEAD = 221              # Raise Dead 17473
_ICON_GRAVE = 1                     # generic
_ICON_BATTLE_STANDARD = 1569        # Battle Standard 23034
_ICON_CHARGE = 457                  # Charge 11578
_ICON_REPENTANCE = 1764             # Repentance 20066
_ICON_GREATER_HEAL = 1946           # Greater Heal 10963
_ICON_PWS = 566                     # Power Word: Shield 600
_ICON_WHIRLWIND = 83                # Whirlwind 1680


def _state(spell_id: int, name: str, visual: int, desc: str, aura_desc: str, notes: str, *, icon: int,
           duration_ms: int = -1, school: School = School.NORMAL, stacks: int = 0, attributes: int = 0):
    """A DUMMY aura a unit casts on itself (triggered): a lasting look or a count. Not dispellable."""
    raw = kit_raw(desc, aura_desc, CastingTimeIndex=1, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG)
    if visual:
        raw['SpellVisualID_1'] = visual
    if stacks:
        raw['CumulativeAura'] = stacks
    return spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES | attributes,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


# --- the Desecration (the trigger) -----------------------------------------------------------------------------------

hard_mode_aura_212480 = _state(
    212480, 'The Desecration', TH_HARD_MODE_AURA, 'The dead of the Crusade answer the Bloodmage.',
    'The Desecration. The dead of the Crusade will rise for him.',
    f'{_D4H}: Thalnos\'s red aura while DATA_HARD_MODE_THALNOS is lit on heroic, cast by him on himself (triggered) by '
    'the idle hook (after the right answer, a wipe, a cold load) and at a hard mode pull; removed when the flag is '
    'not lit. The hard mode red aura SV 90554 (V TH_HARD_MODE_AURA: `deathknight_plaguestrikestatered` as a STATE). '
    'No effect.',
    icon=_ICON_DEATH_KNIGHT_BLOOD, school=School.SHADOW,
)

stone_stir_212485 = _state(
    212485, 'Disturbed', TH_STONE_STIR, 'A grave stirs.', 'Disturbed.',
    f'{_D4H}, the Desecration: a touched stone\'s faint glow, the aura of the shared stalker 300922 standing on the '
    'stone (go_sm_desecration_stone summons it), while the attempt counts touches; gone at the judge (a right answer '
    'turns it red, a wrong one dark). No right or wrong signal (the build spec). The shipped holy zone, 4 yd (V '
    'TH_STONE_STIR). No effect.',
    icon=_ICON_GRAVE, school=School.SHADOW, attributes=ATTR0_DO_NOT_DISPLAY,
)

stone_blood_212486 = _state(
    212486, 'Blood of the Fallen', TH_STONE_ANSWERED, 'The grave bleeds.', 'The grave bleeds.',
    f'{_D4H}, the Desecration: the four answered stones bleed and glow red for the rest of the lockout, and the blood '
    'rite on the court\'s wall glows red on heroic: the aura of a shared stalker 300922 on the object (its script '
    'summons it). The hard mode red aura SV 90554 (V TH_STONE_ANSWERED, TH_RITE_BLOOD). No effect.',
    icon=_ICON_GRAVE, school=School.SHADOW, attributes=ATTR0_DO_NOT_DISPLAY,
)

disturb_the_grave_212487 = spell(
    id=212487, name='Disturb the Grave', school=School.SHADOW, dispel=0, mechanic=0, attributes=0,
    cast_time_ms=DISTURB_CAST_MS, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=DISTURB_RANGE_YD, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, base_points=0, die_sides=0,
                    implicit_target_a=_TARGET_GAMEOBJECT_TARGET)],
    spell_icon_id=_ICON_GRAVE,
    notes=f'{_D4H}, the Desecration: the 2 s use of a gravestone, cast by the player (not triggered: the bar shows, '
          'moving or a hit breaks it) on the stone after the gossip option "Disturb the Grave.". No handler: the '
          'stone\'s GameObjectAI::SpellHit counts the touch (the instance keeps the order and judges the fourth). '
          'Heroic only (the stones\' spawn mask), out of combat, the council dead (section 7 #18 A).',
    raw_overrides=kit_raw('Disturb the grave of a fallen hero of the Crusade.',
                          InterruptFlags=15, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- TH7 No Rest for the Angry Dead ----------------------------------------------------------------------------------

no_rest_212481 = cast_bar(
    212481, 'No Rest for the Angry Dead', NO_REST_CAST_MS, 'Tears the living out of the crypt into the yard above.',
    f'{_D4H}, TH7: at 75% on a hard mode pull, line 1 ("No rest... for the angry dead!") and this 3 s bar; at its end '
    '(the script\'s clock) every fight player within 60 yd of him and Thalnos land on the lawn disc (1798.5, 1348.5) '
    'and the risen rise. Arcane: his kickable bars are Shadow and Physical, so a kick\'s lockout never blocks it (rule '
    '5); not interruptible (a scripted transition). Mass Teleport 16807\'s SV 7934 (V TH_TELEPORT).',
    icon=_ICON_MASS_TELEPORT, visual=TH_TELEPORT, school=School.ARCANE,
)

# --- TH8 Blood Pact --------------------------------------------------------------------------------------------------

blood_pact_212482 = _state(
    212482, 'Blood Pact', 0, 'The blood of the risen binds the Bloodmage.',
    'Blood Pact. Takes 20% less damage for each risen hero of the Crusade that lives.',
    f'{_D4H}, TH8: Thalnos\'s buff, one stack per living risen (the kit\'s WardOfTheLiving holds the count, up to 4: '
    'CumulativeAura 4). The reduction itself is the script\'s (WardOfTheLiving::Mitigate in his DamageTaken: 20% a '
    'stack, 80% with all four); the aura is the players\' read. Not dispellable (a purge must not lift the pact; the '
    'ward puts it back anyway). The tethers (212483) are the look.',
    icon=_ICON_BLOOD_LINK, school=School.SHADOW, stacks=PACT_STACKS,
)

pact_tether_212483 = spell(
    id=212483, name='Blood Pact', school=School.SHADOW, dispel=0, mechanic=0, attributes=0, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=600000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_BLOOD_LINK,
    notes=f'{_D4H}, TH8: each living risen channels a red tether into Thalnos (triggered, the script re-casts it '
          'every 1 s when it is missing and the risen is not casting). IS_CHANNELED with '
          'ALLOW_ACTION_DURING_CHANNEL (the risen chases, swings and casts through it), no interrupt flags (a kick '
          'cannot end it; the bots\' interrupt list names it priority 0), 100 yd, 10 min. Blood Siphon 24322\'s SV '
          '7270 (V TH_BLOOD_PACT_TETHER: a Beam_RedDrops channel; NEVER Blood Link\'s SV 15256, a missile). No '
          'effect.',
    raw_overrides=kit_raw('The blood binds the risen to the Bloodmage.', 'Bound by blood.', CastingTimeIndex=1,
                          InterruptFlags=0, AuraInterruptFlags=0, ChannelInterruptFlags=0,
                          AttributesEx=_ATTR1_IS_CHANNELED | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AttributesEx5=_ATTR5_ALLOW_ACTION_DURING_CHANNEL,
                          SpellVisualID_1=TH_BLOOD_PACT_TETHER),
)

rise_212484 = self_visual(
    212484, 'Rise', TH_RAISE,
    f'{_D4H}, the fallen of the Crusade: a risen hero\'s look as it rises at its own stone, cast by the risen on '
    'itself (triggered). Raise Dead 17473\'s SV 4582 (V TH_RAISE; NEVER Summon Spirits\' SV 8116, two hand glows). '
    + _LOOK_ONLY,
    icon=_ICON_RAISE_DEAD, school=School.SHADOW,
)

# --- RH1 Rallying Banner ---------------------------------------------------------------------------------------------

rallied_212488 = spell(
    id=212488, name='Rallied', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=RALLIED_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=BANNER_BOOST_PCT, die_sides=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_BATTLE_STANDARD,
    notes=f'{_D4H}, RH1 Rallying Banner: Thalnos and the risen within 10 yd of a standing banner wear it (the hard '
          'mode adds it every 0.5 s while they are inside; 1.5 s, so it drops soon after they leave). The 25% is the '
          'module\'s: a damage hook boosts a Rallied creature\'s melee and spells on players by 25%, and the risen\'s '
          'own registry hits are boosted at their registration (never twice). A DUMMY (25 in the value for the '
          'tooltip only). No look of its own: the banner (300907, BattleStandard_Alliance) is the tell (Battle '
          'Standard 23034\'s SV 6801 is on V\'s WRONG list).',
    raw_overrides=kit_raw('Rallied by the banner of the Crusade.', 'Rallied. Deals 25% more damage.',
                          CastingTimeIndex=1, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- RH2 Crusader's Charge -------------------------------------------------------------------------------------------

charge_look_212489 = self_visual(
    212489, "Crusader's Charge", RH_CHARGE,
    f'{_D4H}, RH2: Galvar\'s look as he starts his run at the marked spot (triggered on himself; the run is a '
    'MoveCharge at 42 yd/s timed to land as the 2 s marker resolves). Charge 11578\'s SV 867 (V RH_CHARGE). '
    + _LOOK_ONLY,
    icon=_ICON_CHARGE,
)

charge_hit_212490 = resolve_copy(
    212490, "Crusader's Charge", School.NORMAL, 'Trampled by a risen commander of the Crusade.',
    f'{_D4H}, RH2: the landing\'s hit, a 5 yd circle at the farthest lawn player\'s spot marked 2 s ahead, every 15 s '
    'from 8 s after Galvar rises: 30% (heroic row; 37.5% while he is Rallied) and Weakened to everyone inside, the '
    'tank included (registry tag 12). Each player hit is a Blood Ritual stack. Copy of the resolve spell 205000 '
    '(Physical).',
    icon=_ICON_CHARGE,
)

# --- RH3 Repent ------------------------------------------------------------------------------------------------------

repent_212491 = spell(
    id=212491, name='Repent', school=School.HOLY, dispel=_DISPEL_MAGIC, mechanic=_MECHANIC_KNOCKOUT,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=REPENT_CAST_MS, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=40.0, duration_ms=REPENT_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, base_points=0, die_sides=0,
                    mechanic=_MECHANIC_KNOCKOUT, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_REPENTANCE,
    notes=f'{_D4H}, RH3: Fairbell\'s 2 s Holy cast on a random lawn player (the tank included), every 12 s from 6 s '
          'after she rises: a 2 s incapacitate (MOD_STUN, mechanic knockout; Magic). Kickable (InterruptFlags 4, '
          'PreventionType 1; the interrupt list, priority 1, a reward). A hit is a Blood Ritual stack (the risen\'s '
          'AI forwards SpellHitTarget). Inside the 2 s loss-of-control rule. Repentance 20066\'s SV 5539 (V '
          'RH_REPENT). Dropped on a map change.',
    raw_overrides=kit_raw('Forces an enemy to repent, incapacitating them for $d.', 'Incapacitated.',
                          InterruptFlags=_INTERRUPT_KICK, PreventionType=_PREVENTION_SILENCE,
                          DefenseType=_DEFENSE_MAGIC, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP, SpellVisualID_1=RH_REPENT),
)

# --- RH4 Greater Heal / RH5 Power Word: Shield -----------------------------------------------------------------------

greater_heal_212492 = spell(
    id=212492, name='Greater Heal', school=School.HOLY, dispel=0, mechanic=0, attributes=0,
    cast_time_ms=HEAL_CAST_MS, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=40.0,
    duration_ms=0,
    effects=[Effect(type=EffectType.HEAL, base_points=1, die_sides=0, implicit_target_a=_TARGET_UNIT_TARGET_ALLY,
                    potency_excluded='Scarlet Monastery D4H: 10% of the ally\'s maximum health, set by the script '
                                     'at the cast (CastSpellExtraArgs BP0, ThalnosHardModeLogic.h HealAmount)')],
    spell_icon_id=_ICON_GREATER_HEAL,
    notes=f'{_D4H}, RH4: Voss\'s 3 s Holy cast on the most wounded ally within 40 yd (Thalnos included, his first on a '
          'tie), every 12 s from 4 s after he rises: 10% of its maximum health (the script sets the value: 36k on a '
          'hard mode Thalnos, 2k on a risen). Ignores caster modifiers. Kickable (InterruptFlags 4, PreventionType '
          '1; the interrupt list, priority 3: expected, a missed heal on Thalnos is a lasting setback). Greater Heal '
          '10963\'s SV 57 (V RH_GREATER_HEAL).',
    raw_overrides=kit_raw('Heals an ally of the Crusade for 10% of its health.',
                          InterruptFlags=_INTERRUPT_KICK, PreventionType=_PREVENTION_SILENCE,
                          DefenseType=_DEFENSE_MAGIC, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, SpellVisualID_1=RH_GREATER_HEAL),
)

power_word_shield_212493 = spell(
    id=212493, name='Power Word: Shield', school=School.HOLY, dispel=_DISPEL_MAGIC, mechanic=_MECHANIC_SHIELD,
    attributes=0, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=40.0, duration_ms=SHIELD_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.SCHOOL_ABSORB, base_points=SHIELD_ABSORB,
                    die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=_TARGET_UNIT_TARGET_ALLY,
                    potency_excluded='Scarlet Monastery D4H: a flat 5k boss-kit absorb (heroic only; designer gap '
                                     '9), never scaled')],
    spell_icon_id=_ICON_PWS,
    notes=f'{_D4H}, RH5: Voss\'s instant shield (triggered) on the most wounded ally without one within 40 yd, every '
          '20 s from 10 s after he rises: absorbs 5,000 damage of any school for 20 s (designer gap 9: "starting '
          'guess 5k, about 1.3 s of hard mode group damage"). Magic: a purge or an offensive dispel (the purge list, '
          'priority 1, a reward). Power Word: Shield 600\'s SV 784 (V RH_PWS: HolyDivineShield_State, lasting).',
    raw_overrides=kit_raw('Shields an ally of the Crusade, absorbing $s1 damage.', 'Absorbs $s1 damage.',
                          CastingTimeIndex=1, DefenseType=_DEFENSE_MAGIC, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=RH_PWS),
)

# --- RH6 Whirlwind ---------------------------------------------------------------------------------------------------

whirlwind_windup_212494 = cast_bar(
    212494, 'Whirlwind', WHIRLWIND_WINDUP_MS, 'Winds up a spin of steel.',
    f'{_D4H}, RH6: Goodchilde\'s 2 s wind-up (emote line 0, "%s begins to spin!"), rooted in place, every 20 s from 6 '
    's after he rises; the registry\'s 8 yd zone round him shows from its start. Physical, not interruptible: a '
    'telegraph, not a kick target (he has no kickable cast, so no lockout can touch it).',
    icon=_ICON_WHIRLWIND, school=School.NORMAL,
)

whirlwind_212495 = _state(
    212495, 'Whirlwind', RH_WHIRLWIND, 'Spinning.', 'Spinning.',
    f'{_D4H}, RH6: the 4 s spin\'s look on Goodchilde (triggered on himself as the wind-up ends; he stays rooted until '
    'it ends). Whirlwind 26083\'s SV 7428 (V RH_WHIRLWIND: Cyclone_State x0.75; NEVER Whirlwind 8989\'s SV 6664, a '
    'dust cloud). No effect: the registry deals the ticks (212496).',
    icon=_ICON_WHIRLWIND, duration_ms=WHIRLWIND_SPIN_MS,
)

whirlwind_hit_212496 = resolve_copy(
    212496, 'Whirlwind', School.NORMAL, 'Cut by a spinning blade.',
    f'{_D4H}, RH6: a spin tick, an 8 yd persistent zone round Goodchilde\'s spot, one tick a second for the 4 s spin: '
    '30% (heroic row; 37.5% while he is Rallied) and Weakened, the tank included (registry tag 16): staying for the '
    'whole spin (120%) is lethal by design (hub ruling 54). Each player hit is one Blood Ritual stack for the spin. '
    'Copy of the resolve spell 205000 (Physical).',
    icon=_ICON_WHIRLWIND,
)
