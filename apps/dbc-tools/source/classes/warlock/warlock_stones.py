"""
Warlock - Firestone and Spellstone as 2 hour self-buffs (dungeon-prereqs S5b, PLAN D9).

Design: .agents/plans/dungeon-prereqs/dungeon-prereqs.WARLOCK-STONES.md (sections 2-9; user rulings 2026-10-31 at
its top: the stone on-use KEEPS the old 3 sec cast, the Mastery-in-tenths core term is allowed).

The conjured stone items stay. Each stone item's on-use spell (13 stock ids, rewritten in place below) is a 3 sec cast
whose only effect is a TRIGGER_SPELL that casts the 2 hour buff (200714 Firestone / 200715 Spellstone). A buff cast
through a trigger carries no cast item, so the engine's Proc Chance multiplier reaches its proc (Aura::CalcProcChance
skips only auras with a CastItemGUID), it refreshes in place, and it outlives the stone. Each buff holds one stat effect
and one PROC_TRIGGER_SPELL effect with a spell_proc row; spell_warl_stone_buff (spell_warlock_demonology.cpp) adds the
"own hit on a hostile target" and "a cast rolls once" checks. Master Conjuror (warlock_trigger_spells.py 18767/18768)
scales the stat, the Fire Blast damage and the Surge Mastery through three SpellMods on the bits named in _masks.py.

Ids: 200714-200717 (the warlock-shared spares, SHARED s1), spell_group 1203 (SHARED s2), SpellDescriptionVariables
1430 (ids.yaml `reservations: warlock`).
"""

from lib.dsl import AuraType, CombatRating, Effect, EffectType, RANGE_SELF, School
from lib.dsl.registry import pot_text, procs_on, scripted_by, spell, spell_group, spell_group_rule, tooltip_vars
from lib.dsl.tooltip import talent_mult

from . import _masks as m
from .warlock_trigger_spells import master_conjuror_18767, master_conjuror_18768

# ---- Spell.dbc flag values (src/server/shared/SharedDefines.h) ----
_SPELLFAMILY_WARLOCK = 5
_ATTR0_DO_NOT_SHEATH = 0x40000  # the stock on-use rows' only Attributes bit
_ATTR2_ALLOW_DEAD_TARGET = 0x1
_ATTR3_SUPPRESS_CASTER_PROCS = 0x10000  # Fire Blast: marker only, the real no-proc guard is the triggered cast
_ATTR3_ALLOW_AURA_WHILE_DEAD = 0x100000  # with AttributesEx2 0x1: the shaman imbue "persists through death" flags
_DMG_MAGIC = 1  # DefenseType: SPELL_DAMAGE_CLASS_MAGIC
_TARGET_UNIT_CASTER = 1
_TARGET_UNIT_TARGET_ENEMY = 6
_INTERRUPT_ON_MOVE_PUSHBACK_INTERRUPT_COMBAT = 15  # the stock on-use rows' InterruptFlags (a 3 sec cast)

# spell_proc masks (src/server/game/Spells/SpellMgr.h)
_PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_NEG = 0x1000
_PROC_ATTR_CANT_PROC_FROM_ITEM_CAST = 0x100
_SCHOOL_MASK_SHADOW = 32

# Stock icons and visuals: Firestone 1735, Spellstone 344, Fire Blast icon 12 / visual 143, Shadow Mastery icon 22.
_ICON_FIRESTONE = 1735
_ICON_SPELLSTONE = 344
_ICON_FIRE_BLAST = 12
_SV_FIRE_BLAST = 143
_ICON_SHADOW_MASTERY = 22

_TWO_HOURS_MS = 7200000
_LANG_MASKS = {'Name_Lang_Mask': 16712190, 'Description_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712188,
               'NameSubtext_Lang_Mask': 16712188}


# =====================================================================================================================
# Tooltip variables (section 9): Master Conjuror's three effects as multipliers
# =====================================================================================================================

# mcflat = the stat (eff1 +100/200%), mcproc = Fire Blast damage (eff2 +50/100%), mcmast = Surge Mastery
# (eff3 +50/100%).
warlock_stones_1430 = tooltip_vars(
    1430, "Warlock stones: Master Conjuror multipliers",
    mcflat=talent_mult([master_conjuror_18767, master_conjuror_18768], effect=1),
    mcproc=talent_mult([master_conjuror_18767, master_conjuror_18768], effect=2),
    mcmast=talent_mult([master_conjuror_18767, master_conjuror_18768], effect=3),
)


# =====================================================================================================================
# The procs' payloads
# =====================================================================================================================

# Firestone's proc: 40 potency Fire, off-GCD payout (T stays 1.5 s). Its own d2 bit joins no composite, so only Master
# Conjuror's eff1 scopes it; school-wide damage, crit, Versatility and spell power still apply. A triggered cast without
# NOT_A_PROC, so it procs nothing (never Firestone, Spellstone or a talent).
fire_blast_200716 = spell(
    id=200716, name='Fire Blast', school=School.FIRE, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=40.0, potency_kind='direct', time_basis_ms=1500,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_FIRE_BLAST,
    notes='dungeon-prereqs S5b (WARLOCK-STONES s3): the Firestone proc, triggered by 200714 eff1. '
          'Potency 40 Fire direct, '
          'T 1500, d2 STONE_FIRE_BLAST (Master Conjuror eff1 only). Range 50000 (triggered helper). '
          'AttributesEx3 0x10000 '
          'is a marker; the triggered cast is the no-proc guard.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_WARLOCK, 'SpellClassMask_2': m.STONE_FIRE_BLAST, 'DefenseType': _DMG_MAGIC,
        'EquippedItemClass': -1, 'SpellLevel': 28, 'CastingTimeIndex': 1,
        'AttributesEx3': _ATTR3_SUPPRESS_CASTER_PROCS, 'SpellVisualID_1': _SV_FIRE_BLAST,
        'Description_Lang_enUS': 'Blasts the target for {pot1} Fire damage.',
    },
)

# Spellstone's proc: +1% Mastery per stack (aura 306, misc 1 << MASTERY_TENTHS, amount 10 tenths = stored 9), up to 3
# stacks, 10 sec, each proc refreshes. Master Conjuror's eff2 (SPELLMOD_EFFECT1) makes it 15 / 20 tenths per stack; the
# engine multiplies the amount by the stack count and recomputes it on every new stack.
spellstone_surge_200717 = spell(
    id=200717, name='Spellstone Surge', school=School.SHADOW, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=10000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_CUSTOM_STAT_PCT,
                    misc_value=1 << CombatRating.MASTERY_TENTHS, base_points=9, implicit_target_a=_TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_SHADOW_MASTERY,
    tooltip_vars=warlock_stones_1430,
    notes='dungeon-prereqs S5b (WARLOCK-STONES s3): the Spellstone proc, triggered by 200715 eff1. '
          'Aura 306 misc 1 << 25 '
          '(Mastery in tenths, Player::GetMasteryPercentage) stored 9 = 1.0% per stack, CumulativeAura 3, 10 sec. '
          'd2 STONE_SURGE (Master Conjuror eff2). Not death-persistent.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_WARLOCK, 'SpellClassMask_2': m.STONE_SURGE, 'EquippedItemClass': -1,
        'SpellLevel': 36, 'CastingTimeIndex': 1, 'CumulativeAura': 3,
        'Description_Lang_enUS': 'Mastery increased by ${$<mcmast>*1}.1% per stack.',
        'AuraDescription_Lang_enUS': 'Mastery increased.',
    },
)


# =====================================================================================================================
# Tooltip text (section 9)
# =====================================================================================================================

_FIRESTONE_TEXT = (
    'Firestone increases your spell critical strike chance by ${$<mcflat>*1}%, and your direct damage spells have a '
    '30% chance to hit the target with a Fire Blast for ' + pot_text(fire_blast_200716, var='mcproc')
    + ' Fire damage, at most once per sec. Only one stone can be active at a time. Persists through death.'
)
_SPELLSTONE_TEXT = (
    'Spellstone increases your haste by ${$<mcflat>*1}%, and your Shadow critical strikes have a 10% chance to grant '
    '${$<mcmast>*1}.1% Mastery for 10 sec, stacking up to 3 times. This can only occur once every 3 sec. Only one '
    'stone can be active at a time. Persists through death.'
)
FIRESTONE_USE_TEXT = 'Grants Firestone for 2 hrs. ' + _FIRESTONE_TEXT
SPELLSTONE_USE_TEXT = 'Grants Spellstone for 2 hrs. ' + _SPELLSTONE_TEXT
# Create Firestone 6366 / Create Spellstone 2362 (warlock_spells.py)
CREATE_FIRESTONE_TEXT = 'Creates a Firestone. Using it grants Firestone for 2 hrs. ' + _FIRESTONE_TEXT
CREATE_SPELLSTONE_TEXT = 'Creates a Spellstone. Using it grants Spellstone for 2 hrs. ' + _SPELLSTONE_TEXT


# =====================================================================================================================
# The buffs
# =====================================================================================================================

def _stone_buff_raw(class_mask_1, spell_level, description, aura_description):
    """A visible, not consolidated, death-persistent 2 hour self-buff (the shaman imbue flags), family 5."""
    return {
        'SpellClassSet': _SPELLFAMILY_WARLOCK, 'SpellClassMask_1': class_mask_1, 'EquippedItemClass': -1,
        'SpellLevel': spell_level, 'CastingTimeIndex': 1,
        'AttributesEx2': _ATTR2_ALLOW_DEAD_TARGET, 'AttributesEx3': _ATTR3_ALLOW_AURA_WHILE_DEAD,
        'Description_Lang_enUS': description, 'AuraDescription_Lang_enUS': aura_description,
    }


# Firestone: +1% spell crit (aura 57, stored 0; Master Conjuror eff0 scales it to 2 / 3%) and the Fire Blast proc.
firestone_200714 = spell(
    id=200714, name='Firestone', school=School.FIRE, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=_TWO_HOURS_MS,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_SPELL_CRIT_CHANCE, base_points=0,
               implicit_target_a=_TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PROC_TRIGGER_SPELL, trigger_spell=fire_blast_200716.id,
               implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_FIRESTONE,
    tooltip_vars=warlock_stones_1430,
    notes='dungeon-prereqs S5b (WARLOCK-STONES s3): 2 h self-buff from the Firestone items\' on-use (trigger, no cast '
          'item). eff0 aura 57 +1% spell crit (Master Conjuror eff0), '
          'eff1 PROC_TRIGGER_SPELL 200716 (spell_proc below, '
          'spell_warl_stone_buff). d1 FIRESTONE_ENCHANT. spell_group 1203. AttributesEx3 0x100000 + AttributesEx2 0x1 '
          '(persists through death).',
    raw_overrides=_stone_buff_raw(
        m.FIRESTONE_ENCHANT, 28, _FIRESTONE_TEXT,
        'Spell critical strike chance increased. Your direct damage spells can hit the target with a Fire Blast.'),
)

# Spellstone: +1% spell haste (aura 65, joins no haste group: a 2 h baseline buff) and the Surge proc.
spellstone_200715 = spell(
    id=200715, name='Spellstone', school=School.SHADOW, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=_TWO_HOURS_MS,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_CASTING_SPEED_NOT_STACK, base_points=0,
               implicit_target_a=_TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PROC_TRIGGER_SPELL,
               trigger_spell=spellstone_surge_200717.id, implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_SPELLSTONE,
    tooltip_vars=warlock_stones_1430,
    notes='dungeon-prereqs S5b (WARLOCK-STONES s3): 2 h self-buff from the Spellstone items\' on-use (trigger, no cast '
          'item). eff0 aura 65 +1% spell haste (Master Conjuror eff0), '
          'eff1 PROC_TRIGGER_SPELL 200717 (spell_proc below, '
          'spell_warl_stone_buff). d1 SPELLSTONE. spell_group 1203. AttributesEx3 0x100000 + AttributesEx2 0x1 '
          '(persists through death).',
    raw_overrides=_stone_buff_raw(
        m.SPELLSTONE, 36, _SPELLSTONE_TEXT, 'Haste increased. Your Shadow critical strikes can grant Mastery.'),
)


# =====================================================================================================================
# The stone items' on-use spells (13 stock ids, rewritten in place)
# =====================================================================================================================

# Item -> spell links stay as they are (41170 Lesser Firestone ... 40773 Master Firestone; 41191 Spellstone ... 41196
# Grand Spellstone), so no client item cache goes stale; only 41170 and 41191 can be created today (the single-rank
# Create spells), the rest stay consistent for any stray higher rank. Each keeps its name and the old 3 sec cast (user
# ruling 2026-10-31), and loses the weapon target: Targets 0, EquippedItemClass -1, no EquippedItemInvTypes, no
# AttributesEx2 0x2000 (enchant own item only), no SpellVisual (3182 was the weapon glow). Family 5 with no bits.
_STONE_USE_SPELLS = (
    # (id, name, buff, icon, description)
    (55152, 'Lesser Firestone', firestone_200714, _ICON_FIRESTONE, FIRESTONE_USE_TEXT),
    (55153, 'Firestone', firestone_200714, _ICON_FIRESTONE, FIRESTONE_USE_TEXT),
    (55154, 'Greater Firestone', firestone_200714, _ICON_FIRESTONE, FIRESTONE_USE_TEXT),
    (55155, 'Major Firestone', firestone_200714, _ICON_FIRESTONE, FIRESTONE_USE_TEXT),
    (55156, 'Fel Firestone', firestone_200714, _ICON_FIRESTONE, FIRESTONE_USE_TEXT),
    (55158, 'Grand Firestone', firestone_200714, _ICON_FIRESTONE, FIRESTONE_USE_TEXT),
    (54721, 'Master Firestone', firestone_200714, _ICON_FIRESTONE, FIRESTONE_USE_TEXT),
    (55171, 'Spellstone', spellstone_200715, _ICON_SPELLSTONE, SPELLSTONE_USE_TEXT),
    (55175, 'Greater Spellstone', spellstone_200715, _ICON_SPELLSTONE, SPELLSTONE_USE_TEXT),
    (55178, 'Major Spellstone', spellstone_200715, _ICON_SPELLSTONE, SPELLSTONE_USE_TEXT),
    (55188, 'Master Spellstone', spellstone_200715, _ICON_SPELLSTONE, SPELLSTONE_USE_TEXT),
    (55190, 'Demonic Spellstone', spellstone_200715, _ICON_SPELLSTONE, SPELLSTONE_USE_TEXT),
    (55194, 'Grand Spellstone', spellstone_200715, _ICON_SPELLSTONE, SPELLSTONE_USE_TEXT),
)

for _use_id, _use_name, _use_buff, _use_icon, _use_text in _STONE_USE_SPELLS:
    spell(
        id=_use_id, name=_use_name, school=School.NORMAL, attributes=_ATTR0_DO_NOT_SHEATH,
        cast_time_ms=3000, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        effects=[Effect(type=EffectType.TRIGGER_SPELL, trigger_spell=_use_buff.id,
                        implicit_target_a=_TARGET_UNIT_CASTER)],
        spell_icon_id=_use_icon,
        tooltip_vars=warlock_stones_1430,
        notes=f'dungeon-prereqs S5b (WARLOCK-STONES s3): stone item on-use, rewritten in place from the stock weapon '
              f'enchant (effect 54, item target) into a 3 sec cast that triggers the {_use_buff.name} buff '
              f'{_use_buff.id}. Targets 0, EquippedItemClass -1, no weapon glow; name, icon and the 3 sec cast kept.',
        raw_overrides={
            'SpellClassSet': _SPELLFAMILY_WARLOCK, 'EquippedItemClass': -1, 'Targets': 0, 'SpellLevel': 15,
            'InterruptFlags': _INTERRUPT_ON_MOVE_PUSHBACK_INTERRUPT_COMBAT, 'ProcChance': 101,
            'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500,
            'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0,
            'Description_Lang_enUS': _use_text, **_LANG_MASKS,
        },
    )


# =====================================================================================================================
# Exclusivity and procs (sections 4 and 6)
# =====================================================================================================================

# One stone at a time: EXCLUSIVE (rule 1), using the other stone replaces the active buff.
spell_group(1203, firestone_200714, spellstone_200715)
spell_group_rule(1203, stack_rule=1, description='Warlock stones: one at a time')

# Firestone: any non-periodic damage hit the warlock's own (untriggered, non-item) spell lands, any school or family;
# 30%, 1 sec internal cooldown. eff0 (the stat) never procs. Proc Chance scales the 30% through the engine.
procs_on(
    firestone_200714,
    proc_flags=m.PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG | _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_NEG,
    spell_type_mask=m.PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=m.PROC_SPELL_PHASE_HIT,
    attributes_mask=_PROC_ATTR_CANT_PROC_FROM_ITEM_CAST, disable_effects_mask=0x1, chance=30, cooldown_ms=1000,
)
scripted_by(firestone_200714, 'spell_warl_stone_buff')

# Spellstone: Shadow crits, direct and periodic (Shadowflame's Shadow+Fire counts); 10%, 3 sec internal cooldown.
procs_on(
    spellstone_200715,
    proc_flags=m.PROC_FLAG_DONE_SPELL_MAGIC_DMG_CLASS_NEG | _PROC_FLAG_DONE_SPELL_NONE_DMG_CLASS_NEG
    | m.PROC_FLAG_DONE_PERIODIC,
    school_mask=_SCHOOL_MASK_SHADOW, spell_type_mask=m.PROC_SPELL_TYPE_DAMAGE, spell_phase_mask=m.PROC_SPELL_PHASE_HIT,
    hit_mask=m.PROC_HIT_CRITICAL, attributes_mask=_PROC_ATTR_CANT_PROC_FROM_ITEM_CAST, disable_effects_mask=0x1,
    chance=10, cooldown_ms=3000,
)
scripted_by(spellstone_200715, 'spell_warl_stone_buff')
