"""
Shaman - the shared totems' new rows (SH0b A3, docs/reworks/shaman-shared-rework.md "Totems" and the per-totem entries).

Ids (SH0b-WP-BRIEF.md id map):
    202260 Earthbind root, 202261 Earthen Wall Totem (summon at an ally) + 202262 its shield, 202263 Windwalk Totem
    (summon) + 202264 Windwalk (the party area aura), 202265 Capacitor Totem (ground summon) + 202266 its passive +
    202267 the stun, 202268 Magma Totem (player ground summon; 8190 stays for the NPC casters) + 202269 its passive,
    202270 Searing bolt, 202271 Healing Stream heal.
    Creatures 300274 Earthen Wall, 300275 Windwalk, 300276 Capacitor, 300277 Magma, 300278 Searing.
    SkillLineAbility 30660-30663 (class mask 64, acquire 0), trainer 210 rows for the four summons.

The stock totem shape (CORE-AUDIT-A A1/A5/A8/A9, 0-verify tables 6 and 9): `Attributes 0x10000` (NOT_SHAPESHIFTED),
`AttributesEx7 0x20` (SUMMON_PLAYER_TOTEM), SUMMON effect with the SummonProperties in `EffectMiscValueB_1` (Fire 63,
Earth 81, Water 82, Air 83), Category 0 and no category cooldown, GCD 1000 / category 133 (the stock totems', not the
spike's 1500), no tool column (the tool strip is the point of SH0b), EquippedItemClass -1. The cooldown is longer than
the duration on every one (30 s / 60 s against 10-15 s); Cooldown Haste picks them up at 30 s and up.

Pulse timing. Every pulse totem's passive carries `AttributesEx5 0x200` (EXTRA_INITIAL_PERIOD): a totem caster ticks
the first time after 100 ms, so the totem "pulses the moment it is placed" and then on its period. The one deliberate
exception is Capacitor: its passive is the 2 s charge, so the first tick must stay at 2000 ms (no 0x200), and the
passive's own 2100 ms duration ends the totem right after the discharge (A37: `Unit::_UnapplyAura` kills a
TOTEM_PASSIVE totem when its passive expires).

Passive totems: Totem::InitStats makes a totem TOTEM_ACTIVE only when `m_spells[0]` has a cast time, and TotemAI does
nothing for a TOTEM_PASSIVE one. 300275 / 300276 / 300277 therefore carry their passive on `creature_template_spell`
Index 0 (cast on themselves at summon); 300274 / 300278 have an empty `m_spells[0]` and are driven by their own
`UpdateAI` (npc_sha_earthen_wall_totem / npc_sha_searing_totem).

Family bits (SpellClassSet 11; FAMILY-BITS section 5, constants from `_masks.py`):
    Earthen Wall summon d0 b3 + b29, shield d2 b15 (never d1 b5/b10, d0 b10); Windwalk and Capacitor summons d0 b29
    only; Magma ground summon d0 b12 (the stock Magma identity bit, which the "any totem" mask lists: Magma lacks b29,
    FAMILY-BITS section 3) ; Earthbind root d2 b5 + b14 (controlled-root DR); Searing bolt d0 b30; Healing Stream heal
    d0 b13. The passives, the stun and the Windwalk aura carry the family with no bits.

Script bindings (spell_shaman_totems.cpp, B3): `spell_sha_earthbind_pulse` on 6474 (replaces the stock
`spell_sha_earthbind_totem`, literal key 6474), `spell_sha_healing_stream_passive` on 5672 (the player-totem pulse,
so it works solo and across raid subgroups), `spell_sha_healing_stream_pulse` on 52041 (the NPC-owner path only;
replaces `spell_sha_healing_stream_totem`, literal key 52041), `spell_sha_earthen_wall` on 202261 and
`spell_sha_earthen_wall_shield` on 202262.

Costs (new totems; the nearest stock analog's %, every one [tune]): Earthen Wall 6% (Stoneclaw 5730), Windwalk 5%
(brief; Wrath of Air is 11% but a 10 s totem), Capacitor 8% (brief), Magma ground 27% (stock 8190).
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, RANGE_SELF, School
from lib.dsl.registry import (
    const, creature_model, creature_spell, creature_template, pot_text, scripted_by, skill_line_ability, spell,
    trained_by, unbind_script,
)

from . import _masks as m
from .shaman_trigger_spells import magma_totem_8187

SPELLFAMILY_SHAMAN = 11

SPELL_ATTR0_PASSIVE = 0x40
SPELL_ATTR0_DO_NOT_DISPLAY = 0x80
SPELL_ATTR0_NOT_SHAPESHIFTED = 0x10000
SPELL_ATTR1_NO_REDIRECTION_AND_REFLECTION = 0x88   # stock Earthbind 3600's AttributesEx
SPELL_ATTR2_IGNORE_LINE_OF_SIGHT = 0x4
SPELL_ATTR2_NOT_AN_ACTION = 0x10000000             # stock Earthbind 3600's AttributesEx2
SPELL_ATTR3_PVP_ENABLING = 0x1                     # stock Earthbind 3600's AttributesEx3
SPELL_ATTR5_EXTRA_INITIAL_PERIOD = 0x200
SPELL_ATTR7_SUMMON_PLAYER_TOTEM = 0x20             # "Summons player-owned totem"

EFFECT_APPLY_AREA_AURA_PARTY = 35                  # SPELL_EFFECT_APPLY_AREA_AURA_PARTY (not in the DSL EffectType enum)
AURA_MOD_MINIMUM_SPEED = 305                       # SPELL_AURA_MOD_MINIMUM_SPEED (Unit::UpdateSpeed; Ghost Wolf 67116)

TARGET_UNIT_CASTER = 1
TARGET_UNIT_SRC_AREA_ENEMY = 15
TARGET_UNIT_TARGET_ALLY = 21
TARGET_SRC_CASTER = 22
TARGET_DEST_CASTER_BACK_RIGHT = 43                 # stock 3738 / 8512 (Air slot)
TARGET_DEST_TARGET_ANY = 63                        # the explicit unit target's position (P0 spike 6b)
TARGET_DEST_DEST = 87                              # the ground cursor (Lightwell 724)
TARGET_FLAG_DEST_LOCATION = 0x40

# SummonProperties for a real Totem: Fire 63, Earth 81, Water 82, Air 83.
SUMMON_PROPS_FIRE = 63
SUMMON_PROPS_EARTH = 81
SUMMON_PROPS_AIR = 83

SCHOOL_MASK_ALL = 127                              # SCHOOL_ABSORB misc: every school

MAGMA_SUMMON_D0_B12 = 0x1000                       # d0 b12: stock Magma Totem's identity bit (8190), kept on 202268

TRAINER_SHAMAN = 210
SKILL_LINE_RESTORATION = 374
SKILL_LINE_ENHANCEMENT = 373
SKILL_LINE_ELEMENTAL = 375
CLASS_MASK_SHAMAN = 64

# Stock icons: Stoneclaw Totem 5730 (689), Stoneskin Totem buff 8071 (690), Wrath of Air 3738 (340), Grounding Totem
# 8177 (1677, the Capacitor analog), Magma 8190 (37), Earthbind 2484 (686), Searing 3599 (680), Healing Stream 52042
# (2213).
ICON_EARTHEN_WALL = 689
ICON_EARTHEN_WALL_SHIELD = 690
ICON_WINDWALK = 340
ICON_CAPACITOR = 1677
ICON_MAGMA = 37
ICON_EARTHBIND = 686
ICON_SEARING = 680
ICON_HEALING_STREAM_HEAL = 2213

# Stock visuals: Stoneclaw summon 362, Wrath of Air summon 319, Magma summon 369, Searing bolt 67, Healing Stream heal
# 366, Earth Shield state kit 7362 (placeholder for the barrier, art is the V stage), Thunderstorm cast kit 11302.
SV_EARTHEN_WALL_SUMMON = 362
SV_AIR_SUMMON = 319
SV_MAGMA_SUMMON = 369
SV_SEARING_BOLT = 67
SV_HEALING_STREAM_HEAL = 366
SV_EARTH_SHIELD_STATE = 7362
SV_CAPACITOR_DISCHARGE = 11302

# Stock totem displays (CreatureDisplayInfo): earth 4588, fire 4589, water 4587, air 4590.
DISPLAY_EARTH_TOTEM = 4588
DISPLAY_FIRE_TOTEM = 4589
DISPLAY_AIR_TOTEM = 4590

NOTE = 'shaman-rework SH0b A3: '

# =====================================================================================================================
# Script numbers (generated into ShamanData::)
# =====================================================================================================================
SEARING_BOLT_PERIOD_MS = const('SEARING_BOLT_PERIOD_MS', 1000,
                               'Searing Totem: ms between bolts, the first at placement [fixed].')
SEARING_BOLT_COUNT = const('SEARING_BOLT_COUNT', 10, 'Searing Totem: bolts per placement [fixed].')
SEARING_RANGE_YD = const('SEARING_RANGE_YD', 20.0, 'Searing Totem: target search radius, yd (stock) [tune].')
EARTHEN_WALL_PERIOD_MS = const('EARTHEN_WALL_PERIOD_MS', 2000,
                               'Earthen Wall Totem: ms between pulses, the first at placement [fixed].')
EARTHEN_WALL_PULSES = const('EARTHEN_WALL_PULSES', 8, 'Earthen Wall Totem: pulses per placement [fixed].')
EARTHEN_WALL_RANGE_YD = const('EARTHEN_WALL_RANGE_YD', 40.0,
                              'Earthen Wall Totem: spill-to-ally search radius, yd [tune].')
HEALING_STREAM_TARGETS = const('HEALING_STREAM_TARGETS', 5,
                               'Healing Stream Totem: allies healed per pulse, lowest health percent first [fixed].')
HEALING_STREAM_RANGE_YD = const('HEALING_STREAM_RANGE_YD', 40.0,
                                'Healing Stream Totem: ally search radius, yd [fixed].')


def _raw(spell_level, description='', aura_description=None, instant=True, gcd=False, base_level=True, **extra):
    """Columns every A3 row carries: shaman family (bits come in `extra`), no equipped-item requirement, magic defense,
    the learn level (and, off the potency path, the matching BaseLevel). `gcd` adds the stock totem GCD, 1000 / 133."""
    raw = {
        'SpellClassSet': SPELLFAMILY_SHAMAN,
        'EquippedItemClass': -1,
        'DefenseType': 1,
        'SpellLevel': spell_level,
    }
    if base_level:
        raw['BaseLevel'] = spell_level
    if instant:
        raw['CastingTimeIndex'] = 1
    if gcd:
        raw['StartRecoveryCategory'] = 133
        raw['StartRecoveryTime'] = 1000
    if description:
        raw['Description_Lang_enUS'] = description
    if aura_description is not None:
        raw['AuraDescription_Lang_enUS'] = aura_description
    raw.update(extra)
    return raw


def _summon(spell_id, name, creature, props, target_a, duration_ms, cooldown_ms, mana_pct, range_yards, icon,
            spell_level, description, notes, *, target_b=0, attributes=SPELL_ATTR0_NOT_SHAPESHIFTED, effects_extra=None,
            **raw_extra):
    """A player totem summon in the stock totem shape: SUMMON creature (HP 5, base_points 4 as stock 3738 / 5394 /
    8190), SummonProperties in EffectMiscValueB_1, AttributesEx7 SUMMON_PLAYER_TOTEM, Category 0, no category
    cooldown, instant, GCD 1000 / 133, no tool column."""
    effects = [Effect(
        type=EffectType.SUMMON, base_points=4, implicit_target_a=target_a, implicit_target_b=target_b,
        misc_value=creature,
    )]
    effects += effects_extra or []
    raw = _raw(
        spell_level, description, gcd=True,
        EffectMiscValueB_1=props, AttributesEx7=SPELL_ATTR7_SUMMON_PLAYER_TOTEM, **raw_extra,
    )
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=attributes, category=0, cast_time_ms=0,
        cooldown_ms=cooldown_ms, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=mana_pct, range_yards=range_yards,
        duration_ms=duration_ms, effects=effects, spell_icon_id=icon, notes=NOTE + notes, raw_overrides=raw,
    )


# =====================================================================================================================
# Earthbind root (202260): the baseline totem's 2 s root on placement, then the stock 50% slow (3600)
# =====================================================================================================================
earthbind_root_202260 = spell(
    id=202260, name='Earthbind', school=School.NATURE, dispel=DispelType.MAGIC, mechanic=Mechanic.ROOT, attributes=0,
    category=0, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=2000,
    effects=[Effect(
        type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_ROOT, implicit_target_a=TARGET_SRC_CASTER,
        implicit_target_b=TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=10.0,
    )],
    spell_icon_id=ICON_EARTHBIND,
    notes=NOTE + 'the 2 s root of the Earthbind Totem (docs "Earthbind Totem"). Cast by the totem at itself from '
          'spell_sha_earthbind_pulse on the passive 6474\'s first tick (player owners only; an NPC-owned totem keeps '
          'the slow alone). Same area shape as the stock slow 3600: SRC_CASTER / SRC_AREA_ENEMY, 10 yd, AttributesEx '
          '0x88, AttributesEx2 0x10000000, AttributesEx3 0x1, so the two spells treat targets alike (no ignore-LoS: an '
          'enemy behind a wall is neither slowed nor rooted). Family d2 b5 (Earthbind) + d2 b14 (the controlled-root '
          'DR, SpellMgr.cpp SPELLFAMILY_SHAMAN 0x4000). Mechanic ROOT, dispel magic (the slow\'s). 10 yd [tune], 2 s '
          '[fixed]. Aura text "Rooted." (number-free).',
    raw_overrides=_raw(
        6, 'Roots nearby enemies for $d.', 'Rooted.',
        AttributesEx=SPELL_ATTR1_NO_REDIRECTION_AND_REFLECTION,
        AttributesEx2=SPELL_ATTR2_NOT_AN_ACTION,
        AttributesEx3=SPELL_ATTR3_PVP_ENABLING,
        SpellClassMask_3=m.EARTHBIND_ROOT | m.ROOT_DR,
        PreventionType=1,
        SpellVisualID_1=68,
    ),
)
scripted_by(6474, 'spell_sha_earthbind_pulse')
unbind_script(6474, 'spell_sha_earthbind_totem')

# =====================================================================================================================
# Earthen Wall Totem (202261) and its shield (202262)
# =====================================================================================================================
earthen_wall_shield_202262 = spell(
    id=202262, name='Earthen Wall', school=School.NATURE, dispel=DispelType.MAGIC, attributes=0, category=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0,
    duration_ms=6000,
    effects=[Effect(
        type=EffectType.APPLY_AURA, apply_aura=AuraType.SCHOOL_ABSORB, misc_value=SCHOOL_MASK_ALL,
        implicit_target_a=TARGET_UNIT_TARGET_ALLY, sp_potency=40.0, potency_kind='absorb', time_basis_ms=2000,
    )],
    spell_icon_id=ICON_EARTHEN_WALL_SHIELD,
    notes=NOTE + 'the stone barrier: absorb 40 potency on the healing scale (T 2000, ~565 at 60), 6 s, every school, '
          'visible buff (not passive, not consolidated). Cast by the Earthen Wall totem (caster = the totem, so no '
          'shaman proc ever rolls) at an ally up to 40 yd away, hence range 50000 and AttributesEx2 0x4 (the positive '
          'totem-cast LoS exemption in CheckCast does not cover CheckEffectTarget; stock 52042 gets the same bit from '
          'SpellInfoCorrections). Owner spell power is added by spell_sha_earthen_wall_shield (absorbs get none from '
          'the engine) from the generated EffectBonusMultiplier_1. Family d2 b15; never d1 b5 / b10 or d0 b10 (the '
          'elemental-shield and NO_THREAT readers). Visual: Earth Shield state kit 7362 as a placeholder (V stage). '
          'Aura text number-free.',
    raw_overrides=_raw(
        20, 'Absorbs {pot1} damage for $d.', 'A stone barrier absorbs damage.', base_level=False,
        AttributesEx2=SPELL_ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=0x80,  # 0x80 = stack per caster (two shamans' shields coexist)
        SpellClassMask_3=m.EARTHEN_WALL_SHIELD,
        SpellVisualID_1=SV_EARTH_SHIELD_STATE,
    ),
)
scripted_by(earthen_wall_shield_202262, 'spell_sha_earthen_wall_shield')

earthen_wall_totem_202261 = _summon(
    202261, 'Earthen Wall Totem', 300274, SUMMON_PROPS_EARTH, TARGET_DEST_TARGET_ANY, 15000, 60000, 6, 40.0,
    ICON_EARTHEN_WALL, 20,
    "Summons an Earthen Wall Totem at a friendly target's feet for $d. When placed and every 2 sec, it shields the "
    'target, absorbing ' + pot_text(earthen_wall_shield_202262) + ' damage for 6 sec. If the target\'s shield is still '
    'full, the pulse shields the most injured ally within 40 yards instead. 1 min cooldown.',
    'Earthen Wall Totem, learned at 20 (trainer 210), replaces Stoneclaw. 15 s, 1 min cooldown, 6% base mana [tune] '
    '(Stoneclaw\'s), GCD 1000 / 133. P0 spike 6b / A9 shape: eff0 SUMMON creature 300274 (props 81) at the explicit '
    'target\'s position (TARGET_DEST_TARGET_ANY 63), eff1 DUMMY on TARGET_UNIT_TARGET_ALLY (21) so the cursor wants an '
    'ally, CheckTarget enforces it and spell_sha_earthen_wall hands the totem its GUID. 40 yd. Family d0 b3 + b29. '
    'Visual: Stoneclaw\'s summon kit 362.',
    effects_extra=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ALLY)],
    SpellClassMask_1=m.EARTHEN_WALL_SUMMON | m.SUMMON_D0_B29,
    SpellVisualID_1=SV_EARTHEN_WALL_SUMMON,
)
scripted_by(earthen_wall_totem_202261, 'spell_sha_earthen_wall')

# =====================================================================================================================
# Windwalk Totem (202263) and the party aura (202264)
# =====================================================================================================================
windwalk_202264 = spell(
    id=202264, name='Windwalk', school=School.NATURE, attributes=0, category=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(
            type=EFFECT_APPLY_AREA_AURA_PARTY, base_points=19, implicit_target_a=TARGET_UNIT_CASTER,
            apply_aura=AuraType.MOD_INCREASE_SPEED, radius_yards=10.0,
        ),
        Effect(
            type=EFFECT_APPLY_AREA_AURA_PARTY, base_points=99, implicit_target_a=TARGET_UNIT_CASTER,
            apply_aura=AURA_MOD_MINIMUM_SPEED, radius_yards=10.0,
        ),
    ],
    spell_icon_id=ICON_WINDWALK,
    notes=NOTE + 'the totem\'s Index-0 passive and the visible buff: a party area aura (APPLY_AREA_AURA_PARTY 35, the '
          'stock totem-buff shape of 8515 / 52109, 10 yd [tune]) cast on the totem itself, so the aura owner is the '
          'totem and UnitAura::FillTargetMap scans its party within 10 yd; eff0 MOD_INCREASE_SPEED +20% (stored 19) '
          '[tune], eff1 MOD_MINIMUM_SPEED 305 stored 99 = never below 100% (Ghost Wolf 67116\'s value; honoured in '
          'Unit::UpdateSpeed). Implicit target A is 1 (caster), not 20: an area-aura effect on a party-area target '
          'would make every party member an aura owner scanning its own radius. Not passive and not hidden (the buff '
          'shows); no duration of its own (the totem is the clock). Aura text number-free.',
    raw_overrides=_raw(
        30, '', 'Movement speed increased and cannot be slowed below normal.',
        SpellVisualID_1=366,
    ),
)

windwalk_totem_202263 = _summon(
    202263, 'Windwalk Totem', 300275, SUMMON_PROPS_AIR, TARGET_DEST_CASTER_BACK_RIGHT, 10000, 60000, 5, RANGE_SELF,
    ICON_WINDWALK, 30,
    'Summons a Windwalk Totem for $d that increases the movement speed of party members within 10 yards by 20% and '
    'prevents their movement speed from being reduced below normal. 1 min cooldown.',
    'Windwalk Totem, learned at 30 (trainer 210). 10 s, 1 min cooldown, 5% base mana [tune] (brief; stock Wrath of Air '
    'is 11%), GCD 1000 / 133. Attributes 0 (no 0x10000 NOT_SHAPESHIFTED), Stances 0: castable in Ghost Wolf, and '
    'casting it does not drop the form (T0b section 3). Air slot, back-right of the caster like 3738. Family d0 b29 '
    'only.',
    attributes=0,
    SpellClassMask_1=m.SUMMON_D0_B29,
    SpellVisualID_1=SV_AIR_SUMMON,
)

# =====================================================================================================================
# Capacitor Totem (202265), its passive (202266) and the stun (202267)
# =====================================================================================================================
capacitor_stun_202267 = spell(
    id=202267, name='Capacitor Totem', school=School.NATURE, dispel=DispelType.MAGIC, mechanic=Mechanic.STUN,
    attributes=0, category=0, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=RANGE_SELF, duration_ms=3000,
    effects=[Effect(
        type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, implicit_target_a=TARGET_SRC_CASTER,
        implicit_target_b=TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=8.0,
    )],
    spell_icon_id=ICON_CAPACITOR,
    notes=NOTE + 'the discharge: 3 s stun on every enemy within 8 yd [fixed] of the totem, fired by the passive '
          '202266\'s trigger at the 2 s mark. Area shape of the stock slow 3600 (SRC_CASTER / SRC_AREA_ENEMY, '
          'AttributesEx 0x88, Ex2 0x10000000, Ex3 0x1). Mechanic STUN, so it takes the stun DR like any stun; dispel '
          'magic (Stoneclaw stun 39796\'s). No family bits. Cast kit: Thunderstorm\'s SV 11302 (Thunder Caster '
          'Impact at the totem). Aura text "Stunned.".',
    raw_overrides=_raw(
        42, 'Stuns nearby enemies for $d.', 'Stunned.',
        AttributesEx=SPELL_ATTR1_NO_REDIRECTION_AND_REFLECTION,
        AttributesEx2=SPELL_ATTR2_NOT_AN_ACTION,
        AttributesEx3=SPELL_ATTR3_PVP_ENABLING,
        PreventionType=1,
        SpellVisualID_1=SV_CAPACITOR_DISCHARGE,
    ),
)

capacitor_totem_passive_202266 = spell(
    id=202266, name='Capacitor Totem Passive', school=School.NATURE,
    attributes=SPELL_ATTR0_PASSIVE | SPELL_ATTR0_DO_NOT_DISPLAY, category=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=2100,
    effects=[Effect(
        type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, base_points=-1,
        implicit_target_a=TARGET_UNIT_CASTER, amplitude=2000, trigger_spell=capacitor_stun_202267.id,
    )],
    spell_icon_id=ICON_CAPACITOR,
    notes=NOTE + '300276\'s m_spells[0]: the 2 s charge. PERIODIC_TRIGGER_SPELL, period 2000, triggers the stun 202267 '
          'once; duration 2100 ms so the passive expires right after the discharge and the totem dies with it (A37: '
          'Unit::_UnapplyAura, TOTEM_PASSIVE only). Deliberately NO AttributesEx5 0x200: the first tick must come at '
          '2000 ms (the 0x200 rule is for pulse totems; the doc\'s "Capacitor ... gathers electricity, then after 2 '
          'sec stuns" is the exception).',
    raw_overrides=_raw(42, '', gcd=False),
)

capacitor_totem_202265 = _summon(
    202265, 'Capacitor Totem', 300276, SUMMON_PROPS_AIR, TARGET_DEST_DEST, 3000, 60000, 8, 30.0, ICON_CAPACITOR, 42,
    'Summons a Capacitor Totem at the target location that gathers electricity, then after 2 sec stuns all enemies '
    'within 8 yards for 3 sec. 1 min cooldown.',
    'Capacitor Totem, learned at 42 (trainer 210). Ground-targeted (A=87 TARGET_DEST_DEST + Targets 0x40 '
    'DEST_LOCATION, the Lightwell 724 shape), 30 yd [tune], Air props 83. The totem lives until it discharges: its '
    'passive 202266 ends it at 2.1 s, and the summon duration (3 s) is only the backstop and the totem-bar timer. '
    '1 min cooldown, 8% base mana [tune] (brief), GCD 1000 / 133. Family d0 b29 only.',
    SpellClassMask_1=m.SUMMON_D0_B29,
    Targets=TARGET_FLAG_DEST_LOCATION,
    SpellVisualID_1=SV_AIR_SUMMON,
)

# =====================================================================================================================
# Magma Totem, player id (202268) and its passive (202269)
# =====================================================================================================================
magma_totem_passive_202269 = spell(
    id=202269, name='Magma Totem Passive', school=School.FIRE,
    attributes=SPELL_ATTR0_PASSIVE | SPELL_ATTR0_DO_NOT_DISPLAY, category=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(
        type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_TRIGGER_SPELL, base_points=-1,
        implicit_target_a=TARGET_UNIT_CASTER, amplitude=1500, trigger_spell=magma_totem_8187.id,
    )],
    spell_icon_id=ICON_MAGMA,
    notes=NOTE + '300277\'s m_spells[0] (the player Magma Totem\'s pulse driver). PERIODIC_TRIGGER_SPELL, period 1500, '
          'triggers the stock pulse 8187 (potency 20, T 1500); AttributesEx5 0x200 so it pulses at placement; 15 s '
          'makes 10 pulses. The stock passive 8188 (period 2000) and creature 5929 stay for the NPC casters of 8190.',
    raw_overrides=_raw(26, '', gcd=False, AttributesEx5=SPELL_ATTR5_EXTRA_INITIAL_PERIOD),
)

magma_totem_ground_202268 = _summon(
    202268, 'Magma Totem', 300277, SUMMON_PROPS_FIRE, TARGET_DEST_DEST, 15000, 30000, 27, 30.0, ICON_MAGMA, 26,
    'Summons a Magma Totem at the target location for $d that deals ' + pot_text(magma_totem_8187) + ' Fire damage '
    'to all enemies within 8 yards every 1.5 sec. 30 sec cooldown.',
    'Magma Totem, learned at 26 (trainer 210); the player id (ground targeting would break the NPC casters of 8190, '
    'SAI 2555 / 17235, which keep the stock spell, creature 5929 and passive 8188). Ground-targeted (A=87 + Targets '
    '0x40), 30 yd [tune], Fire props 63 (Fire Nova needs a real Totem in the fire slot). 15 s, 30 s cooldown, 27% '
    'base mana [tune] (stock 8190), GCD 1000 / 133. Family d0 b12 (the stock Magma identity bit, in the "any totem" '
    'mask), not b29. Visual: stock 369.',
    SpellClassMask_1=MAGMA_SUMMON_D0_B12,
    Targets=TARGET_FLAG_DEST_LOCATION,
    SpellVisualID_1=SV_MAGMA_SUMMON,
)

# =====================================================================================================================
# Searing bolt (202270) and the Healing Stream heal (202271): cast by their totems, never by the owner
# =====================================================================================================================
searing_bolt_202270 = spell(
    id=202270, name='Searing Bolt', school=School.FIRE, attributes=0, category=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=20.0,
    effects=[Effect(
        type=EffectType.SCHOOL_DAMAGE, sp_potency=25.0, potency_kind='direct', time_basis_ms=1000,
        implicit_target_a=6,
    )],
    spell_icon_id=ICON_SEARING,
    notes=NOTE + 'the Searing Totem\'s bolt: instant Fire, 25 potency on T 1000 (about 45 at 60 [tune]), 20 yd '
          '(stock). Cast by npc_sha_searing_totem (300278) at an engaged enemy each second from placement, plain '
          'cast, no owner GUID, so none of the shaman\'s procs roll. The stock 3606 (2.2 s cast, creatures 2523 / '
          '21995) is left alone: an instant 3606 would flip those totems to TOTEM_PASSIVE. Family d0 b30 (the '
          'Fire-totem damage bit shared with the Magma pulse). Missile Speed 19 and visual 67 as 3606.',
    raw_overrides=_raw(
        10, 'Deals {pot1} Fire damage to the target.', base_level=False,
        SpellClassMask_1=m.SEARING_MAGMA_BOLT,
        Speed=19.0,
        PreventionType=1,
        SpellVisualID_1=SV_SEARING_BOLT,
    ),
)

healing_stream_heal_202271 = spell(
    id=202271, name='Healing Stream Totem', school=School.NATURE, attributes=0, category=0, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0,
    effects=[Effect(
        type=EffectType.HEAL, sp_potency=20.0, potency_kind='heal', time_basis_ms=2000,
        implicit_target_a=TARGET_UNIT_TARGET_ALLY,
    )],
    spell_icon_id=ICON_HEALING_STREAM_HEAL,
    notes=NOTE + 'the Healing Stream Totem\'s heal: Nature, 20 potency on the healing scale (T 2000, about 282 at 60 '
          '[fixed]). Cast by spell_sha_healing_stream_passive (on the totem\'s passive 5672, every pulse) once per '
          'target of the 5 most injured players within 40 yd, cast by the totem with no owner GUID (no procs; it can '
          'crit). Range '
          '50000 and AttributesEx2 0x4 (stock 52042 gets 40 yd + ignore LoS from SpellInfoCorrections), DefenseType 1 '
          'so it is a magic-class heal. Family d0 b13 (Earthfury 3pc +10 yd accepted, PLAN 1D.6). SpellLevel 20 = the '
          'totem\'s learn level. The stock 52042 stays for NPC-owned Healing Stream totems.',
    raw_overrides=_raw(
        20, 'Heals the target for {pot1}.', base_level=False,
        AttributesEx2=SPELL_ATTR2_IGNORE_LINE_OF_SIGHT,
        SpellClassMask_1=m.HEALING_STREAM_HEAL,
        SpellVisualID_1=SV_HEALING_STREAM_HEAL,
    ),
)
scripted_by(5672, 'spell_sha_healing_stream_passive')
scripted_by(52041, 'spell_sha_healing_stream_pulse')
unbind_script(52041, 'spell_sha_healing_stream_totem')

# =====================================================================================================================
# Creatures: five new Totem entries (every one a real Totem, summoned with SummonProperties 63 / 81 / 83)
# =====================================================================================================================
_TOTEM_COLUMNS = dict(
    minlevel=1, maxlevel=80, faction=58, speed_walk=1.0, speed_run=1.0, speed_swim=1.0, speed_flight=1.0,
    DamageModifier=1.0, ManaModifier=1.0, ArmorModifier=1.0, ExperienceModifier=1.0, RegenHealth=1,
    BaseAttackTime=2000, RangeAttackTime=2000, BaseVariance=1.0, RangeVariance=1.0, HoverHeight=1.0,
    unit_flags=0, unit_flags2=2048, type=11, flags_extra=0,
)

# Stoneclaw 3579's columns without its two spells (5728 taunt passive, 55328 absorb carrier): a PASSIVE totem with an
# empty m_spells[0], driven by npc_sha_earthen_wall_totem.
earthen_wall_totem_300274 = creature_template(
    300274, 'Earthen Wall Totem', detection_range=18.0, unit_class=2, HealthModifier=0.26,
    ScriptName='npc_sha_earthen_wall_totem', **_TOTEM_COLUMNS,
)
creature_model(300274, display_id=DISPLAY_EARTH_TOTEM)

# Wrath of Air 15447's columns; Index 0 = the Windwalk aura.
windwalk_totem_300275 = creature_template(
    300275, 'Windwalk Totem', detection_range=20.0, unit_class=1, HealthModifier=0.05, ScriptName='',
    **_TOTEM_COLUMNS,
)
creature_model(300275, display_id=DISPLAY_AIR_TOTEM)
creature_spell(300275, 0, windwalk_202264)

# Same row; Index 0 = the Capacitor charge.
capacitor_totem_300276 = creature_template(
    300276, 'Capacitor Totem', detection_range=20.0, unit_class=1, HealthModifier=0.05, ScriptName='',
    **_TOTEM_COLUMNS,
)
creature_model(300276, display_id=DISPLAY_AIR_TOTEM)
creature_spell(300276, 0, capacitor_totem_passive_202266)

# Magma 5929's columns widened from level 34 to 1-80; Index 0 = the 1.5 s pulse driver.
magma_totem_300277 = creature_template(
    300277, 'Magma Totem', detection_range=18.0, unit_class=1, HealthModifier=0.05, ScriptName='',
    **_TOTEM_COLUMNS,
)
creature_model(300277, display_id=DISPLAY_FIRE_TOTEM)
creature_spell(300277, 0, magma_totem_passive_202269)

# Searing 2523's columns, level 1-80; empty m_spells[0], driven by npc_sha_searing_totem.
searing_totem_300278 = creature_template(
    300278, 'Searing Totem', detection_range=18.0, unit_class=1, HealthModifier=1.0,
    ScriptName='npc_sha_searing_totem', **_TOTEM_COLUMNS,
)
creature_model(300278, display_id=DISPLAY_FIRE_TOTEM)

# =====================================================================================================================
# Trainer 210 (priced by the learn-level curve) and spellbook entries. 5730 / 8190 are untrained in shaman_spells.py;
# the Earth / Fire / Water / Storm Elementals are trained in shaman_spells.py / shaman_elementals.py.
# =====================================================================================================================
trained_by(earthen_wall_totem_202261, TRAINER_SHAMAN, 20)
trained_by(windwalk_totem_202263, TRAINER_SHAMAN, 30)
trained_by(capacitor_totem_202265, TRAINER_SHAMAN, 42)
trained_by(magma_totem_ground_202268, TRAINER_SHAMAN, 26)

skill_line_ability(id=30660, skill_line=SKILL_LINE_ELEMENTAL, spell_id=earthen_wall_totem_202261.id,
                   class_mask=CLASS_MASK_SHAMAN, acquire_method=0)
skill_line_ability(id=30661, skill_line=SKILL_LINE_ENHANCEMENT, spell_id=windwalk_totem_202263.id,
                   class_mask=CLASS_MASK_SHAMAN, acquire_method=0)
skill_line_ability(id=30662, skill_line=SKILL_LINE_ENHANCEMENT, spell_id=capacitor_totem_202265.id,
                   class_mask=CLASS_MASK_SHAMAN, acquire_method=0)
skill_line_ability(id=30663, skill_line=SKILL_LINE_ELEMENTAL, spell_id=magma_totem_ground_202268.id,
                   class_mask=CLASS_MASK_SHAMAN, acquire_method=0)
