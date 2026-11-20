"""
Blackrock Depths build WP-D8: Warder Stilgiss and Verek (9041, 9042), "The Antiquarian of Blackrock City", normal and
heroic (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.4 / s3.5 row D8 / s3.6; build spec
docs/dungeons/blackrock-depths-2-shadowforge-city.md "Warder Stilgiss and Verek", Build spec, rulings 40, 41, 88).
WP-D8 owns this file (its spells: kSpellsStilgissVerek 211050-211089 of modules/mod-dungeon-bosses
src/BlackrockDepths/BlackrockDepthsRework.h only; StilgissVerekLogic.h names the same ids).

- 9041 Warder Stilgiss: boss_warder_stilgiss_rework (SmartAI off: the S0 SQL rev dropped his five rows, Frost Armor
  included, which the script casts out of combat now), the build spec's normal health (110k = HealthModifier 54.294 on
  the level 54 paladin class base 2,026), DamageModifier 3.5 (the stock value: the live one is a mod-progression
  leftover; he never melees), stun immunity 1972, INSTANCE_BIND. Heroic 180k is WP-H's override. His stock Frost Ward
  15044 and the flee for assist at 15% are retired; Frostbolt and Frost Nova are his own copies below.
- 9042 Verek: npc_verek_rework (SmartAI off, his two rows dropped by S0's rev), 50k = HealthModifier 20.383 on the level
  53 warrior class base 2,453, DamageModifier 3.5, stun immunity 1972 (the "-251" of the stock row; handoff section
  7 #10 and STAGE-H report 7 item 3: D8 sets his normal row, the heroic copy states 1972 too), no INSTANCE_BIND (row
  233 credits the pair by spell 211066; only Stilgiss binds, _common.py NO_INSTANCE_BIND). Heroic
  85k is WP-H's. His display (9019, the red hound), his model rows and his Enrage 8599 are the stock ones.
- No boss-kit creature of its own: the Bindings chain and the Black Blood patch ride on the shared generic stalker
  NPC_BRD_STALKER (300796, a shared-file request: the orchestrator declares it, like Blackrock Spire's 300713). The
  script summons it when it exists and the fight plays without the look when it does not. No heroic template for it.

Spells. Every artifact's hit is a dungeon copy of the mod-boss-mechanics resolve spell (the registry's percent of the
reference row; the combat log names the mechanic); the Bindings tick, Frostbolt and Black Blood's heal are the kit's
percent spells (spell_dungeon_refflat_damage; the heal is a plain percent of Verek's own health). The rest is the cast
bars, the looks, the debuffs and Verek's curse:

  211050  Open Coffer          SV1 the 2 s opening at a coffer door (a cast bar, not interruptible, Physical), Opening
                               Relic Coffer 13478's SV 104
  211051  Eye of Kajal         SV2 the beam's hit: resolve copy (Shadow), 25% / 40% Weakened; Eye Beam 26134's chest
                               impact SV 7434
  211052  Black Steel Bindings SV3 the 8 s DUMMY debuff on both of the chained pair, so each knows who he is chained to
  211053  Black Steel Bindings SV3 the tick while the pair is more than 8 yd apart: 4% / 6% a second (Physical)
  211054  Black Steel Bindings SV3 the chain look: a channel from a stalker standing on one of the pair to the other
                               (Harpoon Chain 49679's SV 10920); ends with the Bindings
  211055  Magma Forged Band     SV4 the 2.5 s bar (Fire, not interruptible), Magma Wave 55916's SV 12227
  211056  Magma Forged Band     SV4 the band's hit: resolve copy (Fire), 30% / 45% Weakened
  211057  Wand of Eternal Light SV5 a line's hit: resolve copy (Holy), 20% / 35% Weakened; Holy Fire 15261's SV 3400
  211058  Black Blood           SV6 a pool's tick: resolve copy (Shadow), 4% / 6% a second
  211059  Black Blood           SV6 Verek's heal while he stands in a pool: 2% of his health a second (HEAL_PCT)
  211060  Frost Nova            SV7 the 1.5 s bar (Arcane, see below; not interruptible)
  211061  Frost Nova            SV7 the nova's hit: resolve copy (Frost), 10% / 14%, with the 2 s root; Frost Nova
                               12674's SV 17
  211062  Frost Nova            SV7 the 2 s root (the stock one is 8 s)
  211063  Frostbolt             SV8 his stock bolt as his own copy: 3 s, 40 yd, 8% / 10% and the stock -50% for 4 s,
                               interruptible (a reward)
  211064  Curse of Blood        SV9 Verek's curse: +10% physical damage taken for 30 s (stock: +1 flat), a Curse
  211065  Black Blood           SV6 the pool's dark patch, a state on the stalker standing in it
  211066  Stilgiss and Verek    the encounter's credit (F-1a): a server-side DUMMY never cast; the instance credits
                               lfg row 233 (creditType 1) with it once both are dead
  211067-211089 spare.

Frost Nova's bar is Arcane on purpose (handoff section 3.5 rule 5): a kick on Frostbolt (Frost) locks Frost for the
interrupt's length, and a Frost bar of his would stop casting then. Visual ids are WP-V-1's (._visuals); the three
stock looks _visuals.py does not name (Frostbolt SV 13, Curse of Blood SV 876 and Frost Armor's) are local constants
below and a shared-file request. Every look is unconfirmed until seen in game. Tooltips are number-free.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import ATTR1_NO_THREAT, ATTR2_IGNORE_LINE_OF_SIGHT, TARGET_UNIT_CASTER
from lib.dsl.registry import creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    ST_CURSE_OF_BLOOD,
    ST_FROSTBOLT,
    SHIPPED_SHADOW_POOL_4_STATE,
    ST_BLACK_STEEL_BINDINGS,
    ST_EYE_IMPACT,
    ST_MAGMA_BAND,
    ST_OPEN_COFFER,
    ST_WAND_IMPACT,
    VL_FROST_NOVA,
)

creature_template_columns(9041, **boss_columns(
    'boss_warder_stilgiss_rework', 54.294, damage_modifier=3.5,
))
creature_template_columns(9042, **boss_columns(
    'npc_verek_rework', 20.383, damage_modifier=3.5, instance_bind=False,
))

_SD = 'Blackrock Depths build WP-D8 (Warder Stilgiss and Verek)'

_SCRIPT_REFFLAT = ('Blackrock Depths: a percent of reference health in hundredths, set at launch by the kit\'s '
                   'spell_dungeon_refflat_damage (DungeonKit::RefFlatOn)')
_SCRIPT_HEAL_PCT = 'Blackrock Depths: a percent of the target\'s own maximum health, not a heal value'
_REFFLAT = 'spell_dungeon_refflat_damage'

# Icons of the stock spells the looks come from (Spell.dbc, the working copy).
_ICON_GENERIC = 1
_ICON_EYE_BEAM = 141                        # Eye Beam 26134
_ICON_CHAINS = 1540                         # Chains of Kel'Thuzad 28410
_ICON_MAGMA_WAVE = 1137                     # Magma Wave 55916
_ICON_HOLY_LIGHT = 70                       # Holy Light 1026
_ICON_BLACK_BLOOD = 2179                    # Black Blood 35331
_ICON_FROST_NOVA = 193                      # Frost Nova 12674
_ICON_FROSTBOLT = 188                       # Frostbolt 12675
_ICON_CURSE_OF_BLOOD = 130                  # Curse of Blood 15042
_ICON_CHILLED = 181                         # Chilled 6136

_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_UNIT_TARGET_ALLY = 21
_TARGET_FLAG_UNIT = 0x2
_DEFENSE_MAGIC = 1
_PREVENTION_SILENCE = 1
_INTERRUPT_FLAGS_KICKABLE = 15
_ATTR1_IS_CHANNELED = 0x00000004
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000     # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map
_MECHANIC_SNARE = 11
_MECHANIC_ROOT = 7
_DISPEL_CURSE = 2
_SCHOOL_MASK_PHYSICAL = 1                   # MOD_DAMAGE_PERCENT_TAKEN's EffectMiscValue

# StilgissVerekLogic.h: the percents in hundredths (normal; heroic in EffectMiscValueB_1) and the durations.
_OPEN_COFFER_MS = 2000                      # kOpenMs
_MAGMA_CAST_MS = 2500                       # kMagmaCastMs
_NOVA_CAST_MS = 1500                        # kNovaCastMs
_NOVA_ROOT_MS = 2000                        # kNovaRootMs
_BINDINGS_MS = 8000                         # kBindingsMs
_BLOOD_LIFE_MS = 30000                      # kBloodLifeMs (the look lasts as long as the pool)
_FROSTBOLT_CAST_MS = 3000                   # kFrostboltCastMs
_FROSTBOLT_SLOW_MS = 4000                   # kFrostboltSlowMs
_CURSE_MS = 30000                           # kCurseMs
_CURSE_PCT = 10                             # kCursePhysicalPct
_BINDINGS_TICK = (400, 600)                 # kBindingsPct 4 / 6
_FROSTBOLT_HIT = (800, 1000)                # kFrostboltPct 8 / 10
_BLOOD_HEAL = 2                             # kBloodHealPct 2 (HEAL_PCT base 1 + 1)
_FROSTBOLT_SPEED = 24.0                     # Frostbolt 12675's missile speed

# --- SV1 Open Coffer -------------------------------------------------------------------------------------------------

open_coffer_211050 = cast_bar(
    211050, 'Open Coffer', _OPEN_COFFER_MS, 'Warder Stilgiss opens a coffer.',
    f'{_SD}, SV1: the 2 s opening at a Relic Coffer door (SP: not interruptible, designer), cast by '
    'boss_warder_stilgiss_rework (not triggered, so the bar shows) once he has walked to the door; the artifact is '
    'drawn when it ends. DUMMY on the caster, Physical. The door only plays its animation (a custom animation by '
    'script); its state and lock never change. Opening Relic Coffer 13478\'s SV 104 (animation and sound).',
    icon=_ICON_GENERIC, visual=ST_OPEN_COFFER,
)

# --- SV2 Eye of Kajal ------------------------------------------------------------------------------------------------

eye_hit_211051 = resolve_copy(
    211051, 'Eye of Kajal', School.SHADOW, 'The Eye of Kajal burns everything in its gaze.',
    f'{_SD}, SV2: the beam\'s hit: a 4 yd line from Stilgiss through a random player to the wall (the kit\'s '
    'LineStrike, clipped to the hall), 2 s marker, 25% (heroic 40%) of the reference row to everyone on it, the tank '
    'on its own row, 1 Weakened. Copy of the mod-boss-mechanics resolve spell (Shadow). Eye Beam 26134\'s '
    'SV 7434 on every unit hit: only the chest impact, the red line marker is the beam (VISUALS report).',
    icon=_ICON_EYE_BEAM, visual=ST_EYE_IMPACT,
)

# --- SV3 Black Steel Bindings ----------------------------------------------------------------------------------------

bindings_211052 = spell(
    id=211052, name='Black Steel Bindings', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=_BINDINGS_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_CHAINS,
    notes=f'{_SD}, SV3: the 8 s debuff on both of the chained pair (two random players, the tank included, ruling 88; '
          'every 15 s while the artifact is held), put on by boss_warder_stilgiss_rework (AddAura, Stilgiss as '
          'caster) so each knows he is chained. DUMMY, no damage, not dispellable (the cost is the script\'s tick, '
          '211053). The script ends it early when either dies or leaves, and on reset, evade and death. '
          'AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('Chained to another player. Stay close to them.',
                          'Chained to another player. Taking damage while more than $s1 yards apart.',
                          CastingTimeIndex=1, EffectMiscValueB_1=0, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

bindings_tick_211053 = spell(
    id=211053, name='Black Steel Bindings', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=_BINDINGS_TICK[0] - 1, die_sides=1,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_CHAINS,
    notes=f'{_SD}, SV3: the tick on each of the chained pair every second while they are more than 8 yd apart (or on '
          'another floor): 4% (heroic 6%) of the reference row, the tank on its own row (spell_dungeon_refflat_damage, '
          'hundredths in the effect, heroic in EffectMiscValueB_1). Physical; ignores caster modifiers; cast by '
          'Stilgiss (triggered). The chain look is 211054.',
    raw_overrides=kit_raw('The chains tear at you.', instant=True, InterruptFlags=0, PreventionType=0,
                          DefenseType=0, EffectMiscValueB_1=_BINDINGS_TICK[1], AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(bindings_tick_211053, _REFFLAT)

bindings_chain_211054 = spell(
    id=211054, name='Black Steel Bindings', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=_BINDINGS_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_CHAINS,
    notes=f'{_SD}, SV3: the chain look, a channel the stalker standing on one of the pair (it follows them) casts '
          '(triggered) on the other: Harpoon Chain 49679\'s SV 10920 (an iron chain between caster and target, VISUALS '
          'report; never Chains of Kel\'Thuzad SV 7597). A DUMMY aura on the other player, no damage; 8 s, cut by the '
          'script when the pair ends. Not a cast of a player: the chained players keep casting. Ignores line of sight. '
          'AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('', 'Chained.', CastingTimeIndex=1, InterruptFlags=0, ChannelInterruptFlags=0,
                          PreventionType=0, SpellVisualID_1=ST_BLACK_STEEL_BINDINGS,
                          AttributesEx=_ATTR1_IS_CHANNELED | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- SV4 Magma Forged Band -------------------------------------------------------------------------------------------

magma_cast_211055 = cast_bar(
    211055, 'Magma Forged Band', _MAGMA_CAST_MS, 'Warder Stilgiss raises the Magma Forged Band.',
    f'{_SD}, SV4: the 2.5 s bar before the band burns (every 15 s while the artifact is held; the cast queue holds '
    'his other casts and his walk). DUMMY on the caster, Fire, not interruptible: a kick on Frostbolt (Frost) never '
    'locks it. The registry\'s 4 to 9 yd donut round him owns the hit (211056). Magma Wave 55916\'s SV 12227 on him '
    'for the bar.',
    icon=_ICON_MAGMA_WAVE, visual=ST_MAGMA_BAND, school=School.FIRE,
)

magma_hit_211056 = resolve_copy(
    211056, 'Magma Forged Band', School.FIRE, 'The band of magma burns everything near it, but not the closest ground.',
    f'{_SD}, SV4: the donut\'s hit: 30% (heroic 45%) of the reference row to everyone 4 to 9 yd from Stilgiss (safe '
    'hugging him or beyond 9 yd), the tank on its own row, 1 Weakened. Copy of the mod-boss-mechanics resolve spell '
    '(Fire).',
    icon=_ICON_MAGMA_WAVE,
)

# --- SV5 Wand of Eternal Light ---------------------------------------------------------------------------------------

wand_hit_211057 = resolve_copy(
    211057, 'Wand of Eternal Light', School.HOLY, 'The Wand of Eternal Light sears everything in its lines.',
    f'{_SD}, SV5: a line\'s hit: three 3 yd lines across the hall (chords 60 degrees apart), 2 s marker, 20% (heroic '
    '35%) of the reference row to everyone on one (once per line), the tank on its own row, 1 Weakened. Copy of the '
    'mod-boss-mechanics resolve spell (Holy). Holy Fire 15261\'s SV 3400 on every unit hit (the lines are the kit\'s '
    'white 3 yd markers; never Beam of Light SV 12479, VISUALS report).',
    icon=_ICON_HOLY_LIGHT, visual=ST_WAND_IMPACT,
)

# --- SV6 Black Blood of the Tormented --------------------------------------------------------------------------------

blood_hit_211058 = resolve_copy(
    211058, 'Black Blood of the Tormented', School.SHADOW, 'The Black Blood burns.',
    f'{_SD}, SV6: a pool\'s tick: a persistent 3 yd circle where a random player stood (2 s marker, then 30 s), 4% '
    '(heroic 6%) of the reference row a second to everyone inside, the tank on its own row, no Weakened. Copy of the '
    'mod-boss-mechanics resolve spell (Shadow). The pool\'s dark patch is 211065.',
    icon=_ICON_BLACK_BLOOD,
)

blood_heal_211059 = spell(
    id=211059, name='Black Blood of the Tormented', school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL_PCT, base_points=_BLOOD_HEAL - 1, implicit_target_a=_TARGET_UNIT_TARGET_ALLY,
                    potency_excluded=_SCRIPT_HEAL_PCT)],
    spell_icon_id=_ICON_BLACK_BLOOD,
    notes=f'{_SD}, SV6: Verek\'s heal while he stands in a pool: 2% of his maximum health each second (HEAL_PCT, '
          'BasePoints 1 + DieSides 1), cast on Verek by Stilgiss (triggered) once a second from the AI\'s own clock, '
          'not on Stilgiss (designer). Never on anyone but Verek. Unscaled by DD (custom id).',
    raw_overrides=kit_raw('Black Blood mends Verek.', instant=True, InterruptFlags=0, PreventionType=0,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

blood_look_211065 = spell(
    id=211065, name='Black Blood of the Tormented', school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=_BLOOD_LIFE_MS + 4000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=1)],
    spell_icon_id=_ICON_BLACK_BLOOD,
    notes=f'{_SD}, SV6: the pool\'s dark patch, a lasting STATE on the stalker standing in the pool (cast by the '
          'stalker on itself, triggered): the shipped Ascension shadow quad SV 90601 (4 yd; the kit\'s red 3 yd marker '
          'carries the exact edge; never the green Black Blood SV 8305, VISUALS report). The script despawns the '
          'stalker when the pool ends, so the aura\'s length is only a ceiling. No effect, no damage.',
    raw_overrides=kit_raw('', 'A pool of black blood.', CastingTimeIndex=1, InterruptFlags=0, PreventionType=0,
                          SpellVisualID_1=SHIPPED_SHADOW_POOL_4_STATE, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- SV7 Frost Nova --------------------------------------------------------------------------------------------------

nova_cast_211060 = cast_bar(
    211060, 'Frost Nova', _NOVA_CAST_MS, 'Warder Stilgiss gathers the cold.',
    f'{_SD}, SV7: the 1.5 s bar before the nova, started when 2 or more players are within 10 yd of him (15 s apart, '
    'the first no sooner than 8 s). DUMMY on the caster, not interruptible, ARCANE on purpose: a kick on Frostbolt '
    '(Frost) locks the school for the interrupt\'s length and a Frost bar of his would stop then (handoff section 3.5 '
    'rule 5). The registry\'s 10 yd circle on him owns the hit (211061).',
    icon=_ICON_FROST_NOVA, school=School.ARCANE,
)

nova_hit_211061 = resolve_copy(
    211061, 'Frost Nova', School.FROST, 'A ring of frost freezes everyone near Warder Stilgiss in place.',
    f'{_SD}, SV7: the nova\'s hit (the stock Frost Nova 12674 rescaled, its 8 s root cut to 2 s): 10% (heroic 14%) of '
    'the reference row to everyone within 10 yd of him, the tank on its own row, no Weakened (the root is the '
    'penalty), with the 2 s root rider (211062). Copy of the mod-boss-mechanics resolve spell (Frost). Frost '
    'Nova 12674\'s SV 17 on every unit hit.',
    icon=_ICON_FROST_NOVA, visual=VL_FROST_NOVA,
)

nova_root_211062 = spell(
    id=211062, name='Frost Nova', school=School.FROST, dispel=0, mechanic=_MECHANIC_ROOT,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=_NOVA_ROOT_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_ROOT, mechanic=_MECHANIC_ROOT,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_FROST_NOVA,
    notes=f'{_SD}, SV7: the nova\'s 2 s root (the stock Frost Nova roots 8 s and takes a Dispel Magic; 2 s is not '
          'worth a cure), applied by the registry as the nova\'s rider to everyone it hits. Not dispellable. '
          'AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('Rooted in place.', 'Rooted.', CastingTimeIndex=1, DefenseType=_DEFENSE_MAGIC,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- SV8 Frostbolt ---------------------------------------------------------------------------------------------------

frostbolt_211063 = spell(
    id=211063, name='Frostbolt', school=School.FROST, dispel=0, mechanic=0, cast_time_ms=_FROSTBOLT_CAST_MS,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=40.0,
    duration_ms=_FROSTBOLT_SLOW_MS,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=_FROSTBOLT_HIT[0] - 1, die_sides=1,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT),
             Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DECREASE_SPEED, base_points=-51,
                    die_sides=1, mechanic=_MECHANIC_SNARE, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_FROSTBOLT,
    notes=f'{_SD}, SV8: his stock Frostbolt 12675 as his own copy (never the stock id), cast by '
          'boss_warder_stilgiss_rework (not triggered, so the bar shows) at a random player in line of sight, 2.4 to '
          '3.8 s after the last one started. 3 s, 40 yd, Frost, 8% (heroic 10%) of the reference row (the tank on its '
          'own row; spell_dungeon_refflat_damage, hundredths in the effect, heroic in EffectMiscValueB_1) and the '
          'stock -50% movement for 4 s. Interruptible and silence-preventable (InterruptFlags 15, PreventionType '
          'silence; his immunity set 1972 holds no interrupt or silence): the descriptor\'s interrupt list, priority '
          '1 (a reward, heroic too). Ignores caster modifiers. The stock missile and impact (SV 13, 24 yd/s). '
          'AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('Hurls a frost bolt that damages and slows its target.', 'Movement slowed.',
                          InterruptFlags=_INTERRUPT_FLAGS_KICKABLE, PreventionType=_PREVENTION_SILENCE,
                          DefenseType=_DEFENSE_MAGIC, Speed=_FROSTBOLT_SPEED, Targets=_TARGET_FLAG_UNIT,
                          EffectMiscValueB_1=_FROSTBOLT_HIT[1], SpellVisualID_1=ST_FROSTBOLT,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(frostbolt_211063, _REFFLAT)

# --- SV9 Curse of Blood (Verek) --------------------------------------------------------------------------------------

curse_of_blood_211064 = spell(
    id=211064, name='Curse of Blood', school=School.SHADOW, dispel=_DISPEL_CURSE, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=20.0, duration_ms=_CURSE_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN,
                    base_points=_CURSE_PCT - 1, die_sides=1, misc_value=_SCHOOL_MASK_PHYSICAL,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_CURSE_OF_BLOOD,
    notes=f'{_SD}, SV9: Verek\'s Curse of Blood 15042 as his own copy, changed (the stock one is +1 flat physical '
          'damage taken, which does nothing): +10% physical damage taken for 30 s on his victim (the tank), cast by '
          'npc_verek_rework 3 to 5 s into the fight and every 30 to 45 s after (the stock cadence). A Curse: the '
          'dispel list, priority 1 (a reward). 20 yd, Shadow. Curse of Blood\'s SV 876 (the curse hands and the '
          'lasting curse state). AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('Increases physical damage taken by $s1%.', 'Physical damage taken increased by $s1%.',
                          CastingTimeIndex=1, DefenseType=_DEFENSE_MAGIC, Speed=60.0,
                          SpellVisualID_1=ST_CURSE_OF_BLOOD, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- The encounter's credit (F-1a) -----------------------------------------------------------------------------------

credit_211066 = spell(
    id=211066, name='Warder Stilgiss and Verek', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_GENERIC,
    notes=f'{_SD}: the encounter\'s credit (BlackrockDepthsRework.h kSpellStilgissVerekCredit). Never cast: once both '
          'Stilgiss and Verek are dead the instance calls UpdateEncounterState(ENCOUNTER_CREDIT_CAST_SPELL, 211066), '
          'and lfg dungeon_encounters row 233 (heroic 1061) names it (creditType 1). ObjectMgr::LoadInstanceEncounters '
          'only needs the spell to exist. No effect.',
    raw_overrides=kit_raw('', instant=True, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)
