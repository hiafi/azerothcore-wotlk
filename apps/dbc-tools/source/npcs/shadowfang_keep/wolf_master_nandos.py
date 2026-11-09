"""
Shadowfang Keep build WP-S8: Wolf Master Nandos and his pack (.agents/plans/shadowfang-keep-build/
shadowfang-keep-build.HANDOFF.md s3.5 rows NA1-NA8, s3.6 row S8; build spec docs/dungeons/shadowfang-keep-rework.md
SK 1338-1390 (build spec), SK 1238-1337 (design)). WP-S8 owns this file (its spells: kSpellsNandos 206040-206059 in
modules/mod-dungeon-bosses src/ShadowfangKeep/ShadowfangKeepRework.h only; NandosLogic.h names the same ids).

- 3927 Wolf Master Nandos: bound to boss_wolf_master_nandos_rework (SmartAI off; WP-S8's SQL rev drops the stock rows),
  normal 9,378 (HealthModifier 18, warrior base 521 at 21), stun immune (IMMUNITY_BOSS_STUN 1972). Stock melee
  (DamageModifier 3.3 on a 2.0 s swing). Heroic 244,160 is WP-H's override in source/world/dungeons/shadowfang_keep.py.
- 300509-300512, the pack (SK ruling 4: boss kit): copies of the stock Bleak Worg 3861, Lupine Horror 3863, Slavering
  Worg 3862 and Wolfguard Worg 5058 (read-only SELECTs 2026-11-07: rank, family, type, flags, speeds, swing, damage,
  loot, skinning, immunities, model), fixed at level 20 with HealthModifier 3.099 (warrior base 484: 1,500, the build
  spec's number), npc_sfk_pack_wolf instead of SmartAI. The stock entries stay stock (they are trash elsewhere in the
  keep). WP-S8's SQL rev repoints spawns 16239 / 16238 / 16240 / 16241 to them (spawnMask 3). Heroic 30,000 each is
  WP-H's `_KIT_ADD_HEROIC` (applied because this file declares them); each row names its heroic entry
  (difficulty_entry_1, STAGE-H report s4: 310064-310067).
- Lupine Delusion 5097 stays stock (its SmartAI despawns it when hit).

Spells (Spell.dbc 3.3.5 for every stock id quoted):

  206040  Acid Slaver        NA4 the 2 s cast bar (no effect, not interruptible), Acid Breath 12533's SV 2619 (the
                             acid breath plays from the caster when the bar ends, as the cone lands) and icon 636
  206041  Acid Slaver        NA4 the registry's resolve copy, Nature: 35% + Weakened on the 90 degree cone, the
                             caster's target exempt (8 yd from a Slavering Worg, 20 yd from Nandos inherited). SV 2619
                             for the poison impact on every player hit (VISUALS-REPORT correction 6: not Acid Spit's
                             missile)
  206042  Guardian Howl      NA5 normal: 2 s cast, interruptible (InterruptFlags 15, PreventionType silence), HEAL_PCT
                             5% on Nandos and the living pack (spell_sfk_nandos_guardian_howl keeps only them), Howling
                             Rage 7481's SV 754 and icon 50
  206043  Guardian Howl      NA5 heroic: the same plus +15% damage done for 10 s on the same units
  206044  Pack Bond          NA7 Nandos's buff: MOD_DAMAGE_PERCENT_TAKEN, -40% as declared; the script sets -10 per
                             living wolf (AuraEffect::ChangeAmount) and removes it with the last wolf. Not dispellable
  206045  Pack Bond          NA7 the look: each living wolf casts it on Nandos, a hidden DUMMY aura with Blood Mirror
                             70445's SV 14876 (a red beam from the wolf to him), removed when that wolf dies
  206046  Marked Prey        NA6 the prey's 4 s head marker: Hunter's Mark 1130's SV 3239 (the red arrow), icon 538,
                             a DUMMY debuff naming the job. Dispel none
  206047  Mark the Prey      NA6 a lunging wolf's hit, Physical: the share (25% of reference health per living wolf,
                             split among the players in the ring, 75% cap) is the script's base point
                             (CastCustomSpell), DieSides 0. Rip 1079's SV 3941 (claw swipe on the wolf, blood burst on
                             the player; VISUALS-REPORT correction 5: not Lunge's frost blade). The resolve attribute
                             set (no defense, always hit, no crit, ignores caster modifiers: Guardian Howl's buff does
                             not reach it)
  206048  Wavering Will      NA1 inherited (heroic): a Shadow DoT, 2% of reference health per stack every 2 s
                             (spell_sfk_nandos_wavering_will sets the per-stack amount), 5 stacks, 60 s, Magic; one
                             dispel clears every stack and the stock 7127 slows Nandos put with it. Wavering Will
                             7127's icon 221 and SV 599
  206049  Lupine Terror      NA3 (heroic): the fear rider, 2 s (the shared loss of control limit), mechanic fear,
                             Terrifying Howl 8715's SV 247 (the fear state over the head), icon 166. Magic
  206050  Lupine Terror      NA3 the fear spot's resolve copy (Shadow, no damage: the registry Circle carries only the
                             rider), so the combat log names it
  206051-206059 spare.

Stock spells kept (DD scales them on heroic): Wavering Will 7127 (Bleak Worg; Nandos inherited), Summon Lupine
Delusions 7132 (Lupine Horror; Nandos inherited).
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
from ._visuals import NA_ACID_SLAVER, NA_HOWLING_RAGE, NA_LUNGE, NA_MARK_THE_PREY, NA_PACK_BOND, NA_TERRIFYING_HOWL

creature_template_columns(3927, **boss_columns('boss_wolf_master_nandos_rework', 18))

# --- The pack (boss kit) -------------------------------------------------------------------------------------------

# Level 20, warrior base 484: HealthModifier 3.099 gives ceil(484 x 3.099) = 1,500 (3.1 would round up to 1,501).
_PACK_HEALTH_MODIFIER = 3.099

_PACK = {
    **KIT_CREATURE, 'minlevel': 20, 'maxlevel': 20, 'unit_class': 1, 'HealthModifier': _PACK_HEALTH_MODIFIER,
    'DamageModifier': 1.7, 'pickpocketloot': 0, 'mingold': 0, 'maxgold': 0, 'ScriptName': 'npc_sfk_pack_wolf',
}

bleak_worg_300509 = creature_template(
    300509, 'Bleak Worg', **{**_PACK, 'rank': 1, 'family': 1, 'type': 1, 'type_flags': 1, 'unit_flags': 64,
                             'BaseAttackTime': 2000, 'ExperienceModifier': 1.25, 'lootid': 3861, 'skinloot': 100006,
                             'CreatureImmunitiesId': -6, 'difficulty_entry_1': 310064},
)
creature_model(300509, display_id=801)

lupine_horror_300510 = creature_template(
    300510, 'Lupine Horror', **{**_PACK, 'rank': 1, 'family': 0, 'type': 6, 'type_flags': 0, 'unit_flags': 64,
                                'BaseAttackTime': 2000, 'ExperienceModifier': 1.25, 'lootid': 3863, 'skinloot': 0,
                                'CreatureImmunitiesId': -114, 'difficulty_entry_1': 310065},
)
creature_model(300510, display_id=2446)

slavering_worg_300511 = creature_template(
    300511, 'Slavering Worg', **{**_PACK, 'rank': 1, 'family': 1, 'type': 1, 'type_flags': 1, 'unit_flags': 64,
                                 'speed_run': 1.42857, 'BaseAttackTime': 1200, 'ExperienceModifier': 1.25,
                                 'lootid': 3862, 'skinloot': 100006, 'CreatureImmunitiesId': 0,
                                 'difficulty_entry_1': 310066},
)
creature_model(300511, display_id=11421)

wolfguard_worg_300512 = creature_template(
    300512, 'Wolfguard Worg', **{**_PACK, 'rank': 0, 'family': 1, 'type': 1, 'type_flags': 0, 'unit_flags': 0,
                                 'detection_range': 18.0, 'BaseAttackTime': 1500, 'ExperienceModifier': 1.0,
                                 'lootid': 5058, 'skinloot': 100006, 'CreatureImmunitiesId': 0,
                                 'difficulty_entry_1': 310067},
)
creature_model(300512, display_id=246)

# --- Spells --------------------------------------------------------------------------------------------------------

_TARGET_UNIT_SRC_AREA_ALLY = 30
_TARGET_UNIT_TARGET_ENEMY = 6

_DISPEL_MAGIC = 1
_MECHANIC_FEAR = 5
_SCHOOL_ALL = 127
_INTERRUPT_FLAGS_STANDARD = 15     # movement, pushback, interrupt, auto-attack: a kickable cast
_PREVENTION_SILENCE = 1

_ICON_ACID_BREATH = 636     # Acid Breath 12533
_ICON_HOWL = 50             # Howling Rage 7481
_ICON_BLOOD_MIRROR = 1876   # Blood Mirror 70445
_ICON_HUNTERS_MARK = 538    # Hunter's Mark 1130
_ICON_RIP = 108             # Rip 1079
_ICON_WAVERING_WILL = 221   # Wavering Will 7127
_ICON_TERRIFYING_HOWL = 166  # Terrifying Howl 8715

# The looks (WP-V's _visuals.py, VISUALS-REPORT section 19 top picks); Wavering Will keeps its stock look.
_SV_ACID_BREATH = NA_ACID_SLAVER        # 2619, Acid Breath 12533
_SV_HOWLING_RAGE = NA_HOWLING_RAGE      # 754, Howling Rage 7481
_SV_BLOOD_MIRROR = NA_PACK_BOND         # 14876, Blood Mirror 70445
_SV_HUNTERS_MARK = NA_MARK_THE_PREY     # 3239, Hunter's Mark 1130
_SV_RIP = NA_LUNGE                      # 3941, Rip 1079
_SV_WAVERING_WILL = 599                 # Wavering Will 7127
_SV_TERRIFYING_HOWL = NA_TERRIFYING_HOWL  # 247, Terrifying Howl 8715

_SCRIPT_EXCLUDED = 'Shadowfang Keep: a percent of reference health, set by the script (DungeonKit::RefFlat)'

# --- NA4 Acid Slaver -----------------------------------------------------------------------------------------------
acid_slaver_bar_206040 = cast_bar(
    206040, 'Acid Slaver', 2000, 'Slavers acid in a cone in front of the caster.',
    'Shadowfang Keep WP-S8: NA4 the 2 s cast bar on a Slavering Worg (8 yd) or, inherited on heroic, Nandos (20 yd). '
    'No effect, not interruptible: the registry Frontal registered beside it owns the hit. Acid Breath 12533\'s SV '
    '2619: the acid breath plays from the caster as the bar ends and the cone lands.',
    icon=_ICON_ACID_BREATH, visual=_SV_ACID_BREATH, school=School.NATURE,
)

acid_slaver_206041 = resolve_copy(
    206041, 'Acid Slaver', School.NATURE, 'Acid in a cone.',
    'Shadowfang Keep WP-S8: NA4 the resolve copy (Nature): 35% + 1 Weakened on everyone in the 90 degree cone but the '
    'caster\'s target. SV 2619 for the poison impact on each player hit (VISUALS-REPORT correction 6).',
    icon=_ICON_ACID_BREATH, visual=_SV_ACID_BREATH,
)


# --- NA5 Guardian Howl ---------------------------------------------------------------------------------------------
def _guardian_howl(spell_id: int, heroic: bool):
    effects = [Effect(type=EffectType.HEAL_PCT, base_points=4, implicit_target_a=TARGET_SRC_CASTER,
                      implicit_target_b=_TARGET_UNIT_SRC_AREA_ALLY, radius_yards=50.0,
                      potency_excluded='Shadowfang Keep: a percent of each unit\'s own health, not a heal value')]
    desc = 'Heals Nandos and every wolf of his pack for $s1% of their health.'
    if heroic:
        effects.append(Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=14,
                              misc_value=_SCHOOL_ALL, implicit_target_a=TARGET_SRC_CASTER,
                              implicit_target_b=_TARGET_UNIT_SRC_AREA_ALLY, radius_yards=50.0,
                              potency_excluded='Guardian Howl: a flat +15% damage done, not a damage value'))
        desc = ('Heals Nandos and every wolf of his pack for $s1% of their health and increases their damage done by '
                '$s2% for $d.')
    label = 'heroic: heals 5% and +15% damage done for 10 s' if heroic else 'normal: heals 5%'
    s = spell(
        id=spell_id, name='Guardian Howl', school=School.NORMAL, cast_time_ms=2000, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=10000 if heroic else 0, effects=effects, spell_icon_id=_ICON_HOWL,
        notes=f'Shadowfang Keep WP-S8: NA5 {label}. A real 2 s cast by the Wolfguard Worg (8 s, then every 20 s) or, '
              'inherited on heroic, Nandos (every 20 s); interruptible (InterruptFlags 15, PreventionType silence; on '
              'the descriptor\'s interrupt list). The 50 yd area-ally search is cut to Nandos and the living pack by '
              'spell_sfk_nandos_guardian_howl. Howling Rage 7481\'s SV 754 (the roar).',
        raw_overrides=kit_raw(desc, 'Damage done increased by $s2%.' if heroic else '', CastingTimeIndex=5,
                              InterruptFlags=_INTERRUPT_FLAGS_STANDARD, PreventionType=_PREVENTION_SILENCE,
                              SpellVisualID_1=_SV_HOWLING_RAGE),
    )
    scripted_by(s, 'spell_sfk_nandos_guardian_howl')
    return s


guardian_howl_206042 = _guardian_howl(206042, heroic=False)
guardian_howl_heroic_206043 = _guardian_howl(206043, heroic=True)

# --- NA7 Pack Bond -------------------------------------------------------------------------------------------------
pack_bond_206044 = spell(
    id=206044, name='Pack Bond', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=-41,
                    misc_value=_SCHOOL_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Pack Bond: a damage taken percent, not a damage value')],
    spell_icon_id=_ICON_BLOOD_MIRROR,
    notes='Shadowfang Keep WP-S8: NA7 on Nandos from the pull: damage taken -40% (BasePoints -41 + DieSides 1) while '
          'all four wolves live; boss_wolf_master_nandos_rework sets the amount to -10 per living wolf '
          '(AuraEffect::ChangeAmount: -30, -20, -10, additive steps, not four multiplied auras) and removes the aura '
          'with the last wolf. Not dispellable, not stealable (Dispel none).',
    raw_overrides=kit_raw('Damage taken reduced.', 'Damage taken reduced.', CastingTimeIndex=1),
)

pack_bond_link_206045 = spell(
    id=206045, name='Pack Bond', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_BLOOD_MIRROR,
    notes='Shadowfang Keep WP-S8: NA7\'s look. Each living wolf casts it on Nandos at the pull: a hidden DUMMY aura '
          'with Blood Mirror 70445\'s SV 14876, whose StateKit chain draws a red beam from the aura\'s caster (the '
          'wolf) to its holder (VISUALS-REPORT gap 19, top pick). The script removes that wolf\'s aura when it dies, '
          'so the beams count the -10% steps. No effect.',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=_SV_BLOOD_MIRROR, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- NA6 Mark the Prey ---------------------------------------------------------------------------------------------
marked_prey_206046 = spell(
    id=206046, name='Marked Prey', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=4000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=0,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_HUNTERS_MARK,
    notes='Shadowfang Keep WP-S8: NA6 the prey\'s head marker for the 4 s of the Stack ring (Hunter\'s Mark 1130\'s SV '
          '3239, the red arrow; VISUALS-REPORT gap 19). DUMMY, AURA_IS_DEBUFF + NO_IMMUNITIES (it lands through Divine '
          'Shield), Dispel none: the ring is the job.',
    raw_overrides=kit_raw('The pack lunges at you in $d. Gather your allies around you to share the bites.',
                          'The pack lunges at you soon. Gather your allies.', CastingTimeIndex=1,
                          SpellVisualID_1=_SV_HUNTERS_MARK),
)

mark_the_prey_206047 = spell(
    id=206047, name='Mark the Prey', school=School.NORMAL, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=0, die_sides=0,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY,
                    potency_excluded='Shadowfang Keep: a split share of reference health, the script\'s base point')],
    spell_icon_id=_ICON_RIP,
    notes='Shadowfang Keep WP-S8: NA6 a wolf\'s lunge. boss_wolf_master_nandos_rework computes the shares when the '
          'Stack resolves (DungeonKit::SplitShares: 25% of reference health per living wolf, split among the players '
          'in the ring, at most 75% each) and each share is cast by one of the living wolves (round robin) with the '
          'share as base point 0 (DieSides 0: exact). Physical, no Weakened (a split hit). The resolve attribute set '
          '(no active defense, redirection, reflection or threat; ignores LoS; cannot crit; not a proc; always hits; '
          'ignores caster modifiers). Rip 1079\'s SV 3941: a claw swipe on the wolf and a blood burst on the player.',
    raw_overrides=kit_raw('The pack lunges at its prey.', CastingTimeIndex=1, SpellVisualID_1=_SV_RIP,
                          Attributes=ATTR0_NO_ACTIVE_DEFENSE,
                          AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_NOT_A_PROC | ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, DefenseType=1),
)

# --- NA1 Wavering Will (inherited, heroic) -------------------------------------------------------------------------
wavering_will_206048 = spell(
    id=206048, name='Wavering Will', school=School.SHADOW, dispel=_DISPEL_MAGIC, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=60000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE, base_points=0, amplitude=2000,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_EXCLUDED)],
    spell_icon_id=_ICON_WAVERING_WILL,
    notes='Shadowfang Keep WP-S8: NA1 inherited (heroic). Once the Bleak Worg dies, Nandos puts the stock 7127 slows '
          'and one stack of this on his tank every 15 s (DungeonKit::AddStacks, 5 at most). Each stack deals 2% of '
          'reference health as Shadow every 2 s (spell_sfk_nandos_wavering_will sets the per-stack amount; the aura '
          'multiplies it by the stacks), 60 s, refreshed by each stack. Magic: the same script makes one dispel clear '
          'every stack and the stock slows from the same caster. ALWAYS_HIT, NO_REFLECTION, IGNORE_CASTER_MODIFIERS '
          '(Guardian Howl\'s buff does not reach it). Wavering Will 7127\'s icon 221 and SV 599.',
    raw_overrides=kit_raw('Deals Shadow damage every $t1 sec for $d, more with each stack, up to 5 stacks.',
                          'Shadow damage every $t1 sec.', CastingTimeIndex=1, CumulativeAura=5,
                          AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                          AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS, DefenseType=1,
                          SpellVisualID_1=_SV_WAVERING_WILL),
)
scripted_by(wavering_will_206048, 'spell_sfk_nandos_wavering_will')

# --- NA3 Lupine Terror (heroic) ------------------------------------------------------------------------------------
lupine_terror_206049 = spell(
    id=206049, name='Lupine Terror', school=School.SHADOW, dispel=_DISPEL_MAGIC, mechanic=_MECHANIC_FEAR,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=100.0, duration_ms=2000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_FEAR, base_points=0,
                    mechanic=_MECHANIC_FEAR, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_TERRIFYING_HOWL,
    notes='Shadowfang Keep WP-S8: NA3 (heroic) the fear rider of the 5 yd spot a vanished delusion leaves (2 s after '
          'it vanishes): 2 s fear (the shared loss of control limit), mechanic fear (Fear Ward, Berserker Rage and '
          'fear immunities still work), Magic. Cast by the registry marker at the spot (the rider caster), so the '
          'feared player runs from the spot. Terrifying Howl 8715\'s SV 247 (the fear state over the head) and icon '
          '166.',
    raw_overrides=kit_raw('Feared for $d.', 'Feared.', CastingTimeIndex=1, SpellVisualID_1=_SV_TERRIFYING_HOWL),
)

lupine_terror_hit_206050 = resolve_copy(
    206050, 'Lupine Terror', School.SHADOW, 'Fear where a delusion vanished.',
    'Shadowfang Keep WP-S8: NA3 (heroic) the 5 yd fear spot\'s resolve copy. The registry Circle has no damage, only '
    'the 206049 rider, so this names the hit in the combat log; no visual (the fear state is the rider\'s).',
    icon=_ICON_TERRIFYING_HOWL,
)
