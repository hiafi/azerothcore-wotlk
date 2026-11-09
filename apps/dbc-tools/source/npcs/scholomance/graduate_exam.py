"""
Scholomance build WP-S13: Darkmaster Gandling's hard mode "the Graduate Exam", heroic only
(.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.5 row S13, s3.6, s3.10; build spec
docs/dungeons/scholomance-rework.md SC 2909-3006, 3046-3063). WP-S13 owns this file (its spells: kSpellsGandlingHardMode
206365-206384 of modules/mod-dungeon-bosses src/Scholomance/ScholomanceRework.h only; GraduateExamLogic.h names the
same ids; its creatures: the seven Graduate Examiners 300548-300554). The engine side is
src/Scholomance/graduate_exam.cpp (the instance owns its driver: the grade displays, the paper, the gauntlet); the
honors program paper (GO 301153), its heroic spawn, the examiners' ghost tint (creature_template_addon) and their
copied texts are WP-S13's SQL rev (dbc-tools does not declare gameobjects).

- The Passing Grades (ruling 22): six display auras, one per instructor (the instance holds the grades, saved; the
  driver shows each on every player of the map who holds it, every 2 s). Earned at the instructor's death by the
  players inside the instructor's arena (an unreleased body counts, a released ghost does not) with no failure
  (orchestrator ruling 2026-11-08). Not cancellable, kept through death (ALLOW_AURA_WHILE_DEAD), dropped on a map change
  (AuraInterruptFlags CHANGE_MAP; the engine also strips CHANGE_MAP auras at every logout and login, and the 2 s sweep
  shows them again inside Scholomance). Icons: WP-V's PASSING_GRADE_ICONS.
- The seven Graduate Examiners: each instructor's own AI in examiner mode (heroic values on any map, no boss state, no
  grades), bound to its separate ScriptName (user ruling 2026-11-08; registered behind kWaveCBound by the instructors'
  files). Heroic only and summoned directly at these entries by the gauntlet: NO heroic template and no
  difficulty_entry_1 (the wave C mint rule; source/world/dungeons/scholomance.py lists none of them). Level 60 elites
  with the instructor's model, class, creature type and speeds, the stun immunity set 1972, no loot, no gold; the
  heroic tier's melee (the instructors' heroic templates: DamageModifier 20.6772 for a warrior, 22.23 for a paladin,
  Corvane's 6.2503). Health from the build spec (SC "Hard mode, the gauntlet": 80k each, the Ravenian 60k, Corvane
  20k); every examiner AI but Krastinov's sets it again on reset, the template makes it the same. Subname "Graduate
  Examiner".
    300548 Instructor Malicia   npc_sc_examiner_malicia     paladin base 2,442 x 32.76004 = 80,000
    300549 Krastinov            npc_sc_examiner_krastinov   warrior base 3,052 x 26.21232 = 80,000 (S6's number; no
                                                            CIVILIAN bit: the gauntlet pulls him)
    300550 Lorekeeper Polkelt   npc_sc_examiner_polkelt     warrior 26.21232 = 80,000
    300551 The Ravenian         npc_sc_examiner_ravenian    warrior 19.65924 = 60,000; he seats his own 300552
    300552 Master Corvane       npc_sc_examiner_corvane     mage base 2,136 x 9.3633 = 20,000; 300542's flags
                                                            (unit_flags 0x02000002: seated, not selectable until his
                                                            50% drop)
    300553 Lord Alexei Barov    npc_sc_examiner_alexei      warrior 26.21232 = 80,000
    300554 Lady Illucia Barov   npc_sc_examiner_illucia     paladin 32.76004 = 80,000

Spells (looks from WP-V's ._visuals, all stock):

  206365  Passing Grade: Instructor Malicia          the grade display (Spell_Shadow_SoulGem)
  206366  Passing Grade: Doctor Theolen Krastinov    (INV_Misc_SurgeonGlove_01)
  206367  Passing Grade: Lorekeeper Polkelt          (Trade_Alchemy)
  206368  Passing Grade: The Ravenian                (Spell_Shadow_AnimateDead)
  206369  Passing Grade: Lord Alexei Barov           (INV_Rod_EnchantedFelsteel)
  206370  Passing Grade: Lady Illucia Barov          (Spell_Shadow_MindSteal)
  206371-206384 spare.
"""

from lib.dsl import AuraType, Effect, EffectType, School
from lib.dsl.registry import creature_model, creature_template, spell

from ._common import (
    ATTR0_NO_IMMUNITIES,
    ATTR4_NO_CAST_LOG,
    IMMUNITY_BOSS_STUN,
    KIT_CREATURE,
    TARGET_UNIT_CASTER,
    kit_raw,
)
from ._visuals import DISPLAY_CORVANE, PASSING_GRADE_ICONS

_GE = 'Scholomance build WP-S13 (the Graduate Exam)'

_ATTR0_NO_AURA_CANCEL = 0x80000000
_ATTR3_ALLOW_AURA_WHILE_DEAD = 0x00100000    # SharedDefines.h SPELL_ATTR3_ALLOW_AURA_WHILE_DEAD: kept through death
# AURA_INTERRUPT_FLAG_CHANGE_MAP (SpellDefines.h): a map change drops it (a same-map teleport keeps it).
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000

# The instructors, in the Instructor order of ScholomanceRework.h (the grade bits, the icons).
_INSTRUCTORS = ('Instructor Malicia', 'Doctor Theolen Krastinov', 'Lorekeeper Polkelt', 'The Ravenian',
                'Lord Alexei Barov', 'Lady Illucia Barov')

# --- The Passing Grades (206365-206370) -----------------------------------------------------------------------------

passing_grades = [
    spell(
        id=206365 + index, name=f'Passing Grade: {instructor}', school=School.NORMAL, dispel=0, mechanic=0,
        attributes=_ATTR0_NO_AURA_CANCEL | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=0.0, duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY,
                        implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon,
        notes=f'{_GE}: the Passing Grade display for {instructor} (ruling 22). A player inside the instructor\'s '
              'arena at the death (alive, or dead and not released) without a failure the registry records holds the '
              'grade in instance data (saved; a death, a release or a logout never loses it); graduate_exam.cpp '
              'shows this aura on them (self-applied, triggered, every 2 s). No effect. Not cancellable, kept '
              'through death, dropped on a map change and at a logout (the engine strips CHANGE_MAP auras; the '
              'sweep shows it again inside). When every instructor has grades from 3 of 5 players, the honors '
              'program paper in the study can be signed (the Graduate Exam). Number-free text.',
        raw_overrides=kit_raw(f'Passed {instructor}\'s class without a failing mark.',
                              f'Passed {instructor}\'s class without a failing mark.', instant=True,
                              AttributesEx3=_ATTR3_ALLOW_AURA_WHILE_DEAD, AttributesEx4=ATTR4_NO_CAST_LOG,
                              AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
    )
    for index, (instructor, icon) in enumerate(zip(_INSTRUCTORS, PASSING_GRADE_ICONS))
]

# --- The Graduate Examiners (300548-300554) -------------------------------------------------------------------------

# The instructors' stock models (creature_template_model of 10505, 11261, 10901, 10507, 10504, 10502 [db]).
_DISPLAY_MALICIA = 20981
_DISPLAY_KRASTINOV = 10901
_DISPLAY_POLKELT = 11492
_DISPLAY_RAVENIAN = 10433
_DISPLAY_ALEXEI = 11072
_DISPLAY_ILLUCIA = 11835

# The heroic tier's melee (the instructors' heroic templates, lib/heroic_templates.py's boss tier at level 60).
_DM_WARRIOR = 20.6772
_DM_PALADIN = 22.23
_DM_CORVANE = 6.2503     # Master Corvane's heroic copy 310118 (he never melees)

# HealthModifier on the level 60 class base: warrior 3,052, paladin 2,442, mage 2,136.
_HM_80K_WARRIOR = 26.21232
_HM_80K_PALADIN = 32.76004
_HM_60K_WARRIOR = 19.65924
_HM_20K_MAGE = 9.3633

_UNIT_FLAG_SEATED = 0x02000000 | 0x2     # Corvane: not selectable or attackable until his drop (300542's flags)


def _examiner(entry: int, name: str, script: str, display: int, *, unit_class: int, type_: int, health_mod: float,
              damage_mod: float, unit_flags: int, **more) -> dict:
    row = creature_template(
        entry, name, **{
            **KIT_CREATURE, 'subname': 'Graduate Examiner', 'minlevel': 60, 'maxlevel': 60, 'rank': 1, 'type': type_,
            'unit_class': unit_class, 'unit_flags': unit_flags, 'HealthModifier': health_mod,
            'DamageModifier': damage_mod, 'ManaModifier': 3.0 if unit_class == 2 else 1.0,
            'CreatureImmunitiesId': IMMUNITY_BOSS_STUN, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0,
            'mingold': 0, 'maxgold': 0, 'ScriptName': script, **more,
        },
    )
    creature_model(entry, display_id=display)
    return row


examiner_malicia_300548 = _examiner(
    300548, 'Instructor Malicia', 'npc_sc_examiner_malicia', _DISPLAY_MALICIA, unit_class=2, type_=7,
    health_mod=_HM_80K_PALADIN, damage_mod=_DM_PALADIN, unit_flags=64)
examiner_krastinov_300549 = _examiner(
    300549, 'Doctor Theolen Krastinov', 'npc_sc_examiner_krastinov', _DISPLAY_KRASTINOV, unit_class=1, type_=7,
    health_mod=_HM_80K_WARRIOR, damage_mod=_DM_WARRIOR, unit_flags=64, BaseAttackTime=1500, speed_run=1.42857)
examiner_polkelt_300550 = _examiner(
    300550, 'Lorekeeper Polkelt', 'npc_sc_examiner_polkelt', _DISPLAY_POLKELT, unit_class=1, type_=6,
    health_mod=_HM_80K_WARRIOR, damage_mod=_DM_WARRIOR, unit_flags=64)
examiner_ravenian_300551 = _examiner(
    300551, 'The Ravenian', 'npc_sc_examiner_ravenian', _DISPLAY_RAVENIAN, unit_class=1, type_=6,
    health_mod=_HM_60K_WARRIOR, damage_mod=_DM_WARRIOR, unit_flags=64, speed_walk=0.8)
examiner_corvane_300552 = _examiner(
    300552, 'Master Corvane', 'npc_sc_examiner_corvane', DISPLAY_CORVANE, unit_class=8, type_=7,
    health_mod=_HM_20K_MAGE, damage_mod=_DM_CORVANE, unit_flags=_UNIT_FLAG_SEATED)
examiner_alexei_300553 = _examiner(
    300553, 'Lord Alexei Barov', 'npc_sc_examiner_alexei', _DISPLAY_ALEXEI, unit_class=1, type_=6,
    health_mod=_HM_80K_WARRIOR, damage_mod=_DM_WARRIOR, unit_flags=32832)
examiner_illucia_300554 = _examiner(
    300554, 'Lady Illucia Barov', 'npc_sc_examiner_illucia', _DISPLAY_ILLUCIA, unit_class=2, type_=6,
    health_mod=_HM_80K_PALADIN, damage_mod=_DM_PALADIN, unit_flags=32832)
