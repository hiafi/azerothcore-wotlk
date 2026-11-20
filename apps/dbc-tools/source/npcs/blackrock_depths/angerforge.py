"""
Blackrock Depths build WP-D14: General Angerforge (9033; squad 300830-300832; GO 301289 (mole machine))
(.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D14; build spec
docs/dungeons/blackrock-depths-3-manufactory.md S3 "General Angerforge", AF1-AF6). WP-D14 owns this file (its spells:
kSpellsAngerforge 211300-211329 of modules/mod-dungeon-bosses src/BlackrockDepths/BlackrockDepthsRework.h;
AngerforgeLogic.h names the same ids; his texts, the mole machine's gameobject_template and the Squad Reservist's
SmartAI rows are the core SQL rev rev_angerforge_blackrock_depths.sql).

Wave 2: the wave switch (_common.py BIND_WAVE_2) holds back what rebinds a STOCK unit: Angerforge's own columns
(ANGERFORGE_COLUMNS below, registered only once the switch is on) and the three squad adds' ScriptName (an unbound name
logs "not assigned" at boot). The new entries, their models and their spells are declared either way: nothing spawns
them until the C++ binds.

- 9033 General Angerforge: bound to boss_general_angerforge_rework (modules/mod-dungeon-bosses src/BlackrockDepths/
  boss_general_angerforge_rework.cpp), SmartAI off (the stock boss has none), normal 150k at 5 players
  (HealthModifier 57.383 on the level 55 warrior class base 2,614), stun immune (1972; the stock -251 already held it:
  "add stun immunity if missing" is a no-op), INSTANCE_BIND, DamageModifier the stock 3.5 (the live 6.5 is a
  leftover). Hamstring and the 21% reinforcement call are retired (nothing casts them). Heroic 210k and the tier's
  melee are WP-H's (source/world/dungeons/blackrock_depths.py). His loot is kept.
- 300830 Anvilrage Squad Officer, 300831 Squad Reservist, 300832 Squad Medic: the boss-kit adds (S3 "Build spec"),
  each its own entry (the stock 8895, 8901 and 8894 are trash across the dungeon), level 55 (the section's one
  number), no loot, no XP (the drill brings more for the whole fight). Officer: warrior class, 10,000 health, the
  Overseer look (CDI 8754), rank 1, C++ npc_brd_squad_officer (Commanding Aura). Reservist: warrior class, 3,000
  health, the stock Reservist look (CDI 8755 at 0.9), rank 0, SmartAI (the stock 8901 kit, rev rows). Medic: mage
  class, 5,000 health, the stock Medic look (CDI 8752), rank 1, C++ npc_brd_squad_medic (Heal, Mind Blast).
  DamageModifier is this WP's default (gap 36; designer question): Officer 3.0, Reservist 1.5, Medic 1.0, about 5%,
  3% and 2% of the level 55 tank row a swing; the heroic melee is WP-H's. Heroic 15k / 4.5k / 7.5k: `difficulty_entry_1`
  310407-310409 (WP-H's predicted lock lines).

Spells (looks from ._visuals, WP-V-2's AF_* picks; every look unconfirmed until seen in game):

  211300  Mighty Blow        AF1 the kept stock 14099 (rule 15: a copy in the slice): 25% (heroic 30%) of the reference
                             row on his victim and the stock knockback
  211301  Cleave             AF2 the kept stock 20691 (a copy): 12% (heroic 15%) on everyone in a frontal arc, up to 5
  211302  Commanding Aura    AF4 the aura on each Officer: the name and the tooltip
  211303  Commanding Aura    AF4 the shield on an add within 15 yd: -50% damage taken, no kicks, no silences
  211304  Commanding Shout   look: Commanding Shout's ring and flash (SV 6506), re-cast every 5 s by an Officer
  211305  Heal               AF5 the Medic's 3 s heal on Angerforge: 5% of his maximum health
  211306  Fireburst Grenade  AF6 the mark: 5 s on a carrier, the orange rune ring under them
  211307  Fireburst Grenade  AF6 a carrier's own hit at detonation: 15% (heroic 25%) of the reference row
  211308  Fireburst Grenade  AF6 the hit on everyone else within 8 yd: 25% (heroic 40%) + Weakened (resolve copy, Fire)
  211309  Fireburst Grenade  look: Iron Grenade's bomb thrown at a carrier (SV 3819)
  211310  Deploy Mole Machine look: the dirt burst where the machine comes up (SV 9788)
  211311  Retreat            look: the burst where it goes down again (SV 9901)
  211312-211329 spare
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
    KIT_CREATURE,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    AF_COMMANDING_SHOUT,
    AF_GRENADE_MARK,
    AF_IRON_GRENADE,
    AF_MEDIC_HEAL,
    AF_MOLE_DEPLOY,
    AF_MOLE_RETREAT,
    DISPLAY_SQUAD_MEDIC,
    DISPLAY_SQUAD_OFFICER,
    DISPLAY_SQUAD_RESERVIST,
)

_D14 = 'Blackrock Depths build WP-D14 (General Angerforge)'
_SCRIPT_REFFLAT = ('Blackrock Depths: a percent of reference health in hundredths, set by the kit\'s '
                   'spell_dungeon_refflat_damage (DungeonKit::RefFlatOn)')

# --- the boss ---------------------------------------------------------------------------------------------------------

# 57.383 x the level 55 warrior base 2,614 = 150,000 (the S0 skeleton's value, kept). Held back until wave 2 binds
# (_common.py BIND_WAVE_2): stock until then.
ANGERFORGE_COLUMNS = boss_columns('boss_general_angerforge_rework', 57.383, damage_modifier=3.5)
if BIND_WAVE_2:
    creature_template_columns(9033, **ANGERFORGE_COLUMNS)

# --- constants (AngerforgeLogic.h; lib/test_blackrock_depths_angerforge.py pins each against the header) --------------

MIGHTY_BLOW = (2500, 3000)          # kMightyBlowPct 25 / 30 (hundredths)
CLEAVE = (1200, 1500)               # kCleavePct 12 / 15 (hundredths)
CLEAVE_MAX_TARGETS = 5              # kCleaveMaxTargets
CLEAVE_RADIUS_YD = 8.0              # the frontal arc's reach
GRENADE_MARKED = (1500, 2500)       # kGrenadeMarkedPct 15 / 25 (hundredths)
GRENADE_WARN_MS = 5000              # kGrenadeWarnMs
COMMANDED_PCT = -50                 # kCommandedDamageTakenPct
COMMANDED_MS = 2500                 # kCommandedMs
COMMANDING_RADIUS_YD = 15.0         # kCommandingRadiusYd (the script's pulse; the tooltip says it)
HEAL_PCT = 5                        # kHealPctOfBoss
HEAL_CAST_MS = 3000                 # kHealCastMs
HEAL_RANGE_YD = 40.0

SQUAD_LEVEL = 55                    # the section's one number (ruling 5); heroic is WP-H's
WARRIOR_55_BASE = 2614              # creature_classlevelstats basehp0, class 1 level 55 (live 2026-11-17)
MAGE_55_BASE = 1830                 # class 8 level 55
OFFICER_HEALTH, RESERVIST_HEALTH, MEDIC_HEALTH = 10_000, 3_000, 5_000   # kOfficerHealth, kReservistHealth, kMedicHealth
OFFICER_DAMAGE_MODIFIER, RESERVIST_DAMAGE_MODIFIER, MEDIC_DAMAGE_MODIFIER = 3.0, 1.5, 1.0
OFFICER, RESERVIST, MEDIC = 300830, 300831, 300832
OFFICER_HEROIC, RESERVIST_HEROIC, MEDIC_HEROIC = 310407, 310408, 310409     # WP-H's lock lines (STAGE-H-REPORT s3)
MOLE_MACHINE_GO = 301289

# The scripts the C++ registers (boss_general_angerforge_rework.cpp AddSC_): bound by data only once wave 2 is.
SQUAD_SCRIPTS = {OFFICER: 'npc_brd_squad_officer', MEDIC: 'npc_brd_squad_medic'}

_FLAGS_EXTRA_NO_XP = 0x40
_INTERRUPT_FLAGS_CAST = 15
_PREVENTION_SILENCE = 1
_PREVENTION_PACIFY = 2
_DEFENSE_MAGIC = 1
_DEFENSE_MELEE = 2
_MECHANIC_SILENCE = 9
_MECHANIC_INTERRUPT = 26
_SCHOOL_MASK_ALL = 127
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_UNIT_TARGET_ALLY = 21
_TARGET_UNIT_CONE_ENEMY_104 = 104
_TARGET_DEST_DEST = 87
_TARGET_FLAG_DEST_LOCATION = 0x40
_ATTR0_DO_NOT_DISPLAY = 0x00000080
_ATTR0_DO_NOT_LOG = 0x00000100

# Stock icons (Spell.dbc SpellIconID of the named spell)
_ICON_MIGHTY_BLOW = 314             # Mighty Blow 14099
_ICON_CLEAVE = 277                  # Cleave 20691
_ICON_COMMANDING = 332              # Commanding Shout 22440
_ICON_HEAL = 104                    # Heal 15586
_ICON_GRENADE = 37                  # Iron Grenade 4068
_ICON_MOLE = 66                     # Mole Machine Spawn 43563


def _health_modifier(target: int, base: int) -> float:
    """The HealthModifier that makes ceil(base x modifier) = target: the exact quotient cut to six digits from below
    (a rounded-up one would ceil to target + 1)."""
    return math.floor(target / base * 1_000_000) / 1_000_000


# --- the squad: 300830 Officer, 300831 Reservist, 300832 Medic --------------------------------------------------------
# The entries are written as numbers: source/world/dungeons/blackrock_depths.py finds the declared kit adds by the
# pattern `creature_template(<entry>, ...)` (WP-H) and gives them their heroic health.

squad_officer_300830 = creature_template(300830, 'Anvilrage Squad Officer', **{
    **KIT_CREATURE, 'minlevel': SQUAD_LEVEL, 'maxlevel': SQUAD_LEVEL, 'rank': 1, 'unit_class': 1, 'unit_flags': 0,
    'HealthModifier': _health_modifier(OFFICER_HEALTH, WARRIOR_55_BASE), 'DamageModifier': OFFICER_DAMAGE_MODIFIER,
    'BaseAttackTime': 2000, 'speed_run': 1.14286, 'detection_range': 20.0, 'CreatureImmunitiesId': 0,
    'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'flags_extra': _FLAGS_EXTRA_NO_XP,
    'ScriptName': SQUAD_SCRIPTS[OFFICER] if BIND_WAVE_2 else '', 'difficulty_entry_1': OFFICER_HEROIC,
})
creature_model(OFFICER, display_id=DISPLAY_SQUAD_OFFICER)

squad_reservist_300831 = creature_template(300831, 'Anvilrage Squad Reservist', **{
    **KIT_CREATURE, 'minlevel': SQUAD_LEVEL, 'maxlevel': SQUAD_LEVEL, 'rank': 0, 'unit_class': 1, 'unit_flags': 0,
    'HealthModifier': _health_modifier(RESERVIST_HEALTH, WARRIOR_55_BASE), 'DamageModifier': RESERVIST_DAMAGE_MODIFIER,
    'BaseAttackTime': 2000, 'speed_run': 1.14286, 'detection_range': 18.0, 'CreatureImmunitiesId': 0,
    'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'flags_extra': _FLAGS_EXTRA_NO_XP,
    'AIName': 'SmartAI', 'ScriptName': '', 'difficulty_entry_1': RESERVIST_HEROIC,
})
creature_model(RESERVIST, display_id=DISPLAY_SQUAD_RESERVIST, scale=0.9)

squad_medic_300832 = creature_template(300832, 'Anvilrage Squad Medic', **{
    **KIT_CREATURE, 'minlevel': SQUAD_LEVEL, 'maxlevel': SQUAD_LEVEL, 'rank': 1, 'unit_class': 8, 'unit_flags': 0,
    'HealthModifier': _health_modifier(MEDIC_HEALTH, MAGE_55_BASE), 'DamageModifier': MEDIC_DAMAGE_MODIFIER,
    'BaseAttackTime': 2000, 'speed_run': 1.14286, 'detection_range': 20.0, 'CreatureImmunitiesId': 0,
    'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0, 'flags_extra': _FLAGS_EXTRA_NO_XP,
    'ScriptName': SQUAD_SCRIPTS[MEDIC] if BIND_WAVE_2 else '', 'difficulty_entry_1': MEDIC_HEROIC,
})
creature_model(MEDIC, display_id=DISPLAY_SQUAD_MEDIC)


# --- AF1 Mighty Blow, AF2 Cleave --------------------------------------------------------------------------------------

mighty_blow_211300 = spell(
    id=211300, name='Mighty Blow', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, base_points=MIGHTY_BLOW[0] - 1, die_sides=1,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT),
        # the stock second effect, unchanged: 75-125 knockback, the vertical 10
        Effect(type=EffectType.KNOCK_BACK, base_points=74, die_sides=51, misc_value=100,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_MIGHTY_BLOW,
    notes=f'{_D14}, AF1: the stock Mighty Blow 14099 (+25 weapon, 75-125 damage, a knockback) kept and rescaled (rule '
          '15: a copy in the slice, never the shared id). Angerforge casts it (triggered) on his victim in melee '
          'reach, 8 s after the pull and every 18 s (the stock timers): Physical, 25% (heroic 30%: EffectMiscValueB) '
          'of the reference row through spell_dungeon_refflat_damage (RefFlatOn: the tank\'s row on the tank), and '
          'the stock knockback (base 74, 51 sides, vertical 100). The spec leaves the numbers to "stock rescaled" '
          '(gap 8 / 36): these are this WP\'s defaults. Always hits, cannot crit, ignores his modifiers. No look of '
          'its own: the swing is his melee animation.',
    raw_overrides=kit_raw('Inflicts damage and knocks the target back.', instant=True, DefenseType=_DEFENSE_MELEE,
                          PreventionType=_PREVENTION_PACIFY, EffectMiscValueB_1=MIGHTY_BLOW[1],
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(mighty_blow_211300, 'spell_dungeon_refflat_damage')

cleave_211301 = spell(
    id=211301, name='Cleave', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=CLEAVE[0] - 1, die_sides=1,
                    implicit_target_a=_TARGET_UNIT_CONE_ENEMY_104, radius_yards=CLEAVE_RADIUS_YD,
                    potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_CLEAVE,
    notes=f'{_D14}, AF2: the stock Cleave 20691 (weapon damage on the victim and a chain of 5) kept and rescaled '
          '(rule 15: a copy in the slice). The stock chain has no front, so the copy is a real frontal arc: everyone '
          f'in the 104 degree cone ({CLEAVE_RADIUS_YD:.0f} yd) in front of him, at most {CLEAVE_MAX_TARGETS} '
          '(MaxTargets): '
          'the tank faces him away from the group, and melee who stand behind him are never hit (S3 "Cleave: Keep ... '
          'so melee stand behind him"). Cast (triggered) at his victim in melee reach, 16 s after the pull and every '
          '9 s. Physical, 12% (heroic 15%: EffectMiscValueB) of the reference row through spell_dungeon_refflat_damage '
          '(the tank\'s row on the tank). Gap 8 / 36 default. Always hits, cannot crit, ignores his modifiers.',
    raw_overrides=kit_raw('Inflicts damage on enemies in a frontal arc.', instant=True, DefenseType=_DEFENSE_MELEE,
                          PreventionType=_PREVENTION_PACIFY, EffectMiscValueB_1=CLEAVE[1],
                          MaxTargets=CLEAVE_MAX_TARGETS, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(cleave_211301, 'spell_dungeon_refflat_damage')

# --- AF4 Commanding Aura ----------------------------------------------------------------------------------------------

commanding_aura_211302 = spell(
    id=211302, name='Commanding Aura', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_COMMANDING,
    notes=f'{_D14}, AF4: the aura on each Squad Officer (cast on itself, triggered, when it lands): the name and the '
          'tooltip players read on it, and the key of the rule. The shield itself is 211303, given every second by the '
          'Officer\'s script (npc_brd_squad_officer) to the other adds within 15 yd; the orange 15 yd ring on the '
          'floor '
          'is the registry\'s (a decoy circle on the Officer). Lasts until the Officer dies. Not dispellable.',
    raw_overrides=kit_raw('Allies within 15 yards take 50% less damage and cannot be interrupted.',
                          'Allies within 15 yards take 50% less damage and cannot be interrupted.', instant=True,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

commanded_211303 = spell(
    id=211303, name='Commanding Aura', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=COMMANDED_MS,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=COMMANDED_PCT,
               die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_TARGET_ANY,
               potency_excluded='Commanding Aura: a flat -50% damage taken, not a damage or heal value'),
        # No kick: the interrupt mechanic (Kick, Pummel, Counterspell, Shield Bash, Mind Freeze, Wind Shear carry it)
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MECHANIC_IMMUNITY, base_points=0, die_sides=0,
               misc_value=_MECHANIC_INTERRUPT, implicit_target_a=TARGET_UNIT_TARGET_ANY),
        # ... and no silence either ("their casts cannot be interrupted": a silence stops a cast just the same)
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MECHANIC_IMMUNITY, base_points=0, die_sides=0,
               misc_value=_MECHANIC_SILENCE, implicit_target_a=TARGET_UNIT_TARGET_ANY),
    ],
    spell_icon_id=_ICON_COMMANDING,
    notes=f'{_D14}, AF4: the shield. Each Squad Officer casts it (triggered) every second on every other add within 15 '
          'yd (the squad, the other Officer and the four stock Reservists; never Angerforge): -50% damage taken, '
          'immunity to the interrupt mechanic (26) and the silence mechanic (9). 2.5 s, so it ends within 2.5 s of the '
          'Officer dying (the Officer also removes its own at once) or of the add walking out of range. A second '
          'Officer\'s shield does not stack (the same effect from another caster). Not dispellable, positive, '
          'NO_IMMUNITIES. The descriptor\'s interrupt entry on the Medic\'s Heal is `Not(HasAura(211303))` and a hold '
          'on '
          'any unit with it keeps stock kicks off it. In game: confirm the Heal really shrugs off a Kick (handoff '
          '3.4 row D14). AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('Take 50% less damage and cannot be interrupted.',
                          'Damage taken reduced by 50%. Immune to interrupts.', CastingTimeIndex=1,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=ATTR3_ALWAYS_HIT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

commanding_shout_211304 = self_visual(
    211304, 'Commanding Shout', AF_COMMANDING_SHOUT,
    f'{_D14}, AF4: an Officer\'s shout, cast on itself (triggered) every 5 s while it lives: Commanding Shout 22440\'s '
    'ring and flash (SV 6506, V-1: one ring and one flash, so it is re-cast; the lasting read is the registry\'s '
    'orange ring). Look only.',
    icon=_ICON_COMMANDING,
)

# --- AF5 Medic Heal ---------------------------------------------------------------------------------------------------

heal_211305 = spell(
    id=211305, name='Heal', school=School.HOLY, dispel=0, mechanic=0, cast_time_ms=HEAL_CAST_MS, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=HEAL_RANGE_YD, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL_PCT, base_points=HEAL_PCT, die_sides=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ALLY,
                    potency_excluded='Medic Heal: a percent of the target\'s maximum health (HEAL_PCT), not a scaled '
                                     'heal')],
    spell_icon_id=_ICON_HEAL,
    notes=f'{_D14}, AF5: the Squad Medic\'s heal on Angerforge (stock Heal 15586\'s look, a new spell: the stock heal '
          'is '
          'a flat 879-1,021). 3 s cast, 5% of his maximum health (HEAL_PCT), first 6 s after the Medic lands, then '
          'every 12 s while he misses at least 5%. Interruptible (InterruptFlags 15) and silence-preventable '
          '(PreventionType 1) unless an Officer shields the Medic (211303: no kick, no silence). Holy. The '
          'descriptor\'s interrupt list names it (priority 2 normal, a reward; 3 heroic, expected). The look is Heal '
          '15586\'s SV 135.',
    raw_overrides=kit_raw('Heals Angerforge for 5% of his maximum health.',
                          InterruptFlags=_INTERRUPT_FLAGS_CAST, PreventionType=_PREVENTION_SILENCE,
                          DefenseType=_DEFENSE_MAGIC, SpellVisualID_1=AF_MEDIC_HEAL),
)

# --- AF6 Fireburst Grenade --------------------------------------------------------------------------------------------

grenade_mark_211306 = spell(
    id=211306, name='Fireburst Grenade', school=School.FIRE, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=GRENADE_WARN_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_GRENADE,
    notes=f'{_D14}, AF6: the mark. Cast by Angerforge (triggered) on each of 2 (heroic 3) players, the tank too '
          '(ruling '
          '88), when he lobs the grenade (boss emote line 2 names the player): 5 s, the orange rune ring under them '
          '(SV 90613). A DUMMY debuff, not dispellable; removed at the detonation, on a reset and on his death. '
          'AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('A grenade is coming for you. Run away from the others.',
                          'Marked: the grenade lands here when this ends.', CastingTimeIndex=1,
                          SpellVisualID_1=AF_GRENADE_MARK, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

grenade_marked_211307 = spell(
    id=211307, name='Fireburst Grenade', school=School.FIRE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=GRENADE_MARKED[0] - 1, die_sides=1,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REFFLAT)],
    spell_icon_id=_ICON_GRENADE,
    notes=f'{_D14}, AF6: a marked player\'s own hit at the detonation, 15% (heroic 25%: EffectMiscValueB) of the '
          'reference row through spell_dungeon_refflat_damage (the tank\'s row on the tank), Fire, no Weakened (the '
          'spec puts Weakened on the others). Cast (triggered) by Angerforge on each carrier when the registry\'s '
          'Spread resolves. Always hits, cannot crit, ignores his modifiers.',
    raw_overrides=kit_raw('Hurls a grenade at an enemy.', instant=True, DefenseType=_DEFENSE_MAGIC,
                          EffectMiscValueB_1=GRENADE_MARKED[1], AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_CANT_CRIT | ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(grenade_marked_211307, 'spell_dungeon_refflat_damage')

grenade_211308 = resolve_copy(
    211308, 'Fireburst Grenade', School.FIRE, 'The grenade bursts.',
    f'{_D14}, AF6: the burst on everyone else within 8 yd of a marked player, 5 s after the marks go up: 25% (heroic '
    '40%) of the reference row and 1 Weakened (registry tag 1, a Spread with the two or three carriers fixed at the '
    'throw). Copy of the mod-boss-mechanics resolve spell 205001 (Fire).',
    icon=_ICON_GRENADE,
)

grenade_look_211309 = spell(
    id=211309, name='Fireburst Grenade', school=School.FIRE, attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_GRENADE,
    notes=f'{_D14}, AF6: the bomb. Angerforge casts it (triggered) at each carrier 0.6 s before the detonation: Iron '
          'Grenade 4068\'s missile and burst (SV 3819). Look only; the hit is the registry\'s and 211307.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=AF_IRON_GRENADE, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- AF3 Deploy Mole Machine ------------------------------------------------------------------------------------------


def _look_at_point(spell_id: int, name: str, visual: int, notes: str):
    """A look-only spell cast at a point (a DUMMY aimed at a destination; DO_NOT_DISPLAY | DO_NOT_LOG), the boss's own
    cast, triggered (the Bael'Gar look shape)."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
        spell_icon_id=_ICON_MOLE, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, Targets=_TARGET_FLAG_DEST_LOCATION,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


mole_deploy_look_211310 = _look_at_point(
    211310, 'Deploy Mole Machine', AF_MOLE_DEPLOY,
    f'{_D14}, AF3: the rumble. Angerforge casts it (triggered) at the chosen spot as he yells (line 1): Mole Machine '
    'Spawn 43563\'s dirt burst and shake (SV 9788), 2 s before the machine (GO 301289) comes up. Look only.',
)

mole_retreat_look_211311 = _look_at_point(
    211311, 'Retreat', AF_MOLE_RETREAT,
    f'{_D14}, AF3: the machine goes down. Angerforge casts it (triggered) at the spot 3 s after the squad lands, as '
    'the '
    'object goes: Mole Machine Retreat 44204\'s burst and shake (SV 9901). Look only.',
)
