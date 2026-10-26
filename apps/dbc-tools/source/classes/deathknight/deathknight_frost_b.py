"""
Death Knight - S2a Frost: new rows 203308-203325 (Deathchill, Hungering Cold, the Killing Machine buff, Avalanche, the Heart
Strike off-hand copy, the Improved Icy Touch helpers) and the script bindings they own. Owner: A6.
Source of truth: docs/reworks/death-knight-frost-rework.md (tooltips and aura texts verbatim, minus cost / cooldown
sentences), .agents/plans/death-knight-rework/death-knight-rework.S2a-WP-BRIEF.md (rulings D1-D17, field contracts
section 4), S2-HANDOFF U6, U9, U10, U15, U16, U22, U23 and section 4 (ids, icons, visuals) / section 5 (family bits).

Ids and header names (the generator names a row from its VARIABLE name, so the variable names are frozen; the visible
`name=` is what the client shows): 203308-203310 Deathchill r1-r3 (talent rank passives) · 203311 Deathchill buff · 203312
Deathchill marker · 203313 Deathchill lockout · 203314 Hungering Cold passive · 203315 storm · 203316 tick · 203317 slow ·
203318 freeze · 203319 freeze lockout · 203320 Killing Machine buff · 203321 Avalanche · 203322 Heart Strike off-hand ·
203323-203325 Improved Icy Touch helper r1-r3. The talent / SkillLineAbility rows are deathknight_talents.py's; the type-2
link rows that attach 203323-203325 to the Improved Icy Touch ranks are deathknight_trigger_spells.py's.

Conventions: SpellClassSet 15 and EquippedItemClass -1 on every row, CastingTimeIndex 1, stored static base points = live
- 1, SpellLevel = 9 + 5 x row + rank on the talent rank passives and the potency rows (L6), aura texts number-free,
tooltips verbatim. Family bits come from _masks.py: d2 b16 FROST_OTHER_MAGIC on the Hungering Cold tick and Avalanche,
d0 b24 on the Heart Strike off-hand copy (as Heart Strike), none on any buff / marker / lockout / helper (FB section 5).
"""

from lib.dsl import AuraType, DispelType, Effect, EffectType, Mechanic, RANGE_SELF, School, SpellModOp
from lib.dsl.registry import pot_text, scripted_by, spell

from . import _masks as m

# ---- Spell.dbc flag values (src/server/shared/SharedDefines.h) ----
_ATTR0_IS_ABILITY = 0x10
_ATTR0_PASSIVE = 0x40
_ATTR0_DO_NOT_DISPLAY = 0x80
_ATTR0_NO_ACTIVE_DEFENSE = 0x200000
_ATTR0_AURA_IS_DEBUFF = 0x04000000
_HIDDEN_PASSIVE = _ATTR0_PASSIVE | _ATTR0_DO_NOT_DISPLAY
_TALENT_PASSIVE = 464                      # 0x1D0, the stock talent-rank passive frame (Vendetta 49015)
_ATTR3_DOT_STACKING_RULE = 0x80            # one aura per caster (SpellAuras.cpp CanStackWith)
_ATTR3_SUPPRESS_CASTER_PROCS = 0x10000
_ATTR3_ALWAYS_HIT = 0x40000
_ATTR3_ALLOW_AURA_WHILE_DEAD = 0x00100000
_ATTR3_REQUIRES_OFF_HAND_WEAPON = 0x01000000
_SPELLFAMILY_DEATHKNIGHT = 15

# ---- Targets (SharedDefines.h) ----
_TARGET_UNIT_CASTER = 1
_TARGET_UNIT_TARGET_ENEMY = 6
_TARGET_UNIT_SRC_AREA_ENEMY = 15

# ---- Stock icons / visuals (S2-HANDOFF section 4, 0-verify item 4) ----
_ICON_DEATHCHILL = 2028                    # SoulLeech_2: the talent, the buff
_ICON_HUNGERING_COLD = 2797                # INV_Staff_15: the talent and the storm (NEVER on the freeze: disorient DR)
_ICON_KILLING_MACHINE = 2702
_ICON_ICY_REACH = 36                       # the helpers are hidden; Icy Reach's icon (NOT 2721, the stock dummy hook)
_ICON_ICICLE = 1236                        # Spell_Frost_IceShard: damage helpers (tick, Avalanche)
_ICON_SLOW = 180                           # Spell_Frost_ChainsOfIce
_ICON_FREEZE = 2132                        # Spell_Frost_FrozenCore
_ICON_HEART_STRIKE = 3145
_SV_DEATHCHILL = 11515                     # DeathKnight_Deathchill.mdx
_SV_KILLING_MACHINE = 11801
_SV_HUNGERING_COLD_STORM = 90180           # custom (patch_deathknight_vfx_models.py): StateKit with the Blizzard Spawn cloud
#                                            (stock 14540 Cyclone caster state + Snow Tempest was a 145 yd plane, far too big)
_SV_HUNGERING_COLD_TICK = 9487             # stock Blizzard tick (42208): the "Blizzard Impact Base" ice burst on each target
_SV_FREEZE = 4499                          # icebarrier_state.mdx
_SV_AVALANCHE = 14570                      # Ice Burst
_SV_HEART_STRIKE = 11148

# ---- Hidden numbers: the C++ consts (KILLING_MACHINE_MAX_STACKS, DEATHCHILL_DAMAGE_PCT, HUNGERING_COLD_*) are
# deathknight_frost.py's _C list; nothing here redefines them. ----

_DEATHCHILL_TEXT = ('Every {sec} sec, your next Icy Touch, Howling Blast, Frost Strike or Obliterate is a critical strike '
                    'and deals 20% more damage.')
_DEATHCHILL_AURA_TEXT = ('Your next Icy Touch, Howling Blast, Frost Strike or Obliterate is a critical strike and deals '
                         'more damage.')


def _class_mask(raw, effect_index, triple):
    """Write an effect's (d0, d1, d2) EffectSpellClassMask triple: letter = effect (A / B / C), number = dword."""
    for dword, value in enumerate(triple, start=1):
        if value:
            raw[f'EffectSpellClassMask{"ABC"[effect_index]}_{dword}'] = value


def _base_raw(level, description, **extra):
    raw = {
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'EquippedItemClass': -1, 'CastingTimeIndex': 1,
        'SpellLevel': level, 'Description_Lang_enUS': description,
    }
    raw.update(extra)
    return raw


# =====================================================================================================================
# Deathchill (row 4, 3 ranks): passive rank auras 203308-203310 (talent), visible buff 203311, hidden marker 203312,
# hidden lockout 203313. U9: a script, no charged SpellMod (Player::RemoveSpellMods consumes a charge on any affected
# cast, including a Killing Machine Obliterate).
# =====================================================================================================================

_DEATHCHILL_RANK_NOTE = (
    'S2a Frost (4,0) Deathchill rank {rank}: hidden talent passive (frame of stock Vendetta 49015, Attributes 0x1D0). One '
    'DUMMY aura on the caster, stored {stored} = live {sec}: the lockout seconds (the tooltip $s1; the script reads the rank '
    'from which of 203308 / 203309 / 203310 the Death Knight has, brief section 4). Bound to spell_dk_deathchill through '
    'the negative chain key below: AfterEffectApply grants the buff 203311 when no lockout 203313 exists ("ready at the '
    'start of a fight", "ready at login once the lockout lapsed"). The talent has flags 0 (a passive, not a button). '
    'SpellLevel 9 + 5 x 4 + {rank}. No family bits, no spell_proc row.'
)


def _deathchill_rank(spell_id, rank, seconds):
    return spell(
        id=spell_id, name='Deathchill', school=School.FROST, attributes=_TALENT_PASSIVE, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
        effects=[
            Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, base_points=seconds - 1,
                   implicit_target_a=_TARGET_UNIT_CASTER),
        ],
        spell_icon_id=_ICON_DEATHCHILL,
        notes=_DEATHCHILL_RANK_NOTE.format(rank=rank, stored=seconds - 1, sec=seconds),
        raw_overrides=_base_raw(29 + rank, _DEATHCHILL_TEXT.format(sec=seconds), ProcChance=101, RuneCostID=0,
                                EffectChainAmplitude_1=1.0),
    )


deathchill_203308 = _deathchill_rank(203308, 1, 60)
deathchill_203309 = _deathchill_rank(203309, 2, 45)
deathchill_203310 = _deathchill_rank(203310, 3, 30)
scripted_by(-203308, 'spell_dk_deathchill')

# The charge: a visible buff with NO charges and NO SpellMods (the crit rides on the marker, which the Icy Touch /
# Howling Blast / Frost Strike / Obliterate scripts add in OnCast and remove in AfterCast).
deathchill_buff_203311 = spell(
    id=203311, name='Deathchill', school=School.FROST, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_DEATHCHILL,
    notes=(
        'S2a Frost (4,0) U9: the Deathchill charge. Visible self buff (not passive, no consolidation flag), permanent, NO '
        'ProcCharges, no SpellMods, one DUMMY effect so the aura exists. SpellVisual 11515 (stock Deathchill). Number-free '
        'aura text (doc). AttributesEx3 ALLOW_AURA_WHILE_DEAD (kept through death, WP-R M1). Granted by the rank passive on apply and by the lockout 203313 on EXPIRE; spent by the four '
        'strike scripts (marker + lockout), never spent on a Killing Machine Obliterate.'
    ),
    raw_overrides=_base_raw(0, _DEATHCHILL_AURA_TEXT, SpellVisualID_1=_SV_DEATHCHILL,
                            AuraDescription_Lang_enUS=_DEATHCHILL_AURA_TEXT,
                            AttributesEx3=_ATTR3_ALLOW_AURA_WHILE_DEAD),
)

# The marker: a hidden SpellMod pair added for exactly one cast. A flat +100 crit chance on Icy Touch (d0 b1) and Howling
# Blast / Frost Strike / Obliterate (d1 0x20006), the shape of stock 49796 minus its ProcCharges (U9).
deathchill_marker_203312 = spell(
    id=203312, name='Deathchill Marker', school=School.FROST, attributes=_HIDDEN_PASSIVE, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.ADD_FLAT_MODIFIER, base_points=99,
               misc_value=int(SpellModOp.CRITICAL_CHANCE), implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_DEATHCHILL,
    notes=(
        'S2a Frost (4,0) U9: the hidden crit marker. eff0 ADD_FLAT_MODIFIER SPELLMOD_CRITICAL_CHANCE stored 99 = +100 on '
        'm.DEATHCHILL_READ = (Icy Touch d0 0x2, Howling Blast + Frost Strike + Obliterate d1 0x20006) in '
        'EffectSpellClassMaskA_1 / A_2. Hidden passive (0x40 | 0x80), permanent, NO ProcCharges (a charged mod would be '
        'consumed by any affected cast). The scripts add it in OnCast and remove it in AfterCast; it is never armed on a '
        'Killing Machine Obliterate (two +100 crit mods are non-deterministic, Player.cpp:10098-10100). No script, no proc '
        'row.'
    ),
    raw_overrides=_base_raw(0, 'Your next Icy Touch, Howling Blast, Frost Strike or Obliterate is a critical strike.',
                            ProcChance=101, EffectChainAmplitude_1=1.0,
                            EffectSpellClassMaskA_1=m.DEATHCHILL_READ[0], EffectSpellClassMaskA_2=m.DEATHCHILL_READ[1]),
)

# The lockout: hidden but SAVEABLE (not passive: a passive aura is never saved), so a relog keeps the timer. Duration
# 60 s by default; the cast script overrides it per rank (60 / 45 / 30 s). EXPIRE re-grants the buff.
deathchill_lockout_203313 = spell(
    id=203313, name='Deathchill Lockout', school=School.FROST, attributes=_ATTR0_DO_NOT_DISPLAY, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=60000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_DEATHCHILL,
    notes=(
        'S2a Frost (4,0) U9: the hidden charge timer. DO_NOT_DISPLAY only (not passive, so it is saved with the character '
        'and survives a relog), AttributesEx3 ALLOW_AURA_WHILE_DEAD (kept through death, WP-R M1), self, default 60 s: spell_dk_deathchill_lockout is cast with a custom duration of 60 / 45 / '
        '30 s by rank (read from 203308 / 203309 / 203310) and re-grants the buff 203311 on EXPIRE. No SpellMods, no proc '
        'row, no family bits.'
    ),
    raw_overrides=_base_raw(0, 'Deathchill is recharging.', AuraDescription_Lang_enUS='Deathchill is recharging.',
                            AttributesEx3=_ATTR3_ALLOW_AURA_WHILE_DEAD),
)
scripted_by(deathchill_lockout_203313, 'spell_dk_deathchill_lockout')

# =====================================================================================================================
# Hungering Cold (row 6, 1 rank): passive 203314, storm 203315, tick 203316, slow 203317, freeze 203318, lockout 203319.
# U10: a Howling Blast surrounds the Death Knight in a 10 s storm; its third tick on one enemy freezes it for 3 s.
# =====================================================================================================================

# The tick, cast by spell_dk_hungering_cold_storm each 2 s: Frost, magic class, 8 yd around the caster, no target cap,
# 15 attack-power potency (RETUNE 2026-10-25: back to the doc's 15; S2 TUNE had 10) on the 2 s cadence (L2), crits through Runic Focus (d2 b16), rolls no procs and grants no
# Killing Machine (SUPPRESS_CASTER_PROCS).
hungering_cold_tick_203316 = spell(
    id=203316, name='Hungering Cold Tick', school=School.FROST, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=15.0, potency_kind='direct', time_basis_ms=2000,
               implicit_target_a=_TARGET_UNIT_SRC_AREA_ENEMY, radius_yards=8.0),
    ],
    spell_icon_id=_ICON_ICICLE,
    notes=(
        'S2a Frost (6,2) U10: the Hungering Cold storm tick. Frost, DmgClass MAGIC (DefenseType 1), SCHOOL_DAMAGE ap_potency '
        '15 (RETUNE 2026-10-25; S2 TUNE 10, doc 15) direct with time_basis_ms 2000 (L2: the storm ticks every 2 s, not the 1500 default), '
        'SpellLevel 40 = 9 + 5 x 6 '
        '+ 1 (L6), 8 yd TARGET_UNIT_SRC_AREA_ENEMY around the caster (RANGE_SELF), no target cap. d2 b16 '
        'FROST_OTHER_MAGIC (Runic Focus 200% crit and Razorice read it). AttributesEx3 SUPPRESS_CASTER_PROCS: rolls no '
        'procs and grants no Killing Machine. The script filters to enemies engaged with the owner or group and applies '
        'the slow / freeze per target in OnHit.'
    ),
    raw_overrides=_base_raw(
        40, 'The storm deals {pot1} Frost damage to enemies within 8 yards.', SpellClassMask_3=m.FROST_OTHER_MAGIC,
        DefenseType=1, PreventionType=1, AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS,
        SpellVisualID_1=_SV_HUNGERING_COLD_TICK,
    ),
)
scripted_by(hungering_cold_tick_203316, 'spell_dk_hungering_cold_tick')

hungering_cold_passive_203314 = spell(
    id=203314, name='Hungering Cold', school=School.FROST, attributes=_TALENT_PASSIVE, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_HUNGERING_COLD,
    notes=(
        'S2a Frost (6,2) U10: hidden talent passive (frame of stock Vendetta 49015) that marks the talent: Howling Blast '
        'applies the storm 203315 when HasAura(203314). One DUMMY aura; no script, no proc row, no family bits. Icon 2797 '
        '(the talent keeps the stock icon; only an aura with a stun mechanic reads it for DR, SpellMgr.cpp:251-255). '
        'SpellLevel 40 = 9 + 5 x 6 + 1. The stock 49203 / 51209 stay bound and inert.'
    ),
    raw_overrides=_base_raw(
        40,
        'Your Howling Blast surrounds you in a freezing storm for 10 sec, dealing ' + pot_text(hungering_cold_tick_203316)
        + ' Frost damage to enemies within 8 yards every 2 sec. Each tick slows an enemy by a further 20%, and its third '
          'tick freezes the enemy in place for 3 sec.',
        ProcChance=101, RuneCostID=0, EffectChainAmplitude_1=1.0,
    ),
)

# The storm: a visible self aura, PERIODIC_DUMMY every 2 s (a fixed cadence: no ATTR5 haste flag), 10 s. A new Howling
# Blast calls SetDuration(10000) on the live aura (never RefreshDuration / a re-cast, which reset the tick timer).
hungering_cold_storm_203315 = spell(
    id=203315, name='Hungering Cold', school=School.FROST, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=10000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DUMMY, amplitude=2000,
               implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_HUNGERING_COLD,
    notes=(
        'S2a Frost (6,2) U10: the storm. Visible self aura (not passive, no consolidation flag), 10 s, eff0 PERIODIC_DUMMY '
        'amplitude 2000 with no SPELL_HASTE_AFFECTS_PERIODIC bit (always 5 ticks, haste adds none), icon 2797, SpellVisual '
        '90180 (playtest fix: the mage Blizzard cloud, Blizzard_Spawn.mdx at 0.8 scale, as the aura StateKit; the stock '
        '14540 Snow Tempest plane was 145 yd wide). spell_dk_hungering_cold_storm casts the tick 203316 from '
        'OnPeriodic; one storm per Death Knight. Number-free aura text (doc). No family bits.'
    ),
    raw_overrides=_base_raw(
        40, 'A freezing storm surrounds you, damaging, slowing and freezing nearby enemies.',
        SpellVisualID_1=_SV_HUNGERING_COLD_STORM,
        AuraDescription_Lang_enUS='A freezing storm surrounds you, damaging, slowing and freezing nearby enemies.',
        ProcChance=101, EffectChainAmplitude_1=1.0,
    ),
)
scripted_by(hungering_cold_storm_203315, 'spell_dk_hungering_cold_storm')

# The slow: 20% per stack, 2 stacks (CumulativeAura 2), ~3 s refreshed by every tick, per caster (DOT_STACKING_RULE), so
# two Death Knights' storms stack. NEVER d1 b18: Frost Fever removal strips d1 b18 auras (Unit.cpp:5145-5152).
hungering_cold_slow_203317 = spell(
    id=203317, name='Hungering Cold', school=School.FROST, dispel=DispelType.MAGIC, attributes=0, cast_time_ms=0,
    cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=3000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DECREASE_SPEED, base_points=-21,
               mechanic=Mechanic.SNARE, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_SLOW,
    notes=(
        'S2a Frost (6,2) U10: the per-tick slow. eff0 MOD_DECREASE_SPEED stored -21 = -20% per stack, mechanic SNARE, '
        'CumulativeAura 2 (so -40% at 2 stacks), 3 s so it fades about 3 s after the enemy leaves the storm (each tick '
        're-applies it), dispel Magic. AttributesEx3 DOT_STACKING_RULE (one aura per caster) | ALWAYS_HIT (the tick already '
        'rolled the hit; a missed slow would eat a stack). DefenseType 1 / PreventionType 1. No family bits (never d1 '
        'b18). No script.'
    ),
    raw_overrides=_base_raw(
        40, 'Movement slowed.', AuraDescription_Lang_enUS='Movement slowed.', CumulativeAura=2,
        AttributesEx3=_ATTR3_DOT_STACKING_RULE | _ATTR3_ALWAYS_HIT, DefenseType=1, PreventionType=1,
        EffectChainAmplitude_1=1.0,
    ),
)

# The freeze: Frost + MOD_STUN gives AURA_STATE_FROZEN (SpellInfo.cpp:2075-2079). No interrupt flags (damage never
# breaks it), no charges, NOT icon 2797 (that icon adds disorient DR on a family-15 spell, SpellMgr.cpp:251-255).
hungering_cold_freeze_203318 = spell(
    id=203318, name='Frozen', school=School.FROST, mechanic=Mechanic.STUN, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=3000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_STUN, mechanic=Mechanic.STUN,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_FREEZE,
    notes=(
        'S2a Frost (6,2) U10: the third-tick freeze. Frost school, eff0 MOD_STUN with mechanic STUN (spell and effect), 3 s, '
        'no AuraInterruptFlags and no ProcCharges (damage does not break it), so it carries AURA_STATE_FROZEN '
        '(SpellInfo.cpp:2075-2079) and counts as Frozen for every Frozen reader. Icon 2132, NOT 2797. SpellVisual 4499 '
        '(icebarrier_state). Not dispellable (a 3 s design stun). AttributesEx3 ALWAYS_HIT. DefenseType 1 / PreventionType '
        '1. Cast only when the target is not stun-immune and has no lockout 203319. Its own stun mechanic still enters the '
        'stun DR group (playtest row). No family bits.'
    ),
    raw_overrides=_base_raw(
        40, 'Frozen.', AuraDescription_Lang_enUS='Frozen.', SpellVisualID_1=_SV_FREEZE,
        AttributesEx3=_ATTR3_DOT_STACKING_RULE | _ATTR3_ALWAYS_HIT, DefenseType=1, PreventionType=1, EffectChainAmplitude_1=1.0,
    ),
)

# The per-enemy, per-caster 20 s freeze lockout: a hidden debuff on the enemy (DOT_STACKING_RULE: two Death Knights keep
# separate lockouts).
hungering_cold_lockout_203319 = spell(
    id=203319, name='Hungering Cold Lockout', school=School.FROST,
    attributes=_ATTR0_DO_NOT_DISPLAY | _ATTR0_AURA_IS_DEBUFF, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0,
    mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=20000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.DUMMY, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_SLOW,
    notes=(
        'S2a Frost (6,2) U10: hidden 20 s debuff on the frozen enemy; it cannot be frozen again by that Death Knight while '
        'it lasts. DO_NOT_DISPLAY | AURA_IS_DEBUFF, AttributesEx3 DOT_STACKING_RULE (per caster) | ALWAYS_HIT. Icon 180, '
        'never 2797. No script, no family bits.'
    ),
    raw_overrides=_base_raw(
        40, 'Cannot be frozen by Hungering Cold again yet.',
        AttributesEx3=_ATTR3_DOT_STACKING_RULE | _ATTR3_ALWAYS_HIT, EffectChainAmplitude_1=1.0,
    ),
)

# =====================================================================================================================
# Killing Machine buff 203320 (U6): CumulativeAura 2, 30 s, no charges, no spell_proc row. The talent ranks (51123 /
# 51127 / 51128) are deathknight_trigger_spells.py's; they trigger this buff on an auto attack hit.
# =====================================================================================================================

killing_machine_buff_203320 = spell(
    id=203320, name='Killing Machine', school=School.FROST, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=30000,
    effects=[
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.ADD_FLAT_MODIFIER, base_points=99,
               misc_value=int(SpellModOp.CRITICAL_CHANCE), implicit_target_a=_TARGET_UNIT_CASTER),
    ],
    spell_icon_id=_ICON_KILLING_MACHINE,
    notes=(
        'S2a Frost (3,0) U6: the Killing Machine buff (stock 51124 stays bound and inert: SpellInfoCorrections.cpp:268 '
        'forces its ProcCharges to 1 and spell_dk.cpp:2778 forces its mask). Visible self buff (not passive, no '
        'consolidation flag), 30 s, CumulativeAura 2 (two stacks), NO ProcCharges, NO spell_proc row. eff0 '
        'ADD_FLAT_MODIFIER SPELLMOD_CRITICAL_CHANCE stored 99 = +100 on m.KILLING_MACHINE_READ = Obliterate d1 b17 '
        '(EffectSpellClassMaskA_2), which reaches 203054 and the off-hand copy 66198. The Obliterate script consumes one '
        'stack in AfterCast (ModStackAmount(-1)) and switches the school to Frost in OnCast (U5). SpellVisual 11801 '
        '(stock Killing Machine). Number-free aura text (doc). SpellLevel 0 (no potency).'
    ),
    raw_overrides=_base_raw(
        0, 'Your next Obliterate is a critical strike and deals Frost damage.',
        AuraDescription_Lang_enUS='Your next Obliterate is a critical strike and deals Frost damage.',
        SpellVisualID_1=_SV_KILLING_MACHINE, CumulativeAura=2, ProcChance=101, EffectChainAmplitude_1=1.0,
        EffectSpellClassMaskA_1=m.KILLING_MACHINE_READ[0], EffectSpellClassMaskA_2=m.KILLING_MACHINE_READ[1],
    ),
)

# =====================================================================================================================
# Avalanche 203321 (Rime rank 3 capstone): an icicle per enemy a Rime Howling Blast hit, up to 5, triggered.
# =====================================================================================================================

avalanche_203321 = spell(
    id=203321, name='Avalanche', school=School.FROST, attributes=0, cast_time_ms=0, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
    effects=[
        Effect(type=EffectType.SCHOOL_DAMAGE, ap_potency=25.0, potency_kind='direct', time_basis_ms=1500,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_ICICLE,
    notes=(
        'S2a Frost (3,1) Rime rank 3 capstone: one icicle, cast triggered by the Howling Blast script at each enemy that '
        'Rime Howling Blast hit (at most one per enemy, at most RIME_AVALANCHE_TARGETS = 5). Frost, DmgClass MAGIC '
        '(DefenseType 1), SCHOOL_DAMAGE ap_potency 25 (RETUNE 2026-10-25; S2 TUNE 17, doc 25) direct (default 1500 time basis, L2), '
        'SpellLevel 27 = 9 + 5 x 3 + 3 '
        '(L6). d2 b16 FROST_OTHER_MAGIC (Runic Focus 200% crit and Razorice read it). AttributesEx3 SUPPRESS_CASTER_PROCS: '
        'rolls no procs and grants no Killing Machine. SpellVisual 14570 (Ice Burst).'
    ),
    raw_overrides=_base_raw(
        27, 'Icicles deal {pot1} Frost damage.', SpellClassMask_3=m.FROST_OTHER_MAGIC, DefenseType=1, PreventionType=1,
        AttributesEx3=_ATTR3_SUPPRESS_CASTER_PROCS, SpellVisualID_1=_SV_AVALANCHE,
    ),
)

# =====================================================================================================================
# Heart Strike off-hand copy 203322 (U16): the frame of Death Strike's copy 66188 (the three attribute words) with Heart
# Strike's two effects, percent first. D1: a physical copy stores HALF the main-hand flat potency (10 -> 5) because the
# engine doubles the Death Knight off-hand flat then multiplies by 0.5 x (1 + Nerves), so the flat nets (1 + N) x 5 =
# the target 0.5 x (1 + N) x 10.
# =====================================================================================================================

heart_strike_offhand_203322 = spell(
    id=203322, name='Heart Strike', school=School.NORMAL, attributes=_ATTR0_IS_ABILITY | 0x40000 | _ATTR0_NO_ACTIVE_DEFENSE,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    effects=[
        Effect(type=EffectType.WEAPON_PERCENT_DAMAGE, weapon_potency=60, implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
        Effect(type=EffectType.NORMALIZED_WEAPON_DMG, sp_potency=5, potency_kind='direct', time_basis_ms=1500,
               implicit_target_a=_TARGET_UNIT_TARGET_ENEMY),
    ],
    spell_icon_id=_ICON_HEART_STRIKE,
    notes=(
        'S2a Frost (7,0) U16 / D1: the Threat of Thassarian off-hand Heart Strike, cast triggered by the main-hand Heart '
        'Strike (spell_dk_frost_offhand). Frame copy of Heart Strike 55050 with the attribute words of 66188 (0-verify '
        'item 2): Attributes 0x240010, AttributesEx 0x8000000, AttributesEx3 0x1040000 = REQUIRES_OFF_HAND_WEAPON | '
        'ALWAYS_HIT, EquippedItemClass 2 / subclass 173555, so the weapon part reads the off-hand. Effects: eff0 '
        'WEAPON_PERCENT_DAMAGE weapon_potency 60 FIRST, eff1 NORMALIZED_WEAPON_DMG sp_potency 5 SECOND (half the main hand\'s '
        '10: D1), EFFECT_2 empty (the core Heart Strike disease branch reads Effects[EFFECT_2] and finds zero). Single '
        'target only (no chain_targets). SpellLevel 1 (as 55050). d0 b24 HEART_STRIKE (so Gravefrost / Vendetta / the HS '
        'readers match it); triggered, so no Threat of Thassarian loop and no rune cost. Physical (School NORMAL, '
        'DefenseType 2), so the engine\'s off-hand path applies; a school switch (Gravefrost) is the helper\'s job.'
    ),
    raw_overrides={
        'SpellClassSet': _SPELLFAMILY_DEATHKNIGHT, 'SpellClassMask_1': m.HEART_STRIKE, 'EquippedItemClass': 2,
        'EquippedItemSubclass': 173555, 'CastingTimeIndex': 1, 'SpellLevel': 1, 'DefenseType': 2, 'PreventionType': 2,
        'AttributesEx': 0x8000000, 'AttributesEx3': _ATTR3_ALWAYS_HIT | _ATTR3_REQUIRES_OFF_HAND_WEAPON,
        'SpellVisualID_1': _SV_HEART_STRIKE, 'ProcChance': 101, 'EffectChainAmplitude_1': 1.0,
        'EffectChainAmplitude_2': 1.0,
        'Description_Lang_enUS': 'Strikes the target with your off-hand weapon.',
    },
)
scripted_by(heart_strike_offhand_203322, 'spell_dk_frost_offhand')

# =====================================================================================================================
# Improved Icy Touch helpers (row 0, 3 ranks): hidden passives added with each rank by the type-2 link rows on the Improved
# Icy Touch ranks (deathknight_trigger_spells.py). SPELLMOD_DOT +5 / 10 / 15% on Frost Fever; rank 3 adds the capstone
# +10 yd range on Icy Touch, Chains of Ice and Howling Blast (the Icy Reach 55061 shape).
# =====================================================================================================================


def _iit_helper(spell_id, rank, stored_pct, range_capstone):
    effects = [
        Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.ADD_PCT_MODIFIER, base_points=stored_pct,
               misc_value=int(SpellModOp.DOT), implicit_target_a=_TARGET_UNIT_CASTER),
    ]
    raw = _base_raw(
        9 + rank, f'Your Frost Fever deals {5 * rank}% more damage.' + (
            ' Increases the range of your Icy Touch, Chains of Ice and Howling Blast by 10 yards.'
            if range_capstone else ''),
        ProcChance=101, EffectChainAmplitude_1=1.0,
    )
    _class_mask(raw, 0, (0, m.FROST_FEVER_DISEASE, 0))
    if range_capstone:
        effects.append(
            Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.ADD_FLAT_MODIFIER, base_points=9,
                   misc_value=int(SpellModOp.RANGE), implicit_target_a=_TARGET_UNIT_CASTER))
        raw['EffectChainAmplitude_2'] = 1.0
        _class_mask(raw, 1, m.IMPROVED_ICY_TOUCH_RANGE)
    return spell(
        id=spell_id, name='Improved Icy Touch Helper', school=School.FROST, attributes=_HIDDEN_PASSIVE, cast_time_ms=0,
        cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
        effects=effects, spell_icon_id=_ICON_ICY_REACH,
        notes=(
            f'S2a Frost (0,1) Improved Icy Touch rank {rank} helper: hidden passive added and removed with the rank by the '
            f'type-2 spell_linked_spell row on the rank (A2). eff0 ADD_PCT_MODIFIER SPELLMOD_DOT stored {stored_pct} = '
            f'+{5 * rank}% on Frost Fever only (EffectSpellClassMaskA_2 = m.FROST_FEVER_DISEASE, d1 b26; the DoT modifier '
            'snapshots when the disease is applied, the doc\'s rule; the Icy Touch part is the stock icon-2721 dummy). '
            + ('eff1 ADD_FLAT_MODIFIER SPELLMOD_RANGE stored 9 = +10 yd on m.IMPROVED_ICY_TOUCH_RANGE = Icy Touch + Chains '
               'of Ice (d0 0x6) and Howling Blast (d1 0x2) in EffectSpellClassMaskB_1 / B_2 (the capstone; Icy Reach '
               '55061 shape, +10 instead of +5). ' if range_capstone else '')
            + 'Icon 36 (Icy Reach), not 2721 (the stock dummy hook). No script, no proc row, no family bits.'
        ),
        raw_overrides=raw,
    )


improved_icy_touch_helper_203323 = _iit_helper(203323, 1, 4, False)
improved_icy_touch_helper_203324 = _iit_helper(203324, 2, 9, False)
improved_icy_touch_helper_203325 = _iit_helper(203325, 3, 14, True)
