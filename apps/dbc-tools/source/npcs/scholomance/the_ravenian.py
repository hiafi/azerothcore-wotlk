"""
Scholomance build WP-S8: The Ravenian (10507) and Master Corvane (300542), normal and heroic
(.agents/plans/scholomance-build/scholomance-build.HANDOFF.md s3.4 rows RV, s3.5 row S8, s3.6; build spec
docs/dungeons/scholomance-rework.md SC 2193-2259, design SC 2052-2192; the user ruling of 2026-11-08 on Corvane's seat).
WP-S8 owns this file (its spells: kSpellsRavenian 206270-206289 of modules/mod-dungeon-bosses
src/Scholomance/ScholomanceRework.h only; RavenianLogic.h names the same ids; its creature: Master Corvane 300542).

- 10507 The Ravenian: boss_the_ravenian_rework (src/Scholomance/boss_the_ravenian_rework.cpp), SmartAI off (the WP-S8
  SQL rev drops the five stock rows and adds the texts), the build spec's normal health (160k: HealthModifier 52.425 on
  the level 60 warrior base 3,052), DamageModifier 3.5 (the AzerothCore base value; the live 7 is the retired
  mod-progression's leftover, handoff s2.3), stun immunity 1972, INSTANCE_BIND. Heroic 210k is WP-H's override
  (source/world/dungeons/scholomance.py).
- 300542 Master Corvane (new, SC "Encounter"): class mage (base 2,136 x 23.4082 = 50,000; heroic 65,000 is WP-H's
  `_KIT_ADD_HEROIC`, and his row names its heroic entry, difficulty_entry_1 310118, STAGE-H report s4), the Necromancer
  model 23277 (WP-V DISPLAY_CORVANE), stun immune (1972, handoff s7 #9: silence and interrupts work), elite, humanoid,
  no loot. Not selectable and not attackable as he spawns (unit_flags 0x02000002): the Ravenian's script seats him
  behind the Ravenian (the user's spot kRavenianUserSpot) and makes him attackable at the 50% transition.
  npc_sc_master_corvane only reports his casts and death to the Ravenian's script (and fights on alone while the
  Ravenian lies collapsed at 1 HP: user ruling 1, 2026-11-08). He never melees (passive, rooted on the floor).
- The two Graduate Examiners (S13, 300551 / 300552) run the same C++ in examiner mode (npc_sc_examiner_ravenian,
  npc_sc_examiner_corvane: 60k / 20k by script); WP-S13 declares the entries. The detention lesson (the Vault of the
  Ravenian) is C++ too and uses 206271-206276; its echo 300545 is WP-S11's entry.

Spells (Spell.dbc 3.3.5 for every stock id quoted; looks from WP-V's ._visuals and the stock order moves, all stock):

  206270  Leash                the beam: Corvane's channel on the Ravenian (DUMMY aura), his other casts go on
                               (SPELL_ATTR5_ALLOW_ACTION_DURING_CHANNEL); Shadow Channeling 43897's SV 9843
  206271  Order: Trample       RV1 Corvane's 2 s order (kickable; he is unselectable in phase 1, so only phase 2 counts)
  206272  Order: Sweep         RV2
  206273  Order: Smash         RV3
  206274  Trample              RV1 the line's hit: resolve copy (Physical), stock Trample 15550's SV 672
  206275  Sweep                RV2 the frontal's hit: resolve copy (Physical), Sundering Cleave 25174's SV 219
  206276  Smash                RV3 the ring's hit: resolve copy (Physical), Knock Away 10101's SV 2069
  206277  Mend Construct       RV5 the 50% heal from the seat: 2 s, cannot be stopped (no interrupt flags), 10% / 15%
  206278  Mend Construct       RV8 the phase 2 heal: 3 s, kickable (the must-kick), 6% / 10%
  206279  Teleport             RV5 the teleport's look on Corvane (Teleport Visual 41236's SV 9343)
  206280  Unbound              RV6 the kicked move on Corvane: 8% of his health (spell_scholo_ravenian_unbound_strike)
  206281  Unbound              RV6 the Ravenian's 2 s stand: the leash snapped (Chains of Kel'Thuzad 28410's SV 7597)
  206282  Driven               RV7 heroic: +10% damage done a stack, for the fight, uncapped (ruling 24)
  206283  Shadow Bolt          RV9 Corvane's filler, 2.5 s, 15% / 20% (spell_scholo_corvane_shadow_bolt)
  206284  Bereaved             RV10 the survivor: +10% damage done a stack, every 5 s, uncapped (Unholy Frenzy's SV 47)
  206285  Sundering Cleave     RV11 stock 25174 on one target (stock: 3)
  206286-206289 spare.

Stock Cleave 20691, Knock Away 10101 and Trample 15550 are retired from his kit.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR1_NO_THREAT,
    ATTR2_CANT_CRIT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    TARGET_UNIT_TARGET_ENEMY,
    self_visual,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    BIND_WAVE_B,
    IMMUNITY_BOSS_STUN,
    KIT_CREATURE,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_CORVANE,
    RV_BEREAVED,
    RV_LEASH_BEAM,
    RV_LEASH_BEAM_ALT,
    RV_MEND_CONSTRUCT,
    RV_TELEPORT_DOWN,
)

# Held back until wave B binds this boss (_common.py BIND_WAVE_B; R-A S-11): stock until then.
if BIND_WAVE_B:
    creature_template_columns(10507, **boss_columns('boss_the_ravenian_rework', 52.425, DamageModifier=3.5))

_RV = 'Scholomance build WP-S8 (The Ravenian and Master Corvane)'
_SCRIPT_EXCLUDED = 'Scholomance: a percent of reference health, set by the script (DungeonKit::RefFlat)'
_SCRIPT_HEAL = "Scholomance: a percent of the Ravenian's health, set by spell_scholo_ravenian_mend"

_TARGET_UNIT_TARGET_ALLY = 21
_ATTR0_IS_ABILITY = 0x00000010
_ATTR1_IS_CHANNELED = 0x00000004
_ATTR5_ALLOW_ACTION_DURING_CHANNEL = 0x00000001
_INTERRUPT_FLAGS_STANDARD = 15     # movement, pushback, interrupt, auto-attack: a kickable cast
_PREVENTION_SILENCE = 1
_PREVENTION_PACIFY = 2
_DEFENSE_MAGIC = 1
_DEFENSE_MELEE = 2
_SCHOOL_MASK_ALL = 127
_AURA_MOD_RESISTANCE = 22
_RESISTANCE_ARMOR = 1              # SpellSchoolMask normal: the armor resistance

# Stock order moves (Spell.dbc 3.3.5): the looks of his retired kit become the orders' hits.
_SV_TRAMPLE = 672                  # Trample 15550
_SV_SUNDERING_CLEAVE = 219         # Sundering Cleave 25174 (and Cleave 20691)
_SV_KNOCK_AWAY = 2069              # Knock Away 10101
_SV_SHADOW_BOLT = 64               # Shadow Bolt 686 (the bolt and its missile)
_ICON_TRAMPLE = 168
_ICON_SUNDERING_CLEAVE = 565
_ICON_KNOCK_AWAY = 314
_ICON_SHADOW_BOLT = 213
_ICON_DARK_MENDING = 55            # Dark Mending 16588
_ICON_SHADOW_CHANNELING = 207      # Shadow Channeling 43897
_ICON_TELEPORT = 1                 # Teleport Visual 41236
_ICON_CHAINS = 1540                # Chains of Kel'Thuzad 28410
_ICON_UNHOLY_FRENZY = 38           # Unholy Frenzy 8699

_ORDER_CAST_MS = 2000              # RavenianLogic.h kOrderCastMs
_TRANSITION_CAST_MS = 2000         # kTransitionCastMs
_MEND_CAST_MS = 3000               # kMendCastMs
_SHADOW_BOLT_CAST_MS = 2500        # kShadowBoltCastMs
_UNBOUND_STAND_MS = 2000           # kUnboundStandMs
_LEASH_MS = 300000                 # the channel's length: the script casts it again whenever it is down

# --- 300542 Master Corvane -------------------------------------------------------------------------------------------

# Level 60 elite humanoid mage, base 2,136: ceil(2,136 x 23.4082) = 50,000.
master_corvane_300542 = creature_template(
    300542, 'Master Corvane', **{
        **KIT_CREATURE, 'subname': 'Professor of Necromancy', 'minlevel': 60, 'maxlevel': 60, 'rank': 1, 'type': 7,
        'unit_class': 8, 'unit_flags': 0x02000000 | 0x2, 'HealthModifier': 23.4082, 'ManaModifier': 1.0,
        'DamageModifier': 1.0, 'BaseAttackTime': 2000, 'ExperienceModifier': 1.0, 'speed_walk': 1.0,
        'CreatureImmunitiesId': IMMUNITY_BOSS_STUN, 'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0,
        'maxgold': 0, 'ScriptName': 'npc_sc_master_corvane', 'difficulty_entry_1': 310118,
    },
)
creature_model(300542, display_id=DISPLAY_CORVANE)

# --- The leash -------------------------------------------------------------------------------------------------------

leash_206270 = spell(
    id=206270, name='Leash', school=School.SHADOW, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=_LEASH_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_SHADOW_CHANNELING,
    notes=f'{_RV}: the leash beam (SC "Theme" pitch A): Corvane\'s channel from his hands to the Ravenian\'s back, '
          'cast (triggered) on the Ravenian from his seat, again after the teleport and after the Unbound snap '
          '(RavenianFight KeepLeash, every second while it is down). SPELL_ATTR5_ALLOW_ACTION_DURING_CHANNEL: his '
          'orders, Mend Construct and bolts do not break it; no interrupt or channel-interrupt flags (a kick never '
          'cuts it: ruling round 3, the leash breaks on interrupts of the orders only). A DUMMY aura on the Ravenian, '
          'no threat. Shadow Channeling 43897\'s SV 9843 (RitualSummoning precast and shadow hands; WP-V: no beam '
          'model, the line between them is checked in game; alternative RV_LEASH_BEAM_ALT 7597).',
    raw_overrides=kit_raw("Master Corvane's leash.", 'Held by Master Corvane.', CastingTimeIndex=1,
                          SpellVisualID_1=RV_LEASH_BEAM, InterruptFlags=0, ChannelInterruptFlags=0,
                          AuraInterruptFlags=0, AttributesEx=_ATTR1_IS_CHANNELED | ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AttributesEx5=_ATTR5_ALLOW_ACTION_DURING_CHANNEL),
)

# --- RV1-RV3 the orders ----------------------------------------------------------------------------------------------


def _order(spell_id: int, move: str, icon: int, what: str):
    """Corvane's 2 s order (SC RV1-RV4): a named cast bar he casts on himself as he yells the move (lines 1-3). In
    phase 2 it is kickable (InterruptFlags 15, PreventionType silence; the descriptor's interrupt list, priority 2):
    kicked, the Ravenian does the move on Corvane (Unbound); finished, the Ravenian does it on the group (on heroic
    with a Driven stack). In phase 1 he is unselectable, so nothing stops it. The detention echo casts the same bars."""
    return spell(
        id=spell_id, name=f'Order: {move}', school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=_ORDER_CAST_MS,
        cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
        effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon,
        notes=f'{_RV}, {what}: Corvane\'s 2 s order, a cast bar on himself with no effect (the AI acts on the cast\'s '
              'end: OnSpellCast performs the move, OnSpellFailed in phase 2 is Unbound). Kickable: InterruptFlags 15, '
              'PreventionType silence (stun immunity 1972 leaves silences and kicks working).',
        raw_overrides=kit_raw(f'Orders the Ravenian to {move.lower()}.', InterruptFlags=_INTERRUPT_FLAGS_STANDARD,
                              PreventionType=_PREVENTION_SILENCE, DefenseType=_DEFENSE_MAGIC,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


order_trample_206271 = _order(206271, 'Trample', _ICON_TRAMPLE, 'RV1')
order_sweep_206272 = _order(206272, 'Sweep', _ICON_SUNDERING_CLEAVE, 'RV2')
order_smash_206273 = _order(206273, 'Smash', _ICON_KNOCK_AWAY, 'RV3')

trample_206274 = resolve_copy(
    206274, 'Trample', School.NORMAL, 'The Ravenian tramples through.',
    f'{_RV}, RV1: the Trample line\'s hit: 4 yd wide, from the Ravenian through a random non-tank player to the '
    'vault\'s wall (RavenianLogic.h VaultWalls), a 2 s marker after the order: 35% normal / 50% heroic of the '
    'non-tank row, times his Driven and Bereaved factor (no penalty, SC RV1). The solo lesson uses it at 15% / 25% '
    'and Weakened. Copy of the resolve spell 205000 (Physical). His stock Trample 15550\'s SV 672 on whoever is hit.',
    icon=_ICON_TRAMPLE, visual=_SV_TRAMPLE,
)

sweep_206275 = resolve_copy(
    206275, 'Sweep', School.NORMAL, 'The Ravenian sweeps in front of him.',
    f'{_RV}, RV2: the Sweep frontal\'s hit: 120 degrees, 12 yd, toward his tank (a Frontal: the tank is exempt), a 2 s '
    'marker after the order: 45% normal / 60% heroic, times his Driven and Bereaved factor. The solo lesson\'s Sweep '
    '(a fixed cone from the echo\'s spot) uses it at 15% / 25% and Weakened. Copy of the resolve spell 205000 '
    '(Physical). Sundering Cleave 25174\'s SV 219 on whoever is hit.',
    icon=_ICON_SUNDERING_CLEAVE, visual=_SV_SUNDERING_CLEAVE,
)

smash_206276 = resolve_copy(
    206276, 'Smash', School.NORMAL, 'The Ravenian smashes the ground.',
    f'{_RV}, RV3: the Smash ring\'s hit: 6 yd on a random non-tank player, a 2 s marker after the order: 30% normal / '
    '40% heroic plus Weakened (ruling 21, both difficulties), times his Driven and Bereaved factor. The solo lesson '
    'uses it at 15% / 25%. Copy of the resolve spell 205000 (Physical). Knock Away 10101\'s SV 2069 on whoever is hit.',
    icon=_ICON_KNOCK_AWAY, visual=_SV_KNOCK_AWAY,
)

# --- RV5 / RV8 Mend Construct ----------------------------------------------------------------------------------------


def _mend(spell_id: int, cast_ms: int, kickable: bool, what: str):
    raw = kit_raw('Mends the Ravenian.', SpellVisualID_1=RV_MEND_CONSTRUCT, AttributesEx=ATTR1_NO_THREAT,
                  AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT | ATTR2_CANT_CRIT,
                  AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS)
    if kickable:
        raw.update(InterruptFlags=_INTERRUPT_FLAGS_STANDARD, PreventionType=_PREVENTION_SILENCE,
                   DefenseType=_DEFENSE_MAGIC)
    else:
        raw.update(InterruptFlags=0, PreventionType=0)
    s = spell(
        id=spell_id, name='Mend Construct', school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=cast_ms,
        cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.HEAL, implicit_target_a=_TARGET_UNIT_TARGET_ALLY,
                        potency_excluded=_SCRIPT_HEAL)],
        spell_icon_id=_ICON_DARK_MENDING, notes=f'{_RV}, {what} Dark Mending 16588\'s SV 27.', raw_overrides=raw,
    )
    scripted_by(s, 'spell_scholo_ravenian_mend')
    return s


mend_transition_206277 = _mend(
    206277, _TRANSITION_CAST_MS, False,
    'RV5: the transition\'s Mend Construct at 50%: Corvane casts it on the Ravenian from his seat (2 s; out of reach '
    'and with no interrupt flags: it always lands), heals 10% normal / 15% heroic of the Ravenian\'s max health '
    '(spell_scholo_ravenian_mend sets it at launch; ignores caster modifiers, cannot crit); then he teleports down.')
mend_206278 = _mend(
    206278, _MEND_CAST_MS, True,
    'RV8: phase 2\'s Mend Construct, 10 s after he lands, then every 20 s: a 3 s kickable cast (InterruptFlags 15, '
    'PreventionType silence; the descriptor\'s interrupt list, priority 3, the must-kick): heals 6% normal / 10% '
    'heroic of the Ravenian\'s max health. Capped by Corvane\'s death.')

teleport_206279 = self_visual(
    206279, 'Teleport', RV_TELEPORT_DOWN,
    f'{_RV}, RV5: Corvane\'s teleport down from his seat to his landing: cast on himself (triggered) before and after '
    'the move. Teleport Visual 41236\'s SV 9343. Look only.',
    icon=_ICON_TELEPORT,
)

# --- RV6 Unbound -----------------------------------------------------------------------------------------------------

unbound_strike_206280 = spell(
    id=206280, name='Unbound', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_KNOCK_AWAY,
    notes=f'{_RV}, RV6: a kicked order in phase 2: the Ravenian, unbound for a moment, does the move on his maker. '
          'Cast (triggered) by the Ravenian on Corvane; spell_scholo_ravenian_unbound_strike deals exactly 8% of '
          'Corvane\'s max health itself (a DUMMY, so his armor does not cut it) and logs it. The reward for the kick. '
          'Knock Away 10101\'s SV 2069 on Corvane.',
    raw_overrides=kit_raw('The construct turns on its maker.', instant=True, SpellVisualID_1=_SV_KNOCK_AWAY,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx3=ATTR3_ALWAYS_HIT, AttributesEx4=ATTR4_NO_CAST_LOG),
)
scripted_by(unbound_strike_206280, 'spell_scholo_ravenian_unbound_strike')

unbound_206281 = spell(
    id=206281, name='Unbound', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
    duration_ms=_UNBOUND_STAND_MS,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=TARGET_UNIT_CASTER)],
    spell_icon_id=_ICON_CHAINS,
    notes=f'{_RV}, RV6: the Ravenian\'s 2 s stand after the Unbound strike (the leash snapping): the tell only; the AI '
          'roots him and holds his swings for the same 2 s, and Corvane\'s beam drops and comes back. Chains of '
          'Kel\'Thuzad 28410\'s SV 7597 (the enslave state on him).',
    raw_overrides=kit_raw('The leash snaps.', 'The leash snapped.', instant=True, SpellVisualID_1=RV_LEASH_BEAM_ALT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- RV7 Driven / RV10 Bereaved --------------------------------------------------------------------------------------


def _damage_stacks(spell_id: int, name: str, icon: int, visual: int, desc: str, notes: str):
    raw = kit_raw(desc, 'Damage done increased by $s1% per application.', instant=True, CumulativeAura=255,
                  AttributesEx4=ATTR4_NO_CAST_LOG)
    if visual:
        raw['SpellVisualID_1'] = visual
    return spell(
        id=spell_id, name=name, school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_NO_IMMUNITIES,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF,
        duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=10,
                        die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER)],
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


driven_206282 = _damage_stacks(
    206282, 'Driven', _ICON_TRAMPLE, 0, 'Every order obeyed drives the construct harder.',
    f'{_RV}, RV7 (heroic): an order nobody kicks in phase 2 gives the Ravenian a stack for the fight: +10% damage done '
    'a stack (the engine multiplies by the stacks), uncapped (ruling 24; CumulativeAura 255, the aura\'s stack limit). '
    'His orders ignore caster modifiers, so the AI scales them by the same factor (RavenianLogic.h DamageScale). '
    'Dispel none (no purge in the build spec). No look: the stack count is the tell.')

bereaved_206284 = _damage_stacks(
    206284, 'Bereaved', _ICON_UNHOLY_FRENZY, RV_BEREAVED, 'Grief turns to fury.',
    f'{_RV}, RV10: the survivor when one of the two falls first (Corvane dies, or the Ravenian collapses): a stack '
    'every 5 s, +10% damage done a stack, uncapped (CumulativeAura 255). Corvane\'s bolt and the Ravenian\'s orders '
    'are scaled by the script by the same factor (Driven x Bereaved, multiplied as the engine does on his melee). '
    'Unholy Frenzy 8699\'s SV 47 (BloodLust_State_Hand).')

# --- RV9 Shadow Bolt -------------------------------------------------------------------------------------------------

shadow_bolt_206283 = spell(
    id=206283, name='Shadow Bolt', school=School.SHADOW, dispel=0, mechanic=0, cast_time_ms=_SHADOW_BOLT_CAST_MS,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=40.0, duration_ms=0,
    effects=[Effect(type=EffectType.SCHOOL_DAMAGE, implicit_target_a=TARGET_UNIT_TARGET_ENEMY,
                    potency_excluded=_SCRIPT_EXCLUDED)],
    spell_icon_id=_ICON_SHADOW_BOLT,
    notes=f'{_RV}, RV9: Corvane\'s filler between orders and heals (phase 2, and alone): a 2.5 s cast at a random '
          'player in 40 yd: 15% normal / 20% heroic of the reference row, times his Bereaved factor '
          '(spell_scholo_corvane_shadow_bolt, RefFlatOn at launch, so defensives count). Kickable like any cast, but '
          'not on the interrupt list. Ignores caster modifiers, cannot crit. Shadow Bolt 686\'s SV 64 (the bolt '
          'missile, speed 20).',
    raw_overrides=kit_raw('Hurls a bolt of shadow.', InterruptFlags=_INTERRUPT_FLAGS_STANDARD,
                          PreventionType=_PREVENTION_SILENCE, DefenseType=_DEFENSE_MAGIC,
                          SpellVisualID_1=_SV_SHADOW_BOLT, Speed=20.0, AttributesEx2=ATTR2_CANT_CRIT,
                          AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS),
)
scripted_by(shadow_bolt_206283, 'spell_scholo_corvane_shadow_bolt')

# --- RV11 Sundering Cleave (stock 25174 on one target) ---------------------------------------------------------------

sundering_cleave_206285 = spell(
    id=206285, name='Sundering Cleave', school=School.NORMAL, dispel=0, mechanic=0,
    attributes=_ATTR0_IS_ABILITY | ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=5.0, duration_ms=30000,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=100,
               implicit_target_a=TARGET_UNIT_TARGET_ENEMY),
        Effect(type=EffectType.APPLY_AURA, apply_aura=_AURA_MOD_RESISTANCE, base_points=-240, die_sides=0,
               misc_value=_RESISTANCE_ARMOR, implicit_target_a=TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_SUNDERING_CLEAVE,
    notes=f'{_RV}, RV11: stock Sundering Cleave 25174 (weapon damage and -240 armor for 30 s) on his victim only '
          '(stock: up to 3 targets, ChainTarget 3): the armor cut stays as tank pressure. The weapon hit is 100% '
          'weapon damage (WEAPON_PERCENT_DAMAGE, weapon_potency 100: the potency lint takes no flat weapon bonus; the '
          'stock +30 is noise against his swing), so it follows the template\'s melee (heroic: the heroic '
          'template\'s). Cast on his victim in melee range: first 1 to 22 s, then every 14 to 24 s (the stock SmartAI '
          'timers). Stock look: SV 219, icon 565.',
    raw_overrides=kit_raw('Inflicts $s1% weapon damage and reduces armor by $s2 for $d.', 'Armor reduced by $s2.',
                          instant=True, DefenseType=_DEFENSE_MELEE, PreventionType=_PREVENTION_PACIFY,
                          SpellVisualID_1=_SV_SUNDERING_CLEAVE),
)
