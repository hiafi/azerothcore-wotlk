"""
Shaman - SH0b A5: the three shared ground / burst spells, Earthquake, Elemental Blast and Healing Rain, with their
tick / pulse helpers, trainer rows, spellbook entries and script bindings.

Source of truth: docs/reworks/shaman-shared-rework.md (Earthquake, Elemental Blast, Healing Rain),
.agents/plans/shaman-rework/shaman-rework.SH0b-WP-BRIEF.md (id map, decisions, consts),
shaman-rework.T0b-REPORT.md sections 4 and 8 (the fixed-tick ground shape, Earthquake as a Nature direct tick),
shaman-rework.HEALING-RAIN-VFX.md and p0-spike-ref/shaman_p0_spike.py (the Healing Rain shape that passed the P0
playtest, ring SpellVisual 90130), SH0-HANDOFF.md (family bits, potency table, lessons L1-L18, H7, H8).

Ids (spell block 202260-202339, brief id map): 202280 Earthquake (ground cast), 202281 Earthquake tick,
202282 Elemental Blast, 202283 Healing Rain (ground cast), 202284 Healing Rain heal. SkillLineAbility 30666-30668.

Shape of the two ground casts (T0b section 4, "the trigger shape"): eff0 PERSISTENT_AREA_AURA with a dummy aura makes
the DynamicObject and draws the PersistentAreaKit of the cast's SpellVisual; eff1 is a PERIODIC_DUMMY on the caster
(Earthquake 1000 ms for 6 s, Healing Rain 2000 ms for 20 s) that the aura script turns into one single-target
triggered cast per target (caster = the shaman). Neither row carries AttributesEx5 0x2000 (SPELL_HASTE_AFFECTS_PERIODIC,
the Blizzard 10 / Rain of Fire 5740 clone trap), 0x200 (EXTRA_INITIAL_PERIOD would add a tick), or a periodic
damage / heal aura, so the ticks never speed up with haste (6 and 10 ticks at any haste). Attributes stays 0:
DO_NOT_DISPLAY (0x80) hid the spell from the spellbook in the P0 retest. The caster's own aura is hidden with
AttributesEx5 0x08000000 (NO_CASTER_AURA_ICON).

Family bits (SH0-HANDOFF "Family bits"): Earthquake cast + tick d2 b19, Elemental Blast d2 b20, Healing Rain cast +
heal d2 b21. None of the never-bits (d0 b0 / b1 / b10 / b14 / b28, d1 b4 / b5 / b10 / b11 / b12 / b17 / b24,
d2 b2 / b11 / b31) is used. EquippedItemClass -1 on every row (L1); every potency row sets SpellLevel (the generator
owns BaseLevel / MaxLevel); helpers triggered at another unit have range_yards=50000.0 (L6).
"""

from lib.dsl import AuraType, Effect, EffectType, School
from lib.dsl.registry import (
    const, pot_text, product, scripted_by, skill_line_ability, spell, talent_mult, tooltip_vars, trained_by,
)

from . import _masks as m
from .shaman_restoration import torrent_heal_202667
from .shaman_resto_tooltips import shaman_rain_1222

_SPELLFAMILY_SHAMAN = 11
_DMG_MAGIC = 1                              # raw DefenseType (SPELL_DAMAGE_CLASS_MAGIC)
_ATTR3_SUPPRESS_CASTER_PROCS = 0x10000      # H8: the Earthquake tick rolls no caster procs (Blizzard precedent)
_ATTR5_NO_CASTER_AURA_ICON = 0x08000000     # the shaman's own eff1 aura shows no icon
_TARGETS_DEST_LOCATION = 0x40               # raw Targets: ground cursor
_INTERRUPT_CAST = 15                        # InterruptFlags of a normal cast (movement, pushback, interrupt)

_TARGET_UNIT_CASTER = 1
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_UNIT_TARGET_ALLY = 21
_TARGET_DEST_DYNOBJ_ENEMY = 28              # Rain of Fire 5740's eff0 target
_TARGET_DEST_DYNOBJ_ALLY = 29               # Power Word: Barrier / P0 Healing Rain: an ally-side dynobj aura cannot pull

_TRAINER_SHAMAN = 210
_SKILL_LINE_ELEMENTAL = 375
_SKILL_LINE_RESTORATION = 374
_CLASS_MASK_SHAMAN = 64

# Stock SpellIconIDs (apps/dbc-tools/var/model-visual-dbc SpellIcon.dbc). Final art is the V stage.
_ICON_EARTHQUAKE = 66                       # Spell_Nature_Earthquake (stock Earthquake 41966)
_ICON_ELEMENTAL_BLAST = 1930                # Spell_Fire_ElementalDevastation (placeholder; no WotLK Elemental Blast icon)
_ICON_HEALING_RAIN = 2011                   # Spell_Nature_GiftoftheWaterSpirit (placeholder)

# SpellVisual ids. 10405 is stock Earthquake's (PersistentAreaKit 9287, "Earth Burrow Cast (Scale x5)": scaling it
# down is the V stage); 11565 is Lava Burst's (missile + impact, "Lava Burst missile with a lightning impact" is a
# V-stage clone); 90130 is the ported Ascension Healing Rain ring (patch_shaman_vfx_models.py, pending SQL
# rev_1792395354330090836.sql).
_SV_EARTHQUAKE = 10405
_SV_ELEMENTAL_BLAST = 11565
_SV_HEALING_RAIN_RING = 90130

# tooltip_vars 1213 / 1214 (S1a A4; S1-NOTES section 5): Elemental-tree, unconditional % talents only, bare rank ids.
# Earthquake's tick number (shown on the ground cast through pot_text): Concussion eff B and Convection eff B. Elemental
# Blast: Concussion eff B, Booming Echoes (shock + EB damage), Fusion of Elements (EB damage, eff A; ranks 202529 / 202530).
shaman_quake_1213 = tooltip_vars(
    1213, "Earthquake tick: Concussion (eff B), Convection (eff B)",
    cnc=talent_mult([16035, 16105, 16106], effect=2),
    cnv=talent_mult([16039, 16109, 16110], effect=2),
    mult=product('cnc', 'cnv'),
)
shaman_blast_1214 = tooltip_vars(
    1214, "Elemental Blast: Concussion (eff B), Booming Echoes, Fusion of Elements",
    cnc=talent_mult([16035, 16105, 16106], effect=2),
    bme=talent_mult([63370, 63372, 202535], effect=1),
    fus=talent_mult([202529, 202530], effect=1),
    mult=product('cnc', 'bme', 'fus'),
)

HEALING_RAIN_TARGETS = const(
    'HEALING_RAIN_TARGETS', 5, 'Allies Healing Rain heals per pulse, most injured first, players only [fixed].',
    cpp_type='uint8',
)

# =====================================================================================================================
# Earthquake (shared doc "Earthquake"): trained at 38, Nature, ground, 1.5 s cast, 30 s cooldown, 10% base mana,
# 8 yd radius, 35 yd range, 6 ticks of 50 potency to every enemy inside. Haste never adds ticks.
# =====================================================================================================================

# The per-target tick (T0b section 8, B27 trigger shape): a direct SCHOOL_DAMAGE Nature hit cast by the shaman at one
# enemy by spell_sha_earthquake each second, so it crits and takes Nature / Versatility / % mods live, and being a
# single-target cast it gets no AoE reduction or 10-target split. 50 potency, T 1000 ("about 89 at 60"). H8:
# AttributesEx3 SUPPRESS_CASTER_PROCS so the tick triggers nothing that needs a direct hit ("ticks are periodic
# damage"; Elemental Devastation / Precision capstone / Elemental Focus / Raw Power). Both rows carry d2 b19 so
# Concussion / Convection / Earth Empowerment read the tick's flags and cost / cooldown mods read the cast's.
earthquake_tick_202281 = spell(
    id=202281, name='Earthquake', school=School.NATURE, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=21.5, potency_kind='direct', time_basis_ms=1000,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_EARTHQUAKE,
    notes='SH0b A5, shared doc "Earthquake": the per-target tick, never player-cast (no SkillLineAbility, no trainer). '
          'Nature SCHOOL_DAMAGE, sp_potency 21.5 direct (was 50; x0.43 smoke-test fix pass 2026-10-20), T 1000, SpellLevel 38, d2 b19. AttributesEx3 0x10000 '
          '(SUPPRESS_CASTER_PROCS, H8: the tick rolls no caster procs; the mask exclusions per talent are the Elemental '
          'stage\'s to revisit). range_yards 50000 (L6: the shaman casts it at enemies up to 35 yd + 8 yd away). '
          'AttributesEx2 0x4 (ignore LoS) IS set (orchestrator, after B3): spell_sha_earthquake filters LoS from the zone '
          'itself, so the engine\'s caster-to-target check must not skip enemies the shaman cannot see.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_SHAMAN, 'SpellClassMask_3': m.EARTHQUAKE, 'DefenseType': _DMG_MAGIC,
        'EquippedItemClass': -1, 'SpellLevel': 38, 'CastingTimeIndex': 1,
        'AttributesEx2': 0x4, 'AttributesEx3': _ATTR3_SUPPRESS_CASTER_PROCS,
        'Description_Lang_enUS': 'Deals {pot1} Nature damage.',
    },
)

# The ground cast. eff0 targets as Rain of Fire 5740 (28, TARGET_DEST_DYNOBJ_ENEMY) with none of its attributes; radius
# 8 yd; no potency on it (the tick carries it). Visual 10405 is the stock Earthquake kit as is.
earthquake_202280 = spell(
    id=202280, name='Earthquake', school=School.NATURE, attributes=0,
    cast_time_ms=1500, cooldown_ms=30000, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=10,
    range_yards=35.0, duration_ms=6000,
    effects=[
        Effect(type=EffectType.PERSISTENT_AREA_AURA, apply_aura=AuraType.DUMMY,
               implicit_target_a=_TARGET_DEST_DYNOBJ_ENEMY, radius_yards=8.0),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=1000,
               implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_EARTHQUAKE,
    notes='SH0b A5, shared doc "Earthquake" + T0b section 4: Nature, 1.5 s cast, RecoveryTime 30000 (Cooldown Haste '
          'applies, >= 30 s), 10% base mana, GCD 1500 / 133, 35 yd, 6 s. eff0 PERSISTENT_AREA_AURA dummy, target 28 '
          '(Rain of Fire 5740\'s), radius 8 yd, raw Targets 0x40 (ground cursor); eff1 PERIODIC_DUMMY 1000 ms on the '
          'caster (6 ticks, not hasted: no AttributesEx5 0x2000 / 0x200, no periodic damage aura). AttributesEx5 '
          '0x08000000 hides the caster aura; Attributes stays 0 (0x80 hid the P0 spike from the spellbook). d2 b19, '
          'SpellLevel 38. SpellVisualID 10405 = stock Earthquake\'s kit as is (100 yd scale x5, V stage scales it '
          'down). spell_sha_earthquake (AuraScript, eff1) casts the tick 202281 at every attackable enemy inside the '
          'dynobj with LoS (H7). Rows carry no AuraDescription number; the aura sits on enemies inside the area as a '
          'dummy debuff.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_SHAMAN, 'SpellClassMask_3': m.EARTHQUAKE, 'DefenseType': _DMG_MAGIC,
        'PreventionType': 1, 'EquippedItemClass': -1, 'SpellLevel': 38,
        'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'InterruptFlags': _INTERRUPT_CAST,
        'Targets': _TARGETS_DEST_LOCATION, 'AttributesEx5': _ATTR5_NO_CASTER_AURA_ICON,
        'SpellVisualID_1': _SV_EARTHQUAKE,
        'Description_Lang_enUS': 'Causes the earth to shake beneath the target area, dealing '
                                 + pot_text(earthquake_tick_202281, var='mult')
                                 + ' Nature damage every $t2 sec for $d to all enemies inside it. 30 sec cooldown.',
        'AuraDescription_Lang_enUS': 'Shaken by an earthquake.',
    },
    tooltip_vars=shaman_quake_1213,
)
scripted_by(earthquake_202280, 'spell_sha_earthquake')

# =====================================================================================================================
# Elemental Blast (shared doc "Elemental Blast"): trained at 50, instant, Fire + Frost + Nature in one hit.
# =====================================================================================================================
elemental_blast_202282 = spell(
    id=202282, name='Elemental Blast', school=School.FIRE | School.FROST | School.NATURE, attributes=0,
    cast_time_ms=0, cooldown_ms=12000, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=6, range_yards=40.0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, sp_potency=43.0, potency_kind='direct', time_basis_ms=1500,
                    implicit_target_a=_TARGET_UNIT_TARGET_ENEMY)],
    spell_icon_id=_ICON_ELEMENTAL_BLAST,
    notes='SH0b A5, shared doc "Elemental Blast": instant, SchoolMask 0x1C (Fire 4 + Frost 16 + Nature 8: counts as '
          'all three for every school bonus), sp_potency 43 direct (was 100; x0.43 smoke-test fix pass 2026-10-20), T 1500, RecoveryTime 12000 (not Cooldown Haste: '
          '< 30 s), 40 yd, 6% base mana (was 8%; user playtest fix pass 2026-10-22, P1), GCD 1500 / 133 (an explicit spell-GCD like Lava Burst, brief decision 4), '
          'd2 b20 (no d0 b0 / b1, d1 b12). Speed 24 and SpellVisualID 11565 = Lava Burst\'s missile and impact (a '
          'lightning-impact clone of 11565 in the 90131+ block is the V stage). SpellLevel 50. Icon 1930 is a '
          'placeholder (the 3.3.5 client has no Elemental Blast icon).',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_SHAMAN, 'SpellClassMask_3': m.ELEMENTAL_BLAST, 'DefenseType': _DMG_MAGIC,
        'PreventionType': 1, 'EquippedItemClass': -1, 'SpellLevel': 50, 'CastingTimeIndex': 1,
        'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'Speed': 24.0,
        'SpellVisualID_1': _SV_ELEMENTAL_BLAST,
        'Description_Lang_enUS': 'Harnesses the raw power of the elements, dealing {pot1*mult} Fire, Frost and Nature '
                                 'damage to the target. 12 sec cooldown.',
    },
    tooltip_vars=shaman_blast_1214,
)

# =====================================================================================================================
# Healing Rain (shared doc "Healing Rain"): trained at 30, Nature, ground, 2 s cast, no cooldown, 20 s, radius 10 yd,
# up to 5 most injured allies per 2 s pulse (10 pulses). Shape and values of the P0 spike 202775 / 202776.
# =====================================================================================================================

# The per-target pulse heal: cast live by the shaman each pulse at the 5 most injured players inside the rain
# (Heal::SelectMostInjured, players only), 5 potency, T 2000. Triggered, so it rolls none of the shaman's procs.
healing_rain_heal_202284 = spell(
    id=202284, name='Healing Rain', school=School.NATURE, attributes=0,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=50000.0,
    effects=[Effect(type=EffectType.HEAL, sp_potency=5.0, potency_kind='heal', time_basis_ms=2000,
                    implicit_target_a=_TARGET_UNIT_TARGET_ALLY)],
    spell_icon_id=_ICON_HEALING_RAIN,
    notes='SH0b A5, shared doc "Healing Rain": the per-target pulse heal, never player-cast (no SkillLineAbility, no '
          'trainer). Nature HEAL on TARGET_UNIT_TARGET_ALLY, sp_potency 5 heal, T 2000, SpellLevel 30, d2 b21 '
          '(Ancestral Awakening / Healing Way hook here later). range_yards 50000 (= RangeIndex 13 as the P0 202776; '
          'L6). The Healing Rain script reads it live each pulse. AttributesEx2 0x4 is set (see 202281): the script picks targets from the ring.',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_SHAMAN, 'SpellClassMask_3': m.HEALING_RAIN, 'DefenseType': _DMG_MAGIC,
        'EquippedItemClass': -1, 'SpellLevel': 30, 'CastingTimeIndex': 1, 'AttributesEx2': 0x4,
        'Description_Lang_enUS': 'Heals the target for {pot1}.',
    },
)

# The ground cast: P0 202775 (passed) with the values of the doc. eff0 targets 29 / 29 (ally-side dynobj, Barrier
# 200132's shape: an ally dynobj aura cannot pull enemies into combat), radius 10; eff1 PERIODIC_DUMMY 2000 ms;
# the torrent is its own spell (shaman_restoration.py, d2 b22); the old eff2 potency-carrier DUMMY is gone (S2a A4).
healing_rain_202283 = spell(
    id=202283, name='Healing Rain', school=School.NATURE, attributes=0,
    cast_time_ms=2000, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=20,
    range_yards=30.0, duration_ms=20000,
    effects=[
        Effect(type=EffectType.PERSISTENT_AREA_AURA, apply_aura=AuraType.DUMMY,
               implicit_target_a=_TARGET_DEST_DYNOBJ_ALLY, implicit_target_b=_TARGET_DEST_DYNOBJ_ALLY,
               radius_yards=10.0),
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=2000,
               implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_HEALING_RAIN,
    tooltip_vars=shaman_rain_1222,
    notes='SH0b A5, shared doc "Healing Rain" + T0b section 4 + P0 202775 (PASS): Nature, 2 s cast, no cooldown, 20 s, '
          '30 yd, GCD 1500 / 133, cost 20% base mana [tune] (Chain Heal 19%, Riptide 18%; balance pass), d2 b21, '
          'SpellLevel 30. eff0 PERSISTENT_AREA_AURA dummy, targets 29 / 29 + raw Targets 0x40, radius 10 yd; eff1 '
          'PERIODIC_DUMMY 2000 ms on the caster (10 pulses, not hasted: no AttributesEx5 0x2000 / 0x200). '
          'AttributesEx5 0x08000000 hides the caster aura; Attributes stays 0 (0x80 hid the spike from the spellbook). '
          'InterruptFlags 15. SpellVisualID 90130 = the ported Ascension ring (patch_shaman_vfx_models.py, pending '
          'rev_1792395354330090836.sql). spell_sha_healing_rain removes the old rain and its aura before the cast; '
          'its aura script heals SelectMostInjured(owner, dynobj, radius, HEALING_RAIN_TARGETS) with 202284. '
          'S2a A4 (Restoration): the placeholder eff2 (a 10-potency DUMMY that only carried the torrent\'s tooltip number) is '
          'deleted; the tooltip now reads the real torrent heal 202667 (d2 b22, 10 potency) through pot_text(), with the Healing '
          'Way / Torrent / Purification product (tooltip entry 1222 `tide`), and the pulse number with the Healing Way / Rainfall / '
          'Purification product (`rain`).',
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_SHAMAN, 'SpellClassMask_3': m.HEALING_RAIN, 'DefenseType': _DMG_MAGIC,
        'PreventionType': 1, 'EquippedItemClass': -1, 'SpellLevel': 30,
        'StartRecoveryCategory': 133, 'StartRecoveryTime': 1500, 'InterruptFlags': _INTERRUPT_CAST,
        'Targets': _TARGETS_DEST_LOCATION, 'AttributesEx5': _ATTR5_NO_CASTER_AURA_ICON,
        'SpellVisualID_1': _SV_HEALING_RAIN_RING,
        'Description_Lang_enUS': 'Calls down a healing rain on the target area for $d, healing up to 5 allies inside '
                                 'it for ' + pot_text(healing_rain_heal_202284, var='rain') + ' every $t2 sec. Casting Riptide on '
                                 'an ally in your Healing Rain releases a torrent that heals up to 5 allies in it for '
                                 + pot_text(torrent_heal_202667, var='tide') + '. Only one Healing Rain can be active at a time.',
        'AuraDescription_Lang_enUS': 'Standing in a healing rain.',
    },
)
scripted_by(healing_rain_202283, 'spell_sha_healing_rain')

# ---- Trainer 210 (priced by the learn-level curve) and spellbook entries (class mask 64, acquire 0) ----
trained_by(earthquake_202280, _TRAINER_SHAMAN, 38)
trained_by(elemental_blast_202282, _TRAINER_SHAMAN, 50)
trained_by(healing_rain_202283, _TRAINER_SHAMAN, 30)

skill_line_ability(id=30666, skill_line=_SKILL_LINE_ELEMENTAL, spell_id=earthquake_202280.id,
                   class_mask=_CLASS_MASK_SHAMAN, acquire_method=0)
skill_line_ability(id=30667, skill_line=_SKILL_LINE_ELEMENTAL, spell_id=elemental_blast_202282.id,
                   class_mask=_CLASS_MASK_SHAMAN, acquire_method=0)
skill_line_ability(id=30668, skill_line=_SKILL_LINE_RESTORATION, spell_id=healing_rain_202283.id,
                   class_mask=_CLASS_MASK_SHAMAN, acquire_method=0)
