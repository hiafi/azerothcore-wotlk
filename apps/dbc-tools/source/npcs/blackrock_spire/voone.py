"""
Blackrock Spire build WP-B3: War Master Voone (9237), "the Axe Master"
(.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.5 row B3; build spec
docs/dungeons/blackrock-spire-rework.md SP "War Master Voone", VO1-VO13). WP-B3 owns this file (its spells:
kSpellsVoone 210090-210119 of modules/mod-dungeon-bosses src/BlackrockSpire/BlackrockSpireRework.h; VooneLogic.h names
the same ids; its creature is the Chain Anchor 300704; the Stuck Axe gameobject 301250 and his eight texts are the core
SQL rev rev_warmaster_voone_blackrock_spire.sql).

- 9237 War Master Voone: bound to boss_warmaster_voone_rework (SmartAI off: the stock C++ script
  boss_warmaster_voone stays registered, unbound by this data), normal 174k at 5 players (HealthModifier 60.606 on the
  level 58 warrior class base 2,871; the flex scaler multiplies it at the pull), stun immune (1972: stun, no silence, so
  the heroic War Cry can be silenced, handoff s7 #16), INSTANCE_BIND. DamageModifier 3.5, the stock value (the live 7.5
  is a mod-progression leftover; WP-T tunes melee). Heroic health 230k and the tier's melee are WP-H's
  (source/world/dungeons/blackrock_spire.py). The Mor Grayhoof trigger 45841 and the brazier are untouched, and so are
  his loot rows (L-1's).
- 300704 Chain Anchor: the invisible unit that stands on each stuck axe. It throws the axe's flight home (the Recall's
  look, both difficulties) and, on heroic, channels the chain beam at Voone. The mod-boss-mechanics stalker display
  11686 WITHOUT the trigger bit (0x80 hides a unit from non-GMs, and a hidden unit draws no beam; Greenskin's rope
  anchor 300425 is the same unit). Not selectable, not attackable, no loot, no XP (KIT_HELPER). Summoned on both
  difficulties from the normal entry (no heroic row: a helper, not a combat add).

Spells (looks from ._visuals, WP-V-1's VO_* picks; every look unconfirmed until seen in game):

  210090  Axe Throw      VO3 the Brawler lane's hit: Physical, 30% / 40% of the reference row + Weakened, from the
                         registry (a resolve copy). The missile look SV 3962 (Throw Axe 16075) flies him -> the hit.
                         Also VO1's hold answer: 20% / 25% (no Weakened) at a player hitting him from beyond 12 yd
  210091  Axe Fan        VO4 the Thrasher fan's hit (resolve copy, as 210090)
  210092  Axe Rain       VO5 the War Master circle's hit (resolve copy; Axe Volley 42357's own look is wrong, SV 3962)
  210093  Recall         VO7 a Recall lane's hit (resolve copy, no look: the flight is 210096)
  210094  Chain          VO11 (heroic) a chain crossing: 10% + Weakened (resolve copy, no look)
  210095  Axe Flight     look: an axe flies from him to a point (DUMMY at a destination, missile SV 3962, 15 yd/s: a
                         30 yd lane in the throw's 2 s warning)
  210096  Axe Return     look: a stuck axe flies from its spot to him (the anchor casts it at his position, SV 3962,
                         10 yd/s: 30 yd in the Recall's 3 s warning)
  210097  Chained Axe    VO11 (heroic) the chain: channeled by the anchor at him; Harpoon Chain 49679's beam (SV 10920)
  210098  War Cry        VO12 (heroic) the 2.5 s interruptible cast (Nature, silence-preventable); landed it is the
                         script's early Recall and Berserking for 10 s; kicked it does nothing
  210099  Berserking     VO10 +30% attack speed (SV 6943 STATE, Berserking 23505's red hands)
  210100  Berserker      VO1 the charge's look (Berserker Charge 16636's SV 4259), cast on himself as he jumps
          Charge
  210101  Recall         VO7 the 3 s cast bar naming the Recall (not interruptible; Physical, a school the War Cry
                         does not use: a kick on the War Cry never locks the bar)
  210102-210119 spare
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_THREAT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, spell

from ._common import (
    ATTR4_NO_CAST_LOG,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import DISPLAY_INVISIBLE_STALKER, VO_BERSERKER_CHARGE, VO_BERSERKING, VO_HARPOON_CHAIN, VO_THROW_AXE

_B3 = 'Blackrock Spire build WP-B3 (War Master Voone)'

creature_template_columns(9237, **boss_columns(
    'boss_warmaster_voone_rework', 60.606, damage_modifier=3.5,
))

# 300704 Chain Anchor: Greenskin's rope anchor's shape (the same stalker display, no trigger bit).
_FLAGS_EXTRA_NO_XP = 0x40

chain_anchor_300704 = creature_template(
    300704, 'Chain Anchor', **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1, 'type': 10,
                               'flags_extra': _FLAGS_EXTRA_NO_XP, 'ScriptName': ''},
)
creature_model(300704, display_id=DISPLAY_INVISIBLE_STALKER)

# --- shared bits -----------------------------------------------------------------------------------------------------

_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40
_ATTR1_IS_CHANNELED = 0x00000004
_ATTR3_SUPPRESS_CASTER_PROCS = 0x00010000
_ATTR3_SUPPRESS_TARGET_PROCS = 0x00020000
_ATTR5_ALLOW_ACTION_DURING_CHANNEL = 0x00000001

_ICON_THROW_AXE = 1             # generic (no stock axe icon id read)

# VooneLogic.h kThrowMissileSpeed / kReturnMissileSpeed: a 30 yd lane in the warning
_THROW_MISSILE_SPEED = 15.0
_RETURN_MISSILE_SPEED = 10.0

# --- VO3, VO4, VO5, VO7, VO11: the hits (resolve copies) --------------------------------------------------------------

axe_throw_210090 = resolve_copy(
    210090, 'Axe Throw', School.NORMAL, 'Voone hurls an axe down a lane.',
    f'{_B3}, VO3 (Brawler): the lane\'s hit. 30% (heroic 40%) of the reference row and 1 Weakened on a player in the '
    '4 x 30 yd lane, 2 s after the warning starts; the axe sticks at the lane\'s end. Copy of the mod-boss-mechanics '
    'resolve spell 205001 (Physical). The missile of Throw Axe 16075 (SV 3962) flies him -> each player hit. Also '
    'VO1\'s hold answer (R-1 ruling 1): while he holds after the charge, a player who damages him from beyond 12 yd '
    'is hit by one axe (20% / 25%, no Weakened, at most every 2 s, landing with the 210095 flight).',
    icon=_ICON_THROW_AXE, visual=VO_THROW_AXE,
)

axe_fan_210091 = resolve_copy(
    210091, 'Axe Fan', School.NORMAL, 'Voone hurls a fan of axes.',
    f'{_B3}, VO4 (Thrasher): a fan lane\'s hit, as 210090 (three lanes 30 degrees apart; a player where two lanes '
    'cross is hit by each).',
    icon=_ICON_THROW_AXE, visual=VO_THROW_AXE,
)

axe_rain_210092 = resolve_copy(
    210092, 'Axe Rain', School.NORMAL, 'Axes rain down.',
    f'{_B3}, VO5 (War Master): the circle\'s hit, 4 yd under a player, 2 s after the warning starts; an axe sticks in '
    'the circle\'s centre. As 210090. Axe Volley 42357\'s own look (SV 9766) has no missile: the Throw Axe missile '
    '(SV 3962) stands in (VISUALS-REPORT, handoff s3.10).',
    icon=_ICON_THROW_AXE, visual=VO_THROW_AXE,
)

recall_hit_210093 = resolve_copy(
    210093, 'Recall', School.NORMAL, 'The axes fly home.',
    f'{_B3}, VO7: a Recall lane\'s hit, 4 yd wide from each stuck axe toward him, the 5 yd at his side excluded '
    '(ExcludeSourceEnd). 30% (heroic 40%) of the reference row and 1 Weakened per axe through a player: two at once '
    'can kill. Resolve copy (Physical), no look of its own (the axe\'s flight is SPELL 210096).',
    icon=_ICON_THROW_AXE,
)

chain_hit_210094 = resolve_copy(
    210094, 'Chain', School.NORMAL, 'The chain bites.',
    f'{_B3}, VO11 (heroic): crossing a chain, 10% of the reference row and 1 Weakened, once per chain every 2 s '
    '(the persistent line\'s tick). Resolve copy (Physical), no look (the beam is SPELL 210097).',
    icon=_ICON_THROW_AXE,
)

# --- the looks --------------------------------------------------------------------------------------------------------


def _flight_look(spell_id: int, name: str, speed: float, notes: str):
    """An instant DUMMY at a destination: the missile of Throw Axe 16075 (SV 3962) travels from the caster to the
    point at `speed`; nothing else (no damage, no aura; DO_NOT_DISPLAY | DO_NOT_LOG)."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
        spell_icon_id=_ICON_THROW_AXE, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=VO_THROW_AXE, Speed=speed,
                              Targets=_TARGET_FLAG_DEST_LOCATION, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


axe_flight_210095 = _flight_look(
    210095, 'Axe Flight', _THROW_MISSILE_SPEED,
    f'{_B3}, VO3 / VO4 / VO5: the look of a thrown axe, cast by him (triggered) at the lane\'s end or the circle\'s '
    'centre as the warning starts. Throw Axe 16075\'s missile (SV 3962) at 15 yd/s: a 30 yd lane in the 2 s warning. '
    'Look only; the registry owns the hit.',
)

axe_return_210096 = _flight_look(
    210096, 'Axe Return', _RETURN_MISSILE_SPEED,
    f'{_B3}, VO7: a stuck axe flies home, cast by its Chain Anchor (triggered) at his position as the Recall\'s '
    'warning starts. Throw Axe 16075\'s missile (SV 3962) at 10 yd/s: 30 yd in the 3 s warning (the stock look '
    'cannot play backwards; the missile flies from the axe, which is the right way). Look only.',
)

# --- VO11: the chain beam ---------------------------------------------------------------------------------------------

chained_axe_210097 = spell(
    id=210097, name='Chained Axe', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=60000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_THROW_AXE,
    notes=f'{_B3}, VO11 (heroic): the chain. Channeled by the stuck axe\'s Chain Anchor at Voone; the channel draws '
          'the beam (Skadi\'s Harpoon Chain 49679\'s SV 10920, kit 10076, ruling 32) and the aura is on him (one per '
          'anchor: different casters coexist). IS_CHANNELED + NO_THREAT, ignores LoS, suppresses procs, always hits, '
          'ALLOW_ACTION_DURING_CHANNEL, no interrupt flags; 60 s is only the cap on a lost handle: the script '
          'removes it when the axe is recalled, with the anchor.',
    raw_overrides=kit_raw('An iron chain binds an axe to its master.', 'Chained to an axe.', CastingTimeIndex=1,
                          InterruptFlags=0, AuraInterruptFlags=0, ChannelInterruptFlags=0,
                          AttributesEx=_ATTR1_IS_CHANNELED | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS | _ATTR3_SUPPRESS_TARGET_PROCS
                          | ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG,
                          AttributesEx5=_ATTR5_ALLOW_ACTION_DURING_CHANNEL,
                          SpellVisualID_1=VO_HARPOON_CHAIN),
)

# --- VO12: War Cry ----------------------------------------------------------------------------------------------------

war_cry_210098 = spell(
    id=210098, name='War Cry', school=School.NATURE, cast_time_ms=2500, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_THROW_AXE,
    notes=f'{_B3}, VO12 (heroic): the interruptible cast, first at 15 s, then every 25 s. DUMMY on the caster, 2.5 s '
          '(VooneLogic.h kWarCryCastMs). Interruptible and silence-preventable (InterruptFlags 15, PreventionType '
          'silence, as the stock casters): his stun-only immunity set 1972 lets a silence work (handoff s7 #16). '
          'Nature, a school none of his other casts use, so a kick locks nothing else. Landed (OnSpellCast) the '
          'script sends the early Recall (1.5 s warning) and gives Berserking 10 s; kicked it does nothing.',
    raw_overrides=kit_raw('Voone bellows a war cry: every chain yanks taut, and he flies into a berserk rage.',
                          InterruptFlags=15, PreventionType=1, DefenseType=1),
)

# --- VO10: Berserking -------------------------------------------------------------------------------------------------

berserking_210099 = spell(
    id=210099, name='Berserking', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=60000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_MELEE_HASTE, base_points=30, die_sides=0,
                    implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Berserking: a flat +30% attack speed, not a damage or heal value')],
    spell_icon_id=_ICON_THROW_AXE,
    notes=f'{_B3}, VO10: +30% attack speed (MOD_MELEE_HASTE 30) while he wears it: the War Master stance (to its '
          'end) and a landed War Cry (10 s), whichever ends later. The script casts it on himself (triggered) and '
          'shortens the aura to the time left (DungeonKit::ShortenAura); 60 s is only the cap. The troll racial\'s '
          'look, Berserking 23505\'s red hands (SV 6943, a STATE).',
    raw_overrides=kit_raw('Increases attack speed by $s1%.', 'Attack speed increased by $s1%.', CastingTimeIndex=1,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          SpellVisualID_1=VO_BERSERKING),
)

# --- VO1: the charge, VO7: the cast bar -------------------------------------------------------------------------------

charge_look_210100 = self_visual(
    210100, 'Berserker Charge', VO_BERSERKER_CHARGE,
    f'{_B3}, VO1: the charge\'s look, cast by him on himself as he jumps from his quarters to the hall\'s charge spot '
    '(DungeonKit::JumpTo lookSpell). Berserker Charge 16636\'s SV 4259 (a trail and dust, no stun state). The jump '
    'itself is the script\'s.',
)

recall_bar_210101 = cast_bar(
    210101, 'Recall', 3000, 'Voone calls his axes home.',
    f'{_B3}, VO7: the 3 s cast bar of the stance change\'s Recall (emote line 4 "%s calls his axes home!" beside it). '
    'DUMMY on the caster, not interruptible (InterruptFlags 0, PreventionType 0), Physical: a school the War Cry '
    '(Nature) does not use. The registry lanes own the hit.',
)
