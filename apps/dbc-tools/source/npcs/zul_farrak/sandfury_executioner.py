"""
Zul'Farrak build WP-D4a: the Sandfury Executioner (7274) and the Block, stage 1 of the Pyramid, plus the Pyramid-wide
pieces every stage shares (Grievous Wound, Offerings, Blood Price), normal and heroic
(.agents/plans/zul-farrak-build/zul-farrak-build.HANDOFF.md s3.5 row D4a, s3.6, s3.8, s7 #11 A, #12 A, #43 A, #44 A;
build spec docs/dungeons/zul-farrak-rework.md SP 1346-1432 (PY1-PY3, PY15, PY16), design SP 1180-1281). WP-D4a owns
this file (its spells: kSpellsBlock 213960-213989 of modules/mod-dungeon-bosses src/ZulFarrak/ZulFarrakRework.h only;
BlockLogic.h names the same ids). The engine side is src/ZulFarrak/boss_sandfury_executioner_rework.cpp and
PyramidFight.h; the text is data/sql/updates/pending_db_world/rev_sandfury_executioner_zul_farrak.sql.

- 7274 Sandfury Executioner: boss_sandfury_executioner_rework (SmartAI off: rev_skeleton_zul_farrak.sql drops his
  rows), normal health 136,058 = 70.9 on the level 46 warrior base 1,919 (s3.6, s7 #1 A x1.6), stock DamageModifier 2.4,
  immunity -93 -> 1972 (gap 3), INSTANCE_BIND with both assist flags, detection 12 (WP-S0's boss_columns). Heroic
  226,764 and the tier's melee are WP-H's overrides. His loot (the cage key) stays stock.
- 301019 Zul'Farrak Pyramid Stalker: npc_zf_pyramid_stalker, the invisible stalker 11686, inert. D4a: the Block's rope
  holder (the channel fields at the Executioner's feet). D4b may use the same entry for its lane. No heroic template.

Spells. The axe deals its damage through a dungeon copy of the mod-boss-mechanics resolve spell (the kit's RegistryHit:
the registry's percent of the reference row, the tank row on the tank; the combat log names the mechanic). The bar is
a no-effect cast on the prisoner (Physical, not kickable: he has no kickable cast at all), keeping his swing timer
(SPELL_ATTR2_DO_NOT_RESET_COMBAT_TIMERS, LESSONS L3). The rest are auras and looks:

  213960  Behead                PY1 the 4 s bar on the prisoner (Physical, not kickable)
  213961  Behead                PY1 the axe on its soaker: resolve copy (Physical), 40% / 60%, heroic 150% wounded
  213962  Behead                PY1 the axe on the prisoner as it falls (Execute Prisoner 30273's SV 39)
  213963  Grievous Wound        PY2 heroic: Physical bleed, 3% of the reference row a second, until healed to 95%
  213964  Grievous Wound        PY2 the one-shot as a wound opens (Grievous Wound 31956's SV 121)
  213965  Offerings             PY3 normal: +10% damage done a stack, 4 stacks, on every Sandfury of the encounter
  213966  Blood Price           PY16 heroic: +0.5% damage done a stack (the amount is the script's), no cap
  213967  Chain                 PY1 the rope (Wrangling Rope 40856's SV 9275): a channel field, never cast
  213968-213989 spare.

Berserker Stance 7366 (on aggro) and Cleave 15496 (every 7 to 11 s) stay stock, cast as they are. Tooltips are
number-free.
"""

from lib.dsl import RANGE_SELF, AuraType, Effect, EffectType, School
from lib.dsl.dungeon_kit import ATTR0_DO_NOT_DISPLAY, ATTR0_DO_NOT_LOG, ATTR1_NO_THREAT, ATTR2_IGNORE_LINE_OF_SIGHT
from lib.dsl.registry import creature_model, creature_template, creature_template_columns, scripted_by, spell

from ._common import (
    ATTR0_AURA_IS_DEBUFF,
    ATTR3_IGNORE_CASTER_MODIFIERS,
    ATTR4_NO_CAST_LOG,
    KIT_HELPER,
    TARGET_UNIT_CASTER,
    TARGET_UNIT_TARGET_ANY,
    boss_columns,
    kit_raw,
    resolve_copy,
)
from ._visuals import (
    DISPLAY_INVISIBLE_STALKER,
    PY_BEHEAD,
    PY_CHAIN,
    PY_GRIEVOUS,
    PY_GRIEVOUS_STATE,
    PY_OFFERING_BUFF,
)

creature_template_columns(7274, **boss_columns(
    'boss_sandfury_executioner_rework', 70.9, damage_modifier=2.4,
))

_PY = "Zul'Farrak build WP-D4a (the Block)"
_SCRIPT_DAMAGE = ("Zul'Farrak: the kit's spell_dungeon_refflat_periodic sets each tick (a percent of the reference "
                  "row, hundredths in the base point), not a potency value")

_SCHOOL_MASK_ALL = 127
_ATTR1_IS_CHANNELED = 0x00000004
_ATTR2_DO_NOT_RESET_COMBAT_TIMERS = 0x00020000      # a finished cast keeps his swing timer (LESSONS L3)
# AURA_INTERRUPT_FLAG_CHANGE_MAP (SpellDefines.h): the aura never leaves the instance on the character.
_AURA_INTERRUPT_CHANGE_MAP = 0x00080000

# BlockLogic.h Tune (the DT test pins each against the header).
_BEHEAD_CAST_MS = 4000              # kBeheadCastMs
_WOUND_TICK_HUNDREDTHS = 300        # kWoundTickHundredths (3.00% of the reference row)
_WOUND_TICK_MS = 1000               # kWoundTickMs
_OFFERINGS_PCT = 10                 # kOfferingsPctPerStack
_OFFERINGS_CAP = 4                  # ZulFarrakRework.h kOfferingsCap
_AURA_STACK_LIMIT = 255             # kAuraStackLimit
_BAR_RANGE_YD = 30.0                # the prisoner is chained 2.5 yd from him (a CR teleport lands there too)

# Stock icons (Spell.dbc 2026-11-25).
_ICON_EXECUTE_PRISONER = 564        # Execute Prisoner 30273
_ICON_GRIEVOUS_WOUND = 243          # Grievous Wound 31956
_ICON_BLOOD_FURY = 1662             # Blood Fury 20572
_ICON_ROPE = 2452                   # Wrangling Rope 40856


def _look(spell_id: int, name: str, visual: int, icon: int, notes: str):
    """A look cast triggered on its target: an instant DUMMY, no handler, hidden from the log."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG,
        cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
        duration_ms=0, effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
        spell_icon_id=icon, notes=notes,
        raw_overrides=kit_raw(instant=True, SpellVisualID_1=visual, AttributesEx=ATTR1_NO_THREAT,
                              AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


def _sandfury_buff(spell_id: int, name: str, base: int, stacks: int, desc: str, aura_desc: str, notes: str):
    """A stacking damage done buff on a Sandfury of the encounter (DungeonKit::AddStacks on itself, all schools,
    permanent, not dispellable). His reference-sized hits ignore caster modifiers: it raises his melee and stock
    blows only."""
    return spell(
        id=spell_id, name=name, school=School.NORMAL, dispel=0, mechanic=0, cast_time_ms=0, cooldown_ms=0,
        category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=RANGE_SELF, duration_ms=-1,
        effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.MOD_DAMAGE_PERCENT_DONE, base_points=base,
                        die_sides=0, misc_value=_SCHOOL_MASK_ALL, implicit_target_a=TARGET_UNIT_CASTER,
                        potency_excluded=f'{name}: a flat percent of damage done a stack, not a damage or heal value')],
        spell_icon_id=_ICON_BLOOD_FURY, notes=notes,
        raw_overrides=kit_raw(desc, aura_desc, instant=True, CumulativeAura=stacks, SpellVisualID_1=PY_OFFERING_BUFF,
                              AttributesEx=ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
    )


# --- PY1 the Block ---------------------------------------------------------------------------------------------------

behead_bar_213960 = spell(
    id=213960, name='Behead', school=School.NORMAL, cast_time_ms=_BEHEAD_CAST_MS, cooldown_ms=0,
    category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=_BAR_RANGE_YD, duration_ms=0,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_EXECUTE_PRISONER,
    notes=f'{_PY}, PY1: the 4 s bar on the chained prisoner (he faces them), every 20 s from 10 s (heroic gaps 18 s, '
          '16 s ... down to 5 s), with yell line 2 at the tear and a 2 yd registry Soak on the prisoner. No effect: '
          'the AI lands the axe (213961 on the soaker, or the prisoner dies) at its end. Physical and not '
          'interruptible (InterruptFlags 0, PreventionType 0; his immunity set 1972 holds stun, fear and polymorph): '
          'he has no kickable cast. Keeps his swing timer.',
    raw_overrides=kit_raw('Raises the axe over a prisoner.', InterruptFlags=0, PreventionType=0,
                          AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=_ATTR2_DO_NOT_RESET_COMBAT_TIMERS | ATTR2_IGNORE_LINE_OF_SIGHT,
                          AttributesEx4=ATTR4_NO_CAST_LOG),
)

behead_213961 = resolve_copy(
    213961, 'Behead', School.NORMAL, 'The axe falls.',
    f'{_PY}, PY1: the axe on the one player standing on the prisoner (2 yd) as the bar ends (the kit\'s RegistryHit): '
    '40% normal / 60% heroic of the reference row (the tank row on the tank, tank included); heroic, 150% on a soaker '
    'still carrying Grievous Wound (s7 #43 A (c): bots refuse them, a human may take it). A soak: no Weakened. Heroic '
    'rider: Grievous Wound (213963). Copy of the resolve spell 205001 (Physical: armor cuts it). No visual (213962 '
    'is the axe).',
    icon=_ICON_EXECUTE_PRISONER,
)

behead_look_213962 = _look(
    213962, 'Behead', PY_BEHEAD, _ICON_EXECUTE_PRISONER,
    f'{_PY}, PY1: the axe the Executioner swings at the prisoner as the bar ends (triggered), soaked or not. Execute '
    'Prisoner 30273\'s SV 39 (cast anim Special1H, DecisiveStrike impact).')

chain_213967 = spell(
    id=213967, name='Chain', school=School.NORMAL, attributes=ATTR0_DO_NOT_DISPLAY | ATTR0_DO_NOT_LOG, dispel=0,
    mechanic=0, cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0,
    range_yards=100.0, duration_ms=15000,
    effects=[Effect(type=EffectType.DUMMY, implicit_target_a=TARGET_UNIT_TARGET_ANY)],
    spell_icon_id=_ICON_ROPE,
    notes=f'{_PY}, PY1: the rope from the Executioner\'s feet to the chained prisoner for the bar: never cast; the '
          'script sets the channel fields of the Pyramid stalker 301019 it summons at his feet '
          '(UNIT_FIELD_CHANNEL_OBJECT = the prisoner, UNIT_CHANNEL_SPELL = this id) and despawns it when the axe '
          'falls. Wrangling Rope 40856\'s SV 9275 (V: a rope, no chain-link beam exists; Shackle\'s SV 68 is never '
          'wired).',
    raw_overrides=kit_raw(instant=True, SpellVisualID_1=PY_CHAIN,
                          AttributesEx=_ATTR1_IS_CHANNELED | ATTR1_NO_THREAT, AttributesEx4=ATTR4_NO_CAST_LOG),
)

# --- PY2 Grievous Wound ----------------------------------------------------------------------------------------------

grievous_wound_213963 = spell(
    id=213963, name='Grievous Wound', school=School.NORMAL, dispel=0, mechanic=0, attributes=ATTR0_AURA_IS_DEBUFF,
    cast_time_ms=0, cooldown_ms=0, category_cooldown_ms=0, mana_cost=0, mana_cost_pct=0, range_yards=100.0,
    duration_ms=-1,
    effects=[Effect(type=EffectType.APPLY_AURA, apply_aura=AuraType.PERIODIC_DAMAGE,
                    base_points=_WOUND_TICK_HUNDREDTHS, die_sides=0, amplitude=_WOUND_TICK_MS,
                    implicit_target_a=TARGET_UNIT_TARGET_ANY, potency_excluded=_SCRIPT_DAMAGE)],
    spell_icon_id=_ICON_GRIEVOUS_WOUND,
    notes=f'{_PY}, PY2 (heroic): a bleed, 3% of the reference row a second (the kit\'s spell_dungeon_refflat_periodic, '
          'base point 300 = 3.00% in hundredths, heroic the same; the tank row on the tank), Physical, until the '
          'carrier is healed to 95% or more (spell_zf_pyramid_grievous_wound: that tick deals nothing and removes it; '
          'PyramidFight.h also clears it every 250 ms while a stage runs). Every wound of the encounter: the Block\'s '
          'soaker (the axe\'s rider), a Berserker\'s heroic charge and Nekrum\'s Gutchew (D4b, '
          'ZfPyramid::ApplyGrievousWound). While any player carries one the Sandfury gain a Blood Price stack a second '
          '(PY16). Dispel none and mechanic none (no cure, no Stoneform or bleed immunity takes it: healing is the '
          'answer, ruling 23); ignores caster modifiers (Blood Price never grows it). Permanent; removed on death, by '
          'a wipe of the stage and at the Pyramid\'s end. Boiling Blood 72385\'s SV 15286 (the lasting chest state; '
          'the one-shot 121 is 213964). AuraInterruptFlags CHANGE_MAP.',
    raw_overrides=kit_raw('A grievous wound that bleeds until healed.', 'Bleeding. Heal to nearly full health to close '
                          'the wound. While it bleeds, the Sandfury grow stronger.', CastingTimeIndex=1,
                          SpellVisualID_1=PY_GRIEVOUS_STATE, AttributesEx=ATTR1_NO_THREAT,
                          AttributesEx2=ATTR2_IGNORE_LINE_OF_SIGHT, AttributesEx3=ATTR3_IGNORE_CASTER_MODIFIERS,
                          AttributesEx4=ATTR4_NO_CAST_LOG, AuraInterruptFlags=_AURA_INTERRUPT_CHANGE_MAP),
)
scripted_by(grievous_wound_213963, 'spell_dungeon_refflat_periodic', 'spell_zf_pyramid_grievous_wound')

grievous_look_213964 = _look(
    213964, 'Grievous Wound', PY_GRIEVOUS, _ICON_GRIEVOUS_WOUND,
    f'{_PY}, PY2: the one-shot as a wound opens (triggered on the carrier with 213963). Grievous Wound 31956\'s SV '
    '121 (BloodyExplosion once; the lasting look is 213963\'s 15286).')

# --- PY3 Offerings, PY16 Blood Price ---------------------------------------------------------------------------------

offerings_213965 = _sandfury_buff(
    213965, 'Offerings', _OFFERINGS_PCT, _OFFERINGS_CAP, 'Strengthened by the blood of the block.',
    'Strengthened by the blood of the block. Damage done increased.',
    f'{_PY}, PY3 (normal): +10% damage done a stack (all schools), one stack per crew member lost on the Block, cap 4 '
    '(the instance counts them, DATA_OFFERINGS; PyramidFight.h keeps every Sandfury of the encounter at that count: '
    'the Executioner, the climbers, Sezz\'ziz and Nekrum). For the rest of the encounter; a wipe restores the count '
    'of the stage\'s start. Not on heroic (Blood Price replaces it). Blood Fury 20572\'s SV 47 (glowing hands).',
)

blood_price_213966 = _sandfury_buff(
    213966, 'Blood Price', 0, _AURA_STACK_LIMIT, 'Fed by the blood of the living.',
    'Fed by the blood of the living. Damage done increased.',
    f'{_PY}, PY16 (heroic): a stack a second while any player bleeds from Grievous Wound, 30 at once per crew member '
    'lost on the Block (the instance\'s DATA_BLOOD_PRICE), no cap; every Sandfury of the encounter carries the total '
    '(PyramidFight.h). +0.5% damage done a stack: the base point is 0 and the script sets the amount to half the '
    'total (rounded down) with AuraEffect::ChangeAmount, so the damage keeps growing past the counter\'s 255 '
    '(CumulativeAura 255 shows the stacks). Not dispellable. Blood Fury 20572\'s SV 47 (as Offerings: it replaces '
    'them on heroic).',
)

# --- 301019 the Pyramid stalker --------------------------------------------------------------------------------------

pyramid_stalker_301019 = creature_template(
    301019, "Zul'Farrak Pyramid Stalker", **{**KIT_HELPER, 'minlevel': 46, 'maxlevel': 46, 'rank': 0,
                                             'unit_class': 1, 'type': 10, 'flags_extra': 0x40 | 0x80,
                                             'ScriptName': 'npc_zf_pyramid_stalker'},
)
creature_model(301019, display_id=DISPLAY_INVISIBLE_STALKER)
