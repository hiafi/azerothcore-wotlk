"""
Blackrock Depths build WP-D18: Hurley Blackbreath (9537), his Blackbreath Cronies (9541), the Thunderbrew Lager Keg
(300839) and the Lager Puddle (300840) (.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row
D18, s7 #13; build spec docs/dungeons/blackrock-depths-4-imperial-seat.md S4 "Hurley Blackbreath", HU1-HU8; rulings
59-60). WP-D18 owns this file (its spells: kSpellsHurley 211430-211459 of modules/mod-dungeon-bosses
src/BlackrockDepths/BlackrockDepthsRework.h; HurleyLogic.h names the same ids; the SmartAI drops, the 43,200 s respawn
and his texts are the core SQL rev rev_hurley_blackrock_depths.sql).

Wave 2: the wave switch (_common.py BIND_WAVE_2) holds back what rebinds a STOCK unit (Hurley's and the Cronies'
columns, HURLEY_COLUMNS and CRONY_COLUMNS below, registered only once the switch is on) and the keg's ScriptName (an
unbound name logs "not assigned" at boot). The new entries, their models and their spells are declared either way:
nothing spawns them until the C++ binds.

- 9537 Hurley Blackbreath: bound to boss_hurley_blackbreath_rework (modules/mod-dungeon-bosses
  src/BlackrockDepths/boss_hurley_blackbreath_rework.cpp), SmartAI off (the rev drops his 20 rows), normal 140k at 5
  players (HealthModifier 53.558 on the level 55 warrior class base 2,614, the S0 skeleton's value), stun immune
  (1972), INSTANCE_BIND, DamageModifier the stock 7.5 (base SQL: about 475-590 a swing; Liquid Courage adds 15% a
  stack). Hamstring, Drunken Rage and the stock Flame Breath 9573 are retired (nothing casts them). Heroic 200k and the
  tier's melee are WP-H's (source/world/dungeons/blackrock_depths.py). His loot is kept.
- 9541 Blackbreath Crony: bound to npc_blackbreath_crony_rework (s7 #13: C++ for the heroic Bottle Toss; the rev drops
  the three spawns' per-guid SmartAI), 8,000 at 5 players (HealthModifier 3.261312 on the level 53 warrior base
  2,453), DamageModifier the stock 7.5 (base SQL; a designer question), immunities kept (none). Sinister Strike 15581
  and the heroic Rupture 15583 are the stock spells (kept, not rescaled). Heroic 12k: WP-H's override.
- 300839 Thunderbrew Lager Keg: the boss-kit target (S4 "Build spec"), level 55, rank 0, 4,000 health (HealthModifier
  1.530222 on 2,614; 6,000 until a 2026-11-19 bot run showed short keg runs), not selectable until Hurley marks it
  (unit_flags NOT_SELECTABLE; the script clears it), no melee,
  rooted and passive (npc_brd_lager_keg), immunity 1972 (no fear, no stun: it never moves), no loot, no XP. On V-1's
  minted keg display CDI 90770 (`G_Keg.mdx`; the spec's 24860 is an invisible stalker, never wired). Heroic 9k:
  `difficulty_entry_1` 310414 (WP-H's predicted lock line).
- 300840 Lager Puddle: a kit helper (not selectable, not attackable, no XP) on the invisible stalker skin that carries
  the puddle's look (SV 90650, then the burning lava rung on heroic). No script, no heroic template (s7 #2).

Spells (looks from ._visuals, WP-V-1's HU_* picks; every look unconfirmed until seen in game):

  211430  Mortal Strike      HU1 the stock 16856 rescaled (rule 15: a copy): 20% (heroic 25%) of the reference row
                             (the tank row on the tank) and -50% healing taken, 5 s
  211431  Flame Breath       HU2 the 2 s bar (not interruptible: InterruptFlags 0)
  211432  Flame Breath       HU2 the cone's hit, 15 yd, 60 degrees (heroic after a drink 120): 30% (heroic 45%) +
                             Weakened on everyone but his victim (resolve copy, Fire)
  211433  Flame Breath       HU2 the tank's own hit when he stands in the arc: 10% (heroic 15%) of the tank row
  211434  Flame Breath       look: Breath of Fire 12278's cone (SV 7651)
  211435  Thunderbrew Lager  HU3 the 3 s drink at the keg: the bar and the tankard (SV 101); the script heals 10%
  211436  Liquid Courage     HU4 +15% damage done and +10% attack speed a stack, up to 6, for the fight (Berserking's
                             lasting red hands, SV 6943)
  211437  Liquid Courage     look: Drunken Rage's flash (SV 870) on each drink
  211438  Thunderbrew Lager Keg  HU3 the marked keg's orange ring (SV 90613) and the kill order's key
  211439  Lager Buzz         HU5 +10% damage done, 5 s (refreshed each second inside a puddle)
  211440  Tipsy              HU5 -30% movement speed, 1.5 s (refreshed each second inside: ends on leaving)
  211441  Lager Puddle       HU5 the puddle's amber state on its stalker (SV 90650)
  211442  Burning Lager      HU6 heroic: a burning puddle's tick, 8% a second (resolve copy, Fire)
  211443  Burning Lager      HU6 heroic: the burning state on the stalker (the 5 yd lava rung, SV 90607)
  211444  Bottle Toss        HU8 heroic: the 3 yd circle's hit, 25% + Weakened (resolve copy, Physical)
  211445  Bottle Toss        look: Throw Bottle 43291's bottle and splat (SV 9741) at the spot
  211446-211459 spare
"""

import math

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_2,
    IMMUNITY_BOSS_STUN,
    KIT_CREATURE,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_INVISIBLE_STALKER,
    DISPLAY_LAGER_KEG,
    HU_BOTTLE_TOSS,
    HU_BURNING_LAGER,
    HU_DRINK,
    HU_FLAME_BREATH,
    HU_KEG_MARK,
    HU_LAGER_BUZZ_FLASH,
    HU_LAGER_PUDDLE,
    HU_LIQUID_COURAGE,
    HU_TIPSY,
)

_D18 = 'Blackrock Depths build WP-D18 (Hurley Blackbreath)'
_SCRIPT_REFFLAT = ('Blackrock Depths: a percent of reference health in hundredths, set by the kit\'s '
                   'spell_dungeon_refflat_damage (DungeonKit::RefFlatOn)')

# --- constants (HurleyLogic.h; lib/test_blackrock_depths_hurley.py pins each against the header) ----------------------

HURLEY = 9537
CRONY = 9541
KEG = 300839
PUDDLE = 300840
KEG_HEROIC = 310414                 # WP-H's lock line (STAGE-H-REPORT s3)
WARRIOR_55_BASE = 2614              # creature_classlevelstats level 55, class 1 (basehp0)
WARRIOR_53_BASE = 2453              # level 53
HURLEY_HEALTH = 140_000             # kHurleyHealth normal
CRONY_HEALTH = 8_000                # kCronyHealth normal
KEG_HEALTH = 4_000                  # kKegHealth normal
KEG_LEVEL = 55
KEG_COUNT = 6                       # kKegCount (Liquid Courage's cap)

MORTAL_STRIKE = (2000, 2500)        # kMortalStrikePct 20 / 25 (hundredths)
MORTAL_STRIKE_MS = 5000             # kMortalStrikeMs
MORTAL_STRIKE_HEALING_PCT = 50      # kMortalStrikeHealingPct
BREATH_TANK = (1000, 1500)          # kBreathTankPct 10 / 15 (hundredths)
BREATH_CAST_MS = 2000               # kBreathCastMs
DRINK_MS = 3000                     # kDrinkMs
COURAGE_DAMAGE_PCT = 15             # kCourageDamagePct
COURAGE_HASTE_PCT = 10              # kCourageHastePct
LAGER_BUZZ_PCT = 10                 # kLagerBuzzPct
LAGER_BUZZ_MS = 5000                # kLagerBuzzMs
TIPSY_PCT = 30                      # kTipsyPct
TIPSY_MS = 1500                     # kTipsyMs
BOTTLE_SPEED = 20.0                 # the look's missile, yd/s: a Crony 10-25 yd off lands it inside the 1.5 s marker

_FLAGS_EXTRA_NO_XP = 0x40
_UNIT_FLAG_NOT_SELECTABLE = 0x02000000
_CREATURE_TYPE_NOT_SPECIFIED = 10
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40
_DEFENSE_MAGIC = 1
_DEFENSE_MELEE = 2
_MECHANIC_SNARE = 11
_SCHOOL_MASK_ALL = 127
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_ATTR0_DO_NOT_LOG = 0x00000100

# Stock icons (Spell.dbc SpellIconID of the named spell)
_ICON_MORTAL_STRIKE = 564           # Mortal Strike 16856
_ICON_BREATH_OF_FIRE = 937          # Breath of Fire 12278
_ICON_THUNDERBREW = 1313            # Thunderbrew Lager 5257
_ICON_DRUNKEN_RAGE = 95             # Drunken Rage 14822
_ICON_DRUNKEN_STUPOR = 1314         # Drunken Stupor 14870 (the icon only; its SV 2816 is a stun swirl, never wired)
_ICON_CHUCK_MUG = 1513              # Chuck Mug 50276


def _health_modifier(target: int, base: int) -> float:
    """The HealthModifier that makes ceil(base x modifier) = target: the exact quotient cut to six digits from below
    (a rounded-up one would ceil to target + 1)."""
    return math.floor(target / base * 1_000_000) / 1_000_000


# --- the stock units (held back until wave 2 binds them: _common.py BIND_WAVE_2) --------------------------------------

# 53.558 x the level 55 warrior base 2,614 = 140,000 (the S0 skeleton's value, kept).
HURLEY_COLUMNS = boss_columns('boss_hurley_blackbreath_rework', 53.558, damage_modifier=7.5)
CRONY_COLUMNS = {
    'ScriptName': 'npc_blackbreath_crony_rework',
    'AIName': '',
    'HealthModifier': _health_modifier(CRONY_HEALTH, WARRIOR_53_BASE),
    'DamageModifier': 7.5,
}
if BIND_WAVE_2:
    creature_template_columns(HURLEY, **HURLEY_COLUMNS)
    creature_template_columns(CRONY, **CRONY_COLUMNS)

# --- 300839 Thunderbrew Lager Keg, 300840 Lager Puddle ----------------------------------------------------------------
# The entries are written as numbers: source/world/dungeons/blackrock_depths.py finds the declared kit adds by the
# pattern `creature_template(<entry>, ...)` (WP-H) and gives them their heroic health.

lager_keg_300839 = creature_template(300839, 'Thunderbrew Lager Keg', **{
    **KIT_CREATURE, 'type': _CREATURE_TYPE_NOT_SPECIFIED, 'minlevel': KEG_LEVEL, 'maxlevel': KEG_LEVEL, 'rank': 0,
    'unit_class': 1, 'unit_flags': _UNIT_FLAG_NOT_SELECTABLE,
    'HealthModifier': _health_modifier(KEG_HEALTH, WARRIOR_55_BASE), 'DamageModifier': 0.0, 'BaseAttackTime': 2000,
    'detection_range': 0.0, 'CreatureImmunitiesId': IMMUNITY_BOSS_STUN, 'lootid': 0, 'pickpocketloot': 0,
    'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'flags_extra': _FLAGS_EXTRA_NO_XP,
    'ScriptName': 'npc_brd_lager_keg' if BIND_WAVE_2 else '', 'difficulty_entry_1': KEG_HEROIC,
})
creature_model(KEG, display_id=DISPLAY_LAGER_KEG)

lager_puddle_300840 = creature_template(300840, 'Lager Puddle', **{
    **KIT_HELPER, 'minlevel': KEG_LEVEL, 'maxlevel': KEG_LEVEL, 'rank': 0, 'unit_class': 1,
})
creature_model(PUDDLE, display_id=DISPLAY_INVISIBLE_STALKER)


# --- HU1 Mortal Strike ------------------------------------------------------------------------------------------------

mortal_strike_211430 = spell(
    id=211430, name='Mortal Strike', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=MORTAL_STRIKE_MS,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=MORTAL_STRIKE[0] - 1, die_sides=1,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_HEALING_PCT,
               base_points=-MORTAL_STRIKE_HEALING_PCT, die_sides=0, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
               potency_excluded='Mortal Strike: a flat -50% healing taken, not a damage or heal value'),
    ],
    spell_icon_id=_ICON_MORTAL_STRIKE,
    notes=f'{_D18}, HU1: the stock Mortal Strike 16856 (200% weapon damage, -50% healing 5 s) rescaled (rule 15: a '
          'copy in the slice). 5-8 s after the pull, then every 8-13 s (the stock event 14), on his victim in melee '
          'range (triggered; never while he walks to a keg or drinks): 20% (heroic 25%: EffectMiscValueB) of the '
          'reference row through spell_dungeon_refflat_damage (RefFlatOn: the tank row on the tank; the spec leaves '
          'the number unset, a designer question), Physical, and -50% healing taken for 5 s. Always hits, cannot '
          'crit, ignores his modifiers (Liquid Courage grows his melee, not this). Not dispellable. No look '
          '(16856\'s SV 39 is not one of V-1\'s picks). AuraInterruptFlags CHANGE_MAP; removed when the fight ends.',
    raw_overrides=kit_raw('A vicious strike that reduces healing taken.', 'Healing taken reduced by $s2%.',
                          instant=True, DefenseType=_DEFENSE_MELEE, EffectMiscValueB_1=MORTAL_STRIKE[1],
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(mortal_strike_211430, 'spell_dungeon_refflat_damage')

# --- HU2 Flame Breath -------------------------------------------------------------------------------------------------

flame_breath_bar_211431 = cast_bar(
    211431, 'Flame Breath', BREATH_CAST_MS, 'Hurley takes a deep breath of fire.',
    f'{_D18}, HU2: Hurley\'s 2 s bar as he faces his victim, 8 s after the pull, then every 15 s (never while he walks '
    'to a keg or drinks); the registry\'s cone (211432) and the tank\'s hit (211433) land as it ends. Not '
    'interruptible (InterruptFlags 0: the spec retires the stock interruptible 9573), so no interrupt list. Fire.',
    icon=_ICON_BREATH_OF_FIRE, school=School.FIRE,
)

flame_breath_211432 = resolve_copy(
    211432, 'Flame Breath', School.FIRE, 'Hurley breathes fire down his front.',
    f'{_D18}, HU2: the cone\'s hit, 15 yd (the stock radius) and 60 degrees (this WP\'s default; heroic: 120 after a '
    'drink) down his front as the 2 s bar ends, his victim exempt (TankExempt: the tank takes 211433 instead): 30% '
    '(heroic 45%) of the reference row and 1 Weakened (registry tag 1). Heroic (Firewater): every Lager Puddle the '
    'cone touches ignites (211442). Copy of the mod-boss-mechanics resolve spell 205003 (Fire).',
    icon=_ICON_BREATH_OF_FIRE,
)

flame_breath_tank_211433 = spell(
    id=211433, name='Flame Breath', school=School.FIRE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=BREATH_TANK[0] - 1, die_sides=1,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_BREATH_OF_FIRE,
    notes=f'{_D18}, HU2: the tank\'s own hit, cast by Hurley (triggered) on his victim when the breath resolves and '
          'the victim stands in the arc (the cone skipped him, TankExempt): 10% (heroic 15%: EffectMiscValueB) of '
          'the tank row through spell_dungeon_refflat_damage, Fire. No Weakened (he is meant to face it). Always '
          'hits, cannot crit, ignores caster modifiers.',
    raw_overrides=kit_raw('Hurley breathes fire on his foe.', instant=True, DefenseType=_DEFENSE_MAGIC,
                          EffectMiscValueB_1=BREATH_TANK[1], AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(flame_breath_tank_211433, 'spell_dungeon_refflat_damage')

flame_breath_look_211434 = self_visual(
    211434, 'Flame Breath', HU_FLAME_BREATH,
    f'{_D18}, HU2: the breath\'s look, cast by Hurley on himself (triggered) as the cone resolves: Breath of Fire '
    '12278\'s cone (SV 7651).',
    icon=_ICON_BREATH_OF_FIRE, school=School.FIRE,
)

# --- HU3 / HU4 the Keg Run --------------------------------------------------------------------------------------------

drink_211435 = cast_bar(
    211435, 'Thunderbrew Lager', DRINK_MS, 'Hurley drains a keg of Thunderbrew Lager.',
    f'{_D18}, HU3: the drink. Hurley reached the marked keg before the group smashed it: a 3 s bar (he does not '
    'attack), then the script heals 10% of his maximum health (HealBySpell under this name), adds a Liquid Courage '
    'stack (211436) and drains the keg (it despawns: no puddle). The clock decides, so a refused bar changes nothing; '
    'smashing the keg during the bar stops the drink (no heal, no stack). Not interruptible. Thunderbrew Lager 5257\'s '
    'tankard in the hand and its heal glow (SV 101).',
    icon=_ICON_THUNDERBREW, visual=HU_DRINK,
)

liquid_courage_211436 = spell(
    id=211436, name='Liquid Courage', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=COURAGE_DAMAGE_PCT,
               die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
               potency_excluded='Liquid Courage: a flat +15% damage done a stack, not a damage value'),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_MELEE_HASTE, base_points=COURAGE_HASTE_PCT,
               die_sides=0, implicit_target_a=TARGET_UNIT_CASTER,
               potency_excluded='Liquid Courage: a flat +10% attack speed a stack, not a damage value'),
    ],
    spell_icon_id=_ICON_DRUNKEN_RAGE,
    notes=f'{_D18}, HU4: a stack per drink (DungeonKit::AddStacks, Hurley as caster), up to 6 (CumulativeAura: one per '
          'keg), for the rest of the fight: +15% damage done and +10% attack speed a stack (his melee grows; his '
          'spells ignore caster modifiers). Replaces the stock Drunken Rage 14872 (a 30% health trigger). Not '
          'purgeable (no purge list). Berserking\'s lasting red hands (SV 6943; the doc\'s Drunken Rage SV 870 shows '
          'once per drink, 211437). Removed on reset, evade and death.',
    raw_overrides=kit_raw('Hurley grows braver with every keg.', 'Damage done increased by $s1%. Attack speed '
                          'increased by $s2%.', instant=True, CumulativeAura=KEG_COUNT,
                          SpellVisualID_1=HU_LIQUID_COURAGE, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

courage_flash_211437 = self_visual(
    211437, 'Liquid Courage', HU_LAGER_BUZZ_FLASH,
    f'{_D18}, HU4: the roar as a drink ends (emote line 3): Drunken Rage 14822\'s one-shot flash (SV 870; V-1: the '
    'doc\'s pick, once per drink).',
    icon=_ICON_DRUNKEN_RAGE,
)

keg_mark_211438 = spell(
    id=211438, name='Thunderbrew Lager Keg', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_THUNDERBREW,
    notes=f'{_D18}, HU3: the marked keg, cast by the keg on itself (triggered) when Hurley picks it (yell 2): the '
          'orange rune ring under it (SV 90613, V-1\'s "smash this" read). The keg also turns selectable and joins '
          'the fight; the descriptor\'s kill order keys on this aura (TargetEntry when HasAura, priority 3: the keg '
          'before the Cronies and him). Unmarked kegs stay unselectable, so AoE never reaches them. Not purgeable.',
    raw_overrides=kit_raw('Hurley is going for this keg.', 'Hurley is going for this keg. Smash it first!',
                          instant=True, SpellVisualID_1=HU_KEG_MARK, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- HU5 the Lager Puddle ---------------------------------------------------------------------------------------------

lager_buzz_211439 = spell(
    id=211439, name='Lager Buzz', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=LAGER_BUZZ_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=LAGER_BUZZ_PCT,
                    die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Lager Buzz: a flat +10% damage done, not a damage or heal value')],
    spell_icon_id=_ICON_THUNDERBREW,
    notes=f'{_D18}, HU5: standing in a Lager Puddle: +10% damage done (every school) for 5 s, cast by the player on '
          'themself (triggered) the first second inside and refreshed each second after (the script refreshes the '
          'aura instead of recasting, so the flash shows once), so it lasts about 5 s after leaving. The choice of the '
          'puddle (Tipsy 211440 is the cost); no damage. Drunken Rage\'s one-shot flash (SV 870, V-1: fine for a 5 s '
          'tail). A buff, not stacking. AuraInterruptFlags CHANGE_MAP; removed when the fight ends.',
    raw_overrides=kit_raw('Spilled lager: damage done increased.', 'Damage done increased by $s1%.', instant=True,
                          SpellVisualID_1=HU_LAGER_BUZZ_FLASH, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

tipsy_211440 = spell(
    id=211440, name='Tipsy', school=School.NORMAL, dispel=0, mechanic=_MECHANIC_SNARE,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=TIPSY_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DECREASE_SPEED, base_points=-(TIPSY_PCT + 1),
                    die_sides=1, mechanic=_MECHANIC_SNARE, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_DRUNKEN_STUPOR,
    notes=f'{_D18}, HU5: the puddle\'s stagger: -30% movement speed while inside, 1.5 s, cast by the player on '
          'themself (triggered) the first second inside and refreshed each second after (no recast), so it ends '
          'within 1.5 s of leaving. A snare (mechanic 11): freedom effects clear it. Blind 2094\'s confused glyphs '
          '(SV 3440; never Drunken Stupor\'s SV 2816, a stun swirl). Not dispellable. AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('Spilled lager underfoot.', 'Movement speed reduced by $s1%.', instant=True,
                          SpellVisualID_1=HU_TIPSY, AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)


def _state(spell_id: int, name: str, visual: int, notes: str, icon: int, school: School = School.NORMAL):
    """A look that lasts: a DUMMY aura the puddle's stalker casts on itself (triggered), no effect; the stalker
    despawns with the puddle."""
    return spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(name + '.', name + '.', CastingTimeIndex=1, SpellVisualID_1=visual,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


lager_puddle_211441 = _state(
    211441, 'Lager Puddle', HU_LAGER_PUDDLE,
    f'{_D18}, HU5: the puddle\'s look on its stalker (300840) for its 30 s: the minted amber beer goo state (SV 90650, '
    'Ascension `Goo_flow_state_wheat_beer` at 0.21, about 5 yd; the tint is a designer check in game).',
    icon=_ICON_THUNDERBREW,
)

# --- HU6 Firewater (heroic) -------------------------------------------------------------------------------------------

burning_lager_211442 = resolve_copy(
    211442, 'Burning Lager', School.FIRE, 'The spilled lager is burning.',
    f'{_D18}, HU6 (heroic, Firewater): a puddle his breath touched burns for 20 s, 5 yd: a persistent registry zone '
    'ticking 8% of the reference row a second (the tank\'s row on the tank; registry tag 2; the bots\' persistent '
    'Zone). No Weakened (a lasting patch, not a single hit). Copy of the mod-boss-mechanics resolve spell 205003 '
    '(Fire).',
    icon=_ICON_BREATH_OF_FIRE,
)

burning_lager_look_211443 = _state(
    211443, 'Burning Lager', HU_BURNING_LAGER,
    f'{_D18}, HU6 (heroic): the burning puddle\'s look, replacing the amber state on the same stalker for the 20 s: '
    'the shipped 5 yd lava pool rung (SV 90607, Blackrock Spire\'s ladder).',
    icon=_ICON_BREATH_OF_FIRE, school=School.FIRE,
)

# --- HU8 Bottle Toss (heroic) -----------------------------------------------------------------------------------------

bottle_toss_211444 = resolve_copy(
    211444, 'Bottle Toss', School.NORMAL, 'A Crony smashes a bottle at your feet.',
    f'{_D18}, HU8 (heroic): each Crony, 6 s after it engages, then every 12 s: a 3 yd circle at a random player\'s '
    'spot in its fight (the tank too, ruling 88), 1.5 s: 25% of the reference row and 1 Weakened (registry tag 3, '
    'owned by Hurley: no toss while he is not fighting). Copy of the mod-boss-mechanics resolve spell 205001 '
    '(Physical).',
    icon=_ICON_CHUCK_MUG,
)

bottle_toss_look_211445 = spell(
    id=211445, name='Bottle Toss', school=School.NORMAL, attributes=_ATTR0_DO_NOT_LOG, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
    spell_icon_id=_ICON_CHUCK_MUG,
    notes=f'{_D18}, HU8: the toss\'s look, a no-effect DUMMY the Crony casts (triggered) at the circle\'s spot: Throw '
          f'Bottle 43291\'s bottle and orange splat (SV 9741; alternate Chuck Mug SV 11037). Speed {BOTTLE_SPEED} '
          'yd/s: a Crony 10-25 yd off lands it about as the 1.5 s marker resolves.',
    raw_overrides=kit_raw('', SpellVisualID_1=HU_BOTTLE_TOSS, Speed=BOTTLE_SPEED, Targets=_TARGET_FLAG_DEST_LOCATION,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, CastingTimeIndex=1),
)
