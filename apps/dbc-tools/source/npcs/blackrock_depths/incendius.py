"""
Blackrock Depths build WP-D11: Lord Incendius (9017; Ember of Incendius 300794), normal and heroic
(.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.4 / s3.5 row D11, s3.6, s3.8, s3.10, s7 #14
A; build spec docs/dungeons/blackrock-depths-2-shadowforge-city.md "Lord Incendius" IN1-IN8). WP-D11 owns this file
(its spells: kSpellsIncendius 211140-211179 of modules/mod-dungeon-bosses src/BlackrockDepths/BlackrockDepthsRework.h
only; IncendiusLogic.h names the same ids; its creature: 300794). The engine side is
src/BlackrockDepths/boss_lord_incendius_rework.cpp; his texts are
data/sql/updates/pending_db_world/rev_incendius_blackrock_depths.sql. The hard mode (Lord of the Lake) is WP-D12's
incendius_hard_mode.py.

- 9017 Lord Incendius: boss_lord_incendius_rework (SmartAI off: the S0 SQL rev drops his five stock rows), the build
  spec's normal health (100k first life: HealthModifier 40.766 on the level 53 warrior class base 2,453), the fire
  giants' immunity set 1973 (1972 + Fire school, s7 #10: stun immune, not interrupt immune), INSTANCE_BIND (flags_extra
  1), DamageModifier 3.5 (the stock base value; the live 5 is a leftover). Heroic 160k is WP-H's override
  (source/world/dungeons/blackrock_depths.py). His patrol (path 477330) and his loot are the stock rows'.
- 300794 Ember of Incendius (IN6): a boss-kit add, a fire elemental (type 4, faction 91 like him), level 53 elite
  warrior class, 6,000 health (HealthModifier 2.4459 on 2,453), no melee worth the name (DamageModifier 1.0: it never
  attacks, it rolls), no loot, no XP, no immunities (slows, roots and stuns hold it back: a reward), the fire elemental
  display 1405 (V-1's DISPLAY_EMBER_OF_INCENDIUS). npc_brd_ember_of_incendius. Heroic 9,000 is WP-H's `extra=`
  (difficulty_entry_1 310405, STAGE-H-REPORT section 3).

Spells. The registry hits (Fire Storm's ticks, Magma Fist, Lava Surge) deal their damage through dungeon copies of the
mod-boss-mechanics resolve spell (Fire). Fiery Burst is a percent of the reference row on the kit's generic script
(spell_dungeon_refflat_damage: the hundredths in the effect, the heroic ones in EffectMiscValueB). The Curse is a copy
of the stock one with the new effect. The rest are looks:

  211140  Curse of the Elemental Lord  IN1 +10% Fire damage taken, everyone within 45 yd, 60 s, Curse (copy of 26977)
  211141  Fiery Burst                  IN2 1.5 s, interruptible, everyone within 10 yd of his victim, 12% / 15% Fire
  211142  Fire Storm                   IN3 a patch tick: resolve copy, Fire, 4% / 6% a second
  211143  Fire Storm                   IN3 the cast hands on him as the marker goes down (look)
  211144  Fire Storm                   IN3 the 5 yd lava pool on a stalker for the patch's life (look)
  211145  Magma Fist                   IN4 the line's hit: resolve copy, Fire, 25% / 40% + Weakened (the throw is C++)
  211146  Magma Fist                   IN4 the magma wave from him to the line's end (look)
  211147  Magma Fist                   IN4 the fire ring at his feet as the line goes down (look)
  211148  Lava Surge                   IN5 the strip's hit: resolve copy, Fire, 30% / 45% + Weakened
  211149  Lava Surge                   IN5 Lava Strike along the strip (look)
  211150  Shatter                      IN6 the eruption where he breaks (look, on a stalker)
  211151  Reborn at the Anvil          IN7 the fire pillar as he reforms (look)
  211152  Reborn at the Anvil          IN6 an Ember sinks into the Anvil (look)
  211153  The Island Crumbles          IN8 Lava Strike along a band as it crumbles (look)
  211154  Crumbled Edge                IN8 the crack and lava glow on a stalker, the rest of the fight (look)
  211155  Crumbling Ground             IN8 the burst on a unit thrown over the edge (look; the throw is the kit's)
  211156-211179 spare

Retired: Mighty Blow 14099 (Magma Fist); the stock Curse 26977, Fiery Burst 13900 and Fire Storm 13899 are not cast
any more (rule 15: copies in the slice). Visual ids are V-1's (._visuals IN_*); every look is unconfirmed until seen in
game.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    ATTR3_NOT_A_PROC,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    FACTION_ELEMENTAL,
    IMMUNITY_FIRE_GIANT,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    kit_creature,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    IN_CURSE,
    DISPLAY_EMBER_OF_INCENDIUS,
    IN_CRUMBLE_BURST,
    IN_CRUMBLED_EDGE_CRACK,
    IN_FIERY_BURST,
    IN_FIRE_STORM_CAST,
    IN_FIRE_STORM_PATCH,
    IN_LAVA_SURGE,
    IN_MAGMA_FIST,
    IN_MAGMA_FIST_RING,
    IN_REBORN_AT_THE_ANVIL,
    IN_SHATTER_INTO_EMBERS,
)

creature_template_columns(9017, **boss_columns(
    'boss_lord_incendius_rework', 40.766, damage_modifier=3.5, CreatureImmunitiesId=IMMUNITY_FIRE_GIANT,
))

_IN = 'Blackrock Depths build WP-D11 (Lord Incendius)'
_SCRIPT_REFFLAT = ('Blackrock Depths: a percent of reference health in hundredths, set at launch by the kit\'s '
                   'spell_dungeon_refflat_damage (DungeonKit::RefFlatOn)')

_TARGET_SRC_CASTER = 22
_TARGET_UNIT_SRC_AREA_ENEMY = 15
_TARGET_UNIT_DEST_AREA_ENEMY = 16
_TARGET_DEST_TARGET_ENEMY = 53
_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40
_DISPEL_CURSE = 2
_DEFENSE_MAGIC = 1
_PREVENTION_SILENCE = 1
_INTERRUPT_FLAGS_KICKABLE = 15
_FIRE_MASK = 4                      # SPELL_SCHOOL_MASK_FIRE
# AURA_INTERRUPT_FLAG_CHANGE_MAP (SpellDefines.h): a map change or a logout drops it, so nothing outlives the instance.
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000

# Icons (the client Spell.dbc, the stock spells').
_ICON_CURSE = 876                   # Curse of the Elemental Lord 26977
_ICON_FIERY_BURST = 18              # Fiery Burst 13900
_ICON_FIRE_STORM = 37               # Fire Storm 13899
_ICON_MAGMA_FIST = 314              # Mighty Blow 14099 (the retired spell it replaces)
_ICON_GENERIC = 1

# Numbers (IncendiusLogic.h).
_CURSE_MS = 60000                   # kCurseMs
_CURSE_PCT = 10                     # kCurseFirePct
_CURSE_RADIUS = 45.0                # kCurseRadiusYd
_BURST_CAST_MS = 1500               # kBurstCastMs
_BURST = (1200, 1500)               # kBurstPct, hundredths
_BURST_RADIUS = 10.0                # kBurstRadiusYd
_BURST_RANGE = 40.0                 # kBurstRangeYd
_PATCH_MS = 30000                   # kFireStormLifeMs (the stalker carries it; D12's 20 s patch despawns sooner)
_FIST_WAVE_SPEED = 30.0             # the magma wave's flight, yd/s (a look)
_EMBER_HEALTH_MODIFIER = 2.4459     # ceil(2,453 x 2.4459) = 6,000 at level 53 (kEmberHealth normal)
EMBER_HEROIC_ENTRY = 310405         # heroic_ids.lock: Ember of Incendius (STAGE-H-REPORT section 3)

# The scripted hit: no threat, no crit, always hits, ignores his modifiers (a percent of the reference row).
_HIT_ATTRS = dict(
    AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
    AttributesEx2=ATTR2_CANT_CRIT,
    AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
)


def _state_aura(spell_id: int, name: str, visual: int, duration_ms: int, notes: str):
    """A hidden DUMMY aura a stalker casts on itself for its look (a state kit needs an aura to play; not passive: a
    passive aura is never sent to the client). `duration_ms` -1: until the stalker goes."""
    return spell(
        id=spell_id, name=name, school=School.FIRE, dispel=0, mechanic=0,
        attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=_ICON_GENERIC, notes=notes,
        raw_overrides=kit_raw(SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                              CastingTimeIndex=1),
    )


def _look_at_point(spell_id: int, name: str, visual: int, notes: str, *, speed: float = 0.0):
    """A look-only spell cast at a point (a DUMMY aimed at a destination; DO_NOT_DISPLAY | DO_NOT_LOG), the boss's own
    cast, triggered. `speed` > 0: the visual flies there (a missile)."""
    more = {'Speed': speed} if speed else {}
    return spell(
        id=spell_id, name=name, school=School.FIRE, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
        spell_icon_id=_ICON_GENERIC, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, Targets=_TARGET_FLAG_DEST_LOCATION,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                              AttributesEx4=ATTR4_NO_CAST_LOG, **more),
    )


# --- 300794 Ember of Incendius ----------------------------------------------------------------------------------------

ember_300794 = creature_template(
    300794, 'Ember of Incendius', **{
        **kit_creature(faction=FACTION_ELEMENTAL, type=4), 'minlevel': 53, 'maxlevel': 53, 'rank': 1,
        'unit_class': 1, 'unit_flags': 0, 'HealthModifier': _EMBER_HEALTH_MODIFIER, 'DamageModifier': 1.0,
        'BaseAttackTime': 2000, 'ExperienceModifier': 0.0, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0,
        'mingold': 0, 'maxgold': 0, 'ScriptName': 'npc_brd_ember_of_incendius',
        'difficulty_entry_1': EMBER_HEROIC_ENTRY,
    },
)
creature_model(300794, display_id=DISPLAY_EMBER_OF_INCENDIUS)

# --- IN1 Curse of the Elemental Lord, IN2 Fiery Burst -----------------------------------------------------------------

curse_211140 = spell(
    id=211140, name='Curse of the Elemental Lord', school=School.FIRE, dispel=_DISPEL_CURSE, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=_CURSE_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN,
                    base_points=_CURSE_PCT - 1, die_sides=1, misc_value=_FIRE_MASK,
                    implicit_target_a=_TARGET_SRC_CASTER, implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY,
                    radius_yards=_CURSE_RADIUS)],
    spell_icon_id=_ICON_CURSE,
    notes=f'{_IN}, IN1: the stock Curse of the Elemental Lord 26977 (-100 Fire resistance) changed (rule 15: a copy in '
          'the slice): +10% Fire damage taken (MOD_DAMAGE_PERCENT_TAKEN, Fire mask) on every enemy within 45 yd for '
          '60 s, a Curse: removing it is a reward (the descriptor\'s dispel list). He casts it on himself, triggered, '
          'at 16 s and every 22 s (the stock timers). The stock look (SV 3959). Dropped on a map change; removed '
          'from every player when the fight ends.',
    raw_overrides=kit_raw('Increases Fire damage taken by all enemies within $a1 yards by $s1% for $d.',
                          'Fire damage taken increased by $s1%.', instant=True, DefenseType=_DEFENSE_MAGIC,
                          SpellVisualID_1=IN_CURSE, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

fiery_burst_211141 = spell(
    id=211141, name='Fiery Burst', school=School.FIRE, dispel=0, mechanic=0, cast_time_ms=_BURST_CAST_MS,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=_BURST_RANGE, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=_BURST[0] - 1, die_sides=1,
                    implicit_target_a=_TARGET_DEST_TARGET_ENEMY, implicit_target_b=_TARGET_UNIT_DEST_AREA_ENEMY,
                    radius_yards=_BURST_RADIUS, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_FIERY_BURST,
    notes=f'{_IN}, IN2: the stock Fiery Burst 13900 (510-690 Fire in 10 yd) rescaled (rule 15: a copy in the slice). '
          'A 1.5 s cast on his victim, at 9 s then every 9-13 s (the stock timers): every enemy within 10 yd of the '
          'victim takes 12% of the row (heroic 15%; hundredths 1200, EffectMiscValueB 1500; gap 36, designer '
          'question 1), the tank row on a tank. Interruptible (InterruptFlags 15, PreventionType silence): a reward '
          'on normal, expected on heroic (the descriptor\'s interrupt list). Cannot crit, always hits, ignores his '
          'modifiers. The stock SV 516. Bound to D12\'s spell_brd_lake_scaled_hit (the refflat percent times '
          'Firelord\'s Will on him: x1 off the hard mode), so the hard mode\'s Will raises it too (D12 request 1).',
    raw_overrides=kit_raw('Blasts enemies within $a1 yards of the target with fire.', CastingTimeIndex=16,
                          InterruptFlags=_INTERRUPT_FLAGS_KICKABLE, PreventionType=_PREVENTION_SILENCE,
                          DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=IN_FIERY_BURST,
                          EffectMiscValueB_1=_BURST[1], **_HIT_ATTRS),
)
scripted_by(fiery_burst_211141, 'spell_brd_lake_scaled_hit')     # refflat x Firelord's Will (D12)

# --- IN3 Fire Storm ---------------------------------------------------------------------------------------------------

fire_storm_211142 = resolve_copy(
    211142, 'Fire Storm', School.FIRE, 'The ground burns.',
    f'{_IN}, IN3: a Fire Storm patch\'s tick: every 10 s (heroic 8 s) from 6 s a 2 s marker at a random player\'s spot '
    '(the tank too, ruling 88), then a 5 yd patch for 30 s (D12: 20 s) that hits everyone inside every second for 4% '
    '(heroic 6%) of the row, plus the kit\'s Standing in It slow, through the registry. Copy of the resolve spell '
    '205001 with the Fire school. The pool is 211144.',
    icon=_ICON_FIRE_STORM,
)

fire_storm_cast_211143 = self_visual(
    211143, 'Fire Storm', IN_FIRE_STORM_CAST,
    f'{_IN}, IN3: Lord Incendius casts it on himself (triggered) as a Fire Storm marker goes down: the stock Fire '
    'Storm 13899\'s SV 10383, the cast hands and channel only (its own 23 yd PersistentArea is not the patch). Look '
    'only.',
    icon=_ICON_FIRE_STORM, school=School.FIRE,
)

fire_storm_patch_211144 = _state_aura(
    211144, 'Fire Storm', IN_FIRE_STORM_PATCH, _PATCH_MS,
    f'{_IN}, IN3: the patch\'s look: a stalker (300796) at the spot casts it on itself as the marker ends and lives '
    'as long as the patch (30 s; D12 20 s). Blackrock Spire\'s 5 yd lava pool state (SV 90607). Look only.',
)

# --- IN4 Magma Fist ---------------------------------------------------------------------------------------------------

magma_fist_211145 = resolve_copy(
    211145, 'Magma Fist', School.FIRE, 'A fist of magma drives along the ground.',
    f'{_IN}, IN4: the line\'s hit (from Mighty Blow 14099, retired): every 20 s from 12 s a 2 s line from him through '
    'a random player (the tank too, ruling 88; never the tank in D12, ruling 90), 4 yd wide (designer question 2), '
    'then 25% (heroic 40%) of the row + Weakened through the registry. Each player hit is thrown 10 yd along the line '
    'by the script (the kit\'s PushAlong: on the floor, or past the edge into the lava: ruling 48). Copy of the '
    'resolve spell 205001 with the Fire school.',
    icon=_ICON_MAGMA_FIST,
)

magma_fist_wave_211146 = _look_at_point(
    211146, 'Magma Fist', IN_MAGMA_FIST,
    f'{_IN}, IN4: the fist\'s look: he casts it (triggered) at the line\'s far end as it lands: Magma Wave 55916\'s SV '
    '12227, the fire wave projectile, at 30 yd/s. Look only.',
    speed=_FIST_WAVE_SPEED,
)

magma_fist_ring_211147 = self_visual(
    211147, 'Magma Fist', IN_MAGMA_FIST_RING,
    f'{_IN}, IN4: he casts it on himself (triggered) as the line goes down: Ember Blast 34133\'s SV 9426, the FireNova '
    'ring at his feet. Look only.',
    icon=_ICON_MAGMA_FIST, school=School.FIRE,
)

# --- IN5 Lava Surge ---------------------------------------------------------------------------------------------------

lava_surge_211148 = resolve_copy(
    211148, 'Lava Surge', School.FIRE, 'Lava surges over the edge of the island.',
    f'{_IN}, IN5: every 25 s (heroic 20 s) from 15 s, a 3 s marker, then a 6 yd strip along the long edge of the bulge '
    'where more players stand (s -3 to +15 on the causeway frame, its outer side on the current crumbled edge): 30% '
    '(heroic 45%) of the row + Weakened through the registry. Copy of the resolve spell 205001 with the Fire school.',
    icon=_ICON_FIRE_STORM,
)

lava_surge_burst_211149 = _look_at_point(
    211149, 'Lava Surge', IN_LAVA_SURGE,
    f'{_IN}, IN5: he casts it (triggered) at four points along the strip as it lands: Lava Strike 57571\'s SV 12456, '
    'fire bursts. Look only.',
)

# --- IN6 / IN7 Shatter and Reborn -------------------------------------------------------------------------------------

shatter_211150 = self_visual(
    211150, 'Shatter', IN_SHATTER_INTO_EMBERS,
    f'{_IN}, IN6: a lethal hit while a rebirth is left: he yells (line 0), breaks and is gone; a stalker at his spot '
    'casts this on itself (he is hidden the same tick): Massive Eruption 20483\'s SV 889. 4 (heroic 5) Embers 300794 '
    'appear at the edges. Look only.',
    icon=_ICON_FIERY_BURST, school=School.FIRE,
)

reborn_211151 = self_visual(
    211151, 'Reborn at the Anvil', IN_REBORN_AT_THE_ANVIL,
    f'{_IN}, IN7: 12 s after the shatter he reforms by The Black Anvil (40% of his health + 10% per Ember that '
    'arrived) and casts this on himself (triggered): Pillar of Fire 43541\'s SV 9727 (never the blue SV 3944). Look '
    'only.',
    icon=_ICON_FIERY_BURST, school=School.FIRE,
)

ember_arrives_211152 = self_visual(
    211152, 'Reborn at the Anvil', IN_FIERY_BURST,
    f'{_IN}, IN6: an Ember of Incendius that reaches The Black Anvil casts this on itself (triggered) and sinks in (it '
    'despawns 0.5 s later; he will reform 10% stronger): Fiery Burst 13900\'s SV 516, a small fire burst. Look only.',
    icon=_ICON_FIERY_BURST, school=School.FIRE,
)

# --- IN8 The trap closes ----------------------------------------------------------------------------------------------

crumble_burst_211153 = _look_at_point(
    211153, 'The Island Crumbles', IN_CRUMBLE_BURST,
    f'{_IN}, IN8 (and D12 IN13): as a lethal band crumbles (5 s after its edge marker) he casts it (triggered) every '
    '10 yd along the band: Lava Strike 57571\'s SV 12456. Look only.',
)

crumbled_edge_211154 = _state_aura(
    211154, 'Crumbled Edge', IN_CRUMBLED_EDGE_CRACK, -1,
    f'{_IN}, IN8 (and D12 IN13): the crumbled band\'s look for the rest of the fight: a stalker (300796) every 10 yd '
    'along the band casts it on itself; it goes with the stalker at the fight\'s cleanup. The minted crack and lava '
    'glow (SV 90651, Ascension `groundcrack_fire_state` at 0.35). Look only.',
)

crumbling_ground_211155 = spell(
    id=211155, name='Crumbling Ground', school=School.FIRE, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_GENERIC,
    notes=f'{_IN}, IN8 (and D12 IN11 / IN13): he casts it (triggered) on each unit a crumbled band (the kit\'s '
          'LethalBand pushSpell) or a throw sends over the edge, as the jump starts: Lava Strike 57571\'s SV 12456 '
          'on the unit. The throw itself is the kit\'s PushOverEdge, the death the FallWatch (ruling 48). Look only.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=IN_CRUMBLE_BURST, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)
