"""
Blackrock Depths build WP-D13: Bael'Gar (9016; GO 301281 (Fallen Boulder, GODI 3711))
(.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D13; build spec docs/dungeons S2
1138-1183, BG1-BG6). WP-D13 owns this file; WP-S0 wrote the skeleton.

- 9016 Bael'Gar: bound to boss_baelgar_rework (modules/mod-dungeon-bosses src/BlackrockDepths/
  boss_baelgar_rework.cpp), SmartAI off (WP-S0's rev dropped his five rows; Summon Spawn of Bael'Gar 13895 is retired,
  the Spawn 9436 has no spawns and goes unused, so no boss-kit add and no creature_heroic entry), the build spec's
  normal health (HealthModifier 84.353 on the level 52 warrior class base 2,371 = 200,000), stun and Fire immunity
  (1973: the 1972 set plus the Fire school, section 7 #10), INSTANCE_BIND (flags_extra 1), DamageModifier the stock
  3.5 (the live 6 is a leftover). Heroic health (320,000) and the tier's melee are WP-H's
  (source/world/dungeons/blackrock_depths.py). Display 12162 (Magmus wears it too) is the stock one and stays.
- GO 301281 Fallen Boulder: generic (type 5, no click), display 3711 Lavarock01 (the fallback is 5736, one constant in
  BaelgarLogic.h kBoulderDisplay), declared in data/sql/updates/pending_db_world/rev_baelgar_blackrock_depths.sql with
  his four texts (9016 groups 0-3).

Spells (kSpellsBaelgar 211230-211259, BaelgarLogic.h names the same ids; looks from ._visuals, WP-V-1's BG_* picks,
every look unconfirmed until seen in game):

  211230  Magma Splash         BG1 the kept stock 13880 (rule 15: a copy in the slice): an instant Fire hit on the tank,
                               a 30 s Fire damage over time and -250 armor. 10% (heroic 15%) hit and 1.5% (heroic
                               2.5%) of the tank's row every 3 s through spell_dungeon_refflat_damage / _periodic
  211231  Rockfall             BG2 a circle's hit: 3 yd, 1.5 s, 15% / 25% + Weakened (resolve copy, Physical)
  211232  Falling Boulder      BG3 the impact's hit: 8 yd, 3 s, 40% / 60% (resolve copy, Physical)
  211233  Molten Furnace       BG4 the 5 s cast bar (not interruptible)
  211234  Molten Furnace       BG4 the wave's hit: 80% / 95% on everyone he sees (resolve copy, Fire, Heat Wave's look)
  211235  Fissure              BG6 the 2 s stomp bar (not interruptible)
  211236  Fissure              BG6 the crack's hit: 4 yd line, 25% / 40% + Weakened (resolve copy, Fire)
  211237  Fissure              BG6 the lava's tick: 6% a second while standing in a crack (resolve copy, Fire)
  211238  Rockfall             look: Rock Shower's dust at each circle as it lands
  211239  Falling Boulder      look: Boulder Impact's shake and sound where the Boulder lands
  211240  The Boulders Melt    look: Exploding Stone Impact at a Boulder's base (BG5)
  211241  Fissure              look: the burst where the crack opens
  211242  Fissure              look: a lava patch, an aura on a generic stalker 300796 every 6 yd along a crack
  211243-211259 spare.

Not wired: the falling Boulder's missile (BG_BOULDER_MISSILE, Boulder Volley from a stalker overhead). The Falling
Boulder follows its carrier for the whole 3 s, so there is no fixed target to launch at before it lands; the landing
look is Boulder Impact alone (report, designer question 5).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR1_NO_THREAT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
)
from lib.dsl.registry import creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    IMMUNITY_FIRE_GIANT,
    TARGET_UNIT_CASTER,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    BG_BOULDER_LAND,
    BG_BOULDER_MELT,
    BG_FISSURE_BURST,
    BG_FISSURE_LAVA,
    BG_MAGMA_SPLASH,
    BG_MOLTEN_FURNACE,
    BG_ROCKFALL,
)

_D13 = 'Blackrock Depths build WP-D13 (Bael\'Gar)'
_SCRIPT_REFFLAT = ('Blackrock Depths: a percent of reference health in hundredths, set by the kit\'s '
                   'spell_dungeon_refflat_damage / _periodic (DungeonKit::RefFlatOn)')

creature_template_columns(9016, **boss_columns(
    'boss_baelgar_rework', 84.353, damage_modifier=3.5, CreatureImmunitiesId=IMMUNITY_FIRE_GIANT,
))

# --- constants (BaelgarLogic.h; lib/test_blackrock_depths_baelgar.py pins each against the header) -------------------

MAGMA_HIT = (1000, 1500)        # kMagmaSplashHitPct 10 / 15 (hundredths)
MAGMA_TICK = (150, 250)         # kMagmaSplashTickPct 1.5 / 2.5 (hundredths)
MAGMA_TICK_MS = 3000            # kMagmaSplashTickMs
MAGMA_DOT_MS = 30000            # kMagmaSplashDotMs
MAGMA_ARMOR = -250              # kMagmaSplashArmor
FURNACE_CAST_MS = 5000          # kFurnaceCastMs
FISSURE_CAST_MS = 2000          # kFissureWarnMs

_AURA_MOD_RESISTANCE = 22       # SPELL_AURA_MOD_RESISTANCE (misc value 1 = the physical school: armor)
_TARGET_DEST_DEST = 87
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_FLAG_DEST_LOCATION = 0x40
_ATTR0_DO_NOT_DISPLAY = 0x00000080
_ATTR0_DO_NOT_LOG = 0x00000100
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_DEFENSE_MAGIC = 1

# Stock icons (Spell.dbc SpellIconID of the named spell)
_ICON_MAGMA_SPLASH = 31         # Magma Splash 13880
_ICON_HEAT_WAVE = 1197          # Heat Wave 35236
_ICON_ROCK = 132                # Cave In 36240 / Boulder Impact 46895 / Rock Shower 60919
_ICON_FISSURE = 66              # Fissure 49656

# --- BG1 Magma Splash ------------------------------------------------------------------------------------------------

magma_splash_211230 = spell(
    id=211230, name='Magma Splash', school=School.FIRE, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=MAGMA_DOT_MS,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=MAGMA_HIT[0] - 1, die_sides=1,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=MAGMA_TICK[0],
               die_sides=0, amplitude=MAGMA_TICK_MS, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
               potency_excluded=_SCRIPT_REFFLAT),
        Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_MOD_RESISTANCE, base_points=MAGMA_ARMOR, die_sides=0,
               misc_value=1, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
               potency_excluded='Magma Splash: a flat -250 armor, not a damage or heal value'),
    ],
    spell_icon_id=_ICON_MAGMA_SPLASH,
    notes=f'{_D13}, BG1: the stock Magma Splash 13880 (93-107 Fire, a 50 Fire DoT every 3 s for 30 s, -250 armor) '
          'kept and rescaled (rule 15: a copy in the slice, never the shared id). Bael\'Gar casts it (triggered) on '
          'his victim, the tank, 8 s after the pull and every 10-14 s: an instant Fire hit of 10% (heroic 15%: '
          'EffectMiscValueB) of the tank\'s row, then a 30 s Fire DoT of 1.5% (heroic 2.5%) every 3 s, and -250 armor '
          'for the 30 s. The spec leaves the numbers to "stock rescaled" (gap 8 / 36): these are this WP\'s defaults. '
          'A recast refreshes the aura. Both damage effects read their percent through spell_dungeon_refflat_damage '
          '/ _periodic (RefFlatOn: the tank\'s row on the tank). Not dispellable (stock), no mechanic. Always hits, '
          'ignores his modifiers. The Immolate state on the tank (SV 3221, BG_MAGMA_SPLASH). AuraInterruptFlags '
          'CHANGE_MAP; removed when the fight ends.',
    raw_overrides=kit_raw('Burns the target for Fire damage and more every 3 sec, and lowers its armor.',
                          'Burning for Fire damage every 3 sec. Armor reduced by $s3.', CastingTimeIndex=1,
                          EffectMiscValueB_1=MAGMA_HIT[1], EffectMiscValueB_2=MAGMA_TICK[1],
                          DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=BG_MAGMA_SPLASH,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(magma_splash_211230, 'spell_dungeon_refflat_damage', 'spell_dungeon_refflat_periodic')

# --- BG2 Rockfall, BG3 Falling Boulder -------------------------------------------------------------------------------

rockfall_211231 = resolve_copy(
    211231, 'Rockfall', School.NORMAL, 'Rocks crumble from the ceiling.',
    f'{_D13}, BG2 Rockfall: a 3 yd circle\'s hit, 1.5 s after its marker, five circles every 15 s (heroic 12 s), the '
    'first at 5 s: 15% (heroic 25%) of the reference row and 1 Weakened (registry tag 1). Three (heroic four) drop '
    'under distinct random players, the tank too (ruling 88), the rest on random floor spots off the cracks. Copy of '
    'the resolve spell 205001 (Physical).',
    icon=_ICON_ROCK,
)

falling_boulder_211232 = resolve_copy(
    211232, 'Falling Boulder', School.NORMAL, 'A boulder crashes down.',
    f'{_D13}, BG3 Falling Boulder: the impact\'s hit, 8 yd, 3 s after the marker starts to follow its carrier (a '
    'random player, the tank too; the carrier is never hit by their own marker), with each Rockfall: 40% (heroic '
    '60%) of the reference row, no Weakened (the spec\'s penalty cell is empty; registry tag 2). The Boulder '
    '(GO 301281) stays where it lands unless it lands on a crack. Copy of the resolve spell 205001 (Physical).',
    icon=_ICON_ROCK,
)

# --- BG4 Molten Furnace ----------------------------------------------------------------------------------------------

molten_furnace_cast_211233 = cast_bar(
    211233, 'Molten Furnace', FURNACE_CAST_MS, 'Bael\'Gar stokes the Molten Furnace. Get out of his sight.',
    f'{_D13}, BG4 Molten Furnace: the 5 s bar players read while the wave is coming (emote line 0, boss emote). Not '
    'interruptible: the registry\'s Hide mechanic (tag 16) lands the wave at the cast\'s end whatever happens to the '
    'bar. Fire. No look of its own: the breath plays with the wave (211234).',
    icon=_ICON_HEAT_WAVE, school=School.FIRE,
)

molten_furnace_211234 = resolve_copy(
    211234, 'Molten Furnace', School.FIRE, 'A wave of heat. Only a boulder\'s shadow saves you.',
    f'{_D13}, BG4 Molten Furnace: the wave, at the cast\'s end, on every player within 60 yd whom Bael\'Gar can see '
    '(the BM Hide kind: a real IsWithinLOSInMap from him, so a Fallen Boulder\'s collision model blocks it): 80% '
    '(heroic 95%) of the reference row, no Weakened ("a hit over 50% is its own penalty"); the tank too (ruling 88). '
    'Copy of the resolve spell 205001 (Fire). Heat Wave 35236\'s look (SV 3119: a breath from his mouth and a '
    'burning state on each target).',
    icon=_ICON_HEAT_WAVE, visual=BG_MOLTEN_FURNACE,
)

# --- BG6 Fissure ----------------------------------------------------------------------------------------------------

fissure_cast_211235 = cast_bar(
    211235, 'Fissure', FISSURE_CAST_MS, 'Bael\'Gar slams the ground and the floor cracks open.',
    f'{_D13}, BG6 Fissure: the 2 s stomp bar (emote line 2) while the line marker shows the crack\'s path. Not '
    'interruptible (the registry lands the hit whatever happens to the bar). Fire.',
    icon=_ICON_FISSURE, school=School.FIRE,
)

fissure_211236 = resolve_copy(
    211236, 'Fissure', School.FIRE, 'The floor cracks open.',
    f'{_D13}, BG6 Fissure: the crack\'s hit, a 4 yd line about 40 yd from him in a random direction (clipped to the '
    'floor and the leash circle), 2 s after the stomp starts: 25% (heroic 40%) of the reference row and 1 Weakened '
    '(registry tag 3). Copy of the resolve spell 205001 (Fire). The crack then stays as a lava line for the fight '
    '(211237).',
    icon=_ICON_FISSURE,
)

fissure_lava_211237 = resolve_copy(
    211237, 'Fissure', School.FIRE, 'Lava.',
    f'{_D13}, BG6 Fissure: the lasting lava, a persistent 4 yd line on the crack, a tick a second for the rest of the '
    'fight: 6% of the reference row each (no Weakened: a lingering zone never applies it; registry tag 4). Copy of '
    'the resolve spell 205001 (Fire).',
    icon=_ICON_FISSURE,
)

# --- looks -----------------------------------------------------------------------------------------------------------


def _look_at_point(spell_id: int, name: str, visual: int, notes: str, icon: int = _ICON_ROCK):
    """A look-only spell cast at a point (a DUMMY aimed at a destination; DO_NOT_DISPLAY | DO_NOT_LOG), the boss's own
    cast, triggered (the Fineous pillar look shape)."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, Targets=_TARGET_FLAG_DEST_LOCATION,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


rockfall_look_211238 = _look_at_point(
    211238, 'Rockfall', BG_ROCKFALL,
    f'{_D13}, BG2: the dust of a landing circle. Bael\'Gar casts it (triggered) at each circle\'s spot as it resolves: '
    'Rock Shower 60919\'s SpellVisual 12855 (a dust plume; never Cave In\'s faint SV 8455). Look only.',
)

boulder_land_look_211239 = _look_at_point(
    211239, 'Falling Boulder', BG_BOULDER_LAND,
    f'{_D13}, BG3: the Boulder lands. Bael\'Gar casts it (triggered) at the impact as the circle resolves, whether the '
    'Boulder stands or falls into a crack: Boulder Impact 46895\'s SpellVisual 12714 (shake and sound). Look only.',
)

boulder_melt_look_211240 = _look_at_point(
    211240, 'The Boulders Melt', BG_BOULDER_MELT,
    f'{_D13}, BG5: a Boulder melts when the Furnace\'s wave ends. Bael\'Gar casts it (triggered) at the Boulder\'s '
    'base as the object goes: Exploding Stone Impact\'s SpellVisual 8097. Look only.',
)

fissure_burst_look_211241 = _look_at_point(
    211241, 'Fissure', BG_FISSURE_BURST,
    f'{_D13}, BG6: the burst where the crack opens. Bael\'Gar casts it (triggered) at his feet as the crack resolves: '
    'Fissure 49656\'s SpellVisual 10917 (one blob at the start, not a line). Look only.',
    icon=_ICON_FISSURE,
)

fissure_lava_look_211242 = spell(
    id=211242, name='Fissure', school=School.FIRE, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_FISSURE,
    notes=f'{_D13}, BG6: the lava\'s look, a DUMMY aura a generic stalker (300796) casts on itself (triggered), one '
          'every 6 yd along the crack when it opens: the shipped 4 yd lava pool state (SV 90606, Blackrock Spire\'s '
          'ladder), under the registry\'s 4 yd line marker. No effect; the stalkers despawn with the fight. Fallback: '
          'a wider rung of the ladder (SHIPPED_LAVA_POOL) at a wider spacing.',
    raw_overrides=kit_raw('Lava.', 'Lava.', CastingTimeIndex=1, SpellVisualID_1=BG_FISSURE_LAVA,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)
