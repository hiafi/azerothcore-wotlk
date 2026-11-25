"""
Ragefire Chasm build WP-D4H: Starving, Taragaman's hard mode (heroic only)
(.agents/plans/ragefire-chasm-build/ragefire-chasm-build.HANDOFF.md s3.7, s3.5 row D4H, s7 #15-#18, #22, #37; build spec
docs/dungeons/ragefire-chasm-rework.md "Hard mode kit: Starving", TG7-TG9). WP-D4H owns this file. The engine side is
modules/mod-dungeon-bosses src/RagefireChasm/taragaman_hard_mode.cpp (on D4's TaragamanFight.h hooks), the pure rules
TaragamanHardModeLogic.h. His lines 7-9, the Blood Shrine 301340 and the pour spot 301341 (templates and heroic spawns)
are data/sql/updates/pending_db_world/rev_taragaman_hard_mode_ragefire_chasm.sql.

- 300987 Blood Globule (TG8): four every 20 s in phase 2, crawling from the arm ends to him at 2.5 yd/s
  (npc_rfc_blood_globule). Level 60, 6,000 health, never attacks (passive, no damage), no immunity set (a slow, a
  root or a stun holds it back), immune to taunts and knockbacks, neither calls nor answers assistance (the Enforcers
  of the bank trails stand 7 yd from the arm ends), no loot, no XP. Display 8573 (the stock crimson slime, gap 9). It
  exists on heroic only, so its normal row carries the hard mode's level and health too; its heroic entry is 310500, the
  last id of WP-H's mint order (source/world/dungeons/ragefire_chasm.py `extra=`, health 6,000).

Spells (kSpellsStarving 213690-213719; TaragamanHardModeLogic.h names the same ids; looks from ._visuals, unconfirmed
until seen in game):

  213690  Hungerer's Blood   the carrier's aura from the Blood Shrine: 10 min, no effect; ends on death, off the map and
                             at logout; the pour takes it
  213691  Hungerer's Blood   the pour's look, a stalker 300988 at the lava below the -x arm
  213692  Starving           the hard mode's red aura on Taragaman from the pour; holds a wipe
  213693  Blood Lake         phase 2: the lake's red look, on four stalkers at the arm ends
  213694  Blood Burst        TG9 the burst's hit: resolve copy, Shadow, 30%
  213695  Blood Burst        TG9 the burst's look, the spot's stalker on itself
  213696-213719 spare.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import ATTR1_NO_THREAT, self_visual
from lib.dsl.registry import creature_model, creature_template, spell

from ._common import (
    ATTR0_NO_IMMUNITIES,
    ATTR4_NO_CAST_LOG,
    FACTION_SEARING_BLADE,
    FLAGS_EXTRA_DONT_CALL_ASSISTANCE,
    FLAGS_EXTRA_IGNORE_ALL_ASSISTANCE_CALLS,
    KIT_CREATURE,
    TARGET_UNIT_CASTER,
    kit_raw,
    resolve_copy,
)
from ._visuals import DISPLAY_BLOOD_GLOBULE, TG_BLOOD_LAKE, TG_GLOBULE_BURST, TG_HM_AURA, TG_POUR

_D4H = 'Ragefire Chasm build WP-D4H (Starving, Taragaman\'s hard mode)'

# --- constants (RagefireChasmRework.h namespace Taragaman; lib/test_ragefire_chasm_taragaman_hard_mode.py pins each) --

GLOBULE_HEALTH = 6000               # kGlobuleHealth
HUNGERERS_BLOOD_MS = 600000         # kHungerersBloodMs

# WP-H's mint order (STAGE-H s3): 8996, 11318-11324, 11517-11520, then 300987, from 310488.
BLOOD_GLOBULE_HEROIC = 310500

_BASE_HP_60_WARRIOR = 3052          # creature_classlevelstats level 60 class 1 basehp0 (live 2026-11-24)
_CLASS_WARRIOR = 1
_LEVEL = 60
_CREATURE_TYPE_NOT_SPECIFIED = 10
_FLAGS_EXTRA_NO_XP = 0x00000040
_FLAGS_EXTRA_NO_TAUNT = 0x00000100
_FLAGS_EXTRA_IMMUNITY_KNOCKBACK = 0x40000000

_AURA_INTERRUPT_CHANGE_MAP = 0x00080000         # AURA_INTERRUPT_FLAG_CHANGE_MAP: leaving the map, and at logout
_ATTR1_AURA_STAYS_AFTER_COMBAT = 0x02000000     # Unit::RemoveEvadeAuras keeps it: the red aura holds a wipe

# Stock icons (Spell.dbc SpellIconID of the named spell)
_ICON_BLOOD = 541                   # Boiling Blood 38027
_ICON_STARVING = 38                 # Taste of Blood 69634

# --- the Blood Globule ------------------------------------------------------------------------------------------------

blood_globule_300987 = creature_template(300987, 'Blood Globule', **{
    **KIT_CREATURE, 'difficulty_entry_1': BLOOD_GLOBULE_HEROIC, 'faction': FACTION_SEARING_BLADE,
    'type': _CREATURE_TYPE_NOT_SPECIFIED, 'minlevel': _LEVEL, 'maxlevel': _LEVEL, 'rank': 0,
    'unit_class': _CLASS_WARRIOR, 'unit_flags': 0, 'HealthModifier': round(GLOBULE_HEALTH / _BASE_HP_60_WARRIOR, 4),
    'DamageModifier': 0.0, 'BaseAttackTime': 2000, 'CreatureImmunitiesId': 0, 'ExperienceModifier': 0.0,
    'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0,
    'flags_extra': (_FLAGS_EXTRA_NO_XP | _FLAGS_EXTRA_NO_TAUNT | _FLAGS_EXTRA_IMMUNITY_KNOCKBACK
                    | FLAGS_EXTRA_DONT_CALL_ASSISTANCE | FLAGS_EXTRA_IGNORE_ALL_ASSISTANCE_CALLS),
    'AIName': '', 'ScriptName': 'npc_rfc_blood_globule',
})
creature_model(300987, display_id=DISPLAY_BLOOD_GLOBULE)

# --- the trigger ------------------------------------------------------------------------------------------------------

hungerers_blood_213690 = spell(
    id=213690, name='Hungerer\'s Blood', school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=HUNGERERS_BLOOD_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_BLOOD,
    notes=f'{_D4H}, the trigger (s7 #15 A, #17 A): the player who uses the Blood Shrine casts it on themselves '
          '(triggered): 10 min, no effect, may be drawn again. Used at the pour spot (go_rfc_pour_spot) it sets the '
          'hard mode flag and ends for every carrier. Ends on death; dropped on a map change and at logout '
          '(AURA_INTERRUPT_FLAG_CHANGE_MAP). Not dispellable.',
    raw_overrides=kit_raw('Draws the blood the Hungerer craves.',
                          'You carry the Hungerer\'s blood. Pour it into the lava below his plateau.', instant=True,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)

pour_213691 = self_visual(
    213691, 'Hungerer\'s Blood', TG_POUR,
    f'{_D4H}, the trigger: the pour\'s look, cast (triggered) on itself by a stalker 300988 at the lava below the -x '
    'arm as the pour counts: SV 15253 (a blood rain impact). Look only.',
    icon=_ICON_BLOOD, school=School.SHADOW,
)

starving_213692 = spell(
    id=213692, name='Starving', school=School.SHADOW, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_STARVING,
    notes=f'{_D4H}: the hard mode\'s aura on Taragaman, cast on himself (triggered) at the pour. A DUMMY with no '
          'effect: the read is the hard mode red aura SV 90554 (shipped). AURA_STAYS_AFTER_COMBAT: an evade keeps it '
          '(the flag holds through wipes); after a cold load or a respawn D4\'s idle hook puts it back; a GM who '
          'clears the flag takes it off.',
    raw_overrides=kit_raw('He has tasted blood.', 'Starving: he hunts whoever bleeds most.', instant=True,
                          SpellVisualID_1=TG_HM_AURA, AttributesEx=ATTR1_NO_THREAT | _ATTR1_AURA_STAYS_AFTER_COMBAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- phase 2, the blood lake ------------------------------------------------------------------------------------------

blood_lake_213693 = spell(
    id=213693, name='Blood Lake', school=School.SHADOW, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_BLOOD,
    notes=f'{_D4H}, phase 2 (flavor): the lake\'s red look, a DUMMY aura four stalkers 300988 at the lava of the arm '
          'ends cast on themselves (triggered); they go with the fight. SV 90554 (shipped; the Ascension blood pool '
          'row 90372 is not, s7 #37 A). No effect.',
    raw_overrides=kit_raw('The lake runs red.', 'The lake runs red.', instant=True, SpellVisualID_1=TG_BLOOD_LAKE,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

burst_213694 = resolve_copy(
    213694, 'Blood Burst', School.SHADOW, 'A globule of boiling blood bursts.',
    f'{_D4H}, TG9: a Blood Globule that dies (a drunk one does not) marks a 6 yd circle where it died, 1.5 s, then 30% '
    'of the reference row, the tank row on the tank, and 1 Weakened (registry tag 17). Not his own hit: Gorged does '
    'not raise it. Copy of the resolve spell 205001 (Shadow).',
    icon=_ICON_BLOOD,
)

burst_look_213695 = self_visual(
    213695, 'Blood Burst', TG_GLOBULE_BURST,
    f'{_D4H}, TG9: the burst\'s look, cast (triggered) by the spot\'s stalker 300988 on itself as the burst lands: SV '
    '15253 (a blood rain impact). Look only.',
    icon=_ICON_BLOOD, school=School.SHADOW,
)
