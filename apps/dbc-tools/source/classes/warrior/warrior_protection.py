"""
Warrior - S1 Protection delta, data half owned by agent A2: the new Protection spells 204770 (Empowered Revenge),
204774 (Improved Bloodrage buff) and 204775 (Bloodstorm tick), the stock override of Sword and Board's buff 50227, and
every S1 `scripted_by` / `unbind_script` / `remove_spell_proc` on a stock or legacy id (so the big rank files only carry
row edits; S1 handoff D32).

Source of truth: docs/reworks/warrior-protection-rework.md (tooltips and aura texts verbatim),
.agents/plans/warrior-rework/warrior-rework.S1-HANDOFF.md (D7, D12, D13, D15, D19, D31, D32),
warrior-rework.S1-WP-BRIEF.md (frozen ids, variable names, bindings; the brief wins over the handoff) and
warrior-rework.S1-0VERIFY.md (items 2, 6-9).

Ids 204771-204773 stay unused (brief ruling 2: Firm Grip is ungated on the rank instead of getting helper passives).
Bindings use raw ids, never imports of variables from the sibling files, so this file has no import cycle with the
rank files A1 and A3 are editing.
"""

from lib.dsl import AuraType, Effect, EffectType, RANGE_SELF, School, SpellModOp
from lib.dsl.registry import custom_attr, remove_spell_proc, scripted_by, spell, spell_group, unbind_script


# ---- Spell.dbc flag values (src/server/shared/SharedDefines.h, decoded) ----
_ATTR0_DO_NOT_DISPLAY = 0x80                # SPELL_ATTR0_DO_NOT_DISPLAY: not in the spellbook, aura bar or combat log
_ATTR2_CANT_CRIT = 0x20000000               # SPELL_ATTR2_CANT_CRIT
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x4           # SPELL_ATTR2_IGNORE_LINE_OF_SIGHT (a tick must not die behind a corner)
_ATTR3_SUPPRESS_CASTER_PROCS = 0x10000      # SPELL_ATTR3_SUPPRESS_CASTER_PROCS: the tick raises no caster procs
_ATTR3_ALWAYS_HIT = 0x40000                 # SPELL_ATTR3_ALWAYS_HIT: never missed, dodged, parried or blocked
_ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000   # SPELL_ATTR3_IGNORE_CASTER_MODIFIERS: caster done-mods not applied
# Server-only custom attribute (SpellInfo.h SPELL_ATTR0_CU_IGNORE_ARMOR). Unit.cpp checks armor before the bleed
# exemption, so without it every Bloodstorm tick (a share of a hit that already went through armor) would lose armor a
# second time. Not 0x200000 (ignore damage taken mods): the target's taken-mods (Colossus Smash, Blood Frenzy, Mangle)
# must still raise each tick (doc "Bloodstorm").
_CU_IGNORE_ARMOR = 0x8000

# ---- Auras / effects / targets / misc values ----
_SPELLFAMILY_WARRIOR = 4
_TARGET_UNIT_CASTER = 1
_TARGET_UNIT_TARGET_ENEMY = 6
_MECHANIC_BLEED = 15
_SCHOOLS_ALL = 127                          # aura 87 misc 127: every school
_SHAPESHIFT_DEFENSIVE_STANCE = 1 << 17      # ShapeshiftMask: 1 << (FORM_DEFENSIVESTANCE 18 - 1) = 131072
_SCRIPT_CAST_RANGE = 50000.0                # a script-cast payload at an enemy: a real range (a triggered cast is
                                            # range-checked; the Bloodstorm tick fires at any distance the holder lives)

# ---- Stock icons (S1 D34: nothing new minted) ----
_ICON_REVENGE = 562                         # Revenge 6572
_ICON_BLOODRAGE = 86                        # Bloodrage 2687
_ICON_BLOODSTORM = 2774                     # Bloodstorm holder 200030

# ---- Revenge / Shield Slam family bits (SpellClassSet 4; FAMILY-BITS section 2) ----
_REVENGE_D0 = 0x400                         # d0 b10: Revenge and its stock ranks only
_SHIELD_SLAM_D1 = 0x200                     # d1 b9: Shield Slam and its stock ranks only


# =====================================================================================================================
# 204770 Empowered Revenge (D15; doc "Empowered Revenge")
# =====================================================================================================================
# Visible buff, 20 s (idx 18), ONE charge (ProcCharges 1: the next Revenge cast consumes it, the same shape as
# Devastate: Extra Target 200045). eff0 = ADD_PCT_MODIFIER (108) op DAMAGE (0) +30 (stored 29, die 1) on Revenge's own
# bit, EffectSpellClassMaskA_1 = effect 0 / dword 0 = 0x400. The 2% Storm's Bulwark shield is granted by the dispatcher's
# Revenge branch while this buff is up (before the charge is spent at cast); Unrelenting's Devastate script applies it.
# Not self-cast by a target: TARGET_UNIT_CASTER. No button glow (3.3.5 has no overlay).
empowered_revenge_204770 = spell(
    id=204770,
    name='Empowered Revenge',
    school=School.NORMAL,
    attributes=0,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.ADD_PCT_MODIFIER, base_points=29,
               misc_value=int(SpellModOp.DAMAGE), implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_REVENGE,
    notes='warrior-rework S1 A2 (D15, doc "Empowered Revenge"): visible 20 s buff (DurationIndex 18), one charge '
          '(ProcCharges 1, consumed by the next Revenge cast like Devastate: Extra Target 200045), eff0 ADD_PCT_MODIFIER '
          'DAMAGE +30 (bp 29 + die 1) with EffectSpellClassMaskA_1 = effect 0 / d0 = 0x400 (Revenge only). Applied by '
          'Unrelenting (Devastate script); the dispatcher grants the 2% Storm\'s Bulwark shield before the charge is '
          'spent. Attributes 0 (not passive, not hidden), SpellClassSet 4 with no carrier bits.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_WARRIOR, 'EquippedItemClass': -1, 'CastingTimeIndex': 1,
        'ProcChance': 101, 'ProcCharges': 1,
        'EffectSpellClassMaskA_1': _REVENGE_D0,
        'Description_Lang_enUS': "Your next Revenge deals 30% more damage and adds to your Storm's Bulwark shield.",
        'AuraDescription_Lang_enUS': 'Your next Revenge is empowered.',
    },
)


# =====================================================================================================================
# 204774 Improved Bloodrage buff (D19; doc "Improved Bloodrage")
# =====================================================================================================================
# Cast on self by the dispatcher when Bloodrage (2687) is cast in Defensive Stance by a warrior holding Improved
# Bloodrage, with the rank amount (-2 / -4) set by the caster (SPELLVALUE_BASE_POINT0), so the stored amount is only a
# rank-1 placeholder (bp -3 = -2, die 1). eff0 = MOD_DAMAGE_PERCENT_TAKEN (87) misc 127 (all schools). 10 s (idx 1) =
# Bloodrage's 29131. ShapeshiftMask 131072 (Defensive Stance): the shapeshift-lost handler removes a self-cast
# non-passive aura whose Stances exclude the new form (Aura::IsRemovedOnShapeLost), so it ends when the warrior leaves
# Defensive Stance. Attributes: NO 0x10000 (SPELL_ATTR0_NOT_SHAPESHIFTED) and AttributesEx2 NO 0x80000
# (ALLOW_WHILE_NOT_SHAPESHIFTED), or the removal would not happen. Hidden (0x80 DO_NOT_DISPLAY): the doc says "Shows a
# buff: no (Bloodrage's own buff shows)".
improved_bloodrage_buff_204774 = spell(
    id=204774,
    name='Improved Bloodrage',
    school=School.NORMAL,
    attributes=_ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=RANGE_SELF,
    duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=-3,
               misc_value=_SCHOOLS_ALL, implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_BLOODRAGE,
    notes='warrior-rework S1 A2 (D19, doc "Improved Bloodrage"): the damage-taken half of the talent. Aura 87 misc 127 '
          '(all schools), amount set by the caster (-2 / -4, SPELLVALUE_BASE_POINT0; stored bp -3 is a rank-1 '
          'placeholder), 10 s (DurationIndex 1, the length of Bloodrage 29131\'s buff), ShapeshiftMask 131072 '
          '(1 << 17, Defensive Stance 71) so leaving the stance removes it, Attributes 0x80 only (hidden, doc: no buff '
          'shown; NO 0x10000 NOT_SHAPESHIFTED, NO AttributesEx2 0x80000 ALLOW_WHILE_NOT_SHAPESHIFTED), self-cast.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_WARRIOR, 'EquippedItemClass': -1, 'CastingTimeIndex': 1,
        'ShapeshiftMask': _SHAPESHIFT_DEFENSIVE_STANCE,
        'Description_Lang_enUS': 'Reduces damage taken while Bloodrage lasts.',
        'AuraDescription_Lang_enUS': 'Damage taken reduced.',
    },
)


# =====================================================================================================================
# 204775 Bloodstorm tick (D7; doc "Bloodstorm")
# =====================================================================================================================
# The hidden damage spell spell_warr_bloodstorm casts at the target every 3 s from the holder 200030 (A1), with
# bp0 = the per-tick amount Warrior::ApplyPercentBleed stored in the target's CustomData (a share of the Thunder Clap
# hit's final damage). Physical SCHOOL_DAMAGE, mechanic 15 (bleed), hidden. Attributes (decoded):
#   Attributes   0x80       DO_NOT_DISPLAY
#   AttributesEx2 0x20000000 CANT_CRIT                (percent-of-damage rule: a tick never crits)
#                 0x00000004 IGNORE_LINE_OF_SIGHT     (S2 fix pass m2: a script-cast tick runs CheckCast's LoS test)
#   AttributesEx3 0x20000000 IGNORE_CASTER_MODIFIERS  (the stored share already carries every caster modifier)
#                 0x00040000 ALWAYS_HIT               (never missed, dodged, parried or blocked)
#                 0x00010000 SUPPRESS_CASTER_PROCS    (raises no caster procs)
#   custom_attr  0x8000     SPELL_ATTR0_CU_IGNORE_ARMOR (see _CU_IGNORE_ARMOR)
# Not hasted (a script-cast tick has no periodic haste) and potency-excluded (percent-of-other-damage, like the Rogue
# Doomblade tick 203830, rogue_assassination.py). No family carrier bits: nothing modifies the tick by mask.
bloodstorm_tick_204775 = spell(
    id=204775,
    name='Bloodstorm',
    school=School.NORMAL,
    mechanic=_MECHANIC_BLEED,
    attributes=_ATTR0_DO_NOT_DISPLAY,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=_SCRIPT_CAST_RANGE,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, mechanic=_MECHANIC_BLEED, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
               potency_excluded='the amount is the stored per-tick share of the Thunder Clap hit that '
                                'spell_warr_bloodstorm passes as bp0 (percent-of-other-damage rule, Prot doc '
                                '"Bloodstorm"); no potency of its own'),
    ],
    spell_icon_id=_ICON_BLOODSTORM,
    notes='warrior-rework S1 A2 (D7, doc "Bloodstorm"; Rogue Doomblade tick 203830 shape): the hidden tick cast by '
          'spell_warr_bloodstorm every 3 s with bp0 = the stored per-tick amount (Warrior::ApplyPercentBleed). Physical '
          'SCHOOL_DAMAGE, mechanic 15 (bleed), Attributes 0x80 DO_NOT_DISPLAY, Ex2 0x20000000 CANT_CRIT, Ex3 '
          '0x20000000 IGNORE_CASTER_MODIFIERS + 0x40000 ALWAYS_HIT + 0x10000 SUPPRESS_CASTER_PROCS, DefenseType 0, '
          'custom_attr 0x8000 (SPELL_ATTR0_CU_IGNORE_ARMOR), range 50000 yd (script cast), potency_excluded. SpellClassSet '
          '4 with no carrier bits.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_WARRIOR, 'EquippedItemClass': -1, 'CastingTimeIndex': 1, 'DefenseType': 0,
        'AttributesEx2': _ATTR2_CANT_CRIT | _ATTR2_IGNORE_LINE_OF_SIGHT,
        'AttributesEx3': _ATTR3_IGNORE_CASTER_MODIFIERS | _ATTR3_ALWAYS_HIT | _ATTR3_SUPPRESS_CASTER_PROCS,
        'Description_Lang_enUS': 'Deals Physical damage to the target.',
    },
)
custom_attr(bloodstorm_tick_204775, _CU_IGNORE_ARMOR)


# =====================================================================================================================
# 50227 Sword and Board buff (stock id, D13) - declared here, taken over from source/spells/npc.csv
# =====================================================================================================================
# The rank spells 46951-46953 cast it on a successful roll (the dispatcher, D13). The row is the legacy npc.csv row
# (Protection Warrior rework phase 2) with three changes:
#   eff1 (index 1, DBC Effect_2): ADD_PCT_MODIFIER DAMAGE +10 (bp 9 + die 1) moves from Revenge's bit (the stock vestigial
#       effect, EffectSpellClassMaskB_1 = effect 1 / d0 = 0x400, bp -1 from a stale raw override that silently beat the
#       typed bp 9) to Shield Slam's bit: EffectSpellClassMaskB_2 = effect 1 / d1 = 0x200 (512).
#   eff0 (index 0): COST -100% on Shield Slam (bp -101, EffectSpellClassMaskA_2 = effect 0 / d1 = 0x200) is kept.
#   Description / aura text rewritten (the stock text mentioned Devastate/Revenge and used $ variables).
# Both effects share ProcCharges 1: one Shield Slam cast spends the charge. Duration 5 s (stock idx 28), SpellClassSet 4,
# AttributesEx6 64 (SPELL_ATTR6_FLOATING_COMBAT_TEXT_ON_CAST, kept from the stock row), stock visual 345.
sword_and_board_buff_50227 = spell(
    id=50227,
    name='Sword and Board',
    school=School.NORMAL,
    attributes=16,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    range_yards=0.0,
    duration_ms=5000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.ADD_PCT_MODIFIER, base_points=-101,
               misc_value=int(SpellModOp.COST), implicit_target_a=_TARGET_UNIT_CASTER),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.ADD_PCT_MODIFIER, base_points=9,
               misc_value=int(SpellModOp.DAMAGE), implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=2780,
    notes='warrior-rework S1 A2 (D13): Sword and Board buff, taken over from the legacy source/spells/npc.csv row. eff0 '
          'COST -100% on Shield Slam kept (EffectSpellClassMaskA_2 = effect 0 / d1 = 0x200). eff1 is now ADD_PCT_MODIFIER '
          'DAMAGE +10 on Shield Slam (EffectSpellClassMaskB_2 = effect 1 / d1 = 0x200 = 512; was bp -1 on Revenge\'s '
          'bit EffectSpellClassMaskB_1 = 0x400 because a stale raw EffectBasePoints_2 = -1 beat the typed bp 9). One '
          'charge (ProcCharges 1) shared by both mods.',
    raw_overrides={
        'AttributesEx6': 64, 'CastingTimeIndex': 1, 'EquippedItemClass': -1,
        'ProcChance': 100, 'ProcCharges': 1, 'ProcTypeMask': 16,
        'RangeIndex': 1, 'SpellClassSet': _SPELLFAMILY_WARRIOR, 'SpellLevel': 1, 'SpellPriority': 50,
        'SpellVisualID_1': 345,
        'EffectSpellClassMaskA_2': _SHIELD_SLAM_D1,     # effect 0, d1: Shield Slam (cost -100%)
        'EffectSpellClassMaskB_2': _SHIELD_SLAM_D1,     # effect 1, d1: Shield Slam (damage +10%)
        'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0,
        'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712172,
        'Description_Lang_enUS': 'Your next Shield Slam costs no rage and deals 10% more damage.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_enUS': 'Shield Slam is free and deals more damage.',
        'AuraDescription_Lang_Mask': 16712190,
    },
)


# =====================================================================================================================
# 50720 Vigilance (stock id, D10 / D24; WP-R finding 9) - declared only for the doc tooltip
# =====================================================================================================================
# The talent rank (talent 148) is the stock spell 50720, which no source file declared, so the talent pane kept the
# client's stock text ("your Taunt cooldown is refreshed"). This is the stock row reproduced field for field (diffed
# against the stock Spell.dbc row by the A2 check, no live spell_dbc row exists): the aura-42 trigger of 50725 on eff0,
# the dead effects 1 and 2 with their stock bp (-4 and -11, the $s3 behind $<threat>), Attributes 327696, Ex 524288,
# Ex5 32, Ex6 67108864, AuraInterruptFlags 4718592, ProcTypeMask 139944, 30 min, 40 yd, 1.5 s GCD category 133. Only
# the Description changes (the doc text with Growl named; $s1 / $<threat> / $d keep the stock variable route so the
# numbers still follow the data). BaseLevel / SpellLevel 40 are the stock values (D10's level 40 needs no change).
# Both AuraScripts (stock spell_warr_vigilance and spell_warr_vigilance_focused_rage, bound below) still match eff0.
vigilance_talent_50720 = spell(
    id=50720,
    name='Vigilance',
    school=School.NORMAL,
    attributes=327696,
    cast_time_ms=0,
    cooldown_ms=0,
    category_cooldown_ms=0,
    mana_cost=0,
    mana_cost_pct=0,
    effects=[
        Effect(type=EffectType.APPLY_AURA, base_points=-4, implicit_target_a=57, apply_aura=42, trigger_spell=50725),
    ],
    spell_icon_id=2834,
    notes='warrior-rework S1 A2 (D10, WP-R finding 9): the stock Vigilance row, declared only to carry the doc tooltip '
          '(Taunt and Growl refresh). Every other column equals the stock Spell.dbc row; BaseLevel / SpellLevel 40 are '
          'stock. Kept $s1 / $<threat> / $d (SpellDescriptionVariableID 87) so the numbers follow the data.',
    raw_overrides={
        'AttributesEx': 524288, 'AttributesEx5': 32, 'AttributesEx6': 67108864, 'AuraInterruptFlags': 4718592,
        'BaseLevel': 40, 'SpellLevel': 40, 'CastingTimeIndex': 1, 'DurationIndex': 30, 'RangeIndex': 4,
        'EquippedItemClass': -1, 'ProcTypeMask': 139944, 'ProcChance': 100,
        'EffectDieSides_2': 1, 'EffectDieSides_3': 1, 'EffectBasePoints_2': -4, 'EffectBasePoints_3': -11,
        'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0, 'EffectChainAmplitude_3': 1.0,
        'SpellVisualID_1': 13118, 'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'PreventionType': 2,
        'SpellDescriptionVariableID': 87,
        'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712188,
        'Description_Lang_enUS': 'Focus your protective gaze on a group or raid target to reduce their damage taken by '
                                 '$s1% and transfer $<threat>% of the threat they cause to you. Each time they are hit '
                                 'by an attack your Taunt and Growl cooldown is refreshed. Lasts $d. This effect can '
                                 'only be on one target at a time.',
        'Description_Lang_Mask': 16712190,
        'AuraDescription_Lang_enUS': 'Damage taken reduced by $s1% and $s3% of all threat transferred to warrior.',
        'AuraDescription_Lang_Mask': 16712190,
    },
)

# The Thunderstruck echo's slow (200065 eff1, aura 138) must not stack with Thunder Clap's slow (WP-R finding 4): join the
# stock melee-attack-speed slow group 1059 (EXCLUSIVE_SAME_EFFECT, the group Thunder Clap and Improved Consecration
# 201372 are in), the same way paladin_prot_spells.py does for 201372.
spell_group(1059, 200065)


# =====================================================================================================================
# S1 script bindings and proc-row removals on stock / legacy ids (D2, D6, D7, D11, D13, D16, D21, D24, D32)
# =====================================================================================================================
# New fork classes (registered in spell_warrior_protection.cpp, AddSC_warrior_protection_spell_scripts).
scripted_by(12809, 'spell_warr_concussion_blow_rework')       # Concussion Blow: potency damage + Concussed on a stun-immune target
scripted_by(50720, 'spell_warr_vigilance_focused_rage')       # Vigilance (Focused Rage capstone), second AuraScript on the stock id
scripted_by(50725, 'spell_warr_vigilance_trigger_growl')      # Vigilance trigger: also clears Growl 6795's cooldown, second script
scripted_by(200030, 'spell_warr_bloodstorm')                  # Bloodstorm holder: casts the tick 204775 each 3 s period
scripted_by(200065, 'spell_warr_thunder_clap_echo')           # Thunderstruck echo: stored-pct shield + Sword and Board roll
scripted_by(200066, 'spell_warr_thunderstruck_echo_holder')   # Echo holder: casts 200065 at the Thunder Clap's spot

# Stock / legacy classes S1 retires from these ids (the stock class stays registered where the id list says so).
unbind_script(12809, 'spell_warr_concussion_blow')            # D2: stock class restored upstream; its EFFECT_2 handler would find no DUMMY
unbind_script(-46951, 'spell_warr_sword_and_board')           # D13: the roll moves to the dispatcher; stock class stays registered
unbind_script(50687, 'spell_warr_incite')                     # D11: Incite moves to WarriorUnitScript::OnSpellDamageTakenFinal; class deleted

# spell_proc rows the rewritten ranks no longer use (their ProcTypeMask / ProcChance are zeroed in A1's file, so no
# default entry is built either).
remove_spell_proc(-29593)                                     # Iron Temper: the Defensive-Stance proc is gone (D16)
remove_spell_proc(-46945)                                     # Safeguard: now a plain SpellMod (D21)
remove_spell_proc(-46951)                                     # Sword and Board: the roll moves to the dispatcher (D13)
