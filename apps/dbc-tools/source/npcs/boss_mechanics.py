"""Boss mechanics registry data (mod-boss-mechanics, stages M1 and M4): Weakened, the resolve spells, the drill's bait
rotation stand-in (Baited) and the NPCs.

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
  300400        Mechanic Marker - the telegraph stalker and resolve caster (npc_boss_mechanic_marker).
  300401        Mechanic Test Owner - the hostile owner of `.mech test` (same script).
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
