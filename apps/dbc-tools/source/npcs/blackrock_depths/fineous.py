"""
Blackrock Depths build WP-D10: Fineous Darkvire (9056; GOs 301282 (hanging rope), 301283 (pillar); item 70622)
(.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D10; build spec docs/dungeons S2
737-756). WP-D10 owns this file; WP-S0 wrote the skeleton.

- 9056 Fineous Darkvire: bound to npc_fineous_darkvire_rework (modules/mod-dungeon-bosses
  src/BlackrockDepths/npc_fineous_darkvire_rework.cpp), SmartAI off (the S0 rev dropped his six rows; rev_fineous_
  blackrock_depths.sql keeps nothing of them: the stock spells are cast by the script), the build spec's normal health
  (HealthModifier 25.484 on the level 53 paladin class base 1,962 = 50,000), stun immunity 1972 (section 7 #10),
  no INSTANCE_BIND (flags_extra 0: credit 234 dropped), the stock DamageModifier. His patrol
  (path 476310, creature_addon) is the stock row's.
  Heroic health (80,000) and its overrides are WP-H's (source/world/dungeons/blackrock_depths.py).

Spells (kSpellsFineous 211120-211139, FineousLogic.h names the same ids):

  211120  Shoddy Construction  FD1 the pillar's collapse: 6 yd circle, 3 s after it goes in, 25% (heroic 40%) of the
                               non-tank row + Weakened (the registry; a copy of the resolve spell 205001, Physical).
  211121  Holy Light           FD2 his 2.5 s self-heal, interruptible (a copy of the stock 15493 in the slice: the heal
                               is a percent of his health, 4% = 2,000 / 3,200, so it scales with his 50,000 / 80,000;
                               the stock 467-541 on 13,734 was 3.4-3.9%). Cast once at 60% and once at 40%.
  211122  Shoddy Construction  FD1 the pillar goes in (look only): Ground Spike 59750's SV 12718 at the spot.
  211123  Shoddy Construction  FD1 the pillar collapses (look only): Rock Shower 60919's SV 12855, a dust plume.
  211124-211139 spare.

Stock spells kept as they were (cast by the script from the stock SmartAI's rows): Devotion Aura 8258, Holy Strike
13953, Kick 11978, Seal of Reckoning 15346.

The rope's use spell is WP-IT's (event_items.py: 211261, bound to spell_brd_guzzler_rope, which this WP's C++ file
registers); item 70622 is IT's; GO 301282 (the hanging rope, display 7717) and 301283 (the pillar, display 5073) are
declared in data/sql/updates/pending_db_world/rev_fineous_blackrock_depths.sql.
"""

from lib.dsl import Effect, EffectType, School
from lib.dsl.dungeon_kit import ATTR1_NO_THREAT, ATTR2_IGNORE_LINE_OF_SIGHT
from lib.dsl.registry import creature_template_columns, spell

from ._common import ATTR4_NO_CAST_LOG, boss_columns, kit_raw, resolve_copy
from ._visuals import FD_COLLAPSE_DUST, FD_HOLY_LIGHT, FD_PILLAR_SPAWN_BURST

creature_template_columns(9056, **boss_columns(
    'npc_fineous_darkvire_rework', 25.484, damage_modifier=3.5, instance_bind=False,
))

# --- spells (211120-211139) ----------------------------------------------------------------------------------------

_TARGET_DEST_DEST = 87
_TARGET_UNIT_TARGET_ALLY = 21
_TARGET_FLAG_DEST_LOCATION = 0x40
_ATTR0_DO_NOT_DISPLAY = 0x00000080
_ATTR0_DO_NOT_LOG = 0x00000100

_ICON_GENERIC = 1
_ICON_HOLY_LIGHT = 70           # 1026
_ICON_SHODDY = 1

_BRD = 'Blackrock Depths build WP-D10'

shoddy_collapse_211120 = resolve_copy(
    211120, 'Shoddy Construction', School.NORMAL, 'A badly built pillar comes down.',
    f'{_BRD}, FD1 Shoddy Construction: the 6 yd collapse 3 s after the pillar goes in at a random player\'s spot, 25% '
    '(heroic 40%) of the non-tank row + Weakened. Copy of the resolve spell 205001 (Physical). The pillar is GO '
    '301283 and the earth spike / the dust are 211122 / 211123 at the spot; the hit itself carries no look.',
    icon=_ICON_SHODDY,
)

holy_light_211121 = spell(
    id=211121, name='Holy Light', school=School.HOLY, cast_time_ms=2500, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=40.0, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL_PCT, base_points=3, implicit_target_a=_TARGET_UNIT_TARGET_ALLY,
                    potency_excluded='Blackrock Depths: a percent of the target\'s own health, not a heal value')],
    spell_icon_id=_ICON_HOLY_LIGHT,
    notes=f'{_BRD}, FD2: a copy of the stock Holy Light 15493 (never the shared id: its heal is flat and tiny on '
          '50,000 health): 2.5 s cast, interruptible (InterruptFlags 15 and PreventionType silence, the interruptible '
          'pair), heals 4% of the target\'s maximum health (HEAL_PCT, BasePoints 3 + DieSides 1). Fineous casts it on '
          'himself once at 60% and once at 40% health, never again: the descriptor names it for the bots. '
          'SpellVisual 2936.',
    raw_overrides=kit_raw('Heals a friendly target for $s1% of its maximum health.', CastingTimeIndex=20,
                          InterruptFlags=15, PreventionType=1, DefenseType=1, SpellPriority=50,
                          SpellVisualID_1=FD_HOLY_LIGHT),
)


def _look_at_point(spell_id: int, name: str, visual: int, notes: str):
    """A look-only spell cast at a point (a DUMMY aimed at a destination; DO_NOT_DISPLAY | DO_NOT_LOG), the boss's own
    cast, triggered (the Zigris Blast 210185 shape)."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
        spell_icon_id=_ICON_GENERIC, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, Targets=_TARGET_FLAG_DEST_LOCATION,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


pillar_rise_211122 = _look_at_point(
    211122, 'Shoddy Construction', FD_PILLAR_SPAWN_BURST,
    f'{_BRD}, FD1: the pillar goes in. Fineous casts it (triggered) at the player\'s spot beside the pillar object: '
    'Ground Spike 59750\'s SpellVisual 12718 (World GroundSpike_Impact, an earth spike, FD_PILLAR_SPAWN_BURST). Look '
    'only.',
)

collapse_dust_211123 = _look_at_point(
    211123, 'Shoddy Construction', FD_COLLAPSE_DUST,
    f'{_BRD}, FD1: the pillar falls. Fineous casts it (triggered) at the spot as the circle resolves: Rock Shower '
    '60919\'s SpellVisual 12855 (a dust plume, FD_COLLAPSE_DUST; alternate 8216). Look only.',
)
