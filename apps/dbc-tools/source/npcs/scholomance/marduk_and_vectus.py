"""
Scholomance build WP-S3: Marduk Blackpool (10433) and Vectus (10432), one encounter with one shared health pool
(.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row S3, s3.6; build spec
docs/dungeons/scholomance-rework.md SC 934-991, MV1-MV7). WP-S3 owns this file (its spells: kSpellsMardukVectus
206150-206169 in modules/mod-dungeon-bosses src/Scholomance/ScholomanceRework.h only; MardukVectusLogic.h names the
same ids; its creature: the Graduate 300533; the students 10475's columns).

- 10433 Marduk Blackpool and 10432 Vectus (WP-KS's skeleton): bound to boss_marduk_blackpool_rework /
  boss_vectus_rework (src/Scholomance/boss_marduk_vectus_rework.cpp), SmartAI off (the WP-S3 SQL rev deletes the
  rows), stun immunity 1972, flags_extra 1 (INSTANCE_BIND). Both rows carry the pool's normal health (300k, handoff
  s3.6): HealthModifier 130.605 on Marduk's level 58 class base 2,297 and 122.85 on Vectus's level 60 base 2,442.
  DamageModifier back to the stock 3.5 on both (the live 6.25 on Marduk is the retired mod-progression's leftover,
  handoff s2.3; WP-T tunes melee). Vectus never swings (the script). Heroic health 425k and its overrides are WP-H's
  (source/world/dungeons/scholomance.py).
- 10475 Scholomance Student (32 spawns, all in the Viewing Room): props at their desks (npc_sc_student). Not selectable
  and not attackable (unit_flags 64 | NON_ATTACKABLE 0x2 | NOT_SELECTABLE 0x02000000; the script sets the same flags,
  since a heroic template copies the replayed stock row), except the Pop Quiz student, who stands and becomes
  attackable for the quiz. Level 59, HealthModifier 2.70178: ceil(2,961 x 2.70178) = 8,000 (the quiz student's
  normal health). Heroic 12,000 is WP-H's override (310075).
- 300533 Scholomance Graduate (boss-kit add, SC "Encounter"): a student whose quiz finished, summoned by Vectus at the
  student's desk; npc_sc_graduate casts Shadow Bolt (206166) at random players and never moves or swings. Level 60
  elite humanoid, warrior base 3,052 x 4.9148 = 15,000; heroic 22,000 is WP-H's `_KIT_ADD_HEROIC` (applied because
  this file declares it), and its row names its heroic entry (difficulty_entry_1 310113, STAGE-H report s4). The four
  student models and the student's black book (creature_equip_template, WP-S3 SQL rev).

Spells (Spell.dbc 3.3.5 for every stock id quoted; looks from WP-V's ._visuals, all stock):

  206150  Flamestrike Drill   MV1 a student's 3 s cast at a floor point (CastSpell(x, y, z)): a PERSISTENT_AREA_AURA
                              of 6 yd for 2 s with Flamestrike 18399's SV 10383 (fire hands on the student while it
                              casts; Flamestrike_Impact_Base on the ground as the circle lands: a PersistentAreaKit,
                              so the look needs a dynamic object). Its DUMMY aura is hidden and does nothing; the
                              registry circle beside it owns the hit
  206151  Flamestrike Drill   MV1 heroic: the same, the fire burns 10 s (the lingering circle's look)
  206152  Flamestrike Drill   MV1 the registry's resolve copy, Fire: 45% / 60%, no Weakened. Fire Blast's impact
                              (SV 796, Fire_ImpactDD_Chest) on each player hit
  206153  Flamestrike Drill   MV1 heroic: the burning circle's tick (linger resolve copy), Fire, 10% a second, with the
                              kit's slow rider. Same impact
  206154  Group Exercise      MV2 the marked player's 4 s marker: Hunter's Mark 1130's SV 3239 (the red arrow), a
                              DUMMY debuff naming the job. Dispel none
  206155  Group Exercise      MV2 a student's Shadow Bolt at a player in the ring: one split share (160% / 240% of
                              reference health split among the players inside, at most 75% each) as base point 0
                              (CastCustomSpell, DieSides 0). Shadow Bolt Volley 17228's SV 2318 and missile speed 20
                              (the bolt flies from the desk; Shadowbolt_Chest_Impact on the player). The resolve
                              attribute set (no defense, always hits, no crit, ignores caster modifiers)
  206156  Group Exercise      MV2 the same bolt with no damage (DUMMY): the students with no share fire it at the
                              marked player, so the whole class is seen to volley
  206157  On the Spot         MV3 the quiz student's own aura while it stands (10 s; the script removes it): the
                              descriptor's target priority and ignore list key on it. DUMMY, no look
  206158  Pop Quiz            MV3 the quiz student's 5 s cast, interruptible (InterruptFlags 15, PreventionType
                              silence; the descriptor's interrupt list): Shadow to every enemy within 100 yd (the
                              whole room), 30% / 50% of the reference row set at launch by spell_sc_mv_ref_flat.
                              SV 2318 and speed 20. Ignores caster modifiers, cannot crit
  206159  Ebon Sweep          MV4 Marduk's 2 s wind-up (no effect, not interruptible). Shadow Cleave 29832's SV 7684:
                              its cast kit (the purple cleave swing) plays on Marduk as the bar ends and the cone lands
  206160  Ebon Sweep          MV4 the registry's resolve copy, Shadow: 60% / 70% to everyone in the 90 / 120 degree,
                              10 yd cone but his target. SV 7684's ShadowStrike chest impact on each player hit
  206161  Ebon Sweep          MV4 the tank's own heavy hit (R2 S-1): Shadow, 35% / 40% of the tank row (WP-T tunes
                              it), set at launch by spell_sc_mv_ref_flat, so the tank's defensives count. SV 7684.
                              The resolve attribute set (always hits, no crit, ignores caster modifiers)
  206162  Fireball            MV5 Vectus's filler: a real 3 s cast at a random player, Fire, 10% of the reference row
                              (spell_sc_mv_ref_flat; WP-T tunes it), interruptible, but do-not-kick on the descriptor
                              (the bots keep their kicks for the quiz). Fireball 9053's SV 67 and speed 24
  206163  Whirlwind           MV6 (heroic) Marduk's 2 s cast bar (no effect, not interruptible). Whirlwind 1680's icon
  206164  Whirlwind           MV6 (heroic) the 4 s spin on Marduk: a shown DUMMY aura with Bladestorm 46924's SV 10704
                              (as Rhahk'Zor's); the script roots him and holds his swings while it lasts
  206165  Whirlwind           MV6 (heroic) the spin tick (resolve copy), Physical: 20% every 1 s on the 8 yd circle, one
                              Weakened on a player's first tick per spin. SV 3362 (DecisiveStrike_Impact_Chest)
  206166  Shadow Bolt         the Graduate's bolt: a real 2 s cast at a random player in sight, Shadow, 10% of the
                              reference row (spell_sc_mv_ref_flat; WP-T tunes it), interruptible. SV 2318, speed 20
  206167-206169 spare.

Stock spells kept (DD scales them on heroic): Blast Wave 17277 (Vectus, anyone within 10 yd), Defiling Aura 17695
(Marduk, on the pull), Resurrection 58854 and Viewing Room Student Transform 18115 (Dawn's Gambit).
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
    TARGET_SRC_CASTER,
    TARGET_UNIT_SRC_AREA_ENEMY,
    TARGET_UNIT_TARGET_ENEMY,
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
    MV_DRILL_IMPACT,
    MV_EBON_SWEEP,
    MV_FIREBALL,
    MV_FLAMESTRIKE_DRILL,
    MV_GROUP_EXERCISE_MARK,
    MV_SHADOW_BOLT_VOLLEY,
    MV_WHIRLWIND,
    MV_WHIRLWIND_IMPACT,
)

# One encounter, one drop (WP-L, source/items/scholomance_loot.py): Vectus carries the merged list, the Haunted gloves
# and the encounter's one purse (the sum of the two stock purses, 1,073-1,406 and 1,162-1,522 copper); Marduk's corpse
# has no loot table and no gold.
creature_template_columns(10433, **boss_columns('boss_marduk_blackpool_rework', 130.605, DamageModifier=3.5,
                                                lootid=0, mingold=0, maxgold=0))
creature_template_columns(10432, **boss_columns('boss_vectus_rework', 122.85, DamageModifier=3.5,
                                                mingold=2235, maxgold=2928))

# --- The students (props) and the Graduate -------------------------------------------------------------------------

_UNIT_FLAG_UNK_6 = 0x40                 # the stock students' unit_flags
_UNIT_FLAG_NON_ATTACKABLE = 0x2
_UNIT_FLAG_NOT_SELECTABLE = 0x02000000
_STUDENT_FLAGS = _UNIT_FLAG_UNK_6 | _UNIT_FLAG_NON_ATTACKABLE | _UNIT_FLAG_NOT_SELECTABLE

# Level 59, warrior base 2,961: ceil(2,961 x 2.70178) = 8,000 (the quiz student, SC "Tuning starting points").
creature_template_columns(10475, ScriptName='npc_sc_student', AIName='', minlevel=59, maxlevel=59,
                          HealthModifier=2.70178, unit_flags=_STUDENT_FLAGS)

# The student models (creature_template_model 10475, read-only SELECT 2026-11-08), so a graduate looks like the
# student it replaces.
_STUDENT_DISPLAYS = (11161, 11134, 11135, 11136)

# Level 60, warrior base 3,052: ceil(3,052 x 4.9148) = 15,000.
scholomance_graduate_300533 = creature_template(
    300533, 'Scholomance Graduate', **{
        **KIT_CREATURE, 'minlevel': 60, 'maxlevel': 60, 'rank': 1, 'type': 7, 'unit_class': 1, 'unit_flags': 0,
        'HealthModifier': 4.9148, 'DamageModifier': 1.0, 'BaseAttackTime': 2000, 'ExperienceModifier': 1.0,
        'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0,
        'ScriptName': 'npc_sc_graduate', 'difficulty_entry_1': 310113,
    },
)
for _idx, _display in enumerate(_STUDENT_DISPLAYS):
    creature_model(300533, display_id=_display, idx=_idx)

# --- Spells --------------------------------------------------------------------------------------------------------

_TARGET_DEST_DYNOBJ_ENEMY = 28
_TARGET_FLAG_DEST_LOCATION = 0x40
_INTERRUPT_FLAGS_STANDARD = 15     # movement, pushback, interrupt, auto-attack: a kickable cast
_PREVENTION_SILENCE = 1

_ICON_FLAMESTRIKE = 37      # Flamestrike 18399
_ICON_HUNTERS_MARK = 538    # Hunter's Mark 1130
_ICON_SHADOW_BOLT_VOLLEY = 213  # Shadow Bolt Volley 17228
_ICON_SHADOW_CLEAVE = 277   # Shadow Cleave 29832
_ICON_FIREBALL = 183        # Fireball 9053
_ICON_WHIRLWIND = 83        # Whirlwind 1680


_MV = 'Scholomance WP-S3'
_SCRIPT_EXCLUDED = 'Scholomance: a percent of reference health, set by the script (DungeonKit::RefFlat)'
_RESOLVE_ATTRS = dict(
    Attributes=ATTR0_NO_ACTIVE_DEFENSE, AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION | ATTR1_NO_THREAT,
    AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
    AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG,
)


# --- MV1 Flamestrike Drill -----------------------------------------------------------------------------------------
def _drill_cast(spell_id: int, burn_ms: int, label: str):
    return spell(
        id=spell_id, name='Flamestrike Drill', school=School.FIRE,
        attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_NO_IMMUNITIES, cast_time_ms=3000, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=burn_ms,
        effects=[Effect(type=EffectType.PERSISTENT_AREA_AURA, apply_aura=AuraType.DUMMY,
                        implicit_target_a=_TARGET_DEST_DYNOBJ_ENEMY, radius_yards=6.0)],
        spell_icon_id=_ICON_FLAMESTRIKE,
        notes=f'{_MV}, MV1 {label}: a student\'s 3 s cast at a floor point (CastSpell(x, y, z), not triggered, so the '
              'cast bar and the fire hands show). Flamestrike 18399\'s SV 10383 is a PersistentAreaKit '
              '(Flamestrike_Impact_Base), so the look needs a dynamic object: 6 yd like the registry circle, created '
              f'as the cast ends and the circle lands, {burn_ms // 1000} s. Its DUMMY aura is hidden and does '
              'nothing; the registry circle owns the hit. Not interruptible (the students cannot be targeted anyway).',
        raw_overrides=kit_raw('Flamestrike at the target point.', SpellVisualID_1=MV_FLAMESTRIKE_DRILL,
                              Targets=_TARGET_FLAG_DEST_LOCATION, InterruptFlags=0, PreventionType=0,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


drill_cast_206150 = _drill_cast(206150, 2000, 'normal')
drill_cast_heroic_206151 = _drill_cast(206151, 10000, 'heroic (the circle burns 10 s)')

drill_206152 = resolve_copy(
    206152, 'Flamestrike Drill', School.FIRE, 'The class practices Flamestrike.',
    f'{_MV}, MV1 the registry\'s resolve copy (Fire): 45% normal, 60% heroic, no Weakened, on everyone in a 6 yd '
    'circle as a student\'s cast ends. SV 796 (Fire_ImpactDD_Chest) for the impact on each player hit.',
    icon=_ICON_FLAMESTRIKE, visual=MV_DRILL_IMPACT,
)

drill_burn_206153 = resolve_copy(
    206153, 'Flamestrike Drill', School.FIRE, 'Standing in the fire hurts.',
    f'{_MV}, MV1 heroic: the burning circle\'s tick (DungeonKit::ImpactThenLinger), 10% of the reference row every '
    '1 s for 10 s, with the kit\'s Standing in It slow. SV 796 on each player hit.',
    icon=_ICON_FLAMESTRIKE, visual=MV_DRILL_IMPACT,
)

# --- MV2 Group Exercise --------------------------------------------------------------------------------------------
group_exercise_mark_206154 = spell(
    id=206154, name='Group Exercise', school=School.SHADOW, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=4000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_HUNTERS_MARK,
    notes=f'{_MV}, MV2: the marked player\'s marker for the 4 s of the Stack ring (Hunter\'s Mark 1130\'s SV 3239, the '
          'red arrow, as Nandos\'s Marked Prey). DUMMY, AURA_IS_DEBUFF + NO_IMMUNITIES (it lands through Divine '
          'Shield), Dispel none: the ring is the job.',
    raw_overrides=kit_raw('The class volleys at you in $d. Gather your allies around you to share the bolts.',
                          'The class volleys at you soon. Gather your allies.', CastingTimeIndex=1,
                          SpellVisualID_1=MV_GROUP_EXERCISE_MARK),
)

group_exercise_206155 = spell(
    id=206155, name='Group Exercise', school=School.SHADOW, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY,
                    potency_excluded='Scholomance: a split share of reference health, the script\'s base point')],
    spell_icon_id=_ICON_SHADOW_BOLT_VOLLEY,
    notes=f'{_MV}, MV2 a student\'s bolt. boss_vectus_rework computes the shares when the Stack resolves '
          '(DungeonKit::SplitShares: 160% normal / 240% heroic of reference health, split among the players in the '
          'ring, at most 75% each) and each share is cast by one of the nearest free students (round robin) with the '
          'share as base point 0 (DieSides 0: exact). Shadow, no Weakened (a split hit). Shadow Bolt Volley 17228\'s '
          'SV 2318 and speed 20: the bolt flies from the desk and lands with Shadowbolt_Chest_Impact. The resolve '
          'attribute set (no active defense, redirection, reflection or threat; ignores LoS; cannot crit; not a '
          'proc; always hits; ignores caster modifiers).',
    raw_overrides=kit_raw('The class volleys at its target.', CastingTimeIndex=1,
                          SpellVisualID_1=MV_SHADOW_BOLT_VOLLEY, Speed=20.0, DefenseType=1, **_RESOLVE_ATTRS),
)

group_exercise_look_206156 = spell(
    id=206156, name='Group Exercise', school=School.SHADOW, attributes=ATTR0_NO_IMMUNITIES, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_SHADOW_BOLT_VOLLEY,
    notes=f'{_MV}, MV2 the look of the rest of the volley: the free students with no share fire this at the marked '
          'player (no damage, no threat). SV 2318 and speed 20, like 206155.',
    raw_overrides=kit_raw(CastingTimeIndex=1, SpellVisualID_1=MV_SHADOW_BOLT_VOLLEY, Speed=20.0,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- MV3 Pop Quiz --------------------------------------------------------------------------------------------------
on_the_spot_206157 = spell(
    id=206157, name='On the Spot', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=10000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_SHADOW_BOLT_VOLLEY,
    notes=f'{_MV}, MV3: the quiz student\'s own aura while it stands for the quiz (cast on itself, triggered; the '
          'script removes it when the quiz ends). The descriptor keys on it: the student with it is the bots\' first '
          'target, every student without it is on the ignore list (a prop). DUMMY, no look. Not dispellable.',
    raw_overrides=kit_raw('Called up in front of the class.', 'Called up in front of the class.',
                          CastingTimeIndex=1, AttributesEx4=ATTR4_NO_CAST_LOG),
)

pop_quiz_206158 = spell(
    id=206158, name='Pop Quiz', school=School.SHADOW, cast_time_ms=5000, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=TARGET_SRC_CASTER,
                    implicit_target_b=TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=100.0,
                    potency_excluded=_SCRIPT_EXCLUDED)],
    spell_icon_id=_ICON_SHADOW_BOLT_VOLLEY,
    notes=f'{_MV}, MV3: the quiz student\'s 5 s cast, interruptible (InterruptFlags 15, PreventionType silence; the '
          'descriptor\'s interrupt list, priority 3). Finished, Shadow to every enemy within 100 yd (the whole '
          'Viewing Room): 30% normal / 50% heroic of the reference row, set at launch by spell_sc_mv_ref_flat '
          '(RefFlatOn: the tank row on the tank). Then the student graduates (cap 3 alive). Ignores caster '
          'modifiers and cannot crit. Shadow Bolt Volley 17228\'s SV 2318 and speed 20 (a bolt flies to everyone).',
    raw_overrides=kit_raw('Hurls a volley of shadow bolts at every enemy in the room.',
                          InterruptFlags=_INTERRUPT_FLAGS_STANDARD, PreventionType=_PREVENTION_SILENCE, DefenseType=1,
                          SpellVisualID_1=MV_SHADOW_BOLT_VOLLEY, Speed=20.0, AttributesEx2=ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS),
)
scripted_by(pop_quiz_206158, 'spell_sc_mv_ref_flat')

# --- MV4 Ebon Sweep ------------------------------------------------------------------------------------------------
ebon_sweep_bar_206159 = cast_bar(
    206159, 'Ebon Sweep', 2000, 'Sweeps the runeblade through everything in front of the caster.',
    f'{_MV}, MV4 Marduk\'s 2 s wind-up (with emote 2), every 15 s from 10 s. No effect, not interruptible: the '
    'registry Frontal registered beside it owns the hit. Shadow Cleave 29832\'s SV 7684: its cast kit (the purple '
    'cleave swing, attack animation) plays on Marduk as the bar ends and the cone lands.',
    icon=_ICON_SHADOW_CLEAVE, visual=MV_EBON_SWEEP, school=School.SHADOW,
)

ebon_sweep_206160 = resolve_copy(
    206160, 'Ebon Sweep', School.SHADOW, 'A sweep of the runeblade.',
    f'{_MV}, MV4 the registry\'s resolve copy (Shadow): 60% normal / 70% heroic on everyone in the 10 yd cone (90 / '
    '120 degrees) in front of Marduk but his target (TankExempt). No Weakened (a hit over 50%, ruling 21). SV 7684\'s '
    'ShadowStrike chest impact on each player hit.',
    icon=_ICON_SHADOW_CLEAVE, visual=MV_EBON_SWEEP,
)

ebon_sweep_tank_206161 = spell(
    id=206161, name='Ebon Sweep', school=School.SHADOW, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=TARGET_UNIT_TARGET_ENEMY,
                    potency_excluded=_SCRIPT_EXCLUDED)],
    spell_icon_id=_ICON_SHADOW_CLEAVE,
    notes=f'{_MV}, MV4 the tank\'s heavy hit (the R2 S-1 pattern: the cone skips the tank, his own spell hits him when '
          'he stands in the arc as it resolves). Shadow, 35% normal / 40% heroic of the tank row (no number in the '
          'build spec; WP-T tunes it), set at launch by spell_sc_mv_ref_flat, so the tank\'s defensives count. '
          'Always hits, cannot crit, ignores caster modifiers. SV 7684.',
    raw_overrides=kit_raw('A heavy sweep of the runeblade.', CastingTimeIndex=1, SpellVisualID_1=MV_EBON_SWEEP,
                          DefenseType=1, **_RESOLVE_ATTRS),
)
scripted_by(ebon_sweep_tank_206161, 'spell_sc_mv_ref_flat')

# --- MV5 Fireball --------------------------------------------------------------------------------------------------
fireball_206162 = spell(
    id=206162, name='Fireball', school=School.FIRE, cast_time_ms=3000, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=45.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=TARGET_UNIT_TARGET_ENEMY,
                    potency_excluded=_SCRIPT_EXCLUDED)],
    spell_icon_id=_ICON_FIREBALL,
    notes=f'{_MV}, MV5 Vectus\'s filler ("free casting: Fireball at random players between lessons, healer load"): a '
          'real 3 s cast at a random player in sight, back to back with a 1.5-3.5 s gap. Fire, 10% of the reference '
          'row (no number in the build spec; WP-T tunes it), set at launch by spell_sc_mv_ref_flat. Interruptible '
          '(InterruptFlags 15), but do-not-kick on the descriptor so the bots keep their kicks for the Pop Quiz. '
          'Ignores caster modifiers, cannot crit. Fireball 9053\'s SV 67 and speed 24.',
    raw_overrides=kit_raw('Hurls a fiery ball at an enemy.', InterruptFlags=_INTERRUPT_FLAGS_STANDARD,
                          PreventionType=_PREVENTION_SILENCE, DefenseType=1, SpellVisualID_1=MV_FIREBALL, Speed=24.0,
                          AttributesEx2=ATTR2_CANT_CRIT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS),
)
scripted_by(fireball_206162, 'spell_sc_mv_ref_flat')

# --- MV6 Whirlwind (heroic) ----------------------------------------------------------------------------------------
whirlwind_bar_206163 = cast_bar(
    206163, 'Whirlwind', 2000, 'Begins to whirl the runeblade.',
    f'{_MV}, MV6 (heroic) Marduk\'s 2 s Whirlwind cast bar (with emote 3), every 30 s from 20 s. No effect, not '
    'interruptible: the registry circle on him owns the ticks.',
    icon=_ICON_WHIRLWIND,
)

whirlwind_spin_206164 = spell(
    id=206164, name='Whirlwind', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=4000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_WHIRLWIND,
    notes=f'{_MV}, MV6 (heroic): the 4 s spin on Marduk (cast on himself, triggered, as the cast bar ends). A shown '
          'DUMMY aura carrying Bladestorm 46924\'s SV 10704 (warrior_bladestorm, as Rhahk\'Zor\'s spin 205215); the '
          'script roots him and holds his swings and Ebon Sweep while it lasts.',
    raw_overrides=kit_raw('Spinning. Lasts $d.', 'Spinning.', CastingTimeIndex=1, SpellVisualID_1=MV_WHIRLWIND,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

whirlwind_206165 = resolve_copy(
    206165, 'Whirlwind', School.NORMAL, 'A spinning runeblade.',
    f'{_MV}, MV6 (heroic) the spin tick (resolve copy, Physical): 20% every 1 s on the 8 yd circle on Marduk for 4 s, '
    'one Weakened on a player\'s first tick per spin. SV 3362 (DecisiveStrike_Impact_Chest) on each player hit.',
    icon=_ICON_WHIRLWIND, visual=MV_WHIRLWIND_IMPACT,
)

# --- The Graduate's Shadow Bolt ------------------------------------------------------------------------------------
graduate_bolt_206166 = spell(
    id=206166, name='Shadow Bolt', school=School.SHADOW, cast_time_ms=2000, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=45.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=TARGET_UNIT_TARGET_ENEMY,
                    potency_excluded=_SCRIPT_EXCLUDED)],
    spell_icon_id=_ICON_SHADOW_BOLT_VOLLEY,
    notes=f'{_MV}: the Graduate\'s bolt, a real 2 s cast at a random player in sight every 3.5-5 s. Shadow, 10% of the '
          'reference row (no number in the build spec; WP-T tunes it), set at launch by spell_sc_mv_ref_flat. '
          'Interruptible. Ignores caster modifiers, cannot crit. SV 2318 and speed 20.',
    raw_overrides=kit_raw('Sends a shadowy bolt at an enemy.', InterruptFlags=_INTERRUPT_FLAGS_STANDARD,
                          PreventionType=_PREVENTION_SILENCE, DefenseType=1, SpellVisualID_1=MV_SHADOW_BOLT_VOLLEY,
                          Speed=20.0, AttributesEx2=ATTR2_CANT_CRIT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS),
)
scripted_by(graduate_bolt_206166, 'spell_sc_mv_ref_flat')
