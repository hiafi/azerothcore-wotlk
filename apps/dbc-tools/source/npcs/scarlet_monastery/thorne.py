"""
Scarlet Monastery build WP-D12: Brother Aldous Thorne, the Gardener (Thorne 300946, Seedling 300947, Briar 300948,
Blessed Bramble 300949) (.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.5 row D12,
s7 #32 A; build spec docs/dungeons/scarlet-monastery-4-cathedral.md "Brother Aldous Thorne, the Gardener", GD1-GD3).
WP-D12 owns this file; WP-S0 wrote the skeleton. His texts, his spawn, his scythe (creature_equip_template) and the
moved Centurion are data/sql/updates/pending_db_world/rev_thorne_scarlet_monastery.sql.

Wave 2: the four creatures and the spells are declared now, so FD-SM's credit_creature(300946) (encounter 1080) has a
template and WP-H's heroic overrides (Thorne 300k, the bramble 8k; heroic entries THORNE_HEROIC / BRAMBLE_HEROIC once
set) apply; only the ScriptNames wait for the wave switch (BIND_WAVE_2, flipped with kWave2Bound by W2-SETUP). While
wave 2 is unbound he is a plain melee elite in the garden (ScriptName '': the AI is not registered, so naming it would
log "not assigned" at boot).

- 300946 Brother Aldous Thorne <Keeper of the Blessed Grain>: a NEW boss, boss_gardener_rework (modules/
  mod-dungeon-bosses src/ScarletMonastery/boss_gardener_rework.cpp). Level 40 paladin, Scarlet Crusade (faction 67),
  elite, the build spec's normal health (60k = HealthModifier 48.940 on the level 40 paladin base 1,226),
  DamageModifier 2.4 (Doan's and Loksey's: a teaching boss, his sweep is the heavy hit), stun immunity 1972,
  INSTANCE_BIND (the encounter row's credit creature), display 2502 (the male Scarlet Chaplain: V's pick, s7 #34; the
  doc's 2501 is female), Soul Harvester (item 20536) in hand by the SQL rev's equipment, SmartAI off, lootid 300946
  (L-2's lists). Heroic health (300k) and the tier's melee are WP-H's overrides.
- 300947 Seedling (GD1): not selectable, cannot be harmed, never fights (KIT_HELPER), the Thornling's display 14392 at
  scale 0.5, grown to 1.0 by the script as it buds. Summoned at each planted seed; runs on its normal entry on heroic
  (no heroic template: WP-H's no-heroic list).
- 300948 Briar (GD1d, normal): the 4 yd patch's anchor, an invisible stalker (KIT_HELPER, display 11686) wearing the
  thorns look. Normal only; no heroic template.
- 300949 Blessed Bramble (GD1e, heroic): a rooted add that never swings (DamageModifier 0, npc_sm_blessed_bramble keeps
  it passive and rooted), Barbed Lasher's display 12347 at scale 0.7, elemental like the lashers, NO immunity set (it
  can be stunned and crowd controlled: nothing stops its pollen; taunt does nothing to a unit that never swings).
  Normal row level 40 (never summoned on normal); WP-H's heroic copy is 8k at 60 (in `extra=`; section 10 sizing C).

Spells (kSpellsThorne 213060-213099; ThorneLogic.h names the same ids; looks from ._visuals, WP-V's GD_* picks, every
look unconfirmed until seen in game). His damage is a percent of the reference row (the tank row on the tank): the
registry lands the sweep on others, the blooms, the briars and Holy Water through resolve copies; the sweep's tank hit
binds the kit's spell_dungeon_refflat_damage (the percent in hundredths in the effect, EffectMiscValueB on heroic); the
pollen is a custom value the AI sets per player (DungeonKit::RefFlatOn with Thorne as the owner):

  213060  Blessed Grain        GD1 the carrier's 5 s debuff (Seed Pod 48082's SV 10713); the seed is planted as it ends
  213061  Blessed Grain        GD1 the seed taking root and budding, a look on the seedling (SV 10713)
  213062  Prune                GD1a the sweep on others: resolve copy, Physical, 30% / 45% and Weakened
  213063  Prune                GD1a the sweep on the tank: 15% / 25% of the tank row (kit percent script)
  213064  Prune                GD1a the scythe's sweep, a look on him (Cleave 15496's SV 219)
  213065  Bloom                GD1c the burst: resolve copy, Holy, 20% / 30% and Weakened
  213066  Bloom                GD1c the bloom at the seedling (Wild Growth 48438's SV 11568, a look at the point)
  213067  Briar                GD1d a briar's tick (normal): resolve copy, Nature, 10% a second
  213068  Briar                GD1d / GD1e the 50% slow, the briar ticks' rider
  213069  Briar                GD1d / GD1e the thorns, an aura on the briar and the bramble (Entangling Roots' SV 38)
  213070  Briar                GD1e a bramble's briar tick (heroic): resolve copy, Nature, 15% a second
  213071  Blessed Pollen       GD1f a pulse on a player (heroic): Holy, a custom value (1% rising to 20% of the row)
  213072  Blessed Pollen       GD1f the pollen's glow, an aura on the bramble (the 4 yd gold holy zone 90509: V's
                               stand-in, no gold pollen exists; Pollen 45610's SV 8529 is violet)
  213073  Holy Water           GD2 the 2.5 s bar (Holy, not interruptible; Sprinkle Holy Water 57806's SV 12483)
  213074  Holy Water           GD2 the splash: resolve copy, Holy, 30% / 45% and Weakened
  213075  Blessed Ground       GD2a the ground's look, an aura on a stalker (the Strat 8 yd holy zone 90512; NEVER
                               Consecration's 5600: the Last Stand's look)
  213076  Blessed Ground       GD2a his heal while he stands in it: 1% of his health a second (a custom value)
  213077  Bless the Harvest    GD3 the 2.5 s interruptible cast (heroic; Nature: the Holy Water bar is Holy; Bounty of
                               the Harvest 24006's SV 563)
  213078-213099 spare.
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
    standing_in_it,
)
from lib.dsl.registry import creature_model, creature_template, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_2,
    FACTION_SCARLET_CRUSADE,
    IMMUNITY_BOSS_STUN,
    KIT_CREATURE,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    BRAMBLE_SCALE,
    DISPLAY_BLESSED_BRAMBLE,
    DISPLAY_INVISIBLE_STALKER,
    DISPLAY_SEEDLING,
    DISPLAY_THORNE,
    GD_BLESSED_GROUND,
    GD_BLESS_CAST,
    GD_BLOOM,
    GD_BRIAR,
    GD_HOLY_WATER,
    GD_POLLEN_ALT,
    GD_SEED,
    GD_SWEEP,
    SEEDLING_SCALE_RANGE,
)

_D12 = 'Scarlet Monastery build WP-D12 (Brother Aldous Thorne)'

# --- the creatures ---------------------------------------------------------------------------------------------------

# The heroic entries (difficulty_entry_1 = the id in source/world/heroic_ids.lock). WP-H's mint table names 310479 for
# Thorne and 310480 for the bramble (wave 2's 4th and 5th units after the 18 of wave 1); every lower kit unit is
# declared, so the run mints exactly those ids (W2-SETUP's reconcile; lib/test_scarlet_monastery_heroic.py
# KIT_HEROIC_ID names the same ids).
THORNE_HEROIC_PLANNED = 310479
THORNE_HEROIC = THORNE_HEROIC_PLANNED
BRAMBLE_HEROIC_PLANNED = 310480
BRAMBLE_HEROIC = BRAMBLE_HEROIC_PLANNED

THORNE = 300946
SEEDLING = 300947
BRIAR = 300948
BLESSED_BRAMBLE = 300949

SCRIPT_NAME = 'boss_gardener_rework'
BRAMBLE_SCRIPT_NAME = 'npc_sm_blessed_bramble'

_RANK_NORMAL = 0
_RANK_ELITE = 1
_CLASS_WARRIOR = 1
_CLASS_PALADIN = 2
_TYPE_ELEMENTAL = 4

# The build spec's normal health at 5 players (S0's table): 60k = 48.940 x 1,226 (the level 40 paladin).
# creature_classlevelstats basehp0, live 2026-11-20.
THORNE_HEALTH_MODIFIER = 48.940
THORNE_DAMAGE_MODIFIER = 2.4


def _heroic_entry(columns: dict, heroic_entry) -> dict:
    """`columns` with difficulty_entry_1 when it is set (a declared full row must carry it)."""
    if heroic_entry:
        return {**columns, 'difficulty_entry_1': heroic_entry}
    return columns


brother_aldous_thorne_300946 = creature_template(300946, 'Brother Aldous Thorne', **_heroic_entry({
    **KIT_CREATURE, 'subname': 'Keeper of the Blessed Grain', 'minlevel': 40, 'maxlevel': 40, 'rank': _RANK_ELITE,
    'unit_class': _CLASS_PALADIN, 'faction': FACTION_SCARLET_CRUSADE, 'type': 7, 'exp': 0,
    'HealthModifier': THORNE_HEALTH_MODIFIER, 'DamageModifier': THORNE_DAMAGE_MODIFIER, 'ManaModifier': 1.0,
    'ExperienceModifier': 2.0, 'BaseAttackTime': 2000, 'speed_run': 1.14286, 'detection_range': 20.0,
    'CreatureImmunitiesId': IMMUNITY_BOSS_STUN, 'lootid': 300946, 'mingold': 400, 'maxgold': 1200,
    'flags_extra': 1, 'ScriptName': SCRIPT_NAME if BIND_WAVE_2 else '', 'AIName': '',
}, THORNE_HEROIC))
creature_model(300946, display_id=DISPLAY_THORNE)

seedling_300947 = creature_template(300947, 'Seedling', **{
    **KIT_HELPER, 'faction': FACTION_SCARLET_CRUSADE, 'minlevel': 40, 'maxlevel': 40, 'rank': _RANK_NORMAL,
    'unit_class': _CLASS_WARRIOR, 'type': _TYPE_ELEMENTAL,
    'unit_flags': 0x2 | 0x100 | 0x200 | 0x02000000, 'ScriptName': '', 'AIName': '',
})
creature_model(300947, display_id=DISPLAY_SEEDLING, scale=SEEDLING_SCALE_RANGE[0])

briar_300948 = creature_template(300948, 'Briar', **{
    **KIT_HELPER, 'faction': FACTION_SCARLET_CRUSADE, 'minlevel': 40, 'maxlevel': 40, 'rank': _RANK_NORMAL,
    'unit_class': _CLASS_WARRIOR,
    'unit_flags': 0x2 | 0x100 | 0x200 | 0x02000000, 'ScriptName': '', 'AIName': '',
})
creature_model(300948, display_id=DISPLAY_INVISIBLE_STALKER)

blessed_bramble_300949 = creature_template(300949, 'Blessed Bramble', **_heroic_entry({
    **KIT_CREATURE, 'minlevel': 40, 'maxlevel': 40, 'rank': _RANK_NORMAL, 'unit_class': _CLASS_WARRIOR,
    'faction': FACTION_SCARLET_CRUSADE, 'type': _TYPE_ELEMENTAL, 'HealthModifier': 2.0, 'DamageModifier': 0.0,
    'detection_range': 0.0, 'lootid': 0, 'CreatureImmunitiesId': 0,
    'flags_extra': 0x40, 'ScriptName': BRAMBLE_SCRIPT_NAME if BIND_WAVE_2 else '', 'AIName': '',
}, BRAMBLE_HEROIC))
creature_model(300949, display_id=DISPLAY_BLESSED_BRAMBLE, scale=BRAMBLE_SCALE)

# --- constants (ThorneLogic.h; lib/test_scarlet_monastery_thorne.py pins each against the header) ---------------------

HOLY_WATER_CAST_MS = 2500           # kHolyWaterCastMs
BLESS_CAST_MS = 2500                # kBlessCastMs
SOW_DEBUFF_MS = 5000                # kSowDebuffMs
PRUNE_TANK_PCT = (1500, 2500)       # kPruneTankPct 15 / 25 (hundredths: normal in the effect, heroic in MiscValueB)
BRIAR_SLOW_PCT = 50                 # kBriarSlowPct

_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40
_DEFENSE_MAGIC = 1
_DEFENSE_MELEE = 2
_PREVENTION_SILENCE = 1
_SPELL_INTERRUPT_FLAGS_KICK = 15
_ATTR0_DO_NOT_DISPLAY = 0x00000080
_ATTR0_DO_NOT_LOG = 0x00000100

_SCRIPT_REFFLAT = ('Scarlet Monastery D12: a percent of reference health in hundredths, set by the kit\'s '
                   'spell_dungeon_refflat_damage (DungeonKit::RefFlatOn: the tank row on the tank)')
_SCRIPT_POLLEN = ('Scarlet Monastery D12: a percent of reference health set at the cast (CastCustomSpell with '
                  'DungeonKit::RefFlatOn(Thorne, player, 1-20%))')
_SCRIPT_HEAL = ('Scarlet Monastery D12: 1% of his maximum health set at the cast (CastCustomSpell; ThorneLogic.h '
                'BlessedGroundHeal)')

# Stock icons (Spell.dbc SpellIconID of the named spell, read from the stock client 2026-11-20)
_ICON_SEED_POD = 1634                   # Seed Pod 48082
_ICON_CLEAVE = 277                      # Cleave 15496
_ICON_WILD_GROWTH = 2864                # Wild Growth 48438
_ICON_ENTANGLING_ROOTS = 20             # Entangling Roots 339
_ICON_THORNS = 53                       # Thorns 467
_ICON_POLLEN = 2013                     # Pollen 45610
_ICON_HOLY_WATER = 2820                 # Sprinkle Holy Water 57806
_ICON_CONSECRATION = 51                 # Consecration 20116
_ICON_BOUNTY = 1512                     # Bounty of the Harvest 24006


def _look_at_point(spell_id: int, name: str, visual: int, notes: str, icon: int):
    """A look-only spell cast at a point (a DUMMY aimed at a destination; DO_NOT_DISPLAY | DO_NOT_LOG), triggered (the
    Kell / Crell look shape)."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, Targets=_TARGET_FLAG_DEST_LOCATION,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


def _self_look(spell_id: int, name: str, visual: int, desc: str, notes: str, icon: int, school: School):
    """A lasting look: a DUMMY aura (no duration) the unit casts on itself (triggered); it goes with the unit (or the
    script removes it). No effect, not dispellable."""
    return spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, desc, CastingTimeIndex=1, SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- GD1 Sow ----------------------------------------------------------------------------------------------------------

blessed_grain_213060 = spell(
    id=213060, name='Blessed Grain', school=School.NATURE, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=SOW_DEBUFF_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_SEED_POD,
    notes=f'{_D12}, GD1 Sow: the carrier\'s debuff, cast by Thorne (triggered) on 2 (heroic 3) random players, '
          'never the tank (F-4b), at 6 s and every 20 s. 5 s; as it ends the script plants the seed where the carrier '
          'stands '
          '(the furrow 5 yd ahead of him is the registry Spot, tag 1). A clock only: no effect of its own, not '
          'dispellable (the boss data has no dispel list). Seed Pod 48082\'s SpellVisual 10713 (`DruidMorph` impact) '
          'on landing.',
    raw_overrides=kit_raw('Blessed grain to sow.',
                          'Carrying blessed grain. When it ends the seed is planted where you stand: plant it in the '
                          'furrow, then step out before the sweep.', CastingTimeIndex=1, SpellVisualID_1=GD_SEED,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

plant_look_213061 = self_visual(
    213061, 'Blessed Grain', GD_SEED,
    f'{_D12}, GD1: the seed taking root (as the seedling appears) and the bud forming (half its time), cast by the '
    'seedling on itself (triggered): Seed Pod 48082\'s SpellVisual 10713. Look only (the sprout and bud themselves are '
    'the Thornling model growing 0.5 -> 1.0).',
    icon=_ICON_SEED_POD, school=School.NATURE,
)

# --- GD1a Prune -------------------------------------------------------------------------------------------------------

prune_213062 = resolve_copy(
    213062, 'Prune', School.NORMAL, 'The scythe sweeps the furrow.',
    f'{_D12}, GD1a Prune: the sweep on others, a registry Frontal (120 degrees, 8 yd ahead of him, a 2 s wind-up with '
    'the cone marker, the tank exempt) every 10 s from 5 s: 30% (heroic 45%) of the reference row and 1 Weakened '
    '(registry tag 11). Every seedling inside is cut (GD1b, the script). Copy of the mod-boss-mechanics resolve spell '
    '205001 (Physical).',
    icon=_ICON_CLEAVE,
)

prune_tank_213063 = spell(
    id=213063, name='Prune', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_ACTIVE_DEFENSE,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=PRUNE_TANK_PCT[0] - 1, die_sides=1,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_CLEAVE,
    notes=f'{_D12}, GD1a: the sweep on the tank as the Frontal lands (his victim inside the cone): 15% (heroic 25%: '
          'EffectMiscValueB) of the tank\'s row, Physical, instant, never missed (always hits, no active defense, '
          'cannot crit) and ignoring his modifiers. Tank work: no Weakened. Binds the kit\'s '
          'spell_dungeon_refflat_damage. Cleave 15496\'s SV 219.',
    raw_overrides=kit_raw('The scythe sweeps the furrow.', instant=True, EffectMiscValueB_1=PRUNE_TANK_PCT[1],
                          DefenseType=_DEFENSE_MELEE, SpellVisualID_1=GD_SWEEP,
                          AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(prune_tank_213063, 'spell_dungeon_refflat_damage')

prune_look_213064 = self_visual(
    213064, 'Prune', GD_SWEEP,
    f'{_D12}, GD1a: the scythe\'s sweep, cast by Thorne on himself (triggered) as the Frontal lands (Cleave 15496\'s '
    'SpellVisual 219 on the Soul Harvester: the weapon model is unconfirmed, gap 17). Look only.',
    icon=_ICON_CLEAVE,
)

# --- GD1c Bloom, GD1d Briar, GD1e Blessed Bramble, GD1f Blessed Pollen ------------------------------------------------

bloom_213065 = resolve_copy(
    213065, 'Bloom', School.HOLY, 'Holy thorns burst from the untended seed.',
    f'{_D12}, GD1c Bloom: a seedling no sweep cut blooms 15 s (heroic 10 s) after it was planted: a 6 yd circle at it, '
    'a 2 s marker as the bud opens: 20% (heroic 30%) of the reference row and 1 Weakened, the tank row on the tank '
    '(registry tag 13). Then a briar (normal) or a Blessed Bramble (heroic). Copy of the resolve spell 205001 (Holy).',
    icon=_ICON_WILD_GROWTH,
)

bloom_look_213066 = _look_at_point(
    213066, 'Bloom', GD_BLOOM,
    f'{_D12}, GD1c: the bloom, cast by Thorne at the seedling\'s spot (triggered) as it bursts: Wild Growth 48438\'s '
    'SpellVisual 11568 (look unconfirmed, gap 17). Look only.',
    icon=_ICON_WILD_GROWTH,
)

briar_213067 = resolve_copy(
    213067, 'Briar', School.NATURE, 'Holy thorns.',
    f'{_D12}, GD1d Briar (normal): a briar\'s tick, a persistent 4 yd Zone where a seedling bloomed, one tick a second '
    'for the rest of the fight (at most six; a seventh withers the oldest): 10% of the reference row, the tank row on '
    'the tank, and the 50% slow (213068) as its rider (registry tag 14). Lingering: no Weakened. Copy of the resolve '
    'spell 205001 (Nature).',
    icon=_ICON_THORNS,
)

briar_slow_213068 = standing_in_it(
    213068,
    f'{_D12}, GD1d / GD1e: the briar\'s slow, the rider of every briar tick (normal briars and the heroic brambles\' '
    'briars): movement -50% for 2 s, refreshed by each tick, so it ends soon after the player steps out. Not loss of '
    'control (the build spec\'s approval check). The kit\'s Standing in It shape at 50%.',
    name='Briar', slow_pct=BRIAR_SLOW_PCT, desc='Thorns slow your movement. Lasts $d.',
    aura_desc='Thorns: movement slowed by 50%.',
)

briar_look_213069 = _self_look(
    213069, 'Briar', GD_BRIAR, 'Holy thorns.',
    f'{_D12}, GD1d / GD1e: the thorns, a DUMMY aura the briar stalker (300948) and the Blessed Bramble (300949) cast '
    'on themselves: Entangling Roots 339\'s lasting SpellVisual 38 (`EntanglingRoots_State`; Thorns\' SV 201 is the '
    'alternative). Its size against the 4 / 5 yd ring is unmeasured: the registry\'s ring is the exact edge.',
    icon=_ICON_ENTANGLING_ROOTS, school=School.NATURE,
)

bramble_briar_213070 = resolve_copy(
    213070, 'Briar', School.NATURE, 'The bramble\'s thorns.',
    f'{_D12}, GD1e Blessed Bramble (heroic): its briar\'s tick, a persistent 5 yd Zone round the rooted bramble, one '
    'tick a second until it dies: 15% of the reference row, the tank row on the tank, and the 50% slow (213068) as its '
    'rider (registry tag 15). Lingering: no Weakened. Copy of the resolve spell 205001 (Nature).',
    icon=_ICON_THORNS,
)

pollen_213071 = spell(
    id=213071, name='Blessed Pollen', school=School.HOLY, dispel=0, mechanic=0, attributes=ATTR0_NO_ACTIVE_DEFENSE,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_POLLEN)],
    spell_icon_id=_ICON_POLLEN,
    notes=f'{_D12}, GD1f Blessed Pollen (heroic): every 2 s from 2 s after a bramble grows, cast by the bramble '
          '(triggered) on every player of the fight: 1% of the reference row on the first pulse, 1% more each pulse, '
          'at most 20% (the 20th pulse, 40 s); a custom value Thorne\'s AI sets (DungeonKit::RefFlatOn with him as the '
          'owner). Never missed, cannot crit, ignores the bramble\'s modifiers, no threat. Group damage: no Weakened. '
          'Answered by killing the bramble. A stun or crowd control on the bramble stops nothing (a triggered cast).',
    raw_overrides=kit_raw('Blessed pollen burns the unclean.', instant=True, DefenseType=_DEFENSE_MAGIC,
                          AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

pollen_look_213072 = _self_look(
    213072, 'Blessed Pollen', GD_POLLEN_ALT, 'Blessed pollen drifts from the bramble.',
    f'{_D12}, GD1f: the pollen\'s glow, a DUMMY aura the Blessed Bramble casts on itself as it grows: the shipped 4 yd '
    'gold holy zone 90509 (V\'s stand-in: no gold pollen model exists; Pollen 45610\'s SV 8529 is violet arcane, VR '
    'RISKY). Look only.',
    icon=_ICON_POLLEN, school=School.HOLY,
)

# --- GD2 Holy Water, GD2a Blessed ground ------------------------------------------------------------------------------

holy_water_cast_213073 = cast_bar(
    213073, 'Holy Water', HOLY_WATER_CAST_MS, 'Brother Aldous Thorne raises the aspergillum.',
    f'{_D12}, GD2 Holy Water: the 2.5 s bar at 17 s and every 20 s, while the 10 yd (heroic 12 yd) ring round him is '
    'marked; he stands still and keeps his facing. Not interruptible: the registry lands the splash whatever happens '
    'to the bar. Holy: Bless the Harvest (Nature, heroic) is the interruptible cast, so a kick on it never locks this '
    'bar (rule 5). Sprinkle Holy Water 57806\'s SpellVisual 12483.',
    icon=_ICON_HOLY_WATER, visual=GD_HOLY_WATER, school=School.HOLY,
)

holy_water_213074 = resolve_copy(
    213074, 'Holy Water', School.HOLY, 'Holy water splashes the ground around him.',
    f'{_D12}, GD2 Holy Water: the splash, a 10 yd (heroic 12 yd) circle round where he stands as the bar ends: 30% '
    '(heroic 45%) of the reference row and 1 Weakened, the tank row on the tank (registry tag 2). Step out, then '
    'come back. Copy of the resolve spell 205001 (Holy).',
    icon=_ICON_HOLY_WATER,
)

blessed_ground_look_213075 = _self_look(
    213075, 'Blessed Ground', GD_BLESSED_GROUND, 'Blessed ground.',
    f'{_D12}, GD2a Blessed ground (heroic): the ground\'s look for its 8 s, a DUMMY aura on the wave 2 stalker '
    '(300958) at his Holy Water spot: the shipped Strat 8 yd holy zone 90512 (NEVER Consecration\'s SV 5600, the Last '
    'Stand\'s look). The registry\'s zone (the tank only, no damage, tag 21) is the exact edge.',
    icon=_ICON_CONSECRATION, school=School.HOLY,
)

blessed_ground_heal_213076 = spell(
    id=213076, name='Blessed Ground', school=School.HOLY, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL, base_points=0, die_sides=0, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded=_SCRIPT_HEAL)],
    spell_icon_id=_ICON_CONSECRATION,
    notes=f'{_D12}, GD2a Blessed ground (heroic): every second of its 8 s that he stands within 8 yd of where he cast '
          'Holy Water he heals 1% of his maximum health (3,000 on heroic). Cast triggered on himself with base point 0 '
          'set from the script. Ignores caster modifiers; healing-reduction effects on him (Mortal Strike, Wound '
          'Poison) still count. The tank drags him off it.',
    raw_overrides=kit_raw('The blessed ground mends him.', instant=True, InterruptFlags=0, PreventionType=0,
                          AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- GD3 Bless the Harvest (heroic) -----------------------------------------------------------------------------------

bless_the_harvest_213077 = spell(
    id=213077, name='Bless the Harvest', school=School.NATURE, dispel=0, mechanic=0, attributes=0,
    cast_time_ms=BLESS_CAST_MS, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_BOUNTY,
    notes=f'{_D12}, GD3 Bless the Harvest (heroic): a 2.5 s cast at 9 s and every 20 s (yell line 2), ending just '
          'after the seeds are planted: an expected interrupt. NOT triggered, so the bar shows and a kick stops it: '
          'InterruptFlags 15 and PreventionType 1 (a silence); his immunity set 1972 holds no INTERRUPT or SILENCE. No '
          'effect of its own: the script reads the outcome (OnSpellFailed: nothing; OnSpellCast: every standing '
          'seedling blooms at once, its 2 s marker from then). On the bots\' interrupt list (priority 3). Nature: the '
          'Holy Water bar is Holy, so a kick on this never locks it. Bounty of the Harvest 24006\'s SpellVisual 563 '
          '(look unconfirmed, gap 17).',
    raw_overrides=kit_raw('Thorne blesses the seeds in the ground. Interrupt him or they bloom at once.',
                          InterruptFlags=_SPELL_INTERRUPT_FLAGS_KICK, PreventionType=_PREVENTION_SILENCE,
                          SpellVisualID_1=GD_BLESS_CAST, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
