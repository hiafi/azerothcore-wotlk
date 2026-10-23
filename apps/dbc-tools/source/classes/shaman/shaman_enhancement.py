"""
Shaman - S3a A3: the Enhancement spec's new spells, buffs, helpers, creatures, tooltip entries and script bindings
(docs/reworks/shaman-enhancement-rework.md section 5/6; brief .agents/plans/shaman-rework/shaman-rework.S3a-WP-BRIEF.md id
map, S3-NOTES sections 2-6, S3a-0VERIFY).

Ids (Enhancement block 202360-202519):
    202360-202375  talent rank spells and the Living Earth castable (Elemental Charge, Living Earth, Volcanic Eruption 2,
                   Ascendance, Molten Fury 3, Spirit Guard 3, Shamanistic Focus r2/r3, Spirit Weapons r2/r3, Frozen Power r3)
    202376         [A3 addition] Shamanistic Focus capstone helper (the -1 s shock cooldown; see "Deviations" below)
    202380-202412  buffs and helpers (read by the C++ by id)
    202413         [S3a fix pass] Stormstrike cleave strike, main hand (clone of 32175 that procs nothing; M1)
    202414         [A3 addition] Elemental Ascendance speed helper (see "Deviations" below)
    202415         [S3a fix pass] Stormstrike cleave strike, off hand (clone of 32176 that procs nothing; M1)
    202416-202419  [playtest fix pass P2] the cosmetic ascend bursts at the shaman's feet: Fire / Frost / Wind / Earth (Elemental and
                   Earthen Ascendance share the Earth one); no damage, threat, aura or script binding
SkillLineAbility 30680 (Living Earth), creatures 300262-300265 (the four Elemental Spirit wolves), tooltip entries 1217-1219,
spell_group 1259.

Effect-index table (the C++ reads these; effect N below is the 0-based `GetEffect(N)` / `EFFECT_N`):
    Fire / Frost / Wind / Earth Charge (202380-83)  E0 DUMMY holder; the stack count is the charge count (CumulativeAura 10/10/10/60)
    Fire Ascendance 202387      E0 SPELLMOD_DAMAGE pct on Flame Shock (d0 b28), E1 SPELLMOD_DOT pct on Flame Shock (no transform since 2026-10-22)
    Frost Ascendance 202388     E0 SPELLMOD_DAMAGE pct on the Stormstrike strikes (d2 b10 / b12)
    Wind Ascendance 202389      E0 MOD_SPEED_ALWAYS (aura 129, stacks with Ghost Wolf's aura 31) +15 %, E1 SPELLMOD_DAMAGE pct on Gust (d2 b18; placeholder 0 %, the Mastery
                                share)
    Elemental Ascendance 202390 E0 SPELLMOD_DAMAGE pct 60 on Flame Shock + the Stormstrike strikes, E1 SPELLMOD_DOT pct 60 on Flame
                                Shock, E2 SPELLMOD_DAMAGE pct 100 on Gust; +30 % speed is the linked hidden aura 202414
    Earthen Ascendance 202393   E0 DUMMY (marker; the effects are script-side)
    Spirit Guard ranks 202368-70: E0 MOD_PARRY_PERCENT 0 (enables parry), E1 DUMMY = Rockbiter parry bonus 1/2/3 %, E2 DUMMY =
                                Stoneskin per parry 3/6/10 (live = stored + 1)
    Volcanic Eruption ranks 202362/63: E0 DUMMY = the Flametongue Attack chance 5/10 %
    Molten Fury ranks 202365-67: E0 SPELLMOD_DAMAGE pct (Magma pulse d0 b2 only + Fire Nova d1 b18 / b31), r3 E1 DUMMY capstone marker
Percent amounts the scripts pass or refresh are stored in the row as their base value (live - 1); the scripts set the live amount.

Conventions (copied from shaman_restoration.py / shaman_elemental.py)
- SpellClassSet 11 only where a SpellMod / aura 271 mask / class bit needs it; script-sized wolf rows (Spirit Flame Shock, the Frost
  copy) and the Wind Burst stay in family 0 so no shaman SpellMod and no all-zero-mask family-11 mod can reach them.
  `EquippedItemClass -1` on every row (L1). No row carries a family-11 DUMMY with icon 688 at effect 0 (SpellEffects.cpp:3754).
- Static rows store live - 1 (a +10 % mod is base_points 9). Visible buffs are non-passive with no consolidation flag
  (AttributesEx7 0x10000000 clear) and a number-free aura text; hidden helpers carry SPELL_ATTR0_DO_NOT_DISPLAY. State indicators
  (charges, the three single Ascendances, the Elemental Spirits timer) carry SPELL_ATTR0_NO_AURA_CANCEL (L-13). Nothing here is
  death-persistent (D9: charges, singles and Earthen Ascendance drop on death); only the hidden children that follow Rockbiter
  through death carry the L5 pair AttributesEx3 0x100000 + AttributesEx2 0x1.
- Potency rows set SpellLevel (the learn level of the granting row; the generator owns BaseLevel / MaxLevel).

Deviations from the brief's id map (recorded in the S3a-A3 report):
- 202376 SHAMANISTIC_FOCUS_CAPSTONE: rank 3 needs crit + damage + DOT + the -1 s cooldown = four SpellMod effects and a spell holds three.
  The cooldown cut lives on this hidden passive, applied in lockstep with rank 3 (202372) by `spell_linked_spell` type 2 (data only).
- 202414 ELEMENTAL_ASCENDANCE_SPEED: Elemental Ascendance needs Flame Shock damage + DOT + Stormstrike + Gust x2(1 + M) + speed = four
  effects and a spell holds three. The three Mastery-scaled SpellMods stay on the buff (B1 refreshes every DAMAGE / DOT SpellMod
  effect of the buff); the +30 % speed lives on this hidden aura, applied and removed in lockstep with 202390 by `spell_linked_spell` type 2.
"""

from lib.dsl import AuraType, Effect, EffectType, RANGE_SELF, School, SpellModOp
from lib.dsl.registry import (
    const, creature_model, creature_template, custom_attr, linked_spell, pot_text, procs_on, scripted_by, skill_line_ability, spell,
    spell_group, spell_group_rule,
)

from . import _masks as m
from .shaman_enh_tooltips import shaman_imbuehits_1218, shaman_livearth_1219, shaman_lshield_1217  # noqa: F401  (1217 / 1218 are A2 / A4's to attach)

SPELLFAMILY_SHAMAN = 11
NOTE = 'shaman-rework S3a A3: '

# ---- Spell.dbc flag values ------------------------------------------------------------------------------------------
ATTR0_PASSIVE_HIDDEN = 0x1D0          # PASSIVE | DO_NOT_DISPLAY | ...: the talent-rank shape (stock attributes 464)
ATTR0_HIDDEN_PASSIVE = 0xC0           # PASSIVE | DO_NOT_DISPLAY: the imbue children's shape (shaman_imbues.py)
ATTR0_DO_NOT_DISPLAY = 0x80
ATTR0_NO_AURA_CANCEL = 0x80000000      # SPELL_ATTR0_CANT_CANCEL: no right-click cancel (SpellHandler.cpp)
ATTR2_ALLOW_DEAD_TARGET = 0x1
ATTR2_IGNORE_LOS = 0x4
ATTR3_SUPPRESS_CASTER_PROCS = 0x10000
ATTR4_SUPPRESS_WEAPON_PROCS = 0x00800000   # no item / enchant procs from a melee-class hit (Spell.cpp CastItemCombatSpell)
ATTR3_ALLOW_AURA_WHILE_DEAD = 0x100000
ATTR5_NO_CASTER_AURA_ICON = 0x08000000  # the shaman's own periodic aura shows no icon (Earthquake / Healing Rain)

TARGET_UNIT_CASTER = 1
TARGET_UNIT_TARGET_ENEMY = 6
TARGET_UNIT_SRC_AREA_ENEMY = 15
TARGET_UNIT_DEST_AREA_ENEMY = 16
TARGET_SRC_CASTER = 22
TARGET_DEST_DYNOBJ_ENEMY = 28
TARGET_DEST_DEST = 87

EFFECT_DISPEL_MECHANIC = 108
EFFECT_ATTACK_ME = 114
AURA_MOD_PARRY_PERCENT = 47            # not in the DSL's AuraType subset
MECHANIC_ROOT = 7
MECHANIC_SNARE = 11
STAT_AGILITY = 1

SCHOOL_ALL = 127
SCHOOL_MASK_ALL_MAGIC = 126
SCHOOL_MASK_FIRE_FROST_NATURE = 28     # 4 + 16 + 8: the "Fire, Frost and Nature damage" of Unleashed Rage / Dual Wield Spec
SCHOOL_MASK_PHYSICAL = 1

PROC_FLAG_DONE_MELEE_AUTO = 0x4
PROC_FLAG_TAKEN_MELEE_AUTO = 0x8
PROC_FLAG_DONE_SPELL_MELEE = 0x10
PROC_FLAG_TAKEN_SPELL_MELEE = 0x20
PROC_FLAG_DONE_MAGIC_NEG = 0x10000
PROC_ATTR_TRIGGERED_CAN_PROC = 0x2
PROC_ATTR_REQ_SPELLMOD = 0x8
PROC_HIT_PARRY = 0x20
PHASE_CAST = 0x1
PHASE_HIT = 0x2
TYPE_DAMAGE = 0x1

SKILL_LINE_ENHANCEMENT = 373
CLASS_MASK_SHAMAN = 64

# ---- Family masks (SpellClassSet 11) ---------------------------------------------------------------------------------------
FLAME_SHOCK = 0x10000000              # d0 b28 (also the periodic ticks)
SHOCKS = 0x90100000                   # d0: Earth b20, Flame b28, Frost b31
SS_STRIKES_D2 = 0x1400                # d2 b10 | b12: the Stormstrike strikes 32175 / 32176 (Spirit Weapons' bits)
LAVA_LASH_D2 = 0x4                    # d2 b2: Lava Lash 60103
FIRE_NOVA_DAMAGE = 0x80040000         # d1 b18 | b31: Fire Nova 8349
# Improved Stormstrike's aura 271 mask (S3a-0VERIFY "Settled shapes" D11): every shaman Fire / Frost / Nature damage bit.
IMP_SS_D0 = 0x91300403                # LB b0, CL b1, orb b10, Earth Shock b20, Flametongue b21, Frostbrand b24, Flame Shock b28, Frost Shock b31
IMP_SS_D1 = 0x80041000                # Lava Burst b12, Fire Nova b18 / b31
IMP_SS_D2 = 0x20180004                # Lava Lash b2, Earthquake b19, Elemental Blast b20, ENH_SPELL_HIT b29
MQ_MELEE_D2 = SS_STRIKES_D2 | LAVA_LASH_D2   # the direct melee abilities Mental Quickness boosts
# The direct damaging spells Mental Quickness' spell buff boosts (S3a code review m3): Lightning Bolt b0, Chain Lightning b1, the
# three shocks (SHOCKS), Lava Burst d1 b12, Elemental Blast d2 b20. Same set as the capstone's proc row (30814).
MQ_SPELLS_D0 = SHOCKS | 0x3
MQ_SPELLS_D1 = 0x1000
MQ_SPELLS_D2 = m.ELEMENTAL_BLAST

# ---- Stock spell ids the rows reference ------------------------------------------------------------------------------------
SPELL_ROCKBITER = 8017

# ---- Spell icons (stock SpellIconID; unique inside the Enhancement talent tree, art is the V stage) ---------------------------
ICON_ELEMENTAL_CHARGE = 680            # Searing Totem
ICON_LIVING_EARTH = 93                 # Stoneform (the doc: "stone shell on the shaman, stock Stoneform tint")
ICON_VOLCANIC_ERUPTION = 3064          # Lava Burst
ICON_ASCENDANCE = 3080                 # Thunderstorm
ICON_MOLTEN_FURY = 37                  # Magma Totem
ICON_SPIRIT_GUARD = 28                 # Block
ICON_SHAMANISTIC_FOCUS = 2016          # the talent's stock icon (ranks 2 / 3 share it)
ICON_SPIRIT_WEAPONS = 558              # the talent's stock icon
ICON_FROZEN_POWER = 3780               # the talent's stock icon
ICON_FIRE = 678                        # Flame Shock
ICON_FROST = 681                       # Frostbrand Weapon
ICON_WIND = 220                        # Windfury Weapon
ICON_EARTH = 687                       # Earth Shock (never 688: the family-11 DUMMY icon-688 Lava Lash hardcode)
ICON_FIRE_NOVA = 33
ICON_CHAIN_LIGHTNING = 165
ICON_FIRE_ELEMENTAL = 2290
ICON_EARTH_ELEMENTAL = 2289
ICON_WRATH_OF_AIR = 340
ICON_STONESKIN = 690
ICON_GHOST_WOLF = 67
ICON_THUNDERING_STRIKES = 25
ICON_LAVA_LASH = 3741
ICON_DUAL_WIELD_SPEC = 2023
ICON_IMPROVED_STORMSTRIKE = 3159
ICON_STORMSTRIKE = 2562
ICON_BLIZZARD = 285
ICON_UNLEASHED_RAGE = 2021
ICON_MENTAL_QUICKNESS = 2022
ICON_SPIRIT_WOLF = 3081
ICON_LIGHTNING_SHIELD = 19
ICON_TAUNT = 24
ICON_EARTH_SHOCK = 687

# Stock visuals: Stoneform 5787, Blizzard's ground kit 9490 and its tick missile 9487, Taunt 34. The ascend bursts (P2, 2026-10-22):
# 963 Fire Nova (the NPC nova 11969 / Blast Wave; cast kit 984 = FireNova_Area.mdx at the caster's base), 17 Frost Nova (cast kit 160 =
# Frost_Nova_area.mdx at the caster's base), 11302 Thunderstorm (cast kit 10459 = shaman_thunder.mdx world effect), 5719 War Stomp (cast
# kit 5089 = ThunderClap_Cast_Base.mdx world effect). All four have their aura-time state kit unused: the helpers apply no aura.
SV_ASCEND_FIRE = 963
SV_ASCEND_FROST = 17
SV_ASCEND_WIND = 11302
SV_ASCEND_EARTH = 5719
SV_STONEFORM = 5787
SV_BLIZZARD_AREA = 9490
SV_BLIZZARD_TICK = 9487
SV_TAUNT = 34

# Stock wolf (Spirit Wolf 29264): display 21114 (Wolf_ghost.mdx).
DISPLAY_SPIRIT_WOLF = 21114


# =====================================================================================================================
# Script numbers (generated into ShamanData::). The brief's list; per-rank percentages come from a rank's DUMMY effect
# (L-8), these are the fixed ones.
# =====================================================================================================================
CHARGE_CAP_ELEMENT = const('CHARGE_CAP_ELEMENT', 10, 'Elemental Charge: maximum Fire / Frost / Wind charges [fixed]; also the CumulativeAura of 202380-82.')
CHARGE_CAP_EARTH = const('CHARGE_CAP_EARTH', 60, 'Elemental Charge: maximum Earth Charge [fixed]; also the CumulativeAura of 202383.')
EC_AUTO_CHANCE = const('EC_AUTO_CHANCE', 20, 'Elemental Charge: chance a melee auto attack grants 1 charge, percent (Proc Chance applies) [fixed].')
EC_OOC_MS = const('EC_OOC_MS', 120000, 'Elemental Charge: out-of-combat time before the charges clear, ms [fixed].')
SR_CHARGES = const('SR_CHARGES', 5, 'Shamanistic Rage: charges of the active imbue granted on cast (banked during Elemental Ascendance) [fixed].')
BURST_TARGETS = const('BURST_TARGETS', 5, 'Elemental Burst: enemies hit, nearest engaged first [fixed].')
BURST_RADIUS_YD = const('BURST_RADIUS_YD', 5.0, 'Elemental Burst: radius around the target (the shaman with no target), yd [fixed].')
ASC_DURATION_EA_MS = const('ASC_DURATION_EA_MS', 20000, 'Elemental Ascendance: duration, ms [fixed].')
ASC_OOC_MS = const('ASC_OOC_MS', 120000, 'Ascendance: out-of-combat time before a held single Ascendance falls off, ms [fixed].')
LE_STONESKIN = const('LE_STONESKIN', 10, 'Living Earth: Stoneskin stacks granted [fixed].')
LE_EARTH_CHARGE_COST = const('LE_EARTH_CHARGE_COST', 30, 'Living Earth: Earth Charge spent for Earthen Ascendance [fixed].')
EARTHEN_ASC_DURATION_MS = const('EARTHEN_ASC_DURATION_MS', 10000, 'Earthen Ascendance: duration, ms [fixed].')
EARTHEN_ASC_RADIUS_YD = const('EARTHEN_ASC_RADIUS_YD', 8.0, 'Earthen Ascendance: radius of the Earth Shock copies around the shaman, yd [tune].')
GUST_CHANCE = const('GUST_CHANCE', 15, 'Gust: chance per melee hit under Wind / Elemental Ascendance and per Wind Spirit bite, percent (Proc Chance applies) [fixed].')
GUST_SPLASH_RADIUS_YD = const('GUST_SPLASH_RADIUS_YD', 8.0, 'Gust splash: radius around the struck target, yd [fixed].')
GUST_SPLASH_TARGETS = const('GUST_SPLASH_TARGETS', 5, 'Gust splash: enemies hit besides the struck target [fixed].')
SS_CLEAVE_RADIUS_YD = const('SS_CLEAVE_RADIUS_YD', 8.0, 'Stormstrike cleave: radius around the target, yd [tune].')
TOUGHNESS_THRESHOLD_PCT = const('TOUGHNESS_THRESHOLD_PCT', 35, 'Toughness capstone: health percent below which Stoneskin erodes slower [fixed].')
TOUGHNESS_ERODE_PCT = const('TOUGHNESS_ERODE_PCT', 50, 'Toughness capstone: percent of the normal Stoneskin erosion that remains [fixed].')
MW_CHANCE_STEP = const('MW_CHANCE_STEP', 7, 'Maelstrom Weapon: chance per rank, percent (7 / 14 / 21; Proc Chance applies) [tune].')
FS_SPREAD_TARGETS = const('FS_SPREAD_TARGETS', 4, 'Elemental Weapons capstone: enemies the Flame Shock spreads to [fixed].')
FS_SPREAD_RADIUS_YD = const('FS_SPREAD_RADIUS_YD', 10.0, 'Elemental Weapons capstone: spread radius, yd [tune].')
SS_STATIC_SHOCK_CHARGES = const('SS_STATIC_SHOCK_CHARGES', 3, 'Static Shock capstone: Lightning Shield charges Stormstrike adds [fixed].')
SS_STATIC_SHOCK_CAP = const('SS_STATIC_SHOCK_CAP', 9, 'Static Shock capstone: Lightning Shield charge cap (3 + the talent\'s 6) [fixed].')
ILS_NO_EXPEND_CHANCE = const('ILS_NO_EXPEND_CHANCE', 30, 'Improved Lightning Shield capstone: chance an orb does not expend a charge, percent (Proc Chance applies) [fixed].')
ILS_ORB_STONESKIN = const('ILS_ORB_STONESKIN', 1, 'Improved Lightning Shield: Stoneskin per orb under Rockbiter [fixed].')
SPIRIT_GUARD_STONESKIN_R1 = const('SPIRIT_GUARD_STONESKIN_R1', 3, 'Spirit Guard rank 1: Stoneskin per parry under Rockbiter [fixed].')
SPIRIT_GUARD_STONESKIN_R2 = const('SPIRIT_GUARD_STONESKIN_R2', 6, 'Spirit Guard rank 2: Stoneskin per parry under Rockbiter [fixed].')
SPIRIT_GUARD_STONESKIN_R3 = const('SPIRIT_GUARD_STONESKIN_R3', 10, 'Spirit Guard rank 3: Stoneskin per parry under Rockbiter [fixed].')
GUARDIAN_TOTEMS_ARMOR_DURATION_MS = const('GUARDIAN_TOTEMS_ARMOR_DURATION_MS', 10000, 'Guardian Totems capstone: armor buff duration, ms [fixed].')
ES_TAUNT_DURATION_MS = const('ES_TAUNT_DURATION_MS', 3000, 'Earth Shock under Rockbiter: taunt duration, ms [tune].')
IGW_SPRINT_ICD_MS = const('IGW_SPRINT_ICD_MS', 20000, 'Improved Ghost Wolf capstone: internal cooldown of the sprint, ms [fixed].')
TS_CHANCE = const('TS_CHANCE', 10, 'Thundering Strikes capstone: chance per spell cast, percent (Proc Chance applies) [fixed].')
TS_ICD_MS = const('TS_ICD_MS', 6000, 'Thundering Strikes capstone: internal cooldown, ms [fixed].')
MQ_SPELLS_PCT = const('MQ_SPELLS_PCT', 10, 'Mental Quickness capstone: spell damage bonus after a direct melee ability, percent [fixed].')
MQ_MELEE_PCT = const('MQ_MELEE_PCT', 5, 'Mental Quickness capstone: melee ability damage bonus after a damaging spell, percent [fixed].')
VE_CHANCE_R1 = const('VE_CHANCE_R1', 5, 'Volcanic Eruption rank 1: chance per Flametongue Attack, percent (Proc Chance applies) [fixed].')
VE_CHANCE_R2 = const('VE_CHANCE_R2', 10, 'Volcanic Eruption rank 2: chance per Flametongue Attack, percent (Proc Chance applies) [fixed].')
FP_BLIZZARD_DURATION_MS = const('FP_BLIZZARD_DURATION_MS', 8000, 'Frozen Power capstone: Blizzard duration, ms [fixed]; also 202404\'s duration.')
FP_BLIZZARD_RADIUS_YD = const('FP_BLIZZARD_RADIUS_YD', 8.0, 'Frozen Power capstone: Blizzard radius, yd [tune]; also 202404\'s radius.')
WOLF_DURATION_MS = const('WOLF_DURATION_MS', 20000, 'Elemental Spirits: wolf duration, ms [fixed]; also 51533\'s and the timer 202407\'s duration.')
WOLF_FS_POTENCY = const('WOLF_FS_POTENCY', 25, 'Spirit Flame Shock: potency per 3 s tick [tune]; also the 202408 row.')
FROST_COPY_PCT = const('FROST_COPY_PCT', 50, 'Frost Spirit: percent of the shaman\'s Stormstrike damage the copy deals [tune].')
ROCK_TAUNT_RADIUS_YD = const('ROCK_TAUNT_RADIUS_YD', 10.0, 'Rock Spirit: taunt radius on summon, yd [tune]; also 202410\'s radius.')
ROCK_SPIRIT_STONESKIN_PER_HIT = const('ROCK_SPIRIT_STONESKIN_PER_HIT', 1, 'Rock Spirit: Stoneskin the shaman gains per Rock Spirit hit [fixed].')
ROCK_TAUNT_MS = const('ROCK_TAUNT_MS', 3000, 'Rock Spirit: taunt duration, ms [tune]; also 202410\'s duration.')
UR_R1 = const('UR_R1', 3, 'Unleashed Rage rank 1: magic damage bonus while Shamanistic Rage or Elemental Ascendance is up, percent [fixed].')
UR_R2 = const('UR_R2', 6, 'Unleashed Rage rank 2: magic damage bonus, percent [fixed].')
UR_R3 = const('UR_R3', 9, 'Unleashed Rage rank 3: magic damage bonus, percent [fixed].')
MOLTEN_FURY_RAMP_PCT = const('MOLTEN_FURY_RAMP_PCT', 10, 'Molten Fury capstone: Magma Totem damage bonus per pulse already fired, percent [fixed].')
MASTERY_ROUND_PCT = const('MASTERY_ROUND_PCT', 1, 'Ascendance capstone: Mastery is rounded to whole percent in the integer aura amounts (Stoneskin 1 % x (1 + M) per stack) [fixed].')


# =====================================================================================================================
# Helpers
# =====================================================================================================================
def _text(description: str = '', aura: str = '') -> dict:
    return {
        'Description_Lang_Mask': 16712190 if description else 16712188,
        'Description_Lang_enUS': description,
        'AuraDescription_Lang_Mask': 16712190 if aura else 16712188,
        'AuraDescription_Lang_enUS': aura,
        'Name_Lang_Mask': 16712190,
        'NameSubtext_Lang_Mask': 16712188,
    }


def _emask(effect: int, mask) -> dict:
    """EffectSpellClassMask{A,B,C}_{1,2,3}: the LETTER is the effect (1 -> A), the number the dword. `mask` is an int
    (dword 0) or a (d0, d1, d2) tuple."""
    letter = 'ABC'[effect - 1]
    dwords = mask if isinstance(mask, tuple) else (mask, 0, 0)
    return {f'EffectSpellClassMask{letter}_{i + 1}': value for i, value in enumerate(dwords) if value}


def _raw(description: str = '', aura: str = '', level: int = 1, family: bool = True, **extra) -> dict:
    raw = {
        **_text(description, aura),
        'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0,
        'CastingTimeIndex': 1,
        'EquippedItemClass': -1,
        'ProcChance': 101,
        'SpellLevel': level,
    }
    if family:
        raw['SpellClassSet'] = SPELLFAMILY_SHAMAN
    raw.update(extra)
    return raw


def _aura(aura, base_points: int = 0, misc_value: int = 0, target: int = TARGET_UNIT_CASTER, **kw) -> Effect:
    return Effect(type=EffectType.APPLY_AURA, apply_aura=aura, base_points=base_points, misc_value=int(misc_value),
                  implicit_target_a=target, **kw)


def _mod(op: SpellModOp, pct: bool, base_points: int) -> Effect:
    """A self-targeted SpellMod; the scope mask goes through `_emask` on the same effect slot."""
    return _aura(AuraType.ADD_PCT_MODIFIER if pct else AuraType.ADD_FLAT_MODIFIER, base_points, int(op))


def _dummy(base_points: int = 0) -> Effect:
    return _aura(AuraType.DUMMY, base_points)


def _desc(text: str, capstone: str | None = None, last: bool = False) -> str:
    """talent-tooltip-audit step 5: grey capstone clause on every non-final rank, plain on the final one."""
    if capstone is None:
        return text
    if last:
        return f'{text}\n\nCapstone Bonus: {capstone}'
    return f'{text}\n\n|cFF9D9D9DCapstone Bonus: {capstone}|r'


def _rank(spell_id: int, name: str, effects: list, icon: int, level: int, description: str, notes: str,
          subtext: str = '', **raw_extra):
    """A talent rank spell: hidden passive, infinite, self."""
    raw = _raw(description, '', level, **raw_extra)
    if subtext:
        raw['NameSubtext_Lang_Mask'] = 16712190
        raw['NameSubtext_Lang_enUS'] = subtext
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=ATTR0_PASSIVE_HIDDEN,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=RANGE_SELF, duration_ms=-1, effects=effects, spell_icon_id=icon,
        notes=NOTE + notes, raw_overrides=raw,
    )


def _buff(spell_id: int, name: str, effects: list, icon: int, duration_ms: int, aura: str = '', description: str = '',
          notes: str = '', school=School.NATURE, hidden: bool = False, stacks: int = 0, charges: int = 0,
          level: int = 1, family: bool = True, range_yards=RANGE_SELF, no_cancel: bool = False, **raw_extra):
    """A buff. Visible by default (non-passive, no consolidation flag); `hidden` adds DO_NOT_DISPLAY; `no_cancel` adds
    SPELL_ATTR0_NO_AURA_CANCEL (a state indicator the player must not click off). `stacks` = CumulativeAura,
    `charges` = ProcCharges."""
    raw = _raw(description, aura, level, family, **raw_extra)
    if stacks:
        raw['CumulativeAura'] = stacks
    if charges:
        raw['ProcCharges'] = charges
        raw['ProcChance'] = 100
    return spell(
        id=spell_id, name=name, school=school,
        attributes=(ATTR0_DO_NOT_DISPLAY if hidden else 0) | (ATTR0_NO_AURA_CANCEL if no_cancel else 0),
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=range_yards, duration_ms=duration_ms, effects=effects, spell_icon_id=icon,
        notes=NOTE + notes, raw_overrides=raw,
    )


def _hidden_child(spell_id: int, name: str, effects: list, icon: int, school, description: str, notes: str, **raw_extra):
    """A hidden passive child that follows its parent through death (the imbue children's shape, L5): PASSIVE |
    DO_NOT_DISPLAY, infinite, AttributesEx3 ALLOW_AURA_WHILE_DEAD + AttributesEx2 ALLOW_DEAD_TARGET, no family bits."""
    raw = _raw(description, '', 1, AttributesEx2=ATTR2_ALLOW_DEAD_TARGET, AttributesEx3=ATTR3_ALLOW_AURA_WHILE_DEAD,
               **raw_extra)
    return spell(
        id=spell_id, name=name, school=school, attributes=ATTR0_HIDDEN_PASSIVE,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
        range_yards=RANGE_SELF, duration_ms=-1, effects=effects, spell_icon_id=icon,
        notes=NOTE + notes, raw_overrides=raw,
    )


# =====================================================================================================================
# Elemental Charge: the four charge buffs and the three Elemental Bursts (202380-202386)
# =====================================================================================================================
_FIRE_CHARGE_TEXT = ('Elemental energy builds up from your attacks. Swapping imbues at full charge releases an Elemental '
                     'Burst.')
_EARTH_CHARGE_TEXT = 'Earth energy builds up from your attacks. Living Earth can spend it.'


def _charge(spell_id: int, name: str, school, icon: int, stacks: int, text: str, element: str, notes: str):
    return _buff(
        spell_id, name, [_dummy()], icon, -1, text, text,
        f'{element} Charge: visible state indicator, non-passive, no consolidation flag, ATTR0 0x80000000 (no right-click '
        f'cancel, L-13), infinite (the 2 min out-of-combat clear is Shaman::OnEnhCombatChange\'s, EC_OOC_MS), not '
        f'death-persistent (D9). E0 DUMMY holder; CumulativeAura {stacks} is the cap and the stack count IS the charge count '
        f'(P0 5a: stack counts show on the client). No family bits. {notes}',
        school=school, stacks=stacks, level=15, no_cancel=True,
    )


fire_charge_202380 = _charge(
    202380, 'Fire Charge', School.FIRE, ICON_FIRE, 10, _FIRE_CHARGE_TEXT, 'Fire',
    'Built under Flametongue; swapping away at 10 releases Flame Burst and grants Fire Ascendance.')
frost_charge_202381 = _charge(
    202381, 'Frost Charge', School.FROST, ICON_FROST, 10, _FIRE_CHARGE_TEXT, 'Frost',
    'Built under Frostbrand; swapping away at 10 releases Storm Burst and grants Frost Ascendance.')
wind_charge_202382 = _charge(
    202382, 'Wind Charge', School.NATURE, ICON_WIND, 10, _FIRE_CHARGE_TEXT, 'Wind',
    'Built under Windfury; swapping away at 10 releases Wind Burst and grants Wind Ascendance.')
earth_charge_202383 = _charge(
    202383, 'Earth Charge', School.NATURE, ICON_EARTH, 60, _EARTH_CHARGE_TEXT, 'Earth',
    'Built under Rockbiter (Earth Shock grants 1); Living Earth spends 30 for Earthen Ascendance. Icon 687, never 688.')


def _burst(spell_id: int, name: str, school, effect_description: str, icon: int, spell_description: str,
           notes: str, magic: bool, **raw_extra):
    """An Elemental Burst: SCHOOL_DAMAGE 150 potency per target on the area around a destination (Fire Nova 8349's A 87 /
    B 16 shape, 5 yd), triggered by Shaman::CastElementalBurst at the shaman's target (or the shaman), range 50000 (L6)."""
    sp = 150.0 if magic else 0.0
    ap = 0.0 if magic else 150.0
    raw = _raw(spell_description, '', 15, family=magic, DefenseType=1 if magic else 2, PreventionType=1 if magic else 0,
               AttributesEx3=ATTR3_SUPPRESS_CASTER_PROCS, **raw_extra)
    return spell(
        id=spell_id, name=name, school=school, attributes=0,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0,
        effects=[Effect(
            type=EffectType.SCHOOL_DAMAGE, sp_potency=sp, ap_potency=ap, potency_kind='direct', time_basis_ms=1500,
            implicit_target_a=TARGET_DEST_DEST, implicit_target_b=TARGET_UNIT_DEST_AREA_ENEMY, radius_yards=5.0,
        )],
        spell_icon_id=icon,
        notes=NOTE + notes + ' Potency 150 direct, T 1500, SpellLevel 15 (Elemental Charge\'s row). SchoolMask ' + effect_description +
              '. Area targets as Fire Nova 8349 (A 87 DEST_DEST, B 16, radius 5 yd = BURST_RADIUS_YD) so the caster picks the '
              'centre by the cast target (the shaman\'s current target, else the shaman); spell_sha_enh_burst filters to '
              'enemies in combat with the shaman or the group and keeps the BURST_TARGETS nearest (Q16). Triggered with no '
              'NOT_A_PROC and AttributesEx3 SUPPRESS_CASTER_PROCS: it rolls nothing and no proc row accepts a triggered '
              'cast; it can crit. range_yards 50000 (L6).',
        raw_overrides=raw,
    )


# Flame Burst (Fire, spell potency) and Storm Burst (Frost + Nature, spell potency) carry d2 b29 ENH_SPELL_HIT so Improved
# Stormstrike's aura 271 reaches them; Wind Burst (Physical, attack power potency, melee class) carries nothing and stays out.
flame_burst_202384 = _burst(
    202384, 'Flame Burst', School.FIRE, 'Fire (4)', ICON_FIRE_NOVA,
    'Deals {pot1} Fire damage to up to 5 enemies within 5 yards of your target.',
    'Flame Burst, released by swapping away from Flametongue at 10 Fire Charge. Family d2 b29.', True,
    SpellClassMask_3=m.ENH_SPELL_HIT,
)
storm_burst_202385 = _burst(
    202385, 'Storm Burst', School.FROST | School.NATURE, 'Frost + Nature (24)', ICON_CHAIN_LIGHTNING,
    'Deals {pot1} Frost and Nature damage to up to 5 enemies within 5 yards of your target.',
    'Storm Burst, released by swapping away from Frostbrand at 10 Frost Charge. Family d2 b29.', True,
    SpellClassMask_3=m.ENH_SPELL_HIT,
)
wind_burst_202386 = _burst(
    202386, 'Wind Burst', School.NORMAL, 'Physical (1)', ICON_WIND,
    'Deals {pot1} Physical damage to up to 5 enemies within 5 yards of your target.',
    'Wind Burst, released by swapping away from Windfury at 10 Wind Charge. ap_potency 150, DmgClass MELEE (D6), SpellClassSet 0 '
    '(no family bits, so no shaman SpellMod and not Improved Stormstrike\'s aura 271).', False,
)
for _burst_spell in (flame_burst_202384, storm_burst_202385, wind_burst_202386):
    scripted_by(_burst_spell, 'spell_sha_enh_burst')


# =====================================================================================================================
# Gust and its splash (202391 / 202392): Physical, attack power potency, d2 b18
# =====================================================================================================================
def _gust(spell_id: int, name: str, potency: float, description: str, notes: str, suppress_caster_procs: bool = False):
    # AttributesEx4 SUPPRESS_WEAPON_PROCS on both (S3a code review M1b): a melee-class hit would otherwise run
    # CastItemCombatSpell, giving weapon-enchant and item procs (up to 6 per Gust with the splash). The Gust itself must keep
    # reaching Maelstrom Weapon, so only the splash also carries SUPPRESS_CASTER_PROCS (it rolls nothing at all).
    extra = {'AttributesEx3': ATTR3_SUPPRESS_CASTER_PROCS} if suppress_caster_procs else {}
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=0,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=potency, potency_kind='direct', time_basis_ms=1500,
                        implicit_target_a=TARGET_UNIT_TARGET_ENEMY)],
        spell_icon_id=ICON_WRATH_OF_AIR,
        notes=NOTE + notes + ' ap_potency ' + str(potency) + ' direct, T 1500, SpellLevel 40 (Ascendance\'s row), Physical, DmgClass '
              'MELEE (D6: Flurry never sees it, it is dodgeable), d2 b18 GUST (Improved Windfury, the Ascendance Gust mods). '
              'Triggered with no NOT_A_PROC: ' + (
                  'it rolls Maelstrom Weapon only (the MW row\'s CheckProc whitelist, named exception) and nothing else; '
                  'AttributesEx4 SUPPRESS_WEAPON_PROCS (0x00800000) keeps weapon-enchant and item procs off it. '
                  if not suppress_caster_procs else
                  'AttributesEx3 SUPPRESS_CASTER_PROCS + AttributesEx4 SUPPRESS_WEAPON_PROCS: it rolls nothing at all (no '
                  'Maelstrom Weapon, no enchant or item procs). ') +
              'range_yards 50000, AttributesEx2 IGNORE_LOS: the Wind Spirit\'s Gusts are cast by the shaman '
              'at the wolf\'s target.',
        raw_overrides=_raw(
            description, '', 40, DefenseType=2, PreventionType=0, AttributesEx2=ATTR2_IGNORE_LOS,
            AttributesEx4=ATTR4_SUPPRESS_WEAPON_PROCS, SpellClassMask_3=m.GUST, **extra,
        ),
    )


gust_202391 = _gust(
    202391, 'Gust', 35.0, 'Deals {pot1} Physical damage to the target.',
    'the Gust: rolled by Wind / Elemental Ascendance (the aura proc rows below) and by the Wind Spirit.')
gust_splash_202392 = _gust(
    202392, 'Gust', 17.5, 'Deals {pot1} Physical damage to the target.',
    'the Gust splash, half of the Gust, cast by spell_sha_enh_gust at up to GUST_SPLASH_TARGETS other enemies within '
    'GUST_SPLASH_RADIUS_YD of the struck target. It never rolls Gust (triggered) and rolls nothing else (SUPPRESS_CASTER_PROCS).',
    suppress_caster_procs=True)
scripted_by(gust_202391, 'spell_sha_enh_gust')


# =====================================================================================================================
# Stormstrike cleave strikes (202413 / 202415): the proc-free copies of the stock strikes 32175 / 32176
# =====================================================================================================================
SV_STORMSTRIKE = 7660                  # 32175's SpellVisualID_1 (32176 has none)


def _cleave_strike(spell_id: int, off_hand: bool):
    """A clone of the stock Stormstrike strike (32175 main hand / 32176 off hand) for the Frost / Elemental Ascendance cleave
    (S3a code review M1a). The stock strikes carry SPELL_ATTR3_NOT_A_PROC (that is how the primary Stormstrike's hits reach
    Flametongue, Windfury, Frostbrand and Static Shock), so cast on the cleave targets they would roll every one of those procs
    (and weapon-enchant / item procs). The clone drops NOT_A_PROC and adds SUPPRESS_CASTER_PROCS (Spell.cpp canEffectTrigger: no
    proc event at all, so no CastItemCombatSpell either) and SUPPRESS_WEAPON_PROCS (belt and braces). Everything else is the
    stock row, so the damage is the primary strike's: effect 58 (weapon damage, base 0 / die 0), school Physical, melee range,
    DefenseType 2, SpellLevel 40 and the REQUIRES_MAIN_HAND 0x400 / REQUIRES_OFF_HAND 0x1000000 attack-type pick (SpellInfo
    ::GetAttackType). EquippedItemClass is -1, not the stock 2 / 173555: the cleave is always a triggered cast (the
    weapon check is skipped) and -1 is the rule for custom rows (the Windfury Attacks' shape, custom-spells.md). Family bits d2 b10 / b12 (SS_STRIKES_D2) are
    kept, so Frost / Elemental Ascendance, Spirit Weapons, Improved Stormstrike's crit and Mental Quickness' melee buff still
    apply. The stock d1 b4 (magic-GCD haste, FORBIDDEN_D1_B4) is dropped: a triggered strike has no GCD. The stock
    ProcTypeMask / ProcCharges (dead on a non-aura spell) are not copied."""
    return spell(
        id=spell_id, name='Stormstrike', school=School.NORMAL, attributes=0x250010 if off_hand else 0x250000,
        power_type=3 if off_hand else 0,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=5.0,
        effects=[Effect(
            type=EffectType.WEAPON_DAMAGE, base_points=0, die_sides=0, implicit_target_a=TARGET_UNIT_TARGET_ENEMY,
            potency_excluded='clone of the stock Stormstrike strike ' + ('32176' if off_hand else '32175') + ': 100% weapon damage '
                             'like the primary strike, level independent.',
        )],
        spell_icon_id=ICON_STORMSTRIKE,
        notes=NOTE + 'Stormstrike cleave strike, ' + ('off hand (clone of 32176)' if off_hand else 'main hand (clone of 32175)') +
              ': cast by spell_sha_enh_stormstrike::Cleave on the Frost Ascendance (1) / Elemental Ascendance (2) cleave targets. '
              'Same as the stock strike except AttributesEx3 loses NOT_A_PROC (0x200) and gains SUPPRESS_CASTER_PROCS (0x10000), '
              'AttributesEx4 gains SUPPRESS_WEAPON_PROCS (0x00800000), and the own mask is d2 b10 | b12 only (no d1 b4). It rolls '
              'no proc of the shaman\'s and no enchant / item proc (S3a code review M1a). Physical, melee range, SpellLevel 40.',
        raw_overrides=_raw(
            'Instantly attacks with ' + ('your off-hand weapon.' if off_hand else 'your main-hand weapon.'), '', 40,
            AttributesEx=512 if not off_hand else 0,
            AttributesEx3=(0x1040000 if off_hand else 0x40400) | ATTR3_SUPPRESS_CASTER_PROCS,
            AttributesEx4=0x1 | ATTR4_SUPPRESS_WEAPON_PROCS,
            DefenseType=2, EffectBonusMultiplier_1=1.0, FacingCasterFlags=1,
            RangeIndex=2, SpellClassMask_3=SS_STRIKES_D2,
            **({} if off_hand else {'SpellVisualID_1': SV_STORMSTRIKE}),
        ),
    )


stormstrike_cleave_main_hand_202413 = _cleave_strike(202413, off_hand=False)
stormstrike_cleave_off_hand_202415 = _cleave_strike(202415, off_hand=True)


# =====================================================================================================================
# Ascendance: the singles, Elemental Ascendance and Earthen Ascendance (202387-202390, 202393, 202414)
# =====================================================================================================================
_ASC_NOTE_COMMON = ('No transform (removed 2026-10-22, playtest P2: the elemental forms were dropped for a one-shot cosmetic burst at the '
                    'shaman\'s feet, 202416-202419, cast by Shaman::CastAscendanceVisual). '
                    'Amounts are the base values; Shaman::RefreshAscendance sets the live Mastery amounts (capstone always on). ')

fire_ascendance_202387 = _buff(
    202387, 'Fire Ascendance',
    [_mod(SpellModOp.DAMAGE, True, 29), _mod(SpellModOp.DOT, True, 29)],
    ICON_FIRE_ELEMENTAL, -1,
    'Your Flame Shock deals more damage.',
    'Your Flame Shock deals 30% more damage.',
    'Fire Ascendance (single): E0 SPELLMOD_DAMAGE pct +30 % (stored 29) and E1 SPELLMOD_DOT pct +30 % on Flame Shock (d0 b28; '
    'L-9: the tick is DOT; Spirit Flame Shock carries no d0 b28). ' + _ASC_NOTE_COMMON + 'State indicator: '
    'non-passive, visible, no consolidation flag, ATTR0 0x80000000, infinite (held until Elemental Ascendance consumes it; 2 min '
    'out of combat is ASC_OOC_MS), dropped on death and logout (D9).',
    school=School.FIRE, level=40, no_cancel=True,
    **_emask(1, FLAME_SHOCK), **_emask(2, FLAME_SHOCK),
)
frost_ascendance_202388 = _buff(
    202388, 'Frost Ascendance',
    [_mod(SpellModOp.DAMAGE, True, 29)],
    ICON_FROST, -1,
    'Your Stormstrike deals more damage and strikes an additional nearby enemy.',
    'Your Stormstrike deals 30% more damage and strikes 1 additional nearby enemy.',
    'Frost Ascendance (single): E0 SPELLMOD_DAMAGE pct +30 % (stored 29) on the Stormstrike strikes 32175 / 32176 (d2 b10 / b12). '
    'The extra cleave hit is spell_sha_enh_stormstrike\'s. ' + _ASC_NOTE_COMMON + 'State indicator: non-passive, visible, '
    'no consolidation flag, ATTR0 0x80000000, infinite.',
    school=School.FROST, level=40, no_cancel=True,
    **_emask(1, (0, 0, SS_STRIKES_D2)),
)
wind_ascendance_202389 = _buff(
    202389, 'Wind Ascendance',
    [_aura(AuraType.MOD_SPEED_ALWAYS, 14), _mod(SpellModOp.DAMAGE, True, -1)],
    ICON_WRATH_OF_AIR, -1,
    'Movement speed increased and your melee attacks can unleash a Gust.',
    'Movement speed increased by 15% and your melee attacks have a 15% chance to unleash a Gust.',
    'Wind Ascendance (single): E0 MOD_SPEED_ALWAYS (aura 129, stacks with Ghost Wolf\'s aura 31) +15 % (stored 14, does not scale), E1 SPELLMOD_DAMAGE pct on Gust (d2 b18): '
    'placeholder 0 % (stored -1), the script sets it to Mastery % (Gust x(1 + M)). The Gust roll is the spell_proc row '
    'below (non-triggered melee hits: auto attacks and the Stormstrike / Lava Lash casts, HIT phase; Windfury Attacks, the cleave and '
    'the splash are triggered and never match). ' + _ASC_NOTE_COMMON + 'State indicator: non-passive, visible, no consolidation flag, '
    'ATTR0 0x80000000, infinite.',
    school=School.NATURE, level=40, no_cancel=True,
    **_emask(2, (0, 0, m.GUST)),
)
elemental_ascendance_202390 = _buff(
    202390, 'Elemental Ascendance',
    [_mod(SpellModOp.DAMAGE, True, 59), _mod(SpellModOp.DOT, True, 59), _mod(SpellModOp.DAMAGE, True, 99)],
    ICON_FIRE_ELEMENTAL, 20000,
    'Your Ascendances are combined and empowered.',
    'Your Ascendances are combined and empowered for 20 sec.',
    'Elemental Ascendance (20 s, ASC_DURATION_EA_MS; not no-cancel: the removal script flushes the banked Shamanistic Rage '
    'charges): E0 SPELLMOD_DAMAGE pct +60 % (stored 59 = 1 + 2 x 0.3) on Flame Shock (d0 b28) + the Stormstrike strikes (d2 b10 / b12), '
    'E1 SPELLMOD_DOT pct +60 % on Flame Shock, E2 SPELLMOD_DAMAGE pct +100 % (stored 99, Gust x2) on Gust (d2 b18; the splash carries the '
    'same bit). NO transform. The +30 % speed is the hidden '
    'aura 202414, linked in lockstep (spell_linked_spell type 2; it does not scale with Mastery). The Gust roll is the spell_proc row '
    'below. Shaman::RefreshAscendance adds round(2 x M) to E0 / E1 / E2 (60 + 200 M, 60 + 200 M, 100 + 200 M). Visible, '
    'non-passive, no consolidation flag. The three singles are consumed by Shaman::GrantAscendance.',
    school=School.NATURE, level=40,
    **_emask(1, (FLAME_SHOCK, 0, SS_STRIKES_D2)), **_emask(2, FLAME_SHOCK), **_emask(3, (0, 0, m.GUST)),
)
# Gust rolls under Wind and Elemental Ascendance: auto attacks and non-triggered melee-class casts, HIT phase, any spell type (the
# Stormstrike cast has no damage of its own); the spell_sha_enh_ascendance AuraScript rolls GUST_CHANCE x Proc Chance.
for _gust_carrier in (wind_ascendance_202389, elemental_ascendance_202390):
    procs_on(
        _gust_carrier, proc_flags=PROC_FLAG_DONE_MELEE_AUTO | PROC_FLAG_DONE_SPELL_MELEE, spell_phase_mask=PHASE_HIT, chance=100,
    )
for _ascendance in (fire_ascendance_202387, frost_ascendance_202388, wind_ascendance_202389, elemental_ascendance_202390):
    scripted_by(_ascendance, 'spell_sha_enh_ascendance')

elemental_ascendance_speed_202414 = spell(
    id=202414, name='Elemental Ascendance', school=School.NATURE, attributes=ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[_aura(AuraType.MOD_SPEED_ALWAYS, 29)],
    spell_icon_id=ICON_FIRE_ELEMENTAL,
    notes=NOTE + 'hidden companion of Elemental Ascendance (202390), not passive: E0 MOD_SPEED_ALWAYS (aura 129) +30 % (stored 29; does not scale). '
          'Applied and removed in lockstep with 202390 by spell_linked_spell type 2 (the deviation from the brief: 202390\'s three '
          'effect slots are all Mastery-scaled SpellMods, which Shaman::RefreshAscendance adjusts on the buff itself). Not '
          'death-persistent: it goes with 202390.',
    raw_overrides=_raw('Movement speed increased by 30%.', '', 40, family=False),
)
linked_spell(202390, 202414, type=2, comment='Elemental Ascendance: the hidden +30% speed aura rides with the buff')

earthen_ascendance_202393 = _buff(
    202393, 'Earthen Ascendance', [_dummy()], ICON_EARTH_ELEMENTAL, 10000,
    'Your Stoneskin does not erode and your Earth Shock strikes all nearby enemies.',
    'Your Stoneskin does not erode and your Earth Shock strikes all nearby enemies for 10 sec.',
    'Earthen Ascendance (10 s, EARTHEN_ASC_DURATION_MS; Living Earth capstone): E0 DUMMY (a marker: an aura needs an effect; the '
    'transform was removed 2026-10-22, playtest P2). The effects (no Stoneskin erosion, the Earth Shock copies, no Earth Charge) are '
    'Shaman::IsEarthenAscendant\'s and spell_sha_earth_shock_rockbiter\'s. Visible, non-passive, no consolidation flag; not '
    'no-cancel (cancelling just ends it). Not death-persistent (D9).',
    school=School.NATURE, level=40,
)


# =====================================================================================================================
# Ascend bursts (playtest fix pass P2, 2026-10-22): the one-shot cosmetic at the shaman's feet when an Ascendance is gained
# (202416-202419). Cast by Shaman::CastAscendanceVisual (triggered, self): Fire / Frost / Wind from GrantAscendance, Earth from
# Elemental Ascendance (the third single) and from Earthen Ascendance (Living Earth). Not an aura, so the stock visuals' state kits
# (stun swirl, frost root swirl, Fire Nova state) never play; the cast kit alone does. No damage, no threat, no aggro: the only
# effect is a DUMMY on the caster that nothing binds, AttributesEx3 SUPPRESS_CASTER_PROCS so it rolls nothing, school kept off
# any shaman family (SpellClassSet 0).
# =====================================================================================================================
def _ascend_burst(spell_id: int, name: str, school, visual: int, icon: int, notes: str):
    return spell(
        id=spell_id, name=name, school=school, attributes=0,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon,
        notes=NOTE + notes + ' Cosmetic only (P2): a self-cast DUMMY that nothing binds, SpellVisualID_1 ' + str(visual) +
              ', AttributesEx3 SUPPRESS_CASTER_PROCS, family 0, no aura, no target, no threat; cast by '
              'Shaman::CastAscendanceVisual (triggered, instant).',
        raw_overrides=_raw('', '', 40, family=False, AttributesEx3=ATTR3_SUPPRESS_CASTER_PROCS, SpellVisualID_1=visual),
    )


ascendance_fire_nova_202416 = _ascend_burst(
    202416, 'Ascendance Fire Nova', School.FIRE, SV_ASCEND_FIRE, ICON_FIRE_NOVA,
    'Fire Ascendance gained: the Fire Nova ring (stock SpellVisual 963, the Fire Nova NPC / Blast Wave kit).')
ascendance_frost_nova_202417 = _ascend_burst(
    202417, 'Ascendance Frost Nova', School.FROST, SV_ASCEND_FROST, ICON_FROST,
    'Frost Ascendance gained: the Frost Nova ring (stock SpellVisual 17).')
ascendance_wind_burst_202418 = _ascend_burst(
    202418, 'Ascendance Wind Burst', School.NATURE, SV_ASCEND_WIND, ICON_WIND,
    'Wind Ascendance gained: the Thunderstorm lightning burst (stock SpellVisual 11302).')
ascendance_earth_stomp_202419 = _ascend_burst(
    202419, 'Ascendance Earth Stomp', School.NATURE, SV_ASCEND_EARTH, ICON_EARTH,
    'Elemental Ascendance or Earthen Ascendance gained: the War Stomp ring (stock SpellVisual 5719).')


# =====================================================================================================================
# Living Earth (talent 60296): the castable IS the talent's single rank (SkillLineAbility 30680, CotE precedent)
# =====================================================================================================================
living_earth_202361 = spell(
    id=202361, name='Living Earth', school=School.NATURE, attributes=0, category=0,
    cast_time_ms=0, cooldown_ms=10000, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=3, range_yards=RANGE_SELF,
    duration_ms=10000,
    effects=[Effect(
        type=EffectType.APPLY_AURA, apply_aura=AuraType.SCHOOL_ABSORB, misc_value=SCHOOL_ALL,
        implicit_target_a=TARGET_UNIT_CASTER, sp_potency=40.0, potency_kind='absorb', time_basis_ms=1500,
    )],
    spell_icon_id=ICON_LIVING_EARTH,
    tooltip_vars=shaman_livearth_1219,
    notes=NOTE + 'Living Earth (talent 60296 rank, SLA 30680, learned at 30): instant, GCD 1500 / 133 (core-hasted: magic class, not an '
          'ability), RecoveryTime 10000 (Cooldown Haste does not apply: < 30 s), 3% base mana, CasterAuraSpell 8017 ("Requires '
          'Rockbiter"; the server refuses with SPELL_FAILED_CASTER_AURASTATE). E0 SCHOOL_ABSORB every school, 40 potency absorb on the '
          'healing scale (T 1500, about 424 at 60 [tune]), 10 s; E0 is the effect Guardian Totems\' SPELLMOD_EFFECT1 (+10 / 20 %, '
          'effect 3 of 16258 / 16293) reaches through d2 b16 (LIVING_EARTH). Not dispellable. The Stoneskin and the Earthen Ascendance '
          'are spell_sha_enh_living_earth\'s (AfterCast). Never d1 b5 / b10 or d0 b10 (the elemental-shield readers). Visual: '
          'Stoneform\'s kit 5787 as the placeholder (V stage). Aura text number-free.',
    raw_overrides=_raw(
        'Requires Rockbiter. Encases you in living stone, absorbing {pot1*gt} damage and granting 10 Stoneskin. If you know '
        'Ascendance and have at least 30 Earth Charge, Living Earth also consumes 30 Earth Charge to grant Earthen Ascendance '
        'for 10 sec: your Stoneskin does not erode and your Earth Shock strikes all nearby enemies. 10 sec cooldown.',
        'A shell of living stone absorbs damage.', 30,
        BaseLevel=30, DefenseType=1, PreventionType=1, StartRecoveryCategory=133, StartRecoveryTime=1500,
        CasterAuraSpell=SPELL_ROCKBITER, SpellClassMask_3=m.LIVING_EARTH, SpellVisualID_1=SV_STONEFORM,
    ),
)
scripted_by(living_earth_202361, 'spell_sha_enh_living_earth')
skill_line_ability(id=30680, skill_line=SKILL_LINE_ENHANCEMENT, spell_id=living_earth_202361.id,
                   class_mask=CLASS_MASK_SHAMAN, acquire_method=0)


# =====================================================================================================================
# Frozen Power capstone: the Blizzard (202404) and its tick (202405), after Earthquake's shape
# =====================================================================================================================
frozen_blizzard_tick_202405 = spell(
    id=202405, name='Blizzard', school=School.FROST, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=30.0, potency_kind='direct', time_basis_ms=1000,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=ICON_BLIZZARD,
    notes=NOTE + 'the Frozen Power Blizzard tick (shared doc "Frozen Power": 30 potency Frost damage every 1 sec to every enemy inside, '
          'no cap, no split): per-target direct SCHOOL_DAMAGE cast by spell_sha_enh_frozen_blizzard once a second at each enemy inside '
          'the area (Earthquake\'s tick shape: single-target casts, so no AoE reduction or 10-target split), sp_potency 30 direct, T 1000 '
          '(about 53 at 60), SpellLevel 35 (Frozen Power\'s row). Family d2 b29 ENH_SPELL_HIT (Improved Stormstrike\'s aura 271 reaches '
          'it). AttributesEx3 SUPPRESS_CASTER_PROCS (the ticks roll nothing), AttributesEx2 IGNORE_LOS (the script filters LoS from the '
          'zone, as the Earthquake tick), range 50000 (L6). DmgClass magic.',
    raw_overrides=_raw(
        'Deals {pot1} Frost damage.', '', 35, DefenseType=1, PreventionType=1,
        AttributesEx2=ATTR2_IGNORE_LOS, AttributesEx3=ATTR3_SUPPRESS_CASTER_PROCS,
        SpellClassMask_3=m.ENH_SPELL_HIT, SpellVisualID_1=SV_BLIZZARD_TICK,
    ),
)

frozen_blizzard_202404 = spell(
    id=202404, name='Blizzard', school=School.FROST, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0, duration_ms=8000,
    effects=[
        Effect(type=EffectType.PERSISTENT_AREA_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_DEST_DYNOBJ_ENEMY,
               radius_yards=8.0),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=1000,
               implicit_target_a=TARGET_UNIT_CASTER),
    ],
    spell_icon_id=ICON_BLIZZARD,
    notes=NOTE + 'the Frozen Power Blizzard ground zone (Earthquake 202280\'s shape): triggered by spell_sha_enh_frozen_power on an '
          'Elemental Blast hit under Frostbrand, cast at a POSITION (the struck target\'s, like Earthquake: eff0 A 28 DEST_DYNOBJ_ENEMY '
          'takes the explicit destination; a unit-target cast would centre on the caster), 8 s (FP_BLIZZARD_DURATION_MS), radius 8 yd '
          '(FP_BLIZZARD_RADIUS_YD, eff0). eff1 PERIODIC_DUMMY 1000 ms on the caster: 8 ticks, NOT hasted (no AttributesEx5 0x2000 / '
          '0x200); spell_sha_enh_frozen_blizzard (AuraScript, periodic dummy on EFFECT_1) casts 202405 at every attackable enemy '
          'inside the dynobj with LoS. AttributesEx5 0x08000000 hides the caster aura, raw Targets 0x40 (ground), SpellVisualID 9490 = '
          'the mage Blizzard ground kit. No family bits, no potency (the tick carries it). Triggered: no GCD, no cost, no cooldown.',
    raw_overrides=_raw(
        'Calls down a Blizzard on the target area for $d.', 'Caught in a Blizzard.', 35, family=False, DefenseType=1,
        PreventionType=1, Targets=0x40, AttributesEx5=ATTR5_NO_CASTER_AURA_ICON, SpellVisualID_1=SV_BLIZZARD_AREA,
    ),
)
scripted_by(frozen_blizzard_202404, 'spell_sha_enh_frozen_blizzard')


# =====================================================================================================================
# Buffs and helpers 202394-202412
# =====================================================================================================================
def _taunt(spell_id: int, name: str, duration_ms: int, icon: int, description: str, aura: str, notes: str, area: bool,
           radius: float | None = None):
    """The stock Taunt's shape (355: ATTACK_ME + MOD_TAUNT, Attributes 0x50010, AttributesEx2 0x04000000, AttributesEx4 0x800, magic
    class, silence prevention), either at one target (Earth Shock's) or around the caster (the Rock Spirit's). A taunt-immune target
    (creature_immunities: effect 114 + aura 11) skips both effects silently; range 50000 (L6)."""
    kw = {'implicit_target_a': TARGET_SRC_CASTER, 'implicit_target_b': TARGET_UNIT_SRC_AREA_ENEMY, 'radius_yards': radius} if area \
        else {'implicit_target_a': TARGET_UNIT_TARGET_ENEMY}
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=0x50010,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0,
        duration_ms=duration_ms,
        effects=[
            Effect(type=EFFECT_ATTACK_ME, **kw),
            Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_TAUNT, **kw),
        ],
        spell_icon_id=icon,
        notes=NOTE + notes,
        raw_overrides=_raw(
            description, aura, 1, family=False, DefenseType=1, PreventionType=1, AttributesEx2=0x4000000,
            AttributesEx4=0x800, SpellVisualID_1=SV_TAUNT,
        ),
    )


earth_shock_taunt_202394 = _taunt(
    202394, 'Earth Shock', ES_TAUNT_DURATION_MS['value'], ICON_EARTH_SHOCK,
    'Taunts the target to attack you.', 'Compelled to attack the shaman.',
    'the Earth Shock taunt under Rockbiter (shared doc Q9): ATTACK_ME (114) + MOD_TAUNT (11), 3 s (ES_TAUNT_DURATION_MS [tune]), both '
    'single-target (A 6), the stock Taunt 355\'s shape. Cast by spell_sha_earth_shock_rockbiter at the Earth Shock target (and at every '
    'enemy hit during Earthen Ascendance), player caster with Rockbiter only, never an NPC caster, never a taunt-immune target '
    '(IsImmunedToSpellEffect pre-check; the engine skips an immune target silently), one taunt per target per cast. No family bits.',
    area=False,
)

guardian_totems_armor_202395 = _buff(
    202395, 'Guardian Totems', [_aura(AuraType.MOD_RESISTANCE_PCT, 9, SCHOOL_MASK_PHYSICAL)], ICON_STONESKIN, 10000,
    'Armor increased.', 'Armor increased by 10%.',
    'Guardian Totems capstone buff: aura 101 (MOD_RESISTANCE_PCT) physical +10 % (stored 9), 10 s (GUARDIAN_TOTEMS_ARMOR_DURATION_MS), '
    'refreshes, does not stack with itself. Applied by Shaman::OnPlayerTotemAdded for any shaman totem placement (creator family 11, '
    'elementals included). Visible, non-passive, no consolidation flag. Icon 690 = the Stoneskin Totem buff.',
    level=1,
)

ghost_wolf_sprint_202396 = spell(
    id=202396, name='Improved Ghost Wolf', school=School.NATURE, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=2000,
    effects=[
        _aura(AuraType.MOD_SPEED_ALWAYS, 59),
        Effect(type=EFFECT_DISPEL_MECHANIC, misc_value=MECHANIC_SNARE, implicit_target_a=TARGET_UNIT_CASTER),
        Effect(type=EFFECT_DISPEL_MECHANIC, misc_value=MECHANIC_ROOT, implicit_target_a=TARGET_UNIT_CASTER),
    ],
    spell_icon_id=ICON_GHOST_WOLF,
    notes=NOTE + 'the Improved Ghost Wolf capstone sprint: E0 MOD_SPEED_ALWAYS (aura 129) +60 % (stored 59) for 2 s, E1 DISPEL_MECHANIC snare '
          '(11) and E2 DISPEL_MECHANIC root (7) on the caster ("removes all movement impairing effects"). Cast by '
          'spell_sha_enh_improved_ghost_wolf (AfterEffectApply of the rank 2 passive 16287, player in world and not loading) with the '
          '20 s IGW_SPRINT_ICD_MS gate (AddSpellCooldown(202396)). Visible, non-passive, no consolidation flag. No family bits: never '
          'spell-level d0 b11 (SpellAuras.cpp Ghost Wolf PvP-set hardcode).',
    raw_overrides=_raw('Removes all movement impairing effects and increases your movement speed by 60% for 2 sec.',
                       'Movement speed increased.', 1, family=False, DefenseType=1, PreventionType=1),
)

thundering_strikes_agility_202397 = _buff(
    202397, 'Thundering Strikes', [_aura(AuraType.MOD_STAT, -1, STAT_AGILITY, points_per_level=1.0)], ICON_THUNDERING_STRIKES, 12000,
    'Agility increased.', 'Agility increased by an amount equal to your level.',
    'Thundering Strikes capstone buff: aura 29 (MOD_STAT) Agility, base -1 + 1.0 per level with SpellLevel 0 / BaseLevel 0 = exactly '
    'the caster\'s level (SpellEffectInfo::CalcValue levels off max(BaseLevel, SpellLevel)), 12 s, refreshes (recast), never stacks. '
    'Cast by the rank 3 proc (aura 42 PROC_TRIGGER_SPELL, A2). Visible, non-passive, no consolidation flag.',
    level=0, family=False,
)

volcanic_eruption_buff_202398 = _buff(
    202398, 'Volcanic Eruption', [_mod(SpellModOp.DAMAGE, True, 29)], ICON_LAVA_LASH, 10000,
    'Your next Lava Lash deals more damage.', 'Your next Lava Lash within 10 sec deals 30% more damage.',
    'Volcanic Eruption buff: SPELLMOD_DAMAGE pct +30 % (stored 29) on Lava Lash (d2 b2), ProcCharges 1, 10 s, refreshes, never stacks. '
    'Consumed by the next Lava Lash through the REQ_SPELLMOD spell_proc row below (HIT phase: the charge drops after the damage is '
    'computed). Granted by spell_sha_flametongue_proc with the Lava Lash cooldown reset.',
    school=School.FIRE, charges=1, level=35, **_emask(1, (0, 0, LAVA_LASH_D2)),
)
procs_on(
    volcanic_eruption_buff_202398, proc_flags=PROC_FLAG_DONE_SPELL_MELEE, family_name=SPELLFAMILY_SHAMAN,
    family_mask=(0, 0, LAVA_LASH_D2), spell_type_mask=TYPE_DAMAGE, spell_phase_mask=PHASE_HIT,
    attributes_mask=PROC_ATTR_REQ_SPELLMOD, chance=100, charges=1,
)

mental_quickness_spells_202399 = _buff(
    202399, 'Mental Quickness', [_mod(SpellModOp.DAMAGE, True, MQ_SPELLS_PCT['value'] - 1)], ICON_MENTAL_QUICKNESS, 6000,
    'Spell damage increased.', 'Increases the damage of your shocks, Lightning Bolt, Chain Lightning, Lava Burst and Elemental Blast by 10%.',
    'Mental Quickness capstone, melee ability -> spells: SPELLMOD_DAMAGE pct +10 % (stored 9, MQ_SPELLS_PCT) scoped by the effect-0 '
    'class mask to the direct damaging spells (d0 0x90100003: Lightning Bolt b0, Chain Lightning b1, Earth Shock b20, Flame Shock '
    'b28, Frost Shock b31; d1 b12 Lava Burst; d2 b20 Elemental Blast), SpellClassSet 11. S3a code review m3 (user ruling '
    '2026-10-21): it was aura 79 on every magic school and so also lifted Lava Lash (which grants it), the imbue attacks, orbs, '
    'Bursts, DoT ticks and totem pulses; SPELLMOD_DAMAGE is the direct part only (Flame Shock\'s ticks are SPELLMOD_DOT). 6 s, latest '
    'trigger replaces. Group 1259 rule 1 with 202400 (one active). Visible, non-passive, no consolidation flag. Applied by '
    'spell_sha_enh_mental_quickness after a direct Stormstrike / Lava Lash hit.',
    level=1, **_emask(1, (MQ_SPELLS_D0, MQ_SPELLS_D1, MQ_SPELLS_D2)),
)
mental_quickness_melee_202400 = _buff(
    202400, 'Mental Quickness', [_mod(SpellModOp.DAMAGE, True, 4)], ICON_MENTAL_QUICKNESS, 6000,
    'Melee ability damage increased.', 'Melee ability damage increased by 5%.',
    'Mental Quickness capstone, spells -> melee abilities: SPELLMOD_DAMAGE pct +5 % (stored 4, MQ_MELEE_PCT) on the direct melee '
    'abilities (the Stormstrike strikes d2 b10 / b12 and Lava Lash d2 b2), 6 s. Group 1259 rule 1 with 202399. Visible, '
    'non-passive, no consolidation flag. Applied by spell_sha_enh_mental_quickness after a direct damaging spell hit.',
    level=1, **_emask(1, (0, 0, MQ_MELEE_D2)),
)
spell_group(1259, mental_quickness_spells_202399, mental_quickness_melee_202400)
spell_group_rule(1259, stack_rule=1, description='Mental Quickness buffs: one at a time, the latest replaces')

dual_wield_spec_buff_202401 = _buff(
    202401, 'Dual Wield Specialization', [_aura(AuraType.MOD_DAMAGE_PERCENT_DONE, 1, SCHOOL_MASK_FIRE_FROST_NATURE)],
    ICON_DUAL_WIELD_SPEC, 8000,
    'Fire, Frost and Nature damage increased.', 'Fire, Frost and Nature damage increased by 2%.',
    'Dual Wield Specialization buff: aura 79 Fire | Frost | Nature (mask 28) +2 % (stored 1; the rank passive 30816 / 30818 / 30819 '
    '(aura 231) overrides the amount to 2 / 4 / 6), 8 s, refreshes by recast, no level scaling. Self-targeted (aura 231 triggers at '
    'the actor, so a self effect). Visible, non-passive, no consolidation flag.',
    school=School.NATURE, level=0, family=False,
)

improved_stormstrike_debuff_202402 = spell(
    id=202402, name='Improved Stormstrike', school=School.NATURE, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0, duration_ms=6000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_FROM_CASTER, base_points=4,
                    implicit_target_a=TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=ICON_IMPROVED_STORMSTRIKE,
    notes=NOTE + 'the Improved Stormstrike debuff (D11, S3a-0VERIFY (b)): aura 271 (MOD_DAMAGE_FROM_CASTER), per caster, scoped by the '
          'effect-0 class mask to the shaman\'s own Fire / Frost / Nature damage bits (d0 0x91300403, d1 0x80041000, d2 0x20180004 '
          'with d2 b29 ENH_SPELL_HIT on Flame Burst, Storm Burst and the Blizzard tick; Magma / Searing, the Wind Burst, Gust and '
          'Windfury stay out). Amount 5 / 10 % set by the Stormstrike script from the rank DUMMY (SPELLVALUE_BASE_POINT0; stored 4 = '
          '5 % placeholder), 6 s, refreshes. Visible, non-passive, no consolidation flag. Totem- and wolf-cast damage has another '
          'caster and is not amplified. range 50000 (L6).',
    raw_overrides=_raw(
        'Increases the Fire, Frost and Nature damage the target takes from the shaman.',
        'Fire, Frost and Nature damage taken from the shaman increased.', 45, DefenseType=1, PreventionType=1,
        **_emask(1, (IMP_SS_D0, IMP_SS_D1, IMP_SS_D2)),
    ),
)
improved_stormstrike_mana_202403 = spell(
    id=202403, name='Improved Stormstrike', school=School.NATURE, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    effects=[Effect(
        type=EffectType.ENERGIZE, base_points=0, misc_value=0, implicit_target_a=TARGET_UNIT_CASTER,
        potency_excluded='script-sized: 10 / 20 % of the shaman\'s BASE mana (the rank DUMMY of Improved Stormstrike) is passed as '
                         'SPELLVALUE_BASE_POINT0 by spell_sha_enh_stormstrike.',
    )],
    spell_icon_id=ICON_IMPROVED_STORMSTRIKE,
    notes=NOTE + 'the Improved Stormstrike mana: ENERGIZE mana on the caster, amount script-sized (potency_excluded): the Stormstrike '
          'script passes 10 / 20 % of the base mana (Player::GetCreateMana) as BASE_POINT0 (live - 1: die sides 1). AttributesEx3 '
          'SUPPRESS_CASTER_PROCS (it cannot proc anything). No family bits.',
    raw_overrides=_raw('Restores mana.', '', 45, family=False, AttributesEx3=ATTR3_SUPPRESS_CASTER_PROCS),
)

unleashed_rage_clause_202406 = _buff(
    202406, 'Unleashed Rage', [_aura(AuraType.MOD_DAMAGE_PERCENT_DONE, 2, SCHOOL_MASK_FIRE_FROST_NATURE)], ICON_UNLEASHED_RAGE, -1,
    '', 'Increases your Fire, Frost and Nature damage.',
    'Unleashed Rage damage clause (hidden, not passive): aura 79 Fire | Frost | Nature (mask 28), the amount UR_R1 / R2 / R3 (3 / 6 / '
    '9 %) is set from the Unleashed Rage rank by Shaman::UpdateUnleashedRage, applied while Shamanistic Rage or Elemental '
    'Ascendance is up and removed otherwise (Q12, ruled 2026-10-18). Placeholder stored 2 = 3 %. DO_NOT_DISPLAY, infinite, '
    'dropped on death.',
    school=School.NATURE, hidden=True, level=25, family=False,
)

elemental_spirits_timer_202407 = _buff(
    202407, 'Elemental Spirits', [_dummy()], ICON_SPIRIT_WOLF, 20000,
    'Elemental Spirits fight at your side.', 'The Elemental Spirits fight at your side for 20 sec.',
    'Elemental Spirits timer (Q24, "a timer buff on the shaman"): DUMMY holder, 20 s (WOLF_DURATION_MS), ATTR0 0x80000000 (no right-click '
    'cancel, L-13), visible, non-passive, no consolidation flag. Applied by spell_sha_enh_elemental_spirits with the three wolves; '
    'not death-persistent. No family bits.',
    school=School.NATURE, level=60, no_cancel=True, family=False,
)

spirit_flame_shock_202408 = spell(
    id=202408, name='Spirit Flame Shock', school=School.FIRE, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0, duration_ms=18000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, amplitude=3000, sp_potency=25.0,
                    potency_kind='periodic', time_basis_ms=3000, implicit_target_a=TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=ICON_FIRE,
    notes=NOTE + 'the Fire Spirit\'s bite (shared doc "Elemental Spirit wolves"): PERIODIC_DAMAGE Fire, 25 potency per 3 s tick (T 3000), '
          '18 s = 6 ticks (WOLF_FS_POTENCY [tune]), SpellLevel 60 (Elemental Spirits\' row). SpellClassSet 0 and NO d0 b28: Lava Burst '
          'never reads it as Flame Shock (Unit.cpp Lava Burst auto-crit) and no shaman SpellMod or Elemental Weapons spread reaches it; '
          'it stacks with the shaman\'s own Flame Shock (own spell id) and refreshes its own copy. The wolf casts it on every bite; '
          'spell_sha_enh_spirit_flame_shock fixes the owner\'s Fire / Elemental Ascendance bonus at application (snapshot). Visible '
          'debuff, no consolidation flag. range 50000 (L6).',
    raw_overrides=_raw(
        'Burns the target for {pot1.total} Fire damage over $d.', 'Burning from a Fire Spirit\'s bite.', 60, family=False,
        DefenseType=1, PreventionType=1,
    ),
)
scripted_by(spirit_flame_shock_202408, 'spell_sha_enh_spirit_flame_shock')

frost_spirit_copy_202409 = spell(
    id=202409, name='Frost Spirit Stormstrike', school=School.NORMAL, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0,
    effects=[Effect(
        type=EffectType.SCHOOL_DAMAGE, implicit_target_a=TARGET_UNIT_TARGET_ENEMY,
        potency_excluded='script-sized: FROST_COPY_PCT (50 %) of the shaman\'s landed Stormstrike damage (main hand + off hand) is '
                         'passed as the base points by the Frost Spirit AI (Shaman::OnStormstrikeLanded request).',
    )],
    spell_icon_id=ICON_STORMSTRIKE,
    notes=NOTE + 'the Frost Spirit\'s Stormstrike copy: Physical SCHOOL_DAMAGE, script-sized (potency_excluded), cast by the wolf at the '
          'shaman\'s Stormstrike target. SpellClassSet 0 and no bits: Spirit Weapons, Frost / Elemental Ascendance and Improved '
          'Stormstrike\'s mask must not stack onto the 50 %. The copy applies no Nature debuff. DmgClass melee, SpellLevel 60. range '
          '50000 (L6). Never a proc source (triggered by a guardian; the owner\'s procs never see it).',
    raw_overrides=_raw('Strikes the target for a share of the shaman\'s Stormstrike.', '', 60, family=False, DefenseType=2),
)
# The amount is already the post-armor landed damage: ignore armor so the copy is not mitigated twice (SPELL_ATTR0_CU_IGNORE_ARMOR).
custom_attr(frost_spirit_copy_202409, 0x8000)

rock_spirit_taunt_202410 = _taunt(
    202410, 'Rock Spirit', ROCK_TAUNT_MS['value'], ICON_TAUNT,
    'Taunts nearby enemies to attack the Rock Spirit.', 'Compelled to attack the Rock Spirit.',
    'the Rock Spirit\'s taunt on summon (shared doc "Elemental Spirit wolves"): a SINGLE-target ATTACK_ME + MOD_TAUNT (the stock Taunt\'s '
    'shape, A 6), 3 s (ROCK_TAUNT_MS [tune]). npc_sha_rock_spirit enumerates the enemies within ROCK_TAUNT_RADIUS_YD (10 yd [tune]) and '
    'casts it once per enemy; caster = the wolf, so enemies turn on the Rock Spirit. A taunt-immune enemy skips it silently. '
    'SpellClassSet 0.',
    area=False,
)

rockbiter_ils_threat_202411 = _hidden_child(
    202411, 'Rockbiter Lightning Shield', [_mod(SpellModOp.THREAT, True, 99)], ICON_LIGHTNING_SHIELD, School.NATURE,
    'Your Lightning Shield orbs generate more threat.',
    'hidden child of Rockbiter for Improved Lightning Shield (S3a-WP-BRIEF item 19, NOTES section 2 row 1,3): SPELLMOD_THREAT pct +100 % '
    '(stored 99) on the orb 26364 (d0 b10) and the shield 324; applied by spell_sha_imbue with Rockbiter while Improved Lightning Shield '
    'is known (and on talent learn / reset, Shaman::OnEnhTalentsChanged), removed with Rockbiter. Passive + DO_NOT_DISPLAY, AttributesEx3 '
    '0x100000 + AttributesEx2 0x1 (follows Rockbiter through death, L5). Compounds with Rockbiter\'s own +100 %. No family bits of its own.',
    **_emask(1, 0x400),
)

spirit_guard_parry_202412 = _hidden_child(
    202412, 'Rockbiter Parry', [_aura(AURA_MOD_PARRY_PERCENT, 0)], ICON_SPIRIT_GUARD, School.NORMAL,
    'Your chance to parry is increased.',
    'hidden child of Rockbiter for Spirit Guard (S3a-WP-BRIEF item 13): aura 47 (MOD_PARRY_PERCENT), amount set by CastCustomSpell / '
    'SPELLVALUE_BASE_POINT0 from the rank\'s parry-bonus DUMMY (E1 of 202368-70; stored 0 = 1 % placeholder). Applied by '
    'spell_sha_imbue::HandleApply for Rockbiter when the Spirit Guard rank is above 0, removed in HandleRemove, re-applied on talent '
    'learn / reset. Passive + DO_NOT_DISPLAY with the L5 pair. The talent itself teaches parry with an amount-0 aura 47 (P0 7a, '
    'S3a-0VERIFY (e)); once learned the ability stays until relog. No family bits.',
)


# =====================================================================================================================
# Talent rank spells 202360-202375 (the learn level of row N is 10 + 5N), 202376 helper
# =====================================================================================================================

# ---- Elemental Charge (60295, row 1): the passive proc carrier ------------------------------------------------------------------
_EC_TEXT = (
    'While Flametongue, Frostbrand or Windfury is active, your damaging abilities build Elemental Charge of that element, up to 10. '
    'Stormstrike, Lava Lash and the shock matching your imbue grant 2 charges, other damaging abilities grant 1, and your melee '
    'auto attacks have a 20% chance to grant 1. Switching to a different imbue at 10 charges releases that element\'s Elemental '
    'Burst, dealing ' + pot_text(flame_burst_202384) + ' damage to up to 5 enemies near your target. Switching with fewer than 10 '
    'charges resets them. While Rockbiter is active, your abilities build Earth Charge instead, up to 60.'
)
elemental_charge_202360 = _rank(
    202360, 'Elemental Charge', [_dummy()], ICON_ELEMENTAL_CHARGE, 15, _EC_TEXT,
    'Elemental Charge (talent 60295, learned at 15): hidden passive proc carrier, E0 DUMMY. spell_proc below: melee auto attacks (flags '
    '0x4: no phase needed) and the NON-triggered melee-class (0x10) and hostile magic (0x10000) casts of family 11, HIT phase, '
    'SpellTypeMask 0 (the Stormstrike cast, which does no damage of its own, matches; the SS strikes, Windfury / Flametongue / '
    'Frostbrand Attacks, Gusts, Bursts, wolves and periodic ticks are triggered or periodic and never match). A multi-target cast '
    'raises one event per target: the script dedupes by the cast (GetProcSpell). spell_sha_enh_elemental_charge '
    '(AuraScript) decides the grant from the cast spell (SS, Lava Lash and the matching shock 2, others 1; Earth Shock under '
    'Rockbiter 1), rolls EC_AUTO_CHANCE x Proc Chance on autos, and builds Earth Charge under Rockbiter. Chance 100 in the row.',
)
procs_on(
    elemental_charge_202360, proc_flags=PROC_FLAG_DONE_MELEE_AUTO | PROC_FLAG_DONE_SPELL_MELEE | PROC_FLAG_DONE_MAGIC_NEG,
    family_name=SPELLFAMILY_SHAMAN, spell_phase_mask=PHASE_HIT, chance=100,
    attributes_mask=PROC_ATTR_TRIGGERED_CAN_PROC,   # Fire Nova's eruption 8349 is a triggered cast (the script whitelists it)
)
scripted_by(elemental_charge_202360, 'spell_sha_enh_elemental_charge')

# ---- Volcanic Eruption (60297, row 5): DUMMY chance markers 5 / 10 % ---------------------------------------------------------------
_VE_TEXT = ('While Flametongue is active, your Flametongue Attacks have a {chance}% chance to reset the cooldown of your Lava Lash '
            'and cause your next Lava Lash within 10 sec to deal 30% more damage.')
volcanic_eruption_rank1_202362 = _rank(
    202362, 'Volcanic Eruption', [_dummy(4)], ICON_VOLCANIC_ERUPTION, 35, _VE_TEXT.format(chance=5),
    'Volcanic Eruption rank 1 (talent 60297, learned at 35): marker, E0 DUMMY = the chance, 5 % (stored 4; VE_CHANCE_R1). The roll is '
    'spell_sha_flametongue_proc\'s (per Flametongue Attack, Proc Chance applies, skipped for hits Lava Lash caused).', subtext='Rank 1',
)
volcanic_eruption_rank2_202363 = _rank(
    202363, 'Volcanic Eruption', [_dummy(9)], ICON_VOLCANIC_ERUPTION, 35, _VE_TEXT.format(chance=10),
    'Volcanic Eruption rank 2: marker, E0 DUMMY = 10 % (stored 9; VE_CHANCE_R2).', subtext='Rank 2',
)

# ---- Ascendance (60298, row 6): single-rank marker --------------------------------------------------------------------------------
ascendance_202364 = _rank(
    202364, 'Ascendance', [_dummy()], ICON_ASCENDANCE, 40,
    'Transforming 10 Elemental Charge grants that element\'s Ascendance until you gain Elemental Ascendance. Fire Ascendance: your '
    'Flame Shock deals 30% more damage. Frost Ascendance: your Stormstrike deals 30% more damage and strikes 1 additional nearby '
    'enemy. Wind Ascendance: your movement speed is increased by 15%, and your melee attacks have a 15% chance to unleash a Gust, '
    'dealing ' + pot_text(gust_202391) + ' Physical damage to the target and half as much to up to 5 enemies near it. Holding all '
    'three consumes them and grants Elemental Ascendance for 20 sec: Flame Shock and Stormstrike deal 60% more damage, Stormstrike '
    'strikes 2 additional nearby enemies, Gusts deal double damage and your movement speed is increased by 30%. Capstone: Your '
    'Mastery increases the damage bonuses of your Ascendances and the damage reduction of each Stoneskin stack.',
    'Ascendance (talent 60298, learned at 40): marker, E0 DUMMY. The transform and the grants are Shaman::OnImbueChanged / '
    'GrantAscendance; the capstone (live Mastery) is always on with this rank. Tooltips show base values only.',
)

# ---- Molten Fury (60299, row 6): Magma pulse and Fire Nova damage, rank 3 = the ramp capstone -----------------------------------------
_MOLTEN_FURY_CAPSTONE = 'Each pulse of your Magma Totem increases its damage by 10%. Resets when Magma Totem is placed again.'


def _molten_fury(spell_id: int, pct: int, last: bool):
    effects = [_mod(SpellModOp.DAMAGE, True, pct - 1)]
    if last:
        effects.append(_dummy())
    return _rank(
        spell_id, 'Molten Fury', effects, ICON_MOLTEN_FURY, 40,
        _desc(f'Increases the damage of your Magma Totem and Fire Nova by {pct}%.', _MOLTEN_FURY_CAPSTONE, last),
        f'Molten Fury rank {pct // 10} (talent 60299, learned at 40): E0 SPELLMOD_DAMAGE pct +{pct} % (stored {pct - 1}) on the Magma pulse '
        f'8187 (d0 b2 ONLY: d0 b30 is the Searing bolt\'s too) and Fire Nova 8349 (d1 b18 / b31). The pulse is cast by the totem; its '
        f'spell mod owner is the shaman.'
        + (' Rank 3 is the capstone: E1 is the marker (DUMMY); spell_sha_enh_molten_fury (8187, entry gate NPC_MAGMA_TOTEM) adds '
           'MOLTEN_FURY_RAMP_PCT per pulse already fired.' if last else ''),
        subtext=f'Rank {pct // 10}', **_emask(1, (m.MAGMA_PULSE_B2, FIRE_NOVA_DAMAGE, 0)),
    )


molten_fury_rank1_202365 = _molten_fury(202365, 10, False)
molten_fury_rank2_202366 = _molten_fury(202366, 20, False)
molten_fury_rank3_202367 = _molten_fury(202367, 30, True)

# ---- Spirit Guard (60300, row 7): teaches parry, Rockbiter parry bonus and Stoneskin per parry -----------------------------------------
_SPIRIT_GUARD_BONUS = (1, 2, 3)
_SPIRIT_GUARD_STONESKIN = (3, 6, 10)


def _spirit_guard(spell_id: int, rank: int):
    bonus, stoneskin = _SPIRIT_GUARD_BONUS[rank - 1], _SPIRIT_GUARD_STONESKIN[rank - 1]
    return _rank(
        spell_id, 'Spirit Guard',
        [_aura(AURA_MOD_PARRY_PERCENT, -1), _dummy(bonus - 1), _dummy(stoneskin - 1)], ICON_SPIRIT_GUARD, 45,
        f'Teaches you to parry. While Rockbiter is active, increases your chance to parry by {bonus}%, and parrying an attack grants '
        f'you {stoneskin} Stoneskin.',
        f'Spirit Guard rank {rank} (talent 60300, learned at 45): E0 MOD_PARRY_PERCENT amount 0 (stored -1: the handler enables the '
        f'parry skill, S3a-0VERIFY (e); the 5 % engine baseline appears once learned and stays until relog), E1 DUMMY = the Rockbiter '
        f'parry bonus {bonus} % (stored {bonus - 1}; the hidden child 202412 carries it), E2 DUMMY = Stoneskin per parry {stoneskin} '
        f'(stored {stoneskin - 1}; SPIRIT_GUARD_STONESKIN_R{rank}). spell_proc -202368 (taken parry) + spell_sha_enh_spirit_guard.',
        subtext=f'Rank {rank}',
    )


spirit_guard_rank1_202368 = _spirit_guard(202368, 1)
spirit_guard_rank2_202369 = _spirit_guard(202369, 2)
spirit_guard_rank3_202370 = _spirit_guard(202370, 3)
# Parrying an attack: taken melee auto attacks and taken melee-class spells, HitMask PARRY. Negative key = the Talent.dbc chain.
procs_on(
    -202368, proc_flags=PROC_FLAG_TAKEN_MELEE_AUTO | PROC_FLAG_TAKEN_SPELL_MELEE, hit_mask=PROC_HIT_PARRY, chance=100,
)
scripted_by(-202368, 'spell_sha_enh_spirit_guard')

# ---- Shamanistic Focus ranks 2 / 3 (talent 617, row 2; rank 1 is 43338 = A2's): the same three effects in A2's order -----------------
_SF_CAPSTONE = 'Reduces the cooldown of your Shock spells by 1 sec.'


def _shamanistic_focus(spell_id: int, rank: int, crit: int, damage: int):
    last = rank == 3
    return _rank(
        spell_id, 'Shamanistic Focus',
        [_mod(SpellModOp.CRITICAL_CHANCE, False, crit - 1), _mod(SpellModOp.DAMAGE, True, damage - 1),
         _mod(SpellModOp.DOT, True, damage - 1)],
        ICON_SHAMANISTIC_FOCUS, 20,
        _desc(f'Increases the critical strike chance of your Shock spells by {crit}% and their damage by {damage}%.',
              _SF_CAPSTONE, last),
        f'Shamanistic Focus rank {rank} (talent 617, learned at 20): the effect order of A2\'s rank 1 (43338): E0 SPELLMOD_CRITICAL_CHANCE flat '
        f'+{crit} (stored {crit - 1}) on the shocks (d0 b20 / b28 / b31), E1 SPELLMOD_DAMAGE pct +{damage} % (stored {damage - 1}) on the shocks '
        f'(talent_mult effect 2, entry 1212), E2 SPELLMOD_DOT pct +{damage} % on the Flame Shock periodic (d0 b28, L-9). The stock mana '
        f'clause is gone.'
        + (' The capstone (-1 s shock cooldown) cannot be a fourth effect: it is the hidden helper 202376, linked to this rank by '
           'spell_linked_spell type 2.' if last else ''),
        subtext=f'Rank {rank}', **_emask(1, SHOCKS), **_emask(2, SHOCKS), **_emask(3, FLAME_SHOCK),
    )


shamanistic_focus_rank2_202371 = _shamanistic_focus(202371, 2, 4, 8)
shamanistic_focus_rank3_202372 = _shamanistic_focus(202372, 3, 6, 12)

shamanistic_focus_capstone_202376 = spell(
    id=202376, name='Shamanistic Focus', school=School.NORMAL, attributes=ATTR0_PASSIVE_HIDDEN,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[_aura(AuraType.ADD_FLAT_MODIFIER, -1001, int(SpellModOp.COOLDOWN))],
    spell_icon_id=ICON_SHAMANISTIC_FOCUS,
    notes=NOTE + 'Shamanistic Focus capstone helper (A3 addition to the brief\'s id map: rank 3 needs four effects): hidden passive, E0 '
          'SPELLMOD_COOLDOWN flat -1000 ms (stored -1001) on the three shocks (d0 b20 / b28 / b31; the shocks carry their own 6 s '
          'RecoveryTime, < 30 s so no Cooldown Haste). Applied and removed in lockstep with rank 3 (202372) by spell_linked_spell type 2, so '
          'it follows learn, reset, spec swap and login. Stacks with Elemental\'s Reverberation (each shock at 3.5 sec on a hybrid).',
    raw_overrides=_raw('Reduces the cooldown of your Shock spells by 1 sec.', '', 20, **_emask(1, SHOCKS)),
)
linked_spell(202372, 202376, type=2, comment='Shamanistic Focus rank 3: the capstone cooldown cut rides with the rank passive')

# ---- Spirit Weapons ranks 2 / 3 (talent 616, row 5; rank 1 is 16268 = A2's) ----------------------------------------------------------
spirit_weapons_rank2_202373 = _rank(
    202373, 'Spirit Weapons', [_mod(SpellModOp.DAMAGE, True, 9)], ICON_SPIRIT_WEAPONS, 35,
    'Increases the damage of your Stormstrike and Windfury Attacks by 10%.',
    'Spirit Weapons rank 2 (talent 616, learned at 35): E0 SPELLMOD_DAMAGE pct +10 % (stored 9) on the Stormstrike strikes (d2 b10 / '
    'b12) and the Windfury Attacks (d0 b23), as A2\'s rank 1 (talent_mult effect 1, entry 1218). No LEARN_SPELL effects: the stock Parry '
    'grant (18848) and threat clause (36591) are gone (C5).', subtext='Rank 2', **_emask(1, (m.WINDFURY_ATTACK, 0, SS_STRIKES_D2)),
)
spirit_weapons_rank3_202374 = _rank(
    202374, 'Spirit Weapons', [_mod(SpellModOp.DAMAGE, True, 14)], ICON_SPIRIT_WEAPONS, 35,
    'Increases the damage of your Stormstrike and Windfury Attacks by 15%.',
    'Spirit Weapons rank 3: E0 SPELLMOD_DAMAGE pct +15 % (stored 14), same masks as rank 2.', subtext='Rank 3',
    **_emask(1, (m.WINDFURY_ATTACK, 0, SS_STRIKES_D2)),
)

# ---- Frozen Power rank 3 (talent 2263, row 5; ranks 1 / 2 are 63373 / 63374 = A2's): the freeze chance and the capstone ----------------
frozen_power_rank3_202375 = _rank(
    202375, 'Frozen Power', [_dummy(99)], ICON_FROZEN_POWER, 35,
    _desc('Your Frost Shock has a 100% chance to freeze the target in place for 3 sec.',
          'While Frostbrand is active, your Elemental Blast also creates a Blizzard at the target\'s location for 8 sec, dealing '
          + pot_text(frozen_blizzard_tick_202405) + ' Frost damage every 1 sec to all enemies inside it.', True),
    'Frozen Power rank 3 (talent 2263, learned at 35): E0 DUMMY = the freeze chance 100 % (stored 99; the same effect 1 as ranks 1 / 2, read '
    'by spell_sha_enh_frozen_power, L-8). Joins the -63373 spell_proc / script chain through Talent.dbc. The capstone is rank-based: '
    'Elemental Blast hit under Frostbrand casts the Blizzard 202404.', subtext='Rank 3',
)


# =====================================================================================================================
# The four Elemental Spirit wolves (300262-300265): the stock Spirit Wolf 29264's template (S3a-0VERIFY (g))
# =====================================================================================================================
def _wolf(entry: int, name: str, script: str):
    """The stock Feral Spirit wolf's columns (type beast, unit_class 1, exp 2, scale-1 template modifiers, attack time 1500, run speed
    2.14286, detection 18, flags2 2048, movementId 191, no creature_template_spell: the wolves do not get Spirit Hunt / Walk, D2). The
    level is set from the owner at summon; the 29264 setup (weapon damage 1.5L-2.5L, avoidance 32233, scaling 61017 / 35674-76, the Orc
    racial) that Pet.cpp:1310 only gives entry 29264 is replicated by the PetScript::OnInitStatsForLevel hook (B4)."""
    row = creature_template(
        entry, name, subname='', minlevel=1, maxlevel=80, exp=2, faction=14, speed_walk=2.0, speed_run=2.14286, speed_swim=1.0,
        speed_flight=1.0, detection_range=18.0, unit_class=1, unit_flags=0, unit_flags2=2048, type=1, DamageModifier=1.0,
        BaseAttackTime=1500, RangeAttackTime=2000, HealthModifier=1.0, ManaModifier=1.0, ArmorModifier=1.0,
        ExperienceModifier=1.0, RegenHealth=1, movementId=191, HoverHeight=1.0, flags_extra=0, ScriptName=script,
    )
    creature_model(entry, display_id=DISPLAY_SPIRIT_WOLF)
    return row


fire_spirit_300262 = _wolf(300262, 'Fire Spirit', 'npc_sha_fire_spirit')
frost_spirit_300263 = _wolf(300263, 'Frost Spirit', 'npc_sha_frost_spirit')
wind_spirit_300264 = _wolf(300264, 'Wind Spirit', 'npc_sha_wind_spirit')
rock_spirit_300265 = _wolf(300265, 'Rock Spirit', 'npc_sha_rock_spirit')


# --- Script bindings on stock / other-file ids (orchestrator, S3a integration; the brief's class table) -------------------
# Rank-chain keys (-N) resolve through Talent.dbc; 324 / 8042 / 17364 / 30823 / 51533 / 8187 / 202206 are plain ids.
scripted_by(-51528, 'spell_sha_enh_maelstrom_weapon')
scripted_by(16287, 'spell_sha_enh_improved_ghost_wolf')
scripted_by(29080, 'spell_sha_enh_elemental_weapons')
scripted_by(30814, 'spell_sha_enh_mental_quickness')
scripted_by(16303, 'spell_sha_enh_thundering_strikes')   # S3a code review m1: the capstone roll once per cast
scripted_by(17364, 'spell_sha_enh_stormstrike')
scripted_by(30823, 'spell_sha_enh_shamanistic_rage')
scripted_by(51533, 'spell_sha_enh_elemental_spirits')
scripted_by(8187, 'spell_sha_enh_molten_fury')
scripted_by(8042, 'spell_sha_earth_shock_rockbiter')
scripted_by(202206, 'spell_sha_stoneskin')
scripted_by(324, 'spell_sha_enh_lightning_shield')
