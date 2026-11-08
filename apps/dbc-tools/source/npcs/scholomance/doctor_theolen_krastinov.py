"""
Scholomance build WP-S6: Doctor Theolen Krastinov (11261), "Open-Heart Surgery"
(.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.4 rows KR, s3.5 row S6, s3.6; build spec
docs/dungeons/scholomance-rework.md SC 1703-1764). WP-S6 owns this file (its spells: kSpellsKrastinov 206225-206249 in
modules/mod-dungeon-bosses src/Scholomance/ScholomanceRework.h only; KrastinovLogic.h names the same ids).

- 11261 Doctor Theolen Krastinov: boss_doctor_theolen_krastinov_rework (SmartAI off; WP-S6's SQL rev drops stock rows
  11261: Backhand 18103, Rend 16509, Frenzy 8269 and the Talk rows, now in C++), normal HealthModifier 52.425 (160k on
  the level 60 warrior base 3,052), stun immune (1972), flags_extra 3 (INSTANCE_BIND | CIVILIAN: he fights only when
  attacked). DamageModifier 6.0: his own now (the live 11 is a mod-progression leftover); WP-T tunes it. Heroic health
  240k and the tier's melee are WP-H's heroic template 310103 (source/world/dungeons/scholomance.py).
- 300538 Work Bench: the vehicle (VehicleId 6: one seat, VehicleSeat 441, control and cast, no exit by the player). A
  prop, not selectable or attackable (KIT_HELPER), the room's own bench model (CDI 30297 undead_alchemy_table, scale
  0.7, the model of the static GO 176561 it stands on). npc_sc_work_bench (a NullCreatureAI). Its spell slot 0 is
  Wrench Free: the passenger's one button. Summoned by the fight on the pull (and by the detention lesson), never
  spawned. No heroic template (handoff s3.3).
- 300539 Failed Patient: a combat add (Diseased Ghoul display 519), 6,000 health on normal (warrior base 3,052 x
  1.96593), heroic 9,000 via WP-H's heroic template 310115 (_KIT_ADD_HEROIC; it copies the speeds); run speed
  0.514286 (3.6 yd/s: about 6 s from the south alcove to the bench; their chase runs, so speed_run sets the pace, not
  speed_walk). npc_sc_failed_patient.

Spells. The damage spells' numbers are set by the script (DungeonKit::RefFlatOn: a percent of the reference row, carried
in base point 0; the escape stab's exact amount), so every one ignores caster modifiers:

  206225  Surgeon's Hook     KR1 his 1 s cast on the patient (Scourge Hook's chain look), then the seat
  206226  Strapped Down      KR1 the bench's aura while a patient is strapped in: stacks = straps left (lesson: cuts
                             left)
  206227  Wrench Free        KR2 the bench's vehicle button (creature_template_spell 300538 slot 0), 3 s cooldown
  206228  Wrench Free        KR2 the jolt on whoever holds the saw (Kick's impact; look only)
  206229  Incision           KR3 his 1.5 s cast bar on the patient (no effect; not kickable)
  206230  Incision           KR3 a landed cut: 20% / 30% (detention 15% / 25%), a bleed cut (no armor)
  206231  Saw Descending     KR3 the bench's 1.5 s aura: the window Wrench Free must hit
  206232  Scalpel Stab       KR4 the escape: the patient stabs him for 5% of his maximum health
  206233  Stitched Wound     KR5 the patient after a success: max health -15% per stack, the fight (never saved)
  206234  Killing Frenzy     KR6 hands: attack speed +25% (heroic +40% from the script)
  206235  Grafted Eyes       KR6 eyes: the look (the script makes escapes need 4 interrupts)
  206236  Grafted Heart      KR6 heart: heals 10% / 15% of his maximum health (base point 0 from the script)
  206237  Grafted Heart      KR6 heart: the look, one stack per heart
  206238  Backhand           KR8 the 2 s tank buster: 40% / 55% of the tank row, Physical (armor applies)
  206239  Butcher's Rend     KR9 the tank's stacking bleed: 2% of the tank row per stack per 3 s, 5 stacks, 15 s
  206240  Infected Claws     KR7 the Failed Patients' light bleed: 1% per 2 s for 10 s
  206241  Claw at the Straps KR7 heroic: a Failed Patient at the bench undoes an interrupt (look)
  206242-206249 spare

Visual ids are WP-V's (._visuals; every look is unconfirmed until seen in game).
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import self_visual
from lib.dsl.registry import (
    creature_model,
    creature_spell,
    creature_template,
    creature_template_columns,
    custom_attr,
    scripted_by,
    spell,
)

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_B,
    KIT_CREATURE,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    kit_raw,
)
from ._visuals import (
    DISPLAY_FAILED_PATIENT,
    DISPLAY_WORK_BENCH,
    KR_DRAG_ONTO_BENCH,
    KR_GRAFT_EYES,
    KR_GRAFT_HANDS,
    KR_GRAFT_HEART,
    KR_INCISION,
    KR_STITCHED_WOUND,
    KR_WRENCH_FREE_IMPACT,
)

_S6 = 'Scholomance build WP-S6 (Krastinov)'

# --- Constants -------------------------------------------------------------------------------------------------------
_TARGET_UNIT_TARGET_ENEMY = 6

_ATTR0_NO_ACTIVE_DEFENSE = 0x00200000
_ATTR1_NO_REDIRECTION = 0x00000008
_ATTR1_NO_REFLECTION = 0x00000080
_ATTR1_NO_THREAT = 0x00000400
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_NOT_A_PROC = 0x00000200
_ATTR3_ALWAYS_HIT = 0x00040000

_AURA_MOD_INCREASE_HEALTH_PERCENT = 133     # SpellAuraDefines.h SPELL_AURA_MOD_INCREASE_HEALTH_PERCENT
_MECHANIC_BLEED = 15
_DEFENSE_MAGIC = 1
_DEFENSE_MELEE = 2
_VEHICLE_WORK_BENCH = 6                     # Vehicle.dbc 6: one seat, VehicleSeat 441 (control and cast, no exit)
_SPELL_ATTR0_CU_AURA_CANNOT_BE_SAVED = 0x01000000   # SpellInfo.h SpellCustomAttributes
# The Failed Patients' pace: 3.6 yd/s (about 6 s over the 21.7 yd from the rise spot to the bench), as a fraction of
# the 7 yd/s base run speed. Their chase runs (creature_template_movement Chase 0), so speed_run is the pace.
_SPEED_RUN_FAILED_PATIENT = 0.514286

_ICON_HOOK = 2735           # INV_Misc_Hook_01
_ICON_CHAINS = 180          # Spell_Frost_ChainsOfIce
_ICON_WRENCH = 1497         # INV_Misc_Wrench_01
_ICON_SAW = 2949            # INV_Misc_SawBlade_01 (the Passing Grade alternative, VISUALS-REPORT)
_ICON_KNIFE = 1505          # INV_ThrowingKnife_01
_ICON_BANDAGE = 1237        # INV_Misc_Bandage_08
_ICON_FRENZY = 95           # Frenzy 8269 (his stock frenzy)
_ICON_EYE = 1720            # INV_Misc_Eye_01
_ICON_HEART = 1840          # INV_Misc_Organ_01
_ICON_BACKHAND = 314        # Backhand 18103
_ICON_REND = 245            # Rend 16509
_ICON_CLAW = 262            # Claw 16827
_ICON_MONSTER_CLAW = 1561   # INV_Misc_MonsterClaw_04
_SV_BACKHAND = 1184         # Backhand 18103 (his stock swing)
_SV_REND = 372              # Rend 16509
_SV_CLAW = 6762             # Claw 16827

_SCRIPT_REF = ('Scholomance: base point 0 is the percent; spell_sc_krastinov_ref_hit / _ref_dot set the damage '
               '(DungeonKit::RefFlatOn: the reference row of the target)')
_SCRIPT_EXACT = 'Scholomance: base point 0 is the exact amount, computed by boss_doctor_theolen_krastinov_rework'

# The resolve-style attribute set for the scripted hits: no active defense, no redirection or reflection, ignores LoS,
# cannot crit, always hits, not a proc, ignores caster modifiers (the Pilot's lesson R1 S-1: the number is exact).
_HIT_RAW = dict(
    Attributes=_ATTR0_NO_ACTIVE_DEFENSE, AttributesEx=_ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION,
    AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
    AttributesEx3=_ATTR3_NOT_A_PROC | _ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
)

# Held back until wave B binds this boss (_common.py BIND_WAVE_B; R-A S-11): stock until then.
if BIND_WAVE_B:
    creature_template_columns(11261, **boss_columns('boss_doctor_theolen_krastinov_rework', 52.425, flags_extra=3,
                                                    DamageModifier=6.0))

    # --- Boss-kit creatures ------------------------------------------------------------------------------------------
    work_bench_300538 = creature_template(
        300538, 'Work Bench', **{**KIT_HELPER, 'minlevel': 60, 'maxlevel': 60, 'rank': 0, 'unit_class': 1,
                                 'VehicleId': _VEHICLE_WORK_BENCH, 'ScriptName': 'npc_sc_work_bench'},
    )
    creature_model(300538, display_id=DISPLAY_WORK_BENCH, scale=0.7)

    failed_patient_300539 = creature_template(
        300539, 'Failed Patient', **{
            **KIT_CREATURE, 'minlevel': 60, 'maxlevel': 60, 'rank': 1, 'type': 6, 'unit_class': 1, 'unit_flags': 0,
            'HealthModifier': 1.96593, 'DamageModifier': 1.5, 'BaseAttackTime': 2000, 'speed_walk': 1.45,
            'speed_run': _SPEED_RUN_FAILED_PATIENT,
            'ExperienceModifier': 1.0, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0,
            'ScriptName': 'npc_sc_failed_patient', 'difficulty_entry_1': 310115,
        },
    )
    creature_model(300539, display_id=DISPLAY_FAILED_PATIENT)

# --- KR1 Operation -----------------------------------------------------------------------------------------------
surgeons_hook_206225 = spell(
    id=206225, name="Surgeon's Hook", school=School.NORMAL, cast_time_ms=1000, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_HOOK,
    notes=f'{_S6} KR1 Operation: his 1 s cast on the patient (emote line 5 with it); when it ends the script straps '
          'the patient into the Work Bench seat. No effect of its own (the seat is Unit::EnterVehicle). Not '
          "kickable (InterruptFlags 0, PreventionType 0): the operation is not a group interrupt. Scourge Hook 50335's "
          'SpellVisual 11055 (the chain, CharParam 502; a short cast so it shows).',
    raw_overrides=kit_raw('Hooks a patient and drags them onto the Work Bench.', InterruptFlags=0, PreventionType=0,
                          AttributesEx=_ATTR1_NO_THREAT, AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT,
                          SpellVisualID_1=KR_DRAG_ONTO_BENCH),
)

strapped_down_206226 = spell(
    id=206226, name='Strapped Down', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_CHAINS,
    notes=f'{_S6} KR1: on the Work Bench (300538) while a patient is strapped in; the stacks are the straps left (3, '
          'or 4 after the eyes graft, minus the standing interrupts; heroic claws add them back), in detention the '
          "cuts left (3). The vehicle's auras show in the passenger's buff frame (in game: unconfirmed), and bots read "
          'it (WP-PB). Applied and changed with DungeonKit::AddStacks, removed at the end. Not passive (it must be '
          'sent to the client), number-free texts.',
    raw_overrides=kit_raw('Strapped to the Work Bench.', 'Strapped down. Wrench Free while the saw comes down.',
                          instant=True, CumulativeAura=4, AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- KR2 Wrench Free ---------------------------------------------------------------------------------------------
wrench_free_206227 = spell(
    id=206227, name='Wrench Free', school=School.NORMAL, cast_time_ms=0, cooldown_ms=3000, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_WRENCH,
    notes=f'{_S6} KR2 Wrench Free: the Work Bench\'s vehicle button (creature_template_spell 300538 slot 0; the seat '
          '441 has CAN_CONTROL + CAN_CAST, so the passenger\'s bar is this one spell). Cast by the bench (the '
          'client\'s mover), self-targeted (boarding clears the target). spell_sc_krastinov_wrench_free: refused while '
          "the bench's 3 s cooldown runs (Creature::AddSpellCooldown, which also tells the passenger; the server adds "
          "none to a vehicle's cast by itself), then the operation decides: during a cut's cast it interrupts it "
          '(3 to escape, 4 after the eyes), in a pause it is wasted. No GCD. In the client patch (the bar shows its '
          'icon and cooldown from this row).',
    raw_overrides=kit_raw('Wrench against the straps. Interrupts the Incision being cast on you; between cuts it does '
                          'nothing.', instant=True, InterruptFlags=0, PreventionType=0, StartRecoveryCategory=0,
                          StartRecoveryTime=0, AttributesEx=_ATTR1_NO_THREAT),
)
scripted_by(wrench_free_206227, 'spell_sc_krastinov_wrench_free')

if BIND_WAVE_B:
    creature_spell(300538, 0, wrench_free_206227)

wrench_impact_206228 = self_visual(
    206228, 'Wrench Free', KR_WRENCH_FREE_IMPACT,
    f'{_S6} KR2: the jolt when Wrench Free stops a cut, on whoever holds the saw (cast by him on himself, or by the '
    "bench on itself in detention; triggered). Kick 1766's SpellVisual 90 (Kick_Chest_Impact): the instant button "
    "itself shows nothing (Use Wrench 58925's look is a state kit). Look only.",
    icon=_ICON_WRENCH,
)

# --- KR3 Incision --------------------------------------------------------------------------------------------------
incision_206229 = spell(
    id=206229, name='Incision', school=School.NORMAL, cast_time_ms=1500, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_SAW,
    notes=f'{_S6} KR3 Incision: his 1.5 s cast bar on the patient, the warning the patient times Wrench Free on. No '
          'effect: the operation lands the cut (206230) when the bar ends, or stops the bar on an interrupt. Not '
          'kickable by the group (InterruptFlags 0, PreventionType 0; no pushback): Incision is the patient\'s, '
          "through the bench (SC boss data). Not cast in detention (a cast by the student's own vehicle would block "
          'Wrench Free); the bench\'s window aura (206231) is the cue there.',
    raw_overrides=kit_raw('Cuts into the patient on the Work Bench.', InterruptFlags=0, PreventionType=0,
                          AttributesEx=_ATTR1_NO_THREAT, AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT),
)

incision_hit_206230 = spell(
    id=206230, name='Incision', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=50000.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0, mechanic=_MECHANIC_BLEED,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_REF)],
    spell_icon_id=_ICON_SAW,
    notes=f'{_S6} KR3: a landed cut on the patient, cast triggered with base point 0 = the percent: 20% / 30% of the '
          'reference row (733 / 1,236), or in detention the lesson\'s failure hit 15% / 25% (550 / 1,030) plus a '
          'Weakened stack (script). Cast by him, or in detention by the lesson owner (S11\'s stalker; range '
          'unlimited). Physical with the bleed mechanic on the effect (no armor), no Weakened on the boss\'s cut '
          '(healer load, SC). Whale Dissection 45264\'s SpellVisual 10107 (BloodyExplosion) on the patient: the '
          'visible impact.',
    raw_overrides=kit_raw('A surgical cut.', instant=True, DefenseType=_DEFENSE_MAGIC, InterruptFlags=0,
                          PreventionType=0, SpellVisualID_1=KR_INCISION, AttributesEx4=ATTR4_NO_CAST_LOG,
                          **{**_HIT_RAW, 'AttributesEx': _HIT_RAW['AttributesEx'] | _ATTR1_NO_THREAT}),
)
scripted_by(incision_hit_206230, 'spell_sc_krastinov_ref_hit')

saw_descending_206231 = spell(
    id=206231, name='Saw Descending', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=1500,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_SAW,
    notes=f'{_S6} KR3: the cut window, 1.5 s, on the Work Bench (cast by the bench on itself, triggered, as each cut '
          'starts; removed when the cut lands or is interrupted). The same window as his Incision bar, and the only '
          'cue in detention, where the bench operates itself. Shows in the passenger\'s vehicle buff frame (in game: '
          'unconfirmed). The bot strategy (WP-PB) reads it: aura on my vehicle base = press Wrench Free now.',
    raw_overrides=kit_raw('The saw comes down.', 'The saw is coming down. Wrench Free now.', instant=True,
                          AttributesEx=_ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- KR4 Escape ----------------------------------------------------------------------------------------------------
scalpel_stab_206232 = spell(
    id=206232, name='Scalpel Stab', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0, mechanic=_MECHANIC_BLEED,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_EXACT)],
    spell_icon_id=_ICON_KNIFE,
    notes=f'{_S6} KR4 Escape: the straps snap and the patient drives the scalpel into him: 5% of his maximum health '
          '(8,000 normal, 12,000 heroic), base point 0 set by the operation, cast triggered by the patient on him '
          'right after the eject. Exact: ignores caster modifiers, a bleed (no armor), cannot crit, always hits; no '
          "threat (the patient must not pull him off the tank). Kick 1766's SpellVisual 90 on him.",
    raw_overrides=kit_raw('Drives the scalpel into the surgeon.', instant=True, DefenseType=_DEFENSE_MELEE,
                          InterruptFlags=0, PreventionType=0, SpellVisualID_1=KR_WRENCH_FREE_IMPACT,
                          **{**_HIT_RAW, 'AttributesEx': _HIT_RAW['AttributesEx'] | _ATTR1_NO_THREAT}),
)

# --- KR5 Success / KR6 Grafts ------------------------------------------------------------------------------------
stitched_wound_206233 = spell(
    id=206233, name='Stitched Wound', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_MOD_INCREASE_HEALTH_PERCENT, base_points=-15,
                    die_sides=0, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_BANDAGE,
    notes=f'{_S6} KR5 Success: the patient keeps a Stitched Wound: maximum health -15% per stack '
          '(SPELL_AURA_MOD_INCREASE_HEALTH_PERCENT -15, the engine multiplies by the stacks), stacking on a second '
          'operation, for the rest of the fight (the script removes it on his death, evade or reset). Added with '
          "DungeonKit::AddStacks. Not dispellable. Necrotic Strike 70659's SpellVisual 15205 (DeathKnight_"
          'PlagueStrikeState, a state kit on the aura). Never saved (SPELL_ATTR0_CU_AURA_CANNOT_BE_SAVED): a patient '
          "who logs out mid-fight misses the script's cleanup, and a saved -1 duration aura would stay until death.",
    raw_overrides=kit_raw('An organ was taken. Maximum health reduced.', 'Maximum health reduced.', instant=True,
                          CumulativeAura=10, AttributesEx=_ATTR1_NO_THREAT, SpellVisualID_1=KR_STITCHED_WOUND),
)
custom_attr(stitched_wound_206233, _SPELL_ATTR0_CU_AURA_CANNOT_BE_SAVED)

killing_frenzy_206234 = spell(
    id=206234, name='Killing Frenzy', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_MELEE_HASTE, base_points=25, die_sides=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_FRENZY,
    notes=f'{_S6} KR6 the hands graft (the first success): attack speed +25% for the rest of the fight; heroic +40% '
          '(base point 0 from the script). Emote line 4 (his stock "%s goes into a frenzy!", now a boss emote). '
          "Unholy Frenzy 8699's SpellVisual 47 (BloodLust_State_Hand on both hands). Attack speed only: the tank and "
          'healer feel it; the reference-sized hits ignore caster modifiers. Not dispellable.',
    raw_overrides=kit_raw('Grafted hands: attack speed increased.', 'Attack speed increased.', instant=True,
                          AttributesEx=_ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          SpellVisualID_1=KR_GRAFT_HANDS),
)

grafted_eyes_206235 = spell(
    id=206235, name='Grafted Eyes', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_EYE,
    notes=f'{_S6} KR6 the eyes graft (the second success): he sees the struggle coming, so later patients need 4 '
          'interrupts to escape (the script). Emote line 6. A DUMMY aura for the look: [DND] Dalaran Brilliance '
          "61332's SpellVisual 9188 (dalaran_eye_01 over the head).",
    raw_overrides=kit_raw('Grafted eyes: he sees the struggle coming.', 'Escapes need one more interrupt.',
                          instant=True, AttributesEx=_ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          SpellVisualID_1=KR_GRAFT_EYES),
)

grafted_heart_heal_206236 = spell(
    id=206236, name='Grafted Heart', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.HEAL, base_points=0, die_sides=0, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded=_SCRIPT_EXACT)],
    spell_icon_id=_ICON_HEART,
    notes=f'{_S6} KR6 the heart graft (the third success and every one after it): heals him 10% (heroic 15%) of his '
          'maximum health (16,000 / 36,000), base point 0 from the script, cast triggered on himself. Emote line 7. '
          'The look is the heart aura (206237) beside it.',
    raw_overrides=kit_raw('Sews in a fresh heart.', instant=True, InterruptFlags=0, PreventionType=0,
                          AttributesEx=_ATTR1_NO_THREAT,
                          AttributesEx3=_ATTR3_NOT_A_PROC | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

grafted_heart_206237 = spell(
    id=206237, name='Grafted Heart', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_HEART,
    notes=f'{_S6} KR6: the heart graft\'s look, one stack per heart (DungeonKit::AddStacks), the fight. Perpetual '
          "Instability 49163's SpellVisual 10883 (a pulsing floatingminepulse in the chest; Amorous 7489 is the "
          'runner-up).',
    raw_overrides=kit_raw('Grafted hearts.', 'A grafted heart beats in his chest.', instant=True, CumulativeAura=10,
                          AttributesEx=_ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG,
                          SpellVisualID_1=KR_GRAFT_HEART),
)

# --- KR8 Backhand / KR9 Butcher's Rend -------------------------------------------------------------------------------
backhand_206238 = spell(
    id=206238, name='Backhand', school=School.NORMAL, cast_time_ms=2000, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=40.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=40, die_sides=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_REF)],
    spell_icon_id=_ICON_BACKHAND,
    notes=f'{_S6} KR8 Backhand, the tank buster (stock 18103 changed: no stun): a 2 s cast on his victim that cannot '
          'be interrupted (InterruptFlags 0, PreventionType 0), then 40% (heroic 55%, base point 0 from the script) of '
          "the reference tank row (1,484 / 2,261 before armor), Physical: the tank's armor and defensives apply (set "
          'at launch, spell_sc_krastinov_ref_hit), it cannot crit (no crit in stance) and cannot be dodged, parried '
          'or blocked. First at 10 s, then every 15 s, never during an operation. Range 40 yd '
          '(KrastinovLogic.h kBackhandRangeYd): the range is checked again when the bar ends, so a 10 yd range let a '
          "tank step out of it; a cast that does not start retries 1 s later. Backhand 18103's SpellVisual 1184.",
    raw_overrides=kit_raw('A brutal backhand.', DefenseType=_DEFENSE_MELEE, InterruptFlags=0, PreventionType=0,
                          SpellVisualID_1=_SV_BACKHAND, **_HIT_RAW),
)
scripted_by(backhand_206238, 'spell_sc_krastinov_ref_hit')

butchers_rend_206239 = spell(
    id=206239, name="Butcher's Rend", school=School.NORMAL, dispel=0, mechanic=_MECHANIC_BLEED,
    attributes=ATTR0_AURA_IS_DEBUFF | _ATTR0_NO_ACTIVE_DEFENSE, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=10.0, duration_ms=15000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=2, die_sides=0,
                    amplitude=3000, mechanic=_MECHANIC_BLEED, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
                    potency_excluded=_SCRIPT_REF)],
    spell_icon_id=_ICON_REND,
    notes=f'{_S6} KR9 Butcher\'s Rend (stock Rend 16509 changed): a stacking bleed on the tank, the healer\'s steady '
          'load between operations. Base point 2 = 2% of the reference row per stack per 3 s (the tank row on the '
          'tank: 74 normal, 82 heroic per stack; spell_sc_krastinov_ref_dot), up to 5 stacks, 15 s, refreshed by '
          'each application (section 7 #24, tuned in WP-T). First at 3-7 s, then every 14-18 s, never during an '
          "operation. Bleed (no armor), not dispellable, ignores caster modifiers. Rend 16509's SpellVisual 372.",
    raw_overrides=kit_raw('A deep cleaver wound that bleeds.', 'Bleeding.', instant=True, CumulativeAura=5,
                          DefenseType=_DEFENSE_MELEE, AttributesEx=_ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION,
                          AttributesEx2=_ATTR2_CANT_CRIT,
                          AttributesEx3=_ATTR3_NOT_A_PROC | _ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          SpellVisualID_1=_SV_REND),
)
scripted_by(butchers_rend_206239, 'spell_sc_krastinov_ref_dot')

# --- KR7 Failed Patients ---------------------------------------------------------------------------------------------
infected_claws_206240 = spell(
    id=206240, name='Infected Claws', school=School.NORMAL, dispel=0, mechanic=_MECHANIC_BLEED,
    attributes=ATTR0_AURA_IS_DEBUFF | _ATTR0_NO_ACTIVE_DEFENSE, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=10.0, duration_ms=10000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=1, die_sides=0,
                    amplitude=2000, mechanic=_MECHANIC_BLEED, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
                    potency_excluded=_SCRIPT_REF)],
    spell_icon_id=_ICON_CLAW,
    notes=f'{_S6} KR7 the Failed Patients\' light bleed (SC gap, section 7 #24): every 6-9 s a Failed Patient in '
          'melee range claws its victim: base point 1 = 1% of the reference row per 2 s for 10 s (37 / 41 per tick; '
          'spell_sc_krastinov_ref_dot), refreshed, not stacking. Not the stock ghouls\' disease (disease is '
          "Polkelt's). Bleed, not dispellable, ignores caster modifiers. Rend's SpellVisual 372.",
    raw_overrides=kit_raw('Festering claws open old wounds.', 'Bleeding.', instant=True, DefenseType=_DEFENSE_MELEE,
                          AttributesEx=_ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION, AttributesEx2=_ATTR2_CANT_CRIT,
                          AttributesEx3=_ATTR3_NOT_A_PROC | _ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          SpellVisualID_1=_SV_REND),
)
scripted_by(infected_claws_206240, 'spell_sc_krastinov_ref_dot')

claw_at_straps_206241 = spell(
    id=206241, name='Claw at the Straps', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=10.0, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_MONSTER_CLAW,
    notes=f'{_S6} KR7 heroic (The Waiting Room Wants In): a Failed Patient at the bench pulls the straps tight again, '
          'one of the patient\'s interrupts undone (the script; every 3 s per Failed Patient within 5 yd of the '
          "bench). Cast triggered by the Failed Patient on the patient: Claw 16827's SpellVisual 6762. Look only.",
    raw_overrides=kit_raw('Pulls the straps tight again.', instant=True, InterruptFlags=0, PreventionType=0,
                          AttributesEx=_ATTR1_NO_THREAT, AttributesEx2=_ATTR2_IGNORE_LINE_OF_SIGHT,
                          SpellVisualID_1=_SV_CLAW),
)
