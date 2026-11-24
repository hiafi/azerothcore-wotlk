"""
Scarlet Monastery build WP-D9: Forgemaster Gideon Crell, the Armorer (Crell 300940, Scarlet Recruit 300941; the forge,
anvil and quench trough GOs 301325-301327) (.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md
s3.5 row D9, s7 #28 A, s7 #29 A; build spec docs/dungeons/scarlet-monastery-3-armory.md "Forgemaster Gideon Crell,
the Armorer", AR1-AR8). WP-D9 owns this file; WP-S0 wrote the skeleton. The GO templates and spawns, his texts and his
spawn are data/sql/updates/pending_db_world/rev_crell_scarlet_monastery.sql.

Wave 2: the two creatures and the spells are declared now, so FD-SM's credit_creature(300940) (encounter 1078) has a
template and WP-H's heroic override (270k, heroic entry 310476 once set: CRELL_HEROIC) applies; only his ScriptName
waits for the wave switch (BIND_WAVE_2, flipped with kWave2Bound by W2-SETUP). While wave 2 is unbound he is a plain
melee elite at the anvil (ScriptName '': the AI is not registered, so naming it would log "not assigned" at boot).

- 300940 Forgemaster Gideon Crell <Armorer of the Crusade>: a NEW boss, boss_forgemaster_gideon_crell_rework
  (modules/mod-dungeon-bosses src/ScarletMonastery/boss_forgemaster_gideon_crell_rework.cpp). Level 37 warrior,
  Scarlet Crusade (faction 67), elite, the build spec's normal health (54k = HealthModifier 40.419 on the level 37
  warrior base 1,336), DamageModifier 2.6 (between Doan's 2.4 and Herod's 3.8: the Blade's cleave is his heavy hit),
  stun immunity 1972, INSTANCE_BIND (the encounter row's credit creature), display 3278 (Godric Rothgar, Armorer: V's
  pick, section 7 #34), SmartAI off, lootid 300940 (L-2's lists). Heroic health (270k) and the tier's melee are
  WP-H's overrides.
- 300941 Scarlet Recruit (heroic set dressing, AR6): not selectable, cannot be harmed, never fights (KIT_HELPER with
  the Scarlet faction and IMMUNE_TO_PC | IMMUNE_TO_NPC), display 2467 (the Scarlet Trainee, unarmed), walks at 1.5 yd/s
  (speed_walk 0.6). Summoned by Crell at the Armor Crate; no heroic template (WP-H's no-heroic list).

Spells (kSpellsCrell 212900-212949; CrellLogic.h names the same ids; looks from ._visuals, WP-V's AR_* picks, every
look unconfirmed until seen in game). His damage is a percent of the reference row (the tank row on the tank): the
registry lands the sparks, the slag, the Hammer, the steam, the bursts, the cleave on others, the dash lines and the
rivets through resolve copies; the cleave's tank hit binds the kit's spell_dungeon_refflat_damage (the percent in
hundredths in the effect, EffectMiscValueB on heroic). The plate's absorb and burn-back are absolute (5k / 25k, 20%):

  212900  Heat              AR2 a spark's hit: resolve copy, Fire, 30% / 45% and Weakened
  212901  Heat              AR2 the spark's burst at its spot (Molten Metal's SV 380, a look at the point)
  212902  Slag              AR2a a slag pool's tick (heroic): resolve copy, Fire, 10% a second
  212903  Slag              AR2a the pool's look, an aura on a stalker (the shipped 4 yd lava rung SV 90606)
  212904  Hammer            AR3 the 2.5 s bar (Physical, not interruptible)
  212905  Hammer            AR3 the donut's hit: resolve copy, Physical, 30% / 45% and Weakened
  212906  Anvil Burst       AR3 the anvil circle's hit: resolve copy, Physical, 30% / 45% and Weakened
  212907  Hammer            AR3 the strike on the anvil (Temper 52238's SV 11517, a look at the point)
  212908  Quench            AR4 the steam's tick: resolve copy, Fire, 8% / 12% a second
  212909  Quench            AR4 the steam's look, an aura on a stalker (Scalding Water's SV 8657)
  212910  Slag Burst        AR4a a pool's burst (heroic): resolve copy, Fire, 45% and Weakened
  212911  Slag Burst        AR4a the burst at the pool (Fire Nova's SV 963, a look at the point)
  212912  Temper            AR5 the 2.5 s interruptible cast (heroic; Fire: the Hammer's bar is Physical)
  212913  Flawed            AR5 the kicked piece's marker on Crell (look and tooltip only)
  212914  Masterwork        AR5 the missed piece's marker on Crell (look and tooltip only)
  212915  Forged Blade      AR-Bl the holder aura for the Blade window (the script removes it)
  212916  Cleave            AR-Bl the cleave on others: resolve copy, Physical, 30% / 45% and Weakened
  212917  Cleave            AR-Bl the cleave on the tank: 15% / 25% of the tank row (kit percent script)
  212918  Proving Strike    AR7 a dash line's hit: resolve copy, Physical, 30% / 45%, the follow-ups 20% / 30%
  212919  Proving Strike    AR7 the dash on Crell (Charge's SV 867)
  212920  Red-Hot Plate     AR-Pl the absorb (spell_sm_crell_red_hot_plate; Burning Brand's state SV 1946)
  212921  Red-Hot Plate     AR-Pl the burn-back on an attacker: Fire, 20% of the absorbed hit (custom value)
  212922  Popping Rivet     AR8 a rivet's hit: resolve copy, Fire, 30% / 45% and Weakened
  212923  Popping Rivet     AR8 the rivet's flight (Fireball's SV 67: never Heated Hammer's 7671)
  212924-212949 spare.
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
    TARGET_UNIT_TARGET_ENEMY,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, scripted_by, spell

from ._common import (
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_2,
    FACTION_SCARLET_CRUSADE,
    IMMUNITY_BOSS_STUN,
    KIT_CREATURE,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    AR_ANVIL_STRIKE,
    AR_CLEAVE,
    AR_DASH,
    AR_PLATE,
    AR_RIVET,
    AR_SLAG,
    AR_SLAG_BURST,
    AR_SPARKS,
    AR_STEAM,
    DISPLAY_CRELL,
    DISPLAY_SCARLET_TRAINEE,
)

_D9 = 'Scarlet Monastery build WP-D9 (Forgemaster Gideon Crell)'

# --- the creatures ---------------------------------------------------------------------------------------------------

# His heroic entry (difficulty_entry_1 = his id in source/world/heroic_ids.lock). WP-H's mint table names 310476 (the
# first wave 2 unit after the 18 wave 1 kit units); every lower kit unit is declared, so the run mints exactly that id
# (W2-SETUP's reconcile; lib/test_scarlet_monastery_heroic.py KIT_HEROIC_ID names the same id).
CRELL_HEROIC_PLANNED = 310476
CRELL_HEROIC = CRELL_HEROIC_PLANNED

CRELL = 300940
SCARLET_RECRUIT = 300941

SCRIPT_NAME = 'boss_forgemaster_gideon_crell_rework'

_RANK_ELITE = 1
_CLASS_WARRIOR = 1
_FLAGS_EXTRA_NO_XP = 0x40
_UNIT_FLAG_NON_ATTACKABLE = 0x2
_UNIT_FLAG_IMMUNE_TO_PC = 0x100
_UNIT_FLAG_IMMUNE_TO_NPC = 0x200
_UNIT_FLAG_NOT_SELECTABLE = 0x02000000

# The build spec's normal health at 5 players (S0's table): 54k = 40.419 x 1,336 (the level 37 warrior).
# creature_classlevelstats basehp0, live 2026-11-20.
CRELL_HEALTH_MODIFIER = 40.419
CRELL_DAMAGE_MODIFIER = 2.6
# R-2-FW MN-1: 9 yd, so the storeroom can be cleared around him (the nearest Guardsmen stand 10.4 and 11 yd away and a
# body pull of them brings the tank 9-14 yd from him); D9 wants him pulled alone (Halden's approach, 10 yd).
CRELL_DETECTION_RANGE = 9.0



def _heroic_entry(columns: dict, heroic_entry) -> dict:
    """`columns` with difficulty_entry_1 when it is set (a declared full row must carry it)."""
    if heroic_entry:
        return {**columns, 'difficulty_entry_1': heroic_entry}
    return columns


forgemaster_gideon_crell_300940 = creature_template(300940, 'Forgemaster Gideon Crell', **_heroic_entry({
    **KIT_CREATURE, 'subname': 'Armorer of the Crusade', 'minlevel': 37, 'maxlevel': 37, 'rank': _RANK_ELITE,
    'unit_class': _CLASS_WARRIOR, 'faction': FACTION_SCARLET_CRUSADE, 'type': 7, 'exp': 0,
    'HealthModifier': CRELL_HEALTH_MODIFIER, 'DamageModifier': CRELL_DAMAGE_MODIFIER, 'ManaModifier': 1.0,
    'ExperienceModifier': 2.0, 'BaseAttackTime': 2000, 'speed_run': 1.14286, 'detection_range': CRELL_DETECTION_RANGE,
    'CreatureImmunitiesId': IMMUNITY_BOSS_STUN, 'lootid': 300940, 'mingold': 300, 'maxgold': 900,
    'flags_extra': 1, 'ScriptName': SCRIPT_NAME if BIND_WAVE_2 else '', 'AIName': '',
}, CRELL_HEROIC))
creature_model(300940, display_id=DISPLAY_CRELL)

scarlet_recruit_300941 = creature_template(300941, 'Scarlet Recruit', **{
    **KIT_HELPER, 'faction': FACTION_SCARLET_CRUSADE, 'minlevel': 30, 'maxlevel': 30, 'rank': 0,
    'unit_class': _CLASS_WARRIOR,
    'unit_flags': _UNIT_FLAG_NON_ATTACKABLE | _UNIT_FLAG_IMMUNE_TO_PC | _UNIT_FLAG_IMMUNE_TO_NPC
    | _UNIT_FLAG_NOT_SELECTABLE,
    'speed_walk': 0.6, 'speed_run': 1.14286, 'flags_extra': _FLAGS_EXTRA_NO_XP, 'ScriptName': '', 'AIName': '',
})
creature_model(300941, display_id=DISPLAY_SCARLET_TRAINEE)

# --- constants (CrellLogic.h; lib/test_scarlet_monastery_crell.py pins each against the header) -----------------------

HAMMER_CAST_MS = 2500               # kHammerCastMs
TEMPER_CAST_MS = 2500               # kTemperCastMs
CLEAVE_TANK_PCT = (1500, 2500)      # kCleaveTankPct 15 / 25 (hundredths: normal in the effect, heroic in MiscValueB)
RIVET_SPEED = 12.0                  # yd/s: a rivet near a player 15-30 yd off flies about the 2 s marker

_AURA_SCHOOL_MASK_ALL = 127
_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40
_DEFENSE_MAGIC = 1
_DEFENSE_MELEE = 2
_PREVENTION_SILENCE = 1
_SPELL_INTERRUPT_FLAGS_KICK = 15
_ATTR0_DO_NOT_DISPLAY = 0x00000080
_ATTR0_DO_NOT_LOG = 0x00000100

_SCRIPT_REFFLAT = ('Scarlet Monastery D9: a percent of reference health in hundredths, set by the kit\'s '
                   'spell_dungeon_refflat_damage (DungeonKit::RefFlatOn: the tank row on the tank)')
_SCRIPT_PLATE = ('Scarlet Monastery D9: the absorb amount is set at the cast (CastCustomSpell: 5k / 25k, flawed 12.5k, '
                 'masterwork 50k; CrellLogic.h PlateAbsorb)')
_SCRIPT_BURN = ('Scarlet Monastery D9: the burn-back is 20% of the hit the plate absorbed, set at the cast by '
                'spell_sm_crell_red_hot_plate (CastCustomSpell)')

# Stock icons (Spell.dbc SpellIconID of the named spell, read from the stock client 2026-11-20)
_ICON_MOLTEN_METAL = 12                 # Molten Metal 5213
_ICON_FLAME_PATCH = 876                 # Flame Patch 35383
_ICON_THUNDERCLAP = 199                 # Thunder Clap 6343 (the Hammer)
_ICON_STEAM = 1920                      # Scalding Water 37284
_ICON_FIRE_NOVA = 33                    # Fire Nova 11969
_ICON_TEMPER = 42                       # Temper 52238
_ICON_CLEAVE = 277                      # Cleave 15496
_ICON_CHARGE = 457                      # Charge 100
_ICON_MOLTEN_ARMOR = 2307               # Molten Armor 30482
_ICON_FIREBALL = 185                    # Fireball 133

# --- AR2 Heat, AR2a Slag ----------------------------------------------------------------------------------------------


def _look_at_point(spell_id: int, name: str, visual: int, notes: str, icon: int, speed: float = 0.0):
    """A look-only spell cast at a point (a DUMMY aimed at a destination; DO_NOT_DISPLAY | DO_NOT_LOG), triggered (the
    Kell / Baelgar look shape). `speed` (yd/s) makes it a missile from the caster."""
    raw = kit_raw(instant=True, SpellVisualID_1=visual, Targets=_TARGET_FLAG_DEST_LOCATION,
                  AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                  AttributesEx4=ATTR4_NO_CAST_LOG)
    if speed:
        raw['Speed'] = speed
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


def _stalker_look(spell_id: int, name: str, visual: int, desc: str, notes: str, icon: int):
    """A lasting look: a DUMMY aura (no duration) the wave 2 stalker 300958 casts on itself (triggered); the stalker
    despawns with the effect. No effect."""
    return spell(
        id=spell_id, name=name, school=School.FIRE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, desc, CastingTimeIndex=1, SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


def _marker_aura(spell_id: int, name: str, desc: str, aura_desc: str, notes: str, icon: int, visual: int = 0):
    """A DUMMY aura Crell casts on himself (triggered), no duration: the script removes it. Not dispellable."""
    raw = kit_raw(desc, aura_desc, CastingTimeIndex=1, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG)
    if visual:
        raw['SpellVisualID_1'] = visual
    return spell(
        id=spell_id, name=name, school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


spark_212900 = resolve_copy(
    212900, 'Heat', School.FIRE, 'Sparks shower the storeroom.',
    f'{_D9}, AR2 Heat: a spark\'s hit, one of 10 circles of 5 yd (heroic 16 of 4 yd: s7 #28 A) at random floor spots '
    'at least 4 yd apart (never aimed at a player), a 2.5 s marker, at each order\'s yell: 30% (heroic 45%) of the '
    'reference row and 1 Weakened, the tank row on the tank (registry tag 2). Copy of the mod-boss-mechanics resolve '
    'spell 205001 (Fire).',
    icon=_ICON_MOLTEN_METAL,
)

spark_look_212901 = _look_at_point(
    212901, 'Heat', AR_SPARKS,
    f'{_D9}, AR2: the spark\'s burst, cast by Crell at the spark\'s spot (triggered) as it lands: Molten Metal 5213\'s '
    'SpellVisual 380 (`FlamestrikeSmall_Impact_Base`, 3.9 yd). The marker is the registry\'s. Look only.',
    icon=_ICON_MOLTEN_METAL,
)

slag_212902 = resolve_copy(
    212902, 'Slag', School.FIRE, 'A pool of molten slag.',
    f'{_D9}, AR2a Slag (heroic): a pool\'s tick, a persistent 3 yd Zone where each spark landed, one tick a second '
    'until the Quench bursts it: 10% of the reference row (registry tag 21). Lingering: no Weakened. Copy of the '
    'resolve spell 205001 (Fire).',
    icon=_ICON_FLAME_PATCH,
)

slag_look_212903 = _stalker_look(
    212903, 'Slag', AR_SLAG, 'Molten slag.',
    f'{_D9}, AR2a: the pool\'s look, a DUMMY aura on a stalker at the pool (the shipped 4 yd lava rung SV 90606; the '
    'pool is 3 yd, the registry\'s ring is the exact edge: VR RISKY). The stalker goes with the burst.',
    icon=_ICON_FLAME_PATCH,
)

# --- AR3 Hammer -------------------------------------------------------------------------------------------------------

hammer_cast_212904 = cast_bar(
    212904, 'Hammer', HAMMER_CAST_MS, 'Forgemaster Gideon Crell raises his hammer over the anvil.',
    f'{_D9}, AR3 Hammer: the 2.5 s bar while the donut (8 yd from the anvil to the walls) is marked; the anvil circle '
    'follows 2 s (heroic 1.5 s) after it lands. Not interruptible: the registry lands the hits whatever happens to the '
    'bar. Physical: a kicked Temper (Fire, heroic) never locks this bar (rule 5).',
    icon=_ICON_THUNDERCLAP,
)

hammer_ring_212905 = resolve_copy(
    212905, 'Hammer', School.NORMAL, 'The blow rolls out from the anvil.',
    f'{_D9}, AR3 Hammer: the donut\'s hit, everything from the anvil\'s 8 yd circle to the walls (60 yd), at the '
    'bar\'s end: 30% (heroic 45%) of the reference row and 1 Weakened, the tank row on the tank (registry tag 3). '
    'Copy of the resolve spell 205001 (Physical).',
    icon=_ICON_THUNDERCLAP,
)

anvil_burst_212906 = resolve_copy(
    212906, 'Anvil Burst', School.NORMAL, 'The anvil bursts.',
    f'{_D9}, AR3 Hammer: the anvil circle\'s hit, 8 yd round the anvil, 2 s (heroic 1.5 s) after the donut: 30% '
    '(heroic 45%) of the reference row and 1 Weakened, the tank row on the tank (registry tag 31). In, then out. Copy '
    'of the resolve spell 205001 (Physical).',
    icon=_ICON_THUNDERCLAP,
)

anvil_strike_look_212907 = _look_at_point(
    212907, 'Hammer', AR_ANVIL_STRIKE,
    f'{_D9}, AR3: the strike on the anvil, cast by Crell at the anvil (triggered) as the donut and as the circle land: '
    'Temper 52238\'s SpellVisual 11517 (`DecisiveStrike_Impact_Chest`, sound 3091). Look only.',
    icon=_ICON_THUNDERCLAP,
)

# --- AR4 Quench, AR4a Slag Burst --------------------------------------------------------------------------------------

steam_212908 = resolve_copy(
    212908, 'Quench', School.FIRE, 'Scalding steam.',
    f'{_D9}, AR4 Quench: the steam\'s tick, a persistent 10 yd Zone round the trough for 8 s, one tick a second (the '
    'first a second after the plunge): 8% (heroic 12%) of the reference row, the tank row on the tank (registry tag '
    '4). Lingering: no Weakened. The tank walks him out. Copy of the resolve spell 205001 (Fire).',
    icon=_ICON_STEAM,
)

steam_look_212909 = _stalker_look(
    212909, 'Quench', AR_STEAM, 'Scalding steam.',
    f'{_D9}, AR4: the steam\'s look, a DUMMY aura on a stalker at the trough for the 9 s of the steam: Scalding Water '
    '37284\'s SpellVisual 8657 (`steam.mdx` State; never Scalding Steam\'s one-shot SV 10373). Size unmeasured (VR '
    'RISKY): the registry\'s ring is the exact edge.',
    icon=_ICON_STEAM,
)

slag_burst_212910 = resolve_copy(
    212910, 'Slag Burst', School.FIRE, 'The slag explodes.',
    f'{_D9}, AR4a Slag Burst (heroic): at the Quench every slag pool swells (a 2.5 s marker) and bursts, a 5 yd circle '
    'at the pool: 45% of the reference row and 1 Weakened, the tank row on the tank (registry tag 41); the pool is '
    'gone. Copy of the resolve spell 205001 (Fire).',
    icon=_ICON_FIRE_NOVA,
)

slag_burst_look_212911 = _look_at_point(
    212911, 'Slag Burst', AR_SLAG_BURST,
    f'{_D9}, AR4a: the burst at a pool, cast by Crell at the pool (triggered) as it bursts: Fire Nova 11969\'s '
    'SpellVisual 963 (`FireNova_Area`). Look only.',
    icon=_ICON_FIRE_NOVA,
)

# --- AR5 Temper (heroic) ----------------------------------------------------------------------------------------------

temper_212912 = spell(
    id=212912, name='Temper', school=School.FIRE, dispel=0, mechanic=0, attributes=0,
    cast_time_ms=TEMPER_CAST_MS, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_TEMPER,
    notes=f'{_D9}, AR5 Temper (heroic): a 2.5 s cast at each order\'s T+10 (emote line 3), ending on the Issue: an '
          'expected interrupt. NOT triggered, so the bar shows and a kick stops it: InterruptFlags 15 and '
          'PreventionType 1 (a silence); his immunity set 1972 holds no INTERRUPT or SILENCE. No effect of its own: '
          'the script reads the outcome (OnSpellFailed: flawed, the Blade 8 s and the plate 12.5k; OnSpellCast: '
          'masterwork, 25 s and 50k). On the bots\' interrupt list (priority 3). Fire: the Hammer\'s bar is '
          'Physical, so a kick on this never locks the Hammer.',
    raw_overrides=kit_raw('Crell tempers the piece. Interrupt him or it comes out masterwork.',
                          InterruptFlags=_SPELL_INTERRUPT_FLAGS_KICK, PreventionType=_PREVENTION_SILENCE,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

flawed_212913 = _marker_aura(
    212913, 'Flawed', 'The piece came out flawed.', 'Flawed: the Blade lasts 8 sec, the plate holds half.',
    f'{_D9}, AR5: the kicked Temper\'s marker, on Crell from the kick to the next order (tooltip only).',
    icon=_ICON_TEMPER,
)

masterwork_212914 = _marker_aura(
    212914, 'Masterwork', 'The piece came out masterwork.',
    'Masterwork: the Blade lasts 25 sec, the plate holds double and burns twice as much.',
    f'{_D9}, AR5: the missed Temper\'s marker, on Crell from the cast\'s end to the next order (tooltip only).',
    icon=_ICON_TEMPER,
)

# --- AR-Bl Forged Blade, AR7 Proving Strike ---------------------------------------------------------------------------

forged_blade_212915 = _marker_aura(
    212915, 'Forged Blade', 'Crell takes up the blade he forged.',
    'Forged Blade: his swings cleave in front of him, and he tests the edge on everyone.',
    f'{_D9}, AR-Bl Forged Blade: the holder aura for the Blade window, 15 s (heroic flawed 8, masterwork 25); the '
    'script removes it. The look is the sword in his hand (creature equipment, item 5305).',
    icon=_ICON_CLEAVE,
)

cleave_212916 = resolve_copy(
    212916, 'Cleave', School.NORMAL, 'The forged blade cleaves.',
    f'{_D9}, AR-Bl: the cleave on others, a registry Frontal (90 degrees, 8 yd, a 1.5 s marker, the tank exempt) every '
    '6 s while he holds the Blade: 30% (heroic 45%) of the reference row and 1 Weakened (registry tag 10). Copy of the '
    'resolve spell 205001 (Physical).',
    icon=_ICON_CLEAVE, visual=AR_CLEAVE,
)

cleave_tank_212917 = spell(
    id=212917, name='Cleave', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_ACTIVE_DEFENSE,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=CLEAVE_TANK_PCT[0] - 1, die_sides=1,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_CLEAVE,
    notes=f'{_D9}, AR-Bl: the cleave on the tank as the Frontal lands (the victim inside the cone): 15% (heroic 25%: '
          'EffectMiscValueB) of the tank\'s row, Physical, instant, never missed (always hits, no active defense, '
          'cannot crit) and ignoring his modifiers. Tank work: no Weakened. Binds the kit\'s '
          'spell_dungeon_refflat_damage. Cleave 15496\'s SV 219.',
    raw_overrides=kit_raw('The forged blade cleaves.', instant=True, EffectMiscValueB_1=CLEAVE_TANK_PCT[1],
                          DefenseType=_DEFENSE_MELEE, SpellVisualID_1=AR_CLEAVE,
                          AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(cleave_tank_212917, 'spell_dungeon_refflat_damage')

proving_strike_212918 = resolve_copy(
    212918, 'Proving Strike', School.NORMAL, 'Crell tests the edge.',
    f'{_D9}, AR7 Proving Strike: a dash line\'s hit, 3 yd wide from where Crell stands to 5 yd past a player\'s spot '
    '(stopped at a wall), one per player in a random order, 2 s after the Blade\'s Issue (heroic: every 10 s while he '
    'holds it); the first marked 2 s, the later ones 1 s: 30% (heroic 45%), the follow-ups 20% (30%) of the reference '
    'row and 1 Weakened, the tank row on the tank (registry tag 7). Copy of the resolve spell 205001 (Physical).',
    icon=_ICON_CHARGE,
)

dash_look_212919 = self_visual(
    212919, 'Proving Strike', AR_DASH,
    f'{_D9}, AR7: the dash, cast by Crell on himself (triggered) as he charges along a line: Charge 100\'s SpellVisual '
    '867. The line\'s marker is the registry\'s. Look only.',
    icon=_ICON_CHARGE,
)

# --- AR-Pl Red-Hot Plate, AR8 Popping Rivets --------------------------------------------------------------------------

red_hot_plate_212920 = spell(
    id=212920, name='Red-Hot Plate', school=School.FIRE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.SCHOOL_ABSORB, base_points=0, die_sides=0,
                    misc_value=_AURA_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded=_SCRIPT_PLATE)],
    spell_icon_id=_ICON_MOLTEN_ARMOR,
    notes=f'{_D9}, AR-Pl Red-Hot Plate: the armor fresh from the forge, cast by Crell on himself (triggered) at a '
          'Plate Issue (normal even orders, heroic every order) with the absorb as its custom value: 5k (heroic 25k; '
          'flawed 12.5k, masterwork 50k), every school, until broken. spell_sm_crell_red_hot_plate burns 20% of each '
          'absorbed hit back on its attacker (212921) and tells the AI the plate broken (a rivet per quarter, heroic '
          'eighth). Sunder Armor, Expose Armor and Faerie Fire tear 500 more off by the AI\'s SpellHit (no burn). Not '
          'dispellable or stealable. Burning Brand 29618\'s lasting state SV 1946 (`Immolate_State_Base`; Molten '
          'Armor\'s 7757 and Fire Shield\'s 289 are one-shot head impacts).',
    raw_overrides=kit_raw('Red-hot armor absorbs damage and burns its attackers.',
                          'Absorbs damage. 20% of the damage it absorbs burns the attacker as Fire.',
                          CastingTimeIndex=1, SpellVisualID_1=AR_PLATE, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(red_hot_plate_212920, 'spell_sm_crell_red_hot_plate')

plate_burn_212921 = spell(
    id=212921, name='Red-Hot Plate', school=School.FIRE, dispel=0, mechanic=0, attributes=ATTR0_NO_ACTIVE_DEFENSE,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_BURN)],
    spell_icon_id=_ICON_MOLTEN_ARMOR,
    notes=f'{_D9}, AR-Pl: the burn-back, cast by Crell (triggered) on whoever\'s hit the plate absorbed (players, '
          'pets, their spells and ticks alike): 20% of the absorbed amount as Fire, a custom value (no percent of a '
          'row: the plate\'s size fixes the total, 1k across the group on normal). Never missed, cannot crit, ignores '
          'his modifiers, no threat. No Weakened: a healing tax.',
    raw_overrides=kit_raw('The red-hot plate burns its attacker.', instant=True, DefenseType=_DEFENSE_MAGIC,
                          AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

rivet_212922 = resolve_copy(
    212922, 'Popping Rivet', School.FIRE, 'A red-hot rivet lands.',
    f'{_D9}, AR8 Popping Rivets: a rivet\'s hit, a 4 yd circle at a random floor spot within 8 yd of a random player '
    '(the tank included), a 2 s marker, one per quarter (heroic eighth) of the plate broken: 30% (heroic 45%) of the '
    'reference row and 1 Weakened, the tank row on the tank (registry tag 8). Copy of the resolve spell 205001 (Fire).',
    icon=_ICON_FIREBALL,
)

rivet_look_212923 = _look_at_point(
    212923, 'Popping Rivet', AR_RIVET,
    f'{_D9}, AR8: the rivet\'s flight, a missile from Crell to the rivet\'s spot (triggered) as its marker starts, at '
    f'{RIVET_SPEED:.0f} yd/s: Fireball 133\'s SpellVisual 67 (`Fireball_Missile_Low` + `MoltenBlast`; never Heated '
    'Hammer\'s 7671, a silver holy hammer). Look only.',
    icon=_ICON_FIREBALL, speed=RIVET_SPEED,
)
