"""
Scarlet Monastery build WP-D10: Drillmaster Corin Halden, the Master-at-Arms (Halden 300942, Drill Recruit 300943)
(.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.5 row D10, s7 #30 A; build spec
docs/dungeons/scarlet-monastery-3-armory.md "Drillmaster Corin Halden, the Master-at-Arms", MA0-MA4). WP-D10 owns this
file; WP-S0 wrote the skeleton. His texts and his spawn are data/sql/updates/pending_db_world/
rev_halden_scarlet_monastery.sql.

Wave 2: the two creatures and the spells are declared now, so FD-SM's credit_creature(300942) (encounter 1079) has a
template and WP-H's heroic override (300k, heroic entry 310477) applies; only his ScriptName waits for the wave switch
(BIND_WAVE_2, flipped with kWave2Bound by W2-SETUP). While wave 2 is unbound he is a plain melee elite mid-hall
(ScriptName '': the AI is not registered, so naming it would log "not assigned" at boot) and no recruit stands with
him (the AI summons them).

- 300942 Drillmaster Corin Halden <Master-at-Arms>: a NEW boss, boss_drillmaster_corin_halden_rework
  (modules/mod-dungeon-bosses src/ScarletMonastery/boss_drillmaster_corin_halden_rework.cpp). Level 37 warrior,
  Scarlet Crusade (faction 67), elite, the build spec's normal health (60k = HealthModifier 44.910 on the level 37
  warrior base 1,336), DamageModifier 3.0 (between Crell's 2.6 and Herod's 3.8: his melee on the tank is his only hit;
  the squad is his kit), stun immunity 1972, INSTANCE_BIND (the encounter row's credit creature), display 2514 (the
  Scarlet Myrmidon: V's pick, gap 15), SmartAI off, lootid 300942 (L-2's lists). detection_range 10: five stock
  soldiers stand 11 to 18 yd from his spot in the same chamber (a Protector, three Defenders, a Myrmidon), so the
  group can pull them without him. Heroic health (300k) and the tier's melee are WP-H's overrides.
- 300943 Drill Recruit (MA0-MA4, Crell's recruits, hub ruling 34): not selectable, cannot be harmed, never fights
  (KIT_HELPER with the Scarlet faction, IMMUNE_TO_PC | IMMUNE_TO_NPC), display 2522 (the Scarlet Soldier), a spear in
  hand (the AI sets the virtual item, HaldenLogic.h kItemRecruitSpear), runs at 8 yd/s (the rank re-forms in about
  2 s). Summoned by Halden in rank; no heroic template (WP-H's no-heroic list).

Spells (kSpellsHalden 212950-212979; HaldenLogic.h names the same ids; looks from ._visuals, WP-V's MA_* picks, every
look unconfirmed until seen in game). Every hit is a percent of the reference row (the tank row on the tank) the
registry lands through a resolve copy:

  212950  Charge!           MA1 a lane's hit: resolve copy, Physical, 30% / 45% and Weakened
  212951  Charge!           MA1 the charge on a recruit (Charge 100's SV 867)
  212952  Spears, level!    MA2 a cone's hit: resolve copy, Physical, 30% / 45% and Weakened
  212953  Spears, level!    MA2 the thrust on a recruit (Thrust 62544's SV 13365)
  212954  Javelins!         MA3 his 2 s cast, interruptible (a kick and a silence)
  212955  Javelin           MA3, MA3a a javelin's hit: resolve copy, Physical, 30% / 45% and Weakened
  212956  Javelin           MA3 the javelin's flight from a recruit (Throw Javelin 62778's SV 11993, 18 yd/s)
  212957  Close Ranks!      MA4 the band's tick: resolve copy, Physical, 10% / 12% a second (no Weakened)
  212958  Close Ranks!      MA4 Shield Wall 871's SV 345 on a recruit (an impact, replayed every 2 s)
  212959-212979 spare.
"""

from lib.dsl import RANGE_SELF, Effect, EffectType, School
from lib.dsl.dungeon_kit import ATTR1_NO_THREAT, ATTR2_IGNORE_LINE_OF_SIGHT, self_visual
from lib.dsl.registry import creature_model, creature_template, spell

from ._common import (
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_2,
    FACTION_SCARLET_CRUSADE,
    IMMUNITY_BOSS_STUN,
    KIT_CREATURE,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_DRILL_RECRUIT,
    DISPLAY_HALDEN,
    MA_CHARGE,
    MA_CLOSE_RANKS,
    MA_JAVELIN,
    MA_SPEARS,
)

_D10 = 'Scarlet Monastery build WP-D10 (Drillmaster Corin Halden)'

# --- the creatures ---------------------------------------------------------------------------------------------------

# His heroic entry (difficulty_entry_1 = his id in source/world/heroic_ids.lock: WP-H's mint table, the second wave 2
# unit after Crell's 310476). generate.py --check names the interim number while a lower unit is undeclared.
HALDEN_HEROIC = 310477

HALDEN = 300942
DRILL_RECRUIT = 300943

SCRIPT_NAME = 'boss_drillmaster_corin_halden_rework'

_RANK_ELITE = 1
_CLASS_WARRIOR = 1
_FLAGS_EXTRA_NO_XP = 0x40
_UNIT_FLAG_NON_ATTACKABLE = 0x2
_UNIT_FLAG_IMMUNE_TO_PC = 0x100
_UNIT_FLAG_IMMUNE_TO_NPC = 0x200
_UNIT_FLAG_NOT_SELECTABLE = 0x02000000

# The build spec's normal health at 5 players (S0's table): 60k = 44.910 x 1,336 (the level 37 warrior).
# creature_classlevelstats basehp0, live 2026-11-20.
HALDEN_HEALTH_MODIFIER = 44.910
HALDEN_DAMAGE_MODIFIER = 3.0
HALDEN_DETECTION_RANGE = 10.0

drillmaster_corin_halden_300942 = creature_template(300942, 'Drillmaster Corin Halden', **{
    **KIT_CREATURE, 'subname': 'Master-at-Arms', 'minlevel': 37, 'maxlevel': 37, 'rank': _RANK_ELITE,
    'unit_class': _CLASS_WARRIOR, 'faction': FACTION_SCARLET_CRUSADE, 'type': 7, 'exp': 0,
    'HealthModifier': HALDEN_HEALTH_MODIFIER, 'DamageModifier': HALDEN_DAMAGE_MODIFIER, 'ManaModifier': 1.0,
    'ExperienceModifier': 2.0, 'BaseAttackTime': 2000, 'speed_run': 1.14286,
    'detection_range': HALDEN_DETECTION_RANGE, 'CreatureImmunitiesId': IMMUNITY_BOSS_STUN, 'lootid': 300942,
    'mingold': 300, 'maxgold': 900, 'flags_extra': 1, 'ScriptName': SCRIPT_NAME if BIND_WAVE_2 else '', 'AIName': '',
    'difficulty_entry_1': HALDEN_HEROIC,
})
creature_model(300942, display_id=DISPLAY_HALDEN)

drill_recruit_300943 = creature_template(300943, 'Drill Recruit', **{
    **KIT_HELPER, 'faction': FACTION_SCARLET_CRUSADE, 'minlevel': 30, 'maxlevel': 30, 'rank': 0,
    'unit_class': _CLASS_WARRIOR,
    'unit_flags': _UNIT_FLAG_NON_ATTACKABLE | _UNIT_FLAG_IMMUNE_TO_PC | _UNIT_FLAG_IMMUNE_TO_NPC
    | _UNIT_FLAG_NOT_SELECTABLE,
    'speed_walk': 1.0, 'speed_run': 1.14286, 'flags_extra': _FLAGS_EXTRA_NO_XP, 'ScriptName': '', 'AIName': '',
})
creature_model(300943, display_id=DISPLAY_DRILL_RECRUIT)

# --- constants (HaldenLogic.h; lib/test_scarlet_monastery_halden.py pins each against the header) ---------------------

JAVELINS_CAST_MS = 2000             # kJavelinCastMs
JAVELIN_SPEED = 18.0                # kJavelinSpeed: Throw Javelin 62778's Speed

_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40
_PREVENTION_SILENCE = 1
_SPELL_INTERRUPT_FLAGS_KICK = 15
_ATTR0_DO_NOT_DISPLAY = 0x00000080
_ATTR0_DO_NOT_LOG = 0x00000100

# Stock icons (Spell.dbc SpellIconID of the named spell, read from the stock client 2026-11-20)
_ICON_CHARGE = 457                      # Charge 100
_ICON_THRUST = 3808                     # Thrust 62544
_ICON_JAVELIN = 370                     # Throw Javelin 62778
_ICON_SHIELD_WALL = 281                 # Shield Wall 871

# --- MA1 Charge! ------------------------------------------------------------------------------------------------------

charge_212950 = resolve_copy(
    212950, 'Charge!', School.NORMAL, 'The recruits charge down their lanes.',
    f'{_D10}, MA1 Charge!: a lane\'s hit, one 4 yd lane per recruit from its rank spot straight ahead (35 yd, clipped '
    'at the room\'s far wall: 8 to 10 yd past him in the middle chamber, s7 #30 A), 4 yd gaps (heroic 3 yd), a 2.5 s '
    'marker: 30% (heroic 45%) of the reference row and 1 Weakened, the tank row on the tank (registry tag 1). Copy of '
    'the mod-boss-mechanics resolve spell 205001 (Physical).',
    icon=_ICON_CHARGE,
)

charge_look_212951 = self_visual(
    212951, 'Charge!', MA_CHARGE,
    f'{_D10}, MA1: the charge, cast by a recruit on itself (triggered) as it runs down its lane: Charge 100\'s '
    'SpellVisual 867. The lane\'s marker is the registry\'s. Look only.',
    icon=_ICON_CHARGE,
)

# --- MA2 Spears, level! -----------------------------------------------------------------------------------------------

spears_212952 = resolve_copy(
    212952, 'Spears, level!', School.NORMAL, 'The recruits thrust their spears.',
    f'{_D10}, MA2 Spears, level!: a cone\'s hit, a 60 degree cone 10 yd ahead of each recruit (from the rank 8 yd '
    'behind him: a band over his back and flanks to 2 yd past him), a 2.5 s marker: 30% (heroic 45%) of the reference '
    'row and 1 Weakened, the tank row on the tank (registry tag 2). Copy of the resolve spell 205001 (Physical).',
    icon=_ICON_THRUST,
)

spears_look_212953 = self_visual(
    212953, 'Spears, level!', MA_SPEARS,
    f'{_D10}, MA2: the thrust, cast by a recruit on itself (triggered) as the cones land (heroic also as the ring '
    'passes): Thrust 62544\'s SpellVisual 13365 (the spear-thrust animation; the recruits carry a polearm). Look only.',
    icon=_ICON_THRUST,
)

# --- MA3 Javelins! ----------------------------------------------------------------------------------------------------

javelins_212954 = spell(
    id=212954, name='Javelins!', school=School.NORMAL, dispel=0, mechanic=0, attributes=0,
    cast_time_ms=JAVELINS_CAST_MS, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_JAVELIN,
    notes=f'{_D10}, MA3 Javelins!: his 2 s cast at the command\'s yell (normal a reward interrupt, heroic expected). '
          'NOT triggered, so the bar shows and a kick stops it: InterruptFlags 15 and PreventionType 1 (a silence); '
          'his immunity set 1972 holds no INTERRUPT or SILENCE. No effect of its own: the script reads the outcome '
          '(OnSpellFailed: kicked, normal no volley and the fumble emote, heroic one volley; OnSpellCast: the volley, '
          'heroic and the second volley). On the bots\' interrupt list (priority 2 normal, 3 heroic).',
    raw_overrides=kit_raw('The drillmaster raises his arm. Interrupt him or the recruits throw.',
                          InterruptFlags=_SPELL_INTERRUPT_FLAGS_KICK, PreventionType=_PREVENTION_SILENCE,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

javelin_212955 = resolve_copy(
    212955, 'Javelin', School.NORMAL, 'A javelin lands.',
    f'{_D10}, MA3 Javelins! and MA3a the second volley: a javelin\'s hit, a 5 yd circle fixed at the throw at a '
    'player\'s spot (heroic a random spot within 5 yd of the player), one per recruit at a different player (heroic '
    'two more at random players), a 2.5 s flight (the second volley 1.5 s): 30% (heroic 45%) of the reference row and '
    '1 Weakened, the tank row on the tank (registry tags 3 and 31). Copy of the resolve spell 205001 (Physical).',
    icon=_ICON_JAVELIN,
)

javelin_look_212956 = spell(
    id=212956, name='Javelin', school=School.NORMAL, attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
    spell_icon_id=_ICON_JAVELIN,
    notes=f'{_D10}, MA3: the javelin\'s flight, a missile from a recruit to the javelin\'s spot (triggered), cast so '
          f'it lands with the hit (HaldenLogic.h LookDelayMs at {JAVELIN_SPEED:.0f} yd/s): Throw Javelin 62778\'s '
          'SpellVisual 11993 (the throw animation and a `HumanSpear01` missile). Look only.',
    raw_overrides={**kit_raw(instant=True, SpellVisualID_1=MA_JAVELIN, Targets=_TARGET_FLAG_DEST_LOCATION,
                             AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                             AttributesEx4=ATTR4_NO_CAST_LOG),
                   'Speed': JAVELIN_SPEED},
)

# --- MA4 Close Ranks! -------------------------------------------------------------------------------------------------

close_ranks_212957 = resolve_copy(
    212957, 'Close Ranks!', School.NORMAL, 'The recruits wheel around the drillmaster, spears out.',
    f'{_D10}, MA4 Close Ranks!: the band\'s tick, a persistent donut 5 to 11 yd round him (s7 #30 A; the spec\'s 6 to '
    '14 yd covered half the middle chamber) moving with him, a 2.5 s marker, then 6 s (heroic 8 s) of one tick a '
    'second: 10% (heroic 12%) of the reference row, the tank row on the tank (registry tag 4; the drill row '
    '`close-ranks` keys it 27). Lingering: no Weakened. Copy of the resolve spell 205001 (Physical).',
    icon=_ICON_SHIELD_WALL,
)

close_ranks_look_212958 = self_visual(
    212958, 'Close Ranks!', MA_CLOSE_RANKS,
    f'{_D10}, MA4: Shield Wall 871\'s SpellVisual 345 (`DefensiveStance_Impact_Chest`), cast by each recruit on itself '
    '(triggered) every 2 s while the ring turns (VR RISKY: an impact, so it is replayed). Look only.',
    icon=_ICON_SHIELD_WALL,
)
