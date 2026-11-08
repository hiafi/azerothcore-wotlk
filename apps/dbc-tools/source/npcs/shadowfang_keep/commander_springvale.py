"""
Shadowfang Keep build WP-S4: Commander Springvale and his three Risen Guardsmen
(.agents/plans/shadowfang-keep-build/shadowfang-keep-build.HANDOFF.md s3.5 rows SP1-SP8, s3.6 row S4; build spec
docs/dungeons/shadowfang-keep-rework.md SK 754-812 (build spec), SK 625-753 (design)). WP-S4 owns this file (its spells:
kSpellsSpringvale 205965-205989 only; modules/mod-dungeon-bosses src/ShadowfangKeep/SpringvaleLogic.h names the same
ids). User ruling (handoff s10, s7 #20): the Unbreakable Oath is damage taken -90%, not immunity.

- 4278 Commander Springvale: bound to boss_commander_springvale_rework (SmartAI off; WP-S4's SQL rev drops the stock
  rows 5588 / 1026 / 33581), normal health 12,124 (paladin base 433 x HealthModifier 28, s3.7), stun immune
  (IMMUNITY_BOSS_STUN 1972, s7 #8). Heroic 305,250 is WP-H's override in source/world/dungeons/shadowfang_keep.py.
- 300506 / 300507 / 300508 Risen Guardsman of the Light / of the Hammer / of the Altar (npc_sfk_risen_guardsman):
  boss-kit adds the Oath summons, copies of the Wailing Guardsman 3877 (undead, warrior, elite, faction 24, display
  3226, unit_flags 32832, DamageModifier 1.7 on a 2.0 s swing; its equipment row is WP-S4's SQL rev) at Springvale's
  level 20, normal health 1,000 (warrior base 484 x 2.0661, SK "1,000"), heroic 15,000 (WP-H's `_KIT_ADD_HEROIC`);
  no loot or gold (summoned adds), stunnable (no immunity set, s6 "kit adds stay stunnable"). Each names its heroic
  entry (STAGE-H s4: 310061-310063). Their heroic melee is the damage hook's tier swing (SK SP10); their heroic
  abilities are the script's (SP9, SP1, SP3), so this file has no other heroic number.

Spells. The registry's resolve copies (205965, 205968, 205970) carry mod-boss-mechanics' 205001 attribute set and are
bound to its resolve script, so they only rename the hit in the combat log; the shape, damage and Weakened stay the
registry's. The script spells that deal damage (205966, 205969, 205974) carry the same set (IGNORE_CASTER_MODIFIERS:
the Pilot's lesson R1 S-1) and set their value in OnEffectLaunchTarget (DungeonKit::RefFlat), so the target's
defensives count.

  205965  Hammer of Judgement   SP1 resolve copy (Holy): anyone else within 8 yd of the marked player, 25%, Weakened.
  205966  Hammer of Judgement   SP1 the marked player's own 10% (spell_sfk_springvale_hammer_marked): Hammer of Wrath
                                24239's SpellVisual 7250 (the holy hammer missile, Speed 20, a big holy burst), thrown
                                so it lands as the 3 s ring ends.
  205967  Hammer of Judgement   SP1 / SP2 rider: a 1.5 s stun on every other player hit (Hammer of Justice 5588's
                                SpellVisual 322: fist impact and stun swirl). Dispel none.
  205968  Ricochet              SP2 (heroic) resolve copy (Holy), as 205965.
  205969  Ricochet              SP2 (heroic) the bounce target's own 10%, as 205966.
  205970  Consecration          SP3 resolve copy (Holy): the lingering pool's 1 s tick, 5%.
  205971  Consecration          SP3 normal: the 10 s holy ground (Consecration 32773's SpellVisual 5600, 8 yd), a
                                dynamic object Springvale casts at the pool (his own pools and the Altar's).
  205972  Consecration          SP3 heroic: the same look for 40 s.
  205973  Holy Light            SP4 / SP9: a copy of 1026 (never the player id): 2.5 s, interruptible (InterruptFlags
                                15, PreventionType silence), heals 5% of the target's maximum health (HEAL_PCT),
                                SpellVisual 2936. On the descriptor's interrupt list.
  205974  Searing Light         SP5 (heroic): 15% Holy to every player within 100 yd (players only;
                                spell_sfk_springvale_searing_light), Holy Fire 14914's SpellVisual 3400 on each.
  205975  Unbreakable Oath      SP6: damage taken -90% (all schools) until the script removes it, Divine Shield
                                33581's SpellVisual 154 (the golden bubble). Not immunity (user ruling).
  205976  Cracked Oath          SP6: one stack per guardsman killed while the Oath holds (a DUMMY the boss frame
                                shows; the third kill shatters the Oath instead).
  205977  Oathbroken            SP7: damage taken +25% for 6 s, on the shatter.
  205978  Wrath of God          SP8 (heroic): the 30 s cast bar (Holy Wrath 28883's SpellVisual 12986). Not
                                interruptible (InterruptFlags 0, PreventionType 0): only the shatter stops it.
  205979  Wrath of God          SP8 (heroic): the kill on every player when the cast finishes (INSTAKILL, through
                                Divine Shield: NO_IMMUNITIES, always hits), the same SpellVisual on each.
  205980  Risen Guardsman       SP6: the rise look on each guardsman (Raise Dead Arelas Brightstar 67705's SpellVisual
                                14312, SK's pick; an unholy rise. The VISUALS report's holy alternative is SV 41).
  205981-205989 spare.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_NO_ACTIVE_DEFENSE,
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    ATTR3_NOT_A_PROC,
    RESOLVE_RAW,
    TARGET_SRC_CASTER,
    TARGET_UNIT_SRC_AREA_ENEMY,
    TARGET_UNIT_TARGET_ENEMY,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    KIT_CREATURE,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    SP_CONSECRATION,
    SP_DIVINE_SHIELD,
    SP_HAMMER_LANDING,
    SP_HOLY_LIGHT,
    SP_RISE_UNHOLY,
    SP_SEARING_LIGHT,
    SP_WRATH_OF_GOD,
)

creature_template_columns(4278, **boss_columns('boss_commander_springvale_rework', 28))

# --- the Risen Guardsmen (300506-300508) ---------------------------------------------------------------------------

_GUARDSMAN = {
    **KIT_CREATURE, 'type': 6, 'minlevel': 20, 'maxlevel': 20, 'rank': 1, 'unit_class': 1, 'unit_flags': 32832,
    'HealthModifier': 2.0661, 'DamageModifier': 1.7, 'BaseAttackTime': 2000, 'ExperienceModifier': 1.0, 'lootid': 0,
    'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'ScriptName': 'npc_sfk_risen_guardsman',
}
_DISPLAY_WAILING_GUARDSMAN = 3226

guardsman_light_300506 = creature_template(
    300506, 'Risen Guardsman of the Light', **{**_GUARDSMAN, 'difficulty_entry_1': 310061},
)
creature_model(300506, display_id=_DISPLAY_WAILING_GUARDSMAN)

guardsman_hammer_300507 = creature_template(
    300507, 'Risen Guardsman of the Hammer', **{**_GUARDSMAN, 'difficulty_entry_1': 310062},
)
creature_model(300507, display_id=_DISPLAY_WAILING_GUARDSMAN)

guardsman_altar_300508 = creature_template(
    300508, 'Risen Guardsman of the Altar', **{**_GUARDSMAN, 'difficulty_entry_1': 310063},
)
creature_model(300508, display_id=_DISPLAY_WAILING_GUARDSMAN)

# --- spells (205965-205989) ------------------------------------------------------------------------------------------

_TARGET_DEST_DYNOBJ_ENEMY = 28
_TARGET_UNIT_TARGET_ALLY = 21
_TARGET_FLAG_DEST_LOCATION = 0x40
_EFFECT_INSTAKILL = 1           # SPELL_EFFECT_INSTAKILL (SharedDefines.h; not in lib/dsl's EffectType subset)
_MECHANIC_STUN = 12
_SCHOOL_MASK_ALL = 127

# WP-V's picks (_visuals.py, VISUALS-REPORT s13): Hammer of Wrath 24239 (holy_hammer_missile + Holy_ImpactDD_Uber),
# Consecration 32773, Holy Light 1026, Holy Fire 14914, Divine Shield 33581, Holy Wrath 28883 (Sir Zeliek), Raise Dead
# Arelas Brightstar 67705 (SK's pick). The stun's look is the report's runner-up, Hammer of Justice 5588 (FistOfJustice
# impact, StunSwirl state), "only for the stun".
_SV_HAMMER_OF_WRATH = SP_HAMMER_LANDING
_SV_HAMMER_OF_JUSTICE = 322
_SV_CONSECRATION = SP_CONSECRATION
_SV_HOLY_LIGHT = SP_HOLY_LIGHT
_SV_HOLY_FIRE = SP_SEARING_LIGHT
_SV_DIVINE_SHIELD = SP_DIVINE_SHIELD
_SV_HOLY_WRATH = SP_WRATH_OF_GOD
_SV_RAISE_DEAD = SP_RISE_UNHOLY

_ICON_HAMMER_OF_JUSTICE = 302   # 5588
_ICON_HAMMER_OF_WRATH = 42      # 24239
_ICON_CONSECRATION = 51         # 32773
_ICON_HOLY_LIGHT = 70           # 1026
_ICON_HOLY_FIRE = 156           # 14914
_ICON_DIVINE_SHIELD = 81        # 33581
_ICON_FORBEARANCE = 236         # 25771
_ICON_HOLY_WRATH = 548          # 28883
_ICON_RAISE_DEAD = 61           # 67705

_HAMMER_SPEED = 20.0            # SpringvaleLogic.h kHammerSpeed

_REF_FLAT_NOTE = ('Shadowfang Keep WP-S4: the damage is set per target by its SpellScript (OnEffectLaunchTarget '
                  'SetEffectValue = DungeonKit::RefFlat, a percent of the reference health row)')


def _ring_resolve(spell_id: int, name: str, icon: int, sp: str, desc: str):
    return resolve_copy(
        spell_id, name, School.HOLY, desc,
        f'Shadowfang Keep WP-S4, {sp}: a copy of the registry resolve spell 205001 under its own name (Holy), bound to '
        'spell_boss_mechanics_resolve: the RunOut\'s circle on the marked player filters the 100 yd target list (the '
        'marked player is never hit by his own circle) and the registry sets the damage (25%, Weakened, the stun '
        'rider 205967).',
        icon=icon)


def _marked_hit(spell_id: int, name: str, icon: int, sp: str):
    """The marked player's own 10%: one enemy target, a missile (Speed) carrying Hammer of Wrath's look."""
    return spell(
        id=spell_id, name=name, school=School.HOLY, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=TARGET_UNIT_TARGET_ENEMY,
                        potency_excluded=_REF_FLAT_NOTE)],
        spell_icon_id=icon,
        notes=f'Shadowfang Keep WP-S4, {sp}: the marked player\'s own hit, 10% Holy of the reference row '
              '(spell_sfk_springvale_hammer_marked; unavoidable healer work, no Weakened). Thrown by the Hammer\'s '
              f'source (Springvale or the Guardsman of the Hammer), triggered, Speed {_HAMMER_SPEED:g}: the script '
              'launches it so it lands as the ring ends. Hammer of Wrath 24239\'s SpellVisual 7250 (a holy hammer '
              'missile and a big holy burst on the player). The resolve attribute set (no defense, reflect, threat, '
              'LoS, crit; always hit; IGNORE_CASTER_MODIFIERS).',
        raw_overrides=kit_raw('Hurls a hammer of holy light at the target.', Speed=_HAMMER_SPEED,
                              SpellVisualID_1=_SV_HAMMER_OF_WRATH, **RESOLVE_RAW),
    )


hammer_of_judgement_205965 = _ring_resolve(205965, 'Hammer of Judgement', _ICON_HAMMER_OF_JUSTICE, 'SP1',
                                           'The hammer lands near you.')

hammer_of_judgement_marked_205966 = _marked_hit(205966, 'Hammer of Judgement', _ICON_HAMMER_OF_WRATH, 'SP1')
scripted_by(hammer_of_judgement_marked_205966, 'spell_sfk_springvale_hammer_marked')

hammer_of_judgement_stun_205967 = spell(
    id=205967, name='Hammer of Judgement', school=School.HOLY, dispel=0, mechanic=_MECHANIC_STUN,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=1500,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, mechanic=_MECHANIC_STUN,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_HAMMER_OF_JUSTICE,
    notes='Shadowfang Keep WP-S4, SP1 / SP2: the 1.5 s stun on every other player the Hammer (or Ricochet) hits, '
          'the registry rider (cast with Springvale as the original caster; inside the 2 s rule). Stun mechanic, '
          'Dispel none. Hammer of Justice 5588\'s SpellVisual 322: the fist impact and the stun swirl, so every hit '
          'shows.',
    raw_overrides=kit_raw('Stunned for $d.', 'Stunned.', CastingTimeIndex=1, SpellVisualID_1=_SV_HAMMER_OF_JUSTICE,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

ricochet_205968 = _ring_resolve(205968, 'Ricochet', _ICON_HAMMER_OF_WRATH, 'SP2 (heroic)',
                                'The ricocheting hammer lands near you.')

ricochet_marked_205969 = _marked_hit(205969, 'Ricochet', _ICON_HAMMER_OF_WRATH, 'SP2 (heroic)')
scripted_by(ricochet_marked_205969, 'spell_sfk_springvale_hammer_marked')

consecration_205970 = resolve_copy(
    205970, 'Consecration', School.HOLY, 'Holy ground burns you.',
    'Shadowfang Keep WP-S4, SP3: a copy of the registry resolve spell 205001 under its own name (Holy), bound to '
    'spell_boss_mechanics_resolve: the lingering pool\'s 1 s tick (DungeonKit::Linger, 8 yd, 5%, no slow; a '
    'lingering zone, so no Weakened).',
    icon=_ICON_CONSECRATION)


def _consecration_ground(spell_id: int, duration_ms: int, label: str):
    return spell(
        id=spell_id, name='Consecration', school=School.HOLY, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_NO_IMMUNITIES,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=duration_ms,
        effects=[Effect(type=EffectType.PERSISTENT_AREA_AURA, apply_aura=AuraType.DUMMY,
                        implicit_target_a=_TARGET_DEST_DYNOBJ_ENEMY, radius_yards=8.0)],
        spell_icon_id=_ICON_CONSECRATION,
        notes=f'Shadowfang Keep WP-S4, SP3 {label}: the holy ground of one pool, cast by Springvale at the pool\'s '
              'spot (triggered), his own and the Guardsman of the Altar\'s, so the look stays when the Altar dies. '
              'Consecration 32773\'s SpellVisual 5600 (consecration_impact_base, 23 yd at scale 1, scaled by the '
              'dynamic object\'s 8 yd radius). Its DUMMY aura is hidden and does nothing: the registry pool '
              '(205970) owns the ticks.',
        raw_overrides=kit_raw('Holy ground.', CastingTimeIndex=1, SpellVisualID_1=_SV_CONSECRATION,
                              Targets=_TARGET_FLAG_DEST_LOCATION, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


consecration_ground_205971 = _consecration_ground(205971, 10000, 'normal (10 s)')
consecration_ground_heroic_205972 = _consecration_ground(205972, 40000, 'heroic (40 s)')

holy_light_205973 = spell(
    id=205973, name='Holy Light', school=School.HOLY, cast_time_ms=2500, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=40.0, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL_PCT, base_points=4, implicit_target_a=_TARGET_UNIT_TARGET_ALLY,
                    potency_excluded='Shadowfang Keep: a percent of the target\'s own health, not a heal value')],
    spell_icon_id=_ICON_HOLY_LIGHT,
    notes='Shadowfang Keep WP-S4, SP4 / SP9: a copy of Holy Light 1026 (never the player id): 2.5 s cast, '
          'interruptible (InterruptFlags 15 and PreventionType silence, as 1026), heals 5% of the target\'s maximum '
          'health (HEAL_PCT, BasePoints 4 + DieSides 1). Springvale casts it on himself below 60%; on heroic the '
          'Guardsman of the Light casts it on Springvale or a wounded guardsman. A finished cast on heroic triggers '
          'Searing Light (205974). On the descriptor\'s interrupt list. SpellVisual 2936.',
    raw_overrides=kit_raw('Heals a friendly target for $s1% of its maximum health.', CastingTimeIndex=20,
                          InterruptFlags=15, PreventionType=1, DefenseType=1, SpellPriority=50,
                          SpellVisualID_1=_SV_HOLY_LIGHT),
)

searing_light_205974 = spell(
    id=205974, name='Searing Light', school=School.HOLY, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=TARGET_SRC_CASTER,
                    implicit_target_b=TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=100.0,
                    potency_excluded=_REF_FLAT_NOTE)],
    spell_icon_id=_ICON_HOLY_FIRE,
    notes='Shadowfang Keep WP-S4, SP5 (heroic): every finished Holy Light (Springvale\'s or the Guardsman of the '
          'Light\'s) sears every player within 100 yd of its caster for 15% Holy of the reference row (players only; '
          'spell_sfk_springvale_searing_light). Group damage, healer work, no Weakened. Holy Fire 14914\'s '
          'SpellVisual 3400 on each player. The resolve attribute set (unavoidable, exact).',
    raw_overrides=kit_raw('Sears every enemy with holy light.', SpellVisualID_1=_SV_HOLY_FIRE, **RESOLVE_RAW),
)
scripted_by(searing_light_205974, 'spell_sfk_springvale_searing_light')

unbreakable_oath_205975 = spell(
    id=205975, name='Unbreakable Oath', school=School.HOLY, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=-91,
                    misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Unbreakable Oath: a flat -90% damage taken, not a damage or heal value')],
    spell_icon_id=_ICON_DIVINE_SHIELD,
    notes='Shadowfang Keep WP-S4, SP6: Springvale\'s Oath at 30%, damage taken -90% from every school '
          '(BasePoints -91 + DieSides 1), not immunity (user ruling, handoff s10 / s7 #20): he stays attackable and '
          'keeps his threat, and burning him through it is far slower than killing the three guardsmen. Lasts until '
          'the script removes it (the shatter, the normal 30 s cap, Wrath of God). Dispel none (not purgeable). '
          'Divine Shield 33581\'s SpellVisual 154, the golden bubble.',
    raw_overrides=kit_raw('Damage taken reduced by 90% while the Risen Guardsmen stand.',
                          'Damage taken reduced by 90% while the Risen Guardsmen stand.', CastingTimeIndex=1,
                          SpellVisualID_1=_SV_DIVINE_SHIELD),
)

cracked_oath_205976 = spell(
    id=205976, name='Cracked Oath', school=School.HOLY, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_FORBEARANCE,
    notes='Shadowfang Keep WP-S4, SP6: the cracks in the Oath, one stack per Risen Guardsman killed while it holds '
          '(DungeonKit::AddStacks, CumulativeAura 3); the third kill shatters the Oath instead. A shown DUMMY so the '
          'boss frame tells the group how far they are. Dispel none.',
    raw_overrides=kit_raw('The Oath cracks with every fallen guardsman.',
                          'The Oath cracks with every fallen guardsman.', CastingTimeIndex=1, CumulativeAura=3),
)

oathbroken_205977 = spell(
    id=205977, name='Oathbroken', school=School.HOLY, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=6000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=24,
                    misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Oathbroken: a flat +25% damage taken, not a damage or heal value')],
    spell_icon_id=_ICON_FORBEARANCE,
    notes='Shadowfang Keep WP-S4, SP7: the reward for killing all three guardsmen while the Oath holds: damage taken '
          '+25% for 6 s (BasePoints 24 + DieSides 1). Not after the normal cap. Dispel none.',
    raw_overrides=kit_raw('Damage taken increased by 25%. Lasts $d.', 'Damage taken increased by 25%.',
                          CastingTimeIndex=1),
)

wrath_of_god_205978 = cast_bar(
    205978, 'Wrath of God', 30000, 'Calls down the Light on every intruder.',
    'Shadowfang Keep WP-S4, SP8 (heroic): Springvale\'s 30 s cast as the Oath goes up (a failure-driven enrage, '
    'Dungeon ruling 5). No effect: the script\'s own 30 s clock (SpringvaleLogic.h OathTimeline) lands the kill '
    '(205979). Not interruptible (InterruptFlags 0, PreventionType 0), and he is stun immune (1972): only killing '
    'the third guardsman stops it. Holy Wrath 28883\'s SpellVisual 12986 (glowing cast).',
    icon=_ICON_HOLY_WRATH, visual=_SV_HOLY_WRATH, school=School.HOLY)

wrath_of_god_kill_205979 = spell(
    id=205979, name='Wrath of God', school=School.HOLY, attributes=ATTR0_NO_ACTIVE_DEFENSE | ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0,
    effects=[Effect(type=_EFFECT_INSTAKILL, implicit_target_a=TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_HOLY_WRATH,
    notes='Shadowfang Keep WP-S4, SP8 (heroic): Wrath of God finished: the script casts this on every player in the '
          'hall (triggered), a scripted instant kill (SPELL_EFFECT_INSTAKILL). NO_IMMUNITIES (through Divine Shield '
          'and Ice Block), always hits, ignores LoS. Holy Wrath 28883\'s SpellVisual 12986 (the holy burst) on each.',
    raw_overrides=kit_raw('Kills the target.', CastingTimeIndex=1, SpellVisualID_1=_SV_HOLY_WRATH,
                          AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

guardsman_rise_205980 = self_visual(
    205980, 'Risen Guardsman', _SV_RAISE_DEAD,
    'Shadowfang Keep WP-S4, SP6: the rise look each Risen Guardsman casts on itself as it is summoned (it stays '
    'unattackable and passive for 2 s, then acts). Raise Dead Arelas Brightstar 67705\'s SpellVisual 14312 (SK\'s '
    'pick, "look to check in game": an unholy rise, SummonGhouls; the VISUALS report\'s holy alternative is '
    'Redeeming the Soul 23254\'s SV 41).',
    icon=_ICON_RAISE_DEAD, school=School.HOLY)
