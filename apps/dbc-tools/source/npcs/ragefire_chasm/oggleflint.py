"""
Ragefire Chasm build WP-D1: Oggleflint (11517) (.agents/plans/ragefire-chasm-build/ragefire-chasm-build.HANDOFF.md
s3.5 row D1, s3.6, s3.8, s3.10, s3.12, s7 #28, #35; build spec docs/dungeons/ragefire-chasm-rework.md "Oggleflint",
OG1-OG5, ruling 15). WP-D1 owns this file (its spells: kSpellsOggleflint 213550-213579 of modules/mod-dungeon-bosses
src/RagefireChasm/RagefireChasmRework.h only; OggleflintLogic.h names the same ids; the texts are the core SQL rev
rev_oggleflint_ragefire_chasm.sql).

- 11517 Oggleflint: boss_oggleflint_rework (SmartAI off: rev_skeleton_ragefire_chasm.sql drops its row, Cleave 40505),
  the build spec's normal health (8,544 = HealthModifier 24 on the level 16 warrior base 356), the stock DamageModifier
  (until T), stun immunity 1972, INSTANCE_BIND with both assist flags, detection range 12 (s7 #12 A). Heroic 238,056 is
  WP-H's override (source/world/dungeons/ragefire_chasm.py).
- 300985 The Borer (OG1, OG2): npc_rfc_borer, the invisible carrier display 15294 wearing the dirt trail 213552, not
  selectable, not attackable; Oggleflint's script chases with it (the kit's Chaser), shows the worm 11010 for the
  eruption and removes it. No heroic template. Its display's creature_model_info row is stock (Ouro's Dirt Mound 15712;
  SELECT 2026-11-24), the worm's too (Earthborer 11320).

Spells. The rings' hits are dungeon copies of the mod-boss-mechanics resolve spell; the tank's swing is a plain effect
the kit's spell_dungeon_refflat_damage sets (RefFlatOn, the tank row); all ignore caster modifiers (rule 2):

  213550  Borer Eruption   OG2 the 4 yd ring's hit: resolve copy, Physical, 30% / 45% and Weakened
  213551  Borer Eruption   OG2 the dirt burst at the Borer's spot (SV 7443, its area kit)
  213552  Tunneling        OG1 the Borer's trail: a state aura on itself (SV 14013)
  213553  Club Swing       OG3 the 2 s wind-up bar, never interruptible
  213554  Club Swing       OG3 the cone's hit on everyone but the tank: resolve copy, Physical, 30% / 40% and Weakened
  213555  Club Swing       OG3 the tank's hit: 10% of the tank row (both difficulties)
  213556  Club Swing       OG3 the arc when no tank stands in the cone (SV 219)
  213557  Beating Blow     OG4 heroic: a blow's hit, resolve copy, Physical, 35% and Weakened (SV 2643)
  213558-213579 spare.

Retired as a cast: Cleave 40505. Looks are copied, never the stock spells (Tunnel Bore Passive 29147, Emergence 36633
and Wide Swipe 6749 are not used: s3.10). He casts nothing a player can kick.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR0_NO_ACTIVE_DEFENSE,
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    ATTR3_NOT_A_PROC,
    TARGET_UNIT_TARGET_ENEMY,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import DISPLAY_BORER_TUNNEL, OG_BEATING_BLOW, OG_BORER_ERUPTION, OG_BORER_TRAIL, OG_CLUB_SWING

_D1 = 'Ragefire Chasm build WP-D1 (Oggleflint)'

# --- the creatures ---------------------------------------------------------------------------------------------------

creature_template_columns(11517, **boss_columns(
    'boss_oggleflint_rework', 24.0, damage_modifier=2.2,
))

_TYPE_BEAST = 1

the_borer_300985 = creature_template(300985, 'The Borer', **{
    **KIT_HELPER, 'minlevel': 16, 'maxlevel': 16, 'rank': 0, 'unit_class': 1, 'type': _TYPE_BEAST,
    'ScriptName': 'npc_rfc_borer',
})
creature_model(300985, display_id=DISPLAY_BORER_TUNNEL)

# --- constants (RagefireChasmRework.h namespace Oggleflint; lib/test_ragefire_chasm_oggleflint.py pins each) ----------

SWING_WARN_MS = 2000                # kSwingWarnMs
SWING_TANK_PCT = 1000               # kSwingTankPct 10, in hundredths; EffectMiscValueB 0: the same on heroic

_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40
_DEFENSE_MELEE = 2

_SCRIPT_REFFLAT = ('Ragefire Chasm D1: a percent of reference health in hundredths, set by the kit\'s '
                   'spell_dungeon_refflat_damage (DungeonKit::RefFlatOn: the tank row on the tank)')

# Stock icons (Spell.dbc SpellIconID of the named spell, read 2026-11-24)
_ICON_BURROW = 252                  # Burrow 26381
_ICON_CLEAVE = 277                  # Cleave 40505
_ICON_GROUND_SMASH = 298            # Ground Smash 12734


def _look_at_point(*, spell_id: int, name: str, visual: int, notes: str, icon: int):
    """A look-only spell cast at a point (a DUMMY aimed at a destination; DO_NOT_DISPLAY | DO_NOT_LOG), triggered: the
    cast kit on the caster, the area kit at the point, no impact kit on anyone (the Crell / Baelgar look shape)."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, Targets=_TARGET_FLAG_DEST_LOCATION,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- OG1 Borer Hunt, OG2 the eruption --------------------------------------------------------------------------------

borer_eruption_213550 = resolve_copy(
    213550, 'Borer Eruption', School.NORMAL, 'The Borer bursts out of the ground and throws you into the air.',
    f'{_D1}, OG2: the 4 yd ring where the Borer stopped, 2 s: 30% (heroic 45%) of the reference row and 1 Weakened, '
    'the tank row on the tank (registry tag 2); the script throws players straight up. Copy of the resolve spell '
    '205001 (Physical).',
    icon=_ICON_BURROW,
)

borer_eruption_look_213551 = _look_at_point(
    spell_id=213551, name='Borer Eruption', visual=OG_BORER_ERUPTION, icon=_ICON_BURROW,
    notes=f'{_D1}, OG2: the dirt burst, cast by the Borer (triggered) at its own spot as the ring lands: SpellVisual '
    '7443 (BurrowEarth_Brown_Missile area kit; its stock spells 26271 and 26221 are aimed at a destination too). Look '
    'only.',
)

tunneling_213552 = spell(
    id=213552, name='Tunneling', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_BURROW,
    notes=f'{_D1}, OG1: the Borer\'s dirt trail, a DUMMY aura it casts on itself (triggered), no duration: the script '
          'removes it at the eruption. SpellVisual 14013 (the stock Pursuing Spikes state). No effect.',
    raw_overrides=kit_raw('Tunnels under the ground.', 'Tunneling.', CastingTimeIndex=1,
                          SpellVisualID_1=OG_BORER_TRAIL, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- OG3 Club Swing --------------------------------------------------------------------------------------------------

club_swing_bar_213553 = cast_bar(
    213553, 'Club Swing', SWING_WARN_MS, 'Swings his club at everyone in front of him.',
    f'{_D1}, OG3: the 2 s wind-up bar beside the registry\'s Frontal (90 degrees, 8 yd). Not interruptible; no kick '
    'of his school can exist (he casts nothing kickable).',
    icon=_ICON_CLEAVE,
)

club_swing_213554 = resolve_copy(
    213554, 'Club Swing', School.NORMAL, 'Swings his club at everyone in front of him.',
    f'{_D1}, OG3: the swing on others, a registry Frontal (90 degrees, 8 yd, the 2 s wind-up, the tank exempt): '
    '30% (heroic 40%) of the reference row and 1 Weakened (registry tag 18). Copy of the resolve spell 205001 '
    '(Physical). Cleave\'s SpellVisual 219.',
    icon=_ICON_CLEAVE, visual=OG_CLUB_SWING,
)

club_swing_tank_213555 = spell(
    id=213555, name='Club Swing', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_ACTIVE_DEFENSE,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=SWING_TANK_PCT - 1, die_sides=1,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_CLEAVE,
    notes=f'{_D1}, OG3: the swing on the tank as the Frontal lands (the victim inside the cone): 10% of the tank\'s '
          'row on both difficulties (s7 #35), Physical, instant, never missed (always hits, no active defense, cannot '
          'crit) and ignoring his modifiers. Tank work: no Weakened. Binds the kit\'s spell_dungeon_refflat_damage. '
          'Cleave\'s SpellVisual 219.',
    raw_overrides=kit_raw('Swings his club at everyone in front of him.', instant=True, DefenseType=_DEFENSE_MELEE,
                          SpellVisualID_1=OG_CLUB_SWING, AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(club_swing_tank_213555, 'spell_dungeon_refflat_damage')

club_swing_look_213556 = _look_at_point(
    spell_id=213556, name='Club Swing', visual=OG_CLUB_SWING, icon=_ICON_CLEAVE,
    notes=f'{_D1}, OG3: his swing when no tank stands in the cone (213555 carries it otherwise), cast at his own spot '
    '(triggered): SpellVisual 219. Look only.',
)

# --- OG4 the Beating (heroic) ----------------------------------------------------------------------------------------

beating_blow_213557 = resolve_copy(
    213557, 'Beating Blow', School.NORMAL, 'Leaps after you and clubs the spot you stood on.',
    f'{_D1}, OG4 (heroic): one of three blows 1.5 s apart, a 3 yd circle on the spot the beaten player stood when it '
    'was marked: 35% of the reference row and 1 Weakened, the tank row on the tank (registry tag 3). Copy of the '
    'resolve spell 205001 (Physical). Ground Smash 12734\'s SpellVisual 2643.',
    icon=_ICON_GROUND_SMASH, visual=OG_BEATING_BLOW,
)
