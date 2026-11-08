"""
Scholomance build WP-S1: Jandice Barov (10503), her Shell Game copies (11439, reused) and her reflections (300530)
(.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.4 rows JB, s3.5 row S1, s3.8, s7 #12; build spec
docs/dungeons/scholomance-rework.md SC 546-601, design SC 380-545). WP-S1 owns this file (its spells: kSpellsJandice
206110-206129 only; modules/mod-dungeon-bosses src/Scholomance/JandiceLogic.h names the same ids). The SQL rev
(data/sql/updates/pending_db_world/) drops SmartAI 10503, adds the emotes 1-3 and the reflection's journal.

- 10503 Jandice Barov: bound to boss_jandice_barov_rework (SmartAI off), normal 175k (HealthModifier 69.583 on the
  level 61 class base 2,515), stun immune (1972), INSTANCE_BIND. DamageModifier 3.5, the stock Scholomance value (the
  live 5 is a mod-progression leftover, handoff s2.3); heroic melee is the damage hook's tier swing. Heroic 265k is
  WP-H's override in source/world/dungeons/scholomance.py.
- 11439 Illusion of Jandice Barov, reused as the Shell Game copy (hers alone: no spawn, no other summoner). Its
  columns make it look exactly like her: her name, class (paladin: the same mana bar), unit_flags, mana modifier, walk
  speed and immunity set (an AoE root or fear must not tell the copies from her), still (MovementType 0), no health
  regen; no melee (DamageModifier 0), no XP. Health: her normal 175k on the template (HealthModifier 69.583, the same
  class base); the script mirrors her current health and mana onto every copy anyway. npc_sc_shell_game_copy clears its
  journal (equipment), takes 0 from everything and shatters on a direct hit.
- 300530 Reflection of Jandice Barov (npc_sc_jandice_reflection): her look (display 11073), not selectable or
  attackable (KIT_HELPER), level 61. creature_equip_template ID 1 (the SQL rev) is the journal 12866: the boss loads
  it on a real reflection and clears it on the heroic decoy.

  206110  Curse of Blood     JB9: a copy of 16098 (never the stock id): 2 s cast (interruptible as the stock one),
                             everyone within 10 yd, physical damage taken +20% for 30 s, Curse (the dispel list).
  206111  The Shell Game     JB2: her vanish (self): Blood Mirror (Transition Visual) 50910's SV 11181.
  206112  Shatter            JB3: a copy's hit on its attacker (a pet's owner), 25% / 40% Shadow of the reference row
                             (spell_sc_jandice_shatter, RefFlatOn at launch; the tank's row on the tank). Damage only.
  206113  Shatter            JB3: the copy shatters (self): Crystal Shatter Visual 51150's SV 11222.
  206114  Unmasked           JB4: damage taken +20% for 8 s on Jandice.
  206115  Blood Sigil        JB1 / JB5: the registry resolve copy (Shadow), Blood Nova's SV 9312 on whoever is hit.
  206116  Bloodlines         JB6: the registry resolve copy (Shadow), SV 9312.
  206117  Blood Price        JB8 (heroic): 4% Shadow on every player (spell_sc_jandice_blood_price, RefFlat at
                             launch), Blood Boil 48721's SV 11117 on each.
  206118  Reflection         a reflection or copy appears / a copy dissolves (self): Mirror Image 36847's SV 2046.
  206119  Blood Sigil        a real circle bursts at its reflection (self): SV 9312.
  206120  Fake Sigil         the heroic decoy pops harmlessly (self): Vanish Visual 24222's SV 255.
  206121  Blood Thread       JB7 (heroic): the 1 s thread from one swapping figure to the other (a DUMMY aura): Blood
                             Mirror 70445's SV 14876.
  206122  Blood Beam         JB6: a lane reflection's beam (a DUMMY aura on itself until it dissolves): Blood Beam
                             Visual RHand 72304's SV 15275.
  206123-206129 spare.
"""

from lib.dsl import RANGE_SELF, AuraType, DispelType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_REDIRECTION,
    ATTR1_NO_REFLECTION,
    ATTR1_NO_THREAT,
    RESOLVE_RAW,
    TARGET_SRC_CASTER,
    TARGET_UNIT_SRC_AREA_ENEMY,
    TARGET_UNIT_TARGET_ENEMY,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR4_NO_CAST_LOG,
    IMMUNITY_BOSS_STUN,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    JB_BLOOD_PRICE_TICK,
    JB_BLOODLINES_BEAM,
    JB_COPY_SHATTERS,
    JB_FAKE_SIGIL_POP,
    JB_REFLECTION_POOF,
    JB_SHUFFLE_THREAD,
    JB_SIGIL_BURST,
    JB_VANISH_INTO_COPIES,
)

_HEALTH_MODIFIER = 69.583           # 175,000 / 2,515 (level 61 paladin base, exp 0)

creature_template_columns(10503, **boss_columns('boss_jandice_barov_rework', _HEALTH_MODIFIER, DamageModifier=3.5))

# --- the Shell Game copy 11439 (reused) ------------------------------------------------------------------------------

_JANDICE_UNIT_FLAGS = 32832         # 10503's own unit_flags (read-only SELECT 2026-11-08)
_JANDICE_MANA_MODIFIER = 3.0        # 10503's ManaModifier
_FLAGS_EXTRA_NO_XP = 0x40

creature_template_columns(
    11439, name='Jandice Barov', ScriptName='npc_sc_shell_game_copy', AIName='', unit_class=2,
    unit_flags=_JANDICE_UNIT_FLAGS, HealthModifier=_HEALTH_MODIFIER, ManaModifier=_JANDICE_MANA_MODIFIER,
    DamageModifier=0.0, speed_walk=1.0, MovementType=0, RegenHealth=0, ExperienceModifier=0.0,
    CreatureImmunitiesId=IMMUNITY_BOSS_STUN, flags_extra=_FLAGS_EXTRA_NO_XP,
)

# --- the reflection 300530 -------------------------------------------------------------------------------------------

_DISPLAY_JANDICE = 11073            # creature_template_model 10503 and 11439

reflection_of_jandice_barov_300530 = creature_template(
    300530, 'Reflection of Jandice Barov',
    **{**KIT_HELPER, 'minlevel': 61, 'maxlevel': 61, 'unit_class': 2, 'speed_walk': 1.0,
       'ScriptName': 'npc_sc_jandice_reflection'},
)
creature_model(300530, display_id=_DISPLAY_JANDICE)

# --- spells (206110-206129) ------------------------------------------------------------------------------------------

_SCHOOL_MASK_PHYSICAL = 1
_SCHOOL_MASK_ALL = 127
_DEFENSE_MAGIC = 1
_INTERRUPT_FLAGS_STANDARD = 15
_PREVENTION_SILENCE = 1
_SV_CURSE_OF_BLOOD = 876            # Curse of Blood 16098's own SpellVisual

_ICON_CURSE_OF_BLOOD = 130          # Curse of Blood 16098
_ICON_BLOOD_MIRROR = 1876           # Blood Mirror 70445
_ICON_MIRROR_IMAGE = 1489           # Mirror Image 36847
_ICON_BLOOD_BOIL = 2725             # Blood Boil 48721

_REF_FLAT_NOTE = ('Scholomance boss spell: the script sets the damage at launch (DungeonKit::RefFlat, a percent of the '
                  'reference row); the base points are a placeholder')

curse_of_blood_206110 = spell(
    id=206110, name='Curse of Blood', school=School.SHADOW, dispel=DispelType.CURSE, mechanic=0,
    attributes=ATTR0_AURA_IS_DEBUFF, cast_time_ms=2000, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0,
    mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=30000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=19,
                    misc_value=_SCHOOL_MASK_PHYSICAL, implicit_target_a=TARGET_SRC_CASTER,
                    implicit_target_b=TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=10.0,
                    potency_excluded='Curse of Blood: a flat +20% physical damage taken, not a damage or heal value')],
    spell_icon_id=_ICON_CURSE_OF_BLOOD,
    notes='Scholomance WP-S1, JB9 Curse of Blood: a copy of the stock 16098 (never the stock id), Jandice\'s 2 s cast '
          'at 3 to 11 s, then every 30 s (never in the Shell Game). Everyone within 10 yd: physical damage taken +20% '
          'for 30 s (BasePoints 19 + DieSides 1, misc 1 = physical; the stock +2 per hit did nothing at 60). Curse '
          '(DispelType 2; the descriptor\'s dispel list: decursing is a reward). Interruptible as the stock spell '
          '(InterruptFlags 15, PreventionType silence), not on the interrupt list. The stock SpellVisual 876.',
    raw_overrides=kit_raw('Increases the Physical damage taken by nearby enemies by $s1% for $d.',
                          'Physical damage taken increased by $s1%.', InterruptFlags=_INTERRUPT_FLAGS_STANDARD,
                          PreventionType=_PREVENTION_SILENCE, DefenseType=_DEFENSE_MAGIC,
                          AttributesEx=ATTR1_NO_REDIRECTION | ATTR1_NO_REFLECTION,
                          SpellVisualID_1=_SV_CURSE_OF_BLOOD),
)

the_shell_game_206111 = self_visual(
    206111, 'The Shell Game', JB_VANISH_INTO_COPIES,
    'Scholomance WP-S1, JB2: Jandice vanishes into her copies; she casts it (triggered) on herself with the emote, '
    'then is gone for 1 s. Blood Mirror (Transition Visual) 50910\'s SpellVisual 11181.',
    icon=_ICON_BLOOD_MIRROR, school=School.SHADOW)

shatter_206112 = spell(
    id=206112, name='Shatter', school=School.SHADOW, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=TARGET_UNIT_TARGET_ENEMY,
                    potency_excluded=_REF_FLAT_NOTE)],
    spell_icon_id=_ICON_MIRROR_IMAGE,
    notes='Scholomance WP-S1, JB3 Shatter: a Shell Game copy hit directly (a melee swing or a spell aimed at it; area '
          'damage never touches a copy) shatters and hits its attacker (a pet\'s owner): 25% normal / 40% heroic '
          'Shadow of the reference row, the tank\'s row on the tank (spell_sc_jandice_shatter, RefFlatOn at launch, '
          'so the target\'s own reductions apply). Damage only, no Weakened (designer). Cast by the copy, triggered. '
          'Blood Nova 72379\'s SpellVisual 9312 on the attacker. The resolve attribute set (no defense, reflect, '
          'threat, LoS, crit; always hit; IGNORE_CASTER_MODIFIERS).',
    raw_overrides=kit_raw('The illusion shatters, and the blood in it lashes back at you.',
                          SpellVisualID_1=JB_SIGIL_BURST, **RESOLVE_RAW),
)
scripted_by(shatter_206112, 'spell_sc_jandice_shatter')

shatter_look_206113 = self_visual(
    206113, 'Shatter', JB_COPY_SHATTERS,
    'Scholomance WP-S1, JB3: a struck copy shatters (cast on itself, triggered) and is gone 0.4 s later. Crystal '
    'Shatter Visual 51150\'s SpellVisual 11222.',
    icon=_ICON_MIRROR_IMAGE, school=School.SHADOW)

unmasked_206114 = spell(
    id=206114, name='Unmasked', school=School.SHADOW, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=8000,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_TAKEN, base_points=19,
                    misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                    potency_excluded='Unmasked: a flat +20% damage taken, not a damage or heal value')],
    spell_icon_id=_ICON_BLOOD_MIRROR,
    notes='Scholomance WP-S1, JB4 Unmasked: the reward for a fast find. Jandice casts it on herself (triggered) on '
          'the hit that ends the Shell Game (heroic: on the first find): damage taken +20% from every school for 8 s '
          '(BasePoints 19 + DieSides 1). Dispel none.',
    raw_overrides=kit_raw('Damage taken increased by $s1%. Lasts $d.', 'Damage taken increased by $s1%.',
                          CastingTimeIndex=1),
)

blood_sigil_206115 = resolve_copy(
    206115, 'Blood Sigil', School.SHADOW, 'A blood sigil bursts beneath you.',
    'Scholomance WP-S1, JB1 / JB5: a copy of the registry resolve spell 205001 under its own name (Shadow), bound to '
    'spell_boss_mechanics_resolve: the 8 yd circle around a real reflection (JB1: 40% normal / 60% heroic; the '
    'heroic grid\'s circles are 9 yd) and around every copy left standing when the Shell Game runs out (JB5: the '
    'same numbers). No Weakened (penalty none). Blood Nova 72379\'s SpellVisual 9312 on whoever is hit.',
    icon=_ICON_BLOOD_MIRROR, visual=JB_SIGIL_BURST)

bloodlines_206116 = resolve_copy(
    206116, 'Bloodlines', School.SHADOW, 'Blood floods your lane.',
    'Scholomance WP-S1, JB6: a copy of the registry resolve spell 205001 under its own name (Shadow), bound to '
    'spell_boss_mechanics_resolve: every real lane on the aisle frame (whole lanes: 6.17 yd across, 5.25 yd along) '
    'and the alcove\'s circle, 50% normal / 70% heroic. No Weakened (penalty none). SpellVisual 9312 on whoever is '
    'hit.',
    icon=_ICON_BLOOD_MIRROR, visual=JB_SIGIL_BURST)

blood_price_206117 = spell(
    id=206117, name='Blood Price', school=School.SHADOW, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=TARGET_SRC_CASTER,
                    implicit_target_b=TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=100.0,
                    potency_excluded=_REF_FLAT_NOTE)],
    spell_icon_id=_ICON_BLOOD_BOIL,
    notes='Scholomance WP-S1, JB8 Blood Price (heroic): every 3 s while the Shell Game is up, 4% Shadow of the '
          'reference non-tank row on every player within 100 yd (players only; spell_sc_jandice_blood_price, RefFlat '
          'at launch). Unavoidable healer work, no Weakened; a 25 s game is 8 ticks, 32%. Cast by Jandice, '
          'triggered. Blood Boil 48721\'s SpellVisual 11117 on each player. The resolve attribute set.',
    raw_overrides=kit_raw('The illusions feed on your blood.', SpellVisualID_1=JB_BLOOD_PRICE_TICK, **RESOLVE_RAW),
)
scripted_by(blood_price_206117, 'spell_sc_jandice_blood_price')

reflection_206118 = self_visual(
    206118, 'Reflection', JB_REFLECTION_POOF,
    'Scholomance WP-S1: a reflection or a Shell Game copy appears (and a copy dissolves when the game is won), cast on '
    'itself, triggered. Mirror Image 36847\'s SpellVisual 2046 (the summon poof; the look is the display).',
    icon=_ICON_MIRROR_IMAGE, school=School.SHADOW)

blood_sigil_burst_206119 = self_visual(
    206119, 'Blood Sigil', JB_SIGIL_BURST,
    'Scholomance WP-S1, JB1 / JB5 / JB6: a real circle or lane bursts at its reflection (or copy), which is gone 0.4 s '
    'later. Blood Nova 72379\'s SpellVisual 9312.',
    icon=_ICON_BLOOD_MIRROR, school=School.SHADOW)

fake_sigil_206120 = self_visual(
    206120, 'Fake Sigil', JB_FAKE_SIGIL_POP,
    'Scholomance WP-S1, JB1 / JB6 heroic: the empty-handed reflection\'s decoy circle or lane pops harmlessly. Vanish '
    'Visual 24222\'s SpellVisual 255.',
    icon=_ICON_MIRROR_IMAGE, school=School.SHADOW)


def _look_aura(spell_id: int, name: str, visual: int, duration_ms: int, target: int, notes: str):
    """A shown (not passive) DUMMY aura with no handler, hidden from the buff frame, for its SpellVisual's state."""
    return spell(
        id=spell_id, name=name, school=School.SHADOW, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=duration_ms,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=target)],
        spell_icon_id=_ICON_BLOOD_MIRROR, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx4=ATTR4_NO_CAST_LOG),
    )


blood_thread_206121 = _look_aura(
    206121, 'Blood Thread', JB_SHUFFLE_THREAD, 1000, TARGET_UNIT_TARGET_ANY,
    'Scholomance WP-S1, JB7 Shuffle (heroic): the 1 s thread between two figures about to swap places, cast by one '
    'on the other (triggered); then they run to each other\'s spots. Blood Mirror 70445\'s SpellVisual 14876 (a beam '
    'between the two is unconfirmed: check in game).')

blood_beam_206122 = _look_aura(
    206122, 'Blood Beam', JB_BLOODLINES_BEAM, -1, TARGET_UNIT_CASTER,
    'Scholomance WP-S1, JB6 Bloodlines: a lane reflection\'s blood, on itself until the lanes burst and it dissolves. '
    'Blood Beam Visual RHand 72304\'s SpellVisual 15275 (a beam down the lane is unconfirmed: check in game).')
