"""
Scarlet Monastery build WP-D13: the Last Stand, Scarlet Commander Mograine (3976; the companies 300950-300955; the
chest GOs 301330 / 301331 are hand SQL) (.agents/plans/scarlet-monastery-build/scarlet-monastery-build.HANDOFF.md s3.5
row D13; build spec docs/dungeons/scarlet-monastery-4-cathedral.md "The Last Stand", LS0-LS7). WP-D13 owns this file
(its spells: kSpellsLastStand 213100-213149 of modules/mod-dungeon-bosses src/ScarletMonastery/ScarletMonasteryRework.h;
LastStandLogic.h names the same ids; the texts, the nave's spawn deletes and the chest are the core SQL rev
rev_last_stand_scarlet_monastery.sql).

- 3976 Scarlet Commander Mograine: boss_mograine_rework (SmartAI off: W2-SETUP's rev drops rows 0-28 and the lists
  397600-397602), the build spec's normal health (55k = HealthModifier 44.861 on the level 40 paladin class base 1,226),
  stun immunity 1972, no INSTANCE_BIND (_common.py NO_INSTANCE_BIND: the Last Stand credits by spell 212301, which the
  instance sends), the stock DamageModifier 2.6. Held back until wave 2 binds him (BIND_WAVE_2). Heroic 250k is WP-H's
  override (source/world/dungeons/scarlet_monastery.py).
- 300950-300955 the companies (CATH "Build spec": the nave's stock entries spawn outside the nave too, so the companies
  have their own): level 40 elites (heroic 60: WP-H's copies), the stock trash's classes and displays (V's picks),
  4k / 3k health on their class bases, one C++ script for the six (npc_sm_last_stand_company, the role follows the
  entry), no loot (the Last Stand's reward is the chest), XP as the stock nave gave. Declared on every wave: only
  Mograine's AI summons them, so they change nothing until W2-SETUP binds him; their script registers on every wave too
  (a declared ScriptName with no script, or the reverse, is a boot error). DamageModifier is this WP's default (rule 19:
  sized against the level 40 tank row 2,307 with the add count, not copied from stock): the melee units 2.0 (about 3%
  of the tank row a 2 s swing each: a Chapel Guard's three melee about 4.5% a second before Devotion), the casters 1.0.
  Heroic melee is WP-H's (the tier's default, tuned in T).

Spells. Every damage is a percent of the reference row (the tank row on the tank): the registry's resolve copies, the
kit's spell_dungeon_refflat_damage (hundredths in the value, heroic in EffectMiscValueB) for the Fireball, the marked
player's Hammer and the tank's Divine Storm. Every damage spell ignores caster modifiers (rule 2):

  213100  Hammer of Justice    LS4 look: the thrown silver hammer (Hammer of Wrath's missile, SV 7250), at the target
  213101  Hammer of Justice    LS4 the others in the 5 yd circle: 20% / 30% + Weakened (resolve copy, Holy)
  213102  Hammer of Justice    LS4 the marked player's own hit: 20% / 30% (refflat, Holy)
  213103  Hammer of Justice    LS4 the 2 s stun on everyone in the circle (Hammer of Justice's stun swirl, SV 322)
  213104  Divine Storm         LS5 the 2 s wind-up bar (Physical, not interruptible; the spin, SV 12006)
  213105  Divine Storm         LS5 the whirl on the others: 30% / 45% + Weakened (resolve copy, Physical)
  213106  Divine Storm         LS5 the tank's own hit: 15% / 25% of the tank row (refflat, Physical)
  213107  Devotion Aura        LS1a the Captain's buff on a company unit within 15 yd: 30% less damage taken (heroic
                               40%: the script's base point), 2.5 s re-applied every second (SV 199, lasting)
  213108  Devotion Aura        LS1a look: the Captain's rune on arrival (SV 160)
  213109  Consecration         LS1b a Monk's ground: 10% / 15% a second (resolve copy, Holy)
  213110  Consecration         LS1b look: the ground under the Monk, 6 yd, 8 s (SV 11182, a dynamic object)
  213111  Fireball             LS1c the Wizard's 2.5 s cast: 15% / 20% (refflat, Fire); interruptible
  213112  Purifying Flame      LS2 the Wizard's 2.5 s cast at a player's spot (Fire); interruptible: no circle
  213113  Purifying Flame      LS2 the 5 yd circle: 30% / 45% + Weakened (resolve copy, Fire)
  213114  Purifying Flame      LS2 the fire: 10% / 15% a second (resolve copy, Fire)
  213115  Purifying Flame      LS2 look: the fire, 5 yd, 6 s (the lava rung SV 90607, a dynamic object)
  213116  Purifying Flame      LS2 look: the heroic fire, 10 s
  213117  Greater Heal         LS3 normal: 3 s Holy, 30% of the most hurt member; interruptible (a reward)
  213118  Greater Heal         LS3 heroic: the 3 s bar (a DUMMY on the member); a cast that lands heals the company
  213119  Greater Heal         LS3 heroic missed: 50% on every member of the company
  213120  Charge               LS6 heroic: the 3 yd charge line: 45% + Weakened (resolve copy, Physical)
  213121  Charge               LS6 look: Charge's run (SV 867)
  213122-213149 spare.

Kept stock spells (cast as they are; none rescaled, rule 15): Crusader Strike 14518, Retribution Aura 8990 (Mograine);
Holy Strike 17143 (Champions), Kick 11978 and Thrash 3417 (Monks), Fire Shield 2601 (Wizards), Power Word: Shield 6066
(the Clergy's Chaplain), Renew 8362 (Chaplains and Abbots), Frenzy 8269 (Abbots). Retired: Hammer of Justice 5589 on the
tank (a live player override, never cast here), the Wizards' Arcane Explosion 8439, the Abbots' Heal 6064.

Visual ids are WP-V's (._visuals; every look is unconfirmed until seen in game).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    self_visual,
)
from lib.dsl.registry import (
    creature_model,
    creature_template,
    creature_template_columns,
    scripted_by,
    spell,
)

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_2,
    KIT_CREATURE,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    cast_bar,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_CAPTAIN,
    DISPLAY_CAPTAIN_ALT,
    DISPLAY_COMPANY_ABBOT,
    DISPLAY_COMPANY_CHAPLAIN,
    DISPLAY_COMPANY_CHAPLAIN_ALT,
    DISPLAY_COMPANY_MONK,
    DISPLAY_COMPANY_MONK_ALT,
    DISPLAY_COMPANY_WIZARD,
    DISPLAY_COMPANY_WIZARD_ALT,
    LS_CHARGE,
    LS_CONSECRATION,
    LS_DEVOTION,
    LS_DEVOTION_APPLY,
    LS_DIVINE_STORM,
    LS_FIREBALL,
    LS_FLAME,
    LS_FLAME_POOL,
    LS_GREATER_HEAL,
    LS_HAMMER,
    LS_HAMMER_STUN,
)

_D13 = 'Scarlet Monastery build WP-D13 (the Last Stand)'
_SCRIPT_REFFLAT = ('Scarlet Monastery: a percent of reference health in hundredths, set by the kit\'s '
                   'spell_dungeon_refflat_damage (DungeonKit::RefFlatOn)')

# Held back until wave 2 binds this boss (_common.py BIND_WAVE_2): stock until then.
if BIND_WAVE_2:
    creature_template_columns(3976, **boss_columns(
        'boss_mograine_rework', 44.861, damage_modifier=2.6, instance_bind=False,
    ))

# --- constants (LastStandLogic.h; lib/test_scarlet_monastery_last_stand.py pins each against the header) -------------

HAMMER_PCT = (2000, 3000)           # kHammerPct 20 / 30 (hundredths)
HAMMER_STUN_MS = 2000               # kHammerStunMs
HAMMER_SPEED = 20.0                 # kHammerMissileSpeed
STORM_CAST_MS = 2000                # kStormCastMs
STORM_TANK_PCT = (1500, 2500)       # kStormTankPct 15 / 25 (hundredths)
DEVOTION_PCT = 30                   # kDevotionPct normal (heroic 40: the script's base point)
DEVOTION_AURA_MS = 2500             # kDevotionAuraMs
CONSECRATION_MS = 8000              # kConsecrationMs
CONSECRATION_RADIUS = 6.0           # kConsecrationRadiusYd
FIREBALL_CAST_MS = 2500             # kFireballCastMs
FIREBALL_PCT = (1500, 2000)         # kFireballPct 15 / 20 (hundredths)
FIREBALL_SPEED = 24.0               # stock Fireball 133's
FLAME_CAST_MS = 2500                # kFlameCastMs
FLAME_RADIUS = 5.0                  # kFlameRadiusYd
FLAME_FIRE_MS = (6000, 10000)       # kFlameFireMs
GREATER_HEAL_CAST_MS = 3000         # kGreaterHealCastMs
GREATER_HEAL_PCT = 30               # kGreaterHealPct
MISSED_HEAL_PCT = 50                # kMissedHealPct
CAST_RANGE = 40.0

CHAMPION, CAPTAIN, CHAPLAIN, MONK, WIZARD, ABBOT = range(300950, 300956)
COMPANY_LEVEL = 40
COMPANY_SCRIPT = 'npc_sm_last_stand_company'
# creature_classlevelstats basehp0 at level 40 (live 2026-11-20): warrior 1,524, paladin 1,226, mage 1,077.
WARRIOR_40_BASE, PALADIN_40_BASE, MAGE_40_BASE = 1524, 1226, 1077
# Health modifiers (ceil(base x modifier) = the build spec's health: 4,000 / 3,000).
PALADIN_4K, PALADIN_3K, WARRIOR_4K, MAGE_3K = 3.2626, 2.4469, 2.6246, 2.7855
MELEE_DAMAGE_MODIFIER = 2.0
CASTER_DAMAGE_MODIFIER = 1.0
# WP-H's heroic entries (STAGE-H-REPORT section 3, the mint table: the 30 kit units in entry order; source/world/
# heroic_ids.lock after the write run). Every lower-numbered unit is declared, so the run mints exactly these ids
# (W2-SETUP's reconcile; lib/test_scarlet_monastery_heroic.py KIT_HEROIC_ID names the same ids).
HEROIC_TABLE = {CHAMPION: 310481, CAPTAIN: 310482, CHAPLAIN: 310483, MONK: 310484, WIZARD: 310485, ABBOT: 310486}
HEROIC_ENTRIES = dict(HEROIC_TABLE)


def _heroic(entry: int) -> dict:
    """difficulty_entry_1 once HEROIC_ENTRIES names it (a declared full row must carry it)."""
    heroic_entry = HEROIC_ENTRIES[entry]
    return {'difficulty_entry_1': heroic_entry} if heroic_entry else {}

_CLASS_WARRIOR, _CLASS_PALADIN, _CLASS_MAGE = 1, 2, 8
_RANK_ELITE = 1
_DISPEL_MAGIC = 1
_MECHANIC_STUN = 12
_DEFENSE_MAGIC = 1
_DEFENSE_MELEE = 2
_SPELL_INTERRUPT_FLAGS_KICK = 15
_PREVENTION_SILENCE = 1
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_SCHOOL_MASK_ALL = 127
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_UNIT_TARGET_ALLY = 21
_TARGET_DEST_DYNOBJ_ENEMY = 28
_TARGET_FLAG_DEST_LOCATION = 0x40

# Stock icons (Spell.dbc SpellIconID of the named spell)
_ICON_HAMMER = 302                  # Hammer of Justice 5589
_ICON_HAMMER_THROW = 42             # Hammer of Wrath 24275
_ICON_DIVINE_STORM = 3027           # Divine Storm 53385
_ICON_DEVOTION = 291                # Devotion Aura 465
_ICON_CONSECRATION = 51             # Consecration 26573 / Raging Consecration 50915
_ICON_FIREBALL = 185                # Fireball 133
_ICON_FLAMESTRIKE = 37              # Flamestrike 2120
_ICON_GREATER_HEAL = 241            # Greater Heal 2060
_ICON_CHARGE = 457                  # Charge 100

# --- 300950-300955 the companies -------------------------------------------------------------------------------------

# The entries are written as numbers: source/world/dungeons/scarlet_monastery.py finds the declared kit units by the
# pattern `creature_template(<entry>, ...)` (WP-H) and gives them their heroic health.
_COMPANY = {
    **KIT_CREATURE, 'minlevel': COMPANY_LEVEL, 'maxlevel': COMPANY_LEVEL, 'rank': _RANK_ELITE, 'unit_flags': 0,
    'ManaModifier': 2.0, 'CreatureImmunitiesId': 0, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0,
    'maxgold': 0, 'flags_extra': 0, 'ScriptName': COMPANY_SCRIPT,
}

champion_300950 = creature_template(300950, 'Chapel Guard Champion', **{
    **_COMPANY, 'subname': 'Chapel Guard', 'unit_class': _CLASS_PALADIN, 'HealthModifier': PALADIN_4K,
    'DamageModifier': MELEE_DAMAGE_MODIFIER, **_heroic(CHAMPION),
})
creature_model(CHAMPION, display_id=DISPLAY_CAPTAIN, idx=0)
creature_model(CHAMPION, display_id=DISPLAY_CAPTAIN_ALT, idx=1)

captain_300951 = creature_template(300951, 'Captain of the Guard', **{
    **_COMPANY, 'subname': 'Chapel Guard', 'unit_class': _CLASS_PALADIN, 'HealthModifier': PALADIN_4K,
    'DamageModifier': MELEE_DAMAGE_MODIFIER, **_heroic(CAPTAIN),
})
# A Scarlet Champion with a sword and a kite shield (the script equips items 1899 + 1984, V's pick), a little bigger
# than his Champions so the kill target reads.
creature_model(CAPTAIN, display_id=DISPLAY_CAPTAIN, scale=1.1, idx=0)
creature_model(CAPTAIN, display_id=DISPLAY_CAPTAIN_ALT, scale=1.1, idx=1)

chaplain_300952 = creature_template(300952, 'Company Chaplain', **{
    **_COMPANY, 'unit_class': _CLASS_PALADIN, 'HealthModifier': PALADIN_3K,
    'DamageModifier': CASTER_DAMAGE_MODIFIER, **_heroic(CHAPLAIN),
})
creature_model(CHAPLAIN, display_id=DISPLAY_COMPANY_CHAPLAIN, idx=0)
creature_model(CHAPLAIN, display_id=DISPLAY_COMPANY_CHAPLAIN_ALT, idx=1)

monk_300953 = creature_template(300953, 'Company Monk', **{
    **_COMPANY, 'unit_class': _CLASS_WARRIOR, 'HealthModifier': WARRIOR_4K, 'ManaModifier': 1.0,
    'DamageModifier': MELEE_DAMAGE_MODIFIER, 'BaseAttackTime': 1800, **_heroic(MONK),
})
creature_model(MONK, display_id=DISPLAY_COMPANY_MONK, idx=0)
creature_model(MONK, display_id=DISPLAY_COMPANY_MONK_ALT, idx=1)

wizard_300954 = creature_template(300954, 'Company Wizard', **{
    **_COMPANY, 'unit_class': _CLASS_MAGE, 'HealthModifier': MAGE_3K, 'DamageModifier': CASTER_DAMAGE_MODIFIER,
    **_heroic(WIZARD),
})
creature_model(WIZARD, display_id=DISPLAY_COMPANY_WIZARD, idx=0)
creature_model(WIZARD, display_id=DISPLAY_COMPANY_WIZARD_ALT, idx=1)

abbot_300955 = creature_template(300955, 'Company Abbot', **{
    **_COMPANY, 'unit_class': _CLASS_PALADIN, 'HealthModifier': PALADIN_4K,
    'DamageModifier': CASTER_DAMAGE_MODIFIER, **_heroic(ABBOT),
})
creature_model(ABBOT, display_id=DISPLAY_COMPANY_ABBOT, idx=0)


def _refflat_raw(desc: str, normal_hundredths: int, heroic_hundredths: int, **more) -> dict:
    """The raw columns of a refflat damage spell: the heroic hundredths in EffectMiscValueB, the resolve set's
    attributes (always hits, cannot crit, ignores caster modifiers, no threat)."""
    return kit_raw(desc, EffectMiscValueB_1=heroic_hundredths, AttributesEx=ATTR1_NO_THREAT,
                   AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                   AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                   AttributesEx4=ATTR4_NO_CAST_LOG, **more)


def _ground_look(spell_id: int, name: str, visual: int, radius: float, duration_ms: int, notes: str):
    """A look-only dynamic object at a point (PERSISTENT_AREA_AURA, a DUMMY aura that reaches nobody: the registry's
    persistent Zone owns the ticks); cast at a point by the companies' mechanic owner, removed with it."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=duration_ms,
        effects=[Effect(type=EffectType.PERSISTENT_AREA_AURA, apply_aura=AuraType.DUMMY,
                        implicit_target_a=_TARGET_DEST_DYNOBJ_ENEMY, radius_yards=radius)],
        spell_icon_id=_ICON_CONSECRATION if visual == LS_CONSECRATION else _ICON_FLAMESTRIKE, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, Targets=_TARGET_FLAG_DEST_LOCATION,
                              InterruptFlags=0, PreventionType=0, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- LS4 Hammer of Justice -------------------------------------------------------------------------------------------

hammer_throw_213100 = spell(
    id=213100, name='Hammer of Justice', school=School.HOLY, attributes=ATTR0_DO_NOT_LOG, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_HAMMER_THROW,
    notes=f'{_D13}, LS4: the thrown hammer, a no-effect missile Mograine casts (triggered) at each marked player so '
          'it lands as the 2 s circle resolves (LastStandLogic.h HammerLaunchDelayMs: Speed 20 yd/s = '
          'kHammerMissileSpeed). Hammer of Wrath 24275\'s look (SV 7250: the hammer in hand, the silver '
          'holy_hammer_missile, the holy impact): Hammer of Justice\'s own SV 322 throws nothing (VR).',
    raw_overrides=kit_raw('Mograine hurls the Hammer of Justice.', instant=True, SpellVisualID_1=LS_HAMMER,
                          Speed=HAMMER_SPEED, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

hammer_hit_213101 = resolve_copy(
    213101, 'Hammer of Justice', School.HOLY, 'The Hammer of Justice lands.',
    f'{_D13}, LS4: the 5 yd circle on the marked player (registry Spread, tag 4; the marked player is not hit by its '
    'own circle): everyone else caught takes 20% (heroic 30%) of the reference row (the tank row on the tank), 1 '
    'Weakened and the 2 s stun rider (213103). Copy of the mod-boss-mechanics resolve spell 205002 (Holy).',
    icon=_ICON_HAMMER,
)

hammer_strike_213102 = spell(
    id=213102, name='Hammer of Justice', school=School.HOLY, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=HAMMER_PCT[0] - 1, die_sides=1,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_HAMMER,
    notes=f'{_D13}, LS4: the marked player\'s own hit as the circle resolves (the registry Spread skips its carrier): '
          '20% (heroic 30%: EffectMiscValueB) of the reference row through spell_dungeon_refflat_damage (RefFlatOn: '
          'the tank row on the tank), Holy, no Weakened (the build spec: Weakened only on the others caught). The '
          'stun (213103) follows it.',
    raw_overrides=_refflat_raw('Strikes the target for 20% of the reference health.', HAMMER_PCT[0], HAMMER_PCT[1],
                               instant=True, DefenseType=_DEFENSE_MAGIC),
)
scripted_by(hammer_strike_213102, 'spell_dungeon_refflat_damage')

hammer_stun_213103 = spell(
    id=213103, name='Hammer of Justice', school=School.HOLY, dispel=_DISPEL_MAGIC, mechanic=_MECHANIC_STUN,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=HAMMER_STUN_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, base_points=0,
                    mechanic=_MECHANIC_STUN, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_HAMMER,
    notes=f'{_D13}, LS4: the 2 s stun (the loss-of-control limit) on everyone in the circle: the registry\'s rider '
          'on the others, Mograine\'s triggered cast on the marked player. A copy (rule 15): the stock 5589 is a live '
          'player override and stuns 5 s. Stun mechanic, Magic (a dispel takes it, as the stock one); the stun swirl '
          '(SV 322). AuraInterruptFlags CHANGE_MAP; the script removes it from everyone when the stand ends.',
    raw_overrides=kit_raw('Stunned.', 'Stunned.', CastingTimeIndex=1, SpellVisualID_1=LS_HAMMER_STUN,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

# --- LS5 Divine Storm ------------------------------------------------------------------------------------------------

divine_storm_cast_213104 = cast_bar(
    213104, 'Divine Storm', STORM_CAST_MS, 'Mograine winds up a Divine Storm.',
    f'{_D13}, LS5: the 2 s wind-up of the whirl round him (8 yd, heroic 10), first 12 s after his descent and every 15 '
    's. Not interruptible (cast_bar): the registry circle (213105) and the tank\'s own hit (213106) own the damage. '
    'Physical, a school no interruptible cast of the stand uses (rule 5: Fireball and Purifying Flame are Fire, '
    'Greater Heal Holy). Divine Storm 53385\'s spin (SV 12006) plays as the bar starts.',
    icon=_ICON_DIVINE_STORM, visual=LS_DIVINE_STORM, school=School.NORMAL,
)

divine_storm_hit_213105 = resolve_copy(
    213105, 'Divine Storm', School.NORMAL, 'Mograine\'s Divine Storm.',
    f'{_D13}, LS5: the whirl on everyone in 8 yd (heroic 10) but the tank (TankExempt): 30% (heroic 45%) of the '
    'non-tank row and 1 Weakened (registry tag 5). Copy of the resolve spell 205001 (Physical).',
    icon=_ICON_DIVINE_STORM,
)

divine_storm_tank_213106 = spell(
    id=213106, name='Divine Storm', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=STORM_TANK_PCT[0] - 1, die_sides=1,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_DIVINE_STORM,
    notes=f'{_D13}, LS5: the tank\'s hit. The registry circle skips Mograine\'s victim (TankExempt), so he casts this '
          'on his victim (triggered) when the whirl lands with the victim inside it: 15% (heroic 25%: '
          'EffectMiscValueB) of the tank row through spell_dungeon_refflat_damage (RefFlatOn), Physical, armor '
          'applies, no Weakened (the tank).',
    raw_overrides=_refflat_raw('Hits the target for 15% of the tank reference health.', STORM_TANK_PCT[0],
                               STORM_TANK_PCT[1], instant=True, DefenseType=_DEFENSE_MELEE),
)
scripted_by(divine_storm_tank_213106, 'spell_dungeon_refflat_damage')

# --- LS1a Devotion Aura ----------------------------------------------------------------------------------------------

devotion_aura_213107 = spell(
    id=213107, name='Devotion Aura', school=School.HOLY, dispel=0, mechanic=0, attributes=0, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=DEVOTION_AURA_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN,
                    base_points=-DEVOTION_PCT, die_sides=0, misc_value=_SCHOOL_MASK_ALL,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY,
                    potency_excluded='Devotion Aura: a flat 30% (heroic 40%) less damage taken, not a damage value')],
    spell_icon_id=_ICON_DEVOTION,
    notes=f'{_D13}, LS1a: the Captain of the Guard\'s aura. He casts it (triggered) every second on every company unit '
          'within 15 yd, himself too: 30% less damage taken (heroic 40%: the script sets the base point, '
          'kDevotionPct), 2.5 s, so it drops a moment after he dies or the unit steps out. Not dispellable and not '
          'purgeable (Dispel none: the answer is killing him, the kill order). RighteousnessAura_Base\'s lasting '
          'ground rune (SV 199, V: Devotion Aura\'s own 160 plays once).',
    raw_overrides=kit_raw('Protected by the Captain\'s Devotion Aura.', 'Damage taken reduced by $s1%.',
                          CastingTimeIndex=1, SpellVisualID_1=LS_DEVOTION, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

devotion_pulse_213108 = self_visual(
    213108, 'Devotion Aura', LS_DEVOTION_APPLY,
    f'{_D13}, LS1a: the Captain\'s rune as he arrives (Devotion Aura 465\'s SV 160, a one-shot): the aura\'s look on '
    'the members is 213107\'s.',
    icon=_ICON_DEVOTION,
)

# --- LS1b Consecration -----------------------------------------------------------------------------------------------

consecration_hit_213109 = resolve_copy(
    213109, 'Consecration', School.HOLY, 'Consecrated ground burns the unholy.',
    f'{_D13}, LS1b: a Monk\'s ground, 6 yd for 8 s, every second: 10% (heroic 15%) of the reference row (the tank row '
    'on the tank: it drags the Monk out), no Weakened (lingering ground). Registry persistent Zone, tag 12. Copy of '
    'the resolve spell 205002 (Holy).',
    icon=_ICON_CONSECRATION,
)

consecration_ground_213110 = _ground_look(
    213110, 'Consecration', LS_CONSECRATION, CONSECRATION_RADIUS, CONSECRATION_MS,
    f'{_D13}, LS1b: the ground under a Monk (Raging Consecration 50915\'s SV 11182; VR: the same ground model as SV '
    '5600, so Thorne\'s blessed ground took the Strat holy zone instead), 6 yd, 8 s, visual only.',
)

# --- LS1c Fireball ---------------------------------------------------------------------------------------------------

fireball_213111 = spell(
    id=213111, name='Fireball', school=School.FIRE, cast_time_ms=FIREBALL_CAST_MS, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=CAST_RANGE, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=FIREBALL_PCT[0] - 1, die_sides=1,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_FIREBALL,
    notes=f'{_D13}, LS1c: each Company Wizard, 3 s after it arrives and every 8 s, a 2.5 s cast at a random player '
          '(the tank too): 15% (heroic 20%: EffectMiscValueB) of the reference row through '
          'spell_dungeon_refflat_damage, Fire, unavoidable. Interruptible (InterruptFlags 15) and silence-preventable '
          '(PreventionType 1): a reward, on the interrupt list (priority 1). Fireball 133\'s look and missile (SV 67, '
          'Speed 24).',
    raw_overrides=_refflat_raw('Hurls a fiery ball for 15% of the reference health.', FIREBALL_PCT[0],
                               FIREBALL_PCT[1], InterruptFlags=_SPELL_INTERRUPT_FLAGS_KICK,
                               PreventionType=_PREVENTION_SILENCE, DefenseType=_DEFENSE_MAGIC,
                               SpellVisualID_1=LS_FIREBALL, Speed=FIREBALL_SPEED),
)
scripted_by(fireball_213111, 'spell_dungeon_refflat_damage')

# --- LS2 Purifying Flame ---------------------------------------------------------------------------------------------

purifying_flame_cast_213112 = spell(
    id=213112, name='Purifying Flame', school=School.FIRE, cast_time_ms=FLAME_CAST_MS, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=CAST_RANGE, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_FLAMESTRIKE,
    notes=f'{_D13}, LS2: each Company Wizard, 6 s after it arrives and every 12 s, a 2.5 s cast at a random player '
          '(the tank too) that marks a 5 yd circle at the player\'s spot (registry, tag 2). The circle lands when the '
          'cast ends (the script\'s OnSpellCast detonates it); a kick (InterruptFlags 15, PreventionType 1) takes it '
          'away (OnSpellFailed): no circle. On the interrupt list (priority 2, a reward). Flamestrike 2120\'s cast '
          '(SV 10383).',
    raw_overrides=kit_raw('Calls purifying flame down on the target\'s position.',
                          InterruptFlags=_SPELL_INTERRUPT_FLAGS_KICK, PreventionType=_PREVENTION_SILENCE,
                          DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=LS_FLAME, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

purifying_flame_hit_213113 = resolve_copy(
    213113, 'Purifying Flame', School.FIRE, 'Purifying flame falls.',
    f'{_D13}, LS2: the 5 yd circle as it lands: 30% (heroic 45%) of the reference row (the tank row on the tank) and 1 '
    'Weakened (registry tag 2). Copy of the resolve spell 205003 (Fire); Flamestrike\'s burst (SV 10383) where it '
    'lands.',
    icon=_ICON_FLAMESTRIKE, visual=LS_FLAME,
)

purifying_flame_fire_213114 = resolve_copy(
    213114, 'Purifying Flame', School.FIRE, 'The purifying fire burns.',
    f'{_D13}, LS2: the fire the circle leaves, 6 s (heroic 10), every second: 10% (heroic 15%) of the reference row '
    '(the tank row on the tank), no Weakened (lingering ground), the kit\'s Standing in It slow (205201) as the '
    'rider. Registry persistent Zone, tag 22. Copy of the resolve spell 205003 (Fire).',
    icon=_ICON_FLAMESTRIKE,
)

purifying_flame_pool_213115 = _ground_look(
    213115, 'Purifying Flame', LS_FLAME_POOL, FLAME_RADIUS, FLAME_FIRE_MS[0],
    f'{_D13}, LS2: the fire on the ground, 5 yd, 6 s (normal), visual only: the shipped lava rung (SV 90607, 5 yd).',
)

purifying_flame_pool_h_213116 = _ground_look(
    213116, 'Purifying Flame', LS_FLAME_POOL, FLAME_RADIUS, FLAME_FIRE_MS[1],
    f'{_D13}, LS2: the heroic fire, 10 s; otherwise as 213115.',
)

# --- LS3 Greater Heal ------------------------------------------------------------------------------------------------

greater_heal_213117 = spell(
    id=213117, name='Greater Heal', school=School.HOLY, dispel=0, mechanic=0, cast_time_ms=GREATER_HEAL_CAST_MS,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=CAST_RANGE, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL_PCT, base_points=GREATER_HEAL_PCT, die_sides=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ALLY,
                    potency_excluded='Greater Heal: a percent of the target\'s maximum health (HEAL_PCT), not a '
                                     'scaled heal')],
    spell_icon_id=_ICON_GREATER_HEAL,
    notes=f'{_D13}, LS3 (normal): one cast per company every 10 s (5 s after it arrives): the Chapel Guard\'s '
          'Chaplain, the Clergy\'s Abbots taking turns; 3 s, 30% of the most hurt member\'s maximum health. '
          'Interruptible (InterruptFlags 15) and silence-preventable (PreventionType 1): a reward, on the interrupt '
          'list (priority 3). Holy: a kick locks the healer\'s Renew and Shield too. Heal 6064\'s look (SV 135).',
    raw_overrides=kit_raw('Heals a member of the company for 30% of its maximum health.',
                          InterruptFlags=_SPELL_INTERRUPT_FLAGS_KICK, PreventionType=_PREVENTION_SILENCE,
                          DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=LS_GREATER_HEAL),
)

greater_heal_h_213118 = spell(
    id=213118, name='Greater Heal', school=School.HOLY, dispel=0, mechanic=0, cast_time_ms=GREATER_HEAL_CAST_MS,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=CAST_RANGE, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ALLY)],
    spell_icon_id=_ICON_GREATER_HEAL,
    notes=f'{_D13}, LS3 (heroic): the same 3 s bar on the most hurt member, a DUMMY: a cast that lands (OnSpellCast) '
          'heals every living member of the company 50% (213119). The expected interrupt (priority 4). '
          'Interruptible and silence-preventable as 213117; SV 135.',
    raw_overrides=kit_raw('Heals the whole company for 50% of their maximum health.',
                          InterruptFlags=_SPELL_INTERRUPT_FLAGS_KICK, PreventionType=_PREVENTION_SILENCE,
                          DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=LS_GREATER_HEAL),
)

greater_heal_pulse_213119 = spell(
    id=213119, name='Greater Heal', school=School.HOLY, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL_PCT, base_points=MISSED_HEAL_PCT, die_sides=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ALLY,
                    potency_excluded='Greater Heal (heroic missed): a percent of the target\'s maximum health '
                                     '(HEAL_PCT), not a scaled heal')],
    spell_icon_id=_ICON_GREATER_HEAL,
    notes=f'{_D13}, LS3 (heroic missed): the healer casts it (triggered) on every living member of its company when '
          'its Greater Heal (213118) lands: 50% of each one\'s maximum health. SV 135 on each.',
    raw_overrides=kit_raw('Heals for 50% of maximum health.', instant=True, SpellVisualID_1=LS_GREATER_HEAL,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- LS6 Charge (heroic) ---------------------------------------------------------------------------------------------

charge_hit_213120 = resolve_copy(
    213120, 'Charge', School.NORMAL, 'A Chapel Guard Champion charges.',
    f'{_D13}, LS6 (heroic): each Champion of the Chapel Guard and of the Last Reserve, at its arm\'s mouth: a 3 yd '
    'line to a random player in its line of sight (handoff s7 #33 A: the lines start at the arm mouths and are '
    'clipped to LOS), 2 s, then the charge: 45% (heroic) of the reference row (the tank row on the tank) and 1 '
    'Weakened (DungeonKit::LineStrike, tag 6). Copy of the resolve spell 205001 (Physical).',
    icon=_ICON_CHARGE,
)

charge_look_213121 = self_visual(
    213121, 'Charge', LS_CHARGE,
    f'{_D13}, LS6: the Champion\'s run as its charge leaves the mouth (Charge 100\'s SV 867); the line is the marker.',
    icon=_ICON_CHARGE,
)
