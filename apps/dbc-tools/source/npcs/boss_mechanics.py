"""Boss mechanics registry data (mod-boss-mechanics, stages M1 and M4): Weakened, the resolve spells, the drills'
stand-in auras (Baited, Marked) and the NPCs.

Ids are pinned in .agents/plans/dungeon-mechanics/dungeon-mechanics.STAGE-M1-HANDOFF.md section 3.1 and reserved under
`bossmechanics` in source/ids.yaml (spells 205000-205099, creatures 300400-300419).

  205000        Weakened - the per-mechanic failure debuff. Self-applied by the module (Weakened::AddStack), 7 stacks,
                30 s refreshed on every stack. EFFECT_0 is -10% damage done per stack (AuraEffect::CalculateAmount
                multiplies by the stack count: 1 stack -10%, 7 stacks -70%). BasePoints -11 with DieSides 1: the
                core adds one (SpellEffectInfo::CalcValue), so the value and the tooltip's $s1 are -10 / "10"; the
                first build had -10 and so ran -9% per stack. EFFECT_1 is MOD_THREAT with base 0: the
                module sets the exact threat compensator after every stack change (ThreatPct = 11, 25, 43, 67, 100,
                150, 233), and the AuraScript pins the engine-calculated amount to 0 so no recalculation can leave a
                stale value. NO_IMMUNITIES lets it land through Divine Shield / Ice Block; Dispel none, so it cannot be
                dispelled.
  205001-205007 Mechanic Impact - the resolve damage, one per school (205001 + SpellSchools value: Physical 0, Holy 1,
                Fire 2, Nature 3, Frost 4, Shadow 5, Arcane 6). One SCHOOL_DAMAGE effect, TARGET_SRC_CASTER /
                TARGET_UNIT_SRC_AREA_ENEMY, 100 yd base radius that the module shrinks per cast with
                SPELLVALUE_RADIUS_MOD. The SpellScript spell_boss_mechanics_resolve filters the target list to the
                mechanic's shape and sets each target's damage (OnEffectLaunchTarget SetEffectValue), so the effect has
                no DBC value. The attribute set is the healing sim's (source/npcs/healsim_spells.py documents every bit
                against the core) plus NO_REFLECTION: no active defense, no redirection, no reflection, no threat,
                ignores LoS, cannot crit, triggered hits still fire the victim's procs (NOT_A_PROC), always hits,
                ignores caster modifiers (boss buffs / creature damage rate cannot change the number), cannot be
                resisted. DefenseType 1 makes every school DmgClass MAGIC, which Spell Reflection would bounce onto
                the marker: SPELL_ATTR1_NO_REFLECTION (0x80) is required, ALWAYS_HIT does not stop the reflect roll
                (Object.cpp, the Spell const* SpellHitResult overload). Physical (205001) stays armor-reduced and the
                other schools ignore resistances; damage-taken auras and absorbs apply to all of them.
  205008        Baited (drill) - a generic stand-in for a boss's bait rotation debuff in the `.mech drill fenrus`
                drill: the rider (`.mech test rider=205008`) on every player the Bait hits, baiter included, and the
                aura the Bait rule counts ("fewest stacks baits"). It does not model the real Fenrus debuff (+200%
                damage taken from the leap): one DUMMY aura, no damage-taken, stat or damage effect, 10 stacks, 2 min
                refreshed on every stack. Cast by the marker with the owner as original caster, so the stacks from
                every leap collect on one aura; TARGET_UNIT_TARGET_ANY so a neutral owner (the training dummy, faction
                31) can land it too. Dispel none.
  205009        Marked (drill) - a generic stand-in for an eligibility or order aura in the drills (`.mech drill ras`:
                Chill; `.mech drill soaks`: the ordered soak's stacks). The drill step `marker <stacks>` sets it on a
                member (Player::AddAura, self as caster, then the exact stack count), so drill setup never hands out
                Weakened (orchestrator ruling on STAGE-M4-R-REPORT M-2). Same harmless shape as 205008 (one DUMMY aura,
                10 stacks, 2 min, Dispel none) with its own icon. Its own id, so the fenrus Baited stacks never count
                for ras or soaks within one program slice.
  300400        Mechanic Marker - the telegraph stalker and resolve caster (npc_boss_mechanic_marker).
  300401        Mechanic Test Owner - the hostile owner of `.mech test` (same script).
  205010-205029 Stage M5 descriptor stand-ins (section "M5 stand-ins" below; 205024-205029 reserved, undeclared).
  300402        Mechanics Training Dummy - the stage M4 training dummy (npc_boss_mechanics_dummy, MechanicDummyAI): a
                player engages it and it runs the `.mech drill` program on itself as the boss stand-in (row below).

Marker flags: unit_flags 33554946 = NOT_SELECTABLE | IMMUNE_TO_NPC | NON_ATTACKABLE (no IMMUNE_TO_PC: an attacker with
it cannot hit player-controlled units, so the stalker could not be the caster); flags_extra 66 = CIVILIAN | NO_XP and
deliberately NOT the TRIGGER bit (0x80: a trigger's display is forced invisible for non-GMs). The marker (300400) adds
NO_MOVE_FLAGS_UPDATE (0x200, so 578): without it the core recomputes movement flags when a moving marker stops, drops
the gravity-off flag the module sets (the template has no flight), and the client drops the floor quad. Level 1 here;
the AI copies the owner's level and faction at summon time. Model 11686 is the invisible stalker display; the module
swaps in the marker displays (91000-93999, patch_bossmechanics_markers.py) at runtime.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.registry import creature_model, creature_template, scripted_by, spell

_TARGET_UNIT_CASTER = 1
_TARGET_SRC_CASTER = 22
_TARGET_UNIT_SRC_AREA_ENEMY = 15

_ATTR0_AURA_IS_DEBUFF = 0x04000000
_ATTR0_NO_ACTIVE_DEFENSE = 0x00200000
_ATTR0_NO_IMMUNITIES = 0x20000000
_ATTR1_NO_REDIRECTION = 0x00000008
_ATTR1_NO_REFLECTION = 0x00000080
_ATTR1_NO_THREAT = 0x00000400
_ATTR2_IGNORE_LINE_OF_SIGHT = 0x00000004
_ATTR2_CANT_CRIT = 0x20000000
_ATTR3_NOT_A_PROC = 0x00000200
_ATTR3_ALWAYS_HIT = 0x00040000
_ATTR3_IGNORE_CASTER_MODIFIERS = 0x20000000
_ATTR4_NO_CAST_LOG = 0x00000001

_WEAKENED_ICON = 543  # Curse of Weakness (702), stock
_SCHOOL_ALL = 127

# Aura tooltip: the 3.3.5 client fills $s1 from the DBC (BasePoints + 1, shown without its sign) and never multiplies it
# by the stack count, so the per-stack wording carries the stacking (stock and custom stacking auras word it the same
# way, e.g. paladin_holy_spells.py: "increased by $s1% per stack"). $u is CumulativeAura (7), $d the duration.
_WEAKENED_AURA_TEXT = 'Damage done reduced by $s1% per stack.'
_WEAKENED_TEXT = 'Damage done reduced by $s1% per stack, stacking up to $u times. Lasts $d.'

weakened_205000 = spell(
    id=205000, name='Weakened', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=_ATTR0_AURA_IS_DEBUFF | _ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=-11,
               misc_value=_SCHOOL_ALL, implicit_target_a=_TARGET_UNIT_CASTER,
               potency_excluded='Weakened: a flat -10% damage done per stack, not a damage or heal value'),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_THREAT, base_points=0,
               misc_value=_SCHOOL_ALL, implicit_target_a=_TARGET_UNIT_CASTER,
               potency_excluded='Weakened: threat compensator, set exactly by the module after every stack change'),
    ],
    spell_icon_id=_WEAKENED_ICON,
    notes=(
        'mod-boss-mechanics M1: the failure debuff, applied to the player by itself (caster = target) so one aura '
        'collects stacks from any boss or stalker. CumulativeAura 7, 30 s refreshed per stack, AURA_IS_DEBUFF + '
        'NO_IMMUNITIES, Dispel none. eff0 -10% damage done per stack (all schools; BasePoints -11 + DieSides 1); '
        'eff1 MOD_THREAT base 0, set to ThreatPct(stacks) by Weakened::AddStack (the AuraScript pins the calculated '
        'amount to 0). Stock icon 543.'
    ),
    raw_overrides={
        'SpellClassSet': 0, 'EquippedItemClass': -1, 'CastingTimeIndex': 1, 'SpellLevel': 0, 'CumulativeAura': 7,
        'EffectChainAmplitude_1': 1.0, 'EffectChainAmplitude_2': 1.0,
        'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '',
        'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': _WEAKENED_TEXT,
        'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': _WEAKENED_AURA_TEXT,
    },
)
scripted_by(weakened_205000, 'spell_boss_mechanics_weakened')

# --- Baited (drill) 205008 (stage M4, user ruling 2026-11-04) ------------------------------------------------------
# The baiter doing the job gets no Weakened, so the drill's Bait rotation needs its own stand-in rotation debuff: a
# harmless stacking DUMMY aura the Bait rule counts (no damage-taken modifier; the drill does not model the real one).
# Aura text number-free (custom-spells.md).
_TARGET_UNIT_TARGET_ANY = 25
_BAITED_DRILL_ICON = 538  # Ability_Hunter_SniperShot (Hunter's Mark), stock
_BAITED_DRILL_TEXT = 'Drill stand-in for a bait rotation debuff; baits go to the fewest stacks. Lasts $d.'
_BAITED_DRILL_AURA_TEXT = 'Drill stand-in for a bait rotation debuff; baits go to the fewest stacks.'

baited_drill_205008 = spell(
    id=205008, name='Baited (drill)', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=_ATTR0_AURA_IS_DEBUFF | _ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=120000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
               implicit_target_a=_TARGET_UNIT_TARGET_ANY),
    ],
    spell_icon_id=_BAITED_DRILL_ICON,
    notes=(
        'mod-boss-mechanics M4: the drill stand-in for a bait rotation debuff. `.mech test rider=205008` casts it on '
        'every player a Bait hits (the baiter too) and `aura=205008` makes the fewest-stacks rule count it, so the '
        'pick rotates without Weakened on the baiter. One DUMMY aura, no damage-taken, stat or damage effect; '
        'CumulativeAura 10, 2 min refreshed per stack, AURA_IS_DEBUFF + NO_IMMUNITIES, Dispel none. '
        'TARGET_UNIT_TARGET_ANY: the marker casts it for a hostile or a neutral owner. Stock icon 538.'
    ),
    raw_overrides={
        'SpellClassSet': 0, 'EquippedItemClass': -1, 'CastingTimeIndex': 1, 'SpellLevel': 0, 'CumulativeAura': 10,
        'EffectChainAmplitude_1': 1.0,
        'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '',
        'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': _BAITED_DRILL_TEXT,
        'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': _BAITED_DRILL_AURA_TEXT,
    },
)

# --- Marked (drill) 205009 (stage M4 WP-F, orchestrator ruling on STAGE-M4-R-REPORT M-2) ------------------------------
# Drill setup selectors (ras's runners, the ordered soak) used Weakened stacks; Weakened is only for failures, so the
# drills set this harmless stacking DUMMY aura instead (`marker <stacks>` steps). Separate from Baited 205008: the
# fenrus rider stacks must not count for ras or soaks eligibility. Aura text number-free (custom-spells.md).
_MARKED_DRILL_ICON = 133  # Spell_Frost_WizardMark, stock (205008 uses 538)
_MARKED_DRILL_TEXT = 'Drill stand-in for an eligibility or order aura; the drill reads its stacks. Lasts $d.'
_MARKED_DRILL_AURA_TEXT = 'Drill stand-in for an eligibility or order aura; the drill reads its stacks.'

marked_drill_205009 = spell(
    id=205009, name='Marked (drill)', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=_ATTR0_AURA_IS_DEBUFF | _ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=120000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
               implicit_target_a=_TARGET_UNIT_TARGET_ANY),
    ],
    spell_icon_id=_MARKED_DRILL_ICON,
    notes=(
        'mod-boss-mechanics M4: the drill stand-in for an eligibility or order aura. The drill step `marker <stacks>` '
        'sets it on a member (self as caster, exact stack count) and `aura=` / `self=` / `order=205009` read it, so '
        'drill setup never hands out Weakened. One DUMMY aura, no damage-taken, stat or damage effect; CumulativeAura '
        '10, 2 min, AURA_IS_DEBUFF + NO_IMMUNITIES, Dispel none. Stock icon 133 (205008 has 538).'
    ),
    raw_overrides={
        'SpellClassSet': 0, 'EquippedItemClass': -1, 'CastingTimeIndex': 1, 'SpellLevel': 0, 'CumulativeAura': 10,
        'EffectChainAmplitude_1': 1.0,
        'Name_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '',
        'Description_Lang_Mask': 16712190, 'Description_Lang_enUS': _MARKED_DRILL_TEXT,
        'AuraDescription_Lang_Mask': 16712190, 'AuraDescription_Lang_enUS': _MARKED_DRILL_AURA_TEXT,
    },
)

_SCHOOLS = (
    (0, School.NORMAL, 'Physical'), (1, School.HOLY, 'Holy'), (2, School.FIRE, 'Fire'), (3, School.NATURE, 'Nature'),
    (4, School.FROST, 'Frost'), (5, School.SHADOW, 'Shadow'), (6, School.ARCANE, 'Arcane'),
)

for _offset, _school, _label in _SCHOOLS:
    _impact = spell(
        id=205001 + _offset, name='Mechanic Impact', school=_school, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[
            Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=_TARGET_SRC_CASTER,
                   implicit_target_b=_TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=100.0,
                   potency_excluded='mod-boss-mechanics: the damage is set per target by the resolve SpellScript '
                                    '(OnEffectLaunchTarget SetEffectValue) from the reference-health provider'),
        ],
        notes=(
            f'mod-boss-mechanics M1 resolve spell, {_label}. 100 yd base radius shrunk per cast by RadiusMod; the '
            'script filters the target list to the mechanic shape. Healing-sim attribute set (healsim_spells.py) '
            'plus NO_REFLECTION: no active defense, no redirection, no reflection (DmgClass magic would otherwise '
            'be reflectable; ALWAYS_HIT does not stop it), no threat, ignore LoS, cannot crit, triggered hits still '
            'fire the victim procs (NOT_A_PROC), always hit, ignore caster modifiers, cannot be resisted. '
            'DmgClass magic (1), instant, Speed 0.'
        ),
        raw_overrides={
            'Attributes': _ATTR0_NO_ACTIVE_DEFENSE,
            'AttributesEx': _ATTR1_NO_REDIRECTION | _ATTR1_NO_REFLECTION | _ATTR1_NO_THREAT,  # 0x488
            'AttributesEx2': _ATTR2_IGNORE_LINE_OF_SIGHT | _ATTR2_CANT_CRIT,
            'AttributesEx3': _ATTR3_NOT_A_PROC | _ATTR3_ALWAYS_HIT | _ATTR3_IGNORE_CASTER_MODIFIERS,
            'AttributesEx4': _ATTR4_NO_CAST_LOG,
            'CastingTimeIndex': 1,
            'DefenseType': 1,
            'EquippedItemClass': -1,
            'SpellClassSet': 0,
            'SpellLevel': 0,
        },
    )
    scripted_by(_impact, 'spell_boss_mechanics_resolve')

# --- M5 stand-ins (205010-205023, stage M5 WP-K-data) ---------------------------------------------------------------
# Generic stand-ins the descriptor drills (`.mech drill interrupts|dispels|purges|targets|ignore`) cast on the Drill
# NPCs and the drill members; ids pinned in dungeon-mechanics.STAGE-M5-HANDOFF.md section 3.6. Names and icons borrowed
# from stock spells, tooltips number-free (custom-spells.md). 205024-205029 are RESERVED (summons, prison aura), not
# declared. Damage is a small fixed value (BasePoints 49 + DieSides 1 -> 50): drill filler, not balanced content, so
# it is potency-excluded like the resolve spells; the Magic/Curse/Poison/Disease debuffs only need to be present.
_TARGET_UNIT_SRC_AREA_ALLY = 30
_AURA_DEBUFF = _ATTR0_AURA_IS_DEBUFF
_DISPEL_ENRAGE = 9
_STANDIN_TEXT = {'Description_Lang_Mask': 16712190, 'NameSubtext_Lang_Mask': 16712190, 'NameSubtext_Lang_enUS': '',
                 'Name_Lang_Mask': 16712190, 'AuraDescription_Lang_Mask': 16712190}
_STANDIN_FIXED = 'drill stand-in: small fixed filler damage, not content'


def _standin_raw(desc, aura_desc='', **more):
    return {'SpellClassSet': 0, 'EquippedItemClass': -1, 'CastingTimeIndex': 1, 'SpellLevel': 0,
            'Description_Lang_enUS': desc, 'AuraDescription_Lang_enUS': aura_desc, **_STANDIN_TEXT, **more}


def _standin_cast(spell_id, name, school, cast_ms, icon, desc, note):
    # InterruptFlags 15 (movement | pushback | INTERRUPT | autoattack) is what lets a kick interrupt the cast;
    # PreventionType 1 (silence) is what lets a silence stop it (Holy Light's pair, paladin_spells.py).
    raw = _standin_raw(desc, InterruptFlags=15, PreventionType=1, DefenseType=1)
    raw.pop('CastingTimeIndex')
    return spell(
        id=spell_id, name=name, school=school, cast_time_ms=cast_ms, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=49, implicit_target_a=_TARGET_UNIT_TARGET_ANY,
                        potency_excluded=_STANDIN_FIXED)],
        spell_icon_id=icon, notes=note, raw_overrides=raw,
    )


spell_cast_low_205010 = _standin_cast(
    205010, 'Frost Bolt (drill)', School.FROST, 2000, 188, 'Drill stand-in for a low priority interruptible cast.',
    'M5 drill stand-in: low priority interruptible cast, 2.0 s, Frost damage. InterruptFlags 15, PreventionType silence. '
    'Stock Frostbolt icon 188.')
spell_cast_mid_205011 = _standin_cast(
    205011, 'Shadow Bolt (drill)', School.SHADOW, 2500, 213, 'Drill stand-in for a mid priority interruptible cast.',
    'M5 drill stand-in: mid priority interruptible cast, 2.5 s, Shadow damage. InterruptFlags 15, PreventionType '
    'silence. Stock Shadow Bolt icon 213.')
spell_cast_high_205012 = _standin_cast(
    205012, 'Fireball (drill)', School.FIRE, 3000, 185, 'Drill stand-in for a high priority interruptible cast.',
    'M5 drill stand-in: high priority interruptible cast, 3.0 s, Fire damage. InterruptFlags 15, PreventionType '
    'silence. Stock Fireball icon 185.')
spell_cast_nokick_205013 = _standin_cast(
    205013, 'Ritual (drill)', School.ARCANE, 2500, 2290, 'Drill stand-in for a cast that must not be interrupted.',
    'M5 drill stand-in: the do-not-kick cast, 2.5 s, Arcane damage; interruptible on purpose, the drill counts a kick '
    'as the violation. InterruptFlags 15, PreventionType silence. Stock Fire Elemental Totem icon 2290.')


def _standin_dot(spell_id, name, school, dispel, icon, duration_ms, desc, note):
    return spell(
        id=spell_id, name=name, school=school, dispel=dispel, mechanic=0, attributes=_AURA_DEBUFF, cast_time_ms=0,
        cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=9,
                        amplitude=3000, implicit_target_a=_TARGET_UNIT_TARGET_ANY,
                        potency_excluded=_STANDIN_FIXED)],
        spell_icon_id=icon, notes=note, raw_overrides=_standin_raw(desc + ' Lasts $d.', desc),
    )


spell_dispel_magic_205014 = _standin_dot(
    205014, 'Magic Affliction (drill)', School.SHADOW, 1, 234, 24000, 'Drill stand-in for a dispellable Magic debuff.',
    'M5 drill stand-in: Magic debuff, light periodic Shadow damage every 3 s, 24 s. Stock Shadow Word: Pain icon 234.')
spell_dispel_curse_205015 = _standin_dot(
    205015, 'Curse Affliction (drill)', School.SHADOW, 2, 544, 24000, 'Drill stand-in for a dispellable Curse debuff.',
    'M5 drill stand-in: Curse debuff, light periodic Shadow damage every 3 s, 24 s. Stock Bane of Agony icon 544.')
spell_dispel_poison_205016 = _standin_dot(
    205016, 'Poison Affliction (drill)', School.NATURE, 4, 513, 24000,
    'Drill stand-in for a dispellable Poison debuff.',
    'M5 drill stand-in: Poison debuff, light periodic Nature damage every 3 s, 24 s. Stock Deadly Poison icon 513.')
spell_dispel_disease_205017 = _standin_dot(
    205017, 'Disease Affliction (drill)', School.NATURE, 3, 253, 24000,
    'Drill stand-in for a dispellable Disease debuff.',
    'M5 drill stand-in: Disease debuff, light periodic Nature damage every 3 s, 24 s. Stock Viper Sting icon 253.')

spell_urgent_205018 = spell(
    id=205018, name='Stunning Grip (drill)', school=School.HOLY, dispel=1, mechanic=12, attributes=_AURA_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=7000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, mechanic=12,
                    implicit_target_a=_TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=302,
    notes='M5 drill stand-in: urgent loss of control, Magic, stun mechanic, 7 s. Stock Hammer of Justice icon 302.',
    raw_overrides=_standin_raw('Drill stand-in for an urgent loss of control. Lasts $d.',
                               'Drill stand-in for an urgent loss of control.'),
)

spell_deadline_205019 = spell(
    id=205019, name='Doom Mark (drill)', school=School.SHADOW, dispel=1, mechanic=0, attributes=_AURA_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=8000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=1488,
    notes='M5 drill stand-in: deadline debuff, Magic, 8 s, DUMMY aura. On expiry 205020 must go off: NOT expressible '
          'in the DSL (no on-expire trigger), so C++ (an AuraScript AfterRemove on expire, or a '
          'spell_linked_spell -205019 -> 205020 row) casts it. Stock Psychic Scream icon 1488.',
    raw_overrides=_standin_raw('Drill stand-in for a deadline debuff; it bursts when it expires, unless dispelled in '
                               'time. Lasts $d.', 'Drill stand-in for a deadline debuff; it bursts when it expires.'),
)

spell_deadline_burst_205020 = spell(
    id=205020, name='Doom Burst (drill)', school=School.SHADOW, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=99, implicit_target_a=22,
                    implicit_target_b=_TARGET_UNIT_SRC_AREA_ALLY, radius_yards=10.0,
                    potency_excluded=_STANDIN_FIXED)],
    spell_icon_id=1488,
    notes='M5 drill stand-in: the expiry burst of 205019, Shadow damage to allies of the caster within 10 yd of the '
          'caster; cast by C++ (or a linked spell) when 205019 expires, with the doomed player as caster.',
    raw_overrides=_standin_raw('Drill stand-in for the burst of a deadline debuff.'),
)

spell_purgeable_205021 = spell(
    id=205021, name='Arcane Shield (drill)', school=School.ARCANE, dispel=1, mechanic=0, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=30000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=19,
                    misc_value=_SCHOOL_ALL, implicit_target_a=_TARGET_UNIT_TARGET_ANY,
                    potency_excluded='drill stand-in: flat +20% damage done on an add')],
    spell_icon_id=566,
    notes='M5 drill stand-in: purgeable Magic buff on an add, +20% damage done, 30 s. Stock Power Word: Shield '
          'icon 566.',
    raw_overrides=_standin_raw('Drill stand-in for a purgeable buff that increases damage done. Lasts $d.',
                               'Drill stand-in for a purgeable buff that increases damage done.'),
)

spell_enrage_205022 = spell(
    id=205022, name='Frenzy (drill)', school=School.NORMAL, dispel=_DISPEL_ENRAGE, mechanic=0, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=30000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=19,
                    misc_value=_SCHOOL_ALL, implicit_target_a=_TARGET_UNIT_TARGET_ANY,
                    potency_excluded='drill stand-in: flat +20% damage done on an add')],
    spell_icon_id=169,
    notes='M5 drill stand-in: Enrage (dispel type 9, soothe) buff on an add, +20% damage done, 30 s. Stock Death '
          'Wish icon 169.',
    raw_overrides=_standin_raw('Drill stand-in for an Enrage effect that increases damage done. Lasts $d.',
                               'Drill stand-in for an Enrage effect that increases damage done.'),
)

spell_aiming_205023 = spell(
    id=205023, name='Aiming (drill)', school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=30000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=502,
    notes='M5 drill stand-in: "Aiming" aura on an add, DUMMY and visual only; the module treats a unit carrying it as '
          'higher priority. 30 s, Dispel none. Stock Mind Vision icon 502.',
    raw_overrides=_standin_raw('Drill stand-in for an add that is preparing a dangerous attack. Lasts $d.',
                               'Drill stand-in for an add that is preparing a dangerous attack.'),
)

# --- NPCs ---------------------------------------------------------------------------------------------------------
_MARKER = dict(
    IconName="", faction=14, minlevel=1, maxlevel=1, detection_range=0, unit_class=1, unit_flags=33554946,
    unit_flags2=2048, type=10, flags_extra=66, ScriptName="npc_boss_mechanic_marker", VerifiedBuild=0,
)
creature_template(300400, "Mechanic Marker", subname="", **{**_MARKER, "flags_extra": 66 | 0x200})
creature_model(300400, display_id=11686)
creature_template(300401, "Mechanic Test Owner", subname="", **_MARKER)
creature_model(300401, display_id=11686)

# --- Mechanics Training Dummy (300402, stage M4 WP-K) ----------------------------------------------------------------
# .agents/plans/dungeon-mechanics/dungeon-mechanics.STAGE-M4-HANDOFF.md section 3.2. Spawned with `.npc add 300402`;
# its AI (mod-boss-mechanics MechanicDummyAI.cpp) owns its own encounter and runs the drill program on itself. It never
# dies, moves or attacks. Re-derived from the healsim boss (training_dummies.py, 900015-900017), with these changes:
#   faction 31        the player training dummies' faction (900001-900003): neutral to everyone (FactionTemplate 31 has
#                     no enemy or friend group), so any player can attack it and, unlike the healsim boss's hostile 14,
#                     also talk to it: Player::GetNPCIfCanInteractWith refuses gossip at reaction unfriendly or worse.
#   npcflag 1         UNIT_NPC_FLAG_GOSSIP: the program / damage / report menu (players need no GM).
#   rank 3            boss rank; type_flags 4 is CREATURE_TYPE_FLAG_BOSS_MOB, so Creature::getLevelForTarget plays it
#                     at the attacker's level + 3 (a level 20 player meets a boss of 23, not of 80) and boss-only
#                     branches behave as on a dungeon boss. The AI also copies the engaging player's level into the
#                     level field, which the reference-health provider reads for percent damage.
#   level 80          the health pool of a level 80 boss times HealthModifier 23809.5, which player DPS cannot dent in
#                     a session; RegenHealth 0. The AI clamps every hit so it never dies and keeps a 40% floor.
#   type 5 (Giant)    deliberately inert, as on the healsim boss (not mechanical: bleeds and poisons land).
#   DamageModifier 0, detection_range 0, CreatureImmunitiesId -362, flags_extra 100925504: the healsim boss's values
#                     (it never swings or aggroes; immune to control, knockback, pull and taunt so nothing moves it; no
#                     XP, no skill gains, no assistance calls). unit_flags stays 0.
creature_template(
    300402, "Mechanics Training Dummy", subname="Boss Mechanics", IconName="", faction=31, npcflag=1, rank=3,
    minlevel=80, maxlevel=80, detection_range=0, DamageModifier=0, BaseAttackTime=2000, RangeAttackTime=2000,
    unit_class=1, unit_flags2=2048, type=5, type_flags=4, HealthModifier=23809.5, RegenHealth=0,
    CreatureImmunitiesId=-362, flags_extra=100925504, ScriptName="npc_boss_mechanics_dummy", VerifiedBuild=0,
)
creature_model(300402, display_id=3019)
creature_template(
    300403, "Descriptor Training Dummy", subname="Boss Mechanics", IconName="", faction=31, npcflag=1, rank=3,
    minlevel=80, maxlevel=80, detection_range=0, DamageModifier=0, BaseAttackTime=2000, RangeAttackTime=2000,
    unit_class=1, unit_flags2=2048, type=5, type_flags=4, HealthModifier=23809.5, RegenHealth=0,
    CreatureImmunitiesId=-273, flags_extra=100925504, ScriptName="npc_boss_mechanics_dummy", VerifiedBuild=0,
)
creature_model(300403, display_id=3019)
# 300403 is 300402 with CreatureImmunitiesId -273 (the reworked bosses' set: stun, fear, root, silence ... but not
# INTERRUPT and not NO_TAUNT), so boss-cast kick drills work live. Same ScriptName: MechanicDummyAI.

# --- M5 drill NPCs (300404-300407) ---------------------------------------------------------------------------------
# Hostile (faction 14), attackable, no loot / XP / reputation. The drill programs (owner SummonCreature entries) place
# them; none has a ScriptName. Level 80, a small pool each (HealthModifier 2) so players can kill or break them.
#   flags_extra 64 = NO_XP; type 7 humanoid; no loot (no loot_id, no gold), no reputation (no faction rewards).
_DRILL_NPC = dict(
    IconName="", faction=14, minlevel=80, maxlevel=80, detection_range=0, DamageModifier=0, BaseAttackTime=2000,
    RangeAttackTime=2000, unit_class=1, unit_flags2=2048, type=7, HealthModifier=2, RegenHealth=0,
    flags_extra=64, ScriptName="", VerifiedBuild=0,
)
creature_template(300404, "Drill Caster", subname="Boss Mechanics", **_DRILL_NPC)  # casts the stand-in spells
creature_model(300404, display_id=2329)  # Defias Conjurer (stock)
creature_template(300405, "Drill Add", subname="Boss Mechanics", **_DRILL_NPC)  # buffed / aiming add
creature_model(300405, display_id=2338)  # Defias Pillager
creature_template(300406, "Drill Copy", subname="Boss Mechanics", **_DRILL_NPC)  # the ignore-list copy
creature_model(300406, display_id=2339)  # Defias Pillager, second skin
creature_template(300407, "Drill Prison", subname="Boss Mechanics", **_DRILL_NPC)  # holds a player; break-out target
creature_model(300407, display_id=2148)  # Defias Prisoner
