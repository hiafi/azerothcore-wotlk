"""
Shaman - the four Elemental Attunements (SH0a A4): raid-wide, death-persistent self auras that replace the removed
buff totems (docs/reworks/shaman-shared-rework.md "Elemental Attunement", CORE-AUDIT-B B11-B14).

Ids (SH0a-WP-BRIEF.md): 202207 Earth @10, 202208 Water @20, 202209 Fire @26, 202210 Air @32 (parents, trained by
trainer 210); 202211 Earth armor child and 202212 Fire spell-power child (hidden, cast and removed by
`spell_sha_attunement` on the Earth / Fire parent). SkillLineAbility 30640-30643, groups 1252 / 1253.

Shape of every parent: `SPELL_EFFECT_APPLY_AREA_AURA_RAID` (65) on the caster, 40 yd, so the shaman is included and
every party / raid member in range gets it (the Devotion Aura 465 shape, paladin_trigger_spells.py). Infinite, no
cost, no cooldown, instant, GCD 1500 / category 133, `AttributesEx3 0x100000` (persists through death) with
`AttributesEx2 0x1` (ALLOW_DEAD_TARGET, so it can sit on a dead target). No family bits (SpellClassSet 11 only),
`EquippedItemClass -1`. Deliberately NOT `NOT_SHAPESHIFTED` (0x10000, it would strip the aura in Ghost Wolf) and
NOT `IS_ABILITY` (a bit-less ability would fall under the gcd_haste policy; as a magic GCD it simply hastes with
spell haste).

Values are the stock totem buff + 20% (user answer 14, 2026-10-18), scaled by the caster's level. The curve is
`BP + int((clamp(L, BaseLevel, MaxLevel) - max(BaseLevel, SpellLevel)) * ppl) + 1` (SpellEffectInfo::CalcValue).
`SpellLevel` is the learn level (the trainer lint wants SpellLevel <= ReqLevel); `BaseLevel` is the stock curve's
anchor level (>= SpellLevel), so a caster below it gets the flat anchor value, as the stock totem buff did;
`MaxLevel` 60 stops the curve at the server's level cap. BasePoints / ppl are the stock ones x1.2 (BP rounded):

    effect (stock source)                      BP    ppl        Base/Spell/Max   L10  L20  L26  L32  L40  L50  L60  target L60
    Earth Strength  (8076 eff0, 9 / 2.07143)   11    2.485716   10 / 10 / 60      12   36   51   66   86  111  136  135.6
    Earth armor     (8072 eff0, 94 / 13.8816)  213   16.65792   10 / 10 / 60     214  380  480  580  713  880 1046  1046.4
    Water mp5       (5677 eff0, 15 / 1.38889)  18    1.68       26 / 20 / 60      19   19   19   29   42   59   76  75.6
    Fire spell power (52109 eff0+eff1, 24 / 2.70455)  29  3.24546  28 / 26 / 60   30   30   30   42   68  101  133  133.2
    Air Agility     (8076 eff1, 9 / 2.07143)   65    2.5        32 / 32 / 60      66   66   66   66   86  111  136  135.6

(Air is only learnable at 32, so its L10-L26 columns are the flat anchor value.) Spell haste 5% (BP 4), melee haste
10% and ranged haste 10% (BP 9) are flat. 8076's inert third effect (aura 52) is not copied.

Stacking (CORE-AUDIT-B B12-B14, all rows below are plain `spell_group` members):
- 1252 (rule 2, EXCLUSIVE_FROM_SAME_CASTER): the four parents, one per shaman. `CheckSpellGroupStackRules` returns the
  rule of the lowest group id two spells share, so 1252 must be below every other group two attunements share: only
  Earth and Air share another one (1253), and 1253 > 1252. 1022 holds only Air and 1105 only Water.
- 1253 (rule 3, per-stat max): Horn of Winter 57330, Earth (Strength), Air (Agility).
- 1086 (stock armor group, rule 4): the Earth armor child and Devotion Aura 465. Rule 4 is whole-aura, so armor sits
  on its own single-effect child; 465 has exactly one effect (0-verify table 8).
- 1048 (stock spell-power group, rule 4): the Fire spell-power child (aura 13 + 135 on one child, one aura).
- 1022 (stock melee-haste group, rule 3): Air, so Improved Icy Talons (20% melee haste) wins over the 10%.
  Ranged haste is aura 140, not 192 (192 ignores 1022 and would stack with Improved Icy Talons).
- 1105 (stock MP5 group, rule 3): Water, with Blessing of Wisdom.
Stock groups 1086 / 1048 / 1022 / 1105 already have their rule rows; only members are added here.
"""

from lib.dsl import AuraType, Effect, EffectType, RANGE_SELF, School
from lib.dsl.registry import scripted_by, skill_line_ability, spell, spell_group, spell_group_rule, trained_by

SPELLFAMILY_SHAMAN = 11

SPELL_ATTR0_DO_NOT_DISPLAY = 0x80       # child auras: no aura-bar icon, not in a spellbook
SPELL_ATTR0_DO_NOT_LOG = 0x100
SPELL_ATTR2_ALLOW_DEAD_TARGET = 0x1     # the aura can sit on a dead target
SPELL_ATTR3_ALLOW_AURA_WHILE_DEAD = 0x100000   # persists through death (hunter-rework S1 L5 pattern)

AURA_MOD_RESISTANCE = 22                # SPELL_AURA_MOD_RESISTANCE (not in the DSL AuraType enum)
AURA_MOD_POWER_REGEN = 85               # SPELL_AURA_MOD_POWER_REGEN (mp5)
AURA_MOD_RANGED_HASTE = 140             # SPELL_AURA_MOD_RANGED_HASTE (not 192, which ignores group 1022)

TARGET_UNIT_CASTER = 1
ATTUNEMENT_RADIUS_YARDS = 40.0          # [fixed] (shared doc "Elemental Attunement")

TRAINER_SHAMAN = 210
SKILL_LINE_ENHANCEMENT = 373
SKILL_LINE_RESTORATION = 374
CLASS_MASK_SHAMAN = 64

# Stock buff icons: Stoneskin Totem 8071 / 8072, Mana Spring 5675 / 5677, Flametongue Totem 8227 / 52109, Windfury
# Totem 8512 / 8515 (all SpellIconID values read from the stock rows).
ICON_EARTH = 690
ICON_WATER = 338
ICON_FIRE = 72
ICON_AIR = 1397

# Stock spells referenced by bare id (never imported from shaman_spells.py).
SPELL_HORN_OF_WINTER = 57330
SPELL_DEVOTION_AURA = 465
GROUP_ARMOR_BUFFS = 1086
GROUP_SPELL_POWER_BUFFS = 1048
GROUP_MELEE_HASTE_BUFFS = 1022
GROUP_MP5_BUFFS = 1105

STAT_STRENGTH = 0
STAT_AGILITY = 1
RESISTANCE_PHYSICAL = 1                 # MOD_RESISTANCE misc 1: armor
SCHOOL_MASK_ALL_MAGIC = 126             # MOD_DAMAGE_DONE misc: Holy through Arcane
SCHOOL_MASK_ALL = 127                   # MOD_HEALING_DONE misc

_PERSIST = {'AttributesEx2': SPELL_ATTR2_ALLOW_DEAD_TARGET, 'AttributesEx3': SPELL_ATTR3_ALLOW_AURA_WHILE_DEAD}


def _area(aura, base_points=0, points_per_level=0.0, misc_value=0):
    """One raid area-aura effect on the caster, 40 yd (Devotion Aura's shape)."""
    return Effect(
        type=EffectType.APPLY_AREA_AURA_RAID, base_points=base_points, points_per_level=points_per_level,
        implicit_target_a=TARGET_UNIT_CASTER, apply_aura=aura, misc_value=misc_value,
        radius_yards=ATTUNEMENT_RADIUS_YARDS,
    )


def _raw(spell_level, base_level, description=None, aura_description=None, **extra):
    """Columns every attunement row carries: shaman family with no bits, magic school defense, silence prevention,
    instant, GCD 1500 / 133, no equipped-item requirement, death persistence, level triple (MaxLevel 60)."""
    raw = {
        'SpellClassSet': SPELLFAMILY_SHAMAN,
        'EquippedItemClass': -1,
        'DefenseType': 1,
        'PreventionType': 1,
        'CastingTimeIndex': 1,
        'StartRecoveryCategory': 133,
        'StartRecoveryTime': 1500,
        'SpellLevel': spell_level,
        'BaseLevel': base_level,
        'MaxLevel': 60,
    }
    raw.update(_PERSIST)
    if description is not None:
        raw['Description_Lang_enUS'] = description
    if aura_description is not None:
        raw['AuraDescription_Lang_enUS'] = aura_description
    raw.update(extra)
    return raw


def _attunement(spell_id, name, icon, effects, spell_level, base_level, description, aura_description, notes):
    return spell(
        id=spell_id, name=name, school=School.NATURE, attributes=0, category=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
        effects=effects, spell_icon_id=icon, notes='shaman-rework SH0a A4: ' + notes,
        raw_overrides=_raw(spell_level, base_level, description, aura_description),
    )


def _child(spell_id, name, icon, effects, spell_level, base_level, notes):
    """Hidden child, cast on the shaman by the parent's `spell_sha_attunement` and removed with it. Not passive, so it
    is saved with the player and survives relog; hidden (DO_NOT_DISPLAY) so the bar shows only the parent."""
    return spell(
        id=spell_id, name=name, school=School.NATURE, attributes=SPELL_ATTR0_DO_NOT_DISPLAY | SPELL_ATTR0_DO_NOT_LOG,
        category=0, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=RANGE_SELF, duration_ms=-1, effects=effects, spell_icon_id=icon,
        notes='shaman-rework SH0a A4: ' + notes,
        raw_overrides=_raw(spell_level, base_level),
    )


# ---- Earth @10: Strength on the parent, armor on a hidden child (rule-4 armor group is whole-aura, B14) ----
earth_attunement_202207 = _attunement(
    202207, 'Earth Attunement', ICON_EARTH,
    [_area(AuraType.MOD_STAT, base_points=11, points_per_level=2.485716, misc_value=STAT_STRENGTH)],
    spell_level=10, base_level=10,
    description='Attunes you to Earth, increasing the armor and Strength of party and raid members within 40 yards.',
    aura_description='Armor and Strength increased.',
    notes='Strength = stock Strength of Earth 8076 eff0 x1.2 (136 at 60); armor comes from the child 202211. '
          'Group 1252 (rule 2) and 1253 (Str/Agi, rule 3).',
)
earth_attunement_armor_202211 = _child(
    202211, 'Earth Attunement Armor', ICON_EARTH,
    [_area(AURA_MOD_RESISTANCE, base_points=213, points_per_level=16.65792, misc_value=RESISTANCE_PHYSICAL)],
    spell_level=10, base_level=10,
    notes='hidden child of 202207: armor = stock Stoneskin 8072 eff0 x1.2 (1046 at 60). In stock group 1086 with '
          'Devotion Aura 465 (rule 4, highest wins).',
)

# ---- Water @20: mana per 5 sec, one effect, straight into the MP5 group ----
water_attunement_202208 = _attunement(
    202208, 'Water Attunement', ICON_WATER,
    [_area(AURA_MOD_POWER_REGEN, base_points=18, points_per_level=1.68)],
    spell_level=20, base_level=26,
    description='Attunes you to Water, restoring mana every 5 sec to party and raid members within 40 yards.',
    aura_description='Mana restored over time.',
    notes='mp5 = stock Mana Spring 5677 x1.2 (76 at 60; flat 19 until level 26, as the stock curve). Stock group 1105.',
)

# ---- Fire @26: spell haste on the parent, spell power on a hidden child (rule-4 SP group is whole-aura, B14) ----
fire_attunement_202209 = _attunement(
    202209, 'Fire Attunement', ICON_FIRE,
    [_area(AuraType.MOD_CASTING_SPEED_NOT_STACK, base_points=4)],
    spell_level=26, base_level=26,
    description='Attunes you to Fire, increasing the spell power of party and raid members within 40 yards and their '
                'spell haste by 5%.',
    aura_description='Spell power and spell haste increased.',
    notes='spell haste 5% (BP 4, aura 65, no stock group); spell power comes from the child 202212.',
)
fire_attunement_spell_power_202212 = _child(
    202212, 'Fire Attunement Spell Power', ICON_FIRE,
    [
        _area(AuraType.MOD_DAMAGE_DONE, base_points=29, points_per_level=3.24546, misc_value=SCHOOL_MASK_ALL_MAGIC),
        _area(AuraType.MOD_HEALING_DONE, base_points=29, points_per_level=3.24546, misc_value=SCHOOL_MASK_ALL),
    ],
    spell_level=26, base_level=28,
    notes='hidden child of 202209: spell power (aura 13 school mask 126 + aura 135) = stock Flametongue Totem 52109 '
          'x1.2 (133 at 60; flat 30 until level 28). In stock group 1048 (rule 4).',
)

# ---- Air @32: melee + ranged haste 10% and Agility ----
air_attunement_202210 = _attunement(
    202210, 'Air Attunement', ICON_AIR,
    [
        _area(AuraType.MOD_MELEE_HASTE, base_points=9),
        _area(AURA_MOD_RANGED_HASTE, base_points=9),
        _area(AuraType.MOD_STAT, base_points=65, points_per_level=2.5, misc_value=STAT_AGILITY),
    ],
    spell_level=32, base_level=32,
    description='Attunes you to Air, increasing the melee and ranged haste of party and raid members within 40 '
                'yards by 10% and their Agility.',
    aura_description='Melee and ranged haste and Agility increased.',
    notes='melee haste (138) and ranged haste (140, not 192) 10% each; Agility = stock Strength of Earth 8076 eff1 '
          'x1.2 (136 at 60). Groups 1252, 1253, 1022.',
)

scripted_by(earth_attunement_202207, 'spell_sha_attunement')
scripted_by(fire_attunement_202209, 'spell_sha_attunement')

# ---- Trainer 210 (priced by the learn-level curve) and spellbook entries ----
trained_by(earth_attunement_202207, TRAINER_SHAMAN, 10)
trained_by(water_attunement_202208, TRAINER_SHAMAN, 20)
trained_by(fire_attunement_202209, TRAINER_SHAMAN, 26)
trained_by(air_attunement_202210, TRAINER_SHAMAN, 32)

skill_line_ability(id=30640, skill_line=SKILL_LINE_ENHANCEMENT, spell_id=earth_attunement_202207.id,
                   class_mask=CLASS_MASK_SHAMAN, acquire_method=0)
skill_line_ability(id=30641, skill_line=SKILL_LINE_RESTORATION, spell_id=water_attunement_202208.id,
                   class_mask=CLASS_MASK_SHAMAN, acquire_method=0)
skill_line_ability(id=30642, skill_line=SKILL_LINE_ENHANCEMENT, spell_id=fire_attunement_202209.id,
                   class_mask=CLASS_MASK_SHAMAN, acquire_method=0)
skill_line_ability(id=30643, skill_line=SKILL_LINE_ENHANCEMENT, spell_id=air_attunement_202210.id,
                   class_mask=CLASS_MASK_SHAMAN, acquire_method=0)

# ---- Stacking groups (see the module docstring) ----
spell_group(1252, earth_attunement_202207, water_attunement_202208, fire_attunement_202209, air_attunement_202210)
spell_group_rule(1252, 2, 'Shaman Elemental Attunements: one per shaman')
spell_group(1253, SPELL_HORN_OF_WINTER, earth_attunement_202207, air_attunement_202210)
spell_group_rule(1253, 3, 'Strength and Agility: Horn of Winter, Earth and Air Attunement')

spell_group(GROUP_ARMOR_BUFFS, earth_attunement_armor_202211, SPELL_DEVOTION_AURA)
spell_group(GROUP_SPELL_POWER_BUFFS, fire_attunement_spell_power_202212)
spell_group(GROUP_MELEE_HASTE_BUFFS, air_attunement_202210)
spell_group(GROUP_MP5_BUFFS, water_attunement_202208)
