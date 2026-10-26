"""
Death Knight - DK0b minion live-stat mirror rows (203056-203058) and the passthrough rebind of the stock pet-scaling
auras. Hunter 201700-201702 (hunter_pet.py) is the shape. Amounts are stored 0; spell_dk_minion_mirror sets them live.
"""

from lib.dsl import AuraType, Effect, EffectType, School
from lib.dsl.registry import const, custom_attr, scripted_by, spell, unbind_script

MINION_AP_SHARE_PCT = const('MINION_AP_SHARE_PCT', 100, 'Minion attack power per owner attack power, percent (DK0b U8).')
# S3a (U15): per-kind attack power shares for the Unholy minions, all [tune] (docs "[tune]"). Read per MinionKind in
# RefreshMinionMirror and spell_dk_minion_mirror::CalcAttackPower; MINION_AP_SHARE_PCT stays the DK0b default.
MINION_ARMY_AP_SHARE_PCT = const('MINION_ARMY_AP_SHARE_PCT', 15, 'Army of the Dead ghoul attack power per owner attack power, percent (S3a U15, [tune]).')
MINION_GHOUL_AP_SHARE_PCT = const('MINION_GHOUL_AP_SHARE_PCT', 60, 'Permanent ghoul (Raise Dead) attack power per owner attack power, percent (S3a U15, [tune]; RETUNE 2026-10-25: was 90).')
MINION_LESSER_GHOUL_AP_SHARE_PCT = const('MINION_LESSER_GHOUL_AP_SHARE_PCT', 25, 'Lesser Ghoul attack power per owner attack power, percent (S3a U15, [tune]; RETUNE 2026-10-25: was 50).')
MINION_ABOMINATION_AP_SHARE_PCT = const('MINION_ABOMINATION_AP_SHARE_PCT', 70, 'Abomination attack power per owner attack power, percent (S3a U15, [tune]; RETUNE 2026-10-25: was 100).')
MINION_SP_SHARE_PCT = const('MINION_SP_SHARE_PCT', 100, 'Minion spell power per owner attack power, percent (DK0b U8, Gargoyle).')
MINION_CRIT_SHARE_PCT = const('MINION_CRIT_SHARE_PCT', 100, 'Share of owner crit the minion inherits, percent (DK0b U8).')
MINION_HASTE_SHARE_PCT = const('MINION_HASTE_SHARE_PCT', 100, 'Share of owner spell haste the minion inherits, percent (DK0b U8).')
MINION_VERSATILITY_SHARE_PCT = const('MINION_VERSATILITY_SHARE_PCT', 100, 'Share of owner versatility the minion inherits, percent (DK0b U8).')
# U16 user ruling: 4 Bloodworms ~ 5% of a Blood DK's single-target damage. Stock worm damage = 13.5 DPS per worm at the
# 1,000 AP reference (15-45 + 0.6% AP per hit at 2.66 s), so a 0 share (AP term dropped) = stock. Read per kind in
# RefreshMinionMirror and spell_dk_minion_mirror::CalcAttackPower. [tune]; S1b-2 measures.
MINION_BLOODWORM_AP_SHARE_PCT = const('MINION_BLOODWORM_AP_SHARE_PCT', 0, 'Bloodworm attack power per owner attack power, percent (S1a U16, [tune]); 0 = stock worm damage.')
MINION_STAMINA_SHARE_PCT = const('MINION_STAMINA_SHARE_PCT', 30, 'Minion stamina inherited from owner stamina, percent, computed live (DK0b U9).')

_MIRROR_RAW = {'AuraDescription_Lang_Mask': 16712188, 'Description_Lang_Mask': 16712188, 'Name_Lang_Mask': 16712188, 'NameSubtext_Lang_Mask': 16712188, 'ProcChance': 101, 'EquippedItemClass': -1, 'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0, 'AttributesEx3': 0x40000}  # ALWAYS_HIT


def _mirror(spell_id, name, effects, notes):
    return spell(
        id=spell_id,
        name=name,
        school=School.NORMAL,
        attributes=464,
        cast_time_ms=0,
        cooldown_ms=0,
        category_cooldown_ms=0,
        mana_cost=0,
        mana_cost_pct=0,
        range_yards=0.0,
        duration_ms=-1,
        effects=effects,
        spell_icon_id=0,
        notes=notes,
        raw_overrides=dict(_MIRROR_RAW),
    )


minion_mirror_203056 = _mirror(
    203056, 'Minion Mirror',
    [
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_ATTACK_POWER),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_DONE, misc_value=126),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=1000),
    ],
    'DK0b U8: hidden mirror aura on a DK minion. eff0 attack power, eff1 spell power (MOD_DAMAGE_DONE misc 126), eff2 1 s refresh tick. Amounts stored 0, set by spell_dk_minion_mirror. Family 0, ALWAYS_HIT.',
)
scripted_by(minion_mirror_203056, 'spell_dk_minion_mirror')

minion_mirror_crit_haste_203057 = _mirror(
    203057, 'Minion Mirror: Crit and Haste',
    [
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_CRIT_PCT),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.HASTE_ALL),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=71, misc_value=126),
    ],
    'DK0b U8: hidden mirror aura. eff0 MOD_CRIT_PCT (290), eff1 HASTE_ALL (193), eff2 MOD_SPELL_CRIT_CHANCE_SCHOOL (71) misc 126 (S3a WP-R M2: minion spell crit = owner crit; the aura 71 amount is set live). Amounts stored 0, set by spell_dk_minion_mirror. Family 0, ALWAYS_HIT.',
)

minion_mirror_versatility_203058 = _mirror(
    203058, 'Minion Mirror: Versatility',
    [
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, misc_value=127),
        Effect(type=EffectType.APPLY_AURA, base_points=0, implicit_target_a=1, apply_aura=AuraType.MOD_HEALING_DONE_PERCENT),
    ],
    'DK0b U8: hidden mirror aura (hunter 201700 shape). eff0 +V done, eff1 -V/2 taken, eff2 +V healing done. Amounts stored 0, set by spell_dk_minion_mirror. Family 0, ALWAYS_HIT. custom_attr POSITIVE (eff1 negative would classify it negative).',
)
custom_attr(minion_mirror_versatility_203058, attributes=0x0E000000)

# Stock pet-scaling rebind: the passthrough replaces the stock scripts (Strength 0, live Stamina, shares 0 for AP/SP).
for _sid, _stock in (
    (51996, 'spell_dk_pet_scaling'),
    (54566, 'spell_dk_pet_scaling'),
    (61697, 'spell_dk_pet_scaling'),
    (49040, 'spell_dk_army_of_the_dead_passive'),
):
    unbind_script(_sid, _stock)
    scripted_by(_sid, 'spell_dk_minion_passthrough')
