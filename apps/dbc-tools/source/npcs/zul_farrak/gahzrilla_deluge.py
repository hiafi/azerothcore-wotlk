"""
Zul'Farrak build WP-D7Hb: the Deluge, phase 3 of the hard mode "The Crew at the Pool" (GZ22-GZ24)
(.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.5 row D7Hb, s3.7, s3.9 rows 9 and 10; build spec
docs/dungeons/zul-farrak-rework.md "Hard mode: the crew at the pool", Phase 3, rulings 42 and 43). WP-D7Hb owns this
file (its spells: kSpellsDeluge 214190-214209 of modules/mod-dungeon-bosses src/ZulFarrak/ZulFarrakRework.h only;
GahzrillaDelugeLogic.h names the same ids; Gahz'rilla's emote line 1 is the core SQL rev
rev_gahzrilla_deluge_zul_farrak.sql). The C++ is src/ZulFarrak/gahzrilla_deluge.cpp, a package of D7's PoolFight.h.

- 301033 the strike stalker (npc_zf_strike_stalker): KIT_HELPER (not selectable, not attackable, no XP) wearing the
  invisible stalker display 11686, passive. One is summoned at the pool's middle when the Deluge has risen and casts
  each Storm Strike's bolt at its point (V: "cast by a stalker at the point"); D7's cleanup despawns it. No trigger
  flag (the pool's stalker 301030's rule: its casts must show). No heroic template (stalkers run on their entry).
- 301032 (the second head of the stub's list) is not declared: Twin Call is D7Ha's (Raven, GZ20). Spare for D7Ha.

Spells:

  214190  Storm Strike    GZ24: the registry's resolve copy (Nature): 30% of the reference row and Weakened in a 3 yd
                          circle, 1.5 s after its warning, three a second near random players (the registry sets the
                          damage per target; the tank row on the tank)
  214191  Storm Strike    GZ24: the bolt at the point, cast by the strike stalker as the circle lands (V's SV 90702:
                          SV 3's InstantAreaKit only). Look only
  214192-214209 spare.

No kickable cast and no new bar: the Deluge is a scripted transition (emote line 1 and 5 s of rising water, the look is
D7's water disc 90830 at V's DELUGE_DISC_SCALE), the floes are KT's ice sheets (D7's ice disc 90831, D7's freeze look
214121), the strikes are registry Zones. Nothing new is dispellable (Weakened is the shared one).
"""

from lib.dsl import Effect, EffectType, School
from lib.dsl.dungeon_kit import ATTR0_DO_NOT_DISPLAY, ATTR0_DO_NOT_LOG, ATTR1_NO_THREAT, ATTR2_IGNORE_LINE_OF_SIGHT
from lib.dsl.registry import creature_model, creature_template, spell

from ._common import ATTR4_NO_CAST_LOG, KIT_HELPER, kit_raw, resolve_copy
from ._visuals import DELUGE_DISC_SCALE, DELUGE_DISC_START_SCALE, DISPLAY_INVISIBLE_STALKER, GZ_STORM_STRIKE

_D7HB = "Zul'Farrak build WP-D7Hb (the Deluge)"

# --- constants (GahzrillaDelugeLogic.h; lib/test_zul_farrak_deluge.py pins each) --------------------------------------

STRIKE_PCT = 30                 # Tune::kStrikePct
STRIKE_RADIUS_YD = 3            # Tune::kStrikeRadiusYd
STRIKE_WARN_MS = 1500           # Tune::kStrikeWarnMs
STRIKES_PER_SECOND = 3          # Tune::kStrikesPerSecond
RISE_SCALES = (DELUGE_DISC_START_SCALE, DELUGE_DISC_SCALE)  # Tune::kRiseStartScale, kRiseEndScale (V's)

# Stock icons (Spell.dbc SpellIconID of the named spell; read from the stock DBC 2026-11-25, as gahzrilla.py).
_ICON_LIGHTNING = 19            # Static Electricity 3742, Lightning Shield 324

_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40

# --- the strike stalker -----------------------------------------------------------------------------------------------

strike_stalker_301033 = creature_template(
    301033, 'Storm Strike Stalker', **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1,
                                       'type': 10, 'ScriptName': 'npc_zf_strike_stalker'},
)
creature_model(301033, display_id=DISPLAY_INVISIBLE_STALKER)

# --- GZ24 Storm Strikes -----------------------------------------------------------------------------------------------

storm_strike_214190 = resolve_copy(
    214190, 'Storm Strike', School.NATURE, 'Lightning strikes the flooded shore.',
    f'{_D7HB}, GZ24 (hard mode, phase 3, from the end of the rise): three a second in all (ruling 43), each a 3 yd '
    'Circle AoE 0 to 10 yd from a random player in a random direction, warned 1.5 s: 30% of the reference row and 1 '
    'Weakened, the tank included, the tank row on the tank (registry tag 38, the drill\'s row 10). Copy of the resolve '
    'spell 205001 (Nature). The bolt is 214191.',
    icon=_ICON_LIGHTNING,
)

storm_strike_look_214191 = spell(
    id=214191, name='Storm Strike', school=School.NATURE, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
    spell_icon_id=_ICON_LIGHTNING,
    notes=f'{_D7HB}, GZ24: the bolt where a Storm Strike lands, cast (triggered) at the point by the strike stalker '
          '301033 as the registry\'s circle resolves. V\'s SV 90702 (SV 3\'s InstantAreaKit 9161 only: call '
          'lightning, sound 30); SV 4229 is never wired. Look only.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=GZ_STORM_STRIKE, Targets=_TARGET_FLAG_DEST_LOCATION,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
