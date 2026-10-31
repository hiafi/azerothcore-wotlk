"""
Warrior - W0b creatures: the two Skull Banner models (docs/reworks/warrior-shared-rework.md "Skull Banner", user pick
2026-10-29: the Alliance Battle Standard for Alliance warriors, the Horde one for Horde).

Skull Banner 204405 summons 300370 by data (eff0 = stock 23034's SUMMON with SummonProperties 121); for a Horde
caster spell_warr_skull_banner drops that summon and casts the helper 204408, whose SUMMON names 300371. Both are
declared here, not in source/classes/warrior/warrior_shared.py, only because a class package is also loaded without
creature columns (lib/test_warrior_shield_spec.py), where creature_template() raises. creature_template rows are
never pruned (upsert-only); the model rows are reported, not deleted, if this file goes.

Columns are the Alliance Battle Standard 14465's live ones (read-only SELECT 2026-10-28: faction 58, level 1,
speed_walk / run 1, detection_range 18, unit_class 1, unit_flags2 2048, type 10, HealthModifier 1,
CreatureImmunitiesId -311) except level 60, faction 35, unit_flags NON_ATTACKABLE (0x2; still selectable so a .morph
target works), flags_extra 0 (bug log), no ScriptName / AIName, no creature_template_addon (14465's aura 23036 is not
copied), no creature_spell: a banner that does nothing but stand there. Both are named "Skull Banner"; they differ by
entry and display only.
"""

from lib.dsl.registry import creature_model, creature_template

DISPLAY_ALLIANCE_STANDARD = 14541  # creature 14465's only model
DISPLAY_HORDE_STANDARD = 14542

_BANNER = dict(
    subname='', minlevel=60, maxlevel=60, exp=0, faction=35, speed_walk=1.0, speed_run=1.0, speed_swim=1.0,
    speed_flight=1.0, detection_range=18.0, DamageModifier=1.0, BaseAttackTime=2000, RangeAttackTime=2000,
    BaseVariance=1.0, RangeVariance=1.0, unit_class=1, unit_flags=0x2, unit_flags2=2048, type=10, type_flags=0,
    HoverHeight=1.0, HealthModifier=1.0, ManaModifier=1.0, ArmorModifier=1.0, ExperienceModifier=1.0, RegenHealth=1,
    CreatureImmunitiesId=-311, flags_extra=0, ScriptName='', AIName='',
)

skull_banner_alliance_300370 = creature_template(300370, 'Skull Banner', **_BANNER)
creature_model(300370, display_id=DISPLAY_ALLIANCE_STANDARD, idx=0)

skull_banner_horde_300371 = creature_template(300371, 'Skull Banner', **_BANNER)
creature_model(300371, display_id=DISPLAY_HORDE_STANDARD, idx=0)
