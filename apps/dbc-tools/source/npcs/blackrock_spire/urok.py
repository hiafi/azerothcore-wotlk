"""
Blackrock Spire build WP-B5: Urok Doomhowl (10584), "Stolen Magic"
(.agents/plans/blackrock-spire-build/blackrock-spire-build.HANDOFF.md s3.4 rows UR, s3.5 row B5, s3.6; build spec
docs/dungeons/blackrock-spire-rework.md SP 1471-1688, UR1-UR11, rulings 37-39). WP-B5 owns this file; WP-S0 wrote the
skeleton. Its spells: kSpellsUrok 210150-210179 (modules/mod-dungeon-bosses src/BlackrockSpire/BlackrockSpireRework.h;
UrokLogic.h names the same ids); its creature: the Stolen Magic Shard 300706 (reused by WP-B9's Spirestone Champion,
WT10, with Stolen Power 210151 and the Overcharge spells 210160-210162: src/BlackrockSpire/UrokShards.h).

- 10584 Urok Doomhowl: boss_urok_doomhowl_rework (SmartAI off), normal 150k at 5 players (HealthModifier 61.425 on the
  level 60 paladin base 2,442; the flex scaler multiplies it at the pull), stun immune (1972), INSTANCE_BIND,
  DamageModifier 3.5 (the stock value; Stolen Power adds +5% a stack to his melee, Rend and Strike). Heroic 195k is
  WP-H's override (source/world/dungeons/blackrock_spire.py). Summoned only, by the tribute pile (C++), hidden through
  the prelude.
- 10601 Urok Enforcer and 10602 Urok Ogre Magus: unchanged here (stock health and SmartAI combat rows; WP-B5's SQL rev
  drops their fail and pike rows: the boss script runs the challenge).
- 300706 Stolen Magic Shard (UR3): a passive helper (KIT_HELPER: not selectable, not attackable, no XP) with the Power
  Spark creature display 26753 (V-1 DISPLAY_POWER_SPARK; it floats), npc_brs_stolen_magic_shard (a NullCreatureAI: the
  kit's CrawlPickups moves and despawns it). No heroic template (a helper runs on its normal entry).
- The tribute pile 175621 (a goober, go_brs_urok_pile) and the creature_text rows 2-5 are WP-B5's SQL rev.

Spells (looks from ._visuals, all stock ids; V-1's corrections applied: Arcane Bomb 56431 draws no missile, so the
lob is Arcane Barrage's missile SV 9947):

  210150  Warosh's Power     UR4 +5% damage and healing done a stack, 3 stacks, 20 s (the grab's flash SV 12205)
  210151  Stolen Power       UR5 +5% damage done a stack, 8 (the script holds heroic at 5), the fight
  210152  Stolen Magic       UR5 the reclaim look on Urok as a shard reaches him (Power Spark 55845's SV 12205)
  210153  Wild Bolt          UR6 the hit: resolve copy, Arcane (25% / 30% + 1 Weakened), Arcane Explosion SV 965
  210154  Wild Bolt          UR6 the missile to the spot: a no-effect cast at a point, SV 9947, Speed 30
  210155  Wild Bolt          UR6 the landing look (the new shard casts it; the Unstable burst's look too), SV 965
  210156  Doomhowl           UR7 the 2.5 s cast bar
  210157  Doomhowl           UR7 the hit: resolve copy, Physical (20% / 30% + 1 Weakened), tank exempt
  210158  Doomhowl           UR7 the 2 s fear rider (SV 247: the fear skulls)
  210159  Doomhowl           UR7 the roar's look on Urok (Intimidating Roar 16508's SV 247)
  210160  Overcharge         UR9 the 3 s cast bar (heroic), Arcane Overload 56432's SV 12303 (the bubble)
  210161  Overcharge         UR9 the hit: resolve copy, Arcane (40%, no Weakened), SV 965 on everyone hit
  210162  Overcharge         UR9 the nova's look on Urok (Mana Bomb Explosion 35513's SV 8340)
  210163  Unstable           UR10 the carrier's stacks (heroic): a DUMMY debuff, 6 s, Unstable Magic 29900's SV 969
  210164  Unstable           UR10 the rune look, re-cast on the carrier every 2.5 s (SV 969 is a 2.5 s rune)
  210165  Unstable Burst     UR10 the burst: resolve copy, Arcane (others 30% + 1 Weakened; the carrier 10% a stack,
                             no Weakened, through RegistryHit)
  210166-210179 spare
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import self_visual
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR4_NO_CAST_LOG,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_POWER_SPARK,
    UR_DOOMHOWL,
    UR_OVERCHARGE_CAST,
    UR_OVERCHARGE_HIT,
    UR_SHARD_FLASH,
    UR_UNSTABLE_MAGIC,
    UR_WILD_BOLT_LANDING,
    UR_WILD_BOLT_MISSILE,
)

_B5 = 'Blackrock Spire build WP-B5 (Urok)'

creature_template_columns(10584, **boss_columns(
    'boss_urok_doomhowl_rework', 61.425, damage_modifier=3.5,
))

# --- Constants -------------------------------------------------------------------------------------------------------
_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40

_ATTR0_DO_NOT_LOG = 0x00000100
_ATTR0_NO_IMMUNITIES = 0x20000000
_ATTR1_NO_THREAT = 0x00000400
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004

_MECHANIC_FEAR = 5
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000     # SpellDefines.h AURA_INTERRUPT_FLAG_CHANGE_MAP
_SCHOOL_MASK_ALL = 127
_FLAGS_EXTRA_NO_XP = 0x40

_ICON_ARCANE = 122          # Arcane Explosion 1449
_ICON_BARRAGE = 3376        # Arcane Barrage 44425
_ICON_FEAR = 148            # Intimidating Roar 16508
_ICON_POWER = 62            # Arcane Power 12042
_ICON_OVERLOAD = 2294       # Arcane Overload 56432
_ICON_UNSTABLE = 1910       # Unstable Magic 29900

_WAROSH_STACKS = 3          # UrokLogic.h kWaroshMaxStacks
_WAROSH_MS = 20000          # kWaroshMs
_STOLEN_POWER_CAP = 8       # kStolenPowerCap normal (heroic 5 is the script's cap)
_UNSTABLE_FUSE_MS = 6000    # kUnstableFuseMs
_UNSTABLE_STACKS = 10       # the script allows 3 (anyone grabs at 0-2, bots at 0-1); the GM test can go past it
_FEAR_MS = 2000             # kDoomhowlFearMs
_MISSILE_SPEED = 30.0       # kWildBoltMissileSpeed

# --- 300706 Stolen Magic Shard (UR3; WT10 reuses it) ----------------------------------------------------------------
stolen_magic_shard_300706 = creature_template(
    300706, 'Stolen Magic Shard', **{
        **KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1, 'type': 10,
        'flags_extra': _FLAGS_EXTRA_NO_XP, 'ScriptName': 'npc_brs_stolen_magic_shard',
    },
)
creature_model(300706, display_id=DISPLAY_POWER_SPARK)

# --- UR4 Warosh's Power, UR5 Stolen Power ----------------------------------------------------------------------------
waroshs_power_210150 = spell(
    id=210150, name="Warosh's Power", school=School.ARCANE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=_WAROSH_MS,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=5, die_sides=0,
               misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_HEALING_DONE_PERCENT, base_points=5, die_sides=0,
               misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_POWER,
    notes=f'{_B5} UR4 Warosh\'s Power: a player who walks over a Stolen Magic shard (2 yd) takes a stack (the script, '
          'DungeonKit::AddStacks on the taker): +5% damage done (every school) and +5% healing done a stack, up to 3 '
          '(+15%), 20 s, every grab refreshes it. The reward for grabbing (SP: up to +15% per player). Power Spark '
          "55845's SpellVisual 12205 (the spark burst) as the grab's flash. Dispel none.",
    raw_overrides=kit_raw('Damage and healing done increased by $s1% for $d.',
                          'Damage and healing done increased by $s1%.', instant=True, CumulativeAura=_WAROSH_STACKS,
                          AttributesEx=_ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          SpellVisualID_1=UR_SHARD_FLASH),
)

stolen_power_210151 = spell(
    id=210151, name='Stolen Power', school=School.ARCANE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=5,
                    die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_POWER,
    notes=f'{_B5} UR5 Stolen Power: a shard that reaches Urok (a prelude shard that reached the pile counts when he '
          'arrives) gives him a stack: +5% damage done a stack, up to 8 (+40%) for the rest of the fight; on heroic '
          'the script holds 5 and he Overcharges (UR9, the stacks go). It raises his melee, Rend and Strike; the '
          'percent hits ignore caster modifiers, so the reference-sized hits stay exact. WP-B9 puts the same stacks '
          'on the Spirestone Champion (WT10). Applied by the script (DungeonKit::AddStacks); no look of its own (the '
          'reclaim look is 210152). Not dispellable.',
    raw_overrides=kit_raw('Damage done increased by $s1% per application.', 'Damage done increased by $s1%.',
                          instant=True, CumulativeAura=_STOLEN_POWER_CAP, AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

shard_reclaim_210152 = self_visual(
    210152, 'Stolen Magic', UR_SHARD_FLASH,
    f'{_B5} UR5: the reclaim look, cast by Urok (or the Spirestone Champion, WT10) on himself (triggered) as a shard '
    "reaches him, with the emote line 3. Power Spark 55845's SpellVisual 12205 (the spark burst). Look only.",
    icon=_ICON_POWER, school=School.ARCANE,
)

# --- UR6 Wild Bolt ---------------------------------------------------------------------------------------------------
wild_bolt_210153 = resolve_copy(
    210153, 'Wild Bolt', School.ARCANE, 'Stolen magic, hurled clumsily.',
    f'{_B5} UR6 Wild Bolt: the blast\'s hit, a 6 yd circle at a random floor point within 8 yd of each of 1 / 2 random '
    'non-tanks (the flex count), 2 s after it is marked: 25% (heroic 30%) of the non-tank row + 1 Weakened, through '
    'the registry. Each blast leaves a Stolen Magic shard at its center. Copy of the resolve spell 205001 (Arcane). '
    "Arcane Explosion 1449's SpellVisual 965 (the blue dome) on every unit hit: the visible impact.",
    icon=_ICON_ARCANE, visual=UR_WILD_BOLT_LANDING,
)

wild_bolt_missile_210154 = spell(
    id=210154, name='Wild Bolt', school=School.ARCANE, attributes=_ATTR0_DO_NOT_LOG | _ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
    spell_icon_id=_ICON_BARRAGE,
    notes=f'{_B5} UR6: the bolt in flight to the circle\'s center, a no-effect missile Urok casts at a point '
          "(triggered). Arcane Barrage 44425's SpellVisual 9947 (V-1's correction: Arcane Bomb 56431's SV 12302 has "
          'no missile). Speed 30 yd/s = UrokLogic.h kWildBoltMissileSpeed: the script launches it so it lands when '
          'the circle resolves (LaunchDelayMs). Look only.',
    raw_overrides=kit_raw('Hurls stolen magic.', SpellVisualID_1=UR_WILD_BOLT_MISSILE, Speed=_MISSILE_SPEED,
                          Targets=_TARGET_FLAG_DEST_LOCATION, AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          CastingTimeIndex=1),
)

wild_bolt_landing_210155 = self_visual(
    210155, 'Wild Bolt', UR_WILD_BOLT_LANDING,
    f'{_B5} UR6: the landing look, cast by the new shard on itself (triggered) where the bolt lands, hit or not; also '
    "the Unstable burst's look on its carrier (UR10). Arcane Explosion 1449's SpellVisual 965. Look only.",
    icon=_ICON_ARCANE, school=School.ARCANE,
)

# --- UR7 Doomhowl ----------------------------------------------------------------------------------------------------
doomhowl_cast_210156 = cast_bar(
    210156, 'Doomhowl', 2500, 'Urok draws a deep breath.',
    f'{_B5} UR7 Doomhowl: the 2.5 s cast bar (emote line 2) while the registry circle (12 yd on him, the tank exempt) '
    'is marked; the circle owns the hit (210157). Not interruptible (Intimidating Roar was not either).',
    icon=_ICON_FEAR,
)

doomhowl_210157 = resolve_copy(
    210157, 'Doomhowl', School.NORMAL, 'A howl that strikes fear into the weak.',
    f'{_B5} UR7 Doomhowl: the howl\'s hit, everyone but his tank within 12 yd of him when the 2.5 s cast ends: 20% '
    '(heroic 30%) of the non-tank row + 1 Weakened, with the 2 s fear rider (210158), through the registry '
    '(TankExempt). From stock Intimidating Roar 16508 (an 8 s paralyze on the tank and fear around him: 4 times the '
    'loss-of-control limit, SP). Copy of the resolve spell 205001 (Physical); the fear skulls of the rider are the '
    'visible impact.',
    icon=_ICON_FEAR,
)

doomhowl_fear_210158 = spell(
    id=210158, name='Doomhowl', school=School.NORMAL, dispel=0, mechanic=_MECHANIC_FEAR,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=_FEAR_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_FEAR, base_points=0,
                    mechanic=_MECHANIC_FEAR, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_FEAR,
    notes=f'{_B5} UR7: the 2 s fear (the shared limit on loss of control) the howl applies as the registry\'s rider, '
          'cast by Urok on every unit hit. Mechanic Fear and not NO_IMMUNITIES, so a fear break (Fear Ward, Berserker '
          'Rage, Will of the Forsaken) is a reward. Dispel none: 2 s is not worth a cure. Intimidating Roar 16508\'s '
          'SpellVisual 247 (the fear skulls). AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('Terrified by the howl: runs in fear for $d.', 'Running in terror.', CastingTimeIndex=1,
                          SpellVisualID_1=UR_DOOMHOWL, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

doomhowl_look_210159 = self_visual(
    210159, 'Doomhowl', UR_DOOMHOWL,
    f'{_B5} UR7: the roar\'s look, cast by Urok on himself (triggered) as the howl lands. Intimidating Roar 16508\'s '
    'SpellVisual 247 (the roar ring; the telegraph kit\'s ring shows the real 12 yd). Look only.',
    icon=_ICON_FEAR,
)

# --- UR9 Overcharge (heroic) -----------------------------------------------------------------------------------------
overcharge_cast_210160 = cast_bar(
    210160, 'Overcharge', 3000, 'The stolen magic boils over.',
    f'{_B5} UR9 Overcharge (heroic): the 3 s cast bar (emote line 4) when Urok reaches 5 Stolen Power; the hit lands '
    'on the script\'s clock at its end (210161) and the stacks reset. Arcane Overload 56432\'s SpellVisual 12303 (the '
    'bubble on the caster, look unconfirmed). Not interruptible: the reset is the answer, not a kick. WP-B9 casts it '
    'from the Spirestone Champion too (WT10).',
    icon=_ICON_OVERLOAD, visual=UR_OVERCHARGE_CAST, school=School.ARCANE,
)

overcharge_210161 = resolve_copy(
    210161, 'Overcharge', School.ARCANE, 'The stolen magic backfires.',
    f'{_B5} UR9 Overcharge (heroic): 40% of the non-tank row (the tank row on the tank) to every player within 100 yd '
    'of the caster, no Weakened (a group failure; the reset caps it), through DungeonKit::RegistryHit '
    '(BrsStolenMagic::Overcharge, also WT10\'s). Copy of the resolve spell 205001 (Arcane). Arcane Explosion 1449\'s '
    'SpellVisual 965 on every unit hit: the visible impact.',
    icon=_ICON_ARCANE, visual=UR_WILD_BOLT_LANDING,
)

overcharge_look_210162 = self_visual(
    210162, 'Overcharge', UR_OVERCHARGE_HIT,
    f'{_B5} UR9: the nova\'s look, cast by the caster on itself (triggered) as the backfire lands. Mana Bomb '
    "Explosion 35513's SpellVisual 8340 (the arcane nova). Look only.",
    icon=_ICON_ARCANE, school=School.ARCANE,
)

# --- UR10 Unstable (heroic) ------------------------------------------------------------------------------------------
unstable_210163 = spell(
    id=210163, name='Unstable', school=School.ARCANE, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | _ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=_UNSTABLE_FUSE_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_UNSTABLE,
    notes=f'{_B5} UR10 Unstable (heroic): every shard grab adds a stack (DungeonKit::AddStacks from Urok); 6 s after '
          'the first stack (the script resets the shown time to what is left: later grabs do not reset the fuse) the '
          'carrier bursts (210165). Anyone may grab at 0 to 2 stacks (3 at most); bots claim only at 0 or 1. The '
          'stack count is what the bursts read: the carrier 10% a stack, the others within 8 yd + 2 a stack past the '
          'first. A DUMMY debuff that shows the clock: NO_IMMUNITIES (it lands through Divine Shield), dispel none. '
          "Unstable Magic 29900's SpellVisual 969 (a 2.5 s rune; 210164 re-casts it).",
    raw_overrides=kit_raw('Unstable stolen magic. Bursts after $d, hurting you and everyone near you.',
                          'Bursts when the time runs out: keep away from the group.', CastingTimeIndex=1,
                          CumulativeAura=_UNSTABLE_STACKS, AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, SpellVisualID_1=UR_UNSTABLE_MAGIC),
)

unstable_look_210164 = self_visual(
    210164, 'Unstable', UR_UNSTABLE_MAGIC,
    f'{_B5} UR10: the rune\'s look, cast by the carrier on itself (triggered) at the first stack and again every '
    "2.5 s while the fuse burns (Unstable Magic 29900's SpellVisual 969 is a 2.5 s rune: RISKY as a lasting look, "
    'V-1). Look only.',
    icon=_ICON_UNSTABLE, school=School.ARCANE,
)

unstable_burst_210165 = resolve_copy(
    210165, 'Unstable Burst', School.ARCANE, 'Stolen magic bursts out of its carrier.',
    f'{_B5} UR10 (heroic): the burst. Everyone but the carrier within 8 yd + 2 yd a stack past the first takes 30% of '
    'the row + 1 Weakened (a registry RunOut on the carrier); the carrier takes 10% a stack, no Weakened '
    '(DungeonKit::RegistryHit). Copy of the resolve spell 205001 (Arcane). Arcane Explosion 1449\'s SpellVisual 965 '
    'on every unit hit: the visible impact (the carrier also casts 210155).',
    icon=_ICON_ARCANE, visual=UR_WILD_BOLT_LANDING,
)
