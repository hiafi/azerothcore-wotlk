"""
Blackrock Depths build WP-D6: the Ring of Law's hard mode, the Encore (heroic only): Theldren 16059, Korv 16053, Lefty
16049, Volida 16058, Malgen Longspear 16052, Korv's three totems 300789-300791 and the banner (gameobject 301280)
(.agents/plans/blackrock-depths-build/blackrock-depths-build.HANDOFF.md s3.5 row D6, s3.7; build spec
docs/dungeons/blackrock-depths-1-detention-block.md S1 "Hard mode: the Encore", "Theldren and his team" and the Ring's
Build spec rows EN1-EN16). WP-D6 owns this file (its spells: kSpellsEncore 210960-211019 of modules/mod-dungeon-bosses
src/BlackrockDepths/BlackrockDepthsRework.h; RingEncoreLogic.h names the same ids). The members' SmartAI drop,
Theldren's death line and the banner's gameobject_template row are the core SQL rev
rev_ring_encore_blackrock_depths.sql.

- The five: bound to ring_encore_hard_mode.cpp's AIs (AIName ''; the rev drops their SmartAI). They exist on heroic only
  (Grimstone summons them after the title holder when the banner burned), so their health is WP-H's heroic overrides
  (source/world/dungeons/blackrock_depths.py: 160k / 80k / 100k, ruling 30); the normal rows keep their stock
  HealthModifier and DamageModifier. Theldren is stun immune (S1: the kit set 1972, stock -93 fear and horror) with
  no INSTANCE_BIND (boss_columns instance_bind=False: the Ring's credit is Grimstone's); the other four
  keep no immunities (S1: "taunt and crowd control work").
- 300789 Healing Stream Totem, 300790 Searing Totem, 300791 Earthbind Totem (EN6): level 60 totems of the team's
  faction, no loot or XP, npc_brd_encore_totem (rooted, passive; the script sets 1 health: "one hit", WP-H s7 item 3);
  heroic lock lines 310400-310402 (STAGE-H-REPORT s3; their heroic row is the tier template).

Spells (looks from ._visuals, WP-V-1's TH_ / KO_ / LE_ / VL_ / MA_ picks and RL_BANNER_BURN; every look unconfirmed
until seen in game): 210960-210999 as RingEncoreLogic.h lists them; 211000-211019 spare.

Kept stock (S1 "Keep"): Battle Shout 27578, Mortal Strike 27580, Hamstring 27584 (Theldren), Frost Shock 21401, Purge
27626 (Korv), Sinister Strike 14873, Eviscerate 27611 (Lefty), Frostbolt 20822, Cone of Cold 20828 (Volida). Retired
(never cast by the reworked scripts): Intercept 27577, Frightening Shout 19134, Demoralizing Shout 27579, Lesser Healing
Wave 27624, Earthbind Totem 15786, Kidney Shot 27615, Aimed Shot 31623, Freezing Trap 32419, Blizzard 27618. Malgen's
Snap Trap object is Blackrock Spire's Net Trap gameobject 301253 (display 7529, GODI_SNAP_TRAP), reused as is.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import (
    ATTR0_DO_NOT_DISPLAY,
    ATTR0_DO_NOT_LOG,
    ATTR1_NO_THREAT,
    ATTR2_IGNORE_LINE_OF_SIGHT,
    ATTR3_ALWAYS_HIT,
    TARGET_UNIT_TARGET_ENEMY,
    cast_bar,
    self_visual,
    standing_in_it,
)
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR0_NO_IMMUNITIES,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    FACTION_DARK_IRON,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    kit_creature,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_KORV_TOTEM_EARTHBIND,
    DISPLAY_KORV_TOTEM_HEALING,
    DISPLAY_KORV_TOTEM_SEARING,
    KO_ANCESTRAL_SPIRIT,
    KO_CHAIN_HEAL,
    KO_EARTH_SHIELD,
    KO_SEARING_BOLT,
    LE_EVASION,
    LE_SHADOWSTEP,
    LE_VICIOUS_WOUND,
    MA_DISENGAGE,
    MA_MULTI_SHOT,
    MA_PIERCING_SHOT,
    MA_SNAP_TRAP_FREEZE,
    RL_BANNER_BURN,
    TH_CHAMPIONS_PRIDE,
    TH_EXECUTE,
    TH_EXECUTIONERS_CHARGE,
    TH_INTIMIDATING_ROAR,
    VL_BLINK,
    VL_BLIZZARD,
    VL_FROST_NOVA,
    VL_ICE_BARRIER,
)

_D6 = 'Blackrock Depths build WP-D6 (the Ring of Law: the Encore)'
_SCRIPT_VALUE = 'Blackrock Depths: the script sets the value per target (DungeonKit::RefFlatOn, CastCustomSpell)'
_SCRIPT_HEAL = 'Blackrock Depths: the script sets the heal (a percent of the target\'s health, CastCustomSpell)'

# --- constants (RingEncoreLogic.h; lib/test_blackrock_depths_ring_encore.py pins each against the header) -------------

# entry: (script, the AI's member)
MEMBERS = {
    16059: 'npc_brd_encore_theldren',
    16053: 'npc_brd_encore_korv',
    16049: 'npc_brd_encore_lefty',
    16058: 'npc_brd_encore_volida',
    16052: 'npc_brd_encore_malgen',
}
THELDREN_HEALTH_MODIFIER = 3.5      # stock (the normal row is never summoned: the Encore is heroic only)
THELDREN_DAMAGE_MODIFIER = 7.5      # stock
# Korv's totems: entry -> (name, display (V-1), heroic lock line (STAGE-H-REPORT s3))
TOTEMS = {
    300789: ('Healing Stream Totem', DISPLAY_KORV_TOTEM_HEALING, 310400),
    300790: ('Searing Totem', DISPLAY_KORV_TOTEM_SEARING, 310401),
    300791: ('Earthbind Totem', DISPLAY_KORV_TOTEM_EARTHBIND, 310402),
}
TOTEM_SCRIPT = 'npc_brd_encore_totem'
TOTEM_LEVEL = 60

CHARGE_WARN_MS = 1500           # kChargeWarnMs
WOUNDED_MS = 6000               # kWoundedMs
WOUNDED_HEALING_PCT = 50        # kWoundedHealingPct
ROAR_WARN_MS = 2500             # kRoarWarnMs
ROAR_FEAR_MS = 2000             # kRoarFearMs
PRIDE_HASTE_PCT = 25            # kPrideHastePct
CHAIN_HEAL_CAST_MS = 2000       # kChainHealCastMs
SPIRIT_CAST_MS = 5000           # kSpiritCastMs
SPIRIT_RANGE_YD = 30.0          # kSpiritRangeYd
EARTH_SHIELD_CHARGES = 6        # kEarthShieldCharges
EARTH_SHIELD_MS = 600000        # kEarthShieldMs
EARTHBIND_SLOW_PCT = 50         # kEarthbindSlowPct
EARTHBIND_SLOW_MS = 2000        # kEarthbindSlowMs
KIDNEY_SHOT_MS = 2000           # kKidneyShotMs
WOUND_CAP = 5                   # kWoundCap
WOUND_MS = 60000                # kWoundMs
EVASION_MS = 8000               # kEvasionMs
EVASION_DODGE_PCT = 75          # kEvasionDodgePct
BLIZZARD_SLOW_PCT = 50          # kBlizzardSlowPct
BLIZZARD_SLOW_MS = 2000         # kBlizzardSlowMs
BLIZZARD_MS = 6000              # kBlizzardMs
BLIZZARD_RADIUS = 8.0           # kBlizzardRadius
NOVA_CAST_MS = 1500             # kNovaCastMs
NOVA_ROOT_MS = 2000             # kNovaRootMs
ICE_BARRIER_MS = 60000          # kIceBarrierMs
PIERCING_CAST_MS = 3000         # kPiercingCastMs
TRAP_FREEZE_MS = 2000           # kTrapFreezeMs
MULTI_SHOT_WARN_MS = 2000       # kMultiShotWarnMs

_FLAGS_EXTRA_NO_XP = 0x40
_CREATURE_TYPE_TOTEM = 11
_DISPEL_MAGIC = 1
_MECHANIC_FEAR = 5
_MECHANIC_ROOT = 7
_MECHANIC_STUN = 12
_MECHANIC_FREEZE = 13
_MECHANIC_BLEED = 15
_SCHOOL_MASK_ALL = 127
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000
_SPELL_INTERRUPT_FLAGS_KICK = 15
_PREVENTION_SILENCE = 1
_DEFENSE_MAGIC = 1
_DEFENSE_RANGED = 3
_TARGET_DEST_DEST = 87
_TARGET_DEST_CASTER = 18
_TARGET_DEST_DYNOBJ_ALLY = 29
_TARGET_FLAG_DEST_LOCATION = 0x40

# Stock icons (Spell.dbc SpellIconID of the named spell, read 2026-11-17 from the base DBC)
_ICON_CHARGE = 457                      # Charge 100
_ICON_INTIMIDATING_SHOUT = 148          # Intimidating Shout 5246
_ICON_EXECUTE = 1648                    # Execute 5308
_ICON_MORTAL_STRIKE = 564               # Mortal Strike 27580
_ICON_RECKLESSNESS = 138                # Recklessness 1719
_ICON_CHAIN_HEAL = 963                  # Chain Heal 1064
_ICON_ANCESTRAL_SPIRIT = 149            # Ancestral Spirit 2008
_ICON_EARTH_SHIELD = 2015               # Earth Shield 974
_ICON_SEARING_TOTEM = 680               # Searing Totem 3599
_ICON_HEALING_STREAM = 1647             # Healing Stream Totem 5394
_ICON_EARTHBIND = 686                   # Earthbind Totem 2484
_ICON_SHADOWSTEP = 2363                 # Shadowstep 36563
_ICON_KIDNEY_SHOT = 499                 # Kidney Shot 27615
_ICON_GARROTE = 498                     # Garrote 703
_ICON_EVASION = 178                     # Evasion 4086
_ICON_BLIZZARD = 285                    # Blizzard 27618
_ICON_FROST_NOVA = 193                  # Frost Nova 122
_ICON_BLINK = 1499                      # Blink 1953
_ICON_ICE_BARRIER = 32                  # Ice Barrier 11426
_ICON_AIMED_SHOT = 1629                 # Aimed Shot 31623
_ICON_FREEZING_TRAP = 180               # Freezing Trap Effect 3355
_ICON_DISENGAGE = 539                   # Disengage 781
_ICON_MULTI_SHOT = 85                   # Multi-Shot 2643
_ICON_SHOOT = 126                       # Shoot 6660

# --- the bindings -----------------------------------------------------------------------------------------------------

creature_template_columns(16059, **boss_columns(MEMBERS[16059], THELDREN_HEALTH_MODIFIER,
                                                damage_modifier=THELDREN_DAMAGE_MODIFIER, instance_bind=False))
for _entry, _script in MEMBERS.items():
    if _entry != 16059:
        creature_template_columns(_entry, ScriptName=_script, AIName='')


# --- EN6 Korv's totems ------------------------------------------------------------------------------------------------

def _totem_columns(heroic: int) -> dict:
    """A totem: the team's faction, level 60, a totem, no loot or XP, rooted and passive by its own AI."""
    return {
        **kit_creature(faction=FACTION_DARK_IRON, type=_CREATURE_TYPE_TOTEM), 'minlevel': TOTEM_LEVEL,
        'maxlevel': TOTEM_LEVEL, 'rank': 0, 'unit_class': 1, 'unit_flags': 0, 'HealthModifier': 1.0,
        'DamageModifier': 0.0, 'BaseAttackTime': 2000, 'detection_range': 0.0, 'CreatureImmunitiesId': 0,
        'lootid': 0, 'pickpocketloot': 0, 'skinloot': 0, 'mingold': 0, 'maxgold': 0,
        'flags_extra': _FLAGS_EXTRA_NO_XP, 'ScriptName': TOTEM_SCRIPT, 'difficulty_entry_1': heroic,
    }


# The entries are written as numbers: source/world/dungeons/blackrock_depths.py finds the declared kit adds by the
# pattern `creature_template(<entry>, ...)` (WP-H); the totems get no heroic health override (the tier template).
healing_stream_totem_300789 = creature_template(300789, 'Healing Stream Totem', **_totem_columns(TOTEMS[300789][2]))
searing_totem_300790 = creature_template(300790, 'Searing Totem', **_totem_columns(TOTEMS[300790][2]))
earthbind_totem_300791 = creature_template(300791, 'Earthbind Totem', **_totem_columns(TOTEMS[300791][2]))
for _entry, (_name, _display, _heroic) in TOTEMS.items():
    creature_model(_entry, display_id=_display)


# --- helpers ----------------------------------------------------------------------------------------------------------

def _aura(spell_id: int, name: str, effects: list[dict], *, duration_ms: int, debuff: bool, icon: int, desc: str,
          aura_desc: str, notes: str, stacks: int = 0, visual: int = 0, school: School = School.NORMAL,
          mechanic: int = 0, dispel: int = 0, target: int = TARGET_UNIT_TARGET_ANY, extra: dict | None = None):
    """An aura the script applies (triggered); every effect an APPLY_AURA on `target`; dropped on a map change."""
    raw = kit_raw(desc, aura_desc, CastingTimeIndex=1, AttributesEx=ATTR1_NO_THREAT,
                  AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_ALWAYS_HIT,
                  AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP)
    if stacks:
        raw['CumulativeAura'] = stacks
    if visual:
        raw['SpellVisualID_1'] = visual
    if extra:
        raw.update(extra)
    built = []
    for e in effects:
        effect = dict(type=EffectType.APPLY_AURA, die_sides=0, implicit_target_a=target, mechanic=mechanic)
        effect.update(e)
        built.append(Effect(**effect))
    return spell(
        id=spell_id, name=name, school=school, dispel=dispel, mechanic=mechanic,
        attributes=(ATTR0_AURA_IS_DEBUFF if debuff else 0) | ATTR0_NO_IMMUNITIES, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=duration_ms,
        effects=built, spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


def _value_hit(spell_id: int, name: str, school: School, desc: str, notes: str, *, icon: int, visual: int = 0,
               ranged: bool = False):
    """A one-target hit whose number the script sets (CastCustomSpell BasePoint0 = RefFlatOn(...)): ignores caster
    modifiers (the reference row is the number), no threat, always hits."""
    raw = kit_raw(desc, CastingTimeIndex=1, DefenseType=_DEFENSE_RANGED if ranged else _DEFENSE_MAGIC,
                  AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                  AttributesEx3=ATTR3_ALWAYS_HIT | ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG)
    if visual:
        raw['SpellVisualID_1'] = visual
    return spell(
        id=spell_id, name=name, school=school, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.SCHOOL_DAMAGE, base_points=1, die_sides=0,
                        implicit_target_a=TARGET_UNIT_TARGET_ENEMY, potency_excluded=_SCRIPT_VALUE)],
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


def _value_heal(spell_id: int, name: str, desc: str, notes: str, *, icon: int, visual: int = 0):
    """A one-target heal whose number the script sets (a percent of the target's health); ignores caster modifiers."""
    raw = kit_raw(desc, CastingTimeIndex=1, AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                  AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS, AttributesEx4=ATTR4_NO_CAST_LOG)
    if visual:
        raw['SpellVisualID_1'] = visual
    return spell(
        id=spell_id, name=name, school=School.NATURE, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0, duration_ms=0,
        effects=[Effect(type=EffectType.HEAL, base_points=1, die_sides=0, implicit_target_a=TARGET_UNIT_TARGET_ANY,
                        potency_excluded=_SCRIPT_HEAL)],
        spell_icon_id=icon, notes=notes, raw_overrides=raw,
    )


def _kickable(spell_id: int, name: str, school: School, cast_ms: int, desc: str, notes: str, *, icon: int,
              target: int = TARGET_UNIT_CASTER, range_yards: float = RANGE_SELF):
    """A kickable cast with no effect of its own (DUMMY): the script acts when it lands (OnSpellCast) and cancels its
    registry mechanic when it is kicked (OnSpellFailed). InterruptFlags 15, silence-preventable."""
    return spell(
        id=spell_id, name=name, school=school, cast_time_ms=cast_ms, cooldown_ms=0, category_cooldown_ms=0,
        mana_cost=0, mana_cost_pct=0, range_yards=range_yards, duration_ms=0,
        effects=[Effect(type=EffectType.DUMMY, implicit_target_a=target)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(desc, InterruptFlags=_SPELL_INTERRUPT_FLAGS_KICK, PreventionType=_PREVENTION_SILENCE,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- EN2-EN3 Theldren -------------------------------------------------------------------------------------------------

charge_bar_210960 = cast_bar(
    210960, 'Executioner\'s Charge', CHARGE_WARN_MS, 'Theldren picks out the weakest.',
    f'{_D6}, EN2: Theldren\'s 1.5 s bar while the lowest-health player wears the mark 210961 (the tank too, ruling '
    '88); then the charge. Not interruptible (cast_bar; he is stun immune).',
    icon=_ICON_CHARGE,
)
charge_mark_210961 = _aura(
    210961, 'Executioner\'s Mark', [dict(apply_aura=AuraType.DUMMY, base_points=0)],
    duration_ms=CHARGE_WARN_MS, debuff=True, icon=_ICON_CHARGE, desc='Theldren is coming for you.',
    aura_desc='Theldren is coming for you.',
    notes=f'{_D6}, EN2: the 1.5 s mark on the charge\'s target (no number; what the player reads). Not dispellable.',
)
charge_hit_210962 = _value_hit(
    210962, 'Executioner\'s Charge', School.NORMAL, 'Theldren crashes into you.',
    f'{_D6}, EN2: the charge\'s landing on the marked player: 25% of the reference row (the tank row on the tank: '
    'RefFlatOn), with -50% healing 6 s (210963). No stun (the stock Intercept 27577\'s 3 s stun is retired). Charge '
    '100\'s look (SV 867).',
    icon=_ICON_CHARGE, visual=TH_EXECUTIONERS_CHARGE,
)
wounded_210963 = _aura(
    210963, 'Mortal Wound', [dict(apply_aura=AuraType.MOD_HEALING_PCT, base_points=-WOUNDED_HEALING_PCT,
                                  potency_excluded='Mortal Wound: a flat -50% healing taken, not a heal value')],
    duration_ms=WOUNDED_MS, debuff=True, icon=_ICON_MORTAL_STRIKE, desc='Healing taken reduced.',
    aura_desc='Healing taken reduced by $s1%.',
    notes=f'{_D6}, EN2: the charge\'s -50% healing taken for 6 s. Not dispellable (a physical wound).',
)
execute_210964 = _value_hit(
    210964, 'Execute', School.NORMAL, 'Theldren finishes the job.',
    f'{_D6}, EN2: the charged player is below 30% health on the landing: Execute for 40% of the reference row '
    '(RefFlatOn). Execute 5308\'s blood hands and impact (SV 250).',
    icon=_ICON_EXECUTE, visual=TH_EXECUTE,
)
roar_bar_210965 = cast_bar(
    210965, 'Intimidating Roar', ROAR_WARN_MS, 'Theldren draws breath.',
    f'{_D6}, EN3: the 2.5 s bar while the 8 yd ring on him fills (the registry owns the hit). Not interruptible.',
    icon=_ICON_INTIMIDATING_SHOUT,
)
roar_210966 = resolve_copy(
    210966, 'Intimidating Roar', School.NORMAL, 'Theldren roars.',
    f'{_D6}, EN3: every 18 s (12 s below 30%), 8 yd round him, everyone inside, the tank too (ruling 88): 35% of the '
    'reference row, 1 Weakened and the 2 s fear 210967 (registry tag 29). Copy of the resolve spell 205001 '
    '(Physical) with Intimidating Shout 5246\'s look (SV 247).',
    icon=_ICON_INTIMIDATING_SHOUT, visual=TH_INTIMIDATING_ROAR,
)
roar_fear_210967 = _aura(
    210967, 'Intimidating Roar', [dict(apply_aura=AuraType.MOD_FEAR, base_points=0)],
    duration_ms=ROAR_FEAR_MS, debuff=True, icon=_ICON_INTIMIDATING_SHOUT, mechanic=_MECHANIC_FEAR,
    desc='Feared.', aura_desc='Feared.',
    notes=f'{_D6}, EN3: the roar\'s 2 s fear (the registry\'s rider; the fix of the stock 6 s Frightening Shout).',
)
pride_210968 = _aura(
    210968, 'Champion\'s Pride', [dict(apply_aura=AuraType.MOD_MELEE_HASTE, base_points=PRIDE_HASTE_PCT,
                                       potency_excluded='Champion\'s Pride: a flat +25% attack speed')],
    duration_ms=-1, debuff=False, icon=_ICON_RECKLESSNESS, visual=TH_CHAMPIONS_PRIDE, target=TARGET_UNIT_CASTER,
    desc='The champion will not yield.', aura_desc='Attack speed increased by $s1%.',
    notes=f'{_D6}, Champion\'s Pride: below 30% health, +25% attack speed for the rest of the fight (and the Roar '
          'every 12 s). Recklessness 1719\'s lasting red glow (SV 236). Not dispellable.',
)

# --- EN4-EN7 Korv -----------------------------------------------------------------------------------------------------

chain_heal_210969 = _kickable(
    210969, 'Chain Heal', School.NATURE, CHAIN_HEAL_CAST_MS, 'Heals up to three teammates.',
    f'{_D6}, EN4: every 8 s, a 2 s cast (Nature; from the stock Lesser Healing Wave 27624): when it lands the three '
    'lowest standing teammates (Korv too) are healed 12% each (210970). Kickable; the Ring\'s interrupt list: '
    'expected (priority 2).',
    icon=_ICON_CHAIN_HEAL,
)
chain_heal_hit_210970 = _value_heal(
    210970, 'Chain Heal', 'Heals a teammate.',
    f'{_D6}, EN4: one teammate\'s heal, 12% of its health (the script). Chain Heal 1064\'s look (SV 3659).',
    icon=_ICON_CHAIN_HEAL, visual=KO_CHAIN_HEAL,
)
ancestral_spirit_210971 = _kickable(
    210971, 'Ancestral Spirit', School.NATURE, SPIRIT_CAST_MS, 'Returns a fallen teammate to the fight.',
    f'{_D6}, EN5: a teammate fell (a held body, KT-D1): a 5 s cast at the body (Nature); if it lands the teammate '
    'stands at 50% health, once per teammate. Kickable; the interrupt list\'s top priority (3).',
    icon=_ICON_ANCESTRAL_SPIRIT, target=TARGET_UNIT_TARGET_ANY, range_yards=SPIRIT_RANGE_YD + 5.0,
)
spirit_look_210972 = self_visual(
    210972, 'Ancestral Spirit', KO_ANCESTRAL_SPIRIT,
    f'{_D6}, EN5: the resurrection burst on the body as it stands (Ancestral Spirit 2008, SV 344).',
    icon=_ICON_ANCESTRAL_SPIRIT, school=School.NATURE,
)
earth_shield_210973 = _aura(
    210973, 'Earth Shield', [dict(apply_aura=AuraType.DUMMY, base_points=0)],
    duration_ms=EARTH_SHIELD_MS, debuff=False, icon=_ICON_EARTH_SHIELD, school=School.NATURE, dispel=_DISPEL_MAGIC,
    desc='Protects the target with an earthen shield.', aura_desc='Each hit taken heals the target.',
    notes=f'{_D6}, EN7: every 30 s on Theldren: 6 charges (ProcCharges, set again by the script), each hit he takes '
          'heals him 2% of his health (210974; the script\'s DamageTaken spends a charge). Magic: a Purge removes it '
          'whole (the reward; the purge list). Look: Earth Shield 974\'s own (KO_EARTH_SHIELD, SV 7362).',
    extra={'ProcCharges': EARTH_SHIELD_CHARGES}, visual=KO_EARTH_SHIELD,
)
earth_shield_heal_210974 = _value_heal(
    210974, 'Earth Shield', 'Heals the shielded target.',
    f'{_D6}, EN7: a charge\'s heal, 2% of Theldren\'s health (the script).',
    icon=_ICON_EARTH_SHIELD,
)
searing_bolt_210975 = _value_hit(
    210975, 'Searing Bolt', School.FIRE, 'The Searing Totem burns you.',
    f'{_D6}, EN6: the Searing Totem (300790) shoots a random player within 20 yd every 2 s for 3% of the reference row '
    '(RefFlatOn) for its 20 s. Look: the Searing Totem\'s Attack 3606\'s bolt (KO_SEARING_BOLT, SV 67).',
    icon=_ICON_SEARING_TOTEM, visual=KO_SEARING_BOLT,
)
healing_stream_210976 = _value_heal(
    210976, 'Healing Stream', 'Heals a nearby teammate.',
    f'{_D6}, EN6: the Healing Stream Totem (300789) heals every standing teammate within 20 yd for 2% of its health '
    'every second until it is killed (one hit).',
    icon=_ICON_HEALING_STREAM,
)
earthbind_210977 = standing_in_it(
    210977, f'{_D6}, EN6: the Earthbind Totem (300791) pulses every second for 20 s: every player within 10 yd is '
    'slowed 50% for 2 s (re-applied each pulse, so it ends soon after leaving). Snare.',
    name='Earthbind', slow_pct=EARTHBIND_SLOW_PCT, duration_ms=EARTHBIND_SLOW_MS, desc='Slowed by the earth.',
    aura_desc='Movement speed reduced.', icon=_ICON_EARTHBIND,
)

# --- EN8-EN10 Lefty ---------------------------------------------------------------------------------------------------

shadowstep_look_210978 = self_visual(
    210978, 'Shadowstep', LE_SHADOWSTEP,
    f'{_D6}, EN8: the step behind the healer (Shadowstep 36563\'s shadow and anim, SV 8262); the move is server side.',
    icon=_ICON_SHADOWSTEP, school=School.SHADOW,
)
kidney_shot_210979 = _aura(
    210979, 'Kidney Shot', [dict(apply_aura=AuraType.MOD_STUN, base_points=0)],
    duration_ms=KIDNEY_SHOT_MS, debuff=True, icon=_ICON_KIDNEY_SHOT, mechanic=_MECHANIC_STUN,
    desc='Stunned.', aura_desc='Stunned.',
    notes=f'{_D6}, EN8: every 15 s after the Shadowstep, a 2 s stun on the healer (the fix of the stock 4 s Kidney '
          'Shot 27615; rule limit).',
)
vicious_wound_210980 = _aura(
    210980, 'Vicious Wound', [dict(apply_aura=AuraType.DUMMY, base_points=0)],
    duration_ms=WOUND_MS, debuff=True, icon=_ICON_GARROTE, stacks=WOUND_CAP, visual=LE_VICIOUS_WOUND,
    mechanic=_MECHANIC_BLEED, desc='Bleeding.', aura_desc='Bleeding each second. Heal above 90% health to close it.',
    notes=f'{_D6}, EN9: each Sinister Strike that lands adds a stack (cap 5, DungeonKit::AddStacks); Lefty\'s script '
          'ticks it every second for 1% of the reference row a stack (210981) and removes it once the target is '
          'above 90% health. No dispel (Dispel none). Bite\'s lasting bleed state (SV 376; never Garrote\'s one puff).',
)
vicious_wound_tick_210981 = _value_hit(
    210981, 'Vicious Wound', School.NORMAL, 'The wound bleeds.',
    f'{_D6}, EN9: a tick, 1% of the reference row per stack (RefFlatOn).',
    icon=_ICON_GARROTE,
)
evasion_210982 = _aura(
    210982, 'Evasion', [dict(apply_aura=AuraType.MOD_DODGE_PERCENT, base_points=EVASION_DODGE_PCT,
                             potency_excluded='Evasion: a flat +75% dodge, not a damage value')],
    duration_ms=EVASION_MS, debuff=False, icon=_ICON_EVASION, visual=LE_EVASION, target=TARGET_UNIT_CASTER,
    desc='Dodges most attacks.', aura_desc='Dodge chance increased by $s1%.',
    notes=f'{_D6}, EN10: at 50% and at 25% health, 8 s: +75% dodge (this WP\'s default for "dodges most physical '
          'attacks"; ranged and spells land). Not dispellable. Adrenaline Rush 13750\'s lasting look (SV 8996).',
)

# --- EN11-EN13 Volida -------------------------------------------------------------------------------------------------

blizzard_210983 = resolve_copy(
    210983, 'Blizzard', School.FROST, 'Ice shards fall on you.',
    f'{_D6}, EN11: every 12 s, an 8 yd circle at a random player\'s spot, 2 s, then 6 s of ticks: 4% of the reference '
    'row a second and the slow 210984 (registry tag 30, persistent; Crowd Favor judges its landing, then -1 per '
    'player per storm). Copy of the resolve spell 205004 (Frost).',
    icon=_ICON_BLIZZARD,
)
blizzard_slow_210984 = standing_in_it(
    210984, f'{_D6}, EN11: the storm\'s slow, -50% for 2 s, re-applied by every tick that hits (the registry\'s '
    'rider).',
    name='Blizzard', slow_pct=BLIZZARD_SLOW_PCT, duration_ms=BLIZZARD_SLOW_MS, desc='Slowed by the storm.',
    aura_desc='Movement speed reduced.', icon=_ICON_BLIZZARD,
)
blizzard_look_210985 = spell(
    id=210985, name='Blizzard', school=School.FROST, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=BLIZZARD_MS,
    effects=[Effect(type=EffectType.PERSISTENT_AREA_AURA, base_points=0, implicit_target_a=_TARGET_DEST_CASTER,
                    implicit_target_b=_TARGET_DEST_DYNOBJ_ALLY, apply_aura=AuraType.DUMMY,
                    radius_yards=BLIZZARD_RADIUS)],
    spell_icon_id=_ICON_BLIZZARD,
    notes=f'{_D6}, EN11: visual only, the storm for its 6 s on a stalker (300796) at the spot, cast as the marker '
          'ends. '
          'TARGET_DEST_CASTER / TARGET_DEST_DYNOBJ_ALLY with a DUMMY aura (Balnazzar\'s ground look\'s shape: it '
          'reaches nobody). Blizzard 27618\'s area look (SV 10386).',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=VL_BLIZZARD, AttributesEx4=ATTR4_NO_CAST_LOG),
)
frost_nova_cast_210986 = _kickable(
    210986, 'Frost Nova', School.FROST, NOVA_CAST_MS, 'Volida gathers the cold.',
    f'{_D6}, EN12: when 2 or more players stand within 10 yd of her, a 1.5 s cast (Frost); the 10 yd ring at her spot '
    'resolves as it ends (210987), then she blinks 15 yd away. Kickable (a kick cancels the ring); the interrupt '
    'list, priority 2.',
    icon=_ICON_FROST_NOVA,
)
frost_nova_210987 = resolve_copy(
    210987, 'Frost Nova', School.FROST, 'The cold bites.',
    f'{_D6}, EN12: 10 yd at her spot, everyone inside, the tank too: 20% of the reference row, 1 Weakened and the 2 s '
    'root 210988 (registry tag 31). Copy of the resolve spell 205004 (Frost) with Frost Nova 122\'s look (SV 17).',
    icon=_ICON_FROST_NOVA, visual=VL_FROST_NOVA,
)
frost_nova_root_210988 = _aura(
    210988, 'Frost Nova', [dict(apply_aura=AuraType.MOD_ROOT, base_points=0)],
    duration_ms=NOVA_ROOT_MS, debuff=True, icon=_ICON_FROST_NOVA, school=School.FROST, mechanic=_MECHANIC_ROOT,
    dispel=_DISPEL_MAGIC, desc='Frozen in place.', aura_desc='Frozen in place.',
    notes=f'{_D6}, EN12: the nova\'s 2 s root (the registry\'s rider). Magic: a dispel is a reward.',
)
blink_look_210989 = self_visual(
    210989, 'Blink', VL_BLINK,
    f'{_D6}, EN12: the Blink after a nova (Blink 1953, SV 263); the move is server side, kept on the floor.',
    icon=_ICON_BLINK, school=School.ARCANE,
)
ice_barrier_210990 = _aura(
    210990, 'Ice Barrier', [dict(apply_aura=AuraType.SCHOOL_ABSORB, base_points=1, misc_value=_SCHOOL_MASK_ALL,
                                 potency_excluded=_SCRIPT_VALUE)],
    duration_ms=ICE_BARRIER_MS, debuff=False, icon=_ICON_ICE_BARRIER, visual=VL_ICE_BARRIER, school=School.FROST,
    dispel=_DISPEL_MAGIC, target=TARGET_UNIT_CASTER, desc='Absorbs damage.', aura_desc='Absorbs damage.',
    notes=f'{_D6}, EN13: every 30 s a shield worth 10% of her health (CastCustomSpell BasePoint0). Magic: Purge or '
          'Spellsteal is the reward (the purge list). Ice Barrier 11426\'s look (SV 4302).',
)

# --- EN14-EN16 Malgen -------------------------------------------------------------------------------------------------

piercing_cast_210991 = _kickable(
    210991, 'Piercing Shot', School.NORMAL, PIERCING_CAST_MS, 'Malgen draws a long shot.',
    f'{_D6}, EN14: every 15 s, a 3 s cast (from the stock Aimed Shot 31623) while a 3 yd line from him through a '
    'random player to the wall fills; it resolves as the cast ends (210992). Kickable (a kick cancels the line); the '
    'interrupt list, a reward (priority 1).',
    icon=_ICON_AIMED_SHOT,
)
piercing_210992 = resolve_copy(
    210992, 'Piercing Shot', School.NORMAL, 'The arrow passes through you.',
    f'{_D6}, EN14: the line\'s hit, everyone in it: 40% of the reference row and 1 Weakened (registry tag 32). Copy of '
    'the resolve spell 205001 (Physical) with Aimed Shot 31623\'s bolt (SV 7955).',
    icon=_ICON_AIMED_SHOT, visual=MA_PIERCING_SHOT,
)
snap_trap_210993 = resolve_copy(
    210993, 'Snap Trap', School.NORMAL, 'The trap snaps shut.',
    f'{_D6}, EN15: after 3 s with a player in melee, a 3 yd trap at his feet (the registry\'s Mine: arms in 1 s, 60 s, '
    'at most 3; Blackrock Spire\'s Net Trap object 301253) and a 15 yd Disengage: the first player on it takes 20% '
    'of the reference row, 1 Weakened and the 2 s freeze 210994 (registry tag 33). Copy of the resolve spell 205001.',
    icon=_ICON_FREEZING_TRAP,
)
snap_trap_freeze_210994 = _aura(
    210994, 'Snap Trap', [dict(apply_aura=AuraType.MOD_STUN, base_points=0)],
    duration_ms=TRAP_FREEZE_MS, debuff=True, icon=_ICON_FREEZING_TRAP, visual=MA_SNAP_TRAP_FREEZE,
    school=School.FROST, mechanic=_MECHANIC_FREEZE, dispel=_DISPEL_MAGIC, desc='Frozen.', aura_desc='Frozen.',
    notes=f'{_D6}, EN15: the trap\'s 2 s freeze (the fix of the stock 20 s Freezing Trap). Magic: a dispel is a '
          'reward. Freezing Trap Effect 3355\'s ice state (SV 4499).',
)
disengage_look_210995 = self_visual(
    210995, 'Disengage', MA_DISENGAGE,
    f'{_D6}, EN15: the Disengage leap\'s anim (Disengage 781, SV 12305); the jump is server side, kept on the floor.',
    icon=_ICON_DISENGAGE,
)
multi_shot_bar_210996 = cast_bar(
    210996, 'Multi-Shot', MULTI_SHOT_WARN_MS, 'Malgen nocks a handful of arrows.',
    f'{_D6}, EN16: the 2 s bar while the 30 yd cone toward a random player fills (the registry owns the hit). Not '
    'interruptible (cast_bar).',
    icon=_ICON_MULTI_SHOT,
)
multi_shot_210997 = resolve_copy(
    210997, 'Multi-Shot', School.NORMAL, 'A spray of arrows.',
    f'{_D6}, EN16: every 10 s, a 40 degree (this WP\'s default), 30 yd cone from him toward a random player: 25% of '
    'the '
    'reference row and 1 Weakened (registry tag 34). Copy of the resolve spell 205001 (Physical) with Multi-Shot '
    '2643\'s look (SV 567).',
    icon=_ICON_MULTI_SHOT, visual=MA_MULTI_SHOT,
)
shoot_210998 = _value_hit(
    210998, 'Shoot', School.NORMAL, 'Malgen shoots.',
    f'{_D6}: Malgen\'s filler between the shots (S1 unset: this WP\'s default), every 2.5 s at his victim 5 yd or more '
    'away: 5% of the reference row (RefFlatOn). Ranged defense; no look (Shoot 6660 has none: the client draws his '
    'bow\'s shot).',
    icon=_ICON_SHOOT, ranged=True,
)

# --- EN1 the banner ---------------------------------------------------------------------------------------------------

banner_burn_210999 = spell(
    id=210999, name='Burn the Banner', school=School.FIRE, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=_TARGET_DEST_DEST)],
    spell_icon_id=1,
    notes=f'{_D6}, EN1: look only, the clicking player sets the banner (301280) alight: a dest missile at it (Ignite '
          'Horde Siege Engine 32979\'s fire hands, missile and explosion, SV 8490). The click itself is the '
          'gameobject\'s script (DATA_BANNER_BURNED, Grimstone line 11).',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=RL_BANNER_BURN, Targets=_TARGET_FLAG_DEST_LOCATION,
                          AttributesEx=ATTR1_NO_THREAT, AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)
